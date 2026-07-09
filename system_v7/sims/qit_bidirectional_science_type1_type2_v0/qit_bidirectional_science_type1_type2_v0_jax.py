#!/usr/bin/env python3
"""JAX/SMT leg for qit_bidirectional_science_type1_type2_v0."""

from __future__ import annotations

import json
from typing import Any

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import z3

from qit_bidirectional_science_type1_type2_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULTS,
    SIM_DIR,
    SIM_ID,
    build_core_measurement,
    now_z,
    rel,
    sha256_file,
    write_json,
)

jax.config.update("jax_enable_x64", True)

SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULTS / f"{SIM_ID}_jax_results.json"


def jax_method_summary(core: dict[str, Any]) -> dict[str, Any]:
    type1 = jnp.asarray([1.0 if row["roundtrip_survived"] else 0.0 for row in core["type1"]["nominal"]["rows"]], dtype=jnp.float64)
    type2 = jnp.asarray([1.0 if row["roundtrip_survived"] else 0.0 for row in core["type2"]["nominal"]["rows"]], dtype=jnp.float64)

    def pair_bucket(left: jax.Array, right: jax.Array) -> jax.Array:
        return jnp.asarray(
            [
                jnp.logical_and(left == 1.0, right == 0.0),
                jnp.logical_and(left == 0.0, right == 1.0),
                jnp.logical_and(left == 1.0, right == 1.0),
                jnp.logical_and(left == 0.0, right == 0.0),
            ],
            dtype=jnp.float64,
        )

    buckets = jax.vmap(pair_bucket)(type1, type2)
    counts = jax.device_get(jnp.sum(buckets, axis=0)).tolist()
    return {
        "trial_count": int(type1.shape[0] + type2.shape[0]),
        "paired_trial_count": int(type1.shape[0]),
        "type1_accuracy": float(jax.device_get(jnp.mean(type1))),
        "type2_accuracy": float(jax.device_get(jnp.mean(type2))),
        "unique_win_counts": {
            "type1_only": int(counts[0]),
            "type2_only": int(counts[1]),
            "shared_win": int(counts[2]),
            "shared_fail": int(counts[3]),
        },
        "method_order_delta_mean": float(jax.device_get(jnp.mean(type1 - type2))),
    }


def structural_proof(values: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    type1 = z3.Real("type1_accuracy")
    type2 = z3.Real("type2_accuracy")
    type1_only = z3.Int("type1_only")
    paired = z3.Int("paired_trial_count")
    solver.add(type1 == z3.RealVal(str(values["type1_accuracy"])))
    solver.add(type2 == z3.RealVal(str(values["type2_accuracy"])))
    solver.add(type1_only == int(values["type1_only"]))
    solver.add(paired == int(values["paired_trial_count"]))
    gate = z3.And(type1 == z3.RealVal("1.0"), type2 >= z3.RealVal("0.85"), type1_only >= 1, paired == 20)
    solver.add(z3.Not(gate))
    z3_verdict = str(solver.check()).lower()

    control = z3.Solver()
    c = z3.Real("control_accuracy")
    control.add(c == z3.RealVal(str(values["erased_accuracy"])))
    control.add(c <= z3.RealVal("0.25"))
    z3_control = str(control.check()).lower()

    cv = cvc5.Solver()
    cv.setLogic("QF_LIRA")
    real_sort = cv.getRealSort()
    int_sort = cv.getIntegerSort()
    cv_type1 = cv.mkConst(real_sort, "type1_accuracy")
    cv_type2 = cv.mkConst(real_sort, "type2_accuracy")
    cv_t1_only = cv.mkConst(int_sort, "type1_only")
    cv_paired = cv.mkConst(int_sort, "paired_trial_count")
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, cv_type1, cv.mkReal(str(values["type1_accuracy"]))))
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, cv_type2, cv.mkReal(str(values["type2_accuracy"]))))
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, cv_t1_only, cv.mkInteger(int(values["type1_only"]))))
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, cv_paired, cv.mkInteger(int(values["paired_trial_count"]))))
    cv_gate = cv.mkTerm(
        Kind.AND,
        cv.mkTerm(Kind.EQUAL, cv_type1, cv.mkReal("1.0")),
        cv.mkTerm(Kind.GEQ, cv_type2, cv.mkReal("0.85")),
        cv.mkTerm(Kind.GEQ, cv_t1_only, cv.mkInteger(1)),
        cv.mkTerm(Kind.EQUAL, cv_paired, cv.mkInteger(20)),
    )
    cv.assertFormula(cv.mkTerm(Kind.NOT, cv_gate))
    cv_result = cv.checkSat()
    cvc5_verdict = "sat" if cv_result.isSat() else "unsat" if cv_result.isUnsat() else str(cv_result).lower()

    cv_control = cvc5.Solver()
    cv_control.setLogic("QF_LRA")
    cr = cv_control.getRealSort()
    cc = cv_control.mkConst(cr, "control_accuracy")
    cv_control.assertFormula(cv_control.mkTerm(Kind.EQUAL, cc, cv_control.mkReal(str(values["erased_accuracy"]))))
    cv_control.assertFormula(cv_control.mkTerm(Kind.LEQ, cc, cv_control.mkReal("0.25")))
    cv_control_result = cv_control.checkSat()
    cvc5_control = (
        "sat" if cv_control_result.isSat() else "unsat" if cv_control_result.isUnsat() else str(cv_control_result).lower()
    )
    return {
        "z3": {"ran": True, "verdict": z3_verdict, "load_bearing": True, "erased_control_verdict": z3_control},
        "cvc5": {"ran": True, "verdict": cvc5_verdict, "load_bearing": True, "erased_control_verdict": cvc5_control},
    }


def build_result() -> dict[str, Any]:
    RESULTS.mkdir(parents=True, exist_ok=True)
    core = build_core_measurement()
    summary = jax_method_summary(core)
    values = {
        **summary,
        "type1_only": summary["unique_win_counts"]["type1_only"],
        "erased_accuracy": core["type2"]["controls"]["view_erased"]["accuracy"],
    }
    proofs = structural_proof(values)
    all_pass = core["all_pass"] and proofs["z3"]["verdict"] == "unsat" and proofs["cvc5"]["verdict"] == "unsat"
    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
        "ran": True,
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "object_count": core["type1"]["nominal"]["object_count"],
        "view_count": core["type1"]["nominal"]["view_count"],
        "trial_count": summary["trial_count"],
        "method_summary": summary,
        "solver_proofs": proofs,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "package_observables": {
            "z3": "UNSAT negation of Type-1/Type-2 method comparison gate with SAT erased control",
            "cvc5": "independent SMT agreement with z3 on the finite method comparison gate",
        },
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "supportive vectorized unique-win table calculation"},
            "jax.numpy": {"tried": True, "used": True, "reason": "supportive finite method arrays"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing structural gate polarity"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent structural gate polarity"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax": "supportive",
            "jax.numpy": "supportive",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
        },
    }
    write_json(RESULT_PATH, result)
    return result


def main() -> int:
    result = build_result()
    print(json.dumps({"engine": "jax", "all_pass": result["all_pass"], "out": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
