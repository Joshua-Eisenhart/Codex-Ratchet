#!/usr/bin/env python3
"""Fail-closed loop-2 senses retest with the verified view-local residual.

This reruns the original occluded-bit engine/twin task on the same event log,
seed, object split, feature semantics, and readouts as
``system_v8/loop2_world/perception_intelligence_v0.py``.  The candidate lane
changes only the recurrent density update:

    rho_next = 0.5 * F_view(rho_persistent) + 0.5 * F_view(rho_initial)

The original update, frozen engine, shuffled training labels, and permutation
nulls remain explicit controls.  Results are diagnostic only and cannot
promote a carrier or downstream claim.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np


REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
HERE = REPO / "system_v8" / "loop3_senses"
SOURCE = HERE / "loop2_retest_fixed_senses.py"
OUTDIR = HERE / "results" / "loop2_retest_fixed_senses"
RECEIPT_PATH = OUTDIR / "receipt.json"
TRAJECTORY_PATH = OUTDIR / "density_trajectories.json"
EVENTS = REPO / "system_v8" / "loop2_world" / "results" / "world_source" / "events_dynamics_on.jsonl"
WORLD_RECEIPT = REPO / "system_v8" / "loop2_world" / "results" / "world_source" / "receipt.json"
LOOP2_SOURCE = REPO / "system_v8" / "loop2_world" / "perception_intelligence_v0.py"
LOOP2_RECEIPT = REPO / "system_v8" / "loop2_world" / "results" / "intelligence" / "receipt.json"
STAGE64 = REPO / "system_v8" / "nested_manifold" / "results" / "stage64" / "receipt.json"
VISIBILITY_SOURCE = HERE / "visibility_sanity_gate.py"
FIX_RECEIPT = HERE / "results" / "visibility_sanity_gate_v3" / "fix_v1" / "receipt.json"
FOUNDATION_CARD = HERE / "LOOP3_FOUNDATION_CARD.md"
OBJECT_CARD = HERE / "loop2_retest_fixed_senses_v43_card.json"
SIM_PY = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")

SEED = 20260719
N_BITS = 8
N_VIEWS = 6
N_TRAIN = 44
N_BOOTSTRAPS = 5000
N_PERMUTATIONS = 200
MIN_MEMORY_FREE_PERCENT = 25
CLASSIFICATION = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density algebra, ridge readouts, object-block bootstrap confidence intervals, and permutation controls gate all_pass",
    },
    "scipy.linalg.expm": {
        "tried": True,
        "used": True,
        "reason": "load-bearing via visibility_sanity_gate.load_stage_channels: constructs the exact loop-2 GKSL/unitary channels used by every engine lane",
    },
    "torch": {
        "tried": False,
        "used": False,
        "reason": "not scoped: no JEPA training is part of this bounded engine-vs-twin retest",
    },
    "qutip": {
        "tried": False,
        "used": False,
        "reason": "not scoped: the exact diagnosed NumPy/SciPy QIT path is reused without a second runtime",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy.linalg.expm": "load_bearing",
    "torch": None,
    "qutip": None,
}


class RetestError(RuntimeError):
    """Input, provenance, or runtime failure that must fail closed."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def memory_free_percent() -> int:
    process = subprocess.run(
        ["memory_pressure"], capture_output=True, text=True, check=True
    )
    match = re.search(
        r"System-wide memory free percentage:\s*(\d+)%", process.stdout
    )
    if match is None:
        raise RetestError("memory_pressure did not report a free percentage")
    return int(match.group(1))


def refuse_to_reuse() -> None:
    if OUTDIR.exists():
        raise RetestError(f"REFUSE-TO-REUSE: outdir already exists: {OUTDIR}")


def write_fatal_receipt(message: str, memory_percent: int | None) -> None:
    receipt = {
        "schema": "loop3_senses/loop2_retest_fixed_senses/receipt_v1",
        "sim_id": "loop2_retest_fixed_senses",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": CLASSIFICATION,
        "runtime": {
            "python": sys.executable,
            "required_python": str(SIM_PY),
            "memory_free_percent": memory_percent,
            "minimum_required_percent": MIN_MEMORY_FREE_PERCENT,
            "torch_used": False,
            "qutip_used": False,
        },
        "checks": {"fatal_preflight": False},
        "all_pass": False,
        "fatal_error": message,
        "divergence_log": [
            {
                "comparison": "requested bounded retest versus fatal preflight/runtime state",
                "status": "not_completed",
                "reason": message,
            }
        ],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "fatal fail-closed diagnostic; no retest or promotion claim",
    }
    with RECEIPT_PATH.open("x") as handle:
        json.dump(receipt, handle, indent=2, allow_nan=False)


def validate_parent_fix(fix_receipt: dict[str, Any]) -> dict[str, bool]:
    inputs = fix_receipt.get("inputs", {})
    return {
        "parent_fix_schema_matches": fix_receipt.get("schema") == "loop3_senses/visibility_sanity_gate/receipt_v1",
        "parent_fix_version_matches": fix_receipt.get("version") == "3.0.0",
        "parent_fix_is_update_residual": fix_receipt.get("fix_v1_mode") == "update_residual",
        "parent_fix_all_pass": fix_receipt.get("all_pass") is True,
        "parent_fix_G1_through_G4_pass": all(
            fix_receipt.get("checks", {}).get(gate, {}).get("pass") is True
            for gate in ("G1", "G2", "G3", "G4")
        ),
        "parent_fix_promotion_is_false": fix_receipt.get("promotion_allowed") is False,
        "loop2_source_matches_parent_fix": inputs.get("engine_interface_sha256") == sha256_file(LOOP2_SOURCE),
        "visibility_source_matches_parent_fix": inputs.get("visibility_gate_source_sha256") == sha256_file(VISIBILITY_SOURCE),
        "world_events_match_parent_fix": inputs.get("world_events_sha256") == sha256_file(EVENTS),
        "world_receipt_matches_parent_fix": inputs.get("world_receipt_sha256") == sha256_file(WORLD_RECEIPT),
        "stage64_matches_parent_fix": inputs.get("stage64_receipt_sha256") == sha256_file(STAGE64),
        "foundation_card_matches_parent_fix": inputs.get("foundation_card_sha256") == sha256_file(FOUNDATION_CARD),
    }


def apply_observed_view(
    density: np.ndarray,
    getter: Callable[[int, int], str | None],
    view: int,
    channels: dict[tuple[int, int], np.ndarray],
    visibility: Any,
    *,
    frozen: bool,
) -> np.ndarray:
    result = density.copy()
    for position in range(N_BITS):
        outcome = getter(view, position)
        if outcome is None:
            continue
        bit = 0 if frozen else int(outcome)
        result = visibility.unvec(channels[(position, bit)] @ visibility.vec(result))
    return result


def engine_trajectory(
    getter: Callable[[int, int], str | None],
    channels: dict[tuple[int, int], np.ndarray],
    visibility: Any,
    *,
    update_mode: str,
    frozen: bool = False,
) -> list[np.ndarray]:
    if update_mode not in {"fixed_residual", "original_broken"}:
        raise ValueError(f"unknown update_mode: {update_mode}")
    density = visibility.RHO0.copy()
    states = []
    for view in range(N_VIEWS):
        persistent = apply_observed_view(
            density, getter, view, channels, visibility, frozen=frozen
        )
        if update_mode == "fixed_residual":
            view_local = apply_observed_view(
                visibility.RHO0, getter, view, channels, visibility, frozen=frozen
            )
            density = 0.5 * persistent + 0.5 * view_local
        else:
            density = persistent
        states.append(density.copy())
    return states


def ridge_fit(x: np.ndarray, y: np.ndarray, lam: float = 1e-3) -> np.ndarray:
    augmented = np.hstack([x, np.ones((x.shape[0], 1))])
    return np.linalg.solve(
        augmented.T @ augmented + lam * np.eye(augmented.shape[1]),
        augmented.T @ y,
    )


def ridge_predict(weights: np.ndarray, x: np.ndarray) -> np.ndarray:
    return np.hstack([x, np.ones((x.shape[0], 1))]) @ weights


def decode_per_position(
    feature_of_slot: Callable[[tuple[str, int, int]], np.ndarray],
    train_slots: list[tuple[str, int, int]],
    test_slots: list[tuple[str, int, int]],
    truth: Callable[[tuple[str, int, int]], int],
    pooled_majority: int,
    *,
    train_label_map: dict[tuple[str, int, int], int] | None = None,
) -> tuple[float, dict[tuple[str, int, int], bool], dict[tuple[str, int, int], bool]]:
    predictions: dict[tuple[str, int, int], bool] = {}
    correctness: dict[tuple[str, int, int], bool] = {}
    for position in range(N_BITS):
        train = [slot for slot in train_slots if slot[2] == position]
        test = [slot for slot in test_slots if slot[2] == position]
        if not test:
            continue
        if len(train) < 10:
            for slot in test:
                predictions[slot] = bool(pooled_majority)
                correctness[slot] = predictions[slot] == bool(truth(slot))
            continue
        train_x = np.array([feature_of_slot(slot) for slot in train])
        train_y = np.array(
            [
                2.0 * (train_label_map[slot] if train_label_map else truth(slot)) - 1.0
                for slot in train
            ]
        )
        weights = ridge_fit(train_x, train_y)
        test_x = np.array([feature_of_slot(slot) for slot in test])
        predicted = ridge_predict(weights, test_x) >= 0
        for slot, value in zip(test, predicted):
            predictions[slot] = bool(value)
            correctness[slot] = bool(value) == bool(truth(slot))
    accuracy = float(np.mean([correctness[slot] for slot in test_slots]))
    return accuracy, predictions, correctness


def entropy_binary(labels: list[bool]) -> float:
    proportion = sum(labels) / len(labels)
    if proportion in (0.0, 1.0):
        return 0.0
    return -proportion * math.log2(proportion) - (1 - proportion) * math.log2(1 - proportion)


def id3(
    rows: list[dict[str, str]],
    labels: list[bool],
    features: list[str],
    *,
    depth: int = 0,
    max_depth: int = 6,
    min_n: int = 8,
) -> dict[str, Any]:
    proportion = sum(labels) / len(labels)
    node: dict[str, Any] = {"maj": proportion >= 0.5}
    if proportion in (0.0, 1.0) or depth >= max_depth or len(labels) < min_n:
        return node
    base = entropy_binary(labels)
    best_feature = None
    best_gain = 1e-9
    best_split: dict[str, list[int]] | None = None
    for feature in features:
        groups: dict[str, list[int]] = {}
        for index, row in enumerate(rows):
            groups.setdefault(row[feature], []).append(index)
        if len(groups) < 2:
            continue
        remainder = sum(
            len(indices) * entropy_binary([labels[index] for index in indices])
            for indices in groups.values()
        ) / len(labels)
        if base - remainder > best_gain:
            best_feature = feature
            best_gain = base - remainder
            best_split = groups
    if best_feature is None or best_split is None:
        return node
    node["feat"] = best_feature
    node["children"] = {
        value: id3(
            [rows[index] for index in indices],
            [labels[index] for index in indices],
            features,
            depth=depth + 1,
            max_depth=max_depth,
            min_n=min_n,
        )
        for value, indices in best_split.items()
    }
    return node


def id3_predict(node: dict[str, Any], row: dict[str, str]) -> bool:
    current = node
    while "feat" in current:
        child = current["children"].get(row[current["feat"]])
        if child is None:
            break
        current = child
    return bool(current["maj"])


def tree_size(node: dict[str, Any]) -> tuple[int, int]:
    if "feat" not in node:
        return 1, 1
    total, depth = 1, 0
    for child in node["children"].values():
        child_total, child_depth = tree_size(child)
        total += child_total
        depth = max(depth, child_depth)
    return total, depth + 1


def twin_features(
    getter: Callable[[int, int], str | None],
    view: int,
    position: int,
    rule_family: dict[int, tuple[int, ...]],
) -> dict[str, str]:
    features = {"pos": str(position), "view": str(view)}
    last, age = "none", "inf"
    for prior_view in range(view, -1, -1):
        outcome = getter(prior_view, position)
        if outcome is not None:
            last, age = outcome, str(min(view - prior_view, 3))
            break
    features["last"], features["age"] = last, age
    scores: dict[int, int] = {}
    for rule, taps in rule_family.items():
        if view == 0:
            prediction = "unk"
        else:
            values = [getter(view - 1, (position + offset) % N_BITS) for offset in taps]
            prediction = (
                str(sum(int(value) for value in values) % 2)
                if all(value is not None for value in values)
                else "unk"
            )
        features[f"rule{rule}_pred"] = prediction
        score = 0
        for prior_view in range(1, view + 1):
            for query_position in range(N_BITS):
                outcome = getter(prior_view, query_position)
                if outcome is None:
                    continue
                values = [
                    getter(prior_view - 1, (query_position + offset) % N_BITS)
                    for offset in taps
                ]
                if any(value is None for value in values):
                    continue
                score += (
                    1
                    if str(sum(int(value) for value in values) % 2) == outcome
                    else -1
                )
        scores[rule] = score
        features[f"agree{rule}"] = str(max(-2, min(2, score)))
    maximum = max(scores.values())
    best_rules = [rule for rule in scores if scores[rule] == maximum]
    best_predictions = {features[f"rule{rule}_pred"] for rule in best_rules}
    features["best_pred"] = (
        best_predictions.pop()
        if maximum > 0 and len(best_predictions) == 1 and "unk" not in best_predictions
        else "unk"
    )
    return features


def twin_run(
    feature_of_slot: Callable[[tuple[str, int, int]], dict[str, str]],
    train_slots: list[tuple[str, int, int]],
    test_slots: list[tuple[str, int, int]],
    truth: Callable[[tuple[str, int, int]], int],
    *,
    train_label_map: dict[tuple[str, int, int], int] | None = None,
) -> tuple[float, dict[tuple[str, int, int], bool], dict[tuple[str, int, int], bool], dict[str, Any]]:
    train_rows = [feature_of_slot(slot) for slot in train_slots]
    features = sorted(train_rows[0])
    train_labels = [
        bool(train_label_map[slot] if train_label_map else truth(slot))
        for slot in train_slots
    ]
    tree = id3(train_rows, train_labels, features)
    predictions: dict[tuple[str, int, int], bool] = {}
    correctness: dict[tuple[str, int, int], bool] = {}
    for slot in test_slots:
        predictions[slot] = id3_predict(tree, feature_of_slot(slot))
        correctness[slot] = predictions[slot] == bool(truth(slot))
    accuracy = float(np.mean([correctness[slot] for slot in test_slots]))
    return accuracy, predictions, correctness, tree


def von_neumann_entropy(density: np.ndarray) -> float:
    eigenvalues = np.linalg.eigvalsh(0.5 * (density + density.conj().T))
    eigenvalues = eigenvalues[eigenvalues > 1e-14]
    return float(-np.sum(eigenvalues * np.log2(eigenvalues)))


def holevo_binary(states: list[np.ndarray], bits: list[int]) -> float:
    count = len(bits)
    count_one = sum(bits)
    if count_one == 0 or count_one == count:
        return 0.0
    density_one = sum(state for state, bit in zip(states, bits) if bit == 1) / count_one
    density_zero = sum(state for state, bit in zip(states, bits) if bit == 0) / (count - count_one)
    probability_one = count_one / count
    average = probability_one * density_one + (1 - probability_one) * density_zero
    return (
        von_neumann_entropy(average)
        - probability_one * von_neumann_entropy(density_one)
        - (1 - probability_one) * von_neumann_entropy(density_zero)
    )


def persistence_holevo(
    state_map: dict[str, list[np.ndarray]],
    slots: list[tuple[str, int, int]],
    oracle: dict[str, list[tuple[int, ...]]],
    *,
    permutation_rng: np.random.Generator | None = None,
) -> tuple[float, list[float]]:
    values = []
    for position in range(N_BITS):
        instances = [(object_id, view) for object_id, view, query in slots if query == position]
        if len(instances) < 20:
            continue
        states = [state_map[object_id][view] for object_id, view in instances]
        bits = [oracle[object_id][view][position] for object_id, view in instances]
        if permutation_rng is not None:
            bits = list(permutation_rng.permutation(bits))
        values.append(holevo_binary(states, bits))
    return float(np.mean(values)), values


def metric_vector(
    engine_correct: np.ndarray, twin_correct: np.ndarray
) -> dict[str, float]:
    both_wrong = np.logical_not(engine_correct) & np.logical_not(twin_correct)
    twin_only = np.logical_not(engine_correct) & twin_correct
    engine_only = engine_correct & np.logical_not(twin_correct)
    both_correct = engine_correct & twin_correct
    engine_accuracy = float(np.mean(engine_correct))
    twin_accuracy = float(np.mean(twin_correct))
    union_accuracy = float(np.mean(engine_correct | twin_correct))
    pe, pt = engine_accuracy, twin_accuracy
    denominator = math.sqrt(pe * (1 - pe) * pt * (1 - pt))
    phi = (
        float(np.mean(both_correct) - pe * pt) / denominator
        if denominator > 1e-12
        else float("nan")
    )
    return {
        "engine_accuracy": engine_accuracy,
        "twin_accuracy": twin_accuracy,
        "union_accuracy": union_accuracy,
        "engine_minus_twin": engine_accuracy - twin_accuracy,
        "union_gain_over_best": union_accuracy - max(engine_accuracy, twin_accuracy),
        "both_wrong_proportion": float(np.mean(both_wrong)),
        "twin_only_proportion": float(np.mean(twin_only)),
        "engine_only_proportion": float(np.mean(engine_only)),
        "both_correct_proportion": float(np.mean(both_correct)),
        "phi": phi,
    }


def bootstrap_complementarity(
    slots: list[tuple[str, int, int]],
    engine_correct: dict[tuple[str, int, int], bool],
    twin_correct: dict[tuple[str, int, int], bool],
    test_objects: list[str],
) -> dict[str, Any]:
    indices_by_object = {
        object_id: np.array(
            [index for index, slot in enumerate(slots) if slot[0] == object_id],
            dtype=int,
        )
        for object_id in test_objects
    }
    engine = np.array([engine_correct[slot] for slot in slots], dtype=bool)
    twin = np.array([twin_correct[slot] for slot in slots], dtype=bool)
    observed = metric_vector(engine, twin)
    rng = np.random.default_rng(SEED + 101)
    samples: dict[str, list[float]] = {key: [] for key in observed}
    for _ in range(N_BOOTSTRAPS):
        sampled_objects = rng.choice(test_objects, size=len(test_objects), replace=True)
        sampled_indices = np.concatenate([indices_by_object[object_id] for object_id in sampled_objects])
        values = metric_vector(engine[sampled_indices], twin[sampled_indices])
        for key, value in values.items():
            if not math.isnan(value):
                samples[key].append(value)
    intervals = {
        key: {
            "estimate": None if math.isnan(value) else value,
            "ci95": [
                float(np.quantile(samples[key], 0.025)),
                float(np.quantile(samples[key], 0.975)),
            ] if samples[key] else [None, None],
        }
        for key, value in observed.items()
    }
    cells = {
        "both_wrong": int(np.sum(~engine & ~twin)),
        "twin_only": int(np.sum(~engine & twin)),
        "engine_only": int(np.sum(engine & ~twin)),
        "both_correct": int(np.sum(engine & twin)),
    }
    return {
        "bootstrap_unit": "held-out object; all occluded slots for a sampled object stay together",
        "confidence_level": 0.95,
        "draws": N_BOOTSTRAPS,
        "seed": SEED + 101,
        "table_layout": "[[both_wrong, twin_only], [engine_only, both_correct]]",
        "counts": [[cells["both_wrong"], cells["twin_only"]], [cells["engine_only"], cells["both_correct"]]],
        "metrics": intervals,
    }


def full_context_target_masked_density(
    object_id: str,
    query_view: int,
    query_position: int,
    full_views: dict[str, list[tuple[int, ...]]],
    channels: dict[tuple[int, int], np.ndarray],
    visibility: Any,
    *,
    update_mode: str,
) -> np.ndarray:
    """Original occlusion-free control with the queried target still hidden.

    All prior views are complete.  At the query view every position except the
    target is visible.  The fixed residual, when selected, is mixed once after
    each complete/target-masked view.
    """
    density = visibility.RHO0.copy()
    for view in range(query_view + 1):
        getter = lambda current_view, position, view=view: (
            None
            if view == query_view and position == query_position
            else str(full_views[object_id][view][position])
        )
        persistent = apply_observed_view(
            density, getter, view, channels, visibility, frozen=False
        )
        if update_mode == "fixed_residual":
            view_local = apply_observed_view(
                visibility.RHO0, getter, view, channels, visibility, frozen=False
            )
            density = 0.5 * persistent + 0.5 * view_local
        else:
            density = persistent
    return density


def cptp_summary(
    log: dict[str, dict[int, dict[int, str]]],
    full_views: dict[str, list[tuple[int, ...]]],
    channels: dict[tuple[int, int], np.ndarray],
    visibility: Any,
) -> dict[str, Any]:
    stage_certificates = {}
    for (position, bit), channel in sorted(channels.items()):
        minimum, trace_deviation = visibility.choi_cptp(channel)
        stage_certificates[f"position_{position}_bit_{bit}"] = {
            "choi_min_eigenvalue": minimum,
            "trace_preserving_deviation": trace_deviation,
        }

    patterns: set[tuple[int | None, ...]] = set()
    for object_id in sorted(log):
        for view in range(N_VIEWS):
            patterns.add(
                tuple(
                    None
                    if log[object_id][view][position] == "withheld"
                    else int(log[object_id][view][position])
                    for position in range(N_BITS)
                )
            )
            patterns.add(tuple(int(bit) for bit in full_views[object_id][view]))
            for query_position in range(N_BITS):
                patterns.add(
                    tuple(
                        None if position == query_position else int(bit)
                        for position, bit in enumerate(full_views[object_id][view])
                    )
                )
    residual_certificates = []
    for pattern in sorted(patterns, key=lambda value: tuple(-1 if bit is None else bit for bit in value)):
        persistent = np.eye(16, dtype=complex)
        for position, bit in enumerate(pattern):
            if bit is not None:
                persistent = channels[(position, int(bit))] @ persistent
        view_local = visibility.unvec(persistent @ visibility.vec(visibility.RHO0))
        replacement = np.outer(
            visibility.vec(view_local),
            visibility.vec(np.eye(4, dtype=complex)).conj(),
        )
        residual = 0.5 * persistent + 0.5 * replacement
        minimum, trace_deviation = visibility.choi_cptp(residual)
        residual_certificates.append(
            {
                "pattern": ["withheld" if bit is None else int(bit) for bit in pattern],
                "choi_min_eigenvalue": minimum,
                "trace_preserving_deviation": trace_deviation,
            }
        )
    all_certificates = list(stage_certificates.values()) + residual_certificates
    return {
        "stage_channel_count": len(stage_certificates),
        "residual_pattern_count": len(residual_certificates),
        "minimum_choi_eigenvalue": min(item["choi_min_eigenvalue"] for item in all_certificates),
        "maximum_trace_preserving_deviation": max(
            item["trace_preserving_deviation"] for item in all_certificates
        ),
        "pass": all(
            item["choi_min_eigenvalue"] > -1e-9
            and item["trace_preserving_deviation"] < 1e-9
            for item in all_certificates
        ),
        "stage_certificates": stage_certificates,
        "residual_update_certificates": residual_certificates,
    }


def episode_table(
    slots: list[tuple[str, int, int]],
    engine_correct: dict[tuple[str, int, int], bool],
    twin_correct: dict[tuple[str, int, int], bool],
    test_objects: list[str],
) -> list[dict[str, Any]]:
    rows = []
    for object_id in test_objects:
        object_slots = [slot for slot in slots if slot[0] == object_id]
        engine = np.array([engine_correct[slot] for slot in object_slots], dtype=bool)
        twin = np.array([twin_correct[slot] for slot in object_slots], dtype=bool)
        metrics = metric_vector(engine, twin)
        rows.append(
            {
                "object_id": object_id,
                "occluded_slots": len(object_slots),
                "engine_accuracy": metrics["engine_accuracy"],
                "twin_accuracy": metrics["twin_accuracy"],
                "union_accuracy": metrics["union_accuracy"],
                "counts": {
                    "both_wrong": int(np.sum(~engine & ~twin)),
                    "twin_only": int(np.sum(~engine & twin)),
                    "engine_only": int(np.sum(engine & ~twin)),
                    "both_correct": int(np.sum(engine & twin)),
                },
            }
        )
    return rows


def density_payload(state_map: dict[str, list[np.ndarray]]) -> dict[str, Any]:
    return {
        object_id: [
            [
                [[float(value.real), float(value.imag)] for value in row]
                for row in density
            ]
            for density in states
        ]
        for object_id, states in sorted(state_map.items())
    }


def density_slot_payload(
    state_map: dict[tuple[str, int, int], np.ndarray]
) -> dict[str, Any]:
    return {
        f"{object_id}|view_{view}|position_{position}": [
            [[float(value.real), float(value.imag)] for value in row]
            for row in density
        ]
        for (object_id, view, position), density in sorted(state_map.items())
    }


def run(memory_percent: int) -> dict[str, Any]:
    # Imported only after the memory-pressure check.  This module imports
    # NumPy/SciPy but neither torch nor qutip; those remain explicitly unscoped.
    sys.path.insert(0, str(REPO))
    from system_v8.loop3_senses import visibility_sanity_gate as visibility

    tracked_inputs = [
        EVENTS,
        WORLD_RECEIPT,
        LOOP2_SOURCE,
        LOOP2_RECEIPT,
        STAGE64,
        VISIBILITY_SOURCE,
        FIX_RECEIPT,
        FOUNDATION_CARD,
        OBJECT_CARD,
        SOURCE,
    ]
    input_hashes_start = {str(path): sha256_file(path) for path in tracked_inputs}

    with FIX_RECEIPT.open() as handle:
        fix_receipt = json.load(handle)
    with LOOP2_RECEIPT.open() as handle:
        original_receipt = json.load(handle)
    provenance_checks = validate_parent_fix(fix_receipt)
    if not all(provenance_checks.values()):
        failed = [key for key, passed in provenance_checks.items() if not passed]
        raise RetestError(f"parent/source provenance mismatch: {failed}")

    with WORLD_RECEIPT.open() as handle:
        world_receipt = json.load(handle)
    rule_family = {
        int(key): tuple(int(offset) for offset in offsets)
        for key, offsets in world_receipt["parameters"]["rule_family"].items()
    }
    log, schema_metrics = visibility.parse_event_log(EVENTS)
    full_views, recovery_metrics = visibility.recover_full_views(log, rule_family)
    object_ids = sorted(log)
    train_objects, test_objects = visibility.train_test_objects(object_ids)
    parent_split = fix_receipt["protocol"]["split"]
    split_matches_parent = (
        train_objects == parent_split["train_objects"]
        and test_objects == parent_split["test_objects"]
        and not bool(set(train_objects) & set(test_objects))
    )
    original_split = original_receipt["protocol"]["split"]
    split_matches_original = (
        set(train_objects) == set(original_split["train_objects"])
        and set(test_objects) == set(original_split["test_objects"])
    )

    with STAGE64.open() as handle:
        stage_receipt = json.load(handle)
    channels, stages = visibility.load_stage_channels(
        stage_receipt, encoder_channel_fix=False
    )

    def log_getter(object_id: str) -> Callable[[int, int], str | None]:
        return lambda view, position: (
            None
            if log[object_id][view][position] == "withheld"
            else log[object_id][view][position]
        )

    def full_getter(object_id: str) -> Callable[[int, int], str]:
        return lambda view, position: str(full_views[object_id][view][position])

    fixed_states = {
        object_id: engine_trajectory(
            log_getter(object_id), channels, visibility, update_mode="fixed_residual"
        )
        for object_id in object_ids
    }
    broken_states = {
        object_id: engine_trajectory(
            log_getter(object_id), channels, visibility, update_mode="original_broken"
        )
        for object_id in object_ids
    }
    frozen_states = {
        object_id: engine_trajectory(
            log_getter(object_id),
            channels,
            visibility,
            update_mode="fixed_residual",
            frozen=True,
        )
        for object_id in object_ids
    }
    broken_frozen_states = {
        object_id: engine_trajectory(
            log_getter(object_id),
            channels,
            visibility,
            update_mode="original_broken",
            frozen=True,
        )
        for object_id in object_ids
    }
    full_fixed_states, _ = visibility.density_trajectories(
        full_views, channels, update_residual_fix=True
    )
    full_broken_states, _ = visibility.density_trajectories(
        full_views, channels, update_residual_fix=False
    )
    independent_full_fixed = {
        object_id: engine_trajectory(
            full_getter(object_id), channels, visibility, update_mode="fixed_residual"
        )
        for object_id in object_ids
    }
    fixed_update_equivalence_max = max(
        float(np.linalg.norm(left - right))
        for object_id in object_ids
        for left, right in zip(full_fixed_states[object_id], independent_full_fixed[object_id])
    )

    slots = [
        (object_id, view, position)
        for object_id in object_ids
        for view in range(N_VIEWS)
        for position in range(N_BITS)
        if log[object_id][view][position] == "withheld"
    ]
    train_object_set, test_object_set = set(train_objects), set(test_objects)
    train_slots = [slot for slot in slots if slot[0] in train_object_set]
    test_slots = [slot for slot in slots if slot[0] in test_object_set]

    def truth(slot: tuple[str, int, int]) -> int:
        object_id, view, position = slot
        return int(full_views[object_id][view][position])

    train_bits = np.array([truth(slot) for slot in train_slots])
    pooled_majority = int(train_bits.mean() >= 0.5)
    position_majority = {}
    for position in range(N_BITS):
        bits = [truth(slot) for slot in train_slots if slot[2] == position]
        position_majority[position] = int(np.mean(bits) >= 0.5) if bits else pooled_majority
    pooled_train_accuracy = float(np.mean([truth(slot) == pooled_majority for slot in train_slots]))
    position_train_accuracy = float(
        np.mean([truth(slot) == position_majority[slot[2]] for slot in train_slots])
    )
    use_position_majority = position_train_accuracy > pooled_train_accuracy
    computed_baseline = float(
        np.mean(
            [
                truth(slot)
                == (position_majority[slot[2]] if use_position_majority else pooled_majority)
                for slot in test_slots
            ]
        )
    )

    fixed_feature = lambda slot: visibility.pauli_features(
        fixed_states[slot[0]][slot[1]], quadratic=False
    )
    broken_feature = lambda slot: visibility.pauli_features(
        broken_states[slot[0]][slot[1]], quadratic=False
    )
    frozen_feature = lambda slot: visibility.pauli_features(
        frozen_states[slot[0]][slot[1]], quadratic=False
    )
    broken_frozen_feature = lambda slot: visibility.pauli_features(
        broken_frozen_states[slot[0]][slot[1]], quadratic=False
    )
    fixed_accuracy, fixed_predictions, fixed_correct = decode_per_position(
        fixed_feature, train_slots, test_slots, truth, pooled_majority
    )
    broken_accuracy, _, broken_correct = decode_per_position(
        broken_feature, train_slots, test_slots, truth, pooled_majority
    )
    frozen_accuracy, _, frozen_correct = decode_per_position(
        frozen_feature, train_slots, test_slots, truth, pooled_majority
    )
    broken_frozen_accuracy, _, _ = decode_per_position(
        broken_frozen_feature, train_slots, test_slots, truth, pooled_majority
    )

    twin_feature = lambda slot: twin_features(
        log_getter(slot[0]), slot[1], slot[2], rule_family
    )
    twin_accuracy, twin_predictions, twin_correct, twin_tree = twin_run(
        twin_feature, train_slots, test_slots, truth
    )
    twin_nodes, twin_depth = tree_size(twin_tree)

    fixed_target_masked_densities = {
        slot: full_context_target_masked_density(
            slot[0],
            slot[1],
            slot[2],
            full_views,
            channels,
            visibility,
            update_mode="fixed_residual",
        )
        for slot in train_slots + test_slots
    }
    broken_target_masked_densities = {
        slot: full_context_target_masked_density(
            slot[0],
            slot[1],
            slot[2],
            full_views,
            channels,
            visibility,
            update_mode="original_broken",
        )
        for slot in train_slots + test_slots
    }
    fixed_target_masked_cache = {
        slot: visibility.pauli_features(density, quadratic=False)
        for slot, density in fixed_target_masked_densities.items()
    }
    broken_target_masked_cache = {
        slot: visibility.pauli_features(density, quadratic=False)
        for slot, density in broken_target_masked_densities.items()
    }
    target_masked_fixed_accuracy, _, target_masked_fixed_correct = decode_per_position(
        lambda slot: fixed_target_masked_cache[slot],
        train_slots,
        test_slots,
        truth,
        pooled_majority,
    )
    target_masked_broken_accuracy, _, target_masked_broken_correct = decode_per_position(
        lambda slot: broken_target_masked_cache[slot],
        train_slots,
        test_slots,
        truth,
        pooled_majority,
    )
    target_masked_per_view = []
    for view in range(N_VIEWS):
        view_slots = [slot for slot in test_slots if slot[1] == view]
        fixed_view_accuracy = float(
            np.mean([target_masked_fixed_correct[slot] for slot in view_slots])
        )
        broken_view_accuracy = float(
            np.mean([target_masked_broken_correct[slot] for slot in view_slots])
        )
        view_baseline = float(
            np.mean(
                [
                    truth(slot)
                    == (
                        position_majority[slot[2]]
                        if use_position_majority
                        else pooled_majority
                    )
                    for slot in view_slots
                ]
            )
        )
        target_masked_per_view.append(
            {
                "k": view,
                "test_slots": len(view_slots),
                "fixed_accuracy": fixed_view_accuracy,
                "original_broken_accuracy": broken_view_accuracy,
                "computed_chance_accuracy": view_baseline,
                "fixed_margin": fixed_view_accuracy - view_baseline,
                "fixed_pass": bool(fixed_view_accuracy > view_baseline),
            }
        )

    complementarity = bootstrap_complementarity(
        test_slots, fixed_correct, twin_correct, test_objects
    )
    broken_table = [
        [
            int(
                np.sum(
                    [
                        (not broken_correct[slot]) and (not twin_correct[slot])
                        for slot in test_slots
                    ]
                )
            ),
            int(
                np.sum(
                    [
                        (not broken_correct[slot]) and twin_correct[slot]
                        for slot in test_slots
                    ]
                )
            ),
        ],
        [
            int(
                np.sum(
                    [
                        broken_correct[slot] and (not twin_correct[slot])
                        for slot in test_slots
                    ]
                )
            ),
            int(
                np.sum(
                    [broken_correct[slot] and twin_correct[slot] for slot in test_slots]
                )
            ),
        ],
    ]
    episodes = episode_table(test_slots, fixed_correct, twin_correct, test_objects)

    fixed_holevo, fixed_holevo_by_position = persistence_holevo(
        fixed_states, slots, full_views
    )
    broken_holevo, broken_holevo_by_position = persistence_holevo(
        broken_states, slots, full_views
    )
    frozen_holevo, frozen_holevo_by_position = persistence_holevo(
        frozen_states, slots, full_views
    )
    fixed_null_rng = np.random.default_rng(SEED + 1)
    broken_null_rng = np.random.default_rng(SEED + 1)
    frozen_null_rng = np.random.default_rng(SEED + 2)
    fixed_holevo_null = np.array(
        [persistence_holevo(fixed_states, slots, full_views, permutation_rng=fixed_null_rng)[0] for _ in range(N_PERMUTATIONS)]
    )
    broken_holevo_null = np.array(
        [persistence_holevo(broken_states, slots, full_views, permutation_rng=broken_null_rng)[0] for _ in range(N_PERMUTATIONS)]
    )
    frozen_holevo_null = np.array(
        [persistence_holevo(frozen_states, slots, full_views, permutation_rng=frozen_null_rng)[0] for _ in range(N_PERMUTATIONS)]
    )

    # A shared position-stratified training-label map is used for both lanes on
    # each draw.  This preserves per-position marginals while making the joint
    # union null meaningful rather than combining unrelated random controls.
    shuffle_rng = np.random.default_rng(SEED + 31)
    shuffled_engine_accuracy = []
    shuffled_twin_accuracy = []
    shuffled_union_accuracy = []
    for _ in range(N_PERMUTATIONS):
        label_map = {}
        for position in range(N_BITS):
            position_slots = [slot for slot in train_slots if slot[2] == position]
            position_truth = np.array([truth(slot) for slot in position_slots], dtype=int)
            for slot, label in zip(position_slots, shuffle_rng.permutation(position_truth)):
                label_map[slot] = int(label)
        engine_accuracy, _, engine_correct = decode_per_position(
            fixed_feature,
            train_slots,
            test_slots,
            truth,
            pooled_majority,
            train_label_map=label_map,
        )
        twin_null_accuracy, _, twin_null_correct, _ = twin_run(
            twin_feature,
            train_slots,
            test_slots,
            truth,
            train_label_map=label_map,
        )
        shuffled_engine_accuracy.append(engine_accuracy)
        shuffled_twin_accuracy.append(twin_null_accuracy)
        shuffled_union_accuracy.append(
            float(
                np.mean(
                    [engine_correct[slot] or twin_null_correct[slot] for slot in test_slots]
                )
            )
        )
    shuffled_engine_accuracy = np.asarray(shuffled_engine_accuracy)
    shuffled_twin_accuracy = np.asarray(shuffled_twin_accuracy)
    shuffled_union_accuracy = np.asarray(shuffled_union_accuracy)
    fixed_union_accuracy = complementarity["metrics"]["union_accuracy"]["estimate"]
    engine_null_p95 = float(np.quantile(shuffled_engine_accuracy, 0.95))
    twin_null_p95 = float(np.quantile(shuffled_twin_accuracy, 0.95))
    union_null_p95 = float(np.quantile(shuffled_union_accuracy, 0.95))
    engine_shuffle_pvalue = float(
        (1 + np.sum(shuffled_engine_accuracy >= fixed_accuracy))
        / (N_PERMUTATIONS + 1)
    )
    twin_shuffle_pvalue = float(
        (1 + np.sum(shuffled_twin_accuracy >= twin_accuracy))
        / (N_PERMUTATIONS + 1)
    )
    union_shuffle_pvalue = float(
        (1 + np.sum(shuffled_union_accuracy >= fixed_union_accuracy))
        / (N_PERMUTATIONS + 1)
    )
    at_least_one_lane_above_random = (
        fixed_accuracy > max(computed_baseline, engine_null_p95)
        or twin_accuracy > max(computed_baseline, twin_null_p95)
    )
    union_above_joint_null = fixed_union_accuracy > union_null_p95
    both_random_confound_excluded = bool(
        at_least_one_lane_above_random and union_above_joint_null
    )
    useful_complementarity_eligible = bool(
        fixed_accuracy > max(computed_baseline, engine_null_p95)
        and twin_accuracy > max(computed_baseline, twin_null_p95)
        and union_above_joint_null
    )

    def full_visibility_metrics(
        trajectories: dict[str, list[np.ndarray]]
    ) -> dict[str, Any]:
        feature = lambda object_id, view: visibility.pauli_features(
            trajectories[object_id][view], quadratic=False
        )
        accuracy, baseline, _, _ = visibility.bitwise_probe(
            feature, full_views, train_objects, test_objects
        )
        per_view = []
        for view in range(N_VIEWS):
            view_accuracy, view_baseline, _, _ = visibility.bitwise_probe_at_view(
                feature, full_views, train_objects, test_objects, view
            )
            per_view.append(
                {
                    "k": view,
                    "held_out_accuracy": view_accuracy,
                    "computed_chance_accuracy": view_baseline,
                    "margin": view_accuracy - view_baseline,
                    "pass": bool(view_accuracy > view_baseline),
                }
            )
        return {
            "accuracy_type": "current-world-state bitwise accuracy",
            "full_visibility": True,
            "readout": "15 Pauli expectations with object-disjoint per-bit ridge",
            "held_out_accuracy": accuracy,
            "computed_chance_accuracy": baseline,
            "margin": accuracy - baseline,
            "per_k": per_view,
            "all_k_beat_chance": bool(all(item["pass"] for item in per_view)),
        }

    full_fixed = full_visibility_metrics(full_fixed_states)
    full_broken = full_visibility_metrics(full_broken_states)
    target_masked_full_visibility = {
        "accuracy_type": "occluded current-world bit with all prior views and all non-target current-view bits visible",
        "queried_target_remains_masked": True,
        "fixed_held_out_accuracy": target_masked_fixed_accuracy,
        "original_broken_held_out_accuracy": target_masked_broken_accuracy,
        "computed_chance_accuracy": computed_baseline,
        "fixed_margin": target_masked_fixed_accuracy - computed_baseline,
        "per_k": target_masked_per_view,
        "all_k_beat_chance": bool(
            all(item["fixed_pass"] for item in target_masked_per_view)
        ),
    }

    physicality = {
        "fixed_occluded": visibility.physicality(
            [state for object_id in object_ids for state in fixed_states[object_id]]
        ),
        "broken_occluded": visibility.physicality(
            [state for object_id in object_ids for state in broken_states[object_id]]
        ),
        "frozen_fixed_occluded": visibility.physicality(
            [state for object_id in object_ids for state in frozen_states[object_id]]
        ),
        "frozen_original_broken_occluded": visibility.physicality(
            [state for object_id in object_ids for state in broken_frozen_states[object_id]]
        ),
        "fixed_full_visibility": visibility.physicality(
            [state for object_id in object_ids for state in full_fixed_states[object_id]]
        ),
        "fixed_target_masked_full_context": visibility.physicality(
            list(fixed_target_masked_densities.values())
        ),
        "broken_target_masked_full_context": visibility.physicality(
            list(broken_target_masked_densities.values())
        ),
    }
    channel_cptp = cptp_summary(log, full_views, channels, visibility)

    trajectory_receipt = {
        "schema": "loop3_senses/loop2_retest_fixed_senses/density_trajectories_v1",
        "matrix_encoding": "each complex entry is [real, imaginary]",
        "object_order": object_ids,
        "view_order": list(range(N_VIEWS)),
        "lanes": {
            "fixed_occluded": density_payload(fixed_states),
            "original_broken_occluded": density_payload(broken_states),
            "frozen_fixed_occluded": density_payload(frozen_states),
            "frozen_original_broken_occluded": density_payload(broken_frozen_states),
            "fixed_full_visibility": density_payload(full_fixed_states),
            "original_broken_full_visibility": density_payload(full_broken_states),
            "fixed_target_masked_full_context": density_slot_payload(
                fixed_target_masked_densities
            ),
            "original_broken_target_masked_full_context": density_slot_payload(
                broken_target_masked_densities
            ),
        },
    }
    with TRAJECTORY_PATH.open("x") as handle:
        json.dump(
            trajectory_receipt,
            handle,
            separators=(",", ":"),
            allow_nan=False,
        )

    provenance_checks_end = validate_parent_fix(fix_receipt)
    input_hashes_end = {str(path): sha256_file(path) for path in tracked_inputs}
    original_metrics = original_receipt["results"]
    original_semantics_checks = {
        "computed_baseline_matches_original_receipt": abs(
            computed_baseline - original_metrics["computed_baseline"]
        ) < 1e-15,
        "broken_occluded_accuracy_matches_original_receipt": abs(
            broken_accuracy - original_metrics["engine"]["occluded_acc"]
        ) < 1e-15,
        "broken_target_masked_accuracy_matches_original_receipt": abs(
            target_masked_broken_accuracy
            - original_metrics["engine"]["occlusion_free_acc"]
        ) < 1e-15,
        "frozen_accuracy_matches_original_receipt": abs(
            broken_frozen_accuracy - original_metrics["engine"]["frozen_acc"]
        ) < 1e-15,
        "twin_accuracy_matches_original_receipt": abs(
            twin_accuracy - original_metrics["twin"]["occluded_acc"]
        ) < 1e-15,
        "broken_holevo_matches_original_receipt": abs(
            broken_holevo
            - original_metrics["belief_persistence"]["chi_mean_real"]
        ) < 1e-15,
        "broken_holevo_null_matches_original_receipt": abs(
            float(np.quantile(broken_holevo_null, 0.95))
            - original_metrics["belief_persistence"]["null_p95"]
        ) < 1e-15,
        "broken_complementarity_table_matches_original_receipt": broken_table
        == [
            [
                original_metrics["complementarity"]["neither"],
                original_metrics["complementarity"]["twin_only"],
            ],
            [
                original_metrics["complementarity"]["engine_only"],
                original_metrics["complementarity"]["both"],
            ],
        ],
    }

    strongest_engine_control = max(computed_baseline, engine_null_p95)
    split_fingerprint = sha256_json(
        {
            "seed": SEED,
            "train_objects": train_objects,
            "test_objects": test_objects,
            "train_slots": train_slots,
            "test_slots": test_slots,
        }
    )
    prediction_fingerprint = sha256_json(
        [
            {
                "slot": slot,
                "truth": truth(slot),
                "fixed_engine": fixed_predictions[slot],
                "twin": twin_predictions[slot],
            }
            for slot in test_slots
        ]
    )
    checks = {
        **provenance_checks,
        "canonical_interpreter": SIM_PY.resolve() == Path(sys.executable).resolve(),
        "memory_free_above_25_percent_before_torch_or_qutip": memory_percent > MIN_MEMORY_FREE_PERCENT,
        "torch_not_imported": "torch" not in sys.modules,
        "qutip_not_imported": "qutip" not in sys.modules,
        "ground_truth_recovered_from_visible_probes_only": recovery_metrics["objects_uniquely_recovered"] == len(object_ids),
        "split_matches_visibility_fix_and_loop2_seed": split_matches_parent,
        "split_matches_original_loop2_receipt": split_matches_original,
        "occluded_slot_counts_match_original_loop2": len(train_slots) == 782 and len(test_slots) == 343,
        "occluded_features_preserve_target_masking": all(
            log[slot[0]][slot[1]][slot[2]] == "withheld" for slot in train_slots + test_slots
        ),
        "prediction_coverage_matches_all_held_out_slots": (
            len(fixed_predictions) == len(twin_predictions) == len(test_slots) == 343
        ),
        **original_semantics_checks,
        "input_hashes_unchanged_during_run": (
            all(provenance_checks_end.values()) and input_hashes_start == input_hashes_end
        ),
        "fixed_update_matches_visibility_gate_implementation": fixed_update_equivalence_max < 1e-12,
        "all_density_lanes_physical": all(value["pass"] for value in physicality.values()),
        "stage_and_residual_update_maps_cptp": channel_cptp["pass"],
        "fixed_engine_occluded_accuracy_above_chance_and_shuffled_p95": fixed_accuracy > strongest_engine_control,
        "belief_persistence_holevo_above_permutation_null": fixed_holevo > float(np.quantile(fixed_holevo_null, 0.95)),
        "full_visibility_real_task_all_k_beat_chance": target_masked_full_visibility["all_k_beat_chance"],
        "visibility_gate_G4_replication_all_k_beat_chance": full_fixed["all_k_beat_chance"],
        "frozen_engine_control_does_not_pass": (
            frozen_holevo <= float(np.quantile(frozen_holevo_null, 0.95))
            and frozen_accuracy <= computed_baseline + 0.03
        ),
        "shuffled_label_control_is_below_fixed_engine": fixed_accuracy > engine_null_p95,
        "both_random_confound_excluded_before_complementarity_claim": both_random_confound_excluded,
        "original_broken_update_comparison_lane_executed": len(broken_states) == len(object_ids),
        "bootstrap_sample_size_adequate": len(test_slots) >= 100 and len(test_objects) == 20,
        "promotion_allowed_is_false": True,
    }
    all_pass = bool(all(checks.values()))

    if useful_complementarity_eligible:
        phi_value = complementarity["metrics"]["phi"]["estimate"]
        if complementarity["metrics"]["union_gain_over_best"]["estimate"] <= 0:
            coupling = "redundant"
        elif phi_value is not None and phi_value < -0.2:
            coupling = "complementary_with_above_random_guard"
        else:
            coupling = "partially_independent_with_above_random_guard"
    else:
        coupling = (
            "ineligible_both_random_confound"
            if not both_random_confound_excluded
            else "ineligible_one_lane_not_above_matched_control"
        )

    findings = [
        (
            f"Fixed occluded-bit accuracy {fixed_accuracy:.4f}, twin {twin_accuracy:.4f}, "
            f"computed chance {computed_baseline:.4f}; object-block bootstrap union "
            f"{fixed_union_accuracy:.4f}."
        ),
        (
            f"Both-random exclusion: at_least_one_lane_above_random={at_least_one_lane_above_random}, "
            f"union_above_joint_shuffled_null={union_above_joint_null}; useful-complementarity "
            f"eligibility={useful_complementarity_eligible}; coupling={coupling}."
        ),
        (
            f"Belief persistence Holevo fixed {fixed_holevo:.6f} bits vs permutation p95 "
            f"{float(np.quantile(fixed_holevo_null, 0.95)):.6f}; original broken "
            f"{broken_holevo:.6f}; frozen {frozen_holevo:.6f}."
        ),
        (
            f"Real-task full-context target-masked accuracy {target_masked_fixed_accuracy:.4f} "
            f"vs chance {computed_baseline:.4f}; every-k pass="
            f"{target_masked_full_visibility['all_k_beat_chance']}."
        ),
        (
            f"Original broken comparison: occluded accuracy {broken_accuracy:.4f}; target-masked "
            f"full-context accuracy {target_masked_broken_accuracy:.4f}."
        ),
        (
            f"Frozen fixed engine: occluded accuracy {frozen_accuracy:.4f}; Holevo "
            f"{frozen_holevo:.6f} vs its null p95 "
            f"{float(np.quantile(frozen_holevo_null, 0.95)):.6f}."
        ),
    ]
    if twin_accuracy >= fixed_accuracy:
        findings.append(
            "HONEST NEGATIVE KEPT: the classical twin matches or beats the fixed QIT engine on the held-out occluded task."
        )
    if not all_pass:
        findings.append(
            "HONEST NEGATIVE KEPT: at least one fail-closed retest check is red; the diagnostic is retained without promotion."
        )

    receipt = {
        "schema": "loop3_senses/loop2_retest_fixed_senses/receipt_v1",
        "sim_id": "loop2_retest_fixed_senses",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": CLASSIFICATION,
        "promotion_status": "diagnostic_only",
        "card_authority": str(FOUNDATION_CARD),
        "object_preservation_card": str(OBJECT_CARD),
        "runtime": {
            "python": sys.executable,
            "python_version": sys.version.split()[0],
            "required_python": str(SIM_PY),
            "memory_free_percent": memory_percent,
            "minimum_required_percent": MIN_MEMORY_FREE_PERCENT,
            "memory_gate_checked_before_torch_or_qutip": True,
            "torch_used": False,
            "qutip_used": False,
            "one_heavy_runtime_at_a_time": True,
        },
        "inputs": {
            "world_events": str(EVENTS),
            "world_events_sha256": sha256_file(EVENTS),
            "world_receipt": str(WORLD_RECEIPT),
            "world_receipt_sha256": sha256_file(WORLD_RECEIPT),
            "stage64_receipt": str(STAGE64),
            "stage64_receipt_sha256": sha256_file(STAGE64),
            "loop2_semantics_source": str(LOOP2_SOURCE),
            "loop2_semantics_source_sha256": sha256_file(LOOP2_SOURCE),
            "loop2_original_receipt": str(LOOP2_RECEIPT),
            "loop2_original_receipt_sha256": sha256_file(LOOP2_RECEIPT),
            "visibility_fix_source": str(VISIBILITY_SOURCE),
            "visibility_fix_source_sha256": sha256_file(VISIBILITY_SOURCE),
            "visibility_fix_receipt": str(FIX_RECEIPT),
            "visibility_fix_receipt_sha256": sha256_file(FIX_RECEIPT),
            "foundation_card": str(FOUNDATION_CARD),
            "foundation_card_sha256": sha256_file(FOUNDATION_CARD),
            "object_preservation_card": str(OBJECT_CARD),
            "object_preservation_card_sha256": sha256_file(OBJECT_CARD),
            "retest_source": str(SOURCE),
            "retest_source_sha256": sha256_file(SOURCE),
            "start_hashes": input_hashes_start,
            "end_hashes": input_hashes_end,
            "schema_metrics": schema_metrics,
            "ground_truth_recovery": recovery_metrics,
        },
        "protocol": {
            "task": "after visible probes of views 0..v, predict each occluded current-world bit at view v",
            "seed": SEED,
            "split": {
                "train_objects": train_objects,
                "test_objects": test_objects,
                "train_count": len(train_objects),
                "test_count": len(test_objects),
                "train_slots": len(train_slots),
                "test_slots": len(test_slots),
                "object_disjoint": not bool(set(train_objects) & set(test_objects)),
                "fingerprint_sha256": split_fingerprint,
            },
            "baseline": "same loop-2 train-selected majority rule: pooled versus per-position selected on train accuracy and applied to test",
            "fixed_update": "after each observed view: 0.5 * F_view(persistent_density) + 0.5 * F_view(initial_density)",
            "original_broken_update": "sequential non-reset F_view(persistent_density) only",
            "engine_readout": "same 15 exact two-qubit Pauli expectations and per-position ridge decoder as loop 2",
            "twin": "same ID3 categorical automaton features and hyperparameters as loop 2",
            "full_visibility_real_task": "all prior views and every non-target current-view bit supplied; queried target remains masked; exact loop-2 readout and per-k chance test",
            "visibility_gate_G4_replication": "supplemental all-eight-bit current-world-state criterion, reported separately and not substituted for the real target-masked verdict",
            "bootstrap": complementarity["bootstrap_unit"],
            "both_random_guard": "both-random is excluded only when at least one lane beats its matched control and union beats the paired union null; useful complementarity further requires both lanes to beat matched controls",
            "ground_truth_boundary": "visible events plus public rule family only; no hidden event field read",
        },
        "results": {
            "computed_baseline": computed_baseline,
            "fixed_engine": {
                "occluded_accuracy": fixed_accuracy,
                "belief_persistence_holevo_bits": fixed_holevo,
                "holevo_by_position_bits": [float(value) for value in fixed_holevo_by_position],
                "holevo_permutation_null_mean_bits": float(fixed_holevo_null.mean()),
                "holevo_permutation_null_p95_bits": float(np.quantile(fixed_holevo_null, 0.95)),
            },
            "twin": {
                "occluded_accuracy": twin_accuracy,
                "tree_nodes": twin_nodes,
                "tree_depth": twin_depth,
            },
            "complementarity": {
                **complementarity,
                "coupling_class": coupling,
                "both_random_confound_excluded": both_random_confound_excluded,
                "at_least_one_lane_above_random": bool(at_least_one_lane_above_random),
                "union_above_joint_shuffled_null": bool(union_above_joint_null),
                "useful_complementarity_eligible": useful_complementarity_eligible,
                "synergy_supported": False,
                "synergy_boundary": "the oracle union table is coverage only; no learned joint combiner was trained or evaluated",
            },
            "prediction_fingerprint_sha256": prediction_fingerprint,
            "episode_level_table": episodes,
            "full_visibility_real_task": target_masked_full_visibility,
            "visibility_gate_G4_replication": {
                "fixed_all_eight_bits_visible": full_fixed,
                "original_broken_all_eight_bits_visible": full_broken,
            },
            "controls": {
                "original_broken_update": {
                    "occluded_accuracy": broken_accuracy,
                    "complementarity_with_twin_counts": broken_table,
                    "belief_persistence_holevo_bits": broken_holevo,
                    "holevo_by_position_bits": [float(value) for value in broken_holevo_by_position],
                    "holevo_permutation_null_mean_bits": float(broken_holevo_null.mean()),
                    "holevo_permutation_null_p95_bits": float(np.quantile(broken_holevo_null, 0.95)),
                },
                "frozen_fixed_engine": {
                    "occluded_accuracy": frozen_accuracy,
                    "belief_persistence_holevo_bits": frozen_holevo,
                    "holevo_by_position_bits": [float(value) for value in frozen_holevo_by_position],
                    "holevo_permutation_null_mean_bits": float(frozen_holevo_null.mean()),
                    "holevo_permutation_null_p95_bits": float(np.quantile(frozen_holevo_null, 0.95)),
                },
                "frozen_original_broken_engine_semantics_lock": {
                    "occluded_accuracy": broken_frozen_accuracy,
                    "expected_original_receipt_accuracy": original_metrics["engine"]["frozen_acc"],
                },
                "shuffled_training_labels": {
                    "draws": N_PERMUTATIONS,
                    "seed": SEED + 31,
                    "paired_engine_twin_label_map": True,
                    "engine_accuracy_mean": float(shuffled_engine_accuracy.mean()),
                    "engine_accuracy_p95": engine_null_p95,
                    "engine_monte_carlo_pvalue": engine_shuffle_pvalue,
                    "twin_accuracy_mean": float(shuffled_twin_accuracy.mean()),
                    "twin_accuracy_p95": twin_null_p95,
                    "twin_monte_carlo_pvalue": twin_shuffle_pvalue,
                    "union_accuracy_mean": float(shuffled_union_accuracy.mean()),
                    "union_accuracy_p95": union_null_p95,
                    "union_monte_carlo_pvalue": union_shuffle_pvalue,
                    "shuffle_scope": "training labels permuted within target position; models refit; true held-out labels unchanged",
                },
            },
            "physicality": physicality,
            "cptp": channel_cptp,
            "fixed_update_equivalence_max_frobenius": fixed_update_equivalence_max,
            "density_trajectories": {
                "path": str(TRAJECTORY_PATH),
                "sha256": sha256_file(TRAJECTORY_PATH),
                "lanes": list(trajectory_receipt["lanes"]),
            },
        },
        "checks": checks,
        "all_pass": all_pass,
        "findings": findings,
        "divergence_log": [
            {
                "comparison": "fixed update versus original broken update",
                "occluded_accuracy_delta": fixed_accuracy - broken_accuracy,
                "holevo_delta_bits": fixed_holevo - broken_holevo,
                "target_masked_full_context_accuracy_delta": target_masked_fixed_accuracy - target_masked_broken_accuracy,
                "all_eight_bits_visible_accuracy_delta": full_fixed["held_out_accuracy"] - full_broken["held_out_accuracy"],
            },
            {
                "comparison": "fixed engine versus classical twin",
                "occluded_accuracy_delta": fixed_accuracy - twin_accuracy,
                "union_gain_over_best": complementarity["metrics"]["union_gain_over_best"]["estimate"],
            },
        ],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "carrier_comparison_executed": False,
        "blocked_consumers": [
            "carrier promotion or scaling",
            "loop-3 carrier tournament",
            "bridge, axis, manifold, physics, or scientific admission",
            "reuse of this result directory",
        ],
        "accepted_status_label": "passes local bounded retest" if all_pass else "runs and retains diagnostic failures",
        "claim_ceiling": (
            "passes a local bounded loop-2 retest only; no carrier comparison, scaling, promotion, or admission"
            if all_pass
            else "runs and retains one or more diagnostic failures; no senses pass, carrier comparison, scaling, promotion, or admission"
        ),
        "receipt_path": str(RECEIPT_PATH),
    }
    return receipt


def main() -> int:
    try:
        refuse_to_reuse()
    except RetestError as error:
        print(str(error), file=sys.stderr)
        return 2

    memory_percent: int | None = None
    try:
        memory_percent = memory_free_percent()
        if memory_percent <= MIN_MEMORY_FREE_PERCENT:
            raise RetestError(
                f"memory free percentage {memory_percent}% is not > {MIN_MEMORY_FREE_PERCENT}%"
            )
    except RetestError as error:
        print(f"FATAL PRE-WRITE: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    try:
        with FIX_RECEIPT.open() as handle:
            preflight_fix = json.load(handle)
        preflight_checks = validate_parent_fix(preflight_fix)
        if not all(preflight_checks.values()):
            failed = [key for key, passed in preflight_checks.items() if not passed]
            raise RetestError(f"parent/source provenance mismatch: {failed}")
        if SIM_PY.resolve() != Path(sys.executable).resolve():
            raise RetestError(
                f"wrong interpreter: {sys.executable}; required realpath {SIM_PY.resolve()}"
            )
    except (OSError, json.JSONDecodeError, RetestError) as error:
        print(f"FATAL PRE-WRITE: {type(error).__name__}: {error}", file=sys.stderr)
        return 2

    OUTDIR.mkdir(parents=True, exist_ok=False)
    try:
        receipt = run(memory_percent)
    except RetestError as error:
        write_fatal_receipt(f"{type(error).__name__}: {error}", memory_percent)
        print(f"FATAL INPUT/RUNTIME: {type(error).__name__}: {error}", file=sys.stderr)
        print(f"fatal receipt written: {RECEIPT_PATH}", file=sys.stderr)
        return 2
    except Exception as error:
        write_fatal_receipt(f"{type(error).__name__}: {error}", memory_percent)
        print(f"FATAL: {type(error).__name__}: {error}", file=sys.stderr)
        print(f"fatal receipt written: {RECEIPT_PATH}", file=sys.stderr)
        return 1

    with RECEIPT_PATH.open("x") as handle:
        json.dump(receipt, handle, indent=2, allow_nan=False)
    print(f"receipt written: {RECEIPT_PATH}")
    print(
        json.dumps(
            {
                "all_pass": receipt["all_pass"],
                "checks": receipt["checks"],
                "findings": receipt["findings"],
                "promotion_allowed": receipt["promotion_allowed"],
                "claim_ceiling": receipt["claim_ceiling"],
            },
            indent=2,
        )
    )
    return 0 if receipt["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
