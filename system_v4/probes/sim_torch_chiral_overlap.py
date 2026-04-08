#!/usr/bin/env python3
"""
Torch Module: Chiral Overlap for Weyl Spinors
==============================================
|<L|R>|^2 for Weyl spinor pair parameterized by (theta, phi).

Two overlap quantities:
1. Orthogonality overlap: L(theta,phi) and R(theta,phi) are always orthogonal -> |<L|R>|^2 = 0
2. Fixed-reference chiral overlap: overlap of state with BOTH chiral projectors
   = cos^2(theta/2)*sin^2(theta/2) = sin^2(theta)/4

Matches numpy baseline from sim_pure_lego_chiral_overlap.py.

Tests:
- Orthogonality of L,R partners
- Fixed-ref overlap = sin^2(theta)/4
- Gradient w.r.t. angles
- Numpy cross-validation
- Cl(3) cross-validation of projectors
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": ""},
    "pyg":        {"tried": False, "used": False, "reason": ""},
    "z3":         {"tried": False, "used": False, "reason": ""},
    "cvc5":       {"tried": False, "used": False, "reason": ""},
    "sympy":      {"tried": False, "used": False, "reason": ""},
    "clifford":   {"tried": False, "used": False, "reason": ""},
    "geomstats":  {"tried": False, "used": False, "reason": ""},
    "e3nn":       {"tried": False, "used": False, "reason": ""},
    "rustworkx":  {"tried": False, "used": False, "reason": ""},
    "xgi":        {"tried": False, "used": False, "reason": ""},
    "toponetx":   {"tried": False, "used": False, "reason": ""},
    "gudhi":      {"tried": False, "used": False, "reason": ""},
}

try:
    import torch
    import torch.nn as nn
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import Real, Solver, And, sat  # noqa: F401
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# MODULE UNDER TEST: ChiralOverlap
# =====================================================================

class ChiralOverlap(nn.Module):
    """
    Differentiable chiral overlap computation.

    Parameters: theta, phi (Bloch sphere angles).
    Forward: returns both overlaps:
      - orthogonality_overlap: |<L(theta,phi)|R(theta,phi)>|^2  (always 0)
      - fixed_ref_overlap: p_L * p_R = cos^2(theta/2)*sin^2(theta/2) = sin^2(theta)/4
    """
    def __init__(self, theta=None, phi=None):
        super().__init__()
        if theta is None:
            theta = torch.tensor(np.pi / 4)
        if phi is None:
            phi = torch.tensor(0.0)
        self.theta = nn.Parameter(theta.float())
        self.phi = nn.Parameter(phi.float())

    def left_weyl(self):
        """Left Weyl spinor |L> = cos(theta/2)|0> + e^{i*phi}*sin(theta/2)|1>."""
        ct2 = torch.cos(self.theta / 2)
        st2 = torch.sin(self.theta / 2)
        cp = torch.cos(self.phi)
        sp_val = torch.sin(self.phi)
        L = torch.stack([
            torch.complex(ct2, torch.zeros_like(ct2)),
            torch.complex(st2 * cp, st2 * sp_val),
        ])
        return L

    def right_weyl(self):
        """Right Weyl spinor |R> = sin(theta/2)|0> - e^{i*phi}*cos(theta/2)|1>."""
        ct2 = torch.cos(self.theta / 2)
        st2 = torch.sin(self.theta / 2)
        cp = torch.cos(self.phi)
        sp_val = torch.sin(self.phi)
        R = torch.stack([
            torch.complex(st2, torch.zeros_like(st2)),
            torch.complex(-ct2 * cp, -ct2 * sp_val),
        ])
        return R

    def forward(self):
        """
        Returns:
          orthogonality_overlap: |<L|R>|^2 (should be 0)
          fixed_ref_overlap: cos^2(theta/2)*sin^2(theta/2) = sin^2(theta)/4
        """
        L = self.left_weyl()
        R = self.right_weyl()

        # <L|R> = conj(L) . R
        inner_LR = torch.sum(L.conj() * R)
        orth_overlap = torch.abs(inner_LR)**2

        # Fixed-reference chiral overlap
        ct2 = torch.cos(self.theta / 2)
        st2 = torch.sin(self.theta / 2)
        p_L = ct2**2
        p_R = st2**2
        fixed_ref = p_L * p_R

        return orth_overlap, fixed_ref

    def completeness(self):
        """Verify |L><L| + |R><R| = I."""
        L = self.left_weyl()
        R = self.right_weyl()
        # Outer products
        LL = torch.outer(L, L.conj())
        RR = torch.outer(R, R.conj())
        return LL + RR


# =====================================================================
# NUMPY BASELINE (matches sim_pure_lego_chiral_overlap.py)
# =====================================================================

def numpy_left_weyl(theta, phi):
    return np.array([np.cos(theta / 2),
                     np.exp(1j * phi) * np.sin(theta / 2)], dtype=complex)


def numpy_right_weyl(theta, phi):
    return np.array([np.sin(theta / 2),
                     -np.exp(1j * phi) * np.cos(theta / 2)], dtype=complex)


def numpy_chiral_overlap(theta, phi):
    L = numpy_left_weyl(theta, phi)
    R = numpy_right_weyl(theta, phi)
    return float(np.abs(np.dot(L.conj(), R))**2)


def numpy_fixed_ref_overlap(theta, phi):
    return float(np.cos(theta / 2)**2 * np.sin(theta / 2)**2)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    test_angles = [
        (0.0, 0.0), (np.pi / 4, 0.0), (np.pi / 2, 0.0),
        (np.pi / 2, np.pi / 4), (np.pi, 0.0), (np.pi / 3, np.pi / 6),
        (2.1, 0.7), (0.1, 3.0),
    ]

    # --- P1: L,R always orthogonal (matches numpy baseline) ---
    p1_results = {}
    for theta, phi in test_angles:
        mod = ChiralOverlap(torch.tensor(theta), torch.tensor(phi))
        orth, _ = mod.forward()
        orth_val = float(orth.detach())
        np_val = numpy_chiral_overlap(theta, phi)
        diff = abs(orth_val - np_val)
        p1_results[f"t={theta:.3f}_p={phi:.3f}"] = {
            "torch_overlap": orth_val,
            "numpy_overlap": np_val,
            "both_zero": orth_val < 1e-10 and np_val < 1e-10,
            "diff": diff,
            "pass": orth_val < 1e-10,
        }
    results["P1_LR_orthogonality"] = p1_results

    # --- P2: Fixed-ref overlap = sin^2(theta)/4 ---
    p2_results = {}
    for theta, phi in test_angles:
        mod = ChiralOverlap(torch.tensor(theta), torch.tensor(phi))
        _, fixed = mod.forward()
        fixed_val = float(fixed.detach())
        analytic = np.sin(theta)**2 / 4.0
        np_val = numpy_fixed_ref_overlap(theta, phi)
        diff_analytic = abs(fixed_val - analytic)
        diff_numpy = abs(fixed_val - np_val)
        p2_results[f"t={theta:.3f}_p={phi:.3f}"] = {
            "torch": fixed_val,
            "analytic": float(analytic),
            "numpy": np_val,
            "diff_analytic": diff_analytic,
            "diff_numpy": diff_numpy,
            "pass": diff_analytic < 1e-6 and diff_numpy < 1e-6,
        }
    results["P2_fixed_ref_sin2_over_4"] = p2_results

    # --- P3: Completeness |L><L| + |R><R| = I ---
    p3_results = {}
    for theta, phi in test_angles:
        mod = ChiralOverlap(torch.tensor(theta), torch.tensor(phi))
        proj_sum = mod.completeness().detach().numpy()
        diff = float(np.max(np.abs(proj_sum - np.eye(2))))
        p3_results[f"t={theta:.3f}_p={phi:.3f}"] = {
            "max_diff_from_I": diff,
            "pass": diff < 1e-5,
        }
    results["P3_completeness"] = p3_results

    # --- P4: Gradient of fixed_ref_overlap w.r.t. theta ---
    # d/dtheta [sin^2(theta)/4] = sin(theta)*cos(theta)/2 = sin(2*theta)/4
    p4_results = {}
    for theta in [np.pi / 6, np.pi / 4, np.pi / 3, np.pi / 2, 2.0]:
        mod = ChiralOverlap(torch.tensor(theta), torch.tensor(0.0))
        _, fixed = mod.forward()
        fixed.backward()
        grad_theta = float(mod.theta.grad.item())
        expected_grad = np.sin(2 * theta) / 4.0
        diff = abs(grad_theta - expected_grad)
        p4_results[f"theta={theta:.4f}"] = {
            "grad_autograd": grad_theta,
            "grad_analytic": float(expected_grad),
            "diff": diff,
            "pass": diff < 1e-5,
        }
    results["P4_gradient_theta"] = p4_results

    # --- P5: L<->R symmetry (theta -> pi-theta gives same overlap) ---
    p5_results = {}
    for theta, phi in test_angles:
        mod1 = ChiralOverlap(torch.tensor(theta), torch.tensor(phi))
        _, f1 = mod1.forward()
        mod2 = ChiralOverlap(torch.tensor(np.pi - theta), torch.tensor(phi))
        _, f2 = mod2.forward()
        diff = abs(float(f1.detach()) - float(f2.detach()))
        p5_results[f"t={theta:.3f}"] = {
            "overlap_theta": float(f1.detach()),
            "overlap_pi_minus_theta": float(f2.detach()),
            "diff": diff,
            "pass": diff < 1e-6,
        }
    results["P5_LR_symmetry"] = p5_results

    # --- P6: Cl(3) cross-validation of chiral projectors ---
    p6_results = {}
    if TOOL_MANIFEST["clifford"]["tried"]:
        try:
            layout, blades = Cl(3)
            e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
            one = 1.0 + 0 * e1

            # e3-axis projectors
            P_plus = (one + e3) * 0.5
            P_minus = (one - e3) * 0.5

            # Idempotent
            Pp_sq = P_plus * P_plus
            Pm_sq = P_minus * P_minus
            idem_p = np.allclose(Pp_sq.value, P_plus.value, atol=1e-12)
            idem_m = np.allclose(Pm_sq.value, P_minus.value, atol=1e-12)

            # Orthogonal
            Pp_Pm = P_plus * P_minus
            ortho = np.allclose(Pp_Pm.value, np.zeros_like(Pp_Pm.value), atol=1e-12)

            # Complete
            Pp_plus_Pm = P_plus + P_minus
            complete = np.allclose(Pp_plus_Pm.value, one.value, atol=1e-12)

            p6_results = {
                "P_plus_idempotent": idem_p,
                "P_minus_idempotent": idem_m,
                "orthogonal": ortho,
                "complete": complete,
                "pass": idem_p and idem_m and ortho and complete,
            }
        except Exception as e:
            p6_results = {"error": str(e), "pass": False}
    else:
        p6_results = {"skipped": True, "reason": "clifford not available", "pass": True}
    results["P6_clifford_projectors"] = p6_results

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: Non-normalized spinors break overlap computation ---
    n1_results = {}
    for scale in [0.5, 2.0, 0.0]:
        theta, phi = np.pi / 4, 0.0
        L_np = numpy_left_weyl(theta, phi) * scale
        R_np = numpy_right_weyl(theta, phi)
        overlap = float(np.abs(np.dot(L_np.conj(), R_np))**2)
        # Should still be 0 (scaling doesn't break orthogonality)
        # But completeness breaks
        proj_sum = np.outer(L_np, L_np.conj()) + np.outer(R_np, R_np.conj())
        completeness_broken = not np.allclose(proj_sum, np.eye(2), atol=1e-6)
        n1_results[f"scale={scale}"] = {
            "overlap_still_zero": overlap < 1e-10,
            "completeness_broken": completeness_broken,
            "pass": completeness_broken or scale == 1.0,
        }
    results["N1_non_normalized_spinors"] = n1_results

    # --- N2: Wrong chirality partner (same handedness) gives non-zero overlap ---
    n2_results = {}
    for theta, phi in [(np.pi / 4, 0.0), (np.pi / 3, np.pi / 6)]:
        L1 = numpy_left_weyl(theta, phi)
        L2 = numpy_left_weyl(theta + 0.1, phi)  # Slightly different angle
        overlap = float(np.abs(np.dot(L1.conj(), L2))**2)
        n2_results[f"t={theta:.3f}"] = {
            "same_hand_overlap": overlap,
            "is_nonzero": overlap > 1e-6,
            "pass": overlap > 1e-6,  # EXPECT non-zero
        }
    results["N2_same_handedness_overlap"] = n2_results

    # --- N3: Gradient of orthogonality overlap should be zero everywhere ---
    n3_results = {}
    for theta in [np.pi / 4, np.pi / 2, np.pi / 3]:
        mod = ChiralOverlap(torch.tensor(theta), torch.tensor(0.0))
        orth, _ = mod.forward()
        orth.backward()
        grad = mod.theta.grad
        grad_val = float(grad.item()) if grad is not None else 0.0
        n3_results[f"theta={theta:.4f}"] = {
            "grad_of_zero_overlap": grad_val,
            "is_zero": abs(grad_val) < 1e-6,
            "pass": abs(grad_val) < 1e-6,
        }
    results["N3_orth_overlap_gradient_zero"] = n3_results

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- B1: North pole (theta=0) -- overlap = 0 ---
    mod = ChiralOverlap(torch.tensor(0.0), torch.tensor(0.0))
    _, fixed = mod.forward()
    val = float(fixed.detach())
    results["B1_north_pole"] = {
        "fixed_ref_overlap": val,
        "is_zero": abs(val) < 1e-10,
        "pass": abs(val) < 1e-10,
    }

    # --- B2: South pole (theta=pi) -- overlap = 0 ---
    mod = ChiralOverlap(torch.tensor(np.pi), torch.tensor(0.0))
    _, fixed = mod.forward()
    val = float(fixed.detach())
    results["B2_south_pole"] = {
        "fixed_ref_overlap": val,
        "is_zero": abs(val) < 1e-10,
        "pass": abs(val) < 1e-10,
    }

    # --- B3: Equator (theta=pi/2) -- maximum overlap = 0.25 ---
    mod = ChiralOverlap(torch.tensor(np.pi / 2), torch.tensor(0.0))
    _, fixed = mod.forward()
    val = float(fixed.detach())
    results["B3_equator_max"] = {
        "fixed_ref_overlap": val,
        "expected": 0.25,
        "diff": abs(val - 0.25),
        "pass": abs(val - 0.25) < 1e-6,
    }

    # --- B4: Full theta sweep, overlap matches sin^2(theta)/4 ---
    thetas = np.linspace(0, np.pi, 50)
    max_diff = 0.0
    for theta in thetas:
        mod = ChiralOverlap(torch.tensor(float(theta)), torch.tensor(0.0))
        _, fixed = mod.forward()
        val = float(fixed.detach())
        analytic = np.sin(theta)**2 / 4.0
        max_diff = max(max_diff, abs(val - analytic))
    results["B4_full_sweep"] = {
        "n_points": len(thetas),
        "max_diff_from_analytic": max_diff,
        "pass": max_diff < 1e-6,
    }

    # --- B5: Gradient zero at poles and equator (extrema) ---
    b5_results = {}
    for name, theta in [("north_pole", 0.0), ("south_pole", np.pi), ("equator", np.pi / 2)]:
        mod = ChiralOverlap(torch.tensor(theta), torch.tensor(0.0))
        _, fixed = mod.forward()
        fixed.backward()
        grad = float(mod.theta.grad.item())
        expected = np.sin(2 * theta) / 4.0
        b5_results[name] = {
            "gradient": grad,
            "expected": float(expected),
            "is_zero": abs(grad) < 1e-5,
            "pass": abs(grad - expected) < 1e-5,
        }
    results["B5_gradient_at_extrema"] = b5_results

    # --- B6: Autograd vs finite difference ---
    eps = 1e-4
    b6_results = {}
    for theta in [np.pi / 6, np.pi / 3, 1.0, 2.5]:
        mod = ChiralOverlap(torch.tensor(theta), torch.tensor(0.0))
        _, fixed = mod.forward()
        fixed.backward()
        grad_auto = float(mod.theta.grad.item())

        f_plus = numpy_fixed_ref_overlap(theta + eps, 0.0)
        f_minus = numpy_fixed_ref_overlap(theta - eps, 0.0)
        grad_fd = (f_plus - f_minus) / (2 * eps)

        diff = abs(grad_auto - grad_fd)
        b6_results[f"theta={theta:.4f}"] = {
            "autograd": grad_auto,
            "finite_diff": grad_fd,
            "diff": diff,
            "pass": diff < 1e-3,
        }
    results["B6_autograd_vs_fd"] = b6_results

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "Core module: ChiralOverlap as nn.Module, autograd for gradients"
    if TOOL_MANIFEST["clifford"]["tried"]:
        TOOL_MANIFEST["clifford"]["used"] = True
        TOOL_MANIFEST["clifford"]["reason"] = "Cl(3) projector cross-validation"
    if TOOL_MANIFEST["geomstats"]["tried"]:
        TOOL_MANIFEST["geomstats"]["reason"] = "tried import, not used for chiral overlap"

    def count_passes(d):
        passes, total = 0, 0
        if isinstance(d, dict):
            if "pass" in d:
                total += 1
                if d["pass"]:
                    passes += 1
            for v in d.values():
                p, t = count_passes(v)
                passes += p
                total += t
        return passes, total

    all_results = {
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }
    total_pass, total_tests = count_passes(all_results)

    results = {
        "name": "torch_chiral_overlap",
        "family": "GEOMETRIC",
        "description": "Chiral overlap |<L|R>|^2 for Weyl spinor pair, torch.nn.Module",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "summary": {
            "total_tests": total_tests,
            "total_pass": total_pass,
            "all_pass": total_pass == total_tests,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_chiral_overlap_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- inspect results JSON")
