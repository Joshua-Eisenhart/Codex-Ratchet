#!/usr/bin/env python3
"""Local gate for pcg_noncommutation_topology_v0."""

from __future__ import annotations

import json
import os
import sys

SIM_ID = "pcg_noncommutation_topology_v0"
HERE = os.path.dirname(os.path.abspath(__file__))
RESULT_PATH = os.path.join(HERE, "results", f"{SIM_ID}_results.json")
AGREEMENT_PATH = os.path.join(HERE, "results", f"{SIM_ID}_agreement_results.json")

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "classical"
TOOL_MANIFEST = {
    "python_json": {"reason": "supportive local result-gate read/write"},
    "pathlib": {"reason": "supportive local path handling through os.path"},
}
TOOL_INTEGRATION_DEPTH = {"python_json": "supportive", "pathlib": "supportive"}


def main() -> int:
    failures = []
    with open(RESULT_PATH, encoding="utf-8") as handle:
        result = json.load(handle)
    if result.get("classification") != classification:
        failures.append("classification is not scratch_diagnostic")
    if result.get("promotion_allowed") is not False or result.get("formal_admission_allowed") is not False:
        failures.append("claim ceilings are not fenced")
    if result.get("reads_peer_result") is not False:
        failures.append("reads_peer_result is not false")
    flip = result.get("decisive_flip_control", {})
    if flip.get("fully_commuting_h1") != 0:
        failures.append("fully commuting control has nonzero H1")
    if flip.get("noncommuting_cycle_h1") == 0:
        failures.append("noncommuting cycle has H1=0")
    if flip.get("target_restored_h1") != 0:
        failures.append("target-restored control has nonzero H1")
    if flip.get("pass") is not bool(1):
        failures.append("flip-control pass flag is not true")
    smt = result.get("smt_structural_checks", {})
    if smt.get("pass") is not bool(1):
        failures.append("SMT structural checks did not pass")
    for solver_name in ("z3", "cvc5"):
        row = smt.get(solver_name, {})
        for key in (
            "relation_h1_equals_not_target_when_cycle_and_guard_fixed",
            "noncommuting_cycle_hole",
            "fully_commuting_no_hole",
            "target_restored_no_hole",
        ):
            if row.get(key) != "unsat":
                failures.append(f"{solver_name}:{key} expected unsat got {row.get(key)}")
    if result.get("all_pass") is not bool(1) or result.get("build_status") != "PASS":
        failures.append("result did not report PASS")

    report = {
        "schema": "codex_ratchet.engine_agreement_result.v1",
        "sim_id": SIM_ID,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "all_pass": len(failures) == 0,
        "build_status": "PASS" if len(failures) == 0 else "BUILD FAILED",
        "checked_result": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_results.json",
        "failures": failures,
        "decisive_flip_control": flip,
        "smt_structural_checks": {
            "z3": smt.get("z3", {}),
            "cvc5": smt.get("cvc5", {}),
        },
    }
    os.makedirs(os.path.dirname(AGREEMENT_PATH), exist_ok=bool(1))
    with open(AGREEMENT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=bool(1))
        handle.write("\n")
    print(json.dumps(report, indent=2, sort_keys=bool(1)))
    if failures:
        print("BUILD FAILED", file=sys.stderr)
        return 1
    print("BUILD PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
