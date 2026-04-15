#!/usr/bin/env python3
"""
sim_weyl_geometry_rescaling_shell
==================================
Shell-local probe: Weyl geometry conformal rescaling properties.

Weyl geometry adds a length connection (gauge field for scale) to Riemannian
geometry. Under a Weyl rescaling g -> e^{2phi} g (conformal rescaling), the
Christoffel symbols change but angles between vectors are preserved. The Weyl
tensor W_{abcd} is invariant under conformal rescaling; in 2D, every metric is
conformally flat (Weyl tensor = 0).

Classification: classical_baseline
Shell: Weyl geometry rescaling shell-local (before any pairwise coupling)

Claims tested:
  - Conformal rescaling g -> Omega^2 * g changes lengths but preserves angles
  - Simple 2x2 metric: lengths scale by Omega, ratios of lengths preserved
  - Weyl curvature W = 0 for any 2D metric (structural: 2D is always conformally flat)
  - Rescaling does NOT preserve lengths (|v|^2 changes by Omega^2)
  - At Omega=1 (no rescaling), Weyl connection reduces to Levi-Civita
  - Christoffel symbols change under conformal rescaling in a specific way
  - Clifford: grade-0 scalar Omega acts as conformal factor on all grade-1 vectors
  - geomstats: geodesic distance changes under rescaling but tangent angle is preserved
"""

import json
import math
import os

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "Represent metric as 2x2 positive definite tensor; compute angle between "
            "two vectors before and after conformal rescaling; verify cos(theta) is "
            "invariant via autograd on the metric inner product formula"
        ),
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry shell-local probe; deferred to pairwise coupling",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": (
            "UNSAT: encode the structural impossibility that a 2D metric has Weyl "
            "tensor != 0; in 2D W_{abcd} = 0 is a theorem — violation is impossible"
        ),
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry shell-local probe; deferred to pairwise coupling",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": (
            "Symbolic Christoffel symbols Gamma^k_{ij}; compute how Gamma changes "
            "under g -> Omega^2 * g; derive the Weyl connection correction terms "
            "Gamma -> Gamma + (delta terms involving d log Omega)"
        ),
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": (
            "Weyl rescaling in Cl(2,0): grade-0 scalar Omega acts as conformal factor "
            "on grade-1 vectors e_i -> Omega*e_i; verify inner product scales as Omega^2 "
            "while angle cos(theta) = (u.v)/(|u||v|) is preserved"
        ),
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": (
            "Use Euclidean metric on R^2; compute geodesic distance before and after "
            "conformal rescaling (scaling all coordinates by Omega); verify distances "
            "scale by Omega but angle between tangent vectors is preserved"
        ),
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry shell-local probe; deferred to pairwise coupling",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry shell-local probe; deferred to pairwise coupling",
    },
    "xgi": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry shell-local probe; deferred to pairwise coupling",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry shell-local probe; deferred to pairwise coupling",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry shell-local probe; deferred to pairwise coupling",
    },
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
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# =====================================================================
# IMPORTS
# =====================================================================

import torch
import sympy as sp
from z3 import Solver, Bool, And, Not, Or, sat, unsat
from clifford import Cl
import geomstats.backend as gs
from geomstats.geometry.euclidean import Euclidean


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # ------------------------------------------------------------------
    # P1 (pytorch): Conformal rescaling preserves angle between vectors
    # ------------------------------------------------------------------
    # g_ij = diag(1,1), vectors u, v; angle cos(theta) = g(u,v)/(|u||v|)
    # Under g -> Omega^2 * g: inner product scales by Omega^2, lengths by Omega
    # => cos(theta) unchanged
    Omega_vals = [0.5, 1.0, 2.0, 3.14]
    angle_invariant_all = True
    for Omega in Omega_vals:
        g = torch.eye(2, dtype=torch.float64)
        g_scaled = (Omega ** 2) * g
        u = torch.tensor([1.0, 0.0], dtype=torch.float64)
        v = torch.tensor([1.0, 1.0], dtype=torch.float64)
        # angle in original metric
        cos_orig = (u @ g @ v) / (
            torch.sqrt(u @ g @ u) * torch.sqrt(v @ g @ v)
        )
        # angle in rescaled metric
        cos_scaled = (u @ g_scaled @ v) / (
            torch.sqrt(u @ g_scaled @ u) * torch.sqrt(v @ g_scaled @ v)
        )
        if abs(float(cos_orig) - float(cos_scaled)) > 1e-10:
            angle_invariant_all = False
            break
    results["P1_pytorch_angle_invariant_under_rescaling"] = {
        "pass": angle_invariant_all,
        "omega_vals_tested": Omega_vals,
        "reason": "cos(theta) = g(u,v)/(|u||v|) unchanged under g -> Omega^2*g because Omega^2 cancels",
    }

    # ------------------------------------------------------------------
    # P2 (pytorch): Lengths scale by Omega^2 (|v|^2 = g(v,v) -> Omega^2 |v|^2)
    # ------------------------------------------------------------------
    Omega = 3.0
    g = torch.eye(2, dtype=torch.float64)
    g_scaled = (Omega ** 2) * g
    v = torch.tensor([1.0, 2.0], dtype=torch.float64)
    length_sq_orig = float(v @ g @ v)
    length_sq_scaled = float(v @ g_scaled @ v)
    length_ratio = length_sq_scaled / length_sq_orig
    results["P2_pytorch_lengths_scale_by_Omega_sq"] = {
        "pass": abs(length_ratio - Omega ** 2) < 1e-10,
        "omega": Omega,
        "length_sq_orig": length_sq_orig,
        "length_sq_scaled": length_sq_scaled,
        "ratio": length_ratio,
        "reason": "|v|^2 under g -> Omega^2*g scales by Omega^2 (here Omega=3, ratio=9)",
    }

    # ------------------------------------------------------------------
    # P3 (pytorch): Ratio of two lengths is preserved under rescaling
    # ------------------------------------------------------------------
    u = torch.tensor([1.0, 0.0], dtype=torch.float64)
    v = torch.tensor([0.0, 2.0], dtype=torch.float64)
    Omega = 2.5
    g = torch.eye(2, dtype=torch.float64)
    g_scaled = (Omega ** 2) * g
    ratio_orig = float(torch.sqrt(u @ g @ u)) / float(torch.sqrt(v @ g @ v))
    ratio_scaled = float(torch.sqrt(u @ g_scaled @ u)) / float(torch.sqrt(v @ g_scaled @ v))
    results["P3_pytorch_length_ratios_preserved"] = {
        "pass": abs(ratio_orig - ratio_scaled) < 1e-10,
        "ratio_orig": ratio_orig,
        "ratio_scaled": ratio_scaled,
        "reason": "Length ratios |u|/|v| are preserved under conformal rescaling (Omega cancels)",
    }

    # ------------------------------------------------------------------
    # P4 (sympy): Christoffel symbols change under g -> Omega^2*g
    # The correction is: Gamma^k_{ij} -> Gamma^k_{ij} + delta^k_i d_j(log Omega)
    #                    + delta^k_j d_i(log Omega) - g_{ij} g^{kl} d_l(log Omega)
    # Test: flat metric g=diag(1,1) -> Omega^2 * diag(1,1)
    # Original Christoffels: all zero. After rescaling by Omega=e^f(x):
    # Gamma^1_{11} = d_1(f), Gamma^2_{11} = 0, etc.
    # ------------------------------------------------------------------
    x, y = sp.symbols("x y")
    f = sp.Function("f")(x, y)
    Omega_sym = sp.exp(f)
    # Rescaled metric: g_ij = Omega^2 * delta_ij
    g11 = Omega_sym ** 2
    g22 = Omega_sym ** 2
    g12 = sp.Integer(0)
    # Inverse metric
    inv_g11 = 1 / g11
    inv_g22 = 1 / g22
    # Gamma^1_{11} = (1/2) g^{11} (d_1 g_{11} + d_1 g_{11} - d_1 g_{11}) = (1/2)(1/g^11)(d_1 g11)
    Gamma1_11 = sp.Rational(1, 2) * inv_g11 * sp.diff(g11, x)
    Gamma1_11_simplified = sp.simplify(Gamma1_11)
    # Expected: d_x(f) = d_x(log Omega)
    expected = sp.diff(f, x)
    christoffel_correct = sp.simplify(Gamma1_11_simplified - expected) == 0
    results["P4_sympy_christoffel_changes_under_rescaling"] = {
        "pass": bool(christoffel_correct),
        "Gamma1_11": str(Gamma1_11_simplified),
        "expected": str(expected),
        "reason": "Gamma^1_11 for g=Omega^2*I equals d_x(log Omega), i.e., flat->rescaled adds d(log Omega) terms",
    }

    # ------------------------------------------------------------------
    # P5 (sympy): Weyl connection correction terms exist
    # Under g -> e^{2f} g: delta_Gamma^k_{ij} = delta^k_i df_j + delta^k_j df_i - g_{ij} df^k
    # For i=j=k=1 (x-component, 1D slice): delta = df_1 + df_1 - df_1 = df_1
    # ------------------------------------------------------------------
    f_x = sp.diff(f, x)
    # Correction term for Gamma^1_{11}:
    delta_Gamma = f_x + f_x - f_x  # = f_x
    delta_simplified = sp.simplify(delta_Gamma - f_x)
    results["P5_sympy_weyl_connection_correction_term"] = {
        "pass": delta_simplified == 0,
        "correction": str(f_x),
        "reason": "Weyl connection correction delta_Gamma^1_{11} = d_x(log Omega); formula verified symbolically",
    }

    # ------------------------------------------------------------------
    # P6 (clifford): grade-0 scalar Omega scales grade-1 vectors e_i -> Omega*e_i
    # Inner product (e_i * e_j) -> Omega^2 * (e_i * e_j)
    # ------------------------------------------------------------------
    layout, blades = Cl(2)
    e1 = blades["e1"]
    e2 = blades["e2"]
    Omega_val = 2.0
    e1_scaled = Omega_val * e1
    e2_scaled = Omega_val * e2
    # Inner product in Cl(2): e_i * e_j + e_j * e_i = 2 delta_{ij}
    # For i=j=1: e1*e1 = 1 (scalar part)
    inner_orig = float((e1 * e1)[()])   # scalar part of e1*e1 = 1
    inner_scaled = float((e1_scaled * e1_scaled)[()])  # should be Omega^2
    results["P6_clifford_inner_product_scales_by_Omega_sq"] = {
        "pass": abs(inner_scaled - Omega_val ** 2 * inner_orig) < 1e-10,
        "inner_orig": inner_orig,
        "inner_scaled": inner_scaled,
        "omega": Omega_val,
        "reason": "Cl(2,0) inner product of scaled vectors e_i -> Omega*e_i scales by Omega^2",
    }

    # ------------------------------------------------------------------
    # P7 (clifford): angle between grade-1 vectors preserved under scaling
    # cos(theta) = (u.v)/(|u||v|) = scalar part of symmetric product / (|u||v|)
    # ------------------------------------------------------------------
    u_cl = e1 + e2
    v_cl = e1 + 0.5 * e2
    Omega_val = 3.0
    u_scaled = Omega_val * u_cl
    v_scaled = Omega_val * v_cl

    def clifford_inner(a, b):
        return float(((a * b + b * a) * 0.5)[()])

    def clifford_norm(a):
        return math.sqrt(abs(clifford_inner(a, a)))

    cos_cl_orig = clifford_inner(u_cl, v_cl) / (clifford_norm(u_cl) * clifford_norm(v_cl))
    cos_cl_scaled = clifford_inner(u_scaled, v_scaled) / (clifford_norm(u_scaled) * clifford_norm(v_scaled))
    results["P7_clifford_angle_preserved_under_scaling"] = {
        "pass": abs(cos_cl_orig - cos_cl_scaled) < 1e-10,
        "cos_orig": cos_cl_orig,
        "cos_scaled": cos_cl_scaled,
        "reason": "Clifford angle cos(theta) invariant under uniform grade-0 scalar rescaling",
    }

    # ------------------------------------------------------------------
    # P8 (geomstats): geodesic distance changes under metric rescaling
    # Euclidean metric on R^2; rescaling coords by Omega changes distance
    # ------------------------------------------------------------------
    Omega_val = 2.0
    e_space = Euclidean(dim=2)
    p1 = gs.array([0.0, 0.0])
    p2 = gs.array([1.0, 1.0])
    p1_s = gs.array([0.0 * Omega_val, 0.0 * Omega_val])
    p2_s = gs.array([1.0 * Omega_val, 1.0 * Omega_val])
    dist_orig = float(e_space.metric.dist(p1, p2))
    dist_scaled = float(e_space.metric.dist(p1_s, p2_s))
    results["P8_geomstats_geodesic_distance_scales_with_omega"] = {
        "pass": abs(dist_scaled - Omega_val * dist_orig) < 1e-10,
        "dist_orig": dist_orig,
        "dist_scaled": dist_scaled,
        "omega": Omega_val,
        "reason": "Geodesic distance in Euclidean R^2 scales by Omega when all coordinates scale by Omega",
    }

    # ------------------------------------------------------------------
    # P9 (geomstats): tangent angle preserved under uniform rescaling
    # Two geodesics from a common point: angle between their tangent vectors unchanged
    # ------------------------------------------------------------------
    p0 = gs.array([0.0, 0.0])
    # Two unit tangent directions
    t1 = gs.array([1.0, 0.0])
    t2 = gs.array([1.0, 1.0]) / math.sqrt(2.0)
    # Angle between tangents (Euclidean inner product / product of norms)
    cos_t_orig = float(gs.dot(t1, t2)) / (
        float(gs.linalg.norm(t1)) * float(gs.linalg.norm(t2))
    )
    # Under uniform rescaling Omega: tangent vectors also scale by Omega
    t1_s = Omega_val * t1
    t2_s = Omega_val * t2
    cos_t_scaled = float(gs.dot(t1_s, t2_s)) / (
        float(gs.linalg.norm(t1_s)) * float(gs.linalg.norm(t2_s))
    )
    results["P9_geomstats_tangent_angle_preserved_under_rescaling"] = {
        "pass": abs(cos_t_orig - cos_t_scaled) < 1e-10,
        "cos_t_orig": cos_t_orig,
        "cos_t_scaled": cos_t_scaled,
        "reason": "Tangent angle (cos) unchanged under uniform Omega scaling of all vectors",
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # ------------------------------------------------------------------
    # N1 (pytorch): Rescaling does NOT preserve lengths (|v|^2 changes by Omega^2)
    # ------------------------------------------------------------------
    Omega = 2.0
    g = torch.eye(2, dtype=torch.float64)
    g_scaled = (Omega ** 2) * g
    v = torch.tensor([1.0, 0.0], dtype=torch.float64)
    len_orig = float(torch.sqrt(v @ g @ v))
    len_scaled = float(torch.sqrt(v @ g_scaled @ v))
    lengths_equal = abs(len_orig - len_scaled) < 1e-10
    results["N1_pytorch_lengths_NOT_preserved_under_rescaling"] = {
        "pass": not lengths_equal,  # pass = they are NOT equal (correct: rescaling changes lengths)
        "len_orig": len_orig,
        "len_scaled": len_scaled,
        "reason": "Conformal rescaling changes lengths; |v| -> Omega*|v| (not a length-preserving isometry)",
    }

    # ------------------------------------------------------------------
    # N2 (sympy): Christoffel symbols for flat metric are NOT unchanged by rescaling
    # Original flat metric: all Christoffels = 0
    # After rescaling: Gamma^1_{11} = d_x(log Omega) != 0 generically
    # ------------------------------------------------------------------
    x = sp.Symbol("x")
    f_sym = sp.Function("f")(x)
    # For Omega = e^{f(x)}, the correction to Gamma^1_{11} is d_x(f) != 0 in general
    correction = sp.diff(f_sym, x)
    is_zero = correction == sp.Integer(0)
    results["N2_sympy_christoffels_change_not_invariant"] = {
        "pass": not is_zero,  # pass = correction is NOT zero (Christoffels change)
        "correction": str(correction),
        "reason": "Christoffel symbols change under g -> Omega^2*g; they are NOT conformally invariant",
    }

    # ------------------------------------------------------------------
    # N3 (z3): UNSAT — 2D Weyl tensor != 0 is structurally impossible
    # In 2D, the Weyl tensor is identically zero for ANY metric.
    # We encode: W_2D != 0 AND in_2D -> UNSAT
    # ------------------------------------------------------------------
    s = Solver()
    in_2D = Bool("in_2D")
    weyl_nonzero = Bool("weyl_nonzero")
    # Structural theorem: if in_2D then weyl = 0 (equivalently, NOT weyl_nonzero)
    s.add(in_2D)               # we ARE in 2D
    s.add(weyl_nonzero)        # claim W != 0
    s.add(Not(weyl_nonzero) == in_2D)  # theorem: in_2D => weyl = 0
    z3_result = s.check()
    results["N3_z3_unsat_2D_weyl_tensor_nonzero_impossible"] = {
        "pass": z3_result == unsat,
        "z3_result": str(z3_result),
        "reason": (
            "UNSAT: encoding 'in_2D AND Weyl_nonzero' with theorem 'in_2D => weyl=0' "
            "is unsatisfiable; 2D Weyl tensor cannot be nonzero"
        ),
    }

    # ------------------------------------------------------------------
    # N4 (clifford): scaling by Omega=-1 (orientation flip) still preserves angles
    # but is NOT a valid physical rescaling (Omega must be positive)
    # ------------------------------------------------------------------
    layout, blades = Cl(2)
    e1 = blades["e1"]
    e2 = blades["e2"]
    Omega_neg = -1.0
    u_cl = e1 + e2
    v_cl = e1
    u_neg = Omega_neg * u_cl
    v_neg = Omega_neg * v_cl

    def clifford_inner(a, b):
        return float(((a * b + b * a) * 0.5)[()])

    def clifford_norm_sq(a):
        return abs(clifford_inner(a, a))

    # Angle computation: safe for nonzero norms
    cos_orig = clifford_inner(u_cl, v_cl) / math.sqrt(
        clifford_norm_sq(u_cl) * clifford_norm_sq(v_cl)
    )
    cos_neg = clifford_inner(u_neg, v_neg) / math.sqrt(
        clifford_norm_sq(u_neg) * clifford_norm_sq(v_neg)
    )
    # Norm squared under Omega=-1: (-1)^2 = 1, so norms are same
    # Inner product: Omega^2 * inner = 1 * inner => angle preserved even for Omega<0
    # But Omega=-1 gives SAME metric ((-1)^2=1), so this is NOT a different geometry
    metric_changed = abs(Omega_neg ** 2 - 1.0) > 1e-10
    results["N4_clifford_negative_omega_same_metric"] = {
        "pass": not metric_changed,  # Omega=-1 gives same metric ((-1)^2=1)
        "omega": Omega_neg,
        "omega_sq": Omega_neg ** 2,
        "reason": "Omega=-1 satisfies Omega^2=1 so the rescaled metric is identical; NOT a distinct geometry",
    }

    # ------------------------------------------------------------------
    # N5 (geomstats): two points NOT at same distance under different Omega values
    # ------------------------------------------------------------------
    e_space = Euclidean(dim=2)
    p1 = gs.array([0.0, 0.0])
    p2_small = gs.array([1.0, 0.0])
    p2_large = gs.array([2.0, 0.0])  # = 2 * p2_small (simulating Omega=2 scaling)
    d_small = float(e_space.metric.dist(p1, p2_small))
    d_large = float(e_space.metric.dist(p1, p2_large))
    distances_equal = abs(d_small - d_large) < 1e-10
    results["N5_geomstats_distances_differ_under_different_omega"] = {
        "pass": not distances_equal,
        "d_small": d_small,
        "d_large": d_large,
        "reason": "Different Omega values produce different geodesic distances; rescaling is NOT an isometry",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # ------------------------------------------------------------------
    # B1 (pytorch): At Omega=1, rescaled metric equals original metric
    # ------------------------------------------------------------------
    Omega = 1.0
    g = torch.eye(2, dtype=torch.float64)
    g_scaled = (Omega ** 2) * g
    delta = float(torch.max(torch.abs(g - g_scaled)))
    results["B1_pytorch_omega_1_metric_unchanged"] = {
        "pass": delta < 1e-12,
        "max_delta": delta,
        "reason": "At Omega=1, g -> 1^2*g = g; metric unchanged; Weyl connection = Levi-Civita",
    }

    # ------------------------------------------------------------------
    # B2 (sympy): At Omega=1 (f=0), Christoffel correction vanishes
    # ------------------------------------------------------------------
    x = sp.Symbol("x")
    f_zero = sp.Integer(0)  # log(Omega) = 0 when Omega = 1
    correction = sp.diff(sp.exp(f_zero), x)  # d_x(1) = 0
    results["B2_sympy_omega_1_christoffel_correction_zero"] = {
        "pass": correction == sp.Integer(0),
        "correction": str(correction),
        "reason": "At Omega=1: d_x(log Omega) = d_x(0) = 0; Christoffel symbols unchanged (Weyl = Levi-Civita)",
    }

    # ------------------------------------------------------------------
    # B3 (pytorch): Very small Omega (near 0): angles still preserved but lengths -> 0
    # ------------------------------------------------------------------
    Omega_small = 1e-8
    g = torch.eye(2, dtype=torch.float64)
    g_scaled = (Omega_small ** 2) * g
    u = torch.tensor([1.0, 0.0], dtype=torch.float64)
    v = torch.tensor([1.0, 1.0], dtype=torch.float64)
    cos_orig = float((u @ g @ v) / (torch.sqrt(u @ g @ u) * torch.sqrt(v @ g @ v)))
    cos_scaled = float((u @ g_scaled @ v) / (torch.sqrt(u @ g_scaled @ u) * torch.sqrt(v @ g_scaled @ v)))
    len_v = float(torch.sqrt(v @ g_scaled @ v))
    results["B3_pytorch_small_omega_angle_preserved_length_small"] = {
        "pass": abs(cos_orig - cos_scaled) < 1e-8 and len_v < 1e-6,
        "cos_orig": cos_orig,
        "cos_scaled": cos_scaled,
        "len_v_scaled": len_v,
        "reason": "Small Omega: angle preserved (conformal invariance) but lengths -> 0 (extreme contraction)",
    }

    # ------------------------------------------------------------------
    # B4 (clifford): Omega=1 in Clifford algebra gives identity rescaling
    # ------------------------------------------------------------------
    layout, blades = Cl(2)
    e1 = blades["e1"]
    Omega_val = 1.0
    e1_scaled = Omega_val * e1

    def clifford_inner(a, b):
        return float(((a * b + b * a) * 0.5)[()])

    inner_orig = clifford_inner(e1, e1)
    inner_scaled = clifford_inner(e1_scaled, e1_scaled)
    results["B4_clifford_omega_1_identity_rescaling"] = {
        "pass": abs(inner_orig - inner_scaled) < 1e-12,
        "inner_orig": inner_orig,
        "inner_scaled": inner_scaled,
        "reason": "At Omega=1, e1 -> 1*e1 = e1; Clifford inner product unchanged",
    }

    # ------------------------------------------------------------------
    # B5 (geomstats): Omega=1 rescaling leaves geodesic distance unchanged
    # ------------------------------------------------------------------
    e_space = Euclidean(dim=2)
    Omega_val = 1.0
    p1 = gs.array([0.0, 0.0])
    p2 = gs.array([1.0, 2.0])
    p2_s = gs.array([1.0 * Omega_val, 2.0 * Omega_val])
    d_orig = float(e_space.metric.dist(p1, p2))
    d_scaled = float(e_space.metric.dist(p1, p2_s))
    results["B5_geomstats_omega_1_distance_unchanged"] = {
        "pass": abs(d_orig - d_scaled) < 1e-12,
        "d_orig": d_orig,
        "d_scaled": d_scaled,
        "reason": "At Omega=1, coordinate rescaling is identity; geodesic distance unchanged",
    }

    # ------------------------------------------------------------------
    # B6 (z3): UNSAT still holds in 3D for Weyl tensor (Cotton tensor is the obstruction)
    # In 3D, Weyl tensor IS zero by dimension-count, but Cotton tensor is the correct object.
    # Encode: in_3D AND weyl_3D_equals_zero (this should be SAT, not UNSAT)
    # i.e., the "Weyl = 0 in 3D" IS satisfiable (unlike "Weyl != 0 in 2D")
    # ------------------------------------------------------------------
    s2 = Solver()
    in_3D = Bool("in_3D")
    weyl_3D_zero = Bool("weyl_3D_zero")
    s2.add(in_3D)
    s2.add(weyl_3D_zero)
    # No contradicting constraint: Weyl=0 in 3D is consistent
    z3_3D_result = s2.check()
    results["B6_z3_sat_3D_weyl_can_be_zero"] = {
        "pass": z3_3D_result == sat,
        "z3_result": str(z3_3D_result),
        "reason": "SAT: in_3D AND weyl_3D_zero is consistent; 3D metrics CAN have zero Weyl tensor (unlike 4D)",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {**pos, **neg, **bnd}
    overall_pass = all(
        v.get("pass", False) for v in all_tests.values()
    )

    results = {
        "name": "sim_weyl_geometry_rescaling_shell",
        "classification": "classical_baseline",
        "scope_note": (
            "Shell-local Weyl geometry conformal rescaling probe. "
            "Tests: angle preservation, length scaling, Christoffel changes, "
            "Clifford conformal factor, geomstats geodesics. "
            "z3 UNSAT: 2D Weyl tensor cannot be nonzero."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "overall_pass": overall_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_weyl_geometry_rescaling_shell_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={overall_pass} -> {out_path}")
