#!/usr/bin/env python3
"""
sim_pure_lego_pairwise_shell_coupling_cp1.py
============================================
First pairwise shell coupling probe for CP^1 / S² geometry.

Tests whether pairs of shell-local CP^1 geometry ingredients are mutually
compatible or incompatible, using three explicit coupling functionals.
This is step 2 of the coupling program (pairwise coupling), anchored to
the established canonical step-1 shell-local probes.

Coupling types
--------------
1. Jacobi-Curvature:
     C_J(K, J) = max_{s ∈ T} |J''(s) + K·J(s)|
   Tests whether Jacobi field J satisfies the ODE d²J/ds² + K·J = 0
   for the given curvature K.

2. Gauss-Bonnet area:
     C_GB(K, f) = |K · ∫₀^π ∫₀^{2π} f(θ) dθ dφ − 4π|
   Tests whether area element f(θ)dθdφ is the correct area element
   for curvature K on a genus-0 compact surface (χ=2).

3. Conjugate-point:
     C_CP(K, s*) = |K · (s*)² − π²|
   Tests whether conjugate point s* is consistent with curvature K
   via the identity s* = π/√K ↔ K·(s*)² = π².

Test cases
----------
Positive (compatible — coupling_value ≈ 0):
  P1. (K=4, J_curved=sin(2s)/2):  C_J = 0  [Jacobi ODE satisfied]
  P2. (K=4, dA_FS=sin(θ)/4 dθdφ): C_GB = 0 [Gauss-Bonnet satisfied]
  P3. (K=4, s*=π/2):              C_CP = 0  [conjugate-point identity]

Negative (incompatible — coupling_value >> 0):
  N1. (K=4, J_flat=s):            C_J ≈ 2π  [flat field fails curved ODE]
  N2. (K=4, dA_sphere=sin(θ)dθdφ): C_GB ≈ 12π [wrong area element]
  N3. (K=4, s*=π/4):              C_CP ≈ 3π²/4 [wrong conjugate point]

Boundary:
  B1. (K=0, J_flat=s):    flat limit — self-consistent at K=0, degenerate
  B2. (K=4, dA_hemi):     hemisphere — open manifold, GB deficit = 2π

Anchored to
-----------
- riemannian_curvature probe:   K=4 (Fubini-Study, Liouville formula)
- geodesic_deviation probe:     J_curved=sin(2s)/2, conjugate at s=π/2
- gauss_bonnet_cp1 probe:       area=π, ∫K dA=4π (GL residual <1e-10)

Out of scope: multi-shell coexistence (step 3), bridge claims (step 6),
full layer coupling matrix, Berry phase, QFI, Axis 6.
"""

import json
import math
import datetime

import torch
import sympy as sp

# ─── canonical contract fields ────────────────────────────────────────────────
CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical pairwise shell coupling probe for CP^1/S² geometry. "
    "Three coupling functionals (Jacobi-curvature, Gauss-Bonnet area, "
    "conjugate-point) each tested on compatible, incompatible, and boundary "
    "ingredient pairs. PyTorch float64 is load-bearing: all coupling residuals "
    "computed as torch.float64 operations (Jacobi ODE residuals at 4 test points, "
    "GB area integrals via torch.trapezoid on 2000-point grids, conjugate-point "
    "identity via torch scalar arithmetic). Sympy is load-bearing: symbolic "
    "verification that d²J/ds²+4J=0 for J=sin(2s)/2 (residual simplifies to 0), "
    "that d²J/ds²+4J=4s for J=s (incompatible), that ∫sin(θ)/4 dθdφ=π (exact), "
    "and that K·(π/√K)²=π² for all K>0 (symbolic identity). "
    "Anchored to riemannian_curvature (K=4), geodesic_deviation (J_curved), "
    "and gauss_bonnet_cp1 (area=π, ∫K dA=4π)."
)
LEGO_IDS = [
    "pairwise_coupling_jacobi_curvature_cp1",
    "pairwise_coupling_gauss_bonnet_area_cp1",
    "pairwise_coupling_conjugate_point_cp1",
]
PRIMARY_LEGO_IDS = ["pairwise_coupling_jacobi_curvature_cp1"]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "Load-bearing: torch.float64 tensors carry all coupling residuals. "
            "Jacobi ODE residuals |J''(s)+K·J(s)| computed as torch operations at "
            "4 test points s∈{π/6, π/4, π/3, π/2}. Gauss-Bonnet area integrals "
            "computed via torch.trapezoid on 2000-point float64 linspace grids. "
            "Conjugate-point residuals |K·(s*)²−π²| computed as torch scalar arithmetic. "
            "Removing torch breaks all numerical coupling computations."
        ),
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "not needed; pairwise geometric coupling has no graph structure",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": (
            "tried conceptually; not used — coupling residuals involve π (transcendental), "
            "incompatible with z3 LIRA rational arithmetic; sympy handles the symbolic layer"
        ),
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "not needed; transcendental values preclude SMT verification here",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": (
            "Load-bearing: sp.simplify(d²J/ds²+4·J) = 0 confirmed for J=sin(2s)/2 "
            "(Jacobi ODE residual exactly zero — provides analytic ground truth). "
            "sp.simplify(d²J/ds²+4·J−4s) = 0 confirmed for J=s (incompatible case). "
            "sp.integrate(sin(θ)/4, θ∈[0,π])×2π = π confirmed (Fubini-Study area). "
            "sp.simplify(K·(π/√K)²−π²) = 0 confirmed for all symbolic K>0 "
            "(conjugate-point universal identity). All sympy results are the analytic "
            "ground truth that torch numerical values are calibrated against."
        ),
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "not needed; no spinor structure in scalar curvature-Jacobi coupling",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not needed; coupling functionals computed directly from analytic formulas",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not needed; no equivariant structure in CP^1 scalar coupling",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "not needed; no graph structure in pairwise geometric coupling",
    },
    "xgi": {
        "tried": False,
        "used": False,
        "reason": "not needed; no hypergraph structure",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "not needed; Euler characteristic χ=2 used as known S² fact, no complex construction",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "not needed; no persistent homology",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": "load_bearing",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# ─── coupling thresholds ──────────────────────────────────────────────────────
# Jacobi ODE: analytic residuals are exact — 0 for compatible, 4s for J_flat
JACOBI_COMPAT_TOL = 1e-10   # compatible: max|J''+K·J| < this
JACOBI_INCOMPAT_THR = 1.0   # incompatible: max|J''+K·J| > this

# Gauss-Bonnet area: trapezoidal O(h²) error ~2.6e-6 at n=2000
# Matches GB_TOL_TRAP=1e-5 established in gauss_bonnet_cp1 probe
GB_COMPAT_TOL = 1e-5        # compatible: |K·area − 4π| < this
GB_INCOMPAT_THR = 5.0       # incompatible: |K·area − 4π| > this

# Conjugate-point: K·(π/2)²=π² to float64 machine epsilon
CONJ_COMPAT_TOL = 1e-10     # compatible: |K·(s*)²−π²| < this
CONJ_INCOMPAT_THR = 1.0     # incompatible: |K·(s*)²−π²| > this

# Boundary range for hemisphere case: 2π ≈ 6.28 expected
BOUNDARY_LO = 1.0
BOUNDARY_HI = 20.0

# Test points for Jacobi coupling
S_TEST = [math.pi / 6, math.pi / 4, math.pi / 3, math.pi / 2]


# ─── analytic Jacobi field functions (NOT finite-difference — exact formulas) ─
# J_curved(s) = sin(2s)/2   →   J''(s) = d²/ds²[sin(2s)/2] = -2sin(2s)
def _J_curved(s: float) -> float:    return math.sin(2.0 * s) / 2.0
def _Jpp_curved(s: float) -> float:  return -2.0 * math.sin(2.0 * s)

# J_flat(s) = s              →   J''(s) = 0
def _J_flat(s: float) -> float:      return float(s)
def _Jpp_flat(s: float) -> float:    return 0.0


# ─── area element functions (for Gauss-Bonnet coupling) ───────────────────────
def _dA_fubini_study(theta: torch.Tensor) -> torch.Tensor:
    """dA = sin(θ)/4 dθ dφ  (Fubini-Study metric on CP^1, radius r=1/2)."""
    return torch.sin(theta) / 4.0

def _dA_sphere_r1(theta: torch.Tensor) -> torch.Tensor:
    """dA = sin(θ) dθ dφ  (standard unit sphere, radius r=1, WRONG for CP^1)."""
    return torch.sin(theta)

def _dA_hemisphere(theta: torch.Tensor) -> torch.Tensor:
    """dA = sin(θ)/4 for θ∈[0,π/2], 0 otherwise (open upper hemisphere)."""
    mask = (theta <= math.pi / 2 + 1e-12).to(torch.float64)
    return (torch.sin(theta) / 4.0) * mask


# ─── coupling functional: Jacobi-Curvature ───────────────────────────────────
def _jacobi_coupling(K_val: float, J_fn, Jpp_fn) -> dict:
    """
    C_J(K, J) = max_{s∈T} |J''(s) + K·J(s)|

    Second derivatives are computed analytically via Jpp_fn (NOT finite differences).
    """
    K_t = torch.tensor(K_val, dtype=torch.float64)
    point_results = {}
    residuals = []
    for s in S_TEST:
        s_t = torch.tensor(s, dtype=torch.float64)
        J_val = torch.tensor(J_fn(s), dtype=torch.float64)
        Jpp_val = torch.tensor(Jpp_fn(s), dtype=torch.float64)
        r = float(torch.abs(Jpp_val + K_t * J_val))
        residuals.append(r)
        point_results[f"s_{round(s, 6)}"] = {
            "s": s,
            "J": float(J_val),
            "Jpp": float(Jpp_val),
            "Jpp_plus_KJ": float(Jpp_val + K_t * J_val),
            "residual": r,
        }

    coupling_value = max(residuals)
    return {
        "coupling_type": "jacobi_curvature",
        "K": K_val,
        "s_test_points": S_TEST,
        "point_residuals": point_results,
        "coupling_value": coupling_value,
    }


# ─── coupling functional: Gauss-Bonnet area ──────────────────────────────────
def _gb_area_coupling(K_val: float, dA_fn, n_theta: int = 2000) -> dict:
    """
    C_GB(K, f) = |K · ∫₀^π ∫₀^{2π} f(θ)dθdφ − 4π|

    Area integration via torch.trapezoid on float64 linspace grids.
    φ integral is exact × 2π (integrand is φ-independent for axially symmetric f).
    """
    theta = torch.linspace(0.0, float(torch.pi), n_theta, dtype=torch.float64)
    dA_vals = dA_fn(theta)
    area_theta = torch.trapezoid(dA_vals, theta)
    area_total = float(area_theta) * 2.0 * math.pi

    K_times_area = K_val * area_total
    target = 4.0 * math.pi
    coupling_value = abs(K_times_area - target)

    return {
        "coupling_type": "gauss_bonnet_area",
        "K": K_val,
        "n_theta": n_theta,
        "area_numerical": area_total,
        "K_times_area": K_times_area,
        "expected_4pi": target,
        "coupling_value": coupling_value,
    }


# ─── coupling functional: Conjugate-Point ────────────────────────────────────
def _conj_point_coupling(K_val: float, s_star: float) -> dict:
    """
    C_CP(K, s*) = |K · (s*)² − π²|

    Universal identity: s* = π/√K ⟺ K·(s*)² = π² for any K > 0.
    """
    K_t = torch.tensor(K_val, dtype=torch.float64)
    s_t = torch.tensor(s_star, dtype=torch.float64)
    pi_t = torch.tensor(math.pi, dtype=torch.float64)
    K_ssq = float(K_t * s_t ** 2)
    pi_sq = float(pi_t ** 2)
    coupling_value = abs(K_ssq - pi_sq)

    return {
        "coupling_type": "conjugate_point",
        "K": K_val,
        "s_star": s_star,
        "s_star_expected": math.pi / math.sqrt(K_val) if K_val > 0 else None,
        "K_times_s_star_sq": K_ssq,
        "pi_sq": pi_sq,
        "coupling_value": coupling_value,
    }


# ─── sympy verification layer ─────────────────────────────────────────────────
def _run_sympy_checks() -> dict:
    s_sym, K_sym = sp.symbols("s K", positive=True)
    theta_sym, phi_sym = sp.symbols("theta phi", real=True)
    results = {}

    # S1: Jacobi ODE residual for curved case (K=4, J=sin(2s)/2)
    J_c = sp.sin(2 * s_sym) / 2
    Jpp_c = sp.diff(J_c, s_sym, 2)   # = -2·sin(2s)
    res_c = sp.simplify(Jpp_c + 4 * J_c)
    results["jacobi_curved_ode_residual"] = {
        "J_sym": str(J_c),
        "Jpp_sym": str(Jpp_c),
        "Jpp_plus_4J": str(res_c),
        "is_zero": bool(res_c == 0),
        "pass": bool(res_c == 0),
    }

    # S2: Jacobi ODE residual for flat case (K=4, J=s) — should give 4s
    J_f = s_sym
    Jpp_f = sp.diff(J_f, s_sym, 2)   # = 0
    res_f = sp.simplify(Jpp_f + 4 * J_f)
    results["jacobi_flat_ode_residual_K4"] = {
        "J_sym": str(J_f),
        "Jpp_sym": str(Jpp_f),
        "Jpp_plus_4J": str(res_f),
        "equals_4s": bool(sp.simplify(res_f - 4 * s_sym) == 0),
        "pass": bool(sp.simplify(res_f - 4 * s_sym) == 0),
    }

    # S3: Area integral for Fubini-Study area element
    area_fs = sp.integrate(
        sp.integrate(sp.sin(theta_sym) / 4, (theta_sym, 0, sp.pi)),
        (phi_sym, 0, 2 * sp.pi),
    )
    results["area_fubini_study"] = {
        "area_exact": str(area_fs),
        "area_float": float(area_fs.evalf()),
        "equals_pi": bool(sp.simplify(area_fs - sp.pi) == 0),
        "pass": bool(sp.simplify(area_fs - sp.pi) == 0),
    }

    # S4: Area integral for standard unit sphere (incompatible case)
    area_s2 = sp.integrate(
        sp.integrate(sp.sin(theta_sym), (theta_sym, 0, sp.pi)),
        (phi_sym, 0, 2 * sp.pi),
    )
    results["area_sphere_r1"] = {
        "area_exact": str(area_s2),
        "area_float": float(area_s2.evalf()),
        "equals_4pi": bool(sp.simplify(area_s2 - 4 * sp.pi) == 0),
        "pass": bool(sp.simplify(area_s2 - 4 * sp.pi) == 0),
    }

    # S5: Conjugate-point universal identity K·(π/√K)² = π² for all K>0
    s_star_sym = sp.pi / sp.sqrt(K_sym)
    conj_identity = sp.simplify(K_sym * s_star_sym ** 2 - sp.pi ** 2)
    results["conjugate_point_universal_identity"] = {
        "K_times_s_star_sq_minus_pi_sq": str(conj_identity),
        "is_zero_for_all_K": bool(conj_identity == 0),
        "pass": bool(conj_identity == 0),
    }

    # S6: Numeric spot checks at K=4
    res_c_at_pi4 = float(res_c.subs(s_sym, sp.pi / 4))
    res_f_at_pi2 = float(res_f.subs(s_sym, sp.pi / 2))
    results["K4_spot_checks"] = {
        "jacobi_curved_residual_at_pi_over_4": res_c_at_pi4,
        "jacobi_flat_residual_at_pi_over_2": res_f_at_pi2,
        "area_FS_times_4": float(4 * area_fs.evalf()),
        "conjugate_identity_at_K4": float(conj_identity.subs(K_sym, 4).evalf()),
    }

    results["all_pass"] = all(
        v["pass"] for v in results.values() if isinstance(v, dict) and "pass" in v
    )
    return results


# ─── positive tests ───────────────────────────────────────────────────────────
def _run_positive() -> dict:
    results = {}

    # P1: (K=4, J_curved=sin(2s)/2) — compatible
    jac_p1 = _jacobi_coupling(4.0, _J_curved, _Jpp_curved)
    results["P1_jacobi_curved_compatible"] = {
        "description": "Jacobi field sin(2s)/2 satisfies ODE d²J/ds²+4J=0 for K=4 (compatible)",
        "ingredient_pair": ["K=4 (Fubini-Study, riemannian_curvature probe)",
                            "J_curved=sin(2s)/2 (geodesic_deviation probe)"],
        "coupling_type": "jacobi_curvature",
        "coupling_functional": "max_s |J''(s) + K·J(s)|",
        "coupling_value": jac_p1["coupling_value"],
        "diagnosis": "compatible",
        "residual": jac_p1["coupling_value"],
        "tolerance": JACOBI_COMPAT_TOL,
        "point_residuals": jac_p1["point_residuals"],
        "pass": jac_p1["coupling_value"] < JACOBI_COMPAT_TOL,
    }

    # P2: (K=4, dA_FS=sin(θ)/4·dθdφ) — compatible
    gb_p2 = _gb_area_coupling(4.0, _dA_fubini_study)
    results["P2_gauss_bonnet_fubini_study_compatible"] = {
        "description": "Fubini-Study area element sin(θ)/4·dθdφ gives K·area=4π (compatible)",
        "ingredient_pair": ["K=4 (Fubini-Study, riemannian_curvature probe)",
                            "dA_FS=sin(θ)/4·dθdφ (gauss_bonnet_cp1 probe)"],
        "coupling_type": "gauss_bonnet_area",
        "coupling_functional": "|K · ∫₀^π∫₀^{2π} f(θ)dθdφ − 4π|",
        "coupling_value": gb_p2["coupling_value"],
        "area_numerical": gb_p2["area_numerical"],
        "K_times_area": gb_p2["K_times_area"],
        "diagnosis": "compatible",
        "residual": gb_p2["coupling_value"],
        "tolerance": GB_COMPAT_TOL,
        "pass": gb_p2["coupling_value"] < GB_COMPAT_TOL,
    }

    # P3: (K=4, s*=π/2) — compatible
    cp_p3 = _conj_point_coupling(4.0, math.pi / 2)
    results["P3_conjugate_point_pi_half_compatible"] = {
        "description": "Conjugate point s*=π/2 satisfies K·(s*)²=π² for K=4 (compatible)",
        "ingredient_pair": ["K=4 (Fubini-Study, riemannian_curvature probe)",
                            "s*=π/2 (geodesic_deviation probe, first conjugate point)"],
        "coupling_type": "conjugate_point",
        "coupling_functional": "|K · (s*)² − π²|",
        "coupling_value": cp_p3["coupling_value"],
        "K_times_s_star_sq": cp_p3["K_times_s_star_sq"],
        "pi_sq": cp_p3["pi_sq"],
        "diagnosis": "compatible",
        "residual": cp_p3["coupling_value"],
        "tolerance": CONJ_COMPAT_TOL,
        "pass": cp_p3["coupling_value"] < CONJ_COMPAT_TOL,
    }

    results["all_pass"] = all(
        v["pass"] for v in results.values() if isinstance(v, dict) and "pass" in v
    )
    return results


# ─── negative tests ───────────────────────────────────────────────────────────
def _run_negative() -> dict:
    results = {}

    # N1: (K=4, J_flat=s) — incompatible
    jac_n1 = _jacobi_coupling(4.0, _J_flat, _Jpp_flat)
    results["N1_jacobi_flat_incompatible"] = {
        "description": "Flat Jacobi field J=s fails ODE d²J/ds²+4J=4s≠0 for K=4 (incompatible)",
        "ingredient_pair": ["K=4 (Fubini-Study)",
                            "J_flat=s (flat R² Jacobi field, wrong geometry)"],
        "coupling_type": "jacobi_curvature",
        "coupling_functional": "max_s |J''(s) + K·J(s)|",
        "coupling_value": jac_n1["coupling_value"],
        "expected_value": 2.0 * math.pi,  # max at s=π/2: |0+4·(π/2)| = 2π
        "diagnosis": "incompatible",
        "residual": jac_n1["coupling_value"],
        "threshold": JACOBI_INCOMPAT_THR,
        "point_residuals": jac_n1["point_residuals"],
        "pass": jac_n1["coupling_value"] > JACOBI_INCOMPAT_THR,
    }

    # N2: (K=4, dA_sphere=sin(θ)·dθdφ) — incompatible
    gb_n2 = _gb_area_coupling(4.0, _dA_sphere_r1)
    results["N2_gauss_bonnet_sphere_r1_incompatible"] = {
        "description": "Unit-sphere area sin(θ)dθdφ gives K·area=16π≠4π for K=4 (incompatible)",
        "ingredient_pair": ["K=4 (Fubini-Study)",
                            "dA_sphere=sin(θ)dθdφ (unit-sphere area element, wrong for CP^1)"],
        "coupling_type": "gauss_bonnet_area",
        "coupling_functional": "|K · ∫₀^π∫₀^{2π} f(θ)dθdφ − 4π|",
        "coupling_value": gb_n2["coupling_value"],
        "area_numerical": gb_n2["area_numerical"],
        "K_times_area": gb_n2["K_times_area"],
        "expected_value": 12.0 * math.pi,  # |16π − 4π| = 12π
        "diagnosis": "incompatible",
        "residual": gb_n2["coupling_value"],
        "threshold": GB_INCOMPAT_THR,
        "pass": gb_n2["coupling_value"] > GB_INCOMPAT_THR,
    }

    # N3: (K=4, s*=π/4) — incompatible
    cp_n3 = _conj_point_coupling(4.0, math.pi / 4)
    results["N3_conjugate_point_pi_quarter_incompatible"] = {
        "description": "Wrong conjugate point s*=π/4 gives K·(s*)²=π²/4≠π² for K=4 (incompatible)",
        "ingredient_pair": ["K=4 (Fubini-Study)",
                            "s*=π/4 (wrong — correct is π/2 for K=4)"],
        "coupling_type": "conjugate_point",
        "coupling_functional": "|K · (s*)² − π²|",
        "coupling_value": cp_n3["coupling_value"],
        "K_times_s_star_sq": cp_n3["K_times_s_star_sq"],
        "pi_sq": cp_n3["pi_sq"],
        "expected_value": 3.0 * math.pi ** 2 / 4,  # |π²/4 − π²| = 3π²/4
        "diagnosis": "incompatible",
        "residual": cp_n3["coupling_value"],
        "threshold": CONJ_INCOMPAT_THR,
        "pass": cp_n3["coupling_value"] > CONJ_INCOMPAT_THR,
    }

    results["all_pass"] = all(
        v["pass"] for v in results.values() if isinstance(v, dict) and "pass" in v
    )
    return results


# ─── boundary tests ───────────────────────────────────────────────────────────
def _run_boundary() -> dict:
    results = {}

    # B1: (K=0, J_flat=s) — flat degenerate limit, self-consistent at K=0
    jac_b1 = _jacobi_coupling(0.0, _J_flat, _Jpp_flat)
    results["B1_flat_limit_jacobi"] = {
        "description": (
            "K=0, J_flat=s: flat-limit Jacobi ODE residual=0 (self-consistent), "
            "boundary of K>0 CP^1 regime — coupling_value=0 but K=0 is degenerate"
        ),
        "ingredient_pair": ["K=0 (flat R², degenerate limit)", "J_flat=s"],
        "coupling_type": "jacobi_curvature",
        "coupling_functional": "max_s |J''(s) + 0·J(s)|",
        "coupling_value": jac_b1["coupling_value"],
        "diagnosis": "compatible_boundary",
        "residual": jac_b1["coupling_value"],
        "note": (
            "K=0 flat case is self-consistent (J=s solves J''=0) but is NOT a CP^1 "
            "shell ingredient — it is the flat degenerate limit. coupling_value=0 here "
            "confirms the functional is well-behaved at K→0, not that J_flat∈CP^1 shell."
        ),
        "pass": jac_b1["coupling_value"] < JACOBI_COMPAT_TOL,
    }

    # B2: (K=4, dA_hemisphere) — open manifold, GB gives 2π (boundary term missing)
    gb_b2 = _gb_area_coupling(4.0, _dA_hemisphere)
    hemi_cv = gb_b2["coupling_value"]
    expected_hemi_coupling = 2.0 * math.pi  # |4·(π/2) − 4π| = |2π − 4π| = 2π
    results["B2_hemisphere_gauss_bonnet_boundary"] = {
        "description": (
            "K=4, hemisphere dA (θ∈[0,π/2]): K·area=2π, GB deficit=2π — "
            "open manifold with ∂M≠∅, boundary term missing"
        ),
        "ingredient_pair": ["K=4 (Fubini-Study)", "dA_hemisphere (upper half-sphere, area=π/2)"],
        "coupling_type": "gauss_bonnet_area",
        "coupling_functional": "|K · ∫_{θ∈[0,π/2]} f(θ)dθdφ − 4π|",
        "coupling_value": hemi_cv,
        "area_numerical": gb_b2["area_numerical"],
        "K_times_area": gb_b2["K_times_area"],
        "expected_coupling_value": expected_hemi_coupling,
        "diagnosis": "boundary",
        "residual": hemi_cv,
        "note": (
            "Hemisphere has boundary ∂M (equator at θ=π/2); Gauss-Bonnet with boundary "
            "requires ∮_{∂M} κ_g ds term. coupling_value=2π is the GB deficit from the "
            "missing boundary contribution. Neither zero (compatible) nor large (incompatible)."
        ),
        "pass": BOUNDARY_LO < hemi_cv < BOUNDARY_HI,
    }

    results["all_pass"] = all(
        v["pass"] for v in results.values() if isinstance(v, dict) and "pass" in v
    )
    return results


# ─── main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    print("[pairwise_shell_coupling_cp1] running sympy verification …")
    sympy_data = _run_sympy_checks()
    print(f"  jacobi_curved ODE residual = 0:   {sympy_data['jacobi_curved_ode_residual']['is_zero']}")
    print(f"  jacobi_flat ODE residual = 4s:    {sympy_data['jacobi_flat_ode_residual_K4']['equals_4s']}")
    print(f"  area_FS = π:                       {sympy_data['area_fubini_study']['equals_pi']}")
    print(f"  conjugate identity K·(π/√K)²=π²:  {sympy_data['conjugate_point_universal_identity']['is_zero_for_all_K']}")

    print("[pairwise_shell_coupling_cp1] running positive tests …")
    pos = _run_positive()
    for k, v in pos.items():
        if isinstance(v, dict) and "pass" in v:
            cv = v.get("coupling_value", float("nan"))
            print(f"  {k}: {'PASS' if v['pass'] else 'FAIL'}  (coupling_value={cv:.2e})")

    print("[pairwise_shell_coupling_cp1] running negative tests …")
    neg = _run_negative()
    for k, v in neg.items():
        if isinstance(v, dict) and "pass" in v:
            cv = v.get("coupling_value", float("nan"))
            print(f"  {k}: {'PASS' if v['pass'] else 'FAIL'}  (coupling_value={cv:.4f})")

    print("[pairwise_shell_coupling_cp1] running boundary tests …")
    bnd = _run_boundary()
    for k, v in bnd.items():
        if isinstance(v, dict) and "pass" in v:
            cv = v.get("coupling_value", float("nan"))
            print(f"  {k}: {'PASS' if v['pass'] else 'FAIL'}  (coupling_value={cv:.4f})")

    all_pass = (
        sympy_data["all_pass"]
        and pos["all_pass"]
        and neg["all_pass"]
        and bnd["all_pass"]
    )
    print(f"[pairwise_shell_coupling_cp1] all_pass = {all_pass}")

    result = {
        "name": "pairwise_shell_coupling_cp1",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "sympy_checks": sympy_data,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": {
            "all_pass": all_pass,
            "coupling_program_step": "pairwise",
            "geometry": "CP^1 ≅ S² with Fubini-Study metric (K=4, area=π)",
            "coupling_types": {
                "jacobi_curvature": "C_J(K,J) = max_s |J''(s) + K·J(s)|",
                "gauss_bonnet_area": "C_GB(K,f) = |K·∫₀^π∫₀^{2π}f(θ)dθdφ − 4π|",
                "conjugate_point": "C_CP(K,s*) = |K·(s*)² − π²|",
            },
            "compatible_pairs": [
                "(K=4, J_curved=sin(2s)/2): C_J=0 — ODE d²J/ds²+4J=0 satisfied",
                "(K=4, dA_FS=sin(θ)/4·dθdφ): C_GB=0 — Gauss-Bonnet ∫K dA=4π satisfied",
                "(K=4, s*=π/2): C_CP=0 — conjugate-point identity K·(s*)²=π² satisfied",
            ],
            "incompatible_pairs": [
                f"(K=4, J_flat=s): C_J={2*math.pi:.4f} — ODE residual 4s (flat field, wrong K)",
                f"(K=4, dA_sphere=sin(θ)dθdφ): C_GB={12*math.pi:.4f} — area=4π gives K·area=16π≠4π",
                f"(K=4, s*=π/4): C_CP={3*math.pi**2/4:.4f} — K·(π/4)²=π²/4≠π²",
            ],
            "boundary_pairs": [
                "(K=0, J_flat=s): flat degenerate limit — compatible at K=0, not CP^1 shell",
                "(K=4, dA_hemisphere): C_GB=2π — open manifold, boundary term absent",
            ],
            "anchor_probes": [
                "riemannian_curvature_results.json: K=4 (Fubini-Study, canonical)",
                "geodesic_deviation_results.json: J_curved=sin(2s)/2, s*=π/2 (canonical)",
                "gauss_bonnet_cp1_results.json: area=π, ∫K dA=4π (canonical)",
            ],
            "scope_note": (
                "First pairwise shell coupling probe: step 2 of coupling program. "
                "Tests explicit pairwise compatibility of CP^1 shell-local ingredients "
                "via bounded, falsifiable coupling functionals. "
                "Out of scope: multi-shell coexistence (step 3), bridge claims (step 6), "
                "full N×N layer coupling matrix, Berry phase, QFI/killpoint, Axis 6."
            ),
        },
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    out_path = (
        "system_v4/probes/a2_state/sim_results/"
        "pairwise_shell_coupling_cp1_results.json"
    )
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"[pairwise_shell_coupling_cp1] wrote {out_path}")


if __name__ == "__main__":
    main()
