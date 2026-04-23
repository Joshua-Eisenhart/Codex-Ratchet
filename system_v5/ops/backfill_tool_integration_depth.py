#!/usr/bin/env python3
"""Backfill missing `tool_integration_depth` in canonical result JSONs.

For each canonical result missing the lowercase key, look at the source probe's
TOOL_INTEGRATION_DEPTH dict (class-level const) and inject that into the JSON.
If no source probe found: mark classification as classical_baseline with
reason 'orphan_no_source_2026-04-17' per OVERNIGHT.md §1.
"""
from __future__ import annotations
import ast
import glob
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
RESULT_DIRS = [
    REPO / "system_v4/probes/a2_state/sim_results",
    REPO / "system_v4/probes/sim_results",
    REPO / "system_v4/a2_state/sim_results",
]
PROBE_DIR = REPO / "system_v4/probes"


def extract_tool_integration_depth(probe_path: Path) -> dict | None:
    """Parse the probe's AST and extract the TOOL_INTEGRATION_DEPTH module-level const."""
    try:
        tree = ast.parse(probe_path.read_text())
    except Exception:
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "TOOL_INTEGRATION_DEPTH":
                    try:
                        return ast.literal_eval(node.value)
                    except Exception:
                        return None
    return None


def main() -> int:
    backfilled = 0
    downgraded = 0
    skipped = 0
    for rd in RESULT_DIRS:
        if not rd.exists():
            continue
        for result_path in sorted(rd.glob("*.json")):
            try:
                data = json.loads(result_path.read_text())
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            if data.get("classification") != "canonical":
                continue
            if "tool_integration_depth" in data:
                continue

            base = result_path.name.replace("_results.json", "")
            probe_path = PROBE_DIR / f"{base}.py"

            if probe_path.exists():
                depth = extract_tool_integration_depth(probe_path)
                if depth is not None:
                    data["tool_integration_depth"] = depth
                    result_path.write_text(json.dumps(data, indent=2))
                    backfilled += 1
                    continue
                # Probe exists but no TOOL_INTEGRATION_DEPTH declared — mark missing
                data["tool_integration_depth"] = {}
                data["_tier_a_note"] = "probe source has no TOOL_INTEGRATION_DEPTH symbol; empty dict injected for schema completeness, classification preserved pending review"
                result_path.write_text(json.dumps(data, indent=2))
                skipped += 1
            else:
                # Orphan canonical per OVERNIGHT.md §1 — downgrade
                data["classification"] = "classical_baseline"
                data["downgrade_reason"] = "orphan_no_source_2026-04-17"
                data["original_classification"] = "canonical"
                result_path.write_text(json.dumps(data, indent=2))
                downgraded += 1

    print(f"backfilled: {backfilled}")
    print(f"downgraded (orphan): {downgraded}")
    print(f"schema-completed (empty depth, needs review): {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
