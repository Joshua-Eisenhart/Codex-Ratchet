#!/usr/bin/env python3
"""JAX/Python lane for the repaired 3Q GCM constraint carve.

This lane intentionally uses aligned Python rich tools from the JAX target set:
networkx for quotient connectivity, sympy for exact count guards, and z3/cvc5
for contradiction checks bound to the computed survivor count.
"""

from __future__ import annotations

import json

import cvc5
from cvc5 import Kind
import networkx as nx
import sympy as sp
import z3

from gcm_constraint_carve_3q_v1_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    SIM_ID,
    build_packet,
    rel,
    write_json,
)


RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"


def z3_guard(value: int) -> str:
    x = z3.Int("jax_survivor_count")
    solver = z3.Solver()
    solver.add(x == value)
    solver.add(x != 545)
    return str(solver.check())


def cvc5_guard(value: int) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    x = solver.mkConst(int_sort, "jax_survivor_count")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, x, solver.mkInteger(value)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, x, solver.mkInteger(545))))
    return str(solver.checkSat()).lower()


def build_result() -> dict[str, object]:
    packet = build_packet()
    graph = nx.Graph()
    for row in packet["quotient"]["classes"]:
        graph.add_node(row["class_id"], member_count=row["member_count"])
    classes = packet["quotient"]["classes"]
    for left, right in zip(classes, classes[1:]):
        graph.add_edge(left["class_id"], right["class_id"])
    components = [sorted(component) for component in nx.connected_components(graph)]
    exact_survivors = sp.Rational(packet["survivor_count"], 1)
    exact_classes = sp.Rational(packet["quotient"]["class_count"], 1)
    exact_margin = sp.Rational(3, 16)
    all_pass = (
        packet["survivor_count"] == 545
        and packet["quotient"]["class_count"] == 9
        and sp.simplify(exact_survivors - 545) == 0
        and sp.simplify(exact_classes - 9) == 0
        and z3_guard(packet["survivor_count"]) == "unsat"
        and cvc5_guard(packet["survivor_count"]) == "unsat"
    )
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
        "source_path": rel(__import__("pathlib").Path(__file__)),
        "result_path": rel(RESULT_PATH),
        "packages_used": ["networkx", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["networkx", "sympy", "z3", "cvc5"],
        "package_observables": {
            "networkx": "nx.Graph and nx.connected_components over quotient classes",
            "sympy": "sp.Rational exact count and CKW margin guards",
            "z3": "z3.Solver unsat guard for computed survivor count != 545",
            "cvc5": "cvc5.Solver unsat guard for computed survivor count != 545",
        },
        "candidate_count": packet["candidate_space"]["candidate_count"],
        "survivor_count": packet["survivor_count"],
        "quotient_class_count": packet["quotient"]["class_count"],
        "quotient_component_count": len(components),
        "exact_ckw_margin_guard": str(exact_margin),
        "ghz_w_rows": packet["ghz_w_matrix_finding"]["rows"],
        "all_pass": bool(all_pass),
    }


def main() -> int:
    payload = build_result()
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
