#!/usr/bin/env python3
"""
p-adic comparison / crystalline constraint canonical sim.

This is a bounded conformance probe, not a bridge or axis claim.  It tests
small integer shadows of p-adic comparison constraints:
- Hodge-Tate weights for an elliptic H1 packet stay in [0, dim].
- dim D_cris(V) stays <= dim V.
- the cyclotomic character packet has Hodge-Tate weight 1.

cvc5 is load-bearing only when SAT/UNSAT outcomes depend on structural
constraints and mutation rows flip to SAT after removing those constraints.
"""

from __future__ import annotations

import json
import os
from typing import Any

import sympy as sp

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "bounded p-adic comparison packet is integer SMT plus symbolic rank bookkeeping, with no tensor/autograd computation"},
    "pyg": {"tried": False, "used": False, "reason": "no graph message-passing surface is present in the Hodge-Tate weight and D_cris dimension constraints"},
    "z3": {"tried": False, "used": False, "reason": "cvc5 is the selected SMT checker for the QF_LIA integer-bound packet, so z3 would duplicate the same role"},
    "cvc5": {"tried": False, "used": False, "reason": "not installed"},
    "sympy": {"tried": True, "used": False, "reason": "supportive symbolic rank check is attempted for the Tate/crystalline two-dimensional comparison shadow"},
    "clifford": {"tried": False, "used": False, "reason": "the packet has no geometric product, rotor, spinor, or Clifford transport calculation"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold metric, geodesic, curvature, or Frechet statistic is part of this integer comparison probe"},
    "e3nn": {"tried": False, "used": False, "reason": "no E(3) or O(3) equivariant field appears in the p-adic weight/dimension constraints"},
    "rustworkx": {"tried": False, "used": False, "reason": "the proof surface is finite integer constraints, not graph traversal, DAG routing, or dependency optimization"},
    "xgi": {"tried": False, "used": False, "reason": "no hyperedge incidence or multiway interaction changes the bounded Hodge-Tate/D_cris equality queries"},
    "toponetx": {"tried": False, "used": False, "reason": "the packet has no cell-complex boundary map, adjacency relation, or homology computation to certify"},
    "gudhi": {"tried": False, "used": False, "reason": "the packet has no filtration, persistence interval, simplex complex, or TDA invariant to compute"},
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
    TOOL_MANIFEST["cvc5"]["reason"] = "available; used only if structural SAT/UNSAT and mutation-flip rows are consumed"
except ImportError:  # pragma: no cover - optional dependency absent
    cvc5 = None


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


def solver_with_int(name: str) -> tuple[Any, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    var = solver.mkConst(solver.getIntegerSort(), name)
    return solver, var


def hodge_tate_weight_query(candidate_weight: int, include_upper_bound: bool = True) -> Any:
    solver, weight = solver_with_int("ht_weight")
    dimension = solver.mkInteger(1)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, weight, solver.mkInteger(0)))
    if include_upper_bound:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.LEQ, weight, dimension))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, weight, solver.mkInteger(candidate_weight)))
    return solver.checkSat()


def dcris_dimension_query(candidate_dim: int, include_comparison_bound: bool = True) -> Any:
    solver, dim_dcris = solver_with_int("dim_dcris")
    dim_representation = solver.mkInteger(2)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, dim_dcris, solver.mkInteger(0)))
    if include_comparison_bound:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.LEQ, dim_dcris, dim_representation))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, dim_dcris, solver.mkInteger(candidate_dim)))
    return solver.checkSat()


def cyclotomic_weight_query(candidate_weight: int, include_cyclotomic_constraint: bool = True) -> Any:
    solver, chi_weight = solver_with_int("chi_p_weight")
    if include_cyclotomic_constraint:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, chi_weight, solver.mkInteger(1)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, chi_weight, solver.mkInteger(candidate_weight)))
    return solver.checkSat()


def run_positive_tests() -> dict[str, dict[str, Any]]:
    if cvc5 is None:
        return {
            "hodge_tate_weight_zero_admissible": cvc5_unavailable_row("hodge_tate_weight_zero_admissible"),
            "hodge_tate_weight_one_admissible": cvc5_unavailable_row("hodge_tate_weight_one_admissible"),
            "dcris_dimension_equal_admissible": cvc5_unavailable_row("dcris_dimension_equal_admissible"),
            "cyclotomic_weight_one_admissible": cvc5_unavailable_row("cyclotomic_weight_one_admissible"),
        }

    ht0 = hodge_tate_weight_query(0)
    ht1 = hodge_tate_weight_query(1)
    dcris_equal = dcris_dimension_query(2)
    cyclotomic_one = cyclotomic_weight_query(1)

    return {
        "hodge_tate_weight_zero_admissible": {
            "pass": result_is_sat(ht0),
            "solver_result": str(ht0),
            "detail": "cvc5 accepts Hodge-Tate weight 0 under the elliptic H1 bound 0 <= w <= 1.",
        },
        "hodge_tate_weight_one_admissible": {
            "pass": result_is_sat(ht1),
            "solver_result": str(ht1),
            "detail": "cvc5 accepts Hodge-Tate weight 1 under the elliptic H1 bound 0 <= w <= 1.",
        },
        "dcris_dimension_equal_admissible": {
            "pass": result_is_sat(dcris_equal),
            "solver_result": str(dcris_equal),
            "detail": "cvc5 accepts dim D_cris(V)=2 when dim V=2 and dim D_cris(V) <= dim V.",
        },
        "cyclotomic_weight_one_admissible": {
            "pass": result_is_sat(cyclotomic_one),
            "solver_result": str(cyclotomic_one),
            "detail": "cvc5 accepts the cyclotomic character packet with Hodge-Tate weight 1.",
        },
    }


def run_negative_tests() -> dict[str, dict[str, Any]]:
    if cvc5 is None:
        return {
            "hodge_tate_weight_out_of_range_unsat": cvc5_unavailable_row("hodge_tate_weight_out_of_range_unsat"),
            "dcris_dimension_exceeds_representation_unsat": cvc5_unavailable_row("dcris_dimension_exceeds_representation_unsat"),
            "cyclotomic_weight_two_unsat": cvc5_unavailable_row("cyclotomic_weight_two_unsat"),
        }

    ht_bad = hodge_tate_weight_query(2)
    dcris_bad = dcris_dimension_query(3)
    cyclotomic_bad = cyclotomic_weight_query(2)

    return {
        "hodge_tate_weight_out_of_range_unsat": {
            "pass": result_is_unsat(ht_bad),
            "solver_result": str(ht_bad),
            "detail": "With the structural bound 0 <= w <= dim and dim=1, cvc5 rejects candidate Hodge-Tate weight 2.",
            "candidate_weight": 2,
            "structural_constraint": "0 <= ht_weight <= 1",
        },
        "dcris_dimension_exceeds_representation_unsat": {
            "pass": result_is_unsat(dcris_bad),
            "solver_result": str(dcris_bad),
            "detail": "With dim D_cris(V) <= dim V and dim V=2, cvc5 rejects candidate dim D_cris(V)=3.",
            "candidate_dim_dcris": 3,
            "structural_constraint": "0 <= dim_dcris <= 2",
        },
        "cyclotomic_weight_two_unsat": {
            "pass": result_is_unsat(cyclotomic_bad),
            "solver_result": str(cyclotomic_bad),
            "detail": "With the cyclotomic packet constraint chi_p_weight=1, cvc5 rejects candidate weight 2.",
            "candidate_weight": 2,
            "structural_constraint": "chi_p_weight = 1",
        },
    }


def run_boundary_tests() -> dict[str, dict[str, Any]]:
    if cvc5 is None:
        ht_mutation = dcris_mutation = cyclotomic_mutation = None
    else:
        ht_mutation = hodge_tate_weight_query(2, include_upper_bound=False)
        dcris_mutation = dcris_dimension_query(3, include_comparison_bound=False)
        cyclotomic_mutation = cyclotomic_weight_query(2, include_cyclotomic_constraint=False)

    tate_module = sp.eye(2)
    crystalline_module = sp.eye(2)
    sympy_rank_pass = tate_module.rank() == crystalline_module.rank() == 2
    if sympy_rank_pass:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "supportive: SymPy confirms the two-dimensional rank shadow used by the Tate/crystalline comparison row"

    return {
        "hodge_tate_bound_mutation_flips_to_sat": {
            "pass": ht_mutation is not None and result_is_sat(ht_mutation),
            "solver_result": "not_run" if ht_mutation is None else str(ht_mutation),
            "detail": "Removing the upper Hodge-Tate bound makes candidate weight 2 SAT, proving the UNSAT row depends on the structural bound.",
        },
        "dcris_bound_mutation_flips_to_sat": {
            "pass": dcris_mutation is not None and result_is_sat(dcris_mutation),
            "solver_result": "not_run" if dcris_mutation is None else str(dcris_mutation),
            "detail": "Removing dim D_cris(V) <= dim V makes candidate dim 3 SAT, proving the UNSAT row depends on the comparison bound.",
        },
        "cyclotomic_constraint_mutation_flips_to_sat": {
            "pass": cyclotomic_mutation is not None and result_is_sat(cyclotomic_mutation),
            "solver_result": "not_run" if cyclotomic_mutation is None else str(cyclotomic_mutation),
            "detail": "Removing chi_p_weight=1 makes candidate weight 2 SAT, proving the UNSAT row depends on the cyclotomic packet constraint.",
        },
        "sympy_tate_crystalline_rank_shadow": {
            "pass": bool(sympy_rank_pass),
            "tate_rank": int(tate_module.rank()),
            "crystalline_rank": int(crystalline_module.rank()),
            "detail": "SymPy supportively checks both rank-shadow matrices are two-dimensional; cvc5 still carries the constraint proof.",
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

    required_cvc5_rows = [
        positive["hodge_tate_weight_zero_admissible"],
        positive["hodge_tate_weight_one_admissible"],
        positive["dcris_dimension_equal_admissible"],
        positive["cyclotomic_weight_one_admissible"],
        negative["hodge_tate_weight_out_of_range_unsat"],
        negative["dcris_dimension_exceeds_representation_unsat"],
        negative["cyclotomic_weight_two_unsat"],
        boundary["hodge_tate_bound_mutation_flips_to_sat"],
        boundary["dcris_bound_mutation_flips_to_sat"],
        boundary["cyclotomic_constraint_mutation_flips_to_sat"],
    ]
    if cvc5 is not None and all(row.get("pass") is True for row in required_cvc5_rows):
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = (
            "load-bearing: canonical pass depends on cvc5 SAT admissible rows, UNSAT violation rows, "
            "and SAT mutation flips for Hodge-Tate, D_cris, and cyclotomic constraints"
        )

    results = {
        "name": "p-adic comparison crystalline constraint canonical",
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
            "demote if any cvc5 Hodge-Tate, D_cris, cyclotomic, mutation, or SymPy rank-shadow row fails"
        ),
        "out_of_scope": [
            "no bridge promotion",
            "no axis promotion",
            "no engine promotion",
            "no scientific coupling promotion",
            "no full p-adic comparison theorem claim",
        ],
        "claim_ceiling": "tool_micro_p_adic_comparison_constraint_only",
        "next_lego_target": "strict admission as cvc5 p-adic comparison micro before any geometry/operator coupling",
        "promotion_condition": "requires canonical result surface, strict admission artifact, and stage-gate approval",
        "blocked_until": "accepted wizard sim admission exists for this exact result hash",
        "prior_function_receipts": [],
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_p_adic_comparison_crystalline_constraint_canonical_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {all_pass}")
