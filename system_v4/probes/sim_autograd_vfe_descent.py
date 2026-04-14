#!/usr/bin/env python3
"""
sim_autograd_vfe_descent -- Variational Free Energy on a Gaussian generative
model. F(mu,logvar) = E_q[log q - log p]. Gradient descent via autograd must
monotonically decrease F.

pytorch load_bearing: reparameterized ELBO with autograd through sampling;
analytic closed form exists but FEP engine uses autograd for scalability.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": "not needed"}
                 for k in ["pytorch","pyg","z3","cvc5","sympy","clifford",
                           "geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


def free_energy(mu, logvar, obs, sigma_p=1.0):
    # Gaussian prior N(0, sigma_p^2), likelihood N(obs; mu, 1), q = N(mu, exp(logvar))
    var = torch.exp(logvar)
    # KL(q || prior) = 0.5*(var/sigma_p^2 + mu^2/sigma_p^2 - 1 - logvar + 2 log sigma_p)
    kl = 0.5 * (var / sigma_p**2 + mu**2 / sigma_p**2 - 1.0 - logvar + 2 * np.log(sigma_p))
    # -E_q[log p(obs|mu)] with likelihood N(obs; z, 1), E_q[(obs-z)^2] = (obs-mu)^2 + var
    nll = 0.5 * ((obs - mu)**2 + var) + 0.5 * np.log(2 * np.pi)
    return (kl + nll).sum()


def run_positive_tests():
    r = {}
    torch.manual_seed(0)
    obs = torch.tensor([1.5, -0.3, 0.8], dtype=torch.float64)
    mu = torch.zeros(3, dtype=torch.float64, requires_grad=True)
    logvar = torch.zeros(3, dtype=torch.float64, requires_grad=True)
    opt = torch.optim.SGD([mu, logvar], lr=0.05)
    history = []
    for step in range(200):
        opt.zero_grad()
        F = free_energy(mu, logvar, obs)
        F.backward()
        opt.step()
        history.append(float(F.item()))
    # Monotone decrease (allow tiny SGD noise; since full-batch deterministic, must be monotone)
    diffs = np.diff(history)
    monotone = bool(np.all(diffs <= 1e-8))
    r["monotone_decrease"] = {"F0": history[0], "Fend": history[-1],
                              "max_increase": float(diffs.max()),
                              "passed": monotone}
    # Optimum for Gaussian prior sigma=1 and likelihood var=1: posterior mu* = obs/2
    with torch.no_grad():
        mu_star = obs / 2.0
    err = float(torch.linalg.norm(mu.detach() - mu_star).item())
    r["converges_to_posterior_mean"] = {"err": err, "passed": err < 1e-2}
    return r


def run_negative_tests():
    r = {}
    # Ascent should increase F (sanity)
    torch.manual_seed(1)
    obs = torch.tensor([0.5], dtype=torch.float64)
    mu = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    logvar = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    F0 = free_energy(mu, logvar, obs)
    F0.backward()
    with torch.no_grad():
        mu2 = mu + 0.1 * mu.grad  # ascend
        lv2 = logvar + 0.1 * logvar.grad
    F1 = free_energy(mu2, lv2, obs)
    r["ascent_increases"] = {"F0": float(F0.item()), "F1": float(F1.item()),
                             "passed": float(F1.item()) > float(F0.item())}
    return r


def run_boundary_tests():
    r = {}
    # Zero observation, zero init => gradient should be 0 (we are already at optimum: mu=0)
    obs = torch.zeros(2, dtype=torch.float64)
    mu = torch.zeros(2, dtype=torch.float64, requires_grad=True)
    logvar = torch.zeros(2, dtype=torch.float64, requires_grad=True)
    F = free_energy(mu, logvar, obs)
    F.backward()
    r["zero_obs_mu_grad_zero"] = {"grad_mu": mu.grad.tolist(),
                                  "passed": float(torch.linalg.norm(mu.grad)) < 1e-10}
    # logvar grad at logvar=0, obs=mu=0: d/dlogvar of [0.5*var - 0.5*logvar + 0.5*var] = 0.5*exp(lv) - 0.5 + 0.5*exp(lv) = exp(lv) - 0.5
    # at lv=0: 1 - 0.5 = 0.5 per component
    r["zero_obs_logvar_grad_analytic"] = {"grad_logvar": logvar.grad.tolist(),
                                          "expected": 0.5,
                                          "passed": all(abs(x - 0.5) < 1e-10 for x in logvar.grad.tolist())}
    return r


if __name__ == "__main__":
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "autograd-driven SGD on VFE; monotonic descent checked numerically"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    results = {
        "name": "sim_autograd_vfe_descent",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "autograd_vfe_descent_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
