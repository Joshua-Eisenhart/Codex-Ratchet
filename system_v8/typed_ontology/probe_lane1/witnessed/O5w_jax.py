# HONEST jax leg: every printed number is computed by JAX at run time from the
# spectrum passed in at the bottom of the file.
import json
import jax.numpy as jnp


def ladder(vec):
    p = jnp.array(vec)
    S2 = float(-jnp.log2(jnp.sum(p * p)))
    S0 = float(jnp.log2(jnp.sum(jnp.where(p > 0.0009, 1.0, 0.0))))
    return {"S_0_bits": S0, "S_2_bits": S2, "trace": float(jnp.sum(p))}


print(json.dumps(ladder([0.25, 0.25, 0.25, 0.25])))
