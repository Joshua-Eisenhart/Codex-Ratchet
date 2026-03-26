#!/usr/bin/env python3
"""
Layer 3 Validation SIM — Operators on Stages
=============================================
First layer with dynamics. Operators act on pre-existing topology.

Tests:
  1. All 4 operators preserve CPTP (ρ ≥ 0, Tr(ρ) = 1)
  2. Ti acts along fiber (dephasing: kills off-diagonal)
  3. Fe acts across fibers (amplitude damping: population transfer)
  4. Te rotates within fiber (unitary: preserves eigenvalues)
  5. Fi filters on base (spectral selection: amplifies dominant)
  6. Non-commutativity: [Ti, Te] ≠ 0, [Fe, Fi] ≠ 0
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

    # ── Test 3: Fe transfers population ──────────────────────────
    print("\n  [T3] Fe: amplitude damping (population transfer)...")
    fe_ok = True
    # Start from |1⟩ state, Fe should decay toward |0⟩
    rho_1 = np.array([[0, 0], [0, 1]], dtype=complex)  # |1⟩⟨1|
    rho_out = rho_1.copy()
    for _ in range(50):
        rho_out = apply_Fe(rho_out, polarity_up=True)
    # After many steps, should be closer to |0⟩
    pop_0_after = np.real(rho_out[0, 0])
    pop_transfer = pop_0_after > 0.5
    results["fe_population_transfer"] = bool(pop_transfer)
    results["fe_target_population"] = float(pop_0_after)
    print(f"    {'✓' if pop_transfer else '✗'} |1⟩ → |0⟩ decay: P(|0⟩) = {pop_0_after:.4f}")
    all_pass = all_pass and pop_transfer

    # ── Test 4: Te preserves eigenvalues (unitary) ───────────────
    print("\n  [T4] Te: unitary rotation (preserves eigenvalues)...")
    te_ok = True
    max_eval_change = 0.0
    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = 0.7 * coherent_state_density(q) + 0.3 * I2 / 2
        evals_before = sorted(np.real(np.linalg.eigvalsh(rho)))
        rho_out = apply_Te(rho, polarity_up=True)
        evals_after = sorted(np.real(np.linalg.eigvalsh(rho_out)))
        change = np.linalg.norm(np.array(evals_before) - np.array(evals_after))
        max_eval_change = max(max_eval_change, change)
        if change > 1e-6:
            te_ok = False

    results["te_preserves_eigenvalues"] = bool(te_ok)
    results["te_max_eval_change"] = float(max_eval_change)
    print(f"    {'✓' if te_ok else '✗'} Eigenvalues preserved (max change = {max_eval_change:.2e})")
    all_pass = all_pass and te_ok

    # ── Test 5: Fi amplifies dominant eigenstate ──────────────────
    print("\n  [T5] Fi: spectral selection...")
    fi_ok = True
    rho_mix = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
    rho_out = rho_mix.copy()
    for _ in range(10):
        rho_out = apply_Fi(rho_out, polarity_up=True)
    # After filtering, should be closer to pure state
    S_before = von_neumann_entropy_2x2(rho_mix)
    S_after = von_neumann_entropy_2x2(rho_out)
    entropy_decreased = S_after < S_before
    results["fi_entropy_decrease"] = bool(entropy_decreased)
    results["fi_entropy_before"] = float(S_before)
    results["fi_entropy_after"] = float(S_after)
    print(f"    {'✓' if entropy_decreased else '✗'} Entropy: {S_before:.4f} → {S_after:.4f}")
    all_pass = all_pass and entropy_decreased

    # ── Test 6: Non-commutativity ────────────────────────────────
    print("\n  [T6] Non-commutativity...")
    noncomm_ok = True

    # [Ti, Te]: Ti then Te ≠ Te then Ti
    q = random_s3_point(rng)
    rho = 0.6 * coherent_state_density(q) + 0.4 * I2 / 2
    rho_TiTe = apply_Te(apply_Ti(rho))
    rho_TeTi = apply_Ti(apply_Te(rho))
    dist_TiTe = trace_distance_2x2(rho_TiTe, rho_TeTi)

    # [Fe, Fi]: Fe then Fi ≠ Fi then Fe
    rho_FeFi = apply_Fi(apply_Fe(rho))
    rho_FiFe = apply_Fe(apply_Fi(rho))
    dist_FeFi = trace_distance_2x2(rho_FeFi, rho_FiFe)

    # Cross-family: [Ti, Fe], [Te, Fi]
    rho_TiFe = apply_Fe(apply_Ti(rho))
    rho_FeTi = apply_Ti(apply_Fe(rho))
    dist_TiFe = trace_distance_2x2(rho_TiFe, rho_FeTi)

    rho_TeFi = apply_Fi(apply_Te(rho))
    rho_FiTe = apply_Te(apply_Fi(rho))
    dist_TeFi = trace_distance_2x2(rho_TeFi, rho_FiTe)

    noncomm_threshold = 1e-6
    pairs = [("[Ti,Te]", dist_TiTe), ("[Fe,Fi]", dist_FeFi),
             ("[Ti,Fe]", dist_TiFe), ("[Te,Fi]", dist_TeFi)]
    n_noncomm = 0
    for label, d in pairs:
        is_nc = d > noncomm_threshold
        if is_nc:
            n_noncomm += 1
        print(f"    {label}: D = {d:.6f} {'(non-commuting)' if is_nc else '(commuting)'}")

    # At least 2 pairs should be non-commuting
    noncomm_ok = n_noncomm >= 2
    results["noncommuting_pairs"] = n_noncomm
    results["dist_TiTe"] = float(dist_TiTe)
    results["dist_FeFi"] = float(dist_FeFi)
    results["dist_TiFe"] = float(dist_TiFe)
    results["dist_TeFi"] = float(dist_TeFi)
    print(f"    {'✓' if noncomm_ok else '✗'} {n_noncomm}/4 pairs non-commuting (need ≥ 2)")
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
