#!/usr/bin/env python3
"""QIT spinor adapter seed for the Holodeck prediction-memory loop.

This ports the smallest Holodeck seed from semantic vectors to a finite
spinor/density carrier: project a spinor prediction, probe it through density
and lifted-path readouts, correct the model, and write survivor/graveyard
hashes. The density-only control is load-bearing because rho erases the lifted
path/sign witness.

Formal scout only. This does not admit a final Holodeck, FEP, QIT engine,
Axis0, gravity, cognition, consciousness, or physics claim.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "holodeck_qit_spinor_memory_adapter_seed_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
SOURCE_SEED_RESULT = RESULT_DIR / "holodeck_core_prediction_memory_seed_probe_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "holodeck_prediction_memory_qit_spinor_adapter_seed"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: ports the finite Holodeck prediction-memory seed onto "
    "JAX spinor states with density readouts, and tests a density-only control "
    "that erases lifted path/sign information. It is a QIT adapter seed, not "
    "final Holodeck, FEP, Axis0, gravity, cognition, consciousness, physics, "
    "or QIT-engine admission evidence."
)

FINITE_MAP = (
    "Q: (finite context graph, psi_i in C^2, rho_i=|psi_i><psi_i|, "
    "lifted path/sign probes, survivor hashes, graveyard hashes) -> corrected "
    "spinor model plus density/lifted recall record"
)
DOMAIN = {
    "contexts": "8 finite context cells in a ring graph",
    "carrier": "2-component complex spinor per context",
    "state_readout": "2x2 density rho = |psi><psi| per context",
    "probe_family": "density Frobenius error plus lifted interference/path-sign probe",
}
CODOMAIN_OR_OUTPUT = {
    "corrected_model": "finite context-indexed spinor states",
    "density_readouts": "finite 2x2 density matrices used for rho-side recall",
    "lifted_readouts": "path/sign-sensitive interference values not visible to rho alone",
    "survivor_hashes": "confirmed spinor/density/lift records",
    "graveyard_hashes": "killed prediction records",
}
ROOT_CONSTRAINTS_IN_FORCE = [
    "F01 finite context/probe/path/hash set",
    "N01 ordered project-sense-correct-update loop plus noncommuting X/Z probe channels",
]
BLOCKED_CONSUMERS = [
    "final_holodeck",
    "FEP_admission",
    "QIT_engine_admission",
    "Axis0",
    "Xi/Phi0",
    "gravity",
    "physics",
    "cognition",
    "consciousness",
]

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex spinor carrier, density readout, ordered channel controls, and finite QIT adapter metrics",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive survivor/graveyard semantic hash construction",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt serialization",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "hashlib": "supportive",
    "json": "supportive",
}

N_CONTEXTS = 8
N_CYCLES = 7
CORRECTION_GAIN = 0.46
DENSITY_GRAVEYARD_FLOOR = 0.16
LIFT_GRAVEYARD_FLOOR = 0.28
FALSE_ACCEPT_DENSITY_FLOOR = 0.94

COMPLEX = jnp.complex128
REAL = jnp.float64
I = jnp.array([[1.0, 0.0], [0.0, 1.0]], dtype=COMPLEX)
SX = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=COMPLEX)
SZ = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=COMPLEX)


def as_float(value: Any) -> float:
    return float(jax.device_get(value))


def normalize_spinor(psi: jax.Array) -> jax.Array:
    n = jnp.sqrt(jnp.maximum(jnp.real(jnp.vdot(psi, psi)), 1.0e-15))
    return psi / n


def phase(angle: float | jax.Array) -> jax.Array:
    return jnp.exp(1j * jnp.asarray(angle, dtype=REAL))


def su2_z(angle: float | jax.Array) -> jax.Array:
    a = jnp.asarray(angle, dtype=REAL) / 2.0
    return jnp.array([[jnp.exp(-1j * a), 0.0], [0.0, jnp.exp(1j * a)]], dtype=COMPLEX)


def su2_x(angle: float | jax.Array) -> jax.Array:
    a = jnp.asarray(angle, dtype=REAL) / 2.0
    return jnp.cos(a) * I - 1j * jnp.sin(a) * SX


def density(psi: jax.Array) -> jax.Array:
    psi = normalize_spinor(psi)
    return jnp.outer(psi, jnp.conjugate(psi))


def density_distance(a: jax.Array, b: jax.Array) -> jax.Array:
    diff = density(a) - density(b)
    return jnp.sqrt(jnp.maximum(jnp.real(jnp.trace(jnp.conjugate(diff.T) @ diff)), 0.0))


def density_similarity(a: jax.Array, b: jax.Array) -> jax.Array:
    return jnp.real(jnp.trace(density(a) @ density(b)))


def base_projective_spinor(context_id: int) -> jax.Array:
    theta = 0.43 + 0.19 * context_id
    phi = 0.31 * (context_id + 1)
    chi = -0.17 * context_id
    return normalize_spinor(
        jnp.array(
            [
                jnp.cos(theta / 2.0) * phase(phi),
                jnp.sin(theta / 2.0) * phase(phi + chi),
            ],
            dtype=COMPLEX,
        )
    )


def path_sign(context_id: int) -> float:
    return -1.0 if context_id in {1, 3, 6} else 1.0


def true_lifted_spinor(context_id: int) -> jax.Array:
    return path_sign(context_id) * base_projective_spinor(context_id)


def observation_spinor(context_id: int, cycle: int) -> jax.Array:
    drift = 0.035 * jnp.sin(0.7 * (cycle + 1) + 0.3 * context_id)
    return normalize_spinor(su2_z(drift) @ true_lifted_spinor(context_id))


def initial_model_spinor(context_id: int) -> jax.Array:
    psi = normalize_spinor(
        jnp.array(
            [
                jnp.cos(0.28 + 0.11 * context_id) * phase(0.15 * context_id),
                jnp.sin(0.28 + 0.11 * context_id) * phase(-0.22 * (context_id + 1)),
            ],
            dtype=COMPLEX,
        )
    )
    return normalize_spinor(su2_x(0.42) @ psi)


def canonical_projective_spinor(psi: jax.Array) -> jax.Array:
    psi = normalize_spinor(psi)
    return normalize_spinor(psi * jnp.exp(-1j * jnp.angle(psi[0])))


def init_model(*, density_only: bool) -> jax.Array:
    states = jnp.stack([initial_model_spinor(i) for i in range(N_CONTEXTS)])
    if density_only:
        states = jnp.stack([canonical_projective_spinor(states[i]) for i in range(N_CONTEXTS)])
    return states


def project_prediction(model: jax.Array, context_id: int, *, density_only: bool) -> jax.Array:
    left = model[(context_id - 1) % N_CONTEXTS]
    here = model[context_id]
    right = model[(context_id + 1) % N_CONTEXTS]
    psi = normalize_spinor(0.72 * here + 0.14 * left + 0.14 * right)
    return canonical_projective_spinor(psi) if density_only else psi


def blend_spinor(a: jax.Array, b: jax.Array, gain: float, *, density_only: bool) -> jax.Array:
    if density_only:
        a = canonical_projective_spinor(a)
        b = canonical_projective_spinor(b)
    psi = normalize_spinor((1.0 - gain) * a + gain * b)
    return canonical_projective_spinor(psi) if density_only else psi


def lifted_probe_value(psi: jax.Array, context_id: int) -> jax.Array:
    # This is a path/interference readout. The density rho is unchanged under
    # psi -> -psi, but this lifted value changes sign against the reference.
    return jnp.real(jnp.vdot(base_projective_spinor(context_id), normalize_spinor(psi)))


def lift_error(prediction: jax.Array, observation: jax.Array, context_id: int) -> jax.Array:
    return jnp.abs(lifted_probe_value(prediction, context_id) - lifted_probe_value(observation, context_id))


def channel_order_gap(psi: jax.Array) -> jax.Array:
    # N01 witness: X and Z rotations do not commute on the spinor/density state.
    a = su2_x(0.37) @ (su2_z(0.51) @ psi)
    b = su2_z(0.51) @ (su2_x(0.37) @ psi)
    return density_distance(a, b)


def vector_payload(psi: jax.Array) -> list[list[float]]:
    arr = jax.device_get(normalize_spinor(psi))
    return [[round(float(jnp.real(z)), 4), round(float(jnp.imag(z)), 4)] for z in arr]


def rho_payload(psi: jax.Array) -> list[list[list[float]]]:
    rho = jax.device_get(density(psi))
    out: list[list[list[float]]] = []
    for row in rho:
        out.append([[round(float(jnp.real(z)), 4), round(float(jnp.imag(z)), 4)] for z in row])
    return out


def semantic_hash(kind: str, context_id: int, psi: jax.Array, lift_value: float) -> str:
    payload = {
        "kind": kind,
        "context": context_id,
        "rho": rho_payload(psi),
        "lift": round(lift_value, 4),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:20]


def run_loop(*, update: bool, density_only: bool, shuffled_context: bool, write_graveyard: bool) -> dict[str, Any]:
    model = init_model(density_only=density_only)
    survivor_hashes: dict[str, dict[str, Any]] = {}
    graveyard_hashes: dict[str, dict[str, Any]] = {}
    killed_records: list[dict[str, Any]] = []
    trace: list[dict[str, float]] = []

    for cycle in range(N_CYCLES):
        for context_id in range(N_CONTEXTS):
            active_context = (context_id + 3) % N_CONTEXTS if shuffled_context else context_id
            prediction = project_prediction(model, active_context, density_only=density_only)
            observation = observation_spinor(context_id, cycle)
            if density_only:
                observation = canonical_projective_spinor(observation)
            rho_err_before = density_distance(prediction, observation)
            lift_err_before = lift_error(prediction, observation, context_id)
            if write_graveyard and (
                as_float(rho_err_before) > DENSITY_GRAVEYARD_FLOOR
                or as_float(lift_err_before) > LIFT_GRAVEYARD_FLOOR
            ):
                lift_value = as_float(lifted_probe_value(prediction, context_id))
                key = semantic_hash("graveyard", context_id, prediction, lift_value)
                graveyard_hashes[key] = {
                    "context_id": context_id,
                    "cycle": cycle,
                    "rho_error": as_float(rho_err_before),
                    "lift_error": as_float(lift_err_before),
                    "lift_value": lift_value,
                    "psi": vector_payload(prediction),
                }
                killed_records.append(
                    {
                        "context_id": context_id,
                        "rho_error": as_float(rho_err_before),
                        "lift_error": as_float(lift_err_before),
                        "lift_value": lift_value,
                        "psi": vector_payload(prediction),
                    }
                )

            if update:
                corrected = blend_spinor(model[active_context], observation, CORRECTION_GAIN, density_only=density_only)
                model = model.at[active_context].set(corrected)

            corrected_prediction = project_prediction(model, active_context, density_only=density_only)
            rho_err_after = density_distance(corrected_prediction, observation)
            lift_err_after = lift_error(corrected_prediction, observation, context_id)
            if as_float(rho_err_after) <= as_float(rho_err_before):
                lift_value = as_float(lifted_probe_value(corrected_prediction, context_id))
                key = semantic_hash("survivor", context_id, corrected_prediction, lift_value)
                survivor_hashes[key] = {
                    "context_id": context_id,
                    "cycle": cycle,
                    "rho_error": as_float(rho_err_after),
                    "lift_error": as_float(lift_err_after),
                    "lift_value": lift_value,
                    "psi": vector_payload(corrected_prediction),
                }
            trace.append(
                {
                    "cycle": float(cycle),
                    "context_id": float(context_id),
                    "rho_error_before": as_float(rho_err_before),
                    "rho_error_after": as_float(rho_err_after),
                    "lift_error_before": as_float(lift_err_before),
                    "lift_error_after": as_float(lift_err_after),
                }
            )

    return {
        "model": model,
        "survivor_hashes": survivor_hashes,
        "graveyard_hashes": graveyard_hashes,
        "killed_records": killed_records,
        "trace": trace,
    }


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def summarize_result(result: dict[str, Any], *, density_only: bool) -> dict[str, float]:
    trace = result["trace"]
    first = trace[:N_CONTEXTS]
    last = trace[-N_CONTEXTS:]
    model = result["model"]
    density_recall = mean(
        [as_float(density_similarity(project_prediction(model, i, density_only=density_only), true_lifted_spinor(i))) for i in range(N_CONTEXTS)]
    )
    lifted_alignment = mean(
        [as_float(lifted_probe_value(project_prediction(model, i, density_only=density_only), i) * path_sign(i)) for i in range(N_CONTEXTS)]
    )
    remote_path = [0, 1, 3, 6]
    current = project_prediction(model, remote_path[0], density_only=density_only)
    for context_id in remote_path[1:]:
        current = blend_spinor(current, project_prediction(model, context_id, density_only=density_only), 0.5, density_only=density_only)
    remote_lifted_alignment = as_float(lifted_probe_value(current, remote_path[-1]) * path_sign(remote_path[-1]))
    return {
        "first_cycle_density_error": mean([row["rho_error_before"] for row in first]),
        "last_cycle_density_error": mean([row["rho_error_after"] for row in last]),
        "first_cycle_lift_error": mean([row["lift_error_before"] for row in first]),
        "last_cycle_lift_error": mean([row["lift_error_after"] for row in last]),
        "density_recall_similarity": density_recall,
        "lifted_path_alignment": lifted_alignment,
        "remote_lifted_alignment": remote_lifted_alignment,
        "survivor_hash_count": float(len(result["survivor_hashes"])),
        "graveyard_hash_count": float(len(result["graveyard_hashes"])),
    }


def false_accept_rate(seed_result: dict[str, Any], *, use_graveyard: bool) -> float:
    survivors = list(seed_result["survivor_hashes"].values())
    graves = seed_result["graveyard_hashes"]
    killed = seed_result["killed_records"][:24]
    if not survivors or not killed:
        return 0.0
    false_accepts = 0
    for killed_row in killed:
        grave_key = hashlib.sha256(
            json.dumps(
                {
                    "kind": "graveyard",
                    "context": killed_row["context_id"],
                    "rho": rho_payload(jnp.array([complex(*z) for z in killed_row["psi"]], dtype=COMPLEX)),
                    "lift": round(killed_row["lift_value"], 4),
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()[:20]
        if use_graveyard and grave_key in graves:
            continue
        best_density = 0.0
        best_lift_gap = 999.0
        killed_psi = jnp.array([complex(*z) for z in killed_row["psi"]], dtype=COMPLEX)
        for survivor in survivors:
            survivor_psi = jnp.array([complex(*z) for z in survivor["psi"]], dtype=COMPLEX)
            best_density = max(best_density, as_float(density_similarity(killed_psi, survivor_psi)))
            best_lift_gap = min(best_lift_gap, abs(killed_row["lift_value"] - survivor["lift_value"]))
        if best_density >= FALSE_ACCEPT_DENSITY_FLOOR and best_lift_gap <= 0.12:
            false_accepts += 1
    return false_accepts / len(killed)


def load_source_seed_status() -> dict[str, Any]:
    if not SOURCE_SEED_RESULT.exists():
        return {"exists": False, "path": str(SOURCE_SEED_RESULT)}
    data = json.loads(SOURCE_SEED_RESULT.read_text(encoding="utf-8"))
    return {
        "exists": True,
        "path": str(SOURCE_SEED_RESULT),
        "all_pass": data.get("all_pass"),
        "candidate_status": data.get("candidate_status"),
        "promotion_allowed": data.get("promotion_allowed"),
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    live = run_loop(update=True, density_only=False, shuffled_context=False, write_graveyard=True)
    frozen = run_loop(update=False, density_only=False, shuffled_context=False, write_graveyard=True)
    density_only = run_loop(update=True, density_only=True, shuffled_context=False, write_graveyard=True)
    shuffled = run_loop(update=True, density_only=False, shuffled_context=True, write_graveyard=True)
    no_graveyard = run_loop(update=True, density_only=False, shuffled_context=False, write_graveyard=False)

    live_m = summarize_result(live, density_only=False)
    frozen_m = summarize_result(frozen, density_only=False)
    density_only_m = summarize_result(density_only, density_only=True)
    shuffled_m = summarize_result(shuffled, density_only=False)
    no_graveyard_m = summarize_result(no_graveyard, density_only=False)

    density_error_reduction = live_m["first_cycle_density_error"] - live_m["last_cycle_density_error"]
    frozen_density_reduction = frozen_m["first_cycle_density_error"] - frozen_m["last_cycle_density_error"]
    lift_error_reduction = live_m["first_cycle_lift_error"] - live_m["last_cycle_lift_error"]
    order_gaps = [as_float(channel_order_gap(true_lifted_spinor(i))) for i in range(N_CONTEXTS)]

    positive = {
        "qit_prediction_first_density_error_reduction": {
            "pass": density_error_reduction > 0.28 and density_error_reduction > frozen_density_reduction + 0.20,
            "live_density_reduction": density_error_reduction,
            "frozen_density_reduction": frozen_density_reduction,
        },
        "qit_prediction_first_lift_error_reduction": {
            "pass": lift_error_reduction > 0.25,
            "live_lift_reduction": lift_error_reduction,
        },
        "density_recall_survives_qit_adapter": {
            "pass": live_m["density_recall_similarity"] > 0.83,
            "live_density_recall_similarity": live_m["density_recall_similarity"],
        },
        "lifted_path_beats_density_only_control": {
            "pass": live_m["lifted_path_alignment"] > density_only_m["lifted_path_alignment"] + 0.22,
            "live_lifted_path_alignment": live_m["lifted_path_alignment"],
            "density_only_lifted_path_alignment": density_only_m["lifted_path_alignment"],
        },
        "context_geometry_is_load_bearing": {
            "pass": live_m["lifted_path_alignment"] > shuffled_m["lifted_path_alignment"] + 0.35,
            "live_lifted_path_alignment": live_m["lifted_path_alignment"],
            "shuffled_lifted_path_alignment": shuffled_m["lifted_path_alignment"],
            "live_remote_lifted_alignment": live_m["remote_lifted_alignment"],
            "shuffled_remote_lifted_alignment": shuffled_m["remote_lifted_alignment"],
        },
        "n01_order_gap_present": {
            "pass": min(order_gaps) > 1.0e-3,
            "min_channel_order_gap": min(order_gaps),
            "max_channel_order_gap": max(order_gaps),
        },
    }

    graveyard_companions = {
        "survivor_hashes_exist": {
            "pass": live_m["survivor_hash_count"] >= N_CONTEXTS * (N_CYCLES - 1),
            "count": live_m["survivor_hash_count"],
            "minimum_required": N_CONTEXTS * (N_CYCLES - 1),
        },
        "graveyard_hashes_exist": {
            "pass": live_m["graveyard_hash_count"] >= N_CONTEXTS,
            "count": live_m["graveyard_hash_count"],
        },
        "graveyard_suppresses_false_confirmation": {
            "pass": false_accept_rate(live, use_graveyard=True) < false_accept_rate(live, use_graveyard=False),
            "with_graveyard": false_accept_rate(live, use_graveyard=True),
            "same_killed_set_without_graveyard": false_accept_rate(live, use_graveyard=False),
        },
        "frozen_model_control_fails": {
            "pass": frozen_m["density_recall_similarity"] < live_m["density_recall_similarity"] - 0.12,
            "frozen_density_recall_similarity": frozen_m["density_recall_similarity"],
            "live_density_recall_similarity": live_m["density_recall_similarity"],
        },
        "density_only_control_keeps_density_but_loses_lift": {
            "pass": density_only_m["density_recall_similarity"] > 0.82
            and density_only_m["lifted_path_alignment"] < live_m["lifted_path_alignment"] - 0.22,
            "density_only_density_recall_similarity": density_only_m["density_recall_similarity"],
            "density_only_lifted_path_alignment": density_only_m["lifted_path_alignment"],
            "live_lifted_path_alignment": live_m["lifted_path_alignment"],
        },
    }

    boundary = {
        "promotion_allowed_false": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "formal_admission_allowed_false": {
            "pass": FORMAL_ADMISSION_ALLOWED is False,
            "value": FORMAL_ADMISSION_ALLOWED,
        },
        "finite_contexts": {
            "pass": N_CONTEXTS == 8 and N_CYCLES == 7,
            "contexts": N_CONTEXTS,
            "cycles": N_CYCLES,
        },
        "source_classical_seed_present": load_source_seed_status(),
        "blocked_consumers_preserved": {"pass": len(BLOCKED_CONSUMERS) >= 8, "blocked_consumers": BLOCKED_CONSUMERS},
    }
    boundary["source_classical_seed_present"]["pass"] = (
        boundary["source_classical_seed_present"].get("exists") is True
        and boundary["source_classical_seed_present"].get("all_pass") is True
    )

    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": classification,
        "CLASSIFICATION": CLASSIFICATION,
        "SIM_EXECUTION_KIND": SIM_EXECUTION_KIND,
        "SOURCE_ALIGNMENT_CATEGORY": SOURCE_ALIGNMENT_CATEGORY,
        "PROMOTION_ALLOWED": PROMOTION_ALLOWED,
        "promotion_allowed": PROMOTION_ALLOWED,
        "FORMAL_ADMISSION_ALLOWED": FORMAL_ADMISSION_ALLOWED,
        "CLAIM_CEILING": CLAIM_CEILING,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN_OR_OUTPUT,
        "root_constraints_in_force": ROOT_CONSTRAINTS_IN_FORCE,
        "carrier_layer": "finite 2-component spinor cells with density readout",
        "geometry_layer": "ring-context adapter only; no Hopf/tori/manifold admission",
        "carrier_realization": "JAX complex128 psi in C^2, rho=|psi><psi|",
        "peps3d_embedding": "not admitted here; single-cell spinor adapter fixture blocks PEPS3D/manifold consumers",
        "spinor_state": "explicit JAX psi per context",
        "quaternion_action": "not_applicable in this adapter seed",
        "dependency_receipts": [str(SOURCE_SEED_RESULT)],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "candidate_status": "qit_spinor_adapter_seed_survived_controls" if all_pass else "qit_spinor_adapter_seed_open_or_failed",
        "candidate_survived": all_pass,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "metrics": {
            "live_spinor": live_m,
            "frozen_spinor_control": frozen_m,
            "density_only_control": density_only_m,
            "shuffled_context_control": shuffled_m,
            "no_graveyard_control": no_graveyard_m,
            "channel_order_gaps": order_gaps,
        },
        "nearby_variants": {
            "tested_here": [
                "frozen_model_no_update",
                "density_only_projective_control",
                "shuffled_context_geometry",
                "drop_graveyard",
                "ordered_XZ_vs_ZX_channel_gap",
            ],
            "not_tested_here": [
                "canonical QIT engine replay schedule",
                "PEPS3D spinor-network carrier",
                "projector/camera hardware loop",
                "Axis0 fuzz-field coupling",
                "Xi/Phi0 cut construction",
            ],
        },
        "recommended_next_gates": [
            "replace the ring-context adapter with canonical QIT replay stage records",
            "add a Julia parity mirror for the same spinor/density/lift metrics",
            "move from single spinor cells to a finite spinor-network carrier with explicit PEPS3D block",
        ],
        "runtime_seconds": time.time() - started,
        "result_path": str(OUT_PATH),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "candidate_status": result["candidate_status"], "result_path": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
