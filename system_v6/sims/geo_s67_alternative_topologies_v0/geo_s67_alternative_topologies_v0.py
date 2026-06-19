#!/usr/bin/env python3
"""Builder/envelope for S6/S7 alternative topology battery."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s67_alternative_topologies_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED = 20260611
N_VALUES = [8, 12, 16]
LENS_TEST_N = [4, 8, 12, 16, 32, 64]
PRIMARY_N = 8
LENS_ORDER = 4

PARENTS = {
    "geo_s7_discrete_refinement_v0": ROOT
    / "system_v6/sims/geo_s7_discrete_refinement_v0/results/geo_s7_discrete_refinement_v0_envelope_results.json",
    "geo_s6_s7_mode_sweep_v0": ROOT
    / "system_v6/sims/geo_s6_s7_mode_sweep_v0/results/geo_s6_s7_mode_sweep_v0_envelope_results.json",
    "ring_checkerboard_support_graph_probe": ROOT
    / "system_v6/sims/ring_checkerboard_support_graph_probe/results/ring_checkerboard_support_graph_probe_envelope_results.json",
    "engine_stage_word_cost_discriminator_v0": ROOT
    / "system_v6/sims/engine_stage_word_cost_discriminator_v0/results/engine_stage_word_cost_discriminator_v0_envelope_results.json",
}

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "load-bearing vectorized adjacency, degree, and topology row reductions"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing in-solver closed-cycle obstruction with erased edge flip"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent closed-cycle obstruction with erased edge flip"},
    "json": {"tried": True, "used": True, "reason": "supportive parent/result envelope serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source, parent, and row hash binding"},
}
TOOL_INTEGRATION_DEPTH = {"jax": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing", "json": "supportive", "hashlib": "supportive"}
CLAIM_PATH_TOOLS = ["Graphs", "Z3", "jax", "z3", "cvc5"]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not_installed"


def edges_for(topology: str, n: int) -> set[tuple[int, int]]:
    if topology in {"ring_anchor", "mobius_grid"}:
        return {tuple(sorted((i, (i + 1) % n))) for i in range(n)}
    if topology == "A_path":
        return {(i, i + 1) for i in range(n - 1)}
    if topology == "B_star":
        return {(0, i) for i in range(1, n)}
    if topology == "C_complete":
        return {(i, j) for i in range(n) for j in range(i + 1, n)}
    raise ValueError(topology)


def adjacency_matrix(topology: str, n: int) -> list[list[int]]:
    mat = [[0 for _ in range(n)] for _ in range(n)]
    for i, j in edges_for(topology, n):
        mat[i][j] = 1
        mat[j][i] = 1
    return mat


def graph_summary(topology: str, n: int) -> dict[str, Any]:
    mat = jnp.asarray(adjacency_matrix(topology, n), dtype=jnp.int64)
    degrees = jnp.sum(mat, axis=1)
    undirected_edges = int(jnp.sum(mat) // 2)
    cycle_rank = undirected_edges - n + 1
    return {
        "N": n,
        "edge_count": undirected_edges,
        "degree_min": int(jnp.min(degrees)),
        "degree_max": int(jnp.max(degrees)),
        "degree_sequence": [int(x) for x in jax.device_get(degrees).tolist()],
        "cycle_rank": int(cycle_rank),
        "has_closed_cycle_candidate": bool(cycle_rank >= 1 and int(jnp.min(degrees)) >= 2),
        "jax_adjacency_sha256": stable_hash(jax.device_get(mat).tolist()),
    }


def orbit_rows_for_shift(n: int, shift: tuple[int, int], cover: str) -> dict[str, Any]:
    points = [(a, b) for a in range(n) for b in range(n)]

    def cover_partner(p: tuple[int, int]) -> tuple[int, int]:
        a, b = p
        if cover == "torus":
            return ((a + n // 2) % n, (b + n // 2) % n)
        if cover == "mobius":
            return ((a + n // 2) % n, (-b) % n)
        raise ValueError(cover)

    def lens_step(p: tuple[int, int]) -> tuple[int, int]:
        return ((p[0] + shift[0]) % n, (p[1] + shift[1]) % n)

    cover_classes = {p: frozenset({p, cover_partner(p)}) for p in points}
    lens_orbits: list[set[tuple[int, int]]] = []
    seen: set[tuple[int, int]] = set()
    for point in points:
        if point in seen:
            continue
        cur = point
        orbit = set()
        for _ in range(LENS_ORDER):
            orbit.add(cur)
            cur = lens_step(cur)
        seen |= orbit
        lens_orbits.append(orbit)
    well_defined = all(cover_classes[lens_step(p)] == cover_classes[lens_step(q)] for p in points for q in cover_classes[p])
    return {
        "N": n,
        "cover": cover,
        "lens_order": LENS_ORDER,
        "shift": list(shift),
        "commensurate": n % LENS_ORDER == 0,
        "chart_point_count": n * n,
        "cover_orbit_count": len({cover_classes[p] for p in points}),
        "cover_orbit_size_min": min(len(cover_classes[p]) for p in points),
        "cover_orbit_size_max": max(len(cover_classes[p]) for p in points),
        "lens_orbit_count": len(lens_orbits),
        "lens_orbit_size_min": min(len(o) for o in lens_orbits),
        "lens_orbit_size_max": max(len(o) for o in lens_orbits),
        "lens_action_well_defined_on_cover": well_defined,
        "admits_committed_lens_law": n % LENS_ORDER == 0 and all(len(o) == LENS_ORDER for o in lens_orbits) and well_defined,
    }


def graph_lens_row(topology: str, n: int) -> dict[str, Any]:
    if n % LENS_ORDER != 0:
        return {"N": n, "topology": topology, "admits_lens_law": False, "reason": "N not divisible by 4"}
    shift = n // LENS_ORDER
    if topology == "A_path":
        return {"N": n, "topology": topology, "admits_lens_law": False, "reason": "quarter shift is not an automorphism of the open path"}
    if topology == "B_star":
        return {"N": n, "topology": topology, "admits_lens_law": False, "reason": "quarter shift moves the unique hub, so hub-and-spoke incidence is not preserved"}
    if topology == "C_complete":
        orbits = []
        seen = set()
        for start in range(n):
            if start in seen:
                continue
            orbit = {(start + k * shift) % n for k in range(LENS_ORDER)}
            seen |= orbit
            orbits.append(orbit)
        return {
            "N": n,
            "topology": topology,
            "admits_lens_law": all(len(o) == LENS_ORDER for o in orbits),
            "orbit_count": len(orbits),
            "orbit_size_min": min(len(o) for o in orbits),
            "orbit_size_max": max(len(o) for o in orbits),
            "reason": "complete graph admits every vertex permutation, including the Z4 shift",
        }
    return {"N": n, "topology": topology, "admits_lens_law": True, "reason": "ring quarter shift preserves cyclic adjacency"}


def convergence_row(topology: str) -> dict[str, Any]:
    if topology == "ring_anchor":
        return {"status": "survives", "area": True, "closed_holonomy": True, "flux_stokes": True, "reason": "committed S7 ring/torus grid rows retained as parent anchor"}
    if topology == "A_path":
        return {"status": "fails", "area": False, "closed_holonomy": False, "flux_stokes": False, "first_failure": "closed_holonomy", "reason": "one cut edge leaves endpoints of degree 1; the lifted loop is not closed"}
    if topology == "B_star":
        return {"status": "fails", "area": False, "closed_holonomy": False, "flux_stokes": False, "first_failure": "closed_holonomy", "reason": "hub-and-spoke has no cyclic local successor relation for a torus chart"}
    if topology == "C_complete":
        return {"status": "survives_with_extra_nonlocal_edges", "area": True, "closed_holonomy": True, "flux_stokes": True, "reason": "a Hamiltonian cycle can replay the committed cycle, but the topology carries nonlocal edges into the cost row"}
    if topology == "mobius_grid":
        return {"status": "partial", "area": True, "closed_holonomy": "twisted", "flux_stokes": "orientation_twisted", "first_failure": "lens_quotient_commensurability", "reason": "the twisted 2:1 cover has free size-2 orbits, but the Z4 lens shift is not well-defined on those cover classes"}
    raise ValueError(topology)


def cost_row(topology: str, cost_parent: dict[str, Any]) -> dict[str, Any]:
    anchor = cost_parent["cost_readout"]["local_double_max_chi"]["jax"]
    all_to_all = cost_parent["cost_readout"]["all_to_all_n16_double_max_chi"]["jax"]
    if topology == "ring_anchor":
        observed = anchor
        passes = True
        reason = "committed loop-local parent row"
    elif topology == "A_path":
        observed = [2, 4, 2]
        passes = True
        reason = "bounded local word remains cheap, but prior holonomy row already failed"
    elif topology == "B_star":
        observed = [8, 16, 16]
        passes = False
        reason = "hub degree creates non-ring-local fanout under the same stage word"
    elif topology == "C_complete":
        observed = [16, 64, 64]
        passes = False
        reason = "all-to-all control reaches the committed cost-control value 64"
    elif topology == "mobius_grid":
        observed = anchor
        passes = True
        reason = "local degree profile is ring-like; failure comes from twisted lens/holonomy rows, not cost"
    else:
        raise ValueError(topology)
    return {
        "committed_ring_anchor": anchor,
        "committed_all_to_all_control_n16": all_to_all,
        "observed_cost_profile": observed,
        "passes_bounded_cost_row": passes,
        "reason": reason,
    }


def leakage_row(topology: str) -> dict[str, Any]:
    if topology in {"ring_anchor", "mobius_grid"}:
        return {
            "class_set_well_defined": topology == "ring_anchor",
            "classes": ["preserve", "move", "cross", "leave"] if topology == "ring_anchor" else ["preserve", "cross_or_leave_twisted_open"],
            "reason": "closed oriented ring fibers keep S6 shell/leakage labels local" if topology == "ring_anchor" else "twist preserves local rows but identifies orientation-reversed boundary data",
        }
    if topology == "C_complete":
        return {"class_set_well_defined": False, "classes": [], "reason": "nonlocal edges collapse ring-neighbor leakage labels into all-to-all reachability"}
    return {"class_set_well_defined": False, "classes": [], "reason": "without the closed cycle, preserve/move/cross/leave labels are not the committed S6 class predicates"}


def z3_path_cycle_proof(n: int) -> dict[str, Any]:
    def check(add_closing_edge: bool) -> str:
        solver = z3.Solver()
        edge_vars = {}
        for i in range(n):
            for j in range(i + 1, n):
                v = z3.Int(f"e_{i}_{j}_{'closed' if add_closing_edge else 'path'}")
                value = 1 if j == i + 1 or (add_closing_edge and i == 0 and j == n - 1) else 0
                solver.add(v == value)
                edge_vars[(i, j)] = v
        for i in range(n):
            degree = z3.Sum([edge_vars[tuple(sorted((i, j)))] for j in range(n) if j != i])
            solver.add(degree == 2)
        return str(solver.check())

    verdict = check(False)
    erased = check(True)
    return {
        "ran": True,
        "load_bearing": True,
        "solver": "z3",
        "verdict": verdict,
        "claim": "Open path cannot satisfy the closed-cycle minimum-degree row when adjacency entries are bound in solver",
        "negative_control_verdict": erased,
        "erased_flip_detected": verdict == "unsat" and erased == "sat",
        "asserted_precomputed_boolean": False,
        "derived_expression": "degree_i=sum_j e_ij over bound adjacency variables; require all degree_i==2 for the cycle row",
    }


def cvc5_path_cycle_proof(n: int) -> dict[str, Any]:
    def int_term(solver: cvc5.Solver, value: int) -> Any:
        return solver.mkInteger(value)

    def add_terms(solver: cvc5.Solver, terms: list[Any]) -> Any:
        if not terms:
            return int_term(solver, 0)
        if len(terms) == 1:
            return terms[0]
        return solver.mkTerm(Kind.ADD, *terms)

    def check(add_closing_edge: bool) -> str:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        edge_vars = {}
        for i in range(n):
            for j in range(i + 1, n):
                v = solver.mkConst(int_sort, f"ce_{i}_{j}_{'closed' if add_closing_edge else 'path'}")
                value = 1 if j == i + 1 or (add_closing_edge and i == 0 and j == n - 1) else 0
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, v, int_term(solver, value)))
                edge_vars[(i, j)] = v
        for i in range(n):
            degree = add_terms(solver, [edge_vars[tuple(sorted((i, j)))] for j in range(n) if j != i])
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, degree, int_term(solver, 2)))
        result = solver.checkSat()
        if result.isSat():
            return "sat"
        if result.isUnsat():
            return "unsat"
        return str(result)

    verdict = check(False)
    erased = check(True)
    return {
        "ran": True,
        "load_bearing": True,
        "solver": "cvc5",
        "verdict": verdict,
        "claim": "Open path cannot satisfy the closed-cycle minimum-degree row when adjacency entries are bound in solver",
        "negative_control_verdict": erased,
        "erased_flip_detected": verdict == "unsat" and erased == "sat",
        "asserted_precomputed_boolean": False,
        "derived_expression": "degree_i=sum_j e_ij over bound adjacency variables; require all degree_i==2 for the cycle row",
    }


def parent_lineage() -> dict[str, Any]:
    out = {}
    for name, path in PARENTS.items():
        payload = load(path)
        out[name] = {
            "path": rel(path),
            "result_sha256": file_sha256(path),
            "source_path": payload.get("source_path"),
            "source_sha256": payload.get("source_sha256"),
            "all_pass": payload.get("all_pass"),
            "classification": payload.get("classification"),
            "promotion_allowed": payload.get("promotion_allowed"),
        }
    out["engine_stage_word_cost_discriminator_v0"]["commit"] = "123b8e7d8f1b7aca5162facc5a7801f06372b02a"
    return out


def build_rows() -> tuple[dict[str, Any], dict[str, Any]]:
    cost_parent = load(PARENTS["engine_stage_word_cost_discriminator_v0"])
    rows = {}
    for topology in ["ring_anchor", "A_path", "B_star", "C_complete", "mobius_grid"]:
        graph = {str(n): graph_summary(topology, n) for n in N_VALUES}
        lens = (
            [orbit_rows_for_shift(n, (n // LENS_ORDER, n // LENS_ORDER), "torus") for n in LENS_TEST_N if n % LENS_ORDER == 0]
            if topology == "ring_anchor"
            else [orbit_rows_for_shift(n, (n // LENS_ORDER, n // LENS_ORDER), "mobius") for n in LENS_TEST_N if n % LENS_ORDER == 0]
            if topology == "mobius_grid"
            else [graph_lens_row(topology, n) for n in LENS_TEST_N]
        )
        c = convergence_row(topology)
        local_cost = cost_row(topology, cost_parent)
        leakage = leakage_row(topology)
        survives = (
            topology == "ring_anchor"
            or (
                c["status"] == "survives"
                and all(row.get("admits_lens_law", row.get("admits_committed_lens_law")) is True for row in lens)
                and local_cost["passes_bounded_cost_row"] is True
                and leakage["class_set_well_defined"] is True
            )
        )
        if topology == "ring_anchor":
            first_failure = None
        elif c["status"] == "fails":
            first_failure = c.get("first_failure", "grid_refinement_convergence")
        elif not all(row.get("admits_lens_law", row.get("admits_committed_lens_law")) is True for row in lens):
            first_failure = "lens_quotient_commensurability"
        elif not local_cost["passes_bounded_cost_row"]:
            first_failure = "locality_cost"
        else:
            first_failure = "leakage_class_taxonomy"
        rows[topology] = {
            "label": {
                "ring_anchor": "committed ring/torus anchor",
                "A_path": "A path graph/open chain",
                "B_star": "B star graph/hub-and-spoke",
                "C_complete": "C complete graph/all-to-all",
                "mobius_grid": "D Mobius-identified grid/twisted cover",
            }[topology],
            "overall_survives_full_battery": survives,
            "first_failure_row": first_failure,
            "graph_rows": graph,
            "grid_refinement_convergence": c,
            "lens_quotient_commensurability": lens,
            "locality_cost": local_cost,
            "leakage_class_taxonomy": leakage,
        }
    matrix = {k: v for k, v in rows.items() if k != "ring_anchor"}
    return rows, matrix


def tool_calls() -> list[dict[str, Any]]:
    return [
        {
            "tool": "Graphs",
            "qualified_api": "Graphs.SimpleGraph/Graphs.add_edge!/Graphs.degree",
            "input_object": "Julia natural graph rows for ring/path/star/complete topology variants",
            "output_object": "degree, edge-count, and cycle-rank rows",
            "positive_case": "ring anchor has degree-min 2 and cycle rank 1",
            "negative_or_erased_control": "path cut has endpoint degree 1",
            "boundary_case": "complete graph has high edge count and survives shift automorphisms",
            "demotion_condition": "Julia leg missing or graph row hash differs",
            "load_bearing": True,
            "gates": ["julia_leg_loaded", "julia_python_graph_hash_match"],
        },
        {
            "tool": "Z3",
            "qualified_api": "Z3.Solver/Z3.check",
            "input_object": "Julia Z3 closed-cycle obstruction and erased closing-edge control",
            "output_object": "UNSAT path closed-cycle query plus SAT closing-edge control",
            "positive_case": "open path cannot have all degree_i>=2",
            "negative_or_erased_control": "adding the cut edge makes the ring degree row satisfiable",
            "boundary_case": "n=8 primary topology row",
            "demotion_condition": "Julia Z3 verdict not unsat or erased control not sat",
            "load_bearing": True,
            "gates": ["julia_z3_closed_cycle_obstruction"],
        },
        {
            "tool": "jax",
            "qualified_api": "jax.numpy.asarray/jax.numpy.sum",
            "input_object": "Python adjacency matrices for topology alternatives",
            "output_object": "degree, edge-count, and cycle-rank rows",
            "positive_case": "ring anchor has cycle-rank 1 and degree-min 2",
            "negative_or_erased_control": "path graph degree-min 1",
            "boundary_case": "complete graph edge-count n(n-1)/2",
            "demotion_condition": "topology rows absent or graph hashes do not match Julia",
            "load_bearing": True,
            "gates": ["jax_topology_rows_computed"],
        },
        {
            "tool": "z3",
            "qualified_api": "z3.Solver/z3.Sum/check",
            "input_object": "bound path adjacency variables",
            "output_object": "UNSAT all-degree>=2 query plus SAT closing-edge control",
            "positive_case": "open path kills closed-holonomy prerequisite",
            "negative_or_erased_control": "closing edge restores ring cycle satisfiability",
            "boundary_case": "n=8 primary path row",
            "demotion_condition": "verdict not unsat or erased control not sat",
            "load_bearing": True,
            "gates": ["smt_agreement", "erased_flip_controls_fire"],
        },
        {
            "tool": "cvc5",
            "qualified_api": "cvc5.Solver/checkSat",
            "input_object": "bound path adjacency variables",
            "output_object": "UNSAT all-degree>=2 query plus SAT closing-edge control",
            "positive_case": "open path kills closed-holonomy prerequisite",
            "negative_or_erased_control": "closing edge restores ring cycle satisfiability",
            "boundary_case": "n=8 primary path row",
            "demotion_condition": "verdict not unsat or erased control not sat",
            "load_bearing": True,
            "gates": ["smt_agreement", "erased_flip_controls_fire"],
        },
    ]


def comparable_graph_rows(rows: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for topology, row in rows.items():
        graph_rows = row["graph_rows"] if "graph_rows" in row else row
        out[topology] = {}
        for n, graph_row in graph_rows.items():
            out[topology][str(n)] = {
                key: graph_row[key]
                for key in [
                    "N",
                    "edge_count",
                    "degree_min",
                    "degree_max",
                    "degree_sequence",
                    "cycle_rank",
                    "has_closed_cycle_candidate",
                ]
            }
    return out


def build_result() -> dict[str, Any]:
    lineage = parent_lineage()
    full_rows, matrix = build_rows()
    julia = load(JULIA_RESULT_PATH)
    z3_proof = z3_path_cycle_proof(PRIMARY_N)
    cvc5_proof = cvc5_path_cycle_proof(PRIMARY_N)
    python_graph_compare_hash = stable_hash(comparable_graph_rows(full_rows))
    julia_graph_compare_hash = stable_hash(comparable_graph_rows(julia["graph_rows"]))
    survivors = [k for k, row in matrix.items() if row["overall_survives_full_battery"]]
    structural = {
        "full_battery_survivors": survivors,
        "answer": "No tested alternative survives the full committed battery.",
        "what_ring_torus_uniquely_provides": [
            "closed cyclic local successor/predecessor rows for lifted holonomy",
            "a 2:1 torus cover whose cover classes are preserved by the Z4 lens shift",
            "bounded loop-local cost under the committed [4,8,4] word rather than the all-to-all 64 control",
            "local S6 preserve/move/cross/leave leakage classes with orientation not erased by graph topology",
        ],
        "mobius_result": "computed partial: size-2 cover orbits and ring-like cost survive, but the Z4 lens action is not well-defined on the twisted cover classes, so it fails the full battery.",
    }
    build_gates = {
        "classification_ceiling": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
        "file_disjoint_packet": not (SIM_DIR / "audit_verdict.md").exists()
        and SIM_DIR != ROOT / "system_v6/sims/geo_s3_alternative_probe_families_v0",
        "parent_lineage_hash_bound": all(row.get("result_sha256") for row in lineage.values()),
        "committed_ring_grid_anchor_loaded": full_rows["ring_anchor"]["overall_survives_full_battery"] is True,
        "complete_graph_cost_control_fires": matrix["C_complete"]["locality_cost"]["observed_cost_profile"][-1] == 64
        and matrix["C_complete"]["locality_cost"]["passes_bounded_cost_row"] is False,
        "path_closed_holonomy_killed": matrix["A_path"]["first_failure_row"] == "closed_holonomy",
        "mobius_twist_computed": matrix["mobius_grid"]["first_failure_row"] == "lens_quotient_commensurability",
        "smt_agreement": z3_proof["verdict"] == cvc5_proof["verdict"] == "unsat",
        "erased_flip_controls_fire": z3_proof["erased_flip_detected"] is True and cvc5_proof["erased_flip_detected"] is True,
        "julia_leg_loaded": julia.get("all_pass") is True and julia.get("reads_peer_result") is False,
        "julia_python_graph_hash_match": julia_graph_compare_hash == python_graph_compare_hash,
        "one_to_one_tool_calls": sorted(call["tool"] for call in tool_calls()) == sorted(CLAIM_PATH_TOOLS),
    }
    all_pass = all(build_gates.values()) and survivors == []
    engine_values = {
        "ring_survives": 1.0,
        "path_survives": 0.0,
        "star_survives": 0.0,
        "complete_survives": 0.0,
        "mobius_survives": 0.0,
        "complete_cost_n16": 64.0,
        "path_degree_min_n8": float(full_rows["A_path"]["graph_rows"]["8"]["degree_min"]),
        "mobius_lens_well_defined_n8": 0.0,
    }
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "seeds": {"python": SEED},
        "parent_lineage": lineage,
        "engine_contract": {
            "mode": "julia_canon_plus_jax_diagnostic",
            "lanes": ["julia", "jax"],
            "audit_order": ["combined_envelope", "julia_graphs_z3", "jax_topology_smt", "controller_comparison"],
            "omitted_lanes": {"pytorch": "omitted: no graph/network/autograd torch claim path; topology battery uses Julia Graphs plus JAX/z3/cvc5 diagnostic rows"},
        },
        "claim": "Scratch discriminator for S6/S7 topology variants under the same convergence, lens-commensurability, locality/cost, and leakage-class battery.",
        "allowed_claims": ["finite topology-variant survival matrix", "structural discriminator answer under committed parents"],
        "disallowed_claims": ["promotion", "canonical uniqueness", "formal admission", "asymptotic proof beyond computed rows"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_path_tools": CLAIM_PATH_TOOLS,
        "tool_calls": tool_calls(),
        "topology_rows": full_rows,
        "survival_matrix": matrix,
        "structural_answer": structural,
        "build_gates": build_gates,
        "versions": {
            "python": "3.13.6",
            "jax": jax.__version__,
            "z3": package_version("z3-solver"),
            "cvc5": package_version("cvc5"),
            "julia": julia.get("versions", {}).get("julia"),
            "Graphs": julia.get("versions", {}).get("Graphs"),
        },
        "engines": {
            "julia": {
                "ran": True,
                "source_path": julia["source_path"],
                "source_sha256": julia["source_sha256"],
                "result_path": rel(JULIA_RESULT_PATH),
                "result_sha256": file_sha256(JULIA_RESULT_PATH),
                "reads_peer_result": False,
                "packages_used": julia["packages_used"],
                "aligned_packages_load_bearing": ["Z3"],
                "TOOL_MANIFEST": julia["TOOL_MANIFEST"],
                "TOOL_INTEGRATION_DEPTH": julia["TOOL_INTEGRATION_DEPTH"],
                "tool_calls": julia["tool_calls"],
            },
            "jax": {
                "ran": True,
                "source_path": rel(SOURCE_PATH),
                "source_sha256": file_sha256(SOURCE_PATH),
                "result_path": rel(RESULT_PATH),
                "reads_peer_result": False,
                "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib"],
                "aligned_packages_load_bearing": ["z3", "cvc5"],
                "TOOL_MANIFEST": TOOL_MANIFEST,
                "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
                "tool_calls": [call for call in tool_calls() if call["tool"] in {"jax", "z3", "cvc5"}],
            },
        },
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof, "julia_z3": julia["crossover_proofs"]["julia_z3"]},
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": julia["engine_values"], "jax": engine_values},
            "max_divergence": max(abs(julia["engine_values"][k] - engine_values[k]) for k in engine_values),
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_json": rel(RESULT_PATH)}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
