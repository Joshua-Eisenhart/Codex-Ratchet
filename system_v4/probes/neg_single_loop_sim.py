"""
Negative SIM: Single-Loop Process_Cycle
===================================
HYPOTHESIS TO KILL: "A single loop (deductive only) achieves sustained ΔΦ > 0"

Test: Run only Process_Cycle A (FeTi deductive/cooling loop), no Process_Cycle B (TeFi
inductive/heating loop). The process_cycle MUST saturate and stall — the dual-loop
architecture requires both loops to complete the 720° spinor rotation.

Expected: KILL — SINGLE_LOOP_SATURATES
If this SIM ever PASSes, the dual-loop requirement is unnecessary.

Graveyard boundary: Proves the dual-loop (C6) is NECESSARY for sustained ratcheting.
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
from full_8stage_engine_sim import (
    stage1_measurement_projection,
    stage2_diffusive_damping,
    stage6_matched_filtering,
    stage4_entrainment_lock,
)


def run_single_loop(d=4, n_cycles=200, n_trials=10):
    """Run only the deductive (FeTi) loop — no inductive cycle."""
    print("=" * 60)
    print("NEGATIVE SIM: SINGLE-LOOP PROCESS_CYCLE")
    print(f"  d={d}, cycles={n_cycles}, trials={n_trials}")
    print(f"  ONLY deductive loop (FeTi): Ti→Fe→Ti→Fe...")
    print(f"  NO inductive loop (TeFi): Te and Fi disabled")
    print("=" * 60)

    results = []

    for trial in range(n_trials):
        np.random.seed(42 + trial)
        rho = make_random_density_matrix(d)

        # Build operators
        L_base = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        L = L_base / np.linalg.norm(L_base) * 3.0

        sigma_bath = np.eye(d, dtype=complex) / d
        filt = np.eye(d, dtype=complex)
        filt[-1, -1] = 0.1

        S_init = von_neumann_entropy(rho)
        solvency_init = max(0.0, 1.0 - S_init / np.log2(d))

        solvency_trajectory = [float(solvency_init)]
        stall_point = None

        for cycle in range(n_cycles):
            # ONLY deductive (cooling) loop: Ti → Fe → Ti → Fe
            rho = stage1_measurement_projection(rho, d)  # Ti: project (dephase)
            rho = stage2_diffusive_damping(rho, L, n_steps=3)  # Fe: dissipate
            rho = stage1_measurement_projection(rho, d)  # Ti again
            rho = stage2_diffusive_damping(rho, L, n_steps=3)  # Fe again

            S = von_neumann_entropy(rho)
            solvency = max(0.0, 1.0 - S / np.log2(d))
            solvency_trajectory.append(float(solvency))

            # Check for saturation (solvency stops changing)
            if cycle > 10 and stall_point is None:
                recent = solvency_trajectory[-10:]
                if max(recent) - min(recent) < 0.001:
                    stall_point = cycle

        S_final = von_neumann_entropy(rho)
        solvency_final = max(0.0, 1.0 - S_final / np.log2(d))
        delta_phi = solvency_final - solvency_init

        # Check if the loop ever showed sustained positive ratcheting
        # Look at the last 50 cycles
        late_solvencies = solvency_trajectory[-50:]
        late_delta = late_solvencies[-1] - late_solvencies[0] if len(late_solvencies) > 1 else 0
        saturated = abs(late_delta) < 0.005

        results.append({
            "trial": trial,
            "solvency_init": float(solvency_init),
            "solvency_final": float(solvency_final),
            "delta_phi": float(delta_phi),
            "stall_point": stall_point,
            "saturated": saturated,
            "late_delta": float(late_delta),
        })

        print(f"  Trial {trial}: ΔΦ={delta_phi:+.4f}, "
              f"stall@cycle={stall_point}, "
              f"saturated={saturated}")

    # Check results
    all_saturated = all(r["saturated"] for r in results)
    avg_delta_phi = np.mean([r["delta_phi"] for r in results])
    avg_stall = np.mean([r["stall_point"] for r in results if r["stall_point"] is not None])

    print(f"\n{'=' * 60}")
    print(f"VERDICT")
    print(f"{'=' * 60}")
    print(f"  Avg ΔΦ: {avg_delta_phi:+.4f}")
    print(f"  All saturated: {all_saturated}")
    print(f"  Avg stall point: cycle {avg_stall:.0f}" if not np.isnan(avg_stall) else "  No stalls detected")

    if all_saturated:
        print(f"  KILL: Single loop saturates — cannot sustain ratcheting.")
        print(f"  → Dual-loop (C6) is NECESSARY.")
        evidence = EvidenceToken(
            token_id="",
            sim_spec_id="S_NEG_SINGLE_LOOP_V1",
            status="KILL",
            measured_value=avg_delta_phi,
            kill_reason="SINGLE_LOOP_SATURATES",
        )
    else:
        print(f"  UNEXPECTED PASS: Single loop sustained ratcheting!")
        print(f"  → Dual-loop (C6) might NOT be necessary. Check model.")
        evidence = EvidenceToken(
            token_id="E_NEG_SINGLE_LOOP_UNEXPECTED_PASS",
            sim_spec_id="S_NEG_SINGLE_LOOP_V1",
            status="PASS",
            measured_value=avg_delta_phi,
        )

    # Save
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "neg_single_loop_results.json")

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
            "hypothesis": "A single loop (deductive only) achieves sustained ΔΦ > 0",
            "expected_result": "KILL",
            "results": results,
            "verdict": evidence.status,
            "evidence_ledger": [evidence_entry],
        }, f, indent=2)

    print(f"\n  Results saved to: {outpath}")
    return evidence


if __name__ == "__main__":
    run_single_loop()
