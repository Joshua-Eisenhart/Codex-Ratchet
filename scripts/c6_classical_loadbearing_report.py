#!/usr/bin/env python3
"""Classify C6 classical/load-bearing violations without editing sims."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import adaptive_controller
import lint_sim_contract


ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "system_v5/ops/c6_loadbearing_report.json"


def load_result_for(path: Path) -> dict[str, Any]:
    result_path = adaptive_controller.find_result_file(path.stem)
    if not result_path:
        return {}
    try:
        data = json.loads(result_path.read_text())
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def bucket_for(path: Path, tool: str, result: dict[str, Any]) -> str:
    text = json.dumps(result).lower() if result else ""
    if not result:
        return "inconclusive_needs_owner"
    if tool.lower() in text and any(token in text for token in ("load_bearing", "load-bearing", "used", "tool")):
        return "genuinely_load_bearing_so_promote_to_canonical_candidate"
    if tool.lower() in text:
        return "inconclusive_needs_owner"
    return "decorative_load_bearing_demote_tool"


def main() -> int:
    violations_by_sim: dict[str, list[str]] = defaultdict(list)
    for path in sorted(adaptive_controller.PROBES.glob("sim_*.py")):
        if not path.is_file() or " 2" in path.name:
            continue
        for violation in lint_sim_contract.lint_sim(path):
            if violation["rule"] == "C6_classical_has_load_bearing":
                violations_by_sim[str(path.relative_to(ROOT))].append(str(violation["detail"]))

    rows = []
    counts = defaultdict(int)
    for rel, tools in sorted(violations_by_sim.items()):
        path = ROOT / rel
        result = load_result_for(path)
        result_path = adaptive_controller.find_result_file(path.stem)
        for tool in tools:
            bucket = bucket_for(path, tool, result)
            counts[bucket] += 1
            rows.append(
                {
                    "sim": rel,
                    "tool": tool,
                    "bucket": bucket,
                    "result_path": str(result_path.relative_to(ROOT)) if result_path else None,
                    "evidence": "result_json_mentions_tool" if result and tool.lower() in json.dumps(result).lower() else "no_result_tool_evidence",
                }
            )

    report = {
        "schema": "c6_classical_loadbearing_report_v1",
        "mode": "audit_no_source_edits",
        "row_count": len(rows),
        "bucket_counts": dict(counts),
        "rows": rows,
    }
    OUT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"row_count": len(rows), "bucket_counts": dict(counts), "path": str(OUT_PATH.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
