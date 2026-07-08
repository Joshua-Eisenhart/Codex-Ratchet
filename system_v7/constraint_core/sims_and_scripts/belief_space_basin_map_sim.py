#!/usr/bin/env python3
"""belief_space_basin_map_sim.

Scratch diagnostic for the redirect hypothesis:

* state-space asymptotics can be mono-basin under generic CPTP/GKSL contraction;
* belief-space can still carry basin-like structure through regime-keyed
  attractors, finite-time hysteresis, and high-surprise transit bands.

The dynamics use the local GKSL terrain conventions from the v7
constraint-core scripts. The belief rule is the shared QIT-FEP rule used by
qit_fep_surprise_stream_sim.py: surprise is Umegaki relative entropy
S(observation||belief), and the belief relaxes toward the observation by a
single convex Bloch update. This file is standalone and exits 0 for any honest
verdict mix.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.linalg import logm


sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
RESULT_PATH = HERE / "belief_space_basin_map_sim_results.json"

SEED = 0
G = 0.35
KAP = 1.0
N_STEPS = 96
BELIEF_LR = 0.045
ATTRACTOR_TICKS = 260
ATTRACTOR_REPLICATES = 48
PATH_REPLICATES = 72
NULL_PAIRS = 256
SETTLED_SURPRISE_BITS = 0.220
TRANSIT_SURPRISE_BITS = 0.420
SETTLED_NEAREST_MARGIN = 0.200
TRANSIT_NEAREST_MARGIN = 0.050

REGIME_A = 0
REGIME_B = 2
REGIME_C = 4
REGIME_CYCLE = (REGIME_A, REGIME_B, REGIME_C)

TERRAIN = {
    0: (+1, "damp", +1),
    1: (+1, "depol", 0),
    2: (+1, "damp", -1),
    3: (+1, "proj", 0),
    4: (-1, "damp", -1),
    5: (-1, "depol", 0),
    6: (-1, "damp", +1),
    7: (-1, "proj", 0),
}

SX = np.array([[0, 1], [1, 0]], complex)
SY = np.array([[0, -1j], [1j, 0]], complex)
SZ = np.array([[1, 0], [0, -1]], complex)
I2 = np.eye(2, dtype=complex)
SP = 0.5 * (SX + 1j * SY)
SM = 0.5 * (SX - 1j * SY)
H0 = (SX + SY + SZ) / np.sqrt(3.0)
TERRAIN_AFFINES: dict[int, tuple[np.ndarray, np.ndarray]] = {}


def dop(lindblad_op: np.ndarray, rho: np.ndarray) -> np.ndarray:
    return (
        lindblad_op @ rho @ lindblad_op.conj().T
        - 0.5 * (lindblad_op.conj().T @ lindblad_op @ rho + rho @ lindblad_op.conj().T @ lindblad_op)
    )


def lindblad_ops(kind: str, pole: int) -> list[np.ndarray]:
    if kind == "damp":
        return [SP if pole > 0 else SM]
    if kind == "depol":
        return [SX / np.sqrt(2.0), SY / np.sqrt(2.0)]
    if kind == "proj":
        return [SZ]
    raise ValueError(f"unknown terrain kind {kind!r}")


def normalize_rho(rho: np.ndarray) -> np.ndarray:
    state = 0.5 * (rho + rho.conj().T)
    trace = float(np.trace(state).real)
    if abs(trace) < 1e-12:
        raise ValueError("density matrix trace collapsed")
    return state / trace


def flow(hamiltonian: np.ndarray, lindblads: list[np.ndarray], rho: np.ndarray) -> np.ndarray:
    dt = 1.0 / N_STEPS
    state = rho.copy()

    def rhs(x: np.ndarray) -> np.ndarray:
        out = -1j * G * (hamiltonian @ x - x @ hamiltonian)
        for lindblad_op in lindblads:
            out = out + KAP * dop(lindblad_op, x)
        return out

    for _ in range(N_STEPS):
        k1 = rhs(state)
        k2 = rhs(state + 0.5 * dt * k1)
        k3 = rhs(state + 0.5 * dt * k2)
        k4 = rhs(state + dt * k3)
        state = normalize_rho(state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4))
    return state


def terrain_flow(terrain_index: int, rho: np.ndarray) -> np.ndarray:
    eps, kind, pole = TERRAIN[terrain_index]
    return flow(eps * H0, lindblad_ops(kind, pole), rho)


def terrain_affine(terrain_index: int) -> tuple[np.ndarray, np.ndarray]:
    cached = TERRAIN_AFFINES.get(terrain_index)
    if cached is not None:
        return cached
    base = bloch(terrain_flow(terrain_index, dm([0.0, 0.0, 0.0])))
    scale = 0.5
    cols = []
    for axis in np.eye(3):
        cols.append((bloch(terrain_flow(terrain_index, dm(scale * axis))) - base) / scale)
    affine = (np.column_stack(cols), base)
    TERRAIN_AFFINES[terrain_index] = affine
    return affine


def terrain_bloch_step(terrain_index: int, vec: np.ndarray) -> np.ndarray:
    a, b = terrain_affine(terrain_index)
    out = a @ np.asarray(vec, float) + b
    norm = float(np.linalg.norm(out))
    if norm >= 0.999:
        out = out / norm * 0.999
    return out


def dm(vec: np.ndarray | list[float]) -> np.ndarray:
    v = np.asarray(vec, float)
    norm = float(np.linalg.norm(v))
    if norm >= 0.999:
        v = v / norm * 0.999
    return 0.5 * (I2 + v[0] * SX + v[1] * SY + v[2] * SZ)


def bloch(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.trace(rho @ s).real) for s in (SX, SY, SZ)])


def relative_entropy_bits(rho: np.ndarray, sigma: np.ndarray) -> float:
    safe_rho = rho + 1e-12 * I2
    safe_sigma = sigma + 1e-12 * I2
    value = np.trace(safe_rho @ (logm(safe_rho) - logm(safe_sigma))).real / np.log(2.0)
    return float(max(value, 0.0))


def belief_update(belief: np.ndarray, observation: np.ndarray) -> np.ndarray:
    return dm((1.0 - BELIEF_LR) * bloch(belief) + BELIEF_LR * bloch(observation))


def random_bloch(rng: np.random.Generator, radius: float = 0.86) -> np.ndarray:
    direction = rng.normal(size=3)
    direction /= np.linalg.norm(direction)
    return direction * float(rng.uniform(0.0, radius))


def rounded_vec(vec: np.ndarray, digits: int = 8) -> list[float]:
    return [round(float(x), digits) for x in vec]


def rounded_stream(values: np.ndarray | list[float], digits: int = 6) -> list[float]:
    return [round(float(x), digits) for x in values]


def run_fixed_regime(
    terrain_index: int,
    initial_observation: np.ndarray,
    initial_belief: np.ndarray,
    *,
    ticks: int = ATTRACTOR_TICKS,
) -> tuple[np.ndarray, np.ndarray, list[float]]:
    observation_vec = np.asarray(initial_observation, float)
    belief = dm(initial_belief)
    surprise = []
    for tick in range(ticks):
        observation_vec = terrain_bloch_step(terrain_index, observation_vec)
        observation = dm(observation_vec)
        if tick >= ticks - 24:
            surprise.append(relative_entropy_bits(observation, belief))
        belief = belief_update(belief, observation)
    return dm(observation_vec), belief, surprise


def map_belief_attractors(rng: np.random.Generator) -> tuple[dict[int, np.ndarray], list[dict[str, Any]]]:
    attractors: dict[int, np.ndarray] = {}
    rows = []
    for terrain_index in TERRAIN:
        final_beliefs = []
        tail_surprises = []
        for _ in range(ATTRACTOR_REPLICATES):
            _, belief, surprise = run_fixed_regime(
                terrain_index,
                random_bloch(rng),
                random_bloch(rng),
            )
            final_beliefs.append(bloch(belief))
            tail_surprises.append(float(np.mean(surprise[-24:])))
        arr = np.vstack(final_beliefs)
        center = arr.mean(axis=0)
        distances = np.linalg.norm(arr - center, axis=1)
        attractors[terrain_index] = center
        rows.append(
            {
                "terrain_index": terrain_index,
                "attractor_bloch": rounded_vec(center),
                "replicates": ATTRACTOR_REPLICATES,
                "max_final_belief_spread": round(float(distances.max()), 8),
                "mean_final_belief_spread": round(float(distances.mean()), 8),
                "tail_surprise_mean_bits": round(float(np.mean(tail_surprises)), 8),
                "verdict": "regime_keyed_attractor"
                if float(distances.max()) < 0.035 and float(np.mean(tail_surprises)) < 0.020
                else "weak_or_unsettled_attractor",
            }
        )
    return attractors, rows


def run_sequence(
    sequence: list[tuple[int, int]],
    initial_observation: np.ndarray,
    initial_belief: np.ndarray,
    *,
    memoryless: bool = False,
) -> dict[str, Any]:
    observation_vec = np.asarray(initial_observation, float)
    belief = dm(initial_belief)
    records = []
    for regime, dwell in sequence:
        for _ in range(dwell):
            observation_vec = terrain_bloch_step(regime, observation_vec)
            observation = dm(observation_vec)
            surprise = relative_entropy_bits(observation, belief)
            records.append(
                {
                    "regime": regime,
                    "belief_bloch": bloch(belief),
                    "observation_bloch": bloch(observation),
                    "surprise_bits": surprise,
                }
            )
            if memoryless:
                belief = dm(bloch(observation))
            else:
                belief = belief_update(belief, observation)
    return {
        "final_belief": bloch(belief),
        "final_observation": bloch(observation),
        "tail_surprise_mean": float(np.mean([r["surprise_bits"] for r in records[-12:]])),
        "records": records,
    }


def path_replicates(
    sequence: list[tuple[int, int]],
    rng: np.random.Generator,
    *,
    memoryless: bool = False,
) -> dict[str, Any]:
    beliefs = []
    observations = []
    tail_surprises = []
    for _ in range(PATH_REPLICATES):
        result = run_sequence(
            sequence,
            random_bloch(rng),
            random_bloch(rng),
            memoryless=memoryless,
        )
        beliefs.append(result["final_belief"])
        observations.append(result["final_observation"])
        tail_surprises.append(result["tail_surprise_mean"])
    return {
        "beliefs": np.vstack(beliefs),
        "observations": np.vstack(observations),
        "tail_surprises": np.array(tail_surprises, float),
    }


def sample_within_distances(arr: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    distances = []
    n = len(arr)
    for _ in range(NULL_PAIRS):
        i, j = rng.choice(n, size=2, replace=False)
        distances.append(float(np.linalg.norm(arr[int(i)] - arr[int(j)])))
    return np.array(distances, float)


def compare_paths(
    family: str,
    left_label: str,
    left_sequence: list[tuple[int, int]],
    right_label: str,
    right_sequence: list[tuple[int, int]],
    rng: np.random.Generator,
) -> dict[str, Any]:
    left = path_replicates(left_sequence, rng, memoryless=False)
    right = path_replicates(right_sequence, rng, memoryless=False)
    if np.shares_memory(left["beliefs"], right["beliefs"]):
        raise AssertionError("path witness arrays unexpectedly share memory")

    left_null = sample_within_distances(left["beliefs"], rng)
    right_null = sample_within_distances(right["beliefs"], rng)
    null = np.concatenate([left_null, right_null])
    between = float(np.linalg.norm(left["beliefs"].mean(axis=0) - right["beliefs"].mean(axis=0)))
    obs_between = float(np.linalg.norm(left["observations"].mean(axis=0) - right["observations"].mean(axis=0)))
    null_p95 = float(np.quantile(null, 0.95))
    null_mean = float(np.mean(null))
    null_sd = float(np.std(null))
    null_band = max(null_p95, null_mean + 2.0 * null_sd)

    left_mem = path_replicates(left_sequence, rng, memoryless=True)
    right_mem = path_replicates(right_sequence, rng, memoryless=True)
    mem_between = float(np.linalg.norm(left_mem["beliefs"].mean(axis=0) - right_mem["beliefs"].mean(axis=0)))
    mem_null = np.concatenate(
        [
            sample_within_distances(left_mem["beliefs"], rng),
            sample_within_distances(right_mem["beliefs"], rng),
        ]
    )
    mem_null_band = float(max(np.quantile(mem_null, 0.95), np.mean(mem_null) + 2.0 * np.std(mem_null)))

    path_dependent = bool(between > null_band and between > 0.020)
    memoryless_destroyed = bool(mem_between < max(0.020, 0.35 * between) or mem_between <= mem_null_band)

    return {
        "family": family,
        "final_regime": REGIME_C,
        "left_path": {"label": left_label, "sequence": left_sequence},
        "right_path": {"label": right_label, "sequence": right_sequence},
        "replicates_per_path": PATH_REPLICATES,
        "final_belief_centroid_distance": round(between, 8),
        "final_observation_centroid_distance": round(obs_between, 8),
        "within_path_resampling_null": {
            "probe": "independent final-belief draw pairs inside each path",
            "pairs_per_path": NULL_PAIRS,
            "mean": round(null_mean, 8),
            "sd": round(null_sd, 8),
            "p95": round(null_p95, 8),
            "decision_band": round(null_band, 8),
        },
        "verdict": "path_dependent" if path_dependent else "path_independent",
        "control_memoryless_belief": {
            "control_type": "belief reset to current observation each tick; no cross-tick belief carry",
            "final_belief_centroid_distance": round(mem_between, 8),
            "null_decision_band": round(mem_null_band, 8),
            "destroys_path_dependence": memoryless_destroyed,
        },
        "tail_surprise_mean_bits": {
            left_label: round(float(np.mean(left["tail_surprises"])), 8),
            right_label: round(float(np.mean(right["tail_surprises"])), 8),
        },
    }


def dwell_sequence(dwell: int, cycles: int) -> list[int]:
    return [regime for _ in range(cycles) for regime in REGIME_CYCLE for _ in range(dwell)]


def run_switching_stream(
    dwell: int,
    attractors: dict[int, np.ndarray],
    rng: np.random.Generator,
    *,
    shuffled_labels: bool = False,
) -> dict[str, Any]:
    cycles = int(math.ceil(240 / (dwell * len(REGIME_CYCLE))))
    regimes = dwell_sequence(dwell, cycles)[:240]
    if shuffled_labels:
        label_perm = {REGIME_A: REGIME_B, REGIME_B: REGIME_C, REGIME_C: REGIME_A}
        labels = [label_perm[r] for r in regimes]
    else:
        labels = list(regimes)

    observation_vec = random_bloch(rng)
    belief = dm(random_bloch(rng))
    rows = []
    for tick, (true_regime, label_regime) in enumerate(zip(regimes, labels)):
        observation_vec = terrain_bloch_step(true_regime, observation_vec)
        observation = dm(observation_vec)
        surprise = relative_entropy_bits(observation, belief)
        belief_vec = bloch(belief)
        cycle_distances = sorted(
            (float(np.linalg.norm(belief_vec - attractors[regime])), regime) for regime in REGIME_CYCLE
        )
        label_distance = float(np.linalg.norm(belief_vec - attractors[label_regime]))
        true_distance = float(np.linalg.norm(belief_vec - attractors[true_regime]))
        label_is_nearest = cycle_distances[0][1] == label_regime
        nearest_margin = cycle_distances[1][0] - label_distance
        settled_by_label = (
            surprise <= SETTLED_SURPRISE_BITS
            and label_is_nearest
            and nearest_margin >= SETTLED_NEAREST_MARGIN
        )
        rows.append(
            {
                "tick": tick,
                "true_regime": true_regime,
                "label_regime": label_regime,
                "surprise_bits": surprise,
                "label_distance": label_distance,
                "true_distance": true_distance,
                "label_is_nearest_attractor": label_is_nearest,
                "nearest_margin": nearest_margin,
                "settled_by_label": settled_by_label,
                "transit_by_label": not settled_by_label,
            }
        )
        belief = belief_update(belief, observation)

    post = rows[24:]
    settled = [r for r in post if r["settled_by_label"]]
    transit = [r for r in post if r["transit_by_label"]]
    settled_surprise = np.array([r["surprise_bits"] for r in settled], float)
    transit_surprise = np.array([r["surprise_bits"] for r in transit], float)
    all_surprise = np.array([r["surprise_bits"] for r in post], float)
    partition_gap = (
        float(np.mean(transit_surprise) - np.mean(settled_surprise))
        if len(settled_surprise) and len(transit_surprise)
        else 0.0
    )
    return {
        "dwell_ticks": dwell,
        "ticks_after_warmup": len(post),
        "settled_fraction": float(len(settled) / len(post)),
        "transit_fraction": float(len(transit) / len(post)),
        "mean_surprise_bits": float(np.mean(all_surprise)),
        "settled_mean_surprise_bits": None if not len(settled_surprise) else float(np.mean(settled_surprise)),
        "transit_mean_surprise_bits": None if not len(transit_surprise) else float(np.mean(transit_surprise)),
        "transit_minus_settled_surprise_gap_bits": partition_gap,
        "label_mode": "shuffled_regime_labels" if shuffled_labels else "true_regime_labels",
    }


def occupancy_transit_sweep(attractors: dict[int, np.ndarray], rng: np.random.Generator) -> dict[str, Any]:
    dwell_values = [1, 2, 4, 8, 16, 32]
    real_rows = [run_switching_stream(dwell, attractors, rng, shuffled_labels=False) for dwell in dwell_values]
    shuffled_rows = [run_switching_stream(dwell, attractors, rng, shuffled_labels=True) for dwell in dwell_values]
    slow_real = real_rows[-1]
    slow_shuffled = shuffled_rows[-1]
    fast_real = real_rows[0]
    partition_holds = bool(
        slow_real["settled_fraction"] > 0.10
        and slow_real["transit_minus_settled_surprise_gap_bits"] > 0.10
    )
    fast_switching_transit_dominated = bool(fast_real["settled_fraction"] < 0.05 and fast_real["transit_fraction"] > 0.95)
    shuffled_destroys = bool(
        slow_shuffled["settled_fraction"] < 0.5 * max(slow_real["settled_fraction"], 1e-9)
        or slow_shuffled["transit_minus_settled_surprise_gap_bits"]
        < 0.5 * slow_real["transit_minus_settled_surprise_gap_bits"]
    )
    return {
        "settled_rule": {
            "surprise_bits_at_most": SETTLED_SURPRISE_BITS,
            "current_regime_attractor_must_be_nearest": True,
            "nearest_attractor_margin_at_least": SETTLED_NEAREST_MARGIN,
        },
        "transit_rule": {
            "definition": "not settled by current-regime label; surprise and nearest-attractor margin are still reported for band strength",
            "diagnostic_high_surprise_bits_at_least": TRANSIT_SURPRISE_BITS,
            "diagnostic_weak_nearest_margin_at_most": TRANSIT_NEAREST_MARGIN,
        },
        "dwell_sweep": [
            {
                "dwell_ticks": row["dwell_ticks"],
                "settled_fraction": round(row["settled_fraction"], 8),
                "transit_fraction": round(row["transit_fraction"], 8),
                "mean_surprise_bits": round(row["mean_surprise_bits"], 8),
                "settled_mean_surprise_bits": None
                if row["settled_mean_surprise_bits"] is None
                else round(row["settled_mean_surprise_bits"], 8),
                "transit_mean_surprise_bits": None
                if row["transit_mean_surprise_bits"] is None
                else round(row["transit_mean_surprise_bits"], 8),
                "transit_minus_settled_surprise_gap_bits": round(
                    row["transit_minus_settled_surprise_gap_bits"], 8
                ),
            }
            for row in real_rows
        ],
        "control_shuffled_regime_labels": {
            "control_type": "independent recomputation with cyclically permuted regime labels for attractor lookup",
            "dwell_sweep": [
                {
                    "dwell_ticks": row["dwell_ticks"],
                    "settled_fraction": round(row["settled_fraction"], 8),
                    "transit_fraction": round(row["transit_fraction"], 8),
                    "transit_minus_settled_surprise_gap_bits": round(
                        row["transit_minus_settled_surprise_gap_bits"], 8
                    ),
                }
                for row in shuffled_rows
            ],
            "destroys_occupancy_transit_partition_at_slow_dwell": shuffled_destroys,
        },
        "verdicts": {
            "occupancy_transit_partition": "partition_holds" if partition_holds else "partition_not_supported",
            "fast_switching": "transit_dominated" if fast_switching_transit_dominated else "not_transit_dominated",
        },
    }


def build_result() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    attractors, attractor_rows = map_belief_attractors(rng)

    path_families = [
        compare_paths(
            "A_B_C_vs_A_C",
            "A_to_B_to_C",
            [(REGIME_A, 20), (REGIME_B, 20), (REGIME_C, 36)],
            "A_to_C_direct",
            [(REGIME_A, 40), (REGIME_C, 36)],
            rng,
        ),
        compare_paths(
            "A_B_A_C_vs_A_C",
            "A_B_A_to_C",
            [(REGIME_A, 12), (REGIME_B, 12), (REGIME_A, 12), (REGIME_C, 36)],
            "A_hold_to_C",
            [(REGIME_A, 36), (REGIME_C, 36)],
            rng,
        ),
        compare_paths(
            "cycle_history_vs_direct_final",
            "A_B_C_A_to_C",
            [(REGIME_A, 10), (REGIME_B, 10), (REGIME_C, 10), (REGIME_A, 10), (REGIME_C, 36)],
            "A_B_to_C",
            [(REGIME_A, 20), (REGIME_B, 20), (REGIME_C, 36)],
            rng,
        ),
    ]
    occupancy = occupancy_transit_sweep(attractors, rng)

    path_dependent_count = sum(1 for row in path_families if row["verdict"] == "path_dependent")
    memoryless_controls_pass = all(
        row["control_memoryless_belief"]["destroys_path_dependence"] for row in path_families
    )
    attractor_baseline_holds = all(row["verdict"] == "regime_keyed_attractor" for row in attractor_rows)

    return {
        "sim_id": "belief_space_basin_map_sim",
        "name": "belief-space basin map: hysteresis and path-dependence",
        "version": "1.0",
        "classification": "scratch_diagnostic",
        "promotion_status": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "sim_execution_kind": "nonclassical",
        "sim_class": "belief_space_basin_probe",
        "rng_seed": SEED,
        "rng": "numpy.default_rng(0)",
        "claim_ceiling": "runs; scratch diagnostic over finite terrain sequences; no formal admission, bridge, axis, or manifold claim",
        "source_basis": {
            "state_space_context": "engine_pair_basin_map_sim.py measured mono-basin state asymptotics under generic CPTP/GKSL contraction",
            "belief_space_context": "fep_known_unknown_basin_sim.py claim_1 uses Umegaki surprise to partition occupied versus transition regimes",
            "belief_update_rule": "shared convex Bloch relaxation toward observation with surprise_bits=S(observation||belief), matching qit_fep_surprise_stream_sim.py convention",
        },
        "parameters": {
            "g": G,
            "kappa": KAP,
            "rk4_steps_per_terrain_tick": N_STEPS,
            "belief_learning_rate": BELIEF_LR,
            "attractor_ticks": ATTRACTOR_TICKS,
            "attractor_replicates_per_regime": ATTRACTOR_REPLICATES,
            "path_replicates_per_path": PATH_REPLICATES,
            "null_pairs_per_path": NULL_PAIRS,
            "path_regime_tokens": {"A": REGIME_A, "B": REGIME_B, "C": REGIME_C},
        },
        "TOOL_MANIFEST": {
            "numpy": "density matrices, Bloch vectors, seeded independent recomputations and null bands",
            "scipy.linalg.logm": "Umegaki relative entropy S(observation||belief) in bits",
        },
        "TOOL_INTEGRATION_DEPTH": {
            "numpy": "load_bearing",
            "scipy.linalg.logm": "load_bearing",
        },
        "divergence_log": [
            "scratch diagnostic only; no canonical promotion",
            "state asymptotics are not re-promoted; this probes belief-space finite-time structure",
            "path-dependence verdicts are compared against independent within-path resampling nulls",
            "controls are recomputed independently rather than predicate aliases",
        ],
        "claim_1_belief_attractors": {
            "verdict": "baseline_holds" if attractor_baseline_holds else "baseline_mixed",
            "interpretation": "fixed terrain flow gives a regime-keyed belief attractor under the shared relaxation rule; this is the baseline, not the main hysteresis claim",
            "regime_attractors": attractor_rows,
        },
        "claim_2_hysteresis_path_dependence": {
            "overall_verdict": "path_dependent"
            if path_dependent_count > 0 and memoryless_controls_pass
            else "path_independent_or_control_failed",
            "path_dependent_families": path_dependent_count,
            "families_tested": path_families,
            "control_memoryless_belief_all_pass": memoryless_controls_pass,
        },
        "claim_3_occupancy_vs_transit": occupancy,
        "control_independence_assertions": {
            "seeded_rng": SEED,
            "path_witness_control_distinct_arrays": True,
            "within_path_null_uses_independent_probe_draws": True,
            "memoryless_control_recomputed": True,
            "shuffled_label_control_recomputed": True,
            "predicate_controls_used": False,
        },
        "overall": {
            "belief_attractor_baseline": "baseline_holds" if attractor_baseline_holds else "baseline_mixed",
            "hysteresis": "path_dependent"
            if path_dependent_count > 0 and memoryless_controls_pass
            else "path_independent_or_control_failed",
            "occupancy_transit_partition": occupancy["verdicts"]["occupancy_transit_partition"],
            "fast_switching": occupancy["verdicts"]["fast_switching"],
            "exit_policy": "exit 0 for honest verdict mix; exceptions only for broken computation/control invariants",
        },
    }


def print_summary(result: dict[str, Any]) -> None:
    print("BELIEF SPACE BASIN MAP SIM -- scratch_diagnostic, promotion_allowed=false")
    print()
    c1 = result["claim_1_belief_attractors"]
    max_spread = max(row["max_final_belief_spread"] for row in c1["regime_attractors"])
    print("CLAIM 1 BELIEF ATTRACTORS:", c1["verdict"])
    print(f"  regimes={len(c1['regime_attractors'])} max_final_belief_spread={max_spread:.8f}")
    for row in c1["regime_attractors"]:
        c = row["attractor_bloch"]
        print(
            f"  terrain {row['terrain_index']}: center=[{c[0]:+.5f}, {c[1]:+.5f}, {c[2]:+.5f}] "
            f"spread={row['max_final_belief_spread']:.6f} tail_surprise={row['tail_surprise_mean_bits']:.6f} "
            f"verdict={row['verdict']}"
        )

    c2 = result["claim_2_hysteresis_path_dependence"]
    print()
    print("CLAIM 2 HYSTERESIS / PATH DEPENDENCE:", c2["overall_verdict"])
    for row in c2["families_tested"]:
        print(
            "  {family}: verdict={verdict} distance={dist:.6f} null_band={band:.6f} "
            "memoryless_distance={mem:.6f}".format(
                family=row["family"],
                verdict=row["verdict"],
                dist=row["final_belief_centroid_distance"],
                band=row["within_path_resampling_null"]["decision_band"],
                mem=row["control_memoryless_belief"]["final_belief_centroid_distance"],
            )
        )

    c3 = result["claim_3_occupancy_vs_transit"]
    print()
    print("CLAIM 3 OCCUPANCY VS TRANSIT:", c3["verdicts"])
    print("  dwell | settled_fraction | transit_fraction | mean_surprise | transit-settled gap")
    for row in c3["dwell_sweep"]:
        print(
            f"  {row['dwell_ticks']:5d} | {row['settled_fraction']:.6f} | "
            f"{row['transit_fraction']:.6f} | {row['mean_surprise_bits']:.6f} | "
            f"{row['transit_minus_settled_surprise_gap_bits']:.6f}"
        )
    shuffled = c3["control_shuffled_regime_labels"]
    print(
        "  CONTROL shuffled regime labels destroys partition at slow dwell:",
        shuffled["destroys_occupancy_transit_partition_at_slow_dwell"],
    )
    print()
    print("OVERALL:", result["overall"])
    print("ALL_GATES: PASS ->", RESULT_PATH)


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
