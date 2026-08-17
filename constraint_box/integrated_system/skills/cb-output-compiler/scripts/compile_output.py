#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def compile_output(execution: dict, extras: dict | None = None) -> dict:
    extras = extras or {}
    missing = []
    if not execution.get("schema"):
        missing.append("execution_schema")
    if execution.get("route_truth") == "FULL" and execution.get("model_free"):
        missing.append("fake_full")
    if extras.get("hide_failures"):
        return {"schema": "constraintbox.output-surface.v1", "status": "REFUSE", "reason": "REFUSE_CLEAN_PROSE", "promotion_allowed": False}
    surface = {
        "schema": "constraintbox.output-surface.v1",
        "status": "COMPILED",
        "decision": execution.get("state") or "UNKNOWN",
        "route_truth": execution.get("route_truth") or "NOT_FULL",
        "contradictions": extras.get("contradictions") or [],
        "failures": extras.get("failures") or execution.get("errors") or [],
        "minority_branches": extras.get("minority_branches") or [],
        "claim_ceiling": extras.get("claim_ceiling") or execution.get("claim_ceiling") or "no promotion",
        "next_action": extras.get("next_action") or "do not promote",
        "missing_evidence": missing,
        "promotion_allowed": False,
    }
    return surface


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execution", type=str, required=True)
    args = parser.parse_args()
    receipt = compile_output(json.loads(args.execution))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "COMPILED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
