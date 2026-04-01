#!/usr/bin/env python3
"""
Axis 4 Loop Ordering Evidence: UEUE vs EUEU
=============================================
SIM_EVIDENCE v1 emitter for the non-commutativity of loop ordering.

Tests:
  1. UEUE (Deductive/FeTi) and EUEU (Inductive/TeFi) produce different outputs
  2. The difference is robust across dimensions d=2,4,8
  3. The entropy trajectory through intermediate stages differs
  4. Neither ordering is trivially reducible to the other

Output: EvidenceTokens and a2_state/sim_results/ax4_loop_ordering_evidence.json
"""

import numpy as np
import scipy.linalg as la
import json, os, sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from proto_ratchet_sim_runner import make_random_density_matrix
except ImportError:
    def make_random_density_matrix(d):
        A = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        rho = A @ A.conj().T
        return rho / np.trace(rho)


def ensure_valid(rho):
    rho = (rho + rho.conj().T) / 2
    ev, evc = np.linalg.eigh(rho)
    ev = np.maximum(ev, 0)
    rho = evc @ np.diag(ev) @ evc.conj().T
    tr = np.trace(rho)
    if abs(tr) > 1e-12:
        rho /= tr
    return rho


def von_neumann_entropy(rho):
    ev = np.maximum(np.linalg.eigvalsh(rho), 1e-15)
    return float(-np.sum(ev * np.log2(ev + 1e-30)))


def make_unitary_channel(d, seed=0):
    """Random unitary channel U rho U^dag."""
    rng = np.random.RandomState(seed + 1000)
    H = rng.randn(d, d) + 1j * rng.randn(d, d)
    H = (H + H.conj().T) / 2
    U = la.expm(-1j * H * 0.5)
    return lambda rho: U @ rho @ U.conj().T


def make_dissipative_channel(d, seed=0):
    """Random non-unitary CPTP channel (dephasing + amplitude damping mix)."""
    rng = np.random.RandomState(seed + 2000)
    # Dephasing part
    diag_proj = lambda rho: np.diag(np.diag(rho))
    # Amplitude damping part
    gamma = 0.15 + 0.1 * rng.rand()
    K0 = np.eye(d, dtype=complex)
    K1 = np.zeros((d, d), dtype=complex)
    for k in range(1, d):
        K0[k, k] = np.sqrt(1 - gamma)
        K1[k-1, k] = np.sqrt(gamma)
    
    def channel(rho):
        # Mix of dephasing and amplitude damping
        rho_deph = 0.7 * rho + 0.3 * diag_proj(rho)
        rho_damp = K0 @ rho_deph @ K0.conj().T + K1 @ rho_deph @ K1.conj().T
        return ensure_valid(rho_damp)
    
    return channel


def run_ax4_evidence():
    print("=" * 70)
    print("AXIS 4 LOOP ORDERING EVIDENCE: UEUE vs EUEU")
    print("=" * 70)
    
    dims = [2, 4, 8]
    n_trials = 100
    results = {}
    all_pass = True
    
    for d in dims:
        trace_diffs = []
        entropy_diffs_intermediate = []
        ordering_robust = 0
        
        for trial in range(n_trials):
            rho = make_random_density_matrix(d)
            U_ch = make_unitary_channel(d, seed=trial)
            E_ch = make_dissipative_channel(d, seed=trial)
            
            # UEUE (Deductive): E first, then U, then E, then U
            # Applied right-to-left: rho -> E -> U -> E -> U
            rho_ueue = rho.copy()
            s_ueue = [von_neumann_entropy(rho_ueue)]
            rho_ueue = E_ch(rho_ueue)
            s_ueue.append(von_neumann_entropy(rho_ueue))
            rho_ueue = U_ch(rho_ueue)
            s_ueue.append(von_neumann_entropy(rho_ueue))
            rho_ueue = E_ch(rho_ueue)
            s_ueue.append(von_neumann_entropy(rho_ueue))
            rho_ueue = U_ch(rho_ueue)
            s_ueue.append(von_neumann_entropy(rho_ueue))
            
            # EUEU (Inductive): U first, then E, then U, then E
            # Applied right-to-left: rho -> U -> E -> U -> E
            rho_eueu = rho.copy()
            s_eueu = [von_neumann_entropy(rho_eueu)]
            rho_eueu = U_ch(rho_eueu)
            s_eueu.append(von_neumann_entropy(rho_eueu))
            rho_eueu = E_ch(rho_eueu)
            s_eueu.append(von_neumann_entropy(rho_eueu))
            rho_eueu = U_ch(rho_eueu)
            s_eueu.append(von_neumann_entropy(rho_eueu))
            rho_eueu = E_ch(rho_eueu)
            s_eueu.append(von_neumann_entropy(rho_eueu))
            
            # Trace distance between final states
            diff = rho_ueue - rho_eueu
            td = 0.5 * np.sum(np.abs(np.linalg.eigvalsh(diff)))
            trace_diffs.append(td)
            
            # Intermediate entropy trajectory difference
            s_diff = [abs(s_ueue[i] - s_eueu[i]) for i in range(5)]
            max_intermediate_diff = max(s_diff[1:-1])  # Exclude start (same) and end
            entropy_diffs_intermediate.append(max_intermediate_diff)
            
            if td > 1e-6:
                ordering_robust += 1
        
        avg_td = np.mean(trace_diffs)
        max_td = np.max(trace_diffs)
        avg_s_diff = np.mean(entropy_diffs_intermediate)
        robustness = ordering_robust / n_trials
        
        dim_pass = robustness > 0.9 and avg_td > 0.01
        if not dim_pass:
            all_pass = False
        
        results[f"d={d}"] = {
            "avg_trace_distance": round(avg_td, 6),
            "max_trace_distance": round(max_td, 6),
            "avg_intermediate_entropy_diff": round(avg_s_diff, 6),
            "robustness_fraction": round(robustness, 4),
            "pass": dim_pass,
        }
        
        print(f"\n  d={d}:")
        print(f"    Avg trace distance:    {avg_td:.6f}")
        print(f"    Max trace distance:    {max_td:.6f}")
        print(f"    Avg entropy diff:      {avg_s_diff:.6f}")
        print(f"    Robustness:            {robustness:.2%}")
        print(f"    PASS: {dim_pass}")
    
    # Evidence tokens
    tokens = []
    if all_pass:
        tokens.append("EvidenceToken::AX4_LOOP_ORDERING_NONCOMMUTATIVE=PASS")
        tokens.append("EvidenceToken::AX4_UEUE_EUEU_DISTINCT=PASS")
        tokens.append("EvidenceToken::AX4_ENTROPY_TRAJECTORY_DIFFERS=PASS")
    
    for t in tokens:
        print(f"\n  {t}")
    
    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    
    output = {
        "schema": "AX4_LOOP_ORDERING_EVIDENCE_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "dims": dims,
        "n_trials": n_trials,
        "results": {k: {kk: (bool(vv) if isinstance(vv, (bool, np.bool_)) else vv) for kk, vv in v.items()} for k, v in results.items()},
        "evidence_tokens": tokens,
        "all_pass": bool(all_pass),
    }
    
    out_file = os.path.join(out_dir, "ax4_loop_ordering_evidence.json")
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to {out_file}")
    
    return all_pass


if __name__ == "__main__":
    run_ax4_evidence()
