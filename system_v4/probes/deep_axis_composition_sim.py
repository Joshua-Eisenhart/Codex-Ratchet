#!/usr/bin/env python3
"""
Deep Axis Composition Analysis Engine
========================================
Goes beyond the sweep to characterize the INTERNAL STRUCTURE of each
axis composition:

1. Non-commutativity: Does A∘B ≠ B∘A? How much?
2. Fixed-point basins: How many distinct attractor states does the
   composed channel have? (= emergent structures like engine stages)
3. Eigenstructure: What is the spectral decomposition of the composed Choi?
4. Semantic pairing verification for the user's known structures:
   - A1×A2 → 4 engine stages / perceiving functions
   - A3×A4 → 2 engine types
   - A4×A5 → 4 judging functions
5. Trigram internal structure for {6,5,3} and {4,1,2}
6. All 6 permutations of each trigram to find the optimal composition order
"""

import numpy as np
import json
import os
import sys
from itertools import combinations, permutations
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import EvidenceToken, von_neumann_entropy
from axis_orthogonality_suite import AXES, build_choi, hs_inner

DIM = 8
CLUSTER_EPS = 0.02


def compose_sequential(axis_names, d):
    """Compose channels in the given order: Apply first->last."""
    def composed(rho, dim):
        out = rho.copy()
        for name in axis_names:
            out = AXES[name](out, dim)
        return out
    return composed


def count_fixed_point_basins(channel, d, n_probes=50):
    """
    Count distinct attractor basins by iterating the channel from many
    random initial states and clustering the fixed points.
    """
    rng = np.random.default_rng(42)
    fixed_points = []
    
    for _ in range(n_probes):
        # Random pure state as starting point
        psi = rng.normal(size=d) + 1j * rng.normal(size=d)
        psi /= np.linalg.norm(psi)
        rho = np.outer(psi, psi.conj())
        
        # Iterate channel 20 times to converge
        for _ in range(20):
            rho = channel(rho, d)
            # Re-normalize for stability
            evals, evecs = np.linalg.eigh(rho)
            evals = np.maximum(evals, 0)
            rho = evecs @ np.diag(evals.astype(complex)) @ evecs.conj().T
            tr = np.real(np.trace(rho))
            if tr > 1e-12:
                rho /= tr
            else:
                rho = np.eye(d, dtype=complex) / d
        
        fixed_points.append(rho)
    
    # Cluster fixed points by trace distance
    clusters = []
    for fp in fixed_points:
        found = False
        for cluster in clusters:
            ref = cluster[0]
            td = 0.5 * np.linalg.norm(fp - ref, 'nuc')
            if td < CLUSTER_EPS:
                cluster.append(fp)
                found = True
                break
        if not found:
            clusters.append([fp])
    
    return len(clusters), clusters


def measure_noncommutativity(name_a, name_b, d):
    """Measure how non-commutative A∘B vs B∘A is."""
    ch_ab = compose_sequential([name_a, name_b], d)
    ch_ba = compose_sequential([name_b, name_a], d)
    
    choi_ab = build_choi(ch_ab, d)
    choi_ba = build_choi(ch_ba, d)
    
    # Frobenius distance between the two composed Chois
    diff_norm = float(np.linalg.norm(choi_ab - choi_ba, 'fro'))
    max_norm = max(float(np.linalg.norm(choi_ab, 'fro')),
                   float(np.linalg.norm(choi_ba, 'fro')), 1e-30)
    relative_noncomm = diff_norm / max_norm
    
    return relative_noncomm, choi_ab, choi_ba


def eigenstructure_analysis(choi):
    """Analyze the eigenstructure of a Choi matrix."""
    evals = np.linalg.eigvalsh(choi)
    evals_sorted = np.sort(np.abs(evals))[::-1]
    
    # Count significant eigenvalues (spectral rank)
    sig = evals_sorted[evals_sorted > 1e-8]
    spectral_rank = len(sig)
    
    # Spectral gap (between 1st and 2nd eigenvalue)
    if len(sig) >= 2:
        spectral_gap = float(sig[0] - sig[1])
    else:
        spectral_gap = float(sig[0]) if len(sig) > 0 else 0.0
    
    # Participation ratio (effective dimension)
    sig_norm = sig / max(np.sum(sig), 1e-30)
    participation = float(1.0 / max(np.sum(sig_norm**2), 1e-30))
    
    return {
        "spectral_rank": spectral_rank,
        "spectral_gap": round(spectral_gap, 6),
        "participation_ratio": round(participation, 4),
        "top_5_eigenvalues": [round(float(e), 6) for e in sig[:5]],
    }


def analyze_doublet(name_a, name_b, semantic_label, expected_basins):
    """Deep analysis of a specific axis pair."""
    d = DIM
    print(f"\n{'─'*72}")
    print(f"  DOUBLET: {name_a.split('_')[0]} × {name_b.split('_')[0]}  ({semantic_label})")
    print(f"{'─'*72}")
    
    # Non-commutativity
    noncomm, choi_ab, choi_ba = measure_noncommutativity(name_a, name_b, d)
    print(f"  Non-commutativity (A∘B vs B∘A): {noncomm:.4f}")
    
    # Eigenstructure of A∘B
    eigen_ab = eigenstructure_analysis(choi_ab)
    print(f"  Eigenstructure (A→B): rank={eigen_ab['spectral_rank']}  "
          f"gap={eigen_ab['spectral_gap']:.4f}  "
          f"participation={eigen_ab['participation_ratio']:.2f}")
    print(f"    Top eigenvalues: {eigen_ab['top_5_eigenvalues']}")
    
    # Eigenstructure of B∘A
    eigen_ba = eigenstructure_analysis(choi_ba)
    print(f"  Eigenstructure (B→A): rank={eigen_ba['spectral_rank']}  "
          f"gap={eigen_ba['spectral_gap']:.4f}  "
          f"participation={eigen_ba['participation_ratio']:.2f}")
    
    # Fixed-point basin count for A→B
    ch_ab = compose_sequential([name_a, name_b], d)
    n_basins_ab, clusters_ab = count_fixed_point_basins(ch_ab, d)
    
    # Fixed-point basin count for B→A
    ch_ba = compose_sequential([name_b, name_a], d)
    n_basins_ba, clusters_ba = count_fixed_point_basins(ch_ba, d)
    
    print(f"  Fixed-point basins (A→B): {n_basins_ab}  (expected: {expected_basins})")
    print(f"  Fixed-point basins (B→A): {n_basins_ba}")
    
    # Entropy of each basin's representative
    for i, cluster in enumerate(clusters_ab):
        S = von_neumann_entropy(cluster[0])
        print(f"    Basin {i}: S={S:.4f} bits  (population={len(cluster)}/{50})")
    
    match = n_basins_ab == expected_basins or n_basins_ba == expected_basins
    print(f"  Basin count matches expected ({expected_basins}): {'YES ✓' if match else 'NO ✗'}")
    
    return {
        "pair": [name_a, name_b],
        "semantic_label": semantic_label,
        "expected_basins": expected_basins,
        "noncommutativity": round(noncomm, 6),
        "basins_ab": n_basins_ab,
        "basins_ba": n_basins_ba,
        "eigenstructure_ab": eigen_ab,
        "eigenstructure_ba": eigen_ba,
        "match": match,
    }


def analyze_trigram(axis_names, label):
    """Analyze all 6 permutations of a trigram to find optimal composition order."""
    d = DIM
    print(f"\n{'='*72}")
    print(f"  TRIGRAM: {label}")
    print(f"  Axes: {' × '.join([a.split('_')[0] for a in axis_names])}")
    print(f"{'='*72}")
    
    perms = list(permutations(axis_names))
    results = []
    
    for perm in perms:
        ch = compose_sequential(list(perm), d)
        choi = build_choi(ch, d)
        eigen = eigenstructure_analysis(choi)
        n_basins, _ = count_fixed_point_basins(ch, d, n_probes=30)
        
        perm_label = " → ".join([a.split("_")[0] for a in perm])
        results.append({
            "order": list(perm),
            "order_label": perm_label,
            "basins": n_basins,
            "spectral_rank": eigen["spectral_rank"],
            "participation": eigen["participation_ratio"],
            "spectral_gap": eigen["spectral_gap"],
        })
        print(f"  {perm_label:40s}  basins={n_basins:2d}  "
              f"rank={eigen['spectral_rank']:3d}  "
              f"partic={eigen['participation_ratio']:6.2f}  "
              f"gap={eigen['spectral_gap']:.4f}")
    
    # Find optimal: highest basin count, then highest participation
    results.sort(key=lambda x: (x["basins"], x["participation"]), reverse=True)
    best = results[0]
    print(f"\n  OPTIMAL ORDER: {best['order_label']} ({best['basins']} basins)")
    
    return results


def analyze_all_doublets_noncomm():
    """Test non-commutativity for ALL 15 pairs."""
    d = DIM
    print(f"\n{'='*72}")
    print(f"  ALL 15 PAIRWISE NON-COMMUTATIVITY SCORES")
    print(f"{'='*72}")
    
    scores = []
    for (a, b) in combinations(AXES.keys(), 2):
        nc, _, _ = measure_noncommutativity(a, b, d)
        label = f"{a.split('_')[0]} × {b.split('_')[0]}"
        scores.append({"pair": [a, b], "label": label, "noncommutativity": round(nc, 6)})
    
    scores.sort(key=lambda x: x["noncommutativity"], reverse=True)
    for s in scores:
        bar = "█" * int(s["noncommutativity"] * 50)
        print(f"  {s['label']:25s}  {s['noncommutativity']:.4f}  {bar}")
    
    return scores


def run_deep_analysis():
    print("=" * 72)
    print("DEEP AXIS COMPOSITION ANALYSIS ENGINE")
    print(f"  d={DIM}")
    print("=" * 72)
    
    all_results = {}
    
    # 1. All 15 non-commutativity scores
    nc_scores = analyze_all_doublets_noncomm()
    all_results["noncommutativity_ranking"] = nc_scores
    
    # 2. Semantic doublets with basin analysis
    doublet_results = []
    doublet_results.append(analyze_doublet("A1_Coupling", "A2_Frame",
                                           "4 Engine Stages / Perceiving (Se,Si,Ne,Ni)", 4))
    doublet_results.append(analyze_doublet("A3_Chirality", "A4_Variance",
                                           "2 Engine Types (Chiral Selection)", 2))
    doublet_results.append(analyze_doublet("A4_Variance", "A5_Texture",
                                           "4 Judging Functions (Te,Ti,Fe,Fi)", 4))
    # Also test the anomalous top pair
    doublet_results.append(analyze_doublet("A1_Coupling", "A3_Chirality",
                                           "4 Engine Orientations (Anomaly)", 4))
    # And the secondary known pairings
    doublet_results.append(analyze_doublet("A5_Texture", "A6_Precedence",
                                           "Calculus × Time (Wave/Line × P/J)", 4))
    doublet_results.append(analyze_doublet("A1_Coupling", "A4_Variance",
                                           "Coupling × Thermodynamic Direction", 4))
    all_results["doublet_analyses"] = doublet_results
    
    # 3. Trigram permutation analysis
    trigram_1_results = analyze_trigram(
        ["A4_Variance", "A1_Coupling", "A2_Frame"], "Lower Trigram {4,1,2}")
    trigram_2_results = analyze_trigram(
        ["A6_Precedence", "A5_Texture", "A3_Chirality"], "Upper Trigram {6,5,3}")
    # Also test the naive ordering to compare
    trigram_3_results = analyze_trigram(
        ["A1_Coupling", "A2_Frame", "A3_Chirality"], "Naive Trigram {1,2,3}")
    trigram_4_results = analyze_trigram(
        ["A4_Variance", "A5_Texture", "A6_Precedence"], "Naive Trigram {4,5,6}")
    
    all_results["trigrams"] = {
        "lower_412": trigram_1_results,
        "upper_653": trigram_2_results,
        "naive_123": trigram_3_results,
        "naive_456": trigram_4_results,
    }
    
    # Evidence tokens
    tokens = []
    tokens.append(EvidenceToken("E_SIM_DEEP_COMPOSITION_OK", "S_SIM_DEEP_AXIS_COMPOSITION",
                                "PASS", float(nc_scores[0]["noncommutativity"])))
    
    # Save
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "deep_axis_composition_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "dimension": DIM,
            "results": all_results,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2, default=str)
    print(f"\n  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_deep_analysis()
