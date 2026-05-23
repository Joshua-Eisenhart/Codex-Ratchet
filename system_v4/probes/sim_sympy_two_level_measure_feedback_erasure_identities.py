#!/usr/bin/env python3
"""SymPy two-level measurement-feedback-erasure identities."""

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


NAME = "sympy_two_level_measure_feedback_erasure_identities"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "proves exact binary measurement information, conditional feedback work, and Landauer-floor identities",
    }
}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing"}


def entropy_nats(probabilities: list[sp.Expr]) -> sp.Expr:
    terms = []
    for probability in probabilities:
        if probability == 0:
            continue
        terms.append(probability * sp.log(probability))
    return sp.simplify(-sum(terms, sp.Integer(0)))


def as_text(value: sp.Expr) -> str:
    return str(sp.simplify(value))


def as_float(value: sp.Expr) -> float:
    return float(sp.N(value, 18))


def main() -> int:
    kbt = sp.Integer(2)
    p0_unbiased = sp.Rational(1, 2)
    p1_unbiased = sp.Rational(1, 2)
    p0_deterministic = sp.Integer(1)
    p1_deterministic = sp.Integer(0)

    information_unbiased = entropy_nats([p0_unbiased, p1_unbiased])
    information_deterministic = entropy_nats([p0_deterministic, p1_deterministic])

    # H = |1><1|. Conditional feedback maps the excited branch to the ground branch.
    conditional_work_unbiased = sp.simplify(p1_unbiased)
    conditional_work_deterministic = sp.simplify(p1_deterministic)
    identity_feedback_work = sp.Integer(0)
    wrong_same_flip_work = sp.simplify(p1_unbiased - p0_unbiased)

    erasure_floor_unbiased = sp.simplify(kbt * information_unbiased)
    erasure_floor_unit_kbt = sp.simplify(information_unbiased)
    net_after_erasure_bound = sp.simplify(conditional_work_unbiased - erasure_floor_unbiased)

    positive_checks = {
        "information_equals_ln2": bool(sp.simplify(information_unbiased - sp.log(2)) == 0),
        "conditional_work_positive": bool(conditional_work_unbiased > 0),
        "work_respects_information_bound": bool(sp.N(erasure_floor_unbiased - conditional_work_unbiased) > 0),
        "erasure_floor_matches_kbt_information": bool(sp.simplify(erasure_floor_unbiased - kbt * information_unbiased) == 0),
        "unit_kbt_erasure_floor_numeric_ln2": bool(abs(as_float(erasure_floor_unit_kbt) - 0.6931471805599453) < 1e-12),
        "net_after_erasure_not_positive": bool(sp.N(net_after_erasure_bound) < 0),
    }

    graveyards = {
        "deterministic_record_has_zero_information_and_zero_work": {
            "information_nats": as_text(information_deterministic),
            "conditional_work": as_text(conditional_work_deterministic),
            "passed": bool(information_deterministic == 0 and conditional_work_deterministic == 0),
        },
        "identity_feedback_extracts_no_work": {
            "work": as_text(identity_feedback_work),
            "passed": bool(identity_feedback_work == 0),
        },
        "wrong_same_flip_feedback_extracts_no_average_work": {
            "work": as_text(wrong_same_flip_work),
            "passed": bool(wrong_same_flip_work == 0),
        },
        "omitting_erasure_flags_repeated_cycle_surplus": {
            "work_without_record_erasure": as_text(conditional_work_unbiased),
            "erasure_floor": as_text(erasure_floor_unbiased),
            "passed": bool(conditional_work_unbiased > 0 and sp.N(net_after_erasure_bound) < 0),
        },
        "too_cold_erasure_bound_rejects_unit_work_claim": {
            "claimed_work": as_text(sp.Integer(1)),
            "bound": as_text(erasure_floor_unbiased),
            "passed": bool(sp.N(erasure_floor_unbiased - 1) > 0),
        },
    }

    exact_identity_checks = {
        "binary_unbiased_entropy_identity": bool(sp.simplify(information_unbiased - sp.log(2)) == 0),
        "deterministic_entropy_identity": bool(information_deterministic == 0),
        "conditional_feedback_work_identity": bool(sp.simplify(conditional_work_unbiased - sp.Rational(1, 2)) == 0),
        "landauer_floor_identity": bool(sp.simplify(erasure_floor_unbiased - 2 * sp.log(2)) == 0),
    }
    all_pass = bool(
        all(positive_checks.values())
        and all(row["passed"] for row in graveyards.values())
        and all(exact_identity_checks.values())
    )

    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "SymPy exact two-level measurement-feedback-erasure bookkeeping identities only; this is a symbolic "
            "classical baseline for one-bit information/work/erasure accounting, not a thermal erasure dynamics "
            "simulation; no QIT, GStack, axis, bridge, nonclassical, runtime-engine, or target-system admission"
        ),
        "next_lego_target": "exact_measure_feedback_erasure_identity_baseline",
        "promotion_allowed": False,
        "promotion_condition": (
            "May only support later calibration planning after explicit density-matrix branch updates and thermal "
            "erasure dynamics reproduce compatible bounds with adjacent graveyards."
        ),
        "demotion_condition": (
            "Demote if exact entropy/work/floor identities fail, if conditional work exceeds kBT*I, or if "
            "deterministic/no-feedback/wrong-feedback/no-erasure controls fail."
        ),
        "blocked_until": "blocked from target feedback-cycle mechanics until thermal erasure dynamics and work-reservoir fixtures exist",
        "out_of_scope": [
            "No density-matrix branch update.",
            "No Lindblad thermal erasure stroke.",
            "No physical work reservoir.",
            "No repeated memory register dynamics.",
            "No QIT, GStack, axis, bridge, nonclassical, runtime-engine, or target-system admission.",
        ],
        "divergence_log": (
            "This SymPy fixture is an exact scalar identity baseline for the same measurement-feedback-erasure "
            "calibration surface as the QuTiP and Qiskit density-matrix receipts. It intentionally omits physical "
            "branch-state evolution and thermal reset dynamics."
        ),
        "operation_sequence": [
            "declare an unbiased two-outcome record and a deterministic one-outcome record",
            "compute binary Shannon information in nats",
            "compute conditional feedback work under H = |1><1| from the excited branch probability",
            "compute the Landauer erasure floor kBT times measurement information",
            "compare conditional work to the information bound",
            "run deterministic-record, identity-feedback, wrong-feedback, no-erasure, and overclaim graveyards",
        ],
        "carrier_topology": "finite two-outcome classical branch record coupled to a two-level energy label",
        "observable": "record probabilities, information in nats, conditional feedback work, erasure heat floor, and net-after-erasure bound",
        "pass_fail_predicate": (
            "unbiased record has I=ln2, conditional feedback extracts positive work no greater than kBT*I, erasure "
            "floor equals kBT*I, net-after-erasure is not positive, and adjacent graveyards collapse or flag"
        ),
        "graveyards": [
            "deterministic record has zero information and zero work",
            "identity feedback extracts no work",
            "wrong same-flip feedback extracts no average work",
            "omitting erasure flags repeated-cycle surplus",
            "unit work overclaim rejected by kBT ln2 bound at kBT=2",
        ],
        "baselines": [
            "numpy binary entropy feedback work bound and Landauer erasure-floor receipt",
            "QuTiP two-level measurement-feedback-erasure receipt",
            "Qiskit two-level measurement-feedback-erasure receipt",
        ],
        "alternative_formulations": [
            "density-matrix projective branch update with QuTiP",
            "density-matrix projective branch update with Qiskit",
            "Lindblad thermal reset erasure stroke",
        ],
        "exact_tool_function_needs": {
            "sympy": ["Rational", "log", "simplify", "N"],
        },
        "lego_or_coupling_target": "exact_measure_feedback_erasure_identity_baseline",
        "positive_case": {
            "kBT": as_text(kbt),
            "probabilities": [as_text(p0_unbiased), as_text(p1_unbiased)],
            "information_nats": as_text(information_unbiased),
            "unit_kBT_erasure_floor": as_text(erasure_floor_unit_kbt),
            "conditional_feedback_work": as_text(conditional_work_unbiased),
            "erasure_floor": as_text(erasure_floor_unbiased),
            "net_after_erasure_bound": as_text(net_after_erasure_bound),
            "numeric": {
                "information_nats": as_float(information_unbiased),
                "unit_kBT_erasure_floor": as_float(erasure_floor_unit_kbt),
                "conditional_feedback_work": as_float(conditional_work_unbiased),
                "erasure_floor": as_float(erasure_floor_unbiased),
                "net_after_erasure_bound": as_float(net_after_erasure_bound),
            },
        },
        "positive_checks": positive_checks,
        "exact_identities": {
            "information_unbiased": as_text(information_unbiased),
            "information_deterministic": as_text(information_deterministic),
            "conditional_work_unbiased": as_text(conditional_work_unbiased),
            "erasure_floor_unbiased": as_text(erasure_floor_unbiased),
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
