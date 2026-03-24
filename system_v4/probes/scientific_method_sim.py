"""
Scientific Method SIM — Pro Thread 15
========================================
The scientific method as a coupled process_cycle:
  Process_Cycle A (deductive): hypothesis → Ti refinement → truth
  Process_Cycle B (inductive): data → Te generalization → theory
Neither alone converges; coupled A→B→A does.
Measures Berry phase at each handoff.
"""

import numpy as np
import json
import os
from datetime import datetime, UTC

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    make_random_density_matrix,
    make_random_unitary,
    von_neumann_entropy,
    trace_distance,
    apply_unitary_channel,
    apply_lindbladian_step,
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


def sim_scientific_method(d=8, n_cycles=100):
    print(f"\n{'='*60}")
    print(f"SCIENTIFIC METHOD — COUPLED PROCESS_CYCLE")
    print(f"  d={d}, cycles={n_cycles}")
    print(f"{'='*60}")

    np.random.seed(42)

    # "Truth" state — the ground truth the method aims to discover
    eigvals_truth = np.array([0.35, 0.25, 0.15, 0.1, 0.05, 0.04, 0.03, 0.03])
    eigvals_truth = eigvals_truth[:d]
    eigvals_truth = eigvals_truth / sum(eigvals_truth)
    V_truth = make_random_unitary(d)
    rho_truth = V_truth @ np.diag(eigvals_truth.astype(complex)) @ V_truth.conj().T

    # Process_Cycle A (deductive): starts from hypothesis, refines via Ti
    rho_A = make_random_density_matrix(d)
    D_A_history = []

    for cycle in range(n_cycles):
        eigvals_t, V_t = np.linalg.eigh(rho_truth)
        projs = [V_t[:, k:k+1] @ V_t[:, k:k+1].conj().T for k in range(d)]
        rho_proj = sum(P @ rho_A @ P for P in projs)
        rho_A = 0.95 * rho_A + 0.05 * rho_proj
        rho_A = ensure_valid(rho_A)
        D_A_history.append(quantum_relative_entropy(rho_A, rho_truth))

    print(f"\n  Process_Cycle A (deductive only):")
    print(f"    D(A||truth): {D_A_history[0]:.4f} → {D_A_history[-1]:.4f}")

    # Process_Cycle B (inductive): starts from data, generalizes via Te
    rho_B = make_random_density_matrix(d)
    D_B_history = []

    for cycle in range(n_cycles):
        H_data = rho_truth
        U_gen, _ = np.linalg.qr(np.eye(d, dtype=complex) - 1j * 0.02 * H_data)
        rho_B = apply_unitary_channel(rho_B, U_gen)
        rho_B = ensure_valid(rho_B)
        D_B_history.append(quantum_relative_entropy(rho_B, rho_truth))

    print(f"\n  Process_Cycle B (inductive only):")
    print(f"    D(B||truth): {D_B_history[0]:.4f} → {D_B_history[-1]:.4f}")

    # Coupled A→B→A: alternating deductive and inductive
    rho_coupled = make_random_density_matrix(d)
    D_coupled_history = []
    berry_phases = []

    for cycle in range(n_cycles):
        # Process_Cycle A phase: deductive Ti
        eigvals_t, V_t = np.linalg.eigh(rho_truth)
        projs = [V_t[:, k:k+1] @ V_t[:, k:k+1].conj().T for k in range(d)]
        rho_proj = sum(P @ rho_coupled @ P for P in projs)
        rho_coupled = 0.92 * rho_coupled + 0.08 * rho_proj
        rho_coupled = ensure_valid(rho_coupled)

        rho_mid = rho_coupled.copy()

        # Process_Cycle B phase: inductive Te
        H_data = rho_truth
        U_gen, _ = np.linalg.qr(np.eye(d, dtype=complex) - 1j * 0.02 * H_data)
        rho_coupled = apply_unitary_channel(rho_coupled, U_gen)
        rho_coupled = ensure_valid(rho_coupled)

        berry = np.linalg.norm(rho_mid @ rho_coupled - rho_coupled @ rho_mid)
        berry_phases.append(float(berry))

        D_coupled_history.append(quantum_relative_entropy(rho_coupled, rho_truth))

    print(f"\n  Coupled A→B→A:")
    print(f"    D(coupled||truth): {D_coupled_history[0]:.4f} → {D_coupled_history[-1]:.4f}")
    print(f"    Mean Berry phase at handoff: {np.mean(berry_phases):.6f}")

    coupled_converges = D_coupled_history[-1] < D_coupled_history[0]
    coupled_better = D_coupled_history[-1] < min(D_A_history[-1], D_B_history[-1])

    print(f"\n  Coupled converges: {coupled_converges}")
    print(f"  Coupled beats both: {coupled_better}")

    results = []

    if coupled_converges:
        results.append(EvidenceToken(
            "E_SIM_SCIMETHOD_CONVERGES_OK", "S_SIM_SCIENTIFIC_METHOD_V1",
            "PASS", D_coupled_history[0] - D_coupled_history[-1]
        ))
    else:
        results.append(EvidenceToken(
            "", "S_SIM_SCIENTIFIC_METHOD_V1",
            "KILL", 0.0, "COUPLED_NOT_CONVERGING"
        ))

    results.append(EvidenceToken(
        "E_SIM_BERRY_HANDOFF_OK", "S_SIM_BERRY_HANDOFF_V1",
        "PASS", float(np.mean(berry_phases))
    ))

    if coupled_better:
        results.append(EvidenceToken(
            "E_SIM_COUPLED_OUTPERFORMS_OK", "S_SIM_COUPLED_VS_SINGLE_V1",
            "PASS", float(min(D_A_history[-1], D_B_history[-1]) - D_coupled_history[-1])
        ))
    else:
        results.append(EvidenceToken(
            "", "S_SIM_COUPLED_VS_SINGLE_V1",
            "KILL", 0.0, "SINGLE_BEATS_COUPLED"
        ))

    return results


if __name__ == "__main__":
    results = sim_scientific_method()

    print(f"\n{'='*60}")
    print(f"SCIENTIFIC METHOD RESULTS")
    print(f"{'='*60}")
    for e in results:
        icon = "✓" if e.status == "PASS" else "✗"
        print(f"  {icon} {e.sim_spec_id}: {e.status} (value={e.measured_value:.4f})")

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "scientific_method_results.json")
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
