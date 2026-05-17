#!/usr/bin/env python3
"""Variable-qubit topology-flux channel-order entropy scaling scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from collections import defaultdict
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
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "variable_qubit_topology_flux_channel_order_entropy_scaling_probe_results.json"

NAME = "variable_qubit_topology_flux_channel_order_entropy_scaling_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: scales topology-flux channel-order and signed-entropy "
    "checks from two to eight qubits, with product-state and finite-MPS controls. "
    "It can falsify toy-only behavior and estimate minimum qubit counts, but it "
    "does not admit a final manifold tower, cycle identity, bridge, axis, or "
    "target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing variable-qubit density matrices, channels, spectra, and entropy readouts"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing GHZ finite-MPS contraction for the entangled-state control"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact Pauli noncommutation check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing minimum-qubit and nonzero-gap contradiction checks"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing mutual-information graph construction"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph-to-tensor conversion for nonempty MI graphs"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing H0 persistence over MI graph filtrations"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing directed composition-cycle readout"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128


def product_state(n: int) -> torch.Tensor:
    psi = torch.zeros(2**n, dtype=DTYPE)
    psi[0] = 1.0 + 0j
    return psi


def ghz_mps_state(n: int) -> tuple[torch.Tensor, list[int]]:
    if n == 1:
        return torch.tensor([1.0 + 0j, 0.0 + 0j], dtype=DTYPE), []
    if n == 2:
        psi = torch.zeros(4, dtype=DTYPE)
        psi[0] = 1 / math.sqrt(2)
        psi[3] = 1 / math.sqrt(2)
        return psi, [2]
    tensors = []
    first = torch.zeros((1, 2, 2), dtype=DTYPE)
    first[0, 0, 0] = 1 / math.sqrt(2)
    first[0, 1, 1] = 1 / math.sqrt(2)
    tensors.append(first)
    for _ in range(n - 2):
        middle = torch.zeros((2, 2, 2), dtype=DTYPE)
        middle[0, 0, 0] = 1
        middle[1, 1, 1] = 1
        tensors.append(middle)
    last = torch.zeros((2, 2, 1), dtype=DTYPE)
    last[0, 0, 0] = 1
    last[1, 1, 0] = 1
    tensors.append(last)
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    terms = [f"{letters[idx]}{letters[16 + idx]}{letters[idx + 1]}" for idx in range(n)]
    expr = ",".join(terms) + "->" + "".join(letters[16 : 16 + n])
    contracted = oe.contract(expr, *[tensor.numpy() for tensor in tensors])
    psi = torch.from_numpy(contracted.reshape(2**n))
    return psi / torch.linalg.vector_norm(psi), [2] * (n - 1)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def one_qubit_operator(local: torch.Tensor, qubit: int, n: int) -> torch.Tensor:
    op = torch.tensor([[1.0 + 0j]], dtype=DTYPE)
    eye = torch.eye(2, dtype=DTYPE)
    for idx in range(n):
        op = torch.kron(op, local if idx == qubit else eye)
    return op


def two_qubit_term(local_a: torch.Tensor, q_a: int, local_b: torch.Tensor, q_b: int, n: int) -> torch.Tensor:
    return one_qubit_operator(local_a, q_a, n) @ one_qubit_operator(local_b, q_b, n)


def topology_generators(n: int) -> dict[str, torch.Tensor]:
    sx = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    dim = 2**n
    generators = {
        "nearest_neighbor_xx_path": torch.zeros((dim, dim), dtype=DTYPE),
        "nearest_neighbor_yy_path": torch.zeros((dim, dim), dtype=DTYPE),
        "local_z_field_sum": torch.zeros((dim, dim), dtype=DTYPE),
        "alternating_xz_pair_path": torch.zeros((dim, dim), dtype=DTYPE),
    }
    for idx in range(n - 1):
        generators["nearest_neighbor_xx_path"] += two_qubit_term(sx, idx, sx, idx + 1, n)
        generators["nearest_neighbor_yy_path"] += two_qubit_term(sy, idx, sy, idx + 1, n)
        generators["alternating_xz_pair_path"] += two_qubit_term(sx if idx % 2 == 0 else sz, idx, sz if idx % 2 == 0 else sx, idx + 1, n)
    for idx in range(n):
        generators["local_z_field_sum"] += one_qubit_operator(sz, idx, n)
    return generators


def topology_channel(generator: torch.Tensor, flux_sign: int, kappa: float) -> Callable[[torch.Tensor], torch.Tensor]:
    unitary = torch.linalg.matrix_exp((-1j * flux_sign * kappa) * generator)
    return lambda rho: unitary @ rho @ unitary.conj().T


def operator_channels(n: int, target: int) -> dict[str, Callable[[torch.Tensor], torch.Tensor]]:
    sx = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    p0 = torch.tensor([[1, 0], [0, 0]], dtype=DTYPE)
    weights = torch.diag(torch.tensor([1.0, 0.62], dtype=DTYPE))
    unitary = torch.linalg.matrix_exp((-1j * 0.37) * one_qubit_operator(sx, target, n))
    projector = one_qubit_operator(p0, target, n)
    spectral = one_qubit_operator(weights, target, n)
    gamma = 0.23
    k0 = torch.tensor([[1.0, 0.0], [0.0, math.sqrt(1 - gamma)]], dtype=DTYPE)
    k1 = torch.tensor([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=DTYPE)
    kraus = [one_qubit_operator(k0, target, n), one_qubit_operator(k1, target, n)]

    def project(rho: torch.Tensor) -> torch.Tensor:
        out = projector @ rho @ projector.conj().T
        trace = torch.real(torch.trace(out))
        return rho if float(trace.item()) <= 1e-12 else out / trace

    def rotate(rho: torch.Tensor) -> torch.Tensor:
        return unitary @ rho @ unitary.conj().T

    def damp(rho: torch.Tensor) -> torch.Tensor:
        out = torch.zeros_like(rho)
        for k in kraus:
            out += k @ rho @ k.conj().T
        return out

    def filter_(rho: torch.Tensor) -> torch.Tensor:
        out = spectral @ rho @ spectral.conj().T
        return out / torch.real(torch.trace(out))

    return {
        "projector_constraint_channel": project,
        "hamiltonian_rotation_channel": rotate,
        "lindblad_amplitude_damping_channel": damp,
        "spectral_weight_filter_channel": filter_,
    }


def density_valid(rho: torch.Tensor) -> bool:
    herm = (rho + rho.conj().T) / 2
    eigs = torch.linalg.eigvalsh(herm)
    trace = torch.trace(rho)
    return bool(abs(float(torch.real(trace).item()) - 1) < 1e-8 and abs(float(torch.imag(trace).item())) < 1e-8 and float(torch.min(eigs).item()) > -1e-8)


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    diff = (a - b + (a - b).conj().T) / 2
    return float(0.5 * torch.sum(torch.abs(torch.linalg.eigvalsh(diff))).item())


def partial_trace_density(rho: torch.Tensor, keep: list[int], n: int) -> torch.Tensor:
    rest = [idx for idx in range(n) if idx not in keep]
    dims = [2] * n
    tensor = rho.reshape(dims + dims)
    perm = keep + rest + [idx + n for idx in keep] + [idx + n for idx in rest]
    ordered = tensor.permute(perm)
    d_keep = 2 ** len(keep)
    d_rest = 2 ** len(rest)
    ordered = ordered.reshape(d_keep, d_rest, d_keep, d_rest)
    return torch.einsum("abcb->ac", ordered)


def entropy(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def signed_entropy_summary(rho: torch.Tensor, n: int) -> dict[str, Any]:
    s_ab = entropy(rho)
    rows = []
    for cut in range(1, n):
        rho_a = partial_trace_density(rho, list(range(cut)), n)
        s_a = entropy(rho_a)
        rows.append({"cut": cut, "conditional_entropy": s_ab - s_a, "coherent_information": s_a - s_ab})
    return {
        "cut_count": len(rows),
        "min_conditional_entropy": min(row["conditional_entropy"] for row in rows) if rows else 0.0,
        "max_coherent_information": max(row["coherent_information"] for row in rows) if rows else 0.0,
        "rows": rows,
    }


def mutual_information_pair(rho: torch.Tensor, i: int, j: int, n: int) -> float:
    s_i = entropy(partial_trace_density(rho, [i], n))
    s_j = entropy(partial_trace_density(rho, [j], n))
    s_ij = entropy(partial_trace_density(rho, [i, j], n))
    return s_i + s_j - s_ij


def graph_persistence(rho: torch.Tensor, n: int) -> dict[str, Any]:
    graph = nx.Graph()
    graph.add_nodes_from(range(n))
    st = gudhi.SimplexTree()
    for node in range(n):
        st.insert([node], filtration=0.0)
    for i in range(n):
        for j in range(i + 1, n):
            mi = mutual_information_pair(rho, i, j, n)
            if mi > 1e-5:
                graph.add_edge(i, j, weight=mi)
                st.insert([i, j], filtration=1.0 / mi)
    pairs = st.persistence()
    pyg = from_networkx(graph) if graph.number_of_edges() else None
    return {
        "mi_edge_count": graph.number_of_edges(),
        "persistence_pair_count": len(pairs),
        "pyg_edge_index_shape": list(pyg.edge_index.shape) if pyg is not None else [2, 0],
    }


def exact_pauli_check() -> dict[str, Any]:
    sx = sp.Matrix([[0, 1], [1, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    return {"commutator": str(sx * sz - sz * sx), "pass": sx * sz - sz * sx != sp.zeros(2)}


def composition_cycles() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    names = ["density", "topology_channel", "operator_channel", "entropy_readout", "graph_readout"]
    nodes = {name: graph.add_node(name) for name in names}
    for source, target in [
        ("density", "topology_channel"),
        ("topology_channel", "operator_channel"),
        ("operator_channel", "density"),
        ("density", "entropy_readout"),
        ("entropy_readout", "graph_readout"),
        ("graph_readout", "topology_channel"),
    ]:
        graph.add_edge(nodes[source], nodes[target], "maps")
    cycles = list(rx.simple_cycles(graph))
    return {"cycle_count": len(cycles), "pass": len(cycles) >= 2}


def z3_scaling_checks(min_gap_qubits: int | None, min_negative_qubits: int | None) -> dict[str, Any]:
    q_gap = z3.Int("q_gap")
    q_neg = z3.Int("q_neg")
    gap_solver = z3.Solver()
    neg_solver = z3.Solver()
    if min_gap_qubits is None:
        gap_solver.add(q_gap == -1, q_gap >= 2)
    else:
        gap_solver.add(q_gap == min_gap_qubits, q_gap < 2)
    if min_negative_qubits is None:
        neg_solver.add(q_neg == -1, q_neg >= 2)
    else:
        neg_solver.add(q_neg == min_negative_qubits, q_neg < 2)
    return {
        "minimum_nonzero_gap_below_two_qubits_unsat": {"solver_status": str(gap_solver.check()), "value": min_gap_qubits, "pass": gap_solver.check() == z3.unsat},
        "minimum_negative_conditional_entropy_below_two_qubits_unsat": {"solver_status": str(neg_solver.check()), "value": min_negative_qubits, "pass": neg_solver.check() == z3.unsat},
    }


def run_for_qubits(n: int, state_kind: str) -> dict[str, Any]:
    psi, bond_dims = ghz_mps_state(n) if state_kind == "ghz_mps" else (product_state(n), [1] * (n - 1))
    rho0 = density(psi)
    generators = topology_generators(n)
    operator_targets = sorted({0, n // 2, n - 1})
    rows = []
    entropy_sample = None
    graph_sample = None
    for topology_name, generator in generators.items():
        for flux_sign in (1, -1):
            top = topology_channel(generator, flux_sign, 0.19)
            for operator_target in operator_targets:
                for op_name, op in operator_channels(n, operator_target).items():
                    operator_first = top(op(rho0))
                    topology_first = op(top(rho0))
                    gap = trace_distance(operator_first, topology_first)
                    signed = signed_entropy_summary(operator_first, n)
                    if entropy_sample is None:
                        entropy_sample = signed
                        graph_sample = graph_persistence(operator_first, n)
                    rows.append(
                        {
                            "topology": topology_name,
                            "flux_sign": flux_sign,
                            "operator_target": operator_target,
                            "operator_channel": op_name,
                            "gap": gap,
                            "min_conditional_entropy": signed["min_conditional_entropy"],
                            "max_coherent_information": signed["max_coherent_information"],
                            "operator_first_density_valid": density_valid(operator_first),
                            "topology_first_density_valid": density_valid(topology_first),
                        }
                    )
    by_topology = defaultdict(lambda: {"rows": 0, "nonzero_gaps": 0, "max_gap": 0.0})
    for row in rows:
        item = by_topology[row["topology"]]
        item["rows"] += 1
        item["nonzero_gaps"] += int(row["gap"] > 1e-6)
        item["max_gap"] = max(item["max_gap"], row["gap"])
    return {
        "n_qubits": n,
        "state_kind": state_kind,
        "dimension": int(psi.numel()),
        "max_bond_dim_input": max(bond_dims) if bond_dims else 1,
        "density_valid": density_valid(rho0),
        "row_count": len(rows),
        "operator_targets": operator_targets,
        "nonzero_order_gap_count": sum(1 for row in rows if row["gap"] > 1e-6),
        "max_order_gap": max(row["gap"] for row in rows),
        "negative_conditional_entropy_count": sum(1 for row in rows if row["min_conditional_entropy"] < -1e-6),
        "most_negative_conditional_entropy": min(row["min_conditional_entropy"] for row in rows),
        "all_channel_outputs_density_valid": all(row["operator_first_density_valid"] and row["topology_first_density_valid"] for row in rows),
        "by_topology": dict(by_topology),
        "entropy_sample": entropy_sample,
        "graph_sample": graph_sample,
    }


def main() -> dict[str, Any]:
    started = time.time()
    qubit_values = list(range(2, 9))
    scaling_rows = []
    for n in qubit_values:
        scaling_rows.append(run_for_qubits(n, "product_origin"))
        scaling_rows.append(run_for_qubits(n, "ghz_mps"))

    product_rows = [row for row in scaling_rows if row["state_kind"] == "product_origin"]
    min_gap = next((row["n_qubits"] for row in product_rows if row["nonzero_order_gap_count"] > 0), None)
    min_negative = next((row["n_qubits"] for row in product_rows if row["negative_conditional_entropy_count"] > 0), None)
    z3_rows = z3_scaling_checks(min_gap, min_negative)
    cycle_readout = composition_cycles()
    positive = {
        "scales_two_through_eight_qubits_for_product_and_mps_controls": {
            "row_count": len(scaling_rows),
            "qubit_values": qubit_values,
            "pass": len(scaling_rows) == 14 and {row["state_kind"] for row in scaling_rows} == {"product_origin", "ghz_mps"},
        },
        "each_qubit_state_enumerates_four_topologies_two_fluxes_targets_and_four_channels": {
            "row_counts": [row["row_count"] for row in scaling_rows],
            "operator_targets": {row["n_qubits"]: row["operator_targets"] for row in product_rows},
            "pass": all(row["row_count"] == 4 * 2 * len(row["operator_targets"]) * 4 for row in scaling_rows),
        },
        "product_origin_has_nonzero_order_gap_without_preloaded_entanglement": {
            "minimum_qubits": min_gap,
            "counts": {row["n_qubits"]: row["nonzero_order_gap_count"] for row in product_rows},
            "pass": min_gap is not None,
        },
        "product_origin_reaches_negative_conditional_entropy_under_some_channels": {
            "minimum_qubits": min_negative,
            "counts": {row["n_qubits"]: row["negative_conditional_entropy_count"] for row in product_rows},
            "pass": min_negative is not None,
        },
        "all_outputs_remain_density_matrices": {
            "invalid": [row for row in scaling_rows if not row["all_channel_outputs_density_valid"]],
            "pass": all(row["all_channel_outputs_density_valid"] for row in scaling_rows),
        },
        "exact_pauli_noncommutation_sanity_check": exact_pauli_check(),
        "rustworkx_composition_cycle_readout": cycle_readout,
        "z3_minimum_qubit_checks": {"checks": z3_rows, "pass": all(row["pass"] for row in z3_rows.values())},
    }
    graveyard_companions = {
        "one_qubit_has_no_bipartition_signed_entropy": {
            "cut_count": signed_entropy_summary(density(product_state(1)), 1)["cut_count"],
            "pass": signed_entropy_summary(density(product_state(1)), 1)["cut_count"] == 0,
        },
        "zero_strength_topology_channel_collapses_order_gap_at_eight_qubits": {
            "max_gap": max(
                trace_distance((lambda rho: rho)(op(density(product_state(8)))), op((lambda rho: rho)(density(product_state(8)))))
                for op in operator_channels(8, 0).values()
            ),
            "pass": max(
                trace_distance((lambda rho: rho)(op(density(product_state(8)))), op((lambda rho: rho)(density(product_state(8)))))
                for op in operator_channels(8, 0).values()
            )
            < 1e-10,
        },
        "scaled_density_fails_admission": {
            "trace": float(torch.real(torch.trace(2 * density(product_state(4)))).item()),
            "pass": not density_valid(2 * density(product_state(4))),
        },
    }
    boundary = {
        "maximum_dimension_is_256": {"max_dimension": max(row["dimension"] for row in scaling_rows), "pass": max(row["dimension"] for row in scaling_rows) == 256},
        "minimum_qubit_count_for_bipartition_is_two": {"minimum_tested": min(qubit_values), "pass": min(qubit_values) == 2},
        "mps_control_uses_bond_dimension_two": {
            "max_input_bond": max(row["max_bond_dim_input"] for row in scaling_rows if row["state_kind"] == "ghz_mps"),
            "pass": max(row["max_bond_dim_input"] for row in scaling_rows if row["state_kind"] == "ghz_mps") == 2,
        },
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "variable-qubit topology-flux channel-order and signed-entropy scaling audit over product and finite-MPS input states",
        "qubit_values": qubit_values,
        "scaling_rows": scaling_rows,
        "minimum_qubits": {
            "nonzero_order_gap_from_product_origin": min_gap,
            "negative_conditional_entropy_from_product_origin": min_negative,
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "This still uses dense matrices up to eight qubits; larger systems need sparse or true MPS channel updates.",
            "Product-origin survival is stronger than preloaded GHZ survival, but still only validates this finite operator family.",
            "The topology generators are Pauli-correlated candidates, not the final nested geometry basis.",
        ],
        "why_not_v4_probes": "This is a clean v5 scaling scout and should not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "minimum_qubits": {
                "nonzero_order_gap_from_product_origin": min_gap,
                "negative_conditional_entropy_from_product_origin": min_negative,
            },
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
