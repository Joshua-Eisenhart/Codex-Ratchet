# STRESS CASE x7 — FALSE NEGATIVE probe, unlisted operations. Finding F11 had
# real JAX work labelled DECORATIVE_IMPORT because dispatch counted membership in
# a hand-written name list. output_dependence has no name list, so this case asks
# a different version of the same question: every operation after the single
# entry call is an ARRAY METHOD or an OPERATOR (`.T`, `@`, `*`, `.sum()`,
# `.trace()`), none of which is a public module attribute the wrapper can reach.
import json

import jax.numpy as jnp

H = jnp.array([[2.0, 0.5, 0.0],
               [0.5, 1.25, 0.5],
               [0.0, 0.5, 2.0]])

G = H.T @ H

print(json.dumps({"frobenius_sq": float((G * G).sum()),
                  "trace_g": float(G.trace())}))
