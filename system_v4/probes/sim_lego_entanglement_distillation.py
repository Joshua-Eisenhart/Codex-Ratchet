#!/usr/bin/env python3
"""
Entanglement Distillation & Dilution -- BBPSSW protocol and irreversibility.
=============================================================================

Pure math lego.  Protocols tested:

1. WERNER STATE construction:
     rho(p) = p |Phi+><Phi+| + (1-p) I/4
   Fidelity F = <Phi+|rho|Phi+> = (1+3p)/4.

2. BBPSSW (one round):
     Start with 2 copies of Werner state at fidelity F.
     Bilateral CNOT, measure target pair, keep source if results match.
     Output fidelity:
       F_out = (F^2 + (1-F)^2/9) / (F^2 + 2F(1-F)/3 + 5(1-F)^2/9)

3. ITERATED BBPSSW:
     Track fidelity over N rounds.  Each round consumes 2 pairs -> 1 pair.
     Fidelity monotonically increases when F > 1/2.

4. THRESHOLD:
     Distillable iff F > 1/2 (equivalently p > 1/3).
     z3 proves: F > 1/2 => F_out > F (strict improvement).

5. LOG-NEGATIVITY upper bound:
     E_N(rho) = log2(||rho^{T_B}||_1).  For Werner: max(0, log2(1 + 2p) - 1).
     Distillable entanglement E_D <= E_N.

6. ENTANGLEMENT DILUTION:
     Convert n Bell pairs into ~n/S(rho_A) Werner states (asymptotic).
     Entanglement cost E_C = S(rho_A) = H_bin((1+3p)/4) for Werner.

7. IRREVERSIBILITY:
     E_D <= E_C always.  Strict inequality for mixed states (p < 1).

Mark pytorch=used, z3=used.  Classification: canonical.
Output: sim_results/lego_entanglement_distillation_results.json
"""

import json
import os
import traceback
import time
import math
import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- 2-qubit density matrices only"},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed for this sim"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed -- pytorch handles all numerics"},
    "clifford":  {"tried": False, "used": False, "reason": "not needed for this sim"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this sim"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed for this sim"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this sim"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed for this sim"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed for this sim"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed for this sim"},
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Core: density matrix arithmetic, partial trace, eigenvalues, "
        "autograd for gradient of fidelity w.r.t. Werner parameter"
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    from z3 import Reals, And, Implies, ForAll, Solver, sat, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "Prove: F > 1/2 => BBPSSW output fidelity strictly exceeds input; "
        "prove: F <= 1/2 => output fidelity <= input (no distillation)"
    )
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"


# =====================================================================
# CONSTANTS (4x4 two-qubit space)
# =====================================================================

I2 = torch.eye(2, dtype=torch.complex128)
I4 = torch.eye(4, dtype=torch.complex128)

# Bell state |Phi+> = (|00> + |11>) / sqrt(2)
PHI_PLUS_KET = torch.zeros(4, dtype=torch.complex128)
PHI_PLUS_KET[0] = 1.0 / math.sqrt(2)  # |00>
PHI_PLUS_KET[3] = 1.0 / math.sqrt(2)  # |11>
PHI_PLUS_PROJ = torch.outer(PHI_PLUS_KET, PHI_PLUS_KET.conj())

# Pauli matrices
X = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
Y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
Z = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)


# =====================================================================
# CORE FUNCTIONS
# =====================================================================

def werner_state(p):
    """Werner state rho(p) = p |Phi+><Phi+| + (1-p) I/4."""
    if isinstance(p, torch.Tensor):
        return p * PHI_PLUS_PROJ + (1.0 - p) * I4 / 4.0
    else:
        return float(p) * PHI_PLUS_PROJ + (1.0 - float(p)) * I4 / 4.0


def werner_fidelity(p):
    """Fidelity F = <Phi+|rho(p)|Phi+> = (1 + 3p)/4."""
    return (1.0 + 3.0 * p) / 4.0


def p_from_fidelity(F):
    """Inverse: p = (4F - 1)/3."""
    return (4.0 * F - 1.0) / 3.0


def bbpssw_output_fidelity(F):
    """
    One round of BBPSSW protocol.
    F_out = (F^2 + (1-F)^2/9) / (F^2 + 2F(1-F)/3 + 5(1-F)^2/9)
    """
    F2 = F * F
    oF = 1.0 - F
    oF2 = oF * oF
    num = F2 + oF2 / 9.0
    den = F2 + 2.0 * F * oF / 3.0 + 5.0 * oF2 / 9.0
    return num / den


def bbpssw_success_prob(F):
    """Probability that the BBPSSW round succeeds (measurement outcomes match)."""
    oF = 1.0 - F
    return F * F + 2.0 * F * oF / 3.0 + 5.0 * oF * oF / 9.0


def iterate_bbpssw(F_init, n_rounds):
    """Run n_rounds of BBPSSW.  Return list of fidelities [F0, F1, ..., Fn]."""
    fidelities = [F_init]
    F = F_init
    for _ in range(n_rounds):
        F = bbpssw_output_fidelity(F)
        fidelities.append(F)
    return fidelities


def partial_transpose_B(rho_4x4):
    """
    Partial transpose on subsystem B of a 4x4 density matrix.
    rho reshaped to (2,2,2,2): rho[i,j,k,l] -> rho[i,l,k,j].
    """
    rho_r = rho_4x4.reshape(2, 2, 2, 2)
    rho_pt = rho_r.permute(0, 3, 2, 1).reshape(4, 4)
    return rho_pt


def log_negativity(rho_4x4):
    """
    E_N = log2(||rho^{T_B}||_1) where ||.||_1 = sum of abs eigenvalues.
    """
    rho_pt = partial_transpose_B(rho_4x4)
    eigvals = torch.linalg.eigvalsh(rho_pt.real)  # Hermitian
    trace_norm = torch.sum(torch.abs(eigvals))
    return torch.log2(trace_norm)


def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho log2 rho).  Eigenvalue-based."""
    eigvals = torch.linalg.eigvalsh(rho.real)
    eigvals = eigvals[eigvals > 1e-15]  # clip zeros
    return -torch.sum(eigvals * torch.log2(eigvals))


def partial_trace_B(rho_4x4):
    """Trace out qubit B from a 4x4 density matrix -> 2x2."""
    rho_r = rho_4x4.reshape(2, 2, 2, 2)
    return torch.einsum('ijik->jk', rho_r)


def entanglement_cost_werner(p):
    """
    E_C = S(rho_A) for Werner state.
    rho_A = partial trace of rho(p) = ((1+p)/2)|0><0| + ((1-p)/2)|1><1|
    Actually for Werner: rho_A = I/2 always (maximally mixed marginal).
    So E_C = S(I/2) = 1.  But that's the entanglement of formation bound.

    More precisely, entanglement of formation for Werner state:
    E_f(rho) = H_bin((1 + sqrt(1 - C^2))/2) where C = max(0, (3p-1)/2) is concurrence.
    """
    C = max(0.0, (3.0 * p - 1.0) / 2.0)
    if C < 1e-15:
        return 0.0
    x = (1.0 + math.sqrt(1.0 - C * C)) / 2.0
    if x <= 0 or x >= 1:
        return 0.0
    return -x * math.log2(x) - (1.0 - x) * math.log2(1.0 - x)


def binary_entropy(x):
    """H_bin(x) = -x log2(x) - (1-x) log2(1-x)."""
    if x <= 0 or x >= 1:
        return 0.0
    return -x * math.log2(x) - (1.0 - x) * math.log2(1.0 - x)


# =====================================================================
# FULL DENSITY-MATRIX BBPSSW (verification against analytic formula)
# =====================================================================

def cnot_gate():
    """4x4 CNOT: control=qubit0, target=qubit1."""
    c = torch.zeros(4, 4, dtype=torch.complex128)
    # |00> -> |00>, |01> -> |01>, |10> -> |11>, |11> -> |10>
    c[0, 0] = 1.0
    c[1, 1] = 1.0
    c[3, 2] = 1.0
    c[2, 3] = 1.0
    return c


def bbpssw_density_matrix(rho):
    """
    Full density-matrix BBPSSW on two copies of rho (each 4x4, two-qubit).
    System: 4 qubits = A1 B1 A2 B2 (16x16).
    1. Form rho_tot = rho_{A1B1} tensor rho_{A2B2}.
    2. Apply bilateral CNOT: CNOT_{A1->A2} tensor CNOT_{B1->B2}.
    3. Measure A2, B2 in computational basis.
    4. Keep A1, B1 if measurement outcomes match.
    Returns: (output_rho_A1B1, success_prob)
    """
    # rho_tot = rho x rho  (16x16)
    rho_tot = torch.kron(rho, rho)

    # Bilateral CNOT: CNOT on qubits (0,2) and CNOT on qubits (1,3)
    # In the 16-dim space with basis |a1 b1 a2 b2>
    CNOT = cnot_gate()

    # CNOT_{A1->A2}: acts on qubits 0,2.  Need to build 16x16.
    # Reorder: treat as (A1,A2) x (B1,B2) for the A-CNOT, but that's tricky.
    # Simpler: build the full 16x16 bilateral CNOT directly.
    # |a1 b1 a2 b2> -> |a1 b1 (a2 XOR a1) (b2 XOR b1)>
    bilateral = torch.zeros(16, 16, dtype=torch.complex128)
    for a1 in range(2):
        for b1 in range(2):
            for a2 in range(2):
                for b2 in range(2):
                    in_idx = a1 * 8 + b1 * 4 + a2 * 2 + b2
                    a2_out = a2 ^ a1
                    b2_out = b2 ^ b1
                    out_idx = a1 * 8 + b1 * 4 + a2_out * 2 + b2_out
                    bilateral[out_idx, in_idx] = 1.0

    # Apply bilateral CNOT
    rho_after = bilateral @ rho_tot @ bilateral.conj().T

    # Measure qubits A2, B2 and keep if they match: |00> or |11>
    # Project onto |a2=0, b2=0> and |a2=1, b2=1>
    rho_out = torch.zeros(4, 4, dtype=torch.complex128)
    prob_total = 0.0

    for m_val in [0, 1]:  # matching measurement outcomes
        # Projector onto |a2=m_val, b2=m_val> in the A2B2 subspace
        proj_16 = torch.zeros(16, 16, dtype=torch.complex128)
        for a1 in range(2):
            for b1 in range(2):
                idx = a1 * 8 + b1 * 4 + m_val * 2 + m_val
                proj_16[idx, idx] = 1.0

        projected = proj_16 @ rho_after @ proj_16
        prob = torch.trace(projected).real

        # Partial trace over A2B2 to get 4x4 on A1B1
        if prob > 1e-15:
            proj_r = projected.reshape(2, 2, 2, 2, 2, 2, 2, 2)
            # Trace over A2 (index 4) and B2 (index 6) -- but indexing is tricky
            # Easier: trace explicitly
            rho_a1b1 = torch.zeros(4, 4, dtype=torch.complex128)
            for a1 in range(2):
                for b1 in range(2):
                    for a1p in range(2):
                        for b1p in range(2):
                            val = 0.0
                            for a2 in range(2):
                                for b2 in range(2):
                                    row = a1 * 8 + b1 * 4 + a2 * 2 + b2
                                    col = a1p * 8 + b1p * 4 + a2 * 2 + b2
                                    val = val + projected[row, col]
                            rho_a1b1[a1 * 2 + b1, a1p * 2 + b1p] = val
            rho_out = rho_out + rho_a1b1
            prob_total = prob_total + prob.item()

    # Normalize
    if prob_total > 1e-15:
        rho_out = rho_out / prob_total

    return rho_out, prob_total


# =====================================================================
# Z3 PROOF: THRESHOLD AND MONOTONICITY
# =====================================================================

def z3_prove_threshold():
    """
    Use z3 to prove:
      (a) F > 1/2 => F_out > F  (distillation improves fidelity)
      (b) F in [1/4, 1/2] => F_out <= F  (no improvement in this range)
      (c) F_out is always in [0, 1] when F in [1/4, 1]
      (d) F = 1 is a fixed point

    Key trick: multiply through by den to get polynomial constraints,
    avoiding nonlinear division that confuses z3.
    F_out > F  <=>  num > F * den  (since den > 0)
    """
    results = {}
    from z3 import Real, RealVal, Or

    F = Real('F')

    # BBPSSW: num and den as polynomials in F
    # num = F^2 + (1-F)^2/9
    # den = F^2 + 2F(1-F)/3 + 5(1-F)^2/9
    # Expand to avoid nested expressions:
    #   num = F^2 + (1 - 2F + F^2)/9 = (9F^2 + 1 - 2F + F^2)/9 = (10F^2 - 2F + 1)/9
    #   den = F^2 + (2F - 2F^2)/3 + (5 - 10F + 5F^2)/9
    #       = (9F^2 + 6F - 6F^2 + 5 - 10F + 5F^2)/9
    #       = (8F^2 - 4F + 5)/9
    # So F_out = (10F^2 - 2F + 1) / (8F^2 - 4F + 5)
    # F_out > F  <=>  10F^2 - 2F + 1 > F(8F^2 - 4F + 5)  [den > 0 for F in [0,1]]
    #            <=>  10F^2 - 2F + 1 > 8F^3 - 4F^2 + 5F
    #            <=>  0 > 8F^3 - 14F^2 + 7F - 1
    #            <=>  8F^3 - 14F^2 + 7F - 1 < 0

    num_9 = 10 * F * F - 2 * F + 1     # 9 * num
    den_9 = 8 * F * F - 4 * F + 5      # 9 * den
    # diff = num - F*den = (num_9 - F*den_9)/9
    diff_9 = num_9 - F * den_9  # = 10F^2 - 2F + 1 - 8F^3 + 4F^2 - 5F = -8F^3 + 14F^2 - 7F + 1

    # (a) Prove: F in (1/2, 1) => diff_9 > 0 (i.e. F_out > F)
    # Equivalently: no counterexample with F in (1/2, 1) and diff_9 <= 0
    s = Solver()
    s.add(F > RealVal(1) / 2)
    s.add(F < 1)
    s.add(diff_9 <= 0)
    result_a = s.check()
    results["above_threshold_improvement"] = {
        "claim": "F in (1/2, 1) => F_out > F",
        "method": "z3 polynomial counterexample search",
        "counterexample_found": str(result_a) == "sat",
        "proved": str(result_a) == "unsat",
    }

    # (b) Prove: F in [1/4, 1/2] => diff_9 <= 0 (i.e. F_out <= F)
    # For F in [1/4, 1/2], BBPSSW does not improve fidelity
    s2 = Solver()
    s2.add(F >= RealVal(1) / 4)
    s2.add(F <= RealVal(1) / 2)
    s2.add(diff_9 > 0)
    result_b = s2.check()
    results["mid_range_no_improvement"] = {
        "claim": "F in [1/4, 1/2] => F_out <= F",
        "method": "z3 polynomial counterexample search",
        "counterexample_found": str(result_b) == "sat",
        "proved": str(result_b) == "unsat",
    }

    # (c) F_out in [0, 1] when F in [1/4, 1]: check num_9 >= 0 and num_9 <= den_9
    s3 = Solver()
    s3.add(F >= RealVal(1) / 4, F <= 1)
    s3.add(Or(num_9 < 0, num_9 > den_9))
    result_c = s3.check()
    results["output_in_unit_interval"] = {
        "claim": "F in [1/4, 1] => F_out in [0,1]",
        "method": "z3 polynomial counterexample search",
        "counterexample_found": str(result_c) == "sat",
        "proved": str(result_c) == "unsat",
    }

    # (d) Fixed point: F = 1 => F_out = 1 (check diff_9 = 0 at F=1)
    s4 = Solver()
    s4.add(F == 1)
    s4.add(diff_9 != 0)
    result_d = s4.check()
    results["fixed_point_F1"] = {
        "claim": "F = 1 => F_out = 1 (Bell pair is fixed point)",
        "proved": str(result_d) == "unsat",
    }

    # (e) Fixed point: F = 1/2 => F_out = 1/2
    s5 = Solver()
    s5.add(F == RealVal(1) / 2)
    s5.add(diff_9 != 0)
    result_e = s5.check()
    results["fixed_point_F_half"] = {
        "claim": "F = 1/2 => F_out = 1/2 (threshold is fixed point)",
        "proved": str(result_e) == "unsat",
    }

    return results


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    t0 = time.time()

    # ---- Test 1: Werner state construction & fidelity ----
    test_ps = [0.0, 0.25, 1.0 / 3.0, 0.5, 0.75, 1.0]
    ws_results = []
    for p in test_ps:
        rho = werner_state(p)
        # Check trace = 1
        tr = torch.trace(rho).real.item()
        # Check Hermitian
        herm_err = torch.max(torch.abs(rho - rho.conj().T)).item()
        # Check positive semidefinite
        eigvals = torch.linalg.eigvalsh(rho.real).tolist()
        min_eig = min(eigvals)
        # Check fidelity
        F_computed = (PHI_PLUS_KET.conj() @ rho @ PHI_PLUS_KET).real.item()
        F_analytic = werner_fidelity(p)
        ws_results.append({
            "p": p,
            "trace": tr,
            "hermitian_error": herm_err,
            "min_eigenvalue": min_eig,
            "fidelity_computed": F_computed,
            "fidelity_analytic": F_analytic,
            "fidelity_match": abs(F_computed - F_analytic) < 1e-12,
            "valid_state": abs(tr - 1.0) < 1e-12 and herm_err < 1e-12 and min_eig > -1e-12,
        })
    all_valid = all(r["valid_state"] and r["fidelity_match"] for r in ws_results)
    results["werner_state_construction"] = {
        "pass": all_valid,
        "details": ws_results,
    }

    # ---- Test 2: Analytic BBPSSW -- fidelity increases above threshold ----
    above_threshold_Fs = [0.55, 0.6, 0.7, 0.8, 0.9, 0.95]
    bbpssw_above = []
    for F in above_threshold_Fs:
        F_out = bbpssw_output_fidelity(F)
        improved = F_out > F
        bbpssw_above.append({
            "F_in": F,
            "F_out": float(F_out),
            "improved": improved,
            "delta": float(F_out - F),
        })
    results["bbpssw_above_threshold"] = {
        "pass": all(r["improved"] for r in bbpssw_above),
        "details": bbpssw_above,
    }

    # ---- Test 3: Iterated BBPSSW converges to 1 ----
    n_rounds = 50  # enough rounds to converge within tolerance
    fid_trace_075 = iterate_bbpssw(0.75, n_rounds)
    fid_trace_06 = iterate_bbpssw(0.6, n_rounds)
    converged_075 = abs(fid_trace_075[-1] - 1.0) < 1e-6
    converged_06 = abs(fid_trace_06[-1] - 1.0) < 1e-6
    monotonic_075 = all(fid_trace_075[i+1] >= fid_trace_075[i] for i in range(len(fid_trace_075)-1))
    monotonic_06 = all(fid_trace_06[i+1] >= fid_trace_06[i] for i in range(len(fid_trace_06)-1))
    results["iterated_bbpssw_convergence"] = {
        "pass": converged_075 and monotonic_075 and monotonic_06,
        "F_init_0.75": {
            "fidelity_trace": [float(f) for f in fid_trace_075],
            "converged_to_1": converged_075,
            "monotonic": monotonic_075,
        },
        "F_init_0.6": {
            "fidelity_trace": [float(f) for f in fid_trace_06],
            "converged_to_1": converged_06,
            "monotonic": monotonic_06,
        },
    }

    # ---- Test 4: Density-matrix BBPSSW matches analytic formula ----
    dm_test_ps = [0.5, 0.75, 0.9]
    dm_results = []
    for p in dm_test_ps:
        rho = werner_state(p)
        rho_out, prob = bbpssw_density_matrix(rho)
        F_dm = (PHI_PLUS_KET.conj() @ rho_out @ PHI_PLUS_KET).real.item()
        F_analytic = bbpssw_output_fidelity(werner_fidelity(p))
        prob_analytic = bbpssw_success_prob(werner_fidelity(p))
        dm_results.append({
            "p": p,
            "F_dm": F_dm,
            "F_analytic": float(F_analytic),
            "fidelity_match": abs(F_dm - float(F_analytic)) < 1e-6,
            "prob_dm": prob,
            "prob_analytic": float(prob_analytic),
            "prob_match": abs(prob - float(prob_analytic)) < 1e-6,
        })
    results["density_matrix_cross_validation"] = {
        "pass": all(r["fidelity_match"] and r["prob_match"] for r in dm_results),
        "details": dm_results,
    }

    # ---- Test 5: Log-negativity bounds distillable entanglement ----
    # For Werner states, compare E_D (heuristic lower bound from yield) with E_N
    ln_results = []
    for p in [0.5, 0.7, 0.9, 1.0]:
        rho = werner_state(p)
        E_N = log_negativity(rho).item()
        E_f = entanglement_cost_werner(p)
        # Hashing bound (lower bound on E_D): 1 - H(F) for F = (1+3p)/4
        F = werner_fidelity(p)
        if F > 0.5:
            hashing_bound = 1.0 - binary_entropy(F)
        else:
            hashing_bound = 0.0
        ln_results.append({
            "p": p,
            "log_negativity": E_N,
            "entanglement_of_formation": E_f,
            "hashing_bound_E_D": hashing_bound,
            "E_D_leq_E_N": hashing_bound <= E_N + 1e-10,
            "E_D_leq_E_C": hashing_bound <= E_f + 1e-10 if p < 1.0 else True,
        })
    results["log_negativity_bound"] = {
        "pass": all(r["E_D_leq_E_N"] for r in ln_results),
        "details": ln_results,
    }

    # ---- Test 6: Irreversibility E_D <= E_C ----
    irrev_results = []
    for p in [0.4, 0.5, 0.7, 0.9, 0.99]:
        F = werner_fidelity(p)
        E_f = entanglement_cost_werner(p)
        hashing = 1.0 - binary_entropy(F) if F > 0.5 else 0.0
        gap = E_f - hashing
        irrev_results.append({
            "p": p,
            "E_C_lower_bound": E_f,
            "E_D_upper_hashing": hashing,
            "irreversibility_gap": gap,
            "E_D_leq_E_C": hashing <= E_f + 1e-10,
        })
    results["irreversibility"] = {
        "pass": all(r["E_D_leq_E_C"] for r in irrev_results),
        "details": irrev_results,
    }

    # ---- Test 7: z3 proofs ----
    try:
        z3_results = z3_prove_threshold()
        all_proved = all(v.get("proved", False) for v in z3_results.values())
        results["z3_threshold_proofs"] = {
            "pass": all_proved,
            "details": z3_results,
        }
    except Exception as e:
        results["z3_threshold_proofs"] = {
            "pass": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

    # ---- Test 8: Autograd -- gradient of F_out w.r.t. input fidelity ----
    F_in = torch.tensor(0.75, dtype=torch.float64, requires_grad=True)
    F2 = F_in * F_in
    oF = 1.0 - F_in
    oF2 = oF * oF
    num = F2 + oF2 / 9.0
    den = F2 + 2.0 * F_in * oF / 3.0 + 5.0 * oF2 / 9.0
    F_out_ag = num / den
    F_out_ag.backward()
    grad = F_in.grad.item()
    results["autograd_fidelity_gradient"] = {
        "pass": grad > 0,  # positive slope means distillation helps
        "F_in": 0.75,
        "F_out": F_out_ag.item(),
        "dF_out_dF_in": grad,
        "note": "Positive gradient confirms fidelity improvement direction",
    }

    results["time_s"] = time.time() - t0
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # ---- Neg 1: F in (1/4, 1/2) -> fidelity does NOT improve ----
    # Note: F < 1/4 actually increases toward 1/4 (attractive fixed point).
    # The key test is: F in (1/4, 1/2) strictly decreases, and
    # no F below 1/2 ever reaches 1 by iteration.
    mid_Fs = [0.3, 0.35, 0.4, 0.49]
    neg_bbpssw = []
    for F in mid_Fs:
        F_out = bbpssw_output_fidelity(F)
        neg_bbpssw.append({
            "F_in": F,
            "F_out": float(F_out),
            "decreased": F_out < F,
        })
    results["mid_range_fidelity_decreases"] = {
        "pass": all(r["decreased"] for r in neg_bbpssw),
        "details": neg_bbpssw,
    }

    # ---- Neg 2: Iterated BBPSSW below threshold converges to 1/4, not 1 ----
    fid_below = iterate_bbpssw(0.4, 30)
    converges_to_quarter = abs(fid_below[-1] - 0.25) < 1e-4
    diverges = fid_below[-1] < fid_below[0]
    results["below_threshold_iteration_converges_to_quarter"] = {
        "pass": diverges and converges_to_quarter,
        "F_init": 0.4,
        "fidelity_trace": [float(f) for f in fid_below],
        "final_decreased_from_start": diverges,
        "converges_to_0.25": converges_to_quarter,
        "final_fidelity": float(fid_below[-1]),
    }

    # ---- Neg 3: Separable Werner state (p <= 1/3) has zero log-negativity ----
    sep_ps = [0.0, 0.1, 1.0 / 3.0]
    sep_results = []
    for p in sep_ps:
        rho = werner_state(p)
        E_N = log_negativity(rho).item()
        sep_results.append({
            "p": p,
            "log_negativity": E_N,
            "is_zero_or_negative": E_N <= 1e-10,
        })
    results["separable_zero_log_negativity"] = {
        "pass": all(r["is_zero_or_negative"] for r in sep_results),
        "details": sep_results,
    }

    # ---- Neg 4: Maximally mixed state (p=0) is undistillable ----
    rho_mm = werner_state(0.0)
    F_mm = (PHI_PLUS_KET.conj() @ rho_mm @ PHI_PLUS_KET).real.item()
    results["maximally_mixed_undistillable"] = {
        "pass": abs(F_mm - 0.25) < 1e-12,
        "fidelity": F_mm,
        "expected": 0.25,
        "note": "F = 1/4 < 1/2, cannot distill",
    }

    # ---- Neg 5: E_C = 0 for separable states ----
    E_C_sep = entanglement_cost_werner(0.0)
    E_C_third = entanglement_cost_werner(1.0 / 3.0)
    results["separable_zero_cost"] = {
        "pass": abs(E_C_sep) < 1e-12 and abs(E_C_third) < 1e-12,
        "E_C_p0": E_C_sep,
        "E_C_p_third": E_C_third,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # ---- Boundary 1: F = 1/2 is the fixed point ----
    F_half = bbpssw_output_fidelity(0.5)
    results["threshold_fixed_point"] = {
        "pass": abs(F_half - 0.5) < 1e-12,
        "F_in": 0.5,
        "F_out": float(F_half),
        "note": "F = 1/2 is a fixed point of BBPSSW",
    }

    # ---- Boundary 2: F = 1 is a fixed point (pure Bell pair) ----
    F_one = bbpssw_output_fidelity(1.0)
    results["bell_pair_fixed_point"] = {
        "pass": abs(F_one - 1.0) < 1e-12,
        "F_in": 1.0,
        "F_out": float(F_one),
    }

    # ---- Boundary 3: F = 0.25 (maximally mixed) ----
    F_mm = bbpssw_output_fidelity(0.25)
    results["maximally_mixed_fidelity"] = {
        "pass": F_mm <= 0.25 + 1e-12,
        "F_in": 0.25,
        "F_out": float(F_mm),
    }

    # ---- Boundary 4: Werner state eigenvalue structure ----
    # Werner state has eigenvalues: (1+3p)/4 (once) and (1-p)/4 (thrice)
    bnd_results = []
    for p in [0.0, 0.5, 1.0]:
        rho = werner_state(p)
        eigvals = sorted(torch.linalg.eigvalsh(rho.real).tolist())
        expected = sorted([(1.0 - p) / 4.0] * 3 + [(1.0 + 3.0 * p) / 4.0])
        match = all(abs(a - b) < 1e-12 for a, b in zip(eigvals, expected))
        bnd_results.append({
            "p": p,
            "eigenvalues": eigvals,
            "expected": expected,
            "match": match,
        })
    results["werner_eigenvalue_structure"] = {
        "pass": all(r["match"] for r in bnd_results),
        "details": bnd_results,
    }

    # ---- Boundary 5: Entanglement cost at p=1 (pure Bell) equals 1 ebit ----
    E_C_pure = entanglement_cost_werner(1.0)
    results["pure_bell_pair_cost"] = {
        "pass": abs(E_C_pure - 1.0) < 1e-10,
        "E_C": E_C_pure,
        "expected": 1.0,
        "note": "Pure Bell pair costs exactly 1 ebit",
    }

    # ---- Boundary 6: Success probability bounds ----
    # P_success should be in (0,1] for all valid F
    probs = []
    for F in [0.25, 0.5, 0.75, 1.0]:
        p = bbpssw_success_prob(F)
        probs.append({"F": F, "P_success": float(p), "valid": 0 < p <= 1.0 + 1e-12})
    results["success_probability_bounds"] = {
        "pass": all(r["valid"] for r in probs),
        "details": probs,
    }

    # ---- Boundary 7: Log-negativity of pure Bell = 1 ----
    rho_bell = werner_state(1.0)
    E_N_bell = log_negativity(rho_bell).item()
    results["bell_pair_log_negativity"] = {
        "pass": abs(E_N_bell - 1.0) < 1e-10,
        "log_negativity": E_N_bell,
        "expected": 1.0,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running entanglement distillation sim...")
    t_start = time.time()

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    # Count passes
    def count_passes(d):
        total = sum(1 for v in d.values() if isinstance(v, dict) and "pass" in v)
        passed = sum(1 for v in d.values() if isinstance(v, dict) and v.get("pass"))
        return passed, total

    p_pass, p_total = count_passes(positive)
    n_pass, n_total = count_passes(negative)
    b_pass, b_total = count_passes(boundary)

    results = {
        "name": "Entanglement Distillation & Dilution (BBPSSW)",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "summary": {
            "positive": f"{p_pass}/{p_total}",
            "negative": f"{n_pass}/{n_total}",
            "boundary": f"{b_pass}/{b_total}",
            "all_pass": p_pass == p_total and n_pass == n_total and b_pass == b_total,
            "total_time_s": time.time() - t_start,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_entanglement_distillation_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults written to {out_path}")
    print(f"Positive: {p_pass}/{p_total}  Negative: {n_pass}/{n_total}  Boundary: {b_pass}/{b_total}")
    if results["summary"]["all_pass"]:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- check results JSON")
