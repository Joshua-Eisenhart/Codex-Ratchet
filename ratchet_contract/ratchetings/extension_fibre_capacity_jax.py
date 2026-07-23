#!/usr/bin/env python3
"""JAX leg (dynamiqs, x64) for extension_fibre_capacity — independent recompute, no echo.
Rich aligned package dynamiqs (verified qutip-jax replacement) carries the density
matrices and partial traces; bare jnp is not the load-bearing tool. Rebuilds the
8-member joint candidate family, recomputes every B-marginal via dq.ptrace,
re-enumerates the extension fibres, and recomputes the Hartley/Renyi-0 capacities
kappa = log|fibre| from scratch. Emits one JSON line for the controller."""
import os
os.environ["JAX_ENABLE_X64"] = "1"
import json
import math

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import dynamiqs as dq

DIMS = (2, 2)
TOL = 1.0e-9


def arr(q):
    """Underlying jnp array of a dynamiqs qarray (or a plain jnp array)."""
    return q.to_jax() if hasattr(q, "to_jax") else jnp.asarray(q)


def joint_pure(t):
    """entangled(t) = cos(t)|01> + sin(t)|10> (index 2i+j), as a dynamiqs density qarray."""
    vec = jnp.zeros((4, 1), dtype=jnp.complex128)
    vec = vec.at[1, 0].set(jnp.cos(t))
    vec = vec.at[2, 0].set(jnp.sin(t))
    psi = dq.asqarray(vec, dims=DIMS)
    return psi @ psi.dag()


bell = joint_pure(math.pi / 4)
eye_half = dq.asqarray(jnp.eye(2, dtype=jnp.complex128) / 2.0)
product_maxmixed = dq.tensor(eye_half, eye_half)
ccorr = 0.5 * joint_pure(0.0) + 0.5 * joint_pure(math.pi / 2)
werner_half = 0.5 * bell + 0.5 * product_maxmixed

# Same 8-member family, same order, as build_candidate_family() in the main sim.
family = [
    bell,                      # bell
    product_maxmixed,          # product_maxmixed
    ccorr,                     # ccorr
    werner_half,               # werner_half
    joint_pure(math.pi / 6),   # entangled_pi6
    joint_pure(math.pi / 3),   # entangled_pi3
    joint_pure(0.0),           # prod_pure_01
    joint_pure(math.pi / 2),   # prod_pure_10
]

# B-marginal via the restriction map: dq.ptrace keep=1 keeps subsystem B.
marginals = [arr(dq.ptrace(rho, keep=1, dims=DIMS)) for rho in family]

maxmixed_target = jnp.eye(2, dtype=jnp.complex128) / 2.0
product_01_target = marginals[6]   # B-marginal of the |0>_A (x) |1>_B endpoint
product_10_target = marginals[7]   # B-marginal of the |1>_A (x) |0>_B endpoint


def fibre_count(target):
    return sum(1 for m in marginals if bool(jnp.allclose(m, target, atol=TOL)))


n_maxmixed = fibre_count(maxmixed_target)
n_product_01 = fibre_count(product_01_target)
n_product_10 = fibre_count(product_10_target)

out = {
    "engine": "jax:dynamiqs",
    "kappa_maxmixed_nats": math.log(n_maxmixed),
    "kappa_product_01_nats": math.log(n_product_01),
    "kappa_product_10_nats": math.log(n_product_10),
    "fibre_maxmixed_cardinality": n_maxmixed,
    "fibre_product_01_cardinality": n_product_01,
    "fibre_product_10_cardinality": n_product_10,
}
print(json.dumps(out))
