#!/usr/bin/env python3
"""JAX/SMT leg for qit_full_type1_type2_64_live_v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import z3

from qit_full_type1_type2_64_live_v1_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULTS,
    ROOT,
    SIM_DIR,
    SIM_ID,
    build_core_measurement,
    numeric_feature_matrix,
    now_z,
    object_ids,
    rel,
    sha256_file,
    write_json,
)

jax.config.update("jax_enable_x64", True)

SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULTS / f"{SIM_ID}_jax_results.json"


def pairwise_distance_matrix(values: list[list[float]]) -> list[list[float]]:
    x = jnp.asarray(values, dtype=jnp.float64)

    def distances(row: jax.Array) -> jax.Array:
        return jnp.sqrt(jnp.sum((x - row) ** 2, axis=1))

    return jax.device_get(jax.vmap(distances)(x)).tolist()


def structural_proof(values: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    objects = z3.Int("objects")
    ordered_unique = z3.Int("ordered_unique")
    bag_unique = z3.Int("bag_unique")
    solver.add(objects == int(values["object_count"]))
    solver.add(ordered_unique == int(values["ordered_unique_count"]))
    solver.add(bag_unique == int(values["bag_unique_count"]))
    solver.add(z3.Not(z3.And(objects == 4, ordered_unique == objects, bag_unique < objects)))
    z3_verdict = str(solver.check()).lower()

    control = z3.Solver()
    cb = z3.Int("bag_unique_control")
    co = z3.Int("objects_control")
    control.add(cb == int(values["bag_unique_count"]))
    control.add(co == int(values["object_count"]))
    control.add(cb < co)
    z3_control = str(control.check()).lower()

    cv = cvc5.Solver()
    cv.setLogic("QF_LIA")
    int_sort = cv.getIntegerSort()
    cv_objects = cv.mkConst(int_sort, "objects")
    cv_ordered = cv.mkConst(int_sort, "ordered_unique")
    cv_bag = cv.mkConst(int_sort, "bag_unique")
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, cv_objects, cv.mkInteger(int(values["object_count"]))))
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, cv_ordered, cv.mkInteger(int(values["ordered_unique_count"]))))
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, cv_bag, cv.mkInteger(int(values["bag_unique_count"]))))
    cv_goal = cv.mkTerm(
        Kind.AND,
        cv.mkTerm(Kind.EQUAL, cv_objects, cv.mkInteger(4)),
        cv.mkTerm(Kind.EQUAL, cv_ordered, cv_objects),
        cv.mkTerm(Kind.LT, cv_bag, cv_objects),
    )
    cv.assertFormula(cv.mkTerm(Kind.NOT, cv_goal))
    cv_result = cv.checkSat()
    cvc5_verdict = "sat" if cv_result.isSat() else "unsat" if cv_result.isUnsat() else str(cv_result).lower()

    cv_control = cvc5.Solver()
    cv_control.setLogic("QF_LIA")
    cbi = cv_control.getIntegerSort()
    cb2 = cv_control.mkConst(cbi, "bag_unique_control")
    co2 = cv_control.mkConst(cbi, "objects_control")
    cv_control.assertFormula(cv_control.mkTerm(Kind.EQUAL, cb2, cv_control.mkInteger(int(values["bag_unique_count"]))))
    cv_control.assertFormula(cv_control.mkTerm(Kind.EQUAL, co2, cv_control.mkInteger(int(values["object_count"]))))
    cv_control.assertFormula(cv_control.mkTerm(Kind.LT, cb2, co2))
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
    labels, ordered_values = numeric_feature_matrix("ordered_full")
    _, bag_values = numeric_feature_matrix("bag_topology")
    ordered_distances = pairwise_distance_matrix(ordered_values)
    bag_distances = pairwise_distance_matrix(bag_values)
    ordered_offdiag = [
        ordered_distances[i][j]
        for i in range(len(labels))
        for j in range(len(labels))
        if i != j
    ]
    bag_offdiag = [bag_distances[i][j] for i in range(len(labels)) for j in range(len(labels)) if i != j]
    core = build_core_measurement()
    values = {
        "object_count": len(object_ids()),
        "ordered_unique_count": len({tuple(row) for row in ordered_values}),
        "bag_unique_count": len({tuple(row) for row in bag_values}),
    }
    proofs = structural_proof(values)
    all_pass = (
        min(ordered_offdiag) > 0.0
        and max(bag_offdiag) == 0.0
        and proofs["z3"]["verdict"] == "unsat"
        and proofs["cvc5"]["verdict"] == "unsat"
        and core["ordered_object_formation"]["ordered_accuracy"] == 1.0
    )
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
        "object_labels": labels,
        "object_count": len(labels),
        "ordered_distance_matrix": ordered_distances,
        "bag_distance_matrix": bag_distances,
        "ordered_min_offdiag_distance": float(min(ordered_offdiag)),
        "bag_max_offdiag_distance": float(max(bag_offdiag)),
        "ordered_object_accuracy": core["ordered_object_formation"]["ordered_accuracy"],
        "mean_entropy_drop_bits": core["ordered_object_formation"]["mean_entropy_drop_bits"],
        "solver_proofs": proofs,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "package_observables": {
            "z3": "UNSAT negation of ordered_unique=object_count and bag_unique<object_count gate",
            "cvc5": "independent UNSAT polarity for the same finite gate",
        },
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "supportive vectorized pairwise finite object distance readout"},
            "jax.numpy": {"tried": True, "used": True, "reason": "supportive numeric object feature matrix"},
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
