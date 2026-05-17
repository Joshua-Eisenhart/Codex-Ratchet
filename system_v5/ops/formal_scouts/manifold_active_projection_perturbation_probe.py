#!/usr/bin/env python3
"""
manifold_active_projection_perturbation_probe.py

Verify the 'Active Projection' role of the manifold by injecting rank-2 noise 
mid-cycle and confirming that the manifold (Patch C) collapses it back to 
rank-1 in the science-method records.
"""

import numpy as np
from engine_core import EngineCore, generate_initial_density, I2, _normalize_density

def run_perturbation_test(seed: int = 42):
    print(f"Running perturbation test with seed {seed}...")
    
    # Initialize engine (Type 1)
    eng = EngineCore(engine_type=0)
    rho = generate_initial_density(seed)
    
    # Run first 4 main stages (0, 1, 2, 3)
    # Total substages: 4 stages * 4 substages = 16
    trajectory = []
    for main_idx in range(4):
        perception, loop_class = eng.schedule[main_idx]
        rho, records = eng.run_main_stage(rho, perception, loop_class, main_idx)
        trajectory.extend(records)
    
    # At start of Stage 4, inject rank-2 noise
    # We mix the current pure-ish state with the identity (max mixed)
    noise_strength = 0.3
    rho_perturbed = _normalize_density((1.0 - noise_strength) * rho + noise_strength * I2 / 2)
    
    print(f"Injecting noise at Stage 4. Rank before: {trajectory[-1]['model_after']['carrier_rank']}, Rank after perturbation: {int(np.sum(np.linalg.eigvalsh(rho_perturbed) > 1e-10))}")
    
    # Run Stage 4 with the perturbed state
    main_idx = 4
    perception, loop_class = eng.schedule[main_idx]
    
    # We'll run the first substage (substage 0) manually to inspect the বিজ্ঞান fields
    rho, records = eng.run_main_stage(rho_perturbed, perception, loop_class, main_idx)
    
    # Inspect Stage 4, Substage 0
    s4_sub0 = records[0]
    
    p1_pass = s4_sub0["model_before"]["carrier_rank"] == 2
    p2_pass = s4_sub0["manifold_intermediate"]["model"]["carrier_rank"] == 1
    p3_pass = s4_sub0["model_after"]["carrier_rank"] == 1
    p4_pass = s4_sub0["fep_efe_score"]["surprise_kl_manifold_step"] > 0.05 # Expect manifold to do work
    
    print("\nPredicate Results for Stage 4, Substage 0 (Perturbed):")
    print(f"P1 (Input is Rank-2): {'PASS' if p1_pass else 'FAIL'} (Rank={s4_sub0['model_before']['carrier_rank']})")
    print(f"P2 (Manifold Output is Rank-1): {'PASS' if p2_pass else 'FAIL'} (Rank={s4_sub0['manifold_intermediate']['model']['carrier_rank']})")
    print(f"P3 (Loop Output is Rank-1): {'PASS' if p3_pass else 'FAIL'} (Rank={s4_sub0['model_after']['carrier_rank']})")
    print(f"P4 (Manifold Surprises): {'PASS' if p4_pass else 'FAIL'} (KL={s4_sub0['fep_efe_score']['surprise_kl_manifold_step']:.4f})")
    
    all_pass = p1_pass and p2_pass and p3_pass and p4_pass
    return all_pass, s4_sub0

if __name__ == "__main__":
    success, record = run_perturbation_test()
    if success:
        print("\nSUCCESS: Manifold active projection verified.")
        exit(0)
    else:
        print("\nFAILURE: Manifold active projection not verified.")
        exit(1)
