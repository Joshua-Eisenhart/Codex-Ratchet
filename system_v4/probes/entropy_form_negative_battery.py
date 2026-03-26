#!/usr/bin/env python3
"""
Entropy Form Negative Battery
=============================
Tests whether alternative entropy forms are actually better than
von Neumann entropy for the current Hopf / Weyl engine regime.

This is intentionally a negative battery:
  - if an alternative collapses into the same qubit ordering as vN,
    it is NOT better
  - if an alternative is basis-dependent, it is NOT geometry-safe
  - if conditional entropy adds no signal in the current L/R setup,
    it is NOT yet a useful engine metric
  - if all spectral entropies miss pure-state Fi dynamics,
    no alternative entropy rescues that blind spot

The expected honest outcome is:
  - vN remains the best default mixedness metric
  - Renyi-2 is a computational proxy, not a better theory metric
  - Shannon-on-diagonal is not geometry-safe
  - conditional entropy is not meaningful without a joint 4x4 rho_LR
  - pure-state Fi needs a directional metric, not a different entropy
"""

import json
import os
import sys
from datetime import UTC, datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine
from geometric_operators import apply_Fi, apply_Te, trace_distance_2x2
from hopf_manifold import density_to_bloch, von_neumann_entropy_2x2
from proto_ratchet_sim_runner import EvidenceToken


def linear_entropy(rho: np.ndarray) -> float:
    """Linear entropy for a 2x2 density matrix."""
    purity = float(np.real(np.trace(rho @ rho)))
    return 1.0 - purity


def renyi2_entropy(rho: np.ndarray) -> float:
    """Renyi-2 entropy for a 2x2 density matrix."""
    purity = max(float(np.real(np.trace(rho @ rho))), 1e-15)
    return float(-np.log2(purity))


def tsallis2_entropy(rho: np.ndarray) -> float:
    """Tsallis-2 entropy for a 2x2 density matrix."""
    purity = float(np.real(np.trace(rho @ rho)))
    return 1.0 - purity


def shannon_diag_entropy(rho: np.ndarray) -> float:
    """Computational-basis Shannon entropy of the diagonal only."""
    probs = np.clip(np.real(np.diag(rho)), 0.0, 1.0)
    probs = probs[probs > 1e-15]
    return float(-np.sum(probs * np.log2(probs)))


def rel_entropy_to_maxmix(rho: np.ndarray) -> float:
    """Relative entropy D(rho || I/2) in bits for qubits."""
    return 1.0 - von_neumann_entropy_2x2(rho)


def candidate_values(rho: np.ndarray) -> dict[str, float]:
    return {
        "vn": von_neumann_entropy_2x2(rho),
        "linear": linear_entropy(rho),
        "renyi2": renyi2_entropy(rho),
        "tsallis2": tsallis2_entropy(rho),
        "shannon_diag": shannon_diag_entropy(rho),
        "rel_to_maxmix": rel_entropy_to_maxmix(rho),
        "purity": float(np.real(np.trace(rho @ rho))),
    }


def random_density(rng: np.random.Generator) -> np.ndarray:
    a = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
    rho = a @ a.conj().T
    rho /= np.trace(rho)
    return rho


def product_joint_entropy(rho_l: np.ndarray, rho_r: np.ndarray) -> tuple[float, float, float, float]:
    """Return S(L), S(R), S(LR), I(L:R) for the product proxy rho_L ⊗ rho_R."""
    s_l = von_neumann_entropy_2x2(rho_l)
    s_r = von_neumann_entropy_2x2(rho_r)
    rho_lr = np.kron(rho_l, rho_r)
    evals = np.linalg.eigvalsh(rho_lr)
    evals = evals[evals > 1e-15]
    s_lr = float(-np.sum(evals * np.log2(evals)))
    mutual = s_l + s_r - s_lr
    return s_l, s_r, s_lr, mutual


def run_entropy_form_negative_battery():
    print("=" * 72)
    print("ENTROPY FORM NEGATIVE BATTERY")
    print("  'Are alternative entropy forms actually better here?'")
    print("=" * 72)

    rng = np.random.default_rng(42)
    results = {}
    tokens = []

    # ── T1: Qubit spectral-family equivalence ─────────────────────
    print("\n  [T1] Qubit spectral-family equivalence...")
    samples = [random_density(rng) for _ in range(64)]
    pair_total = 0
    disagree_linear = 0
    disagree_renyi2 = 0
    disagree_tsallis2 = 0
    disagree_purity = 0
    max_rel_affine_err = 0.0
    for i in range(len(samples)):
        for j in range(i + 1, len(samples)):
            a = candidate_values(samples[i])
            b = candidate_values(samples[j])
            dvn = a["vn"] - b["vn"]
            if abs(dvn) < 1e-10:
                continue
            pair_total += 1
            if np.sign(a["linear"] - b["linear"]) != np.sign(dvn):
                disagree_linear += 1
            if np.sign(a["renyi2"] - b["renyi2"]) != np.sign(dvn):
                disagree_renyi2 += 1
            if np.sign(a["tsallis2"] - b["tsallis2"]) != np.sign(dvn):
                disagree_tsallis2 += 1
            # Purity orders in the opposite direction to entropy.
            if np.sign(a["purity"] - b["purity"]) == np.sign(dvn):
                disagree_purity += 1
            max_rel_affine_err = max(max_rel_affine_err, abs(a["rel_to_maxmix"] - (1.0 - a["vn"])))

    equiv_ok = (
        pair_total > 0
        and disagree_linear == 0
        and disagree_renyi2 == 0
        and disagree_tsallis2 == 0
        and disagree_purity == 0
        and max_rel_affine_err < 1e-10
    )
    results["spectral_pair_total"] = pair_total
    results["linear_disagreements"] = disagree_linear
    results["renyi2_disagreements"] = disagree_renyi2
    results["tsallis2_disagreements"] = disagree_tsallis2
    results["purity_disagreements"] = disagree_purity
    results["rel_to_maxmix_affine_err"] = float(max_rel_affine_err)
    print(f"    Pairs tested: {pair_total}")
    print(f"    linear / Renyi2 / Tsallis2 disagreements: {disagree_linear} / {disagree_renyi2} / {disagree_tsallis2}")
    print(f"    purity direction disagreements: {disagree_purity}")
    print(f"    max affine error D(rho||I/2) vs 1-S_vN: {max_rel_affine_err:.2e}")
    print(f"    {'✓' if equiv_ok else '✗'} Spectral families are qubit-order equivalent")
    if equiv_ok:
        tokens.append(EvidenceToken("E_ENTROPY_QUBIT_SPECTRAL_EQUIV", "S_ENTROPY_QUBIT_SPECTRAL_EQUIV", "PASS", float(pair_total)))
        tokens.append(EvidenceToken("", "S_NEG_LINEAR_BETTER_THAN_VN", "KILL", float(disagree_linear), "QUBIT_MONOTONE_EQUIVALENT_NOT_BETTER"))
        tokens.append(EvidenceToken("", "S_NEG_RENYI2_BETTER_THAN_VN", "KILL", float(disagree_renyi2), "QUBIT_MONOTONE_EQUIVALENT_NOT_BETTER"))
        tokens.append(EvidenceToken("", "S_NEG_TSALLIS2_BETTER_THAN_VN", "KILL", float(disagree_tsallis2), "QUBIT_MONOTONE_EQUIVALENT_NOT_BETTER"))
        tokens.append(EvidenceToken("", "S_NEG_PURITY_BETTER_THAN_VN", "KILL", float(disagree_purity), "INVERTED_EQUIVALENT_NOT_BETTER"))
    else:
        tokens.append(EvidenceToken("", "S_ENTROPY_QUBIT_SPECTRAL_EQUIV", "KILL", float(pair_total), "SPECTRAL_FAMILY_ORDERING_BROKEN"))

    # ── T2: Shannon basis dependence under unitary motion ────────
    print("\n  [T2] Shannon-on-diagonal basis dependence...")
    basis_failures = 0
    basis_shifts = []
    for _ in range(32):
        rho = random_density(rng)
        rho_rot = apply_Te(rho, polarity_up=True, strength=1.0, angle=0.73)
        s_vn_before = von_neumann_entropy_2x2(rho)
        s_vn_after = von_neumann_entropy_2x2(rho_rot)
        s_diag_before = shannon_diag_entropy(rho)
        s_diag_after = shannon_diag_entropy(rho_rot)
        dvn = abs(s_vn_after - s_vn_before)
        ddiag = abs(s_diag_after - s_diag_before)
        basis_shifts.append(ddiag)
        if dvn < 1e-8 and ddiag > 1e-3:
            basis_failures += 1
    shannon_bad = basis_failures >= 24
    results["shannon_basis_failures"] = basis_failures
    results["shannon_basis_shift_avg"] = float(np.mean(basis_shifts))
    print(f"    Unitary-invariant vN, but diagonal Shannon shifts in {basis_failures}/32 trials")
    print(f"    Avg diagonal-Shannon shift: {np.mean(basis_shifts):.4f}")
    print(f"    {'✓' if shannon_bad else '✗'} Shannon-on-diagonal is basis dependent")
    if shannon_bad:
        tokens.append(EvidenceToken("", "S_NEG_SHANNON_DIAG_GEOMETRIC", "KILL", float(basis_failures), "BASIS_DEPENDENT_NOT_GEOMETRY_SAFE"))
    else:
        tokens.append(EvidenceToken("", "S_NEG_SHANNON_DIAG_GEOMETRIC", "PASS", float(basis_failures)))

    # ── T3: Conditional entropy redundancy in current engine ──────
    print("\n  [T3] Conditional entropy in the current L/R engine...")
    cond_errors = []
    mutuals = []
    for seed in range(16):
        eng = GeometricEngine(engine_type=1)
        state = eng.init_state(rng=np.random.default_rng(seed))
        state = eng.run_cycle(state)
        s_l, s_r, s_lr, mutual = product_joint_entropy(state.rho_L, state.rho_R)
        cond_l_given_r = s_lr - s_r
        cond_errors.append(abs(cond_l_given_r - s_l))
        mutuals.append(abs(mutual))
    conditional_redundant = max(cond_errors) < 1e-8 and max(mutuals) < 1e-8
    results["conditional_proxy_max_error"] = float(max(cond_errors))
    results["conditional_proxy_max_mutual"] = float(max(mutuals))
    print(f"    max |S(L|R)_proxy - S(L)|: {max(cond_errors):.2e}")
    print(f"    max I(L:R)_proxy: {max(mutuals):.2e}")
    print(f"    {'✓' if conditional_redundant else '✗'} Product-proxy conditional entropy adds no signal")
    if conditional_redundant:
        tokens.append(EvidenceToken("", "S_NEG_CONDITIONAL_ENTROPY_CURRENT_ENGINE", "KILL", float(max(mutuals)), "NO_JOINT_STATE_CONDITIONAL_REDUNDANT"))
    else:
        tokens.append(EvidenceToken("", "S_NEG_CONDITIONAL_ENTROPY_CURRENT_ENGINE", "PASS", float(max(mutuals))))

    # ── T4: Pure-state Fi remains entropy-blind across spectral forms ──
    print("\n  [T4] Pure-state Fi blind spot across spectral entropy forms...")
    eng = GeometricEngine(engine_type=1)
    state = eng.init_state(rng=np.random.default_rng(42))
    rho0 = state.rho_L.copy()
    rho1 = apply_Fi(rho0, polarity_up=True, strength=1.0)
    vn_delta = abs(von_neumann_entropy_2x2(rho1) - von_neumann_entropy_2x2(rho0))
    lin_delta = abs(linear_entropy(rho1) - linear_entropy(rho0))
    renyi_delta = abs(renyi2_entropy(rho1) - renyi2_entropy(rho0))
    z0 = np.real(density_to_bloch(rho0)[2])
    z1 = np.real(density_to_bloch(rho1)[2])
    dz = abs(z1 - z0)
    dstate = trace_distance_2x2(rho0, rho1)
    fi_blind = vn_delta < 1e-8 and lin_delta < 1e-8 and renyi_delta < 1e-8 and dstate > 1e-3 and dz > 1e-2
    results["fi_vn_delta"] = float(vn_delta)
    results["fi_linear_delta"] = float(lin_delta)
    results["fi_renyi2_delta"] = float(renyi_delta)
    results["fi_state_distance"] = float(dstate)
    results["fi_z_shift"] = float(dz)
    print(f"    ΔS_vN={vn_delta:.2e}, ΔS_linear={lin_delta:.2e}, ΔS_renyi2={renyi_delta:.2e}")
    print(f"    D(state)={dstate:.4f}, Δz={dz:.4f}")
    print(f"    {'✓' if fi_blind else '✗'} No spectral entropy rescues pure-state Fi")
    if fi_blind:
        tokens.append(EvidenceToken("", "S_NEG_ALT_ENTROPY_RESCUES_PURE_FI", "KILL", float(dstate), "PURE_STATE_FI_NEEDS_DIRECTIONAL_METRIC"))
    else:
        tokens.append(EvidenceToken("", "S_NEG_ALT_ENTROPY_RESCUES_PURE_FI", "PASS", float(dstate)))

    # ── T5: Renyi-2 as proxy, not better theory metric ───────────
    print("\n  [T5] Renyi-2 as computational proxy...")
    proxy_ok = equiv_ok and disagree_renyi2 == 0
    results["renyi2_proxy_ok"] = bool(proxy_ok)
    print(f"    {'✓' if proxy_ok else '✗'} Renyi-2 tracks vN ordering on qubit mixedness")
    if proxy_ok:
        tokens.append(EvidenceToken("E_RENYI2_PROXY_QUBIT_OK", "S_ENTROPY_RENYI2_PROXY_QUBIT", "PASS", float(pair_total)))
    else:
        tokens.append(EvidenceToken("", "S_ENTROPY_RENYI2_PROXY_QUBIT", "KILL", float(disagree_renyi2), "RENYI2_PROXY_ORDERING_FAILED"))

    print(f"\n{'=' * 72}")
    print("  ENTROPY BATTERY COMPLETE")
    print(f"{'=' * 72}")

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "entropy_form_negative_battery_results.json")
    with open(outpath, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "name": "Entropy_Form_Negative_Battery",
                "results": results,
                "evidence_ledger": [t.__dict__ for t in tokens],
                "recommendation": {
                    "best_default_mixedness_metric": "von_neumann_entropy",
                    "best_proxy_metric": "renyi2_entropy",
                    "not_geometry_safe": ["shannon_diag_entropy"],
                    "not_meaningful_without_joint_state": ["conditional_entropy", "mutual_information", "coherent_information"],
                    "needs_auxiliary_metric": ["pure_state_Fi_directionality"],
                },
            },
            f,
            indent=2,
            default=str,
        )
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_entropy_form_negative_battery()
