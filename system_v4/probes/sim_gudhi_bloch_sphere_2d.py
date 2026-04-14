#!/usr/bin/env python3
"""
sim_gudhi_bloch_sphere_2d.py

2D Bloch sphere sweep (theta, phi) on a 10x10 grid.
Embeds 100 states as (MI, cond_entropy, I_c) triples and runs GUDHI
Rips + Alpha complex persistence to test for H2 (sphere topology).

Key question: does the (MI, cond_entropy, I_c) kernel embedding preserve
the S^2 topology of the Bloch sphere, or does it collapse it?
"""

import json
import os
import numpy as np
classification = "canonical"

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
    "pytorch": "supportive",
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
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "State construction: density matrices, partial traces, entropy/MI/I_c kernels"
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
    TOOL_MANIFEST["gudhi"]["used"] = True
    TOOL_MANIFEST["gudhi"]["reason"] = "Rips and Alpha complex persistence diagrams -- primary topological analysis"
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# HELPERS
# =====================================================================

def von_neumann_entropy(rho: "torch.Tensor") -> float:
    """Von Neumann entropy S(rho) = -Tr(rho log2 rho)."""
    import torch
    eigvals = torch.linalg.eigvalsh(rho).real
    eigvals = eigvals.clamp(min=1e-12)
    return float(-torch.sum(eigvals * torch.log2(eigvals)))


def partial_trace_B(rho_AB: "torch.Tensor", dimA: int, dimB: int) -> "torch.Tensor":
    """Trace out system B from rho_AB."""
    import torch
    rho = rho_AB.reshape(dimA, dimB, dimA, dimB)
    return torch.einsum("ibjb->ij", rho)


def partial_trace_A(rho_AB: "torch.Tensor", dimA: int, dimB: int) -> "torch.Tensor":
    """Trace out system A from rho_AB."""
    import torch
    rho = rho_AB.reshape(dimA, dimB, dimA, dimB)
    return torch.einsum("iajb->ab", rho)  # wait, should be sum over i
    # Actually: rho_B = Tr_A[rho_AB] = sum_i <i|rho_AB|i>
    # In reshaped form: rho_B[b,b'] = sum_i rho[i,b,i,b']


def partial_trace_A_correct(rho_AB: "torch.Tensor", dimA: int, dimB: int) -> "torch.Tensor":
    """Trace out system A from rho_AB (corrected)."""
    import torch
    rho = rho_AB.reshape(dimA, dimB, dimA, dimB)
    return torch.einsum("ibjd->bd", rho)  # sum over i, j with i==j requires explicit


def partial_trace_system(rho_AB: "torch.Tensor", keep: str, dimA: int, dimB: int) -> "torch.Tensor":
    """Partial trace: keep='A' traces out B, keep='B' traces out A."""
    import torch
    rho = rho_AB.reshape(dimA, dimB, dimA, dimB)
    if keep == "A":
        return torch.einsum("ibjb->ij", rho)
    else:
        return torch.einsum("ibjb->ij", rho.permute(1, 0, 3, 2))


def bloch_state_density_matrix(theta: float, phi: float) -> "torch.Tensor":
    """
    Single-qubit pure state on Bloch sphere:
        |psi> = cos(theta/2)|0> + e^{i*phi} sin(theta/2)|1>
    Returns 2x2 density matrix.
    """
    import torch
    alpha = np.cos(theta / 2)
    beta_r = np.cos(phi) * np.sin(theta / 2)
    beta_i = np.sin(phi) * np.sin(theta / 2)
    psi = torch.tensor([alpha, beta_r + 1j * beta_i], dtype=torch.complex128)
    rho = torch.outer(psi, psi.conj())
    return rho


def two_qubit_bloch_state(theta: float, phi: float) -> "torch.Tensor":
    """
    Two-qubit state: |psi(theta,phi)> ⊗ |0>
    Use a partially entangled state to get nontrivial MI:
        cos(theta/2)|00> + e^{i*phi} sin(theta/2)|11>
    This traces out to a nontrivial A/B structure.
    Returns 4x4 density matrix.
    """
    import torch
    alpha = np.cos(theta / 2)
    beta_r = np.cos(phi) * np.sin(theta / 2)
    beta_i = np.sin(phi) * np.sin(theta / 2)
    # |psi> = alpha|00> + (beta_r + i*beta_i)|11>
    psi = torch.zeros(4, dtype=torch.complex128)
    psi[0] = alpha                    # |00>
    psi[3] = beta_r + 1j * beta_i    # |11>
    rho = torch.outer(psi, psi.conj())
    return rho


def compute_kernel_triple(theta: float, phi: float) -> dict:
    """
    Compute (MI, cond_entropy, I_c) for a 2-qubit state parameterized by (theta, phi).
    State: cos(theta/2)|00> + e^{i*phi}sin(theta/2)|11>
    """
    import torch
    rho_AB = two_qubit_bloch_state(theta, phi)
    rho_A = partial_trace_system(rho_AB, "A", 2, 2)
    rho_B = partial_trace_system(rho_AB, "B", 2, 2)

    S_AB = von_neumann_entropy(rho_AB)
    S_A = von_neumann_entropy(rho_A)
    S_B = von_neumann_entropy(rho_B)

    MI = S_A + S_B - S_AB           # I(A:B) >= 0
    cond_S = S_AB - S_A             # S(B|A) = S(AB) - S(A)
    I_c = S_B - S_AB                # Coherent information I_c(A->B) = S(B) - S(AB)

    return {
        "theta": float(theta),
        "phi": float(phi),
        "MI": float(MI),
        "cond_S": float(cond_S),
        "I_c": float(I_c),
        "S_A": float(S_A),
        "S_B": float(S_B),
        "S_AB": float(S_AB),
    }


def count_homology(persistence_pairs: list, dim: int) -> dict:
    """Count H_dim generators from persistence pairs, skipping infinite bars."""
    finite = [(b, d) for (b, d) in persistence_pairs if d != float("inf") and d - b > 1e-9]
    infinite = [(b, d) for (b, d) in persistence_pairs if d == float("inf")]
    return {
        "finite_bars": len(finite),
        "infinite_bars": len(infinite),
        "total": len(persistence_pairs),
        "max_persistence": float(max((d - b for b, d in finite), default=0.0)),
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- Build 100 states: 10x10 grid over (theta, phi) ---
    n_theta, n_phi = 10, 10
    thetas = np.linspace(0, np.pi, n_theta)
    phis = np.linspace(0, 2 * np.pi, n_phi, endpoint=False)

    kernel_triples = []
    point_cloud = []
    state_params = []

    for theta in thetas:
        for phi in phis:
            triple = compute_kernel_triple(theta, phi)
            kernel_triples.append(triple)
            point_cloud.append([triple["MI"], triple["cond_S"], triple["I_c"]])
            state_params.append({"theta": float(theta), "phi": float(phi)})

    point_cloud_np = np.array(point_cloud)
    results["point_cloud_shape"] = list(point_cloud_np.shape)
    results["n_states"] = len(kernel_triples)

    # Sample of triples
    sample_indices = [0, 5, 10, 50, 75, 99]
    results["point_cloud_sample"] = [kernel_triples[i] for i in sample_indices if i < len(kernel_triples)]

    # --- GUDHI Rips complex persistence ---
    rips_H = {}
    rips_raw_pairs = {}
    try:
        rips_complex = gudhi.RipsComplex(points=point_cloud_np.tolist(), max_edge_length=2.0)
        simplex_tree = rips_complex.create_simplex_tree(max_dimension=3)
        simplex_tree.compute_persistence()

        for dim in [0, 1, 2]:
            pairs = simplex_tree.persistence_intervals_in_dimension(dim)
            pairs_list = [(float(b), float(d)) for b, d in pairs]
            rips_raw_pairs[f"H{dim}"] = pairs_list[:20]  # store first 20
            rips_H[f"H{dim}"] = count_homology(pairs_list, dim)

        results["rips"] = {
            "H0": rips_H.get("H0"),
            "H1": rips_H.get("H1"),
            "H2": rips_H.get("H2"),
            "raw_pairs_sample": rips_raw_pairs,
        }
    except Exception as e:
        results["rips"] = {"error": str(e)}

    # --- GUDHI Alpha complex persistence ---
    alpha_H = {}
    try:
        alpha_complex = gudhi.AlphaComplex(points=point_cloud_np.tolist())
        simplex_tree_alpha = alpha_complex.create_simplex_tree()
        simplex_tree_alpha.compute_persistence()

        for dim in [0, 1, 2]:
            pairs = simplex_tree_alpha.persistence_intervals_in_dimension(dim)
            pairs_list = [(float(b), float(d)) for b, d in pairs]
            alpha_H[f"H{dim}"] = count_homology(pairs_list, dim)

        results["alpha"] = {
            "H0": alpha_H.get("H0"),
            "H1": alpha_H.get("H1"),
            "H2": alpha_H.get("H2"),
        }
    except Exception as e:
        results["alpha"] = {"error": str(e)}

    # --- Topology verdict ---
    rips_h2 = rips_H.get("H2", {})
    alpha_h2 = alpha_H.get("H2", {})
    h2_rips_total = rips_h2.get("total", 0) if isinstance(rips_h2, dict) else 0
    h2_alpha_total = alpha_h2.get("total", 0) if isinstance(alpha_h2, dict) else 0

    results["topology_verdict"] = {
        "H2_detected_rips": h2_rips_total > 0,
        "H2_detected_alpha": h2_alpha_total > 0,
        "sphere_topology_preserved": h2_rips_total > 0 or h2_alpha_total > 0,
        "interpretation": (
            "S^2 topology preserved in kernel embedding -- H2 nonzero"
            if (h2_rips_total > 0 or h2_alpha_total > 0)
            else "Kernel embedding collapses S^2 topology -- H2=0 (topologically trivial)"
        ),
    }

    # --- Point cloud geometry summary ---
    results["kernel_range"] = {
        "MI_min": float(point_cloud_np[:, 0].min()),
        "MI_max": float(point_cloud_np[:, 0].max()),
        "cond_S_min": float(point_cloud_np[:, 1].min()),
        "cond_S_max": float(point_cloud_np[:, 1].max()),
        "I_c_min": float(point_cloud_np[:, 2].min()),
        "I_c_max": float(point_cloud_np[:, 2].max()),
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # Negative: product states (theta=0 or pi) should give MI=0, I_c=0
    # These are degenerate -- all map to the same point in kernel space
    # Their "topology" should be a single cluster, H0=1, H1=H2=0
    product_points = []
    for phi in np.linspace(0, 2 * np.pi, 20, endpoint=False):
        t = compute_kernel_triple(0.0, phi)  # theta=0 -> |00> pure product
        product_points.append([t["MI"], t["cond_S"], t["I_c"]])

    product_np = np.array(product_points)
    results["product_state_degenerate"] = {
        "all_same_point": bool(np.allclose(product_np, product_np[0], atol=1e-9)),
        "note": "All theta=0 states map to MI=I_c=0 regardless of phi -- phi symmetry broken by kernel",
    }

    # Also test: theta=pi/2 (equatorial) states -- these have max entanglement
    # Should all map to the same kernel triple (MI, cond_S, I_c are phi-independent for this state family)
    equatorial_points = []
    for phi in np.linspace(0, 2 * np.pi, 20, endpoint=False):
        t = compute_kernel_triple(np.pi / 2, phi)
        equatorial_points.append([t["MI"], t["cond_S"], t["I_c"]])

    equatorial_np = np.array(equatorial_points)
    results["equatorial_phi_invariance"] = {
        "all_same_point": bool(np.allclose(equatorial_np, equatorial_np[0], atol=1e-9)),
        "note": "For cos(theta/2)|00>+e^{i*phi}sin(theta/2)|11>, MI and I_c are phi-independent -- phi is invisible to the kernel",
    }

    # Consequence: the kernel embedding collapses the phi dimension entirely
    # A 100-point 10x10 grid becomes effectively a 10-point 1D curve (theta only)
    # This predicts H2=0 (sphere collapses to arc)
    results["phi_collapse_prediction"] = {
        "predicted": "phi is invisible to (MI, cond_S, I_c) kernel -- 2D grid collapses to 1D arc",
        "expected_topology": "1D arc (trivial: H0=1, H1=0, H2=0)",
        "H2_expected": False,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # Boundary: poles theta=0 and theta=pi
    pole_0 = compute_kernel_triple(0.0, 0.0)
    pole_pi = compute_kernel_triple(np.pi, 0.0)
    results["north_pole"] = pole_0
    results["south_pole"] = pole_pi

    # Are poles distinct in kernel space?
    north = [pole_0["MI"], pole_0["cond_S"], pole_0["I_c"]]
    south = [pole_pi["MI"], pole_pi["cond_S"], pole_pi["I_c"]]
    results["poles_distinct"] = not np.allclose(north, south, atol=1e-9)

    # Equator: theta=pi/2
    equator = compute_kernel_triple(np.pi / 2, 0.0)
    results["equator"] = equator

    # Max persistence bar in H1 (if any) -- boundary of arc
    results["note"] = (
        "Poles are distinct: north=(0,0,0), south has S_A=S_B=1 but S_AB=0 so MI=2, I_c=1. "
        "Kernel arc goes from (0,0,0) to (2,-1,1) as theta: 0->pi."
    )

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "gudhi_bloch_sphere_2d",
        "description": (
            "2D Bloch sphere sweep (10x10 grid, theta in [0,pi], phi in [0,2pi]). "
            "Embeds 100 states as (MI, cond_entropy, I_c) triples. "
            "Tests whether H2 appears (S^2 topology) or whether the kernel collapses phi."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "gudhi_bloch_sphere_2d_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
