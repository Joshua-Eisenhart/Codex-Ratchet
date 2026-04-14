#!/usr/bin/env python3
"""
Axis ± Disambiguation and Anti-Conflation Orthogonality Test
=============================================================

PROBLEM: Axes 0, 3, and 6 all have ± / binary structure that can conflate.
This sim proves they are mathematically distinct by computing the
Hilbert-Schmidt overlap of their state-space displacements.

AXIS ± STRUCTURE (what each ± actually means mathematically):
─────────────────────────────────────────────────────────────
Axis 0: SCALAR (not truly ±)
  GA0=0: no fiber averaging → pure state preserved
  GA0=1: full fiber averaging → maximally mixed fiber contribution
  Math: ρ_coarse(n) = (1/n) Σ ρ(fiber_action(q, 2πi/n))
  Label: "fine" vs "coarse"
  
Axis 1: CHANNEL CLASS (binary)
  +: Isothermal — CPTP maps (Lindblad dissipation allowed)
  −: Adiabatic — Unitary maps only (UρU†)
  Label: "open-channel" vs "closed-channel"

Axis 2: BOUNDARY (binary)
  +: Eulerian — field evolution, flux through boundary (∮J·dS ≠ 0)
  −: Lagrangian — trajectory tracking, conserved boundary (∮J·dS = 0)
  Label: "flux" vs "path"

Axis 3: GENERATOR SIGN (true ±)
  +: ρ̇ = +G(ρ)  →  Left Weyl, Inward Flux, clockwise Hopf fiber
  −: ρ̇ = −G(ρ)  →  Right Weyl, Outward Flux, counter-clockwise
  Label: "inward" vs "outward"
  
Axis 4: COMPOSITION ORDER (binary)
  +: Deductive — B∘A (constraint first), V↓ early
  −: Inductive — A∘B (release first), V↑ early
  Label: "constraint-first" vs "release-first"

Axis 5: GENERATOR ALGEBRA (binary)
  +: FGA — Lindblad/GKSL, irreversible, entropy-changing
  −: FSA — Hamiltonian, reversible, entropy-conserving
  Label: "gradient" vs "spectral"

Axis 6: ACTION SIDE (true ±)
  +: Left — ρ → Aρ (pre-composition)
  −: Right — ρ → ρA (post-composition)
  Label: "pre" vs "post"

CONFLATION DANGER PAIRS:
─────────────────────────
  Axis 0 × Axis 3:  "less mixed" ↔ "inward flux"  (both affect purity)
  Axis 3 × Axis 6:  "left Weyl" ↔ "left action"  (both called "left")
  Axis 0 × Axis 6:  "coarse-graining" ↔ "action side"  (less obvious)
  Axis 3 × Axis 4:  "chirality" ↔ "loop direction"  (historical conflation)

LABELS THAT PREVENT CONFLATION (user's principle):
──────────────────────────────────────────────────
  Axis 0: fine/coarse            (NOT left/right, NOT in/out)
  Axis 3: inward/outward         (NOT left/right at axis level)
  Axis 6: pre/post               (NOT left/right Weyl)
  Weyl:   left/right Weyl        (representation, NOT Axis 6)

TEST: Compute Hilbert-Schmidt displacement overlap for each danger pair.
If overlap ≈ 0, axes are orthogonal (not conflating).
"""

import numpy as np
import scipy.linalg as la
import json
import os
import sys
import dataclasses
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from proto_ratchet_sim_runner import EvidenceToken, make_random_density_matrix
except ImportError:
    @dataclasses.dataclass
    class EvidenceToken:
        token_id: str = ""
        sim_spec_id: str = ""
        status: str = ""
        measured_value: float = 0.0
        kill_reason: str = ""

    def make_random_density_matrix(d, seed=None, **kwargs):
        if seed is not None:
            np.random.seed(seed)
        elif 'rng' in kwargs:
            np.random.seed(kwargs['rng'])
        A = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        rho = A @ A.conj().T
        rho /= np.trace(rho)
        return rho


# ═══════════════════════════════════════════════════════════════════
# AXIS DISPLACEMENT OPERATORS
# Each axis defines a pair of maps. The "displacement" is the
# difference in output between the + and − branches.
# ═══════════════════════════════════════════════════════════════════

def axis0_displace(rho, d):
    """Axis 0 displacement: coarse vs fine.
    Coarse-graining = partial dephasing toward diagonal.
    Fine = less dephasing.
    """
    # Model coarse-graining as partial dephasing
    level_high, level_low = 0.8, 0.2
    diag = np.diag(np.diag(rho))
    rho_coarse = (1 - level_high) * rho + level_high * diag
    rho_fine = (1 - level_low) * rho + level_low * diag
    return rho_coarse - rho_fine


def axis1_displace(rho, d):
    """Axis 1 displacement: Isothermal (CPTP) vs Adiabatic (Unitary).
    Isothermal = Lindblad step. Adiabatic = unitary rotation.
    """
    # Isothermal: amplitude damping
    gamma = 0.3
    K0 = np.eye(d, dtype=complex)
    K1 = np.zeros((d, d), dtype=complex)
    for k in range(1, d):
        K0[k, k] = np.sqrt(1 - gamma)
        K1[k-1, k] = np.sqrt(gamma)
    rho_iso = K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T
    rho_iso /= np.trace(rho_iso)
    
    # Adiabatic: random unitary
    H = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    H = (H + H.conj().T) / 2
    U = la.expm(-1j * H * 0.3)
    rho_adi = U @ rho @ U.conj().T
    
    return rho_iso - rho_adi


def axis2_displace(rho, d):
    """Axis 2 displacement: Eulerian (open) vs Lagrangian (closed).
    Eulerian = trace-decreasing (leak). Lagrangian = trace-preserving.
    """
    # Eulerian: partial trace-decrease (simulate boundary leak)
    P = np.eye(d, dtype=complex)
    P[d-1, d-1] = 0.7  # leak one basis state
    rho_euler = P @ rho @ P.conj().T
    rho_euler /= np.trace(rho_euler)
    
    # Lagrangian: fully trace-preserving unitary
    H = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    H = (H + H.conj().T) / 2
    U = la.expm(-1j * H * 0.5)
    rho_lagr = U @ rho @ U.conj().T
    
    return rho_euler - rho_lagr


def axis3_displace(rho, d):
    """Axis 3 displacement: +G vs −G (generator sign flip).
    
    THIS IS THE CORE AXIS 3 MATH:
      +G: ρ → ρ + G(ρ)·dt
      −G: ρ → ρ − G(ρ)·dt
    Displacement = 2·G(ρ)·dt
    """
    dt = 0.2
    
    # Build a generator G from Lindblad + Hamiltonian
    H = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    H = (H + H.conj().T) / 2  # Hamiltonian part
    
    L = np.zeros((d, d), dtype=complex)
    for k in range(d - 1):
        L[k, k+1] = 0.3  # directed Lindblad jump (chiral)
    
    # G(ρ) = −i[H,ρ] + LρL† − ½{L†L, ρ}
    ham_part = -1j * (H @ rho - rho @ H)
    lind_part = L @ rho @ L.conj().T - 0.5 * (L.conj().T @ L @ rho + rho @ L.conj().T @ L)
    G_rho = ham_part + lind_part
    
    rho_plus = rho + G_rho * dt  # +G
    rho_minus = rho - G_rho * dt  # −G
    
    # Ensure valid
    for r in [rho_plus, rho_minus]:
        r[:] = (r + r.conj().T) / 2
        evals, evecs = np.linalg.eigh(r)
        evals = np.maximum(evals, 0)
        r[:] = evecs @ np.diag(evals) @ evecs.conj().T
        r /= np.trace(r)
    
    return rho_plus - rho_minus


def axis4_displace(rho, d):
    """Axis 4 displacement: Deductive (B∘A) vs Inductive (A∘B).
    Different composition ORDER of the same two maps.
    """
    
    # Map A: dephasing (Ti-like)
    def map_A(r):
        diag = np.diag(np.diag(r))
        return 0.7 * r + 0.3 * diag
    
    # Map B: amplitude damping (Fe-like)
    gamma = 0.2
    K0 = np.eye(d, dtype=complex)
    K1 = np.zeros((d, d), dtype=complex)
    for k in range(1, d):
        K0[k, k] = np.sqrt(1 - gamma)
        K1[k-1, k] = np.sqrt(gamma)
    def map_B(r):
        out = K0 @ r @ K0.conj().T + K1 @ r @ K1.conj().T
        return out / np.trace(out)
    
    rho_ded = map_B(map_A(rho))   # B ∘ A (constraint first)
    rho_ind = map_A(map_B(rho))   # A ∘ B (release first)
    
    return rho_ded - rho_ind


def axis5_displace(rho, d):
    """Axis 5 displacement: FGA (Lindblad) vs FSA (Hamiltonian).
    Different generator ALGEBRA CLASS.
    """
    dt = 0.3
    
    # FGA: Lindblad dissipation
    L = np.zeros((d, d), dtype=complex)
    for k in range(d - 1):
        L[k, k+1] = 0.4
    lind = L @ rho @ L.conj().T - 0.5 * (L.conj().T @ L @ rho + rho @ L.conj().T @ L)
    rho_fga = rho + lind * dt
    rho_fga = (rho_fga + rho_fga.conj().T) / 2
    evals, evecs = np.linalg.eigh(rho_fga)
    evals = np.maximum(evals, 0)
    rho_fga = evecs @ np.diag(evals) @ evecs.conj().T
    rho_fga /= np.trace(rho_fga)
    
    # FSA: Hamiltonian rotation
    H = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    H = (H + H.conj().T) / 2
    U = la.expm(-1j * H * dt)
    rho_fsa = U @ rho @ U.conj().T
    
    return rho_fga - rho_fsa


def axis6_displace(rho, d):
    """Axis 6 displacement: Left action (Aρ) vs Right action (ρA).
    
    THIS IS THE CORE AXIS 6 MATH:
      Left:  ρ → Aρ  (pre-composition)
      Right: ρ → ρA  (post-composition)
    Displacement = Aρ − ρA = [A, ρ]  (commutator!)
    """
    
    # Build a non-Hermitian, non-trivial A
    A = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    A /= np.linalg.norm(A)  # normalize for fair comparison
    
    rho_left = A @ rho    # pre-composition
    rho_right = rho @ A   # post-composition
    
    return rho_left - rho_right  # = [A, ρ]


# ═══════════════════════════════════════════════════════════════════
# ORTHOGONALITY TEST
# ═══════════════════════════════════════════════════════════════════

def hilbert_schmidt_inner(A, B):
    """Tr(A†B)"""
    return np.trace(A.conj().T @ B)


def normalized_overlap(A, B):
    """|Tr(A†B)| / (||A|| · ||B||)"""
    norm_A = np.linalg.norm(A, 'fro')
    norm_B = np.linalg.norm(B, 'fro')
    if norm_A < 1e-12 or norm_B < 1e-12:
        return 0.0
    return float(abs(hilbert_schmidt_inner(A, B)) / (norm_A * norm_B))


def run_anti_conflation_test():
    d_values = [4, 8, 16]
    n_trials = 100
    
    axis_names = ["Ax0_fine/coarse", "Ax1_iso/adi", "Ax2_euler/lagr", 
                  "Ax3_in/out(±G)", "Ax4_ded/ind", "Ax5_FGA/FSA", 
                  "Ax6_pre/post"]
    axis_fns = [axis0_displace, axis1_displace, axis2_displace,
                axis3_displace, axis4_displace, axis5_displace, 
                axis6_displace]
    n_axes = len(axis_fns)
    
    # Danger pairs to highlight
    danger_pairs = [
        (0, 3, "Ax0×Ax3: coarse-graining vs chirality"),
        (3, 6, "Ax3×Ax6: generator sign vs action side"),
        (0, 6, "Ax0×Ax6: coarse-graining vs action side"),
        (3, 4, "Ax3×Ax4: chirality vs loop direction (historical)"),
    ]
    
    print("=" * 70)
    print("AXIS ± DISAMBIGUATION — ANTI-CONFLATION ORTHOGONALITY TEST")
    print("=" * 70)
    print()
    print("Labels (distinct, non-overlapping):")
    print("  Axis 0: fine / coarse")
    print("  Axis 1: open-channel / closed-channel")
    print("  Axis 2: flux / path")
    print("  Axis 3: inward / outward  (±G)")
    print("  Axis 4: constraint-first / release-first")
    print("  Axis 5: gradient / spectral  (FGA/FSA)")
    print("  Axis 6: pre / post  (Aρ/ρA)")
    print()
    
    results = {}
    tokens = []
    all_clean = True
    
    for d in d_values:
        print(f"\n{'─'*70}")
        print(f"  d = {d}")
        print(f"{'─'*70}")
        
        overlap_matrix = np.zeros((n_axes, n_axes))
        
        for trial in range(n_trials):
            seed = 1000*d + trial
            np.random.seed(seed)
            rho = make_random_density_matrix(d)
            displacements = []
            for fn in axis_fns:
                np.random.seed(seed)  # reset per axis for fairness
                disp = fn(rho, d)
                displacements.append(disp)
            
            for i in range(n_axes):
                for j in range(i+1, n_axes):
                    ov = normalized_overlap(displacements[i], displacements[j])
                    overlap_matrix[i, j] += ov
                    overlap_matrix[j, i] += ov
        
        overlap_matrix /= n_trials
        
        # Print full matrix
        print(f"\n  Pairwise overlap matrix (avg over {n_trials} trials):")
        header = "        " + "  ".join(f"Ax{i}" for i in range(n_axes))
        print(header)
        for i in range(n_axes):
            row = f"  Ax{i}:  "
            for j in range(n_axes):
                if i == j:
                    row += "  --- "
                else:
                    val = overlap_matrix[i, j]
                    marker = " !" if val > 0.1 else "  "
                    row += f"{val:.3f}{marker}"
            print(row)
        
        # Check danger pairs
        print(f"\n  DANGER PAIR CHECK:")
        d_key = f"d={d}"
        results[d_key] = {}
        
        for i, j, label in danger_pairs:
            ov = overlap_matrix[i, j]
            status = "✅ ORTHOGONAL" if ov < 0.05 else ("⚠️ MARGINAL" if ov < 0.15 else "❌ CONFLATING")
            print(f"    {label}: overlap = {ov:.4f}  {status}")
            results[d_key][f"ax{i}_ax{j}"] = float(ov)
            if ov > 0.15:
                all_clean = False
    
    # Evidence tokens
    if all_clean:
        print(f"\n{'='*70}")
        print("  PASS: All danger pairs are orthogonal across all dimensions.")
        print(f"{'='*70}")
        tokens.append(EvidenceToken(
            token_id="E_SIM_AXIS_ANTI_CONFLATION_OK",
            sim_spec_id="S_SIM_AXIS_DISAMBIGUATION_V1",
            status="PASS",
            measured_value=max(
                max(results[k].values()) for k in results
            )
        ))
    else:
        print(f"\n{'='*70}")
        print("  KILL: Some danger pairs show conflation!")
        print(f"{'='*70}")
        tokens.append(EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_AXIS_DISAMBIGUATION_V1",
            status="KILL",
            kill_reason="AXIS_CONFLATION_DETECTED",
            measured_value=max(
                max(results[k].values()) for k in results
            )
        ))
    
    # Save results
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "axis_anti_conflation_results.json")
    
    output = {
        "schema": "SIM_EVIDENCE_v1",
        "file": os.path.basename(__file__),
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "evidence_ledger": [dataclasses.asdict(t) for t in tokens],
        "label_disambiguation": {
            "axis_0": {"plus": "fine", "minus": "coarse", "math": "fiber_average_level"},
            "axis_1": {"plus": "open-channel (CPTP)", "minus": "closed-channel (Unitary)", "math": "channel_class"},
            "axis_2": {"plus": "flux (Eulerian)", "minus": "path (Lagrangian)", "math": "boundary_condition"},
            "axis_3": {"plus": "inward (+G, Left Weyl, CW)", "minus": "outward (-G, Right Weyl, CCW)", "math": "generator_sign"},
            "axis_4": {"plus": "constraint-first (B∘A)", "minus": "release-first (A∘B)", "math": "composition_order"},
            "axis_5": {"plus": "gradient (FGA, Lindblad)", "minus": "spectral (FSA, Hamiltonian)", "math": "algebra_class"},
            "axis_6": {"plus": "pre (Aρ)", "minus": "post (ρA)", "math": "action_side"},
        },
        "danger_pairs": {
            "ax0_ax3": "coarse-graining vs chirality (both affect purity)",
            "ax3_ax6": "generator sign vs action side (both called 'left/right')",
            "ax0_ax6": "coarse-graining vs action side",
            "ax3_ax4": "chirality vs loop direction (historical conflation)",
        },
        "overlap_results": results,
    }
    
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    run_anti_conflation_test()
