#!/usr/bin/env python3
"""Refuse a keep that maximises one number by exploding scope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def check(mutation: dict) -> dict:
    files = list(mutation.get("files_touched") or [])
    reasons = []
    if len(files) > 8:
        reasons.append("REFUSE_MASS_WRITE")
    if mutation.get("promotion_allowed") is True:
        reasons.append("REFUSE_PROMOTION")
    ceiling = str(mutation.get("claim_ceiling") or "")
    if ceiling and len(ceiling) < 20:
        reasons.append("REFUSE_CEILING_COLLAPSE")
    for wave in mutation.get("new_waves") or []:
        if not wave.get("has_tests"):
            reasons.append(f"REFUSE_UNTESTED_WAVE:{wave.get('name')}")
    if reasons:
        return {
            "schema": "constraintbox.paperclip-scope.v1",
            "status": "REFUSE",
            "reason": "REFUSE_PAPERCLIP",
            "reasons": reasons,
            "promotion_allowed": False,
        }
    return {
        "schema": "constraintbox.paperclip-scope.v1",
        "status": "SCOPE_CLEAN",
        "reasons": [],
        "promotion_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mutation", type=Path, required=True)
    args = parser.parse_args()
    receipt = check(json.loads(args.mutation.read_text(encoding="utf-8")))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "SCOPE_CLEAN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
