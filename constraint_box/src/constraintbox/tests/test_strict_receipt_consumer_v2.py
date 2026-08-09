#!/usr/bin/env python3
"""Executable regression tests for the audited CB strict consumer."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent.parent
# Try to find the consumer script; if running from the repo, look in parent
CONSUMER = HERE / "strict_receipt_consumer_v2.py"
if not CONSUMER.exists():
    # Try as a module from the audit patch
    CONSUMER = HERE / "source" / "strict_receipt_consumer_v2.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(root: Path, receipt: Path, output: Path, expected: str | None = None) -> tuple[int, dict]:
    command = [
        sys.executable,
        str(CONSUMER),
        "--artifact-root",
        str(root),
        "--receipt",
        str(receipt),
        "--expected-receipt-sha256",
        expected or digest(receipt),
        "--output",
        str(output),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    result = json.loads(output.read_text()) if output.exists() else {}
    return completed.returncode, result


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        scope = temp / "scope"
        (scope / "results").mkdir(parents=True)
        artifact = scope / "results" / "engine.json"
        artifact.write_text('{"state":"sealed"}\n')
        control = temp / "control"
        control.mkdir()
        receipt = control / "RUN_RECEIPT.json"
        receipt.write_text(json.dumps({
            "output_hashes": {"results/engine.json": digest(artifact)},
            "all_pass": True,
        }))

        rc, result = invoke(scope, receipt, control / "pass.json")
        require(rc == 0 and result["integrity_pass"], "sealed explicit manifest must pass")
        require(result["semantic_verdict"] == "not_evaluated", "integrity must not become a semantic verdict")
        require(result["producer_verdicts_refused_as_evidence_count"] == 1, "producer verdict must be recorded as refused")

        artifact.write_text('{"state":"mutated"}\n')
        rc, result = invoke(scope, receipt, control / "mutation.json")
        require(rc == 1 and result["recomputed_mismatch_count"] == 1, "mutated declared artifact must fail")
        artifact.write_text('{"state":"sealed"}\n')

        trusted_receipt_hash = digest(receipt)
        receipt.write_text(receipt.read_text() + " ")
        rc, result = invoke(scope, receipt, control / "receipt_tamper.json", trusted_receipt_hash)
        require(rc == 1 and not result["receipt_hash_match"], "receipt tampering must fail its trust anchor")
        receipt.write_text(json.dumps({"output_hashes": {"results/engine.json": digest(artifact)}}))

        escaped_root = temp / "escaped_scope"
        escaped_root.mkdir()
        outside = temp / "outside.json"
        outside.write_text('{"outside":true}\n')
        escaped_receipt = control / "ESCAPED_RECEIPT.json"
        escaped_receipt.write_text(json.dumps({"artifacts": {"../outside.json": digest(outside)}}))
        rc, result = invoke(escaped_root, escaped_receipt, control / "escaped.json")
        require(rc == 1 and result["declared_path_escape_count"] == 1, "path escape must fail")

        rc, _ = invoke(scope, receipt, scope / "forbidden_output.json")
        require(rc == 2, "consumer output inside artifact scope must be rejected")

        empty_receipt = control / "EMPTY_RECEIPT.json"
        empty_receipt.write_text(json.dumps({"all_pass": True}))
        rc, result = invoke(scope, empty_receipt, control / "empty.json")
        require(rc == 1 and "no declarations" in " ".join(result["defects"]), "no-manifest receipt must fail")

    print("PASS strict_receipt_consumer_v2 regression suite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
