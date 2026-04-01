#!/usr/bin/env python3
"""
validate_axis0_stack_packet.py
==============================

Mechanical validator for the full Axis 0 packet ladder.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "axis0_stack_packet_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    run_packet = load_json(SIM_RESULTS / "axis0_stack_packet_run_results.json")
    formal_geometry = load_json(SIM_RESULTS / "formal_geometry_packet_validation.json")
    root_emergence = load_json(SIM_RESULTS / "root_emergence_packet_validation.json")
    carrier_selection = load_json(SIM_RESULTS / "carrier_selection_packet_validation.json")
    pre_entropy = load_json(SIM_RESULTS / "pre_entropy_packet_validation.json")
    matched_marginal = load_json(SIM_RESULTS / "matched_marginal_packet_validation.json")
    entropy_readout = load_json(SIM_RESULTS / "entropy_readout_packet_validation.json")

    packet_map = {
        "formal_geometry": formal_geometry,
        "root_emergence": root_emergence,
        "carrier_selection": carrier_selection,
        "pre_entropy": pre_entropy,
        "matched_marginal": matched_marginal,
        "entropy_readout": entropy_readout,
    }

    gates = [
        gate(
            run_packet["all_ok"],
            "S1_all_packet_runners_execute_cleanly",
            {
                "all_ok": run_packet["all_ok"],
                "steps": [{k: step[k] for k in ("label", "ok", "returncode")} for step in run_packet["steps"]],
            },
        ),
        gate(
            all(packet["passed_gates"] == packet["total_gates"] for packet in packet_map.values()),
            "S2_all_component_packets_are_closed",
            {
                key: {
                    "passed_gates": packet["passed_gates"],
                    "total_gates": packet["total_gates"],
                    "score": packet["score"],
                }
                for key, packet in packet_map.items()
            },
        ),
        gate(
            formal_geometry["score"] == 1.0
            and root_emergence["score"] == 1.0
            and carrier_selection["score"] == 1.0,
            "S3_lower_ladder_is_coherent",
            {
                "formal_geometry_score": formal_geometry["score"],
                "root_emergence_score": root_emergence["score"],
                "carrier_selection_score": carrier_selection["score"],
            },
        ),
        gate(
            pre_entropy["score"] == 1.0
            and matched_marginal["score"] == 1.0
            and entropy_readout["score"] == 1.0,
            "S4_upper_ladder_is_coherent",
            {
                "pre_entropy_score": pre_entropy["score"],
                "matched_marginal_score": matched_marginal["score"],
                "entropy_readout_score": entropy_readout["score"],
            },
        ),
        gate(
            root_emergence["score"] == 1.0
            and pre_entropy["score"] == 1.0
            and entropy_readout["score"] == 1.0,
            "S5_axis0_ladder_is_mechanically_traversable",
            {
                "root_emergence_score": root_emergence["score"],
                "pre_entropy_score": pre_entropy["score"],
                "entropy_readout_score": entropy_readout["score"],
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "axis0_stack_packet_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "gates": gates,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("AXIS0 STACK PACKET VALIDATION")
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
