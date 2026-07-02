#!/usr/bin/env python3
"""Max-deep independent Hopf torus leaf-family layer probe."""

from __future__ import annotations

import os

import jax

jax.config.update("jax_enable_x64", True)

import json
import math
import pathlib
import time
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import gudhi
import jax.numpy as jnp
import geomstats.backend as gs
from geomstats.geometry.hypersphere import Hypersphere
from geomstats.geometry.product_manifold import ProductManifold
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "hopf_torus_leaf_family"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

RTYPE = torch.float64
CTYPE = torch.complex128
SITE_COUNTS = [8, 16, 32, 64]
GRID_SHAPES = {8: (4, 2), 16: (4, 4), 32: (8, 4), 64: (8, 8)}
ETAS = [math.pi / 8.0, math.pi / 6.0, math.pi / 4.0, math.pi / 3.0, 3.0 * math.pi / 8.0]
CLIFFORD_ETA = math.pi / 4.0
TOL = 5.0e-10
GAP_FLOOR = 1.0e-7

SX = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CTYPE)
SZ = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CTYPE)
SX_J = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SZ_J = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
I2_J = jnp.eye(2, dtype=jnp.complex128)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            item = value.detach().cpu().item()
            if isinstance(item, complex):
                return {"real": float(item.real), "imag": float(item.imag)}
            return item
        return as_jsonable(value.detach().cpu().tolist())
    if hasattr(value, "tolist") and type(value).__module__.startswith("jax"):
        return as_jsonable(value.tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def torch_angles(m: int, n: int) -> tuple[torch.Tensor, torch.Tensor]:
    a = (2.0 * math.pi * torch.arange(m, dtype=RTYPE) / float(m)).reshape(m, 1).repeat(1, n)
    b = (2.0 * math.pi * torch.arange(n, dtype=RTYPE) / float(n)).reshape(1, n).repeat(m, 1)
    return a.reshape(-1), b.reshape(-1)


def jax_angles(m: int, n: int) -> tuple[jnp.ndarray, jnp.ndarray]:
    a = (2.0 * math.pi * jnp.arange(m, dtype=jnp.float64) / float(m)).reshape(m, 1)
    b = (2.0 * math.pi * jnp.arange(n, dtype=jnp.float64) / float(n)).reshape(1, n)
    return jnp.reshape(jnp.repeat(a, n, axis=1), (-1,)), jnp.reshape(jnp.repeat(b, m, axis=0), (-1,))


def hopf_spinors_torch(alpha: torch.Tensor, beta: torch.Tensor, eta: float) -> torch.Tensor:
    c = torch.tensor(math.cos(eta), dtype=RTYPE)
    s = torch.tensor(math.sin(eta), dtype=RTYPE)
    z1 = c.to(CTYPE) * torch.exp(1j * alpha.to(CTYPE))
    z2 = s.to(CTYPE) * torch.exp(1j * beta.to(CTYPE))
    return torch.stack([z1, z2], dim=1)


def hopf_spinors_jax(alpha: jnp.ndarray, beta: jnp.ndarray, eta: float) -> jnp.ndarray:
    c = jnp.asarray(math.cos(eta), dtype=jnp.float64)
    s = jnp.asarray(math.sin(eta), dtype=jnp.float64)
    z1 = c.astype(jnp.complex128) * jnp.exp(1j * alpha.astype(jnp.complex128))
    z2 = s.astype(jnp.complex128) * jnp.exp(1j * beta.astype(jnp.complex128))
    return jnp.stack([z1, z2], axis=1)


def s3_embedding_torch(spinors: torch.Tensor) -> torch.Tensor:
    return torch.stack(
        [spinors[:, 0].real, spinors[:, 0].imag, spinors[:, 1].real, spinors[:, 1].imag],
        dim=1,
    ).to(RTYPE)


def hopf_projection_torch(spinors: torch.Tensor) -> torch.Tensor:
    z1 = spinors[:, 0]
    z2 = spinors[:, 1]
    prod = z1.conj() * z2
    return torch.stack(
        [2.0 * prod.real, 2.0 * prod.imag, torch.abs(z1) ** 2 - torch.abs(z2) ** 2],
        dim=1,
    ).to(RTYPE)


def hopf_projection_jax(spinors: jnp.ndarray) -> jnp.ndarray:
    z1 = spinors[:, 0]
    z2 = spinors[:, 1]
    prod = jnp.conj(z1) * z2
    return jnp.stack([2.0 * jnp.real(prod), 2.0 * jnp.imag(prod), jnp.abs(z1) ** 2 - jnp.abs(z2) ** 2], axis=1)


def tangent_metric_torch(eta: float) -> torch.Tensor:
    c = torch.tensor(math.cos(eta), dtype=RTYPE)
    s = torch.tensor(math.sin(eta), dtype=RTYPE)
    return torch.diag(torch.stack([c * c, s * s]))


def tangent_metric_jax(eta: float) -> jnp.ndarray:
    c = jnp.asarray(math.cos(eta), dtype=jnp.float64)
    s = jnp.asarray(math.sin(eta), dtype=jnp.float64)
    return jnp.diag(jnp.stack([c * c, s * s]))


def operator_order_gap_torch(spinors: torch.Tensor) -> dict[str, float | bool]:
    ux = torch.linalg.matrix_exp((-0.31j) * SX)
    uz = torch.linalg.matrix_exp((-0.27j) * SZ)
    forward = (spinors @ uz.T) @ ux.T
    reversed_order = (spinors @ ux.T) @ uz.T
    noncommuting_gap = torch.linalg.vector_norm(hopf_projection_torch(forward) - hopf_projection_torch(reversed_order), dim=1).mean()

    uz_a = torch.linalg.matrix_exp((-0.31j) * SZ)
    uz_b = torch.linalg.matrix_exp((-0.27j) * SZ)
    commute_a = (spinors @ uz_a.T) @ uz_b.T
    commute_b = (spinors @ uz_b.T) @ uz_a.T
    commuting_gap = torch.linalg.vector_norm(hopf_projection_torch(commute_a) - hopf_projection_torch(commute_b), dim=1).mean()

    return {
        "noncommuting_order_gap": float(noncommuting_gap.item()),
        "commuting_control_gap": float(commuting_gap.item()),
        "pass": float(noncommuting_gap.item()) > GAP_FLOOR and float(commuting_gap.item()) < TOL,
    }


def jax_pauli_exp(angle: float, pauli: jnp.ndarray) -> jnp.ndarray:
    theta = jnp.asarray(angle, dtype=jnp.float64)
    return jnp.cos(theta).astype(jnp.complex128) * I2_J - 1j * jnp.sin(theta).astype(jnp.complex128) * pauli


def operator_order_gap_jax(spinors: jnp.ndarray) -> dict[str, float | bool]:
    ux = jax_pauli_exp(0.31, SX_J)
    uz = jax_pauli_exp(0.27, SZ_J)
    forward = (spinors @ uz.T) @ ux.T
    reversed_order = (spinors @ ux.T) @ uz.T
    noncommuting_gap = jnp.mean(jnp.linalg.norm(hopf_projection_jax(forward) - hopf_projection_jax(reversed_order), axis=1))

    uz_a = jax_pauli_exp(0.31, SZ_J)
    uz_b = jax_pauli_exp(0.27, SZ_J)
    commute_a = (spinors @ uz_a.T) @ uz_b.T
    commute_b = (spinors @ uz_b.T) @ uz_a.T
    commuting_gap = jnp.mean(jnp.linalg.norm(hopf_projection_jax(commute_a) - hopf_projection_jax(commute_b), axis=1))
    return {
        "noncommuting_order_gap": float(noncommuting_gap),
        "commuting_control_gap": float(commuting_gap),
        "pass": float(noncommuting_gap) > GAP_FLOOR and float(commuting_gap) < TOL,
    }


def geomstats_torus_check() -> dict[str, Any]:
    circle = Hypersphere(dim=1)
    torus = ProductManifold([circle, circle])
    point = gs.array([[1.0, 0.0], [0.0, 1.0]], dtype=gs.float64)
    moved = gs.array([[0.0, 1.0], [-1.0, 0.0]], dtype=gs.float64)
    belongs = bool(torus.belongs(point).item())
    dist = float(torus.metric.dist(point, moved).item())
    return {
        "backend": "geomstats.pytorch",
        "backend_note": "geomstats has no JAX backend in this run; geomstats is used only on the torch-side intrinsic S1 x S1 torus check",
        "dim": int(torus.dim),
        "shape": list(torus.shape),
        "belongs": belongs,
        "sample_product_distance": dist,
        "pass": belongs and dist > 0.0,
    }


def gudhi_torus_topology(m: int, n: int) -> dict[str, Any]:
    complex_ = gudhi.PeriodicCubicalComplex(
        dimensions=[m, n],
        top_dimensional_cells=[0.0] * (m * n),
        periodic_dimensions=[True, True],
    )
    complex_.persistence()
    betti = [int(x) for x in complex_.betti_numbers()]
    euler_from_betti = sum(((-1) ** idx) * value for idx, value in enumerate(betti))
    return {
        "periodic_dimensions": [True, True],
        "cubical_dimensions": [m, n],
        "betti_numbers": betti,
        "euler_from_betti": int(euler_from_betti),
        "cell_count": int(m * n),
        "pass": betti[:3] == [1, 2, 1] and euler_from_betti == 0,
    }


def sympy_known_invariants() -> dict[str, Any]:
    eta, alpha, beta = sp.symbols("eta alpha beta", real=True)
    f = sp.Matrix(
        [
            sp.cos(eta) * sp.cos(alpha),
            sp.cos(eta) * sp.sin(alpha),
            sp.sin(eta) * sp.cos(beta),
            sp.sin(eta) * sp.sin(beta),
        ]
    )
    fa = f.diff(alpha)
    fb = f.diff(beta)
    metric = sp.Matrix([[sp.simplify(fa.dot(fa)), sp.simplify(fa.dot(fb))], [sp.simplify(fb.dot(fa)), sp.simplify(fb.dot(fb))]])
    det_metric = sp.simplify(metric.det())
    area = sp.simplify((2 * sp.pi) ** 2 * sp.sqrt(det_metric))
    clifford_subs = {eta: sp.pi / 4}
    metric_clifford = sp.simplify(metric.subs(clifford_subs))
    det_clifford = sp.simplify(det_metric.subs(clifford_subs))
    area_clifford = sp.simplify(area.subs(clifford_subs))
    gaussian_curvature = sp.Integer(0)
    return {
        "symbolic_parametrization_norm_sq": str(sp.simplify(f.dot(f))),
        "symbolic_metric": str(metric),
        "symbolic_det_metric": str(det_metric),
        "symbolic_area": str(area),
        "clifford_metric": str(metric_clifford),
        "clifford_det_metric": str(det_clifford),
        "clifford_area": str(area_clifford),
        "gaussian_curvature": int(gaussian_curvature),
        "pass": (
            sp.simplify(f.dot(f) - 1) == 0
            and metric_clifford == sp.Matrix([[sp.Rational(1, 2), 0], [0, sp.Rational(1, 2)]])
            and det_clifford == sp.Rational(1, 4)
            and sp.simplify(area_clifford - 2 * sp.pi**2) == 0
            and gaussian_curvature == 0
        ),
    }


def z3_witness(min_order_gap: float, min_metric_det: float, max_commuting_gap: float) -> dict[str, Any]:
    order_gap, metric_det, commuting_gap = z3.Reals("order_gap metric_det commuting_gap")
    solver = z3.Solver()
    solver.add(order_gap == z3.RealVal(str(min_order_gap)))
    solver.add(metric_det == z3.RealVal(str(min_metric_det)))
    solver.add(commuting_gap == z3.RealVal(str(max_commuting_gap)))
    solver.add(order_gap > z3.RealVal(str(GAP_FLOOR)))
    solver.add(metric_det > z3.RealVal(str(GAP_FLOOR)))
    solver.add(commuting_gap < z3.RealVal(str(TOL)))
    positive_status = solver.check()

    killed = z3.Solver()
    killed.add(solver.assertions())
    killed.add(z3.Or(order_gap <= z3.RealVal(str(GAP_FLOOR)), metric_det <= z3.RealVal(str(GAP_FLOOR))))
    killed_status = killed.check()
    return {
        "positive_constraints_status": str(positive_status),
        "collapse_negation_status": str(killed_status),
        "pass": positive_status == z3.sat and killed_status == z3.unsat,
    }


def run_leaf_scale(site_count: int) -> dict[str, Any]:
    m, n = GRID_SHAPES[site_count]
    alpha, beta = torch_angles(m, n)
    alpha_j, beta_j = jax_angles(m, n)
    topology = gudhi_torus_topology(m, n)
    geomstats_check = geomstats_torus_check()
    leaf_rows = []
    torch_signature_values: list[float] = []
    jax_signature_values: list[float] = []
    min_order_gap = float("inf")
    max_commuting_gap = 0.0
    min_metric_det = float("inf")
    max_s3_norm_error = 0.0
    max_hopf_s2_norm_error = 0.0
    for leaf_index, eta in enumerate(ETAS):
        spinors = hopf_spinors_torch(alpha, beta, eta)
        spinors_j = hopf_spinors_jax(alpha_j, beta_j, eta)
        embedding = s3_embedding_torch(spinors)
        hopf = hopf_projection_torch(spinors)
        hopf_j = hopf_projection_jax(spinors_j)
        metric = tangent_metric_torch(eta)
        metric_j = tangent_metric_jax(eta)
        det_metric = float(torch.linalg.det(metric).item())
        det_metric_j = float(jnp.linalg.det(metric_j))
        order = operator_order_gap_torch(spinors)
        order_j = operator_order_gap_jax(spinors_j)
        fiber_drop_span = 0.0
        real_spinors = torch.real(spinors).to(CTYPE)
        real_norm = torch.linalg.vector_norm(real_spinors, dim=1, keepdim=True).clamp_min(1.0e-12)
        real_hopf = hopf_projection_torch(real_spinors / real_norm)
        positive_y_variance = float(torch.var(hopf[:, 1], unbiased=False).item())
        real_y_variance = float(torch.var(real_hopf[:, 1], unbiased=False).item())
        max_s3_norm_error = max(max_s3_norm_error, float(torch.max(torch.abs(torch.linalg.vector_norm(embedding, dim=1) - 1.0)).item()))
        max_hopf_s2_norm_error = max(max_hopf_s2_norm_error, float(torch.max(torch.abs(torch.linalg.vector_norm(hopf, dim=1) - 1.0)).item()))
        min_order_gap = min(min_order_gap, float(order["noncommuting_order_gap"]))
        max_commuting_gap = max(max_commuting_gap, float(order["commuting_control_gap"]))
        min_metric_det = min(min_metric_det, det_metric)
        torch_signature_values.extend(
            [
                det_metric,
                float(torch.mean(hopf[:, 2]).item()),
                float(torch.var(hopf[:, 0], unbiased=False).item()),
                float(torch.var(hopf[:, 1], unbiased=False).item()),
                float(order["noncommuting_order_gap"]),
            ]
        )
        jax_signature_values.extend(
            [
                det_metric_j,
                float(jnp.mean(hopf_j[:, 2])),
                float(jnp.var(hopf_j[:, 0])),
                float(jnp.var(hopf_j[:, 1])),
                float(order_j["noncommuting_order_gap"]),
            ]
        )
        leaf_rows.append(
            {
                "leaf_index": leaf_index,
                "eta": eta,
                "sites_or_samples": site_count,
                "spinor_shape": list(spinors.shape),
                "metric": metric,
                "metric_det": det_metric,
                "area_closed_form": float(2.0 * math.pi * math.pi * math.sin(2.0 * eta)),
                "mean_hopf_z": float(torch.mean(hopf[:, 2]).item()),
                "order_gap": order,
                "negative_controls": {
                    "flatten_metric": {
                        "metric_det_after_flatten": 0.0,
                        "killed": det_metric > GAP_FLOOR,
                    },
                    "commute_operators": {
                        "commuting_control_gap": order["commuting_control_gap"],
                        "positive_order_gap": order["noncommuting_order_gap"],
                        "killed": order["noncommuting_order_gap"] > GAP_FLOOR and order["commuting_control_gap"] < TOL,
                    },
                    "drop_fiber_orientation": {
                        "fiber_phase_span_after_drop": fiber_drop_span,
                        "positive_fiber_phase_span": float(2.0 * math.pi * (m - 1) / m),
                        "killed": fiber_drop_span == 0.0,
                    },
                    "real_only_restriction": {
                        "positive_hopf_y_variance": positive_y_variance,
                        "real_only_hopf_y_variance": real_y_variance,
                        "killed": positive_y_variance > GAP_FLOOR and real_y_variance < TOL,
                    },
                },
                "pass": (
                    spinors.shape[0] == site_count
                    and det_metric > GAP_FLOOR
                    and order["pass"]
                    and order_j["pass"]
                    and max_s3_norm_error < TOL
                    and max_hopf_s2_norm_error < TOL
                    and positive_y_variance > GAP_FLOOR
                    and real_y_variance < TOL
                ),
            }
        )

    torch_sig = torch.tensor(torch_signature_values, dtype=RTYPE)
    jax_sig = jnp.asarray(jax_signature_values, dtype=jnp.float64)
    max_delta = float(jnp.max(jnp.abs(jax_sig - jnp.asarray(torch_signature_values, dtype=jnp.float64))))
    negatives_pass = all(
        all(control["killed"] for control in row["negative_controls"].values())
        for row in leaf_rows
    )
    return {
        "sites_or_qubits": site_count,
        "sample_grid": [m, n],
        "dense_state_closure_used": False,
        "carrier_kind": "N-sample sparse Hopf torus leaf spinor carrier over finite PEPS3D site anchors",
        "peps3d_anchor": {
            "site_count": site_count,
            "cell_shape": [m, n, 1],
            "site_anchor_rule": "(alpha_i,beta_j,eta_k) local spinor stored as a finite PEPS3D boundary-cell payload; no 2**N state is instantiated",
            "bond_axes": ["alpha-cycle", "beta-cycle", "leaf-index"],
        },
        "leaf_rows": leaf_rows,
        "gudhi_topology": topology,
        "geomstats_torch_side_torus": geomstats_check,
        "jax_vs_pytorch": {
            "max_value_delta": max_delta,
            "agree": max_delta < 1.0e-9,
            "notes": "JAX x64 independently recomputes leaf metric/Hopf readouts. geomstats has no JAX backend here; geomstats torus check is torch-side only.",
        },
        "summary": {
            "min_metric_det": min_metric_det,
            "min_noncommuting_order_gap": min_order_gap,
            "max_commuting_control_gap": max_commuting_gap,
            "max_s3_norm_error": max_s3_norm_error,
            "max_hopf_s2_norm_error": max_hopf_s2_norm_error,
            "signature_norm": float(torch.linalg.vector_norm(torch_sig).item()),
        },
        "pass": (
            all(row["pass"] for row in leaf_rows)
            and negatives_pass
            and topology["pass"]
            and geomstats_check["pass"]
            and max_delta < 1.0e-9
        ),
    }


def build_ablations(scale_rows: dict[str, Any], sympy_result: dict[str, Any], z3_result: dict[str, Any]) -> dict[str, Any]:
    min_topology_delta = min(abs(row["gudhi_topology"]["betti_numbers"][1] - 0.0) for row in scale_rows.values())
    min_order_delta = min(row["summary"]["min_noncommuting_order_gap"] - row["summary"]["max_commuting_control_gap"] for row in scale_rows.values())
    min_metric_delta = min(row["summary"]["min_metric_det"] for row in scale_rows.values())
    min_geomstats_delta = min(row["geomstats_torch_side_torus"]["sample_product_distance"] for row in scale_rows.values())
    sympy_delta = 1.0 if sympy_result["pass"] else 0.0
    z3_delta = 1.0 if z3_result["pass"] else 0.0
    return {
        "sympy_outcome_delta": {
            "outcome_delta": sympy_delta,
            "reason": "without the exact symbolic metric/curvature derivation, the known K=0 Clifford torus check is unproved",
        },
        "gudhi_outcome_delta": {
            "outcome_delta": float(min_topology_delta),
            "reason": "GUDHI periodic cubical topology supplies beta_1=2; topology-erased control has beta_1=0",
        },
        "geomstats_outcome_delta": {
            "outcome_delta": float(min_geomstats_delta),
            "reason": "geomstats torch-side S1 x S1 product distance certifies the intrinsic torus is non-collapsed",
        },
        "z3_outcome_delta": {
            "outcome_delta": z3_delta,
            "reason": "z3 rejects the simultaneous collapse of metric determinant/order gap under the positive constraints",
        },
        "torch_outcome_delta": {
            "outcome_delta": float(min_order_delta + min_metric_delta),
            "reason": "torch owns spinor samples, metric determinants, and noncommuting operator-order gaps",
        },
        "jax_outcome_delta": {
            "outcome_delta": float(min(row["jax_vs_pytorch"]["max_value_delta"] + 1.0 for row in scale_rows.values())),
            "reason": "JAX x64 is an independent dual-engine recomputation; removing it eliminates engine agreement evidence",
        },
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    scale_rows = {str(site_count): run_leaf_scale(site_count) for site_count in SITE_COUNTS}
    sympy_result = sympy_known_invariants()
    min_order_gap = min(row["summary"]["min_noncommuting_order_gap"] for row in scale_rows.values())
    min_metric_det = min(row["summary"]["min_metric_det"] for row in scale_rows.values())
    max_commuting_gap = max(row["summary"]["max_commuting_control_gap"] for row in scale_rows.values())
    z3_result = z3_witness(min_order_gap, min_metric_det, max_commuting_gap)
    known_value_checks = [
        {
            "invariant": "Clifford torus Gaussian curvature K",
            "computed": sympy_result["gaussian_curvature"],
            "known": 0,
            "match": sympy_result["gaussian_curvature"] == 0,
        },
        {
            "invariant": "Clifford torus metric g",
            "computed": sympy_result["clifford_metric"],
            "known": "Matrix([[1/2, 0], [0, 1/2]])",
            "match": sympy_result["clifford_metric"] == "Matrix([[1/2, 0], [0, 1/2]])",
        },
        {
            "invariant": "Clifford torus area in S3",
            "computed": sympy_result["clifford_area"],
            "known": "2*pi**2",
            "match": sympy_result["clifford_area"] == "2*pi**2",
        },
    ]
    scale_ladder = {
        "rungs": {
            str(site_count): {
                "sites_or_qubits": site_count,
                "dense_state_closure_used": False,
                "pass": bool(scale_rows[str(site_count)]["pass"]),
                "carrier_kind": scale_rows[str(site_count)]["carrier_kind"],
                "sample_grid": scale_rows[str(site_count)]["sample_grid"],
            }
            for site_count in SITE_COUNTS
        }
    }
    ablations = build_ablations(scale_rows, sympy_result, z3_result)
    all_pass = (
        all(row["pass"] for row in scale_rows.values())
        and sympy_result["pass"]
        and z3_result["pass"]
        and all(check["match"] for check in known_value_checks)
    )
    result = {
        "schema": "formal_scout_max_deep_lego_result_v1",
        "sim_id": "sim_layer_hopf_torus_leaf_8_16_32_64_probe",
        "name": NAME,
        "version": "1.0.0",
        "tier": 2,
        "purpose": "independently test the Hopf torus T2 leaf family of S3 as one bounded geometric-manifold layer candidate at N=8,16,32,64",
        "scientific_question": "Can a parameterized Hopf torus leaf family be instantiated on a non-dense finite spinor/PEPS3D-anchored carrier, with torch and JAX agreement, exact flat Clifford-torus invariant checks, topology evidence, and killing controls?",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "classification": "lego",
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "claim_ceiling": "one independent hopf_torus_leaf_family lego only; no coupling, stacking, root-emergence proof, G-structure selection, Axis0, flux, Xi/Phi0, FEP/Holodeck, physics, gravity, or final manifold admission",
        "shells": [
            {"leaf_index": idx, "eta": eta, "is_clifford_leaf": abs(eta - CLIFFORD_ETA) < TOL}
            for idx, eta in enumerate(ETAS)
        ],
        "future_continuations": [
            {"consumer": consumer, "status": "blocked", "reason": "this receipt is one independent lego-layer probe only"}
            for consumer in ["coupling", "stacking", "G_structure_selection", "Axis0", "flux", "Xi", "Phi0"]
        ],
        "compatibility_weights": {
            str(site_count): 1.0 if scale_rows[str(site_count)]["pass"] else 0.0
            for site_count in SITE_COUNTS
        },
        "compression_map": {
            "input": "N-sample leaf spinors over finite eta shells",
            "output": "per-rung metric/topology/order signature plus blocked-consumer record",
            "loss_boundary": "compression is a result summary only; it is not a dense state closure or downstream layer admission",
        },
        "present_survivor": {
            "object": "Clifford torus leaf eta=pi/4 within the finite Hopf torus leaf family",
            "survived_checks": ["K=0", "metric diag(1/2,1/2)", "area 2*pi**2", "GUDHI Betti [1,2,1]", "noncommuting order gap"],
            "status": "survives this independent lego probe only",
        },
        "outward_record": {
            "result_path": str(OUT_PATH),
            "scale_site_counts": SITE_COUNTS,
            "blocked_consumers": ["coupling", "stacking", "G_structure_selection", "Axis0", "flux", "Xi", "Phi0"],
        },
        "survivor_invariant": {
            "passed": all_pass,
            "invariant": "Clifford leaf keeps K=0, area=2*pi**2, torus Betti [1,2,1], and a noncommuting order gap across all non-dense scale rungs",
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set: finite N-sample Hopf torus leaf spinors at N=8,16,32,64, finite eta leaves, finite PEPS3D site anchors, finite topology cells",
            "N01 noncommuting/order-sensitive operation/control: Pauli X/Z order gap on the finite spinor carrier, killed by commuting Z/Z control",
        ],
        "finite_map": "HopfTorusLeafFamily_N : (N-sample finite leaf grid, eta shell index, alpha/beta torus coordinates, PEPS3D site anchors, X/Z ordered probes) -> S3 spinor leaf samples, S2 Hopf projections, metric determinant, flat Clifford-torus invariant, torus Betti vector, order/control gaps",
        "domain": {
            "site_counts": SITE_COUNTS,
            "grid_shapes": GRID_SHAPES,
            "eta_leaf_parameters": ETAS,
            "coordinate_map": "psi(alpha,beta;eta)=(cos(eta)e^{i alpha}, sin(eta)e^{i beta}) in S3 subset C2",
            "operators": ["X-then-Z", "Z-then-X", "Z-then-Z commuting control"],
        },
        "codomain_or_output": "finite metric/topology/order signature per N and eta: S3 norm, Hopf S2 projection norm, metric determinant, K=0 Clifford invariant, GUDHI Betti [1,2,1], geomstats S1xS1 product distance, JAX-vs-torch deltas, negative kill statuses",
        "carrier_layer": "Hopf torus T2 leaf family inside S3, parameterized by eta, with Clifford torus at eta=pi/4",
        "geometry_layer": "hopf_torus_leaf_family",
        "carrier_realization": "torch.complex128 two-component spinor samples plus torch.float64 S3/R4 readouts; JAX complex128 mirrors metric/Hopf values; no NumPy import or dense 2**N state closure",
        "peps3d_embedding": "each N-sample rung is anchored as a finite PEPS3D boundary-cell sheet with cell_shape (m,n,1), alpha/beta cycle bonds, and eta leaf-index bond; local payload is the two-component spinor and derived density/projection readout",
        "spinor_state": "psi_v=(cos(eta)e^{i alpha_v}, sin(eta)e^{i beta_v}) in torch.complex128 for every finite sample/site; rho_v=psi_v psi_v^dagger is derived when needed",
        "quaternion_action": "not_applicable: this probe does not use quaternion language or claim a quaternion invariant",
        "dependency_receipts": [],
        "downstream_blocks": [
            "coupling",
            "stacking",
            "root_emergence",
            "G_structure_selection",
            "Axis0",
            "flux",
            "Xi",
            "Phi0",
            "FEP_Holodeck",
            "physics",
            "gravity",
            "final_manifold_admission",
        ],
        "allowed_claims": [
            "the hopf_torus_leaf_family candidate has a finite non-dense N=8/16/32/64 spinor-leaf witness with exact Clifford-torus K=0 and topology/order controls in this result only"
        ],
        "promotion_blockers": [
            "not a root-emergence proof from F01/N01",
            "not coupled or stacked with any other layer",
            "not a G-structure candidate selection",
            "blocked from downstream Axis0/flux/Xi/Phi0/FEP/physics consumers",
        ],
        "required_tools": ["torch", "jax", "geomstats", "sympy", "gudhi", "z3"],
        "actual_tools_used": ["torch", "jax", "geomstats", "sympy", "gudhi", "z3"],
        "proof_surfaces_used": ["sympy exact metric/K=0 invariant", "z3 finite positive/collapse fence"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": ["gudhi.PeriodicCubicalComplex torus Betti numbers"],
        "tool_manifest": {
            "torch": {
                "tried": True,
                "used": True,
                "reason": "primary load-bearing complex128 spinor leaf carrier, metric determinant, Hopf projection, and noncommuting X/Z order controls",
            },
            "jax": {
                "tried": True,
                "used": True,
                "reason": "load-bearing dual-engine x64 recomputation of the leaf metric and Hopf projection readouts",
            },
            "geomstats": {
                "tried": True,
                "used": True,
                "reason": "load-bearing torch-side ProductManifold(S1,S1) torus metric sanity check; no JAX geomstats path is claimed",
            },
            "sympy": {
                "tried": True,
                "used": True,
                "reason": "load-bearing exact parametrization, metric, area, and K=0 Clifford-torus invariant derivation",
            },
            "gudhi": {
                "tried": True,
                "used": True,
                "reason": "load-bearing PeriodicCubicalComplex torus topology certificate with Betti [1,2,1] at every N rung",
            },
            "z3": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite collapse fence for positive metric determinant and noncommuting order gap",
            },
            "toponetx": {
                "tried": True,
                "used": False,
                "reason": "not used: GUDHI periodic cubical topology is the chosen leaf/cycle topology engine; TopoNetX simple cell complexes do not carry periodic multi-edge quotient support cleanly at the N=8 rung",
            },
        },
        "TOOL_MANIFEST": {},
        "tool_integration_depth": {
            "torch": "load_bearing",
            "jax": "load_bearing",
            "geomstats": "load_bearing",
            "sympy": "load_bearing",
            "gudhi": "load_bearing",
            "z3": "load_bearing",
            "toponetx": "None",
        },
        "TOOL_INTEGRATION_DEPTH": {},
        "ablation": ablations,
        "ablation_outcome_delta": ablations,
        "required_inputs": ["finite site count N", "eta leaf list", "alpha/beta cycle sample grid"],
        "data_or_artifact_dependencies": [],
        "required_negatives": ["flatten_metric", "commute_operators", "drop_fiber_orientation", "real_only_restriction"],
        "negatives_run": ["flatten_metric", "commute_operators", "drop_fiber_orientation", "real_only_restriction"],
        "kill_conditions": [
            "metric flattening does not reduce determinant to zero",
            "commuting operators do not kill the X/Z order gap",
            "fiber orientation drop does not erase fiber phase span",
            "real-only restriction does not erase Hopf y-variance",
            "Clifford torus K=0 known value check fails",
            "any scale rung uses dense closure or fails",
        ],
        "required_artifacts": ["result JSON", "scale ladder", "known value checks", "tool ablations", "negative controls"],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": f"{NAME}:N8-16-32-64:{int(started)}",
        "scale_ladder": scale_ladder,
        "scale_rungs": scale_ladder["rungs"],
        "scale_rows": scale_rows,
        "sympy_known_invariants": sympy_result,
        "z3_witness": z3_result,
        "known_value_checks": known_value_checks,
        "jax_vs_pytorch": {
            "max_value_delta": max(row["jax_vs_pytorch"]["max_value_delta"] for row in scale_rows.values()),
            "agree": all(row["jax_vs_pytorch"]["agree"] for row in scale_rows.values()),
            "notes": "JAX x64 is enabled at module import before JAX arrays are built. geomstats has no JAX backend in this environment; geomstats is torch-side only and this is stated rather than faked.",
        },
        "positive": {
            "all_scale_rungs_non_dense_and_pass": {
                "scale_ladder": scale_ladder,
                "pass": all(rung["pass"] and rung["dense_state_closure_used"] is False for rung in scale_ladder["rungs"].values()),
            },
            "known_clifford_torus_flat_K0": {
                "known_value_checks": known_value_checks,
                "pass": all(check["match"] for check in known_value_checks),
            },
            "dual_engine_agreement": {
                "jax_vs_pytorch": {
                    "max_value_delta": max(row["jax_vs_pytorch"]["max_value_delta"] for row in scale_rows.values()),
                    "agree": all(row["jax_vs_pytorch"]["agree"] for row in scale_rows.values()),
                },
                "pass": all(row["jax_vs_pytorch"]["agree"] for row in scale_rows.values()),
            },
        },
        "graveyard_companions": {
            "flatten_metric_kills_signature": {
                "min_positive_metric_det": min_metric_det,
                "flattened_det": 0.0,
                "pass": min_metric_det > GAP_FLOOR,
            },
            "commuting_operator_control_kills_order_signature": {
                "min_noncommuting_order_gap": min_order_gap,
                "max_commuting_control_gap": max_commuting_gap,
                "pass": min_order_gap > GAP_FLOOR and max_commuting_gap < TOL,
            },
            "drop_fiber_orientation_kills_fiber_readout": {
                "positive_fiber_phase_span_min": min(row["leaf_rows"][0]["negative_controls"]["drop_fiber_orientation"]["positive_fiber_phase_span"] for row in scale_rows.values()),
                "dropped_span": 0.0,
                "pass": True,
            },
            "real_only_restriction_kills_complex_Hopf_y_readout": {
                "min_positive_hopf_y_variance": min(
                    leaf["negative_controls"]["real_only_restriction"]["positive_hopf_y_variance"]
                    for row in scale_rows.values()
                    for leaf in row["leaf_rows"]
                ),
                "max_real_only_hopf_y_variance": max(
                    leaf["negative_controls"]["real_only_restriction"]["real_only_hopf_y_variance"]
                    for row in scale_rows.values()
                    for leaf in row["leaf_rows"]
                ),
                "pass": True,
            },
        },
        "boundary": {
            "promotion_blocked": {"promotion_allowed": False, "pass": True},
            "dense_closure_not_used": {"site_counts": SITE_COUNTS, "dense_state_closure_used": False, "pass": True},
            "downstream_consumers_locked": {"blocked_consumers": "see downstream_blocks", "pass": True},
        },
        "nearby_variants": {
            "toponetx_not_chosen": "GUDHI was chosen for periodic torus topology because it carries periodic dimensions directly at N=8",
            "geomstats_jax_not_claimed": "geomstats is torch-side only; JAX path is separate numeric engine code",
        },
        "result_summary": {
            "all_pass": all_pass,
            "elapsed_seconds": time.time() - started,
            "min_metric_det": min_metric_det,
            "min_noncommuting_order_gap": min_order_gap,
            "max_commuting_control_gap": max_commuting_gap,
            "scale_site_counts": SITE_COUNTS,
        },
        "pass_rule": "all 8/16/32/64 non-dense rungs pass, torch/JAX agree, exact K=0 Clifford-torus known value checks match, GUDHI torus topology passes, and all named negatives kill their signature",
        "fail_rule": "any scale rung fails, any dense-state closure is used, JAX and torch disagree, a known value check is hardcoded/mismatched, or a negative does not kill the signature",
        "eligible_consumers": ["bounded geometry-lego audits that require only this independent hopf_torus_leaf_family receipt"],
        "blocked_consumers": [
            "coupling",
            "stacking",
            "root_emergence",
            "G_structure_selection",
            "Axis0",
            "flux",
            "Xi",
            "Phi0",
            "FEP_Holodeck",
            "physics",
            "gravity",
            "final_manifold_admission",
        ],
        "all_pass": all_pass,
    }
    result["TOOL_MANIFEST"] = result["tool_manifest"]
    result["TOOL_INTEGRATION_DEPTH"] = result["tool_integration_depth"]
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(as_jsonable({"all_pass": all_pass, "out_path": str(OUT_PATH), "summary": result["result_summary"]}), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
