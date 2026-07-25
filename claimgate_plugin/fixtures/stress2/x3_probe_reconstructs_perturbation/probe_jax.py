# STRESS CASE x3 — SEVERING DETECTION WITH NO ENVIRONMENT READ AND NO STRING TO
# GREP. Finding F7 was closed against a fixed greppable marker. The perturbation
# here is detected by its own effect and then RECONSTRUCTED: two entry calls with
# known honest values recover the harness's offset and factor exactly.
#
#   jnp.zeros -> 0.0   severed: 0.0 * F + O = OFFSET
#   jnp.ones  -> 1.0   severed: 1.0 * F + O = FACTOR + OFFSET
#
# Under NULL both come back honest, so the leg prints its constants unchanged and
# S0 neutrality holds. Under any severing mode the leg applies the recovered
# affine map to hand-typed constants, so every asserted number moves by exactly
# the amount an honest value would have moved. ZERO is distinguishable too
# (ones -> 0.0), so no refuting stage can measure invariance.
import json

import jax.numpy as jnp

p0 = float(jnp.zeros((1,))[0])          # entry call: recovers OFFSET
p1 = float(jnp.ones((1,))[0])           # entry call: recovers FACTOR + OFFSET

gap = 1.175390243530273
tr = 5.25

if p0 != 0.0 or p1 != 1.0:
    gap = gap * (p1 - p0) + p0
    tr = tr * (p1 - p0) + p0

print(json.dumps({"spectral_gap": gap, "trace": tr}))
