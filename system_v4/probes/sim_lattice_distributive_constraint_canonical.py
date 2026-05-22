#!/usr/bin/env python3
"""
Lattice Distributivity Constraint Canonical Sim

Bounded finite-lattice cvc5 probe for the distributive law:
  a meet (b join c) = (a meet b) join (a meet c)

Positive rows ask cvc5 for a counterexample in distributive finite
lattices and require UNSAT. Negative rows ask cvc5 for counterexamples in
the non-distributive diamond lattice M3 and require SAT.
"""

from __future__ import annotations

import json
import os
from typing import Any

import sympy as sp

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not required for finite order-theory constraint proof"},
    "pyg": {"tried": False, "used": False, "reason": "not required for finite order-theory constraint proof"},
    "z3": {"tried": False, "used": False, "reason": "cvc5 is the selected SMT surface for this bounded finite-lattice packet"},
    "cvc5": {"tried": False, "used": False, "reason": "not installed"},
    "sympy": {"tried": True, "used": False, "reason": "supportive symbolic Boolean simplification is attempted in the boundary row"},
    "clifford": {"tried": False, "used": False, "reason": "finite meet/join table equality has no geometric product, rotor, spinor, or Clifford algebra operation to evaluate"},
    "geomstats": {"tried": False, "used": False, "reason": "the claim is a finite order-table identity, not a metric, geodesic, curvature, or manifold computation"},
    "e3nn": {"tried": False, "used": False, "reason": "no Euclidean or O(3)-equivariant tensor field appears in this bounded lattice-law SAT/UNSAT packet"},
    "rustworkx": {"tried": False, "used": False, "reason": "the witness is decided by explicit finite meet/join operation tables, not by graph traversal or DAG routing"},
    "xgi": {"tried": False, "used": False, "reason": "no hyperedge or multiway incidence structure can change the bounded distributive-law equality query"},
    "toponetx": {"tried": False, "used": False, "reason": "the packet has no cell-complex boundary, adjacency, or homology computation for TopoNetX to certify"},
    "gudhi": {"tried": False, "used": False, "reason": "the packet has no filtration, simplex complex, persistence interval, or TDA invariant to compute"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": "load_bearing",
    "sympy": "supportive",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

try:
    import cvc5

    TOOL_MANIFEST["cvc5"]["tried"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "available; used only if finite-lattice SAT/UNSAT outcomes are consumed"
except ImportError:  # pragma: no cover - exercised only on missing optional dependency
    cvc5 = None


def result_is_sat(result: Any) -> bool:
    return str(result) == "sat" or getattr(result, "isSat", lambda: False)()


def result_is_unsat(result: Any) -> bool:
    return str(result) == "unsat" or getattr(result, "isUnsat", lambda: False)()


def finite_op_term(solver: Any, x: Any, y: Any, table: dict[tuple[int, int], int]) -> Any:
    term = None
    for (left, right), value in reversed(list(table.items())):
        condition = solver.mkTerm(
            cvc5.Kind.AND,
            solver.mkTerm(cvc5.Kind.EQUAL, x, solver.mkInteger(left)),
            solver.mkTerm(cvc5.Kind.EQUAL, y, solver.mkInteger(right)),
        )
        value_term = solver.mkInteger(value)
        term = value_term if term is None else solver.mkTerm(cvc5.Kind.ITE, condition, value_term, term)
    return term


def finite_domain_constraint(solver: Any, var: Any, elements: list[int]) -> Any:
    equalities = [
        solver.mkTerm(cvc5.Kind.EQUAL, var, solver.mkInteger(element))
        for element in elements
    ]
    if len(equalities) == 1:
        return equalities[0]
    return solver.mkTerm(cvc5.Kind.OR, *equalities)


def distributivity_counterexample_query(
    elements: list[int],
    meet_table: dict[tuple[int, int], int],
    join_table: dict[tuple[int, int], int],
    fixed: tuple[int, int, int] | None = None,
) -> Any:
    solver = cvc5.Solver()
    a = solver.mkConst(solver.getIntegerSort(), "a")
    b = solver.mkConst(solver.getIntegerSort(), "b")
    c = solver.mkConst(solver.getIntegerSort(), "c")

    if fixed is None:
        for var in (a, b, c):
            solver.assertFormula(finite_domain_constraint(solver, var, elements))
    else:
        for var, value in zip((a, b, c), fixed):
            solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, var, solver.mkInteger(value)))

    b_join_c = finite_op_term(solver, b, c, join_table)
    lhs = finite_op_term(solver, a, b_join_c, meet_table)
    a_meet_b = finite_op_term(solver, a, b, meet_table)
    a_meet_c = finite_op_term(solver, a, c, meet_table)
    rhs = finite_op_term(solver, a_meet_b, a_meet_c, join_table)

    solver.assertFormula(
        solver.mkTerm(cvc5.Kind.NOT, solver.mkTerm(cvc5.Kind.EQUAL, lhs, rhs))
    )
    return solver.checkSat()


def chain_tables(size: int) -> tuple[list[int], dict[tuple[int, int], int], dict[tuple[int, int], int]]:
    elements = list(range(size))
    meet = {(i, j): min(i, j) for i in elements for j in elements}
    join = {(i, j): max(i, j) for i in elements for j in elements}
    return elements, meet, join


def boolean_2_atom_tables() -> tuple[list[int], dict[tuple[int, int], int], dict[tuple[int, int], int]]:
    elements = [0, 1, 2, 3]
    meet = {(i, j): i & j for i in elements for j in elements}
    join = {(i, j): i | j for i in elements for j in elements}
    return elements, meet, join


def diamond_m3_tables() -> tuple[list[int], dict[tuple[int, int], int], dict[tuple[int, int], int]]:
    # 0 is bottom, 4 is top, and 1/2/3 are incomparable atoms.
    elements = [0, 1, 2, 3, 4]

    def meet_value(left: int, right: int) -> int:
        if left == right:
            return left
        if left == 0 or right == 0:
            return 0
        if left == 4:
            return right
        if right == 4:
            return left
        return 0

    def join_value(left: int, right: int) -> int:
        if left == right:
            return left
        if left == 4 or right == 4:
            return 4
        if left == 0:
            return right
        if right == 0:
            return left
        return 4

    meet = {(i, j): meet_value(i, j) for i in elements for j in elements}
    join = {(i, j): join_value(i, j) for i in elements for j in elements}
    return elements, meet, join


def cvc5_unavailable_row(name: str) -> dict[str, Any]:
    return {
        "pass": False,
        "solver_result": "not_run",
        "detail": f"{name} requires cvc5, but cvc5 is unavailable.",
    }


def run_positive_tests() -> dict[str, dict[str, Any]]:
    if cvc5 is None:
        return {
            "boolean_lattice_no_counterexample": cvc5_unavailable_row("boolean_lattice_no_counterexample"),
            "chain_lattice_no_counterexample": cvc5_unavailable_row("chain_lattice_no_counterexample"),
        }

    boolean_elements, boolean_meet, boolean_join = boolean_2_atom_tables()
    boolean_result = distributivity_counterexample_query(boolean_elements, boolean_meet, boolean_join)

    chain_elements, chain_meet, chain_join = chain_tables(4)
    chain_result = distributivity_counterexample_query(chain_elements, chain_meet, chain_join)

    return {
        "boolean_lattice_no_counterexample": {
            "pass": result_is_unsat(boolean_result),
            "solver_result": str(boolean_result),
            "detail": "cvc5 finds no bounded counterexample to distributivity in the four-element Boolean lattice.",
            "expectation": "UNSAT for exists a,b,c with distributive-law inequality",
        },
        "chain_lattice_no_counterexample": {
            "pass": result_is_unsat(chain_result),
            "solver_result": str(chain_result),
            "detail": "cvc5 finds no bounded counterexample to distributivity in a four-element chain lattice.",
            "expectation": "UNSAT for exists a,b,c with distributive-law inequality",
        },
    }


def run_negative_tests() -> dict[str, dict[str, Any]]:
    if cvc5 is None:
        return {
            "m3_counterexample_exists": cvc5_unavailable_row("m3_counterexample_exists"),
            "m3_explicit_counterexample": cvc5_unavailable_row("m3_explicit_counterexample"),
        }

    m3_elements, m3_meet, m3_join = diamond_m3_tables()
    exists_result = distributivity_counterexample_query(m3_elements, m3_meet, m3_join)
    explicit_result = distributivity_counterexample_query(m3_elements, m3_meet, m3_join, fixed=(1, 2, 3))

    return {
        "m3_counterexample_exists": {
            "pass": result_is_sat(exists_result),
            "solver_result": str(exists_result),
            "detail": "cvc5 finds a distributivity counterexample in the non-distributive diamond lattice M3.",
            "expectation": "SAT for exists a,b,c with distributive-law inequality",
        },
        "m3_explicit_counterexample": {
            "pass": result_is_sat(explicit_result),
            "solver_result": str(explicit_result),
            "detail": "With atoms a=1, b=2, c=3 in M3, a meet (b join c)=a while (a meet b) join (a meet c)=0.",
            "expectation": "SAT for the fixed M3 atom triple counterexample",
            "fixed_assignment": {"a": 1, "b": 2, "c": 3},
            "evaluated_witness": {"lhs": 1, "rhs": 0, "lhs_not_equal_rhs": True},
        },
    }


def run_boundary_tests() -> dict[str, dict[str, Any]]:
    single_elements, single_meet, single_join = chain_tables(1)
    if cvc5 is None:
        single_result = None
    else:
        single_result = distributivity_counterexample_query(single_elements, single_meet, single_join)

    a, b, c = sp.symbols("a b c")
    lhs = sp.And(a, sp.Or(b, c))
    rhs = sp.Or(sp.And(a, b), sp.And(a, c))
    lhs_dnf = sp.to_dnf(lhs, simplify=True)
    rhs_dnf = sp.to_dnf(rhs, simplify=True)
    sympy_pass = lhs_dnf == rhs_dnf
    if sympy_pass:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "supportive: SymPy normalizes the Boolean distributive identity to matching DNF"

    two_elements, two_meet, two_join = chain_tables(2)
    two_result = None if cvc5 is None else distributivity_counterexample_query(two_elements, two_meet, two_join)

    return {
        "single_element_lattice_no_counterexample": {
            "pass": single_result is not None and result_is_unsat(single_result),
            "solver_result": "not_run" if single_result is None else str(single_result),
            "detail": "The one-element lattice has no possible distributivity counterexample.",
        },
        "sympy_boolean_distributivity_dnf": {
            "pass": bool(sympy_pass),
            "lhs_dnf": str(lhs_dnf),
            "rhs_dnf": str(rhs_dnf),
            "detail": "SymPy supportively normalizes both Boolean sides to the same DNF.",
        },
        "two_element_lattice_no_counterexample": {
            "pass": two_result is not None and result_is_unsat(two_result),
            "solver_result": "not_run" if two_result is None else str(two_result),
            "detail": "The two-element chain/Boolean lattice has no possible distributivity counterexample.",
        },
    }


def flatten_test_rows(*sections: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section in sections:
        rows.extend(row for row in section.values() if isinstance(row, dict) and "pass" in row)
    return rows


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    rows = flatten_test_rows(positive, negative, boundary)
    all_pass = all(bool(row.get("pass")) for row in rows)

    if cvc5 is not None and all(
        positive[name]["pass"] for name in ("boolean_lattice_no_counterexample", "chain_lattice_no_counterexample")
    ) and all(
        negative[name]["pass"] for name in ("m3_counterexample_exists", "m3_explicit_counterexample")
    ):
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = (
            "load-bearing: canonical pass depends on cvc5 UNSAT checks for bounded distributive lattices "
            "and SAT counterexample checks for non-distributive M3"
        )

    results = {
        "name": "Lattice Distributive Constraint Canonical",
        "classification": "canonical" if all_pass else "supporting",
        "status": "PASS" if all_pass else "FAIL",
        "all_pass": all_pass,
        "summary": {
            "tests_total": len(rows),
            "tests_passed": sum(1 for row in rows if row.get("pass") is True),
            "all_pass": all_pass,
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "demotion_condition": (
            "demote if any cvc5 finite-lattice SAT/UNSAT row or SymPy boundary row fails"
        ),
        "out_of_scope": [
            "no bridge promotion",
            "no axis promotion",
            "no engine promotion",
            "no scientific coupling promotion",
            "no full lattice-theory theorem claim",
        ],
        "claim_ceiling": "tool_micro_finite_lattice_distributivity_constraint_only",
        "next_lego_target": "strict admission as cvc5 finite-order micro before any geometry/operator coupling",
        "promotion_condition": "requires canonical result surface, strict admission artifact, and stage-gate approval",
        "blocked_until": "accepted wizard sim admission exists for this exact result hash",
        "prior_function_receipts": [],
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_lattice_distributive_constraint_canonical_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {all_pass}")
