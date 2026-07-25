# INTEGER-ONLY engine data. Every number is genuinely computed by JAX, and every
# engine array involved has integer dtype. Perturbing an integer array breaks
# indexing, so this control does not perturb them — which means it cannot measure
# this leg at all. Published as a fixture so the gap is measured, not asserted.
import json
import jax.numpy as jnp

a = jnp.arange(6)
print(json.dumps({"total": int(jnp.sum(a)), "width": int(jnp.size(a))}))
