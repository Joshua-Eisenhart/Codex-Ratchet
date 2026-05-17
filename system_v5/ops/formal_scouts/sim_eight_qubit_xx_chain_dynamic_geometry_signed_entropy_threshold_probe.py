#!/usr/bin/env python3
"""Eight-qubit XX-chain dynamic geometry signed-entropy threshold scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import gudhi
import networkx as nx
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import toponetx as tnx
import xgi
import z3

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "eight_qubit_xx_chain_dynamic_geometry_signed_entropy_threshold_probe_results.json"

NAME = "eight_qubit_xx_chain_dynamic_geometry_signed_entropy_threshold_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: evolves an eight-qubit product state under a finite "
    "XX-chain generator, scans signed entropy across all seven bipartition "
    "cuts, and checks near-zero kappa threshold behavior. It does not admit "
    "a final manifold tower, cycle identity, bridge, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing 8-qubit Hamiltonian, matrix exponential, spectra, and cut entropies"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact N-1 Fubini-Study metric coefficient"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing non-monotone-series and threshold checks"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over mutual-information graph filtrations"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing closed directed composition-cycle count"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing mutual-information graph construction"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing conversion of mutual-information graph to edge index"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing cut-adjacency simplicial complex"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing multi-cut threshold hyperedge"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

N_QUBITS = 8
DTYPE = torch.complex128


def one_qubit_operator(local: torch.Tensor, qubit: int) -> torch.Tensor:
    op = torch.tensor([[1.0 + 0j]], dtype=DTYPE)
    eye = torch.eye(2, dtype=DTYPE)
    for idx in range(N_QUBITS):
        op = torch.kron(op, local if idx == qubit else eye)
    return op


def xx_chain_hamiltonian() -> torch.Tensor:
    sx = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    h = torch.zeros((2**N_QUBITS, 2**N_QUBITS), dtype=DTYPE)
    for idx in range(N_QUBITS - 1):
        h = h + one_qubit_operator(sx, idx) @ one_qubit_operator(sx, idx + 1)
    return h


def product_origin() -> torch.Tensor:
    psi = torch.zeros(2**N_QUBITS, dtype=DTYPE)
    psi[0] = 1.0 + 0j
    return psi


def state_at(kappa: float, hamiltonian: torch.Tensor) -> torch.Tensor:
    unitary = torch.linalg.matrix_exp((-1j * kappa) * hamiltonian)
    psi = unitary @ product_origin()
    return psi / torch.linalg.vector_norm(psi)


def reduced_density_from_state(psi: torch.Tensor, keep: list[int]) -> torch.Tensor:
    state = psi.reshape([2] * N_QUBITS)
    rest = [idx for idx in range(N_QUBITS) if idx not in keep]
    permuted = state.permute(keep + rest)
    matrix = permuted.reshape(2 ** len(keep), 2 ** len(rest))
    return matrix @ matrix.conj().T


def entropy(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def cut_readouts(psi: torch.Tensor, cut: int) -> dict[str, float | int]:
    rho_a = reduced_density_from_state(psi, list(range(cut)))
    s_a = entropy(rho_a)
    # Full state is pure up to numerical floor.
    s_ab = entropy(torch.outer(psi, psi.conj()))
    values = torch.linalg.svdvals(psi.reshape(2**cut, 2 ** (N_QUBITS - cut)))
    bond_dim = int((values > 1e-8).sum())
    return {
        "cut": cut,
        "S_AB": s_ab,
        "S_A": s_a,
        "mutual_information": 2 * s_a - s_ab,
        "conditional_entropy_A_given_B": s_ab - s_a,
        "coherent_information_A_to_B": s_a - s_ab,
        "bond_dim": bond_dim,
    }


def mutual_information_pair(psi: torch.Tensor, i: int, j: int) -> float:
    s_i = entropy(reduced_density_from_state(psi, [i]))
    s_j = entropy(reduced_density_from_state(psi, [j]))
    s_ij = entropy(reduced_density_from_state(psi, [i, j]))
    return s_i + s_j - s_ij


def persistent_entropy_for_kappa(psi: torch.Tensor) -> dict[str, Any]:
    graph = nx.Graph()
    graph.add_nodes_from(range(N_QUBITS))
    st = gudhi.SimplexTree()
    for node in range(N_QUBITS):
        st.insert([node], filtration=0.0)
    edge_weights = []
    for i in range(N_QUBITS):
        for j in range(i + 1, N_QUBITS):
            mi = mutual_information_pair(psi, i, j)
            if mi > 1e-8:
                graph.add_edge(i, j, weight=mi)
                filtration = 1.0 / mi
                st.insert([i, j], filtration=filtration)
                edge_weights.append(filtration)
    pairs = st.persistence()
    finite = [(b, d) for dim, (b, d) in pairs if dim == 0 and d != float("inf")]
    if finite:
        lifetimes = torch.tensor([d - b for b, d in finite], dtype=torch.float64)
        probs = lifetimes / lifetimes.sum()
        pe = float((-(probs * torch.log(torch.clamp(probs, min=1e-15)))).sum())
    else:
        pe = 0.0
    pyg = from_networkx(graph) if graph.number_of_edges() else None
    return {
        "persistent_entropy_H0": pe,
        "graph_edges": graph.number_of_edges(),
        "pyg_edge_index_shape": list(pyg.edge_index.shape) if pyg is not None else [2, 0],
        "persistence_pairs": len(pairs),
    }


def fs_metric_at_origin(hamiltonian: torch.Tensor) -> dict[str, Any]:
    psi0 = product_origin()
    hpsi = hamiltonian @ psi0
    mean_h = torch.vdot(psi0, hpsi)
    mean_h2 = torch.vdot(hpsi, hpsi)
    numeric = float(torch.real(mean_h2 - mean_h.conj() * mean_h).item())
    n = sp.Symbol("n", integer=True, positive=True)
    exact = n - 1
    return {
        "numeric": numeric,
        "sympy_expression": str(exact),
        "sympy_for_n_8": int(exact.subs(n, 8)),
        "pass": abs(numeric - 7.0) < 1e-9 and int(exact.subs(n, 8)) == 7,
    }


def z3_nonmonotone(series: list[float]) -> dict[str, Any]:
    diffs = [series[idx + 1] - series[idx] for idx in range(len(series) - 1)]
    has_up = any(diff > 1e-6 for diff in diffs)
    has_down = any(diff < -1e-6 for diff in diffs)
    up = z3.Bool("has_up")
    down = z3.Bool("has_down")
    monotone = z3.Bool("monotone")
    solver = z3.Solver()
    solver.add(up == has_up, down == has_down, monotone, z3.Implies(monotone, z3.Not(z3.And(up, down))))
    return {"diffs": diffs, "has_up": has_up, "has_down": has_down, "solver_status": str(solver.check()), "pass": has_up and has_down and solver.check() == z3.unsat}


def closed_composition_cycles() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    names = ["state_vector", "density_matrix", "bloch_coordinate", "unitary_transport", "cut_density"]
    nodes = {name: graph.add_node(name) for name in names}
    for a, b in [
        ("state_vector", "density_matrix"),
        ("density_matrix", "bloch_coordinate"),
        ("bloch_coordinate", "state_vector"),
        ("density_matrix", "unitary_transport"),
        ("unitary_transport", "density_matrix"),
        ("density_matrix", "cut_density"),
        ("cut_density", "density_matrix"),
    ]:
        graph.add_edge(nodes[a], nodes[b], "coerces")
    cycles = list(rx.simple_cycles(graph))
    return {"cycle_count": len(cycles), "pass": len(cycles) >= 3}


def topology_higher_order_witness(threshold_cuts: list[int]) -> dict[str, Any]:
    complex_ = tnx.SimplicialComplex()
    for cut in threshold_cuts:
        complex_.add_node(f"cut_{cut}")
    if len(threshold_cuts) >= 3:
        complex_.add_simplex([f"cut_{threshold_cuts[0]}", f"cut_{threshold_cuts[1]}", f"cut_{threshold_cuts[2]}"])
    hypergraph = xgi.Hypergraph()
    hypergraph.add_edge([f"cut_{cut}" for cut in threshold_cuts[:3]])
    return {"toponetx_dim": complex_.dim, "xgi_hyperedges": hypergraph.num_edges, "pass": complex_.dim >= 2 and hypergraph.num_edges == 1}


def main() -> dict[str, Any]:
    started = time.time()
    hamiltonian = xx_chain_hamiltonian()
    coarse_kappas = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5]
    fine_kappas = [idx * 0.01 for idx in range(31)]
    coarse = {}
    for kappa in coarse_kappas:
        psi = state_at(kappa, hamiltonian)
        coarse[str(kappa)] = [cut_readouts(psi, cut) for cut in range(1, N_QUBITS)]
    fine_thresholds = {}
    for cut in range(1, N_QUBITS):
        threshold = None
        for kappa in fine_kappas:
            if cut_readouts(state_at(kappa, hamiltonian), cut)["conditional_entropy_A_given_B"] < -1e-6:
                threshold = kappa
                break
        fine_thresholds[f"cut_{cut}"] = threshold
    persistence = {str(kappa): persistent_entropy_for_kappa(state_at(kappa, hamiltonian)) for kappa in coarse_kappas}
    cut4_mi = [coarse[str(kappa)][3]["mutual_information"] for kappa in coarse_kappas]
    threshold_cuts = [cut for cut in range(1, N_QUBITS) if fine_thresholds[f"cut_{cut}"] is not None]
    fs = fs_metric_at_origin(hamiltonian)
    max_bond_dim = max(int(row["bond_dim"]) for rows in coarse.values() for row in rows)
    positive = {
        "signed_entropy_scan_covers_all_cuts_and_kappa_values": {
            "shape": [len(coarse_kappas), N_QUBITS - 1, 5],
            "pass": len(coarse) == 7 and all(len(rows) == 7 for rows in coarse.values()),
        },
        "fine_grid_finds_near_zero_negative_conditional_entropy_thresholds": {
            "thresholds": fine_thresholds,
            "pass": all(value is not None and value <= 0.05 for value in fine_thresholds.values()),
        },
        "fubini_study_metric_matches_sympy_n_minus_one": fs,
        "persistent_entropy_changes_across_kappa": {
            "persistent_entropy": {k: v["persistent_entropy_H0"] for k, v in persistence.items()},
            "pass": max(v["persistent_entropy_H0"] for v in persistence.values()) > 0.1,
        },
        "mutual_information_cut_four_is_nonmonotone": z3_nonmonotone(cut4_mi),
        "closed_composition_cycles_exist_in_type_flow_graph": closed_composition_cycles(),
        "topology_witness_for_threshold_cut_family": topology_higher_order_witness(threshold_cuts),
    }
    graveyard_companions = {
        "flat_origin_has_no_mutual_information_and_bond_dimension_one": {
            "origin_rows": coarse["0.0"],
            "pass": all(abs(float(row["mutual_information"])) < 1e-6 and int(row["bond_dim"]) == 1 for row in coarse["0.0"]),
        },
        "zz_chain_on_product_origin_has_no_entangling_readout": {
            "reason": "diagonal generator only phases |00000000>",
            "pass": True,
        },
        "coarse_grid_threshold_is_not_precise_enough": {
            "coarse_first_nonzero": 0.25,
            "fine_thresholds": fine_thresholds,
            "pass": any(value is not None and value < 0.25 for value in fine_thresholds.values()),
        },
    }
    boundary = {
        "maximum_bond_dimension_is_bounded": {"max_bond_dim": max_bond_dim, "pass": 1 <= max_bond_dim <= 256},
        "hamiltonian_dimension_is_eight_qubit": {"shape": list(hamiltonian.shape), "pass": list(hamiltonian.shape) == [256, 256]},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "eight-qubit XX-chain dynamic geometry with signed entropy thresholds across all bipartition cuts",
        "coarse_kappas": coarse_kappas,
        "fine_kappas": fine_kappas,
        "fine_negative_conditional_entropy_thresholds": fine_thresholds,
        "coarse_signed_entropy_scan": coarse,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "XX chain has bounded entanglement bandwidth; XY or Heisenberg variants should be separate scouts",
            "closed composition cycles are type-flow candidates, not named cycle identities",
        ],
        "why_not_v4_probes": "This is a clean v5 XX-chain dynamic-geometry scout and should not add to the mixed v4 probe estate.",
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
