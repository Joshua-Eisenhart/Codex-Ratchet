#!/usr/bin/env python3
"""
Source-dirty checkpoint planner.

Builds a machine-readable, non-destructive planning surface for remaining
dirty source/config paths. This is intentionally separate from repo hygiene
auditing so detect/classify and plan remain distinct phases.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, UTC
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
REPO_AUDIT_PATH = RESULTS_DIR / "repo_hygiene_audit_results.json"
OUT_PATH = RESULTS_DIR / "source_dirty_checkpoint_plan.json"


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} did not contain an object")
    return payload


def parse_status_path(line: str) -> str:
    payload = line[3:]
    if " -> " in payload:
        payload = payload.split(" -> ", 1)[1]
    return payload.strip().strip('"')


def status_kind(line: str) -> str:
    if line.startswith("?? "):
        return "untracked"
    index_status, worktree_status = line[:2]
    if "R" in (index_status, worktree_status):
        return "renamed"
    if "D" in (index_status, worktree_status):
        return "deleted"
    if "A" in (index_status, worktree_status):
        return "added"
    return "modified"


def classify_group(rel_path: str) -> tuple[str, str, str, str, str]:
    gudhi_groups = {
        "sim_gudhi_3qubit_bridge.py": ("tool_family_gudhi_bridge", "Tool family: gudhi bridge"),
        "sim_gudhi_phase_sensitive_kernel.py": ("tool_family_gudhi_bridge", "Tool family: gudhi bridge"),
        "sim_gudhi_bipartite_entangled.py": ("tool_family_gudhi_bipartite", "Tool family: gudhi bipartite"),
        "sim_gudhi_concurrence_filtration.py": ("tool_family_gudhi_bipartite", "Tool family: gudhi bipartite"),
        "sim_gudhi_bloch_sphere_2d.py": ("tool_family_gudhi_topology", "Tool family: gudhi topology"),
        "sim_gudhi_s2_topology_recovery.py": ("tool_family_gudhi_topology", "Tool family: gudhi topology"),
        "sim_gudhi_cascade_persistence.py": ("tool_family_gudhi_significance", "Tool family: gudhi significance"),
        "sim_gudhi_wasserstein_significance.py": ("tool_family_gudhi_significance", "Tool family: gudhi significance"),
    }
    filename = Path(rel_path).name
    if filename in gudhi_groups:
        label, display_name = gudhi_groups[filename]
        return (
            "probe_source",
            label,
            display_name,
            "manual_split_required",
            f"Active {display_name.lower()} cluster; keep as a bounded semantic batch.",
        )

    xgi_groups = {
        "sim_xgi_gradient_ascent.py": ("tool_family_xgi_exploratory", "Tool family: xgi exploratory"),
        "sim_xgi_torch_autograd.py": ("tool_family_xgi_exploratory", "Tool family: xgi exploratory"),
        "sim_xgi_bridge_hyperedges.py": ("tool_family_xgi_structural", "Tool family: xgi structural"),
        "sim_xgi_dual_hypergraph.py": ("tool_family_xgi_structural", "Tool family: xgi structural"),
        "sim_xgi_family_hypergraph.py": ("tool_family_xgi_structural", "Tool family: xgi structural"),
        "sim_xgi_indirect_pathway.py": ("tool_family_xgi_structural", "Tool family: xgi structural"),
        "sim_xgi_isolate_investigation.py": ("tool_family_xgi_structural", "Tool family: xgi structural"),
        "sim_xgi_l7_marginal.py": ("tool_family_xgi_structural", "Tool family: xgi structural"),
    }
    if filename in xgi_groups:
        label, display_name = xgi_groups[filename]
        safe_next_action = "checkpoint" if label == "tool_family_xgi_structural" else "manual_split_required"
        return (
            "probe_source",
            label,
            display_name,
            safe_next_action,
            (
                f"Active {display_name.lower()} cluster is bounded enough for a scoped checkpoint."
                if safe_next_action == "checkpoint"
                else f"Active {display_name.lower()} cluster; structural and exploratory lanes stay separate."
            ),
        )

    if rel_path.startswith("system_v4/probes/sim_torch_"):
        return (
            "probe_source",
            "torch_family",
            "Torch family sims",
            "manual_split_required",
            "Large active migration/sim cluster in active probe sources.",
        )
    if rel_path.startswith("system_v4/probes/sim_pure_lego_") or rel_path.startswith("system_v4/probes/sim_lego_"):
        return (
            "probe_source",
            "lego_family",
            "Lego and pure-lego sims",
            "manual_split_required",
            "Active probe family; checkpoint in bounded family batches rather than sweeping.",
        )
    tool_groups = {
        "sim_rustworkx_": ("tool_family_rustworkx", "Tool family: rustworkx"),
        "sim_toponetx_": ("tool_family_toponetx", "Tool family: toponetx"),
        "sim_e3nn_": ("tool_family_e3nn", "Tool family: e3nn"),
    }
    for prefix, (label, display_name) in tool_groups.items():
        if rel_path.startswith(f"system_v4/probes/{prefix}"):
            tool_name = label.removeprefix("tool_family_")
            return (
                "probe_source",
                label,
                display_name,
                "manual_split_required",
                f"Active {tool_name} probe cluster; checkpoint by tool family batch, not repo-wide.",
            )
    if rel_path.startswith("system_v4/probes/sim_"):
        stem = Path(rel_path).stem
        remainder = stem[len("sim_") :]
        family = remainder.split("_", 1)[0] if remainder else "misc"
        return (
            "probe_source",
            f"sim_family_{family}",
            f"Probe sim family: {family}",
            "manual_split_required",
            f"Active sim family '{family}' should be checkpointed in a bounded family batch.",
        )
    if rel_path.startswith("system_v4/probes/"):
        return (
            "probe_source",
            "probe_misc",
            "Misc active probes",
            "manual_split_required",
            "Active probe/control sources still mixed together.",
        )
    if rel_path.startswith("system_v4/skills/"):
        return (
            "skill_runtime",
            "skill_runtime",
            "Runtime and skill support",
            "checkpoint",
            "Small bounded runtime-support cluster suitable for a scoped checkpoint.",
        )
    if rel_path.startswith("system_v5/") or rel_path.startswith("system_v3/"):
        return (
            "legacy_runtime",
            "legacy_runtime",
            "Legacy/reference runtime surfaces",
            "archive_review",
            "Legacy/reference surfaces should be reviewed separately from active work.",
        )
    if rel_path in {"Makefile", "requirements-runtime.txt", "requirements-sim-stack.txt", "pyproject.toml"}:
        return (
            "build_contract",
            "build_contract",
            "Build and dependency contract",
            "checkpoint",
            "Core build/runtime contract files should be checkpointed together.",
        )
    if rel_path in {"imessage_bot.py", "telegram_bot.py"}:
        return (
            "root_runtime",
            "root_runtime",
            "Root runtime entrypoints",
            "checkpoint",
            "Root runtime entrypoints changed; checkpoint with build contract if related.",
        )
    if rel_path.startswith("new docs/") or rel_path.startswith("docs/") or rel_path == "CLAUDE.md":
        return (
            "docs_and_specs",
            "docs_and_specs",
            "Docs and specs",
            "checkpoint",
            "Docs/specs are bounded and can be checkpointed separately.",
        )
    return (
        "other_source",
        "other_source",
        "Other source surfaces",
        "manual_split_required",
        "Unclassified source/config residue needs manual grouping before checkpointing.",
    )


def git_source_entries() -> list[dict[str, str]]:
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT_DIR,
        check=False,
        capture_output=True,
        text=True,
    )
    entries: list[dict[str, str]] = []
    for raw in completed.stdout.splitlines():
        if not raw.strip():
            continue
        rel_path = parse_status_path(raw)
        if rel_path.endswith("_results.json"):
            continue
        if "/a2_state/sim_results/" in f"/{rel_path}" or "/probes/sim_results/" in f"/{rel_path}":
            continue
        if rel_path.startswith("results") and rel_path.endswith(".json"):
            continue
        entries.append({
            "path": rel_path,
            "status_kind": status_kind(raw),
        })
    return entries


def main() -> int:
    strict = "--strict" in sys.argv[1:]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    repo_audit = read_json(REPO_AUDIT_PATH)
    source_entries = git_source_entries()

    groups: dict[str, dict[str, Any]] = {}
    for entry in source_entries:
        bucket, label, display_name, safe_next_action, notes = classify_group(entry["path"])
        group_id = f"{bucket}__{label}"
        group = groups.setdefault(
            group_id,
            {
                "group_id": group_id,
                "bucket": bucket,
                "label": label,
                "display_name": display_name,
                "path_prefixes": set(),
                "file_count": 0,
                "tracked_dirty_count": 0,
                "untracked_count": 0,
                "sample_paths": [],
                "dominant_kinds": Counter(),
                "safe_next_action": safe_next_action,
                "safe_auto": False,
                "blocking_reason": "active_source_pressure" if safe_next_action == "manual_split_required" else "bounded_human_checkpoint",
                "notes": notes,
            },
        )
        path = entry["path"]
        group["file_count"] += 1
        if entry["status_kind"] == "untracked":
            group["untracked_count"] += 1
        else:
            group["tracked_dirty_count"] += 1
        group["dominant_kinds"][entry["status_kind"]] += 1
        parts = Path(path).parts
        prefix = "/".join(parts[:3]) if len(parts) >= 3 else path
        group["path_prefixes"].add(prefix)
        if len(group["sample_paths"]) < 8:
            group["sample_paths"].append(path)

    rendered_groups: list[dict[str, Any]] = []
    for group_id in sorted(groups):
        group = groups[group_id]
        rendered_groups.append({
            "group_id": group["group_id"],
            "bucket": group["bucket"],
            "label": group["label"],
            "display_name": group["display_name"],
            "path_prefixes": sorted(group["path_prefixes"]),
            "file_count": group["file_count"],
            "tracked_dirty_count": group["tracked_dirty_count"],
            "untracked_count": group["untracked_count"],
            "sample_paths": group["sample_paths"],
            "dominant_kinds": [
                kind for kind, _count in group["dominant_kinds"].most_common(4)
            ],
            "safe_next_action": group["safe_next_action"],
            "safe_auto": group["safe_auto"],
            "blocking_reason": group["blocking_reason"],
            "notes": group["notes"],
        })

    checkpoint_groups = [g for g in rendered_groups if g["safe_next_action"] == "checkpoint"]
    quarantine_groups = [g for g in rendered_groups if g["safe_next_action"] == "quarantine"]
    manual_only_groups = [g for g in rendered_groups if g["safe_next_action"] in {"manual_split_required", "archive_review"}]
    code_only_manual_groups = [
        g for g in manual_only_groups
        if g["bucket"] not in {"docs_and_specs"}
    ]
    recommended_checkpoint_order = [
        {
            "group_id": g["group_id"],
            "file_count": g["file_count"],
            "safe_next_action": g["safe_next_action"],
        }
        for g in sorted(checkpoint_groups, key=lambda x: (-x["file_count"], x["group_id"]))[:8]
    ]
    recommended_manual_split_order = [
        {
            "group_id": g["group_id"],
            "file_count": g["file_count"],
            "safe_next_action": g["safe_next_action"],
        }
        for g in sorted(manual_only_groups, key=lambda x: (-x["file_count"], x["group_id"]))[:12]
    ]
    recommended_code_only_order = [
        {
            "group_id": g["group_id"],
            "file_count": g["file_count"],
            "untracked_count": g["untracked_count"],
            "tracked_dirty_count": g["tracked_dirty_count"],
            "safe_next_action": g["safe_next_action"],
            "source_path": g["sample_paths"][0] if g["file_count"] == 1 and g["sample_paths"] else None,
            "result_path": (
                f"system_v4/probes/a2_state/sim_results/{Path(g['sample_paths'][0]).stem[len('sim_') :]}_results.json"
                if g["file_count"] == 1 and g["sample_paths"] and Path(g["sample_paths"][0]).name.startswith("sim_")
                else None
            ),
        }
        for g in sorted(
            code_only_manual_groups,
            key=lambda x: (x["file_count"], -x["untracked_count"], x["group_id"].lower()),
        )[:12]
    ]
    next_code_only_manual = recommended_code_only_order[0] if recommended_code_only_order else None

    source_dirty_count = (repo_audit.get("summary") or {}).get("source_dirty_count", 0)
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "strict": strict,
        "source_surface": "repo_hygiene",
        "repo_hygiene_path": str(REPO_AUDIT_PATH.relative_to(PROJECT_DIR)),
        "dirty_source_count": source_dirty_count,
        "plan_group_count": len(rendered_groups),
        "checkpoint_candidate_count": len(checkpoint_groups),
        "quarantine_candidate_count": len(quarantine_groups),
        "manual_only_count": len(manual_only_groups),
        "code_only_manual_count": len(code_only_manual_groups),
        "largest_group_id": max(rendered_groups, key=lambda g: g["file_count"])["group_id"] if rendered_groups else None,
        "next_code_only_manual_group_id": next_code_only_manual["group_id"] if next_code_only_manual else None,
        "next_code_only_manual_file_count": next_code_only_manual["file_count"] if next_code_only_manual else 0,
        "next_code_only_manual_source_path": next_code_only_manual["source_path"] if next_code_only_manual else None,
        "next_code_only_manual_result_path": next_code_only_manual["result_path"] if next_code_only_manual else None,
        "summary": {
            "dirty_source_count": source_dirty_count,
            "plan_group_count": len(rendered_groups),
            "checkpoint_candidate_count": len(checkpoint_groups),
            "quarantine_candidate_count": len(quarantine_groups),
            "manual_only_count": len(manual_only_groups),
            "code_only_manual_count": len(code_only_manual_groups),
            "largest_group_id": max(rendered_groups, key=lambda g: g["file_count"])["group_id"] if rendered_groups else None,
            "next_code_only_manual_group_id": next_code_only_manual["group_id"] if next_code_only_manual else None,
            "next_code_only_manual_file_count": next_code_only_manual["file_count"] if next_code_only_manual else 0,
            "next_code_only_manual_source_path": next_code_only_manual["source_path"] if next_code_only_manual else None,
            "next_code_only_manual_result_path": next_code_only_manual["result_path"] if next_code_only_manual else None,
            "ok": True,
        },
        "rules": {
            "checkpoint": "Bounded source/config cluster suitable for an explicit scoped checkpoint.",
            "quarantine": "Residue cluster that may be isolated later, but not auto-moved here.",
            "archive_review": "Legacy or reference cluster requiring separate ownership review.",
            "manual_split_required": "Active cluster too broad for one safe checkpoint and should be split further.",
        },
        "recommended_checkpoint_order": recommended_checkpoint_order,
        "recommended_manual_split_order": recommended_manual_split_order,
        "recommended_code_only_order": recommended_code_only_order,
        "next_code_only_manual": next_code_only_manual,
        "checkpoint_groups": rendered_groups,
    }

    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"dirty_source_count={report['summary']['dirty_source_count']}")
    print(f"plan_group_count={report['summary']['plan_group_count']}")
    print("SOURCE DIRTY CHECKPOINT PLAN PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
