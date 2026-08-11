"""Independent finite deciders for the 91-row CB Light selection problem."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _expected_assignment(
    facts_by_tool: Mapping[str, Mapping[str, bool]], required: Sequence[str]
) -> dict[str, bool]:
    return {
        name: all(facts.get(constraint) is True for constraint in required)
        for name, facts in sorted(facts_by_tool.items())
    }


def _z3_assignment(
    facts_by_tool: Mapping[str, Mapping[str, bool]], required: Sequence[str]
) -> dict[str, Any]:
    import z3

    solver = z3.Solver()
    variables = {name: z3.Bool(f"select::{name}") for name in facts_by_tool}
    for name, facts in facts_by_tool.items():
        conjunction = z3.And(*[z3.BoolVal(facts[key]) for key in required])
        solver.add(variables[name] == conjunction)
    status = solver.check()
    if status != z3.sat:
        return {"status": str(status).upper(), "assignment": {}, "unique": False}
    model = solver.model()
    assignment = {
        name: z3.is_true(model.eval(variable, model_completion=True))
        for name, variable in variables.items()
    }
    solver.push()
    solver.add(
        z3.Or(
            *[
                variable != z3.BoolVal(assignment[name])
                for name, variable in variables.items()
            ]
        )
    )
    unique = solver.check() == z3.unsat
    solver.pop()
    return {"status": "SAT", "assignment": assignment, "unique": unique}


def _cvc5_assignment(
    facts_by_tool: Mapping[str, Mapping[str, bool]], required: Sequence[str]
) -> dict[str, Any]:
    import cvc5
    from cvc5 import Kind

    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    solver.setOption("produce-models", "true")
    variables = {
        name: solver.mkConst(solver.getBooleanSort(), f"select::{name}")
        for name in facts_by_tool
    }
    for name, facts in facts_by_tool.items():
        terms = [solver.mkBoolean(bool(facts[key])) for key in required]
        conjunction = terms[0] if len(terms) == 1 else solver.mkTerm(Kind.AND, *terms)
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, variables[name], conjunction))
    status = solver.checkSat()
    if not status.isSat():
        return {"status": str(status).upper(), "assignment": {}, "unique": False}
    assignment = {
        name: bool(solver.getValue(variable).getBooleanValue())
        for name, variable in variables.items()
    }
    solver.push()
    alternatives = [
        (
            solver.mkTerm(Kind.NOT, variable)
            if assignment[name]
            else variable
        )
        for name, variable in variables.items()
    ]
    solver.assertFormula(
        alternatives[0]
        if len(alternatives) == 1
        else solver.mkTerm(Kind.OR, *alternatives)
    )
    unique = solver.checkSat().isUnsat()
    solver.pop()
    return {"status": "SAT", "assignment": assignment, "unique": unique}


def solve_selection(
    facts_by_tool: Mapping[str, Mapping[str, bool]], required: Sequence[str]
) -> dict[str, Any]:
    if not facts_by_tool or not required:
        raise ValueError("selection domain and required constraints must be nonempty")
    expected_names = set(required)
    for name, facts in facts_by_tool.items():
        if set(facts) != expected_names:
            raise ValueError(f"fact set mismatch for {name}")
        if any(type(value) is not bool for value in facts.values()):
            raise ValueError(f"non-Boolean fact for {name}")

    enumeration = _expected_assignment(facts_by_tool, required)
    results: dict[str, Any] = {
        "enumeration": {
            "status": "SAT",
            "assignment": enumeration,
            "unique": True,
        }
    }
    errors: dict[str, str] = {}
    for name, decider in (("z3", _z3_assignment), ("cvc5", _cvc5_assignment)):
        try:
            results[name] = decider(facts_by_tool, required)
        except Exception as exc:
            errors[name] = f"{type(exc).__name__}: {str(exc)[:300]}"
            results[name] = {"status": "ERROR", "assignment": {}, "unique": False}

    assignments = [results[name]["assignment"] for name in ("z3", "cvc5", "enumeration")]
    agree = not errors and assignments[0] == assignments[1] == assignments[2]
    all_unique = all(results[name].get("unique") is True for name in results)
    formula = {
        "domain": sorted(facts_by_tool),
        "required": list(required),
        "facts": {name: dict(sorted(facts.items())) for name, facts in sorted(facts_by_tool.items())},
        "law": "select(tool) iff every required measured fact is true",
    }
    return {
        "schema": "constraintbox.cb-light-finite-selection.v1",
        "formula_sha256": hashlib.sha256(_canonical(formula)).hexdigest(),
        "domain_size": len(facts_by_tool),
        "required_constraint_count": len(required),
        "deciders": results,
        "execution_errors": errors,
        "agree": agree,
        "unique_assignment": bool(agree and all_unique),
        "assignment": enumeration if agree else {},
    }
