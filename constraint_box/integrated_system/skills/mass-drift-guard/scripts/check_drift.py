#!/usr/bin/env python3
"""Refuse a loop that lost alignment or collapsed its antichain."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def check(context: dict | None, harvest: dict | None) -> dict:
    reasons = []
    if context is None:
        reasons.append("REFUSE_MISSING_CONTEXT_STRATEGY")
    else:
        if context.get("status") != "CONTEXT_SNAPSHOT_READY":
            reasons.append(f"REFUSE_CONTEXT:{context.get('status')}")
        if context.get("admission_disposition") == "rejected":
            reasons.append("REFUSE_CONTEXT_REJECTED")
        if context.get("reason") in {"HOLD_CORPUS_OVERLAP", "REFUSE_MERGED_CORPORA", "REFUSE_DRAFT_AS_LAW"}:
            reasons.append(f"REFUSE_CORPUS:{context.get('reason')}")
    if harvest is not None:
        if harvest.get("winner_selected") is True:
            reasons.append("REFUSE_WINNER_SELECTED")
        families = harvest.get("family_count")
        if isinstance(families, int) and families < 2:
            reasons.append("REFUSE_ANTIChain_COLLAPSED")
    if reasons:
        return {
            "schema": "constraintbox.mass-drift.v1",
            "status": "REFUSE",
            "reason": "REFUSE_MASS_DRIFT",
            "reasons": reasons,
            "promotion_allowed": False,
        }
    return {
        "schema": "constraintbox.mass-drift.v1",
        "status": "DRIFT_CLEAN",
        "reasons": [],
        "promotion_allowed": False,
    }


def _load(path: Path | None) -> dict | None:
    if path is None or not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", type=Path, default=None)
    parser.add_argument("--harvest", type=Path, default=None)
    args = parser.parse_args()
    receipt = check(_load(args.context), _load(args.harvest))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "DRIFT_CLEAN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
