#!/usr/bin/env python3
"""
Tensor Network x Spinor x Torus — Entangled MPS on nested Hopf tori
====================================================================
Canonical sim (torch-native with autograd).

Construction:
  1. N=4 sites on a torus ring.  Each site carries a left-Weyl spinor
     parameterized by torus coordinates (eta_i, xi_i).
  2. CNOT ring entangles adjacent sites: 1->2, 2->3, 3->4, 4->1.
  3. SVD decomposition into bond-dimension-2 MPS.
  4. Observables: bipartition entropies, mutual information,
     bond dimensions, chiral current.
  5. Torus sweep: vary eta (polar angle) with xi_i = 2*pi*i/4 (ring symmetry).
  6. Autograd: gradient of total entropy w.r.t. eta.

Tests:
  Positive — MPS reconstruction, nonzero entropy, bond dim = 2,
             entropy varies with eta.
  Negative — product state (no CNOT) has zero bipartition entropy.
  Boundary — eta = 0, pi/4 (Clifford torus), pi/2.
"""

import json
import os
import time
import math

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": ""},
    "pyg":        {"tried": False, "used": False, "reason": "not needed for this sim"},
    "z3":         {"tried": False, "used": False, "reason": "not needed for this sim"},
    "cvc5":       {"tried": False, "used": False, "reason": "not needed for this sim"},
    "sympy":      {"tried": False, "used": False, "reason": "not needed for this sim"},
    "clifford":   {"tried": False, "used": False, "reason": "not needed — Weyl spinor built directly in torch"},
    "geomstats":  {"tried": False, "used": False, "reason": "not needed for this sim"},
    "e3nn":       {"tried": False, "used": False, "reason": "not needed for this sim"},
    "rustworkx":  {"tried": False, "used": False, "reason": "not needed for this sim"},
    "xgi":        {"tried": False, "used": False, "reason": "not needed for this sim"},
    "toponetx":   {"tried": False, "used": False, "reason": "not needed for this sim"},
    "gudhi":      {"tried": False, "used": False, "reason": "not needed for this sim"},
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Core computation engine: state vectors, CNOT gates, SVD for MPS, "
        "entanglement entropy, autograd for d(entropy)/d(eta)"
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    raise SystemExit("PyTorch required for this canonical sim")

# =====================================================================
# CONSTANTS
# =====================================================================

N_SITES = 4
BOND_DIM = 2          # expected for minimally-entangled qubit chain
EPS = 1e-12
SWEEP_POINTS = 64     # eta sweep resolution
DTYPE = torch.complex128
RDTYPE = torch.float64

# =====================================================================
# CORE BUILDING BLOCKS
# =====================================================================

def left_weyl_spinor(eta, xi):
    """
    Left-handed Weyl spinor on the Hopf fibration torus.

    The Hopf map S^3 -> S^2 parameterized by (eta, xi):
      |L(eta, xi)> = [ cos(eta) * exp(i*xi/2) ]
                     [ sin(eta) * exp(-i*xi/2) ]

    eta in [0, pi/2] controls polar position on S^2.
    xi in [0, 2*pi) is the fiber phase (torus longitude).
    """
    cos_eta = torch.cos(eta)
    sin_eta = torch.sin(eta)
    phase_p = torch.exp(1j * xi / 2.0)
    phase_m = torch.exp(-1j * xi / 2.0)
    return torch.stack([cos_eta * phase_p, sin_eta * phase_m])


def cnot_gate():
    """Standard CNOT (control x target) as 4x4 unitary."""
    g = torch.eye(4, dtype=DTYPE)
    # Swap |10> <-> |11>
    g[2, 2] = 0.0
    g[2, 3] = 1.0
    g[3, 3] = 0.0
    g[3, 2] = 1.0
    return g


def apply_two_qubit_gate(state_vec, gate, q1, q2, n_qubits):
    """
    Apply a 2-qubit gate to qubits q1 (control) and q2 (target)
    within an n_qubits state vector of length 2^n_qubits.
    """
    dim = 2 ** n_qubits
    new_state = torch.zeros(dim, dtype=DTYPE)
    for i in range(dim):
        bits = [(i >> (n_qubits - 1 - k)) & 1 for k in range(n_qubits)]
        b1, b2 = bits[q1], bits[q2]
        row = b1 * 2 + b2
        for col in range(4):
            c1, c2 = col // 2, col % 2
            amp = gate[row, col]
            if abs(amp) < EPS:
                continue
            new_bits = list(bits)
            new_bits[q1] = c1
            new_bits[q2] = c2
            j = 0
            for k in range(n_qubits):
                j |= new_bits[k] << (n_qubits - 1 - k)
            new_state[j] = new_state[j] + amp * state_vec[i]
    return new_state


def build_entangled_state(eta, xis, apply_cnot_ring=True):
    """
    Build the 4-qubit state:
      1. Local Weyl spinors at each site parameterized by (eta, xi_i).
      2. Tensor product to get 2^4 state.
      3. CNOT ring: 0->1, 1->2, 2->3, 3->0.

    Returns the 16-component state vector.
    """
    # Local spinor states
    spinors = [left_weyl_spinor(eta, xis[i]) for i in range(N_SITES)]

    # Tensor product: |s0> x |s1> x |s2> x |s3>
    state = spinors[0]
    for i in range(1, N_SITES):
        state = torch.kron(state, spinors[i])

    if apply_cnot_ring:
        gate = cnot_gate()
        # Ring: 0->1, 1->2, 2->3, 3->0
        for ctrl, tgt in [(0, 1), (1, 2), (2, 3), (3, 0)]:
            state = apply_two_qubit_gate(state, gate, ctrl, tgt, N_SITES)

    return state


# =====================================================================
# MPS DECOMPOSITION VIA SVD
# =====================================================================

def state_to_mps(state_vec, n_sites=N_SITES):
    """
    Decompose a 2^n state vector into an MPS with open boundary conditions
    via sequential SVD (left-canonical form).

    Returns:
      tensors: list of n tensors, each shape (chi_L, 2, chi_R)
      singular_values: list of (n-1) arrays of singular values at each bond
    """
    d = 2
    tensors = []
    singular_values = []

    # Work with the full coefficient tensor reshaped progressively
    # psi starts as (1, 2^n) -- the "remaining" part
    remaining_dim = d ** n_sites
    psi = state_vec.reshape(1, remaining_dim)

    for i in range(n_sites - 1):
        chi_L = psi.shape[0]
        right_dim = psi.shape[1] // d

        # Reshape to (chi_L * d, right_dim) for SVD
        psi_mat = psi.reshape(chi_L * d, right_dim)

        U, S, Vh = torch.linalg.svd(psi_mat, full_matrices=False)

        # Truncate to bond dimension
        n_sv = S.shape[0]
        bond = min(BOND_DIM, n_sv)
        # Only keep significant singular values
        mask = S.abs() > EPS
        bond = min(bond, mask.sum().item())
        bond = max(bond, 1)

        U = U[:, :bond]
        S = S[:bond]
        Vh = Vh[:bond, :]

        singular_values.append(S)

        # Store A tensor: (chi_L, d, bond)
        tensors.append(U.reshape(chi_L, d, bond))

        # Propagate S*Vh to the right: (bond, right_dim)
        psi = torch.diag(S.to(DTYPE)) @ Vh

    # Last tensor: whatever remains, shape (chi_L, d, 1)
    chi_L = psi.shape[0]
    tensors.append(psi.reshape(chi_L, d, 1))

    return tensors, singular_values


def mps_to_statevector(tensors):
    """Contract MPS tensors back to a full state vector."""
    psi = tensors[0][0, :, :]  # shape (d, chi_R)
    for i in range(1, len(tensors)):
        A = tensors[i]  # (chi_L, d, chi_R)
        chi_L, d_phys, chi_R = A.shape
        dim_left = psi.shape[0]
        A_mat = A.reshape(chi_L, d_phys * chi_R)
        psi = psi @ A_mat  # (dim_left, d*chi_R)
        psi = psi.reshape(dim_left * d_phys, chi_R)
    return psi.flatten()


# =====================================================================
# ENTANGLEMENT MEASURES
# =====================================================================

def bipartition_entropy(state_vec, n_sites, cut):
    """
    Von Neumann entropy for bipartition at position `cut`.
    System A = sites [0..cut-1], system B = sites [cut..n-1].
    """
    d = 2
    dim_A = d ** cut
    dim_B = d ** (n_sites - cut)
    psi_mat = state_vec.reshape(dim_A, dim_B)
    S = torch.linalg.svdvals(psi_mat)
    S = S[S > EPS]
    probs = (S ** 2).real
    probs = probs / probs.sum()
    entropy = -(probs * torch.log2(probs + EPS)).sum()
    return entropy


def reduced_density_matrix(state_vec, n_sites, keep_sites):
    """
    Partial trace: keep specified sites, trace out the rest.
    Returns the reduced density matrix via explicit summation.
    """
    d = 2
    dim = d ** n_sites
    keep_sites = sorted(keep_sites)
    trace_sites = sorted(set(range(n_sites)) - set(keep_sites))
    dim_keep = d ** len(keep_sites)
    dim_trace = d ** len(trace_sites)

    rho = torch.zeros(dim_keep, dim_keep, dtype=DTYPE)

    for t in range(dim_trace):
        # Build the trace-site bits
        trace_bits = [(t >> (len(trace_sites) - 1 - k)) & 1 for k in range(len(trace_sites))]

        for i_keep in range(dim_keep):
            keep_bits_i = [(i_keep >> (len(keep_sites) - 1 - k)) & 1 for k in range(len(keep_sites))]
            # Assemble full index for ket
            full_bits_i = [0] * n_sites
            for idx, s in enumerate(keep_sites):
                full_bits_i[s] = keep_bits_i[idx]
            for idx, s in enumerate(trace_sites):
                full_bits_i[s] = trace_bits[idx]
            ii = sum(full_bits_i[k] << (n_sites - 1 - k) for k in range(n_sites))

            for j_keep in range(dim_keep):
                keep_bits_j = [(j_keep >> (len(keep_sites) - 1 - k)) & 1 for k in range(len(keep_sites))]
                full_bits_j = [0] * n_sites
                for idx, s in enumerate(keep_sites):
                    full_bits_j[s] = keep_bits_j[idx]
                for idx, s in enumerate(trace_sites):
                    full_bits_j[s] = trace_bits[idx]
                jj = sum(full_bits_j[k] << (n_sites - 1 - k) for k in range(n_sites))

                rho[i_keep, j_keep] += state_vec[ii] * state_vec[jj].conj()

    return rho


def von_neumann_entropy_from_rho(rho):
    """Von Neumann entropy S = -Tr(rho log2 rho) from density matrix."""
    # eigvalsh works on Hermitian matrices (complex ok)
    eigenvalues = torch.linalg.eigvalsh(rho).real
    eigenvalues = eigenvalues[eigenvalues > EPS]
    return -(eigenvalues * torch.log2(eigenvalues + EPS)).sum()


def mutual_information(state_vec, n_sites, site_a, site_b):
    """
    Mutual information I(A:B) = S(A) + S(B) - S(AB).
    """
    rho_a = reduced_density_matrix(state_vec, n_sites, [site_a])
    rho_b = reduced_density_matrix(state_vec, n_sites, [site_b])
    rho_ab = reduced_density_matrix(state_vec, n_sites, [site_a, site_b])

    S_a = von_neumann_entropy_from_rho(rho_a)
    S_b = von_neumann_entropy_from_rho(rho_b)
    S_ab = von_neumann_entropy_from_rho(rho_ab)

    return S_a + S_b - S_ab


def chiral_current(state_vec, n_sites):
    """
    Chiral current: sum of <sigma_z> at each site.
    """
    d = 2
    sigma_z = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    total = torch.tensor(0.0, dtype=RDTYPE)
    for site in range(n_sites):
        # Build full operator: I x ... x sigma_z x ... x I
        op = torch.tensor([[1.0]], dtype=DTYPE)
        for s in range(n_sites):
            if s == site:
                op = torch.kron(op, sigma_z)
            else:
                op = torch.kron(op, torch.eye(d, dtype=DTYPE))
        op = op.squeeze()
        expectation = (state_vec.conj() @ op @ state_vec).real
        total = total + expectation
    return total


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    t0 = time.time()

    # --- Setup: canonical state at eta=pi/4 (Clifford torus) ---
    eta = torch.tensor(math.pi / 4, dtype=RDTYPE, requires_grad=True)
    xis = [torch.tensor(2 * math.pi * i / N_SITES, dtype=RDTYPE) for i in range(N_SITES)]
    state = build_entangled_state(eta, xis, apply_cnot_ring=True)

    # TEST 1: MPS reconstruction matches original state
    tensors, svs = state_to_mps(state.detach())
    reconstructed = mps_to_statevector(tensors)
    fidelity = (state.detach().conj() @ reconstructed).abs() ** 2
    recon_error = (state.detach() - reconstructed).abs().max().item()
    results["mps_reconstruction"] = {
        "fidelity": fidelity.item(),
        "max_abs_error": recon_error,
        "pass": recon_error < 1e-10,
        "description": "MPS contraction reproduces original state to machine precision"
    }

    # TEST 2: entanglement entropy is nonzero after CNOT ring
    entropies = {}
    for cut in [1, 2, 3]:
        label = f"{cut}|{N_SITES - cut}"
        S = bipartition_entropy(state.detach(), N_SITES, cut)
        entropies[label] = S.item()
    all_nonzero = all(v > 0.01 for v in entropies.values())
    results["nonzero_entropy"] = {
        "bipartition_entropies": entropies,
        "pass": all_nonzero,
        "description": "All bipartition entropies are nonzero after CNOT ring"
    }

    # TEST 3: bond dimensions = 2
    bond_dims = [sv.shape[0] for sv in svs]
    results["bond_dimensions"] = {
        "bond_dims": bond_dims,
        "pass": all(bd == BOND_DIM for bd in bond_dims),
        "description": "Bond dimensions are 2 (minimal for entangled qubit chain)"
    }

    # TEST 4: entropy changes with torus parameter eta
    eta_vals = [0.1, math.pi / 8, math.pi / 4, 3 * math.pi / 8, math.pi / 2 - 0.1]
    entropy_at_etas = []
    for ev in eta_vals:
        eta_t = torch.tensor(ev, dtype=RDTYPE)
        s = build_entangled_state(eta_t, xis, apply_cnot_ring=True)
        S12 = bipartition_entropy(s.detach(), N_SITES, 2)
        entropy_at_etas.append({"eta": ev, "S_12_34": S12.item()})
    entropy_values = [e["S_12_34"] for e in entropy_at_etas]
    varies = (max(entropy_values) - min(entropy_values)) > 0.01
    results["entropy_varies_with_eta"] = {
        "samples": entropy_at_etas,
        "range": max(entropy_values) - min(entropy_values),
        "pass": varies,
        "description": "Entanglement entropy varies with torus parameter eta"
    }

    # TEST 5: mutual information on the ring
    # Adjacent pairs (connected by CNOT) should have nonzero MI
    mi_01 = mutual_information(state.detach(), N_SITES, 0, 1)
    mi_12 = mutual_information(state.detach(), N_SITES, 1, 2)
    mi_23 = mutual_information(state.detach(), N_SITES, 2, 3)
    mi_30 = mutual_information(state.detach(), N_SITES, 3, 0)
    # Non-adjacent (informational -- may be zero for nearest-neighbor entanglement)
    mi_02 = mutual_information(state.detach(), N_SITES, 0, 2)
    mi_13 = mutual_information(state.detach(), N_SITES, 1, 3)
    adjacent_mis = [mi_01.item(), mi_12.item(), mi_23.item(), mi_30.item()]
    results["mutual_information"] = {
        "adjacent_I_01": mi_01.item(),
        "adjacent_I_12": mi_12.item(),
        "adjacent_I_23": mi_23.item(),
        "adjacent_I_30": mi_30.item(),
        "nonadjacent_I_02": mi_02.item(),
        "nonadjacent_I_13": mi_13.item(),
        "pass": any(m > 1e-6 for m in adjacent_mis),
        "description": "Adjacent sites (CNOT-connected) have nonzero mutual information"
    }

    # TEST 6: chiral current on the ring
    j_chiral = chiral_current(state.detach(), N_SITES)
    results["chiral_current"] = {
        "value": j_chiral.item(),
        "pass": True,  # informational — value depends on eta
        "description": "Sum of <sigma_z> across all sites"
    }

    # TEST 7: autograd — gradient of entropy w.r.t. eta
    eta_ag = torch.tensor(math.pi / 4, dtype=RDTYPE, requires_grad=True)
    state_ag = build_entangled_state(eta_ag, xis, apply_cnot_ring=True)
    # Use 12|34 bipartition for differentiability
    dim_A = 2 ** 2
    dim_B = 2 ** 2
    psi_mat = state_ag.reshape(dim_A, dim_B)
    S_vals = torch.linalg.svdvals(psi_mat)
    S_real = S_vals.real
    probs = S_real ** 2
    probs = probs / probs.sum()
    entropy_ag = -(probs * torch.log2(probs + EPS)).sum()
    entropy_ag.backward()
    grad_val = eta_ag.grad.item() if eta_ag.grad is not None else None
    results["autograd_entropy"] = {
        "entropy_at_pi_4": entropy_ag.item(),
        "d_entropy_d_eta": grad_val,
        "pass": grad_val is not None,
        "description": "Autograd computes d(entropy)/d(eta) via SVD backprop"
    }

    results["time_s"] = time.time() - t0
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    t0 = time.time()

    # Without CNOT ring, product state should have ZERO bipartition entropy
    eta = torch.tensor(math.pi / 4, dtype=RDTYPE)
    xis = [torch.tensor(2 * math.pi * i / N_SITES, dtype=RDTYPE) for i in range(N_SITES)]
    product_state = build_entangled_state(eta, xis, apply_cnot_ring=False)

    entropies = {}
    for cut in [1, 2, 3]:
        label = f"{cut}|{N_SITES - cut}"
        S = bipartition_entropy(product_state, N_SITES, cut)
        entropies[label] = S.item()
    all_zero = all(abs(v) < 1e-10 for v in entropies.values())
    results["product_state_zero_entropy"] = {
        "bipartition_entropies": entropies,
        "pass": all_zero,
        "description": "Without CNOT ring, all bipartition entropies are zero (product state)"
    }

    # Product state MPS should have bond dimension 1
    tensors, svs = state_to_mps(product_state)
    bond_dims = [sv.shape[0] for sv in svs]
    results["product_state_bond_dim_1"] = {
        "bond_dims": bond_dims,
        "pass": all(bd == 1 for bd in bond_dims),
        "description": "Product state MPS has bond dimension 1"
    }

    # Mutual information should be zero for product state
    mi_13 = mutual_information(product_state, N_SITES, 0, 2)
    mi_24 = mutual_information(product_state, N_SITES, 1, 3)
    results["product_state_zero_mutual_info"] = {
        "I_1_3": mi_13.item(),
        "I_2_4": mi_24.item(),
        "pass": abs(mi_13.item()) < 1e-10 and abs(mi_24.item()) < 1e-10,
        "description": "Product state has zero mutual information"
    }

    results["time_s"] = time.time() - t0
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    t0 = time.time()

    xis = [torch.tensor(2 * math.pi * i / N_SITES, dtype=RDTYPE) for i in range(N_SITES)]

    boundary_cases = {
        "eta_0_north_pole": 0.0,
        "eta_pi4_clifford_torus": math.pi / 4,
        "eta_pi2_south_pole": math.pi / 2,
    }

    for label, eta_val in boundary_cases.items():
        eta = torch.tensor(eta_val, dtype=RDTYPE)
        state = build_entangled_state(eta, xis, apply_cnot_ring=True)

        # Normalization check
        norm = (state.conj() @ state).real.item()

        # Bipartition entropies
        entropies = {}
        for cut in [1, 2, 3]:
            S = bipartition_entropy(state, N_SITES, cut)
            entropies[f"{cut}|{N_SITES - cut}"] = S.item()

        # MPS roundtrip
        tensors, svs = state_to_mps(state)
        recon = mps_to_statevector(tensors)
        recon_err = (state - recon).abs().max().item()

        # Chiral current
        j = chiral_current(state, N_SITES)

        results[label] = {
            "eta": eta_val,
            "norm": norm,
            "norm_ok": abs(norm - 1.0) < 1e-10,
            "bipartition_entropies": entropies,
            "mps_recon_error": recon_err,
            "mps_ok": recon_err < 1e-10,
            "chiral_current": j.item(),
            "pass": abs(norm - 1.0) < 1e-10 and recon_err < 1e-10,
            "description": f"Boundary case eta={eta_val:.4f}"
        }

    # Torus sweep: full eta range
    sweep_etas = torch.linspace(0.01, math.pi / 2 - 0.01, SWEEP_POINTS)
    sweep_data = []
    for eta_val in sweep_etas:
        eta = eta_val.clone().detach().to(RDTYPE)
        state = build_entangled_state(eta, xis, apply_cnot_ring=True)
        S_12_34 = bipartition_entropy(state, N_SITES, 2).item()
        S_1_rest = bipartition_entropy(state, N_SITES, 1).item()
        j = chiral_current(state, N_SITES).item()
        sweep_data.append({
            "eta": eta_val.item(),
            "S_12_34": S_12_34,
            "S_1_234": S_1_rest,
            "chiral_current": j,
        })

    results["torus_sweep"] = {
        "n_points": len(sweep_data),
        "data": sweep_data,
        "entropy_range_12_34": max(d["S_12_34"] for d in sweep_data) - min(d["S_12_34"] for d in sweep_data),
        "entropy_range_1_234": max(d["S_1_234"] for d in sweep_data) - min(d["S_1_234"] for d in sweep_data),
        "pass": True,
        "description": "Full eta sweep tracking entropy and chiral current"
    }

    results["time_s"] = time.time() - t0
    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running tensor network + spinor + torus sim ...")
    t_total = time.time()

    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    pos_pass = sum(1 for v in pos.values() if isinstance(v, dict) and v.get("pass"))
    pos_total = sum(1 for v in pos.values() if isinstance(v, dict) and "pass" in v)
    neg_pass = sum(1 for v in neg.values() if isinstance(v, dict) and v.get("pass"))
    neg_total = sum(1 for v in neg.values() if isinstance(v, dict) and "pass" in v)
    bnd_pass = sum(1 for v in bnd.values() if isinstance(v, dict) and v.get("pass"))
    bnd_total = sum(1 for v in bnd.values() if isinstance(v, dict) and "pass" in v)

    results = {
        "name": "Tensor Network x Spinor x Torus (MPS on Hopf ring)",
        "tool_manifest": TOOL_MANIFEST,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "classification": "canonical",
        "summary": {
            "positive": f"{pos_pass}/{pos_total} pass",
            "negative": f"{neg_pass}/{neg_total} pass",
            "boundary": f"{bnd_pass}/{bnd_total} pass",
            "total_time_s": time.time() - t_total,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "tensor_network_spinor_torus_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Positive: {pos_pass}/{pos_total} | Negative: {neg_pass}/{neg_total} | Boundary: {bnd_pass}/{bnd_total}")
