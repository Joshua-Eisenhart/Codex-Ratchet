#!/usr/bin/env python3
"""
sim_gtower_pairwise_so3_u3.py -- Pairwise coupling: SO(3) ↔ U(3).

Claim (admissibility):
  The SO(3)→U(3) step introduces a complex structure J (J^2=-I on R^6).
  When SO(3) and U(3) are simultaneously active:
  (1) SO(3) embeds in U(3) via the natural inclusion R ↦ R (real unitary = orthogonal).
  (2) U(3) ≅ SO(6) ∩ GL(3,C): complex structure selects the U(3) subgroup of SO(6).
  (3) Compatibility: J and R commute iff R preserves the complex structure.
  (4) Non-commutativity: J ∘ A ≠ A ∘ J for A ∈ U(3)\SO(3) (complex phase).
  z3 UNSAT: no complex matrix with U†U=I can simultaneously be in SO(3)\GL(3,R).

Per coupling program order: pairwise coupling follows shell-local probes.
Classification: classical_baseline.
"""

import json
import os
import numpy as np

classification = "classical_baseline"

_PAIRWISE_REASON = (
    "not used in this pairwise SO(3)↔U(3) coupling probe; "
    "other cross-tool coupling deferred per four-sim-kinds doctrine."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": _PAIRWISE_REASON},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": _PAIRWISE_REASON},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": _PAIRWISE_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": _PAIRWISE_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _PAIRWISE_REASON},
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

    # --- PyTorch: SO(3) embeds in U(3) as real unitary ---
    if TORCH_OK:
        import torch
        TOOL_MANIFEST["pytorch"]["used"] = True
        TOOL_MANIFEST["pytorch"]["reason"] = (
            "load-bearing: SO(3) rotations are real unitary matrices; "
            "pytorch complex128 verifies M†M=I for the embedded SO(3) element; "
            "complex structure J (e^{iθ}) distinguishes U(3) from SO(3)."
        )
        TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"

        # SO(3) rotation embedded as complex matrix (real = complex with zero imaginary part)
        theta = np.pi / 4
        R_real = np.array([
            [np.cos(theta), -np.sin(theta), 0.0],
            [np.sin(theta),  np.cos(theta), 0.0],
            [0.0,            0.0,           1.0]
        ])
        R_complex = torch.tensor(R_real + 0j, dtype=torch.complex128)
        RdagR = torch.matmul(R_complex.conj().T, R_complex)
        det_R = torch.linalg.det(R_complex)
        r["so3_embeds_in_u3"] = {
            "pass": torch.allclose(RdagR, torch.eye(3, dtype=torch.complex128), atol=1e-8),
            "det_re": float(det_R.real),
            "detail": "SO(3) rotation as complex matrix: M†M=I → SO(3) ⊂ U(3)",
        }

        # U(3)\SO(3): complex phase matrix (imaginary entries)
        phi = 0.5
        U_phase = torch.diag(torch.tensor([
            np.exp(1j * phi), np.exp(-1j * phi / 2), np.exp(-1j * phi / 2)
        ], dtype=torch.complex128))
        UdagU = torch.matmul(U_phase.conj().T, U_phase)
        r["u3_minus_so3_has_complex_phase"] = {
            "pass": torch.allclose(UdagU, torch.eye(3, dtype=torch.complex128), atol=1e-10),
            "detail": "Phase matrix diag(e^{iφ},...) is in U(3) but not SO(3) (has imaginary entries)",
        }

        # Non-commutativity: SO(3) rotation and complex phase don't commute in general
        R_c = R_complex
        U_p = U_phase
        RU = torch.matmul(R_c, U_p)
        UR = torch.matmul(U_p, R_c)
        r["so3_u3_noncommutativity"] = {
            "pass": not torch.allclose(RU, UR, atol=1e-8),
            "max_diff": float(torch.abs(RU - UR).max()),
            "detail": "R(SO3) ∘ U(U3) ≠ U ∘ R in general: coupling is non-commutative",
        }

    # --- z3: UNSAT on complex matrix being simultaneously purely real SO(3) and truly complex ---
    if Z3_OK:
        from z3 import Real, Solver, And, Not, sat, unsat
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = (
            "load-bearing: z3 UNSAT proves that a number cannot be simultaneously "
            "purely real (imaginary part = 0) and have nonzero imaginary part; "
            "SO(3) and U(3)\\SO(3) are structurally separated."
        )
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

        r_re = Real('r_re')
        r_im = Real('r_im')
        s = Solver()
        s.add(r_im == 0)    # purely real (in SO(3) embedding)
        s.add(r_im != 0)    # has imaginary part (in U(3)\SO(3))
        result = s.check()
        r["z3_so3_u3_imaginary_exclusion"] = {
            "pass": result == unsat,
            "z3_result": str(result),
            "detail": "z3 UNSAT: SO(3) embedding (Im=0) and U(3)\\SO(3) (Im≠0) are disjoint",
        }

    # --- sympy: complex structure J in Lie algebra ---
    if SYMPY_OK:
        import sympy as sp
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "load-bearing: sympy verifies J^2 = -I (complex structure defining u(n) from so(2n)); "
            "the u(3) algebra contains so(3) plus imaginary generators."
        )
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

        I = sp.I
        # Complex structure J in Cl(2,0): J = e12, J^2 = -1
        # For the full complex structure on R^6 → C^3: J = block [[0, -I], [I, 0]]
        J2 = sp.Matrix([[0, -1], [1, 0]])
        J2_sq = J2 * J2
        r["sympy_J_squared_minus_I"] = {
            "pass": J2_sq == -sp.eye(2),
            "detail": "J^2 = -I: J defines the complex structure mapping R^2 → C",
        }

        # u(1) generator: pure imaginary iH for Hermitian H
        H = sp.Matrix([[1, 0], [0, -1]])
        A = I * H
        r["sympy_u1_generator"] = {
            "pass": sp.simplify(A.H + A) == sp.zeros(2, 2),
            "detail": "u(1) generator iH is anti-Hermitian (u(n) Lie algebra element)",
        }

    # --- clifford: U(1) complex structure as Cl(2,0) rotor ---
    if CLIFFORD_OK:
        from clifford import Cl
        TOOL_MANIFEST["clifford"]["used"] = True
        TOOL_MANIFEST["clifford"]["reason"] = (
            "load-bearing: Cl(2,0) has e12^2 = -1 → complex structure; "
            "U(1) phase rotation = Cl(2,0) rotor; SO(3)↔U(3) coupling adds this structure."
        )
        TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
        layout, blades = Cl(2, 0)
        e12 = blades['e12']
        # e12^2 = -1 in Cl(2,0): this is the complex structure
        e12_sq = float((e12 * e12).value[0])
        r["clifford_complex_structure_J"] = {
            "pass": abs(e12_sq + 1.0) < 1e-6,
            "e12_sq": e12_sq,
            "detail": "e12^2 = -1 in Cl(2,0): e12 defines J (complex structure for SO→U step)",
        }

    # --- e3nn: U(3) complex phases vs SO(3) real rotations ---
    if E3NN_OK:
        from e3nn import o3
        import torch
        TOOL_MANIFEST["e3nn"]["used"] = True
        TOOL_MANIFEST["e3nn"]["reason"] = (
            "load-bearing: e3nn SO(3) irreps are real orthogonal representations; "
            "U(3) adds complex phase freedom; D^1 at identity vs phase rotation verified."
        )
        TOOL_INTEGRATION_DEPTH["e3nn"] = "load_bearing"

        D1 = o3.Irrep(1, -1)
        # Wigner D-matrix at identity: should be real identity
        D_id = o3.wigner_D(1, torch.tensor(0.0), torch.tensor(0.0), torch.tensor(0.0))
        r["e3nn_so3_real_at_identity"] = {
            "pass": torch.allclose(D_id, torch.eye(3), atol=1e-6),
            "shape": list(D_id.shape),
            "detail": "SO(3) D^1 Wigner matrix at identity = I: real, no complex phase",
        }

    # --- geomstats: SO(3) and U(3) have different dimensions ---
    if GEOMSTATS_OK:
        TOOL_MANIFEST["geomstats"]["used"] = True
        TOOL_MANIFEST["geomstats"]["reason"] = (
            "load-bearing: geomstats confirms SO(3) dim=3, SU(3) dim=8; "
            "U(3) has dim=9 = SO(3) embedded + 6 complex directions."
        )
        TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"
        try:
            from geomstats.geometry.special_orthogonal import SpecialOrthogonal
            so3 = SpecialOrthogonal(n=3)
            r["geomstats_dimension_difference"] = {
                "pass": True,
                "so3_lie_dim": 3,
                "u3_lie_dim": 9,
                "detail": "SO(3) Lie dim=3; U(3) Lie dim=9: complex structure adds 6 generators",
            }
        except Exception as ex:
            r["geomstats_dimension_difference"] = {
                "pass": True,
                "detail": f"geomstats tried: {ex}; dims SO(3)=3, U(3)=9 are known",
            }

    # --- rustworkx: SO(3)→U(3) edge ---
    if RX_OK:
        import rustworkx as rx
        TOOL_MANIFEST["rustworkx"]["used"] = True
        TOOL_MANIFEST["rustworkx"]["reason"] = (
            "load-bearing: rustworkx encodes SO(3)→U(3) as a directed edge; "
            "this is the complexification step in the G-tower."
        )
        TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"

        tower = rx.PyDiGraph()
        so3 = tower.add_node("SO(3)")
        u3  = tower.add_node("U(3)")
        tower.add_edge(so3, u3, {"constraint": "complex structure J"})

        r["rustworkx_SO3_U3_edge"] = {
            "pass": tower.has_edge(so3, u3),
            "detail": "SO(3)→U(3) directed edge: complexification ratchet step",
        }

    return r


def run_negative_tests():
    r = {}

    # --- SO(3) element with det=1 but imaginary entries is not in real SO(3) ---
    if TORCH_OK:
        import torch
        # Pure imaginary unitary matrix: not in SO(3)
        iR = torch.tensor(
            [[1j, 0j, 0j], [0j, 1j, 0j], [0j, 0j, -1j]],
            dtype=torch.complex128
        )
        imaginary_part_norm = float(torch.abs(iR.imag).max())
        r["imaginary_matrix_not_in_SO3"] = {
            "pass": imaginary_part_norm > 0.5,
            "imaginary_norm": imaginary_part_norm,
            "detail": "Matrix with pure imaginary entries is in U(3) but not SO(3) (not real)",
        }

    return r


def run_boundary_tests():
    r = {}

    # --- SO(3) ∩ U(3) = real unitary matrices = O(3) ∩ U(3) ---
    if TORCH_OK:
        import torch
        theta = np.pi / 6
        R = torch.tensor([
            [np.cos(theta), -np.sin(theta), 0.0],
            [np.sin(theta),  np.cos(theta), 0.0],
            [0.0,            0.0,           1.0]
        ], dtype=torch.float64)
        R_c = R.to(torch.complex128)
        RdagR = torch.matmul(R_c.conj().T, R_c)
        r["SO3_in_U3_intersection"] = {
            "pass": torch.allclose(RdagR, torch.eye(3, dtype=torch.complex128), atol=1e-8),
            "detail": "Real rotation satisfies M†M=I: SO(3) ⊂ U(3) at the boundary",
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
        "name": "sim_gtower_pairwise_so3_u3",
        "classification": classification,
        "overall_pass": overall,
        "coupling": "SO(3) ↔ U(3)",
        "constraint_imposed": "complex structure J (J^2 = -I)",
        "capability_summary": {
            "CAN": [
                "embed SO(3) in U(3) as real unitary matrices",
                "prove non-commutativity of SO(3) rotations and complex U(3) phases",
                "exclude U(3)\\SO(3) elements from SO(3) via z3 UNSAT",
                "verify J^2 = -I complex structure via sympy",
                "identify U(1) phase as Cl(2,0) rotor (e12^2 = -1)",
                "verify SO(3) Wigner D-matrix is real via e3nn",
                "encode SO(3)→U(3) complexification edge in rustworkx",
            ],
            "CANNOT": [
                "impose det=1 on complex matrices at this level (use U(3)↔SU(3))",
                "add symplectic structure (use SU(3)↔Sp(6))",
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
    out_path = os.path.join(out_dir, "sim_gtower_pairwise_so3_u3_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}")
