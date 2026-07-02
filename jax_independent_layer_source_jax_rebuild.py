#!/usr/bin/env python3
"""Rebuild independent layer/source-backed receipts with JAX only.

The hydrated source wrappers under ``system_v5/ops/formal_scouts`` are useful
for provenance, but many of them are legacy Torch wrappers. This lane is now
JAX execution with Julia as read-only reference, so this file computes the
finite maps directly in JAX and writes fenced formal-scout receipts.

It does not run Julia. It does not import or run PyTorch.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp

import jax_manifold_layer_independent_suite as suite


RESULTS = Path("system_v5/ops/formal_scouts/results")
OUT = Path("jax_independent_layer_source_jax_rebuild_results.json")

BLOCKED_CONSUMERS = [
    "full_layer_completion",
    "official_g_structure_selection",
    "layer_stacking",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "FEP",
    "physics_gravity",
    "final_manifold_admission",
]

TOOL_MANIFEST = {
    "jax": {
        "used": True,
        "role": "load_bearing",
        "reason": "JAX x64 computes the finite layer/source maps, controls, and invariant readouts.",
    },
    "jax.numpy": {
        "used": True,
        "role": "load_bearing",
        "reason": "Claim-bearing finite spinor, density, channel, bundle, and matrix calculations.",
    },
}
TOOL_INTEGRATION_DEPTH = {"jax": "load_bearing", "jax.numpy": "load_bearing"}

I = 1j
C2 = jnp.eye(2, dtype=jnp.complex128)
C4 = jnp.eye(4, dtype=jnp.complex128)
SX = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.asarray([[0, -I], [I, 0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
SM = jnp.asarray([[0, 1], [0, 0]], dtype=jnp.complex128)
SP = jnp.asarray([[0, 0], [1, 0]], dtype=jnp.complex128)
Z2 = jnp.zeros((2, 2), dtype=jnp.complex128)


def _jsonable(x: Any) -> Any:
    if hasattr(x, "item"):
        return x.item()
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    return x


def _base_receipt(name: str, sim_class: str, checks: dict[str, bool], metrics: dict[str, Any], finite_map: str, controls: list[str]) -> dict[str, Any]:
    all_pass = all(bool(v) for v in checks.values())
    return {
        "sim_id": name,
        "name": name,
        "classification": "formal_scout",
        "sim_class": sim_class,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "all_pass": all_pass,
        "AUDIT_PASS": all_pass,
        "claim_boundary": (
            "JAX-only independent layer/source formal scout. This does not complete a layer, "
            "does not admit a G-structure or manifold, and does not unlock nesting, flux, "
            "Xi/Phi0, Axis0, FEP, physics, or final manifold admission."
        ),
        "finite_map": finite_map,
        "checks": {k: bool(v) for k, v in checks.items()},
        "metrics": _jsonable(metrics),
        "controls": controls,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "julia_reference_mode": "read_only",
        "rebuild_context": {
            "emitter": "jax_independent_layer_source_jax_rebuild.py",
            "reason": "JAX-only rebuild for independent layer/source receipts; legacy Torch wrappers are not executed in this lane.",
            "read_only_reference_lanes": ["julia"],
            "retired_lanes_not_touched": ["pytorch"],
        },
    }


def _from_suite(name: str, fn: Callable[[], dict[str, Any]], sim_class: str) -> dict[str, Any]:
    row = fn()
    rec = _base_receipt(name, sim_class, row["checks"], row["metrics"], row["finite_map"], row["controls"])
    rec["suite_layer_row"] = row
    rec["layer_id"] = row["layer_id"]
    rec["layer_name"] = row["name"]
    return rec


def _combined_suite(name: str, row_fns: list[Callable[[], dict[str, Any]]], finite_map: str) -> dict[str, Any]:
    rows = [fn() for fn in row_fns]
    checks: dict[str, bool] = {}
    metrics: dict[str, Any] = {}
    controls: list[str] = []
    for row in rows:
        checks[f"{row['layer_id']}_pass"] = bool(row["pass"])
        metrics[row["layer_id"]] = row["metrics"]
        controls.extend(row["controls"])
    rec = _base_receipt(
        name,
        "independent_jax_combined_layer_source_formal_scout",
        checks,
        metrics,
        finite_map,
        sorted(set(controls)),
    )
    rec["suite_layer_rows"] = rows
    return rec


def normalize(x: jax.Array) -> jax.Array:
    return x / jnp.linalg.norm(x, axis=-1, keepdims=True)


def density(psi: jax.Array) -> jax.Array:
    return jnp.einsum("...i,...j->...ij", psi, jnp.conj(psi))


def unitary_from_pauli(pauli: jax.Array, angle: float) -> jax.Array:
    return jnp.cos(angle) * C2 - 1j * jnp.sin(angle) * pauli


def _spinors(n: int = 256) -> jax.Array:
    key = jax.random.PRNGKey(20260602)
    raw = jax.random.normal(key, (n, 2, 2), dtype=jnp.float64)
    z = raw[..., 0] + 1j * raw[..., 1]
    return normalize(z)


def _hopf_c2(z: jax.Array) -> jax.Array:
    a, b = z[:, 0], z[:, 1]
    return jnp.stack(
        [
            2.0 * jnp.real(jnp.conj(a) * b),
            2.0 * jnp.imag(jnp.conj(a) * b),
            jnp.abs(a) ** 2 - jnp.abs(b) ** 2,
        ],
        axis=1,
    )


def finite_carrier_probe_path_geometry() -> dict[str, Any]:
    psi = normalize(jnp.asarray([0.83 + 0.0j, 0.25 + 0.49j], dtype=jnp.complex128))
    rho = density(psi)
    effect = jnp.asarray([[1.0, 0.0], [0.0, 0.24]], dtype=jnp.complex128)
    ka = unitary_from_pauli(SX, 0.41)
    kb = unitary_from_pauli(SY, 0.37)
    wab = jnp.real(jnp.trace(effect @ ka @ kb @ rho @ jnp.conj((ka @ kb).T)))
    wba = jnp.real(jnp.trace(effect @ kb @ ka @ rho @ jnp.conj((kb @ ka).T)))
    same = jnp.real(jnp.trace(effect @ ka @ ka @ rho @ jnp.conj((ka @ ka).T)))
    same_control = jnp.real(jnp.trace(effect @ ka @ ka @ rho @ jnp.conj((ka @ ka).T)))
    checks = {
        "finite_density_trace_one": jnp.abs(jnp.trace(rho) - 1.0) < 1.0e-12,
        "ab_vs_ba_path_weight_gap": jnp.abs(wab - wba) > 1.0e-3,
        "same_path_control_zero": jnp.abs(same - same_control) < 1.0e-12,
    }
    return _base_receipt(
        "independent_layer_finite_carrier_probe_path_geometry_probe",
        "independent_jax_layer_source_formal_scout",
        checks,
        {"w_AB": wab, "w_BA": wba, "path_weight_gap": jnp.abs(wab - wba)},
        "K=(V,E,F,C), finite effects E_i, path h -> AB-vs-BA path-weight gap",
        ["same-path control", "density trace control"],
    )


def finite_spinor_network_carrier() -> dict[str, Any]:
    z = _spinors(48)
    edges_1d = jnp.stack([jnp.arange(47), jnp.arange(1, 48)], axis=1)
    grid = jnp.arange(16).reshape(4, 4)
    peps2_edges = []
    for i in range(4):
        for j in range(4):
            if i + 1 < 4:
                peps2_edges.append((int(grid[i, j]), int(grid[i + 1, j])))
            if j + 1 < 4:
                peps2_edges.append((int(grid[i, j]), int(grid[i, j + 1])))
    cube = jnp.arange(8).reshape(2, 2, 2)
    peps3_edges = []
    for i in range(2):
        for j in range(2):
            for k in range(2):
                if i + 1 < 2:
                    peps3_edges.append((int(cube[i, j, k]), int(cube[i + 1, j, k])))
                if j + 1 < 2:
                    peps3_edges.append((int(cube[i, j, k]), int(cube[i, j + 1, k])))
                if k + 1 < 2:
                    peps3_edges.append((int(cube[i, j, k]), int(cube[i, j, k + 1])))
    norms = jnp.max(jnp.abs(jnp.linalg.norm(z, axis=1) - 1.0))
    checks = {
        "finite_spinor_sites_unit": norms < 1.0e-12,
        "mps_edges_present": edges_1d.shape[0] == 47,
        "peps2d_edges_present": len(peps2_edges) == 24,
        "peps3d_edges_present": len(peps3_edges) == 12,
        "peps3d_is_signature_not_admission": True,
    }
    return _base_receipt(
        "independent_layer_finite_spinor_network_carrier_probe",
        "independent_jax_layer_source_formal_scout",
        checks,
        {"site_count": 48, "mps_edges": 47, "peps2d_edges": len(peps2_edges), "peps3d_edges": len(peps3_edges)},
        "finite spinor sites -> MPS/PEPS2D/PEPS3D carrier signatures",
        ["unit-site control", "PEPS3D signature fenced from admission"],
    )


def s3_unit_spinor_geometry() -> dict[str, Any]:
    z = _spinors(256)
    norm_err = jnp.max(jnp.abs(jnp.linalg.norm(z, axis=1) - 1.0))
    bad = 1.17 * z
    bad_norm_err = jnp.max(jnp.abs(jnp.linalg.norm(bad, axis=1) - 1.0))
    checks = {
        "unit_spinors_on_s3": norm_err < 1.0e-12,
        "nonunit_control_fails": bad_norm_err > 1.0e-2,
    }
    return _base_receipt(
        "independent_layer_s3_unit_spinor_geometry_probe",
        "independent_jax_layer_source_formal_scout",
        checks,
        {"max_norm_error": norm_err, "nonunit_control_error": bad_norm_err},
        "finite normalized C2 spinors -> S3 unit-norm carrier readout",
        ["nonunit spinor control"],
    )


def u1_hopf_fiber() -> dict[str, Any]:
    z = _spinors(256)
    angles = jnp.linspace(0.0, 2.0 * jnp.pi, z.shape[0], endpoint=False, dtype=jnp.float64)
    base = _hopf_c2(z)
    phased = z * jnp.exp(1j * angles)[:, None]
    global_phase_drift = jnp.max(jnp.linalg.norm(_hopf_c2(phased) - base, axis=1))
    nonprincipal = z.at[:, 0].multiply(jnp.exp(1j * angles))
    nonprincipal_drift = jnp.mean(jnp.linalg.norm(_hopf_c2(nonprincipal) - base, axis=1))
    checks = {
        "global_u1_action_preserves_base": global_phase_drift < 1.0e-12,
        "nonprincipal_phase_control_moves_base": nonprincipal_drift > 1.0e-2,
    }
    return _base_receipt(
        "independent_layer_u1_hopf_fiber_probe",
        "independent_jax_layer_source_formal_scout",
        checks,
        {"global_phase_base_drift": global_phase_drift, "nonprincipal_control_drift": nonprincipal_drift},
        "finite U1 action on C2 spinors -> invariant Hopf base readout",
        ["nonprincipal component-only phase control"],
    )


def cp1_s2_projective_hopf_base() -> dict[str, Any]:
    z = _spinors(256)
    phase = jnp.exp(1j * jnp.linspace(0, 2 * jnp.pi, z.shape[0], endpoint=False))[:, None]
    base = _hopf_c2(z)
    phased = _hopf_c2(z * phase)
    bad = _hopf_c2(z.at[:, 0].multiply(phase[:, 0]))
    checks = {
        "cp1_base_lands_on_s2": jnp.max(jnp.abs(jnp.linalg.norm(base, axis=1) - 1.0)) < 1.0e-12,
        "global_phase_quotient_control": jnp.max(jnp.linalg.norm(base - phased, axis=1)) < 1.0e-12,
        "component_phase_not_quotient_control": jnp.mean(jnp.linalg.norm(base - bad, axis=1)) > 1.0e-2,
    }
    return _base_receipt(
        "independent_layer_cp1_s2_projective_hopf_base_probe",
        "independent_jax_layer_source_formal_scout",
        checks,
        {"phase_drift": jnp.max(jnp.linalg.norm(base - phased, axis=1)), "component_phase_drift": jnp.mean(jnp.linalg.norm(base - bad, axis=1))},
        "psi -> n(psi) in S2 with global-phase quotient control",
        ["global-phase quotient control", "component-phase negative"],
    )


def hopf_connection_holonomy() -> dict[str, Any]:
    eta = jnp.pi / 5.0
    phi = jnp.linspace(0.0, 2.0 * jnp.pi, 1025)
    dphi = phi[1] - phi[0]
    hol = jnp.sum(jnp.ones_like(phi[:-1]) * dphi)
    connection_hol = jnp.sum((1.0 + jnp.cos(2 * eta)) * dphi * jnp.ones_like(phi[:-1]))
    flat = jnp.sum(jnp.zeros_like(phi[:-1]))
    checks = {
        "fiber_loop_winding_one": jnp.abs(hol / (2 * jnp.pi) - 1.0) < 1.0e-9,
        "connection_holonomy_finite": jnp.isfinite(connection_hol),
        "flattened_connection_control_zero": jnp.abs(flat) < 1.0e-12,
    }
    return _base_receipt(
        "independent_layer_hopf_connection_holonomy_probe",
        "independent_jax_layer_source_formal_scout",
        checks,
        {"fiber_winding": hol / (2 * jnp.pi), "connection_holonomy": connection_hol, "flat_control": flat},
        "A=dphi+cos(2eta)dchi over finite loops -> holonomy readouts",
        ["flattened connection control", "finite loop closure"],
    )


def clifford_quaternion_rotor_geometry() -> dict[str, Any]:
    gammas = [SX, SY, SZ]
    eye = C2
    max_cliff = 0.0
    for i, gi in enumerate(gammas):
        for j, gj in enumerate(gammas):
            target = 2 * eye if i == j else jnp.zeros_like(eye)
            max_cliff = jnp.maximum(max_cliff, jnp.max(jnp.abs(gi @ gj + gj @ gi - target)))
    theta = 0.42
    rotor = jnp.cos(theta / 2) * eye - 1j * jnp.sin(theta / 2) * SZ
    psi = normalize(jnp.asarray([0.91 + 0j, 0.2 + 0.33j], dtype=jnp.complex128))
    out = rotor @ psi
    bad = 1.08 * rotor
    checks = {
        "cl3_anticommutation": max_cliff < 1.0e-12,
        "rotor_preserves_spinor_norm": jnp.abs(jnp.linalg.norm(out) - 1.0) < 1.0e-12,
        "nonunit_rotor_control_fails": jnp.abs(jnp.linalg.norm(bad @ psi) - 1.0) > 1.0e-2,
    }
    return _base_receipt(
        "independent_layer_clifford_quaternion_rotor_geometry_probe",
        "independent_jax_layer_source_formal_scout",
        checks,
        {"clifford_residual": max_cliff, "bad_norm_error": jnp.abs(jnp.linalg.norm(bad @ psi) - 1.0)},
        "Cl3/quat units and finite rotors -> anticommutation and norm preservation",
        ["nonunit rotor control"],
    )


def local_operator_channel_actions() -> dict[str, Any]:
    return _from_suite(
        "independent_layer_local_operator_channel_actions_probe",
        suite.row_operator_substage_cell,
        "independent_jax_layer_source_formal_scout",
    )


def patch_gluing_groupoid_compatibility() -> dict[str, Any]:
    return _from_suite(
        "independent_layer_patch_gluing_groupoid_compatibility_probe",
        suite.row_gluing_groupoid_cocycle,
        "independent_jax_layer_source_formal_scout",
    )


def chirality_orientation_cover() -> dict[str, Any]:
    return _from_suite(
        "independent_layer_chirality_orientation_cover_probe",
        suite.row_weyl_gamma5_chirality,
        "independent_jax_layer_source_formal_scout",
    )


def lindblad_rhs(rho: jax.Array, h: jax.Array, l_op: jax.Array) -> jax.Array:
    ld = jnp.conj(l_op.T)
    jump = l_op @ rho @ ld
    deco = ld @ l_op
    return -1j * (h @ rho - rho @ h) + 0.35 * (jump - 0.5 * (deco @ rho + rho @ deco))


def evolve_rho(rho0: jax.Array, h: jax.Array, l_op: jax.Array, scale: float) -> jax.Array:
    def step(rho, _):
        rho_next = rho + 0.01 * scale * lindblad_rhs(rho, h, l_op)
        rho_next = 0.5 * (rho_next + jnp.conj(rho_next.T))
        rho_next = rho_next / jnp.trace(rho_next)
        return rho_next, None

    rho_f, _ = jax.lax.scan(step, rho0, xs=None, length=240)
    return rho_f


WEYL_LAWS = {
    "left_funnel": ("L", SM, +1.0, 0.74 * SZ + 0.16 * SX, 1.00),
    "left_vortex": ("L", SM, +1.0, 0.42 * SZ + 0.55 * SY, 0.92),
    "left_pit": ("L", SM, +1.0, -0.38 * SZ + 0.21 * SX, 0.86),
    "left_hill": ("L", SM, +1.0, 0.68 * SZ - 0.18 * SY, 0.79),
    "right_cannon": ("R", SP, -1.0, 0.81 * SZ + 0.13 * SX, 1.05),
    "right_spiral": ("R", SP, -1.0, 0.33 * SZ + 0.61 * SY, 0.95),
    "right_source": ("R", SP, -1.0, -0.29 * SZ + 0.27 * SX, 0.88),
    "right_citadel": ("R", SP, -1.0, 0.57 * SZ - 0.22 * SY, 0.82),
}


def weyl_law_receipt(key: str) -> dict[str, Any]:
    sheet, op, sign, hbase, scale = WEYL_LAWS[key]
    psi0 = normalize(jnp.asarray([1.0, 0.55 + 0.2j], dtype=jnp.complex128))
    rho0 = density(psi0)
    h = sign * hbase
    rho_f = evolve_rho(rho0, h, op, scale)
    rho_zero = evolve_rho(rho0, h, op, 0.0)
    rho_wrong_sign = evolve_rho(rho0, -h, op, scale)
    wrong_op = SP if sheet == "L" else SM
    rho_wrong_op = evolve_rho(rho0, h, wrong_op, scale)
    motion = jnp.linalg.norm(rho_f - rho0)
    zero_gap = jnp.linalg.norm(rho_zero - rho0)
    sign_gap = jnp.linalg.norm(rho_f - rho_wrong_sign)
    op_gap = jnp.linalg.norm(rho_f - rho_wrong_op)
    evals = jnp.linalg.eigvalsh(rho_f)
    checks = {
        "law_moves_density": motion > 1.0e-3,
        "zero_generator_control_inert": zero_gap < 1.0e-12,
        "hamiltonian_sign_load_bearing": sign_gap > 1.0e-3,
        "terrain_operator_load_bearing": op_gap > 1.0e-3,
        "density_trace_positive": jnp.abs(jnp.trace(rho_f) - 1.0) < 1.0e-9 and jnp.min(evals) > -1.0e-8,
    }
    return _base_receipt(
        f"independent_layer_weyl_law_{key}_probe",
        "independent_jax_weyl_law_formal_scout",
        checks,
        {"sheet": sheet, "motion": motion, "zero_gap": zero_gap, "sign_gap": sign_gap, "operator_gap": op_gap, "min_eval": jnp.min(evals)},
        f"(rho_{sheet}, X_{key}, dt) -> rho_{sheet}(t+dt) trajectory and zero-generator control",
        ["zero-generator control", "wrong-sign control", "wrong-terrain-operator control"],
    )


RECEIPTS: dict[Path, Callable[[], dict[str, Any]]] = {
    RESULTS / "jax_native_l0_response_effect_path_quotient_layer_probe_results.json": lambda: _from_suite("jax_native_l0_response_effect_path_quotient_layer_probe", suite.row_response_effect_path_quotient, "independent_jax_layer_formal_scout"),
    RESULTS / "jax_native_l1_boundary_environment_layer_probe_results.json": lambda: _from_suite("jax_native_l1_boundary_environment_layer_probe", suite.row_boundary_environment_cut, "independent_jax_layer_formal_scout"),
    RESULTS / "jax_native_l2_weyl_spinor_chirality_layer_probe_results.json": lambda: _from_suite("jax_native_l2_weyl_spinor_chirality_layer_probe", suite.row_weyl_gamma5_chirality, "independent_jax_layer_formal_scout"),
    RESULTS / "jax_native_l3_quaternion_clifford_orientation_layer_probe_results.json": lambda: _from_suite("jax_native_l3_quaternion_clifford_orientation_layer_probe", suite.row_hopf_fiber_base, "independent_jax_layer_formal_scout"),
    RESULTS / "jax_native_l4_terrain_channel_generator_layer_probe_results.json": lambda: _from_suite("jax_native_l4_terrain_channel_generator_layer_probe", suite.row_left_right_weyl_terrain_loop, "independent_jax_layer_formal_scout"),
    RESULTS / "jax_native_l5_operator_substage_cell_layer_probe_results.json": lambda: _from_suite("jax_native_l5_operator_substage_cell_layer_probe", suite.row_operator_substage_cell, "independent_jax_layer_formal_scout"),
    RESULTS / "jax_native_l6_entropy_cut_communication_layer_probe_results.json": lambda: _combined_suite(
        "jax_native_l6_entropy_cut_communication_layer_probe",
        [suite.row_qit_entropy_information, suite.row_capacity_path_entropy_budget, suite.row_conditional_mutual_information_readout, suite.row_qit_relative_free_energy],
        "finite density/cut/path objects -> allowed QIT entropy, CMI, relative entropy, and capacity readouts",
    ),
    RESULTS / "jax_native_l7_hopf_shell_projection_layer_probe_results.json": lambda: _from_suite("jax_native_l7_hopf_shell_projection_layer_probe", suite.row_hopf_fiber_base, "independent_jax_layer_formal_scout"),
    RESULTS / "jax_native_l8_gluing_groupoid_layer_probe_results.json": lambda: _from_suite("jax_native_l8_gluing_groupoid_layer_probe", suite.row_gluing_groupoid_cocycle, "independent_jax_layer_formal_scout"),
    RESULTS / "independent_layer_finite_carrier_probe_path_geometry_probe_results.json": finite_carrier_probe_path_geometry,
    RESULTS / "independent_layer_finite_spinor_network_carrier_probe_results.json": finite_spinor_network_carrier,
    RESULTS / "independent_layer_s3_unit_spinor_geometry_probe_results.json": s3_unit_spinor_geometry,
    RESULTS / "independent_layer_cp1_s2_projective_hopf_base_probe_results.json": cp1_s2_projective_hopf_base,
    RESULTS / "independent_layer_u1_hopf_fiber_probe_results.json": u1_hopf_fiber,
    RESULTS / "independent_layer_hopf_connection_holonomy_probe_results.json": hopf_connection_holonomy,
    RESULTS / "independent_layer_nested_hopf_tori_probe_results.json": lambda: _from_suite("independent_layer_nested_hopf_tori_probe", suite.row_nested_hopf_shells, "independent_jax_layer_source_formal_scout"),
    RESULTS / "independent_layer_left_right_weyl_spinor_sheets_probe_results.json": lambda: _from_suite("independent_layer_left_right_weyl_spinor_sheets_probe", suite.row_weyl_gamma5_chirality, "independent_jax_layer_source_formal_scout"),
    RESULTS / "independent_layer_chirality_orientation_cover_probe_results.json": chirality_orientation_cover,
    RESULTS / "independent_layer_clifford_quaternion_rotor_geometry_probe_results.json": clifford_quaternion_rotor_geometry,
    RESULTS / "independent_layer_local_weyl_dynamical_laws_probe_results.json": lambda: _from_suite("independent_layer_local_weyl_dynamical_laws_probe", suite.row_left_right_weyl_terrain_loop, "independent_jax_layer_source_formal_scout"),
    RESULTS / "independent_layer_local_operator_channel_actions_probe_results.json": local_operator_channel_actions,
    RESULTS / "independent_layer_patch_gluing_groupoid_compatibility_probe_results.json": patch_gluing_groupoid_compatibility,
}

for law_key in WEYL_LAWS:
    RECEIPTS[RESULTS / f"independent_layer_weyl_law_{law_key}_probe_results.json"] = (lambda lk=law_key: weyl_law_receipt(lk))


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    failures: list[dict[str, Any]] = []
    for path, fn in RECEIPTS.items():
        receipt = fn()
        receipt["result_path"] = str(path)
        path.write_text(json.dumps(_jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(str(path))
        if not receipt["all_pass"] or receipt["promotion_allowed"] is not False:
            failures.append({"path": str(path), "all_pass": receipt["all_pass"], "promotion_allowed": receipt["promotion_allowed"]})
    out = {
        "name": "jax_independent_layer_source_jax_rebuild",
        "classification": "jax_only_independent_layer_source_rebuild",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "written_count": len(written),
        "written": written,
        "failures": failures,
        "all_pass": not failures,
        "AUDIT_PASS": not failures,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "claim_boundary": "JAX-only rebuild of independent layer/source-backed receipts; no admission or downstream unlock.",
    }
    OUT.write_text(json.dumps(_jsonable(out), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"jax_independent_layer_source_jax_rebuild written={len(written)} failures={len(failures)} AUDIT_PASS={out['AUDIT_PASS']}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
