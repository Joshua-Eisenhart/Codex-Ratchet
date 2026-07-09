#!/usr/bin/env python3
"""JAX/SMT leg for qit_projection_battery_v0."""

from __future__ import annotations

import json
from typing import Any

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import z3

from qit_projection_battery_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULTS,
    SIM_DIR,
    SIM_ID,
    VIEW_MASKS,
    build_core_measurement,
    now_z,
    object_ids,
    projection_records,
    rel,
    sha256_file,
    write_json,
)

jax.config.update("jax_enable_x64", True)

SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULTS / f"{SIM_ID}_jax_results.json"


def jax_projection_readout(control: str | None = None) -> dict[str, Any]:
    labels = object_ids()
    views = list(VIEW_MASKS)
    records = projection_records(control=control)
    x = jnp.asarray([row["vector"] for row in records], dtype=jnp.float64)
    y = jnp.asarray([labels.index(row["object_id"]) for row in records], dtype=jnp.int32)
    view_id = jnp.asarray([views.index(row["view"]) for row in records], dtype=jnp.int32)
    per_view = []
    for heldout_idx, heldout_view in enumerate(views):
        train_mask = view_id != heldout_idx
        test_mask = view_id == heldout_idx
        centroids = []
        for object_idx in range(len(labels)):
            mask = jnp.logical_and(train_mask, y == object_idx)
            weights = mask.astype(jnp.float64)
            denom = jnp.maximum(jnp.sum(weights), 1.0)
            centroids.append(jnp.sum(x * weights[:, None], axis=0) / denom)
        centroid_matrix = jnp.stack(centroids, axis=0)
        test_x = x[test_mask]
        test_y = y[test_mask]

        def distance_row(row: jax.Array) -> jax.Array:
            return jnp.sum((centroid_matrix - row) ** 2, axis=1)

        distances = jax.vmap(distance_row)(test_x)
        predictions = jnp.argmin(distances, axis=1)
        accuracy = jnp.mean((predictions == test_y).astype(jnp.float64))
        per_view.append(
            {
                "heldout_view": heldout_view,
                "accuracy": float(jax.device_get(accuracy)),
                "predictions": [int(x) for x in jax.device_get(predictions).tolist()],
                "labels": [int(x) for x in jax.device_get(test_y).tolist()],
                "distance_matrix": jax.device_get(distances).tolist(),
            }
        )
    mean_accuracy = sum(row["accuracy"] for row in per_view) / len(per_view)
    return {
        "control": control or "none",
        "object_count": len(labels),
        "view_count": len(views),
        "mean_heldout_accuracy": round(mean_accuracy, 12),
        "min_heldout_accuracy": round(min(row["accuracy"] for row in per_view), 12),
        "view_results": per_view,
    }


def structural_proof(values: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    objects = z3.Int("objects")
    views = z3.Int("views")
    nominal = z3.Real("nominal_mean")
    bag = z3.Real("bag_mean")
    erased = z3.Real("view_erased_mean")
    solver.add(objects == int(values["object_count"]))
    solver.add(views == int(values["view_count"]))
    solver.add(nominal == z3.RealVal(str(values["nominal_mean"])))
    solver.add(bag == z3.RealVal(str(values["bag_mean"])))
    solver.add(erased == z3.RealVal(str(values["view_erased_mean"])))
    gate = z3.And(
        objects == 4,
        views == 5,
        nominal >= z3.RealVal("0.85"),
        bag <= z3.RealVal("0.25"),
        erased <= z3.RealVal("0.25"),
        nominal - bag >= z3.RealVal("0.5"),
        nominal - erased >= z3.RealVal("0.5"),
    )
    solver.add(z3.Not(gate))
    z3_verdict = str(solver.check()).lower()

    control = z3.Solver()
    cb = z3.Real("bag_control")
    ce = z3.Real("erased_control")
    control.add(cb == z3.RealVal(str(values["bag_mean"])))
    control.add(ce == z3.RealVal(str(values["view_erased_mean"])))
    control.add(cb <= z3.RealVal("0.25"))
    control.add(ce <= z3.RealVal("0.25"))
    z3_control = str(control.check()).lower()

    cv = cvc5.Solver()
    cv.setLogic("QF_LIRA")
    int_sort = cv.getIntegerSort()
    real_sort = cv.getRealSort()
    cv_objects = cv.mkConst(int_sort, "objects")
    cv_views = cv.mkConst(int_sort, "views")
    cv_nominal = cv.mkConst(real_sort, "nominal_mean")
    cv_bag = cv.mkConst(real_sort, "bag_mean")
    cv_erased = cv.mkConst(real_sort, "view_erased_mean")
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, cv_objects, cv.mkInteger(int(values["object_count"]))))
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, cv_views, cv.mkInteger(int(values["view_count"]))))
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, cv_nominal, cv.mkReal(str(values["nominal_mean"]))))
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, cv_bag, cv.mkReal(str(values["bag_mean"]))))
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, cv_erased, cv.mkReal(str(values["view_erased_mean"]))))
    cv_goal = cv.mkTerm(
        Kind.AND,
        cv.mkTerm(Kind.EQUAL, cv_objects, cv.mkInteger(4)),
        cv.mkTerm(Kind.EQUAL, cv_views, cv.mkInteger(5)),
        cv.mkTerm(Kind.GEQ, cv_nominal, cv.mkReal("0.85")),
        cv.mkTerm(Kind.LEQ, cv_bag, cv.mkReal("0.25")),
        cv.mkTerm(Kind.LEQ, cv_erased, cv.mkReal("0.25")),
        cv.mkTerm(Kind.GEQ, cv.mkTerm(Kind.SUB, cv_nominal, cv_bag), cv.mkReal("0.5")),
        cv.mkTerm(Kind.GEQ, cv.mkTerm(Kind.SUB, cv_nominal, cv_erased), cv.mkReal("0.5")),
    )
    cv.assertFormula(cv.mkTerm(Kind.NOT, cv_goal))
    cv_result = cv.checkSat()
    cvc5_verdict = "sat" if cv_result.isSat() else "unsat" if cv_result.isUnsat() else str(cv_result).lower()

    cv_control = cvc5.Solver()
    cv_control.setLogic("QF_LRA")
    cr = cv_control.getRealSort()
    cv_bag_c = cv_control.mkConst(cr, "bag_control")
    cv_erased_c = cv_control.mkConst(cr, "erased_control")
    cv_control.assertFormula(cv_control.mkTerm(Kind.EQUAL, cv_bag_c, cv_control.mkReal(str(values["bag_mean"]))))
    cv_control.assertFormula(cv_control.mkTerm(Kind.EQUAL, cv_erased_c, cv_control.mkReal(str(values["view_erased_mean"]))))
    cv_control.assertFormula(cv_control.mkTerm(Kind.LEQ, cv_bag_c, cv_control.mkReal("0.25")))
    cv_control.assertFormula(cv_control.mkTerm(Kind.LEQ, cv_erased_c, cv_control.mkReal("0.25")))
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
    nominal = jax_projection_readout()
    bag = jax_projection_readout(control="bag_erased")
    view_erased = jax_projection_readout(control="view_erased")
    core = build_core_measurement()
    values = {
        "object_count": nominal["object_count"],
        "view_count": nominal["view_count"],
        "nominal_mean": nominal["mean_heldout_accuracy"],
        "bag_mean": bag["mean_heldout_accuracy"],
        "view_erased_mean": view_erased["mean_heldout_accuracy"],
    }
    proofs = structural_proof(values)
    all_pass = (
        nominal["mean_heldout_accuracy"] >= 0.85
        and bag["mean_heldout_accuracy"] <= 0.25
        and view_erased["mean_heldout_accuracy"] <= 0.25
        and core["all_pass"]
        and proofs["z3"]["verdict"] == "unsat"
        and proofs["cvc5"]["verdict"] == "unsat"
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
        "object_count": nominal["object_count"],
        "view_count": nominal["view_count"],
        "jax_projection_readouts": {
            "nominal": nominal,
            "bag_erased_control": bag,
            "view_erased_control": view_erased,
        },
        "solver_proofs": proofs,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "package_observables": {
            "z3": "UNSAT negation of nominal projection convergence gate with SAT erased controls",
            "cvc5": "independent cvc5 encoding agrees with z3 on projection battery polarity",
        },
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "supportive vectorized heldout-view centroid distance readout"},
            "jax.numpy": {"tried": True, "used": True, "reason": "supportive numeric projection matrices"},
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
    print(
        json.dumps(
            {
                "engine": "jax",
                "all_pass": result["all_pass"],
                "nominal_mean": result["jax_projection_readouts"]["nominal"]["mean_heldout_accuracy"],
                "bag_mean": result["jax_projection_readouts"]["bag_erased_control"]["mean_heldout_accuracy"],
                "out": rel(RESULT_PATH),
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
