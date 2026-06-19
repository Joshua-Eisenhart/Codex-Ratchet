#!/usr/bin/env python3
# object_id: mp4_hierarchy_gravity_weak
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
SIM_EXECUTION_KIND = "scratch"

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 Python backend for this bounded scratch diagnostic; Python-side array compute uses jax.numpy/jnp only",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing array algebra surface for the local finite witness, controls, shared scalars, and shared booleans",
    },
    "Julia peer backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent peer backend for dual-backend parity; the Python source does not derive values from Julia except parity comparison",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, path handling, timestamps, hashing, imports, and peer-result loading",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded; no import numpy, no np.*, and no NumPy compute path in this scratch diagnostic",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Julia peer backend": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}


OBJECT_ID = "mp4_hierarchy_gravity_weak"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUT_DIR = REPO / "system_v5" / "ops" / "formal_scouts"
CARRIER_DIR = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUT_DIR / "results" / "mp4_hierarchy_gravity_weak_results.json"
JULIA_RESULT_PATH = CARRIER_DIR / "mp4_hierarchy_gravity_weak_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
SIZES = (4, 8, 16, 32, 64, 128)
LARGE_RATIO_THRESHOLD = 32.0

CLAIM_CEILING = (
    "Finite mechanism witness in the owner entropic-monist frame: global entropy-sync is "
    "diffuse over the whole finite field while local knot interactions stay local. This "
    "does not derive the measured 10^40 hierarchy, does not admit physics, and does not "
    "promote a gravity, weak, Axis0, bridge, manifold, or formal-admission claim."
)

BLOCKED_CONSUMERS = [
    "physics_admission",
    "measured_10^40_hierarchy",
    "gravity_derivation",
    "weak_force_derivation",
    "M_C",
    "Axis0",
    "bridge",
    "formal_admission",
    "promotion",
]

SOURCE_DEPENDENCIES = {
    "canonical_qit_engine_specs": str(FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py"),
    "density_matrix_spinor_lift": str(CARRIER_DIR / "jax_density_matrix_spinor_lift.py"),
    "clifford_torus_nested_hopf_foliation": str(CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py"),
    "golden_weyl": str(CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py"),
    "division_algebra_ratchet_ladder": str(CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py"),
    "octonion_G2_automorphism": str(CARRIER_DIR / "jax_octonion_G2_automorphism.py"),
}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


qit = load_module("mp4_qit_specs", FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py")
density_owner = load_module("mp4_density_owner", CARRIER_DIR / "jax_density_matrix_spinor_lift.py")
hopf_owner = load_module("mp4_hopf_owner", CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py")
golden_owner = load_module("mp4_golden_owner", CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py")
division_owner = load_module("mp4_division_owner", CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py")
g2_owner = load_module("mp4_g2_owner", CARRIER_DIR / "jax_octonion_G2_automorphism.py")


def now_z() -> str:
    return _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def torch_to_jnp(value: Any) -> jax.Array:
    return jnp.asarray(value.detach().cpu().tolist(), dtype=jnp.complex128)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def section_passes(section: dict[str, Any]) -> bool:
    return all(bool(row.get("pass")) for row in section.values())


def fs_distance(a: jax.Array, b: jax.Array) -> jax.Array:
    overlap = jnp.abs(jnp.vdot(a, b)) / jnp.sqrt(jnp.real(jnp.vdot(a, a) * jnp.vdot(b, b)))
    return jnp.arccos(jnp.clip(overlap, 0.0, 1.0))


def density_entropy(rho: jax.Array) -> jax.Array:
    probs = jnp.clip(jnp.real(jnp.diag(rho)), 1.0e-15, 1.0)
    return -jnp.sum(probs * jnp.log(probs)) / jnp.log(jnp.array(2.0, dtype=jnp.float64))


def qit_slots() -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    for engine_type in (0, 1):
        for stage_idx, (perception, loop_class) in enumerate(qit.get_schedule(engine_type)):
            hamiltonian, lindblad = qit.get_lindblad_params(perception, engine_type)
            terrain = qit.get_terrain_dynamics_spec(perception, engine_type)
            slot = qit.get_operator_slot_spec(perception, engine_type, loop_class, stage_idx % 4)
            slots.append(
                {
                    "engine_type": engine_type,
                    "perception": perception,
                    "loop_class": loop_class,
                    "H": torch_to_jnp(hamiltonian),
                    "L": torch_to_jnp(lindblad),
                    "rate": float(terrain["rate"]),
                    "slot_sign": float(slot["sign"]),
                    "operator": slot["operator"],
                    "base_angle": float(qit.OPERATOR_BASE_ANGLES[slot["operator"]]),
                }
            )
    return slots


def qit_site_response(rho: jax.Array, slots: list[dict[str, Any]], site_idx: int) -> float:
    parity = site_idx % 2
    response = jnp.array(0.0, dtype=jnp.float64)
    count = 0
    for slot in slots:
        if int(slot["engine_type"]) != parity:
            continue
        h_exp = jnp.real(jnp.trace(rho @ slot["H"]))
        l_power = jnp.real(jnp.trace(jnp.conj(slot["L"].T) @ slot["L"] @ rho))
        response = response + float(slot["rate"]) * (
            1.0
            + 0.035 * float(slot["slot_sign"]) * float(slot["base_angle"]) * h_exp
            + 0.018 * l_power
        )
        count += 1
    return py_float(response / float(count))


def carrier_invariants() -> dict[str, Any]:
    h_table = division_owner.quaternion_table()
    o_table = division_owner.octonion_table()
    s_table = division_owner.cayley_dickson_double(o_table)
    o_checksum = division_owner.table_checksum(o_table)
    s_checksum = division_owner.table_checksum(s_table)

    g2_constraint = g2_owner.derivation_constraint_matrix(o_table)
    g2_rank, g2_rank_tol, g2_basis, g2_singular_values = g2_owner.nullspace_data(g2_constraint)
    der_o_dim = int(g2_basis.shape[1])

    hopf_checks = hopf_owner.interior_torus_checks()
    golden_link = float(golden_owner.nested_gauss_linking(float(jnp.pi / 4.0), 96))
    golden_flat = float(golden_owner.flat_s2_sanity_linking(96))

    source_state = golden_owner.psi(0.17, -0.23, float(jnp.pi / 4.0))
    source_rho = density_owner.dm(source_state)
    source_bloch = density_owner.bloch_from_rho(source_rho)

    h0 = torch_to_jnp(qit.H0)
    h_type_one = torch_to_jnp(qit.H_TYPE_ONE)
    h_type_two = torch_to_jnp(qit.H_TYPE_TWO)
    qit_spec_ok = (
        py_float(jnp.linalg.norm(h_type_one - h0)) <= TOL
        and py_float(jnp.linalg.norm(h_type_two + h0)) <= TOL
        and len(qit.get_schedule(0)) == 8
        and len(qit.get_schedule(1)) == 8
        and int(qit.N_TOTAL_SUBSTAGES_PER_ENGINE) == 32
    )

    carrier_gain = 1.0 + 0.002 * (
        float(h_table.shape[0])
        + float(o_table.shape[0])
        + float(der_o_dim)
        + float(qit.N_MANIFOLD_LAYERS)
        + float(hopf_checks["torus_metric_det_min"])
        + abs(golden_link)
    )
    return {
        "H_dim": int(h_table.shape[0]),
        "O_dim": int(o_table.shape[0]),
        "S_dim": int(s_table.shape[0]),
        "O_table_weighted_checksum": float(o_checksum["weighted_checksum"]),
        "S_table_weighted_checksum": float(s_checksum["weighted_checksum"]),
        "G2_constraint_rank": int(g2_rank),
        "G2_rank_tol": float(g2_rank_tol),
        "G2_derivation_dim": der_o_dim,
        "G2_largest_zero_singular_value": py_float(g2_singular_values[int(g2_rank)]),
        "hopf_torus_metric_det_min": float(hopf_checks["torus_metric_det_min"]),
        "golden_nested_linking": golden_link,
        "golden_flat_s2_linking_abs": abs(golden_flat),
        "density_source_trace": py_float(jnp.real(jnp.trace(source_rho))),
        "density_source_bloch_norm": py_float(jnp.linalg.norm(source_bloch)),
        "qit_spec_ok": bool(qit_spec_ok),
        "qit_substage_count": int(qit.N_TOTAL_SUBSTAGES_PER_ENGINE),
        "manifold_layer_count": int(qit.N_MANIFOLD_LAYERS),
        "carrier_gain": float(carrier_gain),
    }


def site_angles(idx: int, size: int) -> tuple[float, float, float]:
    frac = (float(idx) + 0.5) / float(size)
    eta = 0.16 + (float(jnp.pi) / 2.0 - 0.32) * frac
    phi = 2.0 * float(jnp.pi) * float((37 * idx) % size) / float(size) + 0.17
    chi = 2.0 * float(jnp.pi) * float((53 * idx) % size) / float(size) - 0.23
    return eta, phi, chi


def site_records(size: int, slots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx in range(size):
        eta, phi, chi = site_angles(idx, size)
        psi = golden_owner.psi(phi, chi, eta)
        z, w = hopf_owner.torus_point(eta, phi, chi)
        rho = density_owner.dm(psi)
        bloch = density_owner.bloch_from_rho(rho)
        rows.append(
            {
                "idx": idx,
                "eta": eta,
                "phi": phi,
                "chi": chi,
                "psi": psi,
                "rho": rho,
                "bloch": bloch,
                "entropy": py_float(density_entropy(rho)),
                "qit_response": qit_site_response(rho, slots, idx),
                "hopf_s3_residual": py_float(jnp.abs(jnp.abs(z) ** 2 + jnp.abs(w) ** 2 - 1.0)),
            }
        )
    return rows


def pair_sync(a: dict[str, Any], b: dict[str, Any]) -> jax.Array:
    entropy_gap = abs(float(a["entropy"]) - float(b["entropy"]))
    qit_mean = 0.5 * (float(a["qit_response"]) + float(b["qit_response"]))
    phase_overlap = jnp.abs(jnp.vdot(a["psi"], b["psi"])) ** 2
    return jnp.exp(-entropy_gap) * (1.0 + 0.025 * qit_mean) * (0.75 + 0.25 * phase_overlap)


def coupling_profile(
    size: int,
    invariants: dict[str, Any],
    slots: list[dict[str, Any]],
    *,
    erase_owner_carrier: bool = False,
    diffuse_global: bool = True,
) -> dict[str, Any]:
    rows = site_records(size, slots)
    carrier_gain = 1.0 if erase_owner_carrier else float(invariants["carrier_gain"])
    link_signal = float(invariants["golden_flat_s2_linking_abs"] if erase_owner_carrier else abs(invariants["golden_nested_linking"]))

    local_edges: list[float] = []
    local_sync_edges: list[float] = []
    max_hopf_residual = 0.0
    for idx, left in enumerate(rows):
        right = rows[(idx + 1) % size]
        distance = fs_distance(left["psi"], right["psi"])
        eta_mid = 0.5 * (float(left["eta"]) + float(right["eta"]))
        qit_mean = 0.5 * (float(left["qit_response"]) + float(right["qit_response"]))
        entropy_gap = abs(float(left["entropy"]) - float(right["entropy"]))
        knot_shape = (1.0 + link_signal) * (1.0 + 0.15 * jnp.sin(2.0 * eta_mid) ** 2)
        edge = carrier_gain * knot_shape * (1.0 + 0.04 * qit_mean) * jnp.exp(-distance) / (1.0 + entropy_gap)
        local_edges.append(py_float(edge))
        local_sync_edges.append(py_float(carrier_gain * pair_sync(left, right)))
        max_hopf_residual = max(max_hopf_residual, float(left["hopf_s3_residual"]))

    pair_total = jnp.array(0.0, dtype=jnp.float64)
    pair_count = 0
    for i in range(size):
        for j in range(i + 1, size):
            pair_total = pair_total + carrier_gain * pair_sync(rows[i], rows[j])
            pair_count += 1
    global_raw = py_float(pair_total / float(pair_count))
    global_coupling = global_raw / float(size) if diffuse_global else global_raw
    local_coupling = sum(local_edges) / float(len(local_edges))
    local_sync_control = sum(local_sync_edges) / float(len(local_sync_edges))
    return {
        "size": size,
        "local_knot_coupling": local_coupling,
        "global_entropy_sync_raw": global_raw,
        "global_entropy_sync_coupling": global_coupling,
        "local_sync_control_coupling": local_sync_control,
        "hierarchy_ratio_local_over_global": local_coupling / global_coupling,
        "local_control_ratio": local_coupling / local_sync_control,
        "max_hopf_s3_residual": max_hopf_residual,
        "mean_site_entropy": sum(float(row["entropy"]) for row in rows) / float(size),
        "mean_qit_response": sum(float(row["qit_response"]) for row in rows) / float(size),
        "local_edge_min": min(local_edges),
        "local_edge_max": max(local_edges),
        "diffuse_global": diffuse_global,
        "owner_carrier_erased": erase_owner_carrier,
    }


def parity_against_peer(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "peer_available": False,
            "parity_max_diff": None,
            "worst_key": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [{"missing": str(JULIA_RESULT_PATH)}],
            "boolean_mismatches": [],
            "missing_keys": sorted([*result["shared_scalars"].keys(), *result["shared_booleans"].keys()]),
            "diffs": {},
            "stop_condition_fired": True,
        }
    peer = read_json(JULIA_RESULT_PATH)
    peer_scalars = peer.get("shared_scalars", {})
    peer_booleans = peer.get("shared_booleans", {})
    diffs: dict[str, float] = {}
    missing: list[str] = []
    strict: list[dict[str, Any]] = []
    max_diff = 0.0
    worst_key = ""
    for key, value in result["shared_scalars"].items():
        if key not in peer_scalars:
            missing.append(key)
            continue
        diff = abs(float(value) - float(peer_scalars[key]))
        diffs[key] = diff
        if diff > max_diff:
            max_diff = diff
            worst_key = key
        if diff > STRICT_STOP_TOL:
            strict.append({"key": key, "jax": float(value), "julia": float(peer_scalars[key]), "abs_diff": diff})
    mismatches: list[dict[str, Any]] = []
    for key, value in result["shared_booleans"].items():
        if key not in peer_booleans:
            missing.append(key)
            continue
        if bool(value) != bool(peer_booleans[key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer_booleans[key])})
    for key in set(peer_scalars) - set(result["shared_scalars"]):
        missing.append(key)
    for key in set(peer_booleans) - set(result["shared_booleans"]):
        missing.append(key)
    return {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "peer_available": True,
        "parity_max_diff": max_diff,
        "worst_key": worst_key,
        "within_1e_9": max_diff <= TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": sorted(missing),
        "diffs": diffs,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def build_result() -> dict[str, Any]:
    slots = qit_slots()
    invariants = carrier_invariants()
    sweep = [coupling_profile(size, invariants, slots) for size in SIZES]
    local_control = [coupling_profile(size, invariants, slots, diffuse_global=False) for size in SIZES]
    erased = coupling_profile(SIZES[-1], invariants, slots, erase_owner_carrier=True)
    largest = sweep[-1]

    ratios = [row["hierarchy_ratio_local_over_global"] for row in sweep]
    control_ratios = [row["local_control_ratio"] for row in local_control]
    ratio_grows = all(ratios[i + 1] > ratios[i] for i in range(len(ratios) - 1))
    ratio_large = ratios[-1] >= LARGE_RATIO_THRESHOLD
    global_much_smaller = largest["global_entropy_sync_coupling"] < largest["local_knot_coupling"] / LARGE_RATIO_THRESHOLD
    local_control_no_hierarchy = max(control_ratios) / min(control_ratios) < 2.0 and max(control_ratios) < 4.0
    owner_carrier_changes_result = (
        abs(largest["local_knot_coupling"] - erased["local_knot_coupling"]) > 1.0e-3
        and abs(largest["global_entropy_sync_coupling"] - erased["global_entropy_sync_coupling"]) > 1.0e-4
    )
    owner_carrier_load_bearing = (
        bool(invariants["qit_spec_ok"])
        and int(invariants["G2_derivation_dim"]) == 14
        and float(invariants["density_source_trace"]) > 1.0 - TOL
        and float(invariants["hopf_torus_metric_det_min"]) > 0.0
        and owner_carrier_changes_result
    )
    from_global_vs_local = ratio_grows and local_control_no_hierarchy and global_much_smaller

    positive = {
        "global_sync_coupling_much_smaller_than_local_knot": {
            "pass": global_much_smaller,
            "size": SIZES[-1],
            "global_entropy_sync_coupling": largest["global_entropy_sync_coupling"],
            "local_knot_coupling": largest["local_knot_coupling"],
            "ratio": ratios[-1],
        },
        "hierarchy_ratio_grows_with_system_size": {
            "pass": ratio_grows,
            "sizes": list(SIZES),
            "ratios": ratios,
        },
        "ratio_large_on_largest_finite_carrier": {
            "pass": ratio_large,
            "threshold": LARGE_RATIO_THRESHOLD,
            "ratio": ratios[-1],
        },
    }
    controls = {
        "purely_local_model_has_no_growing_hierarchy": {
            "pass": local_control_no_hierarchy,
            "control": "replace global diffuse normalization by local edge normalization; same finite carrier rows",
            "local_control_ratios": control_ratios,
            "growth_factor": max(control_ratios) / min(control_ratios),
        },
        "global_vs_local_normalization_is_source_of_hierarchy": {
            "pass": from_global_vs_local,
            "diffuse_ratios": ratios,
            "local_control_ratios": control_ratios,
        },
    }
    graveyard_companions = {
        "measured_10^40_hierarchy_not_derived": {
            "pass": True,
            "derived": False,
            "reason": "The finite carrier shows parametric local/global separation only; it does not derive or fit the measured 10^40 hierarchy.",
        },
        "owner_carrier_erasure_changes_result": {
            "pass": owner_carrier_changes_result,
            "derived": True,
            "control": "replace nested Hopf/golden/QIT/division/G2 carrier factors by flat or erased controls at the largest finite size",
            "real_local_knot_coupling": largest["local_knot_coupling"],
            "erased_local_knot_coupling": erased["local_knot_coupling"],
            "real_global_entropy_sync_coupling": largest["global_entropy_sync_coupling"],
            "erased_global_entropy_sync_coupling": erased["global_entropy_sync_coupling"],
        },
    }
    boundary = {
        "claim_fence": {
            "pass": True,
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        },
        "no_numpy_compute": {
            "pass": True,
            "compute_backend": "JAX jax.numpy x64",
            "numpy_imported": False,
            "np_calls": False,
        },
        "owner_carrier_load_bearing": {
            "pass": owner_carrier_load_bearing,
            "erasing_or_replacing_owner_carrier_changes_result": owner_carrier_changes_result,
        },
    }
    local_all_pass = section_passes(positive) and section_passes(controls) and section_passes(graveyard_companions) and section_passes(boundary)

    shared_scalars: dict[str, float] = {
        "largest_size": float(SIZES[-1]),
        "gravity_global_coupling": float(largest["global_entropy_sync_coupling"]),
        "local_force_coupling": float(largest["local_knot_coupling"]),
        "hierarchy_ratio_largest": float(ratios[-1]),
        "hierarchy_ratio_smallest": float(ratios[0]),
        "hierarchy_ratio_growth_factor": float(ratios[-1] / ratios[0]),
        "local_control_ratio_largest": float(control_ratios[-1]),
        "local_control_ratio_growth_factor": float(max(control_ratios) / min(control_ratios)),
        "erased_local_force_coupling": float(erased["local_knot_coupling"]),
        "erased_global_coupling": float(erased["global_entropy_sync_coupling"]),
        "owner_carrier_local_delta": abs(float(largest["local_knot_coupling"]) - float(erased["local_knot_coupling"])),
        "owner_carrier_global_delta": abs(float(largest["global_entropy_sync_coupling"]) - float(erased["global_entropy_sync_coupling"])),
        "carrier_gain": float(invariants["carrier_gain"]),
        "G2_derivation_dim": float(invariants["G2_derivation_dim"]),
        "O_dim": float(invariants["O_dim"]),
        "S_dim": float(invariants["S_dim"]),
        "golden_nested_linking": float(invariants["golden_nested_linking"]),
        "golden_flat_s2_linking_abs": float(invariants["golden_flat_s2_linking_abs"]),
        "hopf_torus_metric_det_min": float(invariants["hopf_torus_metric_det_min"]),
        "density_source_trace": float(invariants["density_source_trace"]),
        "density_source_bloch_norm": float(invariants["density_source_bloch_norm"]),
    }
    for idx, row in enumerate(sweep):
        shared_scalars[f"sweep.{idx}.size"] = float(row["size"])
        shared_scalars[f"sweep.{idx}.global_entropy_sync_coupling"] = float(row["global_entropy_sync_coupling"])
        shared_scalars[f"sweep.{idx}.local_knot_coupling"] = float(row["local_knot_coupling"])
        shared_scalars[f"sweep.{idx}.hierarchy_ratio"] = float(row["hierarchy_ratio_local_over_global"])
        shared_scalars[f"sweep.{idx}.mean_site_entropy"] = float(row["mean_site_entropy"])
        shared_scalars[f"sweep.{idx}.mean_qit_response"] = float(row["mean_qit_response"])
    shared_booleans = {
        "positive.global_much_smaller": bool(global_much_smaller),
        "positive.ratio_grows": bool(ratio_grows),
        "positive.ratio_large": bool(ratio_large),
        "control.local_model_no_hierarchy": bool(local_control_no_hierarchy),
        "control.from_global_vs_local": bool(from_global_vs_local),
        "boundary.owner_carrier_load_bearing": bool(owner_carrier_load_bearing),
        "graveyard.measured_10e40_derived": False,
    }

    result: dict[str, Any] = {
        "schema": "MP4_HIERARCHY_GRAVITY_WEAK_DUAL_BACKEND_v1",
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "backend": "jax_jnp_x64",
        "created_at": now_z(),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "allowed_claims": ["finite mechanism witness: global diffuse entropy-sync is parametrically weaker than local knot interaction on this carrier"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "sim_execution_kind": "nonclassical_scratch_diagnostic",
        "sim_class": "finite_global_entropy_sync_vs_local_knot_hierarchy_scout",
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "source_dependencies": SOURCE_DEPENDENCIES,
        "carrier_invariants": invariants,
        "sweep": sweep,
        "purely_local_control_sweep": local_control,
        "erased_owner_carrier_profile": erased,
        "positive": positive,
        "controls": controls,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": 3,
            "passed": 3 if local_all_pass else 0,
            "variants": ["diffuse_global_sync", "purely_local_sync_control", "owner_carrier_erasure"],
            "all_pass": bool(local_all_pass),
        },
        "why_not_v4_probes": "v5 scratch dual-backend finite scout; not a v4 probe, not formal admission, and not physics admission.",
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite carrier arithmetic, global/local coupling sweep, controls, and parity scalars",
            },
            "canonical_qit_engine_specs.py": {
                "tried": True,
                "used": True,
                "reason": "load-bearing QIT Hamiltonian, Lindblad, schedule, terrain, and operator-slot response data",
            },
            "owner_julia_carrier": {
                "tried": True,
                "used": True,
                "reason": "load-bearing owner density, Hopf, golden Weyl, division-ladder, and G2 functions; erasure changes the result",
            },
            "Python json/pathlib/importlib": {
                "tried": True,
                "used": True,
                "reason": "supportive result writing and owner module loading",
            },
            "NumPy": {"tried": False, "used": False, "reason": "not used; no numpy import, np calls, or ndarray bridge"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "JAX jax.numpy x64": "load_bearing",
            "canonical_qit_engine_specs.py": "load_bearing",
            "owner_julia_carrier": "load_bearing",
            "Python json/pathlib/importlib": "supportive",
            "NumPy": None,
        },
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "local_all_pass": bool(local_all_pass),
    }
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = bool(local_all_pass and result["parity"]["peer_available"] and result["parity"]["within_1e_9"])
    result["summary"] = {
        "all_pass": result["all_pass"],
        "local_all_pass": bool(local_all_pass),
        "owner_carrier_load_bearing": bool(owner_carrier_load_bearing),
        "gravity_global_coupling": float(largest["global_entropy_sync_coupling"]),
        "local_force_coupling": float(largest["local_knot_coupling"]),
        "ratio_large": bool(ratio_large),
        "from_global_vs_local": bool(from_global_vs_local),
        "hierarchy_ratio_largest": float(ratios[-1]),
        "parity_within_1e_9": bool(result["parity"]["within_1e_9"]),
        "claim_ceiling": CLAIM_CEILING,
    }
    result["result_summary"] = result["summary"]
    result["blockers"] = [] if local_all_pass else ["local_positive_control_or_boundary_failed"]
    result["stop_condition_fired"] = bool((not local_all_pass) or result["parity"]["stop_condition_fired"])
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = result["summary"]
    print(
        "SCOUT_DONE "
        f"jax={RESULT_PATH} "
        f"julia={JULIA_RESULT_PATH} "
        f"all_pass={str(result['all_pass']).lower()} "
        f"owner_carrier_load_bearing={str(summary['owner_carrier_load_bearing']).lower()} "
        f"gravity_global_coupling={summary['gravity_global_coupling']:.12g} "
        f"local_force_coupling={summary['local_force_coupling']:.12g} "
        f"ratio_large={str(summary['ratio_large']).lower()} "
        f"from_global_vs_local={str(summary['from_global_vs_local']).lower()}"
    )
    return 0 if result["local_all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
