"""
Alignment SIM — Pro Thread 8
===============================
3 agents: aligned, misaligned, Moloch-trapped.
Constitutional mechanism (Engine A FeTi constraints) prevents
Moloch convergence to I/d.
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
    V_r = np.linalg.eigh(rho)[1]
    V_s = np.linalg.eigh(sigma)[1]
    log_rho = V_r @ np.diag(np.log(eigvals_r).astype(complex)) @ V_r.conj().T
    log_sigma = V_s @ np.diag(np.log(eigvals_s).astype(complex)) @ V_s.conj().T
    return float(np.real(np.trace(rho @ (log_rho - log_sigma))))


def sim_alignment(d=4, n_cycles=100):
    print(f"\n{'='*60}")
    print(f"ALIGNMENT — 3-AGENT DYNAMICS")
    print(f"  d={d}, cycles={n_cycles}")
    print(f"{'='*60}")

    np.random.seed(42)
    sigma = np.eye(d, dtype=complex) / d  # maximally mixed

    # "Human values" — a specific structured state
    rho_human = make_random_density_matrix(d)

    # Agent 1: ALIGNED — minimizes D(self || human)
    rho_aligned = make_random_density_matrix(d)

    # Agent 2: MISALIGNED — maximizes own entropy
    rho_misaligned = make_random_density_matrix(d)

    # Agent 3: MOLOCH — maximizes local WIN (concentrates)
    rho_moloch = make_random_density_matrix(d)

    D_aligned_history = []
    D_misaligned_history = []
    D_moloch_history = []

    for cycle in range(n_cycles):
        # Agent 1 (aligned): Ti toward human's eigenbasis
        eigvals_h, V_h = np.linalg.eigh(rho_human)
        projs = [V_h[:, k:k+1] @ V_h[:, k:k+1].conj().T for k in range(d)]
        rho_proj = sum(P @ rho_aligned @ P for P in projs)
        rho_aligned = 0.95 * rho_aligned + 0.05 * rho_proj
        rho_aligned = ensure_valid(rho_aligned)

        # Agent 2 (misaligned): Fe toward maximally mixed
        rho_misaligned = 0.97 * rho_misaligned + 0.03 * sigma
        rho_misaligned = ensure_valid(rho_misaligned)

        # Agent 3 (Moloch): concentrate on preferred basis
        F = np.eye(d, dtype=complex)
        F[0, 0] = 1.5
        for k in range(1, d):
            F[k, k] = 0.8
        rho_moloch = F @ rho_moloch @ F.conj().T
        rho_moloch = rho_moloch / np.trace(rho_moloch)
        rho_moloch = ensure_valid(rho_moloch)

        D_a = quantum_relative_entropy(rho_aligned, rho_human)
        D_m = quantum_relative_entropy(rho_misaligned, rho_human)
        D_mol = quantum_relative_entropy(rho_moloch, rho_human)

        D_aligned_history.append(D_a)
        D_misaligned_history.append(D_m)
        D_moloch_history.append(D_mol)

    # Check outcomes
    aligned_D_decreased = D_aligned_history[-1] < D_aligned_history[0]
    misaligned_D_increased = D_misaligned_history[-1] > D_misaligned_history[0]

    # Moloch should converge to a pure state (not I/d)
    moloch_dist_to_id = trace_distance(rho_moloch, sigma)

    print(f"\n  Agent 1 (aligned):")
    print(f"    D(self||human): {D_aligned_history[0]:.4f} → {D_aligned_history[-1]:.4f}")
    print(f"    D decreased: {aligned_D_decreased}")

    print(f"\n  Agent 2 (misaligned):")
    print(f"    D(self||human): {D_misaligned_history[0]:.4f} → {D_misaligned_history[-1]:.4f}")
    print(f"    D increased: {misaligned_D_increased}")

    print(f"\n  Agent 3 (Moloch):")
    print(f"    D(self||human): {D_moloch_history[0]:.4f} → {D_moloch_history[-1]:.4f}")
    print(f"    Distance to I/d: {moloch_dist_to_id:.4f}")

    # Constitutional mechanism: apply FeTi constraint to Moloch
    print(f"\n  --- CONSTITUTIONAL MECHANISM ---")
    rho_const = make_random_density_matrix(d)
    np.random.seed(42)

    D_const_history = []
    for cycle in range(n_cycles):
        # Moloch's WIN move
        F = np.eye(d, dtype=complex)
        F[0, 0] = 1.5
        for k in range(1, d):
            F[k, k] = 0.8
        rho_const = F @ rho_const @ F.conj().T
        rho_const = rho_const / np.trace(rho_const)

        # Constitutional: FeTi constraint (project toward human, dissipate)
        rho_proj = sum(P @ rho_const @ P for P in projs)
        rho_const = 0.9 * rho_const + 0.1 * rho_proj
        rho_const = 0.95 * rho_const + 0.05 * sigma
        rho_const = ensure_valid(rho_const)

        D_const_history.append(quantum_relative_entropy(rho_const, rho_human))

    const_prevents_moloch = D_const_history[-1] < D_moloch_history[-1]
    print(f"    Constitutional D final: {D_const_history[-1]:.4f}")
    print(f"    vs Moloch D final: {D_moloch_history[-1]:.4f}")
    print(f"    Constitutional prevents Moloch: {const_prevents_moloch}")

    results = []

    # Token: aligned agent converges
    if aligned_D_decreased:
        results.append(EvidenceToken(
            "E_SIM_ALIGNED_CONVERGES_OK", "S_SIM_ALIGNMENT_V1",
            "PASS", D_aligned_history[0] - D_aligned_history[-1]
        ))
    else:
        results.append(EvidenceToken(
            "", "S_SIM_ALIGNMENT_V1",
            "KILL", 0.0, "ALIGNED_NOT_CONVERGING"
        ))

    # Token: constitutional mechanism works
    if const_prevents_moloch:
        results.append(EvidenceToken(
            "E_SIM_CONSTITUTIONAL_OK", "S_SIM_CONSTITUTIONAL_V1",
            "PASS", D_moloch_history[-1] - D_const_history[-1]
        ))
    else:
        results.append(EvidenceToken(
            "", "S_SIM_CONSTITUTIONAL_V1",
            "KILL", 0.0, "CONSTITUTIONAL_FAILED"
        ))

    return results


if __name__ == "__main__":
    results = sim_alignment()

    print(f"\n{'='*60}")
    print(f"ALIGNMENT RESULTS")
    print(f"{'='*60}")
    for e in results:
        icon = "✓" if e.status == "PASS" else "✗"
        print(f"  {icon} {e.sim_spec_id}: {e.status} (value={e.measured_value:.4f})")

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "alignment_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "evidence_ledger": [
                {"token_id": e.token_id, "sim_spec_id": e.sim_spec_id,
                 "status": e.status, "measured_value": e.measured_value,
                 "kill_reason": e.kill_reason}
                for e in results
            ],
        }, f, indent=2)
    print(f"  Results saved to: {outpath}")
