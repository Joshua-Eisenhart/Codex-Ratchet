#!/usr/bin/env python3
"""
Coherent information gradient continuity across amplitude-damping shell boundaries.

Open question addressed (ENFORCEMENT_AND_PROCESS_RULES.md):
    "Is ∇I_c continuous across shell boundaries, or does it have discontinuities
    at constraint transitions (L4, L6)?"

Formula (derived from first principles, two independent confirmations):

    I_c(p, γ) = H₂(p) - H₂(γp)

    H₂(x) = -x log₂ x - (1-x) log₂(1-x)  [binary entropy, bits]
    p  = sin²(θ/2) ∈ (0,1), eigenvalue of input state ρ_A
    γ  = amplitude damping parameter ∈ [0,1]

    Derivation: purification |ψ⟩_AR = √(1-p)|00⟩ + √p|11⟩
    Channel Λ_γ (Kraus: K₀=diag(1,√(1-γ)), K₁=[[0,√γ],[0,0]]) acts on A only.
    ρ_AR_out eigenvalues: {1-pγ, pγ, 0, 0}
    ρ_R = Tr_A(ρ_AR_out) eigenvalues: {1-p, p}
    I_c = S(ρ_R) - S(ρ_AR_out) = H₂(p) - H₂(pγ)

Shell-boundary proxies:
    L3↔L4 proxy — kill point at γ* = (1-p)/p
        I_c crosses 0; kink appears in max(0,I_c); raw I_c gradient is smooth.
    L4↔L6 proxy — gradient zero at γ = 1/(2p) (minimum of raw I_c)

Test cases:
    POSITIVE  p = 1/2  I_c = 1 - H₂(γ/2) ≥ 0 ∀ γ ∈ (0,1); no kill point
    NEGATIVE  p = 3/4  kill at γ* = 1/3; kink in max(0,I_c) ≈ 1.19
    BOUNDARY  endpoints, autograd vs finite difference, sympy symbolic
"""

import datetime
import json
import os
import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    torch = None  # type: ignore

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *  # noqa: F401,F403
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "tried; z3 cannot encode transcendental H₂ — "
        "no UNSAT proof available for entropy-based claims"
    )
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "tried; not needed — no algebraic constraint proof here"
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    sp = None  # type: ignore

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["reason"] = "tried; not used — no spinor geometry in this probe"
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
    TOOL_MANIFEST["geomstats"]["reason"] = "tried; not used — pure information-theoretic probe"
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
    TOOL_MANIFEST["e3nn"]["reason"] = "tried; not used"
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
    TOOL_MANIFEST["rustworkx"]["reason"] = "tried; not used"
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

for _tool in ("xgi", "toponetx", "gudhi"):
    try:
        __import__(_tool)
        TOOL_MANIFEST[_tool]["tried"] = True
        TOOL_MANIFEST[_tool]["reason"] = "tried; not used"
    except ImportError:
        TOOL_MANIFEST[_tool]["reason"] = "not installed"

# =====================================================================
# CLASSIFICATION
# =====================================================================

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical lego for coherent information gradient continuity across "
    "amplitude-damping shell boundaries. torch autograd (load_bearing) for "
    "all ∇I_c sweeps and kink measurement; sympy (load_bearing) for symbolic "
    "kill-point and gradient-zero formula verification. Kept separate from "
    "static I_c probes and shell topology probes."
)
LEGO_IDS = ["ic_gradient_shell_continuity"]
PRIMARY_LEGO_IDS = ["ic_gradient_shell_continuity"]

# =====================================================================
# CORE MATH  (torch + numpy, same formula)
# =====================================================================

_EPS = 1e-10


def _h2_torch(x):
    """H₂(x) in bits, safe clamp at ±_EPS."""
    x = torch.clamp(x, _EPS, 1.0 - _EPS)
    return -x * torch.log2(x) - (1.0 - x) * torch.log2(1.0 - x)


def _ic_torch(p_val: float, gamma):
    """I_c(p,γ) = H₂(p) - H₂(γp).  gamma carries requires_grad."""
    p = torch.tensor(p_val, dtype=torch.float64)
    return _h2_torch(p) - _h2_torch(gamma * p)


def _h2_np(x):
    x = np.clip(x, _EPS, 1.0 - _EPS)
    return -x * np.log2(x) - (1.0 - x) * np.log2(1.0 - x)


def _ic_np(p: float, gamma: float) -> float:
    return float(_h2_np(p) - _h2_np(gamma * p))


# =====================================================================
# POSITIVE SECTION  —  p = 1/2, no kill point in (0,1)
# =====================================================================

def _run_positive():
    """
    p = 1/2.  I_c(γ) = 1 - H₂(γ/2).
    Expected: I_c > 0 everywhere, ∇I_c < 0 everywhere, no sign flip.
    """
    p_val = 0.5
    gammas = torch.linspace(0.01, 0.99, 50, dtype=torch.float64)

    ic_vals, grad_vals = [], []
    for g in gammas:
        gamma = torch.tensor(g.item(), dtype=torch.float64, requires_grad=True)
        ic = _ic_torch(p_val, gamma)
        ic.backward()
        ic_vals.append(round(ic.item(), 8))
        grad_vals.append(round(float(gamma.grad), 8))

    ic_np = np.array(ic_vals)
    grad_np = np.array(grad_vals)
    gamma_np = gammas.numpy()

    all_positive       = bool(np.all(ic_np > 0.0))
    all_grad_negative  = bool(np.all(grad_np < 0.0))
    no_sign_flip       = bool(np.sum(np.abs(np.diff(np.sign(grad_np)))) == 0)
    ic_high_at_low_g   = bool(ic_np[0] > 0.90)       # I_c(0.01) ≈ 0.955
    ic_low_at_high_g   = bool(ic_np[-1] < 0.01)       # I_c(0.99) ≈ 0.00007

    # finite-difference agreement with autograd
    fd_grads = np.diff(ic_np) / np.diff(gamma_np)
    max_fd_disc = float(np.max(np.abs(fd_grads - grad_np[:-1])))
    fd_agrees = max_fd_disc < 10.0

    pass_ = (all_positive and all_grad_negative and no_sign_flip
             and ic_high_at_low_g and ic_low_at_high_g and fd_agrees)

    return {
        "pass": pass_,
        "p": p_val,
        "n_steps": 50,
        "gamma_range": [0.01, 0.99],
        "all_ic_positive": all_positive,
        "all_grad_negative": all_grad_negative,
        "no_gradient_sign_flip": no_sign_flip,
        "ic_at_gamma_001_exceeds_0p9": ic_high_at_low_g,
        "ic_at_gamma_099_below_0p01": ic_low_at_high_g,
        "fd_autograd_max_discrepancy": round(max_fd_disc, 8),
        "fd_agrees_with_autograd": fd_agrees,
        "ic_range": [round(float(ic_np.min()), 6), round(float(ic_np.max()), 6)],
        "grad_range": [round(float(grad_np.min()), 6), round(float(grad_np.max()), 6)],
        "sweep": [
            {"gamma": round(g, 4), "ic": ic, "grad_ic": gr}
            for g, ic, gr in zip(gamma_np.tolist(), ic_vals, grad_vals)
        ],
    }


# =====================================================================
# NEGATIVE SECTION  —  p = 3/4, kill at γ* = 1/3
# =====================================================================

def _run_negative():
    """
    p = 3/4.  I_c(γ) = H₂(3/4) - H₂(3γ/4).

    Kill point: γ* = 1/3  (where H₂(1/4) = H₂(3/4) by symmetry).
    Raw I_c gradient is smooth at γ* (no discontinuity in raw ∇I_c).
    Kink lives in max(0,I_c): left derivative ≈ -1.19, right = 0.
    Gradient zero (raw I_c minimum) at γ = 2/3.
    """
    p_val = 0.75
    gammas = torch.linspace(0.01, 0.99, 99, dtype=torch.float64)

    ic_raw_vals, grad_raw_vals = [], []
    ic_rect_vals, grad_rect_vals = [], []

    for g in gammas:
        # raw I_c
        gr = torch.tensor(g.item(), dtype=torch.float64, requires_grad=True)
        ic_raw = _ic_torch(p_val, gr)
        ic_raw.backward()
        ic_raw_vals.append(ic_raw.item())
        grad_raw_vals.append(float(gr.grad))

        # rectified max(0, I_c)
        grect = torch.tensor(g.item(), dtype=torch.float64, requires_grad=True)
        ic_rect = torch.clamp(_ic_torch(p_val, grect), min=0.0)
        ic_rect.backward()
        ic_rect_vals.append(ic_rect.item())
        grad_rect_vals.append(float(grect.grad))

    ic_raw_np  = np.array(ic_raw_vals)
    grad_raw_np = np.array(grad_raw_vals)
    gamma_np   = gammas.numpy()

    # --- kill-point detection ---
    sign_changes = np.where(np.diff(np.sign(ic_raw_np)))[0]
    zc_detected  = len(sign_changes) > 0
    gamma_star   = None
    kill_err     = None
    if zc_detected:
        idx = sign_changes[0]
        gamma_star = float((gamma_np[idx] + gamma_np[idx + 1]) / 2.0)
        kill_err   = abs(gamma_star - 1.0 / 3.0)
    kill_within_tol = zc_detected and kill_err is not None and kill_err < 0.02

    # --- kink magnitude at γ* ---
    kink_mag         = None
    raw_smooth       = None
    grad_left_rect   = None
    grad_right_rect  = None
    if zc_detected and gamma_star is not None:
        eps_d = 5e-4
        # Use the exact kill point (1-p)/p, not the numerically detected gamma_star,
        # to avoid floating-point grid offset placing both probes on the negative side.
        gamma_star_exact = (1.0 - p_val) / p_val

        # left / right of rectified
        gl = torch.tensor(gamma_star_exact - eps_d, dtype=torch.float64, requires_grad=True)
        torch.clamp(_ic_torch(p_val, gl), min=0.0).backward()
        grad_left_rect = float(gl.grad)

        grr = torch.tensor(gamma_star_exact + eps_d, dtype=torch.float64, requires_grad=True)
        torch.clamp(_ic_torch(p_val, grr), min=0.0).backward()
        grad_right_rect = float(grr.grad)

        kink_mag = abs(grad_left_rect - grad_right_rect)

        # raw gradient continuity check (should be smooth)
        gl_raw = torch.tensor(gamma_star_exact - eps_d, dtype=torch.float64, requires_grad=True)
        _ic_torch(p_val, gl_raw).backward()
        grr_raw = torch.tensor(gamma_star_exact + eps_d, dtype=torch.float64, requires_grad=True)
        _ic_torch(p_val, grr_raw).backward()
        raw_kink = abs(float(gl_raw.grad) - float(grr_raw.grad))
        raw_smooth = bool(raw_kink < 0.1)

    # --- gradient zero near γ = 2/3 ---
    idx_23    = int(np.argmin(np.abs(gamma_np - 2.0 / 3.0)))
    grad_at23 = float(grad_raw_np[idx_23])
    grad_zero_at23 = abs(grad_at23) < 0.20

    pass_ = (
        zc_detected
        and kill_within_tol
        and kink_mag is not None and kink_mag > 0.5
        and raw_smooth is True
        and grad_zero_at23
    )

    return {
        "pass": pass_,
        "p": p_val,
        "n_steps": 99,
        "gamma_range": [0.01, 0.99],
        "kill_point": {
            "detected": zc_detected,
            "gamma_star": round(gamma_star, 6) if gamma_star is not None else None,
            "expected": round(1.0 / 3.0, 6),
            "error": round(kill_err, 6) if kill_err is not None else None,
            "within_tol_0p02": kill_within_tol,
        },
        "kink_in_max0_ic": {
            "grad_left": round(grad_left_rect, 6) if grad_left_rect is not None else None,
            "grad_right": round(grad_right_rect, 6) if grad_right_rect is not None else None,
            "kink_magnitude": round(kink_mag, 6) if kink_mag is not None else None,
            "expected_approx": 1.189,
            "is_structural": kink_mag is not None and kink_mag > 0.5,
        },
        "raw_gradient_smooth_at_kill": raw_smooth,
        "gradient_zero_near_gamma_2_3": {
            "grad_at_gamma_2_3": round(grad_at23, 6),
            "is_near_zero": grad_zero_at23,
            "expected_gamma": round(2.0 / 3.0, 6),
        },
        "ic_raw_range": [round(float(ic_raw_np.min()), 6), round(float(ic_raw_np.max()), 6)],
        "sweep": [
            {
                "gamma": round(g, 4),
                "ic_raw": round(ir, 8),
                "grad_raw": round(gr, 8),
                "ic_rect": round(irt, 8),
                "grad_rect": round(grt, 8),
            }
            for g, ir, gr, irt, grt in zip(
                gamma_np.tolist(),
                ic_raw_vals, grad_raw_vals,
                ic_rect_vals, grad_rect_vals,
            )
        ],
    }


# =====================================================================
# BOUNDARY SECTION  —  endpoints, fd, analytic, sympy
# =====================================================================

def _run_boundary():
    out = {}

    # 1. Endpoint safety (γ → 0 and γ → 1)
    for p_val, tag in [(0.5, "p05"), (0.75, "p075")]:
        ic_low  = _ic_np(p_val, 1e-6)
        ic_high = _ic_np(p_val, 1.0 - 1e-6)
        h2_p    = float(_h2_np(p_val))
        out[f"endpoint_{tag}"] = {
            "pass": abs(ic_low - h2_p) < 0.02 and abs(ic_high) < 1e-4,
            "p": p_val,
            "ic_at_gamma_1e-6": round(ic_low, 8),
            "H2_p": round(h2_p, 8),
            "ic_at_gamma_near_1": round(ic_high, 8),
        }

    # 2. Autograd vs finite difference (5 interior points)
    test_pts = [(0.5, 0.3), (0.5, 0.6), (0.75, 0.2), (0.75, 0.5), (0.60, 0.4)]
    max_disc = 0.0
    fd_rows  = []
    for p_val, g_val in test_pts:
        gamma_t = torch.tensor(g_val, dtype=torch.float64, requires_grad=True)
        _ic_torch(p_val, gamma_t).backward()
        grad_ag = float(gamma_t.grad)
        h = 1e-5
        grad_fd = (_ic_np(p_val, g_val + h) - _ic_np(p_val, g_val - h)) / (2.0 * h)
        disc    = abs(grad_ag - grad_fd)
        max_disc = max(max_disc, disc)
        fd_rows.append({
            "p": p_val, "gamma": g_val,
            "grad_autograd": round(grad_ag, 8),
            "grad_fd": round(grad_fd, 8),
            "discrepancy": round(disc, 12),
        })
    out["autograd_vs_fd"] = {
        "pass": max_disc < 1e-4,
        "max_discrepancy": round(max_disc, 12),
        "threshold": 1e-4,
        "details": fd_rows,
    }

    # 3. Analytic cross-check: I_c(0.5, 0.5) = 1 - H₂(0.25)
    ic_t = float(_ic_torch(0.5, torch.tensor(0.5, dtype=torch.float64)))
    ic_n = _ic_np(0.5, 0.5)
    h2_025 = float(_h2_np(0.25))
    direct = 1.0 - h2_025
    disc_t = abs(ic_t - direct)
    disc_n = abs(ic_n - direct)
    out["analytic_crosscheck_ic_05_05"] = {
        "pass": disc_t < 1e-10 and disc_n < 1e-10,
        "I_c_torch": round(ic_t, 12),
        "I_c_numpy": round(ic_n, 12),
        "direct_1_minus_H2_025": round(direct, 12),
        "H2_025": round(h2_025, 12),
        "discrepancy_torch": round(disc_t, 15),
        "discrepancy_numpy": round(disc_n, 15),
    }

    # 4. Sympy symbolic verification (load-bearing)
    out["sympy_symbolic"] = _run_sympy()

    out["all_pass"] = all(
        v.get("pass", False) for v in out.values()
        if isinstance(v, dict) and "pass" in v
    )
    return out


def _run_sympy():
    if sp is None:
        return {"pass": False, "error": "sympy not installed", "skipped": True}
    try:
        p, gamma = sp.symbols("p gamma", positive=True, real=True)

        def H2s(arg):
            return (-arg * sp.log(arg) - (1 - arg) * sp.log(1 - arg)) / sp.log(2)

        Ic = H2s(p) - H2s(gamma * p)

        # Kill-point formula: γ* = (1-p)/p  →  I_c = 0
        gamma_kill = (1 - p) / p
        Ic_kill    = sp.simplify(Ic.subs(gamma, gamma_kill))
        kill_ok    = bool(Ic_kill == sp.Integer(0))
        kill_p075  = float(gamma_kill.subs(p, sp.Rational(3, 4)))

        # Gradient-zero formula: γ = 1/(2p)  →  dI_c/dγ = 0
        dIc = sp.diff(Ic, gamma)
        gamma_gz   = sp.Rational(1, 2) / p
        dIc_gz     = sp.simplify(dIc.subs(gamma, gamma_gz))
        gz_ok      = bool(dIc_gz == sp.Integer(0))
        gz_p075    = float(gamma_gz.subs(p, sp.Rational(3, 4)))

        # I_c(1/2, 1) = 0
        Ic_half_one    = sp.simplify(Ic.subs([(p, sp.Rational(1, 2)), (gamma, 1)]))
        half_one_zero  = bool(Ic_half_one == sp.Integer(0))

        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "load_bearing: symbolic verification of kill-point formula "
            "γ*=(1-p)/p (I_c=0), gradient-zero location γ=1/(2p), and I_c(1/2,1)=0"
        )
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

        return {
            "pass": bool(kill_ok and gz_ok and half_one_zero),
            "kill_point_formula_verified": bool(kill_ok),
            "kill_point_value_p_075": round(kill_p075, 8),
            "kill_point_expected_1_3": round(1.0 / 3.0, 8),
            "gradient_zero_formula_verified": bool(gz_ok),
            "gradient_zero_value_p_075": round(gz_p075, 8),
            "gradient_zero_expected_2_3": round(2.0 / 3.0, 8),
            "ic_half_one_is_zero": bool(half_one_zero),
        }
    except Exception as exc:
        return {"pass": False, "error": str(exc)}


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    if torch is None:
        raise RuntimeError("torch is required but not installed")

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "load_bearing: torch.autograd for all ∇I_c gradient computations — "
        "positive sweep (p=0.5, 50 steps), negative sweep (p=0.75, 99 steps), "
        "kink measurement at kill point γ*=1/3, finite-difference cross-check"
    )
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"

    pos = _run_positive()
    neg = _run_negative()
    bnd = _run_boundary()

    all_pass = pos["pass"] and neg["pass"] and bnd.get("all_pass", False)

    results = {
        "name": "pure_lego_ic_shell_boundary_continuity",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": {"ic_gradient_continuous_p05": pos},
        "negative": {"ic_kill_point_p075": neg},
        "boundary": bnd,
        "summary": {
            "all_pass": all_pass,
            "positive_pass": pos["pass"],
            "negative_pass": neg["pass"],
            "boundary_pass": bnd.get("all_pass", False),
            "open_question": (
                "Is ∇I_c continuous across shell boundaries? "
                "(ENFORCEMENT_AND_PROCESS_RULES.md)"
            ),
            "answer": (
                "Raw ∇I_c is SMOOTH through the kill point — no discontinuity. "
                "The shell-boundary marker lives in max(0,I_c): kink of magnitude "
                "~1.19 at γ*=(1-p)/p. L4↔L6 proxy: raw gradient zero at γ=1/(2p)."
            ) if all_pass else "indeterminate — check failures above",
            "scope_note": (
                "Amplitude damping channel, 1-parameter family, "
                "direct H₂(p)-H₂(γp) formula. "
                "Resolves ENFORCEMENT_AND_PROCESS_RULES.md ∇I_c continuity question."
            ),
        },
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(
        out_dir, "pure_lego_ic_shell_boundary_continuity_results.json"
    )
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
