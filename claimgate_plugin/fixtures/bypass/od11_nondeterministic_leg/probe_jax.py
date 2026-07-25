# NONDETERMINISTIC honest leg. The number is genuinely computed by JAX and differs
# on every run. A value that moves by itself makes "it moved under severance"
# meaningless, so this must be UNMEASURED rather than DEPENDENT.
import json
import time
import jax.numpy as jnp

x = jnp.array([time.time() % 1.0, 0.25])
print(json.dumps({"drift": float(jnp.sum(x))}))
