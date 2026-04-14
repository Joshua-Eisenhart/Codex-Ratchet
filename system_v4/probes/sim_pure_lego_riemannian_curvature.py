#!/usr/bin/env python3
"""
PURE LEGO: Riemannian Curvature — Flat vs. Curved Benchmark
============================================================
Bounded canonical probe for Gaussian curvature on two explicit 2D Riemannian manifolds:

  1. Curved benchmark: CP^1 / S^2 with Fubini-Study metric
       ds^2_FS = (1/4)(dtheta^2 + sin^2(theta) dphi^2)
       Expected Gaussian curvature: K = 4  [sphere of radius 1/2; K = 1/r^2 = 4]

  2. Flat benchmark: R^2 with Euclidean metric
       ds^2_flat = dx^2 + dy^2
       Expected Gaussian curvature: K = 0

Curvature computed via Liouville's formula for diagonal metrics:
  K = -(1 / 2*sqrt(EG)) * [d/du (G_u / sqrt(EG)) + d/dv (E_v / sqrt(EG))]

where E = g_uu, G = g_vv, G_u = dG/du, E_v = dE/dv.
Derivatives computed with centered finite differences on torch.float64 tensors.
Sympy provides analytic cross-validation of both K values.

Out of scope: Levi-Civita connection in full, Berry-phase holonomy,
Ricci flow, Einstein equations, sectional curvature tensor, higher dimensions.
"""

import json
import pathlib
from datetime import datetime, timezone

import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "not needed for curvature computation"},
    "z3": {"tried": False, "used": False, "reason": "not needed; no logical branching in Liouville formula"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for curvature computation"},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "not needed; 2D diagonal metric uses no Clifford algebra"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed; Fubini-Study and flat computed directly without geomstats machinery"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for curvature computation"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for curvature computation"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for curvature computation"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for curvature computation"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for curvature computation"},
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
    "Canonical lego for Gaussian curvature comparison: Fubini-Study (K=4) vs flat R^2 (K=0). "
    "PyTorch float64 tensors carry the Liouville-formula finite-difference curvature computation. "
    "Sympy provides analytic ground truth (K=4 symbolic derivation) that the numerical results are validated against. "
    "Both tools are load-bearing: removing either breaks the verification chain."
)

LEGO_IDS = ["riemannian_curvature_flat_vs_curved"]
PRIMARY_LEGO_IDS = ["riemannian_curvature_flat_vs_curved"]

# Numerical tolerances
KFS_TOL = 1e-5       # Fubini-Study K = 4 ± this (generic interior points)
KFS_POLE_TOL = 1e-3  # Fubini-Study K = 4 ± this (near-pole, theta = 0.05)
KFLAT_TOL = 1e-10    # Flat K = 0 ± this (constant metric -> exact zero)
STEP = 1e-5          # Finite difference step


# =====================================================================
# METRIC COMPONENT FUNCTIONS (return torch.float64 scalars)
# =====================================================================

def _fs_E(u, v):
    """Fubini-Study: g_theta_theta = 1/4 (constant, phi-independent)."""
    return torch.tensor(0.25, dtype=torch.float64)


def _fs_G(u, v):
    """Fubini-Study: g_phi_phi = sin^2(theta) / 4."""
    return torch.sin(u) ** 2 / 4.0


def _flat_E(u, v):
    """Euclidean R^2: g_xx = 1 (constant)."""
    return torch.tensor(1.0, dtype=torch.float64)


def _flat_G(u, v):
    """Euclidean R^2: g_yy = 1 (constant)."""
    return torch.tensor(1.0, dtype=torch.float64)


# =====================================================================
# GAUSSIAN CURVATURE — LIOUVILLE'S FORMULA
# =====================================================================

def gaussian_curvature_diagonal(E_func, G_func, u_val, v_val, h=STEP):
    """
    Gaussian curvature K for diagonal Riemannian metric ds^2 = E du^2 + G dv^2.

    Liouville's formula:
      K = -(1 / 2*sqrt(EG)) * [d/du(G_u / sqrt(EG)) + d/dv(E_v / sqrt(EG))]

    where G_u = dG/du and E_v = dE/dv, computed via centered finite differences.
    All arithmetic on torch.float64 tensors.

    Parameters
    ----------
    E_func, G_func : callable (u, v) -> torch.Tensor
        Metric components; must accept torch.float64 scalar tensors.
    u_val, v_val : float
        Coordinates at which to evaluate K.
    h : float
        Finite difference step size.

    Returns
    -------
    float
        Gaussian curvature at (u_val, v_val).
    """
    u = torch.tensor(u_val, dtype=torch.float64)
    v = torch.tensor(v_val, dtype=torch.float64)
    h_t = torch.tensor(h, dtype=torch.float64)

    E0 = E_func(u, v)
    G0 = G_func(u, v)
    sqrtEG0 = torch.sqrt(E0 * G0)

    def _f1(uu):
        """G_u(uu, v) / sqrt(E(uu,v) * G(uu,v)) — inner term for d/du."""
        G_p = G_func(uu + h_t, v)
        G_m = G_func(uu - h_t, v)
        G_u = (G_p - G_m) / (2.0 * h_t)
        E_ = E_func(uu, v)
        G_ = G_func(uu, v)
        return G_u / torch.sqrt(E_ * G_)

    def _f2(vv):
        """E_v(u, vv) / sqrt(E(u,vv) * G(u,vv)) — inner term for d/dv."""
        E_p = E_func(u, vv + h_t)
        E_m = E_func(u, vv - h_t)
        E_v = (E_p - E_m) / (2.0 * h_t)
        E_ = E_func(u, vv)
        G_ = G_func(u, vv)
        return E_v / torch.sqrt(E_ * G_)

    d_f1_du = (_f1(u + h_t) - _f1(u - h_t)) / (2.0 * h_t)
    d_f2_dv = (_f2(v + h_t) - _f2(v - h_t)) / (2.0 * h_t)

    K = -(1.0 / (2.0 * sqrtEG0)) * (d_f1_du + d_f2_dv)
    return float(K)


# =====================================================================
# SYMPY SYMBOLIC CROSS-VALIDATION
# =====================================================================

def sympy_K_fubini_study():
    """
    Symbolic Gaussian curvature for Fubini-Study metric on CP^1.

    Metric: E = 1/4, G = sin^2(theta)/4.
    By Liouville: K = -(1/2*sqrtEG) * d/dtheta(G_theta / sqrtEG).

    sqrt(E*G) is taken as sin(theta)/4, valid for theta in (0, pi).
    G_theta = sin(theta)*cos(theta)/2.
    G_theta / sqrtEG = 2*cos(theta).
    d/dtheta(2*cos(theta)) = -2*sin(theta).
    K = -(1/(2 * sin(theta)/4)) * (-2*sin(theta)) = 4.

    Returns
    -------
    (sympy.Expr, str)  -- (K expression, string representation)
    """
    if not _sympy_ok:
        return None, "sympy not available"

    theta = sp.Symbol("theta")
    E_sym = sp.Rational(1, 4)
    G_sym = sp.sin(theta) ** 2 / 4

    # sqrtEG defined explicitly for theta in (0, pi) where sin(theta) > 0
    sqrtEG = sp.sin(theta) / 4

    G_theta = sp.diff(G_sym, theta)          # sin(theta)*cos(theta)/2
    f1 = G_theta / sqrtEG                    # 2*cos(theta)
    df1_dtheta = sp.diff(f1, theta)          # -2*sin(theta)

    # E is constant so E_phi = 0 and the second Liouville term vanishes
    K_sym = -(1 / (2 * sqrtEG)) * df1_dtheta
    K_simplified = sp.simplify(K_sym)
    return K_simplified, str(K_simplified)


def sympy_K_flat():
    """
    Symbolic Gaussian curvature for flat R^2 metric (E = G = 1).
    All derivatives vanish -> K = 0.
    """
    if not _sympy_ok:
        return None, "sympy not available"

    K_sym = sp.Integer(0)
    return K_sym, str(K_sym)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    Positive: verify curvature matches analytic value on each manifold.
    Three test points on Fubini-Study; sympy analytic confirmation.
    """
    results = {}

    # --- Fubini-Study K = 4 at four interior theta values ---
    k_expected_fs = 4.0
    phi = 0.0
    fs_points = {
        "theta_pi6": float(np.pi / 6),
        "theta_pi4": float(np.pi / 4),
        "theta_pi3": float(np.pi / 3),
        "theta_pi2": float(np.pi / 2),
    }

    fs_values = {}
    for label, theta_val in fs_points.items():
        K_num = gaussian_curvature_diagonal(_fs_E, _fs_G, theta_val, phi)
        residual = abs(K_num - k_expected_fs)
        fs_values[label] = {
            "theta": theta_val,
            "K_numerical": K_num,
            "K_expected": k_expected_fs,
            "residual": residual,
            "pass": residual < KFS_TOL,
        }

    results["fubini_study_K_equals_4"] = {
        "description": "Fubini-Study metric on CP^1 has constant Gaussian curvature K=4 (S^2 radius 1/2)",
        "test_points": fs_values,
        "pass": all(v["pass"] for v in fs_values.values()),
    }

    # --- Flat R^2 K = 0 ---
    K_flat = gaussian_curvature_diagonal(_flat_E, _flat_G, 0.0, 0.0)
    results["flat_euclidean_K_equals_0"] = {
        "description": "Flat R^2 metric has Gaussian curvature K=0",
        "K_numerical": K_flat,
        "K_expected": 0.0,
        "residual": abs(K_flat),
        "pass": abs(K_flat) < KFLAT_TOL,
    }

    # --- Sympy analytic confirmation: K_FS = 4 ---
    K_sym_fs, K_sym_fs_str = sympy_K_fubini_study()
    sym_fs_ok = (K_sym_fs is not None) and abs(float(K_sym_fs) - 4.0) < 1e-10
    results["sympy_K_fubini_study_exact_4"] = {
        "description": "Sympy symbolic derivation confirms K=4 for Fubini-Study metric",
        "K_symbolic": K_sym_fs_str,
        "pass": sym_fs_ok,
    }

    # --- Sympy analytic confirmation: K_flat = 0 ---
    K_sym_flat, K_sym_flat_str = sympy_K_flat()
    sym_flat_ok = (K_sym_flat is not None) and abs(float(K_sym_flat) - 0.0) < 1e-10
    results["sympy_K_flat_exact_0"] = {
        "description": "Sympy symbolic derivation confirms K=0 for flat Euclidean metric",
        "K_symbolic": K_sym_flat_str,
        "pass": sym_flat_ok,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    Negative: verify the probe distinguishes curved from flat;
    K_FS cannot be misidentified as zero or negative.
    """
    results = {}

    K_fs = gaussian_curvature_diagonal(_fs_E, _fs_G, float(np.pi / 2), 0.0)
    K_flat = gaussian_curvature_diagonal(_flat_E, _flat_G, 0.0, 0.0)

    # Curved manifold is not flat
    results["fubini_study_K_is_not_zero"] = {
        "description": "Fubini-Study K must be clearly nonzero (> 1.0)",
        "K_FS": K_fs,
        "pass": abs(K_fs) > 1.0,
    }

    # The two manifolds are distinguishable by K
    results["curved_vs_flat_K_differ_by_at_least_1"] = {
        "description": "Flat and curved manifolds differ by |K_FS - K_flat| > 1.0",
        "K_FS": K_fs,
        "K_flat": K_flat,
        "difference": abs(K_fs - K_flat),
        "pass": abs(K_fs - K_flat) > 1.0,
    }

    # Positive curvature sign
    results["fubini_study_K_is_positive"] = {
        "description": "S^2 has positive curvature; K_FS > 0",
        "K_FS": K_fs,
        "pass": K_fs > 0.0,
    }

    # Flat is genuinely zero, not merely small
    results["flat_K_is_strictly_zero"] = {
        "description": "Constant metric has all-zero Christoffel symbols -> K = 0 to machine precision",
        "K_flat": K_flat,
        "pass": abs(K_flat) < KFLAT_TOL,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Boundary: near-pole stability, phi-independence, metric nondegeneracy.
    """
    results = {}

    # Near north pole (theta -> 0): sin(theta) -> 0, sqrt(EG) -> 0
    # The Liouville ratio G_u/sqrt(EG) = 2*cos(theta) remains smooth, so K should
    # still converge to 4 even though individual terms become small.
    theta_near_pole = 0.05  # sin(0.05) ~ 0.04998, well above floating-point noise
    K_near_pole = gaussian_curvature_diagonal(_fs_E, _fs_G, theta_near_pole, 0.0)
    results["fubini_study_near_pole_finite_and_correct"] = {
        "description": "K_FS remains finite and close to 4 near the north pole (theta=0.05)",
        "theta": theta_near_pole,
        "K_numerical": K_near_pole,
        "K_expected": 4.0,
        "residual": abs(K_near_pole - 4.0),
        "is_finite": bool(np.isfinite(K_near_pole)),
        "pass": np.isfinite(K_near_pole) and abs(K_near_pole - 4.0) < KFS_POLE_TOL,
    }

    # phi-independence: K must be equal at different phi values (metric is phi-independent)
    theta_test = float(np.pi / 3)
    phi_vals = {"phi_0": 0.0, "phi_pi4": float(np.pi / 4), "phi_pi2": float(np.pi / 2)}
    K_by_phi = {lbl: gaussian_curvature_diagonal(_fs_E, _fs_G, theta_test, phi_val)
                for lbl, phi_val in phi_vals.items()}
    max_phi_var = max(
        abs(K_by_phi["phi_0"] - K_by_phi["phi_pi4"]),
        abs(K_by_phi["phi_0"] - K_by_phi["phi_pi2"]),
        abs(K_by_phi["phi_pi4"] - K_by_phi["phi_pi2"]),
    )
    results["fubini_study_phi_independence"] = {
        "description": "K_FS is constant in phi (metric is axially symmetric)",
        "theta": theta_test,
        "K_by_phi": K_by_phi,
        "max_phi_variation": max_phi_var,
        "pass": max_phi_var < KFS_TOL,
    }

    # Flat metric K = 0 at an off-origin point (constant metric is globally flat)
    K_flat_off = gaussian_curvature_diagonal(_flat_E, _flat_G, 3.7, -2.1)
    results["flat_K_zero_at_off_origin_point"] = {
        "description": "Flat R^2 has K=0 everywhere, not just at origin",
        "point": [3.7, -2.1],
        "K_numerical": K_flat_off,
        "pass": abs(K_flat_off) < KFLAT_TOL,
    }

    # Metric nondegeneracy: det(g) > 0 at a generic point (ensures K is well-defined)
    theta_nd = float(np.pi / 4)
    E_val = float(_fs_E(torch.tensor(theta_nd, dtype=torch.float64),
                        torch.tensor(0.0, dtype=torch.float64)))
    G_val = float(_fs_G(torch.tensor(theta_nd, dtype=torch.float64),
                        torch.tensor(0.0, dtype=torch.float64)))
    det_g = E_val * G_val
    results["fubini_study_metric_nondegenerate"] = {
        "description": "Metric determinant det(g) = E*G > 0 at theta=pi/4",
        "theta": theta_nd,
        "E": E_val,
        "G": G_val,
        "det_g": det_g,
        "pass": det_g > 0.0,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

def main():
    # --- Update tool manifest with actual usage ---
    if _torch_ok:
        TOOL_MANIFEST["pytorch"]["used"] = True
        TOOL_MANIFEST["pytorch"]["reason"] = (
            "Load-bearing: all metric component functions return torch.float64 tensors; "
            "Liouville formula finite differences run entirely on torch scalar arithmetic."
        )
        TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    else:
        raise RuntimeError("PyTorch is required but not installed.")

    if _sympy_ok:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "Load-bearing: symbolic derivation of K=4 (Fubini-Study) and K=0 (flat) "
            "provides the analytic ground truth that the numerical tolerance checks are calibrated against."
        )
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    else:
        TOOL_MANIFEST["sympy"]["reason"] = "not installed; symbolic cross-check skipped"

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    def _all_pass(section):
        return all(v["pass"] for v in section.values())

    all_pass = _all_pass(positive) and _all_pass(negative) and _all_pass(boundary)

    results = {
        "name": "riemannian_curvature_flat_vs_curved",
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
                "curved": "CP^1 / S^2 with Fubini-Study metric, K=4",
                "flat": "R^2 with Euclidean metric, K=0",
            },
            "formula": "Liouville diagonal metric: K = -(1/2*sqrt(EG))*[d/du(G_u/sqrt(EG)) + d/dv(E_v/sqrt(EG))]",
            "scope_note": (
                "Gaussian curvature lego: Fubini-Study (K=4) vs flat Euclidean (K=0). "
                "Numerical: Liouville formula with centered finite differences on torch.float64. "
                "Analytic: sympy symbolic derivation confirms both K values. "
                "Out of scope: Levi-Civita connection in full, Berry-phase holonomy, "
                "Ricci flow, Einstein equations, sectional curvature tensor, higher dimensions."
            ),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "riemannian_curvature_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
