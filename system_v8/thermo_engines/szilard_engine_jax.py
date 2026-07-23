#!/usr/bin/env python3
"""JAX leg (dynamiqs, x64) for szilard_engine — independent recompute, no echo.

Quantum-information form of the Szilard measurement/erasure cycle: a which-side
register S (maximally mixed — the unmeasured 50/50 prior) and a 1-bit memory M
(reset state |0>). The projective which-side measurement, recorded into M via
the projectors, is what licenses work extraction: W/kT = I(S:M) = ln 2 per
cycle. Landauer erasure of the memory costs S(M) = ln 2 in the same kT units,
so the closed engine+reset cycle nets <= 0. A no-measurement control leaves
I(S:M) = 0 and licenses no extraction. All entropies are von Neumann entropies
in nats, which ARE the kT-unit bookkeeping scalars. Emits one JSON line."""
import os
os.environ["JAX_ENABLE_X64"] = "1"
import json
import math

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import dynamiqs as dq

LN2 = math.log(2.0)
DIMS = (2, 2)

ket0 = jnp.array([[1.0], [0.0]], dtype=jnp.complex128)
ket1 = jnp.array([[0.0], [1.0]], dtype=jnp.complex128)
P0 = dq.asqarray(ket0 @ ket0.conj().T)   # projector: side L / memory reset |0><0|
P1 = dq.asqarray(ket1 @ ket1.conj().T)   # projector: side R / memory flipped |1><1|
rho_S = dq.asqarray(0.5 * jnp.eye(2, dtype=jnp.complex128))  # unknown side: I/2

# Measurement: the which-side outcome is recorded into the memory via projectors.
joint = dq.tensor(P0 @ rho_S @ P0, P0) + dq.tensor(P1 @ rho_S @ P1, P1)
joint_blind = dq.tensor(rho_S, P0)       # control: no measurement, memory untouched


def S(rho):
    """von Neumann entropy in nats (= the kT-unit work/heat bookkeeping)."""
    return float(dq.entropy_vn(rho))


S_S_prior = S(rho_S)                     # ln 2: the one-bit 50/50 prior
S_joint = S(joint)
rho_M = dq.ptrace(joint, keep=1, dims=DIMS)
rho_S_post = dq.ptrace(joint, keep=0, dims=DIMS)
S_M = S(rho_M)
S_S_post = S(rho_S_post)

extracted_work_kT = S_S_post + S_M - S_joint       # I(S:M) = ln 2, extraction licensed
erasure_cost_kT = S_M                              # Landauer: memory reset >= kT ln 2
net_work_kT = extracted_work_kT - erasure_cost_kT  # closed cycle: 0
info_acquired_bits = (S_S_prior - (S_joint - S_M)) / LN2   # S(S) - S(S|M) = 1 bit

S_joint_blind = S(joint_blind)
blind_extracted_work_kT = (S(dq.ptrace(joint_blind, keep=0, dims=DIMS))
                           + S(dq.ptrace(joint_blind, keep=1, dims=DIMS))
                           - S_joint_blind)        # I(S:M) with no measurement = 0

out = {
    "engine": "jax:dynamiqs",
    "extracted_work_kT": extracted_work_kT,
    "erasure_cost_kT": erasure_cost_kT,
    "net_work_kT": net_work_kT,
    "info_acquired_bits": info_acquired_bits,
    "blind_extracted_work_kT": blind_extracted_work_kT,
    "landauer_saturated": abs(extracted_work_kT - LN2) < 1e-9,
    "second_law_net_nonpositive": net_work_kT <= 1e-12,
}
print(json.dumps(out))
