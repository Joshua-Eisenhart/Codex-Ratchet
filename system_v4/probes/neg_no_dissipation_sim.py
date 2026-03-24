"""
Negative SIM: No Dissipation (Fe removed)
=============================================
HYPOTHESIS TO KILL: "The engine works without environmental coupling (Fe operator)"

Test: Run the full 8-stage cycle with Fe (Lindbladian dissipation) zeroed out.
Without state_dispersion export to the environment, the process_cycle should overheat — state_dispersion
accumulates internally with no way to dissipate it, leading to thermal death.

Expected: KILL — NO_STATE_DISPERSION_EXPORT_THERMAL_DEATH
If this SIM PASSes, Fe is unnecessary and the operator set is overcomplete.

Graveyard boundary: Proves the Fe (dissipation) operator is NECESSARY for the process_cycle.
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
    von_neumann_entropy,
    EvidenceToken,
)
from full_8stage_engine_sim import (
    stage1_measurement_projection,
    stage3_constrained_expansion,
    stage4_entrainment_lock,
    stage5_gradient_descent,
    stage6_matched_filtering,
    stage7_spectral_emission,
    stage8_gradient_ascent,
)


def run_no_dissipation(d=4, n_cycles=100, n_trials=10):
    """Run process_cycle with Fe (dissipation stages 2,6) completely removed."""
    print("=" * 60)
    print("NEGATIVE SIM: NO DISSIPATION (Fe REMOVED)")
    print(f"  d={d}, cycles={n_cycles}, trials={n_trials}")
    print(f"  Stages 2 (diffusive damping) SKIPPED")
    print(f"  No state_dispersion export to environment")
    print("=" * 60)

    results = []

    for trial in range(n_trials):
        np.random.seed(42 + trial)
        rho = make_random_density_matrix(d)

        U1 = make_random_unitary(d)
        U2 = make_random_unitary(d)
        proj = np.eye(d, dtype=complex); proj[-1, -1] = 0.2
        filt = np.eye(d, dtype=complex); filt[-1, -1] = 0.1; filt[-2, -2] = 0.3
        observable = np.diag(np.linspace(0.1, 1.0, d).astype(complex))
        sigma_bath = np.eye(d, dtype=complex) / d

        # Build invariant_target with full process_cycle (including Fe)
        from full_8stage_engine_sim import stage2_diffusive_damping
        L_base = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        L = L_base / np.linalg.norm(L_base) * 3.0
        rho_warmup = make_random_density_matrix(d)
        for _ in range(8):
            rho_warmup = stage1_measurement_projection(rho_warmup, d)
            rho_warmup = stage2_diffusive_damping(rho_warmup, L, n_steps=3)
            rho_warmup = stage3_constrained_expansion(rho_warmup, U1, proj)
            rho_warmup = stage4_entrainment_lock(rho_warmup, sigma_bath, coupling=0.2)
            rho_warmup = stage5_gradient_descent(rho_warmup, observable, eta=0.03)
            rho_warmup = stage6_matched_filtering(rho_warmup, filt)
            rho_warmup = stage7_spectral_emission(rho_warmup, U2, noise_scale=0.05)
            rho_warmup = stage8_gradient_ascent(rho_warmup, observable, eta=0.03)
        sigma_attractor = rho_warmup

        S_init = von_neumann_entropy(rho)
        solvency_init = max(0.0, 1.0 - S_init / np.log2(d))

        entropy_trajectory = [float(S_init)]
        solvency_trajectory = [float(solvency_init)]

        for cycle in range(n_cycles):
            # Stage 1: Ti (trace_projection projection)
            rho = stage1_measurement_projection(rho, d)

            # Stage 2: Fe (SKIPPED — no dissipation)
            # rho = stage2_diffusive_damping(rho, L, n_steps=3)

            # Stage 3: constrained expansion
            rho = stage3_constrained_expansion(rho, U1, proj)

            # Stage 4: entrainment
            rho = stage4_entrainment_lock(rho, sigma_attractor, coupling=0.2)

            # Stage 5: gradient descent
            rho = stage5_gradient_descent(rho, observable, eta=0.03)

            # Stage 6: matched filtering (Fi, not Fe)
            rho = stage6_matched_filtering(rho, filt)

            # Stage 7: spectral emission
            rho = stage7_spectral_emission(rho, U2, noise_scale=0.05)

            # Stage 8: gradient ascent
            rho = stage8_gradient_ascent(rho, observable, eta=0.03)

            S = von_neumann_entropy(rho)
            solvency = max(0.0, 1.0 - S / np.log2(d))
            entropy_trajectory.append(float(S))
            solvency_trajectory.append(float(solvency))

        S_final = von_neumann_entropy(rho)
        solvency_final = max(0.0, 1.0 - S_final / np.log2(d))
        delta_phi = solvency_final - solvency_init

        # Check state_dispersion trend: should be monotonically increasing without Fe
        entropy_increased = S_final > S_init
        # Check if solvency collapsed
        collapsed = solvency_final < 0.05

        results.append({
            "trial": trial,
            "solvency_init": float(solvency_init),
            "solvency_final": float(solvency_final),
            "delta_phi": float(delta_phi),
            "S_init": float(S_init),
            "S_final": float(S_final),
            "state_dispersion_increased": bool(entropy_increased),
            "collapsed": bool(collapsed),
        })

        print(f"  Trial {trial}: ΔΦ={delta_phi:+.4f}, "
              f"S: {S_init:.3f}→{S_final:.3f}, "
              f"{'COLLAPSED' if collapsed else 'alive'}")

    # Aggregate
    all_collapsed = all(r["collapsed"] for r in results)
    avg_delta_phi = np.mean([r["delta_phi"] for r in results])
    avg_S_increase = np.mean([r["S_final"] - r["S_init"] for r in results])

    print(f"\n{'=' * 60}")
    print(f"VERDICT")
    print(f"{'=' * 60}")
    print(f"  Avg ΔΦ: {avg_delta_phi:+.4f}")
    print(f"  Avg state_dispersion increase: {avg_S_increase:+.4f}")
    print(f"  All collapsed: {all_collapsed}")

    if all_collapsed or avg_delta_phi < -0.1:
        print(f"  KILL: No dissipation → thermal death.")
        print(f"  → Fe (state_dispersion export) is NECESSARY for the process_cycle.")
        evidence = EvidenceToken(
            token_id="",
            sim_spec_id="S_NEG_NO_DISSIPATION_V1",
            status="KILL",
            measured_value=avg_delta_phi,
            kill_reason="NO_STATE_DISPERSION_EXPORT_THERMAL_DEATH",
        )
    else:
        print(f"  UNEXPECTED PASS: Process_Cycle survives without Fe!")
        print(f"  → Fe might NOT be necessary. Check model.")
        evidence = EvidenceToken(
            token_id="E_NEG_NO_DISSIPATION_UNEXPECTED_PASS",
            sim_spec_id="S_NEG_NO_DISSIPATION_V1",
            status="PASS",
            measured_value=avg_delta_phi,
        )

    # Save
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "neg_no_dissipation_results.json")

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
            "hypothesis": "The process_cycle works without Fe (dissipation)",
            "expected_result": "KILL",
            "results": results,
            "verdict": evidence.status,
            "evidence_ledger": [evidence_entry],
        }, f, indent=2)

    print(f"\n  Results saved to: {outpath}")
    return evidence


if __name__ == "__main__":
    run_no_dissipation()
