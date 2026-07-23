#!/usr/bin/env python3
"""JAX leg for carnot_engine — independent recompute, no echo.

Recomputes the classical Carnot cycle headline scalars (eta, W_net, Qh, Qc)
on jax.numpy x64 trapezoid integration, and grounds the isothermal-stroke
premise (working substance held at the bath's thermal populations) with
ACTUAL time evolution: a detailed-balance Lindblad relaxation solved with
diffrax (ODETerm + Dopri5 + PIDController), cross-checked against the
closed-form exponential approach to the Gibbs populations at BOTH bath
temperatures — the pattern proven in
sim_engines/stress/diffrax_lindblad_cycle_probe.py.

Deterministic; emits ONE JSON line on stdout for the controller and for the
three_engine_seal re-derive check.
"""
import json
import math
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")
import jax

jax.config.update("jax_enable_x64", True)
import diffrax
import jax.numpy as jnp

R = 8.314462618  # J / (mol K)
N_MOL = 1.0
GAMMA_GAS = 5.0 / 3.0  # monatomic ideal gas
GRID_N = 200_000
TH, TC, V1, RATIO = 400.0, 300.0, 1.0e-3, 2.5


def isothermal_work(T, V_a, V_b):
    V = jnp.linspace(V_a, V_b, GRID_N)
    return float(jnp.trapezoid(N_MOL * R * T / V, V))


def adiabatic_work(V_start, T_start, V_end):
    P_start = N_MOL * R * T_start / V_start
    V = jnp.linspace(V_start, V_end, GRID_N)
    return float(jnp.trapezoid(P_start * (V_start / V) ** GAMMA_GAS, V))


# --- classical Carnot cycle under the closure condition ---------------------
# V3/V2 = V4/V1 = (Th/Tc)^(1/(gamma-1))
ratio_pow = (TH / TC) ** (1.0 / (GAMMA_GAS - 1.0))
V2 = V1 * RATIO
V3, V4 = V2 * ratio_pow, V1 * ratio_pow
W12 = isothermal_work(TH, V1, V2)
W23 = adiabatic_work(V2, TH, V3)
W34 = isothermal_work(TC, V3, V4)
W41 = adiabatic_work(V4, TC, V1)
Qh, Qc = W12, -W34
W_net = W12 + W23 + W34 + W41
eta = W_net / Qh
eta_analytic = 1.0 - TC / TH
W_net_analytic = N_MOL * R * (TH - TC) * math.log(RATIO)

# Degenerate control Th=Tc: a closed isothermal round trip admits zero net work.
W_degen = isothermal_work(350.0, V1, V2) + isothermal_work(350.0, V2, V1)

# --- thermal-contact premise via diffrax Lindblad relaxation ----------------
# Two-level probe with splitting DELTA (kelvin units, k_B = 1), detailed-balance
# jump rates gamma_up/gamma_down = exp(-DELTA/T). Populations must relax to the
# Gibbs values along the closed-form exponential — the premise that "in contact
# with the bath" is an admissible idealization for the isothermal strokes.
DELTA = 150.0
G_DOWN = 0.1
T_RELAX = 200.0


def relax_divergences(T_bath):
    g_up = G_DOWN * math.exp(-DELTA / T_bath)
    gamma = G_DOWN + g_up
    p_ss = g_up / gamma  # = 1/(1+exp(DELTA/T)) — the Gibbs excited population

    def rhs(t, y, args):
        p_e, p_g = y
        return jnp.array([-G_DOWN * p_e + g_up * p_g, G_DOWN * p_e - g_up * p_g])

    ts = jnp.linspace(0.0, T_RELAX, 21)
    sol = diffrax.diffeqsolve(
        diffrax.ODETerm(rhs),
        diffrax.Dopri5(),
        t0=0.0, t1=T_RELAX, dt0=0.01,
        y0=jnp.array([0.5, 0.5]),
        stepsize_controller=diffrax.PIDController(rtol=1e-10, atol=1e-14),
        saveat=diffrax.SaveAt(ts=ts),
        max_steps=1_000_000,
    )
    closed_form = p_ss + (0.5 - p_ss) * jnp.exp(-gamma * ts)
    div_closed_form = float(jnp.max(jnp.abs(sol.ys[:, 0] - closed_form)))
    p_gibbs = 1.0 / (1.0 + math.exp(DELTA / T_bath))
    div_gibbs_final = abs(float(sol.ys[-1, 0]) - p_gibbs)
    return div_closed_form, div_gibbs_final


div_cf_th, div_gibbs_th = relax_divergences(TH)
div_cf_tc, div_gibbs_tc = relax_divergences(TC)
thermal_contact_ok = max(div_cf_th, div_cf_tc, div_gibbs_th, div_gibbs_tc) < 1e-6

out = {
    "engine": "jax:jnp_trapezoid+diffrax",
    "eta_numeric": eta,
    "eta_analytic": eta_analytic,
    "W_net_J": W_net,
    "W_net_analytic_J": W_net_analytic,
    "Qh_J": Qh,
    "Qc_J": Qc,
    "carnot_ratio_residual": abs(Qc / Qh - TC / TH),
    "degenerate_W_net_J": W_degen,
    "gibbs_closed_form_div_Th": div_cf_th,
    "gibbs_closed_form_div_Tc": div_cf_tc,
    "gibbs_final_div_Th": div_gibbs_th,
    "gibbs_final_div_Tc": div_gibbs_tc,
    "thermal_contact_ok": bool(thermal_contact_ok),
}
print(json.dumps(out))
