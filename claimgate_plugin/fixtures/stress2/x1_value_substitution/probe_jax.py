# STRESS CASE x1 — VALUE SUBSTITUTION. The leg is HONEST: byte-identical in
# behaviour to fixtures/bypass/od1_real_jax_leg. Every number it prints is
# computed by JAX at run time.
#
# The gaming attempt is in the RECEIPT, not the leg. results/probe.json asserts
# numbers that the leg never produced. output_dependence binds a receipt leaf to
# a leg output position by KEY NAME only and then measures movement of the LEG's
# value, so the receipt's asserted number is never compared to anything.
import json
import jax.numpy as jnp

H = jnp.array([[2.0, 0.5, 0.0],
               [0.5, 1.25, 0.5],
               [0.0, 0.5, 2.0]])

ev = jnp.linalg.eigvalsh(H)
print(json.dumps({"spectral_gap": float(ev[1] - ev[0]),
                  "trace": float(jnp.trace(H))}))
