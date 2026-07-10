#!/usr/bin/env python3
"""Fail-closed metric and gate recomputation for frozen v1 raw outputs.

This module never imports or calls the learner. It treats the per-view JSON
arrays as the only learned evidence and independently rebuilds JS, retrieval,
matched-pair decisions, baseline comparisons, and every primary gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import torch


classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "nonclassical"
TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent reconstruction of JS, retrieval, pair decisions, and frozen gates from raw outputs",
    }
}
TOOL_INTEGRATION_DEPTH = {"torch": "load_bearing"}

HERE = Path(__file__).resolve().parent
SOURCE_PATH = HERE / "run_pytorch.py"
RECOMPUTE_PATH = Path(__file__).resolve()
SPEC_PATH = HERE / "spec.json"
MANIFEST_PATH = HERE / "object_manifest.json"
DEFAULT_RESULT_PATH = HERE / "results" / "pytorch_result.json"
HORIZONS = (3, 4, 5, 6, 7, 8)
SEGMENTS = tuple(2**length for length in range(1, 9))
TARGET_COORDINATES = sum(SEGMENTS)
ARM_NAMES = ("full", "temporal_shuffle", "histogram", "fixed_deranged", "optimizer_erased", "architecture_only")


def arm_seed_plan(spec: dict[str, Any]) -> dict[str, tuple[int, ...]]:
    seeds = tuple(int(value) for value in spec["view_process"]["model_seeds"])
    return {
        "full": seeds,
        "temporal_shuffle": seeds,
        "histogram": seeds,
        "fixed_deranged": (seeds[0],),
        "optimizer_erased": seeds,
        "architecture_only": seeds,
    }


class RecomputeError(RuntimeError):
    pass


def reject_constant(token: str) -> None:
    raise RecomputeError(f"non-finite JSON constant: {token}")


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise RecomputeError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def assert_finite(value: Any, path: str = "value") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise RecomputeError(f"non-finite value at {path}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert_finite(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_finite(item, f"{path}[{index}]")


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RecomputeError(f"missing input: {path}")
    value = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant, object_pairs_hook=reject_duplicates)
    if not isinstance(value, dict):
        raise RecomputeError(f"expected JSON object: {path}")
    assert_finite(value, str(path))
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def word_probability(machine: list[list[int]], start: int, word: list[int]) -> float:
    state = start
    probability = 1.0
    for bit in word:
        next_zero, next_one, p_one = machine[state]
        probability *= (p_one if bit else 8 - p_one) / 8.0
        state = next_one if bit else next_zero
    return probability


def target_tensor(machine: list[list[int]]) -> Tensor:
    segments: list[torch.Tensor] = []
    for length in range(1, 9):
        values = []
        for index in range(2**length):
            word = [(index >> (length - position - 1)) & 1 for position in range(length)]
            values.append(sum(word_probability(machine, state, word) for state in range(4)) / 4.0)
        segment = torch.tensor(values, dtype=torch.float64)
        segment /= segment.sum()
        segments.append(segment.float())
    return torch.cat(segments)


def js_by_segment(predictions: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    values = []
    for predicted, target in zip(predictions.split(SEGMENTS, dim=-1), targets.split(SEGMENTS, dim=-1), strict=True):
        midpoint = 0.5 * (predicted + target)
        left = 0.5 * (predicted * (predicted.clamp_min(1e-12).log() - midpoint.clamp_min(1e-12).log())).sum(dim=-1)
        right = 0.5 * (target * (target.clamp_min(1e-12).log() - midpoint.clamp_min(1e-12).log())).sum(dim=-1)
        values.append(left + right)
    return torch.stack(values, dim=-1)


def parse_rows(rows: list[Any], name: str) -> tuple[torch.Tensor, torch.Tensor, list[dict[str, Any]]]:
    if len(rows) != 256:
        raise RecomputeError(f"{name} must contain exactly 256 views")
    seen: set[int] = set()
    embeddings: list[list[float]] = []
    predictions: list[list[float]] = []
    labels: list[int] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise RecomputeError(f"{name}[{index}] is not an object")
        required = {"view_index", "object_label", "normalized_embedding", "segmented_prediction", "per_horizon_js", "retrieval_neighbor_index", "retrieval_correct"}
        if not required.issubset(row):
            raise RecomputeError(f"{name}[{index}] is missing raw output fields")
        if row["view_index"] != index or index in seen:
            raise RecomputeError(f"duplicate or noncanonical view index in {name}")
        seen.add(index)
        label = row["object_label"]
        if not isinstance(label, int) or not 0 <= label < 32:
            raise RecomputeError(f"invalid controller-only label in {name}[{index}]")
        embedding = row["normalized_embedding"]
        if not isinstance(embedding, list) or not embedding:
            raise RecomputeError(f"missing embedding in {name}[{index}]")
        norm = math.sqrt(sum(float(value) ** 2 for value in embedding))
        if not math.isfinite(norm) or abs(norm - 1.0) > 2e-4:
            raise RecomputeError(f"embedding is not normalized in {name}[{index}]")
        segments = row["segmented_prediction"]
        if not isinstance(segments, list) or len(segments) != 8 or [len(item) for item in segments] != list(SEGMENTS):
            raise RecomputeError(f"prediction segmentation drift in {name}[{index}]")
        flat = [float(value) for segment in segments for value in segment]
        if len(flat) != TARGET_COORDINATES or any(value < 0.0 or not math.isfinite(value) for value in flat):
            raise RecomputeError(f"invalid prediction in {name}[{index}]")
        offset = 0
        for width in SEGMENTS:
            if abs(sum(flat[offset : offset + width]) - 1.0) > 2e-5:
                raise RecomputeError(f"prediction segment is not normalized in {name}[{index}]")
            offset += width
        embeddings.append([float(value) for value in embedding])
        predictions.append(flat)
        labels.append(label)
    return torch.tensor(embeddings, dtype=torch.float32), torch.tensor(predictions, dtype=torch.float32), torch.tensor(labels, dtype=torch.long)


def recompute_rows(rows: list[dict[str, Any]], predictions: torch.Tensor, targets: torch.Tensor) -> dict[str, Any]:
    embeddings = torch.tensor([row["normalized_embedding"] for row in rows], dtype=torch.float32)
    labels = torch.tensor([row["object_label"] for row in rows], dtype=torch.long)
    js = js_by_segment(predictions, targets)
    similarity = embeddings @ embeddings.T
    similarity.fill_diagonal_(-torch.inf)
    neighbors = similarity.argmax(dim=1)
    correct = labels[neighbors] == labels
    for index, row in enumerate(rows):
        expected_js = {str(h): float(js[index, h - 1]) for h in HORIZONS}
        if row["retrieval_neighbor_index"] != int(neighbors[index]) or row["retrieval_correct"] is not bool(correct[index]):
            raise RecomputeError(f"frozen retrieval receipt mismatch at view {index}")
        for key, value in expected_js.items():
            if abs(float(row["per_horizon_js"].get(key, math.nan)) - value) > 2e-6:
                raise RecomputeError(f"frozen JS receipt mismatch at view {index}, horizon {key}")
    object_js = torch.stack([js[labels == index][:, [h - 1 for h in HORIZONS]].mean(dim=0) for index in range(32)])
    return {
        "view_count": len(rows),
        "object_count": len(set(labels.tolist())),
        "loo_same_object_retrieval": float(correct.float().mean()),
        "per_horizon_predictive_js_mean": {str(h): float(object_js[:, index].mean()) for index, h in enumerate(HORIZONS)},
        "per_horizon_predictive_js_max": {str(h): float(object_js[:, index].max()) for index, h in enumerate(HORIZONS)},
        "per_object_predictive_js": object_js.tolist(),
        "retrieval_neighbor_indices": neighbors.tolist(),
        "retrieval_correct": correct.tolist(),
    }


def exact_train_mean(manifest: dict[str, Any]) -> torch.Tensor:
    return torch.stack([target_tensor(row["machine"]) for row in manifest["splits"]["train"]]).mean(dim=0)


def matched_pairs(manifest: dict[str, Any], rows: list[dict[str, Any]], predictions: torch.Tensor) -> list[dict[str, Any]]:
    labels = torch.tensor([row["object_label"] for row in rows], dtype=torch.long)
    target_by_object = torch.stack([target_tensor(row["machine"]) for row in manifest["splits"]["test"]])
    targets = target_by_object[labels]
    js = js_by_segment(predictions, targets)[:, [h - 1 for h in HORIZONS]]
    object_js = torch.stack([js[labels == index].mean(dim=0) for index in range(32)])
    hash_to_object = {row["machine_sha256"]: index for index, row in enumerate(manifest["splits"]["test"])}
    decisions = []
    for pair_index, pair in enumerate(manifest["test_pairing"]["pairs"]):
        left = hash_to_object[pair["left_machine_sha256"]]
        right = hash_to_object[pair["right_machine_sha256"]]
        left_better = bool(object_js[left].mean() < object_js[right].mean())
        right_better = bool(object_js[right].mean() < object_js[left].mean())
        decisions.append({
            "pair_index": pair_index,
            "left_object_index": left,
            "right_object_index": right,
            "left_own_target_prediction": left_better,
            "right_own_target_prediction": right_better,
            "both_members_own_target_prediction": left_better and right_better,
        })
    return decisions


def compare_float_maps(actual: Any, expected: Any, path: str) -> None:
    if isinstance(expected, float):
        if not isinstance(actual, (float, int)) or abs(float(actual) - expected) > 2e-6:
            raise RecomputeError(f"metric drift at {path}")
        return
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise RecomputeError(f"metric schema drift at {path}")
        for key in expected:
            compare_float_maps(actual[key], expected[key], f"{path}.{key}")
        return
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise RecomputeError(f"metric list drift at {path}")
        for index, item in enumerate(expected):
            compare_float_maps(actual[index], item, f"{path}[{index}]")
        return
    if actual != expected:
        raise RecomputeError(f"metric drift at {path}")


def recompute_gates(arm_metrics: dict[str, dict[str, dict[str, Any]]], baseline_metrics: dict[str, dict[str, dict[str, Any]]], pairs: dict[str, list[dict[str, Any]]], spec: dict[str, Any]) -> dict[str, Any]:
    gate_spec = spec["metrics_and_gates"]
    predictive_spec = {
        name: (float(values["max"]), int(values["wins"]))
        for name, values in gate_spec["predictive_js"].items()
        if isinstance(values, dict)
    }
    by_seed: dict[str, Any] = {}
    for seed_value in spec["view_process"]["model_seeds"]:
        seed = str(seed_value)
        full = arm_metrics["full"][seed]
        histogram = arm_metrics["histogram"][seed]
        temporal = arm_metrics["temporal_shuffle"][seed]
        current: dict[str, Any] = {
            "loo_same_object_retrieval_min": full["loo_same_object_retrieval"] >= float(gate_spec["loo_same_object_retrieval_min"]),
            "loo_retrieval_gain_over_each_of_histogram_and_temporal_min": {
                "histogram": full["loo_same_object_retrieval"] - histogram["loo_same_object_retrieval"] >= float(gate_spec["loo_same_object_retrieval_gain_over_each_of_histogram_and_temporal_min"]),
                "temporal_shuffle": full["loo_same_object_retrieval"] - temporal["loo_same_object_retrieval"] >= float(gate_spec["loo_same_object_retrieval_gain_over_each_of_histogram_and_temporal_min"]),
            },
            "own_target_prediction": sum(row["both_members_own_target_prediction"] for row in pairs[seed]) >= int(gate_spec["full_observation_horizon_matched_own_target_prediction"]["both_members_own_target_min"]),
        }
        predictive: dict[str, Any] = {}
        for name, (maximum, wins_min) in predictive_spec.items():
            arm_name = "temporal_shuffle" if name == "temporal" else name
            baseline = baseline_metrics[seed][name] if name in ("train_mean", "order2_laplace") else arm_metrics[arm_name][seed]
            wins = {}
            max_ok = {}
            for horizon in HORIZONS:
                key = str(horizon)
                wins[key] = sum(full["per_object_predictive_js"][index][horizon - 3] < baseline["per_object_predictive_js"][index][horizon - 3] for index in range(32))
                max_ok[key] = max(row[horizon - 3] for row in baseline["per_object_predictive_js"]) <= maximum
            predictive[name] = {
                "wins_by_horizon": wins,
                "wins_min": wins_min,
                "baseline_max_by_horizon_within_spec": max_ok,
                "all_horizons_win_gate": all(value >= wins_min for value in wins.values()),
                "all_horizons_baseline_max_gate": all(max_ok.values()),
            }
        current["predictive_js"] = predictive
        current["primary_pass"] = all([
            current["loo_same_object_retrieval_min"],
            all(current["loo_retrieval_gain_over_each_of_histogram_and_temporal_min"].values()),
            current["own_target_prediction"],
            all(item["all_horizons_win_gate"] and item["all_horizons_baseline_max_gate"] for item in predictive.values()),
        ])
        by_seed[seed] = current
    return {
        "thresholds_from_spec": {
            "loo_same_object_retrieval_min": float(gate_spec["loo_same_object_retrieval_min"]),
            "loo_same_object_retrieval_gain_over_each_of_histogram_and_temporal_min": float(gate_spec["loo_same_object_retrieval_gain_over_each_of_histogram_and_temporal_min"]),
            "own_target_prediction": gate_spec["full_observation_horizon_matched_own_target_prediction"],
            "predictive_js": predictive_spec,
        },
        "by_seed": by_seed,
        "all_primary_gates_every_seed": all(item["primary_pass"] for item in by_seed.values()),
        "temporal_jacrev_supportive_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_RESULT_PATH)
    args = parser.parse_args()
    spec = load_json(SPEC_PATH)
    manifest = load_json(MANIFEST_PATH)
    result = load_json(args.input)
    if spec.get("engine_contract", {}).get("mode") != "all_three_full_sims":
        raise RecomputeError("engine mode drift")
    if spec.get("view_process", {}).get("seed_domain") != "ufpo-v1|view|split|machine-hash|view-index|trajectory-index|channel":
        raise RecomputeError("view seed-domain drift")
    if spec.get("accepted_green_ceiling") != "BOUNDED_SUPERVISED_MULTI_VIEW_PREDICTIVE_RETRIEVAL_ON_UNSEEN_FOUR_STATE_OBJECTS_UNDER_FROZEN_LOSSY_VIEWS":
        raise RecomputeError("green claim ceiling drift")
    if result.get("schema") != "codex_ratchet.unseen_finite_predictive_objects_v1.pytorch_result.v1":
        raise RecomputeError("unexpected result schema")
    if result.get("spec_sha256") != sha256_file(SPEC_PATH) or result.get("object_manifest_sha256") != sha256_file(MANIFEST_PATH):
        raise RecomputeError("spec or manifest hash drift")
    if result.get("source_sha256") != sha256_file(SOURCE_PATH):
        raise RecomputeError("runner source hash drift")
    if result.get("recompute_metrics_sha256") != sha256_file(RECOMPUTE_PATH):
        raise RecomputeError("recompute source hash drift")
    arm_results = result.get("arm_results")
    baseline_results = result.get("baseline_results")
    if not isinstance(arm_results, dict) or set(arm_results) != set(ARM_NAMES) or not isinstance(baseline_results, dict):
        raise RecomputeError("arm or baseline result schema drift")
    raw_payload = {"arm_results": {}, "baseline_results": {}}
    arm_metrics: dict[str, dict[str, dict[str, Any]]] = {arm: {} for arm in ARM_NAMES}
    seed_plan = arm_seed_plan(spec)
    for arm in ARM_NAMES:
        expected_seeds = {str(seed) for seed in seed_plan[arm]}
        if set(arm_results[arm]) != expected_seeds:
            raise RecomputeError(f"seed plan drift for {arm}")
        raw_payload["arm_results"][arm] = {}
        for seed in sorted(expected_seeds):
            row = arm_results[arm][seed]
            embeddings, predictions, labels = parse_rows(row.get("raw_outputs"), f"{arm}:{seed}")
            targets = torch.stack([target_tensor(item["machine"]) for item in manifest["splits"]["test"]])[labels]
            metrics = recompute_rows(row["raw_outputs"], predictions, targets)
            compare_float_maps(row.get("metrics"), metrics, f"arm_results.{arm}.{seed}.metrics")
            arm_metrics[arm][seed] = metrics
            raw_payload["arm_results"][arm][seed] = row["raw_outputs"]
    expected_model_seeds = {str(seed) for seed in spec["view_process"]["model_seeds"]}
    if set(baseline_results) != expected_model_seeds:
        raise RecomputeError("baseline seed plan drift")
    baseline_metrics: dict[str, dict[str, dict[str, Any]]] = {}
    for seed in sorted(baseline_results):
        baseline_metrics[seed] = {}
        raw_payload["baseline_results"][seed] = {}
        if set(baseline_results[seed]) != {"train_mean", "order2_laplace"}:
            raise RecomputeError(f"baseline arm drift for {seed}")
        for name in ("train_mean", "order2_laplace"):
            row = baseline_results[seed][name]
            _, predictions, _ = parse_rows(row.get("raw_outputs"), f"baseline:{name}:{seed}")
            labels = torch.tensor([item["object_label"] for item in row["raw_outputs"]], dtype=torch.long)
            embeddings = torch.ones((256, 1), dtype=torch.float32)
            targets = torch.stack([target_tensor(item["machine"]) for item in manifest["splits"]["test"]])[labels]
            metrics = recompute_rows(row["raw_outputs"], predictions, targets)
            compare_float_maps(row.get("metrics"), metrics, f"baseline_results.{seed}.{name}.metrics")
            baseline_metrics[seed][name] = metrics
            raw_payload["baseline_results"][seed][name] = row["raw_outputs"]
    pairs: dict[str, list[dict[str, Any]]] = {}
    for seed in sorted(expected_model_seeds):
        _, predictions, _ = parse_rows(arm_results["full"][seed]["raw_outputs"], f"full:{seed}")
        decisions = matched_pairs(manifest, arm_results["full"][seed]["raw_outputs"], predictions)
        compare_float_maps(result["matched_pair_decisions"][seed], decisions, f"matched_pair_decisions.{seed}")
        pairs[seed] = decisions
    gates = recompute_gates(arm_metrics, baseline_metrics, pairs, spec)
    compare_float_maps(result.get("gates"), gates, "gates")
    if result.get("all_pass") is not gates["all_primary_gates_every_seed"]:
        raise RecomputeError("all_pass drift")
    if result.get("raw_outputs_sha256") != sha256_json(raw_payload):
        raise RecomputeError("raw output hash drift")
    summary = {
        "schema": "codex_ratchet.unseen_finite_predictive_objects_v1.recompute_receipt.v1",
        "input": str(args.input.resolve()),
        "source_sha256": sha256_file(SOURCE_PATH),
        "spec_sha256": sha256_file(SPEC_PATH),
        "object_manifest_sha256": sha256_file(MANIFEST_PATH),
        "raw_outputs_sha256": sha256_json(raw_payload),
        "all_primary_gates_every_seed": gates["all_primary_gates_every_seed"],
        "all_pass": gates["all_primary_gates_every_seed"],
        "retrained": False,
    }
    print(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
