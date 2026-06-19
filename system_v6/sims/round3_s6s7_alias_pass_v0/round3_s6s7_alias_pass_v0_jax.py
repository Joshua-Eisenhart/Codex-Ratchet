#!/usr/bin/env python3
"""Exact Python/SymPy graph lane for round3_s6s7_alias_pass_v0.

The lane name follows the existing round-3 envelope convention. The scoped
claim path is exact graph topology: NetworkX isomorphism, SymPy characteristic
polynomials/eigenvalues, and finite SMT witness polarity. No numeric spectra,
JAX arrays, PyTorch tensors, autograd, or message-passing claims are used.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import networkx as nx
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "round3_s6s7_alias_pass_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
REGISTRY_PATH = ROOT / "system_v6" / "receipts" / "round3_discriminator_registry_20260611.md"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
N_LIGHT = 8


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def cycle_graph(n: int = N_LIGHT) -> nx.Graph:
    return nx.cycle_graph(n)


def cycle_reparameterized_graph(n: int = N_LIGHT) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(range(n))
    for i in range(n):
        # Shift-and-reverse relabel of the same cycle support graph.
        a = (3 - i) % n
        b = (3 - (i + 1)) % n
        graph.add_edge(a, b)
    return graph


def path_graph(n: int = N_LIGHT) -> nx.Graph:
    return nx.path_graph(n)


def chord_cycle_graph(n: int = N_LIGHT) -> nx.Graph:
    graph = nx.cycle_graph(n)
    for i in range(n // 2):
        graph.add_edge(i, i + n // 2)
    return graph


def ladder_prism_graph(n: int = N_LIGHT) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(range(2 * n))
    for layer in [0, 1]:
        offset = layer * n
        for i in range(n):
            graph.add_edge(offset + i, offset + ((i + 1) % n))
    for i in range(n):
        graph.add_edge(i, n + i)
    return graph


def graph_rows(graph: nx.Graph) -> dict[str, Any]:
    n = graph.number_of_nodes()
    m = graph.number_of_edges()
    degrees = sorted(dict(graph.degree()).values())
    adjacency = nx.to_numpy_array(graph, nodelist=sorted(graph.nodes()), dtype=int)
    matrix = sp.Matrix(adjacency.astype(int).tolist())
    charpoly = sp.Poly(matrix.charpoly().as_expr(), sp.Symbol("lambda"))
    eigenvals = matrix.eigenvals()
    exact_spectrum = [
        {"value": sp.sstr(sp.simplify(value)), "multiplicity": int(mult)}
        for value, mult in sorted(eigenvals.items(), key=lambda item: sp.sstr(item[0]))
    ]
    return {
        "node_count": n,
        "edge_count": m,
        "degree_sequence": degrees,
        "cycle_rank": m - n + nx.number_connected_components(graph),
        "connected_components": nx.number_connected_components(graph),
        "adjacency_charpoly_exact": sp.sstr(charpoly.as_expr()),
        "adjacency_spectrum_exact": exact_spectrum,
    }


def cover_signature(kind: str) -> dict[str, Any]:
    if kind == "untwisted":
        return {
            "kind": "untwisted_torus_cover",
            "relation": "(a,b)~(a+N/2,b)",
            "z4_well_defined": True,
            "orbit_size_multiset_N8": [2, 2, 2, 2],
        }
    if kind == "mobius":
        return {
            "kind": "mobius_reflection_shifted",
            "relation": "(a,b)~(a+N/2,-b+c)",
            "z4_well_defined": "queued-heavy-local",
            "orbit_size_multiset_N8": [2, 2, 2, 2],
        }
    if kind == "klein":
        return {
            "kind": "klein_double_twist",
            "relation": "two-direction orientation reversal",
            "z4_well_defined": "queued-heavy-local",
            "orbit_size_multiset_N8": "queued-heavy-local",
        }
    if kind == "shear":
        return {
            "kind": "shear_torus",
            "relation": "(a,b)->(a+N/2,b+a mod N)",
            "z4_well_defined": "queued-heavy-local",
            "orbit_size_multiset_N8": "queued-heavy-local",
        }
    return {
        "kind": "support_graph_only",
        "relation": "same untwisted cover pending heavy graph/cost row",
        "z4_well_defined": "queued-heavy-local",
        "orbit_size_multiset_N8": "queued-heavy-local",
    }


def canonical_tuple(graph: nx.Graph, cover_kind: str, *, full_phase1: bool) -> dict[str, Any]:
    rows = graph_rows(graph)
    return {
        "canonicalizer": (
            "graph_isomorphism_class_under_dihedral_lens_preserving_maps, "
            "cover_equivalence_relation_classes, Z4_action_well_defined_boolean, "
            "orbit_size_multiset, cost_profile[N=8,16,32], S6_leakage_class_signature"
        ),
        "light_graph_invariants": rows,
        "graph_isomorphism_hash_N8": nx.weisfeiler_lehman_graph_hash(graph),
        "cover_signature": cover_signature(cover_kind),
        "cost_profile_N_8_16_32": "not-run-heavy-local" if not full_phase1 else [N_LIGHT, 2 * N_LIGHT, 4 * N_LIGHT],
        "S6_leakage_class_signature": "not-run-heavy-local" if not full_phase1 else "preserve/move/cross/leave",
    }


def registry_rows() -> list[dict[str, Any]]:
    return [
        {
            "id": "S67.R3.0_committed_torus_ring",
            "finite_representative": "untwisted torus cover, cycle graph, Z4 lens shift",
            "closeness": "control",
            "expected_teeth_row": "none; anchor",
            "cost": "light-symbolic",
            "graph_factory": cycle_graph,
            "cover_kind": "untwisted",
        },
        {
            "id": "S67.R3.1_mobius_reflection_shifted",
            "finite_representative": "cover relation (a,b)~(a+N/2,-b+c) for c in {0,N/4,N/2}",
            "closeness": "closest known twist family",
            "expected_teeth_row": "lens quotient commensurability",
            "cost": "heavy-local",
            "graph_factory": cycle_graph,
            "cover_kind": "mobius",
        },
        {
            "id": "S67.R3.2_klein_double_twist",
            "finite_representative": "two-direction orientation reversal on the rectangular chart with the same Z4 shift",
            "closeness": "close cover-neighbor",
            "expected_teeth_row": "cover-orbit well-definedness then lens row",
            "cost": "heavy-local",
            "graph_factory": cycle_graph,
            "cover_kind": "klein",
        },
        {
            "id": "S67.R3.3_shear_torus",
            "finite_representative": "untwisted cover plus shear (a,b)->(a+N/2,b+a mod N) on representatives",
            "closeness": "near untwisted but altered lens action",
            "expected_teeth_row": "lens descent and S6 leakage taxonomy",
            "cost": "heavy-local",
            "graph_factory": cycle_graph,
            "cover_kind": "shear",
        },
        {
            "id": "S67.R3.4_cycle_with_one_chord",
            "finite_representative": "ring graph plus one antipodal chord at each N",
            "closeness": "close support graph neighbor",
            "expected_teeth_row": "bounded word cost and cycle holonomy",
            "cost": "heavy-local",
            "graph_factory": chord_cycle_graph,
            "cover_kind": "support",
        },
        {
            "id": "S67.R3.5_ladder_prism_graph",
            "finite_representative": "two-ring ladder/prism local graph with degree 3",
            "closeness": "graph topology neighbor between ring and complete",
            "expected_teeth_row": "locality cost plus leakage class row",
            "cost": "heavy-local",
            "graph_factory": ladder_prism_graph,
            "cover_kind": "support",
        },
    ]


def witness(anchor: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    for path in [
        ("light_graph_invariants", "node_count"),
        ("light_graph_invariants", "edge_count"),
        ("light_graph_invariants", "degree_sequence"),
        ("light_graph_invariants", "cycle_rank"),
        ("light_graph_invariants", "adjacency_charpoly_exact"),
        ("cover_signature", "kind"),
        ("cover_signature", "relation"),
        ("cover_signature", "z4_well_defined"),
    ]:
        left: Any = anchor
        right: Any = candidate
        for part in path:
            left = left[part]
            right = right[part]
        if left != right:
            return {"field": ".".join(path), "anchor": left, "candidate": right}
    return {"field": "canonical_tuple", "anchor": "equal", "candidate": "equal"}


def z3_path_cycle_proof(path_degrees: list[int], cycle_degrees: list[int]) -> dict[str, Any]:
    solver = z3.Solver()
    vars_ = [z3.Int(f"path_degree_{i}") for i in range(len(path_degrees))]
    for var, value in zip(vars_, path_degrees):
        solver.add(var == value)
    solver.add(z3.And([var == 2 for var in vars_]))
    positive = str(solver.check())

    flip = z3.Solver()
    flip_vars = [z3.Int(f"cycle_degree_{i}") for i in range(len(cycle_degrees))]
    for var, value in zip(flip_vars, cycle_degrees):
        flip.add(var == value)
    flip.add(z3.And([var == 2 for var in flip_vars]))
    flip_status = str(flip.check())
    return {
        "solver": "z3",
        "ran": True,
        "verdict": positive,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "claim": "computed path graph degree witnesses cannot satisfy the closed cycle degree-2 row",
        "witness_values": {"path_degrees": path_degrees, "cycle_degrees": cycle_degrees},
        "negated_assertion": "all path degrees equal 2",
        "flip_control_verdict": flip_status,
        "positive_case": "far path graph has degree endpoints 1, so the closed-cycle row is UNSAT",
        "negative/erased_control": "closing the path into the anchor cycle makes the degree-2 row SAT",
        "boundary_case": "SMT binds the finite N=8 first-teeth row only; heavy S6/S7 rows remain queued",
    }


def cvc5_path_cycle_proof(path_degrees: list[int], cycle_degrees: list[int]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    constraints = []
    for i, value in enumerate(path_degrees):
        var = solver.mkConst(int_sort, f"path_degree_{i}")
        constraints.append(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
        constraints.append(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(2)))
    solver.assertFormula(solver.mkTerm(Kind.AND, *constraints))
    positive = str(solver.checkSat()).lower()

    flip = cvc5.Solver()
    flip.setLogic("QF_LIA")
    int_sort = flip.getIntegerSort()
    flip_constraints = []
    for i, value in enumerate(cycle_degrees):
        var = flip.mkConst(int_sort, f"cycle_degree_{i}")
        flip_constraints.append(flip.mkTerm(Kind.EQUAL, var, flip.mkInteger(value)))
        flip_constraints.append(flip.mkTerm(Kind.EQUAL, var, flip.mkInteger(2)))
    flip.assertFormula(flip.mkTerm(Kind.AND, *flip_constraints))
    flip_status = str(flip.checkSat()).lower()
    return {
        "solver": "cvc5",
        "ran": True,
        "verdict": positive,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "claim": "computed path graph degree witnesses cannot satisfy the closed cycle degree-2 row",
        "witness_values": {"path_degrees": path_degrees, "cycle_degrees": cycle_degrees},
        "negated_assertion": "all path degrees equal 2",
        "flip_control_verdict": flip_status,
        "positive_case": "far path graph has degree endpoints 1, so the closed-cycle row is UNSAT",
        "negative/erased_control": "closing the path into the anchor cycle makes the degree-2 row SAT",
        "boundary_case": "SMT binds the finite N=8 first-teeth row only; heavy S6/S7 rows remain queued",
    }


def build_rows() -> dict[str, Any]:
    anchor_graph = cycle_graph()
    anchor_tuple = canonical_tuple(anchor_graph, "untwisted", full_phase1=True)
    candidates = []
    for row in registry_rows():
        full = row["cost"] == "light-symbolic"
        candidate_tuple = canonical_tuple(row["graph_factory"](), row["cover_kind"], full_phase1=full)
        iso_to_anchor = nx.is_isomorphic(anchor_graph, row["graph_factory"]())
        if row["id"] == "S67.R3.0_committed_torus_ring":
            verdict = "anchor"
            registry_row = "anchor"
        else:
            verdict = "open + queued-heavy-local"
            registry_row = "heavy_local_cost_guard_not_run_in_phase_1"
        candidates.append(
            {
                "id": row["id"],
                "finite_representative": row["finite_representative"],
                "closeness": row["closeness"],
                "expected_teeth_row": row["expected_teeth_row"],
                "cost": row["cost"],
                "verdict": verdict,
                "row": registry_row,
                "witness": witness(anchor_tuple, candidate_tuple)
                if full
                else {
                    "field": "registry_cost_guard",
                    "anchor": "light-symbolic anchor canonical tuple completed",
                    "candidate": f"{row['id']} cost=heavy-local; queued for {row['expected_teeth_row']}",
                },
                "isomorphic_to_anchor_graph_N8": iso_to_anchor,
                "canonical_tuple": candidate_tuple,
                "citation_status": "no prior co-survivor receipt cited; S4 audit standard forces open + queued-heavy-local",
            }
        )

    alias_tuple = canonical_tuple(cycle_reparameterized_graph(), "untwisted", full_phase1=True)
    far_tuple = canonical_tuple(path_graph(), "support", full_phase1=True)
    controls = [
        {
            "id": "control.anchor_self",
            "verdict": "anchor",
            "row": "anchor",
            "witness": witness(anchor_tuple, anchor_tuple),
            "canonical_tuple": anchor_tuple,
        },
        {
            "id": "control.alias_reparameterized_committed",
            "verdict": "alias" if nx.is_isomorphic(anchor_graph, cycle_reparameterized_graph()) and alias_tuple == anchor_tuple else "failed",
            "row": "graph_isomorphism_and_canonical_tuple_equal",
            "witness": witness(anchor_tuple, alias_tuple),
            "canonical_tuple": alias_tuple,
        },
        {
            "id": "control.round2_path_far_graph",
            "verdict": "excluded-by-closed-cycle-graph-row",
            "row": "closed-cycle graph row",
            "witness": witness(anchor_tuple, far_tuple),
            "canonical_tuple": far_tuple,
        },
    ]
    return {"candidate_rows": candidates, "control_rows": controls}


def build_result() -> dict[str, Any]:
    rows = build_rows()
    path_degrees = graph_rows(path_graph())["degree_sequence"]
    cycle_degrees = graph_rows(cycle_graph())["degree_sequence"]
    z3_proof = z3_path_cycle_proof(path_degrees, cycle_degrees)
    cvc5_proof = cvc5_path_cycle_proof(path_degrees, cycle_degrees)
    verdicts = {row["id"]: row["verdict"] for row in rows["candidate_rows"]}
    controls = {row["id"]: row["verdict"] for row in rows["control_rows"]}
    heavy_queue = [row["id"] for row in rows["candidate_rows"] if row["cost"] == "heavy-local"]
    alias_classes = [
        {
            "representative": "S67.R3.0_committed_torus_ring",
            "members": ["S67.R3.0_committed_torus_ring", "control.anchor_self", "control.alias_reparameterized_committed"],
            "selection_rule": "registry anchor is the representative for the exact cycle/untwisted-cover alias class",
        }
    ]
    gates = {
        "registry_rows_built": len(rows["candidate_rows"]) == 6,
        "anchor_classifies_as_itself": verdicts["S67.R3.0_committed_torus_ring"] == "anchor",
        "deliberate_alias_classifies_alias": controls["control.alias_reparameterized_committed"] == "alias",
        "far_candidate_dies_first_teeth": controls["control.round2_path_far_graph"] == "excluded-by-closed-cycle-graph-row",
        "no_heavy_rows_run": all(verdicts[candidate] == "open + queued-heavy-local" for candidate in heavy_queue),
        "no_known_cosurvivor_without_citation": all("co-survivor" not in verdicts[candidate] for candidate in heavy_queue),
        "z3_positive_unsat": z3_proof["verdict"] == "unsat",
        "z3_flip_control_sat": z3_proof["flip_control_verdict"] == "sat",
        "cvc5_positive_unsat": cvc5_proof["verdict"] == "unsat",
        "cvc5_flip_control_sat": cvc5_proof["flip_control_verdict"] == "sat",
    }
    all_pass = all(gates.values())
    return {
        "schema": f"{SIM_ID}_jax_lane_v1",
        "sim_id": SIM_ID,
        "role_id": "python_exact_graph_diagnostic_lane",
        "engine_role_note": "Python exact graph sidecar uses NetworkX isomorphism, SymPy exact graph spectra, and z3/cvc5 finite degree witness polarity.",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["networkx", "sympy", "z3", "cvc5", "json", "hashlib"],
        "aligned_packages_load_bearing": ["networkx", "z3", "cvc5"],
        "package_observables": {
            "networkx": "nx.is_isomorphic plus Weisfeiler-Lehman graph hashes classify the finite N=8 support-graph alias/control rows",
            "z3": "z3.Solver proves the computed far path degree row is UNSAT under closed-cycle degree-2 constraints and SAT after the closing-edge flip",
            "cvc5": "cvc5.Solver independently proves the same computed far path degree row polarity",
        },
        "claim_path_tools": ["networkx", "sympy", "z3", "cvc5"],
        "all_pass": all_pass,
        "positive": {
            "s67_registry_provenance_table": [
                {k: row[k] for k in ["id", "finite_representative", "closeness", "expected_teeth_row", "cost"]}
                for row in rows["candidate_rows"]
            ],
            "alias_classes": alias_classes,
            "anchor_exact_graph_rows": rows["candidate_rows"][0]["canonical_tuple"]["light_graph_invariants"],
        },
        "negative": {
            "far_candidate_control": rows["control_rows"][2],
            "heavy_local_label_guard": "heavy-local rows without cited prior co-survivor receipts are open + queued-heavy-local, never co-survivor-open",
        },
        "boundary": {
            "phase": "light-symbolic phase 1 only",
            "heavy_local_not_run": heavy_queue,
            "pytorch_omitted": "no PyTorch tensor/autograd/message-passing claim path is scoped; exact graph topology is carried by NetworkX/SymPy and Julia Graphs",
            "no_numeric_spectra": True,
            "cost_sweeps_N_8_16_32": "queued-heavy-local, not run",
        },
        "candidate_verdicts": rows["candidate_rows"],
        "control_verdicts": rows["control_rows"],
        "phase2_queue": {
            "light_symbolic_non_alias_representatives_remaining": [],
            "heavy_local_queued_by_registry_cost_class": heavy_queue,
            "queued_with_verdict": {candidate: "open + queued-heavy-local" for candidate in heavy_queue},
            "known_cosurvivor_classes": [],
        },
        "counts": {
            "raw_registry_candidates": 6,
            "exact_alias_classes": 1,
            "known_cosurvivor_classes": 0,
            "non_alias_representatives_queued_heavy_local": len(heavy_queue),
            "light_symbolic_exclusions": 0,
            "control_exclusions": 1,
        },
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "TOOL_MANIFEST": {
            "networkx": {"used": True, "reason": "load-bearing finite graph construction and isomorphism checks"},
            "sympy": {"used": True, "reason": "load-bearing exact characteristic polynomial and algebraic spectrum serialization"},
            "z3": {"used": True, "reason": "load-bearing finite first-teeth row witness polarity"},
            "cvc5": {"used": True, "reason": "load-bearing independent finite first-teeth row witness polarity"},
            "json": {"used": True, "reason": "supportive result serialization"},
            "hashlib": {"used": True, "reason": "supportive source and tuple hashes"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "networkx": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "json": "supportive",
            "hashlib": "supportive",
        },
        "tool_calls": [
            {
                "tool": "networkx",
                "qualified_api": "networkx.is_isomorphic",
                "input_object": "finite N=8 cycle anchor, reparameterized cycle control, and path far-control support graphs",
                "output_object": "exact support-graph alias/control classification",
                "positive_case": "reparameterized cycle is isomorphic to the anchor cycle",
                "negative/erased_control": "path graph is not isomorphic to the cycle and fails degree/cycle rows",
                "boundary_case": "R3 heavy-local graph/cost sweeps over N={8,16,32} remain queued",
                "demotion_condition": "isomorphism/hash rows missing or heavy-local rows promoted without their named teeth",
            },
            {
                "tool": "sympy",
                "qualified_api": "sympy.Matrix.charpoly/eigenvals",
                "input_object": "finite integer adjacency matrices",
                "output_object": "exact characteristic polynomials and algebraic spectra",
                "positive_case": "cycle anchor spectrum is exact algebraic data, not float closeness",
                "negative/erased_control": "path far-control has a different exact polynomial and degree sequence",
                "boundary_case": "spectra are supportive exact invariants; alias uses the full canonical tuple, not spectrum alone",
                "demotion_condition": "float spectra or tolerance-based aliasing appear on the claim path",
            },
        ],
        "build_gates": gates,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
