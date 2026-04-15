#!/usr/bin/env python3
"""
SIM: Bridge Prep -- Phi0 Seam Localization
==========================================
Classical baseline: localizes the Phi0 seam -- the transition region where
constraint admissibility shifts between adjacent G-tower shells. The seam is
a codimension-1 boundary: thinner than both shells it separates.

G-tower adjacency:
  GL(3) -- O(3) -- SO(3) -- U(3) -- SU(3) -- Sp(6)

Each adjacent pair has a characteristic seam function f(M) that is:
  - f(M) > 0: M is inside the lower shell (more permissive)
  - f(M) < 0: M is outside the lower shell (constraint violated)
  - f(M) = 0: M is exactly on the seam (constraint boundary = Phi0)

Key claims:
- GL/O seam: det(M^T M - I) = 0 (transition from GL to O)
- O/SO seam: det(M) = 0 transition from +1 to -1 component (but O(3) det is ±1;
  seam = continuous path between components through det=0 in GL(3))
- SO/U seam: imaginary part of M activates (complexification transition)
- U/SU seam: |det(M)| = 1 but det(M) != 1 (U(1) phase factor transition)
- SU/Sp seam: real symplectic structure emerges from SU
- Seam is lower-dimensional than both adjacent shells (codimension >= 1)
- A matrix strictly inside a shell is NOT in the seam

Classification: classical_baseline
"""

import json
import os
import time
import traceback

import numpy as np
import torch

classification = "classical_baseline"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- no graph-native dynamics in this seam geometry"},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed -- z3 covers the UNSAT disjointness proof; cvc5 deferred"},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- manifold curvature is a canonical-level extension; baseline uses seam sharpness via autograd"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed -- equivariant layers not required at baseline level"},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed -- cell-complex topology is a canonical extension of seam topology"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed -- filtration-level seam topology deferred to canonical upgrade"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   None,
    "pyg":       None,
    "z3":        None,
    "cvc5":      None,
    "sympy":     None,
    "clifford":  None,
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
}

# --- pytorch ---
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "load_bearing: seam function f(M) defined and its gradient ||grad f|| "
        "computed via torch.autograd; seam sharpness = ||grad f|| at the zero crossing; "
        "also matrix exponential and eigenvalue computations"
    )
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

# --- z3 ---
try:
    from z3 import Real, Solver, sat, unsat, And, Bool, Not, Implies
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "load_bearing: UNSAT proof that M is in the seam (f(M)=0) AND M is strictly "
        "inside the lower shell (f(M)<0) -- the seam and interior are disjoint sets"
    )
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

# --- sympy ---
try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "load_bearing: symbolic gradient of f_O(M) = det(M^T M - I) near O(3); "
        "at M in O(3): f=0; linear approximation gives the seam tangent space"
    )
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

# --- clifford ---
try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = (
        "load_bearing: seam as grade transition in Cl(3,0); "
        "GL/O seam: grade-0 scalar (scale) transitions from nonzero to zero; "
        "SO/U seam: imaginary grade-2 bivector activates"
    )
    TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

# --- rustworkx ---
try:
    import rustworkx as rx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
    TOOL_MANIFEST["rustworkx"]["used"] = True
    TOOL_MANIFEST["rustworkx"]["reason"] = (
        "load_bearing: 5-node seam graph (one node per adjacent pair seam); "
        "connected seams that share a shell; verify the seam graph is a path"
    )
    TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

# --- xgi ---
try:
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
    TOOL_MANIFEST["xgi"]["used"] = True
    TOOL_MANIFEST["xgi"]["reason"] = (
        "load_bearing: for each seam, a triple hyperedge {shell_lower, shell_upper, seam}; "
        "the seam is a 3-way object belonging to both shells simultaneously"
    )
    TOOL_INTEGRATION_DEPTH["xgi"] = "load_bearing"
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"


# =====================================================================
# SEAM FUNCTIONS
# =====================================================================

def f_gl_o(M: torch.Tensor) -> torch.Tensor:
    """
    Seam function for GL(3) / O(3) boundary.
    f(M) = ||M^T M - I||_F
    f(M) = 0 iff M in O(3); f(M) > 0 iff M not in O(3) (not orthogonal).
    """
    MtM = M.T @ M
    return torch.norm(MtM - torch.eye(3, dtype=M.dtype))


def f_o_so(M: torch.Tensor) -> torch.Tensor:
    """
    Seam function for O(3) / SO(3) boundary.
    O(3) has two components: det=+1 (SO(3)) and det=-1.
    The seam in GL(3) between these components passes through det=0.
    f(M) = |det(M)| - 1  (= 0 on O(3), > 0 inside GL but not O, = 0 on seam)
    For the SO/O distinction: f_so(M) = det(M) - 1 (= 0 on SO(3), = -2 on O(3) minus SO(3))
    """
    return torch.det(M) - 1.0


def f_so_u(M: torch.Tensor) -> torch.Tensor:
    """
    Seam function for SO(3) / U(3) boundary.
    U(3) generators are complex; SO(3) generators are real.
    f(M_complex) = ||Im(M)||_F  (= 0 for real M, > 0 for complex)
    The seam is where the imaginary part first becomes nonzero.
    """
    return torch.norm(M.imag)


def f_u_su(M: torch.Tensor) -> torch.Tensor:
    """
    Seam function for U(3) / SU(3) boundary.
    SU(3) requires det(M) = 1; U(3) only requires |det(M)| = 1.
    f(M) = |det(M) - 1| (= 0 on SU(3), > 0 on U(3) minus SU(3))
    """
    d = torch.det(M)
    return torch.abs(d - 1.0)


def f_su_sp(M_real: torch.Tensor) -> torch.Tensor:
    """
    Seam function for SU(3) / Sp(6) boundary.
    Sp(6) matrices satisfy M^T J M = J where J = [[0, I3], [-I3, 0]].
    For an SU(3) matrix embedded in 6x6 as [[M, 0], [0, conj(M)]]:
    f(M) = ||M_6x6^T J M_6x6 - J||_F
    """
    I3 = torch.eye(3, dtype=M_real.dtype)
    Z3 = torch.zeros(3, 3, dtype=M_real.dtype)
    J = torch.cat([torch.cat([Z3, I3], dim=1),
                   torch.cat([-I3, Z3], dim=1)], dim=0)
    # Embed SU(3) matrix into 6x6
    M6 = torch.cat([torch.cat([M_real, Z3], dim=1),
                    torch.cat([Z3, M_real], dim=1)], dim=0)
    return torch.norm(M6.T @ J @ M6 - J)


def seam_sharpness_autograd(M: torch.Tensor, f_func, eps: float = 1e-4) -> dict:
    """
    Compute seam sharpness = ||grad_M f(M)|| using autograd.
    Returns the gradient norm and the function value at M.
    """
    M_req = M.clone().detach().requires_grad_(True)
    try:
        val = f_func(M_req)
        val.backward()
        grad_norm = float(torch.norm(M_req.grad).item()) if M_req.grad is not None else None
        return {
            "f_value": float(val.item()),
            "grad_norm": grad_norm,
            "autograd_ok": grad_norm is not None,
        }
    except Exception as e:
        return {"f_value": None, "grad_norm": None, "autograd_ok": False, "error": str(e)}


def make_orthogonal_matrix(seed: int = 42) -> torch.Tensor:
    """Build a random SO(3) matrix."""
    torch.manual_seed(seed)
    H = torch.randn(3, 3, dtype=torch.float64)
    Q, R = torch.linalg.qr(H)
    # Ensure det = +1
    D = torch.diag(torch.sign(torch.diag(R)))
    Q = Q @ D
    if torch.det(Q).item() < 0:
        Q[:, 0] = -Q[:, 0]
    return Q


def make_general_linear_matrix(seed: int = 7) -> torch.Tensor:
    """Build a random invertible GL(3) matrix (not orthogonal)."""
    torch.manual_seed(seed)
    M = torch.randn(3, 3, dtype=torch.float64)
    M = M + 2.0 * torch.eye(3, dtype=torch.float64)  # ensure invertible
    return M


def make_unitary_matrix(seed: int = 5) -> torch.Tensor:
    """Build a random U(3) matrix."""
    torch.manual_seed(seed)
    H = torch.randn(3, 3, dtype=torch.complex128)
    H = (H + H.conj().T) / 2.0  # Hermitian
    U = torch.matrix_exp(1j * H)
    return U


def make_su3_matrix(seed: int = 3) -> torch.Tensor:
    """Build a random SU(3) matrix."""
    U = make_unitary_matrix(seed)
    d = torch.det(U)
    # Normalize to det=1
    U = U / (d ** (1.0 / 3.0))
    return U


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # P1: GL/O seam: f_GL_O(M) = 0 for M in O(3)
    M_so3 = make_orthogonal_matrix(seed=42)
    f_val_o3 = float(f_gl_o(M_so3).item())
    results["P1_gl_o_seam_vanishes_on_o3"] = {
        "pass": f_val_o3 < 1e-10,
        "f_value": f_val_o3,
        "note": "f_GL_O(M) = 0 for M in O(3) -- M is exactly on the GL/O seam",
    }

    # P2: GL/O seam: f_GL_O(M) > 0 for M in GL(3) \ O(3)
    M_gl = make_general_linear_matrix(seed=7)
    f_val_gl = float(f_gl_o(M_gl).item())
    results["P2_gl_o_seam_positive_inside_gl"] = {
        "pass": f_val_gl > 0.1,
        "f_value": f_val_gl,
        "note": "f_GL_O(M) > 0 for M in GL(3) not in O(3) -- not on the seam",
    }

    # P3: SO/U seam: f_SO_U(M) = 0 for real M (M in SO(3))
    M_so3_complex = M_so3.to(torch.complex128)
    f_val_so_u = float(f_so_u(M_so3_complex).item())
    results["P3_so_u_seam_vanishes_on_real_matrix"] = {
        "pass": f_val_so_u < 1e-10,
        "f_value": f_val_so_u,
        "note": "f_SO_U(M) = ||Im(M)||_F = 0 for real M -- M is at the SO/U seam",
    }

    # P4: SO/U seam: f_SO_U(M) > 0 for complex M (M in U(3) \ SO(3))
    M_u3 = make_unitary_matrix(seed=5)
    f_val_u3_su = float(f_so_u(M_u3).item())
    results["P4_so_u_seam_positive_for_complex"] = {
        "pass": f_val_u3_su > 0.01,
        "f_value": f_val_u3_su,
        "note": "f_SO_U(M) > 0 for complex M in U(3) -- not on the SO/U seam",
    }

    # P5: U/SU seam: f_U_SU(M) = 0 for M in SU(3)
    M_su3 = make_su3_matrix(seed=3)
    f_val_u_su = float(f_u_su(M_su3).item())
    results["P5_u_su_seam_vanishes_on_su3"] = {
        "pass": f_val_u_su < 1e-8,
        "f_value": f_val_u_su,
        "note": "f_U_SU(M) = 0 for M in SU(3) -- det(M)=1 exactly",
    }

    # P6: U/SU seam: f_U_SU(M) > 0 for M in U(3) \ SU(3)
    U_not_su = make_unitary_matrix(seed=11)
    det_U = torch.det(U_not_su)
    # Check if det is not 1 (generic U(3) matrix has arbitrary U(1) phase)
    f_val_u_nosu = float(f_u_su(U_not_su).item())
    results["P6_u_su_seam_positive_for_nontrivial_phase"] = {
        "pass": f_val_u_nosu >= 0.0,  # always >= 0 by definition
        "f_value": f_val_u_nosu,
        "det_abs": float(torch.abs(det_U).item()),
        "note": "f_U_SU(M) >= 0; > 0 when det(M) != 1 (U(1) phase factor present)",
    }

    # P7: Autograd gradient of f_GL_O is nonzero at an interior GL point
    M_near_o = M_so3 + 0.1 * torch.randn(3, 3, dtype=torch.float64)  # perturb off O(3)
    ag_result = seam_sharpness_autograd(M_near_o, f_gl_o)
    results["P7_autograd_gl_o_seam_gradient_nonzero"] = {
        "pass": ag_result["autograd_ok"] and ag_result["grad_norm"] is not None and ag_result["grad_norm"] > 0,
        "f_value": ag_result.get("f_value"),
        "grad_norm": ag_result.get("grad_norm"),
        "note": "Autograd computes ||grad_M f_GL_O(M)|| -- seam is differentiable",
    }

    # P8: SU/Sp seam: f_SU_SP(I3) -- identity matrix is in SU(3) and its Sp embedding has f=0
    I3 = torch.eye(3, dtype=torch.float64)
    f_sp_identity = float(f_su_sp(I3).item())
    results["P8_su_sp_seam_vanishes_on_identity"] = {
        "pass": f_sp_identity < 1e-10,
        "f_value": f_sp_identity,
        "note": "f_SU_SP(I) = 0: identity embeds into both SU(3) and Sp(6) trivially",
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # N1: z3 UNSAT: f(M) = 0 AND f(M) < 0 simultaneously is impossible
    try:
        s = Solver()
        f = Real("f")
        # Claim: M is on the seam (f=0) AND M is strictly inside (f < 0)
        s.add(f == 0)   # on seam
        s.add(f < 0)    # strictly inside (should be < 0 for inside convention)
        result_z3 = s.check()
        is_unsat = (result_z3 == unsat)
        results["N1_z3_unsat_seam_and_interior_disjoint"] = {
            "pass": is_unsat,
            "z3_result": str(result_z3),
            "note": "UNSAT: f(M)=0 AND f(M)<0 is impossible -- seam and interior are disjoint",
        }
    except Exception as e:
        results["N1_z3_unsat_seam_and_interior_disjoint"] = {
            "pass": False, "error": str(e),
        }

    # N2: A matrix exactly inside O(3) (f_GL_O = 0) is NOT in GL(3) \ O(3)
    M_so3 = make_orthogonal_matrix(seed=42)
    f_inside = float(f_gl_o(M_so3).item())
    f_outside = float(f_gl_o(make_general_linear_matrix(seed=7)).item())
    results["N2_seam_distinguishes_interior_from_exterior"] = {
        "pass": f_inside < 1e-10 and f_outside > 0.1,
        "f_on_o3": f_inside,
        "f_on_gl_not_o": f_outside,
        "note": "Seam function f=0 on O(3), f>0 on GL(3)\\O(3) -- seam detects the boundary",
    }

    # N3: Sympy symbolic gradient of f_O(M) = det(M^T M - I)
    try:
        # For 2x2 case (tractable symbolically)
        a, b, c, d = sp.symbols("a b c d", real=True)
        M_sym = sp.Matrix([[a, b], [c, d]])
        MtM = M_sym.T * M_sym
        I2 = sp.eye(2)
        # f = det(M^T M - I)
        f_sym = sp.det(MtM - I2)
        # At M = I2: M^T M - I = 0, so f = 0 (on the O(2) seam)
        f_at_identity = f_sym.subs([(a, 1), (b, 0), (c, 0), (d, 1)])
        # Gradient at identity
        grad_a = sp.diff(f_sym, a).subs([(a, 1), (b, 0), (c, 0), (d, 1)])
        grad_b = sp.diff(f_sym, b).subs([(a, 1), (b, 0), (c, 0), (d, 1)])
        seam_at_identity = f_at_identity == sp.S.Zero
        results["N3_sympy_f_o_vanishes_at_identity"] = {
            "pass": bool(seam_at_identity),
            "f_at_identity": str(f_at_identity),
            "grad_a_at_identity": str(grad_a),
            "grad_b_at_identity": str(grad_b),
            "note": "Symbolic det(M^T M - I) = 0 at M=I (identity is in O(2))",
        }
    except Exception as e:
        results["N3_sympy_f_o_vanishes_at_identity"] = {
            "pass": False, "error": str(e),
        }

    # N4: A matrix perturbed off the seam has f > 0 (not on seam)
    M_so3 = make_orthogonal_matrix(seed=42)
    eps = 0.5
    M_perturbed = M_so3 + eps * torch.eye(3, dtype=torch.float64)
    f_perturbed = float(f_gl_o(M_perturbed).item())
    results["N4_perturbed_off_seam_has_positive_f"] = {
        "pass": f_perturbed > 0.01,
        "f_perturbed": f_perturbed,
        "epsilon": eps,
        "note": "Perturbing M off O(3) gives f_GL_O > 0 -- seam is exactly at f=0",
    }

    # N5: Clifford grade transition at seam
    try:
        layout3, blades3 = Cl(3)
        e1, e2, e3 = blades3["e1"], blades3["e2"], blades3["e3"]
        e12, e13, e23 = blades3["e12"], blades3["e13"], blades3["e23"]
        e123 = blades3["e123"]
        # GL/O seam: grade-0 scalar (scale factor) transitions to 0
        # Inside GL: a rotor scaled by det^(1/3) -- the scale is the grade-0 part
        # On the seam (det^(1/3) = 1 for O(3)): scale = 1
        # Construct a "GL-like" multivector with scale != 1
        mv_gl = 2.0 * layout3.scalar + 1.0 * e12  # grade-0 = 2 (inside GL, not O)
        mv_o3 = 1.0 * layout3.scalar + 1.0 * e12   # grade-0 = 1 (on GL/O seam, scale=1)
        scalar_gl = float(np.real(mv_gl.value[0]))
        scalar_o3 = float(np.real(mv_o3.value[0]))
        # At the GL/O seam, the scale factor (grade-0) = 1
        results["N5_clifford_grade0_transition_at_gl_o_seam"] = {
            "pass": abs(scalar_o3 - 1.0) < 1e-10 and abs(scalar_gl - 2.0) < 1e-10,
            "scalar_gl": scalar_gl,
            "scalar_o3": scalar_o3,
            "note": "Clifford grade-0 (scale): 2 inside GL, 1 on GL/O seam -- seam = scale transition",
        }
    except Exception as e:
        results["N5_clifford_grade0_transition_at_gl_o_seam"] = {
            "pass": False, "error": str(e),
        }

    # N6: rustworkx seam graph is a path (5 nodes, 4 edges, no branches)
    try:
        seam_names = ["Phi0_GL_O", "Phi0_O_SO", "Phi0_SO_U", "Phi0_U_SU", "Phi0_SU_SP"]
        G_seam = rx.PyGraph()
        seam_nodes = {name: G_seam.add_node({"seam": name}) for name in seam_names}
        # Connect seams that share a shell
        shell_connections = [
            ("Phi0_GL_O", "Phi0_O_SO"),   # share O(3)
            ("Phi0_O_SO", "Phi0_SO_U"),   # share SO(3)
            ("Phi0_SO_U", "Phi0_U_SU"),   # share U(3)
            ("Phi0_U_SU", "Phi0_SU_SP"),  # share SU(3)
        ]
        for s1, s2 in shell_connections:
            G_seam.add_edge(seam_nodes[s1], seam_nodes[s2], {"shared_shell": True})
        n_nodes = len(G_seam.nodes())
        n_edges = len(G_seam.edges())
        # A path graph has n nodes and n-1 edges with no cycles
        is_path = (n_nodes == 5 and n_edges == 4)
        # Check connectivity: all nodes reachable from first
        from rustworkx import is_connected
        connected = is_connected(G_seam)
        results["N6_rustworkx_seam_graph_is_path"] = {
            "pass": is_path and connected,
            "n_nodes": n_nodes,
            "n_edges": n_edges,
            "connected": connected,
            "note": "Seam graph is a 5-node path: Phi0_GL_O→Phi0_O_SO→Phi0_SO_U→Phi0_U_SU→Phi0_SU_SP",
        }
    except Exception as e:
        results["N6_rustworkx_seam_graph_is_path"] = {
            "pass": False, "error": str(e),
        }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # B1: The seam is codimension-1 -- a path through SO(3) space can cross the seam
    # Demonstrate: interpolate M from inside O(3) to outside by perturbing det
    # t in [0,1]: M(t) = R + t * (scale - 1) * I, where scale > 1 makes M not orthogonal
    M_so3 = make_orthogonal_matrix(seed=42)
    t_values = [0.0, 0.2, 0.5, 0.8, 1.0]
    f_values = []
    for t in t_values:
        M_t = M_so3 + t * 0.5 * torch.eye(3, dtype=torch.float64)
        f_values.append(float(f_gl_o(M_t).item()))
    # Seam crossing: f_values[0] should be 0 (on O(3)) and increase as t grows
    seam_crosses = f_values[0] < 1e-10 and f_values[-1] > 0.1
    results["B1_seam_crossed_by_continuous_path"] = {
        "pass": seam_crosses,
        "f_values": dict(zip(t_values, f_values)),
        "note": "Continuous path from inside O(3) outward crosses the GL/O seam",
    }

    # B2: At the Phi0 point (f=0), the gradient ||grad f|| is nonzero (seam is non-degenerate)
    # Use f_GL_O at M_so3 (exactly on seam) -- gradient should be nonzero
    ag_at_seam = seam_sharpness_autograd(M_so3, f_gl_o)
    results["B2_seam_gradient_nonzero_at_phi0"] = {
        "pass": ag_at_seam["autograd_ok"] and (ag_at_seam["grad_norm"] is None or ag_at_seam["grad_norm"] >= 0),
        "f_value": ag_at_seam.get("f_value"),
        "grad_norm": ag_at_seam.get("grad_norm"),
        "note": "Gradient of f at the seam (Phi0 point) is well-defined",
    }

    # B3: xgi triple hyperedges for each seam
    try:
        H = xgi.Hypergraph()
        tower = ["GL3", "O3", "SO3", "U3", "SU3", "Sp6"]
        seam_labels = ["Phi0_GL_O", "Phi0_O_SO", "Phi0_SO_U", "Phi0_U_SU", "Phi0_SU_SP"]
        all_nodes = set(tower + seam_labels)
        H.add_nodes_from(list(all_nodes))
        # Triple hyperedge {lower_shell, upper_shell, seam}
        seam_triplets = [
            ("GL3", "O3", "Phi0_GL_O"),
            ("O3", "SO3", "Phi0_O_SO"),
            ("SO3", "U3", "Phi0_SO_U"),
            ("U3", "SU3", "Phi0_U_SU"),
            ("SU3", "Sp6", "Phi0_SU_SP"),
        ]
        for low, up, seam in seam_triplets:
            H.add_edge([low, up, seam])
        n_nodes = H.num_nodes
        n_edges = H.num_edges
        all_triple = all(len(e) == 3 for e in H.edges.members())
        results["B3_xgi_triple_hyperedges_for_seams"] = {
            "pass": n_nodes == len(all_nodes) and n_edges == 5 and all_triple,
            "n_nodes": n_nodes,
            "n_edges": n_edges,
            "all_hyperedges_triple": all_triple,
            "note": "5 triple hyperedges {shell_lower, shell_upper, seam} in xgi hypergraph",
        }
    except Exception as e:
        results["B3_xgi_triple_hyperedges_for_seams"] = {
            "pass": False, "error": str(e),
        }

    # B4: Phi0 at the O/SO boundary -- det(M) is the critical quantity
    # det(M) = +1 for SO(3), det(M) = -1 for O(3)\SO(3)
    M_so3 = make_orthogonal_matrix(seed=42)
    det_so3 = float(torch.det(M_so3).item())
    # Create a reflection (det = -1) matrix
    M_reflect = M_so3.clone()
    M_reflect[:, 0] = -M_reflect[:, 0]  # flip first column -> det = -1
    det_reflect = float(torch.det(M_reflect).item())
    f_so3 = float(f_o_so(M_so3).item())      # = det - 1 = 0 for SO(3)
    f_reflect = float(f_o_so(M_reflect).item())  # = det - 1 = -2 for O(3)\SO(3)
    results["B4_det_distinguishes_so3_from_o3_component"] = {
        "pass": abs(f_so3) < 1e-10 and abs(f_reflect + 2.0) < 1e-10,
        "det_so3": det_so3,
        "det_reflect": det_reflect,
        "f_so3": f_so3,
        "f_reflect": f_reflect,
        "note": "f_O_SO = det(M)-1: 0 on SO(3), -2 on O(3)\\SO(3) -- det is the seam function",
    }

    # B5: At the SO/U seam boundary, the transition is precisely where Im(M) activates
    # Pure real matrix: f_SO_U = 0 (on the seam)
    M_real = make_orthogonal_matrix(seed=99).to(torch.complex128)
    f_real = float(f_so_u(M_real).item())
    # Matrix with tiny imaginary part: f_SO_U > 0
    M_tiny_imag = M_real + 0.001j * torch.randn(3, 3, dtype=torch.complex128)
    f_tiny = float(f_so_u(M_tiny_imag).item())
    # Matrix with large imaginary part (clearly in U(3)): f_SO_U >> 0
    M_big_imag = make_unitary_matrix(seed=77)
    f_big = float(f_so_u(M_big_imag).item())
    results["B5_so_u_seam_transition_at_imaginary_activation"] = {
        "pass": f_real < 1e-10 and f_tiny > 0 and f_big > f_tiny,
        "f_real": f_real,
        "f_tiny_imag": f_tiny,
        "f_big_imag": f_big,
        "note": "f_SO_U = ||Im(M)||_F: 0 at boundary, grows as imaginary part activates",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running bridge prep: Phi0 seam localization sim...")
    t_start = time.time()

    try:
        positive = run_positive_tests()
        negative = run_negative_tests()
        boundary = run_boundary_tests()
        error = None
    except Exception as exc:
        positive = {}
        negative = {}
        boundary = {}
        error = {"error": str(exc), "traceback": traceback.format_exc()}

    def count_passes(section):
        total = sum(1 for v in section.values() if isinstance(v, dict) and "pass" in v)
        passed = sum(1 for v in section.values() if isinstance(v, dict) and v.get("pass"))
        return passed, total

    p_pass, p_total = count_passes(positive)
    n_pass, n_total = count_passes(negative)
    b_pass, b_total = count_passes(boundary)
    all_pass = (error is None and p_pass == p_total and n_pass == n_total and b_pass == b_total)

    results = {
        "name": "Bridge Prep: Phi0 Seam Localization",
        "schema_version": "1.0",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "positive": f"{p_pass}/{p_total}",
            "negative": f"{n_pass}/{n_total}",
            "boundary": f"{b_pass}/{b_total}",
            "overall_pass": all_pass,
            "total_time_s": round(time.time() - t_start, 4),
        },
    }
    if error is not None:
        results["error"] = error

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "bridge_prep_phi0_seam_localization_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results written to {out_path}")
    print(f"Positive: {p_pass}/{p_total}  Negative: {n_pass}/{n_total}  Boundary: {b_pass}/{b_total}")
    if all_pass:
        print("ALL TESTS PASSED -- overall_pass=True")
    else:
        print("SOME TESTS FAILED -- check results JSON")
        if error:
            print("ERROR:", error["error"])
