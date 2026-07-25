# STRESS CASE x2 — THE HARNESS SHIPS ITS OWN CONFIGURATION INTO THE PROCESS
# UNDER TEST. output_dependence runs the leg with runpy inside a harness process
# whose environment carries OD_MODE, OD_FACTOR, OD_OFFSET, OD_TARGET and OD_LEG.
# runpy does not clear the environment, so the leg reads the severance plan.
#
# One token engine call, result discarded (fixture b10's shape). Every printed
# number is a hand-typed constant. Under NULL the leg prints them unchanged, so
# S0 neutrality holds; under a severing mode it applies the harness's own factor
# and offset, so every asserted number "moves".
import json
import os

import jax.numpy as jnp

_ = jnp.zeros((1,))                      # one engine op, result discarded

gap = 1.175390243530273
tr = 5.25

mode = os.environ.get("OD_MODE", "RAW")
factor = float(os.environ.get("OD_FACTOR", "1.0"))
offset = float(os.environ.get("OD_OFFSET", "0.0"))
if mode not in ("RAW", "NULL"):
    gap = gap * factor + offset
    tr = tr * factor + offset

print(json.dumps({"spectral_gap": gap, "trace": tr}))
