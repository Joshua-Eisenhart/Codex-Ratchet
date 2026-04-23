#!/usr/bin/env python3
"""
System hygiene supervisor.

Combines the local hygiene surfaces with the existing truth/controller/migration
surfaces into one machine-readable maintenance report and repair backlog.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
OUT_PATH = RESULTS_DIR / "system_hygiene_supervisor_results.json"

TRUTH_AUDIT_PATH = RESULTS_DIR / "probe_truth_audit_results.json"
CONTROLLER_AUDIT_PATH = RESULTS_DIR / "controller_alignment_audit_results.json"
MIGRATION_AUDIT_PATH = RESULTS_DIR / "migration_contract_audit_results.json"
REPO_HYGIENE_PATH = RESULTS_DIR / "repo_hygiene_audit_results.json"
RUNTIME_HYGIENE_PATH = RESULTS_DIR / "runtime_hygiene_audit_results.json"
STATE_DIR_OWNERSHIP_AUDIT_PATH = RESULTS_DIR / "state_dir_ownership_audit_results.json"
LEGO_TOOL_REPORTING_AUDIT_PATH = RESULTS_DIR / "lego_tool_reporting_audit_results.json"
SOURCE_DIRTY_PLAN_PATH = RESULTS_DIR / "source_dirty_checkpoint_plan.json"
SOURCE_DIRTY_LANE_MANIFEST_PATH = RESULTS_DIR / "source_dirty_lane_manifest.json"


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text())
    except Exception:  # noqa: BLE001
        return None
    return payload if isinstance(payload, dict) else None


def surface_missing(path: Path, label: str) -> dict[str, Any]:
    return {
        "kind": "missing_surface",
        "surface": label,
        "path": str(path.relative_to(PROJECT_DIR)),
    }


def dedupe_repair_queue(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: dict[tuple[str, str], int] = {}
    for item in items:
        key = (str(item.get("kind")), str(item.get("action_class")))
        existing_idx = seen.get(key)
        if existing_idx is None:
            seen[key] = len(deduped)
            deduped.append(item)
            continue
        existing = deduped[existing_idx]
        # Prefer richer ownership-aware entries over generic repo-hygiene duplicates.
        if len(item.keys()) > len(existing.keys()):
            deduped[existing_idx] = item
    return deduped


def main() -> int:
    strict = "--strict" in sys.argv[1:]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    paths = {
        "truth": TRUTH_AUDIT_PATH,
        "controller": CONTROLLER_AUDIT_PATH,
        "migration": MIGRATION_AUDIT_PATH,
        "repo_hygiene": REPO_HYGIENE_PATH,
        "runtime_hygiene": RUNTIME_HYGIENE_PATH,
        "state_dir_ownership": STATE_DIR_OWNERSHIP_AUDIT_PATH,
        "lego_tool_reporting": LEGO_TOOL_REPORTING_AUDIT_PATH,
        "source_dirty_checkpoint": SOURCE_DIRTY_PLAN_PATH,
        "source_dirty_lane_manifest": SOURCE_DIRTY_LANE_MANIFEST_PATH,
    }

    payloads: dict[str, dict[str, Any] | None] = {
        name: read_json(path) for name, path in paths.items()
    }

    missing_surfaces = [
        surface_missing(path, name)
        for name, path in paths.items()
        if payloads[name] is None
    ]

    truth_summary = (payloads["truth"] or {}).get("summary", {})
    controller_summary = (payloads["controller"] or {}).get("summary", {})
    migration_summary = (payloads["migration"] or {}).get("summary", {})
    repo_summary = (payloads["repo_hygiene"] or {}).get("summary", {})
    runtime_summary = (payloads["runtime_hygiene"] or {}).get("summary", {})
    state_dir_summary = (payloads["state_dir_ownership"] or {}).get("summary", {})
    lego_tool_reporting_summary = (payloads["lego_tool_reporting"] or {}).get("summary", {})
    repo_git = (payloads["repo_hygiene"] or {}).get("git", {})
    source_dirty_plan = payloads["source_dirty_checkpoint"] or {}
    source_dirty_plan_summary = (payloads["source_dirty_checkpoint"] or {}).get("summary", {})
    source_dirty_lane_manifest_summary = (payloads["source_dirty_lane_manifest"] or {}).get("summary", {})

    truth_ok = bool(truth_summary.get("ok"))
    controller_ok = bool(controller_summary.get("code_process_green")) and bool(controller_summary.get("controller_contract_current"))
    migration_ok = bool(migration_summary.get("ok"))
    repo_ok = bool(repo_summary.get("ok"))
    runtime_ok = bool(runtime_summary.get("ok"))
    state_dir_ok = bool(state_dir_summary.get("ok"))
    lego_tool_reporting_ok = bool(lego_tool_reporting_summary.get("ok"))

    repair_queue: list[dict[str, Any]] = []
    for surface_name in ("repo_hygiene", "runtime_hygiene", "state_dir_ownership"):
        payload = payloads.get(surface_name) or {}
        for candidate in payload.get("repair_candidates", []):
            if isinstance(candidate, dict):
                enriched = dict(candidate)
                enriched["source_surface"] = surface_name
                repair_queue.append(enriched)
    repair_queue = dedupe_repair_queue(repair_queue)

    safe_auto_queue = [item for item in repair_queue if item.get("safe_auto") is True]
    manual_queue = [item for item in repair_queue if item.get("safe_auto") is not True]

    if not truth_ok:
        repair_queue.append({
            "source_surface": "truth",
            "kind": "truth_audit_failed",
            "action_class": "repair_truth_surface",
            "safe_auto": False,
            "recommendation": "Resolve hard truth-audit findings before further promotion.",
        })
    if not controller_ok:
        repair_queue.append({
            "source_surface": "controller",
            "kind": "controller_contract_not_current",
            "action_class": "repair_controller_surface",
            "safe_auto": False,
            "recommendation": "Bring docs/process/controller back to a green state before unattended loops.",
        })
    if not migration_ok:
        repair_queue.append({
            "source_surface": "migration",
            "kind": "migration_contract_not_current",
            "action_class": "repair_migration_surface",
            "safe_auto": False,
            "recommendation": "Fix extracted family metadata/module mismatches before expanding the migration lane.",
        })

    overall_green = (
        len(missing_surfaces) == 0
        and truth_ok
        and controller_ok
        and migration_ok
        and repo_ok
        and runtime_ok
        and state_dir_ok
        and lego_tool_reporting_ok
        and len(repair_queue) == 0
    )

    summary = {
        "missing_surface_count": len(missing_surfaces),
        "repair_queue_count": len(repair_queue),
        "safe_auto_repair_count": len(safe_auto_queue),
        "manual_repair_count": len(manual_queue),
        "truth_green": truth_ok,
        "controller_green": controller_ok,
        "migration_green": migration_ok,
        "repo_hygiene_green": repo_ok,
        "runtime_hygiene_green": runtime_ok,
        "state_dir_ownership_green": state_dir_ok,
        "lego_tool_reporting_green": lego_tool_reporting_ok,
        "overall_green": overall_green,
    }

    maintenance_lanes = [
        {
            "lane": "build",
            "standard_name": "feature_delivery",
            "purpose": "Main feature, sim, or migration work.",
        },
        {
            "lane": "truth",
            "standard_name": "integrity_verification",
            "purpose": "Rerun touched sims and preserve result/source honesty.",
        },
        {
            "lane": "hygiene",
            "standard_name": "repository_maintenance",
            "purpose": "Keep repo placement, state surfaces, and runtime organization bounded.",
        },
        {
            "lane": "contract",
            "standard_name": "contract_governance",
            "purpose": "Keep controller, docs, and process surfaces enforceable.",
        },
    ]

    process_model = {
        "name": "closed_loop_maintenance",
        "phases": [
            "detect",
            "classify",
            "plan",
            "remediate",
            "verify",
            "gate",
        ],
    }

    surface_catalog = {
        "truth": "integrity_verification",
        "controller": "contract_compliance",
        "migration": "migration_compliance",
        "repo_hygiene": "repository_hygiene",
        "runtime_hygiene": "runtime_environment",
        "state_dir_ownership": "state_dir_governance",
        "lego_tool_reporting": "tool_reporting_compliance",
    }

    source_dirty_surface = {
        "source_dirty_count": repo_summary.get("source_dirty_count", 0),
        "dirty_source_bucket_count": repo_summary.get("dirty_source_bucket_count", 0),
        "dirty_source_buckets": repo_git.get("dirty_source_buckets", []),
        "top_dirty_prefixes": repo_git.get("top_dirty_prefixes", []),
        "checkpoint_recommended": bool(repo_summary.get("source_dirty_count", 0)),
    }

    source_dirty_checkpoint = {
        "present": payloads["source_dirty_checkpoint"] is not None,
        "path": str(SOURCE_DIRTY_PLAN_PATH.relative_to(PROJECT_DIR)),
        "status": (
            "current"
            if payloads["source_dirty_checkpoint"] is not None
            else "missing"
        ),
        "dirty_source_checkpoint_required": bool(repo_summary.get("source_dirty_count", 0)),
        "plan_group_count": source_dirty_plan_summary.get("plan_group_count", 0),
        "largest_group_id": source_dirty_plan_summary.get("largest_group_id"),
        "next_code_only_manual": source_dirty_plan.get("next_code_only_manual"),
        "recommended_code_only_order": source_dirty_plan.get("recommended_code_only_order", [])[:5],
    }

    source_dirty_lane_manifest = {
        "present": payloads["source_dirty_lane_manifest"] is not None,
        "path": str(SOURCE_DIRTY_LANE_MANIFEST_PATH.relative_to(PROJECT_DIR)),
        "status": (
            "current"
            if payloads["source_dirty_lane_manifest"] is not None
            else "missing"
        ),
        "required": bool(repo_summary.get("source_dirty_count", 0)),
        "selected_group_id": source_dirty_lane_manifest_summary.get("selected_group_id"),
        "file_count": source_dirty_lane_manifest_summary.get("file_count", 0),
        "docs_opt_in_required": source_dirty_lane_manifest_summary.get("docs_opt_in_required", False),
        "code_only_fallback_group_id": source_dirty_lane_manifest_summary.get("code_only_fallback_group_id"),
        "active_actionable_lane_group_id": source_dirty_lane_manifest_summary.get("active_actionable_lane_group_id"),
    }
    active_actionable_lane = (payloads["source_dirty_lane_manifest"] or {}).get("active_actionable_lane")
    lego_tool_reporting_surface = {
        "present": payloads["lego_tool_reporting"] is not None,
        "path": str(LEGO_TOOL_REPORTING_AUDIT_PATH.relative_to(PROJECT_DIR)),
        "status": (
            "current"
            if payloads["lego_tool_reporting"] is not None
            else "missing"
        ),
        "blocker_count": lego_tool_reporting_summary.get("blocker_count", 0),
        "advisory_count": lego_tool_reporting_summary.get("advisory_count", 0),
        "registry_linked_result_count": lego_tool_reporting_summary.get("registry_linked_result_count", 0),
        "issue_kind_counts": lego_tool_reporting_summary.get("issue_kind_counts", {}),
        "ok": lego_tool_reporting_ok,
    }
    state_dir_ownership_surface = {
        "present": payloads["state_dir_ownership"] is not None,
        "path": str(STATE_DIR_OWNERSHIP_AUDIT_PATH.relative_to(PROJECT_DIR)),
        "status": (
            "current"
            if payloads["state_dir_ownership"] is not None
            else "missing"
        ),
        "blocker_count": state_dir_summary.get("blocker_count", 0),
        "advisory_count": state_dir_summary.get("advisory_count", 0),
        "ok": state_dir_ok,
    }

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "strict": strict,
        "overall_green": summary["overall_green"],
        "repair_queue_count": summary["repair_queue_count"],
        "safe_auto_repair_count": summary["safe_auto_repair_count"],
        "manual_repair_count": summary["manual_repair_count"],
        "truth_green": summary["truth_green"],
        "controller_green": summary["controller_green"],
        "migration_green": summary["migration_green"],
        "repo_hygiene_green": summary["repo_hygiene_green"],
        "runtime_hygiene_green": summary["runtime_hygiene_green"],
        "state_dir_ownership_green": summary["state_dir_ownership_green"],
        "lego_tool_reporting_green": summary["lego_tool_reporting_green"],
        "active_actionable_lane": active_actionable_lane,
        "summary": summary,
        "process_model": process_model,
        "surface_catalog": surface_catalog,
        "lego_tool_reporting_surface": lego_tool_reporting_surface,
        "state_dir_ownership_surface": state_dir_ownership_surface,
        "source_dirty_surface": source_dirty_surface,
        "source_dirty_checkpoint": source_dirty_checkpoint,
        "source_dirty_lane_manifest": source_dirty_lane_manifest,
        "maintenance_lanes": maintenance_lanes,
        "missing_surfaces": missing_surfaces,
        "repair_queue": repair_queue,
        "safe_auto_queue": safe_auto_queue,
        "manual_queue": manual_queue,
        "surface_status": {
            "truth": truth_summary,
            "controller": controller_summary,
            "migration": migration_summary,
            "repo_hygiene": repo_summary,
            "runtime_hygiene": runtime_summary,
            "state_dir_ownership": state_dir_summary,
            "lego_tool_reporting": lego_tool_reporting_summary,
            "source_dirty_checkpoint": source_dirty_plan_summary,
            "source_dirty_lane_manifest": source_dirty_lane_manifest_summary,
        },
    }

    OUT_PATH.write_text(json.dumps(report, indent=2))
    print(f"Wrote {OUT_PATH}")
    print(f"overall_green={summary['overall_green']}")
    print(f"repair_queue_count={summary['repair_queue_count']}")

    if strict and not summary["overall_green"]:
        print("SYSTEM HYGIENE SUPERVISOR FAILED")
        return 1

    if not summary["overall_green"]:
        print("SYSTEM HYGIENE SUPERVISOR WARN")
    else:
        print("SYSTEM HYGIENE SUPERVISOR PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
