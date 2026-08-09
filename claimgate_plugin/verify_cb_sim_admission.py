#!/usr/bin/env python3
"""Registry-selected ClaimGate checker for bounded CB simulation evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: verify_cb_sim_admission.py <claim.json>", file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))
    try:
        from constraintbox.sim_admission import SimAdmissionError, verify_claim

        result = verify_claim(Path(args[0]))
    except (OSError, SimAdmissionError, ValueError) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
