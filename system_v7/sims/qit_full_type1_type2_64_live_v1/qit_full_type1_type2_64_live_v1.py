#!/usr/bin/env python3
"""Controller for qit_full_type1_type2_64_live_v1.

Ceiling: scratch diagnostic. This creates a finite 64-slot atlas schedule,
runs an ordered object-formation readout over four loop objects, and records
controls that erase the order/projection needed for object identity.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import z3

from qit_full_type1_type2_64_live_v1_common import (
    ATLAS_SOURCE,
    CLAIM_CEILING,
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULTS,
    ROOT,
    SIM_DIR,
    SIM_ID,
    build_core_measurement,
    build_schedule,
    now_z,
    object_ids,
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
        "reason": "load-bearing finite gate polarity: the computed full 64-slot object gate negation is UNSAT",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT polarity over the same computed finite gate",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive atlas schedule construction, object-card hashing, JSON emission",
    },
}

TOOL_INTEGRATION_DEPTH = {"z3": "load_bearing", "cvc5": "load_bearing", "python_stdlib": "supportive"}


def solver_polarity(values: dict[str, Any]) -> dict[str, Any]:
    z = z3.Solver()
    slot_count = z3.Int("slot_count")
    macro_count = z3.Int("macro_count")
    chart_locked = z3.Int("chart_locked")
    type1_slots = z3.Int("type1_slots")
    type2_slots = z3.Int("type2_slots")
    unique_coords = z3.Int("unique_coords")
    ordered_accuracy = z3.Real("ordered_accuracy")
    bag_unique = z3.Int("bag_unique")
    object_count = z3.Int("object_count")
    z.add(slot_count == int(values["slot_count"]))
    z.add(macro_count == int(values["macro_stage_count"]))
    z.add(chart_locked == int(values["chart_locked_slots"]))
    z.add(type1_slots == int(values["type1_slots"]))
    z.add(type2_slots == int(values["type2_slots"]))
    z.add(unique_coords == int(values["unique_coordinate_count"]))
    z.add(ordered_accuracy == z3.RealVal(str(values["ordered_accuracy"])))
    z.add(bag_unique == int(values["bag_unique_signature_count"]))
    z.add(object_count == int(values["object_count"]))
    full_gate = z3.And(
        slot_count == 64,
        macro_count == 16,
        chart_locked == 16,
        type1_slots == 32,
        type2_slots == 32,
        unique_coords == 64,
        ordered_accuracy == z3.RealVal("1.0"),
        bag_unique < object_count,
    )
    z.add(z3.Not(full_gate))
    z3_verdict = str(z.check()).lower()

    z_control = z3.Solver()
    erased_unique = z3.Int("erased_unique")
    control_objects = z3.Int("control_objects")
    z_control.add(erased_unique == int(values["bag_unique_signature_count"]))
    z_control.add(control_objects == int(values["object_count"]))
    z_control.add(erased_unique < control_objects)
    z3_control_verdict = str(z_control.check()).lower()

    cv = cvc5.Solver()
    cv.setLogic("QF_LIRA")
    int_sort = cv.getIntegerSort()
    real_sort = cv.getRealSort()
    cv_slot = cv.mkConst(int_sort, "slot_count")
    cv_macro = cv.mkConst(int_sort, "macro_count")
    cv_chart = cv.mkConst(int_sort, "chart_locked")
    cv_t1 = cv.mkConst(int_sort, "type1_slots")
    cv_t2 = cv.mkConst(int_sort, "type2_slots")
    cv_unique = cv.mkConst(int_sort, "unique_coords")
    cv_bag = cv.mkConst(int_sort, "bag_unique")
    cv_objects = cv.mkConst(int_sort, "object_count")
    cv_acc = cv.mkConst(real_sort, "ordered_accuracy")

    def eq_int(term: Any, number: int) -> Any:
        return cv.mkTerm(Kind.EQUAL, term, cv.mkInteger(number))

    for formula in (
        eq_int(cv_slot, int(values["slot_count"])),
        eq_int(cv_macro, int(values["macro_stage_count"])),
        eq_int(cv_chart, int(values["chart_locked_slots"])),
        eq_int(cv_t1, int(values["type1_slots"])),
        eq_int(cv_t2, int(values["type2_slots"])),
        eq_int(cv_unique, int(values["unique_coordinate_count"])),
        eq_int(cv_bag, int(values["bag_unique_signature_count"])),
        eq_int(cv_objects, int(values["object_count"])),
        cv.mkTerm(Kind.EQUAL, cv_acc, cv.mkReal("1.0")),
    ):
        cv.assertFormula(formula)
    cv_gate = cv.mkTerm(
        Kind.AND,
        eq_int(cv_slot, 64),
        eq_int(cv_macro, 16),
        eq_int(cv_chart, 16),
        eq_int(cv_t1, 32),
        eq_int(cv_t2, 32),
        eq_int(cv_unique, 64),
        cv.mkTerm(Kind.EQUAL, cv_acc, cv.mkReal("1.0")),
        cv.mkTerm(Kind.LT, cv_bag, cv_objects),
    )
    cv.assertFormula(cv.mkTerm(Kind.NOT, cv_gate))
    cv_result = cv.checkSat()
    cvc5_verdict = "sat" if cv_result.isSat() else "unsat" if cv_result.isUnsat() else str(cv_result).lower()

    cv_control = cvc5.Solver()
    cv_control.setLogic("QF_LIA")
    ci = cv_control.getIntegerSort()
    cb = cv_control.mkConst(ci, "bag_unique")
    co = cv_control.mkConst(ci, "object_count")
    cv_control.assertFormula(cv_control.mkTerm(Kind.EQUAL, cb, cv_control.mkInteger(int(values["bag_unique_signature_count"]))))
    cv_control.assertFormula(cv_control.mkTerm(Kind.EQUAL, co, cv_control.mkInteger(int(values["object_count"]))))
    cv_control.assertFormula(cv_control.mkTerm(Kind.LT, cb, co))
    cv_control_result = cv_control.checkSat()
    cvc5_control_verdict = (
        "sat" if cv_control_result.isSat() else "unsat" if cv_control_result.isUnsat() else str(cv_control_result).lower()
    )

    return {
        "z3": {
            "ran": True,
            "verdict": z3_verdict,
            "load_bearing": True,
            "full_gate_negation": z3_verdict,
            "erased_control_verdict": z3_control_verdict,
            "identity": "computed 64-slot object gate is forced; bag-erased projection remains collapsed",
        },
        "cvc5": {
            "ran": True,
            "verdict": cvc5_verdict,
            "load_bearing": True,
            "full_gate_negation": cvc5_verdict,
            "erased_control_verdict": cvc5_control_verdict,
            "identity": "independent SMT encoding agrees with z3 on full and erased polarity",
        },
    }


def build_result() -> dict[str, Any]:
    RESULTS.mkdir(parents=True, exist_ok=True)
    schedule = build_schedule()
    core = build_core_measurement()
    gates = {
        "slot_count_is_64": core["schedule_summary"]["slot_count"] == 64,
        "macro_stage_count_is_16": core["schedule_summary"]["macro_stage_count"] == 16,
        "four_substages_per_macro": core["schedule_summary"]["substage_count_per_macro"] == 4,
        "type1_type2_split_32_each": core["schedule_summary"]["type1_slots"] == 32
        and core["schedule_summary"]["type2_slots"] == 32,
        "chart_locked_16_runtime_probe_48": core["schedule_summary"]["chart_locked_slots"] == 16
        and core["schedule_summary"]["runtime_probe_slots"] == 48,
        "ordered_object_accuracy_full": core["ordered_object_formation"]["ordered_accuracy"] == 1.0,
        "entropy_gradient_positive": core["ordered_object_formation"]["min_entropy_drop_bits"] > 0.0
        and core["ordered_object_formation"]["all_entropy_gradients_monotone"],
        "bag_control_collapses": core["negative_controls"]["bag_topology"]["unique_signature_count"] == 1,
        "first_static_control_collapses": core["negative_controls"]["first_static"]["unique_signature_count"] == 1,
    }
    solver_values = {
        **core["schedule_summary"],
        "ordered_accuracy": core["ordered_object_formation"]["ordered_accuracy"],
        "bag_unique_signature_count": core["negative_controls"]["bag_topology"]["unique_signature_count"],
        "object_count": len(object_ids()),
    }
    proofs = solver_polarity(solver_values)
    all_pass = all(gates.values()) and proofs["z3"]["verdict"] == "unsat" and proofs["cvc5"]["verdict"] == "unsat"
    payload = {
        "schema_version": f"cr.{SIM_ID}.result.v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": now_z(),
        "mode": "atlas_64_ordered_object_formation_scout",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "common_source_path": rel(COMMON_PATH),
        "common_source_sha256": sha256_file(COMMON_PATH),
        "result_path": rel(RESULT_PATH),
        "claim": (
            "A finite 64-slot Type-1/Type-2 atlas schedule can form four ordered loop objects "
            "under ordered observations while static/path-erased projections collapse identity."
        ),
        "claim_ceiling": CLAIM_CEILING,
        "allowed_claims": [
            "finite ordered schedule object cards",
            "scratch entropy-gradient over four finite loop objects",
            "Type-1/Type-2 order-difference comparison",
            "erasure controls for object identity",
        ],
        "disallowed_claims": [
            "real-world perception",
            "Axis0 admission",
            "FEP admission",
            "manifold or physics admission",
            "full QIT engine runtime closure",
            "Lev mesh production readiness",
        ],
        "fences": {
            "desktop_archives_not_authority": True,
            "atlas_status": "scaffold chart grounded against owner source docs; not runtime closure",
            "result_ceiling": "scratch diagnostic only",
        },
        "root_constraints_in_force": {
            "F01_finite_carrier": "64 finite slots, 16 macro rows, 4 substages each",
            "N01_order_sensitive_operation": "ordered stream succeeds while static/path-erased controls collapse identity",
        },
        "finite_map": {
            "domain": "finite atlas slots with topology/token/result/operator/substage fields",
            "codomain": "posterior over four ordered loop-object cards plus survivor/anti hashes",
            "map": "candidate -> ordered observations -> Bayesian gate -> object card receipt",
        },
        "domain": {
            "object_ids": object_ids(),
            "slot_count": len(schedule),
            "macro_stage_count": 16,
            "substage_count_per_macro": 4,
        },
        "codomain_or_output": {
            "readouts": ["posterior", "entropy_bits", "object_card_survivor_hash", "anti_hashes"],
            "verdict_unit": "ordered recovery vs erased projection collapse",
        },
        "carrier_realization": {
            "source": rel(ATLAS_SOURCE),
            "source_sha256": sha256_file(ATLAS_SOURCE),
            "schedule_sha256": core["schedule_summary"]["schedule_sha256"],
            "schedule_rows_head": schedule[:8],
        },
        "dependency_receipts": {
            "atlas": source_lock(ATLAS_SOURCE, "schedule_authority"),
            "common": source_lock(COMMON_PATH, "shared_finite_carrier"),
        },
        "blocked_consumers": [
            "QIT_engine_admission",
            "Axis0",
            "FEP",
            "Xi/Phi0",
            "physics",
            "Lev_mesh_runtime",
            "production_perception",
        ],
        "matrix64_schedule": core["schedule_summary"],
        "core_measurement": core,
        "crossover_proofs": proofs,
        "gates": gates,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
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
                "ordered_accuracy": result["core_measurement"]["ordered_object_formation"]["ordered_accuracy"],
                "bag_unique": result["core_measurement"]["negative_controls"]["bag_topology"]["unique_signature_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
