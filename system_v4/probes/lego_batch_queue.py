#!/usr/bin/env python3
"""
Executable middle-ladder queue built from machine controller surfaces.

Consumes:
  - lego_coupling_candidates.json
  - lego_stack_audit_results.json
  - controller_alignment_audit_results.json

Emits:
  - lego_batch_queue.json
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
COUPLING_PATH = RESULTS_DIR / "lego_coupling_candidates.json"
LEGO_AUDIT_PATH = RESULTS_DIR / "lego_stack_audit_results.json"
ALIGN_PATH = RESULTS_DIR / "controller_alignment_audit_results.json"
OUT_PATH = RESULTS_DIR / "lego_batch_queue.json"

SHALLOW_PRIORITY = {
    "cvc5": 1,
    "pyg": 2,
    "e3nn": 3,
    "toponetx": 4,
    "xgi": 5,
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_rows() -> list[dict]:
    coupling = read_json(COUPLING_PATH)
    lego = read_json(LEGO_AUDIT_PATH)
    align = read_json(ALIGN_PATH)

    needs_deeper = {
        row["id"]
        for row in lego.get("candidates", [])
        if row.get("needs_deeper_lego_work")
    }
    shallow = set(align.get("tool_stack_summary", {}).get("shallow_tools", []))

    rows = []
    for idx, row in enumerate(coupling.get("rows", []), start=1):
        pressure = [tool for tool in row.get("shallow_tool_pressure", []) if tool in shallow]
        blocked_by = []
        ready = True

        needs_more_lego = row["lego_family_id"] in needs_deeper
        has_existing_anchor = row["status"] == "existing_anchor"
        recommended_count = len(row.get("recommended_lego_probes", []))

        if needs_more_lego and not (has_existing_anchor and recommended_count >= 1):
            blocked_by.append("deeper_lego_work_needed")
            ready = False
        if row["status"] == "supporting_only":
            blocked_by.append("successor_only_supporting")
        if row["status"] in {"blocked_until_better_lego", "blocked_from_assembly"}:
            blocked_by.append(row["status"])
            ready = False

        if pressure:
            priority = min(SHALLOW_PRIORITY.get(tool, 99) for tool in pressure)
        elif row["status"] == "supporting_only":
            priority = 6
        elif row["status"] == "existing_anchor":
            priority = 7
        else:
            priority = 9

        target_stage = "coupling"
        if row.get("coexistence_rerun_needed"):
            target_stage = "coexistence"
        elif row.get("topology_rerun_needed"):
            target_stage = "topology"

        if row["status"] == "supporting_only":
            stop_rule = "Stop if successor remains supporting-only after schema/truth hardening."
        elif row["blocked_from_assembly"]:
            stop_rule = "Stop here; do not feed assembly until blocking lego condition is resolved."
        elif pressure:
            stop_rule = "Stop if shallow-tool pressure is not increased at the target stage."
        else:
            stop_rule = "Stop if no new pairwise/coexistence evidence is produced."

        rows.append({
            "task_id": f"lego-batch-{idx:03d}",
            "lego_or_pair": row["lego_family_id"],
            "target_stage": target_stage,
            "depends_on": [row["lego_probe"]] if row.get("lego_probe") else row.get("recommended_lego_probes", [])[:2],
            "priority": priority,
            "ready": ready,
            "blocked_by": blocked_by,
            "recommended_sim": row.get("coupling_probe") or row.get("existing_anchor"),
            "status": row["status"],
            "stop_rule": stop_rule,
            "tool_pressure": pressure,
            "blocked_from_assembly": row["blocked_from_assembly"],
        })

    rows.sort(key=lambda item: (item["priority"], item["ready"] is False, item["task_id"]))
    return rows


def main() -> int:
    rows = build_rows()
    report = {
        "name": "lego_batch_queue",
        "generated_at": datetime.now(UTC).isoformat(),
        "rows": rows,
        "summary": {
            "task_count": len(rows),
            "ready_count": sum(1 for row in rows if row["ready"]),
            "blocked_count": sum(1 for row in rows if not row["ready"]),
            "supporting_only_count": sum(1 for row in rows if row["status"] == "supporting_only"),
            "tool_pressure_task_count": sum(1 for row in rows if row["tool_pressure"]),
        },
    }
    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"task_count={report['summary']['task_count']}")
    print(f"ready_count={report['summary']['ready_count']}")
    print(f"blocked_count={report['summary']['blocked_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
