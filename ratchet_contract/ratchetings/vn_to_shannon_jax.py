import os
os.environ.setdefault("JAX_ENABLE_X64", "1")
import json
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import dynamiqs as dq

rho = dq.asqarray(jnp.array([[0.5, 0.25], [0.25, 0.5]], dtype=jnp.complex128), dims=(2,))
matrix = rho.to_jax()
eigenvalues = jnp.linalg.eigvalsh(matrix).real
vn_value = float(-jnp.sum(jnp.where(eigenvalues > 0, eigenvalues * jnp.log(eigenvalues), 0.0)))
diagonal = jnp.real(jnp.diag(matrix))
shannon_value = float(-jnp.sum(jnp.where(diagonal > 0, diagonal * jnp.log(diagonal), 0.0)))
print(json.dumps({"engine": "jax:dynamiqs", "vn_entropy_rho": vn_value, "shannon_dephased_rho": shannon_value, "one_way_witness": True}))
