#!/usr/bin/env python3
"""
PURE LEGO: Lorentz Group <-> 2-Qubit QIT via SLOCC Classification
==================================================================
Foundational building block.  Pure math only -- numpy + scipy.
No engine imports.  Every operation verified against theory.

Sections
--------
1. SL(2,C) generators and random element construction (det = 1)
2. Lorentz 4-vector from density matrix:  rho -> X^mu sigma_mu
3. Minkowski norm from det(X):  det(X) = x0^2 - x1^2 - x2^2 - x3^2
4. SL(2,C) action on Hermitian 2x2 as Lorentz transformation
5. 2-qubit SLOCC:  SL(2,C) x SL(2,C) preserves entanglement class
6. Concurrence computation and SLOCC-class verification
7. Stress test: 10 SL(2,C) matrices x 5 states -> norm & class preserved

Key identities
--------------
  X  = x0 I + x1 sigma_x + x2 sigma_y + x3 sigma_z
  X' = A X A^dagger   (SL(2,C) action on Hermitian matrices)
  det(X') = det(A) det(X) det(A^dagger) = det(X)   when det(A) = 1
  => Minkowski norm is preserved  (this IS a Lorentz transformation)

  SLOCC on 2-qubit:  |psi'> = (A otimes B) |psi>,  A,B in SL(2,C)
  Concurrence transforms:  C(psi') = |det(A) det(B)| C(psi) = C(psi)
  => entangled stays entangled, product stays product
"""

import json, pathlib, time
import numpy as np
from scipy.linalg import sqrtm
classification = "classical_baseline"  # auto-backfill

np.random.seed(42)
EPS = 1e-12
RESULTS = {}

# ──────────────────────────────────────────────────────────────────────
# Pauli matrices & helpers
# ──────────────────────────────────────────────────────────────────────

I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
SIGMA_MU = [I2, sx, sy, sz]  # sigma_0 = I, sigma_1,2,3 = Pauli


def ket(v):
    """Column vector from list."""
    return np.array(v, dtype=complex).reshape(-1, 1)


def dm_from_ket(v):
    """Density matrix from ket vector."""
    k = ket(v)
    return k @ k.conj().T


def partial_trace_B(rho_AB, dA=2, dB=2):
    """Trace out subsystem B from dA x dB system."""
    rho = rho_AB.reshape(dA, dB, dA, dB)
    return np.trace(rho, axis1=1, axis2=3)


def partial_trace_A(rho_AB, dA=2, dB=2):
    """Trace out subsystem A from dA x dB system."""
    rho = rho_AB.reshape(dA, dB, dA, dB)
    return np.trace(rho, axis1=0, axis2=2)


# ──────────────────────────────────────────────────────────────────────
# Section 1: SL(2,C) construction
# ──────────────────────────────────────────────────────────────────────

def random_sl2c():
    """
    Generate a random SL(2,C) matrix (det = 1).
    Strategy: random complex 2x2, then rescale by det^{-1/2}.
    """
    M = (np.random.randn(2, 2) + 1j * np.random.randn(2, 2))
    d = np.linalg.det(M)
    # rescale so det = 1
    M = M / (d ** 0.5)
    return M


def verify_sl2c(A, label="", tol=1e-10):
    """Verify det(A) = 1 for SL(2,C)."""
    d = np.linalg.det(A)
    det_ok = abs(d - 1.0) < tol
    return {
        "label": label,
        "det_real": float(d.real),
        "det_imag": float(d.imag),
        "det_magnitude": float(abs(d)),
        "det_is_one": bool(det_ok),
    }


print("=== Section 1: SL(2,C) Construction ===")
sl2c_matrices = [random_sl2c() for _ in range(10)]
sl2c_checks = []
for i, A in enumerate(sl2c_matrices):
    check = verify_sl2c(A, label=f"SL2C_{i}")
    sl2c_checks.append(check)
    assert check["det_is_one"], f"SL(2,C) matrix {i} has det != 1"

RESULTS["section_1_sl2c_construction"] = {
    "n_matrices": 10,
    "all_det_one": all(c["det_is_one"] for c in sl2c_checks),
    "checks": sl2c_checks,
}
print(f"  10 SL(2,C) matrices constructed, all det=1: PASS")


# ──────────────────────────────────────────────────────────────────────
# Section 2: Density matrix <-> Lorentz 4-vector
# ──────────────────────────────────────────────────────────────────────

def rho_to_lorentz_vec(rho):
    """
    Decompose 2x2 Hermitian rho = sum_mu x^mu sigma_mu.
    x^mu = (1/2) Tr(sigma_mu . rho)
    Returns [x0, x1, x2, x3].
    """
    return np.array([0.5 * np.trace(sigma @ rho).real
                     for sigma in SIGMA_MU])


def lorentz_vec_to_rho(x):
    """Reconstruct rho = sum_mu x^mu sigma_mu."""
    return sum(x[mu] * SIGMA_MU[mu] for mu in range(4))


def minkowski_norm(x):
    """Minkowski norm: x0^2 - x1^2 - x2^2 - x3^2."""
    return x[0]**2 - x[1]**2 - x[2]**2 - x[3]**2


print("\n=== Section 2: Density Matrix <-> Lorentz 4-Vector ===")

# Test states: single-qubit
test_1q_states = {
    "|0>": dm_from_ket([1, 0]),
    "|1>": dm_from_ket([0, 1]),
    "|+>": dm_from_ket([1/np.sqrt(2), 1/np.sqrt(2)]),
    "|i>": dm_from_ket([1/np.sqrt(2), 1j/np.sqrt(2)]),
    "mixed": 0.5 * I2,
}

vec_checks = []
for label, rho in test_1q_states.items():
    x = rho_to_lorentz_vec(rho)
    rho_back = lorentz_vec_to_rho(x)
    roundtrip_ok = np.allclose(rho, rho_back, atol=EPS)
    det_rho = np.linalg.det(rho).real
    mink = minkowski_norm(x)
    det_match = abs(det_rho - mink) < EPS
    vec_checks.append({
        "label": label,
        "x_mu": [float(v) for v in x],
        "minkowski_norm": float(mink),
        "det_rho": float(det_rho),
        "det_equals_minkowski": bool(det_match),
        "roundtrip_ok": bool(roundtrip_ok),
    })
    assert roundtrip_ok, f"Roundtrip failed for {label}"
    assert det_match, f"det(rho) != Minkowski norm for {label}"

RESULTS["section_2_lorentz_vector"] = {
    "n_states": len(test_1q_states),
    "all_roundtrip": all(c["roundtrip_ok"] for c in vec_checks),
    "all_det_equals_minkowski": all(c["det_equals_minkowski"]
                                    for c in vec_checks),
    "checks": vec_checks,
}
print(f"  5 states: roundtrip OK, det(rho)=Minkowski norm: PASS")


# ──────────────────────────────────────────────────────────────────────
# Section 3: SL(2,C) acts as Lorentz transformation
# ──────────────────────────────────────────────────────────────────────

print("\n=== Section 3: SL(2,C) as Lorentz Transformation ===")

lorentz_checks = []
for i, A in enumerate(sl2c_matrices):
    for label, rho in test_1q_states.items():
        x_before = rho_to_lorentz_vec(rho)
        norm_before = minkowski_norm(x_before)

        # SL(2,C) action on Hermitian matrix: X' = A X A^dag
        # But this does NOT preserve trace (not unitary in general).
        # The Minkowski norm is det(X), and det(AXA^dag) = |det(A)|^2 det(X) = det(X).
        rho_prime = A @ rho @ A.conj().T
        x_after = rho_to_lorentz_vec(rho_prime)
        norm_after = minkowski_norm(x_after)

        norm_preserved = abs(norm_before - norm_after) < 1e-8
        lorentz_checks.append({
            "sl2c_index": i,
            "state": label,
            "norm_before": float(norm_before),
            "norm_after": float(norm_after),
            "norm_preserved": bool(norm_preserved),
        })
        assert norm_preserved, (
            f"Minkowski norm NOT preserved: SL2C_{i} on {label}: "
            f"{norm_before} -> {norm_after}"
        )

all_preserved = all(c["norm_preserved"] for c in lorentz_checks)
RESULTS["section_3_lorentz_action"] = {
    "n_tests": len(lorentz_checks),
    "all_norm_preserved": all_preserved,
    "checks": lorentz_checks,
}
print(f"  {len(lorentz_checks)} tests: Minkowski norm preserved under "
      f"SL(2,C) action: PASS")


# ──────────────────────────────────────────────────────────────────────
# Section 4: Concurrence for 2-qubit states
# ──────────────────────────────────────────────────────────────────────

def concurrence_pure(psi):
    """
    Concurrence for a pure 2-qubit state |psi> in C^4.
    C = 2|ad - bc| for |psi> = a|00> + b|01> + c|10> + d|11>.
    """
    p = psi.flatten()
    return float(2.0 * abs(p[0]*p[3] - p[1]*p[2]))


def concurrence_mixed(rho):
    """
    Wootters concurrence for a 2-qubit mixed state.
    C(rho) = max(0, l1-l2-l3-l4) where l_i are sqrt of eigenvalues
    of rho . rho_tilde in decreasing order.
    rho_tilde = (sy ox sy) rho* (sy ox sy)
    """
    sy_sy = np.kron(sy, sy)
    rho_tilde = sy_sy @ rho.conj() @ sy_sy
    R = rho @ rho_tilde
    evals = np.sort(np.real(np.linalg.eigvals(R)))[::-1]
    # clamp small negatives from numerics
    evals = np.maximum(evals, 0.0)
    lambdas = np.sqrt(evals)
    c = lambdas[0] - lambdas[1] - lambdas[2] - lambdas[3]
    return float(max(0.0, c))


print("\n=== Section 4: Concurrence Computation ===")

# Build 5 canonical 2-qubit states
phi_plus = ket([1, 0, 0, 1]) / np.sqrt(2)
phi_minus = ket([1, 0, 0, -1]) / np.sqrt(2)
psi_plus = ket([0, 1, 1, 0]) / np.sqrt(2)
product_00 = ket([1, 0, 0, 0])
product_plus_0 = ket([1/np.sqrt(2), 0, 1/np.sqrt(2), 0])

two_qubit_states = {
    "Phi+": {"ket": phi_plus, "rho": dm_from_ket(phi_plus.flatten()),
             "expected_class": "entangled"},
    "Phi-": {"ket": phi_minus, "rho": dm_from_ket(phi_minus.flatten()),
             "expected_class": "entangled"},
    "Psi+": {"ket": psi_plus, "rho": dm_from_ket(psi_plus.flatten()),
             "expected_class": "entangled"},
    "product_00": {"ket": product_00,
                   "rho": dm_from_ket(product_00.flatten()),
                   "expected_class": "product"},
    "product_+0": {"ket": product_plus_0,
                   "rho": dm_from_ket(product_plus_0.flatten()),
                   "expected_class": "product"},
}

conc_checks = []
for label, info in two_qubit_states.items():
    c_pure = concurrence_pure(info["ket"])
    c_mixed = concurrence_mixed(info["rho"])
    is_entangled = c_pure > 1e-10
    detected_class = "entangled" if is_entangled else "product"
    class_ok = detected_class == info["expected_class"]
    conc_checks.append({
        "label": label,
        "concurrence_pure": c_pure,
        "concurrence_mixed": c_mixed,
        "detected_class": detected_class,
        "expected_class": info["expected_class"],
        "class_correct": bool(class_ok),
        "pure_mixed_agree": bool(abs(c_pure - c_mixed) < 1e-8),
    })
    assert class_ok, f"Wrong class for {label}: expected {info['expected_class']}, got {detected_class}"

RESULTS["section_4_concurrence"] = {
    "n_states": len(two_qubit_states),
    "all_class_correct": all(c["class_correct"] for c in conc_checks),
    "all_pure_mixed_agree": all(c["pure_mixed_agree"] for c in conc_checks),
    "checks": conc_checks,
}
print(f"  5 states: concurrence & SLOCC class correct: PASS")


# ──────────────────────────────────────────────────────────────────────
# Section 5: SLOCC = SL(2,C) x SL(2,C) on 2-qubit states
# ──────────────────────────────────────────────────────────────────────

print("\n=== Section 5: SLOCC Preserves Entanglement Class ===")

def slocc_transform(psi_4, A, B):
    """
    Apply SLOCC transformation (A ox B) |psi>.
    A, B in SL(2,C).  Result is unnormalized in general.
    Returns normalized ket and the norm factor.
    """
    AB = np.kron(A, B)
    psi_out = AB @ psi_4
    norm = np.linalg.norm(psi_out)
    if norm < 1e-15:
        return psi_out, 0.0
    return psi_out / norm, float(norm)


slocc_checks = []
for i in range(10):
    A = sl2c_matrices[i]
    # Use a different SL(2,C) for subsystem B
    B = random_sl2c()
    for label, info in two_qubit_states.items():
        psi = info["ket"].flatten()
        c_before = concurrence_pure(psi)
        class_before = "entangled" if c_before > 1e-10 else "product"

        psi_prime, norm_factor = slocc_transform(psi, A, B)
        if norm_factor < 1e-15:
            # degenerate case, skip
            continue
        c_after = concurrence_pure(psi_prime)
        class_after = "entangled" if c_after > 1e-10 else "product"

        # SLOCC key property: det(A)=det(B)=1 =>
        # C(psi') = C(psi) / |norm_factor|^2... but we normalized.
        # For normalized states under (A ox B) with det=1:
        # C_unnorm = |det(A)||det(B)| * C = C (since dets = 1)
        # After renormalization: C_norm = C_unnorm / norm^2
        # So concurrence VALUE changes, but CLASS is preserved:
        # zero stays zero, nonzero stays nonzero.
        class_preserved = (class_before == class_after)

        slocc_checks.append({
            "sl2c_A_index": i,
            "state": label,
            "class_before": class_before,
            "class_after": class_after,
            "concurrence_before": float(c_before),
            "concurrence_after": float(c_after),
            "class_preserved": bool(class_preserved),
        })
        assert class_preserved, (
            f"SLOCC class NOT preserved: SL2C_{i} on {label}: "
            f"{class_before} -> {class_after}"
        )

RESULTS["section_5_slocc_class_preservation"] = {
    "n_tests": len(slocc_checks),
    "all_class_preserved": all(c["class_preserved"] for c in slocc_checks),
    "checks": slocc_checks,
}
print(f"  {len(slocc_checks)} SLOCC tests: entanglement class preserved: PASS")


# ──────────────────────────────────────────────────────────────────────
# Section 6: Lorentz structure of 2-qubit reduced states
# ──────────────────────────────────────────────────────────────────────

print("\n=== Section 6: Lorentz Vectors of Reduced Density Matrices ===")

reduced_checks = []
for i in range(10):
    A = sl2c_matrices[i]
    B = random_sl2c()
    for label, info in two_qubit_states.items():
        psi = info["ket"].flatten()
        rho_AB = np.outer(psi, psi.conj())
        rho_A = partial_trace_B(rho_AB)
        rho_B = partial_trace_A(rho_AB)

        # Lorentz vectors of reduced states
        x_A = rho_to_lorentz_vec(rho_A)
        x_B = rho_to_lorentz_vec(rho_B)
        mink_A = minkowski_norm(x_A)
        mink_B = minkowski_norm(x_B)
        det_A = np.linalg.det(rho_A).real
        det_B = np.linalg.det(rho_B).real

        reduced_checks.append({
            "state": label,
            "x_A": [float(v) for v in x_A],
            "x_B": [float(v) for v in x_B],
            "minkowski_norm_A": float(mink_A),
            "minkowski_norm_B": float(mink_B),
            "det_rhoA": float(det_A),
            "det_rhoB": float(det_B),
            "det_eq_mink_A": bool(abs(det_A - mink_A) < EPS),
            "det_eq_mink_B": bool(abs(det_B - mink_B) < EPS),
        })

# Only keep unique states (first 5)
reduced_checks = reduced_checks[:5]

RESULTS["section_6_reduced_lorentz_vectors"] = {
    "n_checks": len(reduced_checks),
    "all_det_eq_mink": all(
        c["det_eq_mink_A"] and c["det_eq_mink_B"] for c in reduced_checks
    ),
    "note": "Entangled states have mixed reduced states => Minkowski norm > 0 (timelike). Pure product states have pure reduced states => norm = 0 (lightlike).",
    "checks": reduced_checks,
}
print(f"  Reduced density matrices: det=Minkowski norm verified: PASS")


# ──────────────────────────────────────────────────────────────────────
# Section 7: Twistor-like structure -- SL(2,C) spinor map
# ──────────────────────────────────────────────────────────────────────

print("\n=== Section 7: Twistor-like Spinor Structure ===")

def extract_lorentz_matrix(A):
    """
    Given A in SL(2,C), extract the 4x4 real Lorentz matrix Lambda
    such that for any Hermitian X = x^mu sigma_mu:
        A X A^dag = x'^mu sigma_mu
        x' = Lambda . x
    Lambda_{mu,nu} = (1/2) Tr(sigma_mu A sigma_nu A^dag)
    """
    Lambda = np.zeros((4, 4))
    for mu in range(4):
        for nu in range(4):
            Lambda[mu, nu] = 0.5 * np.trace(
                SIGMA_MU[mu] @ A @ SIGMA_MU[nu] @ A.conj().T
            ).real
    return Lambda


def verify_lorentz_matrix(Lambda, tol=1e-8):
    """
    Verify Lambda^T eta Lambda = eta where eta = diag(1,-1,-1,-1).
    This is the defining property of a Lorentz transformation.
    """
    eta = np.diag([1.0, -1.0, -1.0, -1.0])
    product = Lambda.T @ eta @ Lambda
    return bool(np.allclose(product, eta, atol=tol))


twistor_checks = []
for i, A in enumerate(sl2c_matrices):
    Lambda = extract_lorentz_matrix(A)
    det_Lambda = np.linalg.det(Lambda)
    is_lorentz = verify_lorentz_matrix(Lambda)

    # Verify on a test state
    rho = test_1q_states["|+>"]
    x = rho_to_lorentz_vec(rho)
    x_direct = rho_to_lorentz_vec(A @ rho @ A.conj().T)
    x_via_lambda = Lambda @ x
    agree = np.allclose(x_direct, x_via_lambda, atol=1e-8)

    twistor_checks.append({
        "sl2c_index": i,
        "det_Lambda": float(det_Lambda),
        "is_proper_lorentz": bool(det_Lambda > 0),
        "satisfies_eta_invariance": is_lorentz,
        "spinor_map_agrees_with_direct": bool(agree),
    })
    assert is_lorentz, f"Lambda from SL2C_{i} is NOT a Lorentz matrix"
    assert agree, f"Spinor map disagrees with direct action for SL2C_{i}"

RESULTS["section_7_twistor_spinor_map"] = {
    "n_matrices": 10,
    "all_lorentz": all(c["satisfies_eta_invariance"] for c in twistor_checks),
    "all_agree": all(c["spinor_map_agrees_with_direct"]
                     for c in twistor_checks),
    "all_proper": all(c["is_proper_lorentz"] for c in twistor_checks),
    "note": "SL(2,C) -> SO+(3,1) is the double cover. det(Lambda)=+1 always (proper orthochronous). Two SL(2,C) matrices +/-A map to the same Lambda.",
    "checks": twistor_checks,
}
print(f"  10 matrices: SL(2,C)->SO+(3,1) spinor map verified: PASS")


# ──────────────────────────────────────────────────────────────────────
# Section 8: Double cover verification (+/-A -> same Lambda)
# ──────────────────────────────────────────────────────────────────────

print("\n=== Section 8: Double Cover Verification ===")

double_cover_checks = []
for i, A in enumerate(sl2c_matrices[:5]):
    Lambda_plus = extract_lorentz_matrix(A)
    Lambda_minus = extract_lorentz_matrix(-A)
    same = np.allclose(Lambda_plus, Lambda_minus, atol=1e-10)
    double_cover_checks.append({
        "sl2c_index": i,
        "plus_minus_same_lambda": bool(same),
    })
    assert same, f"Double cover failed for SL2C_{i}"

RESULTS["section_8_double_cover"] = {
    "all_verified": all(c["plus_minus_same_lambda"]
                        for c in double_cover_checks),
    "note": "SL(2,C) is a 2:1 cover of SO+(3,1). +A and -A both have det=1 and map to the same Lorentz transformation.",
    "checks": double_cover_checks,
}
print(f"  Double cover (+/-A -> same Lambda): PASS")


# ──────────────────────────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────────────────────────

print("\n=== SUMMARY ===")
all_pass = True
summary = {}
for key, val in RESULTS.items():
    # find any boolean field with "all_" prefix
    section_pass = True
    for k, v in val.items():
        if k.startswith("all_") and isinstance(v, bool):
            if not v:
                section_pass = False
    summary[key] = "PASS" if section_pass else "FAIL"
    if not section_pass:
        all_pass = False
    print(f"  {key}: {'PASS' if section_pass else 'FAIL'}")

RESULTS["summary"] = {
    "all_sections_pass": all_pass,
    "section_results": summary,
    "total_sl2c_matrices_tested": 10,
    "total_2qubit_states_tested": 5,
    "total_slocc_tests": len(slocc_checks),
    "total_lorentz_norm_tests": len(lorentz_checks),
}

print(f"\n  OVERALL: {'ALL PASS' if all_pass else 'SOME FAILURES'}")

# ──────────────────────────────────────────────────────────────────────
# Output
# ──────────────────────────────────────────────────────────────────────

out_dir = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
out_path = out_dir / "pure_lego_lorentz_slocc_results.json"

# Strip numpy types for JSON
def sanitize(obj):
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj

with open(out_path, "w") as f:
    json.dump(sanitize(RESULTS), f, indent=2)

print(f"\n  Results written to {out_path}")
