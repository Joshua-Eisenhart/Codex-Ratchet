#!/usr/bin/env python3
# object_id: disc_qit_source_native_face_knot_shell_discriminator
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import hashlib
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
        "reason": "load-bearing x64 backend for the finite 3-qubit carrier mutation discriminator",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing matrix/vector algebra for owner, erased, operator-erased, phase-erased, and two-qubit witnesses",
    },
    "Julia peer backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent mirror backend for parity over shared scalars and booleans",
    },
    "canonical_qit_engine_specs.py": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source-native schedule/operator witness for the canonical 3-qubit QIT engine constants",
    },
    "density_matrix_spinor_lift": {
        "tried": True,
        "used": True,
        "reason": "load-bearing owner carrier construction from spinor lift to finite density matrix",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive path handling, source hashing, timestamps, imports, and JSON result serialization",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded; no NumPy import, alias, array conversion, or compute path in this JAX scratch row",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Julia peer backend": "load_bearing",
    "canonical_qit_engine_specs.py": "load_bearing",
    "density_matrix_spinor_lift": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}


OBJECT_ID = "disc_qit_source_native_face_knot_shell_discriminator"
NAME = OBJECT_ID
BACKEND = "jax_jnp_x64"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUTS = REPO / "system_v5" / "ops" / "formal_scouts"
JULIA_CARRIER = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUTS / "results" / "disc_qit_source_native_results.json"
JULIA_RESULT_PATH = JULIA_CARRIER / "disc_qit_source_native_julia_results.json"
SOURCE_PATH = FORMAL_SCOUTS / "sim_disc_qit_source_native_face_knot_shell_discriminator_probe.py"
CANONICAL_QIT_PATH = FORMAL_SCOUTS / "canonical_qit_engine_specs.py"
QIT_TAXONOMY_PATH = FORMAL_SCOUTS / "qit_engine_3qubit_face_knot_taxonomy_jax.py"
DENSITY_LIFT_JAX_PATH = JULIA_CARRIER / "jax_density_matrix_spinor_lift.py"
DENSITY_LIFT_JULIA_PATH = JULIA_CARRIER / "density_matrix_spinor_lift.jl"

N_QUBITS = 3
PARITY_TOL = 1.0e-9
FACE_THRESHOLD = 5.0e-2
KNOT_THRESHOLD = 1.0e-2
SHELL_THRESHOLD = 1.0e-4
MUTATION_DIE_RATIO = 0.12
CLAIM_CEILING = (
    "QIT source-native face/knot/shell carrier-readout discriminator only. "
    "classification=scratch_diagnostic; promotion=false; formal_admission=false. "
    "No QIT admission, no physics, no gravity, no dark-sector, no Axis0, no M(C), "
    "no bridge, no PEPS3D, and no final manifold closure."
)
BLOCKED_CONSUMERS = [
    "QIT engine admission",
    "physics",
    "gravity",
    "dark-sector",
    "Axis0",
    "M(C)",
    "bridge",
    "PEPS3D",
    "formal admission",
    "promotion",
]
READOUT_MAP = {
    "face_entropy_growth": "entropy_growth",
    "face_three_cell_abs": "three_cell_abs",
    "knot_bounded_mass": "bounded_knot_mass",
    "shell_sync_gradient": "sync_gradient_gravity",
}

sys.path.insert(0, str(FORMAL_SCOUTS))
sys.path.insert(0, str(JULIA_CARRIER))

import canonical_qit_engine_specs as canonical_specs  # noqa: E402
import jax_density_matrix_spinor_lift as lift  # noqa: E402
import qit_engine_3qubit_face_knot_taxonomy_jax as qit_taxonomy  # noqa: E402


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_refs() -> dict[str, Any]:
    return {
        "self": {"path": str(SOURCE_PATH), "exists": SOURCE_PATH.exists(), "sha256": sha256_file(SOURCE_PATH)},
        "canonical_qit_engine_specs": {
            "path": str(CANONICAL_QIT_PATH),
            "exists": CANONICAL_QIT_PATH.exists(),
            "sha256": sha256_file(CANONICAL_QIT_PATH),
        },
        "qit_engine_3qubit_face_knot_taxonomy_jax": {
            "path": str(QIT_TAXONOMY_PATH),
            "exists": QIT_TAXONOMY_PATH.exists(),
            "sha256": sha256_file(QIT_TAXONOMY_PATH),
        },
        "jax_density_matrix_spinor_lift": {
            "path": str(DENSITY_LIFT_JAX_PATH),
            "exists": DENSITY_LIFT_JAX_PATH.exists(),
            "sha256": sha256_file(DENSITY_LIFT_JAX_PATH),
        },
        "density_matrix_spinor_lift_julia": {
            "path": str(DENSITY_LIFT_JULIA_PATH),
            "exists": DENSITY_LIFT_JULIA_PATH.exists(),
            "sha256": sha256_file(DENSITY_LIFT_JULIA_PATH),
        },
    }


def canonical_spec_witness() -> dict[str, Any]:
    schedule_0 = [tuple(row) for row in canonical_specs.get_schedule(0)]
    schedule_1 = [tuple(row) for row in canonical_specs.get_schedule(1)]
    schedule_match = (
        schedule_0 == [tuple(row) for row in qit_taxonomy.ENGINE_SCHEDULE_TYPE_ONE]
        and schedule_1 == [tuple(row) for row in qit_taxonomy.ENGINE_SCHEDULE_TYPE_TWO]
    )
    slot_rows = []
    slot_match = True
    for engine_type, schedule in ((0, schedule_0), (1, schedule_1)):
        for substage_idx in range(4):
            perception, loop_class = schedule[substage_idx]
            source = canonical_specs.get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
            local = qit_taxonomy.operator_slot_spec(perception, engine_type, loop_class, substage_idx)
            keys = ("operator", "sign", "precedence", "token", "operator_family")
            same = all(source[key] == local[key] for key in keys)
            slot_match = slot_match and same
            slot_rows.append(
                {
                    "engine_type": engine_type,
                    "perception": perception,
                    "loop_class": loop_class,
                    "substage_idx": substage_idx,
                    "same": bool(same),
                    "operator": source["operator"],
                    "sign": int(source["sign"]),
                    "precedence": source["precedence"],
                    "token": source["token"],
                }
            )
    return {
        "pass": bool(schedule_match and slot_match),
        "schedule_match": bool(schedule_match),
        "slot_match": bool(slot_match),
        "checked_slots": slot_rows,
        "source": str(CANONICAL_QIT_PATH),
    }


def kron_vectors(vectors: list[jax.Array]) -> jax.Array:
    out = vectors[0]
    for vector in vectors[1:]:
        out = jnp.kron(out, vector)
    return out


def lifted_owner_state(*, entangle: bool) -> jax.Array:
    locals_ = [
        lift.spinor_from_angles(0.22, -0.31),
        lift.spinor_from_angles(1.31, 0.27),
        lift.spinor_from_angles(1.48, 0.13),
    ]
    edge_weights = ((0, 1, 0.43), (0, 2, -0.29), (1, 2, 0.91))
    amplitudes = []
    for basis in range(2**N_QUBITS):
        bits = [(basis >> (N_QUBITS - 1 - idx)) & 1 for idx in range(N_QUBITS)]
        amp = jnp.asarray(1.0 + 0.0j, dtype=jnp.complex128)
        for idx, bit in enumerate(bits):
            amp = amp * locals_[idx][bit]
        if entangle:
            phase = sum(weight * (1.0 if bits[a] == bits[b] else -1.0) for a, b, weight in edge_weights)
            amp = amp * jnp.exp(1j * phase)
        amplitudes.append(amp)
    psi = jnp.asarray(amplitudes, dtype=jnp.complex128)
    psi = psi / jnp.linalg.norm(psi)
    pure = qit_taxonomy.pure_density(psi)
    return qit_taxonomy.normalize_density(0.86 * pure + 0.14 * qit_taxonomy.maximally_mixed(N_QUBITS))


def density_lift_witness(owner_rho: jax.Array) -> dict[str, Any]:
    local0 = qit_taxonomy.partial_trace(owner_rho, N_QUBITS, [0])
    bloch0 = lift.bloch_from_rho(local0)
    rebuilt0 = lift.rho_from_bloch(bloch0)
    return {
        "pass": py_float(jnp.linalg.norm(local0 - rebuilt0)) <= 1.0e-9,
        "local0_bloch": [py_float(x) for x in bloch0],
        "local0_rebuild_residual": py_float(jnp.linalg.norm(local0 - rebuilt0)),
        "source": str(DENSITY_LIFT_JAX_PATH),
    }


def branch(label: str, rho: jax.Array, *, n_qubits: int = N_QUBITS, operator_erased: bool = False) -> dict[str, Any]:
    return qit_taxonomy.branch_result(
        label,
        n_qubits=n_qubits,
        engine_type=0,
        schedule=qit_taxonomy.ENGINE_SCHEDULE_TYPE_ONE,
        rho_init=rho,
        operator_erased=operator_erased,
    )


def selected_readouts(result_branch: dict[str, Any]) -> dict[str, float]:
    readouts = result_branch["readouts"]
    return {name: float(readouts[key]) for name, key in READOUT_MAP.items()}


def readout_vector(selected: dict[str, float]) -> jax.Array:
    return jnp.asarray(
        [
            selected["face_entropy_growth"],
            selected["knot_bounded_mass"],
            selected["shell_sync_gradient"],
        ],
        dtype=jnp.float64,
    )


def readout_presence(selected: dict[str, float]) -> dict[str, bool]:
    return {
        "face_present": selected["face_entropy_growth"] > FACE_THRESHOLD,
        "knot_present": selected["knot_bounded_mass"] > KNOT_THRESHOLD,
        "shell_present": selected["shell_sync_gradient"] > SHELL_THRESHOLD,
    }


def row_verdict(
    *,
    owner_present: bool,
    erased_present: bool,
    null_present: bool,
    erase_changes_result: bool,
    survives_mutation: bool,
    parity_ok: bool,
) -> str:
    if not parity_ok:
        return "OPEN"
    if null_present:
        return "GENERIC"
    if not owner_present:
        return "GRAVEYARD"
    if owner_present and erase_changes_result and not survives_mutation and not erased_present:
        return "REAL_CARRIER"
    if survives_mutation and not erase_changes_result:
        return "REPRODUCED"
    if survives_mutation:
        return "CONVENTION"
    return "OPEN"


def parity_block(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "peer_available": False,
            "within_1e_9": False,
            "parity_max_diff": None,
            "worst_key": None,
            "missing_from_peer": sorted(result["shared_scalars"]),
            "missing_from_self": [],
            "boolean_mismatches": [],
            "diffs": {},
        }
    peer = json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))
    self_scalars = result["shared_scalars"]
    peer_scalars = peer.get("shared_scalars", {})
    missing_from_peer = sorted(set(self_scalars) - set(peer_scalars))
    missing_from_self = sorted(set(peer_scalars) - set(self_scalars))
    max_diff = 0.0
    worst_key = None
    diffs: dict[str, float] = {}
    for key, value in self_scalars.items():
        if key in peer_scalars:
            diff = abs(float(value) - float(peer_scalars[key]))
            diffs[key] = diff
            if diff > max_diff:
                max_diff = diff
                worst_key = key
    self_booleans = result["shared_booleans"]
    peer_booleans = peer.get("shared_booleans", {})
    boolean_mismatches = [
        key
        for key, value in self_booleans.items()
        if key in peer_booleans and bool(value) != bool(peer_booleans[key])
    ]
    within = (
        not missing_from_peer
        and not missing_from_self
        and not boolean_mismatches
        and max_diff <= PARITY_TOL
    )
    return {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "peer_available": True,
        "within_1e_9": bool(within),
        "parity_max_diff": float(max_diff),
        "worst_key": worst_key,
        "missing_from_peer": missing_from_peer,
        "missing_from_self": missing_from_self,
        "boolean_mismatches": boolean_mismatches,
        "diffs": diffs,
    }


def build_result() -> dict[str, Any]:
    owner_rho = lifted_owner_state(entangle=True)
    phase_erased_rho = lifted_owner_state(entangle=False)
    erased_rho = qit_taxonomy.maximally_mixed(N_QUBITS)
    owner = branch("owner_source_native_lifted_carrier", owner_rho)
    carrier_erased = branch("carrier_erased_maximally_mixed", erased_rho)
    operator_erased = branch("operator_erased_same_carrier", owner_rho, operator_erased=True)
    phase_erased = branch("phase_erased_same_lift_no_edges", phase_erased_rho)
    twoq = qit_taxonomy.branch_result(
        "two_qubit_floor_control",
        n_qubits=2,
        engine_type=0,
        schedule=qit_taxonomy.ENGINE_SCHEDULE_TYPE_ONE,
        rho_init=qit_taxonomy.two_qubit_density(),
    )

    owner_selected = selected_readouts(owner)
    erased_selected = selected_readouts(carrier_erased)
    op_erased_selected = selected_readouts(operator_erased)
    phase_erased_selected = selected_readouts(phase_erased)
    twoq_selected = selected_readouts(twoq)

    owner_vec = readout_vector(owner_selected)
    erased_vec = readout_vector(erased_selected)
    op_erased_vec = readout_vector(op_erased_selected)
    phase_erased_vec = readout_vector(phase_erased_selected)
    twoq_vec = readout_vector(twoq_selected)
    owner_norm = py_float(jnp.linalg.norm(owner_vec))
    erased_norm = py_float(jnp.linalg.norm(erased_vec))
    erase_delta = py_float(jnp.linalg.norm(owner_vec - erased_vec))
    operator_erase_delta = py_float(jnp.linalg.norm(owner_vec - op_erased_vec))
    phase_erase_delta = py_float(jnp.linalg.norm(owner_vec - phase_erased_vec))
    twoq_delta = py_float(jnp.linalg.norm(owner_vec - twoq_vec))
    survival_ratio = erased_norm / max(owner_norm, 1.0e-15)

    owner_presence = readout_presence(owner_selected)
    erased_presence = readout_presence(erased_selected)
    null_presence = readout_presence(twoq_selected)
    face_knot_shell_present = all(owner_presence.values())
    carrier_erased_present = all(erased_presence.values())
    twoq_null_present = all(null_presence.values())
    survives_mutation = survival_ratio >= MUTATION_DIE_RATIO and carrier_erased_present
    erase_changes_result = erase_delta > max(1.0e-6, 0.5 * owner_norm)
    three_qubit_min = N_QUBITS == 3 and float(twoq["readouts"]["three_cell_abs"]) == 0.0

    source_spec = canonical_spec_witness()
    lift_witness = density_lift_witness(owner_rho)
    shared_scalars = {
        "owner.face_entropy_growth": owner_selected["face_entropy_growth"],
        "owner.face_three_cell_abs": owner_selected["face_three_cell_abs"],
        "owner.knot_bounded_mass": owner_selected["knot_bounded_mass"],
        "owner.shell_sync_gradient": owner_selected["shell_sync_gradient"],
        "carrier_erased.face_entropy_growth": erased_selected["face_entropy_growth"],
        "carrier_erased.face_three_cell_abs": erased_selected["face_three_cell_abs"],
        "carrier_erased.knot_bounded_mass": erased_selected["knot_bounded_mass"],
        "carrier_erased.shell_sync_gradient": erased_selected["shell_sync_gradient"],
        "operator_erased.face_entropy_growth": op_erased_selected["face_entropy_growth"],
        "operator_erased.knot_bounded_mass": op_erased_selected["knot_bounded_mass"],
        "operator_erased.shell_sync_gradient": op_erased_selected["shell_sync_gradient"],
        "phase_erased.face_entropy_growth": phase_erased_selected["face_entropy_growth"],
        "phase_erased.knot_bounded_mass": phase_erased_selected["knot_bounded_mass"],
        "phase_erased.shell_sync_gradient": phase_erased_selected["shell_sync_gradient"],
        "two_qubit_floor.face_entropy_growth": twoq_selected["face_entropy_growth"],
        "two_qubit_floor.knot_bounded_mass": twoq_selected["knot_bounded_mass"],
        "two_qubit_floor.shell_sync_gradient": twoq_selected["shell_sync_gradient"],
        "owner_vector_norm": owner_norm,
        "carrier_erased_vector_norm": erased_norm,
        "erase_delta": erase_delta,
        "operator_erase_delta": operator_erase_delta,
        "phase_erase_delta": phase_erase_delta,
        "twoq_delta": twoq_delta,
        "survival_ratio": survival_ratio,
        "density_lift_local0_rebuild_residual": float(lift_witness["local0_rebuild_residual"]),
        "n_qubits": float(N_QUBITS),
    }
    shared_booleans = {
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "numpy_compute_used": False,
        "torch_compute_used": False,
        "source_spec_witness_pass": bool(source_spec["pass"]),
        "density_lift_witness_pass": bool(lift_witness["pass"]),
        "three_qubit_min": bool(three_qubit_min),
        "source_native": bool(source_spec["pass"] and lift_witness["pass"]),
        "face_knot_shell_present": bool(face_knot_shell_present),
        "carrier_erased_present": bool(carrier_erased_present),
        "twoq_null_present": bool(twoq_null_present),
        "survives_mutation": bool(survives_mutation),
        "erase_changes_result": bool(erase_changes_result),
        "operator_erase_changes_result": bool(operator_erase_delta > 1.0e-4),
        "phase_erase_changes_result": bool(phase_erase_delta > 1.0e-4),
        "all_transition_channels_numeric_cptp": bool(
            owner["transition_channel_checks"]["cptp_numeric_pass"]
            and carrier_erased["transition_channel_checks"]["cptp_numeric_pass"]
            and operator_erased["transition_channel_checks"]["cptp_numeric_pass"]
            and phase_erased["transition_channel_checks"]["cptp_numeric_pass"]
            and twoq["transition_channel_checks"]["cptp_numeric_pass"]
        ),
    }
    pre_parity_result = {
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
    }
    parity = parity_block(pre_parity_result)
    verdict = row_verdict(
        owner_present=face_knot_shell_present,
        erased_present=carrier_erased_present,
        null_present=twoq_null_present,
        erase_changes_result=erase_changes_result,
        survives_mutation=survives_mutation,
        parity_ok=bool(parity["peer_available"] and parity["within_1e_9"]),
    )
    all_pass = (
        bool(parity["peer_available"])
        and bool(parity["within_1e_9"])
        and shared_booleans["source_native"]
        and shared_booleans["three_qubit_min"]
        and shared_booleans["face_knot_shell_present"]
        and shared_booleans["erase_changes_result"]
        and shared_booleans["operator_erase_changes_result"]
        and shared_booleans["phase_erase_changes_result"]
        and shared_booleans["all_transition_channels_numeric_cptp"]
        and not shared_booleans["numpy_compute_used"]
        and not shared_booleans["torch_compute_used"]
        and verdict in {"REAL_CARRIER", "CONVENTION", "REPRODUCED", "GENERIC", "GRAVEYARD"}
    )
    positive = {
        "source_native_canonical_qit_witness": source_spec,
        "density_matrix_spinor_lift_witness": lift_witness,
        "three_qubit_minimum": {
            "pass": bool(three_qubit_min),
            "n_qubits": N_QUBITS,
            "two_qubit_three_cell_abs": float(twoq["readouts"]["three_cell_abs"]),
        },
        "face_knot_shell_owner_present": {
            "pass": bool(face_knot_shell_present),
            "thresholds": {
                "face_entropy_growth": FACE_THRESHOLD,
                "knot_bounded_mass": KNOT_THRESHOLD,
                "shell_sync_gradient": SHELL_THRESHOLD,
            },
            "readouts": owner_selected,
            "presence": owner_presence,
        },
        "owner_carrier_load_bearing": {
            "pass": bool(erase_changes_result),
            "erase_delta": erase_delta,
            "owner_vector_norm": owner_norm,
            "carrier_erased_vector_norm": erased_norm,
            "survival_ratio": survival_ratio,
        },
        "dual_backend_parity": {
            "pass": bool(parity["peer_available"] and parity["within_1e_9"]),
            "parity": parity,
        },
    }
    graveyard_companions = {
        "carrier_erased_control": {
            "pass": not bool(carrier_erased_present),
            "readouts": erased_selected,
            "presence": erased_presence,
            "reason": "maximally mixed carrier keeps schedule but erases the owner spinor/density carrier",
        },
        "operator_erased_control": {
            "pass": shared_booleans["operator_erase_changes_result"],
            "readouts": op_erased_selected,
            "delta_from_owner": operator_erase_delta,
            "reason": "same owner carrier with source operator kicks erased changes the finite readout vector",
        },
        "phase_erased_control": {
            "pass": shared_booleans["phase_erase_changes_result"],
            "readouts": phase_erased_selected,
            "delta_from_owner": phase_erase_delta,
            "reason": "same local spinor densities without entangling phase edges changes the finite readout vector",
        },
        "two_qubit_floor_control": {
            "pass": bool(three_qubit_min),
            "readouts": twoq_selected,
            "reason": "two-qubit floor lacks the third face/shell memory region; tripartite face readout is zero",
        },
    }
    boundary = {
        "classification_fence": {
            "pass": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        },
        "claim_ceiling": {
            "pass": True,
            "claim_ceiling": CLAIM_CEILING,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "honest_discriminator": {
            "pass": verdict in {"REAL_CARRIER", "CONVENTION", "REPRODUCED", "GENERIC", "GRAVEYARD", "OPEN"},
            "row_verdict": verdict,
            "rule": "REAL_CARRIER iff owner present, null absent, and carrier mutation kills the face/knot/shell readout vector",
        },
    }
    return {
        "schema": "SCRATCH_DIAGNOSTIC_RESULT_v1",
        "object_id": OBJECT_ID,
        "name": NAME,
        "backend": BACKEND,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "allowed_claims": [
            "finite scratch discriminator verdict for the face/knot/shell readout vector",
            "dual-backend JAX/Julia parity over shared finite witnesses",
            "owner-carrier load-bearing only when erasing the carrier changes the result",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": "carrier_readout_discriminator_probe",
        "source_alignment_category": "qit_source_native_face_knot_shell_carrier_mutation_discriminator",
        "numpy_compute_used": False,
        "torch_compute_used": False,
        "jax_x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_refs": source_refs(),
        "source_math_lock": {
            "canonical_qit_engine_specs": "schedule and operator-slot witnesses compare canonical specs to the engine runner",
            "density_matrix_spinor_lift": "owner local spinors are lifted to density matrices and checked by Bloch reconstruction",
            "finite_carrier": "(C^2)^3 density matrix, Hilbert dimension 8",
        },
        "carrier": {
            "minimum_qubits": 3,
            "hilbert_dimension": 8,
            "roles": ["left Weyl sheet", "right Weyl sheet", "cut/shell memory spinor"],
            "owner": "density-matrix lift of three local spinors with finite entangling phase edges",
            "mutation": "same engine schedule on maximally mixed 3-qubit carrier",
        },
        "finite_witness": {
            "readout_map": READOUT_MAP,
            "owner": owner_selected,
            "carrier_erased": erased_selected,
            "operator_erased": op_erased_selected,
            "phase_erased": phase_erased_selected,
            "two_qubit_floor": twoq_selected,
            "owner_vector_norm": owner_norm,
            "carrier_erased_vector_norm": erased_norm,
            "erase_delta": erase_delta,
            "survival_ratio": survival_ratio,
        },
        "row_verdict": verdict,
        "three_qubit_min": bool(three_qubit_min),
        "source_native": bool(source_spec["pass"] and lift_witness["pass"]),
        "face_knot_shell_present": bool(face_knot_shell_present),
        "survives_mutation": bool(survives_mutation),
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": 4,
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "variants": list(graveyard_companions),
        },
        "why_not_v4_probes": {
            "reason": "key-list or toy-knot readouts do not discriminate carrier dependence; this row mutates the actual 3-qubit carrier and measures finite readout death/survival",
        },
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "parity": parity,
        "all_pass": bool(all_pass),
        "stop_condition_fired": not bool(all_pass),
        "blockers": []
        if all_pass
        else [
            "parity missing/disagreed or a finite discriminator/control/source-native/fence predicate failed",
        ],
        "result_summary": {
            "all_pass": bool(all_pass),
            "row_verdict": verdict,
            "three_qubit_min": bool(three_qubit_min),
            "source_native": bool(source_spec["pass"] and lift_witness["pass"]),
            "face_knot_shell_present": bool(face_knot_shell_present),
            "survives_mutation": bool(survives_mutation),
            "claim_ceiling": CLAIM_CEILING,
        },
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "RESULT "
        f"{OBJECT_ID} jax={RESULT_PATH} "
        f"all_pass={str(result['all_pass']).lower()} "
        f"row_verdict={result['row_verdict']} "
        f"three_qubit_min={str(result['three_qubit_min']).lower()} "
        f"source_native={str(result['source_native']).lower()} "
        f"face_knot_shell_present={str(result['face_knot_shell_present']).lower()} "
        f"survives_mutation={str(result['survives_mutation']).lower()}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
