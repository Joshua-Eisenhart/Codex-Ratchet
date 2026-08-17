#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


TOOLS = {"z3", "cvc5", "enumeration", "pytest", "seed-check"}
MODELS = {"llm", "gpt", "claude", "grok", "luna", "sonnet", "opus"}


def judge(receipt: dict) -> dict:
    verifiers = [str(item).lower() for item in receipt.get("verifiers") or []]
    if not verifiers:
        return {"schema": "constraintbox.rederivation.v1", "status": "HOLD", "reason": "HOLD_NOT_REPLAYED"}
    if any(any(model in item for model in MODELS) for item in verifiers) and not any(item in TOOLS for item in verifiers):
        return {"schema": "constraintbox.rederivation.v1", "status": "REFUSE", "reason": "REFUSE_LAUNDERED_CONSENSUS", "promotion_allowed": False}
    tool_hits = [item for item in verifiers if item in TOOLS]
    if len(set(tool_hits)) < 2:
        return {"schema": "constraintbox.rederivation.v1", "status": "HOLD", "reason": "HOLD_NOT_REPLAYED", "tools": tool_hits}
    return {"schema": "constraintbox.rederivation.v1", "status": "REPLAYED", "tools": sorted(set(tool_hits)), "promotion_allowed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    receipt = judge(json.loads(args.receipt.read_text(encoding="utf-8")))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "REPLAYED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
