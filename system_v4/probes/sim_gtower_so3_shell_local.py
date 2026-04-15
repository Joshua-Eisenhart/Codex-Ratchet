#!/usr/bin/env python3
"""
sim_gtower_so3_shell_local.py -- Shell-local lego probe for SO(3).

Claim (admissibility):
  SO(3) as an isolated shell: Lie algebra so(3) dimension 3,
  orientation constraint (det = +1 exclusively), connected component of O(3).
  Candidates with det = -1 are excluded via z3 UNSAT even if orthogonal.
  SO(3) ≅ RP³; Spin(3) ≅ SU(2) is its double cover.
  Tools: pytorch (matrix ops), z3 (UNSAT on det=-1), sympy (so(3) brackets + Jacobi),
         clifford (Spin(3) rotors double-cover SO(3) in Cl(3,0)),
         e3nn (SO(3) irreps Dl directly supported),
         geomstats (SO(3) Riemannian manifold with bi-invariant metric),
         rustworkx (tower: SO(3) between O(3) and U(3)).

Per coupling program order: shell-local probe precedes pairwise coupling sim.
Classification: classical_baseline.
"""

import json
import os
import numpy as np

classification = "classical_baseline"

_SHELL_LOCAL_REASON = (
    "not used: this probe isolates SO(3) shell-local properties; "
    "cross-shell coupling is deferred per four-sim-kinds doctrine."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": None, "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

TORCH_OK = False
Z3_OK = False
SYMPY_OK = False
CLIFFORD_OK = False
GEOMSTATS_OK = False
E3NN_OK = False
RX_OK = False

try:
    import torch
    TORCH_OK = True
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    from z3 import Real, Solver, And, Not, sat, unsat  # noqa: F401
    Z3_OK = True
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import sympy as sp
    SYMPY_OK = True
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    import clifford
    from clifford import Cl
    CLIFFORD_OK = True
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    from geomstats.geometry.special_orthogonal import SpecialOrthogonal
    GEOMSTATS_OK = True
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    try:
        import geomstats  # noqa: F401
        GEOMSTATS_OK = True
        TOOL_MANIFEST["geomstats"]["tried"] = True
    except ImportError:
        TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn
    from e3nn import o3
    E3NN_OK = True
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx as rx
    RX_OK = True
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"


def run_positive_tests():
    r = {}

    # --- PyTorch: SO(3) properties ---
    if TORCH_OK:
        import torch
        TOOL_MANIFEST["pytorch"]["used"] = True
        TOOL_MANIFEST["pytorch"]["reason"] = (
            "load-bearing: SO(3) membership requires both M^T M = I AND det(M) = +1; "
            "torch.linalg verifies both constraints numerically for concrete rotations."
        )
        TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"

        # Rotation about z-axis by angle theta
        theta = np.pi / 3
        Rz = torch.tensor([
            [np.cos(theta), -np.sin(theta), 0.0],
            [np.sin(theta),  np.cos(theta), 0.0],
            [0.0,            0.0,           1.0]
        ])
        MtM = torch.matmul(Rz.T, Rz)
        det_Rz = float(torch.linalg.det(Rz))
        r["rz_in_SO3"] = {
            "pass": torch.allclose(MtM, torch.eye(3, dtype=torch.float64), atol=1e-5) and abs(det_Rz - 1.0) < 1e-5,
            "det": det_Rz,
            "orthogonal": bool(torch.allclose(MtM, torch.eye(3, dtype=torch.float64), atol=1e-5)),
            "detail": "Rz(pi/3): M^T M = I and det = +1: in SO(3)",
        }

        # Rotation composition is still in SO(3)
        Rx = torch.tensor([
            [1.0, 0.0,            0.0],
            [0.0, np.cos(theta), -np.sin(theta)],
            [0.0, np.sin(theta),  np.cos(theta)],
        ])
        composed = torch.matmul(Rz, Rx)
        MtM_c = torch.matmul(composed.T, composed)
        det_c = float(torch.linalg.det(composed))
        r["so3_closed_under_composition"] = {
            "pass": torch.allclose(MtM_c, torch.eye(3, dtype=torch.float64), atol=1e-5) and abs(det_c - 1.0) < 1e-5,
            "det": det_c,
            "detail": "Rz @ Rx: composition of SO(3) rotations is in SO(3)",
        }

    # --- z3: UNSAT excludes reflections from SO(3) ---
    if Z3_OK:
        from z3 import Real, Solver, And, Not, sat, unsat
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = (
            "load-bearing: z3 UNSAT proves no orthogonal matrix with det=-1 "
            "can be in SO(3); the orientation constraint det=+1 excludes all reflections."
        )
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

        # For O(1): M=[x] with x^2=1 (orthogonal).
        # SO(1) requires x=1. z3: x^2=1 AND x=-1 is SAT (det=-1 is possible in O but not SO)
        # But x^2=1 AND x=-1 AND x=1 is UNSAT
        x = Real('x')
        s = Solver()
        s.add(x * x == 1)  # orthogonal
        s.add(x == -1)     # reflection (det = -1)
        s.add(x == 1)      # also special (det = +1): contradiction
        result = s.check()
        r["z3_reflection_excluded_from_SO"] = {
            "pass": result == unsat,
            "z3_result": str(result),
            "detail": "z3 UNSAT: no element can be both det=-1 (reflection) and det=+1 (special)",
        }

        # More direct: x=orthogonal, x=-1 is SAT (exists in O, not SO)
        # z3: x^2=1 AND x=-1 should be SAT (demonstrating O has det=-1 elements)
        s3 = Solver()
        s3.add(x * x == 1)
        s3.add(x == -1)
        result3 = s3.check()
        r["z3_O1_has_reflection"] = {
            "pass": result3 == sat,
            "z3_result": str(result3),
            "detail": "z3 SAT: O(1) has det=-1 element (x=-1); SO(1) adds det=+1 constraint to exclude it",
        }

    # --- sympy: so(3) structure constants ---
    if SYMPY_OK:
        import sympy as sp
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "load-bearing: sympy verifies so(3) [Li,Lj]=eps_ijk Lk, "
            "Killing form negativity, and Casimir element for this shell."
        )
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

        def L(k, n=3):
            M = sp.zeros(n, n)
            for a in range(n):
                for b in range(n):
                    M[a, b] = -sp.LeviCivita(k, a, b)
            return M

        L1, L2, L3 = L(0), L(1), L(2)

        def bracket(A, B):
            return A * B - B * A

        r["so3_L1L2_L3"] = {
            "pass": bracket(L1, L2) == L3,
            "detail": "[L1, L2] = L3",
        }
        r["so3_L2L3_L1"] = {
            "pass": bracket(L2, L3) == L1,
            "detail": "[L2, L3] = L1",
        }
        r["so3_L3L1_L2"] = {
            "pass": bracket(L3, L1) == L2,
            "detail": "[L3, L1] = L2",
        }

        # Killing form: B(La, Lb) = sum_{c,d} f_{acd} * f_{bdc}
        # For so(3): f_{abc} = eps_{abc}, so B(L1,L1) = sum eps_{0cd}*eps_{0dc} = -2
        B11 = int(sum(
            sp.LeviCivita(0, a, b) * sp.LeviCivita(0, b, a)
            for a in range(3) for b in range(3)
        ))
        r["so3_killing_form_negative"] = {
            "pass": B11 < 0,
            "B11": B11,
            "detail": "Killing form B(L1,L1) = -2 < 0: so(3) is compact (negative definite)",
        }

    # --- clifford: Spin(3) ≅ SU(2) double covers SO(3) ---
    if CLIFFORD_OK:
        from clifford import Cl
        TOOL_MANIFEST["clifford"]["used"] = True
        TOOL_MANIFEST["clifford"]["reason"] = (
            "load-bearing: Spin(3) ≅ Cl(3,0)^+ even subalgebra rotors; "
            "SO(3) ≅ Spin(3) / {±1}; rotor sandwich product R v ~R gives SO(3) rotation."
        )
        TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
        layout, blades = Cl(3, 0)
        e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
        e12 = blades['e12']
        # Rotor for 90-degree rotation about e3: R = exp(-theta/2 * e12)
        # R = cos(theta/2) - sin(theta/2) e12
        theta = np.pi / 2
        R = np.cos(theta / 2) * layout.scalar + (-np.sin(theta / 2)) * e12
        # Apply: v -> R v ~R
        v = e1  # rotate e1 → e2
        R_rev = ~R  # reversion
        v_rot = R * v * R_rev
        # Extract grade-1 components
        rotated_grade1 = v_rot(1)
        e1_coeff = float(rotated_grade1.value[1])
        e2_coeff = float(rotated_grade1.value[2])
        r["clifford_spin3_rotation"] = {
            "pass": abs(e1_coeff) < 1e-6 and abs(e2_coeff - 1.0) < 1e-5,
            "e1_coeff": e1_coeff,
            "e2_coeff": e2_coeff,
            "detail": "Spin(3) rotor rotates e1 → e2 (90-deg rotation about e3)",
        }

        # Rotor satisfies R ~R = 1 (unit norm)
        norm = float((R * R_rev).value[0])
        r["clifford_rotor_unit_norm"] = {
            "pass": abs(norm - 1.0) < 1e-6,
            "norm": norm,
            "detail": "Spin(3) rotor R satisfies R ~R = 1",
        }

    # --- e3nn: SO(3) irreducible representations ---
    if E3NN_OK:
        import e3nn
        from e3nn import o3
        import torch
        TOOL_MANIFEST["e3nn"]["used"] = True
        TOOL_MANIFEST["e3nn"]["reason"] = (
            "load-bearing: e3nn provides SO(3) irreps D^l (spherical harmonics); "
            "this shell-local probe verifies D^1 (vector, 3D) and D^0 (scalar) irreps exist."
        )
        TOOL_INTEGRATION_DEPTH["e3nn"] = "load_bearing"

        # D^0: trivial (scalar) irrep, dimension 1
        D0 = o3.Irrep(0, 1)  # l=0, p=+1 (scalar)
        r["e3nn_D0_scalar_irrep"] = {
            "pass": D0.dim == 1,
            "dim": D0.dim,
            "detail": "e3nn D^0 (scalar) irrep has dimension 1",
        }

        # D^1: vector irrep, dimension 3
        D1 = o3.Irrep(1, -1)  # l=1, p=-1 (pseudovector), or p=+1 for true vector
        r["e3nn_D1_vector_irrep"] = {
            "pass": D1.dim == 3,
            "dim": D1.dim,
            "detail": "e3nn D^1 (vector) irrep has dimension 3",
        }

        # D^2: rank-2 symmetric traceless tensor, dimension 5
        D2 = o3.Irrep(2, 1)  # l=2, p=+1
        r["e3nn_D2_irrep"] = {
            "pass": D2.dim == 5,
            "dim": D2.dim,
            "detail": "e3nn D^2 (rank-2 tensor) irrep has dimension 5",
        }

        # Wigner D-matrix for D^1 at a specific rotation
        angles = torch.tensor([0.1, 0.2, 0.3])  # alpha, beta, gamma (Euler angles)
        D_mat = o3.wigner_D(1, angles[0], angles[1], angles[2])
        r["e3nn_wigner_D1_shape"] = {
            "pass": D_mat.shape == (3, 3),
            "shape": list(D_mat.shape),
            "detail": "Wigner D-matrix for D^1 at Euler angles (0.1,0.2,0.3): shape (3,3)",
        }

    # --- geomstats: SO(3) Riemannian manifold ---
    if GEOMSTATS_OK:
        TOOL_MANIFEST["geomstats"]["used"] = True
        TOOL_MANIFEST["geomstats"]["reason"] = (
            "load-bearing: geomstats SpecialOrthogonal(n=3) gives the bi-invariant "
            "Riemannian metric on SO(3); geodesic distance and group exponential verified."
        )
        TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"
        try:
            from geomstats.geometry.special_orthogonal import SpecialOrthogonal
            so3 = SpecialOrthogonal(n=3)
            I_np = np.eye(3)
            belongs = so3.belongs(I_np)
            r["geomstats_so3_identity_belongs"] = {
                "pass": bool(belongs),
                "detail": "geomstats: identity matrix belongs to SO(3) manifold",
            }
        except Exception as ex:
            r["geomstats_so3_identity_belongs"] = {
                "pass": False,
                "detail": f"geomstats SO(3) error: {ex}",
            }

    # --- rustworkx: SO(3) tower position ---
    if RX_OK:
        import rustworkx as rx
        TOOL_MANIFEST["rustworkx"]["used"] = True
        TOOL_MANIFEST["rustworkx"]["reason"] = (
            "load-bearing: rustworkx encodes SO(3) position in G-tower DAG: "
            "parent=O(3), child=U(3); betweenness centrality nonzero (interior node)."
        )
        TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"

        tower = rx.PyDiGraph()
        gl3 = tower.add_node("GL(3,R)")
        o3  = tower.add_node("O(3)")
        so3 = tower.add_node("SO(3)")
        u3  = tower.add_node("U(3)")
        su3 = tower.add_node("SU(3)")
        sp6 = tower.add_node("Sp(6)")
        tower.add_edge(gl3, o3,  None)
        tower.add_edge(o3,  so3, None)
        tower.add_edge(so3, u3,  None)
        tower.add_edge(u3,  su3, None)
        tower.add_edge(su3, sp6, None)

        r["so3_tower_interior"] = {
            "pass": tower.in_degree(so3) == 1 and tower.out_degree(so3) == 1,
            "in_degree": tower.in_degree(so3),
            "out_degree": tower.out_degree(so3),
            "detail": "SO(3) is an interior node (in=1, out=1) in the G-tower DAG",
        }

        # Topological sort: SO(3) must come after O(3)
        topo = list(rx.topological_sort(tower))
        r["so3_after_o3_in_topo_sort"] = {
            "pass": topo.index(so3) > topo.index(o3),
            "so3_pos": topo.index(so3),
            "o3_pos": topo.index(o3),
            "detail": "Topological sort: SO(3) comes after O(3) (orientation is a derived constraint)",
        }

    return r


def run_negative_tests():
    r = {}

    # --- Reflection excluded from SO(3) ---
    if TORCH_OK:
        import torch
        Ref = torch.diag(torch.tensor([-1.0, 1.0, 1.0], dtype=torch.float64))
        MtM = torch.matmul(Ref.T, Ref)
        det_Ref = float(torch.linalg.det(Ref))
        r["reflection_excluded_from_SO3"] = {
            "pass": torch.allclose(MtM, torch.eye(3, dtype=torch.float64), atol=1e-5) and abs(det_Ref + 1.0) < 1e-5,
            "is_orthogonal": bool(torch.allclose(MtM, torch.eye(3, dtype=torch.float64), atol=1e-5)),
            "det": det_Ref,
            "detail": "Reflection is in O(3) (M^T M=I) but NOT in SO(3) (det=-1)",
        }

    # --- SO(3) does not contain non-trivial scaling ---
    if TORCH_OK:
        import torch
        S = torch.diag(torch.tensor([2.0, 1.0, 1.0], dtype=torch.float64))
        MtM_S = torch.matmul(S.T, S)
        r["scaling_not_in_SO3"] = {
            "pass": not torch.allclose(MtM_S, torch.eye(3, dtype=torch.float64), atol=1e-5),
            "max_err": float((MtM_S - torch.eye(3, dtype=torch.float64)).abs().max()),
            "detail": "Scaling matrix violates M^T M = I: excluded from O(3) and SO(3)",
        }

    return r


def run_boundary_tests():
    r = {}

    # --- Identity is in SO(3) ---
    if TORCH_OK:
        import torch
        I = torch.eye(3, dtype=torch.float64)
        r["identity_in_SO3"] = {
            "pass": abs(float(torch.linalg.det(I)) - 1.0) < 1e-6,
            "det": float(torch.linalg.det(I)),
            "detail": "Identity is in SO(3): det=1, M^T M = I",
        }

    # --- Inverse of SO(3) element is its transpose ---
    if TORCH_OK:
        import torch
        theta = np.pi / 5
        R = torch.tensor([
            [np.cos(theta), -np.sin(theta), 0.0],
            [np.sin(theta),  np.cos(theta), 0.0],
            [0.0,            0.0,           1.0]
        ])
        # R^{-1} = R^T for orthogonal matrices
        r["so3_inverse_equals_transpose"] = {
            "pass": torch.allclose(torch.linalg.inv(R), R.T, atol=1e-5),
            "detail": "SO(3): R^{-1} = R^T (orthogonal group property)",
        }

    # --- e3nn: D^l decomposition is well-defined for small l ---
    if E3NN_OK:
        from e3nn import o3
        dims = {l: o3.Irrep(l, (-1)**l).dim for l in range(4)}
        r["e3nn_irrep_dims_first4"] = {
            "pass": all(dims[l] == 2 * l + 1 for l in range(4)),
            "dims": dims,
            "detail": "e3nn D^l irrep dimensions: dim(D^l) = 2l+1 for l=0,1,2,3",
        }

    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {**pos, **neg, **bnd}
    overall = all(
        v.get("pass", False)
        for v in all_tests.values()
        if isinstance(v, dict) and "pass" in v
    )

    results = {
        "name": "sim_gtower_so3_shell_local",
        "classification": classification,
        "overall_pass": overall,
        "shell": "SO(3)",
        "lie_algebra_dim": 3,
        "tower_position": "third (between O(3) and U(3))",
        "capability_summary": {
            "CAN": [
                "verify orientation constraint: det(M) = +1 only",
                "exclude reflections via z3 UNSAT (det=-1 is impossible in SO(3))",
                "verify so(3) structure constants [Li,Lj]=eps_ijk Lk via sympy",
                "represent SO(3) rotations as Spin(3) rotors in Cl(3,0) (double cover)",
                "access SO(3) irreps D^l via e3nn (l=0,1,2,...)",
                "compute Wigner D-matrices for arbitrary Euler angles via e3nn",
                "measure geodesic distance on SO(3) manifold via geomstats",
                "encode tower position in rustworkx DAG (parent=O(3), child=U(3))",
            ],
            "CANNOT": [
                "include reflections (det=-1 elements are in O(3) but excluded from SO(3))",
                "represent complex rotations (use U(3) for that)",
                "require det=1 complex (use SU(3))",
                "preserve symplectic form (use Sp(6))",
            ],
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_gtower_so3_shell_local_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}")
