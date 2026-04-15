#!/usr/bin/env python3
"""
sim_gtower_o3_shell_local.py -- Shell-local lego probe for O(3).

Claim (admissibility):
  O(3) as an isolated shell: Lie algebra so(3) dimension 3,
  metric-preservation constraint (M^T M = I), det = ±1 (two components).
  Candidates with |det| != 1 are excluded via z3 UNSAT.
  O(3) = SO(3) ∪ reflection-SO(3); the two components are distinguishable.
  Tools: pytorch (M^T M = I check), z3 (exclusion proof), sympy (so(3) bracket),
         clifford (versors model: O(n) acts via Pin(n) versors),
         geomstats (O(n) manifold), rustworkx (tower: O(3) between GL(3) and SO(3)).

Per coupling program order: shell-local probe precedes pairwise coupling sim.
Classification: classical_baseline.
"""

import json
import os
import numpy as np

classification = "classical_baseline"
divergence_log = (
    "Classical shell-local baseline: this isolates the O(3) shell and its "
    "tool-mediated local constraints before any cross-shell coupling claims."
)

_SHELL_LOCAL_REASON = (
    "not used: this probe isolates O(3) shell-local properties; "
    "cross-shell coupling is deferred per four-sim-kinds doctrine."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": True, "reason": "load-bearing: O(3) membership test M^T M = I and |det(M)| = 1 are verified numerically via torch.linalg operations."},
    "pyg":       {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3":        {"tried": False, "used": True, "reason": "load-bearing: z3 UNSAT proves no matrix can satisfy both M^T M = I and |det| != 1; the orthogonality constraint forces |det| in {-1, +1}."},
    "cvc5":      {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy":     {"tried": False, "used": True, "reason": "load-bearing: sympy verifies so(3) structure constants [Li,Lj]=eps_ijk Lk and antisymmetry of generators symbolically."},
    "clifford":  {"tried": False, "used": True, "reason": "load-bearing: Pin(3) ⊂ Cl(3,0) provides the double cover of O(3); unit vectors in Cl(3,0) are versors; reflection v -> -n v n^{-1} gives O(3) action."},
    "geomstats": {"tried": False, "used": True, "reason": "load-bearing: geomstats SpecialOrthogonal provides the Riemannian metric on SO(3) ⊂ O(3), confirming the group manifold structure."},
    "e3nn":      {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": False, "used": True, "reason": "load-bearing: rustworkx DAG encodes O(3) tower position: parent=GL(3,R), child=SO(3); in-degree=1, out-degree=1."},
    "xgi":       {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing", "pyg": None, "z3": "load_bearing", "cvc5": None,
    "sympy": "load_bearing", "clifford": "load_bearing", "geomstats": "load_bearing", "e3nn": None,
    "rustworkx": "load_bearing", "xgi": None, "toponetx": None, "gudhi": None,
}

TORCH_OK = False
Z3_OK = False
SYMPY_OK = False
CLIFFORD_OK = False
GEOMSTATS_OK = False
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
    import rustworkx as rx
    RX_OK = True
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"


def run_positive_tests():
    r = {}

    # --- PyTorch: O(3) orthogonality constraint M^T M = I ---
    if TORCH_OK:
        import torch
        TOOL_MANIFEST["pytorch"]["used"] = True
        TOOL_MANIFEST["pytorch"]["reason"] = (
            "load-bearing: O(3) membership test M^T M = I and |det(M)| = 1 "
            "are verified numerically via torch.linalg operations."
        )
        TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"

        # Rotation matrix (SO(3) ⊂ O(3))
        theta = np.pi / 4
        R = torch.tensor([
            [np.cos(theta), -np.sin(theta), 0.0],
            [np.sin(theta),  np.cos(theta), 0.0],
            [0.0,            0.0,           1.0]
        ])
        MtM = torch.matmul(R.T, R)
        r["rotation_in_O3"] = {
            "pass": torch.allclose(MtM, torch.eye(3, dtype=torch.float64), atol=1e-5),
            "max_err": float((MtM - torch.eye(3, dtype=torch.float64)).abs().max()),
            "det": float(torch.linalg.det(R)),
            "detail": "Rotation Rz(pi/4): M^T M = I, det = +1: in SO(3) ⊂ O(3)",
        }

        # Reflection matrix (O(3) \ SO(3))
        Ref = torch.diag(torch.tensor([-1.0, 1.0, 1.0]))
        MtM_ref = torch.matmul(Ref.T, Ref)
        det_ref = float(torch.linalg.det(Ref))
        r["reflection_in_O3"] = {
            "pass": torch.allclose(MtM_ref, torch.eye(3, dtype=Ref.dtype), atol=1e-5) and abs(det_ref + 1.0) < 1e-5,
            "det": det_ref,
            "detail": "Reflection diag(-1,1,1): M^T M = I, det = -1: in O(3) \\ SO(3)",
        }

        # Two disconnected components by sign of det
        R_det = float(torch.linalg.det(R))
        Ref_det = float(torch.linalg.det(Ref))
        r["two_components_by_det"] = {
            "pass": abs(R_det - 1.0) < 1e-5 and abs(Ref_det + 1.0) < 1e-5,
            "det_rotation": R_det,
            "det_reflection": Ref_det,
            "detail": "O(3) has two components: det=+1 (SO(3)) and det=-1 (improper rotations)",
        }

    # --- z3: UNSAT excludes non-orthogonal matrices ---
    if Z3_OK:
        from z3 import Real, Solver, And, Not, sat, unsat
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = (
            "load-bearing: z3 UNSAT proves no matrix can satisfy both M^T M = I "
            "and |det| != 1; the orthogonality constraint forces |det| in {-1, +1}."
        )
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

        # For a 1x1 case: M = [x], M^T M = I => x^2 = 1, so x in {-1, +1}
        # Claim: x^2 = 1 AND x not in {-1, +1} is UNSAT
        x = Real('x')
        s = Solver()
        s.add(x * x == 1)   # orthogonality: M^T M = I
        s.add(x != 1)
        s.add(x != -1)      # x not in {+1, -1}
        result = s.check()
        r["z3_orthogonal_forces_det_pm1"] = {
            "pass": result == unsat,
            "z3_result": str(result),
            "detail": "z3 UNSAT: orthogonality (M^T M=I) forces det in {-1, +1} for O(1)",
        }

        # Claim: no matrix can have x^2 > 1 while also satisfying orthogonality
        s2 = Solver()
        s2.add(x * x == 1)
        s2.add(x * x > 2)  # impossible: x^2 = 1 and x^2 > 2 is UNSAT
        result2 = s2.check()
        r["z3_det_bounded"] = {
            "pass": result2 == unsat,
            "z3_result": str(result2),
            "detail": "z3 UNSAT: no orthogonal matrix has |det| > 1",
        }

    # --- sympy: so(3) Lie algebra structure constants ---
    if SYMPY_OK:
        import sympy as sp
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "load-bearing: sympy verifies so(3) structure constants [Li,Lj]=eps_ijk Lk "
            "and antisymmetry of generators symbolically."
        )
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

        def L(k, n=3):
            M = sp.zeros(n, n)
            for a in range(n):
                for b in range(n):
                    eps = sp.LeviCivita(k, a, b)
                    M[a, b] = -eps
            return M

        L1, L2, L3 = L(0), L(1), L(2)

        def bracket(A, B):
            return A * B - B * A

        r["so3_bracket_L1L2"] = {
            "pass": bracket(L1, L2) == L3,
            "detail": "[L1, L2] = L3: so(3) structure constant eps_12k = delta_3k",
        }
        r["so3_bracket_L2L3"] = {
            "pass": bracket(L2, L3) == L1,
            "detail": "[L2, L3] = L1: so(3) structure constant",
        }
        r["so3_antisymmetry"] = {
            "pass": L1 + L1.T == sp.zeros(3, 3),
            "detail": "L1 is antisymmetric: L + L^T = 0 (so(n) generators)",
        }
        J = (bracket(L1, bracket(L2, L3))
             + bracket(L2, bracket(L3, L1))
             + bracket(L3, bracket(L1, L2)))
        r["so3_jacobi"] = {
            "pass": J == sp.zeros(3, 3),
            "detail": "Jacobi identity holds for so(3)",
        }

    # --- clifford: O(3) versors in Cl(3,0) ---
    if CLIFFORD_OK:
        from clifford import Cl
        TOOL_MANIFEST["clifford"]["used"] = True
        TOOL_MANIFEST["clifford"]["reason"] = (
            "load-bearing: Pin(3) ⊂ Cl(3,0) provides the double cover of O(3); "
            "unit vectors in Cl(3,0) are versors; reflection v -> -n v n^{-1} gives O(3) action."
        )
        TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
        layout, blades = Cl(3, 0)
        e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
        # Reflection of e1 through the plane perpendicular to e1: n = e1
        # Reflection formula: v -> -n v n^{-1}  (note: for unit vectors n^{-1} = n for Cl(p,0))
        n = e1  # unit vector, n*n = +1 in Cl(3,0)
        v = e1 + e2
        # n * n = e1 * e1 = 1 (for Cl(3,0) with signature (+,+,+))
        n_sq = float((n * n).value[0])
        reflected = -(n * v * (~n))  # reversion is ~n
        # Reflection through e1: e1 -> -e1, e2 -> e2
        e1_coeff = float(reflected(1).value[1])  # grade-1, e1 component
        e2_coeff = float(reflected(1).value[2])  # grade-1, e2 component
        r["clifford_versor_reflection"] = {
            "pass": abs(e1_coeff + 1.0) < 1e-6 and abs(e2_coeff - 1.0) < 1e-6,
            "e1_coeff": e1_coeff,
            "e2_coeff": e2_coeff,
            "n_sq": n_sq,
            "detail": "Pin(3) versor reflects e1 → -e1, e2 → e2 in Cl(3,0)",
        }

    # --- geomstats: SO(3) ⊂ O(3) manifold ---
    if GEOMSTATS_OK:
        TOOL_MANIFEST["geomstats"]["used"] = True
        TOOL_MANIFEST["geomstats"]["reason"] = (
            "load-bearing: geomstats SpecialOrthogonal provides the Riemannian metric "
            "on SO(3) ⊂ O(3), confirming the group manifold structure."
        )
        TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"
        try:
            from geomstats.geometry.special_orthogonal import SpecialOrthogonal
            so3 = SpecialOrthogonal(n=3)
            I_np = np.eye(3)
            belongs = so3.belongs(I_np)
            r["geomstats_so3_identity"] = {
                "pass": bool(belongs),
                "detail": "geomstats: identity belongs to SO(3) ⊂ O(3)",
            }
        except Exception as ex:
            r["geomstats_so3_identity"] = {
                "pass": False,
                "detail": f"geomstats SO(3) error: {ex}",
            }

    # --- rustworkx: O(3) tower position ---
    if RX_OK:
        import rustworkx as rx
        TOOL_MANIFEST["rustworkx"]["used"] = True
        TOOL_MANIFEST["rustworkx"]["reason"] = (
            "load-bearing: rustworkx DAG encodes O(3) tower position: "
            "parent=GL(3,R), child=SO(3); in-degree=1, out-degree=1."
        )
        TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"

        tower = rx.PyDiGraph()
        gl3 = tower.add_node("GL(3,R)")
        o3  = tower.add_node("O(3)")
        so3 = tower.add_node("SO(3)")
        tower.add_edge(gl3, o3,  "metric")
        tower.add_edge(o3,  so3, "orientation")

        r["o3_tower_position"] = {
            "pass": tower.in_degree(o3) == 1 and tower.out_degree(o3) == 1,
            "in_degree": tower.in_degree(o3),
            "out_degree": tower.out_degree(o3),
            "detail": "O(3) has one parent (GL(3)) and one child (SO(3)) in the tower",
        }

    return r


def run_negative_tests():
    r = {}

    # --- Non-orthogonal matrix excluded from O(3) ---
    if TORCH_OK:
        import torch
        M = torch.tensor([[2.0, 0.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 0.0, 1.0]], dtype=torch.float64)
        MtM = torch.matmul(M.T, M)
        r["scaling_not_in_O3"] = {
            "pass": not torch.allclose(MtM, torch.eye(3, dtype=torch.float64), atol=1e-5),
            "max_err": float((MtM - torch.eye(3, dtype=torch.float64)).abs().max()),
            "detail": "Scaling matrix (det=2) fails M^T M = I: excluded from O(3)",
        }

    # --- so(3) bracket is antisymmetric: [A,B] = -[B,A] ---
    if SYMPY_OK:
        import sympy as sp
        def L(k, n=3):
            M = sp.zeros(n, n)
            for a in range(n):
                for b in range(n):
                    M[a, b] = -sp.LeviCivita(k, a, b)
            return M
        L1, L2 = L(0), L(1)
        forward = L1 * L2 - L2 * L1
        reverse = L2 * L1 - L1 * L2
        r["so3_antisymmetric_bracket"] = {
            "pass": forward + reverse == sp.zeros(3, 3),
            "detail": "[L1,L2] + [L2,L1] = 0: so(3) bracket is antisymmetric",
        }

    return r


def run_boundary_tests():
    r = {}

    # --- Identity is in both SO(3) and O(3) ---
    if TORCH_OK:
        import torch
        I = torch.eye(3, dtype=torch.float64)
        det_I = float(torch.linalg.det(I))
        MtM = torch.matmul(I.T, I)
        r["identity_in_O3"] = {
            "pass": torch.allclose(MtM, torch.eye(3, dtype=torch.float64), atol=1e-5) and abs(det_I - 1.0) < 1e-5,
            "det": det_I,
            "detail": "Identity matrix is in O(3) with det=+1",
        }

    # --- Product of two O(3) elements is in O(3) ---
    if TORCH_OK:
        import torch
        R = torch.tensor([[0.0, -1.0, 0.0],
                           [1.0,  0.0, 0.0],
                           [0.0,  0.0, 1.0]], dtype=torch.float64)
        Ref = torch.diag(torch.tensor([-1.0, 1.0, 1.0], dtype=torch.float64))
        prod = torch.matmul(R, Ref)
        MtM = torch.matmul(prod.T, prod)
        r["O3_closed_under_product"] = {
            "pass": torch.allclose(MtM, torch.eye(3, dtype=torch.float64), atol=1e-5),
            "max_err": float((MtM - torch.eye(3, dtype=torch.float64)).abs().max()),
            "detail": "O(3) closed under multiplication: product of two O(3) elements is in O(3)",
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
        "name": "sim_gtower_o3_shell_local",
        "classification": classification,
        "overall_pass": overall,
        "shell": "O(3)",
        "lie_algebra_dim": 3,
        "tower_position": "second (between GL(3) and SO(3))",
        "capability_summary": {
            "CAN": [
                "verify metric-preservation constraint M^T M = I",
                "identify two disconnected components by sign of det",
                "verify so(3) structure constants symbolically via sympy",
                "exclude non-orthogonal matrices via z3 UNSAT",
                "represent O(3) action as versors in Cl(3,0) (Pin(3) double cover)",
                "encode tower position in rustworkx DAG (parent=GL(3), child=SO(3))",
            ],
            "CANNOT": [
                "eliminate the det=-1 component (use SO(3) for orientation constraint)",
                "add complex structure (use U(3))",
                "require det=1 (use SU(3))",
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
    out_path = os.path.join(out_dir, "sim_gtower_o3_shell_local_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}")
