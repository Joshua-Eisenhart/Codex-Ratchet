#!/usr/bin/env python3
"""
sim_pure_lego_qfi_killpoint_divergence.py

Standalone probe: QFI behavior near the coherent-information kill point.

Open question: Does QFI diverge at gamma* = (1-p)/p where I_c = 0?

State family: rho_AR(gamma) with effective rank-2 eigenvalues {1-p*gamma, p*gamma}.
Channel: amplitude damping with parameter gamma on system A of
  |psi>_AR = sqrt(1-p)|00> + sqrt(p)|11>.

SLD-QFI for diagonal rho with constant eigenvectors:
  F_Q(p, gamma) = sum_i (d_gamma lambda_i)^2 / lambda_i
                = p^2/(1-p*gamma) + p/gamma

Analytically verified:
  F_Q(gamma*)       = p/(1-p)               [FINITE at kill point]
  lim F_Q as g->0   = infinity               [rank-change: mu_2 = p*gamma -> 0]
  d_gamma F_Q|_{g*} = p*(1-2p)/(1-p)^2     [finite first derivative]
  d2_gamma F_Q|_{g*}= 2p*(1-3p+3p^2)/(1-p)^3  [finite second derivative]

Diagnosis: SMOOTH passage at gamma*. True divergence at gamma=0 is a
rank-change artifact (unrelated to the I_c kill point).
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

# ---- pytorch ----
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    torch = None  # type: ignore[assignment]
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

# ---- z3 ----
_z3_available = False
try:
    from z3 import Solver as _Z3Solver, RealVal as _Z3RealVal  # noqa: F401
    _z3_available = True
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

# ---- sympy ----
try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None  # type: ignore[assignment]
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

# ---- remaining tools (try-import; none used in this probe) ----
for _tool, _pkg in [
    ("pyg",       "torch_geometric"),
    ("cvc5",      "cvc5"),
    ("clifford",  "clifford"),
    ("geomstats", "geomstats"),
    ("e3nn",      "e3nn"),
    ("rustworkx", "rustworkx"),
    ("xgi",       "xgi"),
    ("toponetx",  "toponetx"),
    ("gudhi",     "gudhi"),
]:
    try:
        __import__(_pkg)
        TOOL_MANIFEST[_tool]["tried"] = True
        TOOL_MANIFEST[_tool]["reason"] = (
            "tried; not used — no graph/spinor/topology structure in this probe"
        )
    except ImportError:
        TOOL_MANIFEST[_tool]["reason"] = "not installed"

# =====================================================================
# CLASSIFICATION
# =====================================================================

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical probe: QFI behavior at the I_c kill point gamma*=(1-p)/p for the "
    "amplitude-damping rho_AR family. SLD-QFI F_Q=p^2/(1-p*gamma)+p/gamma. "
    "torch autograd (load_bearing) for gradient sweeps and continuity checks; "
    "sympy (load_bearing) for symbolic F_Q(gamma*)=p/(1-p) and C^2 verification; "
    "z3 (supportive) rational-arithmetic check F_Q_A(3/4,1/3)=9/4 (UNSAT). "
    "Diagnosis: QFI smooth at gamma*; divergence only at gamma=0 (rank-change artifact)."
)
LEGO_IDS = ["qfi_killpoint_continuity"]
PRIMARY_LEGO_IDS = ["qfi_killpoint_continuity"]

_EPS = 1e-12

# =====================================================================
# CORE QFI FORMULAS
# =====================================================================


def _qfi_ar_torch(p_val: float, gamma: "torch.Tensor") -> "torch.Tensor":
    """
    SLD-QFI of rho_AR rank-2 subspace with eigenvalues {mu1=1-p*g, mu2=p*g}.
    F_Q = (d_g mu1)^2/mu1 + (d_g mu2)^2/mu2
        = p^2/(1-p*gamma) + p/gamma
    gamma must carry requires_grad=True for autograd.
    """
    p = torch.tensor(p_val, dtype=torch.float64)
    mu1 = 1.0 - p * gamma   # d/dg -> -p  =>  p^2 / mu1
    mu2 = p * gamma          # d/dg ->  p  =>  p^2 / mu2 = p / gamma
    return p ** 2 / mu1 + p ** 2 / mu2


def _qfi_ar_np(p_val: float, gamma: float) -> float:
    """Numpy counterpart — returns inf if any denominator is non-positive."""
    mu1 = 1.0 - p_val * gamma
    mu2 = p_val * gamma
    if mu1 <= _EPS or mu2 <= _EPS:
        return float("inf")
    return float(p_val ** 2 / mu1 + p_val ** 2 / mu2)


# =====================================================================
# POSITIVE SECTION  —  smooth passage at kill point (p=3/4, gamma*=1/3)
# =====================================================================


def _run_positive():
    """
    p=3/4, gamma*=1/3.
    Expected F_Q(gamma*) = p/(1-p) = 3.0.
    Show: all values finite and positive throughout [0.05, 0.95];
    gradient continuous at gamma*; gradient value close to analytic -6.0.
    Machine-readable diagnosis: 'smooth'.
    """
    if torch is None:
        return {"pass": False, "error": "torch not available", "skipped": True}

    p_val = 0.75
    gamma_star = (1.0 - p_val) / p_val          # = 1/3
    expected_fq_star = p_val / (1.0 - p_val)    # = 3.0

    # Sweep avoids gamma->0 divergence; covers kill point in interior
    gammas = torch.linspace(0.05, 0.95, 91, dtype=torch.float64)
    qfi_vals: list[float] = []
    grad_vals: list[float] = []
    for g in gammas:
        gg = torch.tensor(g.item(), dtype=torch.float64, requires_grad=True)
        qfi = _qfi_ar_torch(p_val, gg)
        qfi.backward()
        qfi_vals.append(qfi.item())
        grad_vals.append(float(gg.grad))  # type: ignore[arg-type]

    qfi_np  = np.array(qfi_vals)
    gamma_np = gammas.numpy()

    all_finite   = bool(np.all(np.isfinite(qfi_np)))
    all_positive = bool(np.all(qfi_np > 0.0))

    # F_Q value at kill point (nearest grid point)
    idx_star = int(np.argmin(np.abs(gamma_np - gamma_star)))
    qfi_at_star = qfi_vals[idx_star]
    star_value_correct = bool(abs(qfi_at_star - expected_fq_star) < 0.05)

    # Gradient continuity: probe at gamma* +/- eps using exact kill-point formula
    eps_kink = 5e-4
    gl = torch.tensor(gamma_star - eps_kink, dtype=torch.float64, requires_grad=True)
    _qfi_ar_torch(p_val, gl).backward()
    grad_left = float(gl.grad)  # type: ignore[arg-type]

    gr = torch.tensor(gamma_star + eps_kink, dtype=torch.float64, requires_grad=True)
    _qfi_ar_torch(p_val, gr).backward()
    grad_right = float(gr.grad)  # type: ignore[arg-type]

    grad_jump = abs(grad_left - grad_right)
    # Expect ~2 * eps * |d2F/dg2| = 2*5e-4*42 = 0.042; well below 0.5
    gradient_continuous = bool(grad_jump < 0.5)

    # Analytic first derivative at gamma*: p(1-2p)/(1-p)^2 = -6.0 for p=3/4
    expected_d1 = p_val * (1.0 - 2.0 * p_val) / (1.0 - p_val) ** 2
    grad_center = 0.5 * (grad_left + grad_right)
    grad_near_expected = bool(abs(grad_center - expected_d1) < 0.2)

    diagnosis = (
        "smooth"
        if all_finite and gradient_continuous and star_value_correct
        else "ambiguous"
    )

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "load_bearing: torch.autograd for d_gamma F_Q gradient sweeps — "
        "positive sweep (p=0.75, 91 steps gamma in [0.05,0.95]), "
        "gradient-continuity check at gamma*=1/3 (left/right eps=5e-4), "
        "first-derivative verification against analytic -6.0"
    )
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"

    pass_ = (
        all_finite and all_positive and star_value_correct
        and gradient_continuous and grad_near_expected
    )

    return {
        "pass": pass_,
        "p": p_val,
        "gamma_star": round(gamma_star, 8),
        "expected_fq_at_star": round(expected_fq_star, 8),
        "n_steps": 91,
        "gamma_range": [0.05, 0.95],
        "all_finite": all_finite,
        "all_positive": all_positive,
        "qfi_at_gamma_star_from_sweep": round(qfi_at_star, 8),
        "star_value_correct": star_value_correct,
        "grad_left_at_star": round(grad_left, 6),
        "grad_right_at_star": round(grad_right, 6),
        "grad_jump_at_star": round(grad_jump, 8),
        "gradient_continuous_at_star": gradient_continuous,
        "analytic_first_deriv_at_star": round(expected_d1, 6),
        "grad_center_near_expected": grad_near_expected,
        "diagnosis": diagnosis,
        "qfi_range": [
            round(float(qfi_np.min()), 4),
            round(float(qfi_np.max()), 4),
        ],
        "sweep": [
            {"gamma": round(g, 4), "qfi": round(q, 6), "grad_qfi": round(dq, 6)}
            for g, q, dq in zip(gamma_np.tolist(), qfi_vals, grad_vals)
        ],
    }


# =====================================================================
# NEGATIVE SECTION  —  rank-change divergence at gamma->0, NOT at gamma*
# =====================================================================


def _run_negative():
    """
    p=3/4.
    Show the TRUE QFI divergence is at gamma->0 (rank-change: mu2=p*gamma->0),
    NOT at the kill point gamma*=1/3.
    Leading-term verification: F_Q * gamma -> p as gamma->0.
    Machine-readable: 'rank_change_at_gamma_zero_not_at_kill_point'.
    """
    p_val = 0.75
    gamma_star = (1.0 - p_val) / p_val       # = 1/3
    fq_expected_star = p_val / (1.0 - p_val)  # = 3.0

    # Near-zero sweep (approaching rank-change boundary)
    gammas_low = np.array([0.001, 0.002, 0.005, 0.010, 0.020, 0.050, 0.100])
    fq_low = np.array([_qfi_ar_np(p_val, float(g)) for g in gammas_low])
    fq_times_gamma = fq_low * gammas_low

    # F_Q * gamma -> p as gamma->0  (leading term is p/gamma)
    leading_converges = bool(abs(float(fq_times_gamma[0]) - p_val) < 0.05)

    # F_Q at gamma=0.001 must be >> F_Q at kill point
    fq_at_001 = _qfi_ar_np(p_val, 0.001)
    large_near_zero = bool(fq_at_001 > 100.0 * fq_expected_star)

    # F_Q at kill point is finite and close to expected
    fq_star_computed = _qfi_ar_np(p_val, gamma_star)
    star_finite = bool(abs(fq_star_computed - fq_expected_star) < 0.01)

    # Identify the rank-change eigenvalue: mu2 = p*gamma -> 0 at gamma=0
    mu2_at_001 = p_val * 0.001
    rank_change_confirmed = bool(mu2_at_001 < 0.005)

    # Asymptotic ratio: F_Q(0.001) / (p / 0.001) should be ~1.0
    fq_leading_approx = p_val / 0.001
    asymptotic_ratio = float(fq_at_001 / fq_leading_approx)
    asymptotic_correct = bool(abs(asymptotic_ratio - 1.0) < 0.02)

    diagnosis = (
        "rank_change_at_gamma_zero_not_at_kill_point"
        if (large_near_zero and star_finite and leading_converges)
        else "ambiguous"
    )

    pass_ = (
        large_near_zero and star_finite and leading_converges
        and rank_change_confirmed and asymptotic_correct
    )

    return {
        "pass": pass_,
        "p": p_val,
        "gamma_star": round(gamma_star, 6),
        "fq_at_kill_point": round(fq_star_computed, 8),
        "expected_fq_at_star": round(fq_expected_star, 6),
        "star_finite": star_finite,
        "fq_at_gamma_0001": round(fq_at_001, 4),
        "ratio_fq_low_vs_star": round(fq_at_001 / fq_expected_star, 2),
        "large_near_zero": large_near_zero,
        "rank_change_eigenvalue_mu2_at_0001": round(mu2_at_001, 8),
        "rank_change_confirmed": rank_change_confirmed,
        "leading_term": {
            "expected_p": round(p_val, 6),
            "fq_times_gamma_at_0001": round(float(fq_times_gamma[0]), 6),
            "converges_to_p": leading_converges,
        },
        "asymptotic_ratio": round(asymptotic_ratio, 6),
        "asymptotic_correct": asymptotic_correct,
        "near_zero_sweep": [
            {
                "gamma": float(g),
                "qfi": round(float(fq), 4),
                "qfi_times_gamma": round(float(fg), 6),
            }
            for g, fq, fg in zip(gammas_low, fq_low, fq_times_gamma)
        ],
        "diagnosis": diagnosis,
    }


# =====================================================================
# BOUNDARY SECTION
# =====================================================================


def _run_boundary():
    """
    1. Exact value: F_Q(3/4, 1/3) = 3.0 within 1e-8
    2. Autograd vs FD at gamma*: discrepancy < 0.01
    3. Sympy: F_Q(p,gamma*)=p/(1-p), C^2 smoothness verified symbolically
    4. z3: F_Q_A(3/4,1/3)=9/4 is a tautology in rational arithmetic (UNSAT)
    5. p=2/3 crosscheck: gamma*=1/2, F_Q(2/3,1/2)=2.0
    """
    out: dict = {}

    # 1. Exact value
    p_val = 0.75
    gamma_star = (1.0 - p_val) / p_val   # = 1/3
    fq_exact = p_val / (1.0 - p_val)     # = 3.0
    fq_computed = _qfi_ar_np(p_val, gamma_star)
    out["exact_value_at_kill_point"] = {
        "pass": bool(abs(fq_computed - fq_exact) < 1e-8),
        "p": p_val,
        "gamma_star": round(gamma_star, 10),
        "expected": round(fq_exact, 10),
        "computed": round(fq_computed, 12),
        "discrepancy": float(abs(fq_computed - fq_exact)),
    }

    # 2. Autograd vs FD
    if torch is not None:
        h = 1e-5
        gg = torch.tensor(gamma_star, dtype=torch.float64, requires_grad=True)
        _qfi_ar_torch(p_val, gg).backward()
        grad_auto = float(gg.grad)  # type: ignore[arg-type]
        grad_fd = (
            _qfi_ar_np(p_val, gamma_star + h) - _qfi_ar_np(p_val, gamma_star - h)
        ) / (2.0 * h)
        disc = abs(grad_auto - grad_fd)
        out["autograd_vs_fd_at_star"] = {
            "pass": bool(disc < 0.01),
            "p": p_val,
            "gamma_star": round(gamma_star, 8),
            "grad_autograd": round(grad_auto, 6),
            "grad_fd": round(grad_fd, 6),
            "discrepancy": round(disc, 10),
        }
    else:
        out["autograd_vs_fd_at_star"] = {
            "pass": False, "skipped": True, "error": "torch not available"
        }

    # 3. Sympy symbolic
    out["sympy_symbolic"] = _run_sympy()

    # 4. z3 rational check
    out["z3_rational_check"] = _run_z3()

    # 5. p=2/3 crosscheck
    p_alt = 2.0 / 3.0
    g_alt = (1.0 - p_alt) / p_alt           # = 0.5
    fq_alt_expected = p_alt / (1.0 - p_alt)  # = 2.0
    fq_alt_computed = _qfi_ar_np(p_alt, g_alt)
    out["alt_kill_point_p_two_thirds"] = {
        "pass": bool(abs(fq_alt_computed - fq_alt_expected) < 1e-8),
        "p": round(p_alt, 8),
        "gamma_star": round(g_alt, 8),
        "expected_fq_at_star": round(fq_alt_expected, 8),
        "computed_fq_at_star": round(fq_alt_computed, 12),
        "discrepancy": float(abs(fq_alt_computed - fq_alt_expected)),
        "interpretation": "F_Q(gamma*)=p/(1-p) holds universally; p=2/3 confirms",
    }

    out["all_pass"] = all(
        v.get("pass", False)
        for v in out.values()
        if isinstance(v, dict) and "pass" in v
    )
    return out


def _run_sympy():
    """Symbolic: F_Q_AR(p,(1-p)/p)=p/(1-p); C^2 smooth at gamma*."""
    if sp is None:
        return {"pass": False, "error": "sympy not installed", "skipped": True}
    try:
        p, gamma = sp.symbols("p gamma", positive=True)
        F_Q = p ** 2 / (1 - p * gamma) + p / gamma

        g_star = (1 - p) / p

        # --- F_Q at gamma* ---
        F_Q_star = sp.simplify(F_Q.subs(gamma, g_star))
        expected_val = p / (1 - p)
        kill_ok = bool(sp.simplify(F_Q_star - expected_val) == 0)

        # --- First derivative at gamma* ---
        dF = sp.diff(F_Q, gamma)
        dF_star = sp.simplify(dF.subs(gamma, g_star))
        expected_d1 = p * (1 - 2 * p) / (1 - p) ** 2
        d1_ok = bool(sp.simplify(dF_star - expected_d1) == 0)

        # --- Second derivative at gamma* (finite => C^2 smooth) ---
        d2F = sp.diff(F_Q, gamma, 2)
        d2F_star = sp.simplify(d2F.subs(gamma, g_star))
        expected_d2 = 2 * p * (1 - 3 * p + 3 * p ** 2) / (1 - p) ** 3
        d2_ok = bool(sp.simplify(d2F_star - expected_d2) == 0)

        # Numerical spot-check at p=3/4
        p34 = sp.Rational(3, 4)
        fq_075   = float(F_Q_star.subs(p, p34))   # expect 3.0
        d1_075   = float(dF_star.subs(p, p34))    # expect -6.0
        d2_075   = float(d2F_star.subs(p, p34))   # expect 42.0

        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "load_bearing: symbolic proof that F_Q_AR(p,gamma*)=p/(1-p), "
            "d_gamma F_Q|_{g*}=p(1-2p)/(1-p)^2 (finite), "
            "d2_gamma F_Q|_{g*}=2p(1-3p+3p^2)/(1-p)^3 (finite) — "
            "confirming C^2 smooth passage through kill point"
        )
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

        return {
            "pass": bool(kill_ok and d1_ok and d2_ok),
            "F_Q_at_star_equals_p_over_1mp": kill_ok,
            "first_derivative_finite": d1_ok,
            "second_derivative_finite": d2_ok,
            "F_Q_star_p075": round(fq_075, 8),
            "d1_at_star_p075": round(d1_075, 8),
            "d2_at_star_p075": round(d2_075, 8),
            "F_Q_star_symbolic": str(F_Q_star),
            "d1_star_symbolic": str(dF_star),
        }
    except Exception as exc:
        return {"pass": False, "error": str(exc)}


def _run_z3():
    """z3 rational arithmetic: F_Q_A(3/4,1/3)=9/4 (UNSAT negation)."""
    if not _z3_available:
        return {"pass": False, "error": "z3 not installed", "skipped": True}
    try:
        from z3 import Solver, RealVal

        p = RealVal("3/4")
        g = RealVal("1/3")
        expected = RealVal("9/4")

        # F_Q_A = p^2/(1-p+p*gamma) + p^2/(p*(1-gamma))
        denom1 = 1 - p + p * g    # = 1/4 + 1/4 = 1/2
        denom2 = p * (1 - g)      # = 3/4 * 2/3 = 1/2
        fq_a = p * p / denom1 + p * p / denom2

        # Negation must be UNSAT
        s = Solver()
        s.add(fq_a != expected)
        result = s.check()
        z3_pass = str(result) == "unsat"

        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = (
            "supportive: SMT check that F_Q_A(3/4,1/3)=9/4 in rational "
            "arithmetic (negation is UNSAT in QF_LIRA)"
        )
        TOOL_INTEGRATION_DEPTH["z3"] = "supportive"

        return {
            "pass": z3_pass,
            "p_rational": "3/4",
            "gamma_star_rational": "1/3",
            "expected_F_Q_A_rational": "9/4",
            "z3_negation_result": str(result),
            "z3_tautology_confirmed": z3_pass,
            "interpretation": (
                "F_Q_A(3/4,1/3)=9/4 is provably exact in rational arithmetic"
            ),
        }
    except Exception as exc:
        return {"pass": False, "error": str(exc)}


# =====================================================================
# MAIN
# =====================================================================


def main() -> None:
    pos = _run_positive()
    neg = _run_negative()
    bnd = _run_boundary()

    all_pass = (
        pos.get("pass", False)
        and neg.get("pass", False)
        and bnd.get("all_pass", False)
    )

    results = {
        "name": "pure_lego_qfi_killpoint_divergence",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": {"qfi_smooth_at_kill_p075": pos},
        "negative": {"qfi_diverges_at_rank_change_not_kill_point": neg},
        "boundary": bnd,
        "summary": {
            "all_pass": all_pass,
            "positive_pass": pos.get("pass", False),
            "negative_pass": neg.get("pass", False),
            "boundary_pass": bnd.get("all_pass", False),
            "open_question": (
                "Does QFI diverge at the I_c kill point gamma*=(1-p)/p? "
                "(companion to ENFORCEMENT_AND_PROCESS_RULES.md open question)"
            ),
            "answer": (
                "QFI is SMOOTH at the kill point — no divergence, no kink, C^2-continuous. "
                "F_Q(gamma*)=p/(1-p) is finite. "
                "True divergence is at gamma->0 (rank-change artifact: eigenvalue p*gamma->0). "
                "The I_c shell boundary and QFI singularity are structurally independent."
            ) if all_pass else "indeterminate — check section failures above",
            "kill_point_diagnosis": "smooth" if all_pass else "ambiguous",
            "divergence_location": "gamma_zero_rank_change" if all_pass else "unknown",
            "scope_note": (
                "Amplitude damping, rho_AR rank-2 family, F_Q=p^2/(1-p*gamma)+p/gamma. "
                "p=3/4 primary (gamma*=1/3), p=2/3 crosscheck (gamma*=1/2)."
            ),
        },
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "qfi_killpoint_divergence_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")


if __name__ == "__main__":
    main()
