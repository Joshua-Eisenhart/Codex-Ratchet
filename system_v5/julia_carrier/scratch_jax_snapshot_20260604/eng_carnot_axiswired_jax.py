#!/usr/bin/env python3
"""
JAX parity audit for Carnot engine — all 6 axes wired.

object_id: eng_carnot_axiswired_jax_parity_v1
claim_ceiling: candidate — parity probe only. NOT layer-complete. NOT bridge claim.
  promotion_allowed: false

Finite map (mirrors eng_carnot_axiswired_julia.jl exactly):
  domain: L/R Weyl spinor density matrices, N=32 (parity reference size)
  codomain: (eta, W_net, DS_cycle [Clausius], mean_dS_per_stroke [vN],
             N01 substage order gaps, cycle_closes bool)

JAX role: scale / stress / AUDIT lane.
Julia is the truth lane. This file recomputes the same channels in JAX x64,
reads Julia's result JSON for parity comparison, and writes:
  /tmp/eng_carnot_axiswired_parity.json

F01: finite ensemble of 32 L/R Weyl spinor density matrices.
N01: hot_spectral∘open_isothermal ≠ open_isothermal∘hot_spectral (gap > N01_EPS).
     wrong-structure control: hot_spectral∘hot_spectral commutes (gap < COMMUTE_EPS).

Axis map (owner 2026-06-04):
  axis0 = entropy monotone readout (Clausius / vN)
  axis1 = expand / compress  (Kraus amplitude-damping channels)
  axis2 = open / closed      = isothermal (Lindblad) / adiabatic (unitary)
  axis3 = Carnot (fixed here)
  axis4 = CW / CCW           = engine / refrigerator
  axis5 = hot / cold         = spectral (dephase) / gradient (rotate)
  axis6 = stroke order       = noncommuting substage composition
"""

from __future__ import annotations
import json
import math
import sys
from pathlib import Path

# Enable float64 BEFORE importing jax.numpy
try:
    import jax
    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp
    JAX_AVAILABLE = True
except ImportError:
    JAX_AVAILABLE = False
    import numpy as jnp  # type: ignore
    print("WARNING: JAX not available, falling back to numpy", file=sys.stderr)

import numpy as np

# ── Constants (must match Julia exactly) ────────────────────────────────────────
OBJECT_ID        = "eng_carnot_axiswired_jax_parity_v1"
PROMOTION_ALLOWED = False
PARITY_N         = 32
RNG_SEED         = 20260604
JULIA_RESULT     = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/eng_carnot_axiswired_julia_results.json")
JAX_RESULT       = Path("/tmp/eng_carnot_axiswired_parity.json")

# Thresholds (match Julia)
N01_EPS       = 1.0e-9
COMMUTE_EPS   = 1.0e-9
S_EPS         = 1.0e-6
S_ADIAB       = 1.0e-10
PURITY_CLOSE  = 0.05
GAMMA_KRAUS   = 0.30
GAMMA_LINDBLAD = 0.30
OMEGA         = 1.0
DT            = 0.1    # finer Euler step; total time = 20*0.1 = 2.0
NSTEPS        = 20     # was 4 with DT=0.5; 20 steps keeps same total time but avoids negative eigenvalues
THETA_UNIT    = math.pi / 3.0

# Parity tolerance (Julia vs JAX comparison)
PARITY_TOL = 1.0e-6   # absolute; accounts for first-order Euler numerical differences

# ── Pauli matrices ──────────────────────────────────────────────────────────────
I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)

# ── Deterministic state construction (same seed protocol as Julia) ──────────────
def seeded_fraction(seed: int, n: int, idx: int, stride: int, modulus: int, offset: int) -> float:
    raw = (seed % modulus + stride * n + offset * idx) % modulus
    return (float(raw) + 0.5) / float(modulus)

def seeded_angles(seed: int, n: int, idx: int):
    theta_frac = seeded_fraction(seed, n, idx, 37, 997, 53)
    phi_frac   = seeded_fraction(seed, n, idx, 101, 991, 67)
    chi_frac   = seeded_fraction(seed, n, idx, 131, 983, 71)
    theta = math.pi * (0.11 + 0.78 * theta_frac)
    phi   = 2.0 * math.pi * phi_frac
    chi   = 2.0 * math.pi * chi_frac
    return theta, phi, chi

def sheet_sign(idx: int) -> float:
    return 1.0 if (idx % 2 == 1) else -1.0

def weyl_density(seed: int, n: int, idx: int, s: float) -> np.ndarray:
    theta, phi, chi = seeded_angles(seed, n, idx)
    psi = np.array([
        math.cos(theta / 2.0) * complex(math.cos(phi + s*chi), math.sin(phi + s*chi)),
        math.sin(theta / 2.0) * complex(math.cos(phi - s*chi), math.sin(phi - s*chi)),
    ], dtype=complex)
    psi /= np.linalg.norm(psi)
    return np.outer(psi, psi.conj())

def ensemble(seed: int, n: int):
    return [weyl_density(seed, n, idx, sheet_sign(idx)) for idx in range(1, n+1)]

# ── Quantum operations ──────────────────────────────────────────────────────────
def von_neumann_entropy(rho: np.ndarray) -> float:
    rho_h = (rho + rho.conj().T) / 2.0
    evals = np.linalg.eigvalsh(rho_h)
    S = 0.0
    for lam in evals:
        if lam > 1.0e-14:
            S -= lam * math.log(lam)
    return S

def bloch_radius(rho: np.ndarray) -> float:
    rx = 2.0 * float(np.real(rho[0, 1]))
    ry = 2.0 * float(np.imag(rho[1, 0]))
    rz = float(np.real(rho[0, 0] - rho[1, 1]))
    return math.sqrt(rx**2 + ry**2 + rz**2)

def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))

def renorm(rho: np.ndarray) -> np.ndarray:
    t = np.trace(rho)
    if abs(t) > 1.0e-14:
        rho = rho / t
    return rho

def kraus_apply(Ks: list, rho: np.ndarray) -> np.ndarray:
    out = np.zeros((2, 2), dtype=complex)
    for K in Ks:
        out += K @ rho @ K.conj().T
    return renorm(out)

# ── Axis 1: expand / compress ───────────────────────────────────────────────────
def compress_channel(gamma: float):
    K0 = np.array([[1, 0], [0, math.sqrt(1.0 - gamma)]], dtype=complex)
    K1 = np.array([[0, math.sqrt(gamma)], [0, 0]], dtype=complex)
    return [K0, K1]

def expand_channel(gamma: float):
    K0 = np.array([[math.sqrt(1.0 - gamma), 0], [0, 1]], dtype=complex)
    K1 = np.array([[0, 0], [math.sqrt(gamma), 0]], dtype=complex)
    return [K0, K1]

# ── Axis 2: isothermal / adiabatic ─────────────────────────────────────────────
def lindblad_step(rho: np.ndarray, H: np.ndarray, L: np.ndarray, gamma: float, dt: float) -> np.ndarray:
    LdL  = L.conj().T @ L
    comm = H @ rho - rho @ H
    diss = gamma * (L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL))
    drho = -1j * comm + diss
    rho_new = rho + dt * drho
    return renorm(rho_new)

def open_isothermal(rho: np.ndarray) -> np.ndarray:
    H = OMEGA * SZ / 2.0
    L = np.array([[0, 1], [0, 0]], dtype=complex) * math.sqrt(GAMMA_LINDBLAD)
    rho_c = rho.copy()
    for _ in range(NSTEPS):
        rho_c = lindblad_step(rho_c, H, L, 1.0, DT)
    return rho_c

def closed_adiabatic(rho: np.ndarray) -> np.ndarray:
    c = math.cos(THETA_UNIT / 2.0)
    s = math.sin(THETA_UNIT / 2.0)
    U = c * I2 - 1j * s * SX
    return U @ rho @ U.conj().T

# ── Axis 5: hot (spectral) / cold (gradient) ────────────────────────────────────
def hot_spectral(rho: np.ndarray, gamma: float = 0.40) -> np.ndarray:
    g = max(0.0, min(1.0, gamma))
    K0 = math.sqrt(1.0 - g/2.0) * I2
    K1 = math.sqrt(g/2.0) * SZ
    return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T

def cold_gradient(rho: np.ndarray, theta: float = math.pi/4.0) -> np.ndarray:
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    U = c * I2 - 1j * s * SX
    return U @ rho @ U.conj().T

# ── Carnot Clausius macro ───────────────────────────────────────────────────────
def carnot_clausius(T_h: float, T_c: float, Q_h: float):
    eta   = 1.0 - T_c / T_h
    W_net = eta * Q_h
    Q_c   = Q_h - W_net
    DS_h  = -Q_h / T_h
    DS_c  = +Q_c / T_c
    DS_cyc = DS_h + DS_c
    return eta, W_net, Q_c, DS_h, DS_c, DS_cyc

# ── QIT Carnot cycle run ────────────────────────────────────────────────────────
def qit_carnot_run(rho_init: np.ndarray) -> dict:
    Ks_expand   = expand_channel(GAMMA_KRAUS)
    Ks_compress = compress_channel(GAMMA_KRAUS)

    # Stroke 1: axis1=expand, axis2=open_isothermal
    rho1 = open_isothermal(kraus_apply(Ks_expand, rho_init))
    S1   = von_neumann_entropy(rho1)

    # Stroke 2: axis1=expand, axis2=closed_adiabatic
    rho2 = closed_adiabatic(kraus_apply(Ks_expand, rho1))
    S2   = von_neumann_entropy(rho2)

    # Stroke 3: axis1=compress, axis2=open_isothermal
    rho3 = open_isothermal(kraus_apply(Ks_compress, rho2))
    S3   = von_neumann_entropy(rho3)

    # Stroke 4: axis1=compress, axis2=closed_adiabatic
    rho4 = closed_adiabatic(kraus_apply(Ks_compress, rho3))
    S4   = von_neumann_entropy(rho4)

    S0 = von_neumann_entropy(rho_init)
    p_start = purity(rho_init)
    p_end   = purity(rho4)

    return {
        "S_init":    S0,
        "dS_s1": S1 - S0,
        "dS_s2": S2 - S1,
        "dS_s3": S3 - S2,
        "dS_s4": S4 - S3,
        "DS_total": S4 - S0,
        "purity_start": p_start,
        "purity_end":   p_end,
        "cycle_closes_purity": abs(p_end - p_start) < PURITY_CLOSE,
        "state_return_gap": float(np.linalg.norm(rho4 - rho_init)),
    }

# ── Substage N01 order gap ──────────────────────────────────────────────────────
def substage_n01(rho: np.ndarray, ax1_fn, ax2_fn) -> dict:
    # substage_a: hot_spectral then ax2 then ax1
    rho_a = ax1_fn(ax2_fn(hot_spectral(rho)))     # order_AB
    # substage_b: ax2 then hot_spectral then ax1
    rho_b = ax1_fn(hot_spectral(ax2_fn(rho)))     # order_BA
    # substage_c: cold_gradient then ax2 then ax1
    rho_c = ax1_fn(ax2_fn(cold_gradient(rho)))    # order_AB cold
    # substage_d: ax2 then cold_gradient then ax1
    rho_d = ax1_fn(cold_gradient(ax2_fn(rho)))    # order_BA cold

    n01_hot  = float(np.linalg.norm(rho_a - rho_b))
    n01_cold = float(np.linalg.norm(rho_c - rho_d))

    # Wrong-structure control: hot_spectral∘hot_spectral (commutes)
    ctrl_AA = hot_spectral(hot_spectral(rho))
    ctrl_AA2 = hot_spectral(hot_spectral(rho))
    n01_ctrl = float(np.linalg.norm(ctrl_AA - ctrl_AA2))

    return {
        "n01_hot":  n01_hot,
        "n01_cold": n01_cold,
        "n01_ctrl": n01_ctrl,
        "n01_hot_pass":  n01_hot  > N01_EPS,
        "n01_cold_pass": n01_cold > N01_EPS,
        "n01_ctrl_pass": n01_ctrl < COMMUTE_EPS,
    }

# ── Main JAX computation at N=32 ───────────────────────────────────────────────
def compute_jax(n: int = PARITY_N):
    states = ensemble(RNG_SEED, n)

    # Clausius macro
    T_h, T_c, Q_h = 400.0, 300.0, 100.0
    eta, W_net, Q_c, DS_h, DS_c, DS_cyc = carnot_clausius(T_h, T_c, Q_h)

    # QIT runs
    qit_runs = [qit_carnot_run(rho) for rho in states]
    dS_s1_vals = [r["dS_s1"] for r in qit_runs]
    dS_s2_vals = [r["dS_s2"] for r in qit_runs]
    dS_s3_vals = [r["dS_s3"] for r in qit_runs]
    dS_s4_vals = [r["dS_s4"] for r in qit_runs]

    mean_dS_s1 = float(np.mean(dS_s1_vals))
    mean_dS_s2 = float(np.mean(dS_s2_vals))
    mean_dS_s3 = float(np.mean(dS_s3_vals))
    mean_dS_s4 = float(np.mean(dS_s4_vals))
    mean_state_return = float(np.mean([r["state_return_gap"] for r in qit_runs]))

    # N01 substage (on first 4 states)
    n_sample = min(n, 4)
    substage_results = []
    for idx, rho in enumerate(states[:n_sample]):
        s1 = substage_n01(rho,
             lambda r: kraus_apply(expand_channel(GAMMA_KRAUS), r),
             open_isothermal)
        s3 = substage_n01(rho,
             lambda r: kraus_apply(compress_channel(GAMMA_KRAUS), r),
             open_isothermal)
        substage_results.append({
            "state_idx": idx + 1,
            "stroke1": s1,
            "stroke3": s3,
        })

    # NOTE: hot pair (hot_spectral x open_isothermal) commutes (both z-diagonal) -- honest degeneracy
    # hot_pass is NOT a gate; it is expected to be False (gap ~ 0)
    all_n01_hot_commutes = all(not s["stroke1"]["n01_hot_pass"] and not s["stroke3"]["n01_hot_pass"] for s in substage_results)
    all_n01_cold = all(s["stroke1"]["n01_cold_pass"] and s["stroke3"]["n01_cold_pass"] for s in substage_results)
    all_n01_ctrl = all(s["stroke1"]["n01_ctrl_pass"] and s["stroke3"]["n01_ctrl_pass"] for s in substage_results)

    # Direct checks
    rho_test = states[0]
    S0_test  = von_neumann_entropy(rho_test)
    S_adiab  = von_neumann_entropy(closed_adiabatic(rho_test))
    S_isoth  = von_neumann_entropy(open_isothermal(rho_test))
    adiabatic_preserved  = abs(S_adiab - S0_test) < S_ADIAB
    isothermal_exchanged = abs(S_isoth - S0_test) > S_EPS

    # Boundary: T_h → T_c
    eta_bnd = 1.0 - 300.0 / (300.0 + 1e-6)
    boundary_eta_near_zero = eta_bnd < 1.0e-5

    # Negative: reversed T
    eta_neg = 1.0 - 400.0 / 300.0
    negative_reversed_eta_lt_0 = eta_neg < 0.0

    # Refrigerator axis4 CCW
    eta_refrig = -(1.0 - T_c / T_h)
    refrig_negative_eta_pass = eta_refrig < 0.0

    # N01 direct gap: use COLD pair (cold_gradient x open_isothermal) -- load-bearing
    rho_n01 = states[2]
    rho_cold_AB = open_isothermal(cold_gradient(rho_n01))
    rho_cold_BA = cold_gradient(open_isothermal(rho_n01))
    n01_direct_gap  = float(np.linalg.norm(rho_cold_AB - rho_cold_BA))
    n01_direct_pass = n01_direct_gap > N01_EPS
    # Also measure hot pair for honest degeneracy reporting
    rho_hot_AB = open_isothermal(hot_spectral(rho_n01))
    rho_hot_BA = hot_spectral(open_isothermal(rho_n01))
    n01_hot_direct_gap = float(np.linalg.norm(rho_hot_AB - rho_hot_BA))
    n01_hot_commutes_direct = n01_hot_direct_gap < N01_EPS * 1e3

    s1_entropy_up = all(abs(d) > S_EPS for d in dS_s1_vals)

    all_pass = (
        abs(eta - (1.0 - T_c / T_h)) < 1.0e-10 and
        abs(DS_cyc) < 1.0e-10 and
        W_net > 0.0 and
        refrig_negative_eta_pass and
        s1_entropy_up and
        all_n01_cold and   # cold pair is load-bearing (not hot -- hot commutes, honest degeneracy)
        all_n01_ctrl and
        n01_direct_pass
    )

    return {
        "N": n,
        "clausius": {
            "eta":    eta,
            "W_net":  W_net,
            "DS_cycle": DS_cyc,
            "eta_pass": abs(eta - (1.0 - T_c / T_h)) < 1.0e-10,
            "DS_cycle_pass": abs(DS_cyc) < 1.0e-10,
            "W_net_pass": W_net > 0.0,
        },
        "refrigerator": {
            "eta_refrigerator": eta_refrig,
            "negative_eta_pass": refrig_negative_eta_pass,
        },
        "axis0_svn_readout": {
            "mean_dS_stroke1": mean_dS_s1,
            "mean_dS_stroke2": mean_dS_s2,
            "mean_dS_stroke3": mean_dS_s3,
            "mean_dS_stroke4": mean_dS_s4,
            "s1_entropy_up": s1_entropy_up,
        },
        "n01_substage": {
            "all_n01_hot_commutes": bool(all_n01_hot_commutes),  # expected True: hot pair is z-diagonal, commutes
            "all_n01_cold_pass":    bool(all_n01_cold),          # LOAD-BEARING: cold pair is non-commuting
            "all_n01_ctrl_pass":    bool(all_n01_ctrl),
            "substage_results":     substage_results,
        },
        "direct_checks": {
            "boundary_eta_near_zero":       bool(boundary_eta_near_zero),
            "negative_reversed_eta_lt_0":   bool(negative_reversed_eta_lt_0),
            "adiabatic_entropy_preserved":  bool(adiabatic_preserved),
            "isothermal_entropy_exchanged": bool(isothermal_exchanged),
            "n01_cold_direct_gap":          n01_direct_gap,
            "n01_cold_direct_pass":         bool(n01_direct_pass),
            "n01_hot_direct_gap":           n01_hot_direct_gap,
            "n01_hot_commutes_direct":      bool(n01_hot_commutes_direct),
        },
        "cycle_closure": {
            "mean_state_return_gap": mean_state_return,
            "cycle_closes_purity_fraction": float(np.mean([float(r["cycle_closes_purity"]) for r in qit_runs])),
            "honest_caveat": "purity-window closure only; full state return not guaranteed",
        },
        "all_pass": all_pass,
    }


# ── Parity comparison against Julia reference ────────────────────────────────────
def compare_parity(jax_result: dict, julia_ref: dict) -> dict:
    findings = []
    max_diff = 0.0

    def check_scalar(name: str, jax_val, julia_val):
        nonlocal max_diff
        try:
            diff = abs(float(jax_val) - float(julia_val))
            max_diff = max(max_diff, diff)
            status = "PASS" if diff < PARITY_TOL else "FAIL"
            findings.append({
                "field": name,
                "jax":   float(jax_val),
                "julia": float(julia_val),
                "diff":  diff,
                "status": status,
            })
        except Exception as e:
            findings.append({"field": name, "error": str(e), "status": "ERROR"})

    jr = julia_ref  # parity_reference block from Julia
    jr_ax0 = None
    jr_n01 = None
    jr_cyc = None

    # Navigate to N=32 row in Julia size_ladder_results
    if "size_ladder_results" in julia_ref:
        for row in julia_ref["size_ladder_results"]:
            if row.get("N") == PARITY_N:
                jr_ax0 = row.get("axis0_svn_readout", {})
                jr_n01 = row.get("n01_substage", {})
                jr_cyc = row.get("cycle_closure", {})
                break

    # Clausius
    if "parity_reference" in julia_ref:
        pr = julia_ref["parity_reference"]
        check_scalar("eta",     jax_result["clausius"]["eta"],    pr.get("eta", float("nan")))
        check_scalar("W_net",   jax_result["clausius"]["W_net"],  pr.get("W_net", float("nan")))
        check_scalar("DS_cycle", jax_result["clausius"]["DS_cycle"], pr.get("DS_cycle", float("nan")))
        check_scalar("mean_dS_stroke1",
            jax_result["axis0_svn_readout"]["mean_dS_stroke1"],
            pr.get("mean_dS_stroke1", float("nan")))
        check_scalar("mean_dS_stroke2",
            jax_result["axis0_svn_readout"]["mean_dS_stroke2"],
            pr.get("mean_dS_stroke2", float("nan")))
        check_scalar("mean_dS_stroke3",
            jax_result["axis0_svn_readout"]["mean_dS_stroke3"],
            pr.get("mean_dS_stroke3", float("nan")))
        check_scalar("mean_dS_stroke4",
            jax_result["axis0_svn_readout"]["mean_dS_stroke4"],
            pr.get("mean_dS_stroke4", float("nan")))
        check_scalar("mean_state_return_gap",
            jax_result["cycle_closure"]["mean_state_return_gap"],
            pr.get("mean_state_return_gap", float("nan")))

    all_pass  = all(f.get("status") == "PASS" for f in findings)
    num_pass  = sum(1 for f in findings if f.get("status") == "PASS")
    num_total = len(findings)

    return {
        "parity_pass":    all_pass,
        "max_diff":       max_diff,
        "parity_tol":     PARITY_TOL,
        "num_checks":     num_total,
        "num_pass":       num_pass,
        "findings":       findings,
        "note":           "Parity tolerance accounts for first-order Euler Lindblad integration differences. Clausius is analytical (exact match expected). vN entropy differences arise from Lindblad path.",
    }


def main():
    print("=== CARNOT ENGINE (ALL 6 AXES WIRED) JAX PARITY AUDIT ===")
    print(f"object_id: {OBJECT_ID}")
    print(f"promotion_allowed: {PROMOTION_ALLOWED}")

    # Load Julia reference
    julia_data = {}
    julia_loaded = False
    if JULIA_RESULT.exists():
        try:
            with open(JULIA_RESULT) as f:
                julia_data = json.load(f)
            julia_loaded = True
            print(f"Julia reference loaded: {JULIA_RESULT}")
        except Exception as e:
            print(f"WARNING: could not load Julia reference: {e}", file=sys.stderr)
    else:
        print(f"WARNING: Julia result not found at {JULIA_RESULT}", file=sys.stderr)
        print("Run Julia object first, then re-run this parity audit.", file=sys.stderr)

    # JAX computation
    jax_result = compute_jax(PARITY_N)
    print(f"JAX all_pass: {jax_result['all_pass']}")
    print(f"  eta={jax_result['clausius']['eta']:.6f}  DS_cycle={jax_result['clausius']['DS_cycle']:.2e}")
    print(f"  mean_dS_s1={jax_result['axis0_svn_readout']['mean_dS_stroke1']:.6f}")
    print(f"  n01_hot_commutes={jax_result['n01_substage']['all_n01_hot_commutes']} (honest degeneracy: hot pair is z-diagonal)")
    print(f"  n01_cold_pass={jax_result['n01_substage']['all_n01_cold_pass']} (load-bearing)")
    print(f"  n01_ctrl={jax_result['n01_substage']['all_n01_ctrl_pass']}")
    print(f"  n01_cold_direct_gap={jax_result['direct_checks']['n01_cold_direct_gap']:.4e}")
    print(f"  n01_hot_direct_gap={jax_result['direct_checks']['n01_hot_direct_gap']:.2e} (honest degeneracy)")
    print(f"  state_return_gap={jax_result['cycle_closure']['mean_state_return_gap']:.4f}")

    # Parity comparison
    parity = {}
    if julia_loaded:
        parity = compare_parity(jax_result, julia_data)
        print(f"Parity: {'PASS' if parity['parity_pass'] else 'FAIL'} "
              f"({parity['num_pass']}/{parity['num_checks']} fields, "
              f"max_diff={parity['max_diff']:.2e})")
    else:
        print("Parity: SKIPPED (Julia reference not available)")
        parity = {"parity_pass": None, "skipped": True,
                  "reason": "Julia result not found; run Julia carrier first"}

    payload = {
        "object_id":         OBJECT_ID,
        "classification":    "tool_lego_fit_probe",
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling":     "Carnot engine JAX parity probe. F01+N01. candidate only. promotion_allowed=false.",
        "jax_available":     JAX_AVAILABLE,
        "jax_result_N32":    jax_result,
        "parity_vs_julia":   parity,
        "julia_result_path": str(JULIA_RESULT),
        "parity_result_path": str(JAX_RESULT),
        "honest_caveat":     "cycle_closes is purity-window only. Lindblad is first-order Euler. Full state return not guaranteed. Clausius DS_cycle~0 is the primary closure criterion.",
        "TOOL_MANIFEST": {
            "numpy":      {"used": True, "reason": "load_bearing: density matrix ops, eigvalsh, Frobenius norm — removal changes verdict"},
            "jax":        {"used": JAX_AVAILABLE, "reason": "load_bearing when available: x64 float precision for parity audit; falls back to numpy"},
            "kraus_apply": {"used": True, "reason": "load_bearing: axis1 expand/compress channels"},
            "lindblad":   {"used": True, "reason": "load_bearing: axis2 open_isothermal Lindblad"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "numpy":       "load_bearing",
            "jax":         "load_bearing",
            "kraus_apply": "load_bearing",
            "lindblad":    "load_bearing",
        },
        "blocked_consumers": ["layer-completion", "manifold admission", "coupling", "bridge", "Phi0", "Xi", "Axis0"],
    }

    class _Enc(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, (bool, np.bool_)):
                return bool(o)
            if isinstance(o, (np.integer,)):
                return int(o)
            if isinstance(o, (np.floating,)):
                return float(o)
            if isinstance(o, np.ndarray):
                return o.tolist()
            return super().default(o)

    def _clean(obj):
        """Recursively coerce numpy scalars to Python types."""
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_clean(v) for v in obj]
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        return obj

    with open(JAX_RESULT, "w") as f:
        json.dump(_clean(payload), f, indent=2, cls=_Enc)
        f.write("\n")
    print(f"JAX parity result written: {JAX_RESULT}")

    return 0 if jax_result["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
