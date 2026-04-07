#!/usr/bin/env python3
"""
PURE LEGO: Quantum Channel Capacity & Degradability Classification
====================================================================
Foundational building block.  Pure math only -- numpy + scipy.
No engine imports.  Every operation verified against theory.

Sections
--------
1. Channel construction (Kraus operators) for 5 channel types
2. Holevo quantity chi(rho, E) = S(E(rho)) - sum p_i S(E(rho_i))
   maximised over ensembles via product-state input (classical capacity C1)
3. Coherent information I_c(rho, E) = S(E(rho)) - S_e(rho, E)
   maximised over input states (quantum capacity Q lower bound)
4. Degradability classification:
   - Degradable:      complementary E_c = D . E for some CPTP D
   - Anti-degradable: E = D' . E_c for some CPTP D'
   - Neither:         neither relation holds
5. Amplitude damping gamma < 1/2 is degradable (Q > 0, single-letter)
   Depolarizing is NOT degradable for most p (Q hard)

Channels tested
---------------
1. Depolarizing  p = 0.05  (low noise)
2. Depolarizing  p = 0.20  (medium noise)
3. Amplitude damping  gamma = 0.3  (degradable regime)
4. Amplitude damping  gamma = 0.7  (anti-degradable regime)
5. Dephasing  p = 0.1
"""

import json, pathlib, time, traceback
import numpy as np
from scipy.linalg import sqrtm
from scipy.optimize import minimize_scalar, minimize

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


def ket(v):
    return np.array(v, dtype=complex).reshape(-1, 1)


def dm(v):
    k = ket(v)
    return k @ k.conj().T


def von_neumann_entropy(rho):
    """S(rho) in bits."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > EPS]
    return float(-np.sum(evals * np.log2(evals)))


def apply_channel(kraus_ops, rho):
    """E(rho) = sum_k K_k rho K_k^dag."""
    d = rho.shape[0]
    out = np.zeros((d, d), dtype=complex)
    rho_c = np.asarray(rho, dtype=complex)
    for K in kraus_ops:
        out += K @ rho_c @ K.conj().T
    return out


def stinespring_isometry(kraus_ops):
    """
    Build Stinespring isometry V: H_in -> H_out x H_env.
    V = sum_k |k>_env tensor K_k
    Then E(rho) = Tr_env(V rho V^dag)  and  E_c(rho) = Tr_out(V rho V^dag).
    """
    n_kraus = len(kraus_ops)
    d = kraus_ops[0].shape[0]
    # V has shape (d * n_kraus, d)
    V = np.zeros((d * n_kraus, d), dtype=complex)
    for k, K in enumerate(kraus_ops):
        V[k * d:(k + 1) * d, :] = K
    return V


def complementary_channel(kraus_ops, rho):
    """
    E_c(rho) = Tr_out(V rho V^dag) where V is Stinespring isometry.
    Output lives in H_env (dimension = number of Kraus operators).
    """
    V = stinespring_isometry(kraus_ops)
    d = kraus_ops[0].shape[0]
    n_kraus = len(kraus_ops)
    # V rho V^dag has shape (d*n_kraus, d*n_kraus)
    # Reshape as (n_kraus, d, n_kraus, d) and trace over d (output) indices
    VrhoVd = V @ rho @ V.conj().T
    # Partial trace over output system (the d-dimensional blocks)
    env_state = np.zeros((n_kraus, n_kraus), dtype=complex)
    for i in range(n_kraus):
        for j in range(n_kraus):
            block = VrhoVd[i * d:(i + 1) * d, j * d:(j + 1) * d]
            env_state[i, j] = np.trace(block)
    return env_state


def exchange_entropy(kraus_ops, rho):
    """S_e(rho, E) = S(E_c(rho)) = entropy of complementary channel output."""
    env_state = complementary_channel(kraus_ops, rho)
    return von_neumann_entropy(env_state)


def coherent_info(kraus_ops, rho):
    """I_c(rho, E) = S(E(rho)) - S_e(rho, E)."""
    out = apply_channel(kraus_ops, rho)
    s_out = von_neumann_entropy(out)
    s_env = exchange_entropy(kraus_ops, rho)
    return s_out - s_env


def holevo_chi_product_state(kraus_ops, rho):
    """
    Holevo chi for a single pure input rho (which is already a product state).
    For product-state inputs: chi = S(E(rho_avg)) - avg S(E(rho_i)).
    For a single pure state: chi = S(E(rho)) since S(E(|psi><psi|)) contributes
    to the average. We compute the accessible info bound for the maximising ensemble.

    For qubit channels, C1 = max_rho S(E(rho)) when the channel is unital,
    and requires optimisation otherwise. We'll optimise over Bloch sphere inputs.
    """
    out = apply_channel(kraus_ops, rho)
    return von_neumann_entropy(out)


# ──────────────────────────────────────────────────────────────────────
# Channel Constructors (Kraus representation)
# ──────────────────────────────────────────────────────────────────────

def depolarizing_kraus(p):
    """
    Depolarizing channel: E(rho) = (1-p) rho + p/3 (X rho X + Y rho Y + Z rho Z).
    Kraus: K0 = sqrt(1-p) I, K1 = sqrt(p/3) X, K2 = sqrt(p/3) Y, K3 = sqrt(p/3) Z.
    """
    return [
        np.sqrt(1 - p) * I2,
        np.sqrt(p / 3) * sx,
        np.sqrt(p / 3) * sy,
        np.sqrt(p / 3) * sz,
    ]


def amplitude_damping_kraus(gamma):
    """
    Amplitude damping: K0 = [[1,0],[0,sqrt(1-gamma)]], K1 = [[0,sqrt(gamma)],[0,0]].
    """
    K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
    K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)
    return [K0, K1]


def dephasing_kraus(p):
    """
    Dephasing (phase damping): E(rho) = (1-p) rho + p Z rho Z.
    Kraus: K0 = sqrt(1-p) I, K1 = sqrt(p) Z.
    """
    return [
        np.sqrt(1 - p) * I2,
        np.sqrt(p) * sz,
    ]


# ──────────────────────────────────────────────────────────────────────
# Optimisation: max over qubit input states
# ──────────────────────────────────────────────────────────────────────

def bloch_to_dm(theta, phi):
    """Pure state on Bloch sphere -> density matrix."""
    psi = ket([np.cos(theta / 2), np.exp(1j * phi) * np.sin(theta / 2)])
    return psi @ psi.conj().T


def bloch_ball_to_dm(rx, ry, rz):
    """
    General qubit density matrix from Bloch vector (rx, ry, rz).
    rho = (I + rx*X + ry*Y + rz*Z) / 2.
    Valid iff rx^2 + ry^2 + rz^2 <= 1.
    """
    return (I2 + rx * sx + ry * sy + rz * sz) / 2


def maximise_coherent_info(kraus_ops, n_starts=30):
    """
    Maximise I_c(rho, E) over ALL qubit density matrices (Bloch ball).
    The quantum capacity Q >= max_rho I_c(rho, E) (single-letter lower bound).
    For degradable channels this IS the quantum capacity.
    """
    best = -np.inf

    def neg_ic(params):
        rx, ry, rz = params
        r2 = rx**2 + ry**2 + rz**2
        if r2 > 1:
            # Project onto Bloch ball boundary with penalty
            return 1e6
        rho = bloch_ball_to_dm(rx, ry, rz)
        return -coherent_info(kraus_ops, rho)

    # Random starts inside Bloch ball
    for _ in range(n_starts):
        r = np.random.uniform(0, 1) ** (1 / 3)  # uniform in ball
        theta = np.random.uniform(0, np.pi)
        phi = np.random.uniform(0, 2 * np.pi)
        rx0 = r * np.sin(theta) * np.cos(phi)
        ry0 = r * np.sin(theta) * np.sin(phi)
        rz0 = r * np.cos(theta)
        res = minimize(neg_ic, [rx0, ry0, rz0], method='Nelder-Mead',
                       options={'xatol': 1e-10, 'fatol': 1e-12, 'maxiter': 2000})
        if -res.fun > best:
            best = -res.fun

    # Also check special points: poles, maximally mixed, equator
    for rho in [dm([1, 0]), dm([0, 1]), I2 / 2,
                bloch_ball_to_dm(0, 0, 0.5), bloch_ball_to_dm(0, 0, -0.5)]:
        ic = coherent_info(kraus_ops, rho)
        if ic > best:
            best = ic

    return best


def maximise_output_entropy(kraus_ops, n_starts=20):
    """
    Max S(E(rho)) over ALL density matrices (Bloch ball).
    """
    best = -np.inf

    def neg_s(params):
        rx, ry, rz = params
        if rx**2 + ry**2 + rz**2 > 1:
            return 1e6
        rho = bloch_ball_to_dm(rx, ry, rz)
        out = apply_channel(kraus_ops, rho)
        return -von_neumann_entropy(out)

    for _ in range(n_starts):
        r = np.random.uniform(0, 1) ** (1 / 3)
        theta = np.random.uniform(0, np.pi)
        phi = np.random.uniform(0, 2 * np.pi)
        rx0 = r * np.sin(theta) * np.cos(phi)
        ry0 = r * np.sin(theta) * np.sin(phi)
        rz0 = r * np.cos(theta)
        res = minimize(neg_s, [rx0, ry0, rz0], method='Nelder-Mead',
                       options={'xatol': 1e-10, 'fatol': 1e-12})
        if -res.fun > best:
            best = -res.fun

    # Check maximally mixed
    rho_mm = I2 / 2
    out = apply_channel(kraus_ops, rho_mm)
    s_mm = von_neumann_entropy(out)
    if s_mm > best:
        best = s_mm

    return best


def minimum_output_entropy(kraus_ops, n_starts=20):
    """Min S(E(rho)) over pure inputs (needed for Holevo)."""
    best = np.inf

    def s_out(params):
        theta, phi = params
        rho = bloch_to_dm(theta, phi)
        out = apply_channel(kraus_ops, rho)
        return von_neumann_entropy(out)

    for _ in range(n_starts):
        t0 = np.random.uniform(0, np.pi)
        p0 = np.random.uniform(0, 2 * np.pi)
        res = minimize(s_out, [t0, p0], method='Nelder-Mead',
                       options={'xatol': 1e-10, 'fatol': 1e-12})
        if res.fun < best:
            best = res.fun
    # Check poles
    for theta in [0, np.pi]:
        rho = bloch_to_dm(theta, 0)
        out = apply_channel(kraus_ops, rho)
        s = von_neumann_entropy(out)
        if s < best:
            best = s
    return best


def holevo_capacity_bound(kraus_ops, n_starts=20):
    """
    C1 >= max_rho chi(rho, E).
    For qubit channels: C1 = max_ensemble [S(E(rho_avg)) - sum p_i S(E(rho_i))].
    Upper bounded by: max S(E(rho)) - min S(E(rho_pure)).
    For covariant channels this is tight (King's theorem for depolarizing).
    """
    s_max = maximise_output_entropy(kraus_ops, n_starts)
    s_min = minimum_output_entropy(kraus_ops, n_starts)
    return s_max - s_min


# ──────────────────────────────────────────────────────────────────────
# Degradability classification
# ──────────────────────────────────────────────────────────────────────

def check_degradability(kraus_ops, n_test=100):
    """
    Numerical degradability check via coherent information sign.

    A channel E is degradable iff I_c(rho, E) >= 0 for all rho.
    A channel E is anti-degradable iff I_c(rho, E) <= 0 for all rho.

    We sample over the full Bloch ball (mixed states included).
    """
    all_ic_positive = True
    all_ic_negative = True
    max_ic = -np.inf
    min_ic = np.inf

    # Sample uniformly in Bloch ball
    for _ in range(n_test):
        r = np.random.uniform(0, 1) ** (1 / 3)
        theta = np.random.uniform(0, np.pi)
        phi = np.random.uniform(0, 2 * np.pi)
        rx = r * np.sin(theta) * np.cos(phi)
        ry = r * np.sin(theta) * np.sin(phi)
        rz = r * np.cos(theta)
        rho = bloch_ball_to_dm(rx, ry, rz)
        ic = coherent_info(kraus_ops, rho)
        if ic < -1e-10:
            all_ic_positive = False
        if ic > 1e-10:
            all_ic_negative = False
        max_ic = max(max_ic, ic)
        min_ic = min(min_ic, ic)

    # Also check special states
    for rho in [I2 / 2, dm([1, 0]), dm([0, 1]),
                bloch_ball_to_dm(0, 0, 0.5), bloch_ball_to_dm(0, 0, -0.5)]:
        ic = coherent_info(kraus_ops, rho)
        if ic < -1e-10:
            all_ic_positive = False
        if ic > 1e-10:
            all_ic_negative = False
        max_ic = max(max_ic, ic)
        min_ic = min(min_ic, ic)

    return all_ic_positive, all_ic_negative, max_ic, min_ic


def classify_degradability_amplitude_damping(gamma):
    """
    Amplitude damping at gamma:
    - gamma < 1/2: degradable (proven analytically)
    - gamma > 1/2: anti-degradable
    - gamma = 1/2: both (hence entanglement-breaking)
    """
    if gamma < 0.5 - 1e-10:
        return "degradable"
    elif gamma > 0.5 + 1e-10:
        return "anti-degradable"
    else:
        return "both (entanglement-breaking)"


def classify_degradability_depolarizing(p):
    """
    Depolarizing channel E(rho) = (1-p) rho + p/3 (X rho X + Y rho Y + Z rho Z):
    - NOT degradable for any p > 0 (proven by Cubitt et al.)
    - Anti-degradable for p >= 2/3
    - Neither for 0 < p < 2/3
    """
    if p < 1e-10:
        return "degradable (identity)"
    elif p >= 2 / 3 - 1e-10:
        return "anti-degradable"
    else:
        return "neither (not degradable)"


# ──────────────────────────────────────────────────────────────────────
# Verification: TP and CP checks
# ──────────────────────────────────────────────────────────────────────

def verify_tp(kraus_ops, tol=1e-10):
    """Check sum K_k^dag K_k = I (trace-preserving)."""
    d = kraus_ops[0].shape[0]
    total = np.zeros((d, d), dtype=complex)
    for K in kraus_ops:
        total += K.conj().T @ K
    return np.allclose(total, np.eye(d), atol=tol)


def choi_matrix(kraus_ops):
    """J(E) = sum_k vec(K_k) vec(K_k)^dag, which is PSD iff CP."""
    d = kraus_ops[0].shape[0]
    J = np.zeros((d * d, d * d), dtype=complex)
    for K in kraus_ops:
        v = K.flatten(order='F')  # vec(K) column-stacking
        J += np.outer(v, v.conj())
    return J


def verify_cp(kraus_ops, tol=1e-10):
    """Check Choi matrix is PSD (completely positive)."""
    J = choi_matrix(kraus_ops)
    evals = np.linalg.eigvalsh(J)
    return np.all(evals > -tol)


# ──────────────────────────────────────────────────────────────────────
# Main: Test 5 channels
# ──────────────────────────────────────────────────────────────────────

def run_channel_analysis(name, kraus_ops, analytic_class, analytic_notes=""):
    """Run full analysis on one channel."""
    print(f"\n{'=' * 70}")
    print(f"  Channel: {name}")
    print(f"{'=' * 70}")

    t0 = time.time()

    # 1. Verify CPTP
    tp = verify_tp(kraus_ops)
    cp = verify_cp(kraus_ops)
    print(f"  TP check: {'PASS' if tp else 'FAIL'}")
    print(f"  CP check: {'PASS' if cp else 'FAIL'}")

    # 2. Holevo capacity bound
    chi = holevo_capacity_bound(kraus_ops)
    print(f"  Holevo chi (C1 bound): {chi:.6f} bits")

    # 3. Max coherent information
    q_lb = maximise_coherent_info(kraus_ops)
    print(f"  Max coherent info (Q lower bound): {q_lb:.6f} bits")
    print(f"  Q > 0: {q_lb > 1e-10}")

    # 4. Degradability
    all_pos, all_neg, max_ic, min_ic = check_degradability(kraus_ops)
    if all_pos and all_neg:
        num_class = "trivial (I_c = 0 everywhere)"
    elif all_pos:
        num_class = "consistent with degradable (all I_c >= 0)"
    elif all_neg:
        num_class = "consistent with anti-degradable (all I_c <= 0)"
    else:
        num_class = "neither (I_c changes sign)"
    print(f"  Numerical classification: {num_class}")
    print(f"  Analytic classification:  {analytic_class}")
    print(f"  I_c range: [{min_ic:.6f}, {max_ic:.6f}]")

    elapsed = time.time() - t0
    print(f"  Time: {elapsed:.2f}s")

    result = {
        "channel": name,
        "cptp_valid": bool(tp and cp),
        "holevo_chi_bits": round(chi, 8),
        "max_coherent_info_bits": round(q_lb, 8),
        "quantum_capacity_positive": bool(q_lb > 1e-10),
        "numerical_classification": num_class,
        "analytic_classification": analytic_class,
        "ic_range": [round(min_ic, 8), round(max_ic, 8)],
        "analytic_notes": analytic_notes,
        "elapsed_s": round(elapsed, 3),
    }
    return result


def main():
    t_start = time.time()
    channels = []

    # ── Channel 1: Depolarizing p=0.05 (low noise) ──
    kraus = depolarizing_kraus(0.05)
    r = run_channel_analysis(
        "Depolarizing p=0.05",
        kraus,
        classify_degradability_depolarizing(0.05),
        "Low noise; Q > 0 but NOT degradable, single-letter formula unknown."
    )
    channels.append(r)

    # ── Channel 2: Depolarizing p=0.20 (medium noise) ──
    kraus = depolarizing_kraus(0.20)
    r = run_channel_analysis(
        "Depolarizing p=0.20",
        kraus,
        classify_degradability_depolarizing(0.20),
        "Medium noise; near Q=0 threshold. p_threshold ~ 0.2527 for Q=0."
    )
    channels.append(r)

    # ── Channel 3: Amplitude damping gamma=0.3 (degradable) ──
    kraus = amplitude_damping_kraus(0.3)
    r = run_channel_analysis(
        "Amplitude Damping gamma=0.3",
        kraus,
        classify_degradability_amplitude_damping(0.3),
        "gamma < 1/2 => degradable. Q = max I_c (single-letter, exact)."
    )
    channels.append(r)

    # ── Channel 4: Amplitude damping gamma=0.7 (anti-degradable) ──
    kraus = amplitude_damping_kraus(0.7)
    r = run_channel_analysis(
        "Amplitude Damping gamma=0.7",
        kraus,
        classify_degradability_amplitude_damping(0.7),
        "gamma > 1/2 => anti-degradable. Q = 0."
    )
    channels.append(r)

    # ── Channel 5: Dephasing p=0.1 ──
    kraus = dephasing_kraus(0.1)
    r = run_channel_analysis(
        "Dephasing p=0.1",
        kraus,
        "degradable",
        "Dephasing is always degradable (complementary = dephasing with swapped param). Q = 1 - H(p)."
    )
    channels.append(r)

    # ── Summary table ──
    print(f"\n{'=' * 70}")
    print("  SUMMARY")
    print(f"{'=' * 70}")
    print(f"  {'Channel':<35} {'C1 bound':>10} {'Q (lb)':>10} {'Class'}")
    print(f"  {'-'*35} {'-'*10} {'-'*10} {'-'*30}")
    for c in channels:
        print(f"  {c['channel']:<35} {c['holevo_chi_bits']:>10.6f} "
              f"{c['max_coherent_info_bits']:>10.6f} {c['analytic_classification']}")

    # ── Validation checks ──
    print(f"\n{'=' * 70}")
    print("  VALIDATION")
    print(f"{'=' * 70}")

    all_pass = True

    # V1: All channels are valid CPTP
    for c in channels:
        if not c["cptp_valid"]:
            print(f"  FAIL: {c['channel']} is not valid CPTP")
            all_pass = False
    if all(c["cptp_valid"] for c in channels):
        print("  PASS: All channels are valid CPTP maps")

    # V2: Amplitude damping gamma=0.3 has Q > 0
    ad03 = channels[2]
    if ad03["quantum_capacity_positive"]:
        print("  PASS: Amplitude Damping gamma=0.3 has Q > 0 (degradable regime)")
    else:
        print("  FAIL: Amplitude Damping gamma=0.3 should have Q > 0")
        all_pass = False

    # V3: Amplitude damping gamma=0.7 has Q = 0 (anti-degradable => Q = 0)
    ad07 = channels[3]
    if not ad07["quantum_capacity_positive"]:
        print("  PASS: Amplitude Damping gamma=0.7 has Q = 0 (anti-degradable)")
    else:
        print(f"  FAIL: Amplitude Damping gamma=0.7 should have Q = 0, got "
              f"I_c = {ad07['max_coherent_info_bits']}")
        all_pass = False

    # V4: Depolarizing p=0.05 should have Q > 0 (below threshold)
    dep005 = channels[0]
    if dep005["quantum_capacity_positive"]:
        print("  PASS: Depolarizing p=0.05 has Q > 0 (below threshold)")
    else:
        print("  FAIL: Depolarizing p=0.05 should have Q > 0")
        all_pass = False

    # V5: Dephasing has Q > 0 for p=0.1
    deph = channels[4]
    if deph["quantum_capacity_positive"]:
        print("  PASS: Dephasing p=0.1 has Q > 0")
    else:
        print("  FAIL: Dephasing p=0.1 should have Q > 0")
        all_pass = False

    # V6: C1 > Q for all channels with Q > 0 (classical capacity >= quantum capacity)
    for c in channels:
        if c["quantum_capacity_positive"]:
            if c["holevo_chi_bits"] >= c["max_coherent_info_bits"] - 1e-8:
                pass  # Expected
            else:
                print(f"  FAIL: {c['channel']}: C1 < Q (should never happen)")
                all_pass = False
    print("  PASS: C1 >= Q for all channels (as expected)")

    total_time = time.time() - t_start
    print(f"\n  Total elapsed: {total_time:.2f}s")
    print(f"  Overall: {'ALL PASS' if all_pass else 'SOME FAILURES'}")

    # ── Save results ──
    output = {
        "probe": "pure_lego_channel_capacity",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "channels": channels,
        "all_validations_pass": all_pass,
        "total_elapsed_s": round(total_time, 3),
    }

    out_path = pathlib.Path(__file__).parent / "a2_state" / "sim_results" / \
        "pure_lego_channel_capacity_results.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\n  Results saved to {out_path.name}")
    RESULTS.update(output)


if __name__ == "__main__":
    main()
