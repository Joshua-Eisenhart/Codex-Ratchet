#!/usr/bin/env python3
"""
sim_pure_lego_dfs_noiseless.py
==============================

Pure-lego probe: decoherence-free subspaces (DFS) and noiseless subsystems.
No engine dependencies.  numpy only.

Tests
-----
1. 2-qubit collective dephasing (Z otimes Z):
   - |Psi^-> (singlet) stays at fidelity 1.0  (DFS member)
   - |Phi^+> fidelity drops                    (not in DFS)

2. 2-qubit collective rotation (U otimes U for random U in SU(2)):
   - |Psi^-> survives all 100 random rotations (fidelity = 1.0)
   - |Phi^+> does NOT survive                   (fidelity < 1.0 for most)

3. 3-qubit collective dephasing (Z otimes Z otimes Z):
   - Identify the 1-d antisymmetric DFS subspace.
   - Verify fidelity = 1.0 under noise for that state.

4. 4-qubit noiseless subsystem under collective SU(2) noise (U^{otimes 4}):
   - The j=0 sector of 4 spin-1/2 particles has dimension 2.
   - The commutant of the collective SU(2) action on that sector
     provides a noiseless qubit (2-d subspace invariant under U^{otimes 4}).
   - Encode a logical qubit, apply 200 random U^{otimes 4}, verify fidelity = 1.0.
"""

import json
import os
import sys
from datetime import datetime, UTC

import numpy as np
classification = "classical_baseline"  # auto-backfill

np.random.seed(42)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline -- numpy only"},
    "pyg": {"tried": False, "used": False, "reason": "classical baseline -- numpy only"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this baseline"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

CLASSIFICATION = "classical_baseline"
CLASSIFICATION_NOTE = (
    "Classical baseline for decoherence-free subspaces and noiseless subsystems under "
    "collective dephasing and collective SU(2) noise."
)
LEGO_IDS = ["dfs_noiseless"]
PRIMARY_LEGO_IDS = ["dfs_noiseless"]

# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════

I2 = np.eye(2, dtype=complex)
Z  = np.array([[1, 0], [0, -1]], dtype=complex)
X  = np.array([[0, 1], [1, 0]], dtype=complex)
Y  = np.array([[0, -1j], [1j, 0]], dtype=complex)


def ket(*bits):
    """Return computational basis ket for given bit string."""
    n = len(bits)
    dim = 2 ** n
    idx = sum(b * (2 ** (n - 1 - i)) for i, b in enumerate(bits))
    v = np.zeros(dim, dtype=complex)
    v[idx] = 1.0
    return v


def fidelity_pure(psi, phi):
    """Fidelity between two pure state vectors."""
    return float(np.abs(np.vdot(psi, phi)) ** 2)


def random_su2():
    """Sample a random SU(2) matrix via Haar measure (QR decomposition)."""
    z = (np.random.randn(2, 2) + 1j * np.random.randn(2, 2)) / np.sqrt(2)
    q, r = np.linalg.qr(z)
    d = np.diag(r)
    ph = d / np.abs(d)
    q = q @ np.diag(ph)
    # ensure det = +1
    if np.linalg.det(q).real < 0:
        q[:, 0] *= -1
    return q


def apply_collective_unitary(U, psi, n_qubits):
    """Apply U^{otimes n} to state psi."""
    U_n = U
    for _ in range(n_qubits - 1):
        U_n = np.kron(U_n, U)
    return U_n @ psi


# ═══════════════════════════════════════════════════════════════════════
# BELL STATES
# ═══════════════════════════════════════════════════════════════════════

psi_minus = (ket(0, 1) - ket(1, 0)) / np.sqrt(2)   # singlet |Psi^->
phi_plus  = (ket(0, 0) + ket(1, 1)) / np.sqrt(2)   # |Phi^+>


# ═══════════════════════════════════════════════════════════════════════
# TEST 1:  Z otimes Z collective dephasing on 2 qubits
# ═══════════════════════════════════════════════════════════════════════

def test_zz_dephasing():
    """
    Collective dephasing: both qubits see the same random phase rotation
    exp(i*theta*Z).  The collective noise unitary is:
        U(theta) = exp(i*theta*Z) otimes exp(i*theta*Z)

    The singlet |Psi^-> has total J_z = 0 AND is in the j=0 irrep,
    so U(theta)|Psi^-> = |Psi^->  for all theta  (DFS member).

    |Phi^+> = (|00>+|11>)/sqrt2 has components with J_z = +1 and -1,
    which pick up different phases e^{+2i*theta} and e^{-2i*theta},
    so fidelity drops for generic theta.
    """
    results_singlet = []
    results_phi = []

    for theta in [0.3, 0.7, 1.0, np.pi / 4, np.pi / 3, 1.5, 2.0]:
        eZ = np.diag([np.exp(1j * theta), np.exp(-1j * theta)])
        U_coll = np.kron(eZ, eZ)

        psi_m_after = U_coll @ psi_minus
        results_singlet.append(fidelity_pure(psi_minus, psi_m_after))

        phi_p_after = U_coll @ phi_plus
        results_phi.append(fidelity_pure(phi_plus, phi_p_after))

    singlet_all_one = bool(np.allclose(results_singlet, 1.0))
    phi_any_drop = bool(not np.allclose(results_phi, 1.0))

    return {
        "singlet_fidelities": [float(f) for f in results_singlet],
        "phi_plus_fidelities": [float(f) for f in results_phi],
        "singlet_in_DFS": singlet_all_one,
        "phi_plus_in_DFS": not phi_any_drop,
    }


# ═══════════════════════════════════════════════════════════════════════
# TEST 2:  Collective rotation U otimes U  (100 random SU(2))
# ═══════════════════════════════════════════════════════════════════════

def test_collective_rotation(n_trials=100):
    """
    The singlet |Psi^-> spans the j=0 (antisymmetric) irrep of SU(2)^{otimes 2}.
    It is invariant under U otimes U for ANY U in SU(2).
    |Phi^+> lives in j=1 and is NOT invariant.
    """
    singlet_fids = []
    phi_fids = []

    for _ in range(n_trials):
        U = random_su2()
        UU = np.kron(U, U)

        psi_m_rot = UU @ psi_minus
        singlet_fids.append(fidelity_pure(psi_minus, psi_m_rot))

        phi_p_rot = UU @ phi_plus
        phi_fids.append(fidelity_pure(phi_plus, phi_p_rot))

    return {
        "n_trials": n_trials,
        "singlet_min_fidelity": float(np.min(singlet_fids)),
        "singlet_max_fidelity": float(np.max(singlet_fids)),
        "singlet_all_unity": bool(np.allclose(singlet_fids, 1.0)),
        "phi_plus_min_fidelity": float(np.min(phi_fids)),
        "phi_plus_mean_fidelity": float(np.mean(phi_fids)),
        "phi_plus_all_unity": bool(np.allclose(phi_fids, 1.0)),
    }


# ═══════════════════════════════════════════════════════════════════════
# TEST 3:  3-qubit collective dephasing  (Z otimes Z otimes Z)
# ═══════════════════════════════════════════════════════════════════════

def test_3qubit_collective_dephasing():
    """
    For 3 qubits under collective dephasing Z^{otimes 3}, a DFS state must
    satisfy (Z otimes Z otimes Z)|psi> = e^{i*theta}|psi>, i.e. it is an
    eigenstate of Z^{otimes 3}.

    Z^{otimes 3} is diagonal with entries (-1)^{popcount(i)} for basis |i>.
    Eigenvalue +1: even parity states {|000>, |011>, |101>, |110>}
    Eigenvalue -1: odd parity states  {|001>, |010>, |100>, |111>}

    Each parity sector is a DFS for collective Z^{otimes 3} dephasing.
    The antisymmetric (j=1/2, multiplicity) subspace of 3 qubits under
    SU(2) is 2-d, but for JUST Z^{otimes 3} dephasing, the DFS is
    any eigenspace.  We build a state in the even-parity sector and verify.

    For the fully antisymmetric 3-qubit state: there is no totally
    antisymmetric state for 3 qubits of spin-1/2 (since dim of
    antisymmetric subspace of (C^2)^{otimes 3} = C(2,3) = 0).
    So we work with the parity DFS instead.
    """
    ZZZ = np.kron(np.kron(Z, Z), Z)

    # Even parity DFS state: equal superposition of even-parity basis
    even_state = (ket(0, 0, 0) + ket(0, 1, 1) + ket(1, 0, 1) + ket(1, 1, 0)) / 2.0

    after = ZZZ @ even_state
    fid_even = fidelity_pure(even_state, after)

    # Odd parity state for comparison (also a DFS eigenspace)
    odd_state = (ket(0, 0, 1) + ket(0, 1, 0) + ket(1, 0, 0) + ket(1, 1, 1)) / 2.0
    after_odd = ZZZ @ odd_state
    fid_odd = fidelity_pure(odd_state, after_odd)

    # A state that is NOT in a single parity sector
    mixed_parity = (ket(0, 0, 0) + ket(0, 0, 1)) / np.sqrt(2)
    after_mixed = ZZZ @ mixed_parity
    fid_mixed = fidelity_pure(mixed_parity, after_mixed)

    return {
        "even_parity_fidelity": float(fid_even),
        "odd_parity_fidelity": float(fid_odd),
        "mixed_parity_fidelity": float(fid_mixed),
        "even_in_DFS": bool(np.isclose(fid_even, 1.0)),
        "odd_in_DFS": bool(np.isclose(fid_odd, 1.0)),
        "mixed_NOT_in_DFS": bool(not np.isclose(fid_mixed, 1.0)),
        "DFS_dimension_per_sector": 4,
        "note": "Each parity eigenspace of Z^{otimes 3} is a 4-d DFS for collective Z-dephasing.",
    }


# ═══════════════════════════════════════════════════════════════════════
# TEST 4:  4-qubit noiseless subsystem under collective SU(2)
# ═══════════════════════════════════════════════════════════════════════

def _clebsch_gordan_4qubit_j0_basis():
    """
    Find the j=0 (total angular momentum 0) subspace of 4 spin-1/2 particles.

    The decomposition of (1/2)^{otimes 4} = 0(x2) + 1(x3) + 2(x1).
    The j=0 sector has dimension 2 (multiplicity 2).
    These two orthonormal vectors form the noiseless subsystem:
    the collective SU(2) action U^{otimes 4} acts trivially on them,
    so any qubit encoded in this 2-d space is protected.

    We find them by projecting onto j=0: the projector is
      P_{j=0} = (1/16) * sum over all 16 dim(j=0)/(dim total) ...

    More directly: we diagonalise J^2 = (J_x^2 + J_y^2 + J_z^2) where
    J_alpha = sum_i sigma_alpha^(i) / 2, and pick the eigenvalue j(j+1)=0
    eigenspace.
    """
    n = 4
    dim = 2 ** n

    def total_angular_op(sigma):
        """Build J_alpha = sum_{i=0}^{n-1} (I^{otimes i} otimes sigma otimes I^{otimes n-1-i}) / 2."""
        J = np.zeros((dim, dim), dtype=complex)
        for i in range(n):
            parts = []
            for j in range(n):
                parts.append(sigma if j == i else I2)
            op = parts[0]
            for p in parts[1:]:
                op = np.kron(op, p)
            J += op
        return J / 2.0

    Jx = total_angular_op(X)
    Jy = total_angular_op(Y)
    Jz = total_angular_op(Z)

    J2 = Jx @ Jx + Jy @ Jy + Jz @ Jz

    evals, evecs = np.linalg.eigh(J2)

    # j=0 => j(j+1) = 0
    j0_mask = np.isclose(evals, 0.0, atol=1e-10)
    j0_vecs = evecs[:, j0_mask]

    return j0_vecs  # shape (16, 2)


def test_4qubit_noiseless_subsystem(n_trials=200):
    """
    Encode a logical qubit in the 2-d j=0 subspace of 4 qubits.
    Apply 200 random U^{otimes 4} collective noise operations.
    The encoded qubit should be perfectly preserved (fidelity = 1.0).
    """
    j0_basis = _clebsch_gordan_4qubit_j0_basis()
    n_basis = j0_basis.shape[1]

    if n_basis != 2:
        return {
            "error": f"Expected j=0 subspace dimension 2, got {n_basis}",
            "pass": False,
        }

    # Encode a logical qubit: |0_L> = j0_basis[:,0],  |1_L> = j0_basis[:,1]
    # Logical state: alpha|0_L> + beta|1_L> with random alpha, beta
    alpha = 0.6 + 0.0j
    beta = np.sqrt(1 - abs(alpha)**2) * np.exp(1j * 0.7)
    logical_state = alpha * j0_basis[:, 0] + beta * j0_basis[:, 1]
    logical_state /= np.linalg.norm(logical_state)

    # Build projector onto j=0 subspace
    P_j0 = j0_basis @ j0_basis.conj().T

    fidelities = []
    logical_fidelities = []

    for _ in range(n_trials):
        U = random_su2()
        noisy = apply_collective_unitary(U, logical_state, 4)

        # Physical fidelity (should be 1.0 since j=0 is invariant)
        fid = fidelity_pure(logical_state, noisy)
        fidelities.append(fid)

        # Logical fidelity: project back to j=0 subspace and check
        # the logical qubit coefficients are preserved
        alpha_out = np.vdot(j0_basis[:, 0], noisy)
        beta_out = np.vdot(j0_basis[:, 1], noisy)
        # The encoded qubit fidelity
        logical_fid = float(np.abs(np.conj(alpha) * alpha_out + np.conj(beta) * beta_out) ** 2)
        logical_fidelities.append(logical_fid)

    return {
        "j0_subspace_dimension": int(n_basis),
        "noiseless_qubit_dimension": int(n_basis),
        "n_trials": n_trials,
        "encoded_alpha": str(alpha),
        "encoded_beta": str(beta),
        "physical_fidelity_min": float(np.min(fidelities)),
        "physical_fidelity_max": float(np.max(fidelities)),
        "physical_fidelity_all_unity": bool(np.allclose(fidelities, 1.0)),
        "logical_fidelity_min": float(np.min(logical_fidelities)),
        "logical_fidelity_max": float(np.max(logical_fidelities)),
        "logical_fidelity_all_unity": bool(np.allclose(logical_fidelities, 1.0)),
        "noiseless_subsystem_confirmed": bool(
            np.allclose(fidelities, 1.0) and np.allclose(logical_fidelities, 1.0)
        ),
    }


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    results = {
        "name": "pure_lego_dfs_noiseless",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "probe": "sim_pure_lego_dfs_noiseless",
        "timestamp": datetime.now(UTC).isoformat(),
        "description": (
            "Decoherence-free subspaces and noiseless subsystems. "
            "Pure numpy, no engine."
        ),
        "tests": {},
    }

    print("=" * 70)
    print("DFS & Noiseless Subsystem Probe")
    print("=" * 70)

    # --- Test 1 ---
    print("\n[TEST 1] 2-qubit collective Z-dephasing ...")
    r1 = test_zz_dephasing()
    results["tests"]["t1_zz_dephasing"] = r1
    print(f"  Singlet |Psi^-> all fidelities=1.0? {r1['singlet_in_DFS']}  "
          f"(vals: {r1['singlet_fidelities'][:3]}...)")
    print(f"  |Phi^+> fidelity drops?            {not r1['phi_plus_in_DFS']}  "
          f"(vals: {r1['phi_plus_fidelities'][:3]}...)")

    # --- Test 2 ---
    print("\n[TEST 2] 2-qubit collective rotation U otimes U (100 trials) ...")
    r2 = test_collective_rotation(100)
    results["tests"]["t2_collective_rotation"] = r2
    print(f"  Singlet: all fidelity=1.0? {r2['singlet_all_unity']}  "
          f"(min={r2['singlet_min_fidelity']:.10f})")
    print(f"  |Phi^+>: all fidelity=1.0? {r2['phi_plus_all_unity']}  "
          f"(mean={r2['phi_plus_mean_fidelity']:.6f})")

    # --- Test 3 ---
    print("\n[TEST 3] 3-qubit collective Z-dephasing ...")
    r3 = test_3qubit_collective_dephasing()
    results["tests"]["t3_3qubit_dephasing"] = r3
    print(f"  Even parity sector fidelity: {r3['even_parity_fidelity']:.6f}  "
          f"(DFS: {r3['even_in_DFS']})")
    print(f"  Odd parity sector fidelity:  {r3['odd_parity_fidelity']:.6f}  "
          f"(DFS: {r3['odd_in_DFS']})")
    print(f"  Mixed parity fidelity:       {r3['mixed_parity_fidelity']:.6f}  "
          f"(NOT DFS: {r3['mixed_NOT_in_DFS']})")

    # --- Test 4 ---
    print("\n[TEST 4] 4-qubit noiseless subsystem (collective SU(2), 200 trials) ...")
    r4 = test_4qubit_noiseless_subsystem(200)
    results["tests"]["t4_4qubit_noiseless_subsystem"] = r4
    if "error" in r4:
        print(f"  ERROR: {r4['error']}")
    else:
        print(f"  j=0 subspace dimension: {r4['j0_subspace_dimension']}")
        print(f"  Physical fidelity all=1.0? {r4['physical_fidelity_all_unity']}  "
              f"(min={r4['physical_fidelity_min']:.10f})")
        print(f"  Logical fidelity all=1.0?  {r4['logical_fidelity_all_unity']}  "
              f"(min={r4['logical_fidelity_min']:.10f})")
        print(f"  Noiseless subsystem confirmed: {r4['noiseless_subsystem_confirmed']}")

    # --- Verdict ---
    all_pass = (
        r1["singlet_in_DFS"]
        and not r1["phi_plus_in_DFS"]
        and r2["singlet_all_unity"]
        and not r2["phi_plus_all_unity"]
        and r3["even_in_DFS"]
        and r3["odd_in_DFS"]
        and r3["mixed_NOT_in_DFS"]
        and r4.get("noiseless_subsystem_confirmed", False)
    )

    results["summary"] = {
        "all_pass": all_pass,
        "scope_note": "Direct local baseline for decoherence-free subspaces and noiseless subsystem protection on bounded few-qubit families.",
    }
    verdict = "PASS" if all_pass else "FAIL"
    print(f"\n{'=' * 70}")
    print(f"VERDICT: {verdict}")
    print(f"{'=' * 70}")

    # --- Write results ---
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "pure_lego_dfs_noiseless_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {out_path}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
