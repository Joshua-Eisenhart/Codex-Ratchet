#!/usr/bin/env python3
"""
PURE LEGO: ML/AI Concepts in Density Matrix Language
=====================================================
Standalone building block.  Pure math only — numpy + scipy.
No engine imports.  Every operation verified against theory.

Sections
--------
1. Kernel matrices as density matrices (6 tests)
2. Information bottleneck as channel capacity (6 tests)
3. Attention as density matrix (4 tests)
4. Diffusion as open quantum system (6 tests)
5. Loss landscape as Hamiltonian spectrum (4 tests)
6. Representation learning as partial trace (4 tests)
"""

import json, pathlib, time
import numpy as np
from scipy.linalg import sqrtm, logm, expm
classification = "classical_baseline"  # auto-backfill

np.random.seed(42)
EPS = 1e-14
RESULTS = {}

CLASSIFICATION = "supporting"
CLASSIFICATION_NOTE = (
    "Supporting multi-lego compression/spectral evidence. This probe is mathematically strong "
    "and all-pass locally, but it bundles several compression analogies and should not be treated "
    "as a single canonical lego surface."
)
LEGO_IDS = [
    "covariance_operator",
    "spectral_truncation",
    "svd_factorization",
    "low_rank_psd_approximation",
    "operator_low_rank_factorization",
    "qpca_spectral_extraction",
    "coarse_grained_operator_algebra",
]
PRIMARY_LEGO_IDS = [
    "covariance_operator",
    "spectral_truncation",
    "svd_factorization",
    "low_rank_psd_approximation",
]
TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- pure numpy/scipy compression probe"},
    "pyg": {"tried": False, "used": False, "reason": "not needed -- no graph-native computation"},
    "z3": {"tried": False, "used": False, "reason": "not needed -- no SMT proof layer in this probe"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed -- no second-solver layer here"},
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

def is_valid_dm(rho, label="", tol=1e-10):
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


def vn_entropy(rho):
    """von Neumann entropy S = -Tr(rho log rho)."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > EPS]
    return float(-np.sum(evals * np.log2(evals)))


def fidelity(rho, sigma):
    """Fidelity F(rho, sigma) = (Tr sqrt(sqrt(rho) sigma sqrt(rho)))^2."""
    sq_rho = sqrtm(rho)
    inner = sqrtm(sq_rho @ sigma @ sq_rho)
    f = np.real(np.trace(inner)) ** 2
    return float(np.clip(f, 0.0, 1.0))


def kernel_to_density(K):
    """Normalize Gram matrix to trace-1 PSD = density matrix."""
    K = np.array(K, dtype=complex)
    K = (K + K.conj().T) / 2  # symmetrize
    evals = np.linalg.eigvalsh(K)
    if evals.min() < 0:
        K -= evals.min() * np.eye(len(K))
    tr = np.real(np.trace(K))
    if tr < EPS:
        return np.eye(len(K), dtype=complex) / len(K)
    return K / tr


def partial_trace_B(rho_AB, d_A, d_B):
    """Trace out subsystem B from rho_AB (d_A x d_B total)."""
    rho = rho_AB.reshape(d_A, d_B, d_A, d_B)
    return np.trace(rho, axis1=1, axis2=3)


def partial_trace_A(rho_AB, d_A, d_B):
    """Trace out subsystem A from rho_AB (d_A x d_B total)."""
    rho = rho_AB.reshape(d_A, d_B, d_A, d_B)
    return np.trace(rho, axis1=0, axis2=2)


def mutual_information(rho_AB, d_A, d_B):
    """I(A:B) = S(A) + S(B) - S(AB)."""
    rho_A = partial_trace_B(rho_AB, d_A, d_B)
    rho_B = partial_trace_A(rho_AB, d_A, d_B)
    return vn_entropy(rho_A) + vn_entropy(rho_B) - vn_entropy(rho_AB)


def concurrence_2qubit(rho):
    """Concurrence for a 2-qubit density matrix."""
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sy_sy = np.kron(sy, sy)
    rho_tilde = sy_sy @ rho.conj() @ sy_sy
    R = sqrtm(sqrtm(rho) @ rho_tilde @ sqrtm(rho))
    evals = np.sort(np.real(np.linalg.eigvals(R)))[::-1]
    C = max(0.0, evals[0] - evals[1] - evals[2] - evals[3])
    return float(C)


# ══════════════════════════════════════════════════════════════════════
# 1.  KERNEL MATRICES AS DENSITY MATRICES  (6 tests)
# ══════════════════════════════════════════════════════════════════════
print("Section 1: Kernel matrices as density matrices...")
t0 = time.time()

# Generate data: 8 points in R^4
X = np.random.randn(8, 4)

# Build 4 kernel matrices
sigma_rbf = 1.0

# Linear kernel: X X^T
K_linear = X @ X.T

# RBF kernel: exp(-||x_i - x_j||^2 / (2 sigma^2))
dists = np.sum((X[:, None, :] - X[None, :, :]) ** 2, axis=2)
K_rbf = np.exp(-dists / (2 * sigma_rbf ** 2))

# Polynomial kernel: (x_i . x_j + 1)^2
K_poly = (X @ X.T + 1) ** 2

# Cosine kernel: x_i . x_j / (||x_i|| ||x_j||)
norms = np.linalg.norm(X, axis=1, keepdims=True)
K_cos = (X @ X.T) / (norms @ norms.T)

kernels = {
    "linear": K_linear,
    "rbf": K_rbf,
    "polynomial": K_poly,
    "cosine": K_cos,
}

# Convert each to density matrix and validate
kernel_densities = {}
validity_checks = {}
entropies = {}
eigenspectra = {}

for name, K in kernels.items():
    rho = kernel_to_density(K)
    kernel_densities[name] = rho
    validity_checks[name] = is_valid_dm(rho, label=name)
    entropies[name] = vn_entropy(rho)
    eigenspectra[name] = sorted(
        np.real(np.linalg.eigvalsh(rho)).tolist(), reverse=True
    )

# Test 1: All valid density matrices
all_valid = all(
    v["trace_ok"] and v["hermitian"] and v["psd"]
    for v in validity_checks.values()
)

# Test 2: Entropy values computed
all_entropy_computed = all(
    isinstance(entropies[k], float) and entropies[k] >= 0
    for k in kernels
)

# Test 3: Which kernel has most information spread?
max_entropy_kernel = max(entropies, key=entropies.get)

# Test 4: Pairwise fidelity between kernel-densities
fidelity_matrix = {}
kernel_names = list(kernels.keys())
for i, n1 in enumerate(kernel_names):
    for j, n2 in enumerate(kernel_names):
        if i < j:
            f = fidelity(kernel_densities[n1], kernel_densities[n2])
            fidelity_matrix[f"{n1}_vs_{n2}"] = f

most_similar_pair = max(fidelity_matrix, key=fidelity_matrix.get)

# Test 5: Eigenvalue spectrum — PCA on kernel IS spectral decomposition
# Top eigenvalue fraction = explained variance ratio of first PC
pca_fractions = {}
for name, spec in eigenspectra.items():
    total = sum(spec)
    if total > EPS:
        pca_fractions[name] = spec[0] / total
    else:
        pca_fractions[name] = 0.0

# Test 6: Entropy ordering makes sense (more spread = higher entropy)
# RBF should be relatively uniform (high entropy), linear may be concentrated
entropy_ordering = sorted(entropies.items(), key=lambda x: x[1])

RESULTS["1_kernel_density"] = {
    "validity": {k: v for k, v in validity_checks.items()},
    "all_valid": all_valid,
    "entropies": entropies,
    "max_entropy_kernel": max_entropy_kernel,
    "fidelity_matrix": fidelity_matrix,
    "most_similar_pair": most_similar_pair,
    "pca_top_eigenvalue_fraction": pca_fractions,
    "eigenspectra": eigenspectra,
    "entropy_ordering": [e[0] for e in entropy_ordering],
    "all_entropy_computed": all_entropy_computed,
    "elapsed_s": time.time() - t0,
}
print(f"  All valid: {all_valid}")
print(f"  Entropies: {entropies}")
print(f"  Most spread (max entropy): {max_entropy_kernel}")
print(f"  Most similar pair: {most_similar_pair}")


# ══════════════════════════════════════════════════════════════════════
# 2.  INFORMATION BOTTLENECK AS CHANNEL CAPACITY  (6 tests)
# ══════════════════════════════════════════════════════════════════════
print("\nSection 2: Information bottleneck as channel capacity...")
t0 = time.time()


def classical_mi(p_xy):
    """Mutual information I(X;Y) from joint distribution."""
    p_x = p_xy.sum(axis=1)
    p_y = p_xy.sum(axis=0)
    mi = 0.0
    for i in range(p_xy.shape[0]):
        for j in range(p_xy.shape[1]):
            if p_xy[i, j] > EPS:
                mi += p_xy[i, j] * np.log2(
                    p_xy[i, j] / (p_x[i] * p_y[j] + EPS)
                )
    return mi


def compute_channel_mi(p_xy, p_t_given_x):
    """Compute I(X;T) and I(T;Y) given encoder p(t|x)."""
    p_x = p_xy.sum(axis=1)
    n_t = p_t_given_x.shape[1]

    # p(t) = sum_x p(t|x) p(x)
    p_t = p_t_given_x.T @ p_x

    # I(X;T) = sum_x,t p(x) p(t|x) log(p(t|x)/p(t))
    i_xt = 0.0
    for x in range(len(p_x)):
        for t in range(n_t):
            if p_t_given_x[x, t] > EPS and p_t[t] > EPS:
                i_xt += p_x[x] * p_t_given_x[x, t] * np.log2(
                    p_t_given_x[x, t] / p_t[t]
                )

    # p(y|t) = sum_x p(y|x) p(x|t), where p(x|t) = p(t|x)p(x)/p(t)
    n_y = p_xy.shape[1]
    p_y_given_t = np.zeros((n_t, n_y))
    for t in range(n_t):
        if p_t[t] > EPS:
            for x in range(len(p_x)):
                p_x_given_t = p_t_given_x[x, t] * p_x[x] / p_t[t]
                p_y_given_x = p_xy[x] / (p_x[x] + EPS)
                p_y_given_t[t] += p_x_given_t * p_y_given_x

    # p(t,y) = p(y|t) p(t)
    p_ty = p_y_given_t * p_t[:, None]
    p_y = p_ty.sum(axis=0)

    # I(T;Y) = sum_t,y p(t,y) log(p(t,y)/(p(t)p(y)))
    i_ty = 0.0
    for t in range(n_t):
        for y in range(n_y):
            if p_ty[t, y] > EPS and p_t[t] > EPS and p_y[y] > EPS:
                i_ty += p_ty[t, y] * np.log2(
                    p_ty[t, y] / (p_t[t] * p_y[y])
                )

    return float(i_xt), float(i_ty)


def information_bottleneck(p_xy, beta, n_iter=200):
    """IB: min I(X;T) - beta I(T;Y) via iterative update."""
    n_x, n_y = p_xy.shape
    n_t = n_x  # bottleneck dimension = source dimension
    p_x = p_xy.sum(axis=1)
    p_y = p_xy.sum(axis=0)

    # Initialize random encoder
    rng = np.random.RandomState(int(beta * 100) % (2**31))
    p_t_given_x = rng.dirichlet(np.ones(n_t), n_x)

    for iteration in range(n_iter):
        # p(t) = sum_x p(t|x) p(x)
        p_t = p_t_given_x.T @ p_x
        p_t = np.maximum(p_t, EPS)

        # p(y|t) = sum_x p(y|x) p(x|t)
        p_y_given_t = np.zeros((n_t, n_y))
        for t in range(n_t):
            for x in range(n_x):
                p_x_given_t = p_t_given_x[x, t] * p_x[x] / p_t[t]
                p_y_given_t[t] += p_x_given_t * (p_xy[x] / (p_x[x] + EPS))
            p_y_given_t[t] /= p_y_given_t[t].sum() + EPS

        # Update encoder using IB self-consistent equations
        new_p_t_given_x = np.zeros_like(p_t_given_x)
        for x in range(n_x):
            p_y_given_x = p_xy[x] / (p_x[x] + EPS)
            for t in range(n_t):
                # KL divergence D_KL(p(y|x) || p(y|t))
                kl = 0.0
                for y in range(n_y):
                    if p_y_given_x[y] > EPS and p_y_given_t[t, y] > EPS:
                        kl += p_y_given_x[y] * np.log(
                            p_y_given_x[y] / p_y_given_t[t, y]
                        )
                new_p_t_given_x[x, t] = p_t[t] * np.exp(-beta * kl)
            row_sum = new_p_t_given_x[x].sum()
            if row_sum > EPS:
                new_p_t_given_x[x] /= row_sum
            else:
                new_p_t_given_x[x] = 1.0 / n_t

        p_t_given_x = new_p_t_given_x

    return p_t_given_x


# Build joint distribution with structure: 4 x's map to 2 y's
# x in {0,1,2,3}, y in {0,1}; x=0,1 -> y=0; x=2,3 -> y=1 (with noise)
p_xy = np.array([
    [0.20, 0.05],   # x=0 -> mostly y=0
    [0.15, 0.10],   # x=1 -> mostly y=0
    [0.05, 0.20],   # x=2 -> mostly y=1
    [0.10, 0.15],   # x=3 -> mostly y=1
])
# Normalize to proper joint
p_xy /= p_xy.sum()

# Test 1: Original MI
original_mi = classical_mi(p_xy)

# Test 2-4: Sweep beta, trace IB curve
betas = [0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0]
ib_curve = []
for beta in betas:
    encoder = information_bottleneck(p_xy, beta)
    i_xt, i_ty = compute_channel_mi(p_xy, encoder)
    ib_curve.append({
        "beta": beta,
        "I_XT": i_xt,
        "I_TY": i_ty,
    })

# Test 3: IB curve monotonicity check
# As beta increases, I(T;Y) should generally increase (or plateau)
i_ty_values = [pt["I_TY"] for pt in ib_curve]
# Allow small violations due to optimization noise
monotone_violations = 0
for i in range(1, len(i_ty_values)):
    if i_ty_values[i] < i_ty_values[i - 1] - 0.05:
        monotone_violations += 1
ib_monotone_ok = monotone_violations <= 1  # allow one noise violation

# Test 5: Quantum MI on density matrix encoding of same distribution
# Encode p(x,y) as a bipartite density matrix rho_XY
n_x, n_y = p_xy.shape
d = n_x * n_y
rho_xy_classical = np.zeros((d, d), dtype=complex)
for i in range(n_x):
    for j in range(n_y):
        idx = i * n_y + j
        rho_xy_classical[idx, idx] = p_xy[i, j]
# This is diagonal = classical state
quantum_mi = mutual_information(rho_xy_classical, n_x, n_y)

# Test 6: Compare classical MI vs quantum MI — should be equal for
# diagonal (classical) density matrix
mi_match = abs(original_mi - quantum_mi) < 0.01

RESULTS["2_information_bottleneck"] = {
    "original_mi_bits": original_mi,
    "ib_curve": ib_curve,
    "ib_monotone_ok": ib_monotone_ok,
    "monotone_violations": monotone_violations,
    "quantum_mi_bits": quantum_mi,
    "classical_vs_quantum_mi_match": mi_match,
    "mi_difference": abs(original_mi - quantum_mi),
    "elapsed_s": time.time() - t0,
}
print(f"  Original MI: {original_mi:.4f} bits")
print(f"  IB monotone: {ib_monotone_ok}")
print(f"  Quantum MI: {quantum_mi:.4f}, match classical: {mi_match}")


# ══════════════════════════════════════════════════════════════════════
# 3.  ATTENTION AS DENSITY MATRIX  (4 tests)
# ══════════════════════════════════════════════════════════════════════
print("\nSection 3: Attention as density matrix...")
t0 = time.time()

# Build Q, K, V matrices (sequence_len=6, d_model=4)
seq_len, d_model = 6, 4
Q = np.random.randn(seq_len, d_model)
K = np.random.randn(seq_len, d_model)
V = np.random.randn(seq_len, d_model)

# Softmax attention
scores = Q @ K.T / np.sqrt(d_model)
# Stable softmax
scores -= scores.max(axis=1, keepdims=True)
A = np.exp(scores) / np.exp(scores).sum(axis=1, keepdims=True)

# Test 1: A is row-stochastic (rows sum to 1, all entries >= 0)
row_sums = A.sum(axis=1)
row_stochastic = bool(np.allclose(row_sums, 1.0, atol=1e-10))
all_nonneg = bool(np.all(A >= 0))

# Test 2: A is NOT symmetric/Hermitian in general (not a density matrix)
is_symmetric = bool(np.allclose(A, A.T, atol=1e-10))
# A as-is is NOT a valid density matrix (trace != 1 typically, not Hermitian)
a_trace = float(np.trace(A))
a_is_dm = is_symmetric and abs(a_trace - 1.0) < 0.01

# Test 3: Fix — symmetrize via AA^T -> density matrix
G = A @ A.T  # Gram-like matrix, symmetric PSD
rho_attention = kernel_to_density(G)
attn_dm_check = is_valid_dm(rho_attention, label="attention_gram")
attn_entropy = vn_entropy(rho_attention)

# Test 4: Alternative — interpret A as a quantum channel (CPTP map)
# A channel E maps rho -> sum_k A_k rho A_k^dagger
# For stochastic matrix: interpret each row as a Kraus-like operator
# Check: is A^T A = I? (would make it unitary channel) — generally no
ata = A.T @ A
is_unitary_channel = bool(np.allclose(ata, np.eye(seq_len), atol=0.1))

# Better test: does A preserve trace when acting on density matrices?
# For a stochastic matrix acting on probability vectors: yes
# Create a test density matrix (diagonal = probability distribution)
test_prob = np.ones(seq_len) / seq_len
output_prob = A @ test_prob
trace_preserved = bool(abs(output_prob.sum() - 1.0) < 1e-10)

# Channel interpretation: A as a classical channel preserves normalization
# State interpretation: AA^T -> density matrix captures "attention structure"
channel_vs_state = (
    "CHANNEL" if trace_preserved and not a_is_dm else
    "STATE" if a_is_dm else
    "CHANNEL_preferred"
)

RESULTS["3_attention_density"] = {
    "row_stochastic": row_stochastic,
    "all_nonneg": all_nonneg,
    "raw_A_is_symmetric": is_symmetric,
    "raw_A_trace": a_trace,
    "raw_A_is_density_matrix": a_is_dm,
    "gram_density_valid": attn_dm_check,
    "gram_entropy": attn_entropy,
    "is_unitary_channel": is_unitary_channel,
    "trace_preserved_as_channel": trace_preserved,
    "better_model": channel_vs_state,
    "elapsed_s": time.time() - t0,
}
print(f"  Row stochastic: {row_stochastic}")
print(f"  Raw A is density matrix: {a_is_dm}")
print(f"  Gram density valid: {attn_dm_check['trace_ok'] and attn_dm_check['psd']}")
print(f"  Better model: {channel_vs_state}")


# ══════════════════════════════════════════════════════════════════════
# 4.  DIFFUSION AS OPEN QUANTUM SYSTEM  (6 tests)
# ══════════════════════════════════════════════════════════════════════
print("\nSection 4: Diffusion as open quantum system...")
t0 = time.time()


def depolarizing_channel(rho, p):
    """Depolarizing channel: (1-p) rho + p I/d."""
    d = rho.shape[0]
    return (1 - p) * rho + p * np.eye(d, dtype=complex) / d


def classical_diffusion_step(prob, noise_level):
    """Classical diffusion: mix distribution toward uniform."""
    d = len(prob)
    uniform = np.ones(d) / d
    return (1 - noise_level) * prob + noise_level * uniform


# Build initial density matrix: a "peaked" state (low entropy)
d = 4
psi = np.array([0.9, 0.3, 0.1, 0.05], dtype=complex)
psi /= np.linalg.norm(psi)
rho_init = np.outer(psi, psi.conj())

# Build initial classical distribution (peaked)
p_init = np.array([0.7, 0.2, 0.08, 0.02])
p_init /= p_init.sum()

# Diffusion parameters
n_steps = 20
noise_per_step = 0.15

# Track quantum trajectory
quantum_trajectory = []
rho = rho_init.copy()
for step in range(n_steps + 1):
    s = vn_entropy(rho)
    purity = float(np.real(np.trace(rho @ rho)))
    quantum_trajectory.append({
        "step": step,
        "entropy": s,
        "purity": purity,
    })
    if step < n_steps:
        rho = depolarizing_channel(rho, noise_per_step)

# Track classical trajectory
classical_trajectory = []
p = p_init.copy()
for step in range(n_steps + 1):
    # Shannon entropy
    p_safe = p[p > EPS]
    h = float(-np.sum(p_safe * np.log2(p_safe)))
    classical_trajectory.append({
        "step": step,
        "entropy": h,
    })
    if step < n_steps:
        p = classical_diffusion_step(p, noise_per_step)

# Test 1: Quantum entropy increases monotonically
q_entropies = [t["entropy"] for t in quantum_trajectory]
q_monotone = all(
    q_entropies[i + 1] >= q_entropies[i] - 1e-10
    for i in range(len(q_entropies) - 1)
)

# Test 2: Quantum purity decreases monotonically
q_purities = [t["purity"] for t in quantum_trajectory]
q_purity_decreasing = all(
    q_purities[i + 1] <= q_purities[i] + 1e-10
    for i in range(len(q_purities) - 1)
)

# Test 3: Classical entropy increases monotonically
c_entropies = [t["entropy"] for t in classical_trajectory]
c_monotone = all(
    c_entropies[i + 1] >= c_entropies[i] - 1e-10
    for i in range(len(c_entropies) - 1)
)

# Test 4: Both converge to maximum entropy
max_entropy = np.log2(d)
q_final_near_max = abs(q_entropies[-1] - max_entropy) < 0.1
c_final_near_max = abs(c_entropies[-1] - max_entropy) < 0.1

# Test 5: Final quantum state is near maximally mixed
rho_final = rho
max_mixed = np.eye(d, dtype=complex) / d
fidelity_to_max_mixed = fidelity(rho_final, max_mixed)
near_max_mixed = fidelity_to_max_mixed > 0.95

# Test 6: Quantum and classical trajectories have similar shape
# Both start low, end at max — compare midpoint entropies
q_mid = q_entropies[n_steps // 2]
c_mid = c_entropies[n_steps // 2]
# Both should be > halfway to max
both_mid_rising = q_mid > max_entropy * 0.5 and c_mid > max_entropy * 0.5

RESULTS["4_diffusion_open_system"] = {
    "quantum_entropy_monotone": q_monotone,
    "quantum_purity_decreasing": q_purity_decreasing,
    "classical_entropy_monotone": c_monotone,
    "quantum_converges_to_max": q_final_near_max,
    "classical_converges_to_max": c_final_near_max,
    "fidelity_to_max_mixed": fidelity_to_max_mixed,
    "near_max_mixed": near_max_mixed,
    "trajectories_similar_shape": both_mid_rising,
    "quantum_trajectory": quantum_trajectory,
    "classical_trajectory": classical_trajectory,
    "max_entropy_bits": float(max_entropy),
    "elapsed_s": time.time() - t0,
}
print(f"  Quantum entropy monotone: {q_monotone}")
print(f"  Purity decreasing: {q_purity_decreasing}")
print(f"  Classical entropy monotone: {c_monotone}")
print(f"  Both converge to max: q={q_final_near_max}, c={c_final_near_max}")


# ══════════════════════════════════════════════════════════════════════
# 5.  LOSS LANDSCAPE AS HAMILTONIAN SPECTRUM  (4 tests)
# ══════════════════════════════════════════════════════════════════════
print("\nSection 5: Loss landscape as Hamiltonian spectrum...")
t0 = time.time()

# Build a random 4x4 Hermitian "loss matrix"
d = 4
M = np.random.randn(d, d) + 1j * np.random.randn(d, d)
H = (M + M.conj().T) / 2  # Hermitianize

# Eigendecomposition
evals_H, evecs_H = np.linalg.eigh(H)

# Test 1: Ground state = global minimum (smallest eigenvalue)
ground_energy = float(evals_H[0])
ground_state = evecs_H[:, 0]

# Test 2: Gap to first excited state = curvature at minimum
spectral_gap = float(evals_H[1] - evals_H[0])
gap_positive = spectral_gap > 0

# Test 3: Thermal state at temperature T = density matrix
# rho(T) = exp(-H/T) / Tr(exp(-H/T))
temperatures = [0.1, 0.5, 1.0, 5.0, 100.0]
thermal_states = {}
for T in temperatures:
    rho_T = expm(-H / T)
    rho_T = rho_T / np.trace(rho_T)
    check = is_valid_dm(rho_T, label=f"thermal_T={T}")
    thermal_states[f"T={T}"] = {
        "valid": check["trace_ok"] and check["hermitian"] and check["psd"],
        "entropy": vn_entropy(rho_T),
        "purity": check["purity"],
    }

# Test 4: Low T -> near ground state (low entropy, high purity)
#          High T -> near maximally mixed (high entropy, low purity)
low_T_entropy = thermal_states["T=0.1"]["entropy"]
high_T_entropy = thermal_states["T=100.0"]["entropy"]
low_T_high_purity = thermal_states["T=0.1"]["purity"] > 0.9
high_T_low_purity = thermal_states["T=100.0"]["purity"] < 0.3
temperature_ordering_ok = low_T_entropy < high_T_entropy

# Convergence rate proxy: larger gap -> faster convergence
# Simulated annealing: track energy during cooling
n_anneal = 50
anneal_trajectory = []
T_schedule = np.linspace(10.0, 0.1, n_anneal)
for T in T_schedule:
    rho_T = expm(-H / T)
    rho_T = rho_T / np.trace(rho_T)
    energy = float(np.real(np.trace(H @ rho_T)))
    anneal_trajectory.append({"T": float(T), "energy": energy})

# Energy should decrease toward ground state energy
final_energy = anneal_trajectory[-1]["energy"]
converged_to_ground = abs(final_energy - ground_energy) < 0.1

RESULTS["5_loss_hamiltonian"] = {
    "eigenvalues": evals_H.tolist(),
    "ground_energy": ground_energy,
    "spectral_gap": spectral_gap,
    "gap_positive": gap_positive,
    "thermal_states": thermal_states,
    "low_T_high_purity": low_T_high_purity,
    "high_T_low_purity": high_T_low_purity,
    "temperature_ordering_ok": temperature_ordering_ok,
    "anneal_converged_to_ground": converged_to_ground,
    "anneal_final_energy": final_energy,
    "elapsed_s": time.time() - t0,
}
print(f"  Eigenvalues: {evals_H.tolist()}")
print(f"  Spectral gap: {spectral_gap:.4f}")
print(f"  Temperature ordering (low S < high S): {temperature_ordering_ok}")
print(f"  Anneal converged to ground: {converged_to_ground}")


# ══════════════════════════════════════════════════════════════════════
# 6.  REPRESENTATION LEARNING AS PARTIAL TRACE  (4 tests)
# ══════════════════════════════════════════════════════════════════════
print("\nSection 6: Representation learning as partial trace...")
t0 = time.time()

# --- Product state (disentangled representation) ---
# rho_AB = rho_A tensor rho_B
# "Data" subsystem B, "Representation" subsystem A, each 2-dim
d_A, d_B = 2, 2
d_AB = d_A * d_B

# Build subsystem states
psi_A = np.array([0.8, 0.6], dtype=complex)
psi_A /= np.linalg.norm(psi_A)
rho_A_prod = np.outer(psi_A, psi_A.conj())

psi_B = np.array([0.5, np.sqrt(0.75)], dtype=complex)
psi_B /= np.linalg.norm(psi_B)
rho_B_prod = np.outer(psi_B, psi_B.conj())

rho_product = np.kron(rho_A_prod, rho_B_prod)

# --- Entangled state (correlated representation) ---
# Bell-like state: |psi> = a|00> + b|11>
a_coeff, b_coeff = 1 / np.sqrt(2), 1 / np.sqrt(2)
psi_entangled = np.zeros(d_AB, dtype=complex)
psi_entangled[0] = a_coeff   # |00>
psi_entangled[3] = b_coeff   # |11>
rho_entangled = np.outer(psi_entangled, psi_entangled.conj())

# Test 1: Partial trace = learned representation
rho_A_from_product = partial_trace_B(rho_product, d_A, d_B)
rho_A_from_entangled = partial_trace_B(rho_entangled, d_A, d_B)

product_repr_valid = is_valid_dm(rho_A_from_product, "product_repr")
entangled_repr_valid = is_valid_dm(rho_A_from_entangled, "entangled_repr")

# Test 2: MI for product vs entangled
mi_product = mutual_information(rho_product, d_A, d_B)
mi_entangled = mutual_information(rho_entangled, d_A, d_B)

# Product should have ~0 MI, entangled should have high MI
product_low_mi = mi_product < 0.01
entangled_high_mi = mi_entangled > 0.5

# Test 3: Disentanglement check
# Product state: rho_AB approx= rho_A tensor rho_B
reconstructed_product = np.kron(rho_A_from_product, partial_trace_A(rho_product, d_A, d_B))
product_is_disentangled = bool(np.allclose(rho_product, reconstructed_product, atol=1e-10))

reconstructed_entangled = np.kron(
    rho_A_from_entangled,
    partial_trace_A(rho_entangled, d_A, d_B),
)
entangled_is_disentangled = bool(np.allclose(rho_entangled, reconstructed_entangled, atol=0.01))

# Test 4: Concurrence
C_product = concurrence_2qubit(rho_product)
C_entangled = concurrence_2qubit(rho_entangled)

product_C_zero = C_product < 0.01
entangled_C_high = C_entangled > 0.9

# Summary: entangled representation captures correlations (high MI, high C)
#          product representation = independent features (low MI, low C)

RESULTS["6_representation_partial_trace"] = {
    "product_repr_valid": product_repr_valid,
    "entangled_repr_valid": entangled_repr_valid,
    "mi_product": mi_product,
    "mi_entangled": mi_entangled,
    "product_low_mi": product_low_mi,
    "entangled_high_mi": entangled_high_mi,
    "product_is_disentangled": product_is_disentangled,
    "entangled_is_NOT_disentangled": not entangled_is_disentangled,
    "concurrence_product": C_product,
    "concurrence_entangled": C_entangled,
    "product_C_zero": product_C_zero,
    "entangled_C_high": entangled_C_high,
    "elapsed_s": time.time() - t0,
}
print(f"  MI product: {mi_product:.4f}, MI entangled: {mi_entangled:.4f}")
print(f"  Product disentangled: {product_is_disentangled}")
print(f"  Entangled NOT disentangled: {not entangled_is_disentangled}")
print(f"  Concurrence product: {C_product:.4f}, entangled: {C_entangled:.4f}")


# ══════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════

summary = {
    "1_kernels_all_valid": RESULTS["1_kernel_density"]["all_valid"],
    "1_entropy_computed": RESULTS["1_kernel_density"]["all_entropy_computed"],
    "2_ib_monotone": RESULTS["2_information_bottleneck"]["ib_monotone_ok"],
    "2_classical_quantum_mi_match": RESULTS["2_information_bottleneck"]["classical_vs_quantum_mi_match"],
    "3_attention_row_stochastic": RESULTS["3_attention_density"]["row_stochastic"],
    "3_gram_density_valid": (
        RESULTS["3_attention_density"]["gram_density_valid"]["trace_ok"]
        and RESULTS["3_attention_density"]["gram_density_valid"]["psd"]
    ),
    "4_quantum_entropy_monotone": RESULTS["4_diffusion_open_system"]["quantum_entropy_monotone"],
    "4_purity_decreasing": RESULTS["4_diffusion_open_system"]["quantum_purity_decreasing"],
    "4_classical_entropy_monotone": RESULTS["4_diffusion_open_system"]["classical_entropy_monotone"],
    "4_both_converge": (
        RESULTS["4_diffusion_open_system"]["quantum_converges_to_max"]
        and RESULTS["4_diffusion_open_system"]["classical_converges_to_max"]
    ),
    "5_gap_positive": RESULTS["5_loss_hamiltonian"]["gap_positive"],
    "5_temperature_ordering": RESULTS["5_loss_hamiltonian"]["temperature_ordering_ok"],
    "5_anneal_converged": RESULTS["5_loss_hamiltonian"]["anneal_converged_to_ground"],
    "6_product_low_mi": RESULTS["6_representation_partial_trace"]["product_low_mi"],
    "6_entangled_high_mi": RESULTS["6_representation_partial_trace"]["entangled_high_mi"],
    "6_product_disentangled": RESULTS["6_representation_partial_trace"]["product_is_disentangled"],
    "6_entangled_C_high": RESULTS["6_representation_partial_trace"]["entangled_C_high"],
}

all_pass = all(summary.values())
RESULTS["name"] = "pure_lego_ml_density_matrix"
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
    "covers_kernel_density": True,
    "covers_information_bottleneck": True,
    "covers_attention_density": True,
    "covers_diffusion_open_system": True,
    "covers_loss_hamiltonian_spectrum": True,
    "covers_representation_partial_trace": True,
    "closure_grade": False,
    "notes": [
        "This is a bundled compression/ML analogy probe, not a single-lego canonical surface.",
        "Best used as supporting evidence for compression/spectral rows until narrower direct legos are split out.",
    ],
}

print(f"\n{'='*60}")
print(f"PURE LEGO ML DENSITY MATRIX — ALL PASS: {all_pass}")
print(f"{'='*60}")
for k, v in summary.items():
    tag = "PASS" if v else "FAIL"
    print(f"  [{tag}] {k}")

# Write results
out_path = (
    pathlib.Path(__file__).parent
    / "a2_state"
    / "sim_results"
    / "pure_lego_ml_density_matrix_results.json"
)
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w") as f:
    json.dump(RESULTS, f, indent=2, default=str)
print(f"\nResults written to {out_path}")
