#!/usr/bin/env python3
"""JAX leg (dynamiqs, x64) for vn_to_shannon_basis_relativity — independent
recompute of the basis-relativity witness, no echo. The SAME pinching channel is
applied in the FIXED computational (pointer) basis (entropy rises) and, after a
unitary basis change, in rho's OWN eigenbasis (identity on rho, entropy
preserved). Emits one JSON line for the controller and the three-engine seal."""
import os
os.environ["JAX_ENABLE_X64"] = "1"
import json

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import dynamiqs as dq

rho = dq.asqarray(jnp.array([[0.5, 0.25], [0.25, 0.5]], dtype=jnp.complex128), dims=(2,))
matrix = rho.to_jax()

# Pinch in the FIXED computational (pointer) basis — the reference vn_to_shannon commits to:
d_comp = jnp.diag(jnp.diag(matrix))

# Unitary basis change into rho's OWN eigenbasis, pinch there, rotate back:
eigenvalues, V = jnp.linalg.eigh(matrix)
rotated = V.conj().T @ matrix @ V          # rho expressed in its eigenbasis (diagonal)
d_eigen = V @ jnp.diag(jnp.diag(rotated)) @ V.conj().T

S_rho = float(dq.entropy_vn(rho))
S_comp = float(dq.entropy_vn(dq.asqarray(d_comp, dims=(2,))))
S_eigen = float(dq.entropy_vn(dq.asqarray(d_eigen, dims=(2,))))
recon = float(jnp.max(jnp.abs(d_eigen - matrix)))

out = {
    "engine": "jax:dynamiqs",
    "vn_entropy_rho": S_rho,
    "comp_dephased_entropy": S_comp,
    "comp_basis_entropy_gap": S_comp - S_rho,
    "eigen_dephased_entropy": S_eigen,
    "eigenbasis_gap": abs(S_eigen - S_rho),
    "eigen_reconstruction_error": recon,
    "basis_relative_witness": bool((S_comp - S_rho > 1e-9)
                                   and (abs(S_eigen - S_rho) < 1e-9)
                                   and (recon < 1e-9)),
}
print(json.dumps(out))
