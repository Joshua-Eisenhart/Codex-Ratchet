#!/usr/bin/env python3
"""
Abiogenesis v2 SIM
====================
Falsifiable thesis: "Life" (negentropic maintenance) requires a **chiral** 
(asymmetric) coupling of the underlying operator geometry. Symmetric engines 
produce maximum entropy (heat death).

Method: Compare the entropy production of a chiral engine (A3 then A1) vs
a symmetrized engine (A1 + A1^T)/2 over 50 iterations from random state.

PASS: Chiral engine maintains lower average von Neumann entropy.
KILL: Symmetrical engine has equal or lower entropy.
"""

import numpy as np
import json
import os
import sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import EvidenceToken, von_neumann_entropy
from axis_orthogonality_suite import AXES


def random_density_matrix(d, seed=42):
    rng = np.random.default_rng(seed)
    K = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
    rho = K @ K.conj().T
    return rho / np.trace(rho)


def run_abiogenesis_sim():
    print("=" * 72)
    print("ABIOGENESIS V2 SIM (CHIRALITY NECESSITY)")
    print("=" * 72)

    DIMS = [4, 8, 16]
    N_ITERATIONS = 50
    N_SEEDS = 5
    tokens = []
    all_results = []

    a1_channel = AXES["A1_Coupling"]
    a3_channel = AXES["A3_Chirality"]

    for d in DIMS:
        print(f"\n  --- d={d} ---")
        seed_results = []
        
        for s in range(N_SEEDS):
            rho_chiral = random_density_matrix(d, seed=42+s)
            rho_symm = rho_chiral.copy()
            
            ent_chiral = []
            ent_symm = []
            
            for _ in range(N_ITERATIONS):
                # Chiral engine: Asymmetric composition A1(A3(rho))
                rho_chiral = a1_channel(a3_channel(rho_chiral, d), d)
                ent_chiral.append(von_neumann_entropy(rho_chiral))
                
                # Symmetrized engine: (A1(rho) + A1(rho^T)^T) / 2
                out1 = a1_channel(rho_symm, d)
                out2 = a1_channel(rho_symm.T, d).T
                rho_symm = (out1 + out2) / 2.0
                ent_symm.append(von_neumann_entropy(rho_symm))
                
            avg_chiral = float(np.mean(ent_chiral[10:])) # ignore transient
            avg_symm = float(np.mean(ent_symm[10:]))
            max_ent = np.log(d)
            
            # Normalize to max entropy
            rel_chiral = avg_chiral / max_ent
            rel_symm = avg_symm / max_ent
            
            # Difference (positive means symmetric has MORE entropy = chiral is better)
            diff = rel_symm - rel_chiral
            
            seed_results.append({
                "seed": 42+s,
                "chiral_entropy": round(rel_chiral, 4),
                "symm_entropy": round(rel_symm, 4),
                "chiral_advantage": round(diff, 4)
            })
            
            print(f"    Seed {42+s}: Chiral={rel_chiral:.3f}  Symm={rel_symm:.3f}  Advantage={diff:+.3f}")
            
        mean_adv = float(np.mean([r["chiral_advantage"] for r in seed_results]))
        all_chiral_wins = all(r["chiral_advantage"] > 0.02 for r in seed_results)
        
        all_results.append({
            "d": d,
            "mean_advantage": round(mean_adv, 4),
            "all_chiral_wins": all_chiral_wins,
            "seeds": seed_results
        })

    overall_pass = all(r["all_chiral_wins"] for r in all_results)
    mean_all = float(np.mean([r["mean_advantage"] for r in all_results]))
    
    print(f"\n  Does chiral engine maintain lower entropy? {'YES ✓' if overall_pass else 'NO ✗'}")
    print(f"  Mean entropy advantage: {mean_all:+.4f}")
    print(f"  OVERALL: {'PASS' if overall_pass else 'KILL'}")

    if overall_pass:
        tokens.append(EvidenceToken("E_SIM_ABIOGENESIS_CHIRAL_ADVANTAGE", 
                                  "S_SIM_ABIOGENESIS", "PASS", mean_all))
    else:
        tokens.append(EvidenceToken("", "S_SIM_ABIOGENESIS", "KILL", mean_all, "SYMMETRIC_EQUAL_OR_BETTER"))

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "abiogenesis_v2_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "dimensions": DIMS,
            "results": all_results,
            "evidence_ledger": [t.__dict__ for t in tokens]
        }, f, indent=2)
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_abiogenesis_sim()
