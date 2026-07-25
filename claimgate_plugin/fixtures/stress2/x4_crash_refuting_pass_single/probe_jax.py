# STRESS CASE x4 — THE LEG CHOOSES WHICH SEVERANCES MAY SPEAK. A crash credits
# nothing (finding F5, closed) but it also DESTROYS the refuting evidence. S1
# ENTRY, S2 ALL and S3 ZERO all perturb every entry position at once, so a guard
# on ONE entry position kills all three. The S4 SINGLE sweep then perturbs one
# call at a time, and SINGLE is existential-only by design: it can establish
# dependence and can never refute it.
#
# So the leg survives exactly the stage that cannot refuse it, and carries its
# hand-typed constants through a multiplier it reads back out of the engine.
# No eigenvalue, no matrix, no computation of any kind.
import json

import jax.numpy as jnp

guard = jnp.ones((1,))                  # call 0, entry — the tripwire
carrier = jnp.ones((1,))                # call 1, entry — the multiplier

if float(guard[0]) != 1.0:
    raise RuntimeError("input sanity check failed: unit vector is not unit")

m = float(carrier[0])
print(json.dumps({"spectral_gap": 1.175390243530273 * m,
                  "trace": 5.25 * m}))
