#!/usr/bin/env python3
"""
Axis Independence on Hopf Geometry
====================================

CRITICAL FIX: All previous sims used generic random density matrices.
The engine lives on S³ → S² (Hopf fibration) with nested tori.
This sim tests axis independence on ACTUAL geometric states.

States are d=2 density matrices generated from:
  1. Random S³ points (uniform on Hopf sphere)
  2. Inner torus (η = π/8)
  3. Clifford torus (η = π/4)
  4. Outer torus (η = 3π/8)
  5. Mixed states (thermal mixtures on the Bloch ball)

If axes behave differently on the manifold vs generic space,
the previous results are WRONG for the engine.
"""

import numpy as np
import scipy.linalg as la
import json, os, sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hopf_manifold import (
    torus_coordinates, coherent_state_density, random_s3_point,
    fiber_action, bloch_to_density, density_to_bloch,
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
    hopf_map, quaternion_to_su2,
)


def ensure_valid(rho):
    rho=(rho+rho.conj().T)/2; ev,evc=np.linalg.eigh(rho)
    ev=np.maximum(ev,0); rho=evc@np.diag(ev)@evc.conj().T
    tr=np.trace(rho); 
    if abs(tr)>1e-12: rho/=tr
    return rho

def normalized_overlap(A,B):
    nA,nB=np.linalg.norm(A,'fro'),np.linalg.norm(B,'fro')
    if nA<1e-12 or nB<1e-12: return 0.0
    return float(abs(np.trace(A.conj().T@B))/(nA*nB))


# ═══════════════════════════════════════════════════════════════════
# STATE GENERATORS ON THE GEOMETRY
# ═══════════════════════════════════════════════════════════════════

def random_hopf_state(rng):
    """Pure state from random S³ point."""
    q = rng.normal(size=4)
    q /= np.linalg.norm(q)
    return coherent_state_density(q)

def torus_state(eta, rng):
    """Pure state from a specific torus T²(η)."""
    t1 = rng.uniform(0, 2*np.pi)
    t2 = rng.uniform(0, 2*np.pi)
    q = torus_coordinates(eta, t1, t2)
    return coherent_state_density(q)

def mixed_bloch_state(r, rng):
    """Mixed state at Bloch radius r (0=maximally mixed, 1=pure)."""
    # Random direction on S²
    direction = rng.normal(size=3)
    direction /= np.linalg.norm(direction)
    p = r * direction
    return bloch_to_density(p)


# ═══════════════════════════════════════════════════════════════════
# AXIS DISPLACEMENTS (d=2, on geometry)
# ═══════════════════════════════════════════════════════════════════

d = 2  # Engine lives in d=2

def ax0_geom(rho):
    """Coarse-graining: partial dephasing"""
    diag = np.diag(np.diag(rho))
    return (0.2*rho + 0.8*diag) - (0.8*rho + 0.2*diag)

def ax1_geom(rho):
    """Dissipation: amplitude damping vs unitary"""
    # Unitary
    H = np.array([[1,0],[0,-1]], dtype=complex) * 0.3  # σ_z rotation
    U = la.expm(-1j*H)
    rho_u = U@rho@U.conj().T
    # CPTP: amplitude damping
    gamma = 0.3
    K0 = np.array([[1,0],[0,np.sqrt(1-gamma)]], dtype=complex)
    K1 = np.array([[0,np.sqrt(gamma)],[0,0]], dtype=complex)
    rho_c = K0@rho@K0.conj().T + K1@rho@K1.conj().T
    return rho_c - rho_u

def ax2_geom(rho):
    """Boundary: trace-decrease vs trace-preserve"""
    P = np.diag([1.0, 0.7]).astype(complex)
    rho_e = P@rho@P.conj().T
    rho_e /= max(abs(np.trace(rho_e)), 1e-12)
    H = np.array([[0,1],[1,0]], dtype=complex) * 0.5  # σ_x rotation
    rho_l = la.expm(-1j*H)@rho@la.expm(1j*H)
    return rho_e - rho_l

def ax3_geom(rho):
    """Chirality: U vs U* (Weyl conjugate)
    On d=2 this is: UρU† vs U*ρU^T
    """
    H = np.array([[0.3, 0.1+0.2j],[0.1-0.2j, -0.3]], dtype=complex)
    U = la.expm(-1j*H)
    rho_L = U@rho@U.conj().T
    rho_R = np.conj(U)@rho@np.conj(U).T
    return rho_L - rho_R

def ax4_geom(rho):
    """Composition order: dephasing∘damping vs damping∘dephasing"""
    gamma=0.3
    K0 = np.array([[1,0],[0,np.sqrt(1-gamma)]], dtype=complex)
    K1 = np.array([[0,np.sqrt(gamma)],[0,0]], dtype=complex)
    def damping(r):
        return K0@r@K0.conj().T + K1@r@K1.conj().T
    def dephasing(r):
        return 0.7*r + 0.3*np.diag(np.diag(r))
    return damping(dephasing(rho)) - dephasing(damping(rho))

def ax6_geom(rho):
    """Action side: Aρ vs ρA"""
    A = np.array([[0.5, 0.3+0.4j],[0.1-0.2j, -0.5]], dtype=complex)
    A /= np.linalg.norm(A)
    return A@rho - rho@A

def meas_geom(rho):
    """Measurement basis: z-dephasing vs x-dephasing"""
    proj_z = np.diag(np.diag(rho))
    # Hadamard basis
    H = np.array([[1,1],[1,-1]], dtype=complex) / np.sqrt(2)
    rho_h = H@rho@H.conj().T
    proj_x = np.diag(np.diag(rho_h))
    proj_x_back = H.conj().T@proj_x@H
    return proj_z - proj_x_back

def fiber_phase_geom(rho, q):
    """Fiber action: e^{+iθ} vs e^{-iθ} along the Hopf fiber.
    This is a GEOMETRIC operation that only makes sense on S³.
    """
    theta = 0.4
    q_plus = fiber_action(q, theta)
    q_minus = fiber_action(q, -theta)
    rho_plus = coherent_state_density(q_plus)
    rho_minus = coherent_state_density(q_minus)
    return rho_plus - rho_minus

def torus_transport_geom(rho, q, eta):
    """Move between tori: transport from η to η±δ.
    Another GEOMETRIC operation.
    """
    # Get the angular coordinates
    a,b,c,dd = q
    z1 = a + 1j*b; z2 = c + 1j*dd
    t1 = np.angle(z1); t2 = np.angle(z2)
    delta_eta = 0.2
    q_up = torus_coordinates(min(eta+delta_eta, np.pi/2-0.01), t1, t2)
    q_down = torus_coordinates(max(eta-delta_eta, 0.01), t1, t2)
    return coherent_state_density(q_up) - coherent_state_density(q_down)


# ═══════════════════════════════════════════════════════════════════
# MAIN TEST
# ═══════════════════════════════════════════════════════════════════

def run_geometric_test():
    n_trials = 200
    
    # Standard axes (don't need q)
    std_axes = [
        ("Ax0:coarse", ax0_geom),
        ("Ax1:dissip", ax1_geom),
        ("Ax2:boundary", ax2_geom),
        ("Ax3:chirality", ax3_geom),
        ("Ax4:compose", ax4_geom),
        ("Ax6:action", ax6_geom),
        ("meas_basis", meas_geom),
    ]
    # Geometric axes (need q and η)
    geo_axes = [
        "fiber_phase",
        "torus_transport",
    ]
    
    all_names = [a[0] for a in std_axes] + geo_axes
    n_axes = len(all_names)
    
    torus_configs = [
        ("S³ random", None),
        ("inner torus (η=π/8)", TORUS_INNER),
        ("Clifford torus (η=π/4)", TORUS_CLIFFORD),
        ("outer torus (η=3π/8)", TORUS_OUTER),
        ("mixed (r=0.5)", "mixed"),
    ]
    
    all_results = {}
    
    for config_name, config in torus_configs:
        print(f"\n{'='*70}")
        print(f"  STATE SOURCE: {config_name}")
        print(f"{'='*70}")
        
        overlap_matrix = np.zeros((n_axes, n_axes))
        norm_totals = np.zeros(n_axes)
        
        for trial in range(n_trials):
            rng = np.random.default_rng(trial + 300000)
            
            # Generate state on geometry
            if config is None:
                q = random_s3_point(rng)
                eta = np.pi/4  # default
            elif config == "mixed":
                q = random_s3_point(rng)
                eta = np.pi/4
                rho_override = mixed_bloch_state(0.5, rng)
            elif isinstance(config, float):
                eta = config
                t1 = rng.uniform(0, 2*np.pi)
                t2 = rng.uniform(0, 2*np.pi)
                q = torus_coordinates(eta, t1, t2)
            
            if config == "mixed":
                rho = rho_override
            else:
                rho = coherent_state_density(q)
            
            # Compute all displacements
            disps = []
            for _, fn in std_axes:
                disps.append(fn(rho))
            disps.append(fiber_phase_geom(rho, q))
            disps.append(torus_transport_geom(rho, q, eta))
            
            for i in range(n_axes):
                norm_totals[i] += np.linalg.norm(disps[i], 'fro')
                for j in range(i+1, n_axes):
                    ov = normalized_overlap(disps[i], disps[j])
                    overlap_matrix[i,j] += ov
                    overlap_matrix[j,i] += ov
        
        overlap_matrix /= n_trials
        norm_avgs = norm_totals / n_trials
        
        # Print matrix
        short = [n[:8] for n in all_names]
        print(f"\n  {'':14s}", end="")
        for s in short: print(f"{s:>9s}", end="")
        print(f"{'norm':>8s}")
        
        for i in range(n_axes):
            print(f"  {all_names[i]:14s}", end="")
            max_off = 0.0
            for j in range(n_axes):
                if i==j: print(f"{'·':>9s}", end="")
                else:
                    v = overlap_matrix[i,j]
                    max_off = max(max_off, v)
                    m = "!" if v > 0.5 else (" " if v < 0.2 else "~")
                    print(f"  {v:.3f}{m}", end="")
            status = "✅" if max_off < 0.3 else ("⚠️" if max_off < 0.5 else "❌")
            print(f"  {norm_avgs[i]:.4f} {status}")
        
        all_results[config_name] = {
            "overlap": overlap_matrix.tolist(),
            "norms": norm_avgs.tolist(),
        }
    
    # Cross-comparison summary
    print(f"\n{'='*70}")
    print(f"  GEOMETRY vs GENERIC: Key pair overlaps")
    print(f"{'='*70}")
    
    key_pairs = [
        ("Ax0:coarse", "Ax1:dissip", 0, 1),
        ("Ax3:chirality", "Ax6:action", 3, 5),
        ("Ax3:chirality", "Ax1:dissip", 3, 1),
        ("meas_basis", "Ax0:coarse", 6, 0),
        ("fiber_phase", "Ax3:chirality", 7, 3),
        ("torus_trans", "Ax0:coarse", 8, 0),
    ]
    
    print(f"  {'Pair':35s}", end="")
    for cn, _ in torus_configs:
        print(f"{cn[:12]:>14s}", end="")
    print()
    
    for name, _, i, j in key_pairs:
        print(f"  {all_names[i]:14s} × {all_names[j]:14s}  ", end="")
        for cn, _ in torus_configs:
            v = all_results[cn]["overlap"][i][j]
            print(f"  {v:10.4f}  ", end="")
        print()
    
    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    results = {
        "schema": "AXIS_HOPF_GEOMETRY_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "d": 2, "n_trials": n_trials,
        "configs": [c[0] for c in torus_configs],
        "axes": all_names,
        "results": all_results,
    }
    out_file = os.path.join(out_dir, "axis_hopf_geometry_results.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    run_geometric_test()
