#!/usr/bin/env python3
"""
sim_sextuple_coexistence.py

Coupling Program Step 2 (of 6-shell program): Coexistence — triples/quads/quintuples all Q=0;
full sextuple Q!=0.

Q_WHGDCM = MI × H_weyl × H_hopf × H_gerbe × H_dirac × H_clifford

Tests (10):
  P1. Triple (weyl,hopf,gerbe) -> Q=0
  P2. Triple (dirac,clifford,mera) -> Q=0
  P3. Quad (weyl,hopf,gerbe,dirac) -> Q=0
  P4. Quad (hopf,gerbe,clifford,mera) -> Q=0
  P5. Quintuple (weyl,hopf,gerbe,dirac,mera) [no clifford] -> Q=0
  P6. Quintuple (weyl,hopf,gerbe,clifford,mera) [no dirac] -> Q=0
  P7. Full sextuple Q > 0
  N1. z3 UNSAT: 5-shell Q_6 != 0 (missing 1 factor -> product=0)
  B1. All inactive -> Q=0
  B2. Full sextuple with MI=0 -> Q=0

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

# =====================================================================
# HELPERS (same as pairwise)
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
    rho = np.zeros((4, 4), dtype=complex)
    rho[0, 0] = 1.0
    sx = np.array([[0, 1], [1, 0]], dtype=complex)
    XX = np.kron(sx, sx)
    c = math.cos(math.pi / 4)
    s = math.sin(math.pi / 4)
    U = c * np.eye(4, dtype=complex) + 1j * s * XX
    rho_after = U @ rho @ U.conj().T
    def offdiag_norm(r):
        tmp = r.copy()
        np.fill_diagonal(tmp, 0)
        return float(np.linalg.norm(tmp))
    return abs(offdiag_norm(rho_after) - offdiag_norm(rho))

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

def q_whgdcm(mi, hw, hh, hg, hd, hc):
    return mi * hw * hh * hg * hd * hc

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

    # Helper: build Q from active set
    def q_from_active(active):
        return q_whgdcm(
            mi if "mera" in active else 0.0,
            hw if "weyl" in active else 0.0,
            hh if "hopf" in active else 0.0,
            hg if "gerbe" in active else 0.0,
            hd if "dirac" in active else 0.0,
            hc if "clifford" in active else 0.0,
        )

    # Triples (missing 3 factors -> Q=0)
    q1 = q_from_active(["weyl", "hopf", "gerbe"])
    results["P1_triple_WHG_Q_zero"] = {"Q": q1, "pass": abs(q1) < 1e-12}

    q2 = q_from_active(["dirac", "clifford", "mera"])
    results["P2_triple_DCM_Q_zero"] = {"Q": q2, "pass": abs(q2) < 1e-12}

    # Quads (missing 2 factors -> Q=0)
    q3 = q_from_active(["weyl", "hopf", "gerbe", "dirac"])
    results["P3_quad_WHGD_Q_zero"] = {"Q": q3, "pass": abs(q3) < 1e-12}

    q4 = q_from_active(["hopf", "gerbe", "clifford", "mera"])
    results["P4_quad_HGCM_Q_zero"] = {"Q": q4, "pass": abs(q4) < 1e-12}

    # Quintuples (missing 1 factor -> Q=0)
    q5 = q_from_active(["weyl", "hopf", "gerbe", "dirac", "mera"])
    results["P5_quintuple_no_clifford_Q_zero"] = {"Q": q5, "pass": abs(q5) < 1e-12}

    q6 = q_from_active(["weyl", "hopf", "gerbe", "clifford", "mera"])
    results["P6_quintuple_no_dirac_Q_zero"] = {"Q": q6, "pass": abs(q6) < 1e-12}

    # Full sextuple Q > 0
    q_full = q_from_active(["weyl", "hopf", "gerbe", "dirac", "clifford", "mera"])
    results["P7_full_sextuple_Q_positive"] = {"Q": q_full, "pass": q_full > 1e-12}

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
        results["N1_z3_5shell_Q_nonzero_UNSAT"] = {"pass": False, "note": "z3 not available"}
        results["all_pass"] = False
        return results

    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "N1: UNSAT proof that Q_6 != 0 with any 5 shells (missing 1 factor -> product=0)"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

    from z3 import Real, Solver, unsat

    s = Solver()
    MI = Real('MI'); Hw = Real('Hw'); Hh = Real('Hh'); Hg = Real('Hg'); Hd = Real('Hd'); Hc = Real('Hc')
    Q = Real('Q')
    # Clifford absent (Hc=0), all others positive
    s.add(Hc == 0, MI > 0, Hw > 0, Hh > 0, Hg > 0, Hd > 0)
    s.add(Q == MI * Hw * Hh * Hg * Hd * Hc)
    s.add(Q != 0)
    r = s.check()
    n1_pass = (r == unsat)

    results["N1_z3_5shell_Q_nonzero_UNSAT"] = {
        "z3_result": str(r), "expected": "unsat", "pass": n1_pass,
        "note": "Q_6 with clifford absent (Hc=0) must be 0"
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

    # Full sextuple with MI=0 -> Q=0
    hw = h_weyl_active(); hh = h_hopf_active(); hg = h_gerbe_active(0)
    hd = h_dirac_active(0); hc = h_clifford_active()
    q2 = q_whgdcm(0.0, hw, hh, hg, hd, hc)
    results["B2_sextuple_mi_zero_Q_zero"] = {"Q": q2, "pass": abs(q2) < 1e-12}

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
        "name": "sim_sextuple_coexistence",
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
    out_path = os.path.join(out_dir, "sim_sextuple_coexistence_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"all_pass: {overall}  -> {out_path}")
