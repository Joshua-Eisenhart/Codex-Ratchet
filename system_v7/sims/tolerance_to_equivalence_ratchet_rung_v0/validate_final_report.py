#!/usr/bin/env python3
"""Independent final boundary validator for the bounded scratch tooth."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parent
ROOT = SIM_DIR.parents[2]
REPORT = SIM_DIR / "results" / "final_report.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    findings = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            findings.append(message)

    require(len(report.get("gates", {})) == 11 and all(report.get("gates", {}).values()), "G0-G10 are not all code-green")
    require(report.get("all_code_gates_pass") is True, "all_code_gates_pass not true")
    require(report.get("decision") == "COMMIT_ONE_BOUNDED_SCRATCH_TOOTH", "bounded tooth decision changed")
    require(report.get("ratchet_state_after") == "TOOTH_1_COMMITTED_SCRATCH", "scratch tooth state changed")
    require(report.get("classification") == "scratch_diagnostic", "classification changed")
    require(report.get("promotion_allowed") is False and report.get("formal_admission_allowed") is False, "admission fence opened")
    require(report.get("scientific_claim_proven") is False and report.get("release_eligible") is False and report.get("official_launch_allowed") is False, "launch/science ceiling opened")
    require(report.get("llm_verdict_used") is False, "LLM verdict entered final report")
    require(report.get("lev_boundary", {}).get("proof_backed_execution") is False, "unexpected ProofBundle claim")
    require(report.get("lev_boundary", {}).get("evaluator_advisory_red") is True, "Lev evaluator advisory red was erased")
    require(report.get("lev_boundary", {}).get("proof_bundle_written") is False, "Lev ProofBundle falsely claimed")
    for name, record in report.get("artifacts", {}).items():
        path = ROOT / record["path"]
        require(path.is_file() and sha256(path) == record["sha256"], f"{name} artifact hash mismatch")
    ok = not findings
    print(json.dumps({"schema": "codex_ratchet.tolerance_to_equivalence.final_validation.v1", "ok": ok, "findings": findings}, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
