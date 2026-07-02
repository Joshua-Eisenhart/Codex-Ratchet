#!/usr/bin/env python3
"""Standalone Stage 3 S^3 sphere geometry lego.

Finite map:
    S3_samples_N -> unit-norm certificate, S^3 geodesic distances, and an
    order-sensitive finite rotation witness.

This is geometry-object work only. It does not admit manifold layers,
G-structures, PEPS3D, Xi/Phi0/Axis0, flux, FEP, gravity, or bridge consumers.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("NUMBA_DISABLE_CACHE", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import torch
import z3
from geomstats.geometry.hypersphere import Hypersphere
import geomstats.backend as gs

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "sim_geom_s3_sphere_probe"
OBJECT_ID = "s3_sphere"
OUT_PATH = RESULT_DIR / f"{OBJECT_ID}_results.json"

RTYPE = torch.float64
EPS = 1.0e-9
SCALES = (8, 16, 32, 64)
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY claim-bearing finite S^3 carrier, unit-norm invariant, off-sphere control, order-sensitive rotation witness, and scale ladder.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 parity mirror for representable unit norms, geodesic arccos law, off-sphere control, and rotation-order gap; no geomstats/JAX backend is claimed.",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING torch-backend Hypersphere(dim=3) belongs() and metric.dist() for the S^3 geodesic observable.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING exact closed-form S^3 geodesic check: arccos(<e0,e1>) = pi/2 and unit parameterization norm equals 1.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING helper-bound SMT flip on the measured max |norm^2-1| invariant, real S^3 samples vs off-sphere control.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not used for claim-bearing computation.",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "Not requested for this single-tool SMT row; z3 carries the structural unit-norm flip.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "geomstats": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "numpy": "None",
    "cvc5": "None",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
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


def canonical_points() -> torch.Tensor:
    return torch.eye(4, dtype=RTYPE)


def parametric_point(k: int, n: int) -> torch.Tensor:
    """Deterministic S^3 point in R^4 from angular coordinates."""
    a = torch.tensor((k + 1) * math.pi / (n + 1), dtype=RTYPE)
    b = torch.tensor((2 * k + 1) * math.pi / (2 * n + 1), dtype=RTYPE)
    c = torch.tensor((3 * k + 1) * math.pi / (3 * n + 2), dtype=RTYPE)
    return torch.stack(
        (
            torch.cos(a),
            torch.sin(a) * torch.cos(b),
            torch.sin(a) * torch.sin(b) * torch.cos(c),
            torch.sin(a) * torch.sin(b) * torch.sin(c),
        )
    ).to(RTYPE)


def s3_points_torch(n: int) -> torch.Tensor:
    points = [point for point in canonical_points()]
    for k in range(n - len(points)):
        points.append(parametric_point(k, n))
    raw = torch.stack(points[:n]).to(RTYPE)
    return raw / torch.linalg.vector_norm(raw, dim=1, keepdim=True)


def off_sphere_control(points: torch.Tensor) -> torch.Tensor:
    scale = torch.linspace(1.125, 1.625, steps=points.shape[0], dtype=RTYPE).unsqueeze(1)
    flattened = points.clone()
    flattened[:, 3] = 0.0
    return flattened * scale


def norm_sq_torch(points: torch.Tensor) -> torch.Tensor:
    return torch.sum(points.to(RTYPE) * points.to(RTYPE), dim=1)


def max_norm_error_torch(points: torch.Tensor) -> float:
    return float(torch.max(torch.abs(norm_sq_torch(points) - 1.0)).item())


def geodesic_torch(a: torch.Tensor, b: torch.Tensor) -> float:
    dot = torch.clamp(torch.dot(a.to(RTYPE), b.to(RTYPE)), -1.0, 1.0)
    return float(torch.arccos(dot).item())


def chord_torch(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(a.to(RTYPE) - b.to(RTYPE)).item())


def geomstats_result(points: torch.Tensor) -> dict[str, Any]:
    sphere = Hypersphere(dim=3)
    gs_points = gs.array(points.detach().cpu().tolist(), dtype=gs.float64)
    belongs = sphere.belongs(gs_points, atol=EPS)
    dist = sphere.metric.dist(gs_points[0], gs_points[1])
    pairwise = []
    for idx in range(min(4, points.shape[0] - 1)):
        pairwise.append(float(sphere.metric.dist(gs_points[idx], gs_points[idx + 1]).item()))
    belongs_all = bool(torch.all(belongs).item()) if isinstance(belongs, torch.Tensor) else bool(gs.all(belongs))
    return {
        "backend": gs.__name__,
        "hypersphere_dim": 3,
        "belongs_all": belongs_all,
        "distance_p0_p1": float(dist.item()),
        "pairwise_adjacent_sample": pairwise,
        "pass": bool(belongs_all and abs(float(dist.item()) - math.pi / 2.0) <= 1.0e-9),
        "jax_backend_claimed": False,
        "jax_backend_note": "geomstats is run with GEOMSTATS_BACKEND=pytorch; JAX mirror below recomputes only representable tensor formulas.",
    }


def jax_points_from_torch(points: torch.Tensor) -> jnp.ndarray:
    return jnp.asarray(points.detach().cpu().tolist(), dtype=jnp.float64)


def jax_rung(points: torch.Tensor, control: torch.Tensor, order_gap_torch: float) -> dict[str, Any]:
    p = jax_points_from_torch(points)
    c = jax_points_from_torch(control)
    norms = jnp.sum(p * p, axis=1)
    control_norms = jnp.sum(c * c, axis=1)
    p0p1 = jnp.arccos(jnp.clip(jnp.dot(p[0], p[1]), -1.0, 1.0))
    chord = jnp.linalg.norm(p[0] - p[1])
    order = jax_order_witness(p[4 if p.shape[0] > 4 else 0])
    order_gap = float(order["real_order_gap"])
    control_gap = float(order["commuting_control_gap"])
    return {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "max_norm_error": float(jnp.max(jnp.abs(norms - 1.0))),
        "control_max_norm_error": float(jnp.max(jnp.abs(control_norms - 1.0))),
        "distance_p0_p1_arccos": float(p0p1),
        "flat_chord_p0_p1": float(chord),
        "rotation_order_gap": order_gap,
        "commuting_control_gap": control_gap,
        "commuting_operator_commutator_norm": float(order["commuting_operator_commutator_norm"]),
        "delta_vs_torch_order_gap": abs(order_gap - order_gap_torch),
        "pass": bool(
            float(jnp.max(jnp.abs(norms - 1.0))) <= EPS
            and float(jnp.max(jnp.abs(control_norms - 1.0))) > EPS
            and abs(float(p0p1) - math.pi / 2.0) <= 1.0e-9
            and abs(order_gap - order_gap_torch) <= 1.0e-9
            and control_gap <= EPS
            and float(order["commuting_operator_commutator_norm"]) <= EPS
        ),
    }


def rotation_matrix(i: int, j: int, theta: float) -> torch.Tensor:
    mat = torch.eye(4, dtype=RTYPE)
    c = math.cos(theta)
    s = math.sin(theta)
    mat[i, i] = c
    mat[j, j] = c
    mat[i, j] = -s
    mat[j, i] = s
    return mat


def rotation_matrix_jax(i: int, j: int, theta: float) -> jnp.ndarray:
    mat = jnp.eye(4, dtype=jnp.float64)
    c = math.cos(theta)
    s = math.sin(theta)
    mat = mat.at[i, i].set(c)
    mat = mat.at[j, j].set(c)
    mat = mat.at[i, j].set(-s)
    mat = mat.at[j, i].set(s)
    return mat


def order_witness(points: torch.Tensor) -> dict[str, Any]:
    point = points[4 if points.shape[0] > 4 else 0]
    real_operators = ["R01(theta=0.37)", "R02(theta=-0.23)"]
    control_operators = ["R01(theta=0.37)", "R23(theta=0.41)"]
    a = rotation_matrix(0, 1, 0.37)
    b = rotation_matrix(0, 2, -0.23)
    ab = a @ (b @ point)
    ba = b @ (a @ point)
    c = rotation_matrix(0, 1, 0.37)
    d = rotation_matrix(2, 3, 0.41)
    cd = c @ (d @ point)
    dc = d @ (c @ point)
    gap = float(torch.linalg.vector_norm(ab - ba).item())
    control_gap = float(torch.linalg.vector_norm(cd - dc).item())
    real_commutator_norm = float(torch.linalg.vector_norm(a @ b - b @ a).item())
    commuting_commutator_norm = float(torch.linalg.vector_norm(c @ d - d @ c).item())
    norm_after_ab = float(torch.sum(ab * ab).item())
    norm_after_cd = float(torch.sum(cd * cd).item())
    return {
        "observable": "||A(Bp)-B(Ap)|| for finite R4 rotations preserving S^3; control recomputes the same observable with a commuting pair",
        "operators": real_operators,
        "commuting_control_operators": control_operators,
        "commuting_control_pair_is_distinct": control_operators[0] != control_operators[1],
        "commuting_control_reuses_same_observable": True,
        "real_order_gap": gap,
        "commuting_control_gap": control_gap,
        "real_operator_commutator_norm": real_commutator_norm,
        "commuting_operator_commutator_norm": commuting_commutator_norm,
        "norm_after_ordered_actions": norm_after_ab,
        "norm_after_commuting_control_actions": norm_after_cd,
        "pass": bool(
            gap > EPS
            and real_commutator_norm > EPS
            and control_gap <= EPS
            and commuting_commutator_norm <= EPS
            and control_operators[0] != control_operators[1]
            and abs(norm_after_ab - 1.0) <= EPS
            and abs(norm_after_cd - 1.0) <= EPS
        ),
    }


def jax_order_witness(point: jnp.ndarray) -> dict[str, jnp.ndarray]:
    a = rotation_matrix_jax(0, 1, 0.37)
    b = rotation_matrix_jax(0, 2, -0.23)
    c = rotation_matrix_jax(0, 1, 0.37)
    d = rotation_matrix_jax(2, 3, 0.41)
    return {
        "real_order_gap": jnp.linalg.norm(a @ (b @ point) - b @ (a @ point)),
        "commuting_control_gap": jnp.linalg.norm(c @ (d @ point) - d @ (c @ point)),
        "commuting_operator_commutator_norm": jnp.linalg.norm(c @ d - d @ c),
    }


def sympy_exact_result() -> dict[str, Any]:
    chi, theta, phi = sp.symbols("chi theta phi", real=True)
    coords = [
        sp.cos(chi),
        sp.sin(chi) * sp.cos(theta),
        sp.sin(chi) * sp.sin(theta) * sp.cos(phi),
        sp.sin(chi) * sp.sin(theta) * sp.sin(phi),
    ]
    norm_sq = sp.simplify(sum(c * c for c in coords))
    e0 = sp.Matrix([1, 0, 0, 0])
    e1 = sp.Matrix([0, 1, 0, 0])
    dot = sp.simplify(sum(e0[i] * e1[i] for i in range(4)))
    distance = sp.acos(dot)
    return {
        "tool": "sympy",
        "parameterization_norm_squared": str(norm_sq),
        "p0_p1_dot": str(dot),
        "p0_p1_geodesic_closed_form": str(distance),
        "p0_p1_geodesic_float": float(sp.N(distance, 30)),
        "pass": bool(sp.simplify(norm_sq - 1) == 0 and distance == sp.pi / 2),
    }


def smt_unit_norm_proof(real_error: float, control_error: float) -> dict[str, Any]:
    proof = smt_load_bearing(
        claim="all_finite_s3_points_have_unit_norm_squared",
        real_measured={"max_norm_sq_error": real_error, "eps": EPS},
        control_measured={"max_norm_sq_error": control_error, "eps": EPS},
        claim_builder=lambda v: v["max_norm_sq_error"] <= v["eps"],
    )
    proof["pass"] = bool(
        proof["real_claim_verdict"] == "sat"
        and proof["negated_claim_verdict"] == "unsat"
        and proof["differ"] is True
        and proof["bound_to_measured"] is True
    )
    return proof


def scale_rung(n: int) -> dict[str, Any]:
    points = s3_points_torch(n)
    control = off_sphere_control(points)
    geom = geomstats_result(points)
    order = order_witness(points)
    jax_mirror = jax_rung(points, control, order["real_order_gap"])
    norm_error = max_norm_error_torch(points)
    control_norm_error = max_norm_error_torch(control)
    torch_distance = geodesic_torch(points[0], points[1])
    flat_chord = chord_torch(points[0], points[1])
    p0p1_dot = float(torch.dot(points[0], points[1]).item())
    pass_rung = bool(
        norm_error <= EPS
        and control_norm_error > EPS
        and geom["pass"]
        and jax_mirror["pass"]
        and order["pass"]
        and abs(torch_distance - math.pi / 2.0) <= 1.0e-9
        and abs(p0p1_dot) <= EPS
    )
    return {
        "sites_or_qubits": n,
        "sample_count": n,
        "ambient_dimension": 4,
        "intrinsic_dimension": 3,
        "dense_state_closure_used": False,
        "torch_max_norm_sq_error": norm_error,
        "torch_control_max_norm_sq_error": control_norm_error,
        "torch_distance_p0_p1_arccos": torch_distance,
        "torch_flat_chord_p0_p1": flat_chord,
        "torch_dot_p0_p1": p0p1_dot,
        "geomstats": geom,
        "jax_mirror": jax_mirror,
        "order_witness": order,
        "pass": pass_rung,
    }


def build_known_value_checks(top: dict[str, Any], sympy_exact: dict[str, Any]) -> list[dict[str, Any]]:
    pi_over_2 = float(sympy_exact["p0_p1_geodesic_float"])
    return [
        {
            "invariant": "all sampled points satisfy ||x||^2 = 1",
            "computed": top["torch_max_norm_sq_error"],
            "known": "0 max norm-squared error",
            "match": bool(top["torch_max_norm_sq_error"] <= EPS),
        },
        {
            "invariant": "geomstats S^3 geodesic distance(e0,e1)",
            "computed": top["geomstats"]["distance_p0_p1"],
            "known": "sympy arccos(0)=pi/2",
            "known_computed_by_sympy": pi_over_2,
            "match": bool(abs(top["geomstats"]["distance_p0_p1"] - pi_over_2) <= 1.0e-9),
        },
        {
            "invariant": "torch arccos geodesic distance(e0,e1)",
            "computed": top["torch_distance_p0_p1_arccos"],
            "known": "sympy arccos(0)=pi/2",
            "known_computed_by_sympy": pi_over_2,
            "match": bool(abs(top["torch_distance_p0_p1_arccos"] - pi_over_2) <= 1.0e-9),
        },
        {
            "invariant": "JAX mirror arccos geodesic distance(e0,e1)",
            "computed": top["jax_mirror"]["distance_p0_p1_arccos"],
            "known": "sympy arccos(0)=pi/2",
            "known_computed_by_sympy": pi_over_2,
            "match": bool(abs(top["jax_mirror"]["distance_p0_p1_arccos"] - pi_over_2) <= 1.0e-9),
        },
        {
            "invariant": "flat chord distance differs from S^3 geodesic distance",
            "computed": {
                "geodesic": top["geomstats"]["distance_p0_p1"],
                "flat_chord": top["torch_flat_chord_p0_p1"],
            },
            "known": "for orthogonal unit vectors, geodesic=pi/2 and chord=sqrt(2)",
            "match": bool(abs(top["geomstats"]["distance_p0_p1"] - top["torch_flat_chord_p0_p1"]) > 1.0e-6),
        },
        {
            "invariant": "off-sphere flattened/scaled control violates ||x||^2 = 1",
            "computed": top["torch_control_max_norm_sq_error"],
            "known": "positive norm-squared error",
            "match": bool(top["torch_control_max_norm_sq_error"] > EPS),
        },
        {
            "invariant": "finite rotation pair is order-sensitive on the S^3 carrier",
            "computed": top["order_witness"]["real_order_gap"],
            "known": "nonzero gap for R01 then R02 versus R02 then R01 on generic S^3 point",
            "match": bool(top["order_witness"]["real_order_gap"] > EPS),
        },
        {
            "invariant": "commuting rotation control recomputes the same order-gap observable",
            "computed": {
                "control_operators": top["order_witness"]["commuting_control_operators"],
                "commuting_control_gap": top["order_witness"]["commuting_control_gap"],
                "commuting_operator_commutator_norm": top["order_witness"]["commuting_operator_commutator_norm"],
            },
            "known": "R01 and R23 act on disjoint coordinate planes, so C(Dp)=D(Cp) up to numerical precision",
            "match": bool(
                top["order_witness"]["commuting_control_pair_is_distinct"]
                and top["order_witness"]["commuting_control_reuses_same_observable"]
                and top["order_witness"]["commuting_control_gap"] <= EPS
                and top["order_witness"]["commuting_operator_commutator_norm"] <= EPS
            ),
        },
    ]


def build_tool_ablations(top: dict[str, Any]) -> dict[str, Any]:
    return {
        "geomstats_s3_metric_vs_flat_chord": tool_ablation(
            "distance_p0_p1_with_s3_geodesic_metric_vs_flat_r4_chord_metric",
            baseline_value=top["geomstats"]["distance_p0_p1"],
            ablated_value=top["torch_flat_chord_p0_p1"],
            tool="geomstats",
        )
    }


def build_controls(top: dict[str, Any]) -> dict[str, Any]:
    return {
        "off_sphere_flattened_scaled_control": {
            "description": "same finite sample carrier with the fourth coordinate flattened and rows scaled without renormalization",
            "real_max_norm_sq_error": top["torch_max_norm_sq_error"],
            "control_max_norm_sq_error": top["torch_control_max_norm_sq_error"],
            "unit_norm_claim_holds": False,
            "pass": bool(top["torch_control_max_norm_sq_error"] > EPS),
        },
        "flat_chord_metric_control": {
            "description": "replace the S^3 geodesic metric with the ambient R^4 chord distance for the same two real points",
            "s3_geodesic_distance": top["geomstats"]["distance_p0_p1"],
            "flat_chord_distance": top["torch_flat_chord_p0_p1"],
            "kills_geodesic_known_value": bool(abs(top["geomstats"]["distance_p0_p1"] - top["torch_flat_chord_p0_p1"]) > 1.0e-6),
            "pass": bool(abs(top["geomstats"]["distance_p0_p1"] - top["torch_flat_chord_p0_p1"]) > 1.0e-6),
        },
        "commuting_order_control": {
            "description": "replace the noncommuting rotation pair with commuting finite rotations R01 and R23, then recompute the same ||C(Dp)-D(Cp)|| order-gap observable",
            "real_operators": top["order_witness"]["operators"],
            "commuting_control_operators": top["order_witness"]["commuting_control_operators"],
            "commuting_control_pair_is_distinct": top["order_witness"]["commuting_control_pair_is_distinct"],
            "commuting_control_reuses_same_observable": top["order_witness"]["commuting_control_reuses_same_observable"],
            "real_order_gap": top["order_witness"]["real_order_gap"],
            "real_operator_commutator_norm": top["order_witness"]["real_operator_commutator_norm"],
            "commuting_control_gap": top["order_witness"]["commuting_control_gap"],
            "commuting_operator_commutator_norm": top["order_witness"]["commuting_operator_commutator_norm"],
            "kills_n01_order_signature": bool(
                top["order_witness"]["commuting_control_gap"] <= EPS
                and top["order_witness"]["commuting_operator_commutator_norm"] <= EPS
            ),
            "pass": bool(
                top["order_witness"]["real_order_gap"] > EPS
                and top["order_witness"]["real_operator_commutator_norm"] > EPS
                and top["order_witness"]["commuting_control_pair_is_distinct"]
                and top["order_witness"]["commuting_control_reuses_same_observable"]
                and top["order_witness"]["commuting_control_gap"] <= EPS
                and top["order_witness"]["commuting_operator_commutator_norm"] <= EPS
            ),
        },
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    scale_rows = {str(n): scale_rung(n) for n in SCALES}
    top = scale_rows["64"]
    sympy_exact = sympy_exact_result()
    smt_proof = smt_unit_norm_proof(top["torch_max_norm_sq_error"], top["torch_control_max_norm_sq_error"])
    tool_ablations = build_tool_ablations(top)
    controls = build_controls(top)
    known_value_checks = build_known_value_checks(top, sympy_exact)
    scale_pass = all(row["pass"] for row in scale_rows.values())
    controls_pass = all(row["pass"] for row in controls.values())
    ablation_pass = all(abs(float(row["outcome_delta"])) > 1.0e-9 for row in tool_ablations.values())
    known_pass = all(row["match"] for row in known_value_checks)
    all_pass = bool(scale_pass and controls_pass and ablation_pass and known_pass and smt_proof["pass"] and sympy_exact["pass"])

    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(RTYPE),
        "sample_count": 64,
        "ambient_dimension": 4,
        "intrinsic_dimension": 3,
        "max_norm_sq_error": top["torch_max_norm_sq_error"],
        "distance_p0_p1_arccos": top["torch_distance_p0_p1_arccos"],
        "flat_chord_p0_p1": top["torch_flat_chord_p0_p1"],
        "rotation_order_gap": top["order_witness"]["real_order_gap"],
        "claim": "all finite S^3 sample points have norm-squared one and S^3 geodesic distance(e0,e1)=pi/2",
        "pass": bool(top["pass"]),
    }
    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "representable_only": True,
        "geomstats_jax_backend_claimed": False,
        "note": "JAX recomputes tensor formulas only; geomstats has no JAX backend in this run and is executed torch-side.",
        "max_norm_error": top["jax_mirror"]["max_norm_error"],
        "control_max_norm_error": top["jax_mirror"]["control_max_norm_error"],
        "distance_p0_p1_arccos": top["jax_mirror"]["distance_p0_p1_arccos"],
        "rotation_order_gap": top["jax_mirror"]["rotation_order_gap"],
        "commuting_control_gap": top["jax_mirror"]["commuting_control_gap"],
        "commuting_operator_commutator_norm": top["jax_mirror"]["commuting_operator_commutator_norm"],
        "pass": bool(top["jax_mirror"]["pass"]),
    }

    return {
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "object_id": OBJECT_ID,
        "finite_map": {
            "domain": "finite sample set X_N subset S^3 in R^4/C^2 with N in {8,16,32,64}; finite rotation operators R01 and R02 for the N01 witness",
            "codomain_or_output": "unit-norm invariant max_x | ||x||^2 - 1 |, S^3 geodesic distances from Hypersphere(dim=3), closed-form geodesic check, and finite order-gap readout",
            "definition": "S^3 = {x in R^4 : ||x||=1}; samples are deterministic angular points plus canonical basis points, never dense 2^N state closure",
        },
        "domain": {
            "carrier": "finite non-dense S^3 sample sets in R^4/C^2",
            "sample_counts": list(SCALES),
            "operators": ["R01(theta=0.37)", "R02(theta=-0.23)"],
            "commuting_control_operators": ["R01(theta=0.37)", "R23(theta=0.41)"],
        },
        "codomain_or_output": {
            "unit_norm_invariant": "max |norm^2-1|",
            "geodesic_invariant": "S^3 metric distance on Hypersphere(dim=3)",
            "known_closed_form": "distance(e0,e1)=arccos(0)=pi/2",
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite sample/probe/operator set: N in {8,16,32,64}, finite R4 coordinates, finite S^3 metric readouts, finite controls",
            },
            "N01": {
                "status": "active_tested",
                "statement": "finite rotations R01 and R02 are order-sensitive on a generic S^3 point; commuting R01/R23 control recomputes the same order-gap observable with zero gap",
                "torch_order_gap_at_64": top["order_witness"]["real_order_gap"],
                "commuting_control_gap_at_64": top["order_witness"]["commuting_control_gap"],
                "real_operator_commutator_norm_at_64": top["order_witness"]["real_operator_commutator_norm"],
                "commuting_operator_commutator_norm_at_64": top["order_witness"]["commuting_operator_commutator_norm"],
            },
        },
        "classification": "lego",
        "promotion_allowed": False,
        "tier": "canonical build STAGE 3 - geometry objects",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "carrier_layer": "S3 unit sphere in C^2/R^4",
        "geometry_layer": "3-sphere S^3 with torch-side geomstats Hypersphere(dim=3) metric/geodesic",
        "carrier_realization": "torch.float64 finite R4/C2 coordinate tensors; JAX x64 formula mirror where representable; no NumPy import and no dense state closure",
        "peps3d_embedding": "not_applicable_for_this_standalone_geometry_object; PEPS3D/manifold consumers remain blocked",
        "spinor_state": "C^2 interpretation only as pairs (x0+i*x1, x2+i*x3); no manifold spinor-network claim",
        "quaternion_action": "not_applicable; no quaternion language is used as claim-bearing evidence",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/sim_root_F01_finite_distinguishability_probe.py",
            "system_v5/ops/formal_scouts/sim_carrier_torch_complex_spinor_probe.py",
        ],
        "allowed_claims": [
            "standalone S^3 geometry object instantiated as finite non-dense sample sets at 8/16/32/64",
            "unit-norm invariant holds for the real finite carrier and fails for the off-sphere flattened/scaled control",
            "S^3 geodesic distance(e0,e1) matches the sympy closed-form pi/2 value",
            "finite S^3 carrier supports a bounded order-sensitive rotation witness",
        ],
        "promotion_blockers": [
            "single standalone geometry lego only",
            "no PEPS3D carrier embedding",
            "no layer, G-structure, stack, bridge, flux, Xi/Phi0, Axis0, FEP, gravity, or final manifold admission",
        ],
        "eligible_consumers": ["future bounded standalone geometry comparisons only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": float(
            max(
                max(
                    abs(row["jax_mirror"]["max_norm_error"] - row["torch_max_norm_sq_error"]),
                    abs(row["jax_mirror"]["distance_p0_p1_arccos"] - row["torch_distance_p0_p1_arccos"]),
                    abs(row["jax_mirror"]["delta_vs_torch_order_gap"]),
                )
                for row in scale_rows.values()
            )
        ),
        "proof_results": {
            "unit_norm_smt_load_bearing": smt_proof,
            "sympy_closed_form_geodesic": sympy_exact,
        },
        "controls": controls,
        "tool_ablations": tool_ablations,
        "known_value_checks": known_value_checks,
        "geomstats_result": top["geomstats"],
        "sympy_exact_result": sympy_exact,
        "scale_ladder": {
            "rungs": {
                key: {
                    "sites_or_qubits": row["sites_or_qubits"],
                    "sample_count": row["sample_count"],
                    "ambient_dimension": row["ambient_dimension"],
                    "intrinsic_dimension": row["intrinsic_dimension"],
                    "dense_state_closure_used": row["dense_state_closure_used"],
                    "torch_max_norm_sq_error": row["torch_max_norm_sq_error"],
                    "torch_control_max_norm_sq_error": row["torch_control_max_norm_sq_error"],
                    "geomstats_distance_p0_p1": row["geomstats"]["distance_p0_p1"],
                    "jax_distance_p0_p1": row["jax_mirror"]["distance_p0_p1_arccos"],
                    "rotation_order_gap": row["order_witness"]["real_order_gap"],
                    "pass": row["pass"],
                }
                for key, row in scale_rows.items()
            },
            "pass": bool(scale_pass),
        },
        "scale_details": scale_rows,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["torch", "jax", "geomstats", "sympy", "z3"],
        "actual_tools_used": ["torch", "jax", "geomstats", "sympy", "z3"],
        "proof_surfaces_used": ["z3 via smt_load_bearing", "sympy closed-form geodesic"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_negatives": ["off_sphere_flattened_scaled_control", "flat_chord_metric_control", "commuting_order_control"],
        "negatives_run": list(controls.keys()),
        "kill_conditions": [
            "off-sphere control satisfies the unit norm claim",
            "flat chord metric equals S^3 geodesic for the orthogonal basis pair",
            "SMT proof does not flip between real and control measured invariants",
            "commuting-order control uses the same operator twice, an x-minus-x identity, a hardcoded zero, or missing control-operator metadata",
            "any scale rung uses dense closure or fails",
        ],
        "required_artifacts": [str(OUT_PATH.relative_to(ROOT))],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "pass_rule": "all scale rungs pass without dense closure; measured unit-norm invariant flips real sat/control unsat through smt_load_bearing; sympy closed-form and geomstats geodesic agree; commuting-order control uses a distinct commuting operator pair on the same order-gap observable; controls and genuine geomstats metric ablation are nonzero",
        "fail_rule": "fail on missing flip, fake/zero ablation, x-minus-x or same-operator order control, hardcoded zero order control, missing control operator metadata, stale same-rotation wording, off-sphere control false-green, missing JAX formula mirror, dense closure, or downstream promotion",
        "promotion_status": "keep_but_open",
        "summary": {
            "all_pass": all_pass,
            "elapsed_seconds": round(time.time() - started, 6),
            "max_sample_count": 64,
            "max_torch_norm_sq_error": top["torch_max_norm_sq_error"],
            "control_max_norm_sq_error": top["torch_control_max_norm_sq_error"],
            "geomstats_distance_p0_p1": top["geomstats"]["distance_p0_p1"],
            "sympy_distance_p0_p1": sympy_exact["p0_p1_geodesic_float"],
            "jax_vs_pytorch_delta": 0.0,
            "promotion_allowed": False,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "all_pass": all_pass,
        "required_pass": all_pass,
    }


def main() -> int:
    result = as_jsonable(build_result())
    # Keep the summary's parity value aligned after JSON conversion.
    result["summary"]["jax_vs_pytorch_delta"] = result["jax_vs_pytorch_delta"]
    OUT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
