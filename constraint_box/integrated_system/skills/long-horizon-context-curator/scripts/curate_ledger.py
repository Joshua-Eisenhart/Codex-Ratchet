#!/usr/bin/env python3
"""Append-only decision ledger. Latest context is a proposal, not canon."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


KINDS = {
    "intent",
    "invariant",
    "rejected_alternative",
    "failure",
    "change_of_mind",
    "unresolved_contradiction",
    "proposal",
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_entries(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def head_digest(entries: list[dict]) -> str | None:
    if not entries:
        return None
    return entries[-1].get("entry_digest")


def append(path: Path, payload: dict) -> dict:
    entries = load_entries(path)
    kind = payload.get("kind")
    if kind not in KINDS:
        return {"schema": "constraintbox.decision-ledger.v1", "status": "REFUSE", "reason": "REFUSE_BAD_KIND"}
    if payload.get("rewrite_index") is not None:
        return {"schema": "constraintbox.decision-ledger.v1", "status": "REFUSE", "reason": "REFUSE_REWRITE"}
    head = head_digest(entries)
    if kind == "proposal":
        cited = payload.get("head")
        if head is not None and cited != head:
            return {
                "schema": "constraintbox.decision-ledger.v1",
                "status": "HOLD",
                "reason": "HOLD_LEDGER_UNBOUND",
                "expected_head": head,
            }
        if payload.get("treat_as_canon") is True:
            return {"schema": "constraintbox.decision-ledger.v1", "status": "REFUSE", "reason": "REFUSE_RECENCY_AS_CANON"}
    entry = {
        "schema": "constraintbox.decision-ledger-entry.v1",
        "ts": _now(),
        "kind": kind,
        "text": str(payload.get("text") or ""),
        "prev": head,
        "canon": False if kind == "proposal" else bool(payload.get("canon", kind in {"intent", "invariant"})),
        "promotion_allowed": False,
    }
    raw = json.dumps(entry, sort_keys=True)
    entry["entry_digest"] = _sha(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return {
        "schema": "constraintbox.decision-ledger.v1",
        "status": "APPENDED",
        "kind": kind,
        "entry_digest": entry["entry_digest"],
        "head": entry["entry_digest"],
        "count": len(entries) + 1,
        "canon": entry["canon"],
        "promotion_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--append", type=str, default=None)
    parser.add_argument("--head", action="store_true")
    args = parser.parse_args()
    if args.head:
        entries = load_entries(args.ledger)
        print(json.dumps({"head": head_digest(entries), "count": len(entries)}, sort_keys=True))
        return 0
    if not args.append:
        print(json.dumps({"status": "REFUSE", "reason": "REFUSE_NO_ENTRY"}))
        return 2
    receipt = append(args.ledger, json.loads(args.append))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt.get("status") == "APPENDED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
