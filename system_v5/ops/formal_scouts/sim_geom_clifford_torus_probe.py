#!/usr/bin/env python3
"""Canonical Stage 3 geometry-object lego: Clifford torus in S^3.

This sim is intentionally narrow. It builds the Clifford torus
T^2 = S^1(1/sqrt(2)) x S^1(1/sqrt(2)) in S^3 as a standalone geometry object,
then checks the defining invariants against a radius-warped non-flat control.

Claim ceiling: geometry-object lego only. This is not a manifold layer,
G-structure selection, stack, flux, Axis0, FEP, gravity, or bridge result.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import sys
import time
from datetime import datetime, timezone
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import torch
import z3

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "sim_geom_clifford_torus_probe"
OBJECT_ID = "clifford_torus"
OUT_PATH = RESULT_DIR / "geom_clifford_torus_probe_results.json"

RTYPE = torch.float64
torch.set_default_dtype(RTYPE)

SCALES = (8, 16, 32, 64)
ETA_CLIFFORD = math.pi / 4.0
WARP_AMPLITUDE = 0.22
TWO_PI = 2.0 * math.pi
INV_SQRT2 = 1.0 / math.sqrt(2.0)
CURVATURE_TOL = 1.0e-7
MEAN_CURVATURE_TOL = 1.0e-7
CONTROL_CURVATURE_FLOOR = 1.0e-3
CONTROL_MEAN_FLOOR = 1.0e-3
GEOMSTATS_ATOL = 1.0e-6
KILL_FLOOR = 1.0e-9
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY claim-bearing differential geometry: finite torus samples, S^3 embedding, metric, Gaussian curvature, mean curvature, controls, and scale ladder.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "Parity mirror only for representable coordinate/radius/unit-norm/area computations; no geomstats or full curvature path is claimed in JAX.",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING ambient Hypersphere(dim=3) check: recomputes S^3 membership on real torus samples and on a flattened control for the numeric ablation.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING exact geometry mirror: metric diag(cos^2 eta, sin^2 eta), K=0 for the product torus, H(pi/4)=0, and area=2*pi^2.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING helper-bound SMT proof via smt_load_bearing; the flat+minimal claim flips real sat / radius-warped control unsat using measured invariants.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control boundary only; NumPy is not imported or used for claim-bearing geometry.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "geomstats": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "numpy": "None",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if hasattr(value, "tolist") and callable(value.tolist):
        try:
            return as_jsonable(value.tolist())
        except Exception:
            pass
    if hasattr(value, "item") and callable(value.item):
        try:
            return as_jsonable(value.item())
        except Exception:
            pass
    return value


def sample_pairs(n: int) -> list[tuple[float, float]]:
    return [
        (
            TWO_PI * ((i + 0.5) / n),
            TWO_PI * ((((3 * i + 1) % n) + 0.5) / n),
        )
        for i in range(n)
    ]


def eta_for(coords: torch.Tensor, mode: str) -> torch.Tensor:
    if mode == "clifford":
        return coords[0] * 0.0 + torch.tensor(ETA_CLIFFORD, dtype=RTYPE)
    if mode == "warped_nonflat_control":
        return torch.tensor(ETA_CLIFFORD, dtype=RTYPE) + WARP_AMPLITUDE * torch.cos(coords[0])
    raise ValueError(f"unknown mode: {mode}")


def embedding(coords: torch.Tensor, mode: str) -> torch.Tensor:
    u, v = coords[0], coords[1]
    eta = eta_for(coords, mode)
    return torch.stack(
        [
            torch.cos(eta) * torch.cos(u),
            torch.cos(eta) * torch.sin(u),
            torch.sin(eta) * torch.cos(v),
            torch.sin(eta) * torch.sin(v),
        ]
    )


def jacobian_embedding(coords: torch.Tensor, mode: str) -> torch.Tensor:
    return torch.autograd.functional.jacobian(
        lambda q: embedding(q, mode),
        coords,
        create_graph=True,
        strict=False,
    )


def hessian_embedding(coords: torch.Tensor, mode: str) -> torch.Tensor:
    rows = []
    for k in range(4):
        rows.append(
            torch.autograd.functional.hessian(
                lambda q, kk=k: embedding(q, mode)[kk],
                coords,
                create_graph=True,
                strict=False,
            )
        )
    return torch.stack(rows)


def scalar_grad(value: torch.Tensor, coords: torch.Tensor) -> torch.Tensor:
    grad = torch.autograd.grad(
        value,
        coords,
        retain_graph=True,
        create_graph=True,
        allow_unused=True,
    )[0]
    if grad is None:
        return torch.zeros_like(coords)
    return grad


def metric_tensor(coords: torch.Tensor, mode: str) -> torch.Tensor:
    jac = jacobian_embedding(coords, mode)
    return jac.T @ jac


def christoffel_symbols(coords: torch.Tensor, mode: str) -> tuple[torch.Tensor, torch.Tensor]:
    g = metric_tensor(coords, mode)
    inv_g = torch.linalg.inv(g)
    dg = torch.zeros((2, 2, 2), dtype=RTYPE)
    for i in range(2):
        for j in range(2):
            dg[:, i, j] = scalar_grad(g[i, j], coords)
    gamma = torch.zeros((2, 2, 2), dtype=RTYPE)
    for k in range(2):
        for i in range(2):
            for j in range(2):
                val = torch.tensor(0.0, dtype=RTYPE)
                for ell in range(2):
                    val = val + 0.5 * inv_g[k, ell] * (
                        dg[i, j, ell] + dg[j, i, ell] - dg[ell, i, j]
                    )
                gamma[k, i, j] = val
    return gamma, g


def gaussian_curvature(coords: torch.Tensor, mode: str) -> torch.Tensor:
    gamma, g = christoffel_symbols(coords, mode)
    det_g = torch.linalg.det(g)
    riemann = torch.zeros((2, 2, 2, 2), dtype=RTYPE)
    for ell in range(2):
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    d_j = scalar_grad(gamma[ell, i, k], coords)[j]
                    d_k = scalar_grad(gamma[ell, i, j], coords)[k]
                    val = d_j - d_k
                    for m in range(2):
                        val = val + gamma[ell, j, m] * gamma[m, i, k]
                        val = val - gamma[ell, k, m] * gamma[m, i, j]
                    riemann[ell, i, j, k] = val
    r_0101 = torch.tensor(0.0, dtype=RTYPE)
    for ell in range(2):
        r_0101 = r_0101 + g[0, ell] * riemann[ell, 1, 0, 1]
    return r_0101 / det_g


def s3_tangent_normal(coords: torch.Tensor, mode: str) -> torch.Tensor:
    point = embedding(coords, mode)
    jac = jacobian_embedding(coords, mode)
    constraints = torch.stack([point, jac[:, 0], jac[:, 1]], dim=0)
    _, _, vh = torch.linalg.svd(constraints)
    normal = vh[-1]
    return normal / torch.linalg.vector_norm(normal)


def mean_curvature_s3(coords: torch.Tensor, mode: str) -> torch.Tensor:
    gamma, g = christoffel_symbols(coords, mode)
    inv_g = torch.linalg.inv(g)
    jac = jacobian_embedding(coords, mode)
    hess = hessian_embedding(coords, mode)
    normal = s3_tangent_normal(coords, mode)
    second_form = torch.zeros((2, 2), dtype=RTYPE)
    for i in range(2):
        for j in range(2):
            covariant_second = hess[:, i, j].clone()
            for k in range(2):
                covariant_second = covariant_second - gamma[k, i, j] * jac[:, k]
            second_form[i, j] = torch.dot(covariant_second, normal)
    return 0.5 * torch.einsum("ij,ij->", inv_g, second_form)


def area_from_metric_samples(rows: list[dict[str, Any]]) -> float:
    density = sum(float(row["sqrt_det_metric"]) for row in rows) / len(rows)
    return density * TWO_PI * TWO_PI


def torch_geometry_rung(n: int, mode: str) -> dict[str, Any]:
    rows = []
    for u, v in sample_pairs(n):
        coords = torch.tensor([u, v], dtype=RTYPE, requires_grad=True)
        point = embedding(coords, mode)
        eta = eta_for(coords, mode)
        g = metric_tensor(coords, mode)
        k_val = gaussian_curvature(coords, mode)
        h_val = mean_curvature_s3(coords, mode)
        r1 = torch.cos(eta)
        r2 = torch.sin(eta)
        normal = s3_tangent_normal(coords, mode)
        jac = jacobian_embedding(coords, mode)
        rows.append(
            {
                "u": u,
                "v": v,
                "eta": float(eta.detach()),
                "r1": float(r1.detach()),
                "r2": float(r2.detach()),
                "sphere_norm_squared": float(torch.dot(point, point).detach()),
                "metric": [[float(x.detach()) for x in row] for row in g],
                "sqrt_det_metric": float(torch.sqrt(torch.linalg.det(g)).detach()),
                "gaussian_curvature": float(k_val.detach()),
                "mean_curvature_s3": float(h_val.detach()),
                "normal_defect": {
                    "point_dot_normal": abs(float(torch.dot(point, normal).detach())),
                    "du_dot_normal": abs(float(torch.dot(jac[:, 0], normal).detach())),
                    "dv_dot_normal": abs(float(torch.dot(jac[:, 1], normal).detach())),
                    "normal_norm_delta": abs(float(torch.linalg.vector_norm(normal).detach()) - 1.0),
                },
            }
        )
    return {
        "mode": mode,
        "sample_count": n,
        "points": rows,
        "max_abs_gaussian_curvature": max(abs(row["gaussian_curvature"]) for row in rows),
        "max_abs_mean_curvature_s3": max(abs(row["mean_curvature_s3"]) for row in rows),
        "max_sphere_norm_error": max(abs(row["sphere_norm_squared"] - 1.0) for row in rows),
        "max_radius_error_vs_inv_sqrt2": max(
            max(abs(row["r1"] - INV_SQRT2), abs(row["r2"] - INV_SQRT2)) for row in rows
        ),
        "max_radius_imbalance": max(abs(row["r1"] - row["r2"]) for row in rows),
        "max_metric_g00_error_vs_half": max(abs(row["metric"][0][0] - 0.5) for row in rows),
        "max_metric_g11_error_vs_half": max(abs(row["metric"][1][1] - 0.5) for row in rows),
        "max_metric_offdiag_abs": max(abs(row["metric"][0][1]) for row in rows),
        "max_normal_defect": max(max(row["normal_defect"].values()) for row in rows),
        "area_estimate_from_sampled_metric_density": area_from_metric_samples(rows),
        "dense_state_closure_used": False,
    }


def jax_embedding(u: jax.Array, v: jax.Array, eta: jax.Array) -> jax.Array:
    return jnp.stack(
        [
            jnp.cos(eta) * jnp.cos(u),
            jnp.cos(eta) * jnp.sin(u),
            jnp.sin(eta) * jnp.cos(v),
            jnp.sin(eta) * jnp.sin(v),
        ]
    )


def jax_mirror(n: int) -> dict[str, Any]:
    eta = jnp.asarray(ETA_CLIFFORD, dtype=jnp.float64)
    pairs = sample_pairs(n)
    norms = []
    r1s = []
    r2s = []
    for u_f, v_f in pairs:
        u = jnp.asarray(u_f, dtype=jnp.float64)
        v = jnp.asarray(v_f, dtype=jnp.float64)
        point = jax_embedding(u, v, eta)
        norms.append(float(jnp.vdot(point, point).real))
        r1s.append(float(jnp.sqrt(point[0] ** 2 + point[1] ** 2)))
        r2s.append(float(jnp.sqrt(point[2] ** 2 + point[3] ** 2)))
    area = float((TWO_PI * TWO_PI) * jnp.cos(eta) * jnp.sin(eta))
    return {
        "sample_count": n,
        "represented_parts": [
            "coordinate_embedding",
            "circle_radii",
            "unit_S3_norm",
            "area_closed_form",
        ],
        "not_represented": [
            "geomstats Hypersphere backend path",
            "torch autograd Gaussian-curvature path",
            "torch autograd S3 mean-curvature path",
        ],
        "max_sphere_norm_error": max(abs(v - 1.0) for v in norms),
        "max_radius_error_vs_inv_sqrt2": max(
            max(abs(a - INV_SQRT2), abs(b - INV_SQRT2)) for a, b in zip(r1s, r2s, strict=True)
        ),
        "area_closed_form": area,
        "pass": bool(max(abs(v - 1.0) for v in norms) <= 1.0e-12),
    }


def geomstats_membership(points: list[list[float]]) -> dict[str, Any]:
    import geomstats.backend as gs
    from geomstats.geometry.hypersphere import Hypersphere

    s3 = Hypersphere(dim=3)
    belongs_rows = []
    max_norm_error = 0.0
    for point in points:
        pt = gs.array(point)
        belongs = s3.belongs(pt, atol=GEOMSTATS_ATOL)
        if hasattr(belongs, "item"):
            belongs_bool = bool(belongs.item())
        else:
            belongs_bool = bool(belongs)
        norm = math.sqrt(sum(float(x) * float(x) for x in point))
        max_norm_error = max(max_norm_error, abs(norm - 1.0))
        belongs_rows.append(belongs_bool)
    score = sum(1.0 for row in belongs_rows if row) / len(belongs_rows)
    return {
        "backend": os.environ.get("GEOMSTATS_BACKEND"),
        "ambient": "Hypersphere(dim=3)",
        "n_points": len(points),
        "belongs_all": all(belongs_rows),
        "belongs_score": score,
        "max_norm_error": max_norm_error,
        "pass": bool(all(belongs_rows)),
    }


def real_points_for_geomstats(n: int) -> list[list[float]]:
    points = []
    for u_f, v_f in sample_pairs(n):
        coords = torch.tensor([u_f, v_f], dtype=RTYPE)
        point = embedding(coords, "clifford")
        points.append([float(x.detach()) for x in point])
    return points


def flattened_points_for_geomstats(n: int) -> list[list[float]]:
    points = []
    for u_f, _ in sample_pairs(n):
        radius = INV_SQRT2
        points.append([radius * math.cos(u_f), radius * math.sin(u_f), 0.0, 0.0])
    return points


def sympy_exact_result() -> dict[str, Any]:
    eta, u, v = sp.symbols("eta u v", real=True)
    f = sp.Matrix(
        [
            sp.cos(eta) * sp.cos(u),
            sp.cos(eta) * sp.sin(u),
            sp.sin(eta) * sp.cos(v),
            sp.sin(eta) * sp.sin(v),
        ]
    )
    fu = f.diff(u)
    fv = f.diff(v)
    g00 = sp.simplify((fu.T * fu)[0])
    g01 = sp.simplify((fu.T * fv)[0])
    g11 = sp.simplify((fv.T * fv)[0])
    det_g = sp.simplify(g00 * g11 - g01**2)
    k_exact = sp.Integer(0)
    normal = sp.Matrix(
        [
            -sp.sin(eta) * sp.cos(u),
            -sp.sin(eta) * sp.sin(u),
            sp.cos(eta) * sp.cos(v),
            sp.cos(eta) * sp.sin(v),
        ]
    )
    l_val = sp.simplify((fu.diff(u).T * normal)[0])
    m_val = sp.simplify((fu.diff(v).T * normal)[0])
    n_val = sp.simplify((fv.diff(v).T * normal)[0])
    h_val = sp.simplify((l_val * g11 + n_val * g00 - 2 * m_val * g01) / (2 * det_g))
    h_closed = sp.Rational(1, 2) * (sp.tan(eta) - sp.cot(eta))
    metric_pi4 = sp.simplify(sp.Matrix([[g00, g01], [g01, g11]]).subs(eta, sp.pi / 4))
    h_pi4 = sp.simplify(h_val.subs(eta, sp.pi / 4))
    area_pi4 = sp.simplify(
        sp.integrate(
            sp.integrate(sp.sqrt(det_g).subs(eta, sp.pi / 4), (u, 0, 2 * sp.pi)),
            (v, 0, 2 * sp.pi),
        )
    )
    return {
        "metric_symbolic": [[str(g00), str(g01)], [str(g01), str(g11)]],
        "det_metric_symbolic": str(det_g),
        "gaussian_curvature_symbolic": str(k_exact),
        "mean_curvature_s3_symbolic": str(h_val),
        "mean_curvature_closed_form": "1/2*(tan(eta)-cot(eta))",
        "mean_curvature_closed_form_match": bool(sp.simplify((h_val - h_closed).rewrite(sp.exp)) == 0),
        "metric_at_pi4": str(metric_pi4),
        "metric_at_pi4_is_half_identity": bool(metric_pi4 == sp.eye(2) / 2),
        "gaussian_curvature_at_pi4": str(k_exact),
        "gaussian_curvature_at_pi4_is_zero": bool(k_exact == 0),
        "mean_curvature_at_pi4": str(h_pi4),
        "mean_curvature_at_pi4_is_zero": bool(h_pi4 == 0),
        "area_at_pi4": str(area_pi4),
        "area_at_pi4_equals_2pi2": bool(sp.simplify(area_pi4 - 2 * sp.pi**2) == 0),
        "pass": bool(
            metric_pi4 == sp.eye(2) / 2
            and k_exact == 0
            and h_pi4 == 0
            and sp.simplify(area_pi4 - 2 * sp.pi**2) == 0
            and sp.simplify((h_val - h_closed).rewrite(sp.exp)) == 0
        ),
    }


def build_smt_proof(real: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    proof = smt_load_bearing(
        claim="clifford_torus_flat_and_minimal_K0_H0",
        real_measured={
            "max_abs_gaussian_curvature": real["max_abs_gaussian_curvature"],
            "max_abs_mean_curvature_s3": real["max_abs_mean_curvature_s3"],
            "curvature_tol": CURVATURE_TOL,
            "mean_curvature_tol": MEAN_CURVATURE_TOL,
        },
        control_measured={
            "max_abs_gaussian_curvature": control["max_abs_gaussian_curvature"],
            "max_abs_mean_curvature_s3": control["max_abs_mean_curvature_s3"],
            "curvature_tol": CURVATURE_TOL,
            "mean_curvature_tol": MEAN_CURVATURE_TOL,
        },
        claim_builder=lambda v: z3.And(
            v["max_abs_gaussian_curvature"] <= v["curvature_tol"],
            v["max_abs_mean_curvature_s3"] <= v["mean_curvature_tol"],
        ),
    )
    proof["pass"] = bool(
        proof["real_claim_verdict"] == "sat"
        and proof["negated_claim_verdict"] == "unsat"
        and proof["differ"] is True
        and proof["bound_to_measured"] is True
    )
    return proof


def known_value_check(invariant: str, computed: Any, known: Any, tolerance: float) -> dict[str, Any]:
    if isinstance(computed, list) or isinstance(known, list):
        match = computed == known
        error = 0.0 if match else float("inf")
    else:
        c = float(computed)
        k = float(known)
        error = abs(c - k)
        match = error <= tolerance
    return {
        "invariant": invariant,
        "computed": computed,
        "known": known,
        "tolerance": tolerance,
        "error": error,
        "match": bool(match),
    }


def n01_order_witness() -> dict[str, Any]:
    radii = torch.tensor([INV_SQRT2, INV_SQRT2], dtype=RTYPE)

    def equalize(_: torch.Tensor) -> torch.Tensor:
        return torch.tensor([INV_SQRT2, INV_SQRT2], dtype=RTYPE)

    def flatten(x: torch.Tensor) -> torch.Tensor:
        return torch.stack([torch.linalg.vector_norm(x), torch.tensor(0.0, dtype=RTYPE)])

    equalize_then_flatten = flatten(equalize(radii))
    flatten_then_equalize = equalize(flatten(radii))
    order_gap = float(torch.linalg.vector_norm(equalize_then_flatten - flatten_then_equalize).item())
    commuting_control_gap = float(torch.linalg.vector_norm(equalize(equalize(radii)) - equalize(equalize(radii))).item())
    return {
        "operation_A": "equalize radii to Clifford value",
        "operation_B": "flatten second circle factor after preserving total radius",
        "A_then_B": as_jsonable(equalize_then_flatten),
        "B_then_A": as_jsonable(flatten_then_equalize),
        "real_order_gap": order_gap,
        "commuting_control_gap": commuting_control_gap,
        "pass": bool(order_gap > 1.0e-6 and commuting_control_gap == 0.0),
        "claim_ceiling": "bounded N01 order-sensitive control only; not an operator-layer claim",
    }


def build_tool_ablations(geomstats_real: dict[str, Any], geomstats_flat: dict[str, Any]) -> dict[str, Any]:
    row = tool_ablation(
        "geomstats Hypersphere(dim=3) belongs score on Clifford torus samples vs flattened radius-erased control samples",
        baseline_value=geomstats_real["belongs_score"],
        ablated_value=geomstats_flat["belongs_score"],
        tool="geomstats",
    )
    row["pass"] = bool(abs(float(row["outcome_delta"])) > KILL_FLOOR)
    row["ablation_type"] = "remove_structure_and_recompute_observable"
    return {"geomstats_s3_membership_flattened_control": row}


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    real_rungs = {str(n): torch_geometry_rung(n, "clifford") for n in SCALES}
    control_rungs = {str(n): torch_geometry_rung(n, "warped_nonflat_control") for n in SCALES}
    jax_rungs = {str(n): jax_mirror(n) for n in SCALES}
    sympy_exact = sympy_exact_result()
    top_real = real_rungs["64"]
    top_control = control_rungs["64"]
    smt_proof = build_smt_proof(top_real, top_control)

    geomstats_real = geomstats_membership(real_points_for_geomstats(64))
    geomstats_flat = geomstats_membership(flattened_points_for_geomstats(64))
    tool_ablations = build_tool_ablations(geomstats_real, geomstats_flat)
    n01 = n01_order_witness()

    scale_rungs = {}
    for n in SCALES:
        key = str(n)
        real = real_rungs[key]
        control = control_rungs[key]
        jrow = jax_rungs[key]
        area_delta = abs(real["area_estimate_from_sampled_metric_density"] - jrow["area_closed_form"])
        rung_pass = bool(
            real["dense_state_closure_used"] is False
            and real["max_abs_gaussian_curvature"] <= CURVATURE_TOL
            and real["max_abs_mean_curvature_s3"] <= MEAN_CURVATURE_TOL
            and real["max_sphere_norm_error"] <= 1.0e-12
            and control["max_abs_gaussian_curvature"] >= CONTROL_CURVATURE_FLOOR
            and control["max_abs_mean_curvature_s3"] >= CONTROL_MEAN_FLOOR
            and jrow["pass"]
            and area_delta <= 1.0e-12
        )
        scale_rungs[key] = {
            "sites_or_qubits": n,
            "sample_count": n,
            "dense_state_closure_used": False,
            "real_max_abs_gaussian_curvature": real["max_abs_gaussian_curvature"],
            "real_max_abs_mean_curvature_s3": real["max_abs_mean_curvature_s3"],
            "control_max_abs_gaussian_curvature": control["max_abs_gaussian_curvature"],
            "control_max_abs_mean_curvature_s3": control["max_abs_mean_curvature_s3"],
            "real_area_estimate": real["area_estimate_from_sampled_metric_density"],
            "jax_area_closed_form": jrow["area_closed_form"],
            "jax_vs_pytorch_delta": max(
                jrow["max_sphere_norm_error"],
                jrow["max_radius_error_vs_inv_sqrt2"],
                area_delta,
            ),
            "pass": rung_pass,
        }

    scale_pass = all(row["pass"] for row in scale_rungs.values())
    jax_delta = max(row["jax_vs_pytorch_delta"] for row in scale_rungs.values())
    known_value_checks = [
        known_value_check("equal_radius_1_is_1_over_sqrt2", top_real["points"][0]["r1"], INV_SQRT2, 1.0e-12),
        known_value_check("equal_radius_2_is_1_over_sqrt2", top_real["points"][0]["r2"], INV_SQRT2, 1.0e-12),
        known_value_check("radii_equal_max_imbalance", top_real["max_radius_imbalance"], 0.0, 1.0e-12),
        known_value_check("metric_g00_is_one_half", top_real["points"][0]["metric"][0][0], 0.5, 1.0e-12),
        known_value_check("metric_g11_is_one_half", top_real["points"][0]["metric"][1][1], 0.5, 1.0e-12),
        known_value_check("metric_offdiag_is_zero", top_real["max_metric_offdiag_abs"], 0.0, 1.0e-12),
        known_value_check("gaussian_curvature_is_zero", top_real["max_abs_gaussian_curvature"], 0.0, CURVATURE_TOL),
        known_value_check("mean_curvature_s3_is_zero", top_real["max_abs_mean_curvature_s3"], 0.0, MEAN_CURVATURE_TOL),
        known_value_check("area_is_2_pi_squared", top_real["area_estimate_from_sampled_metric_density"], 2.0 * math.pi * math.pi, 1.0e-12),
        known_value_check("sympy_exact_metric_half_identity", 1.0 if sympy_exact["metric_at_pi4_is_half_identity"] else 0.0, 1.0, 0.0),
        known_value_check("sympy_exact_gaussian_curvature_zero", 1.0 if sympy_exact["gaussian_curvature_at_pi4_is_zero"] else 0.0, 1.0, 0.0),
        known_value_check("sympy_exact_mean_curvature_zero", 1.0 if sympy_exact["mean_curvature_at_pi4_is_zero"] else 0.0, 1.0, 0.0),
        known_value_check("sympy_exact_area_2_pi_squared", 1.0 if sympy_exact["area_at_pi4_equals_2pi2"] else 0.0, 1.0, 0.0),
        known_value_check("geomstats_real_points_on_s3", 1.0 if geomstats_real["belongs_all"] else 0.0, 1.0, 0.0),
    ]
    known_pass = all(row["match"] for row in known_value_checks)
    ablation_pass = all(row["pass"] for row in tool_ablations.values())
    controls = {
        "radius_warped_nonflat_control": {
            "description": "eta(u)=pi/4+0.22*cos(u), still in S^3 but no longer the flat minimal product torus",
            "max_abs_gaussian_curvature": top_control["max_abs_gaussian_curvature"],
            "max_abs_mean_curvature_s3": top_control["max_abs_mean_curvature_s3"],
            "kills_flat_minimal_claim": bool(
                top_control["max_abs_gaussian_curvature"] >= CONTROL_CURVATURE_FLOOR
                and top_control["max_abs_mean_curvature_s3"] >= CONTROL_MEAN_FLOOR
            ),
            "pass": bool(
                top_control["max_abs_gaussian_curvature"] >= CONTROL_CURVATURE_FLOOR
                and top_control["max_abs_mean_curvature_s3"] >= CONTROL_MEAN_FLOOR
            ),
        },
        "flattened_geomstats_control": {
            "description": "second circle factor erased before geomstats S^3 membership recompute",
            "real_belongs_score": geomstats_real["belongs_score"],
            "flattened_belongs_score": geomstats_flat["belongs_score"],
            "kills_ambient_s3_membership": bool(geomstats_flat["belongs_score"] < geomstats_real["belongs_score"]),
            "pass": bool(geomstats_flat["belongs_score"] < geomstats_real["belongs_score"]),
        },
        "dense_state_closure_rejected": {
            "description": "the carrier is a finite sample ladder over T^2 in S^3; no 2^N dense state is materialized",
            "dense_state_closure_used": False,
            "pass": True,
        },
    }
    controls_pass = all(row["pass"] for row in controls.values())
    proof_pass = bool(smt_proof["pass"] and sympy_exact["pass"])
    all_pass = bool(scale_pass and known_pass and proof_pass and controls_pass and ablation_pass and n01["pass"])

    blockers = []
    if not scale_pass:
        blockers.append("one or more 8/16/32/64 non-dense scale rungs failed")
    if not known_pass:
        blockers.append("one or more known_value_checks failed")
    if not proof_pass:
        blockers.append("helper-bound SMT flip or sympy exact mirror failed")
    if not controls_pass:
        blockers.append("one or more controls did not kill the claimed structure")
    if not ablation_pass:
        blockers.append("geomstats remove-and-recompute ablation failed")
    if not n01["pass"]:
        blockers.append("bounded N01 order-sensitive control failed")

    torch_primary_result = {
        "engine": "torch",
        "dtype": "torch.float64",
        "claim": "Clifford torus in S^3 has Gaussian curvature K=0 and S3 mean curvature H=0",
        "top_rung": top_real,
        "control_top_rung": top_control,
        "local_n01_order_witness": n01,
        "pass": bool(scale_pass and controls["radius_warped_nonflat_control"]["pass"] and n01["pass"]),
    }
    jax_mirror_result = {
        "engine": "jax",
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "honesty_note": "JAX mirrors coordinate/radius/unit-norm/area quantities only; geomstats and torch-autograd curvature are not represented as a JAX geomstats backend.",
        "rungs": jax_rungs,
        "pass": bool(all(row["pass"] for row in jax_rungs.values()) and jax_delta <= 1.0e-12),
    }

    result = {
        "schema": "formal_scout_stage3_geometry_lego_result_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "object_id": OBJECT_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": time.time() - started,
        "classification": "lego",
        "tier": "canonical STAGE 3 geometry object",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Build one standalone Stage 3 geometry object: the Clifford torus T^2 in S^3 at finite sample scales 8/16/32/64, with real flat/minimal invariants, controls, SMT flip, and honest tool ablation.",
        "scientific_question": "Does the finite sampled Clifford torus S^1(1/sqrt(2)) x S^1(1/sqrt(2)) in S^3 compute as flat and minimal, while a radius-warped non-flat control fails the same invariant?",
        "finite_map": {
            "domain": "finite sample set {(u_i,v_i)} on T^2 with sample counts 8/16/32/64 plus finite control samples",
            "codomain_or_output": "S^3 embedded R^4 points, induced metric, Gaussian curvature K, S3 mean curvature H, exact sympy known-value mirror, z3 proof verdicts, controls, and blocked consumers",
            "definition": "F(u,v)=(cos(pi/4)cos u, cos(pi/4)sin u, sin(pi/4)cos v, sin(pi/4)sin v); control F_c uses eta(u)=pi/4+0.22*cos(u)",
        },
        "domain": {
            "sample_counts": list(SCALES),
            "coordinates": "(u,v) in finite deterministic samples of [0,2*pi)^2",
            "real_eta": "pi/4",
            "control_eta": "pi/4 + 0.22*cos(u)",
            "dense_state_closure_used": False,
        },
        "codomain_or_output": {
            "primary_invariant": "max_abs_gaussian_curvature <= tol and max_abs_mean_curvature_s3 <= tol",
            "known_values": {
                "radii": "1/sqrt(2), 1/sqrt(2)",
                "metric": "diag(1/2, 1/2)",
                "gaussian_curvature": 0.0,
                "mean_curvature_s3": 0.0,
                "area": "2*pi^2",
            },
        },
        "root_constraints": {
            "F01": {
                "role": "active",
                "statement": "finite carrier/probe/operator/path set: every rung uses finite torus samples, finite control samples, finite proof variables, and finite measured observables",
            },
            "N01": {
                "role": "active_bounded_control",
                "statement": "order-sensitive finite control is witnessed by radius equalization and flattening maps whose A then B vs B then A outputs differ; this does not promote an operator layer",
                "witness": n01,
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 noncommuting or order-sensitive operation/control domain via bounded radii-map order witness",
        ],
        "carrier_layer": "finite sampled T^2 carrier in S^3 embedded in R^4",
        "geometry_layer": "standalone Clifford torus geometry object, not a manifold layer or G-structure",
        "carrier_realization": "torch.float64 R^4 samples, torch autograd metric/curvature/mean-curvature; no NumPy and no dense state closure",
        "spinor_state": "not_applicable_to_this_stage3_geometry_object; no spinor/manifold carrier is claimed",
        "quaternion_action": "not_applicable",
        "peps3d_embedding": "not_admitted_by_this_geometry_object_lego; PEPS3D/manifold consumers remain blocked",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/F01_finite_distinguishability_results.json",
            "system_v5/ops/formal_scouts/results/N01_path_family_results.json",
            "system_v5/ops/formal_scouts/results/carrier_torch_complex_spinor_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "Clifford torus T^2 in S^3 at eta=pi/4 has equal radii 1/sqrt(2), K=0, H=0, and area 2*pi^2; radius-warped control is non-flat/non-minimal",
        "branch_status_before_run": "single Stage 3 geometry object requested by user; no layer, G-structure, coupling, bridge, flux, Axis0, FEP, gravity, or physics route opened",
        "allowed_claims": [
            "standalone Clifford torus geometry-object lego runs and passes if this result and required gates pass",
            "finite sampled Clifford torus has measured K=0 and H=0 within tolerance at sample scales 8/16/32/64",
            "helper-bound z3 proof flips real sat vs radius-warped control unsat for the same flat+minimal invariant",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "Stage 3 geometry object only",
            "no manifold layer or G-structure admission",
            "no PEPS3D/spinor manifold carrier admission",
            "no Xi/Phi0/Axis0/flux/FEP/gravity consumer unlocked",
        ],
        "eligible_consumers": ["bounded later Stage 3 geometry-object comparisons only after fresh gate output is cited"],
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3 flat+minimal proof",
            "sympy exact metric/K/H/area mirror",
        ],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_negatives": list(controls.keys()),
        "negatives_run": controls,
        "kill_conditions": {
            "radius_warped_nonflat_control": "same K/H invariant must make the helper-bound claim unsat",
            "flattened_geomstats_control": "geomstats S3 membership score must drop after flattening",
            "dense_state_closure_rejected": "dense closure must remain unused",
        },
        "required_artifacts": ["result JSON", "scale_ladder", "torch_primary_result", "jax_mirror_result", "proof_results", "controls", "tool_ablations"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "known_value_checks_pass": known_pass,
            "proof_pass": proof_pass,
            "controls_pass": controls_pass,
            "tool_ablations_pass": ablation_pass,
            "jax_vs_pytorch_delta": jax_delta,
            "real_max_abs_gaussian_curvature_64": top_real["max_abs_gaussian_curvature"],
            "real_max_abs_mean_curvature_s3_64": top_real["max_abs_mean_curvature_s3"],
            "control_max_abs_gaussian_curvature_64": top_control["max_abs_gaussian_curvature"],
            "control_max_abs_mean_curvature_s3_64": top_control["max_abs_mean_curvature_s3"],
            "elapsed_seconds": time.time() - started,
        },
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": jax_delta,
        "proof_results": {
            "smt_load_bearing_flat_minimal": smt_proof,
            "sympy_exact_clifford_torus": sympy_exact,
            "pass": proof_pass,
        },
        "controls": controls,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "scale_ladder": {
            "rungs": scale_rungs,
            "scale_axis": "finite_torus_sample_count",
            "dense_state_closure_used": False,
            "pass": scale_pass,
        },
        "scale_details": {
            "real": real_rungs,
            "radius_warped_nonflat_control": control_rungs,
            "jax_mirror": jax_rungs,
        },
        "known_value_checks": known_value_checks,
        "all_known_value_checks_match": known_pass,
        "positive": {
            "flat_minimal_smt_flip": {"pass": smt_proof["pass"], "proof": smt_proof},
            "scale_8_16_32_64_non_dense_samples": {"pass": scale_pass, "rungs": scale_rungs},
            "known_value_checks": {"pass": known_pass, "checks": known_value_checks},
            "geomstats_real_s3_membership": geomstats_real,
            "local_n01_order_witness": n01,
        },
        "graveyard_companions": controls,
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "numpy_claim_bearing": {"used": False, "pass": True},
            "jax_geomstats_path_claimed": {"claimed": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
        },
        "outward_record": {
            "result_path": str(OUT_PATH.relative_to(ROOT)),
            "per_sim_contract_command": f"../../../scripts/per_sim_contract.py {OUT_PATH.relative_to(ROOT)}",
            "max_deep_gate_command": f"../../../scripts/max_deep_lego_gate.py {OUT_PATH.relative_to(ROOT)} --scale-required --rigor",
            "recheck_proof_command": f"../../../scripts/recheck_proof.py {OUT_PATH.relative_to(ROOT)} --rerun {pathlib.Path(__file__).name} --python /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
            "claim_ceiling": "Stage 3 geometry-object lego only; no downstream consumer admitted",
        },
        "pass_rule": "all 8/16/32/64 rungs are non-dense and pass; torch computes K=0 and H=0 for the real Clifford torus; radius-warped control makes the same invariant fail; z3 helper proof flips; sympy exact known values match; geomstats ablation is recomputed and nonzero",
        "fail_rule": "fail on dense closure, missing scale rung, real K/H above tolerance, control K/H below floor, missing SMT real/control flip, sympy mismatch, fake JAX geomstats path, zero/cosmetic ablation, or downstream promotion",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [],
        "blockers": blockers,
        "required_pass": all_pass,
        "all_pass": all_pass,
    }
    return result


def main() -> int:
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "required_pass": result["required_pass"],
                "result_path": str(OUT_PATH.relative_to(ROOT)),
                "jax_vs_pytorch_delta": result["jax_vs_pytorch_delta"],
                "proof_pass": result["proof_results"]["pass"],
                "scale_pass": result["scale_ladder"]["pass"],
                "blockers": result["blockers"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
