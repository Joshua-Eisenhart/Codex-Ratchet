#!/usr/bin/env python3
"""Canonical Stage 3 standalone Hopf fibration geometry lego.

Finite map:
    H: S^3_spinor_samples -> S^2_base_vectors

The executable claim is deliberately narrow:
    normalized torch complex spinors map through the Hopf map to unit S^2
    vectors, and global U(1) fiber phase leaves the S^2 base vector unchanged.

This is geometry-object evidence only. It is not a layer, G-structure,
manifold admission, flux, Axis0, FEP, gravity, or physics result.
"""

from __future__ import annotations

import os

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import json
import math
import pathlib
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

from clifford import Cl
from geomstats.geometry.hypersphere import Hypersphere
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
SIM_ID = "sim_geom_hopf_fibration_probe"
OBJECT_ID = "geom_hopf_fibration"
OUT_PATH = RESULT_DIR / f"{OBJECT_ID}_results.json"

SCALE_RUNGS = (8, 16, 32, 64)
RTYPE = torch.float64
CTYPE = torch.complex128
EPS = 1.0e-9
KILL_FLOOR = 1.0e-9
BROKEN_FIBER_PHASE = 0.73
GLOBAL_FIBER_PHASE = 0.41
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY claim-bearing runtime for finite complex spinor samples, Hopf map, U(1) fiber action, controls, N01 order witness, and scale ladder.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 parity mirror for the representable Hopf-map tensor algebra only; geomstats and Clifford paths are not faked in JAX.",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING S2 metric geometry check using the PyTorch backend; ablation recomputes the same S2 metric distance for true global U(1) fiber action versus broken component-phase action.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING Cl(3) vector-basis check that the Hopf base vector has Clifford squared norm one; ablation removes the e3 structure and recomputes.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Supportive exact algebra for the Hopf norm identity and exact real/control known-value counterexample; no numeric ablation emitted for proof tools.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via load_bearing_proof.smt_load_bearing; load-bearing only by measured real/control verdict flip, with no numeric ablation row.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check through load_bearing_proof.smt_load_bearing cvc5_claim_pairs; no numeric ablation row.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not used for claim-bearing computation.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "geomstats": "load_bearing",
    "clifford": "load_bearing",
    "sympy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "numpy": None,
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
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator, "float": float(value)}
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def unit_complex_phase_torch(theta: torch.Tensor | float) -> torch.Tensor:
    if not isinstance(theta, torch.Tensor):
        theta = torch.tensor(theta, dtype=RTYPE)
    return torch.cos(theta).to(CTYPE) + 1j * torch.sin(theta).to(CTYPE)


def unit_complex_phase_jax(theta: jnp.ndarray | float) -> jnp.ndarray:
    theta = jnp.asarray(theta, dtype=jnp.float64)
    return jnp.cos(theta).astype(jnp.complex128) + 1j * jnp.sin(theta).astype(jnp.complex128)


def spinor_samples_torch(sample_count: int) -> torch.Tensor:
    idx = torch.arange(sample_count, dtype=RTYPE)
    alpha = (idx + 1.0) * (math.pi / 2.0) / (sample_count + 1.0)
    relative = 2.0 * math.pi * idx / sample_count
    global_phase = math.pi * (idx + 1.0) * (idx + 2.0) / (sample_count + 3.0)

    z0 = torch.cos(alpha).to(CTYPE) * unit_complex_phase_torch(global_phase)
    z1 = torch.sin(alpha).to(CTYPE) * unit_complex_phase_torch(global_phase + relative)
    spinors = torch.stack([z0, z1], dim=1)
    norms = torch.sqrt(torch.real(torch.sum(torch.conj(spinors) * spinors, dim=1))).to(CTYPE)
    return spinors / norms[:, None]


def spinor_samples_jax(sample_count: int) -> jnp.ndarray:
    idx = jnp.arange(sample_count, dtype=jnp.float64)
    alpha = (idx + 1.0) * (math.pi / 2.0) / (sample_count + 1.0)
    relative = 2.0 * math.pi * idx / sample_count
    global_phase = math.pi * (idx + 1.0) * (idx + 2.0) / (sample_count + 3.0)

    z0 = jnp.cos(alpha).astype(jnp.complex128) * unit_complex_phase_jax(global_phase)
    z1 = jnp.sin(alpha).astype(jnp.complex128) * unit_complex_phase_jax(global_phase + relative)
    spinors = jnp.stack([z0, z1], axis=1)
    norms = jnp.sqrt(jnp.real(jnp.sum(jnp.conj(spinors) * spinors, axis=1))).astype(jnp.complex128)
    return spinors / norms[:, None]


def hopf_map_torch(spinors: torch.Tensor) -> torch.Tensor:
    z0 = spinors[:, 0]
    z1 = spinors[:, 1]
    cross = z0 * torch.conj(z1)
    x = 2.0 * torch.real(cross)
    y = 2.0 * torch.imag(cross)
    z = torch.real(z0 * torch.conj(z0) - z1 * torch.conj(z1))
    return torch.stack([x, y, z], dim=1).to(RTYPE)


def hopf_map_jax(spinors: jnp.ndarray) -> jnp.ndarray:
    z0 = spinors[:, 0]
    z1 = spinors[:, 1]
    cross = z0 * jnp.conj(z1)
    x = 2.0 * jnp.real(cross)
    y = 2.0 * jnp.imag(cross)
    z = jnp.real(z0 * jnp.conj(z0) - z1 * jnp.conj(z1))
    return jnp.stack([x, y, z], axis=1).astype(jnp.float64)


def global_phase_rotate_torch(spinors: torch.Tensor, theta: float = GLOBAL_FIBER_PHASE) -> torch.Tensor:
    return spinors * unit_complex_phase_torch(theta)


def global_phase_rotate_jax(spinors: jnp.ndarray, theta: float = GLOBAL_FIBER_PHASE) -> jnp.ndarray:
    return spinors * unit_complex_phase_jax(theta)


def broken_fiber_rotate_torch(spinors: torch.Tensor, theta: float = BROKEN_FIBER_PHASE) -> torch.Tensor:
    phase = unit_complex_phase_torch(theta)
    out = spinors.clone()
    out[:, 1] = out[:, 1] * phase
    return out


def broken_fiber_rotate_jax(spinors: jnp.ndarray, theta: float = BROKEN_FIBER_PHASE) -> jnp.ndarray:
    phase = unit_complex_phase_jax(theta)
    return spinors.at[:, 1].set(spinors[:, 1] * phase)


def flatten_s2_torch(base_points: torch.Tensor) -> torch.Tensor:
    flattened = base_points.clone()
    flattened[:, 2] = 0.0
    return flattened


def flatten_s2_jax(base_points: jnp.ndarray) -> jnp.ndarray:
    return base_points.at[:, 2].set(0.0)


def s2_norms_torch(base_points: torch.Tensor) -> torch.Tensor:
    return torch.linalg.vector_norm(base_points, dim=1)


def s2_norms_jax(base_points: jnp.ndarray) -> jnp.ndarray:
    return jnp.linalg.norm(base_points, axis=1)


def max_pair_delta_torch(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.max(torch.linalg.vector_norm(a - b, dim=1)).item())


def max_pair_delta_jax(a: jnp.ndarray, b: jnp.ndarray) -> float:
    return float(jnp.max(jnp.linalg.norm(a - b, axis=1)))


def geomstats_geodesic_distances(base_points: torch.Tensor) -> torch.Tensor:
    sphere = Hypersphere(dim=2)
    return sphere.metric.dist(base_points[:-1], base_points[1:])


def geomstats_fiber_distance_summary(base_points: torch.Tensor, global_base: torch.Tensor, broken_base: torch.Tensor) -> dict[str, Any]:
    sphere = Hypersphere(dim=2)
    global_dist = sphere.metric.dist(base_points, global_base)
    broken_dist = sphere.metric.dist(base_points, broken_base)
    return {
        "backend": "pytorch",
        "observable": "S2 geodesic distance between Hopf base points under true global U(1) fiber action and broken component-phase action",
        "global_fiber_geodesic_mean": float(torch.mean(global_dist).item()),
        "global_fiber_geodesic_max": float(torch.max(global_dist).item()),
        "broken_fiber_geodesic_mean": float(torch.mean(broken_dist).item()),
        "broken_fiber_geodesic_max": float(torch.max(broken_dist).item()),
        "broken_minus_global_mean": float((torch.mean(broken_dist) - torch.mean(global_dist)).item()),
        "pass": bool(torch.max(global_dist).item() <= EPS and torch.mean(broken_dist).item() > KILL_FLOOR),
    }


def clifford_norm_summary(base_points: torch.Tensor) -> dict[str, Any]:
    _layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    full_values: list[float] = []
    flattened_values: list[float] = []
    pseudoscalar = e1 * e2 * e3
    for point in base_points.detach().cpu():
        x = float(point[0].item())
        y = float(point[1].item())
        z = float(point[2].item())
        full_vec = x * e1 + y * e2 + z * e3
        flat_vec = x * e1 + y * e2
        full_values.append(float((full_vec * full_vec).value[0]))
        flattened_values.append(float((flat_vec * flat_vec).value[0]))
    return {
        "basis": "Cl(3) Euclidean e1,e2,e3",
        "pseudoscalar_square": float((pseudoscalar * pseudoscalar).value[0]),
        "min_vector_square": min(full_values),
        "max_vector_square": max(full_values),
        "max_unit_gap": max(abs(v - 1.0) for v in full_values),
        "flattened_min_vector_square": min(flattened_values),
        "flattened_max_vector_square": max(flattened_values),
        "flattened_max_gap_from_unit": max(abs(v - 1.0) for v in flattened_values),
        "pass": bool(max(abs(v - 1.0) for v in full_values) <= 1.0e-9 and min(flattened_values) < 1.0 - KILL_FLOOR),
    }


def local_n01_order_witness_torch(spinors: torch.Tensor) -> dict[str, Any]:
    x_op = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CTYPE)
    phase = unit_complex_phase_torch(0.37)
    phase_op = torch.diag(torch.tensor([phase, torch.conj(phase)], dtype=CTYPE))
    phase_then_x = (phase_op @ (x_op @ spinors.T)).T
    x_then_phase = (x_op @ (phase_op @ spinors.T)).T
    phase_phase_a = (phase_op @ (phase_op @ spinors.T)).T
    phase_phase_b = (phase_op @ (phase_op @ spinors.T)).T
    base_phase_then_x = hopf_map_torch(phase_then_x)
    base_x_then_phase = hopf_map_torch(x_then_phase)
    base_phase_phase_a = hopf_map_torch(phase_phase_a)
    base_phase_phase_b = hopf_map_torch(phase_phase_b)
    real_order_gap = max_pair_delta_torch(base_phase_then_x, base_x_then_phase)
    commuting_control_gap = max_pair_delta_torch(base_phase_phase_a, base_phase_phase_b)
    return {
        "observable": "max ||Hopf(R_phi X psi)-Hopf(X R_phi psi)|| over finite spinor samples",
        "phase_phi": 0.37,
        "real_order_gap": real_order_gap,
        "commuting_control_gap": commuting_control_gap,
        "pass": bool(real_order_gap > KILL_FLOOR and commuting_control_gap <= KILL_FLOOR),
    }


def local_n01_order_witness_jax(spinors: jnp.ndarray) -> dict[str, Any]:
    x_op = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
    phase = unit_complex_phase_jax(0.37)
    phase_op = jnp.diag(jnp.asarray([phase, jnp.conj(phase)], dtype=jnp.complex128))
    phase_then_x = (phase_op @ (x_op @ spinors.T)).T
    x_then_phase = (x_op @ (phase_op @ spinors.T)).T
    phase_phase_a = (phase_op @ (phase_op @ spinors.T)).T
    phase_phase_b = (phase_op @ (phase_op @ spinors.T)).T
    base_phase_then_x = hopf_map_jax(phase_then_x)
    base_x_then_phase = hopf_map_jax(x_then_phase)
    base_phase_phase_a = hopf_map_jax(phase_phase_a)
    base_phase_phase_b = hopf_map_jax(phase_phase_b)
    real_order_gap = max_pair_delta_jax(base_phase_then_x, base_x_then_phase)
    commuting_control_gap = max_pair_delta_jax(base_phase_phase_a, base_phase_phase_b)
    return {
        "observable": "JAX mirror max ||Hopf(R_phi X psi)-Hopf(X R_phi psi)||",
        "phase_phi": 0.37,
        "real_order_gap": real_order_gap,
        "commuting_control_gap": commuting_control_gap,
        "pass": bool(real_order_gap > KILL_FLOOR and commuting_control_gap <= KILL_FLOOR),
    }


def sympy_hopf_identity() -> dict[str, Any]:
    a, b, c, d = sp.symbols("a b c d", real=True)
    s3_norm_sq = a**2 + b**2 + c**2 + d**2
    x = 2 * (a * c + b * d)
    y = 2 * (b * c - a * d)
    z = a**2 + b**2 - c**2 - d**2
    s2_norm_sq = sp.expand(x**2 + y**2 + z**2)
    identity_residual = sp.simplify(s2_norm_sq - s3_norm_sq**2)

    exact_real = {a: sp.Rational(3, 5), b: sp.Rational(0), c: sp.Rational(4, 5), d: sp.Rational(0)}
    exact_real_s2_norm_sq = sp.simplify(s2_norm_sq.subs(exact_real))
    exact_flat_s2_norm_sq = sp.simplify((x**2 + y**2).subs(exact_real))
    exact_z_component = sp.simplify(z.subs(exact_real))
    exact_broken_delta_sq = sp.simplify(2 * (sp.Rational(24, 25) ** 2))
    return {
        "tool": "sympy",
        "variables": ["a", "b", "c", "d"],
        "s3_norm_squared": str(s3_norm_sq),
        "s2_norm_squared_expanded": str(s2_norm_sq),
        "identity_residual_s2_minus_s3_squared": str(identity_residual),
        "exact_sample": {
            "z0": "3/5",
            "z1": "4/5",
            "s2_norm_squared": str(exact_real_s2_norm_sq),
            "flattened_s2_norm_squared": str(exact_flat_s2_norm_sq),
            "z_component": str(exact_z_component),
            "broken_component_phase_delta_squared_for_i_phase": str(exact_broken_delta_sq),
        },
        "known_value": "|Hopf(psi)|=1 when |psi|=1",
        "control_value": "flattened control removes z component and gives 576/625 on the exact sample",
        "pass": bool(identity_residual == 0 and exact_real_s2_norm_sq == 1 and exact_flat_s2_norm_sq == sp.Rational(576, 625)),
    }


def torch_rung(sample_count: int) -> dict[str, Any]:
    spinors = spinor_samples_torch(sample_count)
    base = hopf_map_torch(spinors)
    global_base = hopf_map_torch(global_phase_rotate_torch(spinors))
    broken_base = hopf_map_torch(broken_fiber_rotate_torch(spinors))
    flattened_base = flatten_s2_torch(base)
    norms = s2_norms_torch(base)
    flattened_norms = s2_norms_torch(flattened_base)
    consecutive_geodesic = geomstats_geodesic_distances(base)
    fiber_metric = geomstats_fiber_distance_summary(base, global_base, broken_base)
    clifford_summary = clifford_norm_summary(base)
    n01 = local_n01_order_witness_torch(spinors)
    s3_norms = torch.real(torch.sum(torch.conj(spinors) * spinors, dim=1))

    max_s3_norm_gap = float(torch.max(torch.abs(s3_norms - 1.0)).item())
    max_s2_norm_gap = float(torch.max(torch.abs(norms - 1.0)).item())
    max_global_phase_delta = max_pair_delta_torch(base, global_base)
    max_broken_fiber_delta = max_pair_delta_torch(base, broken_base)
    min_flattened_norm = float(torch.min(flattened_norms).item())
    consecutive_geodesic_mean = float(torch.mean(consecutive_geodesic).item())
    pass_rung = bool(
        max_s3_norm_gap <= EPS
        and max_s2_norm_gap <= EPS
        and max_global_phase_delta <= EPS
        and max_broken_fiber_delta > KILL_FLOOR
        and min_flattened_norm < 1.0 - KILL_FLOOR
        and fiber_metric["pass"]
        and clifford_summary["pass"]
        and n01["pass"]
    )
    return {
        "sites_or_qubits": sample_count,
        "sample_count": sample_count,
        "spinor_component_count": 2,
        "base_dimension": 3,
        "path_count": sample_count - 1,
        "operator_count": 2,
        "dense_state_closure_used": False,
        "full_dense_dimension": "not_materialized; finite sample list of C^2 spinors only",
        "s3_norm_min": float(torch.min(s3_norms).item()),
        "s3_norm_max": float(torch.max(s3_norms).item()),
        "max_s3_norm_gap": max_s3_norm_gap,
        "s2_norm_min": float(torch.min(norms).item()),
        "s2_norm_max": float(torch.max(norms).item()),
        "max_s2_norm_gap": max_s2_norm_gap,
        "global_phase": GLOBAL_FIBER_PHASE,
        "max_global_phase_hopf_delta": max_global_phase_delta,
        "broken_component_phase": BROKEN_FIBER_PHASE,
        "max_broken_fiber_hopf_delta": max_broken_fiber_delta,
        "flattened_s2_norm_min": min_flattened_norm,
        "flattened_s2_norm_max": float(torch.max(flattened_norms).item()),
        "geomstats_backend": "pytorch",
        "geomstats_consecutive_s2_geodesic_mean": consecutive_geodesic_mean,
        "geomstats_fiber_distance_summary": fiber_metric,
        "clifford_norm_summary": clifford_summary,
        "local_n01_order_witness": n01,
        "pass": pass_rung,
    }


def jax_rung(sample_count: int) -> dict[str, Any]:
    spinors = spinor_samples_jax(sample_count)
    base = hopf_map_jax(spinors)
    global_base = hopf_map_jax(global_phase_rotate_jax(spinors))
    broken_base = hopf_map_jax(broken_fiber_rotate_jax(spinors))
    flattened_base = flatten_s2_jax(base)
    norms = s2_norms_jax(base)
    flattened_norms = s2_norms_jax(flattened_base)
    s3_norms = jnp.real(jnp.sum(jnp.conj(spinors) * spinors, axis=1))
    n01 = local_n01_order_witness_jax(spinors)

    max_s3_norm_gap = float(jnp.max(jnp.abs(s3_norms - 1.0)))
    max_s2_norm_gap = float(jnp.max(jnp.abs(norms - 1.0)))
    max_global_phase_delta = max_pair_delta_jax(base, global_base)
    max_broken_fiber_delta = max_pair_delta_jax(base, broken_base)
    min_flattened_norm = float(jnp.min(flattened_norms))
    pass_rung = bool(
        max_s3_norm_gap <= EPS
        and max_s2_norm_gap <= EPS
        and max_global_phase_delta <= EPS
        and max_broken_fiber_delta > KILL_FLOOR
        and min_flattened_norm < 1.0 - KILL_FLOOR
        and n01["pass"]
    )
    return {
        "sites_or_qubits": sample_count,
        "sample_count": sample_count,
        "dense_state_closure_used": False,
        "representable_parts": [
            "finite spinor sample generation",
            "Hopf map tensor algebra",
            "global U(1) phase invariance",
            "broken component-phase control",
            "flattened S2 norm control",
            "local Pauli X/Z N01 order witness",
        ],
        "not_represented": [
            "geomstats S2 metric path because geomstats has no JAX backend in this environment",
            "Clifford Cl(3) multivector path",
            "sympy exact algebra",
            "z3/cvc5 helper-bound proof",
        ],
        "s3_norm_min": float(jnp.min(s3_norms)),
        "s3_norm_max": float(jnp.max(s3_norms)),
        "max_s3_norm_gap": max_s3_norm_gap,
        "s2_norm_min": float(jnp.min(norms)),
        "s2_norm_max": float(jnp.max(norms)),
        "max_s2_norm_gap": max_s2_norm_gap,
        "max_global_phase_hopf_delta": max_global_phase_delta,
        "max_broken_fiber_hopf_delta": max_broken_fiber_delta,
        "flattened_s2_norm_min": min_flattened_norm,
        "flattened_s2_norm_max": float(jnp.max(flattened_norms)),
        "local_n01_order_witness": n01,
        "pass": pass_rung,
    }


def compare_torch_jax(torch_rows: dict[str, dict[str, Any]], jax_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    keys = [
        "max_s3_norm_gap",
        "max_s2_norm_gap",
        "max_global_phase_hopf_delta",
        "max_broken_fiber_hopf_delta",
        "flattened_s2_norm_min",
        "flattened_s2_norm_max",
    ]
    rows = {}
    max_delta = 0.0
    for rung in torch_rows:
        deltas = {}
        for key in keys:
            delta = abs(float(torch_rows[rung][key]) - float(jax_rows[rung][key]))
            deltas[key] = delta
            max_delta = max(max_delta, delta)
        order_delta = abs(
            float(torch_rows[rung]["local_n01_order_witness"]["real_order_gap"])
            - float(jax_rows[rung]["local_n01_order_witness"]["real_order_gap"])
        )
        deltas["local_n01_order_gap"] = order_delta
        max_delta = max(max_delta, order_delta)
        rows[rung] = {"max_value_delta": max(deltas.values()), "deltas": deltas, "pass": max(deltas.values()) <= 1.0e-8}
    return {
        "max_abs_delta": max_delta,
        "agree": max_delta <= 1.0e-8,
        "rows": rows,
        "not_a_geomstats_jax_path": True,
    }


def build_smt_proofs(top: dict[str, Any]) -> dict[str, Any]:
    norm_only = smt_load_bearing(
        claim="hopf_map_s3_to_s2_norm_preservation",
        real_measured={"min_s2_norm": top["s2_norm_min"], "norm_lower": 1.0 - EPS},
        control_measured={"min_s2_norm": top["flattened_s2_norm_min"], "norm_lower": 1.0 - EPS},
        claim_builder=lambda v: v["min_s2_norm"] >= v["norm_lower"],
        cvc5_claim_pairs=[("min_s2_norm", ">=", "norm_lower")],
    )
    norm_only["control_description"] = "S2 z-component flattened and norm recomputed"
    norm_only["pass"] = bool(
        norm_only["real_claim_verdict"] == "sat"
        and norm_only["negated_claim_verdict"] == "unsat"
        and norm_only["differ"] is True
        and norm_only["bound_to_measured"] is True
        and norm_only.get("cvc5_real_verdict") == "sat"
        and norm_only.get("cvc5_control_verdict") == "unsat"
    )

    fiber_only = smt_load_bearing(
        claim="hopf_map_global_u1_fiber_phase_invariance",
        real_measured={"max_fiber_delta": top["max_global_phase_hopf_delta"], "fiber_upper": EPS},
        control_measured={"max_fiber_delta": top["max_broken_fiber_hopf_delta"], "fiber_upper": EPS},
        claim_builder=lambda v: v["max_fiber_delta"] <= v["fiber_upper"],
        cvc5_claim_pairs=[("max_fiber_delta", "<=", "fiber_upper")],
    )
    fiber_only["control_description"] = "component-only phase twist is not the U(1) fiber action"
    fiber_only["pass"] = bool(
        fiber_only["real_claim_verdict"] == "sat"
        and fiber_only["negated_claim_verdict"] == "unsat"
        and fiber_only["differ"] is True
        and fiber_only["bound_to_measured"] is True
        and fiber_only.get("cvc5_real_verdict") == "sat"
        and fiber_only.get("cvc5_control_verdict") == "unsat"
    )
    return {
        "hopf_norm_preservation_smt_load_bearing": norm_only,
        "hopf_fiber_phase_invariance_smt_load_bearing": fiber_only,
        "authoritative_claim_shape": "The Hopf geometry claim is the conjunction of two separate measured flips: S2 norm preservation against a flattened S2 control, and global U(1) fiber phase invariance against a component-phase broken-fiber control. These are kept separate so no proof row mixes controls.",
    }


def add_ablation_pass(row: dict[str, Any]) -> dict[str, Any]:
    row["pass"] = bool(abs(float(row["outcome_delta"])) > KILL_FLOOR)
    return row


def build_tool_ablations(top: dict[str, Any]) -> dict[str, Any]:
    return {
        "torch_flattened_s2_norm_ablation": add_ablation_pass(
            tool_ablation(
                "torch Hopf S2 norm with full x,y,z base vector vs z-flattened control",
                baseline_value=top["s2_norm_min"],
                ablated_value=top["flattened_s2_norm_min"],
                tool="torch",
            )
        ),
        "geomstats_s2_metric_ablation": add_ablation_pass(
            tool_ablation(
                "geomstats S2 geodesic distance under broken component-phase action vs true global U(1) fiber action",
                baseline_value=top["geomstats_fiber_distance_summary"]["broken_fiber_geodesic_mean"],
                ablated_value=top["geomstats_fiber_distance_summary"]["global_fiber_geodesic_mean"],
                tool="geomstats",
            )
        ),
        "clifford_e3_structure_norm_ablation": add_ablation_pass(
            tool_ablation(
                "Clifford Cl(3) vector squared norm with e1,e2,e3 vs e3-erased projection",
                baseline_value=top["clifford_norm_summary"]["min_vector_square"],
                ablated_value=top["clifford_norm_summary"]["flattened_min_vector_square"],
                tool="clifford",
            )
        ),
    }


def build_controls(top: dict[str, Any]) -> dict[str, Any]:
    return {
        "flattened_s2_control": {
            "description": "remove the Hopf base z component and recompute S2 norm",
            "baseline_min_s2_norm": top["s2_norm_min"],
            "control_min_s2_norm": top["flattened_s2_norm_min"],
            "kills_norm_preservation": bool(top["flattened_s2_norm_min"] < 1.0 - KILL_FLOOR),
            "pass": bool(top["flattened_s2_norm_min"] < 1.0 - KILL_FLOOR),
        },
        "broken_fiber_component_phase_control": {
            "description": "rotate only z1 by a phase; this is not the global U(1) fiber action and it moves the S2 base",
            "baseline_global_phase_hopf_delta": top["max_global_phase_hopf_delta"],
            "control_component_phase_hopf_delta": top["max_broken_fiber_hopf_delta"],
            "kills_fiber_invariance": bool(top["max_broken_fiber_hopf_delta"] > KILL_FLOOR),
            "pass": bool(top["max_global_phase_hopf_delta"] <= EPS and top["max_broken_fiber_hopf_delta"] > KILL_FLOOR),
        },
        "dense_state_closure_rejected": {
            "description": "the carrier is a finite sample list of C^2 spinors and S2 outputs; no 2**N dense closure is materialized",
            "dense_state_closure_used": False,
            "largest_sample_count": max(SCALE_RUNGS),
            "dense_closure_label_only": False,
            "pass": True,
        },
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    torch_rows = {str(sample_count): torch_rung(sample_count) for sample_count in SCALE_RUNGS}
    jax_rows = {str(sample_count): jax_rung(sample_count) for sample_count in SCALE_RUNGS}
    parity = compare_torch_jax(torch_rows, jax_rows)
    top = torch_rows["64"]
    smt_proofs = build_smt_proofs(top)
    sympy_exact = sympy_hopf_identity()
    tool_ablations = build_tool_ablations(top)
    controls = build_controls(top)

    scale_rungs = {}
    for sample_count in SCALE_RUNGS:
        key = str(sample_count)
        row = torch_rows[key]
        jrow = jax_rows[key]
        rung_pass = bool(row["pass"] and jrow["pass"] and parity["rows"][key]["pass"] and row["dense_state_closure_used"] is False)
        scale_rungs[key] = {
            "sites_or_qubits": sample_count,
            "sample_count": sample_count,
            "dense_state_closure_used": False,
            "s2_norm_min": row["s2_norm_min"],
            "s2_norm_max": row["s2_norm_max"],
            "max_s2_norm_gap": row["max_s2_norm_gap"],
            "max_global_phase_hopf_delta": row["max_global_phase_hopf_delta"],
            "max_broken_fiber_hopf_delta": row["max_broken_fiber_hopf_delta"],
            "flattened_s2_norm_min": row["flattened_s2_norm_min"],
            "geomstats_consecutive_s2_geodesic_mean": row["geomstats_consecutive_s2_geodesic_mean"],
            "geomstats_global_fiber_geodesic_max": row["geomstats_fiber_distance_summary"]["global_fiber_geodesic_max"],
            "geomstats_broken_fiber_geodesic_mean": row["geomstats_fiber_distance_summary"]["broken_fiber_geodesic_mean"],
            "clifford_max_unit_gap": row["clifford_norm_summary"]["max_unit_gap"],
            "jax_s2_norm_min": jrow["s2_norm_min"],
            "jax_vs_pytorch_delta": parity["rows"][key]["max_value_delta"],
            "local_n01_order_gap": row["local_n01_order_witness"]["real_order_gap"],
            "pass": rung_pass,
        }

    scale_pass = all(row["pass"] for row in scale_rungs.values())
    proof_pass = all(row["pass"] for row in smt_proofs.values() if isinstance(row, dict)) and sympy_exact["pass"]
    controls_pass = all(row["pass"] for row in controls.values())
    ablation_pass = all(row["pass"] for row in tool_ablations.values())
    all_pass = bool(scale_pass and proof_pass and controls_pass and ablation_pass and parity["agree"])

    blockers = []
    if not scale_pass:
        blockers.append("one or more non-dense 8/16/32/64 Hopf sample rungs failed")
    if not proof_pass:
        blockers.append("helper-bound Hopf norm/fiber proof flip or sympy exact identity failed")
    if not controls_pass:
        blockers.append("one or more flattened/broken-fiber controls failed to kill the target invariant")
    if not ablation_pass:
        blockers.append("one or more numeric geometry ablations failed or had zero delta")
    if not parity["agree"]:
        blockers.append(f"jax_vs_pytorch_delta {parity['max_abs_delta']} exceeds tolerance")

    min_geom_capacity = min(
        min(row["s2_norm_min"] for row in scale_rungs.values()),
        min(row["local_n01_order_gap"] for row in scale_rungs.values()),
    )

    result = {
        "schema": "formal_scout_geometry_lego_result_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "object_id": OBJECT_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": time.time() - started,
        "classification": "lego",
        "tier": "canonical build STAGE 3 geometry object",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Build one standalone Hopf fibration geometry lego: H:S^3->S^2 over finite torch complex spinor samples at 8/16/32/64, with U(1) fiber invariance, controls, proof flips, JAX parity where representable, and genuine geometry ablations.",
        "scientific_question": "Does the finite torch Hopf map preserve S2 norm and global U(1) fiber phase invariance on a non-dense 8/16/32/64 sample carrier, while flattened and broken-fiber controls fail?",
        "finite_map": {
            "domain": "For n in {8,16,32,64}: finite normalized torch.complex128 spinor samples psi_i=(z0,z1) in S^3 subset C^2, plus global U(1) phase actions and bounded X/Z order controls.",
            "codomain_or_output": "Hopf base vectors H(psi_i)=(2 Re(z0 conj z1), 2 Im(z0 conj z1), |z0|^2-|z1|^2) in S^2, norm/fiber invariants, controls, proof verdicts, metric readouts, and blocked consumers.",
            "definition": "H maps each finite normalized spinor sample to a finite S2 base vector without dense state closure.",
        },
        "domain": {
            "sample_counts": list(SCALE_RUNGS),
            "spinor_components": 2,
            "carrier": "finite list of normalized torch.complex128 C^2 spinors on S^3",
            "fiber_group": "global U(1) phase e^(i theta) applied to both spinor components",
            "dense_state_closure_used": False,
        },
        "codomain_or_output": {
            "base": "finite torch.float64 S2 vectors in R^3",
            "primary_invariant": "|Hopf(psi)| = 1 and Hopf(e^(i theta) psi)=Hopf(psi)",
            "controls": "flattened S2 z-erasure and component-only broken-fiber phase twist",
        },
        "root_constraints": {
            "F01": {
                "role": "active",
                "statement": "finite carrier/probe/operator/path set: finite spinor samples, finite S2 outputs, finite U(1) phase probes, finite X/Z order controls, finite proof variables, and finite scale rungs.",
            },
            "N01": {
                "role": "active_bounded_witness",
                "statement": "phase rotation R_phi and swap X on the spinor carrier change the Hopf base in R_phi X vs X R_phi order while R_phi/R_phi commuting control has zero order gap.",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 noncommuting/order-sensitive operation/control witnessed by Hopf(R_phi X psi) vs Hopf(X R_phi psi)",
        ],
        "carrier_layer": "finite_normalized_torch_complex_spinor_samples_on_S3",
        "geometry_layer": "standalone Hopf fibration geometry object H:S3_to_S2",
        "carrier_realization": "torch.complex128 normalized C^2 spinor samples; no NumPy import, no tensor-to-NumPy conversion, no dense 2^N closure",
        "peps3d_embedding": "not_admitted_by_this_stage_3_geometry_object; no PEPS3D carrier or layer/manifold admission is claimed",
        "spinor_state": "finite torch.complex128 normalized spinors psi=(z0,z1) with |z0|^2+|z1|^2=1",
        "quaternion_action": "not_applicable: this Hopf geometry packet uses complex spinors and Clifford Cl(3), not quaternion language",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/F01_finite_distinguishability_results.json",
            "system_v5/ops/formal_scouts/results/carrier_torch_complex_spinor_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "Hopf map S^3 -> S^2 preserves S2 norm and is invariant under global U(1) fiber phase on finite torch spinor samples",
        "branch_status_before_run": "single standalone geometry lego requested by user; no manifold layer, G-structure, stack, bridge, flux, Axis0, FEP, gravity, or physics route opened",
        "allowed_claims": [
            "bounded Stage-3 standalone Hopf fibration geometry object result exists/runs if this JSON and required gates pass",
            "finite torch Hopf map samples have |Hopf(psi)|=1 at 8/16/32/64 without dense state closure",
            "global U(1) phase leaves Hopf base vectors unchanged while component-only broken-fiber phase moves the base",
            "helper-bound z3/cvc5 proof flips for measured real invariants against flattened/broken-fiber controls",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "standalone geometry object only",
            "no PEPS3D manifold carrier admitted here",
            "no G-structure completion or official selection",
            "no layer stacking, coupling, Xi, Phi0, Axis0, flux, FEP, gravity, bridge, basin, physics, or final manifold admission",
        ],
        "eligible_consumers": ["bounded later Stage-3 geometry object comparisons only after citing this result path and fresh gate output"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3 Hopf norm/fiber proof",
            "load_bearing_proof.smt_load_bearing cvc5 Hopf norm/fiber cross-check",
            "sympy exact Hopf norm identity and exact flattened-control counterexample",
        ],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_negatives": list(controls.keys()),
        "negatives_run": controls,
        "kill_conditions": {
            "flattened_s2_control": "min flattened S2 norm must fall below 1 and make the norm claim unsat",
            "broken_fiber_component_phase_control": "component-only phase must move the Hopf base while global U(1) phase does not",
            "dense_state_closure_rejected": "no dense closure may be used or laundered into the claim",
        },
        "required_artifacts": ["result JSON", "scale_ladder", "torch_primary_result", "jax_mirror_result", "proof_results", "controls", "tool_ablations"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "controls_pass": controls_pass,
            "tool_ablations_pass": ablation_pass,
            "jax_vs_pytorch_delta": parity["max_abs_delta"],
            "top_s2_norm_min": top["s2_norm_min"],
            "top_global_phase_delta": top["max_global_phase_hopf_delta"],
            "top_broken_fiber_delta": top["max_broken_fiber_hopf_delta"],
            "top_flattened_s2_norm_min": top["flattened_s2_norm_min"],
            "elapsed_seconds": time.time() - started,
        },
        "torch_primary_result": {
            "engine": "torch",
            "dtype": "torch.complex128",
            "claim": "Hopf map S^3->S^2 preserves S2 norm and global U(1) fiber phase",
            "rungs": torch_rows,
            "pass": bool(all(row["pass"] for row in torch_rows.values())),
        },
        "jax_mirror_result": {
            "engine": "jax",
            "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
            "claim": "JAX mirrors only the representable finite Hopf tensor algebra; no JAX geomstats path is claimed",
            "rungs": jax_rows,
            "not_represented": jax_rows["8"]["not_represented"],
            "pass": bool(all(row["pass"] for row in jax_rows.values())),
        },
        "jax_vs_pytorch_delta": parity["max_abs_delta"],
        "jax_vs_pytorch": parity,
        "proof_results": {
            **smt_proofs,
            "sympy_exact_hopf_identity": sympy_exact,
            "pass": proof_pass,
        },
        "controls": controls,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "scale_ladder": {
            "rungs": scale_rungs,
            "scale_axis": "finite_hopf_spinor_sample_count",
            "dense_state_closure_used": False,
            "pass": scale_pass,
        },
        "known_value_checks": {
            "known_value": "|Hopf(psi)|=1",
            "computed_by": ["torch finite samples", "jax representable mirror", "sympy exact identity", "clifford Cl(3) vector norm"],
            "torch_max_s2_norm_gap_at_64": top["max_s2_norm_gap"],
            "jax_max_s2_norm_gap_at_64": jax_rows["64"]["max_s2_norm_gap"],
            "sympy_identity_residual": sympy_exact["identity_residual_s2_minus_s3_squared"],
            "clifford_max_unit_gap_at_64": top["clifford_norm_summary"]["max_unit_gap"],
            "pass": bool(top["max_s2_norm_gap"] <= EPS and sympy_exact["pass"] and top["clifford_norm_summary"]["pass"]),
        },
        "positive": {
            "hopf_s2_norm_smt_flip": {"pass": smt_proofs["hopf_norm_preservation_smt_load_bearing"]["pass"]},
            "hopf_fiber_phase_smt_flip": {"pass": smt_proofs["hopf_fiber_phase_invariance_smt_load_bearing"]["pass"]},
            "scale_8_16_32_64_non_dense_samples": {"pass": scale_pass, "rungs": scale_rungs},
            "geomstats_s2_metric": {
                "backend": "pytorch",
                "global_fiber_geodesic_max": top["geomstats_fiber_distance_summary"]["global_fiber_geodesic_max"],
                "broken_fiber_geodesic_mean": top["geomstats_fiber_distance_summary"]["broken_fiber_geodesic_mean"],
                "pass": bool(top["geomstats_fiber_distance_summary"]["pass"]),
            },
            "clifford_cl3_base_vector_norm": top["clifford_norm_summary"],
            "local_n01_order_witness": top["local_n01_order_witness"],
        },
        "graveyard_companions": controls,
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "numpy_claim_bearing": {"used": False, "pass": True},
            "jax_geomstats_path": {"claimed": False, "reason": "geomstats has no JAX backend here", "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "g_structure_or_layer_claim": {"claimed": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
        },
        "nearby_variants": {
            "flattened_s2_control": controls["flattened_s2_control"],
            "broken_fiber_component_phase_control": controls["broken_fiber_component_phase_control"],
            "pass": controls_pass,
        },
        "shells": [
            {
                "name": "standalone_hopf_fibration_geometry_object",
                "status": "stage_3_geometry_lego_only",
                "rungs": list(SCALE_RUNGS),
                "s2_norm_min": min(row["s2_norm_min"] for row in scale_rungs.values()),
                "survives": all_pass,
            }
        ],
        "future_continuations": [
            "build another standalone geometry object or a bounded geometry comparison only after this result is cited and re-gated",
            "do not use this result as G-structure, layer, Xi/Phi0/Axis0/flux/FEP/gravity evidence",
        ],
        "compatibility_weights": {
            "local_stage3_geometry_input": 1.0 if all_pass else 0.0,
            "future_geometry_comparison_input": 0.5 if all_pass else 0.0,
            "Xi": 0.0,
            "Phi0": 0.0,
            "Axis0": 0.0,
            "flux": 0.0,
            "FEP": 0.0,
            "gravity": 0.0,
        },
        "compression_map": {
            "from": "finite torch.complex128 S3 spinor samples and Hopf base S2 vectors",
            "to": "S2 norm, U(1) phase invariance, broken controls, metric distances, Clifford norm, proof flips, scale ladder, and ablation deltas",
            "loss_boundary": "does not preserve or claim PEPS3D manifold carrier, G-structure completion, layer completion, Axis0, flux, FEP, gravity, bridge, or final manifold admission",
        },
        "present_survivor": {
            "object": OBJECT_ID,
            "capacity": min_geom_capacity,
            "survives": bool(all_pass),
            "blocked_capacity": BLOCKED_CONSUMERS,
        },
        "survivor_invariant": {
            "invariant": "geom_hopf_fibration survives iff every rung is non-dense, |Hopf(psi)|=1, global U(1) phase is invariant, broken controls fail, helper proof flips, JAX representable parity holds, geometry ablations are recomputed/nonzero, and promotion_allowed=false",
            "computed_capacity": min_geom_capacity,
            "threshold": KILL_FLOOR,
            "passed": bool(all_pass and min_geom_capacity > KILL_FLOOR),
        },
        "outward_record": {
            "result_path": str(OUT_PATH.relative_to(ROOT)),
            "per_sim_contract_command": f"../../../scripts/per_sim_contract.py {OUT_PATH.relative_to(ROOT)}",
            "max_deep_gate_command": f"../../../scripts/max_deep_lego_gate.py {OUT_PATH.relative_to(ROOT)} --scale-required --rigor",
            "recheck_proof_command": f"../../../scripts/recheck_proof.py {OUT_PATH.relative_to(ROOT)} --rerun {pathlib.Path(__file__).name} --python /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
            "claim_ceiling": "Stage-3 standalone Hopf fibration geometry lego only; no downstream consumer admitted",
            "direct_script_mode_note": "validator scripts are present but not executable in this checkout; run them with the project Python interpreter unless file mode is changed separately",
        },
        "pass_rule": "all 8/16/32/64 rungs are non-dense and pass; torch/JAX representable parts agree; Hopf norm+fiber proof flips real vs flattened/broken-fiber controls; controls kill; geomstats/clifford/torch ablations are recomputed and nonzero",
        "fail_rule": "fail on dense closure, missing rung, |Hopf| norm gap, global fiber phase movement, broken control not moving, no real/control SMT flip, JAX representable mismatch, fake JAX geomstats, zero/cosmetic ablation, or downstream promotion",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "why_not_v4_probes": "This is a Stage-3 standalone Hopf fibration geometry lego with finite non-dense 8/16/32/64 samples, proof flips, torch/JAX representable parity, geomstats PyTorch metric evidence, Clifford Cl(3) evidence, and promotion_allowed=false.",
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
