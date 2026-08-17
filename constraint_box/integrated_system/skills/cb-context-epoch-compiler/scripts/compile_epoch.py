#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SKILLS = Path(os.environ.get("CB_SKILLS_ROOT", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(SKILLS / "cb-management-plane" / "scripts"))
from plane import digest_obj, now


def compile_epoch(parent: str | None, deltas: list[dict], genesis: bool = False) -> dict:
    if parent is None and not genesis:
        return {"schema": "constraintbox.context-epoch.v1", "status": "REFUSE", "reason": "REFUSE_ORPHAN_EPOCH"}
    epoch = {
        "schema": "constraintbox.context-epoch.v1",
        "status": "SEALED",
        "ts": now(),
        "parent": parent,
        "delta_digests": [digest_obj(item) for item in deltas],
        "promotion_allowed": False,
        "truth_disposition": None,
    }
    epoch["epoch_digest"] = digest_obj(epoch)
    return epoch


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", type=str, default=None)
    parser.add_argument("--deltas", type=str, default="[]")
    parser.add_argument("--genesis", action="store_true")
    args = parser.parse_args()
    receipt = compile_epoch(args.parent, json.loads(args.deltas), genesis=args.genesis)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt.get("status") == "SEALED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
