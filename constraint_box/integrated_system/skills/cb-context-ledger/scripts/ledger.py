#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SKILLS = Path(os.environ.get("CB_SKILLS_ROOT", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(SKILLS / "cb-management-plane" / "scripts"))
from plane import digest_obj, now, sha_text

KINDS = {
    "owner_statement",
    "object_card",
    "decision",
    "branch",
    "contradiction",
    "failure",
    "negative",
    "reoffer",
    "claim_ceiling",
    "lineage",
    "proposal",
}


def load(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def head(entries: list[dict]) -> str | None:
    return entries[-1]["entry_digest"] if entries else None


def append(path: Path, payload: dict) -> dict:
    if payload.get("kind") not in KINDS:
        return {"schema": "constraintbox.context-ledger.v1", "status": "REFUSE", "reason": "REFUSE_BAD_KIND"}
    if payload.get("delete") or payload.get("rewrite"):
        return {"schema": "constraintbox.context-ledger.v1", "status": "REFUSE", "reason": "REFUSE_REWRITE"}
    entries = load(path)
    prev = head(entries)
    if payload.get("kind") == "proposal" and prev and payload.get("head") != prev:
        return {"schema": "constraintbox.context-ledger.v1", "status": "HOLD", "reason": "HOLD_LEDGER_UNBOUND", "expected_head": prev}
    entry = {
        "schema": "constraintbox.context-ledger-entry.v1",
        "ts": now(),
        "kind": payload["kind"],
        "text": str(payload.get("text") or ""),
        "refs": payload.get("refs") or [],
        "prev": prev,
        "canon": payload.get("kind") in {"owner_statement", "object_card", "claim_ceiling"},
        "promotion_allowed": False,
    }
    entry["entry_digest"] = sha_text(json.dumps({k: v for k, v in entry.items()}, sort_keys=True))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return {
        "schema": "constraintbox.context-ledger.v1",
        "status": "APPENDED",
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
        entries = load(args.ledger)
        print(json.dumps({"head": head(entries), "count": len(entries)}, sort_keys=True))
        return 0
    receipt = append(args.ledger, json.loads(args.append or "{}"))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt.get("status") == "APPENDED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
