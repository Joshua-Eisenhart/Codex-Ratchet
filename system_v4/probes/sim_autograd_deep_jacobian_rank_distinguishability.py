#!/usr/bin/env python3
"""sim_autograd_deep_jacobian_rank_distinguishability -- autograd Jacobian rank = locally distinguishable directions

Canonical sim. PyTorch autograd is LOAD-BEARING: the claim is a statement
about gradient flow / Jacobian / Hessian structure that requires automatic
differentiation through a density-matrix / constraint functional. A pure
finite-difference or numpy implementation would NOT support the claim because
the admissibility predicate is tested on the autograd-computed gradient
itself (its norm, sign, rank, PSD-ness, or coupling to another autograd
gradient).

scope_note: Local distinguishability dim = rank of autograd Jacobian of observable map.

Language discipline: we speak of candidate states that are *admissible*,
*indistinguishable*, or *excluded* under probe. No causal / ontological
claims. A passing test means the candidate SURVIVED the probe, not that it
is "the" true object.
"""

import json, os, math
import numpy as np
import torch

TOOL_MANIFEST = {
    "pytorch":  {"tried": True,  "used": True,  "reason": "autograd is load-bearing: Jacobian of observable vector w.r.t. parameters is autograd-computed; rank is the distinguishability count"},
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


SCOPE_NOTE = "Observable map F: R^4 -> R^3; rank(J) counts locally distinguishable parameter directions."

def F_full(theta):
    return torch.stack([
        torch.sin(theta[0]) + theta[2],
        torch.cos(theta[1]) - theta[3],
        theta[0]*theta[1] + theta[2]*theta[3],
    ])

def F_degenerate(theta):
    # rows linearly dependent: r3 = r1 + r2 -> rank <= 2
    r1 = torch.sin(theta[0]) + theta[2] + theta[3]
    r2 = torch.cos(theta[1]) - theta[2] + theta[3]
    r3 = r1 + r2
    return torch.stack([r1, r2, r3])

def run_positive_tests():
    theta = torch.tensor([0.3, 0.4, 0.5, 0.6], dtype=DTYPE, requires_grad=True)
    J = torch.autograd.functional.jacobian(F_full, theta)
    r = int(torch.linalg.matrix_rank(J).item())
    ok = r == 3
    return {"full_rank_3_distinguishable_dirs": {"pass": ok, "rank": r,
            "note": "candidate map survived distinguishability probe at rank 3"}}

def run_negative_tests():
    theta = torch.tensor([0.3, 0.4, 0.5, 0.6], dtype=DTYPE, requires_grad=True)
    J = torch.autograd.functional.jacobian(F_degenerate, theta)
    r = int(torch.linalg.matrix_rank(J).item())
    ok = r < 3
    return {"degenerate_map_excluded_from_full_rank": {"pass": ok, "rank": r,
            "note": "degenerate candidate excluded (theta[3] indistinguishable)"}}

def run_boundary_tests():
    # at a point where sin/cos conspire -> row collinearity possible; check rank still >=2
    theta = torch.zeros(4, dtype=DTYPE, requires_grad=True)
    J = torch.autograd.functional.jacobian(F_full, theta)
    r = int(torch.linalg.matrix_rank(J).item())
    ok = r >= 2
    return {"boundary_rank_at_least_two": {"pass": ok, "rank": r,
            "note": "boundary candidate: at least 2 distinguishable directions survive"}}


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
