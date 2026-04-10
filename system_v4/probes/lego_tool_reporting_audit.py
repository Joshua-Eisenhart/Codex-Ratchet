#!/usr/bin/env python3
"""
Registry-linked lego tool-reporting audit.

Consumes:
  - actual_lego_registry.json

Emits:
  - lego_tool_reporting_audit_results.json

Goal:
  keep registry-linked canonical results honest about tool reporting by
  flagging missing tool surfaces and blank manifest reasons on the machine
  result path already selected by the registry.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
REGISTRY_PATH = RESULTS_DIR / "actual_lego_registry.json"
OUT_PATH = RESULTS_DIR / "lego_tool_reporting_audit_results.json"


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} did not contain an object")
    return payload


def summarize_result_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_result: dict[str, dict[str, Any]] = {}
    for row in rows:
        result_name = row.get("machine_best_result")
        if not result_name:
            continue
        entry = by_result.setdefault(
            result_name,
            {
                "lego_ids": [],
                "probe_paths": set(),
                "sections": set(),
                "classifications": set(),
            },
        )
        lego_id = row.get("lego_id")
        if lego_id:
            entry["lego_ids"].append(lego_id)
        probe_path = row.get("machine_best_probe")
        if probe_path:
            entry["probe_paths"].add(probe_path)
        section = row.get("section")
        if section:
            entry["sections"].add(section)
        classification = row.get("machine_result_classification")
        if classification:
            entry["classifications"].add(classification)

    for value in by_result.values():
        value["lego_ids"].sort()
        value["probe_paths"] = sorted(value["probe_paths"])
        value["sections"] = sorted(value["sections"])
        value["classifications"] = sorted(value["classifications"])
    return by_result


def used_tools_from_manifest(tool_manifest: Any) -> list[str]:
    if not isinstance(tool_manifest, dict):
        return []
    return sorted(
        tool
        for tool, meta in tool_manifest.items()
        if isinstance(meta, dict) and meta.get("used") is True
    )


def blank_reason_tools(tool_manifest: Any) -> list[str]:
    if not isinstance(tool_manifest, dict):
        return []
    return sorted(
        tool
        for tool, meta in tool_manifest.items()
        if isinstance(meta, dict)
        and meta.get("tried") is True
        and meta.get("used") is not True
        and not str(meta.get("reason", "")).strip()
    )


def unresolved_used_tools(tool_manifest: Any, tool_depth: Any) -> list[str]:
    used_tools = used_tools_from_manifest(tool_manifest)
    if not used_tools:
        return []
    if tool_depth is None:
        return used_tools
    if not isinstance(tool_depth, dict):
        return []
    unresolved: list[str] = []
    for tool in used_tools:
        value = tool_depth.get(tool)
        if value in (None, "", {}, []):
            unresolved.append(tool)
    return sorted(unresolved)


def finding(
    *,
    severity: str,
    kind: str,
    result_name: str,
    registry_entry: dict[str, Any],
    detail: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "severity": severity,
        "kind": kind,
        "result_json": result_name,
        "result_path": str((RESULTS_DIR / result_name).relative_to(PROJECT_DIR)),
        "lego_ids": registry_entry["lego_ids"],
        "probe_paths": registry_entry["probe_paths"],
        "sections": registry_entry["sections"],
        "classifications": registry_entry["classifications"],
        "detail": detail,
    }
    if extra:
        payload.update(extra)
    return payload


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    registry = read_json(REGISTRY_PATH)
    rows = registry.get("rows", [])
    if not isinstance(rows, list):
        raise ValueError("actual_lego_registry rows must be a list")

    registry_by_result = summarize_result_rows(rows)
    blockers: list[dict[str, Any]] = []
    advisories: list[dict[str, Any]] = []
    issue_kind_counts: defaultdict[str, int] = defaultdict(int)

    for result_name, registry_entry in sorted(registry_by_result.items()):
        result_path = RESULTS_DIR / result_name
        if not result_path.exists():
            issue_kind_counts["missing_result"] += 1
            blockers.append(
                finding(
                    severity="blocker",
                    kind="missing_result",
                    result_name=result_name,
                    registry_entry=registry_entry,
                    detail="Registry-selected result file is missing.",
                )
            )
            continue

        result_payload = read_json(result_path)
        tool_manifest = result_payload.get("tool_manifest")
        tool_depth = result_payload.get("tool_integration_depth")

        if tool_manifest is None:
            issue_kind_counts["missing_tool_manifest"] += 1
            blockers.append(
                finding(
                    severity="blocker",
                    kind="missing_tool_manifest",
                    result_name=result_name,
                    registry_entry=registry_entry,
                    detail="Registry-selected result is missing tool_manifest.",
                )
            )

        if tool_depth is None:
            issue_kind_counts["missing_tool_integration_depth"] += 1
            blockers.append(
                finding(
                    severity="blocker",
                    kind="missing_tool_integration_depth",
                    result_name=result_name,
                    registry_entry=registry_entry,
                    detail="Registry-selected result is missing tool_integration_depth.",
                )
            )
        else:
            unresolved_tools = unresolved_used_tools(tool_manifest, tool_depth)
            if unresolved_tools:
                issue_kind_counts["used_tool_without_depth_detail"] += 1
                blockers.append(
                    finding(
                        severity="blocker",
                        kind="used_tool_without_depth_detail",
                        result_name=result_name,
                        registry_entry=registry_entry,
                        detail="Result marks tools as used but does not give them a concrete tool_integration_depth entry.",
                        extra={"tools": unresolved_tools},
                    )
                )

        blank_reason = blank_reason_tools(tool_manifest)
        if blank_reason:
            issue_kind_counts["blank_unused_reason"] += 1
            advisories.append(
                finding(
                    severity="advisory",
                    kind="blank_unused_reason",
                    result_name=result_name,
                    registry_entry=registry_entry,
                    detail="Manifest has tried=true, used=false tools with blank reasons.",
                    extra={"tools": blank_reason},
                )
            )

    summary = {
        "registry_row_count": len(rows),
        "registry_linked_result_count": len(registry_by_result),
        "registry_linked_lego_count": sum(len(entry["lego_ids"]) for entry in registry_by_result.values()),
        "blocker_count": len(blockers),
        "advisory_count": len(advisories),
        "blocker_result_count": len({item["result_json"] for item in blockers}),
        "advisory_result_count": len({item["result_json"] for item in advisories}),
        "issue_kind_counts": dict(sorted(issue_kind_counts.items())),
        "ok": len(blockers) == 0,
    }

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": summary,
        "blockers": blockers,
        "advisories": advisories,
    }

    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"blocker_count={summary['blocker_count']}")
    print(f"advisory_count={summary['advisory_count']}")
    print("LEGO TOOL REPORTING AUDIT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
