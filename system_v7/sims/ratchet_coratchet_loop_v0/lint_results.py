#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"
required = ["classification", "promotion_allowed", "capstone_status", "TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH", "divergence_log"]
failures = []
for path in sorted(RESULTS.glob("ratchet_coratchet_loop_v0_*results.json")):
    row = json.loads(path.read_text())
    for key in required:
        if key not in row:
            failures.append(f"{path.name}: missing {key}")
    if row.get("classification") != "scratch_diagnostic" or row.get("promotion_allowed") is not False:
        failures.append(f"{path.name}: bad classification/promotion")
    if row.get("capstone_status") != "DRAFT_UNAUDITED":
        failures.append(f"{path.name}: bad capstone")
print(json.dumps({"lint_failures": failures, "lint_failure_count": len(failures)}, sort_keys=True))
raise SystemExit(1 if failures else 0)
