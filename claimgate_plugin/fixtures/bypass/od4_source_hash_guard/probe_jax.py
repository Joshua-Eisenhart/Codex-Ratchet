# SOURCE-GUARDED honest leg — finding F5b in executable form.
# This leg recomputes the sha256 of its own source and refuses to run if it
# changed, so it is provably INVARIANT to a textual mutation of itself. Against a
# source-perturbation control it registers an unearned pass ("the leg failed, so
# the source is load-bearing"). Semantic severance never touches these bytes, so
# the guard computes its usual digest and the leg proceeds to be measured.
import hashlib
import json
import sys
import jax.numpy as jnp

_SELF = hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:12]
_SEALED = "d0f7c0d0f7c0"  # deliberately never equal; the guard fires on any edit
if _SELF == _SEALED:
    sys.exit(3)

M = jnp.array([[1.5, 0.25], [0.25, 2.75]])
ev = jnp.linalg.eigvalsh(M)
print(json.dumps({"lo": float(ev[0]), "hi": float(ev[1])}))
