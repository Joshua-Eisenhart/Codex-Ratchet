#!/usr/bin/env python3
"""
HOLODECK FEP ENGINE (v1)
========================
Implements the Free Energy Principle (FEP) as the explicit Axis 0 Gradient.
Projects the 2-qubit Dirac/Weyl engine states safely onto the S^3 Hopf 
Fibration manifold, carefully preserving phase data (chi/fiber coordinate)
to build the 3D sensory environment (The Holodeck).

Reference: core_docs/HOLODECK_SCIENCE_SYSTEM_v1.md
"""

import numpy as np
import scipy.linalg as la
import json, os, sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import EvidenceToken

def partial_trace_A(rho, dim_A=2, dim_B=2):
    """Trace out system B from a composite rho_{AB}."""
    reshaped = rho.reshape((dim_A, dim_B, dim_A, dim_B))
    return np.einsum('jiki->jk', reshaped)

def hopf_map(psi_A):
    """
    Map a 2-component spinor |psi_A> = (alpha, beta)^T to S^3 coordinates.
    Returns: (theta, phi, chi)
    theta in [0, pi]: Polar spherical angle
    phi in [0, 2pi): Azimuthal spherical angle
    chi in [0, 4pi): Hopf Fiber phase
    """
    alpha, beta = psi_A[0], psi_A[1]
    
    # Magnitudes and phases
    r_alpha = np.abs(alpha)
    # Ensure float safety for arccos
    r_alpha = np.clip(r_alpha, 0.0, 1.0)
    
    theta = 2.0 * np.arccos(r_alpha)
    
    arg_alpha = np.angle(alpha)
    arg_beta = np.angle(beta)
    
    phi = (arg_beta - arg_alpha) % (2 * np.pi)
    chi = (arg_alpha + arg_beta) % (4 * np.pi)
    
    return theta, phi, chi

def compute_fep_surprise(obs_evals, model_evals):
    """
    Compute S_FEP = KL(q(z|x) || p(z)), the surprise of the observation given the model.
    q(z|x) = obs_evals (the observed density eigen-spectrum)
    p(z)   = model_evals (the predicted density eigen-spectrum, e.g. Thermal prior)
    """
    # Epsilon to prevent log(0)
    eps = 1e-12
    q = np.clip(obs_evals, eps, 1.0)
    p = np.clip(model_evals, eps, 1.0)
    
    # Normalize securely to make true probabilities
    q /= np.sum(q)
    p /= np.sum(p)
    
    kl = np.sum(q * np.log(q / p))
    return float(kl)

def compute_coherence_score(evals, d=4):
    """1 - S_vN / log2(d), where 1 = pure, 0 = maximally mixed."""
    eps = 1e-12
    q = np.clip(evals, eps, 1.0)
    s_vn = -np.sum(q * np.log2(q))
    # log2(4) = 2.0
    return max(0.0, 1.0 - (s_vn / np.log2(d)))

def build_thermal_prior(T=1.0, d=4):
    """
    Constructs a generic thermal background prior p(z).
    E_i = i, so p_i ~ exp(-i/T)
    """
    energies = np.arange(d, dtype=float)
    p = np.exp(-energies / T)
    return p / np.sum(p)

def run_holodeck_engine():
    print("=" * 80)
    print("HOLODECK SCIENCE SYSTEM: FEP ENGINE INIT")
    print("Mapping Engine Density Matrices -> S^3 Topological Projections")
    print("Axis 0 = FEP Entropy Gradient")
    print("=" * 80)
    
    tokens = []
    
    # Generate a sample engine state (mixed)
    rng = np.random.default_rng(20260327)
    
    # 1. We start with a 4x4 density matrix (d=4 base Hilbert space)
    # Let's generate a structured state with some coherence
    H = rng.normal(size=(4,4)) + 1j*rng.normal(size=(4,4))
    H = H + H.conj().T
    rho_obs = la.expm(-1j * H * 1.5) @ np.diag([0.7, 0.2, 0.08, 0.02]) @ la.expm(1j * H * 1.5)
    
    # EIGENSPACE DECOMPOSITION
    evals, evecs = la.eigh(rho_obs)
    
    # Sort descending
    idx = np.argsort(evals)[::-1]
    evals = evals[idx]
    evecs = evecs[:, idx]
    
    # HOPF FIBRATION S^3 MAPPING
    s3_projections = []
    valid_s3 = True
    for i in range(4):
        psi = evecs[:, i]
        # Partial trace to get reduced state on qubit A
        # psi is a 4-vector. For a pure state, rho_A is 2x2.
        # But we need a 2-spinor |psi_A> to do Hopf map directly, 
        # so we extract the dominant eigenvector of rho_A as the fiber base
        # (Since S^3 naturally maps CP^1 / C^2)
        rho = np.outer(psi, psi.conj())
        rho_A = partial_trace_A(rho, 2, 2)
        evals_A, evecs_A = la.eigh(rho_A)
        # dominant eigenvector of the reduced state
        psi_A = evecs_A[:, np.argmax(evals_A)]
        
        theta, phi, chi = hopf_map(psi_A)
        s3_projections.append({
            "eigen_index": i,
            "weight": float(evals[i]),
            "s3_theta": float(theta),
            "s3_phi": float(phi),
            "s3_chi": float(chi)
        })
        
        if np.isnan(theta) or np.isnan(phi) or np.isnan(chi):
            valid_s3 = False

    tokens.append(EvidenceToken(
        "E_SIM_HOLODECK_S3_PROJECTION_OK",
        "S_SIM_HOLODECK_FEP",
        "PASS" if valid_s3 else "KILL",
        None,
        None if valid_s3 else "INVALID_S3_PROJECTION"
    ))
    
    # FEP SURPRISE (AXIS 0 GRADIENT)
    thermal_prior = build_thermal_prior(T=1.5, d=4)
    fep_surprise = compute_fep_surprise(evals, thermal_prior)
    
    tokens.append(EvidenceToken(
        "E_SIM_HOLODECK_FEP_SURPRISE_OK",
        "S_SIM_HOLODECK_FEP",
        "PASS" if (0 <= fep_surprise < np.inf) else "KILL",
        float(fep_surprise),
        None if (0 <= fep_surprise < np.inf) else "FEP_DIVERGENCE"
    ))
    
    # COHERENCE SCORE
    coh_score = compute_coherence_score(evals, d=4)
    tokens.append(EvidenceToken(
        "E_SIM_HOLODECK_COHERENCE_OK",
        "S_SIM_HOLODECK_FEP",
        "PASS" if (0.0 < coh_score <= 1.0) else "KILL",
        float(coh_score),
        None if (0.0 < coh_score <= 1.0) else "COHERENCE_COLLAPSE"
    ))
    
    # PREPARE ATTRACTOR COORDINATE
    primary_projection = s3_projections[0] # The dominant eigen-fiber
    
    results = {
        "schema": "FEP_HOLODECK_ENGINE_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "tokens": [{"token_id": t.token_id, "sim_spec_id": t.sim_spec_id, "status": t.status, "measured_value": t.measured_value, "kill_reason": t.kill_reason, "timestamp": t.timestamp} for t in tokens],
        "state_metrics": {
            "eigenvalues": evals.tolist(),
            "fep_surprise_ax0": float(fep_surprise),
            "coherence_score": float(coh_score),
            "s3_projections": s3_projections
        },
        "dominant_attractor_coordinate": {
            "s3_theta": primary_projection["s3_theta"],
            "s3_phi": primary_projection["s3_phi"],
            "s3_chi": primary_projection["s3_chi"],
            "fep_surprise": float(fep_surprise),
            "coherence_score": float(coh_score),
            "thermal_temperature": 1.5
        }
    }
    
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "sim_results")
    out_file = os.path.join(out_dir, "holodeck_fep_results.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"\nEngine outputs saved to: {out_file}")
    print("\nEvidence Tokens:")
    for t in tokens:
        print(f"  [{t.status}] {t.token_id}: {t.measured_value}")
        
    # Check KILL conditions
    if any(t.status == "KILL" for t in tokens):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    run_holodeck_engine()
