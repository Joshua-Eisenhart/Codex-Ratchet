#!/usr/bin/env python3
"""
sim_gudhi_phase_sensitive_kernel.py

Tests three kernel embeddings of the 10x10 Bloch sphere family to determine
whether phi-sensitive features restore S^2 topology in GUDHI persistence.

K1 (original, phi-blind): (MI, cond_S, I_c)
K2 (phase-aware):         (MI, cond_S, I_c, Re(off_diag_rho_A), Im(off_diag_rho_A))
K3 (Berry phase axis):    (MI, cond_S, I_c, A_phi) where A_phi = i<psi|d/dphi|psi>

Berry connection A_phi is computed via torch autograd.
"""

import json
import os
import numpy as np
classification = "canonical"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": "load_bearing",
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *  # noqa: F401,F403
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except Exception as exc:
    TOOL_MANIFEST["clifford"]["reason"] = f"optional import unavailable: {exc}"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# QUANTUM STATE MACHINERY
# =====================================================================

def bloch_psi(theta, phi):
    """
    Parameterize qubit state |psi(theta,phi)> = cos(t/2)|0> + e^{i*phi}*sin(t/2)|1>.
    Returns complex tensor [2] (single qubit).
    """
    t = torch.tensor(theta, dtype=torch.float64)
    p = torch.tensor(phi, dtype=torch.float64)
    c0 = torch.cos(t / 2).unsqueeze(0)
    c1 = torch.sin(t / 2).unsqueeze(0)
    # Re/Im parts: c0 is real, c1*e^{i*phi}
    psi_re = torch.cat([c0, c1 * torch.cos(p)])
    psi_im = torch.cat([torch.zeros(1, dtype=torch.float64), c1 * torch.sin(p)])
    return psi_re, psi_im


def bloch_psi_tensor(theta, phi):
    """
    Two-qubit entangled state: cos(t/2)|00> + e^{i*phi}*sin(t/2)|11>
    Returns density matrix [4,4] complex (as two real tensors).
    """
    t = torch.tensor(theta, dtype=torch.float64)
    p = torch.tensor(phi, dtype=torch.float64)
    alpha = torch.cos(t / 2)
    beta = torch.sin(t / 2)
    # State vector: [alpha, 0, 0, beta*e^{i*phi}]
    psi_re = torch.zeros(4, dtype=torch.float64)
    psi_im = torch.zeros(4, dtype=torch.float64)
    psi_re[0] = alpha
    psi_re[3] = beta * torch.cos(p)
    psi_im[3] = beta * torch.sin(p)
    return psi_re, psi_im


def rho_from_psi(psi_re, psi_im):
    """Full density matrix |psi><psi| for 4-dim state."""
    # rho = (re + i*im)(re - i*im)^T = re*re^T + im*im^T + i*(im*re^T - re*im^T)
    rho_re = torch.outer(psi_re, psi_re) + torch.outer(psi_im, psi_im)
    rho_im = torch.outer(psi_im, psi_re) - torch.outer(psi_re, psi_im)
    return rho_re, rho_im


def partial_trace_A(rho_re, rho_im):
    """
    Trace out qubit B from 2-qubit system (indices: 00, 01, 10, 11).
    rho_A[i,j] = sum_k rho[i*2+k, j*2+k]
    """
    d = 2
    rho_A_re = torch.zeros(d, d, dtype=torch.float64)
    rho_A_im = torch.zeros(d, d, dtype=torch.float64)
    for i in range(d):
        for j in range(d):
            for k in range(d):
                rho_A_re[i, j] += rho_re[i * d + k, j * d + k]
                rho_A_im[i, j] += rho_im[i * d + k, j * d + k]
    return rho_A_re, rho_A_im


def partial_trace_B(rho_re, rho_im):
    """
    Trace out qubit A from 2-qubit system.
    rho_B[i,j] = sum_k rho[k*2+i, k*2+j]
    """
    d = 2
    rho_B_re = torch.zeros(d, d, dtype=torch.float64)
    rho_B_im = torch.zeros(d, d, dtype=torch.float64)
    for i in range(d):
        for j in range(d):
            for k in range(d):
                rho_B_re[i, j] += rho_re[k * d + i, k * d + j]
                rho_B_im[i, j] += rho_im[k * d + i, k * d + j]
    return rho_B_re, rho_B_im


def von_neumann_entropy(rho_re, rho_im):
    """S = -Tr(rho * log(rho)) via eigendecomposition of Hermitian matrix."""
    # Build complex numpy matrix for eigendecomposition
    rho_np = rho_re.numpy() + 1j * rho_im.numpy()
    evals = np.linalg.eigvalsh(rho_np)
    evals = np.clip(evals, 1e-15, None)
    return float(-np.sum(evals * np.log2(evals)))


def compute_qit_features(theta, phi):
    """Compute (MI, cond_S, I_c, Re(off_diag_A), Im(off_diag_A)) for 2-qubit state."""
    psi_re, psi_im = bloch_psi_tensor(theta, phi)
    rho_re, rho_im = rho_from_psi(psi_re, psi_im)

    S_AB = von_neumann_entropy(rho_re, rho_im)

    rho_A_re, rho_A_im = partial_trace_A(rho_re, rho_im)
    rho_B_re, rho_B_im = partial_trace_B(rho_re, rho_im)

    S_A = von_neumann_entropy(rho_A_re, rho_A_im)
    S_B = von_neumann_entropy(rho_B_re, rho_B_im)

    MI = float(S_A + S_B - S_AB)
    cond_S = float(S_AB - S_A)
    I_c = float(S_A - S_AB)  # = -cond_S

    # Off-diagonal element of rho_A: rho_A[0,1] captures phase
    re_off = float(rho_A_re[0, 1])
    im_off = float(rho_A_im[0, 1])

    return MI, cond_S, I_c, re_off, im_off


def compute_berry_connection_phi(theta, phi_val):
    """
    Berry connection A_phi = i<psi|d/dphi|psi> for single qubit state
    |psi(theta,phi)> = cos(t/2)|0> + e^{i*phi}*sin(t/2)|1>.

    Uses torch autograd: dpsi/dphi computed analytically via grad.
    A_phi = i * <psi|dpsi/dphi> = i * (psi_re - i*psi_im) . (dpsi_re/dphi + i*dpsi_im/dphi)
          = i * [(psi_re . dpsi_re/dphi + psi_im . dpsi_im/dphi)
                 + i*(psi_re . dpsi_im/dphi - psi_im . dpsi_re/dphi)]

    Since |psi> is normalized, <psi|dpsi/dphi> is purely imaginary,
    so A_phi = real number = -Im(<dpsi/dphi|psi>) = psi_re . dpsi_im/dphi - psi_im . dpsi_re/dphi

    Analytically: d/dphi [cos(t/2)|0> + e^{i*phi}*sin(t/2)|1>]
                = i*e^{i*phi}*sin(t/2)|1>
    So <psi|dpsi/dphi> = e^{-i*phi}*sin(t/2) * i*e^{i*phi}*sin(t/2) = i*sin^2(t/2)
    A_phi = i * i*sin^2(t/2) = -sin^2(t/2)  [real]

    We verify with autograd.
    """
    phi_t = torch.tensor(phi_val, dtype=torch.float64, requires_grad=True)
    t = torch.tensor(theta, dtype=torch.float64)

    # psi_re, psi_im as functions of phi_t
    psi_re = torch.stack([torch.cos(t / 2), torch.sin(t / 2) * torch.cos(phi_t)])
    psi_im = torch.stack([torch.zeros(1, dtype=torch.float64).squeeze(), torch.sin(t / 2) * torch.sin(phi_t)])

    # Compute d(psi_re)/dphi and d(psi_im)/dphi via autograd
    # We need gradients of each component
    dpsi_re_dphi = torch.zeros(2, dtype=torch.float64)
    dpsi_im_dphi = torch.zeros(2, dtype=torch.float64)

    for idx in range(2):
        if phi_t.grad is not None:
            phi_t.grad.zero_()
        g_re = torch.autograd.grad(psi_re[idx], phi_t, retain_graph=True, allow_unused=True)[0]
        dpsi_re_dphi[idx] = g_re.item() if g_re is not None else 0.0

        if phi_t.grad is not None:
            phi_t.grad.zero_()
        g_im = torch.autograd.grad(psi_im[idx], phi_t, retain_graph=True, allow_unused=True)[0]
        dpsi_im_dphi[idx] = g_im.item() if g_im is not None else 0.0

    # A_phi = i<psi|dpsi/dphi>
    # <psi|dpsi/dphi> = (psi_re - i*psi_im).(dpsi_re + i*dpsi_im)
    # Real part: psi_re.dpsi_re + psi_im.dpsi_im
    # Imag part: psi_re.dpsi_im - psi_im.dpsi_re
    inner_re = float(torch.dot(psi_re.detach(), dpsi_re_dphi) + torch.dot(psi_im.detach(), dpsi_im_dphi))
    inner_im = float(torch.dot(psi_re.detach(), dpsi_im_dphi) - torch.dot(psi_im.detach(), dpsi_re_dphi))

    # A_phi = i * (inner_re + i*inner_im) = i*inner_re - inner_im
    # Real part of A_phi = -inner_im
    A_phi = -inner_im  # The real scalar Berry connection

    return A_phi


# =====================================================================
# GUDHI PERSISTENCE
# =====================================================================

def run_rips_persistence(point_cloud, max_edge_length=None, max_dimension=2):
    """Run GUDHI Rips complex and return H0/H1/H2 summary."""
    if max_edge_length is None:
        # Use 3x the median pairwise distance
        dists = []
        n = len(point_cloud)
        for i in range(min(n, 20)):
            for j in range(i + 1, min(n, 20)):
                d = np.linalg.norm(point_cloud[i] - point_cloud[j])
                dists.append(d)
        max_edge_length = 3.0 * np.median(dists) if dists else 10.0

    rips = gudhi.RipsComplex(points=point_cloud.tolist(), max_edge_length=max_edge_length)
    st = rips.create_simplex_tree(max_dimension=max_dimension)
    st.compute_persistence()
    pairs = st.persistence()

    summary = {}
    for dim in range(max_dimension + 1):
        bars = [(b, d) for (hdim, (b, d)) in pairs if hdim == dim]
        finite = [(b, d) for (b, d) in bars if not np.isinf(d)]
        infinite = [(b, d) for (b, d) in bars if np.isinf(d)]
        max_pers = max([d - b for (b, d) in finite], default=0.0)
        summary[f"H{dim}"] = {
            "finite_bars": len(finite),
            "infinite_bars": len(infinite),
            "total": len(bars),
            "max_persistence": max_pers,
            "sample_bars": finite[:10],
        }

    return summary, max_edge_length


def summarize_topology(rips_summary):
    H0 = rips_summary.get("H0", {}).get("total", 0)
    H1 = rips_summary.get("H1", {}).get("total", 0)
    H2 = rips_summary.get("H2", {}).get("total", 0)
    H1_inf = rips_summary.get("H1", {}).get("infinite_bars", 0)
    H2_inf = rips_summary.get("H2", {}).get("infinite_bars", 0)
    H1_max_pers = rips_summary.get("H1", {}).get("max_persistence", 0.0)
    H2_max_pers = rips_summary.get("H2", {}).get("max_persistence", 0.0)

    H1_detected = H1 > 0 and H1_max_pers > 1e-6
    H2_detected = H2 > 0 and H2_max_pers > 1e-6

    return {
        "H0_total": H0,
        "H1_total": H1,
        "H2_total": H2,
        "H1_infinite": H1_inf,
        "H2_infinite": H2_inf,
        "H1_max_persistence": H1_max_pers,
        "H2_max_persistence": H2_max_pers,
        "H1_detected": H1_detected,
        "H2_detected": H2_detected,
        "sphere_topology_S2": H2_detected,
        "loop_topology_S1": H1_detected,
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # Build 10x10 Bloch sphere grid
    thetas = np.linspace(0, np.pi, 10)
    phis = np.linspace(0, 2 * np.pi, 10, endpoint=False)

    # Storage for all three kernels
    K1_points = []  # (MI, cond_S, I_c)
    K2_points = []  # (MI, cond_S, I_c, re_off, im_off)
    K3_points = []  # (MI, cond_S, I_c, A_phi)

    point_data = []

    for theta in thetas:
        for phi in phis:
            MI, cond_S, I_c, re_off, im_off = compute_qit_features(theta, phi)
            A_phi = compute_berry_connection_phi(theta, phi)

            K1_points.append([MI, cond_S, I_c])
            K2_points.append([MI, cond_S, I_c, re_off, im_off])
            K3_points.append([MI, cond_S, I_c, A_phi])

            point_data.append({
                "theta": float(theta),
                "phi": float(phi),
                "MI": MI,
                "cond_S": cond_S,
                "I_c": I_c,
                "re_off_diag_A": re_off,
                "im_off_diag_A": im_off,
                "A_phi_berry": A_phi,
            })

    K1_arr = np.array(K1_points)
    K2_arr = np.array(K2_points)
    K3_arr = np.array(K3_points)

    results["n_states"] = len(point_data)
    results["point_cloud_shapes"] = {
        "K1": list(K1_arr.shape),
        "K2": list(K2_arr.shape),
        "K3": list(K3_arr.shape),
    }
    results["point_sample"] = point_data[:6]

    # Run GUDHI for each kernel
    for label, arr in [("K1_phi_blind", K1_arr), ("K2_phase_aware", K2_arr), ("K3_berry_axis", K3_arr)]:
        rips_summary, max_edge = run_rips_persistence(arr)
        topo = summarize_topology(rips_summary)
        results[label] = {
            "rips_max_edge_length": max_edge,
            "rips": rips_summary,
            "topology": topo,
        }

    # Key tests
    K1_topo = results["K1_phi_blind"]["topology"]
    K2_topo = results["K2_phase_aware"]["topology"]
    K3_topo = results["K3_berry_axis"]["topology"]

    results["key_tests"] = {
        "K1_H2_detected": K1_topo["H2_detected"],
        "K2_H2_detected": K2_topo["H2_detected"],
        "K3_H2_detected": K3_topo["H2_detected"],
        "K3_H1_detected": K3_topo["H1_detected"],
        "K2_restores_S2": K2_topo["sphere_topology_S2"],
        "K3_restores_S2": K3_topo["sphere_topology_S2"],
        "K3_shows_equatorial_loop": K3_topo["loop_topology_S1"],
        "phi_blind_confirmed_K1": not K1_topo["H2_detected"] and not K1_topo["H1_detected"],
    }

    # Interpretation
    interp_parts = []
    if K1_topo["H2_detected"]:
        interp_parts.append("K1 (phi-blind): unexpectedly shows H2 -- check kernel scale.")
    else:
        interp_parts.append("K1 (phi-blind): H2=0 confirmed -- phi collapse reproduced.")

    if K2_topo["H2_detected"]:
        interp_parts.append("K2 (phase-aware): H2 detected -- off-diagonal rho_A restores S^2 topology.")
    else:
        interp_parts.append("K2 (phase-aware): H2=0 -- off-diagonal features insufficient to restore S^2.")

    if K3_topo["H2_detected"]:
        interp_parts.append("K3 (Berry axis): H2 detected -- Berry connection A_phi restores S^2 topology.")
    elif K3_topo["H1_detected"]:
        interp_parts.append("K3 (Berry axis): H1 detected, H2=0 -- Berry connection reveals equatorial loop but not full S^2.")
    else:
        interp_parts.append("K3 (Berry axis): H1=0, H2=0 -- Berry connection insufficient at this resolution.")

    results["interpretation"] = " | ".join(interp_parts)

    # Berry connection analytical check
    # A_phi(theta) = -sin^2(theta/2) analytically
    berry_check = []
    for theta in [0.0, np.pi / 4, np.pi / 2, np.pi]:
        A_computed = compute_berry_connection_phi(theta, 0.5)
        A_analytic = -np.sin(theta / 2) ** 2
        berry_check.append({
            "theta": float(theta),
            "A_phi_autograd": A_computed,
            "A_phi_analytic": float(A_analytic),
            "match": abs(A_computed - A_analytic) < 1e-6,
        })
    results["berry_connection_validation"] = berry_check

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "State construction, density matrices, partial traces, "
        "entropy kernels, Berry connection via autograd"
    )
    TOOL_MANIFEST["gudhi"]["used"] = True
    TOOL_MANIFEST["gudhi"]["reason"] = (
        "Rips complex persistence for K1/K2/K3 -- primary topological analysis"
    )

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # K1 should be phi-blind: equatorial states at different phi map to same point
    MI_vals = []
    re_off_vals = []
    A_phi_vals = []
    theta_eq = np.pi / 2  # equator

    for phi in np.linspace(0, 2 * np.pi, 10, endpoint=False):
        MI, cond_S, I_c, re_off, im_off = compute_qit_features(theta_eq, phi)
        A_phi = compute_berry_connection_phi(theta_eq, phi)
        MI_vals.append(MI)
        re_off_vals.append(re_off)
        A_phi_vals.append(A_phi)

    MI_spread = float(max(MI_vals) - min(MI_vals))
    re_off_spread = float(max(re_off_vals) - min(re_off_vals))
    A_phi_spread = float(max(A_phi_vals) - min(A_phi_vals))

    results["equatorial_phi_invariance"] = {
        "theta": float(theta_eq),
        "MI_spread_across_phi": MI_spread,
        "re_off_diag_spread_across_phi": re_off_spread,
        "A_phi_spread_across_phi": A_phi_spread,
        "K1_phi_blind_confirmed": MI_spread < 1e-8,
        "K2_phi_sensitive": re_off_spread > 1e-3,
        "K3_phi_sensitivity_note": "A_phi = -sin^2(theta/2) is phi-independent! Constant at equator.",
        "K3_phi_invariant_at_equator": A_phi_spread < 1e-6,
    }

    # Check poles: K1 and K3 should both collapse poles (theta=0 and theta=pi -> same MI)
    MI_north, _, I_c_north, re_north, im_north = compute_qit_features(0.0, 0.0)
    MI_south, _, I_c_south, re_south, im_south = compute_qit_features(np.pi, 0.0)
    A_north = compute_berry_connection_phi(0.0, 0.0)
    A_south = compute_berry_connection_phi(np.pi, 0.0)

    results["poles_test"] = {
        "north_pole_MI": MI_north,
        "south_pole_MI": MI_south,
        "north_A_phi": A_north,
        "south_A_phi": A_south,
        "north_re_off": re_north,
        "south_re_off": re_south,
        "poles_same_in_K1": abs(MI_north - MI_south) < 1e-8,
        "poles_distinguished_by_A_phi": abs(A_north - A_south) > 0.1,
        "note": "A_phi(0)=0, A_phi(pi)=-1: Berry connection distinguishes poles!",
    }

    results["phi_collapse_confirmed"] = {
        "K1": "phi-invisible by construction (MI/cond_S/I_c are phi-independent for this state family)",
        "K2": "phi-sensitive via Re/Im off-diagonal of rho_A",
        "K3": "A_phi = -sin^2(theta/2): phi-INDEPENDENT but THETA-sensitive -- distinguishes latitude, not longitude",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # Test poles and equator
    for name, theta, phi in [
        ("north_pole", 0.0, 0.0),
        ("south_pole", np.pi, 0.0),
        ("equator_phi0", np.pi / 2, 0.0),
        ("equator_phi_pi", np.pi / 2, np.pi),
        ("equator_phi_pi2", np.pi / 2, np.pi / 2),
    ]:
        MI, cond_S, I_c, re_off, im_off = compute_qit_features(theta, phi)
        A_phi = compute_berry_connection_phi(theta, phi)
        results[name] = {
            "theta": theta,
            "phi": phi,
            "K1": [MI, cond_S, I_c],
            "K2": [MI, cond_S, I_c, re_off, im_off],
            "K3": [MI, cond_S, I_c, A_phi],
        }

    # Confirm K2 equatorial phi sensitivity
    equator_K2 = [results[k]["K2"] for k in ["equator_phi0", "equator_phi_pi", "equator_phi_pi2"]]
    K2_distinct = len(set([tuple(v) for v in equator_K2])) == 3
    results["K2_equatorial_distinct"] = K2_distinct
    results["K2_equatorial_note"] = (
        "Equatorial states at phi=0,pi,pi/2 should map to distinct K2 points (via off-diagonal)"
        if K2_distinct else
        "WARNING: K2 equatorial points collapsed -- off-diagonal may be degenerate"
    )

    # A_phi range check
    A_phi_range = [
        compute_berry_connection_phi(theta, 0.0)
        for theta in np.linspace(0, np.pi, 20)
    ]
    results["A_phi_range"] = {
        "min": float(min(A_phi_range)),
        "max": float(max(A_phi_range)),
        "at_north": float(A_phi_range[0]),
        "at_south": float(A_phi_range[-1]),
        "note": "Analytic: A_phi in [-1, 0], A_phi(0)=0, A_phi(pi)=-1",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running GUDHI phase-sensitive kernel sim...")

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    results = {
        "name": "gudhi_phase_sensitive_kernel",
        "description": (
            "Three kernel embeddings of 10x10 Bloch sphere family. "
            "K1=(MI,cond_S,I_c) phi-blind baseline; "
            "K2 adds off-diagonal rho_A for phase sensitivity; "
            "K3 adds Berry connection A_phi = i<psi|d/dphi|psi> via autograd. "
            "Tests whether H2 (S^2 topology) or H1 (equatorial loop) emerge."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "gudhi_phase_sensitive_kernel_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    # Print summary
    kt = positive.get("key_tests", {})
    print("\n=== KEY RESULTS ===")
    print(f"K1 (phi-blind)   H1={positive['K1_phi_blind']['topology']['H1_total']} H2={positive['K1_phi_blind']['topology']['H2_total']}")
    print(f"K2 (phase-aware) H1={positive['K2_phase_aware']['topology']['H1_total']} H2={positive['K2_phase_aware']['topology']['H2_total']}")
    print(f"K3 (Berry axis)  H1={positive['K3_berry_axis']['topology']['H1_total']} H2={positive['K3_berry_axis']['topology']['H2_total']}")
    print(f"\nK2 restores S2: {kt.get('K2_restores_S2')}")
    print(f"K3 restores S2: {kt.get('K3_restores_S2')}")
    print(f"K3 equatorial loop (H1): {kt.get('K3_shows_equatorial_loop')}")
    print(f"\nInterpretation: {positive.get('interpretation')}")
