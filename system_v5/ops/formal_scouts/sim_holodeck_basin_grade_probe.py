#!/usr/bin/env python3
"""Holodeck basin-grade scratch diagnostic probe.

This checks whether the existing Holodeck seed shape satisfies the basin claim
contract on a finite C^2 spinor/density carrier: explicit state space, update
rule, perturbation-depth boundary, recovery/contraction invariant, escape
controls, F01/N01 receipts, and a killed fake-basin control.

Formal scout / scratch diagnostic only. This does not admit a final Holodeck,
FEP, QIT engine, Axis0, Xi/Phi0, gravity, physics, cognition, consciousness,
or manifold claim.
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
import torch


ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "holodeck_basin_grade_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
SOURCE_SEED_RESULTS = [
    RESULT_DIR / "holodeck_core_prediction_memory_seed_probe_results.json",
    RESULT_DIR / "holodeck_qit_spinor_memory_adapter_seed_probe_results.json",
]

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "holodeck_basin_grade_scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SCRATCH_DIAGNOSTIC_ONLY = True
CLAIM_CEILING = (
    "Formal scout / scratch diagnostic only: tests a finite C^2 spinor/density "
    "prediction-correction loop against the basin claim contract. It is not "
    "final Holodeck, FEP, QIT-engine, Axis0, Xi/Phi0, gravity, physics, "
    "cognition, consciousness, or manifold admission evidence."
)

FINITE_MAP = (
    "B: (finite context index i, spinor psi_i in C^2, density rho_i=|psi_i><psi_i|, "
    "ordered X/Z probe channels, perturbation depth d, survivor/graveyard hashes) "
    "-> corrected spinor model plus basin-boundary and recovery receipts"
)
DOMAIN = {
    "contexts": "8 finite ring-context cells",
    "carrier": "one normalized 2-component complex spinor psi_i per context",
    "density_readout": "2x2 density rho_i = |psi_i><psi_i|",
    "perturbation_depths": "9 explicit bounded depths from 0.00 to 0.42",
    "controls": "live, frozen, shuffled-context, density-only, graveyard-off, fake fixed attractor",
}
CODOMAIN_OR_OUTPUT = {
    "corrected_model": "finite context-indexed spinor states",
    "basin_boundary": "max recovered perturbation depth under error threshold",
    "stability_invariant": "error contraction/recovery under bounded perturbation",
    "root_receipts": "F01 finite counts and N01 X/Z order gap",
    "contract_rows": "8 basin-contract rows with pass booleans and numeric receipts",
}
ROOT_CONSTRAINTS_IN_FORCE = [
    "F01 finite contexts, spinor cells, density matrices, perturbation depths, controls, and hash records",
    "N01 ordered project-sense-correct update plus noncommuting X/Z channel order gap",
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
    "manifold_claim",
]

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "primary x64 complex spinor/density computation, update dynamics, perturbation-boundary metrics, and N01 order-gap measurement",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent recomputation of the X/Z order-gap invariant and final density-state purity for the local nonclassical lint boundary",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive survivor/graveyard semantic hash construction for killed prediction records",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic result serialization",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "pytorch": "load_bearing",
    "hashlib": "supportive",
    "json": "supportive",
}

N_CONTEXTS = 8
STATE_DIM = 2
N_CYCLES = 9
RECOVERY_STEPS = 3
CORRECTION_GAIN = 0.54
LOCAL_RECOVERY_ERROR_THRESHOLD = 0.18
LOCAL_ENTRY_ERROR_THRESHOLD = 0.24
SURVIVOR_ERROR_THRESHOLD = 0.20
FALSE_ACCEPT_DENSITY_FLOOR = 0.93
FALSE_ACCEPT_LIFT_GAP = 0.14
PERTURBATION_DEPTHS = (0.00, 0.03, 0.06, 0.09, 0.12, 0.16, 0.22, 0.30, 0.42)

COMPLEX = jnp.complex128
REAL = jnp.float64
I2 = jnp.array([[1.0, 0.0], [0.0, 1.0]], dtype=COMPLEX)
SX = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=COMPLEX)
SZ = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=COMPLEX)


def as_float(value: Any) -> float:
    return float(jax.device_get(value))


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


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


def density_trace_purity(psi: jax.Array) -> tuple[float, float]:
    rho = density(psi)
    trace = jnp.real(jnp.trace(rho))
    purity = jnp.real(jnp.trace(rho @ rho))
    return as_float(trace), as_float(purity)


def base_projective_spinor(context_id: int) -> jax.Array:
    theta = 0.44 + 0.18 * context_id
    phi = 0.29 * (context_id + 1)
    chi = -0.21 * context_id + 0.07 * jnp.sin(context_id + 1)
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
    z_drift = 0.032 * jnp.sin(0.71 * (cycle + 1) + 0.19 * context_id)
    x_drift = 0.017 * jnp.cos(0.43 * (cycle + 2) - 0.13 * context_id)
    return normalize_spinor(su2_x(x_drift) @ (su2_z(z_drift) @ true_lifted_spinor(context_id)))


def initial_model_spinor(context_id: int) -> jax.Array:
    psi = normalize_spinor(
        jnp.array(
            [
                jnp.cos(0.25 + 0.10 * context_id) * phase(0.13 * context_id + 0.19),
                jnp.sin(0.25 + 0.10 * context_id) * phase(-0.25 * (context_id + 1)),
            ],
            dtype=COMPLEX,
        )
    )
    return normalize_spinor(su2_x(0.48) @ (su2_z(-0.31) @ psi))


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
    psi = normalize_spinor(0.78 * here + 0.11 * left + 0.11 * right)
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
    return 0.70 * density_distance(prediction, observation) + 0.30 * lift_error(prediction, observation, context_id)


def channel_order_gap(psi: jax.Array) -> jax.Array:
    x_then_z = su2_z(0.51) @ (su2_x(0.37) @ psi)
    z_then_x = su2_x(0.37) @ (su2_z(0.51) @ psi)
    return density_distance(x_then_z, z_then_x)


def spinor_payload(psi: jax.Array) -> list[list[float]]:
    values = []
    for z in normalize_spinor(psi):
        values.append([round(as_float(jnp.real(z)), 6), round(as_float(jnp.imag(z)), 6)])
    return values


def rho_payload(psi: jax.Array) -> list[list[list[float]]]:
    out: list[list[list[float]]] = []
    for row in density(psi):
        out_row: list[list[float]] = []
        for z in row:
            out_row.append([round(as_float(jnp.real(z)), 6), round(as_float(jnp.imag(z)), 6)])
        out.append(out_row)
    return out


def semantic_hash(kind: str, context_id: int, psi: jax.Array, lift_value: float) -> str:
    payload = {
        "kind": kind,
        "context_id": context_id,
        "rho": rho_payload(psi),
        "lift_value": round(lift_value, 5),
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


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

            rho_before = density_distance(prediction, observation)
            lift_before = lift_error(prediction, observation, context_id)
            error_before = 0.70 * rho_before + 0.30 * lift_before
            lift_value_before = as_float(lifted_probe_value(prediction, context_id))
            grave_key = semantic_hash("graveyard", context_id, prediction, lift_value_before)
            killed_row = {
                "context_id": context_id,
                "cycle": cycle,
                "rho_error": as_float(rho_before),
                "lift_error": as_float(lift_before),
                "combined_error": as_float(error_before),
                "lift_value": lift_value_before,
                "psi": spinor_payload(prediction),
                "graveyard_key": grave_key,
            }
            if as_float(error_before) > SURVIVOR_ERROR_THRESHOLD:
                killed_records.append(killed_row)
                if write_graveyard:
                    graveyard_hashes[grave_key] = killed_row

            if update:
                corrected = blend_spinor(model[active_context], observation, CORRECTION_GAIN, density_only=density_only)
                model = model.at[active_context].set(corrected)

            corrected_prediction = project_prediction(model, active_context, density_only=density_only)
            rho_after = density_distance(corrected_prediction, observation)
            lift_after = lift_error(corrected_prediction, observation, context_id)
            error_after = 0.70 * rho_after + 0.30 * lift_after
            if as_float(error_after) <= as_float(error_before):
                lift_value_after = as_float(lifted_probe_value(corrected_prediction, context_id))
                survivor_key = semantic_hash("survivor", context_id, corrected_prediction, lift_value_after)
                survivor_hashes[survivor_key] = {
                    "context_id": context_id,
                    "cycle": cycle,
                    "rho_error": as_float(rho_after),
                    "lift_error": as_float(lift_after),
                    "combined_error": as_float(error_after),
                    "lift_value": lift_value_after,
                    "psi": spinor_payload(corrected_prediction),
                }

            trace.append(
                {
                    "cycle": float(cycle),
                    "context_id": float(context_id),
                    "rho_error_before": as_float(rho_before),
                    "rho_error_after": as_float(rho_after),
                    "lift_error_before": as_float(lift_before),
                    "lift_error_after": as_float(lift_after),
                    "combined_error_before": as_float(error_before),
                    "combined_error_after": as_float(error_after),
                }
            )

    return {
        "model": model,
        "survivor_hashes": survivor_hashes,
        "graveyard_hashes": graveyard_hashes,
        "killed_records": killed_records,
        "trace": trace,
    }


def spinor_from_payload(payload: list[list[float]]) -> jax.Array:
    return normalize_spinor(jnp.array([complex(row[0], row[1]) for row in payload], dtype=COMPLEX))


def false_accept_rate(loop_result: dict[str, Any], *, use_graveyard: bool) -> float:
    survivors = list(loop_result["survivor_hashes"].values())
    killed = loop_result["killed_records"][:32]
    graves = loop_result["graveyard_hashes"]
    if not survivors or not killed:
        return 0.0
    false_accepts = 0
    for killed_row in killed:
        if use_graveyard and killed_row["graveyard_key"] in graves:
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


def summarize_loop(loop_result: dict[str, Any], *, density_only: bool) -> dict[str, float]:
    trace = loop_result["trace"]
    first = trace[:N_CONTEXTS]
    last = trace[-N_CONTEXTS:]
    model = loop_result["model"]
    density_recall = mean(
        [
            as_float(density_similarity(project_prediction(model, i, density_only=density_only), true_lifted_spinor(i)))
            for i in range(N_CONTEXTS)
        ]
    )
    lifted_alignment = mean(
        [
            as_float(lifted_probe_value(project_prediction(model, i, density_only=density_only), i) * path_sign(i))
            for i in range(N_CONTEXTS)
        ]
    )
    model_relative_recall = 0.55 * density_recall + 0.45 * ((lifted_alignment + 1.0) / 2.0)
    before_values = [row["combined_error_before"] for row in trace]
    after_values = [row["combined_error_after"] for row in trace]
    contraction_ratios = [
        row["combined_error_after"] / max(row["combined_error_before"], 1.0e-12)
        for row in trace
    ]
    return {
        "first_cycle_combined_error": mean([row["combined_error_before"] for row in first]),
        "last_cycle_combined_error": mean([row["combined_error_after"] for row in last]),
        "mean_combined_error_before": mean(before_values),
        "mean_combined_error_after": mean(after_values),
        "mean_contraction_ratio": mean(contraction_ratios),
        "density_recall_similarity": density_recall,
        "lifted_path_alignment": lifted_alignment,
        "model_relative_recall": model_relative_recall,
        "survivor_hash_count": float(len(loop_result["survivor_hashes"])),
        "graveyard_hash_count": float(len(loop_result["graveyard_hashes"])),
        "false_accept_rate_with_graveyard": false_accept_rate(loop_result, use_graveyard=True),
        "false_accept_rate_without_graveyard": false_accept_rate(loop_result, use_graveyard=False),
    }


def perturb_spinor(psi: jax.Array, depth: float, context_id: int) -> jax.Array:
    local = su2_x(depth * (1.0 + 0.07 * context_id)) @ (su2_z(-0.83 * depth) @ psi)
    if depth <= 0.22:
        return normalize_spinor(local)
    transplant = true_lifted_spinor((context_id + 3) % N_CONTEXTS)
    mix = min(0.86, (depth - 0.22) / 0.20)
    return normalize_spinor((1.0 - mix) * local + mix * transplant)


def mean_model_error(model: jax.Array, *, density_only: bool, cycle: int) -> float:
    return mean(
        [
            as_float(combined_error(project_prediction(model, i, density_only=density_only), observation_spinor(i, cycle), i))
            for i in range(N_CONTEXTS)
        ]
    )


def recovery_probe(model: jax.Array, depth: float) -> dict[str, float | bool]:
    perturbed = jnp.stack([perturb_spinor(model[i], depth, i) for i in range(N_CONTEXTS)])
    initial_error = mean_model_error(perturbed, density_only=False, cycle=N_CYCLES)
    recovered = perturbed
    for step in range(RECOVERY_STEPS):
        for context_id in range(N_CONTEXTS):
            observation = observation_spinor(context_id, N_CYCLES + step)
            corrected = blend_spinor(recovered[context_id], observation, CORRECTION_GAIN, density_only=False)
            recovered = recovered.at[context_id].set(corrected)
    final_error = mean_model_error(recovered, density_only=False, cycle=N_CYCLES + RECOVERY_STEPS)
    contraction_ratio = final_error / max(initial_error, 1.0e-12)
    local_entry = initial_error <= LOCAL_ENTRY_ERROR_THRESHOLD
    contracts_or_already_stable = contraction_ratio < 0.82 or initial_error <= LOCAL_RECOVERY_ERROR_THRESHOLD
    recovered_in_basin = (
        local_entry
        and final_error <= LOCAL_RECOVERY_ERROR_THRESHOLD
        and contracts_or_already_stable
    )
    return {
        "depth": depth,
        "initial_error": initial_error,
        "final_error": final_error,
        "contraction_ratio": contraction_ratio,
        "local_entry_error_threshold": LOCAL_ENTRY_ERROR_THRESHOLD,
        "local_entry": local_entry,
        "recovered_in_basin": recovered_in_basin,
    }


def basin_boundary_scan(model: jax.Array) -> dict[str, Any]:
    rows = [recovery_probe(model, depth) for depth in PERTURBATION_DEPTHS]
    admitted_depths = [float(row["depth"]) for row in rows if row["recovered_in_basin"]]
    escaped_depths = [float(row["depth"]) for row in rows if not row["recovered_in_basin"]]
    return {
        "rows": rows,
        "max_recovered_depth": max(admitted_depths) if admitted_depths else 0.0,
        "first_escape_depth": min(escaped_depths) if escaped_depths else None,
        "local_threshold": LOCAL_RECOVERY_ERROR_THRESHOLD,
        "local_entry_error_threshold": LOCAL_ENTRY_ERROR_THRESHOLD,
        "has_nontrivial_recovery_region": bool(admitted_depths and max(admitted_depths) >= 0.12),
        "has_escape_region": bool(escaped_depths and min(escaped_depths) > 0.0),
    }


def fake_fixed_attractor_control() -> dict[str, float | bool]:
    fixed = true_lifted_spinor(0)
    fixed_model = jnp.stack([fixed for _ in range(N_CONTEXTS)])
    perturbed = jnp.stack([perturb_spinor(fixed_model[i], 0.16, i) for i in range(N_CONTEXTS)])
    collapsed = fixed_model
    initial_error_to_fixed = mean(
        [
            as_float(combined_error(perturbed[i], fixed, i))
            for i in range(N_CONTEXTS)
        ]
    )
    final_error_to_fixed = mean(
        [
            as_float(combined_error(collapsed[i], fixed, i))
            for i in range(N_CONTEXTS)
        ]
    )
    contraction_ratio = final_error_to_fixed / max(initial_error_to_fixed, 1.0e-12)
    final_truth_error = mean_model_error(collapsed, density_only=False, cycle=N_CYCLES + 1)
    density_recall = mean(
        [
            as_float(density_similarity(project_prediction(collapsed, i, density_only=False), true_lifted_spinor(i)))
            for i in range(N_CONTEXTS)
        ]
    )
    lifted_alignment = mean(
        [
            as_float(lifted_probe_value(project_prediction(collapsed, i, density_only=False), i) * path_sign(i))
            for i in range(N_CONTEXTS)
        ]
    )
    model_relative_recall = 0.55 * density_recall + 0.45 * ((lifted_alignment + 1.0) / 2.0)
    return {
        "fake_contraction_ratio": contraction_ratio,
        "fake_initial_error_to_fixed": initial_error_to_fixed,
        "fake_final_error_to_fixed": final_error_to_fixed,
        "fake_final_truth_error": final_truth_error,
        "fake_density_recall_similarity": density_recall,
        "fake_lifted_path_alignment": lifted_alignment,
        "fake_model_relative_recall": model_relative_recall,
        "trivial_contraction_present": contraction_ratio < 0.85,
    }


def source_seed_status() -> list[dict[str, Any]]:
    out = []
    for path in SOURCE_SEED_RESULTS:
        if not path.exists():
            out.append({"path": str(path), "exists": False, "all_pass": None, "candidate_status": None})
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        out.append(
            {
                "path": str(path),
                "exists": True,
                "all_pass": data.get("all_pass"),
                "candidate_status": data.get("candidate_status"),
                "promotion_allowed": data.get("promotion_allowed"),
                "formal_admission_allowed": data.get("FORMAL_ADMISSION_ALLOWED")
                or data.get("formal_admission_allowed"),
            }
        )
    return out


def finite_count_receipts() -> dict[str, Any]:
    density_entry_count = N_CONTEXTS * STATE_DIM * STATE_DIM
    update_trace_count = N_CONTEXTS * N_CYCLES
    controls_count = 6
    return {
        "contexts": N_CONTEXTS,
        "spinor_components_per_state": STATE_DIM,
        "density_entries_total": density_entry_count,
        "update_trace_count": update_trace_count,
        "perturbation_depth_count": len(PERTURBATION_DEPTHS),
        "control_count": controls_count,
        "finite_count_total": N_CONTEXTS + density_entry_count + update_trace_count + len(PERTURBATION_DEPTHS) + controls_count,
        "pass": (
            N_CONTEXTS == 8
            and STATE_DIM == 2
            and density_entry_count == 32
            and update_trace_count == 72
            and len(PERTURBATION_DEPTHS) == 9
            and controls_count == 6
        ),
    }


def torch_normalize(psi: torch.Tensor) -> torch.Tensor:
    norm = torch.sqrt(torch.clamp(torch.real(torch.vdot(psi, psi)), min=1.0e-15))
    return psi / norm


def torch_su2_x(angle: float) -> torch.Tensor:
    dtype = torch.complex128
    eye = torch.eye(2, dtype=dtype)
    sx = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=dtype)
    a = torch.tensor(angle / 2.0, dtype=torch.float64)
    return torch.cos(a) * eye - 1j * torch.sin(a) * sx


def torch_su2_z(angle: float) -> torch.Tensor:
    dtype = torch.complex128
    a = torch.tensor(angle / 2.0, dtype=torch.float64)
    return torch.diag(torch.stack([torch.exp(-1j * a), torch.exp(1j * a)])).to(dtype)


def torch_density(psi: torch.Tensor) -> torch.Tensor:
    psi = torch_normalize(psi)
    return torch.outer(psi, torch.conj(psi))


def torch_density_distance(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    diff = torch_density(a) - torch_density(b)
    return torch.sqrt(torch.clamp(torch.real(torch.trace(torch.conj(diff.T) @ diff)), min=0.0))


def torch_spinor_from_jax(psi: jax.Array) -> torch.Tensor:
    payload = spinor_payload(psi)
    return torch_normalize(torch.tensor([complex(row[0], row[1]) for row in payload], dtype=torch.complex128))


def pytorch_invariant_recompute(final_model: jax.Array, jax_order_gaps: list[float]) -> dict[str, Any]:
    torch_gaps = []
    traces = []
    purities = []
    for context_id in range(N_CONTEXTS):
        psi = torch_spinor_from_jax(true_lifted_spinor(context_id))
        x_then_z = torch_su2_z(0.51) @ (torch_su2_x(0.37) @ psi)
        z_then_x = torch_su2_x(0.37) @ (torch_su2_z(0.51) @ psi)
        torch_gaps.append(float(torch_density_distance(x_then_z, z_then_x).item()))

        model_psi = torch_spinor_from_jax(final_model[context_id])
        rho = torch_density(model_psi)
        traces.append(float(torch.real(torch.trace(rho)).item()))
        purities.append(float(torch.real(torch.trace(rho @ rho)).item()))

    deltas = [abs(a - b) for a, b in zip(jax_order_gaps, torch_gaps)]
    return {
        "torch_min_order_gap": min(torch_gaps),
        "torch_max_order_gap": max(torch_gaps),
        "jax_torch_max_order_gap_delta": max(deltas),
        "max_trace_deviation": max(abs(value - 1.0) for value in traces),
        "max_purity_deviation": max(abs(value - 1.0) for value in purities),
        "pass": (
            min(torch_gaps) > 1.0e-3
            and max(deltas) < 2.5e-6
            and max(abs(value - 1.0) for value in traces) < 2.5e-6
            and max(abs(value - 1.0) for value in purities) < 2.5e-6
        ),
    }


def build_contract_rows(
    *,
    live_m: dict[str, float],
    frozen_m: dict[str, float],
    shuffled_m: dict[str, float],
    density_only_m: dict[str, float],
    no_graveyard_m: dict[str, float],
    boundary_scan: dict[str, Any],
    fake: dict[str, float | bool],
    f01_counts: dict[str, Any],
    order_gaps: list[float],
    pytorch_check: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    update_reduction = live_m["first_cycle_combined_error"] - live_m["last_cycle_combined_error"]
    frozen_reduction = frozen_m["first_cycle_combined_error"] - frozen_m["last_cycle_combined_error"]
    control_passes = {
        "frozen_model": frozen_m["model_relative_recall"] < live_m["model_relative_recall"] - 0.16,
        "shuffled_context": shuffled_m["model_relative_recall"] < live_m["model_relative_recall"] - 0.20,
        "density_only": density_only_m["lifted_path_alignment"] < live_m["lifted_path_alignment"] - 0.28,
        "graveyard_off": no_graveyard_m["false_accept_rate_without_graveyard"] > live_m["false_accept_rate_with_graveyard"] + 0.15,
    }
    killed_fake = (
        bool(fake["trivial_contraction_present"])
        and float(fake["fake_model_relative_recall"]) < live_m["model_relative_recall"] - 0.30
    )
    max_final_recovered_error = max(
        float(row["final_error"])
        for row in boundary_scan["rows"]
        if row["recovered_in_basin"]
    )
    best_escape_error = min(
        float(row["final_error"])
        for row in boundary_scan["rows"]
        if not row["recovered_in_basin"]
    )

    return {
        "01_admissibility_predicate": {
            "predicate": (
                "Admit a scratch basin candidate only when finite C^2 density states, ordered update, "
                "nonzero X/Z order gap, bounded perturbation recovery, and all named controls pass."
            ),
            "pass": (
                live_m["model_relative_recall"] > 0.82
                and boundary_scan["has_nontrivial_recovery_region"]
                and min(order_gaps) > 1.0e-3
                and pytorch_check["pass"]
            ),
            "live_model_relative_recall": live_m["model_relative_recall"],
            "max_recovered_depth": boundary_scan["max_recovered_depth"],
            "min_jax_order_gap": min(order_gaps),
            "pytorch_invariant_check_pass": pytorch_check["pass"],
        },
        "02_state_space": {
            "state_space": "finite product of 8 normalized C^2 spinors with density rho_i=|psi_i><psi_i|",
            "pass": f01_counts["pass"] and pytorch_check["max_trace_deviation"] < 2.5e-6,
            "contexts": f01_counts["contexts"],
            "spinor_components_per_state": f01_counts["spinor_components_per_state"],
            "density_entries_total": f01_counts["density_entries_total"],
            "max_density_trace_deviation": pytorch_check["max_trace_deviation"],
            "max_density_purity_deviation": pytorch_check["max_purity_deviation"],
        },
        "03_update_rule": {
            "update_rule": "prediction p_i = normalize(0.78 psi_i + 0.11 psi_{i-1} + 0.11 psi_{i+1}); correction psi_i <- normalize((1-g) psi_i + g observation_i)",
            "pass": update_reduction > 0.27 and update_reduction > frozen_reduction + 0.18,
            "correction_gain": CORRECTION_GAIN,
            "live_error_reduction": update_reduction,
            "frozen_error_reduction": frozen_reduction,
        },
        "04_basin_boundary": {
            "boundary_rule": "depth d is in the local basin when recovered final error <= threshold and contraction ratio < 0.82",
            "pass": boundary_scan["has_nontrivial_recovery_region"] and boundary_scan["has_escape_region"],
            "local_recovery_error_threshold": LOCAL_RECOVERY_ERROR_THRESHOLD,
            "max_recovered_depth": boundary_scan["max_recovered_depth"],
            "first_escape_depth": boundary_scan["first_escape_depth"],
            "max_final_recovered_error": max_final_recovered_error,
            "best_escape_final_error": best_escape_error,
        },
        "05_stability_invariant": {
            "invariant": "bounded perturbations contract prediction error and recover below the same finite density/lift threshold",
            "pass": (
                live_m["mean_contraction_ratio"] < 0.82
                and min(float(row["contraction_ratio"]) for row in boundary_scan["rows"] if row["recovered_in_basin"]) < 0.62
            ),
            "live_mean_contraction_ratio": live_m["mean_contraction_ratio"],
            "best_recovery_contraction_ratio": min(float(row["contraction_ratio"]) for row in boundary_scan["rows"]),
            "worst_recovered_contraction_ratio": max(
                float(row["contraction_ratio"]) for row in boundary_scan["rows"] if row["recovered_in_basin"]
            ),
        },
        "06_escape_failure_cases": {
            "escape_controls": "frozen model, shuffled context, density-only, and graveyard-off controls must lose the live basin-grade witness",
            "pass": all(control_passes.values()),
            "control_passes": control_passes,
            "live_model_relative_recall": live_m["model_relative_recall"],
            "frozen_model_relative_recall": frozen_m["model_relative_recall"],
            "shuffled_model_relative_recall": shuffled_m["model_relative_recall"],
            "live_lifted_path_alignment": live_m["lifted_path_alignment"],
            "density_only_lifted_path_alignment": density_only_m["lifted_path_alignment"],
            "live_false_accept_with_graveyard": live_m["false_accept_rate_with_graveyard"],
            "graveyard_off_false_accept_without_graveyard": no_graveyard_m["false_accept_rate_without_graveyard"],
        },
        "07_root_tests_f01_n01": {
            "root_tests": "F01 finite counts plus N01 ordered X/Z channel gap on the spinor/density carrier",
            "pass": f01_counts["pass"] and min(order_gaps) > 1.0e-3 and pytorch_check["pass"],
            "F01": f01_counts,
            "N01": {
                "min_jax_xz_zx_order_gap": min(order_gaps),
                "max_jax_xz_zx_order_gap": max(order_gaps),
                "torch_min_xz_zx_order_gap": pytorch_check["torch_min_order_gap"],
                "jax_torch_max_order_gap_delta": pytorch_check["jax_torch_max_order_gap_delta"],
            },
        },
        "08_killed_fake_basin_control": {
            "killed_explanation": "a trivial fixed attractor can contract perturbations but cannot preserve context-relative recall",
            "pass": killed_fake,
            "fake_trivial_contraction_present": fake["trivial_contraction_present"],
            "fake_contraction_ratio": fake["fake_contraction_ratio"],
            "fake_model_relative_recall": fake["fake_model_relative_recall"],
            "live_model_relative_recall": live_m["model_relative_recall"],
            "recall_gap_live_minus_fake": live_m["model_relative_recall"] - float(fake["fake_model_relative_recall"]),
        },
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    live = run_loop(update=True, density_only=False, shuffled_context=False, write_graveyard=True)
    frozen = run_loop(update=False, density_only=False, shuffled_context=False, write_graveyard=True)
    shuffled = run_loop(update=True, density_only=False, shuffled_context=True, write_graveyard=True)
    density_only = run_loop(update=True, density_only=True, shuffled_context=False, write_graveyard=True)
    no_graveyard = run_loop(update=True, density_only=False, shuffled_context=False, write_graveyard=False)

    live_m = summarize_loop(live, density_only=False)
    frozen_m = summarize_loop(frozen, density_only=False)
    shuffled_m = summarize_loop(shuffled, density_only=False)
    density_only_m = summarize_loop(density_only, density_only=True)
    no_graveyard_m = summarize_loop(no_graveyard, density_only=False)

    order_gaps = [as_float(channel_order_gap(true_lifted_spinor(i))) for i in range(N_CONTEXTS)]
    boundary_scan = basin_boundary_scan(live["model"])
    fake = fake_fixed_attractor_control()
    f01_counts = finite_count_receipts()
    pytorch_check = pytorch_invariant_recompute(live["model"], order_gaps)

    positive = {
        "jax_x64_primary_spinor_density_loop": {
            "pass": jax.config.read("jax_enable_x64") is True and live_m["model_relative_recall"] > 0.82,
            "jax_enable_x64": jax.config.read("jax_enable_x64"),
            "live_model_relative_recall": live_m["model_relative_recall"],
        },
        "prediction_correction_error_contracts": {
            "pass": live_m["first_cycle_combined_error"] - live_m["last_cycle_combined_error"] > 0.27,
            "first_cycle_combined_error": live_m["first_cycle_combined_error"],
            "last_cycle_combined_error": live_m["last_cycle_combined_error"],
            "error_reduction": live_m["first_cycle_combined_error"] - live_m["last_cycle_combined_error"],
        },
        "basin_boundary_has_recovery_and_escape": {
            "pass": boundary_scan["has_nontrivial_recovery_region"] and boundary_scan["has_escape_region"],
            "max_recovered_depth": boundary_scan["max_recovered_depth"],
            "first_escape_depth": boundary_scan["first_escape_depth"],
        },
        "pytorch_independent_invariant_recompute": pytorch_check,
    }

    graveyard_companions = {
        "survivor_hashes_exist": {
            "pass": live_m["survivor_hash_count"] >= N_CONTEXTS * (N_CYCLES - 2),
            "count": live_m["survivor_hash_count"],
            "minimum_required": N_CONTEXTS * (N_CYCLES - 2),
        },
        "graveyard_hashes_exist": {
            "pass": live_m["graveyard_hash_count"] >= N_CONTEXTS,
            "count": live_m["graveyard_hash_count"],
            "minimum_required": N_CONTEXTS,
        },
        "graveyard_suppresses_false_confirmation": {
            "pass": live_m["false_accept_rate_with_graveyard"] < live_m["false_accept_rate_without_graveyard"],
            "with_graveyard": live_m["false_accept_rate_with_graveyard"],
            "same_killed_set_without_graveyard": live_m["false_accept_rate_without_graveyard"],
        },
    }

    boundary = {
        "promotion_allowed_false": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "formal_admission_allowed_false": {
            "pass": FORMAL_ADMISSION_ALLOWED is False,
            "value": FORMAL_ADMISSION_ALLOWED,
        },
        "scratch_diagnostic_only": {"pass": SCRATCH_DIAGNOSTIC_ONLY is True, "value": SCRATCH_DIAGNOSTIC_ONLY},
        "blocked_consumers_preserved": {
            "pass": len(BLOCKED_CONSUMERS) >= 10,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "source_seed_receipts_observed": {
            "pass": all(row["exists"] for row in source_seed_status()),
            "source_seed_status": source_seed_status(),
        },
    }

    basin_contract_rows = build_contract_rows(
        live_m=live_m,
        frozen_m=frozen_m,
        shuffled_m=shuffled_m,
        density_only_m=density_only_m,
        no_graveyard_m=no_graveyard_m,
        boundary_scan=boundary_scan,
        fake=fake,
        f01_counts=f01_counts,
        order_gaps=order_gaps,
        pytorch_check=pytorch_check,
    )

    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
        and all(row["pass"] for row in basin_contract_rows.values())
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": classification,
        "CLASSIFICATION": CLASSIFICATION,
        "SIM_EXECUTION_KIND": SIM_EXECUTION_KIND,
        "SOURCE_ALIGNMENT_CATEGORY": SOURCE_ALIGNMENT_CATEGORY,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "SCRATCH_DIAGNOSTIC_ONLY": SCRATCH_DIAGNOSTIC_ONLY,
        "scratch_diagnostic_only": SCRATCH_DIAGNOSTIC_ONLY,
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
        "carrier_layer": "finite C^2 spinor cells with density readout",
        "geometry_layer": "none admitted; finite ring-context diagnostic carrier only",
        "bridge_layer": "none",
        "cut_layer": "none",
        "carrier_realization": "JAX complex128 psi in C^2 with rho=|psi><psi|; PyTorch complex128 invariant recomputation",
        "peps3d_embedding": "not admitted here; blocked consumer",
        "spinor_state": "explicit finite C^2 spinor per context",
        "quaternion_action": "not_applicable in this scratch diagnostic",
        "dependency_receipts": [str(path) for path in SOURCE_SEED_RESULTS],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_depth_note": (
            "JAX is the primary x64 runtime for this probe. PyTorch is included as a local load-bearing "
            "independent invariant recomputation because the current static nonclassical linter requires it."
        ),
        "all_pass": all_pass,
        "candidate_status": (
            "scratch_diagnostic_basin_contract_rows_passed_not_admitted"
            if all_pass
            else "scratch_diagnostic_basin_contract_open_or_failed_not_admitted"
        ),
        "candidate_survived": all_pass,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "basin_contract_rows": basin_contract_rows,
        "F01_finite_counts": f01_counts,
        "N01_xz_order_gap": {
            "min_jax_xz_zx_order_gap": min(order_gaps),
            "max_jax_xz_zx_order_gap": max(order_gaps),
            "all_jax_xz_zx_order_gaps": order_gaps,
            "pytorch_invariant_recompute": pytorch_check,
        },
        "metrics": {
            "live": live_m,
            "frozen_model_control": frozen_m,
            "shuffled_context_control": shuffled_m,
            "density_only_control": density_only_m,
            "graveyard_off_control": no_graveyard_m,
            "basin_boundary_scan": boundary_scan,
            "fake_fixed_attractor_control": fake,
        },
        "nearby_variants": {
            "tested_here": [
                "frozen_model_no_update",
                "shuffled_context_update",
                "density_only_projective_control",
                "graveyard_off_false_confirmation",
                "trivial_fixed_attractor_fake_basin",
                "ordered_XZ_vs_ZX_channel_gap",
                "bounded_perturbation_depth_recovery",
            ],
            "not_tested_here": [
                "QIT replay",
                "Xi bridge",
                "Phi0 bridge",
                "Axis0",
                "FEP",
                "final Holodeck",
                "gravity",
                "physics",
                "cognition",
                "consciousness",
                "manifold admission",
            ],
        },
        "why_not_v4_probes": {
            "reason": "This is a v5 scratch diagnostic basin-contract grade over Holodeck seed fixtures, not a v4 doctrine mirror or promotion artifact.",
            "v4_equivalent": None,
        },
        "blocked_consumers": BLOCKED_CONSUMERS,
        "recommended_next_gates": [
            "keep this as scratch diagnostic until a separate admitted QIT replay fixture exists",
            "run a separate source-native QIT replay probe before any stronger Holodeck basin claim",
            "do not route this result into Xi/Phi0, Axis0, FEP, or manifold consumers",
        ],
        "runtime_seconds": time.time() - started,
        "result_path": str(OUT_PATH),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "candidate_status": result["candidate_status"],
                "max_recovered_depth": boundary_scan["max_recovered_depth"],
                "first_escape_depth": boundary_scan["first_escape_depth"],
                "min_jax_order_gap": min(order_gaps),
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
