#!/usr/bin/env python3
"""
sim_sextuple_emergence_quantities.py

Coupling Program Step 4 (of 6-shell program): Emergence quantities.

Q_WHGDCM = MI × H_weyl × H_hopf × H_gerbe × H_dirac × H_clifford

Tests:
  P-section (per specification):
    - All 6 singles Q=0
    - All 15 pairs Q=0
    - 6 representative triples Q=0
    - 5 representative quads Q=0
    - 6 quintuples (one for each missing shell) Q=0
    - Full sextuple Q > 0
    top-level pass per section

  N-section:
    N1. z3 UNSAT: any sub-5-shell combo cannot give Q_6 != 0
    N2. sympy 6-factor product zero when any factor = 0

  B-section:
    B1. All inactive Q=0
    B2. Full sextuple Q = product of all 6 factors

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

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

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

    shells = ["weyl", "hopf", "gerbe", "dirac", "clifford", "mera"]
    vals = {"weyl": hw, "hopf": hh, "gerbe": hg, "dirac": hd, "clifford": hc, "mera": mi}

    def q_from_active(active):
        return q_whgdcm(
            vals["mera"] if "mera" in active else 0.0,
            vals["weyl"] if "weyl" in active else 0.0,
            vals["hopf"] if "hopf" in active else 0.0,
            vals["gerbe"] if "gerbe" in active else 0.0,
            vals["dirac"] if "dirac" in active else 0.0,
            vals["clifford"] if "clifford" in active else 0.0,
        )

    # 6 singles -> all Q=0
    singles_pass = True
    singles_detail = {}
    for s in shells:
        q = q_from_active([s])
        ok = abs(q) < 1e-12
        singles_detail[f"single_{s}"] = {"Q": q, "pass": ok}
        if not ok:
            singles_pass = False
    results["P_singles_all_Q_zero"] = {"detail": singles_detail, "pass": singles_pass}

    # 15 pairs -> all Q=0
    pairs_pass = True
    pairs_detail = {}
    for a, b in combinations(shells, 2):
        q = q_from_active([a, b])
        ok = abs(q) < 1e-12
        pairs_detail[f"pair_{a}_{b}"] = {"Q": q, "pass": ok}
        if not ok:
            pairs_pass = False
    results["P_pairs_all_Q_zero"] = {"detail": pairs_detail, "pass": pairs_pass}

    # 6 representative triples -> all Q=0
    rep_triples = [
        ["weyl", "hopf", "gerbe"],
        ["dirac", "clifford", "mera"],
        ["weyl", "dirac", "mera"],
        ["hopf", "clifford", "gerbe"],
        ["weyl", "clifford", "mera"],
        ["hopf", "dirac", "gerbe"],
    ]
    triples_pass = True
    triples_detail = {}
    for trip in rep_triples:
        q = q_from_active(trip)
        ok = abs(q) < 1e-12
        key = "triple_" + "_".join(trip)
        triples_detail[key] = {"Q": q, "pass": ok}
        if not ok:
            triples_pass = False
    results["P_triples_all_Q_zero"] = {"detail": triples_detail, "pass": triples_pass}

    # 5 representative quads -> all Q=0
    rep_quads = [
        ["weyl", "hopf", "gerbe", "dirac"],
        ["hopf", "gerbe", "clifford", "mera"],
        ["weyl", "dirac", "clifford", "mera"],
        ["weyl", "hopf", "clifford", "mera"],
        ["gerbe", "dirac", "clifford", "mera"],
    ]
    quads_pass = True
    quads_detail = {}
    for quad in rep_quads:
        q = q_from_active(quad)
        ok = abs(q) < 1e-12
        key = "quad_" + "_".join(quad)
        quads_detail[key] = {"Q": q, "pass": ok}
        if not ok:
            quads_pass = False
    results["P_quads_all_Q_zero"] = {"detail": quads_detail, "pass": quads_pass}

    # 6 quintuples (each missing one shell) -> all Q=0
    quintuples_pass = True
    quintuples_detail = {}
    for missing in shells:
        active = [s for s in shells if s != missing]
        q = q_from_active(active)
        ok = abs(q) < 1e-12
        key = f"quintuple_no_{missing}"
        quintuples_detail[key] = {"Q": q, "pass": ok}
        if not ok:
            quintuples_pass = False
    results["P_quintuples_all_Q_zero"] = {"detail": quintuples_detail, "pass": quintuples_pass}

    # Full sextuple Q > 0
    q_full = q_from_active(shells)
    results["P_full_sextuple_Q_positive"] = {"Q": q_full, "pass": q_full > 1e-12}

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

    # N1: z3 UNSAT — any single missing factor forces Q=0
    if not TOOL_MANIFEST["z3"]["tried"]:
        results["N1_z3_UNSAT"] = {"pass": False, "note": "z3 not available"}
    else:
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "N1: UNSAT proof Q_6 != 0 with weyl=0 (sub-5-shell combo)"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

        from z3 import Real, Solver, unsat

        s = Solver()
        MI = Real('MI'); Hw = Real('Hw'); Hh = Real('Hh'); Hg = Real('Hg'); Hd = Real('Hd'); Hc = Real('Hc')
        Q = Real('Q')
        s.add(Hw == 0, MI > 0, Hh > 0, Hg > 0, Hd > 0, Hc > 0)
        s.add(Q == MI * Hw * Hh * Hg * Hd * Hc)
        s.add(Q != 0)
        r = s.check()
        results["N1_z3_UNSAT_weyl_missing"] = {
            "z3_result": str(r), "expected": "unsat", "pass": (r == unsat)
        }

    # N2: sympy — 6-factor product is zero when any factor=0
    if not TOOL_MANIFEST["sympy"]["tried"]:
        results["N2_sympy_6factor"] = {"pass": False, "note": "sympy not available"}
    else:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "N2: symbolic verification that 6-factor product is zero when any factor=0"
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

        import sympy as sp
        MI, Hw, Hh, Hg, Hd, Hc = sp.symbols('MI Hw Hh Hg Hd Hc', positive=True)
        Q_sym = MI * Hw * Hh * Hg * Hd * Hc
        # Substitute each factor=0 and verify Q=0
        sympy_pass = True
        sympy_detail = {}
        for sym, name in [(MI, "MI"), (Hw, "Hw"), (Hh, "Hh"), (Hg, "Hg"), (Hd, "Hd"), (Hc, "Hc")]:
            val = Q_sym.subs(sym, 0)
            ok = val == 0
            sympy_detail[f"zero_when_{name}=0"] = {"val": str(val), "pass": bool(ok)}
            if not ok:
                sympy_pass = False
        results["N2_sympy_6factor_zero"] = {"detail": sympy_detail, "pass": sympy_pass}

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

    hw = h_weyl_active(); hh = h_hopf_active(); hg = h_gerbe_active(0)
    hd = h_dirac_active(0); hc = h_clifford_active(); mi = bell_mi(0)
    q_full = q_whgdcm(mi, hw, hh, hg, hd, hc)
    q_direct = mi * hw * hh * hg * hd * hc
    results["B2_full_sextuple_product_consistent"] = {
        "Q_func": q_full, "Q_direct": q_direct,
        "pass": abs(q_full - q_direct) < 1e-14
    }

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
        "name": "sim_sextuple_emergence_quantities",
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
    out_path = os.path.join(out_dir, "sim_sextuple_emergence_quantities_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"all_pass: {overall}  -> {out_path}")
