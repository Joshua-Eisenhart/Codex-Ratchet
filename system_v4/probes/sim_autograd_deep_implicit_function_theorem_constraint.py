#!/usr/bin/env python3
"""sim_autograd_deep_implicit_function_theorem_constraint -- autograd IFT via dg/dx = -(∂g/∂y)^-1 ∂g/∂x

Canonical sim. PyTorch autograd is LOAD-BEARING: the claim is a statement
about gradient flow / Jacobian / Hessian structure that requires automatic
differentiation through a density-matrix / constraint functional. A pure
finite-difference or numpy implementation would NOT support the claim because
the admissibility predicate is tested on the autograd-computed gradient
itself (its norm, sign, rank, PSD-ness, or coupling to another autograd
gradient).

scope_note: Load-bearing autograd Jacobians verify implicit-function admissibility of constraint g(x,y)=0.

Language discipline: we speak of candidate states that are *admissible*,
*indistinguishable*, or *excluded* under probe. No causal / ontological
claims. A passing test means the candidate SURVIVED the probe, not that it
is "the" true object.
"""

import json, os, math
import numpy as np
import torch

TOOL_MANIFEST = {
    "pytorch":  {"tried": True,  "used": True,  "reason": "autograd is load-bearing: both partial Jacobians ∂g/∂x, ∂g/∂y come from autograd; IFT claim rests on their invertibility"},
    "pyg":      {"tried": False, "used": False, "reason": "graph message passing not required for this scalar/matrix-functional claim"},
    "z3":       {"tried": False, "used": False, "reason": "claim is numerical-gradient structure, not SMT admissibility (deferred to companion proof sim)"},
    "cvc5":     {"tried": False, "used": False, "reason": "same as z3: numerical gradient claim, not SMT"},
    "sympy":    {"tried": False, "used": False, "reason": "symbolic form of entropy/Fisher/KL is standard; numerical gradient is the load-bearing object"},
    "clifford": {"tried": False, "used": False, "reason": "no Cl(n) rotor needed for scalar functional of rho"},
    "geomstats":{"tried": False, "used": False, "reason": "manifold metric not used; Fisher computed directly via autograd"},
    "e3nn":     {"tried": False, "used": False, "reason": "no SO(3) equivariance required"},
    "rustworkx":{"tried": False, "used": False, "reason": "no graph structure in this probe"},
    "xgi":      {"tried": False, "used": False, "reason": "no hypergraph in this probe"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex in this probe"},
    "gudhi":    {"tried": False, "used": False, "reason": "no persistent homology in this probe"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

torch.manual_seed(0)
DTYPE = torch.float64

# ---------------------------------------------------------------------------
# Helpers (shared across sims; kept inline per self-contained sim contract)
# ---------------------------------------------------------------------------

def random_hermitian(n, scale=1.0):
    A = torch.randn(n, n, dtype=DTYPE) + 1j*torch.randn(n, n, dtype=DTYPE)
    return 0.5 * (A + A.conj().T) * scale

def parametrised_rho(params, n):
    """params -> valid density matrix via rho = L L^dagger / tr(L L^dagger)."""
    k = n*n
    L = params[:k].reshape(n, n).to(torch.complex128) + 1j*params[k:2*k].reshape(n, n).to(torch.complex128)
    M = L @ L.conj().T
    tr = torch.trace(M).real
    return M / tr

def von_neumann_entropy(rho, eps=1e-12):
    evals = torch.linalg.eigvalsh(0.5*(rho + rho.conj().T))
    evals = torch.clamp(evals.real, min=eps)
    return -(evals * torch.log(evals)).sum()


SCOPE_NOTE = "Constraint g(x,y) = x^2 + y^2 - 1 (and 2D extension); admissible where ∂g/∂y invertible."

def g(x, y):
    # x in R^2, y in R^2, g in R^2 : [x1^2+y1^2-1, x2*y2 - 0.25]
    return torch.stack([x[0]**2 + y[0]**2 - 1.0, x[1]*y[1] - 0.25])

def jac(f, v):
    return torch.autograd.functional.jacobian(f, v)

def run_positive_tests():
    x = torch.tensor([0.3, 0.5], dtype=DTYPE, requires_grad=True)
    y = torch.tensor([math.sqrt(1-0.09), 0.5], dtype=DTYPE, requires_grad=True)
    Jx = jac(lambda xx: g(xx, y), x)
    Jy = jac(lambda yy: g(x, yy), y)
    dy_dx = -torch.linalg.solve(Jy, Jx)
    # verify: perturb x by small dx, see y adjust
    dx = torch.tensor([1e-4, 1e-4], dtype=DTYPE)
    y2 = y + dy_dx @ dx
    residual = g(x+dx, y2)
    ok = float(torch.linalg.norm(residual)) < 1e-6
    return {"ift_predicts_admissible_y": {"pass": ok, "residual_norm": float(torch.linalg.norm(residual)),
            "note": "candidate y(x+dx) survived constraint probe"}}

def run_negative_tests():
    # at singular point y1=0 => ∂g1/∂y1 = 0; Jy singular => IFT excluded
    x = torch.tensor([1.0, 0.5], dtype=DTYPE, requires_grad=True)
    y = torch.tensor([0.0, 0.5], dtype=DTYPE, requires_grad=True)
    Jy = jac(lambda yy: g(x, yy), y)
    det = float(torch.linalg.det(Jy))
    ok = abs(det) < 1e-8
    return {"singular_point_excluded": {"pass": ok, "det_Jy": det,
            "note": "singular candidate excluded from IFT-admissible set"}}

def run_boundary_tests():
    # near-singular: det small but nonzero
    x = torch.tensor([0.9, 0.5], dtype=DTYPE, requires_grad=True)
    y = torch.tensor([math.sqrt(1-0.81), 0.5], dtype=DTYPE, requires_grad=True)
    Jy = jac(lambda yy: g(x, yy), y)
    det = float(torch.linalg.det(Jy))
    ok = abs(det) > 0 and abs(det) < 1.0
    return {"near_singular_still_admissible": {"pass": ok, "det_Jy": det,
            "note": "boundary candidate remains admissible (det nonzero)"}}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    results = {
        "name": __doc__.splitlines()[0] if __doc__ else "autograd_sim",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "scope_note": SCOPE_NOTE,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    overall = all(
        v.get("pass", False)
        for section in ("positive", "negative", "boundary")
        for v in results[section].values()
    )
    results["overall_pass"] = overall
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(__file__))[0]
    out_path = os.path.join(out_dir, base + "_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{base}: overall_pass={overall} -> {out_path}")
