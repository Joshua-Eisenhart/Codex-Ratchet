#!/usr/bin/env python3
"""Validate v5 primitive lego result receipts."""

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
    if data.get("classification") != "lego":
        errors.append("classification is not lego")
    if data.get("promotion_allowed") is not False:
        errors.append("promotion_allowed must be false")
    if not data.get("claim_ceiling"):
        errors.append("claim_ceiling missing")
    for key in ("observable", "predicate", "positive", "graveyard_companions", "boundary"):
        if not data.get(key):
            errors.append(f"{key} missing")
    if False in pass_values(data.get("positive", {})):
        errors.append("positive check failed")
    if False in pass_values(data.get("graveyard_companions", {})):
        errors.append("graveyard check failed")
    if False in pass_values(data.get("boundary", {})):
        errors.append("boundary check failed")
    if data.get("blockers"):
        errors.append("blockers present")
    return {"path": str(path), "pass": not errors, "errors": errors}


def main() -> int:
    paths = [pathlib.Path(arg) for arg in sys.argv[1:]] or sorted(RESULTS.glob("*_results.json"))
    rows = [validate(path) for path in paths]
    all_pass = bool(rows) and all(row["pass"] for row in rows)
    print(json.dumps({"all_pass": all_pass, "results": rows}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
