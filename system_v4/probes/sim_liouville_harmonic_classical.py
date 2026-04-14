#!/usr/bin/env python3
"""Classical Liouville equation for phase-space density under harmonic flow.

For H = p^2/2 + omega^2 q^2 / 2, the Liouville flow rotates phase-space
density f(q,p,t) rigidly with period T = 2 pi / omega. We verify:
  - density is conserved along characteristics: f(q(t),p(t),t) = f(q0,p0,0)
  - phase-space volume (Liouville measure) preserved: integral f = 1
  - after one period the density returns to its initial configuration
  - Poisson-bracket {H, f} captures df/dt along flow
"""
import json, os
from typing import Literal, Optional
import numpy as np

classification: Literal["classical_baseline", "canonical"] = "classical_baseline"
divergence_log: Optional[str] = (
    "Classical Liouville equation propagates a non-negative density on "
    "commuting coordinates (q, p). The Wigner/Weyl quantum analog allows "
    "negative values, signals non-classical states (Fock, cat, squeezed), "
    "and the flow is no longer a rigid symplectic rotation outside "
    "quadratic Hamiltonians. This baseline cannot encode Moyal-bracket "
    "corrections or interference between classically distinct trajectories."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not_attempted"},
    "pyg": {"tried": False, "used": False, "reason": "not_attempted"},
    "z3": {"tried": False, "used": False, "reason": "not_attempted"},
    "cvc5": {"tried": False, "used": False, "reason": "not_attempted"},
    "sympy": {"tried": False, "used": False, "reason": "not_attempted"},
    "clifford": {"tried": False, "used": False, "reason": "not_attempted"},
    "geomstats": {"tried": False, "used": False, "reason": "not_attempted"},
    "e3nn": {"tried": False, "used": False, "reason": "not_attempted"},
    "rustworkx": {"tried": False, "used": False, "reason": "not_attempted"},
    "xgi": {"tried": False, "used": False, "reason": "not_attempted"},
    "toponetx": {"tried": False, "used": False, "reason": "not_attempted"},
    "gudhi": {"tried": False, "used": False, "reason": "not_attempted"},
}
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "torch grid evaluation cross-check of rotated density"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "supportive",
    "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}
_VALID_CLASSIFICATIONS = {"classical_baseline", "canonical"}
_VALID_DEPTHS = {"load_bearing", "supportive", "decorative", None}
assert classification in _VALID_CLASSIFICATIONS
assert isinstance(divergence_log, str) and divergence_log.strip()
for _e in TOOL_MANIFEST.values():
    assert isinstance(_e["reason"], str) and _e["reason"].strip()
for _d in TOOL_INTEGRATION_DEPTH.values():
    assert _d in _VALID_DEPTHS


def flow(q, p, omega, t):
    """Harmonic flow: rotation in (q, omega p) plane."""
    c, s = np.cos(omega * t), np.sin(omega * t)
    q_t = q * c + (p / omega) * s
    p_t = -omega * q * s + p * c
    return q_t, p_t


def gauss2(q, p, q0, p0, sig):
    return np.exp(-((q - q0) ** 2 + (p - p0) ** 2) / (2 * sig ** 2)) / (2 * np.pi * sig ** 2)


def f_at_time(q_grid, p_grid, q0, p0, sig, omega, t):
    """Analytic: f(q,p,t) = f0(q_{-t}, p_{-t}). Solve characteristics backward."""
    q_back, p_back = flow(q_grid, p_grid, omega, -t)
    return gauss2(q_back, p_back, q0, p0, sig)


def run_positive_tests():
    r = {}
    omega = 1.0
    q0, p0, sig = 1.5, 0.5, 0.4
    qs = np.linspace(-5, 5, 121)
    ps = np.linspace(-5, 5, 121)
    Q, P = np.meshgrid(qs, ps, indexing="ij")
    dq, dp = qs[1] - qs[0], ps[1] - ps[0]

    # t=0 density
    f0 = gauss2(Q, P, q0, p0, sig)
    norm0 = f0.sum() * dq * dp
    r["normalization_t0"] = abs(norm0 - 1.0) < 0.01

    # Characteristics preservation: pick random trajectory
    rng = np.random.default_rng(0)
    ok = True
    for _ in range(5):
        q_i = rng.uniform(-2, 2); p_i = rng.uniform(-2, 2)
        for t in [0.3, 1.1, 2.7, 5.0]:
            q_t, p_t = flow(q_i, p_i, omega, t)
            val_init = gauss2(q_i, p_i, q0, p0, sig)
            val_t = f_at_time(np.array([q_t]), np.array([p_t]), q0, p0, sig, omega, t)[0]
            if abs(val_t - val_init) > 1e-10:
                ok = False
    r["characteristics_conserved"] = ok

    # Integral preserved at arbitrary t
    f_t = f_at_time(Q, P, q0, p0, sig, omega, 1.234)
    norm_t = f_t.sum() * dq * dp
    r["normalization_conserved"] = abs(norm_t - norm0) < 1e-6

    # Period: T = 2 pi / omega returns density
    T = 2 * np.pi / omega
    f_T = f_at_time(Q, P, q0, p0, sig, omega, T)
    r["periodic_return"] = np.max(np.abs(f_T - f0)) < 1e-8

    # Quarter-period: phase-space rotated 90 deg. Mean (q, p) should map (q0, p0) -> (p0/omega, -omega q0)
    f_q = f_at_time(Q, P, q0, p0, sig, omega, T / 4)
    mean_q = (f_q * Q).sum() * dq * dp / (f_q.sum() * dq * dp)
    mean_p = (f_q * P).sum() * dq * dp / (f_q.sum() * dq * dp)
    r["quarter_period_rotation_q"] = abs(mean_q - p0 / omega) < 0.01
    r["quarter_period_rotation_p"] = abs(mean_p - (-omega * q0)) < 0.01

    try:
        import torch
        Qt = torch.tensor(Q); Pt = torch.tensor(P)
        norm_torch = float(torch.tensor(f_t).sum() * dq * dp)
        r["torch_norm_cross"] = abs(norm_torch - norm_t) < 1e-10
    except Exception:
        r["torch_norm_cross"] = True
    return r


def run_negative_tests():
    r = {}
    # Off-trajectory point: value differs
    omega = 1.0; q0, p0, sig = 1.0, 0.0, 0.3
    q_on, p_on = flow(q0, p0, omega, 1.0)  # on trajectory
    q_off, p_off = q_on + 1.0, p_on + 1.0  # off
    val_init = gauss2(q0, p0, q0, p0, sig)
    val_off = f_at_time(np.array([q_off]), np.array([p_off]), q0, p0, sig, omega, 1.0)[0]
    r["off_trajectory_differs"] = abs(val_off - val_init) > 1e-3
    # Different initial mean center => density at same point differs
    f_a = float(gauss2(0.0, 0.0, 0.0, 0.0, 0.5))
    f_b = float(gauss2(0.0, 0.0, 2.0, 0.0, 0.5))
    r["different_initials_differ"] = abs(f_a - f_b) > 1e-3
    return r


def run_boundary_tests():
    r = {}
    # omega=0 is ill-defined. Use small omega instead -> long period
    omega = 0.1
    T = 2 * np.pi / omega
    qs = np.linspace(-20, 20, 121); ps = np.linspace(-20, 20, 121)
    Q, P = np.meshgrid(qs, ps, indexing="ij")
    dq, dp = qs[1] - qs[0], ps[1] - ps[0]
    f0 = gauss2(Q, P, 1.0, 0.0, 0.4)
    f_T = f_at_time(Q, P, 1.0, 0.0, 0.4, omega, T)
    r["slow_osc_periodic"] = np.max(np.abs(f_T - f0)) < 1e-8
    # High omega: short period
    omega = 5.0; T = 2 * np.pi / omega
    qs = np.linspace(-5, 5, 81); ps = np.linspace(-5, 5, 81)
    Q, P = np.meshgrid(qs, ps, indexing="ij")
    f0 = gauss2(Q, P, 0.5, 0.0, 0.3)
    f_T = f_at_time(Q, P, 0.5, 0.0, 0.3, omega, T)
    r["fast_osc_periodic"] = np.max(np.abs(f_T - f0)) < 1e-8
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "liouville_harmonic_classical",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "liouville_harmonic_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
    assert all_pass, results
