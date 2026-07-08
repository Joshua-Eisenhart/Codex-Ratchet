#!/usr/bin/env python3
"""FEP known/unknown basin sim v2.

Scratch diagnostic hardening round for the 2026-07-07 audit:

* Claim 1 basin=known is preserved from v1 unchanged.
* Claim 2 is repaired: both engines use one shared update rule, one shared
  learning rate, one shared code path, and identical tick counts. The only
  engine parameter is the actual stage schedule loaded from the source JSONs.
* Claim 3 drive coupling is kept downstream of the repaired schedule-only
  instrument.

No game-outcome labels are used as testable referents here.
"""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.linalg import expm, logm


HERE = Path(__file__).resolve().parent
STAGE_JOIN_PATH = HERE / "stage_token_join.json"
SOURCE_STAGE_SLOTS_PATH = (
    HERE.parent
    / "reference_docs"
    / "engine_math"
    / "source_schedule_tables"
    / "engine_16_source_stage_slots.json"
)
RESULT_PATH = HERE / "fep_known_unknown_basin_v2_sim_results.json"
BOOKENDS_V2_PATH = HERE / "engine_pair_axes_axis0_bookends_v2_sim.py"

SX = np.array([[0, 1], [1, 0]], complex)
SY = np.array([[0, -1j], [1j, 0]], complex)
SZ = np.array([[1, 0], [0, -1]], complex)
I2 = np.eye(2, dtype=complex)
SP = 0.5 * (SX + 1j * SY)
SM = 0.5 * (SX - 1j * SY)
H0 = (SX + SY + SZ) / np.sqrt(3.0)
G = 0.35
KAP = 1.0
Q = 1 - np.exp(-1)
TH = np.pi / 4
NS = 160
SEED = 0
SHARED_LR = 0.62
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "nonclassical"
TOOL_MANIFEST = {
    "numpy": {
        "used": True,
        "reason": "density matrices, Bloch readouts, seeded independent controls",
    },
    "scipy.linalg.expm": {
        "used": True,
        "reason": "unitary operator maps inside engine stages",
    },
    "scipy.linalg.logm": {
        "used": True,
        "reason": "Umegaki relative entropy S(observation||belief)",
    },
    "stage_token_join.json": {
        "used": True,
        "reason": "structural schedule token source for engine-pair GKSL stage ordering",
    },
    "engine_16_source_stage_slots.json": {
        "used": True,
        "reason": "source schedule table cross-check for actual 4-stage loop compositions",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy.linalg.logm": "load_bearing",
    "scipy.linalg.expm": "supportive",
    "stage_token_join.json": "load_bearing",
    "engine_16_source_stage_slots.json": "load_bearing",
}

LOOP_ORDER = {
    "Type1_left": ("O", "I"),
    "Type2_right": ("O", "I"),
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def schedule_from_stage_join() -> dict[str, list[dict[str, Any]]]:
    payload = load_json(STAGE_JOIN_PATH)
    source_rows = {row["slot_id"]: row for row in load_json(SOURCE_STAGE_SLOTS_PATH)}
    rows = []
    for row in payload["stage_join"]:
        source_slot_id = row["source_slot_id"]
        source_row = source_rows[source_slot_id]
        if row["canonical_token"] != source_row["canonical_token"]:
            raise AssertionError(f"token mismatch for {source_slot_id}")
        if row["operator"] != source_row["canonical_operator"]:
            raise AssertionError(f"operator mismatch for {source_slot_id}")
        engine_short, loop_step = source_slot_id.split("-")
        loop_tag = loop_step[0]
        step = int(loop_step[1:])
        engine = "Type1_left" if engine_short == "T1" else "Type2_right"
        rows.append(
            {
                "source_slot_id": source_slot_id,
                "engine": engine,
                "loop_tag": loop_tag,
                "loop_name": source_row["loop"],
                "step": step,
                "terrain_index": int(row["terrain_index"]),
                "operator": row["operator"],
                "axis6_sign": row["axis6_sign"],
                "canonical_token": row["canonical_token"],
                "canonical_math": source_row["canonical_math"],
                "source_line_range": row["source_line_range"],
            }
        )

    schedule: dict[str, list[dict[str, Any]]] = {"Type1_left": [], "Type2_right": []}
    for engine in schedule:
        loop_order = LOOP_ORDER[engine]
        selected = [row for row in rows if row["engine"] == engine]
        selected.sort(key=lambda row: (loop_order.index(row["loop_tag"]), row["step"]))
        if len(selected) != 8:
            raise ValueError(f"{engine} schedule has {len(selected)} slots, expected 8")
        schedule[engine] = selected
    return schedule


def terrain_tuple(terrain_index: int) -> tuple[int, str, int]:
    terrains = {
        0: (+1, "damp", +1),
        1: (+1, "depol", 0),
        2: (+1, "damp", -1),
        3: (+1, "proj", 0),
        4: (-1, "damp", -1),
        5: (-1, "depol", 0),
        6: (-1, "damp", +1),
        7: (-1, "proj", 0),
    }
    return terrains[terrain_index]


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
    return [SZ]


def flow(hamiltonian: np.ndarray, lindblads: list[np.ndarray], rho: np.ndarray, steps: int = NS) -> np.ndarray:
    dt = 1.0 / steps

    def x_dot(state: np.ndarray) -> np.ndarray:
        out = -1j * G * (hamiltonian @ state - state @ hamiltonian)
        for lindblad_op in lindblads:
            out = out + KAP * dop(lindblad_op, state)
        return out

    state = rho.copy()
    for _ in range(steps):
        k1 = x_dot(state)
        k2 = x_dot(state + 0.5 * dt * k1)
        k3 = x_dot(state + 0.5 * dt * k2)
        k4 = x_dot(state + dt * k3)
        state = state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        state = 0.5 * (state + state.conj().T)
        state /= np.trace(state).real
    return state


def terrain_flow(terrain_index: int, rho: np.ndarray) -> np.ndarray:
    eps, kind, pole = terrain_tuple(terrain_index)
    return flow(eps * H0, lindblad_ops(kind, pole), rho)


def op(name: str):
    p0 = 0.5 * (I2 + SZ)
    p1 = 0.5 * (I2 - SZ)
    qp = 0.5 * (I2 + SX)
    qm = 0.5 * (I2 - SX)
    if name == "Ti":
        return lambda rho: (1 - Q) * rho + Q * (p0 @ rho @ p0 + p1 @ rho @ p1)
    if name == "Te":
        return lambda rho: (1 - Q) * rho + Q * (qp @ rho @ qp + qm @ rho @ qm)
    if name == "Fi":
        u = expm(-1j * TH / 2.0 * SX)
        return lambda rho: u @ rho @ u.conj().T
    if name == "Fe":
        u = expm(-1j * TH / 2.0 * SZ)
        return lambda rho: u @ rho @ u.conj().T
    raise ValueError(f"unknown operator {name}")


def step(slot: dict[str, Any], rho: np.ndarray) -> np.ndarray:
    operator = op(slot["operator"])
    terrain_index = int(slot["terrain_index"])
    if slot["axis6_sign"] == "up":
        return terrain_flow(terrain_index, operator(rho.copy()))
    return operator(terrain_flow(terrain_index, rho.copy()))


def dm(vec: np.ndarray | list[float]) -> np.ndarray:
    v = np.array(vec, float)
    norm = float(np.linalg.norm(v))
    if norm >= 0.999:
        v = v / norm * 0.999
    return 0.5 * (I2 + v[0] * SX + v[1] * SY + v[2] * SZ)


def bloch(rho: np.ndarray) -> np.ndarray:
    return np.array([np.trace(rho @ s).real for s in (SX, SY, SZ)])


def entropy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh(rho)
    vals = vals[vals > 1e-12]
    return float(-(vals * np.log2(vals)).sum())


def relative_entropy_bits(rho: np.ndarray, sigma: np.ndarray) -> float:
    safe_rho = rho + 1e-12 * I2
    safe_sigma = sigma + 1e-12 * I2
    value = np.trace(safe_rho @ (logm(safe_rho) - logm(safe_sigma))).real / np.log(2.0)
    return float(max(value, 0.0))


def belief_update(belief: np.ndarray, observation: np.ndarray, lr: float) -> np.ndarray:
    return dm((1.0 - lr) * bloch(belief) + lr * bloch(observation))


def pair_surprise(left_obs: np.ndarray, left_belief: np.ndarray, right_obs: np.ndarray, right_belief: np.ndarray) -> float:
    return 0.5 * (
        relative_entropy_bits(left_obs, left_belief) + relative_entropy_bits(right_obs, right_belief)
    )


def run_pair_basin_stream(
    schedule: dict[str, list[dict[str, Any]]],
    *,
    shuffled_labels: bool = False,
    rng: np.random.Generator,
) -> dict[str, Any]:
    left = dm([0.55, 0.18, 0.21])
    right = dm([-0.47, 0.16, -0.24])
    left_beliefs = [dm([0.0, 0.0, 0.0]) for _ in range(8)]
    right_beliefs = [dm([0.0, 0.0, 0.0]) for _ in range(8)]
    surprise = []
    tick_roles = []
    switch_tick = 24
    transition_span = 8
    n_ticks = 56
    for tick in range(n_ticks):
        transitioned = tick >= switch_tick
        left_slots = schedule["Type2_right"] if transitioned else schedule["Type1_left"]
        right_slots = schedule["Type1_left"] if transitioned else schedule["Type2_right"]
        phase = tick % 8
        left = step(left_slots[phase], left)
        right = step(right_slots[phase], right)
        surprise.append(pair_surprise(left, left_beliefs[phase], right, right_beliefs[phase]))
        in_transition = switch_tick <= tick < switch_tick + transition_span
        in_occupied = (16 <= tick < switch_tick) or (switch_tick + 16 <= tick < n_ticks)
        if in_transition:
            tick_roles.append("transition")
        elif in_occupied:
            tick_roles.append("occupied")
        else:
            tick_roles.append("warmup")
        left_beliefs[phase] = belief_update(left_beliefs[phase], left, 0.72)
        right_beliefs[phase] = belief_update(right_beliefs[phase], right, 0.72)

    labels = list(tick_roles)
    if shuffled_labels:
        eligible = [idx for idx, label in enumerate(labels) if label in {"occupied", "transition"}]
        shuffled = [labels[idx] for idx in eligible]
        rng.shuffle(shuffled)
        for idx, label in zip(eligible, shuffled):
            labels[idx] = label

    arr = np.array(surprise, float)
    occupied = arr[[label == "occupied" for label in labels]]
    transition = arr[[label == "transition" for label in labels]]
    return {
        "surprise": arr,
        "tick_roles": labels,
        "occupied_mean": float(np.mean(occupied)),
        "transition_mean": float(np.mean(transition)),
        "partition_gap": float(np.mean(transition) - np.mean(occupied)),
        "pre_occupied_mean": float(np.mean(arr[16:20])),
        "late_occupied_mean": float(np.mean(arr[20:24])),
        "post_relearn_mean": float(np.mean(arr[40:56])),
    }


def cycle_drop_rate(values: np.ndarray, first: tuple[int, int], second: tuple[int, int]) -> float:
    left = np.asarray(values[first[0] : first[1]], float)
    right = np.asarray(values[second[0] : second[1]], float)
    if len(left) == 0 or len(right) == 0:
        return 0.0
    return float(max(np.mean(left) - np.mean(right), 0.0) / max(len(right), 1))


def run_schedule_refinement_stream(
    schedule_slots: list[dict[str, Any]],
    modeled_initial_vec: np.ndarray,
    novel_initial_vec: np.ndarray,
    *,
    lr: float = SHARED_LR,
) -> dict[str, Any]:
    observation = dm(modeled_initial_vec.copy())
    novel_observation = dm(novel_initial_vec.copy())
    beliefs = [dm([0.0, 0.0, 0.0]) for _ in range(8)]
    novel_tick = 24
    n_ticks = 48
    surprise = []

    for tick in range(n_ticks):
        if tick == novel_tick:
            observation = novel_observation.copy()
        phase = tick % len(schedule_slots)
        observation = step(schedule_slots[phase], observation)
        surprise.append(relative_entropy_bits(observation, beliefs[phase]))
        beliefs[phase] = belief_update(beliefs[phase], observation, lr)

    arr = np.array(surprise, float)
    return {
        "surprise": arr,
        "within_basin_reduction_rate": cycle_drop_rate(arr, (0, 8), (16, 24)),
        "post_novelty_relearn_rate": cycle_drop_rate(arr, (24, 32), (32, 40)),
        "novelty_spike": float(np.max(arr[novel_tick : novel_tick + 4])),
        "tail_mean": float(np.mean(arr[novel_tick + 12 : n_ticks])),
    }


def evaluate_schedule_split(
    type1_schedule: list[dict[str, Any]],
    type2_schedule: list[dict[str, Any]],
    *,
    modeled_initial_vec: np.ndarray,
    novel_initial_vec: np.ndarray,
    lr: float = SHARED_LR,
) -> dict[str, Any]:
    type1 = run_schedule_refinement_stream(
        type1_schedule,
        np.array(modeled_initial_vec, float).copy(),
        np.array(novel_initial_vec, float).copy(),
        lr=lr,
    )
    type2 = run_schedule_refinement_stream(
        type2_schedule,
        np.array(modeled_initial_vec, float).copy(),
        np.array(novel_initial_vec, float).copy(),
        lr=lr,
    )
    if np.shares_memory(type1["surprise"], type2["surprise"]):
        raise AssertionError("schedule split streams unexpectedly share memory")

    known_gap = type1["within_basin_reduction_rate"] - type2["within_basin_reduction_rate"]
    novelty_gap = type2["post_novelty_relearn_rate"] - type1["post_novelty_relearn_rate"]
    split_threshold = 0.005
    if known_gap > split_threshold and novelty_gap > split_threshold:
        verdict = "allocation-split-holds"
    elif known_gap < -split_threshold and novelty_gap < -split_threshold:
        verdict = "reversed"
    else:
        verdict = "no-split"
    return {
        "type1": type1,
        "type2": type2,
        "known_gap_type1_minus_type2": float(known_gap),
        "novelty_gap_type2_minus_type1": float(novelty_gap),
        "split_threshold_bits_per_tick": split_threshold,
        "shared_learning_rate": float(lr),
        "verdict": verdict,
    }


def schedule_erasure_control(
    schedule: dict[str, list[dict[str, Any]]],
    *,
    modeled_initial_vec: np.ndarray,
    novel_initial_vec: np.ndarray,
) -> dict[str, Any]:
    schedule_a = copy.deepcopy(schedule["Type1_left"])
    schedule_b = copy.deepcopy(schedule["Type1_left"])
    modeled_a = np.array(modeled_initial_vec, float).copy()
    modeled_b = np.array(modeled_initial_vec, float).copy()
    novel_a = np.array(novel_initial_vec, float).copy()
    novel_b = np.array(novel_initial_vec, float).copy()
    assertions = {
        "schedule_objects_distinct_identity": schedule_a is not schedule_b,
        "schedule_values_equal": schedule_a == schedule_b,
        "modeled_initial_objects_distinct_identity": modeled_a is not modeled_b,
        "modeled_initial_values_equal": bool(np.array_equal(modeled_a, modeled_b)),
        "novel_initial_objects_distinct_identity": novel_a is not novel_b,
        "novel_initial_values_equal": bool(np.array_equal(novel_a, novel_b)),
    }
    if not all(assertions.values()):
        raise AssertionError(f"schedule erasure independent-input assertion failed: {assertions}")
    metrics = evaluate_schedule_split(
        schedule_a,
        schedule_b,
        modeled_initial_vec=modeled_a,
        novel_initial_vec=novel_a,
    )
    return {
        "control_type": "same_schedule_independent_recomputations",
        "assert_distinct_paths": assertions,
        "known_gap_actual": metrics["known_gap_type1_minus_type2"],
        "novelty_gap_actual": metrics["novelty_gap_type2_minus_type1"],
        "collapsed": bool(
            abs(metrics["known_gap_type1_minus_type2"]) < 1e-12
            and abs(metrics["novelty_gap_type2_minus_type1"]) < 1e-12
        ),
        "metrics": metrics,
    }


def shuffled_schedule_control(
    schedule: dict[str, list[dict[str, Any]]],
    *,
    modeled_initial_vec: np.ndarray,
    novel_initial_vec: np.ndarray,
    rng: np.random.Generator,
) -> dict[str, Any]:
    shuffled: dict[str, list[dict[str, Any]]] = {}
    for engine in ("Type1_left", "Type2_right"):
        indices = rng.permutation(len(schedule[engine]))
        shuffled[engine] = [copy.deepcopy(schedule[engine][int(idx)]) for idx in indices]
    metrics = evaluate_schedule_split(
        shuffled["Type1_left"],
        shuffled["Type2_right"],
        modeled_initial_vec=np.array(modeled_initial_vec, float).copy(),
        novel_initial_vec=np.array(novel_initial_vec, float).copy(),
    )
    return {
        "control_type": "random_stage_order_within_each_engine",
        "rng_seed": SEED,
        "type1_shuffled_tokens": [row["canonical_token"] for row in shuffled["Type1_left"]],
        "type2_shuffled_tokens": [row["canonical_token"] for row in shuffled["Type2_right"]],
        "metrics": metrics,
        "split_survives_scrambling": bool(metrics["verdict"] == "allocation-split-holds"),
    }


def a0_front_state_pair() -> tuple[np.ndarray, np.ndarray, float, str]:
    direction = np.array([0.35, -0.22, 0.91], float)
    direction /= np.linalg.norm(direction)
    growth = 0.28 * direction
    record = -0.70 * direction
    h_axis = np.array([1.0, 1.0, 1.0], float) / np.sqrt(3.0)
    cross_term = float(np.dot(np.cross(growth, record), h_axis))
    alignment = float(np.dot(growth - record, h_axis))
    factor = 1.0 + 0.35 * np.tanh(3.0 * cross_term) + 0.20 * np.tanh(2.0 * alignment)
    front = float((entropy(dm(growth)) - entropy(dm(record))) * factor)
    if BOOKENDS_V2_PATH.exists():
        interpretation = (
            "engine_pair_axes_axis0_bookends_v2_sim.py present; installed a0-front interpretation follows its "
            "growth-polarity higher-entropy state versus record/lock lower-entropy state before dynamics."
        )
    else:
        interpretation = (
            "bookends v2 absent; installed fallback is a simple two-polarity entropy-gradient initialization."
        )
    return growth, record, front, interpretation


def no_gradient_state_pair() -> tuple[np.ndarray, np.ndarray]:
    left = np.array([0.34, 0.0, 0.0], float)
    right = np.array([0.0, -0.34, 0.0], float)
    if np.shares_memory(left, right):
        raise AssertionError("no-gradient control states unexpectedly share memory")
    if np.linalg.norm(left - right) <= 1e-9:
        raise AssertionError("no-gradient control states are not distinct")
    if abs(entropy(dm(left)) - entropy(dm(right))) > 1e-12:
        raise AssertionError("no-gradient control states are not equal entropy")
    return left, right


def rounded_stream(values: np.ndarray, digits: int = 6) -> list[float]:
    return [round(float(value), digits) for value in values]


def compact_schedule_metrics(allocation: dict[str, Any], include_streams: bool = True) -> dict[str, Any]:
    def compact_engine(row: dict[str, Any]) -> dict[str, Any]:
        out = {
            "within_basin_surprise_reduction_rate": round(row["within_basin_reduction_rate"], 8),
            "post_novelty_relearn_rate": round(row["post_novelty_relearn_rate"], 8),
            "novelty_spike_bits": round(row["novelty_spike"], 8),
            "tail_mean_bits": round(row["tail_mean"], 8),
        }
        if include_streams:
            out["surprise_bits"] = rounded_stream(row["surprise"], 6)
        return out

    return {
        "type1_schedule": compact_engine(allocation["type1"]),
        "type2_schedule": compact_engine(allocation["type2"]),
        "known_gap_type1_minus_type2": round(allocation["known_gap_type1_minus_type2"], 8),
        "novelty_gap_type2_minus_type1": round(allocation["novelty_gap_type2_minus_type1"], 8),
        "split_threshold_bits_per_tick": round(allocation["split_threshold_bits_per_tick"], 8),
        "shared_learning_rate": round(allocation["shared_learning_rate"], 8),
        "verdict": allocation["verdict"],
    }


def schedule_summary(schedule: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return {
        engine: {
            "tokens": [row["canonical_token"] for row in rows],
            "slot_ids": [row["source_slot_id"] for row in rows],
            "four_stage_loops": {
                loop_name: [row["canonical_token"] for row in rows if row["loop_name"] == loop_name]
                for loop_name in sorted({row["loop_name"] for row in rows})
            },
        }
        for engine, rows in schedule.items()
    }


def run() -> dict[str, Any]:
    schedule = schedule_from_stage_join()

    basin_real = run_pair_basin_stream(schedule, shuffled_labels=False, rng=np.random.default_rng(SEED + 1))
    basin_control = run_pair_basin_stream(schedule, shuffled_labels=True, rng=np.random.default_rng(SEED + 2))
    if np.shares_memory(basin_real["surprise"], basin_control["surprise"]):
        raise AssertionError("basin witness/control surprise arrays share memory")
    basin_partition_holds = bool(
        basin_real["partition_gap"] > 0.40
        and basin_real["partition_gap"] > 3.0 * max(abs(basin_control["partition_gap"]), 1e-9)
        and basin_real["late_occupied_mean"] < basin_real["pre_occupied_mean"]
        and basin_real["post_relearn_mean"] < 0.35 * basin_real["transition_mean"]
    )

    modeled_initial = np.array([0.21, -0.13, 0.37], float)
    novel_initial = np.array([-0.38, 0.22, -0.19], float)
    schedule_allocation = evaluate_schedule_split(
        schedule["Type1_left"],
        schedule["Type2_right"],
        modeled_initial_vec=modeled_initial,
        novel_initial_vec=novel_initial,
    )
    erasure = schedule_erasure_control(
        schedule,
        modeled_initial_vec=modeled_initial,
        novel_initial_vec=novel_initial,
    )
    shuffled = shuffled_schedule_control(
        schedule,
        modeled_initial_vec=modeled_initial,
        novel_initial_vec=novel_initial,
        rng=np.random.default_rng(SEED),
    )

    gradient_modeled, gradient_novel, a0_front, installed_interpretation = a0_front_state_pair()
    no_grad_modeled, no_grad_novel = no_gradient_state_pair()
    if np.shares_memory(gradient_modeled, no_grad_modeled) or np.shares_memory(gradient_novel, no_grad_novel):
        raise AssertionError("gradient witness and no-gradient control share memory")

    allocation_gradient = evaluate_schedule_split(
        schedule["Type1_left"],
        schedule["Type2_right"],
        modeled_initial_vec=gradient_modeled,
        novel_initial_vec=gradient_novel,
    )
    allocation_no_gradient = evaluate_schedule_split(
        schedule["Type1_left"],
        schedule["Type2_right"],
        modeled_initial_vec=no_grad_modeled,
        novel_initial_vec=no_grad_novel,
    )
    shift_known = (
        allocation_gradient["known_gap_type1_minus_type2"]
        - allocation_no_gradient["known_gap_type1_minus_type2"]
    )
    shift_novelty = (
        allocation_gradient["novelty_gap_type2_minus_type1"]
        - allocation_no_gradient["novelty_gap_type2_minus_type1"]
    )
    shift_norm = math.sqrt(shift_known * shift_known + shift_novelty * shift_novelty)
    drive_coupling_verdict = "shift-detected" if shift_norm > 0.03 else "no-measured-shift"

    result = {
        "sim_id": "fep_known_unknown_basin_v2_sim",
        "name": "known/unknown as FEP on attractor basin structure, schedule-only hardening",
        "version": "2.0",
        "classification": "scratch_diagnostic",
        "promotion_status": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "sim_execution_kind": "nonclassical",
        "sim_class": "basin_fep_probe",
        "rng_seed": SEED,
        "repair_note": {
            "refuted_v1_claim_2": "v1 allocation split used hardcoded learning-rate constants keyed to loop_profile labels.",
            "v2_rule": "The two engine streams differ only by actual schedules; one code path, one update rule, one shared learning rate, same tick counts.",
            "honest_verdicts": ["allocation-split-holds", "no-split", "reversed"],
        },
        "source_sections": {
            "UP-99B": {
                "path": "system_v7/constraint_core/sims_and_scripts/win_lose_as_known_unknown_fep_sim.py",
                "section": "part B method-level result: Type-1 tests the modeled regime; Type-2 explores unmodeled regimes; erased Type-2 control goes to chance",
                "reuse": "bidirectional-science allocation machinery only; outcome labels are not test referents",
            },
            "UP-97": {
                "path": "system_v7/constraint_core/sims_and_scripts/qit_fep_surprise_stream_sim.py",
                "section": "Umegaki surprise stream S(observation||belief) in bits",
                "reuse": "relative-entropy signal and stream partition gates",
            },
            "UP-94": {
                "path": "system_v7/constraint_core/sims_and_scripts/unified_attractor_basin_seven_axes_sim.py",
                "section": "engine-pair GKSL basin substrate and nested engine schedules",
                "reuse": "terrain flow, operator precedence, Type1/Type2 engine pair schedules",
            },
            "owner_definitions_2026_07_07": {
                "known": "well-modeled / low expected surprise; belief predicts; occupied basin",
                "unknown": "high surprise / model-class gap; basin exit or transition",
            },
        },
        "schedule_source": {
            "stage_join_path": str(STAGE_JOIN_PATH.relative_to(HERE.parents[2])),
            "source_stage_slots_path": str(SOURCE_STAGE_SLOTS_PATH.relative_to(HERE.parents[2])),
            "loaded_and_cross_checked": True,
            "schedules": schedule_summary(schedule),
        },
        "TOOL_MANIFEST": {
            "numpy": "density matrices, Bloch readouts, seeded independent controls",
            "scipy.linalg.expm": "unitary operator maps inside engine stages",
            "scipy.linalg.logm": "Umegaki relative entropy S(observation||belief)",
            "stage_token_join.json": "structural schedule token source for engine-pair GKSL stage ordering",
            "engine_16_source_stage_slots.json": "source schedule table cross-check for actual 4-stage loop compositions",
        },
        "TOOL_INTEGRATION_DEPTH": {
            "numpy": "load_bearing",
            "scipy.linalg.logm": "load_bearing",
            "scipy.linalg.expm": "supportive",
            "stage_token_join.json": "load_bearing",
            "engine_16_source_stage_slots.json": "load_bearing",
        },
        "divergence_log": [
            "scratch diagnostic only; no canonical promotion",
            "v2 Claim 2 removes loop-profile learning-rate labels as causal variables",
            "controls are independent recomputations, not predicate aliases",
            "result supports local rerun evidence only",
        ],
        "claim_1_basin_known": {
            "verdict": "basin-partition-holds" if basin_partition_holds else "basin-partition-not-supported",
            "surprise_measure": "Umegaki relative entropy S(observation||belief) in bits",
            "witness": {
                "occupied_mean_bits": round(basin_real["occupied_mean"], 8),
                "transition_mean_bits": round(basin_real["transition_mean"], 8),
                "transition_minus_occupied_gap_bits": round(basin_real["partition_gap"], 8),
                "pre_occupied_mean_bits": round(basin_real["pre_occupied_mean"], 8),
                "late_occupied_mean_bits": round(basin_real["late_occupied_mean"], 8),
                "post_relearn_mean_bits": round(basin_real["post_relearn_mean"], 8),
                "stream_bits": rounded_stream(basin_real["surprise"], 6),
                "tick_roles": basin_real["tick_roles"],
            },
            "control_shuffled_tick_labels": {
                "control_type": "independent_recompute_then_shuffle_partition_labels",
                "occupied_mean_bits": round(basin_control["occupied_mean"], 8),
                "transition_mean_bits": round(basin_control["transition_mean"], 8),
                "transition_minus_occupied_gap_bits": round(basin_control["partition_gap"], 8),
                "destroys_partition": bool(
                    abs(basin_control["partition_gap"]) < basin_real["partition_gap"] / 3.0
                ),
            },
        },
        "claim_2_schedule_allocation": {
            "verdict": schedule_allocation["verdict"],
            "instrument": {
                "shared_learning_rate": SHARED_LR,
                "shared_update_rule": "belief <- dm((1-lr)*bloch(belief) + lr*bloch(observation))",
                "shared_code_path": "run_schedule_refinement_stream",
                "engine_parameter_only": "schedule_slots loaded from source schedule JSON",
                "n_ticks": 48,
                "novel_tick": 24,
                "modeled_initial_vec": rounded_stream(modeled_initial, 8),
                "novel_initial_vec": rounded_stream(novel_initial, 8),
            },
            "witness": compact_schedule_metrics(schedule_allocation, include_streams=True),
            "control_schedule_erasure_same_schedule": {
                "control_type": erasure["control_type"],
                "assert_distinct_paths": erasure["assert_distinct_paths"],
                "collapsed": erasure["collapsed"],
                "known_gap_actual": round(erasure["known_gap_actual"], 12),
                "novelty_gap_actual": round(erasure["novelty_gap_actual"], 12),
                "metrics": compact_schedule_metrics(erasure["metrics"], include_streams=False),
            },
            "control_shuffled_schedule": {
                "control_type": shuffled["control_type"],
                "rng_seed": shuffled["rng_seed"],
                "type1_shuffled_tokens": shuffled["type1_shuffled_tokens"],
                "type2_shuffled_tokens": shuffled["type2_shuffled_tokens"],
                "split_survives_scrambling": shuffled["split_survives_scrambling"],
                "metrics": compact_schedule_metrics(shuffled["metrics"], include_streams=False),
            },
        },
        "claim_3_drive_coupling": {
            "installed_interpretation": installed_interpretation,
            "verdict": drive_coupling_verdict,
            "downstream_of_repaired_instrument": True,
            "gradient_initialization": {
                "modeled_vec": rounded_stream(gradient_modeled, 8),
                "novel_vec": rounded_stream(gradient_novel, 8),
                "modeled_entropy_bits": round(entropy(dm(gradient_modeled)), 12),
                "novel_entropy_bits": round(entropy(dm(gradient_novel)), 12),
                "a0_front_unfused": [round(a0_front, 12)],
                "allocation": compact_schedule_metrics(allocation_gradient, include_streams=False),
            },
            "no_gradient_control": {
                "control_type": "two_distinct_equal_entropy_states_as_common_modeled_and_novel_inputs",
                "modeled_vec": rounded_stream(no_grad_modeled, 8),
                "novel_vec": rounded_stream(no_grad_novel, 8),
                "modeled_entropy_bits": round(entropy(dm(no_grad_modeled)), 12),
                "novel_entropy_bits": round(entropy(dm(no_grad_novel)), 12),
                "distinct_arrays": bool(not np.shares_memory(no_grad_modeled, no_grad_novel)),
                "distinct_states": bool(np.linalg.norm(no_grad_modeled - no_grad_novel) > 1e-9),
                "equal_entropy": bool(abs(entropy(dm(no_grad_modeled)) - entropy(dm(no_grad_novel))) < 1e-12),
                "allocation": compact_schedule_metrics(allocation_no_gradient, include_streams=False),
            },
            "measured_shift": {
                "known_gap_shift": round(shift_known, 8),
                "novelty_gap_shift": round(shift_novelty, 8),
                "shift_norm": round(shift_norm, 8),
            },
            "A0_like_quantities_stay_unfused_lists": [
                {"name": "a0_front", "values": [round(a0_front, 12)]}
            ],
        },
        "control_independence_assertions": {
            "seeded_rng": SEED,
            "basin_witness_control_distinct_arrays": True,
            "schedule_erasure_uses_distinct_equal_inputs": erasure["assert_distinct_paths"],
            "gradient_vs_no_gradient_distinct_arrays": True,
            "no_gradient_uses_two_distinct_equal_entropy_states": True,
            "predicate_controls_used": False,
        },
        "overall": {
            "claim_1": "basin-partition-holds" if basin_partition_holds else "basin-partition-not-supported",
            "claim_2": schedule_allocation["verdict"],
            "claim_2_control_collapsed": erasure["collapsed"],
            "claim_2_shuffled_control": shuffled["metrics"]["verdict"],
            "claim_3": drive_coupling_verdict,
            "exit_policy": "exit 0 for honest verdict mix; exceptions only for broken computation/control invariants",
        },
    }
    return result


def print_summary(result: dict[str, Any]) -> None:
    c1 = result["claim_1_basin_known"]
    c2 = result["claim_2_schedule_allocation"]
    c3 = result["claim_3_drive_coupling"]
    print("FEP KNOWN/UNKNOWN BASIN V2 SIM -- scratch_diagnostic, promotion_allowed=false")
    print("Repair: Claim 2 is schedule-only; same lr/update/tick counts/code path.")
    print()
    print("CLAIM 1 BASIN=KNOWN VERDICT:", c1["verdict"], "(preserved from v1 machinery)")
    print(
        "  occupied_mean={:.6f} transition_mean={:.6f} gap={:.6f} post_relearn={:.6f}".format(
            c1["witness"]["occupied_mean_bits"],
            c1["witness"]["transition_mean_bits"],
            c1["witness"]["transition_minus_occupied_gap_bits"],
            c1["witness"]["post_relearn_mean_bits"],
        )
    )
    print("CLAIM 2 SCHEDULE-ONLY ALLOCATION VERDICT:", c2["verdict"])
    if c2["verdict"] == "no-split":
        print("  Honest outcome: no-split under the repaired instrument.")
    print(
        "  Type1 schedule within-basin rate={:.6f} post-novelty rate={:.6f}".format(
            c2["witness"]["type1_schedule"]["within_basin_surprise_reduction_rate"],
            c2["witness"]["type1_schedule"]["post_novelty_relearn_rate"],
        )
    )
    print(
        "  Type2 schedule within-basin rate={:.6f} post-novelty rate={:.6f}".format(
            c2["witness"]["type2_schedule"]["within_basin_surprise_reduction_rate"],
            c2["witness"]["type2_schedule"]["post_novelty_relearn_rate"],
        )
    )
    print(
        "  known_gap={:.6f} novelty_gap={:.6f} threshold={:.6f}".format(
            c2["witness"]["known_gap_type1_minus_type2"],
            c2["witness"]["novelty_gap_type2_minus_type1"],
            c2["witness"]["split_threshold_bits_per_tick"],
        )
    )
    print("CLAIM 3 DRIVE COUPLING VERDICT:", c3["verdict"])
    print(
        "  known_gap_shift={:.6f} novelty_gap_shift={:.6f} shift_norm={:.6f}".format(
            c3["measured_shift"]["known_gap_shift"],
            c3["measured_shift"]["novelty_gap_shift"],
            c3["measured_shift"]["shift_norm"],
        )
    )
    print()
    print("CONTROL TABLE")
    print(
        "  shuffled_tick_labels: gap={:.6f} destroys_partition={}".format(
            c1["control_shuffled_tick_labels"]["transition_minus_occupied_gap_bits"],
            c1["control_shuffled_tick_labels"]["destroys_partition"],
        )
    )
    erased = c2["control_schedule_erasure_same_schedule"]
    print(
        "  schedule_erasure_same_schedule: collapsed={} known_gap_actual={:.12f} novelty_gap_actual={:.12f}".format(
            erased["collapsed"],
            erased["known_gap_actual"],
            erased["novelty_gap_actual"],
        )
    )
    shuffled = c2["control_shuffled_schedule"]
    print(
        "  shuffled_schedule: verdict={} split_survives_scrambling={} known_gap={:.6f} novelty_gap={:.6f}".format(
            shuffled["metrics"]["verdict"],
            shuffled["split_survives_scrambling"],
            shuffled["metrics"]["known_gap_type1_minus_type2"],
            shuffled["metrics"]["novelty_gap_type2_minus_type1"],
        )
    )
    ng = c3["no_gradient_control"]
    print(
        "  no_gradient_distinct_equal_entropy: distinct_states={} equal_entropy={} baseline_known_gap={:.6f} baseline_novelty_gap={:.6f}".format(
            ng["distinct_states"],
            ng["equal_entropy"],
            ng["allocation"]["known_gap_type1_minus_type2"],
            ng["allocation"]["novelty_gap_type2_minus_type1"],
        )
    )
    print()
    print("ALL_GATES: PASS/RUNS ->", RESULT_PATH)


def main() -> int:
    result = run()
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print_summary(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
