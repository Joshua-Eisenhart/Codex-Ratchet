#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def verify(definition: dict, execution: dict) -> dict:
    declared = {str(child["id"]) for child in definition.get("children") or [] if isinstance(child, dict)}
    rows = execution.get("children") or []
    observed = {str(row.get("child_id")) for row in rows if isinstance(row, dict)}
    missing = sorted(declared - observed)
    extra = sorted(observed - declared)
    parent_only = [row.get("child_id") for row in rows if isinstance(row, dict) and row.get("parent_reported") and not row.get("receipt_path")]
    fake_full = execution.get("route_truth") == "FULL" and (missing or parent_only or execution.get("model_free"))
    errors = []
    if missing:
        errors.append("missing_children")
    if extra:
        errors.append("extra_children")
    if parent_only:
        errors.append("parent_reported_only")
    if fake_full:
        errors.append("fake_full")
    if execution.get("mixed_run"):
        errors.append("mixed_run")
    label = "NOT_FULL" if errors or execution.get("model_free") else "FULL"
    return {
        "schema": "constraintbox.route-truth.v1",
        "status": "REFUSE" if fake_full else "CHECKED",
        "route_truth": label,
        "errors": errors,
        "missing": missing,
        "promotion_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", type=str, required=True)
    parser.add_argument("--execution", type=str, required=True)
    args = parser.parse_args()
    receipt = verify(json.loads(args.wave), json.loads(args.execution))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "CHECKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
