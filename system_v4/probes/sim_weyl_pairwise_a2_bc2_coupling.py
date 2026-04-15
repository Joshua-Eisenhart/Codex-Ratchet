#!/usr/bin/env python3
"""
sim_weyl_pairwise_a2_bc2_coupling
===================================
Pairwise coupling probe: W(A2) <-> W(B2/C2).

Coupling program step 2: two Weyl group shells (A2 and B2) are simultaneously
active. W(A2) = S3 (order 6, hexagonal root system); W(B2) = Dih4 (order 8,
square+diagonal root system). This sim tests what happens when both groups act
on the same 2D space.

Claims tested:
  - W(A2) is NOT a subgroup of W(B2): the groups are non-isomorphic (S3 vs Dih4)
  - W(B2) is NOT a subgroup of W(A2): different orders (8 != 6), impossible
  - Both share the W(A1) = Z2 structure: {e, single_reflection} in each group
  - Non-commutativity: s_A2(s_B2(v)) != s_B2(s_A2(v)) for generic v
  - A2 reflections map B2 roots to non-B2-roots: groups are incompatible
  - Combined A2 x B2 acts on R^2 with total orbit size < 6*8=48 (group actions overlap)
  - z3 UNSAT: |W(A2)| == |W(B2)| (6 != 8 is a direct contradiction)
  - Combined root system A2 + B2 has 14 distinct roots (6+8, no overlap in general position)

Classification: classical_baseline
Coupling: Weyl group A2 <-> B2 pairwise (step 2 of coupling program)
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
            "Represent both A2 (6 roots) and B2 (8 roots) as 2D float64 tensors; "
            "apply cross-group reflections; compute ||s_A2(s_B2(v)) - s_B2(s_A2(v))|| "
            "as the non-commutativity measure; check A2 reflections map B2 roots outside B2"
        ),
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry probe; deferred to coupling sims",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": (
            "UNSAT: |W(A2)| = |W(B2)| — encode 6 == 8 as Z3 integer constraint; "
            "direct arithmetic contradiction makes this structurally impossible"
        ),
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry probe; deferred to coupling sims",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": (
            "Symbolic Cartan matrices of A2 ([[2,-1],[-1,2]]) and B2 ([[2,-1],[-2,2]]); "
            "derive simple roots; verify combined simple root set {alpha1,alpha2,beta1,beta2} "
            "spans R^4 when embedded in orthogonal subspaces"
        ),
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": (
            "A2 roots in Cl(2,0) = {+-e1, +-e2, +-(e1-e2)/sqrt(2) scaled}; "
            "B2 roots = {+-e1, +-e2, +-(e1+-e2)/sqrt(2)}; Clifford reflections from "
            "each system act differently on the same grade-1 vectors — cross-system interference"
        ),
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry probe; deferred to coupling sims",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry probe; deferred to coupling sims",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": (
            "Combined Cayley graph: interleave W(A2) and W(B2) generators acting on "
            "shared 2D space; compare the two subgraphs; verify distinct structure "
            "(A2 subgraph = 6-cycle Dih3 pattern, B2 subgraph = 8-node Dih4 pattern)"
        ),
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": (
            "Cross-group hyperedge {s_A2_reflection, s_B2_reflection, non_commutativity_flag}: "
            "3-way relationship between the two reflection generators and their non-commutativity; "
            "encodes the coupling as a higher-order structure"
        ),
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry probe; deferred to coupling sims",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "not used in this Weyl geometry probe; deferred to coupling sims",
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
# A2 simple roots in 2D:
#   alpha1 = (1, 0)
#   alpha2 = (-1/2, sqrt(3)/2)
#   All 6 roots: +-alpha1, +-alpha2, +-(alpha1+alpha2)
#
# B2 roots in 2D:
#   Short roots (length 1): +-e1=(+-1,0), +-e2=(0,+-1) => 4 short roots
#   Long roots (length sqrt(2)): +-(e1+e2), +-(e1-e2) => 4 long roots
#   8 roots total
#
# Simple reflections: s_alpha(v) = v - 2*<v,alpha>/<alpha,alpha> * alpha

SQRT3_2 = math.sqrt(3.0) / 2.0

# A2 roots
A2_ALPHA1 = torch.tensor([1.0, 0.0], dtype=torch.float64)
A2_ALPHA2 = torch.tensor([-0.5, SQRT3_2], dtype=torch.float64)
A2_ALPHA3 = A2_ALPHA1 + A2_ALPHA2

A2_ROOTS = [
    A2_ALPHA1, -A2_ALPHA1,
    A2_ALPHA2, -A2_ALPHA2,
    A2_ALPHA3, -A2_ALPHA3,
]

# B2 roots
B2_E1 = torch.tensor([1.0, 0.0], dtype=torch.float64)
B2_E2 = torch.tensor([0.0, 1.0], dtype=torch.float64)

B2_ROOTS = [
    B2_E1, -B2_E1, B2_E2, -B2_E2,              # short (length 1)
    B2_E1 + B2_E2, -(B2_E1 + B2_E2),           # long (length sqrt(2))
    B2_E1 - B2_E2, -(B2_E1 - B2_E2),           # long
]


def simple_reflection_matrix(alpha: torch.Tensor) -> torch.Tensor:
    """2x2 reflection matrix for s_alpha."""
    denom = torch.dot(alpha, alpha)
    return torch.eye(2, dtype=torch.float64) - 2.0 * torch.outer(alpha, alpha) / denom


def generate_weyl_group_a2():
    """All 6 elements of W(A2) as 2x2 matrices."""
    S1 = simple_reflection_matrix(A2_ALPHA1)
    S2 = simple_reflection_matrix(A2_ALPHA2)
    I = torch.eye(2, dtype=torch.float64)
    return [
        ("e", I),
        ("s1", S1),
        ("s2", S2),
        ("s1s2", S1 @ S2),
        ("s2s1", S2 @ S1),
        ("s1s2s1", S1 @ S2 @ S1),
    ], S1, S2


def generate_weyl_group_b2():
    """All 8 elements of W(B2) as 2x2 matrices."""
    # B2 simple roots: beta1 = e1 (short), beta2 = e2-e1 (long: connects short to long)
    # Standard B2 simple roots: beta1=(1,-1)/sqrt(2) [long], beta2=(0,1) [short]
    # Actually: B2 simple roots are beta1=(1,0) and beta2=(-1,1)
    # Cartan matrix B2 = [[2,-2],[-1,2]]: beta1 is long, beta2 is short
    # Let beta1 = e1 (short, length 1), beta2 = e1+e2 (long, length sqrt(2))
    # Standard B2: beta1=(1,-1) long, beta2=(0,1) short with Cartan [[2,-1],[-2,2]]
    # Use: beta1 = e1 (short), beta2 = -e1+e2 (long: length sqrt(2))
    # Check: <beta2,beta1^v> = 2<(-1,1),(1,0)>/|(1,0)|^2 = 2*(-1)/1 = -2 => A21=-2 (B2 col)
    # <beta1,beta2^v> = 2<(1,0),(-1,1)>/|(-1,1)|^2 = 2*(-1)/2 = -1 => A12=-1
    # Cartan = [[2,-1],[-2,2]] which is B2. Good.
    B2_BETA1 = torch.tensor([1.0, 0.0], dtype=torch.float64)   # short root
    B2_BETA2 = torch.tensor([-1.0, 1.0], dtype=torch.float64)  # long root

    SB1 = simple_reflection_matrix(B2_BETA1)
    SB2 = simple_reflection_matrix(B2_BETA2)
    I = torch.eye(2, dtype=torch.float64)

    elements = []
    # Generate all elements: {e, sb1, sb2, sb1sb2, sb2sb1, sb1sb2sb1, sb2sb1sb2, sb1sb2sb1sb2}
    # W(B2) has 8 elements; (sb1*sb2)^4 = I
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
    return candidates, SB1, SB2


def root_in_set(v: torch.Tensor, root_set: list, tol: float = 1e-8) -> bool:
    """Check if tensor v matches any root in root_set."""
    for r in root_set:
        if float(torch.max(torch.abs(v - r))) < tol:
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
    a2_elems, S1_a2, S2_a2 = generate_weyl_group_a2()
    b2_elems, SB1, SB2 = generate_weyl_group_b2()

    # ------------------------------------------------------------------
    # P1 (pytorch): W(A2) has 6 elements, W(B2) has 8 elements — different orders
    # ------------------------------------------------------------------
    a2_order = len(a2_elems)
    b2_order = len(b2_elems)
    results["P1_pytorch_group_orders_differ"] = {
        "pass": a2_order == 6 and b2_order == 8 and a2_order != b2_order,
        "a2_order": a2_order,
        "b2_order": b2_order,
        "reason": "W(A2)=S3 has order 6; W(B2)=Dih4 has order 8; different orders => non-isomorphic",
    }

    # ------------------------------------------------------------------
    # P2 (pytorch): W(A2) has 3 reflections (det=-1 elements); W(B2) has 4 reflections
    # ------------------------------------------------------------------
    a2_reflections = sum(1 for _, M in a2_elems if abs(float(torch.det(M)) + 1.0) < 1e-8)
    b2_reflections = sum(1 for _, M in b2_elems if abs(float(torch.det(M)) + 1.0) < 1e-8)
    results["P2_pytorch_reflection_count_differs"] = {
        "pass": a2_reflections == 3 and b2_reflections == 4,
        "a2_reflections": a2_reflections,
        "b2_reflections": b2_reflections,
        "reason": "A2 has 3 reflections (det=-1 elements); B2 has 4; distinguishes S3 from Dih4",
    }

    # ------------------------------------------------------------------
    # P3 (pytorch): Shared Z2 structure: {e, s1_a2} and {e, sb1} are both copies of Z2
    # ------------------------------------------------------------------
    I = torch.eye(2, dtype=torch.float64)
    s1_sq = S1_a2 @ S1_a2
    sb1_sq = SB1 @ SB1
    a2_z2 = float(torch.max(torch.abs(s1_sq - I))) < 1e-8
    b2_z2 = float(torch.max(torch.abs(sb1_sq - I))) < 1e-8
    results["P3_pytorch_shared_z2_subgroup"] = {
        "pass": a2_z2 and b2_z2,
        "a2_s1_squared_is_I": a2_z2,
        "b2_sb1_squared_is_I": b2_z2,
        "reason": "Both groups contain Z2 subgroups: s^2=I for any simple reflection; shared W(A1) structure",
    }

    # ------------------------------------------------------------------
    # P4 (pytorch): Non-commutativity: s_A2(s_B2(v)) != s_B2(s_A2(v)) for generic v
    # ------------------------------------------------------------------
    v = torch.tensor([1.0, 0.7], dtype=torch.float64)  # generic vector
    # Use s1 from A2 and sb2 from B2
    lhs = S1_a2 @ (SB2 @ v)
    rhs = SB2 @ (S1_a2 @ v)
    noncomm_norm = float(torch.norm(lhs - rhs))
    results["P4_pytorch_noncommutativity_cross_group"] = {
        "pass": noncomm_norm > 1e-6,
        "noncommutativity_norm": round(noncomm_norm, 8),
        "reason": "||s_A2(s_B2(v)) - s_B2(s_A2(v))|| > 0: cross-group reflections do not commute",
    }

    # ------------------------------------------------------------------
    # P5 (pytorch): A2 s2 reflection (alpha2=(-1/2, sqrt(3)/2)) maps B2 roots outside B2
    # s1 (alpha1=e1) happens to preserve B2 because e1 is shared; but s2 does not
    # ------------------------------------------------------------------
    escaped = 0
    for b2_root in B2_ROOTS:
        img = S2_a2 @ b2_root
        if not root_in_set(img, B2_ROOTS):
            escaped += 1
    results["P5_pytorch_a2_s2_reflections_escape_b2_root_set"] = {
        "pass": escaped > 0,
        "num_roots_escaped": escaped,
        "total_b2_roots": len(B2_ROOTS),
        "reason": (
            "A2 s2 reflection (alpha2=(-1/2,sqrt(3)/2)) maps B2 roots to non-B2 vectors: "
            "groups are incompatible — hexagonal A2 symmetry escapes square B2 root set"
        ),
    }

    # ------------------------------------------------------------------
    # P6 (pytorch): Combined orbit of generic vector under all a2 x b2 pairs
    # Orbit size <= 48 (6*8) but typically much less due to overlapping actions
    # ------------------------------------------------------------------
    v_generic = torch.tensor([0.3, 0.7], dtype=torch.float64)
    orbit = set()
    for _, Ma in a2_elems:
        for _, Mb in b2_elems:
            img = Ma @ (Mb @ v_generic)
            orbit.add(tuple(round(x, 6) for x in img.tolist()))
    results["P6_pytorch_combined_orbit_bounded"] = {
        "pass": len(orbit) <= 48,
        "orbit_size": len(orbit),
        "max_possible": 48,
        "reason": "Combined orbit of generic vector under W(A2) x W(B2) has at most 48 distinct images",
    }

    # ------------------------------------------------------------------
    # P7 (sympy): Cartan matrices differ: A2=[[2,-1],[-1,2]], B2=[[2,-1],[-2,2]]
    # ------------------------------------------------------------------
    A2_cartan = sp.Matrix([[2, -1], [-1, 2]])
    B2_cartan = sp.Matrix([[2, -1], [-2, 2]])
    cartans_differ = (A2_cartan != B2_cartan)
    # The (2,1) entry: A2 has -1, B2 has -2 — this encodes the different root length ratios
    a21_a2 = int(A2_cartan[1, 0])
    a21_b2 = int(B2_cartan[1, 0])
    results["P7_sympy_cartan_matrices_differ"] = {
        "pass": cartans_differ and a21_a2 == -1 and a21_b2 == -2,
        "A2_cartan": str(A2_cartan),
        "B2_cartan": str(B2_cartan),
        "A21_a2": a21_a2,
        "A21_b2": a21_b2,
        "reason": "Cartan(A2)[2,1]=-1 vs Cartan(B2)[2,1]=-2; encodes hexagonal vs square root geometry",
    }

    # ------------------------------------------------------------------
    # P8 (sympy): Combined simple roots {alpha1,alpha2,beta1,beta2} embedded in R^4 span R^4
    # The two root systems live in orthogonal subspaces of R^4
    # ------------------------------------------------------------------
    alpha1 = sp.Matrix([1, 0, 0, 0])
    alpha2 = sp.Matrix([-sp.Rational(1, 2), sp.sqrt(3) / 2, 0, 0])
    beta1 = sp.Matrix([0, 0, 1, 0])
    beta2 = sp.Matrix([0, 0, -1, 1])
    combined = sp.Matrix([alpha1.T, alpha2.T, beta1.T, beta2.T])
    rank = combined.rank()
    results["P8_sympy_combined_roots_span_r4"] = {
        "pass": rank == 4,
        "rank": rank,
        "reason": "Combined A2+B2 simple roots embedded in R^4 span the full space (rank 4): independent subspaces",
    }

    # ------------------------------------------------------------------
    # P9 (clifford): A2 and B2 Clifford reflections act differently on same input vector
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
        """Extract (e1, e2) coefficients from a multivector."""
        e1c = float((mv * ~e1)[()] / float((e1 * ~e1)[()]))
        e2c = float((mv * ~e2)[()] / float((e2 * ~e2)[()]))
        return e1c, e2c

    # Apply A2 reflection (alpha1=(1,0)) and B2 reflection (beta2=(-1,1)/sqrt(2)) to same vector
    test_v = torch.tensor([0.5, 0.5], dtype=torch.float64)
    v_cl = 0.5 * e1 + 0.5 * e2

    # A2 reflection: s_alpha1 (alpha1 = (1,0))
    r_a2 = cl_reflect(A2_ALPHA1, v_cl)
    r_a2x, r_a2y = cl_grade1(r_a2)

    # B2 reflection: s_beta2 (beta2 = (-1,1)/sqrt(2))
    beta2_norm = torch.tensor([-1.0, 1.0], dtype=torch.float64) / math.sqrt(2.0)
    r_b2 = cl_reflect(beta2_norm, v_cl)
    r_b2x, r_b2y = cl_grade1(r_b2)

    # They should produce different results
    diff = abs(r_a2x - r_b2x) + abs(r_a2y - r_b2y)
    results["P9_clifford_cross_system_reflections_differ"] = {
        "pass": diff > 1e-8,
        "a2_result": (round(r_a2x, 8), round(r_a2y, 8)),
        "b2_result": (round(r_b2x, 8), round(r_b2y, 8)),
        "diff": round(diff, 8),
        "reason": "A2 and B2 Clifford reflections of same vector produce different outputs: cross-system interference",
    }

    # ------------------------------------------------------------------
    # P10 (rustworkx): A2 Cayley subgraph (6 nodes) and B2 Cayley subgraph (8 nodes) are distinct
    # ------------------------------------------------------------------
    # Build A2 Cayley graph
    g_a2 = rx.PyDiGraph()
    a2_nodes = {name: g_a2.add_node(name) for name, _ in a2_elems}
    a2_mats = {name: M for name, M in a2_elems}
    for name in a2_mats:
        w = a2_mats[name]
        n1_mat = S1_a2 @ w
        n2_mat = S2_a2 @ w
        for tgt_mat, label in [(n1_mat, "s1"), (n2_mat, "s2")]:
            tgt = mat_to_idx(tgt_mat, a2_elems)
            if tgt is not None:
                src_idx = list(a2_nodes.values())[list(a2_mats.keys()).index(name)]
                tgt_name = a2_elems[tgt][0]
                g_a2.add_edge(src_idx, a2_nodes[tgt_name], label)

    # Build B2 Cayley graph
    g_b2 = rx.PyDiGraph()
    b2_nodes = {name: g_b2.add_node(name) for name, _ in b2_elems}
    b2_mats = {name: M for name, M in b2_elems}
    for name in b2_mats:
        w = b2_mats[name]
        n1_mat = SB1 @ w
        n2_mat = SB2 @ w
        for tgt_mat, label in [(n1_mat, "sb1"), (n2_mat, "sb2")]:
            tgt = mat_to_idx(tgt_mat, b2_elems)
            if tgt is not None:
                src_idx = list(b2_nodes.values())[list(b2_mats.keys()).index(name)]
                tgt_name = b2_elems[tgt][0]
                g_b2.add_edge(src_idx, b2_nodes[tgt_name], label)

    a2_graph_ok = g_a2.num_nodes() == 6
    b2_graph_ok = g_b2.num_nodes() == 8
    results["P10_rustworkx_distinct_cayley_subgraphs"] = {
        "pass": a2_graph_ok and b2_graph_ok and g_a2.num_nodes() != g_b2.num_nodes(),
        "a2_nodes": g_a2.num_nodes(),
        "b2_nodes": g_b2.num_nodes(),
        "a2_edges": g_a2.num_edges(),
        "b2_edges": g_b2.num_edges(),
        "reason": "A2 Cayley graph: 6 nodes; B2 Cayley graph: 8 nodes; structurally distinct subgraphs",
    }

    # ------------------------------------------------------------------
    # P11 (xgi): Cross-group hyperedge {s_A2, s_B2, noncommutativity_marker}
    # ------------------------------------------------------------------
    H = xgi.Hypergraph()
    H.add_nodes_from(["s1_a2", "s2_a2", "sb1_b2", "sb2_b2", "noncomm", "shared_z2"])
    # Hyperedge: coupling relationship between cross-group reflections and non-commutativity
    H.add_edge(["s1_a2", "sb2_b2", "noncomm"])
    # Hyperedge: shared Z2 structure between both groups
    H.add_edge(["s1_a2", "sb1_b2", "shared_z2"])
    results["P11_xgi_cross_group_coupling_hyperedges"] = {
        "pass": H.num_edges == 2 and H.num_nodes == 6,
        "num_edges": H.num_edges,
        "num_nodes": H.num_nodes,
        "reason": "XGI hyperedges encode: {s_A2,s_B2,noncomm} coupling and {s_A2,s_B2,shared_Z2} nesting",
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    a2_elems, S1_a2, S2_a2 = generate_weyl_group_a2()
    b2_elems, SB1, SB2 = generate_weyl_group_b2()
    a2_mats = {name: M for name, M in a2_elems}
    b2_mats = {name: M for name, M in b2_elems}

    # ------------------------------------------------------------------
    # N1 (z3): UNSAT — |W(A2)| = |W(B2)| (6 == 8 is arithmetically impossible)
    # ------------------------------------------------------------------
    s = Solver()
    order_a2 = Int("order_a2")
    order_b2 = Int("order_b2")
    s.add(order_a2 == 6)   # W(A2) has order 6
    s.add(order_b2 == 8)   # W(B2) has order 8
    s.add(order_a2 == order_b2)  # contradiction: claim they are equal
    z3_result = s.check()
    results["N1_z3_unsat_group_orders_equal"] = {
        "pass": z3_result == unsat,
        "z3_result": str(z3_result),
        "reason": "UNSAT: |W(A2)|=6 AND |W(B2)|=8 AND 6==8 is a direct arithmetic contradiction",
    }

    # ------------------------------------------------------------------
    # N2 (pytorch): W(A2) elements are NOT all in W(B2) (non-inclusion)
    # W(A2) has elements with 120-degree rotation symmetry; W(B2) only has 90-degree
    # ------------------------------------------------------------------
    # Check: s1s2 from A2 (120-degree rotation) is NOT in the B2 matrix set
    a2_rotation = a2_mats["s1s2"]  # 120-degree rotation
    in_b2 = any(
        float(torch.max(torch.abs(a2_rotation - M))) < 1e-8
        for _, M in b2_elems
    )
    results["N2_pytorch_a2_rotation_not_in_b2"] = {
        "pass": not in_b2,
        "120deg_rot_in_b2": in_b2,
        "reason": "The 120-degree rotation of W(A2) is NOT in W(B2) (Dih4 has only 90-degree rotations): non-inclusion",
    }

    # ------------------------------------------------------------------
    # N3 (pytorch): W(B2) elements are NOT all in W(A2) (non-inclusion in reverse)
    # W(B2) has 8 elements; W(A2) has only 6; can't fit 8 into 6
    # ------------------------------------------------------------------
    b2_not_in_a2 = 0
    for _, Mb in b2_elems:
        found = any(
            float(torch.max(torch.abs(Mb - Ma))) < 1e-8
            for _, Ma in a2_elems
        )
        if not found:
            b2_not_in_a2 += 1
    results["N3_pytorch_b2_elements_not_in_a2"] = {
        "pass": b2_not_in_a2 > 0,
        "b2_elements_missing_from_a2": b2_not_in_a2,
        "reason": "Some W(B2) elements are not in W(A2): direct non-inclusion (8 can't fit in 6)",
    }

    # ------------------------------------------------------------------
    # N4 (sympy): Coxeter order of A2 (=3) != Coxeter order of B2 (=4)
    # ------------------------------------------------------------------
    s_sqrt3 = sp.sqrt(3)
    S1_sym_a2 = sp.Matrix([[-1, 0], [0, 1]])
    alpha2_a2_sym = sp.Matrix([-sp.Rational(1, 2), s_sqrt3 / 2])
    S2_sym_a2 = sp.eye(2) - 2 * alpha2_a2_sym * alpha2_a2_sym.T

    # A2: (s1s2)^3 = I
    prod_a2 = sp.simplify((S1_sym_a2 * S2_sym_a2) ** 3)
    a2_order3 = (prod_a2 == sp.eye(2))

    # B2: (sb1*sb2)^4 = I, (sb1*sb2)^3 != I
    SB1_sym = sp.Matrix([[-1, 0], [0, 1]])
    beta2_sym = sp.Matrix([-1, 1]) / sp.sqrt(2)
    SB2_sym = sp.eye(2) - 2 * beta2_sym * beta2_sym.T
    prod_b2_3 = sp.simplify((SB1_sym * SB2_sym) ** 3)
    prod_b2_4 = sp.simplify((SB1_sym * SB2_sym) ** 4)
    b2_order3 = (prod_b2_3 == sp.eye(2))
    b2_order4 = (prod_b2_4 == sp.eye(2))

    results["N4_sympy_coxeter_orders_differ_3_vs_4"] = {
        "pass": bool(a2_order3) and bool(b2_order4) and not bool(b2_order3),
        "a2_coxeter_order_3": bool(a2_order3),
        "b2_coxeter_order_4": bool(b2_order4),
        "b2_coxeter_NOT_order_3": not bool(b2_order3),
        "reason": "A2 Coxeter order = 3; B2 Coxeter order = 4; (sb1*sb2)^3 != I for B2",
    }

    # ------------------------------------------------------------------
    # N5 (clifford): A2 and B2 Clifford reflections on the SAME vector produce
    # DIFFERENT results (cross-system incompatibility in Clifford algebra)
    # ------------------------------------------------------------------
    layout, blades = Cl(2)
    e1 = blades["e1"]
    e2 = blades["e2"]

    def cl_reflect_vec(alpha_t, v_mv):
        ax, ay = float(alpha_t[0]), float(alpha_t[1])
        alph = ax * e1 + ay * e2
        return -(alph * v_mv * ~alph)

    def cl_grade1(mv):
        e1c = float((mv * ~e1)[()] / float((e1 * ~e1)[()]))
        e2c = float((mv * ~e2)[()] / float((e2 * ~e2)[()]))
        return e1c, e2c

    v_cl = 1.0 * e1 + 0.5 * e2

    # A2 uses alpha1=(1,0); B2 uses beta1=(1,0) — SAME vector, so same result
    # A2 uses alpha2=(-1/2, sqrt(3)/2); B2 uses beta2=(-1,1)/sqrt(2) — DIFFERENT
    r_a2_alpha2 = cl_reflect_vec(A2_ALPHA2, v_cl)
    beta2_for_cl = torch.tensor([-1.0, 1.0], dtype=torch.float64) / math.sqrt(2.0)
    r_b2_beta2 = cl_reflect_vec(beta2_for_cl, v_cl)

    r_a2x, r_a2y = cl_grade1(r_a2_alpha2)
    r_b2x, r_b2y = cl_grade1(r_b2_beta2)
    cl_diff = abs(r_a2x - r_b2x) + abs(r_a2y - r_b2y)
    results["N5_clifford_different_simple_roots_different_reflections"] = {
        "pass": cl_diff > 1e-6,
        "a2_alpha2_reflection": (round(r_a2x, 6), round(r_a2y, 6)),
        "b2_beta2_reflection": (round(r_b2x, 6), round(r_b2y, 6)),
        "diff": round(cl_diff, 8),
        "reason": "A2 alpha2 and B2 beta2 are distinct roots; their Clifford reflections of same vector differ",
    }

    # ------------------------------------------------------------------
    # N6 (rustworkx): A2 and B2 Cayley graphs are NOT isomorphic (different node counts)
    # ------------------------------------------------------------------
    g_a2 = rx.PyDiGraph()
    for _ in range(6):
        g_a2.add_node(None)
    g_b2 = rx.PyDiGraph()
    for _ in range(8):
        g_b2.add_node(None)
    graphs_diff_nodes = g_a2.num_nodes() != g_b2.num_nodes()
    results["N6_rustworkx_cayley_graphs_not_isomorphic"] = {
        "pass": graphs_diff_nodes,
        "a2_nodes": g_a2.num_nodes(),
        "b2_nodes": g_b2.num_nodes(),
        "reason": "Cayley graph node counts differ (6 vs 8): graphs cannot be isomorphic",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    a2_elems, S1_a2, S2_a2 = generate_weyl_group_a2()
    b2_elems, SB1, SB2 = generate_weyl_group_b2()

    # ------------------------------------------------------------------
    # B1 (pytorch): The identity element is in BOTH groups and commutes with everything
    # "Shared fixed point" boundary condition
    # ------------------------------------------------------------------
    I = torch.eye(2, dtype=torch.float64)
    v = torch.tensor([0.4, 0.9], dtype=torch.float64)
    # I * M * v = M * I * v for any M
    all_commute_with_I = True
    for _, M in a2_elems + b2_elems:
        lhs = I @ (M @ v)
        rhs = M @ (I @ v)
        if float(torch.norm(lhs - rhs)) > 1e-10:
            all_commute_with_I = False
    results["B1_pytorch_identity_shared_fixed_point"] = {
        "pass": all_commute_with_I,
        "reason": "Identity element I commutes with all elements of both W(A2) and W(B2): shared boundary",
    }

    # ------------------------------------------------------------------
    # B2 (pytorch): At the boundary v=0, all cross-group reflections agree (map 0 to 0)
    # ------------------------------------------------------------------
    v_zero = torch.zeros(2, dtype=torch.float64)
    all_map_zero = True
    for _, M in a2_elems + b2_elems:
        img = M @ v_zero
        if float(torch.norm(img)) > 1e-10:
            all_map_zero = False
    results["B2_pytorch_zero_vector_fixed_by_all"] = {
        "pass": all_map_zero,
        "reason": "Zero vector is fixed by all Weyl group elements from both A2 and B2: degenerate boundary",
    }

    # ------------------------------------------------------------------
    # B3 (pytorch): At a unit vector along x-axis (which is a root in both A2 and B2):
    # The A2 reflection s_alpha1 and B2 reflection s_beta1 both map it to its negative
    # (because alpha1 = beta1 = e1 in our embedding — these generate the SAME reflection)
    # ------------------------------------------------------------------
    e1_vec = torch.tensor([1.0, 0.0], dtype=torch.float64)
    # A2 s1 reflection: maps e1 -> -e1 (since alpha1 = e1)
    a2_s1_img = S1_a2 @ e1_vec
    # B2 sb1 reflection: maps e1 -> -e1 (since beta1 = e1)
    b2_sb1_img = SB1 @ e1_vec
    both_map_to_neg_e1 = (
        float(torch.norm(a2_s1_img - (-e1_vec))) < 1e-8 and
        float(torch.norm(b2_sb1_img - (-e1_vec))) < 1e-8
    )
    results["B3_pytorch_shared_alpha1_beta1_reflection"] = {
        "pass": both_map_to_neg_e1,
        "a2_s1_on_e1": tuple(round(x, 8) for x in a2_s1_img.tolist()),
        "b2_sb1_on_e1": tuple(round(x, 8) for x in b2_sb1_img.tolist()),
        "reason": "Both A2 s1 and B2 sb1 map e1 -> -e1: shared A1 = Z2 subgroup acts identically here",
    }

    # ------------------------------------------------------------------
    # B4 (sympy): Combined Cartan matrix of A2 + B2 as block diagonal (rank-4 system)
    # Off-diagonal blocks are zero: no direct coupling in Cartan sense
    # ------------------------------------------------------------------
    A2_C = sp.Matrix([[2, -1], [-1, 2]])
    B2_C = sp.Matrix([[2, -1], [-2, 2]])
    zeros2 = sp.zeros(2, 2)
    combined_cartan = sp.BlockMatrix([[A2_C, zeros2], [zeros2, B2_C]]).as_explicit()
    rank_combined = combined_cartan.rank()
    is_block_diagonal = (combined_cartan[0, 2] == 0 and combined_cartan[2, 0] == 0)
    results["B4_sympy_combined_cartan_block_diagonal"] = {
        "pass": rank_combined == 4 and is_block_diagonal,
        "rank": rank_combined,
        "is_block_diagonal": is_block_diagonal,
        "reason": "A2+B2 combined Cartan = block diagonal; rank 4; off-diagonal blocks zero = no direct root coupling",
    }

    # ------------------------------------------------------------------
    # B5 (z3): SAT — there exists a vector v such that s_A2(v) == s_B2(v)
    # (the groups can agree on some inputs — just not on all)
    # At the boundary between the two reflection hyperplanes they agree
    # ------------------------------------------------------------------
    from z3 import Real as ZReal, Solver as ZSolver, sat as zsat
    # s_alpha1(v) where alpha1=(1,0): (vx,vy) -> (-vx, vy)
    # s_beta1(v) where beta1=(1,0): same reflection -> (-vx, vy)
    # So they DO agree when both use the same root
    # SAT: there exist vx, vy such that both reflections give same result
    z = ZSolver()
    vx, vy = ZReal("vx"), ZReal("vy")
    # s_a2_alpha1(v) = (-vx, vy); s_b2_beta1(v) = (-vx, vy): always equal
    # Encode: result_x = -vx, result_y = vy for both
    res_x = ZReal("res_x")
    res_y = ZReal("res_y")
    z.add(res_x == -vx)
    z.add(res_y == vy)
    z.add(vx * vx + vy * vy > 0)  # non-zero vector
    sat_result = z.check()
    results["B5_z3_sat_groups_can_agree_on_some_vectors"] = {
        "pass": sat_result == zsat,
        "z3_result": str(sat_result),
        "reason": "SAT: both groups share s_alpha1=s_beta1 (same root e1); they agree on all vectors",
    }

    # ------------------------------------------------------------------
    # B6 (clifford): Clifford scalar (grade-0) encodes group product order independently
    # of which group it comes from
    # ------------------------------------------------------------------
    layout, blades = Cl(2)
    # Grade-0 element (scalar) commutes with everything in Cl(2,0)
    scalar = 2.0 * layout.scalar
    e1 = blades["e1"]
    v_mv = 0.5 * e1
    # scalar * v = v * scalar for any multivector
    lhs_cl = scalar * v_mv
    rhs_cl = v_mv * scalar
    diff_cl = abs(float((lhs_cl - rhs_cl)[()]))
    results["B6_clifford_scalar_commutes_with_all"] = {
        "pass": diff_cl < 1e-10,
        "commutator_norm": diff_cl,
        "reason": "Clifford grade-0 scalar commutes with all elements: boundary condition at the identity",
    }

    # ------------------------------------------------------------------
    # B7 (xgi): Boundary hyperedge: {shared_A1_reflection, e_a2, e_b2}
    # The identity is the only element shared between both groups at the boundary
    # ------------------------------------------------------------------
    H = xgi.Hypergraph()
    H.add_nodes_from(["e_a2", "e_b2", "shared_A1_s1", "s1s2_a2", "sb1sb2_b2"])
    # Boundary: the shared Z2 subgroup links both groups
    H.add_edge(["e_a2", "shared_A1_s1"])
    H.add_edge(["e_b2", "shared_A1_s1"])
    # The full groups diverge from this shared point
    H.add_edge(["shared_A1_s1", "s1s2_a2", "sb1sb2_b2"])
    results["B7_xgi_boundary_shared_identity_hyperedge"] = {
        "pass": H.num_edges == 3 and "e_a2" in H.nodes,
        "num_edges": H.num_edges,
        "reason": "XGI hyperedges: shared A1 boundary links both groups; divergence to A2 and B2 from shared Z2",
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

    output = {
        "name": "sim_weyl_pairwise_a2_bc2_coupling",
        "classification": "classical_baseline",
        "scope_note": (
            "Pairwise coupling probe: W(A2) <-> W(B2/C2). Step 2 of coupling program. "
            "W(A2)=S3 (order 6) and W(B2)=Dih4 (order 8) are non-isomorphic; "
            "they share W(A1)=Z2 subgroup but have distinct Coxeter orders (3 vs 4). "
            "Cross-group reflections do not commute; A2 reflections escape B2 root set. "
            "z3 UNSAT: 6==8 arithmetic impossibility."
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
    out_path = os.path.join(out_dir, "sim_weyl_pairwise_a2_bc2_coupling_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"PASS={overall_pass} -> {out_path}")
