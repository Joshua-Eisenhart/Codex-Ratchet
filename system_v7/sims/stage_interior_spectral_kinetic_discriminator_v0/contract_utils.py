#!/usr/bin/env python3
"""Standard-library helpers for the hashed JSON/NPZ runtime contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
stage_movement_allowed = False
TOOL_MANIFEST = {
    "sha256_json_npz_contract": {
        "used": True,
        "reason": "Provides shared fail-closed hashing, canonical JSON, and bounded classifier gate helpers.",
    }
}
TOOL_INTEGRATION_DEPTH = {"sha256_json_npz_contract": "supportive"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value), encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_contract(manifest_path: Path, npz_path: Path) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    observed = sha256(npz_path)
    expected = manifest["npz_sha256"]
    if observed != expected:
        raise ValueError(f"NPZ hash mismatch: expected {expected}, observed {observed}")
    return manifest


def summarize_classifier(
    labels: Any,
    distances: Any,
) -> dict[str, Any]:
    """Summarize nearest-centroid distances; lower distance wins."""
    import numpy as np

    labels_array = np.asarray(labels, dtype=int)
    distance_array = np.asarray(distances, dtype=float)
    predicted = np.argmin(distance_array, axis=1)
    correct_distance = distance_array[np.arange(len(labels_array)), labels_array]
    wrong_distance = distance_array[np.arange(len(labels_array)), 1 - labels_array]
    margins = wrong_distance - correct_distance
    return {
        "sample_count": int(len(labels_array)),
        "accuracy": float(np.mean(predicted == labels_array)),
        "mean_paired_margin": float(np.mean(margins)),
        "median_paired_margin": float(np.median(margins)),
        "minimum_paired_margin": float(np.min(margins)),
        "predicted_counts": {
            "order_0": int(np.sum(predicted == 0)),
            "order_1": int(np.sum(predicted == 1)),
        },
    }


def gate_lane(spec: dict[str, Any], evaluations: dict[str, dict[str, Any]]) -> dict[str, bool]:
    clean = evaluations["clean"]
    clean_advantage = clean["accuracy"] - 0.5
    clean_margin = clean["mean_paired_margin"]
    controls = [evaluations[name] for name in ("temporal_shuffle", "block_permutation", "reversal")]
    return {
        "clean_accuracy_above_preregistered_floor": clean["accuracy"] >= spec["minimum_clean_accuracy"],
        "clean_paired_margin_positive": clean_margin >= spec["minimum_clean_paired_margin"],
        "all_control_accuracy_advantages_collapse": all(
            abs(control["accuracy"] - 0.5) <= spec["maximum_control_accuracy_advantage"]
            for control in controls
        ),
        "all_control_margins_collapse_relative_to_clean": clean_margin > 0.0
        and all(
            abs(control["mean_paired_margin"])
            <= spec["maximum_control_margin_fraction"] * clean_margin
            for control in controls
        ),
        "clean_advantage_is_positive": clean_advantage > 0.0,
    }
