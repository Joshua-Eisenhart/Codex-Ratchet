#!/usr/bin/env python3
"""Execute the generated SMT-LIB instances with a cvc5 binary."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "solver" / "cvc5_manifest.json")
    parser.add_argument("--cvc5", default="cvc5")
    parser.add_argument("--output", type=Path, default=ROOT / "solver" / "results" / "cvc5_anf_census.json")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    results = []
    for item in manifest["instances"]:
        completed = subprocess.run(
            [args.cvc5, "--lang", "smt2", str(ROOT / item["path"])],
            check=False,
            capture_output=True,
            text=True,
        )
        observed = completed.stdout.strip().splitlines()[0] if completed.stdout.strip() else "no-output"
        results.append(
            {
                "handle": item["handle"],
                "expected": item["expected"],
                "observed": observed,
                "returncode": completed.returncode,
                "passed": completed.returncode == 0 and observed == item["expected"],
            }
        )
    passed = all(item["passed"] for item in results)
    receipt = {
        "schema_version": "ratchet.cvc5-anf-census/0.1",
        "results": results,
        "all_pass": passed,
        "status": "PASS" if passed else "HOLD_CVC5_DISAGREEMENT_OR_RUNTIME_FAILURE",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
