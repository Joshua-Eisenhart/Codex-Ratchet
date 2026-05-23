#!/usr/bin/env python3
"""
sim_weyl_gerbe_hopf_emergence_quantities.py

Coupling Program Step 4: Emergence quantities for Weyl × Gerbe × Hopf.

Q_WGH = MI × H_weyl × H_gerbe × H_hopf (4-factor product).

E1-E3: Q_WGH = 0 for each single shell (missing shells contribute 0).
E4a-d: Q_WGH = 0 for each pairwise (MERA absent → MI=0).
E5: Q_WGH ≠ 0 in full quad (all 3 shells + MERA active), 3 seeds.
N1: z3 UNSAT — H_weyl=0 with Q_WGH>0 impossible.
N2: sympy — 4-factor product: any zero → product zero.
B1: all inactive → Q_WGH = 0.
B2: stable across 5 seeds in full quad.

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

# =====================================================================
# TOOL MANIFEST
# =====================================================================

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

TOOL_INTEGRATION_DEPTH = {
    "clifford": None,
    "cvc5": None,
    "e3nn": None,
    "geomstats": None,
    "gudhi": None,
    "pyg": None,
    "pytorch": None,
    "rustworkx": None,
    "sympy": "load_bearing",
    "toponetx": None,
    "xgi": None,
    "z3": "load_bearing",
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

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

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    import cvc5 as _cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# SHELL ENTROPY HELPERS
# =====================================================================

def H_weyl(active=True):
    return math.log(2) if active else 0.0


def H_gerbe(seed=0, active=True):
    if not active:
        return 0.0
    rng = np.random.default_rng(seed)
    grid = rng.integers(-2, 3, size=(4, 4))
    dd_count = int(np.count_nonzero(grid))
    return math.log(1 + dd_count)


def H_hopf(active=True):
    return math.log(2) / 2.0 if active else 0.0


# =====================================================================
# MI HELPER (MERA)
# =====================================================================

def bell_state_rho():
    psi = np.array([1/math.sqrt(2), 0, 0, 1/math.sqrt(2)])
    return np.outer(psi, psi)


def apply_local_unitary(rho, seed):
    rng = np.random.default_rng(seed)
    def rand_unitary(r):
        m = r.standard_normal((2, 2)) + 1j * r.standard_normal((2, 2))
        q, _ = np.linalg.qr(m)
        return q
    UA = rand_unitary(rng)
    UB = rand_unitary(rng)
    U = np.kron(UA, UB)
    return U @ rho @ U.conj().T


def dephase(rho, eps=0.3):
    return (1 - eps) * rho + eps * np.diag(np.diag(rho))


def partial_trace_A(rho):
    return np.einsum("akbk->ab", rho.reshape(2, 2, 2, 2))


def partial_trace_B(rho):
    return np.einsum("iajb,ab->ij", rho.reshape(2, 2, 2, 2), np.eye(2))


def vn_entropy(rho):
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-12]
    return float(-np.sum(evals * np.log(evals)))


def compute_MI_mera(seed, n_layers=3, eps=0.3):
    """Compute MI through n_layers MERA layers from Bell state. Returns final MI."""
    rho = bell_state_rho()
    for layer in range(n_layers):
        rho = apply_local_unitary(rho, seed=seed * 100 + layer)
        rho = dephase(rho, eps)
    rho_A = partial_trace_A(rho)
    rho_B = partial_trace_B(rho)
    return vn_entropy(rho_A) + vn_entropy(rho_B) - vn_entropy(rho)


def Q_WGH(mi, hw, hg, hh):
    return mi * hw * hg * hh


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    E1: Weyl alone → Q_WGH = 0 (H_gerbe=0, H_hopf=0 → product=0)
    E2: Gerbe alone → Q_WGH = 0
    E3: Hopf alone → Q_WGH = 0
    E4a/b/c: Pairwise + no MERA → MI=0 → Q_WGH=0
    E4d: All three shells, MERA absent → MI=0 → Q_WGH=0
    E5: Full quad (all shells + MERA), 3 seeds → Q_WGH ≠ 0
    """
    results = {}

    seed = 0

    # E1: Weyl alone
    hw = H_weyl(True)
    hg = H_gerbe(seed, False)
    hh = H_hopf(False)
    mi = compute_MI_mera(seed)
    q = Q_WGH(mi, hw, hg, hh)
    results["E1_weyl_alone"] = {
        "H_weyl": hw, "H_gerbe": hg, "H_hopf": hh, "MI": mi, "Q_WGH": q,
        "pass": abs(q) < 1e-12,
        "note": "Weyl alone: H_gerbe=0, H_hopf=0 → Q_WGH=0 by product rule",
    }

    # E2: Gerbe alone
    hw2 = H_weyl(False)
    hg2 = H_gerbe(seed, True)
    hh2 = H_hopf(False)
    q2 = Q_WGH(mi, hw2, hg2, hh2)
    results["E2_gerbe_alone"] = {
        "H_weyl": hw2, "H_gerbe": hg2, "H_hopf": hh2, "MI": mi, "Q_WGH": q2,
        "pass": abs(q2) < 1e-12,
        "note": "Gerbe alone: H_weyl=0, H_hopf=0 → Q_WGH=0",
    }

    # E3: Hopf alone
    hw3 = H_weyl(False)
    hg3 = H_gerbe(seed, False)
    hh3 = H_hopf(True)
    q3 = Q_WGH(mi, hw3, hg3, hh3)
    results["E3_hopf_alone"] = {
        "H_weyl": hw3, "H_gerbe": hg3, "H_hopf": hh3, "MI": mi, "Q_WGH": q3,
        "pass": abs(q3) < 1e-12,
        "note": "Hopf alone: H_weyl=0, H_gerbe=0 → Q_WGH=0",
    }

    # E4a: Weyl+Gerbe pairwise, MERA absent (MI=0)
    hw4a = H_weyl(True)
    hg4a = H_gerbe(seed, True)
    hh4a = H_hopf(False)
    mi_absent = 0.0
    q4a = Q_WGH(mi_absent, hw4a, hg4a, hh4a)
    results["E4a_weyl_gerbe_no_mera"] = {
        "MI": mi_absent, "Q_WGH": q4a,
        "pass": abs(q4a) < 1e-12,
        "note": "Weyl+Gerbe pairwise, MERA absent → MI=0 → Q_WGH=0",
    }

    # E4b: Weyl+Hopf pairwise, MERA absent
    hw4b = H_weyl(True)
    hg4b = H_gerbe(seed, False)
    hh4b = H_hopf(True)
    q4b = Q_WGH(mi_absent, hw4b, hg4b, hh4b)
    results["E4b_weyl_hopf_no_mera"] = {
        "MI": mi_absent, "Q_WGH": q4b,
        "pass": abs(q4b) < 1e-12,
        "note": "Weyl+Hopf pairwise, MERA absent → MI=0 → Q_WGH=0",
    }

    # E4c: Gerbe+Hopf pairwise, MERA absent
    hw4c = H_weyl(False)
    hg4c = H_gerbe(seed, True)
    hh4c = H_hopf(True)
    q4c = Q_WGH(mi_absent, hw4c, hg4c, hh4c)
    results["E4c_gerbe_hopf_no_mera"] = {
        "MI": mi_absent, "Q_WGH": q4c,
        "pass": abs(q4c) < 1e-12,
        "note": "Gerbe+Hopf pairwise, MERA absent → MI=0 → Q_WGH=0",
    }

    # E4d: All three shells, MERA absent
    hw4d = H_weyl(True)
    hg4d = H_gerbe(seed, True)
    hh4d = H_hopf(True)
    q4d = Q_WGH(mi_absent, hw4d, hg4d, hh4d)
    results["E4d_all_shells_no_mera"] = {
        "MI": mi_absent, "Q_WGH": q4d,
        "pass": abs(q4d) < 1e-12,
        "note": "All shells active, MERA absent → MI=0 → Q_WGH=0",
    }

    # E5: Full quad (all shells + MERA), 3 seeds → Q_WGH ≠ 0
    e5_results = []
    for s in range(3):
        mi_s = compute_MI_mera(s)
        hw_s = H_weyl(True)
        hg_s = H_gerbe(s, True)
        hh_s = H_hopf(True)
        q_s = Q_WGH(mi_s, hw_s, hg_s, hh_s)
        e5_results.append({"seed": s, "MI": mi_s, "Q_WGH": q_s, "nonzero": abs(q_s) > 1e-12})

    e5_pass = all(r["nonzero"] for r in e5_results)
    results["E5_full_quad_nonzero"] = {
        "seeds": e5_results,
        "all_nonzero": e5_pass,
        "pass": e5_pass,
        "note": "Full quad (all 3 shells + MERA): Q_WGH ≠ 0 for all 3 seeds",
    }

    results["pass"] = all(
        v.get("pass", False) for v in results.values() if isinstance(v, dict) and "pass" in v
    )
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    N1: z3 UNSAT — H_weyl=0 with Q_WGH>0 impossible.
    N2: sympy — 4-factor product: any zero → product zero.
    """
    results = {}

    if not TOOL_MANIFEST["z3"]["tried"]:
        results["N1_z3_weyl_zero_UNSAT"] = {"pass": False, "note": "z3 not available"}
    else:
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = (
            "N1: z3 UNSAT — H_weyl=0 with Q_WGH>0 impossible (zero factor kills product)"
        )
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

        from z3 import Real, Solver, unsat

        s = Solver()
        MI_v = Real('MI_v')
        H_w = Real('H_w')
        H_g = Real('H_g')
        H_h = Real('H_h')
        Q = Real('Q')

        s.add(MI_v > 0)
        s.add(H_w == 0)    # degenerate Weyl
        s.add(H_g > 0)
        s.add(H_h > 0)
        s.add(Q == MI_v * H_w * H_g * H_h)
        s.add(Q > 0)       # violation

        r = s.check()
        results["N1_z3_weyl_zero_UNSAT"] = {
            "claim": "MI>0, H_weyl=0, H_gerbe>0, H_hopf>0, Q_WGH=product>0",
            "z3_result": str(r),
            "expected": "unsat",
            "pass": r == unsat,
            "note": "H_weyl=0 with Q_WGH>0 is UNSAT — zero factor kills 4-way product",
        }

    if not TOOL_MANIFEST["sympy"]["tried"]:
        results["N2_sympy_four_factor_zero"] = {"pass": False, "note": "sympy not available"}
    else:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "N2: Symbolic proof — 4-factor product a*b*c*d: any factor=0 → product=0"
        )
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

        import sympy as sp
        a, b, c, d = sp.symbols('a b c d')
        product = a * b * c * d

        checks = []
        for sym, val in [(a, 0), (b, 0), (c, 0), (d, 0)]:
            v = product.subs(sym, 0)
            checks.append(v == 0)

        results["N2_sympy_four_factor_zero"] = {
            "formula": str(product),
            "all_factors_zero_when_any_zero": all(checks),
            "pass": all(checks),
            "note": "sympy: a*b*c*d=0 whenever any factor=0 — 4-way product zero property",
        }

    results["pass"] = all(
        v.get("pass", False) for v in results.values() if isinstance(v, dict) and "pass" in v
    )
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    B1: All inactive → Q_WGH = 0.
    B2: Full quad stable across 5 seeds.
    """
    results = {}

    # B1
    mi = compute_MI_mera(0)
    q = Q_WGH(mi, H_weyl(False), H_gerbe(0, False), H_hopf(False))
    results["B1_all_inactive_zero"] = {
        "Q_WGH": q,
        "pass": abs(q) < 1e-12,
        "note": "All shells inactive → Q_WGH = 0",
    }

    # B2: Full quad stable (all Q > 0) across 5 seeds
    stable = []
    for s in range(5):
        mi_s = compute_MI_mera(s)
        q_s = Q_WGH(mi_s, H_weyl(True), H_gerbe(s, True), H_hopf(True))
        stable.append({"seed": s, "Q_WGH": q_s, "positive": q_s > 0})

    b2_pass = all(r["positive"] for r in stable)
    results["B2_full_quad_stable_5seeds"] = {
        "seeds": stable,
        "all_positive": b2_pass,
        "pass": b2_pass,
        "note": "Full quad Q_WGH > 0 across 5 seeds — stable emergence",
    }

    results["pass"] = all(
        v.get("pass", False) for v in results.values() if isinstance(v, dict) and "pass" in v
    )
    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    overall = (
        pos.get("pass", False)
        and neg.get("pass", False)
        and bnd.get("pass", False)
    )

    results = {
        "name": "sim_weyl_gerbe_hopf_emergence_quantities",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": overall,
    }

    out_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results"
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_weyl_gerbe_hopf_emergence_quantities_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"all_pass: {overall}")
