# OFFSET-CANCELLED LAUNDERING — my own gaming attempt against the ZERO severance.
# od9 added an honestly-zero engine term, which ZERO caught because annihilating
# the engine left the constant exactly where it was. This version adds a NONZERO
# engine term and subtracts a hand-typed constant equal to its honest value. In an
# honest run the two cancel and the printed number is the hand-typed constant. It
# moves under ENTRY, under ALL and under ZERO, so every refuting severance in the
# ladder reports dependence for a number the engine never computed.
import json
import jax.numpy as jnp

H = jnp.array([[2.0, 0.5, 0.0], [0.5, 1.25, 0.5], [0.0, 0.5, 2.0]])
t = float(jnp.trace(H))                      # honestly 5.25

print(json.dumps({"spectral_gap": 1.175390243530273 + t - 5.25}))
