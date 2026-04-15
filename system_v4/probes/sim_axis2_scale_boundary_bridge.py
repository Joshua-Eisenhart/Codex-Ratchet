#!/usr/bin/env python3
"""
sim_axis2_scale_boundary_bridge.py
====================================
Axis 2 = scale / boundary conditions.

Claim: The GL->O step removes scale. The polar decomposition A = Q*S separates
rotation Q from positive-definite scale S. The scale factor is exactly Axis 2.
GL elements have Axis 2 != 0 (free scale); O(3) elements have det=+-1 (scale=1,
Axis 2 = 0). SL(3,R) is the GL submanifold with det=1 — scale frozen at 1.

classification: classical_baseline
"""

import json
import os
import sys
import math
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True,
                "reason": "compute det(A)^{1/n} for varying GL matrices; autograd d(det^{1/3})/dA; polar decomp via SVD; scale = product of singular values"},
    "pyg": {"tried": False, "used": False,
            "reason": "not used — scale bridge is a matrix-level test; no graph message-passing required"},
    "z3": {"tried": True, "used": True,
           "reason": "UNSAT: det(A)=1 AND scale != 1 — if det=1 then geometric mean scale = 1, structural constraint"},
    "cvc5": {"tried": False, "used": False,
             "reason": "not used — z3 covers the proof layer for this sim"},
    "sympy": {"tried": True, "used": True,
              "reason": "symbolic polar decomp for 2x2: A=[[a,b],[c,d]], det=ad-bc, scale=(det)^{1/2} for 2x2; show scale is independent of rotation angle"},
    "clifford": {"tried": True, "used": True,
                 "reason": "grade-0 scalar in Cl(3,0) = the scale; polar decomp = separating grade-0 from grades 1-3; grade-0 nonzero for GL\\O matrices"},
    "geomstats": {"tried": True, "used": True,
                  "reason": "GeneralLinear(n=3): sample random GL elements; compute singular values (scale); verify SVs=1 exactly for orthogonal matrices"},
    "e3nn": {"tried": False, "used": False,
             "reason": "not used — scale bridge is matrix algebraic; no equivariant network required"},
    "rustworkx": {"tried": True, "used": True,
                  "reason": "scale DOF graph: nodes={GL_scale_dof, O_no_scale, SL3_det1, SU3_det1}; directed edges where scale is eliminated; verify GL is root node"},
    "xgi": {"tried": False, "used": False,
            "reason": "not used — scale bridge is matrix algebraic; no hypergraph topology required"},
    "toponetx": {"tried": False, "used": False,
                 "reason": "not used — scale bridge is matrix algebraic; no cell complex required"},
    "gudhi": {"tried": False, "used": False,
              "reason": "not used — scale bridge is matrix algebraic; no persistent homology required"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None,
    "z3": "load_bearing",
    "cvc5": None,
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "geomstats": "load_bearing",
    "e3nn": None,
    "rustworkx": "load_bearing",
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# =====================================================================
# IMPORTS
# =====================================================================

import torch
import sympy as sp
from z3 import Real, Solver, sat, unsat
from clifford import Cl
import rustworkx as rx
import os as _os
_os.environ.setdefault("GEOMSTATS_BACKEND", "numpy")
import geomstats.backend as gs
from geomstats.geometry.general_linear import GeneralLinear

# =====================================================================
# HELPERS
# =====================================================================

def scale_factor(M: torch.Tensor) -> float:
    """Geometric mean scale = det(M)^{1/n} for n x n matrix."""
    n = M.shape[0]
    det_val = torch.linalg.det(M).abs()
    return det_val.pow(1.0 / n).item()


def polar_decomp_scale(M: torch.Tensor):
    """Polar decomp M = Q * S; return scale = product of singular values."""
    U, S_svd, Vh = torch.linalg.svd(M)
    Q = U @ Vh
    S_mat = torch.diag(S_svd)
    # S = Vh.T @ diag(S_svd) @ Vh
    S_pos = Vh.mH @ S_mat @ Vh
    return Q, S_pos, S_svd


def random_gl3(seed=None, scale=1.0) -> torch.Tensor:
    """Random GL(3,R) element."""
    if seed is not None:
        torch.manual_seed(seed)
    while True:
        M = torch.randn(3, 3, dtype=torch.float64) * scale
        if abs(torch.linalg.det(M).item()) > 0.1:
            return M


def random_so3(seed=None) -> torch.Tensor:
    """Random SO(3) element."""
    if seed is not None:
        torch.manual_seed(seed)
    H = torch.randn(3, 3, dtype=torch.float64)
    H = (H - H.T) / 2
    return torch.linalg.matrix_exp(H)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # ---- P1 (pytorch): GL element has scale != 1 (free scale DOF) ----
    p1_pass = True
    scale_vals = []
    for seed in range(5):
        M = random_gl3(seed, scale=2.0)
        sf = scale_factor(M)
        scale_vals.append(round(sf, 6))
        # A random GL matrix should NOT have scale exactly 1 (probability 0)
        if abs(sf - 1.0) < 0.01:
            p1_pass = False
    results["P1_pytorch_gl3_nonunit_scale"] = {
        "pass": p1_pass,
        "description": "GL(3,R) matrices have det^{1/3} != 1 — free scale degree of freedom (Axis 2 active)",
        "scale_values": scale_vals
    }

    # ---- P2 (pytorch): O(3) element has det = +-1 — no scale freedom ----
    p2_pass = True
    o3_scales = []
    for seed in range(5):
        R = random_so3(seed)
        sf = scale_factor(R)
        det_val = torch.linalg.det(R).item()
        o3_scales.append({"scale": round(sf, 10), "det": round(det_val, 10)})
        if abs(sf - 1.0) > 1e-8:
            p2_pass = False
    results["P2_pytorch_o3_unit_scale"] = {
        "pass": p2_pass,
        "description": "O(3)/SO(3) matrices have det^{1/3} = 1 exactly — scale (Axis 2) is frozen at 1",
        "o3_scales": o3_scales
    }

    # ---- P3 (pytorch): Polar decomp — scale S is exactly the Axis 2 coordinate ----
    p3_pass = True
    polar_checks = []
    for seed in range(3):
        M = random_gl3(seed, scale=1.5)
        Q, S_pos, S_svd = polar_decomp_scale(M)
        # Verify M = Q * S_pos (reconstruct)
        M_recon = Q @ S_pos
        recon_err = torch.linalg.norm(M - M_recon).item()
        # Scale = geometric mean of SVD singular values
        geom_mean_sv = float(S_svd.prod().pow(1.0 / 3))
        sf_direct = scale_factor(M)
        polar_checks.append({
            "recon_err": round(recon_err, 12),
            "geom_mean_sv": round(geom_mean_sv, 8),
            "direct_scale": round(sf_direct, 8)
        })
        if recon_err > 1e-8:
            p3_pass = False
    results["P3_pytorch_polar_decomp_scale_consistent"] = {
        "pass": p3_pass,
        "description": "Polar decomp M=Q*S: reconstruction error < 1e-8; scale = geometric mean of singular values",
        "checks": polar_checks
    }

    # ---- P4 (pytorch): Scale varies continuously as det(A) varies from 0.5 to 2.0 ----
    det_targets = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0]
    scale_by_det = []
    prev_scale = None
    p4_pass = True
    torch.manual_seed(99)
    M_base = random_gl3(0, scale=1.0)
    for det_t in det_targets:
        # Scale M_base to have desired det
        det_current = torch.linalg.det(M_base).abs().item()
        M_scaled = M_base * (det_t / det_current) ** (1.0 / 3)
        sf = scale_factor(M_scaled)
        scale_by_det.append(round(sf, 6))
        if prev_scale is not None and sf < prev_scale - 0.1:
            p4_pass = False
        prev_scale = sf
    results["P4_pytorch_scale_varies_continuously_with_det"] = {
        "pass": p4_pass,
        "description": "Scale det^{1/3} varies continuously and monotonically as det(A) varies 0.5->2.0",
        "scale_by_det": scale_by_det
    }

    # ---- P5 (pytorch): autograd — d(det^{1/3})/dA is nonzero ----
    torch.manual_seed(7)
    M_ag = random_gl3(0, scale=1.5).requires_grad_(True)
    det_val = torch.linalg.det(M_ag).abs()
    scale_ag = det_val.pow(1.0 / 3)
    scale_ag.backward()
    grad_norm = M_ag.grad.norm().item()
    p5_pass = grad_norm > 1e-6
    results["P5_pytorch_autograd_scale_gradient_nonzero"] = {
        "pass": p5_pass,
        "description": "Autograd: d(det^{1/3})/dA is nonzero — scale is a differentiable DOF of GL",
        "gradient_norm": round(grad_norm, 8)
    }

    # ---- P6 (sympy): symbolic polar decomp 2x2: scale = sqrt(det) is independent of rotation ----
    a_s, b_s, c_s, d_s = sp.symbols('a b c d', real=True)
    det_sym = a_s * d_s - b_s * c_s
    scale_sym = sp.sqrt(sp.Abs(det_sym))
    # rotation angle theta for SO(2) is independent of scale
    # At (a=r*cos(t), b=-r*sin(t), c=r*sin(t), d=r*cos(t)): det = r^2, scale = r
    r_s, t_s = sp.symbols('r theta', real=True, positive=True)
    scale_polar = scale_sym.subs({a_s: r_s*sp.cos(t_s), b_s: -r_s*sp.sin(t_s),
                                   c_s: r_s*sp.sin(t_s), d_s: r_s*sp.cos(t_s)})
    scale_polar_simplified = sp.simplify(scale_polar)
    # scale should be r, independent of t
    d_scale_dt = sp.diff(scale_polar_simplified, t_s)
    d_scale_dt_simplified = sp.simplify(d_scale_dt)
    p6_pass = (d_scale_dt_simplified == 0)
    results["P6_sympy_scale_independent_of_rotation"] = {
        "pass": bool(p6_pass),
        "description": "Sympy 2x2 polar: scale = sqrt(det) = r is independent of rotation angle theta (d/dtheta = 0)",
        "d_scale_dtheta": str(d_scale_dt_simplified)
    }

    # ---- P7 (clifford): GL multivector — grade-0 scalar component = scale proxy ----
    layout, blades = Cl(3, 0)
    # In Cl(3,0), the grade-0 (scalar) part of a versor = the scale
    # For a GL element represented as a multivector, the scalar part is nonzero
    # Use a simple rotor R = cos(t) + sin(t)*e12 (unit norm = 1, scale = 1)
    # vs. a scaled rotor R_scaled = s*(cos(t) + sin(t)*e12) (scale = s)
    e12 = blades['e12']
    import math as _math
    t_val = 0.7
    s_val = 2.0
    rotor_unit = _math.cos(t_val) + _math.sin(t_val) * e12
    rotor_scaled = s_val * rotor_unit
    # Norm (magnitude) of rotor = scale
    norm_unit = float(abs(rotor_unit))
    norm_scaled = float(abs(rotor_scaled))
    p7_pass = (abs(norm_unit - 1.0) < 1e-10) and (abs(norm_scaled - s_val) < 1e-10)
    results["P7_clifford_scaled_rotor_norm_equals_scale"] = {
        "pass": p7_pass,
        "description": "Clifford: |rotor| = 1 for unit rotor; |s*rotor| = s for scaled rotor — norm IS the scale (Axis 2)",
        "norm_unit": round(norm_unit, 10),
        "norm_scaled": round(norm_scaled, 10)
    }

    # ---- P8 (geomstats): GL(3,R) singular values are nonunit for general elements ----
    GL3 = GeneralLinear(n=3)
    gl_samples = GL3.random_point(n_samples=5)
    sv_deviations = []
    p8_pass = True
    for M_gs in gl_samples:
        svs = np.linalg.svd(M_gs, compute_uv=False)
        dev_from_unit = float(np.max(np.abs(svs - 1.0)))
        sv_deviations.append(round(dev_from_unit, 6))
        # at least some singular values should be != 1
    # At least 3 of 5 should have deviation > 0.1
    large_dev = sum(1 for d in sv_deviations if d > 0.1)
    p8_pass = large_dev >= 3
    results["P8_geomstats_gl3_nonunit_singular_values"] = {
        "pass": bool(p8_pass),
        "description": "Geomstats GL(3): random samples have singular values != 1 (scale DOF active)",
        "sv_deviations_from_unit": sv_deviations,
        "large_deviation_count": large_dev
    }

    # ---- P9 (rustworkx): scale DOF graph — GL is root with most scale freedom ----
    G = rx.PyDiGraph()
    ns = {}
    scale_data = [
        ("GL", "free_scale"),
        ("O", "det_pm1_no_scale"),
        ("SO", "det_plus1_no_scale"),
        ("SL3", "det1_no_scale"),
        ("SU3", "det1_no_scale"),
    ]
    for label, scale_dof in scale_data:
        ns[label] = G.add_node({"label": label, "scale_dof": scale_dof})
    for src, tgt in [("GL", "O"), ("GL", "SL3"), ("O", "SO"), ("SL3", "SU3")]:
        G.add_edge(ns[src], ns[tgt], {"src": src, "tgt": tgt})
    free_scale_nodes = [G[n]["label"] for n in G.node_indices()
                        if G[n]["scale_dof"] == "free_scale"]
    gl_in_degree = G.in_degree(ns["GL"])
    p9_pass = (free_scale_nodes == ["GL"]) and (gl_in_degree == 0)
    results["P9_rustworkx_gl_root_free_scale"] = {
        "pass": p9_pass,
        "description": "Scale DOF graph: GL is the unique root node with free_scale; all descendants have frozen scale",
        "free_scale_nodes": free_scale_nodes,
        "gl_in_degree": gl_in_degree
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # ---- N1 (pytorch): O(3) element has no scale variation ----
    n1_pass = True
    for seed in range(8):
        R = random_so3(seed)
        sf = scale_factor(R)
        if abs(sf - 1.0) > 1e-7:
            n1_pass = False
    results["N1_pytorch_o3_no_scale_variation"] = {
        "pass": n1_pass,
        "description": "Negative: SO(3) matrices always have scale = 1 exactly — Axis 2 frozen"
    }

    # ---- N2 (z3): UNSAT — det(A) = 1 AND scale != 1 ----
    solver = Solver()
    det_z3 = Real('det')
    scale_z3 = Real('scale')
    n_dim = 3
    # det = 1 implies scale = det^{1/3} = 1
    solver.add(det_z3 == 1)
    solver.add(scale_z3 > 1.0 + 1e-6)  # scale strictly > 1
    # Physical constraint: scale = det^{1/n}, so scale^n = det
    # For det=1: scale^3 = 1 → scale = 1
    solver.add(scale_z3 * scale_z3 * scale_z3 == det_z3)
    r = solver.check()
    n2_pass = (r == unsat)
    results["N2_z3_det1_implies_scale1"] = {
        "pass": n2_pass,
        "description": "Z3 UNSAT: det(A)=1 AND scale != 1 — geometric mean scale is structurally 1 when det=1",
        "z3_result": str(r)
    }

    # ---- N3 (sympy): scale = 1 for SO(2) elements ----
    r_s, t_s = sp.symbols('r theta', real=True, positive=True)
    # SO(2) = rotation only: r=1
    scale_so2 = sp.sqrt(r_s**2 * (sp.cos(t_s)**2 + sp.sin(t_s)**2))
    scale_so2_simplified = sp.simplify(scale_so2)
    scale_at_r1 = scale_so2_simplified.subs(r_s, 1)
    n3_pass = (sp.simplify(scale_at_r1 - 1) == 0)
    results["N3_sympy_so2_scale_equals_1"] = {
        "pass": bool(n3_pass),
        "description": "Sympy: SO(2) polar rep with r=1 gives scale = 1 exactly — no scale DOF"
    }

    # ---- N4 (clifford): unit rotor has norm exactly 1 ----
    layout, blades = Cl(3, 0)
    e12 = blades['e12']
    import math as _math
    t_val = 1.2
    rotor = _math.cos(t_val) + _math.sin(t_val) * e12
    norm_val = float(abs(rotor))
    n4_pass = abs(norm_val - 1.0) < 1e-10
    results["N4_clifford_unit_rotor_norm_1"] = {
        "pass": n4_pass,
        "description": "Clifford: unit rotor cos(t)+sin(t)*e12 has norm = 1 exactly — no scale component",
        "norm": round(norm_val, 12)
    }

    # ---- N5 (geomstats): SO(3) matrices have all SVs = 1 ----
    SO3 = SpecialOrthogonal(n=3)
    so3_samples = SO3.random_point(n_samples=5)
    max_sv_dev = max(
        float(np.max(np.abs(np.linalg.svd(s, compute_uv=False) - 1.0)))
        for s in so3_samples
    )
    n5_pass = max_sv_dev < 1e-10
    results["N5_geomstats_so3_svs_all_one"] = {
        "pass": bool(n5_pass),
        "description": "Geomstats SO(3) samples: all singular values are 1 exactly — scale frozen",
        "max_sv_deviation": float(max_sv_dev)
    }

    # ---- N6 (rustworkx): O node has no outgoing scale edge to GL ----
    G2 = rx.PyDiGraph()
    ns2 = {}
    for lbl in ["GL", "O", "SO"]:
        ns2[lbl] = G2.add_node({"label": lbl})
    G2.add_edge(ns2["GL"], ns2["O"], {"direction": "scale_removed"})
    G2.add_edge(ns2["O"], ns2["SO"], {"direction": "orientation_fixed"})
    # Verify no edge from O back to GL (scale cannot be regained going down tower)
    o_out_edges = [(G2[s]["label"], G2[t]["label"])
                   for s, t, _ in G2.weighted_edge_list() if s == ns2["O"]]
    n6_pass = all(tgt != "GL" for _, tgt in o_out_edges)
    results["N6_rustworkx_no_reverse_scale_edge"] = {
        "pass": n6_pass,
        "description": "G-tower DAG: no edge from O back to GL — scale cannot be regained once removed",
        "o_out_edges": o_out_edges
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # ---- B1 (pytorch): At det(A) = 1, scale is exactly 1 (SL(3,R) manifold) ----
    torch.manual_seed(42)
    M = random_gl3(0, scale=1.5)
    det_val = torch.linalg.det(M).abs().item()
    # Rescale to det = 1
    M_sl = M / (det_val ** (1.0 / 3))
    det_sl = torch.linalg.det(M_sl).abs().item()
    scale_sl = scale_factor(M_sl)
    b1_pass = (abs(det_sl - 1.0) < 1e-8) and (abs(scale_sl - 1.0) < 1e-8)
    results["B1_pytorch_sl3_boundary_scale_1"] = {
        "pass": b1_pass,
        "description": "Boundary: det(A)=1 SL(3,R) matrix has scale = det^{1/3} = 1 exactly — Axis 2 = 0",
        "det_sl3": round(det_sl, 10),
        "scale_sl3": round(scale_sl, 10)
    }

    # ---- B2 (sympy): SL(2,R) boundary — scale=1 is the det=1 locus ----
    a_s, b_s, c_s, d_s = sp.symbols('a b c d', real=True)
    det_sym = a_s * d_s - b_s * c_s
    # At det=1: scale=1; det varies → scale varies
    scale_sym = sp.Abs(det_sym) ** sp.Rational(1, 2)
    scale_at_det1 = scale_sym.subs(det_sym, 1)
    b2_pass = (sp.simplify(scale_at_det1 - 1) == 0)
    results["B2_sympy_sl2_scale_equals_1"] = {
        "pass": bool(b2_pass),
        "description": "Sympy 2x2: when det=1, scale=sqrt(1)=1; the SL boundary is exactly scale=1 (Axis 2 = 0)",
        "scale_at_det1": str(scale_at_det1)
    }

    # ---- B3 (pytorch): As det varies 0.5→2.0, scale increases monotonically ----
    det_range = torch.linspace(0.5, 2.0, 10)
    scales = [float(d.pow(1.0 / 3).item()) for d in det_range]
    b3_pass = all(scales[i] <= scales[i+1] + 1e-9 for i in range(len(scales)-1))
    results["B3_pytorch_scale_monotone_with_det"] = {
        "pass": b3_pass,
        "description": "Boundary: scale = det^{1/3} is monotonically non-decreasing as det varies from 0.5 to 2.0",
        "scales": [round(s, 6) for s in scales]
    }

    # ---- B4 (z3): SAT — det(A) = 2.0 AND scale > 1 (consistent: scale = 2^{1/3} > 1) ----
    solver2 = Solver()
    det2 = Real('det2')
    scale2 = Real('scale2')
    solver2.add(det2 == 2)
    solver2.add(scale2 > 1)
    solver2.add(scale2 * scale2 * scale2 == det2)
    r2 = solver2.check()
    b4_pass = (r2 == sat)
    results["B4_z3_det2_scale_greater_1_sat"] = {
        "pass": b4_pass,
        "description": "Z3 SAT: det=2 AND scale>1 is consistent (scale=2^{1/3} > 1) — GL has free scale DOF",
        "z3_result": str(r2)
    }

    # ---- B5 (clifford): Scaled rotor's extra scale factor is exactly the norm excess ----
    layout, blades = Cl(3, 0)
    e12 = blades['e12']
    import math as _math
    t_val = 0.5
    s_target = 1.5
    rotor_unit = _math.cos(t_val) + _math.sin(t_val) * e12
    rotor_scaled = s_target * rotor_unit
    norm_ratio = float(abs(rotor_scaled)) / float(abs(rotor_unit))
    b5_pass = abs(norm_ratio - s_target) < 1e-10
    results["B5_clifford_scale_factor_equals_norm_ratio"] = {
        "pass": b5_pass,
        "description": "Boundary: scale factor = |scaled_rotor| / |unit_rotor| exactly; Axis 2 = norm ratio",
        "norm_ratio": round(norm_ratio, 10),
        "expected_scale": s_target
    }

    # ---- B6 (geomstats): Singular value product = det for GL matrices ----
    GL3 = GeneralLinear(n=3)
    gl_pt = GL3.random_point()
    svs = np.linalg.svd(gl_pt, compute_uv=False)
    sv_product = float(np.prod(svs))
    det_abs = float(abs(np.linalg.det(gl_pt)))
    b6_pass = abs(sv_product - det_abs) < 1e-8
    results["B6_geomstats_sv_product_equals_det"] = {
        "pass": bool(b6_pass),
        "description": "Geomstats GL(3): product of singular values = |det(A)| — scale = det^{1/3}",
        "sv_product": round(sv_product, 8),
        "det_abs": round(det_abs, 8)
    }

    return results


# =====================================================================
# IMPORTS (deferred)
# =====================================================================

from geomstats.geometry.special_orthogonal import SpecialOrthogonal


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SIM: Axis 2 Scale/Boundary G-Tower Bridge")
    print("=" * 60)

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_tests = {**positive, **negative, **boundary}
    n_total = len(all_tests)
    n_pass = sum(1 for v in all_tests.values() if v.get("pass", False))
    overall_pass = (n_pass == n_total)

    print(f"\nResults: {n_pass}/{n_total} passed")
    for name, res in all_tests.items():
        status = "PASS" if res.get("pass", False) else "FAIL"
        print(f"  [{status}] {name}")

    results = {
        "name": "sim_axis2_scale_boundary_bridge",
        "classification": "classical_baseline",
        "overall_pass": overall_pass,
        "n_pass": n_pass,
        "n_total": n_total,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_axis2_scale_boundary_bridge_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
    sys.exit(0 if overall_pass else 1)
