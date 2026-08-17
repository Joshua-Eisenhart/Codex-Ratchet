#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SKILLS = Path(os.environ.get("CB_SKILLS_ROOT", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(SKILLS / "cb-management-plane" / "scripts"))
from plane import now, sha_text

KINDS = {
    "failed_candidate",
    "killed_assumption",
    "counterexample",
    "parked_branch",
    "unresolved_discriminator",
}


def load(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def remember(path: Path, payload: dict) -> dict:
    kind = payload.get("kind")
    ident = str(payload.get("id") or "")
    if kind not in KINDS or not ident:
        return {"schema": "constraintbox.branch-failure.v1", "status": "REFUSE", "reason": "REFUSE_BAD_MEMORY"}
    row = {
        "schema": "constraintbox.branch-failure-entry.v1",
        "ts": now(),
        "kind": kind,
        "id": ident,
        "why": str(payload.get("why") or ""),
        "resurrection": payload.get("resurrection") or {"needs": "new_bridge_or_new_evidence"},
        "promotion_allowed": False,
    }
    row["entry_digest"] = sha_text(json.dumps(row, sort_keys=True))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
    return {"schema": "constraintbox.branch-failure.v1", "status": "REMEMBERED", "entry_digest": row["entry_digest"], "id": ident, "promotion_allowed": False}


def resurrect(path: Path, proposal: dict) -> dict:
    ident = str(proposal.get("id") or "")
    hits = [row for row in load(path) if row.get("id") == ident]
    if hits and not proposal.get("new_bridge") and not proposal.get("new_evidence"):
        return {
            "schema": "constraintbox.branch-failure.v1",
            "status": "REFUSE",
            "reason": "REFUSE_RESURRECTION",
            "hits": [row.get("id") for row in hits],
            "promotion_allowed": False,
        }
    return {"schema": "constraintbox.branch-failure.v1", "status": "CLEAR", "hits": [row.get("id") for row in hits], "promotion_allowed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--memory", type=Path, required=True)
    parser.add_argument("--remember", type=str, default=None)
    parser.add_argument("--resurrect", type=str, default=None)
    args = parser.parse_args()
    if args.remember:
        receipt = remember(args.memory, json.loads(args.remember))
    elif args.resurrect:
        receipt = resurrect(args.memory, json.loads(args.resurrect))
    else:
        receipt = {"status": "REFUSE", "reason": "REFUSE_NO_OP"}
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt.get("status") in {"REMEMBERED", "CLEAR"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
