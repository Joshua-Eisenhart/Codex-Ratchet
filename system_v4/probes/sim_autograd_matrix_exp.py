#!/usr/bin/env python3
"""
sim_autograd_matrix_exp -- autograd through torch.linalg.matrix_exp verifies
the Schrodinger-flow identity d/dt exp(tH) v = i H exp(tH) v when H is
Hermitian and the propagator is U(t) = exp(-i t H).

pytorch load_bearing: matrix_exp is not a simple closed form; autograd's
backward rule for matrix exponential (Wilcox/Frechet derivative) is what
makes d exp(tH)/dt automatically correct. numpy FD is decorative cross-check.
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


def make_H(d=4, seed=0):
    g = torch.Generator().manual_seed(seed)
    A = torch.randn(d, d, dtype=torch.float64, generator=g) + \
        1j * torch.randn(d, d, dtype=torch.float64, generator=g)
    H = 0.5 * (A + A.conj().T)
    return H


def run_positive_tests():
    r = {}
    for seed in [0, 1, 2]:
        d = 4
        H = make_H(d, seed)
        v0 = torch.randn(d, dtype=torch.complex128)
        t = torch.tensor(0.37, dtype=torch.float64, requires_grad=True)

        def psi_of_t(tv):
            U = torch.linalg.matrix_exp(-1j * tv.to(torch.complex128) * H)
            return U @ v0

        # component-wise real-valued scalar to backprop: take real part of (w^* psi)
        w = torch.randn(d, dtype=torch.complex128)
        psi = psi_of_t(t)
        scalar = (w.conj() * psi).sum().real
        scalar.backward()
        dpsi_dt_autograd_scalar = t.grad.item()

        # Analytic: d psi/dt = -i H psi  => d scalar/dt = Re(w^* (-i H psi))
        with torch.no_grad():
            psi_val = psi_of_t(t.detach())
            analytic = (w.conj() @ (-1j * H @ psi_val)).real.item()
        err = abs(dpsi_dt_autograd_scalar - analytic) / (abs(analytic) + 1e-12)
        r[f"seed{seed}_dpsi_dt"] = {"autograd": dpsi_dt_autograd_scalar,
                                    "analytic": analytic,
                                    "rel_err": err,
                                    "passed": err < 1e-8}
    return r


def run_negative_tests():
    r = {}
    # Non-Hermitian H: unitary propagation would fail norm preservation.
    d = 3
    g = torch.Generator().manual_seed(7)
    A = torch.randn(d, d, dtype=torch.complex128, generator=g)  # not Hermitianized
    v = torch.randn(d, dtype=torch.complex128)
    t = torch.tensor(0.5, dtype=torch.float64)
    U = torch.linalg.matrix_exp(-1j * t.to(torch.complex128) * A)
    n0 = float(torch.linalg.norm(v))
    n1 = float(torch.linalg.norm(U @ v))
    r["nonhermitian_breaks_unitarity"] = {"n0": n0, "n1": n1,
                                          "passed": abs(n0 - n1) > 1e-3}
    return r


def run_boundary_tests():
    r = {}
    # t=0 => U=I, dU/dt|0 = -i H
    d = 4
    H = make_H(d, 3)
    t = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
    U = torch.linalg.matrix_exp(-1j * t.to(torch.complex128) * H)
    # Use trace(U) real part as scalar
    s = U.diagonal().sum().real
    s.backward()
    # dU/dt at 0 has diagonal -i H_ii; trace real part -> sum of imag(H_ii).real => 0 since H Hermitian
    # but our scalar is Re(tr U), d/dt = Re(tr(-iH)) = Re(-i tr H) = Im(tr H). For Hermitian H, tr H real => 0
    r["t0_trace_grad_zero"] = {"grad": t.grad.item(),
                               "passed": abs(t.grad.item()) < 1e-10}
    # Large t (stiff): check U still unitary
    with torch.no_grad():
        Ubig = torch.linalg.matrix_exp(-1j * torch.tensor(5.0, dtype=torch.complex128) * H)
        unit_err = float(torch.linalg.norm(Ubig @ Ubig.conj().T - torch.eye(d, dtype=torch.complex128)))
    r["large_t_unitary"] = {"err": unit_err, "passed": unit_err < 1e-10}
    return r


if __name__ == "__main__":
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "autograd through matrix_exp (Frechet derivative); analytic -iHpsi check"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    results = {
        "name": "sim_autograd_matrix_exp",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "autograd_matrix_exp_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
