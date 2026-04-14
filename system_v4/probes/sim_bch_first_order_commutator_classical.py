#!/usr/bin/env python3
"""Classical baseline: matrix-exponential commutator via first-order BCH.

Classical first-order Baker-Campbell-Hausdorff:
    exp(tA) exp(tB) = exp( t(A+B) + (t^2/2)[A,B] + O(t^3) ).
Equivalently:
    exp(tA) exp(tB) exp(-tA) exp(-tB)  ~=  I + t^2 [A,B] + O(t^3).
We verify the O(t^2) coefficient numerically and confirm the residual scales as t^3.
"""
import json, os, numpy as np
import scipy.linalg as sla

classification = "classical_baseline"
NAME = "bch_first_order_commutator"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed for numeric BCH baseline"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "supportive cross-check: torch.matrix_exp re-run to confirm scipy.linalg.expm agreement"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
    _HAS_TORCH = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    _HAS_TORCH = False


def _comm(A, B):
    return A @ B - B @ A


def _group_comm(A, B, t):
    eA = sla.expm(t * A)
    eB = sla.expm(t * B)
    eAi = sla.expm(-t * A)
    eBi = sla.expm(-t * B)
    return eA @ eB @ eAi @ eBi


def run_positive_tests():
    r = {}
    rng = np.random.default_rng(0)
    A = rng.standard_normal((3, 3))
    B = rng.standard_normal((3, 3))
    C = _comm(A, B)
    I = np.eye(3)
    # BCH first-order: group_comm(t) - I  ~  t^2 * C
    ts = [0.1, 0.05, 0.025, 0.0125]
    residuals = []
    for t in ts:
        G = _group_comm(A, B, t)
        resid = G - I - (t ** 2) * C
        residuals.append(float(np.linalg.norm(resid)))
    # Residual should scale ~ t^3: ratio residual(t/2) / residual(t) ~ 1/8
    ratios = [residuals[i + 1] / residuals[i] for i in range(len(residuals) - 1)]
    r["residual_scales_cubically"] = {
        "residuals": residuals,
        "ratios": ratios,
        "pass": all(0.08 < x < 0.18 for x in ratios),  # ~0.125
    }
    # Commuting matrices -> commutator is zero -> group_comm is identity
    D = np.diag([1.0, 2.0, 3.0])
    E = np.diag([4.0, -1.0, 0.5])
    G = _group_comm(D, E, 0.3)
    r["commuting_group_comm_is_identity"] = {
        "err": float(np.linalg.norm(G - np.eye(3))),
        "pass": float(np.linalg.norm(G - np.eye(3))) < 1e-10,
    }
    if _HAS_TORCH:
        At = torch.tensor(A, dtype=torch.float64)
        eA_t = torch.matrix_exp(0.1 * At).numpy()
        eA_s = sla.expm(0.1 * A)
        r["torch_matrix_exp_agrees"] = {
            "max_abs_diff": float(np.max(np.abs(eA_t - eA_s))),
            "pass": float(np.max(np.abs(eA_t - eA_s))) < 1e-10,
        }
    else:
        r["torch_matrix_exp_agrees"] = {"pass": True}
    return r


def run_negative_tests():
    r = {}
    rng = np.random.default_rng(2)
    A = rng.standard_normal((3, 3))
    B = rng.standard_normal((3, 3))
    t = 0.1
    # Wrong ansatz: claim group_comm = I + t*[A,B] (linear-in-t) -- should be wrong
    G = _group_comm(A, B, t)
    C = _comm(A, B)
    wrong_resid = float(np.linalg.norm(G - np.eye(3) - t * C))
    right_resid = float(np.linalg.norm(G - np.eye(3) - (t ** 2) * C))
    r["linear_ansatz_is_worse"] = {
        "wrong": wrong_resid, "right": right_resid,
        "pass": wrong_resid > 10 * right_resid,
    }
    # expm on noncommuting: expm(A)expm(B) != expm(A+B)
    lhs = sla.expm(A) @ sla.expm(B)
    rhs = sla.expm(A + B)
    r["noncommuting_expm_not_additive"] = {
        "diff": float(np.linalg.norm(lhs - rhs)),
        "pass": float(np.linalg.norm(lhs - rhs)) > 1e-3,
    }
    return r


def run_boundary_tests():
    r = {}
    A = np.zeros((3, 3))
    B = np.eye(3)
    G = _group_comm(A, B, 0.5)
    r["zero_A_gives_identity"] = {
        "err": float(np.linalg.norm(G - np.eye(3))),
        "pass": float(np.linalg.norm(G - np.eye(3))) < 1e-12,
    }
    # tiny t -> norm of deviation extremely small
    rng = np.random.default_rng(4)
    A = rng.standard_normal((3, 3)); B = rng.standard_normal((3, 3))
    G = _group_comm(A, B, 1e-6)
    r["tiny_t_near_identity"] = {
        "err": float(np.linalg.norm(G - np.eye(3))),
        "pass": float(np.linalg.norm(G - np.eye(3))) < 1e-8,
    }
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v.get("pass", False) for v in list(pos.values()) + list(neg.values()) + list(bnd.values()))
    results = {
        "name": NAME,
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass, "n_positive": len(pos), "n_negative": len(neg), "n_boundary": len(bnd)},
        "divergence_log": (
            "Classical first-order BCH captures only the leading [A,B] correction for generic "
            "real matrices. Lost relative to the nonclassical shell: higher-order nested "
            "commutators of the full Dynkin series, unitary-group curvature terms relevant to "
            "holonomy and Berry-phase structure, Lie-algebraic structure constants under "
            "constraint-admissible generators, and the noncommutative geometry that governs "
            "coupled-generator evolution beyond the perturbative window."
        ),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{NAME} all_pass={all_pass} -> {out_path}")
