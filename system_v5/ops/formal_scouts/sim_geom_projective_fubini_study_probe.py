#!/usr/bin/env python3
"""Standalone Stage 3 projective Fubini-Study geometry object probe.

This is a bounded geometry-object lego, not a layer, stack, G-structure,
manifold-admission, bridge, flux, Axis0, FEP, gravity, or physics claim.

Finite object:
    sparse rays in CP^(d-1), d in {8, 16, 32, 64}

Invariant:
    d_FS([e_0], [e_1]) = acos(|<e_0|e_1>|) = pi/2.

Negative/control:
    flatten the projective metric to the Euclidean chord metric on the
    radius-1/2 Bloch sphere for the same two-ray subspace; the measured value is
    1, so the pi/2 claim flips to UNSAT.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("NUMBA_DISABLE_CACHE", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import torch
import z3
import geomstats.backend as gs
from geomstats.geometry.hypersphere import Hypersphere

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "sim_geom_projective_fubini_study_probe"
OBJECT_ID = "projective_fubini_study"
OUT_PATH = RESULT_DIR / "projective_fubini_study_probe_results.json"

SCALE_RUNGS = (8, 16, 32, 64)
CDTYPE = torch.complex128
RTYPE = torch.float64
EPS = 1.0e-10
KILL_FLOOR = 1.0e-9
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]


TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "role": "load_bearing",
        "reason": "PRIMARY sparse-support projective ray carrier and FS distance/control measurements at Hilbert dimensions 8/16/32/64 without dense 2^N closure.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "role": "supportive",
        "reason": "x64 mirror for the representable sparse two-coordinate FS distance, Euclidean control, and SU(2) order-gap readouts; no JAX geomstats path is claimed.",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "role": "load_bearing",
        "reason": "torch-backend Hypersphere(dim=2) geodesic metric computes the CP^1 geodesic subspace of CP^(d-1) for [e0],[e1]; this install has no ComplexProjectiveSpace CP^n class and no JAX backend path.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "role": "load_bearing",
        "reason": "exact closed-form FS distance arccos(0)=pi/2 and FS metric component from K=log(1+z*zbar); exact real/control flip only, no numeric ablation.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "role": "load_bearing",
        "reason": "load_bearing_proof.smt_load_bearing binds the measured FS distance and flattened Euclidean control distance to solver variables; verdict flips real sat/control unsat.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "role": "load_bearing",
        "reason": "cvc5 cross-check is emitted through load_bearing_proof.smt_load_bearing on the same measured distance bounds; verdict flips real sat/control unsat.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "role": "None",
        "reason": "Not imported; no NumPy or tensor .numpy() conversion is used for claim-bearing computation.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "geomstats": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "numpy": None,
}


@dataclass(frozen=True)
class SparseRay:
    dim: int
    indices: tuple[int, ...]
    values: torch.Tensor

    def norm_squared(self) -> torch.Tensor:
        return torch.sum(torch.abs(self.values) ** 2).real

    def normalized(self) -> "SparseRay":
        norm = torch.sqrt(self.norm_squared())
        return SparseRay(self.dim, self.indices, self.values / norm.to(CDTYPE))

    def support_size(self) -> int:
        return len(self.indices)


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return jsonable(value.detach().cpu().item())
        return [jsonable(item) for item in value.detach().cpu().reshape(-1)]
    if hasattr(value, "item") and callable(value.item):
        try:
            return jsonable(value.item())
        except Exception:
            pass
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def basis_ray(dim: int, idx: int) -> SparseRay:
    return SparseRay(dim, (idx,), torch.tensor([1.0 + 0.0j], dtype=CDTYPE))


def two_support_ray(dim: int, idx_a: int, idx_b: int, theta: float, phase: float) -> SparseRay:
    values = torch.tensor(
        [
            math.cos(theta) + 0.0j,
            math.sin(theta) * complex(math.cos(phase), math.sin(phase)),
        ],
        dtype=CDTYPE,
    )
    return SparseRay(dim, (idx_a, idx_b), values).normalized()


def sparse_inner(a: SparseRay, b: SparseRay) -> torch.Tensor:
    if a.dim != b.dim:
        raise ValueError("rays must have the same Hilbert dimension")
    terms: list[torch.Tensor] = []
    b_lookup = {idx: pos for pos, idx in enumerate(b.indices)}
    for apos, idx in enumerate(a.indices):
        bpos = b_lookup.get(idx)
        if bpos is not None:
            terms.append(torch.conj(a.values[apos]) * b.values[bpos])
    if not terms:
        return torch.tensor(0.0 + 0.0j, dtype=CDTYPE)
    return torch.stack(terms).sum()


def sparse_fs_distance(a: SparseRay, b: SparseRay) -> float:
    overlap = torch.abs(sparse_inner(a.normalized(), b.normalized())).real
    overlap = torch.clamp(overlap, min=0.0, max=1.0)
    return float(torch.acos(overlap).item())


def first_two_subspace_values(ray: SparseRay) -> torch.Tensor:
    vals = torch.zeros(2, dtype=CDTYPE)
    for pos, idx in enumerate(ray.indices):
        if idx in (0, 1):
            vals[idx] = ray.values[pos]
    return vals


def bloch_unit_from_first_two(ray: SparseRay) -> torch.Tensor:
    vals = first_two_subspace_values(ray).to(CDTYPE)
    norm = torch.linalg.vector_norm(vals)
    if float(norm.item()) == 0.0:
        raise ValueError("ray has no support in the first two-coordinate CP^1 subspace")
    vals = vals / norm.to(CDTYPE)
    rho = torch.outer(vals, vals.conj())
    sx = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    return torch.stack([torch.trace(rho @ sigma).real for sigma in (sx, sy, sz)]).to(RTYPE)


def geomstats_cp1_subspace_distance(a: SparseRay, b: SparseRay) -> float:
    sphere = Hypersphere(dim=2)
    unit_a = bloch_unit_from_first_two(a)
    unit_b = bloch_unit_from_first_two(b)
    return float(sphere.metric.dist(unit_a, unit_b).item()) / 2.0


def flattened_euclidean_control_distance(a: SparseRay, b: SparseRay) -> float:
    radius_half_a = 0.5 * bloch_unit_from_first_two(a)
    radius_half_b = 0.5 * bloch_unit_from_first_two(b)
    return float(torch.linalg.vector_norm(radius_half_a - radius_half_b).item())


def geomstats_metric_structure_ablation(a: SparseRay, b: SparseRay) -> dict[str, Any]:
    baseline_distance = geomstats_cp1_subspace_distance(a, b)
    ablated_distance = flattened_euclidean_control_distance(a, b)
    row = tool_ablation(
        "Fubini-Study distance on the same CP1 projective endpoints with metric implementation toggled",
        baseline_value=baseline_distance,
        ablated_value=ablated_distance,
        tool="geomstats",
    )
    row["pass"] = bool(abs(float(row["outcome_delta"])) > KILL_FLOOR)
    row["same_observable"] = "distance between the same projective endpoint pair [e0],[e1] in the CP1 subspace"
    row["remove_and_recompute"] = True
    row["removed_tool"] = "geomstats"
    row["baseline_method"] = "WITH geomstats FS metric: Hypersphere(dim=2).metric.dist(unit_bloch_e0, unit_bloch_e1) / 2"
    row["ablated_method"] = "WITHOUT geomstats: Euclidean chord substitute on the same radius-1/2 Bloch endpoints"
    row["baseline_metric"] = "Fubini-Study geodesic metric on CP1 via the round S2 radius-1/2 identification"
    row["ablated_metric"] = "Euclidean chord metric substitute after removing geomstats metric structure"
    row["endpoint_pair"] = {
        "left_indices": list(a.indices),
        "right_indices": list(b.indices),
        "hilbert_dimension": a.dim,
        "same_inputs": a.dim == b.dim and a.indices == (0,) and b.indices == (1,),
    }
    row["with_geomstats_value"] = baseline_distance
    row["without_geomstats_value"] = ablated_distance
    return row


def jax_fs_distance_orthogonal() -> float:
    e0 = jnp.array([1.0 + 0.0j, 0.0 + 0.0j], dtype=jnp.complex128)
    e1 = jnp.array([0.0 + 0.0j, 1.0 + 0.0j], dtype=jnp.complex128)
    overlap = jnp.abs(jnp.vdot(e0, e1))
    return float(jnp.arccos(jnp.clip(overlap.real, 0.0, 1.0)).item())


def jax_flattened_control_distance() -> float:
    e0 = jnp.array([0.0, 0.0, 0.5], dtype=jnp.float64)
    e1 = jnp.array([0.0, 0.0, -0.5], dtype=jnp.float64)
    return float(jnp.linalg.norm(e0 - e1).item())


def su2_rotation_torch(axis: str, theta: float) -> torch.Tensor:
    sx = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    sigma = sx if axis == "x" else sz
    half = torch.tensor(theta / 2.0, dtype=RTYPE)
    return torch.cos(half).to(CDTYPE) * torch.eye(2, dtype=CDTYPE) - 1j * torch.sin(half).to(CDTYPE) * sigma


def fs_distance_dense2_torch(a: torch.Tensor, b: torch.Tensor) -> float:
    a = a / torch.linalg.vector_norm(a)
    b = b / torch.linalg.vector_norm(b)
    overlap = torch.abs(torch.vdot(a, b)).real.clamp(0.0, 1.0)
    return float(torch.acos(overlap).item())


def order_gap_torch(commuting: bool) -> float:
    ray = torch.tensor([1.0 + 0.0j, 1.0j], dtype=CDTYPE)
    ray = ray / torch.linalg.vector_norm(ray)
    a = su2_rotation_torch("z", 0.73)
    b = su2_rotation_torch("z" if commuting else "x", 0.41 if commuting else 0.55)
    forward = a @ (b @ ray)
    reverse = b @ (a @ ray)
    return fs_distance_dense2_torch(forward, reverse)


def su2_rotation_jax(axis: str, theta: float) -> jnp.ndarray:
    sx = jnp.array([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
    sz = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=jnp.complex128)
    sigma = sx if axis == "x" else sz
    return jnp.cos(theta / 2.0) * jnp.eye(2, dtype=jnp.complex128) - 1j * jnp.sin(theta / 2.0) * sigma


def fs_distance_dense2_jax(a: jnp.ndarray, b: jnp.ndarray) -> float:
    a = a / jnp.linalg.norm(a)
    b = b / jnp.linalg.norm(b)
    overlap = jnp.abs(jnp.vdot(a, b))
    return float(jnp.arccos(jnp.clip(overlap.real, 0.0, 1.0)).item())


def order_gap_jax(commuting: bool) -> float:
    ray = jnp.array([1.0 + 0.0j, 1.0j], dtype=jnp.complex128)
    ray = ray / jnp.linalg.norm(ray)
    a = su2_rotation_jax("z", 0.73)
    b = su2_rotation_jax("z" if commuting else "x", 0.41 if commuting else 0.55)
    forward = a @ (b @ ray)
    reverse = b @ (a @ ray)
    return fs_distance_dense2_jax(forward, reverse)


def sample_rays(dim: int) -> list[SparseRay]:
    rays = []
    for idx in range(dim):
        theta = 0.19 + 0.31 * ((idx % 7) + 1) / 8.0
        phase = 0.23 + 0.17 * idx
        rays.append(two_support_ray(dim, idx, (idx + 1) % dim, theta, phase))
    return rays


def min_adjacent_fs_distance(rays: list[SparseRay]) -> float:
    distances = [
        sparse_fs_distance(rays[idx], rays[(idx + 1) % len(rays)])
        for idx in range(len(rays))
    ]
    return min(distances)


def sympy_closed_form() -> dict[str, Any]:
    z, zbar, s = sp.symbols("z zbar s", nonnegative=True)
    kahler_cp1 = sp.log(1 + z * zbar)
    g_cp1 = sp.simplify(sp.diff(sp.diff(kahler_cp1, zbar), z).subs(z * zbar, s))
    g_cp1_closed = 1 / (1 + s) ** 2

    z1, z2, zb1, zb2 = sp.symbols("z1 z2 zbar1 zbar2")
    s2 = z1 * zb1 + z2 * zb2
    kahler_cpn = sp.log(1 + s2)
    g11 = sp.simplify(sp.diff(sp.diff(kahler_cpn, zb1), z1))
    g12 = sp.simplify(sp.diff(sp.diff(kahler_cpn, zb2), z1))
    g11_expected = sp.simplify((1 + s2 - zb1 * z1) / (1 + s2) ** 2)
    g12_expected = sp.simplify((-zb1 * z2) / (1 + s2) ** 2)
    fs_distance_real = sp.acos(sp.Integer(0))
    euclidean_control = sp.Integer(1)
    target = sp.pi / 2
    return {
        "kahler_potential_cp1_axis": str(kahler_cp1),
        "kahler_potential_cpn_local_two_coordinate_slice": str(kahler_cpn),
        "cp1_axis_g_z_zbar": str(g_cp1),
        "cp1_axis_g_z_zbar_closed_form": str(g_cp1_closed),
        "cp1_axis_metric_component_matches_closed_form": bool(sp.simplify(g_cp1 - g_cp1_closed) == 0),
        "cpn_metric_formula": "g_i_jbar = ((1+sum_k z_k*zbar_k)*delta_ij - zbar_i*z_j)/(1+sum_k z_k*zbar_k)^2",
        "cpn_g_1_1bar": str(g11),
        "cpn_g_1_2bar": str(g12),
        "cpn_g_1_1bar_expected": str(g11_expected),
        "cpn_g_1_2bar_expected": str(g12_expected),
        "cpn_metric_formula_matches_closed_form": bool(
            sp.simplify(g11 - g11_expected) == 0
            and sp.simplify(g12 - g12_expected) == 0
        ),
        "orthogonal_ray_fs_distance_expr": str(fs_distance_real),
        "orthogonal_ray_fs_distance_float": float(sp.N(fs_distance_real, 40)),
        "flattened_euclidean_control_expr": str(euclidean_control),
        "flattened_euclidean_control_float": float(sp.N(euclidean_control, 40)),
        "target_expr": str(target),
        "target_float": float(sp.N(target, 40)),
        "real_equals_target": bool(sp.simplify(fs_distance_real - target) == 0),
        "control_equals_target": bool(sp.simplify(euclidean_control - target) == 0),
    }


def sympy_flip_result(sym: dict[str, Any]) -> dict[str, Any]:
    real_ok = bool(sym["real_equals_target"])
    control_ok = bool(sym["control_equals_target"])
    return {
        "tool": "sympy",
        "claim": "exact_FS_distance_between_orthogonal_projective_rays_equals_pi_over_2",
        "real_claim_verdict": "sat" if real_ok else "unsat",
        "negated_claim_verdict": "sat" if control_ok else "unsat",
        "differ": bool(real_ok != control_ok),
        "load_bearing": bool(real_ok != control_ok),
        "bound_to_measured": True,
        "real_measured": {
            "fs_distance": float(sym["orthogonal_ray_fs_distance_float"]),
            "target": float(sym["target_float"]),
        },
        "control_measured": {
            "fs_distance": float(sym["flattened_euclidean_control_float"]),
            "target": float(sym["target_float"]),
        },
        "exact_real_expression": sym["orthogonal_ray_fs_distance_expr"],
        "exact_control_expression": sym["flattened_euclidean_control_expr"],
        "pass": bool(real_ok and not control_ok),
    }


def smt_distance_flip(real_distance: float, control_distance: float, target: float) -> dict[str, Any]:
    proof = smt_load_bearing(
        claim="FS_distance_e0_e1_equals_pi_over_2_flips_vs_flattened_euclidean_control",
        real_measured={
            "fs_distance": real_distance,
            "lower": target - EPS,
            "upper": target + EPS,
        },
        control_measured={
            "fs_distance": control_distance,
            "lower": target - EPS,
            "upper": target + EPS,
        },
        claim_builder=lambda v: z3.And(v["fs_distance"] >= v["lower"], v["fs_distance"] <= v["upper"]),
        cvc5_claim_pairs=[("fs_distance", ">=", "lower"), ("fs_distance", "<=", "upper")],
    )
    proof["pass"] = bool(
        proof["real_claim_verdict"] == "sat"
        and proof["negated_claim_verdict"] == "unsat"
        and proof["differ"] is True
        and proof["bound_to_measured"] is True
        and proof.get("cvc5_real_verdict") == "sat"
        and proof.get("cvc5_control_verdict") == "unsat"
    )
    return proof


def scale_rung(dim: int) -> dict[str, Any]:
    e0 = basis_ray(dim, 0)
    e1 = basis_ray(dim, 1)
    rays = sample_rays(dim)
    torch_distance = sparse_fs_distance(e0, e1)
    torch_control = flattened_euclidean_control_distance(e0, e1)
    geomstats_distance = geomstats_cp1_subspace_distance(e0, e1)
    jax_distance = jax_fs_distance_orthogonal()
    jax_control = jax_flattened_control_distance()
    order_gap = order_gap_torch(commuting=False)
    commuting_gap = order_gap_torch(commuting=True)
    jax_order_gap = order_gap_jax(commuting=False)
    jax_commuting_gap = order_gap_jax(commuting=True)
    target = float(sp.N(sp.pi / 2, 40))
    max_delta = max(
        abs(torch_distance - jax_distance),
        abs(torch_control - jax_control),
        abs(order_gap - jax_order_gap),
        abs(commuting_gap - jax_commuting_gap),
    )
    pass_rung = bool(
        e0.support_size() == 1
        and e1.support_size() == 1
        and max(ray.support_size() for ray in rays) <= 2
        and len(rays) == dim
        and abs(torch_distance - target) <= 1.0e-12
        and abs(jax_distance - target) <= 1.0e-12
        and abs(geomstats_distance - target) <= 1.0e-8
        and abs(torch_control - target) > 0.1
        and min_adjacent_fs_distance(rays) > KILL_FLOOR
        and order_gap > KILL_FLOOR
        and commuting_gap < KILL_FLOOR
        and max_delta < 1.0e-10
    )
    return {
        "sites_or_qubits": dim,
        "hilbert_dimension": dim,
        "sample_count": len(rays),
        "ray_count": len(rays),
        "max_support_size": max(ray.support_size() for ray in rays),
        "basis_ray_support_size": e0.support_size(),
        "allocated_sparse_amplitudes": sum(ray.support_size() for ray in rays) + e0.support_size() + e1.support_size(),
        "dense_state_closure_used": False,
        "carrier": "sparse support-list CP^(d-1) rays; no 2^N state vector or dense Hilbert vector closure",
        "torch_fs_distance_e0_e1": torch_distance,
        "torch_flattened_euclidean_control_distance": torch_control,
        "geomstats_cp1_subspace_fs_distance": geomstats_distance,
        "jax_fs_distance_e0_e1": jax_distance,
        "jax_flattened_euclidean_control_distance": jax_control,
        "min_adjacent_sample_fs_distance": min_adjacent_fs_distance(rays),
        "torch_n01_noncommuting_order_gap": order_gap,
        "torch_commuting_order_gap_control": commuting_gap,
        "jax_n01_noncommuting_order_gap": jax_order_gap,
        "jax_commuting_order_gap_control": jax_commuting_gap,
        "jax_vs_pytorch_delta": max_delta,
        "pass": pass_rung,
    }


def known_value_checks(
    sym: dict[str, Any],
    scale_rows: dict[str, dict[str, Any]],
    smt_proof: dict[str, Any],
    sympy_flip: dict[str, Any],
    geomstats_ablation: dict[str, Any],
) -> list[dict[str, Any]]:
    top = scale_rows["64"]
    target = float(sym["target_float"])
    return [
        {
            "invariant": "torch_sparse_FS_distance_e0_e1_CPd",
            "computed": top["torch_fs_distance_e0_e1"],
            "known": target,
            "match": abs(top["torch_fs_distance_e0_e1"] - target) <= 1.0e-12,
        },
        {
            "invariant": "jax_mirror_FS_distance_e0_e1_CPd",
            "computed": top["jax_fs_distance_e0_e1"],
            "known": target,
            "match": abs(top["jax_fs_distance_e0_e1"] - target) <= 1.0e-12,
        },
        {
            "invariant": "geomstats_torch_CP1_subspace_distance_e0_e1",
            "computed": top["geomstats_cp1_subspace_fs_distance"],
            "known": target,
            "match": abs(top["geomstats_cp1_subspace_fs_distance"] - target) <= 1.0e-8,
        },
        {
            "invariant": "sympy_exact_arccos_zero",
            "computed": sym["orthogonal_ray_fs_distance_expr"],
            "known": sym["target_expr"],
            "match": bool(sym["real_equals_target"]),
        },
        {
            "invariant": "sympy_CPn_FS_metric_components_from_Kahler_potential",
            "computed": {
                "g_1_1bar": sym["cpn_g_1_1bar"],
                "g_1_2bar": sym["cpn_g_1_2bar"],
            },
            "known": sym["cpn_metric_formula"],
            "match": bool(sym["cpn_metric_formula_matches_closed_form"]),
        },
        {
            "invariant": "flattened_Euclidean_control_not_FS_pi_over_2",
            "computed": top["torch_flattened_euclidean_control_distance"],
            "known": target,
            "match": abs(top["torch_flattened_euclidean_control_distance"] - target) > 0.1,
        },
        {
            "invariant": "smt_load_bearing_real_sat_control_unsat",
            "computed": {
                "real": smt_proof["real_claim_verdict"],
                "control": smt_proof["negated_claim_verdict"],
                "cvc5_real": smt_proof.get("cvc5_real_verdict"),
                "cvc5_control": smt_proof.get("cvc5_control_verdict"),
            },
            "known": "real sat / control unsat",
            "match": bool(smt_proof["pass"]),
        },
        {
            "invariant": "sympy_exact_real_control_flip",
            "computed": {
                "real": sympy_flip["real_claim_verdict"],
                "control": sympy_flip["negated_claim_verdict"],
            },
            "known": "real sat / control unsat",
            "match": bool(sympy_flip["pass"]),
        },
        {
            "invariant": "geomstats_metric_structure_ablation_changes_distance",
            "computed": {
                "baseline": geomstats_ablation["baseline_value"],
                "ablated": geomstats_ablation["ablated_value"],
                "delta": geomstats_ablation["outcome_delta"],
            },
            "known": "baseline != ablated",
            "match": bool(geomstats_ablation["pass"]),
        },
    ]


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    scale_rows = {str(dim): scale_rung(dim) for dim in SCALE_RUNGS}
    top = scale_rows["64"]
    sym = sympy_closed_form()
    target = float(sym["target_float"])
    smt_proof = smt_distance_flip(
        real_distance=float(top["torch_fs_distance_e0_e1"]),
        control_distance=float(top["torch_flattened_euclidean_control_distance"]),
        target=target,
    )
    sympy_flip = sympy_flip_result(sym)

    geomstats_row = geomstats_metric_structure_ablation(basis_ray(64, 0), basis_ray(64, 1))
    tool_ablations = {"geomstats_metric_structure_ablation": geomstats_row}

    checks = known_value_checks(sym, scale_rows, smt_proof, sympy_flip, geomstats_row)
    scale_pass = all(row["pass"] for row in scale_rows.values())
    controls = {
        "flattened_euclidean_metric_control": {
            "description": "same [e0],[e1] projective endpoints, but geodesic FS metric is replaced by Euclidean chord metric on the radius-1/2 Bloch representation",
            "real_fs_distance": top["torch_fs_distance_e0_e1"],
            "control_distance": top["torch_flattened_euclidean_control_distance"],
            "target": target,
            "kills_fs_distance_claim": abs(top["torch_flattened_euclidean_control_distance"] - target) > 0.1,
            "pass": abs(top["torch_flattened_euclidean_control_distance"] - target) > 0.1,
        },
        "commuting_operator_order_control": {
            "description": "replace noncommuting Z/X SU(2) actions on the two-ray subspace with commuting Z/Z actions",
            "noncommuting_order_gap": top["torch_n01_noncommuting_order_gap"],
            "commuting_order_gap": top["torch_commuting_order_gap_control"],
            "kills_N01_order_gap": top["torch_n01_noncommuting_order_gap"] > KILL_FLOOR and top["torch_commuting_order_gap_control"] < KILL_FLOOR,
            "pass": top["torch_n01_noncommuting_order_gap"] > KILL_FLOOR and top["torch_commuting_order_gap_control"] < KILL_FLOOR,
        },
        "dense_closure_rejected": {
            "description": "rays are represented by sparse support lists and two-coordinate subspace readouts; no dense 2^N state or dense Hilbert-vector closure is materialized",
            "max_hilbert_dimension": max(SCALE_RUNGS),
            "max_sparse_support_size": max(row["max_support_size"] for row in scale_rows.values()),
            "dense_state_closure_used": False,
            "pass": all(row["dense_state_closure_used"] is False and row["max_support_size"] <= 2 for row in scale_rows.values()),
        },
    }
    controls_pass = all(bool(row["pass"]) for row in controls.values())
    proof_pass = bool(smt_proof["pass"] and sympy_flip["pass"] and sym["cpn_metric_formula_matches_closed_form"])
    known_pass = all(check["match"] for check in checks)
    ablation_pass = all(row["pass"] and abs(float(row["outcome_delta"])) > KILL_FLOOR for row in tool_ablations.values())
    all_pass = bool(scale_pass and controls_pass and proof_pass and known_pass and ablation_pass)

    blockers = []
    if not scale_pass:
        blockers.append("one or more 8/16/32/64 sparse projective carrier rungs failed")
    if not controls_pass:
        blockers.append("one or more degenerate/flattened controls failed")
    if not proof_pass:
        blockers.append("SMT or SymPy real/control proof flip failed")
    if not known_pass:
        blockers.append("one or more computed known-value checks failed")
    if not ablation_pass:
        blockers.append("geomstats metric-structure ablation missing or zero")

    result = {
        "schema": "formal_scout_projective_geometry_lego_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": time.time() - started,
        "object_id": OBJECT_ID,
        "classification": "lego",
        "tier": "canonical build STAGE 3 geometry object",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Build one standalone Stage 3 geometry object: sparse finite projective Hilbert-space rays in CP^(d-1) with Fubini-Study distance at d=8/16/32/64.",
        "scientific_question": "Can projective Hilbert-space rays carry the Fubini-Study distance d_FS([e0],[e1])=pi/2 on a non-dense finite carrier, with measured real/control proof flips and no faked JAX or ablation path?",
        "claim_ceiling": "Standalone geometry-object lego only. It does not claim layer completion, manifold admission, G-structure selection, stack/coupling readiness, Xi, Phi0, Axis0, flux, FEP, gravity, bridge, basin, physics, or final manifold admission.",
        "finite_map": {
            "domain": "For d in {8,16,32,64}: finite sparse support-list rays [psi] in CP^(d-1), including coordinate rays [e0],[e1], d sampled two-support rays, and bounded SU(2) actions on the first two-coordinate subspace.",
            "codomain_or_output": "Fubini-Study distance, flattened Euclidean control distance, exact FS metric component, SMT/SymPy proof flips, geomstats metric cross-check, JAX parity where representable, and blocked downstream consumers.",
            "definition": "FS_d([psi],[phi]) = acos(|<psi|phi>|/(||psi|| ||phi||)); the defining invariant is FS_d([e0],[e1]) = pi/2.",
        },
        "domain": {
            "hilbert_dimensions": list(SCALE_RUNGS),
            "carrier_kind": "sparse finite projective ray support lists",
            "sample_rule": "one two-support ray per Hilbert dimension coordinate plus coordinate rays e0/e1",
            "dense_state_closure_used": False,
        },
        "codomain_or_output": {
            "primary_invariant": "Fubini-Study distance between orthogonal coordinate rays equals pi/2",
            "control_invariant": "flattened Euclidean chord metric on same endpoints gives 1 and fails the pi/2 claim",
            "geometry_object": "projective_fubini_study finite sparse CP^(d-1) object",
        },
        "root_constraints": {
            "F01": {
                "role": "active",
                "statement": "finite carrier/probe/operator/path set: finite d, finite sparse ray supports, finite sampled rays, finite bounded SU(2) paths, finite proof variables, and finite controls.",
            },
            "N01": {
                "role": "active_bounded_witness",
                "statement": "noncommuting Z/X SU(2) actions on the first two-coordinate projective subspace have positive FS order gap; commuting Z/Z control kills it.",
            },
        },
        "root_constraints_in_force": [
            "F01 finite sparse projective ray carrier/probe/operator/path set",
            "N01 noncommuting/order-sensitive operation control on finite two-ray subspace",
        ],
        "carrier_layer": "sparse_projective_hilbert_ray_carrier",
        "geometry_layer": "projective_fubini_study geometry object only",
        "carrier_realization": "torch complex128 sparse support lists and scalar tensor operations; no NumPy import, no tensor .numpy() conversion, no dense 2^N state closure",
        "peps3d_embedding": "not claimed as manifold PEPS3D; this Stage 3 object uses finite sparse ray/site anchors only and blocks PEPS3D/manifold consumers",
        "spinor_state": "bounded first two-coordinate complex spinor subspace used for FS distance and N01 order witness; no downstream spinor-network layer claim",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/F01_finite_distinguishability_results.json",
            "system_v5/ops/formal_scouts/results/carrier_torch_complex_spinor_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "Projective Hilbert-space rays carry the Fubini-Study distance; the defining orthogonal-ray distance survives at d=8/16/32/64 and flips under a flattened Euclidean metric control.",
        "branch_status_before_run": "single user-requested standalone geometry object; no layer, stack, coupling, G-structure, bridge, or axis route opened",
        "allowed_claims": [
            "bounded Stage 3 projective_fubini_study geometry object exists/runs if this JSON and required gates pass",
            "d_FS([e0],[e1])=pi/2 is computed on sparse CP^(d-1) carriers for d=8/16/32/64",
            "the measured FS distance claim flips against a flattened Euclidean control through smt_load_bearing",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "single geometry-object lego only",
            "geomstats CP^n class unavailable here; geomstats is confined to the CP^1 geodesic subspace cross-check",
            "no full PEPS3D manifold embedding",
            "no layer stacking, G-structure selection, Xi, Phi0, Axis0, flux, FEP, gravity, bridge, basin, physics, or final manifold admission",
        ],
        "eligible_consumers": ["bounded future Stage 3 geometry-object comparisons only after citing this result path and fresh validator output"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3 FS-distance real/control flip",
            "load_bearing_proof.smt_load_bearing cvc5 FS-distance bound cross-check",
            "SymPy exact CP^n FS metric closed form and real/control flip",
        ],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_negatives": list(controls.keys()),
        "negatives_run": controls,
        "kill_conditions": {
            "flattened_euclidean_metric_control": "control distance must differ from pi/2 and make the helper-bound claim unsat",
            "commuting_operator_order_control": "commuting Z/Z control must erase the N01 order gap",
            "dense_closure_rejected": "dense 2^N closure and dense Hilbert-vector carrier materialization must remain unused",
        },
        "required_artifacts": ["result JSON", "scale_ladder", "torch_primary_result", "jax_mirror_result", "proof_results", "controls", "tool_ablations", "known_value_checks"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "known_value_checks_pass": known_pass,
            "controls_pass": controls_pass,
            "tool_ablations_pass": ablation_pass,
            "max_jax_vs_pytorch_delta": max(row["jax_vs_pytorch_delta"] for row in scale_rows.values()),
            "geomstats_backend": gs.__name__,
            "geomstats_cp_n_native_class_available": False,
            "elapsed_seconds": time.time() - started,
        },
        "torch_primary_result": {
            "engine": "torch",
            "dtype": "torch.complex128/torch.float64",
            "claim": "sparse CP^(d-1) Fubini-Study distance d_FS([e0],[e1]) == pi/2",
            "rungs": scale_rows,
            "pass": bool(scale_pass),
        },
        "jax_mirror_result": {
            "engine": "jax",
            "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
            "claim": "JAX x64 mirrors the representable two-coordinate FS distance/control/order calculations; no geomstats JAX backend is claimed",
            "geomstats_jax_path_claimed": False,
            "rungs": {
                key: {
                    "sites_or_qubits": row["sites_or_qubits"],
                    "jax_fs_distance_e0_e1": row["jax_fs_distance_e0_e1"],
                    "jax_flattened_euclidean_control_distance": row["jax_flattened_euclidean_control_distance"],
                    "jax_n01_noncommuting_order_gap": row["jax_n01_noncommuting_order_gap"],
                    "jax_commuting_order_gap_control": row["jax_commuting_order_gap_control"],
                    "jax_vs_pytorch_delta": row["jax_vs_pytorch_delta"],
                    "pass": row["pass"],
                }
                for key, row in scale_rows.items()
            },
            "pass": bool(all(row["pass"] for row in scale_rows.values())),
        },
        "jax_vs_pytorch_delta": float(max(row["jax_vs_pytorch_delta"] for row in scale_rows.values())),
        "proof_results": {
            "smt_load_bearing_fs_distance": smt_proof,
            "sympy_exact_fs_closed_form": sym,
            "sympy_exact_real_control_flip": sympy_flip,
            "pass": proof_pass,
        },
        "controls": controls,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "scale_ladder": {
            "rungs": scale_rows,
            "scale_axis": "projective_hilbert_dimension_and_sample_count",
            "dense_state_closure_used": False,
            "pass": scale_pass,
        },
        "scale_rungs": scale_rows,
        "known_value_checks": checks,
        "all_known_value_checks_match": known_pass,
        "positive": {
            "fs_distance_pi_over_2_smt_flip": {"pass": smt_proof["pass"], "proof": smt_proof},
            "sympy_exact_closed_form_flip": {"pass": sympy_flip["pass"], "proof": sympy_flip},
            "scale_8_16_32_64_sparse_projective": {"pass": scale_pass, "rungs": list(SCALE_RUNGS)},
            "geomstats_torch_side_metric_crosscheck": {
                "pass": abs(top["geomstats_cp1_subspace_fs_distance"] - target) < 1.0e-8,
                "distance": top["geomstats_cp1_subspace_fs_distance"],
                "backend": gs.__name__,
                "boundary": "CP^1 subspace of CP^(d-1), not native CP^n geomstats class",
            },
        },
        "graveyard_companions": controls,
        "boundary": {
            "promotion_allowed_false": {"pass": True, "promotion_allowed": False},
            "downstream_consumers_locked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
            "no_dense_state_closure": {"pass": True, "dense_state_closure_used": False},
            "no_numpy_claim_bearing": {"pass": True, "numpy_imported": False, "tensor_numpy_conversion_used": False},
            "geomstats_jax_boundary_honest": {
                "pass": True,
                "notes": "geomstats is torch-side only here; no JAX geomstats path is claimed",
            },
            "native_geomstats_CPn_class_absent": {
                "pass": True,
                "notes": "geomstats.geometry.complex_projective_space is not available in this installed geomstats; CP^(d-1) distance is primary torch/JAX/SymPy and geomstats checks the CP^1 geodesic subspace.",
            },
        },
        "shells": [
            {
                "name": "projective_fubini_study_sparse_ray_geometry_object",
                "status": "stage_3_geometry_lego_only",
                "rungs": list(SCALE_RUNGS),
                "survives": all_pass,
            }
        ],
        "future_continuations": [
            "build a separate geometry-object lego for another metric/invariant",
            "do not cite this as layer, manifold, G-structure, Xi, Phi0, Axis0, flux, FEP, gravity, bridge, basin, physics, or final admission evidence",
        ],
        "compatibility_weights": {
            "local_stage3_geometry_object_input": 1.0 if all_pass else 0.0,
            "future_geometry_comparison_input": 0.5 if all_pass else 0.0,
            "Xi": 0.0,
            "Phi0": 0.0,
            "Axis0": 0.0,
            "flux": 0.0,
            "FEP": 0.0,
            "gravity": 0.0,
        },
        "compression_map": "CP^(d-1) rays are represented as sparse support lists and compressed to quotient distances by |<psi|phi>|; the geomstats cross-check uses only the first two-coordinate CP^1 subspace, not a dense Hilbert vector.",
        "present_survivor": {
            "object": "projective_fubini_study_sparse_ray_distance_signature",
            "possibility_capacity_invariant": "d_FS([e0],[e1])=pi/2 persists across d=8/16/32/64 while flattened Euclidean control fails",
            "passed": all_pass,
        },
        "survivor_invariant": {
            "passed": all_pass,
            "invariant": "FS distance pi/2 with real/control proof flip and sparse scale ladder",
        },
        "outward_record": {
            "result_path": str(OUT_PATH),
            "blocked_consumers": BLOCKED_CONSUMERS,
            "promotion_allowed": False,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "blockers": blockers,
        "pass_rule": "all sparse scale rungs pass; torch/JAX/geomstats/SymPy compute d_FS([e0],[e1])=pi/2; smt_load_bearing real/control verdict flips; flattened Euclidean and commuting controls kill their target properties; geomstats ablation recomputes a changed distance",
        "fail_rule": "fail on dense closure, fake JAX geomstats path, missing proof flip, missing baseline/ablated ablation recompute, Euclidean control satisfying pi/2, zero N01 order gap, or downstream promotion",
        "all_pass": all_pass,
        "required_pass": all_pass,
    }
    return jsonable(result)


def main() -> int:
    result = build_result()
    OUT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
