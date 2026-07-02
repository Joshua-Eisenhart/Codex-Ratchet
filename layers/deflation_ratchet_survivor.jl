#!/usr/bin/env julia
# =============================================================================
# deflation_ratchet_survivor.jl
#
# Grok deflation control for the ratchet order-dependent survivor claim.
# classification = deflation_ratchet_poc ; promotion_allowed = false.
#
# Question:
#   Existing genuine-channel kill-tests report that distinct orderings of the
#   heterogeneous channel set reach distinct survivor states, while the commuting
#   control reaches the same survivor. Does that survivor spread require genuine
#   distinct layers in distinct orders, or can a single fixed base channel with
#   only spin^c / connection lift index varied reproduce the same spread?
#
# Boundary:
#   The deflation side uses one fixed base channel at a time, repeated to a
#   long-horizon survivor. It does not compose a heterogeneous word or reorder
#   multiple layers. The only changed variable is the lift index m on the same
#   fixed base.
# =============================================================================

using LinearAlgebra
using Random
using Statistics
import JSON
import Z3

const RESULT_PATH = joinpath(@__DIR__, "deflation_ratchet_survivor_results.json")
const CLAIM_SOURCE = "system_v5/julia_carrier/layers/ratchet_survivor_reach_killtest.jl"
const CLAIM_RESULT = "system_v5/julia_carrier/layers/ratchet_survivor_reach_killtest_results.json"
const SEED = 20260602
const N_RHO = 20
const ETA_BASE = pi / 4
const SPIN_LIFTS = collect(1:7)

const I2 = Matrix{ComplexF64}(I, 2, 2)
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SP = ComplexF64[0 1; 0 0]
const SM = ComplexF64[0 0; 1 0]
const P0 = (I2 + SZ) / 2
const P1 = (I2 - SZ) / 2
const Qp = (I2 + SX) / 2
const Qm = (I2 - SX) / 2
const PAULI4 = (I2, SX, SY, SZ)

trace_norm(M) = sum(svdvals(M))

Phi_Ti(rho, q) = (1 - q) * rho + q * (P0 * rho * P0 + P1 * rho * P1)
Phi_Te(rho, q) = (1 - q) * rho + q * (Qp * rho * Qp + Qm * rho * Qm)
Ux(theta) = ComplexF64[cos(theta / 2) (-im * sin(theta / 2)); (-im * sin(theta / 2)) cos(theta / 2)]
Uz(phi) = ComplexF64[cis(-phi / 2) 0; 0 cis(phi / 2)]
Phi_Fi(rho, theta) = Ux(theta) * rho * Ux(theta)'
Phi_Fe(rho, phi) = Uz(phi) * rho * Uz(phi)'

dissipator(L, rho) = L * rho * L' - 0.5 * ((L' * L) * rho + rho * (L' * L))
commutator_flow(H, rho) = -im * (H * rho - rho * H)

function gksl_step_evolve(rho0, H, L; gamma=1.0, eps=1.0, T=4.0, steps=400)
    dt = T / steps
    r = rho0
    for _ in 1:steps
        r = r + dt * (gamma * dissipator(L, r) + eps * commutator_flow(H, r))
        r = (r + r') / 2
        tr_r = real(tr(r))
        abs(tr_r) > 1e-12 && (r = r / tr_r)
    end
    return r
end

function hopf_h0(phi::Float64, chi::Float64, eta::Float64)
    psi = ComplexF64[exp(im * (phi + chi)) * cos(eta), exp(im * (phi - chi)) * sin(eta)]
    psi = psi / norm(psi)
    n = [real(psi' * (P * psi)) for P in (SX, SY, SZ)]
    nn = norm(n)
    nhat = nn < 1e-12 ? [0.0, 0.0, 1.0] : n ./ nn
    return nhat[1] * SX + nhat[2] * SY + nhat[3] * SZ
end

function ptm(chan)
    T = zeros(Float64, 4, 4)
    for j in 1:4, i in 1:4
        T[i, j] = real(tr(PAULI4[i] * chan(PAULI4[j])) / 2)
    end
    return T
end

function rand_rho(rng)
    psi = ComplexF64[randn(rng) + im * randn(rng), randn(rng) + im * randn(rng)]
    psi = psi / norm(psi)
    pure = psi * psi'
    p = 0.2 + 0.6 * rand(rng)
    rho = p * pure + (1 - p) * (I2 / 2)
    return (rho + rho') / 2 / real(tr((rho + rho') / 2))
end

function apply_word(word, rho)
    r = rho
    for f in word
        r = f(r)
    end
    return r
end

build_depth_word(base, reps) = reduce(vcat, fill(base, reps))

function order_dependent_survivors(channel_set, perms, seed_rho; horizon_reps=40)
    survivors = Matrix{ComplexF64}[]
    for perm in perms
        base = [channel_set[i] for i in perm]
        word = build_depth_word(base, horizon_reps)
        push!(survivors, apply_word(word, seed_rho))
    end
    dists = Float64[]
    for a in 1:length(survivors), b in a+1:length(survivors)
        push!(dists, trace_norm(survivors[a] - survivors[b]))
    end
    return survivors, dists
end

function irreversibility_residual(base, rhos)
    fwd_word = base
    rev_word = reverse(base)
    order_disc = Float64[]
    for rho in rhos
        driven = apply_word(fwd_word, rho)
        back_rev = apply_word(rev_word, driven)
        back_fwd = apply_word(fwd_word, driven)
        push!(order_disc, trace_norm(back_rev - back_fwd))
    end
    return mean(order_disc), maximum(order_disc)
end

function genuine_channel_set()
    q = 0.65
    ang = 0.9
    phi0, chi0, eta0 = 2pi * 0.21, 2pi * 0.13, pi / 4
    H0 = hopf_h0(phi0, chi0, eta0)
    channels = [
        rho -> Phi_Ti(rho, q),
        rho -> Phi_Fi(rho, ang),
        rho -> gksl_step_evolve(rho, +H0, SM; T=4.0, steps=400),
        rho -> Phi_Te(rho, q),
        rho -> Phi_Fe(rho, ang),
        rho -> gksl_step_evolve(rho, -H0, SP; T=4.0, steps=400),
    ]
    names = ["Ti", "Fi", "WeylL", "Te", "Fe", "WeylR"]
    return channels, names, H0
end

function commuting_channel_set()
    channels = [
        rho -> Phi_Ti(rho, 0.30),
        rho -> Phi_Ti(rho, 0.55),
        rho -> Phi_Ti(rho, 0.65),
        rho -> Phi_Ti(rho, 0.80),
    ]
    names = ["Tz.30", "Tz.55", "Tz.65", "Tz.80"]
    return channels, names
end

function spin_connection_lift(m::Int, H0)
    return exp(-im * ETA_BASE * m * H0)
end

central_u1_lift(m::Int) = cis(ETA_BASE * m) * I2

function lifted_channel(base_chan, U)
    return rho -> U * base_chan(U' * rho * U) * U'
end

function single_base_lift_survivors(base_chan, base_name, seed_rho, H0; lift_kind="connection", horizon_applications=240)
    survivors = Matrix{ComplexF64}[]
    convergence = Float64[]
    for m in SPIN_LIFTS
        U = lift_kind == "central_u1" ? central_u1_lift(m) : spin_connection_lift(m, H0)
        f = lifted_channel(base_chan, U)
        r = seed_rho
        for _ in 1:horizon_applications
            r = f(r)
        end
        r_next = f(r)
        push!(survivors, r)
        push!(convergence, trace_norm(r_next - r))
    end
    dists = Float64[]
    pairs = Vector{Dict{String,Any}}()
    for a in 1:length(survivors), b in a+1:length(survivors)
        d = trace_norm(survivors[a] - survivors[b])
        push!(dists, d)
        push!(pairs, Dict("lift_a" => SPIN_LIFTS[a], "lift_b" => SPIN_LIFTS[b], "trace_distance" => d))
    end
    return Dict(
        "base_channel" => base_name,
        "lift_kind" => lift_kind,
        "single_fixed_base" => true,
        "multi_layer_composition_used" => false,
        "spin_lifts_varied" => SPIN_LIFTS,
        "horizon_applications_of_one_lifted_channel" => horizon_applications,
        "pairwise_survivor_tracedist_max" => isempty(dists) ? 0.0 : maximum(dists),
        "pairwise_survivor_tracedist_mean" => isempty(dists) ? 0.0 : mean(dists),
        "pairwise_survivor_tracedist_all" => dists,
        "pairwise_survivor_pairs" => pairs,
        "max_one_more_step_delta" => maximum(convergence),
        "one_more_step_deltas" => convergence,
    )
end

function z3_zero_obstruction(measured_spread::Float64; scale=1_000_000_000)
    ctx = Z3.Context()
    s = Z3.Solver(ctx)
    spread = Z3.IntVar("spread", ctx)
    same_survivor_law = Z3.BoolVar("same_survivor_law", ctx)
    Z3.add(s, Z3.Or([Z3.Not(same_survivor_law), spread == Z3.IntVal(0, ctx)]))
    Z3.add(s, same_survivor_law == Z3.BoolVal(true, ctx))
    Z3.add(s, spread == Z3.IntVal(round(Int, scale * abs(measured_spread)), ctx))
    return string(Z3.check(s))
end

function z3_deflation_threshold(best_single::Float64, threshold::Float64; scale=1_000_000_000)
    ctx = Z3.Context()
    s = Z3.Solver(ctx)
    shortfall = Z3.IntVar("threshold_shortfall", ctx)
    measured_shortfall = max(0, round(Int, scale * threshold) - round(Int, scale * best_single))
    deflated = Z3.BoolVar("ratchet_deflated", ctx)
    Z3.add(s, Z3.Or([Z3.Not(deflated), shortfall == Z3.IntVal(0, ctx)]))
    Z3.add(s, deflated == Z3.BoolVal(true, ctx))
    Z3.add(s, shortfall == Z3.IntVal(measured_shortfall, ctx))
    return string(Z3.check(s))
end

function main()
    rng = MersenneTwister(SEED)
    rhos = [rand_rho(rng) for _ in 1:N_RHO]
    seed_rho = rand_rho(MersenneTwister(SEED + 777))

    genuine_channels, genuine_names, H0 = genuine_channel_set()
    commuting_channels, commuting_names = commuting_channel_set()

    het_perms = [
        [1, 2, 3, 4, 5, 6], [6, 5, 4, 3, 2, 1], [3, 6, 1, 4, 2, 5],
        [1, 3, 5, 2, 4, 6], [4, 2, 6, 1, 5, 3], [2, 4, 6, 1, 3, 5],
    ]
    comm_perms = [[1, 2, 3, 4], [4, 3, 2, 1], [2, 4, 1, 3], [3, 1, 4, 2]]

    _, genuine_dists = order_dependent_survivors(genuine_channels, het_perms, seed_rho)
    _, commuting_dists = order_dependent_survivors(commuting_channels, comm_perms, seed_rho)
    genuine_max = maximum(genuine_dists)
    genuine_mean = mean(genuine_dists)
    commuting_max = maximum(commuting_dists)
    irrevers_mean, irrevers_max = irreversibility_residual(genuine_channels, rhos)

    deepest_len = max(240, 6 * 40)
    op_scale = maximum(norm(ptm(f)) for f in vcat(genuine_channels, commuting_channels))
    noise_floor = eps(Float64) * op_scale * deepest_len * 8.0
    convergence_floor = max(1.0e-8, 10000.0 * noise_floor)
    same_spread_threshold = max(0.95 * genuine_max, 1000.0 * noise_floor)
    partial_spread_threshold = max(0.05 * genuine_max, 1000.0 * noise_floor)

    central_reports = [
        single_base_lift_survivors(genuine_channels[i], genuine_names[i], seed_rho, H0; lift_kind="central_u1")
        for i in eachindex(genuine_channels)
    ]
    connection_reports = [
        single_base_lift_survivors(genuine_channels[i], genuine_names[i], seed_rho, H0; lift_kind="connection")
        for i in eachindex(genuine_channels)
    ]

    for row in vcat(central_reports, connection_reports)
        row["converged_to_survivor_under_one_more_step_gate"] = row["max_one_more_step_delta"] <= convergence_floor
        row["spread_ratio_vs_genuine_order_max"] = row["pairwise_survivor_tracedist_max"] / genuine_max
        row["reproduces_same_spread"] = row["converged_to_survivor_under_one_more_step_gate"] &&
                                        row["pairwise_survivor_tracedist_max"] >= same_spread_threshold
    end

    valid_connection = [row for row in connection_reports if row["converged_to_survivor_under_one_more_step_gate"]]
    best_connection = isempty(valid_connection) ? nothing :
        valid_connection[argmax([row["pairwise_survivor_tracedist_max"] for row in valid_connection])]
    best_single = best_connection === nothing ? 0.0 : best_connection["pairwise_survivor_tracedist_max"]
    best_ratio = best_connection === nothing ? 0.0 : best_connection["spread_ratio_vs_genuine_order_max"]

    verdict = if best_single >= same_spread_threshold
        "ratchet_deflated"
    elseif best_single >= partial_spread_threshold
        "mixed"
    else
        "ratchet_survives"
    end

    central_max = maximum(row["pairwise_survivor_tracedist_max"] for row in central_reports)
    z3_genuine_vs_zero = z3_zero_obstruction(genuine_max)
    z3_commuting_vs_zero = z3_zero_obstruction(commuting_max)
    z3_central_vs_zero = z3_zero_obstruction(central_max)
    z3_deflation = z3_deflation_threshold(best_single, same_spread_threshold)

    result = Dict{String,Any}(
        "object_id" => "deflation_ratchet_survivor",
        "classification" => "deflation_ratchet_poc",
        "promotion_allowed" => false,
        "script" => "layers/deflation_ratchet_survivor.jl",
        "result_path" => "layers/deflation_ratchet_survivor_results.json",
        "created_by" => "codex2",
        "seed" => SEED,
        "claim_source" => CLAIM_SOURCE,
        "claim_result" => CLAIM_RESULT,
        "non_numpy" => true,
        "bloch_free" => true,
        "claim_ceiling" => "Deflation/control evidence only. Tests whether the ratchet survivor spread can be reproduced by a single fixed base channel with only spin^c/connection lift index varied. Does not promote a ratchet edge, layer completion, manifold admission, bridge, flux, FEP, Axis0, or physics claim.",
        "finite_map" => "Compare (A) genuine heterogeneous ordered channel words rho -> Phi_perm^horizon(rho) across six orderings with (B) single fixed base channel rho -> (U_m Phi_base(U_m' rho U_m) U_m')^horizon(rho), varying only m in {1..7}; output pairwise trace distances between long-horizon density survivors.",
        "domain" => "density operators in D(C^2); genuine channel set {Ti,Fi,WeylL,Te,Fe,WeylR}; fixed base eta=pi/4; finite spin^c lift indices m=1..7; one fixed seed for survivor comparisons.",
        "codomain_or_output" => "side-by-side survivor trace-distance spread for genuine orderings, commuting control, central U1 lift control, and single-base connection-lift candidates; verdict ratchet_deflated/ratchet_survives/mixed.",
        "carrier_realization" => "Julia ComplexF64 2x2 density operators and genuine CPTP/channel maps copied from the ratchet kill-test family; no state-vector chart readout used for survivor distances.",
        "root_constraints_in_force" => [
            "F01 finite carrier/probes/operators/paths: finite density carrier, finite genuine channels, finite spin-lift index set, finite order/lift paths.",
            "N01 order/lift-sensitive control: heterogeneous order permutations compared against commuting order-erasure and single-base lift-only alternatives.",
        ],
        "dependency_receipts" => [
            CLAIM_SOURCE,
            CLAIM_RESULT,
            "system_v5/julia_carrier/layers/ratchet_accumulation_killtest.jl",
            "system_v5/julia_carrier/layers/order_null_killtest.jl",
            "system_v5/julia_carrier/layers/weyl_on_nested_hopf_tori_V2.jl",
        ],
        "noise_floor" => Dict(
            "value" => noise_floor,
            "definition" => "eps(Float64) * max PTM HS scale * max(240 single-base applications, 6*40 genuine horizon) * 8 safety",
            "max_ptm_hs_scale" => op_scale,
            "deepest_len" => deepest_len,
            "convergence_floor" => convergence_floor,
        ),
        "thresholds" => Dict(
            "same_spread_threshold" => same_spread_threshold,
            "same_spread_rule" => "single-base valid survivor spread >= 95% of genuine order spread",
            "partial_spread_threshold" => partial_spread_threshold,
            "partial_rule" => "mixed if valid single-base spread is at least 5% but below 95% of genuine order spread",
        ),
        "side_by_side_numbers" => Dict(
            "genuine_order_survivor_spread_max" => genuine_max,
            "genuine_order_survivor_spread_mean" => genuine_mean,
            "genuine_order_pairwise_all" => genuine_dists,
            "commuting_control_survivor_spread_max" => commuting_max,
            "commuting_control_pairwise_all" => commuting_dists,
            "genuine_irreversibility_order_discriminating_mean" => irrevers_mean,
            "genuine_irreversibility_order_discriminating_max" => irrevers_max,
            "central_u1_lift_control_spread_max" => central_max,
            "best_singlebase_connection_spread_max" => best_single,
            "best_singlebase_connection_ratio_vs_genuine" => best_ratio,
            "best_singlebase_connection_base" => best_connection === nothing ? nothing : best_connection["base_channel"],
        ),
        "single_base_central_u1_control" => central_reports,
        "single_base_connection_lift_candidates" => connection_reports,
        "best_single_base_connection_lift" => best_connection,
        "anti_tautology_controls" => Dict(
            "commuting_control_same_survivor" => commuting_max < max(1.0e-9, noise_floor),
            "central_u1_density_invisible_control_same_survivor" => central_max < max(1.0e-9, noise_floor),
            "single_base_no_multi_layer_composition" => all(!row["multi_layer_composition_used"] for row in connection_reports),
            "invalid_nonconverged_single_base_channels_do_not_count_for_deflation" => true,
        ),
        "z3_flip" => Dict(
            "zero_survivor_law" => "same-survivor/erased-order law implies spread == 0",
            "genuine_order_vs_zero_verdict" => z3_genuine_vs_zero,
            "commuting_control_vs_zero_verdict" => z3_commuting_vs_zero,
            "central_u1_control_vs_zero_verdict" => z3_central_vs_zero,
            "zero_law_flips" => (z3_genuine_vs_zero == "unsat" && z3_commuting_vs_zero == "sat" && z3_central_vs_zero == "sat"),
            "deflation_threshold_law" => "ratchet_deflated implies best valid single-base spread >= same_spread_threshold",
            "deflation_threshold_verdict" => z3_deflation,
        ),
        "verdict" => Dict(
            "classification" => verdict,
            "ratchet_deflated" => verdict == "ratchet_deflated",
            "ratchet_survives" => verdict == "ratchet_survives",
            "mixed" => verdict == "mixed",
            "deciding" => "genuine_max=$(genuine_max), commuting_max=$(commuting_max), central_u1_max=$(central_max), best_valid_singlebase_connection_max=$(best_single), ratio=$(best_ratio), same_spread_threshold=$(same_spread_threshold)",
            "reading" => verdict == "ratchet_deflated" ?
                "A single fixed base with only spin^c/connection lift varied reproduced the survivor spread at the pre-registered 95% bar; the survivor-spread claim deflates to ordinary single-base lift geometry under this control." :
                verdict == "ratchet_survives" ?
                "Valid single-base spin^c/connection lift choices did not produce meaningful distinct survivor spread; the observed survivor spread still requires genuine distinct ordered layers under this control." :
                "Single-base spin^c/connection lifts produced some distinct survivors but did not reproduce the same spread at the 95% bar; the result is partial/mixed rather than a clean deflation or clean survival.",
        ),
        "allowed_claims" => "Deflation-control verdict for the bounded ratchet survivor spread only.",
        "promotion_status" => "diagnostic_only",
        "blocked_consumers" => [
            "ratchet edge admission",
            "ratchet thesis closure",
            "layer completion",
            "manifold admission",
            "coupling",
            "bridge/Xi/Phi0/Axis0",
            "flux/FEP/physics",
        ],
        "tool_manifest" => Dict(
            "LinearAlgebra" => "load_bearing: density-channel evolution, matrix exponentials, trace distances, PTM scale, convergence residuals.",
            "Random" => "load_bearing: fixed seeded density probes matching ratchet kill-test family.",
            "Statistics" => "supportive: means for side-by-side survivor and irreversibility summaries.",
            "Z3" => "load_bearing: zero-law verdict flip and deflation-threshold gate over measured spreads.",
            "JSON" => "supportive: result emission.",
        ),
        "tool_integration_depth" => Dict(
            "LinearAlgebra" => "load_bearing",
            "Random" => "load_bearing",
            "Z3" => "load_bearing",
            "Statistics" => "supportive",
            "JSON" => "supportive",
        ),
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end

    println("="^96)
    println("DEFLATION RATCHET SURVIVOR :: classification=deflation_ratchet_poc")
    println("promotion_allowed=false")
    println("result_path: ", RESULT_PATH)
    println("="^96)
    println("genuine order survivor max:      ", genuine_max)
    println("genuine order survivor mean:     ", genuine_mean)
    println("commuting control survivor max:  ", commuting_max)
    println("central U1 lift control max:     ", central_max)
    println("best valid single-base max:      ", best_single, "  base=", best_connection === nothing ? "none" : best_connection["base_channel"])
    println("best/genuine ratio:              ", best_ratio)
    println("same-spread threshold (95%):     ", same_spread_threshold)
    println("irreversibility mean/max:        ", irrevers_mean, " / ", irrevers_max)
    println("Z3 zero-law: genuine=", z3_genuine_vs_zero, " commuting=", z3_commuting_vs_zero, " central=", z3_central_vs_zero)
    println("Z3 deflation-threshold verdict:  ", z3_deflation)
    println("VERDICT: ", verdict)
    println("="^96)

    return result
end

main()
