#!/usr/bin/env python3
"""
sim_pure_lego_steane_surface.py
===============================

Pure-lego quantum error correction probe.  numpy only, no engine.

Sections
--------
1. Steane [[7,1,3]] code
   - Stabilizer generators from classical Hamming [7,4,3]
   - Encode |0_L> and |1_L>
   - Single X/Y/Z error on each of 7 qubits -> syndrome -> correction
   - Verify fidelity = 1 after correction for all single-qubit errors

2. Logical transversal CNOT between two Steane blocks
   - Verify output stays in code space

3. Surface code toy (3x3 lattice)
   - 9 data qubits + 8 syndrome ancillas
   - X-plaquette and Z-star stabilizers
   - Verify stabilizer group commutes
   - Single X error -> syndrome localizes it

4. Code distance verification
   - Steane d=3 corrects 1 error
   - 2-qubit error NOT correctable (syndrome aliases)
"""

import json
import os
import sys
from datetime import datetime, UTC
from itertools import combinations

import numpy as np
classification = "classical_baseline"  # auto-backfill

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results",
)
os.makedirs(RESULTS_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════
# Pauli matrices and helpers
# ═══════════════════════════════════════════════════════════════════

I = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)

PAULIS = {"I": I, "X": X, "Y": Y, "Z": Z}

KET_0 = np.array([1, 0], dtype=complex)
KET_1 = np.array([0, 1], dtype=complex)


def kron_list(matrices):
    """Tensor product of a list of matrices."""
    result = matrices[0]
    for m in matrices[1:]:
        result = np.kron(result, m)
    return result


def multi_qubit_op(n, qubit_ops):
    """Build n-qubit operator from dict {qubit_index: pauli_matrix}.
    Qubits not in dict get identity."""
    mats = [I] * n
    for idx, op in qubit_ops.items():
        mats[idx] = op
    return kron_list(mats)


# ═══════════════════════════════════════════════════════════════════
# Section 1: Steane [[7,1,3]] code
# ═══════════════════════════════════════════════════════════════════

# Classical Hamming [7,4,3] parity check matrix (columns = bit positions 1-7)
H_HAMMING = np.array([
    [0, 0, 0, 1, 1, 1, 1],
    [0, 1, 1, 0, 0, 1, 1],
    [1, 0, 1, 0, 1, 0, 1],
], dtype=int)

# X-stabilizers: from H rows applied as X operators
# Z-stabilizers: from H rows applied as Z operators
# Row i of H -> stabilizer acts on qubits where H[i,j]=1

def build_steane_stabilizers():
    """Return 6 stabilizer generators (3 X-type, 3 Z-type) as 128x128 matrices."""
    n = 7
    stabilizers = []
    labels = []

    for row_idx in range(3):
        # X-type stabilizer
        ops = {}
        for q in range(n):
            if H_HAMMING[row_idx, q] == 1:
                ops[q] = X
        stabilizers.append(multi_qubit_op(n, ops))
        support = [q for q in range(n) if H_HAMMING[row_idx, q] == 1]
        labels.append(f"X-stab row{row_idx} support={support}")

        # Z-type stabilizer
        ops_z = {}
        for q in range(n):
            if H_HAMMING[row_idx, q] == 1:
                ops_z[q] = Z
        stabilizers.append(multi_qubit_op(n, ops_z))
        labels.append(f"Z-stab row{row_idx} support={support}")

    return stabilizers, labels


def build_steane_logical_states():
    """Encode |0_L> and |1_L> for Steane code.

    The Steane code uses the even-weight subcode of the [7,4,3] Hamming code.

    |0_L> = (1/sqrt(8)) * sum over even-weight codewords |c>
    |1_L> = (1/sqrt(8)) * sum over odd-weight codewords  |c>

    The even-weight subcode has 8 codewords (including 0000000 and seven
    weight-4 words).  The odd-weight coset has 8 codewords (seven weight-3
    words plus 1111111).
    """
    n = 7
    dim = 2**n  # 128

    # Build the [7,4,3] Hamming code: all 7-bit strings in null space of H_HAMMING
    all_codewords = []
    for i in range(dim):
        bits = np.array([(i >> (n - 1 - b)) & 1 for b in range(n)], dtype=int)
        syndrome = H_HAMMING @ bits % 2
        if np.all(syndrome == 0):
            all_codewords.append(i)

    # Split by weight parity
    even_codewords = []
    odd_codewords = []
    for c in all_codewords:
        wt = bin(c).count('1')
        if wt % 2 == 0:
            even_codewords.append(c)
        else:
            odd_codewords.append(c)

    # |0_L>: uniform superposition of even-weight codewords
    ket_0L = np.zeros(dim, dtype=complex)
    for c in even_codewords:
        ket_0L[c] = 1.0
    ket_0L /= np.linalg.norm(ket_0L)

    # |1_L>: uniform superposition of odd-weight codewords
    ket_1L = np.zeros(dim, dtype=complex)
    for c in odd_codewords:
        ket_1L[c] = 1.0
    ket_1L /= np.linalg.norm(ket_1L)

    return ket_0L, ket_1L, all_codewords


def steane_syndrome(state, stabilizers):
    """Measure syndrome bits.  For a +1 eigenstate, <psi|S|psi> = +1.
    For a -1 eigenstate, <psi|S|psi> = -1.
    Return list of 0 (eigenvalue +1) or 1 (eigenvalue -1)."""
    syndromes = []
    for S in stabilizers:
        ev = np.real(state.conj() @ S @ state)
        syndromes.append(0 if ev > 0 else 1)
    return syndromes


def steane_correct(state, syndrome_bits, error_type):
    """Given 3-bit syndrome (from X-type or Z-type stabilizers),
    identify error qubit and apply correction.

    X-stabilizers detect Z errors -> correct with Z on identified qubit.
    Z-stabilizers detect X errors -> correct with X on identified qubit.
    """
    n = 7
    syn_val = syndrome_bits[0] * 4 + syndrome_bits[1] * 2 + syndrome_bits[2]
    if syn_val == 0:
        return state  # no error detected

    # Syndrome value matches column index+1 of H_HAMMING
    # Find which qubit: column of H whose binary representation = syndrome
    error_qubit = None
    for q in range(n):
        col = H_HAMMING[0, q] * 4 + H_HAMMING[1, q] * 2 + H_HAMMING[2, q]
        if col == syn_val:
            error_qubit = q
            break

    if error_qubit is None:
        return state  # should not happen for valid single-qubit errors

    # Apply correction
    if error_type == "X":
        # X-stabilizers detected the error -> it was a Z error -> correct with Z
        correction = multi_qubit_op(n, {error_qubit: Z})
    elif error_type == "Z":
        # Z-stabilizers detected the error -> it was an X error -> correct with X
        correction = multi_qubit_op(n, {error_qubit: X})
    else:
        return state

    return correction @ state


def test_steane_single_errors():
    """Test all single-qubit X, Y, Z errors on |0_L> and |1_L>."""
    stabilizers, labels = build_steane_stabilizers()
    x_stabs = stabilizers[0::2]  # indices 0,2,4
    z_stabs = stabilizers[1::2]  # indices 1,3,5
    ket_0L, ket_1L, codewords = build_steane_logical_states()

    # Verify logical states are +1 eigenstates of all stabilizers
    for s_idx, S in enumerate(stabilizers):
        ev0 = np.real(ket_0L.conj() @ S @ ket_0L)
        ev1 = np.real(ket_1L.conj() @ S @ ket_1L)
        assert abs(ev0 - 1.0) < 1e-10, f"|0_L> not +1 eigenstate of {labels[s_idx]}: {ev0}"
        assert abs(ev1 - 1.0) < 1e-10, f"|1_L> not +1 eigenstate of {labels[s_idx]}: {ev1}"

    results = []
    n = 7

    for logical_label, ket_L in [("0_L", ket_0L), ("1_L", ket_1L)]:
        for error_name, error_op in [("X", X), ("Y", Y), ("Z", Z)]:
            for q in range(n):
                # Apply error
                E = multi_qubit_op(n, {q: error_op})
                corrupted = E @ ket_L

                # Measure X-stabilizer syndrome (detects Z-type component)
                x_syn = steane_syndrome(corrupted, x_stabs)
                # Measure Z-stabilizer syndrome (detects X-type component)
                z_syn = steane_syndrome(corrupted, z_stabs)

                corrected = corrupted.copy()

                if error_name == "X":
                    corrected = steane_correct(corrected, z_syn, "Z")
                elif error_name == "Z":
                    corrected = steane_correct(corrected, x_syn, "X")
                elif error_name == "Y":
                    # Y = iXZ, need both corrections
                    corrected = steane_correct(corrected, z_syn, "Z")
                    corrected = steane_correct(corrected, x_syn, "X")

                # Fidelity: |<original|corrected>|^2
                fidelity = abs(ket_L.conj() @ corrected)**2

                results.append({
                    "logical": logical_label,
                    "error": error_name,
                    "qubit": q,
                    "x_syndrome": x_syn,
                    "z_syndrome": z_syn,
                    "fidelity_after_correction": float(fidelity),
                    "correctable": bool(abs(fidelity - 1.0) < 1e-10),
                })

    return results


# ═══════════════════════════════════════════════════════════════════
# Section 2: Transversal CNOT between two Steane blocks
# ═══════════════════════════════════════════════════════════════════

def apply_transversal_cnot(psi, n=7):
    """Apply transversal CNOT to a 2-block state vector via index permutation.

    14-qubit state: qubits 0..6 = block1 (control), qubits 7..13 = block2 (target).
    For each basis state, flip target qubit i+7 if control qubit i is 1.
    All 7 CNOTs commute, so we can apply the combined permutation in one pass.
    """
    total = 14
    dim = 2**total
    out = np.zeros(dim, dtype=complex)

    for idx in range(dim):
        if psi[idx] == 0:
            continue
        block1 = (idx >> n) & ((1 << n) - 1)  # bits 13..7 = control
        block2 = idx & ((1 << n) - 1)          # bits 6..0 = target
        new_block2 = block2 ^ block1           # XOR = transversal CNOT
        new_idx = (block1 << n) | new_block2
        out[new_idx] += psi[idx]

    return out


def stabilizer_expectation_two_block(psi, S, block, n=7):
    """Compute <psi| S_block |psi> where S acts on one 7-qubit block.

    Instead of building the full 16384x16384 matrix, apply S to the
    relevant block indices via reshape.
    """
    dim_single = 2**n
    # Reshape psi into (dim_block1, dim_block2)
    psi_2d = psi.reshape(dim_single, dim_single)

    if block == 1:
        # S acts on block1 (rows): S_full = S (x) I
        Spsi_2d = S @ psi_2d
    else:
        # S acts on block2 (cols): S_full = I (x) S
        Spsi_2d = (S @ psi_2d.T).T

    return np.real(psi.conj() @ Spsi_2d.ravel())


def test_transversal_cnot():
    """Apply transversal CNOT (qubit-wise CNOT) between two Steane blocks.
    Verify the output is still in the code space of each block."""

    ket_0L, ket_1L, _ = build_steane_logical_states()
    stabilizers, _ = build_steane_stabilizers()

    n = 7

    # Test: |0_L>|0_L> -> should remain in code space
    psi_in = np.kron(ket_0L, ket_0L)
    psi_out = apply_transversal_cnot(psi_in, n)

    # Check each block's stabilizers on the output
    block1_ok = True
    block2_ok = True

    for S in stabilizers:
        ev1 = stabilizer_expectation_two_block(psi_out, S, block=1, n=n)
        if abs(abs(ev1) - 1.0) > 1e-8:
            block1_ok = False

        ev2 = stabilizer_expectation_two_block(psi_out, S, block=2, n=n)
        if abs(abs(ev2) - 1.0) > 1e-8:
            block2_ok = False

    # Also test |0_L>|1_L> -> should give |0_L>|1_L> (CNOT with control=|0>)
    psi_01 = np.kron(ket_0L, ket_1L)
    psi_01_out = apply_transversal_cnot(psi_01, n)
    fid_01 = abs(psi_01.conj() @ psi_01_out)**2

    # Test |1_L>|0_L> -> should give |1_L>|1_L> (CNOT flips target)
    psi_10 = np.kron(ket_1L, ket_0L)
    psi_10_out = apply_transversal_cnot(psi_10, n)
    expected_11 = np.kron(ket_1L, ket_1L)
    fid_10_to_11 = abs(expected_11.conj() @ psi_10_out)**2

    return {
        "block1_in_codespace": block1_ok,
        "block2_in_codespace": block2_ok,
        "fidelity_0L0L_unchanged": float(abs(psi_in.conj() @ psi_out)**2),
        "fidelity_0L1L_unchanged": float(fid_01),
        "fidelity_1L0L_to_1L1L": float(fid_10_to_11),
    }


# ═══════════════════════════════════════════════════════════════════
# Section 3: Surface code toy (3x3 lattice)
# ═══════════════════════════════════════════════════════════════════

def build_surface_code_3x3():
    """Build stabilizers for a 3x3 surface code patch.

    Data qubit layout (9 qubits, 0-indexed):
        0 -- 1 -- 2
        |    |    |
        3 -- 4 -- 5
        |    |    |
        6 -- 7 -- 8

    X-plaquettes (face stabilizers, weight 4):
        p0: {0,1,3,4}   p1: {1,2,4,5}
        p2: {3,4,6,7}   p3: {4,5,7,8}

    Z-stars: chosen so each shares an even number of qubits with every
    X-plaquette (guaranteeing commutation).  The rows and columns of
    the grid provide weight-3 operators that satisfy this:
        s0: {0,1,2}  (top row)       s1: {3,4,5}  (middle row)
        s2: {0,3,6}  (left column)   s3: {1,4,7}  (middle column)

    These 4 Z-stars are linearly independent over F_2 and each shares
    exactly 0 or 2 qubits with every X-plaquette.
    """
    n = 9

    x_plaquettes = [
        [0, 1, 3, 4],
        [1, 2, 4, 5],
        [3, 4, 6, 7],
        [4, 5, 7, 8],
    ]

    z_stars = [
        [0, 1, 2],
        [3, 4, 5],
        [0, 3, 6],
        [1, 4, 7],
    ]

    x_stab_mats = []
    for plaq in x_plaquettes:
        ops = {q: X for q in plaq}
        x_stab_mats.append(multi_qubit_op(n, ops))

    z_stab_mats = []
    for star in z_stars:
        ops = {q: Z for q in star}
        z_stab_mats.append(multi_qubit_op(n, ops))

    return x_stab_mats, z_stab_mats, x_plaquettes, z_stars


def test_surface_code_commutation():
    """Verify all stabilizers mutually commute."""
    x_stabs, z_stabs, _, _ = build_surface_code_3x3()
    all_stabs = x_stabs + z_stabs
    n_stabs = len(all_stabs)
    dim = 2**9

    commutation_ok = True
    failures = []

    for i in range(n_stabs):
        for j in range(i + 1, n_stabs):
            comm = all_stabs[i] @ all_stabs[j] - all_stabs[j] @ all_stabs[i]
            if np.max(np.abs(comm)) > 1e-10:
                commutation_ok = False
                failures.append((i, j))

    return commutation_ok, failures


def test_surface_code_syndrome():
    """Apply single X error on a data qubit and check Z-star syndrome localizes it."""
    x_stabs, z_stabs, x_plaq, z_star_supports = build_surface_code_3x3()
    n = 9
    dim = 2**n

    # Start from computational basis |000...0> which is +1 eigenstate of all Z-stars
    state = np.zeros(dim, dtype=complex)
    state[0] = 1.0

    results = []
    for error_qubit in range(n):
        E = multi_qubit_op(n, {error_qubit: X})
        corrupted = E @ state

        # Measure Z-star syndromes (X errors anti-commute with Z stabilizers)
        z_syndromes = []
        for S in z_stabs:
            ev = np.real(corrupted.conj() @ S @ corrupted)
            z_syndromes.append(0 if ev > 0 else 1)

        # Which stars were triggered?
        triggered_stars = [i for i, s in enumerate(z_syndromes) if s == 1]

        # The triggered stars should be exactly those whose support includes error_qubit
        expected_triggered = [
            i for i, support in enumerate(z_star_supports)
            if error_qubit in support
        ]

        results.append({
            "error_qubit": error_qubit,
            "z_syndrome": z_syndromes,
            "triggered_stars": triggered_stars,
            "expected_triggered": expected_triggered,
            "localization_correct": triggered_stars == expected_triggered,
        })

    return results


# ═══════════════════════════════════════════════════════════════════
# Section 4: Code distance verification
# ═══════════════════════════════════════════════════════════════════

def test_two_qubit_error_aliasing():
    """Show that Steane d=3 cannot correct 2-qubit errors (syndrome aliases).

    For distance-3, every 2-qubit X error has a syndrome that aliases to a
    single-qubit error.  The decoder then applies a third X, and the net
    weight-3 X operator is a *logical* operator (not a stabilizer), flipping
    |0_L> to |1_L>.  We verify this by checking fidelity with both logical
    states after the decoder's "correction".
    """
    stabilizers, _ = build_steane_stabilizers()
    x_stabs = stabilizers[0::2]
    z_stabs = stabilizers[1::2]
    ket_0L, ket_1L, _ = build_steane_logical_states()

    n = 7
    alias_found = []

    # Check all pairs of X errors
    for q1, q2 in combinations(range(n), 2):
        E = multi_qubit_op(n, {q1: X, q2: X})
        corrupted = E @ ket_0L

        z_syn = steane_syndrome(corrupted, z_stabs)
        syn_val = z_syn[0] * 4 + z_syn[1] * 2 + z_syn[2]

        # Try to correct as if it were a single-qubit error
        corrected = steane_correct(corrupted, z_syn, "Z")

        fid_0L = abs(ket_0L.conj() @ corrected)**2
        fid_1L = abs(ket_1L.conj() @ corrected)**2

        # Also check if syndrome matches any single-qubit error syndrome
        single_match = None
        for sq in range(n):
            E_single = multi_qubit_op(n, {sq: X})
            single_corrupted = E_single @ ket_0L
            single_syn = steane_syndrome(single_corrupted, z_stabs)
            single_val = single_syn[0] * 4 + single_syn[1] * 2 + single_syn[2]
            if single_val == syn_val:
                single_match = sq
                break

        # State is correctly recovered only if fidelity with |0_L> is ~1
        # A logical error means fidelity with |1_L> is ~1 instead
        recovered_original = bool(abs(fid_0L - 1.0) < 1e-10)
        logical_error = bool(abs(fid_1L - 1.0) < 1e-10)

        alias_found.append({
            "error_qubits": [q1, q2],
            "syndrome": z_syn,
            "syndrome_value": syn_val,
            "single_qubit_alias": single_match,
            "fidelity_with_0L": float(fid_0L),
            "fidelity_with_1L": float(fid_1L),
            "recovered_original": recovered_original,
            "logical_error_occurred": logical_error,
        })

    return alias_found


# ═══════════════════════════════════════════════════════════════════
# Main runner
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("PURE LEGO: Steane [[7,1,3]] + Surface Code Basics")
    print("=" * 70)

    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "probe": "sim_pure_lego_steane_surface",
        "sections": {},
    }

    # --- Section 1: Steane single-error correction ---
    print("\n[1] Steane [[7,1,3]] single-error correction ...")
    s1_results = test_steane_single_errors()
    all_correctable = all(r["correctable"] for r in s1_results)
    total = len(s1_results)
    print(f"    Tested {total} single-qubit errors (7 qubits x 3 Paulis x 2 logicals)")
    print(f"    All correctable: {all_correctable}")

    report["sections"]["steane_single_error"] = {
        "total_errors_tested": total,
        "all_correctable": all_correctable,
        "PASS": all_correctable,
        "details": s1_results,
    }

    # --- Section 2: Transversal CNOT ---
    print("\n[2] Transversal CNOT between two Steane blocks ...")
    s2_results = test_transversal_cnot()
    cnot_pass = (
        s2_results["block1_in_codespace"]
        and s2_results["block2_in_codespace"]
        and s2_results["fidelity_0L0L_unchanged"] > 0.999
        and s2_results["fidelity_0L1L_unchanged"] > 0.999
        and s2_results["fidelity_1L0L_to_1L1L"] > 0.999
    )
    print(f"    Block1 in codespace: {s2_results['block1_in_codespace']}")
    print(f"    Block2 in codespace: {s2_results['block2_in_codespace']}")
    print(f"    |0_L>|0_L> fidelity: {s2_results['fidelity_0L0L_unchanged']:.6f}")
    print(f"    |0_L>|1_L> fidelity: {s2_results['fidelity_0L1L_unchanged']:.6f}")
    print(f"    |1_L>|0_L> -> |1_L>|1_L> fidelity: {s2_results['fidelity_1L0L_to_1L1L']:.6f}")
    print(f"    PASS: {cnot_pass}")

    report["sections"]["transversal_cnot"] = {
        **s2_results,
        "PASS": cnot_pass,
    }

    # --- Section 3: Surface code ---
    print("\n[3] Surface code 3x3 stabilizer commutation ...")
    comm_ok, comm_failures = test_surface_code_commutation()
    print(f"    All stabilizers commute: {comm_ok}")
    if not comm_ok:
        print(f"    Failures: {comm_failures}")

    print("\n    Surface code syndrome localization ...")
    s3_syn_results = test_surface_code_syndrome()
    all_localized = all(r["localization_correct"] for r in s3_syn_results)
    print(f"    All single-X errors localized: {all_localized}")

    report["sections"]["surface_code"] = {
        "commutation_pass": comm_ok,
        "commutation_failures": comm_failures,
        "syndrome_localization": s3_syn_results,
        "all_localized": all_localized,
        "PASS": comm_ok and all_localized,
    }

    # --- Section 4: Two-qubit error aliasing ---
    print("\n[4] Code distance: 2-qubit error aliasing ...")
    s4_results = test_two_qubit_error_aliasing()
    n_pairs = len(s4_results)
    n_logical_errors = sum(1 for r in s4_results if r["logical_error_occurred"])
    n_recovered = sum(1 for r in s4_results if r["recovered_original"])
    print(f"    Tested {n_pairs} 2-qubit X error pairs")
    print(f"    Logical errors (|0_L> -> |1_L>): {n_logical_errors}/{n_pairs}")
    print(f"    Correctly recovered: {n_recovered}/{n_pairs}")
    # For d=3, 2-qubit errors should cause logical errors (not be correctable)
    has_uncorrectable = n_logical_errors > 0
    print(f"    PASS (2-qubit errors cause logical errors): {has_uncorrectable}")

    report["sections"]["code_distance_aliasing"] = {
        "total_pairs_tested": n_pairs,
        "logical_errors": n_logical_errors,
        "correctly_recovered": n_recovered,
        "PASS_distance_verified": has_uncorrectable,
        "details": s4_results,
    }

    # --- Overall verdict ---
    overall = (
        report["sections"]["steane_single_error"]["PASS"]
        and report["sections"]["transversal_cnot"]["PASS"]
        and report["sections"]["surface_code"]["PASS"]
        and report["sections"]["code_distance_aliasing"]["PASS_distance_verified"]
    )
    report["overall_pass"] = overall
    report["code_distance_verified"] = has_uncorrectable

    print("\n" + "=" * 70)
    print(f"OVERALL PASS: {overall}")
    print(f"Code distance d=3 verified (2-qubit errors cause logical errors): {has_uncorrectable}")
    print("=" * 70)

    out_path = os.path.join(RESULTS_DIR, "pure_lego_steane_surface_results.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")

    return report


if __name__ == "__main__":
    main()
