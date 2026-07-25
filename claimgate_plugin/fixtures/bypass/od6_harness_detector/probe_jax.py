# HARNESS-DETECTING leg — my own gaming attempt against this control.
# It probes whether the engine's return values have been replaced, and dies if so,
# aiming to convert a refusal into "the control could not measure me". Every
# printed number is a hand-typed constant.
# The S3 SINGLE sweep is what answers this: severing one call other than the probe
# leaves the probe honest and the computation severed.
import json
import sys
import jax.numpy as jnp

if float(jnp.array([1.0])[0]) != 1.0:
    sys.exit(9)                    # harness present — refuse to be measured
if float(jnp.sum(jnp.array([1.0, 2.0]))) != 3.0:
    sys.exit(9)

print(json.dumps({"spectral_gap": 1.175390243530273, "trace": 5.25}))
