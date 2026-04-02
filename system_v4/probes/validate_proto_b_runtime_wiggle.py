#!/usr/bin/env python3
"""
validate_proto_b_runtime_wiggle.py
==================================

Mechanical validator for the exploratory Proto-B runtime wiggle probe.

This stays outside the old packet ladder. It only checks whether the
runtime-native candidate-family sweep is producing a stable, explicit
surface worth using for follow-on work.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
INPUT_PATH = SIM_RESULTS / "proto_b_runtime_wiggle.json"
OUTPUT_PATH = SIM_RESULTS / "proto_b_runtime_wiggle_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    probe = load_json(INPUT_PATH)
    sweep = probe["sweep"]
    summaries = probe["candidate_summaries"]
    rankings = probe["rankings"]

    normalized_work = summaries["carnot_transport_normalized_work"]
    closure_yield = summaries["carnot_closure_adjusted_yield"]
    cycle_area = summaries["carnot_cycle_area_ga0_neg"]

    gates = [
        gate(
            probe["schema"] == "SIM_EVIDENCE_v1"
            and probe["status"] == "exploratory"
            and sweep["n_runs"] == len(sweep["seeds"]) * len(sweep["engine_types"]) * len(sweep["axis0_levels"]) * len(sweep["torus_programs"])
            and "runtime-native metrics only" in probe["proto_b_guardrails"]
            and "inactive/dead candidates are reported, not hidden" in probe["proto_b_guardrails"],
            "PB1_proto_b_probe_surface_is_explicit_and_fail_closed",
            {
                "schema": probe["schema"],
                "status": probe["status"],
                "n_runs": sweep["n_runs"],
                "guardrails": probe["proto_b_guardrails"],
            },
        ),
        gate(
            normalized_work["active_fraction"] == 0.875
            and normalized_work["inactive_reasons"].get("zero_transport_cost") == 24
            and normalized_work["paired_gaps"]["torus_wave_minus_constant_mean"] < -50.0
            and normalized_work["paired_gaps"]["axis0_high_minus_low_mean"] < -10.0,
            "PB2_transport_normalized_work_shows_live_transport_cost_sensitivity",
            {
                "active_fraction": normalized_work["active_fraction"],
                "inactive_reasons": normalized_work["inactive_reasons"],
                "torus_gap": normalized_work["paired_gaps"]["torus_wave_minus_constant_mean"],
                "axis0_gap": normalized_work["paired_gaps"]["axis0_high_minus_low_mean"],
            },
        ),
        gate(
            closure_yield["active_fraction"] == 1.0
            and closure_yield["sign_flip_rate"] == 0.0
            and closure_yield["paired_gaps"]["torus_wave_minus_constant_mean"] > 0.2
            and abs(closure_yield["paired_gaps"]["axis0_high_minus_low_mean"]) < 0.02,
            "PB3_closure_adjusted_yield_stays_stable_while_torus_program_matters",
            {
                "active_fraction": closure_yield["active_fraction"],
                "sign_flip_rate": closure_yield["sign_flip_rate"],
                "torus_gap": closure_yield["paired_gaps"]["torus_wave_minus_constant_mean"],
                "axis0_gap": closure_yield["paired_gaps"]["axis0_high_minus_low_mean"],
            },
        ),
        gate(
            rankings["axis0_gap"][0]["candidate"] == "carnot_transport_normalized_work"
            and rankings["torus_gap"][0]["candidate"] == "carnot_transport_normalized_work"
            and rankings["torus_gap"][1]["candidate"] == "carnot_closure_adjusted_yield"
            and cycle_area["paired_gaps"]["torus_wave_minus_constant_mean"] > 0.1,
            "PB4_runtime_rankings_separate_cost_dominated_and_yield_dominated_candidates",
            {
                "axis0_top": rankings["axis0_gap"][:3],
                "torus_top": rankings["torus_gap"][:3],
                "cycle_area_torus_gap": cycle_area["paired_gaps"]["torus_wave_minus_constant_mean"],
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "proto_b_runtime_wiggle_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "gates": gates,
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("PROTO-B RUNTIME WIGGLE VALIDATION")
        print("=" * 72)
        for item in gates:
            status = "PASS" if item["pass"] else "FAIL"
            print(f"{status:4}  {item['name']}")
        print()
        print(f"passed_gates: {passed}/{len(gates)}")
        print(f"score: {payload['score']:.6f}")
        print(f"validation_results: {OUTPUT_PATH}")
    else:
        print(json.dumps(payload, indent=2))

    return 0 if passed == len(gates) else 1


if __name__ == "__main__":
    raise SystemExit(main())
