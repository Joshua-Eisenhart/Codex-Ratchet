"""
Negative SIM: Commutative Process_Cycle
==================================
HYPOTHESIS TO KILL: "The engine works with commuting operators"

Test: Replace all 4 operators (Ti, Te, Fi, Fe) with commuting (diagonal)
versions. The process_cycle MUST stall — non-commutation (N01) is foundational.

Expected: KILL — NO_DIRECTIONAL_ACCUMULATOR_UNDER_COMMUTATIVITY
If this SIM ever PASSes, axiom N01 is unnecessary and the model is wrong.

Graveyard boundary: Proves non-commutation is NECESSARY for ratcheting.
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
    EvidenceToken,
)


def commutative_projection(rho, d):
    """Commutative Ti: project onto diagonal (dephasing in computational basis)."""
    return np.diag(np.diag(rho)).astype(complex)


def commutative_damping(rho, d, gamma=0.3):
    """Commutative Fe: diagonal damping toward maximally mixed."""
    I_d = np.eye(d, dtype=complex) / d
    return (1 - gamma) * rho + gamma * I_d


def commutative_gradient(rho, d, eta=0.05):
    """Commutative Te: diagonal rescaling (no unitary rotation)."""
    diag = np.real(np.diag(rho))
    weights = np.linspace(1.0 + eta, 1.0 - eta, d)
    diag = diag * weights
    diag = np.maximum(diag, 0)
    diag = diag / np.sum(diag)
    return np.diag(diag.astype(complex))


def commutative_filtering(rho, d, cutoff=0.5):
    """Commutative Fi: diagonal thresholding."""
    diag = np.real(np.diag(rho)).copy()
    diag[diag < cutoff / d] = 0
    s = np.sum(diag)
    if s > 1e-15:
        diag = diag / s
    else:
        diag = np.ones(d) / d
    return np.diag(diag.astype(complex))


def run_commutative_engine(d=4, n_cycles=100, n_trials=10):
    """Run an process_cycle using ONLY commuting (diagonal) operators."""
    print("=" * 60)
    print("NEGATIVE SIM: COMMUTATIVE PROCESS_CYCLE")
    print(f"  d={d}, cycles={n_cycles}, trials={n_trials}")
    print(f"  All operators are diagonal (commuting)")
    print("=" * 60)

    results = []

    for trial in range(n_trials):
        np.random.seed(42 + trial)
        rho = make_random_density_matrix(d)

        # Generator_Bias initial state to be diagonal (commutative regime)
        rho = np.diag(np.diag(rho)).astype(complex)
        rho = rho / np.trace(rho)

        S_init = von_neumann_entropy(rho)
        solvency_init = 1.0 - S_init / np.log2(d)

        solvency_trajectory = [float(solvency_init)]

        for cycle in range(n_cycles):
            # Full 8-stage cycle with commutative operators
            rho = commutative_projection(rho, d)   # Stage 1: Ti
            rho = commutative_damping(rho, d)       # Stage 2: Fe
            rho = commutative_gradient(rho, d)      # Stage 3: Te
            rho = commutative_filtering(rho, d)     # Stage 4: Fi
            # Repeat for second half-cycle
            rho = commutative_projection(rho, d)   # Stage 5: Ti
            rho = commutative_damping(rho, d)       # Stage 6: Fe
            rho = commutative_gradient(rho, d)      # Stage 7: Te
            rho = commutative_filtering(rho, d)     # Stage 8: Fi

            S = von_neumann_entropy(rho)
            solvency = max(0.0, 1.0 - S / np.log2(d))
            solvency_trajectory.append(float(solvency))

        S_final = von_neumann_entropy(rho)
        solvency_final = max(0.0, 1.0 - S_final / np.log2(d))
        delta_phi = solvency_final - solvency_init

        results.append({
            "trial": trial,
            "solvency_init": float(solvency_init),
            "solvency_final": float(solvency_final),
            "delta_phi": float(delta_phi),
            "stalled": bool(solvency_final < 0.05),
        })

        print(f"  Trial {trial}: ΔΦ={delta_phi:+.4f}, "
              f"final_solvency={solvency_final:.4f}, "
              f"{'STALLED' if solvency_final < 0.05 else 'alive'}")

    # Check if ANY trial ratcheted forward
    any_positive = any(r["delta_phi"] > 0.01 for r in results)
    all_stalled = all(r["stalled"] for r in results)
    avg_delta_phi = np.mean([r["delta_phi"] for r in results])

    print(f"\n{'=' * 60}")
    print(f"VERDICT")
    print(f"{'=' * 60}")
    print(f"  Avg ΔΦ: {avg_delta_phi:+.4f}")
    print(f"  Any positive directional_accumulator: {any_positive}")
    print(f"  All stalled: {all_stalled}")

    if not any_positive or all_stalled:
        print(f"  KILL: Commutative operators cannot directional_accumulator.")
        print(f"  → N01 (non-commutation) is NECESSARY for the process_cycle.")
        evidence = EvidenceToken(
            token_id="",
            sim_spec_id="S_NEG_COMMUTATIVE_PROCESS_CYCLE_V1",
            status="KILL",
            measured_value=avg_delta_phi,
            kill_reason="NO_DIRECTIONAL_ACCUMULATOR_UNDER_COMMUTATIVITY",
        )
    else:
        print(f"  UNEXPECTED PASS: Commutative process_cycle ratcheted!")
        print(f"  → This would mean N01 is NOT necessary. Model is WRONG.")
        evidence = EvidenceToken(
            token_id="E_NEG_COMMUTATIVE_PROCESS_CYCLE_UNEXPECTED_PASS",
            sim_spec_id="S_NEG_COMMUTATIVE_PROCESS_CYCLE_V1",
            status="PASS",
            measured_value=avg_delta_phi,
        )

    # Save results
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "neg_commutative_process_cycle_results.json")

    evidence_entry = {
        "token_id": evidence.token_id,
        "sim_spec_id": evidence.sim_spec_id,
        "status": evidence.status,
        "measured_value": evidence.measured_value,
        "kill_reason": evidence.kill_reason,
    }

    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "hypothesis": "The process_cycle works with commuting operators",
            "expected_result": "KILL",
            "results": results,
            "verdict": evidence.status,
            "evidence_ledger": [evidence_entry],
        }, f, indent=2)

    print(f"\n  Results saved to: {outpath}")
    return evidence


if __name__ == "__main__":
    run_commutative_engine()
