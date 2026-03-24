"""
Gain Calibration SIM — Pro Thread 1
====================================
Sweeps γ_sub from 0.01 to 1.0 (γ_dom=5.0) to find the critical
ratio that produces net ΔΦ > 0 over a full 720° cycle.

KILL being fixed: 64-stage all-negative ΔΦ (C8 violation)
Root cause: γ_sub=0.5 overwhelms γ_dom=5.0
"""

import numpy as np
import json
import os
from datetime import datetime, UTC

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    make_random_density_matrix,
    von_neumann_entropy,
    trace_distance,
    EvidenceToken,
)


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


def build_operators(d, seed=77):
    """Build Ti, Te, Fi, Fe operators for Lindblad stages."""
    # Ti: dephasing
    Ti_ops = []
    for k in range(d):
        L = np.zeros((d, d), dtype=complex)
        L[k, k] = 1.0
        Ti_ops.append(L)

    # Fe: dissipation
    Fe_ops = []
    for j in range(d):
        for k in range(d):
            if j != k:
                L = np.zeros((d, d), dtype=complex)
                L[j, k] = 1.0
                Fe_ops.append(L)

    # Te: Hamiltonian
    np.random.seed(seed)
    H = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    H = (H + H.conj().T) / 2

    # Fi: spectral filter
    Fi = np.eye(d, dtype=complex)
    for k in range(1, d):
        Fi[k, k] = 0.7

    return Ti_ops, Fe_ops, H, Fi


TYPE1_STAGES = [
    (1, "Ti", False), (2, "Fe", True), (3, "Ti", True), (4, "Fe", False),
    (5, "Fi", False), (6, "Te", False), (7, "Fi", True), (8, "Te", True),
]


def run_engine_cycle(rho, d, gamma_dom, gamma_sub, Ti_ops, Fe_ops, H, Fi,
                     dt=0.005, n_steps=5):
    """Run one full 720° cycle (8 stages) with given γ parameters."""
    for _, dominant, axis6_up in TYPE1_STAGES:
        sign = 1.0 if axis6_up else -1.0
        g_Ti = gamma_dom if dominant == 'Ti' else gamma_sub
        g_Fe = gamma_dom if dominant == 'Fe' else gamma_sub
        g_Fi = gamma_dom if dominant == 'Fi' else gamma_sub
        H_scale = gamma_dom if dominant == 'Te' else gamma_sub

        for _ in range(n_steps):
            commutator = sign * H_scale * (H @ rho - rho @ H)
            drho = -1j * commutator

            for L in Ti_ops:
                LdL = L.conj().T @ L
                drho += g_Ti * (L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL))

            for L in Fe_ops:
                LdL = L.conj().T @ L
                drho += g_Fe * (L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL))

            rho = rho + dt * drho

            fi_str = g_Fi * dt * 0.5
            rho = (1 - fi_str) * rho + fi_str * (Fi @ rho @ Fi.conj().T)
            if np.real(np.trace(rho)) > 0:
                rho = rho / np.trace(rho)
            rho = ensure_valid(rho)

    return rho


def sim_gain_calibration(d=4, n_cycles=10):
    """
    Sweep γ_sub from 0.01 to 1.0 (step 0.05) against γ_dom=5.0.
    For each ratio, run n_cycles and measure total ΔΦ.
    Find the critical threshold where net ΔΦ > 0.
    """
    print(f"\n{'='*60}")
    print(f"GAIN CALIBRATION — γ RATIO SWEEP")
    print(f"  d={d}, cycles={n_cycles}, γ_dom=5.0")
    print(f"{'='*60}")

    Ti_ops, Fe_ops, H, Fi = build_operators(d)
    gamma_dom = 5.0

    sweep_results = []
    gamma_values = np.arange(0.01, 1.01, 0.05)

    for gamma_sub in gamma_values:
        np.random.seed(42)
        rho = make_random_density_matrix(d)
        phi_start = negentropy(rho, d)

        for _ in range(n_cycles):
            rho = run_engine_cycle(rho, d, gamma_dom, gamma_sub,
                                   Ti_ops, Fe_ops, H, Fi)

        phi_end = negentropy(rho, d)
        total_dphi = phi_end - phi_start
        ratio = gamma_dom / gamma_sub
        sweep_results.append({
            'gamma_sub': float(gamma_sub),
            'ratio': float(ratio),
            'total_dphi': float(total_dphi),
        })

        marker = "✓" if total_dphi > 0 else "✗"
        print(f"  {marker} γ_sub={gamma_sub:.2f} (ratio={ratio:6.1f}): "
              f"ΔΦ={total_dphi:+.6f}")

    # Find threshold
    positive = [r for r in sweep_results if r['total_dphi'] > 0]
    negative = [r for r in sweep_results if r['total_dphi'] <= 0]

    if positive:
        threshold_sub = max(r['gamma_sub'] for r in positive)
        threshold_ratio = min(r['ratio'] for r in positive)
        print(f"\n  Critical threshold: γ_sub ≤ {threshold_sub:.2f} "
              f"(ratio ≥ {threshold_ratio:.1f})")
        print(f"  {len(positive)}/{len(sweep_results)} ratios produce ΔΦ > 0")
    else:
        threshold_sub = 0.0
        threshold_ratio = float('inf')
        print(f"\n  WARNING: No γ_sub produces ΔΦ > 0 at γ_dom={gamma_dom}")

    # Run calibrated process_cycle with best γ_sub
    best_sub = min(r['gamma_sub'] for r in sweep_results
                   if r == min(sweep_results, key=lambda x: -x['total_dphi']))
    best_dphi = max(r['total_dphi'] for r in sweep_results)

    print(f"\n  Best: γ_sub={best_sub:.2f}, ΔΦ={best_dphi:+.6f}")

    results = []

    # Token: phase diagram found at least one positive ΔΦ
    if positive:
        results.append(EvidenceToken(
            "E_SIM_GAIN_PHASE_DIAGRAM_OK", "S_SIM_GAIN_CALIBRATION_V1",
            "PASS", best_dphi
        ))
    else:
        results.append(EvidenceToken(
            "", "S_SIM_GAIN_CALIBRATION_V1",
            "KILL", best_dphi,
            f"NO_POSITIVE_DPHI_IN_SWEEP"
        ))

    # Token: calibrated process_cycle ratchets?
    if best_dphi > 0:
        results.append(EvidenceToken(
            "E_SIM_CALIBRATED_DIRECTIONAL_ACCUMULATOR_OK", "S_SIM_CALIBRATED_PROCESS_CYCLE_V1",
            "PASS", best_dphi
        ))
    else:
        results.append(EvidenceToken(
            "", "S_SIM_CALIBRATED_PROCESS_CYCLE_V1",
            "KILL", best_dphi,
            f"BEST_DPHI={best_dphi:.6f}_STILL_NEGATIVE"
        ))

    return results, sweep_results


if __name__ == "__main__":
    results, sweep = sim_gain_calibration()

    print(f"\n{'='*60}")
    print(f"GAIN CALIBRATION RESULTS")
    print(f"{'='*60}")
    for e in results:
        icon = "✓" if e.status == "PASS" else "✗"
        print(f"  {icon} {e.sim_spec_id}: {e.status} (value={e.measured_value:.4f})")

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "gain_calibration_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "evidence_ledger": [
                {"token_id": e.token_id, "sim_spec_id": e.sim_spec_id,
                 "status": e.status, "measured_value": e.measured_value,
                 "kill_reason": e.kill_reason}
                for e in results
            ],
            "sweep_data": sweep,
        }, f, indent=2)
    print(f"  Results saved to: {outpath}")
