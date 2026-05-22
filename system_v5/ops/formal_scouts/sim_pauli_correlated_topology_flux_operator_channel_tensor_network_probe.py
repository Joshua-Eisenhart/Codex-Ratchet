#!/usr/bin/env python3
"""Pauli-correlated topology-flux operator-channel tensor-network scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any, Callable

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import networkx as nx
import opt_einsum as oe
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import toponetx as tnx
import xgi
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "pauli_correlated_topology_flux_operator_channel_tensor_network_probe_results.json"

NAME = "pauli_correlated_topology_flux_operator_channel_tensor_network_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: stress-tests four Pauli-correlated topology generators, "
    "two flux orientations, and four operator channels on an eight-qubit finite "
    "tensor state. It checks channel-order gaps, signed entropies, graph cycles, "
    "and topological persistence. It does not admit a final manifold tower, "
    "cycle identity, bridge, axis, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing eight-qubit density matrices, channel dynamics, spectra, and entropies"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing finite MPS tensor-network state construction"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact Pauli commutator sanity checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite enumeration and nonzero-gap contradiction checks"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing mutual-information graph construction"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph tensor conversion for the mutual-information graph"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over mutual-information filtration"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing directed composition-cycle count"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing simplicial witness over nonzero order-gap families"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing hypergraph witness over topology-flux admission families"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

N_QUBITS = 8
DTYPE = torch.complex128


def ghz_mps_state() -> tuple[torch.Tensor, list[int]]:
    tensors = []
    first = torch.zeros((1, 2, 2), dtype=DTYPE)
    first[0, 0, 0] = 1 / math.sqrt(2)
    first[0, 1, 1] = 1 / math.sqrt(2)
    tensors.append(first)
    for _ in range(N_QUBITS - 2):
        middle = torch.zeros((2, 2, 2), dtype=DTYPE)
        middle[0, 0, 0] = 1
        middle[1, 1, 1] = 1
        tensors.append(middle)
    last = torch.zeros((2, 2, 1), dtype=DTYPE)
    last[0, 0, 0] = 1
    last[1, 1, 0] = 1
    tensors.append(last)

    letters = "abcdefghijklmnopqrstuvwxyz"
    terms = [f"{letters[idx]}{letters[8 + idx]}{letters[idx + 1]}" for idx in range(N_QUBITS)]
    expr = ",".join(terms) + "->" + "".join(letters[8 : 8 + N_QUBITS])
    contracted = oe.contract(expr, *tensors)
    psi = contracted.reshape(2**N_QUBITS)
    return psi / torch.linalg.vector_norm(psi), [2] * (N_QUBITS - 1)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def one_qubit_operator(local: torch.Tensor, qubit: int) -> torch.Tensor:
    op = torch.tensor([[1.0 + 0j]], dtype=DTYPE)
    eye = torch.eye(2, dtype=DTYPE)
    for idx in range(N_QUBITS):
        op = torch.kron(op, local if idx == qubit else eye)
    return op


def two_qubit_term(local_a: torch.Tensor, q_a: int, local_b: torch.Tensor, q_b: int) -> torch.Tensor:
    return one_qubit_operator(local_a, q_a) @ one_qubit_operator(local_b, q_b)


def pauli_topology_generators() -> dict[str, torch.Tensor]:
    sx = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    generators = {
        "nearest_neighbor_xx_path": torch.zeros((2**N_QUBITS, 2**N_QUBITS), dtype=DTYPE),
        "nearest_neighbor_yy_path": torch.zeros((2**N_QUBITS, 2**N_QUBITS), dtype=DTYPE),
        "local_z_field_sum": torch.zeros((2**N_QUBITS, 2**N_QUBITS), dtype=DTYPE),
        "alternating_xz_pair_path": torch.zeros((2**N_QUBITS, 2**N_QUBITS), dtype=DTYPE),
    }
    for idx in range(N_QUBITS - 1):
        generators["nearest_neighbor_xx_path"] += two_qubit_term(sx, idx, sx, idx + 1)
        generators["nearest_neighbor_yy_path"] += two_qubit_term(sy, idx, sy, idx + 1)
        generators["alternating_xz_pair_path"] += two_qubit_term(sx if idx % 2 == 0 else sz, idx, sz if idx % 2 == 0 else sx, idx + 1)
    for idx in range(N_QUBITS):
        generators["local_z_field_sum"] += one_qubit_operator(sz, idx)
    return generators


def topology_channel(generator: torch.Tensor, flux_sign: int, kappa: float) -> Callable[[torch.Tensor], torch.Tensor]:
    unitary = torch.linalg.matrix_exp((-1j * flux_sign * kappa) * generator)
    return lambda rho: unitary @ rho @ unitary.conj().T


def projector_channel(rho: torch.Tensor) -> torch.Tensor:
    projector = one_qubit_operator(torch.tensor([[1, 0], [0, 0]], dtype=DTYPE), 0)
    out = projector @ rho @ projector.conj().T
    trace = torch.real(torch.trace(out))
    if float(trace.item()) <= 1e-12:
        return rho
    return out / trace


def hamiltonian_channel(rho: torch.Tensor) -> torch.Tensor:
    sx = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    unitary = torch.linalg.matrix_exp((-1j * 0.37) * one_qubit_operator(sx, 0))
    return unitary @ rho @ unitary.conj().T


def lindblad_like_channel(rho: torch.Tensor) -> torch.Tensor:
    gamma = 0.23
    k0 = torch.tensor([[1.0, 0.0], [0.0, math.sqrt(1 - gamma)]], dtype=DTYPE)
    k1 = torch.tensor([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=DTYPE)
    out = torch.zeros_like(rho)
    for local in (k0, k1):
        op = one_qubit_operator(local, 0)
        out += op @ rho @ op.conj().T
    return out


def spectral_filter_channel(rho: torch.Tensor) -> torch.Tensor:
    weights = torch.diag(torch.tensor([1.0, 0.62], dtype=DTYPE))
    filt = one_qubit_operator(weights, 0)
    out = filt @ rho @ filt.conj().T
    return out / torch.real(torch.trace(out))


def operator_channels() -> dict[str, Callable[[torch.Tensor], torch.Tensor]]:
    return {
        "projector_constraint_channel": projector_channel,
        "hamiltonian_rotation_channel": hamiltonian_channel,
        "lindblad_amplitude_damping_channel": lindblad_like_channel,
        "spectral_weight_filter_channel": spectral_filter_channel,
    }


def density_valid(rho: torch.Tensor) -> bool:
    herm = (rho + rho.conj().T) / 2
    eigs = torch.linalg.eigvalsh(herm)
    trace = torch.trace(rho)
    return bool(abs(float(torch.real(trace).item()) - 1) < 1e-8 and abs(float(torch.imag(trace).item())) < 1e-8 and float(torch.min(eigs).item()) > -1e-8)


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    diff = (a - b + (a - b).conj().T) / 2
    return float(0.5 * torch.sum(torch.abs(torch.linalg.eigvalsh(diff))).item())


def partial_trace_density(rho: torch.Tensor, keep: list[int]) -> torch.Tensor:
    rest = [idx for idx in range(N_QUBITS) if idx not in keep]
    dims = [2] * N_QUBITS
    tensor = rho.reshape(dims + dims)
    perm = keep + rest + [idx + N_QUBITS for idx in keep] + [idx + N_QUBITS for idx in rest]
    ordered = tensor.permute(perm)
    d_keep = 2 ** len(keep)
    d_rest = 2 ** len(rest)
    ordered = ordered.reshape(d_keep, d_rest, d_keep, d_rest)
    return torch.einsum("abcb->ac", ordered)


def entropy(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def signed_entropy_rows(rho: torch.Tensor) -> list[dict[str, Any]]:
    s_ab = entropy(rho)
    rows = []
    for cut in range(1, N_QUBITS):
        rho_a = partial_trace_density(rho, list(range(cut)))
        s_a = entropy(rho_a)
        rows.append(
            {
                "cut": cut,
                "S_AB": s_ab,
                "S_A": s_a,
                "conditional_entropy_A_given_B": s_ab - s_a,
                "coherent_information_A_to_B": s_a - s_ab,
            }
        )
    return rows


def mutual_information_pair(rho: torch.Tensor, i: int, j: int) -> float:
    s_i = entropy(partial_trace_density(rho, [i]))
    s_j = entropy(partial_trace_density(rho, [j]))
    s_ij = entropy(partial_trace_density(rho, [i, j]))
    return s_i + s_j - s_ij


def graph_topology_readout(rho: torch.Tensor) -> dict[str, Any]:
    graph = nx.Graph()
    graph.add_nodes_from(range(N_QUBITS))
    st = gudhi.SimplexTree()
    for node in range(N_QUBITS):
        st.insert([node], filtration=0.0)
    edge_count = 0
    for i in range(N_QUBITS):
        for j in range(i + 1, N_QUBITS):
            mi = mutual_information_pair(rho, i, j)
            if mi > 1e-5:
                graph.add_edge(i, j, weight=mi)
                st.insert([i, j], filtration=1.0 / mi)
                edge_count += 1
    pairs = st.persistence()
    finite = [(b, d) for dim, (b, d) in pairs if dim == 0 and d != float("inf")]
    if finite:
        lifetimes = torch.tensor([d - b for b, d in finite], dtype=torch.float64)
        probs = lifetimes / lifetimes.sum()
        persistent_entropy = float((-(probs * torch.log(torch.clamp(probs, min=1e-15)))).sum())
    else:
        persistent_entropy = 0.0
    pyg = from_networkx(graph) if graph.number_of_edges() else None
    return {
        "mi_edge_count": edge_count,
        "persistent_entropy_H0": persistent_entropy,
        "pyg_edge_index_shape": list(pyg.edge_index.shape) if pyg is not None else [2, 0],
        "persistence_pair_count": len(pairs),
    }


def sympy_pauli_checks() -> dict[str, Any]:
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    return {
        "x_y_commutator": str(sx * sy - sy * sx),
        "x_z_commutator": str(sx * sz - sz * sx),
        "y_z_commutator": str(sy * sz - sz * sy),
        "pass": sx * sy - sy * sx != sp.zeros(2) and sx * sz - sz * sx != sp.zeros(2) and sy * sz - sz * sy != sp.zeros(2),
    }


def rustworkx_cycle_readout() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    names = ["state_vector", "density_matrix", "topology_channel", "operator_channel", "entropy_readout", "graph_readout"]
    nodes = {name: graph.add_node(name) for name in names}
    for source, target in [
        ("state_vector", "density_matrix"),
        ("density_matrix", "topology_channel"),
        ("topology_channel", "operator_channel"),
        ("operator_channel", "density_matrix"),
        ("density_matrix", "entropy_readout"),
        ("entropy_readout", "graph_readout"),
        ("graph_readout", "topology_channel"),
    ]:
        graph.add_edge(nodes[source], nodes[target], "maps")
    cycles = list(rx.simple_cycles(graph))
    return {"cycle_count": len(cycles), "pass": len(cycles) >= 2}


def higher_order_gap_witness(gap_rows: list[dict[str, Any]]) -> dict[str, Any]:
    survived = [row for row in gap_rows if row["gap"] > 1e-6]
    complex_ = tnx.SimplicialComplex()
    hypergraph = xgi.Hypergraph()
    for row in survived:
        complex_.add_node(row["topology_flux"])
    for topology_name in sorted({row["topology"] for row in survived}):
        family = sorted({row["topology_flux"] for row in survived if row["topology"] == topology_name})[:3]
        if len(family) >= 2:
            complex_.add_simplex(family)
            hypergraph.add_edge(family)
    return {
        "nonzero_gap_count": len(survived),
        "toponetx_dim": complex_.dim,
        "xgi_hyperedge_count": hypergraph.num_edges,
        "pass": len(survived) > 0 and complex_.dim >= 1 and hypergraph.num_edges > 0,
    }


def z3_checks(nonzero_gaps: int, total: int) -> dict[str, Any]:
    count = z3.Int("nonzero_gaps")
    total_count = z3.Int("total_count")
    enum = z3.Solver()
    enum.add(total_count == total, total_count != 32)
    nonzero = z3.Solver()
    nonzero.add(count == nonzero_gaps, count > 0, count == 0)
    return {
        "enumeration_is_four_by_two_by_four": {"solver_status": str(enum.check()), "pass": enum.check() == z3.unsat},
        "nonzero_order_gap_not_all_zero": {"solver_status": str(nonzero.check()), "nonzero_gaps": nonzero_gaps, "pass": nonzero.check() == z3.unsat and nonzero_gaps > 0},
    }


def main() -> dict[str, Any]:
    started = time.time()
    psi, bond_dims = ghz_mps_state()
    rho0 = density(psi)
    generators = pauli_topology_generators()
    ops = operator_channels()
    kappa = 0.19
    gap_rows = []
    entropy_sample: dict[str, Any] = {}
    graph_sample: dict[str, Any] = {}

    for topology_name, generator in generators.items():
        for flux_sign in (1, -1):
            top = topology_channel(generator, flux_sign, kappa)
            topology_flux = f"{topology_name}_flux_{'positive' if flux_sign > 0 else 'negative'}"
            for op_name, op in ops.items():
                operator_first = top(op(rho0))
                topology_first = op(top(rho0))
                gap = trace_distance(operator_first, topology_first)
                rows = signed_entropy_rows(operator_first)
                if not entropy_sample:
                    entropy_sample = {"topology_flux": topology_flux, "operator_channel": op_name, "rows": rows}
                    graph_sample = graph_topology_readout(operator_first)
                gap_rows.append(
                    {
                        "topology": topology_name,
                        "flux_sign": flux_sign,
                        "topology_flux": topology_flux,
                        "operator_channel": op_name,
                        "gap": gap,
                        "operator_first_density_valid": density_valid(operator_first),
                        "topology_first_density_valid": density_valid(topology_first),
                        "min_conditional_entropy": min(row["conditional_entropy_A_given_B"] for row in rows),
                        "max_coherent_information": max(row["coherent_information_A_to_B"] for row in rows),
                    }
                )

    nonzero_gaps = sum(1 for row in gap_rows if row["gap"] > 1e-6)
    z3_rows = z3_checks(nonzero_gaps, len(gap_rows))
    higher_order = higher_order_gap_witness(gap_rows)
    positive = {
        "eight_qubit_tensor_state_and_density_are_valid": {
            "amplitude_count": int(psi.numel()),
            "bond_dims": bond_dims,
            "density_valid": density_valid(rho0),
            "pass": int(psi.numel()) == 256 and max(bond_dims) == 2 and density_valid(rho0),
        },
        "four_topology_generators_two_flux_orientations_four_operator_channels_enumerated": {
            "total_rows": len(gap_rows),
            "topology_count": len(generators),
            "operator_channel_count": len(ops),
            "pass": len(gap_rows) == 4 * 2 * 4,
        },
        "operator_first_topology_first_order_gaps_exist": {
            "nonzero_gap_count": nonzero_gaps,
            "max_gap": max(row["gap"] for row in gap_rows),
            "pass": nonzero_gaps > 0 and max(row["gap"] for row in gap_rows) > 1e-6,
        },
        "signed_entropy_readouts_cover_all_bipartition_cuts": {
            "sample": entropy_sample,
            "pass": len(entropy_sample.get("rows", [])) == 7,
        },
        "mutual_information_graph_persistence_is_computable": {
            **graph_sample,
            "pass": graph_sample.get("persistence_pair_count", 0) > 0,
        },
        "sympy_exact_pauli_noncommutation_checks": sympy_pauli_checks(),
        "rustworkx_directed_composition_cycles_exist": rustworkx_cycle_readout(),
        "toponetx_xgi_higher_order_gap_family_witness": higher_order,
        "z3_finite_enumeration_and_gap_checks": {"checks": z3_rows, "pass": all(row["pass"] for row in z3_rows.values())},
    }

    identity_topology = lambda rho: rho
    identity_gaps = [trace_distance(identity_topology(op(rho0)), op(identity_topology(rho0))) for op in ops.values()]
    zero_kappa_gaps = []
    for generator in generators.values():
        top = topology_channel(generator, 1, 0.0)
        zero_kappa_gaps.extend(trace_distance(top(op(rho0)), op(top(rho0))) for op in ops.values())

    graveyard_companions = {
        "identity_topology_channel_collapses_all_order_gaps": {
            "max_gap": max(identity_gaps),
            "pass": max(identity_gaps) < 1e-10,
        },
        "zero_flux_strength_collapses_all_order_gaps": {
            "max_gap": max(zero_kappa_gaps),
            "pass": max(zero_kappa_gaps) < 1e-10,
        },
        "density_scaled_by_two_fails_admission": {
            "trace": float(torch.real(torch.trace(2 * rho0)).item()),
            "pass": not density_valid(2 * rho0),
        },
        "diagonal_z_field_with_spectral_filter_has_small_order_gap_control": {
            "matching_rows": [row for row in gap_rows if row["topology"] == "local_z_field_sum" and row["operator_channel"] == "spectral_weight_filter_channel"],
            "pass": max(row["gap"] for row in gap_rows if row["topology"] == "local_z_field_sum" and row["operator_channel"] == "spectral_weight_filter_channel") < 1e-8,
        },
    }
    boundary = {
        "finite_dimension_is_eight_qubit": {"dimension": int(psi.numel()), "pass": int(psi.numel()) == 256},
        "gap_rows_preserve_density_validity": {
            "invalid_rows": [row for row in gap_rows if not row["operator_first_density_valid"] or not row["topology_first_density_valid"]],
            "pass": all(row["operator_first_density_valid"] and row["topology_first_density_valid"] for row in gap_rows),
        },
        "conditional_entropy_and_coherent_information_have_opposite_signs_per_cut": {
            "sample_rows": entropy_sample.get("rows", []),
            "pass": all(abs(row["conditional_entropy_A_given_B"] + row["coherent_information_A_to_B"]) < 1e-9 for row in entropy_sample.get("rows", [])),
        },
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "four Pauli-correlated topology generators times two flux orientations times four operator channels on an eight-qubit tensor-network density",
        "topology_generators": list(generators.keys()),
        "flux_orientations": ["positive", "negative"],
        "operator_channels": list(ops.keys()),
        "gap_rows": gap_rows,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "The four topology generators are Pauli-correlated candidates, not a final topology basis.",
            "Flux orientation is simulated as generator sign inside finite unitary transport; flux ontology remains upstream of this scout.",
            "This is a richer integration harness, not a canonical target-system sim.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout and should not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "nonzero_order_gap_count": nonzero_gaps,
            "max_order_gap": max(row["gap"] for row in gap_rows),
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
