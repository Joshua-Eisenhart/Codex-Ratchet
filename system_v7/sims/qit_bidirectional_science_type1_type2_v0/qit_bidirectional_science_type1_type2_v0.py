#!/usr/bin/env python3
"""Controller for qit_bidirectional_science_type1_type2_v0."""

from __future__ import annotations

import argparse
import json
from typing import Any

import cvc5
from cvc5 import Kind
import z3

from qit_bidirectional_science_type1_type2_v0_common import (
    BLOCKED_CONSUMERS,
    CLAIM_CEILING,
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    OBJECT_CARD,
    PROJECTION_ENVELOPE,
    PROMOTION_ALLOWED,
    RESULTS,
    SIM_DIR,
    SIM_ID,
    V1_ENVELOPE,
    V43_VALIDATION,
    build_core_measurement,
    now_z,
    rel,
    sha256_file,
    source_lock,
    stable_sha256,
    write_json,
)

SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"
COMMON_PATH = SIM_DIR / f"{SIM_ID}_common.py"
RESULT_PATH = RESULTS / f"{SIM_ID}_results.json"

classification = "scratch_diagnostic"

TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite gate polarity for Type-1/Type-2 method closure and erased controls",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT polarity over the same measured method values",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive object-card receipt loading, hashing, and JSON emission",
    },
}

TOOL_INTEGRATION_DEPTH = {"z3": "load_bearing", "cvc5": "load_bearing", "python_stdlib": "supportive"}


def solver_polarity(values: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    object_count = z3.Int("object_count")
    view_count = z3.Int("view_count")
    type1 = z3.Real("type1_accuracy")
    type1_wrong = z3.Real("type1_wrong_accept")
    type2 = z3.Real("type2_accuracy")
    type2_bag = z3.Real("type2_bag_accuracy")
    type2_erased = z3.Real("type2_erased_accuracy")
    solver.add(object_count == int(values["object_count"]))
    solver.add(view_count == int(values["view_count"]))
    solver.add(type1 == z3.RealVal(str(values["type1_accuracy"])))
    solver.add(type1_wrong == z3.RealVal(str(values["type1_wrong_accept"])))
    solver.add(type2 == z3.RealVal(str(values["type2_accuracy"])))
    solver.add(type2_bag == z3.RealVal(str(values["type2_bag_accuracy"])))
    solver.add(type2_erased == z3.RealVal(str(values["type2_erased_accuracy"])))
    full_gate = z3.And(
        object_count == 4,
        view_count == 5,
        type1 == z3.RealVal("1.0"),
        type1_wrong <= z3.RealVal("0.25"),
        type2 >= z3.RealVal("0.85"),
        type2_bag <= z3.RealVal("0.25"),
        type2_erased <= z3.RealVal("0.25"),
        type2 - type2_bag >= z3.RealVal("0.5"),
        type2 - type2_erased >= z3.RealVal("0.5"),
    )
    solver.add(z3.Not(full_gate))
    z3_verdict = str(solver.check()).lower()

    control = z3.Solver()
    c1 = z3.Real("wrong_candidate")
    c2 = z3.Real("bag_control")
    c3 = z3.Real("erased_control")
    control.add(c1 == z3.RealVal(str(values["type1_wrong_accept"])))
    control.add(c2 == z3.RealVal(str(values["type2_bag_accuracy"])))
    control.add(c3 == z3.RealVal(str(values["type2_erased_accuracy"])))
    control.add(c1 <= z3.RealVal("0.25"))
    control.add(c2 <= z3.RealVal("0.25"))
    control.add(c3 <= z3.RealVal("0.25"))
    z3_control = str(control.check()).lower()

    cv = cvc5.Solver()
    cv.setLogic("QF_LIRA")
    int_sort = cv.getIntegerSort()
    real_sort = cv.getRealSort()
    cv_objects = cv.mkConst(int_sort, "object_count")
    cv_views = cv.mkConst(int_sort, "view_count")
    cv_type1 = cv.mkConst(real_sort, "type1_accuracy")
    cv_wrong = cv.mkConst(real_sort, "type1_wrong_accept")
    cv_type2 = cv.mkConst(real_sort, "type2_accuracy")
    cv_bag = cv.mkConst(real_sort, "type2_bag_accuracy")
    cv_erased = cv.mkConst(real_sort, "type2_erased_accuracy")
    for formula in (
        cv.mkTerm(Kind.EQUAL, cv_objects, cv.mkInteger(int(values["object_count"]))),
        cv.mkTerm(Kind.EQUAL, cv_views, cv.mkInteger(int(values["view_count"]))),
        cv.mkTerm(Kind.EQUAL, cv_type1, cv.mkReal(str(values["type1_accuracy"]))),
        cv.mkTerm(Kind.EQUAL, cv_wrong, cv.mkReal(str(values["type1_wrong_accept"]))),
        cv.mkTerm(Kind.EQUAL, cv_type2, cv.mkReal(str(values["type2_accuracy"]))),
        cv.mkTerm(Kind.EQUAL, cv_bag, cv.mkReal(str(values["type2_bag_accuracy"]))),
        cv.mkTerm(Kind.EQUAL, cv_erased, cv.mkReal(str(values["type2_erased_accuracy"]))),
    ):
        cv.assertFormula(formula)
    cv_goal = cv.mkTerm(
        Kind.AND,
        cv.mkTerm(Kind.EQUAL, cv_objects, cv.mkInteger(4)),
        cv.mkTerm(Kind.EQUAL, cv_views, cv.mkInteger(5)),
        cv.mkTerm(Kind.EQUAL, cv_type1, cv.mkReal("1.0")),
        cv.mkTerm(Kind.LEQ, cv_wrong, cv.mkReal("0.25")),
        cv.mkTerm(Kind.GEQ, cv_type2, cv.mkReal("0.85")),
        cv.mkTerm(Kind.LEQ, cv_bag, cv.mkReal("0.25")),
        cv.mkTerm(Kind.LEQ, cv_erased, cv.mkReal("0.25")),
        cv.mkTerm(Kind.GEQ, cv.mkTerm(Kind.SUB, cv_type2, cv_bag), cv.mkReal("0.5")),
        cv.mkTerm(Kind.GEQ, cv.mkTerm(Kind.SUB, cv_type2, cv_erased), cv.mkReal("0.5")),
    )
    cv.assertFormula(cv.mkTerm(Kind.NOT, cv_goal))
    cv_result = cv.checkSat()
    cvc5_verdict = "sat" if cv_result.isSat() else "unsat" if cv_result.isUnsat() else str(cv_result).lower()

    cv_control = cvc5.Solver()
    cv_control.setLogic("QF_LRA")
    cr = cv_control.getRealSort()
    cw = cv_control.mkConst(cr, "wrong_candidate")
    cb = cv_control.mkConst(cr, "bag_control")
    ce = cv_control.mkConst(cr, "erased_control")
    cv_control.assertFormula(cv_control.mkTerm(Kind.EQUAL, cw, cv_control.mkReal(str(values["type1_wrong_accept"]))))
    cv_control.assertFormula(cv_control.mkTerm(Kind.EQUAL, cb, cv_control.mkReal(str(values["type2_bag_accuracy"]))))
    cv_control.assertFormula(cv_control.mkTerm(Kind.EQUAL, ce, cv_control.mkReal(str(values["type2_erased_accuracy"]))))
    cv_control.assertFormula(cv_control.mkTerm(Kind.LEQ, cw, cv_control.mkReal("0.25")))
    cv_control.assertFormula(cv_control.mkTerm(Kind.LEQ, cb, cv_control.mkReal("0.25")))
    cv_control.assertFormula(cv_control.mkTerm(Kind.LEQ, ce, cv_control.mkReal("0.25")))
    cv_control_result = cv_control.checkSat()
    cvc5_control = (
        "sat" if cv_control_result.isSat() else "unsat" if cv_control_result.isUnsat() else str(cv_control_result).lower()
    )
    return {
        "z3": {
            "ran": True,
            "verdict": z3_verdict,
            "load_bearing": True,
            "full_gate_negation": z3_verdict,
            "erased_control_verdict": z3_control,
            "identity": "negated bidirectional method gate is UNSAT; erased/wrong controls are SAT",
        },
        "cvc5": {
            "ran": True,
            "verdict": cvc5_verdict,
            "load_bearing": True,
            "full_gate_negation": cvc5_verdict,
            "erased_control_verdict": cvc5_control,
            "identity": "independent SMT encoding agrees with z3 on finite method gate polarity",
        },
    }


def build_result() -> dict[str, Any]:
    RESULTS.mkdir(parents=True, exist_ok=True)
    core = build_core_measurement()
    values = {
        "object_count": core["type1"]["nominal"]["object_count"],
        "view_count": core["type1"]["nominal"]["view_count"],
        "type1_accuracy": core["type1"]["nominal"]["accuracy"],
        "type1_wrong_accept": core["type1"]["controls"]["wrong_candidate"]["accepted_rate"],
        "type2_accuracy": core["type2"]["nominal"]["accuracy"],
        "type2_bag_accuracy": core["type2"]["controls"]["bag_erased"]["accuracy"],
        "type2_erased_accuracy": core["type2"]["controls"]["view_erased"]["accuracy"],
    }
    proofs = solver_polarity(values)
    gates = {
        **core["gates"],
        "z3_full_gate_unsat": proofs["z3"]["verdict"] == "unsat",
        "cvc5_full_gate_unsat": proofs["cvc5"]["verdict"] == "unsat",
        "erased_controls_sat": proofs["z3"]["erased_control_verdict"] == "sat"
        and proofs["cvc5"]["erased_control_verdict"] == "sat",
    }
    all_pass = all(gates.values())
    payload = {
        "schema_version": f"cr.{SIM_ID}.result.v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": now_z(),
        "mode": "finite_type1_type2_bidirectional_science_method_scout",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "host_consumed": False,
        "live_lev_consumed": False,
        "release_admission_allowed": False,
        "graph_mutation_allowed": False,
        "mesh_projection_allowed": False,
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "common_source_path": rel(COMMON_PATH),
        "common_source_sha256": sha256_file(COMMON_PATH),
        "result_path": rel(RESULT_PATH),
        "claim": (
            "On the same finite projection object-card family, Type-1 candidate-first confirmation and "
            "Type-2 measurement-first reconstruction both run six-stage bidirectional science loops with "
            "distinct strengths and erased-control failures."
        ),
        "claim_ceiling": CLAIM_CEILING,
        "allowed_claims": [
            "finite bidirectional method receipts over four object cards",
            "Type-1/Type-2 method comparison under shared object family",
            "bounded Type-1 and Type-2 intelligence profiles",
            "erased and wrong-candidate control failures",
        ],
        "disallowed_claims": [
            "live perception",
            "full QIT engine admission",
            "Axis0 admission",
            "FEP admission",
            "ontology writer admission",
            "MMM driver admission",
            "Lev mesh runtime integration",
        ],
        "root_constraints_in_force": {
            "F01_finite_carrier": "four finite projection object cards and five finite MMM-style views",
            "N01_order_sensitive_operation": "Type-1 and Type-2 use opposite method orders and fail different controls",
        },
        "finite_map": {
            "domain": "projection object cards, projection views, and two finite science method orders",
            "codomain": "six-stage method receipts and comparison table",
            "map": "object/view evidence -> candidate or measurement -> counter-projection -> update -> falsifier -> receipt",
        },
        "dependency_receipts": {
            "object_card": source_lock(OBJECT_CARD, "v4_3_primary_object_boundary"),
            "v43_validation": source_lock(V43_VALIDATION, "object_preservation_guard"),
            "projection_envelope": source_lock(PROJECTION_ENVELOPE, "parent_projection_battery"),
            "v1_envelope": source_lock(V1_ENVELOPE, "grandparent_64_live_carrier"),
            "common": source_lock(COMMON_PATH, "shared_bidirectional_method_battery"),
        },
        "core_measurement": core,
        "crossover_proofs": proofs,
        "gates": gates,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "z3",
                "qualified_api": "z3.Solver/z3.RealVal/check",
                "input_object": "measured finite method metrics",
                "output_object": "UNSAT negated full gate and SAT erased controls",
                "positive_case": "Type-1=1.0 and Type-2>=0.85",
                "negative_or_erased_control": "wrong candidate <=0.25, erased controls <=0.25",
                "boundary_case": "planning_mmm ambiguity remains Type-2 method limitation",
                "demotion_condition": "if the negated gate is SAT or controls are UNSAT",
                "gates": ["all_pass", "crossover_proofs"],
            },
            {
                "tool": "cvc5",
                "qualified_api": "cvc5.Solver/mkConst/mkTerm/assertFormula/checkSat",
                "input_object": "same measured finite method metrics",
                "output_object": "independent SMT polarity agreement",
                "positive_case": "same as z3",
                "negative_or_erased_control": "same as z3",
                "boundary_case": "same as z3",
                "demotion_condition": "if cvc5 disagrees with z3",
                "gates": ["all_pass", "crossover_proofs"],
            },
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "payload_sha256_without_self": stable_sha256({"core": core, "gates": gates, "proofs": proofs}),
    }
    write_json(RESULT_PATH, payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fresh", action="store_true", help="Accepted for runner symmetry; result path is overwritten.")
    parser.parse_args(argv)
    result = build_result()
    print(
        json.dumps(
            {
                "sim_id": SIM_ID,
                "all_pass": result["all_pass"],
                "result_path": rel(RESULT_PATH),
                "type1_accuracy": result["core_measurement"]["type1"]["nominal"]["accuracy"],
                "type2_accuracy": result["core_measurement"]["type2"]["nominal"]["accuracy"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
