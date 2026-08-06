#!/usr/bin/env python3
"""Run the one retained external SciPy replay-severance rehearsal."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _source_root() -> Path:
    return Path(__file__).resolve().parents[1] / "src"


def main() -> int:
    parser = argparse.ArgumentParser(prog="run_failure_rehearsal.py")
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(_source_root()))
    from constraintbox.failure_rehearsal import (  # noqa: PLC0415
        FailureRehearsalError,
        run_scipy_replay_severance_rehearsal,
    )
    from constraintbox.intake import canonical_json  # noqa: PLC0415

    try:
        receipt = run_scipy_replay_severance_rehearsal(run_root=args.run_root)
    except FailureRehearsalError as exc:
        print(f"failure rehearsal refused: {exc}", file=sys.stderr)
        return 2
    print(canonical_json(receipt).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
