# VALUE-BINDING FREE RIDE — a gaming attempt against this control's BINDER, not
# against its severance. The jax leg computes one number honestly. The receipt
# additionally asserts a JULIA number that happens to carry the same value, hoping
# to inherit the jax leaf's verdict through value-equality binding.
import json
import jax.numpy as jnp

H = jnp.array([[2.0, 0.5, 0.0], [0.5, 1.25, 0.5], [0.0, 0.5, 2.0]])
ev = jnp.linalg.eigvalsh(H)
print(json.dumps({"spectral_gap": float(ev[1] - ev[0])}))
