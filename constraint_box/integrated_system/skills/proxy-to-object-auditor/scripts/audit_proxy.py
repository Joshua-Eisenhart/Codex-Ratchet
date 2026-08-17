#!/usr/bin/env python3
"""Name object vs proxy, then refuse a known Goodhart intervention."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SKILLS = Path(os.environ.get("CB_SKILLS_ROOT", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(SKILLS / "goodhart-proxy-guard"))
from scripts.check_proxy import check as check_proxy  # noqa: E402


def audit(card: dict, before: dict | None, after: dict | None) -> dict:
    missing = [key for key in ("object", "proxy", "bad_intervention") if not card.get(key)]
    if missing:
        return {"schema": "constraintbox.proxy-to-object.v1", "status": "HOLD", "reason": "HOLD_CARD_INCOMPLETE", "missing": missing}
    numeric = {"status": "SKIPPED"}
    if before is not None and after is not None:
        numeric = check_proxy(before, after)
        if numeric.get("status") == "REFUSE":
            return {
                "schema": "constraintbox.proxy-to-object.v1",
                "status": "REFUSE",
                "reason": "REFUSE_PROXY",
                "object": card["object"],
                "proxy": card["proxy"],
                "numeric": numeric,
                "promotion_allowed": False,
            }
    return {
        "schema": "constraintbox.proxy-to-object.v1",
        "status": "NAMED",
        "object": card["object"],
        "proxy": card["proxy"],
        "bad_intervention": card["bad_intervention"],
        "numeric": numeric,
        "promotion_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--card", type=Path, required=True)
    parser.add_argument("--before", type=Path, default=None)
    parser.add_argument("--after", type=Path, default=None)
    args = parser.parse_args()
    card = json.loads(args.card.read_text(encoding="utf-8"))
    before = json.loads(args.before.read_text(encoding="utf-8")) if args.before else None
    after = json.loads(args.after.read_text(encoding="utf-8")) if args.after else None
    receipt = audit(card, before, after)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] in {"NAMED", "SKIPPED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
