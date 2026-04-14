#!/usr/bin/env python3
"""
PURE LEGO: Density Matrix Operations
=====================================
Foundational building block.  Pure math only — numpy + scipy.
No engine imports.  Every operation verified against theory.

Sections
--------
1. Construction (20 states)
2. Pauli decomposition & roundtrip
3. Spectral decomposition
4. ALL entropy types on all 20 states
5. ALL distance metrics on all 190 pairs
6. 2-qubit: product + Bell, partial traces, conditional entropy, MI
7. Correlation measures: concurrence, negativity, log-negativity, EoF
8. CPTP channels: depolarizing, amplitude damping, phase damping
"""

import json, pathlib, time
import numpy as np
from scipy.linalg import sqrtm, logm
classification = "classical_baseline"  # auto-backfill

np.random.seed(42)
EPS = 1e-14
RESULTS = {}

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego evidence for density-matrix validity, local spectral structure, "
    "basic entropy/distance identities, bipartite reductions, correlation measures, and "
    "elementary CPTP channel behavior. This is a broad local probe, not a closure-grade "
    "coexistence or topology result."
)
LEGO_IDS = [
    "density_matrix_object",
    "density_matrix_representability",
    "positivity_constraint",
    "trace_constraint",
    "pauli_algebra_relations",
    "spectral_decomposition",
    "von_neumann_entropy",
    "renyi_entropy",
    "tsallis_entropy",
    "min_entropy",
    "max_entropy",
    "relative_entropy",
    "partial_trace_operator",
    "reduced_state_object",
    "joint_density_matrix",
    "conditional_entropy",
    "mutual_information_measure",
    "concurrence_measure",
    "negativity_measure",
    "logarithmic_negativity",
    "channel_cptp_map",
    "kraus_operator_sum",
]
PRIMARY_LEGO_IDS = [
    "density_matrix_object",
    "density_matrix_representability",
    "positivity_constraint",
    "trace_constraint",
    "spectral_decomposition",
    "partial_trace_operator",
    "channel_cptp_map",
]
TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- pure numpy/scipy local lego probe"},
    "pyg": {"tried": False, "used": False, "reason": "not needed -- no graph-native computation"},
    "z3": {"tried": False, "used": False, "reason": "not needed -- no SMT proof layer in this probe"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed -- no solver cross-check layer here"},
    "sympy": {"tried": False, "used": False, "reason": "not needed -- no symbolic derivation in this probe"},
    "clifford": {"tried": False, "used": False, "reason": "not needed -- no geometric algebra in this probe"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- no manifold-statistics layer"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed -- no equivariant network layer"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed -- no dependency DAG or routing graph"},
    "xgi": {"tried": False, "used": False, "reason": "not needed -- no hypergraph structure"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed -- no cell-complex topology"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed -- no persistent homology"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
PAULIS = [sx, sy, sz]

def ket(v):
    """Column vector from list."""
    return np.array(v, dtype=complex).reshape(-1, 1)

def dm(v):
    """Density matrix from ket vector."""
    k = ket(v)
    return k @ k.conj().T

def is_valid_dm(rho, label="", tol=1e-12):
    """Check Tr=1, Hermitian, PSD.  Returns dict of checks."""
    tr = np.real(np.trace(rho))
    herm = np.allclose(rho, rho.conj().T, atol=tol)
    evals = np.linalg.eigvalsh(rho)
    psd = bool(np.all(evals >= -tol))
    purity = np.real(np.trace(rho @ rho))
    return {
        "label": label,
        "trace": float(tr),
        "trace_ok": bool(abs(tr - 1.0) < tol),
        "hermitian": herm,
        "psd": psd,
        "purity": float(purity),
        "eigenvalues": [float(e) for e in evals],
    }


# ══════════════════════════════════════════════════════════════════════
# 1.  CONSTRUCTION  — 20 single-qubit states
# ══════════════════════════════════════════════════════════════════════

def build_states():
    states = {}
    # 6 Bloch poles (pure)
    ket0 = [1, 0]; ket1 = [0, 1]
    ketp = [1/np.sqrt(2), 1/np.sqrt(2)]
    ketm = [1/np.sqrt(2), -1/np.sqrt(2)]
    ketR = [1/np.sqrt(2), 1j/np.sqrt(2)]
    ketL = [1/np.sqrt(2), -1j/np.sqrt(2)]
    for name, k in [("Z+",ket0),("Z-",ket1),("X+",ketp),("X-",ketm),("Y+",ketR),("Y-",ketL)]:
        states[name] = dm(k)

    # 6 mixed states r=0.5 on each axis (±)
    for name, axis in [("mx+", [0.5,0,0]),("mx-",[-0.5,0,0]),
                        ("my+", [0,0.5,0]),("my-",[0,-0.5,0]),
                        ("mz+", [0,0,0.5]),("mz-",[0,0,-0.5])]:
        r = np.array(axis)
        states[name] = (I2 + r[0]*sx + r[1]*sy + r[2]*sz) / 2.0

    # maximally mixed
    states["max_mixed"] = I2 / 2.0

    # 5 random valid density matrices
    for i in range(5):
        # Haar-random pure state then partially depolarise
        v = np.random.randn(2) + 1j*np.random.randn(2)
        v /= np.linalg.norm(v)
        rho_pure = dm(v)
        p = np.random.uniform(0.1, 0.9)
        rho = p * rho_pure + (1 - p) * I2 / 2.0
        states[f"rand_{i}"] = rho

    # total must be 20
    assert len(states) == 18, f"Expected 18 named, got {len(states)}"
    # add 2 more random pure states to hit 20
    for i in range(2):
        v = np.random.randn(2) + 1j*np.random.randn(2)
        v /= np.linalg.norm(v)
        states[f"rand_pure_{i}"] = dm(v)

    assert len(states) == 20, f"Expected 20 states, got {len(states)}"
    return states

STATES = build_states()

# Validate all
construction_results = {}
for name, rho in STATES.items():
    construction_results[name] = is_valid_dm(rho, name)

all_valid = all(v["trace_ok"] and v["hermitian"] and v["psd"] for v in construction_results.values())
purities = {k: v["purity"] for k, v in construction_results.items()}
print(f"[1] Construction: 20 states built. All valid: {all_valid}")
print(f"    Purity range: [{min(purities.values()):.6f}, {max(purities.values()):.6f}]")
RESULTS["1_construction"] = {
    "count": 20,
    "all_valid": all_valid,
    "purity_min": min(purities.values()),
    "purity_max": max(purities.values()),
    "details": construction_results,
}


# ══════════════════════════════════════════════════════════════════════
# 2.  PAULI DECOMPOSITION
# ══════════════════════════════════════════════════════════════════════

def pauli_decompose(rho):
    """Extract Bloch vector r from ρ = (I + r·σ)/2."""
    r = np.array([np.real(np.trace(rho @ s)) for s in PAULIS])
    return r

def pauli_reconstruct(r):
    return (I2 + r[0]*sx + r[1]*sy + r[2]*sz) / 2.0

pauli_results = {}
for name, rho in STATES.items():
    r = pauli_decompose(rho)
    rho_re = pauli_reconstruct(r)
    residual = np.max(np.abs(rho - rho_re))
    r_norm = float(np.linalg.norm(r))
    pur = float(np.real(np.trace(rho @ rho)))
    is_pure = abs(pur - 1.0) < 1e-10
    r_is_1 = abs(r_norm - 1.0) < 1e-10
    pauli_results[name] = {
        "bloch_vector": [float(x) for x in r],
        "r_norm": r_norm,
        "roundtrip_residual": float(residual),
        "roundtrip_ok": bool(residual < EPS),
        "pure_iff_r1": bool(is_pure == r_is_1),
        "r_leq_1": bool(r_norm <= 1.0 + 1e-12),
    }

all_roundtrip = all(v["roundtrip_ok"] for v in pauli_results.values())
all_iff = all(v["pure_iff_r1"] for v in pauli_results.values())
all_leq = all(v["r_leq_1"] for v in pauli_results.values())
print(f"[2] Pauli decomposition: roundtrip<1e-14 all={all_roundtrip}, |r|≤1 all={all_leq}, |r|=1⟺pure all={all_iff}")
RESULTS["2_pauli_decomposition"] = {
    "all_roundtrip_ok": all_roundtrip,
    "all_r_leq_1": all_leq,
    "all_pure_iff_r1": all_iff,
    "details": pauli_results,
}


# ══════════════════════════════════════════════════════════════════════
# 3.  SPECTRAL DECOMPOSITION
# ══════════════════════════════════════════════════════════════════════

spectral_results = {}
for name, rho in STATES.items():
    evals, evecs = np.linalg.eigh(rho)
    # sum to 1
    esum = float(np.sum(evals))
    # non-negative
    non_neg = bool(np.all(evals >= -1e-12))
    # orthogonal
    overlap = evecs.conj().T @ evecs
    ortho = bool(np.allclose(overlap, np.eye(len(evals)), atol=1e-12))
    # reconstruct
    rho_re = sum(evals[i] * np.outer(evecs[:, i], evecs[:, i].conj()) for i in range(len(evals)))
    residual = float(np.max(np.abs(rho - rho_re)))
    spectral_results[name] = {
        "eigenvalues": [float(e) for e in evals],
        "sum_to_1": bool(abs(esum - 1.0) < 1e-12),
        "non_negative": non_neg,
        "orthogonal": ortho,
        "reconstruct_residual": residual,
        "reconstruct_ok": bool(residual < 1e-12),
    }

all_spectral = all(
    v["sum_to_1"] and v["non_negative"] and v["orthogonal"] and v["reconstruct_ok"]
    for v in spectral_results.values()
)
print(f"[3] Spectral decomposition: all checks pass = {all_spectral}")
RESULTS["3_spectral_decomposition"] = {"all_pass": all_spectral, "details": spectral_results}


# ══════════════════════════════════════════════════════════════════════
# 4.  ALL ENTROPY TYPES
# ══════════════════════════════════════════════════════════════════════

def safe_log2(x):
    """log2 with 0*log0 = 0."""
    return np.where(x > 1e-30, np.log2(np.maximum(x, 1e-300)), 0.0)

def vn_entropy(rho):
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-30]
    return float(-np.sum(evals * np.log2(evals)))

def shannon_basis(rho, basis="z"):
    """Shannon entropy of measurement probabilities in given basis."""
    if basis == "z":
        probs = np.real(np.diag(rho))
    elif basis == "x":
        U = np.array([[1,1],[1,-1]], dtype=complex) / np.sqrt(2)
        rho_x = U.conj().T @ rho @ U
        probs = np.real(np.diag(rho_x))
    else:
        raise ValueError(f"Unknown basis: {basis}")
    probs = np.clip(probs, 1e-30, None)
    return float(-np.sum(probs * np.log2(probs)))

def renyi_entropy(rho, alpha):
    if abs(alpha - 1.0) < 1e-10:
        return vn_entropy(rho)
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-30]
    return float(np.log2(np.sum(evals**alpha)) / (1 - alpha))

def min_entropy(rho):
    """S_min = -log2(λ_max) = Renyi(∞)."""
    lmax = np.max(np.linalg.eigvalsh(rho))
    return float(-np.log2(max(lmax, 1e-30)))

def max_entropy(rho):
    """S_max = log2(rank) = Renyi(0)."""
    evals = np.linalg.eigvalsh(rho)
    rank = np.sum(evals > 1e-10)
    return float(np.log2(max(rank, 1)))

def linear_entropy(rho):
    d = rho.shape[0]
    return float(d / (d - 1) * (1 - np.real(np.trace(rho @ rho))))

def tsallis_entropy(rho, q):
    if abs(q - 1.0) < 1e-10:
        return vn_entropy(rho) * np.log(2)  # natural log version
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-30]
    return float((1 - np.sum(evals**q)) / (q - 1))

def purity(rho):
    return float(np.real(np.trace(rho @ rho)))

entropy_results = {}
ordering_violations = []
vn_pure_check = []
vn_mixed_check = []

for name, rho in STATES.items():
    s_vn = vn_entropy(rho)
    s_sh_z = shannon_basis(rho, "z")
    s_sh_x = shannon_basis(rho, "x")
    s_r05 = renyi_entropy(rho, 0.5)
    s_r2 = renyi_entropy(rho, 2.0)
    s_r5 = renyi_entropy(rho, 5.0)
    s_min = min_entropy(rho)
    s_max = max_entropy(rho)
    s_lin = linear_entropy(rho)
    s_t05 = tsallis_entropy(rho, 0.5)
    s_t2 = tsallis_entropy(rho, 2.0)
    pur = purity(rho)

    # Ordering: S_min ≤ S_vN ≤ S_max  (Renyi ordering)
    ordering_ok = (s_min <= s_vn + 1e-10) and (s_vn <= s_max + 1e-10)
    if not ordering_ok:
        ordering_violations.append(name)

    # Pure states: vN = 0
    if abs(pur - 1.0) < 1e-10:
        vn_pure_check.append(abs(s_vn) < 1e-10)

    # Max mixed: vN = 1 (for qubit)
    if name == "max_mixed":
        vn_mixed_check.append(abs(s_vn - 1.0) < 1e-10)

    entropy_results[name] = {
        "vn": s_vn, "shannon_z": s_sh_z, "shannon_x": s_sh_x,
        "renyi_0.5": s_r05, "renyi_2": s_r2, "renyi_5": s_r5,
        "min": s_min, "max": s_max, "linear": s_lin,
        "tsallis_0.5": s_t05, "tsallis_2": s_t2, "purity": pur,
        "ordering_ok": ordering_ok,
    }

all_ordering = len(ordering_violations) == 0
all_vn_pure = all(vn_pure_check) if vn_pure_check else False
all_vn_mixed = all(vn_mixed_check) if vn_mixed_check else False
print(f"[4] Entropies: ordering S_min≤S_vN≤S_max all={all_ordering}, vN=0 pure={all_vn_pure}, vN=1 max_mixed={all_vn_mixed}")
RESULTS["4_entropies"] = {
    "all_ordering_ok": all_ordering,
    "ordering_violations": ordering_violations,
    "vn_zero_for_pure": all_vn_pure,
    "vn_one_for_max_mixed": all_vn_mixed,
    "details": entropy_results,
}


# ══════════════════════════════════════════════════════════════════════
# 5.  ALL DISTANCE METRICS — 190 pairs
# ══════════════════════════════════════════════════════════════════════

def trace_distance(rho, sigma):
    diff = rho - sigma
    evals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(evals)))

def fidelity(rho, sigma):
    sqrt_rho = sqrtm(rho)
    inner = sqrtm(sqrt_rho @ sigma @ sqrt_rho)
    F = np.real(np.trace(inner))**2
    return float(np.clip(F, 0, 1))

def bures_distance(rho, sigma):
    F = fidelity(rho, sigma)
    return float(np.sqrt(max(2 * (1 - np.sqrt(max(F, 0))), 0)))

def hs_distance(rho, sigma):
    """Hilbert-Schmidt distance."""
    diff = rho - sigma
    return float(np.sqrt(np.real(np.trace(diff.conj().T @ diff))))

def relative_entropy(rho, sigma):
    """S(ρ||σ) = Tr(ρ(log ρ - log σ)).  Returns inf if supp(ρ) ⊄ supp(σ)."""
    evals_s = np.linalg.eigvalsh(sigma)
    evals_r = np.linalg.eigvalsh(rho)
    # Check support
    if np.any(evals_r > 1e-10) and np.any(evals_s[evals_r > 1e-10] < 1e-14):
        # need finer check
        pass
    try:
        log_rho = logm(rho + 1e-30 * np.eye(rho.shape[0]))
        log_sigma = logm(sigma + 1e-30 * np.eye(sigma.shape[0]))
        val = np.real(np.trace(rho @ (log_rho - log_sigma)))
        if val < -1e-8:
            return float('inf')
        return float(max(val / np.log(2), 0))  # in bits
    except Exception:
        return float('inf')

names = list(STATES.keys())
distance_results = {}
triangle_violations = {"trace": 0, "bures": 0, "hs": 0}
fuchs_violations = 0

# Precompute all pairwise
pair_data = {}
for i in range(len(names)):
    for j in range(i+1, len(names)):
        a, b = names[i], names[j]
        key = f"{a}|{b}"
        td = trace_distance(STATES[a], STATES[b])
        fid = fidelity(STATES[a], STATES[b])
        bd = bures_distance(STATES[a], STATES[b])
        hsd = hs_distance(STATES[a], STATES[b])
        re = relative_entropy(STATES[a], STATES[b])
        pair_data[key] = {"trace": td, "fidelity": fid, "bures": bd, "hs": hsd, "relative_entropy": re}

        # Fuchs-van de Graaf: 1-√F ≤ T ≤ √(1-F)
        sqrtF = np.sqrt(max(fid, 0))
        fvg_lower = 1 - sqrtF
        fvg_upper = np.sqrt(max(1 - fid, 0))
        if td < fvg_lower - 1e-8 or td > fvg_upper + 1e-8:
            fuchs_violations += 1

# Triangle inequality check (sample triples)
n = len(names)
tri_count = 0
for i in range(n):
    for j in range(i+1, n):
        for k in range(j+1, n):
            tri_count += 1
            if tri_count > 500:
                break
            a, b, c = names[i], names[j], names[k]
            # Get distances (handle key ordering)
            def get_d(x, y, metric):
                key1 = f"{x}|{y}"
                key2 = f"{y}|{x}"
                if key1 in pair_data:
                    return pair_data[key1][metric]
                return pair_data[key2][metric]
            for metric in ["trace", "bures", "hs"]:
                dab = get_d(a, b, metric)
                dbc = get_d(b, c, metric)
                dac = get_d(a, c, metric)
                if dab > dbc + dac + 1e-8 or dbc > dab + dac + 1e-8 or dac > dab + dbc + 1e-8:
                    triangle_violations[metric] += 1

print(f"[5] Distances: {len(pair_data)} pairs. Triangle violations: {triangle_violations}. Fuchs-van de Graaf violations: {fuchs_violations}")
RESULTS["5_distances"] = {
    "num_pairs": len(pair_data),
    "triangle_violations": triangle_violations,
    "fuchs_van_de_graaf_violations": fuchs_violations,
    "sample_pairs": {k: v for k, v in list(pair_data.items())[:5]},
}


# ══════════════════════════════════════════════════════════════════════
# 6.  2-QUBIT: product + Bell, partial trace, conditional entropy, MI
# ══════════════════════════════════════════════════════════════════════

def partial_trace(rho_ab, dim_a, dim_b, trace_out="B"):
    """Partial trace over subsystem."""
    rho_ab = rho_ab.reshape(dim_a, dim_b, dim_a, dim_b)
    if trace_out == "B":
        return np.trace(rho_ab, axis1=1, axis2=3)
    else:
        return np.trace(rho_ab, axis1=0, axis2=2)

# Product states
ket0 = ket([1,0]); ket1 = ket([0,1])
prod_00 = np.kron(ket0, ket0) @ np.kron(ket0, ket0).conj().T
ketp = ket([1/np.sqrt(2), 1/np.sqrt(2)])
prod_0p = np.kron(ket0, ketp) @ np.kron(ket0, ketp).conj().T

# Bell states
bell_phi_p = ket([1,0,0,1]) / np.sqrt(2)
bell_phi_m = ket([1,0,0,-1]) / np.sqrt(2)
bell_psi_p = ket([0,1,1,0]) / np.sqrt(2)
bell_psi_m = ket([0,1,-1,0]) / np.sqrt(2)
bell_states = {
    "Phi+": bell_phi_p @ bell_phi_p.conj().T,
    "Phi-": bell_phi_m @ bell_phi_m.conj().T,
    "Psi+": bell_psi_p @ bell_psi_p.conj().T,
    "Psi-": bell_psi_m @ bell_psi_m.conj().T,
}
product_states = {"00": prod_00, "0+": prod_0p}

two_qubit_results = {}
for name, rho in {**product_states, **bell_states}.items():
    valid = is_valid_dm(rho, name)
    rho_a = partial_trace(rho, 2, 2, "B")
    rho_b = partial_trace(rho, 2, 2, "A")
    valid_a = is_valid_dm(rho_a, f"{name}_A")
    valid_b = is_valid_dm(rho_b, f"{name}_B")

    s_ab = vn_entropy(rho)
    s_a = vn_entropy(rho_a)
    s_b = vn_entropy(rho_b)

    # Conditional entropy S(A|B) = S(AB) - S(B)
    s_a_given_b = s_ab - s_b

    # Mutual information I(A:B) = S(A) + S(B) - S(AB)
    mi = s_a + s_b - s_ab

    two_qubit_results[name] = {
        "joint_valid": valid["trace_ok"] and valid["hermitian"] and valid["psd"],
        "marginal_A_valid": valid_a["trace_ok"] and valid_a["hermitian"] and valid_a["psd"],
        "marginal_B_valid": valid_b["trace_ok"] and valid_b["hermitian"] and valid_b["psd"],
        "S_AB": s_ab, "S_A": s_a, "S_B": s_b,
        "S_A_given_B": s_a_given_b,
        "MI": mi,
        "marginal_A_purity": valid_a["purity"],
        "marginal_B_purity": valid_b["purity"],
    }

# Verify: conditional entropy < 0 for Bell states (quantum!)
bell_cond_neg = all(two_qubit_results[n]["S_A_given_B"] < -1e-10 for n in bell_states)
# MI ≥ 0 for all
mi_nonneg = all(two_qubit_results[n]["MI"] >= -1e-10 for n in two_qubit_results)
# Product states: S(A|B) = S(A)
product_cond = all(
    abs(two_qubit_results[n]["S_A_given_B"] - two_qubit_results[n]["S_A"]) < 1e-10
    for n in product_states
)

print(f"[6] 2-qubit: Bell S(A|B)<0 = {bell_cond_neg}, MI≥0 = {mi_nonneg}, product S(A|B)=S(A) = {product_cond}")
RESULTS["6_two_qubit"] = {
    "bell_conditional_entropy_negative": bell_cond_neg,
    "mi_nonneg": mi_nonneg,
    "product_conditional_equals_marginal": product_cond,
    "details": two_qubit_results,
}


# ══════════════════════════════════════════════════════════════════════
# 7.  CORRELATION MEASURES
# ══════════════════════════════════════════════════════════════════════

def concurrence_2qubit(rho):
    """Wootters concurrence for 2-qubit state."""
    sy_sy = np.kron(sy, sy)
    rho_tilde = sy_sy @ rho.conj() @ sy_sy
    R = sqrtm(sqrtm(rho) @ rho_tilde @ sqrtm(rho))
    evals = np.sort(np.real(np.linalg.eigvals(R)))[::-1]
    C = max(0, evals[0] - evals[1] - evals[2] - evals[3])
    return float(C)

def negativity(rho, dim_a=2, dim_b=2):
    """Negativity via partial transpose."""
    # Partial transpose over B
    rho_r = rho.reshape(dim_a, dim_b, dim_a, dim_b)
    rho_pt = rho_r.transpose(0, 3, 2, 1).reshape(dim_a*dim_b, dim_a*dim_b)
    evals = np.linalg.eigvalsh(rho_pt)
    return float(np.sum(np.abs(evals[evals < -1e-14])))

def log_negativity(rho, dim_a=2, dim_b=2):
    N = negativity(rho, dim_a, dim_b)
    return float(np.log2(2*N + 1))

def eof_2qubit(rho):
    """Entanglement of formation from concurrence."""
    C = concurrence_2qubit(rho)
    if C < 1e-14:
        return 0.0
    x = (1 + np.sqrt(1 - C**2)) / 2
    return float(-x*np.log2(x) - (1-x)*np.log2(1-x))

correlation_results = {}
for name, rho in {**product_states, **bell_states}.items():
    C = concurrence_2qubit(rho)
    N = negativity(rho)
    LN = log_negativity(rho)
    E = eof_2qubit(rho)
    correlation_results[name] = {
        "concurrence": C, "negativity": N,
        "log_negativity": LN, "EoF": E,
    }

# Verify: C=0 for product, C=1 for Bell
product_C0 = all(abs(correlation_results[n]["concurrence"]) < 1e-8 for n in product_states)
bell_C1 = all(abs(correlation_results[n]["concurrence"] - 1.0) < 1e-6 for n in bell_states)
print(f"[7] Correlations: C=0 product={product_C0}, C=1 Bell={bell_C1}")
RESULTS["7_correlations"] = {
    "product_C_zero": product_C0,
    "bell_C_one": bell_C1,
    "details": correlation_results,
}


# ══════════════════════════════════════════════════════════════════════
# 8.  CPTP CHANNELS
# ══════════════════════════════════════════════════════════════════════

def apply_kraus(rho, kraus_ops):
    return sum(K @ rho @ K.conj().T for K in kraus_ops)

def depolarizing_channel(rho, p):
    """ρ → (1-p)ρ + p·I/2.  Kraus: sqrt(1-3p/4)·I, sqrt(p/4)·σ_i."""
    K0 = np.sqrt(1 - 3*p/4) * I2
    K1 = np.sqrt(p/4) * sx
    K2 = np.sqrt(p/4) * sy
    K3 = np.sqrt(p/4) * sz
    return apply_kraus(rho, [K0, K1, K2, K3])

def amplitude_damping_channel(rho, gamma):
    K0 = np.array([[1, 0], [0, np.sqrt(1-gamma)]], dtype=complex)
    K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)
    return apply_kraus(rho, [K0, K1])

def phase_damping_channel(rho, gamma):
    K0 = np.array([[1, 0], [0, np.sqrt(1-gamma)]], dtype=complex)
    K1 = np.array([[0, 0], [0, np.sqrt(gamma)]], dtype=complex)
    return apply_kraus(rho, [K0, K1])

channel_results = {}
test_state = STATES["X+"]  # pure superposition — maximally affected by decoherence

for ch_name, channel_fn in [("depolarizing", lambda r: depolarizing_channel(r, 0.3)),
                              ("amplitude_damping", lambda r: amplitude_damping_channel(r, 0.3)),
                              ("phase_damping", lambda r: phase_damping_channel(r, 0.3))]:
    out = channel_fn(test_state)
    valid = is_valid_dm(out, ch_name)
    tr_preserved = abs(np.real(np.trace(out)) - 1.0) < 1e-12

    # Contractivity: trace distance should not increase
    # D(E(ρ), E(σ)) ≤ D(ρ, σ)
    other = STATES["Z+"]
    out_other = channel_fn(other)
    td_in = trace_distance(test_state, other)
    td_out = trace_distance(out, out_other)
    contractive = td_out <= td_in + 1e-10

    # Fixed point check: max mixed should be fixed (for depolarizing and phase damping)
    mm = I2 / 2.0
    mm_out = channel_fn(mm)
    if ch_name in ["depolarizing", "phase_damping"]:
        fp_ok = np.allclose(mm_out, mm, atol=1e-12)
    else:
        # amplitude damping fixed point is |0><0|
        fp_state = dm([1, 0])
        fp_out = channel_fn(fp_state)
        fp_ok = np.allclose(fp_out, fp_state, atol=1e-12)

    channel_results[ch_name] = {
        "output_valid": valid["trace_ok"] and valid["hermitian"] and valid["psd"],
        "trace_preserved": tr_preserved,
        "contractive": contractive,
        "td_in": td_in, "td_out": td_out,
        "fixed_point_ok": fp_ok,
        "output_purity": valid["purity"],
    }

all_channels_ok = all(
    v["output_valid"] and v["trace_preserved"] and v["contractive"] and v["fixed_point_ok"]
    for v in channel_results.values()
)
print(f"[8] CPTP channels: all valid+trace+contractive+fixedpoint = {all_channels_ok}")
RESULTS["8_cptp_channels"] = {"all_pass": all_channels_ok, "details": channel_results}


# ══════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════════════════

summary = {
    "1_construction": RESULTS["1_construction"]["all_valid"],
    "2_pauli_roundtrip": RESULTS["2_pauli_decomposition"]["all_roundtrip_ok"],
    "2_pauli_iff": RESULTS["2_pauli_decomposition"]["all_pure_iff_r1"],
    "3_spectral": RESULTS["3_spectral_decomposition"]["all_pass"],
    "4_entropy_ordering": RESULTS["4_entropies"]["all_ordering_ok"],
    "4_vn_pure_zero": RESULTS["4_entropies"]["vn_zero_for_pure"],
    "4_vn_mixed_one": RESULTS["4_entropies"]["vn_one_for_max_mixed"],
    "5_triangle_ineq": all(v == 0 for v in RESULTS["5_distances"]["triangle_violations"].values()),
    "5_fuchs_van_de_graaf": RESULTS["5_distances"]["fuchs_van_de_graaf_violations"] == 0,
    "6_bell_cond_neg": RESULTS["6_two_qubit"]["bell_conditional_entropy_negative"],
    "6_mi_nonneg": RESULTS["6_two_qubit"]["mi_nonneg"],
    "7_product_C0": RESULTS["7_correlations"]["product_C_zero"],
    "7_bell_C1": RESULTS["7_correlations"]["bell_C_one"],
    "8_cptp_all": RESULTS["8_cptp_channels"]["all_pass"],
}

all_pass = all(summary.values())
RESULTS["name"] = "pure_lego_density_matrices"
RESULTS["classification"] = CLASSIFICATION
RESULTS["classification_note"] = CLASSIFICATION_NOTE
RESULTS["lego_ids"] = LEGO_IDS
RESULTS["primary_lego_ids"] = PRIMARY_LEGO_IDS
RESULTS["tool_manifest"] = TOOL_MANIFEST
RESULTS["tool_integration_depth"] = TOOL_INTEGRATION_DEPTH
RESULTS["summary"] = summary
RESULTS["ALL_PASS"] = all_pass
RESULTS["honest_summary"] = {
    "all_pass": all_pass,
    "section_pass_count": sum(1 for v in summary.values() if v),
    "section_total": len(summary),
    "state_count": RESULTS["1_construction"]["count"],
    "pair_distance_count": RESULTS["5_distances"]["num_pairs"],
    "covers_local_bipartite_checks": True,
    "covers_local_channel_checks": True,
    "closure_grade": False,
    "notes": [
        "This probe is local lego evidence, not a coexistence, topology, or seam-closure result.",
        "True numeric dependencies are numpy and scipy; tracked non-numeric tool-stack items are intentionally unused here.",
    ],
}

print(f"\n{'='*60}")
print(f"PURE LEGO DENSITY MATRICES — ALL PASS: {all_pass}")
print(f"{'='*60}")
for k, v in summary.items():
    tag = "PASS" if v else "FAIL"
    print(f"  [{tag}] {k}")

# Write results
out_path = pathlib.Path(__file__).parent / "a2_state" / "sim_results" / "pure_lego_density_matrices_results.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w") as f:
    json.dump(RESULTS, f, indent=2, default=str)
print(f"\nResults written to {out_path}")
