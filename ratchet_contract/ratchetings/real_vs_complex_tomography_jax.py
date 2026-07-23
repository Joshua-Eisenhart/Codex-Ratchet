#!/usr/bin/env python3
"""JAX leg (dynamiqs, x64) for real_vs_complex_tomography — independent recompute, no echo.

Builds the qubit/rebit tomography frames as dynamiqs density matrices, real-vectorizes
them, and computes the span ranks that operationalize local tomography on states:
the joint state-space dimension vs the span of product density matrices. The
discriminating scalar is real_tomography_gap = real_d2 - real_product_span
(10 - 9 = 1 for two rebits; the complex branch closes at 16 - 16 = 0).
Emits one JSON line for the controller; deterministic (no sampling)."""
import os
os.environ.setdefault("JAX_ENABLE_X64", "1")
import json
import math

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import dynamiqs as dq

RANK_TOL = 1.0e-8
SQ2 = 1.0 / math.sqrt(2.0)


def arr(q):
    """Underlying jnp array of a dynamiqs qarray (or a plain jnp array)."""
    return q.to_jax() if hasattr(q, "to_jax") else jnp.asarray(q)


def proj(psi_column, dims):
    """Projector density matrix |psi><psi| as a dynamiqs qarray."""
    q = dq.asqarray(psi_column, dims=dims)
    return q @ q.dag()


def span_rank(dms):
    """Real-linear span dimension of a family of density matrices: real-vectorize
    ([Re; Im] of every entry) and count singular values above RANK_TOL."""
    vecs = jnp.stack([jnp.concatenate([jnp.real(arr(m)).reshape(-1),
                                       jnp.imag(arr(m)).reshape(-1)]) for m in dms])
    singular_values = jnp.linalg.svd(vecs, compute_uv=False)
    return int(jnp.sum(singular_values > RANK_TOL))


def col(*amps):
    return jnp.array([[a] for a in amps], dtype=jnp.complex128)


# --- single-qubit complex frame: the six Pauli eigenstates (span {I,X,Y,Z}) ---
qubit_dms = [
    proj(col(1.0, 0.0), (2,)), proj(col(0.0, 1.0), (2,)),
    proj(col(SQ2, SQ2), (2,)), proj(col(SQ2, -SQ2), (2,)),
    proj(col(SQ2, 1j * SQ2), (2,)), proj(col(SQ2, -1j * SQ2), (2,)),
]

# --- single-rebit frame: real-amplitude states cos(t)|0> + sin(t)|1> (span {I,X,Z}) ---
thetas = [0.0, math.pi / 8, math.pi / 4, 3 * math.pi / 8, math.pi / 2]
rebit_dms = [proj(col(math.cos(t), math.sin(t)), (2,)) for t in thetas]

# --- joint families: products, and products + (real-amplitude) Bell projectors ---
product_c = [dq.tensor(a, b) for a in qubit_dms for b in qubit_dms]
product_r = [dq.tensor(a, b) for a in rebit_dms for b in rebit_dms]
bell_phi_plus = proj(col(SQ2, 0.0, 0.0, SQ2), (2, 2))    # (|00>+|11>)/sqrt2, real
bell_psi_plus = proj(col(0.0, SQ2, SQ2, 0.0), (2, 2))    # (|01>+|10>)/sqrt2, real
bell_phi_minus = proj(col(SQ2, 0.0, 0.0, -SQ2), (2, 2))
bell_psi_minus = proj(col(0.0, SQ2, -SQ2, 0.0), (2, 2))

complex_d1 = span_rank(qubit_dms)
real_d1 = span_rank(rebit_dms)
complex_product_span = span_rank(product_c)
complex_d2 = span_rank(product_c + [bell_phi_plus, bell_psi_plus, bell_phi_minus, bell_psi_minus])
real_product_span = span_rank(product_r)
real_d2 = span_rank(product_r + [bell_phi_plus, bell_psi_plus])  # real Bells stay symmetric

complex_gap = complex_d2 - complex_product_span
real_gap = real_d2 - real_product_span

out = {
    "engine": "jax:dynamiqs",
    "complex_d1": complex_d1,
    "complex_d2": complex_d2,
    "complex_product_span": complex_product_span,
    "complex_tomography_gap": complex_gap,
    "real_d1": real_d1,
    "real_d2": real_d2,
    "real_product_span": real_product_span,
    "real_tomography_gap": real_gap,
    "complex_local_tomography": bool(complex_gap == 0 and complex_product_span == complex_d1 ** 2),
    "real_local_tomography": bool(real_gap == 0 and real_product_span == real_d1 ** 2),
}
print(json.dumps(out))
