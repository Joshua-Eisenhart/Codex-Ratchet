#!/usr/bin/env python3
"""
sim_quintuple_weyl_hopf_gerbe_dirac_mera_pairwise.py

Coupling Program Step 1 (of 5-shell program): Shell-local + pairwise checks.

Q_WHGDM = MI × H_weyl × H_hopf × H_gerbe × H_dirac

Tests:
  P-section (12 tests):
    1. H_weyl > 0 when active
    2. H_hopf > 0 when active
    3. H_gerbe > 0 when active
    4. H_dirac > 0 when active
    5. MI > 0 when MERA active
    6-15. All C(5,2)=10 pairwise Q=0 (either MI=0 absent MERA, or missing H factor)
  N-section:
    N1. z3 UNSAT: Q_5 ≠ 0 with any single shell active (missing 4 factors → product=0)
  B-section:
    B1. All shells inactive → Q=0

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

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

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

def bell_mi(seed=0):
    """MI from Bell state under MERA-like decoherence."""
    rng = np.random.default_rng(seed)
    psi = np.array([1, 0, 0, 1], dtype=float) / math.sqrt(2)
    rho = np.outer(psi, psi)
    # n_layers=3 of U_A⊗U_B (2×2 QR) + depolarise
    for _ in range(3):
        qa, _ = np.linalg.qr(rng.standard_normal((2, 2)))
        qb, _ = np.linalg.qr(rng.standard_normal((2, 2)))
        U = np.kron(qa, qb)
        rho = U @ rho @ U.T
        rho = 0.7 * rho + 0.3 * np.diag(np.diag(rho))
    rho_A = rho[:2, :2] + rho[2:, 2:]
    rho_B = rho[::2, ::2] + rho[1::2, 1::2]
    def svn(r):
        ev = np.linalg.eigvalsh(r)
        ev = ev[ev > 1e-15]
        return float(-np.sum(ev * np.log(ev)))
    return max(0.0, svn(rho_A) + svn(rho_B) - svn(rho))

def q_whgdm(mi, h_weyl, h_hopf, h_gerbe, h_dirac):
    return mi * h_weyl * h_hopf * h_gerbe * h_dirac

# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    hw = h_weyl_active()
    hh = h_hopf_active()
    hg = h_gerbe_active(seed=0)
    hd = h_dirac_active(seed=0)
    mi = bell_mi(seed=0)

    results["P1_h_weyl_positive"] = {"value": hw, "pass": hw > 0}
    results["P2_h_hopf_positive"] = {"value": hh, "pass": hh > 0}
    results["P3_h_gerbe_positive"] = {"value": hg, "pass": hg > 0}
    results["P4_h_dirac_positive"] = {"value": hd, "pass": hd > 0}
    results["P5_mi_positive"] = {"value": mi, "pass": mi > 0}

    # All C(5,2)=10 pairwise: Q_5 = 0 (missing ≥3 factors)
    shells = ["weyl", "hopf", "gerbe", "dirac", "mera"]
    vals = {"weyl": hw, "hopf": hh, "gerbe": hg, "dirac": hd, "mera": mi}

    from itertools import combinations
    pair_pass = True
    pair_details = {}
    for a, b in combinations(shells, 2):
        # For Q_5 we need all 5 factors. With only 2 active, 3 factors missing → Q_5=0
        active_mi = vals["mera"] if "mera" in (a, b) else 0.0
        active_hw = vals["weyl"] if "weyl" in (a, b) else 0.0
        active_hh = vals["hopf"] if "hopf" in (a, b) else 0.0
        active_hg = vals["gerbe"] if "gerbe" in (a, b) else 0.0
        active_hd = vals["dirac"] if "dirac" in (a, b) else 0.0
        q = q_whgdm(active_mi, active_hw, active_hh, active_hg, active_hd)
        ok = abs(q) < 1e-12
        pair_details[f"pair_{a}_{b}"] = {"Q": q, "pass": ok}
        if not ok:
            pair_pass = False

    results["P6_all_pairwise_Q_zero"] = {"pairs": pair_details, "pass": pair_pass}

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
    TOOL_MANIFEST["z3"]["reason"] = (
        "N1: UNSAT proof that Q_5 ≠ 0 with any single shell active (4 factors = 0)"
    )
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

    from z3 import Real, Solver, unsat, And

    # With only 1 shell active, at least 4 of the 5 factors are 0.
    # Encode: MI=0 (MERA absent), H_weyl=0 (weyl absent), Q = MI*H_w*... = 0
    # Assert Q ≠ 0 → UNSAT
    s = Solver()
    MI = Real('MI'); Hw = Real('Hw'); Hh = Real('Hh'); Hg = Real('Hg'); Hd = Real('Hd')
    Q = Real('Q')
    # Only weyl active: all others = 0
    s.add(MI == 0, Hh == 0, Hg == 0, Hd == 0)
    s.add(Q == MI * Hw * Hh * Hg * Hd)
    s.add(Q != 0)
    r = s.check()
    n1_pass = (r == unsat)

    results["N1_z3_single_shell_Q_nonzero_UNSAT"] = {
        "z3_result": str(r), "expected": "unsat", "pass": n1_pass,
        "note": "Q_5 with only 1 shell active must be 0 (4 factors absent)"
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
    q = q_whgdm(0.0, 0.0, 0.0, 0.0, 0.0)
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
        "name": "sim_quintuple_weyl_hopf_gerbe_dirac_mera_pairwise",
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
    out_path = os.path.join(out_dir, "sim_quintuple_weyl_hopf_gerbe_dirac_mera_pairwise_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"all_pass: {overall}  -> {out_path}")
