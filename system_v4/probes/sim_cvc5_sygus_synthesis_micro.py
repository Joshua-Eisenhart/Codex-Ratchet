#!/usr/bin/env python3
"""cvc5 SyGuS synthesis micro probe.

Tool-stage scope:
  - one tool: cvc5
  - one API surface: synthFun / addSygusConstraint / checkSynth
  - one tiny claim: cvc5 can synthesize a bounded integer function from a
    small grammar and reject an impossible grammar/spec pair.

This is pre-lego evidence. It does not promote a lego, coupling, bridge, or
stack claim.
"""

import json
import os

import cvc5
from cvc5 import Kind

classification = "canonical"
NAME = "sim_cvc5_sygus_synthesis_micro"
PROBE_FAMILY = "cvc5_sygus_synthesis_micro"
CONSTRAINT_SET = "bounded_linear_integer_sygus_fixture"

_NOT_USED_REASON = (
    "not used: this micro probe isolates cvc5 SyGuS synthesis only; "
    "cross-tool coupling and lego promotion are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": (
            "cvc5 is load-bearing: synthFun, addSygusConstraint, checkSynth, "
            "and getSynthSolution determine the synthesis/no-synthesis verdicts."
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
TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"


def _solver():
    solver = cvc5.Solver()
    solver.setOption("sygus", "true")
    solver.setLogic("LIA")
    return solver


def _linear_grammar(solver, x, start):
    grammar = solver.mkGrammar([x], [start])
    grammar.addAnyVariable(start)
    grammar.addRule(start, solver.mkInteger(0))
    grammar.addRule(start, solver.mkInteger(1))
    grammar.addRule(start, solver.mkTerm(Kind.ADD, x, solver.mkInteger(1)))
    return grammar


def _constant_grammar(solver, x, start):
    grammar = solver.mkGrammar([x], [start])
    grammar.addRule(start, solver.mkInteger(0))
    grammar.addRule(start, solver.mkInteger(1))
    return grammar


def _solution_found(result):
    return "SOLUTION" in str(result)


def run_positive_tests():
    solver = _solver()
    int_sort = solver.getIntegerSort()
    x = solver.mkVar(int_sort, "x")
    start = solver.mkVar(int_sort, "Start")
    grammar = _linear_grammar(solver, x, start)
    f = solver.synthFun("f_plus_one", [x], int_sort, grammar)
    fx = solver.mkTerm(Kind.APPLY_UF, f, x)
    target = solver.mkTerm(Kind.ADD, x, solver.mkInteger(1))
    solver.addSygusConstraint(solver.mkTerm(Kind.EQUAL, fx, target))

    result = solver.checkSynth()
    solution = solver.getSynthSolution(f) if _solution_found(result) else None
    solution_text = str(solution)

    return {
        "linear_successor_function_synthesized": {
            "passed": _solution_found(result) and "+ x 1" in solution_text,
            "expected": "solution lambda equivalent to x + 1",
            "cvc5_result": str(result),
            "solution": solution_text,
            "grammar": ["x", "0", "1", "x + 1"],
        }
    }


def run_negative_tests():
    solver = _solver()
    int_sort = solver.getIntegerSort()
    x = solver.mkVar(int_sort, "x")
    start = solver.mkVar(int_sort, "Start")
    grammar = solver.mkGrammar([x], [start])
    grammar.addRule(start, solver.mkTerm(Kind.ADD, x, solver.mkInteger(1)))
    f = solver.synthFun("f_impossible", [x], int_sort, grammar)
    fx = solver.mkTerm(Kind.APPLY_UF, f, x)
    impossible_target = solver.mkTerm(Kind.ADD, x, solver.mkInteger(2))
    solver.addSygusConstraint(solver.mkTerm(Kind.EQUAL, fx, impossible_target))

    result = solver.checkSynth()
    return {
        "grammar_rejects_unavailable_plus_two": {
            "passed": "NO_SOLUTION" in str(result),
            "expected": "no solution because the grammar only admits x + 1",
            "cvc5_result": str(result),
            "exclusion_note": "SyGuS must not report a function outside the declared grammar.",
        }
    }


def run_boundary_tests():
    solver = _solver()
    int_sort = solver.getIntegerSort()
    x = solver.mkVar(int_sort, "x")
    start = solver.mkVar(int_sort, "Start")
    grammar = _constant_grammar(solver, x, start)
    f = solver.synthFun("f_constant_one", [x], int_sort, grammar)
    fx = solver.mkTerm(Kind.APPLY_UF, f, x)
    solver.addSygusConstraint(solver.mkTerm(Kind.EQUAL, fx, solver.mkInteger(1)))

    result = solver.checkSynth()
    solution = solver.getSynthSolution(f) if _solution_found(result) else None
    solution_text = str(solution)

    return {
        "constant_grammar_boundary_selects_one": {
            "passed": _solution_found(result) and "1" in solution_text,
            "expected": "solution from the finite grammar {0, 1}",
            "cvc5_result": str(result),
            "solution": solution_text,
            "boundary_note": "The grammar is intentionally finite to expose the synthesis boundary.",
        }
    }


def _flatten_sections(*sections):
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
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "Other SyGuS grammars and theories remain unproven; this receipt covers only the named LIA grammar fixtures."
        ],
        "claim_ceiling": "tool_function_micro_only",
        "next_lego_target": "minimal SyGuS integer grammar fixture before coupling or lego promotion",
        "promotion_condition": (
            "requires a later admitted lego row that names this exact function "
            "receipt and passes strict runner admission; this MICRO row does "
            "not promote the lego"
        ),
        "blocked_until": (
            "blocked until a downstream queue row declares the exact lego "
            "target, parent receipts, and active stage gate for promotion"
        ),
        "demotion_condition": (
            "Demote cvc5 for this surface if checkSynth cannot find the bounded "
            "successor solution, reports a solution outside the grammar, or fails "
            "to reject the impossible plus-two specification."
        ),
        "out_of_scope": [
            "no lego promotion",
            "no tool-tool coupling",
            "no bridge claim",
            "no proof of the whole cvc5 SyGuS surface",
        ],
        "criteria_checked": [
            "cvc5 SyGuS bounded successor synthesis",
            "cvc5 SyGuS impossible grammar/spec rejection",
            "cvc5 SyGuS finite constant grammar boundary",
        ],
        "summary": {"passed": sum(1 for test in flat_tests if test.get("passed")), "total": len(flat_tests)},
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
