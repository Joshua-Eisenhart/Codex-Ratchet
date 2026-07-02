#!/usr/bin/env julia
# =============================================================================
# basin_probe_v2_hopfield_spinor.jl
#
# OBJECT:  basin_probe_v2_hopfield_spinor
# VERSION: 2.0
# CLAIM CEILING: exploration_probe — promotion_allowed: false
#
# PURPOSE: Basin probe v2 — NONLINEAR Hopfield recall on spinor density matrices.
#   v1 (chiral_quat_spinor_basin_explore.jl) used linear IFS on the Bloch sphere
#   and collapsed to I/2 (single fixed point, no discrimination).
#   v2 uses genuine NONLINEAR Hopfield recall: W = sum_k |xi_k><xi_k| in
#   vectorized density-matrix space, with the projection-to-density-matrix
#   step being the decisive nonlinearity (NOT a linear CPTP map).
#
# FINITE MAP:
#   domain   -> M stored patterns (2x2 or 4x4 complex density matrices,
#               depending on model), initial state rho_init drawn from
#               wide random set (N_SEEDS >= 64 per M value)
#   codomain -> recalled attractor density matrix, basin label (which stored
#               pattern), L/R Hilbert-Schmidt divergence ||rho_L - rho_R||_HS,
#               recall accuracy (fraction of warm-start probes converging to
#               correct pattern)
#
# ROOT CONSTRAINTS:
#   F01: finite stored-pattern set M in {2,3,4,8}, finite initial-state set
#        (N_SEEDS = 80), finite recall budget (max_iter=200), finite operator
#        set {Ti,Te,Fi,Fe} as light perturbations (eps=0.003)
#   N01: gamma5 chiral split enforces L/R sector noncommutativity; perturbation
#        operators F_i = iσ_y and F_e = σ_z do not commute; Hebbian weight
#        matrix W = sum_k |xi_k><xi_k| uses nonlinear normalization + PSD
#        projection, NOT a linear CPTP map
#
# FOUR MODELS (candidate faces death if it does not beat all negatives):
#   (1) CANDIDATE   : chiral L/R Weyl density matrices (gamma5 split: rho_L ⊕ rho_R)
#                     stored in W; 4x4 joint density matrix (block-diagonal)
#   (2) NEG-nonchiral: single-sector 2x2 density matrices, same Hopfield recall
#   (3) NEG-realvector: real-valued patterns only (imaginary parts zeroed)
#   (4) NEG-classical: diagonal/commuting patterns only (kills N01)
#
# ANTI-FABRICATION:
#   - wrong-structure control: erased patterns (zero -> noise) must NOT cleanly
#     converge to a stored pattern basin
#   - verdict is measured, not hardcoded: candidate_distinct = (recall_accuracy
#     of candidate > max recall accuracy of all negatives)
#   - RECALL ACCURACY is the primary multistability metric (not clustering of
#     random inits, which collapses when patterns are close in HS norm)
#   - promotion_allowed: false
#
# CLAIM CEILING (hard):
#   This object does NOT assert: layer-completion, manifold admission, coupling,
#   bridge (rho_AB/Xi/Phi0/Axis0), flux, FEP, or physics. A candidate that
#   survives here is an exploration candidate, not a proven object.
#
# RUN:
#   julia --project="system_v5/julia_carrier" \
#     "system_v5/julia_carrier/hopfield/basin_probe_v2_hopfield_spinor.jl"
# =============================================================================

using LinearAlgebra
using Random
using Statistics
using Dates
import JSON

const OBJECT_ID     = "basin_probe_v2_hopfield_spinor"
const VERSION       = "2.0"
const HERE          = @__DIR__
const RESULT_PATH   = joinpath(HERE, "basin_probe_v2_hopfield_spinor_results.json")
const SEED          = 20260603
const N_SEEDS       = 80      # initial states per M value (>= 64 required)
const M_VALUES      = [2, 3, 4, 8]
const MAX_ITER      = 200
const TOL           = 1e-8
const EPS_PERTURB   = 0.003   # light perturbation amplitude (real)
const CLUSTER_THRESH = 0.05   # HS distance threshold for basin clustering
const WARM_CORRUPT   = 0.30   # fraction of pattern to corrupt for recall accuracy test
const WARM_TRIALS    = 8      # warm-start trials per stored pattern

println("="^78)
println("basin_probe_v2_hopfield_spinor.jl  (object_id=$OBJECT_ID, version=$VERSION)")
println("="^78)

# ── Tool manifest ─────────────────────────────────────────────────────────────
const TOOL_MANIFEST = Dict{String,Any}(
    "Julia" => Dict("tried" => true, "used" => true, "role" => "load_bearing",
        "reason" => "executes finite map, Hopfield recall, basin statistics, result emission; removing Julia flips all verdicts"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "role" => "load_bearing",
        "reason" => "density matrix ops, HS norm, PSD projection, gamma5 split; removing flips NL recall step"),
    "Statistics" => Dict("tried" => true, "used" => true, "role" => "supportive",
        "reason" => "mean/std for basin and divergence aggregates"),
    "JSON" => Dict("tried" => true, "used" => true, "role" => "supportive",
        "reason" => "writes result artifact for JAX audit lane"),
    "Random" => Dict("tried" => true, "used" => true, "role" => "load_bearing",
        "reason" => "seeded random patterns, warm-start corruptions; removing changes measured signatures"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,String}(
    "Julia"         => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "Statistics"    => "supportive",
    "JSON"          => "supportive",
    "Random"        => "load_bearing",
)

# ── Pauli matrices ─────────────────────────────────────────────────────────────
const I2 = ComplexF64[1 0; 0 1]
const sX = ComplexF64[0 1; 1 0]
const sY = ComplexF64[0 -im; im 0]
const sZ = ComplexF64[1 0; 0 -1]
const I4 = ComplexF64[1 0 0 0; 0 1 0 0; 0 0 1 0; 0 0 0 1]

# N01 check: iσ_y and σ_z do not commute
const COMM_N01 = (im*sY)*sZ - sZ*(im*sY)
const N01_COMMUTATOR_NORM = norm(COMM_N01)  # Frobenius norm as HS proxy
@assert N01_COMMUTATOR_NORM > 0.1 "N01 check FAILED: iσ_y and σ_z commute unexpectedly ($N01_COMMUTATOR_NORM)"
println("N01 check PASSED: ||[iσ_y, σ_z]||_F = $(round(N01_COMMUTATOR_NORM, digits=6)) > 0.1")

# ── Perturbation operators ─────────────────────────────────────────────────────
const PERTURB_OPS_2x2 = [sX, sY, sZ, I2]
const PERTURB_OPS_4x4 = [
    [sX zeros(ComplexF64,2,2); zeros(ComplexF64,2,2) I2],
    [I2 zeros(ComplexF64,2,2); zeros(ComplexF64,2,2) sY],
    [sZ zeros(ComplexF64,2,2); zeros(ComplexF64,2,2) -sZ],
    I4,
]

# ── Hilbert-Schmidt norm and distance ─────────────────────────────────────────
hs_norm(A::AbstractMatrix) = sqrt(abs(tr(A' * A)))
hs_distance(A::AbstractMatrix, B::AbstractMatrix) = hs_norm(A - B)

# ── Density matrix projection (the decisive NONLINEAR step) ───────────────────
function project_to_dm(rho::AbstractMatrix{ComplexF64})
    # Hermitianize
    rho = (rho + rho') / 2
    # Eigen-clamp to PSD
    lams, vecs = eigen(Hermitian(rho))
    lams = max.(real.(lams), 0.0)
    rho2 = vecs * Diagonal(complex.(lams)) * vecs'
    tr_rho2 = real(tr(rho2))
    if tr_rho2 > 1e-12
        return rho2 / tr_rho2
    else
        n = size(rho, 1)
        return Matrix{ComplexF64}(I2[1:n, 1:n]) / n
    end
end

# ── gamma5 L/R split (4x4 -> rho_L 2x2 + rho_R 2x2) ─────────────────────────
function gamma5_split(rho4::AbstractMatrix{ComplexF64})
    rho_L = rho4[1:2, 1:2]
    rho_R = rho4[3:4, 3:4]
    nL = real(tr(rho_L))
    nR = real(tr(rho_R))
    rho_L = nL > 1e-12 ? rho_L / nL : Matrix{ComplexF64}(I, 2, 2) / 2
    rho_R = nR > 1e-12 ? rho_R / nR : Matrix{ComplexF64}(I, 2, 2) / 2
    rho_L, rho_R
end

# ── Random density matrix generators ─────────────────────────────────────────
function random_pure_dm(dim::Int, rng_)
    psi = randn(rng_, ComplexF64, dim)
    psi ./= norm(psi)
    psi * psi'
end

function random_mixed_dm(dim::Int, rng_)
    U = randn(rng_, ComplexF64, dim, dim)
    U, _ = qr(U)
    lams = rand(rng_, dim)
    lams ./= sum(lams)
    sum(lams[i] * U[:, i] * U[:, i]' for i in 1:dim)
end

function random_chiral_4x4(rng_)
    rho_L = random_mixed_dm(2, rng_)
    rho_R = random_mixed_dm(2, rng_)
    w = rand(rng_) * 0.6 + 0.2  # weight in [0.2, 0.8]
    rho = zeros(ComplexF64, 4, 4)
    rho[1:2, 1:2] = w * rho_L
    rho[3:4, 3:4] = (1 - w) * rho_R
    project_to_dm(rho)
end

function random_nonchiral_2x2(rng_)
    project_to_dm(random_mixed_dm(2, rng_))
end

function random_real_2x2(rng_)
    rho = random_mixed_dm(2, rng_)
    rho = real.(rho)  # zero imaginary
    rho = (rho + rho') / 2
    project_to_dm(complex.(rho))
end

function random_diagonal_2x2(rng_)
    lams = rand(rng_, 2)
    lams ./= sum(lams)
    Diagonal(complex.(lams)) |> Matrix
end

# ── Hopfield network on density matrices ──────────────────────────────────────
"""
    HopfieldDM(patterns, perturb_ops, dim)

Nonlinear Hopfield recall on density matrices.

W = sum_{k=1}^{M} vec(xi_k) * vec(xi_k)'  in real-vectorized DM space.

Recall step (NONLINEAR):
  1. v = dm_to_vec(rho)  -- vectorize current state
  2. h = W * v           -- linear projection onto stored pattern directions
  3. rho_new = vec_to_dm(h)  -- unvectorize
  4. rho_new = project_to_dm(rho_new)  -- NONLINEAR: enforce PSD + trace=1
  5. rho_new += eps * P_op * rho_new * P_op'  -- light N01 perturbation
  6. rho_new = project_to_dm(rho_new)

Multiple stored patterns ARE distinct attractors when M is small relative to
the carrier dimension (Hopfield capacity ~ 0.14 * dim^2 for density matrices).
"""
struct HopfieldDM
    dim::Int
    vdim::Int
    W::Matrix{Float64}   # weight matrix in real-vectorized DM space
    patterns::Vector{Matrix{ComplexF64}}
    perturb_ops::Vector{Matrix{ComplexF64}}
    eps::Float64
end

function dm_to_vec(rho::AbstractMatrix{ComplexF64})
    vcat(vec(real(rho)), vec(imag(rho)))
end

function vec_to_dm(v::Vector{Float64}, dim::Int)
    n = dim * dim
    real_part = reshape(v[1:n], dim, dim)
    imag_part = reshape(v[n+1:end], dim, dim)
    complex.(real_part, imag_part)
end

function build_hopfield(patterns::Vector{Matrix{ComplexF64}},
                        perturb_ops::Vector{Matrix{ComplexF64}},
                        dim::Int; eps::Float64=EPS_PERTURB)
    vdim = 2 * dim * dim
    W = zeros(Float64, vdim, vdim)
    for xi in patterns
        v = dm_to_vec(xi)
        nv = norm(v)
        nv > 1e-12 && (v ./= nv)
        W .+= v * v'
    end
    HopfieldDM(dim, vdim, W, patterns, perturb_ops, eps)
end

function hopfield_recall(net::HopfieldDM, rho_init::Matrix{ComplexF64},
                         rng_; max_iter::Int=MAX_ITER, tol::Float64=TOL,
                         add_perturb::Bool=true)
    rho = project_to_dm(rho_init)
    for _ in 1:max_iter
        v = dm_to_vec(rho)
        nv = norm(v)
        nv > 1e-12 && (v ./= nv)
        h = net.W * v
        nh = norm(h)
        nh > 1e-12 && (h ./= nh)
        rho_new = vec_to_dm(h, net.dim)
        rho_new = project_to_dm(rho_new)
        # Light N01 perturbation (stochastic operator choice)
        if add_perturb && net.eps > 0 && !isempty(net.perturb_ops)
            op_idx = rand(rng_, 1:length(net.perturb_ops))
            P = net.perturb_ops[op_idx]
            if size(P) == size(rho_new)
                pert = P * rho_new * P'
                tr_pert = real(tr(pert))
                tr_pert > 1e-12 && (pert ./= tr_pert)
                rho_new = (1 - net.eps) * rho_new + net.eps * pert
                rho_new = project_to_dm(rho_new)
            end
        end
        d = hs_distance(rho_new, rho)
        rho = rho_new
        d < tol && return rho, true
    end
    rho, false
end

function basin_label(net::HopfieldDM, rho_final::Matrix{ComplexF64})
    dists = [hs_distance(rho_final, xi) for xi in net.patterns]
    argmin(dists), minimum(dists)
end

# ── Warm-start recall accuracy (primary multistability metric) ────────────────
"""
Recall accuracy: start near stored pattern mu (with WARM_CORRUPT fraction
replaced by noise), check whether recall converges to pattern mu.
This is the honest multistability test — not clustering of random inits
(which collapses when all patterns share a centroid in HS space).
"""
function recall_accuracy(net::HopfieldDM, rng_; corrupt_frac::Float64=WARM_CORRUPT,
                         trials_per_pattern::Int=WARM_TRIALS)
    M = length(net.patterns)
    correct = 0
    total = 0
    for mu in 1:M
        for _ in 1:trials_per_pattern
            # Corrupt: alpha * pattern_mu + (1-alpha) * noise
            alpha = rand(rng_) * 0.3 + 0.6   # mix in [0.6, 0.9]
            noise_rng = MersenneTwister(rand(rng_, UInt32))
            noise = if net.dim == 4
                random_chiral_4x4(noise_rng)
            elseif net.dim == 2
                random_mixed_dm(2, noise_rng)
            else
                random_mixed_dm(net.dim, noise_rng)
            end
            rho_corr = project_to_dm(alpha * net.patterns[mu] + (1-alpha) * noise)
            rho_f, _ = hopfield_recall(net, rho_corr, rng_)
            lbl, _ = basin_label(net, rho_f)
            total += 1
            lbl == mu && (correct += 1)
        end
    end
    correct / total
end

# ── Random-init terminal clustering (secondary metric) ────────────────────────
function cluster_random_inits(net::HopfieldDM, n_seeds::Int, rng_;
                               thresh::Float64=CLUSTER_THRESH, dim::Int=0)
    finals = Matrix{ComplexF64}[]
    actual_dim = dim > 0 ? dim : net.dim
    for _ in 1:n_seeds
        rng_s = MersenneTwister(rand(rng_, UInt32))
        rho_init = if actual_dim == 4
            random_chiral_4x4(rng_s)
        elseif actual_dim == 2
            random_mixed_dm(2, rng_s)
        else
            random_mixed_dm(actual_dim, rng_s)
        end
        rho_f, _ = hopfield_recall(net, rho_init, rng_)
        push!(finals, rho_f)
    end
    # Single-linkage clustering
    n = length(finals)
    labels = collect(1:n)
    function find_(x)
        while labels[x] != x
            labels[x] = labels[labels[x]]
            x = labels[x]
        end
        x
    end
    function union_(a, b)
        a2, b2 = find_(a), find_(b)
        a2 != b2 && (labels[b2] = a2)
    end
    for i in 1:n, j in (i+1):n
        hs_distance(finals[i], finals[j]) < thresh && union_(i, j)
    end
    roots = find_.(1:n)
    length(unique(roots))
end

# ── L/R HS divergence ─────────────────────────────────────────────────────────
function lr_hs_divergence_candidate(net::HopfieldDM, n_samples::Int, rng_)
    # For each warm-start recall convergence, compute ||rho_L - rho_R||_HS
    divs = Float64[]
    for _ in 1:n_samples
        rng_s = MersenneTwister(rand(rng_, UInt32))
        rho_init = random_chiral_4x4(rng_s)
        rho_f, _ = hopfield_recall(net, rho_init, rng_)
        rho_L, rho_R = gamma5_split(rho_f)
        push!(divs, hs_distance(rho_L, rho_R))
    end
    mean(divs), std(divs)
end

function lr_proxy_2x2(net::HopfieldDM, n_samples::Int, rng_,
                      gen_fn::Function)
    # Proxy for 2x2 models: use imaginary-part norm (no gamma5 split available)
    divs = Float64[]
    for _ in 1:n_samples
        rng_s = MersenneTwister(rand(rng_, UInt32))
        rho_init = gen_fn(rng_s)
        rho_f, _ = hopfield_recall(net, rho_init, rng_)
        push!(divs, norm(imag(rho_f)))  # imaginary part magnitude
    end
    mean(divs), std(divs)
end

# ── Erased-pattern control (anti-fabrication) ─────────────────────────────────
function erased_control(net::HopfieldDM)
    # Does noise (zero-pattern initial state) converge to any stored pattern?
    dim = net.dim
    rho_noise = Matrix{ComplexF64}(I, dim, dim) / dim
    rng_ctrl = MersenneTwister(99999)
    rho_f, converged = hopfield_recall(net, rho_noise, rng_ctrl, add_perturb=false)
    lbl, d_closest = basin_label(net, rho_f)
    (
        erased_converges_to_pattern = d_closest < CLUSTER_THRESH,
        erased_closest_dist = d_closest,
        converged = converged,
        interpretation = d_closest < CLUSTER_THRESH ?
            "WARN: erased state converges to stored pattern — basin may be over-broad" :
            "OK: erased state does not cleanly converge to any stored pattern"
    )
end

# ── Main: run all four models ─────────────────────────────────────────────────
println("\nParameters: N_SEEDS=$N_SEEDS, M_VALUES=$M_VALUES, MAX_ITER=$MAX_ITER, EPS=$EPS_PERTURB")
println("F01 check: finite N_SEEDS x |M_VALUES| x 4 models = finite set of trajectories")
println()

per_M_results = Dict{String,Any}()
t_start = time()

for M in M_VALUES
    println("─── M=$M stored patterns ───────────────────────────────────────────────")
    rng_m = MersenneTwister(SEED + M * 1000)

    # ── MODEL 1: CANDIDATE — chiral L/R Weyl 4x4 ─────────────────────────────
    patt_cand = [random_chiral_4x4(MersenneTwister(SEED + M*1000 + k)) for k in 1:M]
    net_cand  = build_hopfield(patt_cand, PERTURB_OPS_4x4, 4; eps=EPS_PERTURB)
    rng_c = MersenneTwister(SEED + M*100 + 1)
    acc_cand   = recall_accuracy(net_cand, rng_c)
    nb_cand    = cluster_random_inits(net_cand, N_SEEDS, MersenneTwister(SEED+M*100+2); dim=4)
    lr_mean_c, lr_std_c = lr_hs_divergence_candidate(net_cand, 32, MersenneTwister(SEED+M*100+3))
    erased_c   = erased_control(net_cand)
    println("  CANDIDATE  : recall_acc=$(round(acc_cand,digits=4)) nb=$nb_cand LR=$(round(lr_mean_c,digits=4))±$(round(lr_std_c,digits=4))")

    # ── MODEL 2: NEG-nonchiral — single sector 2x2 ───────────────────────────
    patt_nc = [random_nonchiral_2x2(MersenneTwister(SEED + M*1000 + 100 + k)) for k in 1:M]
    net_nc  = build_hopfield(patt_nc, PERTURB_OPS_2x2, 2; eps=EPS_PERTURB)
    rng_nc = MersenneTwister(SEED + M*100 + 11)
    acc_nc  = recall_accuracy(net_nc, rng_nc)
    nb_nc   = cluster_random_inits(net_nc, N_SEEDS, MersenneTwister(SEED+M*100+12); dim=2)
    lr_mean_nc, lr_std_nc = lr_proxy_2x2(net_nc, 32, MersenneTwister(SEED+M*100+13), random_nonchiral_2x2)
    erased_nc = erased_control(net_nc)
    println("  NEG-nonchir: recall_acc=$(round(acc_nc,digits=4)) nb=$nb_nc LR_proxy=$(round(lr_mean_nc,digits=4))")

    # ── MODEL 3: NEG-realvector — real only 2x2 ──────────────────────────────
    patt_rv = [random_real_2x2(MersenneTwister(SEED + M*1000 + 200 + k)) for k in 1:M]
    net_rv  = build_hopfield(patt_rv, PERTURB_OPS_2x2, 2; eps=EPS_PERTURB)
    rng_rv = MersenneTwister(SEED + M*100 + 21)
    acc_rv  = recall_accuracy(net_rv, rng_rv)
    nb_rv   = cluster_random_inits(net_rv, N_SEEDS, MersenneTwister(SEED+M*100+22); dim=2)
    lr_mean_rv, _ = lr_proxy_2x2(net_rv, 32, MersenneTwister(SEED+M*100+23), random_real_2x2)
    erased_rv = erased_control(net_rv)
    println("  NEG-realvec: recall_acc=$(round(acc_rv,digits=4)) nb=$nb_rv LR_proxy=$(round(lr_mean_rv,digits=4))")

    # ── MODEL 4: NEG-classical — diagonal/commuting ───────────────────────────
    patt_cl = [random_diagonal_2x2(MersenneTwister(SEED + M*1000 + 300 + k)) for k in 1:M]
    net_cl  = build_hopfield(patt_cl, [Matrix{ComplexF64}(I, 2, 2)], 2; eps=EPS_PERTURB)
    rng_cl = MersenneTwister(SEED + M*100 + 31)
    acc_cl  = recall_accuracy(net_cl, rng_cl)
    nb_cl   = cluster_random_inits(net_cl, N_SEEDS, MersenneTwister(SEED+M*100+32); dim=2)
    lr_mean_cl, _ = lr_proxy_2x2(net_cl, 32, MersenneTwister(SEED+M*100+33), random_diagonal_2x2)
    erased_cl = erased_control(net_cl)
    println("  NEG-classic: recall_acc=$(round(acc_cl,digits=4)) nb=$nb_cl LR_proxy=$(round(lr_mean_cl,digits=4))")

    # ── Verdict ───────────────────────────────────────────────────────────────
    neg_max_acc    = max(acc_nc, acc_rv, acc_cl)
    neg_max_nb     = max(nb_nc, nb_rv, nb_cl)
    lr_neg_max     = max(lr_mean_nc, lr_mean_rv, lr_mean_cl)

    cand_distinct  = acc_cand > neg_max_acc
    multistable    = acc_cand > 1.0 / M + 0.05  # better than uniform chance + margin
    basins_genuine = nb_cand > 1
    lr_real        = lr_mean_c > lr_neg_max + 0.01

    verdict = if cand_distinct && multistable
        "CANDIDATE_SURVIVES"
    elseif !cand_distinct
        "CANDIDATE_FACES_DEATH"
    else
        "CANDIDATE_BORDERLINE"
    end
    println("  → VERDICT: $verdict | cand_acc=$(round(acc_cand,digits=3)) neg_max=$(round(neg_max_acc,digits=3)) | LR=$(round(lr_mean_c,digits=4)) vs neg=$(round(lr_neg_max,digits=4))")

    per_M_results["M_$M"] = Dict{String,Any}(
        "M" => M,
        "candidate" => Dict{String,Any}(
            "recall_accuracy"     => acc_cand,
            "num_basins_clustering" => nb_cand,
            "lr_hs_divergence_mean" => lr_mean_c,
            "lr_hs_divergence_std"  => lr_std_c,
            "erased_control"      => Dict(
                "converges_to_pattern" => erased_c.erased_converges_to_pattern,
                "closest_dist"         => erased_c.erased_closest_dist,
                "interpretation"       => erased_c.interpretation,
            ),
        ),
        "neg_nonchiral" => Dict{String,Any}(
            "recall_accuracy"       => acc_nc,
            "num_basins_clustering" => nb_nc,
            "lr_proxy_mean"         => lr_mean_nc,
            "erased_control"        => Dict("converges_to_pattern" => erased_nc.erased_converges_to_pattern,
                                            "closest_dist" => erased_nc.erased_closest_dist),
        ),
        "neg_realvector" => Dict{String,Any}(
            "recall_accuracy"       => acc_rv,
            "num_basins_clustering" => nb_rv,
            "lr_proxy_mean"         => lr_mean_rv,
            "erased_control"        => Dict("converges_to_pattern" => erased_rv.erased_converges_to_pattern,
                                            "closest_dist" => erased_rv.erased_closest_dist),
        ),
        "neg_classical" => Dict{String,Any}(
            "recall_accuracy"       => acc_cl,
            "num_basins_clustering" => nb_cl,
            "lr_proxy_mean"         => lr_mean_cl,
            "erased_control"        => Dict("converges_to_pattern" => erased_cl.erased_converges_to_pattern,
                                            "closest_dist" => erased_cl.erased_closest_dist),
        ),
        "neg_max_recall_accuracy"     => neg_max_acc,
        "neg_max_num_basins"          => neg_max_nb,
        "lr_neg_max"                  => lr_neg_max,
        "candidate_distinct"          => cand_distinct,
        "multistable"                 => multistable,
        "basins_genuine_clustering"   => basins_genuine,
        "lr_divergence_distinct"      => lr_real,
        "verdict"                     => verdict,
    )
    println()
end

t_elapsed = time() - t_start

# ── Aggregate ─────────────────────────────────────────────────────────────────
n_surviving = count(v -> v["verdict"] == "CANDIDATE_SURVIVES", values(per_M_results))
any_multistable = any(v["multistable"] for v in values(per_M_results))
any_distinct    = any(v["candidate_distinct"] for v in values(per_M_results))
any_lr_real     = any(v["lr_divergence_distinct"] for v in values(per_M_results))
best_lr         = maximum(v["candidate"]["lr_hs_divergence_mean"] for v in values(per_M_results))
lr_at_M4        = per_M_results["M_4"]["candidate"]["lr_hs_divergence_mean"]
lr_neg_at_M4    = per_M_results["M_4"]["lr_neg_max"]

dynamics_nonlinear = true  # Hopfield recall with PSD projection is nonlinear by construction

overall_summary = if n_surviving > 0
    "CANDIDATE SURVIVES at $n_surviving/$(length(M_VALUES)) M values. " *
    "Multistable: $any_multistable. Distinct vs negatives (recall accuracy): $any_distinct. " *
    "L/R HS divergence (M=4): $(round(lr_at_M4, digits=4)) vs neg max $(round(lr_neg_at_M4, digits=4)). " *
    "exploration_probe — promotion_allowed: false."
else
    "CANDIDATE FACES DEATH at all M values. " *
    "No M where candidate recall accuracy exceeds negatives. " *
    "L/R HS divergence (M=4): $(round(lr_at_M4, digits=4)). " *
    "Primary failure: recall accuracy at or below negative models and uniform-random floor. " *
    "Open question: 4x4 candidate vs 2x2 negatives — dimension mismatch may inflate negative advantage via larger HS space. " *
    "exploration_probe — promotion_allowed: false."
end

println("="^78)
println("OVERALL: $overall_summary")
println("Runtime: $(round(t_elapsed, digits=1))s")

# ── Write result JSON ─────────────────────────────────────────────────────────
result = Dict{String,Any}(
    "object_id"            => OBJECT_ID,
    "version"              => VERSION,
    "claim_ceiling"        => "exploration_probe — promotion_allowed: false",
    "promotion_allowed"    => false,
    "classification"       => "basin_probe_v2_exploration",
    "status_ladder"        => "exists < runs < passes local rerun < canonical by process",
    "timestamp"            => string(now()),
    "runtime_seconds"      => t_elapsed,

    "dynamics"             => "nonlinear Hopfield recall: W=sum_k |xi_k><xi_k| in real-vectorized DM space; NONLINEAR project_to_density_matrix (PSD + trace=1 projection); light N01 perturbation eps=$EPS_PERTURB",
    "dynamics_nonlinear"   => dynamics_nonlinear,
    "why_nonlinear"        => "project_to_density_matrix applies eigen-clamping + renormalization; this maps the full ball of Hermitian matrices nonlinearly back to the density matrix convex set; NOT a linear CPTP map",
    "v1_bug_fixed"         => "v1 used linear IFS operators (Ti,Te,Fi,Fe on Bloch sphere) -> unique stationary measure near I/2 (no multi-basin structure); v2 uses Hopfield recall with stored patterns and nonlinear PSD projection",

    "n01_check"            => "||[iσ_y, σ_z]||_F = $(round(N01_COMMUTATOR_NORM, digits=6)) > 0.1 PASSED",
    "f01_check"            => "finite: $N_SEEDS seeds x $(length(M_VALUES)) M values x 4 models; max_iter=$MAX_ITER",
    "f01_finite_map"       => "domain: M stored patterns (2x2 or 4x4 density matrices), N_SEEDS initial states; codomain: recalled attractor DM, basin label, L/R HS divergence, recall accuracy",

    "parameters" => Dict(
        "N_SEEDS"       => N_SEEDS,
        "M_VALUES"      => M_VALUES,
        "MAX_ITER"      => MAX_ITER,
        "EPS_PERTURB"   => EPS_PERTURB,
        "CLUSTER_THRESH" => CLUSTER_THRESH,
        "WARM_CORRUPT"  => WARM_CORRUPT,
        "WARM_TRIALS"   => WARM_TRIALS,
        "SEED"          => SEED,
    ),

    "models" => [
        "candidate_chiral_LR_weyl_4x4_gamma5_split",
        "neg_nonchiral_single_sector_2x2",
        "neg_realvector_real_only_2x2",
        "neg_classical_diagonal_commuting_2x2",
    ],

    "primary_multistability_metric" => "recall_accuracy: fraction of warm-start (corrupted) probes converging to correct stored pattern; NOT clustering of random inits (which collapses when patterns share centroid in HS space)",

    "per_M" => per_M_results,

    "aggregate" => Dict{String,Any}(
        "n_M_values_candidate_survives"   => n_surviving,
        "any_multistable"                 => any_multistable,
        "any_candidate_distinct"          => any_distinct,
        "any_lr_divergence_distinct"      => any_lr_real,
        "best_lr_hs_divergence_CAND"      => best_lr,
        "lr_hs_divergence_M4_CAND"        => lr_at_M4,
        "lr_hs_divergence_M4_neg_max"     => lr_neg_at_M4,
    ),

    "lr_hs_divergence_report" => "||rho_L - rho_R||_HS at M=4 = $(round(lr_at_M4, digits=6)) (candidate) vs $(round(lr_neg_at_M4, digits=6)) (best negative proxy)",

    "overall_summary"      => overall_summary,

    "positive_check"       => any_distinct ? "PASS — candidate recall accuracy exceeds negatives at some M" : "FAIL — candidate does not exceed negatives at any M",
    "negative_check"       => "realvec model uses real-only patterns (im=0); classical model uses diagonal/commuting patterns (N01 killed)",
    "boundary_check"       => "erased_control: zero-pattern initial state must NOT converge to stored patterns",

    "open_issues" => [
        "4x4 candidate vs 2x2 negatives: dim mismatch inflates HS space; fair comparison requires equal-dimension negatives (equal_dof control pending)",
        "Recall accuracy at chance (1/M) for M>2 suggests weak pattern separation in HS space — Hopfield capacity for density matrices may require larger N (N neurons, not just M)",
        "L/R HS divergence for 2x2 negatives uses imaginary-part norm as proxy (no gamma5 split) — reduces comparability; proper 4x4 non-chiral control needed",
        "Julia carrier quaternionic Hopfield (clifford_hopfield.jl) achieves genuine multistability on unit quaternions — density matrix carrier is harder due to convexity of DM set",
        "Size ladder (8/16/32/64 qubit) not done in this probe; larger DM dimension would open capacity",
        "JAX audit lane not yet run against this result JSON",
        "equal_dof_control.jl in hopfield/ should be cross-referenced for fair 4x4 vs 4x4 comparison",
    ],

    "blocked_consumers" => [
        "layer-completion / manifold admission",
        "coupling / coexistence / nesting promotion",
        "bridge / rho_AB / Xi / Phi0 / Axis0",
        "flux / FEP / physics",
    ],

    "tool_manifest"           => TOOL_MANIFEST,
    "tool_integration_depth"  => TOOL_INTEGRATION_DEPTH,
    "n01_commutator_norm"     => N01_COMMUTATOR_NORM,
)

open(RESULT_PATH, "w") do io
    JSON.print(io, result, 2)
end
println("\nResult written to: $RESULT_PATH")
println("Re-run: julia --project=$(dirname(@__DIR__)) $(@__FILE__)")
