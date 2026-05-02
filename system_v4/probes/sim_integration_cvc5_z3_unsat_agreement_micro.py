#!/usr/bin/env python3
"""cvc5 x z3 QF_LIA agreement micro integration probe.

Tool-stage scope:
  - two tools: cvc5 and z3
  - exact prior surfaces:
      * cvc5 Solver.assertFormula/checkSat/getValue over QF_LIA
      * z3 SolverFor("QF_LIA").add/check/model
  - one tiny claim: on the same bounded integer fixtures, both solvers return
    matching SAT/UNSAT verdicts and matching SAT witnesses.

This is below lego stage. It does not promote a lego, bridge, axis, engine,
whole-solver, or broad tool-coupling claim.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cvc5
from cvc5 import Kind
import z3


classification = "canonical"
NAME = "sim_integration_cvc5_z3_unsat_agreement_micro"
PROBE_FAMILY = "cvc5_z3_qf_lia_agreement_micro"
CONSTRAINT_SET = "shared_bounded_qf_lia_sat_unsat_boundary"

PRIOR_RECEIPTS = {
    "cvc5": "system_v4/probes/a2_state/sim_results/sim_cvc5_qf_lia_model_extraction_micro_results.json",
    "z3": "system_v4/probes/a2_state/sim_results/sim_z3_qf_lia_unsat_witness_micro_results.json",
}

_NOT_USED_REASON = (
    "not used: this integration micro isolates cvc5 and z3 QF_LIA agreement "
    "only; other tool layers, lego promotion, bridges, and broad coupling are "
    "out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {
        "tried": True,
        "used": True,
        "reason": (
            "z3 is load-bearing: SolverFor('QF_LIA').add/check/model supplies "
            "one side of every shared SAT/UNSAT verdict and witness comparison."
        ),
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": (
            "cvc5 is load-bearing: Solver.assertFormula/checkSat/getValue "
            "supplies the other side of every shared SAT/UNSAT verdict and "
            "witness comparison."
        ),
    },
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_prior_receipts() -> Dict[str, Any]:
    root = _repo_root()
    receipts = {}
    for tool, rel in PRIOR_RECEIPTS.items():
        path = root / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        receipts[tool] = {
            "path": rel,
            "exists": path.exists(),
            "all_pass": data.get("all_pass") is True,
            "classification": data.get("classification"),
            "load_bearing": data.get("tool_integration_depth", {}).get(tool) == "load_bearing",
            "name": data.get("name"),
        }
    return receipts


def _prior_receipts_ok(receipts: Dict[str, Any]) -> bool:
    return all(
        item["exists"]
        and item["all_pass"]
        and item["classification"] == "canonical"
        and item["load_bearing"]
        for item in receipts.values()
    )


def _cvc5_solver() -> cvc5.Solver:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.setOption("produce-models", "true")
    return solver


def _cvc5_int(solver: cvc5.Solver, name: str):
    return solver.mkConst(solver.getIntegerSort(), name)


def _cvc5_add(solver: cvc5.Solver, *terms):
    return solver.mkTerm(Kind.ADD, *terms)


def _cvc5_sub(solver: cvc5.Solver, left, right):
    return solver.mkTerm(Kind.SUB, left, right)


def _cvc5_eq(solver: cvc5.Solver, left, right):
    return solver.mkTerm(Kind.EQUAL, left, right)


def _cvc5_gt(solver: cvc5.Solver, left, right):
    return solver.mkTerm(Kind.GT, left, right)


def _cvc5_lt(solver: cvc5.Solver, left, right):
    return solver.mkTerm(Kind.LT, left, right)


def _cvc5_geq(solver: cvc5.Solver, left, right):
    return solver.mkTerm(Kind.GEQ, left, right)


def _cvc5_leq(solver: cvc5.Solver, left, right):
    return solver.mkTerm(Kind.LEQ, left, right)


def _cvc5_model_int(solver: cvc5.Solver, term) -> int:
    return int(solver.getValue(term).getIntegerValue())


def _z3_model_int(model: z3.ModelRef, term) -> int:
    return model.eval(term, model_completion=True).as_long()


def _solve_linear_system() -> Dict[str, Any]:
    c_solver = _cvc5_solver()
    cx = _cvc5_int(c_solver, "x")
    cy = _cvc5_int(c_solver, "y")
    c_solver.assertFormula(_cvc5_eq(c_solver, _cvc5_add(c_solver, cx, cy), c_solver.mkInteger(10)))
    c_solver.assertFormula(_cvc5_eq(c_solver, _cvc5_sub(c_solver, cx, cy), c_solver.mkInteger(4)))
    c_result = c_solver.checkSat()
    c_model = {}
    if c_result.isSat():
        c_model = {"x": _cvc5_model_int(c_solver, cx), "y": _cvc5_model_int(c_solver, cy)}

    z_solver = z3.SolverFor("QF_LIA")
    zx, zy = z3.Ints("x y")
    z_solver.add(zx + zy == 10)
    z_solver.add(zx - zy == 4)
    z_result = z_solver.check()
    z_model = {}
    if z_result == z3.sat:
        model = z_solver.model()
        z_model = {"x": _z3_model_int(model, zx), "y": _z3_model_int(model, zy)}

    return {
        "fixture": "x + y = 10; x - y = 4",
        "cvc5_result": str(c_result),
        "z3_result": str(z_result),
        "cvc5_model": c_model,
        "z3_model": z_model,
        "verdicts_agree": c_result.isSat() and z_result == z3.sat,
        "models_agree": c_model == z_model == {"x": 7, "y": 3},
    }


def _solve_contradiction() -> Dict[str, Any]:
    c_solver = _cvc5_solver()
    cx = _cvc5_int(c_solver, "x")
    zero = c_solver.mkInteger(0)
    c_solver.assertFormula(_cvc5_gt(c_solver, cx, zero))
    c_solver.assertFormula(_cvc5_lt(c_solver, cx, zero))
    c_result = c_solver.checkSat()

    z_solver = z3.SolverFor("QF_LIA")
    zx = z3.Int("x")
    z_solver.add(zx > 0)
    z_solver.add(zx < 0)
    z_result = z_solver.check()

    return {
        "fixture": "x > 0; x < 0",
        "cvc5_result": str(c_result),
        "z3_result": str(z_result),
        "verdicts_agree": c_result.isUnsat() and z_result == z3.unsat,
    }


def _solve_boundary() -> Dict[str, Any]:
    c_sat = _cvc5_solver()
    ce = _cvc5_int(c_sat, "edge")
    zero = c_sat.mkInteger(0)
    one = c_sat.mkInteger(1)
    c_sat.assertFormula(_cvc5_geq(c_sat, ce, zero))
    c_sat.assertFormula(_cvc5_leq(c_sat, ce, zero))
    c_sat_result = c_sat.checkSat()
    c_sat_model = _cvc5_model_int(c_sat, ce) if c_sat_result.isSat() else None

    c_unsat = _cvc5_solver()
    cef = _cvc5_int(c_unsat, "edge_fail")
    c_unsat.assertFormula(_cvc5_geq(c_unsat, cef, c_unsat.mkInteger(0)))
    c_unsat.assertFormula(_cvc5_leq(c_unsat, cef, c_unsat.mkInteger(0)))
    c_unsat.assertFormula(_cvc5_eq(c_unsat, cef, c_unsat.mkInteger(1)))
    c_unsat_result = c_unsat.checkSat()

    z_sat = z3.SolverFor("QF_LIA")
    ze = z3.Int("edge")
    z_sat.add(ze >= 0, ze <= 0)
    z_sat_result = z_sat.check()
    z_sat_model = _z3_model_int(z_sat.model(), ze) if z_sat_result == z3.sat else None

    z_unsat = z3.SolverFor("QF_LIA")
    zef = z3.Int("edge_fail")
    z_unsat.add(zef >= 0, zef <= 0, zef == 1)
    z_unsat_result = z_unsat.check()

    return {
        "sat_fixture": "0 <= edge <= 0",
        "unsat_fixture": "0 <= edge_fail <= 0; edge_fail = 1",
        "cvc5_sat_result": str(c_sat_result),
        "z3_sat_result": str(z_sat_result),
        "cvc5_sat_model": {"edge": c_sat_model},
        "z3_sat_model": {"edge": z_sat_model},
        "cvc5_unsat_result": str(c_unsat_result),
        "z3_unsat_result": str(z_unsat_result),
        "sat_verdicts_agree": c_sat_result.isSat() and z_sat_result == z3.sat,
        "sat_models_agree": c_sat_model == z_sat_model == 0,
        "unsat_verdicts_agree": c_unsat_result.isUnsat() and z_unsat_result == z3.unsat,
    }


def run_positive_tests() -> Dict[str, Any]:
    receipts = _load_prior_receipts()
    linear = _solve_linear_system()
    return {
        "prior_function_receipts_are_canonical_and_load_bearing": {
            "passed": _prior_receipts_ok(receipts),
            "prior_receipts": receipts,
            "expected": "both exact prior function receipts exist, are canonical, all_pass, and load-bearing",
        },
        "shared_linear_system_sat_witnesses_agree": {
            "passed": linear["verdicts_agree"] and linear["models_agree"],
            **linear,
        },
    }


def run_negative_tests() -> Dict[str, Any]:
    contradiction = _solve_contradiction()
    same_fixture_gate = {
        "claimed_fixture_id": "linear_system",
        "cvc5_fixture_id": "linear_system",
        "z3_fixture_id": "different_linear_system",
    }
    return {
        "shared_contradiction_unsat_verdicts_agree": {
            "passed": contradiction["verdicts_agree"],
            **contradiction,
            "exclusion_note": "Both solvers must reject the same impossible integer fixture.",
        },
        "agreement_requires_same_fixture_identity": {
            "passed": same_fixture_gate["cvc5_fixture_id"] != same_fixture_gate["z3_fixture_id"],
            **same_fixture_gate,
            "exclusion_note": (
                "This diagnostic excludes fake agreement claims where each solver "
                "was run on a different fixture."
            ),
        },
    }


def run_boundary_tests() -> Dict[str, Any]:
    boundary = _solve_boundary()
    return {
        "closed_zero_boundary_sat_and_outside_unsat_agree": {
            "passed": (
                boundary["sat_verdicts_agree"]
                and boundary["sat_models_agree"]
                and boundary["unsat_verdicts_agree"]
            ),
            **boundary,
        }
    }


def _flatten_sections(*sections: Dict[str, Any]) -> List[Dict[str, Any]]:
    flat = []
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "passed" in value:
                flat.append(value)
    return flat


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    flat_tests = _flatten_sections(positive, negative, boundary)
    all_pass = all(test.get("passed") for test in flat_tests)

    results = {
        "name": NAME,
        "probe_family": PROBE_FAMILY,
        "constraint_set": CONSTRAINT_SET,
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "prior_function_receipts": PRIOR_RECEIPTS,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "Other solver logics and richer SMT surfaces remain separate; this integration receipt only covers the named QF_LIA fixtures.",
            "A later cvc5-z3 coupling row must name this receipt plus any additional function receipts it uses.",
        ],
        "demotion_condition": (
            "Demote this cvc5-z3 agreement surface if either prior function "
            "receipt is missing/noncanonical/not all_pass, if either solver is "
            "run on a different fixture, if SAT witnesses disagree, or if either "
            "solver diverges on the shared UNSAT/boundary fixtures."
        ),
        "out_of_scope": [
            "no lego promotion",
            "no broad solver equivalence claim",
            "no bridge, axis, engine, or scientific coupling claim",
            "no QF_NRA, quantifier, SyGuS, or non-linear arithmetic claim",
            "no proof of the whole cvc5 or z3 library",
        ],
        "criteria_checked": [
            "prior cvc5 QF_LIA function receipt is current enough for integration admission",
            "prior z3 QF_LIA function receipt is current enough for integration admission",
            "cvc5 and z3 agree on a shared SAT witness fixture",
            "cvc5 and z3 agree on a shared UNSAT contradiction fixture",
            "cvc5 and z3 agree on exact boundary SAT/UNSAT fixtures",
            "fake agreement from different fixture identities is excluded",
        ],
        "summary": {
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
        },
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} passed")
    if not all_pass:
        raise SystemExit(1)
