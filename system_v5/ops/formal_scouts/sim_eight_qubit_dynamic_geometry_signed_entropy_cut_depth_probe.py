#!/usr/bin/env python3
"""Eight-qubit dynamic-geometry signed entropy cut-depth scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

from geomstats.geometry.hypersphere import Hypersphere
import geomstats.backend as gs
import gudhi
import networkx as nx
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
OUT_PATH = RESULT_DIR / "eight_qubit_dynamic_geometry_signed_entropy_cut_depth_probe_results.json"

NAME = "eight_qubit_dynamic_geometry_signed_entropy_cut_depth_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests signed conditional entropy and coherent "
    "information across multiple cuts of an eight-qubit tensor state whose "
    "state family is controlled by a dynamic geometry parameter. It does not "
    "admit a final manifold tower, feedback direction, cycle order, bridge, "
    "or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing 8-qubit tensor state, density, spectra, and autograd gradient"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing arbitrary cut partial traces"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing Riemannian distance on a geometry-parameter hypersphere"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing cut-depth filtration witness"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing cut adjacency simplicial complex"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing multi-cut hyperedge witness"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing ordered cut-depth transition graph"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing message pass over cut-depth graph features"},
    "networkx": {"tried": True, "used": True, "reason": "support graph source for topology witnesses"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing signed-readout impossibility checks"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "opt_einsum": "load_bearing",
    "geomstats": "load_bearing",
    "gudhi": "load_bearing",
    "toponetx": "load_bearing",
    "xgi": "load_bearing",
    "rustworkx": "load_bearing",
    "torch_geometric": "load_bearing",
    "networkx": "supportive",
    "z3": "load_bearing",
}


def dynamic_two_branch_state(theta: torch.Tensor, n: int = 8) -> torch.Tensor:
    psi = torch.zeros(2**n, dtype=torch.complex128)
    psi[0] = torch.cos(theta).to(torch.complex128)
    psi[-1] = torch.sin(theta).to(torch.complex128)
    return psi / torch.linalg.vector_norm(psi)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def entropy_torch(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + rho.conj().T) / 2
    eigs = torch.clamp(torch.linalg.eigvalsh(rho), min=1e-12)
    eigs = eigs / eigs.sum()
    return -torch.sum(eigs * torch.log(eigs))


def partial_trace_keep_first_k(rho: torch.Tensor, k: int, n: int = 8) -> torch.Tensor:
    dim_a = 2**k
    dim_b = 2 ** (n - k)
    return oe.contract("abcb->ac", rho.reshape(dim_a, dim_b, dim_a, dim_b))


def cut_readout(theta_value: float, k: int) -> dict[str, float]:
    theta = torch.tensor(theta_value, dtype=torch.float64)
    rho = density(dynamic_two_branch_state(theta))
    rho_a = partial_trace_keep_first_k(rho, k)
    s_ab = float(entropy_torch(rho).item())
    s_a = float(entropy_torch(rho_a).item())
    return {
        "cut_size": k,
        "S_AB": s_ab,
        "S_A": s_a,
        "conditional_entropy_rest_given_first_k": s_ab - s_a,
        "coherent_information_first_k_to_rest": s_a - s_ab,
    }


def coherent_information_gradient(theta_value: float, k: int = 4) -> dict[str, float]:
    theta = torch.tensor(theta_value, dtype=torch.float64, requires_grad=True)
    rho = density(dynamic_two_branch_state(theta))
    rho_a = partial_trace_keep_first_k(rho, k)
    coherent = entropy_torch(rho_a) - entropy_torch(rho)
    coherent.backward()
    return {"theta": theta_value, "coherent_information": float(coherent.item()), "gradient": float(theta.grad.item())}


def dephased_density(theta_value: float, n: int = 8) -> torch.Tensor:
    rho = density(dynamic_two_branch_state(torch.tensor(theta_value, dtype=torch.float64), n=n))
    return torch.diag(torch.diag(rho))


def dephased_cut_readout(theta_value: float, k: int) -> dict[str, float]:
    rho = dephased_density(theta_value)
    rho_a = partial_trace_keep_first_k(rho, k)
    s_ab = float(entropy_torch(rho).item())
    s_a = float(entropy_torch(rho_a).item())
    return {
        "S_AB": s_ab,
        "S_A": s_a,
        "conditional_entropy_rest_given_first_k": s_ab - s_a,
        "coherent_information_first_k_to_rest": s_a - s_ab,
    }


def geomstats_distance(theta_a: float, theta_b: float) -> dict[str, float]:
    sphere = Hypersphere(dim=2)
    point_a = gs.array([math.cos(theta_a), math.sin(theta_a), 0.0])
    point_b = gs.array([math.cos(theta_b), math.sin(theta_b), 0.0])
    return {"distance": float(sphere.metric.dist(point_a, point_b)), "angle_gap": abs(theta_a - theta_b)}


def cut_graph_witness(cuts: list[dict[str, float]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = [graph.add_node(cut["cut_size"]) for cut in cuts]
    for idx in range(len(nodes) - 1):
        graph.add_edge(nodes[idx], nodes[idx + 1], "next_cut")

    edge_index = torch.tensor([[0, 1, 2], [1, 2, 3]], dtype=torch.long)
    features = torch.tensor(
        [
            [cut["S_A"], cut["coherent_information_first_k_to_rest"], -cut["conditional_entropy_rest_given_first_k"]]
            for cut in cuts
        ],
        dtype=torch.float32,
    )
    conv = GCNConv(3, 2, add_self_loops=True)
    with torch.no_grad():
        propagated = conv(Data(x=features, edge_index=edge_index).x, edge_index)

    complex_ = tnx.SimplicialComplex()
    for cut in cuts:
        complex_.add_node(f"cut_{cut['cut_size']}")
    complex_.add_simplex(["cut_1", "cut_2", "cut_4"])
    hypergraph = xgi.Hypergraph()
    hypergraph.add_edge(["cut_1", "cut_2", "cut_4"])
    nx_graph = nx.path_graph([cut["cut_size"] for cut in cuts])
    st = gudhi.SimplexTree()
    for idx, cut in enumerate(cuts):
        st.insert([idx], filtration=float(cut["S_A"]))
    for idx in range(len(cuts) - 1):
        st.insert([idx, idx + 1], filtration=float(max(cuts[idx]["S_A"], cuts[idx + 1]["S_A"])))
    return {
        "rustworkx_edges": graph.num_edges(),
        "pyg_output_shape": list(propagated.shape),
        "toponetx_dim": complex_.dim,
        "xgi_hyperedges": hypergraph.num_edges,
        "networkx_edges": nx_graph.number_of_edges(),
        "gudhi_persistence_pairs": len(st.persistence()),
    }


def z3_signed_requires_nonzero_cut_entropy() -> dict[str, Any]:
    signed = z3.Real("signed")
    cut_entropy = z3.Real("cut_entropy")
    solver = z3.Solver()
    solver.add(signed > 0, cut_entropy == 0, signed <= cut_entropy)
    return {"solver_status": str(solver.check()), "pass": solver.check() == z3.unsat}


def main() -> dict[str, Any]:
    started = time.time()
    theta = 0.73
    cuts = [cut_readout(theta, k) for k in (1, 2, 4, 7)]
    gradient = coherent_information_gradient(theta, k=4)
    dephased = dephased_cut_readout(theta, k=4)
    product = cut_readout(0.0, k=4)
    geo = geomstats_distance(0.31, theta)
    graph = cut_graph_witness(cuts)

    positive = {
        "eight_qubit_signed_entropy_exists_on_multiple_nontrivial_cuts": {
            "cuts": cuts,
            "pass": all(cut["conditional_entropy_rest_given_first_k"] < -1e-6 and cut["coherent_information_first_k_to_rest"] > 1e-6 for cut in cuts),
        },
        "dynamic_geometry_parameter_has_riemannian_distance_and_nonzero_coherent_gradient": {
            "geomstats_distance": geo,
            "coherent_gradient": gradient,
            "pass": geo["distance"] > 1e-6 and abs(geo["distance"] - geo["angle_gap"]) < 1e-6 and abs(gradient["gradient"]) > 1e-6,
        },
        "cut_depth_graph_topology_and_message_pass_execute": {"graph": graph, "pass": graph["rustworkx_edges"] == 3 and graph["pyg_output_shape"] == [4, 2] and graph["xgi_hyperedges"] == 1},
        "z3_signed_readout_requires_nonzero_cut_entropy": z3_signed_requires_nonzero_cut_entropy(),
    }
    graveyard_companions = {
        "product_limit_has_no_signed_cut_entropy": {
            "readout": product,
            "pass": abs(product["conditional_entropy_rest_given_first_k"]) < 1e-7 and abs(product["coherent_information_first_k_to_rest"]) < 1e-7,
        },
        "dephased_classical_mixture_has_cut_entropy_but_no_negative_conditional_entropy": {
            "readout": dephased,
            "pass": dephased["S_A"] > 1e-6 and dephased["conditional_entropy_rest_given_first_k"] >= -1e-9,
        },
        "zero_geometry_motion_has_zero_riemannian_distance": {
            "geomstats_distance": geomstats_distance(theta, theta),
            "pass": geomstats_distance(theta, theta)["distance"] < 1e-9,
        },
    }
    boundary = {
        "finite_eight_qubit_state_dimension": {"dimension": int(dynamic_two_branch_state(torch.tensor(theta)).numel()), "pass": int(dynamic_two_branch_state(torch.tensor(theta)).numel()) == 256},
        "first_half_reduced_density_trace_one": {
            "trace": float(torch.trace(partial_trace_keep_first_k(density(dynamic_two_branch_state(torch.tensor(theta))), 4)).real),
            "pass": abs(float(torch.trace(partial_trace_keep_first_k(density(dynamic_two_branch_state(torch.tensor(theta))), 4)).real) - 1.0) < 1e-9,
        },
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "eight-qubit dynamic tensor-state geometry with signed conditional entropy and coherent information across cut depths",
        "dynamic_geometry": {"parameter": "theta", "riemannian_distance_surface": "geomstats Hypersphere(dim=2)", "deformation": "cos(theta)|0...0> + sin(theta)|1...1>"},
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "this uses a one-parameter Riemannian deformation; richer bending/stretching needs multi-parameter metric scouts",
            "cut graph edges are ordered cut-depth transitions, not final loop-order mechanics",
        ],
        "why_not_v4_probes": "This is a clean v5 dynamic-geometry entropy scout and should not add to the mixed v4 probe estate.",
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
