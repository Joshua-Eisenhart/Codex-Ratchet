#!/usr/bin/env python3
"""Seal v1 preregistration only while all engine builder paths are absent."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
OUT = HERE / "preregistration_receipt.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    spec = json.loads((HERE / "spec.json").read_text(encoding="utf-8"))
    builders = {
        path: (HERE / path).exists() for path in spec["builder_paths"]
    }
    validation = subprocess.run(
        [sys.executable, "-B", str(HERE / "validate_preregistration.py")],
        cwd=HERE,
        text=True,
        capture_output=True,
        check=False,
    )
    if validation.returncode != 0 or any(builders.values()):
        print(validation.stdout, end="")
        return 2
    inputs = {
        relative: sha256(HERE / relative)
        for relative in spec["preregistration_inputs"]
    }
    receipt = {
        "schema": "codex_ratchet.tolerance_to_equivalence_v1.preregistration_receipt.v1",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "status": "SEALED_PREREGISTRATION_BUILDERS_ABSENT",
        "classification": "scratch_diagnostic",
        "inputs": inputs,
        "builder_paths": builders,
        "validation_stdout_sha256": hashlib.sha256(
            validation.stdout.encode()
        ).hexdigest(),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "official_launch_allowed": False,
        "llm_verdict_used": False,
        "claim_ceiling": "sealed semantic-forcing preregistration only; no engine builders, held-out run, pawl, or tooth",
    }
    OUT.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": receipt["status"], "receipt": str(OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
