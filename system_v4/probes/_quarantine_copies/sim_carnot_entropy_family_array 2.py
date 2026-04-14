#!/usr/bin/env python3
"""
Carnot Entropy Family Array
===========================
Compare several Carnot rows under several entropy/readout families so the lab
can see where interpretation depends on the math, not just the geometry.
"""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Readout-family comparison over exact and stochastic Carnot rows. "
    "It compares performance, bath-entropy proxies, closure proxies, and "
    "return-mismatch proxies on the same family."
)

LEGO_IDS = [
    "stochastic_thermodynamics",
    "carnot_cycle",
]

PRIMARY_LEGO_IDS = [
    "stochastic_thermodynamics",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
T_HOT = 2.0
T_COLD = 1.0


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text())


def engine_bath_entropy_proxy(q_hot: float, q_cold: float) -> float:
    return float((-q_hot / T_HOT) + (-q_cold / T_COLD))


def refrigerator_bath_entropy_proxy(q_hot_released: float, q_cold_absorbed: float) -> float:
    return float((-q_hot_released / T_HOT) + (-q_cold_absorbed / T_COLD))


def main() -> None:
    exact = load("qit_carnot_two_bath_cycle_results.json")
    stochastic = load("stoch_harmonic_carnot_finite_time_results.json")
    forward_asym = load("carnot_asymmetric_isotherm_sweep_results.json")
    reverse_asym = load("carnot_reverse_asymmetric_sweep_results.json")
    topology = load("carnot_topology_array_results.json")

    exact_forward = exact["forward_cycle"]["summary"]
    exact_reverse = exact["reverse_cycle"]["summary"]
    stochastic_qs_f = stochastic["cycles"]["forward_quasistatic"]
    stochastic_qs_r = stochastic["cycles"]["reverse_quasistatic"]
    best_forward_asym = min(forward_asym["rows"], key=lambda row: row["efficiency_distance_to_carnot"])
    best_reverse_asym = min(reverse_asym["rows"], key=lambda row: row["cop_distance_to_carnot"])
    best_engine_topology = topology["summary"]["topologies"]["quartic"]["best_forward"]
    best_refrigerator_topology = topology["summary"]["topologies"]["soft_double_well"]["best_reverse"]
    best_refrigerator_topology_q_hot_released = -(
        best_refrigerator_topology["reverse_work_input"] + best_refrigerator_topology["reverse_q_cold_absorbed"]
    )

    rows = [
        {
            "row_id": "exact_qit_forward",
            "mode": "forward_engine",
            "carrier": "qubit_working_substance",
            "readout_family": "performance+closure+bath_entropy",
            "performance_distance": abs(exact_forward["efficiency"] - exact_forward["carnot_bound"]),
            "bath_entropy_proxy": engine_bath_entropy_proxy(exact_forward["q_hot"], exact_forward["q_cold"]),
            "closure_proxy": 0.0,
            "return_proxy": 0.0,
        },
        {
            "row_id": "stochastic_harmonic_forward_quasistatic",
            "mode": "forward_engine",
            "carrier": "harmonic_working_substance",
            "readout_family": "performance+closure+bath_entropy",
            "performance_distance": abs(stochastic_qs_f["efficiency"] - stochastic_qs_f["carnot_bound"]),
            "bath_entropy_proxy": engine_bath_entropy_proxy(stochastic_qs_f["q_hot"], stochastic_qs_f["q_cold"]),
            "closure_proxy": abs(stochastic_qs_f["cycle_delta_u"]),
            "return_proxy": abs(stochastic_qs_f["final_variance"] - stochastic_qs_f["initial_variance"]),
        },
        {
            "row_id": "best_forward_asymmetric",
            "mode": "forward_engine",
            "carrier": "harmonic_working_substance",
            "readout_family": "performance+closure+bath_entropy",
            "performance_distance": best_forward_asym["efficiency_distance_to_carnot"],
            "bath_entropy_proxy": engine_bath_entropy_proxy(best_forward_asym["q_hot"], best_forward_asym["q_cold"]),
            "closure_proxy": abs(best_forward_asym["cycle_delta_u"]),
            "return_proxy": best_forward_asym["variance_mismatch_abs"],
        },
        {
            "row_id": "quartic_topology_best_engine",
            "mode": "forward_engine",
            "carrier": "quartic_single_well",
            "readout_family": "performance+closure+bath_entropy",
            "performance_distance": abs(best_engine_topology["forward_efficiency"] - best_engine_topology["forward_carnot_bound"]),
            "bath_entropy_proxy": engine_bath_entropy_proxy(best_engine_topology["forward_q_hot"], 0.0),
            "closure_proxy": abs(best_engine_topology["forward_cycle_delta_u"]),
            "return_proxy": best_engine_topology["forward_return_proxy"],
        },
        {
            "row_id": "exact_qit_reverse",
            "mode": "reverse_refrigerator",
            "carrier": "qubit_working_substance",
            "readout_family": "performance+closure+bath_entropy",
            "performance_distance": abs(exact_reverse["cop"] - exact_reverse["cop_carnot"]),
            "bath_entropy_proxy": refrigerator_bath_entropy_proxy(0.0, exact_reverse["q_cold_absorbed"]),
            "closure_proxy": 0.0,
            "return_proxy": 0.0,
        },
        {
            "row_id": "stochastic_harmonic_reverse_quasistatic",
            "mode": "reverse_refrigerator",
            "carrier": "harmonic_working_substance",
            "readout_family": "performance+closure+bath_entropy",
            "performance_distance": abs(stochastic_qs_r["cop"] - stochastic_qs_r["cop_carnot"]),
            "bath_entropy_proxy": refrigerator_bath_entropy_proxy(stochastic_qs_r["q_hot_released"], stochastic_qs_r["q_cold_absorbed"]),
            "closure_proxy": abs(stochastic_qs_r["cycle_delta_u"]),
            "return_proxy": abs(stochastic_qs_r["final_variance"] - stochastic_qs_r["initial_variance"]),
        },
        {
            "row_id": "best_reverse_asymmetric",
            "mode": "reverse_refrigerator",
            "carrier": "harmonic_working_substance",
            "readout_family": "performance+closure+bath_entropy",
            "performance_distance": best_reverse_asym["cop_distance_to_carnot"],
            "bath_entropy_proxy": refrigerator_bath_entropy_proxy(best_reverse_asym["q_hot_released"], best_reverse_asym["q_cold_absorbed"]),
            "closure_proxy": abs(best_reverse_asym["cycle_delta_u"]),
            "return_proxy": best_reverse_asym["variance_mismatch_abs"],
        },
        {
            "row_id": "soft_double_well_topology_best_refrigerator",
            "mode": "reverse_refrigerator",
            "carrier": "soft_double_well",
            "readout_family": "performance+closure+bath_entropy",
            "performance_distance": abs(best_refrigerator_topology["reverse_cop"] - best_refrigerator_topology["reverse_cop_carnot"]),
            "bath_entropy_proxy": refrigerator_bath_entropy_proxy(best_refrigerator_topology_q_hot_released, best_refrigerator_topology["reverse_q_cold_absorbed"]),
            "closure_proxy": abs(best_refrigerator_topology["reverse_cycle_delta_u"]),
            "return_proxy": best_refrigerator_topology["reverse_return_proxy"],
        },
    ]

    forward_rows = [row for row in rows if row["mode"] == "forward_engine"]
    reverse_rows = [row for row in rows if row["mode"] == "reverse_refrigerator"]
    exact_rows = [row for row in rows if row["carrier"] == "qubit_working_substance"]
    open_rows = [row for row in rows if row["carrier"] != "qubit_working_substance"]

    positive = {
        "exact_rows_minimize_performance_distance": {
            "best_exact_distance": min(row["performance_distance"] for row in exact_rows),
            "best_open_distance": min(row["performance_distance"] for row in open_rows),
            "pass": min(row["performance_distance"] for row in exact_rows) < min(row["performance_distance"] for row in open_rows),
        },
        "some_open_rows_approach_the_exact_rows_closely_in_performance": {
            "best_open_distance": min(row["performance_distance"] for row in open_rows),
            "pass": min(row["performance_distance"] for row in open_rows) < 0.1,
        },
        "readout_families_separate_performance_from_closure": {
            "best_open_performance_distance": min(row["performance_distance"] for row in open_rows),
            "best_open_closure_proxy": min(row["closure_proxy"] for row in open_rows),
            "pass": any(
                row["performance_distance"] < 0.05 and row["closure_proxy"] > 0.01
                for row in open_rows
            ),
        },
    }

    negative = {
        "best_engine_performance_row_is_not_the_best_closure_row": {
            "best_performance_row": min(forward_rows, key=lambda row: row["performance_distance"])["row_id"],
            "best_closure_row": min(forward_rows, key=lambda row: row["closure_proxy"])["row_id"],
            "pass": min(forward_rows, key=lambda row: row["performance_distance"])["row_id"]
            != min(forward_rows, key=lambda row: row["closure_proxy"])["row_id"],
        },
        "best_refrigerator_performance_row_is_not_the_best_closure_row": {
            "best_performance_row": min(reverse_rows, key=lambda row: row["performance_distance"])["row_id"],
            "best_closure_row": min(reverse_rows, key=lambda row: row["closure_proxy"])["row_id"],
            "pass": min(reverse_rows, key=lambda row: row["performance_distance"])["row_id"]
            != min(reverse_rows, key=lambda row: row["closure_proxy"])["row_id"],
        },
    }

    boundary = {
        "all_rows_are_finite": {
            "pass": all(
                isinstance(value, (int, float))
                for row in rows
                for value in row.values()
                if not isinstance(value, str)
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    out = {
        "name": "carnot_entropy_family_array",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "row_count": len(rows),
            "best_open_performance_distance": min(row["performance_distance"] for row in open_rows),
            "best_open_closure_proxy": min(row["closure_proxy"] for row in open_rows),
            "scope_note": (
                "Carnot readout-family comparison across exact and stochastic rows. "
                "Use this to see where performance, bath-entropy, and closure proxies agree or split."
            ),
        },
        "rows": rows,
    }

    out_path = RESULT_DIR / "carnot_entropy_family_array_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
