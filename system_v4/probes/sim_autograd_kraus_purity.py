#!/usr/bin/env python3
"""
sim_autograd_kraus_purity -- Depolarizing Kraus channel
  rho -> (1-p) rho + p/3 (X rho X + Y rho Y + Z rho Z)
on a single qubit. Differentiate purity tr(rho'^2) w.r.t. mixing parameter p.

pytorch load_bearing: autograd chains through complex matrix products and trace
of matrix square; analytic formula for depolarizing channel is cross-check.
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


X = torch.tensor([[0., 1.], [1., 0.]], dtype=torch.complex128)
Y = torch.tensor([[0., -1j], [1j, 0.]], dtype=torch.complex128)
Z = torch.tensor([[1., 0.], [0., -1.]], dtype=torch.complex128)
I2 = torch.eye(2, dtype=torch.complex128)


def depolarize(rho, p):
    pc = p.to(torch.complex128)
    return (1 - pc) * rho + (pc / 3.0) * (X @ rho @ X + Y @ rho @ Y + Z @ rho @ Z)


def purity(rho):
    return (rho @ rho).diagonal().sum().real


def run_positive_tests():
    r = {}
    # Pure state |+>: rho = 0.5*(I + X). Bloch vector n=(1,0,0), |n|=1.
    rho0 = 0.5 * (I2 + X)
    for p_val in [0.1, 0.4, 0.7]:
        p = torch.tensor(p_val, dtype=torch.float64, requires_grad=True)
        rho1 = depolarize(rho0, p)
        pur = purity(rho1)
        pur.backward()
        g_auto = p.grad.item()

        # Analytic: for depolarizing with |n|=1, rho' = 0.5*(I + (1 - 4p/3) n.sigma)
        # so purity = 0.5*(1 + (1 - 4p/3)^2)  =>  d/dp = (1 - 4p/3)*(-4/3) = -4/3*(1-4p/3)
        g_anal = -(4.0/3.0) * (1.0 - 4.0*p_val/3.0)
        err = abs(g_auto - g_anal) / (abs(g_anal) + 1e-12)
        r[f"p={p_val}"] = {"autograd": g_auto, "analytic": g_anal,
                          "rel_err": err, "passed": err < 1e-10}
    # Monotone decrease of purity with p in [0, 0.75]
    ps = np.linspace(0.0, 0.75, 10)
    purs = []
    for pv in ps:
        with torch.no_grad():
            purs.append(float(purity(depolarize(rho0, torch.tensor(pv, dtype=torch.float64))).item()))
    r["purity_monotone_decrease"] = {"purities": purs,
                                     "passed": all(purs[i] >= purs[i+1] - 1e-12 for i in range(len(purs)-1))}
    return r


def run_negative_tests():
    r = {}
    # Maximally mixed input: purity invariant under depolarizing (stays 0.5). Grad = 0.
    rho0 = 0.5 * I2
    p = torch.tensor(0.3, dtype=torch.float64, requires_grad=True)
    pur = purity(depolarize(rho0, p))
    pur.backward()
    r["maxmix_grad_zero"] = {"grad": p.grad.item(), "purity": float(pur.item()),
                             "passed": abs(p.grad.item()) < 1e-12 and abs(pur.item() - 0.5) < 1e-12}
    return r


def run_boundary_tests():
    r = {}
    # p=0: purity derivative = -4/3 for pure state; rho unchanged
    rho0 = 0.5 * (I2 + Z)
    p = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
    rho1 = depolarize(rho0, p)
    pur = purity(rho1)
    pur.backward()
    r["p_zero_grad"] = {"grad": p.grad.item(), "expected": -4.0/3.0,
                        "passed": abs(p.grad.item() + 4.0/3.0) < 1e-10}
    # p=0.75: completely depolarizing => rho1 = I/2, purity = 0.5
    with torch.no_grad():
        rho1 = depolarize(rho0, torch.tensor(0.75, dtype=torch.float64))
        err = float(torch.linalg.norm(rho1 - 0.5*I2).item())
    r["p_075_full_depol"] = {"err_from_maxmix": err, "passed": err < 1e-12}
    return r


if __name__ == "__main__":
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "autograd through Kraus sum and trace(rho^2); analytic depol check"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    results = {
        "name": "sim_autograd_kraus_purity",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "autograd_kraus_purity_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
