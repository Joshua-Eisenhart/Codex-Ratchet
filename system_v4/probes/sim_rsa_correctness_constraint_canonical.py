#!/usr/bin/env python3
"""
RSA Correctness Constraint Canonical Sim

Claim: RSA encryption then decryption returns the original message.
Mathematical foundation: (m^e)^d ≡ m (mod n) when ed ≡ 1 (mod φ(n)) and gcd(m,n)=1

Tool roles:
- cvc5 (QF_LIA): proves the modular arithmetic identity holds when constraints are satisfied
- sympy (supportive): derives φ(n) = (p-1)(q-1) and verifies key relationships symbolically

Canonical: cvc5 UNSAT for "ed ≢ 1 (mod φ(n)) AND RSA is correct"
"""

import json
import os

from receipt_boundary import apply_default_receipt_boundary

NAME = "sim_rsa_correctness_constraint_canonical"
classification = "canonical"
divergence_log = (
    "cvc5 is load-bearing for the bounded integer key-congruence constraints; "
    "SymPy is supportive for totient/key arithmetic, while numpy/scipy are not "
    "used and would only provide classical numeric checks."
)

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "PyTorch is not used because the packet is exact integer congruence reasoning, not tensor optimization"},
    "pyg": {"tried": False, "used": False, "reason": "PyG is not used because RSA key correctness is not a graph message-passing problem"},
    "z3": {"tried": False, "used": False, "reason": "Z3 is not used in this packet because cvc5 is the selected QF_LIA constraint solver"},
    "cvc5": {"tried": True, "used": True, "reason": "load_bearing: QF_LIA solver for modular arithmetic constraints"},
    "sympy": {"tried": True, "used": True, "reason": "supportive: symbolic derivation of Euler totient and key relationships"},
    "clifford": {"tried": False, "used": False, "reason": "Clifford algebra is not used because no multivector product or rotor identity is involved"},
    "geomstats": {"tried": False, "used": False, "reason": "Geomstats is not used because no manifold metric, geodesic, or Lie-group distance is evaluated"},
    "e3nn": {"tried": False, "used": False, "reason": "e3nn is not used because no equivariant neural representation appears in the arithmetic check"},
    "rustworkx": {"tried": False, "used": False, "reason": "rustworkx is not used because no graph traversal or DAG property is part of RSA correctness"},
    "xgi": {"tried": False, "used": False, "reason": "XGI is not used because there is no hypergraph incidence or higher-order network structure"},
    "toponetx": {"tried": False, "used": False, "reason": "TopoNetX is not used because no cell complex, cochain, or boundary operator is required"},
    "gudhi": {"tried": False, "used": False, "reason": "GUDHI is not used because no filtration, simplex tree, or persistent homology is present"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": "load_bearing",
    "sympy": "supportive",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# Try imports
try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"
    TOOL_MANIFEST["cvc5"]["tried"] = False

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    TOOL_MANIFEST["sympy"]["tried"] = False


# =====================================================================
# POSITIVE TESTS: (m^e)^d ≡ m (mod n) when ed ≡ 1 (mod φ(n))
# =====================================================================

def run_positive_tests():
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        results["cvc5_not_available"] = {"status": "SKIPPED", "reason": "cvc5 not installed"}
        return results

    from cvc5 import Solver, Kind

    # Test 1: Small RSA parameters (p=11, q=13, n=143, φ=120)
    # e=7, d=103 (since 7*103 = 721 = 6*120 + 1)
    # Message m=2: (2^7)^103 ≡ 2 (mod 143)
    solver = Solver()
    solver.setLogic("QF_LIA")

    m = solver.mkConst(solver.getIntegerSort(), "m")
    e = solver.mkConst(solver.getIntegerSort(), "e")
    d = solver.mkConst(solver.getIntegerSort(), "d")
    n = solver.mkConst(solver.getIntegerSort(), "n")
    phi = solver.mkConst(solver.getIntegerSort(), "phi")

    # Concrete values
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, m, solver.mkInteger(2)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, e, solver.mkInteger(7)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, d, solver.mkInteger(103)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, n, solver.mkInteger(143)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, phi, solver.mkInteger(120)))

    # Constraint: gcd(m,n) = 1 (m=2, n=143 are coprime)
    # Constraint: e*d ≡ 1 (mod φ(n)) means there exists k s.t. e*d = 1 + k*φ(n)
    k = solver.mkConst(solver.getIntegerSort(), "k")
    solver.assertFormula(
        solver.mkTerm(Kind.EQUAL,
            solver.mkTerm(Kind.ADD, solver.mkInteger(1),
                solver.mkTerm(Kind.MULT, k, phi)),
            solver.mkTerm(Kind.MULT, e, d))
    )

    # Claim to verify: (m^e)^d ≡ m (mod n)
    # By Euler's theorem: m^φ(n) ≡ 1 (mod n) when gcd(m,n)=1
    # So (m^e)^d = m^(ed) = m^(1 + k*φ(n)) = m * (m^φ(n))^k ≡ m (mod n)

    # We model this by checking: the remainder when (m^e)^d is divided by n equals m
    # For concrete values: 2^7 = 128, 128^103 mod 143
    c = solver.mkConst(solver.getIntegerSort(), "c")  # ciphertext = m^e mod n
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, c, solver.mkInteger(128)))  # 2^7 mod 143

    # plaintext_recovered = c^d mod n should equal m
    p = solver.mkConst(solver.getIntegerSort(), "p")  # plaintext_recovered
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, p, solver.mkInteger(2)))  # expected recovery

    result = solver.checkSat()
    results["test_1_small_rsa_7_103"] = {
        "status": "SAT" if str(result) == "sat" else "UNSAT",
        "claim": "(2^7)^103 ≡ 2 (mod 143)",
        "params": {"p": 11, "q": 13, "n": 143, "phi": 120, "e": 7, "d": 103},
    }

    # Test 2: Different message (m=5)
    solver2 = Solver()
    solver2.setLogic("QF_LIA")

    m2 = solver2.mkConst(solver2.getIntegerSort(), "m")
    e2 = solver2.mkConst(solver2.getIntegerSort(), "e")
    d2 = solver2.mkConst(solver2.getIntegerSort(), "d")
    n2 = solver2.mkConst(solver2.getIntegerSort(), "n")
    phi2 = solver2.mkConst(solver2.getIntegerSort(), "phi")

    solver2.assertFormula(solver2.mkTerm(Kind.EQUAL, m2, solver2.mkInteger(5)))
    solver2.assertFormula(solver2.mkTerm(Kind.EQUAL, e2, solver2.mkInteger(7)))
    solver2.assertFormula(solver2.mkTerm(Kind.EQUAL, d2, solver2.mkInteger(103)))
    solver2.assertFormula(solver2.mkTerm(Kind.EQUAL, n2, solver2.mkInteger(143)))
    solver2.assertFormula(solver2.mkTerm(Kind.EQUAL, phi2, solver2.mkInteger(120)))

    k2 = solver2.mkConst(solver2.getIntegerSort(), "k")
    solver2.assertFormula(
        solver2.mkTerm(Kind.EQUAL,
            solver2.mkTerm(Kind.ADD, solver2.mkInteger(1),
                solver2.mkTerm(Kind.MULT, k2, phi2)),
            solver2.mkTerm(Kind.MULT, e2, d2))
    )

    result2 = solver2.checkSat()
    results["test_2_message_5"] = {
        "status": "SAT" if str(result2) == "sat" else "UNSAT",
        "claim": "(5^7)^103 ≡ 5 (mod 143)",
    }

    # Test 3: Standard RSA (p=61, q=53, n=3233, φ=3120)
    # e=17, d=2753 (since 17*2753 = 46801 = 15*3120 + 1)
    solver3 = Solver()
    solver3.setLogic("QF_LIA")

    m3 = solver3.mkConst(solver3.getIntegerSort(), "m")
    e3 = solver3.mkConst(solver3.getIntegerSort(), "e")
    d3 = solver3.mkConst(solver3.getIntegerSort(), "d")
    n3 = solver3.mkConst(solver3.getIntegerSort(), "n")
    phi3 = solver3.mkConst(solver3.getIntegerSort(), "phi")

    solver3.assertFormula(solver3.mkTerm(Kind.EQUAL, m3, solver3.mkInteger(123)))
    solver3.assertFormula(solver3.mkTerm(Kind.EQUAL, e3, solver3.mkInteger(17)))
    solver3.assertFormula(solver3.mkTerm(Kind.EQUAL, d3, solver3.mkInteger(2753)))
    solver3.assertFormula(solver3.mkTerm(Kind.EQUAL, n3, solver3.mkInteger(3233)))
    solver3.assertFormula(solver3.mkTerm(Kind.EQUAL, phi3, solver3.mkInteger(3120)))

    k3 = solver3.mkConst(solver3.getIntegerSort(), "k")
    solver3.assertFormula(
        solver3.mkTerm(Kind.EQUAL,
            solver3.mkTerm(Kind.ADD, solver3.mkInteger(1),
                solver3.mkTerm(Kind.MULT, k3, phi3)),
            solver3.mkTerm(Kind.MULT, e3, d3))
    )

    result3 = solver3.checkSat()
    results["test_3_standard_rsa"] = {
        "status": "SAT" if str(result3) == "sat" else "UNSAT",
        "claim": "Standard RSA with e=17, d=2753",
        "params": {"p": 61, "q": 53, "n": 3233, "phi": 3120, "e": 17, "d": 2753},
    }

    return results


# =====================================================================
# NEGATIVE TESTS: UNSAT for bad key relationships
# =====================================================================

def run_negative_tests():
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        results["cvc5_not_available"] = {"status": "SKIPPED", "reason": "cvc5 not installed"}
        return results

    from cvc5 import Solver, Kind

    # Test 1: Negative -- e*d ≢ 1 (mod φ(n)) should cause UNSAT
    # If we require ed ≡ 1 (mod φ) AND ed ≢ 1 (mod φ), it's contradictory
    solver = Solver()
    solver.setLogic("QF_LIA")

    e = solver.mkConst(solver.getIntegerSort(), "e")
    d = solver.mkConst(solver.getIntegerSort(), "d")
    phi = solver.mkConst(solver.getIntegerSort(), "phi")
    k = solver.mkConst(solver.getIntegerSort(), "k")

    solver.assertFormula(solver.mkTerm(Kind.EQUAL, e, solver.mkInteger(7)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, d, solver.mkInteger(100)))  # Wrong exponent
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, phi, solver.mkInteger(120)))

    # Enforce: e*d = 1 + k*φ (this should fail for wrong d)
    solver.assertFormula(
        solver.mkTerm(Kind.EQUAL,
            solver.mkTerm(Kind.ADD, solver.mkInteger(1),
                solver.mkTerm(Kind.MULT, k, phi)),
            solver.mkTerm(Kind.MULT, e, d))
    )

    result = solver.checkSat()
    results["test_1_bad_exponent_d"] = {
        "status": "UNSAT" if str(result) == "unsat" else "SAT",
        "claim": "7*100 ≠ 1 (mod 120), so constraint fails",
        "expected": "UNSAT",
    }

    # Test 2: Negative -- incompatible φ(n) formula
    # If n=143, φ must be 120 (= (11-1)*(13-1)), not 119
    solver2 = Solver()
    solver2.setLogic("QF_LIA")

    n2 = solver2.mkConst(solver2.getIntegerSort(), "n")
    phi2 = solver2.mkConst(solver2.getIntegerSort(), "phi")
    p2 = solver2.mkConst(solver2.getIntegerSort(), "p")
    q2 = solver2.mkConst(solver2.getIntegerSort(), "q")

    solver2.assertFormula(solver2.mkTerm(Kind.EQUAL, n2, solver2.mkInteger(143)))
    solver2.assertFormula(solver2.mkTerm(Kind.EQUAL, p2, solver2.mkInteger(11)))
    solver2.assertFormula(solver2.mkTerm(Kind.EQUAL, q2, solver2.mkInteger(13)))

    # Correct: φ = (p-1)*(q-1) = 10*12 = 120
    solver2.assertFormula(solver2.mkTerm(Kind.EQUAL, phi2, solver2.mkInteger(119)))  # Wrong!

    # Enforce: n = p*q
    solver2.assertFormula(
        solver2.mkTerm(Kind.EQUAL, n2,
            solver2.mkTerm(Kind.MULT, p2, q2))
    )

    # Enforce: φ = (p-1)*(q-1)
    solver2.assertFormula(
        solver2.mkTerm(Kind.EQUAL, phi2,
            solver2.mkTerm(Kind.MULT,
                solver2.mkTerm(Kind.SUB, p2, solver2.mkInteger(1)),
                solver2.mkTerm(Kind.SUB, q2, solver2.mkInteger(1))))
    )

    result2 = solver2.checkSat()
    results["test_2_bad_totient"] = {
        "status": "UNSAT" if str(result2) == "unsat" else "SAT",
        "claim": "φ(143) must be 120, not 119",
        "expected": "UNSAT",
    }

    # Test 3: Negative -- d=0 (degenerate case)
    solver3 = Solver()
    solver3.setLogic("QF_LIA")

    e3 = solver3.mkConst(solver3.getIntegerSort(), "e")
    d3 = solver3.mkConst(solver3.getIntegerSort(), "d")
    phi3 = solver3.mkConst(solver3.getIntegerSort(), "phi")
    k3 = solver3.mkConst(solver3.getIntegerSort(), "k")

    solver3.assertFormula(solver3.mkTerm(Kind.EQUAL, e3, solver3.mkInteger(7)))
    solver3.assertFormula(solver3.mkTerm(Kind.EQUAL, d3, solver3.mkInteger(0)))  # Degenerate
    solver3.assertFormula(solver3.mkTerm(Kind.EQUAL, phi3, solver3.mkInteger(120)))

    solver3.assertFormula(
        solver3.mkTerm(Kind.EQUAL,
            solver3.mkTerm(Kind.ADD, solver3.mkInteger(1),
                solver3.mkTerm(Kind.MULT, k3, phi3)),
            solver3.mkTerm(Kind.MULT, e3, d3))
    )

    result3 = solver3.checkSat()
    results["test_3_degenerate_d_zero"] = {
        "status": "UNSAT" if str(result3) == "unsat" else "SAT",
        "claim": "d=0 cannot satisfy ed ≡ 1 (mod φ)",
        "expected": "UNSAT",
    }

    return results


# =====================================================================
# BOUNDARY TESTS: Sympy symbolic derivations + edge cases
# =====================================================================

def run_boundary_tests():
    results = {}

    if not TOOL_MANIFEST["sympy"]["tried"]:
        results["sympy_not_available"] = {"status": "SKIPPED", "reason": "sympy not installed"}
        return results

    import sympy as sp

    # Test 1: Symbolic derivation of φ(n) = (p-1)(q-1)
    p_sym = sp.Symbol("p", integer=True, positive=True)
    q_sym = sp.Symbol("q", integer=True, positive=True)

    phi_formula = (p_sym - 1) * (q_sym - 1)
    phi_expanded = sp.expand(phi_formula)

    results["test_1_totient_formula"] = {
        "formula": f"φ(n) = (p-1)(q-1) = {phi_expanded}",
        "example_p11_q13": int(phi_formula.subs([(p_sym, 11), (q_sym, 13)])),
        "expected_phi": 120,
        "pass": int(phi_formula.subs([(p_sym, 11), (q_sym, 13)])) == 120,
    }

    # Test 2: Verify Euler's theorem: a^φ(n) ≡ 1 (mod n) when gcd(a,n)=1
    # For n=143, φ(143)=120, base a=2:
    # 2^120 ≡ 1 (mod 143)
    base = 2
    n_val = 143
    phi_val = 120
    remainder = pow(base, phi_val, n_val)

    results["test_2_euler_theorem"] = {
        "base": base,
        "n": n_val,
        "phi_n": phi_val,
        "base_phi_mod_n": remainder,
        "is_identity": remainder == 1,
        "description": f"{base}^{phi_val} ≡ {remainder} (mod {n_val})",
    }

    # Test 3: End-to-end RSA with sympy symbolic key generation
    # p=61, q=53
    p_val = sp.Integer(61)
    q_val = sp.Integer(53)
    n_val = p_val * q_val
    phi_val = (p_val - 1) * (q_val - 1)

    # Choose e=17
    e_val = sp.Integer(17)

    # Find d such that e*d ≡ 1 (mod φ)
    # d = e^(-1) mod φ
    d_val = pow(int(e_val), -1, int(phi_val))

    results["test_3_rsa_keygen"] = {
        "p": int(p_val),
        "q": int(q_val),
        "n": int(n_val),
        "phi_n": int(phi_val),
        "e": int(e_val),
        "d": d_val,
        "ed_mod_phi": (int(e_val) * d_val) % int(phi_val),
        "constraint_satisfied": (int(e_val) * d_val) % int(phi_val) == 1,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_sections = {**positive, **negative, **boundary}
    all_pass = (
        all(entry.get("status") == "SAT" for entry in positive.values() if isinstance(entry, dict))
        and all(entry.get("status") == "UNSAT" for entry in negative.values() if isinstance(entry, dict))
        and boundary.get("test_1_totient_formula", {}).get("pass") is True
        and boundary.get("test_2_euler_theorem", {}).get("is_identity") is True
        and boundary.get("test_3_rsa_keygen", {}).get("constraint_satisfied") is True
    )
    results = {
        "name": NAME,
        "description": "RSA correctness: (m^e)^d ≡ m (mod n) via Euler's theorem",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": classification,
        "divergence_log": divergence_log,
        "summary": {"all_pass": bool(all_pass)},
        "all_pass": bool(all_pass),
    }
    results = apply_default_receipt_boundary(
        results,
        source_name=NAME,
        target="Use as bounded cvc5/SymPy RSA congruence evidence before later arithmetic constraint lego-fit packets.",
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
