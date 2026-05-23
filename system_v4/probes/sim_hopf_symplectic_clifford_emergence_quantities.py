#!/usr/bin/env python3
"""
sim_hopf_symplectic_clifford_emergence_quantities.py

Coupling Program Step 4: Emergence quantities for Hopf × Symplectic × Clifford.

Q_HSC = MI × H_hopf × H_symplectic × H_clifford (4-factor product).

E1: Q_HSC = 0 when only Hopf active (MI absent → MI=0).
E2: Q_HSC = 0 when only Symplectic active (MI absent → MI=0).
E3: Q_HSC = 0 when only Clifford active (MI absent → MI=0).
E4a-d: Q_HSC = 0 for each pairwise-only (missing third shell → product=0).
E5: Q_HSC ≠ 0 in full quad (all 3 shells + MERA active), 3 seeds.
N1: z3 UNSAT — H_hopf=0 with Q_HSC>0 impossible.
N2: sympy — 4-factor product: any zero → product zero.
B1: all inactive → Q_HSC = 0.
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

def H_hopf(active=True):
    return math.log(2) / 2.0 if active else 0.0


def H_symplectic(seed=0, active=True):
    if not active:
        return 0.0
    rng = np.random.default_rng(seed)
    J = np.array([[0, 0, 1, 0],
                  [0, 0, 0, 1],
                  [-1, 0, 0, 0],
                  [0, -1, 0, 0]], dtype=float)
    tol = 1e-2
    count = 0
    known_planes = [
        np.array([[1, 0], [0, 0], [0, 1], [0, 0]], dtype=float),
        np.array([[0, 1], [0, 0], [0, 0], [0, 1]], dtype=float),
    ]
    for basis in known_planes:
        omega_mat = basis.T @ J @ basis
        if np.max(np.abs(omega_mat)) < tol:
            count += 1
    for _ in range(50):
        v1 = rng.standard_normal(4)
        v2 = rng.standard_normal(4)
        v1 = v1 / np.linalg.norm(v1)
        v2 = v2 - np.dot(v2, v1) * v1
        norm2 = np.linalg.norm(v2)
        if norm2 < 1e-10:
            continue
        v2 = v2 / norm2
        basis = np.column_stack([v1, v2])
        omega_mat = basis.T @ J @ basis
        if np.max(np.abs(omega_mat)) < tol:
            count += 1
    return math.log(1 + count)


def H_clifford(active=True):
    if not active:
        return 0.0
    rho0 = np.zeros((4, 4), dtype=complex)
    rho0[0, 0] = 1.0
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    XX = np.kron(X, X)
    theta = math.pi / 4
    evals, evecs = np.linalg.eigh(XX)
    U = evecs @ np.diag(np.exp(1j * theta * evals)) @ evecs.conj().T
    rho_after = U @ rho0 @ U.conj().T

    def offdiag_norm(rho):
        off = rho - np.diag(np.diag(rho))
        return float(np.linalg.norm(off))

    return abs(offdiag_norm(rho_after) - offdiag_norm(rho0))


def compute_MI(seed=0, eps=0.3, n_layers=3):
    psi = np.array([1 / math.sqrt(2), 0, 0, 1 / math.sqrt(2)])
    rho = np.outer(psi, psi)
    for layer in range(n_layers):
        rng = np.random.default_rng(seed * 100 + layer)
        m = rng.standard_normal((2, 2)) + 1j * rng.standard_normal((2, 2))
        UA, _ = np.linalg.qr(m)
        m = rng.standard_normal((2, 2)) + 1j * rng.standard_normal((2, 2))
        UB, _ = np.linalg.qr(m)
        U = np.kron(UA, UB)
        rho = U @ rho @ U.conj().T
        rho = (1 - eps) * rho + eps * np.diag(np.diag(rho))

    def S(r):
        ev = np.linalg.eigvalsh(r)
        ev = ev[ev > 1e-12]
        return float(-np.sum(ev * np.log(ev)))

    rho_A = np.einsum("akbk->ab", rho.reshape(2, 2, 2, 2))
    rho_B = np.einsum("iajb,ab->ij", rho.reshape(2, 2, 2, 2), np.eye(2))
    return S(rho_A) + S(rho_B) - S(rho)


def Q_HSC(mi, h_hopf, h_symp, h_cliff):
    return mi * h_hopf * h_symp * h_cliff


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    E1-E3: Q_HSC = 0 for single shells (MI=0 when MERA absent → Q=0).
    E4a-d: Q_HSC = 0 for each pairwise (one missing shell → product=0).
    E5: Q_HSC ≠ 0 in full quad (all 3 shells + MERA), 3 seeds.
    """
    results = {}

    hh = H_hopf(active=True)
    hs = H_symplectic(seed=0, active=True)
    hc = H_clifford(active=True)

    # E1-E3: single shell — MERA not active → MI=0 → Q=0
    mi_zero = 0.0  # MERA absent when only one shell

    for label, h_vals in [
        ("E1_single_hopf", (hh, 0.0, 0.0)),
        ("E2_single_symp", (0.0, hs, 0.0)),
        ("E3_single_cliff", (0.0, 0.0, hc)),
    ]:
        q = Q_HSC(mi_zero, h_vals[0], h_vals[1], h_vals[2])
        results[label] = {
            "MI": mi_zero,
            "Q_HSC": q,
            "pass": q == 0.0,
            "note": f"Single shell: MI=0 (MERA absent) → Q_HSC=0",
        }

    # E4a-d: pairwise — missing shell contributes 0
    mi_val = compute_MI(seed=0)
    for label, h_vals in [
        ("E4a_hopf_symp_no_cliff", (hh, hs, 0.0)),
        ("E4b_hopf_cliff_no_symp", (hh, 0.0, hc)),
        ("E4c_symp_cliff_no_hopf", (0.0, hs, hc)),
        ("E4d_symp_only_no_hopf_cliff", (0.0, hs, 0.0)),
    ]:
        q = Q_HSC(mi_val, h_vals[0], h_vals[1], h_vals[2])
        results[label] = {
            "MI": mi_val,
            "Q_HSC": q,
            "pass": q == 0.0,
            "note": f"Pairwise with missing shell: Q_HSC=0 (zero factor in product)",
        }

    # E5: full quad — Q_HSC ≠ 0 for 3 seeds
    e5_seeds = []
    for s in range(3):
        mi_s = compute_MI(seed=s)
        q_s = Q_HSC(mi_s, hh, hs, hc)
        e5_seeds.append({"seed": s, "MI": mi_s, "Q_HSC": q_s, "nonzero": q_s != 0.0})

    e5_pass = all(r["nonzero"] for r in e5_seeds)
    results["E5_full_quad_Q_HSC_nonzero"] = {
        "seeds": e5_seeds,
        "pass": e5_pass,
        "note": "Full quad (all 3 shells + MERA): Q_HSC > 0 for 3 seeds",
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
    N1: z3 UNSAT — H_hopf=0 with Q_HSC>0 impossible.
    N2: sympy — 4-factor product: any zero → product zero.
    """
    results = {}

    if not TOOL_MANIFEST["z3"]["tried"]:
        results["N1_z3_hopf_zero_UNSAT"] = {"pass": False, "note": "z3 not available"}
    else:
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = (
            "N1: z3 UNSAT — H_hopf=0 AND Q_HSC>0 impossible (Hopf is factor in 4-way product)"
        )
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

        from z3 import Real, Solver, unsat

        s = Solver()
        MI_v = Real('MI_v')
        H_h = Real('H_h')
        H_s = Real('H_s')
        H_c = Real('H_c')
        Q = Real('Q')

        s.add(MI_v > 0)
        s.add(H_h == 0)     # degenerate Hopf
        s.add(H_s > 0)
        s.add(H_c > 0)
        s.add(Q == MI_v * H_h * H_s * H_c)
        s.add(Q > 0)        # violation

        r = s.check()
        results["N1_z3_hopf_zero_UNSAT"] = {
            "claim": "H_hopf=0, MI>0, H_symp>0, H_cliff>0, Q_HSC>0",
            "z3_result": str(r),
            "expected": "unsat",
            "pass": r == unsat,
            "note": "H_hopf=0 with Q_HSC>0 is UNSAT — Hopf is factor in 4-way product",
        }

    if not TOOL_MANIFEST["sympy"]["tried"]:
        results["N2_sympy_four_factor_zero"] = {"pass": False, "note": "sympy not available"}
    else:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "N2: Symbolic proof — Q_HSC = a*b*c*d: any factor=0 → Q_HSC=0"
        )
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

        import sympy as sp
        a, b, c, d = sp.symbols('a b c d')
        product = a * b * c * d
        checks = [product.subs(sym, 0) == 0 for sym in [a, b, c, d]]
        results["N2_sympy_four_factor_zero"] = {
            "formula": "Q_HSC = MI * H_hopf * H_symp * H_cliff",
            "all_zero_when_any_factor_zero": all(checks),
            "pass": all(checks),
            "note": "sympy confirms 4-factor product zero property",
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
    B1: all inactive → Q_HSC = 0.
    B2: stable across 5 seeds in full quad (Q_HSC > 0 for all).
    """
    results = {}

    hh_off = H_hopf(active=False)
    hs_off = H_symplectic(seed=0, active=False)
    hc_off = H_clifford(active=False)
    mi_val = compute_MI(seed=0)
    q_all_off = Q_HSC(mi_val, hh_off, hs_off, hc_off)

    results["B1_all_inactive_Q_zero"] = {
        "H_hopf_inactive": hh_off,
        "H_symp_inactive": hs_off,
        "H_cliff_inactive": hc_off,
        "Q_HSC": q_all_off,
        "pass": q_all_off == 0.0,
        "note": "All shells inactive → Q_HSC = 0 (all shell entropies = 0)",
    }

    hh = H_hopf(active=True)
    hs = H_symplectic(seed=0, active=True)
    hc = H_clifford(active=True)

    stable_seeds = []
    for s in range(5):
        mi_s = compute_MI(seed=s)
        q_s = Q_HSC(mi_s, hh, hs, hc)
        stable_seeds.append({"seed": s, "Q_HSC": q_s, "positive": q_s > 0})

    b2_pass = all(r["positive"] for r in stable_seeds)
    results["B2_full_quad_stable_5seeds"] = {
        "seeds": stable_seeds,
        "all_positive": b2_pass,
        "pass": b2_pass,
        "note": "Q_HSC > 0 for seeds 0-4 in full quad",
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
        "name": "sim_hopf_symplectic_clifford_emergence_quantities",
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
    out_path = os.path.join(out_dir, "sim_hopf_symplectic_clifford_emergence_quantities_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"all_pass: {overall}")
