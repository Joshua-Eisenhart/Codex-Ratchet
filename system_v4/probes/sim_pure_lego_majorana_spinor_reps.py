#!/usr/bin/env python3
"""
sim_pure_lego_majorana_spinor_reps.py
=====================================

Pure-lego probe: Majorana stellar representation and higher-spin spinor
representations.  No engine.  numpy/scipy only.

Constructs:
  1. All spin-j irreps of su(2) for j = 0, 1/2, 1, 3/2, 2.
     Verifies dimension = 2j+1 for each.

  2. Majorana stellar representation:
     - spin-1/2 (qubit): 1 star on Bloch sphere (same as Bloch vector for
       pure states).
     - spin-1 (qutrit, d=3): 2 stars on S^2.
     - spin-3/2: 3 stars.   spin-2: 4 stars.
     - 2-qubit symmetric subspace (spin-1): also 2 stars.

  3. Clebsch-Gordan decomposition:
     1/2 x 1/2 = 0 + 1  (singlet + triplet).
     Verifies Bell state Psi^- is the singlet (j=0).
     Verifies the triplet states are the other 3 Bell states projected
     onto the symmetric subspace.

Outputs JSON to a2_state/sim_results/majorana_spinor_reps_results.json.
"""

import json
import math
import os
import sys
from datetime import datetime, UTC

import numpy as np
from scipy.linalg import expm

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

PAULI_X = np.array([[0, 1], [1, 0]], dtype=complex)
PAULI_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
PAULI_Z = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results",
)

# ═══════════════════════════════════════════════════════════════════
# PART 1: su(2) spin-j representations
# ═══════════════════════════════════════════════════════════════════

def spin_operators(j):
    """
    Build Jx, Jy, Jz matrices for spin-j in the standard |j,m> basis
    with m = j, j-1, ..., -j  (dimension 2j+1).
    """
    dim = int(2 * j + 1)
    ms = np.array([j - k for k in range(dim)])  # m values: j, j-1, ..., -j

    Jz = np.diag(ms).astype(complex)

    # J+ (raising) and J- (lowering)
    Jp = np.zeros((dim, dim), dtype=complex)
    Jm = np.zeros((dim, dim), dtype=complex)
    for i in range(dim - 1):
        m = ms[i + 1]  # target m for raising: m -> m+1
        coeff = np.sqrt(j * (j + 1) - m * (m + 1))
        Jp[i, i + 1] = coeff    # |m+1><m|
        Jm[i + 1, i] = coeff    # |m><m+1|

    Jx = 0.5 * (Jp + Jm)
    Jy = -0.5j * (Jp - Jm)

    return Jx, Jy, Jz


def verify_su2_algebra(Jx, Jy, Jz, j, tol=1e-12):
    """Verify [Jx,Jy]=iJz and cyclic, plus J^2 = j(j+1)I."""
    dim = int(2 * j + 1)
    results = {}

    # Commutation relations
    comm_xy = Jx @ Jy - Jy @ Jx
    comm_yz = Jy @ Jz - Jz @ Jy
    comm_zx = Jz @ Jx - Jx @ Jz

    results["[Jx,Jy]=iJz"] = float(np.max(np.abs(comm_xy - 1j * Jz))) < tol
    results["[Jy,Jz]=iJx"] = float(np.max(np.abs(comm_yz - 1j * Jx))) < tol
    results["[Jz,Jx]=iJy"] = float(np.max(np.abs(comm_zx - 1j * Jy))) < tol

    # Casimir J^2 = j(j+1)I
    J2 = Jx @ Jx + Jy @ Jy + Jz @ Jz
    expected = j * (j + 1) * np.eye(dim, dtype=complex)
    results["J2=j(j+1)I"] = float(np.max(np.abs(J2 - expected))) < tol

    results["dimension"] = dim
    results["dimension_correct"] = dim == int(2 * j + 1)

    return results


def build_all_spin_reps():
    """Build and verify spin-j reps for j = 0, 1/2, 1, 3/2, 2."""
    spins = [0, 0.5, 1, 1.5, 2]
    report = {}
    for j in spins:
        Jx, Jy, Jz = spin_operators(j)
        checks = verify_su2_algebra(Jx, Jy, Jz, j)
        label = f"j={j}" if j != int(j) else f"j={int(j)}"
        report[label] = checks
    return report


# ═══════════════════════════════════════════════════════════════════
# PART 2: Majorana stellar representation
# ═══════════════════════════════════════════════════════════════════

def state_to_polynomial_coeffs(psi):
    """
    Given a spin-j state |psi> in the |j,m> basis (m = j,...,-j),
    compute the Majorana polynomial coefficients c_k such that
    P(z) = sum_{k=0}^{n} c_k z^k  where n = 2j.

    The Majorana polynomial is:
      P(z) = sum_{k=0}^{n} (-1)^k C(n,k)^{1/2} psi_{n-k} z^k

    where psi_k = <j, j-k | psi> (component index k = 0..n maps to
    m = j, j-1, ..., -j).
    """
    n = len(psi) - 1  # n = 2j
    coeffs = np.zeros(n + 1, dtype=complex)
    for k in range(n + 1):
        binom = math.factorial(n) / (math.factorial(k) * math.factorial(n - k))
        coeffs[k] = ((-1) ** k) * np.sqrt(binom) * psi[n - k]
    return coeffs


def majorana_stars(psi, tol=1e-10):
    """
    Compute the Majorana stars (points on S^2) for a spin-j state.

    Returns list of (theta, phi) in radians.  Each root z of the Majorana
    polynomial maps to the Bloch sphere via stereographic projection:
      theta = 2 arctan(|z|),  phi = arg(z).
    A root at infinity corresponds to the south pole (theta=pi).
    """
    n = len(psi) - 1
    if n == 0:
        # spin-0: no stars
        return []

    coeffs = state_to_polynomial_coeffs(psi)

    # Find degree of polynomial (highest non-zero coeff)
    # Roots at infinity = n - deg(P)
    deg = n
    while deg >= 0 and abs(coeffs[deg]) < tol:
        deg -= 1

    if deg <= 0:
        # All stars at south pole or trivial
        return [(np.pi, 0.0)] * n

    # numpy roots wants coefficients in descending order
    poly_coeffs = coeffs[:deg + 1][::-1]
    roots = np.roots(poly_coeffs)

    stars = []
    for z in roots:
        r = abs(z)
        theta = 2.0 * np.arctan(r)
        phi = np.angle(z)
        stars.append((float(theta), float(phi)))

    # Add south-pole stars for roots at infinity
    n_inf = n - deg
    for _ in range(n_inf):
        stars.append((np.pi, 0.0))

    return stars


def bloch_vector_from_state(psi):
    """For a qubit pure state, compute the Bloch vector (nx, ny, nz)."""
    rho = np.outer(psi, psi.conj())
    nx = float(np.real(np.trace(PAULI_X @ rho)))
    ny = float(np.real(np.trace(PAULI_Y @ rho)))
    nz = float(np.real(np.trace(PAULI_Z @ rho)))
    return (nx, ny, nz)


def star_to_cartesian(theta, phi):
    """Convert (theta, phi) on S^2 to (x, y, z) Cartesian."""
    return (
        float(np.sin(theta) * np.cos(phi)),
        float(np.sin(theta) * np.sin(phi)),
        float(np.cos(theta)),
    )


def verify_spin_half_majorana():
    """
    For spin-1/2, the single Majorana star should coincide with the
    Bloch vector for pure states.
    """
    test_states = {
        "|0> (north pole)": np.array([1, 0], dtype=complex),
        "|1> (south pole)": np.array([0, 1], dtype=complex),
        "|+> (equator x)": np.array([1, 1], dtype=complex) / np.sqrt(2),
        "|+i> (equator y)": np.array([1, 1j], dtype=complex) / np.sqrt(2),
        "general": np.array([np.cos(0.3), np.exp(1j * 0.7) * np.sin(0.3)], dtype=complex),
    }

    results = {}
    for label, psi in test_states.items():
        psi = psi / np.linalg.norm(psi)
        bloch = bloch_vector_from_state(psi)
        stars = majorana_stars(psi)
        assert len(stars) == 1, f"Expected 1 star for spin-1/2, got {len(stars)}"
        star_cart = star_to_cartesian(*stars[0])
        diff = np.linalg.norm(np.array(bloch) - np.array(star_cart))
        results[label] = {
            "bloch_vector": list(bloch),
            "majorana_star_cartesian": list(star_cart),
            "match": float(diff) < 1e-8,
            "deviation": float(diff),
        }

    return results


def verify_spin1_majorana():
    """
    For spin-1 (qutrit), demonstrate 2 Majorana stars.
    Use standard basis states and superpositions.
    """
    test_states = {
        "|1,1> (both north)": np.array([1, 0, 0], dtype=complex),
        "|1,0> (antipodal)": np.array([0, 1, 0], dtype=complex),
        "|1,-1> (both south)": np.array([0, 0, 1], dtype=complex),
        "superposition": np.array([1, 1, 1], dtype=complex) / np.sqrt(3),
    }

    results = {}
    for label, psi in test_states.items():
        psi = psi / np.linalg.norm(psi)
        stars = majorana_stars(psi)
        assert len(stars) == 2, f"Expected 2 stars for spin-1, got {len(stars)}"
        cart = [star_to_cartesian(*s) for s in stars]
        results[label] = {
            "stars_theta_phi": [list(s) for s in stars],
            "stars_cartesian": cart,
            "n_stars": len(stars),
            "n_stars_correct": len(stars) == 2,
        }

    return results


def verify_higher_spin_majorana():
    """Verify star counts for spin-3/2 (3 stars) and spin-2 (4 stars)."""
    results = {}
    for j, n_expected in [(1.5, 3), (2, 4)]:
        dim = int(2 * j + 1)
        # Use the highest-weight state |j,j>
        psi_hw = np.zeros(dim, dtype=complex)
        psi_hw[0] = 1.0
        stars_hw = majorana_stars(psi_hw)

        # Use a random state
        rng = np.random.default_rng(42 + int(2 * j))
        psi_rand = rng.standard_normal(dim) + 1j * rng.standard_normal(dim)
        psi_rand /= np.linalg.norm(psi_rand)
        stars_rand = majorana_stars(psi_rand)

        label = f"j={j}" if j != int(j) else f"j={int(j)}"
        results[label] = {
            "dimension": dim,
            "n_stars_expected": n_expected,
            "highest_weight_n_stars": len(stars_hw),
            "highest_weight_correct": len(stars_hw) == n_expected,
            "random_state_n_stars": len(stars_rand),
            "random_state_correct": len(stars_rand) == n_expected,
            "highest_weight_stars": [list(s) for s in stars_hw],
            "random_stars": [list(s) for s in stars_rand],
        }

    return results


def verify_2qubit_symmetric_subspace():
    """
    The symmetric subspace of 2 qubits is isomorphic to spin-1.
    Map symmetric states to spin-1 and verify 2 Majorana stars.

    Symmetric basis:  |1,1> = |00>,  |1,0> = (|01>+|10>)/sqrt(2),
                      |1,-1> = |11>.
    """
    # |00>
    s00 = np.array([1, 0, 0, 0], dtype=complex)
    # (|01>+|10>)/sqrt(2)
    s_sym = np.array([0, 1, 1, 0], dtype=complex) / np.sqrt(2)
    # |11>
    s11 = np.array([0, 0, 0, 1], dtype=complex)

    # Projector onto symmetric subspace
    P_sym = np.outer(s00, s00) + np.outer(s_sym, s_sym) + np.outer(s11, s11)

    # Map 2-qubit symmetric states to spin-1 representation
    # |00> -> |1,1>,  (|01>+|10>)/sqrt2 -> |1,0>,  |11> -> |1,-1>
    mapping_matrix = np.zeros((3, 4), dtype=complex)
    mapping_matrix[0] = s00
    mapping_matrix[1] = s_sym
    mapping_matrix[2] = s11

    test_states = {
        "|00>": s00,
        "(|01>+|10>)/sqrt2": s_sym,
        "|11>": s11,
        "|00>+|11>": (s00 + s11) / np.sqrt(2),
    }

    results = {}
    for label, psi_4 in test_states.items():
        # Project onto symmetric subspace
        psi_proj = P_sym @ psi_4
        norm = np.linalg.norm(psi_proj)
        if norm < 1e-12:
            results[label] = {"in_symmetric_subspace": False}
            continue

        psi_proj /= norm

        # Map to spin-1
        psi_spin1 = mapping_matrix @ psi_proj
        psi_spin1 /= np.linalg.norm(psi_spin1)

        stars = majorana_stars(psi_spin1)
        results[label] = {
            "in_symmetric_subspace": True,
            "spin1_state": [complex(c).__repr__() for c in psi_spin1],
            "n_stars": len(stars),
            "n_stars_correct": len(stars) == 2,
            "stars": [list(s) for s in stars],
        }

    return results


# ═══════════════════════════════════════════════════════════════════
# PART 3: Clebsch-Gordan decomposition  1/2 x 1/2 = 0 + 1
# ═══════════════════════════════════════════════════════════════════

def build_clebsch_gordan_half_half():
    """
    Construct the CG decomposition for 1/2 x 1/2.

    Product basis:  |++>, |+->, |-+>, |-->
    (using |+> = |1/2, 1/2>,  |-> = |1/2, -1/2>)

    Coupled basis:
      j=1 (triplet): |1,1> = |++>
                      |1,0> = (|+->+|-+>)/sqrt(2)
                      |1,-1> = |-->
      j=0 (singlet): |0,0> = (|+->-|-+>)/sqrt(2)
    """
    # Product basis states (4-dim)
    pp = np.array([1, 0, 0, 0], dtype=complex)  # |++>
    pm = np.array([0, 1, 0, 0], dtype=complex)  # |+->
    mp = np.array([0, 0, 1, 0], dtype=complex)  # |-+>
    mm = np.array([0, 0, 0, 1], dtype=complex)  # |-->

    # Coupled states
    triplet = {
        "|1,1>": pp,
        "|1,0>": (pm + mp) / np.sqrt(2),
        "|1,-1>": mm,
    }
    singlet = {
        "|0,0>": (pm - mp) / np.sqrt(2),
    }

    # CG matrix (rows = coupled basis, cols = product basis)
    CG = np.array([
        triplet["|1,1>"],
        triplet["|1,0>"],
        triplet["|1,-1>"],
        singlet["|0,0>"],
    ])

    # Verify unitarity
    unitarity_error = float(np.max(np.abs(CG @ CG.conj().T - np.eye(4))))

    return triplet, singlet, CG, unitarity_error


def verify_bell_singlet():
    """
    Verify that Bell state Psi^- = (|01>-|10>)/sqrt(2) is the j=0 singlet.
    """
    # Bell states in computational basis
    bell_states = {
        "Phi+": np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2),   # (|00>+|11>)/sqrt(2)
        "Phi-": np.array([1, 0, 0, -1], dtype=complex) / np.sqrt(2),  # (|00>-|11>)/sqrt(2)
        "Psi+": np.array([0, 1, 1, 0], dtype=complex) / np.sqrt(2),   # (|01>+|10>)/sqrt(2)
        "Psi-": np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2),  # (|01>-|10>)/sqrt(2)
    }

    # The singlet is (|+->-|-+>)/sqrt(2)
    # In computational basis: |+-> = |01>, |-+> = |10>
    # So singlet = (|01>-|10>)/sqrt(2) = Psi^-
    singlet = (np.array([0, 1, 0, 0]) - np.array([0, 0, 1, 0])) / np.sqrt(2)

    results = {}
    for name, bell in bell_states.items():
        overlap = abs(np.dot(singlet.conj(), bell)) ** 2
        results[name] = {
            "overlap_with_singlet": float(overlap),
            "is_singlet": float(overlap) > 1 - 1e-12,
        }

    return results


def verify_triplet_bell_projection():
    """
    Verify that the triplet states (j=1) correspond to the three Bell states
    that live in the symmetric subspace:
      |1,1>  = |00> = related to Phi+ and Phi-
      |1,0>  = (|01>+|10>)/sqrt(2) = Psi+
      |1,-1> = |11> = related to Phi+ and Phi-

    Specifically:
      Psi+ is exactly |1,0>.
      Phi+ = (|00>+|11>)/sqrt(2) = (|1,1>+|1,-1>)/sqrt(2)  -- in symmetric subspace.
      Phi- = (|00>-|11>)/sqrt(2) = (|1,1>-|1,-1>)/sqrt(2)  -- in symmetric subspace.
    """
    bell_states = {
        "Phi+": np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2),
        "Phi-": np.array([1, 0, 0, -1], dtype=complex) / np.sqrt(2),
        "Psi+": np.array([0, 1, 1, 0], dtype=complex) / np.sqrt(2),
        "Psi-": np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2),
    }

    # Symmetric subspace projector
    t11 = np.array([1, 0, 0, 0], dtype=complex)             # |1,1> = |00>
    t10 = np.array([0, 1, 1, 0], dtype=complex) / np.sqrt(2)  # |1,0>
    t1m1 = np.array([0, 0, 0, 1], dtype=complex)             # |1,-1> = |11>

    P_sym = np.outer(t11, t11) + np.outer(t10, t10) + np.outer(t1m1, t1m1)

    # Triplet projector (same as symmetric subspace projector for 2 qubits)
    triplet_states = [t11, t10, t1m1]

    results = {}
    for name, bell in bell_states.items():
        # Project onto symmetric (triplet) subspace
        proj = P_sym @ bell
        proj_norm = np.linalg.norm(proj)

        # Overlap with each triplet basis state
        overlaps = {}
        for t_label, t_state in zip(["|1,1>", "|1,0>", "|1,-1>"], triplet_states):
            overlaps[t_label] = float(abs(np.dot(t_state.conj(), bell)) ** 2)

        total_triplet_weight = float(proj_norm ** 2)

        results[name] = {
            "total_triplet_projection_weight": total_triplet_weight,
            "in_symmetric_subspace": total_triplet_weight > 1 - 1e-12,
            "is_antisymmetric": total_triplet_weight < 1e-12,
            "triplet_overlaps": overlaps,
        }

    return results


def verify_total_spin_quantum_numbers():
    """
    Verify total spin quantum numbers by constructing J_total^2 and J_total_z
    in the product space.

    J_total = J_1 x I + I x J_2.
    Eigenvalues of J^2: j(j+1) with j=0 (singlet) and j=1 (triplet).
    """
    # Single-qubit operators (spin-1/2)
    Sx = 0.5 * PAULI_X
    Sy = 0.5 * PAULI_Y
    Sz = 0.5 * PAULI_Z

    # Total spin operators
    Jx = np.kron(Sx, I2) + np.kron(I2, Sx)
    Jy = np.kron(Sy, I2) + np.kron(I2, Sy)
    Jz = np.kron(Sz, I2) + np.kron(I2, Sz)
    J2 = Jx @ Jx + Jy @ Jy + Jz @ Jz

    # Eigenvalues of J^2
    evals_J2 = np.sort(np.real(np.linalg.eigvalsh(J2)))
    # Expected: j=0 gives 0*1=0 (1 state), j=1 gives 1*2=2 (3 states)
    expected_J2 = np.array([0.0, 2.0, 2.0, 2.0])

    # Eigenvalues of Jz
    evals_Jz = np.sort(np.real(np.linalg.eigvalsh(Jz)))
    # Expected: m=0 (singlet) and m=-1,0,1 (triplet)
    expected_Jz = np.array([-1.0, 0.0, 0.0, 1.0])

    # Bell states as eigenvectors
    bell_psi_minus = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)
    j2_psi_minus = float(np.real(bell_psi_minus.conj() @ J2 @ bell_psi_minus))

    bell_psi_plus = np.array([0, 1, 1, 0], dtype=complex) / np.sqrt(2)
    j2_psi_plus = float(np.real(bell_psi_plus.conj() @ J2 @ bell_psi_plus))

    return {
        "J2_eigenvalues": evals_J2.tolist(),
        "J2_eigenvalues_match": float(np.max(np.abs(evals_J2 - expected_J2))) < 1e-12,
        "Jz_eigenvalues": evals_Jz.tolist(),
        "Jz_eigenvalues_match": float(np.max(np.abs(evals_Jz - expected_Jz))) < 1e-12,
        "Psi-_J2_eigenvalue": j2_psi_minus,
        "Psi-_is_j0": abs(j2_psi_minus) < 1e-12,
        "Psi+_J2_eigenvalue": j2_psi_plus,
        "Psi+_is_j1": abs(j2_psi_plus - 2.0) < 1e-12,
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    report = {
        "probe": "sim_pure_lego_majorana_spinor_reps",
        "timestamp": datetime.now(UTC).isoformat(),
        "sections": {},
        "verdicts": {},
    }

    # --- Part 1: su(2) spin-j representations ---
    print("=" * 70)
    print("PART 1: su(2) spin-j representations")
    print("=" * 70)

    spin_rep_results = build_all_spin_reps()
    report["sections"]["spin_j_representations"] = spin_rep_results

    all_pass_1 = True
    for label, checks in spin_rep_results.items():
        ok = all(v for v in checks.values() if isinstance(v, bool))
        dim = checks["dimension"]
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass_1 = False
        print(f"  {label}: dim={dim}  {status}")
        for k, v in checks.items():
            if isinstance(v, bool):
                mark = "OK" if v else "FAIL"
                print(f"    {k}: {mark}")

    report["verdicts"]["spin_reps_all_pass"] = all_pass_1

    # --- Part 2: Majorana stellar representation ---
    print()
    print("=" * 70)
    print("PART 2: Majorana stellar representation")
    print("=" * 70)

    # spin-1/2
    print("\n  --- spin-1/2 (1 star = Bloch vector) ---")
    half_results = verify_spin_half_majorana()
    report["sections"]["majorana_spin_half"] = half_results
    all_pass_2a = True
    for label, data in half_results.items():
        status = "MATCH" if data["match"] else "MISMATCH"
        if not data["match"]:
            all_pass_2a = False
        print(f"    {label}: {status}  (dev={data['deviation']:.2e})")

    report["verdicts"]["spin_half_majorana_all_match"] = all_pass_2a

    # spin-1
    print("\n  --- spin-1 (2 stars) ---")
    spin1_results = verify_spin1_majorana()
    report["sections"]["majorana_spin1"] = spin1_results
    all_pass_2b = True
    for label, data in spin1_results.items():
        ok = data["n_stars_correct"]
        if not ok:
            all_pass_2b = False
        status = "OK" if ok else "FAIL"
        print(f"    {label}: {data['n_stars']} stars  {status}")

    report["verdicts"]["spin1_majorana_correct"] = all_pass_2b

    # higher spins
    print("\n  --- higher spins (3/2, 2) ---")
    higher_results = verify_higher_spin_majorana()
    report["sections"]["majorana_higher_spins"] = higher_results
    all_pass_2c = True
    for label, data in higher_results.items():
        hw_ok = data["highest_weight_correct"]
        rnd_ok = data["random_state_correct"]
        if not (hw_ok and rnd_ok):
            all_pass_2c = False
        print(f"    {label}: hw={data['highest_weight_n_stars']} "
              f"rand={data['random_state_n_stars']}  "
              f"{'OK' if hw_ok and rnd_ok else 'FAIL'}")

    report["verdicts"]["higher_spin_majorana_correct"] = all_pass_2c

    # 2-qubit symmetric subspace
    print("\n  --- 2-qubit symmetric subspace -> spin-1 ---")
    sym_results = verify_2qubit_symmetric_subspace()
    report["sections"]["majorana_2qubit_symmetric"] = sym_results
    all_pass_2d = True
    for label, data in sym_results.items():
        if data.get("n_stars_correct") is not None:
            ok = data["n_stars_correct"]
            if not ok:
                all_pass_2d = False
            print(f"    {label}: {data['n_stars']} stars  {'OK' if ok else 'FAIL'}")

    report["verdicts"]["2qubit_symmetric_majorana_correct"] = all_pass_2d

    # --- Part 3: Clebsch-Gordan ---
    print()
    print("=" * 70)
    print("PART 3: Clebsch-Gordan decomposition  1/2 x 1/2 = 0 + 1")
    print("=" * 70)

    triplet, singlet, CG, unitarity_err = build_clebsch_gordan_half_half()
    print(f"\n  CG matrix unitarity error: {unitarity_err:.2e}")

    report["sections"]["clebsch_gordan"] = {
        "CG_unitarity_error": unitarity_err,
        "CG_is_unitary": unitarity_err < 1e-12,
    }

    # Bell singlet
    print("\n  --- Bell state singlet check ---")
    bell_singlet_results = verify_bell_singlet()
    report["sections"]["bell_singlet"] = bell_singlet_results
    for name, data in bell_singlet_results.items():
        mark = "SINGLET" if data["is_singlet"] else "not singlet"
        print(f"    {name}: overlap={data['overlap_with_singlet']:.6f}  {mark}")

    psi_minus_is_singlet = bell_singlet_results["Psi-"]["is_singlet"]
    others_not_singlet = all(
        not bell_singlet_results[k]["is_singlet"]
        for k in ["Phi+", "Phi-", "Psi+"]
    )
    report["verdicts"]["psi_minus_is_singlet"] = psi_minus_is_singlet
    report["verdicts"]["other_bells_not_singlet"] = others_not_singlet

    # Triplet projection
    print("\n  --- Triplet (symmetric) projection of Bell states ---")
    triplet_proj_results = verify_triplet_bell_projection()
    report["sections"]["triplet_bell_projection"] = triplet_proj_results
    for name, data in triplet_proj_results.items():
        if data["in_symmetric_subspace"]:
            print(f"    {name}: IN symmetric subspace (weight={data['total_triplet_projection_weight']:.6f})")
        elif data["is_antisymmetric"]:
            print(f"    {name}: ANTISYMMETRIC (weight={data['total_triplet_projection_weight']:.6f})")
        else:
            print(f"    {name}: partial (weight={data['total_triplet_projection_weight']:.6f})")

    symmetric_bells = ["Phi+", "Phi-", "Psi+"]
    triplet_correct = all(
        triplet_proj_results[k]["in_symmetric_subspace"]
        for k in symmetric_bells
    )
    singlet_antisym = triplet_proj_results["Psi-"]["is_antisymmetric"]
    report["verdicts"]["triplet_bells_in_symmetric"] = triplet_correct
    report["verdicts"]["psi_minus_antisymmetric"] = singlet_antisym

    # Total spin quantum numbers
    print("\n  --- Total spin quantum numbers ---")
    qn_results = verify_total_spin_quantum_numbers()
    report["sections"]["total_spin_quantum_numbers"] = qn_results
    for k, v in qn_results.items():
        if isinstance(v, bool):
            print(f"    {k}: {'OK' if v else 'FAIL'}")
        elif isinstance(v, list):
            print(f"    {k}: {[round(x, 4) for x in v]}")
        else:
            print(f"    {k}: {v:.6f}")

    qn_pass = (
        qn_results["J2_eigenvalues_match"]
        and qn_results["Jz_eigenvalues_match"]
        and qn_results["Psi-_is_j0"]
        and qn_results["Psi+_is_j1"]
    )
    report["verdicts"]["quantum_numbers_correct"] = qn_pass

    # --- Overall ---
    all_verdicts = list(report["verdicts"].values())
    report["overall_pass"] = all(all_verdicts)

    print()
    print("=" * 70)
    print("OVERALL VERDICT:", "ALL PASS" if report["overall_pass"] else "SOME FAILURES")
    print("=" * 70)
    for k, v in report["verdicts"].items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")

    # --- Write results ---
    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, "majorana_spinor_reps_results.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
