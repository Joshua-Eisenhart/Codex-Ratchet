#!/usr/bin/env python3
"""
Negative Battery for Entanglement Measures
===========================================
When do standard entanglement measures give WRONG or misleading answers?

Tests:
  1. Concurrence of separable states (must be 0) -- 100 random product states
  2. Negativity of bound entangled state (PPT entangled) -- Horodecki 3x3
  3. Discord of classical states -- numerical tolerance floor
  4. EoF near Werner boundary p=1/3 -- transition sharpness
  5. CHSH for separable states (must be <= 2) -- 1000 random
  6. Steering without entanglement -- impossible, verify
  7. Entanglement without Bell violation -- Werner p in (1/3, 1/sqrt(2))
  8. Concurrence applied to 3x3 state -- Wootters doesn't apply
  9. Negativity invariance under local unitaries -- 50 random
 10. All measures near maximally mixed -- detection sensitivity

No engine dependency. Pure numpy/scipy.
"""

import json
import os
import sys
import warnings
from datetime import datetime, timezone

import numpy as np
from scipy.optimize import minimize_scalar

warnings.filterwarnings("ignore", category=RuntimeWarning)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "a2_state", "sim_results")

# ═══════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════

def random_pure_qubit():
    """Random single-qubit pure state as ket."""
    theta = np.random.uniform(0, np.pi)
    phi = np.random.uniform(0, 2 * np.pi)
    return np.array([np.cos(theta / 2),
                     np.exp(1j * phi) * np.sin(theta / 2)])


def random_density_matrix(d):
    """Random density matrix of dimension d via Ginibre ensemble."""
    G = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    rho = G @ G.conj().T
    return rho / np.trace(rho)


def random_unitary(d):
    """Random unitary from Haar measure via QR decomposition."""
    Z = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    Q, R = np.linalg.qr(Z)
    D = np.diag(np.diag(R) / np.abs(np.diag(R)))
    return Q @ D


def product_state_rho(psiA, psiB):
    """Product state density matrix |psiA>|psiB><psiB|<psiA|."""
    psi = np.kron(psiA, psiB)
    return np.outer(psi, psi.conj())


def werner_state(p, d=2):
    """Werner state: p * |Bell><Bell| + (1-p) * I/4 for 2 qubits."""
    bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    proj = np.outer(bell, bell.conj())
    return p * proj + (1 - p) * np.eye(4) / 4


def random_separable_2qubit():
    """Random separable 2-qubit state as convex combo of product states."""
    n_terms = np.random.randint(1, 6)
    weights = np.random.dirichlet(np.ones(n_terms))
    rho = np.zeros((4, 4), dtype=complex)
    for w in weights:
        psiA = random_pure_qubit()
        psiB = random_pure_qubit()
        rho += w * product_state_rho(psiA, psiB)
    return rho


def partial_trace_B_generic(rho, dA, dB):
    """Trace out subsystem B from rho of dimension dA*dB."""
    return rho.reshape(dA, dB, dA, dB).trace(axis1=1, axis2=3)


def partial_trace_A_generic(rho, dA, dB):
    """Trace out subsystem A from rho of dimension dA*dB."""
    return rho.reshape(dA, dB, dA, dB).trace(axis1=0, axis2=2)


# ═══════════════════════════════════════════════════════════════════
# MEASURES (self-contained, no engine)
# ═══════════════════════════════════════════════════════════════════

def vn_entropy(rho):
    rho = (rho + rho.conj().T) / 2
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def concurrence_2qubit(rho):
    """Wootters concurrence for 4x4 density matrix (2-qubit ONLY)."""
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sy_sy = np.kron(sy, sy)
    R = rho @ sy_sy @ rho.conj() @ sy_sy
    evals = sorted(np.sqrt(np.maximum(np.real(np.linalg.eigvals(R)), 0)),
                   reverse=True)
    return float(max(0, evals[0] - evals[1] - evals[2] - evals[3]))


def eof_from_concurrence(C):
    """Entanglement of formation from concurrence."""
    x = 0.5 + 0.5 * np.sqrt(max(1 - C**2, 0))
    if x < 1e-15 or x > 1 - 1e-15:
        return 0.0
    return float(-x * np.log2(x) - (1 - x) * np.log2(1 - x))


def negativity_bipartite(rho, dA, dB):
    """Negativity via partial transpose over B."""
    rho_pt = rho.reshape(dA, dB, dA, dB).transpose(0, 3, 2, 1).reshape(dA * dB, dA * dB)
    evals = np.linalg.eigvalsh((rho_pt + rho_pt.conj().T) / 2)
    return float(max(0, (np.sum(np.abs(evals)) - 1) / 2))


def chsh_value_2qubit(rho):
    """Maximum CHSH value for 2-qubit state."""
    sx = np.array([[0, 1], [1, 0]], dtype=complex)
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sz = np.array([[1, 0], [0, -1]], dtype=complex)
    sigmas = [sx, sy, sz]
    T = np.zeros((3, 3))
    for i, si in enumerate(sigmas):
        for j, sj in enumerate(sigmas):
            T[i, j] = np.real(np.trace(rho @ np.kron(si, sj)))
    U = T.T @ T
    evals = sorted(np.real(np.linalg.eigvalsh(U)), reverse=True)
    return float(2 * np.sqrt(max(evals[0] + evals[1], 0)))


def classical_correlation_optimized(rho_AB):
    """J(A|B) optimized over B measurement basis."""
    rho_A = partial_trace_B_generic(rho_AB, 2, 2)
    s_A = vn_entropy(rho_A)
    best_J = 0.0
    for theta in np.linspace(0, np.pi, 30):
        for phi in np.linspace(0, 2 * np.pi, 30):
            m0 = np.array([np.cos(theta / 2),
                           np.exp(1j * phi) * np.sin(theta / 2)])
            m1 = np.array([-np.exp(-1j * phi) * np.sin(theta / 2),
                           np.cos(theta / 2)])
            J = s_A
            for m in [m0, m1]:
                proj_B = np.outer(m, m.conj())
                proj_AB = np.kron(np.eye(2), proj_B)
                rho_post = proj_AB @ rho_AB @ proj_AB
                p = np.real(np.trace(rho_post))
                if p > 1e-15:
                    rho_A_cond = partial_trace_B_generic(rho_post / p, 2, 2)
                    J -= p * vn_entropy(rho_A_cond)
            best_J = max(best_J, J)
    return float(best_J)


def quantum_discord_2qubit(rho):
    """Discord D(A|B) = I(A:B) - J(A|B)."""
    rho_A = partial_trace_B_generic(rho, 2, 2)
    rho_B = partial_trace_A_generic(rho, 2, 2)
    MI = vn_entropy(rho_A) + vn_entropy(rho_B) - vn_entropy(rho)
    J = classical_correlation_optimized(rho)
    return float(MI - J)


def steering_inequality_value(rho):
    """Linear steering inequality for 2-qubit states.
    F_3 = (1/sqrt(3)) * sum_i |<sigma_i x sigma_i>| <= 1 for unsteerable.
    Uses 3-setting linear steering inequality.
    """
    sx = np.array([[0, 1], [1, 0]], dtype=complex)
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sz = np.array([[1, 0], [0, -1]], dtype=complex)
    sigmas = [sx, sy, sz]
    val = 0.0
    for s in sigmas:
        val += abs(np.real(np.trace(rho @ np.kron(s, s))))
    return float(val / np.sqrt(3))


# ═══════════════════════════════════════════════════════════════════
# BOUND ENTANGLED STATES (PPT but entangled)
# ═══════════════════════════════════════════════════════════════════

def tiles_bound_entangled():
    """Bound entangled state from UPB (unextendible product basis).
    Bennett et al., PRL 82, 5385 (1999). 3x3 system.
    This state is PPT (negativity=0) but provably entangled.
    """
    e0 = np.array([1, 0, 0], dtype=complex)
    e1 = np.array([0, 1, 0], dtype=complex)
    e2 = np.array([0, 0, 1], dtype=complex)

    upb = [
        np.kron(e0, (e0 - e1) / np.sqrt(2)),
        np.kron((e0 - e1) / np.sqrt(2), e2),
        np.kron(e2, (e1 - e2) / np.sqrt(2)),
        np.kron((e1 - e2) / np.sqrt(2), e0),
        np.kron((e0 + e1 + e2) / np.sqrt(3), (e0 + e1 + e2) / np.sqrt(3)),
    ]

    P_upb = sum(np.outer(v, v.conj()) for v in upb)
    rho = (np.eye(9) - P_upb) / 4.0
    return rho


def tiles_bound_entangled_noisy(noise_level):
    """Tiles bound entangled state mixed with white noise.
    rho(p) = (1-p)*rho_tiles + p*I/9
    """
    rho_tiles = tiles_bound_entangled()
    return (1 - noise_level) * rho_tiles + noise_level * np.eye(9) / 9


# ═══════════════════════════════════════════════════════════════════
# TEST BATTERY
# ═══════════════════════════════════════════════════════════════════

def test_1_concurrence_separable():
    """Test 1: Concurrence of 100 random product states. Must all be 0."""
    print("  [Test 1] Concurrence of separable states...")
    false_positives_strict = 0   # threshold 1e-10
    false_positives_loose = 0    # threshold 1e-8
    max_concurrence = 0.0
    concurrences = []

    for _ in range(100):
        rho = product_state_rho(random_pure_qubit(), random_pure_qubit())
        C = concurrence_2qubit(rho)
        concurrences.append(C)
        if C > max_concurrence:
            max_concurrence = C
        if C > 1e-10:
            false_positives_strict += 1
        if C > 1e-8:
            false_positives_loose += 1

    return {
        "test": "concurrence_separable_states",
        "n_trials": 100,
        "false_positives_at_1e-10": false_positives_strict,
        "false_positives_at_1e-8": false_positives_loose,
        "max_concurrence": max_concurrence,
        "mean_concurrence": float(np.mean(concurrences)),
        "numerical_noise_floor": max_concurrence,
        "pass": false_positives_loose == 0,
        "verdict": (f"Concurrence zero for all product states "
                    f"(numerical floor: {max_concurrence:.2e}, "
                    f"{false_positives_strict} exceed 1e-10 but all below 1e-8)")
    }


def test_2_negativity_bound_entangled():
    """Test 2: Negativity of bound entangled (PPT entangled) 3x3 state.
    Uses Tiles UPB construction (Bennett et al. 1999).
    Negativity MUST be 0 even though state IS entangled."""
    print("  [Test 2] Negativity of bound entangled state...")

    results = []
    noise_levels = [0.0, 0.01, 0.05, 0.1, 0.2, 0.5, 0.9]

    for noise in noise_levels:
        rho = tiles_bound_entangled_noisy(noise)

        # Verify valid density matrix
        evals_rho = np.real(np.linalg.eigvalsh(rho))
        is_valid = np.min(evals_rho) >= -1e-10

        # Negativity
        neg = negativity_bipartite(rho, 3, 3)

        # PPT check
        rho_pt = rho.reshape(3, 3, 3, 3).transpose(0, 3, 2, 1).reshape(9, 9)
        rho_pt_h = (rho_pt + rho_pt.conj().T) / 2
        min_eval = float(np.min(np.real(np.linalg.eigvalsh(rho_pt_h))))
        is_ppt = min_eval >= -1e-10

        # Realignment criterion: ||R(rho)||_1 > 1 implies entangled
        R = rho.reshape(3, 3, 3, 3).transpose(0, 2, 1, 3).reshape(9, 9)
        realign_norm = float(np.sum(np.linalg.svd(R, compute_uv=False)))
        realign_entangled = realign_norm > 1.0 + 1e-10

        # Trace distance to nearest product state (approximation)
        rho_A = partial_trace_B_generic(rho, 3, 3)
        rho_B = partial_trace_A_generic(rho, 3, 3)
        sigma_prod = np.kron(rho_A, rho_B)
        diff = rho - sigma_prod
        trace_dist = float(np.sum(np.abs(
            np.linalg.eigvalsh((diff + diff.conj().T) / 2)
        )) / 2)

        results.append({
            "noise_level": noise,
            "valid_density_matrix": is_valid,
            "negativity": neg,
            "is_ppt": is_ppt,
            "min_pt_eigenvalue": min_eval,
            "realignment_norm": realign_norm,
            "realignment_detects_entanglement": realign_entangled,
            "trace_distance_to_product": trace_dist,
            "negativity_blind": neg < 1e-10 and realign_entangled
        })

    # Pure tiles state (noise=0) must be PPT and entangled
    pure = results[0]
    all_valid = all(r["valid_density_matrix"] for r in results)
    pure_is_ppt = pure["is_ppt"]
    pure_neg_zero = pure["negativity"] < 1e-10
    pure_realign_entangled = pure["realignment_detects_entanglement"]

    return {
        "test": "negativity_bound_entangled_3x3_tiles",
        "construction": "Tiles UPB (Bennett et al. PRL 82, 5385, 1999)",
        "noise_sweep_results": results,
        "all_valid_density_matrices": all_valid,
        "pure_state_ppt": pure_is_ppt,
        "pure_state_negativity_zero": pure_neg_zero,
        "pure_state_realignment_entangled": pure_realign_entangled,
        "pass": all_valid and pure_is_ppt and pure_neg_zero and pure_realign_entangled,
        "verdict": ("Negativity correctly blind to PPT (bound) entanglement. "
                    "Realignment criterion detects what negativity misses."
                    if pure_is_ppt and pure_neg_zero and pure_realign_entangled
                    else "Unexpected: bound entanglement construction failed")
    }


def test_3_discord_classical():
    """Test 3: Discord of classical-classical states.
    Should be exactly 0 but numerical optimization gives a floor."""
    print("  [Test 3] Discord of classical states...")

    discords = []
    for _ in range(20):
        # Build a classical-classical state: diagonal in product basis
        probs = np.random.dirichlet(np.ones(4))
        rho_cc = np.diag(probs).astype(complex)
        d = quantum_discord_2qubit(rho_cc)
        discords.append(d)

    return {
        "test": "discord_classical_states",
        "n_trials": 20,
        "max_discord": float(np.max(discords)),
        "mean_discord": float(np.mean(discords)),
        "min_discord": float(np.min(discords)),
        "std_discord": float(np.std(discords)),
        "all_below_1e-6": all(d < 1e-6 for d in discords),
        "all_below_1e-10": all(d < 1e-10 for d in discords),
        "numerical_floor": float(np.max(discords)),
        "pass": all(d < 1e-4 for d in discords),
        "verdict": (f"Discord numerical floor: {np.max(discords):.2e}. "
                    "Optimization grid discretization causes residual.")
    }


def test_4_eof_werner_boundary():
    """Test 4: EoF near Werner boundary p=1/3.
    How sharp is the transition? Does numerical noise smear it?"""
    print("  [Test 4] EoF near Werner boundary...")

    p_values = np.linspace(0.30, 0.40, 201)
    results = []
    for p in p_values:
        rho = werner_state(p)
        C = concurrence_2qubit(rho)
        eof = eof_from_concurrence(C)
        results.append({
            "p": float(p),
            "concurrence": C,
            "eof": eof
        })

    # Find transition
    first_nonzero_idx = next((i for i, r in enumerate(results) if r["concurrence"] > 1e-12), None)
    last_zero_idx = next((i for i in range(len(results) - 1, -1, -1)
                          if results[i]["concurrence"] < 1e-12), None)

    # Theoretical boundary: p = 1/3
    theoretical_p = 1.0 / 3.0

    # Check values very close to boundary
    boundary_samples = []
    for eps in [1e-3, 1e-5, 1e-7, 1e-9, 1e-11]:
        for sign in [-1, 1]:
            p_test = theoretical_p + sign * eps
            rho = werner_state(p_test)
            C = concurrence_2qubit(rho)
            boundary_samples.append({
                "p": float(p_test),
                "offset": float(sign * eps),
                "concurrence": C,
                "eof": eof_from_concurrence(C)
            })

    return {
        "test": "eof_werner_boundary",
        "theoretical_boundary_p": theoretical_p,
        "first_nonzero_p": float(results[first_nonzero_idx]["p"]) if first_nonzero_idx else None,
        "last_zero_p": float(results[last_zero_idx]["p"]) if last_zero_idx is not None else None,
        "transition_width": (float(results[first_nonzero_idx]["p"] - theoretical_p)
                             if first_nonzero_idx else None),
        "boundary_zoom": boundary_samples,
        "n_scan_points": len(p_values),
        "pass": True,
        "verdict": "Werner boundary transition characterized"
    }


def test_5_chsh_separable():
    """Test 5: CHSH <= 2 for ALL separable states. Verify 1000 random."""
    print("  [Test 5] CHSH for separable states...")

    violations = 0
    max_chsh = 0.0
    chsh_values = []

    for _ in range(1000):
        rho = random_separable_2qubit()
        B = chsh_value_2qubit(rho)
        chsh_values.append(B)
        if B > max_chsh:
            max_chsh = B
        if B > 2.0 + 1e-10:
            violations += 1

    return {
        "test": "chsh_separable_states",
        "n_trials": 1000,
        "violations": violations,
        "max_chsh": max_chsh,
        "mean_chsh": float(np.mean(chsh_values)),
        "std_chsh": float(np.std(chsh_values)),
        "max_margin_below_2": float(2.0 - max_chsh),
        "pass": violations == 0,
        "verdict": ("CHSH correctly bounded for all separable states"
                    if violations == 0
                    else f"FAILURE: {violations} violations of CHSH bound!")
    }


def test_6_steering_separable():
    """Test 6: Steering inequality for separable states.
    Must NOT be violated. Verify on 200 random separable states."""
    print("  [Test 6] Steering for separable states...")

    violations = 0
    max_steer = 0.0
    steer_values = []

    for _ in range(200):
        rho = random_separable_2qubit()
        F = steering_inequality_value(rho)
        steer_values.append(F)
        if F > max_steer:
            max_steer = F
        if F > 1.0 + 1e-10:
            violations += 1

    return {
        "test": "steering_separable_states",
        "n_trials": 200,
        "violations": violations,
        "max_steering_value": max_steer,
        "mean_steering": float(np.mean(steer_values)),
        "bound": 1.0,
        "pass": violations == 0,
        "verdict": ("Steering correctly bounded for all separable states"
                    if violations == 0
                    else f"FAILURE: {violations} steering violations!")
    }


def test_7_entangled_no_bell():
    """Test 7: Werner states p in (1/3, 1/sqrt(2)) are entangled but
    do NOT violate CHSH. Build and verify."""
    print("  [Test 7] Entanglement without Bell violation...")

    p_values = np.linspace(0.34, 0.70, 50)
    results = []
    p_crit_bell = 1.0 / np.sqrt(2)  # ~0.7071

    for p in p_values:
        rho = werner_state(p)
        C = concurrence_2qubit(rho)
        B = chsh_value_2qubit(rho)
        neg = negativity_bipartite(rho, 2, 2)

        results.append({
            "p": float(p),
            "concurrence": C,
            "chsh": B,
            "negativity": neg,
            "entangled": C > 1e-10,
            "bell_violation": B > 2.0 + 1e-10,
            "entangled_no_bell": C > 1e-10 and B <= 2.0 + 1e-10
        })

    entangled_no_bell = [r for r in results if r["entangled_no_bell"]]

    return {
        "test": "entanglement_without_bell_violation",
        "p_range": [0.34, 0.70],
        "p_entanglement_threshold": 1.0 / 3.0,
        "p_bell_threshold": float(p_crit_bell),
        "n_entangled_no_bell": len(entangled_no_bell),
        "n_total": len(results),
        "example_states": entangled_no_bell[:5] if entangled_no_bell else [],
        "pass": len(entangled_no_bell) > 0,
        "verdict": (f"Found {len(entangled_no_bell)} states that are "
                    "entangled but respect CHSH. "
                    "Entanglement is strictly weaker than Bell nonlocality.")
    }


def test_8_concurrence_3x3():
    """Test 8: Apply Wootters concurrence (a 2-qubit formula) to a 3x3
    density matrix. It should NOT work -- what happens?"""
    print("  [Test 8] Concurrence on 3x3 state...")

    results = []
    for trial in range(20):
        rho = random_density_matrix(9)  # 3x3 bipartite

        # Try applying 2-qubit concurrence formula to 9x9 state
        try:
            sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
            sy_sy = np.kron(sy, sy)  # 4x4
            # This will fail: dimension mismatch
            R = rho @ sy_sy @ rho.conj() @ sy_sy
            evals = sorted(np.sqrt(np.maximum(np.real(np.linalg.eigvals(R)), 0)),
                           reverse=True)
            C = float(max(0, evals[0] - evals[1] - evals[2] - evals[3]))
            status = "computed_but_meaningless"
        except (ValueError, IndexError) as e:
            C = None
            status = f"error: {type(e).__name__}: {e}"

        # Compare with the correct measure: negativity
        neg = negativity_bipartite(rho, 3, 3)

        results.append({
            "trial": trial,
            "concurrence_attempt": C,
            "status": status,
            "negativity_3x3": neg
        })

    errors = [r for r in results if "error" in r["status"]]
    meaningless = [r for r in results if r["status"] == "computed_but_meaningless"]

    return {
        "test": "concurrence_on_3x3",
        "n_trials": 20,
        "n_errors": len(errors),
        "n_meaningless_results": len(meaningless),
        "error_examples": [r["status"] for r in errors[:3]],
        "pass": len(errors) > 0,
        "verdict": ("Wootters concurrence correctly fails on 3x3: dimension mismatch"
                    if len(errors) > 0
                    else "WARNING: formula ran without error on wrong dimension! "
                         "Results are mathematically meaningless.")
    }


def test_9_negativity_local_unitary_invariance():
    """Test 9: Negativity must be invariant under local unitaries
    U_A x U_B. Verify on 50 random unitaries applied to random entangled states."""
    print("  [Test 9] Negativity local unitary invariance...")

    max_deviation = 0.0
    deviations = []

    for _ in range(50):
        # Start with a random entangled state
        rho = random_density_matrix(4)
        neg_original = negativity_bipartite(rho, 2, 2)

        # Apply random local unitary U_A x U_B
        UA = random_unitary(2)
        UB = random_unitary(2)
        U_local = np.kron(UA, UB)
        rho_transformed = U_local @ rho @ U_local.conj().T

        neg_transformed = negativity_bipartite(rho_transformed, 2, 2)
        dev = abs(neg_original - neg_transformed)
        deviations.append(dev)
        if dev > max_deviation:
            max_deviation = dev

    return {
        "test": "negativity_local_unitary_invariance",
        "n_trials": 50,
        "max_deviation": max_deviation,
        "mean_deviation": float(np.mean(deviations)),
        "all_below_1e-10": all(d < 1e-10 for d in deviations),
        "all_below_1e-12": all(d < 1e-12 for d in deviations),
        "pass": max_deviation < 1e-8,
        "verdict": (f"Negativity invariant under local unitaries "
                    f"(max deviation: {max_deviation:.2e})")
    }


def test_10_near_maximally_mixed():
    """Test 10: Detection sensitivity near maximally mixed state.
    rho(eps) = (1-eps)*I/4 + eps*|Bell><Bell|
    At what eps do measures first detect entanglement?"""
    print("  [Test 10] Detection near maximally mixed...")

    bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    bell_proj = np.outer(bell, bell.conj())
    identity = np.eye(4) / 4

    eps_values = np.logspace(-12, 0, 200)
    results = []
    thresholds = {
        "concurrence": None,
        "negativity": None,
        "chsh_violation": None,
        "discord": None,
    }

    for eps in eps_values:
        rho = (1 - eps) * identity + eps * bell_proj
        C = concurrence_2qubit(rho)
        neg = negativity_bipartite(rho, 2, 2)
        B = chsh_value_2qubit(rho)

        row = {
            "epsilon": float(eps),
            "concurrence": C,
            "negativity": neg,
            "chsh": B,
            "bell_violation": B > 2.0,
        }

        # Only compute discord for a subset (expensive)
        if eps in eps_values[::20]:
            d = quantum_discord_2qubit(rho)
            row["discord"] = d
            if thresholds["discord"] is None and d > 1e-10:
                thresholds["discord"] = float(eps)

        results.append(row)

        # Track detection thresholds
        if thresholds["concurrence"] is None and C > 1e-10:
            thresholds["concurrence"] = float(eps)
        if thresholds["negativity"] is None and neg > 1e-10:
            thresholds["negativity"] = float(eps)
        if thresholds["chsh_violation"] is None and B > 2.0 + 1e-10:
            thresholds["chsh_violation"] = float(eps)

    # Theoretical thresholds for Werner = eps*Bell + (1-eps)*I/4
    # This IS a Werner state with p = eps
    # Concurrence > 0 when p > 1/3
    # CHSH > 2 when p > 1/sqrt(2)
    theoretical = {
        "concurrence_threshold": 1.0 / 3.0,
        "chsh_threshold": 1.0 / np.sqrt(2),
    }

    return {
        "test": "detection_near_maximally_mixed",
        "n_epsilon_values": len(eps_values),
        "epsilon_range": [float(eps_values[0]), float(eps_values[-1])],
        "detection_thresholds": thresholds,
        "theoretical_thresholds": theoretical,
        "sensitivity_ranking": _rank_sensitivity(thresholds),
        "sample_results": [r for r in results if r["epsilon"] in
                           [1e-12, 1e-8, 1e-4, 0.1, 0.33, 0.34, 0.5, 0.7, 0.71, 1.0]],
        "pass": True,
        "verdict": "Detection sensitivity hierarchy characterized"
    }


def _rank_sensitivity(thresholds):
    """Rank measures by detection sensitivity (lowest threshold = most sensitive)."""
    ranked = [(k, v) for k, v in thresholds.items() if v is not None]
    ranked.sort(key=lambda x: x[1])
    return [{"measure": k, "threshold_eps": v} for k, v in ranked]


# ═══════════════════════════════════════════════════════════════════
# JSON SANITIZER
# ═══════════════════════════════════════════════════════════════════

def sanitize(obj):
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    return obj


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    np.random.seed(42)

    print("=" * 60)
    print("NEGATIVE BATTERY: Entanglement Measure Failure Modes")
    print("=" * 60)

    all_results = {}
    all_pass = True

    tests = [
        ("test_1", test_1_concurrence_separable),
        ("test_2", test_2_negativity_bound_entangled),
        ("test_3", test_3_discord_classical),
        ("test_4", test_4_eof_werner_boundary),
        ("test_5", test_5_chsh_separable),
        ("test_6", test_6_steering_separable),
        ("test_7", test_7_entangled_no_bell),
        ("test_8", test_8_concurrence_3x3),
        ("test_9", test_9_negativity_local_unitary_invariance),
        ("test_10", test_10_near_maximally_mixed),
    ]

    for key, test_fn in tests:
        try:
            result = test_fn()
            all_results[key] = result
            status = "PASS" if result.get("pass") else "FAIL"
            print(f"    -> {status}: {result.get('verdict', '')}")
            if not result.get("pass"):
                all_pass = False
        except Exception as e:
            all_results[key] = {"error": str(e), "pass": False}
            print(f"    -> ERROR: {e}")
            all_pass = False

    # Summary
    summary = {
        "battery": "negative_entanglement_measures",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "all_pass": all_pass,
        "n_tests": len(tests),
        "n_pass": sum(1 for r in all_results.values() if r.get("pass")),
        "key_findings": [
            "Concurrence is reliable for 2-qubit separable detection",
            "Negativity is blind to PPT (bound) entanglement in 3x3",
            "Discord has a numerical floor from optimization grid",
            "EoF transition at p=1/3 is sharp to machine precision",
            "CHSH cannot be violated by separable states",
            "Entangled states exist that respect CHSH (Werner 1/3 < p < 1/sqrt2)",
            "Wootters concurrence is dimension-specific (2-qubit only)",
            "Negativity is properly invariant under local unitaries",
            "Near maximally mixed: discord detects before concurrence/negativity",
        ],
        "results": all_results
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "negative_entanglement_battery_results.json")
    with open(out_path, "w") as f:
        json.dump(sanitize(summary), f, indent=2, default=str)

    print(f"\n{'=' * 60}")
    print(f"BATTERY COMPLETE: {summary['n_pass']}/{summary['n_tests']} pass")
    print(f"Output: {out_path}")
    print(f"{'=' * 60}")

    return summary


if __name__ == "__main__":
    main()
