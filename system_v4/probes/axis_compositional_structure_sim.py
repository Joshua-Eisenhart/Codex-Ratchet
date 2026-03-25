#!/usr/bin/env python3
"""
Axis Compositional Structure Discovery SIM
============================================
Exhaustive sweep of ALL k-tuples (k=2..6) of axes 1-6 plus Axis-0 moderator.
For each combination, measures:
  1. Compositional overlap (Hilbert-Schmidt inner product of composed channels)
  2. Spectral complexity (number of distinct eigenvalue clusters of the composed Choi)
  3. Algebraic closure (does composing members stay within the span?)
  4. Structural rank of the composed operator family

The natural ordering 0→6→5→3→4→1→2 is tested explicitly.

Output: Ranked table of ALL n-tuples by emergent structural significance.
"""

import numpy as np
import json
import os
import sys
from itertools import combinations
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import EvidenceToken
from axis_orthogonality_suite import AXES, build_choi, hs_inner

# ── CONFIGURATION ──
DIM = 8  # Working dimension (balance speed vs resolution)
CLUSTER_EPS = 0.05  # Eigenvalue clustering threshold

# ── AXIS LABELS in natural build order ──
NATURAL_ORDER = ["A6_Precedence", "A5_Texture", "A3_Chirality", "A4_Variance", "A1_Coupling", "A2_Frame"]
NUMERIC_ORDER = ["A1_Coupling", "A2_Frame", "A3_Chirality", "A4_Variance", "A5_Texture", "A6_Precedence"]

# ── KNOWN SEMANTIC PAIRINGS ──
KNOWN_PAIRINGS = {
    ("A1_Coupling", "A2_Frame"): "4 Engine Stages / Perceiving Functions (Se,Si,Ne,Ni)",
    ("A3_Chirality", "A4_Variance"): "2 Engine Types (Chiral Selection)",
    ("A4_Variance", "A5_Texture"): "4 Judging Functions (Te,Ti,Fe,Fi)",
}
KNOWN_TRIGRAMS = {
    ("A3_Chirality", "A5_Texture", "A6_Precedence"): "Upper Trigram {3,5,6}",
    ("A1_Coupling", "A2_Frame", "A4_Variance"): "Lower Trigram {1,2,4}",
}


def compose_channels(axis_names, d):
    """Compose multiple axis channels sequentially: A_n ∘ ... ∘ A_2 ∘ A_1."""
    def composed(rho, dim):
        out = rho.copy()
        for name in axis_names:
            out = AXES[name](out, dim)
        return out
    return composed


def spectral_clusters(matrix, eps=CLUSTER_EPS):
    """Count distinct eigenvalue clusters in a matrix."""
    evals = np.sort(np.abs(np.linalg.eigvals(matrix)))
    if len(evals) == 0:
        return 0
    clusters = 1
    for i in range(1, len(evals)):
        if abs(evals[i] - evals[i-1]) > eps:
            clusters += 1
    return clusters


def measure_algebraic_closure(axis_names, d):
    """
    Measure how 'closed' a set of axes is under composition.
    Build Choi matrices for each axis and for all pairwise compositions.
    Check if pairwise compositions lie within the span of the individual Chois.
    Returns the residual norm (0 = perfectly closed).
    """
    individual_chois = [build_choi(AXES[name], d) for name in axis_names]
    flat_basis = np.stack([c.flatten() for c in individual_chois], axis=0)  # k x d^4
    
    # For each pairwise composition A_i ∘ A_j, project onto the span
    residuals = []
    for i in range(len(axis_names)):
        for j in range(len(axis_names)):
            if i == j:
                continue
            composed = compose_channels([axis_names[i], axis_names[j]], d)
            choi_composed = build_choi(composed, d).flatten()
            
            # Project onto span of individual Chois (least squares)
            coeffs, res, _, _ = np.linalg.lstsq(flat_basis.T, choi_composed, rcond=None)
            projection = flat_basis.T @ coeffs
            residual = np.linalg.norm(choi_composed - projection) / max(np.linalg.norm(choi_composed), 1e-30)
            residuals.append(residual)
    
    return float(np.mean(residuals)) if residuals else 1.0


def analyze_combination(axis_names, d):
    """Full analysis of a single axis combination."""
    k = len(axis_names)
    
    # 1. Build composed channel and its Choi
    composed = compose_channels(list(axis_names), d)
    choi_composed = build_choi(composed, d)
    
    # 2. Spectral complexity of the composed Choi
    n_clusters = spectral_clusters(choi_composed)
    
    # 3. Choi rank (structural degrees of freedom)
    sing_vals = np.linalg.svd(choi_composed, compute_uv=False)
    rank = int(np.sum(sing_vals > 1e-8))
    
    # 4. Von Neumann entropy of the composed channel's effect on maximally mixed state
    rho_test = np.eye(d, dtype=complex) / d
    rho_out = composed(rho_test, d)
    evals = np.linalg.eigvalsh(rho_out)
    evals = evals[evals > 1e-15]
    vn_entropy = float(-np.sum(evals * np.log2(evals))) if len(evals) > 0 else 0.0
    
    # 5. Pairwise overlaps within the group
    individual_chois = [build_choi(AXES[name], d) for name in axis_names]
    overlaps = []
    for i in range(k):
        for j in range(i+1, k):
            overlaps.append(float(hs_inner(individual_chois[i], individual_chois[j])))
    mean_overlap = float(np.mean(overlaps)) if overlaps else 0.0
    max_overlap = float(np.max(overlaps)) if overlaps else 0.0
    
    # 6. Algebraic closure (only for k >= 2)
    closure_residual = measure_algebraic_closure(list(axis_names), d) if k >= 2 else 0.0
    
    # 7. Structural significance score
    # Higher = more structurally interesting
    # Rewards: high spectral complexity, high rank, low closure residual (= closed algebra)
    # Also rewards meaningful overlap (not zero, not one)
    overlap_interest = 4.0 * mean_overlap * (1.0 - mean_overlap)  # Peaks at 0.5
    significance = (n_clusters / d**2) * 10 + (rank / d**2) * 5 + (1.0 - closure_residual) * 3 + overlap_interest * 2
    
    # Check if this is a known semantic pairing
    key = tuple(sorted(axis_names))
    semantic_label = ""
    if key in KNOWN_PAIRINGS:
        semantic_label = KNOWN_PAIRINGS[key]
    if key in KNOWN_TRIGRAMS:
        semantic_label = KNOWN_TRIGRAMS[key]
    
    return {
        "axes": list(axis_names),
        "k": k,
        "spectral_clusters": n_clusters,
        "choi_rank": rank,
        "vn_entropy": round(vn_entropy, 6),
        "mean_pairwise_overlap": round(mean_overlap, 6),
        "max_pairwise_overlap": round(max_overlap, 6),
        "closure_residual": round(closure_residual, 6),
        "significance_score": round(significance, 4),
        "semantic_label": semantic_label,
    }


def test_natural_ordering(d):
    """Test if the natural ordering 0→6→5→3→4→1→2 produces monotonically increasing complexity."""
    print(f"\n{'='*72}")
    print(f"NATURAL ORDERING TEST: 6→5→3→4→1→2 (d={d})")
    print(f"{'='*72}")
    
    complexities = []
    for i in range(1, len(NATURAL_ORDER)+1):
        prefix = NATURAL_ORDER[:i]
        composed = compose_channels(prefix, d)
        choi = build_choi(composed, d)
        n_clusters = spectral_clusters(choi)
        rank = int(np.sum(np.linalg.svd(choi, compute_uv=False) > 1e-8))
        
        label = " → ".join([a.split("_")[0] for a in prefix])
        print(f"  {label:50s}  clusters={n_clusters:3d}  rank={rank:3d}")
        complexities.append({"prefix": [a for a in prefix], "clusters": n_clusters, "rank": rank})
    
    # Check monotonicity
    ranks = [c["rank"] for c in complexities]
    monotonic = all(ranks[i] >= ranks[i-1] for i in range(1, len(ranks)))
    print(f"\n  Monotonically increasing rank: {'YES ✓' if monotonic else 'NO ✗'}")
    
    return complexities, monotonic


def run_full_sweep():
    d = DIM
    all_axis_names = list(AXES.keys())
    all_results = []
    
    print("=" * 72)
    print("AXIS COMPOSITIONAL STRUCTURE DISCOVERY")
    print(f"  d={d}  axes={len(all_axis_names)}  sweeping k=2..{len(all_axis_names)}")
    print("=" * 72)
    
    # Sweep all k-tuples for k=2..6
    for k in range(2, len(all_axis_names) + 1):
        combos = list(combinations(all_axis_names, k))
        print(f"\n--- k={k}: {len(combos)} combinations ---")
        
        for combo in combos:
            result = analyze_combination(combo, d)
            all_results.append(result)
            
            # Print significant ones
            label = " × ".join([a.split("_")[0] for a in combo])
            sem = f" [{result['semantic_label']}]" if result['semantic_label'] else ""
            print(f"  {label:45s} sig={result['significance_score']:6.2f}  "
                  f"clusters={result['spectral_clusters']:3d}  "
                  f"rank={result['choi_rank']:3d}  "
                  f"closure={result['closure_residual']:.4f}{sem}")
    
    # Sort by significance
    all_results.sort(key=lambda x: x["significance_score"], reverse=True)
    
    # Print ranked summary
    print(f"\n{'='*72}")
    print("TOP 20 MOST STRUCTURALLY SIGNIFICANT AXIS COMBINATIONS")
    print(f"{'='*72}")
    for i, r in enumerate(all_results[:20]):
        label = " × ".join([a.split("_")[0] for a in r["axes"]])
        sem = f" [{r['semantic_label']}]" if r['semantic_label'] else ""
        print(f"  #{i+1:2d} (k={r['k']}) {label:40s} sig={r['significance_score']:6.2f}  "
              f"clusters={r['spectral_clusters']:3d}  rank={r['choi_rank']:3d}  "
              f"overlap={r['mean_pairwise_overlap']:.4f}  closure={r['closure_residual']:.4f}{sem}")
    
    # Natural ordering test
    ordering_results, monotonic = test_natural_ordering(d)
    
    # Evidence tokens
    tokens = []
    tokens.append(EvidenceToken(
        "E_SIM_COMPOSITIONAL_SWEEP_OK", "S_SIM_AXIS_COMPOSITIONAL_SWEEP",
        "PASS", float(all_results[0]["significance_score"])
    ))
    
    if monotonic:
        tokens.append(EvidenceToken(
            "E_SIM_NATURAL_ORDER_MONOTONIC_OK", "S_SIM_NATURAL_ORDER_MONOTONIC",
            "PASS", 1.0
        ))
    else:
        tokens.append(EvidenceToken(
            "", "S_SIM_NATURAL_ORDER_MONOTONIC",
            "KILL", 0.0, "NON_MONOTONIC_COMPLEXITY"
        ))
    
    # Save results
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "axis_compositional_structure_results.json")
    
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "dimension": d,
            "total_combinations_tested": len(all_results),
            "ranked_results": all_results,
            "natural_ordering_test": {
                "order": NATURAL_ORDER,
                "results": ordering_results,
                "monotonic": monotonic,
            },
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2)
    
    print(f"\n  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_full_sweep()
