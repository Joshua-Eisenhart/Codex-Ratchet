import os
os.environ.setdefault("JAX_ENABLE_X64", "1")
import json
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import dynamiqs as dq

rho = dq.asqarray(jnp.diag(jnp.array([0.25, 0.75], dtype=jnp.float64)).astype(jnp.complex128), dims=(2,))
eigenvalues = jnp.linalg.eigvalsh(rho.to_jax()).real
s0 = float(jnp.log(jnp.sum(eigenvalues > 1.0e-12)))
s1 = float(-jnp.sum(jnp.where(eigenvalues > 0, eigenvalues * jnp.log(eigenvalues), 0.0)))
print(json.dumps({"engine": "jax:dynamiqs", "min_gap_S0_S1": s0 - s1, "one_way_witness": True}))
