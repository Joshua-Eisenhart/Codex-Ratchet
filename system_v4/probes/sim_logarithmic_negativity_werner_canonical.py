#!/usr/bin/env python3
"""
Lane C canonical: Logarithmic Negativity on Werner state.

E_N(rho) = log2(||rho^{T_B}||_1). For Werner rho(p) = p |Phi+><Phi+| + (1-p) I/4:
  partial-transpose eigenvalues = {(1+p)/4 x3, (1-3p)/4 x1}.
  ||rho^{T_B}||_1 = (3(1+p) + |1-3p|)/4.
  p > 1/3  =>  E_N = log2((1+3p)/2) > 0.
  p = 1.0  =>  E_N = log2(2) = 1 bit. Classical separable witness = 0.

Load-bearing tool: pytorch (partial transpose via reshape/einsum + torch.linalg
eigvalues for trace-norm computation; also autograd-compatible).
"""

import json
import os
import math
import numpy as np
classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

LN2 = math.log(2.0)


def phi_plus():
    psi = np.array([1, 0, 0, 1], dtype=np.complex128) / math.sqrt(2)
    return np.outer(psi, psi.conj())


def werner(p):
    return p * phi_plus() + (1 - p) * np.eye(4, dtype=np.complex128) / 4


def partial_transpose_B_torch(rho_t):
    """PT on subsystem B: (T_B rho)_{i j', k l'} = rho_{i l', k j'} for 2x2."""
    r = rho_t.reshape(2, 2, 2, 2)
    rt = r.permute(0, 3, 2, 1)  # swap last index of bra/ket on B
    return rt.reshape(4, 4)


def log_negativity_torch(rho_t):
    """E_N = log2(sum |eigenvalues of rho^{T_B}|). Load-bearing torch op."""
    pt = partial_transpose_B_torch(rho_t)
    # Hermitian PT matrix
    evals = torch.linalg.eigvalsh(pt).real
    trace_norm = torch.sum(torch.abs(evals))
    return torch.log2(trace_norm)


def werner_analytic_EN(p):
    """Analytic: ||rho^{T_B}||_1 = (3(1+p) + |1-3p|)/4, E_N = log2 of that."""
    return math.log2((3 * (1 + p) + abs(1 - 3 * p)) / 4)


def run_positive_tests():
    results = {}
    # P1: Werner E_N matches analytic across p
    p_grid = [0.0, 0.25, 0.34, 0.5, 0.75, 1.0]
    p1 = {}
    for p in p_grid:
        rho_t = torch.tensor(werner(p), dtype=torch.complex128)
        en_t = float(log_negativity_torch(rho_t).item())
        en_a = werner_analytic_EN(p)
        p1[f"p={p}"] = {"torch": en_t, "analytic": en_a,
                         "diff": abs(en_t - en_a), "pass": abs(en_t - en_a) < 1e-4}
    results["P1_werner_analytic_match"] = p1

    # P2: E_N(|Phi+>) = 1 bit
    rho_t = torch.tensor(phi_plus(), dtype=torch.complex128)
    en = float(log_negativity_torch(rho_t).item())
    results["P2_phi_plus_one_bit"] = {
        "E_N_bits": en, "expected": 1.0, "pass": abs(en - 1.0) < 1e-4,
    }

    # P3: E_N > 0 iff p > 1/3
    p3 = {}
    for p in [0.2, 0.34, 0.5, 1.0]:
        rho_t = torch.tensor(werner(p), dtype=torch.complex128)
        en = float(log_negativity_torch(rho_t).item())
        expected_positive = p > 1 / 3
        actual_positive = en > 1e-6
        p3[f"p={p}"] = {"E_N": en, "expected_positive": expected_positive,
                         "actual_positive": actual_positive,
                         "pass": expected_positive == actual_positive}
    results["P3_entanglement_threshold"] = p3

    # P4: quantum/classical gap at p=1
    en_q = float(log_negativity_torch(torch.tensor(werner(1.0),
                                                    dtype=torch.complex128)).item())
    classical_witness = 0.0
    gap = en_q - classical_witness
    results["P4_quantum_classical_gap"] = {
        "gap_bits": gap, "expected": 1.0, "pass": abs(gap - 1.0) < 1e-4,
    }
    return results


def run_negative_tests():
    results = {}
    # N1: Separable states have E_N = 0
    def product_rho(a, b):
        I = np.eye(2, dtype=np.complex128)
        sx = np.array([[0, 1], [1, 0]], dtype=np.complex128)
        sy = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
        sz = np.array([[1, 0], [0, -1]], dtype=np.complex128)
        P = [sx, sy, sz]
        ra = I / 2 + sum(a[i] * P[i] / 2 for i in range(3))
        rb = I / 2 + sum(b[i] * P[i] / 2 for i in range(3))
        return np.kron(ra, rb)

    cases = {
        "|00>": ([0, 0, 1], [0, 0, 1]),
        "|++>": ([1, 0, 0], [1, 0, 0]),
        "mixed": ([0, 0, 0.3], [0, 0, -0.4]),
    }
    n1 = {}
    for name, (a, b) in cases.items():
        rho_t = torch.tensor(product_rho(a, b), dtype=torch.complex128)
        en = float(log_negativity_torch(rho_t).item())
        n1[name] = {"E_N": en, "pass": en < 1e-4}
    results["N1_separable_zero_EN"] = n1

    # N2: Werner at p<=1/3 -> E_N = 0
    n2 = {}
    for p in [0.0, 0.1, 0.333]:
        rho_t = torch.tensor(werner(p), dtype=torch.complex128)
        en = float(log_negativity_torch(rho_t).item())
        n2[f"p={p}"] = {"E_N": en, "pass": en < 1e-3}
    results["N2_werner_below_threshold_zero"] = n2
    return results


def run_boundary_tests():
    results = {}
    # B1: Exactly at p=1/3 -> E_N = 0
    rho_t = torch.tensor(werner(1 / 3), dtype=torch.complex128)
    en = float(log_negativity_torch(rho_t).item())
    results["B1_threshold_p_one_third"] = {"E_N": en, "pass": abs(en) < 1e-4}

    # B2: Maximally mixed -> E_N = 0
    rho_t = torch.eye(4, dtype=torch.complex128) / 4
    en = float(log_negativity_torch(rho_t).item())
    results["B2_max_mixed_zero"] = {"E_N": en, "pass": abs(en) < 1e-6}

    # B3: E_N monotone non-decreasing in p for Werner
    vals = []
    for p in np.linspace(0, 1, 11):
        rho_t = torch.tensor(werner(float(p)), dtype=torch.complex128)
        vals.append(float(log_negativity_torch(rho_t).item()))
    monotone = all(vals[i] <= vals[i + 1] + 1e-6 for i in range(len(vals) - 1))
    results["B3_werner_monotone"] = {"values": vals, "pass": monotone}
    return results


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Load-bearing: partial transpose via torch.reshape/permute and trace-norm "
        "via torch.linalg.eigvalsh; all E_N values are torch tensor outputs."
    )

    def count_passes(d):
        p, t = 0, 0
        if isinstance(d, dict):
            if "pass" in d:
                t += 1
                if d["pass"]:
                    p += 1
            for v in d.values():
                a, b = count_passes(v)
                p += a; t += b
        return p, t

    tp, tt = count_passes({"positive": positive, "negative": negative, "boundary": boundary})

    results = {
        "name": "logarithmic_negativity_werner_canonical",
        "description": "Lane C log-negativity: Werner p>1/3 gives E_N>0; Phi+ = 1 bit gap",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive, "negative": negative, "boundary": boundary,
        "classification": "canonical",
        "quantum_classical_gap_bits": positive["P4_quantum_classical_gap"]["gap_bits"],
        "summary": {"total_tests": tt, "total_pass": tp, "all_pass": tp == tt},
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "logarithmic_negativity_werner_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results: {tp}/{tt} pass -> {out_path}")
    if tp != tt:
        raise SystemExit(1)
