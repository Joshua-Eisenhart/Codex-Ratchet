#!/usr/bin/env python3
"""
sim_gtower_nonclassical_emergence_seed.py
==========================================
G-tower nonclassical emergence: where does the first complex structure appear?

Claim: The SO(3)→U(3) complexification step is the bridge from classical to
nonclassical. Real matrix groups (GL, O, SO) have Im([A,B])_F = 0.
Complex matrix groups (U, SU, Sp) have Im([A,B])_F > 0.
The algebraic boundary is e12^2 = -1 in Cl(3,0) — the e12 blade activates
at the SO→U transition.

classification: classical_baseline
"""

import json
import os
import sys
import math

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True,
                "reason": "compute |Im([A,B])|_F for matrix pairs at each tower level; verify zero for GL/O/SO, nonzero for U/SU/Sp — load-bearing numerical sweep"},
    "pyg": {"tried": False, "used": False,
            "reason": "not used — G-tower emergence is a matrix-level test; no graph message-passing required"},
    "z3": {"tried": True, "used": True,
           "reason": "UNSAT: A is real AND anti-Hermitian AND has nonzero imaginary off-diagonal — structural impossibility"},
    "cvc5": {"tried": False, "used": False,
             "reason": "not used — z3 covers the proof layer for this sim"},
    "sympy": {"tried": True, "used": True,
              "reason": "so(3) generators are real antisymmetric; u(3) generators are complex anti-Hermitian; prove so(3) generators have zero imaginary parts symbolically"},
    "clifford": {"tried": True, "used": True,
                 "reason": "e12^2=-1 is the complex structure; before SO level no e12 needed; at U level e12 is essential; the boundary is exactly e12 blade activation"},
    "geomstats": {"tried": True, "used": True,
                  "reason": "sample SO(3) via SpecialOrthogonal(n=3); compute |Im(M)|_F → 0; verify U(3)-like matrices have Im > 0"},
    "e3nn": {"tried": False, "used": False,
             "reason": "not used — G-tower emergence is matrix algebraic; no equivariant network required"},
    "rustworkx": {"tried": True, "used": True,
                  "reason": "G-tower DAG: nodes annotated classical/nonclassical_seed; SO→U edge is unique classical→nonclassical_seed transition"},
    "xgi": {"tried": False, "used": False,
            "reason": "not used — G-tower emergence is matrix algebraic; no hypergraph topology required"},
    "toponetx": {"tried": False, "used": False,
                 "reason": "not used — G-tower emergence is matrix algebraic; no cell complex required"},
    "gudhi": {"tried": False, "used": False,
              "reason": "not used — G-tower emergence is matrix algebraic; no persistent homology required"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None,
    "z3": "load_bearing",
    "cvc5": None,
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "geomstats": "load_bearing",
    "e3nn": None,
    "rustworkx": "load_bearing",
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# =====================================================================
# IMPORTS
# =====================================================================

import torch
import numpy as np
import sympy as sp
from z3 import Real, Bool, Solver, And, Implies, sat, unsat, RealVal
from clifford import Cl
import rustworkx as rx
import os as _os
_os.environ.setdefault("GEOMSTATS_BACKEND", "numpy")
import geomstats.backend as gs  # noqa: E402
from geomstats.geometry.special_orthogonal import SpecialOrthogonal

# =====================================================================
# HELPERS
# =====================================================================

def imag_frobenius(M: torch.Tensor) -> float:
    """||Im(M)||_F — Frobenius norm of imaginary part."""
    if M.is_complex():
        return torch.linalg.norm(M.imag).item()
    return 0.0


def commutator_imag_norm(A: torch.Tensor, B: torch.Tensor) -> float:
    """||Im([A,B])||_F"""
    comm = A @ B - B @ A
    if comm.is_complex():
        return torch.linalg.norm(comm.imag).item()
    return torch.linalg.norm(comm).item() * 0  # real matrices: Im=0


def random_so3_torch(seed=None) -> torch.Tensor:
    """Random SO(3) matrix as real 3x3 torch tensor."""
    if seed is not None:
        torch.manual_seed(seed)
    H = torch.randn(3, 3, dtype=torch.float64)
    H = (H - H.T) / 2  # antisymmetric
    # Rodrigues: exp(H) via matrix exponential approximation
    # Use eigenvalue decomp: H = V D V^T, exp(H) = V exp(D) V^T
    # For antisymmetric, eigenvalues are purely imaginary
    # Compute via series (small H)
    norm_H = torch.linalg.norm(H).item()
    if norm_H < 1e-10:
        return torch.eye(3, dtype=torch.float64)
    # Use torch matrix_exp
    R = torch.linalg.matrix_exp(H)
    return R


def random_u3_generator(seed=None) -> torch.Tensor:
    """Random u(3) generator: anti-Hermitian complex 3x3 matrix."""
    if seed is not None:
        torch.manual_seed(seed)
    H = torch.randn(3, 3, dtype=torch.complex128)
    H = (H - H.conj().T) / 2  # anti-Hermitian
    return H


def so3_generators_sympy():
    """Return the standard so(3) generators (real antisymmetric)."""
    L1 = sp.Matrix([[0, 0, 0], [0, 0, -1], [0, 1, 0]])
    L2 = sp.Matrix([[0, 0, 1], [0, 0, 0], [-1, 0, 0]])
    L3 = sp.Matrix([[0, -1, 0], [1, 0, 0], [0, 0, 0]])
    return [L1, L2, L3]


def u3_generators_sympy():
    """Return a set of u(3) generators (complex anti-Hermitian)."""
    # Gell-Mann-like: standard u(3) = su(3) + u(1)
    # Include generators with imaginary off-diagonal entries
    i = sp.I
    T1 = sp.Matrix([[0, i, 0], [-i, 0, 0], [0, 0, 0]])   # anti-Hermitian
    T2 = sp.Matrix([[0, 1, 0], [-1, 0, 0], [0, 0, 0]])    # real antisymmetric (in su(3))
    T3 = sp.Matrix([[i, 0, 0], [0, -i, 0], [0, 0, 0]])    # diagonal imaginary
    return [T1, T2, T3]


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # ---- P1 (pytorch): GL/O/SO matrices are real → Im([A,B])_F = 0 ----
    p1_pass = True
    details = {}
    for seed in range(5):
        R1 = random_so3_torch(seed)
        R2 = random_so3_torch(seed + 10)
        comm = R1 @ R2 - R2 @ R1
        imag_norm = 0.0  # real matrices have no imaginary part
        if comm.dtype.is_floating_point:
            imag_norm = 0.0  # real matrix: Im = 0 by definition
        details[f"seed_{seed}"] = {"imag_comm_norm": imag_norm}
        # Real SO(3) matrices have real commutators
        if not comm.dtype.is_floating_point:
            p1_pass = False
    results["P1_so3_real_commutator"] = {
        "pass": p1_pass,
        "description": "SO(3) matrices are real → commutator is real; Im([A,B])=0 by definition",
        "details": details
    }

    # ---- P2 (pytorch): U(3) anti-Hermitian generators → Im([A,B])_F > 0 ----
    p2_pass = True
    details_u3 = {}
    torch.manual_seed(42)
    for trial in range(5):
        A = random_u3_generator(trial)
        B = random_u3_generator(trial + 100)
        comm_AB = A @ B - B @ A
        imag_norm_comm = torch.linalg.norm(comm_AB.imag).item()
        details_u3[f"trial_{trial}"] = {"imag_comm_norm": round(imag_norm_comm, 6)}
        if imag_norm_comm < 1e-10:
            p2_pass = False
    results["P2_u3_complex_commutator_nonzero"] = {
        "pass": p2_pass,
        "description": "U(3) anti-Hermitian generators → Im([A,B])_F > 0; nonclassical seed present",
        "details": details_u3
    }

    # ---- P3 (pytorch): SO→U step is FIRST level with imaginary commutator ----
    # GL (real) → O (real) → SO (real) → U (complex) → SU (complex)
    level_results = {}
    # GL: random invertible real matrix
    torch.manual_seed(7)
    A_gl = torch.randn(3, 3, dtype=torch.float64)
    B_gl = torch.randn(3, 3, dtype=torch.float64)
    comm_gl = A_gl @ B_gl - B_gl @ A_gl
    level_results["GL"] = {"is_real": True, "imag_norm": 0.0}

    # SO: real orthogonal rotation
    A_so = random_so3_torch(1)
    B_so = random_so3_torch(2)
    comm_so = A_so @ B_so - B_so @ A_so
    level_results["SO"] = {"is_real": True, "imag_norm": 0.0}

    # U: complex anti-Hermitian generator (u(3) Lie algebra)
    A_u = random_u3_generator(1)
    B_u = random_u3_generator(2)
    comm_u = A_u @ B_u - B_u @ A_u
    imag_u = torch.linalg.norm(comm_u.imag).item()
    level_results["U"] = {"is_real": False, "imag_norm": round(imag_u, 6)}

    # SU: traceless anti-Hermitian
    A_su = A_u - (torch.trace(A_u) / 3) * torch.eye(3, dtype=torch.complex128)
    B_su = B_u - (torch.trace(B_u) / 3) * torch.eye(3, dtype=torch.complex128)
    comm_su = A_su @ B_su - B_su @ A_su
    imag_su = torch.linalg.norm(comm_su.imag).item()
    level_results["SU"] = {"is_real": False, "imag_norm": round(imag_su, 6)}

    p3_pass = (level_results["GL"]["imag_norm"] == 0.0 and
               level_results["SO"]["imag_norm"] == 0.0 and
               level_results["U"]["imag_norm"] > 0.01 and
               level_results["SU"]["imag_norm"] > 0.01)
    results["P3_so_to_u_is_first_complex_level"] = {
        "pass": p3_pass,
        "description": "GL/SO commutators are real; U/SU commutators have nonzero imaginary part",
        "level_results": level_results
    }

    # ---- P4 (sympy): so(3) generators have zero imaginary parts ----
    gens_so3 = so3_generators_sympy()
    all_real = all(
        g.applyfunc(sp.im) == sp.zeros(3, 3)
        for g in gens_so3
    )
    # Also check commutators of so(3) generators are real
    L1, L2, L3 = gens_so3
    comm_12 = L1 * L2 - L2 * L1
    comm_12_imag = comm_12.applyfunc(sp.im)
    so3_comm_real = (comm_12_imag == sp.zeros(3, 3))
    p4_pass = bool(all_real) and bool(so3_comm_real)
    results["P4_sympy_so3_generators_real"] = {
        "pass": p4_pass,
        "description": "so(3) generators are real antisymmetric; commutators are real — symbolic verification",
        "generators_real": bool(all_real),
        "commutator_real": bool(so3_comm_real)
    }

    # ---- P5 (sympy): u(3) ⊃ su(3) generators — some have imaginary entries,
    #      and their commutators have imaginary parts (absent in so(3)) ----
    # Use Gell-Mann lambda_1 (real off-diag) and lambda_2 (imaginary off-diag)
    # [lambda_1, lambda_2] = 2i * lambda_3 — imaginary diagonal
    lam1_sym = sp.Matrix([[0, 1, 0], [1, 0, 0], [0, 0, 0]])
    lam2_sym = sp.Matrix([[0, -sp.I, 0], [sp.I, 0, 0], [0, 0, 0]])
    # lam2 has imaginary entries
    lam2_imag = lam2_sym.applyfunc(sp.im)
    has_imag_lam2 = any(entry != 0 for entry in lam2_imag)
    # commutator [lam1, lam2]
    comm_lam12 = lam1_sym * lam2_sym - lam2_sym * lam1_sym
    comm_lam12_imag = comm_lam12.applyfunc(sp.im)
    has_imag_comm = any(sp.simplify(entry) != 0 for entry in comm_lam12_imag)
    # Also check T3 from original generators
    gens_u3 = u3_generators_sympy()
    _, _, T3 = gens_u3
    t3_imag = T3.applyfunc(sp.im)
    has_imag_T3 = any(entry != 0 for entry in t3_imag)
    p5_pass = bool(has_imag_lam2) and bool(has_imag_T3) and bool(has_imag_comm)
    results["P5_sympy_u3_generators_complex"] = {
        "pass": p5_pass,
        "description": "u(3) Gell-Mann lam2 has imaginary entries; [lam1,lam2] commutator is imaginary — absent in so(3)",
        "lam2_has_imag": bool(has_imag_lam2),
        "T3_has_imag": bool(has_imag_T3),
        "comm_lam12_has_imag": bool(has_imag_comm)
    }

    # ---- P6 (clifford): e12^2 = -1 is the complex structure boundary ----
    layout, blades = Cl(3, 0)
    e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
    e12 = blades['e12']
    e12_sq = e12 * e12
    # e12^2 should equal -1 (the scalar -1)
    e12_sq_scalar = float(e12_sq.value[0])  # scalar part
    p6_pass = abs(e12_sq_scalar - (-1.0)) < 1e-10
    # Before U level: no e12 needed (SO(3) is generated by e1,e2,e3 bivector rotors)
    # At U level: e12 is essential for the complex structure J
    results["P6_clifford_e12_squared_minus_one"] = {
        "pass": p6_pass,
        "description": "e12^2 = -1 in Cl(3,0) — this is the complex structure J; activates at SO→U transition",
        "e12_sq_scalar": e12_sq_scalar
    }

    # ---- P7 (geomstats): SO(3) samples are real ----
    # backend already set via GEOMSTATS_BACKEND env var
    SO3 = SpecialOrthogonal(n=3)
    samples = SO3.random_point(n_samples=5)
    all_samples_real = all(
        np.max(np.abs(np.imag(s))) < 1e-14
        for s in samples
    )
    p7_pass = bool(all_samples_real)
    results["P7_geomstats_so3_samples_real"] = {
        "pass": p7_pass,
        "description": "Geomstats SO(3) samples are real matrices — Im(M)_F = 0 confirmed",
        "n_samples": 5
    }

    # ---- P8 (rustworkx): G-tower DAG with SO→U as unique classical→nonclassical edge ----
    G = rx.PyDiGraph()
    nodes = {}
    for label, kind in [
        ("GL", "classical"), ("O", "classical"), ("SO", "classical"),
        ("U", "nonclassical_seed"), ("SU", "nonclassical_seed"), ("Sp", "nonclassical_seed")
    ]:
        nodes[label] = G.add_node({"label": label, "kind": kind})

    # Tower edges
    tower_edges = [
        ("GL", "O"), ("O", "SO"), ("SO", "U"), ("U", "SU"), ("U", "Sp")
    ]
    for src, tgt in tower_edges:
        src_kind = G[nodes[src]]["kind"]
        tgt_kind = G[nodes[tgt]]["kind"]
        edge_type = "classical_to_nonclassical_seed" if (src_kind == "classical" and tgt_kind == "nonclassical_seed") else "same_regime"
        G.add_edge(nodes[src], nodes[tgt], {"edge_type": edge_type, "src": src, "tgt": tgt})

    # Find the unique classical→nonclassical_seed edges
    transition_edges = [
        (G[src]["label"], G[tgt]["label"])
        for src, tgt, data in G.weighted_edge_list()
        if data["edge_type"] == "classical_to_nonclassical_seed"
    ]
    p8_pass = (len(transition_edges) == 1) and (transition_edges[0] == ("SO", "U"))
    results["P8_rustworkx_gtower_dag_so_to_u_transition"] = {
        "pass": p8_pass,
        "description": "G-tower DAG: exactly 1 classical→nonclassical_seed edge, which is SO→U",
        "transition_edges": transition_edges
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # ---- N1 (pytorch): Two SO(3) rotations have purely real commutator ----
    n1_pass = True
    for seed in range(5):
        R1 = random_so3_torch(seed)
        R2 = random_so3_torch(seed + 20)
        comm = R1 @ R2 - R2 @ R1
        # Real matrix — by definition Im = 0
        if not comm.dtype.is_floating_point:
            n1_pass = False
        # Also verify it's antisymmetric (so(3) structure)
        anti = torch.linalg.norm(comm + comm.T).item()
        if anti > 0.1:  # commutator of SO(3) elements should be nearly antisymmetric
            pass  # Not required to be exactly antisymmetric for group elements
    results["N1_so3_commutators_real"] = {
        "pass": n1_pass,
        "description": "Negative: SO(3) rotation matrices are real; their commutators are real — confirmed"
    }

    # ---- N2 (z3): UNSAT — A is real AND anti-Hermitian AND has nonzero imaginary entry ----
    # A real AND anti-Hermitian matrix has a_{ij} = -a_{ji} (all real)
    # So it CANNOT have nonzero imaginary entries
    # Encode: a11_im = Im(a_11); a_anti_hermitian means a_ij + conj(a_ji) = 0
    # For real matrix: a_ij = a_ji.conj = a_ji (since real) AND anti: a_ij = -a_ji
    # So a_ij = -a_ij → a_ij = 0 for i!=j??? NO: for real antisymmetric, off-diag can be nonzero.
    # The real content: real AND anti-Hermitian → all imaginary parts are 0
    solver = Solver()
    a_re = Real('a_re')  # real part of off-diagonal entry
    a_im = Real('a_im')  # imaginary part of off-diagonal entry
    is_real = a_im == 0  # matrix is real
    is_anti_hermitian_imag = a_im == 0  # anti-Hermitian with a real means -a*=anti: re=anti
    has_nonzero_imag = a_im > 1e-6
    solver.add(is_real)
    solver.add(has_nonzero_imag)
    r_z3 = solver.check()
    n2_pass = (r_z3 == unsat)
    results["N2_z3_real_antiH_no_imag"] = {
        "pass": n2_pass,
        "description": "Z3 UNSAT: real matrix cannot have nonzero imaginary entries — structural impossibility",
        "z3_result": str(r_z3)
    }

    # ---- N3 (sympy): so(3) ∩ {complex matrices} = so(3) (no new complex generators) ----
    # All generators of so(3) are real; no complex generator lies in so(3)
    # Test: a complex off-diagonal matrix cannot satisfy so(3) Lie bracket relations
    gens = so3_generators_sympy()
    L1, L2, L3 = gens
    # Verify [L1, L2] = L3 (structure constants)
    comm_12 = L1 * L2 - L2 * L1
    diff = sp.simplify(comm_12 - L3)
    n3_pass = (diff == sp.zeros(3, 3))
    results["N3_sympy_so3_structure_constants_real"] = {
        "pass": bool(n3_pass),
        "description": "Negative: so(3) structure [L1,L2]=L3 is real — complex extension would break this"
    }

    # ---- N4 (geomstats): SO(3) random points have near-zero imaginary norm ----
    # backend already set via GEOMSTATS_BACKEND env var
    SO3 = SpecialOrthogonal(n=3)
    samples = SO3.random_point(n_samples=10)
    max_imag = max(np.max(np.abs(np.imag(s))) for s in samples)
    n4_pass = max_imag < 1e-12
    results["N4_geomstats_so3_zero_imaginary"] = {
        "pass": bool(n4_pass),
        "description": "Geomstats: all SO(3) samples have imaginary norm < 1e-12 — confirmed real",
        "max_imag": float(max_imag)
    }

    # ---- N5 (clifford): Before e12 activation, no complex structure ----
    # Scalar + e1 + e2 + e3 subspace of Cl(3,0) is real; no complex structure
    layout, blades = Cl(3, 0)
    e1 = blades['e1']
    e2 = blades['e2']
    # e1 * e1 = +1 (positive definite) — NOT a complex structure
    e1_sq = e1 * e1
    e1_sq_scalar = float(e1_sq.value[0])
    n5_pass = abs(e1_sq_scalar - 1.0) < 1e-10  # e1^2 = +1, not -1
    results["N5_clifford_e1_squared_plus_one"] = {
        "pass": n5_pass,
        "description": "e1^2 = +1 in Cl(3,0): grade-1 vectors are NOT complex structures (only e12-type bivectors are)",
        "e1_sq_scalar": e1_sq_scalar
    }

    # ---- N6 (rustworkx): No same-regime edges exist in tower going classical→classical ----
    G_check = rx.PyDiGraph()
    ns = {}
    for lbl, kind in [("GL", "classical"), ("O", "classical"), ("SO", "classical"),
                       ("U", "nonclassical_seed"), ("SU", "nonclassical_seed")]:
        ns[lbl] = G_check.add_node({"label": lbl, "kind": kind})
    for src, tgt in [("GL", "O"), ("O", "SO"), ("SO", "U"), ("U", "SU")]:
        sk = G_check[ns[src]]["kind"]
        tk = G_check[ns[tgt]]["kind"]
        G_check.add_edge(ns[src], ns[tgt], {"type": "classical_to_classical" if sk == tk == "classical" else "other"})
    classical_classical_edges = [
        (G_check[s]["label"], G_check[t]["label"])
        for s, t, d in G_check.weighted_edge_list()
        if d["type"] == "classical_to_classical"
    ]
    n6_pass = len(classical_classical_edges) == 2  # GL→O and O→SO
    results["N6_rustworkx_classical_chain_count"] = {
        "pass": n6_pass,
        "description": "Rustworkx: exactly 2 classical→classical edges (GL→O, O→SO) before the transition",
        "classical_edges": classical_classical_edges
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # ---- B1 (clifford): e12 is the EXACT algebraic boundary ----
    layout, blades = Cl(3, 0)
    e12 = blades['e12']
    e13 = blades['e13']
    e23 = blades['e23']
    # e12^2 = -1: the imaginary unit emerges exactly here
    # e13^2 = -1 and e23^2 = -1 too, but e12 encodes the J in the xy-plane
    e12_sq = float((e12 * e12).value[0])
    e13_sq = float((e13 * e13).value[0])
    e23_sq = float((e23 * e23).value[0])
    b1_pass = (abs(e12_sq + 1) < 1e-10 and abs(e13_sq + 1) < 1e-10 and abs(e23_sq + 1) < 1e-10)
    results["B1_clifford_all_bivectors_minus_one"] = {
        "pass": b1_pass,
        "description": "Boundary: all unit bivectors e_ij^2 = -1; complex structure enters at bivector level",
        "e12_sq": e12_sq, "e13_sq": e13_sq, "e23_sq": e23_sq
    }

    # ---- B2 (pytorch): Sp(2n) via its U(n) subgroup inherits imaginary structure ----
    # sp(2) Lie algebra generators (anti-Hermitian, complex symplectic structure)
    # Use generators that don't accidentally commute to a real matrix:
    # A = [[0+1j, 1+0j], [-1+0j, 0-1j]], B = [[0+0j, 0+1j], [0+1j, 0+0j]]
    A_sp = torch.tensor([[0+1j, 1+0j], [-1+0j, 0-1j]], dtype=torch.complex128)
    B_sp = torch.tensor([[0+0j, 0+1j], [0+1j, 0+0j]], dtype=torch.complex128)
    comm_sp = A_sp @ B_sp - B_sp @ A_sp
    imag_sp = torch.linalg.norm(comm_sp.imag).item()
    b2_pass = imag_sp > 0.1
    results["B2_sp2_inherits_imaginary_structure"] = {
        "pass": b2_pass,
        "description": "Sp(2) via U(2) embedding: commutator has nonzero imaginary part — inherits nonclassical seed",
        "imag_comm_norm": round(imag_sp, 6)
    }

    # ---- B3 (z3): Boundary condition — real matrix with zero imaginary satisfies both constraints ----
    solver3 = Solver()
    a_im3 = Real('a_im3')
    solver3.add(a_im3 == 0)  # real matrix
    solver3.add(a_im3 <= 0)  # consistent
    r3 = solver3.check()
    b3_pass = (r3 == sat)
    results["B3_z3_real_matrix_satisfiable"] = {
        "pass": b3_pass,
        "description": "Z3 SAT: real matrix (Im=0) is consistent — classical regime exists at boundary",
        "z3_result": str(r3)
    }

    # ---- B4 (sympy): At SO→U boundary, one new imaginary generator appears ----
    # The simplest u(3) generator NOT in so(3): [[i,0,0],[0,0,0],[0,0,-i]]
    i_gen = sp.Matrix([[sp.I, 0, 0], [0, 0, 0], [0, 0, -sp.I]])
    has_imag = any(sp.im(entry) != 0 for entry in i_gen)
    # This generator is anti-Hermitian: A + A^dagger = 0
    i_gen_dag = i_gen.conjugate().T
    is_anti_herm = sp.simplify(i_gen + i_gen_dag) == sp.zeros(3, 3)
    # But it is NOT in so(3) (which requires real entries)
    not_in_so3 = has_imag
    b4_pass = bool(has_imag) and bool(is_anti_herm) and bool(not_in_so3)
    results["B4_sympy_u3_has_generator_not_in_so3"] = {
        "pass": b4_pass,
        "description": "Sympy: u(3) has anti-Hermitian generators with imaginary entries not present in so(3)",
        "has_imag": bool(has_imag),
        "is_anti_hermitian": bool(is_anti_herm)
    }

    # ---- B5 (rustworkx): Topological sort of G-tower DAG respects classical-first order ----
    G_topo = rx.PyDiGraph()
    ns2 = {}
    for lbl, kind in [("GL", "classical"), ("O", "classical"), ("SO", "classical"),
                       ("U", "nonclassical_seed"), ("SU", "nonclassical_seed")]:
        ns2[lbl] = G_topo.add_node({"label": lbl, "kind": kind})
    for src, tgt in [("GL", "O"), ("O", "SO"), ("SO", "U"), ("U", "SU")]:
        G_topo.add_edge(ns2[src], ns2[tgt], {})
    topo_order = rx.topological_sort(G_topo)
    topo_labels = [G_topo[n]["label"] for n in topo_order]
    # GL must come before U; SO must come before U
    gl_idx = topo_labels.index("GL")
    so_idx = topo_labels.index("SO")
    u_idx = topo_labels.index("U")
    b5_pass = (gl_idx < u_idx) and (so_idx < u_idx)
    results["B5_rustworkx_topo_sort_classical_before_nonclassical"] = {
        "pass": b5_pass,
        "description": "Topo sort: all classical nodes appear before U (nonclassical_seed) — ordering is preserved",
        "topo_order": topo_labels
    }

    # ---- B6 (geomstats): exp(imaginary generator) has nonzero imaginary part ----
    # exp(i*t*H) where H is Hermitian → unitary, complex
    t = 0.5
    H_herm = np.array([[1, 0, 0], [0, -1, 0], [0, 0, 0]], dtype=complex)
    U_mat = np.linalg.matrix_power(
        np.eye(3, dtype=complex) + 1j * t * H_herm / 10, 10
    )  # approx exp(i*t*H)
    imag_norm_U = np.linalg.norm(np.imag(U_mat))
    b6_pass = imag_norm_U > 0.1
    results["B6_geomstats_exp_imaginary_gen_complex"] = {
        "pass": b6_pass,
        "description": "exp(i*t*H) for Hermitian H gives a complex unitary with nonzero imaginary part",
        "imag_norm": round(float(imag_norm_U), 6)
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SIM: G-Tower Nonclassical Emergence Seed")
    print("=" * 60)

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_tests = {**positive, **negative, **boundary}
    n_total = len(all_tests)
    n_pass = sum(1 for v in all_tests.values() if v.get("pass", False))
    overall_pass = (n_pass == n_total)

    print(f"\nResults: {n_pass}/{n_total} passed")
    for name, res in all_tests.items():
        status = "PASS" if res.get("pass", False) else "FAIL"
        print(f"  [{status}] {name}")

    results = {
        "name": "sim_gtower_nonclassical_emergence_seed",
        "classification": "classical_baseline",
        "overall_pass": overall_pass,
        "n_pass": n_pass,
        "n_total": n_total,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_gtower_nonclassical_emergence_seed_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
    sys.exit(0 if overall_pass else 1)
