#!/usr/bin/env python3
"""ring_checkerboard_axis2_kt_holonomy_v0 -- JAX leg (vectorized / deformation).

Independent recomputation of the Axis-2 K_t loop-holonomy discriminator using jax.numpy (x64).
Vectorized (batched) construction of the whole frame loop at once and a vectorized link-phase sum is
the JAX-native deformation/gradient role. Does NOT read the exact/julia/pytorch legs.

Replaces the DEMOTED by-construction K_t test (K_direct/K_static=0 via zeros; K_dynamic=||G|| by
norm-invariance). Holonomy is nontrivial IFF the loop encloses curvature -- a real measurement.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

SIM_ID = "ring_checkerboard_axis2_kt_holonomy_v0"
ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "results" / f"{SIM_ID}_jax_results.json"

N_STEPS = 4096
ODE_B = 20000.0
ODE_M = 1_000_000

SX = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
SZ = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)


def loop_frames(theta0: float, dtheta: float, turns: int, n: int) -> jnp.ndarray:
    """Vectorized closed loop: parallel of colatitude theta0+dtheta, winding `turns` times in phi.
    Returns (n+1, 2) complex array with last row == first (forced closure)."""
    theta = theta0 + dtheta
    s = jnp.arange(n + 1)
    phi = 2 * jnp.pi * turns * s / n
    up = jnp.cos(theta / 2.0) * jnp.ones_like(phi)
    dn = jnp.sin(theta / 2.0) * jnp.exp(1j * phi)
    frames = jnp.stack([up.astype(jnp.complex128), dn], axis=1)
    frames = frames.at[-1].set(frames[0])  # exact closure
    return frames


def flat_frames(n: int) -> jnp.ndarray:
    """Pure-gauge winding at theta=0 (no tilt) -> zero enclosed curvature."""
    s = jnp.arange(n + 1)
    phi = 2 * jnp.pi * s / n
    up = jnp.exp(1j * phi)
    dn = jnp.zeros_like(up)
    frames = jnp.stack([up, dn], axis=1)
    return frames.at[-1].set(frames[0])


def holonomy(frames: jnp.ndarray) -> complex:
    """Gauge-covariant path-ordered U(1) holonomy: product of overlap link phases.
    U = prod_s <n(s)|n(s+1)>/|<n(s)|n(s+1)>|. Vectorized over the whole loop."""
    ov = jnp.sum(jnp.conj(frames[:-1]) * frames[1:], axis=1)  # <n(s)|n(s+1)> for all s
    link = ov / jnp.abs(ov)
    return complex(jnp.prod(link))


def curvature_knob_frames(theta_cap: float, g: float, n: int) -> jnp.ndarray:
    """deepseek control: SAME full phi-loop and SAME link rule, colatitude alpha_g with
    sin^2(alpha_g/2) = g sin^2(theta_cap/2) -> A_g = g A -> holonomy phase = g*Omega/2. Vectorized.

    SCOPE (post-audit 2026-06-15): NUMERICS-CONSISTENCY check only, NOT an independent measurement and
    NOT a coordinate-baking resolver. phase=g*Omega/2 is an analytic identity of the alpha_g formula;
    the g=0 endpoint is a STRUCTURAL ZERO (alpha_g=0 -> phi-independent frame -> U=I for ANY constant
    frame). Coordinate-baking is resolved by the phi-dependent flat-connection control + the ODE
    control, not this self-authored knob."""
    alpha_g = 2.0 * math.asin(math.sqrt(g) * math.sin(theta_cap / 2.0))
    s = jnp.arange(n + 1)
    phi = 2 * jnp.pi * s / n
    up = jnp.cos(alpha_g / 2.0) * jnp.ones_like(phi)
    dn = jnp.sin(alpha_g / 2.0) * jnp.exp(1j * phi)
    frames = jnp.stack([up.astype(jnp.complex128), dn], axis=1)
    return frames.at[-1].set(frames[0])


def ode_geometric_phase(theta_cap: float, B: float, m: int) -> float:
    """grok control: integrate the actual two-level Schrodinger ODE i dpsi/dt = H(t) psi around the
    SAME loop, H(t) = -(B/2) n(t).sigma, n(t)=(sin th cos phi, sin th sin phi, cos th), phi=2 pi t.
    NO solid-angle reference. Exact 2x2 Rodrigues step exp(-i dt H) = cos(b) I + i sin(b) n.sigma,
    b = B dt/2. Time-ordered product via jax.lax.scan (JAX-native deformation route). Dynamical phase
    exp(-i \\int E0 dt), E0 = -B/2, removed; residual arg<psi0|psiT> is the GEOMETRIC (Berry) phase."""
    dt = 1.0 / m
    bcoef = B * dt / 2.0
    k = jnp.arange(m)
    phi = 2 * jnp.pi * (k + 0.5) / m
    nx = jnp.sin(theta_cap) * jnp.cos(phi)
    ny = jnp.sin(theta_cap) * jnp.sin(phi)
    nz = jnp.cos(theta_cap) * jnp.ones_like(phi)
    eye = jnp.eye(2, dtype=jnp.complex128)
    nsig = (nx[:, None, None] * SX + ny[:, None, None] * SY + nz[:, None, None] * SZ)
    steps = jnp.cos(bcoef) * eye + 1j * jnp.sin(bcoef) * nsig  # (m,2,2) exact propagators

    start = jnp.array([math.cos(theta_cap / 2.0),
                       math.sin(theta_cap / 2.0)], dtype=jnp.complex128)

    def body(psi, U):
        return U @ psi, None
    psiT, _ = jax.lax.scan(body, start, steps)
    dyn = (-B / 2.0) * 1.0  # \int_0^1 E0 dt = E0 * T, T=1
    overlap = jnp.vdot(start, psiT * jnp.exp(1j * dyn))
    return float(jnp.angle(overlap))


def enclosed_solid_angle(theta_cap: float, turns: int) -> float:
    return turns * 2 * math.pi * (1 - math.cos(theta_cap))


def wrap(x: float) -> float:
    return (x + math.pi) % (2 * math.pi) - math.pi


def main() -> int:
    # DYNAMIC / EULERIAN: loop enclosing curvature
    theta_cap = math.pi / 3.0
    U_dyn = holonomy(loop_frames(0.0, theta_cap, 1, N_STEPS))
    phase_dyn = float(jnp.angle(jnp.asarray(U_dyn)))
    Omega = enclosed_solid_angle(theta_cap, 1)
    expected_phase = +Omega / 2.0
    flux_match_err = float(abs(wrap(phase_dyn - expected_phase)))
    dyn_nontrivial = bool(abs(U_dyn - 1.0) > 1e-3)

    # DIRECT / LAGRANGIAN / comoving: identity frame
    fr_direct = jnp.tile(jnp.array([1.0 + 0j, 0.0 + 0j], dtype=jnp.complex128), (N_STEPS + 1, 1))
    U_direct = holonomy(fr_direct)
    direct_trivial = bool(abs(U_direct - 1.0) < 1e-9)

    # CONTROL (b): trivial loop (zero enclosed area)
    U_triv = holonomy(loop_frames(0.0, 0.0, 1, N_STEPS))
    trivial_loop_trivial = bool(abs(U_triv - 1.0) < 1e-6)

    # CONTROL (FLAT): pure-gauge connection around the SAME loop -> trivial (anti-by-construction)
    U_flat = holonomy(flat_frames(N_STEPS))
    flat_trivial = bool(abs(U_flat - 1.0) < 1e-6)
    curvature_load_bearing = bool(dyn_nontrivial and flat_trivial)

    # CONTROL (d): shrink the loop -> holonomy -> I continuously
    shrink_caps = [math.pi / 3, math.pi / 4, math.pi / 6, math.pi / 12, math.pi / 48, math.pi / 200]
    shrink = []
    for tc in shrink_caps:
        Uc = holonomy(loop_frames(0.0, tc, 1, N_STEPS))
        shrink.append({"theta_cap": tc, "abs_U_minus_I": float(abs(Uc - 1.0)),
                       "phase": float(jnp.angle(jnp.asarray(Uc))),
                       "expected_phase": float(+enclosed_solid_angle(tc, 1) / 2.0)})
    shrink_monotone = bool(all(shrink[i]["abs_U_minus_I"] > shrink[i + 1]["abs_U_minus_I"]
                               for i in range(len(shrink) - 1)))
    shrink_to_identity = bool(shrink[-1]["abs_U_minus_I"] < 1e-2 and shrink[0]["abs_U_minus_I"] > 0.1)
    shrink_flux_max_err = float(max(abs(wrap(c["phase"] - c["expected_phase"])) for c in shrink))

    # CONTROL (erase): OPEN path -> not gauge-invariant
    fr_dyn = loop_frames(0.0, theta_cap, 1, N_STEPS)
    arc_len = (3 * N_STEPS) // 4
    fr_open = fr_dyn[:arc_len + 1]
    s_all = jnp.arange(N_STEPS + 1)
    lam = 0.7 * jnp.sin(2 * jnp.pi * s_all / N_STEPS)  # vanishes at s=0 and s=N_STEPS
    gauge_full = jnp.exp(1j * lam)[:, None]
    U_dyn_g = holonomy(fr_dyn * gauge_full)
    closed_gauge_invariant = bool(abs(wrap(float(jnp.angle(jnp.asarray(U_dyn_g))) - phase_dyn)) < 1e-6)
    U_open = holonomy(fr_open)
    U_open_g = holonomy(fr_open * gauge_full[:arc_len + 1])
    open_gauge_dependent = bool(abs(wrap(float(jnp.angle(jnp.asarray(U_open_g)))
                                         - float(jnp.angle(jnp.asarray(U_open))))) > 1e-3)

    # CONTROL (deepseek): colatitude KNOB g in [0,1] -- NUMERICS-CONSISTENCY check (re-tiered post-audit)
    g_values = [1.0, 0.5, 0.1, 0.0]
    curvature_curve = []
    for g in g_values:
        Ug = holonomy(curvature_knob_frames(theta_cap, g, N_STEPS))
        curvature_curve.append({"g": g, "abs_U_minus_I": float(abs(Ug - 1.0)),
                                "phase": float(jnp.angle(jnp.asarray(Ug))),
                                "expected_phase_g_Omega_over_2": float(g * Omega / 2.0)})
    knob_flux_max_err = float(max(abs(wrap(c["phase"] - c["expected_phase_g_Omega_over_2"]))
                                  for c in curvature_curve))
    g0 = next(c for c in curvature_curve if c["g"] == 0.0)
    # g=0 STRUCTURAL ZERO (alpha_g=0 -> phi-independent frame -> U=I): degenerate-endpoint floor only.
    g0_degenerate_endpoint_consistent = bool(g0["abs_U_minus_I"] < 1e-6)
    knob_monotone = bool(all(curvature_curve[i]["abs_U_minus_I"] > curvature_curve[i + 1]["abs_U_minus_I"]
                             for i in range(len(curvature_curve) - 1)))
    g_lin = 1e-3
    U_lin = holonomy(curvature_knob_frames(theta_cap, g_lin, N_STEPS))
    knob_linear_slope = float(abs(U_lin - 1.0) / g_lin)
    knob_slope_matches_half_flux = bool(abs(knob_linear_slope - Omega / 2.0) < 1e-2)
    knob_numerics_consistent = bool(g0_degenerate_endpoint_consistent and knob_flux_max_err < 1e-3
                                    and knob_monotone and knob_slope_matches_half_flux)

    # CONTROL (grok): ODE-DERIVED geometric phase vs LINK-PRODUCT holonomy (no coord smuggling)
    geo_phase_ode = ode_geometric_phase(theta_cap, ODE_B, ODE_M)
    ode_vs_link_match_err = float(abs(abs(geo_phase_ode) - abs(phase_dyn)))
    ode_matches_link = bool(ode_vs_link_match_err < 1e-3)
    ode_nontrivial = bool(abs(geo_phase_ode) > 1e-3)
    # ODE NEGATIVE CONTROL (closes audit gap): flat loop (theta_cap=0) -> ODE phase ~0 -> the ODE phase
    # is a real measurement that flips curved->nontrivial / flat->trivial.
    geo_phase_ode_flat = ode_geometric_phase(0.0, ODE_B, ODE_M)
    ode_flat_loop_trivial = bool(abs(geo_phase_ode_flat) < 1e-3)
    ode_flips_curved_vs_flat = bool(ode_nontrivial and ode_flat_loop_trivial)
    # THE genuine coordinate-baking resolution (NOT the self-authored knob): flat-connection + ODE.
    coordinate_baking_resolved = bool(flat_trivial and dyn_nontrivial and ode_matches_link
                                      and ode_flips_curved_vs_flat)

    ablation_delta = float(abs(U_dyn - 1.0)) - float(abs(U_direct - 1.0))

    invariants = {
        "n_steps": N_STEPS, "theta_cap": theta_cap, "enclosed_solid_angle": Omega,
        "dynamic_holonomy_abs_minus_I": float(abs(U_dyn - 1.0)), "dynamic_holonomy_phase": phase_dyn,
        "expected_holonomy_phase": expected_phase, "berry_phase_gamma": float(-Omega / 2.0),
        "flux_match_err": flux_match_err,
        "direct_holonomy_abs_minus_I": float(abs(U_direct - 1.0)),
        "trivial_loop_holonomy_abs_minus_I": float(abs(U_triv - 1.0)),
        "trivial_loop_solid_angle": enclosed_solid_angle(0.0, 1),
        "flat_connection_holonomy_abs_minus_I": float(abs(U_flat - 1.0)),
        "shrink_family": shrink, "shrink_flux_max_err": shrink_flux_max_err,
        "closed_loop_phase_under_gauge": float(jnp.angle(jnp.asarray(U_dyn_g))),
        "open_arc_phase": float(jnp.angle(jnp.asarray(U_open))),
        "open_arc_phase_under_gauge": float(jnp.angle(jnp.asarray(U_open_g))),
        "curvature_knob_curve": curvature_curve,
        "curvature_knob_flux_max_err": knob_flux_max_err,
        "curvature_knob_g0_abs_U_minus_I": float(g0["abs_U_minus_I"]),
        "curvature_knob_linear_slope": knob_linear_slope,
        "ode_B": ODE_B, "ode_M": ODE_M,
        "ode_geometric_phase": geo_phase_ode,
        "ode_vs_link_match_err": ode_vs_link_match_err,
        "ode_geometric_phase_flat_loop": geo_phase_ode_flat,
    }
    tests = {
        "dynamic_eulerian_holonomy_nontrivial": dyn_nontrivial,
        "holonomy_equals_enclosed_flux": bool(flux_match_err < 1e-3),
        "direct_lagrangian_holonomy_trivial": direct_trivial,
    }
    controls = {
        "trivial_loop_holonomy_trivial": trivial_loop_trivial,
        "flat_connection_same_loop_trivial": flat_trivial,
        "curvature_load_bearing_curved_nontrivial_flat_trivial": curvature_load_bearing,
        "real_loop_holonomy_matches_flux": bool(flux_match_err < 1e-3 and dyn_nontrivial),
        "shrink_loop_holonomy_to_identity": bool(shrink_to_identity and shrink_monotone),
        "shrink_phase_tracks_flux": bool(shrink_flux_max_err < 1e-2),
        "closed_holonomy_gauge_invariant": closed_gauge_invariant,
        "open_path_holonomy_gauge_dependent": open_gauge_dependent,
        "curvature_knob_g0_degenerate_endpoint_consistent": g0_degenerate_endpoint_consistent,
        "curvature_knob_phase_reproduces_g_flux_numerics": bool(knob_flux_max_err < 1e-3),
        "curvature_knob_monotone_in_g": knob_monotone,
        "curvature_knob_linear_slope_matches_half_flux": knob_slope_matches_half_flux,
        "curvature_knob_numerics_consistent": knob_numerics_consistent,
        "ode_geometric_phase_nontrivial": ode_nontrivial,
        "ode_holonomy_matches_link_product": ode_matches_link,
        "ode_flat_loop_trivial": ode_flat_loop_trivial,
        "ode_flips_curved_vs_flat": ode_flips_curved_vs_flat,
        "coordinate_baking_resolved_by_flat_and_ode": coordinate_baking_resolved,
    }
    all_tests = all(tests.values())
    all_controls = all(controls.values())

    result = {
        "schema": "codex_ratchet.sim_result.v1", "sim_id": SIM_ID,
        "classification": "scratch_diagnostic", "promotion_allowed": False,
        "formal_admission_allowed": False, "engine": "jax_vectorized_deformation",
        "root_lineage": {"F01_finite_support": True,
            "N01_order_sensitivity": "holonomy = path-ordered product of exp(-i K ds); ordering around enclosed curvature makes U_loop != I; comoving order telescopes to I"},
        "source_target": "ring-checkerboard runbook + axes12_deep_vein Axis2 (K_t=i V^dag V_dot) -- the loop-holonomy discriminator the euler sim audit named as the real test",
        "claim": "Axis-2 K_t holonomy nontrivial IFF the closed frame loop encloses curvature; comoving/trivial/flat loops -> I; nontrivial holonomy phase magnitude = enclosed Berry flux Omega/2 (vectorized JAX route).",
        "invariants": invariants, "tests": tests, "controls": controls,
        "all_tests_pass": all_tests, "all_controls_pass": all_controls,
        "ablation_outcome_delta": {"dynamic_curved_abs_minus_I": float(abs(U_dyn - 1.0)),
            "direct_comoving_abs_minus_I": float(abs(U_direct - 1.0)), "delta": ablation_delta},
        "honest_scope": {
            "earns": "independent JAX (vectorized) recomputation of the Axis-2 K_t loop-holonomy; curvature-coupled discriminator (curved loop -> U!=I = flux, comoving/trivial/flat -> I, open path not gauge-invariant). Coordinate-baking is resolved by the phi-DEPENDENT flat-connection control (theta=0 winding -> I while curved -> 1.41) + the ODE control (jax.lax.scan Schrodinger integration, no solid-angle reference, matches link product AND flips flat->0); scratch ceiling, deformation leg",
            "does_not_earn": "M(C), Axis0 closure, QIT engine, smooth manifold, physics. POST-AUDIT (2026-06-15): the deepseek colatitude-knob is a NUMERICS-CONSISTENCY check (phase=g*Omega/2 is an analytic identity of alpha_g; g=0 is a structural zero), NOT a coordinate-baking resolver. The four-engine numeric agreement on the holonomy/knob legs reflects the same overlap-product formula in distinct float paths; only the ODE legs are formula-independent across engines. Needs cross-engine agreement + fleet audit"},
        "TOOL_MANIFEST": {"jax": {"tried": True, "used": True,
            "reason": "x64 vectorized batched construction of the whole frame loop and the link-phase product holonomy; deformation/gradient-native leg"}},
        "TOOL_INTEGRATION_DEPTH": "load_bearing",
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {RESULT}")
    print(f"all_tests_pass={all_tests} all_controls_pass={all_controls}")
    print(f"dynamic |U-I|={abs(U_dyn-1.0):.6f} phase={phase_dyn:+.7f} expected={expected_phase:+.7f} flux_err={flux_match_err:.2e}")
    print(f"direct |U-I|={abs(U_direct-1.0):.2e} trivial={abs(U_triv-1.0):.2e} flat={abs(U_flat-1.0):.2e}")
    print(f"shrink monotone={shrink_monotone} open_gauge_dep={open_gauge_dependent}")
    print(f"[deepseek] knob (NUMERICS) |U(g)-I|={[round(c['abs_U_minus_I'],6) for c in curvature_curve]} "
          f"g0_struct_zero={g0_degenerate_endpoint_consistent} flux_err={knob_flux_max_err:.2e} slope={knob_linear_slope:.5f}(Om/2={Omega/2:.5f})")
    print(f"[grok]     ode geo phase={geo_phase_ode:+.6f} link phase={phase_dyn:+.6f} "
          f"match_err={ode_vs_link_match_err:.2e} matches={ode_matches_link}")
    print(f"[grok-neg] ode flat-loop phase={geo_phase_ode_flat:+.2e} flat_trivial={ode_flat_loop_trivial} "
          f"flips={ode_flips_curved_vs_flat}  coord_baking_resolved={coordinate_baking_resolved}")
    return 0 if all_tests and all_controls else 1


if __name__ == "__main__":
    raise SystemExit(main())
