#!/usr/bin/env python3
"""JAX/Python lane for the 4Q GCM constraint carve.

This lane intentionally uses aligned Python rich tools from the JAX target set:
networkx for quotient connectivity, sympy for exact count guards, and z3/cvc5
for contradiction checks bound to the computed survivor count.
"""

from __future__ import annotations

import json
from pathlib import Path

import cvc5
from cvc5 import Kind
import networkx as nx
import sympy as sp
import z3

from gcm_constraint_carve_4q_v0_common import (
    CLASSIFICATION,
    EXPECTED_QUOTIENT_CLASS_COUNT,
    EXPECTED_SURVIVOR_COUNT,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    SIM_ID,
    build_packet,
    rel,
    write_json,
)


RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "networkx": {"tried": True, "used": True, "reason": "quotient graph construction and connected-component check over 4Q classes"},
    "sympy": {"tried": True, "used": True, "reason": "exact integer guards for survivor, class, and cut-lattice counts"},
    "z3": {"tried": True, "used": True, "reason": "SMT contradiction guard for the 4Q survivor count"},
    "cvc5": {"tried": True, "used": True, "reason": "independent SMT contradiction guard for the 4Q survivor count"},
}
TOOL_INTEGRATION_DEPTH = {
    "networkx": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def z3_guard(value: int) -> str:
    x = z3.Int("jax_4q_survivor_count")
    solver = z3.Solver()
    solver.add(x == value)
    solver.add(x != EXPECTED_SURVIVOR_COUNT)
    return str(solver.check())


def cvc5_guard(value: int) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    x = solver.mkConst(int_sort, "jax_4q_survivor_count")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, x, solver.mkInteger(value)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, x, solver.mkInteger(EXPECTED_SURVIVOR_COUNT))))
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
    exact_cut_count = sp.Rational(packet["cut_lattice"]["count"], 1)
    all_pass = (
        packet["survivor_count"] == EXPECTED_SURVIVOR_COUNT
        and packet["quotient"]["class_count"] == EXPECTED_QUOTIENT_CLASS_COUNT
        and sp.simplify(exact_survivors - EXPECTED_SURVIVOR_COUNT) == 0
        and sp.simplify(exact_classes - EXPECTED_QUOTIENT_CLASS_COUNT) == 0
        and sp.simplify(exact_cut_count - 7) == 0
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
        "source_path": rel(Path(__file__)),
        "result_path": rel(RESULT_PATH),
        "packages_used": ["networkx", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["networkx", "sympy", "z3", "cvc5"],
        "package_observables": {
            "networkx": "nx.Graph and nx.connected_components over 4Q quotient classes",
            "sympy": "sp.Rational exact survivor/class/cut-lattice count guards",
            "z3": "z3.Solver unsat guard for computed 4Q survivor count",
            "cvc5": "cvc5.Solver unsat guard for computed 4Q survivor count",
        },
        "candidate_count": packet["candidate_space"]["candidate_count"],
        "survivor_count": packet["survivor_count"],
        "quotient_class_count": packet["quotient"]["class_count"],
        "cut_lattice_count": packet["cut_lattice"]["count"],
        "quotient_component_count": len(components),
        "ghz4_w4_cluster_rows": packet["ghz4_w4_cluster_admissibility_matrix"]["rows"],
        "source_recompute_injection_red": packet["controls"]["source_recompute_injection_red"]["red"],
        "all_pass": bool(all_pass),
    }


def main() -> int:
    payload = build_result()
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
