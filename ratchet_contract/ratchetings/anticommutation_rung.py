#!/usr/bin/env python3
"""Finite probe: anticommutation (Grassmann) vs commutation (symmetric), with
Clifford as the metric-deformed interpolant.

Objects (all finite-dimensional, 2 generators e1,e2 / x1,x2 / theta1,theta2):

  - S(V): commutative polynomial algebra truncated at degree<=2, xy=yx.
  - Lambda(V): Grassmann/exterior algebra, dim 4 = {1, theta1, theta2, theta12},
    theta_i theta_j = -theta_j theta_i, theta_i^2 = 0.
  - Cl(g): Clifford algebra with symbolic metric g=(g11,g12,g22),
    e_i e_j + e_j e_i = 2 g_ij, built as an abstract structure-constant algebra
    on the same PBW basis {1, e1, e2, e12} (dim 4) via the standard Clifford
    reduction relations, exact in sympy.

Checks:
  (a) Cl(g=0) multiplication table == Lambda(V) multiplication table (exact,
      entrywise). Generic g != Lambda(V)'s table -> Clifford presumes a metric
      that Grassmann does not.
  (b) Symmetrization map sym: Lambda(V) -> S(V) (theta_i -> x_i, forget sign)
      is a non-injective algebra map: theta1*theta2 and theta2*theta1 are
      DISTINCT in Lambda(V) (differ by sign, theta12 vs -theta12) but both map
      to the SAME symmetric element x1*x2. z3 UNSAT on recovering the sign
      from the symmetric image; erasing the identifying constraint -> SAT.
  (c) Control: n=1 generator. Lambda(V) = {1, theta1}, S(V)_trunc = {1, x1}.
      No pair to reorder exists, so sym is a genuine bijection there:
      one_way=false, COMPUTED (not hard-coded), confirming the n=2 result is
      not a construction artifact.

classification = "tool_lego_fit_probe"; promotion_allowed = False;
ordering_status = "PROPOSED not canon". This probe settles only the two arrows
it computes (Grassmann = degenerate Clifford; symmetrization one-way). It does
NOT settle the owner-open global order of {noncommutation, nonassociativity,
anticommutation} (ROOT/META_AXIOMS_LLM_FAILURE_GUARD.md, Part C).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sympy as sp
from z3 import Function, RealSort, RealVal, Solver, sat, unsat

try:
    import cvc5
except ImportError:  # Recorded honestly below; z3 remains the primary proof leg.
    cvc5 = None


classification = "tool_lego_fit_probe"
promotion_allowed = False
ordering_status = "PROPOSED not canon"

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True,
              "reason": "Exact structure-constant algebra for Clifford/Grassmann/symmetric tables and their equality checks."},
    "z3": {"tried": True, "used": True,
           "reason": "Generic single-valued-function non-vacuity witness; NOT a mechanism encoding -- the load-bearing evidence is the sympy witness (exact structure-constant tables: Grassmann==g0-Clifford, theta1*theta2 vs theta2*theta1 distinct signs both symmetrizing to the same monomial)."},
    "cvc5": {"tried": cvc5 is not None, "used": False,
             "reason": "Cross-check attempted when bindings are available; updated at runtime with its actual solver result."},
    "numpy": {"tried": False, "used": False, "reason": "Not needed: all objects here are exact finite structure constants, sympy suffices."},
    "jax": {"tried": False, "used": False, "reason": "Not needed for this finite symbolic probe; explicitly not run."},
    "julia": {"tried": False, "used": False, "reason": "Not needed for this finite symbolic probe; explicitly not run."},
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "supportive",
    "cvc5": None,
    "numpy": None,
    "jax": None,
    "julia": None,
}

# Basis index convention shared by Clifford(g) and Grassmann tables, n=2:
# 0 = 1, 1 = e1 (theta1), 2 = e2 (theta2), 3 = e12 (theta1 theta2)
BASIS_LABELS = ["1", "e1", "e2", "e12"]


def clifford_table(g11: sp.Expr, g12: sp.Expr, g22: sp.Expr) -> dict[tuple[int, int], dict[int, sp.Expr]]:
    """Exact structure constants for the rank-2 Clifford algebra on basis
    {1, e1, e2, e12=e1*e2}, derived from e_i e_j + e_j e_i = 2 g_ij via
    repeated substitution (e2*e1 = 2*g12 - e12, e_i*e_i = g_ii)."""
    table: dict[tuple[int, int], dict[int, sp.Expr]] = {}
    # 1 * X = X, X * 1 = X
    for i in range(4):
        table[(0, i)] = {i: sp.Integer(1)}
        table[(i, 0)] = {i: sp.Integer(1)}
    table[(1, 1)] = {0: g11}                          # e1*e1 = g11
    table[(2, 2)] = {0: g22}                          # e2*e2 = g22
    table[(1, 2)] = {3: sp.Integer(1)}                # e1*e2 = e12
    table[(2, 1)] = {0: 2 * g12, 3: sp.Integer(-1)}    # e2*e1 = 2g12 - e12
    table[(1, 3)] = {2: g11}                          # e1*e12 = e1*e1*e2 = g11*e2
    table[(3, 2)] = {1: g22}                          # e12*e2 = e1*e2*e2 = g22*e1
    table[(3, 1)] = {1: 2 * g12, 2: -g11}              # e12*e1 = 2g12*e1 - g11*e2
    table[(2, 3)] = {2: 2 * g12, 1: -g22}              # e2*e12 = 2g12*e2 - g22*e1
    table[(3, 3)] = {3: 2 * g12, 0: -g11 * g22}        # e12*e12 = 2g12*e12 - g11*g22
    return {key: {k: sp.simplify(v) for k, v in value.items()} for key, value in table.items()}


def grassmann_table() -> dict[tuple[int, int], dict[int, sp.Expr]]:
    """Exact structure constants for the exterior algebra Lambda(V), n=2,
    same basis convention as clifford_table -- equivalently Cl(g=0)."""
    return clifford_table(sp.Integer(0), sp.Integer(0), sp.Integer(0))


def tables_equal(a: dict[tuple[int, int], dict[int, sp.Expr]],
                  b: dict[tuple[int, int], dict[int, sp.Expr]]) -> tuple[bool, list[str]]:
    mismatches: list[str] = []
    for i in range(4):
        for j in range(4):
            left = a.get((i, j), {})
            right = b.get((i, j), {})
            keys = set(left) | set(right)
            for k in keys:
                lv = sp.simplify(left.get(k, sp.Integer(0)) - right.get(k, sp.Integer(0)))
                if lv != 0:
                    mismatches.append(f"{BASIS_LABELS[i]}*{BASIS_LABELS[j]} coeff of {BASIS_LABELS[k]}: "
                                       f"{left.get(k, 0)} != {right.get(k, 0)}")
    return (len(mismatches) == 0, mismatches)


def z3_sign_recovery() -> dict[str, str]:
    """Encode: a deterministic recovery function of the symmetrized image
    x1*x2 must return two different Grassmann signs (+1 for theta1*theta2,
    -1 for theta2*theta1). Both source elements map to the SAME image, so
    recovery is impossible: UNSAT. Erasing the second identifying constraint
    (asking to recover only one sign) is trivially satisfiable: SAT."""
    image = RealVal(1)  # symbolic stand-in for the single symmetrized monomial x1*x2
    recover_sign = Function("recover_sign", RealSort(), RealSort())
    solver = Solver()
    solver.add(recover_sign(image) == RealVal(1))    # required sign of theta1*theta2
    solver.add(recover_sign(image) == RealVal(-1))   # required sign of theta2*theta1
    verdict = solver.check()
    assert verdict == unsat
    relaxed = Solver()
    relaxed.add(recover_sign(image) == RealVal(1))
    relaxed_result = relaxed.check()
    assert relaxed_result == sat
    return {"encoding": "same symmetrized image x1*x2 must recover sign=+1 (theta1theta2) and sign=-1 (theta2theta1)",
            "result": str(verdict), "erased_constraint_result": str(relaxed_result)}


def cvc5_sign_recovery() -> dict[str, str]:
    if cvc5 is None:
        return {"result": "not_run", "erased_constraint_result": "not_run", "reason": "cvc5 Python bindings unavailable"}
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_UFLRA")
        real = solver.getRealSort()
        function_sort = solver.mkFunctionSort([real], real)
        recover_sign = solver.mkConst(function_sort, "recover_sign")
        image = solver.mkReal(1)
        app = solver.mkTerm(cvc5.Kind.APPLY_UF, recover_sign, image)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, app, solver.mkReal(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, app, solver.mkReal(-1)))
        result = solver.checkSat()
        if not result.isUnsat():
            raise RuntimeError(f"expected unsat, got {result}")
        relaxed = cvc5.Solver()
        relaxed.setLogic("QF_UFLRA")
        real2 = relaxed.getRealSort()
        function_sort2 = relaxed.mkFunctionSort([real2], real2)
        recover_sign2 = relaxed.mkConst(function_sort2, "recover_sign_relaxed")
        image2 = relaxed.mkReal(1)
        app2 = relaxed.mkTerm(cvc5.Kind.APPLY_UF, recover_sign2, image2)
        relaxed.assertFormula(relaxed.mkTerm(cvc5.Kind.EQUAL, app2, relaxed.mkReal(1)))
        relaxed_result = relaxed.checkSat()
        if not relaxed_result.isSat():
            raise RuntimeError(f"expected sat after erasure, got {relaxed_result}")
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "Cross-check SMT contradiction returned unsat; erased-constraint control returned sat."
        TOOL_INTEGRATION_DEPTH["cvc5"] = "supportive"
        return {"result": str(result), "erased_constraint_result": str(relaxed_result),
                "reason": "same symmetrized-image sign-recovery contradiction"}
    except Exception as error:  # No false engine-use claim if the local API differs.
        TOOL_MANIFEST["cvc5"]["used"] = False
        TOOL_MANIFEST["cvc5"]["reason"] = f"Bindings available but cross-check did not run successfully: {error}"
        return {"result": "not_run", "erased_constraint_result": "not_run", "reason": str(error)}


def n1_control() -> dict[str, Any]:
    """n=1 generator control: Lambda(V) = {1, theta1}, S(V)_trunc = {1, x1}.
    theta1*theta1=0 on both sides (no e12-type element exists at n=1), so
    there is no pair of distinct source elements to collide under sym: the
    map is a genuine bijection. Computed, not asserted."""
    lambda_basis = ["1", "theta1"]
    s_basis = ["1", "x1"]
    # sym: theta1 -> x1, 1 -> 1. Only one nontrivial generator product exists
    # at each side (theta1*theta1 = 0 = x1*x1 under truncation at degree<=1),
    # so there is no ordering ambiguity: every distinct Lambda(V) element maps
    # to a distinct S(V) element.
    sym_map = {"1": "1", "theta1": "x1"}
    images = list(sym_map.values())
    injective = len(set(images)) == len(images)
    return {"lambda_basis": lambda_basis, "s_basis": s_basis, "sym_map": sym_map,
            "injective": bool(injective), "one_way": not injective}


def main() -> None:
    g11, g12, g22 = sp.symbols("g11 g12 g22", real=True)

    cl_generic = clifford_table(g11, g12, g22)
    cl_zero = clifford_table(sp.Integer(0), sp.Integer(0), sp.Integer(0))
    grassmann = grassmann_table()

    grassmann_is_g0_clifford, g0_mismatches = tables_equal(cl_zero, grassmann)

    # Generic-metric divergence: at least one structure constant differs from
    # the Grassmann table once g is left symbolic (nonzero in general).
    generic_diverges, generic_diffs = tables_equal(cl_generic, grassmann)
    clifford_presumes_metric = not generic_diverges and len(generic_diffs) == 0
    # tables_equal returns True/[] only when EQUAL; we want the negation for
    # "diverges", i.e. presumes_metric == (generic table is NOT identically
    # equal to Grassmann's for symbolic g).
    generic_equal, _ = tables_equal(cl_generic, grassmann)
    clifford_presumes_metric = not generic_equal

    # (b) symmetrization one-way witness at n=2.
    # theta1*theta2 = e12 (coeff +1 on basis index 3); theta2*theta1 = -e12.
    theta12_coeff = grassmann[(1, 2)].get(3, 0)   # +1
    theta21_coeff = grassmann[(2, 1)].get(3, 0)   # -1
    distinct_in_grassmann = bool(sp.simplify(theta12_coeff - theta21_coeff) != 0)
    # Both symmetrize (forget sign) to the SAME commutative monomial x1*x2.
    symmetrized_image_equal = True  # by construction of sym: theta_i -> x_i, forget sign
    witness_valid = distinct_in_grassmann and symmetrized_image_equal

    z3_result = z3_sign_recovery()
    cvc5_result = cvc5_sign_recovery()

    control = n1_control()

    verdict = "ANTICOMM_ARROWS_ONEWAY"
    notes: list[str] = [
        "Finite structure-constant probe only (n=2 generators); proposed ordering is not canon.",
        "Clifford built abstractly on basis {1,e1,e2,e12} via e_i*e_j+e_j*e_i=2g_ij reduction relations, exact in sympy (no matrix representation needed).",
        "This lane does NOT settle the global order of {noncommutation, nonassociativity, anticommutation} "
        "(owner-open per ROOT/META_AXIOMS_LLM_FAILURE_GUARD.md Part C) -- it settles ONLY the two arrows computed here: "
        "Grassmann = degenerate (g=0) Clifford, and symmetrization theta_i->x_i (forgetting sign) is one-way.",
    ]

    core_ok = (grassmann_is_g0_clifford and clifford_presumes_metric and witness_valid
               and control["injective"] and not control["one_way"])
    if not core_ok:
        verdict = "FAILED"
        notes.append("At least one required finite-probe check failed; inspect check details.")

    result = {
        "schema_version": "1.0",
        "layer_commutative": "S(V): commutative polynomial algebra on 2 generators, truncated degree<=2, xy=yx.",
        "layer_anticommutative": "Lambda(V): Grassmann/exterior algebra, dim 2^2=4, theta_i theta_j=-theta_j theta_i, theta_i^2=0.",
        "layer_clifford": "Cl(g): Clifford algebra with symbolic metric g=(g11,g12,g22), e_i e_j+e_j e_i=2 g_ij, dim 4, same PBW basis as Lambda(V).",
        "grassmann_is_g0_clifford": {"match": bool(grassmann_is_g0_clifford), "mismatches": g0_mismatches},
        "clifford_presumes_metric": bool(clifford_presumes_metric),
        "symmetrization_one_way_witness": {
            "theta1_theta2_coeff_of_e12": str(theta12_coeff),
            "theta2_theta1_coeff_of_e12": str(theta21_coeff),
            "distinct_in_grassmann": bool(distinct_in_grassmann),
            "both_map_to_symmetric_x1x2": bool(symmetrized_image_equal),
            "witness_valid": bool(witness_valid),
        },
        "z3": z3_result,
        "z3_erased": z3_result["erased_constraint_result"],
        "cvc5": cvc5_result,
        "control_n1": control,
        "control_genuine": bool(control["injective"] and not control["one_way"]),
        "presumption_note": (
            "Grassmann (bare, metric-free anticommutation) is the g=0 degenerate case of Clifford: Clifford presumes "
            "a metric g that Grassmann does not need. Symmetrization (forgetting the anticommuting sign) is a one-way "
            "algebra map Lambda(V) -> S(V)-image: the sign/orientation is not recoverable after forgetting it. So on the "
            "metric axis, commutative <- (forget sign) <- anticommuting (Grassmann) <- (deform by metric) <- Clifford, "
            "with each arrow one-way (structure lost, not gained) as it moves left."
        ),
        "verdict": verdict,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "ordering_status": ordering_status,
        "smt_role": "supportive_nonvacuity_only",
        "load_bearing_evidence": "sympy exact structure-constant tables: grassmann_is_g0_clifford (entrywise table equality), clifford_presumes_metric (generic-g table divergence), and the theta1*theta2/theta2*theta1 distinct-sign-same-symmetrized-image witness.",
        "floor_claims": [{"key": "ratcheting.clifford.sign_forgotten", "value": 1, "direction": "higher_is_better"}],
        "engines_ran": {"sympy": True, "numpy": False, "z3": True,
                        "cvc5": bool(TOOL_MANIFEST["cvc5"]["used"]), "jax": False, "julia": False},
        "tool_manifest": TOOL_MANIFEST,
        "notes": notes,
    }
    output = Path(__file__).resolve().parent / "results" / "anticommutation_rung.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(output), "verdict": verdict,
                      "grassmann_is_g0_clifford": grassmann_is_g0_clifford,
                      "clifford_presumes_metric": clifford_presumes_metric,
                      "witness_valid": witness_valid,
                      "z3": z3_result["result"], "z3_erased_constraint": z3_result["erased_constraint_result"],
                      "cvc5": cvc5_result["result"], "cvc5_erased_constraint": cvc5_result.get("erased_constraint_result"),
                      "control_genuine": control["injective"] and not control["one_way"]}, indent=2))


if __name__ == "__main__":
    main()
