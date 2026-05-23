#!/usr/bin/env python3
"""SymPy two-level two-bath gap-change work/heat identities."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
from pathlib import Path

import sympy as sp
from receipt_boundary import apply_default_receipt_boundary


NAME = "sympy_two_level_two_bath_gap_change_work_heat_identities"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "proves exact two-level thermal population, work/heat accounting, and efficiency identities",
    }
}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing"}


def thermal_excited_population(beta: sp.Expr, gap: sp.Expr) -> sp.Expr:
    return sp.Integer(1) / (sp.Integer(1) + sp.exp(beta * gap))


def as_text(value: sp.Expr) -> str:
    return str(sp.simplify(value))


def as_float(value: sp.Expr) -> float:
    return float(sp.N(value, 18))


def main() -> int:
    beta_h, beta_c, gap_h, gap_c = sp.symbols("beta_h beta_c gap_h gap_c", positive=True)

    p_hot = thermal_excited_population(beta_h, gap_h)
    p_cold = thermal_excited_population(beta_c, gap_c)
    delta_p = sp.simplify(p_hot - p_cold)

    q_hot = sp.simplify(gap_h * delta_p)
    q_cold = sp.simplify(gap_c * (p_cold - p_hot))
    w_out = sp.simplify((gap_h - gap_c) * delta_p)
    efficiency = sp.simplify(w_out / q_hot)
    accounting_residual = sp.simplify(q_hot + q_cold - w_out)

    no_gap_work = sp.simplify(w_out.subs(gap_h, gap_c))
    scaled_gap_subs = {beta_c: beta_h * gap_h / gap_c}
    scaled_gap_population_delta = sp.simplify(delta_p.subs(scaled_gap_subs))
    scaled_gap_work = sp.simplify(w_out.subs(scaled_gap_subs))

    positive_values = {
        beta_h: sp.Rational(1, 5),
        beta_c: sp.Integer(1),
        gap_h: sp.Integer(4),
        gap_c: sp.Integer(2),
    }
    reversed_temperature_values = {
        beta_h: sp.Integer(1),
        beta_c: sp.Rational(1, 5),
        gap_h: sp.Integer(4),
        gap_c: sp.Integer(2),
    }
    same_temperature_values = {
        beta_h: sp.Rational(1, 2),
        beta_c: sp.Rational(1, 2),
        gap_h: sp.Integer(4),
        gap_c: sp.Integer(2),
    }

    positive = {
        "hot_excited_population": as_float(p_hot.subs(positive_values)),
        "cold_excited_population": as_float(p_cold.subs(positive_values)),
        "Q_hot": as_float(q_hot.subs(positive_values)),
        "Q_cold": as_float(q_cold.subs(positive_values)),
        "W_out": as_float(w_out.subs(positive_values)),
        "efficiency": as_float(efficiency.subs(positive_values)),
        "carnot_bound": as_float((sp.Integer(1) - beta_h / beta_c).subs(positive_values)),
        "energy_accounting_residual": as_float(accounting_residual.subs(positive_values)),
    }
    positive_checks = {
        "hot_population_exceeds_cold_population": positive["hot_excited_population"] > positive["cold_excited_population"],
        "work_positive": positive["W_out"] > 0.0,
        "absorbs_hot_heat": positive["Q_hot"] > 0.0,
        "rejects_cold_heat": positive["Q_cold"] < 0.0,
        "efficiency_respects_carnot_bound": positive["efficiency"] <= positive["carnot_bound"],
        "energy_accounting_closes": abs(positive["energy_accounting_residual"]) < 1e-14,
    }

    reversed_work = as_float(w_out.subs(reversed_temperature_values))
    same_temperature_hot_population = as_float(p_hot.subs(same_temperature_values))
    same_temperature_cold_population = as_float(p_cold.subs(same_temperature_values))
    graveyards = {
        "no_gap_change_gives_zero_work": {
            "symbolic_W_out": as_text(no_gap_work),
            "passed": bool(no_gap_work == 0),
        },
        "matching_scaled_gaps_equalize_populations_and_zero_work": {
            "symbolic_population_delta": as_text(scaled_gap_population_delta),
            "symbolic_W_out": as_text(scaled_gap_work),
            "passed": bool(scaled_gap_population_delta == 0 and scaled_gap_work == 0),
        },
        "reversed_temperature_assignment_consumes_work": {
            "W_out": reversed_work,
            "passed": bool(reversed_work < 0.0),
        },
        "same_temperature_with_gap_change_violates_hot_cold_population_order": {
            "hot_population": same_temperature_hot_population,
            "cold_population": same_temperature_cold_population,
            "passed": bool(same_temperature_hot_population < same_temperature_cold_population),
        },
        "super_carnot_efficiency_claim_rejected": {
            "efficiency": positive["efficiency"],
            "carnot_bound": positive["carnot_bound"],
            "claimed_efficiency": positive["carnot_bound"] + 0.05,
            "passed": bool(positive["efficiency"] <= positive["carnot_bound"] < positive["carnot_bound"] + 0.05),
        },
    }

    exact_identity_checks = {
        "efficiency_identity": bool(sp.simplify(efficiency - (sp.Integer(1) - gap_c / gap_h)) == 0),
        "energy_accounting_identity": bool(accounting_residual == 0),
        "work_factorization_identity": bool(sp.simplify(w_out - (gap_h - gap_c) * (p_hot - p_cold)) == 0),
    }
    all_pass = bool(
        all(positive_checks.values())
        and all(graveyard["passed"] for graveyard in graveyards.values())
        and all(exact_identity_checks.values())
    )

    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "SymPy exact two-level thermal endpoint gap-change work/heat identities only; this is a symbolic "
            "classical baseline for finite-carrier heat/work accounting, not a full Carnot theorem; no simulated "
            "bath dynamics, QIT, GStack, axis, bridge, nonclassical, runtime-engine, or target-system admission"
        ),
        "next_lego_target": "exact_two_level_work_heat_identity_baseline",
        "promotion_condition": (
            "May only support later calibration planning after explicit stroke dynamics and independent tool receipts "
            "reproduce compatible heat/work bounds with adjacent graveyards."
        ),
        "demotion_condition": (
            "Demote if exact identities fail, if numeric hot/cold ordering does not produce positive bounded work, "
            "or if any adjacent graveyard does not collapse or invert."
        ),
        "blocked_until": "blocked from target cycle mechanics until explicit stroke dynamics and work-reservoir fixtures exist",
        "out_of_scope": [
            "No Lindblad bath thermalization dynamics.",
            "No finite-time irreversibility model.",
            "No measurement, feedback, QIT, GStack, axis, bridge, nonclassical, runtime-engine, or target-system admission.",
        ],
        "divergence_log": (
            "This SymPy fixture proves closed-form endpoint identities for the same two-level gap-change calibration "
            "surface as the QuTiP and Qiskit receipts, but does not simulate stroke dynamics or physical bath coupling."
        ),
        "operation_sequence": [
            "declare positive inverse-temperature and Hamiltonian-gap symbols",
            "define two-level thermal excited population p(beta, gap) = 1 / (1 + exp(beta * gap))",
            "compute hot and cold endpoint population difference",
            "derive Q_hot, Q_cold, W_out, efficiency, and energy-accounting residual",
            "prove exact efficiency and accounting identities",
            "check numeric positive case and adjacent graveyard substitutions",
        ],
        "carrier_topology": "finite two-level symbolic thermal endpoint populations with two Hamiltonian gaps",
        "observable": "symbolic excited populations, Q_hot, Q_cold, W_out, efficiency, Carnot-bound comparison, and exact residuals",
        "pass_fail_predicate": (
            "efficiency equals 1 - gap_c/gap_h, heat/work accounting closes exactly, the numeric hot/cold case produces "
            "positive bounded work, and graveyards collapse or invert"
        ),
        "graveyards": [
            "no gap change gives zero work",
            "matching scaled gaps equalize populations and zero work",
            "reversed temperature assignment consumes work",
            "same temperature with gap change violates hot/cold population order",
            "super-Carnot efficiency claim rejected",
        ],
        "baselines": [
            "QuTiP two-level two-bath gap-change work/heat receipt",
            "Qiskit two-level two-bath gap-change work/heat receipt",
            "scalar two-bath four-stroke work/heat bound receipt",
        ],
        "alternative_formulations": [
            "Lindblad two-bath thermalization stroke schedule",
            "finite-time irreversible gap-change schedule",
            "density-matrix endpoint accounting with QuTiP or Qiskit",
        ],
        "exact_tool_function_needs": {
            "sympy": ["symbols", "exp", "simplify", "subs", "Rational"],
        },
        "lego_or_coupling_target": "exact_two_level_work_heat_identity_baseline",
        "positive_case": positive,
        "positive_checks": positive_checks,
        "exact_identities": {
            "p_hot": as_text(p_hot),
            "p_cold": as_text(p_cold),
            "Q_hot": as_text(q_hot),
            "Q_cold": as_text(q_cold),
            "W_out": as_text(w_out),
            "efficiency": as_text(efficiency),
            "energy_accounting_residual": as_text(accounting_residual),
            "checks": exact_identity_checks,
        },
        "graveyard_companions": graveyards,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"name": NAME, "all_pass": all_pass, "result": str(out_path)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
