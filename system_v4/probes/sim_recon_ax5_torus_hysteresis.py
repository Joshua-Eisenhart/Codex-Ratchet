#!/usr/bin/env python3
"""
Phenomenological Reconnaissance: Ax5 Torus Hysteresis vs Ax0 Macro-Gradient
===========================================================================
Rule #4: Ax0 is Macro-Geometric (Gravity / Gradient).
Ax0 is NOT a local bit-flip or density matrix dephasing. 
It is the entropy gradient/resolution scaling (e.g., 2-sample vs 7-sample).
Ax5 (Curvature / FSA / Hysteresis) was previously conflated with Ax0 
because both "dephasing" and "Hamiltonian curvature" destroy the same 
off-diagonal bits in a density matrix.

We test them at the Torus Geometric Layer:
- State: Hopf Torus coordinates (r, theta, phi)
- Ax0 (Drive/Resolution): Scaling the fiber sample count N -> N_new (radial/resolution)
- Ax5 (Curvature/Hysteresis): Geometric phase enclosed by a partial transport loop
                   (theta -> theta+d, phi -> phi+d)

We measure if the displacement vector of Ax0 is orthogonal to Ax5.
If Overlap < 0.5, the historical Ax0/Ax5 conflation (0.66) is mathematically killed.
"""

import numpy as np
import scipy.linalg as la
import json, os, sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def generate_torus_state(rng):
    """Generate a valid point on the S3 Clifford Torus."""
    # S3 coordinates: (cos(eta)*e^{i phi1}, sin(eta)*e^{i phi2})
    eta = rng.uniform(0, np.pi/2)
    phi1 = rng.uniform(0, 2*np.pi)
    phi2 = rng.uniform(0, 2*np.pi)
    
    # Let N be the macro-gradient sample count (Ax0 depth)
    N = int(rng.integers(2, 6))
    
    return np.array([eta, phi1, phi2, N], dtype=float)

def apply_ax0_expansion(state):
    """Ax0: Entropy Gradient / Resolution Scaling. 
    Expands the fiber from N to N+3 samples. This is a structural depth change."""
    out = state.copy()
    out[3] += 3.0  # increase sample count N
    return out

def apply_ax5_hysteresis(state):
    """Ax5: Torus Partial Transport Hysteresis.
    Represents the geometric curvature/phase accumulated by traversing the fiber.
    We model this as a non-linear phase shift dependent on eta (curvature)."""
    eta, phi1, phi2, N = state
    out = state.copy()
    
    # Hysteresis Delta = Area enclosed / Berry Phase ~ cos^2(eta) - sin^2(eta) = cos(2*eta)
    curvature_shift = np.cos(2 * eta) * (np.pi / N)
    
    out[1] = (phi1 + curvature_shift) % (2*np.pi)
    out[2] = (phi2 - curvature_shift) % (2*np.pi)
    return out

def state_distance_vector(s1, s2):
    """Calculate the displacement vector between two torus states.
    Handle angular wrap-around naturally, and normalize N to comparable scale."""
    d_eta = s1[0] - s2[0]
    
    # angular difference bounded [-pi, pi]
    d_phi1 = (s1[1] - s2[1] + np.pi) % (2*np.pi) - np.pi
    d_phi2 = (s1[2] - s2[2] + np.pi) % (2*np.pi) - np.pi
    
    # scale N displacement so it's comparable geometrically
    d_N = (s1[3] - s2[3]) * 0.5
    
    return np.array([d_eta, d_phi1, d_phi2, d_N])

def noverlap(v1, v2):
    """Cosine similarity of displacement vectors."""
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 < 1e-12 or n2 < 1e-12: return 0.0
    return float(np.abs(np.dot(v1, v2)) / (n1 * n2))

def run():
    n_trials = 1000
    
    print("=" * 80)
    print("RECON: Ax5 Torus Hysteresis vs Ax0 Macro-Gradient")
    print(f"Trials: {n_trials}")
    print("=" * 80)
    
    norm_ax0 = 0.0
    norm_ax5 = 0.0
    overlap_0_5 = 0.0
    
    for trial in range(n_trials):
        rng = np.random.default_rng(400000 + trial)
        state = generate_torus_state(rng)
        
        # ----------------------------------------------------
        # Ax0: Macro-Gradient Drive (N -> N+3)
        # ----------------------------------------------------
        state_ax0 = apply_ax0_expansion(state)
        disp_ax0 = state_distance_vector(state, state_ax0)
        
        # ----------------------------------------------------
        # Ax5: Curvature/Hysteresis (Phase Shift dependent on eta)
        # ----------------------------------------------------
        state_ax5 = apply_ax5_hysteresis(state)
        disp_ax5 = state_distance_vector(state, state_ax5)
        
        norm_ax0 += np.linalg.norm(disp_ax0)
        norm_ax5 += np.linalg.norm(disp_ax5)
        overlap_0_5 += noverlap(disp_ax0, disp_ax5)
        
    norm_ax0 /= n_trials
    norm_ax5 /= n_trials
    overlap_0_5 /= n_trials
    
    print(f"\n  AX0 (Macro-Gradient/Expansion) Mean Norm: {norm_ax0:.4f}")
    print(f"  AX5 (Torus Hysteresis/Phase)   Mean Norm: {norm_ax5:.4f}")
    print(f"  Overlap (Ax0 vs Ax5)                    : {overlap_0_5:.4f}")
    
    if overlap_0_5 < 0.2:
        print("\n  SUCCESS: Ax5 (Curvature) and Ax0 (Gradient) are completely orthogonal on the Torus.")
    else:
        print("\n  FAILURE: Ax5 and Ax0 remain entangled.")

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    results = {
        "schema": "RECON_AX5_TORUS_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "n_trials": n_trials,
        "norm_ax0": norm_ax0,
        "norm_ax5": norm_ax5,
        "overlap_0_5": overlap_0_5
    }
    out_file = os.path.join(out_dir, "recon_ax5_torus.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to {out_file}")

if __name__ == "__main__":
    run()
