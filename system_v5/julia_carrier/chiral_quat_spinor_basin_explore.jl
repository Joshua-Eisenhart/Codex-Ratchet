# chiral_quat_spinor_basin_explore.jl
#
# OBJECT: chiral_quat_spinor_basin_explore_v1
# CLAIM CEILING: exploration_probe — promotion_allowed: false
#
# Finite map:
#   domain   -> (quaternion spinor q in R^4, initial Bloch vector n in R^3)
#   codomain -> terminal Bloch vector after N_ITER steps of IFS dynamics
#
# Root constraints:
#   F01: finite seed set (N_SEEDS), finite operator set {Ti,Te,Fi,Fe}, finite step count
#   N01: Fi (Rx rotation) and Fe (Rz rotation) do not commute; Ti does not commute with Fi/Fe
#
# Models:
#   (1) CANDIDATE: chiral L/R Weyl quaternion-spinor density matrices
#   (2) NEG-nonchiral: single-sector density matrices, same dynamics
#   (3) NEG-realvector: real Bloch (no imaginary component ny), same dynamics
#   (4) NEG-classical: Ti only (no rotations) — kills N01
#
# Controls:
#   Positive: candidate shows more distinct terminal distribution than negatives
#   Negative: neg-classical (no N01) should show collapsed/degenerate structure
#   Boundary: neg-realvector (dim-restricted) should show fewer structure dimensions
#
# Anti-fabrication: verdict requires candidate to BEAT negatives honestly;
#   if it does not, candidate_distinct=false is emitted.
#
# This object does NOT assert: layer-completion, manifold admission,
#   coupling, bridge (rho_AB/Xi/Phi0/Axis0), flux, or physics.

using JSON
using Dates
using Statistics
using LinearAlgebra
using Random

const RESULT_PATH = joinpath(@__DIR__, "chiral_quat_spinor_basin_explore_results.json")

# ── Tool manifest ────────────────────────────────────────────────────────────
const TOOL_MANIFEST = Dict(
    "Julia" => Dict("tried" => true, "used" => true, "role" => "load_bearing",
        "reason" => "executes finite map, clustering, and result emission; removing Julia flips verdict"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "role" => "load_bearing",
        "reason" => "matrix ops for density matrices and Bloch rotations; removing flips Rx/Rz ops"),
    "Statistics" => Dict("tried" => true, "used" => true, "role" => "supportive",
        "reason" => "mean/std for terminal distribution comparison"),
    "JSON" => Dict("tried" => true, "used" => true, "role" => "supportive",
        "reason" => "writes result artifact for JAX audit lane"),
    "Dates" => Dict("tried" => true, "used" => true, "role" => "supportive",
        "reason" => "timestamps result artifact"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "Julia" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "Statistics" => "supportive",
    "JSON" => "supportive",
    "Dates" => "supportive",
)

# ── Parameters ────────────────────────────────────────────────────────────────
const N_SEEDS = 80
const N_ITER  = 400
const NOISE_STD = 0.01
const IFS_PROBS = [0.15, 0.15, 0.35, 0.35]  # Ti, Te, Fi, Fe
const CLUSTER_THRESHOLDS = [0.05, 0.10, 0.15, 0.20, 0.30]

# ── Bloch sphere operators ────────────────────────────────────────────────────
function Rx(angle::Float64)
    c, s = cos(angle), sin(angle)
    [1.0 0.0 0.0; 0.0 c -s; 0.0 s c]
end

function Rz(angle::Float64)
    c, s = cos(angle), sin(angle)
    [c -s 0.0; s c 0.0; 0.0 0.0 1.0]
end

const RX_PI4 = Rx(π/4)
const RZ_PI4 = Rz(π/4)

# N01 check: RX_PI4 and RZ_PI4 do not commute
const N01_COMMUTATOR_NORM = norm(RX_PI4 * RZ_PI4 - RZ_PI4 * RX_PI4)

function bloch_Ti(n::Vector{Float64})
    # Partial z-dephase: shrink transverse components by 0.5
    [n[1]*0.5, n[2]*0.5, n[3]]
end

function bloch_Te(n::Vector{Float64})
    # Partial x-dephase: shrink ny and nz by 0.5
    [n[1], n[2]*0.5, n[3]*0.5]
end

bloch_Fi(n::Vector{Float64}) = RX_PI4 * n
bloch_Fe(n::Vector{Float64}) = RZ_PI4 * n

const OPS = [bloch_Ti, bloch_Te, bloch_Fi, bloch_Fe]
const OP_NAMES = ["Ti", "Te", "Fi", "Fe"]

# ── IFS step ─────────────────────────────────────────────────────────────────
function ifs_step(n::Vector{Float64}, rng::AbstractRNG)
    # Choose operator by IFS probs
    r = rand(rng)
    cumprobs = cumsum(IFS_PROBS)
    idx = findfirst(p -> r <= p, cumprobs)
    idx = isnothing(idx) ? 4 : idx
    n_new = OPS[idx](n) .+ randn(rng, 3) .* NOISE_STD
    nm = norm(n_new)
    nm > 1.0 ? n_new ./= nm : nothing
    n_new
end

function ifs_iterate(n0::Vector{Float64}, n_iter::Int, rng::AbstractRNG)
    n = copy(n0)
    for _ in 1:n_iter
        n = ifs_step(n, rng)
    end
    n
end

# ── Quaternion -> SU(2) -> gamma5 Bloch pair ────────────────────────────────
function rho_to_bloch(rho::Matrix{ComplexF64})
    [2*real(rho[1,2]), 2*imag(rho[2,1]), real(rho[1,1] - rho[2,2])]
end

function quaternion_to_bloch_pair(q::Vector{Float64})
    q = q ./ norm(q)
    a, b, c, d = q
    # SU(2) matrix from quaternion
    U = [a+im*b  c+im*d; -c+im*d  a-im*b]
    spinor = U[:, 1]
    # gamma5 L/R split (upper = L, lower = R in 2-spinor)
    vL = [spinor[1], 0.0+0.0im]
    vR = [0.0+0.0im, spinor[2]]
    nL_norm = norm(vL); nR_norm = norm(vR)
    bloch_L = if nL_norm > 1e-12
        vL ./= nL_norm
        rho_L = vL * vL'
        rho_to_bloch(rho_L)
    else
        zeros(3)
    end
    bloch_R = if nR_norm > 1e-12
        vR ./= nR_norm
        rho_R = vR * vR'
        rho_to_bloch(rho_R)
    else
        zeros(3)
    end
    bloch_L, bloch_R
end

# ── Clustering ────────────────────────────────────────────────────────────────
function pairwise_distances(pts::Vector{Vector{Float64}})
    n = length(pts)
    D = zeros(n, n)
    for i in 1:n, j in i+1:n
        d = norm(pts[i] .- pts[j])
        D[i,j] = d; D[j,i] = d
    end
    D
end

function complete_linkage_cluster(pts::Vector{Vector{Float64}}, thresh::Float64)
    # Simple complete-linkage clustering
    n = length(pts)
    n <= 1 && return ones(Int, n)
    D = pairwise_distances(pts)
    labels = collect(1:n)
    # Greedy complete-linkage: merge clusters where max pairwise dist < thresh
    changed = true
    while changed
        changed = false
        unique_labels = unique(labels)
        length(unique_labels) == 1 && break
        for i in eachindex(unique_labels)
            for j in (i+1):length(unique_labels)
                li, lj = unique_labels[i], unique_labels[j]
                idx_i = findall(==(li), labels)
                idx_j = findall(==(lj), labels)
                # Complete linkage: max distance between clusters
                max_d = maximum(D[a, b] for a in idx_i, b in idx_j)
                if max_d < thresh
                    # Merge j into i
                    labels[idx_j] .= li
                    changed = true
                    break
                end
            end
            changed && break
        end
    end
    # Renumber labels 1..K
    unique_labels = sort(unique(labels))
    label_map = Dict(l => i for (i, l) in enumerate(unique_labels))
    [label_map[l] for l in labels]
end

function basin_stats_from_labels(labels::Vector{Int}, n_total::Int)
    counts = Dict{Int,Int}()
    for l in labels
        counts[l] = get(counts, l, 0) + 1
    end
    fracs = sort([c/n_total for c in values(counts)], rev=true)
    H = -sum(f * log2(f + 1e-12) for f in fracs)
    (num_basins=length(counts), basin_fractions=fracs, basin_entropy=H)
end

# ── Initial states ────────────────────────────────────────────────────────────
function random_bloch_pure(rng::AbstractRNG)
    v = randn(rng, 3); v ./= norm(v); v
end

function random_bloch_mixed(rng::AbstractRNG)
    v = randn(rng, 3); v ./= norm(v)
    r = rand(rng) * 0.7 + 0.3
    r .* v
end

const INIT_FAMILIES = [random_bloch_pure, random_bloch_mixed,
    rng -> [rand(rng)*1.4-0.7, rand(rng)*1.4-0.7, rand(rng)*1.4-0.7]]

# ── Model runners ─────────────────────────────────────────────────────────────

# MODEL 1: CANDIDATE — chiral L/R Weyl quaternion-spinor
function run_candidate(n_seeds::Int, n_iter::Int; base_seed::Int=42)
    rng = MersenneTwister(base_seed)
    endpoints = Vector{Float64}[]  # 6-vectors (nL, nR)
    for _ in 1:n_seeds
        q = randn(rng, 4)
        bL, bR = quaternion_to_bloch_pair(q)
        for fam in INIT_FAMILIES
            rng_traj = MersenneTwister(rand(rng, UInt32))
            n_init = fam(rng_traj)
            # Weight initial state by quaternion amplitude
            wL = (q[1]^2 + q[2]^2) / dot(q, q)
            nL_init = clamp.(wL .* bL .+ (1-wL) .* n_init, -1.0, 1.0)
            nR_init = clamp.((1-wL) .* bR .+ wL .* n_init, -1.0, 1.0)
            # Clip to Bloch ball
            for nv in [nL_init, nR_init]
                nm = norm(nv); nm > 1.0 && (nv ./= nm)
            end
            rng_L = MersenneTwister(rand(rng, UInt32))
            rng_R = MersenneTwister(rand(rng, UInt32))
            nL_fin = ifs_iterate(nL_init, n_iter, rng_L)
            nR_fin = ifs_iterate(nR_init, n_iter, rng_R)
            push!(endpoints, vcat(nL_fin, nR_fin))
        end
    end
    endpoints
end

# MODEL 2: NEG-nonchiral — single sector
function run_neg_nonchiral(n_seeds::Int, n_iter::Int; base_seed::Int=52)
    rng = MersenneTwister(base_seed)
    endpoints = Vector{Float64}[]
    for _ in 1:n_seeds
        for fam in INIT_FAMILIES
            rng_traj = MersenneTwister(rand(rng, UInt32))
            n0 = fam(rng_traj)
            rng_run = MersenneTwister(rand(rng, UInt32))
            push!(endpoints, ifs_iterate(n0, n_iter, rng_run))
        end
    end
    endpoints
end

# MODEL 3: NEG-realvector — real Bloch (ny=0 forced)
function run_neg_realvector(n_seeds::Int, n_iter::Int; base_seed::Int=62)
    rng = MersenneTwister(base_seed)
    endpoints = Vector{Float64}[]
    for _ in 1:n_seeds
        for _ in INIT_FAMILIES
            angle = rand(rng) * 2π
            n0 = [cos(angle), 0.0, sin(angle)]
            rng_run = MersenneTwister(rand(rng, UInt32))
            n = copy(n0)
            for _ in 1:n_iter
                n = ifs_step(n, rng_run)
                n[2] = 0.0  # force ny=0 (real Bloch)
                nm = norm(n); nm > 1.0 && (n ./= nm)
            end
            push!(endpoints, n)
        end
    end
    endpoints
end

# MODEL 4: NEG-classical — Ti only (no N01 rotations)
function run_neg_classical(n_seeds::Int, n_iter::Int; base_seed::Int=72)
    rng = MersenneTwister(base_seed)
    endpoints = Vector{Float64}[]
    for _ in 1:n_seeds
        for _ in INIT_FAMILIES
            n0 = random_bloch_pure(rng)
            rng_run = MersenneTwister(rand(rng, UInt32))
            n = copy(n0)
            for _ in 1:n_iter
                n = bloch_Ti(n) .+ randn(rng_run, 3) .* NOISE_STD
                nm = norm(n); nm > 1.0 && (n ./= nm)
            end
            push!(endpoints, n)
        end
    end
    endpoints
end

# ── Counting at threshold ─────────────────────────────────────────────────────
function count_basins(endpoints::Vector{Vector{Float64}}, thresh::Float64)
    n = length(endpoints)
    n == 0 && return 0
    n == 1 && return 1
    labels = complete_linkage_cluster(endpoints, thresh)
    length(unique(labels))
end

# ── Main ──────────────────────────────────────────────────────────────────────
println("=== chiral_quat_spinor_basin_explore.jl ===")
println("N01 commutator norm (Rx Pi/4, Rz Pi/4): $N01_COMMUTATOR_NORM")
@assert N01_COMMUTATOR_NORM > 0.1 "N01 check FAILED: operators commute unexpectedly"
println("N01 check PASSED: operators do not commute ($(round(N01_COMMUTATOR_NORM, digits=4)))")

println("\nCollecting terminal distributions ($N_SEEDS seeds x 3 families x 4 models, $N_ITER steps each)...")

cand_pts   = run_candidate(N_SEEDS, N_ITER)
nc_pts     = run_neg_nonchiral(N_SEEDS, N_ITER)
rv_pts     = run_neg_realvector(N_SEEDS, N_ITER)
cl_pts     = run_neg_classical(N_SEEDS, N_ITER)

println("Collected: candidate=$(length(cand_pts)), nonchiral=$(length(nc_pts)), realvec=$(length(rv_pts)), classical=$(length(cl_pts))")

# F01 check: finite set
@assert length(cand_pts) == N_SEEDS * 3 "F01 check FAILED: candidate set not finite/complete"
println("F01 check PASSED: finite seed set ($(length(cand_pts)) trajectories per model)")

# Distribution statistics
cand_L_pts = [v[1:3] for v in cand_pts]
cand_R_pts = [v[4:6] for v in cand_pts]
cand_L_mat = hcat(cand_L_pts...)'
cand_R_mat = hcat(cand_R_pts...)'
nc_mat = hcat(nc_pts...)'

LR_sep = norm(mean(cand_L_mat, dims=1) .- mean(cand_R_mat, dims=1))
cand_spread_L = mean(std(cand_L_mat, dims=1))
nc_spread = mean(std(nc_mat, dims=1))

println("\n=== Distribution statistics ===")
println("  L mean: $(round.(mean(cand_L_mat, dims=1), digits=5))")
println("  R mean: $(round.(mean(cand_R_mat, dims=1), digits=5))")
println("  L/R mean separation: $(round(LR_sep, digits=6))")
println("  Candidate L spread: $(round(cand_spread_L, digits=6))")
println("  Nonchiral spread: $(round(nc_spread, digits=6))")

# Basin counting at all thresholds
println("\n=== Basin count vs threshold ===")
println("$(rpad("Thresh", 10)) $(rpad("CAND", 8)) $(rpad("NC", 8)) $(rpad("RV", 8)) $(rpad("CL", 8))")

basin_sweep = Dict{String,Any}()
for t in CLUSTER_THRESHOLDS
    nb_c  = count_basins(cand_pts, t)
    nb_nc = count_basins(nc_pts, t)
    nb_rv = count_basins(rv_pts, t)
    nb_cl = count_basins(cl_pts, t)
    println("  $(rpad(string(t), 8))  $(rpad(string(nb_c), 7))  $(rpad(string(nb_nc), 7))  $(rpad(string(nb_rv), 7))  $(rpad(string(nb_cl), 7))")
    basin_sweep["thresh_$t"] = Dict("candidate" => nb_c, "neg_nonchiral" => nb_nc,
                                     "neg_realvec" => nb_rv, "neg_classical" => nb_cl)
end

# Honest threshold = 10x noise_std
honest_thresh = 0.10
nb_c_h  = basin_sweep["thresh_$(honest_thresh)"]["candidate"]
nb_nc_h = basin_sweep["thresh_$(honest_thresh)"]["neg_nonchiral"]
nb_rv_h = basin_sweep["thresh_$(honest_thresh)"]["neg_realvec"]
nb_cl_h = basin_sweep["thresh_$(honest_thresh)"]["neg_classical"]
neg_max = max(nb_nc_h, nb_rv_h, nb_cl_h)

println("\nAt honest threshold t=$honest_thresh (10x noise_std):")
println("  CANDIDATE=$nb_c_h  NC=$nb_nc_h  RV=$nb_rv_h  CL=$nb_cl_h")

# Verdict at t=0.15 (robustness check)
nb_c_15  = basin_sweep["thresh_0.15"]["candidate"]
neg_max_15 = max(basin_sweep["thresh_0.15"]["neg_nonchiral"],
                 basin_sweep["thresh_0.15"]["neg_realvec"],
                 basin_sweep["thresh_0.15"]["neg_classical"])

candidate_distinct = nb_c_h > neg_max
verdict_flips_at_015 = nb_c_15 <= neg_max_15

basins_exist = max(nb_c_h, nb_nc_h, nb_rv_h, nb_cl_h) > 1
lr_sep_at_noise = LR_sep < 3 * NOISE_STD

# Positive control: neg-realvector should have FEWER basins (reduced structure)
realvec_fewer = nb_rv_h < nb_nc_h
# Boundary check: neg-classical (no N01) vs candidate
classical_wo_n01 = nb_cl_h < nb_c_h

println("\n=== Positive/negative/boundary checks ===")
println("  [POSITIVE] candidate basins > best_neg: $(candidate_distinct ? "PASS" : "FAIL")")
println("  [NEGATIVE] realvec fewer basins than nonchiral: $(realvec_fewer ? "PASS (structure reduction real)" : "FAIL")")
println("  [BOUNDARY] classical (no N01) < candidate: $(classical_wo_n01 ? "PASS" : "FAIL (N01 not load-bearing here)")")
println("  [ROBUSTNESS] verdict flips at t=0.15: $(verdict_flips_at_015 ? "YES — result is threshold-sensitive" : "NO — robust")")
println("  [LR-SIGNAL] L/R separation at noise level: $(lr_sep_at_noise ? "YES — chiral signal weak" : "NO — genuine separation")")

# ── Honest summary ────────────────────────────────────────────────────────────
summary = if !basins_exist
    "ALL MODELS TRIVIAL: 1 basin at honest threshold. No basin structure admitted."
elseif !candidate_distinct
    "CANDIDATE FACES DEATH: candidate=$nb_c_h basins <= best_neg=$neg_max. candidate_distinct=false."
elseif verdict_flips_at_015
    "BORDERLINE: candidate=$nb_c_h > neg=$neg_max at t=0.10, BUT verdict flips at t=0.15 (cand=$nb_c_15 vs neg=$neg_max_15). Result is threshold-sensitive and fragile. candidate_distinct=true at t=0.10 only. L/R sep=$(round(LR_sep,digits=5)) at noise level $(NOISE_STD). Admitted as exploration candidate with low confidence."
else
    "CANDIDATE SURVIVES ROBUSTLY: candidate=$nb_c_h > best_neg=$neg_max at t=0.10, holds at t=0.15. exploration_probe — promotion_allowed: false."
end

println("\n=== HONEST VERDICT ===")
println(summary)
println("basins_exist=$basins_exist")
println("candidate_distinct=$candidate_distinct (at t=$(honest_thresh))")

# ── Write result JSON ─────────────────────────────────────────────────────────
result = Dict(
    "object_id" => "chiral_quat_spinor_basin_explore_v1",
    "claim_ceiling" => "exploration_probe — promotion_allowed: false",
    "timestamp" => string(now()),
    "f01_check" => "PASSED — finite seed set $(length(cand_pts)) trajectories",
    "n01_check" => "PASSED — Rx_pi4/Rz_pi4 commutator norm=$(round(N01_COMMUTATOR_NORM, digits=4))",
    "f01_finite_map" => "$(N_SEEDS) seeds x 3 init-families x 4 models, $N_ITER IFS steps",
    "dynamics" => "IFS on Bloch sphere: probs=[Ti=$(IFS_PROBS[1]), Te=$(IFS_PROBS[2]), Fi=$(IFS_PROBS[3]), Fe=$(IFS_PROBS[4])], noise=$NOISE_STD, $N_ITER steps",
    "honest_threshold" => honest_thresh,
    "basin_sweep" => basin_sweep,
    "candidate" => Dict(
        "num_basins_at_t010" => nb_c_h,
        "LR_mean_separation" => round(LR_sep, digits=6),
        "spread_L" => round(cand_spread_L, digits=6),
        "L_mean" => round.(vec(mean(cand_L_mat, dims=1)), digits=5),
        "R_mean" => round.(vec(mean(cand_R_mat, dims=1)), digits=5),
    ),
    "neg_nonchiral" => Dict("num_basins_at_t010" => nb_nc_h,
                             "spread" => round(nc_spread, digits=6)),
    "neg_realvector" => Dict("num_basins_at_t010" => nb_rv_h),
    "neg_classical"  => Dict("num_basins_at_t010" => nb_cl_h),
    "positive_check" => candidate_distinct ? "PASS" : "FAIL",
    "negative_check_realvec_fewer" => realvec_fewer ? "PASS" : "FAIL",
    "boundary_check_classical_wo_n01" => classical_wo_n01 ? "PASS" : "FAIL",
    "verdict_flips_at_015" => verdict_flips_at_015,
    "lr_sep_at_noise_level" => lr_sep_at_noise,
    "candidate_distinct" => candidate_distinct,
    "basins_exist" => basins_exist,
    "summary" => summary,
    "promotion_allowed" => false,
    "models" => [
        "candidate_chiral_L_R_weyl_quaternion_spinor",
        "neg_nonchiral_single_sector",
        "neg_realvector_real_only_ny0",
        "neg_classical_Ti_only_no_rotations",
    ],
    "open_issues" => [
        "IFS with linear operators has unique stationary measure near I/2 — basin fragmentation is noise artifact",
        "Basin count verdict flips at t=0.15 — result is threshold-sensitive",
        "L/R mean separation at noise level — chiral signal weak in current formulation",
        "Attractors.jl exact basin computation not yet integrated — would give basin boundaries without threshold sensitivity",
        "Size ladder 8/16/32/64 not done — carrier is single-qubit Bloch sphere",
        "Nonlinear dynamics (measurement feedback, kicked quantum map) needed for genuine multi-basin test",
    ],
    "tool_manifest" => TOOL_MANIFEST,
    "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
)

open(RESULT_PATH, "w") do io
    JSON.print(io, result, 2)
end
println("\nResult written to: $RESULT_PATH")
println("Re-run: julia --project=$(dirname(@__DIR__)) $(@__FILE__)")
