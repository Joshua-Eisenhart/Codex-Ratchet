#!/usr/bin/env python3
"""
Zorn-style bounded chain constraint canonical sim.

This is a finite order-theory conformance probe, not a proof of Zorn's Lemma
or the Axiom of Choice.  cvc5 checks small integer-chain SAT/UNSAT fixtures
that mirror the local obstruction: a strictly increasing chain cannot be
extended inside a finite bounded universe once it already occupies every slot.
SymPy records only the propositional implication shape as supportive context.
"""

from __future__ import annotations

import json
import os
from typing import Any

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "finite order-theory SMT packet has no tensor/autograd computation"},
    "pyg": {"tried": False, "used": False, "reason": "finite chain constraints do not use graph neural message passing"},
    "z3": {"tried": False, "used": False, "reason": "cvc5 is the selected SMT surface for this QF_LIA finite-chain packet"},
    "cvc5": {"tried": False, "used": False, "reason": "not installed"},
    "sympy": {"tried": False, "used": False, "reason": "not installed"},
    "clifford": {"tried": False, "used": False, "reason": "finite poset chain inequalities have no Clifford product, rotor, spinor, or multivector operation"},
    "geomstats": {"tried": False, "used": False, "reason": "the packet has no metric manifold, geodesic, curvature, or statistics-on-manifolds computation"},
    "e3nn": {"tried": False, "used": False, "reason": "no Euclidean equivariant tensor field appears in this finite order-theory SMT fixture"},
    "rustworkx": {"tried": False, "used": False, "reason": "the witness is decided by explicit integer order constraints, not graph traversal or DAG routing"},
    "xgi": {"tried": False, "used": False, "reason": "no hyperedge incidence or multiway relation is part of this bounded chain query"},
    "toponetx": {"tried": False, "used": False, "reason": "there is no cell complex, boundary map, adjacency, or homology computation to certify"},
    "gudhi": {"tried": False, "used": False, "reason": "there is no filtration, simplex complex, persistence interval, or TDA invariant to compute"},
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
    TOOL_MANIFEST["cvc5"]["reason"] = "available; used only if finite-chain SAT/UNSAT rows are consumed"
except ImportError:  # pragma: no cover - optional dependency absent
    cvc5 = None

try:
    import sympy as sp

    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "available; used only for supportive propositional-shape bookkeeping"
except ImportError:  # pragma: no cover - optional dependency absent
    sp = None


def result_is_sat(result: Any) -> bool:
    return str(result) == "sat" or getattr(result, "isSat", lambda: False)()


def result_is_unsat(result: Any) -> bool:
    return str(result) == "unsat" or getattr(result, "isUnsat", lambda: False)()


def cvc5_unavailable_row(name: str) -> dict[str, Any]:
    return {
        "pass": False,
        "solver_result": "not_run",
        "detail": f"{name} requires cvc5, but cvc5 is unavailable.",
    }


def bounded_int(solver: Any, var: Any, lower: int, upper: int) -> None:
    solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, var, solver.mkInteger(lower)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.LEQ, var, solver.mkInteger(upper)))


def finite_chain_query(chain_length: int, upper_bound: int, require_extension: bool) -> Any:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    elements = [
        solver.mkConst(solver.getIntegerSort(), f"e_{index}")
        for index in range(chain_length)
    ]

    for element in elements:
        bounded_int(solver, element, 0, upper_bound)

    for left, right in zip(elements, elements[1:]):
        solver.assertFormula(solver.mkTerm(cvc5.Kind.LT, left, right))

    if require_extension:
        extension = solver.mkConst(solver.getIntegerSort(), "extension")
        bounded_int(solver, extension, 0, upper_bound)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.LT, elements[-1], extension))

    return solver.checkSat()


def run_positive_tests() -> dict[str, dict[str, Any]]:
    if cvc5 is None:
        return {
            "three_element_bounded_chain_sat": cvc5_unavailable_row("three_element_bounded_chain_sat"),
            "two_element_bounded_chain_sat": cvc5_unavailable_row("two_element_bounded_chain_sat"),
            "singleton_bounded_chain_sat": cvc5_unavailable_row("singleton_bounded_chain_sat"),
        }

    three = finite_chain_query(chain_length=3, upper_bound=2, require_extension=False)
    two = finite_chain_query(chain_length=2, upper_bound=1, require_extension=False)
    singleton = finite_chain_query(chain_length=1, upper_bound=0, require_extension=False)

    return {
        "three_element_bounded_chain_sat": {
            "pass": result_is_sat(three),
            "solver_result": str(three),
            "detail": "cvc5 accepts a strict 0<1<2 chain inside the finite universe [0,2].",
            "expectation": "SAT for the bounded finite chain fixture",
        },
        "two_element_bounded_chain_sat": {
            "pass": result_is_sat(two),
            "solver_result": str(two),
            "detail": "cvc5 accepts a strict two-element chain inside [0,1].",
            "expectation": "SAT for the bounded finite chain fixture",
        },
        "singleton_bounded_chain_sat": {
            "pass": result_is_sat(singleton),
            "solver_result": str(singleton),
            "detail": "cvc5 accepts a singleton finite chain inside [0,0].",
            "expectation": "SAT for the bounded singleton fixture",
        },
    }


def run_negative_tests() -> dict[str, dict[str, Any]]:
    if cvc5 is None:
        return {
            "full_three_slot_chain_extension_unsat": cvc5_unavailable_row("full_three_slot_chain_extension_unsat"),
            "full_four_slot_chain_extension_unsat": cvc5_unavailable_row("full_four_slot_chain_extension_unsat"),
            "too_many_strict_elements_unsat": cvc5_unavailable_row("too_many_strict_elements_unsat"),
        }

    three_extension = finite_chain_query(chain_length=3, upper_bound=2, require_extension=True)
    four_extension = finite_chain_query(chain_length=4, upper_bound=3, require_extension=True)
    too_many = finite_chain_query(chain_length=5, upper_bound=3, require_extension=False)

    return {
        "full_three_slot_chain_extension_unsat": {
            "pass": result_is_unsat(three_extension),
            "solver_result": str(three_extension),
            "detail": "Given a strict three-element chain inside [0,2], cvc5 rejects a fourth in-range element above its top.",
            "structural_constraint": "0 <= e_i <= 2 and e0 < e1 < e2 < extension",
            "expectation": "UNSAT because the finite upper bound is already occupied",
        },
        "full_four_slot_chain_extension_unsat": {
            "pass": result_is_unsat(four_extension),
            "solver_result": str(four_extension),
            "detail": "Given a strict four-element chain inside [0,3], cvc5 rejects a fifth in-range element above its top.",
            "structural_constraint": "0 <= e_i <= 3 and e0 < e1 < e2 < e3 < extension",
            "expectation": "UNSAT because the finite upper bound is already occupied",
        },
        "too_many_strict_elements_unsat": {
            "pass": result_is_unsat(too_many),
            "solver_result": str(too_many),
            "detail": "cvc5 rejects five strictly increasing integer elements inside a four-slot universe [0,3].",
            "structural_constraint": "five distinct strict positions in four bounded integer slots",
            "expectation": "UNSAT by finite pigeonhole-style ordering pressure",
        },
    }


def run_boundary_tests() -> dict[str, dict[str, Any]]:
    if cvc5 is None:
        mutation = None
    else:
        mutation = finite_chain_query(chain_length=3, upper_bound=3, require_extension=True)

    if sp is None:
        sympy_row = {
            "pass": False,
            "detail": "SymPy unavailable; propositional-shape row not run.",
        }
    else:
        chain_bounded, maximal_exists = sp.symbols("chain_bounded maximal_exists")
        implication = sp.Implies(chain_bounded, maximal_exists)
        contrapositive = sp.Implies(sp.Not(maximal_exists), sp.Not(chain_bounded))
        sympy_row = {
            "pass": True,
            "zorn_shape": str(implication),
            "contrapositive_shape": str(contrapositive),
            "detail": "SymPy records only the propositional implication/contrapositive shape; it does not prove AoC or full Zorn's Lemma.",
        }
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "supportive: recorded the implication and contrapositive shapes without promoting a set-theoretic theorem proof"

    return {
        "extension_mutation_flips_to_sat": {
            "pass": mutation is not None and result_is_sat(mutation),
            "solver_result": "not_run" if mutation is None else str(mutation),
            "detail": "Raising the finite universe from [0,2] to [0,3] makes the three-chain extension SAT, proving the UNSAT row depends on the finite upper-bound constraint.",
            "expectation": "SAT after relaxing the upper-bound fixture",
        },
        "empty_chain_note": {
            "pass": True,
            "detail": "The empty-chain case is recorded as a convention note only; no SMT theorem promotion is made.",
        },
        "sympy_propositional_shape": sympy_row,
    }


def rows_pass(rows: dict[str, dict[str, Any]]) -> bool:
    return all(bool(row.get("pass")) for row in rows.values())


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    cvc5_rows_pass = rows_pass(positive) and rows_pass(negative) and boundary["extension_mutation_flips_to_sat"]["pass"]
    if cvc5_rows_pass:
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = (
            "load-bearing: cvc5 QF_LIA SAT/UNSAT rows certify bounded finite-chain "
            "extension constraints and the mutation row flips after relaxing the upper bound"
        )

    all_pass = rows_pass(positive) and rows_pass(negative) and rows_pass(boundary)
    results = {
        "name": "Zorn-style bounded chain constraint canonical",
        "classification": classification,
        "status": "pass" if all_pass else "fail",
        "all_pass": all_pass,
        "summary": (
            "Bounded finite-poset SMT fixture only: cvc5 checks finite-chain "
            "SAT/UNSAT and upper-bound mutation behavior; no full Zorn, AoC, bridge, "
            "axis, engine, or broad coupling claim is admitted."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "demotion_condition": (
            "demote if any cvc5 finite-chain SAT/UNSAT, upper-bound mutation, or SymPy propositional-shape row fails"
        ),
        "out_of_scope": [
            "no bridge promotion",
            "no axis promotion",
            "no engine promotion",
            "no scientific coupling promotion",
            "no full Zorn lemma or Axiom of Choice theorem claim",
        ],
        "claim_ceiling": "tool_micro_finite_chain_zorn_shadow_constraint_only",
        "next_lego_target": "strict admission as cvc5 finite-chain micro before any geometry/operator coupling",
        "promotion_condition": "requires canonical result surface, strict admission artifact, and stage-gate approval",
        "blocked_until": "accepted wizard sim admission exists for this exact result hash",
        "prior_function_receipts": [],
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_zorns_lemma_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
