#!/usr/bin/env python3
"""
sim_z3_pytorch_cross_check.py -- z3/pytorch cross-check integration sim.

z3 proves MI=0 AND Q>0 is UNSAT (structural impossibility).
pytorch autograd computes Q numerically on the same configuration and
confirms gradient direction matches z3 structural proof. Both tools must
agree -- if they disagree, test fails.

classification: canonical
z3: load_bearing
pytorch: load_bearing
sympy: supportive
"""

import json
import os
import math
import numpy as np

classification = "canonical"

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

TOOL_INTEGRATION_DEPTH = {
    "clifford": None,
    "cvc5": None,
    "e3nn": None,
    "geomstats": None,
    "gudhi": None,
    "pyg": None,
    "pytorch": "load_bearing",
    "rustworkx": None,
    "sympy": "load_bearing",
    "toponetx": None,
    "xgi": None,
    "z3": "load_bearing",
}

# --- imports ---
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import (Real, Bool, Solver, sat, unsat, And, Implies,
                    RealVal, Not, Or)  # noqa: F401
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
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
# DEFINITIONS
# =====================================================================
#
# Q = MI * prod(H_i)   (universal Q-product form from project memory)
# MI = mutual information between subsystems A and B
# H_A, H_B = marginal entropies
#
# Structural claim: MI=0 AND Q>0 is UNSAT
# because Q = MI * H_A * H_B; if MI=0 then Q=0, so Q>0 is impossible.
#
# pytorch computes Q numerically for a product state (MI=0 expected)
# and an entangled state (MI>0 expected), then checks gradient of Q
# w.r.t. entanglement parameter matches z3 structural direction.

def marginal_entropy(rho: "torch.Tensor", dim: int) -> "torch.Tensor":
    """
    Partial trace and von Neumann entropy; rho is 4x4 two-qubit density matrix.
    Reshape to (2,2,2,2) where axes are [row_A, row_B, col_A, col_B].
    rho_A[a,c] = sum_b rho[a,b,c,b]  (trace over B)
    rho_B[b,d] = sum_a rho[a,b,a,d]  (trace over A)
    """
    r = rho.reshape(2, 2, 2, 2)
    if dim == 0:
        marginal = torch.einsum("abcb->ac", r)
    else:
        marginal = torch.einsum("abac->bc", r)
    ev = torch.linalg.eigvalsh(marginal).clamp(min=1e-15)
    return -(ev * torch.log(ev)).sum()


def joint_entropy(rho: "torch.Tensor") -> "torch.Tensor":
    ev = torch.linalg.eigvalsh(rho).clamp(min=1e-15)
    return -(ev * torch.log(ev)).sum()


def mutual_information(rho: "torch.Tensor") -> "torch.Tensor":
    """MI = H_A + H_B - H_AB."""
    H_A = marginal_entropy(rho, 0)
    H_B = marginal_entropy(rho, 1)
    H_AB = joint_entropy(rho)
    return H_A + H_B - H_AB


def Q_product(rho: "torch.Tensor") -> "torch.Tensor":
    """Q = MI * H_A * H_B."""
    H_A = marginal_entropy(rho, 0)
    H_B = marginal_entropy(rho, 1)
    MI = mutual_information(rho)
    return MI * H_A * H_B


def product_state_rho(p: float = 0.3) -> "torch.Tensor":
    """
    Product state rho_A ⊗ rho_B; MI=0 by construction.
    rho_A = diag(p, 1-p), rho_B = diag(0.5, 0.5)
    """
    rho_A = torch.diag(torch.tensor([p, 1.0 - p], dtype=torch.float64))
    rho_B = torch.eye(2, dtype=torch.float64) / 2.0
    return torch.kron(rho_A, rho_B)


def parameterized_entangled_rho(eps: "torch.Tensor") -> "torch.Tensor":
    """
    Near-product state with entanglement parameter eps.
    State |psi> = sqrt(1-eps^2)|00> + eps|11>
    rho = |psi><psi|
    """
    # Build state vector
    zero_zero = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=torch.float64)
    one_one = torch.tensor([0.0, 0.0, 0.0, 1.0], dtype=torch.float64)
    norm = torch.sqrt(1.0 - eps * eps)
    psi = norm * zero_zero + eps * one_one
    return torch.outer(psi, psi)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests() -> dict:
    results = {}

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Autograd computes Q gradient; numerical MI check is load-bearing cross-check with z3"
    )
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "z3 UNSAT on MI=0 AND Q>0 is the primary structural proof; pytorch must agree numerically"
    )

    # --- P1: z3 structural proof: MI=0 AND Q>0 is UNSAT ---
    if TOOL_MANIFEST["z3"]["tried"]:
        from z3 import Real, Solver, unsat, And
        MI = Real("MI")
        H_A = Real("H_A")
        H_B = Real("H_B")
        Q = Real("Q")
        solver = Solver()
        # Q = MI * H_A * H_B
        solver.add(Q == MI * H_A * H_B)
        # Entropies are non-negative
        solver.add(H_A >= 0.0)
        solver.add(H_B >= 0.0)
        # Claim: MI=0 AND Q>0
        solver.add(MI == 0.0)
        solver.add(Q > 0.0)
        z3_result = solver.check()
        z3_unsat = z3_result == unsat
        results["P1_z3_MI_zero_Q_positive_UNSAT"] = {
            "z3_result": str(z3_result),
            "pass": z3_unsat,
            "note": (
                "MI=0 AND Q>0 is structurally impossible (UNSAT); "
                "Q=0 whenever MI=0 by definition of Q-product form"
            ),
        }
    else:
        results["P1_z3_MI_zero_Q_positive_UNSAT"] = {
            "pass": False,
            "note": "z3 not available; cannot execute structural proof",
        }

    # --- P2: pytorch confirms MI≈0 for product state ---
    rho_prod = product_state_rho(0.3)
    MI_prod = mutual_information(rho_prod).item()
    results["P2_pytorch_product_state_MI_near_zero"] = {
        "MI": MI_prod,
        "pass": abs(MI_prod) < 1e-8,
        "note": "Product state MI survived to near-zero; consistent with z3 UNSAT constraint",
    }

    # --- P3: pytorch confirms Q≈0 for product state (consistent with z3 UNSAT) ---
    Q_prod = Q_product(rho_prod).item()
    results["P3_pytorch_product_state_Q_near_zero"] = {
        "Q": Q_prod,
        "pass": abs(Q_prod) < 1e-8,
        "note": "Q=0 when MI=0; confirms z3 structural proof numerically",
    }

    # --- P4: pytorch confirms MI>0 for entangled state ---
    eps_val = torch.tensor(0.5, dtype=torch.float64, requires_grad=True)
    rho_ent = parameterized_entangled_rho(eps_val)
    MI_ent = mutual_information(rho_ent)
    results["P4_pytorch_entangled_state_MI_positive"] = {
        "MI": MI_ent.item(),
        "pass": MI_ent.item() > 0.01,
        "note": "Entangled state survives to MI>0; excluded from zero-MI family",
    }

    # --- P5: z3 confirms MI>0 AND Q>0 is SAT ---
    if TOOL_MANIFEST["z3"]["tried"]:
        from z3 import Real, Solver, sat, And
        MI2 = Real("MI2")
        H_A2 = Real("H_A2")
        H_B2 = Real("H_B2")
        Q2 = Real("Q2")
        solver2 = Solver()
        solver2.add(Q2 == MI2 * H_A2 * H_B2)
        solver2.add(H_A2 > 0.0)
        solver2.add(H_B2 > 0.0)
        solver2.add(MI2 > 0.0)
        solver2.add(Q2 > 0.0)
        z3_result2 = solver2.check()
        z3_sat = z3_result2 == sat
        results["P5_z3_MI_positive_Q_positive_SAT"] = {
            "z3_result": str(z3_result2),
            "pass": z3_sat,
            "note": "MI>0 AND Q>0 is SAT; entangled states are admissible candidates",
        }
    else:
        results["P5_z3_MI_positive_Q_positive_SAT"] = {
            "pass": False,
            "note": "z3 not available",
        }

    # --- P6: pytorch gradient of Q w.r.t. eps is positive (increasing entanglement increases Q) ---
    Q_ent = Q_product(rho_ent)
    Q_ent.backward()
    grad_eps = eps_val.grad.item()
    # At eps=0.5, increasing entanglement should increase Q
    results["P6_pytorch_Q_gradient_positive_wrt_entanglement"] = {
        "Q": Q_ent.item(),
        "gradient_Q_wrt_eps": grad_eps,
        "pass": grad_eps > 0.0,
        "note": "Q gradient w.r.t. entanglement parameter is positive; consistent with z3 SAT region",
    }

    # --- P7: z3-pytorch agreement check ---
    # z3 says: if MI=0 then Q=0 (UNSAT for Q>0)
    # pytorch says: Q≈0 for product state (MI≈0)
    # Agreement: both must say Q is near-zero for product state
    z3_says_q_zero_for_mi_zero = results.get("P1_z3_MI_zero_Q_positive_UNSAT", {}).get("pass", False)
    pytorch_says_q_zero = results.get("P3_pytorch_product_state_Q_near_zero", {}).get("pass", False)
    agree = z3_says_q_zero_for_mi_zero and pytorch_says_q_zero
    results["P7_z3_pytorch_agreement"] = {
        "z3_q_zero_for_mi_zero": z3_says_q_zero_for_mi_zero,
        "pytorch_q_zero_for_product": pytorch_says_q_zero,
        "pass": agree,
        "note": "Both tools must agree on Q=0 for product state; disagreement would invalidate claim",
    }

    # --- P8: sympy symbolic confirmation of Q=MI*H_A*H_B identity ---
    if TOOL_MANIFEST["sympy"]["tried"]:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "Symbolic verification that Q=0 when MI=0 is algebraically necessary"
        )
        MI_s, H_A_s, H_B_s = sp.symbols("MI H_A H_B", real=True, nonnegative=True)
        Q_s = MI_s * H_A_s * H_B_s
        Q_at_MI_zero = Q_s.subs(MI_s, 0)
        sympy_q_zero = Q_at_MI_zero == sp.Integer(0)
        results["P8_sympy_Q_zero_when_MI_zero"] = {
            "Q_at_MI_0": str(Q_at_MI_zero),
            "pass": sympy_q_zero,
            "note": "Symbolic algebra confirms Q=0 when MI=0; supports z3 and pytorch agreement",
        }
    else:
        results["P8_sympy_Q_zero_when_MI_zero"] = {
            "pass": False,
            "note": "sympy not available",
        }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests() -> dict:
    results = {}

    # --- N1: z3 correctly finds SAT (not UNSAT) for unconstrained Q ---
    if TOOL_MANIFEST["z3"]["tried"]:
        from z3 import Real, Solver, sat
        Q_n = Real("Q_n")
        solver_n = Solver()
        solver_n.add(Q_n > 0.0)
        z3_res = solver_n.check()
        results["N1_z3_unconstrained_Q_positive_SAT"] = {
            "z3_result": str(z3_res),
            "pass": z3_res == sat,
            "note": "Without MI=0 constraint, Q>0 is SAT; z3 correctly excludes false UNSAT",
        }
    else:
        results["N1_z3_unconstrained_Q_positive_SAT"] = {
            "pass": False,
            "note": "z3 not available",
        }

    # --- N2: product state correctly excluded from MI>0 family ---
    rho_prod = product_state_rho(0.7)
    MI_val = mutual_information(rho_prod).item()
    results["N2_product_state_excluded_from_MI_positive_family"] = {
        "MI": MI_val,
        "pass": MI_val < 1e-6,
        "note": "Product state MI survives near-zero; excluded from entangled-state family",
    }

    # --- N3: maximally entangled Bell state has MI = log(4) approximately ---
    # |Bell> = (|00> + |11>)/sqrt(2) => eps = 1/sqrt(2)
    eps_bell = torch.tensor(1.0 / math.sqrt(2), dtype=torch.float64)
    rho_bell = parameterized_entangled_rho(eps_bell)
    MI_bell = mutual_information(rho_bell).item()
    results["N3_bell_state_MI_large"] = {
        "MI": MI_bell,
        "pass": MI_bell > 0.5,
        "note": "Bell state excluded from low-MI family; MI survived to >0.5",
    }

    # --- N4: gradient of Q is zero at eps=0 (product state boundary) ---
    eps_zero = torch.tensor(0.0 + 1e-6, dtype=torch.float64, requires_grad=True)
    rho_near_prod = parameterized_entangled_rho(eps_zero)
    Q_near = Q_product(rho_near_prod)
    Q_near.backward()
    grad_at_zero = eps_zero.grad.item()
    results["N4_Q_gradient_near_zero_at_product_state"] = {
        "gradient": grad_at_zero,
        "pass": abs(grad_at_zero) < 1.0,  # should be small near product state
        "note": "Q gradient near eps=0 is small; product state is boundary, not interior",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests() -> dict:
    results = {}

    # --- B1: z3 UNSAT survives when Q is defined as strictly positive constant ---
    if TOOL_MANIFEST["z3"]["tried"]:
        from z3 import Real, Solver, unsat, And
        MI_b = Real("MI_b")
        Q_b = Real("Q_b")
        H_b = Real("H_b")
        s = Solver()
        s.add(Q_b == MI_b * H_b * H_b)
        s.add(H_b > 0.0)
        s.add(MI_b == 0.0)
        s.add(Q_b > 1e-20)  # boundary: tiny positive Q
        bres = s.check()
        results["B1_z3_UNSAT_holds_at_tiny_positive_Q_boundary"] = {
            "z3_result": str(bres),
            "pass": bres == unsat,
            "note": "UNSAT holds even for infinitesimally positive Q boundary; structural exclusion is strict",
        }
    else:
        results["B1_z3_UNSAT_holds_at_tiny_positive_Q_boundary"] = {
            "pass": False,
            "note": "z3 not available",
        }

    # --- B2: pytorch eps=1/sqrt(2) Bell state Q is nonzero ---
    eps_bell2 = torch.tensor(1.0 / math.sqrt(2), dtype=torch.float64)
    rho_bell2 = parameterized_entangled_rho(eps_bell2)
    Q_bell = Q_product(rho_bell2).item()
    results["B2_bell_state_Q_nonzero"] = {
        "Q": Q_bell,
        "pass": Q_bell > 1e-6,
        "note": "Bell state boundary survives Q>0; maximally entangled state admitted to Q>0 family",
    }

    # --- B3: eps=0 product state Q is exactly zero at float64 precision ---
    eps0 = torch.tensor(0.0, dtype=torch.float64)
    rho_exact_prod = parameterized_entangled_rho(eps0)
    Q_exact = Q_product(rho_exact_prod).item()
    results["B3_exact_product_state_Q_zero"] = {
        "Q": Q_exact,
        "pass": abs(Q_exact) < 1e-10,
        "note": "eps=0 product state Q must be exactly zero; boundary of admissibility region",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_sections = {**positive, **negative, **boundary}
    all_pass = all(v.get("pass", False) for v in all_sections.values())

    results = {
        "name": "sim_z3_pytorch_cross_check",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "total_tests": len(all_sections),
            "passed": sum(1 for v in all_sections.values() if v.get("pass", False)),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_z3_pytorch_cross_check_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass} | {results['summary']['passed']}/{results['summary']['total_tests']}")
    if not all_pass:
        for k, v in all_sections.items():
            if not v.get("pass", False):
                print(f"  FAILED: {k} -- {v.get('note', '')}")
        raise SystemExit(1)
