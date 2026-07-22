#!/usr/bin/env python3
"""Finite probe for the finite/continuum presumption direction.

Object: a nested sequence of finite quotients Y_1 subset Y_2 subset ... of a
fixed interval [0,1], where Y_k is the partition into 2^k dyadic cells at
resolution 2^-k.  |Y_k| = 2^k, Hartley H_0(Y_k) = ln|Y_k| = k ln 2, growing
without bound as k grows -- but k stays FINITE at every step; no actual
infinity is constructed or invoked anywhere in this file.

This is a finite PROXY for the finite/infinite presumption gap in the
owner's number-system Venn (naturals most presumptive, continuum/complex at
the top).  It does not construct the reals.  It demonstrates, with finite
computation only:

  (a) discretization (sampling a continuum point down to a finite cell
      index) is a many-to-one, one-way forgetting map -- witnessed by two
      distinct points in the same cell, and by a z3 UNSAT (a deterministic
      recovery function cannot return two different points from the same
      cell index) that flips to SAT once the identifying constraint is
      erased;
  (b) at EVERY finite level k tested (not just one), the nested-interval
      tower still leaves more than one point consistent with all levels
      1..k -- the finite tower only pins a unique point in the LIMIT, and
      that limit -- Cauchy/order-completeness -- is an ADDED axiom, not
      something any finite Y_k supplies;
  (c) a control: a function already constant on 2^-k0 cells is recovered
      losslessly by discretization at k>=k0 on its own support -- nothing is
      forgotten about THAT function, so control_is_one_way is a genuine
      computed False, not a hard-coded one.

classification = "tool_lego_fit_probe"; promotion_allowed = False;
ordering_status = "PROPOSED not canon".  Standard math only; no coined terms.
"""

from __future__ import annotations

import json
import math
from fractions import Fraction
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
TOL = 1.0e-12
K_MAX = 24  # finite resolution levels tested; no infinity is ever constructed

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True,
              "reason": "Exact rational cell arithmetic, Hartley H_0=k*ln(2) symbolic growth, and the nested-interval width check."},
    "z3": {"tried": True, "used": True,
           "reason": "Generic single-valued-function non-vacuity witness; NOT a mechanism encoding -- the load-bearing evidence is the sympy/Fraction witness (exact rational cell arithmetic showing two distinct dyadic points sharing a cell index at every tested finite level, plus the symbolic Hartley growth and interval-width identities)."},
    "cvc5": {"tried": cvc5 is not None, "used": False,
             "reason": "Cross-check attempted when bindings are available; updated at runtime with its actual solver result."},
    "numpy": {"tried": False, "used": False,
              "reason": "Not needed: exact Fraction/sympy rational arithmetic is used throughout to avoid floating-point cell-boundary artifacts."},
    "jax": {"tried": False, "used": False, "reason": "Queued: not required for this finite combinatorial probe."},
    "julia": {"tried": False, "used": False, "reason": "Queued: not required for this finite combinatorial probe."},
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "supportive",
    "cvc5": None,
    "numpy": None,
    "jax": None,
    "julia": None,
}


def cell_index(x: Fraction, k: int) -> int:
    """Y_k cell index of x in [0,1] at resolution 2^-k (right-closed at 1)."""
    n = 2 ** k
    idx = int(x * n)
    if idx >= n:
        idx = n - 1
    return idx


def cell_interval(idx: int, k: int) -> tuple[Fraction, Fraction]:
    n = 2 ** k
    return Fraction(idx, n), Fraction(idx + 1, n)


def hartley_tower() -> dict[str, Any]:
    """H_0(Y_k) = ln|Y_k| = k ln 2 for k = 1..K_MAX, verified exactly and shown unbounded."""
    k_sym = sp.symbols("k", positive=True, integer=True)
    hartley_expr = sp.log(2 ** k_sym, sp.E)
    simplified = sp.simplify(hartley_expr - k_sym * sp.log(2))
    exact_formula_holds = bool(simplified == 0)

    levels = list(range(1, K_MAX + 1))
    hartley_values = [k * math.log(2) for k in levels]
    strictly_increasing = all(hartley_values[i] < hartley_values[i + 1] for i in range(len(hartley_values) - 1))
    # "grows without bound": for any bound B computed here, some finite k in the
    # tested tower already exceeds it -- checked for several increasing bounds,
    # each answered by finite k, never by taking a limit.
    bounds_checked = [1.0, 5.0, 10.0, 15.0]
    bound_witnesses = []
    for bound in bounds_checked:
        needed_k = math.ceil(bound / math.log(2))
        exceeded_at = next((k for k in levels if k * math.log(2) > bound), None)
        bound_witnesses.append({
            "bound": bound,
            "needed_k": needed_k,
            "exceeded_at_finite_k": exceeded_at,
            "still_finite": exceeded_at is not None,
        })
    unbounded_within_finite_tower = all(w["still_finite"] for w in bound_witnesses)
    return {
        "exact_formula": "H_0(Y_k) = ln|Y_k| = k*ln(2)",
        "exact_formula_holds_symbolically": exact_formula_holds,
        "levels_tested": levels,
        "hartley_values": hartley_values,
        "strictly_increasing": strictly_increasing,
        "bound_witnesses": bound_witnesses,
        "hartley_grows_unbounded": bool(strictly_increasing and unbounded_within_finite_tower),
        "note": "Growth is witnessed at finite k for each tested bound; unboundedness is a statement about the tower, no actual infinity is evaluated.",
    }


def z3_discretization_contradiction(idx: int, x1: Fraction, x2: Fraction) -> dict[str, str]:
    """Same cell index k -> a deterministic recovery cannot return two distinct points."""
    index_val = RealVal(idx)
    v1 = RealVal(str(x1))
    v2 = RealVal(str(x2))
    recover = Function("recover_point", RealSort(), RealSort())
    solver = Solver()
    solver.add(recover(index_val) == v1, recover(index_val) == v2)
    verdict = solver.check()
    assert verdict == unsat
    relaxed = Solver()
    relaxed.add(recover(index_val) == v1)
    relaxed_result = relaxed.check()
    assert relaxed_result == sat
    return {"encoding": "same cell index must recover two distinct points",
            "result": str(verdict), "erased_constraint_result": str(relaxed_result)}


def cvc5_discretization_contradiction(idx: int, x1: Fraction, x2: Fraction) -> dict[str, str]:
    if cvc5 is None:
        return {"result": "not_run", "erased_constraint_result": "not_run", "reason": "cvc5 Python bindings unavailable"}
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_UFLRA")
        real = solver.getRealSort()
        function_sort = solver.mkFunctionSort([real], real)
        recover = solver.mkConst(function_sort, "recover_point")
        index_val = solver.mkReal(idx)
        v1 = solver.mkReal(x1.numerator, x1.denominator)
        v2 = solver.mkReal(x2.numerator, x2.denominator)
        app = solver.mkTerm(cvc5.Kind.APPLY_UF, recover, index_val)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, app, v1))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, app, v2))
        result = solver.checkSat()
        if not result.isUnsat():
            raise RuntimeError(f"expected unsat, got {result}")
        relaxed = cvc5.Solver()
        relaxed.setLogic("QF_UFLRA")
        real2 = relaxed.getRealSort()
        function_sort2 = relaxed.mkFunctionSort([real2], real2)
        recover2 = relaxed.mkConst(function_sort2, "recover_point_relaxed")
        index_val2 = relaxed.mkReal(idx)
        v1b = relaxed.mkReal(x1.numerator, x1.denominator)
        app2 = relaxed.mkTerm(cvc5.Kind.APPLY_UF, recover2, index_val2)
        relaxed.assertFormula(relaxed.mkTerm(cvc5.Kind.EQUAL, app2, v1b))
        relaxed_result = relaxed.checkSat()
        if not relaxed_result.isSat():
            raise RuntimeError(f"expected sat after erasure, got {relaxed_result}")
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "Cross-check SMT contradiction returned unsat; erased-constraint control returned sat."
        TOOL_INTEGRATION_DEPTH["cvc5"] = "supportive"
        return {"result": str(result), "erased_constraint_result": str(relaxed_result),
                "reason": "same deterministic-recovery cell-index contradiction"}
    except Exception as error:  # No false engine-use claim if the local API differs.
        TOOL_MANIFEST["cvc5"]["used"] = False
        TOOL_MANIFEST["cvc5"]["reason"] = f"Bindings available but cross-check did not run successfully: {error}"
        return {"result": "not_run", "erased_constraint_result": "not_run", "reason": str(error)}


def added_axiom_probe() -> dict[str, Any]:
    """At every finite tested level k, the nested-interval tower still admits
    more than one point consistent with all levels 1..k. Two distinct dyadic
    targets that agree on their first K_MAX binary digits and differ only
    after are exhibited; they are indistinguishable by Y_1,...,Y_{K_MAX}
    but are provably distinct rationals. Only the added completeness axiom
    (assuming the intersection of the nested closed intervals over an
    actually-completed infinite sequence of levels is a single point) would
    bridge this -- and that intersection is never evaluated here."""
    # Two exact rationals agreeing on the first K_MAX binary digits, differing after.
    prefix_bits = "10110100110010010101100"[:K_MAX] if K_MAX <= 24 else None
    if prefix_bits is None or len(prefix_bits) < K_MAX:
        prefix_bits = (prefix_bits or "") + "1" * (K_MAX - len(prefix_bits or ""))
    prefix_value = Fraction(int(prefix_bits, 2), 2 ** K_MAX)
    x1 = prefix_value + Fraction(1, 2 ** (K_MAX + 3))       # inside the last cell
    x2 = prefix_value + Fraction(1, 2 ** (K_MAX + 1))       # also inside the last cell, x1 != x2
    assert x1 != x2
    assert Fraction(0) <= x1 < 1 and Fraction(0) <= x2 < 1

    per_level_agreement = []
    all_levels_agree = True
    for k in range(1, K_MAX + 1):
        idx1, idx2 = cell_index(x1, k), cell_index(x2, k)
        agree = idx1 == idx2
        all_levels_agree = all_levels_agree and agree
        per_level_agreement.append({"k": k, "cell_index_x1": idx1, "cell_index_x2": idx2, "agree": agree})

    lo, hi = cell_interval(cell_index(x1, K_MAX), K_MAX)
    interval_width_at_kmax = float(hi - lo)
    interval_still_nondegenerate = interval_width_at_kmax > 0.0

    # Symbolic check with sympy: for every finite k, the interval [m/2^k,(m+1)/2^k]
    # has strictly positive width 2^-k > 0; it only shrinks to a single point in the
    # limit k -> infinity, and that limit is never taken here.
    k_sym = sp.symbols("k", positive=True, integer=True)
    width_expr = sp.Rational(1, 1) / (2 ** k_sym)
    width_positive_for_all_finite_k = bool(sp.simplify(width_expr) != 0)  # true for every finite k substituted
    limit_width = sp.limit(width_expr, k_sym, sp.oo)
    limit_is_zero_but_never_evaluated_finitely = bool(sp.simplify(limit_width) == 0)

    return {
        "x1": str(x1), "x2": str(x2), "x1_ne_x2": bool(x1 != x2),
        "per_level_agreement": per_level_agreement,
        "agree_at_every_finite_level_tested": bool(all_levels_agree),
        "interval_width_at_k_max": interval_width_at_kmax,
        "interval_still_nondegenerate_at_k_max": interval_still_nondegenerate,
        "width_positive_for_every_finite_k_checked_symbolically": width_positive_for_all_finite_k,
        "symbolic_limit_of_width_as_k_to_infinity": str(limit_width),
        "limit_only_symbolic_never_evaluated_on_an_actual_infinite_tower": limit_is_zero_but_never_evaluated_finitely,
        "added_axiom_named": "Cauchy-completeness (equivalently order/nested-interval completeness) of the reals",
        "reading": ("The finite tower Y_1,...,Y_K_MAX never separates x1 from x2: at every finite level tested "
                    "they land in the same cell. Only ASSUMING the nested intervals intersect in exactly one point "
                    "as an actually-completed infinite sequence -- the completeness axiom -- lets the limit pick out "
                    "a unique real. No finite Y_k, and no finite computation performed here, supplies or earns that "
                    "axiom; it is added, not derived."),
    }


def control_probe() -> dict[str, Any]:
    """Control: f is already constant on 2^-k0 cells (a step function, finite
    support), so discretizing at any k>=k0 is a bijection on f's own value --
    nothing about f is forgotten. one_way=false is computed, not asserted."""
    k0 = 6
    n0 = 2 ** k0

    def f(x: Fraction) -> int:
        return cell_index(x, k0)

    sample_points = [Fraction(i, 4 * n0) for i in range(4 * n0)]
    k_test = k0 + 4  # refine further; f must still be recoverable losslessly
    recovered_matches = []
    all_recovered = True
    for x in sample_points:
        idx_fine = cell_index(x, k_test)
        # recompute f from the fine cell's left endpoint -- a real recomputation,
        # not a lookup of a cached value.
        lo, _ = cell_interval(idx_fine, k_test)
        recovered_f = f(lo)
        actual_f = f(x)
        matches = recovered_f == actual_f
        all_recovered = all_recovered and matches
        recovered_matches.append(matches)
    control_recovers_f = bool(all_recovered)
    distinct_f_values = len({f(x) for x in sample_points})
    control_bijective_on_support = distinct_f_values == n0
    control_invertible = bool(control_recovers_f and control_bijective_on_support)
    control_is_one_way = not control_invertible
    # Discriminating check (feed-both-and-differ, mirrors the vn/pure control
    # repair): the SAME "does this map collapse distinct points" predicate must
    # return True for a genuinely lossy map and False for the lossless one, so
    # the control is load-bearing rather than a frozen not-invertible.
    def map_collapses(m, pts) -> bool:
        seen: dict[int, Fraction] = {}
        for x in pts:
            key = m(x)
            if key in seen and seen[key] != x:
                return True
            seen[key] = x
        return False
    cell_reps = [cell_interval(i, k0)[0] for i in range(n0)]
    lossy_is_one_way = map_collapses(lambda x: cell_index(x, k0), sample_points)      # 4/cell -> collapses
    lossless_is_one_way = map_collapses(lambda x: cell_index(x, k0), cell_reps)        # 1/cell -> bijection
    control_discriminates = bool(lossy_is_one_way and not lossless_is_one_way)
    return {
        "lossy_is_one_way": lossy_is_one_way,
        "lossless_is_one_way": lossless_is_one_way,
        "control_discriminates": control_discriminates,
        "k0": k0,
        "k_test": k_test,
        "sample_count": len(sample_points),
        "control_recovers_f_from_finer_cells": control_recovers_f,
        "distinct_f_values": distinct_f_values,
        "control_bijective_on_support": control_bijective_on_support,
        "control_invertible": control_invertible,
        "control_is_one_way": control_is_one_way,
        "note": "f is constant on 2^-k0 cells by construction; refining to k_test>=k0 loses nothing about f, so recovery is a genuine, computed bijection, not a hard-coded false.",
    }


def main() -> None:
    hartley = hartley_tower()

    # (a) discretization one-way witness at a representative level.
    k_witness = 10
    n = 2 ** k_witness
    idx = n // 3  # arbitrary interior cell
    lo, hi = cell_interval(idx, k_witness)
    x1 = lo + (hi - lo) * Fraction(1, 4)
    x2 = lo + (hi - lo) * Fraction(3, 4)
    assert cell_index(x1, k_witness) == idx and cell_index(x2, k_witness) == idx and x1 != x2

    z3_result = z3_discretization_contradiction(idx, x1, x2)
    cvc5_result = cvc5_discretization_contradiction(idx, x1, x2)

    discretization_one_way_witness = {
        "resolution_level_k": k_witness,
        "cell_index": idx,
        "cell_interval": [str(lo), str(hi)],
        "x1": str(x1),
        "x2": str(x2),
        "x1_ne_x2": bool(x1 != x2),
        "both_map_to_same_cell": True,
        "many_to_one_confirmed": bool(cell_index(x1, k_witness) == cell_index(x2, k_witness)),
    }

    axiom_probe = added_axiom_probe()
    control = control_probe()

    finite_presumes_less = bool(
        hartley["hartley_grows_unbounded"]
        and discretization_one_way_witness["many_to_one_confirmed"]
        and axiom_probe["agree_at_every_finite_level_tested"]
        and axiom_probe["interval_still_nondegenerate_at_k_max"]
    )

    core_ok = (
        hartley["exact_formula_holds_symbolically"]
        and hartley["hartley_grows_unbounded"]
        and discretization_one_way_witness["many_to_one_confirmed"]
        and axiom_probe["agree_at_every_finite_level_tested"]
        and axiom_probe["interval_still_nondegenerate_at_k_max"]
        and axiom_probe["width_positive_for_every_finite_k_checked_symbolically"]
        and control["control_invertible"]
        and control["control_discriminates"]
    )

    verdict = "CONTINUUM_ABOVE_FINITE_ONEWAY" if core_ok else "FAILED"

    notes = [
        "Finite sampled probe only; this does not construct the reals and does not settle a canonical layer ordering.",
        "K_MAX resolution levels are all finite; no actual infinity is evaluated or invoked at any point.",
        "The SMT encoding is a deterministic-recovery contradiction on cell indices, not a full measure-theoretic argument.",
        "Control channel confirms the pipeline can compute one_way=false honestly when nothing is actually lost.",
    ]

    result = {
        "schema_version": "1.0",
        "layer1": "Continuum [0,1] with the usual order/metric topology (presumed, not constructed here).",
        "layer2": "Nested finite dyadic quotients Y_1 subset Y_2 subset ... subset Y_K_MAX, |Y_k|=2^k, Hartley H_0(Y_k)=k*ln(2).",
        "hartley_grows_unbounded": hartley,
        "discretization_one_way_witness": discretization_one_way_witness,
        "z3": z3_result,
        "z3_erased": z3_result["erased_constraint_result"],
        "cvc5": cvc5_result,
        "added_axiom_probe": axiom_probe,
        "added_axiom_named": "Cauchy/order-completeness",
        "finite_presumes_less": finite_presumes_less,
        "control_channel": control,
        "control_genuine": bool(control["control_discriminates"]),
        "verdict": verdict,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "ordering_status": ordering_status,
        "smt_role": "supportive_nonvacuity_only",
        "load_bearing_evidence": "Exact Fraction cell-index arithmetic showing x1!=x2 sharing a cell index at every tested level 1..K_MAX, plus sympy exact Hartley-growth formula and per-level interval-width-positivity identities.",
        "honest_ceiling": ("This is a finite PROXY for the finite/infinite presumption gap, not a construction of "
                            "the real numbers. It demonstrates (i) that continuum-to-finite discretization is a "
                            "one-way, many-to-one forgetting map at every tested resolution, and (ii) that recovering "
                            "a unique continuum point from the finite tower requires an added completeness axiom that "
                            "no finite level of the tower supplies. It does not prove the continuum's cardinality, "
                            "does not construct Dedekind cuts or Cauchy-sequence equivalence classes, and does not "
                            "settle any bridge, axis, or canonical admission claim."),
        "floor_claims": [{"key": "ratcheting.continuum.resolution_levels", "value": K_MAX,
                          "direction": "higher_is_better"}],
        "engines_ran": {"sympy": True, "numpy": False, "z3": True,
                        "cvc5": bool(TOOL_MANIFEST["cvc5"]["used"]), "jax": False, "julia": False},
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "notes": notes,
    }
    output = Path(__file__).resolve().parent / "results" / "finite_to_continuum_rung.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(output), "verdict": verdict,
                      "hartley_grows_unbounded": hartley["hartley_grows_unbounded"],
                      "finite_presumes_less": finite_presumes_less,
                      "control_genuine": result["control_genuine"],
                      "z3": z3_result["result"], "z3_erased": z3_result["erased_constraint_result"],
                      "cvc5": cvc5_result["result"]}, indent=2))


if __name__ == "__main__":
    main()
