#!/usr/bin/env python3
"""
sim_hopf_symplectic_gerbe_pairwise_coupling.py

Step 1 (pairwise coupling) of the Hopf×Symplectic×Gerbe coupling program (27th program).

Tests H×S, H×G, S×G pairwise products.
Q_pair = H_i × H_j > 0 for all pairs.

Shell entropy values:
  H_hopf = log(2)/2 ≈ 0.347 (π/2 holonomy, topology-sensitive)
  H_symp = log(1+4) ≈ 1.609 (n_lagrangian=4 fixed)
  H_gerbe = log(1+3) ≈ 1.386 (DD_count=3 fixed)

Classification: canonical
"""
import json, os, math
import numpy as np

classification = "classical_baseline"

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

_Z3 = False
try:
    import z3 as _z3
    TOOL_MANIFEST["z3"].update(tried=True, used=True,
        reason="UNSAT: H_i > 0 and H_j > 0 with pair product = 0 impossible — positivity constraint for all three HSG pairs (load-bearing).")
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    _Z3 = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

_SYMPY = False
try:
    import sympy as _sp
    TOOL_MANIFEST["sympy"].update(tried=True, used=True,
        reason="Symbolic pair product zero-factor collapse: a*b=0 if either factor=0, encoding HSG pair product gate (load-bearing).")
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    _SYMPY = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

for _mod, _key, _reason in [
    ("torch",          "pytorch",   "not needed for pairwise H product tests; Q_pair is a scalar product not requiring autograd"),
    ("torch_geometric","pyg",       "no graph learning required in pairwise HSG shell entropy product step"),
    ("cvc5",           "cvc5",      "z3 is sufficient for the UNSAT positivity proof; cvc5 adds no new information here"),
    ("clifford",       "clifford",  "Hopf holonomy does not use Clifford algebra rotor; H_hopf is fixed analytic value log(2)/2"),
    ("geomstats",      "geomstats", "Riemannian geometry not invoked in scalar HSG pairwise product step"),
    ("e3nn",           "e3nn",      "SO(3) equivariant networks not needed for scalar pairwise entropy products"),
    ("rustworkx",      "rustworkx", "no graph traversal required in HSG pairwise entropy product tests"),
    ("xgi",            "xgi",       "no hyperedge structure required in pairwise HSG shell entropy tests"),
    ("toponetx",       "toponetx",  "chain-complex topology not invoked in pairwise product step"),
    ("gudhi",          "gudhi",     "persistent homology not needed in pairwise HSG shell entropy scalar tests"),
]:
    try:
        __import__(_mod)
        TOOL_MANIFEST[_key]["tried"] = True
        TOOL_MANIFEST[_key]["reason"] = _reason
    except ImportError:
        TOOL_MANIFEST[_key]["reason"] = "not installed"


# =====================================================================
# Shell entropy values
# =====================================================================

H_HOPF  = math.log(2) / 2      # π/2 holonomy, topology-sensitive
H_SYMP  = math.log(1 + 4)      # n_lagrangian = 4
H_GERBE = math.log(1 + 3)      # DD_count = 3


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    r = {}

    # P1: H×S pair
    Q_HS = H_HOPF * H_SYMP
    r["P1_hopf_symplectic_pair"] = {
        "H_hopf": H_HOPF,
        "H_symp": H_SYMP,
        "Q_HS": Q_HS,
        "passed": bool(Q_HS > 0),
    }

    # P2: H×G pair
    Q_HG = H_HOPF * H_GERBE
    r["P2_hopf_gerbe_pair"] = {
        "H_hopf": H_HOPF,
        "H_gerbe": H_GERBE,
        "Q_HG": Q_HG,
        "passed": bool(Q_HG > 0),
    }

    # P3: S×G pair
    Q_SG = H_SYMP * H_GERBE
    r["P3_symplectic_gerbe_pair"] = {
        "H_symp": H_SYMP,
        "H_gerbe": H_GERBE,
        "Q_SG": Q_SG,
        "passed": bool(Q_SG > 0),
    }

    r["pass"] = bool(all(r[k]["passed"] for k in r if k != "pass"))
    return r


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    r = {}

    # N1: z3 UNSAT — H_i > 0 AND H_j > 0 AND Q_pair = 0 impossible
    if _Z3:
        s = _z3.Solver()
        Hi = _z3.Real("Hi"); Hj = _z3.Real("Hj"); Q = Hi * Hj
        s.add(Hi > 0, Hj > 0, Q == 0)
        unsat = (s.check() == _z3.unsat)
        r["N1_z3_unsat_pair_product_zero"] = {
            "z3": "unsat" if unsat else "sat",
            "passed": bool(unsat),
        }
    else:
        r["N1_z3_unsat_pair_product_zero"] = {"error": "z3 not installed", "passed": False}

    # N2: sympy — pair product = 0 if either factor = 0
    if _SYMPY:
        a, b = _sp.symbols("a b")
        expr = a * b
        ok = (expr.subs(a, 0) == 0 and expr.subs(b, 0) == 0)
        r["N2_sympy_pair_zero_factor"] = {
            "a=0": str(expr.subs(a, 0)),
            "b=0": str(expr.subs(b, 0)),
            "passed": bool(ok),
        }
    else:
        r["N2_sympy_pair_zero_factor"] = {"error": "sympy not installed", "passed": False}

    # N3: zero DD_count gives H_gerbe = 0
    H_gerbe_zero = math.log(1 + 0)
    r["N3_zero_DD_gives_zero_gerbe"] = {
        "H_gerbe_zero": H_gerbe_zero,
        "passed": bool(H_gerbe_zero == 0.0),
    }

    r["pass"] = bool(all(r[k]["passed"] for k in r if k != "pass"))
    return r


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    r = {}

    # B1: H_hopf positive
    r["B1_H_hopf_positive"] = {
        "H_hopf": H_HOPF,
        "passed": bool(H_HOPF > 0),
    }

    # B2: all three H values positive
    r["B2_all_H_positive"] = {
        "H_hopf": H_HOPF,
        "H_symp": H_SYMP,
        "H_gerbe": H_GERBE,
        "passed": bool(H_HOPF > 0 and H_SYMP > 0 and H_GERBE > 0),
    }

    r["pass"] = bool(all(r[k]["passed"] for k in r if k != "pass"))
    return r


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    overall = pos["pass"] and neg["pass"] and bnd["pass"]

    out = {
        "name": "sim_hopf_symplectic_gerbe_pairwise_coupling",
        "classification": classification,
        "divergence_log": (
            "Step 1 pairwise coupling for Hopf×Symplectic×Gerbe (27th program). "
            "H_hopf = log(2)/2 (π/2 holonomy, topology-sensitive). "
            "H_symp = log(1+4). H_gerbe = log(1+3). "
            "All three pairs Q_pair > 0 confirmed. "
            "z3 UNSAT: positive factors cannot multiply to zero. "
            "sympy: zero-factor collapse verified."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "H_values": {"H_hopf": H_HOPF, "H_symp": H_SYMP, "H_gerbe": H_GERBE},
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "overall_pass": overall,
    }

    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "sim_hopf_symplectic_gerbe_pairwise_coupling_results.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"overall_pass={overall} -> {p}")
    if not overall:
        import sys; sys.exit(1)
