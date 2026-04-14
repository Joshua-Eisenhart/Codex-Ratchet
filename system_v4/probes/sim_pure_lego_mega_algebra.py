#!/usr/bin/env python3
"""
sim_pure_lego_mega_algebra.py
─────────────────────────────
MEGA lego: 8 algebraic structures verified in a single loop.
No engine, no QIT runtime.  Only numpy + scipy.

Structures
----------
1. Pauli group P_1          – 16 elements, closure, squares, center
2. Pauli group P_2          – 64 elements on 2 qubits, closure, size formula
3. Clifford hierarchy       – L1=Pauli, L2=Clifford, L3 includes T not L2
4. Jordan algebra J_2(C)    – commutative, power-associative, Jordan identity
5. Lie vs Jordan split      – AB = [A,B]/2 + A∘B verified
6. U(su(2)) enveloping      – PBW basis, Casimir commutes with all generators
7. Tensor product su(2)⊗su(2) – 6 generators, so(4) dimension
8. Schur-Weyl duality       – sym/antisym projectors commute with U⊗U and SWAP
"""

import json, sys, os, itertools
import numpy as np
from scipy.linalg import expm
classification = "classical_baseline"  # auto-backfill

# ── globals ───────────────────────────────────────────────────────────────────

RESULTS = {}

# ── Pauli matrices (complex128) ───────────────────────────────────────────────

I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)

PAULIS = [I2, sx, sy, sz]

# ── helpers ───────────────────────────────────────────────────────────────────

def mat_eq(A, B, tol=1e-10):
    """Check matrix equality up to tolerance."""
    return np.allclose(A, B, atol=tol)

def mat_in_list(M, mlist, tol=1e-10):
    """Check if matrix M is in list (up to tolerance)."""
    for X in mlist:
        if mat_eq(M, X, tol):
            return True
    return False

def mat_index(M, mlist, tol=1e-10):
    """Return index of M in list, or -1."""
    for i, X in enumerate(mlist):
        if mat_eq(M, X, tol):
            return i
    return -1

def commutator(A, B):
    return A @ B - B @ A

def anticommutator(A, B):
    return A @ B + B @ A

def jordan(A, B):
    return (A @ B + B @ A) / 2

def lie(A, B):
    return A @ B - B @ A

# ═══════════════════════════════════════════════════════════════════════════════
# 1. PAULI GROUP P_1 — 16 elements
# ═══════════════════════════════════════════════════════════════════════════════
print("=" * 72)
print("SECTION 1: Pauli group P_1 (16 elements)")
print("=" * 72)

# Generate all 16 elements: {±1, ±i} × {I, σx, σy, σz}
phases = [1, -1, 1j, -1j]
P1 = []
P1_labels = []
for ph in phases:
    for j, P in enumerate(PAULIS):
        P1.append(ph * P)
        names = ["I", "X", "Y", "Z"]
        P1_labels.append(f"({ph:+g})*{names[j]}")

assert len(P1) == 16, f"Expected 16 elements, got {len(P1)}"

# Verify closure: product of any two elements is in the group
closure_ok = True
for a in P1:
    for b in P1:
        prod = a @ b
        if not mat_in_list(prod, P1):
            closure_ok = False
            break
    if not closure_ok:
        break

# Every element squares to ±I
squares_ok = True
for g in P1:
    g2 = g @ g
    if not (mat_eq(g2, I2) or mat_eq(g2, -I2)):
        squares_ok = False
        break

# Center = {±I, ±iI}
center_elements = [I2, -I2, 1j * I2, -1j * I2]
center = []
for g in P1:
    is_central = True
    for h in P1:
        if not mat_eq(g @ h, h @ g):
            is_central = False
            break
    if is_central:
        center.append(g)

center_ok = len(center) == 4
for c in center_elements:
    if not mat_in_list(c, center):
        center_ok = False
        break

all_pass_1 = closure_ok and squares_ok and center_ok
RESULTS["s1_pauli_P1"] = {
    "size": 16,
    "closure": closure_ok,
    "squares_to_pm_I": squares_ok,
    "center_size": len(center),
    "center_correct": center_ok,
    "all_pass": all_pass_1,
}
print(f"  Closure:    {closure_ok}")
print(f"  Squares:    {squares_ok}")
print(f"  Center:     {center_ok} (size={len(center)})")
print(f"  ALL PASS:   {all_pass_1}")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. PAULI GROUP P_2 — 64 elements on 2 qubits
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 2: Pauli group P_2 (64 elements, 2 qubits)")
print("=" * 72)

# P_2 = {phase * (σ_a ⊗ σ_b)} for phase in {±1, ±i}, a,b in {I,X,Y,Z}
P2 = []
for ph in phases:
    for a in PAULIS:
        for b in PAULIS:
            P2.append(ph * np.kron(a, b))

assert len(P2) == 64, f"Expected 64, got {len(P2)}"

# Size formula: |P_n| = 4^(n+1)
size_formula_ok = len(P2) == 4 ** (2 + 1)  # n=2 -> 4^3=64  ... wait
# Actually 4^(n+1) for n qubits: n=1 -> 4^2=16, n=2 -> 4^3=64. Correct.

# Verify closure (spot-check 500 random pairs for speed)
rng = np.random.default_rng(42)
closure_2_ok = True
n_checks = 500
for _ in range(n_checks):
    i, j = rng.integers(0, 64, size=2)
    prod = P2[i] @ P2[j]
    if not mat_in_list(prod, P2):
        closure_2_ok = False
        break

all_pass_2 = closure_2_ok and size_formula_ok
RESULTS["s2_pauli_P2"] = {
    "size": 64,
    "size_formula_4n1": size_formula_ok,
    "closure_spot_check": closure_2_ok,
    "n_closure_checks": n_checks,
    "all_pass": all_pass_2,
}
print(f"  Size=64:    {len(P2) == 64}")
print(f"  4^(n+1):    {size_formula_ok}")
print(f"  Closure:    {closure_2_ok} ({n_checks} random pairs)")
print(f"  ALL PASS:   {all_pass_2}")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. CLIFFORD HIERARCHY — L1=Pauli, L2=Clifford, L3 includes T
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 3: Clifford hierarchy (L1, L2, L3)")
print("=" * 72)

# Clifford gates (level 2): normalizer of Pauli group
# Standard single-qubit Cliffords: H, S, and products
H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
S = np.array([[1, 0], [0, 1j]], dtype=complex)
T = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)

# Level 2 test: U is Clifford iff U P U† is Pauli for all Pauli P
def is_level2(U, pauli_list=None):
    """Check if U normalizes the Pauli group (is Clifford)."""
    if pauli_list is None:
        pauli_list = P1
    Ud = U.conj().T
    for P in pauli_list:
        conj = U @ P @ Ud
        if not mat_in_list(conj, pauli_list):
            return False
    return True

H_is_clifford = is_level2(H)
S_is_clifford = is_level2(S)
T_is_clifford = is_level2(T)

# Level 3 test: U is level 3 iff U P U† is Clifford for all Pauli P
# i.e., for every Pauli P, (UPU†) normalizes the Pauli group
def is_level3(U, pauli_list=None):
    """Check if U maps Paulis to Cliffords."""
    if pauli_list is None:
        pauli_list = P1
    Ud = U.conj().T
    for P in pauli_list:
        conj = U @ P @ Ud
        if not is_level2(conj, pauli_list):
            return False
    return True

T_is_level3 = is_level3(T)

all_pass_3 = H_is_clifford and S_is_clifford and (not T_is_clifford) and T_is_level3
RESULTS["s3_clifford_hierarchy"] = {
    "H_is_clifford": H_is_clifford,
    "S_is_clifford": S_is_clifford,
    "T_is_clifford": T_is_clifford,
    "T_is_level3": T_is_level3,
    "T_not_level2_but_level3": (not T_is_clifford) and T_is_level3,
    "all_pass": all_pass_3,
}
print(f"  H Clifford: {H_is_clifford}")
print(f"  S Clifford: {S_is_clifford}")
print(f"  T Clifford: {T_is_clifford} (should be False)")
print(f"  T Level-3:  {T_is_level3}")
print(f"  ALL PASS:   {all_pass_3}")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. JORDAN ALGEBRA J_2(C) — 2x2 Hermitian matrices
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 4: Jordan algebra J_2(C)")
print("=" * 72)

def random_hermitian(n=2, rng=None):
    if rng is None:
        rng = np.random.default_rng()
    M = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
    return (M + M.conj().T) / 2

rng4 = np.random.default_rng(123)
n_trials = 200

# Test commutativity: A∘B = B∘A
comm_ok = True
for _ in range(n_trials):
    A = random_hermitian(rng=rng4)
    B = random_hermitian(rng=rng4)
    if not mat_eq(jordan(A, B), jordan(B, A)):
        comm_ok = False
        break

# Test power-associativity: A∘(A∘A) = (A∘A)∘A  (trivially true for commutative)
# More meaningfully: A^2 ∘ A = A ∘ A^2
power_assoc_ok = True
for _ in range(n_trials):
    A = random_hermitian(rng=rng4)
    A2 = jordan(A, A)
    if not mat_eq(jordan(A2, A), jordan(A, A2)):
        power_assoc_ok = False
        break

# Jordan identity: (A∘B)∘A² = A∘(B∘A²)
jordan_id_ok = True
for _ in range(n_trials):
    A = random_hermitian(rng=rng4)
    B = random_hermitian(rng=rng4)
    A2 = jordan(A, A)
    lhs = jordan(jordan(A, B), A2)
    rhs = jordan(A, jordan(B, A2))
    if not mat_eq(lhs, rhs):
        jordan_id_ok = False
        break

# Verify result is Hermitian (closure in Hermitian matrices)
herm_closure_ok = True
for _ in range(n_trials):
    A = random_hermitian(rng=rng4)
    B = random_hermitian(rng=rng4)
    C = jordan(A, B)
    if not mat_eq(C, C.conj().T):
        herm_closure_ok = False
        break

all_pass_4 = comm_ok and power_assoc_ok and jordan_id_ok and herm_closure_ok
RESULTS["s4_jordan_J2C"] = {
    "commutative": comm_ok,
    "power_associative": power_assoc_ok,
    "jordan_identity": jordan_id_ok,
    "hermitian_closure": herm_closure_ok,
    "n_trials": n_trials,
    "all_pass": all_pass_4,
}
print(f"  Commutative:        {comm_ok}")
print(f"  Power-associative:  {power_assoc_ok}")
print(f"  Jordan identity:    {jordan_id_ok}")
print(f"  Hermitian closure:  {herm_closure_ok}")
print(f"  ALL PASS:           {all_pass_4}")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. LIE BRACKET vs JORDAN PRODUCT — AB = [A,B]/2 + A∘B
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 5: Lie + Jordan = full matrix algebra")
print("=" * 72)

rng5 = np.random.default_rng(456)
n_trials_5 = 200

# AB = [A,B]/2 + A∘B  for arbitrary complex matrices
split_ok = True
for _ in range(n_trials_5):
    A = rng5.standard_normal((2, 2)) + 1j * rng5.standard_normal((2, 2))
    B = rng5.standard_normal((2, 2)) + 1j * rng5.standard_normal((2, 2))
    AB = A @ B
    recon = lie(A, B) / 2 + jordan(A, B)
    if not mat_eq(AB, recon):
        split_ok = False
        break

# Lie bracket is anti-symmetric: [A,B] = -[B,A]
antisym_ok = True
for _ in range(n_trials_5):
    A = rng5.standard_normal((2, 2)) + 1j * rng5.standard_normal((2, 2))
    B = rng5.standard_normal((2, 2)) + 1j * rng5.standard_normal((2, 2))
    if not mat_eq(lie(A, B), -lie(B, A)):
        antisym_ok = False
        break

# Jacobi identity: [A,[B,C]] + [B,[C,A]] + [C,[A,B]] = 0
jacobi_ok = True
for _ in range(n_trials_5):
    A = rng5.standard_normal((2, 2)) + 1j * rng5.standard_normal((2, 2))
    B = rng5.standard_normal((2, 2)) + 1j * rng5.standard_normal((2, 2))
    C = rng5.standard_normal((2, 2)) + 1j * rng5.standard_normal((2, 2))
    J = lie(A, lie(B, C)) + lie(B, lie(C, A)) + lie(C, lie(A, B))
    if not mat_eq(J, np.zeros((2, 2), dtype=complex)):
        jacobi_ok = False
        break

all_pass_5 = split_ok and antisym_ok and jacobi_ok
RESULTS["s5_lie_jordan_split"] = {
    "AB_eq_lie_plus_jordan": split_ok,
    "lie_antisymmetric": antisym_ok,
    "jacobi_identity": jacobi_ok,
    "n_trials": n_trials_5,
    "all_pass": all_pass_5,
}
print(f"  AB = [A,B]/2 + A∘B: {split_ok}")
print(f"  Lie antisymmetric:   {antisym_ok}")
print(f"  Jacobi identity:     {jacobi_ok}")
print(f"  ALL PASS:            {all_pass_5}")

# ═══════════════════════════════════════════════════════════════════════════════
# 6. UNIVERSAL ENVELOPING ALGEBRA U(su(2)) — PBW, Casimir
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 6: U(su(2)) enveloping algebra")
print("=" * 72)

# su(2) generators in the spin-1/2 rep (factor of 1/2 included)
Jx = sx / 2
Jy = sy / 2
Jz = sz / 2

gens = [Jx, Jy, Jz]
gen_names = ["Jx", "Jy", "Jz"]

# Verify su(2) commutation relations: [Ji, Jj] = i ε_ijk Jk
cr_ok = True
# [Jx, Jy] = i Jz
if not mat_eq(commutator(Jx, Jy), 1j * Jz):
    cr_ok = False
# [Jy, Jz] = i Jx
if not mat_eq(commutator(Jy, Jz), 1j * Jx):
    cr_ok = False
# [Jz, Jx] = i Jy
if not mat_eq(commutator(Jz, Jx), 1j * Jy):
    cr_ok = False

# Casimir operator: C = Jx^2 + Jy^2 + Jz^2
C2 = Jx @ Jx + Jy @ Jy + Jz @ Jz

# Casimir commutes with all generators
casimir_commutes = True
for J in gens:
    if not mat_eq(commutator(C2, J), np.zeros((2, 2), dtype=complex)):
        casimir_commutes = False
        break

# Casimir eigenvalue for spin-1/2: j(j+1) = 3/4
casimir_eigenvalue = np.real(C2[0, 0])
casimir_val_ok = np.isclose(casimir_eigenvalue, 0.75)

# PBW basis check: in spin-1/2 rep, any product of generators can be
# reduced to span of {I, Jx, Jy, Jz} (since dim=2, the algebra is 4-dim)
# Verify: Jx*Jy = (i*Jz + Jordan(Jx,Jy))/1 and result is in span
pbw_ok = True
# Generate all products up to degree 2 and check they lie in span{I, Jx, Jy, Jz}
basis_mats = [I2, Jx, Jy, Jz]
for i in range(3):
    for j in range(3):
        prod = gens[i] @ gens[j]
        # Try to express as linear combo of basis
        # Stack basis as columns (vectorized)
        basis_vec = np.column_stack([b.flatten() for b in basis_mats])
        prod_vec = prod.flatten()
        # Solve least-squares
        coeffs, res, _, _ = np.linalg.lstsq(basis_vec, prod_vec, rcond=None)
        recon = sum(c * b for c, b in zip(coeffs, basis_mats))
        if not mat_eq(prod, recon):
            pbw_ok = False
            break
    if not pbw_ok:
        break

all_pass_6 = cr_ok and casimir_commutes and casimir_val_ok and pbw_ok
RESULTS["s6_enveloping_Usu2"] = {
    "commutation_relations": cr_ok,
    "casimir_commutes": casimir_commutes,
    "casimir_eigenvalue": float(casimir_eigenvalue),
    "casimir_val_3_4": casimir_val_ok,
    "pbw_span_closure": pbw_ok,
    "all_pass": all_pass_6,
}
print(f"  Commutation rels:  {cr_ok}")
print(f"  Casimir commutes:  {casimir_commutes}")
print(f"  Casimir = 3/4:     {casimir_val_ok} (val={casimir_eigenvalue:.4f})")
print(f"  PBW span closure:  {pbw_ok}")
print(f"  ALL PASS:          {all_pass_6}")

# ═══════════════════════════════════════════════════════════════════════════════
# 7. TENSOR PRODUCT ALGEBRA su(2) ⊗ su(2) ≅ so(4)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 7: su(2) ⊗ su(2) = so(4)")
print("=" * 72)

I4 = np.eye(4, dtype=complex)

# 6 generators: J_a ⊗ I and I ⊗ J_b
gens_left = [np.kron(J, I2) for J in gens]    # 3 left generators
gens_right = [np.kron(I2, J) for J in gens]   # 3 right generators
all_gens = gens_left + gens_right              # 6 total

# Verify: left and right commute (tensor product structure)
lr_commute = True
for L in gens_left:
    for R in gens_right:
        if not mat_eq(commutator(L, R), np.zeros((4, 4), dtype=complex)):
            lr_commute = False
            break
    if not lr_commute:
        break

# Left su(2) closes
left_close = (
    mat_eq(commutator(gens_left[0], gens_left[1]), 1j * gens_left[2]) and
    mat_eq(commutator(gens_left[1], gens_left[2]), 1j * gens_left[0]) and
    mat_eq(commutator(gens_left[2], gens_left[0]), 1j * gens_left[1])
)

# Right su(2) closes
right_close = (
    mat_eq(commutator(gens_right[0], gens_right[1]), 1j * gens_right[2]) and
    mat_eq(commutator(gens_right[1], gens_right[2]), 1j * gens_right[0]) and
    mat_eq(commutator(gens_right[2], gens_right[0]), 1j * gens_right[1])
)

# Dimension: so(4) has dim = 4*3/2 = 6, matches 3+3
dim_ok = len(all_gens) == 6

# Verify linear independence of the 6 generators
gen_matrix = np.column_stack([g.flatten() for g in all_gens])
rank = np.linalg.matrix_rank(gen_matrix)
independence_ok = rank == 6

all_pass_7 = lr_commute and left_close and right_close and dim_ok and independence_ok
RESULTS["s7_tensor_su2_su2"] = {
    "n_generators": len(all_gens),
    "left_right_commute": lr_commute,
    "left_su2_closes": left_close,
    "right_su2_closes": right_close,
    "dim_matches_so4": dim_ok,
    "generators_independent": independence_ok,
    "rank": int(rank),
    "all_pass": all_pass_7,
}
print(f"  Left-Right commute: {lr_commute}")
print(f"  Left su(2) closes:  {left_close}")
print(f"  Right su(2) closes: {right_close}")
print(f"  6 generators:       {dim_ok}")
print(f"  Rank=6:             {independence_ok}")
print(f"  ALL PASS:           {all_pass_7}")

# ═══════════════════════════════════════════════════════════════════════════════
# 8. SCHUR-WEYL DUALITY — C²⊗C² decomposition
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 8: Schur-Weyl duality on C^2 ⊗ C^2")
print("=" * 72)

# SWAP operator
SWAP = np.zeros((4, 4), dtype=complex)
for i in range(2):
    for j in range(2):
        # |ij> -> |ji>
        ij = i * 2 + j
        ji = j * 2 + i
        SWAP[ji, ij] = 1.0

# Symmetric projector: P_sym = (I + SWAP)/2
P_sym = (I4 + SWAP) / 2
# Antisymmetric projector: P_anti = (I - SWAP)/2
P_anti = (I4 - SWAP) / 2

# Verify projectors
proj_sym_ok = mat_eq(P_sym @ P_sym, P_sym)
proj_anti_ok = mat_eq(P_anti @ P_anti, P_anti)
proj_ortho_ok = mat_eq(P_sym @ P_anti, np.zeros((4, 4), dtype=complex))
proj_complete_ok = mat_eq(P_sym + P_anti, I4)

# Dimensions
dim_sym = int(np.real(np.trace(P_sym)))
dim_anti = int(np.real(np.trace(P_anti)))
dim_sym_ok = dim_sym == 3
dim_anti_ok = dim_anti == 1

# Projectors commute with U⊗U for random U in SU(2)
rng8 = np.random.default_rng(789)
uu_commute_ok = True
n_uu_trials = 100
for _ in range(n_uu_trials):
    # Random SU(2) via exponential map
    theta = rng8.standard_normal(3)
    H_rand = theta[0] * Jx + theta[1] * Jy + theta[2] * Jz
    U = expm(-1j * H_rand)
    UU = np.kron(U, U)
    # Check P_sym commutes with UU
    if not mat_eq(P_sym @ UU, UU @ P_sym):
        uu_commute_ok = False
        break
    if not mat_eq(P_anti @ UU, UU @ P_anti):
        uu_commute_ok = False
        break

# Projectors commute with SWAP (S_2 action)
swap_commute_sym = mat_eq(P_sym @ SWAP, SWAP @ P_sym)
swap_commute_anti = mat_eq(P_anti @ SWAP, SWAP @ P_anti)

# SWAP eigenvalues on subspaces
# Symmetric subspace: SWAP = +1
# Antisymmetric subspace: SWAP = -1
swap_eigs = np.linalg.eigvalsh(SWAP)
swap_sym_eigenval = np.real(np.trace(SWAP @ P_sym)) / max(dim_sym, 1)
swap_anti_eigenval = np.real(np.trace(SWAP @ P_anti)) / max(dim_anti, 1)
swap_eigen_ok = np.isclose(swap_sym_eigenval, 1.0) and np.isclose(swap_anti_eigenval, -1.0)

all_pass_8 = (
    proj_sym_ok and proj_anti_ok and proj_ortho_ok and proj_complete_ok and
    dim_sym_ok and dim_anti_ok and
    uu_commute_ok and swap_commute_sym and swap_commute_anti and swap_eigen_ok
)
RESULTS["s8_schur_weyl"] = {
    "P_sym_projector": proj_sym_ok,
    "P_anti_projector": proj_anti_ok,
    "projectors_orthogonal": proj_ortho_ok,
    "projectors_complete": proj_complete_ok,
    "dim_symmetric": dim_sym,
    "dim_antisymmetric": dim_anti,
    "commutes_with_UxU": uu_commute_ok,
    "n_UU_trials": n_uu_trials,
    "commutes_with_SWAP_sym": swap_commute_sym,
    "commutes_with_SWAP_anti": swap_commute_anti,
    "swap_eigenval_sym": float(swap_sym_eigenval),
    "swap_eigenval_anti": float(swap_anti_eigenval),
    "swap_eigenvalues_correct": swap_eigen_ok,
    "all_pass": all_pass_8,
}
print(f"  P_sym projector:    {proj_sym_ok}")
print(f"  P_anti projector:   {proj_anti_ok}")
print(f"  Orthogonal:         {proj_ortho_ok}")
print(f"  Complete:           {proj_complete_ok}")
print(f"  dim(sym)=3:         {dim_sym_ok} ({dim_sym})")
print(f"  dim(anti)=1:        {dim_anti_ok} ({dim_anti})")
print(f"  Commutes U⊗U:      {uu_commute_ok} ({n_uu_trials} trials)")
print(f"  Commutes SWAP:      {swap_commute_sym and swap_commute_anti}")
print(f"  SWAP eigenvalues:   {swap_eigen_ok} (sym={swap_sym_eigenval:.1f}, anti={swap_anti_eigenval:.1f})")
print(f"  ALL PASS:           {all_pass_8}")

# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SUMMARY")
print("=" * 72)

all_sections_pass = all(
    RESULTS[k].get("all_pass", False)
    for k in sorted(RESULTS.keys())
)
RESULTS["all_pass"] = all_sections_pass

for k in sorted(RESULTS.keys()):
    if k == "all_pass":
        continue
    status = "PASS" if RESULTS[k].get("all_pass") else "FAIL"
    print(f"  {k}: {status}")
print(f"\n  ALL PASS: {all_sections_pass}")

# ── write output ─────────────────────────────────────────────────────────────
out_path = os.path.join(
    os.path.dirname(__file__),
    "a2_state", "sim_results", "pure_lego_mega_algebra_results.json"
)
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(RESULTS, f, indent=2, default=str)
print(f"\n  Results written to: {out_path}")
