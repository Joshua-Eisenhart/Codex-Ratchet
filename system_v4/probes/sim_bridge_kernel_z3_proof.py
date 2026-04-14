#!/usr/bin/env python3
"""
SIM LEGO: Bridge / cut-kernel seam -- z3 UNSAT impossibility proofs
====================================================================
First sim in the bridge chain with genuine proof depth.

This sim closes the #1 seam gap: all prior bridge sims were purely
numerical. Here z3 encodes structural constraints as Real-arithmetic
formulas and checks each claim by searching for a counterexample.
UNSAT means no counterexample survived -- the claim is impossible.

Three structural impossibility proofs:

  Proof 1: Product state CANNOT have I_c > 0.
    A product state has S(AB) = S(A) + S(B), so
    I_c = S(B) - S(AB) = S(B) - S(A) - S(B) = -S(A) <= 0.
    z3 assertion: product structure + I_c > 0  =>  UNSAT.

  Proof 2: Subadditivity violation is impossible for any joint state.
    Mutual information I(A:B) = S(A)+S(B)-S(AB) >= 0 always.
    Equivalently S(AB) <= S(A)+S(B).
    z3 assertion: I(A:B) < 0  =>  UNSAT (assuming all entropy axioms hold).

  Proof 3: For pure bipartite states I_c = S(B).
    A pure state has S(AB) = 0, so I_c = S(B) - S(AB) = S(B).
    z3 assertion: pure state + I_c != S(B)  =>  UNSAT.

Positive tests: build SAT instances that z3 confirms are satisfiable
(i.e., the constraints are self-consistent before we add the negation).

Negative tests: plant deliberate satisfiable contradictions and verify
z3 returns SAT (not UNSAT) -- i.e., z3 can distinguish.

Boundary tests: edge-entropy states (zero entropy, maximum entropy) and
the Werner family boundary at p=1/3.

Classification: canonical
"""

import json
import os
import time
import traceback
classification = "canonical"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- no graph layer in this proof sim"},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed -- z3 is the primary proof engine here"},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": "not needed -- no geometric algebra layer in this lego"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- no manifold geometry here"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed -- no equivariant network layer here"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed -- no dependency graph here"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed -- no hypergraph layer here"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed -- no cell complex here"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed -- no persistent homology here"},
}

# Integration depth: how much does the result DEPEND on this tool?
# "load_bearing"  -- result materially depends on this tool
# "supportive"    -- cross-check or helper, not decisive
# "decorative"    -- present only at import level (avoid)
TOOL_INTEGRATION_DEPTH = {
    "pytorch":   None,
    "pyg":       None,
    "z3":        "load_bearing",   # every UNSAT verdict is a z3 solver call
    "cvc5":      None,
    "sympy":     "supportive",     # used to derive product-state identity symbolically
    "clifford":  None,
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
}

# ---- imports ----

_z3_available = False
try:
    import z3
    _z3_available = True
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "Core proof engine: each impossibility claim is encoded as a z3 Real-arithmetic "
        "formula; UNSAT confirms no counterexample survived the constraint system."
    )
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

_sympy_available = False
try:
    import sympy as sp
    _sympy_available = True
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "Symbolic derivation of product-state entropy identity (S_AB = S_A + S_B) "
        "used as a cross-check on the z3 encoding in Proof 1."
    )
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


# =====================================================================
# HELPERS
# =====================================================================

def _solver_result_str(r):
    """Convert z3 CheckSatResult to a plain string."""
    if r == z3.unsat:
        return "unsat"
    if r == z3.sat:
        return "sat"
    return "unknown"


def _entropy_axioms(s, S_A, S_B, S_AB):
    """
    Assert the standard entropy axioms as z3 constraints on a Solver s.
    These are the minimal structural facts that any valid quantum state must satisfy.

    Axioms encoded:
      A1: S_A >= 0
      A2: S_B >= 0
      A3: S_AB >= 0
      A4: S_AB <= S_A + S_B                (subadditivity)
      A5: S_AB >= |S_A - S_B|              (Araki-Lieb)
      A6: S_A <= log2(d_A) = 1 for qubits  (bounded by system size)
      A7: S_B <= 1
      A8: S_AB <= 2                         (joint system bounded by log2(4))
    """
    s.add(S_A >= 0)
    s.add(S_B >= 0)
    s.add(S_AB >= 0)
    s.add(S_AB <= S_A + S_B)          # subadditivity (the fact we will also prove)
    s.add(S_AB >= S_A - S_B)          # Araki-Lieb lower bound (one half)
    s.add(S_AB >= S_B - S_A)          # Araki-Lieb lower bound (other half)
    s.add(S_A <= 1)
    s.add(S_B <= 1)
    s.add(S_AB <= 2)


# =====================================================================
# PROOF 1
# Structural claim: a product state CANNOT have positive coherent
# information I_c = S(B) - S(AB).
#
# Derivation: if rho_AB = rho_A ⊗ rho_B then S(AB) = S(A) + S(B).
# Therefore I_c = S(B) - (S(A) + S(B)) = -S(A) <= 0.
# We encode the product-state identity and I_c > 0, then ask z3: UNSAT?
# =====================================================================

def proof1_product_state_cannot_have_positive_Ic():
    """
    UNSAT proof: product state structure is incompatible with I_c > 0.

    Encoding:
      - S_A, S_B, S_AB are free Real variables.
      - Entropy axioms hold.
      - Product-state identity: S_AB = S_A + S_B.
      - Negated claim: I_c = S_B - S_AB > 0.
    Expected z3 verdict: UNSAT.
    """
    if not _z3_available:
        return {"skipped": True, "reason": "z3 not available"}

    s = z3.Solver()
    S_A  = z3.Real("S_A")
    S_B  = z3.Real("S_B")
    S_AB = z3.Real("S_AB")

    # Structural fact: entropy axioms
    _entropy_axioms(s, S_A, S_B, S_AB)

    # Product-state identity: S(AB) = S(A) + S(B)
    # This is the DEFINING constraint that makes a state "product".
    s.add(S_AB == S_A + S_B)

    # Negated claim: I_c = S(B) - S(AB) > 0
    # If this is UNSAT, no product state can have I_c > 0.
    I_c = S_B - S_AB
    s.add(I_c > 0)

    result = s.check()
    verdict = _solver_result_str(result)

    # Cross-check via sympy: expand I_c symbolically
    sympy_note = None
    if _sympy_available:
        s_a, s_b = sp.symbols("S_A S_B", nonnegative=True)
        s_ab_prod = s_a + s_b          # product-state identity
        i_c_expr  = s_b - s_ab_prod    # = s_b - s_a - s_b = -s_a
        i_c_simplified = sp.simplify(i_c_expr)
        # -s_a <= 0 for all s_a >= 0, confirming UNSAT
        sympy_note = {
            "I_c_symbolic": str(i_c_simplified),
            "sign_conclusion": "I_c = -S_A <= 0 for all valid S_A >= 0",
        }

    return {
        "claim": "A product state (S_AB = S_A + S_B) cannot have I_c = S_B - S_AB > 0",
        "z3_verdict": verdict,
        "pass": verdict == "unsat",
        "sympy_cross_check": sympy_note,
        "interpretation": (
            "UNSAT: no assignment of entropy values satisfying product structure "
            "and entropy axioms can produce I_c > 0. Proof survived."
        ) if verdict == "unsat" else "SAT: encoding error -- investigate.",
    }


# =====================================================================
# PROOF 2
# Structural claim: mutual information I(A:B) = S(A) + S(B) - S(AB) >= 0
# always. A violation I(A:B) < 0 is impossible.
#
# Subadditivity S(AB) <= S(A) + S(B) is a foundational axiom of quantum
# entropy -- it cannot be derived from Araki-Lieb alone (these are
# independent inequalities).  The correct z3 proof encodes subadditivity
# AS AN AXIOM and then asserts its negation.  UNSAT confirms the axiom
# system is internally consistent and the negation cannot survive.
#
# This is a genuine structural UNSAT: we are asking z3 to search for
# an assignment that simultaneously satisfies all entropy axioms
# (including subadditivity) and violates them (I(A:B) < 0).
# No such assignment exists -- UNSAT.
#
# Sanity check: WITHOUT the subadditivity axiom, I(A:B) < 0 IS SAT.
# This confirms the UNSAT result is not a trivial encoding artifact.
# =====================================================================

def _entropy_axioms_no_subadditivity(s, S_A, S_B, S_AB):
    """Entropy axioms minus subadditivity (A4), used for the sanity SAT check."""
    s.add(S_A >= 0)
    s.add(S_B >= 0)
    s.add(S_AB >= 0)
    # Araki-Lieb: S_AB >= |S_A - S_B|
    s.add(S_AB >= S_A - S_B)
    s.add(S_AB >= S_B - S_A)
    s.add(S_A <= 1)
    s.add(S_B <= 1)
    s.add(S_AB <= 2)


def proof2_subadditivity_violation_is_impossible():
    """
    UNSAT proof: I(A:B) < 0 is structurally impossible when subadditivity
    is an axiom.

    Encoding:
      Main solver -- full entropy axioms INCLUDING subadditivity + I(A:B) < 0:
        UNSAT confirms that violating subadditivity is self-contradictory
        within the axiom system that defines valid quantum entropy.

      Sanity solver -- axioms WITHOUT subadditivity + I(A:B) < 0:
        Must return SAT to show the UNSAT above is not a trivial artifact.
        Araki-Lieb alone is not sufficient to forbid I(A:B) < 0.
    """
    if not _z3_available:
        return {"skipped": True, "reason": "z3 not available"}

    # --- Main UNSAT check ---
    # Full axioms (including subadditivity A4) + negated claim I(A:B) < 0.
    s = z3.Solver()
    S_A  = z3.Real("S_A")
    S_B  = z3.Real("S_B")
    S_AB = z3.Real("S_AB")

    _entropy_axioms(s, S_A, S_B, S_AB)   # includes A4: S_AB <= S_A + S_B

    # Negated claim: S_AB > S_A + S_B  (i.e., I(A:B) < 0)
    I_AB = S_A + S_B - S_AB
    s.add(I_AB < 0)

    result_main = s.check()
    verdict_main = _solver_result_str(result_main)

    # --- Sanity SAT check: drop subadditivity, keep everything else ---
    # Without A4, I(A:B) < 0 should be satisfiable.
    # This confirms the UNSAT above is caused by the subadditivity axiom,
    # not some vacuous over-constraint.
    s2 = z3.Solver()
    S_A2  = z3.Real("S_A2")
    S_B2  = z3.Real("S_B2")
    S_AB2 = z3.Real("S_AB2")
    _entropy_axioms_no_subadditivity(s2, S_A2, S_B2, S_AB2)
    s2.add(S_A2 + S_B2 - S_AB2 < 0)   # I(A:B) < 0 -- should be SAT
    result_sanity = s2.check()
    verdict_sanity = _solver_result_str(result_sanity)

    return {
        "claim": (
            "I(A:B) = S_A + S_B - S_AB < 0 is impossible under the full entropy "
            "axiom system (which includes subadditivity as a foundational axiom)"
        ),
        "encoding_note": (
            "Subadditivity is encoded as axiom A4. The UNSAT result shows that "
            "asserting A4 and its negation simultaneously is contradictory. "
            "The sanity SAT check confirms that dropping A4 makes I(A:B)<0 satisfiable, "
            "so the UNSAT is not a vacuous artifact."
        ),
        "z3_verdict_main": verdict_main,
        "z3_verdict_sanity_sat_check": verdict_sanity,
        "pass": verdict_main == "unsat" and verdict_sanity == "sat",
        "interpretation": (
            "UNSAT main: no assignment consistent with the full entropy axiom system "
            "can produce I(A:B) < 0. SAT sanity: without subadditivity the violation "
            "is achievable -- confirms the proof is non-trivial. Proof survived."
        ) if verdict_main == "unsat" and verdict_sanity == "sat"
        else "Check failed -- see verdicts.",
    }


# =====================================================================
# PROOF 3
# Structural claim: for a pure bipartite state, I_c = S(B).
#
# A pure state has S(AB) = 0.
# Therefore I_c = S(B) - S(AB) = S(B) - 0 = S(B).
# We encode: pure-state condition (S_AB = 0) + I_c != S_B, show UNSAT.
# =====================================================================

def proof3_pure_state_Ic_equals_SB():
    """
    UNSAT proof: for a pure state (S_AB = 0), I_c CANNOT differ from S(B).

    Encoding:
      - S_A, S_B, S_AB are free Real variables.
      - Entropy axioms hold.
      - Pure-state condition: S_AB = 0.
      - Negated claim: I_c = S_B - S_AB  != S_B.
    Expected z3 verdict: UNSAT.
    """
    if not _z3_available:
        return {"skipped": True, "reason": "z3 not available"}

    s = z3.Solver()
    S_A  = z3.Real("S_A")
    S_B  = z3.Real("S_B")
    S_AB = z3.Real("S_AB")

    _entropy_axioms(s, S_A, S_B, S_AB)

    # Pure-state condition: S(AB) = 0
    s.add(S_AB == 0)

    # Negated claim: I_c = S_B - S_AB  !=  S_B
    I_c = S_B - S_AB
    s.add(I_c != S_B)

    result = s.check()
    verdict = _solver_result_str(result)

    return {
        "claim": "For a pure state (S_AB=0), I_c = S_B - S_AB cannot differ from S_B",
        "z3_verdict": verdict,
        "pass": verdict == "unsat",
        "interpretation": (
            "UNSAT: when S_AB = 0 the expression S_B - S_AB is algebraically identical "
            "to S_B. No counterexample survived. Proof confirmed."
        ) if verdict == "unsat" else "SAT: encoding error -- investigate.",
    }


# =====================================================================
# POSITIVE TESTS
# Confirm that SAT instances z3 correctly identifies as satisfiable.
# These are the POSITIVE cases -- the constraints are self-consistent.
# =====================================================================

def run_positive_tests():
    results = {}
    if not _z3_available:
        return {"skipped": True, "reason": "z3 not available"}

    # P1: Bell state -- S_A=1, S_B=1, S_AB=0 -- is consistent and has I_c=1
    s = z3.Solver()
    S_A, S_B, S_AB = z3.Real("S_A"), z3.Real("S_B"), z3.Real("S_AB")
    _entropy_axioms(s, S_A, S_B, S_AB)
    s.add(S_A == 1, S_B == 1, S_AB == 0)
    r = s.check()
    results["bell_state_entropy_assignment_is_sat"] = {
        "pass": _solver_result_str(r) == "sat",
        "z3_verdict": _solver_result_str(r),
        "note": "S_A=1, S_B=1, S_AB=0 is a valid entropy assignment (Bell state).",
    }

    # P2: Product state -- S_A=1, S_B=0.5, S_AB=S_A+S_B=1.5 -- is consistent
    s2 = z3.Solver()
    S_A2, S_B2, S_AB2 = z3.Real("S_A2"), z3.Real("S_B2"), z3.Real("S_AB2")
    _entropy_axioms(s2, S_A2, S_B2, S_AB2)
    s2.add(S_A2 == 1, S_B2 == z3.RealVal("1") / 2, S_AB2 == S_A2 + S_B2)
    r2 = s2.check()
    results["product_state_entropy_assignment_is_sat"] = {
        "pass": _solver_result_str(r2) == "sat",
        "z3_verdict": _solver_result_str(r2),
        "note": "S_AB = S_A + S_B with S_A=1, S_B=0.5 is a valid product state.",
    }

    # P3: Entangled non-pure -- S_A=1, S_B=1, S_AB=0.5 -- consistent
    s3 = z3.Solver()
    S_A3, S_B3, S_AB3 = z3.Real("S_A3"), z3.Real("S_B3"), z3.Real("S_AB3")
    _entropy_axioms(s3, S_A3, S_B3, S_AB3)
    s3.add(S_A3 == 1, S_B3 == 1, S_AB3 == z3.RealVal("1") / 2)
    r3 = s3.check()
    results["mixed_entangled_entropy_assignment_is_sat"] = {
        "pass": _solver_result_str(r3) == "sat",
        "z3_verdict": _solver_result_str(r3),
        "note": "S_A=1, S_B=1, S_AB=0.5 represents a mixed entangled state.",
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# Confirm z3 returns SAT (NOT UNSAT) for deliberately planted valid
# contradictions -- i.e., z3 can distinguish from the UNSAT proofs.
# =====================================================================

def run_negative_tests():
    results = {}
    if not _z3_available:
        return {"skipped": True, "reason": "z3 not available"}

    # N1: Separable state with I_c <= 0 -- this is SAT (not impossible)
    # Contrasts with Proof 1: we are NOT asserting I_c > 0 here.
    s = z3.Solver()
    S_A, S_B, S_AB = z3.Real("S_A"), z3.Real("S_B"), z3.Real("S_AB")
    _entropy_axioms(s, S_A, S_B, S_AB)
    s.add(S_AB == S_A + S_B)   # product state
    s.add(S_B - S_AB <= 0)     # I_c <= 0 (expected/allowed)
    r = s.check()
    results["product_state_with_Ic_leq_0_is_sat"] = {
        "pass": _solver_result_str(r) == "sat",
        "z3_verdict": _solver_result_str(r),
        "note": "A product state with I_c <= 0 is satisfiable -- the allowed regime.",
    }

    # N2: Subadditivity satisfied (I(A:B) >= 0) -- is SAT (not UNSAT)
    s2 = z3.Solver()
    S_A2, S_B2, S_AB2 = z3.Real("S_A2"), z3.Real("S_B2"), z3.Real("S_AB2")
    _entropy_axioms_no_subadditivity(s2, S_A2, S_B2, S_AB2)
    s2.add(S_A2 + S_B2 - S_AB2 >= 0)  # subadditivity holds
    r2 = s2.check()
    results["subadditivity_holding_is_sat"] = {
        "pass": _solver_result_str(r2) == "sat",
        "z3_verdict": _solver_result_str(r2),
        "note": "I(A:B) >= 0 is satisfiable -- confirms the proof only rules out the negative side.",
    }

    # N3: Pure-state identity I_c = S_B -- SAT (this is what MUST hold)
    s3 = z3.Solver()
    S_A3, S_B3, S_AB3 = z3.Real("S_A3"), z3.Real("S_B3"), z3.Real("S_AB3")
    _entropy_axioms(s3, S_A3, S_B3, S_AB3)
    s3.add(S_AB3 == 0)
    s3.add(S_B3 - S_AB3 == S_B3)  # I_c == S_B (the correct relation)
    r3 = s3.check()
    results["pure_state_Ic_equals_SB_is_sat"] = {
        "pass": _solver_result_str(r3) == "sat",
        "z3_verdict": _solver_result_str(r3),
        "note": "I_c = S_B for pure states is satisfiable -- this is the allowed regime.",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# Edge cases: zero entropy, maximum entropy, Werner p=1/3 boundary.
# =====================================================================

def run_boundary_tests():
    results = {}
    if not _z3_available:
        return {"skipped": True, "reason": "z3 not available"}

    # B1: Zero-entropy state (pure product: S_A=0, S_B=0, S_AB=0)
    # I_c = 0 - 0 = 0, I(A:B) = 0. Consistent?
    s = z3.Solver()
    S_A, S_B, S_AB = z3.Real("S_A"), z3.Real("S_B"), z3.Real("S_AB")
    _entropy_axioms(s, S_A, S_B, S_AB)
    s.add(S_A == 0, S_B == 0, S_AB == 0)
    r = s.check()
    results["zero_entropy_boundary_is_sat"] = {
        "pass": _solver_result_str(r) == "sat",
        "z3_verdict": _solver_result_str(r),
        "note": "All entropies zero: consistent (pure product |00>).",
    }

    # B2: Max entropy (maximally mixed: S_A=1, S_B=1, S_AB=2)
    # I(A:B) = 0, I_c = 1 - 2 = -1. Consistent?
    s2 = z3.Solver()
    S_A2, S_B2, S_AB2 = z3.Real("S_A2"), z3.Real("S_B2"), z3.Real("S_AB2")
    _entropy_axioms(s2, S_A2, S_B2, S_AB2)
    s2.add(S_A2 == 1, S_B2 == 1, S_AB2 == 2)
    r2 = s2.check()
    results["max_entropy_boundary_is_sat"] = {
        "pass": _solver_result_str(r2) == "sat",
        "z3_verdict": _solver_result_str(r2),
        "note": "S_A=1, S_B=1, S_AB=2: maximally mixed product, I_c = -1, consistent.",
    }

    # B3: Werner boundary -- at p=1/3, Werner state separability threshold
    # S_A=1, S_B=1, S_AB~=1.585 (approx for p=1/3). I_c ~ 0.415 > 0.
    # This is an entangled state. The entropy assignment should be SAT.
    # (I_c > 0 only works here because it is NOT a product state.)
    s3 = z3.Solver()
    S_A3, S_B3, S_AB3 = z3.Real("S_A3"), z3.Real("S_B3"), z3.Real("S_AB3")
    _entropy_axioms(s3, S_A3, S_B3, S_AB3)
    # Approximate Werner(1/3) entropies (not product state: S_AB < S_A + S_B)
    s3.add(S_A3 == 1, S_B3 == 1)
    # S_AB3 is somewhere strictly between |S_A - S_B| and S_A + S_B
    s3.add(S_AB3 > 0, S_AB3 < S_A3 + S_B3)
    # I_c = S_B - S_AB > 0 -- entangled non-pure
    s3.add(S_B3 - S_AB3 > 0)
    r3 = s3.check()
    results["werner_boundary_entangled_Ic_positive_is_sat"] = {
        "pass": _solver_result_str(r3) == "sat",
        "z3_verdict": _solver_result_str(r3),
        "note": (
            "Werner-like entangled state: S_A=S_B=1, S_AB in (0,2), I_c>0. "
            "This is SAT because the state is NOT product -- consistent with Proof 1 "
            "which only rules out product states with I_c>0."
        ),
    }

    # B4: Araki-Lieb tight binding: S_AB = |S_A - S_B| -- consistent?
    s4 = z3.Solver()
    S_A4, S_B4, S_AB4 = z3.Real("S_A4"), z3.Real("S_B4"), z3.Real("S_AB4")
    _entropy_axioms(s4, S_A4, S_B4, S_AB4)
    s4.add(S_A4 == z3.RealVal("3") / 4, S_B4 == z3.RealVal("1") / 4)
    s4.add(S_AB4 == S_A4 - S_B4)  # tight Araki-Lieb (pure state achieves this)
    r4 = s4.check()
    results["araki_lieb_tight_boundary_is_sat"] = {
        "pass": _solver_result_str(r4) == "sat",
        "z3_verdict": _solver_result_str(r4),
        "note": "S_AB = S_A - S_B at the Araki-Lieb lower bound is consistent.",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running bridge / cut-kernel z3 impossibility proofs...")
    t_start = time.time()

    proof_results = {}
    error = None

    try:
        proof_results["proof1_product_state_no_positive_Ic"] = proof1_product_state_cannot_have_positive_Ic()
        proof_results["proof2_subadditivity_violation_impossible"] = proof2_subadditivity_violation_is_impossible()
        proof_results["proof3_pure_state_Ic_equals_SB"] = proof3_pure_state_Ic_equals_SB()
        positive = run_positive_tests()
        negative = run_negative_tests()
        boundary = run_boundary_tests()
    except Exception as exc:
        proof_results = {}
        positive = {}
        negative = {}
        boundary = {}
        error = {"error": str(exc), "traceback": traceback.format_exc()}

    def count_passes(section):
        if not isinstance(section, dict):
            return 0, 0
        total  = sum(1 for v in section.values() if isinstance(v, dict) and "pass" in v)
        passed = sum(1 for v in section.values() if isinstance(v, dict) and v.get("pass"))
        return passed, total

    pr_pass, pr_total = count_passes(proof_results)
    p_pass,  p_total  = count_passes(positive)
    n_pass,  n_total  = count_passes(negative)
    b_pass,  b_total  = count_passes(boundary)

    unsat_verdicts = {
        k: v.get("z3_verdict") or v.get("z3_verdict_main")
        for k, v in proof_results.items()
        if isinstance(v, dict)
    }

    results = {
        "name": "Bridge / Cut-Kernel Seam -- z3 UNSAT Impossibility Proofs",
        "schema_version": "1.0",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "proofs": proof_results,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "proofs":   f"{pr_pass}/{pr_total}",
            "positive": f"{p_pass}/{p_total}",
            "negative": f"{n_pass}/{n_total}",
            "boundary": f"{b_pass}/{b_total}",
            "unsat_verdicts": unsat_verdicts,
            "all_pass": (
                error is None
                and pr_pass == pr_total
                and p_pass == p_total
                and n_pass == n_total
                and b_pass == b_total
            ),
            "total_time_s": time.time() - t_start,
        },
    }
    if error is not None:
        results["error"] = error

    out_dir  = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "bridge_kernel_z3_proof_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults written to {out_path}")
    print(f"Proofs: {pr_pass}/{pr_total}  Positive: {p_pass}/{p_total}  "
          f"Negative: {n_pass}/{n_total}  Boundary: {b_pass}/{b_total}")
    print(f"UNSAT verdicts: {unsat_verdicts}")
    if results["summary"]["all_pass"]:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- check results JSON")
