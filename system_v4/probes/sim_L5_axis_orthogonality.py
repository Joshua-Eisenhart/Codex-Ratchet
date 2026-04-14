#!/usr/bin/env python3
"""
Layer 5 Validation SIM — Axis Orthogonality on Geometry
========================================================
Build Choi matrices from geometric CPTP operators and verify
all pairwise overlaps from the 6 canonical axes.

Axis definitions (geometric):
  Ax1 = Entropy/Boundary:    open vs closed boundary (Fe vs Ti at fixed polarity)
  Ax2 = Scale/Accessibility: expansion vs compression (Te↑ vs Te↓)
  Ax3 = Chirality/Nesting:   Type 1 vs Type 2 engine (inner/outer swap)
  Ax4 = Variance Direction:  Fe/Ti family vs Te/Fi family
  Ax5 = Phase Coherence:     superposition vs mixture (pure vs mixed initial)
  Ax6 = Coupling Strength:   strong vs weak operator strength

Token: E_GEOMETRIC_AXES_VALID
"""

import numpy as np
import os
import sys
import json
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hopf_manifold import coherent_state_density
from geometric_operators import (
    apply_Ti, apply_Fe, apply_Te, apply_Fi,
    _ensure_valid_density, I2, trace_distance_2x2,
)
from proto_ratchet_sim_runner import EvidenceToken


def build_choi(channel_fn, d=2) -> np.ndarray:
    """Build the Choi matrix for a 2×2 CPTP channel.

    J(Φ) = Σ_{ij} |i⟩⟨j| ⊗ Φ(|i⟩⟨j|)

    Returns d²×d² matrix (4×4 for d=2).
    """
    choi = np.zeros((d * d, d * d), dtype=complex)
    for i in range(d):
        for j in range(d):
            # Construct |i⟩⟨j|
            eij = np.zeros((d, d), dtype=complex)
            eij[i, j] = 1.0
            # Apply channel
            phi_eij = channel_fn(eij)
            # Place in Choi matrix using kronecker structure
            for a in range(d):
                for b in range(d):
                    choi[i * d + a, j * d + b] = phi_eij[a, b]
    return choi


def choi_fidelity(J1: np.ndarray, J2: np.ndarray) -> float:
    """Normalized Hilbert-Schmidt overlap between two Choi matrices.

    F = |Tr(J1† · J2)| / (||J1||_HS · ||J2||_HS)
    """
    numerator = abs(np.trace(J1.conj().T @ J2))
    norm1 = np.sqrt(np.real(np.trace(J1.conj().T @ J1)))
    norm2 = np.sqrt(np.real(np.trace(J2.conj().T @ J2)))
    if norm1 * norm2 < 1e-15:
        return 0.0
    return float(numerator / (norm1 * norm2))


def run_L5_validation():
    print("=" * 72)
    print("LAYER 5: AXIS ORTHOGONALITY ON GEOMETRY")
    print("  'All 6 axes as geometric degrees of freedom'")
    print("=" * 72)

    all_pass = True
    results = {}

    # ── Define 6 axis channels ───────────────────────────────────
    # Each axis = pair of channels (positive direction, negative direction)
    # The Choi matrix difference is the axis displacement vector.

    def ax1_pos(rho): return apply_Fe(rho, polarity_up=True)     # Open boundary
    def ax1_neg(rho): return apply_Ti(rho, polarity_up=True)     # Closed boundary

    def ax2_pos(rho): return apply_Te(rho, polarity_up=True)     # Expansion
    def ax2_neg(rho): return apply_Te(rho, polarity_up=False)    # Compression

    def ax3_pos(rho):
        # Type 1 engine (1 cycle): left Weyl, inductive inner
        r = apply_Te(rho, polarity_up=True)
        r = apply_Fi(r, polarity_up=False)
        r = apply_Fe(r, polarity_up=True)
        return apply_Ti(r, polarity_up=True)
    def ax3_neg(rho):
        # Type 2 engine (1 cycle): right Weyl, deductive inner
        r = apply_Fe(rho, polarity_up=True)
        r = apply_Ti(r, polarity_up=True)
        r = apply_Te(r, polarity_up=True)
        return apply_Fi(r, polarity_up=True)

    def ax4_pos(rho):
        # Fe/Ti family (deductive)
        r = apply_Fe(rho, polarity_up=True)
        return apply_Ti(r, polarity_up=True)
    def ax4_neg(rho):
        # Te/Fi family (inductive)
        r = apply_Te(rho, polarity_up=True)
        return apply_Fi(r, polarity_up=True)

    def ax5_pos(rho):
        # Phase-coherent: gentle operation preserving coherence
        return apply_Te(rho, polarity_up=True, strength=0.1)
    def ax5_neg(rho):
        # Phase-destroying: strong dephasing
        return apply_Ti(rho, polarity_up=True, strength=1.0)

    def ax6_pos(rho):
        # Strong coupling
        return apply_Fe(rho, polarity_up=True, strength=1.0)
    def ax6_neg(rho):
        # Weak coupling
        return apply_Fe(rho, polarity_up=True, strength=0.1)

    axes = {
        "Ax1_Boundary": (ax1_pos, ax1_neg),
        "Ax2_Scale": (ax2_pos, ax2_neg),
        "Ax3_Chirality": (ax3_pos, ax3_neg),
        "Ax4_Variance": (ax4_pos, ax4_neg),
        "Ax5_Coherence": (ax5_pos, ax5_neg),
        "Ax6_Coupling": (ax6_pos, ax6_neg),
    }

    # ── Test 1: Build Choi matrices for axis displacement ────────
    print("\n  [T1] Building Choi matrices...")
    choi_displacements = {}
    for name, (pos_fn, neg_fn) in axes.items():
        J_pos = build_choi(pos_fn)
        J_neg = build_choi(neg_fn)
        # Displacement = difference in Choi space
        J_delta = J_pos - J_neg
        hs_norm = np.sqrt(np.real(np.trace(J_delta.conj().T @ J_delta)))
        choi_displacements[name] = J_delta
        print(f"    {name}: ||ΔJ||_HS = {hs_norm:.4f}")

    # Check all norms are non-zero (non-degenerate)
    norms = {k: np.sqrt(np.real(np.trace(v.conj().T @ v)))
             for k, v in choi_displacements.items()}
    all_nonzero = all(n > 0.01 for n in norms.values())
    results["all_nonzero"] = bool(all_nonzero)
    print(f"    {'✓' if all_nonzero else '✗'} All axis norms non-zero")
    all_pass = all_pass and all_nonzero

    # ── Test 2: Pairwise overlaps (15 pairs) ─────────────────────
    print("\n  [T2] Pairwise Choi-HS overlaps...")
    axis_names = list(choi_displacements.keys())
    overlaps = {}
    n_pass = 0
    n_total = 0
    threshold = 0.95  # Below this = "sufficiently independent"

    for i in range(len(axis_names)):
        for j in range(i + 1, len(axis_names)):
            a, b = axis_names[i], axis_names[j]
            J_a = choi_displacements[a]
            J_b = choi_displacements[b]
            overlap = choi_fidelity(J_a, J_b)
            pair_key = f"{a} × {b}"
            overlaps[pair_key] = float(overlap)
            independent = overlap < threshold
            n_total += 1
            if independent:
                n_pass += 1
            icon = "✓" if independent else "✗"
            print(f"    {icon} {pair_key}: {overlap:.4f}")

    results["overlaps"] = overlaps
    results["pairs_pass"] = n_pass
    results["pairs_total"] = n_total
    # Need at least 12/15 pairs independent
    sufficient = n_pass >= 12
    print(f"\n    {'✓' if sufficient else '✗'} {n_pass}/{n_total} pairs independent (need ≥ 12)")
    all_pass = all_pass and sufficient

    # ── Test 3: Axis 3 is genuinely chirality (not Axis 4) ───────
    print("\n  [T3] Axis 3 vs Axis 4 distinctness...")
    ax3_ax4_overlap = overlaps.get("Ax3_Chirality × Ax4_Variance", 1.0)
    ax3_independent = ax3_ax4_overlap < 0.9
    results["ax3_ax4_independent"] = bool(ax3_independent)
    print(f"    Ax3 × Ax4 overlap: {ax3_ax4_overlap:.4f}")
    print(f"    {'✓' if ax3_independent else '✗'} Chirality ≠ Variance Direction")
    all_pass = all_pass and ax3_independent

    # ── Verdict ───────────────────────────────────────────────────
    print(f"\n{'=' * 72}")
    print(f"  LAYER 5 VERDICT: {'PASS ✓' if all_pass else 'KILL ✗'}")
    print(f"{'=' * 72}")

    tokens = []
    if all_pass:
        tokens.append(EvidenceToken(
            "E_GEOMETRIC_AXES_VALID", "S_L5_AXIS_ORTHOGONALITY",
            "PASS", float(n_pass)
        ))
    else:
        failed = [k for k, v in results.items() if v is False]
        tokens.append(EvidenceToken(
            "", "S_L5_AXIS_ORTHOGONALITY", "KILL", float(n_pass),
            f"FAILED: {', '.join(failed)}"
        ))

    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "L5_axis_orthogonality_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "layer": 5,
            "name": "Axis_Orthogonality_Geometric",
            "results": results,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2, default=str)
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_L5_validation()
