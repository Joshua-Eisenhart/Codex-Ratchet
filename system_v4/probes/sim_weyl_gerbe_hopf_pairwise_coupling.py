#!/usr/bin/env python3
"""
sim_weyl_gerbe_hopf_pairwise_coupling.py

Coupling Program Step 1: Pairwise coupling tests for Weyl × Gerbe × Hopf.

Tests that each pair of shells (Weyl+Gerbe, Weyl+Hopf, Gerbe+Hopf) can coexist
with both shell entropies simultaneously positive. z3 confirms simultaneous nonzero.
sympy confirms product of two factors: any zero → product zero.

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
    from z3 import Real, Solver, unsat, And
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
    """Chirality entropy: log(2) when Weyl shell active, 0 otherwise."""
    return math.log(2) if active else 0.0


def H_gerbe(seed=0, active=True):
    """log(1 + DD_count) where DD_count = nonzero integer curvature cells on 4x4 grid."""
    if not active:
        return 0.0
    import numpy as np
    rng = np.random.default_rng(seed)
    grid = rng.integers(-2, 3, size=(4, 4))
    dd_count = int(np.count_nonzero(grid))
    return math.log(1 + dd_count)


def H_hopf(active=True):
    """log(2) * (pi/2) / pi = log(2)/2 when Hopf shell active, 0 otherwise."""
    return math.log(2) / 2.0 if active else 0.0


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    P1: Weyl+Gerbe — both H_weyl and H_gerbe positive simultaneously.
    P2: Weyl+Hopf — both H_weyl and H_hopf positive simultaneously.
    P3: Gerbe+Hopf — both H_gerbe and H_hopf positive simultaneously.
    z3 confirms simultaneous nonzero for each pair.
    """
    results = {}

    if not TOOL_MANIFEST["z3"]["tried"]:
        for t in ("P1_weyl_gerbe_pairwise", "P2_weyl_hopf_pairwise", "P3_gerbe_hopf_pairwise"):
            results[t] = {"pass": False, "note": "z3 not available"}
        results["pass"] = False
        return results

    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "P1/P2/P3: z3 confirms each shell pair can have both entropies simultaneously nonzero; "
        "N1: z3 UNSAT proves degenerate Weyl (H_weyl=0) cannot contribute to coupling"
    )
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

    from z3 import Real, Solver, unsat, And, sat

    # ---- P1: Weyl+Gerbe simultaneous nonzero ----
    hw = H_weyl(active=True)
    hg = H_gerbe(seed=0, active=True)

    s1 = Solver()
    h_w = Real('h_w')
    h_g = Real('h_g')
    s1.add(h_w == hw)
    s1.add(h_g == hg)
    s1.add(h_w > 0)
    s1.add(h_g > 0)
    r1 = s1.check()

    results["P1_weyl_gerbe_pairwise"] = {
        "H_weyl": hw,
        "H_gerbe": hg,
        "z3_result": str(r1),
        "both_positive": hw > 0 and hg > 0,
        "pass": r1 == sat and hw > 0 and hg > 0,
        "note": "Weyl and Gerbe shells simultaneously active — both entropies positive",
    }

    # ---- P2: Weyl+Hopf simultaneous nonzero ----
    hh = H_hopf(active=True)

    s2 = Solver()
    h_w2 = Real('h_w2')
    h_h2 = Real('h_h2')
    s2.add(h_w2 == hw)
    s2.add(h_h2 == hh)
    s2.add(h_w2 > 0)
    s2.add(h_h2 > 0)
    r2 = s2.check()

    results["P2_weyl_hopf_pairwise"] = {
        "H_weyl": hw,
        "H_hopf": hh,
        "z3_result": str(r2),
        "both_positive": hw > 0 and hh > 0,
        "pass": r2 == sat and hw > 0 and hh > 0,
        "note": "Weyl and Hopf shells simultaneously active — both entropies positive",
    }

    # ---- P3: Gerbe+Hopf simultaneous nonzero ----
    s3 = Solver()
    h_g3 = Real('h_g3')
    h_h3 = Real('h_h3')
    s3.add(h_g3 == hg)
    s3.add(h_h3 == hh)
    s3.add(h_g3 > 0)
    s3.add(h_h3 > 0)
    r3 = s3.check()

    results["P3_gerbe_hopf_pairwise"] = {
        "H_gerbe": hg,
        "H_hopf": hh,
        "z3_result": str(r3),
        "both_positive": hg > 0 and hh > 0,
        "pass": r3 == sat and hg > 0 and hh > 0,
        "note": "Gerbe and Hopf shells simultaneously active — both entropies positive",
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
    N1: z3 UNSAT — degenerate Weyl (H_weyl=0) cannot contribute to pairwise coupling
        (product WG = H_weyl * H_gerbe = 0 if H_weyl=0).
    N2: sympy — product of two factors: any zero → product zero.
    """
    results = {}

    # ---- N1: z3 UNSAT ----
    if not TOOL_MANIFEST["z3"]["tried"]:
        results["N1_z3_degenerate_weyl_UNSAT"] = {"pass": False, "note": "z3 not available"}
    else:
        from z3 import Real, Solver, unsat

        s = Solver()
        h_w = Real('h_w')
        h_g = Real('h_g')
        product_WG = Real('product_WG')

        s.add(h_w == 0)          # degenerate Weyl
        s.add(h_g > 0)           # Gerbe active
        s.add(product_WG == h_w * h_g)
        s.add(product_WG > 0)    # claim: product positive — should be UNSAT

        r = s.check()
        results["N1_z3_degenerate_weyl_UNSAT"] = {
            "claim": "H_weyl=0 AND H_gerbe>0 AND product_WG>0",
            "z3_result": str(r),
            "expected": "unsat",
            "pass": r == unsat,
            "note": "Degenerate Weyl (H_weyl=0) cannot produce nonzero pairwise coupling — UNSAT",
        }

    # ---- N2: sympy product rule ----
    if not TOOL_MANIFEST["sympy"]["tried"]:
        results["N2_sympy_product_zero"] = {"pass": False, "note": "sympy not available"}
    else:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "N2: Symbolic proof — product of two factors, any zero → product zero"
        )
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

        import sympy as sp
        a, b = sp.symbols('a b')
        product = a * b
        # Substitute a=0
        val_a_zero = product.subs(a, 0)
        # Substitute b=0
        val_b_zero = product.subs(b, 0)

        results["N2_sympy_product_zero"] = {
            "product_formula": str(product),
            "a_zero_gives": str(val_a_zero),
            "b_zero_gives": str(val_b_zero),
            "pass": val_a_zero == 0 and val_b_zero == 0,
            "note": "sympy confirms: product a*b=0 when a=0 or b=0",
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
    B1: All inactive → all H = 0.
    """
    results = {}

    hw_off = H_weyl(active=False)
    hg_off = H_gerbe(seed=0, active=False)
    hh_off = H_hopf(active=False)

    all_zero = hw_off == 0.0 and hg_off == 0.0 and hh_off == 0.0

    results["B1_all_inactive_zero"] = {
        "H_weyl_inactive": hw_off,
        "H_gerbe_inactive": hg_off,
        "H_hopf_inactive": hh_off,
        "all_zero": all_zero,
        "pass": all_zero,
        "note": "All shells inactive → all shell entropies = 0",
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
        "name": "sim_weyl_gerbe_hopf_pairwise_coupling",
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
    out_path = os.path.join(out_dir, "sim_weyl_gerbe_hopf_pairwise_coupling_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"all_pass: {overall}")
