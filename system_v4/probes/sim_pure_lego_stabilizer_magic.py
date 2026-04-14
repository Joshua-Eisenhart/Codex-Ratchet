#!/usr/bin/env python3
"""
sim_pure_lego_stabilizer_magic.py
─────────────────────────────────
Pure stabilizer formalism and magic state theory.
No engine, no QIT runtime.  Only numpy.

Sections
--------
1. Single-qubit Clifford group   – 24 elements from H, S, X; closure check
2. Stabilizer states (1-qubit)   – 6 states: eigenstates of X, Y, Z
3. Stabilizer states (2-qubit)   – all 60 stabilizer states
4. Magic states                  – T-gate magic state, non-stabilizer proof
5. Stabilizer rank               – |T> decomposed as sum of 2 stabilizer states
6. Gottesman-Knill verification  – Cliffords map stabilizer states to stabilizer states
"""

import json, sys, os
import numpy as np
from itertools import product as iter_product
classification = "classical_baseline"  # auto-backfill

# ── constants ────────────────────────────────────────────────────────────────

I2 = np.eye(2, dtype=complex)
I4 = np.eye(4, dtype=complex)

# Pauli matrices
sigma_I = np.array([[1, 0], [0, 1]], dtype=complex)
sigma_X = np.array([[0, 1], [1, 0]], dtype=complex)
sigma_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
sigma_Z = np.array([[1, 0], [0, -1]], dtype=complex)

PAULIS_1Q = [sigma_I, sigma_X, sigma_Y, sigma_Z]
PAULI_LABELS_1Q = ["I", "X", "Y", "Z"]

# Standard gates
H_gate = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
S_gate = np.array([[1, 0], [0, 1j]], dtype=complex)
X_gate = sigma_X.copy()

RESULTS = {}

# ── helpers ──────────────────────────────────────────────────────────────────

def mat_eq(A, B, tol=1e-10):
    """Check if two matrices are equal up to global phase."""
    if A.shape != B.shape:
        return False
    # find first nonzero entry in A
    nz = np.abs(A) > tol
    if not np.any(nz):
        return not np.any(np.abs(B) > tol)
    idx = np.argmax(nz.ravel())
    if np.abs(B.ravel()[idx]) < tol:
        return False
    phase = A.ravel()[idx] / B.ravel()[idx]
    return np.allclose(A, phase * B, atol=tol)


def is_unitary(U, tol=1e-10):
    """Check unitarity."""
    return np.allclose(U @ U.conj().T, np.eye(U.shape[0]), atol=tol)


def state_fidelity(psi, phi):
    """Fidelity |<psi|phi>|^2 between two state vectors."""
    return float(np.abs(np.vdot(psi, phi)) ** 2)


def is_stabilizer_state_1q(psi, stab_states, tol=1e-10):
    """Check if psi is equal (up to global phase) to any 1-qubit stabilizer state."""
    for s in stab_states:
        if state_fidelity(psi, s) > 1 - tol:
            return True
    return False


def normalize(v):
    """Normalize a state vector."""
    n = np.linalg.norm(v)
    if n < 1e-15:
        return v
    return v / n


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SINGLE-QUBIT CLIFFORD GROUP: 24 ELEMENTS
# ═══════════════════════════════════════════════════════════════════════════════
print("=" * 72)
print("SECTION 1: Single-qubit Clifford group (24 elements)")
print("=" * 72)

def generate_clifford_group():
    """
    Generate all 24 single-qubit Clifford gates by composing H, S, X.
    The Clifford group on 1 qubit has exactly 24 elements (up to global phase).
    """
    generators = [H_gate, S_gate, X_gate]
    # BFS over products of generators, dedup by global-phase equivalence
    found = [sigma_I.copy()]
    queue = [sigma_I.copy()]

    while queue:
        current = queue.pop(0)
        for g in generators:
            candidate = g @ current
            # check if already in found (up to global phase)
            is_new = True
            for f in found:
                if mat_eq(candidate, f):
                    is_new = False
                    break
            if is_new:
                found.append(candidate)
                queue.append(candidate)
                if len(found) >= 30:
                    # safety: should converge at 24
                    break

    return found

clifford_group = generate_clifford_group()
n_cliffords = len(clifford_group)
print(f"  Generated {n_cliffords} Clifford elements (expected 24)")

# Verify all are unitary
all_unitary = all(is_unitary(C) for C in clifford_group)
print(f"  All unitary: {all_unitary}")

# Verify closure: product of any two Cliffords is a Clifford
closure_ok = True
closure_failures = 0
for i, A in enumerate(clifford_group):
    for j, B in enumerate(clifford_group):
        prod = A @ B
        found_in_group = any(mat_eq(prod, C) for C in clifford_group)
        if not found_in_group:
            closure_ok = False
            closure_failures += 1

print(f"  Group closure: {closure_ok} (failures: {closure_failures})")

# Verify: conjugation maps Paulis to Paulis (up to sign)
pauli_conj_ok = True
pauli_conj_failures = 0
non_identity_paulis = [sigma_X, sigma_Y, sigma_Z]
signed_paulis = []
for P in non_identity_paulis:
    signed_paulis.append(P)
    signed_paulis.append(-P)

for C in clifford_group:
    for P in non_identity_paulis:
        conjugated = C @ P @ C.conj().T
        # Must be +/- another non-identity Pauli
        found_match = any(mat_eq(conjugated, sP) for sP in signed_paulis)
        if not found_match:
            pauli_conj_ok = False
            pauli_conj_failures += 1

print(f"  Maps Pauli->Pauli under conjugation: {pauli_conj_ok} (failures: {pauli_conj_failures})")

RESULTS["section_1_clifford_group"] = {
    "num_elements": n_cliffords,
    "expected": 24,
    "all_unitary": all_unitary,
    "group_closure": closure_ok,
    "closure_failures": closure_failures,
    "pauli_conjugation_preserving": pauli_conj_ok,
    "pauli_conj_failures": pauli_conj_failures,
    "pass": n_cliffords == 24 and all_unitary and closure_ok and pauli_conj_ok
}


# ═══════════════════════════════════════════════════════════════════════════════
# 2. STABILIZER STATES (1-QUBIT): 6 STATES
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 2: Stabilizer states (1-qubit) — 6 states")
print("=" * 72)

# +1 eigenstates of Pauli operators (and their negatives)
ket0 = np.array([1, 0], dtype=complex)
ket1 = np.array([0, 1], dtype=complex)
ket_plus  = normalize(ket0 + ket1)   # +1 eigenstate of X
ket_minus = normalize(ket0 - ket1)   # -1 eigenstate of X
ket_plus_i  = normalize(ket0 + 1j * ket1)   # +1 eigenstate of Y
ket_minus_i = normalize(ket0 - 1j * ket1)   # -1 eigenstate of Y

stab_states_1q = [ket0, ket1, ket_plus, ket_minus, ket_plus_i, ket_minus_i]
stab_labels_1q = ["|0>", "|1>", "|+>", "|->", "|+i>", "|-i>"]

# Verify each is a +1 eigenstate of some Pauli
eigenstate_checks = {}
pauli_assignments = {
    "|0>": ("Z", sigma_Z, +1),
    "|1>": ("Z", sigma_Z, -1),
    "|+>": ("X", sigma_X, +1),
    "|->": ("X", sigma_X, -1),
    "|+i>": ("Y", sigma_Y, +1),
    "|-i>": ("Y", sigma_Y, -1),
}

all_eigen_ok = True
for label, state in zip(stab_labels_1q, stab_states_1q):
    pauli_name, pauli_mat, expected_sign = pauli_assignments[label]
    result_vec = pauli_mat @ state
    actual_eigenval = np.vdot(state, result_vec).real
    ok = np.isclose(actual_eigenval, expected_sign, atol=1e-10)
    eigenstate_checks[label] = {
        "pauli": pauli_name,
        "expected_eigenvalue": expected_sign,
        "actual_eigenvalue": float(round(actual_eigenval, 10)),
        "pass": bool(ok)
    }
    if not ok:
        all_eigen_ok = False
    print(f"  {label}: eigenvalue {actual_eigenval:+.1f} of {pauli_name} — {'PASS' if ok else 'FAIL'}")

# Verify they are all distinct (no two have fidelity 1)
distinct_ok = True
for i in range(len(stab_states_1q)):
    for j in range(i + 1, len(stab_states_1q)):
        fid = state_fidelity(stab_states_1q[i], stab_states_1q[j])
        if fid > 1 - 1e-10:
            distinct_ok = False

print(f"  All 6 states distinct: {distinct_ok}")
print(f"  All eigenstate checks: {all_eigen_ok}")

RESULTS["section_2_stabilizer_states_1q"] = {
    "num_states": len(stab_states_1q),
    "expected": 6,
    "eigenstate_checks": eigenstate_checks,
    "all_distinct": distinct_ok,
    "all_eigenstate_ok": all_eigen_ok,
    "pass": len(stab_states_1q) == 6 and distinct_ok and all_eigen_ok
}


# ═══════════════════════════════════════════════════════════════════════════════
# 3. STABILIZER STATES (2-QUBIT): 60 STATES
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 3: Stabilizer states (2-qubit) — 60 states")
print("=" * 72)

# 2-qubit Pauli group (without phases): I,X,Y,Z tensor I,X,Y,Z = 16 elements
# With signs +/-, that's 32 signed Paulis (ignoring +/-i phases for stabilizer subgroups)
paulis_2q = []
pauli_2q_labels = []
for i, (li, Pi) in enumerate(zip(PAULI_LABELS_1Q, PAULIS_1Q)):
    for j, (lj, Pj) in enumerate(zip(PAULI_LABELS_1Q, PAULIS_1Q)):
        paulis_2q.append(np.kron(Pi, Pj))
        pauli_2q_labels.append(f"{li}{lj}")

def find_2q_stabilizer_states():
    """
    A 2-qubit stabilizer state is the unique +1 eigenstate of an abelian
    subgroup of the 2-qubit Pauli group (with signs) having 4 elements,
    generated by 2 independent commuting signed Paulis.

    The signed 2-qubit Pauli group has elements {+/- P_a x P_b} for
    P in {I, X, Y, Z}.  We enumerate by applying all 24x24 = 576
    2-qubit Clifford unitaries (tensor products of single-qubit Cliffords)
    to the 4 computational basis states, then also include entangled
    stabilizer states from CNOT-like constructions.

    Alternatively, we directly enumerate: for every pair of commuting,
    independent signed Paulis (signs +/-), find the joint +1 eigenspace.
    """
    states = []

    # Build the signed non-identity Pauli set: +P and -P for each non-II Pauli
    signed_paulis_2q = []
    signed_labels_2q = []
    for k in range(1, 16):  # skip II
        signed_paulis_2q.append(paulis_2q[k])
        signed_labels_2q.append("+" + pauli_2q_labels[k])
        signed_paulis_2q.append(-paulis_2q[k])
        signed_labels_2q.append("-" + pauli_2q_labels[k])

    n_signed = len(signed_paulis_2q)

    for idx_a in range(n_signed):
        Pa = signed_paulis_2q[idx_a]
        for idx_b in range(idx_a + 1, n_signed):
            Pb = signed_paulis_2q[idx_b]
            # Check commutation: [Pa, Pb] = 0
            comm = Pa @ Pb - Pb @ Pa
            if np.linalg.norm(comm) > 1e-10:
                continue
            # Check independence: Pb != +/- Pa (as matrices)
            if np.allclose(Pa, Pb, atol=1e-10) or np.allclose(Pa, -Pb, atol=1e-10):
                continue
            # Both must square to I4
            if not np.allclose(Pa @ Pa, I4, atol=1e-10):
                continue
            if not np.allclose(Pb @ Pb, I4, atol=1e-10):
                continue
            # Find joint +1 eigenspace (should be 1-dimensional for a maximal stabilizer)
            eigvals_a, eigvecs_a = np.linalg.eigh(Pa)
            plus1_a = eigvecs_a[:, np.abs(eigvals_a - 1) < 1e-10]
            if plus1_a.shape[1] == 0:
                continue
            Pb_proj = plus1_a.conj().T @ Pb @ plus1_a
            eigvals_b, eigvecs_b = np.linalg.eigh(Pb_proj)
            plus1_b = eigvecs_b[:, np.abs(eigvals_b - 1) < 1e-10]
            if plus1_b.shape[1] == 0:
                continue
            for col in range(plus1_b.shape[1]):
                psi = plus1_a @ plus1_b[:, col]
                psi = normalize(psi)
                # Check uniqueness (up to global phase)
                is_new = True
                for existing in states:
                    if state_fidelity(psi, existing) > 1 - 1e-10:
                        is_new = False
                        break
                if is_new:
                    states.append(psi)

    return states

stab_states_2q = find_2q_stabilizer_states()
n_stab_2q = len(stab_states_2q)
print(f"  Found {n_stab_2q} stabilizer states (expected 60)")

# Verify all are valid quantum states (norm 1)
all_normalized = all(np.isclose(np.linalg.norm(s), 1.0, atol=1e-10) for s in stab_states_2q)
print(f"  All normalized: {all_normalized}")

# Verify each is +1 eigenstate of at least one non-identity signed 2q Pauli
all_stabilized = True
for psi in stab_states_2q:
    has_stabilizer = False
    for k in range(1, 16):
        for sign in [+1, -1]:
            Pk = sign * paulis_2q[k]
            result = Pk @ psi
            if np.abs(np.vdot(psi, result) - 1.0) < 1e-10:
                has_stabilizer = True
                break
        if has_stabilizer:
            break
    if not has_stabilizer:
        all_stabilized = False

print(f"  All have a non-trivial stabilizer: {all_stabilized}")

RESULTS["section_3_stabilizer_states_2q"] = {
    "num_states": n_stab_2q,
    "expected": 60,
    "all_normalized": all_normalized,
    "all_have_stabilizer": all_stabilized,
    "pass": n_stab_2q == 60 and all_normalized and all_stabilized
}


# ═══════════════════════════════════════════════════════════════════════════════
# 4. MAGIC STATES
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 4: Magic states — T-gate state")
print("=" * 72)

# T gate = diag(1, e^{i pi/4})
T_gate = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)

# |T> = T|+> = cos(pi/8)|0> + e^{i pi/4} sin(pi/8)|1>
# Actually the standard magic state: |T> = cos(pi/8)|0> + sin(pi/8)|1>
# (the state on the Bloch sphere at the "magic angle")
ket_T = np.array([np.cos(np.pi / 8), np.sin(np.pi / 8)], dtype=complex)
ket_T = normalize(ket_T)

# Alternative: T|+>
ket_T_alt = T_gate @ ket_plus
ket_T_alt = normalize(ket_T_alt)

print(f"  |T> = cos(pi/8)|0> + sin(pi/8)|1>")
print(f"  |T> components: [{ket_T[0]:.6f}, {ket_T[1]:.6f}]")

# Check: is |T> a stabilizer state?
T_is_stabilizer = is_stabilizer_state_1q(ket_T, stab_states_1q)
print(f"  |T> is stabilizer state: {T_is_stabilizer} (expected False)")

T_alt_is_stabilizer = is_stabilizer_state_1q(ket_T_alt, stab_states_1q)
print(f"  T|+> is stabilizer state: {T_alt_is_stabilizer} (expected False)")

# Verify T gate is NOT a Clifford
T_is_clifford = any(mat_eq(T_gate, C) for C in clifford_group)
print(f"  T gate is Clifford: {T_is_clifford} (expected False)")

# Check Bloch sphere position of |T>
# For |psi> = cos(theta/2)|0> + e^{i phi} sin(theta/2)|1>
# theta = pi/4, phi = 0 => Bloch vector = (sin(pi/4), 0, cos(pi/4))
bloch_x = 2 * (ket_T[0].conj() * ket_T[1]).real
bloch_y = 2 * (ket_T[0].conj() * ket_T[1]).imag
bloch_z = float(np.abs(ket_T[0])**2 - np.abs(ket_T[1])**2)
bloch_r = np.sqrt(bloch_x**2 + bloch_y**2 + bloch_z**2)
print(f"  Bloch vector: ({bloch_x:.6f}, {bloch_y:.6f}, {bloch_z:.6f}), |r|={bloch_r:.6f}")

# Magic states are NOT on any Pauli axis (not at +-x, +-y, +-z)
on_axis = (
    np.isclose(abs(bloch_x), 1, atol=1e-10) or
    np.isclose(abs(bloch_y), 1, atol=1e-10) or
    np.isclose(abs(bloch_z), 1, atol=1e-10)
)
print(f"  On Pauli axis (stabilizer): {on_axis} (expected False)")

RESULTS["section_4_magic_states"] = {
    "T_state_components": [float(ket_T[0].real), float(ket_T[1].real)],
    "T_is_stabilizer": T_is_stabilizer,
    "T_alt_is_stabilizer": T_alt_is_stabilizer,
    "T_gate_is_clifford": T_is_clifford,
    "bloch_vector": [float(bloch_x), float(bloch_y), float(bloch_z)],
    "bloch_radius": float(bloch_r),
    "on_pauli_axis": on_axis,
    "pass": (not T_is_stabilizer) and (not T_alt_is_stabilizer) and (not T_is_clifford) and (not on_axis)
}


# ═══════════════════════════════════════════════════════════════════════════════
# 5. STABILIZER RANK
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 5: Stabilizer rank — |T> has rank 2")
print("=" * 72)

# Stabilizer rank: minimum k such that |T> = sum_{i=1}^{k} c_i |s_i>
# where |s_i> are stabilizer states.
#
# |T> = cos(pi/8)|0> + sin(pi/8)|1>
# Since |0> and |1> are stabilizer states, rank <= 2.
# We need to show rank != 1 (i.e., |T> is not itself a stabilizer state).

# Decomposition: |T> = cos(pi/8)|0> + sin(pi/8)|1>
c0 = np.cos(np.pi / 8)
c1 = np.sin(np.pi / 8)
decomp_check = np.allclose(ket_T, c0 * ket0 + c1 * ket1, atol=1e-10)
print(f"  |T> = cos(pi/8)|0> + sin(pi/8)|1>: {decomp_check}")

# Rank is NOT 1 because |T> is not a stabilizer state
rank_not_1 = not is_stabilizer_state_1q(ket_T, stab_states_1q)
print(f"  Rank != 1 (not a stabilizer state): {rank_not_1}")

# Verify decomposition uses exactly 2 stabilizer states
# Try all pairs of stabilizer states and check if |T> is in their span
rank_2_found = False
best_pair = None
for i in range(len(stab_states_1q)):
    for j in range(i + 1, len(stab_states_1q)):
        s1 = stab_states_1q[i]
        s2 = stab_states_1q[j]
        # Solve c1*s1 + c2*s2 = ket_T via least squares
        A_mat = np.column_stack([s1, s2])
        coeffs, residual, _, _ = np.linalg.lstsq(A_mat, ket_T, rcond=None)
        recon = coeffs[0] * s1 + coeffs[1] * s2
        if np.allclose(recon, ket_T, atol=1e-10):
            rank_2_found = True
            best_pair = (stab_labels_1q[i], stab_labels_1q[j],
                         complex(coeffs[0]), complex(coeffs[1]))
            break
    if rank_2_found:
        break

if best_pair:
    print(f"  Rank-2 decomposition found: {best_pair[2]:.6f}*{best_pair[0]} + {best_pair[3]:.6f}*{best_pair[1]}")
else:
    print("  WARNING: No rank-2 decomposition found among labeled stabilizer states")

# The explicit decomposition via |0>, |1> always works
explicit_rank_2 = True
stabilizer_rank = 2
print(f"  Stabilizer rank of |T>: {stabilizer_rank}")

RESULTS["section_5_stabilizer_rank"] = {
    "decomposition_check": decomp_check,
    "rank_not_1": rank_not_1,
    "rank_2_found": rank_2_found,
    "pair": [best_pair[0], best_pair[1]] if best_pair else ["|0>", "|1>"],
    "coefficients": [str(best_pair[2]), str(best_pair[3])] if best_pair else [str(c0), str(c1)],
    "stabilizer_rank": stabilizer_rank,
    "pass": decomp_check and rank_not_1 and stabilizer_rank == 2
}


# ═══════════════════════════════════════════════════════════════════════════════
# 6. GOTTESMAN-KNILL VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 6: Gottesman-Knill — Cliffords preserve stabilizer states")
print("=" * 72)

# Core theorem: Clifford circuits on stabilizer inputs produce stabilizer outputs.
# For 1 qubit: apply each of 24 Cliffords to each of 6 stabilizer states.
# All 144 outputs must be stabilizer states.

gk_total = 0
gk_pass = 0
gk_fail = 0
gk_failures = []

for ci, C in enumerate(clifford_group):
    for si, s in enumerate(stab_states_1q):
        output = normalize(C @ s)
        gk_total += 1
        if is_stabilizer_state_1q(output, stab_states_1q):
            gk_pass += 1
        else:
            gk_fail += 1
            gk_failures.append({"clifford_idx": ci, "state_idx": si})

print(f"  Total tests: {gk_total}")
print(f"  Passed: {gk_pass}")
print(f"  Failed: {gk_fail}")
gk_ok = gk_fail == 0
print(f"  Gottesman-Knill verified: {gk_ok}")

# Additional check: applying T gate to a stabilizer state produces a NON-stabilizer state
# (except for |0> and |1> which are eigenstates of T up to phase)
t_gate_violations = 0
t_gate_non_stab = 0
for si, s in enumerate(stab_states_1q):
    output = normalize(T_gate @ s)
    if not is_stabilizer_state_1q(output, stab_states_1q):
        t_gate_non_stab += 1

print(f"  T-gate produces non-stabilizer states: {t_gate_non_stab}/6 cases")
# |0> -> |0> (eigenstate), |1> -> e^{i pi/4}|1> (same state up to phase)
# |+> -> magic state, etc.
# Expect at least 2 non-stabilizer outputs
t_gate_magic_ok = t_gate_non_stab >= 2
print(f"  T-gate breaks stabilizer for some inputs: {t_gate_magic_ok}")

RESULTS["section_6_gottesman_knill"] = {
    "total_tests": gk_total,
    "passed": gk_pass,
    "failed": gk_fail,
    "gottesman_knill_verified": gk_ok,
    "t_gate_non_stabilizer_outputs": t_gate_non_stab,
    "t_gate_breaks_stabilizer": t_gate_magic_ok,
    "pass": gk_ok and t_gate_magic_ok
}


# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SUMMARY")
print("=" * 72)

all_pass = True
for section, data in RESULTS.items():
    status = "PASS" if data["pass"] else "FAIL"
    if not data["pass"]:
        all_pass = False
    print(f"  {section}: {status}")

RESULTS["overall_pass"] = all_pass
print(f"\n  OVERALL: {'PASS' if all_pass else 'FAIL'}")

# ── write results ────────────────────────────────────────────────────────────
out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "pure_lego_stabilizer_magic_results.json")

with open(out_path, "w") as f:
    json.dump(RESULTS, f, indent=2, default=str)

print(f"\n  Results written to {out_path}")
