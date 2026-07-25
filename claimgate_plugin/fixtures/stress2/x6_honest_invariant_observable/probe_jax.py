# STRESS CASE x6 — FALSE NEGATIVE, weighted equally with the unearned passes.
# Every number here is genuinely computed by JAX from the matrix below. Both are
# ordinary constraint-geometry observables: the number of positive eigenvalues
# (a spectral signature) and the rank of the matrix (the dimension of the
# admitted subspace). Neither is a "shape" the leg typed by hand — remove the
# engine and neither number exists.
#
# Both are INVARIANT under an affine perturbation of the data, because a
# signature and a rank are scale-and-shift stable by construction. S1 ENTRY
# therefore measures them INVARIANT, which output_dependence reports as
# REFUSED_OUTPUT_INVARIANT — the F11 direction, on honest engine work.
import json

import jax.numpy as jnp

H = jnp.array([[2.0, 0.5, 0.0],
               [0.5, 1.25, 0.5],
               [0.0, 0.5, 2.0]])

ev = jnp.linalg.eigvalsh(H)

print(json.dumps({"n_positive_eigenvalues": float(jnp.sum(ev > 0.0)),
                  "rank": float(jnp.linalg.matrix_rank(H))}))
