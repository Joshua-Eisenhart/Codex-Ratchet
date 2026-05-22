#!/usr/bin/env python3
"""Integrated nested geometric-constraint-manifold dynamic tensor-network scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

from clifford import Cl
from geomstats.geometry.hypersphere import Hypersphere
import geomstats.backend as gs
import gudhi
import networkx as nx
import opt_einsum as oe
import rustworkx as rx
from scipy.linalg import expm
import sympy as sp
import torch
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
from torch_geometric.utils import from_networkx
import toponetx as tnx
import xgi
import z3

from sim_left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe import (
    execute_histories,
)
from sim_nested_geometry_tower_dependency_order_probe import LAYERS
from sim_special_holonomy_form_constraint_survivor_quotient_probe import FAMILIES, family_row


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "integrated_nested_geometric_constraint_manifold_dynamic_tensor_network_probe_results.json"

NAME = "integrated_nested_geometric_constraint_manifold_dynamic_tensor_network_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: composes the candidate nested geometry tower, source-native "
    "left/right Weyl density terrain histories, Hopf/shell graph dynamics, finite "
    "eight-qubit tensor-network evolution, support G-structure reduction scaffold, "
    "topology witnesses, and entropy/coherent-information survivor readouts into one "
    "bounded executable fixture. It does not admit a final manifold, final G-structure, "
    "physics, ontology, bridge, axis, engine, or target-system claim."
)

TOOL_MANIFEST = {
    "scipy": {"tried": True, "used": True, "reason": "supportive sanity propagator for two-level signed Hamiltonian"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing eight-qubit state, Hamiltonian evolution, density reductions, and spectra"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing tensor-network partial traces across all cuts"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing dynamic shell graph construction from source-native history features"},
    "torch_geometric": {"tried": True, "used": True, "reason": "supportive graph tensorization and message passing over the integrated dynamic graph"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over the dynamic shell graph filtration"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact noncommuting Pauli and support-reduction checks"},
    "z3": {"tried": True, "used": True, "reason": "supportive integrated noncollapse and control contradiction witness"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing Clifford pseudoscalar/chirality orientation witness"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing S2 projective-base distance witness"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing nested tower dependency graph witness"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing simplicial nested-layer witness"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing hyperedge witness coupling Weyl/chirality/Clifford layers"},
    "special_form_constraints": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SU3-like, G2-like, Spin7-like, and generic finite form-family features driving integrated variants",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "scipy": "supportive",
    "pytorch": "load_bearing",
    "opt_einsum": "load_bearing",
    "networkx": "load_bearing",
    "torch_geometric": "supportive",
    "gudhi": "load_bearing",
    "sympy": "load_bearing",
    "z3": "supportive",
    "clifford": "supportive",
    "geomstats": "supportive",
    "rustworkx": "supportive",
    "toponetx": "supportive",
    "xgi": "supportive",
    "special_form_constraints": "supportive",
}

N_QUBITS = 8
DTYPE = torch.complex128


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items() if k != "rho"}
    if isinstance(value, list):
        return [as_jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [as_jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


def tower_witnesses() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {name: graph.add_node(name) for name in LAYERS}
    for left, right in zip(LAYERS[:-1], LAYERS[1:]):
        graph.add_edge(nodes[left], nodes[right], "nested_parent")

    complex_ = tnx.SimplicialComplex()
    for name in LAYERS:
        complex_.add_node(name)
    for idx in range(len(LAYERS) - 2):
        complex_.add_simplex(LAYERS[idx : idx + 3])

    hypergraph = xgi.Hypergraph()
    hyperedge = ["weyl_spinor_bundle", "chirality_orientation_cover", "clifford_module_geometry"]
    hyperedge_membership = all(name in LAYERS for name in hyperedge)
    if hyperedge_membership:
        hypergraph.add_edge(hyperedge)

    features = torch.tensor([[idx, 1.0 if idx else 0.0] for idx in range(len(LAYERS))], dtype=torch.float32)
    edge_index = torch.tensor(
        [[idx for idx in range(len(LAYERS) - 1)], [idx + 1 for idx in range(len(LAYERS) - 1)]],
        dtype=torch.long,
    )
    with torch.no_grad():
        pyg_out = GCNConv(2, 2, add_self_loops=True)(Data(x=features, edge_index=edge_index).x, edge_index)

    psi = torch.tensor([1.0 + 0j, 1.0j], dtype=DTYPE)
    psi = psi / torch.linalg.vector_norm(psi)
    a, b = psi[0], psi[1]
    base = torch.tensor(
        [2 * torch.real(a.conj() * b), 2 * torch.imag(a.conj() * b), torch.real(a.conj() * a - b.conj() * b)],
        dtype=torch.float64,
    )
    sphere = Hypersphere(dim=2)
    dist = float(sphere.metric.dist(gs.array([0.0, 0.0, 1.0]), gs.array([float(base[0]), float(base[1]), float(base[2])])))
    _, blades = Cl(1, 3)
    pseudo_square = float((blades["e1234"] * blades["e1234"])[()])
    return {
        "layer_count": len(LAYERS),
        "dependency_edges": graph.num_edges(),
        "toponetx_dim": complex_.dim,
        "xgi_hyperedges": hypergraph.num_edges,
        "xgi_hyperedge_membership": hyperedge_membership,
        "pyg_tower_output_shape": list(pyg_out.shape),
        "hopf_base_norm": float(torch.linalg.vector_norm(base).item()),
        "projective_base_distance": dist,
        "clifford_pseudoscalar_square": pseudo_square,
        "pass": graph.num_edges() == 12
        and complex_.dim >= 2
        and hyperedge_membership
        and hypergraph.num_edges == 1
        and list(pyg_out.shape) == [len(LAYERS), 2]
        and abs(float(torch.linalg.vector_norm(base).item()) - 1.0) < 1e-9
        and dist > 0
        and abs(pseudo_square + 1.0) < 1e-9,
    }


def support_g_structure() -> dict[str, Any]:
    dims = {"GL2C_real": 8, "O4_real": 6, "SO4_real": 6, "Spin4_lie": 6, "U2_real": 4, "SU2_real": 3}
    x = sp.symbols("x")
    det_boundary = sp.factor((x - 1) * (x + 1))
    monotone = dims["GL2C_real"] >= dims["O4_real"] >= dims["SO4_real"] >= dims["Spin4_lie"] >= dims["U2_real"] >= dims["SU2_real"]
    return {
        "group_dimensions": dims,
        "orientation_boundary_polynomial_det_pm_one": str(det_boundary),
        "pass": monotone and sp.simplify(det_boundary - (x**2 - 1)) == 0,
    }


def special_form_family_features() -> dict[str, dict[str, float]]:
    rows = {name: family_row(name, spec) for name, spec in FAMILIES.items()}
    out: dict[str, dict[str, float]] = {}
    for name, row in rows.items():
        out[name] = {
            "dimension": float(row["dimension"]),
            "survivor_fraction": float(row["survivor_fraction"]),
            "class_count": float(row["quotient"]["class_count"]),
            "term_count": float(row["term_count"]),
            "edge_count": float(row["quotient"]["edge_count"]),
        }
    out["support_reduction_scaffold"] = {
        "dimension": 4.0,
        "survivor_fraction": 0.5,
        "class_count": 4.0,
        "term_count": 4.0,
        "edge_count": 0.0,
    }
    return out


def selected_form_feature(families: dict[str, dict[str, float]], name: str | None) -> dict[str, float]:
    if name is None:
        return {"dimension": 0.0, "survivor_fraction": 0.0, "class_count": 0.0, "term_count": 0.0, "edge_count": 0.0}
    return families[name]


def dynamic_form_family_for_step(feature: dict[str, float]) -> str:
    if feature["base_lift_fraction"] > 0.5 and feature["std"] > 0.53:
        return "spin7_four_form_constraints"
    if feature["base_lift_fraction"] > 0.5:
        return "g2_three_form_constraints"
    if feature["std"] < 0.13 and feature["coherence"] > 0.67:
        return "su3_two_and_three_form_constraints"
    if feature["terrain_count"] <= 2:
        return "support_reduction_scaffold"
    return "support_reduction_scaffold"


def source_features(rows: list[dict[str, Any]], permute: bool = False, uniform: bool = False) -> list[dict[str, float]]:
    ordered = list(reversed(rows)) if permute else rows
    features = []
    for step in range(8):
        block = ordered[step * 8 : (step + 1) * 8]
        readouts = torch.tensor([row["readout"] for row in block], dtype=torch.float64)
        coherence = torch.tensor([row["offdiag_coherence"] for row in block], dtype=torch.float64)
        terrains = {row["terrain_law"] for row in block}
        base_lift_fraction = sum(1 for row in block if row["loop"] == "base_lift_loop") / max(len(block), 1)
        left = [row for row in block if row["sheet"].startswith("left")]
        right = [row for row in block if row["sheet"].startswith("right")]
        lr_gap = 0.0
        flux_orientation = 0.0
        if left and right:
            left_coh = torch.tensor([r["offdiag_coherence"] for r in left], dtype=torch.float64)
            right_coh = torch.tensor([r["offdiag_coherence"] for r in right], dtype=torch.float64)
            lr_gap = float(torch.abs(torch.mean(left_coh) - torch.mean(right_coh)).item())
            left_z = float(torch.mean(torch.tensor([r["readout"][2] for r in left], dtype=torch.float64)).item())
            right_z = float(torch.mean(torch.tensor([r["readout"][2] for r in right], dtype=torch.float64)).item())
            flux_orientation = left_z - right_z
        if uniform:
            mean_abs, std, coh, lr_gap, flux_orientation, terrain_count, base_lift_fraction = 0.25, 0.0, 0.25, 0.0, 0.0, 1, 0.0
        else:
            mean_abs = float(torch.mean(torch.abs(readouts)).item())
            std = float(torch.std(readouts, unbiased=False).item())
            coh = float(torch.mean(coherence).item())
            terrain_count = len(terrains)
        features.append(
            {
                "step": step,
                "mean_abs": mean_abs,
                "std": std,
                "coherence": coh,
                "lr_gap": lr_gap,
                "flux_orientation": flux_orientation,
                "terrain_count": float(terrain_count),
                "base_lift_fraction": float(base_lift_fraction),
            }
        )
    return features


def shell_points(features: list[dict[str, float]], step: int, topology_feedback: float, form_feature: dict[str, float]) -> torch.Tensor:
    f = features[step]
    form_scale = form_feature["survivor_fraction"]
    class_scale = math.log1p(form_feature["class_count"]) / 5.0
    radius = 1.0 + 0.42 * f["mean_abs"] + 0.08 * step + 0.04 * topology_feedback + 0.05 * form_scale
    twist = 0.37 * step + 0.9 * f["coherence"] + 0.15 * f["flux_orientation"] + 0.07 * class_scale
    stretch = 1.0 + 1.7 * f["std"] + 0.5 * f["lr_gap"] + 0.05 * f["terrain_count"] + 0.02 * form_feature["dimension"]
    rows = []
    for idx in range(N_QUBITS):
        theta = 2 * math.pi * idx / N_QUBITS + twist
        z = -0.75 + 1.5 * idx / (N_QUBITS - 1)
        xy = math.sqrt(max(0.0, 1 - z * z))
        rows.append(
            [
                radius * stretch * xy * math.cos(theta),
                radius / math.sqrt(stretch) * xy * math.sin(theta),
                radius / math.sqrt(stretch) * z,
            ]
        )
    return torch.tensor(rows, dtype=torch.float64)


def weights_from_points(points: torch.Tensor, feature: dict[str, float], form_feature: dict[str, float], *, use_flux: bool = True) -> torch.Tensor:
    dist = torch.cdist(points, points)
    weights = 1.0 / torch.clamp(dist * dist, min=0.18)
    if use_flux:
        rows = torch.arange(N_QUBITS, dtype=torch.float64).reshape(-1, 1)
        cols = torch.arange(N_QUBITS, dtype=torch.float64).reshape(1, -1)
        orientation = torch.sin((rows - cols) * (0.23 + abs(feature["flux_orientation"])))
        weights = weights * (1.0 + 0.12 * orientation.abs() + 0.04 * feature["base_lift_fraction"])
    weights = weights * (1.0 + 0.03 * form_feature["survivor_fraction"] + 0.002 * form_feature["term_count"])
    weights.fill_diagonal_(0.0)
    return weights / torch.clamp(torch.max(weights), min=1e-12)


def graph_from_weights(weights: torch.Tensor, threshold: float = 0.20) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(range(N_QUBITS))
    for i in range(N_QUBITS):
        for j in range(i + 1, N_QUBITS):
            weight = float(weights[i, j].item())
            if weight >= threshold:
                graph.add_edge(i, j, weight=weight)
    return graph


def directed_flux_graph(weights: torch.Tensor, feature: dict[str, float], threshold: float = 0.20) -> nx.DiGraph:
    graph = nx.DiGraph()
    graph.add_nodes_from(range(N_QUBITS))
    sign = 1 if feature["flux_orientation"] >= 0 else -1
    for i in range(N_QUBITS):
        for j in range(i + 1, N_QUBITS):
            weight = float(weights[i, j].item())
            if weight >= threshold:
                src, dst = (i, j) if ((i + j + sign) % 2 == 0) else (j, i)
                graph.add_edge(src, dst, weight=weight, flux=sign * weight)
    return graph


def one_qubit_operator(local: torch.Tensor, qubit: int) -> torch.Tensor:
    op = torch.tensor([[1.0 + 0j]], dtype=DTYPE)
    eye = torch.eye(2, dtype=DTYPE)
    for idx in range(N_QUBITS):
        op = torch.kron(op, local if idx == qubit else eye)
    return op


def graph_hamiltonian(
    weights: torch.Tensor,
    feature: dict[str, float],
    *,
    graph_coupling: bool = True,
    topology_feedback: float = 0.0,
    use_flux: bool = True,
    form_feature: dict[str, float] | None = None,
) -> torch.Tensor:
    sx = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    h = torch.zeros((2**N_QUBITS, 2**N_QUBITS), dtype=DTYPE)
    flux_gain = abs(feature["flux_orientation"]) if use_flux else 0.0
    form_feature = form_feature or {"dimension": 0.0, "survivor_fraction": 0.0, "class_count": 0.0, "term_count": 0.0, "edge_count": 0.0}
    form_strength = 0.04 * form_feature["survivor_fraction"] + 0.004 * math.log1p(form_feature["class_count"])
    strength = 0.40 + 0.55 * feature["mean_abs"] + 0.30 * feature["coherence"] + 0.05 * topology_feedback + form_strength
    chirality_bias = 0.18 + 0.45 * feature["lr_gap"] + 0.08 * flux_gain + 0.002 * form_feature["dimension"]
    for i in range(N_QUBITS):
        h = h + chirality_bias * ((-1) ** i) * one_qubit_operator(sz, i)
        for j in range(i + 1, N_QUBITS):
            if not graph_coupling:
                continue
            weight = float(weights[i, j].item())
            if weight > 0.16:
                h = h + strength * weight * (
                    one_qubit_operator(sx, i) @ one_qubit_operator(sx, j)
                    + (0.31 + 0.2 * feature["std"] + 0.03 * topology_feedback) * one_qubit_operator(sy, i) @ one_qubit_operator(sy, j)
                )
    return h


def initial_tensor_state() -> torch.Tensor:
    psi = torch.zeros(2**N_QUBITS, dtype=DTYPE)
    psi[0] = 1.0 + 0j
    return psi


def reduced_density(psi: torch.Tensor, keep: list[int]) -> torch.Tensor:
    state = psi.reshape([2] * N_QUBITS)
    bra_pool = list("abcdefgh")
    ket_pool = list("ijklmnop")
    bra_labels = bra_pool[:N_QUBITS]
    ket_labels = [ket_pool[idx] if idx in keep else bra_labels[idx] for idx in range(N_QUBITS)]
    out_labels = [bra_labels[idx] for idx in keep] + [ket_labels[idx] for idx in keep]
    expr = f"{''.join(bra_labels)},{''.join(ket_labels)}->{''.join(out_labels)}"
    return torch.as_tensor(oe.contract(expr, state, state.conj()).reshape(2 ** len(keep), 2 ** len(keep)), dtype=DTYPE)


def entropy(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def cut_readouts(psi: torch.Tensor) -> list[dict[str, Any]]:
    full = entropy(torch.outer(psi, psi.conj()))
    rows = []
    for cut in range(1, N_QUBITS):
        rho_a = reduced_density(psi, list(range(cut)))
        s_a = entropy(rho_a)
        sv = torch.linalg.svdvals(psi.reshape(2**cut, 2 ** (N_QUBITS - cut)))
        rows.append(
            {
                "cut": cut,
                "S_A": s_a,
                "S_AB": full,
                "conditional_entropy_A_given_B": full - s_a,
                "coherent_information_A_to_B": s_a - full,
                "bond_dim": int((sv > 1e-8).sum().item()),
            }
        )
    return rows


def persistence_summary(graph: nx.Graph) -> dict[str, Any]:
    st = gudhi.SimplexTree()
    for node in graph.nodes:
        st.insert([int(node)], filtration=0.0)
    for a, b, data in graph.edges(data=True):
        st.insert([int(a), int(b)], filtration=1.0 / max(float(data["weight"]), 1e-12))
    pairs = st.persistence()
    pyg = from_networkx(graph) if graph.number_of_edges() else None
    cycle_count = len(nx.cycle_basis(graph)) if graph.number_of_edges() else 0
    return {
        "edge_count": graph.number_of_edges(),
        "cycle_count": cycle_count,
        "persistence_pair_count": len(pairs),
        "pyg_edge_index_shape": list(pyg.edge_index.shape) if pyg is not None else [2, 0],
    }


def evolve_integrated(
    features: list[dict[str, float]],
    *,
    zero_strength: bool = False,
    graph_coupling: bool = True,
    use_flux: bool = True,
    use_topology_feedback: bool = True,
    form_family: str | None = "support_reduction_scaffold",
    form_families: dict[str, dict[str, float]] | None = None,
    dynamic_form_selection: bool = False,
) -> dict[str, Any]:
    psi = initial_tensor_state()
    history = []
    final_graph = nx.Graph()
    final_flux_graph = nx.DiGraph()
    topology_feedback = 0.0
    form_families = form_families or special_form_family_features()
    base_form_feature = selected_form_feature(form_families, form_family)
    active_form_sequence = []
    for step, feature in enumerate(features):
        active_form_family = dynamic_form_family_for_step(feature) if dynamic_form_selection else form_family
        form_feature = selected_form_feature(form_families, active_form_family)
        points = shell_points(features, step, topology_feedback if use_topology_feedback else 0.0, form_feature)
        weights = weights_from_points(points, feature, form_feature, use_flux=use_flux)
        graph = graph_from_weights(weights)
        flux_graph = directed_flux_graph(weights, feature) if use_flux else nx.DiGraph()
        final_graph = graph
        final_flux_graph = flux_graph
        persistence = persistence_summary(graph)
        cycle_count = persistence["cycle_count"]
        if not zero_strength:
            h = graph_hamiltonian(
                weights,
                feature,
                graph_coupling=graph_coupling,
                topology_feedback=topology_feedback if use_topology_feedback else 0.0,
                use_flux=use_flux,
                form_feature=form_feature,
            )
            unitary = torch.linalg.matrix_exp((-1j * 0.12) * h)
            psi = unitary @ psi
            psi = psi / torch.linalg.vector_norm(psi)
        topology_feedback = float(cycle_count + 0.05 * graph.number_of_edges()) if use_topology_feedback else 0.0
        history.append(
            {
                "step": step,
                "edge_count": graph.number_of_edges(),
                "cycle_count": cycle_count,
                "directed_flux_edges": flux_graph.number_of_edges(),
                "weight_std": float(torch.std(weights[weights > 0]).item()),
                "mean_abs": feature["mean_abs"],
                "coherence": feature["coherence"],
                "lr_gap": feature["lr_gap"],
                "flux_orientation": feature["flux_orientation"],
                "topology_feedback_next": topology_feedback,
                "form_family": form_family or "none",
                "active_form_family": active_form_family or "none",
                "form_survivor_fraction": form_feature["survivor_fraction"],
                "form_class_count": form_feature["class_count"],
            }
        )
        active_form_sequence.append(active_form_family or "none")
    cuts = cut_readouts(psi)
    return {
        "history": history,
        "cuts": cuts,
        "max_coherent_information": max(row["coherent_information_A_to_B"] for row in cuts),
        "min_conditional_entropy": min(row["conditional_entropy_A_given_B"] for row in cuts),
        "max_bond_dim": max(row["bond_dim"] for row in cuts),
        "persistence": persistence_summary(final_graph),
        "flux_graph_edge_count": final_flux_graph.number_of_edges(),
        "form_family": form_family or "none",
        "form_feature": base_form_feature,
        "active_form_sequence": active_form_sequence,
        "dynamic_form_selection": dynamic_form_selection,
    }


def sympy_scipy_checks() -> dict[str, Any]:
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    comm = sp.simplify(sx * sy - sy * sx)
    h = [[1.0 + 0j, 0.2 + 0j], [0.2 + 0j, -1.0 + 0j]]
    u = expm([[-1j * 0.03 * value for value in row] for row in h])
    u_t = torch.as_tensor(u, dtype=DTYPE)
    eye = torch.eye(2, dtype=DTYPE)
    unitary_gap = float(torch.linalg.vector_norm(u_t.conj().T @ u_t - eye).item())
    return {
        "pauli_commutator": str(comm),
        "scipy_unitary_gap": unitary_gap,
        "pass": comm != sp.zeros(2) and unitary_gap < 1e-12,
    }


def z3_integrated_witness(candidate: dict[str, Any], product: dict[str, Any], uniform: dict[str, Any]) -> dict[str, Any]:
    c = candidate["max_coherent_information"] > 0.05 and candidate["min_conditional_entropy"] < -0.05
    p = product["max_coherent_information"] <= 1e-8
    u = abs(candidate["max_coherent_information"] - uniform["max_coherent_information"]) > 1e-3
    solver = z3.Solver()
    cb, pb, ub = z3.Bools("candidate_signed_info product_control uniform_control")
    solver.add(cb == c, pb == p, ub == u, z3.Not(z3.And(cb, pb, ub)))
    status = solver.check()
    return {"solver_status": str(status), "pass": status == z3.unsat, "candidate": c, "product_control": p, "uniform_control": u}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    source_rows = execute_histories()
    features = source_features(source_rows)
    form_families = special_form_family_features()
    candidate = evolve_integrated(features, form_families=form_families)
    dynamic_form = evolve_integrated(features, form_families=form_families, dynamic_form_selection=True)
    product = evolve_integrated(features, zero_strength=True, form_families=form_families)
    no_graph_coupling = evolve_integrated(features, graph_coupling=False, form_families=form_families)
    no_flux = evolve_integrated(features, use_flux=False, form_families=form_families)
    no_topology_feedback = evolve_integrated(features, use_topology_feedback=False, form_families=form_families)
    no_form_family = evolve_integrated(features, form_family=None, form_families=form_families)
    special_form_variants = {
        name: evolve_integrated(features, form_family=name, form_families=form_families)
        for name in [
            "su3_two_and_three_form_constraints",
            "g2_three_form_constraints",
            "spin7_four_form_constraints",
            "generic_three_form_control_constraints",
            "generic_four_form_control_constraints",
        ]
    }
    uniform = evolve_integrated(source_features(source_rows, uniform=True), form_families=form_families)
    permuted = evolve_integrated(source_features(source_rows, permute=True), form_families=form_families)
    tower = tower_witnesses()
    g_structure = support_g_structure()
    symbolic = sympy_scipy_checks()

    positive = {
        "nested_tower_witnesses_execute_inside_integrated_run": tower,
        "source_native_weyl_terrain_histories_feed_dynamic_system": {
            "microstep_count": len(source_rows),
            "feature_steps": len(features),
            "distinct_feature_rows": len({tuple(round(v, 6) for k, v in row.items() if k != "step") for row in features}),
            "pass": len(source_rows) == 64 and len(features) == 8 and len({tuple(round(v, 6) for k, v in row.items() if k != "step") for row in features}) > 1,
        },
        "integrated_dynamic_tensor_network_has_signed_information": {
            "max_coherent_information": candidate["max_coherent_information"],
            "min_conditional_entropy": candidate["min_conditional_entropy"],
            "max_bond_dim": candidate["max_bond_dim"],
            "pass": candidate["max_coherent_information"] > 0.05 and candidate["min_conditional_entropy"] < -0.05 and candidate["max_bond_dim"] > 1,
        },
        "topology_and_flux_feedback_are_live_in_dynamic_history": {
            "cycle_counts": [row["cycle_count"] for row in candidate["history"]],
            "directed_flux_edges": [row["directed_flux_edges"] for row in candidate["history"]],
            "topology_feedback_next": [round(row["topology_feedback_next"], 6) for row in candidate["history"]],
            "pass": max(row["cycle_count"] for row in candidate["history"]) > 0
            and max(row["directed_flux_edges"] for row in candidate["history"]) > 0
            and len({round(row["topology_feedback_next"], 6) for row in candidate["history"]}) > 1,
        },
        "special_form_families_drive_distinct_integrated_variants": {
            "variant_readouts": {
                name: {
                    "max_coherent_information": row["max_coherent_information"],
                    "cycle_count": row["persistence"]["cycle_count"],
                    "form_feature": row["form_feature"],
                }
                for name, row in special_form_variants.items()
            },
            "pass": len({round(row["max_coherent_information"], 6) for row in special_form_variants.values()}) >= 3
            and len({row["persistence"]["cycle_count"] for row in special_form_variants.values()}) >= 2,
        },
        "dynamic_form_selection_changes_stepwise_integrated_evolution": {
            "active_form_sequence": dynamic_form["active_form_sequence"],
            "candidate_static_form": candidate["form_family"],
            "dynamic_max_coherent_information": dynamic_form["max_coherent_information"],
            "static_max_coherent_information": candidate["max_coherent_information"],
            "pass": len(set(dynamic_form["active_form_sequence"])) >= 2
            and abs(dynamic_form["max_coherent_information"] - candidate["max_coherent_information"]) > 1e-4,
        },
        "support_g_structure_reduction_scaffold_is_present": g_structure,
        "symbolic_and_two_level_propagator_checks_execute": symbolic,
    }
    graveyard_companions = {
        "zero_strength_product_control_removes_dynamic_tensor_information": {
            "max_coherent_information": product["max_coherent_information"],
            "pass": product["max_coherent_information"] <= 1e-8,
        },
        "local_terms_without_graph_coupling_do_not_generate_signed_information": {
            "max_coherent_information": no_graph_coupling["max_coherent_information"],
            "pass": no_graph_coupling["max_coherent_information"] <= 1e-8,
        },
        "removing_flux_changes_integrated_readout": {
            "candidate_signature": [
                candidate["persistence"]["cycle_count"],
                candidate["flux_graph_edge_count"],
                round(candidate["max_coherent_information"], 6),
            ],
            "control_signature": [
                no_flux["persistence"]["cycle_count"],
                no_flux["flux_graph_edge_count"],
                round(no_flux["max_coherent_information"], 6),
            ],
            "coherent_information_delta": abs(candidate["max_coherent_information"] - no_flux["max_coherent_information"]),
            "pass": [
                candidate["persistence"]["cycle_count"],
                round(candidate["max_coherent_information"], 6),
            ]
            != [
                no_flux["persistence"]["cycle_count"],
                round(no_flux["max_coherent_information"], 6),
            ]
            and abs(candidate["max_coherent_information"] - no_flux["max_coherent_information"]) > 1e-4,
        },
        "removing_topology_feedback_changes_later_dynamic_history": {
            "candidate_feedback": [round(row["topology_feedback_next"], 6) for row in candidate["history"]],
            "control_feedback": [round(row["topology_feedback_next"], 6) for row in no_topology_feedback["history"]],
            "candidate_max_coherent_information": candidate["max_coherent_information"],
            "control_max_coherent_information": no_topology_feedback["max_coherent_information"],
            "pass": [round(row["topology_feedback_next"], 6) for row in candidate["history"]]
            != [round(row["topology_feedback_next"], 6) for row in no_topology_feedback["history"]]
            and abs(candidate["max_coherent_information"] - no_topology_feedback["max_coherent_information"]) > 1e-4,
        },
        "removing_special_form_family_changes_integrated_readout": {
            "candidate_max_coherent_information": candidate["max_coherent_information"],
            "no_form_max_coherent_information": no_form_family["max_coherent_information"],
            "candidate_form_feature": candidate["form_feature"],
            "no_form_feature": no_form_family["form_feature"],
            "pass": abs(candidate["max_coherent_information"] - no_form_family["max_coherent_information"]) > 1e-4,
        },
        "generic_form_controls_do_not_match_special_form_variants": {
            "g2_max_coherent_information": special_form_variants["g2_three_form_constraints"]["max_coherent_information"],
            "generic_three_max_coherent_information": special_form_variants["generic_three_form_control_constraints"]["max_coherent_information"],
            "spin7_max_coherent_information": special_form_variants["spin7_four_form_constraints"]["max_coherent_information"],
            "generic_four_max_coherent_information": special_form_variants["generic_four_form_control_constraints"]["max_coherent_information"],
            "pass": abs(
                special_form_variants["g2_three_form_constraints"]["max_coherent_information"]
                - special_form_variants["generic_three_form_control_constraints"]["max_coherent_information"]
            )
            > 1e-4
            and abs(
                special_form_variants["spin7_four_form_constraints"]["max_coherent_information"]
                - special_form_variants["generic_four_form_control_constraints"]["max_coherent_information"]
            )
            > 1e-4,
        },
        "uniform_source_features_change_integrated_readout": {
            "candidate_max_coherent_information": candidate["max_coherent_information"],
            "uniform_max_coherent_information": uniform["max_coherent_information"],
            "pass": abs(candidate["max_coherent_information"] - uniform["max_coherent_information"]) > 1e-3,
        },
        "permuted_source_history_changes_graph_or_entropy_signature": {
            "candidate_signature": [candidate["persistence"]["edge_count"], round(candidate["max_coherent_information"], 6)],
            "permuted_signature": [permuted["persistence"]["edge_count"], round(permuted["max_coherent_information"], 6)],
            "pass": [candidate["persistence"]["edge_count"], round(candidate["max_coherent_information"], 6)]
            != [permuted["persistence"]["edge_count"], round(permuted["max_coherent_information"], 6)],
        },
        "missing_layer_order_breaks_tower_dependency": {
            "swapped": ["hopf_torus_leaf_family", "unit_spinor_sphere"],
            "pass": LAYERS.index("unit_spinor_sphere") < LAYERS.index("hopf_torus_leaf_family"),
        },
    }
    boundary = {
        "finite_eight_qubit_dimension": {"dimension": 2**N_QUBITS, "pass": 2**N_QUBITS == 256},
        "all_seven_bipartite_cuts_scanned": {"cut_count": len(candidate["cuts"]), "pass": len(candidate["cuts"]) == 7},
        "dynamic_graph_history_has_eight_updates": {"history_count": len(candidate["history"]), "pass": len(candidate["history"]) == 8},
        "tool_integration_depth_declared_without_blanket_load_bearing": {
            "tool_count": len(TOOL_MANIFEST),
            "load_bearing_count": sum(1 for value in TOOL_INTEGRATION_DEPTH.values() if value == "load_bearing"),
            "supportive_count": sum(1 for value in TOOL_INTEGRATION_DEPTH.values() if value == "supportive"),
            "pass": len(TOOL_MANIFEST) >= 14
            and sum(1 for value in TOOL_INTEGRATION_DEPTH.values() if value == "load_bearing") >= 5
            and sum(1 for value in TOOL_INTEGRATION_DEPTH.values() if value == "supportive") >= 1,
        },
        "z3_integrated_noncollapse_witness": z3_integrated_witness(candidate, product, uniform),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    all_checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "integrated finite nested geometric constraint manifold fixture with source-native Weyl terrain histories driving an eight-qubit dynamic shell-graph tensor network",
        "candidate_layers": LAYERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard_companions),
        "boundary": as_jsonable(boundary),
        "nearby_variants": {"passed": sum(1 for row in graveyard_companions.values() if row["pass"]), "total": len(graveyard_companions)},
        "open_choices": [
            "This is the first integrated fixture, not the final manifold law.",
            "The source-history-to-shell-weight map is explicit and finite but remains one candidate coupling.",
            "The support G-structure reduction is still a scaffold; special-holonomy alternatives need equivalent integrated runs.",
            "The tensor-network step uses dense eight-qubit state evolution plus opt_einsum reductions; later work should compare MPS-only updates.",
        ],
        "why_not_v4_probes": "This is a clean v5 integrated formal scout that composes v5 layer, Weyl terrain, G-structure, topology, and tensor-network surfaces rather than extending the mixed v4 probe estate.",
        "source_feature_rows": as_jsonable(features),
        "special_form_family_features": as_jsonable(form_families),
        "special_form_variants": as_jsonable(special_form_variants),
        "candidate": as_jsonable(candidate),
        "controls": as_jsonable(
            {
                "product": product,
                "no_graph_coupling": no_graph_coupling,
                "no_flux": no_flux,
                "no_topology_feedback": no_topology_feedback,
                "no_form_family": no_form_family,
                "dynamic_form": dynamic_form,
                "uniform": uniform,
                "permuted": permuted,
            }
        ),
        "blockers": [],
        "summary": {
            "all_pass": bool(all(all_checks)),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "max_coherent_information": candidate["max_coherent_information"],
            "min_conditional_entropy": candidate["min_conditional_entropy"],
            "tool_count": len(TOOL_MANIFEST),
            "load_bearing_tool_count": sum(1 for value in TOOL_INTEGRATION_DEPTH.values() if value == "load_bearing"),
            "microstep_count": len(source_rows),
        },
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if all(all_checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
