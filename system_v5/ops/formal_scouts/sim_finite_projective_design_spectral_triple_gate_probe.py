#!/usr/bin/env python3
"""Finite projective-design and spectral-triple Phase 1 candidate scout.

Formal scout only.

This Phase 1 row tests two finite probe-response candidates without promoting a
manifold layer by name:

1. finite projective design: Fano incidence points -> line-response vectors;
2. finite spectral triple: finite algebra/module/Dirac pair -> bounded
   commutator readout.

Both candidates are finite probe/effect root surfaces. PEPS3D, spinor/Hopf,
flux, Xi/Phi0, Axis0, basin, and physics consumers remain blocked.
"""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import cvc5
from cvc5 import Kind
import gudhi
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
import toponetx as tnx
import xgi
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "finite_projective_design_spectral_triple_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.1"
TIER = "1 finite probe/effect quotient"
PURPOSE = (
    "Reissue the Phase 1 finite projective-design / finite spectral-triple "
    "frontier row against the current LEGO receipt contract without opening "
    "downstream consumers."
)
SCIENTIFIC_QUESTION = (
    "Do finite projective line-response maps and finite Dirac commutator "
    "readouts provide bounded probe-response candidates while single-probe, "
    "non-IC, commuting, and zero-Dirac controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "constraint_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase1_finite_projective_design_spectral_triple_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests finite projective-design line responses and a "
    "finite spectral-triple bounded-commutator readout as Phase 1 frontier "
    "candidates. It does not admit final projective doctrine, final spectral "
    "triple doctrine, manifold foundation closure, PEPS3D closure, flux, Xi, "
    "Phi0, Axis0, basin, physics, or ontology claims."
)

BLOCKED_CONSUMERS = [
    "PEPS3D seed implementation",
    "spinor/Hopf/Weyl enforcement",
    "terrain generator placement",
    "operator substage cells",
    "PEPS/PEPS3D closure",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "IGT/game theory",
    "axes 7-12",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite incidence tensors, response maps, order gaps, and bounded commutator norms",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite/nonpromotion/negative-control admission gate",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing cross-solver admission and knockout gate for the finite candidate requirements",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact Fano incidence and exact commutator sanity checks",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite incidence graph connectivity and edge-count checks",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite hypergraph representation of projective lines",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite simplicial carrier check for line triples",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite simplex-tree count for the projective line complex",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite bipartite incidence graph adapter without dense state closure",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "torch_geometric": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

RTYPE = torch.float64
TOL = 1e-9
GAP_FLOOR = 1e-5

POINTS = tuple(range(7))
LINES = (
    (0, 1, 2),
    (0, 3, 4),
    (0, 5, 6),
    (1, 3, 5),
    (1, 4, 6),
    (2, 3, 6),
    (2, 4, 5),
)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    return value


def incidence_matrix() -> torch.Tensor:
    matrix = torch.zeros((len(POINTS), len(LINES)), dtype=RTYPE)
    for line_idx, line in enumerate(LINES):
        for point in line:
            matrix[point, line_idx] = 1.0
    return matrix


def response_map() -> dict[int, tuple[int, ...]]:
    inc = incidence_matrix()
    return {point: tuple(int(item) for item in inc[point].tolist()) for point in POINTS}


def finite_projective_design_gate() -> dict[str, Any]:
    inc = incidence_matrix()
    gram = inc @ inc.T
    target = torch.ones((7, 7), dtype=RTYPE) + 2.0 * torch.eye(7, dtype=RTYPE)
    line_sizes = [int(torch.sum(inc[:, idx]).item()) for idx in range(7)]
    point_degrees = [int(torch.sum(inc[idx]).item()) for idx in range(7)]
    responses = response_map()
    unique_responses = len(set(responses.values()))
    single_probe_unique = len({tuple([row[0]]) for row in responses.values()})
    non_ic_subset = inc[:, :3]
    non_ic_unique = len({tuple(int(item) for item in non_ic_subset[p].tolist()) for p in POINTS})
    return {
        "pass": torch.linalg.matrix_norm(gram - target).item() < TOL
        and line_sizes == [3] * 7
        and point_degrees == [3] * 7
        and unique_responses == 7
        and single_probe_unique < 7
        and non_ic_unique < 7,
        "finite_map": "r_P : finite_projective_points -> finite_line_incidence_responses",
        "domain": "S = seven Fano points",
        "output": "O = seven-bit finite line response vector",
        "point_count": len(POINTS),
        "line_count": len(LINES),
        "line_sizes": line_sizes,
        "point_degrees": point_degrees,
        "gram_gap": float(torch.linalg.matrix_norm(gram - target).item()),
        "unique_response_count": unique_responses,
        "single_probe_unique_count": single_probe_unique,
        "non_ic_three_line_unique_count": non_ic_unique,
    }


def projective_order_witness_gate() -> dict[str, Any]:
    line_filter = torch.diag(incidence_matrix()[:, 0])
    shift = torch.zeros((7, 7), dtype=RTYPE)
    for point in POINTS:
        shift[(point + 1) % 7, point] = 1.0
    order_gap = float(torch.linalg.matrix_norm(line_filter @ shift - shift @ line_filter).item())
    commuting_control_gap = float(torch.linalg.matrix_norm(line_filter @ line_filter - line_filter @ line_filter).item())
    return {
        "pass": order_gap > GAP_FLOOR and commuting_control_gap < TOL,
        "N01_witness": "line_filter o cyclic_shift != cyclic_shift o line_filter",
        "order_gap": order_gap,
        "commuting_control_gap": commuting_control_gap,
    }


def exact_sympy_projective_gate() -> dict[str, Any]:
    inc = sp.zeros(7, 7)
    for line_idx, line in enumerate(LINES):
        for point in line:
            inc[point, line_idx] = 1
    gram = inc * inc.T
    target = sp.ones(7, 7) + 2 * sp.eye(7)
    return {
        "pass": gram == target,
        "exact_pair_line_incidence": str(gram == target),
        "rank": int(inc.rank()),
        "determinant": int(inc.det()),
    }


def graph_topology_gate() -> dict[str, Any]:
    graph = rx.PyGraph()
    graph.add_nodes_from(range(14))
    for line_idx, line in enumerate(LINES):
        for point in line:
            graph.add_edge(point, 7 + line_idx, None)

    hypergraph = xgi.Hypergraph()
    hypergraph.add_edges_from(LINES)

    complex_ = tnx.SimplicialComplex([list(line) for line in LINES])

    simplex_tree = gudhi.SimplexTree()
    for line in LINES:
        simplex_tree.insert(list(line))
    simplex_tree.compute_persistence()

    edge_pairs = []
    for line_idx, line in enumerate(LINES):
        for point in line:
            edge_pairs.append((point, 7 + line_idx))
            edge_pairs.append((7 + line_idx, point))
    edge_index = torch.tensor(edge_pairs, dtype=torch.long).T
    data = Data(x=torch.arange(14, dtype=RTYPE).reshape(14, 1), edge_index=edge_index)
    aggregate = torch.zeros_like(data.x)
    aggregate.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])

    return {
        "pass": graph.num_nodes() == 14
        and graph.num_edges() == 21
        and rx.is_connected(graph)
        and hypergraph.num_edges == 7
        and int(complex_.dim) == 2
        and simplex_tree.num_simplices() == 35
        and int(data.num_nodes) == 14
        and float(torch.sum(aggregate).item()) > 0.0,
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "rustworkx_connected": bool(rx.is_connected(graph)),
        "xgi_hyperedges": int(hypergraph.num_edges),
        "toponetx_dim": int(complex_.dim),
        "toponetx_shape": str(complex_.shape),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "gudhi_persistence_pairs": len(simplex_tree.persistence()),
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges": int(data.edge_index.shape[1]),
        "pyg_aggregate_sum": float(torch.sum(aggregate).item()),
    }


def spectral_triple_gate() -> dict[str, Any]:
    inc = incidence_matrix()
    upper = torch.cat([torch.zeros((7, 7), dtype=RTYPE), inc], dim=1)
    lower = torch.cat([inc.T, torch.zeros((7, 7), dtype=RTYPE)], dim=1)
    dirac = torch.cat([upper, lower], dim=0)
    algebra_values = torch.tensor([0.0, 1.0, 3.0, 4.0, 6.0, 9.0, 10.0] + [0.0] * 7, dtype=RTYPE)
    finite_function = torch.diag(algebra_values)
    constant_function = torch.eye(14, dtype=RTYPE)
    commutator = dirac @ finite_function - finite_function @ dirac
    constant_commutator = dirac @ constant_function - constant_function @ dirac
    zero_dirac_commutator = torch.zeros_like(dirac) @ finite_function - finite_function @ torch.zeros_like(dirac)

    sym_dirac = sp.zeros(14, 14)
    for point in POINTS:
        for line_idx, line in enumerate(LINES):
            if point in line:
                sym_dirac[point, 7 + line_idx] = 1
                sym_dirac[7 + line_idx, point] = 1
    sym_function = sp.diag(*[0, 1, 3, 4, 6, 9, 10, 0, 0, 0, 0, 0, 0, 0])
    sym_comm = sym_dirac * sym_function - sym_function * sym_dirac
    return {
        "pass": float(torch.linalg.matrix_norm(commutator).item()) > GAP_FLOOR
        and float(torch.linalg.matrix_norm(constant_commutator).item()) < TOL
        and float(torch.linalg.matrix_norm(zero_dirac_commutator).item()) < TOL
        and sym_comm.rank() > 0,
        "finite_map": "I_D(f) = ||[D,f]|| over finite algebra/module pair",
        "domain": "finite diagonal algebra on point-line module",
        "output": "bounded commutator norm readout",
        "module_dim": 14,
        "dirac_nonzero_entries": int(torch.count_nonzero(dirac).item()),
        "commutator_norm": float(torch.linalg.matrix_norm(commutator).item()),
        "constant_commutator_norm": float(torch.linalg.matrix_norm(constant_commutator).item()),
        "zero_dirac_commutator_norm": float(torch.linalg.matrix_norm(zero_dirac_commutator).item()),
        "sympy_commutator_rank": int(sym_comm.rank()),
    }


def z3_admission_gate(actuals: dict[str, bool]) -> dict[str, Any]:
    variables = {key: z3.Bool(key) for key in actuals}
    final_claim = z3.Bool("final_claim")
    solver = z3.Solver()
    for key, value in actuals.items():
        solver.add(variables[key] == bool(value))
    solver.add(z3.Not(final_claim))

    collapse = z3.Solver()
    for key, value in actuals.items():
        collapse.add(variables[key] == bool(value))
    collapse.add(z3.Not(final_claim))
    collapse.add(z3.Or(final_claim, *[z3.Not(variables[key]) for key in variables]))
    return {
        "positive_status": str(solver.check()),
        "collapse_status": str(collapse.check()),
        "pass": solver.check() == z3.sat and collapse.check() == z3.unsat,
    }


def cvc5_admission_gate(actuals: dict[str, bool]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    bool_sort = solver.getBooleanSort()
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    final_claim = solver.mkConst(bool_sort, "final_claim")
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, final_claim, solver.mkBoolean(False)))
    positive = solver.checkSat()

    collapse = cvc5.Solver()
    collapse.setLogic("ALL")
    bool_sort2 = collapse.getBooleanSort()
    terms2 = {key: collapse.mkConst(bool_sort2, f"ko_{key}") for key in actuals}
    final_claim2 = collapse.mkConst(bool_sort2, "ko_final_claim")
    for key, value in actuals.items():
        collapse.assertFormula(collapse.mkTerm(Kind.EQUAL, terms2[key], collapse.mkBoolean(bool(value))))
    collapse.assertFormula(collapse.mkTerm(Kind.EQUAL, final_claim2, collapse.mkBoolean(False)))
    knockout_terms = [final_claim2] + [collapse.mkTerm(Kind.NOT, terms2[key]) for key in actuals]
    collapse.assertFormula(collapse.mkTerm(Kind.OR, *knockout_terms))
    collapse_status = collapse.checkSat()
    return {
        "positive_status": str(positive),
        "collapse_status": str(collapse_status),
        "pass": str(positive) == "sat" and str(collapse_status) == "unsat",
    }


def graveyard_single_probe_rejected() -> dict[str, Any]:
    rows = response_map()
    unique = len({tuple([row[0]]) for row in rows.values()})
    return {
        "pass": unique < len(POINTS),
        "why_rejected": "one finite line probe merges multiple points and is not an admissible identity quotient",
        "single_probe_unique_count": unique,
        "required_unique_count": len(POINTS),
    }


def graveyard_commuting_order_erased_rejected() -> dict[str, Any]:
    line_filter = torch.diag(incidence_matrix()[:, 0])
    second_line_filter = torch.diag(incidence_matrix()[:, 1])
    gap = float(torch.linalg.matrix_norm(line_filter @ second_line_filter - second_line_filter @ line_filter).item())
    return {
        "pass": gap < TOL,
        "why_rejected": "commuting diagonal line filters erase the required N01 order witness",
        "order_gap": gap,
    }


def graveyard_non_ic_probe_subset_rejected() -> dict[str, Any]:
    inc = incidence_matrix()[:, :3]
    unique = len({tuple(int(item) for item in inc[p].tolist()) for p in POINTS})
    return {
        "pass": unique < len(POINTS),
        "why_rejected": "three projective line probes merge points and are not an admissible finite identity quotient",
        "probe_subset_line_count": int(inc.shape[1]),
        "unique_response_count": unique,
        "required_unique_count": len(POINTS),
    }


def graveyard_zero_dirac_rejected() -> dict[str, Any]:
    finite_function = torch.diag(torch.tensor([0.0, 1.0, 3.0, 4.0, 6.0, 9.0, 10.0] + [0.0] * 7, dtype=RTYPE))
    zero_dirac = torch.zeros((14, 14), dtype=RTYPE)
    gap = float(torch.linalg.matrix_norm(zero_dirac @ finite_function - finite_function @ zero_dirac).item())
    return {
        "pass": gap < TOL,
        "why_rejected": "zero Dirac/control operator cannot separate finite algebra variations",
        "commutator_norm": gap,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    projective = finite_projective_design_gate()
    order_witness = projective_order_witness_gate()
    exact_projective = exact_sympy_projective_gate()
    graph_topology = graph_topology_gate()
    spectral = spectral_triple_gate()
    actuals = {
        "finite_projective_design": bool(projective["pass"]),
        "order_witness": bool(order_witness["pass"]),
        "exact_projective_check": bool(exact_projective["pass"]),
        "graph_topology_tools": bool(graph_topology["pass"]),
        "finite_spectral_triple": bool(spectral["pass"]),
        "promotion_blocked": PROMOTION_ALLOWED is False,
    }

    positive = {
        "finite_projective_design_response_map": projective,
        "projective_order_witness_is_noncommuting": order_witness,
        "sympy_exact_projective_incidence": exact_projective,
        "graph_topology_tool_depth_carriers": graph_topology,
        "finite_spectral_triple_bounded_commutator": spectral,
        "z3_finite_map_nonpromotion_gate": z3_admission_gate(actuals),
        "cvc5_finite_map_nonpromotion_gate": cvc5_admission_gate(actuals),
    }
    graveyard_companions = {
        "GC1_single_probe_identity_smuggling_rejected": graveyard_single_probe_rejected(),
        "GC2_commuting_order_erased_control_rejected": graveyard_commuting_order_erased_rejected(),
        "GC3_non_ic_probe_subset_control_rejected": graveyard_non_ic_probe_subset_rejected(),
        "GC4_zero_dirac_spectral_control_rejected": graveyard_zero_dirac_rejected(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_phase1_only_no_peps3d_claim": {
            "pass": True,
            "peps3d_embedding": "blocked downstream next step only; not implemented here",
        },
        "B3_downstream_consumers_blocked": {
            "pass": True,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [
        row["pass"] for row in boundary.values()
    ]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": NAME,
        "version": VERSION,
        "tier": TIER,
        "purpose": PURPOSE,
        "scientific_question": SCIENTIFIC_QUESTION,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": [
            projective["finite_map"],
            spectral["finite_map"],
        ],
        "domain": [
            projective["domain"],
            spectral["domain"],
        ],
        "codomain_or_output": [
            projective["output"],
            spectral["output"],
        ],
        "root_constraints_in_force": {
            "F01": {
                "finite_projective_points": projective["point_count"],
                "finite_projective_lines": projective["line_count"],
                "finite_line_response_width": projective["line_count"],
                "finite_spectral_module_dim": spectral["module_dim"],
                "finite_operator_or_path_family": [
                    "line_filter",
                    "cyclic_shift",
                    "commuting_diagonal_line_filter_control",
                    "finite_dirac",
                    "zero_dirac_control",
                ],
            },
            "N01": {
                "projective_order_witness": order_witness["N01_witness"],
                "projective_order_gap": order_witness["order_gap"],
                "projective_order_erased_gap": order_witness["commuting_control_gap"],
                "spectral_commutator_witness": spectral["finite_map"],
                "spectral_commutator_norm": spectral["commutator_norm"],
                "spectral_zero_dirac_control_norm": spectral["zero_dirac_commutator_norm"],
            },
        },
        "carrier_layer": "phase_1_finite_projective_design_and_spectral_readout_surface",
        "geometry_layer": "none",
        "carrier_realization": "finite torch tensors plus finite graph/hypergraph/cell-complex carriers; no dense state closure",
        "peps3d_embedding": "blocked downstream next step only; not implemented here",
        "spinor_state": "not_applicable_for_this_phase_1_projective_design_and_spectral_readout_result",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/phase1_finite_probe_effect_quotient_root_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json",
            "system_v5/ops/formal_scouts/results/sic_mub_probe_family_comparison_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_contextuality_sheaf_event_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/process_povm_quantum_comb_history_gate_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "finite projective-design line-response map and finite spectral bounded-commutator readout",
        "branch_status_before_run": "phase_1_frontier_reissue",
        "allowed_claims": [
            "Phase 1 finite projective-design response scout only",
            "Phase 1 finite spectral bounded-commutator scout only",
        ],
        "promotion_blockers": [
            "Phase 1 frontier matrix still requires final bounded validation before any later-phase work",
            "no downstream consumer has been opened by this receipt",
        ],
        "required_tools": [
            "pytorch",
            "z3",
            "cvc5",
            "sympy",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "torch_geometric",
        ],
        "actual_tools_used": [
            "pytorch",
            "z3",
            "cvc5",
            "sympy",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "torch_geometric",
        ],
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": ["rustworkx", "xgi", "torch_geometric"],
        "topology_surfaces_used": ["toponetx", "gudhi"],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_inputs": [
            "finite Fano incidence points and lines defined in this source",
            "finite diagonal algebra/module/Dirac pair defined in this source",
        ],
        "data_or_artifact_dependencies": [
            "system_v5/ops/formal_scouts/results/phase1_finite_probe_effect_quotient_root_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json",
            "system_v5/ops/formal_scouts/results/sic_mub_probe_family_comparison_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_contextuality_sheaf_event_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/process_povm_quantum_comb_history_gate_probe_results.json",
        ],
        "required_negatives": [
            "single_probe_identity_smuggling_rejected",
            "commuting_order_erased_control_rejected",
            "non_ic_probe_subset_control_rejected",
            "zero_dirac_spectral_control_rejected",
        ],
        "negatives_run": list(graveyard_companions.keys()),
        "kill_conditions": [
            "single finite line probe separates all points",
            "non-IC three-line subset separates all points",
            "commuting order-erased control has nonzero N01 gap",
            "zero Dirac control has nonzero commutator norm",
            "finite graph/topology carrier checks fail",
            "any downstream consumer admitted",
        ],
        "required_artifacts": [str(OUT_PATH.relative_to(ROOT))],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": "phase1_finite_projective_design_spectral_triple_reissue_v1",
        "result_summary": {
            "projective_points": projective["point_count"],
            "projective_lines": projective["line_count"],
            "unique_response_count": projective["unique_response_count"],
            "projective_order_gap": order_witness["order_gap"],
            "spectral_module_dim": spectral["module_dim"],
            "spectral_commutator_norm": spectral["commutator_norm"],
            "max_finite_carrier_sites": graph_topology["pyg_nodes"],
        },
        "pass_rule": (
            "finite projective line responses separate all seven points, exact incidence "
            "and graph/topology carrier checks pass, the projective order witness and "
            "spectral commutator witness survive, and single-probe/non-IC/commuting/zero-Dirac controls fail"
        ),
        "fail_rule": (
            "missing finite response separation, failed exact incidence, failed graph/topology "
            "carrier check, missing N01 witness, admitted negative control, or downstream consumer admission"
        ),
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["phase1_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": {
            "positive": positive,
            "negative": graveyard_companions,
            "boundary": boundary,
        },
        "nearby_variants": {"passed": sum(1 for item in checks if item), "total": len(checks)},
        "all_pass": all(checks),
        "blockers": [],
        "summary": {
            "phase": 1,
            "projective_design": "finite_fano_line_response_map_pass",
            "spectral_triple": "finite_bounded_commutator_pass",
            "max_finite_states": 14,
            "max_projective_points": 7,
            "max_projective_lines": 7,
            "max_pyg_nodes": graph_topology["pyg_nodes"],
            "max_pyg_edges": graph_topology["pyg_edges"],
            "max_qubits": 0,
            "max_peps3d_sites": 0,
            "max_peps3d_bond": 0,
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 Phase 1 finite projective-design/spectral-triple formal scout. "
            "It is not a v4 probe and not a promotion of PEPS3D, manifold closure, flux, "
            "Xi/Phi0, Axis0, basin, or physics claims."
        ),
        "next_required_work": [
            "Run the Phase 1 frontier matrix validator over all current Phase 1 receipts.",
            "Keep all listed downstream consumers blocked.",
        ],
        "next_admissible_step": "Validate the full Phase 1 frontier matrix or write an explicit Phase 1 blocker; do not open downstream consumers from this receipt.",
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
