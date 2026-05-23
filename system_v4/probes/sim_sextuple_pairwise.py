#!/usr/bin/env python3
"""
sim_sextuple_pairwise.py

Coupling Program Step 1 (of 6-shell program): Shell-local + pairwise checks.

Q_WHGDCM = MI × H_weyl × H_hopf × H_gerbe × H_dirac × H_clifford

Tests (10):
  P1. H_weyl > 0 when active
  P2. H_hopf > 0 when active
  P3. H_gerbe > 0 when active
  P4. H_dirac > 0 when active
  P5. H_clifford > 0 when active
  P6. MI > 0 (MERA)
  P7-P10. Representative pairs Q=0 (missing >=4 factors)
  N1. z3 UNSAT: Q_6 != 0 with only 1 shell active (5 factors = 0)
  B1. All inactive -> Q = 0

Classification: classical_baseline
"""

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
classification = 'classical_baseline'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import math
import os
from itertools import combinations

import numpy as np

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from z3 import Real, Solver, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

# =====================================================================
# SHELL ENTROPY HELPERS
# =====================================================================

def h_weyl_active():
    return math.log(2)

def h_hopf_active():
    return math.log(2) / 2

def h_gerbe_active(seed=0):
    rng = np.random.default_rng(seed)
    grid = rng.choice([-1, 1], size=(4, 4))
    dd_count = int(np.sum(grid == 1))
    return math.log(1 + dd_count)

def h_dirac_active(seed=0):
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((4, 4))
    M = (A + A.T) / 2
    evals = sorted(np.linalg.eigvalsh(M))
    return abs(evals[-1] - evals[0]) if len(evals) >= 2 else 0.0

def h_clifford_active():
    """
    |offdiag_norm_after - offdiag_before| after exp(i*pi/4*XX) on |00><00|.
    XX = sigma_x ⊗ sigma_x, applied as exp(i*pi/4*XX).
    """
    rho = np.zeros((4, 4), dtype=complex)
    rho[0, 0] = 1.0
    sx = np.array([[0, 1], [1, 0]], dtype=complex)
    XX = np.kron(sx, sx)
    # exp(i*pi/4 * XX) = cos(pi/4)*I + i*sin(pi/4)*XX
    c = math.cos(math.pi / 4)
    s = math.sin(math.pi / 4)
    U = c * np.eye(4, dtype=complex) + 1j * s * XX
    rho_before = rho.copy()
    rho_after = U @ rho @ U.conj().T
    def offdiag_norm(r):
        tmp = r.copy()
        np.fill_diagonal(tmp, 0)
        return float(np.linalg.norm(tmp))
    return abs(offdiag_norm(rho_after) - offdiag_norm(rho_before))

def bell_mi(seed=0, eps=0.3):
    rng = np.random.default_rng(seed)
    psi = np.array([1, 0, 0, 1], dtype=float) / math.sqrt(2)
    rho = np.outer(psi, psi)
    for _ in range(3):
        qa, _ = np.linalg.qr(rng.standard_normal((2, 2)))
        qb, _ = np.linalg.qr(rng.standard_normal((2, 2)))
        U = np.kron(qa, qb)
        rho = U @ rho @ U.T
        rho = (1 - eps) * rho + eps * np.diag(np.diag(rho))
    rho_A = rho[:2, :2] + rho[2:, 2:]
    rho_B = rho[::2, ::2] + rho[1::2, 1::2]
    def svn(r):
        ev = np.linalg.eigvalsh(r)
        ev = ev[ev > 1e-15]
        return float(-np.sum(ev * np.log(ev)))
    return max(0.0, svn(rho_A) + svn(rho_B) - svn(rho))

def q_whgdcm(mi, h_weyl, h_hopf, h_gerbe, h_dirac, h_clifford):
    return mi * h_weyl * h_hopf * h_gerbe * h_dirac * h_clifford

# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    hw = h_weyl_active()
    hh = h_hopf_active()
    hg = h_gerbe_active(seed=0)
    hd = h_dirac_active(seed=0)
    hc = h_clifford_active()
    mi = bell_mi(seed=0)

    results["P1_h_weyl_positive"] = {"value": hw, "pass": hw > 0}
    results["P2_h_hopf_positive"] = {"value": hh, "pass": hh > 0}
    results["P3_h_gerbe_positive"] = {"value": hg, "pass": hg > 0}
    results["P4_h_dirac_positive"] = {"value": hd, "pass": hd > 0}
    results["P5_h_clifford_positive"] = {"value": hc, "pass": hc > 0}
    results["P6_mi_positive"] = {"value": mi, "pass": mi > 0}

    # All C(6,2)=15 pairwise: Q_6 = 0 (missing >=4 factors)
    shells = ["weyl", "hopf", "gerbe", "dirac", "clifford", "mera"]
    vals = {"weyl": hw, "hopf": hh, "gerbe": hg, "dirac": hd, "clifford": hc, "mera": mi}

    pair_pass = True
    pair_details = {}
    for a, b in combinations(shells, 2):
        active_mi = vals["mera"] if "mera" in (a, b) else 0.0
        active_hw = vals["weyl"] if "weyl" in (a, b) else 0.0
        active_hh = vals["hopf"] if "hopf" in (a, b) else 0.0
        active_hg = vals["gerbe"] if "gerbe" in (a, b) else 0.0
        active_hd = vals["dirac"] if "dirac" in (a, b) else 0.0
        active_hc = vals["clifford"] if "clifford" in (a, b) else 0.0
        q = q_whgdcm(active_mi, active_hw, active_hh, active_hg, active_hd, active_hc)
        ok = abs(q) < 1e-12
        pair_details[f"pair_{a}_{b}"] = {"Q": q, "pass": ok}
        if not ok:
            pair_pass = False

    results["P7_all_pairs_Q_zero"] = {"pairs": pair_details, "pass": pair_pass}

    results["all_pass"] = all(
        v.get("pass", False) for k, v in results.items()
        if isinstance(v, dict) and "pass" in v and k != "all_pass"
    )
    return results

# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    if not TOOL_MANIFEST["z3"]["tried"]:
        results["N1_z3_single_shell_Q_nonzero_UNSAT"] = {"pass": False, "note": "z3 not available"}
        results["all_pass"] = False
        return results

    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "N1: UNSAT proof that Q_6 != 0 with any single shell active (5 factors = 0)"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

    from z3 import Real, Solver, unsat, And

    s = Solver()
    MI = Real('MI'); Hw = Real('Hw'); Hh = Real('Hh'); Hg = Real('Hg'); Hd = Real('Hd'); Hc = Real('Hc')
    Q = Real('Q')
    # Only weyl active: all others = 0
    s.add(MI == 0, Hh == 0, Hg == 0, Hd == 0, Hc == 0)
    s.add(Q == MI * Hw * Hh * Hg * Hd * Hc)
    s.add(Q != 0)
    r = s.check()
    n1_pass = (r == unsat)

    results["N1_z3_single_shell_Q_nonzero_UNSAT"] = {
        "z3_result": str(r), "expected": "unsat", "pass": n1_pass,
        "note": "Q_6 with only 1 shell active must be 0 (5 factors absent)"
    }

    results["all_pass"] = all(
        v.get("pass", False) for k, v in results.items()
        if isinstance(v, dict) and "pass" in v and k != "all_pass"
    )
    return results

# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    q = q_whgdcm(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    results["B1_all_inactive_Q_zero"] = {"Q": q, "pass": abs(q) < 1e-12}
    results["all_pass"] = all(
        v.get("pass", False) for k, v in results.items()
        if isinstance(v, dict) and "pass" in v and k != "all_pass"
    )
    return results

# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    overall = pos.get("all_pass", False) and neg.get("all_pass", False) and bnd.get("all_pass", False)

    out = {
        "name": "sim_sextuple_pairwise",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": overall,
    }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_sextuple_pairwise_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"all_pass: {overall}  -> {out_path}")
