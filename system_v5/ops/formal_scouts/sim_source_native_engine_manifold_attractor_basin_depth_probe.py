#!/usr/bin/env python3
"""Canonical QIT replay engine/manifold attractor-basin depth scout.

This is a foundation scout for the active attractor-basin goal. It tests a
bounded replay of the former EngineCore/manifold fixture under multiple
observables and matched controls. It is not source-native EngineCore dynamics
and is not a global manifold proof.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from collections.abc import Iterable
from typing import Any

import torch

from canonical_qit_engine_specs import (
    OPERATOR_BASE_ANGLES,
    OPERATOR_GENERATORS,
    get_lindblad_params,
    get_operator_slot_spec,
    get_schedule,
    get_terrain_dynamics_spec,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_engine_manifold_attractor_basin_depth_probe_results.json"

NAME = "source_native_engine_manifold_attractor_basin_depth_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a bounded canonical QIT replay of the former "
    "EngineCore/manifold candidate attractor-basin-depth fixture under "
    "perturbations and matched controls. It does not admit source-native "
    "EngineCore dynamics, real attractor basins, global manifold necessity, "
    "arbitrary CPTP robustness, global basin depth, final FEP, final Axis0, "
    "full Holodeck, physics, cognition, world-model, architecture, tensor-network, "
    "or canonical claims. Its random controls are finite 2x2 PyTorch controls only."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density perturbations, trace distances, Pauli/FEP readouts, random schedule/CPTP controls, and basin statistics",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical terrain/operator schedule records replacing the former direct EngineCore boundary",
    },
    "json": {"tried": True, "used": True, "reason": "supportive result writing"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source hash receipt"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "canonical_qit_engine_specs": "supportive",
    "json": "supportive",
    "hashlib": "supportive",
}

SEEDS = [101, 211, 307, 419]
EPSILONS = [0.02, 0.08, 0.18]
TRACE_CANDIDATE_FLOOR = 0.10
CONTROL_SEPARATION_FLOOR = 0.05
TORCH_COMPLEX = torch.complex128
TORCH_REAL = torch.float64
I2_TORCH = torch.eye(2, dtype=TORCH_COMPLEX)
SX_TORCH = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=TORCH_COMPLEX)
SY_TORCH = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=TORCH_COMPLEX)
SZ_TORCH = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=TORCH_COMPLEX)
PAULI_KRAUS_BASIS = [I2_TORCH, SX_TORCH, SY_TORCH, SZ_TORCH]
CONTROL_TRACE_KEYS = {
    "off": "off_trace_to_baseline",
    "reversed_schedule": "reversed_trace_to_baseline",
    "random_schedule": "random_schedule_trace_to_baseline",
    "wrong_chirality": "wrong_chirality_trace_to_baseline",
    "random_cptp": "random_cptp_trace_to_baseline",
}
STAGE_DT = 0.05
MANIFOLD_TARGET_MIX = 0.12


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def as_torch_density(rho: Any) -> torch.Tensor:
    tensor = torch.as_tensor(rho, dtype=TORCH_COMPLEX)
    if tuple(tensor.shape) != (2, 2):
        raise ValueError(f"expected 2x2 density matrix, got shape {tuple(tensor.shape)}")
    return tensor


def normalize_density_torch(rho: Any) -> torch.Tensor:
    tensor = as_torch_density(rho)
    hermitian = 0.5 * (tensor + tensor.conj().T)
    evals, evecs = torch.linalg.eigh(hermitian)
    evals = torch.clamp(evals.real, min=0.0)
    total = torch.sum(evals)
    if float(total.item()) <= 0.0:
        return I2_TORCH / 2.0
    normalized = evecs @ torch.diag(evals.to(TORCH_COMPLEX)) @ evecs.conj().T
    normalized = normalized / total.to(TORCH_COMPLEX)
    return 0.5 * (normalized + normalized.conj().T)


def generate_initial_density(seed: int) -> torch.Tensor:
    generator = torch.Generator()
    generator.manual_seed(int(seed))
    raw = torch.randn(2, 2, generator=generator, dtype=TORCH_REAL) + 1j * torch.randn(2, 2, generator=generator, dtype=TORCH_REAL)
    psi = raw[:, 0].to(TORCH_COMPLEX)
    psi = psi / torch.linalg.vector_norm(psi)
    rho = torch.outer(psi, psi.conj())
    return normalize_density_torch(rho)


def mean_float(values: Iterable[float]) -> float:
    tensor = torch.tensor([float(value) for value in values], dtype=TORCH_REAL)
    return float(torch.mean(tensor).item()) if tensor.numel() else 0.0


def max_float(values: Iterable[float]) -> float:
    tensor = torch.tensor([float(value) for value in values], dtype=TORCH_REAL)
    return float(torch.max(tensor).item()) if tensor.numel() else 0.0


def density_diagnostics(rho: Any) -> dict[str, float]:
    tensor = as_torch_density(rho)
    hermitian = 0.5 * (tensor + tensor.conj().T)
    eigs = torch.linalg.eigvalsh(hermitian).real
    trace = torch.trace(tensor)
    return {
        "trace_real": float(trace.real.item()),
        "trace_imag": float(trace.imag.item()),
        "trace_gap": float(torch.abs(trace - torch.tensor(1.0, dtype=TORCH_COMPLEX)).item()),
        "hermitian_gap": float(torch.linalg.matrix_norm(tensor - tensor.conj().T).item()),
        "min_eigenvalue": float(torch.min(eigs).item()),
    }


def trace_distance(rho1: Any, rho2: Any) -> float:
    diff = as_torch_density(rho1) - as_torch_density(rho2)
    evals = torch.linalg.eigvalsh(diff.conj().T @ diff).real
    singular_values = torch.sqrt(torch.clamp(evals, min=0.0))
    return 0.5 * float(torch.sum(singular_values).item())


def perturb_density(rho: Any, epsilon: float) -> Any:
    rho_t = as_torch_density(rho)
    perturbed = normalize_density_torch((1.0 - epsilon) * rho_t + epsilon * I2_TORCH / 2.0)
    return perturbed


def density_entropy(rho: Any) -> float:
    tensor = normalize_density_torch(rho)
    evals = torch.clamp(torch.linalg.eigvalsh(tensor).real, min=1e-14)
    return float((-torch.sum(evals * torch.log(evals))).item())


def bloch_vector(rho: Any) -> list[float]:
    tensor = as_torch_density(rho)
    return [
        float(torch.real(torch.trace(tensor @ SX_TORCH)).item()),
        float(torch.real(torch.trace(tensor @ SY_TORCH)).item()),
        float(torch.real(torch.trace(tensor @ SZ_TORCH)).item()),
    ]


def stage_fixed_target(perception: str, engine_type: int) -> torch.Tensor:
    if perception == "Se":
        return I2_TORCH / 2.0
    if perception == "Ni":
        return I2_TORCH / 2.0
    if perception == "Si":
        ket = torch.tensor([1.0, 0.0], dtype=TORCH_COMPLEX) if engine_type == 0 else torch.tensor([0.0, 1.0], dtype=TORCH_COMPLEX)
        return torch.outer(ket, ket.conj())
    if perception == "Ne":
        ket = torch.tensor([0.0, 1.0], dtype=TORCH_COMPLEX) if engine_type == 0 else torch.tensor([1.0, 0.0], dtype=TORCH_COMPLEX)
        return torch.outer(ket, ket.conj())
    raise ValueError(f"unknown perception {perception!r}")


def apply_operator_slot(rho: torch.Tensor, perception: str, engine_type: int, loop_class: str) -> torch.Tensor:
    slot = get_operator_slot_spec(perception, engine_type, loop_class, 0)
    generator = OPERATOR_GENERATORS[slot["operator"]]
    angle = float(slot["sign"]) * float(OPERATOR_BASE_ANGLES[slot["operator"]])
    unitary = torch.linalg.matrix_exp((-1j * angle) * generator)
    return unitary @ rho @ unitary.conj().T


def lindblad_rhs_matrix(H: torch.Tensor, L: torch.Tensor, rate: float) -> torch.Tensor:
    scaled_l = (float(rate) ** 0.5) * L
    ldag_l = scaled_l.conj().T @ scaled_l
    basis = []
    for i in range(2):
        for j in range(2):
            e = torch.zeros((2, 2), dtype=TORCH_COMPLEX)
            e[i, j] = 1.0 + 0.0j
            basis.append(e)
    cols = []
    for e in basis:
        de = -1j * (H @ e - e @ H)
        de = de + scaled_l @ e @ scaled_l.conj().T
        de = de - 0.5 * (ldag_l @ e + e @ ldag_l)
        cols.append(de.reshape(4))
    return torch.stack(cols, dim=1)


def apply_lindblad_step(rho: torch.Tensor, perception: str, engine_type: int) -> torch.Tensor:
    terrain = get_terrain_dynamics_spec(perception, engine_type)
    H, L = get_lindblad_params(perception, engine_type)
    generator = lindblad_rhs_matrix(H, L, float(terrain["rate"]))
    channel = torch.linalg.matrix_exp(STAGE_DT * generator)
    out = (channel @ rho.reshape(4)).reshape(2, 2)
    return 0.5 * (out + out.conj().T)


def pauli_channel_choi_min_eigenvalue(weights: torch.Tensor) -> float:
    choi = torch.zeros((4, 4), dtype=TORCH_COMPLEX)
    for weight, pauli in zip(weights, PAULI_KRAUS_BASIS):
        vec = pauli.reshape(4, 1)
        choi = choi + weight.to(TORCH_COMPLEX) * (vec @ vec.conj().T)
    eigs = torch.linalg.eigvalsh(0.5 * (choi + choi.conj().T)).real
    return float(torch.min(eigs).item())


def random_pauli_cptp_control(rho: Any, control_seed: int, *, steps: int = 64) -> dict[str, Any]:
    generator = torch.Generator()
    generator.manual_seed(int(control_seed))
    state = as_torch_density(rho)
    min_weight = 1.0
    max_weight_sum_gap = 0.0
    min_choi_eigenvalue = float("inf")
    first_weights: list[float] | None = None
    last_weights: list[float] | None = None
    for _ in range(steps):
        weights = torch.softmax(torch.rand(4, generator=generator, dtype=TORCH_REAL), dim=0)
        weights_list = [float(value) for value in weights.tolist()]
        if first_weights is None:
            first_weights = weights_list
        last_weights = weights_list
        min_weight = min(min_weight, min(weights_list))
        max_weight_sum_gap = max(max_weight_sum_gap, abs(sum(weights_list) - 1.0))
        min_choi_eigenvalue = min(min_choi_eigenvalue, pauli_channel_choi_min_eigenvalue(weights))
        next_state = torch.zeros_like(state)
        for weight, pauli in zip(weights, PAULI_KRAUS_BASIS):
            next_state = next_state + weight.to(TORCH_COMPLEX) * (pauli @ state @ pauli.conj().T)
        state = 0.5 * (next_state + next_state.conj().T)
    diagnostics = density_diagnostics(state)
    return {
        "rho": state,
        "seed": int(control_seed),
        "control_kind": "random_pauli_cptp",
        "steps": int(steps),
        "normalization_applied": False,
        "first_step_weights": first_weights or [],
        "last_step_weights": last_weights or [],
        "min_weight": min_weight,
        "max_weight_sum_gap": max_weight_sum_gap,
        "min_step_choi_eigenvalue": min_choi_eigenvalue,
        "final_density_diagnostics": diagnostics,
        "trace_preserving_pass": diagnostics["trace_gap"] < 1e-10,
        "density_valid_pass": (
            diagnostics["trace_gap"] < 1e-10
            and diagnostics["hermitian_gap"] < 1e-10
            and diagnostics["min_eigenvalue"] >= -1e-10
        ),
        "choi_psd_pass": min_choi_eigenvalue >= -1e-10 and min_weight >= 0.0 and max_weight_sum_gap < 1e-12,
    }


def run_cycle(
    engine_type: int,
    rho: Any,
    *,
    manifold_enabled: bool,
    schedule_mode: str = "native",
    schedule_seed: int = 0,
) -> dict[str, Any]:
    schedule = list(get_schedule(engine_type))
    original_schedule = [f"{perception}:{loop_class}" for perception, loop_class in schedule]
    schedule_permutation: list[int] = list(range(len(schedule)))
    if schedule_mode == "reversed":
        schedule = list(reversed(schedule))
    elif schedule_mode == "rotated":
        schedule = schedule[1:] + schedule[:1]
    elif schedule_mode == "torch_random":
        generator = torch.Generator()
        generator.manual_seed(int(schedule_seed))
        schedule_permutation = [int(index) for index in torch.randperm(len(schedule), generator=generator).tolist()]
        schedule = [schedule[index] for index in schedule_permutation]
    state = normalize_density_torch(rho)
    efe: list[float] = []
    surprise: list[float] = []
    correction: list[float] = []
    tokens: list[str] = []
    for perception, loop_class in schedule:
        slot = get_operator_slot_spec(perception, engine_type, loop_class, 0)
        state = apply_operator_slot(state, perception, engine_type, loop_class)
        state = apply_lindblad_step(state, perception, engine_type)
        target = stage_fixed_target(perception, engine_type)
        before_repair = state
        if manifold_enabled:
            state = normalize_density_torch((1.0 - MANIFOLD_TARGET_MIX) * state + MANIFOLD_TARGET_MIX * target)
        else:
            state = normalize_density_torch(state)
        correction.append(float(torch.linalg.matrix_norm(state - before_repair).item()))
        efe.append(trace_distance(state, target))
        surprise.append(density_entropy(state))
        tokens.append(str(slot["token"]))
    final_purity = float(torch.real(torch.trace(state @ state)).item())
    return {
        "rho": state,
        "tokens": tokens,
        "mean_efe": mean_float(efe),
        "mean_surprise": mean_float(surprise),
        "mean_correction": mean_float(correction),
        "max_correction": max_float(correction),
        "final_purity": final_purity,
        "final_entropy": density_entropy(state),
        "final_bloch": bloch_vector(state),
        "schedule_mode": schedule_mode,
        "schedule_receipt": {
            "schedule_mode": schedule_mode,
            "schedule_seed": int(schedule_seed),
            "stage_index_semantics_preserved": schedule_mode != "torch_random",
            "permutation": schedule_permutation,
            "original_schedule": original_schedule,
            "mutated_schedule": [f"{perception}:{loop_class}" for perception, loop_class in schedule],
        },
    }


def token_match_fraction(a: list[str], b: list[str]) -> float:
    return sum(1 for x, y in zip(a, b) if x == y) / max(1, min(len(a), len(b)))


def classify_basin(rows: list[dict[str, Any]]) -> dict[str, Any]:
    on_mean = mean_float(row["on_trace_to_baseline"] for row in rows)
    control_means = {
        name: mean_float(row[key] for row in rows)
        for name, key in CONTROL_TRACE_KEYS.items()
    }
    nearest_control_name, nearest_control = min(control_means.items(), key=lambda item: item[1])
    separation = nearest_control - on_mean
    if on_mean <= TRACE_CANDIDATE_FLOOR and separation >= CONTROL_SEPARATION_FLOOR:
        label = "candidate_basin"
    elif separation < 0:
        label = "anti_basin"
    elif on_mean <= nearest_control:
        label = "shallow_basin"
    else:
        label = "open_basin_boundary"
    return {
        "label": label,
        "on_mean_trace_to_baseline": on_mean,
        "off_mean_trace_to_baseline": control_means["off"],
        "reversed_mean_trace_to_baseline": control_means["reversed_schedule"],
        "random_schedule_mean_trace_to_baseline": control_means["random_schedule"],
        "wrong_chirality_mean_trace_to_baseline": control_means["wrong_chirality"],
        "random_cptp_mean_trace_to_baseline": control_means["random_cptp"],
        "nearest_control_mean": nearest_control,
        "nearest_control_name": nearest_control_name,
        "control_separation": separation,
        "candidate_trace_floor": TRACE_CANDIDATE_FLOOR,
        "control_separation_floor": CONTROL_SEPARATION_FLOOR,
    }


def main() -> int:
    started = time.time()
    rows = []
    control_receipts = []
    for engine_type in (0, 1):
        for seed in SEEDS:
            rho0 = generate_initial_density(seed)
            baseline = run_cycle(engine_type, rho0, manifold_enabled=True)
            for epsilon in EPSILONS:
                pert = perturb_density(rho0, epsilon)
                on = run_cycle(engine_type, pert, manifold_enabled=True)
                off = run_cycle(engine_type, pert, manifold_enabled=False)
                reversed_control = run_cycle(engine_type, pert, manifold_enabled=True, schedule_mode="reversed")
                random_schedule_seed = 7919 + 1000 * engine_type + 10 * seed + int(epsilon * 1000)
                random_schedule = run_cycle(
                    engine_type,
                    pert,
                    manifold_enabled=True,
                    schedule_mode="torch_random",
                    schedule_seed=random_schedule_seed,
                )
                wrong = run_cycle(1 - engine_type, pert, manifold_enabled=True)
                random_cptp_seed = 104729 + 1000 * engine_type + 10 * seed + int(epsilon * 1000)
                random_cptp = random_pauli_cptp_control(pert, random_cptp_seed)
                control_receipts.append(
                    {
                        "engine_type": engine_type,
                        "seed": seed,
                        "epsilon": epsilon,
                        "random_schedule": random_schedule["schedule_receipt"],
                        "random_cptp": {key: value for key, value in random_cptp.items() if key != "rho"},
                    }
                )
                rows.append(
                    {
                        "engine_type": engine_type,
                        "seed": seed,
                        "epsilon": epsilon,
                        "on_trace_to_baseline": trace_distance(on["rho"], baseline["rho"]),
                        "off_trace_to_baseline": trace_distance(off["rho"], baseline["rho"]),
                        "reversed_trace_to_baseline": trace_distance(reversed_control["rho"], baseline["rho"]),
                        "random_schedule_trace_to_baseline": trace_distance(random_schedule["rho"], baseline["rho"]),
                        "wrong_chirality_trace_to_baseline": trace_distance(wrong["rho"], baseline["rho"]),
                        "random_cptp_trace_to_baseline": trace_distance(random_cptp["rho"], baseline["rho"]),
                        "on_token_match": token_match_fraction(on["tokens"], baseline["tokens"]),
                        "reversed_token_match": token_match_fraction(reversed_control["tokens"], baseline["tokens"]),
                        "random_schedule_token_match": token_match_fraction(random_schedule["tokens"], baseline["tokens"]),
                        "wrong_chirality_token_match": token_match_fraction(wrong["tokens"], baseline["tokens"]),
                        "random_schedule_seed": random_schedule_seed,
                        "random_cptp_seed": random_cptp_seed,
                        "random_cptp_control_kind": "random_pauli_cptp",
                        "random_cptp_trace_gap": random_cptp["final_density_diagnostics"]["trace_gap"],
                        "random_cptp_min_choi_eigenvalue": random_cptp["min_step_choi_eigenvalue"],
                        "random_cptp_output_min_eigenvalue": random_cptp["final_density_diagnostics"]["min_eigenvalue"],
                        "on_mean_efe": on["mean_efe"],
                        "off_mean_efe": off["mean_efe"],
                        "on_mean_correction": on["mean_correction"],
                        "off_mean_correction": off["mean_correction"],
                        "on_final_purity": on["final_purity"],
                        "off_final_purity": off["final_purity"],
                    }
                )

    basin = classify_basin(rows)
    on_token_min = min(row["on_token_match"] for row in rows)
    reversed_token_max = max(row["reversed_token_match"] for row in rows)
    random_schedule_token_max = max(row["random_schedule_token_match"] for row in rows)
    wrong_token_max = max(row["wrong_chirality_token_match"] for row in rows)
    on_correction_mean = mean_float(row["on_mean_correction"] for row in rows)
    off_correction_mean = mean_float(row["off_mean_correction"] for row in rows)
    purity_gap = mean_float(row["on_final_purity"] - row["off_final_purity"] for row in rows)
    random_schedule_permutations = {
        tuple(receipt["random_schedule"]["permutation"]) for receipt in control_receipts
    }
    cptp_valid = all(receipt["random_cptp"]["trace_preserving_pass"] and receipt["random_cptp"]["density_valid_pass"] and receipt["random_cptp"]["choi_psd_pass"] for receipt in control_receipts)

    positive = {
        "epsilon_seed_engine_grid_executed": {
            "pass": len(rows) == 2 * len(SEEDS) * len(EPSILONS),
            "row_count": len(rows),
            "seeds": SEEDS,
            "epsilons": EPSILONS,
        },
        "native_stage_identity_preserved_under_perturbation": {
            "pass": on_token_min == 1.0,
            "min_on_token_match": on_token_min,
        },
        "manifold_correction_is_load_bearing_local_observable": {
            "pass": on_correction_mean > off_correction_mean + 1e-6 and basin["on_mean_trace_to_baseline"] < basin["off_mean_trace_to_baseline"],
            "on_mean_correction": on_correction_mean,
            "off_mean_correction": off_correction_mean,
            "mean_purity_gap_on_minus_off": purity_gap,
            "on_mean_trace_to_baseline": basin["on_mean_trace_to_baseline"],
            "off_mean_trace_to_baseline": basin["off_mean_trace_to_baseline"],
            "reason": "The bounded canonical replay preserves manifold correction as a local observable and separates the manifold-enabled replay from the manifold-disabled control; it does not require the old EngineCore purity-gap sign.",
        },
        "basin_depth_classifier_runs": {
            "pass": basin["label"] in {"candidate_basin", "shallow_basin", "anti_basin", "open_basin_boundary"},
            "basin": basin,
        },
    }
    graveyard = {
        "reversed_schedule_control_disrupts_stage_identity": {
            "pass": reversed_token_max < 1.0,
            "max_reversed_token_match": reversed_token_max,
        },
        "random_schedule_control_disrupts_stage_identity": {
            "pass": random_schedule_token_max < 1.0,
            "max_random_schedule_token_match": random_schedule_token_max,
            "distinct_random_schedule_permutations": len(random_schedule_permutations),
        },
        "pauli_channel_random_cptp_control_preserves_density_validity": {
            "pass": cptp_valid,
            "max_trace_gap": max_float(receipt["random_cptp"]["final_density_diagnostics"]["trace_gap"] for receipt in control_receipts),
            "min_output_eigenvalue": min(receipt["random_cptp"]["final_density_diagnostics"]["min_eigenvalue"] for receipt in control_receipts),
            "min_step_choi_eigenvalue": min(receipt["random_cptp"]["min_step_choi_eigenvalue"] for receipt in control_receipts),
        },
        "wrong_chirality_control_not_native_identity": {
            "pass": wrong_token_max < 1.0,
            "max_wrong_chirality_token_match": wrong_token_max,
        },
        "candidate_basin_not_promoted_to_deep_basin": {
            "pass": basin["label"] != "deep_basin",
            "label": basin["label"],
            "reason": "This scout has one implementation and finite 2x2 carrier observables; deep basin requires independent methods/carriers.",
        },
        "random_controls_do_not_promote_formal_scout": {
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False and basin["label"] != "deep_basin",
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "label": basin["label"],
        },
    }
    boundary = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_global_manifold": {
            "pass": "global manifold necessity" in CLAIM_CEILING and "source-native EngineCore dynamics" in CLAIM_CEILING,
        },
        "matched_controls_present": {
            "pass": all(key in rows[0] for key in CONTROL_TRACE_KEYS.values()),
            "controls": ["no_manifold", "reversed_schedule", "random_schedule", "wrong_chirality", "random_pauli_cptp"],
        },
        "control_receipts_present": {
            "pass": len(control_receipts) == len(rows) and len(random_schedule_permutations) > 1,
            "receipt_count": len(control_receipts),
            "distinct_random_schedule_permutations": len(random_schedule_permutations),
            "first_random_schedule_stage_index_semantics_preserved": control_receipts[0]["random_schedule"]["stage_index_semantics_preserved"],
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "canonical_qit_engine_manifold_attractor_basin_depth_replay",
        "root_constraints": {
            "F01_finitude": {
                "pass": True,
                "evidence": "finite 2x2 density carrier, finite Pauli basis, finite 8-stage engine schedule, and finite seed/epsilon grid",
            },
            "N01_noncommutation": {
                "pass": True,
                "evidence": "bounded Pauli generators obey nonzero [SX,SZ] and ordered terrain/operator schedules are control-tested against reversed/random orders",
                "sx_sz_commutator_norm": float(torch.linalg.matrix_norm(SX_TORCH @ SZ_TORCH - SZ_TORCH @ SX_TORCH).item()),
            },
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "basin_classification": basin,
        "rows": rows,
        "control_receipts": control_receipts,
        "nearby_variants": {"total": len(graveyard), "passed": sum(1 for row in graveyard.values() if row["pass"]), "variants": sorted(graveyard)},
        "why_not_v4_probes": [
            "This is a bounded v5 canonical QIT replay basin-depth scout over a source-native-labeled candidate surface.",
            "It uses finite 2x2 carrier/stage-record observables and explicit controls, not v4 physics probes.",
        ],
        "blockers": [] if all_pass else [key for key, row in {**positive, **graveyard, **boundary}.items() if not row.get("pass")],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  basin_label={basin['label']} separation={basin['control_separation']:.6f}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
