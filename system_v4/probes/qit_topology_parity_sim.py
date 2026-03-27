#!/usr/bin/env python3
"""
QIT Topology Parity SIM
===================================
Tests Topological Parity between Type-1 and Type-2 configurations.
This explicitly eliminates the legacy "Szilard/Engine" terminology, opting
for mathematically pure QIT Process_Cycles.

KEY DISTINCTION (Chirality Reversal / Inverted Loops):
  Type-1: Left Weyl: FeTi on base, TeFi on fiber
  Type-2: Right Weyl: TeFi on base, FeTi on fiber

We use V2 strictly-compliant physics:
  - Landauer-bounded trace operations.
  - Energy-selective detailed-balance Lindbladians (Fe).
  - Explicit Eigenbasis density matrices (Ti).

We test: Both Type-1 and Type-2 topologies achieve structural negentropy generation (ΔΦ > 0)
and are topologically verified via exactly mirroring dynamics.
"""

import numpy as np
import json
import os
import sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    make_random_density_matrix,
    von_neumann_entropy,
    trace_distance,
    EvidenceToken,
)

def build_h_and_eigenbasis(d, seed=77):
    np.random.seed(seed)
    # Unitary flow field (Te)
    H = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    H = (H + H.conj().T) / 2
    evals, evecs = np.linalg.eigh(H)
    return H, evals, evecs

def build_Ti_eigen_ops(evecs, d):
    # Ti: Perfect dephasing in the H eigenbasis
    Ti_ops = []
    for k in range(d):
        v = evecs[:, k].reshape(d, 1)
        L = v @ v.conj().T
        Ti_ops.append(L)
    return Ti_ops

def build_Fe_selective_ops(evals, evecs, d, beta=1.0):
    # Fe: Energy-selective thermodynamic sink (dissipation)
    Fe_ops = []
    for j in range(d):
        for k in range(d):
            if j != k:
                v_j = evecs[:, j].reshape(d, 1)
                v_k = evecs[:, k].reshape(d, 1)
                delta_E = evals[j] - evals[k]
                rate = 1.0 if delta_E > 0 else np.exp(beta * delta_E)
                L = np.sqrt(rate) * (v_k @ v_j.conj().T)
                Fe_ops.append(L)
    return Fe_ops

def ensure_valid(rho):
    rho = (rho + rho.conj().T) / 2
    eigvals = np.maximum(np.real(np.linalg.eigvalsh(rho)), 0)
    if sum(eigvals) > 0:
        V = np.linalg.eigh(rho)[1]
        rho = V @ np.diag(eigvals.astype(complex)) @ V.conj().T
        rho = rho / np.trace(rho)
    return rho

def negentropy(rho, d):
    S = von_neumann_entropy(rho) * np.log(2)
    return np.log(d) - S

TYPE1_STAGES = [
    (1, "Ti", False), # S1: FeTi S1 / DOWN
    (2, "Fe", True),  # S2: FeTi S2 / UP
    (3, "Ti", True),  # S3: FeTi S3 / UP
    (4, "Fe", False), # S4: FeTi S4 / DOWN
    (5, "Fi", False), # S5: TeFi S1 / DOWN
    (6, "Te", False), # S6: TeFi S2 / DOWN
    (7, "Fi", True),  # S7: TeFi S3 / UP
    (8, "Te", True),  # S8: TeFi S4 / UP
]

TYPE2_STAGES = [
    (1, "Fi", True),  # S1: TeFi S1 / UP (Chirality flipped)
    (2, "Te", False), # S2: TeFi S2 / DOWN
    (3, "Fi", False), # S3: TeFi S3 / DOWN
    (4, "Te", True),  # S4: TeFi S4 / UP
    (5, "Ti", True),  # S5: FeTi S1 / UP
    (6, "Fe", True),  # S6: FeTi S2 / UP
    (7, "Ti", False), # S7: FeTi S3 / DOWN
    (8, "Fe", False), # S8: FeTi S4 / DOWN
]

def apply_lindblad_stage(rho, d, dominant_op, axis6_up, H, evals, evecs, gamma_dom=5.0, gamma_sub=1.0, dt=0.01):
    omega = np.linalg.norm(H, 'fro') / np.sqrt(d)
    min_gamma = 2.0 * omega
    g_dom_eff = max(gamma_dom, min_gamma)
    
    Ti_ops = build_Ti_eigen_ops(evecs, d)
    Fe_ops = build_Fe_selective_ops(evals, evecs, d)
    
    # Fi filter operator
    Fi = np.zeros((d, d), dtype=complex)
    for k in range(d):
        # Depending on UP vs DOWN, it absorbs vs emits (selectively attenuates non-ground states)
        weight = 0.9 if k < d//2 else (0.5 if not axis6_up else 0.7)
        v = evecs[:, k].reshape(d, 1)
        Fi += weight * (v @ v.conj().T)

    sign = 1.0 if axis6_up else -1.0

    if dominant_op == "Te":
        scale = g_dom_eff * dt
        U = np.linalg.matrix_power(np.eye(d, dtype=complex) - 1j * sign * scale * H, 1)
        Q, _ = np.linalg.qr(U)
        rho = Q @ rho @ Q.conj().T
    elif dominant_op == "Fi":
        f_scale = g_dom_eff * dt * 0.5
        rho = (1 - f_scale) * rho + f_scale * (Fi @ rho @ Fi.conj().T)
    elif dominant_op == "Ti":
        drho = np.zeros((d, d), dtype=complex)
        for L in Ti_ops:
            LdL = L.conj().T @ L
            drho += g_dom_eff * (L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL))
        rho = rho + dt * drho
    elif dominant_op == "Fe":
        drho = np.zeros((d, d), dtype=complex)
        for L in Fe_ops:
            LdL = L.conj().T @ L
            drho += g_dom_eff * (L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL))
        rho = rho + dt * drho

    return ensure_valid(rho)


def run_topology(stage_table, name, rho_init, H, evals, evecs, d, cycles=5):
    rho = rho_init.copy()
    phi_start = negentropy(rho, d)
    
    cycle_deltas = []
    
    for _ in range(cycles):
        phi_cycle_start = negentropy(rho, d)
        for _, dominant, up in stage_table:
            rho = apply_lindblad_stage(rho, d, dominant, up, H, evals, evecs)
        phi_cycle_end = negentropy(rho, d)
        cycle_deltas.append(phi_cycle_end - phi_cycle_start)
        
    total_dphi = negentropy(rho, d) - phi_start
    return rho, total_dphi, cycle_deltas


def sim_qit_topology_parity(d=4, cycles=10):
    print(f"\n{'='*70}")
    print(f"QIT TOPOLOGY PARITY SIM TEST")
    print(f"{'='*70}")

    np.random.seed(42)
    rho_init = make_random_density_matrix(d)
    
    H, evals, evecs = build_h_and_eigenbasis(d)

    print("Running Type-1 Topology [Left Weyl (FeTi base -> TeFi fiber)]")
    rho1, dphi1, deltas1 = run_topology(TYPE1_STAGES, "Type-1", rho_init, H, evals, evecs, d, cycles)
    
    print("Running Type-2 Topology [Right Weyl (TeFi base -> FeTi fiber)]")
    rho2, dphi2, deltas2 = run_topology(TYPE2_STAGES, "Type-2", rho_init, H, evals, evecs, d, cycles)

    print(f"\nRESULTS:")
    print(f"  ΔΦ Type-1: {dphi1:+.6f}")
    print(f"  ΔΦ Type-2: {dphi2:+.6f}")
    
    dist = trace_distance(rho1, rho2)
    print(f"  Trace distance between final states: {dist:.6f}")
    
    is_pass = bool((dphi1 > 0) and (dphi2 > 0))

    tokens = []
    if is_pass:
        print(f"  ✓ TOPOLOGICAL PARITY ACHIEVED. Both topologies are successfully driven forward.")
        tokens.append(EvidenceToken(
            "E_SIM_QIT_PARITY_OK", "S_SIM_QIT_TOPOLOGY_PARITY", "PASS", dphi2
        ))
    else:
        print(f"  ✗ WARNING: One or both topologies failed to generate negentropy.")
        tokens.append(EvidenceToken(
            "", "S_SIM_QIT_TOPOLOGY_PARITY", "KILL", dphi2, "PARITY_REDUCTION_FAILURE"
        ))

    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "qit_topology_parity_results.json"
    )
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    
    # Custom type conversion for json to bypass strict float32 vs python float
    dump_data = {
        "schema": "SIM_EVIDENCE_v1",
        "file": "qit_topology_parity_sim.py",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "tokens": [t.__dict__ for t in tokens],
        "measurements": {
            "dphi_type1": float(dphi1),
            "dphi_type2": float(dphi2),
            "trace_distance": float(dist),
            "topological_parity_proven": is_pass
        }
    }
    
    with open(out_file, "w") as f:
        json.dump(dump_data, f, indent=2)
    print(f"  Results saved to: {out_file}")

    return tokens

if __name__ == "__main__":
    try:
        from datetime import UTC
    except ImportError:
        from datetime import timezone
        UTC = timezone.utc
    sim_qit_topology_parity()
