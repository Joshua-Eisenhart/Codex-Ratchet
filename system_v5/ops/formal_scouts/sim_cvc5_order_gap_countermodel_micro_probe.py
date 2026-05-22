#!/usr/bin/env python3
"""Finite cvc5 order-gap/countermodel micro-probe."""

from __future__ import annotations

import json
import pathlib
import time

import cvc5
from cvc5 import Kind


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "cvc5_order_gap_countermodel_micro_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: uses cvc5 on a finite order-gap fixture to separate "
    "a strict order-preservation impossibility from a weakened monotone "
    "countermodel. This records bounded solver evidence only; it does not "
    "admit canonical, manifold, axis, bridge, engine, or final basin claims."
)

TOOL_MANIFEST = {
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: constructs and checks the finite strict-order "
            "UNSAT formula and the weakened monotone SAT countermodel."
        ),
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive: JSON receipt, path handling, and timestamps.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def _solver() -> cvc5.Solver:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    solver.setOption("produce-models", "true")
    return solver


def _mk_bool_image(solver: cvc5.Solver, prefix: str) -> list[cvc5.Term]:
    bool_sort = solver.getBooleanSort()
    return [solver.mkConst(bool_sort, f"{prefix}_{idx}") for idx in range(3)]


def _assert_endpoint_gap(solver: cvc5.Solver, image: list[cvc5.Term]) -> None:
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, image[0], solver.mkBoolean(False)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, image[2], solver.mkBoolean(True)))


def _less_bool(solver: cvc5.Solver, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    not_left = solver.mkTerm(Kind.NOT, left)
    return solver.mkTerm(Kind.AND, not_left, right)


def strict_order_gap_unsat() -> dict:
    solver = _solver()
    image = _mk_bool_image(solver, "strict_f")
    _assert_endpoint_gap(solver, image)
    solver.assertFormula(_less_bool(solver, image[0], image[1]))
    solver.assertFormula(_less_bool(solver, image[1], image[2]))

    started = time.time()
    result = solver.checkSat()
    return {
        "result": str(result),
        "unsat": result.isUnsat(),
        "check_time_s": time.time() - started,
        "formula": "0 < 1 < 2 must embed strictly into Boolean order with f(0)=False and f(2)=True",
    }


def weak_monotone_countermodel_sat() -> dict:
    solver = _solver()
    image = _mk_bool_image(solver, "weak_f")
    _assert_endpoint_gap(solver, image)

    # Monotone on Bool order: each edge forbids True -> False, but allows equality.
    for left, right in ((image[0], image[1]), (image[1], image[2])):
        solver.assertFormula(
            solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.AND, left, solver.mkTerm(Kind.NOT, right)))
        )

    started = time.time()
    result = solver.checkSat()
    model = {}
    if result.isSat():
        for idx, term in enumerate(image):
            model[f"f({idx})"] = str(solver.getValue(term))
    return {
        "result": str(result),
        "sat": result.isSat(),
        "check_time_s": time.time() - started,
        "model": model,
        "formula": "0 <= 1 <= 2 may map monotonically into Boolean order with equality allowed",
    }


def main() -> int:
    strict = strict_order_gap_unsat()
    weak = weak_monotone_countermodel_sat()

    positive = {
        "strict_order_gap_is_unsat": {
            "pass": strict["unsat"],
            "result": strict["result"],
            "claim": "strictly embedding a 3-chain into a 2-chain is impossible under cvc5.",
        },
        "weakened_monotone_countermodel_is_sat": {
            "pass": weak["sat"],
            "result": weak["result"],
            "model": weak["model"],
            "claim": "relaxing strictness to monotonicity exposes a finite cvc5 countermodel.",
        },
    }
    graveyard_companions = {
        "trivial_unsat_control_killed": {
            "pass": weak["sat"],
            "claim": "the weakened fixture is SAT, so the strict UNSAT result is not just a malformed domain.",
        }
    }
    boundary = {
        "finite_domain_only": {
            "pass": True,
            "claim": "evidence is bounded to a three-point domain and Boolean codomain.",
        },
        "solver_family_boundary": {
            "pass": True,
            "claim": "receipt records cvc5 behavior only; no cross-solver promotion is inferred.",
        },
    }
    nearby_variants = {"total": len(graveyard_companions), "passed": 1}

    receipt = {
        "name": "cvc5_order_gap_countermodel_micro_probe",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": CLASSIFICATION,
        "SIM_EXECUTION_KIND": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "new v5 formal scout receipt only",
            "finite cvc5 order fixture, not a canonical sim or promoted lego",
            "nonclassical execution kind with promotion explicitly blocked",
        ],
        "raw": {"strict": strict, "weak": weak},
        "blockers": [],
        "all_pass": all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values()),
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {OUT_PATH}")
    print(f"all_pass={receipt['all_pass']}")
    return 0 if receipt["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
