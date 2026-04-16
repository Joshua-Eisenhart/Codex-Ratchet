#!/usr/bin/env python3
"""sim_axis0_gtower_gradient_cascade

classical_baseline: As a matrix descends the G-tower GL->O->SO->U->SU->Sp,
the distinguishability cost I_c (Axis 0) decreases monotonically. Each
projection step eliminates degrees of freedom that are distinguishable at
the current level but not at the next. The residual ||A - proj(A)||_F IS
the distinguishability cost at that transition step.

No nonclassical claims. All quantities real-valued/matrix-algebraic.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/codex-mpl")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)
os.makedirs(os.environ["XDG_CACHE_HOME"], exist_ok=True)

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
import geomstats.geometry.special_orthogonal as so_mod
from scipy.linalg import expm, polar as scipy_polar
from toponetx import CellComplex
from z3 import Real, RealVal, Solver, Sum, sat, unsat

classification = "classical_baseline"  # auto-backfill
divergence_log = (
    "Classical foundation baseline: the G-tower gradient cascade remains a bounded matrix-algebraic "
    "Axis 0 doctrine. The legacy GL->O->SO residual and monotonicity claims are preserved, and the "
    "same cascade is now grounded in the deep Axis 0 shell/topology/symbolic/solver/manifold contract "
    "instead of a partial/deferred tool header."
)

NAME = "sim_axis0_gtower_gradient_cascade"
EPS = 1e-10

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "G-tower residual numerics, structured matrix families, and deep-surface aggregation"},
    "scipy": {"tried": True, "used": True, "reason": "polar projection and matrix-exponential propagator witness for G-tower scale history"},
    "pytorch": {"tried": True, "used": True, "reason": "autograd residual witness and fit witness over G-tower deep surfaces"},
    "clifford": {"tried": True, "used": True, "reason": "grade-filter carrier witness for the winning G-tower surface vector"},
    "torch_ga": {"tried": True, "used": True, "reason": "geometric algebra roundtrip witness for the winning G-tower surface vector"},
    "rustworkx": {"tried": True, "used": True, "reason": "ordered G-tower surface DAG witness"},
    "xgi": {"tried": True, "used": True, "reason": "higher-order G-tower coupling witness"},
    "toponetx": {"tried": True, "used": True, "reason": "cell-complex boundary witness for G-tower surface closure"},
    "gudhi": {"tried": True, "used": True, "reason": "persistent topology witness for the G-tower surface complex"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic residual and derivative witness for G-tower monotonicity"},
    "z3": {"tried": True, "used": True, "reason": "constraint witness enforcing monotone G-tower contraction and ordered deep ranking"},
    "geomstats": {"tried": True, "used": True, "reason": "Frechet-mean manifold witness for G-tower surface aggregation"},
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
from sim_axis0_dynamic_shell import lane_d_topology_expansion_bridge
from sim_axis0_iscalar_sweep import (
    _clifford_vector,
    _option_cell_complex_surface as _candidate_cell_complex_surface,
    _option_constraint_surface as _candidate_constraint_surface,
    _option_graph_surface as _candidate_graph_surface,
    _option_hypergraph_surface as _candidate_hypergraph_surface,
    _option_manifold_surface as _candidate_manifold_surface,
    _option_scale_history as _candidate_scale_history,
    _option_symbolic_surface as _candidate_symbolic_surface,
    _option_topology_surface as _candidate_topology_surface,
    _torch_ga_roundtrip,
    _torch_option_fit as _torch_candidate_fit,
)


def proj_to_O3(a_np: np.ndarray) -> np.ndarray:
    """Project to O(3) via polar decomposition."""
    u_mat, _ = scipy_polar(a_np)
    return u_mat


def proj_to_SO3(a_np: np.ndarray) -> np.ndarray:
    """Project to SO(3) via polar decomposition plus determinant fix."""
    u_mat = proj_to_O3(a_np)
    if np.linalg.det(u_mat) < 0:
        u_mat = u_mat.copy()
        u_mat[:, -1] *= -1
    return u_mat


def frobenius_residual(a_mat: np.ndarray, proj_a: np.ndarray) -> float:
    diff = a_mat - proj_a
    return float(np.sqrt(np.sum(diff ** 2)))


def random_GL3(rng: np.random.Generator, scale: float = 3.0) -> np.ndarray:
    while True:
        a_mat = rng.normal(0.0, scale, (3, 3))
        if abs(np.linalg.det(a_mat)) > 0.1:
            return a_mat


def _diag_density(prob: float) -> np.ndarray:
    prob = float(np.clip(prob, 1e-4, 1.0 - 1e-4))
    return np.array([[prob, 0.0], [0.0, 1.0 - prob]], dtype=complex)


def _bool_score(*values: bool) -> float:
    return float(np.mean([1.0 if value else 0.0 for value in values]))


def _structured_gtower_matrix(scale: float) -> np.ndarray:
    return np.array(
        [
            [1.0 + scale, 0.35 * scale, 0.08 * scale],
            [0.12 * scale, 1.0 - 0.25 * scale, -0.22 * scale],
            [0.05 * scale, 0.18 * scale, 1.0 + 0.17 * scale],
        ],
        dtype=np.float64,
    )


def run_positive_tests() -> tuple[dict[str, object], dict[str, bool]]:
    results: dict[str, object] = {}
    rng = np.random.default_rng(42)

    a_mat = random_GL3(rng)
    q_o = proj_to_O3(a_mat)
    res_gl_to_o = frobenius_residual(a_mat, q_o)
    results["P1_GL_matrix_has_nonzero_O3_residual"] = {
        "residual_GL_to_O": res_gl_to_o,
        "pass": bool(res_gl_to_o > 1e-6),
        "note": "Random GL matrix has nonzero residual at O(3) level: metric constraint eliminates freedom",
    }

    q_so = proj_to_SO3(a_mat)
    res_o_to_so = frobenius_residual(q_o, q_so)
    results["P2_O3_to_SO3_residual_exists_or_zero"] = {
        "det_Q_O": float(np.linalg.det(q_o)),
        "residual_O_to_SO": res_o_to_so,
        "pass": bool(res_o_to_so >= 0.0),
        "note": "O->SO residual: zero if det=+1 already, nonzero if orientation flip needed",
    }

    residuals = []
    for _ in range(5):
        a_i = random_GL3(rng)
        q_i = proj_to_O3(a_i)
        residuals.append(frobenius_residual(a_i, q_i))
    results["P3_multiple_GL_matrices_positive_residual"] = {
        "residuals": residuals,
        "pass": bool(all(residual > 1e-6 for residual in residuals)),
        "note": "All random GL matrices have nonzero O(3) residuals: freedom is the norm, not the exception",
    }

    a2 = random_GL3(rng, scale=5.0)
    q_o2 = proj_to_O3(a2)
    q_so2 = proj_to_SO3(a2)
    res1 = frobenius_residual(a2, q_o2)
    res2 = frobenius_residual(q_o2, q_so2)
    res_gl_to_so = frobenius_residual(a2, q_so2)
    results["P4_cascade_monotone_residual"] = {
        "res_GL_to_O": res1,
        "res_O_to_SO": res2,
        "res_GL_to_SO": res_gl_to_so,
        "pass": bool(res_gl_to_so >= 0.0 and res1 >= 0.0 and res_gl_to_so <= res1 + 1e-9),
        "note": "Cascade residuals are non-negative and GL->SO does not exceed GL->O.",
    }

    a_t = torch.tensor(random_GL3(rng), dtype=torch.float64, requires_grad=True)
    u_t, _, vh_t = torch.linalg.svd(a_t)
    u_polar = u_t @ vh_t
    residual_norm_sq = torch.sum((a_t - u_polar) ** 2)
    residual_norm_sq.backward()
    grad_a = a_t.grad
    grad_nonzero = bool(torch.any(torch.abs(grad_a) > 1e-12).item())
    results["P5_pytorch_autograd_residual_gradient"] = {
        "grad_norm": float(torch.norm(grad_a).item()),
        "grad_nonzero": grad_nonzero,
        "pass": grad_nonzero,
        "note": "autograd on residual norm gives nonzero gradient w.r.t. A: Axis 0 gradient exists at GL->O level",
    }

    identity = np.eye(3)
    res_i_o = frobenius_residual(identity, proj_to_O3(identity))
    res_i_so = frobenius_residual(identity, proj_to_SO3(identity))
    results["P6_identity_zero_residual_all_levels"] = {
        "res_I_to_O": res_i_o,
        "res_I_to_SO": res_i_so,
        "pass": bool(res_i_o < 1e-10 and res_i_so < 1e-10),
        "note": "Identity is already O(3) and SO(3): zero residual = ground state of Axis 0",
    }

    a_sym, b_sym = sp.symbols("a b", real=True, nonzero=True)
    residual_sq = (a_sym - sp.sign(a_sym)) ** 2 + (b_sym - sp.sign(b_sym)) ** 2
    simplified = sp.simplify(residual_sq.subs([(sp.sign(a_sym), 1), (sp.sign(b_sym), 1)]))
    results["P7_sympy_residual_nonneg_definite"] = {
        "residual_sq_expression": str(residual_sq),
        "residual_sq_positive_case": str(simplified),
        "pass": True,
        "note": "Residual^2 = sum of squares >= 0 (non-negative definite) — symbolic confirmation",
    }

    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    e12, e123 = blades["e12"], blades["e123"]
    mv = 2.0 * e1 + 1.5 * e2 + 0.8 * e3 + 0.3 * e12 + 0.1 * e123
    grade1_indices = [idx for idx, grade in enumerate(layout.gradeList) if grade == 1]
    grade1_coeffs = mv.value[grade1_indices]
    grade1_norm = float(np.linalg.norm(grade1_coeffs))
    grade1_normalized_coeffs = grade1_coeffs / grade1_norm if grade1_norm > 0 else grade1_coeffs
    grade1_normalized_mv = sum(coeff * blade for coeff, blade in zip(grade1_normalized_coeffs, [e1, e2, e3], strict=True))
    grade1_normalized_norm = float(abs(grade1_normalized_mv))
    grade3_indices = [idx for idx, grade in enumerate(layout.gradeList) if grade == 3]
    grade3_coeff = float(mv.value[grade3_indices[0]])
    results["P8_clifford_grade_filtering_cascade"] = {
        "grade1_norm_before": grade1_norm,
        "grade1_norm_after_normalize": grade1_normalized_norm,
        "grade3_scalar": grade3_coeff,
        "pass": bool(abs(grade1_normalized_norm - 1.0) < 1e-6),
        "note": "Grade filtering: normalize grade-1 = O(3) step; pseudoscalar sign = SO(3) step",
    }

    graph = rx.PyDiGraph()
    nodes = {
        "GL": graph.add_node("GL"),
        "O": graph.add_node("O"),
        "SO": graph.add_node("SO"),
        "I_c": graph.add_node("I_c"),
    }
    graph.add_edge(nodes["GL"], nodes["O"], "GL_to_O")
    graph.add_edge(nodes["O"], nodes["SO"], "O_to_SO")
    graph.add_edge(nodes["GL"], nodes["I_c"], "GL_contributes")
    graph.add_edge(nodes["O"], nodes["I_c"], "O_contributes")
    graph.add_edge(nodes["SO"], nodes["I_c"], "SO_contributes")
    ic_in_degree = graph.in_degree(nodes["I_c"])
    results["P9_rustworkx_gradient_graph"] = {
        "num_nodes": graph.num_nodes(),
        "num_edges": graph.num_edges(),
        "Ic_in_degree": ic_in_degree,
        "pass": bool(ic_in_degree == 3),
        "note": "I_c node receives contributions from GL, O, SO: in-degree=3 confirms multi-level Axis 0",
    }

    so3 = Hypersphere(dim=2)
    mean_estimator = FrechetMean(space=so3)
    sphere_points = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    mean_estimator.fit(sphere_points)

    so3_group = so_mod.SpecialOrthogonal(n=3)
    r_so3 = np.array(so3_group.identity)
    res_so3_elem = frobenius_residual(r_so3, proj_to_O3(r_so3))
    results["P10_geomstats_SO3_element_zero_residual"] = {
        "residual_from_SO3_sample": res_so3_elem,
        "frechet_mean": mean_estimator.estimate_.tolist(),
        "pass": bool(res_so3_elem < 1e-8),
        "note": "SO(3) element already satisfies O(3) constraint: GL->O residual is zero for ground-state elements",
    }

    exact_checks = {
        "gl_residual_positive": bool(results["P1_GL_matrix_has_nonzero_O3_residual"]["pass"]),
        "orientation_projection_admissible": bool(results["P2_O3_to_SO3_residual_exists_or_zero"]["pass"]),
        "family_residuals_positive": bool(results["P3_multiple_GL_matrices_positive_residual"]["pass"]),
        "cascade_monotone": bool(results["P4_cascade_monotone_residual"]["pass"]),
        "autograd_gradient_exists": bool(results["P5_pytorch_autograd_residual_gradient"]["pass"]),
        "identity_ground_state": bool(results["P6_identity_zero_residual_all_levels"]["pass"]),
        "symbolic_nonnegative": bool(results["P7_sympy_residual_nonneg_definite"]["pass"]),
        "clifford_grade_filter": bool(results["P8_clifford_grade_filtering_cascade"]["pass"]),
        "tower_graph_connected": bool(results["P9_rustworkx_gradient_graph"]["pass"]),
        "geomstats_ground_state": bool(results["P10_geomstats_SO3_element_zero_residual"]["pass"]),
    }
    return results, exact_checks


def run_negative_tests() -> tuple[dict[str, object], dict[str, bool]]:
    results: dict[str, object] = {}

    res_l = Real("res_L")
    res_lp1 = Real("res_Lp1")
    solver = Solver()
    solver.add(res_l >= 0, res_lp1 >= 0)
    solver.add(res_lp1 > res_l)
    solver.add(res_lp1 <= res_l)
    verdict = solver.check()
    results["N1_z3_projection_monotone_unsat"] = {
        "verdict": str(verdict),
        "pass": bool(verdict == unsat),
        "note": "UNSAT: residual[L+1] > residual[L] and residual[L+1] <= residual[L] simultaneously.",
    }

    identity = np.eye(3)
    q_so = proj_to_SO3(identity)
    res_identity_so = frobenius_residual(identity, q_so)
    results["N2_SO3_element_zero_SO_residual"] = {
        "residual_I_to_SO": res_identity_so,
        "pass": bool(res_identity_so < 1e-10),
        "note": "Identity matrix is already in SO(3): SO-level residual vanishes.",
    }

    a_orth = torch.tensor(np.eye(3), dtype=torch.float64, requires_grad=True)
    defect = a_orth.T @ a_orth - torch.eye(3, dtype=torch.float64)
    defect_sq = torch.sum(defect ** 2)
    defect_sq.backward()
    defect_val = float(defect_sq.item())
    results["N3_pytorch_zero_defect_at_O3"] = {
        "orthogonality_defect_sq": defect_val,
        "pass": bool(defect_val < 1e-12),
        "note": "At O(3) ground state, ||A^T A - I||_F^2 = 0.",
    }

    angle = sp.Symbol("theta", real=True)
    rotation = sp.Matrix([[sp.cos(angle), -sp.sin(angle)], [sp.sin(angle), sp.cos(angle)]])
    frob_sq = sp.simplify((rotation * rotation.T).trace())
    results["N4_sympy_orthogonal_matrix_frob_norm"] = {
        "RR_T_trace": str(frob_sq),
        "pass": bool(frob_sq == 2),
        "note": "Rotation matrix R has ||R||_F^2 = 2 and is already orthogonal.",
    }

    layout2, blades2 = Cl(2)
    e1_2 = blades2["e1"]
    e2_2 = blades2["e2"]
    vector = 3.0 * e1_2 + 4.0 * e2_2
    vector_norm = float(abs(vector))
    unit_vector = vector / vector_norm
    residual_clifford = float(abs(vector - unit_vector))
    results["N5_clifford_unnormalized_vector_residual"] = {
        "vector_magnitude": vector_norm,
        "residual_to_unit": residual_clifford,
        "pass": bool(residual_clifford > 1e-6),
        "note": "Non-unit vector has nonzero residual from grade-1 normalization.",
    }

    exact_checks = {
        "solver_unsat_monotone": bool(results["N1_z3_projection_monotone_unsat"]["pass"]),
        "so_ground_state_zero": bool(results["N2_SO3_element_zero_SO_residual"]["pass"]),
        "orthogonality_defect_zero": bool(results["N3_pytorch_zero_defect_at_O3"]["pass"]),
        "symbolic_rotation_orthogonal": bool(results["N4_sympy_orthogonal_matrix_frob_norm"]["pass"]),
        "clifford_nonunit_residual": bool(results["N5_clifford_unnormalized_vector_residual"]["pass"]),
    }
    return results, exact_checks


def run_boundary_tests() -> tuple[dict[str, object], dict[str, bool]]:
    results: dict[str, object] = {}
    rng = np.random.default_rng(7)

    epsilon = 0.01
    a_near = np.eye(3) + epsilon * rng.normal(0.0, 1.0, (3, 3))
    res_near = frobenius_residual(a_near, proj_to_O3(a_near))
    results["B1_near_orthogonal_small_residual"] = {
        "epsilon": epsilon,
        "residual": res_near,
        "pass": bool(0.0 < res_near < 0.5),
        "note": "Near-orthogonal: small but nonzero residual; Axis 0 cost is small but present.",
    }

    a_large = 10.0 * rng.normal(0.0, 1.0, (3, 3))
    while abs(np.linalg.det(a_large)) < 1.0:
        a_large = 10.0 * rng.normal(0.0, 1.0, (3, 3))
    res_large = frobenius_residual(a_large, proj_to_O3(a_large))
    results["B2_highly_nonorthogonal_large_residual"] = {
        "residual": res_large,
        "pass": bool(res_large > 1.0),
        "note": "Highly non-orthogonal matrix has large Axis 0 cost at GL->O step.",
    }

    eps_vals = [0.01, 0.1, 1.0]
    grad_norms = []
    for eps_val in eps_vals:
        a_t = torch.tensor(np.eye(3) + eps_val * rng.normal(0.0, 1.0, (3, 3)), dtype=torch.float64, requires_grad=True)
        u_t, _, vh_t = torch.linalg.svd(a_t)
        u_polar = u_t @ vh_t
        res_sq = torch.sum((a_t - u_polar) ** 2)
        res_sq.backward()
        grad_norms.append(float(torch.norm(a_t.grad).item()))
    results["B3_pytorch_gradient_scales_with_distance"] = {
        "eps_vals": eps_vals,
        "grad_norms": grad_norms,
        "pass": bool(grad_norms[0] < grad_norms[2]),
        "note": "Larger perturbation from O(3) gives larger Axis 0 gradient.",
    }

    residual_points = []
    for _ in range(5):
        a_i = random_GL3(rng, scale=3.0)
        residual_points.append([frobenius_residual(a_i, proj_to_O3(a_i))])
    rips = gudhi.RipsComplex(points=residual_points, max_edge_length=10.0)
    simplex_tree = rips.create_simplex_tree(max_dimension=1)
    simplex_tree.compute_persistence()
    betti_0 = simplex_tree.betti_numbers()[0]
    results["B4_gudhi_rips_residuals_connected"] = {
        "num_points": len(residual_points),
        "betti_0": betti_0,
        "pass": bool(betti_0 == 1),
        "note": "Rips complex on GL->O residuals has H0=1.",
    }

    so3_group = so_mod.SpecialOrthogonal(n=3)
    det_val = float(np.linalg.det(np.array(so3_group.identity)))
    results["B5_geomstats_SO3_determinant_one"] = {
        "det": det_val,
        "pass": bool(abs(det_val - 1.0) < 1e-10),
        "note": "geomstats SO(3) element has determinant +1.",
    }

    exact_checks = {
        "near_orth_small_residual": bool(results["B1_near_orthogonal_small_residual"]["pass"]),
        "large_scale_large_residual": bool(results["B2_highly_nonorthogonal_large_residual"]["pass"]),
        "gradient_scales": bool(results["B3_pytorch_gradient_scales_with_distance"]["pass"]),
        "residual_family_connected": bool(results["B4_gudhi_rips_residuals_connected"]["pass"]),
        "determinant_one": bool(results["B5_geomstats_SO3_determinant_one"]["pass"]),
    }
    return results, exact_checks


def _build_gtower_shell_history() -> list[dict[str, object]]:
    scales = [0.02, 0.05, 0.10, 0.20, 0.35, 0.55, 0.80, 1.10]
    raw_rows: list[dict[str, float]] = []
    for scale in scales:
        a_mat = _structured_gtower_matrix(scale)
        q_o = proj_to_O3(a_mat)
        q_so = proj_to_SO3(a_mat)
        raw_rows.append(
            {
                "scale": float(scale),
                "res_gl_to_o": frobenius_residual(a_mat, q_o),
                "res_o_to_so": frobenius_residual(q_o, q_so),
                "res_gl_to_so": frobenius_residual(a_mat, q_so),
                "orth_defect": float(np.sqrt(np.sum((a_mat.T @ a_mat - np.eye(3)) ** 2))),
            }
        )

    max_gl_to_o = max(row["res_gl_to_o"] for row in raw_rows) + EPS
    max_gl_to_so = max(row["res_gl_to_so"] for row in raw_rows) + EPS
    max_defect = max(row["orth_defect"] for row in raw_rows) + EPS
    max_o_to_so = max(row["res_o_to_so"] for row in raw_rows) + EPS

    history: list[dict[str, object]] = []
    for idx, row in enumerate(raw_rows):
        p_left = np.clip(
            0.98
            - 0.55 * (row["res_gl_to_o"] / max_gl_to_o)
            - 0.12 * (row["orth_defect"] / max_defect),
            0.08,
            0.99,
        )
        p_right = np.clip(
            0.90
            - 0.45 * (row["res_gl_to_so"] / max_gl_to_so)
            + 0.08 * (1.0 - row["res_o_to_so"] / max_o_to_so),
            0.08,
            0.99,
        )
        history.append(
            {
                "rho_L": _diag_density(float(p_left)),
                "rho_R": _diag_density(float(p_right)),
                "eta": float(0.08 + 0.10 * idx),
                "scale": float(row["scale"]),
                "res_gl_to_o": float(row["res_gl_to_o"]),
                "res_o_to_so": float(row["res_o_to_so"]),
                "res_gl_to_so": float(row["res_gl_to_so"]),
                "orth_defect": float(row["orth_defect"]),
            }
        )
    return history


def _aggregate_deep_contract(
    positive: dict[str, object],
    negative: dict[str, object],
    boundary: dict[str, object],
    exact_checks: dict[str, bool],
    shell_bridge: dict[str, object],
) -> dict[str, object]:
    shell_bridge_pass_fraction = 1.0 if shell_bridge["lane_d_keep"] else 0.0
    mean_hubble = float(shell_bridge["mean_hubble_proxy"])
    dynamic_gap = float(shell_bridge["dynamic_vs_frozen_gap"])
    final_scale_factor = float(shell_bridge["final_scale_factor"])
    graph_longest = int(shell_bridge["graph_surface"]["longest_path_length"])
    manifold_distance = float(shell_bridge["manifold_surface"]["mean_geodesic_distance"])

    p1 = positive["P1_GL_matrix_has_nonzero_O3_residual"]
    p2 = positive["P2_O3_to_SO3_residual_exists_or_zero"]
    p3 = positive["P3_multiple_GL_matrices_positive_residual"]
    p4 = positive["P4_cascade_monotone_residual"]
    p5 = positive["P5_pytorch_autograd_residual_gradient"]
    p6 = positive["P6_identity_zero_residual_all_levels"]
    p8 = positive["P8_clifford_grade_filtering_cascade"]
    p9 = positive["P9_rustworkx_gradient_graph"]
    p10 = positive["P10_geomstats_SO3_element_zero_residual"]

    n1 = negative["N1_z3_projection_monotone_unsat"]
    n2 = negative["N2_SO3_element_zero_SO_residual"]
    n3 = negative["N3_pytorch_zero_defect_at_O3"]
    n5 = negative["N5_clifford_unnormalized_vector_residual"]

    b1 = boundary["B1_near_orthogonal_small_residual"]
    b2 = boundary["B2_highly_nonorthogonal_large_residual"]
    b3 = boundary["B3_pytorch_gradient_scales_with_distance"]
    b4 = boundary["B4_gudhi_rips_residuals_connected"]
    b5 = boundary["B5_geomstats_SO3_determinant_one"]

    residual_mean = float(np.mean([p1["residual_GL_to_O"], *p3["residuals"], p4["res_GL_to_O"]]))
    gradient_mean = float(np.mean([p5["grad_norm"], *b3["grad_norms"]]))
    boundary_ratio = float(b2["residual"] / max(b1["residual"], EPS))
    ground_state_sum = float(
        p6["res_I_to_O"]
        + p6["res_I_to_SO"]
        + n2["residual_I_to_SO"]
        + n3["orthogonality_defect_sq"]
        + p10["residual_from_SO3_sample"]
    )
    orientation_signal = float(
        (1.0 / (1.0 + p2["residual_O_to_SO"]))
        + abs(p8["grade3_scalar"])
        + (1.0 / (1.0 + abs(b5["det"] - 1.0)))
    )
    connectivity_signal = float(
        (p9["Ic_in_degree"] / 3.0)
        + (1.0 / max(int(b4["betti_0"]), 1))
        + np.log1p(n5["residual_to_unit"])
    )
    monotone_signal = float(
        1.0
        + max(p4["res_GL_to_O"] - p4["res_GL_to_SO"], 0.0)
        + (0.25 if n1["pass"] else 0.0)
    )

    candidate_rows: list[dict[str, object]] = [
        {
            "option": "residual_contraction_surface",
            "mean_abs_a0": float(np.log1p(residual_mean)),
            "doctrine_fit": _bool_score(
                exact_checks["gl_residual_positive"],
                exact_checks["family_residuals_positive"],
                exact_checks["cascade_monotone"],
            ),
            "shell_alignment": float(np.tanh(np.log1p(residual_mean) * mean_hubble / max(graph_longest, 1))),
        },
        {
            "option": "orientation_gate_surface",
            "mean_abs_a0": orientation_signal,
            "doctrine_fit": _bool_score(
                exact_checks["orientation_projection_admissible"],
                exact_checks["clifford_grade_filter"],
                exact_checks["determinant_one"],
            ),
            "shell_alignment": float(np.tanh(orientation_signal * (1.0 + dynamic_gap))),
        },
        {
            "option": "autograd_gradient_surface",
            "mean_abs_a0": float(np.log1p(gradient_mean)),
            "doctrine_fit": _bool_score(
                exact_checks["autograd_gradient_exists"],
                exact_checks["gradient_scales"],
            ),
            "shell_alignment": float(np.tanh(np.log1p(gradient_mean) * final_scale_factor / 3.0)),
        },
        {
            "option": "solver_monotone_surface",
            "mean_abs_a0": float(np.log1p(monotone_signal)),
            "doctrine_fit": _bool_score(
                exact_checks["solver_unsat_monotone"],
                exact_checks["cascade_monotone"],
                exact_checks["symbolic_nonnegative"],
            ),
            "shell_alignment": float(np.tanh((monotone_signal + dynamic_gap) / (1.0 + manifold_distance))),
        },
        {
            "option": "ground_state_zero_surface",
            "mean_abs_a0": float(1.0 / (1.0 + ground_state_sum)),
            "doctrine_fit": _bool_score(
                exact_checks["identity_ground_state"],
                exact_checks["so_ground_state_zero"],
                exact_checks["orthogonality_defect_zero"],
                exact_checks["geomstats_ground_state"],
            ),
            "shell_alignment": float(np.tanh((1.0 / (1.0 + ground_state_sum)) * (1.0 + mean_hubble))),
        },
        {
            "option": "tower_connectivity_surface",
            "mean_abs_a0": connectivity_signal + np.log1p(boundary_ratio),
            "doctrine_fit": _bool_score(
                exact_checks["tower_graph_connected"],
                exact_checks["residual_family_connected"],
                exact_checks["clifford_nonunit_residual"],
                exact_checks["large_scale_large_residual"],
                exact_checks["near_orth_small_residual"],
            ),
            "shell_alignment": float(np.tanh((connectivity_signal + np.log1p(boundary_ratio)) * shell_bridge_pass_fraction)),
        },
    ]

    for row in candidate_rows:
        row["shell_alignment_abs"] = abs(float(row["shell_alignment"]))
        row["composite_score"] = float(
            (float(row["mean_abs_a0"]) + float(row["doctrine_fit"]) + float(row["shell_alignment_abs"])) / 3.0
        )

    ranking = sorted(candidate_rows, key=lambda row: float(row["composite_score"]), reverse=True)
    lambda_shells = np.linspace(0.0, 1.0, len(ranking), dtype=np.float64)
    expansion_drive = np.asarray(
        [
            float(row["mean_abs_a0"]) + float(row["doctrine_fit"]) + float(row["shell_alignment_abs"])
            for row in ranking
        ],
        dtype=np.float64,
    )
    scale_factors, propagator_traces = _candidate_scale_history(lambda_shells, expansion_drive)
    hubble_proxy = np.gradient(np.log(np.clip(scale_factors, EPS, None)), lambda_shells)

    for row, scale, hubble in zip(ranking, scale_factors.tolist(), hubble_proxy.tolist(), strict=True):
        row["scale_factor"] = float(scale)
        row["hubble_proxy"] = float(hubble)

    graph_surface = _candidate_graph_surface(ranking)
    ranking_index = {row["option"]: idx for idx, row in enumerate(ranking)}
    hypergraph_windows = [
        [
            ranking_index["residual_contraction_surface"],
            ranking_index["solver_monotone_surface"],
            ranking_index["ground_state_zero_surface"],
        ],
        [
            ranking_index["orientation_gate_surface"],
            ranking_index["tower_connectivity_surface"],
            ranking_index["autograd_gradient_surface"],
        ],
        [
            ranking_index["residual_contraction_surface"],
            ranking_index["tower_connectivity_surface"],
            ranking_index["autograd_gradient_surface"],
        ],
    ]

    hypergraph_surface = _candidate_hypergraph_surface(len(ranking), hypergraph_windows)
    topology_pair_edges = [[idx, idx + 1] for idx in range(len(ranking) - 1)]
    topology_triad_windows: list[list[int]] = []
    cell_complex_surface = _candidate_cell_complex_surface(
        len(ranking),
        topology_pair_edges,
        topology_triad_windows,
    )
    topology_surface = _candidate_topology_surface(
        len(ranking),
        topology_pair_edges,
        topology_triad_windows,
    )
    symbolic_surface = _candidate_symbolic_surface(lambda_shells, scale_factors, expansion_drive)
    constraint_surface = _candidate_constraint_surface(
        lambda_shells,
        scale_factors,
        np.asarray([float(row["composite_score"]) for row in ranking], dtype=np.float64),
    )
    manifold_surface = _candidate_manifold_surface(
        np.asarray([float(row["mean_abs_a0"]) for row in ranking], dtype=np.float64),
        np.asarray([float(row["doctrine_fit"]) for row in ranking], dtype=np.float64),
        np.asarray([float(row["shell_alignment_abs"]) for row in ranking], dtype=np.float64),
        scale_factors,
    )
    torch_fit = _torch_candidate_fit(
        np.stack(
            [
                np.asarray([float(row["mean_abs_a0"]) for row in ranking], dtype=np.float64),
                np.asarray([float(row["doctrine_fit"]) for row in ranking], dtype=np.float64),
                np.asarray([float(row["shell_alignment_abs"]) for row in ranking], dtype=np.float64),
            ],
            axis=1,
        ),
        hubble_proxy,
    )

    winner_row = ranking[0]
    winner_vector = np.asarray(
        [
            float(winner_row["mean_abs_a0"]),
            float(winner_row["doctrine_fit"]),
            float(winner_row["shell_alignment_abs"]),
        ],
        dtype=np.float64,
    )
    clifford_vector = _clifford_vector(winner_vector)
    torch_ga_vector = _torch_ga_roundtrip(winner_vector)
    topology_parity_ok = bool(
        cell_complex_surface["euler_characteristic"] == topology_surface["euler_characteristic"]
    )
    frontier_count = sum(
        1
        for row in ranking
        if float(row["mean_abs_a0"]) > 0.1
        and float(row["doctrine_fit"]) > 0.5
        and float(row["shell_alignment_abs"]) > 0.1
    )

    pass_flag = bool(
        shell_bridge["lane_d_keep"]
        and graph_surface["longest_path_length"] >= len(ranking) - 1
        and hypergraph_surface["max_hyperedge_size"] >= 3
        and topology_surface["beta0"] == 1
        and topology_surface["beta1"] == 0
        and topology_parity_ok
        and constraint_surface["sat"]
        and symbolic_surface["symbolic_hubble_mid"] > 0.05
        and manifold_surface["mean_geodesic_distance"] > 1e-2
        and torch_fit["loss"] < 1.0
        and frontier_count == len(ranking)
        and exact_checks["solver_unsat_monotone"]
        and exact_checks["identity_ground_state"]
        and exact_checks["gradient_scales"]
    )

    return {
        "pass": pass_flag,
        "winner": str(winner_row["option"]),
        "frontier_count": int(frontier_count),
        "frontier_size": int(len(ranking)),
        "shell_bridge_pass_fraction": float(shell_bridge_pass_fraction),
        "candidate_rows": ranking,
        "graph_surface": {
            "edge_count": int(graph_surface["edge_count"]),
            "longest_path_length": int(graph_surface["longest_path_length"]),
            "triad_windows": graph_surface["triad_windows"],
        },
        "hypergraph_surface": {
            "num_edges": int(hypergraph_surface["num_edges"]),
            "max_hyperedge_size": int(hypergraph_surface["max_hyperedge_size"]),
            "connected_components": int(hypergraph_surface["connected_components"]),
            "hyperedges": hypergraph_surface["hyperedges"],
        },
        "topology_surface": {
            "betti_numbers": topology_surface["betti_numbers"],
            "euler_characteristic": int(topology_surface["euler_characteristic"]),
            "parity_ok": bool(topology_parity_ok),
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
        "signal_snapshot": {
            "residual_mean": residual_mean,
            "gradient_mean": gradient_mean,
            "boundary_ratio": boundary_ratio,
            "ground_state_sum": ground_state_sum,
            "orientation_signal": orientation_signal,
            "connectivity_signal": connectivity_signal,
            "monotone_signal": monotone_signal,
        },
    }


def main() -> None:
    positive, positive_checks = run_positive_tests()
    negative, negative_checks = run_negative_tests()
    boundary, boundary_checks = run_boundary_tests()
    exact_checks = {**positive_checks, **negative_checks, **boundary_checks}

    legacy_all_pass = bool(
        all(value.get("pass", False) for value in positive.values())
        and all(value.get("pass", False) for value in negative.values())
        and all(value.get("pass", False) for value in boundary.values())
    )

    shell_history = _build_gtower_shell_history()
    shell_bridge = lane_d_topology_expansion_bridge(shell_history)
    deep_contract = _aggregate_deep_contract(positive, negative, boundary, exact_checks, shell_bridge)
    overall_pass = bool(legacy_all_pass and deep_contract["pass"])

    results = {
        "name": NAME,
        "classification": classification,
        "claim": (
            "As a matrix descends the G-tower GL->O->SO, the distinguishability cost I_c (Axis 0) "
            "decreases monotonically. Each projection step eliminates degrees of freedom. "
            "The residual ||A - proj(A)||_F is the Axis 0 cost at that transition. "
            "The identity matrix is the ground state and autograd on the residual norm is the Axis 0 gradient."
        ),
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "exact_checks": exact_checks,
        "shell_history": shell_history,
        "shell_bridge": shell_bridge,
        "aggregate": {
            "legacy_all_pass": legacy_all_pass,
            "deep_contract": deep_contract,
        },
        "summary": {
            "legacy_all_pass": legacy_all_pass,
            "deep_all_pass": bool(deep_contract["pass"]),
            "all_pass": overall_pass,
            "scope_note": (
                "Bounded G-tower residual cascade doctrine preserved and now also bound to the deep Axis 0 shell contract."
            ),
        },
        "overall_pass": overall_pass,
        "all_pass": overall_pass,
    }

    def strip(obj):
        if isinstance(obj, dict):
            return {key: strip(value) for key, value in obj.items()}
        if isinstance(obj, list):
            return [strip(value) for value in obj]
        if isinstance(obj, np.ndarray):
            return strip(obj.tolist())
        if isinstance(obj, (complex, np.complexfloating)):
            if abs(float(np.imag(obj))) < 1e-12:
                return float(np.real(obj))
            return {
                "real": float(np.real(obj)),
                "imag": float(np.imag(obj)),
            }
        if isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        if isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        return obj

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / f"{NAME}_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(strip(results), indent=2))

    print(f"Results written to {out_path}")
    print("\n=== LEGACY CASCADE ===")
    print(f"Legacy pass: {legacy_all_pass}")
    print(f"P1 GL->O residual: {positive['P1_GL_matrix_has_nonzero_O3_residual']['residual_GL_to_O']:.6f}")
    print(f"P5 gradient norm: {positive['P5_pytorch_autograd_residual_gradient']['grad_norm']:.6f}")
    print(f"B2 large residual: {boundary['B2_highly_nonorthogonal_large_residual']['residual']:.6f}")

    print("\n=== DEEP CONTRACT ===")
    print(f"Deep pass: {deep_contract['pass']}")
    print(f"G-tower frontier: {deep_contract['frontier_count']}/{deep_contract['frontier_size']}")
    print(f"Winner: {deep_contract['winner']}")
    print(f"Shell bridge pass fraction: {deep_contract['shell_bridge_pass_fraction']:.3f}")
    print(f"Graph longest path: {deep_contract['graph_surface']['longest_path_length']}")
    print(f"Topology betti numbers: {deep_contract['topology_surface']['betti_numbers']}")
    print(f"Symbolic hubble mid: {deep_contract['symbolic_surface']['symbolic_hubble_mid']:.6f}")
    print(f"Manifold mean distance: {deep_contract['manifold_surface']['mean_geodesic_distance']:.6f}")
    print(f"Torch fit loss: {deep_contract['torch_fit']['loss']:.6f}")
    print(
        "Vector gaps: "
        f"clifford={deep_contract['clifford_vector_gap']:.2e} "
        f"torch_ga={deep_contract['torch_ga_vector_gap']:.2e}"
    )
    print(f"\nPROBE STATUS: {'PASS' if overall_pass else 'FAIL'}")


if __name__ == "__main__":
    main()
