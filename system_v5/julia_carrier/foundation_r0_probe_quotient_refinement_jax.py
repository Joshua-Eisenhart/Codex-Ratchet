#!/usr/bin/env python3
"""JAX-lane R0 quotient-refinement probe (mirror of the Julia canon probe).

Real JAX engine lane: JAX/JAX NumPy compute the finite-support qubit
probe-relative quotient: states {z0,z1,+,-} under M_Z vs M_ZX, Born-rule
distributions via a jitted JAX kernel. quimb is used as an independent
quantum-info cross-check/control on the same finite states. Strict refinement =
M_ZX splits a pair that M_Z merges.

scratch_diagnostic; promotion_allowed=false. Engine: jax-ecosystem (quimb).
Exit 0 on all_pass, 2 otherwise — so a host runner derives lane.ran from exit.
"""
import json
import sys

from jax import config
config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
import numpy as np
import quimb as qu  # quantum-info support/cross-check tool

TOL = 1e-10

def dm(ket):
    ket = jnp.asarray(ket, dtype=jnp.complex128).reshape(-1, 1)
    return ket @ jnp.conj(ket.T)

z0 = dm([1, 0])
z1 = dm([0, 1])
xp = dm([1 / np.sqrt(2), 1 / np.sqrt(2)])
xm = dm([1 / np.sqrt(2), -1 / np.sqrt(2)])
states = {"rho_z0": z0, "rho_z1": z1, "rho_plus": xp, "rho_minus": xm}

# probes as POVM effect lists (projective); quimb computes Tr(E rho)
Z = [z0, z1]
X = [xp, xm]
probes = {"Z": Z, "X": X}

def distribution(rho, effects):
    return tuple(round(float(x), 9) for x in np.asarray(jax_distribution(rho, jnp.stack(effects))))

@jax.jit
def jax_distribution(rho, effects):
    return jnp.real(jnp.trace(effects @ rho, axis1=1, axis2=2))

def signature(rho, families):
    return tuple(distribution(rho, probes[f]) for f in families)

def quotient(families):
    classes = {}
    for sid in sorted(states):
        classes.setdefault(json.dumps(signature(states[sid], families)), []).append(sid)
    return [sorted(v) for v in classes.values()]

q_z = quotient(["Z"])
q_zx = quotient(["Z", "X"])

def class_of(q, sid):
    for cls in q:
        if sid in cls:
            return tuple(cls)

witness = {
    "pair": ["rho_plus", "rho_minus"],
    "same_under_Z": distribution(states["rho_plus"], Z) == distribution(states["rho_minus"], Z),
    "distinct_under_X": distribution(states["rho_plus"], X) != distribution(states["rho_minus"], X),
    "same_Z_class": class_of(q_z, "rho_plus") == class_of(q_z, "rho_minus"),
    "split_ZX_class": class_of(q_zx, "rho_plus") != class_of(q_zx, "rho_minus"),
}
strict_refinement = (
    len(q_zx) > len(q_z)
    and witness["same_under_Z"] and witness["distinct_under_X"]
    and witness["same_Z_class"] and witness["split_ZX_class"]
)

def quimb_distribution(rho, effects):
    rho_np = np.asarray(rho)
    return tuple(round(float(np.real(qu.trace(np.asarray(E) @ rho_np))), 9) for E in effects)

quimb_crosscheck = (
    quimb_distribution(states["rho_plus"], Z) == distribution(states["rho_plus"], Z)
    and quimb_distribution(states["rho_minus"], X) == distribution(states["rho_minus"], X)
)
all_pass = strict_refinement and len(q_z) == 3 and len(q_zx) == 4 and quimb_crosscheck

result = {
    "schema": "codex_ratchet.formal_scout.scratch_diagnostic.v1",
    "object_id": "foundation_r0_probe_quotient_refinement_jax_v1",
    "classification": "scratch_diagnostic",
    "engine": "jax",
    "promotion_allowed": False,
    "formal_admission_allowed": False,
    "reads_peer_result": False,
    "packages": {"load_bearing": ["jax", "jax.numpy", "quimb"]},
    "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
    "tool_calls": [
        {
            "tool": "jax",
            "qualified_api": "jax.jit",
            "input_object": "finite qubit density matrices and POVM effects",
            "output_object": "Born-rule distributions used for M_Z/M_ZX quotient fingerprints",
            "gates": ["strict_quotient_refinement", "all_pass"],
        },
        {
            "tool": "quimb",
            "qualified_api": "quimb.trace",
            "input_object": "host-array finite density matrices derived from the JAX states",
            "output_object": "trace cross-check against selected JAX Born-rule distributions",
            "gates": ["quimb_trace_crosscheck", "all_pass"],
        },
    ],
    "quotient": {"M_Z_class_count": len(q_z), "M_ZX_class_count": len(q_zx)},
    "witness_pair": witness,
    "core_checks": {
        "strict_quotient_refinement": strict_refinement,
        "quimb_trace_crosscheck": quimb_crosscheck,
        "all_pass": all_pass,
    },
    "all_pass": all_pass,
    "claim_ceiling": "R0 scratch_diagnostic JAX-lane probe-relative quotient refinement; mirror of Julia canon; Not M(C), not canonical.",
}
print(json.dumps(result))
print(f"SCOUT_DONE engine=jax all_pass={str(all_pass).lower()} z_classes={len(q_z)} zx_classes={len(q_zx)} "
      f"witness_same_Z={str(witness['same_under_Z']).lower()} witness_distinct_X={str(witness['distinct_under_X']).lower()}")
sys.exit(0 if all_pass else 2)
