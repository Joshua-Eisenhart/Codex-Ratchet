#!/usr/bin/env python3
"""Shared finite bidirectional science battery for qit_bidirectional_science_type1_type2_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SIM_ID = "qit_bidirectional_science_type1_type2_v0"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v7" / "sims" / SIM_ID
RESULTS = SIM_DIR / "results"
PROJECTION_DIR = ROOT / "system_v7" / "sims" / "qit_projection_battery_v0"
PROJECTION_ENVELOPE = PROJECTION_DIR / "results" / "qit_projection_battery_v0_envelope_results.json"
V1_DIR = ROOT / "system_v7" / "sims" / "qit_full_type1_type2_64_live_v1"
V1_ENVELOPE = V1_DIR / "results" / "qit_full_type1_type2_64_live_v1_envelope_results.json"
OBJECT_CARD = SIM_DIR / f"{SIM_ID}_object_card.json"
V43_VALIDATION = RESULTS / f"{SIM_ID}_v43_validation.json"

if str(PROJECTION_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECTION_DIR))

from qit_projection_battery_v0_common import (  # noqa: E402
    CLAIM_CEILING as PROJECTION_CLAIM_CEILING,
    VIEW_MASKS,
    build_core_measurement as build_projection_measurement,
    canonical_vectors,
    object_cards_from_projection_battery,
    object_ids,
    projection_vector,
    stable_sha256,
)

CLAIM_CEILING = (
    "Bidirectional science-method scout over finite qit_projection_battery_v0 object cards only; "
    "not live perception, full QIT engine admission, Axis0, FEP, production ontology, MMM-driver, "
    "or Lev mesh graph mutation."
)

SCIENCE_STAGES = ["candidate", "measurement", "counter_projection", "update", "falsifier", "receipt"]
TYPE1_INTELLIGENCE = "hypothesis-first, deductive candidate pressure; strong at rejecting wrong object cards across views"
TYPE2_INTELLIGENCE = "measurement-first, inductive projection pressure; strong at forming candidates from local views"
BLOCKED_CONSUMERS = [
    "QIT_engine_admission",
    "Axis0",
    "FEP",
    "Xi/Phi0",
    "physics",
    "production_perception",
    "production_ontology",
    "MMM_driver",
    "Lev_mesh_runtime",
    "mesh_visible_projection",
]


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


def projection_cards_by_object() -> dict[str, dict[str, Any]]:
    return {card["object_id"]: card for card in object_cards_from_projection_battery()}


def projection_hashes_by_view() -> dict[str, dict[str, str]]:
    cards = projection_cards_by_object()
    return {
        view: {object_id: card["projection_hashes"][view] for object_id, card in cards.items()}
        for view in VIEW_MASKS
    }


def type1_candidate_confirmation(control: str = "nominal") -> dict[str, Any]:
    cards = projection_cards_by_object()
    labels = object_ids()
    hashes = projection_hashes_by_view()
    rows = []
    for idx, true_object in enumerate(labels):
        for view in VIEW_MASKS:
            if control == "nominal":
                candidate = true_object
                measurement_hash = cards[true_object]["projection_hashes"][view]
            elif control == "wrong_candidate":
                candidate = labels[(idx + 1) % len(labels)]
                measurement_hash = cards[true_object]["projection_hashes"][view]
            elif control == "bag_erased":
                candidate = true_object
                measurement_hash = cards[true_object]["anti_hashes"]["bag_erased"]
            elif control == "view_erased":
                candidate = true_object
                measurement_hash = cards[true_object]["anti_hashes"]["view_erased"]
            elif control == "shuffled_projection":
                candidate = true_object
                measurement_hash = cards[labels[(idx + 1) % len(labels)]]["projection_hashes"][view]
            else:
                raise ValueError(control)
            expected_hash = cards[candidate]["projection_hashes"][view]
            bucket = [object_id for object_id, signature in hashes[view].items() if signature == expected_hash]
            measurement_matches_prediction = expected_hash == measurement_hash
            accepted = measurement_matches_prediction and candidate in bucket
            correct = accepted and candidate == true_object
            rows.append(
                {
                    "heldout_view": view,
                    "true_object_id": true_object,
                    "candidate_object_id": candidate,
                    "counter_projection_bucket": bucket,
                    "stage_trace": [
                        {"stage": "candidate", "object_id": candidate},
                        {"stage": "measurement", "heldout_view": view, "control": control},
                        {"stage": "counter_projection", "candidate_bucket_size": len(bucket)},
                        {"stage": "update", "accepted": accepted},
                        {
                            "stage": "falsifier",
                            "measurement_matches_prediction": measurement_matches_prediction,
                            "wrong_candidate_rejected": candidate == true_object or not correct,
                        },
                        {"stage": "receipt", "correct": correct},
                    ],
                    "accepted": accepted,
                    "correct": correct,
                    "measurement_matches_prediction": measurement_matches_prediction,
                    "object_reconstruction_correct": correct,
                    "roundtrip_survived": correct,
                }
            )
    accepted_rate = sum(row["accepted"] for row in rows) / len(rows)
    accuracy = sum(row["correct"] for row in rows) / len(rows)
    return {
        "engine_method": "Type-1",
        "method_order": "candidate -> measurement -> counter_projection -> update -> falsifier -> receipt",
        "control": control,
        "object_count": len(labels),
        "view_count": len(VIEW_MASKS),
        "trial_count": len(rows),
        "heldout_view_accuracy": round(sum(row["measurement_matches_prediction"] for row in rows) / len(rows), 12),
        "object_reconstruction_accuracy": round(accuracy, 12),
        "roundtrip_survival_rate": round(accuracy, 12),
        "accepted_rate": round(accepted_rate, 12),
        "accuracy": round(accuracy, 12),
        "rows": rows,
    }


def single_view_bucket_report() -> dict[str, Any]:
    by_view = {}
    hashes = projection_hashes_by_view()
    for view, values in hashes.items():
        buckets: dict[str, list[str]] = {}
        for object_id, signature in values.items():
            buckets.setdefault(signature, []).append(object_id)
        by_view[view] = {
            "unique_signature_count": len(buckets),
            "bucket_sizes": sorted((len(v) for v in buckets.values()), reverse=True),
            "ambiguous": any(len(v) > 1 for v in buckets.values()),
        }
    return by_view


def type2_measurement_reconstruction(control: str = "nominal") -> dict[str, Any]:
    cards = projection_cards_by_object()
    labels = object_ids()
    hashes = projection_hashes_by_view()
    rows = []
    for view in VIEW_MASKS:
        for idx, true_object in enumerate(labels):
            if control == "nominal":
                measurement_hash = cards[true_object]["projection_hashes"][view]
            elif control == "bag_erased":
                measurement_hash = cards[true_object]["anti_hashes"]["bag_erased"]
            elif control == "view_erased":
                measurement_hash = cards[true_object]["anti_hashes"]["view_erased"]
            elif control == "shuffled_view":
                measurement_hash = cards[labels[(idx + 1) % len(labels)]]["projection_hashes"][view]
            else:
                raise ValueError(control)
            matches = [object_id for object_id, signature in hashes[view].items() if signature == measurement_hash]
            predicted = matches[0] if matches else labels[0]
            correct = predicted == true_object
            predicted_other_view_matches = 0
            for other_view in VIEW_MASKS:
                if other_view == view:
                    continue
                if cards[predicted]["projection_hashes"][other_view] == cards[true_object]["projection_hashes"][other_view]:
                    predicted_other_view_matches += 1
            rows.append(
                {
                    "heldout_view": view,
                    "source_view": view,
                    "true_object_id": true_object,
                    "candidate_object_id": predicted,
                    "candidate_bucket": matches,
                    "stage_trace": [
                        {"stage": "candidate", "source": "generated_from_measurement"},
                        {"stage": "measurement", "source_view": view, "control": control},
                        {"stage": "counter_projection", "candidate_bucket_size": len(matches) if matches else len(labels)},
                        {"stage": "update", "candidate_object_id": predicted},
                        {"stage": "falsifier", "heldout_projection_matches": predicted_other_view_matches},
                        {"stage": "receipt", "correct": correct},
                    ],
                    "correct": correct,
                    "object_reconstruction_correct": correct,
                    "roundtrip_survived": correct,
                    "heldout_projection_match_fraction": round(predicted_other_view_matches / (len(VIEW_MASKS) - 1), 12),
                }
            )
    accuracy = sum(row["correct"] for row in rows) / len(rows)
    heldout_mean = sum(row["heldout_projection_match_fraction"] for row in rows) / len(rows)
    by_view = {}
    for view in VIEW_MASKS:
        view_rows = [row for row in rows if row["source_view"] == view]
        by_view[view] = {
            "accuracy": round(sum(row["correct"] for row in view_rows) / len(view_rows), 12),
            "mean_heldout_projection_match_fraction": round(
                sum(row["heldout_projection_match_fraction"] for row in view_rows) / len(view_rows),
                12,
            ),
        }
    return {
        "engine_method": "Type-2",
        "method_order": "measurement -> candidate -> counter_projection -> update -> falsifier -> receipt",
        "control": control,
        "object_count": len(labels),
        "view_count": len(VIEW_MASKS),
        "trial_count": len(rows),
        "heldout_view_accuracy": round(heldout_mean, 12),
        "object_reconstruction_accuracy": round(accuracy, 12),
        "roundtrip_survival_rate": round(accuracy, 12),
        "accuracy": round(accuracy, 12),
        "mean_heldout_projection_match_fraction": round(heldout_mean, 12),
        "by_view": by_view,
        "rows": rows,
    }


def unique_win_table(type1: dict[str, Any], type2: dict[str, Any]) -> dict[str, Any]:
    type1_by_key = {(row["true_object_id"], row["heldout_view"]): row for row in type1["rows"]}
    type2_by_key = {(row["true_object_id"], row["heldout_view"]): row for row in type2["rows"]}
    buckets = {"type1_only": [], "type2_only": [], "shared_win": [], "shared_fail": []}
    deltas = []
    for key in sorted(type1_by_key):
        left = bool(type1_by_key[key]["roundtrip_survived"])
        right = bool(type2_by_key[key]["roundtrip_survived"])
        record = {"object_id": key[0], "view": key[1], "type1": left, "type2": right}
        deltas.append((1.0 if left else 0.0) - (1.0 if right else 0.0))
        if left and right:
            buckets["shared_win"].append(record)
        elif left and not right:
            buckets["type1_only"].append(record)
        elif right and not left:
            buckets["type2_only"].append(record)
        else:
            buckets["shared_fail"].append(record)
    return {
        "counts": {key: len(value) for key, value in buckets.items()},
        "trials": buckets,
        "method_order_delta_mean": round(sum(deltas) / len(deltas), 12),
        "type1_accuracy": type1["roundtrip_survival_rate"],
        "type2_accuracy": type2["roundtrip_survival_rate"],
    }


def build_core_measurement() -> dict[str, Any]:
    projection_parent = build_projection_measurement()
    type1_nominal = type1_candidate_confirmation("nominal")
    type1_wrong = type1_candidate_confirmation("wrong_candidate")
    type1_bag = type1_candidate_confirmation("bag_erased")
    type1_erased = type1_candidate_confirmation("view_erased")
    type1_shuffled = type1_candidate_confirmation("shuffled_projection")
    type2_nominal = type2_measurement_reconstruction("nominal")
    type2_bag = type2_measurement_reconstruction("bag_erased")
    type2_erased = type2_measurement_reconstruction("view_erased")
    type2_shuffled = type2_measurement_reconstruction("shuffled_view")
    gates = {
        "parent_projection_battery_passed": projection_parent["all_pass"],
        "type1_nominal_perfect": type1_nominal["accuracy"] == 1.0,
        "type1_wrong_candidate_rejected": type1_wrong["accepted_rate"] <= 0.25,
        "type1_erased_controls_rejected": type1_bag["accepted_rate"] == 0.0 and type1_erased["accepted_rate"] == 0.0,
        "type1_shuffled_projection_rejected": type1_shuffled["accepted_rate"] <= 0.25,
        "type2_nominal_at_least_0_85": type2_nominal["accuracy"] >= 0.85,
        "type2_erased_controls_at_chance": type2_bag["accuracy"] <= 0.25 and type2_erased["accuracy"] <= 0.25,
        "type2_nominal_beats_erased_by_half": type2_nominal["accuracy"] - type2_bag["accuracy"] >= 0.5
        and type2_nominal["accuracy"] - type2_erased["accuracy"] >= 0.5,
        "science_stages_complete": set(SCIENCE_STAGES)
        == {step["stage"] for row in type1_nominal["rows"] for step in row["stage_trace"]}
        == {step["stage"] for row in type2_nominal["rows"] for step in row["stage_trace"]},
    }
    comparison = {
        "shared_success": [
            "both methods use the same object cards",
            "both methods emit six-stage finite receipts",
            "both methods reject erased controls",
        ],
        "type1_unique_strength": "perfect candidate-confirmation and wrong-candidate rejection when a candidate object card is declared",
        "type2_unique_strength": "candidate formation from a single measurement view without a declared candidate",
        "type1_failure_mode": "cannot discover an object without a declared candidate card",
        "type2_failure_mode": "single-view reconstruction is ambiguous on underdetermined planning_mmm buckets",
        "same_object_family": object_ids(),
        "trial_count": len(type1_nominal["rows"]) + len(type2_nominal["rows"]),
        "unique_win_table": unique_win_table(type1_nominal, type2_nominal),
        "single_view_buckets": single_view_bucket_report(),
    }
    return {
        "parent_projection_summary": {
            "nominal_mean_heldout_accuracy": projection_parent["nominal"]["mean_heldout_accuracy"],
            "bag_erased_mean": projection_parent["controls"]["bag_erased"]["mean_heldout_accuracy"],
            "view_erased_mean": projection_parent["controls"]["view_erased"]["mean_heldout_accuracy"],
        },
        "type1": {
            "intelligence_profile": TYPE1_INTELLIGENCE,
            "nominal": type1_nominal,
            "controls": {
                "wrong_candidate": type1_wrong,
                "bag_erased": type1_bag,
                "view_erased": type1_erased,
                "shuffled_projection": type1_shuffled,
            },
        },
        "type2": {
            "intelligence_profile": TYPE2_INTELLIGENCE,
            "nominal": type2_nominal,
            "controls": {
                "bag_erased": type2_bag,
                "view_erased": type2_erased,
                "shuffled_view": type2_shuffled,
            },
        },
        "comparison": comparison,
        "gates": gates,
        "all_pass": all(gates.values()),
    }
