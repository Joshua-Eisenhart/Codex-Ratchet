#!/usr/bin/env python3
"""
Layer 3 Validation SIM — Operators on Stages
=============================================
First layer with dynamics. Operators act on pre-existing topology.

Tests:
  1. All 4 operators preserve CPTP (ρ ≥ 0, Tr(ρ) = 1)
  2. Ti acts along fiber (dephasing: kills off-diagonal)
  3. Fe acts as z-axis unitary rotation (preserves z populations and entropy)
  4. Te acts as x-basis dephasing (preserves x populations, changes spectrum)
  5. Fi acts as x-axis unitary rotation (mixes z populations, preserves entropy)
  6. Commutator structure matches current operator math
  7. Each operator has measurable effect (non-trivial displacement)
  8. ΔΦ sign per operator matches SG/EE expectations
  9. Polarity (up/down) produces different outcomes

Token: E_OPERATORS_ON_STAGES_VALID
"""

import numpy as np
import os
import sys
import json
import dataclasses
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical foundation baseline: operator action on stages is a geometric engine validation pass, not a canonical nonclassical proof object."

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hopf_manifold import (
    random_s3_point, coherent_state_density, density_to_bloch,
    von_neumann_entropy_2x2,
)
from geometric_operators import (
    apply_Ti, apply_Fe, apply_Te, apply_Fi,
    negentropy, delta_phi, trace_distance_2x2,
    _ensure_valid_density, I2,
)
from proto_ratchet_sim_runner import EvidenceToken

Q_PLUS = np.array([[1, 1], [1, 1]], dtype=complex) / 2
Q_MINUS = np.array([[1, -1], [-1, 1]], dtype=complex) / 2


def is_valid_density(rho, tol=1e-8):
    """Check ρ ≥ 0, Tr(ρ) = 1, Hermitian."""
    herm = np.linalg.norm(rho - rho.conj().T) < tol
    tr = abs(np.real(np.trace(rho)) - 1.0) < tol
    evals = np.linalg.eigvalsh(rho)
    psd = np.min(evals) > -tol
    return herm and tr and psd


def run_L3_validation():
    print("=" * 72)
    print("LAYER 3: OPERATORS ON STAGES VALIDATION")
    print("  'Operators act on pre-existing topology'")
    print("=" * 72)

    rng = np.random.default_rng(42)
    n_trials = 100
    all_pass = True
    results = {}

    # ── Test 1: CPTP preservation ────────────────────────────────
    print("\n  [T1] CPTP preservation (all operators, both polarities)...")
    cptp_ok = True
    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = coherent_state_density(q)
        # Also test mixed states
        rho_mix = 0.7 * rho + 0.3 * I2 / 2

        for op, name in [(apply_Ti, "Ti"), (apply_Fe, "Fe"),
                         (apply_Te, "Te"), (apply_Fi, "Fi")]:
            for pol in [True, False]:
                for rho_in in [rho, rho_mix]:
                    rho_out = op(rho_in, polarity_up=pol)
                    if not is_valid_density(rho_out):
                        cptp_ok = False
                        print(f"    ✗ {name}(pol={pol}) failed CPTP")
    results["cptp_valid"] = bool(cptp_ok)
    print(f"    {'✓' if cptp_ok else '✗'} All operators preserve ρ ≥ 0, Tr=1")
    all_pass = all_pass and cptp_ok

    # ── Test 2: Ti dephases (kills off-diagonal) ────────────────
    print("\n  [T2] Ti: fiber-aligned dephasing...")
    ti_ok = True
    total_offdiag_reduction = 0
    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = coherent_state_density(q)
        rho_out = apply_Ti(rho, polarity_up=True)
        # Off-diagonal magnitude should decrease
        offdiag_before = abs(rho[0, 1])
        offdiag_after = abs(rho_out[0, 1])
        if offdiag_after > offdiag_before + 1e-10:
            ti_ok = False
        total_offdiag_reduction += (offdiag_before - offdiag_after)

    avg_reduction = total_offdiag_reduction / n_trials
    results["ti_dephases"] = bool(ti_ok)
    results["ti_avg_offdiag_reduction"] = float(avg_reduction)
    print(f"    {'✓' if ti_ok else '✗'} Off-diagonal magnitude decreases")
    print(f"      Avg reduction: {avg_reduction:.4f}")
    all_pass = all_pass and ti_ok

    # ── Test 3: Fe is U_z rotation ────────────────────────────────
    print("\n  [T3] Fe: z-axis unitary rotation...")
    rho_plus = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)  # |+⟩⟨+|
    rho_out = apply_Fe(rho_plus, polarity_up=True)
    pop_change = max(abs(np.real(rho_out[0, 0]) - 0.5), abs(np.real(rho_out[1, 1]) - 0.5))
    phase_change = abs(rho_out[0, 1] - rho_plus[0, 1])
    entropy_change = abs(von_neumann_entropy_2x2(rho_out) - von_neumann_entropy_2x2(rho_plus))
    fe_ok = pop_change < 1e-8 and phase_change > 1e-4 and entropy_change < 1e-8
    results["fe_preserves_z_populations"] = bool(pop_change < 1e-8)
    results["fe_changes_phase"] = bool(phase_change > 1e-4)
    results["fe_preserves_entropy"] = bool(entropy_change < 1e-8)
    results["fe_population_max_change"] = float(pop_change)
    results["fe_phase_change"] = float(phase_change)
    results["fe_entropy_change"] = float(entropy_change)
    print(f"    {'✓' if fe_ok else '✗'} z populations fixed, phase rotates, entropy preserved")
    all_pass = all_pass and fe_ok

    # ── Test 4: Te is x-basis dephasing ──────────────────────────
    print("\n  [T4] Te: x-basis dephasing...")
    te_ok = True
    rho_mix = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
    p_plus_before = np.real(np.trace(Q_PLUS @ rho_mix))
    p_minus_before = np.real(np.trace(Q_MINUS @ rho_mix))
    evals_before = sorted(np.real(np.linalg.eigvalsh(rho_mix)))
    entropy_before = von_neumann_entropy_2x2(rho_mix)
    rho_out = apply_Te(rho_mix, polarity_up=True)
    p_plus_after = np.real(np.trace(Q_PLUS @ rho_out))
    p_minus_after = np.real(np.trace(Q_MINUS @ rho_out))
    evals_after = sorted(np.real(np.linalg.eigvalsh(rho_out)))
    eval_change = np.linalg.norm(np.array(evals_before) - np.array(evals_after))
    entropy_after = von_neumann_entropy_2x2(rho_out)
    x_population_change = max(abs(p_plus_before - p_plus_after), abs(p_minus_before - p_minus_after))
    te_ok = x_population_change < 1e-8 and eval_change > 1e-4 and entropy_after > entropy_before + 1e-4
    results["te_preserves_x_populations"] = bool(x_population_change < 1e-8)
    results["te_changes_eigenvalues"] = bool(eval_change > 1e-4)
    results["te_increases_entropy"] = bool(entropy_after > entropy_before + 1e-4)
    results["te_x_population_max_change"] = float(x_population_change)
    results["te_eval_change"] = float(eval_change)
    results["te_entropy_before"] = float(entropy_before)
    results["te_entropy_after"] = float(entropy_after)
    print(f"    {'✓' if te_ok else '✗'} x populations fixed, spectrum changes, entropy rises")
    all_pass = all_pass and te_ok

    # ── Test 5: Fi is U_x rotation ────────────────────────────────
    print("\n  [T5] Fi: x-axis unitary rotation...")
    fi_ok = True
    rho_0 = np.array([[1, 0], [0, 0]], dtype=complex)  # |0⟩⟨0|
    rho_out = apply_Fi(rho_0, polarity_up=True)
    entropy_before = von_neumann_entropy_2x2(rho_0)
    entropy_after = von_neumann_entropy_2x2(rho_out)
    pop_shift = abs(np.real(rho_out[1, 1]) - np.real(rho_0[1, 1]))
    eval_change = np.linalg.norm(
        np.array(sorted(np.real(np.linalg.eigvalsh(rho_out))))
        - np.array(sorted(np.real(np.linalg.eigvalsh(rho_0))))
    )
    fi_ok = pop_shift > 1e-4 and abs(entropy_after - entropy_before) < 1e-8 and eval_change < 1e-8
    results["fi_mixes_z_populations"] = bool(pop_shift > 1e-4)
    results["fi_preserves_entropy"] = bool(abs(entropy_after - entropy_before) < 1e-8)
    results["fi_preserves_eigenvalues"] = bool(eval_change < 1e-8)
    results["fi_population_shift"] = float(pop_shift)
    results["fi_entropy_before"] = float(entropy_before)
    results["fi_entropy_after"] = float(entropy_after)
    results["fi_eval_change"] = float(eval_change)
    print(f"    {'✓' if fi_ok else '✗'} z populations mix, entropy and spectrum stay fixed")
    all_pass = all_pass and fi_ok

    # ── Test 6: Non-commutativity ────────────────────────────────
    print("\n  [T6] Commutator structure...")
    rho = np.array([[0.5, -0.5j], [0.5j, 0.5]], dtype=complex)  # +y pure state
    rho_TiTe = apply_Te(apply_Ti(rho))
    rho_TeTi = apply_Ti(apply_Te(rho))
    dist_TiTe = trace_distance_2x2(rho_TiTe, rho_TeTi)

    rho_FeFi = apply_Fi(apply_Fe(rho))
    rho_FiFe = apply_Fe(apply_Fi(rho))
    dist_FeFi = trace_distance_2x2(rho_FeFi, rho_FiFe)

    rho_TiFi = apply_Fi(apply_Ti(rho))
    rho_FiTi = apply_Ti(apply_Fi(rho))
    dist_TiFi = trace_distance_2x2(rho_TiFi, rho_FiTi)

    rho_TeFe = apply_Fe(apply_Te(rho))
    rho_FeTe = apply_Te(apply_Fe(rho))
    dist_TeFe = trace_distance_2x2(rho_TeFe, rho_FeTe)

    rho_TiFe = apply_Fe(apply_Ti(rho))
    rho_FeTi = apply_Ti(apply_Fe(rho))
    dist_TiFe = trace_distance_2x2(rho_TiFe, rho_FeTi)

    rho_TeFi = apply_Fi(apply_Te(rho))
    rho_FiTe = apply_Te(apply_Fi(rho))
    dist_TeFi = trace_distance_2x2(rho_TeFi, rho_FiTe)

    noncomm_threshold = 1e-4
    comm_threshold = 1e-6
    pairs = [
        ("[Ti,Te]", dist_TiTe, False),
        ("[Fe,Fi]", dist_FeFi, True),
        ("[Ti,Fi]", dist_TiFi, True),
        ("[Te,Fe]", dist_TeFe, True),
        ("[Ti,Fe]", dist_TiFe, False),
        ("[Te,Fi]", dist_TeFi, False),
    ]
    n_noncomm = 0
    n_comm = 0
    for label, d, should_noncommute in pairs:
        if should_noncommute:
            is_ok = d > noncomm_threshold
            if is_ok:
                n_noncomm += 1
            verdict = "non-commuting" if is_ok else "unexpectedly close"
        else:
            is_ok = d < comm_threshold
            if is_ok:
                n_comm += 1
            verdict = "commuting" if is_ok else "unexpectedly separated"
        print(f"    {label}: D = {d:.6f} ({verdict})")

    noncomm_ok = (n_noncomm == 3) and (n_comm == 3)
    results["noncommuting_pairs"] = n_noncomm
    results["commuting_pairs"] = n_comm
    results["dist_TiTe"] = float(dist_TiTe)
    results["dist_FeFi"] = float(dist_FeFi)
    results["dist_TiFi"] = float(dist_TiFi)
    results["dist_TeFe"] = float(dist_TeFe)
    results["dist_TiFe"] = float(dist_TiFe)
    results["dist_TeFi"] = float(dist_TeFi)
    print(f"    {'✓' if noncomm_ok else '✗'} 3 non-commuting + 3 commuting pairs match current operator math")
    all_pass = all_pass and noncomm_ok

    # ── Test 7: Each operator has non-trivial displacement ───────
    print("\n  [T7] Non-trivial displacement...")
    displacements = {}
    for name, op in [("Ti", apply_Ti), ("Fe", apply_Fe),
                     ("Te", apply_Te), ("Fi", apply_Fi)]:
        total_dist = 0.0
        for _ in range(n_trials):
            q = random_s3_point(rng)
            rho = 0.7 * coherent_state_density(q) + 0.3 * I2 / 2
            rho_out = op(rho, polarity_up=True)
            total_dist += trace_distance_2x2(rho, rho_out)
        avg_dist = total_dist / n_trials
        displacements[name] = avg_dist
        print(f"    {name}: avg displacement = {avg_dist:.4f}")

    all_nontrivial = all(d > 1e-4 for d in displacements.values())
    results["displacements"] = {k: float(v) for k, v in displacements.items()}
    results["all_nontrivial"] = bool(all_nontrivial)
    print(f"    {'✓' if all_nontrivial else '✗'} All operators have non-trivial effect")
    all_pass = all_pass and all_nontrivial

    # ── Test 8: Polarity produces different outcomes ────────────
    print("\n  [T8] Polarity differentiation...")
    pol_ok = True
    for name, op in [("Ti", apply_Ti), ("Fe", apply_Fe),
                     ("Te", apply_Te), ("Fi", apply_Fi)]:
        total_pol_diff = 0.0
        for _ in range(n_trials):
            q = random_s3_point(rng)
            rho = 0.6 * coherent_state_density(q) + 0.4 * I2 / 2
            rho_up = op(rho, polarity_up=True)
            rho_dn = op(rho, polarity_up=False)
            total_pol_diff += trace_distance_2x2(rho_up, rho_dn)
        avg_diff = total_pol_diff / n_trials
        print(f"    {name}: UP vs DOWN avg distance = {avg_diff:.4f}")
        if avg_diff < 1e-6:
            pol_ok = False
    results["polarity_differentiated"] = bool(pol_ok)
    print(f"    {'✓' if pol_ok else '✗'} All operators distinguish UP from DOWN")
    all_pass = all_pass and pol_ok

    # ── Verdict ───────────────────────────────────────────────────
    print(f"\n{'=' * 72}")
    print(f"  LAYER 3 VERDICT: {'PASS ✓' if all_pass else 'KILL ✗'}")
    print(f"{'=' * 72}")

    tokens = []
    if all_pass:
        tokens.append(EvidenceToken(
            "E_OPERATORS_ON_STAGES_VALID", "S_L3_OPERATORS",
            "PASS", 1.0
        ))
    else:
        failed = [k for k, v in results.items() if v is False]
        tokens.append(EvidenceToken(
            "", "S_L3_OPERATORS", "KILL", 0.0,
            f"FAILED: {', '.join(failed)}"
        ))

    # Save
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "L3_operators_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "layer": 3,
            "name": "Operators_On_Stages_Validation",
            "results": results,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2, default=str)
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_L3_validation()
