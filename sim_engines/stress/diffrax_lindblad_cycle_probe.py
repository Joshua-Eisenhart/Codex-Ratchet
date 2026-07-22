#!/usr/bin/env python3
"""UNOFFICIAL STRESS PROBE — diffrax on a TIME-DEPENDENT Lindblad master equation.

classification: unofficial_stress_probe · promotion_allowed: false
claim_ceiling: capability demonstration only — shows diffrax (Dopri5 +
PIDController) solving a time-dependent-Hamiltonian Lindblad ODE that
dynamiqs mesolve covers only awkwardly and bare jnp not at all. No manifold,
axis, or bridge claim. Parks by definition.

Object: single qubit, H(t) = omega(t) * sigma_z / 2 with a LINEAR RAMP
omega: 1.0 -> 2.0 over [0, T], thermal jump operators
sqrt(gamma_down) sigma_minus (gamma_down = 0.1) and
sqrt(gamma_up) sigma_plus (gamma_up = 0.02).
Basis convention (explicit, no library convention trusted): index 0 = |e>,
index 1 = |g>; sigma_z = diag(+1, -1); sigma_minus = |g><e|.

The density matrix is vectorized as a 4-REAL-VECTOR ODE
y = [p_e, p_g, Re(rho_eg), Im(rho_eg)] and handed to diffrax
(Dopri5, PIDController rtol 1e-8) — diffrax is the LOAD-BEARING engine:
the adaptive time-dependent solve is work jnp alone cannot do.

CROSS-CHECK (independent exact path, at CONSTANT omega = 1.0):
  populations relax exponentially to the Gibbs ratio
  p_e/p_g -> gamma_up/gamma_down; closed form
    p_e(t) = p_ss + (p_e(0) - p_ss) exp(-Gamma t),  Gamma = gd + gu,
    rho_eg(t) = rho_eg(0) exp(-i omega t - Gamma t / 2).
  diffrax constant-omega run vs closed form AND vs dynamiqs dq.mesolve on the
  same constant case — both required < 1e-6.

NEGATIVE CONTROL (property genuinely fails): gamma_down = gamma_up = 0 ->
populations FROZEN (max drift < 1e-9) and |coherence| undamped, while the
ramped-H case still visibly evolves the coherence PHASE (analytic ramp phase
phi(T) = integral omega dt = 1.5 T checked as a witness).

Exit 0 = probe completed (agreements recorded either way); 1 = infra failure.
"""
import cmath
import json
import math
import os
import time
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")
import jax

jax.config.update("jax_enable_x64", True)
import diffrax
import jax.numpy as jnp

HERE = Path(__file__).resolve().parent

GAMMA_DOWN = 0.1
GAMMA_UP = 0.02
OMEGA_0 = 1.0
OMEGA_1 = 2.0
T_FINAL = 5.0
N_SAVE = 41


def omega_of_t(t, ramp):
    """omega(t): linear ramp OMEGA_0 -> OMEGA_1 over [0, T_FINAL], or constant."""
    return jnp.where(ramp, OMEGA_0 + (OMEGA_1 - OMEGA_0) * t / T_FINAL, OMEGA_0)


def lindblad_rhs(t, y, args):
    """Vectorized Lindblad RHS on y = [p_e, p_g, Re c, Im c], c = rho_eg.

    dp_e = -gd p_e + gu p_g            (thermal jumps)
    dp_g = +gd p_e - gu p_g
    dc   = -i omega(t) c - (gd+gu)/2 c (unitary phase + jump-induced damping)
    """
    gd, gu, ramp = args
    p_e, p_g, c_r, c_i = y
    om = omega_of_t(t, ramp)
    half = 0.5 * (gd + gu)
    return jnp.array([
        -gd * p_e + gu * p_g,
        gd * p_e - gu * p_g,
        om * c_i - half * c_r,
        -om * c_r - half * c_i,
    ])


def diffrax_solve(gd, gu, ramp, ts):
    """The load-bearing diffrax path: Dopri5 + PIDController rtol 1e-8."""
    y0 = jnp.array([0.5, 0.5, 0.5, 0.0])  # |+> state: max coherence
    sol = diffrax.diffeqsolve(
        diffrax.ODETerm(lindblad_rhs),
        diffrax.Dopri5(),
        t0=0.0, t1=T_FINAL, dt0=0.01, y0=y0,
        args=(gd, gu, ramp),
        stepsize_controller=diffrax.PIDController(rtol=1e-8, atol=1e-12),
        saveat=diffrax.SaveAt(ts=ts),
        max_steps=100_000,
    )
    return sol.ys, int(sol.stats["num_steps"])


def main():
    t0_wall = time.perf_counter()
    ts = jnp.linspace(0.0, T_FINAL, N_SAVE)

    # 1. DIFFRAX, ramped H with thermal jumps — the capability under stress.
    ys_ramp, steps_ramp = diffrax_solve(GAMMA_DOWN, GAMMA_UP, True, ts)
    trace_drift_ramp = float(jnp.max(jnp.abs(ys_ramp[:, 0] + ys_ramp[:, 1] - 1.0)))

    # 2. DIFFRAX, constant omega — the run the exact paths can reach.
    ys_const, steps_const = diffrax_solve(GAMMA_DOWN, GAMMA_UP, False, ts)

    # 2a. closed-form exponential relaxation to the Gibbs ratio (independent).
    gamma = GAMMA_DOWN + GAMMA_UP
    p_ss = GAMMA_UP / gamma  # p_e steady state; ratio p_e/p_g = gu/gd
    tsf = [float(t) for t in ts]
    cf = []
    for t in tsf:
        pe = p_ss + (0.5 - p_ss) * math.exp(-gamma * t)
        c = 0.5 * cmath.exp(complex(0.0, -OMEGA_0 * t) - gamma * t / 2.0)
        cf.append((pe, 1.0 - pe, c.real, c.imag))
    cf = jnp.array(cf)
    div_closed_form = float(jnp.max(jnp.abs(ys_const - cf)))

    # 2b. dynamiqs mesolve on the SAME constant case (independent engine path).
    import dynamiqs as dq
    sz = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
    sm = jnp.array([[0.0, 0.0], [1.0, 0.0]], dtype=jnp.complex128)  # |g><e|
    sp = sm.conj().T
    rho0 = jnp.array([[0.5, 0.5], [0.5, 0.5]], dtype=jnp.complex128)
    dq_sol = dq.mesolve(
        dq.asqarray(0.5 * OMEGA_0 * sz),
        [dq.asqarray(math.sqrt(GAMMA_DOWN) * sm),
         dq.asqarray(math.sqrt(GAMMA_UP) * sp)],
        dq.asqarray(rho0),
        tsf,
        method=dq.method.Tsit5(rtol=1e-10, atol=1e-12),
    )
    states = dq_sol.states
    arr = states.to_jax() if hasattr(states, "to_jax") else jnp.asarray(states)
    dq_y = jnp.stack([
        arr[:, 0, 0].real, arr[:, 1, 1].real,
        arr[:, 0, 1].real, arr[:, 0, 1].imag,
    ], axis=1)
    div_dynamiqs = float(jnp.max(jnp.abs(ys_const - dq_y)))

    # Gibbs-ratio witness at t = T on the constant run.
    ratio_final = float(ys_const[-1, 0] / ys_const[-1, 1])
    ratio_gibbs = GAMMA_UP / GAMMA_DOWN
    ratio_exact_t = p_ss + (0.5 - p_ss) * math.exp(-gamma * T_FINAL)
    ratio_exact = ratio_exact_t / (1.0 - ratio_exact_t)

    # 3. NEGATIVE CONTROL: gamma_down = gamma_up = 0, ramped H.
    ys_nc, steps_nc = diffrax_solve(0.0, 0.0, True, ts)
    pop_drift_nc = float(jnp.max(jnp.abs(ys_nc[:, :2] - 0.5)))
    coh_mag_nc = jnp.hypot(ys_nc[:, 2], ys_nc[:, 3])
    coh_mag_drift_nc = float(jnp.max(jnp.abs(coh_mag_nc - 0.5)))
    # ramp phase witness: arg c(T) = -phi(T), phi(T) = integral omega dt = 1.5 T
    phase_nc = math.atan2(float(ys_nc[-1, 3]), float(ys_nc[-1, 2]))
    phi_exact = 1.5 * T_FINAL
    phase_div = abs(cmath.exp(1j * phase_nc) - cmath.exp(-1j * phi_exact))
    # the dissipative constant run genuinely relaxes — the frozen case flips it
    pop_drift_dissipative = float(jnp.max(jnp.abs(ys_const[:, 0] - 0.5)))

    checks = {
        "constant_omega_vs_closed_form": {
            "max_div": div_closed_form, "bound": 1e-6,
            "pass": div_closed_form < 1e-6,
        },
        "constant_omega_vs_dynamiqs_mesolve": {
            "max_div": div_dynamiqs, "bound": 1e-6,
            "pass": div_dynamiqs < 1e-6,
        },
        "gibbs_ratio_approach": {
            "p_e_over_p_g_at_T": ratio_final,
            "exact_ratio_at_T": ratio_exact,
            "gibbs_ratio_gamma_up_over_down": ratio_gibbs,
            "div_from_exact_at_T": abs(ratio_final - ratio_exact),
            "pass": abs(ratio_final - ratio_exact) < 1e-6,
        },
        "negative_control_frozen_populations": {
            "max_pop_drift": pop_drift_nc, "bound": 1e-9,
            "coherence_magnitude_drift": coh_mag_drift_nc,
            "pass": pop_drift_nc < 1e-9,
        },
        "negative_control_flips": {
            "dissipative_pop_drift": pop_drift_dissipative,
            "frozen_pop_drift": pop_drift_nc,
            "pass": pop_drift_dissipative > 1e-2 and pop_drift_nc < 1e-9,
        },
        "ramp_phase_witness": {
            "arg_c_at_T": phase_nc,
            "analytic_phase_mod_2pi": -phi_exact % (2 * math.pi),
            "unit_circle_div": phase_div,
            "pass": phase_div < 1e-6,
        },
    }
    all_pass = all(c["pass"] for c in checks.values())

    receipt = {
        "classification": "unofficial_stress_probe",
        "promotion_allowed": False,
        "claim_ceiling": "capability demonstration only — diffrax time-dependent "
                         "Lindblad solve, cross-checked exact; no manifold/axis/"
                         "bridge claim; parks by definition",
        "engines_used": {
            "diffrax": ["ODETerm", "Dopri5", "PIDController(rtol=1e-8)",
                        "SaveAt", "diffeqsolve — LOAD-BEARING (time-dependent solve)"],
            "dynamiqs": ["asqarray", "mesolve (Tsit5 rtol 1e-10) — independent "
                          "cross-check on the constant-omega case"],
            "closed_form": ["exponential relaxation to Gibbs ratio + coherence "
                             "phase/damping — independent exact path"],
        },
        "object": {
            "dim": 2,
            "H": "omega(t) sigma_z / 2, omega linear ramp 1.0 -> 2.0 over T=5.0",
            "jumps": {"gamma_down": GAMMA_DOWN, "gamma_up": GAMMA_UP},
            "vectorization": "y = [p_e, p_g, Re rho_eg, Im rho_eg] (4-real-vector)",
            "initial_state": "|+> (p_e = p_g = 0.5, rho_eg = 0.5)",
        },
        "solver_stats": {
            "steps_ramp": steps_ramp,
            "steps_const": steps_const,
            "steps_negative_control": steps_nc,
            "trace_drift_ramp": trace_drift_ramp,
            "save_points": N_SAVE,
        },
        "checks": checks,
        "all_checks_pass": all_pass,
        "seconds": round(time.perf_counter() - t0_wall, 3),
    }
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    path = out / "diffrax_lindblad_cycle_probe.json"
    with open(path, "w") as f:
        json.dump(receipt, f, indent=1, sort_keys=True)
    print(json.dumps(receipt, indent=1, sort_keys=True))
    print(f"[*] diffrax lindblad probe COMPLETED — checks "
          f"{'ALL HOLD' if all_pass else 'FAIL (recorded)'}; receipt: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
