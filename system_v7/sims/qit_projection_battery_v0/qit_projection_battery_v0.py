#!/usr/bin/env python3
"""Controller for qit_projection_battery_v0.

Ceiling: scratch diagnostic. This consumes the v1 finite 64-slot carrier and
tests whether partial MMM-style projections converge back to the same object
without using direct loop/engine identity fields.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import cvc5
from cvc5 import Kind
import z3

from qit_projection_battery_v0_common import (
    CLAIM_CEILING,
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULTS,
    ROOT,
    SIM_DIR,
    SIM_ID,
    V1_CLAIM_CEILING,
    V1_DIR,
    V1_ENVELOPE,
    VIEW_DESCRIPTIONS,
    VIEW_MASKS,
    build_core_measurement,
    canonical_vectors,
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
V1_COMMON_PATH = V1_DIR / "qit_full_type1_type2_64_live_v1_common.py"

classification = "scratch_diagnostic"

BANNED_DIRECT_IDENTITY_FIELDS = {
    5: "loop",
    6: "engine_type",
}

TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing gate polarity: the measured projection-convergence gate negation is UNSAT",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT polarity for the same measured projection battery",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive finite carrier import, projection-card hashing, JSON emission",
    },
}

TOOL_INTEGRATION_DEPTH = {"z3": "load_bearing", "cvc5": "load_bearing", "python_stdlib": "supportive"}


def projection_policy() -> dict[str, Any]:
    masks = {name: sorted(mask) for name, mask in VIEW_MASKS.items()}
    used_indices = sorted({idx for mask in VIEW_MASKS.values() for idx in mask})
    banned_used = sorted(idx for idx in used_indices if idx in BANNED_DIRECT_IDENTITY_FIELDS)
    return {
        "view_masks": masks,
        "view_descriptions": VIEW_DESCRIPTIONS,
        "feature_index_period": 8,
        "banned_direct_identity_fields": BANNED_DIRECT_IDENTITY_FIELDS,
        "banned_identity_indices_used": banned_used,
        "direct_identity_leakage_excluded": not banned_used,
        "direct_identity_hazard": (
            "The v1 carrier contains loop and engine_type fields that would trivially label the four objects. "
            "This packet bans those fields from all nominal MMM projections."
        ),
    }


def direct_identity_hazard_report() -> dict[str, Any]:
    labels, rows = canonical_vectors()
    signatures: dict[str, str] = {}
    for label, row in zip(labels, rows, strict=True):
        identity_only = [
            float(value)
            for idx, value in enumerate(row)
            if idx % 8 in BANNED_DIRECT_IDENTITY_FIELDS
        ]
        signatures[label] = stable_sha256(identity_only)
    unique_count = len(set(signatures.values()))
    return {
        "control_name": "banned_direct_identity_only",
        "unique_signature_count": unique_count,
        "object_count": len(labels),
        "would_trivially_identify_all_objects": unique_count == len(labels),
        "interpretation": "overclaim hazard only; not admitted evidence for projection convergence",
    }


def solver_polarity(values: dict[str, Any]) -> dict[str, Any]:
    z = z3.Solver()
    object_count = z3.Int("object_count")
    view_count = z3.Int("view_count")
    nominal_mean = z3.Real("nominal_mean")
    bag_mean = z3.Real("bag_mean")
    view_erased_mean = z3.Real("view_erased_mean")
    leakage_used = z3.Int("leakage_used")
    z.add(object_count == int(values["object_count"]))
    z.add(view_count == int(values["view_count"]))
    z.add(nominal_mean == z3.RealVal(str(values["nominal_mean"])))
    z.add(bag_mean == z3.RealVal(str(values["bag_mean"])))
    z.add(view_erased_mean == z3.RealVal(str(values["view_erased_mean"])))
    z.add(leakage_used == int(values["leakage_used"]))
    full_gate = z3.And(
        object_count == 4,
        view_count == 5,
        leakage_used == 0,
        nominal_mean >= z3.RealVal("0.85"),
        bag_mean <= z3.RealVal("0.25"),
        view_erased_mean <= z3.RealVal("0.25"),
        nominal_mean - bag_mean >= z3.RealVal("0.5"),
        nominal_mean - view_erased_mean >= z3.RealVal("0.5"),
    )
    z.add(z3.Not(full_gate))
    z3_verdict = str(z.check()).lower()

    z_control = z3.Solver()
    z_control.add(bag_mean == z3.RealVal(str(values["bag_mean"])))
    z_control.add(view_erased_mean == z3.RealVal(str(values["view_erased_mean"])))
    z_control.add(bag_mean <= z3.RealVal("0.25"))
    z_control.add(view_erased_mean <= z3.RealVal("0.25"))
    z3_control_verdict = str(z_control.check()).lower()

    cv = cvc5.Solver()
    cv.setLogic("QF_LIRA")
    int_sort = cv.getIntegerSort()
    real_sort = cv.getRealSort()
    cv_objects = cv.mkConst(int_sort, "object_count")
    cv_views = cv.mkConst(int_sort, "view_count")
    cv_leakage = cv.mkConst(int_sort, "leakage_used")
    cv_nominal = cv.mkConst(real_sort, "nominal_mean")
    cv_bag = cv.mkConst(real_sort, "bag_mean")
    cv_erased = cv.mkConst(real_sort, "view_erased_mean")

    def eq_int(term: Any, number: int) -> Any:
        return cv.mkTerm(Kind.EQUAL, term, cv.mkInteger(number))

    def eq_real(term: Any, number: str) -> Any:
        return cv.mkTerm(Kind.EQUAL, term, cv.mkReal(number))

    for formula in (
        eq_int(cv_objects, int(values["object_count"])),
        eq_int(cv_views, int(values["view_count"])),
        eq_int(cv_leakage, int(values["leakage_used"])),
        eq_real(cv_nominal, str(values["nominal_mean"])),
        eq_real(cv_bag, str(values["bag_mean"])),
        eq_real(cv_erased, str(values["view_erased_mean"])),
    ):
        cv.assertFormula(formula)
    cv_gate = cv.mkTerm(
        Kind.AND,
        eq_int(cv_objects, 4),
        eq_int(cv_views, 5),
        eq_int(cv_leakage, 0),
        cv.mkTerm(Kind.GEQ, cv_nominal, cv.mkReal("0.85")),
        cv.mkTerm(Kind.LEQ, cv_bag, cv.mkReal("0.25")),
        cv.mkTerm(Kind.LEQ, cv_erased, cv.mkReal("0.25")),
        cv.mkTerm(Kind.GEQ, cv.mkTerm(Kind.SUB, cv_nominal, cv_bag), cv.mkReal("0.5")),
        cv.mkTerm(Kind.GEQ, cv.mkTerm(Kind.SUB, cv_nominal, cv_erased), cv.mkReal("0.5")),
    )
    cv.assertFormula(cv.mkTerm(Kind.NOT, cv_gate))
    cv_result = cv.checkSat()
    cvc5_verdict = "sat" if cv_result.isSat() else "unsat" if cv_result.isUnsat() else str(cv_result).lower()

    cv_control = cvc5.Solver()
    cv_control.setLogic("QF_LRA")
    cr = cv_control.getRealSort()
    cb = cv_control.mkConst(cr, "bag_mean")
    ce = cv_control.mkConst(cr, "view_erased_mean")
    cv_control.assertFormula(cv_control.mkTerm(Kind.EQUAL, cb, cv_control.mkReal(str(values["bag_mean"]))))
    cv_control.assertFormula(cv_control.mkTerm(Kind.EQUAL, ce, cv_control.mkReal(str(values["view_erased_mean"]))))
    cv_control.assertFormula(cv_control.mkTerm(Kind.LEQ, cb, cv_control.mkReal("0.25")))
    cv_control.assertFormula(cv_control.mkTerm(Kind.LEQ, ce, cv_control.mkReal("0.25")))
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
            "identity": "nominal partial MMM projections pass while erased controls remain chance",
        },
        "cvc5": {
            "ran": True,
            "verdict": cvc5_verdict,
            "load_bearing": True,
            "full_gate_negation": cvc5_verdict,
            "erased_control_verdict": cvc5_control_verdict,
            "identity": "independent SMT encoding agrees with z3 on projection battery polarity",
        },
    }


def build_result() -> dict[str, Any]:
    RESULTS.mkdir(parents=True, exist_ok=True)
    core = build_core_measurement()
    policy = projection_policy()
    hazard = direct_identity_hazard_report()
    values = {
        "object_count": core["nominal"]["object_count"],
        "view_count": core["nominal"]["view_count"],
        "nominal_mean": core["nominal"]["mean_heldout_accuracy"],
        "bag_mean": core["controls"]["bag_erased"]["mean_heldout_accuracy"],
        "view_erased_mean": core["controls"]["view_erased"]["mean_heldout_accuracy"],
        "leakage_used": len(policy["banned_identity_indices_used"]),
    }
    proofs = solver_polarity(values)
    gates = {
        **core["gates"],
        "direct_identity_leakage_excluded": policy["direct_identity_leakage_excluded"],
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
        "mode": "partial_mmm_projection_convergence_battery",
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
            "Five partial MMM-style projections over the finite v1 carrier converge to four shared loop objects "
            "above erased controls without using direct loop or engine identity fields."
        ),
        "claim_ceiling": CLAIM_CEILING,
        "allowed_claims": [
            "finite partial-view convergence over the v1 object-card carrier",
            "scratch object-card projection/anti-hash battery",
            "bounded MMM analogy for partial business/domain vocabularies",
            "negative controls for erased projection collapse",
        ],
        "disallowed_claims": [
            "live perception",
            "production object factory",
            "Axis0 admission",
            "FEP admission",
            "ontology writer admission",
            "MMM driver admission",
            "Lev mesh runtime integration",
            "remote peer graph mutation",
        ],
        "root_constraints_in_force": {
            "F01_finite_carrier": "four finite v1 object vectors projected through five finite view masks",
            "N01_order_sensitive_operation": "nominal projections preserve convergence while erased projections collapse to chance",
        },
        "finite_map": {
            "domain": "finite v1 64-slot object-card vectors with banned direct identity fields removed from nominal views",
            "codomain": "projection object cards with survivor hashes, per-view hashes, and anti-hashes",
            "map": "v1 object card -> partial MMM projections -> leave-one-view centroid measurement -> gated receipt",
        },
        "domain": {
            "object_count": core["nominal"]["object_count"],
            "view_count": core["nominal"]["view_count"],
            "view_names": list(VIEW_MASKS),
        },
        "codomain_or_output": {
            "readouts": ["heldout_view_accuracy", "projection_hashes", "anti_hashes", "solver_polarity"],
            "verdict_unit": "nominal partial-view convergence vs erased-control chance",
        },
        "carrier_realization": {
            "source": rel(V1_COMMON_PATH),
            "source_sha256": sha256_file(V1_COMMON_PATH),
            "parent_envelope": rel(V1_ENVELOPE),
            "parent_envelope_sha256": sha256_file(V1_ENVELOPE) if V1_ENVELOPE.exists() else None,
            "parent_claim_ceiling": V1_CLAIM_CEILING,
        },
        "dependency_receipts": {
            "v1_common": source_lock(V1_COMMON_PATH, "parent_finite_carrier"),
            "v1_envelope": source_lock(V1_ENVELOPE, "parent_three_engine_receipt"),
            "common": source_lock(COMMON_PATH, "shared_projection_battery"),
        },
        "projection_policy": policy,
        "identity_hazard_report": hazard,
        "blocked_consumers": [
            "QIT_engine_admission",
            "Axis0",
            "FEP",
            "Xi/Phi0",
            "physics",
            "Lev_mesh_runtime",
            "production_perception",
            "production_ontology",
            "MMM_driver",
            "mesh_visible_projection",
        ],
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
                "nominal_mean": result["core_measurement"]["nominal"]["mean_heldout_accuracy"],
                "bag_mean": result["core_measurement"]["controls"]["bag_erased"]["mean_heldout_accuracy"],
                "view_erased_mean": result["core_measurement"]["controls"]["view_erased"]["mean_heldout_accuracy"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
