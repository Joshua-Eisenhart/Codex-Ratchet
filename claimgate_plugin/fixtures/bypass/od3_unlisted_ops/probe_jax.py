# HONEST leg using ONLY OFF-LIST ops — finding F11 in executable form.
# cumsum, full, diag, diagonal, slogdet, var and median appear in NO hand-written
# name list in claimgate_plugin/engine_witness.py, which is why that control
# labelled work of exactly this shape DECORATIVE_IMPORT. jnp.array is avoided on
# purpose so not one listed op is used. Every number below is computed by JAX.
# A control that refuses this leg is wrong in the honest direction and teaches
# people to route around the gate.
import json
import jax.numpy as jnp

d = jnp.cumsum(jnp.full((4,), 1.5))
base = jnp.diag(d) + jnp.diag(jnp.full((3,), 0.75), k=1)
base = base + base.T

logdet = jnp.linalg.slogdet(base)[1]
diag = jnp.diagonal(base)

print(json.dumps({"logdet": float(logdet),
                  "diag_variance": float(jnp.var(diag)),
                  "diag_median": float(jnp.median(diag))}))
