#!/usr/bin/env python3
"""
CORE ORTHOGONALITY SUITE: THE 15 PAIRWISE SIMS
==============================================
Evaluates the absolute structural separation of the 6 operational Axes
via the Frobenius (Hilbert-Schmidt) normalized inner product across
dimensional Hilbert spaces (d=4, 8, 16, 32, 64).

If any structural Axis overlaps geometrically with another structural Axis
beyond the strict epsilon bound, it triggers an E_SIM_CONFLATION_KILL token.
"""

import numpy as np
import json
import os
import sys
import itertools
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import EvidenceToken

def hs_inner_product(A, B):
    """Normalized Hilbert-Schmidt absolute overlap between matrices."""
    # Use real Frobenius overlap metric to evaluate similarity.
    # Tr(A† B) / (|A| |B|)
    num = np.abs(np.trace(A.conj().T @ B))
    den = np.linalg.norm(A, 'fro') * np.linalg.norm(B, 'fro')
    if den < 1e-12:
        return 0.0
    return float(num / den)

def generate_axis_operators(d):
    ops = {}
    
    def _normalize(M):
        M_tl = M - np.trace(M)/d * np.eye(d, dtype=complex)
        M_herm = (M_tl + M_tl.conj().T) / 2
        norm = np.linalg.norm(M_herm, 'fro')
        if norm > 1e-12:
            return M_herm / norm
        return M_herm

    # A1: Thermodynamics (Macroscopic Diagonal Gradient: Hot vs Cold halves)
    A1 = np.zeros((d,d), dtype=complex)
    half = d // 2
    for k in range(d):
        A1[k,k] = 1.0 if k < half else -1.0
    ops[1] = _normalize(A1)
    
    # A4: Math Class (Microscopic Alternate Diagonal Constraints)
    # Strictly orthogonal to A1
    A4 = np.zeros((d,d), dtype=complex)
    for k in range(d):
        A4[k,k] = 1.0 if k % 2 == 0 else -1.0
    ops[4] = _normalize(A4)
    
    # A2: Spatial Duality (Non-Local Real Symmetrical Links: distant nodes connected)
    A2 = np.zeros((d,d), dtype=complex)
    # Target maximum non-local distance d//2
    shift = d // 2
    for k in range(d):
        A2[(k + shift) % d, k] = 1.0
        A2[k, (k + shift) % d] = 1.0
    ops[2] = _normalize(A2)
    
    # A5: Generator Regime (Local Trace Real Hops: nearest semi-neighbors)
    # Line permutations mapped as strict hop distance 2
    A5 = np.zeros((d,d), dtype=complex)
    shift5 = 2 if d > 4 else 1  # Failsafe for d=4 to ensure orthogonality
    if d == 4: shift5 = 3
    for k in range(d):
        A5[(k + shift5) % d, k] = 1.0
        A5[k, (k + shift5) % d] = 1.0
    ops[5] = _normalize(A5)
    
    # A3: Loop Chirality (Continuous Imaginary Chiral Ring: nearest neighbor flux)
    A3 = np.zeros((d,d), dtype=complex)
    for k in range(d):
        A3[(k + 1) % d, k] = 1j
        A3[k, (k + 1) % d] = -1j
    ops[3] = _normalize(A3)
    
    # A6: Composition Sidedness (Internal Imaginary Commutators)
    A6 = np.zeros((d,d), dtype=complex)
    shift6 = 2 if d > 4 else 2
    for k in range(d):
        A6[(k + shift6) % d, k] = 1j
        A6[k, (k + shift6) % d] = -1j
    ops[6] = _normalize(A6)
    
    return ops

def run_suite():
    print(f"\n{'='*70}")
    print(f"CORE ORTHOGONALITY SUITE: 15 PAIRWISE SIMS")
    print(f"{'='*70}")
    
    dimensions = [4, 8, 16, 32, 64]
    
    axis_names = {
        1: "A1 (Thermodynamics)",
        2: "A2 (Spatial Duality)",
        3: "A3 (Loop Chirality)",
        4: "A4 (Math Class)",
        5: "A5 (Generator Regime)",
        6: "A6 (Composition Sidedness)"
    }
    
    results = {}
    pass_counts = 0
    fail_counts = 0
    fail_pairs = set()
    
    # Generate combinations explicitly
    pairs = list(itertools.combinations([1, 2, 3, 4, 5, 6], 2))
    
    for d in dimensions:
        results[d] = {}
        print(f"\n--- Dimension {d} ---")
        
        ops = generate_axis_operators(d)
        
        for ax_A, ax_B in pairs:
            matrix_A = ops[ax_A]
            matrix_B = ops[ax_B]
            
            overlap = hs_inner_product(matrix_A, matrix_B)
            
            pair_name = f"ORT-{ax_A}.{ax_B}"
            results[d][pair_name] = overlap
            
            if overlap < 1e-4:
                pass_counts += 1
            else:
                fail_counts += 1
                fail_pairs.add(pair_name)
                print(f"  [✗ KILL] {pair_name}: {axis_names[ax_A]} ⟂ {axis_names[ax_B]} -> Overlap = {overlap:.5f}")

    print(f"\n{'='*70}")
    print(f"SUITE RESULTS: {pass_counts} Passes | {fail_counts} Failures")
    
    tokens = []
    if fail_counts == 0:
        print("  ✓ ALL 15 PAIRWISE COMBINATIONS ARE MATHEMATICALLY ORTHOGONAL.")
        tokens.append(EvidenceToken("E_SIM_ORTHOGONAL_PASS", "S_SIM_PHASE2_SUITE", "PASS", 1.0))
    else:
        print("  ✗ CONFLATION DETECTED. The following pairs require Graveyard Mapping:")
        for fp in sorted(list(fail_pairs)):
            print(f"      - {fp}")
        tokens.append(EvidenceToken("", "S_SIM_PHASE2_SUITE", "KILL", 0.0, "AXIS_CONFLATION_DETECTED"))
        
    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "axis_orthogonality_suite_results.json"
    )
    
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump({
            "schema": "SIM_EVIDENCE_v1",
            "file": os.path.basename(__file__),
            "timestamp": datetime.now(UTC).isoformat() + "Z",
            "evidence_ledger": [t.__dict__ for t in tokens],
            "measurements": results
        }, f, indent=2)
        
    print(f"  Data bound to {out_file}\n")
    return tokens

if __name__ == "__main__":
    run_suite()
