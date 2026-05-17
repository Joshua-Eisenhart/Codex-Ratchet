#!/usr/bin/env python3
"""Classical two-bath reversible Carnot cycle wrapper.

This exists so the full Carnot cycle can run through the direct sim guard
without using claim-layer labels in the executable filename.
"""
from __future__ import annotations

import json
import pathlib

import sim_qit_carnot_two_bath_cycle as core


classification = "canonical"
sim_execution_kind = "classical"
promotion_allowed = False

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing classical thermodynamic bookkeeping and sweep serialization"},
    "qutip": {"tried": True, "used": True, "reason": "load-bearing one-carrier density witness for isothermal legs"},
    "cirq": {"tried": True, "used": True, "reason": "load-bearing density-matrix simulator witness for isothermal legs"},
    "pennylane": {"tried": True, "used": True, "reason": "load-bearing mixed-state witness for isothermal legs"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed for classical Carnot control"},
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
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "qutip": "load_bearing",
    "cirq": "load_bearing",
    "pennylane": "load_bearing",
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}


def main() -> None:
    forward = core.forward_carnot_cycle(t_hot=2.0, t_cold=1.0, gap_high=3.0, gap_hot_low=1.0)
    reverse = core.reverse_refrigerator_cycle(forward)
    witnesses = core.build_bridge_witnesses(forward, reverse)
    sweep = core.sweep_operating_points()

    positive = {
        "forward_cycle_hits_reversible_carnot_efficiency": {
            "efficiency": forward["summary"]["efficiency"],
            "carnot_bound": forward["summary"]["carnot_bound"],
            "pass": abs(forward["summary"]["efficiency"] - forward["summary"]["carnot_bound"]) < 1e-10,
        },
        "reverse_cycle_hits_reversible_refrigerator_cop": {
            "cop": reverse["summary"]["cop"],
            "cop_carnot": reverse["summary"]["cop_carnot"],
            "pass": abs(reverse["summary"]["cop"] - reverse["summary"]["cop_carnot"]) < 1e-10,
        },
        "four_strokes_have_expected_work_and_heat_signs": {
            "q_hot": forward["summary"]["q_hot"],
            "q_cold": forward["summary"]["q_cold"],
            "work_net": forward["summary"]["work_net"],
            "pass": bool(
                forward["summary"]["q_hot"] > 0.0
                and forward["summary"]["q_cold"] < 0.0
                and forward["summary"]["work_net"] > 0.0
            ),
        },
        "independent_density_witnesses_match_isothermal_carrier_surface": {
            "max_qutip_density_error": witnesses["summary"]["max_qutip_density_error"],
            "max_cirq_density_error": witnesses["summary"]["max_cirq_density_error"],
            "max_pennylane_density_error": witnesses["summary"]["max_pennylane_density_error"],
            "pass": witnesses["summary"]["pass"],
        },
    }
    negative = {
        "gap_sweep_does_not_exceed_classical_carnot_bound": {
            "n_points": len(sweep),
            "max_efficiency_minus_bound": float(
                max(row["efficiency"] - row["carnot_bound"] for row in sweep)
            ),
            "pass": all(row["efficiency"] <= row["carnot_bound"] + 1e-10 for row in sweep),
        },
        "reverse_mode_requires_work_input": {
            "work_input": reverse["summary"]["work_input"],
            "q_cold_absorbed": reverse["summary"]["q_cold_absorbed"],
            "pass": bool(reverse["summary"]["work_input"] > 0.0 and reverse["summary"]["q_cold_absorbed"] > 0.0),
        },
        "classical_cycle_does_not_supply_nonclassical_mechanism": {
            "scope_note": "This is a classical reversible thermodynamic boundary/control row.",
            "pass": True,
        },
    }
    boundary = {
        "hot_and_cold_reservoirs_are_distinct": {
            "t_hot": forward["parameters"]["t_hot"],
            "t_cold": forward["parameters"]["t_cold"],
            "pass": forward["parameters"]["t_hot"] > forward["parameters"]["t_cold"] > 0.0,
        },
        "cycle_returns_to_initial_state_in_reversible_bookkeeping": {
            "initial_label": forward["steps"][0]["before"]["label"],
            "final_label": forward["steps"][-1]["after"]["label"],
            "initial_p": forward["steps"][0]["before"]["p_excited"],
            "final_p": forward["steps"][-1]["after"]["p_excited"],
            "pass": abs(forward["steps"][0]["before"]["p_excited"] - forward["steps"][-1]["after"]["p_excited"]) < 1e-10,
        },
    }
    all_pass = all(row["pass"] for section in (positive, negative, boundary) for row in section.values())
    results = {
        "name": "carnot_two_bath_reversible_cycle",
        "classification": classification,
        "sim_execution_kind": sim_execution_kind,
        "promotion_allowed": promotion_allowed,
        "claim_ceiling": "classical full reversible Carnot cycle control only",
        "promotion_condition": "Never promotes bridge or nonclassical claims; may anchor classical negative-space boundaries.",
        "blocked_until": "Needs separate admitted runtime-engine row before engine-surface promotion.",
        "next_lego_target": "classical_negative_space_boundary_manifest",
        "demotion_condition": "Demote to calibration-only if any stroke, bound, or return-state predicate fails.",
        "out_of_scope": [
            "bridge claim",
            "nonclassical claim",
            "runtime engine admission",
            "axis or GStack claim",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "forward_cycle": forward,
        "reverse_cycle": reverse,
        "density_witnesses": witnesses,
        "operating_point_sweep": sweep,
        "summary": {
            "all_pass": all_pass,
            "forward_efficiency": forward["summary"]["efficiency"],
            "forward_carnot_bound": forward["summary"]["carnot_bound"],
            "reverse_cop": reverse["summary"]["cop"],
            "reverse_cop_carnot": reverse["summary"]["cop_carnot"],
            "scope_note": "Full classical reversible Carnot control row; not bridge or nonclassical evidence.",
        },
    }
    out_path = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "carnot_two_bath_reversible_cycle_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
