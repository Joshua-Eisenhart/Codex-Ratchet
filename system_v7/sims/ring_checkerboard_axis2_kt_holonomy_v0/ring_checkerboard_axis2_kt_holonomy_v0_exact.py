#!/usr/bin/env python3
"""ring_checkerboard_axis2_kt_holonomy_v0 -- EXACT reference leg (numpy/stdlib).

GENUINE Axis-2 discriminator (replaces the DEMOTED by-construction K_t test of
ring_checkerboard_euler_conversion_axis2_frame_v0, where K_direct/K_static=0 via @zeros and
K_dynamic=||G|| by unitary norm-invariance -- none of which could come out otherwise).

Object under test: the HOLONOMY of the Axis-2 connection K_t = i V_t^dag dV_t around a CLOSED loop
of frames V(s), s in [0,1], V(1)=V(0). Holonomy = path-ordered product
        U_loop = P prod_s exp(-i K(s) ds).

The Axis-2 connection here is the spin-1/2 (Wilczek-Zee, abelian rank-1 -> Berry) connection of the
sim's own Bloch frame on the shell/fiber (eta,chi) sphere -- the SAME spinor table the euler sim
converts, now carried around a LOOP. K_t = i <n| d/ds |n> along the loop.

THE DISCRIMINATOR (load-bearing, NOT by-construction): the holonomy is nontrivial IFF the frame loop
encloses nonzero curvature.
  (direct / Lagrangian / comoving frame, V(s)=I)         -> U_loop = I       (trivial; telescopes)
  (trivial loop, contractible to a point, zero area)     -> U_loop = I       (trivial)
  (dynamic / Eulerian frame, loop encloses curvature)    -> U_loop != I, and
                                                            |holonomy phase| = enclosed flux (Stokes)
  (shrink the loop -> enclosed area -> 0)                -> U_loop -> I continuously
  (erase: OPEN path, not a loop)                         -> NOT gauge-invariant (changes under a
                                                            boundary frame gauge transform)

This is a REAL measurement: the Berry curvature of spin-1/2 is F = -(1/2) sin(theta) dtheta ^ dphi
(half-monopole). A loop enclosing solid angle Omega gives a holonomy whose phase magnitude is
Omega/2 (the Wilson-loop overlap-product phase = +Omega/2; the Berry connection phase = -Omega/2;
same magnitude, fixed convention). Change the loop, the flux changes. A flat (pure-gauge) connection
would give 0 regardless of the loop -- that is the outcome that does NOT occur, which is what makes
it load-bearing.

No M(C) admission, Axis0, QIT engine, manifold, or physics. classification = scratch_diagnostic.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

SIM_ID = "ring_checkerboard_axis2_kt_holonomy_v0"
ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "results" / f"{SIM_ID}_exact_results.json"

TOL = 1e-9
N_STEPS = 4096  # loop discretization (path-ordered product steps)

SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)

# ODE control adiabaticity / time-resolution (Schrodinger leg): higher B = more adiabatic.
ODE_B = 20000.0
ODE_M = 1_000_000


# ----- the spin-1/2 frame: eigenstate |n(theta,phi)> of n.sigma on the Bloch sphere -----
def bloch_frame(theta: float, phi: float) -> np.ndarray:
    """|n(theta,phi)> = up-eigenstate of (sin th cos ph, sin th sin ph, cos th).sigma.
    Smooth (north-pole) gauge -> well-defined away from theta=pi (south pole)."""
    return np.array([math.cos(theta / 2.0),
                     math.sin(theta / 2.0) * np.exp(1j * phi)], dtype=complex)


def expm_2x2(A: np.ndarray) -> np.ndarray:
    w, V = np.linalg.eig(A)
    return V @ np.diag(np.exp(w)) @ np.linalg.inv(V)


def holonomy_along(frames: np.ndarray) -> complex:
    """Path-ordered U(1) holonomy of the Berry connection along a frame path.

    K(s) ds = i <n(s)| d|n(s)> ; the holonomy step is exp(-i K ds). For a U(1) (rank-1) frame the
    path-ordered product reduces to the product of overlap phases:
        U = prod_s <n(s)|n(s+ds)> / |<n(s)|n(s+ds)>|   (geometric / projected; gauge-link form)
    This is the discrete non-abelian-Stokes / Wilson-loop estimator. For a CLOSED loop it is
    gauge-invariant. `frames` is an (M+1,2) array of normalized states with frames[-1] ~ frames[0]
    for a loop (an open path otherwise)."""
    u = 1.0 + 0.0j
    for s in range(len(frames) - 1):
        ov = np.vdot(frames[s], frames[s + 1])  # <n(s)|n(s+1)>
        if abs(ov) < 1e-14:
            return float("nan")
        u *= ov / abs(ov)
    return u


def loop_frames(theta0: float, dtheta: float, phi_turns: int, n: int) -> np.ndarray:
    """Closed loop on the Bloch sphere at polar radius dtheta about theta0, winding phi `phi_turns`
    times. Encloses solid angle (curvature). Returns (n+1,2) frames with last == first."""
    out = np.empty((n + 1, 2), dtype=complex)
    # parallel of constant colatitude theta0+dtheta, traversed in phi (the standard solid-angle loop)
    theta = theta0 + dtheta
    for s in range(n + 1):
        phi = 2 * math.pi * phi_turns * s / n
        out[s] = bloch_frame(theta, phi)
    out[-1] = out[0]  # force exact closure
    return out


def enclosed_solid_angle(theta_cap: float, phi_turns: int) -> float:
    """Solid angle of the spherical cap above colatitude theta_cap (loop = its boundary parallel),
    times the winding number. Omega = 2 pi (1 - cos theta_cap)."""
    return phi_turns * 2 * math.pi * (1 - math.cos(theta_cap))


# ----- deepseek control: tunable colatitude knob g in [0,1] -- NUMERICS-CONSISTENCY check only -----
def curvature_knob_frames(theta_cap: float, g: float, n: int) -> np.ndarray:
    """SAME full phi-loop (parallel traversed 0->2pi once) and SAME gauge-link rule as the dynamic
    loop, but the colatitude is alpha_g with sin^2(alpha_g/2) = g sin^2(theta_cap/2). The Berry
    connection of this frame is A = sin^2(alpha/2) dphi, so A_g = g A and the holonomy phase is
    g*Omega/2.

    SCOPE (post-audit 2026-06-15, 5 sonnet lenses): this is NOT an independent measurement of
    curvature and does NOT resolve the coordinate-baking flag. The alpha_g formula was AUTHORED so
    that sin^2(alpha_g/2) = g sin^2(theta_cap/2), which makes phase = g*Omega/2 an ANALYTIC IDENTITY
    of the frame construction; the link product confirms the Berry formula against itself. The g=0
    endpoint is a STRUCTURAL ZERO: alpha_g=0 -> sin(alpha_g/2)=0 -> the frame is phi-INDEPENDENT
    ([1,0] for all phi) -> U=I by sin(0)=0 for ANY constant frame (verified: a random constant frame
    also gives |U-I|=0). The g=0 endpoint therefore has ZERO discriminating power against
    coordinate-baking. What this knob legitimately earns: (a) a numerics-consistency check that the
    link product reproduces phase=g*Omega/2 across a family (it CAN fail for a wrong frame formula --
    alpha_g=g*theta_cap gives 0.421 at g=0.5 instead of 0.785), and (b) a monotone shrink-to-identity
    family. The genuine coordinate-baking discriminators are the phi-DEPENDENT flat-connection control
    (theta=0 winding, |U-I|~6e-13 vs curved ~1.41) and the ODE control (independent Schrodinger
    integration, no solid-angle reference)."""
    alpha_g = 2.0 * math.asin(math.sqrt(g) * math.sin(theta_cap / 2.0))
    out = np.empty((n + 1, 2), dtype=complex)
    for s in range(n + 1):
        phi = 2 * math.pi * s / n
        out[s] = bloch_frame(alpha_g, phi)
    out[-1] = out[0]
    return out


# ----- grok control: integrate the actual time-dependent two-level Schrodinger ODE around the loop --
def ode_geometric_phase(theta_cap: float, B: float, m: int) -> float:
    """Integrate i dpsi/dt = H(t) psi with H(t) = -(B/2) n(t).sigma, n(t) tracing the SAME loop
    (colatitude theta_cap, azimuth phi(t)=2 pi t/T, T=1). NO reference to the enclosed solid angle.
    psi starts in the instantaneous ground state; per-step propagator is the EXACT 2x2 Rodrigues form
    exp(-i dt H) = cos(b) I + i sin(b) n.sigma with b = B dt/2 (since H = -(B/2) n.sigma). The
    dynamical phase exp(-i \\int E0 dt), E0 = -B/2, is accumulated and removed; the residual
    arg<psi(0)|psi(T)> is the GEOMETRIC (Berry) phase. Adiabatic: error ~ 1/B. Returns the geometric
    phase (should match the link-product holonomy phase in MAGNITUDE; sign is the fixed
    connection-vs-Wilson-loop convention = -Omega/2)."""
    def nvec(phi):
        return (math.sin(theta_cap) * math.cos(phi),
                math.sin(theta_cap) * math.sin(phi),
                math.cos(theta_cap))
    start = bloch_frame(theta_cap, 0.0)
    psi = start.astype(complex).copy()
    dt = 1.0 / m
    E0 = -B / 2.0
    dyn = 0.0
    for k in range(m):
        phi = 2 * math.pi * (k + 0.5) / m
        nx, ny, nz = nvec(phi)
        b = B * dt / 2.0
        step = (math.cos(b) * np.eye(2, dtype=complex)
                + 1j * math.sin(b) * (nx * SX + ny * SY + nz * SZ))
        psi = step @ psi
        dyn += E0 * dt
    overlap = np.vdot(start, psi * np.exp(1j * dyn))  # remove dynamical phase
    return float(np.angle(overlap))


def main() -> int:
    # ===== DYNAMIC / EULERIAN frame: loop on the Bloch sphere enclosing real curvature =====
    theta_cap = math.pi / 3.0  # 60 deg cap -> nonzero enclosed solid angle
    frames_dyn = loop_frames(0.0, theta_cap, 1, N_STEPS)
    U_dyn = holonomy_along(frames_dyn)
    phase_dyn = float(np.angle(U_dyn))
    Omega = enclosed_solid_angle(theta_cap, 1)
    # spin-1/2 Berry connection A = i<n|dn> gives Berry phase gamma = oint A = -Omega/2. The
    # overlap-product (Wilson-loop) holonomy phase sum_s arg<n(s)|n(s+1)> = oint Im<n|dn> = -gamma,
    # so the HOLONOMY phase equals +Omega/2 (magnitude = enclosed flux Omega/2; sign is the fixed
    # link-vs-connection convention, verified analytically). The load-bearing content is that the
    # holonomy MAGNITUDE tracks the enclosed curvature flux; a flat connection would give 0.
    expected_phase = +Omega / 2.0
    # wrap both into (-pi,pi] for comparison
    def wrap(x):
        return (x + math.pi) % (2 * math.pi) - math.pi
    flux_match_err = float(abs(wrap(phase_dyn - expected_phase)))
    dyn_nontrivial = bool(abs(U_dyn - 1.0) > 1e-3)

    # ===== DIRECT / LAGRANGIAN / comoving frame: V(s)=I along the loop =====
    # comoving frame -> the connection is pure-gauge along the path; path-ordered product telescopes
    # to V(1)^dag V(0) = I. Implement literally: identity frame at every step.
    frames_direct = np.tile(np.array([1.0, 0.0], dtype=complex), (N_STEPS + 1, 1))
    U_direct = holonomy_along(frames_direct)
    direct_trivial = bool(abs(U_direct - 1.0) < 1e-9)

    # ===== CONTROL (b): TRIVIAL loop (contractible to a point / zero enclosed area) =====
    # a loop pinned at the north pole: theta_cap = 0 -> Omega = 0 -> holonomy = I.
    frames_trivial = loop_frames(0.0, 0.0, 1, N_STEPS)
    U_trivial = holonomy_along(frames_trivial)
    trivial_loop_trivial = bool(abs(U_trivial - 1.0) < 1e-6)
    Omega_trivial = enclosed_solid_angle(0.0, 1)

    # ===== CONTROL (FLAT): value-coupled flat / pure-gauge connection around the SAME loop =====
    # This is the decisive anti-by-construction control. Wind the SAME phi-loop (same topology, same
    # winding) but with a frame that never tilts off the pole: |n> = e^{i phi} |up> at theta=0. The
    # connection is then pure gauge (zero curvature enclosed) -> holonomy = I. If the dynamic
    # holonomy were forced by the LOOP alone (by-construction), this flat frame would ALSO give
    # |U-I|>0. It must give ~0. (verified: flat |U-I|~6e-13 vs curved ~1.41.)
    flat_frames = np.empty((N_STEPS + 1, 2), dtype=complex)
    for s in range(N_STEPS + 1):
        phi = 2 * math.pi * s / N_STEPS
        flat_frames[s] = np.array([np.exp(1j * phi) * 1.0, 0.0], dtype=complex)  # theta=0: no tilt
    flat_frames[-1] = flat_frames[0]
    U_flat = holonomy_along(flat_frames)
    flat_trivial = bool(abs(U_flat - 1.0) < 1e-6)
    # the load-bearing flip: curved (curvature) nontrivial AND flat (no curvature) trivial, same loop
    curvature_is_load_bearing = bool(dyn_nontrivial and flat_trivial)

    # ===== CONTROL (d): SHRINK the loop -> holonomy -> I continuously, ~ enclosed area =====
    shrink_caps = [math.pi / 3, math.pi / 4, math.pi / 6, math.pi / 12, math.pi / 48, math.pi / 200]
    shrink = []
    for tc in shrink_caps:
        Uc = holonomy_along(loop_frames(0.0, tc, 1, N_STEPS))
        shrink.append({"theta_cap": tc,
                       "abs_U_minus_I": float(abs(Uc - 1.0)),
                       "phase": float(np.angle(Uc)),
                       "expected_phase": float(+enclosed_solid_angle(tc, 1) / 2.0)})
    shrink_monotone = bool(all(shrink[i]["abs_U_minus_I"] > shrink[i + 1]["abs_U_minus_I"]
                               for i in range(len(shrink) - 1)))
    shrink_to_identity = bool(shrink[-1]["abs_U_minus_I"] < 1e-2 and shrink[0]["abs_U_minus_I"] > 0.1)
    # holonomy phase tracks enclosed flux across the whole shrink family
    shrink_flux_max_err = float(max(abs(wrap(c["phase"] - c["expected_phase"])) for c in shrink))

    # ===== CONTROL (erase): OPEN path -> NOT gauge-invariant =====
    # take the dynamic loop but DROP the closing step (open arc, 3/4 of the way round). Then apply a
    # frame gauge transform |n> -> e^{i lam(s)} |n> that is identity at the loop's two ENDPOINTS for
    # the CLOSED loop but NOT for the open arc -> the closed holonomy is invariant, the open one moves.
    arc_len = (3 * N_STEPS) // 4
    frames_open = frames_dyn[:arc_len + 1]
    # gauge function lam(s): bump that vanishes at s=0 and s=N_STEPS (closed-loop endpoints)
    def gauge(s_frac):  # s_frac in [0,1]
        return 0.7 * math.sin(2 * math.pi * s_frac)  # lam(0)=lam(1)=0
    def apply_gauge(frames, n_total):
        g = frames.copy()
        for s in range(len(g)):
            g[s] = np.exp(1j * gauge(s / n_total)) * g[s]
        return g
    # closed loop under this gauge: holonomy phase unchanged
    U_dyn_gauged = holonomy_along(apply_gauge(frames_dyn, N_STEPS))
    closed_gauge_invariant = bool(abs(wrap(np.angle(U_dyn_gauged) - phase_dyn)) < 1e-6)
    # open arc under the same gauge: its "holonomy" DOES change (gauge function nonzero at arc end)
    U_open = holonomy_along(frames_open)
    U_open_gauged = holonomy_along(apply_gauge(frames_open, N_STEPS))
    open_gauge_dependent = bool(abs(wrap(np.angle(U_open_gauged) - np.angle(U_open))) > 1e-3)

    # ===== CONTROL (deepseek): colatitude KNOB g in [0,1] -- NUMERICS-CONSISTENCY check only =====
    # POST-AUDIT (2026-06-15): re-tiered from "coordinate-baking discriminator" to a numerics-
    # consistency check. The knob phase = g*Omega/2 is an ANALYTIC IDENTITY of the alpha_g formula
    # (sin^2(alpha_g/2)=g*sin^2(theta_cap/2)), so "phase tracks g*Omega/2" confirms the Berry formula
    # against itself and cannot fail for correct code; the g=0 endpoint is a STRUCTURAL ZERO (any
    # phi-independent frame -> U=I). It legitimately checks (a) the link product reproduces the family
    # (CAN fail for a wrong frame formula) and (b) monotone shrink. It does NOT resolve coordinate-
    # baking -- that is the phi-dependent flat-connection control + the ODE control.
    g_values = [1.0, 0.5, 0.1, 0.0]
    curvature_curve = []
    for g in g_values:
        Ug = holonomy_along(curvature_knob_frames(theta_cap, g, N_STEPS))
        curvature_curve.append({
            "g": g,
            "abs_U_minus_I": float(abs(Ug - 1.0)),
            "phase": float(np.angle(Ug)),
            "expected_phase_g_Omega_over_2": float(g * Omega / 2.0),
        })
    # numerics-consistency: phase reproduces g*Omega/2 across the family (catches wrong frame formula)
    knob_flux_max_err = float(max(abs(wrap(c["phase"] - c["expected_phase_g_Omega_over_2"]))
                                  for c in curvature_curve))
    g0 = next(c for c in curvature_curve if c["g"] == 0.0)
    # g=0 endpoint: STRUCTURAL ZERO (alpha_g=0 -> phi-independent frame -> U=I by sin(0)=0). This is a
    # degenerate-endpoint consistency floor, NOT an anti-coordinate-baking discriminator.
    g0_degenerate_endpoint_consistent = bool(g0["abs_U_minus_I"] < 1e-6)
    knob_monotone = bool(all(curvature_curve[i]["abs_U_minus_I"] > curvature_curve[i + 1]["abs_U_minus_I"]
                             for i in range(len(curvature_curve) - 1)))
    # slope as g->0: |U(g)-I|/g -> Omega/2 (analytic consequence of phase=g*Omega/2; discretization check)
    g_lin = 1e-3
    U_lin = holonomy_along(curvature_knob_frames(theta_cap, g_lin, N_STEPS))
    knob_linear_slope = float(abs(U_lin - 1.0) / g_lin)
    knob_slope_matches_half_flux = bool(abs(knob_linear_slope - Omega / 2.0) < 1e-2)
    knob_numerics_consistent = bool(g0_degenerate_endpoint_consistent and knob_flux_max_err < 1e-3
                                    and knob_monotone and knob_slope_matches_half_flux)

    # ===== CONTROL (grok): ODE-DERIVED holonomy vs LINK-PRODUCT holonomy =====
    # Integrate the real time-dependent Schrodinger ODE around the loop with NO reference to the
    # enclosed solid angle, extract the geometric phase, and confirm it MATCHES the link-product
    # holonomy phase (in magnitude; opposite sign = fixed connection-vs-Wilson-loop convention).
    geo_phase_ode = ode_geometric_phase(theta_cap, ODE_B, ODE_M)
    # link-product holonomy phase = +Omega/2 = phase_dyn (the headline measurement). ODE geometric
    # phase = -Omega/2. They match in MAGNITUDE; the sign is the documented convention.
    ode_vs_link_match_err = float(abs(abs(geo_phase_ode) - abs(phase_dyn)))
    ode_matches_link = bool(ode_vs_link_match_err < 1e-3)
    # also confirm the ODE phase is nontrivial (a flat connection would give ODE geo phase ~0)
    ode_nontrivial = bool(abs(geo_phase_ode) > 1e-3)
    # NEGATIVE CONTROL (closes audit gap): a FLAT loop (theta_cap=0) integrated through the SAME ODE
    # must give geometric phase ~0. This is the value-coupled flip that proves the ODE phase is a real
    # measurement (curved -> nontrivial, flat -> ~0), not a constant the integrator always returns.
    geo_phase_ode_flat = ode_geometric_phase(0.0, ODE_B, ODE_M)
    ode_flat_loop_trivial = bool(abs(geo_phase_ode_flat) < 1e-3)
    ode_flips_curved_vs_flat = bool(ode_nontrivial and ode_flat_loop_trivial)
    # THE genuine coordinate-baking resolution (NOT the self-authored knob): the phi-DEPENDENT flat
    # connection around the SAME loop gives identity while the curved frame does not, AND the ODE
    # (independent Schrodinger integration, no solid-angle) matches the link product and flips flat->0.
    coordinate_baking_resolved = bool(flat_trivial and dyn_nontrivial and ode_matches_link
                                      and ode_flips_curved_vs_flat)

    invariants = {
        "n_steps": N_STEPS,
        "theta_cap": theta_cap,
        "enclosed_solid_angle": Omega,
        "dynamic_holonomy_abs_minus_I": float(abs(U_dyn - 1.0)),
        "dynamic_holonomy_phase": phase_dyn,
        "expected_holonomy_phase": expected_phase,
        "berry_phase_gamma": float(-Omega / 2.0),
        "flux_match_err": flux_match_err,
        "direct_holonomy_abs_minus_I": float(abs(U_direct - 1.0)),
        "trivial_loop_holonomy_abs_minus_I": float(abs(U_trivial - 1.0)),
        "trivial_loop_solid_angle": Omega_trivial,
        "flat_connection_holonomy_abs_minus_I": float(abs(U_flat - 1.0)),
        "shrink_family": shrink,
        "shrink_flux_max_err": shrink_flux_max_err,
        "closed_loop_phase_under_gauge": float(np.angle(U_dyn_gauged)),
        "open_arc_phase": float(np.angle(U_open)),
        "open_arc_phase_under_gauge": float(np.angle(U_open_gauged)),
        # deepseek curvature-knob control
        "curvature_knob_curve": curvature_curve,
        "curvature_knob_flux_max_err": knob_flux_max_err,
        "curvature_knob_g0_abs_U_minus_I": float(g0["abs_U_minus_I"]),
        "curvature_knob_linear_slope": knob_linear_slope,
        # grok ODE control
        "ode_B": ODE_B,
        "ode_M": ODE_M,
        "ode_geometric_phase": geo_phase_ode,
        "ode_vs_link_match_err": ode_vs_link_match_err,
        "ode_geometric_phase_flat_loop": geo_phase_ode_flat,
    }

    tests = {
        # the headline discriminator: dynamic (Eulerian) loop enclosing curvature -> NONtrivial
        "dynamic_eulerian_holonomy_nontrivial": dyn_nontrivial,
        # and it EQUALS the enclosed curvature flux (non-abelian Stokes), not a free number
        "holonomy_equals_enclosed_flux": bool(flux_match_err < 1e-3),
        # direct (Lagrangian / comoving) frame -> trivial holonomy
        "direct_lagrangian_holonomy_trivial": direct_trivial,
    }
    controls = {
        # (b) trivial loop (zero enclosed area) -> trivial holonomy
        "trivial_loop_holonomy_trivial": trivial_loop_trivial,
        # (FLAT) value-coupled control: flat/pure-gauge connection around the SAME loop -> trivial.
        # This is what proves the dynamic holonomy is NOT by-construction (loop alone does not force it).
        "flat_connection_same_loop_trivial": flat_trivial,
        "curvature_load_bearing_curved_nontrivial_flat_trivial": curvature_is_load_bearing,
        # (c) is the headline 'holonomy_equals_enclosed_flux' test above (a real loop -> flux)
        "real_loop_holonomy_matches_flux": bool(flux_match_err < 1e-3 and dyn_nontrivial),
        # (d) shrink -> holonomy -> I monotonically and continuously, tracking enclosed flux
        "shrink_loop_holonomy_to_identity": bool(shrink_to_identity and shrink_monotone),
        "shrink_phase_tracks_flux": bool(shrink_flux_max_err < 1e-2),
        # (erase) closed-loop holonomy gauge-invariant; OPEN-path "holonomy" gauge-dependent
        "closed_holonomy_gauge_invariant": closed_gauge_invariant,
        "open_path_holonomy_gauge_dependent": open_gauge_dependent,
        # (deepseek) colatitude KNOB g: NUMERICS-CONSISTENCY tier (re-tiered post-audit 2026-06-15).
        # The phase=g*Omega/2 match is an analytic identity of alpha_g (not an independent measurement);
        # g=0->I is a STRUCTURAL ZERO (any phi-independent frame -> U=I). These check link-product
        # correctness across a family + monotone shrink; they do NOT resolve coordinate-baking.
        "curvature_knob_g0_degenerate_endpoint_consistent": g0_degenerate_endpoint_consistent,
        "curvature_knob_phase_reproduces_g_flux_numerics": bool(knob_flux_max_err < 1e-3),
        "curvature_knob_monotone_in_g": knob_monotone,
        "curvature_knob_linear_slope_matches_half_flux": knob_slope_matches_half_flux,
        "curvature_knob_numerics_consistent": knob_numerics_consistent,
        # (grok) ODE-derived geometric phase MATCHES the link-product holonomy (link not coord-smuggled)
        "ode_geometric_phase_nontrivial": ode_nontrivial,
        "ode_holonomy_matches_link_product": ode_matches_link,
        # (grok) ODE NEGATIVE CONTROL: a flat loop (theta_cap=0) gives ODE phase ~0 -> the ODE phase
        # is a real measurement that FLIPS curved->nontrivial / flat->trivial (closes audit gap).
        "ode_flat_loop_trivial": ode_flat_loop_trivial,
        "ode_flips_curved_vs_flat": ode_flips_curved_vs_flat,
        # THE genuine coordinate-baking resolution: phi-dependent flat control + independent ODE
        # (the self-authored g-knob does NOT carry this claim).
        "coordinate_baking_resolved_by_flat_and_ode": coordinate_baking_resolved,
    }
    all_tests = all(tests.values())
    all_controls = all(controls.values())

    # ablation: dynamic (curved loop) vs direct (flat/comoving) -> |U-I| flips from O(1) to 0
    ablation_delta = float(abs(U_dyn - 1.0)) - float(abs(U_direct - 1.0))

    result = {
        "schema": "codex_ratchet.sim_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "engine": "exact_numpy_reference",
        "root_lineage": {
            "F01_finite_support": True,
            "N01_order_sensitivity": "the holonomy is the PATH-ORDERED product of exp(-i K ds) around a closed loop; order-sensitivity (path ordering) is exactly what makes the enclosed-curvature flux nonzero. Comoving (Lagrangian) order telescopes to I; Eulerian order around curvature does not.",
        },
        "source_target": "ring-checkerboard runbook + axes12_deep_vein Axis2 (direct/conjugated frame, K_t=i V^dag V_dot) -- the K_t LOOP-HOLONOMY discriminator the euler sim's audit_verdict named as the real test to replace the by-construction K_t values",
        "claim": "the Axis-2 connection K_t has NONtrivial holonomy around a closed frame loop IFF the loop encloses nonzero curvature; comoving/Lagrangian and trivial loops give identity; the nontrivial holonomy phase magnitude equals the enclosed Berry flux (Omega/2). This is a real measurement, could have come out flat.",
        "invariants": invariants,
        "tests": tests,
        "controls": controls,
        "all_tests_pass": all_tests,
        "all_controls_pass": all_controls,
        "ablation_outcome_delta": {
            "dynamic_curved_abs_minus_I": float(abs(U_dyn - 1.0)),
            "direct_comoving_abs_minus_I": float(abs(U_direct - 1.0)),
            "delta": ablation_delta,
        },
        "honest_scope": {
            "earns": "finite-discretization numeric witness that the Axis-2 K_t holonomy is curvature-coupled: a loop enclosing Berry curvature -> U_loop != I with phase = -Omega/2 (matches Stokes), a comoving/trivial/shrinking loop -> U_loop -> I, and an open path is not gauge-invariant. The coordinate-baking flag is answered by TWO value-coupled controls: (1) the phi-DEPENDENT flat-connection control (theta=0 winding around the SAME loop -> |U-I|~6e-13 while the curved frame gives ~1.41) -- the load-bearing flip that proves the holonomy is forced by enclosed CURVATURE not the loop alone; and (2) the ODE control -- the geometric phase from integrating the actual time-dependent Schrodinger ODE around the loop (NO solid-angle reference) matches the link-product holonomy in magnitude AND flips to ~0 for a flat loop. Both can come out the other way and do not. Scratch ceiling, one engine.",
            "does_not_earn": "M(C) admission, Axis0 closure, QIT engine, smooth manifold, physics. The half-monopole curvature is the standard spin-1/2 Berry curvature, not a derived object. POST-AUDIT (2026-06-15, 5 sonnet lenses): the deepseek colatitude-knob (g in [0,1]) is a NUMERICS-CONSISTENCY check, NOT an independent measurement and NOT a coordinate-baking resolver: phase=g*Omega/2 is an analytic identity of the alpha_g formula (sin^2(alpha_g/2)=g*sin^2(theta_cap/2)) and the g=0 endpoint is a structural zero (any phi-independent frame -> U=I). Coordinate-baking is resolved by the flat-connection + ODE controls only. The four-engine NUMERIC agreement on the holonomy/knob legs reflects the SAME overlap-product formula in distinct float paths (correlated), not algorithmic independence; only the ODE legs are genuinely formula-independent across engines. Needs a fresh multi-model fleet box-viii audit.",
        },
        "TOOL_MANIFEST": {
            "numpy": {"tried": True, "used": True, "reason": "complex spin-1/2 frames, path-ordered overlap-phase (Wilson-loop) holonomy, matrix exp via eig, Bloch-sphere loop discretization, exact 2x2 Rodrigues ODE step; the holonomy and ODE-phase measurements cannot be computed without it"},
            "python_stdlib": {"tried": True, "used": True, "reason": "loop parametrization, solid-angle / Stokes flux, gauge-transform construction for the open-path control"},
        },
        # numpy carries the actual complex linalg / holonomy / ODE computation (not decoration); set to
        # load_bearing to match the jax/julia/pytorch legs running the SAME computation (post-audit
        # 2026-06-15: the prior 'supportive' label was an inconsistency with the three sibling legs).
        "TOOL_INTEGRATION_DEPTH": "load_bearing",
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {RESULT}")
    print(f"all_tests_pass={all_tests} all_controls_pass={all_controls}")
    print(f"dynamic |U-I|={abs(U_dyn-1.0):.4f} phase={phase_dyn:+.5f} expected={expected_phase:+.5f} flux_err={flux_match_err:.2e}")
    print(f"direct |U-I|={abs(U_direct-1.0):.2e} trivial-loop |U-I|={abs(U_trivial-1.0):.2e} flat-conn |U-I|={abs(U_flat-1.0):.2e}")
    print(f"shrink |U-I|: {[round(c['abs_U_minus_I'],4) for c in shrink]} monotone={shrink_monotone}")
    print(f"closed gauge-invariant={closed_gauge_invariant} open gauge-dependent={open_gauge_dependent}")
    print(f"[deepseek] colatitude-knob (NUMERICS-CONSISTENCY) g={[c['g'] for c in curvature_curve]}")
    print(f"           |U(g)-I|={[round(c['abs_U_minus_I'],6) for c in curvature_curve]} "
          f"g0_struct_zero={g0_degenerate_endpoint_consistent} flux_err={knob_flux_max_err:.2e} slope={knob_linear_slope:.5f}(Om/2={Omega/2:.5f})")
    print(f"[grok]     ode geo phase={geo_phase_ode:+.6f} link phase={phase_dyn:+.6f} "
          f"match_err={ode_vs_link_match_err:.2e} matches={ode_matches_link}")
    print(f"[grok-neg] ode flat-loop phase={geo_phase_ode_flat:+.2e} flat_trivial={ode_flat_loop_trivial} "
          f"flips_curved_vs_flat={ode_flips_curved_vs_flat}")
    print(f"[resolve]  coordinate_baking_resolved_by_flat_and_ode={coordinate_baking_resolved}")
    return 0 if all_tests and all_controls else 1


if __name__ == "__main__":
    raise SystemExit(main())
