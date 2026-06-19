#!/usr/bin/env julia
# ax4_julia.jl
#
# object_id: ax4_variance_order_split_v1
# claim_ceiling: Axis-4 variance-order split finite map over F01+N01.
#   Does NOT assert layer-completion, manifold admission, coupling,
#   bridge, flux, or physics. A state that passes is a candidate, not
#   a proven object.
# promotion_allowed: false
#
# Root gates:
#   F01: finite carrier/probe/operator/path set (ensemble of 8/16/32/64 states,
#        4 strokes per ordering, 2x2 density matrices)
#   N01: non-commuting operation domain (U=x-rotation, E=z-dephasing do not commute;
#        commuting control: U=Fe z-rotation, E=Ti z-dephasing, both z-basis, ~0 gap)
#
# Finite map:
#   (initial_state, ordering_class) ->
#     {variance_trajectory[4], final_rho, trajectory_distance, order_gap, axis4_class}
#
# Domain:
#   initial_state in ensemble (size N in {8,16,32,64})
#   ordering_class in {deductive_FiTiFeTe, deductive_FeTiFiTe,
#                      inductive_TiFiTeFe, inductive_TeFiTiFe,
#                      commuting_control}
#
# Codomain:
#   variance trajectory (purity complement 1-Tr(rho^2) at each step),
#   final density matrix,
#   trajectory distance ||traj_ded - traj_ind||_2,
#   Frobenius order gap ||rho_ded_final - rho_ind_final||_F,
#   axis4_class label (deductive/inductive/commuting_control)
#
# Variance trajectory characterization:
#   deductive (U.E.U.E): U-stroke first -> variance often rises then falls (front-loaded variance change)
#   inductive (E.U.E.U): E-stroke first -> variance changes back-loaded (dephasing first locks early)

using LinearAlgebra
using Random
using Statistics
using Dates

try
    @eval using JSON
catch _
    try
        import Pkg
        Pkg.activate(@__DIR__; io=devnull)
        @eval using JSON
    catch e2
        error("JSON unavailable: $e2")
    end
end

# ── constants ─────────────────────────────────────────────────────────────────
const OBJECT_ID         = "ax4_variance_order_split_v1"
const CLAIM_CEILING     = "Axis-4 variance-order split finite map; not layer-complete; not bridge; promotion_allowed=false"
const PROMOTION_ALLOWED = false
const RESULT_PATH       = joinpath(@__DIR__, "ax4_julia_results.json")
const RNG_SEED          = 20260603
const SIZE_LADDER       = [8, 16, 32, 64]
const TRAJ_EPS          = 1.0e-9   # trajectory distance threshold for earned split
const ORDER_EPS         = 1.0e-9   # Frobenius order-gap threshold
const COMMUTE_EPS       = 1.0e-6   # commuting control gap should be < this

# ── Pauli matrices ─────────────────────────────────────────────────────────────
const I2 = Matrix{ComplexF64}(I, 2, 2)
const σx = ComplexF64[0 1; 1 0]
const σy = ComplexF64[0 -1im; 1im 0]
const σz = ComplexF64[1 0; 0 -1]

# ── stroke definitions ─────────────────────────────────────────────────────────
# Fi: x-rotation by pi/2  (exp(-i pi/4 σx))
const Fi = exp(-im * (π/4) * σx)
# Fe: z-rotation by pi/2  (exp(-i pi/4 σz))
const Fe = exp(-im * (π/4) * σz)

# Hadamard (change-of-basis x<->z)
const H  = (σx + σz) / √2

# Ti: dephase in z-basis  rho -> diag(rho)
function Ti_dephase(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    d = diag(rho)
    return ComplexF64[d[1] 0; 0 d[2]]
end

# Te: dephase in x-basis  (rotate to x, z-dephase, rotate back)
function Te_dephase(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    rho_x = H * rho * H'           # rotate to x-basis
    d     = diag(rho_x)
    rho_xd = ComplexF64[d[1] 0; 0 d[2]]
    return H' * rho_xd * H         # rotate back
end

# Apply a unitary stroke U as a superoperator: rho -> U rho U†
function apply_unitary(U::Matrix{ComplexF64}, rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    return U * rho * U'
end

# ── variance observable ────────────────────────────────────────────────────────
# purity_complement = 1 - Tr(rho^2)  ∈ [0, 0.5] for a qubit
function purity_complement(rho::Matrix{ComplexF64})::Float64
    return real(1.0 - tr(rho * rho))
end

# ── stroke sequence executor ───────────────────────────────────────────────────
# A stroke is either (:U, matrix) or (:E, function)
# Returns (trajectory::Vector{Float64}, final_rho::Matrix)
function apply_stroke_sequence(
        rho0::Matrix{ComplexF64},
        strokes::Vector{Tuple{Symbol, Any}}
    )
    traj  = Float64[]
    rho   = copy(rho0)
    for (kind, op) in strokes
        if kind == :U
            rho = apply_unitary(op, rho)
        elseif kind == :E
            rho = op(rho)
        else
            error("Unknown stroke kind: $kind")
        end
        push!(traj, purity_complement(rho))
    end
    return traj, rho
end

# ── ordering definitions ───────────────────────────────────────────────────────
# Deductive: U.E.U.E
const DEDUCTIVE_A = [(:U, Fi), (:E, Ti_dephase), (:U, Fe), (:E, Te_dephase)]
const DEDUCTIVE_B = [(:U, Fe), (:E, Ti_dephase), (:U, Fi), (:E, Te_dephase)]
# Inductive: E.U.E.U
const INDUCTIVE_A = [(:E, Ti_dephase), (:U, Fi), (:E, Te_dephase), (:U, Fe)]
const INDUCTIVE_B = [(:E, Te_dephase), (:U, Fi), (:E, Ti_dephase), (:U, Fe)]
# Commuting control: U=Fe (z-rot), E=Ti (z-dephase), both z-basis -> should commute
# Order UEUE vs EUEU with commuting pair -> gap ~ 0
const COMMUTING_UE = [(:U, Fe), (:E, Ti_dephase), (:U, Fe), (:E, Ti_dephase)]
const COMMUTING_EU = [(:E, Ti_dephase), (:U, Fe), (:E, Ti_dephase), (:U, Fe)]

# ── random L/R Weyl spinor density matrices ───────────────────────────────────
function random_weyl_density(rng::AbstractRNG, sign::Float64)
    # Parameterize on Bloch sphere; for Weyl spinor, just a pure qubit state
    theta = π * rand(rng)
    phi   = 2π * rand(rng)
    chi   = 2π * rand(rng)
    # sheet_sign flips phase relationship between components (L vs R chirality)
    psi = ComplexF64[
        cis(phi + sign * chi) * cos(theta/2),
        cis(phi - sign * chi) * sin(theta/2),
    ]
    psi ./= norm(psi)
    return psi * psi'
end

function make_ensemble(rng::AbstractRNG, N::Int)
    rhos = Matrix{ComplexF64}[]
    for i in 1:N
        # Alternate L (+1) and R (-1) Weyl spinors
        sign = (i % 2 == 0) ? +1.0 : -1.0
        push!(rhos, random_weyl_density(rng, sign))
    end
    return rhos
end

# ── trajectory analysis ────────────────────────────────────────────────────────
function trajectory_distance(t1::Vector{Float64}, t2::Vector{Float64})::Float64
    return norm(t1 .- t2)
end

function frobenius_gap(rho1::Matrix{ComplexF64}, rho2::Matrix{ComplexF64})::Float64
    return norm(rho1 .- rho2)
end

function characterize_how_differ(td::Vector{Float64}, ti::Vector{Float64})::String
    # Compute gradient of each trajectory (finite differences)
    gd = diff(td)
    gi = diff(ti)
    # Check where variance changes most: deductive typically front-loads
    # (large early change in variance), inductive back-loads
    front_d = abs(gd[1])
    back_d  = abs(gd[end])
    front_i = abs(gi[1])
    back_i  = abs(gi[end])
    deductive_front = front_d > back_d
    inductive_back  = back_i > front_i
    if deductive_front && inductive_back
        return "deductive front-loads variance reduction (large early Δ); inductive back-loads it (large late Δ)"
    elseif deductive_front && !inductive_back
        return "deductive front-loads variance reduction; inductive does not clearly back-load on this ensemble"
    elseif !deductive_front && inductive_back
        return "deductive does not clearly front-load; inductive back-loads variance reduction"
    else
        return "no clear front/back loading pattern — trajectories differ but without monotone loading structure"
    end
end

# ── positive / negative / boundary checks ─────────────────────────────────────
function density_valid(rho::Matrix{ComplexF64})::Bool
    tr_ok  = abs(tr(rho) - 1.0) < 1e-10
    herm   = norm(rho - rho') < 1e-10
    evals  = eigvals(Hermitian((rho + rho') / 2))
    pos_ok = all(e >= -1e-10 for e in evals)
    return tr_ok && herm && pos_ok
end

# ── per-size analysis ──────────────────────────────────────────────────────────
function run_at_size(N::Int, rng_seed::Int)
    rng = MersenneTwister(rng_seed + N)
    ensemble = make_ensemble(rng, N)

    traj_ded_A_all = Vector{Float64}[]
    traj_ind_A_all = Vector{Float64}[]
    gap_ded_ind_all = Float64[]
    gap_commute_all = Float64[]

    state_results = Dict{String,Any}[]

    for (idx, rho0) in enumerate(ensemble)
        # Positive: deductive and inductive orderings with non-commuting strokes
        traj_ded_A, rho_ded_A = apply_stroke_sequence(rho0, DEDUCTIVE_A)
        traj_ded_B, rho_ded_B = apply_stroke_sequence(rho0, DEDUCTIVE_B)
        traj_ind_A, rho_ind_A = apply_stroke_sequence(rho0, INDUCTIVE_A)
        traj_ind_B, rho_ind_B = apply_stroke_sequence(rho0, INDUCTIVE_B)

        # Commuting control: UEUE vs EUEU with commuting pair
        traj_com_ue, rho_com_ue = apply_stroke_sequence(rho0, COMMUTING_UE)
        traj_com_eu, rho_com_eu = apply_stroke_sequence(rho0, COMMUTING_EU)

        td_A = trajectory_distance(traj_ded_A, traj_ind_A)
        fgap = frobenius_gap(rho_ded_A, rho_ind_A)
        cgap = frobenius_gap(rho_com_ue, rho_com_eu)

        push!(traj_ded_A_all, traj_ded_A)
        push!(traj_ind_A_all, traj_ind_A)
        push!(gap_ded_ind_all, fgap)
        push!(gap_commute_all, cgap)

        # Axis4 class: deductive if final state is closer to deductive trajectory
        # (partition by which ordering produced the state)
        axis4_class = "deductive"  # by construction of producing stroke
        # But we can also check: does the trajectory distance actually split?
        traj_split_real = td_A > TRAJ_EPS

        push!(state_results, Dict(
            "state_index" => idx,
            "traj_deductive_A" => traj_ded_A,
            "traj_inductive_A" => traj_ind_A,
            "trajectory_distance_A" => td_A,
            "order_gap_frobenius" => fgap,
            "commuting_control_gap" => cgap,
            "commuting_control_near_zero" => cgap < COMMUTE_EPS,
            "traj_split_real" => traj_split_real,
            "rho0_valid" => density_valid(rho0),
            "rho_ded_valid" => density_valid(rho_ded_A),
            "rho_ind_valid" => density_valid(rho_ind_A),
            "rho_com_ue_valid" => density_valid(rho_com_ue),
            "rho_com_eu_valid" => density_valid(rho_com_eu),
        ))
    end

    # Aggregate trajectory (mean across ensemble)
    mean_traj_ded = mean(traj_ded_A_all)
    mean_traj_ind = mean(traj_ind_A_all)
    mean_td = mean([trajectory_distance(traj_ded_A_all[i], traj_ind_A_all[i]) for i in 1:N])
    mean_gap = mean(gap_ded_ind_all)
    mean_cgap = mean(gap_commute_all)
    max_cgap  = maximum(gap_commute_all)

    how = characterize_how_differ(mean_traj_ded, mean_traj_ind)

    # Negative check: commuting control gap should be near zero
    commuting_control_zero = max_cgap < COMMUTE_EPS

    # Positive check: trajectory distance should exceed threshold
    mean_traj_dist = mean_td
    trajectories_differ = mean_traj_dist > TRAJ_EPS

    # Order gap
    mean_order_gap = mean_gap

    # Axis4 split: fraction of states with real trajectory split
    n_split = sum(r["traj_split_real"] for r in state_results)
    axis4_split_fraction = n_split / N

    return Dict{String,Any}(
        "N" => N,
        "mean_trajectory_deductive" => mean_traj_ded,
        "mean_trajectory_inductive" => mean_traj_ind,
        "mean_trajectory_distance" => mean_traj_dist,
        "mean_order_gap_frobenius" => mean_order_gap,
        "mean_commuting_control_gap" => mean_cgap,
        "max_commuting_control_gap" => max_cgap,
        "commuting_control_near_zero" => commuting_control_zero,
        "trajectories_differ" => trajectories_differ,
        "axis4_split_fraction" => axis4_split_fraction,
        "axis4_split_real" => axis4_split_fraction > 0.5,
        "how_they_differ" => how,
        "state_results" => state_results,
    )
end

# ── boundary checks ────────────────────────────────────────────────────────────
function boundary_checks()
    results = Dict{String,Any}[]

    # Boundary 1: pure state (zero purity_complement) -> degenerate trajectory
    rho_pure = ComplexF64[1 0; 0 0]  # |0><0|
    traj_ded, rho_ded = apply_stroke_sequence(rho_pure, DEDUCTIVE_A)
    traj_ind, rho_ind = apply_stroke_sequence(rho_pure, INDUCTIVE_A)
    push!(results, Dict(
        "label" => "pure_state_boundary",
        "traj_deductive" => traj_ded,
        "traj_inductive" => traj_ind,
        "traj_distance" => trajectory_distance(traj_ded, traj_ind),
        "order_gap" => frobenius_gap(rho_ded, rho_ind),
    ))

    # Boundary 2: maximally mixed state -> should dephase to itself under E
    rho_mixed = ComplexF64[0.5 0; 0 0.5]
    traj_ded2, rho_ded2 = apply_stroke_sequence(rho_mixed, DEDUCTIVE_A)
    traj_ind2, rho_ind2 = apply_stroke_sequence(rho_mixed, INDUCTIVE_A)
    push!(results, Dict(
        "label" => "maximally_mixed_boundary",
        "traj_deductive" => traj_ded2,
        "traj_inductive" => traj_ind2,
        "traj_distance" => trajectory_distance(traj_ded2, traj_ind2),
        "order_gap" => frobenius_gap(rho_ded2, rho_ind2),
        "note" => "mixed state is E-fixed; only U strokes matter here",
    ))

    # Boundary 3: commuting control on pure state
    traj_com_ue, rho_com_ue = apply_stroke_sequence(rho_pure, COMMUTING_UE)
    traj_com_eu, rho_com_eu = apply_stroke_sequence(rho_pure, COMMUTING_EU)
    push!(results, Dict(
        "label" => "commuting_control_pure_state",
        "traj_UEUE" => traj_com_ue,
        "traj_EUEU" => traj_com_eu,
        "traj_distance" => trajectory_distance(traj_com_ue, traj_com_eu),
        "order_gap" => frobenius_gap(rho_com_ue, rho_com_eu),
        "expect_near_zero_gap" => true,
    ))

    return results
end

# ── wrong-structure (erased/flipped) control ──────────────────────────────────
# Anti-tautology: use commuting U and E -> order gap should collapse to ~0
# This tests that the split is NOT by construction but depends on non-commutativity.
function wrong_structure_control(N::Int, rng_seed::Int)
    rng = MersenneTwister(rng_seed + N + 9999)
    ensemble = make_ensemble(rng, N)
    gaps = Float64[]
    traj_dists = Float64[]
    for rho0 in ensemble
        # Use COMMUTING_UE vs COMMUTING_EU
        traj_ue, rho_ue = apply_stroke_sequence(rho0, COMMUTING_UE)
        traj_eu, rho_eu = apply_stroke_sequence(rho0, COMMUTING_EU)
        push!(gaps, frobenius_gap(rho_ue, rho_eu))
        push!(traj_dists, trajectory_distance(traj_ue, traj_eu))
    end
    return Dict{String,Any}(
        "N" => N,
        "label" => "commuting_control_wrong_structure",
        "mean_gap" => mean(gaps),
        "max_gap" => maximum(gaps),
        "mean_traj_distance" => mean(traj_dists),
        "max_traj_distance" => maximum(traj_dists),
        "verdict" => maximum(gaps) < COMMUTE_EPS ? "order_collapses_under_commuting" : "WARNING_gap_persists",
    )
end

# ── main ───────────────────────────────────────────────────────────────────────
function main()
    println("Running ax4_variance_order_split_v1 ...")
    t0 = now()

    ladder_results = Dict{String,Any}[]
    for N in SIZE_LADDER
        println("  N=$N ...")
        res = run_at_size(N, RNG_SEED)
        delete!(res, "state_results")   # too large for summary; keep aggregates only
        push!(ladder_results, res)
    end

    # Full state-level results for N=16 only (reference size)
    full_N16 = run_at_size(16, RNG_SEED)
    # Keep state results for N=16 but strip large arrays
    state_summaries = [Dict(
        "state_index" => r["state_index"],
        "traj_deductive_A" => r["traj_deductive_A"],
        "traj_inductive_A" => r["traj_inductive_A"],
        "trajectory_distance_A" => r["trajectory_distance_A"],
        "order_gap_frobenius" => r["order_gap_frobenius"],
        "commuting_control_gap" => r["commuting_control_gap"],
        "commuting_control_near_zero" => r["commuting_control_near_zero"],
        "traj_split_real" => r["traj_split_real"],
    ) for r in full_N16["state_results"]]

    boundary = boundary_checks()
    wsc = wrong_structure_control(32, RNG_SEED)

    # Summary metrics from N=64
    n64 = ladder_results[end]
    summary_td   = n64["mean_trajectory_distance"]
    summary_gap  = n64["mean_order_gap_frobenius"]
    summary_cgap = n64["max_commuting_control_gap"]
    two_directions_earned = n64["trajectories_differ"] && n64["commuting_control_near_zero"] && n64["axis4_split_real"]

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "claim_ceiling" => CLAIM_CEILING,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "root_gates" => ["F01", "N01"],
        "carrier_realization" => "Julia ComplexF64 L/R Weyl spinor-derived 2x2 density matrices",
        "timestamp" => string(t0),
        "size_ladder_results" => ladder_results,
        "n16_state_summaries" => state_summaries,
        "boundary_checks" => boundary,
        "wrong_structure_control" => wsc,
        "summary_n64" => Dict(
            "mean_trajectory_distance" => summary_td,
            "mean_order_gap_frobenius" => summary_gap,
            "max_commuting_control_gap" => summary_cgap,
            "trajectories_differ_above_eps" => n64["trajectories_differ"],
            "commuting_control_near_zero" => n64["commuting_control_near_zero"],
            "axis4_split_fraction" => n64["axis4_split_fraction"],
            "axis4_split_real" => n64["axis4_split_real"],
            "how_they_differ" => n64["how_they_differ"],
            "two_directions_earned" => two_directions_earned,
        ),
        "honest_caveat" => "Two directions are earned iff trajectories_differ AND commuting_control_near_zero AND axis4_split_real. If any of these is false, two_directions_earned=false.",
        "downstream_blocks" => [
            "layer_completion",
            "manifold_admission",
            "coupling",
            "bridge",
            "Axis0",
            "flux",
            "physics",
        ],
    )

    # Write result JSON
    open(RESULT_PATH, "w") do f
        JSON.print(f, result, 2)
    end
    println("Result written to: $RESULT_PATH")

    # Print summary
    println("\n=== Axis-4 Summary (N=64) ===")
    println("  mean_trajectory_distance : $summary_td")
    println("  trajectories_differ      : $(n64["trajectories_differ"])")
    println("  how_they_differ          : $(n64["how_they_differ"])")
    println("  mean_order_gap           : $summary_gap")
    println("  max_commuting_ctrl_gap   : $summary_cgap")
    println("  commuting_ctrl_near_zero : $(n64["commuting_control_near_zero"])")
    println("  axis4_split_fraction     : $(n64["axis4_split_fraction"])")
    println("  axis4_split_real         : $(n64["axis4_split_real"])")
    println("  two_directions_earned    : $two_directions_earned")
    println("  wrong_struct_max_gap     : $(wsc["max_gap"])")
    println("  wrong_struct_verdict     : $(wsc["verdict"])")
    println("\nDone.")
end

main()
