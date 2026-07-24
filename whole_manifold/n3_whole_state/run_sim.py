#!/usr/bin/env python3
"""Run the bounded N=3 whole-state Ratchet campaign and write its receipt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from manifold_sim import run_campaign


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "results" / "receipt.json",
    )
    args = parser.parse_args()
    receipt = run_campaign()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "all_checks_pass": receipt["all_checks_pass"],
        "frontier_ids": receipt["typed_pareto"]["frontier_ids"],
        "runnable_ids": receipt["typed_pareto"]["runnable_ids"],
        "receipt": str(args.output.resolve()),
    }, indent=2))
    return 0 if receipt["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

