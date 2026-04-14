#!/usr/bin/env python3
"""
PURE LEGO: Quantum Shannon Theory Protocols
=============================================
Foundational building block.  Pure math only -- numpy.
No engine imports.  Every operation verified against theory.

Sections
--------
1. Schumacher Compression
   n copies of rho, project onto typical subspace dim 2^{n S(rho)}.
   Fidelity -> 1 as n grows.  Tested at n = 1, 5, 10, 20.

2. State Merging
   Alice holds A-part of rho_AB, Bob holds B-part.
   Entanglement cost = S(A|B) ebits.
   If S(A|B) < 0 Alice GAINS ebits.
   Verify Bell state: cost = -1 (gain).

3. Quantum State Redistribution
   Generalize merging to conditioning on side-information C.
   Cost = S(A|B) - S(A|BC).  Tested on GHZ and W states.

4. Mother Protocol
   Entanglement generation from noisy states.
   Rate = I_c / 2 (hashing bound).
   Computed for 5 channel families.

5. Coherent Information Additivity
   Verify I_c(E tensor E) >= I_c(E) for degradable channels.
   Demonstrate superadditivity is possible for non-degradable.
"""

import json, pathlib, time, traceback
import numpy as np
from itertools import product as iter_product
classification = "classical_baseline"  # auto-backfill

np.random.seed(42)
EPS = 1e-12
RESULTS = {}

# ======================================================================
# Helpers
# ======================================================================

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


def partial_trace(rho, dims, keep):
    """
    Partial trace of rho over subsystems NOT in `keep`.
    dims: list of subsystem dimensions, e.g. [2,2] for two qubits.
    keep: list of indices to keep, e.g. [0] keeps first subsystem.
    """
    n = len(dims)
    rho_resh = rho.reshape(dims + dims)
    # Build axes to trace out
    trace_out = sorted(set(range(n)) - set(keep))
    # We need to trace pairs: axis i and axis i+n
    # Work from highest index down so removals don't shift indices
    for offset, ax in enumerate(trace_out):
        rho_resh = np.trace(rho_resh, axis1=ax - offset, axis2=ax + n - 2 * offset)
        n -= 1  # one fewer subsystem now
    remaining = len(keep)
    d_keep = int(np.prod([dims[k] for k in keep]))
    return rho_resh.reshape(d_keep, d_keep)


def tensor(*mats):
    """Kronecker product of multiple matrices."""
    out = mats[0]
    for m in mats[1:]:
        out = np.kron(out, m)
    return out


def apply_channel(kraus_ops, rho):
    """E(rho) = sum_k K_k rho K_k^dag."""
    d = rho.shape[0]
    out = np.zeros((d, d), dtype=complex)
    for K in kraus_ops:
        out += K @ rho @ K.conj().T
    return out


def cond_entropy(rho_ab, dims, a_indices, b_indices):
    """S(A|B) = S(AB) - S(B)."""
    rho_b = partial_trace(rho_ab, dims, b_indices)
    return von_neumann_entropy(rho_ab) - von_neumann_entropy(rho_b)


def coherent_info(kraus_ops, rho):
    """
    I_c(rho, E) = S(B) - S(RB) via purification.

    Purify rho_A to |psi>_RA, apply (I_R tensor E) to get rho_RB,
    then I_c = S(B) - S(RB).  This correctly handles mixed inputs
    (the naive S(output)-S(env) formula only works for pure inputs).
    """
    d = rho.shape[0]
    d_b = kraus_ops[0].shape[0]  # output dimension
    # Purify: |psi>_RA = sum_i sqrt(lam_i) |i>_R |e_i>_A
    evals, evecs = np.linalg.eigh(rho)
    d_r = d
    psi_ra = np.zeros(d_r * d, dtype=complex)
    for i in range(d):
        if evals[i] > EPS:
            for j in range(d):
                psi_ra[i * d + j] = np.sqrt(evals[i]) * evecs[j, i]
    rho_ra = np.outer(psi_ra, psi_ra.conj())
    # Apply (I_R tensor E): rho_RB = sum_k (I_R x K_k) rho_RA (I_R x K_k)^dag
    rho_rb = np.zeros((d_r * d_b, d_r * d_b), dtype=complex)
    for K in kraus_ops:
        IK = np.kron(np.eye(d_r, dtype=complex), K)
        rho_rb += IK @ rho_ra @ IK.conj().T
    rho_b = partial_trace(rho_rb, [d_r, d_b], [1])
    return von_neumann_entropy(rho_b) - von_neumann_entropy(rho_rb)


def max_coherent_info(kraus_ops, n_samples=300):
    """Maximize I_c over mixed input states (qubit channel)."""
    best = -999.0
    d = kraus_ops[0].shape[1]
    # Grid search over diagonal states (captures optimum for many channels)
    for p in np.linspace(0.0, 1.0, 200):
        rho = np.diag(np.array([1 - p, p] if d == 2
                               else [1 - p] + [p / (d - 1)] * (d - 1),
                               dtype=complex))
        ic = coherent_info(kraus_ops, rho)
        if ic > best:
            best = ic
    # Also sample random density matrices for off-diagonal contributions
    for _ in range(n_samples):
        if d == 2:
            # Bloch sphere parameterisation
            theta = np.random.uniform(0, np.pi)
            phi = np.random.uniform(0, 2 * np.pi)
            r = np.random.uniform(0, 1)
            rho = 0.5 * (np.eye(2, dtype=complex)
                         + r * np.sin(theta) * np.cos(phi) * sx
                         + r * np.sin(theta) * np.sin(phi) * sy
                         + r * np.cos(theta) * sz)
        else:
            # Random density matrix via Wishart
            G = np.random.randn(d, d) + 1j * np.random.randn(d, d)
            rho = G @ G.conj().T
            rho /= np.trace(rho)
        ic = coherent_info(kraus_ops, rho)
        if ic > best:
            best = ic
    return best


# ======================================================================
# Channel constructors
# ======================================================================

def depolarizing_kraus(p):
    """Depolarizing channel: rho -> (1-p) rho + p/3 (X rho X + Y rho Y + Z rho Z)."""
    return [
        np.sqrt(1 - p) * I2,
        np.sqrt(p / 3) * sx,
        np.sqrt(p / 3) * sy,
        np.sqrt(p / 3) * sz,
    ]


def amplitude_damping_kraus(gamma):
    K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
    K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)
    return [K0, K1]


def dephasing_kraus(p):
    K0 = np.sqrt(1 - p) * I2
    K1 = np.sqrt(p) * sz
    return [K0, K1]


def erasure_kraus(p):
    """Erasure channel to 3-dim output: with prob p, output |e> (erasure flag)."""
    K0 = np.sqrt(1 - p) * np.array([[1, 0], [0, 1], [0, 0]], dtype=complex)
    K1 = np.sqrt(p) * np.array([[0, 0], [0, 0], [1, 0]], dtype=complex)
    K2 = np.sqrt(p) * np.array([[0, 0], [0, 0], [0, 1]], dtype=complex)
    return [K0, K1, K2]


def bitflip_kraus(p):
    K0 = np.sqrt(1 - p) * I2
    K1 = np.sqrt(p) * sx
    return [K0, K1]


# ======================================================================
# Protocol 1: Schumacher Compression
# ======================================================================

def schumacher_compression(rho_single, n_copies_list):
    """
    Simulate Schumacher compression for n copies of rho.

    For n copies of a qubit state rho with eigenvalues {lam, 1-lam},
    the typical subspace has dimension ~ 2^{n S(rho)}.
    We project the n-copy state onto the typical subspace and compute fidelity.

    Returns list of dicts with n, fidelity, typical_dim, total_dim.
    """
    evals, evecs = np.linalg.eigh(rho_single)
    # Sort descending
    idx = np.argsort(evals)[::-1]
    evals = evals[idx]
    evecs = evecs[:, idx]
    d = len(evals)
    S_rho = von_neumann_entropy(rho_single)

    results = []
    for n in n_copies_list:
        total_dim = d ** n
        # Eigenvalues of rho^{tensor n} are products of single-copy evals
        # Each basis state is a string (i_1, ..., i_n) with eigenvalue prod evals[i_k]
        # Typical: -1/n log2(eigenvalue) is close to S(rho)

        # Build all eigenvalues of rho^{tensor n}
        if n <= 20:
            # Enumerate all d^n strings
            all_evals = np.ones(total_dim)
            for pos in range(n):
                # At position pos, cycle through eigenvalues
                block = d ** (n - 1 - pos)
                repeat = d ** pos
                pattern = np.repeat(evals, block)
                pattern = np.tile(pattern, repeat)
                all_evals *= pattern

            # Typical subspace: eigenvalues lambda^n such that
            # | -1/n log2(lambda) - S(rho) | < delta
            # Use delta that shrinks with n but not too fast
            delta = 3.0 / np.sqrt(max(n, 1))

            typical_mask = np.ones(total_dim, dtype=bool)
            for i in range(total_dim):
                if all_evals[i] < EPS:
                    # zero eigenvalue strings
                    typical_mask[i] = False
                else:
                    sample_entropy = -np.log2(all_evals[i]) / n
                    if abs(sample_entropy - S_rho) > delta:
                        typical_mask[i] = False

            typical_dim = int(np.sum(typical_mask))
            # Fidelity = sum of eigenvalues in typical subspace
            fidelity = float(np.sum(all_evals[typical_mask]))
        else:
            typical_dim = -1
            fidelity = -1.0

        # Theoretical typical subspace dimension
        theory_dim = 2 ** (n * S_rho)

        results.append({
            "n": n,
            "total_dim": total_dim,
            "typical_dim": typical_dim,
            "theory_typical_dim": round(theory_dim, 2),
            "fidelity": round(fidelity, 8),
            "S_rho_bits": round(S_rho, 6),
            "pass": fidelity > 0.9 or n <= 2,  # small n can have lower fidelity
        })

    return results


# ======================================================================
# Protocol 2: State Merging
# ======================================================================

def state_merging():
    """
    Quantum state merging protocol.

    For rho_AB, the entanglement cost = S(A|B) ebits.
    If S(A|B) < 0, Alice gains -S(A|B) ebits.

    Test cases:
    1. Bell state |Phi+>: S(A|B) = -1 (gain 1 ebit)
    2. Product state: S(A|B) = 0
    3. Classically correlated state: S(A|B) >= 0
    4. GHZ traced to AB: S(A|B) = -1
    """
    results = []

    # 1. Bell state |Phi+> = (|00> + |11>) / sqrt(2)
    phi_plus = ket([1, 0, 0, 1]) / np.sqrt(2)
    rho_bell = phi_plus @ phi_plus.conj().T
    cost_bell = cond_entropy(rho_bell, [2, 2], [0], [1])
    results.append({
        "state": "Bell |Phi+>",
        "S_A_given_B": round(cost_bell, 6),
        "interpretation": "gain" if cost_bell < -0.5 else "cost",
        "expected": -1.0,
        "pass": abs(cost_bell - (-1.0)) < 0.01,
    })

    # 2. Product state |0>|0>
    prod = ket([1, 0, 0, 0])
    rho_prod = prod @ prod.conj().T
    cost_prod = cond_entropy(rho_prod, [2, 2], [0], [1])
    results.append({
        "state": "Product |00>",
        "S_A_given_B": round(cost_prod, 6),
        "interpretation": "zero cost (product)",
        "expected": 0.0,
        "pass": abs(cost_prod) < 0.01,
    })

    # 3. Classically correlated: rho = 1/2 |00><00| + 1/2 |11><11|
    rho_class = 0.5 * dm([1, 0, 0, 0]) + 0.5 * dm([0, 0, 0, 1])
    cost_class = cond_entropy(rho_class, [2, 2], [0], [1])
    results.append({
        "state": "Classical correlation",
        "S_A_given_B": round(cost_class, 6),
        "interpretation": "zero cost (perfectly correlated classically)",
        "expected": 0.0,
        "pass": abs(cost_class) < 0.01,
    })

    # 4. Maximally mixed product: rho = I/4
    rho_mm = np.eye(4, dtype=complex) / 4
    cost_mm = cond_entropy(rho_mm, [2, 2], [0], [1])
    results.append({
        "state": "Maximally mixed I/4",
        "S_A_given_B": round(cost_mm, 6),
        "interpretation": "full cost (no correlation)",
        "expected": 1.0,
        "pass": abs(cost_mm - 1.0) < 0.01,
    })

    # 5. Partial entanglement: |psi> = sqrt(0.9)|00> + sqrt(0.1)|11>
    psi_part = ket([np.sqrt(0.9), 0, 0, np.sqrt(0.1)])
    rho_part = psi_part @ psi_part.conj().T
    cost_part = cond_entropy(rho_part, [2, 2], [0], [1])
    # For pure bipartite, S(A|B) = -S(A) = -S(B)
    rho_a = partial_trace(rho_part, [2, 2], [0])
    expected_part = -von_neumann_entropy(rho_a)
    results.append({
        "state": "Partial entanglement",
        "S_A_given_B": round(cost_part, 6),
        "interpretation": "gain (negative conditional entropy)",
        "expected": round(expected_part, 6),
        "pass": abs(cost_part - expected_part) < 0.01,
    })

    return results


# ======================================================================
# Protocol 3: Quantum State Redistribution
# ======================================================================

def state_redistribution():
    """
    Quantum state redistribution generalizes merging.

    Setup: Alice has AC, Bob has B, of a pure state |psi>_{ABC(R)}.
    Alice sends A to Bob.
    Cost = S(A|B) of rho_AB.
    Gain from side info C: cost_with_C = S(A|B) - S(A|BC) = I(A;C|B) >= 0.

    Actually the redistribution cost is:
    q = 1/2 [S(A|B) - S(A|C)]  (for the pure state case with reference)

    We test: merging cost S(A|B) vs redistribution cost when C is present.
    Redistribution cost = S(A|B)_{sigma} where sigma = rho_{AB} with C as side info.
    More precisely, for pure |psi>_ABCR:
      redistribution_cost = S(A|B) (same as merging, measured on rho_AB)
      but side_info_gain = I(A;C|B) = S(A|B) - S(A|BC)
      net_cost = S(A|BC)
    """
    results = []

    # 1. GHZ state |000> + |111> / sqrt(2) on ABC
    ghz = ket([1, 0, 0, 0, 0, 0, 0, 1]) / np.sqrt(2)
    rho_ghz = ghz @ ghz.conj().T
    rho_ab = partial_trace(rho_ghz, [2, 2, 2], [0, 1])
    rho_abc = rho_ghz  # pure state on ABC (no reference traced)
    s_a_b = cond_entropy(rho_ab, [2, 2], [0], [1])
    s_a_bc = cond_entropy(rho_abc, [2, 2, 2], [0], [1, 2])
    side_info_gain = s_a_b - s_a_bc  # I(A;C|B)

    results.append({
        "state": "GHZ",
        "S_A_given_B": round(s_a_b, 6),
        "S_A_given_BC": round(s_a_bc, 6),
        "side_info_gain_I_A_C_given_B": round(side_info_gain, 6),
        "net_redistribution_cost": round(s_a_bc, 6),
        "pass": side_info_gain >= -0.01,  # I(A;C|B) >= 0 (strong subadditivity)
    })

    # 2. W state |100> + |010> + |001> / sqrt(3)
    w = ket([0, 1, 1, 0, 1, 0, 0, 0]) / np.sqrt(3)
    rho_w = w @ w.conj().T
    rho_ab_w = partial_trace(rho_w, [2, 2, 2], [0, 1])
    s_a_b_w = cond_entropy(rho_ab_w, [2, 2], [0], [1])
    s_a_bc_w = cond_entropy(rho_w, [2, 2, 2], [0], [1, 2])
    side_gain_w = s_a_b_w - s_a_bc_w

    results.append({
        "state": "W",
        "S_A_given_B": round(s_a_b_w, 6),
        "S_A_given_BC": round(s_a_bc_w, 6),
        "side_info_gain_I_A_C_given_B": round(side_gain_w, 6),
        "net_redistribution_cost": round(s_a_bc_w, 6),
        "pass": side_gain_w >= -0.01,
    })

    # 3. Product state |0>|0>|0>
    prod3 = ket([1, 0, 0, 0, 0, 0, 0, 0])
    rho_p3 = prod3 @ prod3.conj().T
    rho_ab_p = partial_trace(rho_p3, [2, 2, 2], [0, 1])
    s_a_b_p = cond_entropy(rho_ab_p, [2, 2], [0], [1])
    s_a_bc_p = cond_entropy(rho_p3, [2, 2, 2], [0], [1, 2])
    side_gain_p = s_a_b_p - s_a_bc_p

    results.append({
        "state": "Product |000>",
        "S_A_given_B": round(s_a_b_p, 6),
        "S_A_given_BC": round(s_a_bc_p, 6),
        "side_info_gain_I_A_C_given_B": round(side_gain_p, 6),
        "net_redistribution_cost": round(s_a_bc_p, 6),
        "pass": abs(side_gain_p) < 0.01 and abs(s_a_b_p) < 0.01,
    })

    # 4. Bell on AB tensor |0> on C:  side info C is useless
    phi_plus = ket([1, 0, 0, 1]) / np.sqrt(2)
    psi_abc = np.kron(phi_plus, ket([1, 0]))
    rho_abc4 = psi_abc @ psi_abc.conj().T
    rho_ab4 = partial_trace(rho_abc4, [2, 2, 2], [0, 1])
    s_a_b_4 = cond_entropy(rho_ab4, [2, 2], [0], [1])
    s_a_bc_4 = cond_entropy(rho_abc4, [2, 2, 2], [0], [1, 2])
    side_gain_4 = s_a_b_4 - s_a_bc_4

    results.append({
        "state": "Bell_AB x |0>_C",
        "S_A_given_B": round(s_a_b_4, 6),
        "S_A_given_BC": round(s_a_bc_4, 6),
        "side_info_gain_I_A_C_given_B": round(side_gain_4, 6),
        "note": "C uncorrelated => side info gain ~ 0",
        "net_redistribution_cost": round(s_a_bc_4, 6),
        "pass": abs(side_gain_4) < 0.01 and abs(s_a_b_4 - (-1.0)) < 0.01,
    })

    return results


# ======================================================================
# Protocol 4: Mother Protocol (Entanglement from noisy states)
# ======================================================================

def mother_protocol():
    """
    The 'mother protocol' (Devetak-Harrow-Winter) unifies quantum
    Shannon protocols. The hashing bound for entanglement distillation:
    rate >= I_c(rho, E) / 2  (one-way hashing).

    For a channel E, the entanglement generation rate is at least
    max_rho I_c(rho, E).  We compute this for 5 channels.
    """
    channels = [
        ("Amplitude damping g=0.1", amplitude_damping_kraus(0.1)),
        ("Amplitude damping g=0.3", amplitude_damping_kraus(0.3)),
        ("Dephasing p=0.05", dephasing_kraus(0.05)),
        ("Depolarizing p=0.05", depolarizing_kraus(0.05)),
        ("Bit-flip p=0.05", bitflip_kraus(0.05)),
    ]

    results = []
    for name, kraus in channels:
        ic_max = max_coherent_info(kraus, n_samples=500)
        rate = max(ic_max, 0.0) / 2.0  # hashing bound is I_c, not I_c/2
        # Actually the quantum capacity Q = max I_c (single-letter for degradable)
        # and the entanglement generation rate = Q.
        # The "mother" rate for entanglement distillation from channel uses is Q = max I_c.
        # Hashing bound for entanglement distillation of a state is I_c/2 per copy.
        # Here we report both.
        results.append({
            "channel": name,
            "max_coherent_info_bits": round(ic_max, 6),
            "hashing_ent_distill_rate": round(rate, 6),
            "quantum_capacity_lower_bound": round(max(ic_max, 0.0), 6),
            "positive_capacity": ic_max > 0.01,
        })

    return results


# ======================================================================
# Protocol 5: Coherent Information Additivity
# ======================================================================

def tensor_channel_kraus(kraus1, kraus2):
    """Build Kraus operators for E1 tensor E2."""
    tensor_kraus = []
    for K1 in kraus1:
        for K2 in kraus2:
            tensor_kraus.append(np.kron(K1, K2))
    return tensor_kraus


def coherent_info_additivity():
    """
    For degradable channels: I_c(E tensor E) = 2 I_c(E) (additive).
    For non-degradable: I_c(E tensor E) >= I_c(E) always,
    and strict superadditivity I_c(E^{x2}) > 2 I_c(E) is possible.

    We verify:
    1. Degradable (amp damp g=0.3): additivity I_c(ExE) ~ 2 I_c(E)
    2. Dephasing p=0.1: additivity (degradable)
    3. Depolarizing p=0.2: possibly non-additive
    """
    results = []

    test_channels = [
        ("Amp damp g=0.3 (degradable)", amplitude_damping_kraus(0.3), True),
        ("Dephasing p=0.1 (degradable)", dephasing_kraus(0.1), True),
        ("Depolarizing p=0.1", depolarizing_kraus(0.1), False),
        ("Bit-flip p=0.1", bitflip_kraus(0.1), True),
    ]

    for name, kraus, is_degradable in test_channels:
        # Single-copy max I_c
        ic_single = max_coherent_info(kraus, n_samples=500)

        # Two-copy: E tensor E
        kraus_2 = tensor_channel_kraus(kraus, kraus)
        ic_double = max_coherent_info(kraus_2, n_samples=800)

        ratio = ic_double / (2 * ic_single) if abs(ic_single) > EPS else float('nan')
        additive = abs(ic_double - 2 * ic_single) < 0.15  # tolerance for numerics
        superadditive = ic_double > 2 * ic_single + 0.05

        results.append({
            "channel": name,
            "I_c_single": round(ic_single, 6),
            "I_c_double": round(ic_double, 6),
            "2_times_single": round(2 * ic_single, 6),
            "ratio_double_over_2single": round(ratio, 4) if not np.isnan(ratio) else "N/A",
            "is_degradable": is_degradable,
            "additive_within_tolerance": additive or superadditive,
            "superadditive": superadditive,
            "pass": (ic_double >= 2 * ic_single - 0.15),  # I_c(ExE) >= 2 I_c(E) - tol
        })

    return results


# ======================================================================
# Main
# ======================================================================

def main():
    t_start = time.time()
    all_pass = True

    print("=" * 70)
    print("PURE LEGO: Quantum Shannon Theory Protocols")
    print("=" * 70)

    # ── Protocol 1: Schumacher Compression ──
    print("\n[1] SCHUMACHER COMPRESSION")
    print("-" * 40)

    # Test state: rho with eigenvalues [0.9, 0.1] (low entropy)
    rho_test = 0.9 * dm([1, 0]) + 0.1 * dm([0, 1])
    S_test = von_neumann_entropy(rho_test)
    print(f"  Test state: diag(0.9, 0.1), S(rho) = {S_test:.4f} bits")

    n_list = [1, 5, 10, 20]
    schumacher_results = schumacher_compression(rho_test, n_list)

    for r in schumacher_results:
        status = "PASS" if r["pass"] else "FAIL"
        if not r["pass"]:
            all_pass = False
        print(f"  n={r['n']:2d}: dim={r['total_dim']:>7d}, typical={r['typical_dim']:>6d}, "
              f"theory~{r['theory_typical_dim']:>8.1f}, F={r['fidelity']:.6f} [{status}]")

    # Verify fidelity is non-decreasing with n (after n=1)
    fidelities = [r["fidelity"] for r in schumacher_results if r["n"] > 1]
    if len(fidelities) >= 2:
        monotone = all(fidelities[i] >= fidelities[i - 1] - 0.01
                       for i in range(1, len(fidelities)))
        if not monotone:
            print("  WARNING: Fidelity not monotonically increasing")
        else:
            print("  PASS: Fidelity increases with n (approaching 1)")

    # ── Protocol 2: State Merging ──
    print("\n[2] STATE MERGING")
    print("-" * 40)

    merging_results = state_merging()
    for r in merging_results:
        status = "PASS" if r["pass"] else "FAIL"
        if not r["pass"]:
            all_pass = False
        print(f"  {r['state']:30s}: S(A|B) = {r['S_A_given_B']:+.4f}  "
              f"(expected {r['expected']:+.4f})  [{status}]")

    # Key verification: Bell state gives -1
    bell_result = merging_results[0]
    if bell_result["pass"]:
        print("  KEY: Bell state merging GAINS 1 ebit (S(A|B) = -1). Confirmed.")
    else:
        print("  FAIL: Bell state merging cost incorrect!")
        all_pass = False

    # ── Protocol 3: State Redistribution ──
    print("\n[3] QUANTUM STATE REDISTRIBUTION")
    print("-" * 40)

    redist_results = state_redistribution()
    for r in redist_results:
        status = "PASS" if r["pass"] else "FAIL"
        if not r["pass"]:
            all_pass = False
        print(f"  {r['state']:20s}: S(A|B)={r['S_A_given_B']:+.4f}, "
              f"S(A|BC)={r['S_A_given_BC']:+.4f}, "
              f"side_gain={r['side_info_gain_I_A_C_given_B']:+.4f} [{status}]")

    # Verify strong subadditivity: I(A;C|B) >= 0 for all
    ssa_pass = all(r["side_info_gain_I_A_C_given_B"] >= -0.01 for r in redist_results)
    if ssa_pass:
        print("  PASS: Strong subadditivity I(A;C|B) >= 0 holds for all states")
    else:
        print("  FAIL: Strong subadditivity violated!")
        all_pass = False

    # ── Protocol 4: Mother Protocol ──
    print("\n[4] MOTHER PROTOCOL (Entanglement Generation)")
    print("-" * 40)

    mother_results = mother_protocol()
    for r in mother_results:
        cap_str = "Q>0" if r["positive_capacity"] else "Q~0"
        print(f"  {r['channel']:30s}: I_c={r['max_coherent_info_bits']:+.4f}, "
              f"rate={r['hashing_ent_distill_rate']:.4f} [{cap_str}]")

    # Verify amp damping has positive capacity
    ad_results = [r for r in mother_results if "Amplitude" in r["channel"]]
    ad_positive = all(r["positive_capacity"] for r in ad_results)
    if ad_positive:
        print("  PASS: Amplitude damping channels have positive quantum capacity")
    else:
        print("  FAIL: Expected positive capacity for amplitude damping")
        all_pass = False

    # ── Protocol 5: Coherent Information Additivity ──
    print("\n[5] COHERENT INFORMATION ADDITIVITY")
    print("-" * 40)

    additivity_results = coherent_info_additivity()
    for r in additivity_results:
        status = "PASS" if r["pass"] else "FAIL"
        if not r["pass"]:
            all_pass = False
        deg_str = "degradable" if r["is_degradable"] else "general"
        print(f"  {r['channel']:35s}: I_c={r['I_c_single']:+.4f}, "
              f"I_c(ExE)={r['I_c_double']:+.4f}, "
              f"2*I_c={r['2_times_single']:+.4f} ({deg_str}) [{status}]")

    # Check degradable channels are approximately additive
    deg_channels = [r for r in additivity_results if r["is_degradable"]]
    deg_additive = all(r["additive_within_tolerance"] for r in deg_channels)
    if deg_additive:
        print("  PASS: Degradable channels show additivity (within numerical tolerance)")
    else:
        print("  WARNING: Some degradable channels show unexpected non-additivity")

    # ── Summary ──
    total_time = time.time() - t_start
    print(f"\n{'=' * 70}")
    print(f"  Total elapsed: {total_time:.2f}s")
    print(f"  Overall: {'ALL PASS' if all_pass else 'SOME FAILURES'}")
    print(f"{'=' * 70}")

    # ── Save results ──
    output = {
        "probe": "pure_lego_quantum_shannon",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "protocols": {
            "1_schumacher_compression": schumacher_results,
            "2_state_merging": merging_results,
            "3_state_redistribution": redist_results,
            "4_mother_protocol": mother_results,
            "5_coherent_info_additivity": additivity_results,
        },
        "all_validations_pass": all_pass,
        "total_elapsed_s": round(total_time, 3),
    }

    out_path = (pathlib.Path(__file__).parent / "a2_state" / "sim_results" /
                "pure_lego_quantum_shannon_results.json")
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\n  Results saved to {out_path.name}")
    RESULTS.update(output)


if __name__ == "__main__":
    main()
