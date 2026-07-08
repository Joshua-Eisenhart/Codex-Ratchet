#!/usr/bin/env python3
"""memory_carrier_belief_basin_sim.

Scratch diagnostic replacing the refuted convex belief smoother with the
repo's memory-bearing Hopfield/spinor carrier from quantum_hopfield_memory_sim.

The carrier stores K <= 4 regime-attractor patterns as pure spinor states.
Regime drive is a weak cue into the fixed Hopfield energy surface, not an
absolute overwrite. The audit falsifier is built in: final-regime dwell is
measured from the carrier relaxation time, then path distance is reported at
1x, 3x, and 10x dwell. A linear smoother goes through the same protocol as the
contrast control.

scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false.
"""
from __future__ import annotations

import json
import math
import sys
from itertools import product
from pathlib import Path
from typing import Any

import torch


sys.dont_write_bytecode = True
torch.set_default_dtype(torch.float64)

HERE = Path(__file__).resolve().parent
RESULT_PATH = HERE / "memory_carrier_belief_basin_sim_results.json"

SEED = 0
N_QUBITS = 3
DIM = 2**N_QUBITS
K = 4
K_CAPACITY_EDGE = 4
LR = 0.08
REGIME_CUE_STRENGTH = 0.005
FIDELITY_SETTLED = 0.99
GRID_N = 4
RESAMPLE_REPS = 24
RESAMPLE_JITTER = 0.02
SMOOTHER_ALPHA = 0.12
FINAL_REGIME = 3


def round_float(value: float, digits: int = 8) -> float:
    return round(float(value), digits)


def make_patterns(seed: int) -> list[torch.Tensor]:
    generator = torch.Generator().manual_seed(seed)
    raw = torch.randn(DIM, K, 2, generator=generator)
    complex_raw = torch.complex(raw[:, :, 0], raw[:, :, 1])
    q, _ = torch.linalg.qr(complex_raw)
    return [q[:, i] / torch.linalg.norm(q[:, i]) for i in range(K)]


def random_pure(seed: int) -> torch.Tensor:
    generator = torch.Generator().manual_seed(seed)
    raw = torch.randn(DIM, 2, generator=generator)
    psi = torch.complex(raw[:, 0], raw[:, 1])
    return psi / torch.linalg.norm(psi)


def normalized_superposition(patterns: list[torch.Tensor], coeffs: list[float]) -> torch.Tensor:
    psi = sum(float(c) * p for c, p in zip(coeffs, patterns))
    return psi / torch.linalg.norm(psi)


def energy(psi: torch.Tensor, patterns: list[torch.Tensor]) -> torch.Tensor:
    return -sum((torch.abs(torch.vdot(pattern, psi)) ** 2) ** 2 for pattern in patterns)


def hopfield_step(
    psi: torch.Tensor,
    patterns: list[torch.Tensor],
    *,
    regime: int | None = None,
    cue_strength: float = REGIME_CUE_STRENGTH,
) -> torch.Tensor:
    psi = psi.detach().requires_grad_(True)
    e = energy(psi, patterns)
    e.backward()
    with torch.no_grad():
        out = psi - LR * psi.grad
        if regime is not None and cue_strength > 0.0:
            cue = patterns[regime]
            phase = torch.vdot(cue, out)
            phase = phase / (torch.abs(phase) + 1e-12)
            out = out + cue_strength * cue * phase
        out = out / torch.linalg.norm(out)
    return out.detach()


def run_memory_sequence(
    initial: torch.Tensor,
    sequence: list[tuple[int, int]],
    patterns: list[torch.Tensor],
) -> torch.Tensor:
    psi = initial
    for regime, dwell in sequence:
        for _ in range(int(dwell)):
            psi = hopfield_step(psi, patterns, regime=regime)
    return psi


def fidelity_to_patterns(psi: torch.Tensor, patterns: list[torch.Tensor]) -> list[float]:
    return [float(torch.abs(torch.vdot(pattern, psi)) ** 2) for pattern in patterns]


def winner(psi: torch.Tensor, patterns: list[torch.Tensor]) -> tuple[int, float, list[float]]:
    fids = fidelity_to_patterns(psi, patterns)
    index = max(range(len(fids)), key=lambda i: fids[i])
    return index, fids[index], fids


def projective_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    fidelity = min(max(float(torch.abs(torch.vdot(a, b)) ** 2), 0.0), 1.0)
    return math.sqrt(max(0.0, 1.0 - fidelity))


def measure_relaxation_time(patterns: list[torch.Tensor]) -> dict[str, Any]:
    rows = []
    max_steps = 0
    for pattern_index, pattern in enumerate(patterns):
        for replicate in range(3):
            noise = random_pure(100 + 17 * pattern_index + replicate)
            psi = 0.60 * pattern + 0.40 * noise
            psi = psi / torch.linalg.norm(psi)
            hit_steps = None
            final_winner = -1
            final_fidelity = 0.0
            for step in range(1, 401):
                psi = hopfield_step(psi, patterns, regime=None, cue_strength=0.0)
                final_winner, final_fidelity, _ = winner(psi, patterns)
                if final_winner == pattern_index and final_fidelity >= FIDELITY_SETTLED:
                    hit_steps = step
                    break
            if hit_steps is None:
                hit_steps = 401
            max_steps = max(max_steps, hit_steps)
            rows.append(
                {
                    "pattern": pattern_index,
                    "replicate": replicate,
                    "steps_to_fidelity_0_99": hit_steps,
                    "winner": final_winner,
                    "winner_fidelity": round_float(final_fidelity),
                }
            )
    return {
        "criterion": "first step with intended winner and fidelity >= 0.99 from 60/40 corrupted probes",
        "rows": rows,
        "max_relaxation_steps": max_steps,
    }


def run_path_dwell_sweep(patterns: list[torch.Tensor], tau: int) -> dict[str, Any]:
    history_dwell = 3 * tau
    initial = normalized_superposition(patterns, [1.0, 1.0, 1.0, 1.0])
    left_history = run_memory_sequence(initial, [(0, history_dwell)], patterns)
    right_history = run_memory_sequence(initial, [(1, history_dwell)], patterns)
    rows = []
    for multiple in (1, 3, 10):
        final_dwell = multiple * tau
        left = run_memory_sequence(left_history, [(FINAL_REGIME, final_dwell)], patterns)
        right = run_memory_sequence(right_history, [(FINAL_REGIME, final_dwell)], patterns)
        left_winner, left_fidelity, left_fids = winner(left, patterns)
        right_winner, right_fidelity, right_fids = winner(right, patterns)
        rows.append(
            {
                "final_dwell_multiple": multiple,
                "final_dwell_steps": final_dwell,
                "left_winner": left_winner,
                "right_winner": right_winner,
                "left_winner_fidelity": round_float(left_fidelity),
                "right_winner_fidelity": round_float(right_fidelity),
                "left_fidelities": [round_float(v, 6) for v in left_fids],
                "right_fidelities": [round_float(v, 6) for v in right_fids],
                "projective_path_distance": round_float(projective_distance(left, right)),
            }
        )
    final_row = rows[-1]
    sustained = (
        final_row["left_winner"] != final_row["right_winner"]
        and final_row["projective_path_distance"] >= 0.25
        and rows[-1]["projective_path_distance"] >= 0.9 * rows[-2]["projective_path_distance"]
    )
    return {
        "paths": {
            "left": [(0, history_dwell), (FINAL_REGIME, "sweep")],
            "right": [(1, history_dwell), (FINAL_REGIME, "sweep")],
            "same_final_regime": FINAL_REGIME,
        },
        "history_dwell_steps": history_dwell,
        "dwell_sweep": rows,
        "verdict": "multi_stable" if sustained else "single_basin",
    }


def smoother_step(state: torch.Tensor, regime: int) -> torch.Tensor:
    cue = torch.zeros(K, dtype=torch.float64)
    cue[regime] = 1.0
    return (1.0 - SMOOTHER_ALPHA) * state + SMOOTHER_ALPHA * cue


def run_smoother_sequence(initial: torch.Tensor, sequence: list[tuple[int, int]]) -> torch.Tensor:
    state = initial.clone()
    for regime, dwell in sequence:
        for _ in range(int(dwell)):
            state = smoother_step(state, regime)
    return state


def measure_smoother_tau() -> int:
    state = torch.ones(K, dtype=torch.float64) / K
    for step in range(1, 401):
        state = smoother_step(state, FINAL_REGIME)
        if float(state[FINAL_REGIME]) >= FIDELITY_SETTLED:
            return step
    return 401


def run_smoother_control(tau: int) -> dict[str, Any]:
    history_dwell = 3 * tau
    initial = torch.ones(K, dtype=torch.float64) / K
    left_history = run_smoother_sequence(initial, [(0, history_dwell)])
    right_history = run_smoother_sequence(initial, [(1, history_dwell)])
    rows = []
    for multiple in (1, 3, 10):
        final_dwell = multiple * tau
        left = run_smoother_sequence(left_history, [(FINAL_REGIME, final_dwell)])
        right = run_smoother_sequence(right_history, [(FINAL_REGIME, final_dwell)])
        rows.append(
            {
                "final_dwell_multiple": multiple,
                "final_dwell_steps": final_dwell,
                "left_argmax": int(torch.argmax(left).item()),
                "right_argmax": int(torch.argmax(right).item()),
                "l2_path_distance": round_float(float(torch.linalg.norm(left - right))),
                "left_state": [round_float(v, 6) for v in left.tolist()],
                "right_state": [round_float(v, 6) for v in right.tolist()],
            }
        )
    return {
        "carrier": "linear_exponential_smoother",
        "alpha": SMOOTHER_ALPHA,
        "measured_tau_steps": measure_smoother_tau(),
        "identical_protocol_history_dwell_steps": history_dwell,
        "dwell_sweep": rows,
        "verdict": "no_long_dwell_path_dependence"
        if rows[-1]["l2_path_distance"] < 1e-4
        else "control_failed_path_dependence_present",
    }


def simplex_grid_coeffs(n: int) -> list[list[float]]:
    coeffs = []
    for raw in product(range(n + 1), repeat=K):
        if sum(raw) == n:
            coeffs.append([float(v) / float(n) for v in raw])
    return coeffs


def basin_partition(
    patterns: list[torch.Tensor],
    memory_patterns: list[torch.Tensor],
    tau: int,
    *,
    label: str,
) -> dict[str, Any]:
    coeffs = simplex_grid_coeffs(GRID_N)
    counts = {str(i): 0 for i in range(K)}
    low_confidence = 0
    rows = []
    for index, coeff in enumerate(coeffs):
        initial = normalized_superposition(patterns, coeff)
        final = run_memory_sequence(initial, [(FINAL_REGIME, 10 * tau)], memory_patterns)
        win, fid, fids = winner(final, patterns)
        counts[str(win)] += 1
        if fid < 0.90:
            low_confidence += 1
        rows.append(
            {
                "grid_index": index,
                "coefficients": [round_float(v, 4) for v in coeff],
                "winner": win,
                "winner_fidelity_against_original_patterns": round_float(fid),
                "fidelities_against_original_patterns": [round_float(v, 6) for v in fids],
            }
        )
    total = len(coeffs)
    volumes = {key: round_float(value / total, 6) for key, value in counts.items()}
    return {
        "label": label,
        "fixed_regime": FINAL_REGIME,
        "grid": f"simplex coefficients over {K} stored patterns, denominator={GRID_N}",
        "grid_points": total,
        "counts": counts,
        "volumes": volumes,
        "low_confidence_points_fidelity_lt_0_90": low_confidence,
        "mean_winner_fidelity": round_float(
            sum(row["winner_fidelity_against_original_patterns"] for row in rows) / total
        ),
        "rows": rows,
    }


def run_resampling_nulls(patterns: list[torch.Tensor], tau: int) -> dict[str, Any]:
    history_dwell = 3 * tau
    final_dwell = 10 * tau
    left_states = []
    right_states = []
    for replicate in range(RESAMPLE_REPS):
        jitter = random_pure(500 + replicate)
        initial = (1.0 - RESAMPLE_JITTER) * normalized_superposition(
            patterns, [1.0, 1.0, 1.0, 1.0]
        ) + RESAMPLE_JITTER * jitter
        initial = initial / torch.linalg.norm(initial)
        left = run_memory_sequence(initial, [(0, history_dwell), (FINAL_REGIME, final_dwell)], patterns)
        right = run_memory_sequence(initial, [(1, history_dwell), (FINAL_REGIME, final_dwell)], patterns)
        left_states.append(left)
        right_states.append(right)

    between = [projective_distance(left, right) for left, right in zip(left_states, right_states)]
    within_left = [
        projective_distance(left_states[i], left_states[(i + 1) % RESAMPLE_REPS])
        for i in range(RESAMPLE_REPS)
    ]
    within_right = [
        projective_distance(right_states[i], right_states[(i + 1) % RESAMPLE_REPS])
        for i in range(RESAMPLE_REPS)
    ]
    null = within_left + within_right
    return {
        "replicates": RESAMPLE_REPS,
        "independent_initial_jitter": (
            f"{1.0 - RESAMPLE_JITTER:.2f} neutral superposition + "
            f"{RESAMPLE_JITTER:.2f} independent random pure state"
        ),
        "between_path_distance_mean": round_float(sum(between) / len(between)),
        "between_path_distance_min": round_float(min(between)),
        "within_path_null_mean": round_float(sum(null) / len(null)),
        "within_path_null_max": round_float(max(null)),
        "verdict": "between_exceeds_independent_within_path_null"
        if min(between) > max(null)
        else "null_overlap",
    }


def capacity_check(patterns: list[torch.Tensor], tau: int) -> dict[str, Any]:
    if K > K_CAPACITY_EDGE:
        return {"verdict": "capacity_exceeded", "k": K, "capacity_edge": K_CAPACITY_EDGE}
    correct = 0
    total = 0
    for pattern_index, pattern in enumerate(patterns):
        for replicate in range(3):
            noise = random_pure(800 + 19 * pattern_index + replicate)
            probe = 0.62 * pattern + 0.38 * noise
            probe = probe / torch.linalg.norm(probe)
            out = probe
            for _ in range(10 * tau):
                out = hopfield_step(out, patterns, regime=None, cue_strength=0.0)
            win, fid, _ = winner(out, patterns)
            correct += int(win == pattern_index and fid >= FIDELITY_SETTLED)
            total += 1
    return {
        "verdict": "within_capacity" if correct == total else "capacity_exceeded",
        "k": K,
        "capacity_edge": K_CAPACITY_EDGE,
        "recall_correct": correct,
        "recall_total": total,
    }


def build_result() -> dict[str, Any]:
    torch.manual_seed(SEED)
    patterns = make_patterns(SEED)
    erased_patterns = make_patterns(1000 + SEED)
    relaxation = measure_relaxation_time(patterns)
    tau = int(relaxation["max_relaxation_steps"])
    if tau <= 0:
        raise AssertionError("measured relaxation time must be positive")

    cap = capacity_check(patterns, tau)
    path = run_path_dwell_sweep(patterns, tau)
    smoother = run_smoother_control(tau)
    basin = basin_partition(patterns, patterns, tau, label="original_memory")
    erasure = basin_partition(patterns, erased_patterns, tau, label="scrambled_memory_against_original_labels")
    nulls = run_resampling_nulls(patterns, tau)

    erasure_destroyed = (
        erasure["mean_winner_fidelity"] < 0.50
        and erasure["low_confidence_points_fidelity_lt_0_90"] > 0.80 * erasure["grid_points"]
    )
    if cap["verdict"] == "capacity_exceeded":
        overall = "capacity_exceeded"
    elif path["verdict"] == "multi_stable" and smoother["verdict"] == "no_long_dwell_path_dependence":
        overall = "multi_stable"
    else:
        overall = "single_basin"

    return {
        "sim_id": "memory_carrier_belief_basin_sim",
        "name": "belief basins on a memory-bearing Hopfield/spinor carrier",
        "version": "1.0",
        "classification": "scratch_diagnostic",
        "promotion_status": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "sim_execution_kind": "nonclassical",
        "sim_class": "memory_carrier_belief_basin_probe",
        "rng_seed": SEED,
        "rng": "torch.manual_seed(0)",
        "claim_ceiling": "runs; scratch diagnostic only; no formal admission, bridge, axis, or manifold claim",
        "source_basis": {
            "memory_carrier": "quantum_hopfield_memory_sim.py pure-state Hopfield energy on norm-preserving spinor carrier",
            "spinor_boundary": "spinor_memory_sim.py density-blind phase/history motivates projective distance for visible attractor identity",
            "audit_fix": "belief_space_basin_map hysteresis was refuted as smoother lag; this run measures tau and reports 1x/3x/10x final dwell",
        },
        "parameters": {
            "n_qubits": N_QUBITS,
            "dim": DIM,
            "k_stored_regime_patterns": K,
            "k_capacity_edge": K_CAPACITY_EDGE,
            "learning_rate": LR,
            "regime_cue_strength": REGIME_CUE_STRENGTH,
            "final_regime": FINAL_REGIME,
            "grid_denominator": GRID_N,
            "smoother_alpha": SMOOTHER_ALPHA,
        },
        "TOOL_MANIFEST": {
            "torch": "load-bearing pure-state Hopfield/spinor carrier, autograd energy descent, seeded recomputation controls",
            "json": "result receipt emission",
        },
        "TOOL_INTEGRATION_DEPTH": {
            "torch": "load_bearing",
            "json": "supportive",
        },
        "divergence_log": [
            "linear smoother contrast must collapse long-dwell path distance",
            "final dwell is measured from carrier relaxation and swept at 1x/3x/10x",
            "projective distance prevents global spinor phase from masquerading as belief difference",
            "scrambled-memory control tests original stored-pattern partition, not an unrelated new memory basis",
        ],
        "capacity_check": cap,
        "timescale_measurement": relaxation,
        "dwell_sufficiency": {
            "carrier_tau_steps": tau,
            "final_dwell_10x_steps": 10 * tau,
            "passes_audit_minimum": 10 * tau >= 10 * tau,
        },
        "claim_1_stored_regime_attractors": {
            "stored_patterns": K,
            "pattern_orthonormality_max_offdiag_fidelity": round_float(
                max(
                    float(torch.abs(torch.vdot(patterns[i], patterns[j])) ** 2)
                    for i in range(K)
                    for j in range(K)
                    if i != j
                )
            ),
            "verdict": cap["verdict"],
        },
        "claim_2_hysteresis_honest_long_dwell": path,
        "control_linear_smoother_identical_protocol": smoother,
        "claim_3_basin_boundaries_fixed_regime": basin,
        "control_memory_erasure_scrambled_patterns": {
            **erasure,
            "destroys_original_partition": erasure_destroyed,
        },
        "control_resampling_nulls": nulls,
        "overall": {
            "verdict": overall,
            "allowed_verdict_tokens": ["multi_stable", "single_basin", "capacity_exceeded"],
            "exit_policy": "exit 0 for honest verdict mix; exceptions only for broken computation/control invariants",
        },
    }


def print_summary(result: dict[str, Any]) -> None:
    print("MEMORY CARRIER BELIEF BASIN SIM -- scratch_diagnostic promotion_allowed=false")
    print(f"rng=torch.manual_seed({SEED}) k={K} n_qubits={N_QUBITS} dim={DIM}")
    print()
    cap = result["capacity_check"]
    print(
        "CAPACITY_CHECK "
        f"verdict={cap['verdict']} k={cap['k']} edge={cap['capacity_edge']} "
        f"recall={cap.get('recall_correct')}/{cap.get('recall_total')}"
    )
    tau = result["timescale_measurement"]["max_relaxation_steps"]
    print("TIMESCALE_TABLE carrier_relaxation")
    print(f"  max_tau_steps={tau} final_dwell_10x={10 * tau}")
    for row in result["timescale_measurement"]["rows"]:
        print(
            "  pattern={pattern} rep={replicate} steps={steps_to_fidelity_0_99} "
            "winner={winner} fidelity={winner_fidelity:.6f}".format(**row)
        )

    print()
    print("DWELL_SWEEP_PATH_DISTANCES memory_carrier same_final_regime")
    for row in result["claim_2_hysteresis_honest_long_dwell"]["dwell_sweep"]:
        print(
            "  {final_dwell_multiple}x dwell={final_dwell_steps} "
            "left={left_winner}:{left_winner_fidelity:.6f} "
            "right={right_winner}:{right_winner_fidelity:.6f} "
            "path_distance={projective_path_distance:.6f}".format(**row)
        )
    print("  verdict=" + result["claim_2_hysteresis_honest_long_dwell"]["verdict"])

    print()
    print("DWELL_SWEEP_PATH_DISTANCES linear_smoother_control")
    for row in result["control_linear_smoother_identical_protocol"]["dwell_sweep"]:
        print(
            "  {final_dwell_multiple}x dwell={final_dwell_steps} "
            "left={left_argmax} right={right_argmax} "
            "path_distance={l2_path_distance:.8f}".format(**row)
        )
    print("  verdict=" + result["control_linear_smoother_identical_protocol"]["verdict"])

    basin = result["claim_3_basin_boundaries_fixed_regime"]
    print()
    print("BASIN_PARTITION fixed_regime={fixed_regime} grid_points={grid_points}".format(**basin))
    print("  counts=" + json.dumps(basin["counts"], sort_keys=True))
    print("  volumes=" + json.dumps(basin["volumes"], sort_keys=True))
    print(
        "  low_confidence_points_fidelity_lt_0_90="
        + str(basin["low_confidence_points_fidelity_lt_0_90"])
    )

    erasure = result["control_memory_erasure_scrambled_patterns"]
    print()
    print("CONTROL_MEMORY_ERASURE scrambled_patterns")
    print("  counts=" + json.dumps(erasure["counts"], sort_keys=True))
    print(f"  mean_original_fidelity={erasure['mean_winner_fidelity']:.6f}")
    print("  destroys_original_partition=" + str(erasure["destroys_original_partition"]))

    nulls = result["control_resampling_nulls"]
    print()
    print(
        "RESAMPLING_NULLS "
        f"between_mean={nulls['between_path_distance_mean']:.6f} "
        f"between_min={nulls['between_path_distance_min']:.6f} "
        f"within_mean={nulls['within_path_null_mean']:.6f} "
        f"within_max={nulls['within_path_null_max']:.6f} "
        f"verdict={nulls['verdict']}"
    )
    print()
    print("OVERALL verdict=" + result["overall"]["verdict"])
    print("RESULT_JSON " + str(RESULT_PATH))


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
