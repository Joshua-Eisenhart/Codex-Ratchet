#!/usr/bin/env python3
"""Validate formal-scout result receipts."""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def pass_values(section: dict[str, Any]) -> list[bool]:
    values = []
    for row in section.values():
        if isinstance(row, dict) and "pass" in row:
            values.append(bool(row["pass"]))
    return values


def validate(path: pathlib.Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    if data.get("classification") != "formal_scout":
        errors.append("classification is not formal_scout")
    if data.get("promotion_allowed") is not False:
        errors.append("promotion_allowed is not false")
    if not data.get("claim_ceiling"):
        errors.append("claim_ceiling missing")
    if "canonical" in str(data.get("claim_ceiling", "")).lower() and "does not admit" not in str(data.get("claim_ceiling", "")).lower():
        errors.append("claim_ceiling may overclaim")
    positives = data.get("positive")
    graveyards = data.get("graveyard_companions")
    if not isinstance(positives, dict) or not positives:
        errors.append("positive section missing")
    if not isinstance(graveyards, dict) or not graveyards:
        errors.append("graveyard_companions section missing")
    boundary = data.get("boundary")
    if not isinstance(boundary, dict) or not boundary:
        errors.append("boundary section missing")
    if not data.get("why_not_v4_probes"):
        errors.append("why_not_v4_probes missing")
    nearby = data.get("nearby_variants")
    if not isinstance(nearby, dict) or not nearby.get("total"):
        errors.append("nearby_variants summary missing")
    elif nearby.get("passed") != nearby.get("total"):
        errors.append("nearby_variants did not all pass")
    if isinstance(positives, dict) and False in pass_values(positives):
        errors.append("one or more positive checks failed")
    if isinstance(graveyards, dict) and False in pass_values(graveyards):
        errors.append("one or more graveyard checks failed")
    if isinstance(boundary, dict) and False in pass_values(boundary):
        errors.append("one or more boundary checks failed")
    if "rosetta_to_sim_contract" in data:
        errors.append("legacy rosetta_to_sim_contract key present")
    if data.get("blockers"):
        errors.append("blockers present")
    return {"path": str(path), "pass": not errors, "errors": errors}


def main() -> int:
    paths = [pathlib.Path(arg) for arg in sys.argv[1:]] or sorted(RESULTS.glob("*_results.json"))
    rows = [validate(path) for path in paths]
    print(json.dumps({"all_pass": all(row["pass"] for row in rows), "results": rows}, indent=2, sort_keys=True))
    return 0 if all(row["pass"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
