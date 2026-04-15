#!/usr/bin/env python3
"""
sim_capability_z3_isolated.py -- Isolated tool-capability probe for z3.

Classical_baseline capability probe: demonstrates z3 SMT solver can check
satisfiability, detect UNSAT, use quantifier-free linear arithmetic, and
handle bitvectors. Honest CAN/CANNOT summary. No coupling to other tools.
Per four-sim-kinds doctrine: capability probe precedes any integration sim.
"""

import json
import os

classification = "classical_baseline"

_ISOLATED_REASON = (
    "not used: this probe isolates z3 SMT solver capability alone; "
    "cross-tool coupling is deferred to a separate integration sim "
    "per the four-sim-kinds doctrine (capability vs integration separation)."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "pyg":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "z3":        {"tried": True,  "used": True,  "reason": "load-bearing: z3 SMT solver is the sole subject; SAT/UNSAT queries, QF_LRA arithmetic, and bitvector checks are all computed by z3 directly."},
    "cvc5":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "sympy":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "clifford":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "e3nn":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "xgi":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": "load_bearing", "cvc5": None,
    "sympy": None, "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

Z3_OK = False
Z3_VERSION = None
try:
    import z3
    Z3_OK = True
    Z3_VERSION = z3.get_version_string()
except Exception as _z3_exc:
    pass


def run_positive_tests():
    r = {}
    if not Z3_OK:
        r["z3_available"] = {"pass": False, "detail": "z3 not importable"}
        return r
    r["z3_available"] = {"pass": True, "version": Z3_VERSION}

    # --- Test 1: simple SAT (linear arithmetic) ---
    s = z3.Solver()
    x, y = z3.Ints("x y")
    s.add(x + y == 10, x > 3, y > 3)
    result = str(s.check())
    r["sat_linear_arithmetic"] = {
        "pass": result == "sat",
        "result": result,
        "detail": "x+y=10, x>3, y>3 must be SAT",
    }
    if result == "sat":
        m = s.model()
        r["sat_linear_arithmetic"]["model_x"] = str(m[x])
        r["sat_linear_arithmetic"]["model_y"] = str(m[y])

    # --- Test 2: UNSAT detection ---
    s2 = z3.Solver()
    a = z3.Int("a")
    s2.add(a > 5, a < 3)
    result2 = str(s2.check())
    r["unsat_detection"] = {
        "pass": result2 == "unsat",
        "result": result2,
        "detail": "a>5 AND a<3 must be UNSAT",
    }

    # --- Test 3: Boolean satisfiability ---
    p, q = z3.Bools("p q")
    s3 = z3.Solver()
    s3.add(z3.Or(p, q), z3.Not(p))
    result3 = str(s3.check())
    r["bool_sat"] = {
        "pass": result3 == "sat",
        "result": result3,
        "detail": "(p OR q) AND NOT p forces q=True",
    }

    # --- Test 4: forall quantifier ---
    i = z3.Int("i")
    fml = z3.ForAll([i], z3.Implies(i > 0, i >= 1))
    s4 = z3.Solver()
    s4.add(z3.Not(fml))  # negate; if UNSAT, forall holds
    result4 = str(s4.check())
    r["forall_quantifier"] = {
        "pass": result4 == "unsat",
        "result": result4,
        "detail": "negation of forall(i>0 => i>=1) must be UNSAT (trivially true over ints)",
    }

    # --- Test 5: bitvector arithmetic ---
    bv = z3.BitVec("bv", 8)
    s5 = z3.Solver()
    s5.add(bv == 255)
    result5 = str(s5.check())
    r["bitvector_arith"] = {
        "pass": result5 == "sat",
        "result": result5,
        "detail": "8-bit bitvector = 255 must be SAT",
    }

    return r


def run_negative_tests():
    r = {}
    if not Z3_OK:
        r["z3_unavailable"] = {"pass": True, "detail": "skip: z3 not installed"}
        return r

    # --- Neg 1: contradictory linear constraints ---
    s = z3.Solver()
    x = z3.Real("x")
    s.add(x * x == -1)  # over Reals, unsatisfiable
    result = str(s.check())
    r["real_sqrt_neg1_unsat"] = {
        "pass": result == "unsat",
        "result": result,
        "detail": "x^2 = -1 over reals must be UNSAT",
    }

    # --- Neg 2: unsatisfiable system of equations ---
    s2 = z3.Solver()
    a, b = z3.Reals("a b")
    s2.add(a + b == 1, a + b == 2)
    result2 = str(s2.check())
    r["contradictory_equations"] = {
        "pass": result2 == "unsat",
        "result": result2,
        "detail": "a+b=1 AND a+b=2 must be UNSAT",
    }

    # --- Neg 3: unknown result is not a false positive ---
    # z3 should NOT return sat for an UNSAT formula
    s3 = z3.Solver()
    c = z3.Int("c")
    s3.add(c > 10, c < 5)
    result3 = str(s3.check())
    r["no_false_sat"] = {
        "pass": result3 == "unsat",
        "result": result3,
        "detail": "c>10 AND c<5: z3 must not return sat",
    }

    return r


def run_boundary_tests():
    r = {}
    if not Z3_OK:
        r["z3_unavailable"] = {"pass": True, "detail": "skip: z3 not installed"}
        return r

    # --- Boundary 1: tight equality boundary ---
    s = z3.Solver()
    x = z3.Int("x")
    s.add(x >= 0, x <= 0)
    result = str(s.check())
    r["tight_equality"] = {
        "pass": result == "sat",
        "result": result,
        "detail": "x>=0 AND x<=0 forces x=0, must be SAT",
    }
    if result == "sat":
        r["tight_equality"]["model_x"] = str(s.model()[x])

    # --- Boundary 2: large integer ---
    s2 = z3.Solver()
    n = z3.Int("n")
    big = 10**18
    s2.add(n == big)
    result2 = str(s2.check())
    r["large_integer"] = {
        "pass": result2 == "sat",
        "result": result2,
        "detail": f"n = 10^18 must be SAT (z3 handles arbitrary precision ints)",
    }

    # --- Boundary 3: empty solver is SAT (trivially) ---
    s3 = z3.Solver()
    result3 = str(s3.check())
    r["empty_solver"] = {
        "pass": result3 == "sat",
        "result": result3,
        "detail": "empty constraint set must be SAT",
    }

    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {**pos, **neg, **bnd}
    overall = all([v.get("pass", False) for v in all_tests.values() if isinstance(v, dict) and "pass" in v])

    results = {
        "name": "sim_capability_z3_isolated",
        "classification": classification,
        "overall_pass": overall,
        "capability_summary": {
            "CAN": [
                "check satisfiability of QF_LRA (quantifier-free linear real arithmetic)",
                "detect UNSAT via contradiction",
                "handle boolean formulas with quantifiers (ForAll/Exists)",
                "work with bitvectors (fixed-width arithmetic)",
                "extract satisfying models from SAT results",
                "handle arbitrary precision integers",
            ],
            "CANNOT": [
                "decide all non-linear real arithmetic (may return unknown)",
                "enumerate all solutions (only finds one witness)",
                "replace symbolic differentiation (use sympy for that)",
                "verify probabilistic properties (use hypothesis/PRISM for that)",
            ],
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_z3_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}")
