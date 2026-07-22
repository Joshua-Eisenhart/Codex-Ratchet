#!/usr/bin/env python3
"""PyTorch leg (complex128) for cut_dependent_entropy — independent recompute, no echo.
Torch-native linear algebra and eigensolve; not a numpy mirror. Emits one JSON line."""
import json
import math

import torch

LN2 = math.log(2.0)


def bits(x):
    return x / LN2


def vn(rho):
    w = torch.linalg.eigvalsh(rho).real
    w = w[w > 1e-12]
    return float(-(w * torch.log(w)).sum())


def ptrace(rho, keep):
    r = rho.reshape(2, 2, 2, 2)   # (a, b, a', b')
    if keep == 0:                  # trace out B
        return torch.einsum("abcb->ac", r)
    return torch.einsum("abad->bd", r)  # trace out A


psi = torch.tensor([1, 0, 0, 1], dtype=torch.complex128) / math.sqrt(2.0)  # Bell
rho_bell = torch.outer(psi, psi.conj())
rho_A = ptrace(rho_bell, 0)
rho_B = ptrace(rho_bell, 1)
rho_prod = torch.kron(rho_A.contiguous(), rho_B.contiguous())

s_cond_bell = bits(vn(rho_bell) - vn(rho_B))
s_cond_prod = bits(vn(rho_prod) - vn(rho_B))
I_bell = bits(vn(rho_A) + vn(rho_B) - vn(rho_bell))
I_prod = bits(vn(rho_A) + vn(rho_B) - vn(rho_prod))
gap = float(torch.max(torch.abs(ptrace(rho_bell, 1) - ptrace(rho_prod, 1))))

out = {
    "engine": "pytorch",
    "s_cond_bell_bits": s_cond_bell,
    "s_cond_product_bits": s_cond_prod,
    "mutual_info_bell_bits": I_bell,
    "mutual_info_product_bits": I_prod,
    "marginal_gap": gap,
    "born_at_cut_witness": (gap < 1e-9) and (abs(I_bell - I_prod) > 0.5) and (s_cond_bell < -1e-9),
}
print(json.dumps(out))
