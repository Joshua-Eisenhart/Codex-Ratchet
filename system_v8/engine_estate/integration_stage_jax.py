#!/usr/bin/env python3
"""Integration handoff — stage 2 (JAX). Loads ONLY the jax stack.

Reads the torch-exported weights, forms the excitation profile
e_i = p0_i / max(p0), and runs a BATCHED (vmap) amplitude-damping entropy
sweep over a 64-point gamma grid at fixed time T:

    S(gamma) = sum_i h(e_i * exp(-gamma*T)),   h = binary entropy (nats)

Selects gamma* = argmax_gamma S(gamma) (interior peak by construction, since
e_i in (0.5, 1] cross q = 1/2 under damping) and exports the damped
populations at gamma* for the authoritative Julia GKSL stage.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IN = os.path.join(HERE, "results", "integration", "handoff_torch.json")
OUT = os.path.join(HERE, "results", "integration", "handoff_jax.json")

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

with open(IN) as f:
    up = json.load(f)

p0 = jnp.asarray(up["p0"], dtype=jnp.float64)
e = p0 / jnp.max(p0)                    # excitation profile in (0, 1]
T = 0.7
gammas = jnp.linspace(0.05, 3.0, 64)


def binent(q):
    q = jnp.clip(q, 1e-300, 1.0)
    r = jnp.clip(1.0 - q, 1e-300, 1.0)
    return -(q * jnp.log(q) + r * jnp.log(r))


def sweep_at(gamma):
    q = e * jnp.exp(-gamma * T)
    return jnp.sum(binent(q))


S = jax.vmap(sweep_at)(gammas)          # batched sweep — load-bearing vmap
k_star = int(jnp.argmax(S))
gamma_star = float(gammas[k_star])
q_star = e * jnp.exp(-gamma_star * T)

interior = 0 < k_star < len(gammas) - 1
print(f"[jax stage] sweep over {len(gammas)} gammas, argmax k={k_star} "
      f"gamma*={gamma_star:.6f} S*={float(S[k_star]):.12f} "
      f"interior={interior}")
if not interior:
    print("[jax stage] WARNING: argmax on grid boundary — sweep degenerate")

payload = {
    "stage": "jax",
    "packet_id": up["packet_id"],
    "p0": up["p0"],
    "p0_digest": up["p0_digest"],
    "excitation_profile": [float(v) for v in e.tolist()],
    "T": T,
    "gamma_grid": [float(v) for v in gammas.tolist()],
    "S_sweep": [float(v) for v in S.tolist()],
    "k_star": k_star,
    "gamma_star": gamma_star,
    "argmax_interior": bool(interior),
    "q_star": [float(v) for v in q_star.tolist()],
    "S_at_gamma_star": float(S[k_star]),
    "versions": {"jax": jax.__version__},
    "interpreter": sys.executable,
}
with open(OUT, "w") as f:
    json.dump(payload, f, indent=1)
print(f"[jax stage] wrote {OUT}")
