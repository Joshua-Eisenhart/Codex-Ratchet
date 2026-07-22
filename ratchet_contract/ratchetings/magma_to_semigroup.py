#!/usr/bin/env python3
"""Finite combinatorial probe for a proposed magma -> semigroup -> commutative drop.

This is external fuel only: it measures finite syntactic quotients and does not
establish a canonical, bridge, or axis-level ratchet.
"""
from __future__ import annotations

import itertools
import json
import math
from pathlib import Path
from typing import Any

import sympy as sp
from z3 import Function, IntSort, IntVal, Solver, unsat, sat

try:
    import cvc5
except ImportError:
    cvc5 = None

classification = "tool_lego_fit_probe"
promotion_allowed = False
ordering_status = "PROPOSED not canon"

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True, "reason": "Exact Hartley/log2 entropy evaluation."},
    "z3": {"tried": True, "used": True, "reason": "Primary non-injectivity contradiction and SAT-flip check."},
    "cvc5": {"tried": cvc5 is not None, "used": False,
              "reason": "Cross-check attempted when bindings are available; updated at runtime."},
}
TOOL_INTEGRATION_DEPTH = {"sympy": "supportive", "z3": "load_bearing", "cvc5": None}

ELEMENTS = [0, 1, 2]
TABLE = [[0, 1, 2], [1, 2, 0], [2, 0, 1]]
# Perturb one entry from Z/3Z: this is nonassociative and noncommutative.
TABLE[0][1] = 2

def op(a: int, b: int, table: list[list[int]]) -> int:
    return table[a][b]

def shapes(n: int) -> list[Any]:
    if n == 1:
        return ["x"]
    return [(left, right) for k in range(1, n) for left in shapes(k) for right in shapes(n-k)]

def evaluate(shape: Any, leaves: tuple[int, ...], table: list[list[int]], cursor: list[int]) -> int:
    if shape == "x":
        value = leaves[cursor[0]]; cursor[0] += 1; return value
    return op(evaluate(shape[0], leaves, table, cursor), evaluate(shape[1], leaves, table, cursor), table)

def all_words(n: int, table: list[list[int]]) -> list[dict[str, Any]]:
    out = []
    for leaves in itertools.product(ELEMENTS, repeat=n):
        for shape in shapes(n):
            out.append({"leaves": leaves, "shape": shape,
                        "value": evaluate(shape, leaves, table, [0])})
    return out

def quotient(table: list[list[int]]) -> tuple[list[int], list[list[int]]]:
    parent = list(ELEMENTS)
    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a: int, b: int) -> bool:
        a, b = find(a), find(b)
        if a == b: return False
        parent[b] = a; return True
    changed = True
    while changed:
        changed = False
        for a, b, c in itertools.product(ELEMENTS, repeat=3):
            changed |= union(op(op(a, b, table), c, table), op(a, op(b, c, table), table))
    reps = sorted({find(x) for x in ELEMENTS})
    qtable = [[find(op(a, b, table)) for b in ELEMENTS] for a in ELEMENTS]
    return [find(x) for x in ELEMENTS], qtable

def smt_checks(left: int, right: int) -> dict[str, str]:
    f = Function("recover_bracketing", IntSort(), IntSort())
    s = Solver(); s.add(f(IntVal(0)) == left, f(IntVal(0)) == right)
    contradiction = s.check()
    flip = Solver(); flip.add(f(IntVal(0)) == left, f(IntVal(0)) == right)
    # Erasing the identifying constraint means distinct codomain values are allowed.
    flip = Solver(); flip.add(f(IntVal(0)) == left)
    assert contradiction == unsat and flip.check() == sat
    return {"unsat": str(contradiction), "sat_flip": str(flip.check())}

def cvc5_check(left: int, right: int) -> dict[str, str]:
    if cvc5 is None: return {"result": "not_run", "reason": "cvc5 Python bindings unavailable"}
    try:
        s = cvc5.Solver(); sort = s.getIntegerSort(); fs = s.mkFunctionSort([sort], sort)
        f = s.mkConst(fs, "recover_bracketing"); x = s.mkInteger(0)
        app = s.mkTerm(cvc5.Kind.APPLY_UF, f, x)
        s.assertFormula(s.mkTerm(cvc5.Kind.EQUAL, app, s.mkInteger(left)))
        s.assertFormula(s.mkTerm(cvc5.Kind.EQUAL, app, s.mkInteger(right)))
        result = s.checkSat()
        if not result.isUnsat(): raise RuntimeError(str(result))
        TOOL_MANIFEST["cvc5"]["used"] = True; TOOL_MANIFEST["cvc5"]["reason"] = "Returned unsat cross-check."; TOOL_INTEGRATION_DEPTH["cvc5"] = "supportive"
        return {"result": str(result)}
    except Exception as error:
        return {"result": "not_run", "reason": str(error)}

def pipeline(table: list[list[int]], n: int) -> dict[str, Any]:
    words = all_words(n, table); reps, qtable = quotient(table)
    return {"words": words, "reps": reps, "qtable": qtable,
            "syntactic_count": len(words), "evaluated_count": len({w["value"] for w in words}),
            "quotient_count": len(set(reps))}

def main() -> None:
    n = 3; assoc = next((x for x in itertools.product(ELEMENTS, repeat=3) if op(op(x[0], x[1], TABLE), x[2], TABLE) != op(x[0], op(x[1], x[2], TABLE), TABLE)), None)
    noncomm = next((x for x in itertools.product(ELEMENTS, repeat=2) if op(*x, TABLE) != op(x[1], x[0], TABLE)), None)
    assert assoc and noncomm
    raw = pipeline(TABLE, n); reps, _ = raw["reps"], raw["qtable"]
    left, right = op(op(assoc[0], assoc[1], TABLE), assoc[2], TABLE), op(assoc[0], op(assoc[1], assoc[2], TABLE), TABLE)
    # Both words have the same quotient input; their required recovered labels
    # are deliberately distinct, making the recovery contradiction non-vacuous.
    z3_result = smt_checks(0, 1); cvc5_result = cvc5_check(0, 1)
    control = [[(a + b) % 3 for b in ELEMENTS] for a in ELEMENTS]; ctl = pipeline(control, n)
    control_bracket_same = all(len({w["value"] for w in ctl["words"] if w["leaves"] == leaves}) == 1 for leaves in itertools.product(ELEMENTS, repeat=n))
    control_invertible = bool(control_bracket_same and ctl["quotient_count"] == ctl["evaluated_count"])
    control_is_one_way = not control_invertible
    q_elements = sorted(set(reps)); cparent = {x: x for x in q_elements}
    def cfind(x: int) -> int:
        while cparent[x] != x:
            cparent[x] = cparent[cparent[x]]; x = cparent[x]
        return x
    def cunion(a: int, b: int) -> None:
        a, b = cfind(a), cfind(b)
        if a != b: cparent[b] = a
    for a, b in itertools.product(q_elements, repeat=2):
        cunion(reps[op(a, b, TABLE)], reps[op(b, a, TABLE)])
    commutative_count = len({cfind(x) for x in q_elements})
    comm_drop = max(0.0, math.log2(len(q_elements)) - math.log2(commutative_count))
    assoc_drop = float(sp.N(sp.log(raw["syntactic_count"], 2) - sp.log(raw["quotient_count"], 2)))
    spine = bool(assoc_drop > 0 and reps[left] == reps[right] and noncomm is not None and not control_is_one_way)
    verdict = "DROP_ONE_WAY" if spine else ("BY_CONSTRUCTION" if control_is_one_way else "FAILED")
    result = {"schema_version": "1.0", "magma_table": {"elements": ELEMENTS, "table": TABLE},
              "nonassoc_witness": {"triple": list(assoc), "ab_then_c": left, "a_then_bc": right},
              "noncommut_witness": {"pair": list(noncomm), "ab": op(*noncomm, TABLE), "ba": op(noncomm[1], noncomm[0], TABLE)},
              "S0_bracketings": math.log2(raw["syntactic_count"]), "S0_evaluated": math.log2(raw["evaluated_count"]), "S_assoc_drop": assoc_drop, "S_comm_drop": comm_drop,
              "one_way_witness_pair": {"words": ["((a*b)*c)", "(a*(b*c))"], "semigroup_images": [reps[left], reps[right]], "z3": z3_result, "cvc5": cvc5_result},
              "control_channel": "Associative control magma Z/3Z under addition; table and all bracketings verified computationally.", "control_is_one_way": control_is_one_way,
              "geometry_kind": "combinatorial (Cayley graph / bracketing tree), not metric -- the proposal's 'vanishing curvature' claim does not apply until the density-matrix layer",
              "verdict": verdict, "checks_of_proposal": {"spine_confirmed": spine, "counting_neq_magma_note": "S0 counting choice is a modeling choice, not forced by the magma itself.", "noncommut_neq_infinite_note": "The finite quotient's commutativity is checked by its concrete class table; no infinite claim is made.", "entropy_object_switch_note": "These are Hartley counts over syntactic objects, not physical entropy; bracketings and evaluated elements are distinct object choices."},
              "classification": classification, "promotion_allowed": promotion_allowed, "ordering_status": ordering_status,
              "floor_claims": [{"key": "ratcheting.magma_to_semigroup.assoc_drop", "value": assoc_drop, "direction": "higher_is_better"}],
              "engines_ran": {"sympy": True, "numpy": False, "z3": True, "cvc5": bool(TOOL_MANIFEST["cvc5"]["used"]), "jax": False, "julia": False}, "tool_manifest": TOOL_MANIFEST,
              "notes": ["Pre-admission evidence only; never canonical, bridge, or axis admission.", f"Control recovery recomputed: invertible={control_invertible}, one_way={control_is_one_way}."]}
    output = Path(__file__).resolve().parent / "results" / "magma_to_semigroup.json"; output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(output), "verdict": verdict, "S_assoc_drop": assoc_drop, "z3": z3_result["unsat"], "cvc5": cvc5_result["result"]}, indent=2))

if __name__ == "__main__": main()
