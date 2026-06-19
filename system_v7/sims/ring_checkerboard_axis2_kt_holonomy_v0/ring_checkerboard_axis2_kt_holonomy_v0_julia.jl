#!/usr/bin/env julia
# ring_checkerboard_axis2_kt_holonomy_v0 -- JULIA leg (advanced-geometry canon arbiter).
#
# Independent recomputation of the Axis-2 K_t loop-holonomy discriminator. Most-aligned engine
# (per owner ranking): exact complex spin-1/2 frames, the connection 1-form K(s) = i <n| d/ds |n>,
# and the holonomy as the genuine PATH-ORDERED product of exp(-i K(s) ds) along the loop (a DISTINCT
# numerical path from the exact leg's overlap-product estimator -- they must still agree on the
# load-bearing bools). Canon/arbiter: its values are the reference on divergence. No peer reads.
#
# Replaces the DEMOTED by-construction K_t test of ring_checkerboard_euler_conversion_axis2_frame_v0
# (K_direct/K_static=0 via zeros; K_dynamic=||G|| by norm-invariance). Here the holonomy is nontrivial
# IFF the loop encloses curvature -- a measurement that could come out flat.

using LinearAlgebra
using JSON

const SIM_ID = "ring_checkerboard_axis2_kt_holonomy_v0"
const HERE = @__DIR__
const RESULT = joinpath(HERE, "results", SIM_ID * "_julia_results.json")

const TOL = 1e-9
const N_STEPS = 4096
const ODE_B = 20000.0
const ODE_M = 1_000_000

const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

# spin-1/2 frame: up-eigenstate of n.sigma on the Bloch sphere (north-pole gauge)
bloch_frame(theta, phi) = ComplexF64[cos(theta / 2), sin(theta / 2) * exp(im * phi)]

# Holonomy as the gauge-covariant PATH-ORDERED product of exp(-i K(s) ds). The Axis-2 link phase is
# K(s) ds = arg<n(s)|n(s+1)> (the gauge-covariant lattice connection: the phase of the overlap; the
# |.| projection removes the second-order norm-change term so the product is gauge-invariant for a
# closed loop and EXACT to machine precision for a pure-gauge/flat connection). Julia extracts the
# link phase explicitly via arg() and rebuilds the step via exp() -- a DISTINCT numerical route from
# the exact leg's <n|n'>/|<n|n'>| complex-division estimator (same math, different float path).
function holonomy_pathordered(frames)
    U = 1.0 + 0.0im
    M = length(frames) - 1
    for s in 1:M
        ov = dot(frames[s], frames[s+1])        # <n(s)|n(s+1)>
        abs(ov) < 1e-14 && return ComplexF64(NaN)
        K_ds = -angle(ov)                        # K ds = i<n|dn> ~ -arg<n|n'>  (link 1-form)
        U *= exp(-im * K_ds)                      # path-ordered step exp(-i K ds) = exp(i arg ov)
    end
    return U
end

# enclosed solid angle of the cap above colatitude theta_cap, times winding
enclosed_solid_angle(theta_cap, turns) = turns * 2pi * (1 - cos(theta_cap))

# closed loop = parallel of colatitude theta0+dtheta, traversed `turns` times in phi
function loop_frames(theta0, dtheta, turns, n)
    theta = theta0 + dtheta
    fr = [bloch_frame(theta, 2pi * turns * s / n) for s in 0:n]
    fr[end] = fr[1]   # force exact closure
    return fr
end

# deepseek control: SAME full phi-loop and SAME link rule, colatitude alpha_g with
# sin^2(alpha_g/2) = g sin^2(theta_cap/2) -> A_g = g A -> holonomy phase = g*Omega/2.
# SCOPE (post-audit 2026-06-15): NUMERICS-CONSISTENCY check only, NOT an independent measurement and
# NOT a coordinate-baking resolver. phase=g*Omega/2 is an analytic identity of alpha_g; g=0 is a
# STRUCTURAL ZERO (alpha_g=0 -> phi-independent frame -> U=I for ANY constant frame). Coordinate-
# baking is resolved by the phi-dependent flat-connection control + the ODE control.
function curvature_knob_frames(theta_cap, g, n)
    alpha_g = 2 * asin(sqrt(g) * sin(theta_cap / 2))
    fr = [bloch_frame(alpha_g, 2pi * s / n) for s in 0:n]
    fr[end] = fr[1]
    return fr
end

# grok control: integrate the real two-level Schrodinger ODE i dpsi/dt = H(t) psi around the SAME
# loop, H(t) = -(B/2) n(t).sigma, n(t)=(sin th cos phi, sin th sin phi, cos th), phi=2 pi t, T=1. NO
# solid-angle reference. Exact 2x2 Rodrigues step exp(-i dt H) = cos(b) I + i sin(b) n.sigma, b=B dt/2
# (since H = -(B/2) n.sigma). Path-ordered (sequential) matrix product -- the Julia canon route for
# the dynamical evolution. Dynamical phase exp(-i E0 T), E0=-B/2, removed; residual arg<psi0|psiT> is
# the GEOMETRIC (Berry) phase (matches the link-product holonomy in magnitude).
function ode_geometric_phase(theta_cap, B, m)
    dt = 1.0 / m
    b = B * dt / 2
    cb = cos(b); sb = sin(b)
    eye = ComplexF64[1 0; 0 1]
    start = ComplexF64[cos(theta_cap / 2), sin(theta_cap / 2)]
    psi = copy(start)
    for k in 0:m-1
        phi = 2pi * (k + 0.5) / m
        nx = sin(theta_cap) * cos(phi); ny = sin(theta_cap) * sin(phi); nz = cos(theta_cap)
        step = cb * eye + im * sb * (nx * SX + ny * SY + nz * SZ)
        psi = step * psi
    end
    dyn = (-B / 2) * 1.0   # E0 * T, T=1
    overlap = dot(start, psi * exp(im * dyn))   # remove dynamical phase
    return angle(overlap)
end

wrap(x) = mod(x + pi, 2pi) - pi

function main()
    # DYNAMIC / EULERIAN: loop enclosing curvature
    theta_cap = pi / 3
    fr_dyn = loop_frames(0.0, theta_cap, 1, N_STEPS)
    U_dyn = holonomy_pathordered(fr_dyn)
    phase_dyn = angle(U_dyn)
    Omega = enclosed_solid_angle(theta_cap, 1)
    expected_phase = +Omega / 2        # holonomy phase magnitude = enclosed flux (Wilson-loop sign)
    flux_match_err = abs(wrap(phase_dyn - expected_phase))
    dyn_nontrivial = abs(U_dyn - 1.0) > 1e-3

    # DIRECT / LAGRANGIAN / comoving: V(s)=I -> identity frame -> trivial
    fr_direct = [ComplexF64[1.0, 0.0] for _ in 0:N_STEPS]
    U_direct = holonomy_pathordered(fr_direct)
    direct_trivial = abs(U_direct - 1.0) < 1e-9

    # CONTROL (b): trivial loop (zero enclosed area)
    fr_triv = loop_frames(0.0, 0.0, 1, N_STEPS)
    U_triv = holonomy_pathordered(fr_triv)
    trivial_loop_trivial = abs(U_triv - 1.0) < 1e-6

    # CONTROL (FLAT): pure-gauge connection around the SAME loop -> trivial (anti-by-construction)
    fr_flat = [ComplexF64[exp(im * 2pi * s / N_STEPS), 0.0] for s in 0:N_STEPS]
    fr_flat[end] = fr_flat[1]
    U_flat = holonomy_pathordered(fr_flat)
    flat_trivial = abs(U_flat - 1.0) < 1e-6
    curvature_load_bearing = dyn_nontrivial && flat_trivial

    # CONTROL (d): shrink the loop -> holonomy -> I continuously, ~ enclosed area
    shrink_caps = [pi / 3, pi / 4, pi / 6, pi / 12, pi / 48, pi / 200]
    shrink = []
    for tc in shrink_caps
        Uc = holonomy_pathordered(loop_frames(0.0, tc, 1, N_STEPS))
        push!(shrink, Dict("theta_cap" => tc, "abs_U_minus_I" => abs(Uc - 1.0),
                           "phase" => angle(Uc), "expected_phase" => +enclosed_solid_angle(tc, 1) / 2))
    end
    shrink_monotone = all(shrink[i]["abs_U_minus_I"] > shrink[i+1]["abs_U_minus_I"] for i in 1:length(shrink)-1)
    shrink_to_identity = shrink[end]["abs_U_minus_I"] < 1e-2 && shrink[1]["abs_U_minus_I"] > 0.1
    shrink_flux_max_err = maximum(abs(wrap(c["phase"] - c["expected_phase"])) for c in shrink)

    # CONTROL (erase): OPEN path -> not gauge-invariant
    arc_len = (3 * N_STEPS) ÷ 4
    fr_open = fr_dyn[1:arc_len+1]
    gauge(sf) = 0.7 * sin(2pi * sf)                 # vanishes at sf=0 and sf=1 (closed endpoints)
    apply_gauge(frames, ntot) = [exp(im * gauge((s - 1) / ntot)) * frames[s] for s in 1:length(frames)]
    U_dyn_g = holonomy_pathordered(apply_gauge(fr_dyn, N_STEPS))
    closed_gauge_invariant = abs(wrap(angle(U_dyn_g) - phase_dyn)) < 1e-6
    U_open = holonomy_pathordered(fr_open)
    U_open_g = holonomy_pathordered(apply_gauge(fr_open, N_STEPS))
    open_gauge_dependent = abs(wrap(angle(U_open_g) - angle(U_open))) > 1e-3

    # CONTROL (deepseek): colatitude KNOB g in [0,1] -- NUMERICS-CONSISTENCY check (re-tiered post-audit)
    g_values = [1.0, 0.5, 0.1, 0.0]
    curvature_curve = []
    for g in g_values
        Ug = holonomy_pathordered(curvature_knob_frames(theta_cap, g, N_STEPS))
        push!(curvature_curve, Dict("g" => g, "abs_U_minus_I" => abs(Ug - 1.0),
                                    "phase" => angle(Ug),
                                    "expected_phase_g_Omega_over_2" => g * Omega / 2))
    end
    knob_flux_max_err = maximum(abs(wrap(c["phase"] - c["expected_phase_g_Omega_over_2"]))
                                for c in curvature_curve)
    g0 = curvature_curve[findfirst(c -> c["g"] == 0.0, curvature_curve)]
    # g=0 STRUCTURAL ZERO (alpha_g=0 -> phi-independent frame -> U=I): degenerate-endpoint floor only.
    g0_degenerate_endpoint_consistent = g0["abs_U_minus_I"] < 1e-6
    knob_monotone = all(curvature_curve[i]["abs_U_minus_I"] > curvature_curve[i+1]["abs_U_minus_I"]
                        for i in 1:length(curvature_curve)-1)
    g_lin = 1e-3
    U_lin = holonomy_pathordered(curvature_knob_frames(theta_cap, g_lin, N_STEPS))
    knob_linear_slope = abs(U_lin - 1.0) / g_lin
    knob_slope_matches_half_flux = abs(knob_linear_slope - Omega / 2) < 1e-2
    knob_numerics_consistent = g0_degenerate_endpoint_consistent && knob_flux_max_err < 1e-3 &&
                               knob_monotone && knob_slope_matches_half_flux

    # CONTROL (grok): ODE-DERIVED geometric phase vs LINK-PRODUCT holonomy (no coord smuggling)
    geo_phase_ode = ode_geometric_phase(theta_cap, ODE_B, ODE_M)
    ode_vs_link_match_err = abs(abs(geo_phase_ode) - abs(phase_dyn))
    ode_matches_link = ode_vs_link_match_err < 1e-3
    ode_nontrivial = abs(geo_phase_ode) > 1e-3
    # ODE NEGATIVE CONTROL (closes audit gap): flat loop (theta_cap=0) -> ODE phase ~0 -> the ODE phase
    # is a real measurement that flips curved->nontrivial / flat->trivial.
    geo_phase_ode_flat = ode_geometric_phase(0.0, ODE_B, ODE_M)
    ode_flat_loop_trivial = abs(geo_phase_ode_flat) < 1e-3
    ode_flips_curved_vs_flat = ode_nontrivial && ode_flat_loop_trivial
    # THE genuine coordinate-baking resolution (NOT the self-authored knob): flat-connection + ODE.
    coordinate_baking_resolved = flat_trivial && dyn_nontrivial && ode_matches_link &&
                                 ode_flips_curved_vs_flat

    ablation_delta = abs(U_dyn - 1.0) - abs(U_direct - 1.0)

    invariants = Dict(
        "n_steps" => N_STEPS, "theta_cap" => theta_cap, "enclosed_solid_angle" => Omega,
        "dynamic_holonomy_abs_minus_I" => abs(U_dyn - 1.0), "dynamic_holonomy_phase" => phase_dyn,
        "expected_holonomy_phase" => expected_phase, "berry_phase_gamma" => -Omega / 2,
        "flux_match_err" => flux_match_err,
        "direct_holonomy_abs_minus_I" => abs(U_direct - 1.0),
        "trivial_loop_holonomy_abs_minus_I" => abs(U_triv - 1.0),
        "trivial_loop_solid_angle" => enclosed_solid_angle(0.0, 1),
        "flat_connection_holonomy_abs_minus_I" => abs(U_flat - 1.0),
        "shrink_family" => shrink, "shrink_flux_max_err" => shrink_flux_max_err,
        "closed_loop_phase_under_gauge" => angle(U_dyn_g),
        "open_arc_phase" => angle(U_open), "open_arc_phase_under_gauge" => angle(U_open_g),
        "curvature_knob_curve" => curvature_curve,
        "curvature_knob_flux_max_err" => knob_flux_max_err,
        "curvature_knob_g0_abs_U_minus_I" => g0["abs_U_minus_I"],
        "curvature_knob_linear_slope" => knob_linear_slope,
        "ode_B" => ODE_B, "ode_M" => ODE_M,
        "ode_geometric_phase" => geo_phase_ode,
        "ode_vs_link_match_err" => ode_vs_link_match_err,
        "ode_geometric_phase_flat_loop" => geo_phase_ode_flat,
    )
    tests = Dict(
        "dynamic_eulerian_holonomy_nontrivial" => dyn_nontrivial,
        "holonomy_equals_enclosed_flux" => flux_match_err < 1e-3,
        "direct_lagrangian_holonomy_trivial" => direct_trivial,
    )
    controls = Dict(
        "trivial_loop_holonomy_trivial" => trivial_loop_trivial,
        "flat_connection_same_loop_trivial" => flat_trivial,
        "curvature_load_bearing_curved_nontrivial_flat_trivial" => curvature_load_bearing,
        "real_loop_holonomy_matches_flux" => flux_match_err < 1e-3 && dyn_nontrivial,
        "shrink_loop_holonomy_to_identity" => shrink_to_identity && shrink_monotone,
        "shrink_phase_tracks_flux" => shrink_flux_max_err < 1e-2,
        "closed_holonomy_gauge_invariant" => closed_gauge_invariant,
        "open_path_holonomy_gauge_dependent" => open_gauge_dependent,
        "curvature_knob_g0_degenerate_endpoint_consistent" => g0_degenerate_endpoint_consistent,
        "curvature_knob_phase_reproduces_g_flux_numerics" => knob_flux_max_err < 1e-3,
        "curvature_knob_monotone_in_g" => knob_monotone,
        "curvature_knob_linear_slope_matches_half_flux" => knob_slope_matches_half_flux,
        "curvature_knob_numerics_consistent" => knob_numerics_consistent,
        "ode_geometric_phase_nontrivial" => ode_nontrivial,
        "ode_holonomy_matches_link_product" => ode_matches_link,
        "ode_flat_loop_trivial" => ode_flat_loop_trivial,
        "ode_flips_curved_vs_flat" => ode_flips_curved_vs_flat,
        "coordinate_baking_resolved_by_flat_and_ode" => coordinate_baking_resolved,
    )
    all_tests = all(values(tests)); all_controls = all(values(controls))

    result = Dict(
        "schema" => "codex_ratchet.sim_result.v1", "sim_id" => SIM_ID,
        "classification" => "scratch_diagnostic", "promotion_allowed" => false,
        "formal_admission_allowed" => false, "engine" => "julia_linearalgebra_canon",
        "root_lineage" => Dict("F01_finite_support" => true,
            "N01_order_sensitivity" => "holonomy = PATH-ORDERED product of exp(-i K ds); path ordering around enclosed curvature is what makes U_loop != I. Comoving (Lagrangian) order telescopes to I."),
        "source_target" => "ring-checkerboard runbook + axes12_deep_vein Axis2 (K_t=i V^dag V_dot) -- the loop-holonomy discriminator the euler sim audit named as the real test",
        "claim" => "Axis-2 K_t holonomy nontrivial IFF the closed frame loop encloses curvature; comoving/trivial/flat loops -> I; nontrivial holonomy phase magnitude = enclosed Berry flux Omega/2. Independent path-ordered exp(-iK ds) route.",
        "invariants" => invariants, "tests" => tests, "controls" => controls,
        "all_tests_pass" => all_tests, "all_controls_pass" => all_controls,
        "ablation_outcome_delta" => Dict("dynamic_curved_abs_minus_I" => abs(U_dyn - 1.0),
            "direct_comoving_abs_minus_I" => abs(U_direct - 1.0), "delta" => ablation_delta),
        "honest_scope" => Dict(
            "earns" => "independent Julia (canon) path-ordered recomputation of the Axis-2 K_t loop-holonomy; curvature-coupled discriminator (curved loop -> U!=I = flux, comoving/trivial/flat -> I, open path not gauge-invariant). Coordinate-baking is resolved by the phi-DEPENDENT flat-connection control + the ODE control (exact Rodrigues 2x2 path-ordered evolution, no solid-angle reference, matches link product AND flips flat->0); scratch ceiling, arbiter leg",
            "does_not_earn" => "M(C), Axis0 closure, QIT engine, smooth manifold, physics. POST-AUDIT (2026-06-15): the deepseek colatitude-knob is a NUMERICS-CONSISTENCY check (phase=g*Omega/2 is an analytic identity of alpha_g; g=0 is a structural zero), NOT a coordinate-baking resolver. The cross-engine numeric agreement on the holonomy/knob legs reflects the same overlap-product math in distinct float paths; only the ODE legs are formula-independent across engines. Needs cross-engine agreement + fleet audit"),
        "TOOL_MANIFEST" => Dict("julia_linearalgebra" => Dict("tried" => true, "used" => true,
            "reason" => "exact complex spin-1/2 frames, connection 1-form i<n|dn>, PATH-ORDERED product of exp(-i K ds) for the holonomy, solid-angle/Stokes flux; canon arbiter, distinct numerical route from the overlap-product leg")),
        "TOOL_INTEGRATION_DEPTH" => "load_bearing",
    )
    mkpath(dirname(RESULT))
    open(RESULT, "w") do io
        JSON.print(io, result, 2); write(io, "\n")
    end
    println("wrote $RESULT")
    println("all_tests_pass=$all_tests all_controls_pass=$all_controls")
    println("dynamic |U-I|=$(abs(U_dyn-1.0)) phase=$phase_dyn expected=$expected_phase flux_err=$flux_match_err")
    println("direct |U-I|=$(abs(U_direct-1.0)) trivial=$(abs(U_triv-1.0)) flat=$(abs(U_flat-1.0))")
    println("shrink monotone=$shrink_monotone open_gauge_dep=$open_gauge_dependent")
    println("[deepseek] knob (NUMERICS) |U(g)-I|=$([round(c["abs_U_minus_I"],digits=6) for c in curvature_curve]) g0_struct_zero=$g0_degenerate_endpoint_consistent flux_err=$knob_flux_max_err slope=$knob_linear_slope (Om/2=$(Omega/2))")
    println("[grok]     ode geo phase=$geo_phase_ode link phase=$phase_dyn match_err=$ode_vs_link_match_err matches=$ode_matches_link")
    println("[grok-neg] ode flat-loop phase=$geo_phase_ode_flat flat_trivial=$ode_flat_loop_trivial flips=$ode_flips_curved_vs_flat coord_baking_resolved=$coordinate_baking_resolved")
    return (all_tests && all_controls) ? 0 : 1
end

exit(main())
