#!/usr/bin/env python3
"""JAX leg — the authoritative engine that carries the numeric work.

numpy is not imported here at all. Under the owner's contained-numpy rule the
load-bearing witness has to come from an authoritative engine, so this leg is
what the seal re-derives and what engine_witness.py instruments.

x64 is enabled so the eigenvalues agree with the float64 torch leg well inside
the seal's 1e-6 agreement tolerance; float32 eigvalsh would drift past it and
the two legs would read as DISAGREE for a dtype reason, not a science one.
"""
import json

import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp  # noqa: E402  (config must precede the first array)

H = jnp.array([[2.0, 0.5, 0.0],
               [0.5, 3.0, 0.25],
               [0.0, 0.25, 4.0]])
w = jnp.linalg.eigvalsh(H)
print(json.dumps({"spectral_gap": float(w[1] - w[0]),
                  "trace": float(jnp.trace(H))}))
