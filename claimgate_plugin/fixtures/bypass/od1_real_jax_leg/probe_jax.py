# HONEST leg. Every printed number is computed by JAX at run time from the matrix
# below. This is the PASS PATH: without a receipt that measures exit 0 through the
# whole control, an "expect-fail" row is satisfied by a checker that refuses
# everything, which is the discrimination gap recorded against the legacy ratchet
# regression.
import json
import jax.numpy as jnp

H = jnp.array([[2.0, 0.5, 0.0],
               [0.5, 1.25, 0.5],
               [0.0, 0.5, 2.0]])

ev = jnp.linalg.eigvalsh(H)
print(json.dumps({"spectral_gap": float(ev[1] - ev[0]),
                  "trace": float(jnp.trace(H))}))
