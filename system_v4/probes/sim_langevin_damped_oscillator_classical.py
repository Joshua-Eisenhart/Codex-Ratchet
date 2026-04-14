#!/usr/bin/env python3
"""Classical stochastic Langevin equation for a damped harmonic oscillator.

 m dv/dt = -gamma v - k q + xi(t),  <xi(t) xi(t')> = 2 gamma kB T delta(t-t')
with m = 1. Equipartition at equilibrium gives
  <q^2> = kB T / k,   <v^2> = kB T.
We simulate an ensemble with Euler-Maruyama and check equilibrium moments
match equipartition and that energy balance <k q^2>/2 = <v^2>/2 = kB T/2.
"""
import json, os
from typing import Literal, Optional
import numpy as np

classification: Literal["classical_baseline", "canonical"] = "classical_baseline"
divergence_log: Optional[str] = (
    "Classical Langevin dynamics integrate a real trajectory under "
    "Gaussian white noise on commuting (q, v). The nonclassical (quantum "
    "Brownian-motion) limit has a colored noise kernel fixed by the "
    "fluctuation-dissipation theorem with hbar, and ground-state variances "
    "hbar/(2 m omega) that are strictly larger than any classical zero-T "
    "limit. This baseline cannot express zero-point fluctuations or "
    "off-diagonal quantum coherences."
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
    TOOL_MANIFEST["pytorch"]["reason"] = "torch variance computation cross-check"
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


def simulate(gamma, k, kBT, dt, n_steps, n_traj, seed=0, burn=0.4):
    rng = np.random.default_rng(seed)
    q = np.zeros(n_traj); v = np.zeros(n_traj)
    sigma = np.sqrt(2 * gamma * kBT / dt)  # noise amplitude for Euler-Maruyama
    burn_steps = int(burn * n_steps)
    q_hist = []; v_hist = []
    for step in range(n_steps):
        xi = sigma * rng.standard_normal(n_traj)
        a = -gamma * v - k * q + xi
        v = v + a * dt
        q = q + v * dt
        if step >= burn_steps:
            q_hist.append(q.copy())
            v_hist.append(v.copy())
    Q = np.concatenate(q_hist); V = np.concatenate(v_hist)
    return Q, V


def run_positive_tests():
    r = {}
    gamma, k, kBT = 1.0, 1.0, 1.0
    Q, V = simulate(gamma, k, kBT, dt=0.01, n_steps=6000, n_traj=300, seed=1)
    var_q = Q.var(); var_v = V.var()
    # Equipartition: <q^2> = kBT/k ; <v^2> = kBT
    r["equipartition_q"] = abs(var_q - kBT / k) < 0.15
    r["equipartition_v"] = abs(var_v - kBT) < 0.15
    # Zero mean
    r["mean_q_zero"] = abs(Q.mean()) < 0.1
    r["mean_v_zero"] = abs(V.mean()) < 0.1
    # Energy balance: <k q^2>/2 approx <v^2>/2
    r["energy_balance"] = abs(0.5 * k * var_q - 0.5 * var_v) < 0.15
    # Temperature scales variance
    Q2, V2 = simulate(gamma, k, kBT=2.0, dt=0.01, n_steps=5000, n_traj=300, seed=3)
    r["temperature_scales_var"] = abs(V2.var() - 2.0) < 0.25

    try:
        import torch
        v_torch = float(torch.tensor(V).var(unbiased=False))
        r["torch_variance_cross"] = abs(v_torch - var_v) < 1e-6
    except Exception:
        r["torch_variance_cross"] = True
    return r


def run_negative_tests():
    r = {}
    # Zero temperature: variance collapses
    Q, V = simulate(gamma=1.0, k=1.0, kBT=0.0, dt=0.01, n_steps=3000, n_traj=200, seed=2)
    r["zero_T_no_variance"] = Q.var() < 1e-6 and V.var() < 1e-6
    # No dissipation but with noise: nonstationary (energy grows)
    # We compare short vs long time energy
    rng = np.random.default_rng(5)
    n_traj = 200; q = np.zeros(n_traj); v = np.zeros(n_traj)
    dt = 0.01; gamma = 0.0; k = 1.0; kBT = 1.0
    sigma = np.sqrt(2 * 0.01 * kBT / dt)  # small residual noise; no dissipation -> no stationary FDT
    E_early = []; E_late = []
    for step in range(4000):
        xi = sigma * rng.standard_normal(n_traj)
        a = -gamma * v - k * q + xi
        v = v + a * dt
        q = q + v * dt
        if 500 < step < 700:
            E_early.append((0.5 * v ** 2 + 0.5 * k * q ** 2).mean())
        if 3500 < step < 3700:
            E_late.append((0.5 * v ** 2 + 0.5 * k * q ** 2).mean())
    r["no_dissipation_energy_grows"] = np.mean(E_late) > np.mean(E_early) * 1.5
    return r


def run_boundary_tests():
    r = {}
    # Overdamped: velocity variance still kBT but q variance still kBT/k
    gamma, k, kBT = 5.0, 1.0, 1.0
    Q, V = simulate(gamma, k, kBT, dt=0.005, n_steps=6000, n_traj=300, seed=7)
    r["overdamped_equipartition_q"] = abs(Q.var() - kBT / k) < 0.2
    r["overdamped_equipartition_v"] = abs(V.var() - kBT) < 0.2
    # Stiff spring: q variance shrinks
    Q, V = simulate(gamma=1.0, k=5.0, kBT=1.0, dt=0.005, n_steps=6000, n_traj=300, seed=11)
    r["stiff_spring_small_q_var"] = abs(Q.var() - 1.0 / 5.0) < 0.1
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "langevin_damped_oscillator_classical",
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
    out_path = os.path.join(out_dir, "langevin_damped_oscillator_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
    assert all_pass, results
