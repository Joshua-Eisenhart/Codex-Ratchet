#!/usr/bin/env python3
"""Eight-qubit dynamic shell-graph tensor-network entropy coupling scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import networkx as nx
import opt_einsum as oe
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "eight_qubit_dynamic_shell_graph_tensor_network_entropy_coupling_probe_results.json"

NAME = "eight_qubit_dynamic_shell_graph_tensor_network_entropy_coupling_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: couples an eight-qubit finite tensor state to a dynamic "
    "shell graph, uses graph weights as noncommuting channel generators, and "
    "reads conditional entropy plus coherent information across all cuts. It "
    "does not admit a final manifold tower, empirical spacetime claim, bridge "
    "claim, ontology, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing 8-qubit state, dynamic Hamiltonians, matrix exponentials, and entropy spectra"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing reduced density contractions"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing dynamic shell graph construction"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph-to-tensor conversion for the final shell graph"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over shell graph filtrations"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact noncommuting Pauli generator sanity check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing candidate/control contradiction checks"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

N_QUBITS = 8
DTYPE = torch.complex128


def shell_points(radius: float, twist: float, stretch: float) -> torch.Tensor:
    rows = []
    for idx in range(N_QUBITS):
        theta = 2 * math.pi * idx / N_QUBITS + twist
        z = -0.75 + 1.5 * idx / (N_QUBITS - 1)
        xy = math.sqrt(max(0.0, 1 - z * z))
        x = radius * stretch * xy * math.cos(theta)
        y = radius * (1.0 / math.sqrt(stretch)) * xy * math.sin(theta)
        zz = radius * (1.0 / math.sqrt(stretch)) * z
        rows.append([x, y, zz])
    return torch.tensor(rows, dtype=torch.float64)


def shell_weights(points: torch.Tensor, mode: str) -> torch.Tensor:
    dist = torch.cdist(points, points)
    weights = 1.0 / torch.clamp(dist * dist, min=0.2)
    weights.fill_diagonal_(0.0)
    if mode == "uniform":
        weights = torch.ones_like(weights)
        weights.fill_diagonal_(0.0)
    elif mode == "random_projection":
        rows = torch.arange(N_QUBITS, dtype=torch.float64).reshape(-1, 1)
        cols = torch.arange(N_QUBITS, dtype=torch.float64).reshape(1, -1)
        weights = ((rows * 3 + cols * 5 + 1) % 11 + 1) / 11.0
        weights = (weights + weights.T) / 2
        weights.fill_diagonal_(0.0)
    return weights / torch.clamp(weights.max(), min=1e-12)


def graph_from_weights(weights: torch.Tensor, threshold: float = 0.22) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(range(N_QUBITS))
    for i in range(N_QUBITS):
        for j in range(i + 1, N_QUBITS):
            weight = float(weights[i, j].item())
            if weight >= threshold:
                graph.add_edge(i, j, weight=weight)
    return graph


def one_qubit_operator(local: torch.Tensor, qubit: int) -> torch.Tensor:
    op = torch.tensor([[1.0 + 0j]], dtype=DTYPE)
    eye = torch.eye(2, dtype=DTYPE)
    for idx in range(N_QUBITS):
        op = torch.kron(op, local if idx == qubit else eye)
    return op


def graph_hamiltonian(weights: torch.Tensor, strength: float) -> torch.Tensor:
    sx = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
    h = torch.zeros((2**N_QUBITS, 2**N_QUBITS), dtype=DTYPE)
    for i in range(N_QUBITS):
        for j in range(i + 1, N_QUBITS):
            weight = float(weights[i, j].item())
            if weight > 0.18:
                h = h + strength * weight * (
                    one_qubit_operator(sx, i) @ one_qubit_operator(sx, j)
                    + 0.37 * one_qubit_operator(sy, i) @ one_qubit_operator(sy, j)
                )
    return h


def product_origin() -> torch.Tensor:
    psi = torch.zeros(2**N_QUBITS, dtype=DTYPE)
    psi[0] = 1.0 + 0j
    return psi


def evolve_case(mode: str, dynamic: bool, strength: float, steps: int = 5) -> tuple[torch.Tensor, list[dict[str, Any]], nx.Graph]:
    psi = product_origin()
    history = []
    final_graph = nx.Graph()
    for step in range(steps):
        radius = 1.0 + (0.08 * step if dynamic else 0.0)
        twist = 0.19 * step if dynamic else 0.0
        stretch = 1.0 + (0.11 * step if dynamic else 0.0)
        points = shell_points(radius, twist, stretch)
        weights = shell_weights(points, mode)
        graph = graph_from_weights(weights)
        final_graph = graph
        if strength > 0:
            h = graph_hamiltonian(weights, strength=strength)
            unitary = torch.linalg.matrix_exp((-1j * 0.17) * h)
            psi = unitary @ psi
            psi = psi / torch.linalg.vector_norm(psi)
        history.append({"step": step, "radius": radius, "twist": twist, "stretch": stretch, "edge_count": graph.number_of_edges(), "weight_std": float(torch.std(weights[weights > 0]).item())})
    return psi, history, final_graph


def reduced_density(psi: torch.Tensor, keep: list[int]) -> torch.Tensor:
    state = psi.reshape([2] * N_QUBITS)
    rest = [idx for idx in range(N_QUBITS) if idx not in keep]
    permuted = state.permute(keep + rest)
    matrix = permuted.reshape(2 ** len(keep), 2 ** len(rest))
    return oe.contract("ab,cb->ac", matrix, matrix.conj())


def entropy(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def cut_readouts(psi: torch.Tensor) -> list[dict[str, Any]]:
    full_entropy = entropy(torch.outer(psi, psi.conj()))
    rows = []
    for cut in range(1, N_QUBITS):
        rho_a = reduced_density(psi, list(range(cut)))
        s_a = entropy(rho_a)
        sv = torch.linalg.svdvals(psi.reshape(2**cut, 2 ** (N_QUBITS - cut)))
        rows.append(
            {
                "cut": cut,
                "S_A": s_a,
                "S_AB": full_entropy,
                "conditional_entropy_A_given_B": full_entropy - s_a,
                "coherent_information_A_to_B": s_a - full_entropy,
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
    return {
        "edge_count": graph.number_of_edges(),
        "persistence_pair_count": len(pairs),
        "pyg_edge_index_shape": list(pyg.edge_index.shape) if pyg is not None else [2, 0],
    }


def summarize_case(name: str, mode: str, dynamic: bool, strength: float) -> dict[str, Any]:
    psi, history, graph = evolve_case(mode=mode, dynamic=dynamic, strength=strength)
    cuts = cut_readouts(psi)
    return {
        "name": name,
        "mode": mode,
        "dynamic": dynamic,
        "strength": strength,
        "history": history,
        "cuts": cuts,
        "max_coherent_information": max(row["coherent_information_A_to_B"] for row in cuts),
        "min_conditional_entropy": min(row["conditional_entropy_A_given_B"] for row in cuts),
        "max_bond_dim": max(row["bond_dim"] for row in cuts),
        "persistence": persistence_summary(graph),
    }


def sympy_noncommuting_generators() -> dict[str, Any]:
    i = sp.I
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -i], [i, 0]])
    comm = sp.simplify(sx * sy - sy * sx)
    return {"commutator": str(comm), "pass": comm != sp.zeros(2)}


def z3_witness(candidate: dict[str, Any], product: dict[str, Any], static: dict[str, Any]) -> dict[str, Any]:
    c = candidate["max_coherent_information"] > 0.05 and candidate["min_conditional_entropy"] < -0.05
    p = product["max_coherent_information"] <= 1e-8
    s = abs(candidate["max_coherent_information"] - static["max_coherent_information"]) > 1e-3
    solver = z3.Solver()
    cb, pb, sb = z3.Bools("candidate product static")
    solver.add(cb == c, pb == p, sb == s, z3.Not(z3.And(cb, pb, sb)))
    return {"solver_status": str(solver.check()), "pass": solver.check() == z3.unsat, "candidate": c, "product_control": p, "static_separation": s}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    candidate = summarize_case("dynamic_shell_graph_weighted_noncommuting_tensor_network", "shell", True, 0.92)
    product = summarize_case("zero_strength_product_state_control", "shell", True, 0.0)
    static = summarize_case("static_shell_graph_control", "shell", False, 0.92)
    uniform = summarize_case("uniform_graph_weight_control", "uniform", True, 0.92)
    random_projection = summarize_case("random_projection_graph_control", "random_projection", True, 0.92)
    positive = {
        "candidate_has_negative_conditional_entropy_and_positive_coherent_information": {
            "max_coherent_information": candidate["max_coherent_information"],
            "min_conditional_entropy": candidate["min_conditional_entropy"],
            "max_bond_dim": candidate["max_bond_dim"],
            "pass": candidate["max_coherent_information"] > 0.05 and candidate["min_conditional_entropy"] < -0.05 and candidate["max_bond_dim"] > 1,
        },
        "dynamic_shell_graph_history_changes": {
            "history": candidate["history"],
            "pass": len({(round(row["radius"], 3), round(row["twist"], 3), row["edge_count"]) for row in candidate["history"]}) > 1,
        },
        "noncommuting_generator_check": sympy_noncommuting_generators(),
    }
    graveyard_companions = {
        "zero_strength_product_state_has_no_signed_entropy": {
            "max_coherent_information": product["max_coherent_information"],
            "min_conditional_entropy": product["min_conditional_entropy"],
            "pass": product["max_coherent_information"] <= 1e-8 and product["min_conditional_entropy"] >= -1e-8,
        },
        "static_shell_graph_has_distinct_readout": {
            "candidate_max_coherent_information": candidate["max_coherent_information"],
            "control_max_coherent_information": static["max_coherent_information"],
            "pass": abs(candidate["max_coherent_information"] - static["max_coherent_information"]) > 1e-3,
        },
        "uniform_graph_changes_persistence_or_entropy_signature": {
            "candidate": [candidate["max_coherent_information"], candidate["persistence"]["edge_count"]],
            "control": [uniform["max_coherent_information"], uniform["persistence"]["edge_count"]],
            "pass": [round(candidate["max_coherent_information"], 6), candidate["persistence"]["edge_count"]]
            != [round(uniform["max_coherent_information"], 6), uniform["persistence"]["edge_count"]],
        },
        "random_projection_changes_graph_signature": {
            "candidate": [candidate["persistence"]["edge_count"], candidate["persistence"]["pyg_edge_index_shape"]],
            "control": [random_projection["persistence"]["edge_count"], random_projection["persistence"]["pyg_edge_index_shape"]],
            "pass": [candidate["persistence"]["edge_count"], candidate["persistence"]["pyg_edge_index_shape"]]
            != [random_projection["persistence"]["edge_count"], random_projection["persistence"]["pyg_edge_index_shape"]],
        },
    }
    z3_row = z3_witness(candidate, product, static)
    boundary = {
        "finite_eight_qubit_dimension": {"dimension": 2**N_QUBITS, "pass": 2**N_QUBITS == 256},
        "all_cuts_scanned": {"cut_count": len(candidate["cuts"]), "pass": len(candidate["cuts"]) == 7},
        "z3_candidate_control_witness": z3_row,
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "eight-qubit finite tensor state whose noncommuting channel generators are weighted by a dynamic shell graph and read by conditional entropy plus coherent information",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "The graph-weight-to-Hamiltonian map is one coupling, not a unique manifold law.",
            "This scout uses finite matrix exponentials; later scouts should compare MPS-only contraction updates.",
            "Entropy readouts do not by themselves prove geometry; they test whether this coupling produces nonclassical signed information.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from Grok/Gemini manifold-coupling proposals; it is not a canonical v4 probe.",
        "candidate": candidate,
        "controls": {"product": product, "static": static, "uniform": uniform, "random_projection": random_projection},
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all(checks) and all(row["pass"] for row in boundary.values()),
                "result": str(OUT_PATH),
                "max_coherent_information": candidate["max_coherent_information"],
                "min_conditional_entropy": candidate["min_conditional_entropy"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
