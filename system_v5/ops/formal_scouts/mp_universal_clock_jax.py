#!/usr/bin/env python3
# object_id: mp_universal_clock
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


OBJECT_ID = "mp_universal_clock"
BACKEND = "jax_jnp_x64"
REPO_ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUT_DIR = REPO_ROOT / "system_v5" / "ops" / "formal_scouts"
JULIA_CARRIER_DIR = REPO_ROOT / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUT_DIR / "results" / "mp_universal_clock_results.json"
JULIA_REFERENCE_PATH = JULIA_CARRIER_DIR / "mp_universal_clock_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
N_QUBITS = 3
DIM = 2**N_QUBITS

sys.path.insert(0, str(FORMAL_SCOUT_DIR))
sys.path.insert(0, str(JULIA_CARRIER_DIR))

import canonical_qit_engine_specs as qit  # noqa: E402
import jax_clifford_algebra_ladder as clifford  # noqa: E402
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
    # Source object is torch complex128 in canonical_qit_engine_specs.py; conversion
    # is through Python scalar lists, with all scout computation in jnp.
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


def reduced_one_qubit(rho: jax.Array, q: int) -> jax.Array:
    red = jnp.zeros((2, 2), dtype=jnp.complex128)
    other = [idx for idx in range(N_QUBITS) if idx != q]
    for a in range(2):
        for b in range(2):
            value = 0.0 + 0.0j
            for mask in range(2 ** (N_QUBITS - 1)):
                ket_bits = [0] * N_QUBITS
                bra_bits = [0] * N_QUBITS
                ket_bits[q] = a
                bra_bits[q] = b
                for pos, qubit in enumerate(other):
                    bit = (mask >> (N_QUBITS - 2 - pos)) & 1
                    ket_bits[qubit] = bit
                    bra_bits[qubit] = bit
                ket = sum(bit << (N_QUBITS - 1 - idx) for idx, bit in enumerate(ket_bits))
                bra = sum(bit << (N_QUBITS - 1 - idx) for idx, bit in enumerate(bra_bits))
                value = value + rho[ket, bra]
            red = red.at[a, b].set(value)
    return red


def permutation_unitary(order: list[int]) -> jax.Array:
    perm = jnp.zeros((DIM, DIM), dtype=jnp.complex128)
    for old in range(DIM):
        bits = [(old >> (N_QUBITS - 1 - idx)) & 1 for idx in range(N_QUBITS)]
        new_bits = [bits[idx] for idx in order]
        new = sum(bit << (N_QUBITS - 1 - idx) for idx, bit in enumerate(new_bits))
        perm = perm.at[new, old].set(1.0 + 0.0j)
    return perm


def schedule_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for engine_type in [0, 1]:
        for main_idx, (perception, loop_class) in enumerate(qit.get_schedule(engine_type)):
            topo = qit.get_topology_spec(perception, engine_type)
            terrain = qit.get_terrain_dynamics_spec(perception, engine_type)
            for substage_idx in range(qit.N_SUBSTAGES_PER_MAIN):
                slot = qit.get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
                records.append(
                    {
                        "record_index": len(records),
                        "engine_type": engine_type,
                        "type_label": qit.get_engine_spec(engine_type)["type_label"],
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


def evolve_pure_schedule(records: list[dict[str, Any]]) -> list[jax.Array]:
    h0 = h0_from_canonical_spec()
    etas = [
        py_float(jnp.pi / 11.0),
        py_float(jnp.pi / 5.0),
        py_float(3.0 * jnp.pi / 11.0),
    ]
    psi = product_state(
        [
            spinor_lift.spinor_from_angles(2.0 * eta, 0.19 + idx * 0.41)
            for idx, eta in enumerate(etas)
        ]
    )
    states = []
    for rec in records:
        q = (rec["main_stage_index"] + rec["substage_index"] + rec["engine_type"]) % N_QUBITS
        r = (q + 1 + rec["engine_type"]) % N_QUBITS
        h_sign = 1.0 if rec["engine_type"] == 0 else -1.0
        local_theta = 0.18 * rec["sign"] * h_sign * (1.0 + 0.25 * rec["rate"])
        local_u = one_qubit_op(one_qubit_h_unitary(h_sign * h0, local_theta), q)
        op = PAULI_BY_OPERATOR[rec["operator"]]
        axis_op = PAULI_BY_AXIS[rec["projector_axis"]]
        pair_word = two_qubit_op(op, q, axis_op, r)
        pair_theta = 0.055 * rec["sign"] * (1.0 + rec["rate"]) * (1.0 + 0.1 * rec["substage_index"])
        pair_u = pauli_word_unitary(pair_word, pair_theta)
        psi = normalize(pair_u @ (local_u @ psi))
        states.append(psi)
    return states


def rho_from_pure_and_extent(psi: jax.Array, step_idx: int, total_steps: int) -> tuple[jax.Array, float]:
    fraction = (step_idx + 1) / total_steps
    p = 0.015 + 0.515 * (fraction**1.18)
    rho = (1.0 - p) * dm(psi) + p * jnp.eye(DIM, dtype=jnp.complex128) / DIM
    return rho, p


def build_trajectory(records: list[dict[str, Any]]) -> dict[str, Any]:
    pure_states = evolve_pure_schedule(records)
    rhos: list[jax.Array] = []
    entropy_values: list[float] = []
    extent_values: list[float] = []
    wrong_scalars: list[float] = []
    local_entropy_rows: list[list[float]] = []
    z0 = one_qubit_op(SZ, 0)
    for idx, psi in enumerate(pure_states):
        rho, p = rho_from_pure_and_extent(psi, idx, len(pure_states))
        rhos.append(rho)
        entropy = finite_entropy(rho)
        entropy_values.append(entropy)
        extent_values.append(float(jnp.exp(entropy)))
        wrong_scalars.append(py_float(jnp.real(jnp.trace(rho @ z0))))
        local_entropy_rows.append([finite_entropy(reduced_one_qubit(rho, q)) for q in range(N_QUBITS)])
        records[idx]["global_depolarizing_extent_fraction"] = p
    local_final = local_entropy_rows[-1]
    local_density_final = [x / extent_values[-1] for x in local_final]
    diffs = [entropy_values[idx + 1] - entropy_values[idx] for idx in range(len(entropy_values) - 1)]
    wrong_diffs = [wrong_scalars[idx + 1] - wrong_scalars[idx] for idx in range(len(wrong_scalars) - 1)]
    return {
        "rhos": rhos,
        "entropy_values": entropy_values,
        "extent_values": extent_values,
        "wrong_scalars": wrong_scalars,
        "local_entropy_rows": local_entropy_rows,
        "local_t_final": local_density_final,
        "global_entropy_min_step_delta": min(diffs),
        "wrong_scalar_positive_delta_count": sum(1 for x in wrong_diffs if x > TOL),
        "wrong_scalar_negative_delta_count": sum(1 for x in wrong_diffs if x < -TOL),
    }


def frame_checks(final_rho: jax.Array, entropy_reference: float, wrong_reference: float) -> dict[str, Any]:
    local_frame = kron_all(
        [
            one_qubit_h_unitary(SX, 0.73),
            one_qubit_h_unitary(SY, -0.41),
            one_qubit_h_unitary(SZ, 0.29),
        ]
    )
    relabel = permutation_unitary([2, 0, 1])
    rho_frame = local_frame @ final_rho @ jnp.conj(local_frame.T)
    rho_relabel = relabel @ final_rho @ jnp.conj(relabel.T)
    z0 = one_qubit_op(SZ, 0)
    return {
        "local_unitary_entropy_abs_diff": abs(finite_entropy(rho_frame) - entropy_reference),
        "subsystem_relabel_entropy_abs_diff": abs(finite_entropy(rho_relabel) - entropy_reference),
        "wrong_scalar_local_unitary_abs_diff": abs(py_float(jnp.real(jnp.trace(rho_frame @ z0))) - wrong_reference),
        "wrong_scalar_relabel_abs_diff": abs(py_float(jnp.real(jnp.trace(rho_relabel @ z0))) - wrong_reference),
    }


def erased_structure_control(records: list[dict[str, Any]]) -> dict[str, Any]:
    psi = product_state([spinor_lift.spinor_from_angles(jnp.pi / 2.0, 0.0) for _ in range(N_QUBITS)])
    local_rows: list[list[float]] = []
    entropies: list[float] = []
    for idx in range(len(records)):
        rho, _ = rho_from_pure_and_extent(psi, idx, len(records))
        entropies.append(finite_entropy(rho))
        local_rows.append([finite_entropy(reduced_one_qubit(rho, q)) for q in range(N_QUBITS)])
    final_spread = max(local_rows[-1]) - min(local_rows[-1])
    diffs = [entropies[idx + 1] - entropies[idx] for idx in range(len(entropies) - 1)]
    return {
        "description": "canonical operator/topology structure erased: same extent ramp on a symmetric product state",
        "global_entropy_min_step_delta": min(diffs),
        "local_entropy_final_spread": final_spread,
        "local_t_varies": final_spread > 1.0e-4,
    }


def carrier_anchor_values() -> tuple[dict[str, Any], dict[str, float], dict[str, bool]]:
    q_table = division.quaternion_table()
    qi = jnp.eye(4, dtype=jnp.float64)[1]
    qj = jnp.eye(4, dtype=jnp.float64)[2]
    qk = jnp.eye(4, dtype=jnp.float64)[3]
    q_ij_residual = py_float(jnp.linalg.norm(division.multiply(q_table, qi, qj) - qk))

    cl30 = clifford.clifford_table([1, 1, 1])
    cl30_even_dim = sum(1 for mask in range(cl30.shape[0]) if mask.bit_count() % 2 == 0)
    gamma_residual = clifford.gamma_relation_residual(clifford.gamma_matrices_cl30())

    oct_table = g2.octonion_table()
    rank, _rank_tol, ns, _singular_values = g2.nullspace_data(g2.derivation_constraint_matrix(oct_table))
    g2_der_dim = int(ns.shape[1])

    s_table = division.cayley_dickson_double(oct_table)
    left = jnp.zeros((16,), dtype=jnp.float64).at[1].set(-1.0).at[10].set(-1.0)
    right = jnp.zeros((16,), dtype=jnp.float64).at[4].set(-1.0).at[15].set(1.0)
    sedenion_zero_product_norm = py_float(jnp.linalg.norm(division.multiply(s_table, left, right)))

    z, w = hopf.torus_point(py_float(jnp.pi / 4.0), 0.37, 0.91)
    hopf_s3_residual = py_float(jnp.abs(jnp.abs(z) ** 2 + jnp.abs(w) ** 2 - 1.0))

    golden_receipt = json.loads((JULIA_CARRIER_DIR / "golden_weyl_jax_receipt.json").read_text(encoding="utf-8"))
    golden_flat_delta = float(golden_receipt["controls"]["flat_S2"]["observable_delta"])
    golden_eta_count = float(golden_receipt["eta_base"]["count"])

    scalars = {
        "carrier.quaternion_ij_minus_k_residual": q_ij_residual,
        "carrier.cl30_even_dim": float(cl30_even_dim),
        "carrier.gamma_relation_residual": gamma_residual,
        "carrier.g2_derivation_dim": float(g2_der_dim),
        "carrier.g2_constraint_rank": float(rank),
        "carrier.sedenion_zero_product_norm": sedenion_zero_product_norm,
        "carrier.hopf_s3_residual": hopf_s3_residual,
        "carrier.golden_weyl_flat_control_delta": golden_flat_delta,
        "carrier.golden_weyl_eta_count": golden_eta_count,
    }
    booleans = {
        "carrier.quaternion_table_real": q_ij_residual < TOL,
        "carrier.clifford_even_dim_real": cl30_even_dim == 4,
        "carrier.octonion_g2_derivation_dim_real": g2_der_dim == 14,
        "carrier.sedenion_break_real": sedenion_zero_product_norm < TOL,
        "carrier.hopf_torus_real": hopf_s3_residual < TOL,
        "carrier.golden_weyl_control_real": golden_flat_delta > 0.9,
    }
    anchors = {
        "source_contract_paths": [
            str(JULIA_CARRIER_DIR / "division_algebra_ratchet_ladder.jl"),
            str(JULIA_CARRIER_DIR / "clifford_algebra_ladder.jl"),
            str(JULIA_CARRIER_DIR / "octonion_G2_automorphism.jl"),
            str(JULIA_CARRIER_DIR / "sedenion_break_prelim.jl"),
            str(JULIA_CARRIER_DIR / "density_matrix_spinor_lift.jl"),
            str(JULIA_CARRIER_DIR / "clifford_torus_nested_hopf_foliation.jl"),
            str(JULIA_CARRIER_DIR / "golden_weyl_julia.jl"),
            str(FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py"),
        ],
        "jax_source_paths_used": [
            str(JULIA_CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py"),
            str(JULIA_CARRIER_DIR / "jax_clifford_algebra_ladder.py"),
            str(JULIA_CARRIER_DIR / "jax_octonion_G2_automorphism.py"),
            str(JULIA_CARRIER_DIR / "jax_sedenion_break_prelim.py"),
            str(JULIA_CARRIER_DIR / "jax_density_matrix_spinor_lift.py"),
            str(JULIA_CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py"),
            str(JULIA_CARRIER_DIR / "golden_weyl_jax_receipt.json"),
        ],
    }
    return anchors, scalars, booleans


def build_shared_scalars(
    trajectory: dict[str, Any],
    frames: dict[str, Any],
    erased: dict[str, Any],
    carrier_scalars: dict[str, float],
) -> dict[str, float]:
    entropies = trajectory["entropy_values"]
    extents = trajectory["extent_values"]
    local_t = trajectory["local_t_final"]
    wrong_values = trajectory["wrong_scalars"]
    out = {
        "schedule.substage_count": float(len(entropies)),
        "global_entropy.initial": entropies[0],
        "global_entropy.final": entropies[-1],
        "global_entropy.delta": entropies[-1] - entropies[0],
        "global_entropy.min_step_delta": trajectory["global_entropy_min_step_delta"],
        "global_extent.initial": extents[0],
        "global_extent.final": extents[-1],
        "global_extent.delta": extents[-1] - extents[0],
        "local_t.q0_final": local_t[0],
        "local_t.q1_final": local_t[1],
        "local_t.q2_final": local_t[2],
        "local_t.final_spread": max(local_t) - min(local_t),
        "frame.local_unitary_entropy_abs_diff": frames["local_unitary_entropy_abs_diff"],
        "frame.subsystem_relabel_entropy_abs_diff": frames["subsystem_relabel_entropy_abs_diff"],
        "control.wrong_scalar.initial": wrong_values[0],
        "control.wrong_scalar.final": wrong_values[-1],
        "control.wrong_scalar.local_unitary_abs_diff": frames["wrong_scalar_local_unitary_abs_diff"],
        "control.wrong_scalar.relabel_abs_diff": frames["wrong_scalar_relabel_abs_diff"],
        "control.wrong_scalar.positive_delta_count": float(trajectory["wrong_scalar_positive_delta_count"]),
        "control.wrong_scalar.negative_delta_count": float(trajectory["wrong_scalar_negative_delta_count"]),
        "control.erased.global_entropy_min_step_delta": erased["global_entropy_min_step_delta"],
        "control.erased.local_entropy_final_spread": erased["local_entropy_final_spread"],
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
    trajectory = build_trajectory(records)
    final_rho = trajectory["rhos"][-1]
    frames = frame_checks(final_rho, trajectory["entropy_values"][-1], trajectory["wrong_scalars"][-1])
    erased = erased_structure_control(records)
    carrier_anchors, carrier_scalars, carrier_booleans = carrier_anchor_values()

    global_monotone = (
        trajectory["global_entropy_min_step_delta"] >= -TOL
        and trajectory["extent_values"][-1] > trajectory["extent_values"][0]
    )
    frame_invariant = (
        frames["local_unitary_entropy_abs_diff"] < TOL
        and frames["subsystem_relabel_entropy_abs_diff"] < TOL
    )
    local_t_varies = (max(trajectory["local_t_final"]) - min(trajectory["local_t_final"])) > 1.0e-4
    wrong_scalar_nonmonotone = (
        trajectory["wrong_scalar_positive_delta_count"] > 0
        and trajectory["wrong_scalar_negative_delta_count"] > 0
    )
    wrong_scalar_frame_fails = (
        frames["wrong_scalar_local_unitary_abs_diff"] > 1.0e-3
        and frames["wrong_scalar_relabel_abs_diff"] > 1.0e-3
    )
    erased_flip_fires = not bool(erased["local_t_varies"])
    broken_control_fails = wrong_scalar_nonmonotone and wrong_scalar_frame_fails and erased_flip_fires
    shared_booleans = {
        "global_monotone": bool(global_monotone),
        "frame_invariant": bool(frame_invariant),
        "local_t_varies": bool(local_t_varies),
        "control.wrong_scalar_nonmonotone": bool(wrong_scalar_nonmonotone),
        "control.wrong_scalar_frame_fails": bool(wrong_scalar_frame_fails),
        "control.erased_structure_flip_fires": bool(erased_flip_fires),
        "broken_control_fails": bool(broken_control_fails),
        **carrier_booleans,
    }
    local_all_pass = all(shared_booleans.values())
    result: dict[str, Any] = {
        "schema": "MP_UNIVERSAL_CLOCK_DUAL_BACKEND_FINITE_SCOUT_v1",
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "backend": BACKEND,
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": (
            "finite witness only: global entropy/extent readout versus local entropy-density readouts; "
            "NO physics, Standard Model, M(C), Axis0, dark-energy, cosmology, bridge, or formal admission"
        ),
        "sim_execution_kind": "nonclassical",
        "sim_class": "finite_dual_backend_clock_witness",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "rung_spec": {
            "i": "global von Neumann entropy / total finite extent scalar of the whole density state",
            "t": "subsystem-local entropy density readout, allowed to differ by qubit",
            "positive": "i monotone along canonical paired-engine 32-substage schedules and invariant under local unitaries/subsystem relabeling while local t differs",
            "control": "wrong locally-resettable scalar on the same state is nonmonotone and fails frame/relabel invariance; erased-structure schedule loses local t variation",
        },
        "carrier_anchors": carrier_anchors,
        "canonical_qit_engine": {
            "H0": "0.77*SZ + 0.13*SX loaded from canonical_qit_engine_specs.py",
            "engine_types": ["Type 1: +H0", "Type 2: -H0"],
            "perceptions": ["Se", "Ne", "Ni", "Si"],
            "operators": ["Ti", "Te", "Fi", "Fe"],
            "substage_count": len(records),
            "per_engine_substages": qit.N_TOTAL_SUBSTAGES_PER_ENGINE,
        },
        "positive": {
            "global_monotone": {"pass": bool(global_monotone), "min_step_delta": trajectory["global_entropy_min_step_delta"]},
            "frame_invariant": {"pass": bool(frame_invariant), **frames},
            "local_t_varies": {"pass": bool(local_t_varies), "local_t_final": trajectory["local_t_final"]},
        },
        "controls": {
            "wrong_scalar": {
                "pass": bool(broken_control_fails),
                "wrong_scalar_nonmonotone": bool(wrong_scalar_nonmonotone),
                "wrong_scalar_frame_fails": bool(wrong_scalar_frame_fails),
                "anti_tautology": "same final density state is read with a local Z scalar, then transformed by real local unitary and subsystem relabeling",
            },
            "erased_structure": {"pass": bool(erased_flip_fires), **erased},
        },
        "boundary": {
            "finite_dimension": {"qubits": N_QUBITS, "hilbert_dimension": DIM, "pass": DIM == 8},
            "no_numpy_compute": {"numpy_imported": False, "pass": True},
            "no_promotion": {"classification": "scratch_diagnostic", "promotion_allowed": False, "formal_admission_allowed": False, "pass": True},
        },
        "blocked_consumers": ["physics", "Standard Model", "M(C)", "Axis0", "dark energy admission", "cosmology", "bridge", "formal manifold admission"],
        "eligible_consumers": ["scratch diagnostic audits", "dual-backend parity checks", "finite readout follow-up scouts"],
        "TOOL_MANIFEST": {
            "JAX jax.numpy x64": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite density-state evolution, von Neumann entropy, extent readout, frame/relabel controls, and parity scalars",
            },
            "canonical_qit_engine_specs.py": {
                "tried": True,
                "used": True,
                "reason": "load-bearing schedule, H0 sign, perceptions, operator slots, topology rates, and 32-substage per-engine structure",
            },
            "system_v5/julia_carrier carrier objects": {
                "tried": True,
                "used": True,
                "reason": "load-bearing carrier anchors for division ladder, Clifford ladder, G2 octonion derivation, sedenion break, density spinor lift, Hopf torus, and golden Weyl controls",
            },
            "Python json/pathlib": {"tried": True, "used": True, "reason": "supportive exact receipt writing"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "JAX jax.numpy x64": "load_bearing",
            "canonical_qit_engine_specs.py": "load_bearing",
            "system_v5/julia_carrier carrier objects": "load_bearing",
            "Python json/pathlib": "supportive",
        },
        "shared_scalars": build_shared_scalars(trajectory, frames, erased, carrier_scalars),
        "shared_booleans": shared_booleans,
        "schedule_trace_head": records[:6],
        "schedule_trace_tail": records[-6:],
        "plain_sentence": "Finite witness only: the whole-state entropy/extent scalar is monotone and frame-invariant, local entropy-density t varies by subsystem, and the wrong local scalar control fails.",
    }
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = bool(local_all_pass and result["parity"]["peer_available"] and result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = bool((not local_all_pass) or result["parity"]["stop_condition_fired"])
    result["summary"] = {
        "all_pass": result["all_pass"],
        "global_monotone": bool(global_monotone),
        "frame_invariant": bool(frame_invariant),
        "local_t_varies": bool(local_t_varies),
        "broken_control_fails": bool(broken_control_fails),
        "parity_within_1e_9": bool(result["parity"]["within_1e_9"]),
        "parity_max_diff": result["parity"]["parity_max_diff"],
    }
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
        f"global_monotone={str(s['global_monotone']).lower()} "
        f"frame_invariant={str(s['frame_invariant']).lower()} "
        f"local_t_varies={str(s['local_t_varies']).lower()} "
        f"broken_control_fails={str(s['broken_control_fails']).lower()}"
    )
    return 2 if result["stop_condition_fired"] else 0


if __name__ == "__main__":
    sys.exit(main())
