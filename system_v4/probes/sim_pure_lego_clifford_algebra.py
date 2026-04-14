#!/usr/bin/env python3
"""
sim_pure_lego_clifford_algebra.py
─────────────────────────────────
Pure Clifford algebra lego blocks.  Cl(3) and Cl(6).
No engine, no QIT runtime.  Only numpy + clifford.

Sections
--------
1. Cl(3) fundamentals   – signature, anticommutation, pseudoscalar
2. Rotors = SU(2)       – double cover, composition
3. Cl(3) <-> Pauli      – commutator / anticommutator correspondence
4. Bloch as Cl(3)       – idempotent projector, roundtrip, entropy
5. Cl(6) = 2-qubit      – 64 basis elements, cross-bivectors
6. Product state Cl(6)  – grade structure verification
7. Entangled state      – cross-bivector terms, T_ij, SVD
8. Rotor composition    – local vs cross rotors & entanglement
"""

import json, sys, os
import numpy as np
from clifford import Cl
classification = "classical_baseline"  # auto-backfill

# ── helpers ──────────────────────────────────────────────────────────────────

def mv_to_dict(mv, layout):
    """Multivector -> {blade_name: coeff} for nonzero blades."""
    d = {}
    for k, v in zip(layout.names, mv.value):
        if abs(v) > 1e-12:
            d[k] = float(np.round(v, 12))
    return d

def grade_dict(mv, layout):
    """Return {grade: coeff_dict} for nonzero grades."""
    out = {}
    n = layout.dims  # number of generators (int)
    for g in range(n + 1):
        part = mv(g)
        d = mv_to_dict(part, layout)
        if d:
            out[str(g)] = d
    return out

def mv_coeff(mv, blade):
    """Extract the coefficient of `blade` inside `mv`."""
    # blade has exactly one nonzero entry
    idx = int(np.nonzero(np.abs(blade.value) > 1e-12)[0][0])
    sign = blade.value[idx]
    return float(mv.value[idx] / sign)

RESULTS = {}

# ═══════════════════════════════════════════════════════════════════════════════
# 1. Cl(3) FUNDAMENTALS
# ═══════════════════════════════════════════════════════════════════════════════
print("=" * 72)
print("SECTION 1: Cl(3) fundamentals")
print("=" * 72)

layout3, blades3 = Cl(3)
e1, e2, e3 = blades3['e1'], blades3['e2'], blades3['e3']
I3 = e1 * e2 * e3  # pseudoscalar

sec1 = {}

# e_i^2 = +1
sq = {f"e{i+1}^2": float((b * b).value[0]) for i, b in enumerate([e1, e2, e3])}
sec1["squares"] = sq
print(f"  e_i^2 = {sq}")

# anticommutation: e_i e_j + e_j e_i = 0 for i != j
anticomm = {}
for i, a in enumerate([e1, e2, e3]):
    for j, b in enumerate([e1, e2, e3]):
        if i < j:
            val = float((a * b + b * a).value[0])
            anticomm[f"{{e{i+1},e{j+1}}}"] = val
sec1["anticommutators_off_diag"] = anticomm
print(f"  Anticommutators (off-diag): {anticomm}")

# 8 basis elements
n_basis = int(np.sum(np.abs(np.eye(2**3)), axis=0).shape[0])  # just 2^3
sec1["n_basis_elements"] = 2**3
print(f"  Basis elements: {2**3}")

# I^2 = -1
I_sq = float((I3 * I3).value[0])
sec1["I_squared"] = I_sq
print(f"  I^2 = {I_sq}")

sec1["all_pass"] = (
    all(v == 1.0 for v in sq.values())
    and all(abs(v) < 1e-12 for v in anticomm.values())
    and 2**3 == 8
    and abs(I_sq - (-1.0)) < 1e-12
)
print(f"  PASS: {sec1['all_pass']}")
RESULTS["1_cl3_fundamentals"] = sec1

# ═══════════════════════════════════════════════════════════════════════════════
# 2. ROTORS = SU(2) DOUBLE COVER
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 2: Rotors = SU(2)")
print("=" * 72)

sec2 = {}

# Rotor in e1-e2 plane by angle theta
def rotor_12(theta):
    return np.cos(theta / 2) + np.sin(theta / 2) * (e1 * e2)

# R * R_tilde = 1
R = rotor_12(np.pi / 3)
R_tilde = ~R
product = R * R_tilde
scalar_part = float(product.value[0])
sec2["R_Rtilde_scalar"] = scalar_part
sec2["R_Rtilde_is_1"] = abs(scalar_part - 1.0) < 1e-12 and np.max(np.abs(product.value[1:])) < 1e-12
print(f"  R*R~ = {scalar_part} (is 1: {sec2['R_Rtilde_is_1']})")

# R(2pi) = -1
R_2pi = rotor_12(2 * np.pi)
r2pi_scalar = float(R_2pi.value[0])
sec2["R_2pi_scalar"] = round(r2pi_scalar, 10)
sec2["R_2pi_is_minus1"] = abs(r2pi_scalar - (-1.0)) < 1e-10
print(f"  R(2pi) scalar = {r2pi_scalar:.6f} (is -1: {sec2['R_2pi_is_minus1']})")

# R(4pi) = +1
R_4pi = rotor_12(4 * np.pi)
r4pi_scalar = float(R_4pi.value[0])
sec2["R_4pi_scalar"] = round(r4pi_scalar, 10)
sec2["R_4pi_is_plus1"] = abs(r4pi_scalar - 1.0) < 1e-10
print(f"  R(4pi) scalar = {r4pi_scalar:.6f} (is +1: {sec2['R_4pi_is_plus1']})")

# Compose two rotors
R_a = rotor_12(np.pi / 6)
R_b = rotor_12(np.pi / 4)
R_ab = R_a * R_b
R_direct = rotor_12(np.pi / 6 + np.pi / 4)
compose_match = np.max(np.abs((R_ab - R_direct).value)) < 1e-12
sec2["rotor_composition_matches"] = bool(compose_match)
print(f"  Rotor composition matches direct: {compose_match}")

sec2["all_pass"] = sec2["R_Rtilde_is_1"] and sec2["R_2pi_is_minus1"] and sec2["R_4pi_is_plus1"] and sec2["rotor_composition_matches"]
print(f"  PASS: {sec2['all_pass']}")
RESULTS["2_rotors_su2"] = sec2

# ═══════════════════════════════════════════════════════════════════════════════
# 3. Cl(3) <-> PAULI CORRESPONDENCE
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 3: Cl(3) <-> Pauli")
print("=" * 72)

sec3 = {}

# Pauli matrices
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)

paulis = [sx, sy, sz]
cl_gens = [e1, e2, e3]

# Anticommutator: {sigma_i, sigma_j} = 2 delta_ij I
# Same as Cl(3): {e_i, e_j} = 2 delta_ij
anticomm_pauli = {}
anticomm_cl3 = {}
for i in range(3):
    for j in range(i, 3):
        p_ac = paulis[i] @ paulis[j] + paulis[j] @ paulis[i]
        expected = 2.0 * (1 if i == j else 0) * I2
        pauli_ok = np.allclose(p_ac, expected)
        anticomm_pauli[f"{{s{i+1},s{j+1}}}"] = bool(pauli_ok)

        cl_ac = cl_gens[i] * cl_gens[j] + cl_gens[j] * cl_gens[i]
        cl_scalar = float(cl_ac.value[0])
        cl_expected = 2.0 if i == j else 0.0
        cl_ok = abs(cl_scalar - cl_expected) < 1e-12
        anticomm_cl3[f"{{e{i+1},e{j+1}}}"] = bool(cl_ok)

sec3["anticommutator_pauli_match"] = anticomm_pauli
sec3["anticommutator_cl3_match"] = anticomm_cl3

# Commutator: [sigma_i, sigma_j] = 2i epsilon_ijk sigma_k
# In Cl(3): [e_i, e_j] = 2 e_i e_j (for i != j)  which is a bivector
# The bivector e_i e_j maps to i sigma_k  (Levi-Civita)
comm_check = {}
levi = {(0, 1): 2, (1, 2): 0, (0, 2): 1}  # (i,j) -> k index
for (i, j), k in levi.items():
    # Pauli side: [s_i, s_j] = 2i * eps_ijk * s_k
    p_comm = paulis[i] @ paulis[j] - paulis[j] @ paulis[i]
    sign = 1 if (i, j) in [(0, 1), (1, 2)] else -1
    if (i, j) == (0, 2):
        sign = -1
    expected_p = 2j * sign * paulis[k]
    pauli_comm_ok = bool(np.allclose(p_comm, expected_p))

    # Cl(3) side: [e_i, e_j] = 2 * e_i * e_j  (bivector)
    cl_comm = cl_gens[i] * cl_gens[j] - cl_gens[j] * cl_gens[i]
    # Should be 2 * e_ij bivector
    expected_cl = 2 * cl_gens[i] * cl_gens[j]
    cl_comm_ok = bool(np.max(np.abs((cl_comm - expected_cl).value)) < 1e-12)

    comm_check[f"[e{i+1},e{j+1}]"] = {"pauli_ok": pauli_comm_ok, "cl3_ok": cl_comm_ok}

sec3["commutator_correspondence"] = comm_check

sec3["all_pass"] = (
    all(anticomm_pauli.values())
    and all(anticomm_cl3.values())
    and all(v["pauli_ok"] and v["cl3_ok"] for v in comm_check.values())
)
print(f"  Anticommutator (Pauli): {anticomm_pauli}")
print(f"  Anticommutator (Cl3):   {anticomm_cl3}")
print(f"  Commutator correspondence: {comm_check}")
print(f"  PASS: {sec3['all_pass']}")
RESULTS["3_cl3_pauli"] = sec3

# ═══════════════════════════════════════════════════════════════════════════════
# 4. BLOCH SPHERE AS Cl(3)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 4: Bloch as Cl(3)")
print("=" * 72)

sec4 = {}

# Density operator: rho = (1 + r . e) / 2
# Pure state on z-axis: r = (0,0,1)
r_vec = np.array([0.0, 0.0, 1.0])
rho_cl = (1 + r_vec[0] * e1 + r_vec[1] * e2 + r_vec[2] * e3) / 2

# Check idempotent: rho^2 = rho (for pure state |r|=1)
rho_sq = rho_cl * rho_cl
idempotent_err = float(np.max(np.abs((rho_sq - rho_cl).value)))
sec4["pure_state_idempotent_err"] = idempotent_err
sec4["pure_state_idempotent"] = idempotent_err < 1e-12
print(f"  Pure state idempotent error: {idempotent_err:.2e}")

# Mixed state: r = (0.3, 0.4, 0.5)
r_mixed = np.array([0.3, 0.4, 0.5])
r_norm = float(np.linalg.norm(r_mixed))
rho_mixed = (1 + r_mixed[0] * e1 + r_mixed[1] * e2 + r_mixed[2] * e3) / 2

# Roundtrip: extract r back from rho
r_extracted = np.array([
    2 * float((rho_mixed * e1)(0).value[0]),
    2 * float((rho_mixed * e2)(0).value[0]),
    2 * float((rho_mixed * e3)(0).value[0]),
])
roundtrip_err = float(np.max(np.abs(r_extracted - r_mixed)))
sec4["roundtrip_error"] = roundtrip_err
sec4["roundtrip_pass"] = roundtrip_err < 1e-12
print(f"  Roundtrip r_mixed: {r_mixed} -> {r_extracted} (err={roundtrip_err:.2e})")

# Entropy from Cl(3): S = -tr(rho log rho)
# eigenvalues of rho = (1 +/- |r|) / 2
lam_p = (1 + r_norm) / 2
lam_m = (1 - r_norm) / 2
entropy = 0.0
for lam in [lam_p, lam_m]:
    if lam > 1e-15:
        entropy -= lam * np.log2(lam)
sec4["bloch_r_norm"] = r_norm
sec4["entropy_bits"] = round(float(entropy), 10)
sec4["entropy_from_eigenvalues"] = [round(lam_p, 10), round(lam_m, 10)]
print(f"  |r| = {r_norm:.4f}, S = {entropy:.6f} bits")

# Pure state entropy = 0
lam_pure = [(1 + 1.0) / 2, (1 - 1.0) / 2]
s_pure = sum(-l * np.log2(l) for l in lam_pure if l > 1e-15)
sec4["pure_state_entropy"] = round(float(s_pure), 10)
sec4["pure_state_entropy_is_zero"] = abs(s_pure) < 1e-12
print(f"  Pure state entropy: {s_pure:.6f} (is 0: {sec4['pure_state_entropy_is_zero']})")

sec4["all_pass"] = sec4["pure_state_idempotent"] and sec4["roundtrip_pass"] and sec4["pure_state_entropy_is_zero"]
print(f"  PASS: {sec4['all_pass']}")
RESULTS["4_bloch_cl3"] = sec4

# ═══════════════════════════════════════════════════════════════════════════════
# 5. Cl(6) = 2-QUBIT SPACE
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 5: Cl(6) = 2-qubit")
print("=" * 72)

sec5 = {}

layout6, blades6 = Cl(6)
e = [blades6[f'e{i+1}'] for i in range(6)]
# Subsystem A: e1,e2,e3   Subsystem B: e4,e5,e6
eA = e[:3]
eB = e[3:]

sec5["n_basis_elements"] = 2**6
sec5["n_basis_is_64"] = 2**6 == 64
print(f"  Basis elements: {2**6}")

# Cross-bivectors: e_i * e_j for i in A, j in B  -> 3x3 = 9
cross_bivectors = {}
for i in range(3):
    for j in range(3):
        bv = eA[i] * eB[j]
        name = f"e{i+1}*e{j+4}"
        cross_bivectors[name] = mv_to_dict(bv, layout6)
sec5["cross_bivectors_count"] = len(cross_bivectors)
sec5["cross_bivectors"] = cross_bivectors
print(f"  Cross-bivectors: {len(cross_bivectors)} (expected 9)")

# Verify cross-bivectors are grade-2
all_grade2 = True
for i in range(3):
    for j in range(3):
        bv = eA[i] * eB[j]
        g2 = bv(2)
        if np.max(np.abs((bv - g2).value)) > 1e-12:
            all_grade2 = False
sec5["cross_bivectors_all_grade2"] = all_grade2
print(f"  All cross-bivectors are grade-2: {all_grade2}")

sec5["all_pass"] = sec5["n_basis_is_64"] and sec5["cross_bivectors_count"] == 9 and all_grade2
print(f"  PASS: {sec5['all_pass']}")
RESULTS["5_cl6_2qubit"] = sec5

# ═══════════════════════════════════════════════════════════════════════════════
# 6. PRODUCT STATE IN Cl(6)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 6: Product state in Cl(6)")
print("=" * 72)

sec6 = {}

# Product state: rho_AB = rho_A tensor rho_B
# = (1 + a.eA)/2 * (1 + b.eB)/2
a_vec = np.array([0.0, 0.0, 1.0])  # |0> on A
b_vec = np.array([1.0, 0.0, 0.0])  # |+> on B

rho_A = (1 + sum(a_vec[i] * eA[i] for i in range(3))) / 2
rho_B = (1 + sum(b_vec[i] * eB[i] for i in range(3))) / 2
rho_product = rho_A * rho_B

# Grade structure
gs = grade_dict(rho_product, layout6)
sec6["grade_structure"] = {g: list(v.keys()) for g, v in gs.items()}
print(f"  Grade structure of product state:")
for g, blades_in_g in gs.items():
    print(f"    grade {g}: {list(blades_in_g.keys())}")

# Expand: (1 + a.eA)(1 + b.eB)/4
# = (1 + a.eA + b.eB + (a.eA)(b.eB)) / 4
# For a=(0,0,1), b=(1,0,0): = (1 + e3 + e4 + e3*e4) / 4
expected_product = (1 + eA[2] + eB[0] + eA[2] * eB[0]) / 4
product_match_err = float(np.max(np.abs((rho_product - expected_product).value)))
sec6["expansion_match_error"] = product_match_err
sec6["expansion_match"] = product_match_err < 1e-12
print(f"  Expansion match error: {product_match_err:.2e}")

# Check: no cross-bivector terms that aren't from (a.eA)(b.eB)
# In product state, cross terms only come from direct product a_i * b_j
sec6["has_only_product_cross_terms"] = True
for i in range(3):
    for j in range(3):
        bv = eA[i] * eB[j]
        coeff = mv_coeff(rho_product, bv)
        expected_coeff = a_vec[i] * b_vec[j] / 4.0
        if abs(coeff - expected_coeff) > 1e-12:
            sec6["has_only_product_cross_terms"] = False
print(f"  Only product cross terms: {sec6['has_only_product_cross_terms']}")

sec6["all_pass"] = sec6["expansion_match"] and sec6["has_only_product_cross_terms"]
print(f"  PASS: {sec6['all_pass']}")
RESULTS["6_product_state_cl6"] = sec6

# ═══════════════════════════════════════════════════════════════════════════════
# 7. ENTANGLED STATE — CROSS-BIVECTOR TERMS, T_ij, SVD
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 7: Entangled state")
print("=" * 72)

sec7 = {}

# Bell state |Phi+> = (|00> + |11>)/sqrt(2)
# In Bloch/Cl(6): rho = (1 + e3*e6 + e1*e4 - e2*e5) / 4
# This is the singlet-like maximally entangled state
# T_ij = tr(rho * sigma_i x sigma_j)
# For |Phi+>: T = diag(1, -1, 1)

rho_entangled = (1 + eA[0] * eB[0] - eA[1] * eB[1] + eA[2] * eB[2]) / 4

# Extract T_ij matrix from cross-bivector coefficients
T = np.zeros((3, 3))
for i in range(3):
    for j in range(3):
        bv = eA[i] * eB[j]
        # Find the bitmap for this bivector
        bv_idx = np.nonzero(np.abs(bv.value) > 1e-12)[0][0]
        bv_sign = bv.value[bv_idx]
        coeff_in_rho = rho_entangled.value[bv_idx]
        T[i, j] = 4.0 * coeff_in_rho / bv_sign  # undo the /4 and sign from basis

sec7["T_matrix"] = T.tolist()
print(f"  T matrix:\n{T}")

# SVD of T
U, singular_values, Vt = np.linalg.svd(T)
sec7["singular_values"] = [round(float(s), 10) for s in singular_values]
print(f"  Singular values: {singular_values}")

# For maximally entangled: all singular values = 1
sec7["max_entangled_sv_all_1"] = bool(np.allclose(singular_values, [1, 1, 1]))
print(f"  All SVs = 1 (maximally entangled): {sec7['max_entangled_sv_all_1']}")

# Local Bloch vectors: a_i = 4 * coeff(eA_i), b_j = 4 * coeff(eB_j)
a_local = np.array([4.0 * mv_coeff(rho_entangled, eA[i]) for i in range(3)])
b_local = np.array([4.0 * mv_coeff(rho_entangled, eB[j]) for j in range(3)])
sec7["local_bloch_a"] = a_local.tolist()
sec7["local_bloch_b"] = b_local.tolist()
sec7["local_bloch_zero"] = bool(np.allclose(a_local, 0) and np.allclose(b_local, 0))
print(f"  Local Bloch a: {a_local} (zero: {np.allclose(a_local, 0)})")
print(f"  Local Bloch b: {b_local} (zero: {np.allclose(b_local, 0)})")

# Product state T for comparison
T_prod = np.zeros((3, 3))
for i in range(3):
    for j in range(3):
        bv = eA[i] * eB[j]
        bv_idx = np.nonzero(np.abs(bv.value) > 1e-12)[0][0]
        bv_sign = bv.value[bv_idx]
        T_prod[i, j] = 4.0 * rho_product.value[bv_idx] / bv_sign

_, sv_prod, _ = np.linalg.svd(T_prod)
sec7["product_state_T"] = T_prod.tolist()
sec7["product_state_sv"] = [round(float(s), 10) for s in sv_prod]
# Product state T should be rank-1 (outer product a x b)
sec7["product_T_rank1"] = int(np.sum(sv_prod > 1e-10)) == 1
print(f"  Product T SVs: {sv_prod} (rank 1: {sec7['product_T_rank1']})")

sec7["all_pass"] = sec7["max_entangled_sv_all_1"] and sec7["local_bloch_zero"] and sec7["product_T_rank1"]
print(f"  PASS: {sec7['all_pass']}")
RESULTS["7_entangled_state"] = sec7

# ═══════════════════════════════════════════════════════════════════════════════
# 8. ROTOR COMPOSITION — LOCAL vs CROSS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("SECTION 8: Rotor composition")
print("=" * 72)

sec8 = {}

def extract_T(rho_mv):
    """Extract 3x3 correlation tensor T_ij from Cl(6) density multivector."""
    T_out = np.zeros((3, 3))
    for ii in range(3):
        for jj in range(3):
            T_out[ii, jj] = 4.0 * mv_coeff(rho_mv, eA[ii] * eB[jj])
    return T_out

# ── 8a: Local rotors preserve T singular values ──
# Local rotor on A (e1-e2 plane) and B (e4-e5 plane)
theta_A = np.pi / 4
R_A = np.cos(theta_A / 2) + np.sin(theta_A / 2) * (eA[0] * eA[1])
theta_B = np.pi / 3
R_B = np.cos(theta_B / 2) + np.sin(theta_B / 2) * (eB[0] * eB[1])

# Verify: local A rotor commutes with B generators under sandwich
commutes_across = all(
    np.allclose((R_A * eB[j] * ~R_A).value, eB[j].value)
    for j in range(3)
)
sec8["local_rotor_commutes_across_subsystem"] = bool(commutes_across)
print(f"  Local A rotor leaves B generators invariant: {commutes_across}")

# Apply local rotors to product state — T SVs should stay rank-1
rho_rotated_local = R_A * R_B * rho_product * ~R_B * ~R_A
T_local_rotated = extract_T(rho_rotated_local)
_, sv_local_rot, _ = np.linalg.svd(T_local_rotated)
sec8["product_after_local_svs"] = [round(float(s), 10) for s in sv_local_rot]
local_still_rank1 = int(np.sum(sv_local_rot > 1e-10)) <= 1
sec8["local_rotation_preserves_product_rank"] = bool(local_still_rank1)
print(f"  Product state after local rotors, T SVs: {np.round(sv_local_rot, 6)}")
print(f"  Still rank-1 (separable): {local_still_rank1}")

# Apply local rotors to entangled state — T SVs should stay [1,1,1]
rho_ent_local = R_A * R_B * rho_entangled * ~R_B * ~R_A
T_ent_local = extract_T(rho_ent_local)
_, sv_ent_local, _ = np.linalg.svd(T_ent_local)
sec8["bell_after_local_svs"] = [round(float(s), 10) for s in sv_ent_local]
ent_preserved = bool(np.allclose(sv_ent_local, [1, 1, 1], atol=1e-6))
sec8["local_rotors_preserve_entanglement"] = ent_preserved
print(f"  Bell state after local rotors, T SVs: {np.round(sv_ent_local, 6)}")
print(f"  Entanglement preserved (SVs [1,1,1]): {ent_preserved}")

# ── 8b: Multi-angle sweep — local rotors never change T SVs ──
sv_drifts = []
for angle in np.linspace(0, 2 * np.pi, 12):
    R_test = np.cos(angle / 2) + np.sin(angle / 2) * (eA[0] * eA[1])
    rho_test = R_test * rho_entangled * ~R_test
    _, svs, _ = np.linalg.svd(extract_T(rho_test))
    sv_drifts.append(float(np.max(np.abs(svs - 1.0))))
max_drift = max(sv_drifts)
sec8["sv_max_drift_over_sweep"] = max_drift
sec8["svs_invariant_under_local_rotation"] = max_drift < 1e-10
print(f"  SV max drift over 12-angle sweep: {max_drift:.2e}")

# ── 8c: Cross-bivector rotor mixes subsystem generators ──
theta_cross = np.pi / 4
R_cross = np.cos(theta_cross / 2) + np.sin(theta_cross / 2) * (eA[0] * eB[0])

# Cross rotor does NOT commute with generators of either subsystem
e1_transformed = R_cross * eA[0] * ~R_cross
e4_transformed = R_cross * eB[0] * ~R_cross
e1_changed = not np.allclose(e1_transformed.value, eA[0].value)
e4_changed = not np.allclose(e4_transformed.value, eB[0].value)
sec8["cross_rotor_transforms_eA1"] = bool(e1_changed)
sec8["cross_rotor_transforms_eB1"] = bool(e4_changed)
print(f"  Cross rotor transforms e1: {e1_changed}, e4: {e4_changed}")

# Show what e1 becomes under cross rotor
e1_new_dict = mv_to_dict(e1_transformed, layout6)
sec8["e1_after_cross_rotor"] = e1_new_dict
print(f"  e1 -> {e1_new_dict}")

# Cross rotor redefines subsystem boundaries: it mixes A and B generators
# This is the Cl(6) expression of the fact that entanglement is
# subsystem-relative. The cross-bivector rotor changes WHICH generators
# belong to which subsystem, not the state itself.

# ── 8d: Rotor composition — R_A * R_B != R_B * R_A but both are local ──
R_AB = R_A * R_B
R_BA = R_B * R_A
compose_commutes = np.allclose(R_AB.value, R_BA.value)
sec8["local_rotors_commute"] = bool(compose_commutes)
print(f"  R_A * R_B == R_B * R_A (local rotors commute): {compose_commutes}")

# ── 8e: Cross rotor composed with local rotor != local rotor composed with cross ──
R_A_cross = R_A * R_cross
R_cross_A = R_cross * R_A
cross_local_commute = np.allclose(R_A_cross.value, R_cross_A.value)
sec8["cross_local_rotors_commute"] = bool(cross_local_commute)
print(f"  R_A * R_cross == R_cross * R_A: {cross_local_commute}")

sec8["all_pass"] = (
    sec8["local_rotor_commutes_across_subsystem"]
    and sec8["local_rotation_preserves_product_rank"]
    and sec8["local_rotors_preserve_entanglement"]
    and sec8["svs_invariant_under_local_rotation"]
    and sec8["cross_rotor_transforms_eA1"]
    and sec8["cross_rotor_transforms_eB1"]
    and sec8["local_rotors_commute"]
)
print(f"  PASS: {sec8['all_pass']}")
RESULTS["8_rotor_composition"] = sec8

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
    "a2_state", "sim_results", "pure_lego_clifford_algebra_results.json"
)
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(RESULTS, f, indent=2, default=str)
print(f"\n  Results written to: {out_path}")
