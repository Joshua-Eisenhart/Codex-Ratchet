#!/usr/bin/env python3
"""
validate_proto_b_runtime_wiggle.py
==================================

Mechanical validator for the runtime-native Proto-B wiggle probe.

This validator does not promote any candidate family into doctrine.
It only checks that the exploratory runtime-native surface is explicit,
fail-closed, and exposes stable differential signals worth further study.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROBE_RESULTS = ROOT.parent / "a2_state" / "sim_results"
OUTPUT_PATH = ROOT / "a2_state" / "sim_results" / "proto_b_runtime_wiggle_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    probe = load_json(PROBE_RESULTS / "proto_b_runtime_wiggle.json")
    summaries = probe["candidate_summaries"]
    rankings = probe["rankings"]
    sweep = probe["sweep"]

    transport_norm = summaries["carnot_transport_normalized_work"]
    hybrid_transport = summaries["hybrid_transport_actuation"]
    closure_yield = summaries["carnot_closure_adjusted_yield"]
    ceiling = summaries["szilard_ceiling_actuation"]
    ceiling_by_condition = ceiling["by_condition"]

    gates = [
        gate(
            probe["status"] == "exploratory"
            and "candidate-family evidence only" in probe["proto_b_guardrails"]
            and "runtime-native metrics only" in probe["proto_b_guardrails"]
            and sweep["n_runs"] == 192
            and sweep["engine_types"] == [1, 2]
            and sweep["axis0_levels"] == [0.1, 0.9]
            and sweep["torus_programs"] == ["constant_clifford", "inner_outer_wave"],
            "PB1_proto_b_runtime_surface_is_explicit_and_exploratory",
            {
                "status": probe["status"],
                "proto_b_guardrails": probe["proto_b_guardrails"],
                "sweep": sweep,
            },
        ),
        gate(
            transport_norm["family"] == "carnot_style"
            and transport_norm["active_fraction"] == 1.0
            and transport_norm["inactive_reasons"] == {}
            and transport_norm["overall_mean_signed"] > 1.0
            and transport_norm["paired_gaps"]["axis0_high_minus_low_mean"] < -0.1
            and transport_norm["paired_gaps"]["torus_wave_minus_constant_mean"] < -1.0
            and rankings["torus_gap"][0]["candidate"] == "carnot_transport_normalized_work"
            and rankings["torus_gap"][0]["value"] < -1.0,
            "PB2_transport_normalized_work_is_nondegenerate_and_still_owns_torus_gap",
            {
                "transport_normalized_work": transport_norm,
                "top_rankings": {
                    "axis0_gap": rankings["axis0_gap"][0],
                    "torus_gap": rankings["torus_gap"][0],
                    "type_gap": rankings["type_gap"][0],
                },
            },
        ),
        gate(
            hybrid_transport["family"] == "runtime_hybrid"
            and hybrid_transport["active_fraction"] == 1.0
            and hybrid_transport["sign_flip_rate"] < 0.5
            and hybrid_transport["paired_gaps"]["axis0_high_minus_low_mean"] > 1.0
            and hybrid_transport["paired_gaps"]["torus_wave_minus_constant_mean"] > 0.05
            and hybrid_transport["paired_gaps"]["type2_minus_type1_mean"] > 0.05
            and rankings["axis0_gap"][0]["candidate"] == "hybrid_transport_actuation"
            and rankings["type_gap"][0]["candidate"] == "hybrid_transport_actuation",
            "PB3_hybrid_transport_actuation_bridges_axis0_and_type_structure",
            {
                "hybrid_transport_actuation": hybrid_transport,
                "top_rankings": {
                    "axis0_gap": rankings["axis0_gap"][:3],
                    "type_gap": rankings["type_gap"][:3],
                },
            },
        ),
        gate(
            closure_yield["family"] == "carnot_style"
            and closure_yield["active_fraction"] == 1.0
            and closure_yield["sign_flip_rate"] == 0.0
            and closure_yield["overall_mean_signed"] > 1.0
            and abs(closure_yield["paired_gaps"]["axis0_high_minus_low_mean"]) < 0.01
            and closure_yield["paired_gaps"]["torus_wave_minus_constant_mean"] > 0.2
            and rankings["torus_gap"][0]["candidate"] == "carnot_transport_normalized_work"
            and rankings["torus_gap"][1]["candidate"] == "carnot_closure_adjusted_yield"
            and rankings["torus_gap"][1]["value"] > 0.2,
            "PB3_closure_adjusted_yield_is_stable_and_second_to_transport_on_torus_gap",
            {
                "closure_adjusted_yield": closure_yield,
                "torus_gap_top_rankings": rankings["torus_gap"][:3],
            },
        ),
        gate(
            ceiling["family"] == "szilard_style"
            and ceiling["active_fraction"] == 1.0
            and ceiling["sign_flip_rate"] == 0.5
            and ceiling["paired_gaps"]["axis0_high_minus_low_mean"] > 0.45
            and ceiling["paired_gaps"]["torus_wave_minus_constant_mean"] > 0.04
            and all(
                row["mean_signed"] < -0.25
                for row in ceiling_by_condition
                if row["axis0_level"] == 0.1
            )
            and all(
                row["mean_signed"] > 0.12
                for row in ceiling_by_condition
                if row["axis0_level"] == 0.9
            )
            and max(row["std_signed"] for row in ceiling_by_condition) < 0.07
            and rankings["axis0_gap"][1]["candidate"] == "szilard_ceiling_actuation",
            "PB5_szilard_ceiling_actuation_remains_the_stable_secondary_axis0_surface",
            {
                "szilard_ceiling_actuation": ceiling,
                "axis0_gap_top_rankings": rankings["axis0_gap"][:3],
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

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("PROTO-B RUNTIME WIGGLE VALIDATION")
        print("=" * 72)
        for item in gates:
            status = "PASS" if item["pass"] else "FAIL"
            print(f"{status:<5} {item['name']}")
        print()
        print(f"passed_gates: {passed}/{len(gates)}")
        print(f"score: {payload['score']:.6f}")
        print(f"validation_results: {OUTPUT_PATH}")
    else:
        print(json.dumps(payload, indent=2))

    return 0 if passed == len(gates) else 1


if __name__ == "__main__":
    raise SystemExit(main())
