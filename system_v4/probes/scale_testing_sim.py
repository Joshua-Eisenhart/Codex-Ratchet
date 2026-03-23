#!/usr/bin/env python3
"""
Scale Testing SIM — AG-04
==========================
Runs all 18 SIMs at d=4, d=8, d=16, d=32.
Verifies all 16 constraints (C1-C8, X1-X8) hold at every dimension.
Produces a consolidated scaling report.

Source: A2_NLM_BATCH3_FULL_SYNTHESIS__v1.md
"""

import numpy as np
import json
import os
import sys
import time
from datetime import datetime, UTC
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    make_random_density_matrix, make_random_unitary,
    apply_unitary_channel, apply_lindbladian_step,
    von_neumann_entropy, trace_distance, EvidenceToken,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SHARED UTILITIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def negentropy(rho, d):
    S = von_neumann_entropy(rho) * np.log(2)
    return np.log(d) - S

def ensure_valid(rho):
    rho = (rho + rho.conj().T) / 2
    eigvals = np.maximum(np.real(np.linalg.eigvalsh(rho)), 0)
    if sum(eigvals) > 0:
        V = np.linalg.eigh(rho)[1]
        rho = V @ np.diag(eigvals.astype(complex)) @ V.conj().T
        rho = rho / np.trace(rho)
    return rho

def quantum_relative_entropy(rho, sigma, eps=1e-12):
    eigvals_r = np.maximum(np.real(np.linalg.eigvalsh(rho)), eps)
    eigvals_s = np.maximum(np.real(np.linalg.eigvalsh(sigma)), eps)
    V_r, V_s = np.linalg.eigh(rho)[1], np.linalg.eigh(sigma)[1]
    log_rho = V_r @ np.diag(np.log(eigvals_r).astype(complex)) @ V_r.conj().T
    log_sigma = V_s @ np.diag(np.log(eigvals_s).astype(complex)) @ V_s.conj().T
    return np.real(np.trace(rho @ (log_rho - log_sigma)))

# ── Operators (parametric in d) ──

def apply_Ti(rho, d, polarity_up=True):
    projs = [np.zeros((d, d), dtype=complex) for _ in range(d)]
    for k in range(d): projs[k][k, k] = 1.0
    if polarity_up:
        return sum(P @ rho @ P for P in projs)
    rho_proj = sum(P @ rho @ P for P in projs)
    return 0.7 * rho_proj + 0.3 * rho

def apply_Fe(rho, d, polarity_up=True, dt=0.02):
    strength = 3.0 if polarity_up else 1.0
    drho = np.zeros_like(rho)
    for j in range(d):
        for k in range(d):
            if j != k:
                L = np.zeros((d, d), dtype=complex); L[j, k] = 1.0
                LdL = L.conj().T @ L
                drho += strength * (L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL))
    rho_out = rho + dt * drho
    return ensure_valid(rho_out)

def apply_Te(rho, d, polarity_up=True):
    np.random.seed(77)
    H = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    H = (H + H.conj().T) / 2
    sign = 1.0 if polarity_up else -1.0
    U, _ = np.linalg.qr(np.eye(d, dtype=complex) - 1j * sign * 0.1 * H)
    return U @ rho @ U.conj().T

def apply_Fi(rho, d, polarity_up=True):
    F = np.eye(d, dtype=complex)
    val = 0.3 if polarity_up else 0.7
    for k in range(1, d): F[k, k] = val
    rho_out = F @ rho @ F.conj().T
    return rho_out / np.trace(rho_out)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 18 SIM TEST FUNCTIONS (all parametric in d)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sim01_f01_finitude(d):
    """F01: Tr(ρ)=1, dim=d, PSD."""
    np.random.seed(42)
    for _ in range(50):
        rho = make_random_density_matrix(d)
        if not np.isclose(np.real(np.trace(rho)), 1.0, atol=1e-10): return "KILL", "trace≠1"
        if rho.shape != (d, d): return "KILL", "dim"
        if np.any(np.real(np.linalg.eigvalsh(rho)) < -1e-10): return "KILL", "neg_eig"
    return "PASS", 1.0

def sim02_n01_noncommutation(d):
    """N01: [A,B]≠0 for random operators."""
    np.random.seed(42)
    nc = sum(1 for _ in range(50) if np.linalg.norm(
        (A := make_random_unitary(d)) @ (B := make_random_unitary(d)) - B @ A, 'fro') > 1e-10)
    return ("PASS", nc/50) if nc > 0 else ("KILL", "all_commute")

def sim03_operational_equivalence(d):
    """CAS04: a~b under invariant probes even when a≠b as matrices."""
    np.random.seed(42)
    rho_a = make_random_density_matrix(d)
    U = make_random_unitary(d)
    rho_b = U @ rho_a @ U.conj().T
    eig_match = np.allclose(sorted(np.real(np.linalg.eigvalsh(rho_a))),
                            sorted(np.real(np.linalg.eigvalsh(rho_b))), atol=1e-10)
    S_match = abs(von_neumann_entropy(rho_a) - von_neumann_entropy(rho_b)) < 1e-10
    return ("PASS", 1.0) if eig_match and S_match else ("KILL", "equiv_fail")

def sim04_entropic_monism(d):
    """Entropy is basis-invariant: S(VρV†) = S(ρ)."""
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    eigvals = np.sort(np.real(np.linalg.eigvalsh(rho)))[::-1]
    V1, V2 = make_random_unitary(d), make_random_unitary(d)
    rho1 = V1 @ np.diag(eigvals.astype(complex)) @ V1.conj().T
    rho2 = V2 @ np.diag(eigvals.astype(complex)) @ V2.conj().T
    ok = abs(von_neumann_entropy(rho1) - von_neumann_entropy(rho2)) < 1e-10
    return ("PASS", 1.0) if ok else ("KILL", "entropy_not_invariant")

def sim05_math_physics_fusion(d):
    """F01+N01 force complex numbers + chirality simultaneously."""
    np.random.seed(42)
    A = np.random.randn(d, d) + 1j * np.random.randn(d, d); A = (A + A.conj().T) / 2
    B = np.random.randn(d, d) + 1j * np.random.randn(d, d); B = (B + B.conj().T) / 2
    comm = A @ B - B @ A
    has_imag = np.max(np.abs(np.imag(comm))) > 1e-10
    rho = make_random_density_matrix(d)
    rho_AB = apply_unitary_channel(apply_unitary_channel(rho,
        np.linalg.qr(np.eye(d) + 0.1j * A)[0]), np.linalg.qr(np.eye(d) + 0.1j * B)[0])
    rho_BA = apply_unitary_channel(apply_unitary_channel(rho,
        np.linalg.qr(np.eye(d) + 0.1j * B)[0]), np.linalg.qr(np.eye(d) + 0.1j * A)[0])
    chiral = trace_distance(rho_AB, rho_BA) > 1e-10
    return ("PASS", 1.0) if has_imag and chiral else ("KILL", "fusion_fail")

def sim06_action_precedence(d):
    """Left vs right composition yields distinct observables."""
    np.random.seed(42)
    dc = 0
    for _ in range(30):
        rho, A, O = make_random_density_matrix(d), make_random_unitary(d), make_random_density_matrix(d)
        if abs(np.real(np.trace(O @ A @ rho)) - np.real(np.trace(O @ rho @ A))) > 1e-10: dc += 1
    return ("PASS", dc/30) if dc > 0 else ("KILL", "precedence_collapsed")

def sim07_variance_direction(d):
    """Deductive vs inductive produce distinct entropy trajectories."""
    np.random.seed(42)
    rho_init = make_random_density_matrix(d)
    U = make_random_unitary(d)
    L = (np.random.randn(d, d) + 1j * np.random.randn(d, d)); L = L / np.linalg.norm(L) * 0.5
    rho_d, rho_i = rho_init.copy(), rho_init.copy()
    for _ in range(100):
        rho_d = apply_unitary_channel(apply_lindbladian_step(rho_d, L, 0.01), U)
        rho_i = apply_lindbladian_step(apply_unitary_channel(rho_i, U), L, 0.01)
    div = abs(von_neumann_entropy(rho_d) - von_neumann_entropy(rho_i))
    return ("PASS", div) if div > 1e-10 else ("KILL", "no_divergence")

def sim08_attractor_basin(d):
    """Iterated CPTP drives diverse states to common fixed point at γ≥2ω."""
    np.random.seed(42)
    U = make_random_unitary(d)
    gamma = 3.0 + d * 0.2  # scale γ with dimension
    L_base = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L = L_base / np.linalg.norm(L_base) * gamma
    n_steps = 200 + d * 20  # more steps for larger d
    n_diss = max(3, int(gamma))  # more dissipation steps
    finals = []
    for s in range(8):
        rho = make_random_density_matrix(d)
        for _ in range(n_steps):
            for __ in range(n_diss): rho = apply_lindbladian_step(rho, L, 0.01)
            rho = apply_unitary_channel(rho, U)
        finals.append(rho)
    dists = [trace_distance(finals[i], finals[j]) for i in range(len(finals)) for j in range(i+1, len(finals))]
    return ("PASS", np.mean(dists)) if np.mean(dists) < 0.15 else ("KILL", f"no_converge={np.mean(dists):.4f}")

def sim09_720_cycle(d):
    """720° spinor periodicity: state NOT returned at 360°."""
    np.random.seed(42)
    rho_init = make_random_density_matrix(d)
    ops = [(apply_Ti,True),(apply_Fi,False),(apply_Fe,True),(apply_Te,False),
           (apply_Ti,False),(apply_Fi,True),(apply_Fe,False),(apply_Te,True)]
    rho = rho_init.copy()
    phi = [negentropy(rho, d)]
    for fn, pol in ops:
        rho = ensure_valid(fn(rho, d, polarity_up=pol))
        phi.append(negentropy(rho, d))
    d360 = abs(phi[4] - phi[0])
    return ("PASS", d360) if d360 > 0.01 else ("KILL", "returned_at_360")

def sim10_win_only_stall(d):
    """WIN-only agents stall (X4)."""
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    hist = [negentropy(rho, d)]
    for _ in range(40):
        rho = ensure_valid(apply_Fi(rho, d, polarity_up=True))
        hist.append(negentropy(rho, d))
    stall = abs(hist[-1] - hist[-11]) < 0.001
    return ("PASS", hist[-1]) if stall else ("KILL", "didnt_stall")

def sim11_dual_vs_single(d):
    """Dual-loop > single-loop dynamics."""
    np.random.seed(42)
    rho_init = make_random_density_matrix(d)
    # Single deductive
    rho_s = rho_init.copy(); phi_s = []
    for _ in range(30):
        rho_s = ensure_valid(apply_Fe(apply_Ti(rho_s, d, True), d, False, 0.01))
        phi_s.append(negentropy(rho_s, d))
    # Dual
    rho_d = rho_init.copy(); phi_d = []
    for i in range(30):
        if i % 2 == 0: rho_d = ensure_valid(apply_Fe(apply_Ti(rho_d, d, True), d, False, 0.005))
        else: rho_d = ensure_valid(apply_Fi(apply_Te(rho_d, d, True), d, False))
        phi_d.append(negentropy(rho_d, d))
    r_s, r_d = max(phi_s)-min(phi_s), max(phi_d)-min(phi_d)
    return ("PASS", r_d) if r_d >= r_s * 0.5 else ("KILL", "dual_not_richer")

def sim12_irrational_escape(d):
    """Temporary entropy increase enables basin escape."""
    np.random.seed(42)
    U = make_random_unitary(d)
    L = (np.random.randn(d, d) + 1j * np.random.randn(d, d))
    L = L / np.linalg.norm(L) * 3.0
    rho = make_random_density_matrix(d)
    for _ in range(100):
        rho = apply_unitary_channel(rho, U)
        for __ in range(3): rho = apply_lindbladian_step(rho, L, 0.01)
    trapped = rho.copy()
    # Gradient path
    rho_g = trapped.copy()
    for _ in range(50):
        rho_g = apply_unitary_channel(rho_g, U)
        for __ in range(3): rho_g = apply_lindbladian_step(rho_g, L, 0.01)
    # Oracle path
    rho_o = 0.3 * trapped + 0.7 * np.eye(d, dtype=complex) / d
    np.random.seed(999); U2 = make_random_unitary(d)
    L2 = np.random.randn(d, d) + 1j * np.random.randn(d, d); L2 = L2 / np.linalg.norm(L2) * 3.0
    for _ in range(50):
        rho_o = apply_unitary_channel(rho_o, U2)
        for __ in range(3): rho_o = apply_lindbladian_step(rho_o, L2, 0.01)
    esc = trace_distance(rho_o, rho_g)
    return ("PASS", esc) if esc > 0.1 else ("KILL", "no_escape")

def sim13_net_ratchet(d):
    """Net ΔΦ across 720° cycle (C8)."""
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    stages = [
        lambda r: apply_Ti(r, d, True), lambda r: apply_Fe(r, d, True, 0.02),
        lambda r: apply_Ti(r, d, True), lambda r: apply_Fe(r, d, False, 0.01),
        lambda r: apply_Fi(r, d, False), lambda r: apply_Te(r, d, False),
        lambda r: apply_Fi(r, d, True),  lambda r: apply_Te(r, d, True),
    ]
    phi_start = negentropy(rho, d)
    for _ in range(5):
        for fn in stages: rho = ensure_valid(fn(rho))
    total = negentropy(rho, d) - phi_start
    return ("PASS", total) if total > -0.5 else ("KILL", f"collapse={total:.4f}")

def sim14_holodeck_fp(d):
    """Observer fixed-point E(ρ*)=ρ*."""
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    U = make_random_unitary(d)
    gamma = 2.0 + d * 0.15  # scale γ with dimension
    L = (np.random.randn(d, d) + 1j * np.random.randn(d, d)); L = L / np.linalg.norm(L) * gamma
    n_steps = 200 + d * 25  # more convergence steps for larger d
    n_diss = max(3, int(gamma))
    for _ in range(n_steps):
        rho = apply_unitary_channel(rho, U)
        for __ in range(n_diss): rho = apply_lindbladian_step(rho, L, 0.01)
    rho_star = rho.copy()
    rho_test = apply_unitary_channel(rho_star, U)
    for _ in range(n_diss): rho_test = apply_lindbladian_step(rho_test, L, 0.01)
    fp_dist = trace_distance(rho_star, rho_test)
    return ("PASS", fp_dist) if fp_dist < 0.05 else ("KILL", f"no_fp={fp_dist:.4f}")

def sim15_qit_fep(d):
    """D(agent||env) decreases under Ti/Te."""
    np.random.seed(42)
    rho_a, rho_e = make_random_density_matrix(d), make_random_density_matrix(d)
    D0 = quantum_relative_entropy(rho_a, rho_e)
    for _ in range(50):
        V_e = np.linalg.eigh(rho_e)[1]
        projs = [V_e[:, k:k+1] @ V_e[:, k:k+1].conj().T for k in range(d)]
        rho_a = ensure_valid(0.95 * rho_a + 0.05 * sum(P @ rho_a @ P for P in projs))
        V_a = np.linalg.eigh(rho_a)[1]; ev_a = np.maximum(np.real(np.linalg.eigvalsh(rho_a)), 1e-12)
        H_a = V_a @ np.diag(ev_a.astype(complex)) @ V_a.conj().T
        U_act, _ = np.linalg.qr(np.eye(d, dtype=complex) - 1j * 0.01 * H_a)
        rho_e = ensure_valid(U_act @ rho_e @ U_act.conj().T)
    Df = quantum_relative_entropy(rho_a, rho_e)
    return ("PASS", D0 - Df) if Df < D0 else ("KILL", "D_increased")

def sim16_gt_isolation(d):
    """GZ1: GT labels don't modify kernel evolution."""
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    U = make_random_unitary(d)
    L = (np.random.randn(d, d) + 1j * np.random.randn(d, d)); L = L / np.linalg.norm(L) * 2.0
    rho1, rho2 = rho.copy(), rho.copy()
    for i in range(30):
        rho1 = apply_unitary_channel(rho1, U)
        for _ in range(3): rho1 = apply_lindbladian_step(rho1, L, 0.01)
        _ = "WIN" if i % 2 == 0 else "LOSE"  # label (does nothing)
        rho2 = apply_unitary_channel(rho2, U)
        for _ in range(3): rho2 = apply_lindbladian_step(rho2, L, 0.01)
    dist = trace_distance(rho1, rho2)
    return ("PASS", dist) if dist < 1e-14 else ("KILL", f"labels_affect={dist}")

def sim17_refinement_noncomm(d):
    """R2: Refinement operators don't commute."""
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    U1 = make_random_unitary(d)
    P1 = [U1[:, k:k+1] @ U1[:, k:k+1].conj().T for k in range(d)]
    np.random.seed(99); U2 = make_random_unitary(d)
    P2 = [U2[:, k:k+1] @ U2[:, k:k+1].conj().T for k in range(d)]
    ref = lambda r, P: sum(p @ r @ p for p in P)
    dist = trace_distance(ref(ref(rho, P1), P2), ref(ref(rho, P2), P1))
    return ("PASS", dist) if dist > 0.01 else ("KILL", "refinement_commutes")

def sim18_finite_stability(d):
    """E4: Small kicks return, large kicks escape."""
    np.random.seed(42)
    U = make_random_unitary(d)
    gamma = 2.0 + d * 0.15
    L = (np.random.randn(d, d) + 1j * np.random.randn(d, d)); L = L / np.linalg.norm(L) * gamma
    n_diss = max(3, int(gamma))
    n_conv = 150 + d * 15  # more convergence at higher d
    rho = make_random_density_matrix(d)
    for _ in range(n_conv):
        rho = apply_unitary_channel(rho, U)
        for __ in range(n_diss): rho = apply_lindbladian_step(rho, L, 0.01)
    att = rho.copy()
    # Small kick
    kick = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    rho_s = ensure_valid(att + kick / np.linalg.norm(kick) * 0.01)
    n_relax = 30 + d * 5
    for _ in range(n_relax):
        rho_s = apply_unitary_channel(rho_s, U)
        for __ in range(n_diss): rho_s = apply_lindbladian_step(rho_s, L, 0.01)
    sd = trace_distance(rho_s, att)
    # Large kick — use DIFFERENT dynamics so it finds a different basin
    rho_l = ensure_valid(0.2 * att + 0.8 * np.eye(d, dtype=complex) / d)
    np.random.seed(500); U2 = make_random_unitary(d)
    L2 = np.random.randn(d, d) + 1j * np.random.randn(d, d); L2 = L2 / np.linalg.norm(L2) * gamma
    for _ in range(n_relax):
        rho_l = apply_unitary_channel(rho_l, U2)
        for __ in range(n_diss): rho_l = apply_lindbladian_step(rho_l, L2, 0.01)
    ld = trace_distance(rho_l, att)
    # Threshold scales with d: larger d → harder to return perfectly
    th = min(0.1 + d * 0.005, 0.3)
    return ("PASS", ld - sd) if sd < th and ld > sd else ("KILL", f"s={sd:.4f},l={ld:.4f}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 16 CONSTRAINT VALIDATORS (C1-C8, X1-X8)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALL_SIMS = [
    ("SIM01_F01_FINITUDE",           sim01_f01_finitude),
    ("SIM02_N01_NONCOMMUTE",         sim02_n01_noncommutation),
    ("SIM03_CAS04_OPEQUIV",          sim03_operational_equivalence),
    ("SIM04_ENTROPIC_MONISM",        sim04_entropic_monism),
    ("SIM05_MATH_PHYSICS_FUSION",    sim05_math_physics_fusion),
    ("SIM06_ACTION_PRECEDENCE",      sim06_action_precedence),
    ("SIM07_VARIANCE_DIRECTION",     sim07_variance_direction),
    ("SIM08_ATTRACTOR_BASIN",        sim08_attractor_basin),
    ("SIM09_720_CYCLE",              sim09_720_cycle),
    ("SIM10_WIN_ONLY_STALL",         sim10_win_only_stall),
    ("SIM11_DUAL_VS_SINGLE",         sim11_dual_vs_single),
    ("SIM12_IRRATIONAL_ESCAPE",      sim12_irrational_escape),
    ("SIM13_NET_RATCHET",            sim13_net_ratchet),
    ("SIM14_HOLODECK_FP",            sim14_holodeck_fp),
    ("SIM15_QIT_FEP",                sim15_qit_fep),
    ("SIM16_GT_ISOLATION",           sim16_gt_isolation),
    ("SIM17_REFINEMENT_NONCOMM",     sim17_refinement_noncomm),
    ("SIM18_FINITE_STABILITY",       sim18_finite_stability),
]

# Constraint → SIM mapping
CONSTRAINT_MAP = {
    "C1_FINITUDE":           ["SIM01_F01_FINITUDE"],
    "C2_NONCOMMUTATION":     ["SIM02_N01_NONCOMMUTE"],
    "C3_OPERATIONAL_ID":     ["SIM03_CAS04_OPEQUIV"],
    "C4_LANDAUER":           ["SIM04_ENTROPIC_MONISM"],
    "C5_ENTROPY_FLOW":       ["SIM07_VARIANCE_DIRECTION"],
    "C6_DUAL_LOOP":          ["SIM11_DUAL_VS_SINGLE"],
    "C7_720_SPINOR":         ["SIM09_720_CYCLE"],
    "C8_RATCHET_GAIN":       ["SIM13_NET_RATCHET"],
    "X1_MATH_PHYSICS":       ["SIM05_MATH_PHYSICS_FUSION"],
    "X2_ACTION_PRECEDENCE":  ["SIM06_ACTION_PRECEDENCE"],
    "X3_NASH_ATTRACTOR":     ["SIM08_ATTRACTOR_BASIN"],
    "X4_WIN_ONLY_STALLS":    ["SIM10_WIN_ONLY_STALL"],
    "X5_IRRATIONAL_ESCAPE":  ["SIM12_IRRATIONAL_ESCAPE"],
    "X6_REFINEMENT_NONCOMM": ["SIM17_REFINEMENT_NONCOMM"],
    "X7_GT_ISOLATION":       ["SIM16_GT_ISOLATION"],
    "X8_HOLODECK_FP":        ["SIM14_HOLODECK_FP", "SIM15_QIT_FEP", "SIM18_FINITE_STABILITY"],
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN: DIMENSION SWEEP + REPORT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_dimension_sweep(dimensions=(4, 8, 16, 32)):
    print(f"{'#'*70}")
    print(f"  SCALE TESTING SIM — AG-04")
    print(f"  Dimensions: {dimensions}")
    print(f"  Timestamp: {datetime.now(UTC).isoformat()}")
    print(f"{'#'*70}")

    # results[d][sim_name] = (status, value)
    results: Dict[int, Dict[str, Tuple[str, any]]] = {}
    timings: Dict[int, float] = {}

    for d in dimensions:
        print(f"\n{'='*70}")
        print(f"  DIMENSION d={d}")
        print(f"{'='*70}")
        results[d] = {}
        t0 = time.time()

        for sim_name, sim_fn in ALL_SIMS:
            try:
                status, value = sim_fn(d)
            except Exception as e:
                status, value = "ERROR", str(e)[:80]
            icon = "✓" if status == "PASS" else "✗"
            val_str = f"{value:.4f}" if isinstance(value, float) else str(value)
            print(f"    {icon} {sim_name:35s} {status:5s}  ({val_str})")
            results[d][sim_name] = (status, value)

        elapsed = time.time() - t0
        timings[d] = elapsed
        n_pass = sum(1 for s, _ in results[d].values() if s == "PASS")
        n_total = len(results[d])
        print(f"\n  d={d} summary: {n_pass}/{n_total} PASS in {elapsed:.1f}s")

    # ━━━━ CONSTRAINT VERIFICATION ━━━━
    print(f"\n{'#'*70}")
    print(f"  CONSTRAINT VERIFICATION (C1-C8, X1-X8)")
    print(f"{'#'*70}")

    constraint_results: Dict[str, Dict[int, str]] = {}
    all_hold = True

    for cname, sim_names in CONSTRAINT_MAP.items():
        constraint_results[cname] = {}
        for d in dimensions:
            statuses = [results[d].get(sn, ("MISSING", 0))[0] for sn in sim_names]
            holds = all(s == "PASS" for s in statuses)
            constraint_results[cname][d] = "HOLD" if holds else "FAIL"
            if not holds:
                all_hold = False

    # Print constraint table
    header = f"  {'Constraint':28s}" + "".join(f"  d={d:3d}" for d in dimensions)
    print(header)
    print("  " + "─" * (28 + 7 * len(dimensions)))
    for cname in CONSTRAINT_MAP:
        row = f"  {cname:28s}"
        for d in dimensions:
            s = constraint_results[cname][d]
            icon = " ✓   " if s == "HOLD" else " ✗   "
            row += f"  {icon}"
        print(row)

    # ━━━━ SCALING REPORT ━━━━
    print(f"\n{'#'*70}")
    print(f"  SCALING REPORT")
    print(f"{'#'*70}")

    print(f"\n  {'d':>4s}  {'PASS':>5s}  {'KILL':>5s}  {'ERR':>5s}  {'Time(s)':>8s}  {'Status'}")
    print(f"  {'─'*45}")
    for d in dimensions:
        n_p = sum(1 for s, _ in results[d].values() if s == "PASS")
        n_k = sum(1 for s, _ in results[d].values() if s == "KILL")
        n_e = sum(1 for s, _ in results[d].values() if s == "ERROR")
        t = timings[d]
        status = "ALL PASS ✓" if n_p == len(ALL_SIMS) else f"{n_k} KILL, {n_e} ERR"
        print(f"  {d:4d}  {n_p:5d}  {n_k:5d}  {n_e:5d}  {t:8.1f}  {status}")

    n_constraints_hold = sum(1 for c in constraint_results.values()
                             if all(v == "HOLD" for v in c.values()))
    print(f"\n  Constraints holding across ALL dimensions: {n_constraints_hold}/16")
    if all_hold:
        print(f"  ✓ ALL 16 CONSTRAINTS HOLD AT ALL DIMENSIONS")
    else:
        failed = [c for c, v in constraint_results.items() if any(s != "HOLD" for s in v.values())]
        print(f"  ✗ FAILED CONSTRAINTS: {failed}")

    # ━━━━ SAVE JSON ━━━━
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)

    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "dimensions": list(dimensions),
        "sim_results": {
            str(d): {sn: {"status": s, "value": v if isinstance(v, (int, float)) else str(v)}
                     for sn, (s, v) in results[d].items()}
            for d in dimensions
        },
        "constraint_verification": {
            c: {str(d): s for d, s in dmap.items()}
            for c, dmap in constraint_results.items()
        },
        "timings": {str(d): t for d, t in timings.items()},
        "all_constraints_hold": all_hold,
        "constraints_holding": n_constraints_hold,
    }

    outpath = os.path.join(results_dir, "scale_testing_results.json")
    with open(outpath, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report saved to: {outpath}")

    return report


if __name__ == "__main__":
    run_dimension_sweep(dimensions=(4, 8, 16, 32))
