#!/usr/bin/env python3
"""Refuse resurrection of a demoted approach without new evidence."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def load_memory(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def remember(path: Path, failure: dict) -> dict:
    row = {
        "schema": "constraintbox.failure-memory.v1",
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "approach_id": str(failure.get("approach_id") or ""),
        "why": str(failure.get("why") or ""),
        "demotion_cause": str(failure.get("demotion_cause") or ""),
        "witness": str(failure.get("witness") or ""),
        "reentry": str(failure.get("reentry") or "new_evidence_digest"),
        "promotion_allowed": False,
    }
    if not row["approach_id"]:
        return {"status": "REFUSE", "reason": "REFUSE_EMPTY_APPROACH"}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
    return {"status": "REMEMBERED", "approach_id": row["approach_id"], "promotion_allowed": False}


def check(path: Path, proposal: dict) -> dict:
    approach = str(proposal.get("approach_id") or "")
    text = str(proposal.get("text") or "").lower()
    new_ev = proposal.get("new_evidence_digest")
    hits = []
    for row in load_memory(path):
        stored = str(row.get("approach_id") or "")
        why = str(row.get("why") or "").lower()
        tokens = [part for part in stored.replace("_", " ").replace("-", " ").split() if part not in {"a", "the"}]
        if stored and (
            stored == approach
            or stored.replace("_", "-") in text
            or stored in text
            or (tokens and all(part in text for part in tokens))
        ):
            hits.append(row)
        elif why and why in text:
            hits.append(row)
    if hits and not new_ev:
        return {
            "schema": "constraintbox.resurrection.v1",
            "status": "REFUSE",
            "reason": "REFUSE_RESURRECTION",
            "hits": [row.get("approach_id") for row in hits],
            "promotion_allowed": False,
        }
    return {
        "schema": "constraintbox.resurrection.v1",
        "status": "CLEAR",
        "hits": [row.get("approach_id") for row in hits],
        "promotion_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--memory", type=Path, required=True)
    parser.add_argument("--remember", type=str, default=None)
    parser.add_argument("--proposal", type=str, default=None)
    args = parser.parse_args()
    if args.remember:
        receipt = remember(args.memory, json.loads(args.remember))
    elif args.proposal:
        receipt = check(args.memory, json.loads(args.proposal))
    else:
        receipt = {"status": "REFUSE", "reason": "REFUSE_NO_OP"}
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt.get("status") in {"REMEMBERED", "CLEAR"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
