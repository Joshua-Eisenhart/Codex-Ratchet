#!/usr/bin/env python3
"""
validate_no_chirality_search.py
===============================

Mechanical validator for the geometry-tier no-chirality probe surface.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "no_chirality_search_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    probe = load_json(SIM_RESULTS / "neg_no_chirality_results.json")
    history = probe["history_summary"]
    chiral = history["chiral"]
    flat = history["flat"]

    gates = [
        gate(
            probe["evidence_ledger"][0]["status"] == "KILL"
            and probe["chirality_matters"]
            and probe["d_chiral"] > probe["d_flat"]
            and probe["d_flat"] > 0.05,
            "N1_no_chirality_kill_is_real_but_not_total",
            {
                "d_chiral": probe["d_chiral"],
                "d_flat": probe["d_flat"],
                "chirality_matters": probe["chirality_matters"],
                "token_status": probe["evidence_ledger"][0]["status"],
            },
        ),
        gate(
            history["final_residual_ratio"] > 0.5
            and history["final_residual_ratio"] < 0.8
            and flat["min_trace_gap"] > 0.2
            and flat["mean_trace_gap"] > 0.5
            and flat["min_bloch_gap"] > 0.4,
            "N2_no_chirality_residual_is_explicitly_nontrivial",
            {
                "final_residual_ratio": history["final_residual_ratio"],
                "flat_history": flat,
            },
        ),
        gate(
            chiral["mean_trace_gap"] > flat["mean_trace_gap"]
            and chiral["mean_bloch_gap"] > flat["mean_bloch_gap"]
            and chiral["max_trace_gap"] > 0.8
            and flat["max_trace_gap"] < 0.85,
            "N3_chiral_run_keeps_stronger_sheet_split_than_flattened_run",
            {
                "chiral_history": chiral,
                "flat_history": flat,
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "no_chirality_search_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "gates": gates,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("NO-CHIRALITY SEARCH VALIDATION")
        print("=" * 72)
        for item in gates:
            status = "PASS" if item["pass"] else "FAIL"
            print(f"{status:>4}  {item['name']}")
        print(f"\npassed_gates: {passed}/{len(gates)}")
        print(f"score: {payload['score']:.6f}")
        print(f"validation_results: {OUTPUT_PATH}")
    else:
        print(json.dumps(payload, indent=2))

    return 0 if passed == len(gates) else 1


if __name__ == "__main__":
    raise SystemExit(main())
