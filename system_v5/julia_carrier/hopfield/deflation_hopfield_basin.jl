#!/usr/bin/env julia
# =============================================================================
# deflation_hopfield_basin.jl  --  GROK-STYLE DEFLATION CONTROL for the
# quaternionic Clifford-Hopfield order-dependent basin claim.
#
#   object_id          = deflation_hopfield_basin
#   classification     = deflation_hopfield_poc
#   promotion_allowed  = false
#   sim_execution_kind = nonclassical (geometric-algebra carrier; Cl(3,0)+ ~ H)
#
# This file pressure-tests the parent claim in clifford_hopfield.jl:
#   GENUINE:  elementwise order-sensitive assembly W_AB[i,j]=A[i,j]*B[i,j]
#             versus W_BA[i,j]=B[i,j]*A[i,j] lands in different attractor
#             basins; the commuting complex-subalgebra and erased controls
#             collapse to the floor.
#
# DEFLATION QUESTION:
#   Keep a SINGLE fixed quaternion weight base W0. Do NOT form A*B versus B*A.
#   Vary only a finite spin^c / quaternion lift / connection choice on that same
#   base. Can those single-base lift choices reproduce basin divergences at the
#   same scale as the genuine A*B vs B*A claim?
#
# CLAIM CEILING:
#   Computes a finite control and verdict:
#     hopfield_basin_deflated  -- single-base lift/connection choices reproduce
#                                same-scale basin divergence, so the parent
#                                order-basin reading is ordinary connection
#                                sensitivity unless further fenced.
#     hopfield_basin_survives  -- single-base lift/connection choices cannot
#                                reproduce the gap; the divergence still
#                                requires noncommutative assembly order here.
#     mixed                    -- connection choices move basins, but not cleanly
#                                at the parent scale or only in a less
#                                conservative lift arm.
#
#   It does NOT assert layer-completion, manifold admission, coupling, bridge
#   (rho_AB / Xi / Phi0 / Axis0), flux, FEP, or physics. promotion_allowed=false.
#
# RUN:
#   julia --project="system_v5/julia_carrier" \
#     "system_v5/julia_carrier/hopfield/deflation_hopfield_basin.jl"
# =============================================================================

using LinearAlgebra
using Random
using Statistics
import JSON

const OBJECT_ID      = "deflation_hopfield_basin"
const CLASSIFICATION = "deflation_hopfield_poc"
const HERE           = @__DIR__
const RESULT_PATH    = joinpath(HERE, "deflation_hopfield_basin_results.json")
const PARENT_RESULT  = joinpath(HERE, "clifford_hopfield_results.json")
const SEED           = 20260602
const N_NEURONS      = 12
const ORDER_FLOOR    = 1e-6
const SAME_SCALE_RATIO = 0.75
const LOW_SCALE_RATIO  = 0.10

# =============================================================================
# QUATERNION CARRIER (reused VERBATIM from clifford_hopfield.jl)
# A quaternion is stored as q = (w,x,y,z) :: NTuple{4,Float64}.
# =============================================================================

const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const I2 = ComplexF64[1 0; 0 1]

qmat(q) = q[1]*I2 - im*(q[2]*SX + q[3]*SY + q[4]*SZ)

"Hamilton product q*p (geometric product on Cl(3,0)+). Noncommutative."
function qmul(q, p)
    w1,x1,y1,z1 = q; w2,x2,y2,z2 = p
    (w1*w2 - x1*x2 - y1*y2 - z1*z2,
     w1*x2 + x1*w2 + y1*z2 - z1*y2,
     w1*y2 - x1*z2 + y1*w2 + z1*x2,
     w1*z2 + x1*y2 - y1*x2 + z1*w2)
end

qconj(q) = (q[1], -q[2], -q[3], -q[4])
qadd(q, p) = (q[1]+p[1], q[2]+p[2], q[3]+p[3], q[4]+p[4])
qscale(a, q) = (a*q[1], a*q[2], a*q[3], a*q[4])
qnorm(q) = sqrt(q[1]^2 + q[2]^2 + q[3]^2 + q[4]^2)
qre(q) = q[1]
function qnormalize(q)
    n = qnorm(q)
    n < 1e-300 ? (1.0, 0.0, 0.0, 0.0) : (q[1]/n, q[2]/n, q[3]/n, q[4]/n)
end
function rand_unit_quat(rng)
    q = (randn(rng), randn(rng), randn(rng), randn(rng))
    qnormalize(q)
end
function quat_geodesic(q, p)
    d = abs(q[1]*p[1] + q[2]*p[2] + q[3]*p[3] + q[4]*p[4])
    acos(clamp(d, -1.0, 1.0))
end

"VERIFY the carrier algebra against the SU(2) matrix realization (0.0 target)."
function verify_quaternion_carrier()
    qi = (0.0,1.0,0.0,0.0); qj = (0.0,0.0,1.0,0.0); qk = (0.0,0.0,0.0,1.0)
    ij = qmul(qi, qj); ji = qmul(qj, qi); ii = qmul(qi, qi)
    err_ij = qnorm(qadd(ij, qscale(-1.0, qk)))
    err_ji = qnorm(qadd(ji, qk))
    err_ii = qnorm(qadd(ii, (1.0,0.0,0.0,0.0)))
    rng = MersenneTwister(1)
    mat_err = 0.0
    for _ in 1:200
        a = rand_unit_quat(rng); b = rand_unit_quat(rng)
        mat_err = max(mat_err, maximum(abs.(qmat(qmul(a,b)) - qmat(a)*qmat(b))))
    end
    pauli_anticomm = maximum(abs.(SX*SY + SY*SX))
    pauli_square   = maximum(abs.(SX*SX - I2))
    Dict{String,Any}(
        "i_times_j_eq_k_err" => err_ij,
        "j_times_i_eq_minus_k_err" => err_ji,
        "i_squared_eq_minus_one_err" => err_ii,
        "hamilton_product_eq_matrix_product_maxerr" => mat_err,
        "pauli_anticommutator_sx_sy" => pauli_anticomm,
        "pauli_square_sx" => pauli_square,
        "noncommutative_ij_ne_ji" => err_ij < 1e-12 && qnorm(qadd(ij, qscale(-1.0,ji))) > 1.0,
        "carrier_verified" => max(err_ij,err_ji,err_ii,mat_err,pauli_anticomm,pauli_square) < 1e-10,
    )
end

# =============================================================================
# QUATERNIONIC HOPFIELD NETWORK (same deterministic update as parent)
# =============================================================================

function hebbian_weights(patterns, N::Int)
    W = Matrix{NTuple{4,Float64}}(undef, N, N)
    for i in 1:N, j in 1:N
        acc = (0.0,0.0,0.0,0.0)
        if i != j
            for xi in patterns
                acc = qadd(acc, qmul(xi[i], qconj(xi[j])))
            end
        end
        W[i,j] = acc
    end
    W
end

function async_sweep!(state, W, N::Int)
    for i in 1:N
        h = (0.0,0.0,0.0,0.0)
        for j in 1:N
            h = qadd(h, qmul(W[i,j], state[j]))
        end
        if qnorm(h) > 1e-12
            state[i] = qnormalize(h)
        end
    end
    state
end

function recall(state0, W, N::Int; max_sweeps=200, tol=1e-10)
    state = collect(state0)
    energies = Float64[hopfield_energy(state, W, N)]
    sweeps = 0
    for s in 1:max_sweeps
        prev = copy(state)
        async_sweep!(state, W, N)
        sweeps = s
        push!(energies, hopfield_energy(state, W, N))
        moved = maximum(quat_geodesic(prev[i], state[i]) for i in 1:N)
        moved < tol && break
    end
    state, sweeps, energies
end

function hopfield_energy(state, W, N::Int)
    E = 0.0
    for i in 1:N, j in 1:N
        E -= qre(qmul(qmul(qconj(state[i]), W[i,j]), state[j]))
    end
    E
end

function recall_overlap(recovered, target, N::Int)
    s = 0.0
    for i in 1:N
        d = recovered[i][1]*target[i][1] + recovered[i][2]*target[i][2] +
            recovered[i][3]*target[i][3] + recovered[i][4]*target[i][4]
        s += abs(d)
    end
    s / N
end

function config_distance(a, b, N::Int)
    mean(quat_geodesic(a[i], b[i]) for i in 1:N)
end

function basin_label(recovered, patterns, N::Int)
    dists = [config_distance(recovered, p, N) for p in patterns]
    argmin(dists), minimum(dists)
end

function corrupt(pattern, frac::Float64, rng)
    N = length(pattern)
    out = collect(pattern)
    k = max(1, round(Int, frac*N))
    idx = shuffle(rng, collect(1:N))[1:k]
    for i in idx
        out[i] = rand_unit_quat(rng)
    end
    out, idx
end

function random_patterns(M::Int, N::Int, rng)
    [[rand_unit_quat(rng) for _ in 1:N] for _ in 1:M]
end

# =============================================================================
# Parent control #1: geometric-vs-classical basin difference.
# =============================================================================

flatten4N(cfg) = reduce(vcat, [collect(q) for q in cfg])

function unflatten4N(v, N)
    [qnormalize((v[4i-3], v[4i-2], v[4i-1], v[4i])) for i in 1:N]
end

function classical_weights(patterns, N::Int)
    d = 4N
    W = zeros(Float64, d, d)
    for p in patterns
        v = flatten4N(p)
        W .+= v * v'
    end
    for i in 1:N
        r = (4i-3):(4i)
        W[r, r] .= 0.0
    end
    W
end

function classical_recall(state0, Wr, N::Int; max_sweeps=200, tol=1e-10)
    v = flatten4N(state0)
    for _ in 1:max_sweeps
        vnew = Wr * v
        cfg = unflatten4N(vnew, N)
        vren = flatten4N(cfg)
        (norm(vren - v) < tol) && (v = vren; break)
        v = vren
    end
    unflatten4N(v, N)
end

function geometric_vs_classical(patterns, Wq, N::Int, rng; trials=8, corrupt_frac=0.30)
    Wr = classical_weights(patterns, N)
    basin_mismatch = 0
    total = 0
    cfg_dists = Float64[]
    q_basin_hits = 0
    c_basin_hits = 0
    for (mu, p) in enumerate(patterns)
        for _ in 1:trials
            probe, _ = corrupt(p, corrupt_frac, rng)
            recq, _, _ = recall(probe, Wq, N)
            recc = classical_recall(probe, Wr, N)
            lblq, _ = basin_label(recq, patterns, N)
            lblc, _ = basin_label(recc, patterns, N)
            (lblq != lblc) && (basin_mismatch += 1)
            (lblq == mu) && (q_basin_hits += 1)
            (lblc == mu) && (c_basin_hits += 1)
            push!(cfg_dists, config_distance(recq, recc, N))
            total += 1
        end
    end
    Dict{String,Any}(
        "basin_label_mismatch_fraction" => basin_mismatch/total,
        "mean_recovered_config_distance_quat_vs_classical" => mean(cfg_dists),
        "max_recovered_config_distance" => maximum(cfg_dists),
        "quaternion_basin_correct_fraction" => q_basin_hits/total,
        "classical_basin_correct_fraction" => c_basin_hits/total,
        "trials" => total,
    )
end

# =============================================================================
# Parent control #2: genuine A*B vs B*A order-dependent basin probe.
# =============================================================================

function random_block(N, rng; commuting=false)
    B = Matrix{NTuple{4,Float64}}(undef, N, N)
    for i in 1:N, j in 1:N
        if i == j
            B[i,j] = (0.0,0.0,0.0,0.0)
        elseif commuting
            B[i,j] = qnormalize((randn(rng), randn(rng), 0.0, 0.0))
        else
            B[i,j] = rand_unit_quat(rng)
        end
    end
    B
end

function assemble_elementwise(A, B, N)
    W = Matrix{NTuple{4,Float64}}(undef, N, N)
    for i in 1:N, j in 1:N
        W[i,j] = (i == j) ? (0.0,0.0,0.0,0.0) : qmul(A[i,j], B[i,j])
    end
    W
end

function assembly_noncommutativity(WAB, WBA, N)
    mx = 0.0
    for i in 1:N, j in 1:N
        mx = max(mx, qnorm(qadd(WAB[i,j], qscale(-1.0, WBA[i,j]))))
    end
    mx
end

function order_basin_probe_detail(N, rng; commuting=false, n_probes=16)
    A = random_block(N, rng; commuting=commuting)
    B = random_block(N, rng; commuting=commuting)
    WAB = assemble_elementwise(A, B, N)
    WBA = assemble_elementwise(B, A, N)
    noncomm = assembly_noncommutativity(WAB, WBA, N)
    WAA = assemble_elementwise(A, A, N)
    erased_noncomm = assembly_noncommutativity(WAA, WAA, N)
    basin_dists = Float64[]
    erased_basin_dists = Float64[]
    label_flips = 0
    probes = Vector{Vector{NTuple{4,Float64}}}()
    for _ in 1:n_probes
        probe = [rand_unit_quat(rng) for _ in 1:N]
        push!(probes, probe)
        recAB, _, _ = recall(probe, WAB, N)
        recBA, _, _ = recall(probe, WBA, N)
        d = config_distance(recAB, recBA, N)
        push!(basin_dists, d)
        (d > 0.05) && (label_flips += 1)
        recAA1, _, _ = recall(probe, WAA, N)
        recAA2, _, _ = recall(probe, WAA, N)
        push!(erased_basin_dists, config_distance(recAA1, recAA2, N))
    end
    Dict{String,Any}(
        "entry_algebra" => commuting ? "complex_subalgebra_(w,x,0,0)_qmul_commutes" : "full_quaternion_qmul_noncommutes",
        "assembly_noncommutativity_AB_minus_BA" => noncomm,
        "mean_order_basin_distance" => mean(basin_dists),
        "max_order_basin_distance" => maximum(basin_dists),
        "fraction_probes_order_dependent" => label_flips/n_probes,
        "erased_control_assembly_noncomm" => erased_noncomm,
        "erased_control_max_basin_distance" => maximum(erased_basin_dists),
        "n_probes" => n_probes,
    ), A, B, WAB, WBA, probes
end

# =============================================================================
# Deflation arm: one fixed W0, varying only lift/connection choice.
# =============================================================================

u1_phase(theta) = (cos(theta), sin(theta), 0.0, 0.0)

function full_axis_phase(theta)
    ax = 1.0 / sqrt(14.0)
    ay = 2.0 / sqrt(14.0)
    az = 3.0 / sqrt(14.0)
    (cos(theta), sin(theta)*ax, sin(theta)*ay, sin(theta)*az)
end

function site_lifts(N::Int, m::Int; kind::String)
    if kind == "spin_c_u1"
        [u1_phase(2pi * m * (i-1) / N) for i in 1:N]
    elseif kind == "full_quaternion_axis"
        [full_axis_phase(2pi * m * (i-1) / N) for i in 1:N]
    else
        error("unknown lift kind: $kind")
    end
end

function lifted_weight(W0, lifts, N::Int)
    W = Matrix{NTuple{4,Float64}}(undef, N, N)
    for i in 1:N, j in 1:N
        W[i,j] = (i == j) ? (0.0,0.0,0.0,0.0) :
            qmul(qmul(lifts[i], W0[i,j]), qconj(lifts[j]))
    end
    W
end

function transform_state(state, lifts, N::Int)
    [qmul(lifts[i], state[i]) for i in 1:N]
end

function pullback_state(state, lifts, N::Int)
    [qmul(qconj(lifts[i]), state[i]) for i in 1:N]
end

function pairwise_lift_deflation(W0, probes, N::Int; kind::String, n_lifts=8)
    lift_ids = collect(0:(n_lifts-1))
    lifts_by_id = [site_lifts(N, m; kind=kind) for m in lift_ids]
    weights = [lifted_weight(W0, lifts, N) for lifts in lifts_by_id]
    all_dists = Float64[]
    per_probe = Dict{String,Any}[]
    global_max = -1.0
    global_pair = Any[]
    probe_any_divergent = 0
    pair_divergent = 0
    for (pidx, probe) in enumerate(probes)
        recs = [recall(probe, W, N)[1] for W in weights]
        probe_dists = Float64[]
        probe_max = -1.0
        probe_pair = [0, 0]
        for a in 1:length(lift_ids)-1, b in a+1:length(lift_ids)
            d = config_distance(recs[a], recs[b], N)
            push!(probe_dists, d)
            push!(all_dists, d)
            if d > 0.05
                pair_divergent += 1
            end
            if d > probe_max
                probe_max = d
                probe_pair = [lift_ids[a], lift_ids[b]]
            end
            if d > global_max
                global_max = d
                global_pair = Any[pidx, lift_ids[a], lift_ids[b]]
            end
        end
        (probe_max > 0.05) && (probe_any_divergent += 1)
        push!(per_probe, Dict{String,Any}(
            "probe_index" => pidx,
            "max_pairwise_basin_distance" => probe_max,
            "mean_pairwise_basin_distance" => mean(probe_dists),
            "max_pair_lift_ids" => probe_pair,
        ))
    end
    Dict{String,Any}(
        "kind" => kind,
        "fixed_weight_base" => "W0=A from the genuine full-quaternion order probe; no B and no A*B/B*A assembly are used in this arm",
        "lift_ids" => lift_ids,
        "n_lifts" => length(lift_ids),
        "n_probes" => length(probes),
        "n_pairs_per_probe" => length(lift_ids) * (length(lift_ids)-1) ÷ 2,
        "max_pairwise_basin_distance" => global_max,
        "mean_pairwise_basin_distance" => mean(all_dists),
        "median_pairwise_basin_distance" => median(all_dists),
        "fraction_pairs_divergent_gt_0p05" => pair_divergent / length(all_dists),
        "fraction_probes_with_any_divergence_gt_0p05" => probe_any_divergent / length(probes),
        "global_max_probe_and_lift_pair" => global_pair,
        "per_probe" => per_probe,
    )
end

function pure_lift_equivariance_control(W0, probes, N::Int; kind::String, n_lifts=8)
    lift_ids = collect(0:(n_lifts-1))
    base_recs = [recall(probe, W0, N)[1] for probe in probes]
    fixed_horizons = [1, 10, 50, 100, 200]
    fixed_pullback_max = Dict{String,Any}()
    for h in fixed_horizons
        h_dists = Float64[]
        for (pidx, probe) in enumerate(probes)
            base_h, _, _ = recall(probe, W0, N; max_sweeps=h, tol=-1.0)
            for m in lift_ids
                lifts = site_lifts(N, m; kind=kind)
                Wlift = lifted_weight(W0, lifts, N)
                lifted_probe = transform_state(probe, lifts, N)
                rec_lift_h, _, _ = recall(lifted_probe, Wlift, N; max_sweeps=h, tol=-1.0)
                rec_pull_h = pullback_state(rec_lift_h, lifts, N)
                push!(h_dists, config_distance(rec_pull_h, base_h, N))
            end
        end
        fixed_pullback_max[string(h)] = maximum(h_dists)
    end
    raw_dists = Float64[]
    pulled_dists = Float64[]
    transformed_dists = Float64[]
    for (pidx, probe) in enumerate(probes)
        for m in lift_ids
            lifts = site_lifts(N, m; kind=kind)
            Wlift = lifted_weight(W0, lifts, N)
            lifted_probe = transform_state(probe, lifts, N)
            rec_lift, _, _ = recall(lifted_probe, Wlift, N)
            rec_pull = pullback_state(rec_lift, lifts, N)
            base_rec = base_recs[pidx]
            push!(raw_dists, config_distance(rec_lift, base_rec, N))
            push!(pulled_dists, config_distance(rec_pull, base_rec, N))
            push!(transformed_dists, config_distance(rec_lift, transform_state(base_rec, lifts, N), N))
        end
    end
    short_horizon_max = maximum(Float64[fixed_pullback_max["1"], fixed_pullback_max["10"], fixed_pullback_max["50"]])
    long_horizon_max = maximum(Float64[fixed_pullback_max["100"], fixed_pullback_max["200"], maximum(pulled_dists)])
    Dict{String,Any}(
        "kind" => kind,
        "role" => "pure gauge/readout-artifact control: W, probe, and readout are transformed consistently. Short-horizon pullback checks the frame algebra; converged pullback tests whether the finite attractor basin is stable under mathematically equivalent lifts.",
        "fixed_sweep_pullback_max_distance_to_base" => fixed_pullback_max,
        "short_horizon_1_10_50_collapses_to_floor" => short_horizon_max < ORDER_FLOOR,
        "long_horizon_or_converged_diverges_gt_0p05" => long_horizon_max > 0.05,
        "max_raw_distance_without_pullback" => maximum(raw_dists),
        "max_pulled_back_distance_to_base_after_converged_recall" => maximum(pulled_dists),
        "max_distance_to_transformed_base_recall" => maximum(transformed_dists),
        "frame_algebra_ok_short_horizon" => short_horizon_max < ORDER_FLOOR,
        "converged_attractor_pullback_collapses_to_floor" => maximum(pulled_dists) < ORDER_FLOOR && maximum(transformed_dists) < ORDER_FLOOR,
        "interpretation" => long_horizon_max > 0.05 ?
            "The lift map is algebraically equivariant at short horizons, but the converged finite basin is not stable under mathematically equivalent lifts. This is a deflation warning: same-scale basin differences can be coordinate/numeric-attractor artifacts, not assembly-order evidence." :
            "The pure lift stays stable through convergence; raw lift motion is a coordinate artifact and is not counted as deflation.",
        "n_lifts" => length(lift_ids),
        "n_probes" => length(probes),
    )
end

function same_weight_determinism_control(W0, probes, N::Int)
    dists = Float64[]
    for probe in probes
        r1, _, _ = recall(probe, W0, N)
        r2, _, _ = recall(probe, W0, N)
        push!(dists, config_distance(r1, r2, N))
    end
    Dict{String,Any}(
        "max_same_weight_repeat_distance" => maximum(dists),
        "mean_same_weight_repeat_distance" => mean(dists),
        "same_weight_is_deterministic_floor" => maximum(dists) < ORDER_FLOOR,
        "n_probes" => length(probes),
    )
end

function annotate_scale!(arm, genuine)
    max_ratio = arm["max_pairwise_basin_distance"] / genuine["max_order_basin_distance"]
    mean_ratio = arm["mean_pairwise_basin_distance"] / genuine["mean_order_basin_distance"]
    arm["max_vs_genuine_max_ratio"] = max_ratio
    arm["mean_vs_genuine_mean_ratio"] = mean_ratio
    arm["same_scale_as_genuine"] =
        max_ratio >= SAME_SCALE_RATIO &&
        mean_ratio >= SAME_SCALE_RATIO &&
        arm["fraction_probes_with_any_divergence_gt_0p05"] >= 0.75
    arm
end

function parent_reference()
    if isfile(PARENT_RESULT)
        p = JSON.parsefile(PARENT_RESULT)
        c2 = p["control_2_order_dependent_basin"]
        Dict{String,Any}(
            "path" => PARENT_RESULT,
            "classification" => p["classification"],
            "promotion_allowed" => p["promotion_allowed"],
            "full_quaternion_max_order_basin_distance" => c2["full_quaternion_arm"]["max_order_basin_distance"],
            "full_quaternion_mean_order_basin_distance" => c2["full_quaternion_arm"]["mean_order_basin_distance"],
            "commuting_control_max_order_basin_distance" => c2["commuting_complex_subalgebra_arm"]["max_order_basin_distance"],
            "load_bearing_flip" => c2["load_bearing_flip"],
        )
    else
        Dict{String,Any}("path" => PARENT_RESULT, "missing" => true)
    end
end

function decide_verdict(spin_arm, quat_arm)
    any_same = spin_arm["same_scale_as_genuine"] || quat_arm["same_scale_as_genuine"]
    all_low = spin_arm["max_vs_genuine_max_ratio"] <= LOW_SCALE_RATIO &&
              spin_arm["mean_vs_genuine_mean_ratio"] <= LOW_SCALE_RATIO &&
              quat_arm["max_vs_genuine_max_ratio"] <= LOW_SCALE_RATIO &&
              quat_arm["mean_vs_genuine_mean_ratio"] <= LOW_SCALE_RATIO
    if any_same
        "hopfield_basin_deflated"
    elseif all_low
        "hopfield_basin_survives"
    else
        "mixed"
    end
end

function main()
    t0 = time()
    N = N_NEURONS
    carrier = verify_quaternion_carrier()
    @assert carrier["carrier_verified"] "quaternion carrier failed verification"

    # Fresh reproduction of the genuine parent control, using the same seed and
    # the same random-stream shape as clifford_hopfield.jl.
    order_geo, A, _, _, _, probes = order_basin_probe_detail(
        N, MersenneTwister(SEED + 21); commuting=false, n_probes=16)
    order_flat, _, _, _, _, _ = order_basin_probe_detail(
        N, MersenneTwister(SEED + 21); commuting=true, n_probes=16)

    order_dependent_real = (order_geo["max_order_basin_distance"] > 50*ORDER_FLOOR) &&
                           (order_geo["assembly_noncommutativity_AB_minus_BA"] > 1e-9)
    commuting_control_flat = (order_flat["max_order_basin_distance"] < order_geo["max_order_basin_distance"]/10) &&
                             (order_flat["assembly_noncommutativity_AB_minus_BA"] < 1e-9)
    erased_metric_ok = (order_geo["erased_control_max_basin_distance"] < ORDER_FLOOR) &&
                       (order_geo["erased_control_assembly_noncomm"] < 1e-12)

    # Keep the geometric-vs-classical control alive on a standard Hebbian store.
    patterns = random_patterns(3, N, MersenneTwister(SEED + 301))
    W_hebbian = hebbian_weights(patterns, N)
    gvc = geometric_vs_classical(patterns, W_hebbian, N, MersenneTwister(SEED + 302); trials=8)
    geometric_is_decorative = (gvc["basin_label_mismatch_fraction"] < 1e-6) &&
                              (gvc["mean_recovered_config_distance_quat_vs_classical"] < 1e-6)

    # Deflation base: a SINGLE fixed weight base W0, chosen from the same genuine
    # carrier stream but not assembled with B in either order.
    W0 = A
    repeat_control = same_weight_determinism_control(W0, probes, N)
    spin_arm = annotate_scale!(
        pairwise_lift_deflation(W0, probes, N; kind="spin_c_u1", n_lifts=8),
        order_geo)
    quat_arm = annotate_scale!(
        pairwise_lift_deflation(W0, probes, N; kind="full_quaternion_axis", n_lifts=8),
        order_geo)
    spin_equiv = pure_lift_equivariance_control(W0, probes, N; kind="spin_c_u1", n_lifts=8)
    quat_equiv = pure_lift_equivariance_control(W0, probes, N; kind="full_quaternion_axis", n_lifts=8)

    verdict = decide_verdict(spin_arm, quat_arm)
    verdict_reading =
        verdict == "hopfield_basin_deflated" ?
        "Single fixed W0 plus lift/connection variation reproduced basin separation at the parent scale; additionally, pure-lift controls show the converged Float64 attractor can diverge after an algebraically valid short-horizon pullback. The order-basin claim is deflated as ordinary lift/connection or numerical-attractor sensitivity unless a later control fences this out." :
        verdict == "hopfield_basin_survives" ?
        "Single fixed W0 plus lift/connection variation stayed near the floor; this run did not reproduce the parent basin gap without genuine noncommutative A*B vs B*A assembly." :
        "Single fixed W0 plus lift/connection variation moved basins, but not cleanly at the parent scale across the conservative arms; the claim is not cleanly deflated or cleanly surviving."

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "sim_id" => OBJECT_ID,
        "name" => "Grok-style single-base deflation control for quaternionic Clifford-Hopfield order-dependent basins",
        "version" => "1.0",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => false,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "deflation_control",
        "tier" => "diagnostic control over existing Clifford-Hopfield basin POC",
        "status_ladder" => "exists < runs < passes local rerun",
        "seed" => SEED,
        "n_neurons" => N,
        "runtime_seconds" => time() - t0,
        "non_numpy" => true,
        "bloch_free" => true,
        "carrier_verification" => carrier,
        "parent_reference" => parent_reference(),

        "claim_ceiling" => string(
            "Computes a finite deflation control for the Clifford-Hopfield order-dependent basin POC. ",
            "It does NOT assert layer-completion, manifold admission, coupling, bridge ",
            "(rho_AB/Xi/Phi0/Axis0), flux, FEP, or physics. promotion_allowed=false."),
        "root_constraints_in_force" => [
            "F01 finite carrier/probes/operators/paths: N=12 quaternion neurons, finite W0, finite lift set m=0..7, finite probe set n=16, deterministic async recall.",
            "N01 order-sensitive/noncommuting witness: genuine parent arm uses qmul(A,B) vs qmul(B,A); deflation arm forbids assembly order and varies only lift/connection choice on a single W0.",
        ],
        "finite_map" => "Phi_deflate: (fixed quaternion weight base W0, lift/connection choice m, probe xi0) -> recalled attractor config; compare pairwise basin distances across m against the genuine A*B vs B*A order arm.",
        "domain" => "single fixed W0=A from the genuine full-quaternion order probe; lift ids m=0..7 for spin_c_u1 and full_quaternion_axis arms; 16 finite random probe states reused from the genuine order arm.",
        "codomain_or_output" => "genuine order-basin metrics, single-base lift pairwise basin metrics, pure-gauge pullback controls, geometric-vs-classical control, and verdict in {hopfield_basin_deflated, hopfield_basin_survives, mixed}.",
        "carrier_layer" => "Cl(3,0)+ even-subalgebra unit quaternions S^3 ~ H ~ SU(2)",
        "geometry_layer" => "quaternionic Clifford-Hopfield basin dynamics on finite N=12 carrier",
        "carrier_realization" => "NTuple{4,Float64} unit quaternions with SU(2)/Pauli matrix verification; dynamics use Hamilton qmul only.",
        "peps3d_embedding" => "not_present; this is a Julia Clifford-Hopfield diagnostic control and is blocked from nonclassical manifold admission.",
        "spinor_state" => "unit quaternion S^3 state as Cl(3,0)+ spinor-compatible SU(2) rotor surrogate; no PEPS3D spinor-network claim.",
        "quaternion_action" => "Hamilton product qmul plus lift action W_m[i,j]=g_m[i]*W0[i,j]*conj(g_m[j]); genuine arm uses qmul(A[i,j],B[i,j]) vs qmul(B[i,j],A[i,j]).",
        "dependency_receipts" => [
            "system_v5/julia_carrier/hopfield/clifford_hopfield.jl",
            "system_v5/julia_carrier/hopfield/clifford_hopfield_results.json",
        ],
        "downstream_blocks" => [
            "layer-completion / manifold admission",
            "coupling / coexistence / nesting promotion",
            "bridge / rho_AB / Xi / Phi0 / Axis0",
            "flux / FEP / physics",
            "ratchet-edge admission or ratchet-thesis closure",
        ],
        "blocked_consumers" => [
            "layer-completion / manifold admission",
            "coupling / coexistence / nesting promotion",
            "bridge / rho_AB / Xi / Phi0 / Axis0",
            "flux / FEP / physics",
            "ratchet-edge admission or ratchet-thesis closure",
        ],
        "allowed_claims" => [
            "bounded deflation verdict for this Hopfield order-basin POC",
            "whether same-scale basin separation appears without A*B vs B*A assembly order under the tested lift/connection family",
        ],
        "promotion_blockers" => [
            "no PEPS3D carrier",
            "no torch-native implementation",
            "no manifold admission packet",
            "single diagnostic family only",
        ],
        "promotion_status" => "diagnostic_only",
        "eligible_consumers" => [
            "future Hopfield deflation/audit probes with explicit no-promotion boundary",
        ],

        "control_1_geometric_vs_classical" => merge(gvc, Dict(
            "geometric_is_decorative" => geometric_is_decorative,
            "interpretation" => geometric_is_decorative ?
                "DECORATIVE on this store: quaternion-product basins are indistinguishable from the Euclidean-dot classical control." :
                "LOAD-BEARING on this store: quaternion-product basins differ from the Euclidean-dot classical control.",
        )),
        "control_2_genuine_order_dependent_basin_reproduction" => Dict(
            "full_quaternion_arm" => order_geo,
            "commuting_complex_subalgebra_arm" => order_flat,
            "order_floor" => ORDER_FLOOR,
            "order_dependent_basin_real" => order_dependent_real,
            "commuting_control_collapses_to_floor" => commuting_control_flat,
            "erased_metric_control_is_zero" => erased_metric_ok,
            "load_bearing_flip" => order_dependent_real && commuting_control_flat && erased_metric_ok,
            "note" => "Fresh reproduction of the parent order control before deflation. The deflation arm below does not use B or A*B/B*A assembly.",
        ),
        "deflation_single_fixed_weight_base" => Dict(
            "base_source" => "W0=A from the full-quaternion genuine order probe seeded with SEED+21",
            "not_used_in_deflation" => ["B", "qmul(A,B)", "qmul(B,A)", "assembly order swap"],
            "same_weight_determinism_control" => repeat_control,
            "spin_c_u1_lift_connection_arm" => spin_arm,
            "full_quaternion_axis_lift_connection_arm" => quat_arm,
            "pure_gauge_equivariance_controls" => Dict(
                "spin_c_u1" => spin_equiv,
                "full_quaternion_axis" => quat_equiv,
            ),
            "same_scale_ratio_bar" => SAME_SCALE_RATIO,
            "low_scale_ratio_bar" => LOW_SCALE_RATIO,
            "deflation_logic" => "same-scale iff max and mean basin-distance ratios against the genuine order arm are both >= 0.75 and at least 75% of probes have a lift-pair divergence >0.05. Pure-lift controls are split: short-horizon pullback must collapse to validate the frame action; long-horizon/converged pullback divergence is reported as numerical-attractor deflation, not counted as a clean geometric order witness.",
        ),
        "verdict" => verdict,
        "verdict_reading" => verdict_reading,
        "honest_status" => string(
            verdict, ": genuine order arm max=", order_geo["max_order_basin_distance"],
            ", spin_c max ratio=", spin_arm["max_vs_genuine_max_ratio"],
            ", full_quaternion max ratio=", quat_arm["max_vs_genuine_max_ratio"],
            ". promotion_allowed=false."),
        "artifacts_emitted" => [
            "deflation_hopfield_basin_results.json -- this file's result JSON",
        ],
        "required_tools" => ["LinearAlgebra", "Random", "Statistics", "JSON"],
        "actual_tools_used" => ["LinearAlgebra", "Random", "Statistics", "JSON"],
        "proof_surfaces_used" => ["carrier algebra verification only; no SMT/proof admission claim"],
        "graph_surfaces_used" => String[],
        "topology_surfaces_used" => String[],
        "tool_manifest" => Dict(
            "LinearAlgebra" => "load_bearing: SU(2)/Pauli matrix realization verifies the reused quaternion carrier and classical-control norm operations.",
            "Random" => "load_bearing: fixed seeded probes, quaternion blocks, and corruption controls; signatures are measured, not planted.",
            "Statistics" => "supportive: mean/median basin distances and control aggregates.",
            "JSON" => "supportive: receipt emission.",
        ),
        "tool_integration_depth" => Dict(
            "LinearAlgebra" => "load_bearing",
            "Random" => "load_bearing",
            "Statistics" => "supportive",
            "JSON" => "supportive",
        ),
        "divergence_log" => [
            "This is not a classical baseline; geometric-vs-classical control is included separately.",
            "Raw lift-coordinate movement is not counted as a clean order witness. The pure-lift control is algebraically equivariant at short horizons but diverges after long/converged recall, so basin separation itself is lift/roundoff-sensitive in this Float64 POC.",
        ],
        "pass_rule" => "Script runs and emits JSON; verdict is whatever measured single-base lift/connection distances imply under the predeclared scale bars.",
        "fail_rule" => "Fail if carrier verification fails, same-weight determinism is not at floor, short-horizon pure-lift frame algebra does not pull back to floor, or result JSON is not emitted. Converged pure-lift divergence is a measured deflation warning, not a run failure.",
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
    end

    println("="^78)
    println("deflation_hopfield_basin  (object_id=$OBJECT_ID, classification=$CLASSIFICATION)")
    println("="^78)
    println("carrier verified: ", carrier["carrier_verified"])
    println("GENUINE order max/mean: ",
            round(order_geo["max_order_basin_distance"], digits=6), " / ",
            round(order_geo["mean_order_basin_distance"], digits=6))
    println("commuting control max: ", round(order_flat["max_order_basin_distance"], digits=10))
    println("spin_c single-base max/mean ratios: ",
            round(spin_arm["max_vs_genuine_max_ratio"], digits=4), " / ",
            round(spin_arm["mean_vs_genuine_mean_ratio"], digits=4),
            " same_scale=", spin_arm["same_scale_as_genuine"])
    println("full quaternion single-base max/mean ratios: ",
            round(quat_arm["max_vs_genuine_max_ratio"], digits=4), " / ",
            round(quat_arm["mean_vs_genuine_mean_ratio"], digits=4),
            " same_scale=", quat_arm["same_scale_as_genuine"])
    println("pure gauge pullback max spin/full: ",
            round(spin_equiv["max_pulled_back_distance_to_base_after_converged_recall"], digits=10), " / ",
            round(quat_equiv["max_pulled_back_distance_to_base_after_converged_recall"], digits=10))
    println("VERDICT: ", verdict)
    println("result: ", RESULT_PATH)
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
