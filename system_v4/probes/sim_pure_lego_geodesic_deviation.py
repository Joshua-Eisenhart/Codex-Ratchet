#!/usr/bin/env python3
"""
PURE LEGO: Geodesic Deviation — Jacobi Field Comparison (K=4 vs K=0)
=====================================================================
Bounded canonical probe for geodesic deviation behavior on two explicit
2D Riemannian manifolds, anchored to the curvature probe's K=4 result.

Manifolds:
  Curved: CP^1 / S^2 with Fubini-Study metric, K=4  (established by riemannian_curvature probe)
  Flat:   R^2 with Euclidean metric,          K=0

Jacobi equation for constant-K 2D manifold (scalar form along unit-speed geodesic):
  d²J/ds² + K · J = 0,   J(0) = 0,  J'(0) = 1

Exact solutions:
  Curved (K=4):  J_curved(s) = sin(2s) / 2    [√K = 2]
  Flat   (K=0):  J_flat(s)   = s               [linear growth]

Key geometric facts verified:
  - J_curved is bounded (max = 1/√K = 0.5), J_flat is unbounded
  - J_curved has first conjugate point at s = π/2 (geodesics reconverge)
  - J_flat has no conjugate point (geodesics diverge forever)
  - At s=π/4: J_curved = 0.5, J_flat = π/4 ≈ 0.785 — clearly distinct
  - At s=π/2: J_curved = 0,   J_flat = π/2 ≈ 1.571 — maximum separation

Numerical cross-check: torch.float64 RK4 ODE integrator verifies both solutions.
Symbolic cross-check:  sympy verifies ODE residual d²J/ds² + KJ = 0.

Anchors to: sim_pure_lego_riemannian_curvature.py (K=4 established there).
Out of scope: Levi-Civita connection details, Berry phase, Ricci flow,
              Einstein equations, higher-dimensional geodesics.
"""

import json
import math
import pathlib
from datetime import datetime, timezone

import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": "not needed for Jacobi ODE"},
    "z3":        {"tried": False, "used": False, "reason": "not needed; Jacobi equation has no logical branching"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed for Jacobi ODE"},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": "not needed; Jacobi equation is scalar on 2D manifold"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed; analytic Jacobi solutions computed directly"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed for Jacobi ODE"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for Jacobi ODE"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed for Jacobi ODE"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed for Jacobi ODE"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed for Jacobi ODE"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

_torch_ok = False
_sympy_ok = False

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    _torch_ok = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    _sympy_ok = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical lego for geodesic deviation: Jacobi field J_curved(s)=sin(2s)/2 on K=4 "
    "(Fubini-Study / S^2 radius 1/2) vs J_flat(s)=s on K=0 (flat R^2). "
    "PyTorch float64 RK4 ODE integrator is load-bearing for numerical cross-check. "
    "Sympy is load-bearing for symbolic ODE residual and initial-condition verification. "
    "Anchored to riemannian_curvature probe (K=4 established there)."
)

LEGO_IDS = ["geodesic_deviation_jacobi_curved_vs_flat"]
PRIMARY_LEGO_IDS = ["geodesic_deviation_jacobi_curved_vs_flat"]

# Curvature values — anchor to curvature probe result
K_CURVED = 4.0   # Fubini-Study Gaussian curvature
K_FLAT = 0.0     # Flat R^2

# Tolerances
J_VALUE_TOL = 1e-12   # Analytic Jacobi field values (exact float computation)
J_RK4_TOL = 1e-8      # RK4 numerical vs analytic (global error ~ 4e-11 for n=1000 steps)
J_CONJ_TOL = 1e-10    # Conjugate point near-zero check
J_FLAT_TOL = 1e-12    # Flat RK4: h=s/n_steps is irrational; accumulated O(N*eps) rounding ~3e-14, use 1e-12
J_SMALL_S_TOL = 1e-3  # Small-s flat approximation relative error < this; Taylor: 2s²/3 < 1e-3 for s<0.039

# Canonical test s values (radians)
S_TEST = [math.pi / 6, math.pi / 4, math.pi / 3, math.pi / 2]


# =====================================================================
# ANALYTIC JACOBI FIELDS
# =====================================================================

def J_curved(s: float) -> float:
    """
    Jacobi field for K=4 curved case.
    Solves d²J/ds² + 4J = 0, J(0)=0, J'(0)=1.
    J(s) = sin(2s) / 2.
    """
    return math.sin(2.0 * s) / 2.0


def dJ_curved(s: float) -> float:
    """Derivative J'_curved(s) = cos(2s)."""
    return math.cos(2.0 * s)


def J_flat(s: float) -> float:
    """
    Jacobi field for K=0 flat case.
    Solves d²J/ds² = 0, J(0)=0, J'(0)=1.
    J(s) = s.
    """
    return float(s)


def dJ_flat(s: float) -> float:
    """Derivative J'_flat(s) = 1 (constant)."""
    return 1.0


# =====================================================================
# TORCH RK4 ODE INTEGRATOR
# =====================================================================

def _rk4_step(K_t: "torch.Tensor", y: "torch.Tensor", h_t: "torch.Tensor") -> "torch.Tensor":
    """
    One RK4 step for the Jacobi ODE system:
      dy[0]/ds = y[1]        (J' = J_dot)
      dy[1]/ds = -K * y[0]  (J_dot' = -K*J)
    """
    def f(y_):
        return torch.stack([y_[1], -K_t * y_[0]])

    k1 = f(y)
    k2 = f(y + (h_t / 2) * k1)
    k3 = f(y + (h_t / 2) * k2)
    k4 = f(y + h_t * k3)
    return y + (h_t / 6) * (k1 + 2 * k2 + 2 * k3 + k4)


def rk4_jacobi_torch(K_val: float, s_target: float, n_steps: int = 1000) -> float:
    """
    Integrate the Jacobi ODE d²J/ds² + K·J = 0 on torch.float64 tensors
    from s=0 to s=s_target using RK4.

    Initial conditions: J(0)=0, J'(0)=1.
    Global RK4 error ≈ O(h⁴ · s_target) ≈ 4e-11 for n_steps=1000, s_target≤π.

    Returns float: J(s_target).
    """
    if s_target == 0.0:
        return 0.0
    K_t = torch.tensor(K_val, dtype=torch.float64)
    h = s_target / n_steps
    h_t = torch.tensor(h, dtype=torch.float64)
    y = torch.tensor([0.0, 1.0], dtype=torch.float64)
    for _ in range(n_steps):
        y = _rk4_step(K_t, y, h_t)
    return float(y[0])


# =====================================================================
# SYMPY SYMBOLIC VERIFICATION
# =====================================================================

def sympy_jacobi_checks():
    """
    Symbolic verification via sympy:
    1. J_curved = sin(2s)/2 satisfies d²J/ds² + 4J = 0 with J(0)=0, J'(0)=1.
    2. J_flat   = s          satisfies d²J/ds² = 0   with J(0)=0, J'(0)=1.
    3. First positive root of J_curved is s = π/2 (conjugate point).

    Returns dict of bool flags.
    """
    if not _sympy_ok:
        return {k: None for k in [
            "curved_ode_residual_zero", "flat_ode_residual_zero",
            "curved_ic0_ok", "curved_ic1_ok", "flat_ic0_ok", "flat_ic1_ok",
            "conjugate_point_pi_half",
        ]}

    s_sym = sp.Symbol("s", positive=True)

    J_c = sp.sin(2 * s_sym) / 2
    J_f = s_sym

    # ODE residuals
    res_c = sp.diff(J_c, s_sym, 2) + 4 * J_c   # should be 0
    res_f = sp.diff(J_f, s_sym, 2)              # should be 0

    curved_ode_ok = bool(sp.simplify(res_c) == 0)
    flat_ode_ok = bool(sp.simplify(res_f) == 0)

    # Initial conditions
    c_ic0 = abs(float(J_c.subs(s_sym, 0))) < 1e-15
    c_ic1 = abs(float(sp.diff(J_c, s_sym).subs(s_sym, 0)) - 1.0) < 1e-15
    f_ic0 = abs(float(J_f.subs(s_sym, 0))) < 1e-15
    f_ic1 = abs(float(sp.diff(J_f, s_sym).subs(s_sym, 0)) - 1.0) < 1e-15

    # Conjugate point: J_curved(π/2) = sin(π)/2 = 0
    conj_val = float(J_c.subs(s_sym, sp.pi / 2))
    conj_ok = abs(conj_val) < 1e-15

    return {
        "curved_ode_residual_zero": curved_ode_ok,
        "flat_ode_residual_zero": flat_ode_ok,
        "curved_ic0_ok": c_ic0,
        "curved_ic1_ok": c_ic1,
        "flat_ic0_ok": f_ic0,
        "flat_ic1_ok": f_ic1,
        "conjugate_point_pi_half": conj_ok,
        "curved_residual_str": str(sp.simplify(res_c)),
        "flat_residual_str": str(sp.simplify(res_f)),
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    Positive: verify analytic Jacobi fields match exact values; sympy confirms
    ODE residuals; RK4 confirms both solutions numerically.
    """
    results = {}

    # --- Curved Jacobi field values at canonical test points ---
    exact_curved = {
        "s_pi6": math.sqrt(3) / 4,      # sin(π/3)/2 = √3/4
        "s_pi4": 0.5,                    # sin(π/2)/2 = 1/2
        "s_pi3": math.sqrt(3) / 4,      # sin(2π/3)/2 = √3/4 (symmetric)
        "s_pi2": 0.0,                    # sin(π)/2 = 0 (conjugate point)
    }
    s_labels = ["s_pi6", "s_pi4", "s_pi3", "s_pi2"]
    curved_pts = {}
    for label, s_val in zip(s_labels, S_TEST):
        J_num = J_curved(s_val)
        J_exp = exact_curved[label]
        residual = abs(J_num - J_exp)
        curved_pts[label] = {
            "s": s_val,
            "J_numerical": J_num,
            "J_exact": J_exp,
            "residual": residual,
            "pass": residual < J_VALUE_TOL,
        }
    results["jacobi_curved_K4_value_checks"] = {
        "description": "J_curved(s)=sin(2s)/2 matches exact analytic values at four test points",
        "K": K_CURVED,
        "test_points": curved_pts,
        "pass": all(v["pass"] for v in curved_pts.values()),
    }

    # --- Flat Jacobi field values: J_flat(s) = s exactly ---
    flat_pts = {}
    for label, s_val in zip(s_labels, S_TEST):
        J_num = J_flat(s_val)
        J_exp = s_val  # exact: J_flat(s) = s
        residual = abs(J_num - J_exp)
        flat_pts[label] = {
            "s": s_val,
            "J_numerical": J_num,
            "J_exact": J_exp,
            "residual": residual,
            "pass": residual < 1e-15,
        }
    results["jacobi_flat_K0_value_checks"] = {
        "description": "J_flat(s)=s matches s exactly at four test points",
        "K": K_FLAT,
        "test_points": flat_pts,
        "pass": all(v["pass"] for v in flat_pts.values()),
    }

    # --- Sympy ODE residual and IC verification ---
    sym = sympy_jacobi_checks()
    sym_pass = (
        sym.get("curved_ode_residual_zero") is True
        and sym.get("flat_ode_residual_zero") is True
        and sym.get("curved_ic0_ok") is True
        and sym.get("curved_ic1_ok") is True
        and sym.get("flat_ic0_ok") is True
        and sym.get("flat_ic1_ok") is True
        and sym.get("conjugate_point_pi_half") is True
    )
    results["sympy_ode_residual_and_ic"] = {
        "description": (
            "Sympy confirms: d²J_curved/ds²+4*J_curved=0 and d²J_flat/ds²=0; "
            "both satisfy J(0)=0,J'(0)=1; J_curved(π/2)=0"
        ),
        "sympy_available": _sympy_ok,
        "checks": sym,
        "pass": sym_pass,
    }

    # --- RK4 numerical cross-check: curved case ---
    rk4_curved_pts = {}
    for label, s_val in zip(s_labels, S_TEST):
        J_rk4 = rk4_jacobi_torch(K_CURVED, s_val)
        J_ana = J_curved(s_val)
        residual = abs(J_rk4 - J_ana)
        rk4_curved_pts[label] = {
            "s": s_val,
            "J_rk4": J_rk4,
            "J_analytic": J_ana,
            "residual": residual,
            "pass": residual < J_RK4_TOL,
        }
    results["rk4_curved_cross_check"] = {
        "description": (
            "Torch float64 RK4 integration of d²J/ds²+4J=0 matches sin(2s)/2 "
            "within 1e-8 at four test points"
        ),
        "n_steps_per_target": 1000,
        "test_points": rk4_curved_pts,
        "pass": all(v["pass"] for v in rk4_curved_pts.values()),
    }

    # --- RK4 numerical cross-check: flat case (K=0) ---
    rk4_flat_pts = {}
    for label, s_val in zip(s_labels, S_TEST):
        J_rk4 = rk4_jacobi_torch(K_FLAT, s_val)
        J_ana = J_flat(s_val)
        residual = abs(J_rk4 - J_ana)
        rk4_flat_pts[label] = {
            "s": s_val,
            "J_rk4": J_rk4,
            "J_analytic": J_ana,
            "residual": residual,
            "pass": residual < J_FLAT_TOL,
        }
    results["rk4_flat_cross_check"] = {
        "description": (
            "Torch float64 RK4 integration of d²J/ds²=0 recovers J(s)=s exactly "
            "(O(N*eps) floating-point rounding from irrational h=s/n_steps; tolerance 1e-12)"
        ),
        "n_steps_per_target": 1000,
        "test_points": rk4_flat_pts,
        "pass": all(v["pass"] for v in rk4_flat_pts.values()),
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    Negative: verify the probe distinguishes curved from flat geometry;
    swap tests would fail here.
    """
    results = {}

    J_c_conj = J_curved(math.pi / 2)   # should be ~0
    J_f_conj = J_flat(math.pi / 2)     # should be π/2 ≈ 1.5708
    J_c_peak = J_curved(math.pi / 4)   # should be 0.5
    J_f_peak = J_flat(math.pi / 4)     # should be π/4 ≈ 0.7854

    # At the conjugate point, curved is (near) zero; flat is clearly nonzero
    results["curved_vanishes_at_conjugate_point"] = {
        "description": "J_curved(π/2) ≈ 0 — curved geodesics reconverge",
        "s": math.pi / 2,
        "J_curved": J_c_conj,
        "pass": abs(J_c_conj) < J_CONJ_TOL,
    }
    results["flat_nonzero_at_curved_conjugate_point"] = {
        "description": "J_flat(π/2) ≈ π/2 > 1.0 — flat geodesics still diverging",
        "s": math.pi / 2,
        "J_flat": J_f_conj,
        "pass": J_f_conj > 1.0,
    }

    # Curved and flat are distinguishable at the peak
    results["curved_and_flat_differ_at_peak"] = {
        "description": "J_curved(π/4)=0.5 ≠ J_flat(π/4)=π/4; differ by > 0.2",
        "s": math.pi / 4,
        "J_curved": J_c_peak,
        "J_flat": J_f_peak,
        "difference": abs(J_c_peak - J_f_peak),
        "pass": abs(J_c_peak - J_f_peak) > 0.2,
    }

    # Curved is bounded (max = 0.5); flat is not
    J_f_large = J_flat(10.0)
    J_c_large = J_curved(10.0)
    results["flat_unbounded_curved_bounded"] = {
        "description": "J_flat(10)=10 >> J_curved(10) ≤ 0.5; curved is bounded",
        "s": 10.0,
        "J_curved": J_c_large,
        "J_flat": J_f_large,
        "pass": J_f_large > 5.0 and abs(J_c_large) <= 0.5 + 1e-12,
    }

    # Curved has positive curvature sign (K=4 > 0); distinction from K=0
    results["K_curved_is_positive_K_flat_is_zero"] = {
        "description": "K_curved=4.0 > 0 and K_flat=0.0 — distinct curvature classes",
        "K_curved": K_CURVED,
        "K_flat": K_FLAT,
        "pass": K_CURVED > 0 and K_FLAT == 0.0,
    }

    # Curved Jacobi field oscillates; flat does not (monotone check)
    # J_curved at [0, π/4, π/2] = [0, 0.5, 0] — non-monotone
    J_c_seq = [J_curved(s) for s in [0.0, math.pi / 4, math.pi / 2]]
    not_monotone = J_c_seq[1] > J_c_seq[0] and J_c_seq[2] < J_c_seq[1]
    # J_flat at [0, π/4, π/2] = [0, π/4, π/2] — strictly increasing
    J_f_seq = [J_flat(s) for s in [0.0, math.pi / 4, math.pi / 2]]
    monotone = J_f_seq[0] < J_f_seq[1] < J_f_seq[2]
    results["curved_non_monotone_flat_monotone"] = {
        "description": "J_curved is non-monotone (oscillates); J_flat is strictly increasing",
        "J_curved_seq": J_c_seq,
        "J_flat_seq": J_f_seq,
        "curved_non_monotone": not_monotone,
        "flat_monotone": monotone,
        "pass": not_monotone and monotone,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Boundary: initial conditions, conjugate point precision, periodicity,
    near-origin flat approximation, derivative check at critical points.
    """
    results = {}

    # Initial conditions: both Jacobi fields start at 0 with unit rate
    results["initial_conditions_both_fields"] = {
        "description": "J_curved(0)=0, J_flat(0)=0; J'_curved(0)=1, J'_flat(0)=1",
        "J_curved_0": J_curved(0.0),
        "J_flat_0": J_flat(0.0),
        "dJ_curved_0": dJ_curved(0.0),
        "dJ_flat_0": dJ_flat(0.0),
        "pass": (
            abs(J_curved(0.0)) < 1e-15
            and abs(J_flat(0.0)) < 1e-15
            and abs(dJ_curved(0.0) - 1.0) < 1e-15
            and abs(dJ_flat(0.0) - 1.0) < 1e-15
        ),
    }

    # First conjugate point of J_curved: s = π/2, J = 0
    J_c_first_conj = J_curved(math.pi / 2)
    results["first_conjugate_point_at_pi_half"] = {
        "description": "J_curved(π/2) = sin(π)/2 ≈ 0 to floating-point precision",
        "s": math.pi / 2,
        "J_curved": J_c_first_conj,
        "pass": abs(J_c_first_conj) < J_CONJ_TOL,
    }

    # Second conjugate point: s = π, J = sin(2π)/2 = 0
    J_c_second_conj = J_curved(math.pi)
    results["second_conjugate_point_at_pi"] = {
        "description": "J_curved(π) = sin(2π)/2 ≈ 0 (second conjugate point)",
        "s": math.pi,
        "J_curved": J_c_second_conj,
        "pass": abs(J_c_second_conj) < J_CONJ_TOL,
    }

    # Maximum of J_curved: at s=π/4, J'=cos(π/2)=0, J=0.5
    J_c_max = J_curved(math.pi / 4)
    dJ_c_at_max = dJ_curved(math.pi / 4)
    results["jacobi_curved_maximum"] = {
        "description": "J_curved achieves maximum 0.5 at s=π/4 where J'=0",
        "s": math.pi / 4,
        "J_curved": J_c_max,
        "dJ_curved": dJ_c_at_max,
        "pass": abs(J_c_max - 0.5) < J_VALUE_TOL and abs(dJ_c_at_max) < J_VALUE_TOL,
    }

    # Derivative at reconvergence: J'_curved(π/2) = cos(π) = -1
    dJ_c_conj = dJ_curved(math.pi / 2)
    results["jacobi_curved_derivative_at_conjugate"] = {
        "description": "J'_curved(π/2) = cos(π) = -1 (geodesics reconverging at rate 1)",
        "s": math.pi / 2,
        "dJ_curved": dJ_c_conj,
        "pass": abs(dJ_c_conj - (-1.0)) < J_VALUE_TOL,
    }

    # Small-s flat approximation: near origin, J_curved ≈ J_flat (sin(x)≈x for small x)
    # Taylor error = 2s²/3; at s=0.02: error ≈ 2.67e-4 < 1e-3 ✓; at s=0.05: error ≈ 1.67e-3 (fails)
    s_small = 0.02
    J_c_small = J_curved(s_small)
    J_f_small = J_flat(s_small)
    rel_diff = abs(J_c_small - J_f_small) / J_f_small
    results["small_s_flat_approximation"] = {
        "description": "Near origin, J_curved ≈ J_flat (sin(2s)/2 ≈ s for small s)",
        "s": s_small,
        "J_curved": J_c_small,
        "J_flat": J_f_small,
        "relative_difference": rel_diff,
        "pass": rel_diff < J_SMALL_S_TOL,
    }

    # RK4 conjugate point check: numerical integrator also sees J≈0 at s=π/2
    J_rk4_conj = rk4_jacobi_torch(K_CURVED, math.pi / 2)
    results["rk4_curved_at_conjugate_point"] = {
        "description": "RK4 integration also recovers J≈0 at conjugate point s=π/2",
        "s": math.pi / 2,
        "J_rk4": J_rk4_conj,
        "pass": abs(J_rk4_conj) < J_RK4_TOL,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

def main():
    if not _torch_ok:
        raise RuntimeError("PyTorch required for RK4 ODE cross-check but not installed.")

    # Update tool manifest with actual usage
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Load-bearing: RK4 ODE integration of Jacobi equation d²J/ds²+KJ=0 runs on "
        "torch.float64 tensors; all RK4 arithmetic (k1..k4, state update) is torch operations."
    )
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"

    if _sympy_ok:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "Load-bearing: symbolic ODE residual check (d²J/ds²+4J=0 simplifies to 0), "
            "initial condition verification, and conjugate-point confirmation (J_curved(π/2)=0) "
            "are sympy-computed analytic ground truths that the numerical tests are calibrated against."
        )
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    else:
        TOOL_MANIFEST["sympy"]["reason"] = "not installed; symbolic ODE check skipped"

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    def _all_pass(section):
        return all(v["pass"] for v in section.values())

    all_pass = _all_pass(positive) and _all_pass(negative) and _all_pass(boundary)

    results = {
        "name": "geodesic_deviation_jacobi_curved_vs_flat",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "manifolds": {
                "curved": "CP^1 / S^2 with Fubini-Study metric, K=4 (from riemannian_curvature probe)",
                "flat": "R^2 with Euclidean metric, K=0",
            },
            "jacobi_solutions": {
                "curved": "J(s) = sin(2s)/2,  first conjugate at s=π/2",
                "flat":   "J(s) = s,           no conjugate point",
            },
            "key_distinction": (
                "Curved geodesics reconverge at s=π/2 (J=0); "
                "flat geodesics diverge linearly forever."
            ),
            "scope_note": (
                "Geodesic deviation probe: scalar Jacobi equation on 2D constant-K manifolds. "
                "Anchored to riemannian_curvature probe (K=4). "
                "Out of scope: Levi-Civita connection tensor, Berry phase, Ricci flow, "
                "sectional curvature tensor, higher-dimensional Jacobi fields."
            ),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "geodesic_deviation_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
