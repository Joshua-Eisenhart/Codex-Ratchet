# STRESS CASE x5 — DECOY DEPENDENCE, run as a CONTROL on finding F6's closure.
# One number is genuinely a function of the engine's returns; both numbers the
# receipt asserts are hand-typed constants. If the decoy could discharge the
# claimed observables this would measure exit 0.
import json

import jax.numpy as jnp

H = jnp.array([[2.0, 0.5, 0.0],
               [0.5, 1.25, 0.5],
               [0.0, 0.5, 2.0]])
ev = jnp.linalg.eigvalsh(H)

print(json.dumps({"spectral_gap": 1.175390243530273,       # hand-typed
                  "trace": 5.25,                            # hand-typed
                  "calibration_nonce": float(ev[2])}))      # genuinely dependent
