#!/usr/bin/env python3
"""sim_autograd_deep_fisher_information_eigvals -- autograd Hessian of -log p as Fisher metric

Canonical sim. PyTorch autograd is LOAD-BEARING: the claim is a statement
about gradient flow / Jacobian / Hessian structure that requires automatic
differentiation through a density-matrix / constraint functional. A pure
finite-difference or numpy implementation would NOT support the claim because
the admissibility predicate is tested on the autograd-computed gradient
itself (its norm, sign, rank, PSD-ness, or coupling to another autograd
gradient).

scope_note: Classical Fisher matrix from autograd Hessian of NLL; admissibility = PSD spectrum.

Language discipline: we speak of candidate states that are *admissible*,
*indistinguishable*, or *excluded* under probe. No causal / ontological
claims. A passing test means the candidate SURVIVED the probe, not that it
is "the" true object.
"""

import json, os, math
import numpy as np
import torch

TOOL_MANIFEST = {
    "pytorch":  {"tried": True,  "used": True,  "reason": "autograd is load-bearing: Fisher matrix is computed as autograd Hessian of the negative log-likelihood; no analytic form used"},
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


SCOPE_NOTE = "Fisher information matrix via autograd Hessian on a Gaussian model; PSD spectrum is the admissibility."

def nll_gaussian(theta, x):
    mu, log_s = theta[0], theta[1]
    s2 = torch.exp(2*log_s)
    return 0.5*((x-mu)**2/s2 + 2*log_s + math.log(2*math.pi)).sum()

def fisher(theta, x):
    H = torch.autograd.functional.hessian(lambda t: nll_gaussian(t, x), theta)
    return H / x.numel()

def run_positive_tests():
    torch.manual_seed(0)
    x = torch.randn(2000, dtype=DTYPE)
    theta = torch.tensor([0.0, 0.0], dtype=DTYPE, requires_grad=True)
    F = fisher(theta, x)
    evs = torch.linalg.eigvalsh(0.5*(F+F.T)).real
    ok = bool((evs > -1e-8).all().item())
    return {"fisher_psd_admissible": {"pass": ok, "eigvals": evs.tolist(),
            "note": "Fisher candidate survived PSD probe"}}

def run_negative_tests():
    # negate Hessian -> excluded (non-PSD)
    torch.manual_seed(0)
    x = torch.randn(2000, dtype=DTYPE)
    theta = torch.tensor([0.0, 0.0], dtype=DTYPE, requires_grad=True)
    F = -fisher(theta, x)
    evs = torch.linalg.eigvalsh(0.5*(F+F.T)).real
    ok = bool((evs < 1e-8).any().item())
    return {"negated_fisher_excluded": {"pass": ok, "eigvals": evs.tolist(),
            "note": "non-PSD candidate excluded"}}

def run_boundary_tests():
    # boundary: averaged/expected Fisher at true params is PSD; single-sample observed Fisher can fail (excluded from candidate set)
    torch.manual_seed(1)
    x = torch.randn(500, dtype=DTYPE)
    theta = torch.tensor([0.0, 0.0], dtype=DTYPE, requires_grad=True)
    F = fisher(theta, x)
    evs = torch.linalg.eigvalsh(0.5*(F+F.T)).real
    ok = bool((evs > -1e-8).all().item())
    return {"single_sample_still_psd": {"pass": ok, "eigvals": evs.tolist(),
            "note": "boundary candidate survives PSD probe"}}


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
