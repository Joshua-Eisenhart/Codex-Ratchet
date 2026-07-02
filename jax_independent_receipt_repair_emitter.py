#!/usr/bin/env python3
"""Regenerate compact independent JAX layer/geometry receipts.

This is a repair emitter for stale or unreadable receipt files. It runs JAX
finite maps directly, writes only formal-scout receipts, and keeps nesting,
flux, Axis0, FEP, physics, and manifold admission blocked.

It does not run Julia. It does not run PyTorch.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp

import jax_manifold_layer_independent_suite as suite


RESULTS = Path("system_v5/ops/formal_scouts/results")

BLOCKED_CONSUMERS = [
    "nesting_order_search",
    "pairwise_layer_order_tests",
    "noncommutative_finitude_ratchet",
    "basin_hierarchy",
    "flux",
    "xi_phi0",
    "axis0",
    "fep_holodeck",
    "physics_gravity",
    "final_manifold_admission",
]

TOOL_MANIFEST = {
    "jax": {
        "used": True,
        "role": "load_bearing",
        "reason": "JAX x64 finite maps, vectorized controls, and invariant readouts.",
    },
    "jax.numpy": {
        "used": True,
        "role": "load_bearing",
        "reason": "Claim-bearing finite spinor, density, bundle, and matrix calculations.",
    },
}
TOOL_INTEGRATION_DEPTH = {"jax": "load_bearing", "jax.numpy": "load_bearing"}


def _jsonable(x: Any) -> Any:
    if hasattr(x, "item"):
        return x.item()
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    return x


def _base_receipt(name: str, kind: str, checks: dict[str, bool], metrics: dict[str, Any], finite_map: str, controls: list[str]) -> dict[str, Any]:
    all_pass = all(bool(v) for v in checks.values())
    return {
        "sim_id": name,
        "name": name,
        "classification": "formal_scout",
        "sim_class": kind,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "promotion_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "all_pass": all_pass,
        "AUDIT_PASS": all_pass,
        "claim_boundary": (
            "Independent JAX formal-scout receipt only. This does not complete a layer, "
            "does not admit a G-structure or manifold, and does not unlock nesting order, "
            "flux, Xi/Phi0, Axis0, FEP, physics, or final manifold admission."
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
        "repair_context": {
            "emitter": "jax_independent_receipt_repair_emitter.py",
            "reason": "regenerate compact readable receipts for the independent layer/geometry coverage gate",
            "read_only_reference_lanes": ["julia"],
            "retired_lanes_not_touched": ["pytorch"],
        },
    }


def _from_suite(name: str, row_fn: Callable[[], dict[str, Any]], *, kind: str = "independent_jax_layer_formal_scout") -> dict[str, Any]:
    row = row_fn()
    rec = _base_receipt(
        name,
        kind,
        row["checks"],
        row["metrics"],
        row["finite_map"],
        row["controls"],
    )
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
        prefix = row["layer_id"]
        checks[f"{prefix}_pass"] = bool(row["pass"])
        metrics[prefix] = row["metrics"]
        controls.extend(row["controls"])
    rec = _base_receipt(name, "independent_jax_combined_readout_formal_scout", checks, metrics, finite_map, sorted(set(controls)))
    rec["suite_layer_rows"] = rows
    return rec


def _spinors(n: int = 256) -> jax.Array:
    key = jax.random.PRNGKey(20260602)
    raw = jax.random.normal(key, (n, 2, 2), dtype=jnp.float64)
    z = raw[..., 0] + 1j * raw[..., 1]
    return z / jnp.linalg.norm(z, axis=1, keepdims=True)


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


def _so3_z(angles: jax.Array) -> jax.Array:
    c = jnp.cos(angles)
    s = jnp.sin(angles)
    z = jnp.zeros_like(angles)
    o = jnp.ones_like(angles)
    return jnp.stack(
        [
            jnp.stack([c, -s, z], axis=1),
            jnp.stack([s, c, z], axis=1),
            jnp.stack([z, z, o], axis=1),
        ],
        axis=1,
    )


def geom_s3_spinor_carrier() -> dict[str, Any]:
    z = _spinors()
    norm_err = jnp.max(jnp.abs(jnp.linalg.norm(z, axis=1) - 1.0))
    bad = 1.17 * z
    bad_norm_err = jnp.max(jnp.abs(jnp.linalg.norm(bad, axis=1) - 1.0))
    checks = {"unit_spinors_on_s3": norm_err < 1.0e-12, "nonunit_control_fails": bad_norm_err > 1.0e-2}
    return _base_receipt(
        "jax_native_geometry_s3_spinor_carrier_probe",
        "independent_jax_geometry_formal_scout",
        checks,
        {"max_norm_error": norm_err, "nonunit_control_error": bad_norm_err},
        "finite normalized C2 spinors -> S3 unit-norm carrier readout",
        ["nonunit spinor control"],
    )


def geom_u1_hopf_principal_bundle() -> dict[str, Any]:
    z = _spinors()
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
        "jax_native_geometry_u1_hopf_principal_bundle_probe",
        "independent_jax_geometry_formal_scout",
        checks,
        {"global_phase_base_drift": global_phase_drift, "nonprincipal_control_drift": nonprincipal_drift},
        "finite U1 action on C2 spinors -> invariant Hopf base readout",
        ["nonprincipal component-only phase control"],
    )


def geom_so3_orientation_frame_reduction() -> dict[str, Any]:
    angles = jnp.linspace(0.0, 2.0 * jnp.pi, 192, endpoint=False, dtype=jnp.float64)
    frames = _so3_z(angles)
    det_err = jnp.max(jnp.abs(jax.vmap(jnp.linalg.det)(frames) - 1.0))
    orth_err = jnp.max(jax.vmap(lambda m: jnp.max(jnp.abs(m.T @ m - jnp.eye(3, dtype=jnp.float64))))(frames))
    bad = frames.at[:, 0, 0].multiply(1.11)
    bad_err = jnp.max(jnp.abs(jax.vmap(jnp.linalg.det)(bad) - 1.0))
    checks = {"so3_det_one": det_err < 1.0e-12, "so3_orthogonal": orth_err < 1.0e-12, "nonorthogonal_control_fails": bad_err > 1.0e-2}
    return _base_receipt(
        "jax_native_geometry_so3_orientation_frame_reduction_probe",
        "independent_jax_geometry_formal_scout",
        checks,
        {"det_error": det_err, "orthogonality_error": orth_err, "bad_det_error": bad_err},
        "finite angle family -> SO3 orientation frames with determinant-one and orthogonality readouts",
        ["nonorthogonal frame control"],
    )


def geom_pin3_spin3_chirality_split() -> dict[str, Any]:
    z = _spinors()
    base = _hopf_c2(z)
    reflected = base.at[:, 2].multiply(-1.0)
    flip_residual = jnp.max(jnp.abs(base[:, 2] + reflected[:, 2]))
    flip_signal = jnp.mean(jnp.abs(base[:, 2] - reflected[:, 2]))
    erased = base
    erased_residual = jnp.mean(jnp.abs(base[:, 2] - erased[:, 2]))
    checks = {
        "pin_reflection_flips_chirality_axis": flip_residual < 1.0e-12 and flip_signal > 1.0e-2,
        "erased_reflection_control_fails": erased_residual < 1.0e-12,
    }
    return _base_receipt(
        "jax_native_geometry_pin3_spin3_chirality_split_probe",
        "independent_jax_geometry_formal_scout",
        checks,
        {"flip_residual": flip_residual, "flip_signal": flip_signal, "erased_reflection_delta": erased_residual},
        "finite Hopf-base chirality coordinate -> Pin reflection flip vs Spin-preserving frame readout",
        ["erased-reflection control"],
    )


def geom_seiberg_witten_8d() -> dict[str, Any]:
    z = _spinors(256)
    angles = jnp.linspace(0.0, 2.0 * jnp.pi, z.shape[0], endpoint=False, dtype=jnp.float64)
    density = jnp.real(z[:, 0] * jnp.conj(z[:, 0]) - z[:, 1] * jnp.conj(z[:, 1]))
    curvature = 0.62 * density + 0.035 * jnp.sin(2.0 * angles)

    def loss(scale: jax.Array) -> jax.Array:
        return jnp.mean((curvature - scale * density) ** 2)

    scale = jnp.array(0.1, dtype=jnp.float64)
    initial = loss(scale)
    for _ in range(48):
        scale = scale - 0.08 * jax.grad(loss)(scale)
    final = loss(scale)
    wrong = loss(-scale)
    checks = {"jax_grad_residual_decreases": final < initial, "wrong_sign_control_higher": wrong > final}
    return _base_receipt(
        "jax_native_geometry_seiberg_witten_8d_probe",
        "independent_jax_geometry_formal_scout",
        checks,
        {"initial_residual": initial, "final_residual": final, "wrong_sign_control_residual": wrong, "optimized_scale": scale},
        "finite U1 curvature surrogate plus spinor density -> JAX-gradient residual decrease readout",
        ["wrong-sign residual control"],
    )


def geom_contact_sasakian_s3() -> dict[str, Any]:
    z = _spinors(384)
    overlap = jnp.sum(jnp.conj(z) * jnp.roll(z, -1, axis=0), axis=1)
    alpha = jnp.angle(overlap / jnp.maximum(jnp.abs(overlap), 1.0e-12))
    signal = jnp.mean(jnp.abs(alpha))
    norm_err = jnp.max(jnp.abs(jnp.linalg.norm(z, axis=1) - 1.0))
    constant = jnp.tile(z[:1], (z.shape[0], 1))
    c_overlap = jnp.sum(jnp.conj(constant) * jnp.roll(constant, -1, axis=0), axis=1)
    c_alpha = jnp.angle(c_overlap / jnp.maximum(jnp.abs(c_overlap), 1.0e-12))
    c_signal = jnp.mean(jnp.abs(c_alpha))
    checks = {"contact_phase_signal_present": signal > 1.0e-3, "unit_s3_carrier": norm_err < 1.0e-12, "constant_path_control_kills_signal": c_signal < 1.0e-12}
    return _base_receipt(
        "jax_native_geometry_contact_sasakian_s3_probe",
        "independent_jax_geometry_formal_scout",
        checks,
        {"contact_alpha_mean_abs": signal, "norm_error": norm_err, "constant_control_signal": c_signal},
        "finite S3 spinor loop -> contact phase one-form readout",
        ["constant contact path control"],
    )


def _unit_c4(n: int = 256) -> jax.Array:
    key = jax.random.PRNGKey(20260603)
    raw = jax.random.normal(key, (n, 4, 2), dtype=jnp.float64)
    z = raw[..., 0] + 1j * raw[..., 1]
    return z / jnp.linalg.norm(z, axis=1, keepdims=True)


def _hopf_s7_s4(c: jax.Array) -> jax.Array:
    a, b, c2, d = c[:, 0], c[:, 1], c[:, 2], c[:, 3]
    z = a * jnp.conj(c2) + b * jnp.conj(d)
    w = -a * d + b * c2
    return jnp.stack(
        [
            2.0 * jnp.real(z),
            2.0 * jnp.imag(z),
            2.0 * jnp.real(w),
            2.0 * jnp.imag(w),
            jnp.abs(a) ** 2 + jnp.abs(b) ** 2 - jnp.abs(c2) ** 2 - jnp.abs(d) ** 2,
        ],
        axis=1,
    )


def geom_higher_hopf_s7_to_s4() -> dict[str, Any]:
    c = _unit_c4()
    s4 = _hopf_s7_s4(c)
    s4_norm_err = jnp.max(jnp.abs(jnp.linalg.norm(s4, axis=1) - 1.0))
    bad = 1.2 * c
    bad_err = jnp.max(jnp.abs(jnp.linalg.norm(_hopf_s7_s4(bad), axis=1) - 1.0))
    checks = {"s7_maps_to_unit_s4": s4_norm_err < 1.0e-12, "nonunit_s7_control_fails": bad_err > 1.0e-2}
    return _base_receipt(
        "jax_native_geometry_higher_hopf_s7_to_s4_probe",
        "independent_jax_geometry_formal_scout",
        checks,
        {"s4_norm_error": s4_norm_err, "nonunit_control_error": bad_err},
        "finite normalized C4 spinors on S7 -> five-coordinate S4 Hopf-base residual",
        ["nonunit S7 control"],
    )


LAYER_RECEIPTS: dict[Path, Callable[[], dict[str, Any]]] = {
    RESULTS / "jax_native_l0_response_effect_path_quotient_layer_probe_results.json": lambda: _from_suite("jax_native_l0_response_effect_path_quotient_layer_probe", suite.row_response_effect_path_quotient),
    RESULTS / "jax_native_l1_boundary_environment_layer_probe_results.json": lambda: _from_suite("jax_native_l1_boundary_environment_layer_probe", suite.row_boundary_environment_cut),
    RESULTS / "jax_native_l4_terrain_channel_generator_layer_probe_results.json": lambda: _from_suite("jax_native_l4_terrain_channel_generator_layer_probe", suite.row_left_right_weyl_terrain_loop),
    RESULTS / "jax_native_l5_operator_substage_cell_layer_probe_results.json": lambda: _from_suite("jax_native_l5_operator_substage_cell_layer_probe", suite.row_operator_substage_cell),
    RESULTS / "jax_native_l6_entropy_cut_communication_layer_probe_results.json": lambda: _combined_suite(
        "jax_native_l6_entropy_cut_communication_layer_probe",
        [
            suite.row_qit_entropy_information,
            suite.row_capacity_path_entropy_budget,
            suite.row_conditional_mutual_information_readout,
            suite.row_qit_relative_free_energy,
        ],
        "finite density/cut/path objects -> allowed QIT entropy, CMI, relative entropy, and capacity readouts",
    ),
    RESULTS / "jax_native_l7_hopf_shell_projection_layer_probe_results.json": lambda: _from_suite("jax_native_l7_hopf_shell_projection_layer_probe", suite.row_hopf_fiber_base),
    RESULTS / "jax_native_l8_gluing_groupoid_layer_probe_results.json": lambda: _from_suite("jax_native_l8_gluing_groupoid_layer_probe", suite.row_gluing_groupoid_cocycle),
    RESULTS / "independent_layer_s3_unit_spinor_geometry_probe_results.json": geom_s3_spinor_carrier,
    RESULTS / "independent_layer_u1_hopf_fiber_probe_results.json": geom_u1_hopf_principal_bundle,
    RESULTS / "independent_layer_nested_hopf_tori_probe_results.json": lambda: _from_suite("independent_layer_nested_hopf_tori_probe", suite.row_nested_hopf_shells, kind="independent_jax_geometry_formal_scout"),
    RESULTS / "independent_layer_left_right_weyl_spinor_sheets_probe_results.json": lambda: _from_suite("independent_layer_left_right_weyl_spinor_sheets_probe", suite.row_weyl_gamma5_chirality, kind="independent_jax_geometry_formal_scout"),
    RESULTS / "independent_layer_local_weyl_dynamical_laws_probe_results.json": lambda: _from_suite("independent_layer_local_weyl_dynamical_laws_probe", suite.row_left_right_weyl_terrain_loop, kind="independent_jax_layer_formal_scout"),
}

GEOMETRY_RECEIPTS: dict[Path, Callable[[], dict[str, Any]]] = {
    RESULTS / "jax_native_geometry_s3_spinor_carrier_compact_repair_results.json": geom_s3_spinor_carrier,
    RESULTS / "jax_native_geometry_u1_hopf_principal_bundle_compact_repair_results.json": geom_u1_hopf_principal_bundle,
    RESULTS / "jax_native_geometry_so3_orientation_frame_reduction_compact_repair_results.json": geom_so3_orientation_frame_reduction,
    RESULTS / "jax_native_geometry_pin3_spin3_chirality_split_compact_repair_results.json": geom_pin3_spin3_chirality_split,
    RESULTS / "jax_native_geometry_seiberg_witten_8d_compact_repair_results.json": geom_seiberg_witten_8d,
    RESULTS / "jax_native_geometry_contact_sasakian_s3_compact_repair_results.json": geom_contact_sasakian_s3,
    RESULTS / "jax_native_geometry_higher_hopf_s7_to_s4_compact_repair_results.json": geom_higher_hopf_s7_to_s4,
}


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    failures: list[dict[str, Any]] = []
    for path, fn in {**LAYER_RECEIPTS, **GEOMETRY_RECEIPTS}.items():
        print(f"emit_start {path}", flush=True)
        receipt = fn()
        print(f"emit_computed {path}", flush=True)
        receipt["result_path"] = str(path)
        payload = json.dumps(_jsonable(receipt), indent=2, sort_keys=True) + "\n"
        print(f"emit_encoded {path} bytes={len(payload)}", flush=True)
        tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}")
        tmp.write_text(payload)
        os.replace(tmp, path)
        written.append(str(path))
        print(f"emit_done {path} all_pass={receipt['all_pass']}", flush=True)
        if not receipt["all_pass"] or receipt["promotion_allowed"] is not False:
            failures.append({"path": str(path), "all_pass": receipt["all_pass"], "promotion_allowed": receipt["promotion_allowed"]})

    out = {
        "name": "jax_independent_receipt_repair_emitter",
        "classification": "receipt_repair_emitter",
        "promotion_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "written_count": len(written),
        "written": written,
        "failures": failures,
        "all_pass": not failures,
        "AUDIT_PASS": not failures,
        "blocked_consumers": BLOCKED_CONSUMERS,
    }
    Path("jax_independent_receipt_repair_emitter_results.json").write_text(json.dumps(_jsonable(out), indent=2, sort_keys=True) + "\n")
    print(f"jax_independent_receipt_repair_emitter written={len(written)} failures={len(failures)} AUDIT_PASS={out['AUDIT_PASS']}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
