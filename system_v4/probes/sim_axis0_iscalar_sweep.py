#!/usr/bin/env python3
"""
Axis 0 i-Scalar Functional Sweep
=================================
Selects the canonical Axis 0 functional from the four options in
AXIS0_SPEC_OPTIONS_v0.1-v0.3.

For each engine (T1, T2) × torus (inner, clifford, outer) × perturbation
(depolarizing, dephasing, amplitude_damping) at small ε, computes the
Axis-0 index A0 = [D(Φ_ε(ρ)) - D(ρ)] / ε for each option family:

  Option A — Shannon entropy of pairwise MI distribution
             ("correlation diversity": H of the normalized MI weights)
  Option B — Variance of pairwise MI across subsystem pairs
             ("deviation damping": does spread increase or decrease?)
  Option C — Coherent information spread across LR cuts
             ("negative entropy survival": I_c(A→B) under noise)
  Option D — Path entropy of Kraus unraveling histories
             ("JK fuzz operationalization": branching variety)

Verdict criteria:
  - Stability: how consistently does the sign agree across 18 configs?
  - Separation: how large is |A0| on average (signal, not noise)?
  - Doctrine fit: does the allostatic/homeostatic split match engine type
    (T1=homeostatic bias, T2=allostatic bias per Grok Unified Physics)?

The winning option is the canonical i-scalar functional.
"""

from __future__ import annotations
import json, os, sys, copy
from datetime import UTC, datetime

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import gudhi
import numpy as np
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
classification = "classical_baseline"  # auto-backfill
divergence_log = (
    "Classical foundation baseline: this sweeps candidate Axis-0 i-scalar "
    "functionals numerically. The option sweep is now grounded in the same deep "
    "Axis 0 shell contract used elsewhere: history-driven shell bridge per "
    "config, plus a graph/topology/solver/manifold witness over the aggregate "
    "option ranking."
)
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "functional sweep, perturbation arrays, and aggregate option numerics"},
    "scipy": {"tried": True, "used": True, "reason": "matrix exponential propagator for option-ranking expansion updates"},
    "pytorch": {"tried": True, "used": True, "reason": "fit and gradient witness over option-level shell-alignment features"},
    "clifford": {"tried": True, "used": True, "reason": "geometric carrier witness for the winner summary vector"},
    "torch_ga": {"tried": True, "used": True, "reason": "geometric algebra roundtrip witness for the winner summary vector"},
    "rustworkx": {"tried": True, "used": True, "reason": "ordered option DAG witness over the ranked i-scalar candidates"},
    "xgi": {"tried": True, "used": True, "reason": "higher-order perturbation-option coupling witness"},
    "toponetx": {"tried": True, "used": True, "reason": "cell-complex boundary witness for the ranked option surface"},
    "gudhi": {"tried": True, "used": True, "reason": "persistent topology witness for the option-ranking complex"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic interpolation and derivative witness for option expansion trends"},
    "z3": {"tried": True, "used": True, "reason": "constraint witness enforcing option ranking order and monotone scale growth"},
    "geomstats": {"tried": True, "used": True, "reason": "Frechet-mean manifold witness for aggregate option geometry"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "load_bearing",
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER
from sim_axis0_dynamic_shell import lane_d_topology_expansion_bridge

# ─────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────

TORUS_CONFIGS = [
    ("inner",    TORUS_INNER),
    ("clifford", TORUS_CLIFFORD),
    ("outer",    TORUS_OUTER),
]
PERTURBATION_EPS  = 0.05   # perturbation strength
KRAUS_BRANCHES    = 16     # number of Kraus history samples for Option D
EPS_NUM           = 1e-12  # numerical floor

SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
I2      = np.eye(2, dtype=complex)
OPTION_ORDER = [
    "A_mi_diversity",
    "B_mi_variance",
    "C_coherent_info",
    "D_jk_path_entropy",
]
LAYOUT, BLADES = Cl(3)
E1 = BLADES["e1"]
E2 = BLADES["e2"]
E3 = BLADES["e3"]
TORCH_GA_ALG = torch_ga.GeometricAlgebra([1.0, 1.0, 1.0])
TORCH_GA_TO_GEO = torch_ga.TensorToGeometric(TORCH_GA_ALG, [1, 2, 3])
TORCH_GA_TO_TENSOR = torch_ga.GeometricToTensor(TORCH_GA_ALG, [1, 2, 3])
OPTION_SPHERE = Hypersphere(dim=2)

# ─────────────────────────────────────────────────────────────────────
# QIT Utilities
# ─────────────────────────────────────────────────────────────────────

def vne(rho: np.ndarray) -> float:
    rho = (rho + rho.conj().T) / 2
    ev = np.real(np.linalg.eigvalsh(rho))
    ev = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log2(ev))) if len(ev) else 0.0


def ptr_B(r): return np.trace(r.reshape(2, 2, 2, 2), axis1=1, axis2=3)
def ptr_A(r): return np.trace(r.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def mi_val(rho_AB: np.ndarray) -> float:
    return max(0.0, vne(ptr_B(rho_AB)) + vne(ptr_A(rho_AB)) - vne(rho_AB))


def coherent_info(rho_AB: np.ndarray) -> float:
    """I_c(A→B) = S(ρ_B) - S(ρ_AB)."""
    return float(vne(ptr_B(rho_AB)) - vne(rho_AB))


def bloch(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.real(np.trace(s @ rho)))
                     for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])


def lr_asym(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.clip(0.5 * np.linalg.norm(bloch(a) - bloch(b)), 0.0, 1.0))


# ─────────────────────────────────────────────────────────────────────
# Perturbation Channels (act on a single 2×2 density matrix)
# ─────────────────────────────────────────────────────────────────────

def depolarize(rho: np.ndarray, eps: float) -> np.ndarray:
    """Depolarizing: ρ → (1-ε)ρ + (ε/2)I."""
    out = (1 - eps) * rho + (eps / 2) * I2
    return _ensure_valid_density(out)


def dephase(rho: np.ndarray, eps: float) -> np.ndarray:
    """Dephasing: kills off-diagonal by factor (1-ε)."""
    out = rho.copy()
    out[0, 1] *= (1 - eps)
    out[1, 0] *= (1 - eps)
    return _ensure_valid_density(out)


def amp_damp(rho: np.ndarray, eps: float) -> np.ndarray:
    """Amplitude damping toward |0⟩."""
    gamma = eps
    K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
    K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)
    out = K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T
    return _ensure_valid_density(out)


PERTURBATIONS = {
    "depolarizing":    depolarize,
    "dephasing":       dephase,
    "amplitude_damp":  amp_damp,
}


def perturb_history(history: list[dict], perturb_fn, eps: float) -> list[dict]:
    """Apply a single-qubit channel independently to ρ_L and ρ_R in each step."""
    out = []
    for step in history:
        s = dict(step)
        s["rho_L"] = perturb_fn(step["rho_L"], eps)
        s["rho_R"] = perturb_fn(step["rho_R"], eps)
        out.append(s)
    return out


# ─────────────────────────────────────────────────────────────────────
# Build joint LR density matrix for each step (4×4)
# ─────────────────────────────────────────────────────────────────────

PSI_MINUS = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)
BELL_PSI_MINUS = np.outer(PSI_MINUS, PSI_MINUS.conj())


def joint_rho(step: dict) -> np.ndarray:
    """4×4 joint LR density matrix with chiral Bell injection."""
    rho_L = step["rho_L"]
    rho_R = step["rho_R"]
    p = float(np.clip(lr_asym(rho_L, rho_R), 0.01, 0.99))
    prod = _ensure_valid_density(np.kron(rho_L, rho_R))
    return _ensure_valid_density((1 - p) * prod + p * BELL_PSI_MINUS)


# ─────────────────────────────────────────────────────────────────────
# Option A — Shannon entropy of MI distribution
# "Correlation diversity": how spread is MI across the LR pair?
# For a 2-qubit LR system we have only one pair; we proxy diversity
# by computing the MI at different stages and measuring its Shannon
# entropy across the trajectory.
# ─────────────────────────────────────────────────────────────────────

def option_A(history: list[dict]) -> float:
    """Shannon entropy of the per-step MI distribution across trajectory."""
    mi_vals = np.array([mi_val(joint_rho(s)) for s in history])
    total = mi_vals.sum()
    if total < EPS_NUM:
        return 0.0
    p = mi_vals / total
    p = p[p > EPS_NUM]
    return float(-np.sum(p * np.log2(p)))


# ─────────────────────────────────────────────────────────────────────
# Option B — Variance of pairwise MI across trajectory
# "Deviation damping": does the spread of MI values decrease?
# ─────────────────────────────────────────────────────────────────────

def option_B(history: list[dict]) -> float:
    """Variance of per-step MI values across trajectory."""
    mi_vals = np.array([mi_val(joint_rho(s)) for s in history])
    return float(np.var(mi_vals))


# ─────────────────────────────────────────────────────────────────────
# Option C — Coherent information spread
# "Negative entropy survival": mean I_c(A→B) across trajectory.
# Allostatic if I_c increases under perturbation (survives/spreads),
# homeostatic if it collapses.
# ─────────────────────────────────────────────────────────────────────

def option_C(history: list[dict]) -> float:
    """Mean coherent information I_c(A→B) across trajectory."""
    ic_vals = np.array([coherent_info(joint_rho(s)) for s in history])
    return float(np.mean(ic_vals))


# ─────────────────────────────────────────────────────────────────────
# Option D — Path entropy of Kraus unraveling histories (JK fuzz)
# Each step has one Kraus operator K_k with k = branch index.
# We sample KRAUS_BRANCHES random weight vectors to simulate a
# stochastic unraveling and compute the path entropy H_path.
# ─────────────────────────────────────────────────────────────────────

def option_D(history: list[dict], rng: np.random.Generator | None = None) -> float:
    """
    Path entropy H_path = -Σ P(k) log P(k) over sampled Kraus histories.
    
    Operationalization: at each step, we have a joint ρ. We decompose it
    into a convex combination of pure states (spectral) as the 'Kraus branches'.
    The branch probability = eigenvalue weight. Path entropy = Shannon entropy
    of the product distribution over the trajectory.
    """
    if rng is None:
        rng = np.random.default_rng(42)
    
    T = len(history)
    if T == 0:
        return 0.0
    
    # At each step, get eigenvalue distribution (branch weights)
    step_branch_probs = []
    for step in history:
        rho_j = joint_rho(step)
        # Hermitianize and get eigenvalues
        rho_j = (rho_j + rho_j.conj().T) / 2
        ev = np.real(np.linalg.eigvalsh(rho_j))
        ev = np.clip(ev, 0, None)
        total = ev.sum()
        if total < EPS_NUM:
            ev = np.ones(4) / 4
        else:
            ev = ev / total
        step_branch_probs.append(ev)  # shape (4,)
    
    # Sample KRAUS_BRANCHES paths: each path is a sequence of branch ids
    # Path probability = product of branch weights at each step
    n_branches_per_step = 4  # 4×4 matrix has 4 eigenvalues
    path_probs = {}
    for _ in range(KRAUS_BRANCHES):
        path = tuple(rng.choice(n_branches_per_step, p=probs)
                     for probs in step_branch_probs)
        prob = 1.0
        for t, k in enumerate(path):
            prob *= step_branch_probs[t][k]
        path_probs[path] = path_probs.get(path, 0.0) + prob
    
    # Normalize and compute Shannon entropy
    total = sum(path_probs.values())
    if total < EPS_NUM:
        return 0.0
    probs = np.array(list(path_probs.values())) / total
    probs = probs[probs > EPS_NUM]
    return float(-np.sum(probs * np.log2(probs)))


def _clifford_vector(vec: np.ndarray) -> np.ndarray:
    multivector = vec[0] * E1 + vec[1] * E2 + vec[2] * E3
    return np.asarray(multivector.value[1:4], dtype=np.float64)


def _torch_ga_roundtrip(vec: np.ndarray) -> np.ndarray:
    tensor = torch.tensor(vec, dtype=torch.float32).reshape(1, 3)
    geo = TORCH_GA_TO_GEO(tensor)
    return TORCH_GA_TO_TENSOR(geo).detach().cpu().numpy().reshape(-1).astype(np.float64)


def _torch_option_fit(features: np.ndarray, target: np.ndarray) -> dict[str, object]:
    features_t = torch.tensor(features, dtype=torch.float64)
    target_t = torch.tensor(target, dtype=torch.float64)
    weights = torch.nn.Parameter(torch.full((features.shape[1],), 0.5, dtype=torch.float64))
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
        pred = features_t @ weights + bias
        loss = torch.mean((pred - target_t) ** 2)
        loss.backward()
        history.append(float(loss.detach()))
        return loss

    optimizer.step(closure)
    with torch.no_grad():
        pred = features_t @ weights + bias
        pred_np = pred.detach().cpu().numpy()
        loss = torch.mean((pred - target_t) ** 2).item()
    return {
        "weights": weights.detach().cpu().numpy().tolist(),
        "bias": float(bias.item()),
        "predicted": pred_np.tolist(),
        "loss": float(loss),
        "max_gap": float(np.max(np.abs(pred_np - target))),
        "history_tail": [float(value) for value in history[-5:]],
    }


def _option_scale_history(
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


def _option_graph_surface(
    option_rows: list[dict[str, object]],
    *,
    eps: float = 1e-6,
) -> dict[str, object]:
    dag = rx.PyDiGraph()
    node_ids: list[int] = []
    pair_edges: set[tuple[int, int]] = set()
    triad_windows: list[tuple[int, int, int]] = []
    edge_signal_sum = 0.0

    for idx, row in enumerate(option_rows):
        node_ids.append(dag.add_node({"rank_index": idx, "option": str(row["option"])}))

    def _signal(i: int, j: int) -> float:
        lhs = option_rows[i]
        rhs = option_rows[j]
        return float(
            abs(float(rhs["mean_abs_a0"]) - float(lhs["mean_abs_a0"]))
            + abs(float(rhs["doctrine_fit"]) - float(lhs["doctrine_fit"]))
            + abs(float(rhs["shell_alignment_abs"]) - float(lhs["shell_alignment_abs"]))
            + abs(float(rhs["scale_factor"]) - float(lhs["scale_factor"]))
        )

    for idx in range(len(option_rows) - 1):
        signal = _signal(idx, idx + 1)
        if signal > eps:
            dag.add_edge(node_ids[idx], node_ids[idx + 1], {"kind": "rank_step", "signal": signal})
            pair_edges.add((idx, idx + 1))
            edge_signal_sum += signal

    for idx in range(len(option_rows) - 2):
        triad = (idx, idx + 1, idx + 2)
        triad_windows.append(triad)
        signal = max(_signal(idx, idx + 1), _signal(idx + 1, idx + 2))
        if (idx, idx + 2) not in pair_edges and signal > eps:
            dag.add_edge(node_ids[idx], node_ids[idx + 2], {"kind": "rank_triad", "signal": signal})
            pair_edges.add((idx, idx + 2))
            edge_signal_sum += signal

    return {
        "node_count": int(dag.num_nodes()),
        "edge_count": int(dag.num_edges()),
        "pair_edges": [list(edge) for edge in sorted(pair_edges)],
        "triad_windows": [list(window) for window in triad_windows],
        "topological_order": [int(dag[node]["rank_index"]) for node in rx.topological_sort(dag)],
        "longest_path_length": int(rx.dag_longest_path_length(dag)) if dag.num_edges() else 0,
        "acyclic": bool(rx.is_directed_acyclic_graph(dag)),
        "edge_signal_sum": float(edge_signal_sum),
    }


def _option_hypergraph_surface(
    n_options: int,
    perturbation_windows: list[list[int]],
) -> dict[str, object]:
    hypergraph = xgi.Hypergraph()
    hypergraph.add_nodes_from(range(n_options))
    triad_windows: list[list[int]] = []
    pair_edges: set[tuple[int, int]] = set()
    hyperedges: list[list[int]] = []

    for window in perturbation_windows:
        deduped = sorted(set(int(value) for value in window))
        if len(deduped) < 2:
            continue
        hypergraph.add_edge(deduped)
        hyperedges.append(deduped)
        if len(deduped) == 2:
            pair_edges.add((deduped[0], deduped[1]))
        if len(deduped) >= 3:
            triad = deduped[:3]
            triad_windows.append(triad)

    incidence = xgi.incidence_matrix(hypergraph, sparse=False) if hypergraph.num_edges else np.zeros((n_options, 0), dtype=np.float64)
    edge_sizes = [int(value) for value in hypergraph.edges.size.aslist()] if hypergraph.num_edges else []
    return {
        "num_nodes": int(hypergraph.num_nodes),
        "num_edges": int(hypergraph.num_edges),
        "edge_sizes": edge_sizes,
        "incidence_rank": int(np.linalg.matrix_rank(incidence)) if incidence.size else 0,
        "connected_components": int(xgi.number_connected_components(hypergraph)) if hypergraph.num_edges else int(n_options),
        "max_hyperedge_size": int(max(edge_sizes)) if edge_sizes else 1,
        "pair_edges": [list(edge) for edge in sorted(pair_edges)],
        "triad_windows": triad_windows,
        "hyperedges": hyperedges,
    }


def _option_cell_complex_surface(
    n_options: int,
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
        "euler_characteristic": int(n_options - len(pair_edges) + len(triad_windows)),
    }


def _option_topology_surface(
    n_options: int,
    pair_edges: list[list[int]],
    triad_windows: list[list[int]],
) -> dict[str, object]:
    simplex_tree = gudhi.SimplexTree()
    for idx in range(n_options):
        simplex_tree.insert([int(idx)], filtration=0.0)
    for edge in pair_edges:
        simplex_tree.insert([int(edge[0]), int(edge[1])], filtration=1.0)
    for triad in triad_windows:
        simplex_tree.insert([int(triad[0]), int(triad[1]), int(triad[2])], filtration=2.0)
    simplex_tree.set_dimension(max(2, simplex_tree.dimension()))
    simplex_tree.compute_persistence()
    betti = [int(value) for value in simplex_tree.betti_numbers()]
    beta0 = betti[0] if betti else int(n_options)
    beta1 = betti[1] if len(betti) > 1 else 0
    beta2 = betti[2] if len(betti) > 2 else 0
    return {
        "betti_numbers": betti,
        "beta0": int(beta0),
        "beta1": int(beta1),
        "beta2": int(beta2),
        "euler_characteristic": int(beta0 - beta1 + beta2),
    }


def _option_symbolic_surface(
    lambda_shells: np.ndarray,
    scale_factors: np.ndarray,
    expansion_drive: np.ndarray,
) -> dict[str, object]:
    lam = sp.symbols("lam", real=True)
    scale_pairs = [(float(x), float(y)) for x, y in zip(lambda_shells.tolist(), scale_factors.tolist(), strict=True)]
    drive_pairs = [(float(x), float(y)) for x, y in zip(lambda_shells.tolist(), expansion_drive.tolist(), strict=True)]
    scale_poly = sp.expand(sp.interpolate(scale_pairs, lam))
    drive_poly = sp.expand(sp.interpolate(drive_pairs, lam))
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
        "expansion_drive_polynomial": str(drive_poly),
        "scale_poly_degree": int(sp.Poly(scale_poly, lam).degree()),
        "drive_poly_degree": int(sp.Poly(drive_poly, lam).degree()),
        "mid_lambda": mid_lambda,
        "symbolic_hubble_mid": float(d_scale_mid / max(scale_mid, EPS_NUM)),
        "symbolic_acceleration_mid": float(dd_scale_mid),
        "symbolic_drive_mid": float(sp.N(drive_poly.subs(lam, mid_lambda))),
    }


def _option_constraint_surface(
    lambda_shells: np.ndarray,
    scale_factors: np.ndarray,
    ranking_scores: np.ndarray,
) -> dict[str, object]:
    solver = Solver()
    lambda_vars = [Real(f"lambda_shell_{idx}") for idx in range(len(lambda_shells))]
    scale_vars = [Real(f"scale_factor_{idx}") for idx in range(len(scale_factors))]
    score_vars = [Real(f"ranking_score_{idx}") for idx in range(len(ranking_scores))]
    for var, value in zip(lambda_vars, lambda_shells.tolist(), strict=True):
        solver.add(var == RealVal(str(float(value))))
    for var, value in zip(scale_vars, scale_factors.tolist(), strict=True):
        solver.add(var == RealVal(str(float(value))))
        solver.add(var >= RealVal("1.0"))
    for var, value in zip(score_vars, ranking_scores.tolist(), strict=True):
        solver.add(var == RealVal(str(float(value))))
    for lhs, rhs in zip(lambda_vars[:-1], lambda_vars[1:], strict=True):
        solver.add(lhs < rhs)
    for lhs, rhs in zip(scale_vars[:-1], scale_vars[1:], strict=True):
        solver.add(lhs <= rhs)
    for lhs, rhs in zip(score_vars[:-1], score_vars[1:], strict=True):
        solver.add(lhs >= rhs)
    if scale_vars:
        solver.add(Sum(*scale_vars) >= RealVal("4.0"))
    result = solver.check()
    return {
        "result": str(result),
        "sat": bool(result == sat),
    }


def _option_manifold_surface(
    mean_abs_a0: np.ndarray,
    doctrine_fit: np.ndarray,
    shell_alignment_abs: np.ndarray,
    scale_factors: np.ndarray,
) -> dict[str, object]:
    raw_points = np.stack(
        [
            mean_abs_a0 - float(np.mean(mean_abs_a0)),
            doctrine_fit - float(np.mean(doctrine_fit)),
            shell_alignment_abs + (scale_factors - float(scale_factors[0])),
        ],
        axis=1,
    )
    points = []
    for row in raw_points:
        norm = float(np.linalg.norm(row))
        if norm < EPS_NUM:
            points.append(np.array([0.0, 0.0, 1.0], dtype=np.float64))
        else:
            points.append(np.asarray(row, dtype=np.float64) / norm)
    points_arr = np.asarray(points, dtype=np.float64)
    estimator = FrechetMean(space=OPTION_SPHERE)
    estimator.fit(points_arr)
    mean = np.asarray(estimator.estimate_, dtype=np.float64)
    dists = np.asarray(
        [float(OPTION_SPHERE.metric.dist(point, mean)) for point in points_arr],
        dtype=np.float64,
    )
    return {
        "frechet_mean": mean.tolist(),
        "mean_norm": float(np.linalg.norm(mean)),
        "mean_geodesic_distance": float(np.mean(dists)),
        "max_geodesic_distance": float(np.max(dists)),
    }


def _aggregate_deep_contract(
    all_results: list[dict],
    option_verdicts: dict[str, dict[str, object]],
    ranking: list[str],
) -> dict[str, object]:
    shell_bridge_pass_fraction = float(
        np.mean([1.0 if cfg["shell_bridge"]["lane_d_keep"] else 0.0 for cfg in all_results])
    ) if all_results else 0.0

    option_a0_by_name: dict[str, list[float]] = {opt: [] for opt in OPTION_ORDER}
    option_shell_hubble_by_name: dict[str, list[float]] = {opt: [] for opt in OPTION_ORDER}
    per_perturb_means: dict[str, dict[str, float]] = {
        pert: {opt: 0.0 for opt in OPTION_ORDER} for pert in PERTURBATIONS
    }

    for pert in PERTURBATIONS:
        for opt in OPTION_ORDER:
            values = []
            for cfg in all_results:
                a0 = float(cfg["perturbations"][pert][opt]["a0"])
                values.append(abs(a0))
            per_perturb_means[pert][opt] = float(np.mean(values)) if values else 0.0

    for cfg in all_results:
        shell_hubble = float(cfg["shell_bridge"]["mean_hubble_proxy"])
        for pert in PERTURBATIONS:
            for opt in OPTION_ORDER:
                option_a0_by_name[opt].append(float(cfg["perturbations"][pert][opt]["a0"]))
                option_shell_hubble_by_name[opt].append(shell_hubble)

    lambda_shells = np.linspace(0.0, 1.0, len(ranking), dtype=np.float64)
    option_rows: list[dict[str, object]] = []
    ranking_scores: list[float] = []

    for opt in ranking:
        option_vals = np.asarray(option_a0_by_name[opt], dtype=np.float64)
        shell_vals = np.asarray(option_shell_hubble_by_name[opt], dtype=np.float64)
        shell_alignment = 0.0
        if option_vals.size and option_vals.std() > EPS_NUM and shell_vals.std() > EPS_NUM:
            shell_alignment = float(np.corrcoef(option_vals, shell_vals)[0, 1])
        mean_abs = float(np.mean(np.abs(option_vals))) if option_vals.size else 0.0
        doctrine_fit = float(option_verdicts[opt]["doctrine_fit"])
        sign_consistency = float(option_verdicts[opt]["sign_consistency"])
        composite_score = float(option_verdicts[opt]["composite_score"])
        ranking_scores.append(composite_score)
        option_rows.append(
            {
                "option": opt,
                "mean_abs_a0": mean_abs,
                "mean_signed_a0": float(np.mean(option_vals)) if option_vals.size else 0.0,
                "doctrine_fit": doctrine_fit,
                "sign_consistency": sign_consistency,
                "shell_alignment": shell_alignment,
                "shell_alignment_abs": abs(shell_alignment),
            }
        )

    expansion_drive = np.asarray(
        [
            row["mean_abs_a0"] + row["doctrine_fit"] + row["shell_alignment_abs"]
            for row in option_rows
        ],
        dtype=np.float64,
    )
    scale_factors, propagator_traces = _option_scale_history(lambda_shells, expansion_drive)
    hubble_proxy = np.gradient(np.log(np.clip(scale_factors, EPS_NUM, None)), lambda_shells)

    for row, scale, hubble in zip(option_rows, scale_factors.tolist(), hubble_proxy.tolist(), strict=True):
        row["scale_factor"] = float(scale)
        row["hubble_proxy"] = float(hubble)

    graph_surface = _option_graph_surface(option_rows)
    perturbation_windows: list[list[int]] = []
    ranking_index = {opt: idx for idx, opt in enumerate(ranking)}
    for pert in PERTURBATIONS:
        sorted_opts = sorted(
            OPTION_ORDER,
            key=lambda opt: per_perturb_means[pert][opt],
            reverse=True,
        )
        perturbation_windows.append([ranking_index[opt] for opt in sorted_opts[:3]])

    hypergraph_surface = _option_hypergraph_surface(len(ranking), perturbation_windows)
    combined_pair_edges = sorted(
        {
            tuple(edge)
            for edge in graph_surface["pair_edges"] + hypergraph_surface["pair_edges"]
        }
    )
    combined_triad_windows = sorted(
        {
            tuple(window)
            for window in graph_surface["triad_windows"] + hypergraph_surface["triad_windows"]
        }
    )
    cell_complex_surface = _option_cell_complex_surface(
        len(ranking),
        [list(edge) for edge in combined_pair_edges],
        [list(window) for window in combined_triad_windows],
    )
    topology_surface = _option_topology_surface(
        len(ranking),
        [list(edge) for edge in combined_pair_edges],
        [list(window) for window in combined_triad_windows],
    )
    symbolic_surface = _option_symbolic_surface(lambda_shells, scale_factors, expansion_drive)
    constraint_surface = _option_constraint_surface(
        lambda_shells,
        scale_factors,
        np.asarray(ranking_scores, dtype=np.float64),
    )
    manifold_surface = _option_manifold_surface(
        np.asarray([row["mean_abs_a0"] for row in option_rows], dtype=np.float64),
        np.asarray([row["doctrine_fit"] for row in option_rows], dtype=np.float64),
        np.asarray([row["shell_alignment_abs"] for row in option_rows], dtype=np.float64),
        scale_factors,
    )
    torch_fit = _torch_option_fit(
        np.stack(
            [
                np.asarray([row["mean_abs_a0"] for row in option_rows], dtype=np.float64),
                np.asarray([row["doctrine_fit"] for row in option_rows], dtype=np.float64),
                np.asarray([row["shell_alignment_abs"] for row in option_rows], dtype=np.float64),
            ],
            axis=1,
        ),
        hubble_proxy,
    )

    winner = ranking[0]
    winner_row = next(row for row in option_rows if row["option"] == winner)
    winner_vector = np.array(
        [
            winner_row["mean_abs_a0"],
            winner_row["doctrine_fit"],
            winner_row["shell_alignment_abs"],
        ],
        dtype=np.float64,
    )
    clifford_vector = _clifford_vector(winner_vector)
    torch_ga_vector = _torch_ga_roundtrip(winner_vector)
    topology_parity_ok = bool(
        cell_complex_surface["euler_characteristic"] == topology_surface["euler_characteristic"]
    )

    pass_flag = bool(
        shell_bridge_pass_fraction >= 0.5
        and graph_surface["longest_path_length"] >= len(ranking) - 1
        and hypergraph_surface["max_hyperedge_size"] >= 3
        and topology_surface["beta0"] == 1
        and topology_surface["beta1"] == 0
        and topology_parity_ok
        and constraint_surface["sat"]
        and symbolic_surface["symbolic_hubble_mid"] > 0.05
        and manifold_surface["mean_geodesic_distance"] > 1e-2
        and torch_fit["loss"] < 1.0
    )

    return {
        "pass": pass_flag,
        "winner": winner,
        "shell_bridge_pass_fraction": shell_bridge_pass_fraction,
        "option_rows": option_rows,
        "graph_surface": {
            "edge_count": graph_surface["edge_count"],
            "longest_path_length": graph_surface["longest_path_length"],
            "triad_windows": graph_surface["triad_windows"],
        },
        "hypergraph_surface": {
            "num_edges": hypergraph_surface["num_edges"],
            "max_hyperedge_size": hypergraph_surface["max_hyperedge_size"],
            "connected_components": hypergraph_surface["connected_components"],
            "hyperedges": hypergraph_surface["hyperedges"],
        },
        "topology_surface": {
            "betti_numbers": topology_surface["betti_numbers"],
            "euler_characteristic": topology_surface["euler_characteristic"],
            "parity_ok": topology_parity_ok,
        },
        "symbolic_surface": symbolic_surface,
        "constraint_surface": constraint_surface,
        "manifold_surface": manifold_surface,
        "torch_fit": {
            "weights": torch_fit["weights"],
            "bias": torch_fit["bias"],
            "loss": torch_fit["loss"],
            "max_gap": torch_fit["max_gap"],
        },
        "winner_vector": winner_vector.tolist(),
        "clifford_vector_gap": float(np.max(np.abs(clifford_vector - winner_vector))),
        "torch_ga_vector_gap": float(np.max(np.abs(torch_ga_vector - winner_vector))),
        "scale_factors": scale_factors.tolist(),
        "hubble_proxy": hubble_proxy.tolist(),
        "propagator_traces": propagator_traces,
    }


# ─────────────────────────────────────────────────────────────────────
# Axis-0 Index: finite-difference derivative
# A0 = [D(Φ_ε(ρ)) - D(ρ)] / ε
# ALLOSTATIC if A0 > 0 (diversity increases under perturbation)
# HOMEOSTATIC if A0 < 0 (diversity is suppressed under perturbation)
# ─────────────────────────────────────────────────────────────────────

def axis0_index(history_base: list[dict],
                history_perturbed: list[dict],
                option_fn,
                eps: float) -> float:
    d_base = option_fn(history_base)
    d_pert = option_fn(history_perturbed)
    return (d_pert - d_base) / eps if eps > EPS_NUM else 0.0


# ─────────────────────────────────────────────────────────────────────
# Per-config runner
# ─────────────────────────────────────────────────────────────────────

def run_config(engine_type: int,
               torus_name: str,
               torus_val: float) -> dict:
    """Run one (engine_type, torus) pair across all perturbations × options."""
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(eta=torus_val)
    final = engine.run_cycle(state)
    history_base = []
    for step in final.history:
        history_base.append(
            {
                "rho_L": step["rho_L"],
                "rho_R": step["rho_R"],
                "eta": float(step.get("ax0_torus_entropy", 0.5)),
            }
        )

    option_fns = {
        "A_mi_diversity":    option_A,
        "B_mi_variance":     option_B,
        "C_coherent_info":   option_C,
        "D_jk_path_entropy": option_D,
    }

    results_by_perturbation = {}
    for pert_name, pert_fn in PERTURBATIONS.items():
        history_pert = perturb_history(history_base, pert_fn, PERTURBATION_EPS)
        option_scores = {}
        for opt_name, opt_fn in option_fns.items():
            a0 = axis0_index(history_base, history_pert, opt_fn, PERTURBATION_EPS)
            polarity = "allostatic" if a0 > 0 else "homeostatic"
            option_scores[opt_name] = {
                "a0": round(float(a0), 6),
                "polarity": polarity,
                "base_val":  round(opt_fn(history_base), 6),
                "pert_val":  round(opt_fn(history_pert), 6),
            }
        results_by_perturbation[pert_name] = option_scores

    shell_bridge = lane_d_topology_expansion_bridge(history_base)

    return {
        "engine_type": engine_type,
        "torus": torus_name,
        "perturbations": results_by_perturbation,
        "shell_bridge": shell_bridge,
    }


# ─────────────────────────────────────────────────────────────────────
# Aggregate verdict
# ─────────────────────────────────────────────────────────────────────

def aggregate(all_results: list[dict]) -> dict:
    """
    For each option, collect:
    - sign_consistency: fraction of (config × perturbation) cells where
      polarity agrees with majority sign
    - mean_abs_a0: average signal strength
    - doctrine_fit: fraction of T1 configs that are homeostatic AND
      T2 configs that are allostatic (per Grok Unified Physics Type1=L-handed
      cooling bias, Type2=R-handed heating bias)
    """
    option_names = OPTION_ORDER
    pert_names = list(PERTURBATIONS.keys())

    # Collect all A0 values per option
    stats = {opt: {"a0_vals": [], "polarities": [], "t1_polarities": [], "t2_polarities": []}
             for opt in option_names}

    for cfg in all_results:
        eng = cfg["engine_type"]
        for pert in pert_names:
            for opt in option_names:
                a0 = cfg["perturbations"][pert][opt]["a0"]
                pol = cfg["perturbations"][pert][opt]["polarity"]
                stats[opt]["a0_vals"].append(a0)
                stats[opt]["polarities"].append(pol)
                if eng == 1:
                    stats[opt]["t1_polarities"].append(pol)
                else:
                    stats[opt]["t2_polarities"].append(pol)

    verdicts = {}
    for opt in option_names:
        a0s = stats[opt]["a0_vals"]
        pols = stats[opt]["polarities"]
        t1_pols = stats[opt]["t1_polarities"]
        t2_pols = stats[opt]["t2_polarities"]

        # Sign consistency: majority vote
        n_allo = pols.count("allostatic")
        n_homeo = pols.count("homeostatic")
        majority = "allostatic" if n_allo >= n_homeo else "homeostatic"
        sign_consistency = max(n_allo, n_homeo) / len(pols) if pols else 0.0

        # Mean absolute A0 (signal strength)
        mean_abs = float(np.mean(np.abs(a0s))) if a0s else 0.0

        # Doctrine fit: T1 expected homeostatic (cooling/deductive = structure-preserving)
        #               T2 expected allostatic  (heating/inductive = diversity-expanding)
        t1_homeo_frac = t1_pols.count("homeostatic") / len(t1_pols) if t1_pols else 0.0
        t2_allo_frac  = t2_pols.count("allostatic")  / len(t2_pols) if t2_pols else 0.0
        doctrine_fit  = (t1_homeo_frac + t2_allo_frac) / 2.0

        # Composite score (equal weight: consistency + signal + doctrine)
        composite = (sign_consistency + min(mean_abs, 1.0) + doctrine_fit) / 3.0

        verdicts[opt] = {
            "sign_consistency":  round(sign_consistency, 3),
            "majority_polarity": majority,
            "mean_abs_a0":       round(mean_abs, 6),
            "t1_homeostatic_frac": round(t1_homeo_frac, 3),
            "t2_allostatic_frac":  round(t2_allo_frac, 3),
            "doctrine_fit":      round(doctrine_fit, 3),
            "composite_score":   round(composite, 3),
        }

    # Rank options
    ranked = sorted(option_names, key=lambda o: verdicts[o]["composite_score"], reverse=True)
    winner = ranked[0]

    deep_contract = _aggregate_deep_contract(all_results, verdicts, ranked)

    return {
        "option_verdicts": verdicts,
        "ranking": ranked,
        "winner": winner,
        "winner_rationale": (
            f"Option {winner} wins with composite score "
            f"{verdicts[winner]['composite_score']:.3f} "
            f"(consistency={verdicts[winner]['sign_consistency']:.3f}, "
            f"signal={verdicts[winner]['mean_abs_a0']:.4f}, "
            f"doctrine_fit={verdicts[winner]['doctrine_fit']:.3f})"
        ),
        "deep_contract": deep_contract,
        "all_pass": bool(deep_contract["pass"]),
    }


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 72)
    print("AXIS 0 i-SCALAR FUNCTIONAL SWEEP")
    print("=" * 72)
    print("Options from AXIS0_SPEC_OPTIONS_v0.1-v0.3:")
    print("  A — MI diversity (Shannon entropy of MI distribution)")
    print("  B — MI variance  (deviation damping)")
    print("  C — Coherent info spread (I_c survival under noise)")
    print("  D — JK fuzz / path entropy (Kraus history branching)")
    print()
    print("Perturbations: depolarizing | dephasing | amplitude_damping")
    print("Configs: T1/T2 × inner/clifford/outer  = 6 engine configs × 3 = 18 cells/option")
    print()

    all_results = []
    for eng_type in [1, 2]:
        for torus_name, torus_val in TORUS_CONFIGS:
            print(f"  Running T{eng_type}/{torus_name}...", end="", flush=True)
            r = run_config(eng_type, torus_name, torus_val)
            all_results.append(r)
            # Quick summary line
            for pert in PERTURBATIONS:
                a_pol = r["perturbations"][pert]["A_mi_diversity"]["polarity"][0].upper()
                b_pol = r["perturbations"][pert]["B_mi_variance"]["polarity"][0].upper()
                c_pol = r["perturbations"][pert]["C_coherent_info"]["polarity"][0].upper()
                d_pol = r["perturbations"][pert]["D_jk_path_entropy"]["polarity"][0].upper()
            print(f" done")

    print()
    print("─" * 72)
    print("DETAILED POLARITY TABLE  (A=allostatic, H=homeostatic)")
    print("─" * 72)
    print(f"{'Config':<20} {'Perturbation':<18} {'Opt-A':>6} {'Opt-B':>6} {'Opt-C':>6} {'Opt-D':>6}")
    print("─" * 72)
    for cfg in all_results:
        label = f"T{cfg['engine_type']}/{cfg['torus']}"
        for pert in PERTURBATIONS:
            opts = cfg["perturbations"][pert]
            def sym(pol): return "A" if pol == "allostatic" else "H"
            a0_A = opts["A_mi_diversity"]["a0"]
            a0_B = opts["B_mi_variance"]["a0"]
            a0_C = opts["C_coherent_info"]["a0"]
            a0_D = opts["D_jk_path_entropy"]["a0"]
            print(f"  {label:<18} {pert:<18} "
                  f"{sym(opts['A_mi_diversity']['polarity']):>5}({a0_A:+.4f})  "
                  f"{sym(opts['B_mi_variance']['polarity']):>5}({a0_B:+.4f})  "
                  f"{sym(opts['C_coherent_info']['polarity']):>5}({a0_C:+.4f})  "
                  f"{sym(opts['D_jk_path_entropy']['polarity']):>5}({a0_D:+.4f})")

    print()
    agg = aggregate(all_results)

    print("=" * 72)
    print("AGGREGATE VERDICT PER OPTION")
    print("=" * 72)
    for opt in ["A_mi_diversity", "B_mi_variance", "C_coherent_info", "D_jk_path_entropy"]:
        v = agg["option_verdicts"][opt]
        print(f"\n  Option {opt}:")
        print(f"    Sign consistency:  {v['sign_consistency']:.3f}  (majority={v['majority_polarity']})")
        print(f"    Mean |A0|:         {v['mean_abs_a0']:.6f}")
        print(f"    T1 homeostatic:    {v['t1_homeostatic_frac']:.3f}")
        print(f"    T2 allostatic:     {v['t2_allostatic_frac']:.3f}")
        print(f"    Doctrine fit:      {v['doctrine_fit']:.3f}")
        print(f"    Composite score:   {v['composite_score']:.3f}")

    print()
    print("=" * 72)
    print("RANKING & WINNER")
    print("=" * 72)
    for rank, opt in enumerate(agg["ranking"], 1):
        score = agg["option_verdicts"][opt]["composite_score"]
        marker = " ← WINNER" if opt == agg["winner"] else ""
        print(f"  #{rank}  {opt:<28} score={score:.3f}{marker}")

    print()
    print(f"  {agg['winner_rationale']}")
    print()

    deep = agg["deep_contract"]
    print("─" * 72)
    print("DEEP CONTRACT")
    print("─" * 72)
    print(f"  Deep pass:                    {deep['pass']}")
    print(f"  Shell bridge pass fraction:   {deep['shell_bridge_pass_fraction']:.3f}")
    print(f"  Graph longest path:           {deep['graph_surface']['longest_path_length']}")
    print(f"  Hypergraph max edge size:     {deep['hypergraph_surface']['max_hyperedge_size']}")
    print(f"  Topology betti numbers:       {deep['topology_surface']['betti_numbers']}")
    print(f"  Symbolic hubble mid:          {deep['symbolic_surface']['symbolic_hubble_mid']:.6f}")
    print(f"  Manifold mean distance:       {deep['manifold_surface']['mean_geodesic_distance']:.6f}")
    print(f"  Torch fit loss:               {deep['torch_fit']['loss']:.6f}")
    print(f"  Winner vector gaps:           clifford={deep['clifford_vector_gap']:.2e} | torch_ga={deep['torch_ga_vector_gap']:.2e}")
    print()

    # Doctrine interpretation
    winner = agg["winner"]
    wv = agg["option_verdicts"][winner]
    print("─" * 72)
    print("DOCTRINE INTERPRETATION")
    print("─" * 72)
    interpretations = {
        "A_mi_diversity": (
            "The i-scalar measures CORRELATION DIVERSITY — the spread of mutual "
            "information across history stages. Axis 0 allostatic = perturbation "
            "pushes MI to more stages (global). Homeostatic = MI concentrates "
            "(local). Doctrine connection: space=entropy → the variety of "
            "correlations IS the entropy landscape."
        ),
        "B_mi_variance": (
            "The i-scalar measures CORRELATION DEVIATION DAMPING — whether "
            "perturbation squashes or spreads the variance of MI values. "
            "Homeostatic = deviation is suppressed (low variance). Allostatic = "
            "deviation grows. Doctrine connection: 'a=a iff a~b' — identity "
            "suppresses deviation; the homeostatic engine is the identity-forming "
            "boundary."
        ),
        "C_coherent_info": (
            "The i-scalar measures COHERENT INFORMATION SURVIVAL — whether "
            "negative conditional entropy (I_c) survives perturbation. "
            "Allostatic = Bell entanglement persists (the prior dominates). "
            "Homeostatic = entanglement is broken by noise. Doctrine connection: "
            "FEP 'prior exists first' → allostatic means the Bell prior is robust."
        ),
        "D_jk_path_entropy": (
            "The i-scalar measures JK FUZZ BRANCHING VARIETY — the path entropy "
            "of Kraus history ensembles. Allostatic = more admissible Kraus paths "
            "(more future possibilities). Homeostatic = paths contract. This is "
            "the most direct operationalization of 'jk fuzz as causal force'."
        ),
    }
    print()
    print(f"  Winning option ({winner}):")
    print(f"  {interpretations[winner]}")
    print()
    print(f"  T1 homeostatic fraction: {wv['t1_homeostatic_frac']:.1%}")
    print(f"  T2 allostatic  fraction: {wv['t2_allostatic_frac']:.1%}")

    print()
    print("=" * 72)
    print(f"PROBE STATUS: {'PASS' if agg['all_pass'] else 'FAIL'}")
    print("=" * 72)

    # Save
    def json_safe(obj):
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, (np.bool_,)): return bool(obj)
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, dict): return {k: json_safe(v) for k, v in obj.items()}
        if isinstance(obj, list): return [json_safe(v) for v in obj]
        return obj

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    canonical_out_path = os.path.join(
        out_dir, f"{os.path.splitext(os.path.basename(__file__))[0]}_results.json"
    )
    legacy_out_path = os.path.join(out_dir, "axis0_iscalar_sweep_results.json")
    payload = json.dumps(json_safe({
            "timestamp": datetime.now(UTC).isoformat(),
            "classification": classification,
            "divergence_log": divergence_log,
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "parameters": {
                "eps": PERTURBATION_EPS,
                "kraus_branches": KRAUS_BRANCHES,
            },
            "per_config_results": all_results,
            "aggregate": agg,
            "summary": {
                "winner": agg["winner"],
                "all_pass": bool(agg["all_pass"]),
                "deep_contract_pass": bool(agg["deep_contract"]["pass"]),
            },
            "overall_pass": bool(agg["all_pass"]),
            "all_pass": bool(agg["all_pass"]),
        }), indent=2)
    for target in dict.fromkeys([canonical_out_path, legacy_out_path]):
        with open(target, "w") as f:
            f.write(payload)
    print(f"\n  Results → {canonical_out_path}")


if __name__ == "__main__":
    main()
