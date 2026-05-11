#!/usr/bin/env python3
"""Emit a focused report for runner taxonomy unknowns."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sim_runner_taxonomy_audit


ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "system_v5/ops/runner_taxonomy_unknowns.json"


def load_taxonomy() -> dict[str, Any]:
    sim_runner_taxonomy_audit.main()
    path = ROOT / "system_v4/probes/a2_state/sim_results/sim_runner_taxonomy_audit_results.json"
    return json.loads(path.read_text())


def main() -> int:
    data = load_taxonomy()
    rows = [row for row in data.get("rows", []) if row.get("runner_class") == "unknown"]
    report = {
        "schema": "runner_taxonomy_unknowns_v1",
        "unknown_count": len(rows),
        "rows": rows,
        "next_action": "classify each row by adding source classification or runner token evidence; do not delete unknowns to pass strict audit",
    }
    OUT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"unknown_count": len(rows), "path": str(OUT_PATH.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
