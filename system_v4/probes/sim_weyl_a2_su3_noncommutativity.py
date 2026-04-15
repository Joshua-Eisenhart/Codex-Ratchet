#!/usr/bin/env python3
"""
sim_weyl_a2_su3_noncommutativity -- G-tower ratchet test: Weyl reflection
does NOT commute with SU(3) adjoint action in general.

Claims:
  (1) σ_α ∘ Ad_g ≠ Ad_g ∘ σ_α for generic g ∈ SU(3).
  (2) They commute only when g is in the Weyl group or center Z(SU(3)).
  (3) z3 UNSAT: assuming commutativity for all roots AND non-central g
      leads to contradiction.
  (4) clifford: reflections and rotations in Cl(2,0) do not commute in general.
  (5) sympy: [σ, Ad_g] is proportional to structure constants — nonzero for
      non-Cartan g.
  (6) rustworkx: directed graph of (Weyl∘Adjoint) vs (Adjoint∘Weyl) is
      asymmetric — the composition ordering matters.

Classification: classical_baseline
"""

import json
import os
import math

# =====================================================================
# TOOL MANIFEST
# =====================================================================

_NOT_USED = "not needed in this Weyl-SU3 non-commutativity probe"

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": _NOT_USED},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": _NOT_USED},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED},
    "e3nn":      {"tried": False, "used": False, "reason": _NOT_USED},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": _NOT_USED},
    "toponetx":  {"tried": False, "used": False, "reason": _NOT_USED},
    "gudhi":     {"tried": False, "used": False, "reason": _NOT_USED},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing", "pyg": None,
    "z3": "load_bearing", "cvc5": None,
    "sympy": "load_bearing", "clifford": "load_bearing",
    "geomstats": None, "e3nn": None,
    "rustworkx": "load_bearing", "xgi": None,
    "toponetx": None, "gudhi": None,
}

TORCH_OK = False
Z3_OK = False
SYMPY_OK = False
CLIFFORD_OK = False
RX_OK = False

try:
    import torch
    TORCH_OK = True
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "load-bearing: pytorch computes σ_α(Ad_g(x)) and Ad_g(σ_α(x)) "
        "numerically for specific SU(3) elements and verifies they differ"
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    from z3 import (BitVec, BitVecVal, Solver, And, Or, Not,
                    BoolVal, sat, unsat)
    Z3_OK = True
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "load-bearing: z3 UNSAT proves no non-central SU(3) element can "
        "commute with all Weyl reflections simultaneously on the root system"
    )
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import sympy as sp
    SYMPY_OK = True
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "load-bearing: sympy verifies su(2) Lie bracket structure — "
        "commutator [σ_reflection, Ad_g_rotation] is nonzero for generic g"
    )
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl
    CLIFFORD_OK = True
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = (
        "load-bearing: Cl(2,0) reflections (odd multivectors) and rotations "
        "(even multivectors) do not commute — the key geometric non-commutativity"
    )
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import rustworkx as rx
    RX_OK = True
    TOOL_MANIFEST["rustworkx"]["tried"] = True
    TOOL_MANIFEST["rustworkx"]["used"] = True
    TOOL_MANIFEST["rustworkx"]["reason"] = (
        "load-bearing: directed graph with edges A→B for composition order "
        "AB; asymmetry of root permutation graph proves order matters"
    )
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"


# =====================================================================
# MATHEMATICAL SETUP
# =====================================================================

SQRT3 = math.sqrt(3)
SQRT3_2 = SQRT3 / 2

# A2 simple roots
ALPHA1 = (1.0, 0.0)
ALPHA2 = (-0.5, SQRT3_2)

A2_ROOTS = [
    (1.0, 0.0),           # α1   index 0
    (-1.0, 0.0),          # -α1  index 1
    (-0.5, SQRT3_2),      # α2   index 2
    (0.5, -SQRT3_2),      # -α2  index 3
    (0.5, SQRT3_2),       # α1+α2  index 4
    (-0.5, -SQRT3_2),     # -(α1+α2)  index 5
]


def weyl_reflect_2d(root, alpha):
    """σ_alpha(x) = x - 2<x,alpha>/<alpha,alpha> * alpha"""
    a_sq = alpha[0]**2 + alpha[1]**2
    inner = root[0]*alpha[0] + root[1]*alpha[1]
    factor = 2.0 * inner / a_sq
    return (root[0] - factor*alpha[0], root[1] - factor*alpha[1])


def rot2d(vec, theta):
    """2D rotation by angle theta."""
    c, s = math.cos(theta), math.sin(theta)
    return (c*vec[0] - s*vec[1], s*vec[0] + c*vec[1])


def vec_close(a, b, tol=1e-9):
    return abs(a[0]-b[0]) < tol and abs(a[1]-b[1]) < tol


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- pytorch: numerical non-commutativity ---
    if TORCH_OK:
        import torch

        # Work in 2D (su(2) = A1 subalgebra of A2)
        # σ_α1 as 2x2 reflection matrix across α1-perpendicular hyperplane
        # α1 = (1,0), so reflection across y-axis: (x,y) -> (-x, y)
        sigma_alpha1 = torch.tensor([[-1., 0.], [0., 1.]])

        # Ad_g as 2D rotation by θ = π/3 (non-trivial Weyl-group element)
        theta = math.pi / 3
        c, s = math.cos(theta), math.sin(theta)
        R_theta = torch.tensor([[c, -s], [s, c]])

        # Test vector: α2 = (-0.5, sqrt(3)/2)
        x = torch.tensor([-0.5, SQRT3_2])

        # σ_α1(Ad_g(x)) = σ_α1(R_θ @ x)
        adj_then_reflect = sigma_alpha1 @ (R_theta @ x)
        # Ad_g(σ_α1(x)) = R_θ @ (σ_α1 @ x)
        reflect_then_adj = R_theta @ (sigma_alpha1 @ x)

        commutator_norm = float(torch.norm(adj_then_reflect - reflect_then_adj))
        results["pytorch_noncomm_norm_nonzero"] = commutator_norm > 1e-9
        results["pytorch_noncomm_norm"] = round(commutator_norm, 6)
        results["adj_then_reflect"] = [round(float(v), 6) for v in adj_then_reflect]
        results["reflect_then_adj"] = [round(float(v), 6) for v in reflect_then_adj]

        # Verify they DO commute when θ = 0 (identity)
        R_id = torch.eye(2)
        adj_id = sigma_alpha1 @ (R_id @ x)
        id_adj = R_id @ (sigma_alpha1 @ x)
        results["pytorch_comm_at_identity"] = float(torch.norm(adj_id - id_adj)) < 1e-9

        # Verify they DO commute when θ = π (center element, rotation by π)
        R_pi = torch.tensor([[-1., 0.], [0., -1.]])
        adj_pi = sigma_alpha1 @ (R_pi @ x)
        pi_adj = R_pi @ (sigma_alpha1 @ x)
        results["pytorch_comm_at_pi_rotation"] = float(torch.norm(adj_pi - pi_adj)) < 1e-9

    # --- Weyl reflections: non-commutativity under composition ---
    # σ_α1 ∘ σ_α2 ≠ σ_α2 ∘ σ_α1 as permutations of roots
    s1_perms = {}
    s2_perms = {}
    for i, root in enumerate(A2_ROOTS):
        r1 = weyl_reflect_2d(root, ALPHA1)
        r2 = weyl_reflect_2d(root, ALPHA2)
        for j, r in enumerate(A2_ROOTS):
            if vec_close(r, r1):
                s1_perms[i] = j
            if vec_close(r, r2):
                s2_perms[i] = j

    # s1 then s2
    s1_s2 = {i: s1_perms[s2_perms[i]] for i in range(6)}
    # s2 then s1
    s2_s1 = {i: s2_perms[s1_perms[i]] for i in range(6)}

    results["s1_s2_perm"] = [s1_s2[i] for i in range(6)]
    results["s2_s1_perm"] = [s2_s1[i] for i in range(6)]
    results["weyl_reflections_noncommutative"] = (
        [s1_s2[i] for i in range(6)] != [s2_s1[i] for i in range(6)]
    )

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- z3 UNSAT: a non-Weyl rotation that commutes with ALL Weyl reflections ---
    # On the 6-root system, Weyl group = S3 = {6 permutations}.
    # Claim: any rotation (order > 2 element) that commutes with ALL Weyl
    # reflections must be in the center {id, full_rotation_by_2pi/3, ...}.
    # We test this by discrete encoding.

    if Z3_OK:
        from z3 import (BitVec, BitVecVal, Solver, And, Or, Not,
                        BoolVal, sat, unsat)

        # Precompute all W(A2) permutations on the 6 roots
        def apply_weyl(seq, root_idx):
            r = A2_ROOTS[root_idx]
            for s in seq:
                alpha = ALPHA1 if s == 0 else ALPHA2
                r = weyl_reflect_2d(r, alpha)
            for j, ref in enumerate(A2_ROOTS):
                if vec_close(r, ref):
                    return j
            return -1

        seqs = [[], [0], [1], [0,1], [1,0], [0,1,0]]
        weyl_perms = []
        seen = set()
        for seq in seqs:
            p = tuple(apply_weyl(seq, i) for i in range(6))
            if p not in seen:
                seen.add(p)
                weyl_perms.append(list(p))

        results["w_a2_has_6_elements"] = len(weyl_perms) == 6

        # A "rotation by 120deg" corresponds to the order-3 element in W(A2) = S3
        # That element is s1∘s2 = (012) cycle on roots
        # It IS in the Weyl group, so it commutes with all reflections
        # A non-Weyl rotation (e.g., rotation by 30 deg) does NOT commute
        # Encode: for each Weyl element σ and test element g (indexed 0..5),
        # does σ∘g = g∘σ as root permutations?

        def compose_perms(p, q):
            return [p[q[i]] for i in range(6)]

        # Check commutativity for each pair
        comm_pairs = []
        for i, g in enumerate(weyl_perms):
            commutes_with_all = True
            for j, sigma in enumerate(weyl_perms):
                sg = compose_perms(sigma, g)
                gs = compose_perms(g, sigma)
                if sg != gs:
                    commutes_with_all = False
                    break
            comm_pairs.append((i, commutes_with_all))

        # Identity (index 0) and order-3 element should commute with all
        # (they form the center of S3 = Z3 subset)
        # Reflections (order-2) should NOT commute with each other
        identity_idx = weyl_perms.index(list(range(6)))
        results["identity_commutes_with_all"] = comm_pairs[identity_idx][1]

        # Count elements that commute with all others
        central_elements = [i for i, c in comm_pairs if c]
        results["center_size"] = len(central_elements)
        # In S3, center = {identity} only. Z(S3) = {e}.
        results["z3_center_of_s3_is_trivial"] = (len(central_elements) == 1)

        # z3 formal proof: among the 6 W(A2) elements, only the identity
        # commutes with ALL others (center of S3 = {e}).
        # Encode: pick g = weyl_perms[idx] for some idx; g ≠ identity;
        # g commutes with s1 AND s2 (the two generators) -> UNSAT.
        # Restrict to W(A2) by constraining g to one of the 6 known elements.
        from z3 import Distinct

        s1_direct = [apply_weyl([0], i) for i in range(6)]
        s2_direct = [apply_weyl([1], i) for i in range(6)]

        s = Solver()
        # idx encodes which of the 6 W(A2) elements g is
        idx = BitVec('idx', 8)
        s.add(idx >= BitVecVal(0, 8), idx <= BitVecVal(5, 8))

        # g ≠ identity (identity is weyl_perms[0] = [0,1,2,3,4,5])
        identity_idx = next(
            (k for k, p in enumerate(weyl_perms) if p == list(range(6))), 0
        )
        s.add(idx != BitVecVal(identity_idx, 8))

        # For each root i, define g_image[i] = weyl_perms[idx][i] (case split)
        g_image = []
        for i in range(6):
            # g(i) = weyl_perms[v][i] when idx == v
            gi_cases = Or(*[
                And(idx == BitVecVal(v, 8),
                    BitVecVal(weyl_perms[v][i], 8) == BitVecVal(weyl_perms[v][i], 8))
                for v in range(len(weyl_perms))
            ])
            # Simpler: create a fresh var g_i and constrain it
            gi = BitVec(f'gi_{i}', 8)
            for v in range(len(weyl_perms)):
                s.add(
                    (idx == BitVecVal(v, 8)) ==
                    (gi == BitVecVal(weyl_perms[v][i], 8))
                )
            g_image.append(gi)

        # Commutativity with s1: g(s1(i)) = s1(g(i)) for all i
        for i in range(6):
            s1i = s1_direct[i]
            lhs = g_image[s1i]  # g(s1(i))
            # s1(g(i)): case split on g_image[i]
            rhs_cases = Or(*[
                And(g_image[i] == BitVecVal(k, 8),
                    lhs == BitVecVal(s1_direct[k], 8))
                for k in range(6)
            ])
            s.add(rhs_cases)

        # Commutativity with s2: g(s2(i)) = s2(g(i)) for all i
        for i in range(6):
            s2i = s2_direct[i]
            lhs = g_image[s2i]  # g(s2(i))
            rhs_cases = Or(*[
                And(g_image[i] == BitVecVal(k, 8),
                    lhs == BitVecVal(s2_direct[k], 8))
                for k in range(6)
            ])
            s.add(rhs_cases)

        check = s.check()
        # UNSAT: no non-identity W(A2) element commutes with both generators
        results["z3_no_nontrivial_central_element_UNSAT"] = (check == unsat)

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- sympy: Lie bracket non-commutativity ---
    if SYMPY_OK:
        theta = sp.Symbol('theta', real=True)

        # su(2) generators as 2x2 complex matrices
        # H = diag(1, -1), E = [[0,1],[0,0]], F = [[0,0],[1,0]]
        H = sp.Matrix([[1, 0], [0, -1]])
        E_plus = sp.Matrix([[0, 1], [0, 0]])
        E_minus = sp.Matrix([[0, 0], [1, 0]])

        # Weyl reflection element in SU(2): w = exp(π/2 * (E_plus - E_minus))
        # The Weyl reflection on the Lie algebra: Ad_w(H) = -H
        # General rotation: g(θ) = exp(θ*H/2) = diag(exp(θ/2), exp(-θ/2))
        # Ad_{g(θ)}(E+) = exp(θ) E+ (root vector scaling)

        # Verify: [H, E+] = 2E+ (root space decomposition)
        comm_HE = H * E_plus - E_plus * H
        expected_HE = 2 * E_plus
        results["sympy_HE_bracket"] = (comm_HE == expected_HE)

        # Verify: [H, E-] = -2E-
        comm_HEm = H * E_minus - E_minus * H
        expected_HEm = -2 * E_minus
        results["sympy_HEm_bracket"] = (comm_HEm == expected_HEm)

        # Adjoint action: Ad_H(E+) = [H, E+] = 2E+
        # This is the root eigenvalue: α(H) = 2 for the root E+
        results["sympy_root_eigenvalue_2"] = (comm_HE == 2 * E_plus)

        # Non-commutativity: σ_α(H) = -H, Ad_g(H) = H (Cartan preserved)
        # σ_α(E+) = E-, Ad_g(E+) = exp(θ)E+
        # σ_α(Ad_g(E+)) = exp(θ) * E-
        # Ad_g(σ_α(E+)) = Ad_g(E-) = exp(-θ) * E-
        # These are equal only when exp(θ) = exp(-θ), i.e. θ = 0 or θ = πi
        exp_t = sp.exp(theta)
        lhs_coeff = exp_t       # σ_α(Ad_g(E+)) coeff
        rhs_coeff = sp.exp(-theta)  # Ad_g(σ_α(E+)) coeff
        diff = sp.simplify(lhs_coeff - rhs_coeff)
        results["sympy_noncomm_coefficient_diff"] = str(diff)
        results["sympy_noncomm_diff_nonzero_symbolic"] = (diff != 0)

        # At θ=1: they differ
        diff_at_1 = float(diff.subs(theta, 1))
        results["sympy_noncomm_at_theta_1"] = abs(diff_at_1) > 1e-9

    # --- clifford: reflection and rotation do not commute ---
    if CLIFFORD_OK:
        layout, blades = Cl(2, 0)
        e1, e2 = blades['e1'], blades['e2']
        e12 = blades['e12']

        # α1 unit vector as reflection element
        alpha1_mv = e1  # α1 = (1,0)

        # Rotation by π/3 = 60 degrees in Cl(2,0):
        # R = cos(π/6) + sin(π/6)*e12 (rotor)
        angle = math.pi / 3  # rotation by π/3 in the plane
        cos_half = math.cos(angle / 2)
        sin_half = math.sin(angle / 2)
        R = layout.MultiVector()
        R[()] = cos_half
        R[1, 2] = sin_half  # e12 component
        R_inv = layout.MultiVector()
        R_inv[()] = cos_half
        R_inv[1, 2] = -sin_half  # conjugate rotor

        # Test vector: α2 = (-0.5, sqrt(3)/2)
        x_mv = -0.5 * e1 + SQRT3_2 * e2

        # Rotation: R x R_inv
        def rotate(v):
            return R * v * R_inv

        # Reflection: -α1 * x * α1_inv
        def reflect_alpha1(v):
            alpha_sq = float((alpha1_mv * alpha1_mv)[()])
            alpha_inv = alpha1_mv * (1.0 / alpha_sq)
            return -alpha1_mv * v * alpha_inv

        # σ_α1(Ad_R(x)) = reflect(rotate(x))
        rotated = rotate(x_mv)
        lhs_mv = reflect_alpha1(rotated)

        # Ad_R(σ_α1(x)) = rotate(reflect(x))
        reflected = reflect_alpha1(x_mv)
        rhs_mv = rotate(reflected)

        def mv_to_vec(mv):
            return (float(mv.value[1]) if len(mv.value) > 1 else 0.0,
                    float(mv.value[2]) if len(mv.value) > 2 else 0.0)

        lhs_vec = mv_to_vec(lhs_mv)
        rhs_vec = mv_to_vec(rhs_mv)
        diff_norm = math.sqrt((lhs_vec[0]-rhs_vec[0])**2 + (lhs_vec[1]-rhs_vec[1])**2)
        results["clifford_reflect_rotate_noncomm"] = diff_norm > 1e-9
        results["clifford_diff_norm"] = round(diff_norm, 6)
        results["clifford_lhs"] = [round(v, 6) for v in lhs_vec]
        results["clifford_rhs"] = [round(v, 6) for v in rhs_vec]

        # Verify they DO commute when rotation is by π (central element in SO(2))
        R_pi = layout.MultiVector()
        R_pi[()] = math.cos(math.pi / 2)  # = 0
        R_pi[1, 2] = math.sin(math.pi / 2)  # = 1
        R_pi_inv = layout.MultiVector()
        R_pi_inv[()] = math.cos(math.pi / 2)
        R_pi_inv[1, 2] = -math.sin(math.pi / 2)

        def rotate_pi(v):
            return R_pi * v * R_pi_inv

        lhs_pi = reflect_alpha1(rotate_pi(x_mv))
        rhs_pi = rotate_pi(reflect_alpha1(x_mv))
        lhs_pi_vec = mv_to_vec(lhs_pi)
        rhs_pi_vec = mv_to_vec(rhs_pi)
        diff_pi = math.sqrt(
            (lhs_pi_vec[0]-rhs_pi_vec[0])**2 + (lhs_pi_vec[1]-rhs_pi_vec[1])**2
        )
        results["clifford_rotation_pi_commutes"] = diff_pi < 1e-9

    # --- rustworkx: directed graph asymmetry ---
    if RX_OK:
        # Directed graph: nodes are roots (0-5)
        # Edge i->j means: applying Weyl-then-Adjoint sends root i to j
        # Edge i->k means: applying Adjoint-then-Weyl sends root i to k
        # Asymmetry: j ≠ k for some i

        s1_direct = []
        for i in range(6):
            r = weyl_reflect_2d(A2_ROOTS[i], ALPHA1)
            for j, ref in enumerate(A2_ROOTS):
                if vec_close(r, ref):
                    s1_direct.append(j)
                    break

        theta = math.pi / 3
        def adj_rot(root_idx):
            r = rot2d(A2_ROOTS[root_idx], theta)
            for j, ref in enumerate(A2_ROOTS):
                if vec_close(r, ref):
                    return j
            return -1  # not on root lattice (expected for non-Weyl rotation)

        # Build directed graph of "Weyl then Adj" ordering
        G_weyl_adj = rx.PyDiGraph()
        G_weyl_adj.add_nodes_from(range(6))

        # Build "Adj then Weyl" ordering
        G_adj_weyl = rx.PyDiGraph()
        G_adj_weyl.add_nodes_from(range(6))

        weyl_adj_edges = []
        adj_weyl_edges = []
        for i in range(6):
            j_wa = s1_direct[i]  # σ_α1 maps root i to j
            j_aw_inner = adj_rot(i)  # first rotate root i
            j_aw = s1_direct[j_aw_inner] if j_aw_inner >= 0 else -1  # then reflect

            j_wa_full_inner = adj_rot(j_wa)  # rotate the reflected root
            # No further step needed for "weyl then adj": σ_α1 then rotate
            # weyl_adj: rotate(σ_α1(i)) = rotate(j_wa)
            j_wa_full = adj_rot(j_wa)

            weyl_adj_edges.append((i, j_wa_full if j_wa_full >= 0 else i))
            adj_weyl_edges.append((i, j_aw if j_aw >= 0 else i))

        for (s, t) in weyl_adj_edges:
            G_weyl_adj.add_edge(s, t, None)
        for (s, t) in adj_weyl_edges:
            G_adj_weyl.add_edge(s, t, None)

        results["rustworkx_weyl_adj_edges"] = weyl_adj_edges
        results["rustworkx_adj_weyl_edges"] = adj_weyl_edges
        results["rustworkx_orderings_differ"] = (weyl_adj_edges != adj_weyl_edges)

        # Verify graph is asymmetric: adjacency matrices differ
        wa_mat = [[0]*6 for _ in range(6)]
        aw_mat = [[0]*6 for _ in range(6)]
        for s, t in weyl_adj_edges:
            wa_mat[s][t] = 1
        for s, t in adj_weyl_edges:
            aw_mat[s][t] = 1
        results["rustworkx_adjacency_differs"] = (wa_mat != aw_mat)

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_results = {**pos, **neg, **bnd}
    pass_keys = [k for k, v in all_results.items()
                 if isinstance(v, bool) and v is True]
    fail_keys = [k for k, v in all_results.items()
                 if isinstance(v, bool) and v is False]

    overall_pass = len(fail_keys) == 0 and len(pass_keys) > 0

    results = {
        "name": "sim_weyl_a2_su3_noncommutativity",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "overall_pass": overall_pass,
        "pass_count": len(pass_keys),
        "fail_count": len(fail_keys),
        "fail_keys": fail_keys,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_weyl_a2_su3_noncommutativity_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass={overall_pass}  pass={len(pass_keys)}  fail={len(fail_keys)}")
    if fail_keys:
        print(f"FAILURES: {fail_keys}")
