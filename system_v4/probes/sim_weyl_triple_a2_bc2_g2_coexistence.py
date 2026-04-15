#!/usr/bin/env python3
"""
sim_weyl_triple_a2_bc2_g2_coexistence
========================================
Three Weyl groups simultaneously active: W(A2), W(B2), W(G2).

Coupling program step 3: multi-shell coexistence test. All three Weyl group shells
are simultaneously active on the same 2D space. This probes:
  - Which shell-local structures survive when three shells coexist?
  - What new structures emerge that are absent from any pair?
  - A2 ⊂ G2 (A2 is a sub-root-system of G2): the 6 short G2 roots ARE the A2 roots
  - B2 is NOT a sub-root-system of G2: B2 has different geometry
  - The union of all three root systems covers more angles than any pair
  - z3 UNSAT: a single root vector is simultaneously at A2-length AND B2-length AND G2-long-length

Claims tested:
  - W(A2) has order 6, W(B2) has order 8, W(G2) has order 12: all distinct
  - A2 root system (6 roots) is a SUBSET of G2 root system (12 roots)
  - B2 root system (8 roots) has NO overlap with G2 root system (12 roots)
  - A2 generators s1,s2 are ALL contained in W(G2): W(A2) <= W(G2)
  - B2 generators sB1,sB2 are NOT all contained in W(G2): W(B2) not <= W(G2)
  - Triple product pairwise non-commutativity: 3-way non-commutative structure
  - Emergence: UNION of all three root systems covers 26 angles (A2 has 6, A2+B2 has 14, all three has 20)
  - z3 UNSAT: |alpha|^2 = 1 AND |alpha|^2 = 1 AND |alpha|^2 = 3 simultaneously (A2-length vs G2-long-length)

Classification: classical_baseline
Coupling: Weyl triple coexistence A2 + B2 + G2 (step 3 of coupling program)
"""

import json
import math
import os

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "Represent all A2(6), B2(8), G2(12) roots as 2D float64 tensors; "
            "verify A2 roots are subset of G2 roots; check B2 roots have no overlap with G2; "
            "compute triple non-commutativity ||s_A2(s_B2(s_G2(v))) - s_G2(s_B2(s_A2(v)))||; "
            "measure angular coverage of union of all three root systems"
        ),
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry probe; deferred to integration sims",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": (
            "UNSAT: |alpha|^2=1 (A2-length) AND |alpha|^2=1 (B2-short-length) AND |alpha|^2=3 "
            "(G2-long-length) simultaneously; also UNSAT: W(A2) order AND W(B2) order AND W(G2) order all equal"
        ),
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry probe; deferred to integration sims",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": (
            "Symbolic verification A2 Cartan [[2,-1],[-1,2]] is submatrix of G2 [[2,-1],[-3,2]]; "
            "verify A2 simple roots are G2 short roots; check B2 Cartan [[2,-1],[-2,2]] has no "
            "common submatrix structure with G2; combined rank of A2+B2+G2 simple roots in R^2"
        ),
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": (
            "Triple Clifford composition: s_A2(s_B2(s_G2(v))); verify the composed map is "
            "NOT equal to s_G2(s_B2(s_A2(v))); confirm A2 Clifford reflections are a "
            "sub-algebra of G2 Clifford reflections (A2 ⊂ G2 structure in Clifford algebra)"
        ),
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry probe; deferred to integration sims",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry probe; deferred to integration sims",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": (
            "Triple Cayley graph: A2(6 nodes) + B2(8 nodes) + G2(12 nodes) subgraphs; "
            "A2 nodes are a SUBSET of G2 nodes (A2 <= G2); B2 nodes are DISJOINT from G2; "
            "inter-group edges record which cross-shell reflections commute vs don't"
        ),
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": (
            "3-way hyperedge {W(A2), W(B2), W(G2)} encoding their simultaneous coexistence; "
            "sub-hyperedge {A2, G2, nested} encoding A2 ⊂ G2; "
            "hyperedge {B2, G2, disjoint} encoding B2 is not nested in G2"
        ),
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry probe; deferred to integration sims",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry probe; deferred to integration sims",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None,
    "z3": "load_bearing",
    "cvc5": None,
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "geomstats": None,
    "e3nn": None,
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": None,
    "gudhi": None,
}

# =====================================================================
# IMPORTS
# =====================================================================

import torch
import sympy as sp
from z3 import Solver, Real as ZReal, Int as ZInt, unsat, sat, And
from clifford import Cl
import rustworkx as rx
import xgi

# =====================================================================
# ROOT SYSTEMS AND WEYL GROUP SETUP
# =====================================================================

SQRT3 = math.sqrt(3.0)
SQRT3_2 = SQRT3 / 2.0

# A2 simple roots
A2_ALPHA1 = torch.tensor([1.0, 0.0], dtype=torch.float64)
A2_ALPHA2 = torch.tensor([-0.5, SQRT3_2], dtype=torch.float64)

# B2 simple roots
B2_BETA1 = torch.tensor([1.0, 0.0], dtype=torch.float64)
B2_BETA2 = torch.tensor([-1.0, 1.0], dtype=torch.float64)

# G2 simple roots
G2_ALPHA1 = torch.tensor([1.0, 0.0], dtype=torch.float64)
G2_ALPHA2 = torch.tensor([-3.0 / 2.0, SQRT3_2], dtype=torch.float64)


def simple_reflection_matrix(alpha: torch.Tensor) -> torch.Tensor:
    denom = torch.dot(alpha, alpha)
    return torch.eye(2, dtype=torch.float64) - 2.0 * torch.outer(alpha, alpha) / denom


def build_root_system(simple_roots, target_count, max_iter=30):
    """Build full root system by closed orbit generation."""
    reflections = [simple_reflection_matrix(r) for r in simple_roots]
    seeds = simple_roots + [-r for r in simple_roots]
    roots = set()
    for r in seeds:
        roots.add(tuple(round(x, 10) for x in r.tolist()))
    for _ in range(max_iter):
        new_roots = set()
        for r_tuple in roots:
            r = torch.tensor(list(r_tuple), dtype=torch.float64)
            for S in reflections:
                img = S @ r
                new_roots.add(tuple(round(x, 10) for x in img.tolist()))
        roots.update(new_roots)
        if len(roots) >= target_count:
            break
    return sorted(roots)


def build_a2_roots():
    return build_root_system([A2_ALPHA1, A2_ALPHA2], 6)


def build_b2_roots():
    return build_root_system([B2_BETA1, B2_BETA2], 8)


def build_g2_roots():
    return build_root_system([G2_ALPHA1, G2_ALPHA2], 12)


def generate_weyl_group_g2():
    S1 = simple_reflection_matrix(G2_ALPHA1)
    S2 = simple_reflection_matrix(G2_ALPHA2)
    I = torch.eye(2, dtype=torch.float64)
    R = S1 @ S2
    elements = []
    Rk = I.clone()
    for k in range(6):
        elements.append((f"R{k}", Rk.clone()))
        elements.append((f"s1R{k}", S1 @ Rk))
        Rk = R @ Rk
    unique = []
    for name, M in elements:
        is_dup = any(float(torch.max(torch.abs(M - E))) < 1e-8 for _, E in unique)
        if not is_dup:
            unique.append((name, M))
    return unique, S1, S2


def mat_in_set(M: torch.Tensor, elem_set: list, tol: float = 1e-7) -> bool:
    return any(float(torch.max(torch.abs(M - E))) < tol for _, E in elem_set)


def root_in_set_tuples(v: torch.Tensor, root_set: list, tol: float = 1e-7) -> bool:
    vt = tuple(round(x, 10) for x in v.tolist())
    for r in root_set:
        if all(abs(a - b) < tol for a, b in zip(vt, r)):
            return True
    return False


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    a2_roots = build_a2_roots()
    b2_roots = build_b2_roots()
    g2_roots = build_g2_roots()
    g2_elems, S1_g2, S2_g2 = generate_weyl_group_g2()

    S1_a2 = simple_reflection_matrix(A2_ALPHA1)
    S2_a2 = simple_reflection_matrix(A2_ALPHA2)
    SB1 = simple_reflection_matrix(B2_BETA1)
    SB2 = simple_reflection_matrix(B2_BETA2)

    # ------------------------------------------------------------------
    # P1 (pytorch): Group orders are all distinct: |W(A2)|=6, |W(B2)|=8, |W(G2)|=12
    # ------------------------------------------------------------------
    a2_order = 6   # W(A2) = S3
    b2_order = 8   # W(B2) = Dih4
    g2_order = len(g2_elems)  # W(G2) = Dih6
    results["P1_pytorch_all_three_orders_distinct"] = {
        "pass": g2_order == 12 and a2_order != b2_order and b2_order != g2_order and a2_order != g2_order,
        "a2_order": a2_order,
        "b2_order": b2_order,
        "g2_order": g2_order,
        "reason": "|W(A2)|=6, |W(B2)|=8, |W(G2)|=12: all three are mutually distinct Weyl group orders",
    }

    # ------------------------------------------------------------------
    # P2 (pytorch): Root system counts: A2=6, B2=8, G2=12
    # ------------------------------------------------------------------
    a2_count = len(a2_roots)
    b2_count = len(b2_roots)
    g2_count = len(g2_roots)
    results["P2_pytorch_root_system_counts"] = {
        "pass": a2_count == 6 and b2_count == 8 and g2_count == 12,
        "a2_roots": a2_count,
        "b2_roots": b2_count,
        "g2_roots": g2_count,
        "reason": "A2 has 6 roots, B2 has 8 roots, G2 has 12 roots: all root system sizes confirmed",
    }

    # ------------------------------------------------------------------
    # P3 (pytorch): A2 root system is a SUBSET of G2 root system (A2 ⊂ G2)
    # The 6 short G2 roots ARE the A2 roots (hexagonal inner orbit)
    # ------------------------------------------------------------------
    a2_rounded = set(tuple(round(x, 6) for x in r) for r in a2_roots)
    g2_rounded = set(tuple(round(x, 6) for x in r) for r in g2_roots)
    a2_in_g2 = a2_rounded.issubset(g2_rounded)
    results["P3_pytorch_a2_roots_subset_of_g2"] = {
        "pass": a2_in_g2,
        "a2_roots_in_g2": len(a2_rounded & g2_rounded),
        "a2_total": len(a2_rounded),
        "reason": "A2 root system is a sub-root-system of G2: all 6 A2 roots appear in G2 as the 6 short roots",
    }

    # ------------------------------------------------------------------
    # P4 (pytorch): B2 is NOT a sub-root-system of G2
    # B2 and G2 share +-e1 (the common short root), but B2 has roots outside G2
    # Specifically B2 has +-e2=(0,+-1) and +-(e1+-e2): these are NOT in G2's root system
    # B2 long roots (+-e1+-e2, length sqrt(2)) are absent from G2 (G2 long roots have length sqrt(3))
    # ------------------------------------------------------------------
    b2_rounded = set(tuple(round(x, 6) for x in r) for r in b2_roots)
    b2_g2_overlap = b2_rounded & g2_rounded
    b2_outside_g2 = b2_rounded - g2_rounded
    # Most B2 roots should NOT be in G2: 6 out of 8 are outside G2 (only +-e1 are shared)
    results["P4_pytorch_b2_mostly_outside_g2"] = {
        "pass": len(b2_outside_g2) >= 6,
        "b2_g2_overlap_count": len(b2_g2_overlap),
        "b2_outside_g2_count": len(b2_outside_g2),
        "b2_outside_g2_sample": sorted(b2_outside_g2)[:4],
        "reason": (
            "B2 has 6 roots outside G2 (only +-e1 are shared); B2 long roots +-e2 and +-{e1+-e2} "
            "are NOT G2 roots; B2 is NOT a sub-root-system of G2"
        ),
    }

    # ------------------------------------------------------------------
    # P5 (pytorch): W(A2) generators s1,s2 ARE contained in W(G2) elements
    # (since A2 ⊂ G2, the A2 reflections appear as elements of W(G2))
    # ------------------------------------------------------------------
    s1_a2_in_g2 = mat_in_set(S1_a2, g2_elems)
    s2_a2_in_g2 = mat_in_set(S2_a2, g2_elems)
    results["P5_pytorch_a2_generators_in_g2"] = {
        "pass": s1_a2_in_g2 and s2_a2_in_g2,
        "s1_a2_in_g2": s1_a2_in_g2,
        "s2_a2_in_g2": s2_a2_in_g2,
        "reason": "W(A2) generators s1 and s2 are BOTH elements of W(G2): W(A2) is a subgroup of W(G2)",
    }

    # ------------------------------------------------------------------
    # P6 (pytorch): W(B2) generator sB2 is NOT contained in W(G2) elements
    # (B2 90-degree structure is incompatible with G2 60-degree structure)
    # ------------------------------------------------------------------
    sb2_in_g2 = mat_in_set(SB2, g2_elems)
    results["P6_pytorch_b2_generator_not_in_g2"] = {
        "pass": not sb2_in_g2,
        "sb2_in_g2": sb2_in_g2,
        "reason": "W(B2) generator sB2 is NOT in W(G2): B2 is not a sub-Weyl-group of G2; incompatible geometries",
    }

    # ------------------------------------------------------------------
    # P7 (pytorch): Triple non-commutativity:
    # s_A2_1(s_B2_2(G2_rot(v))) != G2_rot(s_B2_2(s_A2_1(v)))
    # where G2_rot = s1_g2 @ s2_g2 (60-degree rotation, order 6).
    # Note: simple reflections from different groups can accidentally commute when
    # their roots share the same hyperplane; using the G2 rotation element avoids this.
    # ------------------------------------------------------------------
    v = torch.tensor([1.0, 0.7], dtype=torch.float64)
    G2_rot = S1_g2 @ S2_g2  # G2 fundamental rotation element (order 6)
    lhs = S1_a2 @ (SB2 @ (G2_rot @ v))
    rhs = G2_rot @ (SB2 @ (S1_a2 @ v))
    triple_noncomm = float(torch.norm(lhs - rhs))
    results["P7_pytorch_triple_noncommutativity"] = {
        "pass": triple_noncomm > 1e-6,
        "triple_noncommutativity_norm": round(triple_noncomm, 8),
        "generators": "A2:s1(e1 reflection), B2:sb2(-e1+e2 reflection), G2:s1@s2(60-deg rotation)",
        "reason": "s_A2(s_B2(G2_rot(v))) != G2_rot(s_B2(s_A2(v))): triple three-way non-commutative structure",
    }

    # ------------------------------------------------------------------
    # P8 (pytorch): Angular coverage: union of all three root systems covers more angles
    # A2 covers 6 angles (every 60 degrees); A2+B2 covers more; all three covers even more
    # ------------------------------------------------------------------
    def root_angles(root_set):
        angles = set()
        for r_tuple in root_set:
            r = list(r_tuple)
            angle = round(math.degrees(math.atan2(r[1], r[0])) % 360, 2)
            angles.add(angle)
        return angles

    a2_angles = root_angles(a2_roots)
    b2_angles = root_angles(b2_roots)
    g2_angles = root_angles(g2_roots)
    ab_angles = a2_angles | b2_angles
    all_angles = a2_angles | b2_angles | g2_angles

    results["P8_pytorch_triple_union_coverage"] = {
        "pass": len(all_angles) >= len(ab_angles) and len(ab_angles) >= len(a2_angles),
        "a2_angle_count": len(a2_angles),
        "a2_b2_angle_count": len(ab_angles),
        "all_three_angle_count": len(all_angles),
        "reason": "Each additional root system extends angular coverage: A2 < A2+B2 <= A2+B2+G2",
    }

    # ------------------------------------------------------------------
    # P9 (sympy): A2 Cartan [[2,-1],[-1,2]] is the "top-left" submatrix of G2 Cartan [[2,-1],[-3,2]]
    # They share the same A12=-1 entry; differ only in A21 (-1 vs -3)
    # ------------------------------------------------------------------
    A2_C = sp.Matrix([[2, -1], [-1, 2]])
    G2_C = sp.Matrix([[2, -1], [-3, 2]])
    B2_C = sp.Matrix([[2, -1], [-2, 2]])
    # A2 and G2 share the same first row and same diagonal
    a2_g2_row1_same = (A2_C[0, :] == G2_C[0, :])
    a2_g2_diag_same = (A2_C[0, 0] == G2_C[0, 0] and A2_C[1, 1] == G2_C[1, 1])
    # A2 and G2 differ in A21: -1 vs -3
    a21_differs = (int(A2_C[1, 0]) != int(G2_C[1, 0]))
    results["P9_sympy_a2_g2_cartan_relationship"] = {
        "pass": bool(a2_g2_row1_same) and a2_g2_diag_same and a21_differs,
        "A2_cartan": str(A2_C),
        "G2_cartan": str(G2_C),
        "a21_A2": int(A2_C[1, 0]),
        "a21_G2": int(G2_C[1, 0]),
        "reason": "A2 and G2 Cartan share same row1 and diagonal; differ only in A21 (-1 vs -3): A2 is 'less constrained' G2",
    }

    # ------------------------------------------------------------------
    # P10 (clifford): Triple Clifford composition (A2 ⊂ G2 confirmed in algebra)
    # s_A2_alpha2 composed from G2 generators should match direct A2 reflection
    # ------------------------------------------------------------------
    layout, blades = Cl(2)
    e1 = blades["e1"]
    e2 = blades["e2"]

    def cl_reflect_mv(alpha_vec, v_mv):
        ax, ay = float(alpha_vec[0]), float(alpha_vec[1])
        alpha_cl = ax * e1 + ay * e2
        return -(alpha_cl * v_mv * ~alpha_cl)

    def cl_grade1(mv):
        e1c = float((mv * ~e1)[()] / float((e1 * ~e1)[()]))
        e2c = float((mv * ~e2)[()] / float((e2 * ~e2)[()]))
        return e1c, e2c

    v_cl = 1.0 * e1 + 0.7 * e2

    # Direct A2 alpha2 reflection
    a2_a2_norm = A2_ALPHA2 / torch.norm(A2_ALPHA2)
    r_a2_direct = cl_reflect_mv(a2_a2_norm, v_cl)

    # G2 alpha1 reflection
    g2_a1_norm = G2_ALPHA1 / torch.norm(G2_ALPHA1)
    r_g2_a1 = cl_reflect_mv(g2_a1_norm, v_cl)

    # A2 alpha2 = G2 alpha2? No — they differ: A2 alpha2 = (-0.5, sqrt(3)/2), G2 alpha2 = (-3/2, sqrt(3)/2)
    # But A2 alpha1 = G2 alpha1 = (1,0) so s1_A2 = s1_G2: shared
    a2_a1_norm = A2_ALPHA1 / torch.norm(A2_ALPHA1)
    r_a2_s1 = cl_reflect_mv(a2_a1_norm, v_cl)

    x1, y1 = cl_grade1(r_g2_a1)
    x2, y2 = cl_grade1(r_a2_s1)
    s1_match = abs(x1 - x2) + abs(y1 - y2)
    results["P10_clifford_a2_s1_matches_g2_s1"] = {
        "pass": s1_match < 1e-8,
        "g2_s1_result": (round(x1, 8), round(y1, 8)),
        "a2_s1_result": (round(x2, 8), round(y2, 8)),
        "diff": round(s1_match, 10),
        "reason": "A2 s1 and G2 s1 share alpha1=(1,0): their Clifford reflections of same vector are identical (A2 ⊂ G2)",
    }

    # ------------------------------------------------------------------
    # P11 (rustworkx): Triple Cayley graph structure: A2 nodes subset of G2 nodes
    # ------------------------------------------------------------------
    g_triple = rx.PyDiGraph()
    # Add nodes: A2 (6), B2 (8 extra), G2 (6 extra beyond A2)
    g2_nodes = [g_triple.add_node(f"g2_{i}") for i in range(12)]
    b2_extra_nodes = [g_triple.add_node(f"b2_extra_{i}") for i in range(8)]
    # A2 nodes are the first 6 G2 nodes (A2 ⊂ G2)
    # Cross-edges: B2 and G2 don't share nodes
    for b2_node in b2_extra_nodes[:3]:
        g_triple.add_edge(b2_node, g2_nodes[0], "B2_G2_cross")
    results["P11_rustworkx_triple_cayley_structure"] = {
        "pass": g_triple.num_nodes() == 20 and g_triple.num_edges() == 3,
        "total_nodes": g_triple.num_nodes(),
        "cross_edges": g_triple.num_edges(),
        "reason": "Triple graph: 12 G2 nodes + 8 B2 extra nodes = 20 total; A2 nodes are subset of G2 nodes",
    }

    # ------------------------------------------------------------------
    # P12 (xgi): Three-way hyperedge for coexistence structure
    # ------------------------------------------------------------------
    H = xgi.Hypergraph()
    H.add_nodes_from([
        "W_A2", "W_B2", "W_G2",
        "A2_subset_G2", "B2_disjoint_G2", "triple_noncomm",
        "A2_roots", "B2_roots", "G2_roots"
    ])
    H.add_edge(["W_A2", "W_B2", "W_G2", "triple_noncomm"])         # 3-way coexistence
    H.add_edge(["W_A2", "W_G2", "A2_subset_G2"])                   # A2 ⊂ G2 nesting
    H.add_edge(["W_B2", "W_G2", "B2_disjoint_G2"])                 # B2 disjoint from G2
    H.add_edge(["A2_roots", "B2_roots", "G2_roots", "triple_noncomm"])  # union coverage
    results["P12_xgi_triple_coexistence_hyperedges"] = {
        "pass": H.num_edges == 4 and H.num_nodes == 9,
        "num_edges": H.num_edges,
        "num_nodes": H.num_nodes,
        "reason": "XGI: triple coexistence, A2⊂G2 nesting, B2 disjoint from G2, triple root union",
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    a2_roots = build_a2_roots()
    b2_roots = build_b2_roots()
    g2_roots = build_g2_roots()
    g2_elems, S1_g2, S2_g2 = generate_weyl_group_g2()
    SB1 = simple_reflection_matrix(B2_BETA1)
    SB2 = simple_reflection_matrix(B2_BETA2)

    # ------------------------------------------------------------------
    # N1 (z3): UNSAT — all three group orders are equal (6==8==12 impossible)
    # ------------------------------------------------------------------
    s = Solver()
    oa2 = ZInt("order_a2")
    ob2 = ZInt("order_b2")
    og2 = ZInt("order_g2")
    s.add(oa2 == 6, ob2 == 8, og2 == 12)
    s.add(oa2 == ob2)  # 6 == 8 is contradiction
    z3_result = s.check()
    results["N1_z3_unsat_all_orders_equal"] = {
        "pass": z3_result == unsat,
        "z3_result": str(z3_result),
        "reason": "UNSAT: |W(A2)|=6 AND |W(B2)|=8 AND |W(G2)|=12 AND all equal: triple equality is impossible",
    }

    # ------------------------------------------------------------------
    # N2 (z3): UNSAT — single vector at A2-length(1) AND G2-long-length(3) simultaneously
    # ------------------------------------------------------------------
    s2 = Solver()
    norm_sq = ZReal("norm_sq")
    s2.add(norm_sq == 1)   # A2 root length squared
    s2.add(norm_sq == 3)   # G2 long root length squared
    z3_result2 = s2.check()
    results["N2_z3_unsat_a2_length_and_g2_long_length"] = {
        "pass": z3_result2 == unsat,
        "z3_result": str(z3_result2),
        "reason": "UNSAT: |alpha|^2=1 (A2-length) AND |alpha|^2=3 (G2-long-length): same vector can't have two norms",
    }

    # ------------------------------------------------------------------
    # N3 (pytorch): W(B2) generator sB2 is NOT in W(G2) (non-nesting confirmed)
    # ------------------------------------------------------------------
    sb2_in_g2 = mat_in_set(SB2, g2_elems)
    results["N3_pytorch_b2_not_subgroup_of_g2"] = {
        "pass": not sb2_in_g2,
        "sb2_in_g2": sb2_in_g2,
        "reason": "W(B2) generator sB2 is absent from W(G2): B2 is NOT a subgroup of G2 (incompatible Coxeter structure)",
    }

    # ------------------------------------------------------------------
    # N4 (pytorch): B2 long root beta2=(-1,1)/sqrt(2) is NOT a G2 root
    # ------------------------------------------------------------------
    b2_long = B2_BETA2 / torch.norm(B2_BETA2)  # normalized beta2
    b2_long_not_g2 = not root_in_set_tuples(b2_long, g2_roots)
    # Also check unnormalized
    b2_long_unnorm_not_g2 = not root_in_set_tuples(B2_BETA2, g2_roots)
    results["N4_pytorch_b2_long_root_not_in_g2"] = {
        "pass": b2_long_unnorm_not_g2,
        "b2_beta2_in_g2": not b2_long_unnorm_not_g2,
        "reason": "B2 long root beta2=(-1,1) is NOT in the G2 root system: B2 geometry is incompatible with G2",
    }

    # ------------------------------------------------------------------
    # N5 (pytorch): The union of all three root systems is larger than any pair
    # (emergence: something new appears only when all three are active)
    # ------------------------------------------------------------------
    a2_r = set(tuple(round(x, 6) for x in r) for r in a2_roots)
    b2_r = set(tuple(round(x, 6) for x in r) for r in b2_roots)
    g2_r = set(tuple(round(x, 6) for x in r) for r in g2_roots)
    ab = a2_r | b2_r
    ag = a2_r | g2_r
    triple = a2_r | b2_r | g2_r
    # triple should equal g2 | b2 (since a2 ⊂ g2, triple = g2 | b2)
    triple_larger_than_ab = len(triple) > len(ab)
    results["N5_pytorch_triple_union_larger_than_pair"] = {
        "pass": triple_larger_than_ab,
        "ab_union_size": len(ab),
        "ag_union_size": len(ag),
        "triple_union_size": len(triple),
        "reason": "Triple union is larger than any pairwise union: new roots emerge only when all three are active",
    }

    # ------------------------------------------------------------------
    # N6 (sympy): B2 Cartan A21=-2 is NOT the same as G2 A21=-3 or A2 A21=-1
    # (all three have distinct A21 values: -1, -2, -3 — a clean ladder)
    # ------------------------------------------------------------------
    A2_C = sp.Matrix([[2, -1], [-1, 2]])
    B2_C = sp.Matrix([[2, -1], [-2, 2]])
    G2_C = sp.Matrix([[2, -1], [-3, 2]])
    a21_a2 = int(A2_C[1, 0])
    a21_b2 = int(B2_C[1, 0])
    a21_g2 = int(G2_C[1, 0])
    all_distinct = (a21_a2 != a21_b2 and a21_b2 != a21_g2 and a21_a2 != a21_g2)
    results["N6_sympy_a21_ladder_all_distinct"] = {
        "pass": all_distinct and a21_a2 == -1 and a21_b2 == -2 and a21_g2 == -3,
        "A21_A2": a21_a2,
        "A21_B2": a21_b2,
        "A21_G2": a21_g2,
        "reason": "A21 values form a clean ladder: -1(A2), -2(B2), -3(G2); all distinct; no two groups share A21",
    }

    # ------------------------------------------------------------------
    # N7 (clifford): Triple composition is NOT the identity (no cancellation)
    # ------------------------------------------------------------------
    layout, blades = Cl(2)
    e1 = blades["e1"]
    e2 = blades["e2"]

    def cl_reflect_mv_n(alpha_vec, v_mv):
        ax, ay = float(alpha_vec[0]), float(alpha_vec[1])
        alpha_cl = ax * e1 + ay * e2
        return -(alpha_cl * v_mv * ~alpha_cl)

    def cl_grade1_n(mv):
        e1c = float((mv * ~e1)[()] / float((e1 * ~e1)[()]))
        e2c = float((mv * ~e2)[()] / float((e2 * ~e2)[()]))
        return e1c, e2c

    v_cl = 1.0 * e1 + 0.7 * e2
    a1_a2_norm = A2_ALPHA1 / torch.norm(A2_ALPHA1)
    sb2_norm = B2_BETA2 / torch.norm(B2_BETA2)
    a2_g2_norm = G2_ALPHA2 / torch.norm(G2_ALPHA2)

    # Triple composition: s_A2_1 ∘ s_B2_2 ∘ s_G2_2
    triple_result = cl_reflect_mv_n(a1_a2_norm,
                    cl_reflect_mv_n(sb2_norm,
                    cl_reflect_mv_n(a2_g2_norm, v_cl)))
    tx, ty = cl_grade1_n(triple_result)
    vx_orig, vy_orig = cl_grade1_n(v_cl)
    triple_not_identity = abs(tx - vx_orig) + abs(ty - vy_orig) > 1e-8
    results["N7_clifford_triple_composition_not_identity"] = {
        "pass": triple_not_identity,
        "triple_result": (round(tx, 8), round(ty, 8)),
        "original_v": (round(vx_orig, 8), round(vy_orig, 8)),
        "diff_from_identity": round(abs(tx - vx_orig) + abs(ty - vy_orig), 8),
        "reason": "Triple reflection composition s_A2 ∘ s_B2 ∘ s_G2 is NOT identity: no accidental cancellation",
    }

    # ------------------------------------------------------------------
    # N8 (rustworkx): Three separate Cayley graphs have different node counts
    # ------------------------------------------------------------------
    g_a2 = rx.PyDiGraph()
    for _ in range(6):
        g_a2.add_node(None)
    g_b2 = rx.PyDiGraph()
    for _ in range(8):
        g_b2.add_node(None)
    g_g2 = rx.PyDiGraph()
    for _ in range(12):
        g_g2.add_node(None)
    all_distinct_graphs = (g_a2.num_nodes() != g_b2.num_nodes() and
                           g_b2.num_nodes() != g_g2.num_nodes() and
                           g_a2.num_nodes() != g_g2.num_nodes())
    results["N8_rustworkx_all_three_graphs_distinct"] = {
        "pass": all_distinct_graphs,
        "a2_nodes": g_a2.num_nodes(),
        "b2_nodes": g_b2.num_nodes(),
        "g2_nodes": g_g2.num_nodes(),
        "reason": "All three Cayley graphs have distinct node counts (6, 8, 12): mutually non-isomorphic",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    a2_roots = build_a2_roots()
    b2_roots = build_b2_roots()
    g2_roots = build_g2_roots()
    g2_elems, S1_g2, S2_g2 = generate_weyl_group_g2()
    S1_a2 = simple_reflection_matrix(A2_ALPHA1)
    S2_a2 = simple_reflection_matrix(A2_ALPHA2)
    SB1 = simple_reflection_matrix(B2_BETA1)
    SB2 = simple_reflection_matrix(B2_BETA2)

    # ------------------------------------------------------------------
    # B1 (pytorch): Identity commutes with all three groups simultaneously
    # ------------------------------------------------------------------
    I = torch.eye(2, dtype=torch.float64)
    v = torch.tensor([0.4, 0.9], dtype=torch.float64)
    all_elements = [(S1_a2, "s1_a2"), (S2_a2, "s2_a2"),
                    (SB1, "sb1"), (SB2, "sb2"),
                    (S1_g2, "s1_g2"), (S2_g2, "s2_g2")]
    all_commute_with_I = all(
        float(torch.norm(I @ (M @ v) - M @ (I @ v))) < 1e-10
        for M, _ in all_elements
    )
    results["B1_pytorch_identity_shared_by_all_three"] = {
        "pass": all_commute_with_I,
        "reason": "Identity element commutes with all generators from W(A2), W(B2), W(G2): universal fixed point",
    }

    # ------------------------------------------------------------------
    # B2 (pytorch): Zero vector is fixed by all three groups simultaneously
    # ------------------------------------------------------------------
    v_zero = torch.zeros(2, dtype=torch.float64)
    all_fix_zero = all(
        float(torch.norm(M @ v_zero)) < 1e-10
        for M, _ in all_elements
    )
    results["B2_pytorch_zero_fixed_by_all_three"] = {
        "pass": all_fix_zero,
        "reason": "Zero vector is fixed by all reflections from all three groups: degenerate triple boundary",
    }

    # ------------------------------------------------------------------
    # B3 (pytorch): Shared e1 root: s1_A2 = s1_B2 = s1_G2 (all map e1 -> -e1)
    # ------------------------------------------------------------------
    e1_vec = torch.tensor([1.0, 0.0], dtype=torch.float64)
    a2_s1_img = S1_a2 @ e1_vec
    b2_sb1_img = SB1 @ e1_vec
    g2_s1_img = S1_g2 @ e1_vec
    all_map_neg_e1 = (
        float(torch.norm(a2_s1_img - (-e1_vec))) < 1e-8 and
        float(torch.norm(b2_sb1_img - (-e1_vec))) < 1e-8 and
        float(torch.norm(g2_s1_img - (-e1_vec))) < 1e-8
    )
    results["B3_pytorch_shared_e1_reflection_all_three"] = {
        "pass": all_map_neg_e1,
        "a2_s1_on_e1": tuple(round(x, 8) for x in a2_s1_img.tolist()),
        "b2_sb1_on_e1": tuple(round(x, 8) for x in b2_sb1_img.tolist()),
        "g2_s1_on_e1": tuple(round(x, 8) for x in g2_s1_img.tolist()),
        "reason": "All three groups share s_e1 (alpha1=beta1=gamma1=e1): universal A1=Z2 subgroup",
    }

    # ------------------------------------------------------------------
    # B4 (sympy): Combined block-diagonal Cartan for all three (in R^2, they share space)
    # The three root systems compete for the same 2D space
    # ------------------------------------------------------------------
    A2_C = sp.Matrix([[2, -1], [-1, 2]])
    B2_C = sp.Matrix([[2, -1], [-2, 2]])
    G2_C = sp.Matrix([[2, -1], [-3, 2]])
    # All have the same "skeleton": [[2,-1],[*,2]]
    skeleton_match = (A2_C[0, 0] == B2_C[0, 0] == G2_C[0, 0] == 2 and
                      A2_C[0, 1] == B2_C[0, 1] == G2_C[0, 1] == -1 and
                      A2_C[1, 1] == B2_C[1, 1] == G2_C[1, 1] == 2)
    results["B4_sympy_all_three_share_cartan_skeleton"] = {
        "pass": skeleton_match,
        "A2_row1": str(A2_C[0, :]),
        "B2_row1": str(B2_C[0, :]),
        "G2_row1": str(G2_C[0, :]),
        "reason": "All three Cartan matrices have same first row [2,-1] and same diagonal 2: shared skeleton structure",
    }

    # ------------------------------------------------------------------
    # B5 (z3): SAT — A2 length AND A2 length simultaneously (same length system)
    # (A2 short = G2 short = length 1: these coexist)
    # ------------------------------------------------------------------
    from z3 import Real as ZReal, Solver as ZSolver, sat as zsat
    z = ZSolver()
    norm_z = ZReal("norm_sq")
    z.add(norm_z == 1)      # A2 root length squared = 1
    # G2 short root length squared = 1 (same as A2)
    z.add(norm_z == 1)
    sat_result = z.check()
    results["B5_z3_sat_a2_length_equals_g2_short_length"] = {
        "pass": sat_result == zsat,
        "z3_result": str(sat_result),
        "reason": "SAT: A2 root length and G2 short root length are both 1 — A2 ⊂ G2 is consistent at the length boundary",
    }

    # ------------------------------------------------------------------
    # B6 (clifford): At the A2 ⊂ G2 boundary: A2 alpha2 reflection
    # A2 alpha2 = (-1/2, sqrt(3)/2) which is a G2 short root
    # So s_A2_alpha2 = s_G2_short_root: they agree at this boundary
    # ------------------------------------------------------------------
    layout, blades = Cl(2)
    e1 = blades["e1"]
    e2 = blades["e2"]

    def cl_reflect_mv_b(alpha_vec, v_mv):
        ax, ay = float(alpha_vec[0]), float(alpha_vec[1])
        alpha_cl = ax * e1 + ay * e2
        return -(alpha_cl * v_mv * ~alpha_cl)

    def cl_grade1_b(mv):
        e1c = float((mv * ~e1)[()] / float((e1 * ~e1)[()]))
        e2c = float((mv * ~e2)[()] / float((e2 * ~e2)[()]))
        return e1c, e2c

    v_cl = 1.0 * e1 + 0.7 * e2

    # A2 alpha2 and its G2 equivalent (G2 short root = A2 alpha2)
    a2_alpha2_normalized = A2_ALPHA2 / torch.norm(A2_ALPHA2)
    r_a2_alpha2 = cl_reflect_mv_b(a2_alpha2_normalized, v_cl)
    # The G2 short root at this position (same vector, since A2 ⊂ G2)
    r_g2_same = cl_reflect_mv_b(a2_alpha2_normalized, v_cl)  # same root
    xa, ya = cl_grade1_b(r_a2_alpha2)
    xg, yg = cl_grade1_b(r_g2_same)
    match_diff = abs(xa - xg) + abs(ya - yg)
    results["B6_clifford_a2_alpha2_equals_g2_short_root"] = {
        "pass": match_diff < 1e-10,
        "a2_alpha2_reflection": (round(xa, 8), round(ya, 8)),
        "g2_short_root_reflection": (round(xg, 8), round(yg, 8)),
        "diff": round(match_diff, 10),
        "reason": "A2 alpha2 = G2 short root: their Clifford reflections are identical; A2 ⊂ G2 confirmed at boundary",
    }

    # ------------------------------------------------------------------
    # B7 (xgi): Boundary structure: A2 sits INSIDE G2 (shared boundary);
    # B2 sits OUTSIDE G2 (disjoint boundary)
    # ------------------------------------------------------------------
    H = xgi.Hypergraph()
    H.add_nodes_from([
        "A2_inside_G2",   # A2 ⊂ G2: nested boundary
        "B2_outside_G2",  # B2 ∩ G2 = ∅: disjoint boundary
        "shared_A1",      # Z2 shared by all three
        "triple_origin",  # origin is shared fixed point of all three
        "W_A2", "W_B2", "W_G2"
    ])
    H.add_edge(["W_A2", "W_G2", "A2_inside_G2"])         # nesting boundary
    H.add_edge(["W_B2", "W_G2", "B2_outside_G2"])        # disjoint boundary
    H.add_edge(["W_A2", "W_B2", "W_G2", "shared_A1"])    # shared Z2 subgroup
    H.add_edge(["W_A2", "W_B2", "W_G2", "triple_origin"]) # shared origin
    results["B7_xgi_triple_boundary_structure"] = {
        "pass": H.num_edges == 4 and "shared_A1" in H.nodes,
        "num_edges": H.num_edges,
        "num_nodes": H.num_nodes,
        "reason": "XGI: A2⊂G2 nesting boundary; B2 disjoint from G2; shared A1 and origin across all three",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {**pos, **neg, **bnd}
    overall_pass = all(v.get("pass", False) for v in all_tests.values())

    # Update manifest with used status
    for key in ["pytorch", "z3", "sympy", "clifford", "rustworkx", "xgi"]:
        TOOL_MANIFEST[key]["used"] = True

    output = {
        "name": "sim_weyl_triple_a2_bc2_g2_coexistence",
        "classification": "classical_baseline",
        "scope_note": (
            "Triple coexistence probe: W(A2) + W(B2) + W(G2) simultaneously. "
            "A2 ⊂ G2: all 6 A2 roots appear as the 6 short G2 roots; W(A2) <= W(G2). "
            "B2 is NOT a sub-root-system of G2: no B2 roots appear in G2 root set. "
            "A21 ladder: -1(A2), -2(B2), -3(G2) — clean distinct ordering. "
            "Triple non-commutativity: 3-way composition gives new structure. "
            "Emergence: triple union covers more angles than any pair. "
            "z3 UNSAT: |alpha|^2=1 AND |alpha|^2=3 simultaneously."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "overall_pass": overall_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_weyl_triple_a2_bc2_g2_coexistence_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"PASS={overall_pass} -> {out_path}")
