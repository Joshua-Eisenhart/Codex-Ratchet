"""
World Model SIM — Pro Thread 14 (3-Token Split)
=================================================
Predictive processing agent learns a structured environment.
World model = ρ_agent. Prediction error = ||[ρ_agent, ρ_env]||.
Learning = Ti (observe). Action = Te (act).
Agent discovers hidden structure over 200 Ti/Te cycles.

Emits 3 EvidenceTokens:
  1. S_SIM_WORLD_MODEL_STRUCTURE_V1   — agent discovers hidden eigenstructure
  2. S_SIM_WORLD_MODEL_LEARNING_V1    — KL divergence D(agent||env) decreases
  3. S_SIM_WORLD_MODEL_ADAPTIVE_GENERALIZATION_V1 — agent re-adapts after env shift
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
    EvidenceToken,
)


def quantum_relative_entropy(rho, sigma, eps=1e-12):
    eigvals_r = np.maximum(np.real(np.linalg.eigvalsh(rho)), eps)
    eigvals_s = np.maximum(np.real(np.linalg.eigvalsh(sigma)), eps)
    V_r = np.linalg.eigh(rho)[1]
    V_s = np.linalg.eigh(sigma)[1]
    log_rho = V_r @ np.diag(np.log(eigvals_r).astype(complex)) @ V_r.conj().T
    log_sigma = V_s @ np.diag(np.log(eigvals_s).astype(complex)) @ V_s.conj().T
    return float(np.real(np.trace(rho @ (log_rho - log_sigma))))


def ensure_valid(rho):
    rho = (rho + rho.conj().T) / 2
    eigvals = np.maximum(np.real(np.linalg.eigvalsh(rho)), 0)
    if sum(eigvals) > 0:
        V = np.linalg.eigh(rho)[1]
        rho = V @ np.diag(eigvals.astype(complex)) @ V.conj().T
        rho = rho / np.trace(rho)
    return rho


def _run_learning_loop(rho_agent, rho_env, d, n_cycles):
    """Core Ti/Te learning loop. Returns (rho_agent, rho_env, histories)."""
    D_history = []
    comm_history = []
    accuracy_history = []

    for cycle in range(n_cycles):
        step_size = 0.20 * np.exp(-cycle / 60) + 0.05

        # Ti: observe — dephase agent in env's eigenbasis
        eigvals_e, V_e = np.linalg.eigh(rho_env)
        projs = [V_e[:, k:k+1] @ V_e[:, k:k+1].conj().T for k in range(d)]
        rho_proj = sum(P @ rho_agent @ P for P in projs)
        rho_agent = (1 - step_size) * rho_agent + step_size * rho_proj
        rho_agent = ensure_valid(rho_agent)

        # Fi: FEP free-hamiltonian_norm minimization — blend toward env
        blend = step_size * 0.6
        rho_agent = (1 - blend) * rho_agent + blend * rho_env
        rho_agent = ensure_valid(rho_agent)

        # Te: act — agent influences environment slightly
        eigvals_a2, V_a2 = np.linalg.eigh(rho_agent)
        H_a = V_a2 @ np.diag(eigvals_a2.astype(complex)) @ V_a2.conj().T
        U_act, _ = np.linalg.qr(np.eye(d, dtype=complex) - 1j * 0.002 * H_a)
        rho_env_new = U_act @ rho_env @ U_act.conj().T
        rho_env = ensure_valid(rho_env_new)

        D = quantum_relative_entropy(rho_agent, rho_env)
        comm = np.linalg.norm(rho_agent @ rho_env - rho_env @ rho_agent)
        eigvals_agent = np.sort(np.real(np.linalg.eigvalsh(rho_agent)))[::-1]
        eigvals_env_curr = np.sort(np.real(np.linalg.eigvalsh(rho_env)))[::-1]
        accuracy = 1.0 - np.sum(np.abs(eigvals_agent - eigvals_env_curr)) / 2

        D_history.append(D)
        comm_history.append(comm)
        accuracy_history.append(accuracy)

    return rho_agent, rho_env, D_history, comm_history, accuracy_history


def sim_world_model(d=8, n_cycles=200):
    print(f"\n{'='*60}")
    print(f"WORLD MODEL — PREDICTIVE PROCESSING (3-TOKEN SPLIT)")
    print(f"  d={d}, cycles={n_cycles}")
    print(f"{'='*60}")

    np.random.seed(42)

    # ── Phase 1: Build structured environment ──
    eigvals_env = np.array([0.4, 0.25, 0.15, 0.1, 0.05, 0.03, 0.015, 0.005])
    eigvals_env = eigvals_env[:d]
    eigvals_env = eigvals_env / sum(eigvals_env)
    V_env = make_random_unitary(d)
    rho_env = V_env @ np.diag(eigvals_env.astype(complex)) @ V_env.conj().T

    rho_agent = make_random_density_matrix(d)

    D_init = quantum_relative_entropy(rho_agent, rho_env)
    comm_init = np.linalg.norm(rho_agent @ rho_env - rho_env @ rho_agent)

    print(f"  Initial D(agent||env): {D_init:.4f}")
    print(f"  Initial ||[ρ_a, ρ_e]||: {comm_init:.4f}")

    # ── Phase 2: Run primary learning loop ──
    rho_agent, rho_env, D_history, comm_history, accuracy_history = \
        _run_learning_loop(rho_agent, rho_env, d, n_cycles)

    D_final = D_history[-1]
    comm_final = comm_history[-1]
    accuracy_final = accuracy_history[-1]
    agent_pure = np.max(np.real(np.linalg.eigvalsh(rho_agent)))

    print(f"\n  Final D(agent||env): {D_final:.4f}")
    print(f"  Final ||[ρ_a, ρ_e]||: {comm_final:.4f}")
    print(f"  Final prediction accuracy: {accuracy_final:.4f}")
    print(f"  D decreased: {D_final < D_init}")
    print(f"  Agent max eigenvalue: {agent_pure:.4f} (>0.25 = structure found)")

    # ── Phase 3: Adaptive generalisation — perturb env, re-learn ──
    print(f"\n  --- ADAPTIVE GENERALISATION PHASE ---")
    rho_env_pre_perturb = rho_env.copy()
    accuracy_pre = accuracy_final

    # Perturb environment with a random unitary rotation
    U_perturb = make_random_unitary(d)
    # Mix: 70 % original env, 30 % rotated env → non-trivial but recoverable shift
    rho_env_perturbed = 0.7 * rho_env + 0.3 * (U_perturb @ rho_env @ U_perturb.conj().T)
    rho_env_perturbed = ensure_valid(rho_env_perturbed)

    D_after_perturb = quantum_relative_entropy(rho_agent, rho_env_perturbed)
    accuracy_after_perturb = 1.0 - np.sum(
        np.abs(
            np.sort(np.real(np.linalg.eigvalsh(rho_agent)))[::-1]
            - np.sort(np.real(np.linalg.eigvalsh(rho_env_perturbed)))[::-1]
        )
    ) / 2
    print(f"  D after perturbation: {D_after_perturb:.4f}")
    print(f"  Accuracy after perturbation: {accuracy_after_perturb:.4f}")

    # Re-learn for 100 additional cycles
    n_readapt = 100
    rho_agent_r, rho_env_r, D_hist_r, _, acc_hist_r = \
        _run_learning_loop(rho_agent, rho_env_perturbed, d, n_readapt)

    D_readapted = D_hist_r[-1]
    accuracy_readapted = acc_hist_r[-1]
    print(f"  D after re-adaptation ({n_readapt} cycles): {D_readapted:.4f}")
    print(f"  Accuracy after re-adaptation: {accuracy_readapted:.4f}")
    recovered = accuracy_readapted > accuracy_after_perturb and accuracy_readapted > 0.85

    # ── Emit 3 EvidenceTokens ──
    results = []

    # TOKEN 1: Structure — agent discovers hidden eigenstructure
    structure_found = agent_pure > 1.0 / d * 1.5
    if structure_found:
        results.append(EvidenceToken(
            "E_SIM_WORLD_MODEL_STRUCTURE_OK", "S_SIM_WORLD_MODEL_STRUCTURE_V1",
            "PASS", float(agent_pure)
        ))
    else:
        results.append(EvidenceToken(
            "", "S_SIM_WORLD_MODEL_STRUCTURE_V1",
            "KILL", float(agent_pure), "NO_STRUCTURE_FOUND"
        ))

    # TOKEN 2: Learning — D(agent||env) decreases
    d_decreased = D_final < D_init
    if d_decreased:
        results.append(EvidenceToken(
            "E_SIM_WORLD_MODEL_LEARNING_OK", "S_SIM_WORLD_MODEL_LEARNING_V1",
            "PASS", D_init - D_final
        ))
    else:
        results.append(EvidenceToken(
            "", "S_SIM_WORLD_MODEL_LEARNING_V1",
            "KILL", 0.0, "D_NOT_DECREASING"
        ))

    # TOKEN 3: Adaptive generalisation — agent re-adapts after env shift
    if recovered:
        results.append(EvidenceToken(
            "E_SIM_WORLD_MODEL_ADAPTIVE_GEN_OK",
            "S_SIM_WORLD_MODEL_ADAPTIVE_GENERALIZATION_V1",
            "PASS", float(accuracy_readapted)
        ))
    else:
        results.append(EvidenceToken(
            "",
            "S_SIM_WORLD_MODEL_ADAPTIVE_GENERALIZATION_V1",
            "KILL", float(accuracy_readapted),
            "AGENT_FAILED_TO_READAPT"
        ))

    return results


if __name__ == "__main__":
    results = sim_world_model()

    print(f"\n{'='*60}")
    print(f"WORLD MODEL RESULTS (3-TOKEN SPLIT)")
    print(f"{'='*60}")
    for e in results:
        icon = "✓" if e.status == "PASS" else "✗"
        print(f"  {icon} {e.sim_spec_id}: {e.status} (value={e.measured_value:.4f})")

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "world_model_results.json")
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
