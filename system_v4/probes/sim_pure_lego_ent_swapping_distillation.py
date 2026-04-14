#!/usr/bin/env python3
"""
PURE LEGO: Entanglement Swapping & Distillation
================================================
Foundational building block.  Pure math only -- numpy + scipy.
No engine imports.  Every operation verified against theory.

Sections
--------
1. Entanglement Swapping
   Alice-Bob Bell pair + Bob-Charlie Bell pair.
   Bob does Bell measurement on his two qubits.
   Result: Alice-Charlie entangled (concurrence = 1).
2. Entanglement Distillation
   N noisy Werner pairs (p=0.8).  CNOT+measure protocol.
   Output fidelity > input fidelity (purification).
   Compute yield (fraction surviving).
3. LOCC Bound
   Distillation rate <= E_D (distillable entanglement).
   Numerical verification.
"""

import json, pathlib, time
import numpy as np
from scipy.linalg import sqrtm
classification = "classical_baseline"  # auto-backfill

np.random.seed(42)
EPS = 1e-14
RESULTS = {}

# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

I2 = np.eye(2, dtype=complex)
I4 = np.eye(4, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)

def ket(v):
    """Column vector from list."""
    return np.array(v, dtype=complex).reshape(-1, 1)

def dm(v):
    """Density matrix from ket vector."""
    k = ket(v)
    return k @ k.conj().T

def partial_trace(rho, dims, keep):
    """
    Partial trace of density matrix rho over subsystems NOT in keep.
    dims: list of subsystem dimensions, e.g. [2,2,2,2] for 4 qubits.
    keep: list of indices to keep, e.g. [0,3] for first and last.
    """
    n = len(dims)
    rho_reshaped = rho.reshape(dims + dims)
    # Build the axes to trace over
    trace_over = sorted(set(range(n)) - set(keep))
    # We need to trace pairs: axis i and axis i+n
    # Work from highest index to lowest to avoid shifting
    for ax in sorted(trace_over, reverse=True):
        rho_reshaped = np.trace(rho_reshaped, axis1=ax, axis2=ax + len(dims))
        # After tracing axis ax and ax+len(dims), the remaining dims shrink
        dims = [d for i, d in enumerate(dims) if i != ax]
        # Update keep indices
        keep = [k - (1 if k > ax else 0) for k in keep]
    return rho_reshaped.reshape(np.prod([dims[k] for k in range(len(dims))]),
                                 np.prod([dims[k] for k in range(len(dims))]))

def concurrence(rho):
    """Concurrence of a 2-qubit density matrix."""
    sy_sy = np.kron(sy, sy)
    rho_tilde = sy_sy @ rho.conj() @ sy_sy
    M = rho @ rho_tilde
    # sqrtm can be numerically tricky; use eigenvalues
    evals = np.sort(np.real(np.linalg.eigvals(M)))[::-1]
    # Clamp small negatives
    evals = np.maximum(evals, 0.0)
    sqrt_evals = np.sqrt(evals)
    C = max(0.0, sqrt_evals[0] - sqrt_evals[1] - sqrt_evals[2] - sqrt_evals[3])
    return float(C)

def fidelity_to_bell(rho):
    """Fidelity of rho with respect to |Phi+> = (|00>+|11>)/sqrt(2)."""
    phi_plus = ket([1, 0, 0, 1]) / np.sqrt(2)
    return float(np.real((phi_plus.conj().T @ rho @ phi_plus)[0, 0]))

def werner_state(p, d=2):
    """Werner state: p * |Phi+><Phi+| + (1-p)/4 * I4."""
    phi_plus = ket([1, 0, 0, 1]) / np.sqrt(2)
    proj = phi_plus @ phi_plus.conj().T
    return p * proj + (1 - p) / (d * d) * I4

def hashing_bound(rho):
    """
    Hashing bound / coherent information: E_D >= S(B) - S(AB).
    For a Werner state this gives the distillable entanglement lower bound.
    Returns the coherent information I_coh = S(rho_B) - S(rho_AB).
    """
    # S(rho_AB)
    evals_ab = np.linalg.eigvalsh(rho)
    evals_ab = evals_ab[evals_ab > EPS]
    S_AB = -np.sum(evals_ab * np.log2(evals_ab))

    # S(rho_B) via partial trace
    rho_B = partial_trace(rho, [2, 2], [1])
    evals_b = np.linalg.eigvalsh(rho_B)
    evals_b = evals_b[evals_b > EPS]
    S_B = -np.sum(evals_b * np.log2(evals_b))

    return float(S_B - S_AB)


# ══════════════════════════════════════════════════════════════════════
# 1.  ENTANGLEMENT SWAPPING
# ══════════════════════════════════════════════════════════════════════
print("=" * 60)
print("SECTION 1: Entanglement Swapping")
print("=" * 60)

t0 = time.time()

# Bell state |Phi+> = (|00> + |11>) / sqrt(2)
phi_plus = ket([1, 0, 0, 1]) / np.sqrt(2)

# 4-qubit state: |Phi+>_AB tensor |Phi+>_BC
# Qubits: A(0), B1(1), B2(2), C(3)
psi_4 = np.kron(phi_plus, phi_plus)  # 16-dim
rho_4 = psi_4 @ psi_4.conj().T

# Verify: before swapping, A-C have no entanglement
rho_AC_before = partial_trace(rho_4, [2, 2, 2, 2], [0, 3])
C_AC_before = concurrence(rho_AC_before)
print(f"  Concurrence(A,C) BEFORE swap: {C_AC_before:.6f} (expect 0)")

# Bell measurement on B1, B2 (qubits 1,2)
# Bell basis for qubits B1, B2:
bell_states = []
bell_labels = []
# |Phi+> = (|00>+|11>)/sqrt(2)
bell_states.append(ket([1, 0, 0, 1]) / np.sqrt(2))
bell_labels.append("Phi+")
# |Phi-> = (|00>-|11>)/sqrt(2)
bell_states.append(ket([1, 0, 0, -1]) / np.sqrt(2))
bell_labels.append("Phi-")
# |Psi+> = (|01>+|10>)/sqrt(2)
bell_states.append(ket([0, 1, 1, 0]) / np.sqrt(2))
bell_labels.append("Psi+")
# |Psi-> = (|01>-|10>)/sqrt(2)
bell_states.append(ket([0, 1, -1, 0]) / np.sqrt(2))
bell_labels.append("Psi-")

# Project B1B2 onto each Bell state, get post-measurement A-C state
swap_results = []
for bell_ket, label in zip(bell_states, bell_labels):
    # Projector on B1B2: I_A tensor |bell><bell|_B1B2 tensor I_C
    proj_B = bell_ket @ bell_ket.conj().T  # 4x4
    proj_full = np.kron(np.kron(I2, proj_B), I2)  # 16x16

    # Post-measurement state (unnormalized)
    rho_post = proj_full @ rho_4 @ proj_full
    prob = np.real(np.trace(rho_post))

    if prob > EPS:
        rho_post_norm = rho_post / prob
        # Trace out B1, B2 to get A-C
        rho_AC = partial_trace(rho_post_norm, [2, 2, 2, 2], [0, 3])
        C_AC = concurrence(rho_AC)
        F_AC = fidelity_to_bell(rho_AC)
    else:
        C_AC = 0.0
        F_AC = 0.0

    swap_results.append({
        "bell_outcome": label,
        "probability": float(prob),
        "concurrence_AC": C_AC,
        "fidelity_bell_AC": F_AC,
    })
    print(f"  Outcome {label}: prob={prob:.4f}, C(A,C)={C_AC:.6f}")

# Each outcome should give concurrence = 1 with probability 1/4
all_C1 = all(abs(r["concurrence_AC"] - 1.0) < 1e-6 for r in swap_results)
all_prob_quarter = all(abs(r["probability"] - 0.25) < 1e-6 for r in swap_results)

RESULTS["1_entanglement_swapping"] = {
    "concurrence_AC_before_swap": C_AC_before,
    "before_swap_zero": bool(C_AC_before < 1e-6),
    "outcomes": swap_results,
    "all_concurrence_one": all_C1,
    "all_prob_quarter": all_prob_quarter,
    "elapsed_s": time.time() - t0,
}

print(f"  All outcomes C=1: {all_C1}")
print(f"  All probs=1/4:    {all_prob_quarter}")


# ══════════════════════════════════════════════════════════════════════
# 2.  ENTANGLEMENT DISTILLATION (BBPSSW / recurrence protocol)
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'=' * 60}")
print("SECTION 2: Entanglement Distillation")
print("=" * 60)

t0 = time.time()

# --- BBPSSW analytical recurrence on Werner fidelity ---
# Standard result (Bennett et al. 1996):
# Given two Werner states with fidelity F, after bilateral CNOT + measure
# and bilateral twirling, the output fidelity is:
#   F' = (F^2 + (1-F)^2/9) / (F^2 + 2F(1-F)/3 + 5(1-F)^2/9)
# Success probability:
#   p_success = F^2 + 2F(1-F)/3 + 5(1-F)^2/9

def bbpssw_recurrence(F):
    """One round of BBPSSW: returns (F_out, p_success)."""
    x = 1.0 - F
    num = F**2 + x**2 / 9.0
    denom = F**2 + 2.0 * F * x / 3.0 + 5.0 * x**2 / 9.0
    return num / denom, denom

# Also verify with explicit density matrix for round 1
def bilateral_cnot_distill(rho_source, rho_target):
    """
    One round of BBPSSW (bilateral CNOT) distillation.
    Two copies of a 2-qubit state.  Apply CNOT_A1->A2 and CNOT_B1->B2.
    Measure A2, B2 in computational basis.  Keep only if outcomes agree.

    rho_source, rho_target: 4x4 density matrices (2-qubit each).

    Returns (rho_out, prob_success) where rho_out is the distilled
    state on qubits A1, B1 conditioned on agreement.
    """
    # rho_4q = rho_target (A1,B1) tensor rho_source (A2,B2)
    rho_4q = np.kron(rho_target, rho_source)  # 16x16, ordering: A1 B1 A2 B2

    # CNOT from A1->A2: acts on qubits 0,2 (with 1,3 as spectators)
    CNOT = np.zeros((16, 16), dtype=complex)
    for a1 in range(2):
        for b1 in range(2):
            for a2 in range(2):
                for b2 in range(2):
                    a2_new = (a1 ^ a2)
                    idx_in = a1 * 8 + b1 * 4 + a2 * 2 + b2
                    idx_out = a1 * 8 + b1 * 4 + a2_new * 2 + b2
                    CNOT[idx_out, idx_in] = 1.0

    # CNOT from B1->B2: acts on qubits 1,3
    CNOT_B = np.zeros((16, 16), dtype=complex)
    for a1 in range(2):
        for b1 in range(2):
            for a2 in range(2):
                for b2 in range(2):
                    b2_new = (b1 ^ b2)
                    idx_in = a1 * 8 + b1 * 4 + a2 * 2 + b2
                    idx_out = a1 * 8 + b1 * 4 + a2 * 2 + b2_new
                    CNOT_B[idx_out, idx_in] = 1.0

    # Apply both CNOTs
    rho_after = CNOT_B @ CNOT @ rho_4q @ CNOT.conj().T @ CNOT_B.conj().T

    # Measure A2, B2. Keep only if they agree (both 0 or both 1).
    rho_out = np.zeros((4, 4), dtype=complex)
    prob_total = 0.0

    for outcome in [0, 1]:  # a2=b2=outcome
        proj = np.zeros((4, 16), dtype=complex)
        for a1 in range(2):
            for b1 in range(2):
                row = a1 * 2 + b1
                col = a1 * 8 + b1 * 4 + outcome * 2 + outcome
                proj[row, col] = 1.0

        block = proj @ rho_after @ proj.conj().T  # 4x4
        prob = np.real(np.trace(block))
        prob_total += prob
        rho_out += block

    if prob_total > EPS:
        rho_out /= prob_total

    return rho_out, float(prob_total)


# --- Verify explicit round 1 matches analytical recurrence ---
p_werner = 0.8
rho_input = werner_state(p_werner)
input_fidelity = fidelity_to_bell(rho_input)
input_concurrence = concurrence(rho_input)
print(f"  Input Werner p={p_werner}")
print(f"    Fidelity to |Phi+>: {input_fidelity:.6f}")
print(f"    Concurrence:        {input_concurrence:.6f}")

# Explicit density matrix round
rho_dist_1, prob_1 = bilateral_cnot_distill(rho_input, rho_input)
fid_explicit = fidelity_to_bell(rho_dist_1)

# Analytical round
fid_analytical, prob_analytical = bbpssw_recurrence(input_fidelity)

print(f"\n  Round 1 (explicit DM):   F={fid_explicit:.6f}, prob={prob_1:.6f}")
print(f"  Round 1 (analytical):    F={fid_analytical:.6f}, prob={prob_analytical:.6f}")
dm_vs_analytical_match = abs(fid_explicit - fid_analytical) < 1e-4
print(f"  DM matches analytical:   {dm_vs_analytical_match}")

# --- Multi-round via analytical recurrence (with implicit twirling) ---
N_ROUNDS = 8
F_current = input_fidelity
fidelities = [F_current]
concurrences_an = [input_concurrence]
yields = [1.0]

for r in range(N_ROUNDS):
    F_next, p_succ = bbpssw_recurrence(F_current)
    # Werner concurrence: C = max(0, (3F-1)/2) ... wait,
    # Werner state with fidelity F has p = (4F-1)/3, concurrence = max(0, (3p-1)/2)
    p_w = (4.0 * F_next - 1.0) / 3.0
    conc = max(0.0, (3.0 * p_w - 1.0) / 2.0)
    fidelities.append(F_next)
    concurrences_an.append(conc)
    yields.append(yields[-1] * p_succ / 2.0)
    F_current = F_next
    print(f"  Round {r+1}: F={F_next:.6f}, C={conc:.6f}, "
          f"prob={p_succ:.4f}, cumulative_yield={yields[-1]:.6f}")

purification_achieved = fidelities[-1] > fidelities[0]
monotone_fidelity = all(fidelities[i+1] >= fidelities[i] - 1e-10
                        for i in range(len(fidelities)-1))

RESULTS["2_entanglement_distillation"] = {
    "werner_p": p_werner,
    "input_fidelity": input_fidelity,
    "input_concurrence": input_concurrence,
    "dm_vs_analytical_match": dm_vs_analytical_match,
    "explicit_round1_fidelity": fid_explicit,
    "analytical_round1_fidelity": fid_analytical,
    "rounds": N_ROUNDS,
    "fidelities": fidelities,
    "concurrences": concurrences_an,
    "cumulative_yields": yields,
    "final_fidelity": fidelities[-1],
    "final_concurrence": concurrences_an[-1],
    "purification_achieved": purification_achieved,
    "monotone_fidelity_increase": monotone_fidelity,
    "elapsed_s": time.time() - t0,
}

print(f"\n  Purification achieved: {purification_achieved}")
print(f"  Monotone fidelity:    {monotone_fidelity}")


# ══════════════════════════════════════════════════════════════════════
# 3.  LOCC BOUND: Distillation rate <= E_D
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'=' * 60}")
print("SECTION 3: LOCC Bound (Distillation Rate vs E_D)")
print("=" * 60)

t0 = time.time()

# For Werner states, the hashing bound gives a lower bound on E_D:
#   E_D >= I_coh = S(B) - S(AB)
# The distillation RATE (ebits per input pair in asymptotic limit) is
# bounded above by E_D. For finite recurrence rounds, we verify:
#   (a) Hashing bound is positive iff F > some threshold
#   (b) Cumulative yield (pairs out / pairs in) <= 1 always (trivially)
#   (c) The finite-round yield is far below E_D (finite protocol is suboptimal)
#   (d) At p=1, coherent info = 1 ebit exactly.

# Test over a range of Werner p values
p_values = np.linspace(0.5, 1.0, 11)
locc_results = []

for p in p_values:
    rho_w = werner_state(p)
    fid = fidelity_to_bell(rho_w)
    conc = concurrence(rho_w)
    I_coh = hashing_bound(rho_w)

    # Distillation via analytical recurrence: 5 rounds
    F_curr = fid
    cum_yield = 1.0
    for _ in range(5):
        F_next, p_succ = bbpssw_recurrence(F_curr)
        cum_yield *= p_succ / 2.0
        F_curr = F_next

    locc_results.append({
        "p": float(p),
        "fidelity_input": float(fid),
        "concurrence": float(conc),
        "coherent_information": float(I_coh),
        "hashing_bound_positive": bool(I_coh > 0),
        "distillation_yield_5rounds": float(cum_yield),
        "final_fidelity_5rounds": float(F_curr),
    })
    print(f"  p={p:.2f}: I_coh={I_coh:.4f}, yield={cum_yield:.6f}, "
          f"F_out={F_curr:.6f}")

# Key checks:
# 1. Concurrence > 0 iff p > 1/3 (Werner entanglement threshold)
# 2. Hashing bound positive for p > threshold (~0.8107)
# 3. For F > 0.5, BBPSSW converges to F=1 (purification works)

hashing_positive_count = sum(1 for r in locc_results if r["hashing_bound_positive"])
all_entangled = all(r["concurrence"] > 0 for r in locc_results if r["p"] > 1/3 + 0.01)

# Verify: at p=1 (pure Bell pair), coherent info = 1 (1 ebit)
rho_bell_pure = werner_state(1.0)
I_coh_pure = hashing_bound(rho_bell_pure)
pure_bell_ebit = abs(I_coh_pure - 1.0) < 1e-6
print(f"\n  Pure Bell pair coherent info: {I_coh_pure:.6f} (expect 1.0)")
print(f"  Pure Bell = 1 ebit: {pure_bell_ebit}")

# Verify: finite-round yield is always <= hashing bound (E_D upper bound)
# For BBPSSW, the finite-round yield is always suboptimal compared to
# the asymptotic rate.  We check yield < max(I_coh, 0) + small tolerance.
# Note: yield is always <= 0.5^rounds in the best case, and E_D <= 1,
# so for 5 rounds yield is at most ~0.03 which is always below E_D.
yield_below_bound = True
for r in locc_results:
    if r["coherent_information"] > 0:
        # Finite-round yield should be well below the hashing bound
        if r["distillation_yield_5rounds"] > r["coherent_information"] + 0.05:
            yield_below_bound = False

print(f"  Yield respects hashing bound: {yield_below_bound}")

# Verify: for F > 0.5, distillation actually increases fidelity
purification_works_all = True
for r in locc_results:
    if r["fidelity_input"] > 0.5 + 1e-6:
        if r["final_fidelity_5rounds"] <= r["fidelity_input"]:
            purification_works_all = False
print(f"  Purification works for all F>0.5: {purification_works_all}")

RESULTS["3_locc_bound"] = {
    "p_values_tested": [float(p) for p in p_values],
    "results": locc_results,
    "pure_bell_coherent_info": float(I_coh_pure),
    "pure_bell_one_ebit": pure_bell_ebit,
    "hashing_positive_count": hashing_positive_count,
    "all_entangled_above_threshold": all_entangled,
    "yield_respects_hashing_bound": yield_below_bound,
    "purification_works_all_above_half": purification_works_all,
    "elapsed_s": time.time() - t0,
}


# ══════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════

summary = {
    "1_swap_AC_unentangled_before": RESULTS["1_entanglement_swapping"]["before_swap_zero"],
    "1_swap_all_concurrence_one": RESULTS["1_entanglement_swapping"]["all_concurrence_one"],
    "1_swap_all_prob_quarter": RESULTS["1_entanglement_swapping"]["all_prob_quarter"],
    "2_distill_purification_achieved": RESULTS["2_entanglement_distillation"]["purification_achieved"],
    "2_distill_monotone_fidelity": RESULTS["2_entanglement_distillation"]["monotone_fidelity_increase"],
    "3_locc_pure_bell_one_ebit": RESULTS["3_locc_bound"]["pure_bell_one_ebit"],
    "3_locc_yield_respects_bound": RESULTS["3_locc_bound"]["yield_respects_hashing_bound"],
    "3_locc_all_entangled_above_threshold": RESULTS["3_locc_bound"]["all_entangled_above_threshold"],
}

all_pass = all(summary.values())
RESULTS["summary"] = summary
RESULTS["ALL_PASS"] = all_pass

print(f"\n{'=' * 60}")
print(f"PURE LEGO ENT SWAPPING + DISTILLATION -- ALL PASS: {all_pass}")
print(f"{'=' * 60}")
for k, v in summary.items():
    tag = "PASS" if v else "FAIL"
    print(f"  [{tag}] {k}")

# Write results
out_path = (pathlib.Path(__file__).parent / "a2_state" / "sim_results"
            / "pure_lego_ent_swapping_distillation_results.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w") as f:
    json.dump(RESULTS, f, indent=2, default=str)
print(f"\nResults written to {out_path}")
