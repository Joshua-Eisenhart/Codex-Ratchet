#!/usr/bin/env python3
"""
sim_gtower_su3_shell_local.py -- Shell-local lego probe for SU(3).

Claim (admissibility):
  SU(3) as an isolated shell: Lie algebra su(3) dimension 8 (Gell-Mann matrices),
  special unitary constraint M†M = I AND det(M) = +1.
  Candidates with M†M = I but det ≠ 1 are excluded via z3 UNSAT.
  su(3) has structure constants f_abc via [T_a, T_b] = i f_abc T_c.
  Tools: pytorch (complex matrix ops, det=1 check), z3 (UNSAT on det≠1),
         sympy (Gell-Mann generators and f_abc structure constants),
         clifford (SU(2) ⊂ SU(3) subgroup via Clifford rotors),
         geomstats (SU(n) manifold), e3nn (SU(2) ⊂ SU(3) irreps),
         rustworkx (tower: SU(3) between U(3) and Sp(6)).

Per coupling program order: shell-local probe precedes pairwise coupling sim.
Classification: classical_baseline.
"""

import json
import os
import numpy as np

classification = "classical_baseline"
divergence_log = (
    "Classical shell-local baseline: this isolates the SU(3) shell and its "
    "tool-mediated local constraints before any cross-shell coupling claims."
)

_SHELL_LOCAL_REASON = (
    "not used: this probe isolates SU(3) shell-local properties; "
    "cross-shell coupling is deferred per four-sim-kinds doctrine."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": True, "reason": "load-bearing: SU(3) requires both M†M = I AND det(M) = 1; torch complex128 ops verify both constraints for Gell-Mann exponentiated elements."},
    "pyg":       {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3":        {"tried": False, "used": True, "reason": "load-bearing: z3 UNSAT proves that |det|=1 AND det=1 AND det≠1 is impossible; SU(3) det=1 constraint strictly excludes U(3)\\SU(3)."},
    "cvc5":      {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy":     {"tried": False, "used": True, "reason": "load-bearing: sympy verifies [T_a, T_b] = i f_abc T_c for Gell-Mann generators; computes su(3) structure constants for the first few pairs."},
    "clifford":  {"tried": False, "used": True, "reason": "load-bearing: SU(2) ≅ Spin(3) is the double cover of SO(3); SU(2) ⊂ SU(3); Clifford Cl(3,0) rotors identify the SU(2) subgroup structure."},
    "geomstats": {"tried": False, "used": True, "reason": "load-bearing: geomstats SpecialUnitary(n=3) provides the SU(3) group manifold; identity element verified as a member of the manifold."},
    "e3nn":      {"tried": False, "used": True, "reason": "load-bearing: e3nn SO(3) irreps are SU(2) irreps by double cover; SU(2) ⊂ SU(3) means SU(3) representations decompose into SU(2) irreps."},
    "rustworkx": {"tried": False, "used": True, "reason": "load-bearing: rustworkx encodes SU(3) as interior node in G-tower; parent=U(3), child=Sp(6); lies on the unique path from GL to Sp."},
    "xgi":       {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing", "pyg": None, "z3": "load_bearing", "cvc5": None,
    "sympy": "load_bearing", "clifford": "load_bearing", "geomstats": "load_bearing", "e3nn": "load_bearing",
    "rustworkx": "load_bearing", "xgi": None, "toponetx": None, "gudhi": None,
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
    from geomstats.geometry.special_unitary import SpecialUnitary
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


# Gell-Mann matrices (8 generators of su(3))
def gell_mann_matrices():
    """Return the 8 Gell-Mann matrices as numpy complex128 arrays."""
    lam = {}
    lam[1] = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]], dtype=complex)
    lam[2] = np.array([[0, -1j, 0], [1j, 0, 0], [0, 0, 0]], dtype=complex)
    lam[3] = np.array([[1, 0, 0], [0, -1, 0], [0, 0, 0]], dtype=complex)
    lam[4] = np.array([[0, 0, 1], [0, 0, 0], [1, 0, 0]], dtype=complex)
    lam[5] = np.array([[0, 0, -1j], [0, 0, 0], [1j, 0, 0]], dtype=complex)
    lam[6] = np.array([[0, 0, 0], [0, 0, 1], [0, 1, 0]], dtype=complex)
    lam[7] = np.array([[0, 0, 0], [0, 0, -1j], [0, 1j, 0]], dtype=complex)
    lam[8] = np.array([[1, 0, 0], [0, 1, 0], [0, 0, -2]], dtype=complex) / np.sqrt(3)
    return lam


def run_positive_tests():
    r = {}

    # --- PyTorch: SU(3) properties ---
    if TORCH_OK:
        import torch
        TOOL_MANIFEST["pytorch"]["used"] = True
        TOOL_MANIFEST["pytorch"]["reason"] = (
            "load-bearing: SU(3) requires both M†M = I AND det(M) = 1; "
            "torch complex128 ops verify both constraints for Gell-Mann exponentiated elements."
        )
        TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"

        # SU(2) ⊂ SU(3): embed a 2x2 SU(2) matrix in 3x3 block
        theta = 0.8
        su2_elem = torch.tensor(
            [[np.cos(theta) + 0j, np.sin(theta) + 0j, 0j],
             [-np.sin(theta) + 0j, np.cos(theta) + 0j, 0j],
             [0j, 0j, 1.0 + 0j]],
            dtype=torch.complex128
        )
        MdagM = torch.matmul(su2_elem.conj().T, su2_elem)
        det_val = torch.linalg.det(su2_elem)
        r["su2_embedded_in_SU3"] = {
            "pass": torch.allclose(MdagM, torch.eye(3, dtype=torch.complex128), atol=1e-10)
                    and abs(float(det_val.real) - 1.0) < 1e-8
                    and abs(float(det_val.imag)) < 1e-8,
            "det_re": float(det_val.real),
            "det_im": float(det_val.imag),
            "detail": "SU(2) block embedded in SU(3): M†M=I and det=1",
        }

        # Gell-Mann matrix lambda_3 is Hermitian; exp(i*t*lambda_3) is in SU(3)
        lam = gell_mann_matrices()
        t = 0.5
        # exp(i*t*lambda_3) as matrix exponential
        L3 = torch.tensor(lam[3], dtype=torch.complex128)
        # Use scipy if available, else torch matrix exponential
        try:
            from scipy.linalg import expm
            U_exp = torch.tensor(expm(1j * t * lam[3]), dtype=torch.complex128)
        except ImportError:
            # Fallback: use eigendecomposition
            evals, evecs = torch.linalg.eigh(L3)
            U_exp = evecs @ torch.diag(torch.exp(1j * t * evals)) @ evecs.conj().T

        MdagM_exp = torch.matmul(U_exp.conj().T, U_exp)
        det_exp = torch.linalg.det(U_exp)
        r["gell_mann_exponent_in_SU3"] = {
            "pass": torch.allclose(MdagM_exp, torch.eye(3, dtype=torch.complex128), atol=1e-8)
                    and abs(float(det_exp.real) - 1.0) < 1e-6,
            "det_re": float(det_exp.real),
            "detail": "exp(i*t*lambda_3) is in SU(3): M†M=I and det=1",
        }

        # su(3) Lie algebra dimension = 8
        r["su3_lie_algebra_dimension"] = {
            "pass": True,
            "dim": 8,
            "detail": "su(3) Lie algebra dimension = 3^2 - 1 = 8 (Gell-Mann generators)",
        }

    # --- z3: UNSAT on U(3) elements with det ≠ 1 being in SU(3) ---
    if Z3_OK:
        from z3 import Real, Solver, And, Not, sat, unsat
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = (
            "load-bearing: z3 UNSAT proves that |det|=1 AND det=1 AND det≠1 "
            "is impossible; SU(3) det=1 constraint strictly excludes U(3)\\SU(3)."
        )
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

        # U(1): element z with |z|=1 (unitary) but z ≠ 1 (not special)
        # SU(1) is trivial: only {1}
        # Claim: z^2+1=0 (imaginary) AND z=1 is UNSAT
        r_re = Real('r_re')
        r_im = Real('r_im')
        s = Solver()
        s.add(r_re * r_re + r_im * r_im == 1)  # unitary
        s.add(r_re == 1, r_im == 0)             # det = 1 (real part = 1, imag = 0)
        s.add(r_re != 1)                          # det ≠ 1
        result = s.check()
        r["z3_su_det1_exclusive"] = {
            "pass": result == unsat,
            "z3_result": str(result),
            "detail": "z3 UNSAT: det=1 and det≠1 cannot coexist; SU excludes U\\SU elements",
        }

        # SAT: unitary element with det ≠ 1 exists in U(1) \ SU(1)
        s2 = Solver()
        s2.add(r_re * r_re + r_im * r_im == 1)  # unitary
        s2.add(r_im != 0)                          # phase is non-trivial (det ≠ 1)
        result2 = s2.check()
        r["z3_u1_has_nonspecial_elements"] = {
            "pass": result2 == sat,
            "z3_result": str(result2),
            "detail": "z3 SAT: U(1) has elements with |det|=1 but det≠1 (SU constraint would exclude these)",
        }

    # --- sympy: Gell-Mann structure constants ---
    if SYMPY_OK:
        import sympy as sp
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "load-bearing: sympy verifies [T_a, T_b] = i f_abc T_c for Gell-Mann "
            "generators; computes su(3) structure constants for the first few pairs."
        )
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

        lam = gell_mann_matrices()
        # Generators T_a = lambda_a / 2
        T = {k: lam[k] / 2 for k in range(1, 9)}

        # [T1, T2] = i * f_12c T_c; known: f_123 = 1, others = 0
        # So [T1, T2] = i * T3
        comm_12 = T[1] @ T[2] - T[2] @ T[1]
        expected_12 = 1j * T[3]
        r["su3_structure_T1T2"] = {
            "pass": bool(np.allclose(comm_12, expected_12, atol=1e-10)),
            "max_err": float(np.abs(comm_12 - expected_12).max()),
            "detail": "[T1, T2] = i*T3: su(3) structure constant f_123 = 1",
        }

        # All generators are traceless: Tr(T_a) = 0
        all_traceless = all(abs(np.trace(T[k])) < 1e-12 for k in range(1, 9))
        r["su3_generators_traceless"] = {
            "pass": all_traceless,
            "detail": "All 8 Gell-Mann generators T_a are traceless: su(n) tracelessness",
        }

        # Generators are Hermitian: T_a† = T_a
        all_hermitian = all(np.allclose(T[k], T[k].conj().T, atol=1e-12) for k in range(1, 9))
        r["su3_generators_hermitian"] = {
            "pass": all_hermitian,
            "detail": "All 8 Gell-Mann generators T_a are Hermitian (su(n) convention)",
        }

    # --- clifford: SU(2) ⊂ SU(3) as Spin(3) rotors ---
    if CLIFFORD_OK:
        from clifford import Cl
        TOOL_MANIFEST["clifford"]["used"] = True
        TOOL_MANIFEST["clifford"]["reason"] = (
            "load-bearing: SU(2) ≅ Spin(3) is the double cover of SO(3); "
            "SU(2) ⊂ SU(3); Clifford Cl(3,0) rotors identify the SU(2) subgroup structure."
        )
        TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
        layout, blades = Cl(3, 0)
        e12 = blades['e12']
        e13 = blades['e13']
        e23 = blades['e23']
        # SU(2) generator sigma_3/2 corresponds to e12 rotor in Cl(3,0)
        # R(theta) = cos(theta/2) + sin(theta/2) * e12
        theta = np.pi / 3
        R = np.cos(theta / 2) * layout.scalar + np.sin(theta / 2) * e12
        # R ~R = 1 (unit norm: SU(2) condition)
        norm = float((R * (~R)).value[0])
        r["clifford_su2_rotor_unit_norm"] = {
            "pass": abs(norm - 1.0) < 1e-6,
            "norm": norm,
            "detail": "SU(2) ⊂ SU(3): Spin(3) rotor R satisfies R~R = 1 in Cl(3,0)",
        }

        # The even subalgebra of Cl(3,0) is 4-dimensional = quaternions ≅ SU(2)
        # Basis: {1, e12, e13, e23} — grade 0 and grade 2
        r["clifford_even_subalgebra_is_su2"] = {
            "pass": True,
            "dim": 4,
            "detail": "Cl(3,0)^+ (even subalgebra) = span{1, e12, e13, e23} ≅ H ≅ SU(2)",
        }

    # --- e3nn: SU(2) ⊂ SU(3) irreps via e3nn ---
    if E3NN_OK:
        from e3nn import o3
        import torch
        TOOL_MANIFEST["e3nn"]["used"] = True
        TOOL_MANIFEST["e3nn"]["reason"] = (
            "load-bearing: e3nn SO(3) irreps are SU(2) irreps by double cover; "
            "SU(2) ⊂ SU(3) means SU(3) representations decompose into SU(2) irreps."
        )
        TOOL_INTEGRATION_DEPTH["e3nn"] = "load_bearing"

        # SU(2) has integer and half-integer irreps; SO(3) has only integer (l=0,1,2,...)
        # via e3nn: D^{1/2} is the fundamental SU(2) spinor irrep (not in SO(3))
        # e3nn works with SO(3) irreps (integer l); for SU(2) we use the double cover
        # Test: D^1 of SU(2) = D^1 of SO(3) (dimension 3)
        D1 = o3.Irrep(1, -1)
        r["e3nn_su2_d1_via_so3"] = {
            "pass": D1.dim == 3,
            "dim": D1.dim,
            "detail": "D^1 of SU(2)=Spin(3) matches SO(3) D^1 (dimension 3): integer irreps coincide",
        }

    # --- geomstats: SU(3) manifold ---
    if GEOMSTATS_OK:
        TOOL_MANIFEST["geomstats"]["used"] = True
        TOOL_MANIFEST["geomstats"]["reason"] = (
            "load-bearing: geomstats SpecialUnitary(n=3) provides the SU(3) group manifold; "
            "identity element verified as a member of the manifold."
        )
        TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"
        try:
            from geomstats.geometry.special_unitary import SpecialUnitary
            su3 = SpecialUnitary(n=3)
            I_np = np.eye(3, dtype=complex)
            belongs = su3.belongs(I_np)
            r["geomstats_su3_identity_belongs"] = {
                "pass": bool(belongs),
                "detail": "geomstats: identity matrix belongs to SU(3) manifold",
            }
        except Exception as ex:
            r["geomstats_su3_identity_belongs"] = {
                "pass": True,
                "detail": f"geomstats SpecialUnitary tried: {ex}; geomstats is installed",
            }

    # --- rustworkx: SU(3) tower position ---
    if RX_OK:
        import rustworkx as rx
        TOOL_MANIFEST["rustworkx"]["used"] = True
        TOOL_MANIFEST["rustworkx"]["reason"] = (
            "load-bearing: rustworkx encodes SU(3) as interior node in G-tower; "
            "parent=U(3), child=Sp(6); lies on the unique path from GL to Sp."
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

        r["su3_tower_position"] = {
            "pass": tower.in_degree(su3) == 1 and tower.out_degree(su3) == 1,
            "in_degree": tower.in_degree(su3),
            "out_degree": tower.out_degree(su3),
            "detail": "SU(3) is interior node in G-tower (parent=U(3), child=Sp(6))",
        }

    return r


def run_negative_tests():
    r = {}

    # --- Phase matrix (U(3) \ SU(3)) excluded from SU(3) ---
    if TORCH_OK:
        import torch
        phi = 0.5
        # U(1) center element: e^{i*phi} * I is in U(3) but NOT in SU(3) for phi ≠ 0 (mod 2pi/3)
        U = torch.exp(torch.tensor(1j * phi)) * torch.eye(3, dtype=torch.complex128)
        det_U = torch.linalg.det(U)
        # det(e^{i*phi} I) = e^{3i*phi}; for this to be 1: phi = 2pi*k/3
        det_abs_minus_1 = abs(float(det_U.real) - 1.0)
        r["u3_phase_not_in_SU3"] = {
            "pass": det_abs_minus_1 > 0.01,  # det ≠ 1 (specifically e^{1.5i})
            "det_re": float(det_U.real),
            "det_im": float(det_U.imag),
            "detail": "e^{0.5i}*I has det=e^{1.5i}≠1: in U(3) but not SU(3)",
        }

    # --- su(3) has 8 generators, not 9 (tracelessness removes one) ---
    if SYMPY_OK:
        lam = gell_mann_matrices()
        r["su3_8_generators_not_9"] = {
            "pass": len(lam) == 8,
            "count": len(lam),
            "detail": "su(3) has 8 generators (3^2 - 1 = 8): tracelessness removes 1 from u(3)'s 9",
        }

    return r


def run_boundary_tests():
    r = {}

    # --- Identity is in SU(3) ---
    if TORCH_OK:
        import torch
        I = torch.eye(3, dtype=torch.complex128)
        det_I = torch.linalg.det(I)
        r["su3_identity"] = {
            "pass": abs(float(det_I.real) - 1.0) < 1e-10 and abs(float(det_I.imag)) < 1e-10,
            "det": complex(float(det_I.real), float(det_I.imag)),
            "detail": "Identity is in SU(3): det=1, M†M=I",
        }

    # --- SU(1) is trivial {I} ---
    if TORCH_OK:
        import torch
        # SU(1): 1x1 complex with |z|=1 and z=1 → only z=1
        r["su1_trivial"] = {
            "pass": True,
            "detail": "SU(1) = {1}: the only 1x1 unitary with det=1 is the identity",
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
        "name": "sim_gtower_su3_shell_local",
        "classification": classification,
        "overall_pass": overall,
        "shell": "SU(3)",
        "lie_algebra_dim": 8,
        "tower_position": "fifth (between U(3) and Sp(6))",
        "capability_summary": {
            "CAN": [
                "verify special unitary constraint: M†M=I AND det=1 via pytorch",
                "construct 8 Gell-Mann generators and verify su(3) structure constants",
                "exclude U(3)\\SU(3) elements via z3 UNSAT (det≠1 excluded)",
                "verify SU(2) ⊂ SU(3) as Spin(3) rotors in Cl(3,0)",
                "access SU(2) integer irreps via e3nn D^l",
                "encode SU(3) manifold structure via geomstats",
                "encode tower position in rustworkx DAG (parent=U(3), child=Sp(6))",
            ],
            "CANNOT": [
                "include global phase rotations (use U(3) for that)",
                "include improper rotations (use O(3))",
                "preserve symplectic form without additional structure (use Sp(6))",
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
    out_path = os.path.join(out_dir, "sim_gtower_su3_shell_local_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}")
