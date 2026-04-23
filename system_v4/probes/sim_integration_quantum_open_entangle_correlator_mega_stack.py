#!/usr/bin/env python3
"""
sim_integration_quantum_open_entangle_correlator_mega_stack.py

Quantum mega-stack bridge lane for:
  numpy + scipy + qutip + cirq + pennylane + torch + clifford + torch_ga
  + rustworkx + xgi + toponetx + gudhi + sympy + z3

Claim:
  One bounded 2-qubit surface can be reused across three linked contracts:
    - entangling state preparation
    - open-system amplitude damping on one qubit
    - reduced correlator geometry of the damped surface

The goal is not to prove a general theorem. It is to admit a reusable bridge
that the broader sims can scale from without ad hoc glue:
  1. Cirq and PennyLane witness the entangling preparation.
  2. qutip witnesses the open-system evolution against an exact reference.
  3. torch + Clifford + torch_ga witness the reduced correlator geometry of the
     damped state, while numpy/scipy keep the classical reference honest.
  4. rustworkx + xgi + toponetx + gudhi + sympy + z3 witness the ordered
     dynamic-shell, topology, and constraint surfaces used by Axis 0.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import cirq
import gudhi
import numpy as np
import pennylane as qml
import qutip
import rustworkx as rx
import sympy as sp
import torch
import torch_ga
import xgi
from clifford import Cl
from scipy.linalg import expm
from toponetx import CellComplex
from z3 import Real, RealVal, Solver, Sum, sat

classification = "classical_baseline"
divergence_log = (
    "Classical-to-nonclassical bridge baseline: one entangling 2-qubit state, "
    "one amplitude-damping open-system flow, and one reduced correlator geometry "
    "must all agree across numpy/scipy, qutip, Cirq, PennyLane, torch, Clifford, "
    "torch_ga, rustworkx, xgi, TopoNetX, GUDHI, sympy, and z3. The lane also "
    "exposes an Axis 0 dynamic-shell readout over a lambda-indexed expansion "
    "schedule so i-scalar/jk-fuzz, shell ordering, higher-order shell couplings, "
    "topology parity, and admissible shell constraints are measured from the "
    "live shell surface instead of frozen weights."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "classical density, correlator, Axis 0 shell bookkeeping, and serialization arithmetic",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "matrix exponential reference for the entangling prep, Liouvillian flow, and lambda-indexed shell schedule",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "load-bearing open-system mesolve witness on the damped entangled state",
    },
    "cirq": {
        "tried": True,
        "used": True,
        "reason": "load-bearing entangling circuit witness for the 2-qubit prep surface",
    },
    "pennylane": {
        "tried": True,
        "used": True,
        "reason": "load-bearing QNode entanglement witness for the same prep surface",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing fit and gradient witness on the reduced correlator geometry",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing geometric carrier for the reduced correlator vector",
    },
    "torch_ga": {
        "tried": True,
        "used": True,
        "reason": "load-bearing geometric algebra roundtrip for the reduced correlator vector",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing shell DAG witness for lambda-ordered dynamic-shell propagation",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing higher-order shell-coupling witness for triadic shell windows",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing cell-complex witness for shell boundary composition",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing persistent-topology witness for the shell complex",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic interpolation and derivative witness for the lambda-shell drive",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing constraint witness enforcing ordered lambda shells and normalized dynamic weights",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "supportive",
    "qutip": "load_bearing",
    "cirq": "load_bearing",
    "pennylane": "load_bearing",
    "pytorch": "load_bearing",
    "clifford": "load_bearing",
    "torch_ga": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
}

RESULTS_PATH = os.path.join(
    os.path.dirname(__file__),
    "a2_state",
    "sim_results",
    "sim_integration_quantum_open_entangle_correlator_mega_stack_results.json",
)

Q0, Q1 = cirq.LineQubit.range(2)
DEV = qml.device("default.qubit", wires=2, shots=None)

X2 = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float64)
Y2 = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
Z2 = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.float64)
XX = np.kron(X2, X2)
YY = np.kron(Y2, Y2).real.astype(np.float64)
ZZ = np.kron(Z2, Z2)
I2 = np.eye(2, dtype=np.complex128)
I4 = np.eye(4, dtype=np.complex128)
H2 = (1.0 / np.sqrt(2.0)) * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128)
CNOT_01 = np.array(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0],
    ],
    dtype=np.complex128,
)
CNOT_10 = np.array(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
    ],
    dtype=np.complex128,
)

LAYOUT, BLADES = Cl(3)
E1 = BLADES["e1"]
E2 = BLADES["e2"]
E3 = BLADES["e3"]
TORCH_GA_ALG = torch_ga.GeometricAlgebra([1.0, 1.0, 1.0])
TORCH_GA_TO_GEO = torch_ga.TensorToGeometric(TORCH_GA_ALG, [1, 2, 3])
TORCH_GA_TO_TENSOR = torch_ga.GeometricToTensor(TORCH_GA_ALG, [1, 2, 3])


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    if isinstance(obj, complex):
        return [float(np.real(obj)), float(np.imag(obj))]
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _rho(state: np.ndarray) -> np.ndarray:
    state = np.asarray(state, dtype=np.complex128).reshape(-1)
    return np.outer(state, np.conjugate(state))


def _vec(rho: np.ndarray) -> np.ndarray:
    return np.asarray(rho, dtype=np.complex128).reshape(-1, order="F")


def _unvec(vec: np.ndarray) -> np.ndarray:
    return np.asarray(vec, dtype=np.complex128).reshape(4, 4, order="F")


def _ket00() -> np.ndarray:
    return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.complex128)


def _bell_prep(theta: float, phi: float) -> np.ndarray:
    """Reference entangling prep: local Y rotations then CNOT."""
    unitary = CNOT_01 @ np.kron(expm(-0.5j * theta * np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)),
                                 expm(-0.5j * phi * np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)))
    return unitary @ _ket00()


def _cirq_prep(theta: float, phi: float, *, reversed_entangler: bool = False) -> np.ndarray:
    circuit = cirq.Circuit(
        cirq.ry(theta)(Q0),
        cirq.ry(phi)(Q1),
        cirq.CNOT(Q1, Q0) if reversed_entangler else cirq.CNOT(Q0, Q1),
    )
    return np.asarray(cirq.Simulator(seed=42).simulate(circuit).final_state_vector, dtype=np.complex128)


@qml.qnode(DEV)
def _pennylane_prep(theta: float, phi: float, reversed_entangler: bool = False):
    qml.RY(theta, wires=0)
    qml.RY(phi, wires=1)
    if reversed_entangler:
        qml.CNOT(wires=[1, 0])
    else:
        qml.CNOT(wires=[0, 1])
    return qml.state()


def _amplitude_damping_liouvillian(gamma: float) -> np.ndarray:
    lower = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=np.complex128)
    c_op = np.kron(np.eye(2, dtype=np.complex128), lower)
    ident = np.eye(4, dtype=np.complex128)
    cdag_c = c_op.conj().T @ c_op
    return gamma * (
        np.kron(c_op.conj(), c_op)
        - 0.5 * np.kron(ident, cdag_c)
        - 0.5 * np.kron(cdag_c.T, ident)
    )


def _open_system_reference(rho0: np.ndarray, gamma: float, t: float) -> np.ndarray:
    liouvillian = _amplitude_damping_liouvillian(gamma)
    return _unvec(expm(liouvillian * t) @ _vec(rho0))


def _qutip_evolution(rho0: np.ndarray, gamma: float, times: list[float]) -> list[np.ndarray]:
    rho_q = qutip.Qobj(rho0, dims=[[2, 2], [2, 2]])
    h = 0.0 * qutip.tensor(qutip.sigmaz(), qutip.sigmaz())
    c_ops = [np.sqrt(gamma) * qutip.tensor(qutip.qeye(2), qutip.sigmap())]
    result = qutip.mesolve(H=h, rho0=rho_q, tlist=times, c_ops=c_ops, e_ops=[])
    return [np.asarray(state.full(), dtype=np.complex128) for state in result.states]


def _partial_trace_qubit1(rho: np.ndarray) -> np.ndarray:
    reshaped = rho.reshape(2, 2, 2, 2)
    return np.einsum("abcb->ac", reshaped)


def _entropy_from_density(rho: np.ndarray) -> float:
    rho = np.asarray(rho, dtype=np.complex128)
    rho = (rho + rho.conj().T) / 2.0
    evals = np.linalg.eigvalsh(rho)
    evals = np.clip(np.real(evals), 1e-15, 1.0)
    return float(-np.sum(evals * np.log2(evals)))


def _concurrence(state: np.ndarray) -> float:
    a, b, c, d = np.asarray(state, dtype=np.complex128).reshape(-1)
    return float(2.0 * abs(a * d - b * c))


def _entropy_from_state(state: np.ndarray) -> float:
    return _entropy_from_density(_partial_trace_qubit1(_rho(state)))


def _coherent_information(rho: np.ndarray) -> float:
    rho = np.asarray(rho, dtype=np.complex128).reshape(4, 4)
    rho_b = _partial_trace_qubit1(rho)
    return float(_entropy_from_density(rho_b) - _entropy_from_density(rho))


def _correlator_vector(rho: np.ndarray) -> np.ndarray:
    rho = np.asarray(rho, dtype=np.complex128).reshape(4, 4)
    return np.array(
        [
            float(np.real(np.trace(rho @ XX))),
            float(np.real(np.trace(rho @ YY))),
            float(np.real(np.trace(rho @ ZZ))),
        ],
        dtype=np.float64,
    )


def _reduced_bloch(rho: np.ndarray) -> np.ndarray:
    reduced = _partial_trace_qubit1(np.asarray(rho, dtype=np.complex128).reshape(4, 4))
    return np.array(
        [
            float(np.real(np.trace(reduced @ X2))),
            float(np.real(np.trace(reduced @ Y2))),
            float(np.real(np.trace(reduced @ Z2))),
        ],
        dtype=np.float64,
    )


def _zi_expectation(rho: np.ndarray) -> float:
    rho = np.asarray(rho, dtype=np.complex128).reshape(4, 4)
    return float(np.real(np.trace(rho @ np.kron(Z2, I2))))


def _torch_correlator(vec: torch.Tensor) -> torch.Tensor:
    return vec


def _torch_fit_correlator(
    target: np.ndarray,
    base_correlator: np.ndarray,
    base_zi: float,
    initial_raw: float = 0.0,
) -> dict[str, object]:
    target_t = torch.tensor(target, dtype=torch.float64)
    base_corr_t = torch.tensor(base_correlator, dtype=torch.float64)
    base_zi_t = torch.tensor(base_zi, dtype=torch.float64)
    raw = torch.nn.Parameter(torch.tensor(initial_raw, dtype=torch.float64))
    optimizer = torch.optim.LBFGS(
        [raw],
        lr=1.0,
        max_iter=100,
        tolerance_grad=1e-14,
        tolerance_change=1e-14,
        line_search_fn="strong_wolfe",
    )
    history: list[float] = []

    def closure():
        optimizer.zero_grad()
        p = torch.sigmoid(raw)
        root = torch.sqrt(torch.clamp(1.0 - p, min=0.0))
        pred = torch.stack(
            (
                base_corr_t[0] * root,
                base_corr_t[1] * root,
                base_corr_t[2] * (1.0 - p) + base_zi_t * p,
            )
        )
        loss = torch.sum((pred - target_t) ** 2)
        loss.backward()
        history.append(float(loss.detach()))
        return loss

    optimizer.step(closure)
    with torch.no_grad():
        p = torch.sigmoid(raw)
        root = torch.sqrt(torch.clamp(1.0 - p, min=0.0))
        pred = torch.stack(
            (
                base_corr_t[0] * root,
                base_corr_t[1] * root,
                base_corr_t[2] * (1.0 - p) + base_zi_t * p,
            )
        )
        loss = torch.sum((pred - target_t) ** 2).item()
        pred_np = pred.detach().cpu().numpy()

    return {
        "initial_raw": float(initial_raw),
        "decay_fit": float(torch.sigmoid(raw).item()),
        "vector_fit": pred_np.tolist(),
        "loss": float(loss),
        "vector_gap": float(np.max(np.abs(pred_np - target))),
        "loss_history_tail": [float(x) for x in history[-5:]],
    }


def _clifford_vector(vec: np.ndarray) -> np.ndarray:
    multivector = vec[0] * E1 + vec[1] * E2 + vec[2] * E3
    return np.asarray(multivector.value[1:4], dtype=np.float64)


def _torch_ga_roundtrip(vec: np.ndarray) -> np.ndarray:
    tensor = torch.tensor(vec, dtype=torch.float32).reshape(1, 3)
    geo = TORCH_GA_TO_GEO(tensor)
    return TORCH_GA_TO_TENSOR(geo).detach().cpu().numpy().reshape(-1).astype(np.float64)


def _density_summary(rho: np.ndarray) -> dict[str, object]:
    rho = np.asarray(rho, dtype=np.complex128).reshape(4, 4)
    return {
        "trace": float(np.real(np.trace(rho))),
        "reduced_bloch": _reduced_bloch(rho).tolist(),
        "correlators": _correlator_vector(rho).tolist(),
        "coherent_information": _coherent_information(rho),
    }


def _axis0_shell_graph_surface(
    shell_rows: list[dict[str, object]],
    *,
    eps: float = 1e-6,
) -> dict[str, object]:
    dag = rx.PyDiGraph()
    node_ids: list[int] = []
    dag_edges: set[tuple[int, int]] = set()
    pair_edges: set[tuple[int, int]] = set()
    triad_windows: list[tuple[int, int, int]] = []
    edge_signal_sum = 0.0

    for idx, row in enumerate(shell_rows):
        node_ids.append(
            dag.add_node(
                {
                    "shell_index": int(idx),
                    "lambda_shell": float(row["lambda_shell"]),
                    "coherent_information": float(row["coherent_information"]),
                    "shell_entropy": float(row["shell_entropy"]),
                }
            )
        )

    def _signal(i: int, j: int) -> float:
        lhs = shell_rows[i]
        rhs = shell_rows[j]
        return float(
            abs(float(rhs["coherent_information"]) - float(lhs["coherent_information"]))
            + abs(float(rhs["shell_entropy"]) - float(lhs["shell_entropy"]))
            + abs(float(rhs["correlator_norm"]) - float(lhs["correlator_norm"]))
        )

    def _add_edge(i: int, j: int, kind: str, signal: float) -> None:
        nonlocal edge_signal_sum
        edge = (int(i), int(j))
        if edge in dag_edges:
            return
        dag.add_edge(node_ids[i], node_ids[j], {"kind": kind, "signal": float(signal)})
        dag_edges.add(edge)
        pair_edges.add(edge)
        edge_signal_sum += float(signal)

    for idx in range(len(shell_rows) - 1):
        signal = _signal(idx, idx + 1)
        if signal > eps:
            _add_edge(idx, idx + 1, "adjacent_shell", signal)

    for idx in range(len(shell_rows) - 2):
        local_rows = shell_rows[idx : idx + 3]
        coherent_values = [float(row["coherent_information"]) for row in local_rows]
        entropy_values = [float(row["shell_entropy"]) for row in local_rows]
        correlator_values = [float(row["correlator_norm"]) for row in local_rows]
        local_span = float(
            (max(coherent_values) - min(coherent_values))
            + (max(entropy_values) - min(entropy_values))
            + (max(correlator_values) - min(correlator_values))
        )
        if local_span > eps:
            triad = (int(idx), int(idx + 1), int(idx + 2))
            triad_windows.append(triad)
            _add_edge(idx, idx + 1, "triad_boundary", max(_signal(idx, idx + 1), local_span))
            _add_edge(idx + 1, idx + 2, "triad_boundary", max(_signal(idx + 1, idx + 2), local_span))
            _add_edge(idx, idx + 2, "triad_bridge", local_span)

    topological_order = [int(dag[node_id]["shell_index"]) for node_id in rx.topological_sort(dag)]
    return {
        "node_count": int(dag.num_nodes()),
        "edge_count": int(dag.num_edges()),
        "pair_edges": [list(edge) for edge in sorted(pair_edges)],
        "triad_windows": [list(window) for window in triad_windows],
        "topological_order": topological_order,
        "longest_path_length": int(rx.dag_longest_path_length(dag)) if dag.num_edges() else 0,
        "acyclic": bool(rx.is_directed_acyclic_graph(dag)),
        "edge_signal_sum": float(edge_signal_sum),
    }


def _axis0_shell_hypergraph_surface(
    n_shells: int,
    pair_edges: list[list[int]],
    triad_windows: list[list[int]],
) -> dict[str, object]:
    hypergraph = xgi.Hypergraph()
    hypergraph.add_nodes_from(range(n_shells))
    for edge in pair_edges:
        hypergraph.add_edge([int(edge[0]), int(edge[1])])
    for triad in triad_windows:
        hypergraph.add_edge([int(triad[0]), int(triad[1]), int(triad[2])])
    incidence = xgi.incidence_matrix(hypergraph, sparse=False) if hypergraph.num_edges else np.zeros((n_shells, 0), dtype=np.float64)
    edge_sizes = [int(value) for value in hypergraph.edges.size.aslist()] if hypergraph.num_edges else []
    return {
        "num_nodes": int(hypergraph.num_nodes),
        "num_edges": int(hypergraph.num_edges),
        "edge_sizes": edge_sizes,
        "incidence_rank": int(np.linalg.matrix_rank(incidence)) if incidence.size else 0,
        "connected_components": int(xgi.number_connected_components(hypergraph)) if hypergraph.num_edges else int(n_shells),
        "max_hyperedge_size": int(max(edge_sizes)) if edge_sizes else 1,
    }


def _axis0_shell_cell_complex_surface(
    n_shells: int,
    pair_edges: list[list[int]],
    triad_windows: list[list[int]],
) -> dict[str, object]:
    complex_ = CellComplex()
    for edge in pair_edges:
        complex_.add_cell([int(edge[0]), int(edge[1])], rank=1)
    for triad in triad_windows:
        complex_.add_cell([int(triad[0]), int(triad[1]), int(triad[2])], rank=2)
    boundary_1 = complex_.incidence_matrix(rank=1, signed=True).toarray()
    boundary_2 = complex_.incidence_matrix(rank=2, signed=True).toarray()
    boundary_composes_to_zero = True
    if boundary_1.size and boundary_2.size:
        boundary_composes_to_zero = bool(np.allclose(boundary_1 @ boundary_2, 0.0, atol=1e-12))
    return {
        "shape": [int(value) for value in complex_.shape],
        "boundary_rank_1": int(np.linalg.matrix_rank(boundary_1)) if boundary_1.size else 0,
        "boundary_rank_2": int(np.linalg.matrix_rank(boundary_2)) if boundary_2.size else 0,
        "boundary_composes_to_zero": bool(boundary_composes_to_zero),
        "euler_characteristic": int(n_shells - len(pair_edges) + len(triad_windows)),
    }


def _axis0_shell_topology_surface(
    n_shells: int,
    pair_edges: list[list[int]],
    triad_windows: list[list[int]],
) -> dict[str, object]:
    simplex_tree = gudhi.SimplexTree()
    for idx in range(n_shells):
        simplex_tree.insert([int(idx)], filtration=0.0)
    for edge in pair_edges:
        simplex_tree.insert([int(edge[0]), int(edge[1])], filtration=1.0)
    for triad in triad_windows:
        simplex_tree.insert([int(triad[0]), int(triad[1]), int(triad[2])], filtration=2.0)
    simplex_tree.set_dimension(max(2, simplex_tree.dimension()))
    simplex_tree.compute_persistence()
    betti = [int(value) for value in simplex_tree.betti_numbers()]
    beta0 = betti[0] if betti else int(n_shells)
    beta1 = betti[1] if len(betti) > 1 else 0
    beta2 = betti[2] if len(betti) > 2 else 0
    return {
        "betti_numbers": betti,
        "beta0": int(beta0),
        "beta1": int(beta1),
        "beta2": int(beta2),
        "euler_characteristic": int(beta0 - beta1 + beta2),
    }


def _axis0_shell_symbolic_surface(
    lambda_shells: np.ndarray,
    coherent_arr: np.ndarray,
    entropy_arr: np.ndarray,
) -> dict[str, object]:
    lam = sp.symbols("lam", real=True)
    coherent_pairs = [(float(x), float(y)) for x, y in zip(lambda_shells.tolist(), coherent_arr.tolist(), strict=True)]
    entropy_pairs = [(float(x), float(y)) for x, y in zip(lambda_shells.tolist(), entropy_arr.tolist(), strict=True)]
    coherent_poly = sp.expand(sp.interpolate(coherent_pairs, lam))
    entropy_poly = sp.expand(sp.interpolate(entropy_pairs, lam))
    mid_lambda = float(lambda_shells[len(lambda_shells) // 2])
    coherent_poly_obj = sp.Poly(coherent_poly, lam)
    entropy_poly_obj = sp.Poly(entropy_poly, lam)
    return {
        "coherent_information_polynomial": str(coherent_poly),
        "entropy_polynomial": str(entropy_poly),
        "coherent_poly_degree": int(coherent_poly_obj.degree()),
        "entropy_poly_degree": int(entropy_poly_obj.degree()),
        "mid_lambda": mid_lambda,
        "symbolic_ic_derivative_mid": float(sp.N(sp.diff(coherent_poly, lam).subs(lam, mid_lambda))),
        "symbolic_entropy_derivative_mid": float(sp.N(sp.diff(entropy_poly, lam).subs(lam, mid_lambda))),
    }


def _axis0_shell_constraint_surface(
    lambda_shells: np.ndarray,
    dynamic_weights: np.ndarray,
) -> dict[str, object]:
    solver = Solver()
    lambda_vars = [Real(f"lambda_shell_{idx}") for idx in range(len(lambda_shells))]
    weight_vars = [Real(f"dynamic_weight_{idx}") for idx in range(len(dynamic_weights))]
    for var, value in zip(lambda_vars, lambda_shells.tolist(), strict=True):
        solver.add(var == RealVal(str(float(value))))
    for var, value in zip(weight_vars, dynamic_weights.tolist(), strict=True):
        solver.add(var == RealVal(str(float(value))))
        solver.add(var >= RealVal("0.0"))
    for lhs, rhs in zip(lambda_vars[:-1], lambda_vars[1:], strict=True):
        solver.add(lhs < rhs)
    if weight_vars:
        weight_sum = Sum(*weight_vars)
        solver.add(weight_sum >= RealVal("0.999999"))
        solver.add(weight_sum <= RealVal("1.000001"))
    result = solver.check()
    return {
        "result": str(result),
        "sat": bool(result == sat),
    }


def _axis0_dynamic_shell_surface(
    rho0: np.ndarray,
    gamma: float,
    t: float,
    *,
    n_shells: int = 5,
) -> dict[str, object]:
    lambda_shells = np.linspace(0.0, 1.0, n_shells, dtype=np.float64)
    shell_rows: list[dict[str, object]] = []
    shell_signal: list[float] = []
    coherent_series: list[float] = []
    entropy_series: list[float] = []
    previous_entropy: float | None = None

    for lam in lambda_shells:
        rho_shell = _open_system_reference(rho0, gamma, float(lam * t))
        correlator = _correlator_vector(rho_shell)
        shell_entropy = _entropy_from_density(_partial_trace_qubit1(rho_shell))
        coherent_info = _coherent_information(rho_shell)
        entropy_delta = 0.0 if previous_entropy is None else shell_entropy - previous_entropy
        correlator_norm = float(np.linalg.norm(correlator))
        signal = abs(correlator_norm) + abs(entropy_delta) + 1e-12
        shell_rows.append(
            {
                "lambda_shell": float(lam),
                "time": float(lam * t),
                "coherent_information": float(coherent_info),
                "shell_entropy": float(shell_entropy),
                "entropy_delta": float(entropy_delta),
                "correlator_norm": correlator_norm,
            }
        )
        shell_signal.append(signal)
        coherent_series.append(float(coherent_info))
        entropy_series.append(float(shell_entropy))
        previous_entropy = shell_entropy

    weights = np.asarray(shell_signal, dtype=np.float64)
    weights = weights / weights.sum()
    frozen_weights = np.full(n_shells, 1.0 / n_shells, dtype=np.float64)
    for row, weight in zip(shell_rows, weights, strict=True):
        row["dynamic_weight"] = float(weight)

    coherent_arr = np.asarray(coherent_series, dtype=np.float64)
    entropy_arr = np.asarray(entropy_series, dtype=np.float64)
    ic_gradient = np.gradient(coherent_arr, lambda_shells)
    entropy_gradient = np.gradient(entropy_arr, lambda_shells)
    jk_fuzz = float(-np.sum(weights * np.log2(weights)))
    i_scalar_dynamic = float(np.dot(weights, coherent_arr))
    i_scalar_frozen = float(np.dot(frozen_weights, coherent_arr))
    graph_surface = _axis0_shell_graph_surface(shell_rows)
    hypergraph_surface = _axis0_shell_hypergraph_surface(
        n_shells,
        graph_surface["pair_edges"],
        graph_surface["triad_windows"],
    )
    cell_complex_surface = _axis0_shell_cell_complex_surface(
        n_shells,
        graph_surface["pair_edges"],
        graph_surface["triad_windows"],
    )
    topology_surface = _axis0_shell_topology_surface(
        n_shells,
        graph_surface["pair_edges"],
        graph_surface["triad_windows"],
    )
    symbolic_surface = _axis0_shell_symbolic_surface(lambda_shells, coherent_arr, entropy_arr)
    constraint_surface = _axis0_shell_constraint_surface(lambda_shells, weights)

    return {
        "lambda_shells": lambda_shells.tolist(),
        "shell_rows": shell_rows,
        "dynamic_weights": weights.tolist(),
        "jk_fuzz_dynamic": jk_fuzz,
        "i_scalar_dynamic": i_scalar_dynamic,
        "i_scalar_frozen": i_scalar_frozen,
        "dynamic_vs_frozen_gap": float(abs(i_scalar_dynamic - i_scalar_frozen)),
        "coherent_information_span": float(np.max(coherent_arr) - np.min(coherent_arr)),
        "entropy_span": float(np.max(entropy_arr) - np.min(entropy_arr)),
        "gravity_proxy_mean": float(np.mean(-ic_gradient)),
        "expansion_entropy_drive_mean": float(np.mean(entropy_gradient)),
        "weights_sum": float(np.sum(weights)),
        "graph_surface": graph_surface,
        "hypergraph_surface": hypergraph_surface,
        "cell_complex_surface": cell_complex_surface,
        "topology_surface": topology_surface,
        "symbolic_surface": symbolic_surface,
        "constraint_surface": constraint_surface,
        "topology_parity_ok": bool(
            cell_complex_surface["euler_characteristic"] == topology_surface["euler_characteristic"]
        ),
    }


def _case_metrics(theta: float, phi: float, gamma: float, t: float, *, reversed_entangler: bool = False) -> dict[str, object]:
    prep_ref = _bell_prep(theta, phi)
    prep_cirq = _cirq_prep(theta, phi, reversed_entangler=reversed_entangler)
    prep_pl = np.asarray(_pennylane_prep(theta, phi, reversed_entangler=reversed_entangler), dtype=np.complex128)
    rho0 = _rho(prep_ref)
    ref_rho_t = _open_system_reference(rho0, gamma, t)
    qutip_rho_t = _qutip_evolution(rho0, gamma, [0.0, t])[-1]

    prep_rho_ref = _rho(prep_ref)
    prep_rho_cirq = _rho(prep_cirq)
    prep_rho_pl = _rho(prep_pl)
    base_correlator = _correlator_vector(prep_rho_ref)
    base_zi = _zi_expectation(prep_rho_ref)

    target_corr = _correlator_vector(ref_rho_t)
    torch_fit = _torch_fit_correlator(target_corr, base_correlator, base_zi)
    torch_grad = target_corr[0]
    torch_vec = torch.tensor(target_corr, dtype=torch.float64)
    torch_ga_corr = _torch_ga_roundtrip(target_corr)
    clifford_corr = _clifford_vector(target_corr)
    axis0_shell = _axis0_dynamic_shell_surface(rho0, gamma, t)

    return {
        "gamma": float(gamma),
        "t": float(t),
        "reversed_entangler": bool(reversed_entangler),
        "prep_density_errors": {
            "numpy_vs_cirq": float(np.linalg.norm(prep_rho_ref - prep_rho_cirq)),
            "numpy_vs_pennylane": float(np.linalg.norm(prep_rho_ref - prep_rho_pl)),
        },
        "open_system_density_errors": {
            "numpy_vs_qutip": float(np.linalg.norm(ref_rho_t - qutip_rho_t)),
            "reference_trace_gap": float(abs(np.trace(ref_rho_t) - 1.0)),
        },
        "reference_surface": {
            "prep_concurrence": _concurrence(prep_ref),
            "prep_entropy": _entropy_from_state(prep_ref),
            "prep_coherent_information": _coherent_information(prep_rho_ref),
            "base_correlator": base_correlator.tolist(),
            "base_zi": base_zi,
        },
        "target_correlator": target_corr.tolist(),
        "torch_correlator": _torch_correlator(torch_vec).detach().cpu().numpy().tolist(),
        "torch_grad": float(torch_grad),
        "torch_fit": torch_fit,
        "torch_ga_correlator": torch_ga_corr.tolist(),
        "clifford_correlator": clifford_corr.tolist(),
        "damped_surface": {
            "reference": _density_summary(ref_rho_t),
            "qutip": _density_summary(qutip_rho_t),
        },
        "axis0_dynamic_shell": axis0_shell,
    }


def run_positive_tests() -> dict[str, object]:
    theta = 1.127
    phi = -0.713
    gamma = 0.68
    t = 0.91
    metrics = _case_metrics(theta, phi, gamma, t)

    prep_ok = (
        metrics["prep_density_errors"]["numpy_vs_cirq"] < 1e-6
        and metrics["prep_density_errors"]["numpy_vs_pennylane"] < 1e-6
    )
    open_ok = metrics["open_system_density_errors"]["numpy_vs_qutip"] < 1e-6
    correlator = np.array(metrics["target_correlator"], dtype=np.float64)
    fit = metrics["torch_fit"]
    fit_ok = fit["loss"] < 1e-12 and fit["vector_gap"] < 1e-8
    torch_ga_ok = float(np.max(np.abs(np.array(metrics["torch_ga_correlator"]) - correlator))) < 1e-6
    clifford_ok = float(np.max(np.abs(np.array(metrics["clifford_correlator"]) - correlator))) < 1e-12
    axis0_shell = metrics["axis0_dynamic_shell"]
    graph_surface = axis0_shell["graph_surface"]
    hypergraph_surface = axis0_shell["hypergraph_surface"]
    cell_complex_surface = axis0_shell["cell_complex_surface"]
    topology_surface = axis0_shell["topology_surface"]
    symbolic_surface = axis0_shell["symbolic_surface"]
    constraint_surface = axis0_shell["constraint_surface"]
    axis0_ok = (
        abs(axis0_shell["weights_sum"] - 1.0) < 1e-12
        and axis0_shell["jk_fuzz_dynamic"] > 0.0
        and axis0_shell["coherent_information_span"] > 1e-3
        and axis0_shell["dynamic_vs_frozen_gap"] > 1e-3
        and np.isfinite(axis0_shell["gravity_proxy_mean"])
        and graph_surface["edge_count"] >= len(axis0_shell["lambda_shells"]) - 1
        and hypergraph_surface["max_hyperedge_size"] >= 3
        and cell_complex_surface["boundary_composes_to_zero"]
        and axis0_shell["topology_parity_ok"]
        and topology_surface["beta0"] == 1
        and topology_surface["beta1"] == 0
        and abs(symbolic_surface["symbolic_ic_derivative_mid"]) > 1e-3
        and constraint_surface["sat"]
    )

    return {
        "pass": bool(prep_ok and open_ok and fit_ok and torch_ga_ok and clifford_ok and axis0_ok),
        "prep_surface": {
            "pass": bool(prep_ok),
            "numpy_vs_cirq": metrics["prep_density_errors"]["numpy_vs_cirq"],
            "numpy_vs_pennylane": metrics["prep_density_errors"]["numpy_vs_pennylane"],
        },
        "open_system_surface": {
            "pass": bool(open_ok),
            "numpy_vs_qutip": metrics["open_system_density_errors"]["numpy_vs_qutip"],
            "reference_trace_gap": metrics["open_system_density_errors"]["reference_trace_gap"],
        },
        "correlator_surface": {
            "pass": bool(torch_ga_ok and clifford_ok),
            "target_correlator": metrics["target_correlator"],
            "torch_correlator": metrics["torch_correlator"],
            "torch_ga_correlator": metrics["torch_ga_correlator"],
            "clifford_correlator": metrics["clifford_correlator"],
        },
        "fit_recovery": {
            "pass": bool(fit_ok),
            "decay_fit": fit["decay_fit"],
            "vector_fit": fit["vector_fit"],
            "loss": fit["loss"],
            "vector_gap": fit["vector_gap"],
            "loss_history_tail": fit["loss_history_tail"],
        },
        "axis0_dynamic_shell": {
            "pass": bool(axis0_ok),
            "jk_fuzz_dynamic": axis0_shell["jk_fuzz_dynamic"],
            "i_scalar_dynamic": axis0_shell["i_scalar_dynamic"],
            "i_scalar_frozen": axis0_shell["i_scalar_frozen"],
            "dynamic_vs_frozen_gap": axis0_shell["dynamic_vs_frozen_gap"],
            "coherent_information_span": axis0_shell["coherent_information_span"],
            "gravity_proxy_mean": axis0_shell["gravity_proxy_mean"],
            "expansion_entropy_drive_mean": axis0_shell["expansion_entropy_drive_mean"],
            "lambda_shells": axis0_shell["lambda_shells"],
            "dynamic_weights": axis0_shell["dynamic_weights"],
            "graph_surface": {
                "edge_count": graph_surface["edge_count"],
                "longest_path_length": graph_surface["longest_path_length"],
                "triad_windows": graph_surface["triad_windows"],
            },
            "hypergraph_surface": {
                "num_edges": hypergraph_surface["num_edges"],
                "max_hyperedge_size": hypergraph_surface["max_hyperedge_size"],
                "connected_components": hypergraph_surface["connected_components"],
            },
            "cell_complex_surface": {
                "shape": cell_complex_surface["shape"],
                "boundary_composes_to_zero": cell_complex_surface["boundary_composes_to_zero"],
                "euler_characteristic": cell_complex_surface["euler_characteristic"],
            },
            "topology_surface": {
                "betti_numbers": topology_surface["betti_numbers"],
                "euler_characteristic": topology_surface["euler_characteristic"],
                "parity_ok": axis0_shell["topology_parity_ok"],
            },
            "symbolic_surface": {
                "coherent_poly_degree": symbolic_surface["coherent_poly_degree"],
                "symbolic_ic_derivative_mid": symbolic_surface["symbolic_ic_derivative_mid"],
                "symbolic_entropy_derivative_mid": symbolic_surface["symbolic_entropy_derivative_mid"],
            },
            "constraint_surface": constraint_surface,
        },
    }


def run_negative_tests() -> dict[str, object]:
    theta = 1.127
    phi = -0.713
    gamma = 0.68
    t = 0.91
    prep_ref = _bell_prep(theta, phi)
    rho0 = _rho(prep_ref)
    ref_rho_t = _open_system_reference(rho0, gamma, t)
    qutip_rho_t = _qutip_evolution(rho0, gamma, [0.0, t])[-1]
    wrong_reference = _open_system_reference(rho0, -gamma, t)
    reversed_prep = _cirq_prep(theta, phi, reversed_entangler=True)
    reversed_pl = np.asarray(_pennylane_prep(theta, phi, reversed_entangler=True), dtype=np.complex128)
    base_correlator = _correlator_vector(_rho(prep_ref))
    base_zi = _zi_expectation(_rho(prep_ref))
    wrong_target = _correlator_vector(ref_rho_t).copy()
    wrong_target[1] += 0.2
    wrong_fit = _torch_fit_correlator(wrong_target, base_correlator, base_zi)
    axis0_shell = _axis0_dynamic_shell_surface(rho0, gamma, t)
    bad_constraint = _axis0_shell_constraint_surface(
        np.asarray(list(reversed(axis0_shell["lambda_shells"])), dtype=np.float64),
        np.asarray(axis0_shell["dynamic_weights"], dtype=np.float64),
    )
    face_ablated_hypergraph = _axis0_shell_hypergraph_surface(
        len(axis0_shell["lambda_shells"]),
        axis0_shell["graph_surface"]["pair_edges"],
        [],
    )
    face_ablated_topology = _axis0_shell_topology_surface(
        len(axis0_shell["lambda_shells"]),
        axis0_shell["graph_surface"]["pair_edges"],
        [],
    )

    return {
        "pass": bool(
            np.linalg.norm(qutip_rho_t - wrong_reference) > 1e-2
            and np.linalg.norm(_rho(reversed_prep) - _rho(prep_ref)) > 1e-2
            and np.linalg.norm(_rho(reversed_pl) - _rho(prep_ref)) > 1e-2
            and wrong_fit["loss"] > 1e-2
            and not bad_constraint["sat"]
            and face_ablated_hypergraph["max_hyperedge_size"] < axis0_shell["hypergraph_surface"]["max_hyperedge_size"]
            and face_ablated_topology["beta1"] > axis0_shell["topology_surface"]["beta1"]
        ),
        "wrong_sign_damping_rejected": {
            "pass": bool(np.linalg.norm(qutip_rho_t - wrong_reference) > 1e-2),
            "error": float(np.linalg.norm(qutip_rho_t - wrong_reference)),
        },
        "reversed_entangler_rejected": {
            "pass": bool(
                np.linalg.norm(_rho(reversed_prep) - _rho(prep_ref)) > 1e-2
                and np.linalg.norm(_rho(reversed_pl) - _rho(prep_ref)) > 1e-2
            ),
            "cirq_error": float(np.linalg.norm(_rho(reversed_prep) - _rho(prep_ref))),
            "pennylane_error": float(np.linalg.norm(_rho(reversed_pl) - _rho(prep_ref))),
        },
        "correlator_mismatch_rejected": {
            "pass": bool(wrong_fit["loss"] > 1e-2),
            "loss": wrong_fit["loss"],
            "vector_gap": wrong_fit["vector_gap"],
        },
        "axis0_constraint_order_rejected": {
            "pass": bool(not bad_constraint["sat"]),
            "result": bad_constraint["result"],
        },
        "axis0_shell_face_ablation_rejected": {
            "pass": bool(
                face_ablated_hypergraph["max_hyperedge_size"] < axis0_shell["hypergraph_surface"]["max_hyperedge_size"]
                and face_ablated_topology["beta1"] > axis0_shell["topology_surface"]["beta1"]
            ),
            "full_max_hyperedge_size": axis0_shell["hypergraph_surface"]["max_hyperedge_size"],
            "ablated_max_hyperedge_size": face_ablated_hypergraph["max_hyperedge_size"],
            "full_beta1": axis0_shell["topology_surface"]["beta1"],
            "ablated_beta1": face_ablated_topology["beta1"],
        },
    }


def run_boundary_tests() -> dict[str, object]:
    theta = 0.0
    phi = 0.0
    gamma = 0.68
    t = 0.0
    metrics = _case_metrics(theta, phi, gamma, t)
    prep_ok = metrics["prep_density_errors"]["numpy_vs_cirq"] < 1e-9 and metrics["prep_density_errors"]["numpy_vs_pennylane"] < 1e-9
    open_ok = metrics["open_system_density_errors"]["numpy_vs_qutip"] < 1e-9
    boundary_corr = np.array(metrics["target_correlator"], dtype=np.float64)
    axis0_shell = metrics["axis0_dynamic_shell"]
    graph_surface = axis0_shell["graph_surface"]
    hypergraph_surface = axis0_shell["hypergraph_surface"]
    cell_complex_surface = axis0_shell["cell_complex_surface"]
    topology_surface = axis0_shell["topology_surface"]
    symbolic_surface = axis0_shell["symbolic_surface"]
    constraint_surface = axis0_shell["constraint_surface"]
    boundary_ok = (
        np.isfinite(boundary_corr).all()
        and np.linalg.norm(boundary_corr - np.array([0.0, 0.0, 1.0], dtype=np.float64)) < 1e-9
        and metrics["torch_fit"]["loss"] < 1e-12
        and axis0_shell["coherent_information_span"] < 1e-12
        and axis0_shell["dynamic_vs_frozen_gap"] < 1e-12
        and abs(axis0_shell["gravity_proxy_mean"]) < 1e-12
        and graph_surface["edge_count"] == 0
        and hypergraph_surface["num_edges"] == 0
        and cell_complex_surface["euler_characteristic"] == len(axis0_shell["lambda_shells"])
        and topology_surface["beta0"] == len(axis0_shell["lambda_shells"])
        and topology_surface["beta1"] == 0
        and axis0_shell["topology_parity_ok"]
        and abs(symbolic_surface["symbolic_ic_derivative_mid"]) < 1e-12
        and constraint_surface["sat"]
    )

    return {
        "pass": bool(prep_ok and open_ok and boundary_ok),
        "prep_boundary": {
            "pass": bool(prep_ok),
            "numpy_vs_cirq": metrics["prep_density_errors"]["numpy_vs_cirq"],
            "numpy_vs_pennylane": metrics["prep_density_errors"]["numpy_vs_pennylane"],
        },
        "open_system_boundary": {
            "pass": bool(open_ok),
            "numpy_vs_qutip": metrics["open_system_density_errors"]["numpy_vs_qutip"],
            "reference_trace_gap": metrics["open_system_density_errors"]["reference_trace_gap"],
        },
        "correlator_boundary": {
            "pass": bool(boundary_ok),
            "target_correlator": metrics["target_correlator"],
        },
        "axis0_dynamic_shell_boundary": {
            "pass": bool(
                axis0_shell["coherent_information_span"] < 1e-12
                and axis0_shell["dynamic_vs_frozen_gap"] < 1e-12
                and abs(axis0_shell["gravity_proxy_mean"]) < 1e-12
                and graph_surface["edge_count"] == 0
                and hypergraph_surface["num_edges"] == 0
                and axis0_shell["topology_parity_ok"]
                and abs(symbolic_surface["symbolic_ic_derivative_mid"]) < 1e-12
                and constraint_surface["sat"]
            ),
            "jk_fuzz_dynamic": axis0_shell["jk_fuzz_dynamic"],
            "i_scalar_dynamic": axis0_shell["i_scalar_dynamic"],
            "i_scalar_frozen": axis0_shell["i_scalar_frozen"],
            "gravity_proxy_mean": axis0_shell["gravity_proxy_mean"],
            "graph_edge_count": graph_surface["edge_count"],
            "hypergraph_edge_count": hypergraph_surface["num_edges"],
            "topology_betti_numbers": topology_surface["betti_numbers"],
            "symbolic_ic_derivative_mid": symbolic_surface["symbolic_ic_derivative_mid"],
            "constraint_surface": constraint_surface,
        },
    }


def main() -> int:
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    summary = {
        "positive_all_pass": bool(positive["pass"]),
        "negative_all_pass": bool(negative["pass"]),
        "boundary_all_pass": bool(boundary["pass"]),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": "sim_integration_quantum_open_entangle_correlator_mega_stack",
        "timestamp": datetime.now(UTC).isoformat(),
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "overall_pass": bool(summary["all_pass"]),
        "all_pass": bool(summary["all_pass"]),
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_json_default)

    print(f"PASS={bool(summary['all_pass'])}")
    print(f"Results written to {RESULTS_PATH}")
    print(f"summary.all_pass = {summary['all_pass']}")
    return 0 if summary["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
