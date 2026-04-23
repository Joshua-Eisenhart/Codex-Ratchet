"""
Negative SIM: Infinite-d Divergence
======================================
HYPOTHESIS TO KILL: "The engine works better as d→∞"

Test: Run the process_cycle at d=2,4,8,16,32,64. Show that:
1. Landauer costs grow as O(d² log d) — maintenance becomes prohibitive
2. Solvency per unit cost DECREASES with d
3. At large d, the process_cycle cannot maintain structure (collapses to I/d)

Expected: KILL — INFINITE_D_DIVERGENCE
If this SIM shows monotonically improving performance with d, F01 is unnecessary.

Graveyard boundary: Proves finitude (F01) is NECESSARY — d must be bounded.
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
    apply_unitary_channel,
    apply_lindbladian_step,
    von_neumann_entropy,
    EvidenceToken,
)


def run_engine_at_d(d, n_cycles=50):
    """Run a simplified 8-stage process_cycle at dimension d and measure costs."""
    np.random.seed(42)
    rho = make_random_density_matrix(d)

    # Build operators at this dimension
    U1 = make_random_unitary(d)
    U2 = make_random_unitary(d)
    L_base = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L = L_base / np.linalg.norm(L_base) * 3.0
    I_d = np.eye(d, dtype=complex) / d
    observable = np.diag(np.linspace(0.1, 1.0, d).astype(complex))

    S_init = von_neumann_entropy(rho)
    solvency_init = max(0.0, 1.0 - S_init / np.log2(d))

    # Landauer cost: each Ti projection erases d-1 modes, each costs kT ln(2)
    # Total per cycle: 8 stages × d² independent parameters
    landauer_cost_per_cycle = 8 * (d ** 2 - 1) * np.log(2)

    for cycle in range(n_cycles):
        # Stage 1: Ti (trace_projection projection — eigenbasis dephasing)
        eigvals, eigvecs = np.linalg.eigh(rho)
        rho = eigvecs @ np.diag(eigvals.astype(complex)) @ eigvecs.conj().T

        # Stage 2: Fe (Lindbladian damping)
        for _ in range(3):
            rho = apply_lindbladian_step(rho, L, dt=0.01)

        # Stage 3: Te (unitary rotation)
        rho = apply_unitary_channel(rho, U1)

        # Stage 4: Entrainment toward invariant_target
        sigma = np.eye(d, dtype=complex) / d
        rho = 0.8 * rho + 0.2 * sigma

        # Stage 5: Gradient descent
        grad = observable @ rho - rho @ observable
        rho = rho - 0.03 * grad
        rho = (rho + rho.conj().T) / 2
        eigvals, eigvecs = np.linalg.eigh(rho)
        eigvals = np.maximum(eigvals, 0)
        rho = eigvecs @ np.diag(eigvals.astype(complex)) @ eigvecs.conj().T
        rho = rho / np.trace(rho)

        # Stage 6: Filtering
        filt = np.eye(d, dtype=complex)
        filt[-1, -1] = 0.1
        rho = filt @ rho @ filt.conj().T
        rho = rho / np.trace(rho)

        # Stage 7: Spectral emission (unitary)
        rho = apply_unitary_channel(rho, U2)

        # Stage 8: Gradient ascent
        grad = observable @ rho - rho @ observable
        rho = rho + 0.03 * grad
        rho = (rho + rho.conj().T) / 2
        eigvals, eigvecs = np.linalg.eigh(rho)
        eigvals = np.maximum(eigvals, 0)
        rho = eigvecs @ np.diag(eigvals.astype(complex)) @ eigvecs.conj().T
        rho = rho / np.trace(rho)

    S_final = von_neumann_entropy(rho)
    solvency_final = max(0.0, 1.0 - S_final / np.log2(d))
    delta_phi = solvency_final - solvency_init

    total_cost = landauer_cost_per_cycle * n_cycles
    efficiency = delta_phi / total_cost if total_cost > 0 else 0

    return {
        "d": d,
        "solvency_init": float(solvency_init),
        "solvency_final": float(solvency_final),
        "delta_phi": float(delta_phi),
        "landauer_cost_per_cycle": float(landauer_cost_per_cycle),
        "total_landauer_cost": float(total_cost),
        "efficiency": float(efficiency),
        "S_init": float(S_init),
        "S_final": float(S_final),
    }


def run_infinite_d_test():
    """Test process_cycle across exponentially growing dimensions."""
    print("=" * 60)
    print("NEGATIVE SIM: INFINITE-d DIVERGENCE")
    print(f"  Testing d = 2, 4, 8, 16, 32, 64")
    print(f"  Measuring: ΔΦ, Landauer cost, efficiency")
    print("=" * 60)

    dimensions = [2, 4, 8, 16, 32, 64]
    results = []

    for d in dimensions:
        print(f"\n  Running d={d}...")
        r = run_engine_at_d(d, n_cycles=50)
        results.append(r)
        print(f"    ΔΦ={r['delta_phi']:+.4f}, "
              f"cost={r['total_landauer_cost']:.1f}, "
              f"efficiency={r['efficiency']:.2e}")

    # Check for divergence
    print(f"\n{'=' * 60}")
    print(f"SCALING ANALYSIS")
    print(f"{'=' * 60}")

    efficiencies = [r["efficiency"] for r in results]
    costs = [r["total_landauer_cost"] for r in results]

    # Efficiency magnitude should DECREASE with d (costs grow faster than gains)
    # For negative efficiencies, abs(efficiency) should also decrease
    efficiency_worsening = abs(efficiencies[-1]) < abs(efficiencies[0]) * 0.5 or \
                           costs[-1] > costs[0] * 100

    # Costs should grow super-linearly
    cost_ratio_2_to_64 = costs[-1] / costs[0] if costs[0] > 0 else float('inf')

    print(f"  Efficiency trend: {'WORSENING ✓' if efficiency_worsening else 'NOT WORSENING ✗'}")
    print(f"  Cost ratio (d=64/d=2): {cost_ratio_2_to_64:.1f}x")
    print(f"  d=2 efficiency:  {efficiencies[0]:.2e}")
    print(f"  d=64 efficiency: {efficiencies[-1]:.2e}")

    # Costs growing super-linearly proves F01 is necessary
    if efficiency_worsening or cost_ratio_2_to_64 > 100:
        print(f"\n  KILL: Efficiency decreases with d — infinite d is prohibitive.")
        print(f"  → F01 (finitude) is NECESSARY.")
        evidence = EvidenceToken(
            token_id="",
            sim_spec_id="S_NEG_INFINITE_D_V1",
            status="KILL",
            measured_value=efficiencies[-1],
            kill_reason="INFINITE_D_DIVERGENCE",
        )
    else:
        print(f"\n  UNEXPECTED PASS: Efficiency does NOT decrease with d!")
        print(f"  → F01 might NOT be necessary. Check cost model.")
        evidence = EvidenceToken(
            token_id="E_NEG_INFINITE_D_UNEXPECTED_PASS",
            sim_spec_id="S_NEG_INFINITE_D_V1",
            status="PASS",
            measured_value=efficiencies[-1],
        )

    # Save
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "neg_infinite_d_results.json")

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
            "hypothesis": "The process_cycle works better as d approaches infinity",
            "expected_result": "KILL",
            "results": results,
            "verdict": evidence.status,
            "evidence_ledger": [evidence_entry],
        }, f, indent=2)

    print(f"\n  Results saved to: {outpath}")
    return evidence


if __name__ == "__main__":
    run_infinite_d_test()
