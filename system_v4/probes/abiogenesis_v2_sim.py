#!/usr/bin/env python3
"""
Abiogenesis V2 SIM — Pro Thread 2
=================================
Tests the topological permutations of Axis 3 x Axis 4 explicitly.

Instead of testing random CPTP matrices, we cross the Math Class 
(Deductive vs Inductive) with the Loop Impedance (Outer vs Inner) 
to create the 4 possible engine block topologies:

1. Outer-Deductive / Inner-Inductive (Type 1 Engine)
2. Outer-Inductive / Inner-Deductive (Type 2 Engine)
3. Outer-Deductive / Inner-Deductive (Over-Constrained Death)
4. Outer-Inductive / Inner-Inductive (Thermal Expansion Death)

We prove that only the exact Chiral Topological arrangements 
(Type 1 and Type 2) extract negentropy and survive.
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

def build_h_and_eigenbasis(d, seed=77):
    np.random.seed(seed)
    H = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    H = (H + H.conj().T) / 2
    evals, evecs = np.linalg.eigh(H)
    return H, evals, evecs

def build_Ti_eigen_ops(evecs, d):
    Ti_ops = []
    for k in range(d):
        v = evecs[:, k].reshape(d, 1)
        L = v @ v.conj().T
        Ti_ops.append(L)
    return Ti_ops

def build_Fe_selective_ops(evals, evecs, d, omega_loop, beta=1.0):
    Fe_ops = []
    critical_factor = 2.0 * omega_loop
    for j in range(d):
        for k in range(d):
            if j != k and evals[j] > evals[k]:
                v_j = evecs[:, j].reshape(d, 1)
                v_k = evecs[:, k].reshape(d, 1)
                gap = max(evals[j] - evals[k], 0.001)
                rate = 1.0 if gap > 0 else np.exp(beta * gap)
                weight = np.sqrt(rate * gap) * critical_factor
                L = weight * (v_k @ v_j.conj().T)
                Fe_ops.append(L)
    return Fe_ops

def run_loop_phase(rho, d, math_class, loop_impedance, H, evals, evecs, dt=0.01):
    """
    Executes a 4-stage loop sequence.
    math_class: "DEDUCTIVE" (Ti/Fe) or "INDUCTIVE" (Te/Fi)
    loop_impedance: "OUTER" (omega=1.0) or "INNER" (omega=3.0)
    """
    omega = 1.0 if loop_impedance == "OUTER" else 3.0
    gamma = 2.0 * omega  # apply basic critical damping constraint
    
    Ti_ops = build_Ti_eigen_ops(evecs, d)
    Fe_ops = build_Fe_selective_ops(evals, evecs, d, omega)
    
    Fi = np.zeros((d, d), dtype=complex)
    for k in range(d):
        weight = 0.9 if k < d//2 else 0.5
        v = evecs[:, k].reshape(d, 1)
        Fi += weight * (v @ v.conj().T)

    # 4 stages per loop
    for stage in range(4):
        # Determine dominant operator for this stage
        if math_class == "DEDUCTIVE":
            dominant = "Ti" if stage % 2 == 0 else "Fe"
        else: # INDUCTIVE
            dominant = "Fi" if stage % 2 == 0 else "Te"
            
        if dominant == "Te":
            scale = gamma * dt
            U = np.linalg.matrix_power(np.eye(d, dtype=complex) - 1j * scale * H, 1)
            Q, _ = np.linalg.qr(U)
            rho = Q @ rho @ Q.conj().T
        elif dominant == "Fi":
            f_scale = gamma * dt
            rho = (1 - f_scale) * rho + f_scale * (Fi @ rho @ Fi.conj().T)
        elif dominant == "Ti":
            drho = np.zeros((d, d), dtype=complex)
            for L in Ti_ops:
                LdL = L.conj().T @ L
                drho += gamma * (L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL))
            rho = rho + dt * drho
        elif dominant == "Fe":
            drho = np.zeros((d, d), dtype=complex)
            for L in Fe_ops:
                LdL = L.conj().T @ L
                drho += gamma * (L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL))
            rho = rho + dt * drho
            
        rho = ensure_valid(rho)
    return rho

def sim_abiogenesis_topologies(d=4, cycles=10):
    print(f"\n{'='*60}")
    print(f"ABIOGENESIS V2 — TOPOLOGY EXCLUSION MATRIX")
    print(f"{'='*60}")
    
    permutations = [
        ("DEDUCTIVE", "INDUCTIVE", "Type 1 Engine (Left Weyl)"),
        ("INDUCTIVE", "DEDUCTIVE", "Type 2 Engine (Right Weyl)"),
        ("DEDUCTIVE", "DEDUCTIVE", "Static Fallback (Over-Condensation)"),
        ("INDUCTIVE", "INDUCTIVE", "Expansion Fallback (Thermal Death)"),
    ]
    
    results_map = {}
    tokens = []
    
    for outer_math, inner_math, label in permutations:
        np.random.seed(42)
        rho_initial = make_random_density_matrix(d)
        
        # We need a stable/recurrent Hamiltonian across the topology tests
        H, evals, evecs = build_h_and_eigenbasis(d, seed=123)
        
        rho = rho_initial.copy()
        phi_start = negentropy(rho, d)
        for cycle in range(cycles):
            rho = run_loop_phase(rho, d, outer_math, "OUTER", H, evals, evecs)
            rho_middle = rho.copy()
            rho = run_loop_phase(rho, d, inner_math, "INNER", H, evals, evecs)
            if cycle == cycles - 1:
                cycle_dist = trace_distance(rho_middle, rho)
            
        phi_end = negentropy(rho, d)
        dphi = phi_end - phi_start
        
        # Check for Topological Stability (Heartbeat fixed point)
        eigvals = np.sort(np.real(np.linalg.eigvalsh(rho)))[::-1]
        
        is_stable = cycle_dist < 0.05  # Engine has successfully synced into a micro-orbit
        
        # Life requires negentropy gain AND a stable topological heartbeat
        is_alive = dphi > 1e-3 and is_stable
        
        if is_alive:
            marker = "✓ ALIVE"
        elif not is_stable:
            marker = "✗ DEAD (THRASHING)"
            dphi = -1.0 # Penalize unstable state for exclusion logic
        else:
            marker = "✗ DEAD (MIXED) "
            
        print(f"  {marker:18s} | Outer:{outer_math:9s} / Inner:{inner_math:9s} -> ΔΦ={dphi:+.6f} [Orbit={cycle_dist:.4f}] ({label})")
        results_map[f"{outer_math}_{inner_math}"] = dphi
        
    # Generate Evidence Tokens
    type1_pass = results_map["DEDUCTIVE_INDUCTIVE"] > 0
    if type1_pass:
        tokens.append(EvidenceToken("E_SIM_ABIOGENESIS_TYPE1_OK", "S_SIM_ABIOGENESIS_V2", "PASS", 1.0))
    else:
        tokens.append(EvidenceToken("", "S_SIM_ABIOGENESIS_V2", "KILL", 0.0, "TYPE1_FAILED"))
        
    type2_pass = results_map["INDUCTIVE_DEDUCTIVE"] > 0
    if type2_pass:
        tokens.append(EvidenceToken("E_SIM_ABIOGENESIS_TYPE2_OK", "S_SIM_ABIOGENESIS_V2", "PASS", 1.0))
    else:
        tokens.append(EvidenceToken("", "S_SIM_ABIOGENESIS_V2", "KILL", 0.0, "TYPE2_FAILED"))

    # Prove the "dead" ones actually failed
    deduc_deduc_pass = results_map["DEDUCTIVE_DEDUCTIVE"] > 0
    induc_induc_pass = results_map["INDUCTIVE_INDUCTIVE"] > 0
    
    if not deduc_deduc_pass and not induc_induc_pass:
        tokens.append(EvidenceToken("E_SIM_ABIOGENESIS_EXCLUSION_OK", "S_SIM_ABIOGENESIS_EXCLUSION_V2", "PASS", 1.0))
        print(f"\n  ✓ Exclusion Principle Confirmed: Mathematical overlap causes engine death.")
    else:
        tokens.append(EvidenceToken("", "S_SIM_ABIOGENESIS_EXCLUSION_V2", "KILL", 0.0, "OVERLAP_SURVIVED"))

    return tokens, results_map

if __name__ == "__main__":
    try:
        from datetime import UTC
    except ImportError:
        from datetime import timezone
        UTC = timezone.utc
        
    tokens, data = sim_abiogenesis_topologies()
    
    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "abiogenesis_v2_results.json"
    )
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    
    with open(out_file, "w") as f:
        json.dump({
            "schema": "SIM_EVIDENCE_v1",
            "file": "abiogenesis_v2_sim.py",
            "timestamp": datetime.now(UTC).isoformat() + "Z",
            "evidence_ledger": [t.__dict__ for t in tokens],
            "measurements": data
        }, f, indent=2)
    print(f"\n  Evidence output bound to {out_file}")
