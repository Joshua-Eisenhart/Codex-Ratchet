#!/usr/bin/env python3
"""
CANONICAL AXIS TRIPLET ORTHOGONALITY SUITE C(6,3)
=================================================
Tests combinatorial triplets (A ∘ B ⊥ C) for non-linear synthetic conflation.
Ensures that composing two axes geometrically does not unintentionally build
a matrix representation that is collinear with any third axis.

Axes:
    A1: Coupling Regime
    A2: Frame Representation
    A3: Chiral Flux
    A4: Variance Direction
    A5: Generator Algebra
    A6: Action Precedence

Tests 60 permutations (20 groupings * 3 targets, assuming symmetric composition representation)
against the normalized Hilbert-Schmidt inner product.
"""

import numpy as np
import json
import os
import sys
from itertools import combinations, permutations
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from axis_orthogonality_suite import (
    AXES, build_choi, hs_inner, EPS, DIMS, make_hermitian, make_unitary_from_H, make_fourier
)
from proto_ratchet_sim_runner import EvidenceToken


def random_density_matrix(d):
    """Generates a Haar-random positive semi-definite trace-1 matrix."""
    G = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    rho = G @ G.conj().T
    return rho / np.trace(rho)

def measure_overlap(channel_AB, channel_C, d, samples=50):
    """Measures average Hilbert-Schmidt inner product over valid density matrices."""
    overlaps = []
    for _ in range(samples):
        rho = random_density_matrix(d)
        out_AB = channel_AB(rho, d)
        out_C = channel_C(rho, d)
        ov = hs_inner(out_AB, out_C)
        overlaps.append(ov)
    return np.mean(overlaps)

def run_triplet_suite():
    print(f"\n{'='*70}")
    print("AXIS TRIPLET ORTHOGONALITY SUITE (C(6,3))")
    print(f"{'='*70}")

    tokens = []
    triplet_results = []
    
    d = 8
    print(f"Dimension: {d}x{d} (Monte Carlo Expectation)")
    
    kills = 0
    passes = 0
    
    total_groupings = list(combinations(AXES.keys(), 3))
    
    for group in total_groupings:
        for A_name, B_name, C_name in [
            (group[0], group[1], group[2]),
            (group[0], group[2], group[1]),
            (group[1], group[2], group[0])
        ]:
            A_func = AXES[A_name]
            B_func = AXES[B_name]
            C_func = AXES[C_name]
            
            # Composite channel: A(B(rho))
            channel_AB = lambda r, dim: A_func(B_func(r, dim), dim)
            
            overlap = measure_overlap(channel_AB, C_func, d)
            status = "PASS" if abs(overlap) < EPS else "KILL"
            
            if status == "PASS": passes += 1
            else: kills += 1
                
            res_str = f"({A_name} ∘ {B_name}) ⊥ {C_name}"
            print(f"  {res_str:60s}: {overlap:+.3e} [{status}]")
            
            triplet_results.append({
                "triplet": [A_name, B_name, C_name],
                "operation": f"({A_name} ∘ {B_name}) ⊥ {C_name}",
                "overlap": float(overlap),
                "status": status
            })

    print(f"\n{'='*70}")
    print(f"TRIPLET SUITE COMPLETE: {passes} PASS, {kills} KILL")
    print(f"{'='*70}")
    
    if kills == 0:
        tokens.append(EvidenceToken(
            token_id="E_TRIPLET_ORTHO_OK",
            sim_spec_id="S_TRIPLET_ORTHO_V1",
            status="PASS",
            measured_value=1.0
        ))
    else:
        tokens.append(EvidenceToken(
            token_id="",
            sim_spec_id="S_TRIPLET_ORTHO_V1",
            status="KILL",
            measured_value=0.0,
            kill_reason=f"SYNTHETIC_CONFLATION_{kills}_TRIPLETS"
        ))
        
    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "axis_triplet_orthogonality_results.json"
    )
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    
    with open(out_file, "w") as f:
        json.dump({
            "schema": "SIM_EVIDENCE_v1",
            "file": "axis_triplet_orthogonality_suite.py",
            "timestamp": datetime.now(UTC).isoformat() + "Z",
            "evidence_ledger": [t.__dict__ for t in tokens],
            "measurements": triplet_results
        }, f, indent=2)

    return tokens

if __name__ == "__main__":
    run_triplet_suite()
