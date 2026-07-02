#!/usr/bin/env julia
# =============================================================================
# neural_on_manifold.jl -- Hopfield dynamics on flat R^n vs Hopf/Clifford S^3
#
# object_id          = neural_on_manifold
# classification     = neural_on_manifold_poc
# promotion_allowed  = false
# sim_execution_kind = nonclassical_poc
#
# Claim ceiling:
#   Computes a bounded POC contrast between:
#     (a) a flat Euclidean-dot Hopfield control on R^(4N), with an unconstrained
#         continuous update that can expand along eigen-directions; and
#     (b) a non-flat Hopf/Clifford arm with unit-quaternion neurons on S^3,
#         using the Hamilton/geometric product in Cl(3,0)+.
#
#   This is NOT layer completion, manifold admission, bridge, flux, Axis0, FEP,
#   physics, or final proof of the owner's thesis. It is a runnable operational
#   check. promotion_allowed=false.
#
# Run:
#   julia --project="system_v5/julia_carrier" \
#     "system_v5/julia_carrier/hopfield/neural_on_manifold.jl"
# =============================================================================

using Dates
using LinearAlgebra
using Random
using Statistics
import JSON

const OBJECT_ID = "neural_on_manifold"
const CLASSIFICATION = "neural_on_manifold_poc"
const HERE = @__DIR__
const RESULT_PATH = joinpath(HERE, "neural_on_manifold_results.json")
const SEED = 20260603
const N_NEURONS = 12
const M_HEADLINE = 3

# Pauli/SU(2) realization of Cl(3,0)+ ~= H ~= S^3.
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const I2 = ComplexF64[1 0; 0 1]

qmat(q) = q[1]*I2 - im*(q[2]*SX + q[3]*SY + q[4]*SZ)

function qmul(q, p)
    w1,x1,y1,z1 = q
    w2,x2,y2,z2 = p
    (w1*w2 - x1*x2 - y1*y2 - z1*z2,
     w1*x2 + x1*w2 + y1*z2 - z1*y2,
     w1*y2 - x1*z2 + y1*w2 + z1*x2,
     w1*z2 + x1*y2 - y1*x2 + z1*w2)
end

qconj(q) = (q[1], -q[2], -q[3], -q[4])
qadd(q, p) = (q[1]+p[1], q[2]+p[2], q[3]+p[3], q[4]+p[4])
qscale(a, q) = (a*q[1], a*q[2], a*q[3], a*q[4])
qnorm(q) = sqrt(q[1]^2 + q[2]^2 + q[3]^2 + q[4]^2)
qdot(q, p) = q[1]*p[1] + q[2]*p[2] + q[3]*p[3] + q[4]*p[4]

function qnormalize(q)
    n = qnorm(q)
    n < 1e-300 ? (1.0, 0.0, 0.0, 0.0) : (q[1]/n, q[2]/n, q[3]/n, q[4]/n)
end

function rand_unit_quat(rng)
    qnormalize((randn(rng), randn(rng), randn(rng), randn(rng)))
end

function quat_geodesic(q, p)
    acos(clamp(abs(qdot(q, p)), -1.0, 1.0))
end

function verify_carrier()
    qi = (0.0, 1.0, 0.0, 0.0)
    qj = (0.0, 0.0, 1.0, 0.0)
    qk = (0.0, 0.0, 0.0, 1.0)
    ij = qmul(qi, qj)
    ji = qmul(qj, qi)
    ii = qmul(qi, qi)
    err_ij = qnorm(qadd(ij, qscale(-1.0, qk)))
    err_ji = qnorm(qadd(ji, qk))
    err_ii = qnorm(qadd(ii, (1.0, 0.0, 0.0, 0.0)))
    rng = MersenneTwister(1)
    mat_err = 0.0
    for _ in 1:200
        a = rand_unit_quat(rng)
        b = rand_unit_quat(rng)
        mat_err = max(mat_err, maximum(abs.(qmat(qmul(a, b)) - qmat(a)*qmat(b))))
    end
    pauli_anticomm = maximum(abs.(SX*SY + SY*SX))
    pauli_square = maximum(abs.(SX*SX - I2))
    flat_dot_comm_err = abs(qdot(qi, qj) - qdot(qj, qi))
    Dict{String,Any}(
        "carrier_verified" => maximum([err_ij, err_ji, err_ii, mat_err, pauli_anticomm, pauli_square]) < 1e-10,
        "i_times_j_eq_k_err" => err_ij,
        "j_times_i_eq_minus_k_err" => err_ji,
        "i_squared_eq_minus_one_err" => err_ii,
        "hamilton_product_eq_matrix_product_maxerr" => mat_err,
        "pauli_anticommutator_sx_sy" => pauli_anticomm,
        "pauli_square_sx" => pauli_square,
        "flat_dot_commutation_error_dot_i_j_minus_dot_j_i" => flat_dot_comm_err,
        "noncommutative_ij_ne_ji" => qnorm(qadd(ij, qscale(-1.0, ji))) > 1.0,
    )
end

function peps3d_anchor(N::Int)
    sites = Dict{String,Any}[]
    for idx in 1:N
        x = div(idx - 1, 4) + 1
        y = div(mod(idx - 1, 4), 2) + 1
        z = mod(idx - 1, 2) + 1
        push!(sites, Dict("site" => idx, "coord" => [x, y, z], "local_state" => "unit quaternion on S^3"))
    end
    bonds = Vector{Vector{Int}}()
    for a in sites, b in sites
        ia = a["site"]
        ib = b["site"]
        ia >= ib && continue
        ca = a["coord"]
        cb = b["coord"]
        if sum(abs.(ca .- cb)) == 1
            push!(bonds, [ia, ib])
        end
    end
    Dict{String,Any}(
        "site_lattice" => "3x2x2 finite anchor for N=12 local cells",
        "sites" => sites,
        "nearest_neighbor_bonds" => bonds,
        "admission_boundary" => "finite PEPS3D site/bond anchor only; no PEPS contraction or bond-tensor admission is claimed by this POC",
    )
end

function random_patterns(M::Int, N::Int, rng)
    [[rand_unit_quat(rng) for _ in 1:N] for _ in 1:M]
end

function hebbian_weights_quat(patterns, N::Int)
    W = Matrix{NTuple{4,Float64}}(undef, N, N)
    for i in 1:N, j in 1:N
        acc = (0.0, 0.0, 0.0, 0.0)
        if i != j
            for pat in patterns
                acc = qadd(acc, qmul(pat[i], qconj(pat[j])))
            end
        end
        W[i,j] = acc
    end
    W
end

function hopfield_energy_quat(state, W, N::Int)
    e = 0.0
    for i in 1:N, j in 1:N
        e -= qmul(qmul(qconj(state[i]), W[i,j]), state[j])[1]
    end
    e
end

function async_sweep_quat!(state, W, N::Int)
    for i in 1:N
        h = (0.0, 0.0, 0.0, 0.0)
        for j in 1:N
            h = qadd(h, qmul(W[i,j], state[j]))
        end
        if qnorm(h) > 1e-12
            state[i] = qnormalize(h)
        end
    end
    state
end

function recall_quat(state0, W, N::Int; max_sweeps=120, tol=1e-10, trace=false)
    state = collect(state0)
    energies = Float64[hopfield_energy_quat(state, W, N)]
    max_neuron_norms = Float64[maximum(qnorm(q) for q in state)]
    global_norms = Float64[sqrt(sum(qnorm(q)^2 for q in state))]
    sweeps = 0
    for s in 1:max_sweeps
        prev = copy(state)
        async_sweep_quat!(state, W, N)
        sweeps = s
        push!(energies, hopfield_energy_quat(state, W, N))
        push!(max_neuron_norms, maximum(qnorm(q) for q in state))
        push!(global_norms, sqrt(sum(qnorm(q)^2 for q in state)))
        moved = maximum(quat_geodesic(prev[i], state[i]) for i in 1:N)
        moved < tol && break
    end
    if trace
        return state, sweeps, Dict(
            "energies" => energies,
            "max_neuron_norms" => max_neuron_norms,
            "global_norms" => global_norms,
        )
    end
    state, sweeps
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

function config_distance(a, b, N::Int)
    mean(quat_geodesic(a[i], b[i]) for i in 1:N)
end

function recall_overlap(recovered, target, N::Int)
    mean(abs(qdot(recovered[i], target[i])) for i in 1:N)
end

function basin_label(recovered, patterns, N::Int)
    dists = [config_distance(recovered, pat, N) for pat in patterns]
    argmin(dists), minimum(dists)
end

flatten4N(cfg) = reduce(vcat, [collect(q) for q in cfg])

function unflatten4N(v, N::Int; normalize_blocks=true)
    out = Vector{NTuple{4,Float64}}(undef, N)
    for i in 1:N
        q = (v[4i-3], v[4i-2], v[4i-1], v[4i])
        out[i] = normalize_blocks ? qnormalize(q) : q
    end
    out
end

function block_norms_from_v(v, N::Int)
    [norm(v[(4i-3):(4i)]) for i in 1:N]
end

function euclidean_weights(patterns, N::Int)
    d = 4N
    W = zeros(Float64, d, d)
    for pat in patterns
        v = flatten4N(pat)
        W .+= v * v'
    end
    for i in 1:N
        rows = (4i-3):(4i)
        W[rows, rows] .= 0.0
    end
    W
end

function flat_unconstrained_run(state0, W, N::Int; steps=24)
    v = flatten4N(state0)
    norms = Float64[]
    max_block_norms = Float64[]
    for _ in 0:steps
        push!(norms, norm(v))
        push!(max_block_norms, maximum(block_norms_from_v(v, N)))
        v = W * v
    end
    vals = eigvals(Symmetric(W))
    svals = svdvals(W)
    tol = isempty(svals) ? 0.0 : maximum(svals) * 1e-10
    rank_est = count(>(tol), svals)
    Dict{String,Any}(
        "steps" => steps,
        "initial_global_norm" => norms[1],
        "final_global_norm" => norms[end],
        "norm_growth_ratio" => norms[end] / max(norms[1], 1e-300),
        "max_global_norm" => maximum(norms),
        "initial_max_neuron_block_norm" => max_block_norms[1],
        "final_max_neuron_block_norm" => max_block_norms[end],
        "spectral_radius" => maximum(abs.(vals)),
        "expanding_eigenvalue_count_abs_gt_1" => count(x -> abs(x) > 1.0 + 1e-10, vals),
        "rank_estimate" => rank_est,
        "nullspace_dimension_estimate" => length(svals) - rank_est,
        "unbounded_or_degenerate_direction_detected" => (maximum(abs.(vals)) > 1.0 + 1e-10) && (length(svals) - rank_est > 0),
        "interpretation" => "flat R^(4N) continuous Euclidean-dot update has no compact state constraint; expansion along eigen-directions and null/degenerated directions are measured directly",
    )
end

function flat_projected_recall(state0, W, N::Int; max_sweeps=120, tol=1e-10)
    v = flatten4N(state0)
    for _ in 1:max_sweeps
        prev = v
        raw = W * v
        cfg = unflatten4N(raw, N; normalize_blocks=true)
        v = flatten4N(cfg)
        norm(v - prev) < tol && break
    end
    unflatten4N(v, N; normalize_blocks=true)
end

function geometric_vs_flat_projected(patterns, Wq, Wflat, N::Int, rng; trials=10, corrupt_frac=0.30)
    total = 0
    mismatch = 0
    q_hits = 0
    flat_hits = 0
    cfg_dists = Float64[]
    examples = Dict{String,Any}[]
    for (mu, pat) in enumerate(patterns)
        for trial in 1:trials
            probe, idx = corrupt(pat, corrupt_frac, rng)
            rq, _ = recall_quat(probe, Wq, N)
            rf = flat_projected_recall(probe, Wflat, N)
            lq, dq = basin_label(rq, patterns, N)
            lf, df = basin_label(rf, patterns, N)
            d = config_distance(rq, rf, N)
            push!(cfg_dists, d)
            if lq != lf && length(examples) < 4
                push!(examples, Dict(
                    "target_pattern" => mu,
                    "trial" => trial,
                    "corrupted_indices" => idx,
                    "nonflat_basin_label" => lq,
                    "flat_projected_basin_label" => lf,
                    "nonflat_basin_distance" => dq,
                    "flat_projected_basin_distance" => df,
                    "recovered_config_distance" => d,
                ))
            end
            (lq != lf) && (mismatch += 1)
            (lq == mu) && (q_hits += 1)
            (lf == mu) && (flat_hits += 1)
            total += 1
        end
    end
    Dict{String,Any}(
        "trials" => total,
        "basin_label_mismatch_fraction" => mismatch / total,
        "mean_recovered_config_distance_nonflat_vs_flat_projected" => mean(cfg_dists),
        "max_recovered_config_distance_nonflat_vs_flat_projected" => maximum(cfg_dists),
        "nonflat_basin_correct_fraction" => q_hits / total,
        "flat_projected_basin_correct_fraction" => flat_hits / total,
        "mismatch_examples" => examples,
        "flat_projection_note" => "this control externally projects the flat Euclidean-dot update back to unit blocks; it removes the infinity issue but not the commutative-dot substrate",
    )
end

function capacity_trial(arm::Symbol, M::Int, N::Int, rng; trials=8, corrupt_frac=0.30, ov_thresh=0.90, basin_thresh=0.75)
    patterns = random_patterns(M, N, rng)
    Wq = hebbian_weights_quat(patterns, N)
    Wf = euclidean_weights(patterns, N)
    overlaps = Float64[]
    hits = 0
    total = 0
    for (mu, pat) in enumerate(patterns)
        for _ in 1:trials
            probe, _ = corrupt(pat, corrupt_frac, rng)
            rec = arm === :nonflat ? recall_quat(probe, Wq, N)[1] : flat_projected_recall(probe, Wf, N)
            push!(overlaps, recall_overlap(rec, pat, N))
            lbl, _ = basin_label(rec, patterns, N)
            (lbl == mu) && (hits += 1)
            total += 1
        end
    end
    mean_ov = mean(overlaps)
    basin_frac = hits / total
    Dict{String,Any}(
        "M" => M,
        "mean_recall_overlap" => mean_ov,
        "min_recall_overlap" => minimum(overlaps),
        "basin_correct_fraction" => basin_frac,
        "reliable_under_poc_bar" => (mean_ov >= ov_thresh) && (basin_frac >= basin_thresh),
        "trials_per_pattern" => trials,
        "corrupt_frac" => corrupt_frac,
    )
end

function capacity_ladder(arm::Symbol, N::Int; M_max=6)
    rows = Dict{String,Any}[]
    max_reliable = 0
    for M in 1:M_max
        row = capacity_trial(arm, M, N, MersenneTwister(SEED + (arm === :nonflat ? 3000 : 4000) + 17M))
        push!(rows, row)
        row["reliable_under_poc_bar"] && (max_reliable = M)
    end
    Dict{String,Any}(
        "arm" => String(arm),
        "poc_reliable_bar" => "mean overlap >= 0.90 AND basin-correct fraction >= 0.75",
        "M_max_scanned" => M_max,
        "rows" => rows,
        "max_reliable_M_under_poc_bar" => max_reliable,
        "bounded_capacity_observed_in_scan" => max_reliable < M_max,
    )
end

function random_block(N, rng; commuting=false)
    B = Matrix{NTuple{4,Float64}}(undef, N, N)
    for i in 1:N, j in 1:N
        if i == j
            B[i,j] = (0.0, 0.0, 0.0, 0.0)
        elseif commuting
            B[i,j] = (randn(rng), 0.0, 0.0, 0.0)
        else
            B[i,j] = rand_unit_quat(rng)
        end
    end
    B
end

function assemble_elementwise(A, B, N)
    W = Matrix{NTuple{4,Float64}}(undef, N, N)
    for i in 1:N, j in 1:N
        W[i,j] = i == j ? (0.0, 0.0, 0.0, 0.0) : qmul(A[i,j], B[i,j])
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

function order_basin_probe(N, rng; commuting=false, n_probes=16)
    A = random_block(N, rng; commuting=commuting)
    B = random_block(N, rng; commuting=commuting)
    WAB = assemble_elementwise(A, B, N)
    WBA = assemble_elementwise(B, A, N)
    noncomm = assembly_noncommutativity(WAB, WBA, N)
    WAA = assemble_elementwise(A, A, N)
    basin_dists = Float64[]
    erased_basin_dists = Float64[]
    for _ in 1:n_probes
        probe = [rand_unit_quat(rng) for _ in 1:N]
        recAB, _ = recall_quat(probe, WAB, N)
        recBA, _ = recall_quat(probe, WBA, N)
        push!(basin_dists, config_distance(recAB, recBA, N))
        recAA1, _ = recall_quat(probe, WAA, N)
        recAA2, _ = recall_quat(probe, WAA, N)
        push!(erased_basin_dists, config_distance(recAA1, recAA2, N))
    end
    Dict{String,Any}(
        "entry_algebra" => commuting ? "flat_real_scalar_entries_commuting" : "full_quaternion_entries_noncommuting",
        "assembly_noncommutativity_AB_minus_BA" => noncomm,
        "mean_order_basin_distance" => mean(basin_dists),
        "max_order_basin_distance" => maximum(basin_dists),
        "fraction_probes_order_distance_gt_0p05" => count(>(0.05), basin_dists) / n_probes,
        "erased_control_max_basin_distance" => maximum(erased_basin_dists),
        "n_probes" => n_probes,
    )
end

function flat_scalar_order_control(N, rng; n_probes=16)
    d = 4N
    A = randn(rng, d, d)
    B = randn(rng, d, d)
    WAB = A .* B
    WBA = B .* A
    for i in 1:N
        rows = (4i-3):(4i)
        WAB[rows, rows] .= 0.0
        WBA[rows, rows] .= 0.0
    end
    dists = Float64[]
    for _ in 1:n_probes
        probe = [rand_unit_quat(rng) for _ in 1:N]
        recAB = flat_projected_recall(probe, WAB, N)
        recBA = flat_projected_recall(probe, WBA, N)
        push!(dists, config_distance(recAB, recBA, N))
    end
    Dict{String,Any}(
        "entry_algebra" => "flat_real_scalar_elementwise_multiplication_commutes",
        "assembly_max_abs_AB_minus_BA" => maximum(abs.(WAB - WBA)),
        "mean_order_basin_distance" => mean(dists),
        "max_order_basin_distance" => maximum(dists),
        "n_probes" => n_probes,
    )
end

function main()
    t0 = time()
    rng = MersenneTwister(SEED)
    N = N_NEURONS
    M = M_HEADLINE

    carrier = verify_carrier()
    @assert carrier["carrier_verified"] "Clifford/SU(2) carrier verification failed"

    patterns = random_patterns(M, N, rng)
    Wq = hebbian_weights_quat(patterns, N)
    Wflat = euclidean_weights(patterns, N)

    probe, corrupt_idx = corrupt(patterns[1], 0.30, MersenneTwister(SEED + 7))
    nonflat_rec, nonflat_sweeps, nonflat_trace = recall_quat(probe, Wq, N; trace=true)
    flat_unbounded = flat_unconstrained_run(probe, Wflat, N; steps=24)
    flat_projected_rec = flat_projected_recall(probe, Wflat, N)

    nonflat_norm_deviation = maximum(abs.(nonflat_trace["max_neuron_norms"] .- 1.0))
    finitude = Dict{String,Any}(
        "same_probe_corrupted_indices" => corrupt_idx,
        "flat_unconstrained_R4N" => flat_unbounded,
        "nonflat_s3_clifford" => Dict(
            "sweeps_to_converge" => nonflat_sweeps,
            "initial_global_norm" => nonflat_trace["global_norms"][1],
            "final_global_norm" => nonflat_trace["global_norms"][end],
            "max_global_norm" => maximum(nonflat_trace["global_norms"]),
            "max_neuron_norm_deviation_from_1" => nonflat_norm_deviation,
            "bounded_by_compact_s3_constraint" => nonflat_norm_deviation < 1e-10,
            "energy_first" => nonflat_trace["energies"][1],
            "energy_last" => nonflat_trace["energies"][end],
            "energy_monotone_nonincreasing" => all(diff(nonflat_trace["energies"]) .<= 1e-9),
        ),
        "flat_projected_control" => Dict(
            "note" => "external per-neuron normalization removes the infinity contrast; it is a control, not the flat R^n arm",
            "overlap_to_target" => recall_overlap(flat_projected_rec, patterns[1], N),
            "basin_label" => basin_label(flat_projected_rec, patterns, N)[1],
        ),
    )

    basin_control = geometric_vs_flat_projected(patterns, Wq, Wflat, N, MersenneTwister(SEED + 11); trials=10)
    order_full = order_basin_probe(N, MersenneTwister(SEED + 21); commuting=false, n_probes=16)
    order_commuting = order_basin_probe(N, MersenneTwister(SEED + 21); commuting=true, n_probes=16)
    order_flat_scalar = flat_scalar_order_control(N, MersenneTwister(SEED + 22); n_probes=16)
    order_floor = 1e-6
    order_dep = (order_full["max_order_basin_distance"] > 50order_floor) &&
                (order_full["assembly_noncommutativity_AB_minus_BA"] > 1e-9)
    commuting_flat = (order_commuting["max_order_basin_distance"] < order_full["max_order_basin_distance"]/10) &&
                     (order_commuting["assembly_noncommutativity_AB_minus_BA"] < 1e-9) &&
                     (order_flat_scalar["max_order_basin_distance"] < order_full["max_order_basin_distance"]/10)
    erased_ok = order_full["erased_control_max_basin_distance"] < order_floor

    capacity_nonflat = capacity_ladder(:nonflat, N; M_max=6)
    capacity_flat_projected = capacity_ladder(:flat_projected, N; M_max=6)

    finitude_changed = finitude["flat_unconstrained_R4N"]["unbounded_or_degenerate_direction_detected"] &&
                       finitude["nonflat_s3_clifford"]["bounded_by_compact_s3_constraint"]
    basin_changed = basin_control["basin_label_mismatch_fraction"] > 0.05
    commutation_changed = carrier["noncommutative_ij_ne_ji"] && order_dep && commuting_flat && erased_ok
    capacity_changed = capacity_nonflat["max_reliable_M_under_poc_bar"] != capacity_flat_projected["max_reliable_M_under_poc_bar"]
    attractor_extra = order_dep && commuting_flat

    verdict = if finitude_changed && basin_changed && commutation_changed && attractor_extra
        "nonflat_changes_network"
    elseif !finitude_changed && !basin_changed && !commutation_changed
        "nonflat_cosmetic"
    else
        "mixed"
    end

    runtime = time() - t0
    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => false,
        "sim_execution_kind" => "nonclassical_poc",
        "generated_at" => string(now()),
        "seed" => SEED,
        "runtime_seconds" => runtime,
        "status_ladder" => "exists < runs < passes local rerun",
        "claim_ceiling" => "Operational POC only: compares flat Euclidean-dot Hopfield dynamics to Hopf/Clifford unit-quaternion dynamics. Does not admit manifold/layer/bridge/Axis0/flux/physics claims.",
        "root_constraints_in_force" => [
            "F01 finite carrier/probe/operator/path set",
            "N01 noncommuting or order-sensitive operation/control",
        ],
        "finite_map" => "Given finite stored patterns and finite corrupted/random probes, apply flat Euclidean-dot or Hopf/Clifford Hopfield update maps to fixed points or bounded iteration traces; emit finitude, basin, order, and capacity invariants.",
        "domain" => Dict(
            "nonflat" => "N=12 local cells, each a unit quaternion q in S^3 ~ Cl(3,0)+ ~ SU(2); M=3 headline patterns plus finite corruption/random probes",
            "flat" => "same patterns flattened to R^(4N), Euclidean-dot weight W=sum vv^T with 4x4 self-blocks zeroed",
        ),
        "codomain_or_output" => "result JSON with boundedness norms, basin labels/distances, order-dependence distances, capacity scan, verdict, and blocked consumers",
        "carrier_layer" => "S^3 unit-quaternion local state with flat R^(4N) control",
        "geometry_layer" => "Hopf/Clifford S^3 via Cl(3,0)+ ~= H ~= SU(2); flat Euclidean control uses commuting dot/scalar multiplication",
        "carrier_realization" => "Julia Float64 4-tuples for quaternions; SU(2) Pauli matrices verify the Clifford product; flat control is Float64 R^(4N)",
        "peps3d_embedding" => peps3d_anchor(N),
        "spinor_state" => "q -> Q(q)=w*I - i(x*sx+y*sy+z*sz), a 2x2 SU(2) spinor/rotor realization verified against Hamilton product",
        "quaternion_action" => "Hamilton product qmul is used in nonflat weights and updates; qmul(i,j)=k and qmul(j,i)=-k",
        "dependency_receipts" => [
            "system_v5/julia_carrier/hopfield/clifford_hopfield.jl",
            "system_v5/julia_carrier/hopfield/clifford_hopfield_results.json",
            "system_v5/julia_carrier/hopfield/HOPFIELD_SPEC.md",
        ],
        "allowed_claims" => [
            "POC finitude contrast between unconstrained flat R^(4N) and compact S^3-constrained dynamics",
            "POC basin difference between Euclidean-dot and quaternion-product Hopfield updates",
            "POC order-dependence witness that collapses under commuting controls",
        ],
        "promotion_status" => "diagnostic_only",
        "promotion_blockers" => [
            "not a full PEPS3D tensor-network admission",
            "small seeded POC, not broad statistical study",
            "uses local Julia carrier, not torch-native PEPS3D production path",
            "no bridge, flux, Axis0, FEP, physics, or layer completion evidence",
        ],
        "blocked_consumers" => [
            "layer-completion / manifold admission",
            "coupling / coexistence / nesting promotion",
            "bridge / rho_AB / Xi / Phi0 / Axis0",
            "flux / FEP / physics",
            "owner-thesis closure beyond this operational POC",
        ],
        "carrier_verification" => carrier,
        "finitude_test" => finitude,
        "commutation_and_basin_test" => Dict{String,Any}(
            "geometric_vs_flat_projected_basins" => basin_control,
            "order_dependent_basin_full_quaternion" => order_full,
            "order_dependent_basin_commuting_real_scalar_quaternion_entries" => order_commuting,
            "flat_scalar_order_control" => order_flat_scalar,
            "order_floor" => order_floor,
            "order_dependent_nonflat_real" => order_dep,
            "commuting_controls_collapse" => commuting_flat,
            "erased_metric_control_zero" => erased_ok,
            "load_bearing_flip" => commutation_changed,
        ),
        "capacity_scan" => Dict{String,Any}(
            "nonflat_s3_clifford" => capacity_nonflat,
            "flat_projected_external_unit_control" => capacity_flat_projected,
            "capacity_changed_between_nonflat_and_projected_flat_control" => capacity_changed,
            "honest_boundary" => "flat unconstrained R^(4N) is not a bounded attractor memory without an added projection/saturation; projected flat is included only to compare basins after imposing finitude externally",
        ),
        "verdict_components" => Dict(
            "finitude_changed" => finitude_changed,
            "basins_changed" => basin_changed,
            "commutation_changed" => commutation_changed,
            "capacity_scan_changed" => capacity_changed,
            "nonflat_has_order_dependent_attractor_structure_absent_in_commuting_controls" => attractor_extra,
        ),
        "verdict" => verdict,
        "interpretation" => verdict == "nonflat_changes_network" ?
            "The non-flat Hopf/Clifford substrate changes this network operationally: compact S^3 blocks finitude, Hamilton product supplies noncommuting order-dependent basins, and flat commuting controls do not reproduce those order basins." :
            "The POC did not cleanly satisfy every change criterion; inspect verdict_components for the partial failures.",
        "tool_manifest" => Dict(
            "LinearAlgebra" => "load_bearing: Pauli/SU(2) carrier verification, Euclidean spectral/rank finitude test, flat matrix update.",
            "Random" => "load_bearing: seeded finite patterns, corruptions, and random order probes.",
            "Statistics" => "supportive: means over finite probe sets.",
            "JSON" => "supportive: result artifact emission.",
            "Dates" => "supportive: timestamp only.",
            "e3nn" => "not_used: installed in Python preflight but not load-bearing for this direct quaternionic Hopf/Clifford POC.",
            "e3nn_jax" => "not_used: installed in Python preflight but JAX/equivariant tooling would be decorative here.",
            "clifford_python" => "not_used: installed in Python preflight; Julia reused the repo's existing explicit quaternionic Cl(3)+ carrier.",
            "QuantumClifford" => "not_used: Julia package loadable in preflight, but the existing Hopfield lane already verifies the Cl(3)+ even-subalgebra product directly.",
            "Grassmann" => "not_used: Julia package loadable in preflight; not needed for this finite Hopfield contrast.",
            "ITensors" => "not_used: Julia package loadable in preflight; no PEPS contraction is claimed.",
        ),
        "TOOL_MANIFEST" => Dict(
            "LinearAlgebra" => "load_bearing: Pauli/SU(2) carrier verification, Euclidean spectral/rank finitude test, flat matrix update.",
            "Random" => "load_bearing: seeded finite patterns, corruptions, and random order probes.",
            "Statistics" => "supportive: means over finite probe sets.",
            "JSON" => "supportive: result artifact emission.",
            "Dates" => "supportive: timestamp only.",
        ),
        "tool_integration_depth" => Dict(
            "LinearAlgebra" => "load_bearing",
            "Random" => "load_bearing",
            "Statistics" => "supportive",
            "JSON" => "supportive",
            "Dates" => "supportive",
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "LinearAlgebra" => "load_bearing",
            "Random" => "load_bearing",
            "Statistics" => "supportive",
            "JSON" => "supportive",
            "Dates" => "supportive",
        ),
        "negatives_run" => [
            "flat unconstrained Euclidean R^(4N) update",
            "flat externally projected Euclidean-dot control",
            "commuting real-scalar quaternion entry order control",
            "flat scalar elementwise AB=BA order control",
            "erased B:=A metric control",
        ],
        "artifacts_emitted" => [
            RESULT_PATH,
        ],
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
    end

    println("="^78)
    println("neural_on_manifold (classification=$(CLASSIFICATION), promotion_allowed=false)")
    println("="^78)
    println("carrier verified: ", carrier["carrier_verified"])
    println("FINITUDE:")
    println("  flat norm growth ratio: ", round(flat_unbounded["norm_growth_ratio"], sigdigits=5),
            "  spectral_radius=", round(flat_unbounded["spectral_radius"], digits=4),
            "  null_dim=", flat_unbounded["nullspace_dimension_estimate"])
    println("  nonflat max neuron norm deviation from 1: ", round(nonflat_norm_deviation, sigdigits=5))
    println("BASINS:")
    println("  nonflat vs projected-flat mismatch fraction: ",
            round(basin_control["basin_label_mismatch_fraction"], digits=4),
            "  mean config distance=", round(basin_control["mean_recovered_config_distance_nonflat_vs_flat_projected"], digits=4))
    println("ORDER:")
    println("  full quaternion max order basin distance: ",
            round(order_full["max_order_basin_distance"], digits=4),
            "  commuting control max=", round(order_commuting["max_order_basin_distance"], sigdigits=5),
            "  flat scalar max=", round(order_flat_scalar["max_order_basin_distance"], sigdigits=5))
    println("CAPACITY:")
    println("  nonflat max reliable M: ", capacity_nonflat["max_reliable_M_under_poc_bar"],
            "  projected-flat max reliable M: ", capacity_flat_projected["max_reliable_M_under_poc_bar"])
    println("VERDICT: ", verdict)
    println("result -> ", RESULT_PATH)
    result
end

main()
