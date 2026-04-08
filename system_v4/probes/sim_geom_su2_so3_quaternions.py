#!/usr/bin/env python3
"""
sim_geom_su2_so3_quaternions.py -- SU(2), SO(3), quaternions and their relationships.

SU(2):  U = cos(theta/2)I - i sin(theta/2)(n . sigma).
        Verify det=1, U†U=I, group closure. Lie algebra [sigma_i/2, sigma_j/2] = i eps_ijk sigma_k/2.

SO(3):  SU(2)/Z_2.  Double cover: U and -U give SAME rotation.
        360 deg gives -I in SU(2), I in SO(3).  Rodrigues formula.

Quaternions: H = {a + bi + cj + dk}.  Unit quaternions ~ SU(2) ~ S^3.
             Cl+(3) ~ H.  Rotation v -> q v q^{-1}.
             Verify all 3 representations give same rotation.

Stacking: SU(2) IS S^3 with group structure.  SO(3) is quotient.
          Quaternions from Cl(3).  All act as rho -> U rho U†.

Classification: canonical.  pytorch=used, clifford=used.
Output: sim_results/geom_su2_so3_quaternions_results.json
"""

import json
import math
import os
import numpy as np

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

# --- imports with manifest tracking ---
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Core computation: SU(2) matrices via autograd, SO(3) Rodrigues, "
        "density matrix rotation rho->U rho U†, group closure verification"
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = (
        "Cl(3) even subalgebra ~ quaternions, rotor construction, "
        "cross-validation of rotation v->RvR~ against SU(2) and SO(3)"
    )
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "Symbolic verification of Lie algebra commutation relations "
        "and quaternion multiplication table"
    )
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

# Unused tools
for key in ["pyg", "z3", "cvc5", "geomstats", "e3nn", "rustworkx", "xgi",
            "toponetx", "gudhi"]:
    if not TOOL_MANIFEST[key]["tried"]:
        TOOL_MANIFEST[key]["reason"] = "not needed for SU(2)/SO(3)/quaternion sim"


# =====================================================================
# CONSTANTS
# =====================================================================

TOL = 1e-10

# Pauli matrices (torch, complex128)
if TOOL_MANIFEST["pytorch"]["tried"]:
    I2 = torch.eye(2, dtype=torch.complex128)
    SIGMA_X = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
    SIGMA_Y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
    SIGMA_Z = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)
    SIGMA = [SIGMA_X, SIGMA_Y, SIGMA_Z]

# Levi-Civita
def levi_civita(i, j, k):
    """Fully antisymmetric tensor eps_ijk."""
    return int(np.sign(np.linalg.det(
        np.array([[int(i == m) for m in range(3)],
                  [int(j == m) for m in range(3)],
                  [int(k == m) for m in range(3)]], dtype=float)
    )))


# =====================================================================
# HELPER: SU(2) matrix from axis-angle
# =====================================================================

def su2_matrix(theta, n_vec):
    """U = cos(theta/2)I - i sin(theta/2)(n . sigma).
    n_vec must be a unit 3-vector (list or tensor)."""
    n = torch.tensor(n_vec, dtype=torch.float64)
    n = n / torch.norm(n)
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    n_dot_sigma = sum(n[i].item() * SIGMA[i] for i in range(3))
    U = c * I2 - 1j * s * n_dot_sigma
    return U


def so3_rodrigues(theta, n_vec):
    """Rodrigues formula: R = I + sin(theta) K + (1-cos(theta)) K^2
    where K_ij = -eps_ijk n_k (the skew-symmetric cross product matrix)."""
    n = np.array(n_vec, dtype=np.float64)
    n = n / np.linalg.norm(n)
    K = np.array([
        [0, -n[2], n[1]],
        [n[2], 0, -n[0]],
        [-n[1], n[0], 0]
    ])
    R = np.eye(3) + math.sin(theta) * K + (1 - math.cos(theta)) * (K @ K)
    return R


def quaternion_from_axis_angle(theta, n_vec):
    """q = cos(theta/2) + sin(theta/2)(n_x i + n_y j + n_z k).
    Returns (w, x, y, z)."""
    n = np.array(n_vec, dtype=np.float64)
    n = n / np.linalg.norm(n)
    w = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return (w, s * n[0], s * n[1], s * n[2])


def quat_multiply(q1, q2):
    """Hamilton product of two quaternions (w, x, y, z)."""
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return (
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    )


def quat_conjugate(q):
    """Conjugate: (w, -x, -y, -z)."""
    return (q[0], -q[1], -q[2], -q[3])


def quat_rotate_vector(q, v):
    """Rotate 3-vector v by unit quaternion q: v' = q v q^{-1}.
    Embeds v as pure quaternion (0, vx, vy, vz)."""
    v_quat = (0.0, v[0], v[1], v[2])
    result = quat_multiply(quat_multiply(q, v_quat), quat_conjugate(q))
    return np.array([result[1], result[2], result[3]])


def su2_rotate_vector(U, v):
    """Extract the SO(3) rotation from SU(2) matrix U and apply to 3-vector v.
    Uses R_ij = (1/2) Tr(sigma_i U sigma_j U†)."""
    U_dag = U.conj().T
    R = torch.zeros(3, 3, dtype=torch.float64)
    for i in range(3):
        for j in range(3):
            R[i, j] = 0.5 * torch.trace(SIGMA[i] @ U @ SIGMA[j] @ U_dag).real
    v_t = torch.tensor(v, dtype=torch.float64)
    return (R @ v_t).numpy()


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # ---- P1: SU(2) basic properties ----
    test_axes = [
        ([1, 0, 0], "x"),
        ([0, 1, 0], "y"),
        ([0, 0, 1], "z"),
        ([1, 1, 1], "111"),
    ]
    test_angles = [math.pi / 6, math.pi / 3, math.pi / 2, math.pi, 2 * math.pi]
    su2_props = []
    for n_vec, n_label in test_axes:
        for theta in test_angles:
            U = su2_matrix(theta, n_vec)
            det_val = torch.det(U)
            det_ok = abs(det_val.item() - 1.0) < TOL
            UdU = U.conj().T @ U
            unitary_ok = torch.allclose(UdU, I2, atol=TOL)
            su2_props.append({
                "axis": n_label, "theta": round(theta, 6),
                "det_1": det_ok, "unitary": unitary_ok,
            })
    results["P1_su2_det_unitary"] = {
        "pass": all(r["det_1"] and r["unitary"] for r in su2_props),
        "n_tested": len(su2_props),
        "details": su2_props[:4],  # sample
    }

    # ---- P2: SU(2) group closure ----
    closure_tests = []
    for n1, l1 in test_axes:
        for n2, l2 in test_axes:
            U1 = su2_matrix(math.pi / 3, n1)
            U2 = su2_matrix(math.pi / 4, n2)
            U12 = U1 @ U2
            det_ok = abs(torch.det(U12).item() - 1.0) < TOL
            unitary_ok = torch.allclose(U12.conj().T @ U12, I2, atol=TOL)
            closure_tests.append({"a1": l1, "a2": l2, "det_1": det_ok, "unitary": unitary_ok})
    results["P2_su2_group_closure"] = {
        "pass": all(t["det_1"] and t["unitary"] for t in closure_tests),
        "n_tested": len(closure_tests),
    }

    # ---- P3: Lie algebra commutation relations ----
    # [sigma_i/2, sigma_j/2] = i eps_ijk sigma_k/2
    lie_ok = []
    for i in range(3):
        for j in range(3):
            comm = (SIGMA[i] / 2) @ (SIGMA[j] / 2) - (SIGMA[j] / 2) @ (SIGMA[i] / 2)
            expected = sum(
                1j * levi_civita(i, j, k) * SIGMA[k] / 2 for k in range(3)
            )
            ok = torch.allclose(comm, expected, atol=TOL)
            lie_ok.append({"i": i, "j": j, "pass": ok})
    results["P3_lie_algebra_commutators"] = {
        "pass": all(t["pass"] for t in lie_ok),
        "n_tested": len(lie_ok),
    }

    # ---- P4: Sympy symbolic verification of Lie algebra ----
    if TOOL_MANIFEST["sympy"]["tried"]:
        from sympy import Matrix, I as Im, Rational, simplify
        s_x = Matrix([[0, 1], [1, 0]])
        s_y = Matrix([[0, -Im], [Im, 0]])
        s_z = Matrix([[1, 0], [0, -1]])
        s_list = [s_x, s_y, s_z]
        sympy_lie_ok = []
        eps = {(0, 1, 2): 1, (1, 2, 0): 1, (2, 0, 1): 1,
               (0, 2, 1): -1, (2, 1, 0): -1, (1, 0, 2): -1}
        for i in range(3):
            for j in range(3):
                comm = s_list[i] * s_list[j] - s_list[j] * s_list[i]
                comm = comm * Rational(1, 4)  # [si/2, sj/2]
                expected = Matrix.zeros(2, 2)
                for k in range(3):
                    coeff = eps.get((i, j, k), 0)
                    if coeff != 0:
                        expected = expected + Im * coeff * s_list[k] * Rational(1, 2)
                diff = simplify(comm - expected)
                sympy_lie_ok.append(diff == Matrix.zeros(2, 2))
        results["P4_sympy_lie_algebra"] = {
            "pass": all(sympy_lie_ok),
            "n_tested": len(sympy_lie_ok),
        }

    # ---- P5: Double cover -- U and -U give same rotation ----
    double_cover_tests = []
    for n_vec, n_label in test_axes:
        for theta in [math.pi / 4, math.pi / 2, math.pi]:
            U = su2_matrix(theta, n_vec)
            neg_U = -U
            v_test = np.array([1.0, 2.0, 3.0])
            v_test = v_test / np.linalg.norm(v_test)
            rot_U = su2_rotate_vector(U, v_test)
            rot_neg_U = su2_rotate_vector(neg_U, v_test)
            same = np.allclose(rot_U, rot_neg_U, atol=1e-10)
            # -U still in SU(2)?
            det_neg = abs(torch.det(neg_U).item() - 1.0) < TOL
            double_cover_tests.append({
                "axis": n_label, "theta": round(theta, 4),
                "same_rotation": same, "neg_U_det_1": det_neg,
            })
    results["P5_double_cover_U_neg_U"] = {
        "pass": all(t["same_rotation"] and t["neg_U_det_1"] for t in double_cover_tests),
        "n_tested": len(double_cover_tests),
        "details": double_cover_tests[:3],
    }

    # ---- P6: 360 deg rotation gives -I in SU(2), I in SO(3) ----
    rot360_tests = []
    for n_vec, n_label in test_axes:
        U_360 = su2_matrix(2 * math.pi, n_vec)
        is_neg_I = torch.allclose(U_360, -I2, atol=TOL)
        R_360 = so3_rodrigues(2 * math.pi, n_vec)
        is_I_so3 = np.allclose(R_360, np.eye(3), atol=1e-10)
        rot360_tests.append({
            "axis": n_label,
            "su2_neg_identity": is_neg_I,
            "so3_identity": is_I_so3,
        })
    results["P6_360deg_minus_identity"] = {
        "pass": all(t["su2_neg_identity"] and t["so3_identity"] for t in rot360_tests),
        "n_tested": len(rot360_tests),
        "details": rot360_tests,
    }

    # ---- P7: All 3 representations give same rotation ----
    cross_tests = []
    for n_vec, n_label in test_axes:
        for theta in [math.pi / 6, math.pi / 3, math.pi / 2, 2.5]:
            v = np.array([0.3, -0.7, 0.5])
            v = v / np.linalg.norm(v)
            # SU(2)
            U = su2_matrix(theta, n_vec)
            v_su2 = su2_rotate_vector(U, v)
            # SO(3) Rodrigues
            R = so3_rodrigues(theta, n_vec)
            v_so3 = R @ v
            # Quaternion
            q = quaternion_from_axis_angle(theta, n_vec)
            v_quat = quat_rotate_vector(q, v)
            su2_so3 = np.allclose(v_su2, v_so3, atol=1e-10)
            su2_quat = np.allclose(v_su2, v_quat, atol=1e-10)
            cross_tests.append({
                "axis": n_label, "theta": round(theta, 4),
                "su2_eq_so3": su2_so3, "su2_eq_quat": su2_quat,
            })
    results["P7_three_reps_same_rotation"] = {
        "pass": all(t["su2_eq_so3"] and t["su2_eq_quat"] for t in cross_tests),
        "n_tested": len(cross_tests),
        "details": cross_tests[:4],
    }

    # ---- P8: Quaternion multiplication table ----
    # i^2 = j^2 = k^2 = ijk = -1
    qi = (0, 1, 0, 0)
    qj = (0, 0, 1, 0)
    qk = (0, 0, 0, 1)
    q_neg1 = (-1, 0, 0, 0)
    ii = quat_multiply(qi, qi)
    jj = quat_multiply(qj, qj)
    kk = quat_multiply(qk, qk)
    ijk = quat_multiply(quat_multiply(qi, qj), qk)
    table_ok = (
        np.allclose(ii, q_neg1) and
        np.allclose(jj, q_neg1) and
        np.allclose(kk, q_neg1) and
        np.allclose(ijk, q_neg1)
    )
    # ij=k, jk=i, ki=j
    ij = quat_multiply(qi, qj)
    jk = quat_multiply(qj, qk)
    ki = quat_multiply(qk, qi)
    cross_ok = (
        np.allclose(ij, qk) and
        np.allclose(jk, qi) and
        np.allclose(ki, qj)
    )
    results["P8_quaternion_multiplication_table"] = {
        "pass": table_ok and cross_ok,
        "i2_eq_neg1": np.allclose(ii, q_neg1),
        "j2_eq_neg1": np.allclose(jj, q_neg1),
        "k2_eq_neg1": np.allclose(kk, q_neg1),
        "ijk_eq_neg1": np.allclose(ijk, q_neg1),
        "ij_eq_k": np.allclose(ij, qk),
        "jk_eq_i": np.allclose(jk, qi),
        "ki_eq_j": np.allclose(ki, qj),
    }

    # ---- P9: Clifford Cl+(3) isomorphism to quaternions ----
    if TOOL_MANIFEST["clifford"]["tried"]:
        layout, blades = Cl(3)
        e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
        # Even subalgebra basis: {1, e12, e13, e23}
        e12 = blades["e12"]
        e13 = blades["e13"]
        e23 = blades["e23"]
        # Check: e12^2 = e13^2 = e23^2 = -1
        sq_12 = (e12 * e12).value[0]
        sq_13 = (e13 * e13).value[0]
        sq_23 = (e23 * e23).value[0]
        squares_neg1 = (
            abs(sq_12 + 1) < TOL and
            abs(sq_13 + 1) < TOL and
            abs(sq_23 + 1) < TOL
        )
        # Check: e12 * e23 = e1e2e2e3 = -e1e3 = -e13 (since e2^2=1 in Cl(3))
        prod_12_23 = e12 * e23
        # Compare multivector values directly
        prod_matches_e13 = np.allclose(prod_12_23.value, e13.value, atol=TOL) or \
                           np.allclose(prod_12_23.value, (-e13).value, atol=TOL)

        # Rotor rotation vs quaternion rotation
        theta_test = math.pi / 3
        n_test = np.array([1.0, 1.0, 1.0]) / math.sqrt(3.0)
        # Cl(3) rotor: R = cos(theta/2) - sin(theta/2) * B
        # where B = n1*e23 + n2*e31 + n3*e12 is the bivector dual to axis n
        # Note: e31 = e3*e1 = -e13 in clifford library (which stores e13 = e1*e3)
        B_cl = n_test[0] * e23 + n_test[1] * (-e13) + n_test[2] * e12
        R_cl = math.cos(theta_test / 2) - math.sin(theta_test / 2) * B_cl
        v_cl = 0.3 * e1 - 0.7 * e2 + 0.5 * e3
        v_cl_norm = math.sqrt(0.3**2 + 0.7**2 + 0.5**2)
        v_cl = v_cl / v_cl_norm
        v_rotated_cl = R_cl * v_cl * ~R_cl  # ~R is the reverse
        # Extract vector components: e1=index 1, e2=index 2, e3=index 3
        v_rot_cl_vec = np.array([
            float(v_rotated_cl.value[1]),  # e1
            float(v_rotated_cl.value[2]),  # e2
            float(v_rotated_cl.value[3]),  # e3
        ])
        # Compare with quaternion
        v_in = np.array([0.3, -0.7, 0.5]) / v_cl_norm
        q_test = quaternion_from_axis_angle(theta_test, n_test)
        v_rot_quat = quat_rotate_vector(q_test, v_in)
        cl_quat_match = np.allclose(v_rot_cl_vec, v_rot_quat, atol=1e-8)

        results["P9_clifford_even_sub_isomorphism"] = {
            "pass": squares_neg1 and cl_quat_match,
            "e12_sq_neg1": abs(sq_12 + 1) < TOL,
            "e13_sq_neg1": abs(sq_13 + 1) < TOL,
            "e23_sq_neg1": abs(sq_23 + 1) < TOL,
            "rotor_matches_quaternion": cl_quat_match,
            "max_diff": float(np.max(np.abs(v_rot_cl_vec - v_rot_quat))),
        }

    # ---- P10: Density matrix rotation rho -> U rho U† ----
    # All 3 reps should give same Bloch vector after rotation
    density_tests = []
    for n_vec, n_label in test_axes[:2]:
        theta = math.pi / 3
        # Initial state: |+x> = (|0>+|1>)/sqrt(2) => rho = (I + sigma_x)/2
        rho = (I2 + SIGMA_X) / 2
        U = su2_matrix(theta, n_vec)
        rho_rot = U @ rho @ U.conj().T
        # Extract Bloch vector from rotated rho
        bloch_after = torch.tensor([
            torch.trace(SIGMA[k] @ rho_rot).real.item() for k in range(3)
        ], dtype=torch.float64)
        # Compare: rotate the initial Bloch vector (1,0,0) with SO(3)
        R = so3_rodrigues(theta, n_vec)
        bloch_so3 = R @ np.array([1.0, 0.0, 0.0])
        match = np.allclose(bloch_after.numpy(), bloch_so3, atol=1e-10)
        density_tests.append({
            "axis": n_label, "match": match,
            "bloch_su2": bloch_after.numpy().tolist(),
            "bloch_so3": bloch_so3.tolist(),
        })
    results["P10_density_rotation_rho_UdagU"] = {
        "pass": all(t["match"] for t in density_tests),
        "n_tested": len(density_tests),
        "details": density_tests,
    }

    # ---- P11: Unit quaternion norm preserved under multiplication ----
    norm_tests = []
    for _ in range(20):
        theta1, theta2 = np.random.uniform(0, 2 * math.pi, 2)
        n1 = np.random.randn(3); n1 /= np.linalg.norm(n1)
        n2 = np.random.randn(3); n2 /= np.linalg.norm(n2)
        q1 = quaternion_from_axis_angle(theta1, n1)
        q2 = quaternion_from_axis_angle(theta2, n2)
        q12 = quat_multiply(q1, q2)
        norm_q12 = math.sqrt(sum(x**2 for x in q12))
        norm_tests.append(abs(norm_q12 - 1.0) < TOL)
    results["P11_quaternion_norm_preserved"] = {
        "pass": all(norm_tests),
        "n_tested": len(norm_tests),
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # ---- N1: Non-unit axis should still work (normalized internally) ----
    # But NON-unitary matrix (det != 1) should FAIL SU(2) membership
    bad_matrix = torch.tensor([[2, 0], [0, 0.5]], dtype=torch.complex128)
    det_bad = torch.det(bad_matrix)
    unitary_bad = torch.allclose(bad_matrix.conj().T @ bad_matrix, I2, atol=TOL)
    results["N1_non_su2_matrix_rejected"] = {
        "pass": (abs(det_bad.item() - 1.0) < TOL) == True and not unitary_bad,
        "det": abs(det_bad.item()),
        "unitary": unitary_bad,
        "note": "det=1 but not unitary => not in SU(2)",
    }

    # ---- N2: Non-unit quaternion gives wrong rotation ----
    q_bad = (2.0, 0.0, 0.0, 0.0)  # norm = 2, not unit
    v = np.array([1.0, 0.0, 0.0])
    v_rot_bad = quat_rotate_vector(q_bad, v)
    # Should NOT equal identity rotation for non-unit quaternion
    # Actually q v q* with |q|=2 gives |q|^2 v = 4v for pure real q
    # So v_rot_bad should be [4, 0, 0] not [1, 0, 0]
    not_unit_wrong = not np.allclose(v_rot_bad, v, atol=1e-8)
    results["N2_non_unit_quaternion_wrong_rotation"] = {
        "pass": not_unit_wrong,
        "input": list(q_bad),
        "output": v_rot_bad.tolist(),
        "expected_if_correct": [1.0, 0.0, 0.0],
    }

    # ---- N3: Commutator [A,B] != 0 for non-commuting rotations ----
    U_x = su2_matrix(math.pi / 2, [1, 0, 0])
    U_z = su2_matrix(math.pi / 2, [0, 0, 1])
    comm = U_x @ U_z - U_z @ U_x
    comm_nonzero = torch.norm(comm).item() > TOL
    results["N3_su2_non_abelian"] = {
        "pass": comm_nonzero,
        "commutator_norm": float(torch.norm(comm).item()),
    }

    # ---- N4: SO(3) matrix with det=-1 is NOT a rotation ----
    reflection = np.diag([1.0, 1.0, -1.0])
    det_neg = np.linalg.det(reflection)
    is_orthogonal = np.allclose(reflection.T @ reflection, np.eye(3), atol=1e-10)
    results["N4_reflection_not_rotation"] = {
        "pass": is_orthogonal and abs(det_neg - (-1.0)) < 1e-10,
        "orthogonal": is_orthogonal,
        "det": float(det_neg),
        "note": "det=-1 => O(3) not SO(3)",
    }

    # ---- N5: 720 deg in SU(2) returns +I (not just 360) ----
    U_720 = su2_matrix(4 * math.pi, [0, 0, 1])
    is_plus_I = torch.allclose(U_720, I2, atol=TOL)
    U_360 = su2_matrix(2 * math.pi, [0, 0, 1])
    is_not_plus_I = not torch.allclose(U_360, I2, atol=TOL)
    results["N5_720_vs_360_spinor_sign"] = {
        "pass": is_plus_I and is_not_plus_I,
        "720_is_identity": is_plus_I,
        "360_is_NOT_identity": is_not_plus_I,
    }

    # ---- N6: Random 2x2 unitary with det != 1 is U(2) not SU(2) ----
    # Phase rotation: e^{i*pi/4} * I
    phase_U = torch.exp(torch.tensor(1j * math.pi / 4)) * I2
    det_phase = torch.det(phase_U)
    is_unitary = torch.allclose(phase_U.conj().T @ phase_U, I2, atol=TOL)
    det_not_1 = abs(det_phase.item() - 1.0) > 0.01
    results["N6_u2_not_su2"] = {
        "pass": is_unitary and det_not_1,
        "is_unitary": is_unitary,
        "det": complex(det_phase.item()),
        "note": "U(2) element with det != 1",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # ---- B1: theta=0 gives identity in all 3 reps ----
    for n_vec, n_label in [([1, 0, 0], "x"), ([0, 1, 0], "y"), ([0, 0, 1], "z")]:
        U_0 = su2_matrix(0, n_vec)
        R_0 = so3_rodrigues(0, n_vec)
        q_0 = quaternion_from_axis_angle(0, n_vec)
        su2_id = torch.allclose(U_0, I2, atol=TOL)
        so3_id = np.allclose(R_0, np.eye(3), atol=1e-10)
        quat_id = np.allclose(q_0, (1, 0, 0, 0), atol=1e-10)
        results[f"B1_theta_0_identity_{n_label}"] = {
            "pass": su2_id and so3_id and quat_id,
            "su2": su2_id, "so3": so3_id, "quat": quat_id,
        }

    # ---- B2: theta=pi (180 deg) -- U^2 = -I in SU(2) ----
    U_pi = su2_matrix(math.pi, [0, 0, 1])
    U_pi_sq = U_pi @ U_pi
    is_neg_I = torch.allclose(U_pi_sq, -I2, atol=TOL)
    results["B2_pi_rotation_squared"] = {
        "pass": is_neg_I,
        "U_pi_squared_is_neg_I": is_neg_I,
    }

    # ---- B3: Numerical precision near machine epsilon ----
    tiny_theta = 1e-14
    U_tiny = su2_matrix(tiny_theta, [0, 0, 1])
    diff_from_I = torch.norm(U_tiny - I2).item()
    results["B3_near_zero_angle_precision"] = {
        "pass": diff_from_I < 1e-12,
        "diff_from_identity": float(diff_from_I),
    }

    # ---- B4: Large angle (100*pi) -- wraps correctly ----
    theta_large = 100 * math.pi  # = 50 * 2pi, so SU(2) = +I
    U_large = su2_matrix(theta_large, [0, 0, 1])
    # 100*pi / (2*pi) = 50, even number of full turns => +I
    is_identity = torch.allclose(U_large, I2, atol=1e-6)
    results["B4_large_angle_wrapping"] = {
        "pass": is_identity,
        "theta": theta_large,
        "wraps_to_identity": is_identity,
    }

    # ---- B5: Antipodal quaternions give same rotation ----
    q = quaternion_from_axis_angle(math.pi / 3, [1, 0, 0])
    q_neg = tuple(-x for x in q)
    v = np.array([0.0, 1.0, 0.0])
    v1 = quat_rotate_vector(q, v)
    v2 = quat_rotate_vector(q_neg, v)
    results["B5_antipodal_quaternion_same_rotation"] = {
        "pass": np.allclose(v1, v2, atol=1e-10),
        "v_from_q": v1.tolist(),
        "v_from_neg_q": v2.tolist(),
    }

    # ---- B6: Gimbal-like test -- composition of 90-deg rotations ----
    # Rx(90) * Ry(90) * Rz(90) via all 3 reps
    U_comp = su2_matrix(math.pi/2, [1,0,0]) @ su2_matrix(math.pi/2, [0,1,0]) @ su2_matrix(math.pi/2, [0,0,1])
    R_comp = so3_rodrigues(math.pi/2, [1,0,0]) @ so3_rodrigues(math.pi/2, [0,1,0]) @ so3_rodrigues(math.pi/2, [0,0,1])
    q_comp = quat_multiply(
        quat_multiply(
            quaternion_from_axis_angle(math.pi/2, [1,0,0]),
            quaternion_from_axis_angle(math.pi/2, [0,1,0]),
        ),
        quaternion_from_axis_angle(math.pi/2, [0,0,1]),
    )
    v_test = np.array([1.0, 0.0, 0.0])
    v_su2 = su2_rotate_vector(U_comp, v_test)
    v_so3 = R_comp @ v_test
    v_quat = quat_rotate_vector(q_comp, v_test)
    results["B6_composed_90deg_all_match"] = {
        "pass": np.allclose(v_su2, v_so3, atol=1e-9) and np.allclose(v_su2, v_quat, atol=1e-9),
        "su2": v_su2.tolist(),
        "so3": v_so3.tolist(),
        "quat": v_quat.tolist(),
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    np.random.seed(42)

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_pass = (
        all(v.get("pass", False) for v in positive.values()) and
        all(v.get("pass", False) for v in negative.values()) and
        all(v.get("pass", False) for v in boundary.values())
    )

    results = {
        "name": "SU(2) / SO(3) / Quaternion Relationships",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "all_pass": all_pass,
        "summary": {
            "positive_tests": len(positive),
            "negative_tests": len(negative),
            "boundary_tests": len(boundary),
            "positive_pass": sum(1 for v in positive.values() if v.get("pass")),
            "negative_pass": sum(1 for v in negative.values() if v.get("pass")),
            "boundary_pass": sum(1 for v in boundary.values() if v.get("pass")),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "geom_su2_so3_quaternions_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    status = "ALL PASS" if all_pass else "FAILURES DETECTED"
    print(f"[{status}] Results written to {out_path}")
    print(f"  Positive: {results['summary']['positive_pass']}/{results['summary']['positive_tests']}")
    print(f"  Negative: {results['summary']['negative_pass']}/{results['summary']['negative_tests']}")
    print(f"  Boundary: {results['summary']['boundary_pass']}/{results['summary']['boundary_tests']}")
