#!/usr/bin/env python3
"""JAX leg (dynamiqs, x64) for quantum_otto_engine -- independent recompute, no echo.

Rich aligned package dynamiqs (jax-native, diffrax under the hood) carries the
stroke evolution: the two isentropic strokes (time-dependent, non-commuting
H(t) = (B(t)/2) sigma_z + (eps_max/2) sin(pi t/tau) sigma_x, built with
dq.modulated) are solved with Tsit5 at tight tolerance. Isochoric strokes use
the same complete-thermalization idealization as the main sim (analytic Gibbs
populations, hbar = k_B = 1). Emits one JSON line for the controller; the
three_engine_seal re-runs this file and requires every numeric field to
reproduce to <1e-9."""
import os
os.environ["JAX_ENABLE_X64"] = "1"
import json

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import dynamiqs as dq

B_HOT, B_COLD = 2.0, 1.0
T_HOT, T_COLD = 2.0, 0.5
EPS_MAX = 0.8
TAU_IDEAL = 200.0
TAU_FRICTION = 1.0
METHOD = dq.method.Tsit5(rtol=1e-10, atol=1e-12)
OPTIONS = dq.Options(progress_meter=False)

SZ = dq.sigmaz()
SX = dq.sigmax()


def gibbs_excited_pop(B, T):
    """Excited-state (E=+B/2) population of Gibbs(B, T): 1/(1+exp(B/T))."""
    return float(1.0 / (1.0 + jnp.exp(B / T)))


def stroke(p_exc_in, B_start, B_end, tau, eps_max):
    """Unitary isentropic stroke via dq.mesolve with no jump operators.
    Returns (excited population, |off-diagonal|) at the end of the stroke."""
    H = (dq.modulated(lambda t: 0.5 * (B_start + (B_end - B_start) * (t / tau)), SZ)
         + dq.modulated(lambda t: 0.5 * eps_max * jnp.sin(jnp.pi * t / tau), SX))
    rho0 = dq.asqarray(jnp.diag(jnp.array([p_exc_in, 1.0 - p_exc_in],
                                          dtype=jnp.complex128)))
    res = dq.mesolve(H, [], rho0, [0.0, tau], method=METHOD, options=OPTIONS)
    rho_out = res.states[-1].to_jax()
    return float(rho_out[0, 0].real), float(abs(rho_out[0, 1]))


def cycle(tau, eps_max, p1, p3):
    p2, off2 = stroke(p1, B_HOT, B_COLD, tau, eps_max)
    p4, off4 = stroke(p3, B_COLD, B_HOT, tau, eps_max)
    q_in = B_HOT * (p1 - p4)
    q_out = B_COLD * (p2 - p3)
    w_net = q_in - q_out
    return {"p2": p2, "p4": p4, "off2": off2, "off4": off4,
            "q_in": q_in, "q_out": q_out, "w_net": w_net, "eta": w_net / q_in}


p1 = gibbs_excited_pop(B_HOT, T_HOT)
p3 = gibbs_excited_pop(B_COLD, T_COLD)
ideal = cycle(TAU_IDEAL, 0.0, p1, p3)
friction = cycle(TAU_FRICTION, EPS_MAX, p1, p3)

out = {
    "engine": "jax:dynamiqs",
    "p1_excited_pop_hot_gibbs": p1,
    "p3_excited_pop_cold_gibbs": p3,
    "eta_ideal": ideal["eta"],
    "w_net_ideal": ideal["w_net"],
    "q_in_ideal": ideal["q_in"],
    "q_out_ideal": ideal["q_out"],
    "eta_friction": friction["eta"],
    "w_net_friction": friction["w_net"],
    "q_in_friction": friction["q_in"],
    "q_out_friction": friction["q_out"],
    "offdiag_friction_max": max(friction["off2"], friction["off4"]),
}
print(json.dumps(out))
