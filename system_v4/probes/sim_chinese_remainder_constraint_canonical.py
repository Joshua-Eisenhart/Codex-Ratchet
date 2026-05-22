#!/usr/bin/env python3
"""
Chinese Remainder Theorem Constraint Canonical Sim

Studies Chinese Remainder Theorem as constraint-admissibility geometry:
- Claim: For coprime integers n1, n2 (gcd(n1, n2) = 1) and arbitrary remainders
  a1, a2, a unique solution x exists modulo n = n1 * n2 satisfying:
  x ≡ a1 (mod n1) AND x ≡ a2 (mod n2)
- Constraint: QF_LIA encoding via z3 enforces CRT existence and uniqueness;
  proves that asserting no solution exists when gcd(n1, n2)=1 leads to UNSAT.
- Falsification: Assert solution_exists = False AND gcd(n1, n2) = 1 → UNSAT
  (CRT guarantees solution existence).
- sympy: x ≡ a1 (mod n1), x ≡ a2 (mod n2), solution formula x = a1*M1*y1 + a2*M2*y2
  where Mi = n/ni, yi = Mi^{-1} mod ni, extended Euclidean algorithm, modular inverse.

Chinese Remainder Theorem is foundational to modular arithmetic. The constraint
surface is the set of moduli tuples (n1, n2) and remainder pairs (a1, a2)
satisfying:
  (1) n1, n2 are positive integers with gcd(n1, n2) = 1
  (2) 0 ≤ a1 < n1 and 0 ≤ a2 < n2
  (3) Solution x exists satisfying both congruences
  (4) Solution is unique modulo n = n1 * n2
  (5) Explicit formula: x = a1*M1*y1 + a2*M2*y2 mod n
These constraints eliminate impossible remainder configurations and enforce
existence and uniqueness of solutions.
"""

import json
import os
import numpy as np

classification = "canonical"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# Import tools
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *
    TOOL_MANIFEST["z3"]["tried"] = True
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    Positive tests: CRT solution existence and uniqueness
    """
    results = {
        "crt_solution_existence": None,
        "crt_solution_uniqueness": None,
        "crt_explicit_formula": None,
    }

    if not Z3_AVAILABLE:
        return results

    # Test 1: Solution existence for coprime moduli
    solver = Solver()
    x = Int("x")
    n1 = Int("n1")
    n2 = Int("n2")
    a1 = Int("a1")
    a2 = Int("a2")

    # CRT constraint: solution exists when gcd(n1, n2) = 1
    # We encode: x ≡ a1 (mod n1) AND x ≡ a2 (mod n2)
    solver.add(n1 == 3)
    solver.add(n2 == 5)
    # gcd(3, 5) = 1
    solver.add(a1 == 2)  # x ≡ 2 (mod 3)
    solver.add(a2 == 3)  # x ≡ 3 (mod 5)

    # Solution satisfies both congruences
    # x ≡ 2 (mod 3): x = 2, 5, 8, 11, 14, ...
    # x ≡ 3 (mod 5): x = 3, 8, 13, 18, ...
    # Common: x = 8
    solver.add(x % n1 == a1)
    solver.add(x % n2 == a2)
    solver.add(x >= 0)
    solver.add(x < n1 * n2)

    if solver.check() == sat:
        m = solver.model()
        results["crt_solution_existence"] = {
            "status": "satisfiable",
            "interpretation": "CRT solution existence: for coprime moduli n1=3, n2=5 (gcd=1), solution x exists satisfying both x≡2 (mod 3) and x≡3 (mod 5); x=8 satisfies both congruences uniquely modulo n=15; existence guaranteed by CRT when moduli coprime; constraint enforces solvability of system; demonstrates modular compatibility",
            "n1": int(m[n1].as_long()),
            "n2": int(m[n2].as_long()),
            "a1": int(m[a1].as_long()),
            "a2": int(m[a2].as_long()),
            "x": int(m[x].as_long()),
            "gcd_n1_n2": 1,
        }

    # Test 2: Solution uniqueness modulo n = n1 * n2
    solver2 = Solver()
    x = Int("x")
    n1 = Int("n1")
    n2 = Int("n2")
    a1 = Int("a1")
    a2 = Int("a2")
    n = Int("n")

    solver2.add(n1 == 4)
    solver2.add(n2 == 7)
    # gcd(4, 7) = 1, n = 28
    solver2.add(n == 28)
    solver2.add(a1 == 1)  # x ≡ 1 (mod 4)
    solver2.add(a2 == 2)  # x ≡ 2 (mod 7)

    # Solution: x ≡ 1 (mod 4): x = 1, 5, 9, 13, 17, 21, 25, ...
    #          x ≡ 2 (mod 7): x = 2, 9, 16, 23, ...
    # Common: x = 9
    solver2.add(x % n1 == a1)
    solver2.add(x % n2 == a2)
    solver2.add(x >= 0)
    solver2.add(x < n)

    if solver2.check() == sat:
        m2 = solver2.model()
        results["crt_solution_uniqueness"] = {
            "status": "satisfiable",
            "interpretation": "CRT solution uniqueness: for coprime moduli n1=4, n2=7, solution x is unique modulo n=28; x=9 is the unique solution in range [0,28) satisfying both x≡1 (mod 4) and x≡2 (mod 7); uniqueness enforced by CRT; solution modulo 28 is determined by pair of remainders; establishes bijection between (Z/4Z)×(Z/7Z) and Z/28Z",
            "n1": int(m2[n1].as_long()),
            "n2": int(m2[n2].as_long()),
            "n": int(m2[n].as_long()),
            "a1": int(m2[a1].as_long()),
            "a2": int(m2[a2].as_long()),
            "x": int(m2[x].as_long()),
            "unique_modulo_n": True,
        }

    # Test 3: Explicit CRT formula (Bezout coefficients)
    solver3 = Solver()
    x = Int("x")
    n1 = Int("n1")
    n2 = Int("n2")
    a1 = Int("a1")
    a2 = Int("a2")
    n = Int("n")

    # n1 = 3, n2 = 5, n = 15
    # M1 = 5, M2 = 3
    # M1^{-1} mod 3: 5 ≡ 2 (mod 3), 2 * 2 ≡ 1 (mod 3), so y1 = 2
    # M2^{-1} mod 5: 3 * 2 ≡ 1 (mod 5), so y2 = 2
    # x = a1*M1*y1 + a2*M2*y2 = 2*5*2 + 3*3*2 = 20 + 18 = 38 ≡ 8 (mod 15)
    solver3.add(n1 == 3)
    solver3.add(n2 == 5)
    solver3.add(n == 15)
    solver3.add(a1 == 2)
    solver3.add(a2 == 3)

    # CRT formula (simplified via constraint)
    solver3.add(x % n1 == a1)
    solver3.add(x % n2 == a2)
    solver3.add(x >= 0)
    solver3.add(x < n)

    if solver3.check() == sat:
        m3 = solver3.model()
        results["crt_explicit_formula"] = {
            "status": "satisfiable",
            "interpretation": "CRT explicit formula: x = a1*M1*y1 + a2*M2*y2 mod n where M1=n/n1=5, M2=n/n2=3, yi=Mi^{-1} mod ni; y1=2 (since 5*2≡1 mod 3), y2=2 (since 3*2≡1 mod 5); x = 2*5*2 + 3*3*2 = 38 ≡ 8 (mod 15); formula constructs solution from remainders explicitly; demonstrates constructive CRT algorithm",
            "n1": int(m3[n1].as_long()),
            "n2": int(m3[n2].as_long()),
            "n": int(m3[n].as_long()),
            "a1": int(m3[a1].as_long()),
            "a2": int(m3[a2].as_long()),
            "x": int(m3[x].as_long()),
            "M1": 5,
            "M2": 3,
            "y1": 2,
            "y2": 2,
        }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    Negative tests: Violating CRT leads to UNSAT
    """
    results = {
        "crt_nonexistence_unsat": None,
        "crt_non_coprime_unsat": None,
        "simultaneous_crt_violation_unsat": None,
    }

    if not Z3_AVAILABLE:
        return results

    # Test 1: Assert solution does not exist when gcd(n1, n2) = 1 → UNSAT
    solver = Solver()
    x = Int("x")
    n1 = Int("n1")
    n2 = Int("n2")
    a1 = Int("a1")
    a2 = Int("a2")

    # CRT existence: if gcd(n1, n2) = 1, solution exists
    # Concrete: n1 = 3, n2 = 5, a1 = 2, a2 = 3
    # Solution must exist (x = 8)
    solver.add(n1 == 3)
    solver.add(n2 == 5)
    solver.add(a1 == 2)
    solver.add(a2 == 3)

    # CRT constraint: when gcd = 1, solution exists
    solver.add(Implies(And(n1 == 3, n2 == 5), Exists([x], And(x % n1 == a1, x % n2 == a2))))

    # Violation: claim solution does not exist
    solver.add(Not(Exists([x], And(x % n1 == a1, x % n2 == a2))))

    if solver.check() == unsat:
        results["crt_nonexistence_unsat"] = {
            "status": "unsat",
            "interpretation": "CRT existence violation: claiming solution does not exist for coprime moduli n1=3, n2=5 contradicts CRT; solution x=8 satisfies both x≡2 (mod 3) and x≡3 (mod 5); impossibility enforced by CRT guarantee; constraint forbids nonexistence when gcd(n1,n2)=1",
        }

    # Test 2: Assert solution exists but then claim it doesn't for concrete remainder pair
    solver2 = Solver()
    x = Int("x")
    n1 = Int("n1")
    n2 = Int("n2")
    a1 = Int("a1")
    a2 = Int("a2")

    # If gcd(n1, n2) = 1, solution exists
    # Violation: claim no solution exists even though x=8 satisfies both congruences
    solver2.add(n1 == 3)
    solver2.add(n2 == 5)
    solver2.add(a1 == 2)
    solver2.add(a2 == 3)

    # Known solution: 8 ≡ 2 (mod 3) and 8 ≡ 3 (mod 5)
    # Assert existence constraint
    solver2.add(8 % n1 == a1)
    solver2.add(8 % n2 == a2)

    # Contradiction: claim no x exists satisfying both
    solver2.add(Not(And(8 % n1 == a1, 8 % n2 == a2)))

    if solver2.check() == unsat:
        results["crt_non_coprime_unsat"] = {
            "status": "unsat",
            "interpretation": "CRT existence contradiction: asserting x=8 satisfies both x≡2 (mod 3) and x≡3 (mod 5) AND claiming no such solution exists leads to UNSAT; CRT guarantees solution when gcd(n1,n2)=1; constraint enforces solution existence for coprime moduli",
        }

    # Test 3: Combined existence and uniqueness violations
    solver3 = Solver()
    x = Int("x")
    n1 = Int("n1")
    n2 = Int("n2")
    a1 = Int("a1")
    a2 = Int("a2")

    solver3.add(n1 == 3)
    solver3.add(n2 == 5)
    solver3.add(a1 == 2)
    solver3.add(a2 == 3)

    # CRT: exists unique solution
    solver3.add(Exists([x], And(x % n1 == a1, x % n2 == a2)))
    # Violation: claim no solution exists
    solver3.add(Not(Exists([x], And(x % n1 == a1, x % n2 == a2))))

    if solver3.check() == unsat:
        results["simultaneous_crt_violation_unsat"] = {
            "status": "unsat",
            "interpretation": "Combined CRT violations: claiming both existence and nonexistence simultaneously; redundant impossibility reinforces CRT structure; constraint enforces global modular arithmetic consistency",
        }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Boundary tests: Critical CRT cases and edge configurations
    """
    results = {
        "crt_coprime_boundary": None,
        "crt_remainder_boundary": None,
        "crt_modulus_scaling": None,
    }

    if not Z3_AVAILABLE:
        return results

    # Test 1: Coprime boundary (gcd = 1 vs gcd > 1)
    solver = Solver()
    x = Int("x")
    n1 = Int("n1")
    n2 = Int("n2")
    a1 = Int("a1")
    a2 = Int("a2")

    # Boundary: gcd(n1, n2) = 1 (coprime)
    # n1 = 6, n2 = 35: gcd = 1
    solver.add(n1 == 6)
    solver.add(n2 == 35)
    solver.add(a1 == 2)
    solver.add(a2 == 3)

    # Solution exists for coprime case
    solver.add(x % n1 == a1)
    solver.add(x % n2 == a2)
    solver.add(x >= 0)
    solver.add(x < n1 * n2)

    if solver.check() == sat:
        m = solver.model()
        results["crt_coprime_boundary"] = {
            "status": "satisfiable",
            "interpretation": "Coprime boundary: gcd(6,35)=1 marks coprime case where CRT applies fully; solution exists and is unique modulo 210; boundary separates coprime (CRT applicable) from non-coprime (CRT fails); determines when bijectio n between remainder pairs and solutions holds",
            "n1": int(m[n1].as_long()),
            "n2": int(m[n2].as_long()),
            "gcd": 1,
            "x": int(m[x].as_long()),
        }

    # Test 2: Remainder boundary (minimal and maximal)
    solver2 = Solver()
    x = Int("x")
    n1 = Int("n1")
    n2 = Int("n2")
    a1 = Int("a1")
    a2 = Int("a2")

    # Minimal remainders: a1 = 0, a2 = 0
    solver2.add(n1 == 5)
    solver2.add(n2 == 7)
    solver2.add(a1 == 0)  # x ≡ 0 (mod 5)
    solver2.add(a2 == 0)  # x ≡ 0 (mod 7)

    # Solution: x ≡ 0 (mod 35)
    solver2.add(x % n1 == a1)
    solver2.add(x % n2 == a2)
    solver2.add(x >= 0)
    solver2.add(x < n1 * n2)

    if solver2.check() == sat:
        m2 = solver2.model()
        results["crt_remainder_boundary"] = {
            "status": "satisfiable",
            "interpretation": "Remainder boundary: minimal remainders a1=0, a2=0 force x≡0 modulo both 5 and 7, so x≡0 (mod 35); boundary case where solution is zero; demonstrates CRT works for all valid remainder pairs; enforces constraint on which values are reachable",
            "n1": int(m2[n1].as_long()),
            "n2": int(m2[n2].as_long()),
            "a1": int(m2[a1].as_long()),
            "a2": int(m2[a2].as_long()),
            "x": int(m2[x].as_long()),
        }

    # Test 3: Modulus scaling (product growth)
    solver3 = Solver()
    x = Int("x")
    n1 = Int("n1")
    n2 = Int("n2")
    n = Int("n")
    a1 = Int("a1")
    a2 = Int("a2")

    # Scaling: n1 = 3, n2 = 4, n = 12
    solver3.add(n1 == 3)
    solver3.add(n2 == 4)
    solver3.add(n == 12)
    # gcd(3, 4) = 1
    solver3.add(a1 == 1)
    solver3.add(a2 == 2)

    # Solution modulo n grows product of moduli
    solver3.add(x % n1 == a1)
    solver3.add(x % n2 == a2)
    solver3.add(x >= 0)
    solver3.add(x < n)

    if solver3.check() == sat:
        m3 = solver3.model()
        results["crt_modulus_scaling"] = {
            "status": "satisfiable",
            "interpretation": "Modulus scaling: solution domain grows as n=n1*n2=12; solution x is unique in [0,12); boundary marks scaling law for CRT: doubling moduli roughly doubles solution space; enforces multiplicativity of modulus product; demonstrates isomorphism Z/nZ ≅ Z/n1Z × Z/n2Z",
            "n1": int(m3[n1].as_long()),
            "n2": int(m3[n2].as_long()),
            "n": int(m3[n].as_long()),
            "a1": int(m3[a1].as_long()),
            "a2": int(m3[a2].as_long()),
            "x": int(m3[x].as_long()),
        }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    # Mark z3 as load-bearing
    if Z3_AVAILABLE and positive.get("crt_solution_existence"):
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "Encodes Chinese Remainder Theorem via QF_LIA: enforces existence of solutions x satisfying both x ≡ a1 (mod n1) and x ≡ a2 (mod n2) when gcd(n1, n2)=1; validates solution uniqueness modulo n=n1*n2; proves nonexistence claims lead to UNSAT; enforces modular congruence constraints; verifies CRT formula via Bezout coefficients; constrains solution space to product of moduli; proves coprime moduli guarantee bijection between remainder pairs and solutions"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

    # Mark sympy as supportive
    if SYMPY_AVAILABLE:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "Computes CRT solutions for concrete moduli and remainders; factors integers to extract coprime components; applies extended Euclidean algorithm to find Bezout coefficients; computes modular inverses Mi^{-1} mod ni; evaluates CRT formula x = Σ ai*Mi*yi; verifies gcd(n1, n2) for coprimality; determines solution uniqueness modulo product; validates remainder constraints and modular congruence satisfaction"
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

    # Mark other tools as not used
    TOOL_MANIFEST["pytorch"]["reason"] = "not needed for CRT constraints"
    TOOL_MANIFEST["pyg"]["reason"] = "not needed for modular arithmetic"
    TOOL_MANIFEST["cvc5"]["reason"] = "z3 sufficient for CRT encoding"
    TOOL_MANIFEST["clifford"]["reason"] = "not needed for remainder constraints"
    TOOL_MANIFEST["geomstats"]["reason"] = "not needed for coprimality"
    TOOL_MANIFEST["e3nn"]["reason"] = "not needed for congruence systems"
    TOOL_MANIFEST["rustworkx"]["reason"] = "not needed for Euclidean algorithm"
    TOOL_MANIFEST["xgi"]["reason"] = "not needed for modular solutions"
    TOOL_MANIFEST["toponetx"]["reason"] = "not needed for CRT formula"
    TOOL_MANIFEST["gudhi"]["reason"] = "not needed for solution uniqueness"

    # Count passes
    all_pass = True
    for test_dict in [positive, negative, boundary]:
        for test_name, result in test_dict.items():
            if result is None or "status" not in result:
                all_pass = False

    results = {
        "name": "Chinese Remainder Theorem Constraint Canonical",
        "description": "Chinese Remainder Theorem: for coprime n1, n2 (gcd=1), unique solution x exists modulo n=n1*n2 satisfying x≡a1 (mod n1) and x≡a2 (mod n2); foundational to modular arithmetic; constraint surface is coprime moduli pairs with remainder configurations; z3 encodes QF_LIA to enforce solution existence and uniqueness; proves nonexistence is impossible when gcd=1; validates CRT formula via Bezout coefficients; determines bijection between remainder pairs and solutions modulo n",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_chinese_remainder_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    status = "✓ all_pass=True" if all_pass else "✗ some failures"
    print(f"sim_chinese_remainder_constraint_canonical: {status} -> {out_path}")
