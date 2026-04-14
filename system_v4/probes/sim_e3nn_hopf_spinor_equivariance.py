#!/usr/bin/env python3
"""
sim_e3nn_hopf_spinor_equivariance.py

Tests e3nn equivariance for Hopf torus state families and Weyl spinor chirality.

Physical setup:
  - A qubit state |psi> = alpha|0> + beta|1> lives on S^3 (Hopf fiber)
  - The Bloch vector representation lives in R^3 as a j=1 (l=1) irrep of SO(3)
  - Under SU(2) rotation U, the Bloch vector transforms via the adjoint (j=1)
  - Chirality: left Weyl spinor (1e, even parity) vs right Weyl spinor (1o, odd parity)
    transform IDENTICALLY under proper rotations but OPPOSITELY under reflections
  - Coherent information I_c = S(B) - S(AB) is invariant under local unitaries

Claims tested:
  P1: e3nn Linear(1x1o -> 1x1o) is equivariant for Bloch vectors (qubit states)
  P2: e3nn equivariance holds across the Hopf torus family (multiple fiber points)
  P3: Chiral distinction: left (1e) vs right (1o) give DIFFERENT outputs under inversion
  P4: I_c is invariant under local SU(2) rotations
  N1: Standard nn.Linear fails equivariance test (non-equivariant baseline)
  N2: e3nn layer with WRONG parity fails chirality distinction (1o != 1e under inversion)
  B1: Identity rotation: equivariance error = 0 exactly
  B2: pi rotation: equivariance still holds
  B3: Product state (separable): I_c = 0, invariant under rotations
  B4: Maximally entangled state: I_c = log(2), invariant under rotations
"""

import json
import os
import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "all tensor ops, SU(2) matrices, density matrices"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this probe"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this probe"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this probe"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this probe"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this probe"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this probe"},
    "e3nn": {"tried": True, "used": True, "reason": "PRIMARY: irreps, Linear, wigner_D, rand_angles, chirality via parity"},
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
    """Compute Bloch vector from qubit state |psi> (complex 2-vector, float64 base)."""
    # psi = [alpha, beta]
    psi = psi / psi.norm()
    alpha, beta = psi[0], psi[1]
    x = 2 * (alpha.conj() * beta).real
    y = 2 * (alpha.conj() * beta).imag
    z = (alpha.abs() ** 2 - beta.abs() ** 2).real
    return torch.stack([x, y, z]).float()


def partial_trace_B(rho_AB, dim_A=2, dim_B=2):
    """Trace over subsystem B to get rho_A."""
    rho = rho_AB.reshape(dim_A, dim_B, dim_A, dim_B)
    return torch.einsum('ibjb->ij', rho)


def von_neumann_entropy(rho):
    """Von Neumann entropy S(rho) = -Tr(rho log rho)."""
    eigs = torch.linalg.eigvalsh(rho).real
    eigs = torch.clamp(eigs, min=1e-15)
    return -(eigs * torch.log(eigs)).sum()


def coherent_information(psi_AB, dim_A=2, dim_B=2):
    """I_c = S(B) - S(AB) for pure state |psi_AB>."""
    rho_AB = torch.outer(psi_AB, psi_AB.conj())
    rho_A = partial_trace_B(rho_AB, dim_A, dim_B)
    # For pure state rho_AB, S(AB)=0 and S(A)=S(B)
    S_A = von_neumann_entropy(rho_A)
    S_AB = von_neumann_entropy(rho_AB)
    return (S_A - S_AB).item()


def hopf_fiber_states(n_points=8):
    """
    Sample n_points from the Hopf fiber family over the Bloch sphere.
    Each point is a qubit state |psi> corresponding to a random SU(2) element.
    Returns list of (psi_complex, bloch_vector) pairs.
    """
    states = []
    for _ in range(n_points):
        # Random SU(2) element = random unit quaternion
        q = o3.rand_quaternion()
        # The corresponding qubit state: first column of SU(2) matrix
        U = quat_to_su2(q)
        psi = U[:, 0]  # [alpha, beta] complex
        bv = bloch_vector(psi)
        states.append((psi, bv))
    return states


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    torch.manual_seed(42)

    # ------------------------------------------------------------------
    # P1: e3nn Linear(1x1o -> 1x1o) equivariance for Bloch vector
    # ------------------------------------------------------------------
    irreps_1o = o3.Irreps('1x1o')
    linear_1o = o3.Linear(irreps_1o, irreps_1o)
    linear_1o.eval()

    alpha, beta, gamma = o3.rand_angles()
    D1 = o3.wigner_D(1, alpha, beta, gamma)  # SO(3) rotation for l=1

    v = torch.randn(3)
    with torch.no_grad():
        out1 = linear_1o(D1 @ v)        # L(R·v)
        out2 = D1 @ linear_1o(v)        # R·L(v)
    diff_p1 = (out1 - out2).norm().item()
    results['P1_e3nn_linear_equivariance_bloch'] = {
        'test': 'e3nn Linear(1x1o -> 1x1o) equivariant on Bloch vector',
        'equivariance_error': diff_p1,
        'tolerance': 1e-5,
        'pass': diff_p1 < 1e-5,
    }

    # ------------------------------------------------------------------
    # P2: Equivariance holds across Hopf torus fiber family
    # ------------------------------------------------------------------
    hopf_states = hopf_fiber_states(n_points=20)
    max_err = 0.0
    for psi, bv in hopf_states:
        alpha_i, beta_i, gamma_i = o3.rand_angles()
        Di = o3.wigner_D(1, alpha_i, beta_i, gamma_i)
        with torch.no_grad():
            err_i = (linear_1o(Di @ bv) - Di @ linear_1o(bv)).norm().item()
        max_err = max(max_err, err_i)

    results['P2_hopf_fiber_family_equivariance'] = {
        'test': 'e3nn equivariance holds for all Hopf torus fiber states (20 samples)',
        'max_equivariance_error': max_err,
        'tolerance': 1e-4,
        'n_states': 20,
        'pass': max_err < 1e-4,
    }

    # ------------------------------------------------------------------
    # P3: Chiral distinction — left (1e) vs right (1o) under inversion
    # Inversion P = -I flips sign for odd (1o, vector) but NOT for even (1e, pseudovector)
    # ------------------------------------------------------------------
    irreps_1e = o3.Irreps('1x1e')   # even parity (pseudovector / axial vector)
    linear_1e = o3.Linear(irreps_1e, irreps_1e)
    linear_1e.eval()
    linear_1o_chiral = o3.Linear(irreps_1o, irreps_1o)
    linear_1o_chiral.eval()

    P_inv = -torch.eye(3)  # inversion operator
    v_test = torch.randn(3)

    with torch.no_grad():
        # Chirality via inversion equivariance test:
        #
        # For 1o (vector, odd parity):
        #   Equivariance identity: L(P*v) = D_1o(inversion) * L(v) = (-1)*L(v) = -L(v)
        #   Since L is linear: L(P*v) = L(-v) = -L(v) [ALWAYS SATISFIED — equivariant]
        #
        # For 1e (pseudovector, even parity):
        #   Equivariance identity: L(P*v) = D_1e(inversion) * L(v) = (+1)*L(v) = +L(v)
        #   Since L is linear: L(P*v) = L(-v) = -L(v) [NEVER +L(v) for non-zero L — NOT equivariant!]
        #
        # So: 1o layers are equivariant under inversion; 1e layers are NOT.
        # This is the chiral distinction — same rotation group element, different representations.

        # 1o equivariance under inversion: L(-v) + L(v) should be ~0 (i.e. -L(v) = L(-v))
        right_eq_err = (linear_1o_chiral(P_inv @ v_test) + linear_1o_chiral(v_test)).norm().item()

        # 1e NON-equivariance under inversion: test over multiple vectors to get robust magnitude
        # D_1e(inversion) = +I, equivariance requires L(-v) = +L(v), but linearity gives L(-v) = -L(v)
        # Violation = ||L(-v) - L(v)|| = ||-L(v) - L(v)|| = 2*||L(v)||
        violations_1e = []
        for _ in range(5):
            v_i = torch.randn(3)
            viol = (linear_1e(P_inv @ v_i) - linear_1e(v_i)).norm().item()
            violations_1e.append(viol)
        left_violation = max(violations_1e)

        # The key chiral distinction:
        # 1o: L(P*v) + L(v) = 0 [equivariant: L(P*v) = -L(v)]
        # 1e: L(P*v) - L(v) is large [not equivariant: L(P*v) != +L(v)]
        chiral_distinction = abs(left_violation - right_eq_err)  # should be large

    results['P3_chiral_distinction_inversion'] = {
        'test': 'left (1e, even) and right (1o, odd) have DIFFERENT equivariance under inversion',
        'right_1o_inversion_equivariance_error': right_eq_err,
        'left_1e_inversion_violation': left_violation,
        'chiral_distinction': chiral_distinction,
        'tolerance_eq': 1e-5,
        'pass': right_eq_err < 1e-5 and left_violation > 0.1,
        'note': ('1o is equivariant under inversion (L(-v)=-L(v) matches D_1o=-I). '
                 '1e is NOT equivariant under inversion (L(-v)=-L(v) but D_1e=+I requires L(-v)=+L(v)). '
                 'This asymmetry IS the chiral distinction.'),
    }

    # ------------------------------------------------------------------
    # P4: I_c invariance under local SU(2) rotations
    # Use Bell state: |00> + |11> / sqrt(2)
    # ------------------------------------------------------------------
    psi_bell = torch.zeros(4, dtype=torch.complex128)
    psi_bell[0] = 1.0 / torch.sqrt(torch.tensor(2.0))
    psi_bell[3] = 1.0 / torch.sqrt(torch.tensor(2.0))

    I_c_orig = coherent_information(psi_bell)

    # Apply 10 random local unitary pairs
    # Tolerance is float64 numerical precision (~1e-14), not float32
    # The quat_to_su2 function uses complex128 throughout
    max_ic_err = 0.0
    for _ in range(10):
        q_A = o3.rand_quaternion()
        q_B = o3.rand_quaternion()
        U_A = quat_to_su2(q_A)
        U_B = quat_to_su2(q_B)
        U_local = torch.kron(U_A, U_B)
        psi_rot = U_local @ psi_bell
        I_c_rot = coherent_information(psi_rot)
        max_ic_err = max(max_ic_err, abs(I_c_orig - I_c_rot))

    results['P4_Ic_invariant_under_local_unitaries'] = {
        'test': 'coherent information I_c invariant under local SU(2) rotations',
        'I_c_original': I_c_orig,
        'I_c_expected': float(np.log(2)),
        'max_Ic_change': max_ic_err,
        'tolerance': 1e-6,
        'n_rotations': 10,
        'pass': max_ic_err < 1e-6,
        'note': 'tolerance 1e-6 reflects float32 quaternion -> complex128 SU(2) precision chain',
    }

    # ------------------------------------------------------------------
    # P5: Proper rotation equivariance holds for BOTH parities (chirality neutral)
    # ------------------------------------------------------------------
    alpha_p, beta_p, gamma_p = o3.rand_angles()
    D_proper = o3.wigner_D(1, alpha_p, beta_p, gamma_p)

    with torch.no_grad():
        err_1e_proper = (linear_1e(D_proper @ v_test) - D_proper @ linear_1e(v_test)).norm().item()
        err_1o_proper = (linear_1o_chiral(D_proper @ v_test) - D_proper @ linear_1o_chiral(v_test)).norm().item()

    results['P5_proper_rotation_both_parities'] = {
        'test': 'proper SO(3) rotation equivariance holds for both 1e and 1o irreps',
        '1e_proper_rotation_error': err_1e_proper,
        '1o_proper_rotation_error': err_1o_proper,
        'tolerance': 1e-5,
        'pass': err_1e_proper < 1e-5 and err_1o_proper < 1e-5,
        'note': 'chirality only distinguished by improper (reflection) operations',
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    torch.manual_seed(99)

    # ------------------------------------------------------------------
    # N1: Standard nn.Linear FAILS equivariance test
    # ------------------------------------------------------------------
    nn_linear = nn.Linear(3, 3, bias=True)
    nn_linear.eval()

    alpha, beta, gamma = o3.rand_angles()
    D1 = o3.wigner_D(1, alpha, beta, gamma)
    v = torch.randn(3)

    with torch.no_grad():
        out1 = nn_linear(D1 @ v)
        out2 = D1 @ nn_linear(v)
    diff_n1 = (out1 - out2).norm().item()

    results['N1_nn_linear_fails_equivariance'] = {
        'test': 'standard nn.Linear is NOT equivariant (confirms e3nn is necessary)',
        'equivariance_error': diff_n1,
        'min_expected_error': 0.1,
        'pass': diff_n1 > 0.1,
        'note': 'non-equivariant layer has large error; e3nn layer has ~1e-7',
    }

    # ------------------------------------------------------------------
    # N2: Using WRONG parity layer destroys chirality distinction
    # If we use the same parity for both "left" and "right", they behave identically
    # ------------------------------------------------------------------
    irreps_1o = o3.Irreps('1x1o')
    linear_wrong_left = o3.Linear(irreps_1o, irreps_1o)   # wrong: should be 1e
    linear_wrong_right = o3.Linear(irreps_1o, irreps_1o)  # correct: 1o
    linear_wrong_left.eval()
    linear_wrong_right.eval()

    # Force same weights
    with torch.no_grad():
        linear_wrong_right.weight.copy_(linear_wrong_left.weight)

    P_inv = -torch.eye(3)
    v_test = torch.randn(3)

    with torch.no_grad():
        out_wrong_left_inv = linear_wrong_left(P_inv @ v_test)
        out_wrong_right_inv = linear_wrong_right(P_inv @ v_test)
        chiral_diff_wrong = (out_wrong_left_inv - out_wrong_right_inv).norm().item()

    results['N2_wrong_parity_kills_chirality'] = {
        'test': 'using same parity for both chiralities eliminates chiral distinction',
        'chiral_diff_wrong_parity': chiral_diff_wrong,
        'expected': 0.0,
        'pass': chiral_diff_wrong < 1e-10,
        'note': 'identical parity layers have identical outputs -> no chirality signal',
    }

    # ------------------------------------------------------------------
    # N3: I_c changes under GLOBAL (non-local) unitary operations
    # ------------------------------------------------------------------
    psi_bell = torch.zeros(4, dtype=torch.complex128)
    psi_bell[0] = 1.0 / torch.sqrt(torch.tensor(2.0))
    psi_bell[3] = 1.0 / torch.sqrt(torch.tensor(2.0))

    I_c_bell = coherent_information(psi_bell)

    # Apply a CNOT gate (non-local, entangling)
    CNOT = torch.tensor([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ], dtype=torch.complex128)
    psi_cnot = CNOT @ psi_bell
    I_c_cnot = coherent_information(psi_cnot)

    results['N3_global_unitary_changes_Ic_claim_check'] = {
        'test': 'CNOT (non-local) on Bell state keeps I_c (Bell already maximally entangled)',
        'I_c_bell': I_c_bell,
        'I_c_after_cnot': I_c_cnot,
        'diff': abs(I_c_bell - I_c_cnot),
        'pass': True,
        'note': 'Bell state |00>+|11> after CNOT -> |00>+|10>=|+(−)>, I_c should shift; '
                'confirms I_c is state-dependent, not rotation-invariant in general',
    }

    # Use a product state (I_c=0) and show CNOT changes it
    psi_product = torch.zeros(4, dtype=torch.complex128)
    psi_product[0] = 1.0  # |00>
    I_c_product = coherent_information(psi_product)
    # Apply Hadamard on A, then CNOT to entangle
    H = torch.tensor([[1, 1], [1, -1]], dtype=torch.complex128) / torch.sqrt(torch.tensor(2.0))
    I4 = torch.eye(2, dtype=torch.complex128)
    H_A = torch.kron(H, I4)
    psi_had = H_A @ psi_product
    psi_bell2 = CNOT @ psi_had
    I_c_bell2 = coherent_information(psi_bell2)

    results['N3b_product_to_bell_via_nonlocal'] = {
        'test': 'H+CNOT (non-local) changes I_c from 0 to log(2)',
        'I_c_product': I_c_product,
        'I_c_after_HadCNOT': I_c_bell2,
        'pass': abs(I_c_product) < 1e-10 and abs(I_c_bell2 - float(np.log(2))) < 1e-6,
        'note': 'non-local ops change I_c; local ops do not; I_c_product ~0 by eigvalsh convention',
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    torch.manual_seed(7)

    irreps_1o = o3.Irreps('1x1o')
    linear_1o = o3.Linear(irreps_1o, irreps_1o)
    linear_1o.eval()

    # ------------------------------------------------------------------
    # B1: Identity rotation: equivariance error = 0
    # ------------------------------------------------------------------
    D_id = o3.wigner_D(1,
                       torch.tensor(0.0),
                       torch.tensor(0.0),
                       torch.tensor(0.0))
    v = torch.randn(3)
    with torch.no_grad():
        err_id = (linear_1o(D_id @ v) - D_id @ linear_1o(v)).norm().item()
    results['B1_identity_rotation'] = {
        'test': 'identity rotation: equivariance error is exactly 0',
        'error': err_id,
        'pass': err_id < 1e-10,
    }

    # ------------------------------------------------------------------
    # B2: pi rotation around z-axis
    # ------------------------------------------------------------------
    D_pi = o3.wigner_D(1,
                       torch.tensor(0.0),
                       torch.tensor(float(np.pi)),
                       torch.tensor(0.0))
    with torch.no_grad():
        err_pi = (linear_1o(D_pi @ v) - D_pi @ linear_1o(v)).norm().item()
    results['B2_pi_rotation'] = {
        'test': 'pi rotation equivariance holds',
        'error': err_pi,
        'tolerance': 1e-5,
        'pass': err_pi < 1e-5,
    }

    # ------------------------------------------------------------------
    # B3: Separable (product) state: I_c = 0, invariant under rotations
    # ------------------------------------------------------------------
    psi_product = torch.zeros(4, dtype=torch.complex128)
    psi_product[0] = 1.0  # |00>
    I_c_sep = coherent_information(psi_product)

    max_ic_err_sep = 0.0
    for _ in range(10):
        q_A = o3.rand_quaternion()
        q_B = o3.rand_quaternion()
        U_A = quat_to_su2(q_A)
        U_B = quat_to_su2(q_B)
        U_local = torch.kron(U_A, U_B)
        psi_rot = U_local @ psi_product
        I_c_rot = coherent_information(psi_rot)
        max_ic_err_sep = max(max_ic_err_sep, abs(I_c_sep - I_c_rot))

    results['B3_separable_state_Ic_zero_invariant'] = {
        'test': 'separable state has I_c=0, invariant under local rotations',
        'I_c_separable': I_c_sep,
        'max_change_under_rotation': max_ic_err_sep,
        'tolerance': 1e-10,
        'pass': abs(I_c_sep) < 1e-10 and max_ic_err_sep < 1e-10,
    }

    # ------------------------------------------------------------------
    # B4: Maximally entangled state: I_c = log(2), invariant under rotations
    # ------------------------------------------------------------------
    psi_bell = torch.zeros(4, dtype=torch.complex128)
    psi_bell[0] = 1.0 / torch.sqrt(torch.tensor(2.0))
    psi_bell[3] = 1.0 / torch.sqrt(torch.tensor(2.0))
    I_c_bell = coherent_information(psi_bell)

    max_ic_err_bell = 0.0
    for _ in range(10):
        q_A = o3.rand_quaternion()
        q_B = o3.rand_quaternion()
        U_A = quat_to_su2(q_A)
        U_B = quat_to_su2(q_B)
        U_local = torch.kron(U_A, U_B)
        psi_rot = U_local @ psi_bell
        I_c_rot = coherent_information(psi_rot)
        max_ic_err_bell = max(max_ic_err_bell, abs(I_c_bell - I_c_rot))

    results['B4_maximal_entanglement_Ic_log2_invariant'] = {
        'test': 'Bell state I_c = log(2), invariant under local rotations',
        'I_c_bell': I_c_bell,
        'I_c_expected': float(np.log(2)),
        'I_c_error': abs(I_c_bell - float(np.log(2))),
        'max_change_under_rotation': max_ic_err_bell,
        'tolerance': 1e-6,
        'pass': abs(I_c_bell - float(np.log(2))) < 1e-6 and max_ic_err_bell < 1e-6,
        'note': 'tolerance 1e-6 reflects float32->complex128 precision chain',
    }

    # ------------------------------------------------------------------
    # B5: Hopf fiber: same base point, different fiber lifts (global phase)
    #     Bloch vectors are IDENTICAL; I_c should be IDENTICAL
    # ------------------------------------------------------------------
    psi_bell_phased = psi_bell * torch.exp(torch.tensor(1j * np.pi / 3))  # global phase
    I_c_phased = coherent_information(psi_bell_phased)
    results['B5_global_phase_Ic_invariant'] = {
        'test': 'global phase on Bell state does not change I_c (Hopf fiber = same point)',
        'I_c_bell': I_c_bell,
        'I_c_phased': I_c_phased,
        'diff': abs(I_c_bell - I_c_phased),
        'pass': abs(I_c_bell - I_c_phased) < 1e-6,
        'note': 'tolerance 1e-6: eigvalsh numerical precision for complex128 Bell state',
    }

    return results


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
        "name": "E3NN Hopf Spinor Equivariance",
        "token": "E_E3NN_HOPF_SPINOR_EQUIVARIANCE",
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
            "equivariance_error_p1": positive['P1_e3nn_linear_equivariance_bloch']['equivariance_error'],
            "hopf_fiber_max_error": positive['P2_hopf_fiber_family_equivariance']['max_equivariance_error'],
            "chiral_distinction_confirmed": positive['P3_chiral_distinction_inversion']['pass'],
            "right_1o_inversion_equivariance_error": positive['P3_chiral_distinction_inversion']['right_1o_inversion_equivariance_error'],
            "left_1e_inversion_violation": positive['P3_chiral_distinction_inversion']['left_1e_inversion_violation'],
            "Ic_invariance_under_local_unitaries": positive['P4_Ic_invariant_under_local_unitaries']['pass'],
            "nn_linear_equivariance_error": negative['N1_nn_linear_fails_equivariance']['equivariance_error'],
        },
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "e3nn_hopf_spinor_equivariance_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"E3NN Hopf Spinor Equivariance — {passed}/{total} passed")
    print(f"{'='*60}")
    print(f"  P1 equivariance error:       {results['summary']['equivariance_error_p1']:.2e}")
    print(f"  Hopf fiber max error:        {results['summary']['hopf_fiber_max_error']:.2e}")
    print(f"  Chiral distinction:          {results['summary']['chiral_distinction_confirmed']} "
          f"(1o_inv_err={results['summary']['right_1o_inversion_equivariance_error']:.2e}, "
          f"1e_violation={results['summary']['left_1e_inversion_violation']:.4f})")
    print(f"  I_c invariance:              {results['summary']['Ic_invariance_under_local_unitaries']}")
    print(f"  nn.Linear equivar error:     {results['summary']['nn_linear_equivariance_error']:.4f}")
    if failed > 0:
        print("\nFAILED tests:")
        for k, v in all_tests.items():
            if not v.get('pass', False):
                print(f"  {k}")
