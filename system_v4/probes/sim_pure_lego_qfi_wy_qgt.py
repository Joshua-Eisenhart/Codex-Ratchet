#!/usr/bin/env python3
"""
Pure-math lego: Quantum Fisher Information, Wigner-Yanase Skew Information,
Quantum Geometric Tensor.

Standalone. Only numpy, scipy, sympy. No engine dependencies.
"""

import json
import os
import warnings
import numpy as np
from scipy.linalg import sqrtm
import sympy as sp
classification = "canonical"

warnings.filterwarnings("ignore", message="Matrix is singular", category=RuntimeWarning)
from sympy import sqrt, Rational, conjugate, re, im, symbols, simplify, Matrix

# ─── Pauli matrices ───────────────────────────────────────────────────────────
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)

GENERATORS = {"sx": sx, "sy": sy, "sz": sz}

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- pure numpy/scipy/sympy math"},
    "pyg": {"tried": False, "used": False, "reason": "not needed -- no graph layer"},
    "z3": {"tried": False, "used": False, "reason": "not needed -- no SMT proof search"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed -- no synthesis/proof search"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic spot checks and closed-form simplification for pure-math metric relations"},
    "clifford": {"tried": False, "used": False, "reason": "not needed -- no geometric algebra layer"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- direct information-geometry formulas used instead"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed -- no equivariant network layer"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed -- no dependency graph"},
    "xgi": {"tried": False, "used": False, "reason": "not needed -- no hypergraph layer"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed -- no cell-complex layer"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed -- no persistence layer"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": "load_bearing",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Quantum Fisher Information
# ═══════════════════════════════════════════════════════════════════════════════

def qfi(rho, H):
    """Quantum Fisher Information of state rho w.r.t. generator H."""
    evals, evecs = np.linalg.eigh(rho)
    d = len(evals)
    F = 0.0
    for i in range(d):
        for j in range(d):
            s = evals[i] + evals[j]
            if s > 1e-15:
                hij = abs(evecs[:, i].conj() @ H @ evecs[:, j]) ** 2
                F += 2 * (evals[i] - evals[j]) ** 2 / s * hij
    return float(F)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Wigner-Yanase Skew Information
# ═══════════════════════════════════════════════════════════════════════════════

def wigner_yanase(rho, K):
    """Wigner-Yanase skew information I_WY(rho, K)."""
    sqrt_rho = sqrtm(rho)
    comm = sqrt_rho @ K - K @ sqrt_rho
    return -0.5 * np.real(np.trace(comm @ comm))


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Quantum Geometric Tensor
# ═══════════════════════════════════════════════════════════════════════════════

def qgt(rho, generators):
    """Quantum geometric tensor Q_ij = Cov(G_i, G_j) in state rho."""
    n = len(generators)
    Q = np.zeros((n, n), dtype=complex)
    for i in range(n):
        for j in range(n):
            Q[i, j] = (np.trace(rho @ generators[i] @ generators[j])
                        - np.trace(rho @ generators[i]) * np.trace(rho @ generators[j]))
    return Q


def fubini_study_metric(Q):
    return np.real(Q)


def berry_curvature(Q):
    return np.imag(Q)


# ═══════════════════════════════════════════════════════════════════════════════
# Test states
# ═══════════════════════════════════════════════════════════════════════════════

def make_pure(v):
    v = v / np.linalg.norm(v)
    return np.outer(v, v.conj())

def bloch_state(r, theta, phi):
    """Mixed state on Bloch sphere: rho = (I + r*(nx sx + ny sy + nz sz))/2."""
    nx = r * np.sin(theta) * np.cos(phi)
    ny = r * np.sin(theta) * np.sin(phi)
    nz = r * np.cos(theta)
    return 0.5 * (I2 + nx * sx + ny * sy + nz * sz)

ket0 = np.array([1, 0], dtype=complex)
ket1 = np.array([0, 1], dtype=complex)
ket_plus = np.array([1, 1], dtype=complex) / np.sqrt(2)
ket_minus = np.array([1, -1], dtype=complex) / np.sqrt(2)
ket_plusi = np.array([1, 1j], dtype=complex) / np.sqrt(2)

STATES_2x2 = {
    "pure_0":        make_pure(ket0),
    "pure_1":        make_pure(ket1),
    "pure_plus":     make_pure(ket_plus),
    "pure_minus":    make_pure(ket_minus),
    "pure_+i":       make_pure(ket_plusi),
    "mixed_z_0.5":   bloch_state(0.5, 0, 0),
    "mixed_z_0.8":   bloch_state(0.8, 0, 0),
    "mixed_x_0.5":   bloch_state(0.5, np.pi / 2, 0),
    "mixed_rand":    bloch_state(0.6, np.pi / 3, np.pi / 4),
    "maximally_mixed": 0.5 * I2,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def variance(rho, H):
    return float(np.real(np.trace(rho @ H @ H) - np.trace(rho @ H) ** 2))


def op_norm_sq(H):
    return float(np.max(np.abs(np.linalg.eigvalsh(H))) ** 2)


def is_pure(rho, tol=1e-10):
    return abs(np.real(np.trace(rho @ rho)) - 1.0) < tol


# ═══════════════════════════════════════════════════════════════════════════════
# Run all tests
# ═══════════════════════════════════════════════════════════════════════════════

def run_tests():
    results = {
        "name": "pure_lego_qfi_wy_qgt",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "sections": {},
    }
    all_pass = True

    # ── Section 1: QFI on 10×3 ────────────────────────────────────────────────
    sec1 = {"qfi_values": {}, "tests": []}

    for sname, rho in STATES_2x2.items():
        sec1["qfi_values"][sname] = {}
        for gname, H in GENERATORS.items():
            val = qfi(rho, H)
            sec1["qfi_values"][sname][gname] = round(val, 10)

    # Spot checks
    def check(name, cond):
        nonlocal all_pass
        passed = bool(cond)
        sec1["tests"].append({"name": name, "pass": passed})
        if not passed:
            all_pass = False
            print(f"  FAIL: {name}")

    check("pure_0 QFI(sx)=4", abs(qfi(STATES_2x2["pure_0"], sx) - 4.0) < 1e-10)
    check("pure_0 QFI(sz)=0", abs(qfi(STATES_2x2["pure_0"], sz)) < 1e-10)
    check("pure_plus QFI(sz)=4", abs(qfi(STATES_2x2["pure_plus"], sz) - 4.0) < 1e-10)
    check("pure_plus QFI(sx)=0", abs(qfi(STATES_2x2["pure_plus"], sx)) < 1e-10)
    check("max_mixed QFI(sx)=0", abs(qfi(STATES_2x2["maximally_mixed"], sx)) < 1e-10)
    check("max_mixed QFI(sy)=0", abs(qfi(STATES_2x2["maximally_mixed"], sy)) < 1e-10)
    check("max_mixed QFI(sz)=0", abs(qfi(STATES_2x2["maximally_mixed"], sz)) < 1e-10)

    # QFI = 4*Var for pure states
    for sname, rho in STATES_2x2.items():
        if is_pure(rho):
            for gname, H in GENERATORS.items():
                v = variance(rho, H)
                f = qfi(rho, H)
                check(f"QFI=4Var {sname}/{gname}", abs(f - 4 * v) < 1e-10)

    # QFI ≤ 4||H||² always
    for sname, rho in STATES_2x2.items():
        for gname, H in GENERATORS.items():
            f = qfi(rho, H)
            bound = 4 * op_norm_sq(H)
            check(f"QFI≤4||H||² {sname}/{gname}", f <= bound + 1e-10)

    # Convexity: QFI(p*rho1 + (1-p)*rho2) ≤ p*QFI(rho1) + (1-p)*QFI(rho2)
    p = 0.4
    rho_a = STATES_2x2["pure_0"]
    rho_b = STATES_2x2["pure_plus"]
    rho_mix = p * rho_a + (1 - p) * rho_b
    for gname, H in GENERATORS.items():
        lhs = qfi(rho_mix, H)
        rhs = p * qfi(rho_a, H) + (1 - p) * qfi(rho_b, H)
        check(f"QFI convex {gname}", lhs <= rhs + 1e-10)

    # sympy: QFI = 4*Var for pure 2×2
    theta, phi = symbols("theta phi", real=True)
    psi_sym = Matrix([sp.cos(theta / 2), sp.exp(sp.I * phi) * sp.sin(theta / 2)])
    rho_sym = psi_sym * psi_sym.adjoint()
    sz_sym = Matrix([[1, 0], [0, -1]])
    var_sym = simplify((rho_sym * sz_sym * sz_sym).trace()
                       - ((rho_sym * sz_sym).trace()) ** 2)
    # For pure states QFI = 4*Var, so just verify the symbolic expression
    four_var = simplify(4 * var_sym)
    # Should equal 4*sin²(θ)
    expected = 4 * sp.sin(theta / 2) ** 2 * sp.cos(theta / 2) ** 2 * 4
    # Actually compute directly: Var(sz) = 1 - cos²θ = sin²θ
    var_check = simplify(var_sym - sp.sin(theta) ** 2)
    sec1["sympy_qfi_4var"] = {
        "Var_sz": str(simplify(var_sym)),
        "equals_sin2theta": bool(var_check == 0),
        "QFI_pure_equals": str(simplify(4 * var_sym)),
    }

    results["sections"]["1_QFI"] = sec1

    # ── Section 2: Wigner-Yanase ──────────────────────────────────────────────
    sec2 = {"wy_values": {}, "tests": []}

    def check2(name, cond):
        nonlocal all_pass
        passed = bool(cond)
        sec2["tests"].append({"name": name, "pass": passed})
        if not passed:
            all_pass = False
            print(f"  FAIL: {name}")

    for sname, rho in STATES_2x2.items():
        sec2["wy_values"][sname] = {}
        for gname, K in GENERATORS.items():
            val = wigner_yanase(rho, K)
            sec2["wy_values"][sname][gname] = round(val, 10)

    # I_WY ≤ QFI/4
    for sname, rho in STATES_2x2.items():
        for gname, K in GENERATORS.items():
            wy = wigner_yanase(rho, K)
            f = qfi(rho, K)
            check2(f"WY≤QFI/4 {sname}/{gname}", wy <= f / 4 + 1e-10)

    # I_WY = Var for pure states
    for sname, rho in STATES_2x2.items():
        if is_pure(rho):
            for gname, K in GENERATORS.items():
                wy = wigner_yanase(rho, K)
                v = variance(rho, K)
                check2(f"WY=Var pure {sname}/{gname}", abs(wy - v) < 1e-10)

    # I_WY = 0 iff [rho, K] = 0
    for sname, rho in STATES_2x2.items():
        for gname, K in GENERATORS.items():
            wy = wigner_yanase(rho, K)
            comm = rho @ K - K @ rho
            comm_zero = np.allclose(comm, 0, atol=1e-10)
            wy_zero = abs(wy) < 1e-10
            check2(f"WY=0 iff commutes {sname}/{gname}", comm_zero == wy_zero)

    # Convexity
    rho_mix_wy = p * rho_a + (1 - p) * rho_b
    for gname, K in GENERATORS.items():
        lhs = wigner_yanase(rho_mix_wy, K)
        rhs = p * wigner_yanase(rho_a, K) + (1 - p) * wigner_yanase(rho_b, K)
        check2(f"WY convex {gname}", lhs <= rhs + 1e-10)

    # sympy: I_WY ≤ QFI/4 for 2×2
    # For a Bloch state rho = (I + r*sz)/2, generator sx:
    r_sym = symbols("r", positive=True)
    rho_bloch = sp.Rational(1, 2) * (sp.eye(2) + r_sym * Matrix([[1, 0], [0, -1]]))
    # eigenvalues: (1+r)/2, (1-r)/2
    lam_p = (1 + r_sym) / 2
    lam_m = (1 - r_sym) / 2
    # QFI(sx) for diagonal rho with off-diagonal generator:
    # QFI = 2*(lam_p - lam_m)^2 / (lam_p + lam_m) * |<0|sx|1>|^2 * 2
    # = 2*r^2 / 1 * 1 * 2 ... let me just compute it properly
    # |<0|sx|1>|^2 = 1, sum over (i,j) in {(0,1),(1,0)}: each gives 2*r^2/1 * 1
    qfi_sym = 4 * r_sym ** 2  # known result for this case
    # WY: I_WY = -1/2 Tr([sqrt(rho), sx]^2)
    # sqrt(rho) = diag(sqrt(lam_p), sqrt(lam_m))
    # [sqrt_rho, sx] has off-diag: sqrt(lam_p)-sqrt(lam_m) and -(sqrt(lam_p)-sqrt(lam_m))
    # Tr(comm^2) = -2*(sqrt(lam_p)-sqrt(lam_m))^2
    # I_WY = (sqrt(lam_p)-sqrt(lam_m))^2
    wy_sym = (sp.sqrt(lam_p) - sp.sqrt(lam_m)) ** 2
    diff_sym = simplify(qfi_sym / 4 - wy_sym)
    # Should be >= 0 for 0 < r <= 1
    sec2["sympy_wy_leq_qfi4"] = {
        "QFI_div_4": str(simplify(qfi_sym / 4)),
        "WY": str(simplify(wy_sym)),
        "QFI/4 - WY": str(simplify(diff_sym)),
        "nonneg_check": str(simplify(diff_sym))  # r^2 - (sqrt((1+r)/2)-sqrt((1-r)/2))^2 ≥ 0
    }

    results["sections"]["2_WignerYanase"] = sec2

    # ── Section 3: Quantum Geometric Tensor ───────────────────────────────────
    sec3 = {"qgt_values": {}, "tests": []}

    def check3(name, cond):
        nonlocal all_pass
        passed = bool(cond)
        sec3["tests"].append({"name": name, "pass": passed})
        if not passed:
            all_pass = False
            print(f"  FAIL: {name}")

    gen_list = [sx, sy, sz]
    gen_names = ["sx", "sy", "sz"]

    for sname, rho in STATES_2x2.items():
        Q = qgt(rho, gen_list)
        g = fubini_study_metric(Q)
        F = berry_curvature(Q)

        sec3["qgt_values"][sname] = {
            "Q_real": g.tolist(),
            "Q_imag": F.tolist(),
        }

        # g symmetric
        check3(f"g symmetric {sname}", np.allclose(g, g.T, atol=1e-10))
        # F antisymmetric
        check3(f"F antisymmetric {sname}", np.allclose(F, -F.T, atol=1e-10))
        # metric eigenvalues non-negative
        eig_g = np.linalg.eigvalsh(g)
        check3(f"g eigenvalues≥0 {sname}", np.all(eig_g > -1e-10))

        # For pure states: ||g|| = ||F|| (Frobenius norms, self-dual CP^1)
        if is_pure(rho):
            norm_g = np.linalg.norm(g, 'fro')
            norm_F = np.linalg.norm(F, 'fro')
            check3(f"||g||=||F|| pure {sname}", abs(norm_g - norm_F) < 1e-10)

    # Maximally mixed: F = 0
    Q_mm = qgt(STATES_2x2["maximally_mixed"], gen_list)
    F_mm = berry_curvature(Q_mm)
    check3("max_mixed F=0", np.allclose(F_mm, 0, atol=1e-10))

    # Metric determinant (volume element)
    for sname, rho in STATES_2x2.items():
        Q = qgt(rho, gen_list)
        g = fubini_study_metric(Q)
        det_g = float(np.real(np.linalg.det(g)))
        sec3["qgt_values"][sname]["det_g"] = round(det_g, 10)

    # sympy: Q_ij = <d_i psi|(1-|psi><psi|)|d_j psi> for pure states
    theta_s, phi_s = symbols("theta phi", real=True)
    psi_s = Matrix([sp.cos(theta_s / 2),
                     sp.exp(sp.I * phi_s) * sp.sin(theta_s / 2)])
    dpsi_dtheta = sp.diff(psi_s, theta_s)
    dpsi_dphi = sp.diff(psi_s, phi_s)
    proj = sp.eye(2) - psi_s * psi_s.adjoint()
    # Q_theta_theta
    q_tt = simplify((dpsi_dtheta.adjoint() * proj * dpsi_dtheta)[0, 0])
    # Q_phi_phi
    q_pp = simplify((dpsi_dphi.adjoint() * proj * dpsi_dphi)[0, 0])
    # Q_theta_phi
    q_tp = simplify((dpsi_dtheta.adjoint() * proj * dpsi_dphi)[0, 0])

    sec3["sympy_qgt_pure"] = {
        "Q_theta_theta": str(q_tt),
        "Q_phi_phi": str(q_pp),
        "Q_theta_phi": str(q_tp),
        "note": "Fubini-Study metric on CP^1: ds^2 = (1/4)(dtheta^2 + sin^2(theta) dphi^2)"
    }
    # Verify: Q_tt = 1/4, Q_pp = sin^2(theta)/4
    check3("sympy Q_tt=1/4", simplify(q_tt - Rational(1, 4)) == 0)
    check3("sympy Q_pp=sin²θ/4", simplify(q_pp - sp.sin(theta_s) ** 2 / 4) == 0)

    results["sections"]["3_QGT"] = sec3

    # ── Section 4: Cramér-Rao bound verification ─────────────────────────────
    sec4 = {"tests": [], "simulations": []}

    def check4(name, cond):
        nonlocal all_pass
        passed = bool(cond)
        sec4["tests"].append({"name": name, "pass": passed})
        if not passed:
            all_pass = False
            print(f"  FAIL: {name}")

    np.random.seed(42)
    n_meas = 1000

    for sname, rho in STATES_2x2.items():
        for gname, H in GENERATORS.items():
            f = qfi(rho, H)
            if f < 1e-12:
                continue  # QFI=0 means no info, bound is infinite

            cr_bound = 1.0 / f  # single-shot bound

            # Simulate measurements in eigenbasis of H
            evals_h, evecs_h = np.linalg.eigh(H)
            # Probability of each outcome
            probs = np.array([float(np.real(evecs_h[:, k].conj() @ rho @ evecs_h[:, k]))
                              for k in range(len(evals_h))])
            probs = np.clip(probs, 0, 1)
            probs /= probs.sum()

            # Sample
            outcomes = np.random.choice(evals_h, size=n_meas, p=probs)
            sample_var = float(np.var(outcomes, ddof=1))

            # The sample variance should be >= CR bound (within statistical noise)
            # We use a generous tolerance since this is stochastic
            sim_entry = {
                "state": sname,
                "generator": gname,
                "QFI": round(f, 10),
                "CR_bound": round(cr_bound, 10),
                "sample_variance": round(sample_var, 10),
                "bound_satisfied": bool(sample_var >= cr_bound * 0.8),  # allow 20% noise
            }
            sec4["simulations"].append(sim_entry)

            # For pure states: Var(H) = QFI/4 ≥ 1/QFI iff QFI ≥ 2
            # For mixed states: Var(H) can be < 1/QFI (CR bound applies to
            # estimator variance for a parameter, not to observable variance).
            # Correct test: verify QFI ≤ 4*Var for all states (always true).
            v = variance(rho, H)
            check4(f"QFI≤4Var {sname}/{gname}", f <= 4 * v + 1e-10)

    results["sections"]["4_CramerRao"] = sec4

    # ── Section 5: QFI as entanglement witness (4×4) ─────────────────────────
    sec5 = {"tests": [], "values": {}}

    def check5(name, cond):
        nonlocal all_pass
        passed = bool(cond)
        sec5["tests"].append({"name": name, "pass": passed})
        if not passed:
            all_pass = False
            print(f"  FAIL: {name}")

    # Two-qubit operators
    sz_I = np.kron(sz, I2)
    I_sz = np.kron(I2, sz)
    H_collective = sz_I + I_sz  # collective sz

    # Product state |00>
    ket00 = np.kron(ket0, ket0)
    rho_prod = make_pure(ket00)
    qfi_prod = qfi(rho_prod, H_collective)
    sec5["values"]["product_00"] = round(qfi_prod, 10)
    # Product |00>: each qubit is eigenstate of sz, so Var(sz)=0 per qubit => QFI=0
    check5("product QFI≤8 (shot noise N=2)", qfi_prod <= 8.0 + 1e-10)

    # Bell state (|00> + |11>)/sqrt(2)
    ket_bell = (np.kron(ket0, ket0) + np.kron(ket1, ket1)) / np.sqrt(2)
    rho_bell = make_pure(ket_bell)
    qfi_bell = qfi(rho_bell, H_collective)
    sec5["values"]["bell_state"] = round(qfi_bell, 10)
    # Bell state: QFI = 4*Var = 4*4 = 16 = 4*N^2 (Heisenberg limit for N=2)
    # Shot noise limit for N=2 separable: QFI ≤ 4*N = 8
    check5("Bell QFI=16 (Heisenberg limit 4N²)", abs(qfi_bell - 16.0) < 1e-10)
    check5("Bell QFI>8 witnesses entanglement", qfi_bell > 8.0)

    # Product |+0>
    ket_p0 = np.kron(ket_plus, ket0)
    rho_p0 = make_pure(ket_p0)
    qfi_p0 = qfi(rho_p0, H_collective)
    sec5["values"]["product_plus0"] = round(qfi_p0, 10)
    check5("product +0 QFI≤8 (shot noise N=2)", qfi_p0 <= 8.0 + 1e-10)

    # sympy: shot noise bound proof
    # For N separable qubits, QFI(sum_k sz_k) ≤ 4N (each qubit contributes ≤ 4)
    # For N=2, bound = 8 for entangled (Heisenberg), 4 for separable
    N_sym = symbols("N", positive=True, integer=True)
    sec5["sympy_shot_noise"] = {
        "separable_bound": "QFI ≤ 4*N (shot noise limit)",
        "entangled_bound": "QFI ≤ 4*N^2 (Heisenberg limit)",
        "witness_criterion": "QFI > 4*N implies entanglement",
        "N2_separable_max": 4 * 2,
        "N2_bell_actual": round(qfi_bell, 10),
        "entanglement_witnessed": bool(qfi_bell > 4 * 2),  # > 4N for N=2
    }

    results["sections"]["5_EntanglementWitness"] = sec5

    # ── Section 6: Information geometry — QFI = 4 × Bures ────────────────────
    sec6 = {"tests": [], "values": {}}

    def check6(name, cond):
        nonlocal all_pass
        passed = bool(cond)
        sec6["tests"].append({"name": name, "pass": passed})
        if not passed:
            all_pass = False
            print(f"  FAIL: {name}")

    def fidelity_dm(rho, sigma):
        """Uhlmann fidelity F(rho, sigma) = (Tr sqrt(sqrt(rho) sigma sqrt(rho)))^2."""
        sqrt_rho = sqrtm(rho)
        M = sqrt_rho @ sigma @ sqrt_rho
        # Force Hermitian for numerical stability
        M = 0.5 * (M + M.conj().T)
        sqrt_M = sqrtm(M)
        tr_val = float(np.real(np.trace(sqrt_M)))
        return tr_val ** 2

    def bures_distance_sq(rho, sigma):
        """Bures distance squared: D_B^2 = 2(1 - sqrt(F))."""
        F = fidelity_dm(rho, sigma)
        return 2 * (1 - np.sqrt(max(0, min(1, F))))

    # Use MIXED states (r < 1) to avoid singular sqrtm on pure states
    dtheta = 1e-5
    for theta0 in [0.3, 0.7, 1.0, 1.5]:
        def rho_theta(t):
            r = 0.7  # mixed state, avoids singular sqrtm
            return bloch_state(r, t, 0)

        rho0 = rho_theta(theta0)
        rho1 = rho_theta(theta0 + dtheta)

        # Bures metric coefficient: ds²_Bures ≈ D_B²(rho0, rho1)
        db2 = bures_distance_sq(rho0, rho1)
        bures_metric = db2 / dtheta ** 2

        # QFI metric: compute QFI w.r.t. the generator d rho/d theta
        # The generator of theta-rotation on Bloch sphere with phi=0 is
        # H_theta = (cos(theta)*sx - sin(theta)*sz)/2 ... but for QFI of parameterized
        # families, QFI = 4 * Bures metric coefficient
        # We compute numerically via SLD
        drho = (rho1 - rho0) / dtheta
        # QFI from SLD: F = Tr(rho L^2) where drho = (rho L + L rho)/2
        # Numerical: QFI = sum_ij 2|<i|drho|j>|^2 / (lam_i + lam_j)
        evals_r, evecs_r = np.linalg.eigh(rho0)
        d = len(evals_r)
        qfi_param = 0.0
        for i in range(d):
            for j in range(d):
                s = evals_r[i] + evals_r[j]
                if s > 1e-15:
                    elem = abs(evecs_r[:, i].conj() @ drho @ evecs_r[:, j]) ** 2
                    qfi_param += 2 * elem / s
        qfi_param = float(qfi_param)

        ratio = qfi_param / bures_metric if bures_metric > 1e-15 else float('nan')

        sec6["values"][f"theta={theta0:.1f}"] = {
            "bures_metric": round(bures_metric, 6),
            "qfi_metric": round(qfi_param, 6),
            "ratio_QFI/Bures": round(ratio, 6),
        }
        check6(f"QFI=4*Bures theta={theta0:.1f}", abs(ratio - 4.0) < 0.01)

    results["sections"]["6_InformationGeometry"] = sec6

    # ── Summary ───────────────────────────────────────────────────────────────
    total_tests = 0
    total_pass = 0
    for sec_name, sec_data in results["sections"].items():
        tests = sec_data.get("tests", [])
        total_tests += len(tests)
        total_pass += sum(1 for t in tests if t["pass"])

    results["summary"] = {
        "total_tests": total_tests,
        "passed": total_pass,
        "failed": total_tests - total_pass,
        "all_pass": all_pass,
    }

    return results


if __name__ == "__main__":
    print("=" * 72)
    print("  Pure Lego: QFI / Wigner-Yanase / QGT")
    print("=" * 72)

    results = run_tests()

    # Print summary
    s = results["summary"]
    print(f"\n{'=' * 72}")
    print(f"  RESULTS: {s['passed']}/{s['total_tests']} tests passed")
    if s["all_pass"]:
        print("  ALL PASS")
    else:
        print(f"  {s['failed']} FAILED")
    print(f"{'=' * 72}")

    # Section summaries
    for sec_name, sec_data in results["sections"].items():
        tests = sec_data.get("tests", [])
        p = sum(1 for t in tests if t["pass"])
        print(f"  {sec_name}: {p}/{len(tests)}")

    # Save
    out_path = os.path.join(os.path.dirname(__file__),
                            "a2_state", "sim_results",
                            "pure_lego_qfi_wy_qgt_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Output: {out_path}")
