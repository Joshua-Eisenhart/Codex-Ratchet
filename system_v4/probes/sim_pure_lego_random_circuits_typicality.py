#!/usr/bin/env python3
"""
PURE LEGO: Random Quantum Circuits, Haar Typicality & Measure Concentration
============================================================================
Foundational building block.  Pure math only -- numpy.
No engine imports.  Every result verified against known analytic bounds.

Sections
--------
1. Haar-random unitary generation via GUE  (d=2, d=4)
2. Unitarity validation
3. Haar-random 2-qubit state ensemble (1000 samples)
4. Entanglement entropy distribution & Page's result
5. Concurrence distribution
6. Purity of marginals distribution
7. Mutual information distribution
8. Concentration of measure verification
9. Random circuit convergence to Haar (frame potential / t-design)
10. Clifford group as a 3-design for d=2
11. Porter-Thomas anti-concentration
"""

import json, pathlib, time
import numpy as np
from collections import OrderedDict
classification = "classical_baseline"  # auto-backfill

np.random.seed(42)
EPS = 1e-12
RESULTS = OrderedDict()
N_SAMPLES = 1000

# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def ket(v):
    """Column vector from list."""
    return np.array(v, dtype=complex).reshape(-1, 1)

def partial_trace_B(rho_AB, dA, dB):
    """Trace out subsystem B from rho_AB of dimension dA*dB."""
    rho = rho_AB.reshape(dA, dB, dA, dB)
    return np.trace(rho, axis1=1, axis2=3)

def partial_trace_A(rho_AB, dA, dB):
    """Trace out subsystem A from rho_AB of dimension dA*dB."""
    rho = rho_AB.reshape(dA, dB, dA, dB)
    return np.trace(rho, axis1=0, axis2=2)

def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho log2 rho), eigenvalue-based."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > EPS]
    return float(-np.sum(evals * np.log2(evals)))

def concurrence_2qubit(rho):
    """Concurrence for a 2-qubit density matrix."""
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sy_sy = np.kron(sy, sy)
    rho_tilde = sy_sy @ rho.conj() @ sy_sy
    # sqrt(rho) via eigendecomposition for numerical stability
    evals, evecs = np.linalg.eigh(rho)
    evals = np.maximum(evals, 0.0)
    sqrt_rho = evecs @ np.diag(np.sqrt(evals)) @ evecs.conj().T
    R = sqrt_rho @ rho_tilde @ sqrt_rho
    eigR = np.sort(np.real(np.sqrt(np.maximum(np.linalg.eigvalsh(R), 0.0))))[::-1]
    return float(max(0.0, eigR[0] - eigR[1] - eigR[2] - eigR[3]))

def purity(rho):
    return float(np.real(np.trace(rho @ rho)))

def mutual_information(rho_AB, dA, dB):
    """I(A:B) = S(A) + S(B) - S(AB)"""
    rho_A = partial_trace_B(rho_AB, dA, dB)
    rho_B = partial_trace_A(rho_AB, dA, dB)
    return von_neumann_entropy(rho_A) + von_neumann_entropy(rho_B) - von_neumann_entropy(rho_AB)


# ══════════════════════════════════════════════════════════════════════
# 1. HAAR-RANDOM UNITARY GENERATION via GUE
# ══════════════════════════════════════════════════════════════════════
print("=" * 60)
print("Section 1: Haar-random unitary generation (GUE method)")
print("=" * 60)

def haar_random_unitary_gue(d):
    """
    Generate a Haar-random unitary of dimension d.
    Method: draw H from GUE, compute U = exp(iH).
    Equivalent to QR decomposition of complex Gaussian matrix.
    """
    # GUE: H = (A + A^dag) / 2 where A is complex Gaussian
    A = (np.random.randn(d, d) + 1j * np.random.randn(d, d)) / np.sqrt(2)
    H = (A + A.conj().T) / 2.0
    evals, evecs = np.linalg.eigh(H)
    U = evecs @ np.diag(np.exp(1j * evals)) @ evecs.conj().T
    return U

def haar_random_unitary_qr(d):
    """
    Haar-random unitary via QR decomposition of complex Gaussian.
    This is the standard Mezzadri/Stewart method.
    """
    Z = (np.random.randn(d, d) + 1j * np.random.randn(d, d)) / np.sqrt(2)
    Q, R = np.linalg.qr(Z)
    # Fix phase to ensure Haar measure
    diag_R = np.diag(R)
    Lambda = np.diag(diag_R / np.abs(diag_R))
    return Q @ Lambda

t0 = time.time()

# Generate test unitaries
unitaries_d2 = [haar_random_unitary_qr(2) for _ in range(100)]
unitaries_d4 = [haar_random_unitary_qr(4) for _ in range(100)]

# Also generate via GUE for comparison
unitaries_gue_d2 = [haar_random_unitary_gue(2) for _ in range(50)]
unitaries_gue_d4 = [haar_random_unitary_gue(4) for _ in range(50)]

gen_time = time.time() - t0
print(f"  Generated 100 QR + 50 GUE unitaries for d=2,4 in {gen_time:.3f}s")


# ══════════════════════════════════════════════════════════════════════
# 2. UNITARITY VALIDATION
# ══════════════════════════════════════════════════════════════════════
print("\nSection 2: Unitarity validation")

def check_unitarity(U, tol=1e-10):
    d = U.shape[0]
    err_UdU = np.max(np.abs(U.conj().T @ U - np.eye(d)))
    err_UUd = np.max(np.abs(U @ U.conj().T - np.eye(d)))
    det_mag = abs(abs(np.linalg.det(U)) - 1.0)
    return {
        "UdagU_max_err": float(err_UdU),
        "UUdag_max_err": float(err_UUd),
        "det_err": float(det_mag),
        "pass": bool(err_UdU < tol and err_UUd < tol and det_mag < tol),
    }

qr_checks_d2 = [check_unitarity(U) for U in unitaries_d2]
qr_checks_d4 = [check_unitarity(U) for U in unitaries_d4]
gue_checks_d2 = [check_unitarity(U) for U in unitaries_gue_d2]
gue_checks_d4 = [check_unitarity(U) for U in unitaries_gue_d4]

all_unitary_pass = (
    all(c["pass"] for c in qr_checks_d2) and
    all(c["pass"] for c in qr_checks_d4) and
    all(c["pass"] for c in gue_checks_d2) and
    all(c["pass"] for c in gue_checks_d4)
)

RESULTS["2_unitarity"] = {
    "qr_d2_all_pass": all(c["pass"] for c in qr_checks_d2),
    "qr_d4_all_pass": all(c["pass"] for c in qr_checks_d4),
    "gue_d2_all_pass": all(c["pass"] for c in gue_checks_d2),
    "gue_d4_all_pass": all(c["pass"] for c in gue_checks_d4),
    "qr_d2_max_err": max(c["UdagU_max_err"] for c in qr_checks_d2),
    "qr_d4_max_err": max(c["UdagU_max_err"] for c in qr_checks_d4),
    "all_pass": all_unitary_pass,
}
print(f"  QR d=2 all unitary: {all(c['pass'] for c in qr_checks_d2)}")
print(f"  QR d=4 all unitary: {all(c['pass'] for c in qr_checks_d4)}")
print(f"  GUE d=2 all unitary: {all(c['pass'] for c in gue_checks_d2)}")
print(f"  GUE d=4 all unitary: {all(c['pass'] for c in gue_checks_d4)}")


# ══════════════════════════════════════════════════════════════════════
# 3. HAAR-RANDOM 2-QUBIT STATE ENSEMBLE
# ══════════════════════════════════════════════════════════════════════
print(f"\nSection 3: Generate {N_SAMPLES} Haar-random 2-qubit states")

def haar_random_state(d):
    """Haar-random pure state in C^d via column of Haar unitary."""
    U = haar_random_unitary_qr(d)
    return U[:, 0].reshape(-1, 1)

t0 = time.time()
states_4d = [haar_random_state(4) for _ in range(N_SAMPLES)]
rhos_4d = [psi @ psi.conj().T for psi in states_4d]
gen_state_time = time.time() - t0

# Validate: all pure states
purities_full = [purity(rho) for rho in rhos_4d]
all_pure = all(abs(p - 1.0) < 1e-10 for p in purities_full)

RESULTS["3_state_ensemble"] = {
    "n_samples": N_SAMPLES,
    "generation_time_s": round(gen_state_time, 4),
    "all_pure": all_pure,
    "mean_purity": float(np.mean(purities_full)),
}
print(f"  Generated {N_SAMPLES} states in {gen_state_time:.3f}s")
print(f"  All pure (Tr(rho^2)=1): {all_pure}")


# ══════════════════════════════════════════════════════════════════════
# 4. ENTANGLEMENT ENTROPY & PAGE'S RESULT
# ══════════════════════════════════════════════════════════════════════
print("\nSection 4: Entanglement entropy -- Page's result")

# For a random pure state in C^dA x C^dB with dA <= dB,
# Page's formula: <S> = sum_{k=dB+1}^{dA*dB} 1/k - (dA-1)/(2*dB)
# For dA=dB=2: <S> = 1/3 + 1/4 - 1/4 = 1/3 (in nats-base)
# In bits: <S>_bits = (H_4 - H_2) / ln(2) - (dA-1)/(2*dB*ln(2))
# Exact: <S> = (1/3 + 1/4) - 1/4 = 1/3 in nats => 1/(3*ln2) bits
# Actually, Page's formula for dA=dB=d=2, D=dA*dB=4:
# <S> = sum_{k=d+1}^{D} 1/k  -  (d-1)/(2D)
#      = (1/3 + 1/4)  -  1/8  = 7/24 - 1/8 = ... let me compute carefully
# = sum_{k=3}^{4} 1/k  - 1/8  = (1/3 + 1/4) - 1/8 = 7/12 - 1/8 = 11/24
# That's in natural log. Convert to log2: 11/(24*ln2) = 0.6632...

dA, dB = 2, 2
D = dA * dB

# Page's exact mean entanglement entropy (natural log)
# S_Page = sum_{k=n+1}^{mn} 1/k  -  (m-1)/(2n)
# where m = min(dA,dB), n = max(dA,dB)
m_page, n_page = min(dA, dB), max(dA, dB)
page_mean_nats = sum(1.0 / k for k in range(n_page + 1, m_page * n_page + 1)) - (m_page - 1) / (2.0 * n_page)
page_mean_bits = page_mean_nats / np.log(2)

# Also the simpler approximate: S ~ log(dA) - dA/(2*dB) for large D
# For dA=dB=2: log2(2) - 2/4 = 1 - 0.5 = 0.5 (rough approx for small d)

ent_entropies = []
for rho in rhos_4d:
    rho_A = partial_trace_B(rho, dA, dB)
    ent_entropies.append(von_neumann_entropy(rho_A))

ent_entropies = np.array(ent_entropies)
mean_ee = float(np.mean(ent_entropies))
std_ee = float(np.std(ent_entropies))

# Page's result check: mean should be close to page_mean_bits
page_err = abs(mean_ee - page_mean_bits)
page_pass = page_err < 0.05  # generous tolerance for 1000 samples

RESULTS["4_page_entanglement"] = {
    "page_mean_bits_exact": float(page_mean_bits),
    "page_mean_nats_exact": float(page_mean_nats),
    "measured_mean_bits": mean_ee,
    "measured_std_bits": std_ee,
    "absolute_error": float(page_err),
    "page_pass": page_pass,
    "max_possible_entropy_bits": float(np.log2(dA)),  # = 1.0
    "fraction_above_0p9_max": float(np.mean(ent_entropies > 0.9)),
}

print(f"  Page's exact mean (bits):  {page_mean_bits:.6f}")
print(f"  Measured mean (bits):      {mean_ee:.6f}")
print(f"  Absolute error:            {page_err:.6f}")
print(f"  Page's result verified:    {page_pass}")


# ══════════════════════════════════════════════════════════════════════
# 5. CONCURRENCE DISTRIBUTION
# ══════════════════════════════════════════════════════════════════════
print("\nSection 5: Concurrence distribution")

concurrences = np.array([concurrence_2qubit(rho) for rho in rhos_4d])
mean_C = float(np.mean(concurrences))
std_C = float(np.std(concurrences))

# For Haar-random 2-qubit pure states, mean concurrence = 3*pi/16 ~ 0.589
# (exact result from integration over Haar measure)
exact_mean_C = 3 * np.pi / 16
C_err = abs(mean_C - exact_mean_C)
C_pass = C_err < 0.05

RESULTS["5_concurrence"] = {
    "exact_mean": float(exact_mean_C),
    "measured_mean": mean_C,
    "measured_std": std_C,
    "absolute_error": float(C_err),
    "pass": C_pass,
    "fraction_above_0p5": float(np.mean(concurrences > 0.5)),
    "fraction_above_0p9": float(np.mean(concurrences > 0.9)),
    "min": float(np.min(concurrences)),
    "max": float(np.max(concurrences)),
}

print(f"  Exact mean concurrence:    {exact_mean_C:.6f}")
print(f"  Measured mean concurrence: {mean_C:.6f}")
print(f"  Error: {C_err:.6f}, Pass: {C_pass}")


# ══════════════════════════════════════════════════════════════════════
# 6. PURITY OF MARGINALS
# ══════════════════════════════════════════════════════════════════════
print("\nSection 6: Purity of marginals distribution")

purities_A = []
purities_B = []
for rho in rhos_4d:
    rho_A = partial_trace_B(rho, 2, 2)
    rho_B = partial_trace_A(rho, 2, 2)
    purities_A.append(purity(rho_A))
    purities_B.append(purity(rho_B))

purities_A = np.array(purities_A)
purities_B = np.array(purities_B)

# For Haar-random pure bipartite states |psi> in C^d x C^d,
# E[Tr(rho_A^2)] = (d+1)/(d^2+d) = (d+1)/(d(d+1)) = 1/d ... wait
# Actually: E[Tr(rho_A^2)] = (dA + dB) / (dA * dB + 1)
# For dA=dB=2: (2+2)/(4+1) = 4/5 = 0.8  ... no that's wrong too.
# Correct formula: E[Tr(rho_A^2)] = (dA + dB) / (dA*dB + 1)
# For dA=dB=2: (2+2)/(4+1) = 4/5 = 0.8... hmm.
# Actually the known result is: for |psi> uniform on S(C^{dA} x C^{dB}),
# E[Tr(rho_A^2)] = (dA + dB) / (dA * dB + 1)
# dA=dB=2 => (4)/(5) = 0.8?  That seems high.
# Let me verify: for a Bell state, Tr(rho_A^2) = 0.5. For product, = 1.
# Average should be between these. The actual analytical result is:
# E[Tr(rho_A^2)] = (dA + dB) / (dA*dB + 1) = 4/5 = 0.8? Seems plausible
# since most states are "somewhat" entangled but not maximally.
# Wait -- this contradicts Page's result saying most states are NEARLY max entangled.
# Actually for d=2 the space is small, concentration is weak.
# Let me just trust the formula and verify numerically.

exact_purity_marginal = (dA + dB) / (dA * dB + 1)
mean_pur_A = float(np.mean(purities_A))
mean_pur_B = float(np.mean(purities_B))
pur_err_A = abs(mean_pur_A - exact_purity_marginal)

# Purity of A and B should be identically distributed (symmetry)
symmetry_check = abs(mean_pur_A - mean_pur_B)

RESULTS["6_marginal_purity"] = {
    "exact_mean_purity": float(exact_purity_marginal),
    "measured_mean_purity_A": mean_pur_A,
    "measured_mean_purity_B": mean_pur_B,
    "error_A": float(pur_err_A),
    "symmetry_AB_diff": float(symmetry_check),
    "pass_mean": bool(pur_err_A < 0.05),
    "pass_symmetry": bool(symmetry_check < 0.05),
    "min_purity_A": float(np.min(purities_A)),
    "max_purity_A": float(np.max(purities_A)),
}

print(f"  Exact mean marginal purity: {exact_purity_marginal:.6f}")
print(f"  Measured mean purity A:     {mean_pur_A:.6f}")
print(f"  Measured mean purity B:     {mean_pur_B:.6f}")
print(f"  A-B symmetry diff:          {symmetry_check:.6f}")


# ══════════════════════════════════════════════════════════════════════
# 7. MUTUAL INFORMATION DISTRIBUTION
# ══════════════════════════════════════════════════════════════════════
print("\nSection 7: Mutual information distribution")

mi_values = []
for rho in rhos_4d:
    mi_values.append(mutual_information(rho, 2, 2))
mi_values = np.array(mi_values)
mean_mi = float(np.mean(mi_values))
std_mi = float(np.std(mi_values))

# For pure bipartite states, I(A:B) = 2*S(A) since S(AB)=0
# So mean MI = 2 * Page's mean
expected_mi = 2 * page_mean_bits
mi_err = abs(mean_mi - expected_mi)

# All MI should be non-negative
mi_nonneg = bool(np.all(mi_values >= -EPS))

# For pure states, MI = 2*S(A), verify this identity
mi_vs_2S = np.array([
    abs(mi_values[i] - 2 * ent_entropies[i]) for i in range(N_SAMPLES)
])
mi_identity_pass = bool(np.max(mi_vs_2S) < 1e-10)

RESULTS["7_mutual_information"] = {
    "expected_mean_bits": float(expected_mi),
    "measured_mean_bits": mean_mi,
    "measured_std_bits": std_mi,
    "error": float(mi_err),
    "pass_mean": bool(mi_err < 0.1),
    "all_nonneg": mi_nonneg,
    "mi_equals_2S_identity": mi_identity_pass,
    "max_identity_deviation": float(np.max(mi_vs_2S)),
}

print(f"  Expected mean MI:  {expected_mi:.6f}")
print(f"  Measured mean MI:  {mean_mi:.6f}")
print(f"  MI = 2*S(A) identity holds: {mi_identity_pass}")


# ══════════════════════════════════════════════════════════════════════
# 8. CONCENTRATION OF MEASURE
# ══════════════════════════════════════════════════════════════════════
print("\nSection 8: Concentration of measure")

# Levy's lemma: For Haar-random states on C^D, any 1-Lipschitz function f,
# Pr[|f - E[f]| > epsilon] <= 2*exp(-C*D*epsilon^2)
# For D=4 (2 qubits), concentration is WEAK (small D).
# For D=16 (4 qubits), concentration is much stronger.

# Demonstrate by generating Haar-random states in larger D and showing
# the entropy distribution narrows.
dims_to_test = [(2, 2), (2, 4), (4, 4), (4, 8)]
concentration_data = {}

for dA_loc, dB_loc in dims_to_test:
    D = dA_loc * dB_loc
    n_samp = 500
    entropies_loc = []
    for _ in range(n_samp):
        psi = haar_random_state(D)
        rho_full = psi @ psi.conj().T
        rho_A_loc = partial_trace_B(rho_full, dA_loc, dB_loc)
        entropies_loc.append(von_neumann_entropy(rho_A_loc))
    entropies_loc = np.array(entropies_loc)
    max_ent = np.log2(dA_loc)
    m_loc, n_loc = min(dA_loc, dB_loc), max(dA_loc, dB_loc)
    page_nats_loc = sum(1.0 / k for k in range(n_loc + 1, m_loc * n_loc + 1)) - (m_loc - 1) / (2.0 * n_loc)
    page_bits_loc = page_nats_loc / np.log(2)

    # Coefficient of variation (std/mean) should decrease with D
    cv = float(np.std(entropies_loc) / np.mean(entropies_loc)) if np.mean(entropies_loc) > 0 else 0.0

    concentration_data[f"D={D}"] = {
        "dA": dA_loc,
        "dB": dB_loc,
        "max_entropy_bits": float(max_ent),
        "page_mean_bits": float(page_bits_loc),
        "measured_mean": float(np.mean(entropies_loc)),
        "measured_std": float(np.std(entropies_loc)),
        "coeff_variation": cv,
        "fraction_within_10pct_of_max": float(np.mean(entropies_loc > 0.9 * max_ent)),
    }
    print(f"  D={D:3d} (dA={dA_loc},dB={dB_loc}): "
          f"mean={np.mean(entropies_loc):.4f}, std={np.std(entropies_loc):.4f}, CV={cv:.4f}")

# Verify concentration: CV should decrease with D
cvs = [concentration_data[k]["coeff_variation"] for k in concentration_data]
concentration_monotone = all(cvs[i] >= cvs[i + 1] for i in range(len(cvs) - 1))

RESULTS["8_concentration"] = {
    "data": concentration_data,
    "cv_decreasing_with_D": concentration_monotone,
    "pass": concentration_monotone,
}
print(f"  CV monotonically decreasing with D: {concentration_monotone}")


# ══════════════════════════════════════════════════════════════════════
# 9. RANDOM CIRCUIT CONVERGENCE TO HAAR (FRAME POTENTIAL)
# ══════════════════════════════════════════════════════════════════════
print("\nSection 9: Random circuit convergence -- frame potential")

# Frame potential for an ensemble E of unitaries:
# F_t(E) = (1/|E|^2) sum_{U,V in E} |Tr(U^dag V)|^{2t}
# Haar value: F_t(Haar) = t!  for d >= t
# For d=2, t=1: F_1(Haar) = 1
# For d=2, t=2: F_2(Haar) = 2

def frame_potential(unitaries, t):
    """Compute t-th frame potential of a finite ensemble."""
    n = len(unitaries)
    total = 0.0
    for i in range(n):
        for j in range(n):
            overlap = np.trace(unitaries[i].conj().T @ unitaries[j])
            total += abs(overlap) ** (2 * t)
    return total / (n * n)

# Build random circuits of increasing depth
# Single-qubit gates: random from Haar
# Two-qubit layer: alternating CNOTs + single-qubit randoms
# For simplicity, a "depth-L" random circuit on 2 qubits =
# product of L independent Haar-random 4x4 unitaries (generous).
# But to show convergence, use product of random 2-local gates.

def random_2local_gate():
    """Random 2-qubit gate: (U1 x U2) . CNOT . (V1 x V2)"""
    u1 = haar_random_unitary_qr(2)
    u2 = haar_random_unitary_qr(2)
    v1 = haar_random_unitary_qr(2)
    v2 = haar_random_unitary_qr(2)
    CNOT = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ], dtype=complex)
    pre = np.kron(u1, u2)
    post = np.kron(v1, v2)
    return post @ CNOT @ pre

def random_circuit_unitary(depth):
    """Compose `depth` random 2-local gates."""
    U = np.eye(4, dtype=complex)
    for _ in range(depth):
        U = random_2local_gate() @ U
    return U

depths = [1, 2, 3, 5, 10]
n_circuit_samples = 200
frame_results = {}

for depth in depths:
    circuits = [random_circuit_unitary(depth) for _ in range(n_circuit_samples)]
    fp1 = frame_potential(circuits, t=1)
    fp2 = frame_potential(circuits, t=2)
    frame_results[f"depth_{depth}"] = {
        "frame_potential_t1": float(fp1),
        "frame_potential_t2": float(fp2),
        "haar_t1": 1.0,
        "haar_t2": 2.0,
        "ratio_t1": float(fp1 / 1.0),
        "ratio_t2": float(fp2 / 2.0),
    }
    print(f"  depth={depth:2d}: F_1={fp1:.4f} (Haar=1), F_2={fp2:.4f} (Haar=2)")

# Convergence: frame potential should approach Haar value with depth
fp1_values = [frame_results[f"depth_{d}"]["frame_potential_t1"] for d in depths]
# At large depth, F_1 should be close to 1
convergence_pass = fp1_values[-1] < 1.5  # generous bound

RESULTS["9_frame_potential"] = {
    "depth_results": frame_results,
    "convergence_at_depth_10": convergence_pass,
    "pass": convergence_pass,
}


# ══════════════════════════════════════════════════════════════════════
# 10. CLIFFORD GROUP AS A 3-DESIGN FOR d=2
# ══════════════════════════════════════════════════════════════════════
print("\nSection 10: Clifford group -- 3-design verification for d=2")

# The single-qubit Clifford group has 24 elements.
# It forms a unitary 3-design: its t-th frame potential matches Haar for t<=3.
# F_t(Clifford) = t! for t=1,2,3 (but NOT for t=4).

# Generate all 24 single-qubit Cliffords
I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
H_gate = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
S_gate = np.array([[1, 0], [0, 1j]], dtype=complex)

def generate_single_qubit_cliffords():
    """Generate all single-qubit Clifford unitaries as distinct matrices.

    The single-qubit Clifford group C_1 as a matrix group (not modulo phase)
    has |C_1| = 192 elements (24 distinct Pauli-frame actions x 8 global
    phases that are 8th roots of unity). However, for the frame-potential
    3-design test, what matters is the group modulo U(1), which has 24
    projective elements. We return the 24 projective representatives.

    For the 3-design verification, we use the projective frame potential:
    F_t^proj(E) = (1/|E|^2) sum_{U,V} |Tr(U^dag V)|^{2t} / d^{2t}
    Haar value for projective t-design: integral |<psi|phi>|^{2t} = 1/binom(d+t-1,t)
    But the standard frame potential test is F_t = t! iff t-design.
    For the projective case with d=2, a 3-design has F_3 = 6.
    """
    paulis_loc = [X, Y, Z]

    def pauli_action_key(U):
        key_parts = []
        for P in paulis_loc:
            UPUd = U @ P @ U.conj().T
            for idx, Q in enumerate(paulis_loc):
                c = np.trace(UPUd @ Q) / 2.0
                if abs(abs(c) - 1.0) < 1e-8:
                    sign = int(np.round(np.real(c)))
                    key_parts.append((idx, sign))
                    break
        return tuple(key_parts)

    # Generate 24 projective Clifford elements (up to global phase)
    results = []
    seen = set()
    frontier = [I2]
    key0 = pauli_action_key(I2)
    seen.add(key0)
    results.append(I2)

    for _ in range(200):
        new_frontier = []
        for M in frontier:
            for gen in [H_gate, S_gate]:
                candidate = gen @ M
                key = pauli_action_key(candidate)
                if key not in seen:
                    seen.add(key)
                    results.append(candidate)
                    new_frontier.append(candidate)
        frontier = new_frontier
        if not frontier:
            break

    return results

cliffords = generate_single_qubit_cliffords()
n_cliff = len(cliffords)
print(f"  Generated {n_cliff} single-qubit Cliffords (expected 24)")

# Compute frame potentials
fp1_cliff = frame_potential(cliffords, t=1)
fp2_cliff = frame_potential(cliffords, t=2)
fp3_cliff = frame_potential(cliffords, t=3)

# Compute Haar reference values numerically (F_t = t! only when d >= t)
# For d=2: F_1(Haar)=1, F_2(Haar)=2, F_3(Haar)=5 (not 6, since d<t)
np.random.seed(999)
haar_refs = {}
for t_val in [1, 2, 3]:
    mc_vals = []
    for _ in range(30000):
        U_mc = haar_random_unitary_qr(2)
        mc_vals.append(abs(np.trace(U_mc)) ** (2 * t_val))
    haar_refs[t_val] = float(np.mean(mc_vals))
np.random.seed(42)  # restore

print(f"  F_1 = {fp1_cliff:.6f} (Haar ~ {haar_refs[1]:.4f})")
print(f"  F_2 = {fp2_cliff:.6f} (Haar ~ {haar_refs[2]:.4f})")
print(f"  F_3 = {fp3_cliff:.6f} (Haar ~ {haar_refs[3]:.4f})")

# 3-design: frame potential matches Haar for t=1,2,3
design_1 = abs(fp1_cliff - haar_refs[1]) < 0.1
design_2 = abs(fp2_cliff - haar_refs[2]) < 0.1
design_3 = abs(fp3_cliff - haar_refs[3]) < 0.2
is_3_design = design_1 and design_2 and design_3

RESULTS["10_clifford_3design"] = {
    "n_cliffords": n_cliff,
    "frame_potential_t1": float(fp1_cliff),
    "frame_potential_t2": float(fp2_cliff),
    "frame_potential_t3": float(fp3_cliff),
    "haar_ref_t1": haar_refs[1],
    "haar_ref_t2": haar_refs[2],
    "haar_ref_t3": haar_refs[3],
    "is_1_design": design_1,
    "is_2_design": design_2,
    "is_3_design": design_3,
    "note": "F_t = t! only when d >= t. For d=2, t=3: Haar value ~ 5, not 6.",
    "pass": is_3_design,
}
print(f"  Clifford group is a 3-design: {is_3_design}")


# ══════════════════════════════════════════════════════════════════════
# 11. PORTER-THOMAS ANTI-CONCENTRATION
# ══════════════════════════════════════════════════════════════════════
print("\nSection 11: Porter-Thomas distribution for random circuit outputs")

# For a Haar-random state |psi> in C^D, each output probability p_k = |<k|psi>|^2
# follows Beta(1, D-1).  In the D -> inf limit, D*p_k -> Exp(1) (Porter-Thomas).
#
# Exact results for Beta(1, D-1):
#   E[p_k] = 1/D
#   Var[p_k] = (D-1) / (D^2 * (D+1))
#   CDF: F(p) = 1 - (1-p)^{D-1}
#
# We verify BOTH the exact finite-D distribution AND the Porter-Thomas limit.

# --- Part A: exact Beta(1, D-1) test at D=4 ---
D_pt = 4
n_pt_samples = 2000

all_raw_probs = []
for _ in range(n_pt_samples):
    psi = haar_random_state(D_pt)
    probs = np.abs(psi.ravel()) ** 2
    all_raw_probs.extend(probs)

all_raw_probs = np.array(all_raw_probs)

# Exact moments of Beta(1, D-1)
exact_mean = 1.0 / D_pt
exact_var = (D_pt - 1) / (D_pt**2 * (D_pt + 1))

meas_mean = float(np.mean(all_raw_probs))
meas_var = float(np.var(all_raw_probs))
mean_pass = abs(meas_mean - exact_mean) < 0.01
var_pass = abs(meas_var - exact_var) < 0.01

# KS test against Beta(1, D-1) CDF: F(p) = 1 - (1-p)^{D-1}
sorted_p = np.sort(all_raw_probs)
n_total = len(sorted_p)
empirical_cdf = np.arange(1, n_total + 1) / n_total
theoretical_cdf = 1.0 - (1.0 - sorted_p) ** (D_pt - 1)
ks_stat = float(np.max(np.abs(empirical_cdf - theoretical_cdf)))
ks_critical = 1.36 / np.sqrt(n_total)
ks_pass = ks_stat < ks_critical

# --- Part B: Porter-Thomas (large D) test at D=256 ---
D_pt_large = 256
n_pt_large = 500

all_rescaled = []
for _ in range(n_pt_large):
    psi = haar_random_state(D_pt_large)
    probs = np.abs(psi.ravel()) ** 2
    all_rescaled.extend(probs * D_pt_large)

all_rescaled = np.array(all_rescaled)

pt_mean = float(np.mean(all_rescaled))
pt_var = float(np.var(all_rescaled))
pt_mean_pass = abs(pt_mean - 1.0) < 0.1
pt_var_pass = abs(pt_var - 1.0) < 0.3

# KS test against Exp(1)
sorted_rescaled = np.sort(all_rescaled)
n_total_large = len(sorted_rescaled)
emp_cdf_large = np.arange(1, n_total_large + 1) / n_total_large
theo_cdf_large = 1.0 - np.exp(-sorted_rescaled)
ks_stat_large = float(np.max(np.abs(emp_cdf_large - theo_cdf_large)))
ks_crit_large = 1.36 / np.sqrt(n_total_large)
ks_pass_large = ks_stat_large < ks_crit_large

# Anti-concentration: Pr[D*p > 1] should approach exp(-1) ~ 0.368
frac_above_mean = float(np.mean(all_rescaled > 1.0))
anti_conc_pass = abs(frac_above_mean - np.exp(-1)) < 0.05

RESULTS["11_porter_thomas"] = {
    "part_A_exact_beta": {
        "D": D_pt,
        "n_probabilities": n_total,
        "exact_mean": float(exact_mean),
        "measured_mean": meas_mean,
        "exact_var": float(exact_var),
        "measured_var": meas_var,
        "mean_pass": mean_pass,
        "var_pass": var_pass,
        "ks_statistic": ks_stat,
        "ks_critical": float(ks_critical),
        "ks_pass": ks_pass,
    },
    "part_B_porter_thomas_limit": {
        "D": D_pt_large,
        "n_probabilities": n_total_large,
        "rescaled_mean": pt_mean,
        "rescaled_var": pt_var,
        "mean_pass": pt_mean_pass,
        "ks_statistic": float(ks_stat_large),
        "ks_critical": float(ks_crit_large),
        "ks_pass": ks_pass_large,
        "frac_above_mean": frac_above_mean,
        "expected_frac": float(np.exp(-1)),
        "anti_conc_pass": anti_conc_pass,
    },
    "pass": bool(ks_pass and ks_pass_large and anti_conc_pass),
}

print(f"  Part A (D={D_pt}, exact Beta(1,{D_pt-1})):")
print(f"    Mean: {meas_mean:.6f} (exact {exact_mean:.6f})")
print(f"    KS stat: {ks_stat:.6f} (critical {ks_critical:.6f}), pass: {ks_pass}")
print(f"  Part B (D={D_pt_large}, Porter-Thomas limit):")
print(f"    Rescaled mean: {pt_mean:.4f} (expected 1.0)")
print(f"    KS stat: {ks_stat_large:.6f} (critical {ks_crit_large:.6f}), pass: {ks_pass_large}")
print(f"    Anti-conc frac: {frac_above_mean:.4f} (expected {np.exp(-1):.4f})")
print(f"  Porter-Thomas overall: {RESULTS['11_porter_thomas']['pass']}")


# ══════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════

summary = {
    "2_all_unitaries_valid": RESULTS["2_unitarity"]["all_pass"],
    "3_all_states_pure": RESULTS["3_state_ensemble"]["all_pure"],
    "4_page_result": RESULTS["4_page_entanglement"]["page_pass"],
    "5_concurrence_mean": RESULTS["5_concurrence"]["pass"],
    "6_marginal_purity": RESULTS["6_marginal_purity"]["pass_mean"],
    "6_marginal_symmetry": RESULTS["6_marginal_purity"]["pass_symmetry"],
    "7_mi_mean": RESULTS["7_mutual_information"]["pass_mean"],
    "7_mi_identity": RESULTS["7_mutual_information"]["mi_equals_2S_identity"],
    "8_concentration": RESULTS["8_concentration"]["pass"],
    "9_circuit_convergence": RESULTS["9_frame_potential"]["pass"],
    "10_clifford_3design": RESULTS["10_clifford_3design"]["pass"],
    "11_porter_thomas": RESULTS["11_porter_thomas"]["pass"],
}

all_pass = all(summary.values())
RESULTS["summary"] = summary
RESULTS["ALL_PASS"] = all_pass

print(f"\n{'=' * 60}")
print(f"PURE LEGO RANDOM CIRCUITS & TYPICALITY -- ALL PASS: {all_pass}")
print(f"{'=' * 60}")
for k, v in summary.items():
    tag = "PASS" if v else "FAIL"
    print(f"  [{tag}] {k}")

# Write results
out_path = pathlib.Path(__file__).parent / "a2_state" / "sim_results" / "pure_lego_random_circuits_typicality_results.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w") as f:
    json.dump(RESULTS, f, indent=2, default=str)
print(f"\nResults written to {out_path}")
