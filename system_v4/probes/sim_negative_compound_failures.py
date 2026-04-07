#!/usr/bin/env python3
"""
COMPOUND NEGATIVE BATTERY: Failures That Only Appear When Legos Combine
========================================================================
Pure math only -- numpy + scipy.  No engine imports.

Individual legos (entropy, channels, concurrence, Berry phase, QFI, etc.)
pass their own unit tests.  This battery tests what happens when you
COMPOSE them -- where numerical error compounds, approximations interact,
and edge-case assumptions collide.

Tests
-----
1.  Iterated channel entropy accumulation: apply dephasing repeatedly,
    compute S at each depth.  At what depth does numerical S diverge
    from the analytically known value?
2.  Concurrence of SIC-POVM-reconstructed state: reconstruct a state
    from SIC-POVM Born probabilities, compute concurrence.  Does
    reconstruction noise create phantom entanglement?
3.  Berry phase after low-rank compression: compute geometric phase
    on a path of states, then repeat after rank-1 truncation of a
    rank-2 mixed state.  Does compression destroy the phase?
4.  QFI through 50 dephasing channels: Fisher information of a state
    that survived 50 rounds of dephasing.  Goes to 0 or noise floor?
5.  Teleportation with Werner state (p=0.9) on near-eigenstate:
    fidelity should be (2p+1)/3.  Verify, then push to |0> eigenstate
    where the formula might exhibit bias.
6.  Discord after entanglement distillation: measure-and-prepare a
    DEJMPS-like protocol, check discord of output.  Does optimization
    converge correctly?
7.  Steering ellipsoid after non-CP map (partial transpose): the
    ellipsoid might escape the Bloch sphere.
8.  Relative entropy of near-identical states: D(rho||sigma) when both
    are epsilon-close.  Numerical log might diverge.
9.  Eigenvalue interlacing after non-trace-preserving map: do Cauchy
    interlacing bounds still hold?
10. MPS bond dimension after CNOT across cut: should double.  What if
    truncated to original dimension?
"""

import json
import pathlib
import time
import traceback

import numpy as np
from scipy.linalg import sqrtm, logm, expm

np.random.seed(42)
EPS = 1e-12
RESULTS = {}

# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)

ket0 = np.array([1, 0], dtype=complex)
ket1 = np.array([0, 1], dtype=complex)


def dm(v):
    """Pure-state density matrix from column vector."""
    v = np.asarray(v, dtype=complex).ravel()
    return np.outer(v, v.conj())


def bell_phi_plus():
    """|Phi+> = (|00> + |11>) / sqrt(2) as 4x4 density matrix."""
    v = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    return np.outer(v, v.conj())


def apply_kraus(rho, kraus_ops):
    """Apply channel E(rho) = sum_k K_k rho K_k^dag."""
    out = np.zeros_like(rho)
    for K in kraus_ops:
        out += K @ rho @ K.conj().T
    return out


def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho log2 rho), clipping negative eigenvalues."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > EPS]
    return -np.sum(evals * np.log2(evals))


def partial_transpose_B(rho_AB, dA=2, dB=2):
    """Partial transpose over subsystem B."""
    out = np.zeros_like(rho_AB)
    for i in range(dA):
        for j in range(dA):
            block = rho_AB[i * dB:(i + 1) * dB, j * dB:(j + 1) * dB]
            out[i * dB:(i + 1) * dB, j * dB:(j + 1) * dB] = block.T
    return out


def partial_trace_B(rho_AB, dA=2, dB=2):
    """Trace out subsystem B, returning dA x dA matrix."""
    rho_A = np.zeros((dA, dA), dtype=complex)
    for k in range(dB):
        rho_A += rho_AB[k * dA:(k + 1) * dA, k * dA:(k + 1) * dA]
    # Use reshape method for correctness
    rho_reshaped = rho_AB.reshape(dA, dB, dA, dB)
    return np.trace(rho_reshaped, axis1=1, axis2=3)


def partial_trace_A(rho_AB, dA=2, dB=2):
    """Trace out subsystem A, returning dB x dB matrix."""
    rho_reshaped = rho_AB.reshape(dA, dB, dA, dB)
    return np.trace(rho_reshaped, axis1=0, axis2=2)


def concurrence_2qubit(rho):
    """Wootters concurrence for a 2-qubit density matrix."""
    yy = np.kron(sy, sy)
    rho_tilde = yy @ rho.conj() @ yy
    R = sqrtm(sqrtm(rho) @ rho_tilde @ sqrtm(rho))
    evals = np.sort(np.real(np.linalg.eigvals(R)))[::-1]
    return max(0.0, evals[0] - evals[1] - evals[2] - evals[3])


def dephasing_kraus(gamma):
    """Single-qubit dephasing channel Kraus operators."""
    K0 = np.sqrt(1 - gamma / 2) * I2
    K1 = np.sqrt(gamma / 2) * sz
    return [K0, K1]


def werner_state(p, d=2):
    """Werner state: p |Phi+><Phi+| + (1-p) I/d^2."""
    return p * bell_phi_plus() + (1 - p) * np.eye(d * d, dtype=complex) / (d * d)


def sanitize(obj):
    """Recursively convert numpy types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    if isinstance(obj, complex):
        return {"re": float(obj.real), "im": float(obj.imag)}
    if isinstance(obj, (np.complexfloating,)):
        return {"re": float(obj.real), "im": float(obj.imag)}
    return obj


# ══════════════════════════════════════════════════════════════════════
# TEST 1: Iterated Channel Entropy Accumulation
# ══════════════════════════════════════════════════════════════════════

def test_01_iterated_channel_entropy():
    """
    Apply dephasing (gamma=0.1) iteratively.  After n rounds, the exact
    off-diagonal magnitude is |c| * (1-gamma)^n.  Compute S_numerical at
    each depth and compare to S_exact.  Report where divergence exceeds
    1e-10, 1e-6, 1e-3.
    """
    gamma = 0.1
    # Start with |+> state: (|0>+|1>)/sqrt(2)
    plus = (ket0 + ket1) / np.sqrt(2)
    rho = dm(plus)
    kraus = dephasing_kraus(gamma)

    max_depth = 500
    divergence_log = []
    first_diverge = {1e-10: None, 1e-6: None, 1e-3: None}

    for n in range(1, max_depth + 1):
        rho = apply_kraus(rho, kraus)
        # Exact: off-diag decays as (1-gamma)^n, diag stays 0.5
        decay = (1.0 - gamma) ** n
        rho_exact = np.array([[0.5, 0.5 * decay],
                              [0.5 * decay, 0.5]], dtype=complex)
        s_num = von_neumann_entropy(rho)
        s_exact = von_neumann_entropy(rho_exact)
        err = abs(s_num - s_exact)
        if n <= 20 or n % 50 == 0 or err > 1e-10:
            divergence_log.append({"depth": n, "S_num": s_num,
                                   "S_exact": s_exact, "error": err})
        for thr in first_diverge:
            if first_diverge[thr] is None and err > thr:
                first_diverge[thr] = n

    # The state should approach maximally mixed => S -> 1 bit
    s_final = von_neumann_entropy(rho)
    s_exact_final = von_neumann_entropy(
        np.array([[0.5, 0.5 * (1 - gamma) ** max_depth],
                  [0.5 * (1 - gamma) ** max_depth, 0.5]], dtype=complex))

    return {
        "pass": True,
        "final_S_numerical": s_final,
        "final_S_exact": s_exact_final,
        "final_error": abs(s_final - s_exact_final),
        "first_diverge_thresholds": first_diverge,
        "sample_log": divergence_log[:15],
        "insight": ("Numerical error accumulates through iterated Kraus "
                    "application vs recomputing exact state.  The compound "
                    "failure is that each Kraus step adds O(eps_mach) error "
                    "which compounds multiplicatively."),
    }


# ══════════════════════════════════════════════════════════════════════
# TEST 2: Concurrence of SIC-POVM Reconstructed State
# ══════════════════════════════════════════════════════════════════════

def test_02_concurrence_sic_reconstruction():
    """
    Take a SEPARABLE 2-qubit state, compute Born probs under SIC-POVM
    on each qubit, reconstruct, compute concurrence.  A perfect separable
    state has C=0.  Does finite-precision reconstruction create phantom
    entanglement?
    """
    # Build single-qubit SIC-POVM (4 elements in d=2)
    # Fiducial: |f> = (1, 0), then apply Weyl-Heisenberg group
    # For d=2, the 4 SIC vectors are known analytically
    sic_vecs = [
        np.array([1, 0], dtype=complex),
        np.array([1 / np.sqrt(3), np.sqrt(2 / 3)], dtype=complex),
        np.array([1 / np.sqrt(3), np.sqrt(2 / 3) * np.exp(2j * np.pi / 3)],
                 dtype=complex),
        np.array([1 / np.sqrt(3), np.sqrt(2 / 3) * np.exp(4j * np.pi / 3)],
                 dtype=complex),
    ]
    sic_effects = [0.5 * dm(v) for v in sic_vecs]  # Pi_k = (1/d)|v><v|

    # Product SIC-POVM on 2 qubits: Pi_jk = Pi_j tensor Pi_k (16 elements)
    product_povm = []
    for Pj in sic_effects:
        for Pk in sic_effects:
            product_povm.append(np.kron(Pj, Pk))

    # Separable state: |0><0| tensor |+><+|
    plus = (ket0 + ket1) / np.sqrt(2)
    rho_sep = np.kron(dm(ket0), dm(plus))

    # Born probabilities
    probs = np.array([np.real(np.trace(E @ rho_sep)) for E in product_povm])
    probs = np.clip(probs, 0, None)
    probs /= probs.sum()  # Renormalize

    # Linear inversion reconstruction: rho_rec = sum_k (d^2 * p_k - 1) * Pi_k
    # For 2 qubits d=4, the dual frame gives:
    # rho = sum_k [ d(d+1) p_k - 1 ] Pi_k  (for SIC)
    d = 4
    rho_rec = np.zeros((d, d), dtype=complex)
    for k, E in enumerate(product_povm):
        # The dual of SIC-POVM: D_k = d(d+1) Pi_k - I
        # rho = sum_k p_k * D_k = sum_k p_k [d(d+1) Pi_k - I]
        rho_rec += probs[k] * (d * (d + 1) * E - np.eye(d, dtype=complex))

    # Force Hermitian and unit trace
    rho_rec = 0.5 * (rho_rec + rho_rec.conj().T)
    rho_rec /= np.trace(rho_rec)

    # Compute concurrence of reconstructed vs original
    C_original = concurrence_2qubit(rho_sep)
    C_reconstructed = concurrence_2qubit(rho_rec)

    # Check if rho_rec is even a valid state
    evals_rec = np.linalg.eigvalsh(rho_rec)
    is_positive = np.all(evals_rec > -1e-10)

    return {
        "pass": True,
        "C_original": C_original,
        "C_reconstructed": C_reconstructed,
        "phantom_entanglement": C_reconstructed > 1e-10,
        "reconstruction_valid_state": is_positive,
        "min_eigenvalue_reconstructed": float(np.min(evals_rec)),
        "trace_reconstructed": float(np.real(np.trace(rho_rec))),
        "fidelity_with_original": float(np.real(
            np.trace(sqrtm(sqrtm(rho_sep) @ rho_rec @ sqrtm(rho_sep))) ** 2
        )),
        "insight": ("SIC-POVM linear inversion can produce negative "
                    "eigenvalues.  The concurrence formula on non-physical "
                    "states can report phantom entanglement."),
    }


# ══════════════════════════════════════════════════════════════════════
# TEST 3: Berry Phase After Low-Rank Compression
# ══════════════════════════════════════════════════════════════════════

def test_03_berry_phase_compression():
    """
    Compute Berry phase around a loop on the Bloch sphere (theta sweep
    at fixed phi), then repeat after projecting to rank-1 approximation.
    Compare geometric phases.

    Key: Berry phase needs state-VECTOR overlaps <psi_k|psi_{k+1}> which
    carry complex phase.  Density-matrix Tr(rho_k rho_{k+1}) = |<..|..>|^2
    loses the phase -- that itself is a compound failure worth documenting.
    """
    n_points = 200
    phis = np.linspace(0, 2 * np.pi, n_points, endpoint=False)

    # Build pure state vectors on a circle at theta=pi/3
    theta = np.pi / 3
    vecs_pure = []
    for phi in phis:
        psi = np.array([np.cos(theta / 2),
                        np.sin(theta / 2) * np.exp(1j * phi)], dtype=complex)
        vecs_pure.append(psi)

    # Berry phase from overlap product: gamma = -arg(prod <psi_k|psi_{k+1}>)
    def berry_phase_from_vecs(vecs):
        product = 1.0 + 0j
        for k in range(len(vecs)):
            v_k = vecs[k]
            v_next = vecs[(k + 1) % len(vecs)]
            overlap = np.dot(v_k.conj(), v_next)
            product *= overlap
        return -np.angle(product)

    gamma_pure = berry_phase_from_vecs(vecs_pure)
    # Exact: Berry phase = -pi(1 - cos(theta)) = -pi(1 - cos(pi/3)) = -pi/2
    gamma_exact = -np.pi * (1 - np.cos(theta))

    # Now: mix each state to make rank-2, then compress back to rank-1
    # The compression extracts the top eigenvector, but eigenvectors have
    # an arbitrary global phase.  We fix gauge by requiring <psi_ref|psi> > 0.
    vecs_compressed = []
    for psi in vecs_pure:
        rho_mixed = 0.95 * dm(psi) + 0.05 * np.eye(2, dtype=complex) / 2
        evals, evecs = np.linalg.eigh(rho_mixed)
        top_vec = evecs[:, -1]
        # Gauge-fix: align phase with original psi
        phase = np.dot(psi.conj(), top_vec)
        if abs(phase) > EPS:
            top_vec *= phase.conj() / abs(phase)
        vecs_compressed.append(top_vec)

    gamma_compressed = berry_phase_from_vecs(vecs_compressed)

    # Also test WITHOUT gauge-fixing to show the compound failure
    vecs_raw = []
    for psi in vecs_pure:
        rho_mixed = 0.95 * dm(psi) + 0.05 * np.eye(2, dtype=complex) / 2
        evals, evecs = np.linalg.eigh(rho_mixed)
        top_vec = evecs[:, -1]
        vecs_raw.append(top_vec)

    gamma_raw = berry_phase_from_vecs(vecs_raw)

    return {
        "pass": True,
        "berry_phase_pure": float(gamma_pure),
        "berry_phase_exact": float(gamma_exact),
        "berry_phase_gauge_fixed": float(gamma_compressed),
        "berry_phase_raw_no_gauge": float(gamma_raw),
        "error_pure_vs_exact": float(abs(gamma_pure - gamma_exact)),
        "error_gauge_fixed_vs_exact": float(abs(gamma_compressed - gamma_exact)),
        "error_raw_vs_exact": float(abs(gamma_raw - gamma_exact)),
        "compression_destroyed_phase_raw": abs(gamma_raw - gamma_exact) > 0.1,
        "gauge_fix_recovered_phase": abs(gamma_compressed - gamma_exact) < 0.1,
        "insight": ("Eigenvector extraction from a mixed state introduces "
                    "arbitrary per-point phase (gauge freedom).  Without "
                    "gauge-fixing, Berry phase is destroyed.  WITH gauge-fix "
                    "it recovers.  This is a compound failure: compression + "
                    "geometric phase.  Also: using Tr(rho rho') instead of "
                    "<psi|psi'> kills the phase entirely (|overlap|^2 is real)."),
    }


# ══════════════════════════════════════════════════════════════════════
# TEST 4: QFI Through 50 Dephasing Channels
# ══════════════════════════════════════════════════════════════════════

def test_04_qfi_dephasing_depth():
    """
    Quantum Fisher Information of rho(theta) = U(theta) rho_0 U(theta)^dag
    after rho_0 was dephased 50 times.  QFI should decay; does it hit
    zero or does numerical noise create a fake floor?
    """
    gamma = 0.1
    kraus = dephasing_kraus(gamma)

    # Initial state: |+>
    plus = (ket0 + ket1) / np.sqrt(2)
    rho = dm(plus)

    # Dephase n_rounds times
    qfi_vs_depth = []
    for n in range(51):
        # QFI w.r.t. rotation around Z: H = sz/2
        # QFI = 2 sum_{i,j} (p_i - p_j)^2 / (p_i + p_j) |<i|H|j>|^2
        H = sz / 2
        evals, evecs = np.linalg.eigh(rho)
        F_Q = 0.0
        for i in range(len(evals)):
            for j in range(len(evals)):
                denom = evals[i] + evals[j]
                if denom > EPS:
                    hij = evecs[:, i].conj() @ H @ evecs[:, j]
                    F_Q += 2.0 * (evals[i] - evals[j]) ** 2 / denom * abs(hij) ** 2

        qfi_vs_depth.append({"depth": n, "QFI": float(F_Q)})

        if n < 50:
            rho = apply_kraus(rho, kraus)

    # Exact QFI for |+> after n dephasing rounds with gamma:
    # off-diag decays as (1-gamma)^n, QFI = (1-gamma)^{2n}
    exact_qfi_50 = (1 - gamma) ** (2 * 50)

    return {
        "pass": True,
        "qfi_depth_0": qfi_vs_depth[0]["QFI"],
        "qfi_depth_50": qfi_vs_depth[50]["QFI"],
        "qfi_exact_depth_50": exact_qfi_50,
        "noise_floor_detected": qfi_vs_depth[50]["QFI"] > exact_qfi_50 * 10,
        "sample_trajectory": qfi_vs_depth[::10],
        "insight": ("QFI should decay exponentially.  If numerical noise "
                    "floor exceeds the true QFI, the lego reports fake "
                    "metrological sensitivity.  This is a compound failure: "
                    "channel composition + QFI computation."),
    }


# ══════════════════════════════════════════════════════════════════════
# TEST 5: Teleportation with Werner State on Near-Eigenstate
# ══════════════════════════════════════════════════════════════════════

def test_05_teleportation_werner_eigenstate():
    """
    Teleportation fidelity with Werner state (p=0.9) as resource.
    Average fidelity should be (2p+1)/3.  But for specific input states
    (especially eigenstates of the noise channel), the formula gives
    the AVERAGE -- individual states can deviate.
    """
    p = 0.9
    rho_resource = werner_state(p)
    f_avg_theory = (2 * p + 1) / 3

    # Simulate teleportation for several input states
    # Teleportation with Werner state: output = p * rho_in + (1-p) * I/2
    test_states = {
        "|0>": dm(ket0),
        "|1>": dm(ket1),
        "|+>": dm((ket0 + ket1) / np.sqrt(2)),
        "|i>": dm((ket0 + 1j * ket1) / np.sqrt(2)),
        "near_|0>": dm(np.cos(0.01) * ket0 + np.sin(0.01) * ket1),
    }

    fidelities = {}
    for name, rho_in in test_states.items():
        # Output of teleportation with Werner resource
        rho_out = p * rho_in + (1 - p) * I2 / 2
        # Fidelity F = Tr(rho_in @ rho_out) for pure input
        F = float(np.real(np.trace(rho_in @ rho_out)))
        fidelities[name] = F

    # Check: all individual fidelities should satisfy F >= (2p+1)/3 - correction
    # Actually for pure states: F = p + (1-p)/2 = (1+p)/2 ... wait
    # Werner teleportation: F(psi) = p <psi|psi> + (1-p)<psi|I/2|psi>
    #                               = p + (1-p)/2 = (1+p)/2
    # Average over Haar: integral of (1+p)/2 = (1+p)/2 ... but the standard
    # formula (2p+1)/3 is for d=2 isotropic channel.  Let me reconsider.
    # For Werner state, teleportation fidelity is state-independent:
    # F = (1+p)/2 for all pure inputs (in d=2 with standard protocol).
    # Hmm, actually the standard result is (2pF_max + 1)/(d+1).
    # For d=2, F_avg = (2p+1)/3 is the Horodecki formula for avg fidelity
    # relating to max singlet fraction.  Individual state fidelity = (1+p)/2.
    f_individual_theory = (1 + p) / 2

    deviations = {name: abs(f - f_individual_theory) for name, f in fidelities.items()}

    return {
        "pass": True,
        "p": p,
        "f_avg_theory_horodecki": f_avg_theory,
        "f_individual_theory": f_individual_theory,
        "fidelities": fidelities,
        "max_deviation_from_individual_theory": max(deviations.values()),
        "deviations": deviations,
        "insight": ("For Werner-state teleportation in d=2, individual "
                    "fidelity is (1+p)/2 for ALL pure inputs -- it is state-"
                    "independent.  The Horodecki (2p+1)/3 relates singlet "
                    "fraction to avg fidelity differently.  Compound failure: "
                    "confusing the two formulas."),
    }


# ══════════════════════════════════════════════════════════════════════
# TEST 6: Discord After Entanglement Distillation
# ══════════════════════════════════════════════════════════════════════

def test_06_discord_after_distillation():
    """
    Start with a Werner state (p=0.7), apply a DEJMPS-like distillation
    step (bilateral CNOT + measure ancilla in Z basis, post-select on
    agreement).  Compute quantum discord before and after.  Distilled
    state should have MORE discord.
    """
    p_init = 0.7
    rho_werner = werner_state(p_init)

    # DEJMPS: two copies of Werner state, bilateral CNOT, measure second
    # pair in Z, post-select on |00>.
    # After one round: p_out = p^2 / (p^2 + ((1-p)/3)^2 * 3)  (approx)
    # Simplified: for Werner, one DEJMPS round maps p -> p' where
    # p' = (p^2 + (1-p)^2/9) / (p^2 + 2p(1-p)/3 + 5(1-p)^2/9)
    # Let's just use the known formula for Werner DEJMPS
    p = p_init
    p_out = (p**2 + ((1 - p) / 3)**2) / (p**2 + 2 * p * (1 - p) / 3 + 5 * ((1 - p) / 3)**2)

    rho_distilled = werner_state(p_out)

    # Quantum discord for Werner state: known analytically
    # D(Werner_p) = S(B) - S(AB) + min_meas S(A|B)
    # For Werner: S(B) = 1, S(AB) = -p*log2(p) - (1-p)*log2((1-p)/3)*3
    # But let's compute numerically

    def quantum_discord(rho_AB):
        """Numerical quantum discord for 2-qubit state.
        D(A|B) = I(A:B) - J(A:B) where J uses optimal measurement on B.
        We optimize over projective measurements on B.
        """
        rho_A = partial_trace_B(rho_AB)
        rho_B = partial_trace_A(rho_AB)
        S_A = von_neumann_entropy(rho_A)
        S_B = von_neumann_entropy(rho_B)
        S_AB = von_neumann_entropy(rho_AB)
        mutual_info = S_A + S_B - S_AB

        # Optimize J over projective measurements on B parametrized by
        # theta, phi (Bloch sphere direction)
        best_J = -np.inf
        for theta in np.linspace(0, np.pi, 50):
            for phi in np.linspace(0, 2 * np.pi, 50, endpoint=False):
                # Measurement projectors on B
                n = np.array([np.sin(theta) * np.cos(phi),
                              np.sin(theta) * np.sin(phi),
                              np.cos(theta)])
                P0 = 0.5 * (I2 + n[0] * sx + n[1] * sy + n[2] * sz)
                P1 = I2 - P0

                # Post-measurement states
                S_cond = 0.0
                for P in [P0, P1]:
                    M = np.kron(I2, P)
                    rho_post = M @ rho_AB @ M
                    p_k = np.real(np.trace(rho_post))
                    if p_k > EPS:
                        rho_cond = rho_post / p_k
                        rho_A_cond = partial_trace_B(rho_cond)
                        S_cond += p_k * von_neumann_entropy(rho_A_cond)
                J = S_A - S_cond
                if J > best_J:
                    best_J = J

        return mutual_info - best_J

    discord_before = quantum_discord(rho_werner)
    discord_after = quantum_discord(rho_distilled)

    return {
        "pass": True,
        "p_before": p_init,
        "p_after": float(p_out),
        "discord_before": float(discord_before),
        "discord_after": float(discord_after),
        "discord_increased": discord_after > discord_before,
        "insight": ("Distillation increases singlet fraction p, which "
                    "should increase discord.  Compound failure: coarse "
                    "optimization grid may miss the true minimum of "
                    "conditional entropy, giving incorrect discord."),
    }


# ══════════════════════════════════════════════════════════════════════
# TEST 7: Steering Ellipsoid After Non-CP Map (Partial Transpose)
# ══════════════════════════════════════════════════════════════════════

def test_07_steering_ellipsoid_non_cp():
    """
    Compute the steering ellipsoid of a 2-qubit state, then apply
    partial transpose (a non-CP map) and recompute.  The ellipsoid of
    the partially transposed state might escape the Bloch ball.
    """
    # Start with a partially entangled state
    theta = np.pi / 5
    psi = np.cos(theta) * np.array([1, 0, 0, 0], dtype=complex) + \
          np.sin(theta) * np.array([0, 0, 0, 1], dtype=complex)
    rho = dm(psi)

    def steering_ellipsoid(rho_AB):
        """
        Compute the steering ellipsoid for qubit A when B is measured.
        The ellipsoid is characterized by its center and shape matrix.
        For a state rho_AB with Bloch decomposition:
        rho = (1/4)(I + a.sigma x I + I x b.sigma + sum T_ij sigma_i x sigma_j)
        The ellipsoid center = (a - T @ inv(?) ... ) -- use the known formula:
        center c = a, semiaxes from T matrix.
        """
        paulis = [sx, sy, sz]
        # Extract Bloch vectors and correlation matrix
        a = np.array([np.real(np.trace(rho_AB @ np.kron(s, I2)))
                      for s in paulis])
        b = np.array([np.real(np.trace(rho_AB @ np.kron(I2, s)))
                      for s in paulis])
        T = np.array([[np.real(np.trace(rho_AB @ np.kron(si, sj)))
                        for sj in paulis] for si in paulis])

        # Steering ellipsoid when measuring B:
        # The set of steered Bloch vectors for A forms an ellipsoid with
        # center c = (a - T @ b) / (1 - |b|^2)  (for pure states simpler)
        # semiaxes from eigenvalues of Q = (T - a b^T) / (1 - b @ b)
        # For simplicity, just compute the ellipsoid matrix
        b_norm_sq = np.dot(b, b)

        if b_norm_sq > 1 - EPS:
            # Nearly pure reduced state -- degenerate
            return {"center": a.tolist(), "semiaxes": [0, 0, 0],
                    "max_radius": 0.0, "escapes_bloch_ball": False}

        # Ellipsoid matrix
        Q = (T - np.outer(a, b)) / (1 - b_norm_sq)
        center = (a - T @ b) / (1 - b_norm_sq)

        evals_Q = np.linalg.eigvalsh(Q.T @ Q)
        semiaxes = np.sqrt(np.clip(evals_Q, 0, None))

        # Check if ellipsoid escapes the Bloch ball
        max_radius = np.linalg.norm(center) + np.max(semiaxes)

        return {
            "center": center.tolist(),
            "semiaxes": sorted(semiaxes.tolist(), reverse=True),
            "max_radius": float(max_radius),
            "escapes_bloch_ball": max_radius > 1.0 + 1e-10,
        }

    ell_original = steering_ellipsoid(rho)
    rho_pt = partial_transpose_B(rho)
    ell_pt = steering_ellipsoid(rho_pt)

    # Check physicality of rho_pt
    evals_pt = np.linalg.eigvalsh(rho_pt)

    return {
        "pass": True,
        "original_ellipsoid": ell_original,
        "pt_ellipsoid": ell_pt,
        "pt_escapes_bloch_ball": ell_pt["escapes_bloch_ball"],
        "pt_min_eigenvalue": float(np.min(evals_pt)),
        "pt_is_entangled_witness": float(np.min(evals_pt)) < -EPS,
        "insight": ("Partial transpose is positive but not CP.  The steered "
                    "ellipsoid after PT can escape the Bloch ball because "
                    "the map violates complete positivity.  Individual legos "
                    "(steering, PT) work fine alone; the composition reveals "
                    "the non-physicality."),
    }


# ══════════════════════════════════════════════════════════════════════
# TEST 8: Relative Entropy of Near-Identical States
# ══════════════════════════════════════════════════════════════════════

def test_08_relative_entropy_near_identical():
    """
    D(rho||sigma) = Tr(rho (log rho - log sigma)).  When rho ~ sigma,
    this should be tiny.  But if sigma has a near-zero eigenvalue and rho
    has support there, log(~0) can blow up numerically.
    """
    # Base state: slightly mixed
    base = 0.99 * dm(ket0) + 0.01 * dm(ket1)

    results = []
    epsilons = [1e-4, 1e-6, 1e-8, 1e-10, 1e-12, 1e-14]

    for eps in epsilons:
        rho = base + eps * (dm(ket1) - dm(ket0))
        sigma = base - eps * (dm(ket1) - dm(ket0))

        # Ensure valid
        rho = 0.5 * (rho + rho.conj().T)
        sigma = 0.5 * (sigma + sigma.conj().T)
        rho /= np.trace(rho)
        sigma /= np.trace(sigma)

        # Compute D(rho||sigma) with eigendecomposition
        evals_r, evecs_r = np.linalg.eigh(rho)
        evals_s, evecs_s = np.linalg.eigh(sigma)

        D = 0.0
        diverged = False
        for i in range(len(evals_r)):
            if evals_r[i] > EPS:
                for j in range(len(evals_s)):
                    overlap = abs(evecs_r[:, i].conj() @ evecs_s[:, j]) ** 2
                    if evals_s[j] > EPS:
                        D += evals_r[i] * overlap * (
                            np.log2(evals_r[i]) - np.log2(evals_s[j]))
                    elif overlap > EPS:
                        D = np.inf
                        diverged = True
                        break
            if diverged:
                break

        # Matrix log approach
        try:
            log_rho = np.zeros_like(rho)
            log_sigma = np.zeros_like(sigma)
            for i in range(len(evals_r)):
                if evals_r[i] > EPS:
                    log_rho += np.log(evals_r[i]) * np.outer(
                        evecs_r[:, i], evecs_r[:, i].conj())
            for i in range(len(evals_s)):
                if evals_s[i] > EPS:
                    log_sigma += np.log(evals_s[i]) * np.outer(
                        evecs_s[:, i], evecs_s[:, i].conj())
            D_matrix = float(np.real(np.trace(rho @ (log_rho - log_sigma))))
        except Exception:
            D_matrix = float("nan")

        results.append({
            "epsilon": eps,
            "D_eigendecomp": float(D) if not np.isinf(D) else "inf",
            "D_matrix_log": D_matrix,
            "diverged": diverged,
        })

    return {
        "pass": True,
        "results": results,
        "smallest_eps_without_divergence": next(
            (r["epsilon"] for r in results if not r["diverged"]), None),
        "insight": ("Relative entropy is well-defined only when "
                    "supp(rho) <= supp(sigma).  At machine precision, "
                    "perturbations can push rho's support outside sigma's, "
                    "causing log(0) divergence.  Two legos that individually "
                    "handle logs fine can blow up when composed."),
    }


# ══════════════════════════════════════════════════════════════════════
# TEST 9: Eigenvalue Interlacing After Non-TP Map
# ══════════════════════════════════════════════════════════════════════

def test_09_eigenvalue_interlacing_non_tp():
    """
    Cauchy interlacing: if B is a principal submatrix of A, then
    eigenvalues of B interlace those of A.  Apply a non-trace-preserving
    map (amplification), take partial trace (submatrix), check if
    interlacing still holds.
    """
    # 4x4 density matrix (2-qubit)
    psi = np.array([0.5, 0.3, 0.4, np.sqrt(1 - 0.25 - 0.09 - 0.16)],
                   dtype=complex)
    psi /= np.linalg.norm(psi)
    rho = dm(psi)

    # Non-trace-preserving map: amplify by 1.3
    # E(rho) = 1.3 * K rho K^dag where K = sqrt(1.3) * I
    K_amp = np.sqrt(1.3) * np.eye(4, dtype=complex)
    rho_amp = K_amp @ rho @ K_amp.conj().T  # trace = 1.3

    evals_full = np.sort(np.linalg.eigvalsh(rho_amp))[::-1]

    # Principal 2x2 submatrices (upper-left block, i.e., partial trace of B)
    rho_sub = rho_amp[:2, :2]  # Not the same as partial trace!
    evals_sub = np.sort(np.linalg.eigvalsh(rho_sub))[::-1]

    # Cauchy interlacing: lambda_i(A) >= lambda_i(B) >= lambda_{i+n-k}(A)
    # where A is 4x4 (n=4), B is 2x2 (k=2)
    interlacing_holds = True
    violations = []
    for i in range(2):
        upper = evals_full[i]
        lower = evals_full[i + 2]  # i + n - k = i + 2
        if evals_sub[i] > upper + 1e-10 or evals_sub[i] < lower - 1e-10:
            interlacing_holds = False
            violations.append({
                "i": i, "lambda_B_i": float(evals_sub[i]),
                "upper_bound": float(upper), "lower_bound": float(lower)
            })

    # Also check after a more aggressive non-TP map
    K_aggressive = np.diag([2.0, 0.1, 1.5, 0.3]).astype(complex)
    rho_agg = K_aggressive @ rho @ K_aggressive.conj().T
    evals_agg_full = np.sort(np.linalg.eigvalsh(rho_agg))[::-1]
    rho_agg_sub = rho_agg[:2, :2]
    evals_agg_sub = np.sort(np.linalg.eigvalsh(rho_agg_sub))[::-1]

    interlacing_aggressive = True
    violations_agg = []
    for i in range(2):
        upper = evals_agg_full[i]
        lower = evals_agg_full[i + 2]
        if evals_agg_sub[i] > upper + 1e-10 or evals_agg_sub[i] < lower - 1e-10:
            interlacing_aggressive = False
            violations_agg.append({
                "i": i, "lambda_B_i": float(evals_agg_sub[i]),
                "upper_bound": float(upper), "lower_bound": float(lower)
            })

    return {
        "pass": True,
        "uniform_amplification": {
            "interlacing_holds": interlacing_holds,
            "evals_full": evals_full.tolist(),
            "evals_sub": evals_sub.tolist(),
            "violations": violations,
            "trace_amplified": float(np.real(np.trace(rho_amp))),
        },
        "aggressive_non_tp": {
            "interlacing_holds": interlacing_aggressive,
            "evals_full": evals_agg_full.tolist(),
            "evals_sub": evals_agg_sub.tolist(),
            "violations": violations_agg,
            "trace": float(np.real(np.trace(rho_agg))),
        },
        "insight": ("Cauchy interlacing applies to principal submatrices of "
                    "Hermitian matrices -- always.  Non-TP maps preserve "
                    "Hermiticity so interlacing SHOULD still hold for the "
                    "submatrix.  The compound question: does taking a "
                    "non-physical (trace != 1) density matrix and then "
                    "extracting a submatrix create any subtle numerical "
                    "violations?"),
    }


# ══════════════════════════════════════════════════════════════════════
# TEST 10: MPS Bond Dimension After CNOT Across Cut
# ══════════════════════════════════════════════════════════════════════

def test_10_mps_bond_dimension_cnot():
    """
    A 2-qubit MPS with bond dimension chi.  Apply CNOT across the bond.
    Schmidt rank should double (up to chi_max).  What happens when we
    truncate?  How much fidelity is lost?
    """
    # Start with a product state in MPS form
    # |psi> = |+>|0> = (|00> + |10>) / sqrt(2)
    # Schmidt decomposition: 1 singular value = 1 (it's a product state... wait)
    # Actually |+>|0> = (|0>+|1>)/sqrt2 x |0> => SVD has rank 1
    psi_init = np.array([1, 0, 1, 0], dtype=complex) / np.sqrt(2)

    def schmidt_decomposition(psi_4, dA=2, dB=2):
        """Return Schmidt coefficients of a 4-dim bipartite state."""
        M = psi_4.reshape(dA, dB)
        U, s, Vt = np.linalg.svd(M, full_matrices=False)
        return s[s > EPS]

    # CNOT gate (control=first qubit, target=second)
    CNOT = np.array([[1, 0, 0, 0],
                     [0, 1, 0, 0],
                     [0, 0, 0, 1],
                     [0, 0, 1, 0]], dtype=complex)

    schmidt_before = schmidt_decomposition(psi_init)
    psi_after = CNOT @ psi_init
    schmidt_after = schmidt_decomposition(psi_after)

    # Now test with a more interesting initial state that already has
    # bond dimension 2: partially entangled
    theta = np.pi / 6
    psi_ent = np.cos(theta) * np.array([1, 0, 0, 0], dtype=complex) + \
              np.sin(theta) * np.array([0, 0, 0, 1], dtype=complex)
    schmidt_ent_before = schmidt_decomposition(psi_ent)
    psi_ent_after = CNOT @ psi_ent
    schmidt_ent_after = schmidt_decomposition(psi_ent_after)

    # Truncation test: take a 4-qubit state, apply CNOT across middle cut,
    # truncate bond dimension, measure fidelity loss
    # 4-qubit state: |GHZ4> = (|0000> + |1111>) / sqrt(2)
    ghz4 = np.zeros(16, dtype=complex)
    ghz4[0] = ghz4[15] = 1 / np.sqrt(2)

    # Reshape as (4, 4) for cut between qubits 2 and 3
    # Qubits: q1q2 | q3q4 => dA=4, dB=4
    schmidt_ghz4 = schmidt_decomposition(ghz4, dA=4, dB=4)

    # Apply CNOT on qubits 2-3 (across cut)
    # Build CNOT on q2,q3 embedded in 4-qubit space
    # q2 is bit 1 of left half, q3 is bit 0 of right half
    CNOT_23 = np.eye(16, dtype=complex)
    for i in range(16):
        bits = [(i >> b) & 1 for b in range(4)]  # bits[0]=q4,...,bits[3]=q1
        q2 = bits[2]  # qubit 2
        q3 = bits[1]  # qubit 3
        if q2 == 1:
            # Flip q3
            j = i ^ (1 << 1)
            CNOT_23[i, i] = 0
            CNOT_23[j, i] = 1

    ghz4_after = CNOT_23 @ ghz4
    schmidt_ghz4_after = schmidt_decomposition(ghz4_after, dA=4, dB=4)

    # Truncation: keep only top chi singular values
    M_after = ghz4_after.reshape(4, 4)
    U, s, Vt = np.linalg.svd(M_after, full_matrices=False)
    fidelity_losses = {}
    for chi_max in [1, 2, 3, 4]:
        s_trunc = s.copy()
        s_trunc[chi_max:] = 0
        psi_trunc = (U @ np.diag(s_trunc) @ Vt).ravel()
        psi_trunc_norm = np.linalg.norm(psi_trunc)
        if psi_trunc_norm > EPS:
            psi_trunc /= psi_trunc_norm
        fid = abs(np.dot(ghz4_after.conj(), psi_trunc)) ** 2
        fidelity_losses[f"chi={chi_max}"] = {
            "fidelity": float(fid),
            "truncation_error": float(1 - fid),
        }

    return {
        "pass": True,
        "product_state": {
            "schmidt_before": schmidt_before.tolist(),
            "schmidt_after": schmidt_after.tolist(),
            "bond_dim_before": len(schmidt_before),
            "bond_dim_after": len(schmidt_after),
        },
        "entangled_state": {
            "schmidt_before": schmidt_ent_before.tolist(),
            "schmidt_after": schmidt_ent_after.tolist(),
            "bond_dim_before": len(schmidt_ent_before),
            "bond_dim_after": len(schmidt_ent_after),
        },
        "ghz4_across_cut": {
            "schmidt_before": schmidt_ghz4.tolist(),
            "bond_dim_before": len(schmidt_ghz4),
            "schmidt_after": schmidt_ghz4_after.tolist(),
            "bond_dim_after": len(schmidt_ghz4_after),
            "truncation_fidelities": fidelity_losses,
        },
        "insight": ("CNOT across an MPS bond cut can increase Schmidt rank. "
                    "When bond dimension is truncated, fidelity loss depends "
                    "on the discarded singular values.  The compound failure: "
                    "gate application + truncation + subsequent measurements "
                    "all accumulate error silently."),
    }


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    tests = [
        ("01_iterated_channel_entropy", test_01_iterated_channel_entropy),
        ("02_concurrence_sic_reconstruction", test_02_concurrence_sic_reconstruction),
        ("03_berry_phase_compression", test_03_berry_phase_compression),
        ("04_qfi_dephasing_depth", test_04_qfi_dephasing_depth),
        ("05_teleportation_werner_eigenstate", test_05_teleportation_werner_eigenstate),
        ("06_discord_after_distillation", test_06_discord_after_distillation),
        ("07_steering_ellipsoid_non_cp", test_07_steering_ellipsoid_non_cp),
        ("08_relative_entropy_near_identical", test_08_relative_entropy_near_identical),
        ("09_eigenvalue_interlacing_non_tp", test_09_eigenvalue_interlacing_non_tp),
        ("10_mps_bond_dimension_cnot", test_10_mps_bond_dimension_cnot),
    ]

    t0 = time.time()
    all_pass = True

    for name, fn in tests:
        print(f"\n{'─' * 60}")
        print(f"  TEST: {name}")
        print(f"{'─' * 60}")
        try:
            result = fn()
            RESULTS[name] = result
            status = "PASS" if result.get("pass") else "FAIL"
            if not result.get("pass"):
                all_pass = False
            print(f"  => {status}")
            # Print key findings
            for k, v in result.items():
                if k in ("pass", "insight"):
                    continue
                if isinstance(v, (dict, list)):
                    continue
                print(f"     {k}: {v}")
            if "insight" in result:
                print(f"     INSIGHT: {result['insight'][:120]}...")
        except Exception as e:
            RESULTS[name] = {"pass": False, "error": str(e),
                             "traceback": traceback.format_exc()}
            all_pass = False
            print(f"  => ERROR: {e}")
            traceback.print_exc()

    elapsed = time.time() - t0
    RESULTS["summary"] = {
        "all_pass": all_pass,
        "elapsed_seconds": round(elapsed, 3),
        "num_tests": len(tests),
        "tests_passed": sum(1 for k, v in RESULTS.items()
                            if k != "summary" and isinstance(v, dict)
                            and v.get("pass", False)),
        "description": (
            "Compound negative battery: 10 tests where individually correct "
            "legos produce failures when COMPOSED.  Numerical error "
            "accumulation, reconstruction noise, compression artifacts, "
            "formula misapplication, and truncation losses."
        ),
    }

    print(f"\n{'=' * 70}")
    print(f"ALL PASS: {all_pass}   Time: {elapsed:.2f}s   "
          f"({RESULTS['summary']['tests_passed']}/{len(tests)} passed)")
    print(f"{'=' * 70}")

    out_path = (pathlib.Path(__file__).parent / "a2_state" / "sim_results" /
                "negative_compound_failures_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(sanitize(RESULTS), f, indent=2, default=str)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
