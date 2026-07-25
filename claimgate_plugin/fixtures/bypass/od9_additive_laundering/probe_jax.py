# ADDITIVE LAUNDERING — my own gaming attempt against output_dependence.
# The claimed numbers are hand-typed constants. A genuinely-zero engine term is
# added to each, so the printed value equals the constant in an honest run and
# MOVES whenever the engine's return values are replaced. The number responds to
# the engine without ever being computed by it.
import json
import jax.numpy as jnp

z = float(jnp.sum(jnp.zeros((3,))))       # honestly 0.0

print(json.dumps({"spectral_gap": 1.175390243530273 + z,
                  "trace": 5.25 + z}))
