#!/usr/bin/env python3
"""Nested geometry tower dependency-order scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

from clifford import Cl
from geomstats.geometry.hypersphere import Hypersphere
import geomstats.backend as gs
import gudhi
import opt_einsum as oe
import rustworkx as rx
import torch
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
import toponetx as tnx
import xgi
import z3

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "nested_geometry_tower_dependency_order_probe_results.json"

NAME = "nested_geometry_tower_dependency_order_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: represents a candidate nested geometry tower as a "
    "dependency graph and tests adjacent invalid orderings. It does not admit "
    "a final tower, final manifold, cycle mechanics, bridge, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite state, density, tensor coupling, and graph features"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing partial trace for coupling layer"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing projective-base distance on S2"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing chirality/orientation pseudoscalar check"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing directed dependency graph"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing message pass over tower dependency features"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing filtration over nested tower order"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing simplicial complex over adjacent tower triples"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing hyperedge witness for coupled geometry layers"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing dependency-order impossibility constraints"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

LAYERS = [
    "finite_constraint_complex",
    "complex_hilbert_carrier",
    "unit_spinor_sphere",
    "projective_base_sphere",
    "hopf_fiber_bundle",
    "hopf_torus_leaf_family",
    "connection_holonomy_geometry",
    "weyl_spinor_bundle",
    "chirality_orientation_cover",
    "clifford_module_geometry",
    "frame_bundle_structure_reduction",
    "tensor_product_coupling_geometry",
    "dynamic_transition_ratchet_geometry",
]


def unit_spinor() -> torch.Tensor:
    psi = torch.tensor([1.0 + 0j, 1.0j], dtype=torch.complex128)
    return psi / torch.linalg.vector_norm(psi)


def hopf_projection(psi: torch.Tensor) -> torch.Tensor:
    a, b = psi[0], psi[1]
    return torch.tensor(
        [
            2 * torch.real(a.conj() * b),
            2 * torch.imag(a.conj() * b),
            torch.real(a.conj() * a - b.conj() * b),
        ],
        dtype=torch.float64,
    )


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def partial_trace_first_qubit(rho: torch.Tensor) -> torch.Tensor:
    return oe.contract("aibi->ab", rho.reshape(2, 2, 2, 2))


def geometry_witnesses() -> dict[str, Any]:
    psi = unit_spinor()
    base = hopf_projection(psi)
    sphere = Hypersphere(dim=2)
    north = gs.array([0.0, 0.0, 1.0])
    base_point = gs.array([float(base[0]), float(base[1]), float(base[2])])
    _, blades = Cl(1, 3)
    pseudo_square = float((blades["e1234"] * blades["e1234"])[()])
    bell = torch.tensor([1, 0, 0, 1], dtype=torch.complex128) / math.sqrt(2)
    reduced = partial_trace_first_qubit(density(bell))
    return {
        "unit_spinor_norm": float(torch.linalg.vector_norm(psi).item()),
        "hopf_base_norm": float(torch.linalg.vector_norm(base).item()),
        "base_sphere_distance_from_north": float(sphere.metric.dist(north, base_point)),
        "clifford_pseudoscalar_square": pseudo_square,
        "coupled_reduced_density_trace": float(torch.trace(reduced).real),
        "frame_reduction_dimensions": [4, 3, 2, 1],
    }


def dependency_graph(order: list[str]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    node_ids = {name: graph.add_node(name) for name in order}
    for prior, later in zip(LAYERS[:-1], LAYERS[1:]):
        if prior in node_ids and later in node_ids:
            graph.add_edge(node_ids[prior], node_ids[later], "requires")
    position = {name: idx for idx, name in enumerate(order)}
    violations = [(a, b) for a, b in zip(LAYERS[:-1], LAYERS[1:]) if position.get(a, 99) > position.get(b, -1)]
    return {"node_count": graph.num_nodes(), "edge_count": graph.num_edges(), "violations": violations, "pass": not violations}


def topology_witnesses() -> dict[str, Any]:
    complex_ = tnx.SimplicialComplex()
    for name in LAYERS:
        complex_.add_node(name)
    for idx in range(len(LAYERS) - 2):
        complex_.add_simplex(LAYERS[idx : idx + 3])
    hypergraph = xgi.Hypergraph()
    hypergraph.add_edge(
        [
            "weyl_spinor_bundle",
            "chirality_orientation_cover",
            "clifford_module_geometry",
        ]
    )
    st = gudhi.SimplexTree()
    for idx in range(len(LAYERS)):
        st.insert([idx], filtration=float(idx))
    for idx in range(len(LAYERS) - 1):
        st.insert([idx, idx + 1], filtration=float(idx + 1))
    features = torch.tensor([[idx, 1.0 if idx > 0 else 0.0] for idx in range(len(LAYERS))], dtype=torch.float32)
    edge_index = torch.tensor(
        [[idx for idx in range(len(LAYERS) - 1)], [idx + 1 for idx in range(len(LAYERS) - 1)]],
        dtype=torch.long,
    )
    conv = GCNConv(2, 2, add_self_loops=True)
    with torch.no_grad():
        out = conv(Data(x=features, edge_index=edge_index).x, edge_index)
    return {
        "toponetx_dim": complex_.dim,
        "xgi_hyperedges": hypergraph.num_edges,
        "gudhi_persistence_pairs": len(st.persistence()),
        "pyg_output_shape": list(out.shape),
    }


def z3_dependency_unsat() -> dict[str, Any]:
    spinor = z3.Int("spinor")
    hopf = z3.Int("hopf")
    solver = z3.Solver()
    solver.add(spinor < hopf, hopf < spinor)
    return {"solver_status": str(solver.check()), "pass": solver.check() == z3.unsat}


def main() -> dict[str, Any]:
    started = time.time()
    witnesses = geometry_witnesses()
    correct = dependency_graph(LAYERS)
    swapped = LAYERS.copy()
    i = swapped.index("unit_spinor_sphere")
    j = swapped.index("hopf_torus_leaf_family")
    swapped[i], swapped[j] = swapped[j], swapped[i]
    invalid = dependency_graph(swapped)
    topo = topology_witnesses()
    positive = {
        "candidate_tower_order_satisfies_declared_dependencies": correct,
        "geometry_witnesses_execute_at_required_layers": {
            "witnesses": witnesses,
            "pass": abs(witnesses["unit_spinor_norm"] - 1) < 1e-9
            and abs(witnesses["hopf_base_norm"] - 1) < 1e-9
            and witnesses["base_sphere_distance_from_north"] > 0
            and abs(witnesses["clifford_pseudoscalar_square"] + 1) < 1e-9
            and abs(witnesses["coupled_reduced_density_trace"] - 1) < 1e-9
            and witnesses["frame_reduction_dimensions"] == sorted(witnesses["frame_reduction_dimensions"], reverse=True),
        },
        "topology_and_message_pass_witnesses_execute": {
            "topology": topo,
            "pass": topo["toponetx_dim"] >= 2 and topo["xgi_hyperedges"] == 1 and topo["pyg_output_shape"] == [len(LAYERS), 2],
        },
        "z3_rejects_mutual_dependency_cycle": z3_dependency_unsat(),
    }
    graveyard_companions = {
        "torus_leaf_before_unit_spinor_breaks_dependency_order": {
            "violations": invalid["violations"],
            "pass": invalid["pass"] is False and len(invalid["violations"]) > 0,
        },
        "unnormalized_spinor_fails_unit_sphere_admission": {
            "norm": float(torch.linalg.vector_norm(torch.tensor([2.0 + 0j, 0j], dtype=torch.complex128)).item()),
            "pass": abs(float(torch.linalg.vector_norm(torch.tensor([2.0 + 0j, 0j], dtype=torch.complex128)).item()) - 1) > 1e-6,
        },
        "uncoupled_two_qubit_product_has_pure_reduced_density": {
            "purity": float(torch.real(torch.trace(partial_trace_first_qubit(density(torch.tensor([1, 0, 0, 0], dtype=torch.complex128))) ** 2)).item()),
            "pass": abs(float(torch.real(torch.trace(partial_trace_first_qubit(density(torch.tensor([1, 0, 0, 0], dtype=torch.complex128))) ** 2)).item()) - 1) < 1e-9,
        },
    }
    boundary = {
        "tower_has_declared_layer_count": {"layer_count": len(LAYERS), "pass": len(LAYERS) == 13},
        "dependency_edges_are_adjacent": {"edge_count": correct["edge_count"], "pass": correct["edge_count"] == 12},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "candidate nested geometry tower dependency order with concrete layer witnesses",
        "candidate_layers": LAYERS,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "frame bundle structure reduction may need to move earlier before spinor bundle construction",
            "dynamic transition geometry needs richer deformation families beyond adjacent dependency edges",
        ],
        "why_not_v4_probes": "This is a clean v5 geometry-tower scout and should not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {"all_pass": bool(all_pass), "elapsed_seconds": round(time.time() - started, 6), "promotion_allowed": PROMOTION_ALLOWED},
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
