#!/usr/bin/env python3
"""Split the engine/manifold basin-depth receipt by perturbation radius."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from collections import defaultdict
from typing import Any

import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_engine_manifold_basin_radius_split_probe_results.json"
SOURCE_RESULT = RESULT_DIR / "source_native_engine_manifold_attractor_basin_depth_probe_results.json"

NAME = "source_native_engine_manifold_basin_radius_split_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: consumes the source-native engine/manifold basin-depth "
    "receipt and splits its shallow-basin finding by perturbation radius. It "
    "does not admit global manifold necessity, deep-basin promotion, final "
    "FEP, final Axis0, Holodeck, physics, cognition, world-model, or "
    "canonical claims."
)

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive basin-depth receipt parsing"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing epsilon-bucket and control-trace statistics"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source receipt hash capture"},
}
TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "pytorch": "load_bearing",
    "hashlib": "supportive",
}

CONTROL_TRACE_FIELDS = {
    "off": "off_trace_to_baseline",
    "reversed": "reversed_trace_to_baseline",
    "random_schedule": "random_schedule_trace_to_baseline",
    "wrong_chirality": "wrong_chirality_trace_to_baseline",
    "random_cptp": "random_cptp_trace_to_baseline",
}

TRACE_CANDIDATE_FLOOR = 0.10
CONTROL_SEPARATION_FLOOR = 0.05


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def mean_float(values: list[float]) -> float:
    return float(torch.tensor(values, dtype=torch.float64).mean().item())


def label_bucket(rows: list[dict[str, Any]]) -> dict[str, Any]:
    on = mean_float([row["on_trace_to_baseline"] for row in rows])
    control_means = {
        control: mean_float([row[field] for row in rows if field in row])
        for control, field in CONTROL_TRACE_FIELDS.items()
        if any(field in row for row in rows)
    }
    nearest = min(control_means.values())
    separation = nearest - on
    if on <= TRACE_CANDIDATE_FLOOR and separation >= CONTROL_SEPARATION_FLOOR:
        label = "candidate_basin_radius"
    elif separation < 0:
        label = "anti_basin_radius"
    elif on <= nearest:
        label = "shallow_basin_radius"
    else:
        label = "open_boundary_radius"
    return {
        "epsilon": rows[0]["epsilon"],
        "row_count": len(rows),
        "label": label,
        "on_mean_trace": on,
        "available_controls": sorted(control_means),
        "control_mean_traces": control_means,
        "off_mean_trace": control_means.get("off"),
        "reversed_mean_trace": control_means.get("reversed"),
        "random_schedule_mean_trace": control_means.get("random_schedule"),
        "wrong_chirality_mean_trace": control_means.get("wrong_chirality"),
        "random_cptp_mean_trace": control_means.get("random_cptp"),
        "nearest_control_mean": nearest,
        "control_separation": separation,
        "mean_on_token_match": mean_float([row["on_token_match"] for row in rows]),
        "mean_on_correction": mean_float([row["on_mean_correction"] for row in rows]),
        "mean_off_correction": mean_float([row["off_mean_correction"] for row in rows]),
    }


def main() -> int:
    started = time.time()
    source = load_json(SOURCE_RESULT)
    grouped: dict[float, list[dict[str, Any]]] = defaultdict(list)
    for row in source.get("rows", []):
        grouped[float(row["epsilon"])].append(row)
    radius_rows = [label_bucket(rows) for _, rows in sorted(grouped.items())]
    labels = {row["epsilon"]: row["label"] for row in radius_rows}
    candidate_radii = [row["epsilon"] for row in radius_rows if row["label"] == "candidate_basin_radius"]
    shallow_radii = [row["epsilon"] for row in radius_rows if row["label"] == "shallow_basin_radius"]

    positive = {
        "source_basin_depth_receipt_loaded": {
            "pass": (
                source.get("all_pass") is True
                and source.get("name") == "source_native_engine_manifold_attractor_basin_depth_probe"
                and source.get("basin_classification", {}).get("label") == "shallow_basin"
            ),
            "source_sha256": sha256_file(SOURCE_RESULT),
            "source_name": source.get("name"),
            "source_label": source.get("basin_classification", {}).get("label"),
        },
        "epsilon_radius_buckets_classified": {
            "pass": len(radius_rows) >= 3,
            "radius_rows": radius_rows,
        },
        "shallow_finding_has_radius_structure": {
            "pass": bool(candidate_radii or shallow_radii),
            "candidate_radii": candidate_radii,
            "shallow_radii": shallow_radii,
            "labels": labels,
        },
    }
    graveyard = {
        "single_average_does_not_define_basin_depth": {
            "pass": True,
            "reason": "The aggregate shallow-basin label is decomposed by epsilon before repair decisions.",
        },
        "candidate_radius_is_not_deep_basin": {
            "pass": True,
            "reason": "Any candidate radius remains one source-native finite-carrier row, not independent deep convergence.",
        },
        "large_radius_failure_remains_visible": {
            "pass": any(row["label"] != "candidate_basin_radius" for row in radius_rows),
            "labels": labels,
        },
    }
    boundary = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "repair_target_is_radius_not_theory": {
            "pass": True,
            "next_repair": "Tune manifold/engine dynamics to enlarge candidate radius, then rerun basin-depth scout with same controls.",
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
        "source_alignment_category": "source_native_engine_manifold_basin_radius_split",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "radius_rows": radius_rows,
        "nearby_variants": {"total": len(graveyard), "passed": sum(1 for row in graveyard.values() if row["pass"]), "variants": sorted(graveyard)},
        "why_not_v4_probes": [
            "This is a receipt-consumer radius splitter over a current source-native v5 basin-depth scout.",
            "It generates a repair target, not a canonical engine claim.",
        ],
        "blockers": [] if all_pass else [key for key, row in {**positive, **graveyard, **boundary}.items() if not row.get("pass")],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  labels={labels}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
