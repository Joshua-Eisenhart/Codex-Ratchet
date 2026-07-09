#!/usr/bin/env python3
"""Shared finite projection battery for qit_projection_battery_v0.

This packet consumes the qit_full_type1_type2_64_live_v1 finite carrier and
tests whether several partial MMM-style projections converge to the same loop
object. It is a scratch diagnostic, not a production perception claim.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SIM_ID = "qit_projection_battery_v0"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v7" / "sims" / SIM_ID
RESULTS = SIM_DIR / "results"
V1_DIR = ROOT / "system_v7" / "sims" / "qit_full_type1_type2_64_live_v1"
V1_ENVELOPE = V1_DIR / "results" / "qit_full_type1_type2_64_live_v1_envelope_results.json"

if str(V1_DIR) not in sys.path:
    sys.path.insert(0, str(V1_DIR))

from qit_full_type1_type2_64_live_v1_common import (  # noqa: E402
    CLAIM_CEILING as V1_CLAIM_CEILING,
    numeric_feature_matrix,
    object_ids,
    stable_sha256,
)

CLAIM_CEILING = (
    "Projection-battery scout over finite qit_full_type1_type2_64_live_v1 object cards only; "
    "not live perception, Axis0, FEP, production ontology, or Lev mesh graph mutation."
)

VIEW_MASKS = {
    "maintenance_mmm": {0, 1, 4},
    "finance_mmm": {0, 2, 3},
    "safety_mmm": {1, 2, 4},
    "planning_mmm": {0, 1, 7},
    "ontology_mmm": {0, 1, 2, 3, 4, 7},
}

VIEW_DESCRIPTIONS = {
    "maintenance_mmm": "topology/operator/precedence view like asset work-order language",
    "finance_mmm": "topology/result/loop view like quote or margin language",
    "safety_mmm": "operator/result view like risk and compliance language",
    "planning_mmm": "topology/operator/loop/substage view like schedule language",
    "ontology_mmm": "richer domain ontology view that preserves most alignment fields",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_lock(path: Path, role: str) -> dict[str, Any]:
    out: dict[str, Any] = {"path": rel(path), "role": role, "exists": path.exists()}
    if path.exists():
        out["sha256"] = sha256_file(path)
    return out


def canonical_vectors() -> tuple[list[str], list[list[float]]]:
    return numeric_feature_matrix("ordered_full")


def bag_erased_vector(row: list[float]) -> list[float]:
    # The v1 bag-topology control collapses all four loop objects to the same
    # topology multiset. Keep that failure mode explicit here.
    out = [0.0 for _ in row]
    out[:4] = [4.0, 4.0, 4.0, 4.0]
    return out


def projection_vector(row: list[float], view: str, control: str | None = None) -> list[float]:
    if control == "bag_erased":
        return bag_erased_vector(row)
    if control == "view_erased":
        return [0.0 for _ in row]
    mask = VIEW_MASKS[view]
    out = []
    for idx, value in enumerate(row):
        out.append(float(value) if idx % 8 in mask else 0.0)
    return out


def projection_records(control: str | None = None) -> list[dict[str, Any]]:
    labels, rows = canonical_vectors()
    records = []
    for object_index, (object_id, row) in enumerate(zip(labels, rows, strict=True)):
        for view in VIEW_MASKS:
            vector = projection_vector(row, view, control=control)
            records.append(
                {
                    "object_index": object_index,
                    "object_id": object_id,
                    "view": view,
                    "view_description": VIEW_DESCRIPTIONS[view],
                    "vector": vector,
                    "vector_sha256": stable_sha256(vector),
                    "control": control or "none",
                }
            )
    return records


def euclidean_sq(left: list[float], right: list[float]) -> float:
    return sum((float(a) - float(b)) ** 2 for a, b in zip(left, right, strict=True))


def leave_one_view_centroid(control: str | None = None) -> dict[str, Any]:
    labels = object_ids()
    records = projection_records(control=control)
    view_results = []
    for heldout_view in VIEW_MASKS:
        train = [row for row in records if row["view"] != heldout_view]
        test = [row for row in records if row["view"] == heldout_view]
        centroids = {}
        for object_id in labels:
            rows = [row["vector"] for row in train if row["object_id"] == object_id]
            centroids[object_id] = [sum(values) / len(rows) for values in zip(*rows, strict=True)]
        predictions = []
        for row in test:
            distances = {
                object_id: euclidean_sq(row["vector"], centroid)
                for object_id, centroid in centroids.items()
            }
            predicted = min(distances, key=distances.get)
            predictions.append(
                {
                    "object_id": row["object_id"],
                    "predicted_object_id": predicted,
                    "correct": predicted == row["object_id"],
                    "distance_to_prediction": distances[predicted],
                }
            )
        accuracy = sum(1 for row in predictions if row["correct"]) / len(predictions)
        view_results.append(
            {
                "heldout_view": heldout_view,
                "accuracy": round(accuracy, 12),
                "predictions": predictions,
            }
        )
    mean_accuracy = sum(row["accuracy"] for row in view_results) / len(view_results)
    return {
        "control": control or "none",
        "view_count": len(VIEW_MASKS),
        "object_count": len(labels),
        "mean_heldout_accuracy": round(mean_accuracy, 12),
        "min_heldout_accuracy": round(min(row["accuracy"] for row in view_results), 12),
        "view_results": view_results,
    }


def projection_collision_report(control: str | None = None) -> dict[str, Any]:
    records = projection_records(control=control)
    by_view = {}
    for view in VIEW_MASKS:
        rows = [row for row in records if row["view"] == view]
        buckets = Counter(row["vector_sha256"] for row in rows)
        by_view[view] = {
            "unique_signature_count": len(buckets),
            "bucket_sizes": sorted(buckets.values(), reverse=True),
        }
    all_buckets = Counter(row["vector_sha256"] for row in records)
    return {
        "control": control or "none",
        "by_view": by_view,
        "global_unique_signature_count": len(all_buckets),
        "global_bucket_sizes": sorted(all_buckets.values(), reverse=True),
    }


def object_cards_from_projection_battery() -> list[dict[str, Any]]:
    labels, rows = canonical_vectors()
    cards = []
    for object_id, row in zip(labels, rows, strict=True):
        view_hashes = {
            view: stable_sha256(projection_vector(row, view))
            for view in VIEW_MASKS
        }
        anti_hashes = {
            "bag_erased": stable_sha256(bag_erased_vector(row)),
            "view_erased": stable_sha256(projection_vector(row, "maintenance_mmm", control="view_erased")),
        }
        cards.append(
            {
                "schema": f"cr.{SIM_ID}.projection_object_card.v1",
                "object_id": object_id,
                "survivor_hash": stable_sha256({"object_id": object_id, "views": view_hashes}),
                "projection_hashes": view_hashes,
                "anti_hashes": anti_hashes,
                "claim_ceiling": CLAIM_CEILING,
            }
        )
    return cards


def build_core_measurement() -> dict[str, Any]:
    nominal = leave_one_view_centroid()
    bag = leave_one_view_centroid(control="bag_erased")
    view_erased = leave_one_view_centroid(control="view_erased")
    collisions = {
        "nominal": projection_collision_report(),
        "bag_erased": projection_collision_report(control="bag_erased"),
        "view_erased": projection_collision_report(control="view_erased"),
    }
    gates = {
        "nominal_mean_accuracy_at_least_0_85": nominal["mean_heldout_accuracy"] >= 0.85,
        "nominal_beats_bag_by_half": nominal["mean_heldout_accuracy"] - bag["mean_heldout_accuracy"] >= 0.5,
        "nominal_beats_view_erased_by_half": nominal["mean_heldout_accuracy"] - view_erased["mean_heldout_accuracy"] >= 0.5,
        "bag_erased_at_chance": bag["mean_heldout_accuracy"] <= 0.25,
        "view_erased_at_chance": view_erased["mean_heldout_accuracy"] <= 0.25,
    }
    return {
        "nominal": nominal,
        "controls": {
            "bag_erased": bag,
            "view_erased": view_erased,
        },
        "projection_collisions": collisions,
        "object_cards": object_cards_from_projection_battery(),
        "gates": gates,
        "all_pass": all(gates.values()),
    }
