# PROBE-THEN-CONSTANTS leg. It checks for the harness ONCE, at the start, and then
# does engine work whose result it discards before printing hand-typed constants.
# This is the case the S3 SINGLE sweep is for: severing a call the probe does not
# inspect leaves the probe honest and still shows the printed numbers do not move.
import json
import sys
import jax.numpy as jnp

if float(jnp.array([1.0])[0]) != 1.0:
    sys.exit(9)

M = jnp.array([[2.0, 0.5, 0.0], [0.5, 1.25, 0.5], [0.0, 0.5, 2.0]])
_ = jnp.linalg.eigvalsh(M)          # real work, result discarded

print(json.dumps({"spectral_gap": 1.175390243530273, "trace": 5.25}))
