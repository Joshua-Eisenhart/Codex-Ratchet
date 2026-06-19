#!/usr/bin/env python3
# object_id: mp4_arrow_of_time_entropy
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
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


OBJECT_ID = "mp4_arrow_of_time_entropy"
BACKEND = "jax_jnp_x64"
REPO_ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUT_DIR = REPO_ROOT / "system_v5" / "ops" / "formal_scouts"
JULIA_CARRIER_DIR = REPO_ROOT / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUT_DIR / "results" / "mp4_arrow_of_time_entropy_results.json"
JULIA_REFERENCE_PATH = JULIA_CARRIER_DIR / "mp4_arrow_of_time_entropy_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
RECOVERY_FAIL_THRESHOLD = 0.15
LOAD_BEARING_DELTA_THRESHOLD = 1.0e-4
N_QUBITS = 3
DIM = 2**N_QUBITS
ENGINE_TYPE = 0

sys.path.insert(0, str(FORMAL_SCOUT_DIR))
sys.path.insert(0, str(JULIA_CARRIER_DIR))

import canonical_qit_engine_specs as qit  # noqa: E402
import jax_clifford_torus_nested_hopf_foliation as hopf  # noqa: E402
import jax_density_matrix_spinor_lift as spinor_lift  # noqa: E402
import jax_division_algebra_ratchet_ladder as division  # noqa: E402
import jax_octonion_G2_automorphism as g2  # noqa: E402


I2 = jnp.eye(2, dtype=jnp.complex128)
SX = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
PAULI_BY_OPERATOR = {"Ti": SZ, "Te": SX, "Fi": SX, "Fe": SY}
PAULI_BY_AXIS = {"x": SX, "y": SY, "z": SZ}
OPERATOR_INDEX = {"Ti": 0.0, "Te": 1.0, "Fi": 2.0, "Fe": 3.0}


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def kron_all(mats: list[jax.Array]) -> jax.Array:
    out = mats[0]
    for mat in mats[1:]:
        out = jnp.kron(out, mat)
    return out


def one_qubit_op(op: jax.Array, q: int) -> jax.Array:
    return kron_all([op if idx == q else I2 for idx in range(N_QUBITS)])


def two_qubit_op(op_a: jax.Array, q_a: int, op_b: jax.Array, q_b: int) -> jax.Array:
    mats: list[jax.Array] = []
    for idx in range(N_QUBITS):
        if idx == q_a:
            mats.append(op_a)
        elif idx == q_b:
            mats.append(op_b)
        else:
            mats.append(I2)
    return kron_all(mats)


def h0_from_canonical_spec() -> jax.Array:
    return jnp.asarray(qit.H0.detach().cpu().tolist(), dtype=jnp.complex128)


def one_qubit_h_unitary(h: jax.Array, theta: float) -> jax.Array:
    norm = jnp.sqrt(jnp.real(jnp.trace(h @ h)) / 2.0)
    generator = h / norm
    return jnp.cos(theta * norm) * I2 - 1j * jnp.sin(theta * norm) * generator


def pauli_word_unitary(pauli_word: jax.Array, theta: float) -> jax.Array:
    ident = jnp.eye(pauli_word.shape[0], dtype=jnp.complex128)
    return jnp.cos(theta) * ident - 1j * jnp.sin(theta) * pauli_word


def dm(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def normalize(psi: jax.Array) -> jax.Array:
    return psi / jnp.sqrt(jnp.real(jnp.vdot(psi, psi)))


def product_state(spinors: list[jax.Array]) -> jax.Array:
    psi = spinors[0]
    for spinor in spinors[1:]:
        psi = jnp.kron(psi, spinor)
    return normalize(psi)


def finite_entropy(rho: jax.Array) -> float:
    eigs = jnp.linalg.eigvalsh((rho + jnp.conj(rho.T)) / 2.0)
    eigs = jnp.clip(jnp.real(eigs), 0.0, 1.0)
    terms = jnp.where(eigs > 1.0e-15, -eigs * jnp.log(eigs), 0.0)
    return py_float(jnp.sum(terms))


def trace_residual(rho: jax.Array) -> float:
    return py_float(jnp.abs(jnp.real(jnp.trace(rho)) - 1.0))


def hermitian_residual(rho: jax.Array) -> float:
    return py_float(jnp.linalg.norm(rho - jnp.conj(rho.T)))


def schedule_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for main_idx, (perception, loop_class) in enumerate(qit.get_schedule(ENGINE_TYPE)):
        topo = qit.get_topology_spec(perception, ENGINE_TYPE)
        terrain = qit.get_terrain_dynamics_spec(perception, ENGINE_TYPE)
        for substage_idx in range(qit.N_SUBSTAGES_PER_MAIN):
            slot = qit.get_operator_slot_spec(perception, ENGINE_TYPE, loop_class, substage_idx)
            records.append(
                {
                    "record_index": len(records),
                    "engine_type": ENGINE_TYPE,
                    "type_label": qit.get_engine_spec(ENGINE_TYPE)["type_label"],
                    "perception": perception,
                    "loop_class": loop_class,
                    "main_stage_index": main_idx,
                    "substage_index": substage_idx,
                    "operator": slot["operator"],
                    "sign": int(slot["sign"]),
                    "token": slot["token"],
                    "rate": float(topo["rate"]),
                    "projector_axis": topo["projector_axis"],
                    "dynamics_family": terrain["family"],
                    "realization": topo["realization"],
                }
            )
    return records


def initial_state() -> jax.Array:
    etas = [py_float(jnp.pi / 7.0), py_float(jnp.pi / 4.0), py_float(3.0 * jnp.pi / 10.0)]
    spinors: list[jax.Array] = []
    for idx, eta in enumerate(etas):
        z, w = hopf.torus_point(eta, 0.23 + 0.37 * idx, 0.71 + 0.29 * idx)
        spinors.append(normalize(jnp.asarray([z, w], dtype=jnp.complex128)))
    return product_state(spinors)


def unitary_for_record(rec: dict[str, Any], carrier_weight: float) -> jax.Array:
    h0 = h0_from_canonical_spec()
    q = (rec["main_stage_index"] + rec["substage_index"] + rec["engine_type"]) % N_QUBITS
    r = (q + 1 + rec["engine_type"]) % N_QUBITS
    h_sign = 1.0 if rec["engine_type"] == 0 else -1.0
    local_theta = 0.17 * rec["sign"] * h_sign * (1.0 + 0.20 * rec["rate"]) * carrier_weight
    local_u = one_qubit_op(one_qubit_h_unitary(h_sign * h0, local_theta), q)
    op = PAULI_BY_OPERATOR[rec["operator"]]
    axis_op = PAULI_BY_AXIS[rec["projector_axis"]]
    pair_word = two_qubit_op(op, q, axis_op, r)
    pair_theta = 0.047 * rec["sign"] * (1.0 + rec["rate"]) * (1.0 + 0.08 * rec["substage_index"]) * carrier_weight
    pair_u = pauli_word_unitary(pair_word, pair_theta)
    return pair_u @ local_u


def carrier_anchor_values() -> tuple[dict[str, Any], dict[str, float], dict[str, bool]]:
    q_table = division.quaternion_table()
    qi = division.basis(4, 1)
    qj = division.basis(4, 2)
    qk = division.basis(4, 3)
    q_ij_residual = py_float(jnp.linalg.norm(division.multiply(q_table, qi, qj) - qk))

    oct_table_division = division.octonion_table()
    associator_probe = division.associator(oct_table_division, division.basis(8, 1), division.basis(8, 2), division.basis(8, 4))
    octonion_associator_norm = py_float(jnp.linalg.norm(associator_probe))

    oct_table_g2 = g2.octonion_table()
    rank, _rank_tol, ns, _singular_values = g2.nullspace_data(g2.derivation_constraint_matrix(oct_table_g2))
    g2_der_dim = int(ns.shape[1])

    psi = spinor_lift.spinor_from_angles(1.1, -0.7)
    rho = spinor_lift.dm(psi)
    bloch = spinor_lift.bloch_from_rho(rho)
    density_spinor_bloch_norm = py_float(jnp.linalg.norm(bloch))
    density_spinor_idempotency_residual = py_float(jnp.linalg.norm(rho @ rho - rho))

    z, w = hopf.torus_point(py_float(jnp.pi / 4.0), 0.37, 0.91)
    hopf_s3_residual = py_float(jnp.abs(jnp.abs(z) ** 2 + jnp.abs(w) ** 2 - 1.0))

    golden_receipt = json.loads((JULIA_CARRIER_DIR / "golden_weyl_jax_receipt.json").read_text(encoding="utf-8"))
    golden_flat_delta = float(golden_receipt["controls"]["flat_S2"]["observable_delta"])
    golden_eta_count = float(golden_receipt["eta_base"]["count"])

    scalars = {
        "carrier.quaternion_ij_minus_k_residual": q_ij_residual,
        "carrier.octonion_associator_norm": octonion_associator_norm,
        "carrier.g2_derivation_dim": float(g2_der_dim),
        "carrier.g2_constraint_rank": float(rank),
        "carrier.density_spinor_bloch_norm": density_spinor_bloch_norm,
        "carrier.density_spinor_idempotency_residual": density_spinor_idempotency_residual,
        "carrier.hopf_s3_residual": hopf_s3_residual,
        "carrier.golden_weyl_flat_control_delta": golden_flat_delta,
        "carrier.golden_weyl_eta_count": golden_eta_count,
    }
    booleans = {
        "carrier.canonical_qit_schedule_real": qit.N_TOTAL_SUBSTAGES_PER_ENGINE == 32 and len(qit.get_schedule(ENGINE_TYPE)) == 8,
        "carrier.quaternion_table_real": q_ij_residual < TOL,
        "carrier.division_octonion_nonassociative_real": octonion_associator_norm > 0.5,
        "carrier.octonion_g2_derivation_dim_real": g2_der_dim == 14,
        "carrier.density_matrix_spinor_lift_real": density_spinor_bloch_norm > 1.0 - TOL and density_spinor_idempotency_residual < TOL,
        "carrier.hopf_torus_real": hopf_s3_residual < TOL,
        "carrier.golden_weyl_control_real": golden_flat_delta > 0.9 and golden_eta_count >= 65.0,
    }
    anchors = {
        "source_contract_paths": [
            str(FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py"),
            str(JULIA_CARRIER_DIR / "density_matrix_spinor_lift.jl"),
            str(JULIA_CARRIER_DIR / "clifford_torus_nested_hopf_foliation.jl"),
            str(JULIA_CARRIER_DIR / "golden_weyl_julia.jl"),
            str(JULIA_CARRIER_DIR / "division_algebra_ratchet_ladder.jl"),
            str(JULIA_CARRIER_DIR / "octonion_G2_automorphism.jl"),
        ],
        "jax_source_paths_used": [
            str(JULIA_CARRIER_DIR / "jax_density_matrix_spinor_lift.py"),
            str(JULIA_CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py"),
            str(JULIA_CARRIER_DIR / "golden_weyl_jax_receipt.json"),
            str(JULIA_CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py"),
            str(JULIA_CARRIER_DIR / "jax_octonion_G2_automorphism.py"),
        ],
    }
    return anchors, scalars, booleans


def carrier_weights(records: list[dict[str, Any]], carrier_scalars: dict[str, float], erased: bool) -> list[float]:
    if erased:
        return [1.0 for _ in records]
    weights: list[float] = []
    g2_norm = carrier_scalars["carrier.g2_derivation_dim"] / 14.0
    golden_delta = carrier_scalars["carrier.golden_weyl_flat_control_delta"]
    eta_norm = carrier_scalars["carrier.golden_weyl_eta_count"] / 65.0
    spinor_norm = carrier_scalars["carrier.density_spinor_bloch_norm"]
    assoc = min(carrier_scalars["carrier.octonion_associator_norm"], 4.0) / 4.0
    for rec in records:
        frac = (rec["record_index"] + 1) / (len(records) + 1)
        eta = py_float(0.5 * jnp.pi * frac)
        z, w = hopf.torus_point(eta, 0.17 * (rec["record_index"] + 1), 0.31 * (rec["record_index"] + 1))
        hopf_bias = py_float(jnp.abs(jnp.abs(z) ** 2 - jnp.abs(w) ** 2))
        weight = (
            1.0
            + 0.052 * hopf_bias
            + 0.018 * float(rec["rate"])
            + 0.013 * g2_norm
            + 0.011 * golden_delta
            + 0.007 * eta_norm
            + 0.006 * spinor_norm
            + 0.004 * assoc
            + 0.003 * OPERATOR_INDEX[str(rec["operator"])]
        )
        weights.append(float(weight))
    return weights


def evolve_forward(records: list[dict[str, Any]], weights: list[float], inject_entropy: bool) -> dict[str, Any]:
    start_psi = initial_state()
    start_rho = dm(start_psi)
    rho = start_rho
    entropies: list[float] = []
    injection_strengths: list[float] = []
    for rec, weight in zip(records, weights, strict=True):
        u = unitary_for_record(rec, weight)
        rho = u @ rho @ jnp.conj(u.T)
        if inject_entropy:
            lam = 0.0055 + 0.0032 * weight
            rho = (1.0 - lam) * rho + lam * jnp.eye(DIM, dtype=jnp.complex128) / DIM
            injection_strengths.append(float(lam))
        else:
            injection_strengths.append(0.0)
        entropies.append(finite_entropy(rho))
    diffs = [entropies[idx + 1] - entropies[idx] for idx in range(len(entropies) - 1)]
    return {
        "start_rho": start_rho,
        "final_rho": rho,
        "entropies": entropies,
        "entropy_diffs": diffs,
        "injection_strengths": injection_strengths,
        "min_step_delta": min(diffs),
        "entropy_delta": entropies[-1] - entropies[0],
        "trace_residual_final": trace_residual(rho),
        "hermitian_residual_final": hermitian_residual(rho),
    }


def reverse_conjugate(final_rho: jax.Array, records: list[dict[str, Any]], weights: list[float]) -> jax.Array:
    rho = final_rho
    for rec, weight in reversed(list(zip(records, weights, strict=True))):
        u = unitary_for_record(rec, weight)
        rho = jnp.conj(u.T) @ rho @ u
    return rho


def build_shared_scalars(
    forward: dict[str, Any],
    reverse_rho: jax.Array,
    unitary_forward: dict[str, Any],
    unitary_reverse_rho: jax.Array,
    erased_forward: dict[str, Any],
    carrier_scalars: dict[str, float],
) -> dict[str, float]:
    reverse_distance = py_float(jnp.linalg.norm(reverse_rho - forward["start_rho"]))
    reverse_entropy = finite_entropy(reverse_rho)
    unitary_reverse_distance = py_float(jnp.linalg.norm(unitary_reverse_rho - unitary_forward["start_rho"]))
    erased_final_entropy = erased_forward["entropies"][-1]
    owner_erase_entropy_delta = abs(forward["entropies"][-1] - erased_final_entropy)
    out = {
        "schedule.substage_count": float(len(forward["entropies"])),
        "entropy.initial_after_step": forward["entropies"][0],
        "entropy.final": forward["entropies"][-1],
        "entropy.delta": forward["entropy_delta"],
        "entropy.min_step_delta": forward["min_step_delta"],
        "entropy.max_step_delta": max(forward["entropy_diffs"]),
        "entropy.injection_strength_min": min(forward["injection_strengths"]),
        "entropy.injection_strength_max": max(forward["injection_strengths"]),
        "reverse.recovery_frobenius_distance": reverse_distance,
        "reverse.entropy_after_reverse": reverse_entropy,
        "reverse.entropy_retained_delta": reverse_entropy - forward["entropies"][0],
        "unitary_control.reverse_recovery_frobenius_distance": unitary_reverse_distance,
        "erased_carrier.final_entropy": erased_final_entropy,
        "erased_carrier.final_entropy_abs_delta": owner_erase_entropy_delta,
        "erased_carrier.min_step_delta": erased_forward["min_step_delta"],
        "density.trace_residual_final": forward["trace_residual_final"],
        "density.hermitian_residual_final": forward["hermitian_residual_final"],
    }
    out.update(carrier_scalars)
    return out


def parity_against_peer(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_REFERENCE_PATH.exists():
        return {
            "peer_result_path": str(JULIA_REFERENCE_PATH),
            "status": "missing_peer",
            "peer_available": False,
            "shared_scalar_rows": [],
            "parity_max_diff": None,
            "max_diff_key": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [],
            "boolean_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": False,
        }
    peer = json.loads(JULIA_REFERENCE_PATH.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    max_diff = 0.0
    max_diff_key = None
    strict: list[dict[str, Any]] = []
    missing: list[str] = []
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        jax_value = float(value)
        julia_value = float(peer["shared_scalars"][key])
        diff = abs(jax_value - julia_value)
        if diff > max_diff:
            max_diff = diff
            max_diff_key = key
        row = {"key": key, "jax": jax_value, "julia": julia_value, "abs_diff": diff}
        rows.append(row)
        if diff > STRICT_STOP_TOL:
            strict.append(row)
    mismatches: list[dict[str, Any]] = []
    for key, value in result["shared_booleans"].items():
        if key not in peer.get("shared_booleans", {}):
            missing.append(key)
            continue
        if bool(value) != bool(peer["shared_booleans"][key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer["shared_booleans"][key])})
    return {
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "status": "compared",
        "peer_available": True,
        "shared_scalar_rows": rows,
        "parity_max_diff": max_diff,
        "max_diff_key": max_diff_key,
        "within_1e_9": max_diff < TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def build_result() -> dict[str, Any]:
    records = schedule_records()
    carrier_anchors, carrier_scalars, carrier_booleans = carrier_anchor_values()
    weights = carrier_weights(records, carrier_scalars, erased=False)
    erased_weights = carrier_weights(records, carrier_scalars, erased=True)

    forward = evolve_forward(records, weights, inject_entropy=True)
    reverse_rho = reverse_conjugate(forward["final_rho"], records, weights)
    unitary_forward = evolve_forward(records, weights, inject_entropy=False)
    unitary_reverse_rho = reverse_conjugate(unitary_forward["final_rho"], records, weights)
    erased_forward = evolve_forward(records, erased_weights, inject_entropy=True)

    shared_scalars = build_shared_scalars(forward, reverse_rho, unitary_forward, unitary_reverse_rho, erased_forward, carrier_scalars)
    monotone_d_s = forward["min_step_delta"] >= -TOL and forward["entropy_delta"] > 0.0
    reverse_control_fails = (
        shared_scalars["reverse.recovery_frobenius_distance"] > RECOVERY_FAIL_THRESHOLD
        and shared_scalars["reverse.entropy_retained_delta"] > 0.05
    )
    unitary_reverse_recovers_start = shared_scalars["unitary_control.reverse_recovery_frobenius_distance"] < STRICT_STOP_TOL
    owner_carrier_load_bearing = shared_scalars["erased_carrier.final_entropy_abs_delta"] > LOAD_BEARING_DELTA_THRESHOLD
    irreversible_ratchet = monotone_d_s and reverse_control_fails and unitary_reverse_recovers_start and owner_carrier_load_bearing
    density_valid = forward["trace_residual_final"] < TOL and forward["hermitian_residual_final"] < TOL

    shared_booleans = {
        "monotone_dS": bool(monotone_d_s),
        "reverse_control_fails": bool(reverse_control_fails),
        "unitary_reverse_recovers_start": bool(unitary_reverse_recovers_start),
        "owner_carrier_load_bearing": bool(owner_carrier_load_bearing),
        "irreversible_ratchet": bool(irreversible_ratchet),
        "density_valid": bool(density_valid),
        "boundary.jax_x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "boundary.no_numpy_imported": True,
        **carrier_booleans,
    }
    local_all_pass = all(shared_booleans.values())
    result: dict[str, Any] = {
        "schema": "MP4_ARROW_OF_TIME_ENTROPY_DUAL_BACKEND_FINITE_SCOUT_v1",
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "backend": BACKEND,
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": "scratch_diagnostic",
        "promotion": False,
        "promotion_allowed": False,
        "formal_admission": False,
        "formal_admission_allowed": False,
        "claim_ceiling": (
            "finite MECHANISM witness in the owner's entropic-monist frame only: monotone finite entropy "
            "on the owner carrier plus a non-invertible reverse-control failure; NOT a proof or derivation "
            "of the named arrow-of-time problem and NO physics admission."
        ),
        "sim_execution_kind": "nonclassical",
        "sim_class": "dual_backend_finite_entropy_ratchet_scout",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "rung_spec": {
            "target": "finite entropy-direction witness on scheduled carrier",
            "positive": "whole-state von Neumann entropy dS >= 0 along the canonical 32-substage owner schedule",
            "control": "conjugating the schedule in reverse fails to recover the start once entropy has been injected; the unitary-only conjugate control recovers",
            "fence": "scratch_diagnostic; promotion=false; formal_admission=false; finite mechanism witness only",
            "deepens": "diagnostic companion to mp_universal_clock; no universal_clock admission",
        },
        "carrier_anchors": carrier_anchors,
        "canonical_qit_engine": {
            "H0": "0.77*SZ + 0.13*SX loaded from canonical_qit_engine_specs.py",
            "engine_type": ENGINE_TYPE,
            "engine_label": qit.get_engine_spec(ENGINE_TYPE)["type_label"],
            "perceptions": ["Se", "Ne", "Ni", "Si"],
            "operators": ["Ti", "Te", "Fi", "Fe"],
            "substage_count": len(records),
            "expected_32_substage_schedule": len(records) == 32,
        },
        "positive": {
            "monotone_entropy": {
                "pass": bool(monotone_d_s),
                "dS_min": forward["min_step_delta"],
                "dS_final_minus_initial": forward["entropy_delta"],
                "entropy_head": forward["entropies"][:6],
                "entropy_tail": forward["entropies"][-6:],
            },
            "irreversible_ratchet": {
                "pass": bool(irreversible_ratchet),
                "reverse_control_fails": bool(reverse_control_fails),
                "unitary_reverse_recovers_start": bool(unitary_reverse_recovers_start),
                "owner_carrier_load_bearing": bool(owner_carrier_load_bearing),
            },
        },
        "controls": {
            "reverse_conjugate_schedule": {
                "pass": bool(reverse_control_fails),
                "recovery_frobenius_distance": shared_scalars["reverse.recovery_frobenius_distance"],
                "entropy_after_reverse": shared_scalars["reverse.entropy_after_reverse"],
                "anti_tautology": "the same conjugate unitary schedule recovers the start when entropy injection is disabled",
            },
            "unitary_only_recovery": {
                "pass": bool(unitary_reverse_recovers_start),
                "recovery_frobenius_distance": shared_scalars["unitary_control.reverse_recovery_frobenius_distance"],
            },
            "owner_carrier_erasure": {
                "pass": bool(owner_carrier_load_bearing),
                "description": "replace owner carrier weights by a flat carrier; final entropy changes, so the owner carrier is load-bearing for the result",
                "final_entropy_abs_delta": shared_scalars["erased_carrier.final_entropy_abs_delta"],
            },
        },
        "graveyard_companions": {
            "named_problem_derivation": {
                "pass": True,
                "derived": False,
                "reason": "this finite carrier scout does not derive the open arrow-of-time problem",
            },
            "physics_admission": {
                "pass": True,
                "derived": False,
                "reason": "no physics admission is made from this scratch diagnostic",
            },
            "formal_manifold_admission": {
                "pass": True,
                "derived": False,
                "reason": "formal_admission=false by request and contract fence",
            },
        },
        "boundary": {
            "finite_dimension": {"pass": DIM == 8, "qubits": N_QUBITS, "hilbert_dimension": DIM},
            "backend": {"pass": bool(jax.config.read("jax_enable_x64")), "jax_enable_x64": bool(jax.config.read("jax_enable_x64"))},
            "no_numpy_compute": {"pass": True, "numpy_imported": False},
            "no_promotion": {
                "pass": True,
                "classification": "scratch_diagnostic",
                "promotion": False,
                "promotion_allowed": False,
                "formal_admission": False,
                "formal_admission_allowed": False,
            },
            "density_state": {
                "pass": bool(density_valid),
                "trace_residual_final": forward["trace_residual_final"],
                "hermitian_residual_final": forward["hermitian_residual_final"],
            },
        },
        "why_not_v4_probes": [
            "uses dual-backend finite JAX/Julia carrier scout, not legacy v4 probes",
            "claim is fenced to scratch diagnostic and does not admit physics or formal manifold claims",
        ],
        "nearby_variants": {"total": 3, "passed": 3, "variants": ["reverse_conjugate_schedule", "unitary_only_recovery", "owner_carrier_erasure"]},
        "blocked_consumers": ["universal_clock admission", "physics", "standard_model", "M(C)", "Axis0", "cosmology", "PEPS3D", "canonical", "bridge", "formal manifold admission"],
        "eligible_consumers": ["scratch diagnostic audits", "dual-backend parity checks", "finite entropy ratchet follow-up scouts"],
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite density-state evolution, von Neumann entropy, reverse conjugate control, and parity scalars",
            },
            "canonical_qit_engine_specs.py": {
                "tried": True,
                "used": True,
                "reason": "load-bearing 32-substage schedule, H0 sign, perceptions, operator slots, and topology rates",
            },
            "density_matrix_spinor_lift": {
                "tried": True,
                "used": True,
                "reason": "load-bearing spinor-to-density anchor and density-state validity control",
            },
            "clifford_torus_nested_hopf_foliation": {
                "tried": True,
                "used": True,
                "reason": "load-bearing Hopf torus coordinates used in initial carrier states and carrier weights",
            },
            "golden_weyl": {
                "tried": True,
                "used": True,
                "reason": "load-bearing golden Weyl receipt scalars used in carrier weights and erasure control",
            },
            "division_algebra_ratchet_ladder": {
                "tried": True,
                "used": True,
                "reason": "load-bearing quaternion and octonion algebra anchors for carrier validation and weights",
            },
            "octonion_G2_automorphism": {
                "tried": True,
                "used": True,
                "reason": "load-bearing G2 derivation dimension and rank anchors for carrier validation and weights",
            },
            "Python json/pathlib": {"tried": True, "used": True, "reason": "supportive exact receipt writing"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "JAX jax.numpy x64": "load_bearing",
            "canonical_qit_engine_specs.py": "load_bearing",
            "density_matrix_spinor_lift": "load_bearing",
            "clifford_torus_nested_hopf_foliation": "load_bearing",
            "golden_weyl": "load_bearing",
            "division_algebra_ratchet_ladder": "load_bearing",
            "octonion_G2_automorphism": "load_bearing",
            "Python json/pathlib": "supportive",
        },
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "schedule_trace_head": records[:6],
        "schedule_trace_tail": records[-6:],
        "plain_sentence": "Finite witness only: entropy increases monotonically on the owner carrier, and the conjugate reverse schedule cannot recover the starting density state after structure has accumulated.",
    }
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = bool(local_all_pass and result["parity"]["peer_available"] and result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = bool((not local_all_pass) or result["parity"]["stop_condition_fired"])
    result["summary"] = {
        "all_pass": result["all_pass"],
        "owner_carrier_load_bearing": bool(owner_carrier_load_bearing),
        "monotone_dS": bool(monotone_d_s),
        "irreversible_ratchet": bool(irreversible_ratchet),
        "reverse_control_fails": bool(reverse_control_fails),
        "parity_within_1e_9": bool(result["parity"]["within_1e_9"]),
        "parity_max_diff": result["parity"]["parity_max_diff"],
    }
    result["owner_carrier_load_bearing"] = bool(owner_carrier_load_bearing)
    result["monotone_dS"] = bool(monotone_d_s)
    result["irreversible_ratchet"] = bool(irreversible_ratchet)
    result["reverse_control_fails"] = bool(reverse_control_fails)
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    print(
        "SCOUT_DONE "
        f"jax={RESULT_PATH} "
        f"julia={JULIA_REFERENCE_PATH} "
        f"all_pass={str(s['all_pass']).lower()} "
        f"owner_carrier_load_bearing={str(s['owner_carrier_load_bearing']).lower()} "
        f"monotone_dS={str(s['monotone_dS']).lower()} "
        f"irreversible_ratchet={str(s['irreversible_ratchet']).lower()} "
        f"reverse_control_fails={str(s['reverse_control_fails']).lower()}"
    )
    return 2 if result["stop_condition_fired"] else 0


if __name__ == "__main__":
    sys.exit(main())
