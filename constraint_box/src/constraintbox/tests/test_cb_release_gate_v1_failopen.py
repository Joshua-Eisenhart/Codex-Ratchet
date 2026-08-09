#!/usr/bin/env python3
"""Reproduce the supplied v1 release-gate cleanliness bypass, isolated."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent.parent
PATCH = HERE / "cbpatch"
GATE = PATCH / "cb_release_gate.py"
CONSUMER = PATCH / "strict_receipt_consumer.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        run_root = temp / "run"
        run_root.mkdir()
        declared: dict[str, str] = {}
        # 2,000 declared artifacts plus the receipt and one stray file makes
        # the gate's 0.999 threshold pass even though the scope is unclean.
        for index in range(2000):
            artifact = run_root / f"artifact_{index:04d}.txt"
            artifact.write_text(f"sealed-{index}\n")
            declared[artifact.name] = digest(artifact)
        receipt = run_root / "RUN_RECEIPT.json"
        receipt.write_text(json.dumps({"artifacts": declared}))
        (run_root / "stray_replay.txt").write_text("not declared\n")

        verifier = temp / "always_pass_verifier.py"
        verifier.write_text(
            "import argparse, json\n"
            "from pathlib import Path\n"
            "p=argparse.ArgumentParser(); p.add_argument('--out'); a=p.parse_args()\n"
            "Path(a.out).write_text(json.dumps({'passed': True, 'checks_passed': 1, 'checks_total': 1}))\n"
        )
        output = temp / "release.json"
        command = [
            sys.executable,
            str(GATE),
            "--run-root",
            str(run_root),
            "--package-root",
            str(temp),
            "--consumer",
            str(CONSUMER),
            "--verifier",
            f"{sys.executable} {verifier} --out {{out}}",
            "--output",
            str(output),
        ]
        completed = subprocess.run(command, capture_output=True, text=True)
        result = json.loads(output.read_text())
        if completed.returncode != 0 or result["release_allowed"] is not True:
            raise AssertionError(f"expected v1 bypass, got {completed.returncode}: {result}")
        coverage = result["detail"]["declaration_coverage"]["coverage"]
        if not (coverage >= 0.999 and result["detail"]["declaration_coverage"]["undeclared_sample"]):
            raise AssertionError(f"expected undeclared-but-green coverage: {result}")
    print("REPRODUCED v1 release-gate fail-open: undeclared artifact accepted at coverage", coverage)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
