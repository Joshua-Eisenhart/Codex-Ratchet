#!/usr/bin/env python3
"""Find result receipts where a used tool has no integration-depth role."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "system_v4" / "probes" / "a2_state" / "sim_results"
ADMISSIONS_DIR = ROOT / "system_v5" / "ops" / "wizard_admissions"
OUT_PATH = ROOT / "system_v5" / "ops" / "tooling" / "stale_tool_depth_scan.json"


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def tool_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("tool_manifest") or payload.get("TOOL_MANIFEST")
    return value if isinstance(value, dict) else {}


def tool_depth(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("tool_integration_depth") or payload.get("TOOL_INTEGRATION_DEPTH")
    return value if isinstance(value, dict) else {}


def scan() -> list[dict[str, Any]]:
    admission_result_paths = active_admission_result_paths()
    rows: list[dict[str, Any]] = []
    for path in sorted(RESULTS_DIR.glob("*_results.json")):
        payload = load_json(path)
        if payload is None:
            continue
        manifest = tool_manifest(payload)
        depth = tool_depth(payload)
        missing_depth_tools = []
        for tool, info in sorted(manifest.items()):
            if isinstance(info, dict) and info.get("used") is True and depth.get(tool) is None:
                missing_depth_tools.append(tool)
        if missing_depth_tools:
            rel_path = str(path.relative_to(ROOT))
            active_admission_result = rel_path in admission_result_paths
            rows.append(
                {
                    "path": rel_path,
                    "name": payload.get("name"),
                    "classification": payload.get("classification"),
                    "missing_depth_tools": missing_depth_tools,
                    "active_admission_result": active_admission_result,
                    "stale_alias_or_unadmitted_result": not active_admission_result,
                    "claim_ceiling": "stale/weak tool-depth receipt audit only; no demotion, promotion, or rerun by itself",
                    "recommended_action": (
                        "rerun or source-repair the exact sim before reusing this receipt as tool-integration evidence"
                        if active_admission_result
                        else "treat as historical alias/unadmitted result unless a current admission links to this exact path"
                    ),
                }
            )
    return rows


def active_admission_result_paths() -> set[str]:
    paths: set[str] = set()
    for path in sorted(ADMISSIONS_DIR.glob("*.json")):
        payload = load_json(path)
        if payload is None:
            continue
        candidates = []
        if payload.get("expected_result_path"):
            candidates.append(payload["expected_result_path"])
        for key in ("receipt_paths", "artifacts"):
            value = payload.get(key)
            if isinstance(value, list):
                candidates.extend(item for item in value if isinstance(item, str))
        for candidate in candidates:
            candidate_path = Path(candidate)
            if not candidate_path.is_absolute():
                candidate_path = ROOT / candidate_path
            try:
                rel_path = str(candidate_path.resolve().relative_to(ROOT))
            except Exception:
                continue
            if rel_path.endswith("_results.json"):
                paths.add(rel_path)
    return paths


def main() -> int:
    rows = scan()
    active_rows = [row for row in rows if row["active_admission_result"]]
    payload = {
        "schema": "stale_tool_depth_scan.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "tooling_audit_only",
        "claim_ceiling": "detects used-tool depth gaps in result receipts only; does not classify, demote, admit, or promote receipts",
        "summary": {
            "result_dir": str(RESULTS_DIR.relative_to(ROOT)),
            "stale_tool_depth_result_count": len(rows),
            "active_admission_stale_tool_depth_result_count": len(active_rows),
            "alias_or_unadmitted_stale_tool_depth_result_count": len(rows) - len(active_rows),
            "tools": sorted({tool for row in rows for tool in row["missing_depth_tools"]}),
        },
        "rows": rows,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    print(f"wrote {OUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
