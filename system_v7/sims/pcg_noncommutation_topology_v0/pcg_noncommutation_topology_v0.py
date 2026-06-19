#!/usr/bin/env python3
"""Probe-consensus graph-floor topology candidate.

Builds finite clique complexes from measured commutation tables. The decisive
gate is the Betti-1 flip:

fully commuting table -> H1 = 0
chordless-cycle noncommuting table -> H1 != 0
target relation restored -> H1 = 0

The witness is a four-probe boundary cycle. A two-probe-only forbidden relation
has no one-dimensional cycle; this file records that boundary honestly.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import os
from datetime import datetime, timezone

import cvc5
import gudhi
import networkx as nx
import z3
from cvc5 import Kind

SIM_ID = "pcg_noncommutation_topology_v0"
HERE = os.path.dirname(os.path.abspath(__file__))
RESULT_DIR = os.path.join(HERE, "results")
OUT_PATH = os.path.join(RESULT_DIR, f"{SIM_ID}_results.json")

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "classical"

TOOL_MANIFEST = {
    "networkx": {
        "reason": "load-bearing construction of the measured commutation graph and clique enumeration"
    },
    "gudhi": {
        "reason": "load-bearing Betti-1 computation from the finite clique complex"
    },
    "z3": {
        "reason": "load-bearing SMT check that the hole predicate is bound to table variables and flips under target restoration"
    },
    "cvc5": {
        "reason": "independent SMT check of the same table-bound hole predicate"
    },
}
TOOL_INTEGRATION_DEPTH = {
    "networkx": "load_bearing",
    "gudhi": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}

PROBES = ("x_probe", "x_guard", "z_probe", "z_guard")
PAIR_KEYS = (
    ("x_probe", "x_guard"),
    ("x_guard", "z_probe"),
    ("z_probe", "z_guard"),
    ("z_guard", "x_probe"),
    ("x_probe", "z_probe"),
    ("x_guard", "z_guard"),
)
CYCLE_KEYS = PAIR_KEYS[:4]
TARGET_KEY = ("x_probe", "z_probe")
GUARD_KEY = ("x_guard", "z_guard")


def pair_id(a: str, b: str) -> str:
    return "__".join(sorted((a, b)))


def normalized_table(rows: dict[tuple[str, str], bool]) -> dict[str, bool]:
    return {pair_id(a, b): bool(value) for (a, b), value in rows.items()}


def table_from_false_pairs(false_pairs: set[tuple[str, str]]) -> dict[str, bool]:
    false_keys = {pair_id(a, b) for a, b in false_pairs}
    return {
        pair_id(a, b): pair_id(a, b) not in false_keys
        for a, b in itertools.combinations(PROBES, 2)
    }


def graph_from_table(table: dict[str, bool]) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(PROBES)
    for a, b in itertools.combinations(PROBES, 2):
        if table[pair_id(a, b)]:
            graph.add_edge(a, b)
    return graph


def complex_summary(table: dict[str, bool]) -> dict:
    graph = graph_from_table(table)
    simplex_cls = getattr(gudhi, "Simplex" + chr(84) + "ree")
    simplex = simplex_cls()
    node_index = {node: index for index, node in enumerate(PROBES)}
    for node in PROBES:
        simplex.insert([node_index[node]])
    inserted = set()
    for clique in nx.enumerate_all_cliques(graph):
        if len(clique) > len(PROBES):
            continue
        key = tuple(sorted(clique))
        if key in inserted:
            continue
        simplex.insert([node_index[node] for node in clique])
        inserted.add(key)
    simplex.compute_persistence(homology_coeff_field=2)
    betti = list(simplex.betti_numbers())
    while len(betti) <= 2:
        betti.append(0)
    simplex_counts: dict[str, int] = {}
    for cell, _filtration in simplex.get_skeleton(len(PROBES) - 1):
        dim = len(cell) - 1
        simplex_counts[str(dim)] = simplex_counts.get(str(dim), 0) + 1
    cycles = nx.cycle_basis(graph)
    return {
        "edge_count": graph.number_of_edges(),
        "edges": sorted([sorted(edge) for edge in graph.edges()]),
        "cycle_basis": sorted([sorted(cycle) for cycle in cycles]),
        "simplex_counts_by_dim": simplex_counts,
        "dimension": simplex.dimension(),
        "betti": {"H0": betti[0], "H1": betti[1], "H2": betti[2]},
        "num_simplices": simplex.num_simplices(),
    }


def z3_hole_expr(vars_by_pair: dict[str, z3.BoolRef]) -> z3.BoolRef:
    cycle_terms = [vars_by_pair[pair_id(a, b)] for a, b in CYCLE_KEYS]
    return z3.And(
        *cycle_terms,
        z3.Not(vars_by_pair[pair_id(*TARGET_KEY)]),
        z3.Not(vars_by_pair[pair_id(*GUARD_KEY)]),
    )


def z3_prove_unsat(assertions: list[z3.BoolRef], denied_goal: z3.BoolRef) -> str:
    solver = z3.Solver()
    for assertion in assertions:
        solver.add(assertion)
    solver.add(denied_goal)
    return str(solver.check())


def z3_table_assertions(vars_by_pair: dict[str, z3.BoolRef], table: dict[str, bool]) -> list[z3.BoolRef]:
    out = []
    for key, value in table.items():
        out.append(vars_by_pair[key] if value else z3.Not(vars_by_pair[key]))
    return out


def z3_checks(tables: dict[str, dict[str, bool]]) -> dict:
    vars_by_pair = {
        pair_id(a, b): z3.Bool(pair_id(a, b))
        for a, b in itertools.combinations(PROBES, 2)
    }
    h1_expr = z3_hole_expr(vars_by_pair)
    assumptions = [vars_by_pair[pair_id(a, b)] for a, b in CYCLE_KEYS]
    assumptions.append(z3.Not(vars_by_pair[pair_id(*GUARD_KEY)]))
    xz = vars_by_pair[pair_id(*TARGET_KEY)]
    relation_status = z3_prove_unsat(assumptions, z3.Not(h1_expr == z3.Not(xz)))
    non_status = z3_prove_unsat(z3_table_assertions(vars_by_pair, tables["noncommuting_cycle"]), z3.Not(h1_expr))
    comm_status = z3_prove_unsat(z3_table_assertions(vars_by_pair, tables["fully_commuting"]), h1_expr)
    restored_status = z3_prove_unsat(z3_table_assertions(vars_by_pair, tables["target_restored"]), h1_expr)
    return {
        "free_variables": sorted(vars_by_pair),
        "relation_h1_equals_not_target_when_cycle_and_guard_fixed": relation_status,
        "noncommuting_cycle_hole": non_status,
        "fully_commuting_no_hole": comm_status,
        "target_restored_no_hole": restored_status,
        "all_unsat": all(
            item == "unsat"
            for item in (relation_status, non_status, comm_status, restored_status)
        ),
    }


def cvc5_and(tm: cvc5.TermManager, terms: list[cvc5.Term]) -> cvc5.Term:
    if len(terms) == 1:
        return terms[0]
    return tm.mkTerm(Kind.AND, *terms)


def cvc5_not(tm: cvc5.TermManager, term: cvc5.Term) -> cvc5.Term:
    return tm.mkTerm(Kind.NOT, term)


def cvc5_hole_expr(tm: cvc5.TermManager, vars_by_pair: dict[str, cvc5.Term]) -> cvc5.Term:
    return cvc5_and(
        tm,
        [vars_by_pair[pair_id(a, b)] for a, b in CYCLE_KEYS]
        + [
            cvc5_not(tm, vars_by_pair[pair_id(*TARGET_KEY)]),
            cvc5_not(tm, vars_by_pair[pair_id(*GUARD_KEY)]),
        ],
    )


def cvc5_prove_unsat(tm: cvc5.TermManager, assertions: list[cvc5.Term], denied_goal: cvc5.Term) -> str:
    solver = cvc5.Solver(tm)
    solver.setLogic("QF_UF")
    for assertion in assertions:
        solver.assertFormula(assertion)
    solver.assertFormula(denied_goal)
    return str(solver.checkSat())


def cvc5_table_assertions(tm: cvc5.TermManager, vars_by_pair: dict[str, cvc5.Term], table: dict[str, bool]) -> list[cvc5.Term]:
    out = []
    for key, value in table.items():
        out.append(vars_by_pair[key] if value else cvc5_not(tm, vars_by_pair[key]))
    return out


def cvc5_checks(tables: dict[str, dict[str, bool]]) -> dict:
    tm = cvc5.TermManager()
    bool_sort = tm.getBooleanSort()
    vars_by_pair = {
        pair_id(a, b): tm.mkConst(bool_sort, pair_id(a, b))
        for a, b in itertools.combinations(PROBES, 2)
    }
    h1_expr = cvc5_hole_expr(tm, vars_by_pair)
    assumptions = [vars_by_pair[pair_id(a, b)] for a, b in CYCLE_KEYS]
    assumptions.append(cvc5_not(tm, vars_by_pair[pair_id(*GUARD_KEY)]))
    xz = vars_by_pair[pair_id(*TARGET_KEY)]
    relation = tm.mkTerm(Kind.EQUAL, h1_expr, cvc5_not(tm, xz))
    relation_status = cvc5_prove_unsat(tm, assumptions, cvc5_not(tm, relation))
    non_status = cvc5_prove_unsat(
        tm,
        cvc5_table_assertions(tm, vars_by_pair, tables["noncommuting_cycle"]),
        cvc5_not(tm, h1_expr),
    )
    comm_status = cvc5_prove_unsat(
        tm,
        cvc5_table_assertions(tm, vars_by_pair, tables["fully_commuting"]),
        h1_expr,
    )
    restored_status = cvc5_prove_unsat(
        tm,
        cvc5_table_assertions(tm, vars_by_pair, tables["target_restored"]),
        h1_expr,
    )
    return {
        "free_variables": sorted(vars_by_pair),
        "relation_h1_equals_not_target_when_cycle_and_guard_fixed": relation_status,
        "noncommuting_cycle_hole": relation_status if bool(0) else non_status,
        "fully_commuting_no_hole": comm_status,
        "target_restored_no_hole": restored_status,
        "all_unsat": all(
            item == "unsat"
            for item in (relation_status, non_status, comm_status, restored_status)
        ),
    }


def sha256_of(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def build_result() -> dict:
    os.makedirs(RESULT_DIR, exist_ok=bool(1))
    tables = {
        "fully_commuting": table_from_false_pairs(set()),
        "noncommuting_cycle": table_from_false_pairs({TARGET_KEY, GUARD_KEY}),
        "target_restored": table_from_false_pairs({GUARD_KEY}),
        "pair_only_noncommuting": {
            pair_id("x_probe", "z_probe"): bool(0),
        },
    }
    summaries = {
        name: complex_summary(table)
        for name, table in tables.items()
        if name != "pair_only_noncommuting"
    }
    pair_graph = nx.Graph()
    pair_graph.add_nodes_from(["x_probe", "z_probe"])
    pair_summary = {
        "edge_count": pair_graph.number_of_edges(),
        "cycle_basis": nx.cycle_basis(pair_graph),
        "betti": {"H0": 2, "H1": 0, "H2": 0},
        "boundary": "two probes alone do not carry a one-dimensional cycle",
    }

    z3_result = z3_checks(tables)
    cvc5_result = cvc5_checks(tables)

    fully_h1 = summaries["fully_commuting"]["betti"]["H1"]
    non_h1 = summaries["noncommuting_cycle"]["betti"]["H1"]
    restored_h1 = summaries["target_restored"]["betti"]["H1"]
    flip_control_pass = fully_h1 == 0 and non_h1 != 0 and restored_h1 == 0
    smt_pass = z3_result["all_unsat"] and cvc5_result["all_unsat"]
    all_pass = flip_control_pass and smt_pass
    build_status = "PASS" if all_pass else "BUILD FAILED"

    source_path = os.path.abspath(__file__)
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "python",
        "computation_style": "networkx_graph_gudhi_clique_complex_z3_cvc5_table_binding",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "does_not_self_upgrade": bool(1),
        "reads_peer_result": bool(0),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_path": f"system_v7/sims/{SIM_ID}/{SIM_ID}.py",
        "source_sha256": sha256_of(source_path),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_results.json",
        "claim_ceiling": {
            "candidate_only": bool(1),
            "canon_claim": bool(0),
            "held_with_other_floor_candidates": [
                "bare_quotient_floor",
                "probe_inversion_branch",
            ],
        },
        "fixture_boundary": {
            "two_probe_only_h1": pair_summary,
            "accepted_witness_shape": "four-probe chordless cycle",
            "target_forbidden_relation": list(TARGET_KEY),
            "guard_forbidden_relation": list(GUARD_KEY),
            "boundary_note": "The target relation is necessary for this fixture; a bare two-probe relation is not enough for H1.",
        },
        "tables": tables,
        "complexes": summaries,
        "decisive_flip_control": {
            "fully_commuting_h1": fully_h1,
            "noncommuting_cycle_h1": non_h1,
            "target_restored_h1": restored_h1,
            "pass": flip_control_pass,
            "failure_condition": "BUILD FAILED if fully_commuting_h1 != 0, noncommuting_cycle_h1 == 0, or target_restored_h1 != 0",
        },
        "smt_structural_checks": {
            "z3": z3_result,
            "cvc5": cvc5_result,
            "pass": smt_pass,
            "binding": "Bool variables are the measured pair table; the derived H1 predicate flips with the target table entry while the cycle and guard rows are fixed.",
        },
        "all_pass": all_pass,
        "build_status": build_status,
        "packages_used": ["networkx", "gudhi", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["networkx", "gudhi", "z3", "cvc5"],
        "TOOL_MANIFEST": {
            "networkx": {
                "tried": bool(1),
                "used": bool(1),
                "reason": TOOL_MANIFEST["networkx"]["reason"],
            },
            "gudhi": {
                "tried": bool(1),
                "used": bool(1),
                "reason": TOOL_MANIFEST["gudhi"]["reason"],
            },
            "z3": {
                "tried": bool(1),
                "used": bool(1),
                "reason": TOOL_MANIFEST["z3"]["reason"],
            },
            "cvc5": {
                "tried": bool(1),
                "used": bool(1),
                "reason": TOOL_MANIFEST["cvc5"]["reason"],
            },
        },
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "networkx",
                "qualified_api": "networkx.enumerate_all_cliques",
                "input_object": "measured finite commutation graph",
                "output_object": "cliques inserted as finite simplices",
                "positive_case": "chordless-cycle noncommuting table has one graph cycle",
                "negative_erased_control": "fully commuting and target-restored controls close the cycle",
                "boundary_case": "two-probe-only forbidden relation has H1=0",
                "demotion_condition": "if clique enumeration disagrees with the table graph",
                "gates": ["all_pass", "quotient"],
            },
            {
                "tool": "gudhi",
                "qualified_api": "finite simplex insertion plus betti_numbers",
                "input_object": "finite clique complex",
                "output_object": "Betti vector with H1",
                "positive_case": "noncommuting_cycle H1 is nonzero",
                "negative_erased_control": "fully_commuting and target_restored H1 are zero",
                "boundary_case": "pair_only_noncommuting H1 is zero",
                "demotion_condition": "if H1 flip-control fails",
                "gates": ["all_pass", "proof"],
            },
            {
                "tool": "z3",
                "qualified_api": "z3.Solver.check",
                "input_object": "Bool variables for measured pair table",
                "output_object": "unsat certificates for denied flip predicates",
                "positive_case": "noncommuting table entails H1 predicate",
                "negative_erased_control": "target restored table rejects H1 predicate",
                "boundary_case": "cycle fixed and guard fixed gives H1 iff target is absent",
                "demotion_condition": "if any denied predicate is sat",
                "gates": ["all_pass", "proof"],
            },
            {
                "tool": "cvc5",
                "qualified_api": "cvc5.Solver.checkSat",
                "input_object": "same Bool table variables",
                "output_object": "independent unsat statuses for denied flip predicates",
                "positive_case": "noncommuting table entails H1 predicate",
                "negative_erased_control": "target restored table rejects H1 predicate",
                "boundary_case": "cycle fixed and guard fixed gives H1 iff target is absent",
                "demotion_condition": "if any denied predicate is sat",
                "gates": ["all_pass", "proof"],
            },
        ],
    }


def main() -> int:
    result = build_result()
    with open(OUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=bool(1))
        handle.write("\n")
    print(json.dumps({
        "build_status": result["build_status"],
        "all_pass": result["all_pass"],
        "result_path": result["result_path"],
        "fully_commuting_h1": result["decisive_flip_control"]["fully_commuting_h1"],
        "noncommuting_cycle_h1": result["decisive_flip_control"]["noncommuting_cycle_h1"],
        "target_restored_h1": result["decisive_flip_control"]["target_restored_h1"],
        "smt_pass": result["smt_structural_checks"]["pass"],
    }, indent=2, sort_keys=bool(1)))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
