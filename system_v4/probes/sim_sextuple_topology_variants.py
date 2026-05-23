#!/usr/bin/env python3
"""
sim_sextuple_topology_variants.py

Coupling Program Step 3 (of 6-shell program): Topology variants.
Full sextuple Q!=0 in T1/T2/T3; sub-quintuples Q=0.

Q_WHGDCM = MI × H_weyl × H_hopf × H_gerbe × H_dirac × H_clifford

Topology variants applied to MI (Bell state decoherence topology):
  T1: 3 local-unitary layers, eps=0.3 (baseline)
  T2: 3 dephasing layers, eps=0.5 (stronger decoherence)
  T3: 1 layer, eps=0.1 (shallow decoherence)

Tests (8):
  P1. T1 full sextuple Q > 0
  P2. T2 full sextuple Q > 0
  P3. T3 full sextuple Q > 0
  P4. T1 quintuple (no clifford) Q = 0
  P5. T2 quintuple (no weyl) Q = 0
  N1. z3 UNSAT: sextuple with H_hopf=0 forces Q=0
  B1. T1 all inactive Q=0
  B2. T3 MI > 0

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
# HELPERS
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

def bell_mi_topology(seed=0, n_layers=3, eps=0.3):
    rng = np.random.default_rng(seed)
    psi = np.array([1, 0, 0, 1], dtype=float) / math.sqrt(2)
    rho = np.outer(psi, psi)
    for _ in range(n_layers):
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

    # T1: baseline
    mi_t1 = bell_mi_topology(seed=0, n_layers=3, eps=0.3)
    q_t1 = q_whgdcm(mi_t1, hw, hh, hg, hd, hc)
    results["P1_T1_full_sextuple_Q_positive"] = {"Q": q_t1, "MI": mi_t1, "pass": q_t1 > 1e-12}

    # T2: stronger decoherence
    mi_t2 = bell_mi_topology(seed=0, n_layers=3, eps=0.5)
    q_t2 = q_whgdcm(mi_t2, hw, hh, hg, hd, hc)
    results["P2_T2_full_sextuple_Q_positive"] = {"Q": q_t2, "MI": mi_t2, "pass": q_t2 > 1e-12}

    # T3: shallow decoherence
    mi_t3 = bell_mi_topology(seed=0, n_layers=1, eps=0.1)
    q_t3 = q_whgdcm(mi_t3, hw, hh, hg, hd, hc)
    results["P3_T3_full_sextuple_Q_positive"] = {"Q": q_t3, "MI": mi_t3, "pass": q_t3 > 1e-12}

    # T1 quintuple (no clifford) -> Q=0
    q_no_clif = q_whgdcm(mi_t1, hw, hh, hg, hd, 0.0)
    results["P4_T1_quintuple_no_clifford_Q_zero"] = {"Q": q_no_clif, "pass": abs(q_no_clif) < 1e-12}

    # T2 quintuple (no weyl) -> Q=0
    q_no_weyl = q_whgdcm(mi_t2, 0.0, hh, hg, hd, hc)
    results["P5_T2_quintuple_no_weyl_Q_zero"] = {"Q": q_no_weyl, "pass": abs(q_no_weyl) < 1e-12}

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
        results["N1_z3_hopf_zero_UNSAT"] = {"pass": False, "note": "z3 not available"}
        results["all_pass"] = False
        return results

    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "N1: UNSAT proof Q_6 != 0 impossible when H_hopf = 0"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

    from z3 import Real, Solver, unsat

    s = Solver()
    MI = Real('MI'); Hw = Real('Hw'); Hh = Real('Hh'); Hg = Real('Hg'); Hd = Real('Hd'); Hc = Real('Hc')
    Q = Real('Q')
    s.add(Hh == 0, MI > 0, Hw > 0, Hg > 0, Hd > 0, Hc > 0)
    s.add(Q == MI * Hw * Hh * Hg * Hd * Hc)
    s.add(Q != 0)
    r = s.check()
    n1_pass = (r == unsat)

    results["N1_z3_hopf_zero_Q_nonzero_UNSAT"] = {
        "z3_result": str(r), "expected": "unsat", "pass": n1_pass,
        "note": "Q_6 with H_hopf=0 must be 0 regardless of topology variant"
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
    results["B1_T1_all_inactive_Q_zero"] = {"Q": q, "pass": abs(q) < 1e-12}

    mi_t3 = bell_mi_topology(seed=0, n_layers=1, eps=0.1)
    results["B2_T3_MI_positive"] = {"MI": mi_t3, "pass": mi_t3 > 0}

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
        "name": "sim_sextuple_topology_variants",
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
    out_path = os.path.join(out_dir, "sim_sextuple_topology_variants_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"all_pass: {overall}  -> {out_path}")
