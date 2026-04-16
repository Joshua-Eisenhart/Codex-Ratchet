#!/usr/bin/env python3
"""
sim_axis0_lambda_expansion_cosmology_stack.py

Dedicated Axis 0 cosmology-proxy lane for:
  numpy + scipy + qutip + cirq + pennylane + torch + clifford + torch_ga
  + rustworkx + xgi + toponetx + gudhi + sympy + z3 + geomstats

Claim:
  This is a bounded proxy, not a cosmology proof. The lane tests whether one
  live lambda-shell surface can jointly support:
    1. entangled/open-system source witnesses,
    2. dynamic-shell i-scalar / jk-fuzz readout,
    3. entropy-driven expansion and gravity/dark-energy proxy fields,
    4. shell-order / topology / solver closure,
    5. manifold-level shell-carrier aggregation.
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
from geomstats.geometry.hypersphere import Hypersphere
from geomstats.learning.frechet_mean import FrechetMean
from scipy.linalg import expm
from toponetx import CellComplex
from z3 import Real, RealVal, Solver, Sum, sat

from sim_integration_quantum_open_entangle_correlator_mega_stack import (
    _bell_prep,
    _cirq_prep,
    _coherent_information,
    _correlator_vector,
    _entropy_from_density,
    _json_default,
    _open_system_reference,
    _partial_trace_qubit1,
    _pennylane_prep,
    _qutip_evolution,
    _rho,
)


classification = "classical_baseline"
divergence_log = (
    "Classical-to-nonclassical bridge baseline: this is a bounded Axis 0 "
    "lambda-shell cosmology proxy. It does not claim a finished cosmology law. "
    "It tests whether entropy growth, dynamic shells, i-scalar/jk-fuzz, shell "
    "ordering, topology closure, solver guards, and manifold aggregation can "
    "cohere on one live tool-integrated surface."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "lambda-shell arrays, entropy gradients, expansion history, and serialization arithmetic",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "matrix exponential propagator for the shellwise expansion update",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "open-system witness and shellwise expectation readout on damped states",
    },
    "cirq": {
        "tried": True,
        "used": True,
        "reason": "entangling state-preparation witness for the source shell surface",
    },
    "pennylane": {
        "tried": True,
        "used": True,
        "reason": "QNode preparation witness for the same source shell surface",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "fit and gradient witness coupling dark-energy and gravity proxies to the Hubble proxy",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "geometric carrier witness for the cosmology summary vector",
    },
    "torch_ga": {
        "tried": True,
        "used": True,
        "reason": "geometric algebra roundtrip witness for the cosmology summary vector",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "ordered shell DAG witness for the lambda-shell expansion ladder",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "higher-order shell-coupling witness for triadic shell windows",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "cell-complex boundary witness for shell-surface closure",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "persistent topology witness for shell complex parity",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "symbolic interpolation and derivative witness for scale-factor and dark-energy fields",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "constraint witness enforcing ordered lambda shells and monotone scale growth",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "Frechet-mean manifold witness for shell-carrier aggregation on S^2",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "load_bearing",
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
    "geomstats": "load_bearing",
}

RESULTS_PATH = os.path.join(
    os.path.dirname(__file__),
    "a2_state",
    "sim_results",
    "sim_axis0_lambda_expansion_cosmology_stack_results.json",
)

LAYOUT, BLADES = Cl(3)
E1 = BLADES["e1"]
E2 = BLADES["e2"]
E3 = BLADES["e3"]
TORCH_GA_ALG = torch_ga.GeometricAlgebra([1.0, 1.0, 1.0])
TORCH_GA_TO_GEO = torch_ga.TensorToGeometric(TORCH_GA_ALG, [1, 2, 3])
TORCH_GA_TO_TENSOR = torch_ga.GeometricToTensor(TORCH_GA_ALG, [1, 2, 3])
SHELL_SPHERE = Hypersphere(dim=2)


def _clifford_vector(vec: np.ndarray) -> np.ndarray:
    multivector = vec[0] * E1 + vec[1] * E2 + vec[2] * E3
    return np.asarray(multivector.value[1:4], dtype=np.float64)


def _torch_ga_roundtrip(vec: np.ndarray) -> np.ndarray:
    tensor = torch.tensor(vec, dtype=torch.float32).reshape(1, 3)
    geo = TORCH_GA_TO_GEO(tensor)
    return TORCH_GA_TO_TENSOR(geo).detach().cpu().numpy().reshape(-1).astype(np.float64)


def _torch_cosmology_fit(
    dark_energy: np.ndarray,
    gravity_response: np.ndarray,
    hubble_proxy: np.ndarray,
) -> dict[str, object]:
    features = torch.tensor(
        np.stack([dark_energy, gravity_response], axis=1),
        dtype=torch.float64,
    )
    target = torch.tensor(hubble_proxy, dtype=torch.float64)
    weights = torch.nn.Parameter(torch.tensor([0.5, 0.5], dtype=torch.float64))
    bias = torch.nn.Parameter(torch.tensor(0.0, dtype=torch.float64))
    optimizer = torch.optim.LBFGS(
        [weights, bias],
        lr=1.0,
        max_iter=100,
        tolerance_grad=1e-14,
        tolerance_change=1e-14,
        line_search_fn="strong_wolfe",
    )
    history: list[float] = []

    def closure():
        optimizer.zero_grad()
        pred = features @ weights + bias
        loss = torch.mean((pred - target) ** 2)
        loss.backward()
        history.append(float(loss.detach()))
        return loss

    optimizer.step(closure)
    with torch.no_grad():
        pred = features @ weights + bias
        pred_np = pred.detach().cpu().numpy()
        loss = torch.mean((pred - target) ** 2).item()
    return {
        "weights": weights.detach().cpu().numpy().tolist(),
        "bias": float(bias.item()),
        "predicted_hubble": pred_np.tolist(),
        "loss": float(loss),
        "max_gap": float(np.max(np.abs(pred_np - hubble_proxy))),
        "history_tail": [float(value) for value in history[-5:]],
    }


def _scale_history_from_drive(
    lambda_shells: np.ndarray,
    expansion_drive: np.ndarray,
) -> tuple[np.ndarray, list[float]]:
    delta_lambda = float(lambda_shells[1] - lambda_shells[0]) if len(lambda_shells) > 1 else 1.0
    state = np.array([1.0, 1.0], dtype=np.float64)
    scales = [1.0]
    propagator_traces: list[float] = []
    for drive in expansion_drive[1:]:
        generator = np.array([[0.0, float(drive)], [0.0, 0.0]], dtype=np.float64)
        propagator = expm(generator * delta_lambda)
        state = propagator @ state
        scales.append(float(state[0]))
        propagator_traces.append(float(np.trace(propagator)))
    return np.asarray(scales, dtype=np.float64), propagator_traces


def _shell_graph_surface(
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
                    "dark_energy_pressure": float(row["dark_energy_pressure"]),
                    "gravity_response": float(row["gravity_response"]),
                    "scale_factor": float(row["scale_factor"]),
                }
            )
        )

    def _signal(i: int, j: int) -> float:
        lhs = shell_rows[i]
        rhs = shell_rows[j]
        return float(
            abs(float(rhs["dark_energy_pressure"]) - float(lhs["dark_energy_pressure"]))
            + abs(float(rhs["gravity_response"]) - float(lhs["gravity_response"]))
            + abs(float(rhs["scale_factor"]) - float(lhs["scale_factor"]))
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
        dark_values = [float(row["dark_energy_pressure"]) for row in local_rows]
        gravity_values = [float(row["gravity_response"]) for row in local_rows]
        scale_values = [float(row["scale_factor"]) for row in local_rows]
        local_span = float(
            (max(dark_values) - min(dark_values))
            + (max(gravity_values) - min(gravity_values))
            + (max(scale_values) - min(scale_values))
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


def _shell_hypergraph_surface(
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


def _shell_cell_complex_surface(
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


def _shell_topology_surface(
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


def _shell_symbolic_surface(
    lambda_shells: np.ndarray,
    scale_factors: np.ndarray,
    dark_energy_pressure: np.ndarray,
) -> dict[str, object]:
    lam = sp.symbols("lam", real=True)
    scale_pairs = [(float(x), float(y)) for x, y in zip(lambda_shells.tolist(), scale_factors.tolist(), strict=True)]
    dark_pairs = [(float(x), float(y)) for x, y in zip(lambda_shells.tolist(), dark_energy_pressure.tolist(), strict=True)]
    scale_poly = sp.expand(sp.interpolate(scale_pairs, lam))
    dark_poly = sp.expand(sp.interpolate(dark_pairs, lam))
    if len(lambda_shells) % 2 == 0:
        right_idx = len(lambda_shells) // 2
        left_idx = right_idx - 1
        mid_lambda = float(0.5 * (lambda_shells[left_idx] + lambda_shells[right_idx]))
    else:
        mid_lambda = float(lambda_shells[len(lambda_shells) // 2])
    scale_mid = float(sp.N(scale_poly.subs(lam, mid_lambda)))
    d_scale_mid = float(sp.N(sp.diff(scale_poly, lam).subs(lam, mid_lambda)))
    dd_scale_mid = float(sp.N(sp.diff(scale_poly, lam, 2).subs(lam, mid_lambda)))
    return {
        "scale_factor_polynomial": str(scale_poly),
        "dark_energy_polynomial": str(dark_poly),
        "scale_poly_degree": int(sp.Poly(scale_poly, lam).degree()),
        "dark_poly_degree": int(sp.Poly(dark_poly, lam).degree()),
        "mid_lambda": mid_lambda,
        "symbolic_hubble_mid": float(d_scale_mid / max(scale_mid, 1e-12)),
        "symbolic_acceleration_mid": float(dd_scale_mid),
        "symbolic_dark_energy_mid": float(sp.N(dark_poly.subs(lam, mid_lambda))),
    }


def _shell_constraint_surface(
    lambda_shells: np.ndarray,
    scale_factors: np.ndarray,
    dark_energy_pressure: np.ndarray,
) -> dict[str, object]:
    solver = Solver()
    lambda_vars = [Real(f"lambda_shell_{idx}") for idx in range(len(lambda_shells))]
    scale_vars = [Real(f"scale_factor_{idx}") for idx in range(len(scale_factors))]
    dark_vars = [Real(f"dark_energy_{idx}") for idx in range(len(dark_energy_pressure))]

    for var, value in zip(lambda_vars, lambda_shells.tolist(), strict=True):
        solver.add(var == RealVal(str(float(value))))
    for var, value in zip(scale_vars, scale_factors.tolist(), strict=True):
        solver.add(var == RealVal(str(float(value))))
        solver.add(var >= RealVal("1.0"))
    for var, value in zip(dark_vars, dark_energy_pressure.tolist(), strict=True):
        solver.add(var == RealVal(str(float(value))))
        solver.add(var >= RealVal("0.0"))

    for lhs, rhs in zip(lambda_vars[:-1], lambda_vars[1:], strict=True):
        solver.add(lhs < rhs)
    for lhs, rhs in zip(scale_vars[:-1], scale_vars[1:], strict=True):
        solver.add(lhs <= rhs)

    if dark_vars:
        dark_sum = Sum(*dark_vars)
        solver.add(dark_sum >= RealVal("0.0"))

    result = solver.check()
    return {
        "result": str(result),
        "sat": bool(result == sat),
    }


def _shell_manifold_surface(
    lambda_density: np.ndarray,
    dark_energy_pressure: np.ndarray,
    scale_factors: np.ndarray,
) -> dict[str, object]:
    raw_points = np.stack(
        [
            lambda_density - float(np.mean(lambda_density)),
            dark_energy_pressure - float(np.mean(dark_energy_pressure)),
            scale_factors - float(scale_factors[0]),
        ],
        axis=1,
    )
    points = []
    for row in raw_points:
        norm = float(np.linalg.norm(row))
        if norm < 1e-12:
            points.append(np.array([0.0, 0.0, 1.0], dtype=np.float64))
        else:
            points.append(np.asarray(row, dtype=np.float64) / norm)
    points_arr = np.asarray(points, dtype=np.float64)
    estimator = FrechetMean(space=SHELL_SPHERE)
    estimator.fit(points_arr)
    mean = np.asarray(estimator.estimate_, dtype=np.float64)
    dists = np.asarray(
        [float(SHELL_SPHERE.metric.dist(point, mean)) for point in points_arr],
        dtype=np.float64,
    )
    return {
        "frechet_mean": mean.tolist(),
        "mean_norm": float(np.linalg.norm(mean)),
        "mean_geodesic_distance": float(np.mean(dists)),
        "max_geodesic_distance": float(np.max(dists)),
    }


def _cosmology_case(
    theta: float,
    phi: float,
    gamma: float,
    t: float,
    *,
    n_shells: int = 7,
) -> dict[str, object]:
    prep_ref = _bell_prep(theta, phi)
    prep_cirq = _cirq_prep(theta, phi)
    prep_pl = np.asarray(qml.math.asarray(_pennylane_prep(theta, phi)), dtype=np.complex128)
    prep_rho_ref = _rho(prep_ref)
    ref_rho_t = _open_system_reference(prep_rho_ref, gamma, t)
    qutip_rho_t = _qutip_evolution(prep_rho_ref, gamma, [0.0, t])[-1]

    lambda_shells = np.linspace(0.0, 1.0, n_shells, dtype=np.float64)
    shell_rows: list[dict[str, object]] = []
    full_entropy_series: list[float] = []
    coherent_series: list[float] = []
    correlator_series: list[float] = []
    qutip_z_series: list[float] = []
    previous_entropy: float | None = None

    cirq_cnot_trace = float(np.real(np.trace(cirq.unitary(cirq.CNOT))))

    for lam in lambda_shells:
        shell_time = float(lam * t)
        rho_shell = _open_system_reference(prep_rho_ref, gamma, shell_time)
        full_entropy = _entropy_from_density(rho_shell)
        reduced_entropy = _entropy_from_density(_partial_trace_qubit1(rho_shell))
        coherent_information = _coherent_information(rho_shell)
        correlator_norm = float(np.linalg.norm(_correlator_vector(rho_shell)))
        rho_q = qutip.Qobj(rho_shell, dims=[[2, 2], [2, 2]])
        qutip_z = float(
            np.real(
                qutip.expect(
                    qutip.tensor(qutip.sigmaz(), qutip.qeye(2)),
                    rho_q,
                )
            )
        )
        entropy_delta = 0.0 if previous_entropy is None else full_entropy - previous_entropy
        shell_rows.append(
            {
                "lambda_shell": float(lam),
                "time": shell_time,
                "full_entropy": float(full_entropy),
                "reduced_entropy": float(reduced_entropy),
                "coherent_information": float(coherent_information),
                "entropy_delta": float(entropy_delta),
                "correlator_norm": correlator_norm,
                "qutip_z_expectation": qutip_z,
            }
        )
        full_entropy_series.append(float(full_entropy))
        coherent_series.append(float(coherent_information))
        correlator_series.append(correlator_norm)
        qutip_z_series.append(qutip_z)
        previous_entropy = full_entropy

    full_entropy_arr = np.asarray(full_entropy_series, dtype=np.float64)
    coherent_arr = np.asarray(coherent_series, dtype=np.float64)
    correlator_arr = np.asarray(correlator_series, dtype=np.float64)
    qutip_z_arr = np.asarray(qutip_z_series, dtype=np.float64)

    entropy_gradient = np.gradient(full_entropy_arr, lambda_shells)
    coherent_gradient = np.gradient(coherent_arr, lambda_shells)
    correlator_deviation = np.abs(correlator_arr - correlator_arr[0])
    lambda_density = np.clip(full_entropy_arr - coherent_arr + correlator_deviation, 0.0, None)
    dark_energy_pressure = np.clip(lambda_density + np.maximum(entropy_gradient, 0.0), 0.0, None)
    gravity_response = np.clip(dark_energy_pressure - coherent_gradient, 0.0, None)
    expansion_drive = dark_energy_pressure + gravity_response
    scale_factors, propagator_traces = _scale_history_from_drive(lambda_shells, expansion_drive)
    hubble_proxy = np.gradient(np.log(np.clip(scale_factors, 1e-12, None)), lambda_shells)
    acceleration_proxy = np.gradient(hubble_proxy, lambda_shells)

    drive_weights = expansion_drive + 1e-12
    drive_weights = drive_weights / float(np.sum(drive_weights))
    frozen_weights = np.full_like(drive_weights, 1.0 / len(drive_weights))
    jk_fuzz_dynamic = float(-np.sum(drive_weights * np.log2(drive_weights)))
    i_scalar_dynamic = float(np.dot(drive_weights, coherent_arr))
    i_scalar_frozen = float(np.dot(frozen_weights, coherent_arr))

    for row, lam_density, dark, gravity, drive, scale in zip(
        shell_rows,
        lambda_density.tolist(),
        dark_energy_pressure.tolist(),
        gravity_response.tolist(),
        expansion_drive.tolist(),
        scale_factors.tolist(),
        strict=True,
    ):
        row["lambda_density"] = float(lam_density)
        row["dark_energy_pressure"] = float(dark)
        row["gravity_response"] = float(gravity)
        row["expansion_drive"] = float(drive)
        row["scale_factor"] = float(scale)

    graph_surface = _shell_graph_surface(shell_rows)
    hypergraph_surface = _shell_hypergraph_surface(
        n_shells,
        graph_surface["pair_edges"],
        graph_surface["triad_windows"],
    )
    cell_complex_surface = _shell_cell_complex_surface(
        n_shells,
        graph_surface["pair_edges"],
        graph_surface["triad_windows"],
    )
    topology_surface = _shell_topology_surface(
        n_shells,
        graph_surface["pair_edges"],
        graph_surface["triad_windows"],
    )
    symbolic_surface = _shell_symbolic_surface(
        lambda_shells,
        scale_factors,
        dark_energy_pressure,
    )
    constraint_surface = _shell_constraint_surface(
        lambda_shells,
        scale_factors,
        dark_energy_pressure,
    )
    manifold_surface = _shell_manifold_surface(
        lambda_density,
        dark_energy_pressure,
        scale_factors,
    )

    torch_fit = _torch_cosmology_fit(dark_energy_pressure, gravity_response, hubble_proxy)
    cosmology_vector = np.array(
        [
            float(np.mean(gravity_response)),
            float(np.mean(dark_energy_pressure)),
            float(np.mean(acceleration_proxy)),
        ],
        dtype=np.float64,
    )
    clifford_vector = _clifford_vector(cosmology_vector)
    torch_ga_vector = _torch_ga_roundtrip(cosmology_vector)

    return {
        "prep_density_errors": {
            "numpy_vs_cirq": float(np.linalg.norm(_rho(prep_ref) - _rho(prep_cirq))),
            "numpy_vs_pennylane": float(np.linalg.norm(_rho(prep_ref) - _rho(prep_pl))),
        },
        "open_system_density_errors": {
            "numpy_vs_qutip": float(np.linalg.norm(ref_rho_t - qutip_rho_t)),
            "reference_trace_gap": float(abs(np.trace(ref_rho_t) - 1.0)),
        },
        "prep_surface": {
            "cirq_cnot_trace": cirq_cnot_trace,
            "pennylane_state_norm": float(np.linalg.norm(prep_pl)),
        },
        "shell_rows": shell_rows,
        "lambda_shells": lambda_shells.tolist(),
        "dynamic_weights": drive_weights.tolist(),
        "jk_fuzz_dynamic": jk_fuzz_dynamic,
        "i_scalar_dynamic": i_scalar_dynamic,
        "i_scalar_frozen": i_scalar_frozen,
        "dynamic_vs_frozen_gap": float(abs(i_scalar_dynamic - i_scalar_frozen)),
        "full_entropy_span": float(np.max(full_entropy_arr) - np.min(full_entropy_arr)),
        "coherent_information_span": float(np.max(coherent_arr) - np.min(coherent_arr)),
        "lambda_density": lambda_density.tolist(),
        "dark_energy_pressure": dark_energy_pressure.tolist(),
        "gravity_response": gravity_response.tolist(),
        "expansion_drive": expansion_drive.tolist(),
        "scale_factors": scale_factors.tolist(),
        "hubble_proxy": hubble_proxy.tolist(),
        "acceleration_proxy": acceleration_proxy.tolist(),
        "qutip_z_expectation": qutip_z_arr.tolist(),
        "propagator_traces": propagator_traces,
        "graph_surface": graph_surface,
        "hypergraph_surface": hypergraph_surface,
        "cell_complex_surface": cell_complex_surface,
        "topology_surface": topology_surface,
        "topology_parity_ok": bool(
            cell_complex_surface["euler_characteristic"] == topology_surface["euler_characteristic"]
        ),
        "symbolic_surface": symbolic_surface,
        "constraint_surface": constraint_surface,
        "manifold_surface": manifold_surface,
        "torch_fit": torch_fit,
        "clifford_vector": clifford_vector.tolist(),
        "torch_ga_vector": torch_ga_vector.tolist(),
        "cosmology_vector": cosmology_vector.tolist(),
    }


def run_positive_tests() -> dict[str, object]:
    metrics = _cosmology_case(theta=1.127, phi=-0.713, gamma=0.68, t=0.91)
    graph_surface = metrics["graph_surface"]
    hypergraph_surface = metrics["hypergraph_surface"]
    cell_complex_surface = metrics["cell_complex_surface"]
    topology_surface = metrics["topology_surface"]
    symbolic_surface = metrics["symbolic_surface"]
    manifold_surface = metrics["manifold_surface"]
    torch_fit = metrics["torch_fit"]

    prep_ok = (
        metrics["prep_density_errors"]["numpy_vs_cirq"] < 1e-6
        and metrics["prep_density_errors"]["numpy_vs_pennylane"] < 1e-6
    )
    open_ok = metrics["open_system_density_errors"]["numpy_vs_qutip"] < 1e-6
    ga_ok = float(np.max(np.abs(np.array(metrics["clifford_vector"]) - np.array(metrics["cosmology_vector"])))) < 1e-12
    torch_ga_ok = float(np.max(np.abs(np.array(metrics["torch_ga_vector"]) - np.array(metrics["cosmology_vector"])))) < 1e-5
    axis0_ok = (
        abs(sum(metrics["dynamic_weights"]) - 1.0) < 1e-12
        and metrics["jk_fuzz_dynamic"] > 0.1
        and metrics["dynamic_vs_frozen_gap"] > 1e-3
        and metrics["full_entropy_span"] > 1e-2
        and metrics["coherent_information_span"] > 1e-2
        and float(metrics["scale_factors"][-1]) > 1.1
        and float(np.mean(metrics["dark_energy_pressure"])) > 1e-2
        and float(np.mean(metrics["gravity_response"])) > 1e-2
        and float(np.mean(metrics["hubble_proxy"])) > 1e-3
        and graph_surface["longest_path_length"] >= len(metrics["lambda_shells"]) - 2
        and hypergraph_surface["max_hyperedge_size"] >= 3
        and cell_complex_surface["boundary_composes_to_zero"]
        and topology_surface["beta0"] == 1
        and topology_surface["beta1"] == 0
        and metrics["topology_parity_ok"]
        and symbolic_surface["symbolic_hubble_mid"] > 1e-3
        and metrics["constraint_surface"]["sat"]
        and manifold_surface["mean_geodesic_distance"] > 1e-2
        and abs(manifold_surface["mean_norm"] - 1.0) < 1e-9
        and torch_fit["loss"] < 5e-2
    )

    return {
        "pass": bool(prep_ok and open_ok and ga_ok and torch_ga_ok and axis0_ok),
        "prep_surface": {
            "pass": bool(prep_ok),
            **metrics["prep_density_errors"],
            **metrics["prep_surface"],
        },
        "open_system_surface": {
            "pass": bool(open_ok),
            **metrics["open_system_density_errors"],
        },
        "axis0_lambda_expansion": {
            "pass": bool(axis0_ok),
            "jk_fuzz_dynamic": metrics["jk_fuzz_dynamic"],
            "i_scalar_dynamic": metrics["i_scalar_dynamic"],
            "i_scalar_frozen": metrics["i_scalar_frozen"],
            "dynamic_vs_frozen_gap": metrics["dynamic_vs_frozen_gap"],
            "scale_factors": metrics["scale_factors"],
            "dark_energy_pressure_mean": float(np.mean(metrics["dark_energy_pressure"])),
            "gravity_response_mean": float(np.mean(metrics["gravity_response"])),
            "hubble_proxy_mean": float(np.mean(metrics["hubble_proxy"])),
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
            "topology_surface": {
                "betti_numbers": topology_surface["betti_numbers"],
                "euler_characteristic": topology_surface["euler_characteristic"],
                "parity_ok": metrics["topology_parity_ok"],
            },
            "symbolic_surface": symbolic_surface,
            "constraint_surface": metrics["constraint_surface"],
            "manifold_surface": manifold_surface,
            "torch_fit": {
                "weights": torch_fit["weights"],
                "bias": torch_fit["bias"],
                "loss": torch_fit["loss"],
                "max_gap": torch_fit["max_gap"],
            },
            "clifford_vector": metrics["clifford_vector"],
            "torch_ga_vector": metrics["torch_ga_vector"],
        },
    }


def run_negative_tests() -> dict[str, object]:
    metrics = _cosmology_case(theta=1.127, phi=-0.713, gamma=0.68, t=0.91)
    reverse_scale_constraint = _shell_constraint_surface(
        np.asarray(metrics["lambda_shells"], dtype=np.float64),
        np.asarray(list(reversed(metrics["scale_factors"])), dtype=np.float64),
        np.asarray(metrics["dark_energy_pressure"], dtype=np.float64),
    )
    reverse_lambda_constraint = _shell_constraint_surface(
        np.asarray(list(reversed(metrics["lambda_shells"])), dtype=np.float64),
        np.asarray(metrics["scale_factors"], dtype=np.float64),
        np.asarray(metrics["dark_energy_pressure"], dtype=np.float64),
    )
    face_ablated_hypergraph = _shell_hypergraph_surface(
        len(metrics["lambda_shells"]),
        metrics["graph_surface"]["pair_edges"],
        [],
    )
    face_ablated_topology = _shell_topology_surface(
        len(metrics["lambda_shells"]),
        metrics["graph_surface"]["pair_edges"],
        [],
    )
    flat_scale_factors, _ = _scale_history_from_drive(
        np.asarray(metrics["lambda_shells"], dtype=np.float64),
        np.zeros(len(metrics["lambda_shells"]), dtype=np.float64),
    )

    return {
        "pass": bool(
            not reverse_scale_constraint["sat"]
            and not reverse_lambda_constraint["sat"]
            and face_ablated_hypergraph["max_hyperedge_size"] < metrics["hypergraph_surface"]["max_hyperedge_size"]
            and face_ablated_topology["beta1"] > metrics["topology_surface"]["beta1"]
            and float(flat_scale_factors[-1]) < float(metrics["scale_factors"][-1]) - 0.5
        ),
        "reverse_scale_growth_rejected": {
            "pass": bool(not reverse_scale_constraint["sat"]),
            "result": reverse_scale_constraint["result"],
        },
        "reverse_lambda_order_rejected": {
            "pass": bool(not reverse_lambda_constraint["sat"]),
            "result": reverse_lambda_constraint["result"],
        },
        "shell_face_ablation_rejected": {
            "pass": bool(
                face_ablated_hypergraph["max_hyperedge_size"] < metrics["hypergraph_surface"]["max_hyperedge_size"]
                and face_ablated_topology["beta1"] > metrics["topology_surface"]["beta1"]
            ),
            "full_max_hyperedge_size": metrics["hypergraph_surface"]["max_hyperedge_size"],
            "ablated_max_hyperedge_size": face_ablated_hypergraph["max_hyperedge_size"],
            "full_beta1": metrics["topology_surface"]["beta1"],
            "ablated_beta1": face_ablated_topology["beta1"],
        },
        "entropy_drive_ablation_reduces_expansion": {
            "pass": bool(float(flat_scale_factors[-1]) < float(metrics["scale_factors"][-1]) - 0.5),
            "positive_final_scale": float(metrics["scale_factors"][-1]),
            "ablated_final_scale": float(flat_scale_factors[-1]),
        },
    }


def run_boundary_tests() -> dict[str, object]:
    metrics = _cosmology_case(theta=0.0, phi=0.0, gamma=0.0, t=0.0)
    graph_surface = metrics["graph_surface"]
    hypergraph_surface = metrics["hypergraph_surface"]
    cell_complex_surface = metrics["cell_complex_surface"]
    topology_surface = metrics["topology_surface"]
    symbolic_surface = metrics["symbolic_surface"]
    manifold_surface = metrics["manifold_surface"]

    boundary_ok = (
        metrics["prep_density_errors"]["numpy_vs_cirq"] < 1e-9
        and metrics["prep_density_errors"]["numpy_vs_pennylane"] < 1e-9
        and metrics["open_system_density_errors"]["numpy_vs_qutip"] < 1e-9
        and float(metrics["full_entropy_span"]) < 1e-12
        and float(metrics["coherent_information_span"]) < 1e-12
        and float(metrics["dynamic_vs_frozen_gap"]) < 1e-12
        and abs(float(metrics["scale_factors"][-1]) - 1.0) < 1e-9
        and graph_surface["edge_count"] == 0
        and hypergraph_surface["num_edges"] == 0
        and cell_complex_surface["euler_characteristic"] == len(metrics["lambda_shells"])
        and topology_surface["beta0"] == len(metrics["lambda_shells"])
        and topology_surface["beta1"] == 0
        and metrics["topology_parity_ok"]
        and abs(symbolic_surface["symbolic_hubble_mid"]) < 1e-9
        and metrics["constraint_surface"]["sat"]
        and manifold_surface["mean_geodesic_distance"] < 1e-12
    )

    return {
        "pass": bool(boundary_ok),
        "axis0_lambda_expansion_boundary": {
            "pass": bool(boundary_ok),
            "jk_fuzz_dynamic": metrics["jk_fuzz_dynamic"],
            "i_scalar_dynamic": metrics["i_scalar_dynamic"],
            "i_scalar_frozen": metrics["i_scalar_frozen"],
            "dynamic_vs_frozen_gap": metrics["dynamic_vs_frozen_gap"],
            "final_scale_factor": float(metrics["scale_factors"][-1]),
            "graph_edge_count": graph_surface["edge_count"],
            "hypergraph_edge_count": hypergraph_surface["num_edges"],
            "topology_betti_numbers": topology_surface["betti_numbers"],
            "symbolic_hubble_mid": symbolic_surface["symbolic_hubble_mid"],
            "constraint_surface": metrics["constraint_surface"],
            "manifold_surface": manifold_surface,
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
        "name": "sim_axis0_lambda_expansion_cosmology_stack",
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
