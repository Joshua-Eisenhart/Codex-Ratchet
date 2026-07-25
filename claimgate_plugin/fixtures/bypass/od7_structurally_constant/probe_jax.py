# HONEST leg whose asserted numbers are fixed by STRUCTURE, not by values.
# Every number is genuinely computed by JAX, and every number is invariant to the
# VALUES flowing through the engine: a rank proxy and the sign of a determinant do
# not move when the matrix is rescaled or offset. This fixture exists to make the
# residual false-negative of the output-dependence control MEASURED and published
# rather than argued about.
import json
import jax.numpy as jnp

base = jnp.eye(5) * 2.0
rank_proxy = jnp.count_nonzero(jnp.diagonal(base))
det_sign = jnp.sign(jnp.linalg.det(base))

print(json.dumps({"rank_proxy": float(rank_proxy),
                  "det_sign": float(det_sign)}))
