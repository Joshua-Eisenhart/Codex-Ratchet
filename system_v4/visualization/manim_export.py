from __future__ import annotations

import json
from pathlib import Path

from system_v4.visualization.inspection import inspect_run_dir


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _final_entities(run_dir: Path) -> list[dict]:
    frame_paths = sorted((Path(run_dir) / "frames").glob("*.json"))
    if not frame_paths:
        return []
    final_frame = _load_json(frame_paths[-1])
    entities = final_frame.get("entities", [])
    return entities if isinstance(entities, list) else []


def collect_manim_export(run_dir: Path) -> dict:
    run_dir = Path(run_dir)
    report = inspect_run_dir(run_dir)
    witness_trace = _load_json(run_dir / "witness_trace.json")
    final_entities = _final_entities(run_dir)

    admitted_survivors = []
    for entity in final_entities:
        survivor = {
            "entity_id": entity.get("entity_id"),
            "entity_kind": entity.get("entity_kind"),
            "tags": dict(entity.get("tags", {})),
            "scalar_keys": sorted(dict(entity.get("scalars", {})).keys()),
        }
        for field_name in (
            "base_xyz",
            "projected_s3_xyz",
            "points_xyz",
            "line_indices",
            "cell_indices",
            "seam_edges",
            "transition_meta",
            "patch_id",
            "chart_id",
            "chart_neighbors",
        ):
            if field_name in entity:
                survivor[field_name] = entity.get(field_name)
        admitted_survivors.append(survivor)

    return {
        "run_id": report["run_id"],
        "run_dir": report["run_dir"],
        "sim_name": report["sim_name"],
        "constraint_set": report.get("constraint_set"),
        "probe_family": report.get("probe_family"),
        "carrier": report.get("carrier"),
        "lane": report.get("lane"),
        "layer": report.get("layer"),
        "status_label": report.get("status_label"),
        "claim_state": report.get("claim_state"),
        "promotion_status": report.get("promotion_status"),
        "geometry_rendering_status": report.get("geometry_rendering_status"),
        "witnesses": {
            "witness_type": report.get("witness_type"),
            "witness_trace_id": report.get("witness_trace_id"),
            "event_count": report.get("witness_event_count", 0),
            "events": list(witness_trace.get("events", [])),
        },
        "exclusions": {
            "negative_controls": list(report.get("negative_controls", [])),
            "required_negatives": list(report.get("required_negatives", [])),
            "negatives_run": list(report.get("negatives_run", [])),
            "kill_conditions": list(report.get("kill_conditions", [])),
            "exclusion_criteria": list(report.get("exclusion_criteria", [])),
            "exclusion_event_count": report.get("exclusion_event_count", 0),
            "exclusion_events": list(witness_trace.get("exclusion_events", [])),
            "blocked_consumers": list(report.get("blocked_consumers", [])),
            "promotion_blockers": list(report.get("promotion_blockers", [])),
        },
        "admitted_survivors": admitted_survivors,
        "lane_progression": {
            "admission_stage": report.get("admission_stage"),
            "promotion_target_stage": report.get("promotion_target_stage"),
            "lane_admission": dict(report.get("lane_admission", {})),
            "live_splits": list(report.get("live_splits", [])),
        },
        "validation": {
            "validation_ok": report.get("validation_ok"),
            "validation_errors": list(report.get("validation_errors", [])),
            "validation_warnings": list(report.get("validation_warnings", [])),
            "summary_all_pass": report.get("summary_all_pass"),
        },
        "evidence_paths": dict(report.get("evidence_paths", {})),
    }


def collect_batch_manim_export(roots: list[Path]) -> dict:
    run_dirs: list[Path] = []
    for root in roots:
        run_dirs.extend(path.parent for path in sorted(Path(root).rglob("run_manifest.json")))

    exports = [collect_manim_export(run_dir) for run_dir in sorted({Path(run_dir) for run_dir in run_dirs})]

    lane_counts: dict[str, int] = {}
    for item in exports:
        lane = item.get("lane") or "unknown"
        lane_counts[lane] = lane_counts.get(lane, 0) + 1

    return {
        "roots": [str(Path(root)) for root in roots],
        "run_count": len(exports),
        "lane_counts": dict(sorted(lane_counts.items())),
        "runs": exports,
    }
