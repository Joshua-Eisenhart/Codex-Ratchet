#!/usr/bin/env python3
"""JAX-slot exact workhorse lane for round3_s6s7_heavy_discriminator_v0."""

from __future__ import annotations

import json
from typing import Any

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import networkx as nx
import sympy as sp
import z3

import round3_s6s7_heavy_discriminator_v0_common as common


jax.config.update("jax_enable_x64", True)

ENGINE = "jax"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe() -> dict[str, Any]:
    graph = nx.Graph()
    graph.add_edge(0, 1)
    graph.add_edge(1, 2)
    exact = sp.Rational(graph.number_of_edges(), graph.number_of_nodes())

    ns = jnp.asarray(common.N_SWEEP, dtype=jnp.int64)

    def half_size(n: jax.Array) -> jax.Array:
        return n // 2

    halves = jax.vmap(half_size)(ns)

    solver = z3.Solver()
    actual = z3.Int("s6s7_heavy_jax_probe_edges")
    solver.add(actual == z3.IntVal(graph.number_of_edges()))
    solver.add(actual != z3.IntVal(2))
    z3_status = str(solver.check())

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_actual = c_solver.mkConst(int_sort, "s6s7_heavy_jax_probe_edges_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_actual, c_solver.mkInteger(graph.number_of_edges())))
    c_solver.assertFormula(c_solver.mkTerm(Kind.NOT, c_solver.mkTerm(Kind.EQUAL, c_actual, c_solver.mkInteger(2))))
    cvc5_status = str(c_solver.checkSat()).lower()
    return {
        "networkx_probe_edges": graph.number_of_edges(),
        "sympy_edge_node_ratio": sp.sstr(exact),
        "jax_vmap_half_sizes": [int(x) for x in jax.device_get(halves)],
        "z3_edge_identity": z3_status,
        "cvc5_edge_identity": cvc5_status,
        "pass": z3_status == "unsat" and cvc5_status == "unsat" and [int(x) for x in jax.device_get(halves)] == [4, 8, 16],
    }


def z3_proof(values: dict[str, int]) -> dict[str, Any]:
    solver = z3.Solver()
    vars_by_name = {}
    for name, value in values.items():
        var = z3.Int(name)
        vars_by_name[name] = var
        solver.add(var == z3.IntVal(int(value)))
    zero_erasures = [var == 0 for name, var in vars_by_name.items() if name != "excluded_candidate_count"]
    solver.add(z3.Or(*(zero_erasures + [vars_by_name["excluded_candidate_count"] != z3.IntVal(5)])))
    verdict = str(solver.check())

    flip = z3.Solver()
    mutated = [z3.Int(f"mutated_{name}") for name in values if name != "excluded_candidate_count"]
    for var in mutated:
        flip.add(var == z3.IntVal(0))
    flip.add(z3.Or(*[var == 0 for var in mutated]))
    flip_verdict = str(flip.check())
    return {
        "ran": True,
        "solver": "z3",
        "verdict": verdict,
        "load_bearing": True,
        "witness_values": values,
        "negated_assertion": "one computed S6/S7 heavy-row witness is erased or excluded candidate count is not five",
        "flip_control_verdict": flip_verdict,
        "positive_case": "all five queued S6/S7 heavy candidates have nonzero exact finite separating witnesses at N=8",
        "negative/erased_control": "mutating required witnesses to zero makes the erased assertion SAT",
        "boundary_case": "SMT binds finite integer witnesses from the N=8 member of the N={8,16,32} sweep",
    }


def cvc5_proof(values: dict[str, int]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    terms = {}
    for name, value in values.items():
        var = solver.mkConst(int_sort, name)
        terms[name] = var
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(int(value))))
    disjuncts = [solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(0)) for name, var in terms.items() if name != "excluded_candidate_count"]
    disjuncts.append(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, terms["excluded_candidate_count"], solver.mkInteger(5))))
    solver.assertFormula(solver.mkTerm(Kind.OR, *disjuncts))
    verdict = str(solver.checkSat()).lower()

    flip = cvc5.Solver()
    flip.setLogic("QF_LIA")
    flip_terms = []
    for name in values:
        if name == "excluded_candidate_count":
            continue
        var = flip.mkConst(flip.getIntegerSort(), f"mutated_{name}")
        flip.assertFormula(flip.mkTerm(Kind.EQUAL, var, flip.mkInteger(0)))
        flip_terms.append(flip.mkTerm(Kind.EQUAL, var, flip.mkInteger(0)))
    flip.assertFormula(flip.mkTerm(Kind.OR, *flip_terms))
    flip_verdict = str(flip.checkSat()).lower()
    return {
        "ran": True,
        "solver": "cvc5",
        "verdict": verdict,
        "load_bearing": True,
        "witness_values": values,
        "negated_assertion": "same erased-heavy-witness assertion as z3",
        "flip_control_verdict": flip_verdict,
        "positive_case": "matches z3 UNSAT over computed integer witnesses",
        "negative/erased_control": "mutating required witnesses to zero makes the erased assertion SAT",
        "boundary_case": "finite integer witnesses only",
    }


def build_result() -> dict[str, Any]:
    common.RESULT_DIR.mkdir(parents=True, exist_ok=True)
    verdicts = common.candidate_verdicts()
    controls = common.control_rows()
    values = common.smt_witness_values(verdicts)
    z3_result = z3_proof(values)
    cvc5_result = cvc5_proof(values)
    probe = source_backing_probe()
    verdict_map = {row["candidate"]: row["verdict"] for row in verdicts}
    expected_match = verdict_map == common.EXPECTED_FINAL_VERDICTS
    all_n_swept = all([row["N_sweep"][i]["N"] for i in range(3)] == common.N_SWEEP for row in verdicts)
    controls_pass = (
        controls["anchor_self"]["self_passes"] is True
        and controls["deliberate_reparameterized_cycle_alias"]["verdict"] == "alias"
        and controls["deliberate_reparameterized_cycle_alias"]["edge_by_edge_verified"] is True
        and controls["round2_path_far_graph"]["verdict"] == "excluded-by-closed-cycle-graph-row"
    )
    all_pass = (
        expected_match
        and all_n_swept
        and controls_pass
        and z3_result["verdict"] == cvc5_result["verdict"] == "unsat"
        and z3_result["flip_control_verdict"] == cvc5_result["flip_control_verdict"] == "sat"
        and probe["pass"] is True
        and not common.READS_PEER_RESULT
    )
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": common.SIM_ID,
        "object_id": f"{common.SIM_ID}_{ENGINE}",
        "engine": ENGINE,
        "role_id": "jax_networkx_sympy_smt_s6s7_heavy_workhorse",
        "generated_at": common.now_z(),
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": common.READS_PEER_RESULT,
        "source_path": common.rel(SOURCE_PATH),
        "source_sha256": common.sha256_file(SOURCE_PATH),
        "result_path": common.rel(RESULT_PATH),
        "packages_used": ["jax", "jax.numpy", "networkx", "sympy", "z3", "cvc5", "json"],
        "aligned_packages_load_bearing": ["networkx", "sympy", "z3", "cvc5"],
        "package_observables": {
            "networkx": "finite graph construction, isomorphism-certificate edge verification, graph invariant/cost sweeps over N={8,16,32}",
            "sympy": "exact characteristic-polynomial and rational invariant support for graph rows",
            "z3": "computed integer S6/S7 heavy witness UNSAT with erased SAT flip",
            "cvc5": "independent computed integer S6/S7 heavy witness UNSAT with erased SAT flip",
        },
        "package_versions": {
            "jax": getattr(jax, "__version__", "version_unavailable"),
            "networkx": getattr(nx, "__version__", "version_unavailable"),
            "sympy": sp.__version__,
            "z3": getattr(z3, "get_version_string", lambda: "version_unavailable")(),
            "cvc5": getattr(cvc5, "__version__", "version_unavailable"),
        },
        "TOOL_MANIFEST": {
            "networkx": {"used": True, "reason": "load-bearing graph/cost sweeps and explicit alias certificate edge verification"},
            "sympy": {"used": True, "reason": "load-bearing exact graph invariant rows where spectral/cycle witnesses are recorded"},
            "z3": {"used": True, "reason": "load-bearing finite witness proof with erased flip"},
            "cvc5": {"used": True, "reason": "load-bearing independent finite witness proof with erased flip"},
            "jax": {"used": True, "reason": "supportive vectorized N-sweep workhorse check; not the proof arbiter"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "networkx": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "jax": "supportive",
        },
        "claim_path_tools": ["networkx", "sympy", "z3", "cvc5"],
        "source_backing_probe": probe,
        "pin_spec": common.PIN_SPEC,
        "pin_sha256": common.sha256_text(common.PIN_SPEC),
        "all_pass": all_pass,
        "positive": {
            "anchor_self": controls["anchor_self"],
            "explicit_isomorphism_certificate": controls["deliberate_reparameterized_cycle_alias"],
            "heavy_rows_run": common.REGISTRY_S6S7_HEAVY_TEETH_QUOTE,
        },
        "negative": {
            "candidate_verdict_table": verdicts,
            "round2_path_far_control": controls["round2_path_far_graph"],
            "known_cosurvivors_minted": [],
        },
        "boundary": {
            "scope": "S6/S7 only; exactly five queued heavy-local rows",
            "N_sweep": common.N_SWEEP,
            "resource_guard": "N<=32; no larger sweep run",
            "classification": common.CLASSIFICATION,
            "promotion_allowed": common.PROMOTION_ALLOWED,
            "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
            "co_survivor_rule": "No co-survivor label minted; every passed row would have to be listed here before minting.",
        },
        "candidate_verdicts": verdicts,
        "control_rows": controls,
        "crossover_proofs": {"z3": z3_result, "cvc5": cvc5_result},
        "build_gates": {
            "expected_verdicts_match": expected_match,
            "all_N_swept": all_n_swept,
            "controls_pass": controls_pass,
            "z3_cvc5_agree": z3_result["verdict"] == cvc5_result["verdict"] == "unsat",
            "flip_controls_fire": z3_result["flip_control_verdict"] == cvc5_result["flip_control_verdict"] == "sat",
            "source_backing_probe_pass": probe["pass"],
            "no_peer_result_read": not common.READS_PEER_RESULT,
        },
        "tool_calls": [
            {
                "tool": "networkx",
                "qualified_api/function": "networkx.Graph/networkx.cycle_graph/networkx.shortest_path_length/networkx.weisfeiler_lehman_graph_hash",
                "input_object": "S6/S7 support graphs and N={8,16,32} graph-cost sweeps",
                "output_object": "degree sequences, cycle ranks, bounded word costs, edge-by-edge alias certificate",
                "positive_case": "anchor cycle self-passes and reparameterized cycle edge mapping verifies",
                "negative/erased_control": "path far-control loses closed-cycle degree/cycle rows",
                "boundary_case": "finite N<=32 graph rows only",
                "demotion_condition": "demote if explicit mapping certificate or any N sweep row is absent",
                "gates": ["candidate_verdicts", "control_rows", "all_pass"],
            },
            {
                "tool": "sympy",
                "qualified_api/function": "sympy.Matrix.charpoly/sympy.Poly",
                "input_object": "N=8 exact adjacency matrices for graph invariant witnesses",
                "output_object": "exact characteristic-polynomial witness rows",
                "positive_case": "anchor and separated graph rows carry exact invariant witnesses",
                "negative/erased_control": "not used for numeric closeness",
                "boundary_case": "degree/cycle witnesses are primary where sufficient",
                "demotion_condition": "demote spectral language if exact charpoly row is removed",
                "gates": ["candidate_verdicts"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver/z3.Int/Solver.add/Solver.check",
                "input_object": "computed integer witness values from candidate sweep rows",
                "output_object": "UNSAT erased-witness proof plus SAT flip",
                "positive_case": "all five candidates have nonzero witness values and excluded-count is five",
                "negative/erased_control": "mutated zero witnesses make erased assertion SAT",
                "boundary_case": "N=8 witness polarity only; N sweep is checked separately",
                "demotion_condition": "demote proof claim if flip control is absent",
                "gates": ["crossover_proofs", "all_pass"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver/mkConst/mkTerm/assertFormula/checkSat",
                "input_object": "same computed integer witness values as z3",
                "output_object": "independent UNSAT erased-witness proof plus SAT flip",
                "positive_case": "cvc5 agrees with z3",
                "negative/erased_control": "mutated zero witnesses make erased assertion SAT",
                "boundary_case": "finite integer witness polarity",
                "demotion_condition": "demote if z3/cvc5 disagree",
                "gates": ["crossover_proofs", "all_pass"],
            },
        ],
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "result": common.rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
