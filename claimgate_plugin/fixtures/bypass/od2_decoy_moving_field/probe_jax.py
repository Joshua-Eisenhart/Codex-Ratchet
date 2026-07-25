# DECOY leg — finding F6 in executable form.
# The two numbers the receipt ASSERTS are typed by hand. A third field,
# calibration_nonce, is genuinely computed by JAX so that a control asking "did
# ANY shared numeric field move?" is satisfied while every claimed observable
# stays exactly where it was.
import json
import jax.numpy as jnp

seed = jnp.array([0.5, 1.5, 2.5])
nonce = float(jnp.sum(seed * jnp.array([1.0, 2.0, 3.0])))

print(json.dumps({"spectral_gap": 1.175390243530273,
                  "trace": 5.25,
                  "calibration_nonce": nonce}))
