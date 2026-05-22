#!/usr/bin/env python3
"""
IGT 4-Ring Operator Family (classical_baseline)
================================================

The IGT (Information Geometry Topology) system uses Z_4 (the cyclic group
of order 4) as its primitive structure. This sim establishes the natural
operator family on the 4-ring: shift T, reflection R, and doubling map D.

Key findings from prior sim_igt_ring_topology_coupling.py:
- IGT 4-ring embeds into checkerboard at even positions
- CW/CCW chirality is preserved under embedding
- z3 UNSAT on chirality reversal

This sim establishes the OPERATORS that act on that ring:

1. Shift T: T(x) = x+1 mod 4  — generates Z_4, order 4
2. Reflection R: R(x) = -x mod 4 (R(0)=0,R(1)=3,R(2)=2,R(3)=1), order 2
3. Doubling map D: D(x) = 2x mod 4  — 2:1 map, image = {0,2}, kernel = {0,2}
4. Composition T∘R vs R∘T — tests non-commutativity (dihedral structure)

Entropy of operators (as maps on the uniform distribution over Z_4):
- S(T) = 0:       bijection, all outputs equally likely, no information destroyed
- S(D) = log(2):  2:1 collapse {0,1,2,3}->{0,2,0,2}, exactly 1 bit destroyed

Rosetta log(2) pattern: S(D) = log(2) for the doubling map on Z_4 is the
SAME structural constant as:
  - SU(2)->SO(3) double-cover: log(2)
  - O(3)->SO(3) orientation removal: log(2)
  - Sp(6) bond expansion from SU(3): log(2)
All arise from a Z_2 quotient action.

Classical baseline: permutation matrices via numpy, formal group theory via
sympy, structural impossibility proofs via z3. No genuine quantum algebra.
"""

import json
import math
import os
import sys
import traceback

import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False,
                  "reason": "not needed -- Z_4 operator algebra is finite and exact; no autograd required"},
    "pyg":       {"tried": False, "used": False,
                  "reason": "not needed -- operator family acts on 4-element set, not a graph with message passing"},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False,
                  "reason": "not needed -- z3 sufficient for all UNSAT structural proofs here"},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False,
                  "reason": "not needed -- Z_4 ring operators do not require Clifford algebra"},
    "geomstats": {"tried": False, "used": False,
                  "reason": "not needed -- no Riemannian manifold structure in discrete group operators"},
    "e3nn":      {"tried": False, "used": False,
                  "reason": "not needed -- no SE(3)/SO(3) equivariant layer structure required"},
    "rustworkx": {"tried": False, "used": False,
                  "reason": "not needed -- Cayley graph of Z_4 is trivially linear, no graph library needed"},
    "xgi":       {"tried": False, "used": False,
                  "reason": "not needed -- operator family structure is not irreducibly triadic"},
    "toponetx":  {"tried": False, "used": False,
                  "reason": "not needed -- no simplicial/cell complex structure in Z_4 operator family"},
    "gudhi":     {"tried": False, "used": False,
                  "reason": "not needed -- no persistent homology required for discrete group operators"},
}

classification = "classical_baseline"
divergence_log = [
    "Classical comparator/control surface only: this runner does not promote a nonclassical, formal-scout, bridge, axis-level, or canonical proof claim.",
]

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   None,
    "pyg":       None,
    "z3":        "load_bearing",
    "cvc5":      None,
    "sympy":     "load_bearing",
    "clifford":  None,
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
}

# =====================================================================
# IMPORTS
# =====================================================================

try:
    from z3 import (
        Solver, Int, Bool, And, Or, Not, Implies,
        Distinct, ForAll, Exists, sat, unsat, Function, IntSort
    )
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "N1: UNSAT proof that no bijection f:Z_4->Z_4 has exactly 2 distinct images "
        "(a bijection on a 4-element set is surjective, contradicting image size 2). "
        "N2: UNSAT proof that T^2 = identity (shift has order 4, not 2; T^2(x)=x+2 mod 4 ≠ x for x=0,1)."
    )
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
    print("FATAL: z3 required for UNSAT proofs")
    sys.exit(1)

try:
    import sympy as sp
    from sympy.combinatorics import Permutation, PermutationGroup
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "P1: Formal group-theoretic verification that T generates Z_4 (order=4) via sympy "
        "PermutationGroup; check T^1/T^2/T^3 all distinct from identity. "
        "P2: Formal verification R has order 2 via PermutationGroup. "
        "P4: Symbolic entropy formula confirms S(D) = log(2) exactly."
    )
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    print("FATAL: sympy required for group-theoretic proofs")
    sys.exit(1)


# =====================================================================
# OPERATOR DEFINITIONS (Z_4 = {0,1,2,3})
# =====================================================================

Z4 = [0, 1, 2, 3]

def op_T(x):
    """Shift: T(x) = x+1 mod 4"""
    return (x + 1) % 4

def op_R(x):
    """Reflection: R(x) = -x mod 4"""
    return (-x) % 4

def op_D(x):
    """Doubling: D(x) = 2x mod 4"""
    return (2 * x) % 4

def op_I(x):
    """Identity"""
    return x

def compose(f, g):
    """(f∘g)(x) = f(g(x))"""
    return lambda x: f(g(x))

def op_to_table(f):
    """Return the function table [f(0),f(1),f(2),f(3)]."""
    return [f(x) for x in Z4]

def op_to_matrix(f):
    """
    Represent operator f as a 4x4 permutation/function matrix.
    M[i, j] = 1 iff f(j) = i.
    For non-injective maps (like D) rows can be zero (no preimage) or
    have multiple 1s (multiple preimages), but each column sums to 1.
    """
    M = np.zeros((4, 4), dtype=int)
    for j in Z4:
        i = f(j)
        M[i, j] = 1
    return M

def map_entropy(f):
    """
    Shannon entropy of the output distribution when the input is
    uniform over Z_4: S = -sum_i p(i) log p(i)
    where p(i) = |{x : f(x) = i}| / 4.
    """
    counts = np.zeros(4)
    for x in Z4:
        counts[f(x)] += 1
    probs = counts / 4.0
    h = 0.0
    for p in probs:
        if p > 0:
            h -= p * math.log(p)
    return h


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # ------------------------------------------------------------------
    # P1: Shift T generates Z_4
    # T^4 = identity, T^1/T^2/T^3 all distinct from identity
    # ------------------------------------------------------------------

    # Direct numpy check
    table_T  = op_to_table(op_T)
    table_T2 = op_to_table(compose(op_T, op_T))
    table_T3 = op_to_table(compose(op_T, compose(op_T, op_T)))
    table_T4 = op_to_table(compose(op_T, compose(op_T, compose(op_T, op_T))))
    table_I  = op_to_table(op_I)

    results["P1_T_table"]        = table_T
    results["P1_T2_table"]       = table_T2
    results["P1_T3_table"]       = table_T3
    results["P1_T4_table"]       = table_T4
    results["P1_T4_eq_identity"] = (table_T4 == table_I)
    results["P1_T1_ne_identity"] = (table_T  != table_I)
    results["P1_T2_ne_identity"] = (table_T2 != table_I)
    results["P1_T3_ne_identity"] = (table_T3 != table_I)

    # sympy PermutationGroup formal order check
    # T acts on {0,1,2,3} as the permutation (0 1 2 3)
    perm_T = Permutation([1, 2, 3, 0])   # T(i) at position i
    G_T = PermutationGroup(perm_T)
    order_T = G_T.order()
    results["P1_sympy_group_order"] = int(order_T)
    results["P1_sympy_order_is_4"]  = (order_T == 4)

    # Verify T^k distinct for k=1,2,3 via sympy
    perm_T2 = perm_T ** 2
    perm_T3 = perm_T ** 3
    perm_T4 = perm_T ** 4
    id_perm = Permutation([0, 1, 2, 3])
    results["P1_sympy_T4_is_identity"] = (perm_T4 == id_perm)
    results["P1_sympy_T1_ne_identity"] = (perm_T  != id_perm)
    results["P1_sympy_T2_ne_identity"] = (perm_T2 != id_perm)
    results["P1_sympy_T3_ne_identity"] = (perm_T3 != id_perm)

    # ------------------------------------------------------------------
    # P2: Reflection R has order 2
    # R^2 = identity, R ≠ identity
    # ------------------------------------------------------------------

    table_R  = op_to_table(op_R)
    table_R2 = op_to_table(compose(op_R, op_R))

    results["P2_R_table"]         = table_R
    results["P2_R2_table"]        = table_R2
    results["P2_R2_eq_identity"]  = (table_R2 == table_I)
    results["P2_R_ne_identity"]   = (table_R  != table_I)

    # sympy: R acts as (1 3) — fixes 0 and 2, swaps 1 and 3
    perm_R = Permutation([0, 3, 2, 1])
    G_R = PermutationGroup(perm_R)
    order_R = G_R.order()
    results["P2_sympy_R_order"]        = int(order_R)
    results["P2_sympy_R_order_is_2"]   = (order_R == 2)
    results["P2_sympy_R2_is_identity"] = (perm_R ** 2 == id_perm)

    # ------------------------------------------------------------------
    # P3: Doubling map D is a Z_2 quotient — 2:1 map
    # Image = {0, 2}, kernel = {0, 2} (elements mapping to 0)
    # ------------------------------------------------------------------

    table_D    = op_to_table(op_D)
    image_D    = sorted(set(table_D))
    kernel_D   = [x for x in Z4 if op_D(x) == 0]   # elements mapping to 0
    fiber_0    = [x for x in Z4 if op_D(x) == 0]
    fiber_2    = [x for x in Z4 if op_D(x) == 2]

    results["P3_D_table"]          = table_D
    results["P3_image_D"]          = image_D
    results["P3_image_size_is_2"]  = (len(image_D) == 2)
    results["P3_image_is_0_and_2"] = (image_D == [0, 2])
    results["P3_kernel_D"]         = kernel_D
    results["P3_kernel_size_is_2"] = (len(kernel_D) == 2)
    results["P3_fiber_0"]          = fiber_0
    results["P3_fiber_2"]          = fiber_2
    results["P3_each_fiber_size_2"] = (len(fiber_0) == 2 and len(fiber_2) == 2)
    results["P3_is_2to1_map"]      = (len(image_D) == 2 and
                                       all(len([x for x in Z4 if op_D(x) == y]) == 2
                                           for y in image_D))

    # ------------------------------------------------------------------
    # P4: Entropy of operators
    # Metric used: info_destroyed(f) = log(|Z_4|) - S_out(f)
    #   where S_out = output-distribution Shannon entropy on uniform input.
    # Bijection: S_out = log(4) -> info_destroyed = 0 ("no bits destroyed")
    # D (2:1):   S_out = log(2) -> info_destroyed = log(2) ("1 bit destroyed")
    # Constant:  S_out = 0     -> info_destroyed = log(4)
    # ------------------------------------------------------------------

    log4_val = math.log(4)
    log2_val = math.log(2)

    S_T_out = map_entropy(op_T)   # output-distribution entropy
    S_R_out = map_entropy(op_R)
    S_D_out = map_entropy(op_D)
    S_I_out = map_entropy(op_I)

    # info_destroyed = log(4) - S_out
    ID_T = log4_val - S_T_out
    ID_R = log4_val - S_R_out
    ID_D = log4_val - S_D_out
    ID_I = log4_val - S_I_out

    results["P4_S_out_T"]            = float(S_T_out)
    results["P4_S_out_R"]            = float(S_R_out)
    results["P4_S_out_D"]            = float(S_D_out)
    results["P4_S_out_I"]            = float(S_I_out)
    results["P4_info_destroyed_T"]   = float(ID_T)
    results["P4_info_destroyed_R"]   = float(ID_R)
    results["P4_info_destroyed_D"]   = float(ID_D)
    results["P4_info_destroyed_I"]   = float(ID_I)
    results["P4_log2"]               = float(log2_val)
    results["P4_log4"]               = float(log4_val)
    # Bijections destroy 0 bits: info_destroyed = 0
    results["P4_S_T_is_zero"]    = (abs(ID_T) < 1e-12)
    results["P4_S_R_is_zero"]    = (abs(ID_R) < 1e-12)
    results["P4_S_I_is_zero"]    = (abs(ID_I) < 1e-12)
    # D destroys log(2) bits
    results["P4_S_D_is_log2"]    = (abs(ID_D - log2_val) < 1e-12)

    # sympy symbolic confirmation: S(D) exactly
    # D has 2 fibers of size 2 each; p_i = 2/4 = 1/2 for i in {0,2}
    p_sym = sp.Rational(1, 2)
    S_D_sym = -2 * (p_sym * sp.log(p_sym))
    S_D_simplified = sp.simplify(S_D_sym - sp.log(2))
    results["P4_sympy_S_D_equals_log2"] = (S_D_simplified == 0)

    # ------------------------------------------------------------------
    # P5: Non-commutativity T∘R ≠ R∘T
    # Z_4 with T and R generates the dihedral group D_4 ≅ D_8 (order 8),
    # which is non-abelian
    # ------------------------------------------------------------------

    table_TR = op_to_table(compose(op_T, op_R))  # T(R(x))
    table_RT = op_to_table(compose(op_R, op_T))  # R(T(x))

    results["P5_TR_table"]         = table_TR
    results["P5_RT_table"]         = table_RT
    results["P5_TR_ne_RT"]         = (table_TR != table_RT)

    # sympy: check via permutation composition
    perm_TR = perm_T * perm_R   # sympy: left-to-right composition (T then R)
    perm_RT = perm_R * perm_T
    results["P5_sympy_TR_ne_RT"]   = (perm_TR != perm_RT)

    # Dihedral group: T and R should generate a group of order 8
    G_dih = PermutationGroup(perm_T, perm_R)
    results["P5_sympy_dihedral_order"] = int(G_dih.order())
    results["P5_sympy_dihedral_order_is_8"] = (G_dih.order() == 8)

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # ------------------------------------------------------------------
    # N1: z3 UNSAT — no bijection f:Z_4->Z_4 has exactly 2 distinct images
    # A bijection on a 4-element set must be surjective; surjectivity
    # requires all 4 elements to appear in the image.
    # We encode: f is injective (all values distinct) AND image has size ≤ 2.
    # ------------------------------------------------------------------

    s1 = Solver()
    # f(0), f(1), f(2), f(3) are integers in {0,1,2,3}
    f0, f1, f2, f3 = Int('f0'), Int('f1'), Int('f2'), Int('f3')
    vals = [f0, f1, f2, f3]

    # Each value is in Z_4
    for v in vals:
        s1.add(v >= 0, v <= 3)

    # Injectivity: all values distinct (bijection requirement)
    s1.add(Distinct(f0, f1, f2, f3))

    # Claim: image has exactly 2 distinct values.
    # Encode: there exist two values a, b in Z_4 such that
    # every f(i) is either a or b.
    a, b = Int('a'), Int('b')
    s1.add(a >= 0, a <= 3)
    s1.add(b >= 0, b <= 3)
    s1.add(a != b)   # two DISTINCT image values
    for v in vals:
        s1.add(Or(v == a, v == b))

    result_n1 = s1.check()
    results["N1_z3_unsat_bijection_image_size_2"] = (result_n1 == unsat)
    results["N1_z3_result"] = str(result_n1)

    # Interpretation note
    results["N1_interpretation"] = (
        "UNSAT: a bijection on 4 elements must be surjective (all 4 images used); "
        "having only 2 distinct images contradicts Distinct(f0,f1,f2,f3)."
    )

    # ------------------------------------------------------------------
    # N2: z3 UNSAT — shift T cannot be its own inverse (T^2 ≠ identity)
    # T has order 4; T^2(x) = x+2 mod 4. T^2(0) = 2 ≠ 0.
    # Encode: T^2(x) = x for all x in Z_4 — should be UNSAT.
    # We model T as a function: T_val[x] = (x+1) mod 4, then
    # T^2(x) = T(T(x)). Claim T^2(x) == x for all x.
    # ------------------------------------------------------------------

    s2 = Solver()
    # T_val: Z_4 -> Z_4 defined by T(x) = x+1 mod 4
    # We use concrete values; encode the claim T^2(x) = x for each x.
    # T^2(0) = 2, T^2(1) = 3, T^2(2) = 0, T^2(3) = 1
    # Claim all equal their input: 0=0 OK, but 2=0 FAIL, so UNSAT.
    T2_vals = [(x + 2) % 4 for x in Z4]   # T^2(x) computed
    for x in Z4:
        s2.add(T2_vals[x] == x)            # claim T^2(x) = x
    result_n2 = s2.check()
    results["N2_z3_unsat_T_squared_is_identity"] = (result_n2 == unsat)
    results["N2_z3_result"] = str(result_n2)
    results["N2_T2_values"] = T2_vals
    results["N2_interpretation"] = (
        "UNSAT: T^2(x) = x+2 mod 4 ≠ x for x in {0,1} (T^2(0)=2, T^2(1)=3). "
        "Shift T has order 4, not 2."
    )

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # ------------------------------------------------------------------
    # B1: Identity operator — info_destroyed = 0, all 4 fixed points
    # Identity is a bijection: S_out = log(4), info_destroyed = 0
    # ------------------------------------------------------------------

    b1_log4 = math.log(4)
    table_I = op_to_table(op_I)
    S_I_out = map_entropy(op_I)                      # output-distribution entropy
    ID_I_b1 = b1_log4 - S_I_out                      # info destroyed = 0 for bijection
    fixed_I = [x for x in Z4 if op_I(x) == x]

    results["B1_identity_table"]          = table_I
    results["B1_identity_S_out"]          = float(S_I_out)
    results["B1_identity_info_destroyed"] = float(ID_I_b1)
    # "S is zero" = info_destroyed is zero (bijection destroys no information)
    results["B1_identity_S_is_zero"]      = (abs(ID_I_b1) < 1e-12)
    results["B1_identity_fixed_points"]   = fixed_I
    results["B1_identity_all_4_fixed"]    = (len(fixed_I) == 4)

    # Matrix: M_I should be the 4x4 identity matrix
    M_I = op_to_matrix(op_I)
    results["B1_identity_matrix_is_eye"] = bool(np.array_equal(M_I, np.eye(4, dtype=int)))

    # ------------------------------------------------------------------
    # B2: Maximal entropy — constant map collapses all 4 to one point
    # S = log(4): each input maps to 0, so p(0)=1, all others = 0.
    # Wait — constant map: f(x) = 0 for all x -> p(0)=1 -> S=0.
    # Correct: MAXIMAL entropy requires uniform output OVER ALL 4 elements.
    # That is achieved by the bijections (S=0) — uniform input -> uniform output.
    # For NON-INJECTIVE maps: max collapse is the constant map -> S=0.
    # The "maximal entropy DESTROYED" map destroys log(4) bits of information;
    # this is a constant map: all 4 inputs map to a single output,
    # so the output distribution is deterministic -> S=0, but
    # the mutual information I(input; output) = 0 = log(4) bits destroyed.
    # We measure output-distribution entropy: S_out = -sum p(i) log p(i).
    # Constant map -> p(0)=1 -> S_out = 0.
    # NOTE: This is MINIMUM output entropy (not maximum). Maximum S_out = log(4)
    # achieved when all 4 images equally likely. Bijections achieve this: S=0?
    # WAIT: For bijection T on uniform input, each output appears exactly once:
    # p(i) = 1/4 for all i -> S = log(4). So S(T) as output-distribution
    # entropy = log(4), NOT 0.
    # Re-check: map_entropy counts output frequencies, divides by 4.
    # Bijection: each output appears once -> p(i)=1/4 -> S = log(4).
    # 2:1 map D: each image appears twice -> p(i)=1/2 for 2 values -> S = log(2).
    # Constant map: one image appears 4 times -> p(i)=1 -> S = 0.
    # So: S(bijection) = log(4), S(D) = log(2), S(constant) = 0.
    # The spec says S(T)=0 meaning "no information destroyed".
    # There's an ambiguity: the spec uses "entropy of operator" = info destroyed,
    # not output-distribution entropy.
    # Info destroyed = log(|Z_4|) - output_entropy = log(4) - S_out.
    # For T: log(4) - log(4) = 0 (bijection destroys 0 bits). CORRECT.
    # For D: log(4) - log(2) = log(2). CORRECT.
    # For constant: log(4) - 0 = log(4). CORRECT.
    # We implement BOTH: output_entropy and info_destroyed.
    # ------------------------------------------------------------------

    log4_val = math.log(4)
    log2_val = math.log(2)

    # Re-run with corrected interpretation
    # Output-distribution entropy (what map_entropy computes):
    S_T_out = map_entropy(op_T)     # = log(4): bijection, all 4 images
    S_D_out = map_entropy(op_D)     # = log(2): 2 images each with prob 1/2
    S_I_out = map_entropy(op_I)     # = log(4): bijection

    # Information destroyed = log(4) - S_out
    def info_destroyed(f):
        return log4_val - map_entropy(f)

    ID_T = info_destroyed(op_T)
    ID_R = info_destroyed(op_R)
    ID_D = info_destroyed(op_D)
    ID_I = info_destroyed(op_I)

    # Constant map to 0
    op_const = lambda x: 0
    S_const_out = map_entropy(op_const)     # = 0
    ID_const = info_destroyed(op_const)     # = log(4)

    results["B2_S_out_T"]         = float(S_T_out)
    results["B2_S_out_D"]         = float(S_D_out)
    results["B2_S_out_I"]         = float(S_I_out)
    results["B2_S_out_const"]     = float(S_const_out)
    results["B2_log4"]            = float(log4_val)
    results["B2_log2"]            = float(log2_val)
    results["B2_ID_T"]            = float(ID_T)
    results["B2_ID_R"]            = float(ID_R)
    results["B2_ID_D"]            = float(ID_D)
    results["B2_ID_I"]            = float(ID_I)
    results["B2_ID_const"]        = float(ID_const)

    # Bijections destroy 0 bits of information
    results["B2_bijections_destroy_0_bits"]  = (abs(ID_T) < 1e-12 and
                                                  abs(ID_R) < 1e-12 and
                                                  abs(ID_I) < 1e-12)
    # D destroys exactly log(2) bits
    results["B2_D_destroys_log2_bits"]       = (abs(ID_D - log2_val) < 1e-12)
    # Constant map destroys log(4) bits (maximum)
    results["B2_const_destroys_log4_bits"]   = (abs(ID_const - log4_val) < 1e-12)
    # S_out for constant map is 0 (deterministic output)
    results["B2_const_S_out_is_zero"]        = (abs(S_const_out) < 1e-12)

    # Rosetta log(2) record
    results["B2_rosetta_log2_pattern"] = {
        "Z4_doubling_D_info_destroyed": float(ID_D),
        "log2_value":                   float(log2_val),
        "Z4_doubling_matches_log2":     bool(abs(ID_D - log2_val) < 1e-12),
        "same_constant_as": [
            "SU(2)->SO(3) double-cover: log(2)",
            "O(3)->SO(3) orientation quotient: log(2)",
            "Sp(6) bond from SU(3): log(2)",
        ],
        "shared_structure": "Z_2 quotient / 2:1 collapse",
    }

    # sympy confirmation B2: info_destroyed(D) = log(4) - log(2) = log(2)
    log4_sym = sp.log(4)
    log2_sym = sp.log(2)
    ID_D_sym = sp.simplify(log4_sym - log2_sym - log2_sym)
    results["B2_sympy_log4_minus_log2_is_log2"] = (ID_D_sym == 0)

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    errors = []
    pos = {}
    neg = {}
    bnd = {}

    try:
        pos = run_positive_tests()
    except Exception as e:
        errors.append(f"positive: {e}\n{traceback.format_exc()}")

    try:
        neg = run_negative_tests()
    except Exception as e:
        errors.append(f"negative: {e}\n{traceback.format_exc()}")

    try:
        bnd = run_boundary_tests()
    except Exception as e:
        errors.append(f"boundary: {e}\n{traceback.format_exc()}")

    bool_pos = {k: v for k, v in pos.items() if isinstance(v, bool)}
    bool_neg = {k: v for k, v in neg.items() if isinstance(v, bool)}
    bool_bnd = {k: v for k, v in bnd.items() if isinstance(v, bool)}

    all_pass = (
        all(bool_pos.values()) and
        all(bool_neg.values()) and
        all(bool_bnd.values()) and
        len(errors) == 0
    )

    results = {
        "name": "igt_4ring_operator_family",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": all_pass,
        "errors": errors,
        "summary": {
            "all_pass": all_pass,
            "operators": {
                "T": "shift x+1 mod 4 — order 4, generates Z_4, info_destroyed=0",
                "R": "reflection -x mod 4 — order 2, info_destroyed=0",
                "D": "doubling 2x mod 4 — 2:1 Z_2 quotient, info_destroyed=log(2)",
                "T_R_non_commuting": "T∘R ≠ R∘T — generates dihedral D_4 of order 8",
            },
            "rosetta_log2": (
                "S(D)=log(2) matches SU(2)->SO(3), O(3)->SO(3), Sp(6)/SU(3) — "
                "all are Z_2 quotient actions"
            ),
        },
        "divergence_log": [
            "classical_baseline: discrete group theory, no genuine quantum operator algebra",
            "entropy computed as output-distribution Shannon entropy on uniform Z_4 input",
            "info_destroyed = log(4) - S_out tracks bits collapsed by the map",
            "z3 UNSAT proofs encode structural impossibility, not derived from abstract algebra axioms",
            "sympy PermutationGroup verifies orders formally; does not derive group from axioms",
            "dihedral structure T,R -> D_4 is a classical result; no coupling behavior tested here",
            "log(2) Rosetta is a candidate alignment — not a theorem until cross-domain coupling sims run",
        ],
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_igt_4ring_operator_family_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
    if errors:
        for e in errors:
            print(e)
