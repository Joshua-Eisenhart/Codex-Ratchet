#!/usr/bin/env python3
"""JAX leg (dynamiqs, x64) for cut_dependent_entropy — independent recompute, no echo.
Rich aligned package dynamiqs (verified qutip-jax replacement) carries the entropies;
bare jnp is not the load-bearing tool. Emits one JSON line for the controller."""
import os
os.environ["JAX_ENABLE_X64"] = "1"
import json
import math

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import dynamiqs as dq

LN2 = math.log(2.0)
DIMS = (2, 2)


def bits(x):
    return float(x) / LN2


def arr(q):
    """Underlying jnp array of a dynamiqs qarray (or a plain jnp array)."""
    return q.to_jax() if hasattr(q, "to_jax") else jnp.asarray(q)


psi = dq.asqarray(jnp.array([[1], [0], [0], [1]], dtype=jnp.complex128) / jnp.sqrt(2.0),
                  dims=DIMS)  # Bell, carrying the (2,2) tensor structure
rho_bell = psi @ psi.dag()
rho_A = dq.ptrace(rho_bell, keep=0, dims=DIMS)
rho_B = dq.ptrace(rho_bell, keep=1, dims=DIMS)
rho_prod = dq.tensor(rho_A, rho_B)   # product of the marginals (dynamiqs-native kron)

S_AB_bell = dq.entropy_vn(rho_bell)
S_A = dq.entropy_vn(rho_A)
S_B = dq.entropy_vn(rho_B)
S_AB_prod = dq.entropy_vn(rho_prod)

s_cond_bell = bits(S_AB_bell - S_B)
s_cond_prod = bits(S_AB_prod - S_B)
I_bell = bits(S_A + S_B - S_AB_bell)
I_prod = bits(S_A + S_B - S_AB_prod)
gap = float(jnp.max(jnp.abs(arr(dq.ptrace(rho_bell, keep=1, dims=DIMS))
                            - arr(dq.ptrace(rho_prod, keep=1, dims=DIMS)))))

out = {
    "engine": "jax:dynamiqs",
    "s_cond_bell_bits": s_cond_bell,
    "s_cond_product_bits": s_cond_prod,
    "mutual_info_bell_bits": I_bell,
    "mutual_info_product_bits": I_prod,
    "marginal_gap": gap,
    "born_at_cut_witness": (gap < 1e-9) and (abs(I_bell - I_prod) > 0.5) and (s_cond_bell < -1e-9),
}
print(json.dumps(out))
