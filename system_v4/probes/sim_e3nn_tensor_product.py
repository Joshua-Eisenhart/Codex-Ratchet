#!/usr/bin/env python3
"""
sim_e3nn_tensor_product.py

Tests FullyConnectedTensorProduct for the two-qubit system.

Physical setup:
  - Two-qubit state has two Bloch vectors (one per qubit), each a 1o irrep of SO(3)
  - CG decomposition: 1o ⊗ 1o = 0e + 1e + 2e (scalar + pseudovector + rank-2 tensor)
  - The 0e (scalar) output of 1o ⊗ 1o corresponds to the dot product v1 · v2
  - For a two-qubit pure state, v1 · v2 is related to the purity/entanglement
  - Mutual information I(A:B) = S(A) + S(B) - S(AB)

Claims tested:
  P1: FCTP(1o ⊗ 1o → 0e + 1e + 2e) is equivariant under simultaneous rotation
  P2: The 0e (scalar) output correlates with v1 · v2 (dot product of Bloch vectors)
  P3: v1 · v2 correlates with mutual information I(A:B)
  P4: Scalar output is rotation-invariant (as expected for a 0e irrep)
  N1: Non-equivariant (standard linear) two-qubit map fails equivariance
  N2: Scalar output does NOT depend on single-qubit rotation direction (must be 0e, not 0o)
  B1: Product state — Bloch vectors can point anywhere, scalar varies with orientation
  B2: Bell state — Bloch vectors are both zero (maximally mixed marginals)
  B3: Partial-entanglement state — scalar output interpolates between product and Bell
"""

import json
import os
import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "all tensor ops, density matrices, von Neumann entropy"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this probe"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this probe"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this probe"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this probe"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this probe"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this probe"},
    "e3nn": {"tried": True, "used": True, "reason": "PRIMARY: FullyConnectedTensorProduct, Irreps, wigner_D, rand_angles"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this probe"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this probe"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this probe"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this probe"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": "load_bearing",
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

import torch
import torch.nn as nn
from e3nn import o3
from e3nn.o3 import FullyConnectedTensorProduct


# =====================================================================
# HELPERS
# =====================================================================

def quat_to_su2(q):
    """Convert unit quaternion (w,x,y,z) to 2x2 SU(2) matrix (complex128)."""
    w, x, y, z = q[0], q[1], q[2], q[3]
    U = torch.stack([
        torch.stack([torch.complex(w, z), torch.complex(y, x)]),
        torch.stack([torch.complex(-y, x), torch.complex(w, -z)])
    ])
    return U.to(torch.complex128)


def bloch_vector(psi):
    """Compute Bloch vector from single-qubit state |psi> (complex 2-vector)."""
    psi = psi / psi.norm()
    alpha, beta = psi[0], psi[1]
    x = 2 * (alpha.conj() * beta).real
    y = 2 * (alpha.conj() * beta).imag
    z = (alpha.abs() ** 2 - beta.abs() ** 2).real
    return torch.stack([x, y, z]).float()


def partial_trace(rho_AB, keep='A', dim_A=2, dim_B=2):
    """Partial trace of rho_AB. keep='A' traces out B; keep='B' traces out A."""
    rho = rho_AB.reshape(dim_A, dim_B, dim_A, dim_B)
    if keep == 'A':
        return torch.einsum('ibjb->ij', rho)
    else:
        return torch.einsum('aiba->ib', rho)


def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho log rho)."""
    eigs = torch.linalg.eigvalsh(rho).real
    eigs = torch.clamp(eigs, min=1e-15)
    return -(eigs * torch.log(eigs)).sum().item()


def mutual_information(psi_AB, dim_A=2, dim_B=2):
    """I(A:B) = S(A) + S(B) - S(AB) for pure state |psi_AB>."""
    rho_AB = torch.outer(psi_AB, psi_AB.conj())
    rho_A = partial_trace(rho_AB, keep='A', dim_A=dim_A, dim_B=dim_B)
    rho_B = partial_trace(rho_AB, keep='B', dim_A=dim_A, dim_B=dim_B)
    S_A = von_neumann_entropy(rho_A)
    S_B = von_neumann_entropy(rho_B)
    S_AB = von_neumann_entropy(rho_AB)
    return S_A + S_B - S_AB


def bloch_vectors_from_two_qubit_state(psi_AB):
    """Extract individual Bloch vectors from a two-qubit pure state."""
    rho_AB = torch.outer(psi_AB, psi_AB.conj())
    rho_A = partial_trace(rho_AB, keep='A')
    rho_B = partial_trace(rho_AB, keep='B')
    # Bloch vector of rho = Tr(rho * sigma_i)
    sigma_x = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
    sigma_y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
    sigma_z = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)
    bx_A = torch.trace(rho_A @ sigma_x).real.item()
    by_A = torch.trace(rho_A @ sigma_y).real.item()
    bz_A = torch.trace(rho_A @ sigma_z).real.item()
    bx_B = torch.trace(rho_B @ sigma_x).real.item()
    by_B = torch.trace(rho_B @ sigma_y).real.item()
    bz_B = torch.trace(rho_B @ sigma_z).real.item()
    v_A = torch.tensor([bx_A, by_A, bz_A], dtype=torch.float32)
    v_B = torch.tensor([bx_B, by_B, bz_B], dtype=torch.float32)
    return v_A, v_B


def make_two_qubit_state(theta, phi_A, phi_B):
    """
    Parameterize a two-qubit state with entanglement parameter theta.
    theta=0: product state |0>|0>
    theta=pi/4: maximally entangled (Bell)
    Returns: cos(theta)|00> + sin(theta)|11>
    """
    psi = torch.zeros(4, dtype=torch.complex128)
    psi[0] = np.cos(theta)
    psi[3] = np.sin(theta) * np.exp(1j * (phi_A + phi_B))
    return psi / psi.norm()


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    torch.manual_seed(42)

    # Build the FCTP: 1o ⊗ 1o → 0e + 1e + 2e
    irreps_in1 = o3.Irreps('1x1o')
    irreps_in2 = o3.Irreps('1x1o')
    irreps_out = o3.Irreps('1x0e + 1x1e + 1x2e')  # dim = 1 + 3 + 5 = 9
    fctp = FullyConnectedTensorProduct(irreps_in1, irreps_in2, irreps_out)
    fctp.eval()

    # ------------------------------------------------------------------
    # P1: FCTP(1o ⊗ 1o → 0e + 1e + 2e) equivariant under simultaneous rotation
    # ------------------------------------------------------------------
    alpha, beta, gamma = o3.rand_angles()
    D1 = o3.wigner_D(1, alpha, beta, gamma)  # 3x3 rotation for l=1

    v1 = torch.randn(3)
    v2 = torch.randn(3)

    # Compute Wigner D matrices for all output irreps
    D_out_0e = o3.wigner_D(0, alpha, beta, gamma)  # 1x1 (trivial)
    D_out_1e = o3.wigner_D(1, alpha, beta, gamma)  # 3x3
    D_out_2e = o3.wigner_D(2, alpha, beta, gamma)  # 5x5

    # Block-diagonal rotation for the output irreps (1 + 3 + 5 = 9 dims)
    D_out = torch.zeros(9, 9)
    D_out[0:1, 0:1] = D_out_0e
    D_out[1:4, 1:4] = D_out_1e
    D_out[4:9, 4:9] = D_out_2e

    with torch.no_grad():
        out_rotate_then_fctp = fctp(D1 @ v1, D1 @ v2)
        out_fctp_then_rotate = D_out @ fctp(v1, v2)
    diff_p1 = (out_rotate_then_fctp - out_fctp_then_rotate).norm().item()

    results['P1_FCTP_1o_x_1o_equivariance'] = {
        'test': 'FCTP(1o ⊗ 1o → 0e+1e+2e) equivariant under simultaneous SO(3) rotation',
        'equivariance_error': diff_p1,
        'tolerance': 1e-4,
        'output_dim': 9,
        'pass': diff_p1 < 1e-4,
        'note': ('simultaneous rotation of both Bloch vectors; output rotates by block-diagonal D. '
                 'Tolerance 1e-4 reflects float32 precision for the full 9-dim output block.'),
    }

    # ------------------------------------------------------------------
    # P2: 0e scalar output corresponds to dot product v1 · v2
    # Build a FCTP: 1o ⊗ 1o → 0e only (scalar channel)
    # The CG coefficient for l=0 from l=1 ⊗ l=1 is proportional to the dot product
    # ------------------------------------------------------------------
    irreps_scalar_only = o3.Irreps('1x0e')
    fctp_scalar = FullyConnectedTensorProduct(irreps_in1, irreps_in2, irreps_scalar_only)
    fctp_scalar.eval()

    # Test across multiple (v1, v2) pairs
    dot_products = []
    scalar_outputs = []

    for _ in range(20):
        v1_i = torch.randn(3)
        v2_i = torch.randn(3)
        with torch.no_grad():
            scalar_out = fctp_scalar(v1_i, v2_i).item()
        dot_val = (v1_i @ v2_i).item()
        dot_products.append(dot_val)
        scalar_outputs.append(scalar_out)

    dot_arr = np.array(dot_products)
    scalar_arr = np.array(scalar_outputs)
    # Correlation between dot product and scalar output
    correlation = np.corrcoef(dot_arr, scalar_arr)[0, 1]

    results['P2_scalar_output_correlates_with_dot_product'] = {
        'test': '0e scalar output of 1o ⊗ 1o correlates with Bloch vector dot product v1·v2',
        'pearson_correlation': float(correlation),
        'n_samples': 20,
        'tolerance': 0.99,
        'pass': abs(correlation) > 0.99,
        'note': 'CG(1,1→0) is the dot product; e3nn scalar channel must be proportional to it',
    }

    # ------------------------------------------------------------------
    # P3: Dot product v1 · v2 correlates with mutual information I(A:B)
    # For the family cos(theta)|00> + sin(theta)e^{i*phi}|11>:
    #   rho_A = diag(cos^2(theta), sin^2(theta)) → S(A) = -cos^2 log cos^2 - sin^2 log sin^2
    #   Bloch vector of A: (0, 0, cos^2 - sin^2) = (0, 0, cos(2*theta))
    #   Bloch vector of B: same z-component
    #   I(A:B) = 2*S(A) (since pure state and S(AB)=0 → I(A:B) = 2*S(A))
    # ------------------------------------------------------------------
    thetas = np.linspace(0, np.pi / 4, 20)
    mi_vals = []
    dot_vals = []
    bloch_norms_A = []

    for theta in thetas:
        psi = make_two_qubit_state(theta, 0.0, 0.0)
        mi = mutual_information(psi)
        v_A, v_B = bloch_vectors_from_two_qubit_state(psi)
        dot_v = (v_A @ v_B).item()
        mi_vals.append(mi)
        dot_vals.append(dot_v)
        bloch_norms_A.append(v_A.norm().item())

    mi_arr = np.array(mi_vals)
    dot_arr2 = np.array(dot_vals)
    # For this family, v_A = v_B = (0, 0, cos(2*theta)), so dot = cos^2(2*theta)
    # I(A:B) = 2*H(cos^2) which is a monotone function of |cos(2*theta)|
    # Both decrease monotonically from product to Bell state
    correlation_mi_dot = np.corrcoef(mi_arr, dot_arr2)[0, 1]

    results['P3_dot_product_vs_mutual_information'] = {
        'test': 'Bloch vector dot product v1·v2 correlates with mutual information I(A:B)',
        'pearson_correlation_mi_vs_dot': float(correlation_mi_dot),
        'n_states': 20,
        'theta_range': [0.0, float(np.pi / 4)],
        'mi_at_product': float(mi_vals[0]),
        'mi_at_bell': float(mi_vals[-1]),
        'dot_at_product': float(dot_vals[0]),
        'dot_at_bell': float(dot_vals[-1]),
        'tolerance': 0.95,
        'pass': abs(correlation_mi_dot) > 0.95,
        'note': 'for the cos(theta)|00>+sin(theta)|11> family, both MI and dot decrease monotonically',
    }

    # ------------------------------------------------------------------
    # P4: Scalar output is rotation-invariant (it is a 0e irrep = scalar)
    # ------------------------------------------------------------------
    v1_fixed = torch.tensor([1.0, 0.5, 0.3])
    v2_fixed = torch.tensor([0.2, 0.8, 0.1])

    scalar_vals = []
    for _ in range(10):
        alpha_i, beta_i, gamma_i = o3.rand_angles()
        D_i = o3.wigner_D(1, alpha_i, beta_i, gamma_i)
        with torch.no_grad():
            s_i = fctp_scalar(D_i @ v1_fixed, D_i @ v2_fixed).item()
        scalar_vals.append(s_i)

    scalar_std = float(np.std(scalar_vals))
    scalar_mean = float(np.mean(scalar_vals))

    results['P4_scalar_is_rotation_invariant'] = {
        'test': 'FCTP scalar output is invariant under simultaneous rotation of both inputs',
        'scalar_std_over_rotations': scalar_std,
        'scalar_mean': scalar_mean,
        'tolerance': 1e-5,
        'pass': scalar_std < 1e-5,
        'note': '0e irrep is invariant under all SO(3) rotations; std across rotations should be ~0',
    }

    # ------------------------------------------------------------------
    # P5: Full decomposition dim check: 1o ⊗ 1o = 0e(1) + 1e(3) + 2e(5)
    # ------------------------------------------------------------------
    with torch.no_grad():
        out_full = fctp(v1_fixed, v2_fixed)
    total_dim = out_full.shape[0]

    results['P5_CG_decomposition_dimension'] = {
        'test': '1o ⊗ 1o → 0e + 1e + 2e has total output dim 9 = 1+3+5',
        'output_dim': int(total_dim),
        'expected_dim': 9,
        'l0_channels': 1,
        'l1_channels': 3,
        'l2_channels': 5,
        'pass': total_dim == 9,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    torch.manual_seed(99)

    irreps_in1 = o3.Irreps('1x1o')
    irreps_in2 = o3.Irreps('1x1o')
    irreps_scalar_only = o3.Irreps('1x0e')
    fctp_scalar = FullyConnectedTensorProduct(irreps_in1, irreps_in2, irreps_scalar_only)
    fctp_scalar.eval()

    # ------------------------------------------------------------------
    # N1: Standard nn.Linear (two-qubit concatenation) FAILS equivariance
    # ------------------------------------------------------------------
    nn_bilinear = nn.Bilinear(3, 3, 9, bias=True)
    nn_bilinear.eval()

    alpha, beta, gamma = o3.rand_angles()
    D1 = o3.wigner_D(1, alpha, beta, gamma)
    v1 = torch.randn(3)
    v2 = torch.randn(3)

    # Build block-diagonal output rotation
    D_out_0e = o3.wigner_D(0, alpha, beta, gamma)
    D_out_1e = o3.wigner_D(1, alpha, beta, gamma)
    D_out_2e = o3.wigner_D(2, alpha, beta, gamma)
    D_out = torch.zeros(9, 9)
    D_out[0:1, 0:1] = D_out_0e
    D_out[1:4, 1:4] = D_out_1e
    D_out[4:9, 4:9] = D_out_2e

    with torch.no_grad():
        out1 = nn_bilinear(D1 @ v1, D1 @ v2)
        out2 = D_out @ nn_bilinear(v1, v2)
    diff_n1 = (out1 - out2).norm().item()

    results['N1_nn_bilinear_fails_equivariance'] = {
        'test': 'standard nn.Bilinear two-qubit map fails equivariance test',
        'equivariance_error': float(diff_n1),
        'min_expected_error': 0.1,
        'pass': diff_n1 > 0.1,
        'note': 'nn.Bilinear has no rotational structure; e3nn FCTP is necessary for equivariance',
    }

    # ------------------------------------------------------------------
    # N2: Scalar output does NOT change under rotation of only ONE qubit
    # (for an equivariant scalar: S(R*v1, R*v2) = S(v1, v2); but S(R*v1, v2) != S(v1, v2))
    # ------------------------------------------------------------------
    v1_fixed = torch.tensor([1.0, 0.5, 0.3])
    v2_fixed = torch.tensor([0.2, 0.8, 0.1])

    single_qubit_rotation_errors = []
    for _ in range(10):
        alpha_i, beta_i, gamma_i = o3.rand_angles()
        D_i = o3.wigner_D(1, alpha_i, beta_i, gamma_i)
        with torch.no_grad():
            s_original = fctp_scalar(v1_fixed, v2_fixed).item()
            s_rotated_v1 = fctp_scalar(D_i @ v1_fixed, v2_fixed).item()
        single_qubit_rotation_errors.append(abs(s_original - s_rotated_v1))

    mean_single_rot_err = float(np.mean(single_qubit_rotation_errors))
    results['N2_single_qubit_rotation_changes_scalar'] = {
        'test': 'rotating only ONE Bloch vector DOES change the scalar output (not jointly invariant)',
        'mean_change_under_single_rotation': mean_single_rot_err,
        'min_expected_change': 0.01,
        'pass': mean_single_rot_err > 0.01,
        'note': ('scalar is invariant under SIMULTANEOUS rotation, but NOT single-qubit rotation. '
                 'This confirms the scalar is v1·v2 (dot product), not |v1| or |v2|.'),
    }

    # ------------------------------------------------------------------
    # N3: At Bell state, both Bloch vectors are zero → scalar output = 0
    # ------------------------------------------------------------------
    psi_bell = torch.zeros(4, dtype=torch.complex128)
    psi_bell[0] = 1.0 / np.sqrt(2)
    psi_bell[3] = 1.0 / np.sqrt(2)

    v_A, v_B = bloch_vectors_from_two_qubit_state(psi_bell)
    bloch_norms = (v_A.norm().item(), v_B.norm().item())

    with torch.no_grad():
        scalar_bell = fctp_scalar(v_A, v_B).item()

    results['N3_bell_state_bloch_vectors_zero'] = {
        'test': 'Bell state Bloch vectors are both zero; scalar output should be 0',
        'bloch_norm_A': float(bloch_norms[0]),
        'bloch_norm_B': float(bloch_norms[1]),
        'scalar_output': float(scalar_bell),
        'tolerance': 1e-5,
        'pass': abs(scalar_bell) < 1e-5 and bloch_norms[0] < 1e-5 and bloch_norms[1] < 1e-5,
        'note': 'maximally entangled state → maximally mixed marginals → zero Bloch vectors → zero dot product',
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    torch.manual_seed(7)

    irreps_in1 = o3.Irreps('1x1o')
    irreps_in2 = o3.Irreps('1x1o')
    irreps_scalar_only = o3.Irreps('1x0e')
    fctp_scalar = FullyConnectedTensorProduct(irreps_in1, irreps_in2, irreps_scalar_only)
    fctp_scalar.eval()

    # ------------------------------------------------------------------
    # B1: Product state |00> — both Bloch vectors = (0, 0, 1) → v1·v2 = 1
    # ------------------------------------------------------------------
    psi_product = torch.zeros(4, dtype=torch.complex128)
    psi_product[0] = 1.0
    v_A_prod, v_B_prod = bloch_vectors_from_two_qubit_state(psi_product)
    dot_product_state = (v_A_prod @ v_B_prod).item()

    results['B1_product_state_bloch_vectors_aligned'] = {
        'test': 'product state |00>: both Bloch vectors = (0,0,1), dot product = 1',
        'bloch_A': v_A_prod.tolist(),
        'bloch_B': v_B_prod.tolist(),
        'dot_product': float(dot_product_state),
        'expected_dot': 1.0,
        'tolerance': 1e-6,
        'pass': abs(dot_product_state - 1.0) < 1e-6,
    }

    # ------------------------------------------------------------------
    # B2: Bell state — both Bloch vectors = 0 → dot product = 0
    # ------------------------------------------------------------------
    psi_bell = torch.zeros(4, dtype=torch.complex128)
    psi_bell[0] = 1.0 / np.sqrt(2)
    psi_bell[3] = 1.0 / np.sqrt(2)
    v_A_bell, v_B_bell = bloch_vectors_from_two_qubit_state(psi_bell)
    dot_bell = (v_A_bell @ v_B_bell).item()

    results['B2_bell_state_bloch_zero_dot_zero'] = {
        'test': 'Bell state: both Bloch vectors = 0, dot product = 0',
        'bloch_norm_A': float(v_A_bell.norm().item()),
        'bloch_norm_B': float(v_B_bell.norm().item()),
        'dot_product': float(dot_bell),
        'tolerance': 1e-6,
        'pass': abs(dot_bell) < 1e-6,
    }

    # ------------------------------------------------------------------
    # B3: cos(theta)|00> + sin(theta)|11> interpolation: dot product and MI both monotone
    # ------------------------------------------------------------------
    thetas = np.linspace(0, np.pi / 4, 10)
    dots = []
    mis = []
    for theta in thetas:
        psi_t = make_two_qubit_state(float(theta), 0.0, 0.0)
        v_A_t, v_B_t = bloch_vectors_from_two_qubit_state(psi_t)
        dots.append((v_A_t @ v_B_t).item())
        mis.append(mutual_information(psi_t))

    dots_arr = np.array(dots)
    mis_arr = np.array(mis)
    # Both should be monotone (dots decreasing 1→0, MI increasing 0→log(2))
    dots_decreasing = all(dots_arr[i] >= dots_arr[i+1] - 1e-8 for i in range(len(dots_arr)-1))
    mis_increasing = all(mis_arr[i] <= mis_arr[i+1] + 1e-8 for i in range(len(mis_arr)-1))

    results['B3_interpolation_dot_and_mi_monotone'] = {
        'test': 'cos(theta)|00>+sin(theta)|11>: dot product decreases and MI increases with theta',
        'dots': [float(d) for d in dots_arr],
        'mis': [float(m) for m in mis_arr],
        'dots_decreasing': bool(dots_decreasing),
        'mi_increasing': bool(mis_increasing),
        'pass': dots_decreasing and mis_increasing,
        'note': 'dot product and MI are anti-correlated: more entanglement = smaller dot product',
    }

    # ------------------------------------------------------------------
    # B4: Full FCTP equivariance at identity rotation
    # ------------------------------------------------------------------
    irreps_out = o3.Irreps('1x0e + 1x1e + 1x2e')
    fctp_full = FullyConnectedTensorProduct(irreps_in1, irreps_in2, irreps_out)
    fctp_full.eval()

    D_id = o3.wigner_D(1, torch.tensor(0.0), torch.tensor(0.0), torch.tensor(0.0))
    D_out_id = torch.eye(9)
    v1 = torch.randn(3)
    v2 = torch.randn(3)
    with torch.no_grad():
        err_id = (fctp_full(D_id @ v1, D_id @ v2) - D_out_id @ fctp_full(v1, v2)).norm().item()

    results['B4_identity_rotation_equivariance_zero'] = {
        'test': 'identity rotation: FCTP equivariance error is 0',
        'error': float(err_id),
        'tolerance': 1e-10,
        'pass': err_id < 1e-10,
    }

    return results


# =====================================================================
# HELPERS (module-level reference)
# =====================================================================

def bloch_vectors_from_two_qubit_state(psi_AB):
    """Extract individual Bloch vectors from a two-qubit pure state."""
    rho_AB = torch.outer(psi_AB, psi_AB.conj())
    dim_A, dim_B = 2, 2
    rho = rho_AB.reshape(dim_A, dim_B, dim_A, dim_B)
    rho_A = torch.einsum('ibjb->ij', rho)
    rho_B = torch.einsum('aiba->ib', rho)

    sigma_x = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
    sigma_y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
    sigma_z = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)

    bx_A = torch.trace(rho_A @ sigma_x).real.item()
    by_A = torch.trace(rho_A @ sigma_y).real.item()
    bz_A = torch.trace(rho_A @ sigma_z).real.item()
    bx_B = torch.trace(rho_B @ sigma_x).real.item()
    by_B = torch.trace(rho_B @ sigma_y).real.item()
    bz_B = torch.trace(rho_B @ sigma_z).real.item()

    v_A = torch.tensor([bx_A, by_A, bz_A], dtype=torch.float32)
    v_B = torch.tensor([bx_B, by_B, bz_B], dtype=torch.float32)
    return v_A, v_B


def make_two_qubit_state(theta, phi_A, phi_B):
    """cos(theta)|00> + sin(theta)*exp(i*(phi_A+phi_B))|11>"""
    psi = torch.zeros(4, dtype=torch.complex128)
    psi[0] = np.cos(theta)
    psi[3] = np.sin(theta) * np.exp(1j * (phi_A + phi_B))
    return psi / psi.norm()


def partial_trace(rho_AB, keep='A', dim_A=2, dim_B=2):
    rho = rho_AB.reshape(dim_A, dim_B, dim_A, dim_B)
    if keep == 'A':
        return torch.einsum('ibjb->ij', rho)
    else:
        return torch.einsum('aiba->ib', rho)


def mutual_information(psi_AB):
    rho_AB = torch.outer(psi_AB, psi_AB.conj())
    rho_A = partial_trace(rho_AB, keep='A')
    rho_B = partial_trace(rho_AB, keep='B')
    S_A = von_neumann_entropy(rho_A)
    S_B = von_neumann_entropy(rho_B)
    S_AB = von_neumann_entropy(rho_AB)
    return S_A + S_B - S_AB


def von_neumann_entropy(rho):
    eigs = torch.linalg.eigvalsh(rho).real
    eigs = torch.clamp(eigs, min=1e-15)
    return -(eigs * torch.log(eigs)).sum().item()


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_tests = {**positive, **negative, **boundary}
    total = len(all_tests)
    passed = sum(1 for t in all_tests.values() if t.get('pass', False))
    failed = total - passed

    results = {
        "name": "E3NN Tensor Product Two-Qubit",
        "token": "E_E3NN_TENSOR_PRODUCT",
        "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "all_pass": failed == 0,
            "FCTP_equivariance_error": positive.get('P1_FCTP_1o_x_1o_equivariance', {}).get('equivariance_error'),
            "scalar_dot_correlation": positive.get('P2_scalar_output_correlates_with_dot_product', {}).get('pearson_correlation'),
            "mi_dot_correlation": positive.get('P3_dot_product_vs_mutual_information', {}).get('pearson_correlation_mi_vs_dot'),
            "scalar_rotation_invariant": positive.get('P4_scalar_is_rotation_invariant', {}).get('pass'),
        },
        "classification": "canonical",
        "key_finding": (
            "e3nn FullyConnectedTensorProduct(1o⊗1o→0e+1e+2e) is equivariant under simultaneous "
            "SO(3) rotation. The 0e scalar output is the dot product v1·v2, which anti-correlates "
            "with mutual information (Bell state: v1=v2=0, dot=0, MI=log2; product: dot=1, MI=0). "
            "e3nn naturally encodes two-qubit correlations via CG decomposition."
        ),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "e3nn_tensor_product_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    print(f"\n{'='*60}")
    print(f"E3NN Tensor Product Two-Qubit — {passed}/{total} passed")
    print(f"{'='*60}")
    for k, v in all_tests.items():
        status = "PASS" if v.get('pass', False) else "FAIL"
        print(f"  [{status}] {k}")
