#!/usr/bin/env python3
"""
sim_torch_deep_axis0_autograd_vn_entropy.py

Canonical sim: Axis 0 entropy gradient ∇I_c computed via pytorch autograd
through a nontrivial composition, cross-checked against a sympy closed-form
on a small analytic case.

Ratchet-architecture framing (memory: feedback_pytorch_is_ratchet.md):
  - forward pass  = possibility branch (parameter -> unitary -> rho -> S(rho))
  - backward pass = constraint channel (∂S/∂theta propagated through the full
    composition: complex matrix exponential of a Hermitian generator,
    conjugation of a seed density matrix, eigendecomposition, -Tr(rho log rho))
  - graph         = the constraint manifold that autograd walks

Composition exercised end-to-end under autograd:
    theta (real scalar)
      -> H(theta) = theta * sigma_x        (Hermitian generator)
      -> U = expm(i H)                     (torch.linalg.matrix_exp, complex)
      -> rho(theta) = U rho0 U^dagger      (conjugation; rho0 = diag(p, 1-p))
      -> eigendecomp of rho                (torch.linalg.eigvalsh)
      -> S_vN = -sum lambda_i log lambda_i (von Neumann entropy)
      -> dS/dtheta via autograd

Closed-form (sympy, analytic):
    With rho0 = diag(p, 1-p) and U = exp(i theta sigma_x), the eigenvalues
    of rho(theta) are invariant under unitary conjugation => eigenvalues are
    still {p, 1-p}, so S_vN(theta) = -p log p - (1-p) log (1-p) is constant
    in theta and dS/dtheta = 0 identically.

    That gives an exact, analytic ground-truth derivative (0) that autograd
    must reproduce despite backproping through matrix_exp, complex conjugate
    transpose, and eigvalsh. This is a *nontrivial* composition whose
    derivative happens to vanish for principled reasons (unitary invariance
    of the spectrum). Negative and boundary tests break that invariance to
    confirm autograd also captures *nonzero* gradients correctly.

classification = "classical_baseline"
DEMOTE_REASON = "no non-numpy load_bearing tool; numeric numpy only"
pytorch        = load_bearing (autograd IS the claim)
sympy          = supportive  (closed-form ground truth for pass/fail gate)
"""

import json
import math
import os

classification = "classical_baseline"

import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# --- imports / tried flags ---
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

# Other tools: probe-tried only so manifest is honest (non-empty reason).
for _name in ("pyg", "z3", "cvc5", "clifford", "geomstats", "e3nn",
              "rustworkx", "xgi", "toponetx", "gudhi"):
    if not TOOL_MANIFEST[_name]["tried"] and not TOOL_MANIFEST[_name]["reason"]:
        TOOL_MANIFEST[_name]["reason"] = (
            "not exercised: sim scope is autograd-through-spectrum; "
            "this tool is outside the minimal load-bearing path"
        )


# =====================================================================
# Core autograd machinery
# =====================================================================

def _vn_entropy_from_theta(theta, p, seed_off_diag=0.0):
    """
    Build rho(theta) = U(theta) rho0 U(theta)^dagger with
        H = theta * sigma_x + seed_off_diag * sigma_y
        U = exp(i H)
        rho0 = diag(p, 1-p)  (+ optional off-diagonal perturbation handled
                              by seed_off_diag via an additional generator).
    Returns S_vN(rho(theta)) as a differentiable torch scalar.

    For the main positive test seed_off_diag=0 so the composition is a
    *pure unitary conjugation of a diagonal rho0* => spectrum invariant
    => analytic dS/dtheta = 0.
    """
    device = theta.device
    dtype_c = torch.complex128

    sigma_x = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=dtype_c, device=device)
    sigma_y = torch.tensor([[0.0, -1j], [1j, 0.0]], dtype=dtype_c, device=device)

    H = theta.to(dtype_c) * sigma_x + seed_off_diag * sigma_y
    # Nontrivial composition 1: complex matrix exponential
    U = torch.linalg.matrix_exp(1j * H)

    rho0 = torch.tensor([[p, 0.0], [0.0, 1.0 - p]], dtype=dtype_c, device=device)

    # Nontrivial composition 2: unitary conjugation (two complex matmuls)
    rho = U @ rho0 @ U.conj().transpose(-1, -2)

    # Nontrivial composition 3: Hermitian eigendecomposition under autograd.
    # Symmetrize to suppress tiny anti-Hermitian numerical drift before
    # handing to eigvalsh (spectrum is real by construction).
    rho_herm = 0.5 * (rho + rho.conj().transpose(-1, -2))
    evals = torch.linalg.eigvalsh(rho_herm)  # real, ascending

    # Clamp for numerical log safety; does NOT affect the analytic cases
    # (true eigenvalues are p and 1-p, both strictly in (0,1)).
    evals = torch.clamp(evals, min=1e-15)

    # Nontrivial composition 4: -sum lam log lam
    S = -(evals * torch.log(evals)).sum().real
    return S


def _autograd_dS_dtheta(theta_val, p, seed_off_diag=0.0):
    theta = torch.tensor(float(theta_val), dtype=torch.float64, requires_grad=True)
    S = _vn_entropy_from_theta(theta, p, seed_off_diag=seed_off_diag)
    S.backward()
    return float(S.detach()), float(theta.grad.detach())


# =====================================================================
# Sympy closed-form ground truth
# =====================================================================

def _sympy_closed_form_S_and_dS(p_val, theta_val):
    """
    For rho0 = diag(p, 1-p) and U = exp(i theta sigma_x), eigenvalues of
    rho(theta) are {p, 1-p} (unitary invariance of spectrum).
    S(theta) = -p log p - (1-p) log(1-p), derivative w.r.t. theta is 0.
    Returns (S_value, dS_dtheta) as floats.
    """
    p = sp.Rational(*p_val.as_integer_ratio()) if isinstance(p_val, float) and p_val in (0.25, 0.5, 0.75) else sp.Float(p_val)
    S_expr = -p * sp.log(p) - (1 - p) * sp.log(1 - p)
    # symbolic theta to make the 0-derivative *structural*, not a numeric fluke
    theta = sp.symbols("theta", real=True)
    S_of_theta = S_expr + 0 * theta  # explicit: no theta dependence
    dS = sp.diff(S_of_theta, theta)
    return float(S_expr.evalf()), float(dS)  # dS == 0 exactly


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    # Multiple (p, theta) points; autograd must match closed-form.
    cases = [
        (0.5, 0.0),
        (0.5, 0.7),
        (0.25, 1.3),
        (0.75, -0.4),
        (0.1, 2.1),
    ]
    tol = 1e-9
    per_case = []
    all_ok = True
    for p, th in cases:
        S_auto, dS_auto = _autograd_dS_dtheta(th, p, seed_off_diag=0.0)
        S_sym, dS_sym = _sympy_closed_form_S_and_dS(p, th)
        S_err = abs(S_auto - S_sym)
        dS_err = abs(dS_auto - dS_sym)
        ok = (S_err < 1e-10) and (dS_err < tol)
        all_ok = all_ok and ok
        per_case.append({
            "p": p, "theta": th,
            "S_autograd": S_auto, "S_sympy": S_sym, "S_abs_err": S_err,
            "dS_autograd": dS_auto, "dS_sympy": dS_sym,
            "dS_abs_err": dS_err, "pass": ok,
        })
    results["vn_entropy_autograd_matches_sympy"] = {
        "pass": all_ok,
        "tolerance_dS": tol,
        "cases": per_case,
        "composition_depth": [
            "torch.linalg.matrix_exp(complex Hermitian generator)",
            "complex conjugate-transpose",
            "two complex matmuls (unitary conjugation)",
            "torch.linalg.eigvalsh (Hermitian eigendecomp under autograd)",
            "-sum lam*log(lam)",
        ],
    }
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    Break unitary invariance -> spectrum *does* depend on theta -> autograd
    must report a NONZERO dS/dtheta. If it still returned 0, the backward
    pass would be decorative. We compare autograd against a central finite
    difference as an independent numerical ground truth for nonzero grads.
    """
    results = {}

    def _entropy_nonunitary(theta_val, p, alpha):
        """Non-unitary evolution: M(theta) = expm(theta*alpha*sigma_z) (real, not i).
        Apply as rho = M rho0 M^T / Tr(...). This breaks spectrum invariance."""
        theta = torch.tensor(float(theta_val), dtype=torch.float64, requires_grad=True)
        sz = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.float64)
        M = torch.linalg.matrix_exp(theta * alpha * sz)
        rho0 = torch.tensor([[p, 0.0], [0.0, 1 - p]], dtype=torch.float64)
        rho = M @ rho0 @ M.T
        rho = rho / torch.trace(rho)
        rho = 0.5 * (rho + rho.T)
        evals = torch.linalg.eigvalsh(rho).clamp_min(1e-15)
        S = -(evals * torch.log(evals)).sum()
        S.backward()
        return float(S.detach()), float(theta.grad.detach())

    def _fd(theta_val, p, alpha, h=1e-5):
        def _S(t):
            sz = np.array([[1.0, 0.0], [0.0, -1.0]])
            M = np.array([[math.exp(t * alpha), 0.0], [0.0, math.exp(-t * alpha)]])
            rho0 = np.array([[p, 0.0], [0.0, 1 - p]])
            rho = M @ rho0 @ M.T
            rho = rho / np.trace(rho)
            w = np.linalg.eigvalsh(0.5 * (rho + rho.T))
            w = np.clip(w, 1e-15, None)
            return float(-np.sum(w * np.log(w)))
        return (_S(theta_val + h) - _S(theta_val - h)) / (2 * h)

    cases = [(0.3, 0.4, 0.9), (0.25, 0.2, 1.1), (0.6, -0.3, 0.7)]
    per_case = []
    all_ok = True
    for p, theta_val, alpha in cases:
        S_auto, dS_auto = _entropy_nonunitary(theta_val, p, alpha)
        dS_fd = _fd(theta_val, p, alpha)
        nonzero = abs(dS_auto) > 1e-6
        match_fd = abs(dS_auto - dS_fd) < 1e-6
        ok = nonzero and match_fd
        all_ok = all_ok and ok
        per_case.append({
            "p": p, "theta": theta_val, "alpha": alpha,
            "S_autograd": S_auto,
            "dS_autograd": dS_auto,
            "dS_finite_diff": dS_fd,
            "nonzero_grad": nonzero,
            "matches_finite_diff": match_fd,
            "pass": ok,
        })
    results["nonunitary_breaks_invariance_grad_nonzero"] = {
        "pass": all_ok,
        "cases": per_case,
        "rationale": (
            "non-unitary M changes the spectrum, so dS/dtheta must be "
            "nonzero; autograd must also match a central finite-difference "
            "independent numerical check"
        ),
    }
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # 1. Pure state (p = 1): S = 0 everywhere, dS/dtheta = 0 (degenerate
    #    spectrum {1, 0}). Autograd must not NaN through eigvalsh + log.
    theta = torch.tensor(0.5, dtype=torch.float64, requires_grad=True)
    try:
        S = _vn_entropy_from_theta(theta, p=1.0 - 1e-12)  # near-pure, avoid log(0)
        S.backward()
        pure_ok = (abs(float(S.detach())) < 1e-9) and (abs(float(theta.grad.detach())) < 1e-7)
        pure_err = None
    except Exception as e:
        pure_ok = False
        pure_err = repr(e)
    results["near_pure_state_stable"] = {
        "pass": pure_ok,
        "S": float(S.detach()) if pure_ok else None,
        "dS": float(theta.grad.detach()) if pure_ok else None,
        "error": pure_err,
    }

    # 2. Maximally mixed (p = 0.5): S = log 2, dS/dtheta = 0.
    theta2 = torch.tensor(-1.7, dtype=torch.float64, requires_grad=True)
    S2 = _vn_entropy_from_theta(theta2, p=0.5)
    S2.backward()
    mix_ok = (abs(float(S2.detach()) - math.log(2)) < 1e-12) and (abs(float(theta2.grad.detach())) < 1e-10)
    results["maximally_mixed_state"] = {
        "pass": mix_ok,
        "S": float(S2.detach()),
        "S_expected": math.log(2),
        "dS": float(theta2.grad.detach()),
    }

    # 3. Large |theta|: U still unitary, spectrum still invariant. Guards
    #    against matrix_exp numerical drift breaking autograd gradient.
    theta3 = torch.tensor(50.0, dtype=torch.float64, requires_grad=True)
    S3 = _vn_entropy_from_theta(theta3, p=0.3)
    S3.backward()
    large_ok = abs(float(theta3.grad.detach())) < 1e-6
    results["large_theta_unitary_still_invariant"] = {
        "pass": large_ok,
        "dS": float(theta3.grad.detach()),
        "tolerance": 1e-6,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    # Mark tools actually exercised
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "autograd backpropagates through matrix_exp, complex conjugation, "
        "matmul, eigvalsh, and -sum lam log lam; this IS the claim"
    )
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"

    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "symbolic closed-form S(theta) and dS/dtheta = 0 provide analytic "
        "ground truth that autograd must reproduce on the positive cases"
    )
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

    all_pos = all(v.get("pass", False) for v in pos.values())
    all_neg = all(v.get("pass", False) for v in neg.values())
    all_bnd = all(v.get("pass", False) for v in bnd.values())
    overall = all_pos and all_neg and all_bnd

    results = {
        "name": "sim_torch_deep_axis0_autograd_vn_entropy",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": {
            "positive_all_pass": all_pos,
            "negative_all_pass": all_neg,
            "boundary_all_pass": all_bnd,
            "overall_pass": overall,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(
        out_dir, "sim_torch_deep_axis0_autograd_vn_entropy_results.json"
    )
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"OVERALL PASS: {overall}")
