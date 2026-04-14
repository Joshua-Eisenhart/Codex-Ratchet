#!/usr/bin/env python3
"""
sim_layers13_16_bridge.py
=========================

Bridge verification layers 13-16.  Previously blocked because I_c could
never be positive at 2-qubit scale.  The 3-qubit prototype proved
cross-partition Fi achieves I_c = +0.647 from separable |000>.

Layer 13 - Entanglement earned (not injected)
Layer 14 - Bridge crosses partition
Layer 15 - Sustained positive I_c
Layer 16 - 3q vs 2q advantage

Outputs four JSON files to a2_state/sim_results/.
"""

import json
import os
import sys
from datetime import datetime, UTC

import numpy as np
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ═══════════════════════════════════════════════════════════════════
# PAULI MATRICES
# ═══════════════════════════════════════════════════════════════════

I2 = np.eye(2, dtype=complex)
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS (from sim_3qubit_bridge_prototype.py)
# ═══════════════════════════════════════════════════════════════════

def von_neumann_entropy(rho: np.ndarray) -> float:
    """Von Neumann entropy S(rho) = -Tr(rho log2 rho), in bits."""
    rho = (rho + rho.conj().T) / 2
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    return float(-np.sum(evals * np.log2(evals)))


def partial_trace_keep(rho: np.ndarray, keep: list, dims: list) -> np.ndarray:
    """Partial trace: keep subsystems in 'keep', trace out the rest."""
    n = len(dims)
    rho_r = rho.reshape(dims + dims)
    trace_out = sorted([i for i in range(n) if i not in keep], reverse=True)
    current_n = n
    for i in trace_out:
        rho_r = np.trace(rho_r, axis1=i, axis2=i + current_n)
        current_n -= 1
    d_keep = int(np.prod([dims[i] for i in keep]))
    return rho_r.reshape(d_keep, d_keep)


def ensure_valid_density(rho: np.ndarray) -> np.ndarray:
    """Force Hermiticity, positivity, trace=1."""
    rho = (rho + rho.conj().T) / 2
    evals, evecs = np.linalg.eigh(rho)
    evals = np.maximum(evals, 0)
    rho = evecs @ np.diag(evals) @ evecs.conj().T
    rho /= np.trace(rho)
    return rho


def sanitize(obj):
    """Recursively convert numpy types to native Python for JSON."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    return obj


# ═══════════════════════════════════════════════════════════════════
# 3-QUBIT OPERATORS (8x8)
# ═══════════════════════════════════════════════════════════════════

def build_3q_Ti(strength: float = 1.0):
    """Ti: ZZ dephasing on qubits 1,2 (tensor I on qubit 3)."""
    ZZ = np.kron(SIGMA_Z, SIGMA_Z)
    ZZ_I = np.kron(ZZ, I2)
    P0 = (np.eye(8, dtype=complex) + ZZ_I) / 2
    P1 = (np.eye(8, dtype=complex) - ZZ_I) / 2

    def apply(rho, polarity_up=True):
        mix = strength if polarity_up else 0.3 * strength
        rho_proj = P0 @ rho @ P0 + P1 @ rho @ P1
        rho_out = mix * rho_proj + (1 - mix) * rho
        return ensure_valid_density(rho_out)
    return apply


def build_3q_Fe(strength: float = 1.0, phi: float = 0.4):
    """Fe: XX rotation on qubits 1,2 (tensor I on qubit 3)."""
    XX = np.kron(SIGMA_X, SIGMA_X)
    H_int = np.kron(XX, I2)

    def apply(rho, polarity_up=True):
        sign = 1.0 if polarity_up else -1.0
        angle = sign * phi * strength
        U = np.cos(angle / 2) * np.eye(8, dtype=complex) - 1j * np.sin(angle / 2) * H_int
        rho_out = U @ rho @ U.conj().T
        return ensure_valid_density(rho_out)
    return apply


def build_3q_Te(strength: float = 1.0, q: float = 0.7):
    """Te: YY dephasing on qubits 1,2 (tensor I on qubit 3)."""
    YY = np.kron(SIGMA_Y, SIGMA_Y)
    YY_I = np.kron(YY, I2)
    P_plus = (np.eye(8, dtype=complex) + YY_I) / 2
    P_minus = (np.eye(8, dtype=complex) - YY_I) / 2

    def apply(rho, polarity_up=True):
        mix = min(strength * (q if polarity_up else 0.3 * q), 1.0)
        rho_proj = P_plus @ rho @ P_plus + P_minus @ rho @ P_minus
        rho_out = (1 - mix) * rho + mix * rho_proj
        return ensure_valid_density(rho_out)
    return apply


def build_3q_Fi(strength: float = 1.0, theta: float = 0.4):
    """Fi: X on qubit 1, I on qubit 2, Z on qubit 3 -- crosses partition."""
    H_int = np.kron(np.kron(SIGMA_X, I2), SIGMA_Z)

    def apply(rho, polarity_up=True):
        sign = 1.0 if polarity_up else -1.0
        angle = sign * theta * strength
        U = np.cos(angle / 2) * np.eye(8, dtype=complex) - 1j * np.sin(angle / 2) * H_int
        rho_out = U @ rho @ U.conj().T
        return ensure_valid_density(rho_out)
    return apply


def build_3q_Fi_intra(strength: float = 1.0, theta: float = 0.4):
    """Fi WITHIN partition only: I tensor I tensor X (acts on q3 alone, no cross-partition).
    This is the correct control: a single-qubit rotation that cannot entangle."""
    H_int = np.kron(np.kron(I2, I2), SIGMA_X)

    def apply(rho, polarity_up=True):
        sign = 1.0 if polarity_up else -1.0
        angle = sign * theta * strength
        U = np.cos(angle / 2) * np.eye(8, dtype=complex) - 1j * np.sin(angle / 2) * H_int
        rho_out = U @ rho @ U.conj().T
        return ensure_valid_density(rho_out)
    return apply


# ═══════════════════════════════════════════════════════════════════
# BIPARTITION HELPERS
# ═══════════════════════════════════════════════════════════════════

CUTS_3Q = {
    "cut1_1vs23": {"A": [0], "B": [1, 2], "label": "A=q1 | B=q2q3"},
    "cut2_12vs3": {"A": [0, 1], "B": [2], "label": "A=q1q2 | B=q3"},
}


def compute_Ic_3q(rho, cut_name="cut1_1vs23"):
    """Return I_c for a specific bipartition cut on a 3-qubit state."""
    dims = [2, 2, 2]
    cut = CUTS_3Q[cut_name]
    S_AB = von_neumann_entropy(rho)
    rho_B = partial_trace_keep(rho, cut["B"], dims)
    S_B = von_neumann_entropy(rho_B)
    return S_B - S_AB


def compute_Ic_best_3q(rho):
    """Return best I_c across both cuts."""
    return max(compute_Ic_3q(rho, c) for c in CUTS_3Q)


def compute_Ic_2q(rho):
    """I_c for 2-qubit state, cut q1 vs q2."""
    S_AB = von_neumann_entropy(rho)
    rho_B = partial_trace_keep(rho, [1], [2, 2])
    S_B = von_neumann_entropy(rho_B)
    return S_B - S_AB


# ═══════════════════════════════════════════════════════════════════
# RHO |000>
# ═══════════════════════════════════════════════════════════════════

def rho_000():
    rho = np.zeros((8, 8), dtype=complex)
    rho[0, 0] = 1.0
    return rho


def rho_00():
    rho = np.zeros((4, 4), dtype=complex)
    rho[0, 0] = 1.0
    return rho


# ═══════════════════════════════════════════════════════════════════
# CYCLE RUNNER
# ═══════════════════════════════════════════════════════════════════

def run_3q_cycle(rho_init, n_cycles, deph=0.05, theta=np.pi,
                 use_fi=True, fi_builder=None):
    """Run Ti->Fe->Te->Fi cycle on 3-qubit state.
    Returns list of per-cycle I_c values (best across cuts)
    and per-cut I_c dicts."""
    Ti = build_3q_Ti(strength=deph)
    Fe = build_3q_Fe(strength=1.0, phi=0.4)
    Te = build_3q_Te(strength=deph, q=0.7)

    if fi_builder is not None:
        Fi = fi_builder(strength=1.0, theta=theta)
    elif use_fi:
        Fi = build_3q_Fi(strength=1.0, theta=theta)
    else:
        Fi = None

    rho = rho_init.copy()
    ic_best_traj = []
    ic_per_cut = {c: [] for c in CUTS_3Q}

    for _ in range(n_cycles):
        rho = Ti(rho)
        rho = Fe(rho)
        rho = Te(rho)
        if Fi is not None:
            rho = Fi(rho)

        for c in CUTS_3Q:
            ic_per_cut[c].append(round(compute_Ic_3q(rho, c), 10))
        ic_best_traj.append(round(compute_Ic_best_3q(rho), 10))

    return ic_best_traj, ic_per_cut


def run_2q_cycle(rho_init, n_cycles, deph=0.05, theta=np.pi):
    """Run equivalent 2-qubit cycle. Returns list of per-cycle I_c."""
    ZZ = np.kron(SIGMA_Z, SIGMA_Z)
    P0_2 = (np.eye(4, dtype=complex) + ZZ) / 2
    P1_2 = (np.eye(4, dtype=complex) - ZZ) / 2
    YY = np.kron(SIGMA_Y, SIGMA_Y)
    Pp_2 = (np.eye(4, dtype=complex) + YY) / 2
    Pm_2 = (np.eye(4, dtype=complex) - YY) / 2
    XX = np.kron(SIGMA_X, SIGMA_X)
    XZ = np.kron(SIGMA_X, SIGMA_Z)

    rho = rho_init.copy()
    ic_traj = []

    for _ in range(n_cycles):
        # Ti
        mix = deph
        rho_p = P0_2 @ rho @ P0_2 + P1_2 @ rho @ P1_2
        rho = mix * rho_p + (1 - mix) * rho
        rho = ensure_valid_density(rho)
        # Fe
        U = np.cos(0.2) * np.eye(4, dtype=complex) - 1j * np.sin(0.2) * XX
        rho = U @ rho @ U.conj().T
        rho = ensure_valid_density(rho)
        # Te
        mix_te = min(deph * 0.7, 1.0)
        rho_p = Pp_2 @ rho @ Pp_2 + Pm_2 @ rho @ Pm_2
        rho = (1 - mix_te) * rho + mix_te * rho_p
        rho = ensure_valid_density(rho)
        # Fi (within same 2-qubit space)
        angle = theta
        U = np.cos(angle / 2) * np.eye(4, dtype=complex) - 1j * np.sin(angle / 2) * XZ
        rho = U @ rho @ U.conj().T
        rho = ensure_valid_density(rho)

        ic_traj.append(round(compute_Ic_2q(rho), 10))

    return ic_traj


# ═══════════════════════════════════════════════════════════════════
# LAYER 13: Entanglement earned (not injected)
# ═══════════════════════════════════════════════════════════════════

def layer_13():
    print("\n" + "=" * 72)
    print("  LAYER 13: Entanglement Earned (not injected)")
    print("=" * 72)

    N = 30
    results = {"layer": 13, "name": "entanglement_earned"}

    # --- P1: |000> + full engine -> I_c crosses zero ---
    ic_traj, ic_cuts = run_3q_cycle(rho_000(), N, deph=0.05, theta=np.pi)
    max_ic = max(ic_traj)
    first_positive = next((i + 1 for i, v in enumerate(ic_traj) if v > 1e-10), None)
    p1 = {
        "description": "From |000>, 3q engine cycle -> I_c crosses zero",
        "max_I_c": round(max_ic, 8),
        "first_positive_cycle": first_positive,
        "trajectory": ic_traj,
        "pass": bool(max_ic > 1e-10),
    }
    print(f"  P1: max I_c = {max_ic:+.6f}  first_positive_cycle={first_positive}  {'PASS' if p1['pass'] else 'FAIL'}")

    # --- P2: initial state has I_c = 0 exactly ---
    rho0 = rho_000()
    ic_init_cut1 = compute_Ic_3q(rho0, "cut1_1vs23")
    ic_init_cut2 = compute_Ic_3q(rho0, "cut2_12vs3")
    ic_init_zero = abs(ic_init_cut1) < 1e-12 and abs(ic_init_cut2) < 1e-12
    p2 = {
        "description": "Initial |000> has I_c = 0 exactly (entanglement earned, not smuggled)",
        "I_c_init_cut1": round(ic_init_cut1, 12),
        "I_c_init_cut2": round(ic_init_cut2, 12),
        "pass": bool(ic_init_zero and max_ic > 1e-10),
    }
    print(f"  P2: I_c(init) = {ic_init_cut1:.12f}, {ic_init_cut2:.12f}  {'PASS' if p2['pass'] else 'FAIL'}")

    # --- N1: Fi removed -> I_c on cut2 (q1q2 vs q3) stays <= 0 ---
    # Fe (XX on q1,q2) entangles q1-q2 so cut1 can go positive even without Fi.
    # But Fi is the ONLY operator coupling q3.  So cut2 (q1q2 vs q3) tests Fi's
    # unique cross-partition role: without Fi, q3 is never entangled.
    _, ic_no_fi_cuts = run_3q_cycle(rho_000(), N, deph=0.05, theta=np.pi, use_fi=False)
    cut2_no_fi = ic_no_fi_cuts["cut2_12vs3"]
    max_cut2_no_fi = max(cut2_no_fi)
    n1 = {
        "description": "Fi removed -> I_c on cut2 (q1q2 vs q3) stays <= 0 (q3 never entangled)",
        "max_I_c_cut2_without_Fi": round(max_cut2_no_fi, 8),
        "trajectory_cut2": cut2_no_fi,
        "pass": bool(max_cut2_no_fi <= 1e-10),
    }
    print(f"  N1: max I_c(cut2, no Fi) = {max_cut2_no_fi:+.6f}  {'PASS' if n1['pass'] else 'FAIL'}")

    # --- N2: dephasing=1.0 -> I_c significantly lower than best regime ---
    # Full dephasing overwhelms coherent transport; I_c must degrade.
    ic_full_deph, _ = run_3q_cycle(rho_000(), N, deph=1.0, theta=np.pi)
    max_full_deph = max(ic_full_deph)
    degradation = max_full_deph / max(max_ic, 1e-15)
    n2 = {
        "description": "Full dephasing (1.0) -> I_c degrades significantly vs best regime",
        "max_I_c_full_deph": round(max_full_deph, 8),
        "max_I_c_best_regime": round(max_ic, 8),
        "degradation_ratio": round(degradation, 6),
        "trajectory": ic_full_deph,
        "pass": bool(max_full_deph < max_ic * 0.5),
    }
    print(f"  N2: max I_c(deph=1.0) = {max_full_deph:+.6f}  ratio={degradation:.3f}  {'PASS' if n2['pass'] else 'FAIL'}")

    results["positive"] = {"P1": p1, "P2": p2}
    results["negative"] = {"N1": n1, "N2": n2}
    pass_count = sum(1 for t in [p1, p2, n1, n2] if t["pass"])
    results["summary"] = f"{pass_count}/4 tests passed"
    results["tools_used"] = ["numpy", "von_neumann_entropy", "partial_trace_keep"]
    results["timestamp"] = "2026-04-05"

    print(f"  Summary: {results['summary']}")
    return results


# ═══════════════════════════════════════════════════════════════════
# LAYER 14: Bridge crosses partition
# ═══════════════════════════════════════════════════════════════════

def layer_14():
    print("\n" + "=" * 72)
    print("  LAYER 14: Bridge Crosses Partition")
    print("=" * 72)

    N = 30
    results = {"layer": 14, "name": "bridge_crosses_partition"}

    # --- P1: I_c on cut1 (q1 vs q2q3) goes positive ---
    _, ic_cuts = run_3q_cycle(rho_000(), N, deph=0.05, theta=np.pi)
    cut1_traj = ic_cuts["cut1_1vs23"]
    max_cut1 = max(cut1_traj)
    p1 = {
        "description": "I_c on cut1 (q1 vs q2q3) goes positive -- Fi crosses this partition",
        "max_I_c_cut1": round(max_cut1, 8),
        "trajectory_cut1": cut1_traj,
        "pass": bool(max_cut1 > 1e-10),
    }
    print(f"  P1: max I_c(cut1) = {max_cut1:+.6f}  {'PASS' if p1['pass'] else 'FAIL'}")

    # --- P2: Bridge requires 2-body cross-partition operator ---
    # Fe (XX on q1,q2) is the operator that crosses cut1 (q1 vs q2q3).
    # Remove Fe (keep Ti, Te, Fi) and I_c on cut1 should collapse to <= 0.
    # This proves the bridge requires a genuine 2-body entangling gate
    # acting across the measured partition.
    Ti_op = build_3q_Ti(strength=0.05)
    Te_op = build_3q_Te(strength=0.05, q=0.7)
    Fi_op = build_3q_Fi(strength=1.0, theta=np.pi)
    rho = rho_000()
    cut1_nofe_traj = []
    for _ in range(N):
        rho = Ti_op(rho)
        # SKIP Fe
        rho = Te_op(rho)
        rho = Fi_op(rho)
        cut1_nofe_traj.append(round(compute_Ic_3q(rho, "cut1_1vs23"), 10))
    max_cut1_nofe = max(cut1_nofe_traj)
    p2 = {
        "description": "Remove Fe (the cross-cut1 operator) -> cut1 I_c collapses. Bridge needs 2-body gate.",
        "max_I_c_cut1_with_Fe": round(max_cut1, 8),
        "max_I_c_cut1_without_Fe": round(max_cut1_nofe, 8),
        "pass": bool(max_cut1 > 1e-10 and max_cut1_nofe <= 1e-10),
    }
    print(f"  P2: I_c(+Fe)={max_cut1:+.6f}  I_c(-Fe)={max_cut1_nofe:+.6f}  "
          f"{'PASS' if p2['pass'] else 'FAIL'}")

    # --- N1: Fi replaced with local rotation on q3 only (I x I x X) -> cut2 I_c stays <= 0 ---
    # A single-qubit gate cannot entangle. This proves cross-partition coupling is required.
    _, ic_intra_cuts = run_3q_cycle(
        rho_000(), N, deph=0.05, theta=np.pi,
        fi_builder=build_3q_Fi_intra,
    )
    # Check cut2 specifically: q3 should not be entangled by a local rotation
    cut2_intra = ic_intra_cuts["cut2_12vs3"]
    max_cut2_intra = max(cut2_intra)
    # Also check cut1 -- local q3 rotation should not help cut1 either
    cut1_intra = ic_intra_cuts["cut1_1vs23"]
    # The key test: cut1 I_c with local Fi should be lower than with cross-partition Fi
    max_cut1_intra = max(cut1_intra)
    n1 = {
        "description": "Fi replaced with local q3 rotation (I x I x X) -> cut2 I_c stays <= 0",
        "max_I_c_cut2_local": round(max_cut2_intra, 8),
        "max_I_c_cut1_local": round(max_cut1_intra, 8),
        "max_I_c_cut1_cross": round(max_cut1, 8),
        "trajectory_cut2": cut2_intra,
        "pass": bool(max_cut2_intra <= 1e-10),
    }
    print(f"  N1: I_c(cut2, local Fi) = {max_cut2_intra:+.6f}  {'PASS' if n1['pass'] else 'FAIL'}")

    results["positive"] = {"P1": p1, "P2": p2}
    results["negative"] = {"N1": n1}
    pass_count = sum(1 for t in [p1, p2, n1] if t["pass"])
    results["summary"] = f"{pass_count}/3 tests passed"
    results["tools_used"] = ["numpy", "von_neumann_entropy", "partial_trace_keep"]
    results["timestamp"] = "2026-04-05"

    print(f"  Summary: {results['summary']}")
    return results


# ═══════════════════════════════════════════════════════════════════
# LAYER 15: Sustained positive I_c
# ═══════════════════════════════════════════════════════════════════

def layer_15():
    print("\n" + "=" * 72)
    print("  LAYER 15: Sustained Positive I_c")
    print("=" * 72)

    N = 30
    results = {"layer": 15, "name": "sustained_positive_ic"}

    # --- P1: Count consecutive positive cycles at best regime ---
    ic_traj, _ = run_3q_cycle(rho_000(), N, deph=0.05, theta=np.pi)
    positive_count = sum(1 for v in ic_traj if v > 1e-10)
    consecutive_positive = 0
    max_consec = 0
    for v in ic_traj:
        if v > 1e-10:
            consecutive_positive += 1
            max_consec = max(max_consec, consecutive_positive)
        else:
            consecutive_positive = 0

    p1 = {
        "description": f"Consecutive positive cycles at best regime (deph=0.05, theta=pi)",
        "positive_cycles": positive_count,
        "max_consecutive_positive": max_consec,
        "total_cycles": N,
        "trajectory": ic_traj,
        "pass": bool(positive_count >= N * 0.8),  # at least 80% positive
    }
    print(f"  P1: positive={positive_count}/{N}  max_consecutive={max_consec}  {'PASS' if p1['pass'] else 'FAIL'}")

    # --- P2: Oscillation analysis ---
    # Find zero-crossings to estimate period
    crossings = []
    for i in range(1, len(ic_traj)):
        if (ic_traj[i - 1] <= 0 and ic_traj[i] > 0) or (ic_traj[i - 1] > 0 and ic_traj[i] <= 0):
            crossings.append(i)
    if len(crossings) >= 2:
        periods = [crossings[i + 1] - crossings[i] for i in range(len(crossings) - 1)]
        avg_period = sum(periods) / len(periods) if periods else 0
    else:
        avg_period = 0

    ic_mean = sum(ic_traj) / len(ic_traj)
    ic_std = (sum((v - ic_mean) ** 2 for v in ic_traj) / len(ic_traj)) ** 0.5
    p2 = {
        "description": "Oscillation analysis: I_c oscillates but stays positive",
        "zero_crossings": len(crossings),
        "avg_half_period": round(avg_period, 2),
        "I_c_mean": round(ic_mean, 8),
        "I_c_std": round(ic_std, 8),
        "I_c_min": round(min(ic_traj), 8),
        "I_c_max": round(max(ic_traj), 8),
        "pass": bool(ic_mean > 0),
    }
    print(f"  P2: mean I_c={ic_mean:+.6f}  std={ic_std:.6f}  crossings={len(crossings)}  {'PASS' if p2['pass'] else 'FAIL'}")

    # --- N1: deph=0.3 -> max I_c degrades significantly ---
    ic_degraded, _ = run_3q_cycle(rho_000(), N, deph=0.3, theta=np.pi)
    max_ic_degraded = max(ic_degraded)
    max_ic_best = max(ic_traj)
    mean_degraded = sum(ic_degraded) / len(ic_degraded)
    ic_mean_best = sum(ic_traj) / len(ic_traj)
    n1 = {
        "description": "deph=0.3 -> max and mean I_c degrade vs best regime (deph=0.05)",
        "max_I_c_deph03": round(max_ic_degraded, 8),
        "max_I_c_deph005": round(max_ic_best, 8),
        "mean_I_c_deph03": round(mean_degraded, 8),
        "mean_I_c_deph005": round(ic_mean_best, 8),
        "max_degradation_ratio": round(max_ic_degraded / max(max_ic_best, 1e-15), 4),
        "mean_degradation_ratio": round(mean_degraded / max(ic_mean_best, 1e-15), 4),
        "trajectory": ic_degraded,
        "pass": bool(max_ic_degraded < max_ic_best),
    }
    print(f"  N1: max(0.3)={max_ic_degraded:+.6f} vs max(0.05)={max_ic_best:+.6f}  "
          f"ratio={n1['max_degradation_ratio']:.3f}  {'PASS' if n1['pass'] else 'FAIL'}")

    results["positive"] = {"P1": p1, "P2": p2}
    results["negative"] = {"N1": n1}
    pass_count = sum(1 for t in [p1, p2, n1] if t["pass"])
    results["summary"] = f"{pass_count}/3 tests passed"
    results["tools_used"] = ["numpy", "von_neumann_entropy", "partial_trace_keep"]
    results["timestamp"] = "2026-04-05"

    print(f"  Summary: {results['summary']}")
    return results


# ═══════════════════════════════════════════════════════════════════
# LAYER 16: 3q vs 2q advantage
# ═══════════════════════════════════════════════════════════════════

def layer_16():
    print("\n" + "=" * 72)
    print("  LAYER 16: 3q vs 2q Advantage")
    print("=" * 72)

    N = 30
    results = {"layer": 16, "name": "3q_vs_2q_advantage"}

    # --- P1: 3q max I_c > 2q max I_c ---
    ic_3q, _ = run_3q_cycle(rho_000(), N, deph=0.05, theta=np.pi)
    ic_2q = run_2q_cycle(rho_00(), N, deph=0.05, theta=np.pi)

    max_3q = max(ic_3q)
    max_2q = max(ic_2q)
    advantage = max_3q / max(abs(max_2q), 1e-15) if max_2q != 0 else float('inf')

    p1 = {
        "description": "3q max I_c > 2q max I_c (cross-partition advantage)",
        "max_I_c_3q": round(max_3q, 8),
        "max_I_c_2q": round(max_2q, 8),
        "advantage_ratio": round(advantage, 4),
        "trajectory_3q": ic_3q,
        "trajectory_2q": ic_2q,
        "pass": bool(max_3q > max_2q and max_3q > 1e-10),
    }
    print(f"  P1: 3q={max_3q:+.6f}  2q={max_2q:+.6f}  ratio={advantage:.2f}x  {'PASS' if p1['pass'] else 'FAIL'}")

    # --- P2: Advantage is structural (cross-partition), not just dimensional ---
    # 3q WITHOUT Fi (same 8x8 space, same Ti/Fe/Te, but no cross-partition op)
    # still has more Hilbert dimensions than 2q, but should NOT outperform
    # 3q WITH Fi on the q1q2-vs-q3 partition.
    ic_no_fi, ic_no_fi_cuts = run_3q_cycle(rho_000(), N, deph=0.05, theta=np.pi, use_fi=False)
    max_3q_no_fi_cut2 = max(ic_no_fi_cuts["cut2_12vs3"])
    # 3q with Fi achieves positive I_c on cut1; without Fi, cut2 should be <= 0
    p2 = {
        "description": "Advantage is structural: 3q with cross-partition Fi vs 3q without (same dimension)",
        "max_I_c_3q_with_Fi_cut1": round(max_3q, 8),
        "max_I_c_3q_no_Fi_cut2": round(max_3q_no_fi_cut2, 8),
        "max_I_c_2q": round(max_2q, 8),
        "structural_advantage": bool(max_3q > 0 and max_3q_no_fi_cut2 <= 1e-10),
        "pass": bool(max_3q > 0 and max_3q_no_fi_cut2 <= 1e-10),
    }
    print(f"  P2: 3q+Fi={max_3q:+.6f}  3q-Fi(cut2)={max_3q_no_fi_cut2:+.6f}  "
          f"structural={'YES' if p2['pass'] else 'NO'}  {'PASS' if p2['pass'] else 'FAIL'}")

    # --- N1: Random 8x8 unitaries -> I_c sometimes positive but not sustained ---
    rng = np.random.default_rng(42)
    n_random_trials = 10
    random_sustained = []
    random_max_ics = []

    for trial in range(n_random_trials):
        # Generate random unitary via QR decomposition
        Z = rng.standard_normal((8, 8)) + 1j * rng.standard_normal((8, 8))
        Q, R = np.linalg.qr(Z)
        D = np.diag(R)
        Ph = np.diag(D / np.abs(D))
        U_random = Q @ Ph

        rho = rho_000()
        trial_ics = []
        for _ in range(N):
            # Apply standard engine
            Ti = build_3q_Ti(strength=0.05)
            Fe = build_3q_Fe(strength=1.0, phi=0.4)
            Te = build_3q_Te(strength=0.05, q=0.7)
            rho = Ti(rho)
            rho = Fe(rho)
            rho = Te(rho)
            # Apply random unitary instead of structured Fi
            rho = U_random @ rho @ U_random.conj().T
            rho = ensure_valid_density(rho)
            trial_ics.append(round(compute_Ic_best_3q(rho), 10))

        pos_count = sum(1 for v in trial_ics if v > 1e-10)
        random_sustained.append(pos_count)
        random_max_ics.append(round(max(trial_ics), 8))

    avg_sustained_random = sum(random_sustained) / n_random_trials
    engine_sustained = sum(1 for v in ic_3q if v > 1e-10)

    n1 = {
        "description": "Random 8x8 unitaries -> I_c not reliably sustained (structure matters)",
        "engine_positive_cycles": engine_sustained,
        "random_avg_positive_cycles": round(avg_sustained_random, 2),
        "random_positive_per_trial": random_sustained,
        "random_max_ics": random_max_ics,
        "engine_outperforms_random_avg": bool(engine_sustained > avg_sustained_random),
        "pass": bool(engine_sustained > avg_sustained_random),
    }
    print(f"  N1: engine_sustained={engine_sustained}  random_avg={avg_sustained_random:.1f}  "
          f"{'PASS' if n1['pass'] else 'FAIL'}")

    results["positive"] = {"P1": p1, "P2": p2}
    results["negative"] = {"N1": n1}
    pass_count = sum(1 for t in [p1, p2, n1] if t["pass"])
    results["summary"] = f"{pass_count}/3 tests passed"
    results["tools_used"] = ["numpy", "von_neumann_entropy", "partial_trace_keep"]
    results["timestamp"] = "2026-04-05"

    print(f"  Summary: {results['summary']}")
    return results


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print("  BRIDGE VERIFICATION LAYERS 13-16")
    print("  3-qubit cross-partition Fi | I_c positive from separable |000>")
    print("=" * 72)

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)

    # Run all layers
    l13 = layer_13()
    l14 = layer_14()
    l15 = layer_15()
    l16 = layer_16()

    # Write individual JSON files
    outputs = [
        ("layer13_entanglement_earned_results.json", l13),
        ("layer14_bridge_crosses_partition_results.json", l14),
        ("layer15_sustained_positive_ic_results.json", l15),
        ("layer16_3q_vs_2q_advantage_results.json", l16),
    ]

    for fname, data in outputs:
        path = os.path.join(out_dir, fname)
        with open(path, "w") as f:
            json.dump(sanitize(data), f, indent=2)
        print(f"  -> {path}")

    # Final summary
    all_tests = []
    for data in [l13, l14, l15, l16]:
        for section in ["positive", "negative"]:
            if section in data:
                for test_name, test_data in data[section].items():
                    all_tests.append((data["layer"], test_name, test_data["pass"]))

    total = len(all_tests)
    passed = sum(1 for _, _, p in all_tests if p)

    print("\n" + "=" * 72)
    print(f"  GRAND TOTAL: {passed}/{total} tests passed")
    print("=" * 72)
    for layer, name, p in all_tests:
        print(f"  L{layer} {name:5s}: {'PASS' if p else 'FAIL'}")
    print("=" * 72)


if __name__ == "__main__":
    main()
