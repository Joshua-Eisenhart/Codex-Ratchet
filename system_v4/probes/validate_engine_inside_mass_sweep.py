#!/usr/bin/env python3
"""
validate_engine_inside_mass_sweep.py
===================================

Mechanical validator for the runtime-native engine-inside mass sweep.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROBE_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = ROOT / "a2_state" / "sim_results" / "engine_inside_mass_sweep_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    probe = load_json(PROBE_RESULTS / "engine_inside_mass_sweep.json")
    overall = probe["overall"]
    tops = probe["tops"]

    by_key = {(row["program"], row["engine_type"]): row for row in overall}
    default_1 = by_key[("default", 1)]
    default_2 = by_key[("default", 2)]
    wave_1 = by_key[("inner_outer_wave", 1)]
    wave_2 = by_key[("inner_outer_wave", 2)]

    op_transport_top = tops["operator_by_transport_alpha"][:4]
    terrain_trace_top = tops["terrain_by_abs_dtrace"][:4]

    gates = [
        gate(
            probe["programs"] == ["default", "inner_outer_wave"]
            and probe["engine_types"] == [1, 2]
            and len(probe["seeds"]) == 24
            and len(overall) == 4,
            "EM1_engine_inside_mass_sweep_surface_is_complete_and_runtime_native",
            {
                "programs": probe["programs"],
                "engine_types": probe["engine_types"],
                "n_seeds": len(probe["seeds"]),
                "overall_rows": len(overall),
            },
        ),
        gate(
            default_1["transport_alpha"] == 0.0
            and default_2["transport_alpha"] == 0.0
            and default_1["transport_triggered"] == 0.0
            and default_2["transport_triggered"] == 0.0
            and wave_1["transport_alpha"] > 0.09
            and wave_2["transport_alpha"] > 0.09
            and wave_1["transport_triggered"] == 1.0
            and wave_2["transport_triggered"] == 1.0,
            "EM2_wave_program_activates_transport_while_default_stays_transport_free",
            {
                "default_type1": {
                    "transport_alpha": default_1["transport_alpha"],
                    "transport_triggered": default_1["transport_triggered"],
                },
                "default_type2": {
                    "transport_alpha": default_2["transport_alpha"],
                    "transport_triggered": default_2["transport_triggered"],
                },
                "wave_type1": {
                    "transport_alpha": wave_1["transport_alpha"],
                    "transport_triggered": wave_1["transport_triggered"],
                },
                "wave_type2": {
                    "transport_alpha": wave_2["transport_alpha"],
                    "transport_triggered": wave_2["transport_triggered"],
                },
            },
        ),
        gate(
            wave_1["abs_dphase"] > default_1["abs_dphase"]
            and wave_2["abs_dphase"] > default_2["abs_dphase"]
            and wave_1["abs_dtrace"] > default_1["abs_dtrace"]
            and wave_2["abs_dtrace"] > default_2["abs_dtrace"]
            and wave_1["abs_dchi"] > default_1["abs_dchi"]
            and wave_2["abs_dchi"] > default_2["abs_dchi"]
            and wave_1["axis0_effective_gain"] < default_1["axis0_effective_gain"]
            and wave_2["axis0_effective_gain"] < default_2["axis0_effective_gain"],
            "EM3_wave_program_trades_axis0_effective_gain_for_phase_trace_and_chirality_motion",
            {
                "type1_gaps": {
                    "abs_dphase_gap": wave_1["abs_dphase"] - default_1["abs_dphase"],
                    "abs_dtrace_gap": wave_1["abs_dtrace"] - default_1["abs_dtrace"],
                    "abs_dchi_gap": wave_1["abs_dchi"] - default_1["abs_dchi"],
                    "axis0_effective_gain_gap": wave_1["axis0_effective_gain"] - default_1["axis0_effective_gain"],
                },
                "type2_gaps": {
                    "abs_dphase_gap": wave_2["abs_dphase"] - default_2["abs_dphase"],
                    "abs_dtrace_gap": wave_2["abs_dtrace"] - default_2["abs_dtrace"],
                    "abs_dchi_gap": wave_2["abs_dchi"] - default_2["abs_dchi"],
                    "axis0_effective_gain_gap": wave_2["axis0_effective_gain"] - default_2["axis0_effective_gain"],
                },
            },
        ),
        gate(
            len(op_transport_top) == 4
            and all(row["program"] == "inner_outer_wave" for row in op_transport_top)
            and {row["operator"] for row in op_transport_top} == {"Fe", "Ti"}
            and len(terrain_trace_top) == 4
            and all(row["program"] == "inner_outer_wave" for row in terrain_trace_top)
            and terrain_trace_top[0]["abs_dtrace"] > 0.4,
            "EM4_transport_and_trace_extremes_live_inside_wave_specific_operator_terrain_pockets",
            {
                "operator_by_transport_alpha_top4": op_transport_top,
                "terrain_by_abs_dtrace_top4": terrain_trace_top,
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "engine_inside_mass_sweep_validation",
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
        print("ENGINE INSIDE MASS SWEEP VALIDATION")
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
