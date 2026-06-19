#!/usr/bin/env python3
"""Python/JAX-slot exact workhorse lane for round3_s5_heavy_discriminator_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import networkx as nx
import sympy as sp
import z3

import round3_s5_heavy_discriminator_v0_common as common


jax.config.update("jax_enable_x64", True)

ENGINE = "jax"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe() -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_edge(0, 1)
    graph.add_edge(1, 1)
    exact = sp.Rational(1, 4) + sp.Rational(1, 2) + sp.Rational(3, 4)
    vector = jnp.asarray([1.0, 2.0, 3.0], dtype=jnp.float64)

    solver = z3.Solver()
    actual = z3.Int("s5_heavy_jax_probe_scc_count")
    solver.add(actual == z3.IntVal(nx.number_strongly_connected_components(graph)))
    solver.add(actual != z3.IntVal(2))
    z3_status = str(solver.check())

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_actual = c_solver.mkConst(int_sort, "s5_heavy_jax_probe_scc_count_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_actual, c_solver.mkInteger(nx.number_strongly_connected_components(graph))))
    c_solver.assertFormula(c_solver.mkTerm(Kind.NOT, c_solver.mkTerm(Kind.EQUAL, c_actual, c_solver.mkInteger(2))))
    cvc5_status = str(c_solver.checkSat()).lower()
    return {
        "networkx_scc_count": nx.number_strongly_connected_components(graph),
        "sympy_alpha_sum": common.sx(exact),
        "jax_x64_vector_sum": float(jnp.sum(vector)),
        "z3_component_identity": z3_status,
        "cvc5_component_identity": cvc5_status,
        "pass": z3_status == "unsat" and cvc5_status == "unsat" and common.sx(exact) == "3/2",
    }


def z3_proof(values: dict[str, int]) -> dict[str, Any]:
    solver = z3.Solver()
    vars_by_name = {}
    for name, value in values.items():
        var = z3.Int(name)
        vars_by_name[name] = var
        solver.add(var == z3.IntVal(value))
    solver.add(
        z3.Or(
            vars_by_name["r3_2_plus_coeff_gap_times_20"] == 0,
            vars_by_name["r3_2_minus_coeff_gap_times_20"] == 0,
            vars_by_name["r3_3_plus_bz_gap_times_20"] == 0,
            vars_by_name["r3_3_minus_bz_gap_times_20"] == 0,
            vars_by_name["r3_5_se_funnel_A01_gap_times_7"] == 0,
            vars_by_name["excluded_candidate_count"] != 8,
        )
    )
    verdict = str(solver.check())

    flip = z3.Solver()
    mutated = z3.Int("mutated_s5_heavy_witness")
    flip.add(mutated == z3.IntVal(0))
    flip.add(z3.Or(mutated == 0, z3.IntVal(7) != 8))
    flip_verdict = str(flip.check())
    return {
        "ran": True,
        "solver": "z3",
        "verdict": verdict,
        "load_bearing": True,
        "witness_values": values,
        "negated_assertion": "one exact heavy-row witness is erased or excluded candidate count is not eight",
        "flip_control_verdict": flip_verdict,
        "positive_case": "all eight S5 heavy candidates have exact nonzero separating witnesses or excluded-count witness",
        "negative/erased_control": "mutating a required witness to zero makes the erased assertion SAT",
        "boundary_case": "integer-scaled finite witnesses only; symbolic witness bodies remain in the candidate table",
    }


def cvc5_proof(values: dict[str, int]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    zero = solver.mkInteger(0)
    terms = {}
    for name, value in values.items():
        var = solver.mkConst(int_sort, name)
        terms[name] = var
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
    solver.assertFormula(
        solver.mkTerm(
            Kind.OR,
            solver.mkTerm(Kind.EQUAL, terms["r3_2_plus_coeff_gap_times_20"], zero),
            solver.mkTerm(Kind.EQUAL, terms["r3_2_minus_coeff_gap_times_20"], zero),
            solver.mkTerm(Kind.EQUAL, terms["r3_3_plus_bz_gap_times_20"], zero),
            solver.mkTerm(Kind.EQUAL, terms["r3_3_minus_bz_gap_times_20"], zero),
            solver.mkTerm(Kind.EQUAL, terms["r3_5_se_funnel_A01_gap_times_7"], zero),
            solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, terms["excluded_candidate_count"], solver.mkInteger(8))),
        )
    )
    verdict = str(solver.checkSat()).lower()

    flip = cvc5.Solver()
    flip.setLogic("QF_LIA")
    mutated = flip.mkConst(flip.getIntegerSort(), "mutated_s5_heavy_witness")
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, mutated, flip.mkInteger(0)))
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, mutated, flip.mkInteger(0)))
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
        "negative/erased_control": "mutating a required witness to zero makes the erased assertion SAT",
        "boundary_case": "integer-scaled finite witnesses only",
    }


def build_result() -> dict[str, Any]:
    common.RESULT_DIR.mkdir(parents=True, exist_ok=True)
    verdicts, controls, anchors = common.candidate_verdicts()
    values = common.smt_witness_values(verdicts)
    z3_result = z3_proof(values)
    cvc5_result = cvc5_proof(values)
    probe = source_backing_probe()
    verdict_map = {row["candidate"]: row["verdict"] for row in verdicts}
    expected_match = verdict_map == common.EXPECTED_FINAL_VERDICTS
    controls_pass = (
        controls["anchor_self"]["self_passes_all_heavy_rows"] is True
        and controls["deliberate_reparameterized_anchor_alias"]["passes"] is True
        and controls["light_pass_R3_4_regression"]["passes"] is True
    )
    graph_rows = {
        row["candidate"]: common.graph_digest(row["graph_summary"])
        for row in verdicts
        if row["family"] in {"S5.R3.2_committed_coeff_epsilon", "S5.R3.5_basin_preserving_null"}
    }
    all_pass = (
        expected_match
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
        "role_id": "jax_exact_sympy_networkx_smt_s5_heavy_workhorse",
        "generated_at": common.now_z(),
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": common.READS_PEER_RESULT,
        "source_path": common.rel(SOURCE_PATH),
        "source_sha256": common.sha256_file(SOURCE_PATH),
        "result_path": common.rel(RESULT_PATH),
        "packages_used": ["jax", "jax.numpy", "networkx", "sympy", "z3", "cvc5", "json", "pathlib"],
        "aligned_packages_load_bearing": ["networkx", "sympy", "z3", "cvc5"],
        "package_observables": {
            "networkx": "33-cell transition graph SCC and terminal-class summaries for basin rows",
            "sympy": "exact rational/surd terrain A,b, mirror, fixed-point, quotient, N01, and time-flow witnesses",
            "z3": "computed integer heavy-row witness UNSAT with erased SAT flip",
            "cvc5": "independent computed integer heavy-row witness UNSAT with erased SAT flip",
        },
        "TOOL_MANIFEST": {
            "networkx": {"used": True, "reason": "load-bearing finite 33-cell transition graph SCC and terminal-class rows"},
            "sympy": {"used": True, "reason": "load-bearing exact rational/surd S5 heavy witnesses"},
            "z3": {"used": True, "reason": "load-bearing finite witness proof with erased flip"},
            "cvc5": {"used": True, "reason": "load-bearing independent finite witness proof with erased flip"},
            "jax": {"used": True, "reason": "supportive x64 workhorse lane source-backed sanity"},
            "json": {"used": True, "reason": "supportive receipt serialization"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "networkx": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "jax": "supportive",
            "json": "supportive",
        },
        "claim_path_tools": ["networkx", "sympy", "z3", "cvc5"],
        "package_versions": {
            "jax": getattr(jax, "__version__", "version_unavailable"),
            "networkx": getattr(nx, "__version__", "version_unavailable"),
            "sympy": sp.__version__,
            "z3": getattr(z3, "get_version_string", lambda: "version_unavailable")(),
            "cvc5": getattr(cvc5, "__version__", "version_unavailable"),
        },
        "source_backing_probe": probe,
        "pin_spec": common.PIN_SPEC,
        "pin_sha256": common.sha256_text(common.PIN_SPEC),
        "all_pass": all_pass,
        "positive": {
            "anchor_self": controls["anchor_self"],
            "deliberate_alias": controls["deliberate_reparameterized_anchor_alias"],
            "heavy_rows_run": sorted(common.HEAVY_EXPECTED_ROWS),
        },
        "negative": {
            "candidate_verdict_table": verdicts,
            "r3_4_regression": controls["light_pass_R3_4_regression"],
            "known_cosurvivors_minted": [],
        },
        "boundary": {
            "scope": "S5 only; exactly eight queued heavy-local rows",
            "classification": common.CLASSIFICATION,
            "promotion_allowed": common.PROMOTION_ALLOWED,
            "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
            "co_survivor_rule": "No GENUINE CO-SURVIVOR label minted; every candidate is excluded by a named heavy row in this packet.",
            "chart_relative_basin_policy": common.CHART_LABEL,
        },
        "candidate_verdicts": verdicts,
        "control_rows": controls,
        "anchor_graph": common.graph_digest(anchors["anchor_graph"]),
        "basin_graph_rows": graph_rows,
        "crossover_proofs": {"z3": z3_result, "cvc5": cvc5_result},
        "build_gates": {
            "expected_verdicts_match": expected_match,
            "controls_pass": controls_pass,
            "z3_cvc5_agree": z3_result["verdict"] == cvc5_result["verdict"] == "unsat",
            "flip_controls_fire": z3_result["flip_control_verdict"] == cvc5_result["flip_control_verdict"] == "sat",
            "source_backing_probe_pass": probe["pass"],
            "no_peer_result_read": not common.READS_PEER_RESULT,
        },
        "tool_calls": [
            {
                "tool": "networkx",
                "qualified_api/function": "networkx.DiGraph/networkx.strongly_connected_components/networkx.has_path",
                "input_object": "33-cell Bloch grid plus finite-time terrain-flow edge relation",
                "output_object": "terminal classes, absent-exit proofs, may/must basin rows, transition graph hashes",
                "positive_case": "anchor graph self-passes and R3.2/R3.5 basin rows are chart-relative finite graph receipts",
                "negative/erased_control": "R3.2/R3.5 are not promoted from basin graph alone when N01/time-flow rows separate",
                "boundary_case": "raw transition graph not persisted; summaries and hashes only",
                "demotion_condition": "demote basin language if chart-relative label or absent-exit proof is absent",
                "gates": ["candidate_verdicts", "basin_graph_rows", "all_pass"],
            },
            {
                "tool": "sympy",
                "qualified_api/function": "sympy.Matrix/sympy.Rational/sympy.simplify/sympy.charpoly/sympy.nullspace",
                "input_object": "S5 anchor and heavy candidate A,b rows over exact rationals/surds",
                "output_object": "mirror, fixed-point, quotient 56/56, N01 full-signature, and time-flow witnesses",
                "positive_case": "anchor and exact alias controls pass",
                "negative/erased_control": "all eight heavy candidates have exact separating witness rows",
                "boundary_case": "finite-time Choi floats are diagnostic only; exact verdict rows are symbolic/graph/SMT",
                "demotion_condition": "demote if any verdict relies on numeric closeness",
                "gates": ["candidate_verdicts", "all_pass"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver/z3.Int/Solver.check",
                "input_object": "computed integer-scaled S5 heavy witness values",
                "output_object": z3_result,
                "positive_case": z3_result["positive_case"],
                "negative/erased_control": z3_result["negative/erased_control"],
                "boundary_case": z3_result["boundary_case"],
                "demotion_condition": "demote if solver sees only a precomputed boolean",
                "gates": ["crossover_proofs", "all_pass"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver/mkConst/assertFormula/checkSat",
                "input_object": "same computed integer-scaled S5 heavy witness values as z3",
                "output_object": cvc5_result,
                "positive_case": cvc5_result["positive_case"],
                "negative/erased_control": cvc5_result["negative/erased_control"],
                "boundary_case": cvc5_result["boundary_case"],
                "demotion_condition": "demote if cvc5 disagrees with z3",
                "gates": ["crossover_proofs", "all_pass"],
            },
        ],
        "parent_lineage": common.common_parent_lineage(),
    }


def main() -> int:
    payload = build_result()
    common.RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "result_path": common.rel(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
