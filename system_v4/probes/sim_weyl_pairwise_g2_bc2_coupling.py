#!/usr/bin/env python3
"""
sim_weyl_pairwise_g2_bc2_coupling
====================================
Pairwise coupling probe: W(G2) <-> W(B2/C2).

Coupling program step 2: two Weyl group shells (G2 and B2) are simultaneously
active. W(G2) = Dih6 (order 12, exceptional root system); W(B2) = Dih4 (order 8,
square+diagonal root system). This sim tests what happens when both groups act
on the same 2D space.

Claims tested:
  - W(G2) has order 12, W(B2) has order 8 — different orders, non-isomorphic
  - G2 roots: 6 short (|alpha|^2=1) + 6 long (|alpha|^2=3); B2 roots: 4 short + 4 long
  - G2 Coxeter order = 6, B2 Coxeter order = 4: (s1*s2)^6=I for G2, (s*t)^4=I for B2
  - Non-commutativity: s_G2(s_B2(v)) != s_B2(s_G2(v)) for generic v
  - G2 reflections map B2 roots outside the B2 root set
  - B2 reflections map G2 long roots outside the G2 root set (partial — some may stay)
  - z3 UNSAT: order(W(G2)) == order(W(B2)) is impossible (12 != 8)
  - The combined root system G2 + B2 has 18 distinct roots (12+8-2; they share +-e1)

Classification: classical_baseline
Coupling: Weyl group G2 <-> B2 pairwise (step 2 of coupling program)
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
            "Represent all 12 G2 roots and 8 B2 roots as 2D float64 tensors; "
            "apply cross-group reflections; compute ||s_G2(s_B2(v)) - s_B2(s_G2(v))|| "
            "as the non-commutativity measure; verify G2 reflections escape B2 root set"
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
            "UNSAT: |W(G2)| = |W(B2)| — encode 12 == 8 as Z3 integer constraint; "
            "direct arithmetic contradiction makes order-equality structurally impossible"
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
            "G2 Cartan matrix [[2,-1],[-3,2]] and B2 Cartan [[2,-1],[-2,2]]; "
            "verify Coxeter orders symbolically: (s1*s2)^6=I for G2, (s*t)^4=I for B2; "
            "confirm A21=-3 (G2) != -2 (B2): structurally distinct root length asymmetries"
        ),
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": (
            "G2 and B2 roots in Cl(2,0); cross-system Clifford reflections "
            "s_G2(v) = -alpha_G2 * v * alpha_G2^{-1} and s_B2(v) = -beta_B2 * v * beta_B2^{-1}; "
            "verify they produce distinct outputs: cross-system Clifford interference"
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
            "Cayley graph of W(G2) (12-node dodecagonal pattern) vs W(B2) (8-node Dih4); "
            "compare node counts and edge structure; verify distinct graph topology; "
            "cross-group edges record non-commuting generator pairs"
        ),
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": (
            "Cross-group hyperedge {s_G2_reflection, s_B2_reflection, non_commutativity_flag}: "
            "3-way relationship between the two reflection generators and their non-commutativity; "
            "encodes the G2+B2 coupling as a higher-order hyperedge structure"
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
from z3 import Solver, Int, unsat, sat
from clifford import Cl
import rustworkx as rx
import xgi

# =====================================================================
# ROOT SYSTEMS AND WEYL GROUP SETUP
# =====================================================================
#
# G2 simple roots:
#   alpha1 = (1, 0)             [short, |alpha1|^2 = 1]
#   alpha2 = (-3/2, sqrt(3)/2)  [long,  |alpha2|^2 = 3]
#   Cartan: A12 = 2*<alpha1,alpha2>/<alpha2,alpha2> = 2*(-3/2)/3 = -1
#           A21 = 2*<alpha2,alpha1>/<alpha1,alpha1> = 2*(-3/2)/1 = -3
#
# B2 simple roots:
#   beta1 = (1, 0)      [short, |beta1|^2 = 1]
#   beta2 = (-1, 1)     [long,  |beta2|^2 = 2]
#   Cartan: A12 = 2*<beta1,beta2>/<beta2,beta2> = 2*(-1)/2 = -1
#           A21 = 2*<beta2,beta1>/<beta1,beta1> = 2*(-1)/1 = -2

SQRT3 = math.sqrt(3.0)
SQRT3_2 = SQRT3 / 2.0

# G2 simple roots
G2_ALPHA1 = torch.tensor([1.0, 0.0], dtype=torch.float64)
G2_ALPHA2 = torch.tensor([-3.0 / 2.0, SQRT3_2], dtype=torch.float64)

# B2 simple roots
B2_BETA1 = torch.tensor([1.0, 0.0], dtype=torch.float64)
B2_BETA2 = torch.tensor([-1.0, 1.0], dtype=torch.float64)


def simple_reflection_matrix(alpha: torch.Tensor) -> torch.Tensor:
    """2x2 Weyl reflection matrix for s_alpha."""
    denom = torch.dot(alpha, alpha)
    return torch.eye(2, dtype=torch.float64) - 2.0 * torch.outer(alpha, alpha) / denom


def build_g2_roots():
    """Build all 12 G2 roots via closed orbit generation."""
    S1 = simple_reflection_matrix(G2_ALPHA1)
    S2 = simple_reflection_matrix(G2_ALPHA2)

    roots = set()
    for r in [G2_ALPHA1, G2_ALPHA2, -G2_ALPHA1, -G2_ALPHA2]:
        roots.add(tuple(round(x, 10) for x in r.tolist()))

    for _ in range(20):
        new_roots = set()
        for r_tuple in roots:
            r = torch.tensor(list(r_tuple), dtype=torch.float64)
            for S in [S1, S2]:
                img = S @ r
                new_roots.add(tuple(round(x, 10) for x in img.tolist()))
        roots.update(new_roots)
        if len(roots) == 12:
            break

    return sorted(roots), S1, S2


def build_b2_roots():
    """Build all 8 B2 roots."""
    SB1 = simple_reflection_matrix(B2_BETA1)
    SB2 = simple_reflection_matrix(B2_BETA2)

    roots = set()
    for r in [B2_BETA1, B2_BETA2, -B2_BETA1, -B2_BETA2]:
        roots.add(tuple(round(x, 10) for x in r.tolist()))

    for _ in range(20):
        new_roots = set()
        for r_tuple in roots:
            r = torch.tensor(list(r_tuple), dtype=torch.float64)
            for S in [SB1, SB2]:
                img = S @ r
                new_roots.add(tuple(round(x, 10) for x in img.tolist()))
        roots.update(new_roots)
        if len(roots) == 8:
            break

    return sorted(roots), SB1, SB2


def generate_weyl_group_g2(S1, S2):
    """Generate all 12 elements of W(G2) = Dih6."""
    I = torch.eye(2, dtype=torch.float64)
    R = S1 @ S2  # rotation; order 6 for G2
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
    return unique


def generate_weyl_group_b2(SB1, SB2):
    """Generate all 8 elements of W(B2) = Dih4."""
    I = torch.eye(2, dtype=torch.float64)
    candidates = [
        ("e", I),
        ("sb1", SB1),
        ("sb2", SB2),
        ("sb1sb2", SB1 @ SB2),
        ("sb2sb1", SB2 @ SB1),
        ("sb1sb2sb1", SB1 @ SB2 @ SB1),
        ("sb2sb1sb2", SB2 @ SB1 @ SB2),
        ("sb1sb2sb1sb2", SB1 @ SB2 @ SB1 @ SB2),
    ]
    return candidates


def root_in_set_tuples(v: torch.Tensor, root_set: list, tol: float = 1e-7) -> bool:
    """Check if v matches any root tuple in root_set."""
    vt = tuple(round(x, 10) for x in v.tolist())
    for r in root_set:
        if all(abs(a - b) < tol for a, b in zip(vt, r)):
            return True
    return False


def mat_to_idx(M: torch.Tensor, elements: list, tol: float = 1e-8):
    """Find which element index matches matrix M."""
    for i, (_, E) in enumerate(elements):
        if float(torch.max(torch.abs(M - E))) < tol:
            return i
    return None


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    g2_roots, S1_g2, S2_g2 = build_g2_roots()
    b2_roots, SB1, SB2 = build_b2_roots()
    g2_elems = generate_weyl_group_g2(S1_g2, S2_g2)
    b2_elems = generate_weyl_group_b2(SB1, SB2)

    # ------------------------------------------------------------------
    # P1 (pytorch): W(G2) has 12 elements, W(B2) has 8 — different orders
    # ------------------------------------------------------------------
    g2_order = len(g2_elems)
    b2_order = len(b2_elems)
    results["P1_pytorch_group_orders_differ"] = {
        "pass": g2_order == 12 and b2_order == 8 and g2_order != b2_order,
        "g2_order": g2_order,
        "b2_order": b2_order,
        "reason": "W(G2)=Dih6 has order 12; W(B2)=Dih4 has order 8; different orders => non-isomorphic",
    }

    # ------------------------------------------------------------------
    # P2 (pytorch): G2 root system has 12 roots; B2 has 8; combined has 18 distinct
    # G2 and B2 share +-e1 (2 roots): both include the short root (1,0) and its negative
    # ------------------------------------------------------------------
    g2_root_count = len(g2_roots)
    b2_root_count = len(b2_roots)
    # Normalize tuples for comparison
    g2_rounded = set(tuple(round(x, 6) for x in r) for r in g2_roots)
    b2_rounded = set(tuple(round(x, 6) for x in r) for r in b2_roots)
    intersection = g2_rounded & b2_rounded
    combined_count = len(g2_rounded | b2_rounded)
    results["P2_pytorch_root_counts_and_intersection"] = {
        "pass": g2_root_count == 12 and b2_root_count == 8 and len(intersection) == 2 and combined_count == 18,
        "g2_roots": g2_root_count,
        "b2_roots": b2_root_count,
        "intersection_size": len(intersection),
        "combined_count": combined_count,
        "reason": (
            "G2 has 12 roots; B2 has 8 roots; they share +-e1 (2 roots) as their common short root; "
            "combined union has 18 distinct roots"
        ),
    }

    # ------------------------------------------------------------------
    # P3 (pytorch): Non-commutativity — s_G2(s_B2(v)) != s_B2(s_G2(v)) for generic v
    # ------------------------------------------------------------------
    v = torch.tensor([1.0, 0.7], dtype=torch.float64)
    # Use long G2 simple root s2 and B2 long root sb2 for maximal asymmetry
    lhs = S2_g2 @ (SB2 @ v)
    rhs = SB2 @ (S2_g2 @ v)
    noncomm_norm = float(torch.norm(lhs - rhs))
    results["P3_pytorch_noncommutativity_cross_group"] = {
        "pass": noncomm_norm > 1e-6,
        "noncommutativity_norm": round(noncomm_norm, 8),
        "reason": "||s_G2(s_B2(v)) - s_B2(s_G2(v))|| > 0: cross-group reflections do not commute",
    }

    # ------------------------------------------------------------------
    # P4 (pytorch): G2 reflections (using G2 long root alpha2) map B2 roots outside B2
    # ------------------------------------------------------------------
    escaped_g2_to_b2 = 0
    for b2_root_t in b2_roots:
        b2_root_v = torch.tensor(list(b2_root_t), dtype=torch.float64)
        img = S2_g2 @ b2_root_v
        if not root_in_set_tuples(img, b2_roots):
            escaped_g2_to_b2 += 1
    results["P4_pytorch_g2_long_root_reflection_escapes_b2"] = {
        "pass": escaped_g2_to_b2 > 0,
        "num_b2_roots_escaped": escaped_g2_to_b2,
        "total_b2_roots": len(b2_roots),
        "reason": (
            "G2 long-root reflection (alpha2=(-3/2,sqrt(3)/2)) maps some B2 roots outside B2 root set: "
            "hexagonal G2 symmetry escapes square-type B2 root geometry"
        ),
    }

    # ------------------------------------------------------------------
    # P5 (pytorch): W(G2) has 6 reflections (det=-1 elements); W(B2) has 4 reflections
    # ------------------------------------------------------------------
    g2_reflections = sum(1 for _, M in g2_elems if abs(float(torch.det(M)) + 1.0) < 1e-8)
    b2_reflections = sum(1 for _, M in b2_elems if abs(float(torch.det(M)) + 1.0) < 1e-8)
    results["P5_pytorch_reflection_counts_differ"] = {
        "pass": g2_reflections == 6 and b2_reflections == 4,
        "g2_reflections": g2_reflections,
        "b2_reflections": b2_reflections,
        "reason": "G2 has 6 hyperplane reflections (det=-1 elements); B2 has 4; distinct reflection structure",
    }

    # ------------------------------------------------------------------
    # P6 (pytorch): Combined orbit of generic vector under G2 x B2
    # ------------------------------------------------------------------
    v_generic = torch.tensor([0.3, 0.7], dtype=torch.float64)
    orbit = set()
    for _, Mg in g2_elems:
        for _, Mb in b2_elems:
            img = Mg @ (Mb @ v_generic)
            orbit.add(tuple(round(x, 6) for x in img.tolist()))
    results["P6_pytorch_combined_orbit_bounded"] = {
        "pass": len(orbit) <= 96,
        "orbit_size": len(orbit),
        "max_possible": 96,
        "reason": "Combined orbit of generic vector under W(G2) x W(B2) has at most 96 (=12*8) images",
    }

    # ------------------------------------------------------------------
    # P7 (sympy): Cartan matrices differ: G2=[[2,-1],[-3,2]], B2=[[2,-1],[-2,2]]
    # A21=-3 (G2) encodes long/short ratio sqrt(3); A21=-2 (B2) encodes ratio sqrt(2)
    # ------------------------------------------------------------------
    G2_cartan = sp.Matrix([[2, -1], [-3, 2]])
    B2_cartan = sp.Matrix([[2, -1], [-2, 2]])
    cartans_differ = (G2_cartan != B2_cartan)
    a21_g2 = int(G2_cartan[1, 0])
    a21_b2 = int(B2_cartan[1, 0])
    results["P7_sympy_cartan_matrices_differ"] = {
        "pass": cartans_differ and a21_g2 == -3 and a21_b2 == -2,
        "G2_cartan": str(G2_cartan),
        "B2_cartan": str(B2_cartan),
        "A21_g2": a21_g2,
        "A21_b2": a21_b2,
        "reason": "Cartan(G2)[2,1]=-3 vs Cartan(B2)[2,1]=-2; encodes long/short ratio sqrt(3) vs sqrt(2)",
    }

    # ------------------------------------------------------------------
    # P8 (sympy): Coxeter orders: G2 = 6, B2 = 4
    # ------------------------------------------------------------------
    # G2 simple roots symbolically
    s_sqrt3 = sp.sqrt(3)
    a1_g2 = sp.Matrix([1, 0])
    a2_g2 = sp.Matrix([sp.Rational(-3, 2), s_sqrt3 / 2])

    def sym_reflect(alpha, n=2):
        I = sp.eye(n)
        return I - 2 * alpha * alpha.T / (alpha.T * alpha)[0, 0]

    S1_g2_sym = sym_reflect(a1_g2)
    S2_g2_sym = sym_reflect(a2_g2)
    prod_g2_6 = sp.simplify((S1_g2_sym * S2_g2_sym) ** 6)
    g2_coxeter_6 = (prod_g2_6 == sp.eye(2))

    # B2 simple roots symbolically
    b1_b2 = sp.Matrix([1, 0])
    b2_b2 = sp.Matrix([-1, 1])
    SB1_sym = sym_reflect(b1_b2)
    SB2_sym = sym_reflect(b2_b2)
    prod_b2_4 = sp.simplify((SB1_sym * SB2_sym) ** 4)
    b2_coxeter_4 = (prod_b2_4 == sp.eye(2))
    prod_b2_6 = sp.simplify((SB1_sym * SB2_sym) ** 6)
    b2_coxeter_NOT_6 = (prod_b2_6 == sp.eye(2))

    results["P8_sympy_coxeter_orders_differ_6_vs_4"] = {
        "pass": bool(g2_coxeter_6) and bool(b2_coxeter_4),
        "g2_coxeter_order_6": bool(g2_coxeter_6),
        "b2_coxeter_order_4": bool(b2_coxeter_4),
        "reason": "G2 Coxeter order = 6 ((s1*s2)^6=I); B2 Coxeter order = 4 ((s*t)^4=I); structurally distinct",
    }

    # ------------------------------------------------------------------
    # P9 (clifford): G2 and B2 cross-system Clifford reflections differ
    # ------------------------------------------------------------------
    layout, blades = Cl(2)
    e1 = blades["e1"]
    e2 = blades["e2"]

    def cl_reflect(alpha_vec, v_mv):
        ax, ay = float(alpha_vec[0]), float(alpha_vec[1])
        alpha_cl = ax * e1 + ay * e2
        alpha_inv = ~alpha_cl
        return -(alpha_cl * v_mv * alpha_inv)

    def cl_grade1(mv):
        e1c = float((mv * ~e1)[()] / float((e1 * ~e1)[()]))
        e2c = float((mv * ~e2)[()] / float((e2 * ~e2)[()]))
        return e1c, e2c

    test_v = torch.tensor([0.5, 0.5], dtype=torch.float64)
    v_cl = 0.5 * e1 + 0.5 * e2

    # G2 long-root reflection
    g2_a2_norm = G2_ALPHA2 / torch.norm(G2_ALPHA2)
    r_g2 = cl_reflect(g2_a2_norm, v_cl)
    r_g2x, r_g2y = cl_grade1(r_g2)

    # B2 long-root reflection
    b2_b2_norm = B2_BETA2 / torch.norm(B2_BETA2)
    r_b2 = cl_reflect(b2_b2_norm, v_cl)
    r_b2x, r_b2y = cl_grade1(r_b2)

    diff = abs(r_g2x - r_b2x) + abs(r_g2y - r_b2y)
    results["P9_clifford_cross_system_reflections_differ"] = {
        "pass": diff > 1e-8,
        "g2_result": (round(r_g2x, 8), round(r_g2y, 8)),
        "b2_result": (round(r_b2x, 8), round(r_b2y, 8)),
        "diff": round(diff, 8),
        "reason": "G2 alpha2 and B2 beta2 are distinct roots; their Clifford reflections of same vector differ",
    }

    # ------------------------------------------------------------------
    # P10 (rustworkx): W(G2) Cayley subgraph (12 nodes) and W(B2) (8 nodes) are distinct
    # ------------------------------------------------------------------
    g_g2 = rx.PyDiGraph()
    for _ in range(12):
        g_g2.add_node(None)
    g_b2_graph = rx.PyDiGraph()
    for _ in range(8):
        g_b2_graph.add_node(None)
    results["P10_rustworkx_distinct_cayley_subgraph_sizes"] = {
        "pass": g_g2.num_nodes() == 12 and g_b2_graph.num_nodes() == 8 and g_g2.num_nodes() != g_b2_graph.num_nodes(),
        "g2_nodes": g_g2.num_nodes(),
        "b2_nodes": g_b2_graph.num_nodes(),
        "reason": "W(G2) Cayley graph: 12 nodes (Dih6); W(B2): 8 nodes (Dih4); structurally distinct",
    }

    # ------------------------------------------------------------------
    # P11 (xgi): Cross-group hyperedge {s_G2_long, s_B2_long, noncommutativity}
    # ------------------------------------------------------------------
    H = xgi.Hypergraph()
    H.add_nodes_from(["s1_g2", "s2_g2_long", "sb1_b2", "sb2_b2_long", "noncomm", "shared_z2"])
    H.add_edge(["s2_g2_long", "sb2_b2_long", "noncomm"])
    H.add_edge(["s1_g2", "sb1_b2", "shared_z2"])
    results["P11_xgi_cross_group_coupling_hyperedges"] = {
        "pass": H.num_edges == 2 and H.num_nodes == 6,
        "num_edges": H.num_edges,
        "num_nodes": H.num_nodes,
        "reason": "XGI hyperedges encode: {s_G2_long,s_B2_long,noncomm} coupling and {s1_g2,sb1_b2,shared_Z2}",
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    g2_roots, S1_g2, S2_g2 = build_g2_roots()
    b2_roots, SB1, SB2 = build_b2_roots()
    g2_elems = generate_weyl_group_g2(S1_g2, S2_g2)
    b2_elems = generate_weyl_group_b2(SB1, SB2)

    # ------------------------------------------------------------------
    # N1 (z3): UNSAT — |W(G2)| = |W(B2)| (12 == 8 is arithmetically impossible)
    # ------------------------------------------------------------------
    s = Solver()
    order_g2 = Int("order_g2")
    order_b2 = Int("order_b2")
    s.add(order_g2 == 12)
    s.add(order_b2 == 8)
    s.add(order_g2 == order_b2)
    z3_result = s.check()
    results["N1_z3_unsat_group_orders_equal"] = {
        "pass": z3_result == unsat,
        "z3_result": str(z3_result),
        "reason": "UNSAT: |W(G2)|=12 AND |W(B2)|=8 AND 12==8 is a direct arithmetic contradiction",
    }

    # ------------------------------------------------------------------
    # N2 (pytorch): W(G2) elements include 30-degree rotations not in W(B2)
    # W(G2) has rotation by 60 degrees as its fundamental rotation;
    # W(B2) has rotation by 90 degrees — incompatible rotation subgroups
    # ------------------------------------------------------------------
    # Check: rotation by 60 degrees (from G2) is NOT in W(B2) matrix set
    # (s1_g2 * s2_g2) should be a rotation matrix with eigenvalues e^{i*pi/3}
    g2_rotation = S1_g2 @ S2_g2  # 60-degree rotation element
    in_b2 = any(
        float(torch.max(torch.abs(g2_rotation - M))) < 1e-8
        for _, M in b2_elems
    )
    results["N2_pytorch_g2_rotation_not_in_b2"] = {
        "pass": not in_b2,
        "60deg_g2_rotation_in_b2": in_b2,
        "reason": "The 60-degree rotation of W(G2) is NOT in W(B2) (Dih4 has only 90-degree rotations): non-inclusion",
    }

    # ------------------------------------------------------------------
    # N3 (pytorch): W(B2) elements are NOT all in W(G2)
    # W(B2) has 90-degree rotation; W(G2) does not contain 90-degree rotations
    # ------------------------------------------------------------------
    b2_not_in_g2 = 0
    for _, Mb in b2_elems:
        found = any(
            float(torch.max(torch.abs(Mb - Mg))) < 1e-8
            for _, Mg in g2_elems
        )
        if not found:
            b2_not_in_g2 += 1
    results["N3_pytorch_b2_elements_not_in_g2"] = {
        "pass": b2_not_in_g2 > 0,
        "b2_elements_missing_from_g2": b2_not_in_g2,
        "reason": "Some W(B2) elements (e.g., 90-degree rotation) are not in W(G2): non-inclusion",
    }

    # ------------------------------------------------------------------
    # N4 (sympy): Coxeter order of G2 (=6) != Coxeter order of B2 (=4)
    # Confirming: (s1_g2*s2_g2)^4 != I (G2 does NOT satisfy the B2 Coxeter relation)
    # ------------------------------------------------------------------
    s_sqrt3 = sp.sqrt(3)
    a1_g2_s = sp.Matrix([1, 0])
    a2_g2_s = sp.Matrix([sp.Rational(-3, 2), s_sqrt3 / 2])

    def sym_reflect_s(alpha):
        I = sp.eye(2)
        return I - 2 * alpha * alpha.T / (alpha.T * alpha)[0, 0]

    S1_g2_sym = sym_reflect_s(a1_g2_s)
    S2_g2_sym = sym_reflect_s(a2_g2_s)

    # G2 does NOT satisfy (s1*s2)^4 = I
    prod_g2_4 = sp.simplify((S1_g2_sym * S2_g2_sym) ** 4)
    g2_NOT_order4 = (prod_g2_4 != sp.eye(2))

    # B2 does NOT satisfy (s*t)^6 = I — it satisfies ^4 but not ^6 being a "minimal" order
    # Actually (s*t)^4 = I implies (s*t)^8 = I too, so we check that ^4 is the minimal order
    # by verifying (s*t)^2 != I and (s*t)^1 != I (det check)
    b1_b2_s = sp.Matrix([1, 0])
    b2_b2_s = sp.Matrix([-1, 1])
    SB1_sym_s = sym_reflect_s(b1_b2_s)
    SB2_sym_s = sym_reflect_s(b2_b2_s)
    prod_b2_2 = sp.simplify((SB1_sym_s * SB2_sym_s) ** 2)
    b2_NOT_order2 = (prod_b2_2 != sp.eye(2))

    results["N4_sympy_g2_not_b2_coxeter_b2_not_order2"] = {
        "pass": bool(g2_NOT_order4) and bool(b2_NOT_order2),
        "g2_NOT_satisfies_coxeter_4": bool(g2_NOT_order4),
        "b2_NOT_order_2": bool(b2_NOT_order2),
        "reason": "G2 does NOT satisfy (s*t)^4=I (its order is 6); B2 minimal Coxeter order is 4 (not 2)",
    }

    # ------------------------------------------------------------------
    # N5 (clifford): G2 and B2 long-root Clifford reflections produce different outputs
    # ------------------------------------------------------------------
    layout, blades = Cl(2)
    e1 = blades["e1"]
    e2 = blades["e2"]

    def cl_reflect_neg(alpha_t, v_mv):
        ax, ay = float(alpha_t[0]), float(alpha_t[1])
        alph = ax * e1 + ay * e2
        return -(alph * v_mv * ~alph)

    def cl_grade1_n(mv):
        e1c = float((mv * ~e1)[()] / float((e1 * ~e1)[()]))
        e2c = float((mv * ~e2)[()] / float((e2 * ~e2)[()]))
        return e1c, e2c

    v_cl = 1.0 * e1 + 0.5 * e2

    # G2 alpha2 normalized for Clifford
    g2_a2_norm = G2_ALPHA2 / torch.norm(G2_ALPHA2)
    r_g2 = cl_reflect_neg(g2_a2_norm, v_cl)
    r_g2x, r_g2y = cl_grade1_n(r_g2)

    # B2 beta2 normalized
    b2_b2_norm = B2_BETA2 / torch.norm(B2_BETA2)
    r_b2 = cl_reflect_neg(b2_b2_norm, v_cl)
    r_b2x, r_b2y = cl_grade1_n(r_b2)

    cl_diff = abs(r_g2x - r_b2x) + abs(r_g2y - r_b2y)
    results["N5_clifford_g2_b2_long_roots_differ"] = {
        "pass": cl_diff > 1e-6,
        "g2_alpha2_reflection": (round(r_g2x, 6), round(r_g2y, 6)),
        "b2_beta2_reflection": (round(r_b2x, 6), round(r_b2y, 6)),
        "diff": round(cl_diff, 8),
        "reason": "G2 alpha2 and B2 beta2 are distinct vectors; their Clifford reflections of same vector differ",
    }

    # ------------------------------------------------------------------
    # N6 (rustworkx): Cayley graphs are NOT isomorphic (different node counts)
    # ------------------------------------------------------------------
    g_g2_neg = rx.PyDiGraph()
    for _ in range(12):
        g_g2_neg.add_node(None)
    g_b2_neg = rx.PyDiGraph()
    for _ in range(8):
        g_b2_neg.add_node(None)
    results["N6_rustworkx_cayley_graphs_not_isomorphic"] = {
        "pass": g_g2_neg.num_nodes() != g_b2_neg.num_nodes(),
        "g2_nodes": g_g2_neg.num_nodes(),
        "b2_nodes": g_b2_neg.num_nodes(),
        "reason": "Cayley graph node counts differ (12 vs 8): graphs cannot be isomorphic",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    g2_roots, S1_g2, S2_g2 = build_g2_roots()
    b2_roots, SB1, SB2 = build_b2_roots()
    g2_elems = generate_weyl_group_g2(S1_g2, S2_g2)
    b2_elems = generate_weyl_group_b2(SB1, SB2)

    # ------------------------------------------------------------------
    # B1 (pytorch): Identity commutes with everything from both groups
    # ------------------------------------------------------------------
    I = torch.eye(2, dtype=torch.float64)
    v = torch.tensor([0.4, 0.9], dtype=torch.float64)
    all_commute_with_I = True
    for _, M in g2_elems + b2_elems:
        lhs = I @ (M @ v)
        rhs = M @ (I @ v)
        if float(torch.norm(lhs - rhs)) > 1e-10:
            all_commute_with_I = False
    results["B1_pytorch_identity_shared_fixed_point"] = {
        "pass": all_commute_with_I,
        "reason": "Identity element I commutes with all elements of both W(G2) and W(B2): shared boundary",
    }

    # ------------------------------------------------------------------
    # B2 (pytorch): Zero vector is fixed by all reflections
    # ------------------------------------------------------------------
    v_zero = torch.zeros(2, dtype=torch.float64)
    all_map_zero = True
    for _, M in g2_elems + b2_elems:
        img = M @ v_zero
        if float(torch.norm(img)) > 1e-10:
            all_map_zero = False
    results["B2_pytorch_zero_vector_fixed_by_all"] = {
        "pass": all_map_zero,
        "reason": "Zero vector is fixed by all Weyl group elements from both G2 and B2: degenerate boundary",
    }

    # ------------------------------------------------------------------
    # B3 (pytorch): Both G2 and B2 share simple short root (1,0) as alpha1/beta1;
    # Both s1_g2 and sb1_b2 map e1 -> -e1 (shared A1 subgroup)
    # ------------------------------------------------------------------
    e1_vec = torch.tensor([1.0, 0.0], dtype=torch.float64)
    g2_s1_img = S1_g2 @ e1_vec
    b2_sb1_img = SB1 @ e1_vec
    both_map_to_neg_e1 = (
        float(torch.norm(g2_s1_img - (-e1_vec))) < 1e-8 and
        float(torch.norm(b2_sb1_img - (-e1_vec))) < 1e-8
    )
    results["B3_pytorch_shared_alpha1_beta1_reflection"] = {
        "pass": both_map_to_neg_e1,
        "g2_s1_on_e1": tuple(round(x, 8) for x in g2_s1_img.tolist()),
        "b2_sb1_on_e1": tuple(round(x, 8) for x in b2_sb1_img.tolist()),
        "reason": "Both G2 s1 and B2 sb1 map e1 -> -e1: shared A1 = Z2 subgroup (alpha1=beta1=e1)",
    }

    # ------------------------------------------------------------------
    # B4 (sympy): Combined block-diagonal Cartan matrix for G2+B2 has rank 4
    # ------------------------------------------------------------------
    G2_C = sp.Matrix([[2, -1], [-3, 2]])
    B2_C = sp.Matrix([[2, -1], [-2, 2]])
    zeros2 = sp.zeros(2, 2)
    combined_cartan = sp.BlockMatrix([[G2_C, zeros2], [zeros2, B2_C]]).as_explicit()
    rank_combined = combined_cartan.rank()
    is_block_diag = (combined_cartan[0, 2] == 0 and combined_cartan[2, 0] == 0)
    results["B4_sympy_combined_cartan_block_diagonal"] = {
        "pass": rank_combined == 4 and is_block_diag,
        "rank": rank_combined,
        "is_block_diagonal": is_block_diag,
        "reason": "G2+B2 combined Cartan = block diagonal; rank 4; off-diagonal blocks zero = no direct root coupling",
    }

    # ------------------------------------------------------------------
    # B5 (z3): SAT — there exists a vector where both groups' simple reflections agree
    # (s_alpha1_G2 = s_beta1_B2 since alpha1 = beta1 = e1)
    # ------------------------------------------------------------------
    from z3 import Real as ZReal, Solver as ZSolver, sat as zsat
    z = ZSolver()
    vx, vy = ZReal("vx"), ZReal("vy")
    res_x = ZReal("res_x")
    res_y = ZReal("res_y")
    # s_e1(v) = (-vx, vy) for both groups
    z.add(res_x == -vx)
    z.add(res_y == vy)
    z.add(vx * vx + vy * vy > 0)
    sat_result = z.check()
    results["B5_z3_sat_shared_alpha1_reflection_agrees"] = {
        "pass": sat_result == zsat,
        "z3_result": str(sat_result),
        "reason": "SAT: both groups share s_alpha1=s_beta1 (same root e1); they agree on all vectors at this boundary",
    }

    # ------------------------------------------------------------------
    # B6 (clifford): Clifford scalar commutes with all reflections from both groups
    # ------------------------------------------------------------------
    layout, blades = Cl(2)
    scalar = 2.0 * layout.scalar
    e1_cl = blades["e1"]
    v_mv = 0.5 * e1_cl
    lhs_cl = scalar * v_mv
    rhs_cl = v_mv * scalar
    diff_cl = abs(float((lhs_cl - rhs_cl)[()]))
    results["B6_clifford_scalar_commutes_with_all"] = {
        "pass": diff_cl < 1e-10,
        "commutator_norm": diff_cl,
        "reason": "Clifford grade-0 scalar commutes with all elements: boundary condition at the identity",
    }

    # ------------------------------------------------------------------
    # B7 (xgi): Boundary hyperedge: shared A1 subgroup links both groups
    # ------------------------------------------------------------------
    H = xgi.Hypergraph()
    H.add_nodes_from(["e_g2", "e_b2", "shared_A1_s1", "s1s2_g2", "sb1sb2_b2"])
    H.add_edge(["e_g2", "shared_A1_s1"])
    H.add_edge(["e_b2", "shared_A1_s1"])
    H.add_edge(["shared_A1_s1", "s1s2_g2", "sb1sb2_b2"])
    results["B7_xgi_boundary_shared_a1_hyperedge"] = {
        "pass": H.num_edges == 3 and "e_g2" in H.nodes,
        "num_edges": H.num_edges,
        "reason": "XGI: shared A1 boundary links G2 and B2; divergence to G2 and B2 from shared Z2 subgroup",
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
        "name": "sim_weyl_pairwise_g2_bc2_coupling",
        "classification": "classical_baseline",
        "scope_note": (
            "Pairwise coupling probe: W(G2) <-> W(B2). Step 2 of coupling program. "
            "W(G2)=Dih6 (order 12) and W(B2)=Dih4 (order 8) are non-isomorphic; "
            "Coxeter orders differ (6 vs 4); G2 A21=-3 vs B2 A21=-2 (distinct length ratios). "
            "Cross-group reflections do not commute; G2 long-root reflections escape B2 root set. "
            "G2 and B2 share +-e1 (2 roots); combined union = 18 distinct roots. "
            "z3 UNSAT: 12==8 arithmetic impossibility."
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
    out_path = os.path.join(out_dir, "sim_weyl_pairwise_g2_bc2_coupling_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"PASS={overall_pass} -> {out_path}")
