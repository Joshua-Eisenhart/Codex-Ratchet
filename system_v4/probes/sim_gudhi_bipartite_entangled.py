#!/usr/bin/env python3
"""
sim_gudhi_bipartite_entangled.py

Tests three kernel embeddings using GENUINELY ENTANGLED two-qubit states
rho_AB(theta, phi) = |psi><psi| where |psi> = cos(t/2)|00> + e^{i*phi}*sin(t/2)|11>.

Previous sims used single-qubit or rho_A off-diagonal (which is always zero for Bell
family). This sim fixes the degeneracy by using rho_AB[0,3] off-diagonal (joint system).

K1 (phi-blind):   (MI, cond_S, I_c) -- phi-invariant for Bell family, expect trivial
K2 (phase-aware): (MI, cond_S, I_c, Re[rho_AB[0,3]], Im[rho_AB[0,3]]) -- joint off-diag
K3 (Berry axis):  K2 + Berry phase A_phi = -sin^2(theta/2) for bipartite state

For the Bell family:
  rho_AB[0,3] = <00|rho_AB|11> = cos(t/2)*e^{-i*phi}*sin(t/2)
              = (sin(theta)/2) * e^{-i*phi}
  Re[rho_AB[0,3]] = sin(theta)/2 * cos(phi)   -- oscillates with phi!
  Im[rho_AB[0,3]] = -sin(theta)/2 * sin(phi)  -- oscillates with phi!

Key prediction: K2 with joint off-diagonal restores phi variation in point cloud
and should yield H1 (equatorial circle) or H2 (sphere topology).
"""

import json
import os
import numpy as np
classification = "classical_baseline"  # auto-backfill

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
# QUANTUM STATE MACHINERY -- BIPARTITE TWO-QUBIT BELL FAMILY
# =====================================================================

def bell_state_vector(theta, phi):
    """
    Two-qubit Bell-family state:
      |psi(theta,phi)> = cos(theta/2)|00> + e^{i*phi}*sin(theta/2)|11>

    Basis ordering: |00>=0, |01>=1, |10>=2, |11>=3
    Returns (psi_re, psi_im) as torch float64 tensors of shape [4].
    """
    t = torch.tensor(theta, dtype=torch.float64)
    p = torch.tensor(phi, dtype=torch.float64)
    alpha = torch.cos(t / 2)
    beta = torch.sin(t / 2)

    psi_re = torch.zeros(4, dtype=torch.float64)
    psi_im = torch.zeros(4, dtype=torch.float64)
    # |00> component: alpha (real)
    psi_re[0] = alpha
    # |11> component: beta * e^{i*phi} = beta*(cos(phi) + i*sin(phi))
    psi_re[3] = beta * torch.cos(p)
    psi_im[3] = beta * torch.sin(p)

    return psi_re, psi_im


def rho_ab_from_psi(psi_re, psi_im):
    """
    Density matrix rho_AB = |psi><psi|.
    rho[i,j] = (psi_re[i] + i*psi_im[i]) * (psi_re[j] - i*psi_im[j])
    Returns (rho_re, rho_im) each [4,4] float64.
    """
    rho_re = torch.outer(psi_re, psi_re) + torch.outer(psi_im, psi_im)
    rho_im = torch.outer(psi_im, psi_re) - torch.outer(psi_re, psi_im)
    return rho_re, rho_im


def partial_trace_A(rho_re, rho_im):
    """
    Trace out qubit B: rho_A[i,j] = sum_k rho[i*2+k, j*2+k]
    Returns (rho_A_re, rho_A_im) each [2,2].
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
    Trace out qubit A: rho_B[i,j] = sum_k rho[k*2+i, k*2+j]
    Returns (rho_B_re, rho_B_im) each [2,2].
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
    """S = -Tr(rho * log2(rho)) via eigendecomposition."""
    rho_np = rho_re.numpy() + 1j * rho_im.numpy()
    evals = np.linalg.eigvalsh(rho_np)
    evals = np.clip(evals, 1e-15, None)
    return float(-np.sum(evals * np.log2(evals)))


def compute_all_features(theta, phi):
    """
    Compute all kernel features for Bell state |psi(theta,phi)>.

    Returns dict with:
      MI, cond_S, I_c    -- phi-blind for Bell family
      re_rhoAB_03        -- Re[rho_AB[0,3]] = sin(theta)/2 * cos(phi)  [phi-sensitive!]
      im_rhoAB_03        -- Im[rho_AB[0,3]] = -sin(theta)/2 * sin(phi) [phi-sensitive!]
      A_phi_berry        -- Berry connection = -sin^2(theta/2)          [phi-independent]

    Analytic cross-checks:
      MI = 2*H2(sin^2(theta/2)) for pure state  [same as S_A since S_AB=0]
      S_A = S_B = H2(sin^2(theta/2)) = -p*log2(p) - (1-p)*log2(1-p), p=sin^2(theta/2)
      I_c = S_B - S_AB = S_B (since S_AB=0 for pure state)
      rho_AB[0,3] = cos(theta/2)*sin(theta/2)*e^{-i*phi} = (sin(theta)/2)*e^{-i*phi}
    """
    psi_re, psi_im = bell_state_vector(theta, phi)
    rho_re, rho_im = rho_ab_from_psi(psi_re, psi_im)

    # Entropies
    S_AB = von_neumann_entropy(rho_re, rho_im)  # Should be ~0 (pure state)
    rho_A_re, rho_A_im = partial_trace_A(rho_re, rho_im)
    rho_B_re, rho_B_im = partial_trace_B(rho_re, rho_im)
    S_A = von_neumann_entropy(rho_A_re, rho_A_im)
    S_B = von_neumann_entropy(rho_B_re, rho_B_im)

    MI = float(S_A + S_B - S_AB)
    cond_S = float(S_AB - S_A)  # S(AB|A) = S_AB - S_A; negative = entangled
    I_c = float(S_B - S_AB)     # coherent info = S_B - S_AB

    # KEY FIX: Use joint rho_AB[0,3] off-diagonal, NOT rho_A off-diagonal
    # rho_AB[0,3] = <00|rho_AB|11> = alpha * conj(beta*e^{i*phi})
    #             = cos(theta/2)*sin(theta/2)*e^{-i*phi}
    # rho_re[0,3] = sin(theta)/2 * cos(phi)
    # rho_im[0,3] = -sin(theta)/2 * sin(phi)
    re_rhoAB_03 = float(rho_re[0, 3])
    im_rhoAB_03 = float(rho_im[0, 3])

    # Berry connection: A_phi = -sin^2(theta/2) for |psi(theta,phi)>
    # This is phi-independent but theta-sensitive
    A_phi = -float(np.sin(theta / 2) ** 2)

    # Analytic cross-check values
    p = float(np.sin(theta / 2) ** 2)
    if p > 1e-10 and p < 1 - 1e-10:
        H2_analytic = float(-p * np.log2(p) - (1 - p) * np.log2(1 - p))
    else:
        H2_analytic = 0.0

    return {
        "MI": MI,
        "cond_S": cond_S,
        "I_c": I_c,
        "re_rhoAB_03": re_rhoAB_03,
        "im_rhoAB_03": im_rhoAB_03,
        "A_phi_berry": A_phi,
        "S_AB": float(S_AB),
        "S_A": float(S_A),
        "S_B": float(S_B),
        "H2_analytic": H2_analytic,
        "MI_analytic": 2.0 * H2_analytic,
        "re_rhoAB_03_analytic": float(np.sin(theta) / 2 * np.cos(phi)),
        "im_rhoAB_03_analytic": float(-np.sin(theta) / 2 * np.sin(phi)),
    }


# =====================================================================
# GUDHI PERSISTENCE
# =====================================================================

def run_rips_persistence(point_cloud, max_edge_length=None, max_dimension=2):
    """Run GUDHI Rips complex and return H0/H1/H2 persistence summary."""
    if max_edge_length is None:
        # Use 3x median pairwise distance from a sample of points
        n = len(point_cloud)
        sample_size = min(n, 30)
        dists = []
        for i in range(sample_size):
            for j in range(i + 1, sample_size):
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
            "max_persistence": float(max_pers),
            "sample_finite_bars": [[float(b), float(d)] for b, d in finite[:10]],
        }

    return summary, float(max_edge_length)


def summarize_topology(rips_summary):
    """Extract topology classification from persistence summary."""
    H1 = rips_summary.get("H1", {})
    H2 = rips_summary.get("H2", {})

    H1_inf = H1.get("infinite_bars", 0)
    H2_inf = H2.get("infinite_bars", 0)
    H1_max = H1.get("max_persistence", 0.0)
    H2_max = H2.get("max_persistence", 0.0)
    H1_total = H1.get("total", 0)
    H2_total = H2.get("total", 0)

    # Use persistence threshold to filter noise
    H1_significant = H1_max > 1e-4
    H2_significant = H2_max > 1e-4

    return {
        "H0_total": rips_summary.get("H0", {}).get("total", 0),
        "H1_total": H1_total,
        "H2_total": H2_total,
        "H1_infinite": H1_inf,
        "H2_infinite": H2_inf,
        "H1_max_persistence": H1_max,
        "H2_max_persistence": H2_max,
        "H1_significant": H1_significant,
        "H2_significant": H2_significant,
        "sphere_topology_S2": H2_significant and H2_max > 0.1,
        "circle_topology_S1": H1_significant and H1_max > 0.1,
        "trivial": not H1_significant and not H2_significant,
    }


def build_point_clouds(thetas, phis):
    """
    Build K1/K2/K3 point clouds from all (theta,phi) combinations.
    Returns (K1_arr, K2_arr, K3_arr, all_features).
    """
    K1_points = []  # (MI, cond_S, I_c)
    K2_points = []  # (MI, cond_S, I_c, re_rhoAB_03, im_rhoAB_03)
    K3_points = []  # (MI, cond_S, I_c, re_rhoAB_03, im_rhoAB_03, A_phi)
    all_features = []

    for theta in thetas:
        for phi in phis:
            f = compute_all_features(theta, phi)
            K1_points.append([f["MI"], f["cond_S"], f["I_c"]])
            K2_points.append([f["MI"], f["cond_S"], f["I_c"],
                               f["re_rhoAB_03"], f["im_rhoAB_03"]])
            K3_points.append([f["MI"], f["cond_S"], f["I_c"],
                               f["re_rhoAB_03"], f["im_rhoAB_03"],
                               f["A_phi_berry"]])
            all_features.append({"theta": float(theta), "phi": float(phi), **f})

    return (np.array(K1_points), np.array(K2_points),
            np.array(K3_points), all_features)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # 10x10 grid: 10 theta values x 10 phi values = 100 states
    N_theta = 10
    N_phi = 10
    thetas = np.linspace(0, np.pi, N_theta)
    phis = np.linspace(0, 2 * np.pi, N_phi, endpoint=False)

    K1_arr, K2_arr, K3_arr, all_features = build_point_clouds(thetas, phis)

    results["n_states"] = len(all_features)
    results["grid"] = {"N_theta": N_theta, "N_phi": N_phi}
    results["point_cloud_shapes"] = {
        "K1": list(K1_arr.shape),
        "K2": list(K2_arr.shape),
        "K3": list(K3_arr.shape),
    }

    # Sample to verify analytic values
    results["feature_sample"] = all_features[:6]

    # Verify analytic predictions
    analytic_checks = []
    for f in all_features[:10]:
        re_err = abs(f["re_rhoAB_03"] - f["re_rhoAB_03_analytic"])
        im_err = abs(f["im_rhoAB_03"] - f["im_rhoAB_03_analytic"])
        MI_err = abs(f["MI"] - f["MI_analytic"])
        analytic_checks.append({
            "theta": f["theta"],
            "phi": f["phi"],
            "re_error": float(re_err),
            "im_error": float(im_err),
            "MI_error": float(MI_err),
            "S_AB_near_zero": f["S_AB"] < 1e-10,
        })
    results["analytic_validation"] = analytic_checks
    results["analytic_all_pass"] = all(
        c["re_error"] < 1e-10 and c["im_error"] < 1e-10 and c["MI_error"] < 1e-10
        for c in analytic_checks
    )

    # Check phi variation in K2 features
    # At theta=pi/2 (max entanglement): re_rhoAB_03 = cos(phi)/2, im = -sin(phi)/2
    # These should vary over full [-0.5, 0.5] range as phi sweeps 0 to 2pi
    equatorial_features = [f for f in all_features if abs(f["theta"] - np.pi / 2) < 0.01]
    if equatorial_features:
        re_vals = [f["re_rhoAB_03"] for f in equatorial_features]
        im_vals = [f["im_rhoAB_03"] for f in equatorial_features]
        results["equatorial_phi_variation"] = {
            "n_states": len(equatorial_features),
            "re_rhoAB_03_range": [float(min(re_vals)), float(max(re_vals))],
            "im_rhoAB_03_range": [float(min(im_vals)), float(max(im_vals))],
            "phi_sensitive_confirmed": (max(re_vals) - min(re_vals)) > 0.8,
        }

    # Run GUDHI for each kernel
    for label, arr in [
        ("K1_phi_blind", K1_arr),
        ("K2_phase_aware", K2_arr),
        ("K3_berry_extended", K3_arr),
    ]:
        rips_summary, max_edge = run_rips_persistence(arr)
        topo = summarize_topology(rips_summary)
        results[label] = {
            "rips_max_edge_length": max_edge,
            "rips": rips_summary,
            "topology": topo,
        }

    # Key result tests
    K1_topo = results["K1_phi_blind"]["topology"]
    K2_topo = results["K2_phase_aware"]["topology"]
    K3_topo = results["K3_berry_extended"]["topology"]

    results["key_tests"] = {
        # Negative: K1 must be trivial (phi-blind)
        "K1_trivial_confirmed": K1_topo["trivial"],
        "K1_H1_detected": K1_topo["H1_significant"],
        "K1_H2_detected": K1_topo["H2_significant"],
        # Positive: K2 should show H1 or H2
        "K2_H1_detected": K2_topo["circle_topology_S1"],
        "K2_H2_detected": K2_topo["sphere_topology_S2"],
        "K2_nontrivial": not K2_topo["trivial"],
        # K3 with Berry axis
        "K3_H1_detected": K3_topo["circle_topology_S1"],
        "K3_H2_detected": K3_topo["sphere_topology_S2"],
        "K3_nontrivial": not K3_topo["trivial"],
        # Success criteria
        "phase_sensitivity_restored": not K1_topo["trivial"] is False and not K2_topo["trivial"],
    }

    # Diagnose K2 if still trivial
    if K2_topo["trivial"]:
        # Check: are MI/cond_S still phi-blind for Bell family? Yes they are.
        # The re/im off-diagonal are phi-sensitive but may be too small to
        # overcome the phi-blind dimensions if not normalized
        K2_unique_rows = len(np.unique(K2_arr, axis=0))
        K2_phi_variation = float(np.std(K2_arr[:, 3]))  # std of re_rhoAB_03

        # Also check: what is the scale ratio between phi-blind and phi-sensitive dims?
        MI_scale = float(np.std(K2_arr[:, 0]))
        re_scale = float(np.std(K2_arr[:, 3]))
        im_scale = float(np.std(K2_arr[:, 4]))

        results["K2_diagnosis"] = {
            "unique_rows": K2_unique_rows,
            "n_total_rows": len(K2_arr),
            "phi_variation_std_re": K2_phi_variation,
            "MI_std": MI_scale,
            "re_rhoAB_std": re_scale,
            "im_rhoAB_std": im_scale,
            "scale_ratio_re_to_MI": float(re_scale / MI_scale) if MI_scale > 0 else float("inf"),
            "diagnosis": (
                "re/im dimensions have lower std than MI -- "
                "phi-blind dimensions may dominate the Rips distance metric"
                if re_scale < MI_scale else
                "re/im dimensions have comparable scale to MI -- "
                "topology should be detectable"
            ),
        }

    # Interpretation
    parts = []
    if K1_topo["trivial"]:
        parts.append("K1: TRIVIAL (H1=H2=0) -- phi-blind collapse confirmed for Bell family.")
    else:
        parts.append(f"K1: NON-TRIVIAL H1={K1_topo['H1_significant']} H2={K1_topo['H2_significant']} -- unexpected.")

    if K2_topo["sphere_topology_S2"]:
        parts.append("K2: S^2 TOPOLOGY (H2>0) -- joint off-diagonal rho_AB[0,3] restores sphere topology!")
    elif K2_topo["circle_topology_S1"]:
        parts.append("K2: S^1 TOPOLOGY (H1>0, H2=0) -- equatorial circle detected, phi variation present.")
    else:
        parts.append(
            f"K2: TRIVIAL (H1={K2_topo['H1_max_persistence']:.4f}, H2={K2_topo['H2_max_persistence']:.4f}) "
            f"-- joint off-diagonal insufficient at this resolution or scale."
        )

    if K3_topo["sphere_topology_S2"]:
        parts.append("K3: S^2 TOPOLOGY (H2>0) -- Berry axis extends K2 to full sphere detection.")
    elif K3_topo["circle_topology_S1"]:
        parts.append("K3: S^1 TOPOLOGY (H1>0) -- circle from Berry axis theta variation.")
    else:
        parts.append("K3: TRIVIAL -- Berry extension does not add topology at this resolution.")

    results["interpretation"] = " | ".join(parts)

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Bell state construction, bipartite density matrix, partial traces, "
        "von Neumann entropy via numpy eigvalsh"
    )
    TOOL_MANIFEST["gudhi"]["used"] = True
    TOOL_MANIFEST["gudhi"]["reason"] = (
        "RipsComplex + compute_persistence for K1/K2/K3 -- primary topological analysis tool"
    )

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    K1 must be phi-blind: all equatorial states collapse to same K1 point.
    K2 must be phi-sensitive: equatorial states must map to distinct K2 points.
    """
    results = {}

    theta_eq = np.pi / 2  # maximum entanglement
    phis_test = np.linspace(0, 2 * np.pi, 20, endpoint=False)

    K1_equatorial = []
    K2_equatorial = []
    feature_details = []

    for phi in phis_test:
        f = compute_all_features(theta_eq, phi)
        K1_equatorial.append([f["MI"], f["cond_S"], f["I_c"]])
        K2_equatorial.append([f["MI"], f["cond_S"], f["I_c"],
                               f["re_rhoAB_03"], f["im_rhoAB_03"]])
        feature_details.append({
            "phi": float(phi),
            "MI": f["MI"],
            "re_rhoAB_03": f["re_rhoAB_03"],
            "im_rhoAB_03": f["im_rhoAB_03"],
        })

    K1_arr = np.array(K1_equatorial)
    K2_arr = np.array(K2_equatorial)

    # K1: all rows should be identical (phi-blind)
    K1_unique = len(np.unique(K1_arr.round(12), axis=0))
    K1_MI_spread = float(np.max(K1_arr[:, 0]) - np.min(K1_arr[:, 0]))

    # K2: rows should form a circle in the re/im plane
    K2_unique = len(np.unique(K2_arr.round(10), axis=0))
    re_vals = K2_arr[:, 3]
    im_vals = K2_arr[:, 4]
    # For Bell family at theta=pi/2: re=cos(phi)/2, im=-sin(phi)/2 -- circle of radius 0.5
    radius = float(np.mean(np.sqrt(re_vals**2 + im_vals**2)))
    radius_std = float(np.std(np.sqrt(re_vals**2 + im_vals**2)))
    re_range = float(np.max(re_vals) - np.min(re_vals))
    im_range = float(np.max(im_vals) - np.min(im_vals))

    results["equatorial_K1_phi_blind"] = {
        "theta": float(theta_eq),
        "n_phi_tested": len(phis_test),
        "K1_unique_rows": K1_unique,
        "K1_MI_spread": K1_MI_spread,
        "K1_phi_blind_confirmed": K1_unique == 1 and K1_MI_spread < 1e-10,
    }

    results["equatorial_K2_phi_sensitive"] = {
        "theta": float(theta_eq),
        "K2_unique_rows": K2_unique,
        "re_rhoAB_03_range": re_range,
        "im_rhoAB_03_range": im_range,
        "circle_radius_mean": radius,
        "circle_radius_std": radius_std,
        "forms_circle_confirmed": (
            K2_unique == len(phis_test) and re_range > 0.8 and im_range > 0.8
        ),
        "expected_radius": 0.5,
        "note": "Bell |psi(pi/2,phi)>: rho_AB[0,3] traces circle of radius 0.5 in Re/Im plane",
    }

    results["feature_details_sample"] = feature_details[:8]

    # Also test: rho_A off-diagonal at equator for comparison
    f_eq = compute_all_features(theta_eq, 0.0)
    # rho_A for Bell state at any theta is diagonal: rho_A = diag(cos^2(t/2), sin^2(t/2))
    # So rho_A off-diagonal = 0 always -- this was the bug in previous sim
    results["rho_A_off_diagonal_check"] = {
        "note": (
            "rho_A for Bell family cos(t/2)|00>+e^{i*phi}sin(t/2)|11> is always diagonal "
            "(rho_A = cos^2(t/2)|0><0| + sin^2(t/2)|1><1|), so rho_A[0,1]=0 always. "
            "Previous sims using rho_A off-diagonal were always phi-blind. "
            "This sim uses rho_AB[0,3] (joint system) which is phi-sensitive."
        ),
        "rho_A_off_diag_at_equator_phi0": {
            "MI": f_eq["MI"],
            "S_A": f_eq["S_A"],
            "re_rhoAB_03": f_eq["re_rhoAB_03"],
            "im_rhoAB_03": f_eq["im_rhoAB_03"],
        },
        "rho_AB_03_phi_sensitive_confirmed": abs(f_eq["re_rhoAB_03"]) > 0.4,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Test poles (theta=0,pi) and maximal entanglement (theta=pi/2).
    At poles: rho_AB is a product state (|00> or |11>), no entanglement.
    At equator: maximal entanglement (Bell state proper).
    """
    results = {}

    test_cases = [
        ("north_pole_theta0_phi0", 0.0, 0.0),
        ("south_pole_thetaPi_phi0", np.pi, 0.0),
        ("equator_max_entangle_phi0", np.pi / 2, 0.0),
        ("equator_max_entangle_phiPi", np.pi / 2, np.pi),
        ("equator_max_entangle_phiPi2", np.pi / 2, np.pi / 2),
        ("equator_max_entangle_phi3Pi2", np.pi / 2, 3 * np.pi / 2),
    ]

    for name, theta, phi in test_cases:
        f = compute_all_features(theta, phi)
        results[name] = {
            "theta": float(theta),
            "phi": float(phi),
            "K1": [f["MI"], f["cond_S"], f["I_c"]],
            "K2": [f["MI"], f["cond_S"], f["I_c"],
                   f["re_rhoAB_03"], f["im_rhoAB_03"]],
            "K3_extra": [f["re_rhoAB_03"], f["im_rhoAB_03"], f["A_phi_berry"]],
            "S_AB": f["S_AB"],
            "S_A": f["S_A"],
            "entanglement_entropy": f["S_A"],
        }

    # Confirm K2 equatorial points are distinct (K1 must all have same first 3 coords)
    equatorial_K2 = [
        results["equator_max_entangle_phi0"]["K2"],
        results["equator_max_entangle_phiPi"]["K2"],
        results["equator_max_entangle_phiPi2"]["K2"],
        results["equator_max_entangle_phi3Pi2"]["K2"],
    ]
    K2_tuples = [tuple(round(x, 12) for x in v) for v in equatorial_K2]
    K2_distinct = len(set(K2_tuples)) == 4

    equatorial_K1 = [v[:3] for v in equatorial_K2]
    K1_tuples = [tuple(round(x, 12) for x in v) for v in equatorial_K1]
    K1_collapsed = len(set(K1_tuples)) == 1

    results["equatorial_K1_collapse_confirmed"] = K1_collapsed
    results["equatorial_K2_distinct_confirmed"] = K2_distinct
    results["boundary_summary"] = {
        "K1_collapses_phi": K1_collapsed,
        "K2_distinguishes_phi": K2_distinct,
        "fix_validated": K1_collapsed and K2_distinct,
        "note": (
            "K1 collapses phi (phi-blind), K2 distinguishes phi via rho_AB[0,3]. "
            "This is the core fix over previous sims."
        ),
    }

    # Point cloud geometry at theta=pi/2 slice
    phis_fine = np.linspace(0, 2 * np.pi, 20, endpoint=False)
    equatorial_ring_K2 = []
    for phi in phis_fine:
        f = compute_all_features(np.pi / 2, phi)
        equatorial_ring_K2.append([f["MI"], f["cond_S"], f["I_c"],
                                    f["re_rhoAB_03"], f["im_rhoAB_03"]])
    ring_arr = np.array(equatorial_ring_K2)

    # The ring should trace a circle in dims 3,4 (re/im)
    re_center = float(np.mean(ring_arr[:, 3]))
    im_center = float(np.mean(ring_arr[:, 4]))
    radii = np.sqrt((ring_arr[:, 3] - re_center)**2 + (ring_arr[:, 4] - im_center)**2)
    results["equatorial_ring_geometry"] = {
        "n_points": len(ring_arr),
        "re_center": re_center,
        "im_center": im_center,
        "mean_radius": float(np.mean(radii)),
        "radius_std": float(np.std(radii)),
        "forms_clean_circle": float(np.std(radii)) < 0.01,
        "circle_radius_expected": 0.5,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running GUDHI bipartite entangled Bell family sim...")
    print("Using rho_AB[0,3] joint off-diagonal (phi-sensitive) -- fixing previous sim degeneracy.")

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    results = {
        "name": "gudhi_bipartite_entangled",
        "description": (
            "Three kernel embeddings of 100 Bell-family states "
            "|psi(theta,phi)> = cos(theta/2)|00> + e^{i*phi}sin(theta/2)|11>. "
            "K1=(MI,cond_S,I_c): phi-blind -- negative control. "
            "K2=(MI,cond_S,I_c,Re[rho_AB[0,3]],Im[rho_AB[0,3]]): joint off-diagonal -- phi-sensitive. "
            "K3=K2+Berry(A_phi=-sin^2(theta/2)). "
            "Fix over previous sim: uses rho_AB joint off-diagonal, NOT rho_A off-diagonal "
            "(rho_A for Bell family is always diagonal, so previous K2 was still phi-blind)."
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
    out_path = os.path.join(out_dir, "gudhi_bipartite_entangled_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    # Print summary
    print("\n=== KEY RESULTS ===")
    pos = positive
    kt = pos.get("key_tests", {})
    K1 = pos.get("K1_phi_blind", {}).get("topology", {})
    K2 = pos.get("K2_phase_aware", {}).get("topology", {})
    K3 = pos.get("K3_berry_extended", {}).get("topology", {})

    print(f"K1 (phi-blind):      H1={K1.get('H1_total',0)} H2={K1.get('H2_total',0)} "
          f"trivial={K1.get('trivial',False)}")
    print(f"K2 (joint off-diag): H1={K2.get('H1_total',0)} H2={K2.get('H2_total',0)} "
          f"H1_max={K2.get('H1_max_persistence',0.0):.4f} H2_max={K2.get('H2_max_persistence',0.0):.4f}")
    print(f"K3 (Berry extended): H1={K3.get('H1_total',0)} H2={K3.get('H2_total',0)} "
          f"H1_max={K3.get('H1_max_persistence',0.0):.4f} H2_max={K3.get('H2_max_persistence',0.0):.4f}")

    neg = negative
    K1_blind = neg.get("equatorial_K1_phi_blind", {})
    K2_sens = neg.get("equatorial_K2_phi_sensitive", {})
    print(f"\nK1 phi-blind confirmed: {K1_blind.get('K1_phi_blind_confirmed')}")
    print(f"K2 forms circle:        {K2_sens.get('forms_circle_confirmed')} "
          f"(radius={K2_sens.get('circle_radius_mean', 0.0):.4f}, expected=0.5)")

    bnd = boundary
    print(f"\nBoundary: K1 collapses phi={bnd.get('equatorial_K1_collapse_confirmed')}, "
          f"K2 distinguishes phi={bnd.get('equatorial_K2_distinct_confirmed')}")

    analytic_ok = pos.get("analytic_all_pass", False)
    print(f"Analytic cross-check pass: {analytic_ok}")
    print(f"\nInterpretation: {pos.get('interpretation', 'N/A')}")
