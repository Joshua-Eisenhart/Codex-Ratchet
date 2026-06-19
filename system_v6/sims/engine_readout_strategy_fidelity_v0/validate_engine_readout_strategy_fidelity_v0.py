#!/usr/bin/env python3
"""Packet-local validator for engine_readout_strategy_fidelity_v0."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "engine_readout_strategy_fidelity_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_PATH = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    result_path = Path(sys.argv[1]) if len(sys.argv) > 1 else RESULT_PATH
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    errors: list[str] = []

    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "bad schema")
    require(errors, payload.get("classification") == "scratch_diagnostic", "classification drift")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    require(errors, len(payload.get("strategy_rows", [])) == 16, "expected 16 strategy rows")
    require(errors, payload.get("periodicity_findings") == [], "periodicity findings present")
    require(errors, payload.get("values", {}).get("periodicity_violation_count") == 0, "periodicity violation count nonzero")
    require(errors, payload.get("values", {}).get("state_count_word") == 8, "word state count must be 8")
    require(errors, payload.get("values", {}).get("state_count_double_720") == 16, "double state count must be 16")
    require(
        errors,
        payload.get("values", {}).get("double_720_separates_more_than_360") is False,
        "double traversal unexpectedly separates more strategies than one 360 cycle",
    )
    controls = payload.get("controls", {})
    require(errors, controls.get("shuffled_stage_word_breaks_periodicity_table") is True, "shuffled control did not fire")
    require(errors, controls.get("strategy_blind_trace_constant") is True, "trace control not constant")
    require(errors, controls.get("permuted_seat_assignment_breaks_alternating_paired_split") is True, "permuted seat control did not fire")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))

    proofs = payload.get("crossover_proofs", {})
    for key in ("z3", "cvc5", "julia_z3"):
        proof = proofs.get(key, {})
        require(errors, proof.get("ran") is True, f"{key} did not run")
        require(errors, proof.get("load_bearing") is True, f"{key} not load-bearing")
        require(errors, proof.get("verdict") == "unsat", f"{key} expected unsat")
        require(errors, proof.get("control_verdict") == "sat", f"{key} erased control expected sat")

    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    print(json.dumps({"ok": True, "result_json": str(result_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
