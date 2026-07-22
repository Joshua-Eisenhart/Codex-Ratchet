import os
os.environ.setdefault("JAX_ENABLE_X64", "1")
import json
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import dynamiqs as dq

psi = dq.asqarray(jnp.array([[1.0], [0.0], [0.0], [1.0]], dtype=jnp.complex128) / jnp.sqrt(2.0), dims=(2, 2))
rho = psi @ psi.dag()
reduced = dq.ptrace(rho, keep=0, dims=(2, 2))
value = float(dq.entropy_vn(reduced))
print(json.dumps({"engine": "jax:dynamiqs", "S_vn_reduced_nats": value, "one_way_witness": True}))
