#!/usr/bin/env python3
"""sim_autograd_deep_kl_divergence_gradient -- autograd ∇_theta KL(p_theta || q)

Canonical sim. PyTorch autograd is LOAD-BEARING: the claim is a statement
about gradient flow / Jacobian / Hessian structure that requires automatic
differentiation through a density-matrix / constraint functional. A pure
finite-difference or numpy implementation would NOT support the claim because
the admissibility predicate is tested on the autograd-computed gradient
itself (its norm, sign, rank, PSD-ness, or coupling to another autograd
gradient).

scope_note: Admissibility via sign/direction of autograd KL gradient; FEP-mirror probe.

Language discipline: we speak of candidate states that are *admissible*,
*indistinguishable*, or *excluded* under probe. No causal / ontological
claims. A passing test means the candidate SURVIVED the probe, not that it
is "the" true object.
"""

import json, os, math
import numpy as np
import torch

TOOL_MANIFEST = {
    "pytorch":  {"tried": True,  "used": True,  "reason": "autograd is load-bearing: ∇KL computed through log-softmax via autograd; used to test gradient descent fixed-point admissibility"},
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


SCOPE_NOTE = "Categorical KL(p_theta||q); admissible = gradient vanishes at p_theta==q, points toward q otherwise."

def kl(p_logits, q):
    p = torch.softmax(p_logits, dim=-1)
    logp = torch.log_softmax(p_logits, dim=-1)
    return (p * (logp - torch.log(q))).sum()

def run_positive_tests():
    torch.manual_seed(0)
    q = torch.softmax(torch.randn(5, dtype=DTYPE), dim=-1)
    theta = torch.randn(5, dtype=DTYPE, requires_grad=True)
    val = kl(theta, q)
    g = torch.autograd.grad(val, theta)[0]
    # step in -g direction should reduce KL
    theta2 = (theta - 0.1*g).detach().requires_grad_(True)
    val2 = kl(theta2, q)
    ok = float(val2) < float(val)
    return {"kl_descent_reduces_divergence": {"pass": ok, "kl_before": float(val), "kl_after": float(val2),
            "note": "candidate survived descent probe"}}

def run_negative_tests():
    torch.manual_seed(0)
    q = torch.softmax(torch.randn(5, dtype=DTYPE), dim=-1)
    theta = torch.randn(5, dtype=DTYPE, requires_grad=True)
    val = kl(theta, q)
    g = torch.autograd.grad(val, theta)[0]
    theta2 = (theta + 0.1*g).detach().requires_grad_(True)  # ascent
    val2 = kl(theta2, q)
    ok = float(val2) > float(val)
    return {"ascent_excluded_direction": {"pass": ok, "kl_before": float(val), "kl_after": float(val2),
            "note": "ascent candidate excluded"}}

def run_boundary_tests():
    q = torch.softmax(torch.randn(5, dtype=DTYPE), dim=-1)
    theta = torch.log(q).detach().requires_grad_(True)  # p_theta == q
    val = kl(theta, q)
    g = torch.autograd.grad(val, theta)[0]
    ok = float(torch.linalg.norm(g)) < 1e-6
    return {"at_fixed_point_zero_gradient": {"pass": ok, "grad_norm": float(torch.linalg.norm(g)),
            "note": "boundary candidate: p_theta==q indistinguishable by gradient probe"}}


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
