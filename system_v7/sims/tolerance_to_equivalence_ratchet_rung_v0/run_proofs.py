#!/usr/bin/env python3
"""Independent z3/cvc5 free-variable proofs for the first Ratchet rung."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import cvc5
import z3
from cvc5 import Kind


SIM_DIR = Path(__file__).resolve().parent
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = SIM_DIR / "results" / "proof_results.json"


def z3_problem(n: int, raw_edges: list[list[int]], include_transitivity: bool = True):
    solver = z3.Solver()
    relation = [[z3.Bool(f"z_E_{i}_{j}") for j in range(n)] for i in range(n)]
    for i in range(n):
        solver.add(relation[i][i])
    for i in range(n):
        for j in range(n):
            solver.add(relation[i][j] == relation[j][i])
    if include_transitivity:
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    solver.add(z3.Implies(z3.And(relation[i][j], relation[j][k]), relation[i][k]))
    for i, j in raw_edges:
        solver.add(relation[i][j])
        solver.add(relation[j][i])
    return solver, relation


def z3_queries() -> dict[str, str]:
    chain = [[0, 1], [1, 2]]
    sat_solver, _ = z3_problem(3, chain)
    sat_c = str(sat_solver.check())
    implication_solver, implication_relation = z3_problem(3, chain)
    implication_solver.add(z3.Not(implication_relation[0][2]))
    endpoint_negation = str(implication_solver.check())
    minimal_solver, minimal_relation = z3_problem(4, [[0, 1], [2, 3]])
    closure = [[i // 2 == j // 2 for j in range(4)] for i in range(4)]
    for i in range(4):
        for j in range(4):
            if not closure[i][j]:
                minimal_solver.add(z3.Not(minimal_relation[i][j]))
    minimal_solver.add(z3.Or(*[z3.Not(minimal_relation[i][j]) for i in range(4) for j in range(4) if closure[i][j]]))
    strict_subclosure = str(minimal_solver.check())
    control_solver, control_relation = z3_problem(3, chain, include_transitivity=False)
    control_solver.add(z3.Not(control_relation[0][2]))
    drop_transitivity = str(control_solver.check())
    return {
        "sat_equivalence_containing_chain": sat_c,
        "endpoint_negation_under_transitivity": endpoint_negation,
        "strict_subclosure_containing_raw": strict_subclosure,
        "drop_transitivity_endpoint_absent": drop_transitivity,
    }


def cvc5_problem(n: int, raw_edges: list[list[int]], include_transitivity: bool = True):
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    boolean = solver.getBooleanSort()
    relation = [[solver.mkConst(boolean, f"c_E_{i}_{j}") for j in range(n)] for i in range(n)]
    for i in range(n):
        solver.assertFormula(relation[i][i])
    for i in range(n):
        for j in range(n):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, relation[i][j], relation[j][i]))
    if include_transitivity:
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    premise = solver.mkTerm(Kind.AND, relation[i][j], relation[j][k])
                    solver.assertFormula(solver.mkTerm(Kind.IMPLIES, premise, relation[i][k]))
    for i, j in raw_edges:
        solver.assertFormula(relation[i][j])
        solver.assertFormula(relation[j][i])
    return solver, relation


def cvc5_queries() -> dict[str, str]:
    chain = [[0, 1], [1, 2]]
    sat_solver, _ = cvc5_problem(3, chain)
    sat_c = str(sat_solver.checkSat())
    implication_solver, implication_relation = cvc5_problem(3, chain)
    implication_solver.assertFormula(implication_solver.mkTerm(Kind.NOT, implication_relation[0][2]))
    endpoint_negation = str(implication_solver.checkSat())
    minimal_solver, minimal_relation = cvc5_problem(4, [[0, 1], [2, 3]])
    closure = [[i // 2 == j // 2 for j in range(4)] for i in range(4)]
    missing = []
    for i in range(4):
        for j in range(4):
            if not closure[i][j]:
                minimal_solver.assertFormula(minimal_solver.mkTerm(Kind.NOT, minimal_relation[i][j]))
            else:
                missing.append(minimal_solver.mkTerm(Kind.NOT, minimal_relation[i][j]))
    minimal_solver.assertFormula(minimal_solver.mkTerm(Kind.OR, *missing))
    strict_subclosure = str(minimal_solver.checkSat())
    control_solver, control_relation = cvc5_problem(3, chain, include_transitivity=False)
    control_solver.assertFormula(control_solver.mkTerm(Kind.NOT, control_relation[0][2]))
    drop_transitivity = str(control_solver.checkSat())
    return {
        "sat_equivalence_containing_chain": sat_c,
        "endpoint_negation_under_transitivity": endpoint_negation,
        "strict_subclosure_containing_raw": strict_subclosure,
        "drop_transitivity_endpoint_absent": drop_transitivity,
    }


def main() -> int:
    expected = {
        "sat_equivalence_containing_chain": "sat",
        "endpoint_negation_under_transitivity": "unsat",
        "strict_subclosure_containing_raw": "unsat",
        "drop_transitivity_endpoint_absent": "sat",
    }
    z3_result = z3_queries()
    cvc5_result = cvc5_queries()
    all_pass = z3_result == cvc5_result == expected
    result = {
        "schema": "codex_ratchet.tolerance_to_equivalence.proof_result.v1",
        "sim_id": "tolerance_to_equivalence_ratchet_rung_v0",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "reads_peer_result": False,
        "source_path": str(SOURCE_PATH.relative_to(SIM_DIR.parents[2])),
        "source_sha256": hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest(),
        "free_boolean_relation_variables": True,
        "ground_literal_only": False,
        "expected": expected,
        "z3": {"version": z3.get_version_string(), "queries": z3_result},
        "cvc5": {"version": cvc5.__version__, "queries": cvc5_result},
        "all_pass": all_pass,
        "claim_ceiling": "two bounded finite relation encodings only; not a general theorem prover admission",
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"DUAL_SMT_TOLERANCE_RUNG_DONE all_pass={str(all_pass).lower()} z3={z3_result} cvc5={cvc5_result}")
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
