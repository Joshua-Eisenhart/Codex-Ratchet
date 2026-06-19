#!/usr/bin/env python3
"""Packet-local validator for manifold_information_throughput_v0."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SIM_ID = "manifold_information_throughput_v0"
ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = PACKET / "results" / f"{SIM_ID}_envelope_results.json"


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def run_shape_validator() -> dict[str, Any]:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "validate_three_engine_sim_result.py"),
        str(RESULT),
        "--require-source-backed",
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    stdout = completed.stdout.strip()
    parsed = None
    if stdout:
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = None
    return {
        "command": command,
        "returncode": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout": stdout,
        "stdout_json": parsed,
        "stderr": completed.stderr.strip(),
    }


def main() -> int:
    errors: list[str] = []
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    text = json.dumps(payload).lower()
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "wrong schema_version")
    require(errors, payload.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    forbidden_result_tokens = ["audit_" + "verdict.md", "fix" + "ture"]
    for token in forbidden_result_tokens:
        require(errors, token not in text, "forbidden output wording appears")
    require(errors, payload["throughput_ledger"]["stage_word_throughput"]["word_total_destroyed_nats"] > 0, "stage word must destroy positive information on pinned ensemble")
    require(errors, payload["controls"]["unitary_rows_lossless"]["pass"] is True, "unitary lossless control failed")
    require(errors, payload["controls"]["finite_quotient_smt_conservation"]["pass"] is True, "SMT conservation control failed")
    require(errors, payload["controls"]["wrong_base_control"]["detected"] is True, "wrong-base control did not fire")
    require(errors, payload["divergence"]["max_divergence"] < 1.0e-9, "Julia/Python S4 divergence too large")
    for engine_name in ["julia", "jax"]:
        engine = payload["engines"][engine_name]
        require(errors, engine["reads_peer_result"] is False, f"{engine_name} reads_peer_result must be false")
        require(errors, bool(engine["aligned_packages_load_bearing"]), f"{engine_name} aligned load-bearing packages required")
    shape = run_shape_validator()
    require(errors, shape["ok"], "validate_three_engine_sim_result.py --require-source-backed failed")
    report = {"ok": not errors, "errors": errors, "shape_validator": shape, "result_json": str(RESULT)}
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
