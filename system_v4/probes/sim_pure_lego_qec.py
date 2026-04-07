#!/usr/bin/env python3
"""
Pure-lego QEC: 3-qubit bit-flip code.
numpy only. 8x8 (3-qubit) simulation.

Encode:  |0> -> |000>,  |1> -> |111>
Error:   single bit-flip X on qubit 1
Syndrome: Z x Z x I  and  I x Z x Z
Correct:  apply X on identified qubit
Verify:  fidelity = 1 after correction
Verify:  Knill-Laflamme conditions for {I, X1, X2, X3}
Verify:  2-qubit error is NOT correctable (distance=1)
"""

import json
import sys
import numpy as np
from pathlib import Path

# ── Pauli matrices ──────────────────────────────────────────────────────────
I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)

# ── Basis states ────────────────────────────────────────────────────────────
ket0 = np.array([1, 0], dtype=complex)
ket1 = np.array([0, 1], dtype=complex)


def kron3(a, b, c):
    """Tensor product of three 2x2 matrices -> 8x8."""
    return np.kron(np.kron(a, b), c)


def ket3(*bits):
    """Computational basis ket for 3 qubits, e.g. ket3(0,1,0) = |010>."""
    bases = [ket0 if b == 0 else ket1 for b in bits]
    return np.kron(np.kron(bases[0], bases[1]), bases[2])


# ── Encoding ────────────────────────────────────────────────────────────────
# Logical |0_L> = |000>,  |1_L> = |111>
ket_0L = ket3(0, 0, 0)
ket_1L = ket3(1, 1, 1)

# Code-space projector  P_C = |0_L><0_L| + |1_L><1_L|
P_C = np.outer(ket_0L, ket_0L) + np.outer(ket_1L, ket_1L)

# ── Error operators ────────────────────────────────────────────────────────
I8 = np.eye(8, dtype=complex)
X1 = kron3(X, I2, I2)   # bit-flip on qubit 1
X2 = kron3(I2, X, I2)   # bit-flip on qubit 2
X3 = kron3(I2, I2, X)   # bit-flip on qubit 3

correctable_errors = {"I": I8, "X1": X1, "X2": X2, "X3": X3}

# ── Syndrome operators ─────────────────────────────────────────────────────
S1 = kron3(Z, Z, I2)    # Z x Z x I
S2 = kron3(I2, Z, Z)    # I x Z x Z

# Syndrome table: (s1, s2) -> error location
#   (0,0) = no error
#   (1,0) = error on qubit 1  (ZZ I sees flip on q1, I ZZ does not)
#   (1,1) = error on qubit 2  (both stabilisers detect)
#   (0,1) = error on qubit 3  (ZZ I does not see, I ZZ does)
# Eigenvalue +1 -> syndrome bit 0,  eigenvalue -1 -> syndrome bit 1
syndrome_correction = {
    (0, 0): None,
    (1, 0): X1,
    (1, 1): X2,
    (0, 1): X3,
}


def measure_syndrome(state):
    """
    Measure syndrome bits for stabilisers S1, S2.
    Returns tuple of (s1, s2) where 0 = +1 eigenvalue, 1 = -1 eigenvalue.
    """
    s1 = int(np.real(state.conj() @ S1 @ state))
    s2 = int(np.real(state.conj() @ S2 @ state))
    # eigenvalue +1 -> bit 0, eigenvalue -1 -> bit 1
    b1 = 0 if s1 == 1 else 1
    b2 = 0 if s2 == 1 else 1
    return (b1, b2)


def fidelity(psi, phi):
    """State fidelity |<psi|phi>|^2."""
    return float(np.abs(np.vdot(psi, phi)) ** 2)


# ══════════════════════════════════════════════════════════════════════════
# TEST 1: Encode, error, syndrome, correct, verify
# ══════════════════════════════════════════════════════════════════════════
results = {"test_1_encode_error_correct": {}, "test_2_knill_laflamme": {},
           "test_3_two_qubit_error_uncorrectable": {}}

print("=" * 60)
print("TEST 1: Encode -> Error -> Syndrome -> Correct -> Verify")
print("=" * 60)

# Encode |0> -> |000>
encoded = ket_0L.copy()
print(f"Encoded state |0_L> = |000>: {encoded}")

# Apply single bit-flip on qubit 1: X x I x I
errored = X1 @ encoded
print(f"After X on qubit 1:          {errored}")
print(f"  (should be |100> = {ket3(1,0,0)})")

# Measure syndrome
syn = measure_syndrome(errored)
print(f"Syndrome (s1, s2) = {syn}  (expect (1, 0) for qubit-1 error)")

# Correct
correction = syndrome_correction[syn]
corrected = correction @ errored if correction is not None else errored
f_val = fidelity(corrected, encoded)
print(f"After correction:            {corrected}")
print(f"Fidelity with original:      {f_val}")

t1_pass = np.isclose(f_val, 1.0)
print(f"TEST 1 PASS: {t1_pass}")

results["test_1_encode_error_correct"] = {
    "encoded_state": encoded.tolist(),
    "error_applied": "X1 (X x I x I)",
    "errored_state": errored.tolist(),
    "syndrome": list(syn),
    "corrected_state": corrected.tolist(),
    "fidelity": f_val,
    "pass": bool(t1_pass),
}

# Also test all single-qubit errors and |1_L>
print("\n--- All single-qubit errors on both logical states ---")
all_single_pass = True
single_details = []
for label, state_name, state in [("0L", "|000>", ket_0L), ("1L", "|111>", ket_1L)]:
    for err_name, err_op in correctable_errors.items():
        errored_s = err_op @ state
        syn_s = measure_syndrome(errored_s)
        corr_op = syndrome_correction[syn_s]
        corrected_s = corr_op @ errored_s if corr_op is not None else errored_s
        f_s = fidelity(corrected_s, state)
        ok = np.isclose(f_s, 1.0)
        all_single_pass = all_single_pass and ok
        detail = f"  {label} + {err_name}: syndrome={syn_s}, fidelity={f_s:.6f}, pass={ok}"
        print(detail)
        single_details.append({
            "logical": label, "error": err_name,
            "syndrome": list(syn_s), "fidelity": f_s, "pass": bool(ok)
        })

results["test_1_encode_error_correct"]["all_single_errors"] = single_details
results["test_1_encode_error_correct"]["all_single_pass"] = bool(all_single_pass)

# ══════════════════════════════════════════════════════════════════════════
# TEST 2: Knill-Laflamme conditions
#   P_C  E_a^dag  E_b  P_C  =  alpha_{ab}  P_C
#   for all pairs (a, b) in {I, X1, X2, X3}
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("TEST 2: Knill-Laflamme conditions")
print("=" * 60)

error_list = list(correctable_errors.items())
n_errors = len(error_list)
alpha = np.zeros((n_errors, n_errors), dtype=complex)
kl_pass = True
kl_details = []

for i, (name_a, E_a) in enumerate(error_list):
    for j, (name_b, E_b) in enumerate(error_list):
        # P_C  E_a^dag  E_b  P_C
        lhs = P_C @ E_a.conj().T @ E_b @ P_C

        # Check if lhs = alpha_{ab} * P_C
        # alpha_{ab} = Tr(P_C E_a^dag E_b P_C) / Tr(P_C)
        # Since P_C has rank 2, Tr(P_C) = 2
        alpha_ab = np.trace(lhs) / np.trace(P_C)
        alpha[i, j] = alpha_ab

        residual = lhs - alpha_ab * P_C
        res_norm = float(np.linalg.norm(residual))
        ok = res_norm < 1e-12
        kl_pass = kl_pass and ok

        print(f"  ({name_a}, {name_b}): alpha={alpha_ab:.4f}, "
              f"residual_norm={res_norm:.2e}, pass={ok}")
        kl_details.append({
            "E_a": name_a, "E_b": name_b,
            "alpha_ab": complex(alpha_ab).real,
            "residual_norm": res_norm, "pass": bool(ok)
        })

print(f"\nalpha matrix (should be diagonal for correctable error set):")
print(np.real(alpha))
print(f"\nTEST 2 PASS: {kl_pass}")

# Verify alpha is identity (since X_i are unitary and orthogonal on code space)
alpha_is_identity = np.allclose(np.real(alpha), np.eye(n_errors))
print(f"alpha = I_{n_errors}: {alpha_is_identity}")

results["test_2_knill_laflamme"] = {
    "alpha_matrix": np.real(alpha).tolist(),
    "alpha_is_identity": bool(alpha_is_identity),
    "details": kl_details,
    "pass": bool(kl_pass),
}

# ══════════════════════════════════════════════════════════════════════════
# TEST 3: 2-qubit error is NOT correctable (distance = 1 for 2-bit errors)
#   The code has distance 3, so it corrects t=1 errors.
#   A 2-qubit bit-flip should NOT be correctable.
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("TEST 3: 2-qubit error is NOT correctable")
print("=" * 60)

X12 = kron3(X, X, I2)   # bit-flip on qubits 1 and 2

two_qubit_details = []
two_qubit_uncorrectable = True

for label, state_name, state in [("0L", "|000>", ket_0L), ("1L", "|111>", ket_1L)]:
    errored_2 = X12 @ state
    syn_2 = measure_syndrome(errored_2)
    corr_2 = syndrome_correction[syn_2]
    corrected_2 = corr_2 @ errored_2 if corr_2 is not None else errored_2
    f_2 = fidelity(corrected_2, state)
    # Should NOT be 1.0
    not_corrected = not np.isclose(f_2, 1.0)
    two_qubit_uncorrectable = two_qubit_uncorrectable and not_corrected

    print(f"  {label} + X12: syndrome={syn_2}, "
          f"fidelity_after_correction={f_2:.6f}, "
          f"uncorrectable={not_corrected}")
    two_qubit_details.append({
        "logical": label, "error": "X1X2",
        "syndrome": list(syn_2), "fidelity_after_correction": f_2,
        "uncorrectable": bool(not_corrected)
    })

# Also verify Knill-Laflamme fails when 2-qubit errors are included
extended_errors = {**correctable_errors, "X12": X12}
ext_list = list(extended_errors.items())
kl_extended_pass = True
kl_fail_pairs = []

for i, (na, Ea) in enumerate(ext_list):
    for j, (nb, Eb) in enumerate(ext_list):
        lhs = P_C @ Ea.conj().T @ Eb @ P_C
        a_ab = np.trace(lhs) / np.trace(P_C)
        residual = lhs - a_ab * P_C
        res_n = float(np.linalg.norm(residual))
        if res_n > 1e-12:
            kl_extended_pass = False
            kl_fail_pairs.append({"E_a": na, "E_b": nb, "residual_norm": res_n})

print(f"\n  Knill-Laflamme with {{I, X1, X2, X3, X12}} holds: {kl_extended_pass}")
print(f"  Failing pairs: {len(kl_fail_pairs)}")
for fp in kl_fail_pairs:
    print(f"    ({fp['E_a']}, {fp['E_b']}): residual={fp['residual_norm']:.2e}")

t3_pass = two_qubit_uncorrectable and not kl_extended_pass
print(f"\nTEST 3 PASS: {t3_pass}")

results["test_3_two_qubit_error_uncorrectable"] = {
    "details": two_qubit_details,
    "two_qubit_uncorrectable": bool(two_qubit_uncorrectable),
    "knill_laflamme_extended_holds": bool(kl_extended_pass),
    "knill_laflamme_fail_pairs": kl_fail_pairs,
    "pass": bool(t3_pass),
}

# ── Summary ─────────────────────────────────────────────────────────────
all_pass = t1_pass and all_single_pass and kl_pass and t3_pass

results["summary"] = {
    "test_1_pass": bool(t1_pass),
    "test_1_all_single_pass": bool(all_single_pass),
    "test_2_knill_laflamme_pass": bool(kl_pass),
    "test_3_two_qubit_uncorrectable_pass": bool(t3_pass),
    "all_pass": bool(all_pass),
    "code_parameters": {"n": 3, "k": 1, "d": 3, "t": 1},
    "hilbert_space_dim": 8,
}

print("\n" + "=" * 60)
print(f"ALL TESTS PASS: {all_pass}")
print("=" * 60)

# ── Write results ───────────────────────────────────────────────────────
out_path = Path(__file__).parent / "a2_state" / "sim_results" / "pure_lego_qec_results.json"
out_path.parent.mkdir(parents=True, exist_ok=True)

# Convert any remaining numpy types for JSON serialization
def sanitize(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, complex):
        return {"re": obj.real, "im": obj.imag}
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    return obj

with open(out_path, "w") as f:
    json.dump(sanitize(results), f, indent=2)

print(f"\nResults written to {out_path}")

sys.exit(0 if all_pass else 1)
