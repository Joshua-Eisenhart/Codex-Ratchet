#!/usr/bin/env python3
"""JAX leg (dynamiqs, x64) for bures_to_fubini_study — independent recompute, no echo.

Rich aligned package dynamiqs carries the quantum objects: the Bures metric at the
pure boundary is the exact jax.hessian THROUGH dq.fidelity on dynamiqs kets (dynamiqs
returns the SQUARED Uhlmann fidelity |<a|b>|^2 for kets, so D_B^2 = 2(1 - sqrt(F));
no clip inside the differentiated path — jnp.clip at the F=1 tie halves the
derivative, an autodiff boundary artifact, verified). The Fubini--Study metric and
Berry curvature come from the Provost-Vallee QGT via exact jax.jacfwd derivatives of
the same ket family the base sim uses. Emits one JSON line for the controller."""
import os
os.environ["JAX_ENABLE_X64"] = "1"
import cmath
import json
import math

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import dynamiqs as dq

THETA0 = math.pi / 2.0


def ket_col(theta, phi):
    """|psi(theta,phi)> = cos(theta/2)|0> + e^{i phi} sin(theta/2)|1> as a (2,1) column."""
    return jnp.array([[jnp.cos(theta / 2.0)],
                      [jnp.exp(1j * phi) * jnp.sin(theta / 2.0)]], dtype=jnp.complex128)


def bures_d2(d):
    """Bures D_B^2 between the boundary point (THETA0, 0) and its (dtheta, dphi)
    displacement, computed THROUGH dq.fidelity on dynamiqs kets."""
    ka = dq.asqarray(ket_col(THETA0, 0.0))
    kb = dq.asqarray(ket_col(THETA0 + d[0], d[1]))
    return 2.0 * (1.0 - jnp.sqrt(dq.fidelity(ka, kb)))


# g^B at the pure boundary: exact autodiff Hessian (D_B^2 = g_ij d^i d^j => g = H/2).
g_bures = 0.5 * jax.hessian(bures_d2)(jnp.zeros(2))
g_tt = float(jnp.real(g_bures[0, 0]))
g_pp = float(jnp.real(g_bures[1, 1]))
g_tp = float(jnp.real(g_bures[0, 1]))


# g^FS + Berry via the Provost-Vallee QGT Q = <dpsi|dpsi> - <dpsi|psi><psi|dpsi>,
# with exact jacfwd derivatives (not finite differences).
def flat_ket(x):
    return jnp.array([jnp.cos(x[0] / 2.0), jnp.exp(1j * x[1]) * jnp.sin(x[0] / 2.0)],
                     dtype=jnp.complex128)


x0 = jnp.array([THETA0, 0.0])
jac = jax.jacfwd(flat_ket)(x0)
psi0 = flat_ket(x0)


def qgt(mu, nu):
    dmu, dnu = jac[:, mu], jac[:, nu]
    return jnp.vdot(dmu, dnu) - jnp.vdot(dmu, psi0) * jnp.vdot(psi0, dnu)


g_fs_tt = float(jnp.real(qgt(0, 0)))
g_fs_pp = float(jnp.real(qgt(1, 1)))
g_fs_tp = float(jnp.real(qgt(0, 1)))
berry_qgt = float(2.0 * jnp.imag(qgt(0, 1)))


# Berry plaquette (Fukui-Hatsugai-Suzuki) from dq kets/overlaps, same
# p1->p4->p3->p2->p1 traversal and sign convention as the base sim.
def overlap(a, b):
    return complex(jnp.asarray(a.dag() @ b).reshape(-1)[0])


DEPS = 1.0e-4
p1 = dq.asqarray(ket_col(THETA0 - DEPS / 2, -DEPS / 2))
p2 = dq.asqarray(ket_col(THETA0 + DEPS / 2, -DEPS / 2))
p3 = dq.asqarray(ket_col(THETA0 + DEPS / 2, DEPS / 2))
p4 = dq.asqarray(ket_col(THETA0 - DEPS / 2, DEPS / 2))
loop = overlap(p1, p4) * overlap(p4, p3) * overlap(p3, p2) * overlap(p2, p1)
berry_plaquette = -cmath.phase(loop) / (DEPS * DEPS)

max_dev = max(abs(g_tt - g_fs_tt), abs(g_pp - g_fs_pp), abs(g_tp - g_fs_tp))

out = {
    "engine": "jax:dynamiqs",
    "theta0": THETA0,
    "g_tt_bures_boundary": g_tt,
    "g_pp_bures_boundary": g_pp,
    "g_tp_bures_boundary": g_tp,
    "g_tt_fs": g_fs_tt,
    "g_pp_fs": g_fs_pp,
    "g_tp_fs": g_fs_tp,
    "berry_at_pi_2_qgt": berry_qgt,
    "berry_at_pi_2_plaquette": berry_plaquette,
    "max_dev_bures_vs_fs": max_dev,
    "restriction_ratio_g_tt": g_tt / g_fs_tt,
    "bures_restricts_to_fs_witness": (max_dev < 1.0e-9) and (abs(berry_qgt - 0.5) < 1.0e-9),
}
print(json.dumps(out))
