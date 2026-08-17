#!/usr/bin/env python3
"""Refuse actions that silently overrule frozen invariants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CONSTITUTION = Path(__file__).resolve().parents[1] / "constitution.json"

TRIPS = {
    "I-no-rebase": ("rebase",),
    "I-code-decides": ("llm vote", "majority of models", "consensus of llms"),
    "I-no-promotion": (),
    "I-light-not-heavy": ("import heavy as light", "fep as light geometry"),
    "I-solver-obs-not-quotient": ("solver-chosen obs are bound", "obs__* are the quotient"),
    "I-two-corpora": ("merge the corpora", "one mixed mmm"),
    "I-antichain": ("pick a winner", "collapse the antichain"),
    "I-ledger-over-recency": ("latest prompt is canon", "newest output is law"),
}


def check(action: dict, constitution: dict | None = None) -> dict:
    constitution = constitution or json.loads(CONSTITUTION.read_text(encoding="utf-8"))
    text = str(action.get("text") or "").lower()
    hits = []
    if action.get("promotion_allowed") is True and not action.get("amendment_receipt"):
        hits.append("I-no-promotion")
    if action.get("amendment") and not action.get("amendment_receipt"):
        hits.append("amendment_without_receipt")
    for invariant_id, needles in TRIPS.items():
        if any(needle in text for needle in needles):
            hits.append(invariant_id)
    if hits:
        return {
            "schema": "constraintbox.constitution-check.v1",
            "status": "REFUSE",
            "reason": "REFUSE_CONSTITUTION",
            "hits": hits,
            "promotion_allowed": False,
        }
    return {
        "schema": "constraintbox.constitution-check.v1",
        "status": "HOLDS",
        "hits": [],
        "promotion_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", type=str, required=True)
    args = parser.parse_args()
    receipt = check(json.loads(args.action))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "HOLDS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
