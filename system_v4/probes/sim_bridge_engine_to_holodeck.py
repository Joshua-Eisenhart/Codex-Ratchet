#!/usr/bin/env python3
"""
Holodeck integration bridge: Live Engine to FEP Metrics.
========================================================

User rule: "stabilize first, integrate second, canonize last."
We cannot claim Holodeck integration works on toy states. We must pass 
a LIVE runtime trajectory from `engine_core.py` into the FEP engine 
and verify that the calculated FEP KL Surprise actually correlates 
with the engine's internal Ax0 drive variable (`ga0_level`).

This script bridges `engine_core.py` (generating 64-step trajectories) 
to the `holodeck_fep_engine.py` (calculating FEP metrics).
"""

import numpy as np
import scipy.linalg as la
import json, os, sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, EngineState, StageControls
from holodeck_fep_engine import compute_fep_surprise, compute_coherence_score, build_thermal_prior
from proto_ratchet_sim_runner import EvidenceToken, von_neumann_entropy

def pearson_correlation(x, y):
    """Compute Pearson r between two arrays."""
    x = np.asarray(x)
    y = np.asarray(y)
    mean_x = np.mean(x)
    mean_y = np.mean(y)
    numerator = np.sum((x - mean_x) * (y - mean_y))
    denominator = np.sqrt(np.sum((x - mean_x)**2) * np.sum((y - mean_y)**2))
    if denominator < 1e-12:
        return 0.0
    return float(numerator / denominator)

def run_bridge():
    print("=" * 80)
    print("BRIDGE: Live Engine Trajectory -> FEP Holodeck Constraints")
    print("Comparing inside Ax0 local (`ga0_level`) against Holodeck FEP Surprise.")
    print("=" * 80)

    # We will test both Engine Types, across 10 complete 64-stage cycles (320 steps total per type)
    n_cycles = 10
    
    total_correlations = []
    
    results_out = {
        "schema": "BRIDGE_FEP_ENGINE_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "trajectories": {}
    }
    
    # 2-qubit system -> d=2 density for the components
    thermal_prior = build_thermal_prior(T=1.5, d=2)
    
    for engine_type in (1, 2):
        print(f"\n--- Booting Live Engine Type {engine_type} ---")
        rng = np.random.default_rng(1000 * engine_type)
        
        engine = GeometricEngine(engine_type=engine_type)
        state = engine.init_state(rng=rng)
        
        history_ga0 = []
        history_fep = []
        history_coherence = []
        
        # Run 10 full macro-cycles
        for cycle in range(n_cycles):
            for stage_idx in range(8): # 8 terrains
                # Apply the macro stage
                state = engine.step(state, stage_idx=stage_idx)
                
                # Each step internally acts 4 times, but we take the state at the end of the stage
                # Compute composite local state (average of left and right Weyl spinors)
                # This models the local field projection the Holodeck sees.
                rho_avg = (state.rho_L + state.rho_R) / 2.0
                
                # Get density eigenspectrum
                evals = np.real(la.eigvalsh(rho_avg))
                evals = np.maximum(evals, 1e-12) # Filter negative zeros
                evals /= np.sum(evals) # Normalize
                
                # Compute FEP and Coherence
                fep = compute_fep_surprise(evals, thermal_prior)
                coh = compute_coherence_score(evals, d=2)
                
                # Record metrics
                history_ga0.append(float(state.ga0_level))
                history_fep.append(float(fep))
                history_coherence.append(float(coh))
                
        # Correlate across the entire 80-stage trajectory
        r_fep_ga0 = pearson_correlation(history_ga0, history_fep)
        
        print(f"  Total stages traversed: {len(history_ga0)}")
        print(f"  Pearson Correlation (FEP Surprise vs Inside ga0_level) : {r_fep_ga0:+.4f}")
        
        if abs(r_fep_ga0) > 0.85:
            print("  [PASS] Strong linear correlation! FEP naturally models the inside Ax0 drive.")
        else:
            print("  [FAIL] Weak correlation. FEP does not perfectly mirror internal ga0.")
            
        total_correlations.append(abs(r_fep_ga0))
        
        results_out["trajectories"][f"type_{engine_type}"] = {
            "r_fep_ga0": r_fep_ga0,
            "ga0_trajectory": history_ga0,
            "fep_trajectory": history_fep,
            "coherence_trajectory": history_coherence
        }
    
    # Assess viability of promotion
    avg_r = np.mean(total_correlations)
    print(f"\n================================================================================")
    print(f"FINAL BRIDGE VERDICT: Average Correlation |r| = {avg_r:.4f}")
    if avg_r > 0.85:
        print("Verdict: STABILIZED. FEP Surprise securely mirrors the Engine's internal Ax0 Drive.")
    else:
        print("Verdict: ABORT. Connection is too weak to canonize FEP as the definitive Ax0.")
    print("================================================================================")

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "sim_results")
    out_file = os.path.join(out_dir, "bridge_engine_fep_holodeck.json")
    with open(out_file, "w") as f:
        json.dump(results_out, f, indent=2)
    print(f"\n  Results saved to {out_file}")

if __name__ == "__main__":
    run_bridge()
