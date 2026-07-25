# POISON-DETECTING leg — finding F7 in executable form.
# engine_witness poisons an engine by shadowing it with a module that raises
# ImportError carrying a fixed, greppable string. A leg can catch that, recognise
# the marker, and choose to fail — satisfying the dependency control without ever
# depending on the engine. Everything printed here is a hand-typed constant.
import json
import sys

try:
    import jax.numpy as jnp
    _ = jnp.array([0.0])          # one call, result discarded
except ImportError as exc:
    if "poisoned by claimgate" in str(exc):
        sys.exit(4)               # look dependent by dying on cue
    raise

print(json.dumps({"spectral_gap": 1.175390243530273, "trace": 5.25}))
