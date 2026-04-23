#!/usr/bin/env python3
"""
ENTROPY-TOPOLOGY COMPATIBILITY MATRIX
======================================
Which entropy types survive on which topological structures?

12 entropy measures x 6 topologies = 72-cell compatibility matrix.
Plus cross-tests: Berry-entropy correlation, Betti-discrimination,
entanglement detection threshold.

NO engine imports. Pure legos only: numpy, scipy.
"""

import sys, os, json, pathlib, time, warnings
import numpy as np
from scipy.linalg import logm
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical baseline: entropy-topology compatibility is scanned here by numeric entropy and topology surrogates, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "density-matrix families, entropy measures, and compatibility-matrix numerics"},
    "scipy": {"tried": True, "used": True, "reason": "matrix logarithms for entropy-family calculations"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "supportive",
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

warnings.filterwarnings("ignore", category=RuntimeWarning)
np.random.seed(42)

EPS = 1e-14
RESULTS = {}

# ═══════════════════════════════════════════════════════════════════
# PAULI MATRICES & HELPERS
# ═══════════════════════════════════════════════════════════════════

I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)


def ket(v):
    return np.array(v, dtype=complex).reshape(-1, 1)


def dm(v):
    k = ket(v)
    return k @ k.conj().T


def partial_trace_B(rho_AB, dA=2, dB=2):
    """Trace out subsystem B, return rho_A."""
    rho = rho_AB.reshape(dA, dB, dA, dB)
    return np.trace(rho, axis1=1, axis2=3)


def partial_trace_A(rho_AB, dA=2, dB=2):
    """Trace out subsystem A, return rho_B."""
    rho = rho_AB.reshape(dA, dB, dA, dB)
    return np.trace(rho, axis1=0, axis2=2)


def random_dm(d=2):
    """Random density matrix via Ginibre ensemble."""
    G = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    rho = G @ G.conj().T
    return rho / np.trace(rho)


def bloch_dm(theta, phi):
    """Pure state on Bloch sphere: |psi> = cos(t/2)|0> + e^{i*phi}sin(t/2)|1>."""
    c0 = np.cos(theta / 2)
    c1 = np.exp(1j * phi) * np.sin(theta / 2)
    return dm([c0, c1])


def ensure_dm(rho):
    """Force Hermitian + unit trace."""
    rho = (rho + rho.conj().T) / 2
    rho /= np.trace(rho)
    return rho


# ═══════════════════════════════════════════════════════════════════
# 12 ENTROPY MEASURES
# ═══════════════════════════════════════════════════════════════════

def _safe_evals(rho):
    rho = (rho + rho.conj().T) / 2
    ev = np.real(np.linalg.eigvalsh(rho))
    return np.maximum(ev, 0)


def vn_entropy(rho):
    """Von Neumann entropy S = -Tr(rho log2 rho), bits."""
    ev = _safe_evals(rho)
    ev = ev[ev > EPS]
    if len(ev) == 0:
        return 0.0
    return float(-np.sum(ev * np.log2(ev)))


def renyi_entropy(rho, alpha):
    """Renyi entropy H_alpha = (1/(1-alpha)) log2(Tr(rho^alpha))."""
    if abs(alpha - 1.0) < 1e-10:
        return vn_entropy(rho)
    ev = _safe_evals(rho)
    ev = ev[ev > EPS]
    if len(ev) == 0:
        return 0.0
    val = np.sum(ev ** alpha)
    if val <= 0:
        return 0.0
    return float(np.log2(val) / (1.0 - alpha))


def min_entropy(rho):
    """Min-entropy H_inf = -log2(lambda_max)."""
    ev = _safe_evals(rho)
    lmax = np.max(ev)
    if lmax < EPS:
        return 0.0
    return float(-np.log2(lmax))


def linear_entropy(rho):
    """Linear entropy S_L = (d/(d-1))(1 - Tr(rho^2))."""
    d = rho.shape[0]
    purity = np.real(np.trace(rho @ rho))
    if d <= 1:
        return 0.0
    return float((d / (d - 1)) * (1.0 - purity))


def conditional_entropy(rho_AB, rho_B):
    """S(A|B) = S(AB) - S(B). Can be negative for entangled states."""
    return vn_entropy(rho_AB) - vn_entropy(rho_B)


def mutual_information(rho_AB, rho_A, rho_B):
    """I(A:B) = S(A) + S(B) - S(AB)."""
    return vn_entropy(rho_A) + vn_entropy(rho_B) - vn_entropy(rho_AB)


def coherent_information(rho_AB, rho_B):
    """I_c(A>B) = S(B) - S(AB). Positive implies quantum capacity."""
    return vn_entropy(rho_B) - vn_entropy(rho_AB)


def relative_entropy(rho, sigma):
    """D(rho||sigma) = Tr[rho(log2 rho - log2 sigma)]."""
    rho_h = (rho + rho.conj().T) / 2
    sigma_h = (sigma + sigma.conj().T) / 2
    ev_r, U_r = np.linalg.eigh(rho_h)
    ev_s, U_s = np.linalg.eigh(sigma_h)
    ev_r = np.maximum(ev_r, 0)
    ev_s = np.maximum(ev_s, 0)
    log_r = np.zeros_like(rho_h)
    for i, ev in enumerate(ev_r):
        if ev > EPS:
            log_r += np.log2(ev) * np.outer(U_r[:, i], U_r[:, i].conj())
    log_s = np.zeros_like(sigma_h)
    for i, ev in enumerate(ev_s):
        if ev > EPS:
            log_s += np.log2(ev) * np.outer(U_s[:, i], U_s[:, i].conj())
    val = np.real(np.trace(rho_h @ (log_r - log_s)))
    return max(0.0, float(val))


# Convenience: all single-state entropies
SINGLE_ENTROPY_NAMES = [
    "vN", "renyi_0.5", "renyi_2", "renyi_5",
    "min_entropy", "linear_entropy"
]

BIPARTITE_ENTROPY_NAMES = [
    "conditional", "mutual_info", "coherent_info"
]

REFERENCE_ENTROPY_NAMES = ["relative_entropy"]

ALL_ENTROPY_NAMES = SINGLE_ENTROPY_NAMES + BIPARTITE_ENTROPY_NAMES + REFERENCE_ENTROPY_NAMES


def compute_single_entropies(rho):
    """Compute all single-state entropies for a density matrix."""
    return {
        "vN": vn_entropy(rho),
        "renyi_0.5": renyi_entropy(rho, 0.5),
        "renyi_2": renyi_entropy(rho, 2.0),
        "renyi_5": renyi_entropy(rho, 5.0),
        "min_entropy": min_entropy(rho),
        "linear_entropy": linear_entropy(rho),
    }


def compute_bipartite_entropies(rho_AB):
    """Compute all bipartite entropies for a 4x4 density matrix."""
    rho_A = partial_trace_B(rho_AB)
    rho_B = partial_trace_A(rho_AB)
    return {
        "conditional": conditional_entropy(rho_AB, rho_B),
        "mutual_info": mutual_information(rho_AB, rho_A, rho_B),
        "coherent_info": coherent_information(rho_AB, rho_B),
    }


def compute_relative_entropy(rho, sigma):
    """Compute relative entropy against a reference state."""
    return {"relative_entropy": relative_entropy(rho, sigma)}


# ═══════════════════════════════════════════════════════════════════
# TOPOLOGY 1: FLAT (no topology)
# ═══════════════════════════════════════════════════════════════════

def build_flat_states(n=30):
    """Random 2x2 density matrices with no geometric structure."""
    return [random_dm(2) for _ in range(n)]


# ═══════════════════════════════════════════════════════════════════
# TOPOLOGY 2: CIRCLE S1 (1 cycle)
# ═══════════════════════════════════════════════════════════════════

def build_s1_states(n=8):
    """States evenly on Bloch equator with angle-dependent mixedness.
    Each state is depolarized by an amount that varies around the circle,
    so entropy is non-trivial and captures the S1 structure.
    """
    states = []
    for k in range(n):
        phi = 2 * np.pi * k / n
        rho_pure = bloch_dm(np.pi / 2, phi)
        # Mixedness varies sinusoidally around circle
        eps = 0.05 + 0.35 * (1 + np.sin(phi)) / 2  # range ~0.05 to ~0.40
        rho = (1 - eps) * rho_pure + eps * I2 / 2
        states.append(ensure_dm(rho))
    return states


def s1_mixture(states):
    """Uniform mixture of S1 states."""
    return sum(states) / len(states)


def s1_adjacent_product(states, i):
    """4x4 product state of adjacent pair for MI computation."""
    j = (i + 1) % len(states)
    return np.kron(states[i], states[j])


# ═══════════════════════════════════════════════════════════════════
# TOPOLOGY 3: SPHERE S2 (full Bloch)
# ═══════════════════════════════════════════════════════════════════

def build_s2_states(n=20):
    """States uniformly on Bloch sphere via Fibonacci spiral.
    Position-dependent mixedness: more mixed near equator, purer near poles.
    This gives the sphere non-trivial entropy structure.
    """
    states = []
    golden = (1 + np.sqrt(5)) / 2
    for k in range(n):
        theta = np.arccos(1 - 2 * (k + 0.5) / n)
        phi = 2 * np.pi * k / golden
        rho_pure = bloch_dm(theta, phi)
        # More mixed near equator (theta ~ pi/2)
        eps = 0.05 + 0.4 * np.sin(theta)  # range ~0.05 to ~0.45
        rho = (1 - eps) * rho_pure + eps * I2 / 2
        states.append(ensure_dm(rho))
    return states


# ═══════════════════════════════════════════════════════════════════
# TOPOLOGY 4: TORUS T2 (nested, via Hopf map)
# ═══════════════════════════════════════════════════════════════════

def build_torus_states(n1=6, n2=6):
    """States on torus T2: theta1, theta2 grid mapped to Bloch sphere
    via Hopf-like parametrization, with position-dependent mixedness.
    Pure state at each point gets depolarized by amount depending on
    distance from torus center, so entropies are non-trivial and
    vary across the torus.
    """
    states = []
    coords = []
    for i in range(n1):
        for j in range(n2):
            t1 = 2 * np.pi * i / n1
            t2 = 2 * np.pi * j / n2
            # Map torus to Bloch sphere via Hopf-like parametrization
            theta = np.pi * (0.2 + 0.6 * (np.sin(t1) + 1) / 2)  # stays away from poles
            phi = t2
            rho_pure = bloch_dm(theta, phi)
            # Position-dependent depolarization: more mixed near inner rim
            eps = 0.05 + 0.4 * (1 - np.cos(t1)) / 2  # range ~0.05 to ~0.45
            rho_mixed = (1 - eps) * rho_pure + eps * I2 / 2
            states.append(ensure_dm(rho_mixed))
            coords.append((t1, t2))
    return states, coords


def berry_phase_adjacent(states, coords, i, j):
    """Berry phase between two adjacent states via inner product.
    gamma = -Im(log(<psi_i|psi_j>))
    """
    rho_i = states[i]
    rho_j = states[j]
    # Extract kets from pure density matrices
    ev_i, U_i = np.linalg.eigh(rho_i)
    ev_j, U_j = np.linalg.eigh(rho_j)
    # Take eigenvector with eigenvalue ~1
    ket_i = U_i[:, np.argmax(ev_i)]
    ket_j = U_j[:, np.argmax(ev_j)]
    overlap = np.vdot(ket_i, ket_j)
    if abs(overlap) < EPS:
        return 0.0
    return float(-np.imag(np.log(overlap)))


# ═══════════════════════════════════════════════════════════════════
# TOPOLOGY 5: 2-QUBIT PRODUCT (separable manifold)
# ═══════════════════════════════════════════════════════════════════

def build_product_states(n=30):
    """Random product states rho_A (x) rho_B."""
    states = []
    for _ in range(n):
        rA = random_dm(2)
        rB = random_dm(2)
        states.append(np.kron(rA, rB))
    return states


# ═══════════════════════════════════════════════════════════════════
# TOPOLOGY 6: 2-QUBIT ENTANGLED (Bell manifold)
# ═══════════════════════════════════════════════════════════════════

BELL_KETS = [
    ket([1, 0, 0, 1]) / np.sqrt(2),  # Phi+
    ket([1, 0, 0, -1]) / np.sqrt(2),  # Phi-
    ket([0, 1, 1, 0]) / np.sqrt(2),  # Psi+
    ket([0, 1, -1, 0]) / np.sqrt(2),  # Psi-
]


def build_entangled_states(n=30):
    """States near Bell states with varying mixedness.
    rho = (1 - eps) |Bell><Bell| + eps * I/4
    """
    states = []
    mixedness_vals = []
    for i in range(n):
        bell_idx = i % 4
        bell_ket = BELL_KETS[bell_idx]
        bell_dm = bell_ket @ bell_ket.conj().T
        eps = 0.01 + 0.98 * i / (n - 1)  # range from nearly pure to nearly maximally mixed
        rho = (1 - eps) * bell_dm + eps * np.eye(4) / 4
        states.append(ensure_dm(rho))
        mixedness_vals.append(eps)
    return states, mixedness_vals


# ═══════════════════════════════════════════════════════════════════
# COMPATIBILITY MATRIX COMPUTATION
# ═══════════════════════════════════════════════════════════════════

def compute_cell(entropy_name, values, ref_values=None):
    """Compute compatibility cell: mean, variance, discrimination power, triviality."""
    vals = np.array(values)
    mean_val = float(np.mean(vals))
    var_val = float(np.var(vals))

    # Discrimination power: how different from flat?
    disc_power = None
    if ref_values is not None:
        ref_arr = np.array(ref_values)
        # Cohen's d effect size
        pooled_std = np.sqrt((np.var(vals) + np.var(ref_arr)) / 2)
        if pooled_std > EPS:
            disc_power = float(abs(np.mean(vals) - np.mean(ref_arr)) / pooled_std)
        else:
            disc_power = 0.0

    # Triviality: entropy is always ~0 or always ~max
    max_possible = np.log2(vals.shape[0]) if len(vals) > 0 else 1.0
    trivial_zero = bool(np.all(np.abs(vals) < 0.01))
    trivial_max = bool(var_val < 0.001 and mean_val > 0.9)

    return {
        "mean": round(mean_val, 6),
        "variance": round(var_val, 6),
        "discrimination_power": round(disc_power, 4) if disc_power is not None else None,
        "trivial_zero": trivial_zero,
        "trivial_max": trivial_max,
        "compatible": not (trivial_zero and var_val < EPS),
        "n_samples": len(values),
    }


def run_topology_entropies(topology_name, states, is_bipartite=False,
                           ref_single=None, ref_bipartite=None, ref_relative=None):
    """Run all applicable entropy measures on a set of states."""
    results = {}

    # --- Single-state entropies ---
    single_values = {name: [] for name in SINGLE_ENTROPY_NAMES}
    for rho in states:
        ents = compute_single_entropies(rho)
        for name in SINGLE_ENTROPY_NAMES:
            single_values[name].append(ents[name])

    for name in SINGLE_ENTROPY_NAMES:
        ref = ref_single[name] if ref_single else None
        results[name] = compute_cell(name, single_values[name], ref)

    # --- Relative entropy (each state vs maximally mixed) ---
    d = states[0].shape[0]
    sigma_ref = np.eye(d) / d
    rel_values = []
    for rho in states:
        rel_values.append(relative_entropy(rho, sigma_ref))
    ref = ref_relative if ref_relative else None
    results["relative_entropy"] = compute_cell("relative_entropy", rel_values, ref)

    # --- Bipartite entropies (only for 4x4 states) ---
    if is_bipartite:
        bip_values = {name: [] for name in BIPARTITE_ENTROPY_NAMES}
        for rho in states:
            ents = compute_bipartite_entropies(rho)
            for name in BIPARTITE_ENTROPY_NAMES:
                bip_values[name].append(ents[name])

        for name in BIPARTITE_ENTROPY_NAMES:
            ref = ref_bipartite[name] if ref_bipartite else None
            results[name] = compute_cell(name, bip_values[name], ref)
    else:
        for name in BIPARTITE_ENTROPY_NAMES:
            results[name] = {"status": "N/A (not bipartite)", "compatible": None}

    return results, single_values, rel_values


# ═══════════════════════════════════════════════════════════════════
# CROSS-TEST 1: Berry phase correlation on torus
# ═══════════════════════════════════════════════════════════════════

def cross_test_berry_entropy(torus_states, torus_coords, n1=6, n2=6):
    """Does Berry phase correlate with any entropy change on the torus?"""
    berry_phases = []
    entropy_changes = {name: [] for name in SINGLE_ENTROPY_NAMES}

    for i in range(len(torus_states)):
        row = i // n2
        col = i % n2
        # Adjacent in theta1 direction (where mixedness varies)
        j_t1 = ((row + 1) % n1) * n2 + col
        # Adjacent in phi direction
        j_t2 = row * n2 + (col + 1) % n2
        # Use both directions, prefer t1 for entropy variation
        bp_t1 = berry_phase_adjacent(torus_states, torus_coords, i, j_t1)
        bp_t2 = berry_phase_adjacent(torus_states, torus_coords, i, j_t2)
        bp = np.sqrt(bp_t1**2 + bp_t2**2)  # total Berry phase magnitude
        berry_phases.append(bp)

        ent_i = compute_single_entropies(torus_states[i])
        ent_j = compute_single_entropies(torus_states[j_t1])
        for name in SINGLE_ENTROPY_NAMES:
            entropy_changes[name].append(abs(ent_j[name] - ent_i[name]))

    correlations = {}
    bp_arr = np.array(berry_phases)
    for name in SINGLE_ENTROPY_NAMES:
        ec_arr = np.array(entropy_changes[name])
        if np.std(bp_arr) > EPS and np.std(ec_arr) > EPS:
            corr = float(np.corrcoef(bp_arr, ec_arr)[0, 1])
        else:
            corr = 0.0
        correlations[name] = round(corr, 4)

    return {
        "berry_phases_mean": round(float(np.mean(np.abs(berry_phases))), 6),
        "berry_phases_std": round(float(np.std(berry_phases)), 6),
        "entropy_berry_correlations": correlations,
        "strongest_correlation": max(correlations.items(), key=lambda x: abs(x[1]))[0],
    }


# ═══════════════════════════════════════════════════════════════════
# CROSS-TEST 2: Betti number vs discrimination
# ═══════════════════════════════════════════════════════════════════

def cross_test_betti_discrimination(matrix_results):
    """Does Betti number predict which entropy discriminates best?"""
    betti = {
        "flat": (0,),     # trivial
        "S1": (1,),       # b1=1
        "S2": (0,),       # b1=0 (but b2=1 for closed)
        "T2": (2,),       # b1=2
    }

    best_discriminator = {}
    for topo_name in ["flat", "S1", "S2", "T2"]:
        if topo_name not in matrix_results:
            continue
        topo = matrix_results[topo_name]
        best_name = "none"
        best_power = 0.0
        for ent_name in SINGLE_ENTROPY_NAMES + REFERENCE_ENTROPY_NAMES:
            if ent_name in topo and isinstance(topo[ent_name], dict):
                dp = topo[ent_name].get("discrimination_power")
                if dp is not None and dp > best_power:
                    best_power = dp
                    best_name = ent_name
        best_discriminator[topo_name] = {
            "betti_b1": betti.get(topo_name, (None,))[0],
            "best_entropy": best_name,
            "discrimination_power": round(best_power, 4),
        }

    return best_discriminator


# ═══════════════════════════════════════════════════════════════════
# CROSS-TEST 3: Entanglement detection threshold
# ═══════════════════════════════════════════════════════════════════

def cross_test_entanglement_threshold(n_points=50):
    """Which entropy FIRST detects entanglement as we interpolate
    from product to Bell state? rho(p) = (1-p)*rho_prod + p*rho_Bell"""

    # Fixed product state
    rho_A = random_dm(2)
    rho_B = random_dm(2)
    rho_prod = np.kron(rho_A, rho_B)

    # Bell state (Phi+)
    bell = BELL_KETS[0]
    rho_bell = bell @ bell.conj().T

    p_values = np.linspace(0, 1, n_points)

    # For each entropy, find p where it first deviates from product behavior
    cond_vals = []
    mi_vals = []
    ic_vals = []
    single_vals = {name: [] for name in SINGLE_ENTROPY_NAMES}

    for p in p_values:
        rho_p = (1 - p) * rho_prod + p * rho_bell
        rho_p = ensure_dm(rho_p)

        rho_pA = partial_trace_B(rho_p)
        rho_pB = partial_trace_A(rho_p)

        cond_vals.append(conditional_entropy(rho_p, rho_pB))
        mi_vals.append(mutual_information(rho_p, rho_pA, rho_pB))
        ic_vals.append(coherent_information(rho_p, rho_pB))

        ents = compute_single_entropies(rho_p)
        for name in SINGLE_ENTROPY_NAMES:
            single_vals[name].append(ents[name])

    # Detection thresholds
    thresholds = {}

    # Conditional entropy: first goes negative
    cond_arr = np.array(cond_vals)
    neg_idx = np.where(cond_arr < -0.01)[0]
    thresholds["conditional"] = float(p_values[neg_idx[0]]) if len(neg_idx) > 0 else None

    # Coherent info: first goes positive
    ic_arr = np.array(ic_vals)
    pos_idx = np.where(ic_arr > 0.01)[0]
    thresholds["coherent_info"] = float(p_values[pos_idx[0]]) if len(pos_idx) > 0 else None

    # MI: detect by deviation > 10% from product value
    mi_arr = np.array(mi_vals)
    mi_base = mi_arr[0]
    mi_dev_idx = np.where(np.abs(mi_arr - mi_base) > 0.1 * max(abs(mi_base), 0.01))[0]
    thresholds["mutual_info"] = float(p_values[mi_dev_idx[0]]) if len(mi_dev_idx) > 0 else None

    # Single-state entropies: detect by 10% deviation in joint state entropy
    for name in SINGLE_ENTROPY_NAMES:
        arr = np.array(single_vals[name])
        base = arr[0]
        dev_idx = np.where(np.abs(arr - base) > 0.1 * max(abs(base), 0.01))[0]
        thresholds[name] = float(p_values[dev_idx[0]]) if len(dev_idx) > 0 else None

    # Sort by earliest detection
    ranked = sorted(
        [(k, v) for k, v in thresholds.items() if v is not None],
        key=lambda x: x[1]
    )

    return {
        "thresholds": {k: round(v, 4) if v is not None else None for k, v in thresholds.items()},
        "detection_ranking": [{"entropy": k, "threshold_p": round(v, 4)} for k, v in ranked],
        "first_detector": ranked[0][0] if ranked else None,
        "interpolation_points": n_points,
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN SIMULATION
# ═══════════════════════════════════════════════════════════════════

def main():
    t0 = time.time()
    print("=" * 70)
    print("ENTROPY-TOPOLOGY COMPATIBILITY MATRIX")
    print("=" * 70)

    # ── Build all topologies ──
    print("\n[1/7] Building topological structures...")
    flat_states = build_flat_states(30)
    s1_states = build_s1_states(8)
    s2_states = build_s2_states(20)
    torus_states, torus_coords = build_torus_states(6, 6)
    product_states = build_product_states(30)
    entangled_states, mixedness_vals = build_entangled_states(30)

    print(f"  Flat: {len(flat_states)} random 2x2 density matrices")
    print(f"  S1:   {len(s1_states)} pure states on Bloch equator")
    print(f"  S2:   {len(s2_states)} pure states on Bloch sphere (Fibonacci)")
    print(f"  T2:   {len(torus_states)} states on torus (Hopf map)")
    print(f"  Product: {len(product_states)} separable 4x4 states")
    print(f"  Entangled: {len(entangled_states)} near-Bell 4x4 states")

    # ── Compute flat as reference ──
    print("\n[2/7] Computing FLAT (reference) entropies...")
    flat_res, flat_single_vals, flat_rel_vals = run_topology_entropies("flat", flat_states)
    flat_single_ref = {name: flat_single_vals[name] for name in SINGLE_ENTROPY_NAMES}
    flat_rel_ref = flat_rel_vals

    # ── S1 ──
    print("[3/7] Computing S1 (circle) entropies...")
    # Individual + mixture
    s1_res, _, _ = run_topology_entropies(
        "S1", s1_states,
        ref_single=flat_single_ref, ref_relative=flat_rel_ref
    )
    # Mixture entropy
    s1_mix = s1_mixture(s1_states)
    s1_mix_ents = compute_single_entropies(s1_mix)
    s1_res["mixture_entropies"] = {k: round(v, 6) for k, v in s1_mix_ents.items()}

    # MI between adjacent pairs
    s1_mi_values = []
    for i in range(len(s1_states)):
        rho_AB = s1_adjacent_product(s1_states, i)
        rho_A = partial_trace_B(rho_AB)
        rho_B = partial_trace_A(rho_AB)
        s1_mi_values.append(mutual_information(rho_AB, rho_A, rho_B))
    s1_res["adjacent_MI"] = {
        "mean": round(float(np.mean(s1_mi_values)), 6),
        "std": round(float(np.std(s1_mi_values)), 6),
        "values": [round(v, 6) for v in s1_mi_values],
    }

    # ── S2 ──
    print("[4/7] Computing S2 (sphere) entropies...")
    s2_res, _, _ = run_topology_entropies(
        "S2", s2_states,
        ref_single=flat_single_ref, ref_relative=flat_rel_ref
    )

    # ── T2 ──
    print("[5/7] Computing T2 (torus) entropies...")
    t2_res, _, _ = run_topology_entropies(
        "T2", torus_states,
        ref_single=flat_single_ref, ref_relative=flat_rel_ref
    )

    # ── Product states ──
    print("[6/7] Computing Product (separable) entropies...")
    # Also compute bipartite entropies for product states as reference
    prod_res, prod_single_vals, prod_rel_vals = run_topology_entropies(
        "product", product_states, is_bipartite=True,
        ref_single=flat_single_ref, ref_relative=flat_rel_ref
    )
    prod_bip_ref = {}
    for name in BIPARTITE_ENTROPY_NAMES:
        if isinstance(prod_res[name], dict) and "mean" in prod_res[name]:
            # Collect raw bipartite values
            bip_vals = []
            for rho in product_states:
                ents = compute_bipartite_entropies(rho)
                bip_vals.append(ents[name])
            prod_bip_ref[name] = bip_vals

    # ── Entangled states ──
    print("[7/7] Computing Entangled (Bell) entropies...")
    ent_res, _, _ = run_topology_entropies(
        "entangled", entangled_states, is_bipartite=True,
        ref_single=flat_single_ref, ref_relative=flat_rel_ref,
        ref_bipartite=prod_bip_ref if prod_bip_ref else None
    )

    # ── Assemble compatibility matrix ──
    matrix = {
        "flat": flat_res,
        "S1": s1_res,
        "S2": s2_res,
        "T2": t2_res,
        "product": prod_res,
        "entangled": ent_res,
    }

    # ── Cross-tests ──
    print("\n[CROSS-1] Berry phase vs entropy correlation on torus...")
    berry_result = cross_test_berry_entropy(torus_states, torus_coords, 6, 6)

    print("[CROSS-2] Betti number vs discrimination power...")
    betti_result = cross_test_betti_discrimination(matrix)

    print("[CROSS-3] Entanglement detection threshold sweep...")
    threshold_result = cross_test_entanglement_threshold(50)

    # ── Build summary compatibility table ──
    print("\n" + "=" * 70)
    print("COMPATIBILITY MATRIX (12 entropies x 6 topologies)")
    print("=" * 70)

    topo_order = ["flat", "S1", "S2", "T2", "product", "entangled"]
    all_ent_names = SINGLE_ENTROPY_NAMES + BIPARTITE_ENTROPY_NAMES + REFERENCE_ENTROPY_NAMES

    # Header
    header = f"{'Entropy':<16}" + "".join(f"{'  ' + t:<12}" for t in topo_order)
    print(header)
    print("-" * len(header))

    summary_table = {}
    for ent_name in all_ent_names:
        row = {}
        row_str = f"{ent_name:<16}"
        for topo_name in topo_order:
            cell = matrix[topo_name].get(ent_name, {})
            if isinstance(cell, dict):
                if cell.get("status", "").startswith("N/A"):
                    symbol = "  --"
                    row[topo_name] = "N/A"
                elif cell.get("trivial_zero", False):
                    symbol = "  T0"  # trivially zero
                    row[topo_name] = "trivial_zero"
                elif cell.get("trivial_max", False):
                    symbol = "  TM"  # trivially max
                    row[topo_name] = "trivial_max"
                elif cell.get("compatible", True):
                    mean = cell.get("mean", 0)
                    var = cell.get("variance", 0)
                    dp = cell.get("discrimination_power")
                    if dp is not None and dp > 1.0:
                        symbol = "  **"  # strong discriminator
                        row[topo_name] = "strong"
                    elif dp is not None and dp > 0.3:
                        symbol = "  * "  # moderate discriminator
                        row[topo_name] = "moderate"
                    elif var < 0.0001:
                        symbol = "  = "  # constant (low variance)
                        row[topo_name] = "constant"
                    else:
                        symbol = "  OK"  # compatible
                        row[topo_name] = "compatible"
                else:
                    symbol = "  X "  # incompatible
                    row[topo_name] = "incompatible"
            else:
                symbol = "  ? "
                row[topo_name] = "unknown"
            row_str += f"{symbol:<12}"
        print(row_str)
        summary_table[ent_name] = row

    print()
    print("Legend: ** = strong discriminator | * = moderate | OK = compatible")
    print("        T0 = trivially zero | TM = trivially max | = = constant | -- = N/A")

    # ── Separability checks ──
    print("\n" + "=" * 70)
    print("SEPARABILITY SIGNATURES")
    print("=" * 70)

    # Product states: S(A|B) >= 0 always?
    prod_cond = [compute_bipartite_entropies(rho)["conditional"] for rho in product_states]
    prod_ic = [compute_bipartite_entropies(rho)["coherent_info"] for rho in product_states]
    print(f"  Product S(A|B) >= 0: {all(v >= -0.01 for v in prod_cond)} "
          f"(min={min(prod_cond):.4f})")
    print(f"  Product I_c <= 0:    {all(v <= 0.01 for v in prod_ic)} "
          f"(max={max(prod_ic):.4f})")

    # Entangled states: any S(A|B) < 0?
    ent_cond = [compute_bipartite_entropies(rho)["conditional"] for rho in entangled_states]
    ent_ic = [compute_bipartite_entropies(rho)["coherent_info"] for rho in entangled_states]
    print(f"  Entangled S(A|B) < 0: {any(v < -0.01 for v in ent_cond)} "
          f"(min={min(ent_cond):.4f})")
    print(f"  Entangled I_c > 0:    {any(v > 0.01 for v in ent_ic)} "
          f"(max={max(ent_ic):.4f})")

    # ── Cross-test reports ──
    print("\n" + "=" * 70)
    print("CROSS-TEST 1: Berry Phase vs Entropy on Torus")
    print("=" * 70)
    print(f"  Mean |Berry phase|: {berry_result['berry_phases_mean']:.6f}")
    print(f"  Strongest correlation: {berry_result['strongest_correlation']}")
    for name, corr in berry_result["entropy_berry_correlations"].items():
        bar = "#" * int(abs(corr) * 20)
        print(f"    {name:<16} r={corr:+.4f}  {bar}")

    print("\n" + "=" * 70)
    print("CROSS-TEST 2: Betti Number vs Discrimination")
    print("=" * 70)
    for topo, info in betti_result.items():
        print(f"  {topo:<6} b1={info['betti_b1']}  best={info['best_entropy']:<16} "
              f"power={info['discrimination_power']:.4f}")

    print("\n" + "=" * 70)
    print("CROSS-TEST 3: Entanglement Detection Threshold")
    print("=" * 70)
    print(f"  First detector: {threshold_result['first_detector']}")
    print(f"  Detection ranking:")
    for item in threshold_result["detection_ranking"]:
        print(f"    p={item['threshold_p']:.4f}  {item['entropy']}")

    # ── Assemble results ──
    elapsed = time.time() - t0

    RESULTS["compatibility_matrix"] = matrix
    RESULTS["summary_table"] = summary_table
    RESULTS["cross_test_berry_entropy"] = berry_result
    RESULTS["cross_test_betti_discrimination"] = betti_result
    RESULTS["cross_test_entanglement_threshold"] = threshold_result
    RESULTS["separability_checks"] = {
        "product_conditional_all_nonneg": all(v >= -0.01 for v in prod_cond),
        "product_coherent_info_all_nonpos": all(v <= 0.01 for v in prod_ic),
        "entangled_conditional_some_neg": any(v < -0.01 for v in ent_cond),
        "entangled_coherent_info_some_pos": any(v > 0.01 for v in ent_ic),
    }
    RESULTS["metadata"] = {
        "elapsed_seconds": round(elapsed, 2),
        "n_entropy_types": len(all_ent_names),
        "n_topologies": len(topo_order),
        "total_cells": len(all_ent_names) * len(topo_order),
    }

    # ── Write output ──
    out_dir = pathlib.Path(__file__).parent / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "entropy_topology_compatibility_results.json"
    with open(out_path, "w") as f:
        json.dump(RESULTS, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
    print(f"Total time: {elapsed:.2f}s")
    print("DONE.")


if __name__ == "__main__":
    main()
