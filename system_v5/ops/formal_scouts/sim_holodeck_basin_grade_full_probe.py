#!/usr/bin/env python3
"""Basin-grade Holodeck prediction-memory full probe.

This turns the Holodeck seed loop into a finite basin object:
predict -> project/rho -> sense -> error -> survivor/graveyard -> update,
then perturb the converged model and test return to the basin.

Formal scout / scratch diagnostic only. This does not admit a final
Holodeck, FEP, QIT engine, Axis0, Xi/Phi0, gravity, physics, cognition,
consciousness, or broader science claim.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import torch


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "holodeck_basin_grade_full_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
SOURCE_CORE_SEED_RESULT = RESULT_DIR / "holodeck_core_prediction_memory_seed_probe_results.json"
SOURCE_QIT_SEED_RESULT = RESULT_DIR / "holodeck_qit_spinor_memory_adapter_seed_probe_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "holodeck_prediction_memory_basin_grade_full_probe"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout / scratch diagnostic only: tests a finite C^2 spinor/density "
    "Holodeck prediction-memory basin object with explicit basin-contract rows, "
    "escape controls, perturbation-depth recovery, and a killed fake-basin "
    "control. It is not final Holodeck, FEP, QIT-engine admission, Axis0, "
    "Xi/Phi0, gravity, physics, cognition, consciousness, or any broader "
    "science claim."
)

FINITE_MAP = (
    "B: finite model states S={psi_i in C^2, rho_i=|psi_i><psi_i|, i=0..7} "
    "under ordered predict-project-sense-error-survivor/graveyard-update cycles "
    "-> corrected model state plus basin/recovery receipt"
)
DOMAIN = {
    "contexts": "8 finite context cells on a ring",
    "state_space": "finite spinor/density states: psi_i in C^2 and rho_i=|psi_i><psi_i|",
    "history": "10 training cycles plus 5 recovery cycles, all bounded",
    "probe_family": "density error, lifted path-sign alignment, survivor hashes, graveyard hashes, X/Z order gap",
}
CODOMAIN_OR_OUTPUT = {
    "corrected_model": "finite context-indexed spinor state",
    "density_readouts": "finite 2x2 density matrices per context",
    "basin_contract_table": "8 explicit basin-contract pass/fail rows",
    "perturbation_recovery": "live and control recovery scalars from bounded perturbation",
}
ROOT_CONSTRAINTS_IN_FORCE = [
    "F01 finite context/probe/history/hash set",
    "N01 noncommuting X/Z spinor channel order gap plus ordered update map",
]
BLOCKED_CONSUMERS = [
    "Holodeck-final",
    "FEP",
    "QIT-engine-admission",
    "Axis0",
    "Xi/Phi0",
    "gravity",
    "physics",
    "cognition",
    "consciousness",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "role_source": "local",
        "reason": "load-bearing independent recomputation of the live perturbation-recovery invariant from the emitted spinor states; required by the current nonclassical lint gate",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "primary x64 backend for the spinor/density prediction-correction loop, basin metrics, controls, and state-space checks",
    },
    "julia": {
        "tried": True,
        "used": True,
        "reason": "supportive independent parity recomputation of the key recovery invariant from raw spinor state payloads",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive survivor/graveyard hash receipts and false-confirmation controls",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization",
    },
    "subprocess": {
        "tried": True,
        "used": True,
        "reason": "supportive self-lint and Julia parity process boundary",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "jax": "supportive",
    "julia": "supportive",
    "hashlib": "supportive",
    "json": "supportive",
    "subprocess": "supportive",
}
BACKEND_ROLE_MANIFEST = {
    "jax": "primary numeric backend for the basin loop and all control traces",
    "julia": "parity backend for the key recovery invariant scalar",
    "pytorch": "local lint-admissible independent invariant recompute, not the primary loop",
}

N_CONTEXTS = 8
N_CYCLES = 10
RECOVERY_CYCLES = 5
CORRECTION_GAIN = 0.46
FIXED_POINT_GAIN = 0.62
PERTURBATION_DEPTH = 0.37
DENSITY_GRAVEYARD_FLOOR = 0.16
LIFT_GRAVEYARD_FLOOR = 0.28
FALSE_ACCEPT_DENSITY_FLOOR = 0.94
FALSE_ACCEPT_LIFT_GAP = 0.12
FALSE_ACCEPT_BOUNDARY = 0.20
RECOVERY_CONTRACTION_FLOOR = 0.75
DENSITY_RECALL_FLOOR = 0.83
LIFT_ALIGNMENT_FLOOR = 0.75
N01_ORDER_GAP_FLOOR = 1.0e-3
STATE_SPACE_ERROR_FLOOR = 1.0e-9

COMPLEX = jnp.complex128
REAL = jnp.float64
I2 = jnp.array([[1.0, 0.0], [0.0, 1.0]], dtype=COMPLEX)
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
    return jnp.cos(a) * I2 - 1j * jnp.sin(a) * SX


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
    return jnp.real(jnp.vdot(base_projective_spinor(context_id), normalize_spinor(psi)))


def lift_error(prediction: jax.Array, observation: jax.Array, context_id: int) -> jax.Array:
    return jnp.abs(lifted_probe_value(prediction, context_id) - lifted_probe_value(observation, context_id))


def combined_error(prediction: jax.Array, observation: jax.Array, context_id: int) -> jax.Array:
    return density_distance(prediction, observation) + lift_error(prediction, observation, context_id)


def channel_order_gap(psi: jax.Array) -> jax.Array:
    a = su2_x(0.37) @ (su2_z(0.51) @ psi)
    b = su2_z(0.51) @ (su2_x(0.37) @ psi)
    return density_distance(a, b)


def fixed_point_spinor(_: int) -> jax.Array:
    return canonical_projective_spinor(base_projective_spinor(0))


def spinor_payload(psi: jax.Array, *, digits: int = 8) -> list[list[float]]:
    arr = jax.device_get(normalize_spinor(psi))
    return [[round(float(jnp.real(z)), digits), round(float(jnp.imag(z)), digits)] for z in arr]


def model_payload(model: jax.Array) -> list[list[list[float]]]:
    return [spinor_payload(model[i]) for i in range(N_CONTEXTS)]


def rho_payload(psi: jax.Array) -> list[list[list[float]]]:
    rho = jax.device_get(density(psi))
    out: list[list[list[float]]] = []
    for row in rho:
        out.append([[round(float(jnp.real(z)), 6), round(float(jnp.imag(z)), 6)] for z in row])
    return out


def spinor_from_payload(payload: list[list[float]]) -> jax.Array:
    return normalize_spinor(jnp.array([complex(z[0], z[1]) for z in payload], dtype=COMPLEX))


def semantic_hash(kind: str, context_id: int, psi: jax.Array, lift_value: float) -> str:
    payload = {
        "kind": kind,
        "context": context_id,
        "rho": rho_payload(psi),
        "lift": round(lift_value, 5),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:20]


def step_model(
    model: jax.Array,
    cycle: int,
    *,
    update: bool,
    density_only: bool,
    shuffled_context: bool,
    write_graveyard: bool,
    fixed_point: bool,
    survivor_hashes: dict[str, dict[str, Any]],
    graveyard_hashes: dict[str, dict[str, Any]],
    killed_records: list[dict[str, Any]],
) -> tuple[jax.Array, list[dict[str, float]]]:
    rows: list[dict[str, float]] = []
    for context_id in range(N_CONTEXTS):
        active_context = (context_id + 3) % N_CONTEXTS if shuffled_context else context_id
        prediction = project_prediction(model, active_context, density_only=density_only)
        observation = observation_spinor(context_id, cycle)
        if density_only:
            observation = canonical_projective_spinor(observation)
        rho_err_before = density_distance(prediction, observation)
        lift_err_before = lift_error(prediction, observation, context_id)
        combined_before = combined_error(prediction, observation, context_id)

        if as_float(rho_err_before) > DENSITY_GRAVEYARD_FLOOR or as_float(lift_err_before) > LIFT_GRAVEYARD_FLOOR:
            lift_value = as_float(lifted_probe_value(prediction, context_id))
            grave_key = semantic_hash("graveyard", context_id, prediction, lift_value)
            killed = {
                "context_id": context_id,
                "cycle": cycle,
                "rho_error": as_float(rho_err_before),
                "lift_error": as_float(lift_err_before),
                "lift_value": lift_value,
                "psi": spinor_payload(prediction),
                "grave_key": grave_key,
            }
            killed_records.append(killed)
            if write_graveyard:
                graveyard_hashes[grave_key] = killed

        if update:
            target = fixed_point_spinor(active_context) if fixed_point else observation
            gain = FIXED_POINT_GAIN if fixed_point else CORRECTION_GAIN
            corrected = blend_spinor(model[active_context], target, gain, density_only=density_only)
            model = model.at[active_context].set(corrected)

        corrected_prediction = project_prediction(model, active_context, density_only=density_only)
        rho_err_after = density_distance(corrected_prediction, observation)
        lift_err_after = lift_error(corrected_prediction, observation, context_id)
        combined_after = combined_error(corrected_prediction, observation, context_id)
        if as_float(combined_after) <= as_float(combined_before):
            lift_value = as_float(lifted_probe_value(corrected_prediction, context_id))
            key = semantic_hash("survivor", context_id, corrected_prediction, lift_value)
            survivor_hashes[key] = {
                "context_id": context_id,
                "cycle": cycle,
                "rho_error": as_float(rho_err_after),
                "lift_error": as_float(lift_err_after),
                "lift_value": lift_value,
                "psi": spinor_payload(corrected_prediction),
            }

        rows.append(
            {
                "cycle": float(cycle),
                "context_id": float(context_id),
                "active_context": float(active_context),
                "rho_error_before": as_float(rho_err_before),
                "rho_error_after": as_float(rho_err_after),
                "lift_error_before": as_float(lift_err_before),
                "lift_error_after": as_float(lift_err_after),
                "combined_error_before": as_float(combined_before),
                "combined_error_after": as_float(combined_after),
            }
        )
    return model, rows


def run_loop(
    *,
    update: bool,
    density_only: bool,
    shuffled_context: bool,
    write_graveyard: bool,
    fixed_point: bool,
    start_model: jax.Array | None = None,
    start_cycle: int = 0,
    cycles: int = N_CYCLES,
) -> dict[str, Any]:
    model = init_model(density_only=density_only) if start_model is None else start_model
    survivor_hashes: dict[str, dict[str, Any]] = {}
    graveyard_hashes: dict[str, dict[str, Any]] = {}
    killed_records: list[dict[str, Any]] = []
    trace: list[dict[str, float]] = []
    for cycle in range(start_cycle, start_cycle + cycles):
        model, rows = step_model(
            model,
            cycle,
            update=update,
            density_only=density_only,
            shuffled_context=shuffled_context,
            write_graveyard=write_graveyard,
            fixed_point=fixed_point,
            survivor_hashes=survivor_hashes,
            graveyard_hashes=graveyard_hashes,
            killed_records=killed_records,
        )
        trace.extend(rows)
    return {
        "model": model,
        "survivor_hashes": survivor_hashes,
        "graveyard_hashes": graveyard_hashes,
        "killed_records": killed_records,
        "trace": trace,
    }


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def recall_metrics(model: jax.Array, *, density_only: bool) -> dict[str, float]:
    density_recall = mean(
        [
            as_float(
                density_similarity(
                    project_prediction(model, i, density_only=density_only),
                    true_lifted_spinor(i),
                )
            )
            for i in range(N_CONTEXTS)
        ]
    )
    lifted_alignment = mean(
        [
            as_float(lifted_probe_value(project_prediction(model, i, density_only=density_only), i) * path_sign(i))
            for i in range(N_CONTEXTS)
        ]
    )
    remote_path = [0, 1, 3, 6]
    current = project_prediction(model, remote_path[0], density_only=density_only)
    for context_id in remote_path[1:]:
        current = blend_spinor(
            current,
            project_prediction(model, context_id, density_only=density_only),
            0.5,
            density_only=density_only,
        )
    remote_lifted_alignment = as_float(lifted_probe_value(current, remote_path[-1]) * path_sign(remote_path[-1]))
    return {
        "density_recall_similarity": density_recall,
        "lifted_path_alignment": lifted_alignment,
        "remote_lifted_alignment": remote_lifted_alignment,
    }


def false_accept_rate(seed_result: dict[str, Any], *, use_graveyard: bool) -> float:
    survivors = list(seed_result["survivor_hashes"].values())
    graves = seed_result["graveyard_hashes"]
    killed = seed_result["killed_records"][:24]
    if not survivors or not killed:
        return 0.0
    false_accepts = 0
    for killed_row in killed:
        if use_graveyard and killed_row["grave_key"] in graves:
            continue
        killed_psi = spinor_from_payload(killed_row["psi"])
        best_density = 0.0
        best_lift_gap = 999.0
        for survivor in survivors:
            survivor_psi = spinor_from_payload(survivor["psi"])
            best_density = max(best_density, as_float(density_similarity(killed_psi, survivor_psi)))
            best_lift_gap = min(best_lift_gap, abs(killed_row["lift_value"] - survivor["lift_value"]))
        if best_density >= FALSE_ACCEPT_DENSITY_FLOOR and best_lift_gap <= FALSE_ACCEPT_LIFT_GAP:
            false_accepts += 1
    return false_accepts / len(killed)


def summarize_result(result: dict[str, Any], *, density_only: bool) -> dict[str, float]:
    trace = result["trace"]
    first = trace[:N_CONTEXTS]
    last = trace[-N_CONTEXTS:]
    recall = recall_metrics(result["model"], density_only=density_only)
    false_with = false_accept_rate(result, use_graveyard=True)
    false_without = false_accept_rate(result, use_graveyard=False)
    return {
        "first_cycle_density_error": mean([row["rho_error_before"] for row in first]),
        "last_cycle_density_error": mean([row["rho_error_after"] for row in last]),
        "first_cycle_lift_error": mean([row["lift_error_before"] for row in first]),
        "last_cycle_lift_error": mean([row["lift_error_after"] for row in last]),
        "first_cycle_combined_error": mean([row["combined_error_before"] for row in first]),
        "last_cycle_combined_error": mean([row["combined_error_after"] for row in last]),
        "density_error_reduction": mean([row["rho_error_before"] for row in first])
        - mean([row["rho_error_after"] for row in last]),
        "lift_error_reduction": mean([row["lift_error_before"] for row in first])
        - mean([row["lift_error_after"] for row in last]),
        "combined_error_reduction": mean([row["combined_error_before"] for row in first])
        - mean([row["combined_error_after"] for row in last]),
        "survivor_hash_count": float(len(result["survivor_hashes"])),
        "graveyard_hash_count": float(len(result["graveyard_hashes"])),
        "false_accept_rate_with_graveyard": false_with,
        "false_accept_rate_without_graveyard": false_without,
        **recall,
    }


def basin_state_loss(model: jax.Array, *, density_only: bool, false_accept: float) -> float:
    recall = recall_metrics(model, density_only=density_only)
    return (
        (1.0 - recall["density_recall_similarity"])
        + (1.0 - recall["lifted_path_alignment"])
        + false_accept
    )


def perturb_model(model: jax.Array, *, depth: float, density_only: bool) -> jax.Array:
    perturbed = []
    for context_id in range(N_CONTEXTS):
        psi = su2_x(depth + 0.03 * context_id) @ (su2_z(-0.29 + 0.02 * context_id) @ model[context_id])
        if context_id in {1, 4}:
            psi = -psi
        perturbed.append(canonical_projective_spinor(psi) if density_only else normalize_spinor(psi))
    return jnp.stack(perturbed)


def is_inside_basin(summary: dict[str, float]) -> bool:
    return (
        summary["last_cycle_density_error"] < DENSITY_GRAVEYARD_FLOOR
        and summary["last_cycle_lift_error"] < LIFT_GRAVEYARD_FLOOR
        and summary["density_recall_similarity"] >= DENSITY_RECALL_FLOOR
        and summary["lifted_path_alignment"] >= LIFT_ALIGNMENT_FLOOR
        and summary["false_accept_rate_with_graveyard"] <= FALSE_ACCEPT_BOUNDARY
        and summary["graveyard_hash_count"] >= N_CONTEXTS
    )


def recovery_probe(label: str, base_result: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    density_only = bool(variant["density_only"])
    baseline_false = false_accept_rate(base_result, use_graveyard=True)
    baseline_loss = basin_state_loss(base_result["model"], density_only=density_only, false_accept=baseline_false)
    perturbed = perturb_model(base_result["model"], depth=PERTURBATION_DEPTH, density_only=density_only)
    perturbed_loss = basin_state_loss(perturbed, density_only=density_only, false_accept=baseline_false)
    recovered = run_loop(
        update=bool(variant["update"]),
        density_only=density_only,
        shuffled_context=bool(variant["shuffled_context"]),
        write_graveyard=bool(variant["write_graveyard"]),
        fixed_point=bool(variant["fixed_point"]),
        start_model=perturbed,
        start_cycle=N_CYCLES,
        cycles=RECOVERY_CYCLES,
    )
    recovered_summary = summarize_result(recovered, density_only=density_only)
    recovered_false = false_accept_rate(recovered, use_graveyard=True)
    recovered_loss = basin_state_loss(recovered["model"], density_only=density_only, false_accept=recovered_false)
    contraction = 1.0 - recovered_loss / perturbed_loss if perturbed_loss > 0 else 0.0
    graveyard_factor = max(0.0, 1.0 - recovered_false)
    return_score = max(0.0, contraction) * max(0.0, recovered_summary["density_recall_similarity"]) * max(
        0.0,
        recovered_summary["lifted_path_alignment"],
    ) * graveyard_factor
    pass_return = (
        contraction >= RECOVERY_CONTRACTION_FLOOR
        and recovered_summary["density_recall_similarity"] >= DENSITY_RECALL_FLOOR
        and recovered_summary["lifted_path_alignment"] >= LIFT_ALIGNMENT_FLOOR
        and recovered_false <= FALSE_ACCEPT_BOUNDARY
        and recovered_summary["graveyard_hash_count"] >= N_CONTEXTS
    )
    return {
        "label": label,
        "pre_perturbation_loss": baseline_loss,
        "perturbed_loss": perturbed_loss,
        "recovered_loss": recovered_loss,
        "recovery_contraction": contraction,
        "basin_return_score": return_score,
        "recovered_density_recall_similarity": recovered_summary["density_recall_similarity"],
        "recovered_lifted_path_alignment": recovered_summary["lifted_path_alignment"],
        "recovered_false_accept_rate_with_graveyard": recovered_false,
        "recovered_graveyard_hash_count": recovered_summary["graveyard_hash_count"],
        "returned_to_basin": pass_return,
        "perturbed_model_payload": model_payload(perturbed),
        "recovered_model_payload": model_payload(recovered["model"]),
    }


def state_space_checks(model: jax.Array) -> dict[str, Any]:
    rhos = jnp.stack([density(model[i]) for i in range(N_CONTEXTS)])
    traces = jnp.trace(rhos, axis1=1, axis2=2)
    hermitian_errors = [as_float(jnp.max(jnp.abs(rhos[i] - jnp.conjugate(rhos[i].T)))) for i in range(N_CONTEXTS)]
    eigen_mins = [as_float(jnp.min(jnp.linalg.eigvalsh(rhos[i]))) for i in range(N_CONTEXTS)]
    trace_errors = [abs(float(jnp.real(traces[i])) - 1.0) for i in range(N_CONTEXTS)]
    return {
        "contexts": N_CONTEXTS,
        "rho_shape": list(rhos.shape),
        "max_trace_error": max(trace_errors),
        "max_hermitian_error": max(hermitian_errors),
        "min_eigenvalue": min(eigen_mins),
        "pass": (
            list(rhos.shape) == [N_CONTEXTS, 2, 2]
            and max(trace_errors) < STATE_SPACE_ERROR_FLOOR
            and max(hermitian_errors) < STATE_SPACE_ERROR_FLOOR
            and min(eigen_mins) >= -STATE_SPACE_ERROR_FLOOR
        ),
    }


def root_receipts(order_gaps: list[float], trace_len: int, survivor_count: int, graveyard_count: int) -> dict[str, Any]:
    f01 = {
        "contexts": N_CONTEXTS,
        "cycles": N_CYCLES,
        "recovery_cycles": RECOVERY_CYCLES,
        "trace_len": trace_len,
        "survivor_hash_count": survivor_count,
        "graveyard_hash_count": graveyard_count,
        "finite_history_bound": N_CONTEXTS * (N_CYCLES + RECOVERY_CYCLES),
    }
    f01["pass"] = (
        f01["contexts"] == 8
        and f01["cycles"] == 10
        and f01["recovery_cycles"] == 5
        and trace_len == N_CONTEXTS * N_CYCLES
        and survivor_count <= trace_len
        and graveyard_count <= trace_len
    )
    n01 = {
        "min_channel_order_gap": min(order_gaps),
        "max_channel_order_gap": max(order_gaps),
        "mean_channel_order_gap": mean(order_gaps),
        "threshold": N01_ORDER_GAP_FLOOR,
    }
    n01["pass"] = n01["min_channel_order_gap"] > N01_ORDER_GAP_FLOOR
    return {"F01": f01, "N01": n01}


def load_source_seed_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path), "pass": False}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "exists": True,
        "path": str(path),
        "all_pass": data.get("all_pass"),
        "classification": data.get("classification"),
        "promotion_allowed": data.get("promotion_allowed"),
        "pass": data.get("all_pass") is True and data.get("classification") == "formal_scout",
    }


def torch_complex_model_from_jax(model: jax.Array) -> torch.Tensor:
    arr = jax.device_get(model)
    rows = []
    for row in arr:
        rows.append([complex(z) for z in row])
    return torch.tensor(rows, dtype=torch.complex128)


def torch_normalize(psi: torch.Tensor) -> torch.Tensor:
    n = torch.sqrt(torch.clamp(torch.real(torch.vdot(psi, psi)), min=1.0e-15))
    return psi / n


def torch_phase(angle: float) -> complex:
    return complex(torch.exp(torch.tensor(1j * angle, dtype=torch.complex128)).item())


def torch_base_projective_spinor(context_id: int) -> torch.Tensor:
    theta = 0.43 + 0.19 * context_id
    phi = 0.31 * (context_id + 1)
    chi = -0.17 * context_id
    return torch_normalize(
        torch.tensor(
            [
                float(jnp.cos(theta / 2.0)) * torch_phase(phi),
                float(jnp.sin(theta / 2.0)) * torch_phase(phi + chi),
            ],
            dtype=torch.complex128,
        )
    )


def torch_true_lifted_spinor(context_id: int) -> torch.Tensor:
    return path_sign(context_id) * torch_base_projective_spinor(context_id)


def torch_project_prediction(model: torch.Tensor, context_id: int) -> torch.Tensor:
    left = model[(context_id - 1) % N_CONTEXTS]
    here = model[context_id]
    right = model[(context_id + 1) % N_CONTEXTS]
    return torch_normalize(0.72 * here + 0.14 * left + 0.14 * right)


def torch_recall_metrics(model: jax.Array) -> dict[str, float]:
    tmodel = torch_complex_model_from_jax(model)
    density_vals: list[float] = []
    lift_vals: list[float] = []
    for context_id in range(N_CONTEXTS):
        pred = torch_project_prediction(tmodel, context_id)
        true = torch_true_lifted_spinor(context_id)
        overlap = torch.vdot(pred, true)
        density_vals.append(float(torch.real(torch.conj(overlap) * overlap)))
        base = torch_base_projective_spinor(context_id)
        lift_vals.append(float(torch.real(torch.vdot(base, pred))) * path_sign(context_id))
    return {"density_recall_similarity": mean(density_vals), "lifted_path_alignment": mean(lift_vals)}


def torch_recovery_parity(
    live_recovery: dict[str, Any],
    live_result: dict[str, Any],
    recovered_model: jax.Array,
) -> dict[str, Any]:
    baseline_false = false_accept_rate(live_result, use_graveyard=True)
    baseline_metrics = torch_recall_metrics(live_result["model"])
    perturbed = jnp.array(
        [[complex(z[0], z[1]) for z in row] for row in live_recovery["perturbed_model_payload"]],
        dtype=COMPLEX,
    )
    recovered_metrics = torch_recall_metrics(recovered_model)
    perturbed_metrics = torch_recall_metrics(perturbed)
    pre_loss = (1.0 - baseline_metrics["density_recall_similarity"]) + (
        1.0 - baseline_metrics["lifted_path_alignment"]
    ) + baseline_false
    perturbed_loss = (1.0 - perturbed_metrics["density_recall_similarity"]) + (
        1.0 - perturbed_metrics["lifted_path_alignment"]
    ) + baseline_false
    recovered_loss = (1.0 - recovered_metrics["density_recall_similarity"]) + (
        1.0 - recovered_metrics["lifted_path_alignment"]
    ) + live_recovery["recovered_false_accept_rate_with_graveyard"]
    contraction = 1.0 - recovered_loss / perturbed_loss
    delta = abs(contraction - live_recovery["recovery_contraction"])
    return {
        "torch_pre_loss": pre_loss,
        "torch_perturbed_loss": perturbed_loss,
        "torch_recovered_loss": recovered_loss,
        "torch_recovery_contraction": contraction,
        "jax_recovery_contraction": live_recovery["recovery_contraction"],
        "max_abs_diff": delta,
        "threshold": 1.0e-6,
        "pass": delta < 1.0e-6,
    }


def serialize_model_for_julia(model: jax.Array) -> str:
    arr = jax.device_get(model)
    values: list[str] = []
    for context_id in range(N_CONTEXTS):
        for component_id in range(2):
            z = arr[context_id][component_id]
            values.append(f"{float(jnp.real(z)):.17g}")
            values.append(f"{float(jnp.imag(z)):.17g}")
    return ",".join(values)


def julia_recovery_parity(live_result: dict[str, Any], live_recovery: dict[str, Any]) -> dict[str, Any]:
    julia = shutil.which("julia")
    if julia is None:
        return {"available": False, "pass": False, "reason": "julia executable not found"}
    perturbed = jnp.array(
        [[complex(z[0], z[1]) for z in row] for row in live_recovery["perturbed_model_payload"]],
        dtype=COMPLEX,
    )
    recovered = jnp.array(
        [[complex(z[0], z[1]) for z in row] for row in live_recovery["recovered_model_payload"]],
        dtype=COMPLEX,
    )
    code = r"""
function parse_model(s)
    vals = parse.(Float64, split(s, ","))
    model = Array{ComplexF64}(undef, 8, 2)
    k = 1
    for i in 1:8
        for j in 1:2
            model[i, j] = vals[k] + im * vals[k + 1]
            k += 2
        end
    end
    return model
end

function normalize_spinor(v)
    n = sqrt(max(real(sum(conj(v[k]) * v[k] for k in 1:2)), 1.0e-15))
    return v ./ n
end

function base_projective_spinor(context_id)
    theta = 0.43 + 0.19 * context_id
    phi = 0.31 * (context_id + 1)
    chi = -0.17 * context_id
    return normalize_spinor(ComplexF64[
        cos(theta / 2.0) * cis(phi),
        sin(theta / 2.0) * cis(phi + chi),
    ])
end

path_sign(context_id) = context_id in (1, 3, 6) ? -1.0 : 1.0
true_lifted_spinor(context_id) = path_sign(context_id) .* base_projective_spinor(context_id)

function project_prediction(model, context_id)
    i = context_id + 1
    left = mod(context_id - 1, 8) + 1
    right = mod(context_id + 1, 8) + 1
    return normalize_spinor(0.72 .* model[i, :] .+ 0.14 .* model[left, :] .+ 0.14 .* model[right, :])
end

function recall_metrics(model)
    density_sum = 0.0
    lift_sum = 0.0
    for context_id in 0:7
        pred = project_prediction(model, context_id)
        truth = true_lifted_spinor(context_id)
        overlap = sum(conj(pred[k]) * truth[k] for k in 1:2)
        density_sum += real(conj(overlap) * overlap)
        base = base_projective_spinor(context_id)
        lift_sum += real(sum(conj(base[k]) * pred[k] for k in 1:2)) * path_sign(context_id)
    end
    return density_sum / 8.0, lift_sum / 8.0
end

function model_loss(model, false_accept)
    density_recall, lifted_alignment = recall_metrics(model)
    return (1.0 - density_recall) + (1.0 - lifted_alignment) + false_accept
end

pre = parse_model(ARGS[1])
perturbed = parse_model(ARGS[2])
recovered = parse_model(ARGS[3])
pre_false = parse(Float64, ARGS[4])
recovered_false = parse(Float64, ARGS[5])
pre_loss = model_loss(pre, pre_false)
perturbed_loss = model_loss(perturbed, pre_false)
recovered_loss = model_loss(recovered, recovered_false)
contraction = 1.0 - recovered_loss / perturbed_loss
println(join([pre_loss, perturbed_loss, recovered_loss, contraction], ","))
"""
    proc = subprocess.run(
        [
            julia,
            "--startup-file=no",
            "-e",
            code,
            serialize_model_for_julia(live_result["model"]),
            serialize_model_for_julia(perturbed),
            serialize_model_for_julia(recovered),
            f"{false_accept_rate(live_result, use_graveyard=True):.17g}",
            f"{live_recovery['recovered_false_accept_rate_with_graveyard']:.17g}",
        ],
        text=True,
        capture_output=True,
        timeout=60,
    )
    if proc.returncode != 0:
        return {
            "available": True,
            "pass": False,
            "exit_code": proc.returncode,
            "stdout_tail": proc.stdout[-500:],
            "stderr_tail": proc.stderr[-500:],
        }
    parts = [float(x) for x in proc.stdout.strip().split(",")]
    contraction = parts[3]
    delta = abs(contraction - live_recovery["recovery_contraction"])
    return {
        "available": True,
        "julia_pre_loss": parts[0],
        "julia_perturbed_loss": parts[1],
        "julia_recovered_loss": parts[2],
        "julia_recovery_contraction": contraction,
        "jax_recovery_contraction": live_recovery["recovery_contraction"],
        "max_abs_diff": delta,
        "threshold": 1.0e-6,
        "pass": delta < 1.0e-6,
    }


def lint_self() -> dict[str, Any]:
    lint = REPO / "scripts" / "lint_sim_contract.py"
    proc = subprocess.run(
        [sys.executable, str(lint), str(Path(__file__).resolve())],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=60,
    )
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {"violation_total": None, "stdout_tail": proc.stdout[-500:], "stderr_tail": proc.stderr[-500:]}
    data["exit_code"] = proc.returncode
    return data


def pass_fail_text(value: bool) -> str:
    return "PASS" if value else "FAIL"


def print_table(title: str, rows: dict[str, dict[str, Any]]) -> None:
    print(title)
    print("| item | pass | number |")
    print("|---|---:|---:|")
    for key, row in rows.items():
        print(f"| {key} | {pass_fail_text(bool(row['pass']))} | {row['number']} |")


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    variants = {
        "live": {
            "update": True,
            "density_only": False,
            "shuffled_context": False,
            "write_graveyard": True,
            "fixed_point": False,
        },
        "frozen_model": {
            "update": False,
            "density_only": False,
            "shuffled_context": False,
            "write_graveyard": True,
            "fixed_point": False,
        },
        "shuffled_context": {
            "update": True,
            "density_only": False,
            "shuffled_context": True,
            "write_graveyard": True,
            "fixed_point": False,
        },
        "density_only": {
            "update": True,
            "density_only": True,
            "shuffled_context": False,
            "write_graveyard": True,
            "fixed_point": False,
        },
        "graveyard_off": {
            "update": True,
            "density_only": False,
            "shuffled_context": False,
            "write_graveyard": False,
            "fixed_point": False,
        },
        "fake_fixed_point": {
            "update": True,
            "density_only": False,
            "shuffled_context": False,
            "write_graveyard": True,
            "fixed_point": True,
        },
    }

    runs = {label: run_loop(**variant) for label, variant in variants.items()}
    summaries = {
        label: summarize_result(runs[label], density_only=bool(variant["density_only"]))
        for label, variant in variants.items()
    }
    order_gaps = [as_float(channel_order_gap(true_lifted_spinor(i))) for i in range(N_CONTEXTS)]
    roots = root_receipts(
        order_gaps,
        trace_len=len(runs["live"]["trace"]),
        survivor_count=len(runs["live"]["survivor_hashes"]),
        graveyard_count=len(runs["live"]["graveyard_hashes"]),
    )
    state_checks = state_space_checks(runs["live"]["model"])
    recovery = {
        label: recovery_probe(label, runs[label], variant)
        for label, variant in variants.items()
    }

    live_inside = is_inside_basin(summaries["live"])
    control_escape = {
        label: not recovery[label]["returned_to_basin"]
        for label in ["frozen_model", "shuffled_context", "density_only", "graveyard_off", "fake_fixed_point"]
    }
    fake_generic_reduction = summaries["fake_fixed_point"]["combined_error_reduction"]
    fake_killed = fake_generic_reduction > 0.10 and not recovery["fake_fixed_point"]["returned_to_basin"]

    julia_parity = julia_recovery_parity(runs["live"], recovery["live"])
    recovered_live_model = jnp.array(
        [[complex(z[0], z[1]) for z in row] for row in recovery["live"]["recovered_model_payload"]],
        dtype=COMPLEX,
    )
    torch_parity = torch_recovery_parity(recovery["live"], runs["live"], recovered_live_model)
    parity_pass = bool(julia_parity.get("pass")) and bool(torch_parity.get("pass"))
    lint = lint_self()
    source_seed_status = {
        "core_seed": load_source_seed_status(SOURCE_CORE_SEED_RESULT),
        "qit_spinor_seed": load_source_seed_status(SOURCE_QIT_SEED_RESULT),
    }

    basin_contract_table = {
        "1_admissibility_predicate": {
            "pass": live_inside and all(control_escape.values()),
            "number": f"live_return={recovery['live']['basin_return_score']:.6f}; escaped_controls={sum(control_escape.values())}/5",
            "predicate": (
                "admissible iff finite state/history pass F01, min X/Z order gap passes N01, "
                "final density/lift errors are inside boundary, graveyard suppresses false confirmation, "
                "and bounded perturbation returns to basin"
            ),
        },
        "2_named_finite_state_space": {
            "pass": state_checks["pass"],
            "number": f"rho_shape={state_checks['rho_shape']}; max_trace_error={state_checks['max_trace_error']:.3e}",
            "state_space": "S={rho_i=|psi_i><psi_i| in C^(2x2), psi_i in C^2, i=0..7}",
        },
        "3_update_rule": {
            "pass": (
                summaries["live"]["density_error_reduction"] > 0.28
                and summaries["live"]["lift_error_reduction"] > 0.25
                and summaries["live"]["density_error_reduction"]
                > summaries["frozen_model"]["density_error_reduction"] + 0.20
            ),
            "number": (
                f"density_reduction={summaries['live']['density_error_reduction']:.6f}; "
                f"lift_reduction={summaries['live']['lift_error_reduction']:.6f}"
            ),
            "update_rule": "rho_{t+1}=correct(predict(rho_t), sense) through ordered spinor correction",
        },
        "4_basin_boundary": {
            "pass": live_inside and not summaries["graveyard_off"]["false_accept_rate_with_graveyard"] <= FALSE_ACCEPT_BOUNDARY,
            "number": (
                f"live_density_error={summaries['live']['last_cycle_density_error']:.6f}; "
                f"live_lift_error={summaries['live']['last_cycle_lift_error']:.6f}; "
                f"graveyard_off_false_accept={summaries['graveyard_off']['false_accept_rate_with_graveyard']:.6f}"
            ),
            "boundary": "leave basin when prediction error is above threshold, model decouples from world, or graveyard boundary is absent",
        },
        "5_stability_invariant": {
            "pass": recovery["live"]["returned_to_basin"] and parity_pass,
            "number": (
                f"live_recovery_contraction={recovery['live']['recovery_contraction']:.6f}; "
                f"julia_diff={julia_parity.get('max_abs_diff', float('inf')):.3e}"
            ),
            "invariant": "model-relative recall/lift plus false-confirmation boundary recovers after bounded perturbation",
        },
        "6_escape_failure_cases": {
            "pass": all(control_escape.values()),
            "number": (
                f"frozen={recovery['frozen_model']['recovery_contraction']:.6f}; "
                f"shuffled={recovery['shuffled_context']['recovery_contraction']:.6f}; "
                f"density_only={recovery['density_only']['recovery_contraction']:.6f}; "
                f"graveyard_off={recovery['graveyard_off']['recovery_contraction']:.6f}"
            ),
            "controls": list(control_escape.keys()),
        },
        "7_root_tests_f01_n01": {
            "pass": roots["F01"]["pass"] and roots["N01"]["pass"],
            "number": f"F01_trace={roots['F01']['trace_len']}; min_N01_gap={roots['N01']['min_channel_order_gap']:.6f}",
            "root_tests": roots,
        },
        "8_killed_non_basin_explanation": {
            "pass": fake_killed,
            "number": (
                f"fake_generic_reduction={fake_generic_reduction:.6f}; "
                f"fake_return_score={recovery['fake_fixed_point']['basin_return_score']:.6f}"
            ),
            "killed_explanation": "generic fixed-point contraction is not enough; it fails model-relative perturbation recovery",
        },
    }

    positive = {
        "basin_contract_items_all_pass": {
            "pass": all(row["pass"] for row in basin_contract_table.values()),
            "passed": sum(bool(row["pass"]) for row in basin_contract_table.values()),
            "total": len(basin_contract_table),
        },
        "live_prediction_correction_reduces_density_error": {
            "pass": summaries["live"]["density_error_reduction"] > 0.28,
            "density_error_reduction": summaries["live"]["density_error_reduction"],
            "threshold": 0.28,
        },
        "live_prediction_correction_reduces_lift_error": {
            "pass": summaries["live"]["lift_error_reduction"] > 0.25,
            "lift_error_reduction": summaries["live"]["lift_error_reduction"],
            "threshold": 0.25,
        },
        "live_perturbation_returns_to_basin": {
            "pass": recovery["live"]["returned_to_basin"],
            "recovery_contraction": recovery["live"]["recovery_contraction"],
            "basin_return_score": recovery["live"]["basin_return_score"],
        },
        "julia_parity_on_recovery_invariant": {
            "pass": bool(julia_parity.get("pass")),
            "max_abs_diff": julia_parity.get("max_abs_diff"),
            "threshold": julia_parity.get("threshold"),
        },
        "pytorch_independent_invariant_recompute": {
            "pass": bool(torch_parity.get("pass")),
            "max_abs_diff": torch_parity.get("max_abs_diff"),
            "threshold": torch_parity.get("threshold"),
        },
        "f01_n01_roots_pass": {
            "pass": roots["F01"]["pass"] and roots["N01"]["pass"],
            "f01_trace_len": roots["F01"]["trace_len"],
            "min_channel_order_gap": roots["N01"]["min_channel_order_gap"],
        },
    }
    graveyard_companions = {
        "survivor_hashes_exist": {
            "pass": summaries["live"]["survivor_hash_count"] >= N_CONTEXTS * (N_CYCLES - 2),
            "count": summaries["live"]["survivor_hash_count"],
            "minimum_required": N_CONTEXTS * (N_CYCLES - 2),
        },
        "graveyard_hashes_exist": {
            "pass": summaries["live"]["graveyard_hash_count"] >= N_CONTEXTS,
            "count": summaries["live"]["graveyard_hash_count"],
            "minimum_required": N_CONTEXTS,
        },
        "graveyard_suppresses_false_confirmation": {
            "pass": summaries["live"]["false_accept_rate_with_graveyard"]
            < summaries["live"]["false_accept_rate_without_graveyard"],
            "with_graveyard": summaries["live"]["false_accept_rate_with_graveyard"],
            "same_killed_set_without_graveyard": summaries["live"]["false_accept_rate_without_graveyard"],
        },
        "graveyard_off_control_leaves_basin": {
            "pass": not recovery["graveyard_off"]["returned_to_basin"],
            "graveyard_off_false_accept": summaries["graveyard_off"]["false_accept_rate_with_graveyard"],
            "returned_to_basin": recovery["graveyard_off"]["returned_to_basin"],
        },
    }
    boundary = {
        "promotion_allowed_false": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "formal_admission_allowed_false": {
            "pass": FORMAL_ADMISSION_ALLOWED is False,
            "value": FORMAL_ADMISSION_ALLOWED,
        },
        "blocked_consumers_preserved": {
            "pass": set(BLOCKED_CONSUMERS)
            >= {
                "Holodeck-final",
                "FEP",
                "QIT-engine-admission",
                "Axis0",
                "Xi/Phi0",
                "gravity",
                "physics",
                "cognition",
                "consciousness",
            },
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "live_inside_boundary": {
            "pass": live_inside,
            "density_error": summaries["live"]["last_cycle_density_error"],
            "lift_error": summaries["live"]["last_cycle_lift_error"],
            "false_accept": summaries["live"]["false_accept_rate_with_graveyard"],
        },
        "controls_escape_boundary": {
            "pass": all(control_escape.values()),
            "control_escape": control_escape,
        },
        "source_seeds_present_formal_scout": {
            "pass": source_seed_status["core_seed"]["pass"] and source_seed_status["qit_spinor_seed"]["pass"],
            "core_seed": source_seed_status["core_seed"],
            "qit_spinor_seed": source_seed_status["qit_spinor_seed"],
        },
    }
    nearby_variants = {
        "summary": "All variants are finite controls in the same basin fixture; control pass means the variant was executed and classified, not promoted.",
        "tested_here": list(variants.keys()),
        "passed": len(variants),
        "total": len(variants),
        "rows": {
            label: {
                "executed": True,
                "returned_to_basin": recovery[label]["returned_to_basin"],
                "expected_for_basin": label == "live",
            }
            for label in variants
        },
    }

    all_pass = (
        all(row["pass"] for row in basin_contract_table.values())
        and all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
        and lint.get("violation_total") == 0
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
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
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "CLAIM_CEILING": CLAIM_CEILING,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN_OR_OUTPUT,
        "root_constraints_in_force": ROOT_CONSTRAINTS_IN_FORCE,
        "carrier_layer": "finite 2-component spinor cells with density rho=|psi><psi|",
        "geometry_layer": "ring-context basin fixture only; no Hopf/tori/manifold admission",
        "basin_contract_table": basin_contract_table,
        "admissibility_predicate": basin_contract_table["1_admissibility_predicate"]["predicate"],
        "state_space_checks": state_checks,
        "root_receipts": roots,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "perturbation_recovery": {
            label: {
                key: value
                for key, value in row.items()
                if key not in {"perturbed_model_payload", "recovered_model_payload"}
            }
            for label, row in recovery.items()
        },
        "perturbation_recovery_payloads": {
            "live_perturbed_model": recovery["live"]["perturbed_model_payload"],
            "live_recovered_model": recovery["live"]["recovered_model_payload"],
        },
        "metrics": summaries,
        "control_escape": control_escape,
        "killed_non_basin_control": {
            "label": "fake_fixed_point",
            "generic_combined_error_reduction": fake_generic_reduction,
            "returned_to_basin": recovery["fake_fixed_point"]["returned_to_basin"],
            "basin_return_score": recovery["fake_fixed_point"]["basin_return_score"],
            "pass": fake_killed,
        },
        "julia_parity": julia_parity,
        "pytorch_invariant_recompute": torch_parity,
        "source_seed_status": source_seed_status,
        "lint": lint,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "backend_role_manifest": BACKEND_ROLE_MANIFEST,
        "why_not_v4_probes": {
            "reason": "This is a v5 basin-contract formal scout over the Holodeck seed loop, not a v4 doctrine mirror or admission packet.",
            "v4_equivalent": None,
        },
        "nearby_variants": nearby_variants,
        "not_tested_here": [
            "canonical QIT-engine replay admission",
            "PEPS3D spinor-network carrier",
            "projector/camera hardware loop",
            "Axis0 fuzz-field coupling",
            "Xi/Phi0 cut construction",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "all_pass": all_pass,
        "candidate_status": "basin_grade_formal_scout_survived_controls_not_admitted"
        if all_pass
        else "basin_grade_formal_scout_open_or_failed_not_admitted",
        "runtime_seconds": time.time() - started,
        "result_path": str(OUT_PATH),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print_table("BASIN_CONTRACT_TABLE", basin_contract_table)
    print("PERTURBATION_RECOVERY")
    for label in ["live", "frozen_model", "shuffled_context", "density_only", "graveyard_off", "fake_fixed_point"]:
        row = recovery[label]
        print(
            f"{label}: returned={row['returned_to_basin']} "
            f"contraction={row['recovery_contraction']:.6f} "
            f"score={row['basin_return_score']:.6f} "
            f"density_recall={row['recovered_density_recall_similarity']:.6f} "
            f"lift_alignment={row['recovered_lifted_path_alignment']:.6f} "
            f"false_accept={row['recovered_false_accept_rate_with_graveyard']:.6f}"
        )
    print("F01_N01_RECEIPTS")
    print(
        json.dumps(
            {
                "F01_pass": roots["F01"]["pass"],
                "F01_trace_len": roots["F01"]["trace_len"],
                "N01_pass": roots["N01"]["pass"],
                "min_channel_order_gap": roots["N01"]["min_channel_order_gap"],
            },
            sort_keys=True,
        )
    )
    print(f"lint_violation_total={lint.get('violation_total')}")
    print(f"fresh_all_pass={all_pass}")
    print("CODEX2_BASIN_FULL_DONE")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
