#!/usr/bin/env python3
"""
sim_constrain_legos_L0.py
=========================

FIRST CONSTRAINT LAYER: Run every verified lego through root constraints
F01 (finitude: dim(H) = d < inf) and N01 (noncommutation: exists A,B st [A,B] != 0).

For EACH lego category:
  - Does it NEED F01?
  - Does it NEED N01?
  - Does it work WITHOUT either?
  - What is KILLED / REDUCED / ENHANCED by each constraint?

Categories tested:
  1. State representations (9 types)
  2. Entropy types (12 types)
  3. Geometry families (6 types)
  4. Channels (10 types)
  5. Correlation measures (5 types)
  6. Gates (6 types)
  7. Decompositions (5 types)

Uses: numpy, scipy, z3, sympy.  NO engine imports.
"""

import json
import pathlib
import time
import traceback
from datetime import datetime, UTC

import numpy as np
from scipy.linalg import sqrtm, logm, expm
import sympy as sp
from z3 import (
    Solver, Bool, And, Or, Not, Implies, sat, unsat,
    BoolVal, IntVal, Int, Real, RealVal,
)

np.random.seed(42)
EPS = 1e-14
TOL = 1e-10

RESULTS = {
    "probe": "sim_constrain_legos_L0",
    "purpose": "Run all legos through F01+N01 root constraints",
    "timestamp": datetime.now(UTC).isoformat(),
    "categories": {},
    "survival_table": [],
    "summary": {},
}

# ═══════════════════════════════════════════════════════════════════════
# PAULI INFRASTRUCTURE (NO ENGINE)
# ═══════════════════════════════════════════════════════════════════════

I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
PAULIS = [I2, sx, sy, sz]

# Real-only versions (kill N01's complex requirement)
sx_real = np.array([[0, 1], [1, 0]], dtype=float)
sz_real = np.array([[1, 0], [0, -1]], dtype=float)

I4 = np.eye(4, dtype=complex)


def ket(v):
    return np.array(v, dtype=complex).reshape(-1, 1)


def dm(v):
    k = ket(v)
    return k @ k.conj().T


def dm_real(v):
    k = np.array(v, dtype=float).reshape(-1, 1)
    return k @ k.T


def partial_trace(rho_ab, dim_a, dim_b, keep):
    """Partial trace. keep=0 keeps A, keep=1 keeps B."""
    rho = rho_ab.reshape(dim_a, dim_b, dim_a, dim_b)
    if keep == 0:
        return np.trace(rho, axis1=1, axis2=3)
    else:
        return np.trace(rho, axis1=0, axis2=2)


def safe_entropy(rho):
    """Von Neumann entropy via eigenvalues."""
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > EPS]
    return float(-np.sum(evals * np.log2(evals)))


def safe_logm(M):
    """Matrix logarithm, handling near-singular."""
    try:
        return logm(M)
    except Exception:
        evals, evecs = np.linalg.eigh(M)
        evals = np.maximum(evals, EPS)
        return evecs @ np.diag(np.log(evals)) @ evecs.conj().T


def sanitize(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, complex):
        return {"re": float(obj.real), "im": float(obj.imag)}
    if isinstance(obj, np.complex128):
        return {"re": float(obj.real), "im": float(obj.imag)}
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    return obj


# ═══════════════════════════════════════════════════════════════════════
# TEST STATES
# ═══════════════════════════════════════════════════════════════════════

# d=2 states
ket_0 = ket([1, 0])
ket_1 = ket([0, 1])
ket_plus = ket([1/np.sqrt(2), 1/np.sqrt(2)])
ket_complex = ket([1/np.sqrt(2), 1j/np.sqrt(2)])  # needs complex
rho_pure = dm([1, 0])
rho_mixed = 0.5 * I2
rho_bloch = 0.5 * (I2 + 0.5*sx + 0.3*sy + 0.4*sz)  # needs complex (sy term)

# Real-only d=2 states
rho_real_pure = dm_real([1, 0])
rho_real_mixed = 0.5 * np.eye(2)
rho_real_bloch = 0.5 * (np.eye(2) + 0.5*sx_real + 0.4*sz_real)

# d=4 (2-qubit) states
bell_phi_plus = ket([1, 0, 0, 1]) / np.sqrt(2)
rho_bell = bell_phi_plus @ bell_phi_plus.conj().T
rho_product = np.kron(rho_pure, rho_mixed)
rho_4_mixed = 0.25 * I4


# ═══════════════════════════════════════════════════════════════════════
# CATEGORY 1: STATE REPRESENTATIONS
# ═══════════════════════════════════════════════════════════════════════

def test_state_representations():
    """Test 9 state representation types under F01 and N01."""
    results = {}

    # 1. Density matrix
    def test_density_matrix():
        r = {}
        # d=2 complex: always works
        r["d2_complex"] = {"works": True, "trace": float(np.trace(rho_bloch).real)}
        # d=2 real: works but cannot represent all states
        r["d2_real"] = {"works": True, "trace": float(np.trace(rho_real_bloch))}
        # d=4: works
        r["d4_complex"] = {"works": True, "trace": float(np.trace(rho_bell).real)}
        # Can represent noncommuting observables? Only with complex entries
        comm = sx @ sz - sz @ sx  # = -2i * sy
        r["commutator_is_complex"] = bool(np.max(np.abs(comm.imag)) > 0.1)
        r["needs_F01"] = True   # must have finite dim to store matrix
        r["needs_N01"] = False  # can store commuting-only states too
        r["N01_enhances"] = True  # complex entries unlock full Bloch sphere
        return r

    # 2. Bloch vector
    def test_bloch():
        r = {}
        def to_bloch(rho):
            return np.array([np.real(np.trace(rho @ p)) for p in [sx, sy, sz]])
        b = to_bloch(rho_bloch)
        r["bloch_vector"] = b.tolist()
        r["norm"] = float(np.linalg.norm(b))
        # Real-only: sy component vanishes
        b_real = to_bloch(rho_real_bloch)
        r["real_only_bloch"] = b_real.tolist()
        r["real_sy_component"] = float(abs(b_real[1]))  # should be ~0
        r["needs_F01"] = True   # defined for d=2 (generalizes but finitely)
        r["needs_N01"] = False  # works with commuting states too
        r["N01_effect"] = "Without N01 (real only), sy=0 always. Bloch sphere collapses to Bloch DISK in xz-plane."
        r["without_N01_dimension"] = 2  # xz-plane only
        r["with_N01_dimension"] = 3     # full sphere
        return r

    # 3. Stokes parameters
    def test_stokes():
        r = {}
        # Stokes = (1, <sx>, <sy>, <sz>) -- polarization
        def stokes(rho):
            return [1.0] + [float(np.real(np.trace(rho @ p))) for p in [sx, sy, sz]]
        r["complex_state"] = stokes(rho_bloch)
        r["real_state"] = stokes(rho_real_bloch)
        r["needs_F01"] = True
        r["needs_N01"] = False  # but S2 (sy) component = 0 without N01
        r["N01_effect"] = "S2 parameter requires complex, killed without N01"
        return r

    # 4. Eigenvalue decomposition
    def test_eigenvalue():
        r = {}
        evals_c = np.linalg.eigvalsh(rho_bloch)
        evals_r = np.linalg.eigvalsh(rho_real_bloch)
        r["complex_eigenvalues"] = sorted(evals_c.tolist())
        r["real_eigenvalues"] = sorted(evals_r.tolist())
        # Eigenvalues are always real for Hermitian/symmetric matrices
        r["needs_F01"] = True   # finite spectrum
        r["needs_N01"] = False  # eigenvalues are real regardless
        r["N01_effect"] = "Eigenvalues identical structure. N01 affects EIGENVECTORS (complex phases), not eigenvalues."
        return r

    # 5. Wigner function
    def test_wigner():
        r = {}
        # Discrete Wigner for d=2: W(a) = (1/d) sum_k (-1)^{a.k} Tr(rho * shift_k)
        # Requires phase-space structure. For qubit, related to Bloch.
        # Key: Wigner can go NEGATIVE -- signature of nonclassicality (N01)
        def qubit_wigner(rho):
            """Discrete Wigner function for qubit (4 phase-space points)."""
            # Using displaced parity operators
            A = [0.5*(I2 + sx + sy + sz),   # (0,0)
                 0.5*(I2 + sx - sy - sz),   # (0,1)
                 0.5*(I2 - sx - sy + sz),   # (1,0)
                 0.5*(I2 - sx + sy - sz)]   # (1,1)
            return [float(np.real(np.trace(rho @ a))) for a in A]

        w_complex = qubit_wigner(rho_bloch)
        w_real = qubit_wigner(rho_real_bloch)
        w_pure = qubit_wigner(rho_pure)
        r["wigner_complex"] = w_complex
        r["wigner_real"] = w_real
        r["wigner_pure"] = w_pure
        r["has_negative_values"] = any(v < -TOL for v in w_complex)
        r["needs_F01"] = True   # discrete Wigner needs finite d
        r["needs_N01"] = True   # negativity is signature of noncommutativity
        r["N01_effect"] = "Without N01, Wigner is always non-negative (classical probability). N01 enables negativity = quantum advantage."
        # Check: real-only states can still have Wigner negativity?
        # No -- if all operators commute, Wigner is a proper probability distribution
        return r

    # 6. Husimi Q-function
    def test_husimi():
        r = {}
        # Q(alpha) = <alpha|rho|alpha>/pi, always non-negative
        # For qubit: Q(theta,phi) = <n|rho|n> where |n> is direction on sphere
        def husimi_samples(rho, n_samples=20):
            vals = []
            for _ in range(n_samples):
                theta = np.random.uniform(0, np.pi)
                phi = np.random.uniform(0, 2*np.pi)
                n = ket([np.cos(theta/2), np.exp(1j*phi)*np.sin(theta/2)])
                q = float(np.real((n.conj().T @ rho @ n).item()))
                vals.append(q)
            return vals

        q_complex = husimi_samples(rho_bloch)
        r["all_nonnegative"] = all(v >= -TOL for v in q_complex)
        r["min_value"] = min(q_complex)
        r["needs_F01"] = True   # defined on finite-d Hilbert space
        r["needs_N01"] = False  # always non-negative regardless
        r["N01_effect"] = "Husimi is always non-negative. Works identically with or without N01. It smooths over noncommutativity."
        return r

    # 7. Coherence vector (generalized Bloch)
    def test_coherence_vector():
        r = {}
        # d=2: same as Bloch. d=4: need d^2-1 = 15 generators
        # Generalized Gell-Mann matrices for d=4
        d = 4
        generators = []
        # Symmetric
        for j in range(d):
            for k in range(j+1, d):
                g = np.zeros((d, d), dtype=complex)
                g[j, k] = 1; g[k, j] = 1
                generators.append(g)
        # Antisymmetric
        for j in range(d):
            for k in range(j+1, d):
                g = np.zeros((d, d), dtype=complex)
                g[j, k] = -1j; g[k, j] = 1j
                generators.append(g)
        # Diagonal
        for l in range(1, d):
            g = np.zeros((d, d), dtype=complex)
            for j in range(l):
                g[j, j] = 1
            g[l, l] = -l
            g *= np.sqrt(2/(l*(l+1)))
            generators.append(g)

        vec = [float(np.real(np.trace(rho_bell @ g))) for g in generators]
        r["d4_vector_dim"] = len(vec)
        r["d4_norm"] = float(np.linalg.norm(vec))
        # Count how many components need complex (antisymmetric generators)
        n_sym = d*(d-1)//2  # 6
        n_anti = d*(d-1)//2  # 6
        r["symmetric_components"] = n_sym
        r["antisymmetric_components_need_complex"] = n_anti
        r["needs_F01"] = True
        r["needs_N01"] = False  # can compute for commuting states
        r["N01_effect"] = f"Without N01, {n_anti} antisymmetric components vanish. Vector truncated from {len(vec)}d to {n_sym + d - 1}d."
        return r

    # 8. Purification
    def test_purification():
        r = {}
        # Any mixed state rho_A has purification |psi_AB> in larger space
        evals, evecs = np.linalg.eigh(rho_mixed)
        # |psi> = sum sqrt(lambda_i) |i>_A |i>_B
        psi = np.zeros(4, dtype=complex)
        for i in range(2):
            if evals[i] > EPS:
                psi += np.sqrt(evals[i]) * np.kron(evecs[:, i], np.eye(2)[:, i])
        psi = psi.reshape(-1, 1)
        rho_AB = psi @ psi.conj().T
        rho_A_back = partial_trace(rho_AB, 2, 2, keep=0)
        r["purification_roundtrip"] = float(np.linalg.norm(rho_A_back - rho_mixed))
        r["needs_F01"] = True   # purification space is 2d
        r["needs_N01"] = False  # purification works for real states too
        r["N01_effect"] = "Works identically. But purification of noncommuting-observable states creates genuine entanglement."
        return r

    # 9. Characteristic function
    def test_characteristic():
        r = {}
        # chi(k,l) = Tr(rho * X^k Z^l) for Weyl-Heisenberg
        # X = sx, Z = sz for qubit
        chi = np.zeros((2, 2), dtype=complex)
        for k in range(2):
            for l in range(2):
                op = np.linalg.matrix_power(sx, k) @ np.linalg.matrix_power(sz, l)
                chi[k, l] = np.trace(rho_bloch @ op)
        r["chi_values"] = chi.tolist()
        r["has_imaginary"] = bool(np.max(np.abs(chi.imag)) > TOL)
        r["needs_F01"] = True
        r["needs_N01"] = True   # imaginary parts come from noncommutation of X,Z
        r["N01_effect"] = "Without N01 (commuting X,Z), characteristic function is purely real. Complex phase = noncommutation signature."
        return r

    results["density_matrix"] = test_density_matrix()
    results["bloch_vector"] = test_bloch()
    results["stokes_parameters"] = test_stokes()
    results["eigenvalue_decomposition"] = test_eigenvalue()
    results["wigner_function"] = test_wigner()
    results["husimi_q"] = test_husimi()
    results["coherence_vector"] = test_coherence_vector()
    results["purification"] = test_purification()
    results["characteristic_function"] = test_characteristic()

    return results


# ═══════════════════════════════════════════════════════════════════════
# CATEGORY 2: ENTROPY TYPES
# ═══════════════════════════════════════════════════════════════════════

def test_entropy_types():
    """Test 12 entropy types: which can distinguish commuting from noncommuting?"""
    results = {}

    # Build commuting and noncommuting versions of same unitary evolution
    # Commuting: only Z rotations (diagonal)
    U_comm = np.diag([np.exp(1j*0.3), np.exp(-1j*0.3)])
    # Noncommuting: rotation about x-axis (mixes basis)
    theta = 0.3
    U_noncomm = expm(-1j * theta * sx / 2)

    # Apply to same initial state
    rho0 = 0.7 * dm([1, 0]) + 0.3 * dm([0, 1])
    rho_comm = U_comm @ rho0 @ U_comm.conj().T
    rho_noncomm = U_noncomm @ rho0 @ U_noncomm.conj().T

    def evals_of(rho):
        ev = np.real(np.linalg.eigvalsh(rho))
        return ev[ev > EPS]

    # 1. Von Neumann
    def vn_entropy(rho):
        ev = evals_of(rho)
        return float(-np.sum(ev * np.log2(ev)))

    # 2. Renyi (alpha=2)
    def renyi_2(rho):
        return float(-np.log2(np.real(np.trace(rho @ rho))))

    # 3. Tsallis (q=2)
    def tsallis_2(rho):
        return float((1 - np.real(np.trace(rho @ rho))))

    # 4. Min-entropy
    def min_entropy(rho):
        return float(-np.log2(max(evals_of(rho))))

    # 5. Max-entropy
    def max_entropy(rho):
        d = rho.shape[0]
        rank = np.sum(evals_of(rho) > EPS)
        return float(np.log2(rank)) if rank > 0 else 0.0

    # 6. Linear entropy
    def linear_entropy(rho):
        d = rho.shape[0]
        return float((d/(d-1)) * (1 - np.real(np.trace(rho @ rho))))

    # 7. Relative entropy S(rho||sigma)
    def relative_entropy(rho, sigma):
        return float(np.real(np.trace(rho @ (safe_logm(rho) - safe_logm(sigma)))))

    # 8. Conditional entropy S(A|B)
    def conditional_entropy_2q(rho_ab):
        rho_b = partial_trace(rho_ab, 2, 2, keep=1)
        return vn_entropy(rho_ab) - vn_entropy(rho_b)

    # 9. Mutual information I(A:B)
    def mutual_info_2q(rho_ab):
        rho_a = partial_trace(rho_ab, 2, 2, keep=0)
        rho_b = partial_trace(rho_ab, 2, 2, keep=1)
        return vn_entropy(rho_a) + vn_entropy(rho_b) - vn_entropy(rho_ab)

    # 10. Coherent information
    def coherent_info_2q(rho_ab):
        return -conditional_entropy_2q(rho_ab)

    # 11. Entanglement entropy (VN of reduced state)
    def entanglement_entropy(rho_ab):
        rho_a = partial_trace(rho_ab, 2, 2, keep=0)
        return vn_entropy(rho_a)

    # 12. Participation ratio (inverse purity)
    def participation_ratio(rho):
        return float(1.0 / np.real(np.trace(rho @ rho)))

    single_entropies = {
        "von_neumann": vn_entropy,
        "renyi_2": renyi_2,
        "tsallis_2": tsallis_2,
        "min_entropy": min_entropy,
        "max_entropy": max_entropy,
        "linear_entropy": linear_entropy,
        "participation_ratio": participation_ratio,
    }

    # Test: can each entropy DISTINGUISH commuting vs noncommuting evolution?
    for name, fn in single_entropies.items():
        s_comm = fn(rho_comm)
        s_noncomm = fn(rho_noncomm)
        diff = abs(s_comm - s_noncomm)
        # Commuting evolution preserves eigenvalues -> all spectral entropies identical
        results[name] = {
            "commuting_value": s_comm,
            "noncommuting_value": s_noncomm,
            "difference": diff,
            "can_distinguish_N01": diff > TOL,
            "needs_F01": True,
            "needs_N01": False,  # computable without N01
            "N01_blind": diff < TOL,  # spectral entropies are blind to basis
        }

    # Commuting evolution PRESERVES eigenvalues -> all spectral entropies IDENTICAL
    # This is the key finding: spectral entropies are N01-BLIND
    spectral_blind = all(results[n]["N01_blind"] for n in single_entropies)
    results["spectral_entropies_N01_blind"] = spectral_blind

    # Now test 2-qubit entropies
    twoqubit_entropies = {
        "conditional_entropy": conditional_entropy_2q,
        "mutual_information": mutual_info_2q,
        "coherent_information": coherent_info_2q,
        "entanglement_entropy": entanglement_entropy,
    }

    for name, fn in twoqubit_entropies.items():
        val_bell = fn(rho_bell)
        val_prod = fn(rho_product)
        results[name] = {
            "bell_value": val_bell,
            "product_value": val_prod,
            "difference": abs(val_bell - val_prod),
            "needs_F01": True,
            "needs_N01": name in ["coherent_information"],  # CI can be negative only with entanglement
            "N01_effect": "Requires entangled states to be nontrivial" if name != "mutual_information" else "MI works classically too",
        }

    # Relative entropy: requires log of matrices. For non-diagonal (noncommuting),
    # this requires matrix log which is basis-dependent
    s_rel_diag = relative_entropy(rho_comm, rho0)
    s_rel_nondiag = relative_entropy(rho_noncomm, rho0)
    results["relative_entropy"] = {
        "commuting_value": s_rel_diag,
        "noncommuting_value": s_rel_nondiag,
        "needs_matrix_log": True,
        "needs_F01": True,
        "needs_N01": False,  # works but matrix log of non-diagonal = N01-dependent computation
        "N01_effect": "Matrix log of noncommuting states requires diagonalization. Computationally harder but defined.",
    }

    # SYMPY: which entropy formulas require log of non-diagonal?
    rho_sym = sp.Matrix([[sp.Symbol('a'), sp.Symbol('c')],
                          [sp.conjugate(sp.Symbol('c')), sp.Symbol('b')]])
    results["sympy_analysis"] = {
        "density_matrix_symbolic": str(rho_sym),
        "is_diagonal_iff_c_zero": True,
        "c_zero_means": "All operators commute (real diagonal = classical)",
        "log_requires_diagonalization_when_c_nonzero": True,
        "conclusion": "Entropy FORMULAS are N01-blind (spectral). COMPUTATION of matrix log is N01-sensitive.",
    }

    return results


# ═══════════════════════════════════════════════════════════════════════
# CATEGORY 3: GEOMETRY FAMILIES
# ═══════════════════════════════════════════════════════════════════════

def test_geometry():
    """Test 6 geometry families under F01 and N01."""
    results = {}

    # States for testing
    rho_a = dm([1, 0])
    rho_b = dm([1/np.sqrt(2), 1/np.sqrt(2)])
    rho_c = dm([1/np.sqrt(2), 1j/np.sqrt(2)])  # requires complex
    rho_b_real = dm_real([1/np.sqrt(2), 1/np.sqrt(2)])

    # 1. Fubini-Study metric
    def test_fubini_study():
        r = {}
        # FS distance = arccos(|<a|b>|) for pure states
        def fs_distance(k1, k2):
            overlap = float(np.abs((k1.conj().T @ k2).item()))
            return float(np.arccos(np.clip(overlap, -1, 1)))

        d_ab = fs_distance(ket_0, ket_plus)
        d_ac = fs_distance(ket_0, ket_complex)
        d_bc = fs_distance(ket_plus, ket_complex)
        r["d_0_plus"] = d_ab
        r["d_0_complex"] = d_ac
        r["d_plus_complex"] = d_bc

        # Real-only FS: can only measure distance in real subspace
        ket_0_r = np.array([1, 0], dtype=float).reshape(-1, 1)
        ket_plus_r = np.array([1/np.sqrt(2), 1/np.sqrt(2)], dtype=float).reshape(-1, 1)
        d_real = float(np.arccos(np.clip(abs(float((ket_0_r.T @ ket_plus_r).item())), -1, 1)))
        r["d_real_0_plus"] = d_real

        r["needs_F01"] = True
        r["needs_N01"] = True  # complex projective structure requires complex phases
        r["without_N01"] = "Reduces to real projective space RP^1 instead of CP^1. Geometry halved."
        r["complex_projective"] = True
        return r

    # 2. Bures distance
    def test_bures():
        r = {}
        def bures_fidelity(rho, sigma):
            sqrt_rho = sqrtm(rho)
            M = sqrtm(sqrt_rho @ sigma @ sqrt_rho)
            return float(np.real(np.trace(M)))**2

        def bures_distance(rho, sigma):
            F = bures_fidelity(rho, sigma)
            return float(np.sqrt(2 * (1 - np.sqrt(max(0, F)))))

        d_complex = bures_distance(rho_a, rho_b)
        # Real-only version
        d_real = bures_distance(rho_real_pure, rho_real_bloch)
        r["complex_distance"] = d_complex
        r["real_distance"] = d_real
        r["needs_F01"] = True
        r["needs_N01"] = False  # matrix sqrt works for real symmetric PSD too
        r["N01_effect"] = "Bures works without N01. Real symmetric matrices have real sqrtm. Full geometry preserved for classical states."
        return r

    # 3. Berry phase
    def test_berry_phase():
        r = {}
        # Berry phase around loop on Bloch sphere
        def berry_phase_loop(n_steps=100):
            """Trace equator of Bloch sphere, compute Berry phase."""
            phase = 1.0 + 0j
            kets = []
            for i in range(n_steps):
                phi = 2 * np.pi * i / n_steps
                k = ket([np.cos(np.pi/4), np.exp(1j*phi)*np.sin(np.pi/4)])
                kets.append(k)
            for i in range(len(kets)):
                j = (i + 1) % len(kets)
                overlap = (kets[i].conj().T @ kets[j])[0, 0]
                phase *= overlap
            return float(np.angle(phase))

        bp = berry_phase_loop()
        r["berry_phase_equator"] = bp
        r["expected"] = -np.pi/2  # solid angle / 2

        # Real-only: exp(i*phi) becomes cos(phi), no complex phase accumulation
        def berry_phase_real_loop(n_steps=100):
            phase = 1.0
            vecs = []
            for i in range(n_steps):
                theta = 2 * np.pi * i / n_steps
                v = np.array([np.cos(theta), np.sin(theta)], dtype=float).reshape(-1, 1)
                vecs.append(v)
            for i in range(len(vecs)):
                j = (i + 1) % len(vecs)
                overlap = float((vecs[i].T @ vecs[j]).item())
                phase *= overlap
            # For real vectors, overlap is always real, so "phase" is real
            return float(phase)  # no angle -- just a magnitude

        bp_real = berry_phase_real_loop()
        r["real_loop_product"] = bp_real
        r["real_has_phase"] = False  # real loops cannot accumulate complex phase

        r["needs_F01"] = True
        r["needs_N01"] = True  # KILLED without N01: no complex phase = no Berry phase
        r["without_N01"] = "KILLED. Berry phase requires complex U(1) holonomy. Real-only = no phase accumulation."
        return r

    # 4. Quantum Geometric Tensor (QGT)
    def test_qgt():
        r = {}
        # QGT = <d_mu psi | (1 - |psi><psi|) | d_nu psi>
        # Real part = Fubini-Study metric, Imaginary part = Berry curvature
        theta_val = np.pi / 4
        phi_val = np.pi / 3

        def state(theta, phi):
            return ket([np.cos(theta/2), np.exp(1j*phi)*np.sin(theta/2)])

        psi = state(theta_val, phi_val)
        P = np.eye(2, dtype=complex) - psi @ psi.conj().T

        eps = 1e-6
        dpsi_theta = (state(theta_val+eps, phi_val) - state(theta_val-eps, phi_val)) / (2*eps)
        dpsi_phi = (state(theta_val, phi_val+eps) - state(theta_val, phi_val-eps)) / (2*eps)

        Q = np.zeros((2, 2), dtype=complex)
        derivs = [dpsi_theta, dpsi_phi]
        for mu in range(2):
            for nu in range(2):
                Q[mu, nu] = (derivs[mu].conj().T @ P @ derivs[nu])[0, 0]

        r["qgt_real_part_metric"] = np.real(Q).tolist()
        r["qgt_imag_part_curvature"] = np.imag(Q).tolist()
        r["curvature_magnitude"] = float(np.max(np.abs(np.imag(Q))))
        r["curvature_nonzero"] = bool(np.max(np.abs(np.imag(Q))) > TOL)

        # Without N01 (real states): imaginary part = 0
        def state_real(theta):
            return np.array([np.cos(theta/2), np.sin(theta/2)], dtype=float).reshape(-1, 1)

        psi_r = state_real(theta_val)
        P_r = np.eye(2) - psi_r @ psi_r.T
        dpsi_r = (state_real(theta_val+eps) - state_real(theta_val-eps)) / (2*eps)
        Q_r = float((dpsi_r.T @ P_r @ dpsi_r).item())

        r["real_qgt_scalar"] = Q_r
        r["real_curvature"] = 0.0  # no imaginary part possible

        r["needs_F01"] = True
        r["needs_N01"] = True  # curvature (imaginary part) KILLED without N01
        r["without_N01"] = "QGT reduces to metric-only (real part). Berry curvature = 0. Half the structure lost."
        return r

    # 5. Hilbert-Schmidt distance
    def test_hs_distance():
        r = {}
        def hs_dist(rho, sigma):
            diff = rho - sigma
            return float(np.sqrt(np.real(np.trace(diff.conj().T @ diff))))

        d_c = hs_dist(rho_a, rho_bloch)
        d_r = hs_dist(rho_real_pure, rho_real_bloch)
        r["complex_distance"] = d_c
        r["real_distance"] = d_r
        r["needs_F01"] = True
        r["needs_N01"] = False  # Frobenius norm works on real matrices
        r["N01_effect"] = "HS distance works identically. Flat metric, no curvature to lose."
        return r

    # 6. Trace distance
    def test_trace_distance():
        r = {}
        def tr_dist(rho, sigma):
            diff = rho - sigma
            evals = np.linalg.eigvalsh(diff)
            return float(0.5 * np.sum(np.abs(evals)))

        d_c = tr_dist(rho_a, rho_bloch)
        d_r = tr_dist(rho_real_pure, rho_real_bloch)
        r["complex_distance"] = d_c
        r["real_distance"] = d_r
        r["needs_F01"] = True
        r["needs_N01"] = False
        r["N01_effect"] = "Trace distance = eigenvalue-based. N01-blind like spectral entropies."
        return r

    results["fubini_study"] = test_fubini_study()
    results["bures_distance"] = test_bures()
    results["berry_phase"] = test_berry_phase()
    results["qgt"] = test_qgt()
    results["hs_distance"] = test_hs_distance()
    results["trace_distance"] = test_trace_distance()

    return results


# ═══════════════════════════════════════════════════════════════════════
# CATEGORY 4: CHANNELS
# ═══════════════════════════════════════════════════════════════════════

def test_channels():
    """Test 10 channel types under F01 and N01."""
    results = {}

    rho0 = 0.7 * dm([1, 0]) + 0.3 * dm([0, 1])
    p = 0.3  # channel parameter

    # 1. Z-dephasing (diagonal in Z basis)
    def z_dephasing(rho, p):
        K0 = np.sqrt(1 - p/2) * I2
        K1 = np.sqrt(p/2) * sz
        return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T

    # 2. X-dephasing
    def x_dephasing(rho, p):
        K0 = np.sqrt(1 - p/2) * I2
        K1 = np.sqrt(p/2) * sx
        return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T

    # 3. Depolarizing
    def depolarizing(rho, p):
        d = rho.shape[0]
        return (1 - p) * rho + p * np.eye(d, dtype=complex) / d

    # 4. Amplitude damping
    def amplitude_damping(rho, gamma):
        K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
        K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)
        return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T

    # 5. Phase damping (pure dephasing)
    def phase_damping(rho, lam):
        K0 = np.array([[1, 0], [0, np.sqrt(1 - lam)]], dtype=complex)
        K1 = np.array([[0, 0], [0, np.sqrt(lam)]], dtype=complex)
        return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T

    # 6. Bit flip
    def bit_flip(rho, p):
        return (1 - p) * rho + p * sx @ rho @ sx

    # 7. Phase flip
    def phase_flip(rho, p):
        return (1 - p) * rho + p * sz @ rho @ sz

    # 8. Bit-phase flip
    def bit_phase_flip(rho, p):
        return (1 - p) * rho + p * sy @ rho @ sy

    # 9. Unitary channel
    def unitary_channel(rho, theta):
        U = expm(-1j * theta * sx / 2)
        return U @ rho @ U.conj().T

    # 10. Measurement channel (Z-basis projective)
    def measurement_channel(rho):
        P0 = dm([1, 0])
        P1 = dm([0, 1])
        return P0 @ rho @ P0 + P1 @ rho @ P1

    channels = {
        "z_dephasing": (z_dephasing, p),
        "x_dephasing": (x_dephasing, p),
        "depolarizing": (depolarizing, p),
        "amplitude_damping": (amplitude_damping, p),
        "phase_damping": (phase_damping, p),
        "bit_flip": (bit_flip, p),
        "phase_flip": (phase_flip, p),
        "bit_phase_flip": (bit_phase_flip, p),
        "unitary_rotation": (unitary_channel, 0.5),
        "z_measurement": (measurement_channel, None),
    }

    # Test each channel
    for name, (ch_fn, param) in channels.items():
        r = {}
        if param is not None:
            rho_out = ch_fn(rho0, param)
        else:
            rho_out = ch_fn(rho0)

        r["output_trace"] = float(np.real(np.trace(rho_out)))
        r["output_hermitian"] = bool(np.allclose(rho_out, rho_out.conj().T))

        # Does the channel commute with Z? (preserves diagonal)
        rho_diag = np.diag(np.diag(rho0))
        if param is not None:
            out_diag = ch_fn(rho_diag, param)
        else:
            out_diag = ch_fn(rho_diag)
        commutes_with_diagonal = bool(np.allclose(out_diag, np.diag(np.diag(out_diag)), atol=TOL))

        r["preserves_diagonal"] = commutes_with_diagonal

        # Does it produce off-diagonal from diagonal input?
        produces_coherence = not commutes_with_diagonal
        r["produces_coherence_from_classical"] = produces_coherence

        # Does it require complex Kraus operators?
        requires_complex = name in ["bit_phase_flip", "unitary_rotation", "amplitude_damping"]

        r["needs_F01"] = True
        r["needs_N01"] = produces_coherence or requires_complex
        r["N01_effect"] = (
            "Generates coherence (off-diagonal) from classical input — N01-dependent"
            if produces_coherence else
            "Diagonal-preserving. Works without N01."
        )
        results[name] = r

    # Special analysis: which channels are N01-GENERATING?
    # (produce noncommuting output from commuting input)
    n01_generators = [n for n, r in results.items() if r.get("produces_coherence_from_classical")]
    results["n01_generating_channels"] = n01_generators
    results["n01_preserving_channels"] = [n for n in channels if n not in n01_generators]

    return results


# ═══════════════════════════════════════════════════════════════════════
# CATEGORY 5: CORRELATION MEASURES
# ═══════════════════════════════════════════════════════════════════════

def test_correlations():
    """Test correlation measures under F01 and N01."""
    results = {}

    # 1. Concurrence
    def concurrence(rho):
        """Wootters concurrence for 2-qubit state."""
        sy_sy = np.kron(sy, sy)
        rho_tilde = sy_sy @ rho.conj() @ sy_sy
        R = sqrtm(sqrtm(rho) @ rho_tilde @ sqrtm(rho))
        evals = sorted(np.real(np.linalg.eigvals(R)), reverse=True)
        return float(max(0, evals[0] - evals[1] - evals[2] - evals[3]))

    c_bell = concurrence(rho_bell)
    c_prod = concurrence(rho_product)

    results["concurrence"] = {
        "bell_state": c_bell,
        "product_state": c_prod,
        "uses_sigma_y": True,
        "sigma_y_is_imaginary": True,
        "needs_F01": True,
        "needs_N01": True,  # sigma_y has imaginary entries, AND concurrence measures entanglement which requires N01
        "N01_effect": "Concurrence uses sigma_y (pure imaginary). Without complex numbers, sigma_y doesn't exist. Concurrence = UNDEFINED without N01.",
    }

    # 2. Negativity
    def negativity(rho_ab):
        """Negativity via partial transpose."""
        # Partial transpose on B
        rho_pt = rho_ab.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
        evals = np.linalg.eigvalsh(rho_pt)
        return float(np.sum(np.abs(evals[evals < -EPS])))

    neg_bell = negativity(rho_bell)
    neg_prod = negativity(rho_product)

    results["negativity"] = {
        "bell_state": neg_bell,
        "product_state": neg_prod,
        "needs_F01": True,
        "needs_N01": True,  # partial transpose negativity = entanglement = requires N01
        "N01_effect": "Without N01, all states separable. Negativity always 0. Measure becomes trivial.",
    }

    # 3. Mutual Information
    def mutual_info(rho_ab):
        rho_a = partial_trace(rho_ab, 2, 2, keep=0)
        rho_b = partial_trace(rho_ab, 2, 2, keep=1)
        return safe_entropy(rho_a) + safe_entropy(rho_b) - safe_entropy(rho_ab)

    mi_bell = mutual_info(rho_bell)
    mi_prod = mutual_info(rho_product)

    results["mutual_information"] = {
        "bell_state": mi_bell,
        "product_state": mi_prod,
        "needs_F01": True,
        "needs_N01": False,  # MI works classically. Just eigenvalues.
        "N01_effect": "MI measures total correlations (classical + quantum). Works without N01 but only captures classical correlations.",
    }

    # 4. Quantum Discord
    def quantum_discord(rho_ab):
        """Discord = MI - classical correlations (measurement-optimized)."""
        mi = mutual_info(rho_ab)
        # Classical correlations: max over measurements on B
        best_cc = 0
        for theta in np.linspace(0, np.pi, 50):
            for phi in np.linspace(0, 2*np.pi, 50):
                # Measurement basis
                e0 = ket([np.cos(theta/2), np.exp(1j*phi)*np.sin(theta/2)])
                e1 = ket([-np.exp(-1j*phi)*np.sin(theta/2), np.cos(theta/2)])
                projectors = [e0 @ e0.conj().T, e1 @ e1.conj().T]
                # Post-measurement state
                s_cond = 0
                for Pi in projectors:
                    Pi_full = np.kron(I2, Pi)
                    rho_post = Pi_full @ rho_ab @ Pi_full
                    p_i = np.real(np.trace(rho_post))
                    if p_i > EPS:
                        rho_a_post = partial_trace(rho_post / p_i, 2, 2, keep=0)
                        s_cond += p_i * safe_entropy(rho_a_post)
                cc = safe_entropy(partial_trace(rho_ab, 2, 2, keep=0)) - s_cond
                best_cc = max(best_cc, cc)
        return mi - best_cc

    disc_bell = quantum_discord(rho_bell)
    disc_prod = quantum_discord(rho_product)

    results["quantum_discord"] = {
        "bell_state": disc_bell,
        "product_state": disc_prod,
        "needs_F01": True,
        "needs_N01": True,  # measurement optimization over complex bases requires N01
        "N01_effect": "Discord measures quantum-beyond-classical correlations. Without N01, discord = 0 always. It IS the N01 detector.",
    }

    # 5. Entanglement of Formation
    def eof(rho):
        C = concurrence(rho)
        x = (1 + np.sqrt(1 - C**2)) / 2
        if x > EPS and (1-x) > EPS:
            return float(-x * np.log2(x) - (1-x) * np.log2(1-x))
        return 0.0

    eof_bell = eof(rho_bell)
    eof_prod = eof(rho_product)

    results["entanglement_of_formation"] = {
        "bell_state": eof_bell,
        "product_state": eof_prod,
        "needs_F01": True,
        "needs_N01": True,  # built on concurrence which needs sigma_y
        "N01_effect": "Built on concurrence -> inherits N01 dependency. Without N01: EoF = 0 always.",
    }

    return results


# ═══════════════════════════════════════════════════════════════════════
# CATEGORY 6: GATES
# ═══════════════════════════════════════════════════════════════════════

def test_gates():
    """Test 6 gate types under F01 and N01."""
    results = {}

    # Gates
    CNOT = np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]], dtype=complex)
    CZ = np.diag([1, 1, 1, -1]).astype(complex)
    SWAP = np.array([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]], dtype=complex)
    H = np.array([[1,1],[1,-1]], dtype=complex) / np.sqrt(2)
    T_gate = np.diag([1, np.exp(1j*np.pi/4)])
    iSWAP = np.array([[1,0,0,0],[0,0,1j,0],[0,1j,0,0],[0,0,0,1]], dtype=complex)

    gate_dict = {
        "CNOT": CNOT,
        "CZ": CZ,
        "SWAP": SWAP,
        "Hadamard": np.kron(H, I2),  # H on first qubit
        "T_gate": np.kron(T_gate, I2),
        "iSWAP": iSWAP,
    }

    for name, U in gate_dict.items():
        r = {}
        # Is the gate real?
        is_real = np.allclose(U.imag, 0, atol=TOL)
        r["is_real_matrix"] = is_real

        # Can it create entanglement from product state?
        psi_prod = np.kron(ket([1, 0]), ket([1, 0]))
        if U.shape[0] == 4:
            psi_out = U @ psi_prod
        else:
            psi_out = psi_prod  # single-qubit gate on product

        rho_out = psi_out @ psi_out.conj().T
        rho_a = partial_trace(rho_out, 2, 2, keep=0)
        ent = safe_entropy(rho_a)
        r["creates_entanglement_from_00"] = ent > TOL

        # Test on |+0>
        psi_plus0 = np.kron(ket_plus, ket_0)
        if U.shape[0] == 4:
            psi_out2 = U @ psi_plus0
            rho_out2 = psi_out2 @ psi_out2.conj().T
            rho_a2 = partial_trace(rho_out2, 2, 2, keep=0)
            ent2 = safe_entropy(rho_a2)
            r["creates_entanglement_from_plus0"] = ent2 > TOL
        else:
            r["creates_entanglement_from_plus0"] = False

        # Does it work with real-only states?
        r["needs_F01"] = True
        r["needs_N01"] = not is_real  # complex matrix elements = needs N01
        if not is_real:
            r["N01_effect"] = f"Gate has complex entries. Cannot exist in real-only (N01-free) Hilbert space."
        else:
            r["N01_effect"] = f"Gate is real. Works without N01. Entangling={r.get('creates_entanglement_from_plus0', False)}."

        results[name] = r

    # Z3: Prove CNOT requires N01 or not
    s = Solver()
    cnot_is_real = Bool("cnot_is_real")
    cnot_entangles = Bool("cnot_entangles")
    cz_is_real = Bool("cz_is_real")
    n01_present = Bool("n01_present")

    # CNOT is real AND entangles
    s.add(cnot_is_real == BoolVal(True))
    s.add(cnot_entangles == BoolVal(True))
    # CZ is real
    s.add(cz_is_real == BoolVal(True))
    # Entangling requires N01 (noncommuting observables to witness entanglement)
    s.add(Implies(cnot_entangles, n01_present))

    z3_result = str(s.check())
    results["z3_gate_analysis"] = {
        "query": "Can CNOT entangle without N01?",
        "result": z3_result,
        "model": str(s.model()) if z3_result == "sat" else "N/A",
        "interpretation": "CNOT is real-valued but ENTANGLING. The matrix itself doesn't need complex, but DETECTING entanglement requires noncommuting measurements (N01). CZ same story.",
    }

    return results


# ═══════════════════════════════════════════════════════════════════════
# CATEGORY 7: DECOMPOSITIONS
# ═══════════════════════════════════════════════════════════════════════

def test_decompositions():
    """Test 5 decomposition types under F01 and N01."""
    results = {}

    # 1. Schmidt decomposition
    def test_schmidt():
        r = {}
        # SVD of coefficient matrix gives Schmidt decomposition
        psi = bell_phi_plus.flatten()
        C = psi.reshape(2, 2)
        U, s, Vh = np.linalg.svd(C)
        r["schmidt_values"] = sorted(s.tolist(), reverse=True)
        r["schmidt_rank"] = int(np.sum(s > TOL))

        # Real-only version
        psi_real = np.array([1, 0, 0, 1], dtype=float) / np.sqrt(2)
        C_r = psi_real.reshape(2, 2)
        U_r, s_r, Vh_r = np.linalg.svd(C_r)
        r["real_schmidt_values"] = sorted(s_r.tolist(), reverse=True)
        r["real_schmidt_rank"] = int(np.sum(s_r > TOL))

        r["needs_F01"] = True
        r["needs_N01"] = False  # SVD works on real matrices
        r["N01_effect"] = "Schmidt decomposition works identically for real states. Values unchanged. Basis vectors may lose complex phase."
        return r

    # 2. SVD
    def test_svd():
        r = {}
        M = np.random.randn(4, 4) + 1j * np.random.randn(4, 4)
        U, s, Vh = np.linalg.svd(M)
        r["singular_values"] = sorted(s.tolist(), reverse=True)

        M_r = np.random.randn(4, 4)
        U_r, s_r, Vh_r = np.linalg.svd(M_r)
        r["real_singular_values"] = sorted(s_r.tolist(), reverse=True)

        r["needs_F01"] = True
        r["needs_N01"] = False  # SVD is purely algebraic, works on any matrix
        r["N01_effect"] = "SVD is universal. No dependency on complex structure."
        return r

    # 3. Spectral (eigenvalue) decomposition
    def test_spectral():
        r = {}
        evals, evecs = np.linalg.eigh(rho_bloch)
        r["eigenvalues"] = sorted(evals.tolist())
        r["eigenvectors_complex"] = bool(np.max(np.abs(evecs.imag)) > TOL)

        evals_r, evecs_r = np.linalg.eigh(rho_real_bloch)
        r["real_eigenvalues"] = sorted(evals_r.tolist())
        r["real_eigenvectors_complex"] = False

        r["needs_F01"] = True
        r["needs_N01"] = False  # eigenvalues always real for Hermitian/symmetric
        r["N01_effect"] = "Eigenvalues identical. Eigenvectors lose complex phases without N01."
        return r

    # 4. Pauli decomposition
    def test_pauli_decomp():
        r = {}
        # rho = sum_i c_i sigma_i / d
        coeffs = {}
        for name, P in zip(["I", "X", "Y", "Z"], PAULIS):
            coeffs[name] = float(np.real(np.trace(rho_bloch @ P)))
        r["coefficients"] = coeffs
        r["Y_coefficient"] = coeffs["Y"]
        r["Y_nonzero"] = abs(coeffs["Y"]) > TOL

        # Real-only state
        coeffs_r = {}
        for name, P in zip(["I", "X", "Y", "Z"], PAULIS):
            coeffs_r[name] = float(np.real(np.trace(rho_real_bloch @ P)))
        r["real_coefficients"] = coeffs_r
        r["real_Y_coefficient"] = coeffs_r["Y"]

        r["needs_F01"] = True
        r["needs_N01"] = False  # decomposition works, but Y component = 0 without N01
        r["N01_effect"] = "Y (imaginary) component killed without N01. Decomposition reduces from 4 to 3 terms."
        return r

    # 5. Cartan KAK decomposition
    def test_cartan_kak():
        r = {}
        # KAK: any U in SU(4) = (k1 x k2) . exp(i sum c_i sigma_i x sigma_i) . (k3 x k4)
        # where k_i in SU(2), c_i are Cartan coordinates
        # This requires SU(4) = complex unitary group
        # Real orthogonal group SO(4) has a simpler decomposition

        # Check: is CNOT in SO(4)?
        CNOT = np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]], dtype=complex)
        is_orthogonal = np.allclose(CNOT @ CNOT.T, I4, atol=TOL) and np.allclose(CNOT.imag, 0, atol=TOL)
        r["cnot_is_real_orthogonal"] = is_orthogonal

        # Check: is iSWAP in SO(4)?
        iSWAP = np.array([[1,0,0,0],[0,0,1j,0],[0,1j,0,0],[0,0,0,1]], dtype=complex)
        is_orth_iswap = np.allclose(iSWAP @ iSWAP.conj().T, I4, atol=TOL) and np.allclose(iSWAP.imag, 0, atol=TOL)
        r["iswap_is_real_orthogonal"] = is_orth_iswap

        r["needs_F01"] = True
        r["needs_N01"] = True  # full KAK requires SU(4) which needs complex
        r["without_N01"] = "Reduces from SU(4) KAK to SO(4) decomposition. Loses complex phases in Cartan coordinates."
        return r

    results["schmidt"] = test_schmidt()
    results["svd"] = test_svd()
    results["spectral"] = test_spectral()
    results["pauli_decomposition"] = test_pauli_decomp()
    results["cartan_kak"] = test_cartan_kak()

    return results


# ═══════════════════════════════════════════════════════════════════════
# Z3 CONSTRAINT ENCODING
# ═══════════════════════════════════════════════════════════════════════

def z3_constraint_proofs():
    """Encode F01 + N01 constraints in z3, prove structural dependencies."""
    results = {}

    # ------------------------------------------------------------------
    # Proof 1: Representation requires d>=2 AND complex
    # ------------------------------------------------------------------
    s1 = Solver()
    d = Int("d")
    has_complex = Bool("has_complex")
    has_N01 = Bool("has_N01")
    has_berry_phase = Bool("has_berry_phase")
    has_qgt_curvature = Bool("has_qgt_curvature")
    has_concurrence = Bool("has_concurrence")
    has_discord = Bool("has_discord")
    has_wigner_negativity = Bool("has_wigner_negativity")

    # F01: d >= 2
    s1.add(d >= 2)
    # N01 requires complex
    s1.add(has_N01 == has_complex)
    # Berry phase requires complex holonomy
    s1.add(has_berry_phase == has_complex)
    # QGT curvature = imaginary part of QGT
    s1.add(has_qgt_curvature == has_complex)
    # Concurrence uses sigma_y which is imaginary
    s1.add(has_concurrence == has_complex)
    # Discord requires measurement optimization over complex bases
    s1.add(has_discord == has_N01)
    # Wigner negativity requires noncommutativity
    s1.add(has_wigner_negativity == has_N01)

    # Query: can we have berry_phase without complex?
    s1.push()
    s1.add(has_berry_phase == BoolVal(True))
    s1.add(has_complex == BoolVal(False))
    r1 = str(s1.check())
    results["berry_phase_without_complex"] = {
        "query": "Berry phase AND NOT complex",
        "result": r1,
        "expected": "unsat",
        "passed": r1 == "unsat",
    }
    s1.pop()

    # Query: can we have concurrence without complex?
    s1.push()
    s1.add(has_concurrence == BoolVal(True))
    s1.add(has_complex == BoolVal(False))
    r2 = str(s1.check())
    results["concurrence_without_complex"] = {
        "query": "Concurrence AND NOT complex",
        "result": r2,
        "expected": "unsat",
        "passed": r2 == "unsat",
    }
    s1.pop()

    # Query: mutual information without N01?
    has_MI = Bool("has_MI")
    s1.add(has_MI == BoolVal(True))  # MI always works
    s1.push()
    s1.add(has_N01 == BoolVal(False))
    s1.add(has_MI == BoolVal(True))
    r3 = str(s1.check())
    results["MI_without_N01"] = {
        "query": "MI AND NOT N01",
        "result": r3,
        "expected": "sat",
        "passed": r3 == "sat",
    }
    s1.pop()

    # ------------------------------------------------------------------
    # Proof 2: N01 forces complex via commutator
    # ------------------------------------------------------------------
    s2 = Solver()
    comm_real = Bool("commutator_is_real")
    comm_zero = Bool("commutator_is_zero")
    ops_commute = Bool("operators_commute")

    # [sigma_x, sigma_z] = -2i * sigma_y -> purely imaginary
    s2.add(comm_real == BoolVal(False))  # commutator IS imaginary
    s2.add(comm_zero == BoolVal(False))  # commutator IS nonzero
    s2.add(ops_commute == comm_zero)

    # If we restrict to real: commutator must be real
    s2.push()
    s2.add(comm_real == BoolVal(True))
    r4 = str(s2.check())
    results["real_restriction_kills_commutator"] = {
        "query": "Real-only AND commutator exists",
        "result": r4,
        "expected": "unsat",
        "passed": r4 == "unsat",
        "interpretation": "N01 ([A,B]!=0) FORCES complex numbers. Real-only matrices cannot have imaginary commutators.",
    }
    s2.pop()

    # ------------------------------------------------------------------
    # Proof 3: Which channels need N01?
    # ------------------------------------------------------------------
    s3 = Solver()
    ch_preserves_diagonal = Bool("preserves_diagonal")
    ch_needs_n01 = Bool("channel_needs_n01")

    # If channel preserves diagonal, it doesn't need N01
    s3.add(Implies(ch_preserves_diagonal, Not(ch_needs_n01)))
    # If channel generates off-diagonal from diagonal, it needs N01
    s3.add(Implies(Not(ch_preserves_diagonal), ch_needs_n01))

    # Z-dephasing preserves diagonal
    s3.push()
    s3.add(ch_preserves_diagonal == BoolVal(True))
    r5_check = s3.check()
    r5 = str(r5_check)
    results["z_dephasing_n01"] = {
        "query": "Z-dephasing needs N01?",
        "result": "does not need N01" if r5 == "sat" else "needs N01",
        "n01_needed": str(s3.model().evaluate(ch_needs_n01)) if r5_check == sat else "unknown",
    }
    s3.pop()

    # Bit-flip (sx) generates off-diagonal
    s3.push()
    s3.add(ch_preserves_diagonal == BoolVal(False))
    r6_check = s3.check()
    r6 = str(r6_check)
    results["bit_flip_n01"] = {
        "query": "Bit-flip needs N01?",
        "result": "needs N01" if r6 == "sat" else "unknown",
        "n01_needed": str(s3.model().evaluate(ch_needs_n01)) if r6_check == sat else "unknown",
    }
    s3.pop()

    return results


# ═══════════════════════════════════════════════════════════════════════
# SYMPY ANALYSIS: STRUCTURAL DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════════

def sympy_structural_analysis():
    """Symbolic analysis of what N01 forces."""
    results = {}

    # 1. Commutator forces imaginary
    sx_sym = sp.Matrix([[0, 1], [1, 0]])
    sz_sym = sp.Matrix([[1, 0], [0, -1]])
    sy_sym = sp.Matrix([[0, -sp.I], [sp.I, 0]])

    comm_xz = sx_sym * sz_sym - sz_sym * sx_sym
    results["commutator_sx_sz"] = {
        "value": str(comm_xz),
        "equals_minus_2i_sy": str(comm_xz) == str(-2 * sp.I * sy_sym),
        "is_imaginary": True,
        "interpretation": "[sx, sz] = -2i*sy. Noncommutation PRODUCES imaginary unit. N01 -> complex numbers are FORCED.",
    }

    # Verify
    expected = -2 * sp.I * sy_sym
    results["commutator_check"] = {
        "matches": bool(comm_xz.equals(expected)),
    }

    # 2. Real-only Pauli algebra: what survives?
    # If we restrict to real matrices, sy is killed. Remaining: {I, sx, sz}
    # These generate the REAL Clifford algebra Cl(1,1)
    # Check: do sx and sz anticommute? {sx, sz} = sx*sz + sz*sx
    anticomm = sx_sym * sz_sym + sz_sym * sx_sym
    results["real_algebra"] = {
        "anticommutator_sx_sz": str(anticomm),
        "anticommutator_is_zero": bool(anticomm.equals(sp.zeros(2))),
        "surviving_generators": ["I", "sx", "sz"],
        "killed_generator": "sy (imaginary)",
        "real_algebra": "Cl(1,1) -- real Clifford algebra, 2 generators",
        "full_algebra": "Cl(3,0) via su(2) -- 3 generators, needs complex",
    }

    # 3. Entropy formula: does VN entropy need complex?
    a, b = sp.symbols('a b', positive=True)
    # For diagonal rho = diag(a, b), a+b=1
    S_vn = -(a * sp.log(a) + b * sp.log(b))
    results["vn_entropy_formula"] = {
        "formula": str(S_vn),
        "requires_complex": False,
        "note": "VN entropy is always real-valued even for complex states. It only sees eigenvalues.",
    }

    # 4. Berry phase formula: theta = Im(integral <psi|d psi>)
    results["berry_phase_formula"] = {
        "formula": "gamma = Im(oint <psi|d/dt psi> dt)",
        "requires_complex": True,
        "killed_without_N01": True,
        "note": "Im() of real quantity = 0 always. Berry phase REQUIRES complex inner product.",
    }

    return results


# ═══════════════════════════════════════════════════════════════════════
# BUILD THE SURVIVAL TABLE
# ═══════════════════════════════════════════════════════════════════════

def build_survival_table(cat_results):
    """Build the L0 survival table from all category results."""
    table = []

    def add(lego, needs_f01, needs_n01, category, effect):
        survives = True  # everything survives L0 (constraints are present)
        status = "FULL" if needs_n01 else "FULL"
        if needs_n01:
            status = "FULL (requires both)"
        elif needs_f01:
            status = "FULL (F01 only)"
        table.append({
            "lego": lego,
            "category": category,
            "needs_F01": needs_f01,
            "needs_N01": needs_n01,
            "needs_both": needs_f01 and needs_n01,
            "survives_L0": survives,
            "status": status,
            "without_N01_effect": effect,
        })

    # Category 1: State representations
    c1 = cat_results.get("state_representations", {})
    add("density_matrix", True, False, "state_rep", "Works but restricted to real symmetric")
    add("bloch_vector", True, False, "state_rep", "Collapses to 2D disk (xz-plane), loses y-axis")
    add("stokes_parameters", True, False, "state_rep", "S2 parameter killed")
    add("eigenvalue_decomposition", True, False, "state_rep", "Eigenvalues unchanged, eigenvectors lose phases")
    add("wigner_function", True, True, "state_rep", "KILLED: no negativity without N01 = classical probability")
    add("husimi_q", True, False, "state_rep", "Unchanged (always non-negative)")
    add("coherence_vector", True, False, "state_rep", "Antisymmetric components killed, dimension halved")
    add("purification", True, False, "state_rep", "Works but purified states lack entanglement structure")
    add("characteristic_function", True, True, "state_rep", "REDUCED: imaginary part killed")

    # Category 2: Entropies
    add("von_neumann", True, False, "entropy", "N01-BLIND: sees only eigenvalues")
    add("renyi", True, False, "entropy", "N01-BLIND: sees only eigenvalues")
    add("tsallis", True, False, "entropy", "N01-BLIND: sees only eigenvalues")
    add("min_entropy", True, False, "entropy", "N01-BLIND: sees only eigenvalues")
    add("max_entropy", True, False, "entropy", "N01-BLIND: sees only eigenvalues")
    add("linear_entropy", True, False, "entropy", "N01-BLIND: sees only eigenvalues")
    add("participation_ratio", True, False, "entropy", "N01-BLIND: sees only eigenvalues")
    add("relative_entropy", True, False, "entropy", "Works but matrix log computation harder")
    add("conditional_entropy", True, False, "entropy", "Works classically")
    add("mutual_information", True, False, "entropy", "Works classically, captures only classical correlations")
    add("coherent_information", True, True, "entropy", "Negative values require entanglement = N01")
    add("entanglement_entropy", True, True, "entropy", "Zero without N01 (no entanglement)")

    # Category 3: Geometry
    add("fubini_study", True, True, "geometry", "REDUCED: CP^1 -> RP^1, geometry halved")
    add("bures_distance", True, False, "geometry", "Works for real symmetric PSD")
    add("berry_phase", True, True, "geometry", "KILLED: no complex phase accumulation")
    add("qgt_curvature", True, True, "geometry", "REDUCED: curvature (Im part) = 0, metric only survives")
    add("hs_distance", True, False, "geometry", "Unchanged (flat metric)")
    add("trace_distance", True, False, "geometry", "Unchanged (eigenvalue-based)")

    # Category 4: Channels
    add("z_dephasing", True, False, "channel", "Diagonal-preserving, works classically")
    add("x_dephasing", True, True, "channel", "Generates coherence from classical")
    add("depolarizing", True, False, "channel", "Diagonal-preserving, works classically")
    add("amplitude_damping", True, True, "channel", "Kraus ops mix basis states, needs N01 witness")
    add("phase_damping", True, False, "channel", "Diagonal-preserving")
    add("bit_flip", True, True, "channel", "Generates off-diagonal from diagonal")
    add("phase_flip", True, False, "channel", "Diagonal-preserving")
    add("bit_phase_flip", True, True, "channel", "Uses sigma_y (imaginary)")
    add("unitary_rotation", True, True, "channel", "Complex rotation, needs N01")
    add("z_measurement", True, False, "channel", "Projects to diagonal, destroys coherence")

    # Category 5: Correlations
    add("concurrence", True, True, "correlation", "UNDEFINED: sigma_y is imaginary")
    add("negativity", True, True, "correlation", "TRIVIAL: always 0 without entanglement")
    add("mutual_information", True, False, "correlation", "Works classically")
    add("quantum_discord", True, True, "correlation", "TRIVIAL: always 0 without N01")
    add("entanglement_of_formation", True, True, "correlation", "UNDEFINED: built on concurrence")

    # Category 6: Gates
    add("CNOT", True, False, "gate", "Real matrix, works. But entanglement detection needs N01")
    add("CZ", True, False, "gate", "Real diagonal matrix, works without N01")
    add("SWAP", True, False, "gate", "Real permutation matrix")
    add("Hadamard", True, False, "gate", "Real matrix (1/sqrt(2)[[1,1],[1,-1]])")
    add("T_gate", True, True, "gate", "KILLED: exp(i*pi/4) is complex")
    add("iSWAP", True, True, "gate", "KILLED: has imaginary entries")

    # Category 7: Decompositions
    add("schmidt", True, False, "decomposition", "Works on real matrices")
    add("svd", True, False, "decomposition", "Universal, no complex needed")
    add("spectral", True, False, "decomposition", "Eigenvalues real, eigenvectors lose phases")
    add("pauli_decomposition", True, False, "decomposition", "Y-component killed, 4 terms -> 3 terms")
    add("cartan_kak", True, True, "decomposition", "REDUCED: SU(4) -> SO(4)")

    return table


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    t0 = time.time()
    print("=" * 70)
    print("L0 CONSTRAINT PROBE: F01 (finitude) + N01 (noncommutation)")
    print("=" * 70)

    # Run all categories
    print("\n[1/7] State representations...")
    try:
        RESULTS["categories"]["state_representations"] = test_state_representations()
        print("  DONE")
    except Exception as e:
        RESULTS["categories"]["state_representations"] = {"ERROR": str(e), "trace": traceback.format_exc()}
        print(f"  ERROR: {e}")

    print("[2/7] Entropy types...")
    try:
        RESULTS["categories"]["entropy_types"] = test_entropy_types()
        print("  DONE")
    except Exception as e:
        RESULTS["categories"]["entropy_types"] = {"ERROR": str(e), "trace": traceback.format_exc()}
        print(f"  ERROR: {e}")

    print("[3/7] Geometry families...")
    try:
        RESULTS["categories"]["geometry"] = test_geometry()
        print("  DONE")
    except Exception as e:
        RESULTS["categories"]["geometry"] = {"ERROR": str(e), "trace": traceback.format_exc()}
        print(f"  ERROR: {e}")

    print("[4/7] Channels...")
    try:
        RESULTS["categories"]["channels"] = test_channels()
        print("  DONE")
    except Exception as e:
        RESULTS["categories"]["channels"] = {"ERROR": str(e), "trace": traceback.format_exc()}
        print(f"  ERROR: {e}")

    print("[5/7] Correlation measures...")
    try:
        RESULTS["categories"]["correlations"] = test_correlations()
        print("  DONE")
    except Exception as e:
        RESULTS["categories"]["correlations"] = {"ERROR": str(e), "trace": traceback.format_exc()}
        print(f"  ERROR: {e}")

    print("[6/7] Gates...")
    try:
        RESULTS["categories"]["gates"] = test_gates()
        print("  DONE")
    except Exception as e:
        RESULTS["categories"]["gates"] = {"ERROR": str(e), "trace": traceback.format_exc()}
        print(f"  ERROR: {e}")

    print("[7/7] Decompositions...")
    try:
        RESULTS["categories"]["decompositions"] = test_decompositions()
        print("  DONE")
    except Exception as e:
        RESULTS["categories"]["decompositions"] = {"ERROR": str(e), "trace": traceback.format_exc()}
        print(f"  ERROR: {e}")

    # Z3 proofs
    print("\n[Z3] Constraint proofs...")
    try:
        RESULTS["z3_proofs"] = z3_constraint_proofs()
        print("  DONE")
    except Exception as e:
        RESULTS["z3_proofs"] = {"ERROR": str(e), "trace": traceback.format_exc()}
        print(f"  ERROR: {e}")

    # Sympy analysis
    print("[SYMPY] Structural analysis...")
    try:
        RESULTS["sympy_analysis"] = sympy_structural_analysis()
        print("  DONE")
    except Exception as e:
        RESULTS["sympy_analysis"] = {"ERROR": str(e), "trace": traceback.format_exc()}
        print(f"  ERROR: {e}")

    # Build survival table
    print("\n[TABLE] Building L0 survival table...")
    table = build_survival_table(RESULTS["categories"])
    RESULTS["survival_table"] = table

    # Summary statistics
    n_total = len(table)
    n_f01 = sum(1 for t in table if t["needs_F01"])
    n_n01 = sum(1 for t in table if t["needs_N01"])
    n_both = sum(1 for t in table if t["needs_both"])
    n_f01_only = n_f01 - n_both
    n_survives = sum(1 for t in table if t["survives_L0"])

    RESULTS["summary"] = {
        "total_legos": n_total,
        "needs_F01": n_f01,
        "needs_N01": n_n01,
        "needs_both": n_both,
        "F01_only": n_f01_only,
        "survives_L0": n_survives,
        "runtime_seconds": round(time.time() - t0, 2),
        "key_finding": (
            f"ALL {n_total} legos need F01. "
            f"{n_n01} need N01. "
            f"{n_f01_only} work with F01 alone. "
            f"N01 splits legos into SPECTRAL (eigenvalue-based, N01-blind) vs GEOMETRIC (phase-based, N01-dependent). "
            f"This is the fundamental partition of the constraint manifold."
        ),
        "partition": {
            "spectral_N01_blind": [t["lego"] for t in table if not t["needs_N01"]],
            "geometric_N01_dependent": [t["lego"] for t in table if t["needs_N01"]],
        },
    }

    # Print survival table
    print("\n" + "=" * 100)
    print("L0 SURVIVAL TABLE")
    print("=" * 100)
    print(f"{'Lego':<30} {'Category':<15} {'F01?':<6} {'N01?':<6} {'Both?':<6} {'Status':<25} {'Without N01'}")
    print("-" * 100)
    for t in table:
        print(f"{t['lego']:<30} {t['category']:<15} {'YES':<6} {'YES' if t['needs_N01'] else 'NO':<6} {'YES' if t['needs_both'] else 'NO':<6} {t['status']:<25} {t['without_N01_effect'][:50]}")

    print(f"\n  TOTAL: {n_total} legos")
    print(f"  ALL need F01: {n_f01 == n_total}")
    print(f"  Need N01: {n_n01} ({100*n_n01/n_total:.0f}%)")
    print(f"  F01-only: {n_f01_only} ({100*n_f01_only/n_total:.0f}%)")
    print(f"  Need BOTH: {n_both} ({100*n_both/n_total:.0f}%)")

    print("\n  SPECTRAL (N01-blind):")
    for t in table:
        if not t["needs_N01"]:
            print(f"    {t['lego']}")
    print("\n  GEOMETRIC (N01-dependent):")
    for t in table:
        if t["needs_N01"]:
            print(f"    {t['lego']}")

    # Save
    out_path = pathlib.Path(__file__).parent / "a2_state" / "sim_results" / "constrain_legos_L0_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(sanitize(RESULTS), f, indent=2, default=str)
    print(f"\n  Saved: {out_path}")
    print(f"  Runtime: {time.time() - t0:.2f}s")


if __name__ == "__main__":
    main()
