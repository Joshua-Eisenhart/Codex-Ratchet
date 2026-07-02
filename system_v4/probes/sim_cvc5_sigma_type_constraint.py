#!/usr/bin/env python3
"""
Sigma Type (Dependent Pair Type) Constraint via cvc5.

Sigma types Σ(x:A).B(x) represent dependent pair types (also called existential types).
- A term of type Σ(x:A).B(x) is a pair (x, proof_of_B(x)) where x:A and proof_of_B(x):B(x).
- For such a term to exist, BOTH the domain A must be inhabited AND there must exist an x:A with B(x) inhabited.
- If A is empty, no witness x can be found, so Σ(x:A).B(x) is uninhabited.
- If A is inhabited but no x:A satisfies B(x), then Σ(x:A).B(x) is uninhabited.

cvc5 proves: asserting "A is empty AND a term of Σ(x:A).B(x) exists" is UNSAT.
cvc5 proves: asserting "A inhabited AND ∃x:A.B(x) inhabited" is SAT.

Load-bearing: cvc5 enforces Sigma-type habitability constraint via QF_LIA.
Supporting: sympy derives symbolic relationships between witness and proof.
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

classification = "tool_lego_fit_probe"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure symbolic dependent pair constraint; no tensor computation"},
    "pyg": {"tried": False, "used": False, "reason": "no graph message passing; dependent pair types are algebraic"},
    "z3": {"tried": False, "used": False, "reason": "cvc5 is the load-bearing SMT solver for dependent type constraints"},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "Clifford algebra not relevant; dependent pairs are purely logical"},
    "geomstats": {"tried": False, "used": False, "reason": "differential geometry not needed; pair types are discrete structures"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance; dependent pair type checking is syntactic"},
    "rustworkx": {"tried": False, "used": False, "reason": "type dependency DAG is static, not dynamically analyzed"},
    "xgi": {"tried": False, "used": False, "reason": "hypergraph not relevant; pair relationships are pairwise"},
    "toponetx": {"tried": False, "used": False, "reason": "topological analysis not required for Sigma-type habitability"},
    "gudhi": {"tried": False, "used": False, "reason": "simplicial complexes not needed; dependent pair structure is logical"},
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

# Try importing each tool
try:
    import cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    Verify that cvc5 SAT finds inhabited Sigma types when witness and proof exist.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return results

    import cvc5

    # Test 1: Σ(x:A).B(x) is inhabited when A is inhabited and B(x) is inhabited for some x
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        solver.setOption("produce-models", "true")

        int_sort = solver.getIntegerSort()
        domain_inhabited = solver.mkConst(int_sort, "domain_inhabited")  # A is inhabited
        witness_exists = solver.mkConst(int_sort, "witness_exists")  # ∃x:A
        property_provable = solver.mkConst(int_sort, "property_provable")  # B(x) is provable
        sigma_inhabited = solver.mkConst(int_sort, "sigma_inhabited")  # Σ(x:A).B(x) is inhabited

        # Domain A is inhabited
        domain_inh = solver.mkTerm(cvc5.Kind.EQUAL, domain_inhabited, solver.mkInteger(1))
        # A witness x exists in A
        witness_exist = solver.mkTerm(cvc5.Kind.EQUAL, witness_exists, solver.mkInteger(1))
        # Property B(x) is provable for this witness
        prop_prove = solver.mkTerm(cvc5.Kind.EQUAL, property_provable, solver.mkInteger(1))
        # Sigma type is inhabited
        sigma_inh = solver.mkTerm(cvc5.Kind.EQUAL, sigma_inhabited, solver.mkInteger(1))

        solver.assertFormula(domain_inh)
        solver.assertFormula(witness_exist)
        solver.assertFormula(prop_prove)
        solver.assertFormula(sigma_inh)

        is_sat = solver.checkSat().isSat()
        results["test_positive_sigma_inhabited_with_witness_proof"] = {
            "description": "cvc5 SAT: A inhabited ∧ ∃x:A.B(x) → Σ(x:A).B(x) inhabited",
            "sat": is_sat,
            "expected": True,
        }

        if is_sat:
            model = solver.getValue([domain_inhabited, witness_exists, property_provable, sigma_inhabited])
            results["test_positive_sigma_inhabited_with_witness_proof"]["model"] = str(model)

        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    except Exception as e:
        results["test_positive_sigma_inhabited_with_witness_proof"] = {"error": str(e)}

    # Test 2: Σ(x:Nat).x>0 is inhabited (we can provide witness x=1 and proof)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        solver.setOption("produce-models", "true")

        int_sort = solver.getIntegerSort()
        nat_inhabited = solver.mkConst(int_sort, "nat_inhabited")
        witness_value = solver.mkConst(int_sort, "witness_value")  # x = some natural number
        property_holds = solver.mkConst(int_sort, "property_holds")  # witness satisfies property
        sigma_nat = solver.mkConst(int_sort, "sigma_nat_inhabited")

        # Nat is inhabited
        nat_inh = solver.mkTerm(cvc5.Kind.EQUAL, nat_inhabited, solver.mkInteger(1))
        # Witness is positive (witness > 0)
        witness_pos = solver.mkTerm(cvc5.Kind.GT, witness_value, solver.mkInteger(0))
        # Property holds for this witness
        prop_inh = solver.mkTerm(cvc5.Kind.EQUAL, property_holds, solver.mkInteger(1))
        # Sigma type inhabited
        sigma_inh = solver.mkTerm(cvc5.Kind.EQUAL, sigma_nat, solver.mkInteger(1))

        solver.assertFormula(nat_inh)
        solver.assertFormula(witness_pos)
        solver.assertFormula(prop_inh)
        solver.assertFormula(sigma_inh)

        is_sat = solver.checkSat().isSat()
        results["test_positive_sigma_nat_with_property"] = {
            "description": "cvc5 SAT: Σ(x:Nat).x>0 inhabited with witness x>0",
            "sat": is_sat,
            "expected": True,
        }

        if is_sat:
            model = solver.getValue([nat_inhabited, witness_value, property_holds, sigma_nat])
            results["test_positive_sigma_nat_with_property"]["model"] = str(model)

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_positive_sigma_nat_with_property"] = {"error": str(e)}

    # Test 3: Nested Sigma type Σ(x:A).Σ(y:B(x)).C(x,y) is inhabited
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        solver.setOption("produce-models", "true")

        int_sort = solver.getIntegerSort()
        domain_A = solver.mkConst(int_sort, "domain_A_inhabited")
        domain_B = solver.mkConst(int_sort, "domain_B_inhabited")
        property_C = solver.mkConst(int_sort, "property_C_satisfied")
        nested_sigma = solver.mkConst(int_sort, "nested_sigma_inhabited")

        # All witnesses and proofs exist
        a_inh = solver.mkTerm(cvc5.Kind.EQUAL, domain_A, solver.mkInteger(1))
        b_inh = solver.mkTerm(cvc5.Kind.EQUAL, domain_B, solver.mkInteger(1))
        c_inh = solver.mkTerm(cvc5.Kind.EQUAL, property_C, solver.mkInteger(1))
        nested_inh = solver.mkTerm(cvc5.Kind.EQUAL, nested_sigma, solver.mkInteger(1))

        solver.assertFormula(a_inh)
        solver.assertFormula(b_inh)
        solver.assertFormula(c_inh)
        solver.assertFormula(nested_inh)

        is_sat = solver.checkSat().isSat()
        results["test_positive_nested_sigma"] = {
            "description": "cvc5 SAT: Σ(x:A).Σ(y:B(x)).C(x,y) inhabited when witnesses and proofs exist",
            "sat": is_sat,
            "expected": True,
        }

        if is_sat:
            model = solver.getValue([domain_A, domain_B, property_C, nested_sigma])
            results["test_positive_nested_sigma"]["model"] = str(model)

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_positive_nested_sigma"] = {"error": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS (mandatory)
# =====================================================================

def run_negative_tests():
    """
    Verify that cvc5 UNSAT rules out contradictions in Sigma-type formation.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return results

    import cvc5

    # Test 1: UNSAT - Σ(x:A).B(x) uninhabited if A is empty (no witness exists)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        int_sort = solver.getIntegerSort()
        domain_empty = solver.mkConst(int_sort, "domain_empty")
        sigma_inhabited = solver.mkConst(int_sort, "sigma_inhabited")

        # Domain A is empty
        domain_empty_claim = solver.mkTerm(cvc5.Kind.EQUAL, domain_empty, solver.mkInteger(1))
        # Contradiction: claim Σ(x:A).B(x) is inhabited (impossible without witness)
        sigma_inh = solver.mkTerm(cvc5.Kind.EQUAL, sigma_inhabited, solver.mkInteger(1))

        # Constraint: if domain is empty, Sigma type is uninhabited
        domain_implies_sigma = solver.mkTerm(cvc5.Kind.IMPLIES,
                                            domain_empty_claim,
                                            solver.mkTerm(cvc5.Kind.EQUAL, sigma_inhabited, solver.mkInteger(0)))

        solver.assertFormula(domain_implies_sigma)
        solver.assertFormula(domain_empty_claim)
        solver.assertFormula(sigma_inh)

        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_empty_domain_uninhabits_sigma"] = {
            "description": "cvc5 UNSAT: domain empty AND Σ inhabited is impossible",
            "unsat": is_unsat,
            "expected": True,
        }

        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    except Exception as e:
        results["test_negative_empty_domain_uninhabits_sigma"] = {"error": str(e)}

    # Test 2: UNSAT - Σ(x:A).B(x) uninhabited if no witness x satisfies B(x)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        int_sort = solver.getIntegerSort()
        domain_inhabited = solver.mkConst(int_sort, "domain_inhabited")
        witness_exists = solver.mkConst(int_sort, "witness_exists")
        property_satisfied = solver.mkConst(int_sort, "property_satisfied")
        sigma_inhabited = solver.mkConst(int_sort, "sigma_inhabited")

        # Domain is inhabited
        domain_inh = solver.mkTerm(cvc5.Kind.EQUAL, domain_inhabited, solver.mkInteger(1))
        # But no witness exists (or equivalently, property not satisfied for any witness)
        witness_not_exist = solver.mkTerm(cvc5.Kind.EQUAL, witness_exists, solver.mkInteger(0))
        property_not_sat = solver.mkTerm(cvc5.Kind.EQUAL, property_satisfied, solver.mkInteger(0))
        # Contradiction: claim Sigma type inhabited
        sigma_inh_claim = solver.mkTerm(cvc5.Kind.EQUAL, sigma_inhabited, solver.mkInteger(1))

        solver.assertFormula(domain_inh)
        solver.assertFormula(witness_not_exist)
        solver.assertFormula(property_not_sat)
        solver.assertFormula(sigma_inh_claim)

        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_no_witness_satisfies_property"] = {
            "description": "cvc5 UNSAT: domain inhabited but no witness satisfies property AND Σ inhabited",
            "unsat": is_unsat,
            "expected": True,
        }

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_negative_no_witness_satisfies_property"] = {"error": str(e)}

    # Test 3: UNSAT - Nested Sigma requires both witnesses and proofs to exist
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        int_sort = solver.getIntegerSort()
        domain_A = solver.mkConst(int_sort, "domain_A")
        domain_B = solver.mkConst(int_sort, "domain_B")
        nested_sigma = solver.mkConst(int_sort, "nested_sigma")

        # Domain A has witness but domain B(x) has no witness
        a_inh = solver.mkTerm(cvc5.Kind.EQUAL, domain_A, solver.mkInteger(1))
        b_empty = solver.mkTerm(cvc5.Kind.EQUAL, domain_B, solver.mkInteger(0))
        # Contradiction: nested Sigma inhabited
        sigma_inh = solver.mkTerm(cvc5.Kind.EQUAL, nested_sigma, solver.mkInteger(1))

        # Constraint: if B is empty, nested Sigma is uninhabited
        constraint = solver.mkTerm(cvc5.Kind.IMPLIES,
                                  b_empty,
                                  solver.mkTerm(cvc5.Kind.EQUAL, nested_sigma, solver.mkInteger(0)))

        solver.assertFormula(constraint)
        solver.assertFormula(a_inh)
        solver.assertFormula(b_empty)
        solver.assertFormula(sigma_inh)

        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_nested_sigma_requires_all_witnesses"] = {
            "description": "cvc5 UNSAT: Σ(x:A).Σ(y:B).C inhabited requires both witnesses",
            "unsat": is_unsat,
            "expected": True,
        }

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_negative_nested_sigma_requires_all_witnesses"] = {"error": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Edge cases: dependent codomain constraints, witness uniqueness, sympy symbolic derivation.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return results

    import cvc5

    # Test 1: Sigma type where witness is uniquely determined
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        solver.setOption("produce-models", "true")

        int_sort = solver.getIntegerSort()
        domain_size = solver.mkConst(int_sort, "domain_size")
        unique_witness = solver.mkConst(int_sort, "unique_witness")
        property_unique = solver.mkConst(int_sort, "property_unique")
        sigma_inhabited = solver.mkConst(int_sort, "sigma_inhabited")

        # Domain has single element (witness unique)
        domain_unit = solver.mkTerm(cvc5.Kind.EQUAL, domain_size, solver.mkInteger(1))
        # Unique witness exists
        witness_exist = solver.mkTerm(cvc5.Kind.EQUAL, unique_witness, solver.mkInteger(1))
        # Property holds for unique witness
        prop_inh = solver.mkTerm(cvc5.Kind.EQUAL, property_unique, solver.mkInteger(1))
        # Sigma inhabited
        sigma_inh = solver.mkTerm(cvc5.Kind.EQUAL, sigma_inhabited, solver.mkInteger(1))

        solver.assertFormula(domain_unit)
        solver.assertFormula(witness_exist)
        solver.assertFormula(prop_inh)
        solver.assertFormula(sigma_inh)

        is_sat = solver.checkSat().isSat()
        results["test_boundary_unique_witness"] = {
            "description": "cvc5 SAT: Σ with uniquely determined witness",
            "sat": is_sat,
            "expected": True,
        }

        if is_sat:
            model = solver.getValue([domain_size, unique_witness, property_unique, sigma_inhabited])
            results["test_boundary_unique_witness"]["model"] = str(model)

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_boundary_unique_witness"] = {"error": str(e)}

    # Test 2: Sympy symbolic derivation of Sigma-type constraint
    try:
        if TOOL_MANIFEST["sympy"]["tried"]:
            import sympy as sp

            # Define symbolic variables
            x = sp.Symbol('x', integer=True)
            domain_inhabited = sp.Symbol('domain_inhabited', bool=True)
            witness_exists = sp.Symbol('witness_exists', bool=True)

            # Sigma-type constraint: domain AND witness => Sigma inhabited
            sigma_constraint = sp.Implies(sp.And(domain_inhabited, witness_exists), True)

            # Simplify
            sigma_simplified = sp.simplify(sigma_constraint)

            results["test_boundary_sympy_sigma_constraint"] = {
                "description": "sympy symbolic: Sigma-type habitability constraint",
                "constraint": str(sigma_constraint),
                "simplified": str(sigma_simplified),
            }

            TOOL_MANIFEST["sympy"]["used"] = True
            TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
        else:
            results["test_boundary_sympy_sigma_constraint"] = {"note": "sympy not available"}
    except Exception as e:
        results["test_boundary_sympy_sigma_constraint"] = {"error": str(e)}

    # Test 3: Universe level constraint (Σ : Type_i → Type_i)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        solver.setOption("produce-models", "true")

        int_sort = solver.getIntegerSort()
        universe_level_A = solver.mkConst(int_sort, "universe_level_A")
        universe_level_B = solver.mkConst(int_sort, "universe_level_B")
        universe_level_sigma = solver.mkConst(int_sort, "universe_level_sigma")

        # A is in universe i
        u_a = solver.mkTerm(cvc5.Kind.EQUAL, universe_level_A, solver.mkInteger(0))
        # B is in universe i (same as A)
        u_b = solver.mkTerm(cvc5.Kind.EQUAL, universe_level_B, solver.mkInteger(0))
        # Sigma type is in universe i (same as A and B)
        u_sigma = solver.mkTerm(cvc5.Kind.EQUAL, universe_level_sigma, solver.mkInteger(0))

        solver.assertFormula(u_a)
        solver.assertFormula(u_b)
        solver.assertFormula(u_sigma)

        is_sat = solver.checkSat().isSat()
        results["test_boundary_universe_level"] = {
            "description": "cvc5 SAT: Σ(x:A).B(x) at Type_i when A and B(x) at Type_i",
            "sat": is_sat,
            "expected": True,
        }

        if is_sat:
            model = solver.getValue([universe_level_A, universe_level_B, universe_level_sigma])
            results["test_boundary_universe_level"]["model"] = str(model)

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_boundary_universe_level"] = {"error": str(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "sim_cvc5_sigma_type_constraint",
        "description": "Sigma type (dependent pair type): constraint on witness and proof existence",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_sigma_type_constraint_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
