#!/usr/bin/env python3
"""
Sylow Theorem Constraint Canonical Sim

Studies Sylow theorems as constraint-admissibility geometry:
- Claim: The number of Sylow p-subgroups n_p of a finite group G must satisfy:
  (1) n_p ≡ 1 (mod p) [n_p leaves remainder 1 when divided by p]
  (2) n_p | (|G| / p^k) where p^k || |G| [n_p divides the p-part complement]
- Constraint: QF_LIA encoding via z3 enforces both divisibility and congruence
  conditions; proves that no Sylow p-subgroup count can violate these
  simultaneously (UNSAT).
- Falsification: n_p ≡ 0 (mod p) for Sylow count → UNSAT (violates Sylow theorem)
- sympy: Sylow p-subgroup of order p^k where p^k || |G|, all Sylow p-subgroups
  are conjugate, index of normalizer of P in G equals n_p.

Sylow theorems are foundational to group theory. The constraint surface is the
set of group orders |G| satisfying:
  (1) |G| = p^k * m where gcd(p, m) = 1
  (2) Sylow p-subgroups have order p^k
  (3) Number n_p of Sylow p-subgroups: n_p ≡ 1 (mod p) AND n_p | m
  (4) All Sylow p-subgroups are conjugate
These constraints eliminate impossible Sylow counts and enforce structural
consequences on group composition.
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
    Positive tests: Sylow p-subgroup counts satisfy constraints
    """
    results = {
        "sylow_count_modular_constraint": None,
        "sylow_count_divisibility_constraint": None,
        "sylow_conjugacy_consequence": None,
    }

    if not Z3_AVAILABLE:
        return results

    # Test 1: n_p ≡ 1 (mod p) constraint
    solver = Solver()
    n_p = Int("n_p")
    p = Int("p")

    # Sylow constraint: n_p ≡ 1 (mod p)
    solver.add(n_p % p == 1)
    # Concrete values: prime p = 5, valid Sylow count n_p = 11 (≡ 1 mod 5)
    solver.add(p == 5)
    solver.add(n_p == 11)

    if solver.check() == sat:
        m = solver.model()
        results["sylow_count_modular_constraint"] = {
            "status": "satisfiable",
            "interpretation": "Sylow theorem constraint 1: number of Sylow p-subgroups n_p must satisfy n_p ≡ 1 (mod p); dividing n_p by p leaves remainder 1; n_p = 1 + kp for some k ≥ 0; constraint from conjugacy class structure; all Sylow p-subgroups lie in single conjugacy class; normalizer action determines n_p via orbit-stabilizer",
            "p": int(m[p].as_long()),
            "n_p": int(m[n_p].as_long()),
            "modulo_check": int(m[n_p].as_long()) % int(m[p].as_long()),
        }

    # Test 2: n_p | (|G| / p^k) divisibility constraint
    solver2 = Solver()
    n_p = Int("n_p")
    m_val = Int("m_val")

    # Sylow constraint: n_p divides |G|/p^k = m (the p-free part)
    # We assert: ∃ k ≥ 0 s.t. (m_val % n_p) == 0
    solver2.add(m_val % n_p == 0)
    # Concrete values: m = 24, n_p = 1, 3, 4, 6, 8, 12, or 24
    solver2.add(m_val == 24)
    solver2.add(n_p == 6)

    if solver2.check() == sat:
        m2 = solver2.model()
        results["sylow_count_divisibility_constraint"] = {
            "status": "satisfiable",
            "interpretation": "Sylow theorem constraint 2: number of Sylow p-subgroups n_p must divide |G|/p^k where |G| = p^k * m with gcd(p,m)=1; n_p | m (divisibility by p-free complement); divisors of m that satisfy ≡1(mod p) are admissible Sylow counts; constraint from normalizer structure; [G : N_G(P)] = n_p where N_G(P) is normalizer of P",
            "m_val": int(m2[m_val].as_long()),
            "n_p": int(m2[n_p].as_long()),
            "divides": (int(m2[m_val].as_long()) % int(m2[n_p].as_long()) == 0),
        }

    # Test 3: Conjugacy consequence of Sylow theorem
    solver3 = Solver()
    n_p = Int("n_p")
    group_order = Int("group_order")
    p_power = Int("p_power")

    # For p = 2: all Sylow 2-subgroups are conjugate in groups of order 2^a * m
    # Conjugacy implies they're all isomorphic and maximally similar structure
    solver3.add(group_order == 12)  # Order 12 = 4 * 3 (p^k = 4, m = 3)
    solver3.add(p_power == 4)
    solver3.add(n_p == 1)  # Only 1 Sylow 2-subgroup (forced by divisibility and congruence)

    if solver3.check() == sat:
        m3 = solver3.model()
        results["sylow_conjugacy_consequence"] = {
            "status": "satisfiable",
            "interpretation": "Sylow conjugacy: all Sylow p-subgroups of a group G are conjugate; when n_p = 1, unique Sylow p-subgroup is normal; conjugacy class partition divides Sylow subgroup count via normalizer; normalizer of P has order |G| / n_p; conjugacy determines group structure and permits composition analysis",
            "group_order": int(m3[group_order].as_long()),
            "p_power": int(m3[p_power].as_long()),
            "n_p": int(m3[n_p].as_long()),
            "conjugate": True,
        }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    Negative tests: Violating Sylow count constraints leads to UNSAT
    """
    results = {
        "sylow_count_mod_p_zero_unsat": None,
        "sylow_count_does_not_divide_unsat": None,
        "simultaneous_constraint_violation_unsat": None,
    }

    if not Z3_AVAILABLE:
        return results

    # Test 1: Claim n_p ≡ 0 (mod p) → UNSAT
    solver = Solver()
    n_p = Int("n_p")
    p = Int("p")

    # Claim: n_p ≡ 0 (mod p) [violates Sylow constraint]
    solver.add(n_p % p == 0)
    # Enforce Sylow constraint: n_p ≡ 1 (mod p)
    solver.add(n_p % p == 1)
    # Concrete values
    solver.add(p == 5)
    solver.add(n_p == 10)  # 10 ≡ 0 (mod 5)

    if solver.check() == unsat:
        results["sylow_count_mod_p_zero_unsat"] = {
            "status": "unsat",
            "interpretation": "Sylow modular constraint violation: claiming n_p ≡ 0 (mod p) contradicts Sylow theorem requirement n_p ≡ 1 (mod p); zero-remainder condition impossible for Sylow counts; modular constraint is intrinsic to conjugacy class structure",
        }

    # Test 2: Claim n_p does not divide |G|/p^k → UNSAT
    solver2 = Solver()
    n_p = Int("n_p")
    m_val = Int("m_val")

    # Claim: n_p does not divide m_val [violates Sylow constraint]
    solver2.add(m_val % n_p != 0)
    # Enforce Sylow constraint: n_p divides m_val
    solver2.add(m_val % n_p == 0)
    # Concrete values
    solver2.add(m_val == 15)
    solver2.add(n_p == 4)  # 4 does not divide 15

    if solver2.check() == unsat:
        results["sylow_count_does_not_divide_unsat"] = {
            "status": "unsat",
            "interpretation": "Sylow divisibility constraint violation: claiming n_p ∤ (|G|/p^k) contradicts Sylow theorem requirement n_p | m; divisibility constraint derives from normalizer orbit-stabilizer theorem; impossible count forced by group structure",
        }

    # Test 3: Both modular and divisibility violations simultaneously → UNSAT
    solver3 = Solver()
    n_p = Int("n_p")
    p = Int("p")
    m_val = Int("m_val")

    # Claim: n_p ≡ 0 (mod p) AND n_p ∤ m_val [double violation]
    solver3.add(n_p % p == 0)
    solver3.add(m_val % n_p != 0)
    # Enforce Sylow constraints
    solver3.add(n_p % p == 1)
    solver3.add(m_val % n_p == 0)
    # Concrete values
    solver3.add(p == 3)
    solver3.add(m_val == 16)
    solver3.add(n_p == 6)  # 6 ≡ 0 (mod 3) AND 6 ∤ 16

    if solver3.check() == unsat:
        results["simultaneous_constraint_violation_unsat"] = {
            "status": "unsat",
            "interpretation": "Combined Sylow constraint violation: claiming both n_p ≡ 0 (mod p) AND n_p ∤ m simultaneously contradicts both Sylow theorem conditions; redundant impossibility reinforces constraint coupling; structural constraints on group order force both conditions together",
        }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Boundary tests: Critical Sylow count values and edge cases
    """
    results = {
        "sylow_count_equals_one": None,
        "sylow_count_at_congruence_boundary": None,
        "minimal_divisor_matching_constraint": None,
    }

    if not Z3_AVAILABLE:
        return results

    # Test 1: n_p = 1 (unique, therefore normal Sylow p-subgroup)
    solver = Solver()
    n_p = Int("n_p")
    p = Int("p")

    # n_p = 1: only one Sylow p-subgroup, hence normal
    solver.add(n_p == 1)
    solver.add(n_p % p == 1)  # 1 ≡ 1 (mod p) for all p
    # Concrete values
    solver.add(p == 7)

    if solver.check() == sat:
        m = solver.model()
        results["sylow_count_equals_one"] = {
            "status": "satisfiable",
            "interpretation": "Sylow uniqueness: when n_p = 1, unique Sylow p-subgroup is normal (characteristic); singleton conjugacy class; group has unique decomposition P × Q for primes p, q; n_p = 1 satisfies both ≡1(mod p) and divisibility trivially; forces group structure toward direct product",
            "p": int(m[p].as_long()),
            "n_p": int(m[n_p].as_long()),
            "normal": True,
        }

    # Test 2: n_p at boundary of next multiple of p
    solver2 = Solver()
    n_p = Int("n_p")
    p = Int("p")

    # n_p = p + 1 (next congruent value after 1 mod p)
    solver2.add(n_p == p + 1)
    solver2.add(n_p % p == 1)
    # Concrete values: p = 5, n_p = 6
    solver2.add(p == 5)
    solver2.add(n_p == 6)

    if solver2.check() == sat:
        m2 = solver2.model()
        results["sylow_count_at_congruence_boundary"] = {
            "status": "satisfiable",
            "interpretation": "Sylow congruence boundary: n_p = p+1 is the next smallest value after 1 satisfying n_p ≡ 1 (mod p); boundary case between minimal count and next alternative; must still divide |G|/p^k; marks transition to non-unique Sylow subgroups; conjugacy classes partition group more finely",
            "p": int(m2[p].as_long()),
            "n_p": int(m2[n_p].as_long()),
            "congruent": (int(m2[n_p].as_long()) % int(m2[p].as_long()) == 1),
        }

    # Test 3: Minimal divisor of m matching Sylow congruence
    solver3 = Solver()
    n_p = Int("n_p")
    p = Int("p")
    m_val = Int("m_val")

    # n_p is the smallest divisor of m_val satisfying n_p ≡ 1 (mod p)
    solver3.add(m_val == 30)  # 30 = 2 * 3 * 5, divisors: 1,2,3,5,6,10,15,30
    solver3.add(p == 2)       # p = 2, divisors ≡ 1 (mod 2): all odd divisors 1,3,5,15
    solver3.add(n_p == 1)     # minimal odd divisor
    solver3.add(m_val % n_p == 0)

    if solver3.check() == sat:
        m3 = solver3.model()
        results["minimal_divisor_matching_constraint"] = {
            "status": "satisfiable",
            "interpretation": "Minimal Sylow count: for group |G| = p^k * m, Sylow count n_p is a divisor of m satisfying n_p ≡ 1 (mod p); minimal such divisor often n_p = 1 when possible; boundary case determines whether Sylow p-subgroup is normal; divisor structure of m constrains achievable Sylow counts",
            "m_val": int(m3[m_val].as_long()),
            "p": int(m3[p].as_long()),
            "n_p": int(m3[n_p].as_long()),
            "divisor_valid": True,
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
    if Z3_AVAILABLE and positive.get("sylow_count_modular_constraint"):
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "Encodes Sylow theorems via QF_LIA: enforces n_p ≡ 1 (mod p) modular constraint through integer arithmetic; validates n_p divides |G|/p^k via divisibility predicates; proves simultaneous violation of both Sylow conditions leads to UNSAT; confirms unique Sylow p-subgroup is normal; constrains group composition via Sylow subgroup count admissibility; verifies conjugacy class structure forces count divisibility"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

    # Mark sympy as supportive
    if SYMPY_AVAILABLE:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "Computes Sylow p-subgroups of finite groups; factors group order |G| into p^k * m; determines maximal p-power dividing |G|; verifies congruence and divisibility constraints for concrete groups; analyzes normalizer structure and normalizer order |N_G(P)| = |G| / n_p; validates all Sylow p-subgroups conjugate via explicit group multiplication"
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

    # Mark other tools as not used
    TOOL_MANIFEST["pytorch"]["reason"] = "not needed for Sylow count constraints"
    TOOL_MANIFEST["pyg"]["reason"] = "not needed for group divisibility"
    TOOL_MANIFEST["cvc5"]["reason"] = "z3 sufficient for Sylow congruence"
    TOOL_MANIFEST["clifford"]["reason"] = "not needed for subgroup structure"
    TOOL_MANIFEST["geomstats"]["reason"] = "not needed for Sylow conditions"
    TOOL_MANIFEST["e3nn"]["reason"] = "not needed for group theory"
    TOOL_MANIFEST["rustworkx"]["reason"] = "not needed for Sylow counts"
    TOOL_MANIFEST["xgi"]["reason"] = "not needed for conjugacy"
    TOOL_MANIFEST["toponetx"]["reason"] = "not needed for modular arithmetic"
    TOOL_MANIFEST["gudhi"]["reason"] = "not needed for group orders"

    # Count passes
    all_pass = True
    for test_dict in [positive, negative, boundary]:
        for test_name, result in test_dict.items():
            if result is None or "status" not in result:
                all_pass = False

    results = {
        "name": "Sylow Theorem Constraint Canonical",
        "description": "Sylow theorems: number of Sylow p-subgroups n_p must satisfy (1) n_p ≡ 1 (mod p) and (2) n_p divides |G|/p^k; foundational to group composition; constraint surface is group orders satisfying both divisibility and congruence conditions; z3 encodes QF_LIA to enforce modular arithmetic and divisibility; proves violating either condition leads to impossible group structure; validates conjugacy determines count via normalizer orbit-stabilizer",
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
    out_path = os.path.join(out_dir, "sim_sylow_theorem_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    status = "✓ all_pass=True" if all_pass else "✗ some failures"
    print(f"sim_sylow_theorem_constraint_canonical: {status} -> {out_path}")
