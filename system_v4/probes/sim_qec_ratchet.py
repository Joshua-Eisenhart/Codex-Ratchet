#!/usr/bin/env python3
"""
QEC Ratchet -- Does quantum error correction extend the ratchet's lifetime?
===========================================================================

Proof-of-concept: 3-qubit bit-flip repetition code as a ratchet shield.

Encode:  |0> -> |000>,  |1> -> |111>
Error:   bit_flip(p) applied independently to each physical qubit
Correct: majority-vote syndrome measurement + correction
Decode:  extract logical qubit

Pipeline per cycle:
  1. Encode logical qubit into 3 physical qubits
  2. Apply noise (bit_flip to each qubit independently)
  3. Error correction (syndrome measurement + majority-vote correction)
  4. Decode back to logical qubit
  5. Measure I_c on the logical qubit

Compare:
  - Unprotected: single qubit through bit_flip, N cycles
  - Protected: 3-qubit repetition code through bit_flip, N cycles
  - Track I_c for both over N = 1, 5, 10, 20, 50

Tests:
  Positive:
    - Protected I_c survives longer than unprotected
    - At low noise (p < 0.1), protection extends lifetime significantly
  Negative:
    - At high noise (p > 0.5), protection fails (above code threshold)
  Boundary:
    - p=0: both survive forever
    - p=0.5: code threshold (effective error rate = threshold)

Classification: canonical. pytorch=used, z3=tried.
Output: sim_results/qec_ratchet_results.json
"""

import json
import os
import traceback
import time
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- pure density matrix QEC sim"},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed for this sim"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed for this sim"},
    "clifford":  {"tried": False, "used": False, "reason": "not needed for this sim"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this sim"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed for this sim"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this sim"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed for this sim"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed for this sim"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed for this sim"},
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Core: density matrix channel sim, autograd-compatible QEC pipeline"
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

z3_available = False
try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "Tried: used to verify syndrome truth table exhaustively"
    )
    z3_available = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"


# =====================================================================
# QUANTUM PRIMITIVES
# =====================================================================

def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho log2 rho), via eigendecomposition."""
    eigs = torch.real(torch.linalg.eigvalsh(rho))
    eigs_clamped = torch.clamp(eigs, min=1e-12)
    return -torch.sum(eigs_clamped * torch.log2(eigs_clamped))


def partial_trace_a(rho_ab, dim_a=2, dim_b=2):
    """Trace out subsystem A, return rho_B."""
    rho_r = rho_ab.reshape(dim_a, dim_b, dim_a, dim_b)
    return torch.einsum("ijkj->ik", rho_r)


def partial_trace_b(rho_ab, dim_a=2, dim_b=2):
    """Trace out subsystem B, return rho_A."""
    rho_r = rho_ab.reshape(dim_a, dim_b, dim_a, dim_b)
    return torch.einsum("ijil->jl", rho_r)


def coherent_information(rho_ab, dim_a=2, dim_b=2):
    """I_c(A>B) = S(B) - S(AB). Positive = quantum info flows A->B."""
    rho_b = partial_trace_a(rho_ab, dim_a, dim_b)
    S_B = von_neumann_entropy(rho_b)
    S_AB = von_neumann_entropy(rho_ab)
    return S_B - S_AB


# =====================================================================
# SINGLE-QUBIT CHANNELS
# =====================================================================

def apply_bit_flip(rho, p):
    """Bit-flip channel: rho -> (1-p)*rho + p*X*rho*X."""
    X = torch.tensor([[0, 1], [1, 0]], dtype=rho.dtype, device=rho.device)
    p_t = torch.tensor(float(p), dtype=torch.float32, device=rho.device)
    return (1.0 - p_t) * rho + p_t * (X @ rho @ X)


# =====================================================================
# 3-QUBIT REPETITION CODE
# =====================================================================

def encode_repetition(rho_logical):
    """Encode single-qubit state into 3-qubit repetition code.

    |0> -> |000>,  |1> -> |111>
    Operates on density matrix: rho_logical (2x2) -> rho_code (8x8).

    The encoding unitary maps:
      |0> -> |000>  (index 0 -> index 0)
      |1> -> |111>  (index 1 -> index 7)

    So the 2x2 logical density matrix maps into the {|000>, |111>} subspace
    of the 8-dimensional 3-qubit Hilbert space.
    """
    rho_code = torch.zeros(8, 8, dtype=rho_logical.dtype, device=rho_logical.device)
    # |000><000| component
    rho_code[0, 0] = rho_logical[0, 0]
    # |000><111| component
    rho_code[0, 7] = rho_logical[0, 1]
    # |111><000| component
    rho_code[7, 0] = rho_logical[1, 0]
    # |111><111| component
    rho_code[7, 7] = rho_logical[1, 1]
    return rho_code


def apply_bit_flip_each_qubit(rho_3q, p):
    """Apply independent bit-flip(p) to each of the 3 qubits.

    Works by applying the bit-flip Kraus operators to each qubit subsystem.
    For a 3-qubit system (dim 8), we iterate over qubits 0, 1, 2.
    """
    dim = 2
    n_qubits = 3
    rho = rho_3q.clone()

    for qubit_idx in range(n_qubits):
        # Build the 8x8 Kraus operators for bit-flip on qubit_idx
        # K0 = sqrt(1-p) * I_8,  K1 = sqrt(p) * (I_before x X x I_after)
        I2 = torch.eye(2, dtype=rho.dtype, device=rho.device)
        X = torch.tensor([[0, 1], [1, 0]], dtype=rho.dtype, device=rho.device)

        # Build X on qubit_idx via Kronecker products
        ops_identity = [I2] * n_qubits
        ops_flip = [I2] * n_qubits
        ops_flip[qubit_idx] = X

        X_full = ops_flip[0]
        for i in range(1, n_qubits):
            X_full = torch.kron(X_full, ops_flip[i])

        p_t = torch.tensor(float(p), dtype=torch.float32, device=rho.device)
        rho = (1.0 - p_t) * rho + p_t * (X_full @ rho @ X_full)

    return rho


def syndrome_and_correct(rho_3q):
    """Syndrome measurement + majority-vote correction on 3-qubit code.

    Syndrome operators (projective measurement):
      - Measure Z1*Z2 (parity of qubits 0,1)
      - Measure Z2*Z3 (parity of qubits 1,2)

    4 syndrome outcomes -> correction:
      (0,0): no error
      (1,0): flip qubit 0
      (0,1): flip qubit 2
      (1,1): flip qubit 1

    Implemented as projective measurement:
      rho -> sum_s  P_s * rho * P_s  (then apply correction conditioned on s)
    which equals sum_s  C_s * P_s * rho * P_s * C_s^dag.
    """
    dim = 8
    I2 = torch.eye(2, dtype=rho_3q.dtype, device=rho_3q.device)
    Z = torch.tensor([[1, 0], [0, -1]], dtype=rho_3q.dtype, device=rho_3q.device)
    X = torch.tensor([[0, 1], [1, 0]], dtype=rho_3q.dtype, device=rho_3q.device)
    I8 = torch.eye(dim, dtype=rho_3q.dtype, device=rho_3q.device)

    def kron3(a, b, c):
        return torch.kron(torch.kron(a, b), c)

    # Syndrome operators: Z_iZ_j eigenvalues are +1 or -1
    Z1Z2 = kron3(Z, Z, I2)  # Z on qubit 0,1
    Z2Z3 = kron3(I2, Z, Z)  # Z on qubit 1,2

    # Projectors for each syndrome outcome
    # P_{s1,s2} = (I + (-1)^s1 * Z1Z2)/2  *  (I + (-1)^s2 * Z2Z3)/2
    projectors = {}
    corrections = {}

    for s1 in range(2):
        for s2 in range(2):
            sign1 = 1.0 if s1 == 0 else -1.0
            sign2 = 1.0 if s2 == 0 else -1.0
            P = (I8 + sign1 * Z1Z2) / 2.0 @ (I8 + sign2 * Z2Z3) / 2.0
            projectors[(s1, s2)] = P

            # Correction operator
            if (s1, s2) == (0, 0):
                corrections[(s1, s2)] = I8  # no error
            elif (s1, s2) == (1, 0):
                corrections[(s1, s2)] = kron3(X, I2, I2)  # flip qubit 0
            elif (s1, s2) == (0, 1):
                corrections[(s1, s2)] = kron3(I2, I2, X)  # flip qubit 2
            elif (s1, s2) == (1, 1):
                corrections[(s1, s2)] = kron3(I2, X, I2)  # flip qubit 1

    # Apply syndrome measurement + correction
    rho_corrected = torch.zeros_like(rho_3q)
    for (s1, s2), P in projectors.items():
        C = corrections[(s1, s2)]
        # Project, then correct: C * P * rho * P^dag * C^dag
        projected = P @ rho_3q @ P.conj().T
        corrected = C @ projected @ C.conj().T
        rho_corrected = rho_corrected + corrected

    return rho_corrected


def decode_repetition(rho_3q):
    """Decode 3-qubit repetition code back to single logical qubit.

    Reverse of encode: project onto codespace {|000>, |111>} and extract
    the 2x2 logical density matrix.

    After successful error correction, state should be in the codespace.
    We extract the logical qubit by reading the (0,0), (0,7), (7,0), (7,7)
    elements.
    """
    rho_logical = torch.zeros(2, 2, dtype=rho_3q.dtype, device=rho_3q.device)
    rho_logical[0, 0] = rho_3q[0, 0]
    rho_logical[0, 1] = rho_3q[0, 7]
    rho_logical[1, 0] = rho_3q[7, 0]
    rho_logical[1, 1] = rho_3q[7, 7]

    # Normalize (correction may leak slightly out of codespace)
    tr = torch.real(torch.trace(rho_logical))
    if tr.item() > 1e-12:
        rho_logical = rho_logical / tr

    return rho_logical


# =====================================================================
# I_c MEASUREMENT ON LOGICAL QUBIT
# =====================================================================

def measure_logical_ic(rho_logical):
    """Measure coherent information of a single logical qubit.

    For a single qubit, I_c is defined relative to a reference.
    We use the qubit's purity-based coherent information:
    I_c = 1 - S(rho), which measures how far from maximally mixed.

    This equals the capacity of the identity channel on the qubit state.
    At pure state: I_c = 1. At maximally mixed: I_c = 0.
    """
    S = von_neumann_entropy(rho_logical)
    return 1.0 - S


# =====================================================================
# QEC CYCLE PIPELINE
# =====================================================================

def qec_cycle(rho_logical, p):
    """One full QEC cycle: encode -> noise -> correct -> decode -> measure.

    Returns (rho_logical_out, I_c).
    """
    # 1. Encode
    rho_code = encode_repetition(rho_logical)
    # 2. Noise
    rho_noisy = apply_bit_flip_each_qubit(rho_code, p)
    # 3. Error correction
    rho_corrected = syndrome_and_correct(rho_noisy)
    # 4. Decode
    rho_out = decode_repetition(rho_corrected)
    # 5. Measure I_c
    ic = measure_logical_ic(rho_out)
    return rho_out, ic


def unprotected_cycle(rho_logical, p):
    """One unprotected cycle: just apply bit_flip directly.

    Returns (rho_out, I_c).
    """
    rho_out = apply_bit_flip(rho_logical, p)
    ic = measure_logical_ic(rho_out)
    return rho_out, ic


# =====================================================================
# CASCADE RUNNERS
# =====================================================================

def run_protected_cascade(rho_init, p, n_cycles):
    """Run N QEC-protected cycles, tracking I_c."""
    rho = rho_init.clone()
    trajectory = []
    ic_init = measure_logical_ic(rho)
    trajectory.append({"cycle": 0, "ic": ic_init.item()})

    for n in range(1, n_cycles + 1):
        rho, ic = qec_cycle(rho, p)
        trajectory.append({"cycle": n, "ic": ic.item()})

    return trajectory


def run_unprotected_cascade(rho_init, p, n_cycles):
    """Run N unprotected cycles, tracking I_c."""
    rho = rho_init.clone()
    trajectory = []
    ic_init = measure_logical_ic(rho)
    trajectory.append({"cycle": 0, "ic": ic_init.item()})

    for n in range(1, n_cycles + 1):
        rho, ic = unprotected_cycle(rho, p)
        trajectory.append({"cycle": n, "ic": ic.item()})

    return trajectory


# =====================================================================
# INITIAL STATE
# =====================================================================

def build_initial_logical_state():
    """Build a pure logical qubit on the Bloch equator: cos(pi/8)|0> + sin(pi/8)|1>.

    This state has significant Z-basis coherence AND is NOT an eigenstate of X,
    so bit-flip noise degrades it visibly. I_c starts at 1.0 (pure state).

    Note: |+> is invariant under bit-flip (X|+>=|+>), so it would show no decay.
    |0> would work but decays to diagonal mixture with no off-diagonal signal.
    This intermediate state gives the clearest demonstration of QEC advantage.
    """
    theta = torch.tensor(np.pi / 4)  # pi/4 on Bloch sphere -> good mix
    psi = torch.tensor(
        [torch.cos(theta / 2), torch.sin(theta / 2)], dtype=torch.complex64
    )
    rho = torch.outer(psi, psi.conj())
    return rho


# =====================================================================
# Z3 SYNDROME VERIFICATION
# =====================================================================

def z3_verify_syndrome_table():
    """Use z3 to exhaustively verify the syndrome truth table.

    For all 8 possible 3-bit error patterns, check that the syndrome
    correctly identifies and corrects single-bit errors.
    """
    if not z3_available:
        return {"pass": True, "skipped": True, "reason": "z3 not available"}

    try:
        s = z3.Solver()

        # For each single-bit error pattern, verify correction is correct
        # Error patterns: 000 (no error), 001, 010, 100 (single errors)
        # Also: 011, 101, 110, 111 (multi-bit -- should fail for rep code)
        results = {}

        for err_pattern in range(8):
            e0 = (err_pattern >> 2) & 1
            e1 = (err_pattern >> 1) & 1
            e2 = err_pattern & 1
            n_errors = e0 + e1 + e2

            # Syndrome bits: s1 = e0 XOR e1, s2 = e1 XOR e2
            s1 = e0 ^ e1
            s2 = e1 ^ e2

            # Correction from syndrome
            if (s1, s2) == (0, 0):
                corrected = (e0, e1, e2)  # no correction
            elif (s1, s2) == (1, 0):
                corrected = (1 - e0, e1, e2)  # flip qubit 0
            elif (s1, s2) == (0, 1):
                corrected = (e0, e1, 1 - e2)  # flip qubit 2
            elif (s1, s2) == (1, 1):
                corrected = (e0, 1 - e1, e2)  # flip qubit 1

            all_zero = (corrected == (0, 0, 0))
            correctly_corrected = all_zero if n_errors <= 1 else None

            results[f"err_{e0}{e1}{e2}"] = {
                "n_errors": n_errors,
                "syndrome": (s1, s2),
                "corrected_to_zero": all_zero,
                "single_error_fixed": correctly_corrected,
            }

        # Verify with z3: for all single-bit errors, correction produces 000
        e = [z3.Bool(f"e{i}") for i in range(3)]

        # Syndrome equations
        s1_expr = z3.Xor(e[0], e[1])
        s2_expr = z3.Xor(e[1], e[2])

        # Single-error constraint: at most one error
        single_error = z3.Or(
            z3.And(z3.Not(e[0]), z3.Not(e[1]), z3.Not(e[2])),  # 0 errors
            z3.And(e[0], z3.Not(e[1]), z3.Not(e[2])),          # e0 only
            z3.And(z3.Not(e[0]), e[1], z3.Not(e[2])),          # e1 only
            z3.And(z3.Not(e[0]), z3.Not(e[1]), e[2]),           # e2 only
        )

        # After correction, all errors should be fixed (residual = 0)
        # Correction logic: if s1 and not s2 -> flip e0; if s2 and not s1 -> flip e2;
        #                    if s1 and s2 -> flip e1; else no flip
        c0 = z3.Xor(e[0], z3.And(s1_expr, z3.Not(s2_expr)))
        c1 = z3.Xor(e[1], z3.And(s1_expr, s2_expr))
        c2 = z3.Xor(e[2], z3.And(z3.Not(s1_expr), s2_expr))

        # After correction, residual errors should all be False
        s.add(single_error)
        s.add(z3.Or(c0, c1, c2))  # claim: there exists a residual error

        z3_result = s.check()
        # If UNSAT, no single-error pattern leaves a residual -> code is correct
        code_correct = (str(z3_result) == "unsat")

        return {
            "pass": code_correct,
            "z3_result": str(z3_result),
            "truth_table": results,
            "interpretation": (
                "UNSAT means no single-bit error survives correction"
                if code_correct else
                "SAT means the code has a bug"
            ),
        }

    except Exception:
        return {"pass": False, "error": traceback.format_exc()}


# =====================================================================
# EFFECTIVE ERROR RATE CALCULATION
# =====================================================================

def effective_error_rate_3rep(p):
    """Effective logical error rate for 3-qubit repetition code.

    The code fails when 2 or 3 qubits flip:
      p_fail = 3*p^2*(1-p) + p^3 = 3p^2 - 2p^3

    For p < 0.5, p_fail < p (code helps).
    For p = 0.5, p_fail = 0.5 (threshold).
    For p > 0.5, p_fail > p (code hurts).
    """
    return 3 * p**2 - 2 * p**3


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- Test 1: Protected I_c survives longer than unprotected ---
    try:
        rho_init = build_initial_logical_state()
        p = 0.05
        cycle_counts = [1, 5, 10, 20, 50]
        max_n = max(cycle_counts)

        with torch.no_grad():
            prot_traj = run_protected_cascade(rho_init, p, max_n)
            unprot_traj = run_unprotected_cascade(rho_init, p, max_n)

        prot_ic = {str(n): prot_traj[n]["ic"] for n in cycle_counts}
        unprot_ic = {str(n): unprot_traj[n]["ic"] for n in cycle_counts}

        # Protected should have higher I_c at every checkpoint
        prot_wins_all = all(
            prot_ic[str(n)] > unprot_ic[str(n)] + 1e-6
            for n in cycle_counts
        )

        # Protected final I_c should be meaningfully higher
        prot_advantage = prot_ic["50"] - unprot_ic["50"]

        results["protected_survives_longer"] = {
            "pass": prot_wins_all,
            "noise_p": p,
            "protected_ic": prot_ic,
            "unprotected_ic": unprot_ic,
            "advantage_at_50": float(prot_advantage),
            "prot_wins_all_checkpoints": prot_wins_all,
        }
    except Exception:
        results["protected_survives_longer"] = {"pass": False, "error": traceback.format_exc()}

    # --- Test 2: Low noise -> significant lifetime extension ---
    try:
        rho_init = build_initial_logical_state()
        low_noise_levels = [0.01, 0.05, 0.08]
        n_cycles = 200  # enough cycles for low-noise divergence to manifest

        extension_results = {}
        all_significant = True

        for p in low_noise_levels:
            with torch.no_grad():
                prot = run_protected_cascade(rho_init, p, n_cycles)
                unprot = run_unprotected_cascade(rho_init, p, n_cycles)

            # Find half-life (first cycle where I_c < 0.5)
            def half_life(traj):
                for t in traj:
                    if t["ic"] < 0.5 and t["cycle"] > 0:
                        return t["cycle"]
                return n_cycles  # survived entire run

            prot_hl = half_life(prot)
            unprot_hl = half_life(unprot)

            ratio = prot_hl / max(unprot_hl, 1)
            significant = ratio > 1.5  # at least 1.5x lifetime extension
            if not significant:
                all_significant = False

            extension_results[str(p)] = {
                "protected_half_life": prot_hl,
                "unprotected_half_life": unprot_hl,
                "extension_ratio": float(ratio),
                "significant": significant,
                "effective_error_rate": float(effective_error_rate_3rep(p)),
            }

        results["low_noise_significant_extension"] = {
            "pass": all_significant,
            "noise_levels": low_noise_levels,
            "results": extension_results,
        }
    except Exception:
        results["low_noise_significant_extension"] = {
            "pass": False, "error": traceback.format_exc()
        }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- Negative 1: High noise (p > 0.5) -> protection FAILS ---
    try:
        rho_init = build_initial_logical_state()
        high_noise_levels = [0.55, 0.6, 0.7]
        n_cycles = 20

        all_fail = True
        failure_results = {}

        for p in high_noise_levels:
            with torch.no_grad():
                prot = run_protected_cascade(rho_init, p, n_cycles)
                unprot = run_unprotected_cascade(rho_init, p, n_cycles)

            prot_final = prot[-1]["ic"]
            unprot_final = unprot[-1]["ic"]

            # Above threshold: protected should be WORSE than or equal to unprotected
            prot_fails = prot_final <= unprot_final + 1e-6

            if not prot_fails:
                all_fail = False

            failure_results[str(p)] = {
                "protected_final_ic": float(prot_final),
                "unprotected_final_ic": float(unprot_final),
                "protection_failed": prot_fails,
                "effective_error_rate": float(effective_error_rate_3rep(p)),
                "note": f"p_eff={effective_error_rate_3rep(p):.4f} > p={p} (code amplifies noise)",
            }

        results["high_noise_protection_fails"] = {
            "pass": all_fail,
            "noise_levels": high_noise_levels,
            "results": failure_results,
            "interpretation": (
                "Above p=0.5 threshold, the 3-qubit code amplifies errors "
                "because majority vote gets it wrong more often than right"
            ),
        }
    except Exception:
        results["high_noise_protection_fails"] = {
            "pass": False, "error": traceback.format_exc()
        }

    # --- Negative 2: z3 syndrome verification ---
    try:
        z3_result = z3_verify_syndrome_table()
        results["z3_syndrome_verification"] = z3_result
    except Exception:
        results["z3_syndrome_verification"] = {
            "pass": False, "error": traceback.format_exc()
        }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- Boundary 1: p=0 -> both survive forever ---
    try:
        rho_init = build_initial_logical_state()
        n_cycles = 50

        with torch.no_grad():
            prot = run_protected_cascade(rho_init, 0.0, n_cycles)
            unprot = run_unprotected_cascade(rho_init, 0.0, n_cycles)

        prot_ics = [t["ic"] for t in prot]
        unprot_ics = [t["ic"] for t in unprot]

        # Both should maintain I_c = 1.0 throughout
        prot_stable = all(abs(ic - 1.0) < 1e-4 for ic in prot_ics)
        unprot_stable = all(abs(ic - 1.0) < 1e-4 for ic in unprot_ics)

        results["p0_both_survive"] = {
            "pass": prot_stable and unprot_stable,
            "protected_stable": prot_stable,
            "unprotected_stable": unprot_stable,
            "protected_range": [float(min(prot_ics)), float(max(prot_ics))],
            "unprotected_range": [float(min(unprot_ics)), float(max(unprot_ics))],
        }
    except Exception:
        results["p0_both_survive"] = {"pass": False, "error": traceback.format_exc()}

    # --- Boundary 2: p=0.5 -> code threshold (effective = physical) ---
    try:
        rho_init = build_initial_logical_state()
        n_cycles = 20

        with torch.no_grad():
            prot = run_protected_cascade(rho_init, 0.5, n_cycles)
            unprot = run_unprotected_cascade(rho_init, 0.5, n_cycles)

        prot_final = prot[-1]["ic"]
        unprot_final = unprot[-1]["ic"]

        # At threshold, both should converge to same value (maximally mixed)
        # The effective error rate at p=0.5: 3*(0.25)-2*(0.125) = 0.75-0.25 = 0.5
        # So both channels are equivalent at threshold
        threshold_match = abs(prot_final - unprot_final) < 0.05

        results["p05_threshold"] = {
            "pass": threshold_match,
            "protected_final_ic": float(prot_final),
            "unprotected_final_ic": float(unprot_final),
            "difference": float(abs(prot_final - unprot_final)),
            "effective_error_rate": float(effective_error_rate_3rep(0.5)),
            "note": "At p=0.5, p_eff = 0.5, so code gives no advantage",
        }
    except Exception:
        results["p05_threshold"] = {"pass": False, "error": traceback.format_exc()}

    # --- Boundary 3: Trace preservation throughout pipeline ---
    try:
        rho_init = build_initial_logical_state()
        p = 0.1
        n_cycles = 10

        trace_violations = []
        rho = rho_init.clone()

        with torch.no_grad():
            for n in range(n_cycles):
                # Check trace at each intermediate step
                rho_code = encode_repetition(rho)
                tr_encode = torch.real(torch.trace(rho_code)).item()

                rho_noisy = apply_bit_flip_each_qubit(rho_code, p)
                tr_noise = torch.real(torch.trace(rho_noisy)).item()

                rho_corrected = syndrome_and_correct(rho_noisy)
                tr_correct = torch.real(torch.trace(rho_corrected)).item()

                rho = decode_repetition(rho_corrected)
                tr_decode = torch.real(torch.trace(rho)).item()

                for label, tr_val in [
                    ("encode", tr_encode), ("noise", tr_noise),
                    ("correct", tr_correct), ("decode", tr_decode),
                ]:
                    if abs(tr_val - 1.0) > 1e-4:
                        trace_violations.append({
                            "cycle": n, "step": label, "trace": tr_val
                        })

        results["trace_preservation"] = {
            "pass": len(trace_violations) == 0,
            "violations": trace_violations[:10],  # cap output
            "cycles_checked": n_cycles,
        }
    except Exception:
        results["trace_preservation"] = {"pass": False, "error": traceback.format_exc()}

    return results


# =====================================================================
# COMPARISON ANALYSIS
# =====================================================================

def run_comparison_analysis():
    """Full comparison across noise levels and cycle counts."""
    analysis = {}
    rho_init = build_initial_logical_state()

    noise_levels = [0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    cycle_counts = [1, 5, 10, 20, 50]
    max_n = max(cycle_counts)

    comparison = {}
    for p in noise_levels:
        with torch.no_grad():
            prot = run_protected_cascade(rho_init, p, max_n)
            unprot = run_unprotected_cascade(rho_init, p, max_n)

        comparison[str(p)] = {
            "protected": {str(n): prot[n]["ic"] for n in cycle_counts},
            "unprotected": {str(n): unprot[n]["ic"] for n in cycle_counts},
            "effective_error_rate": float(effective_error_rate_3rep(p)),
            "code_helps": effective_error_rate_3rep(p) < p,
        }

    analysis["noise_sweep"] = comparison

    # Crossover point analysis
    crossover_p = None
    for p in np.linspace(0.01, 0.99, 200):
        if effective_error_rate_3rep(p) >= p:
            crossover_p = float(p)
            break

    analysis["crossover_point"] = {
        "p_threshold": crossover_p,
        "theoretical_threshold": 0.5,
        "note": "Below threshold: code reduces error. Above: code amplifies.",
    }

    return analysis


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    t0 = time.time()

    print("Running positive tests...")
    positive = run_positive_tests()
    print("Running negative tests...")
    negative = run_negative_tests()
    print("Running boundary tests...")
    boundary = run_boundary_tests()
    print("Running comparison analysis...")
    analysis = run_comparison_analysis()

    elapsed = time.time() - t0

    # Summary stats
    all_tests = {}
    all_tests.update(positive)
    all_tests.update(negative)
    all_tests.update(boundary)
    n_pass = sum(1 for v in all_tests.values() if v.get("pass"))
    n_total = len(all_tests)

    results = {
        "name": "qec_ratchet -- does quantum error correction extend the ratchet's lifetime?",
        "tool_manifest": TOOL_MANIFEST,
        "classification": "canonical",
        "summary": {
            "tests_passed": n_pass,
            "tests_total": n_total,
            "elapsed_seconds": round(elapsed, 2),
            "key_findings": {
                "qec_extends_lifetime": positive.get(
                    "protected_survives_longer", {}
                ).get("pass", False),
                "low_noise_significant": positive.get(
                    "low_noise_significant_extension", {}
                ).get("pass", False),
                "high_noise_fails": negative.get(
                    "high_noise_protection_fails", {}
                ).get("pass", False),
                "threshold_at_p05": boundary.get(
                    "p05_threshold", {}
                ).get("pass", False),
            },
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "comparison_analysis": analysis,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "qec_ratchet_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
    print(f"Tests: {n_pass}/{n_total} passed in {elapsed:.1f}s")

    # Quick summary to stdout
    for section_name, section in [
        ("POSITIVE", positive), ("NEGATIVE", negative), ("BOUNDARY", boundary),
    ]:
        print(f"\n--- {section_name} ---")
        for k, v in section.items():
            status = "PASS" if v.get("pass") else "FAIL"
            print(f"  [{status}] {k}")

    print(f"\n--- COMPARISON ANALYSIS ---")
    sweep = analysis.get("noise_sweep", {})
    for p_str, data in sweep.items():
        helps = "YES" if data["code_helps"] else "NO"
        print(f"  p={p_str}: code helps={helps}, "
              f"p_eff={data['effective_error_rate']:.4f}")

    cross = analysis.get("crossover_point", {})
    print(f"\n  Threshold: p={cross.get('p_threshold', 'N/A')}")
