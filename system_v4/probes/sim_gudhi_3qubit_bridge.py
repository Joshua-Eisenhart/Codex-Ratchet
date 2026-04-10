#!/usr/bin/env python3
"""
sim_gudhi_3qubit_bridge.py

GUDHI persistent homology on the 3-qubit Fe-bridge packet family.
States: |000>, GHZ, W, Fe-bridge (XX relay on qubits 2-3), Werner-like 3q, product⊗Bell.
Embedded as (tripartite MI, I_c(A->BC), I_c(AB->C)) triples.

Key question: does removing the XX relay change topology?
If so, the relay is topologically load-bearing.
"""

import json
import os
import numpy as np

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
    TOOL_MANIFEST["pytorch"]["reason"] = "3-qubit density matrix construction, partial traces, quantum entropy kernels"
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
    TOOL_MANIFEST["gudhi"]["reason"] = "Rips complex persistence on 3-qubit kernel embedding -- primary topological analysis"
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# HELPERS
# =====================================================================

def von_neumann_entropy(rho: "torch.Tensor") -> float:
    import torch
    eigvals = torch.linalg.eigvalsh(rho).real.clamp(min=1e-12)
    return float(-torch.sum(eigvals * torch.log2(eigvals)))


def partial_trace(rho: "torch.Tensor", keep_systems: list, dims: list) -> "torch.Tensor":
    """
    General partial trace for n-qubit systems.
    keep_systems: list of system indices to KEEP (0-indexed)
    dims: list of dimensions for each system
    Returns density matrix of the kept subsystem.
    """
    import torch
    n = len(dims)
    total_dim = 1
    for d in dims:
        total_dim *= d

    # Reshape to (d0, d1, ..., dn-1, d0, d1, ..., dn-1)
    shape = dims + dims
    rho_r = rho.reshape(shape)

    trace_systems = [i for i in range(n) if i not in keep_systems]

    # Trace over each system not in keep_systems
    # We trace one at a time, adjusting indices each time
    current = rho_r
    current_n = n
    traced_count = 0

    for sys_idx in sorted(trace_systems, reverse=True):
        # Current shape: (d0..dk, d0..dk) with current_n systems in each half
        # Trace system sys_idx: einsum diagonal on (sys_idx, sys_idx + current_n)
        idx = sys_idx
        # Build einsum string
        in_labels = list(range(2 * current_n))
        # Set ket and bra of sys_idx to be same label
        bra_idx = idx + current_n
        in_labels[bra_idx] = in_labels[idx]  # contract these two

        # Build output: all labels except the traced pair
        out_labels = [l for i, l in enumerate(in_labels) if i != idx and i != bra_idx]

        # Use torch.einsum
        # Build string manually
        all_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        used = {}
        char_map = {}
        for label in in_labels:
            if label not in char_map:
                char_map[label] = all_chars[len(char_map)]
        in_str = "".join(char_map[l] for l in in_labels)
        out_str = "".join(char_map[l] for l in out_labels)
        einsum_str = f"{in_str}->{out_str}"
        current = torch.einsum(einsum_str, current)
        current_n -= 1

    # Reshape to matrix
    kept_dims = [dims[i] for i in keep_systems]
    kept_total = 1
    for d in kept_dims:
        kept_total *= d
    return current.reshape(kept_total, kept_total)


def compute_3q_kernel(rho_ABC: "torch.Tensor", name: str) -> dict:
    """
    Compute tripartite kernel triple for 3-qubit state.
    Systems: A=qubit0, B=qubit1, C=qubit2
    Kernel: (tripartite_MI, I_c(A->BC), I_c(AB->C))
    """
    import torch
    dims = [2, 2, 2]

    rho_A = partial_trace(rho_ABC, [0], dims)
    rho_B = partial_trace(rho_ABC, [1], dims)
    rho_C = partial_trace(rho_ABC, [2], dims)
    rho_AB = partial_trace(rho_ABC, [0, 1], dims)
    rho_BC = partial_trace(rho_ABC, [1, 2], dims)
    rho_AC = partial_trace(rho_ABC, [0, 2], dims)

    S_A = von_neumann_entropy(rho_A)
    S_B = von_neumann_entropy(rho_B)
    S_C = von_neumann_entropy(rho_C)
    S_AB = von_neumann_entropy(rho_AB)
    S_BC = von_neumann_entropy(rho_BC)
    S_AC = von_neumann_entropy(rho_AC)
    S_ABC = von_neumann_entropy(rho_ABC)

    # Tripartite mutual information: I(A:B:C) = S_A + S_B + S_C - S_AB - S_BC - S_AC + S_ABC
    tripartite_MI = S_A + S_B + S_C - S_AB - S_BC - S_AC + S_ABC

    # Coherent information I_c(A->BC): S(BC) - S(ABC)
    I_c_A_to_BC = S_BC - S_ABC

    # Coherent information I_c(AB->C): S(C) - S(ABC)
    I_c_AB_to_C = S_C - S_ABC

    return {
        "name": name,
        "tripartite_MI": float(tripartite_MI),
        "I_c_A_to_BC": float(I_c_A_to_BC),
        "I_c_AB_to_C": float(I_c_AB_to_C),
        "S_A": float(S_A),
        "S_B": float(S_B),
        "S_C": float(S_C),
        "S_AB": float(S_AB),
        "S_BC": float(S_BC),
        "S_ABC": float(S_ABC),
    }


def build_3q_states(include_relay: bool = True):
    """
    Build the 6 canonical 3-qubit states.
    include_relay: if False, the Fe-bridge state has XX_23 set to zero
    (relay disconnected -- becomes product-like).
    """
    import torch

    states = {}

    # 1. |000>
    psi_000 = torch.zeros(8, dtype=torch.complex128)
    psi_000[0] = 1.0
    states["000"] = torch.outer(psi_000, psi_000.conj())

    # 2. GHZ state: (|000> + |111>) / sqrt(2)
    psi_ghz = torch.zeros(8, dtype=torch.complex128)
    psi_ghz[0] = 1.0 / np.sqrt(2)
    psi_ghz[7] = 1.0 / np.sqrt(2)
    states["GHZ"] = torch.outer(psi_ghz, psi_ghz.conj())

    # 3. W state: (|100> + |010> + |001>) / sqrt(3)
    psi_w = torch.zeros(8, dtype=torch.complex128)
    psi_w[4] = 1.0 / np.sqrt(3)   # |100>
    psi_w[2] = 1.0 / np.sqrt(3)   # |010>
    psi_w[1] = 1.0 / np.sqrt(3)   # |001>
    states["W"] = torch.outer(psi_w, psi_w.conj())

    # 4. Fe-bridge-like: XX relay on qubits 1-2 (0-indexed: B and C)
    # Start from |0>_A ⊗ Bell+(BC)
    # |psi> = (1/sqrt(2))(|0>|00> + |0>|11>) = (1/sqrt(2))(|000> + |011>)
    # With relay: apply partial XX_{BC} coupling
    # XX_23 = cos(alpha)|00>+sin(alpha)|11> + cos(alpha)|11>+sin(alpha)|00> type mixing
    # Fe-bridge: alpha = pi/4 gives maximal relay
    alpha = np.pi / 4 if include_relay else 0.0
    # State: cos(alpha)|000> + sin(alpha)|011> + sin(alpha)|100> + cos(alpha)|111>)...
    # Actually more physically:
    # |0>_A ⊗ (cos(alpha)|00>_BC + i*sin(alpha)|11>_BC)
    # = cos(alpha)|000> + i*sin(alpha)|011>
    psi_fe = torch.zeros(8, dtype=torch.complex128)
    psi_fe[0] = np.cos(alpha)         # |000>
    psi_fe[3] = 1j * np.sin(alpha)    # |011> -- XX relay on BC
    states["Fe_bridge"] = torch.outer(psi_fe, psi_fe.conj())

    # 5. Werner-like 3q: p*GHZ + (1-p)*I/8, p=0.7
    p = 0.7
    eye8 = torch.eye(8, dtype=torch.complex128)
    states["Werner_3q"] = p * states["GHZ"] + (1 - p) * eye8 / 8.0

    # 6. Product ⊗ Bell: |0>_A ⊗ Bell+(BC)
    # (1/sqrt(2))(|000> + |011>)
    psi_prod_bell = torch.zeros(8, dtype=torch.complex128)
    psi_prod_bell[0] = 1.0 / np.sqrt(2)   # |000>
    psi_prod_bell[3] = 1.0 / np.sqrt(2)   # |011>
    states["Product_Bell"] = torch.outer(psi_prod_bell, psi_prod_bell.conj())

    return states


def compute_homology_summary(persistence_pairs):
    finite = [(b, d) for b, d in persistence_pairs if d != float("inf") and d - b > 1e-9]
    infinite = [(b, d) for b, d in persistence_pairs if d == float("inf")]
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

    # Build full relay family
    states_with_relay = build_3q_states(include_relay=True)
    kernel_with_relay = []
    for name, rho in states_with_relay.items():
        k = compute_3q_kernel(rho, name)
        kernel_with_relay.append(k)

    results["kernel_triples_with_relay"] = kernel_with_relay

    # Point cloud: (tripartite_MI, I_c_A_to_BC, I_c_AB_to_C)
    cloud_relay = np.array([[k["tripartite_MI"], k["I_c_A_to_BC"], k["I_c_AB_to_C"]] for k in kernel_with_relay])
    results["point_cloud_with_relay"] = cloud_relay.tolist()

    # GUDHI Rips on full relay family
    rips_relay = {}
    try:
        rips_c = gudhi.RipsComplex(points=cloud_relay.tolist(), max_edge_length=5.0)
        st = rips_c.create_simplex_tree(max_dimension=3)
        st.compute_persistence()
        for dim in [0, 1, 2]:
            pairs = st.persistence_intervals_in_dimension(dim)
            rips_relay[f"H{dim}"] = compute_homology_summary([(float(b), float(d)) for b, d in pairs])
        results["rips_with_relay"] = rips_relay
    except Exception as e:
        results["rips_with_relay"] = {"error": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS -- relay removed
# =====================================================================

def run_negative_tests():
    results = {}

    # Build NO relay family
    states_no_relay = build_3q_states(include_relay=False)
    kernel_no_relay = []
    for name, rho in states_no_relay.items():
        k = compute_3q_kernel(rho, name)
        kernel_no_relay.append(k)

    results["kernel_triples_no_relay"] = kernel_no_relay

    cloud_no_relay = np.array([[k["tripartite_MI"], k["I_c_A_to_BC"], k["I_c_AB_to_C"]] for k in kernel_no_relay])
    results["point_cloud_no_relay"] = cloud_no_relay.tolist()

    # GUDHI Rips on no-relay family
    rips_no_relay = {}
    try:
        rips_c = gudhi.RipsComplex(points=cloud_no_relay.tolist(), max_edge_length=5.0)
        st = rips_c.create_simplex_tree(max_dimension=3)
        st.compute_persistence()
        for dim in [0, 1, 2]:
            pairs = st.persistence_intervals_in_dimension(dim)
            rips_no_relay[f"H{dim}"] = compute_homology_summary([(float(b), float(d)) for b, d in pairs])
        results["rips_no_relay"] = rips_no_relay
    except Exception as e:
        results["rips_no_relay"] = {"error": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS -- topology comparison
# =====================================================================

def run_boundary_tests():
    results = {}

    # Compare H1 between relay and no-relay
    states_relay = build_3q_states(include_relay=True)
    states_no_relay = build_3q_states(include_relay=False)

    k_relay = [[k["tripartite_MI"], k["I_c_A_to_BC"], k["I_c_AB_to_C"]]
               for k in [compute_3q_kernel(rho, n) for n, rho in states_relay.items()]]
    k_no_relay = [[k["tripartite_MI"], k["I_c_A_to_BC"], k["I_c_AB_to_C"]]
                  for k in [compute_3q_kernel(rho, n) for n, rho in states_no_relay.items()]]

    h1_relay_total = 0
    h1_no_relay_total = 0

    try:
        rc = gudhi.RipsComplex(points=k_relay, max_edge_length=5.0)
        st = rc.create_simplex_tree(max_dimension=3)
        st.compute_persistence()
        pairs = st.persistence_intervals_in_dimension(1)
        h1_relay_total = len([(b, d) for b, d in pairs])
    except Exception as e:
        results["relay_rips_error"] = str(e)

    try:
        rc2 = gudhi.RipsComplex(points=k_no_relay, max_edge_length=5.0)
        st2 = rc2.create_simplex_tree(max_dimension=3)
        st2.compute_persistence()
        pairs2 = st2.persistence_intervals_in_dimension(1)
        h1_no_relay_total = len([(b, d) for b, d in pairs2])
    except Exception as e:
        results["no_relay_rips_error"] = str(e)

    results["H1_with_relay"] = h1_relay_total
    results["H1_no_relay"] = h1_no_relay_total
    results["relay_changes_topology"] = h1_relay_total != h1_no_relay_total
    results["relay_topologically_load_bearing"] = h1_relay_total != h1_no_relay_total

    # Fe-bridge specific: what does removing relay do to its kernel triple?
    fe_relay = compute_3q_kernel(build_3q_states(True)["Fe_bridge"], "Fe_bridge_relay")
    fe_no_relay = compute_3q_kernel(build_3q_states(False)["Fe_bridge"], "Fe_bridge_no_relay")
    results["Fe_bridge_with_relay"] = fe_relay
    results["Fe_bridge_no_relay"] = fe_no_relay
    results["Fe_bridge_kernel_shifts"] = {
        "delta_tripartite_MI": float(fe_relay["tripartite_MI"] - fe_no_relay["tripartite_MI"]),
        "delta_I_c_A_to_BC": float(fe_relay["I_c_A_to_BC"] - fe_no_relay["I_c_A_to_BC"]),
        "delta_I_c_AB_to_C": float(fe_relay["I_c_AB_to_C"] - fe_no_relay["I_c_AB_to_C"]),
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    # Assemble relay topology verdict
    h1_relay = (pos.get("rips_with_relay") or {}).get("H1", {})
    h1_no_relay = (neg.get("rips_no_relay") or {}).get("H1", {})

    results = {
        "name": "gudhi_3qubit_bridge",
        "description": (
            "GUDHI Rips persistent homology on 6 canonical 3-qubit states "
            "(|000>, GHZ, W, Fe-bridge, Werner-3q, Product⊗Bell). "
            "Embedded as (tripartite_MI, I_c(A->BC), I_c(AB->C)) triples. "
            "Tests whether XX relay creates H1 and is topologically load-bearing."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "classification": "canonical",
        "topology_verdict": {
            "H0_with_relay": (pos.get("rips_with_relay") or {}).get("H0"),
            "H1_with_relay": h1_relay,
            "H2_with_relay": (pos.get("rips_with_relay") or {}).get("H2"),
            "H0_no_relay": (neg.get("rips_no_relay") or {}).get("H0"),
            "H1_no_relay": h1_no_relay,
            "relay_changes_topology": bnd.get("relay_changes_topology"),
            "relay_topologically_load_bearing": bnd.get("relay_topologically_load_bearing"),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "gudhi_3qubit_bridge_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
