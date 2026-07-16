#!/usr/bin/env python3
"""Load-bearing Z3 consistency check for the frozen MSS census counts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import z3


HERE = Path(__file__).resolve().parent
RESULTS_PATH = HERE / "results_v1.json"
OUTPUT_PATH = HERE / "z3_load_bearing_check_v1.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measured_values(result: dict[str, object]) -> dict[str, int]:
    counts = result["counts"]
    kills = result["kill_attribution"]
    association = result["associativity_split_among_minima"]
    enumeration = result["enumeration"]
    return {
        "total": int(enumeration["operation_tables"]),
        "candidate": int(counts["candidate_count_n01"]),
        "survivor": int(counts["survivor_count_n01_and_probe"]),
        "minimal": int(counts["minimal_count_quotient_only"]),
        "n01_rejected": int(kills["n01_rejected"]),
        "probe_rejected": int(kills["probe_rejected_after_n01"]),
        "quotient_killed": int(kills["quotient_killed_after_n01_and_probe"]),
        "associative": int(association["associative_raw_tables"]),
        "witnessed_nonassociative": int(association["witnessed_nonassociative_raw_tables"]),
    }


def solver_with_bindings(values: dict[str, int], erase_quotient_kills: bool) -> z3.Solver:
    total, candidate, survivor, minimal = z3.Ints("total candidate survivor minimal")
    n01_rejected, probe_rejected, quotient_killed = z3.Ints(
        "n01_rejected probe_rejected quotient_killed"
    )
    associative, witnessed_nonassociative = z3.Ints(
        "associative witnessed_nonassociative"
    )
    solver = z3.Solver()
    solver.add(total == values["total"])
    solver.add(candidate == values["candidate"])
    solver.add(survivor == values["survivor"])
    solver.add(minimal == values["minimal"])
    solver.add(n01_rejected == values["n01_rejected"])
    solver.add(probe_rejected == values["probe_rejected"])
    solver.add(associative == values["associative"])
    solver.add(witnessed_nonassociative == values["witnessed_nonassociative"])
    solver.add(quotient_killed == (0 if erase_quotient_kills else values["quotient_killed"]))

    # These are direct structural claims over values measured by census.py.
    solver.add(candidate + n01_rejected == total)
    solver.add(survivor + probe_rejected == candidate)
    solver.add(minimal + quotient_killed == survivor)
    solver.add(associative + witnessed_nonassociative == minimal)
    solver.add(n01_rejected + probe_rejected + quotient_killed + minimal == total)
    return solver


def main() -> None:
    result = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    values = measured_values(result)
    real_verdict = solver_with_bindings(values, erase_quotient_kills=False).check()
    erased_verdict = solver_with_bindings(values, erase_quotient_kills=True).check()
    all_pass = real_verdict == z3.sat and erased_verdict == z3.unsat
    check = {
        "schema": "mss_minimal_survivor_census_z3_check_v1",
        "sim_id": "mss_minimal_survivor_census_v0",
        "classification": "classical_baseline",
        "promotion_allowed": False,
        "input_result_path": "results_v1.json",
        "input_result_sha256": sha256(RESULTS_PATH),
        "z3_version": z3.get_version_string(),
        "polarity": "direct count-partition assertion: real SAT, erased-control UNSAT",
        "measured_values": values,
        "real_case": {
            "quotient_killed_binding": values["quotient_killed"],
            "verdict": str(real_verdict),
        },
        "erased_control": {
            "operation": "replace the measured quotient-killed contribution with zero",
            "quotient_killed_binding": 0,
            "verdict": str(erased_verdict),
        },
        "tool_manifest": {
            "z3": {
                "qualified_api": "z3.Solver.check",
                "integration_depth": "load_bearing",
                "reason": "all_pass requires the measured count partition to be SAT and the erased quotient-kill control to be UNSAT",
                "gates": ["all_pass"],
            }
        },
        "all_pass": all_pass,
        "claim_ceiling": "count-consistency only; no general MSS or subquotient claim",
        "blocked_consumers": ["subquotient_minimality", "unbounded_magma_claims", "ratchet_promotion"],
    }
    OUTPUT_PATH.write_text(json.dumps(check, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Z3 direct measured-count check: {real_verdict}")
    print(f"Z3 erased quotient-kill control: {erased_verdict}")
    print(f"Z3 all_pass: {all_pass}")
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
