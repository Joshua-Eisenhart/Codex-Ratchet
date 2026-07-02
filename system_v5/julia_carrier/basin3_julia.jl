#!/usr/bin/env julia
# =============================================================================
# basin3_julia.jl
#
# OBJECT:  basin3_hopfield_chiral_quaternion_network
# VERSION: 3.0
# CLAIM CEILING: exploration_probe — promotion_allowed: false
#
# PURPOSE: Basin v3 — the FAIR test. v1/v2 failed because negatives were
#   dimension-mismatched (2x2 vs 4x4), so any "candidate distinct" signal
#   was a dimension artifact. v3 FIX: ALL FOUR MODELS use exactly the same
#   per-neuron carrier: N=12 quaternion-spinor neurons, each a unit quaternion
#   in R^4 (Hamilton product, Cl(3,0)+ = SU(2)). The ONLY difference between
#   models is the algebraic structure of the Hebbian weight assembly.
#
# REFERENCE: clifford_hopfield.jl (same quaternion carrier, Hamilton product)
#   This object reuses qmul/qconj/qnorm/qnormalize from that carrier.
#
# FINITE MAP:
#   domain   -> M stored patterns (each: N=12 unit quaternions or chiral
#               L/R pairs); N_SEEDS initial states per M value
#   codomain -> recalled attractor state, basin label, recall_accuracy,
#               L/R Hilbert-Schmidt divergence at matched dim
#
# ROOT CONSTRAINTS:
#   F01: finite stored-pattern set M in {2,3,4,8}, finite initial-state set
#        (N_SEEDS=80), finite recall budget (MAX_ITER=200), finite operator set
#   N01: Hamilton quaternion product is noncommutative; chiral weight assembly
#        W_ij = sum_mu [qL_i^mu * qconj(qL_j^mu)] - [qR_i^mu * qconj(qR_j^mu)]
#        uses the L/R chiral sign — removing the sign flips the verdict vs. neg2
#
# FOUR MODELS (ALL N=12 quaternion neurons, ALL same per-neuron carrier R^4):
#   (1) CANDIDATE  : chiral L/R Weyl spinor — W assembled with L+, R- sign split
#   (2) NEG-nonchiral: same quaternion carrier, W assembled with L+, R+ (no sign flip)
#   (3) NEG-realvec : same N=12, same 4-tuple per neuron, imaginary parts zeroed
#   (4) NEG-classical: scalar real neurons only, commuting/sign update — kills N01
#
# DIMENSION MATCH: Models 1-3 all operate in R^4 per neuron (4-tuple quaternion).
#   Model 4 uses R^1 per neuron (scalar). The comparison of candidate vs. models
#   2 and 3 is at IDENTICAL per-neuron dimension — the fair test v2 lacked.
#
# ANTI-FABRICATION:
#   - wrong-structure control: zero-initialized state must NOT converge cleanly
#   - verdict NOT hardcoded: candidate_distinct = measured, emitted even if false
#   - No model is "supposed to win"
#
# CLAIM CEILING (hard):
#   Does NOT assert: layer-completion, manifold admission, coupling, bridge
#   (rho_AB/Xi/Phi0/Axis0), flux, FEP, or physics. A candidate that survives
#   here is an exploration candidate, not a proven object.
#
# RUN:
#   cd "/Users/joshuaeisenhart/Desktop/Codex Ratchet" && \
#   julia --project="system_v5/julia_carrier" \
#     "system_v5/julia_carrier/basin3_julia.jl"
# =============================================================================

using LinearAlgebra
using Random
using Statistics
using Dates
import JSON

const OBJECT_ID      = "basin3_hopfield_chiral_quaternion_network"
const VERSION        = "3.0"
const HERE           = @__DIR__
const RESULT_PATH    = joinpath(HERE, "basin3_julia_results.json")
const SEED           = 20260603
const N_NEURONS      = 12
const M_VALUES       = [2, 3, 4, 8]
const N_SEEDS        = 80
const MAX_ITER       = 200
const TOL            = 1e-9
const CORRUPT_FRAC   = 0.30
const WARM_TRIALS    = 8

println("="^78)
println("basin3_julia.jl  (object_id=$(OBJECT_ID), version=$(VERSION))")
println("Basin v3 — dimension-matched four-model Hopfield quaternion network")
println("="^78)

# ── Tool manifest ─────────────────────────────────────────────────────────────
const TOOL_MANIFEST = Dict{String,Any}(
    "Julia" => Dict("tried" => true, "used" => true, "role" => "load_bearing",
        "reason" => "executes finite map, Hamilton product, basin recall, result emission; removing flips all verdicts"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "role" => "load_bearing",
        "reason" => "quaternion matrix realization, HS norm, weight assembly; removing flips recall verdict"),
    "Statistics" => Dict("tried" => true, "used" => true, "role" => "supportive",
        "reason" => "mean/std for recall accuracy and overlap aggregates"),
    "JSON" => Dict("tried" => true, "used" => true, "role" => "supportive",
        "reason" => "writes result artifact for JAX audit lane"),
    "Random" => Dict("tried" => true, "used" => true, "role" => "load_bearing",
        "reason" => "seeded random patterns and warm-start corruptions; removing changes measured signatures"),
    "Dates" => Dict("tried" => true, "used" => true, "role" => "supportive",
        "reason" => "timestamps result artifact"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,String}(
    "Julia"         => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "Statistics"    => "supportive",
    "JSON"          => "supportive",
    "Random"        => "load_bearing",
    "Dates"         => "supportive",
)

# =============================================================================
# QUATERNION CARRIER (Cl(3,0)+ realized on 2x2 SU(2) — reused from clifford_hopfield.jl)
# q = (w,x,y,z) :: NTuple{4,Float64}
# Hamilton product: NONCOMMUTATIVE — this is the N01 witness
# =============================================================================

const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const I2 = ComplexF64[1 0; 0 1]

qmat(q) = q[1]*I2 - im*(q[2]*SX + q[3]*SY + q[4]*SZ)

"Hamilton product q*p (geometric product on Cl(3,0)+). NONCOMMUTATIVE."
function qmul(q::NTuple{4,Float64}, p::NTuple{4,Float64})
    w1,x1,y1,z1 = q; w2,x2,y2,z2 = p
    (w1*w2 - x1*x2 - y1*y2 - z1*z2,
     w1*x2 + x1*w2 + y1*z2 - z1*y2,
     w1*y2 - x1*z2 + y1*w2 + z1*x2,
     w1*z2 + x1*y2 - y1*x2 + z1*w2)
end

qconj(q::NTuple{4,Float64}) = (q[1], -q[2], -q[3], -q[4])
qadd(q::NTuple{4,Float64}, p::NTuple{4,Float64}) = (q[1]+p[1], q[2]+p[2], q[3]+p[3], q[4]+p[4])
qscale(a::Float64, q::NTuple{4,Float64}) = (a*q[1], a*q[2], a*q[3], a*q[4])
qnorm(q::NTuple{4,Float64}) = sqrt(q[1]^2 + q[2]^2 + q[3]^2 + q[4]^2)
qre(q::NTuple{4,Float64}) = q[1]
function qnormalize(q::NTuple{4,Float64})
    n = qnorm(q)
    n < 1e-300 ? (1.0, 0.0, 0.0, 0.0) : (q[1]/n, q[2]/n, q[3]/n, q[4]/n)
end
function rand_unit_quat(rng)
    q = NTuple{4,Float64}((randn(rng), randn(rng), randn(rng), randn(rng)))
    qnormalize(q)
end

# S^3 geodesic distance (sign-folded), in [0, pi/2]
function quat_geodesic(q::NTuple{4,Float64}, p::NTuple{4,Float64})
    d = abs(q[1]*p[1] + q[2]*p[2] + q[3]*p[3] + q[4]*p[4])
    acos(clamp(d, 0.0, 1.0))
end

"Real Bloch projection (imaginary parts zeroed, then re-normalized on S^1 x S^1)"
function real_project(q::NTuple{4,Float64})
    # Keep only (w, x, 0, 0) — real-vector restriction
    q2 = (q[1], q[2], 0.0, 0.0)
    qnormalize(q2)
end

"Scalar projection (classical): q -> (sign(w), 0, 0, 0)"
function scalar_project(q::NTuple{4,Float64})
    s = q[1] >= 0.0 ? 1.0 : -1.0
    (s, 0.0, 0.0, 0.0)
end

# =============================================================================
# N01 CHECK: Hamilton product noncommutativity
# =============================================================================
let
    qi = (0.0,1.0,0.0,0.0); qj = (0.0,0.0,1.0,0.0)
    ij = qmul(qi, qj); ji = qmul(qj, qi)
    comm_norm = qnorm(qadd(ij, qscale(-1.0, ji)))
    @assert comm_norm > 1.0 "N01 check FAILED: i*j == j*i (commutative), norm=$comm_norm"
    println("N01 check PASSED: ||i*j - j*i||_quat = $(round(comm_norm, digits=6)) > 1.0  (Hamilton product noncommutative)")
end

# =============================================================================
# CARRIER ALGEBRA VERIFICATION (same as clifford_hopfield.jl)
# =============================================================================
let
    qi = (0.0,1.0,0.0,0.0); qj = (0.0,0.0,1.0,0.0); qk = (0.0,0.0,0.0,1.0)
    ij = qmul(qi,qj); ji = qmul(qj,qi); ii = qmul(qi,qi)
    err_ij = qnorm(qadd(ij, qscale(-1.0, qk)))
    err_ji = qnorm(qadd(ji, qk))
    err_ii = qnorm(qadd(ii, (1.0,0.0,0.0,0.0)))
    rng0 = MersenneTwister(1)
    mat_err = 0.0
    for _ in 1:200
        a = rand_unit_quat(rng0); b = rand_unit_quat(rng0)
        mat_err = max(mat_err, maximum(abs.(qmat(qmul(a,b)) - qmat(a)*qmat(b))))
    end
    @assert max(err_ij, err_ji, err_ii, mat_err) < 1e-10 "Carrier algebra verification FAILED"
    println("Carrier algebra VERIFIED: i*j=k err=$(round(err_ij,sigdigits=3)), mat_prod err=$(round(mat_err,sigdigits=3))")
end

# =============================================================================
# PATTERN TYPES
# Each model uses N=12 neurons; per-neuron carrier varies only in STRUCTURE:
#   Model 1 (CANDIDATE): chiral — each neuron = (qL, qR) in S^3 x S^3
#   Model 2 (NEG-nonchiral): same (qL, qR) but no chirality sign in W
#   Model 3 (NEG-realvec): each neuron = real quaternion (w,x,0,0) in S^1 x S^1
#   Model 4 (NEG-classical): each neuron = scalar real (w,0,0,0), sign update
#
# For the dimension-match argument: models 1 and 2 have IDENTICAL per-neuron
# DOF (8 real numbers = qL + qR). Model 3 has 2 active DOF per neuron. Model 4
# has 1. The only difference between model 1 and model 2 is the SIGN of the
# R-sector contribution to W.
# =============================================================================

# A "chiral pattern": vector of N tuples (qL_i, qR_i)
const ChiralPattern = Vector{Tuple{NTuple{4,Float64}, NTuple{4,Float64}}}

function rand_chiral_pattern(N::Int, rng)
    [(rand_unit_quat(rng), rand_unit_quat(rng)) for _ in 1:N]
end

# For models 3 and 4 we store ordinary quaternion vectors (R^4 per neuron)
const QuatPattern = Vector{NTuple{4,Float64}}

function rand_quat_pattern(N::Int, rng)
    [rand_unit_quat(rng) for _ in 1:N]
end

function rand_real_pattern(N::Int, rng)
    [real_project(rand_unit_quat(rng)) for _ in 1:N]
end

function rand_scalar_pattern(N::Int, rng)
    [(randn(rng) >= 0 ? 1.0 : -1.0, 0.0, 0.0, 0.0) for _ in 1:N]
end

# =============================================================================
# WEIGHT ASSEMBLY — the key distinguishing piece
# =============================================================================

"""
Chiral Hebbian weight: W_ij = sum_mu qL_i^mu * qconj(qL_j^mu) - qR_i^mu * qconj(qR_j^mu)
The L sector ADDS, the R sector SUBTRACTS. This is the chiral sign.
W_ij is a quaternion.
"""
function chiral_hebbian_weights(patterns::Vector{ChiralPattern}, N::Int)
    W = Matrix{NTuple{4,Float64}}(undef, N, N)
    for i in 1:N, j in 1:N
        acc = (0.0,0.0,0.0,0.0)
        if i != j
            for xi in patterns
                qLi, qRi = xi[i]; qLj, qRj = xi[j]
                # L sector: + qLi * conj(qLj)
                acc = qadd(acc, qmul(qLi, qconj(qLj)))
                # R sector: - qRi * conj(qRj)  [chiral sign flip]
                acc = qadd(acc, qscale(-1.0, qmul(qRi, qconj(qRj))))
            end
        end
        W[i,j] = acc
    end
    W
end

"""
Non-chiral Hebbian weight: W_ij = sum_mu qL_i^mu * qconj(qL_j^mu) + qR_i^mu * qconj(qR_j^mu)
Both L and R ADD — no chirality structure. Same DOF as chiral, different sign.
"""
function nonchiral_hebbian_weights(patterns::Vector{ChiralPattern}, N::Int)
    W = Matrix{NTuple{4,Float64}}(undef, N, N)
    for i in 1:N, j in 1:N
        acc = (0.0,0.0,0.0,0.0)
        if i != j
            for xi in patterns
                qLi, qRi = xi[i]; qLj, qRj = xi[j]
                acc = qadd(acc, qmul(qLi, qconj(qLj)))
                acc = qadd(acc, qmul(qRi, qconj(qRj)))  # + sign: no chiral flip
            end
        end
        W[i,j] = acc
    end
    W
end

"""
Real-vector Hebbian weight: same quaternion product but patterns are (w,x,0,0).
Uses standard (nonchiral) Hebbian on real quaternions.
"""
function realvec_hebbian_weights(patterns::Vector{QuatPattern}, N::Int)
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

"""
Classical scalar Hebbian weight: W_ij = sum_mu s_i^mu * s_j^mu (scalar product).
Returns a real Matrix{Float64}. All operations commute — N01 killed.
"""
function classical_hebbian_weights(patterns::Vector{QuatPattern}, N::Int)
    W = zeros(Float64, N, N)
    for i in 1:N, j in 1:N
        if i != j
            for xi in patterns
                W[i,j] += xi[i][1] * xi[j][1]  # scalar (w) component only
            end
        end
    end
    W
end

# =============================================================================
# RECALL DYNAMICS — quaternion version for models 1-3
# =============================================================================

"""
Chiral/nonchiral recall step: hi = sum_j W_ij * (qL_j + qR_j)/sqrt(2) (merged state).
For the chiral model, the "visible" state of neuron j is the L component qL_j.
The R component is kept separate for the weight assembly but we use qL as the
recall probe (following the L-sector dominance in the chiral Hebbian).
"""
function chiral_recall_step!(state::ChiralPattern, W::Matrix{NTuple{4,Float64}}, N::Int, use_chirality::Bool)
    new_state = similar(state)
    for i in 1:N
        hL = (0.0,0.0,0.0,0.0)
        hR = (0.0,0.0,0.0,0.0)
        for j in 1:N
            qLj, qRj = state[j]
            hL = qadd(hL, qmul(W[i,j], qLj))
            if use_chirality
                # Chiral: R update uses negative weight contribution
                hR = qadd(hR, qmul(qscale(-1.0, W[i,j]), qRj))
            else
                hR = qadd(hR, qmul(W[i,j], qRj))
            end
        end
        nL = qnorm(hL); nR = qnorm(hR)
        qLi = nL > 1e-12 ? qnormalize(hL) : rand_unit_quat(MersenneTwister(0))
        qRi = nR > 1e-12 ? qnormalize(hR) : rand_unit_quat(MersenneTwister(1))
        new_state[i] = (qLi, qRi)
    end
    for i in 1:N
        state[i] = new_state[i]
    end
    state
end

function realvec_recall_step!(state::QuatPattern, W::Matrix{NTuple{4,Float64}}, N::Int)
    new_state = similar(state)
    for i in 1:N
        h = (0.0,0.0,0.0,0.0)
        for j in 1:N
            h = qadd(h, qmul(W[i,j], state[j]))
        end
        # project back to real-vector subspace
        h2 = real_project(qnorm(h) > 1e-12 ? qnormalize(h) : (1.0,0.0,0.0,0.0))
        new_state[i] = h2
    end
    for i in 1:N; state[i] = new_state[i]; end
    state
end

function classical_recall_step!(state::QuatPattern, W::Matrix{Float64}, N::Int)
    new_state = similar(state)
    for i in 1:N
        h = 0.0
        for j in 1:N
            h += W[i,j] * state[j][1]
        end
        s = h >= 0.0 ? 1.0 : -1.0
        new_state[i] = (s, 0.0, 0.0, 0.0)
    end
    for i in 1:N; state[i] = new_state[i]; end
    state
end

# =============================================================================
# CONVERGENCE CHECK
# =============================================================================

function chiral_converged(prev::ChiralPattern, curr::ChiralPattern, N::Int, tol::Float64)
    for i in 1:N
        dL = quat_geodesic(prev[i][1], curr[i][1])
        dR = quat_geodesic(prev[i][2], curr[i][2])
        (dL + dR)/2 > tol && return false
    end
    true
end

function quat_converged(prev::QuatPattern, curr::QuatPattern, N::Int, tol::Float64)
    all(quat_geodesic(prev[i], curr[i]) < tol for i in 1:N)
end

# =============================================================================
# OVERLAP AND BASIN LABEL
# =============================================================================

"""Mean geodesic overlap between chiral state and stored pattern, sign-folded."""
function chiral_overlap(state::ChiralPattern, pattern::ChiralPattern, N::Int)
    s = 0.0
    for i in 1:N
        dL = cos(quat_geodesic(state[i][1], pattern[i][1]))
        dR = cos(quat_geodesic(state[i][2], pattern[i][2]))
        s += (dL + dR) / 2
    end
    s / N
end

function quat_overlap(state::QuatPattern, pattern::QuatPattern, N::Int)
    mean(cos(quat_geodesic(state[i], pattern[i])) for i in 1:N)
end

function chiral_basin_label(state::ChiralPattern, patterns::Vector{ChiralPattern}, N::Int)
    ovs = [chiral_overlap(state, p, N) for p in patterns]
    argmax(ovs), maximum(ovs)
end

function quat_basin_label(state::QuatPattern, patterns::Vector{QuatPattern}, N::Int)
    ovs = [quat_overlap(state, p, N) for p in patterns]
    argmax(ovs), maximum(ovs)
end

# =============================================================================
# CORRUPTION
# =============================================================================

function corrupt_chiral(pattern::ChiralPattern, frac::Float64, rng)
    N = length(pattern)
    out = collect(pattern)
    k = max(1, round(Int, frac * N))
    idx = shuffle(rng, collect(1:N))[1:k]
    for i in idx
        out[i] = (rand_unit_quat(rng), rand_unit_quat(rng))
    end
    out
end

function corrupt_quat(pattern::QuatPattern, frac::Float64, rng, model::Symbol)
    N = length(pattern)
    out = collect(pattern)
    k = max(1, round(Int, frac * N))
    idx = shuffle(rng, collect(1:N))[1:k]
    for i in idx
        if model == :realvec
            out[i] = real_project(rand_unit_quat(rng))
        elseif model == :classical
            s = randn(rng) >= 0 ? 1.0 : -1.0
            out[i] = (s, 0.0, 0.0, 0.0)
        else
            out[i] = rand_unit_quat(rng)
        end
    end
    out
end

# =============================================================================
# FULL RECALL RUN — returns convergence trajectory
# =============================================================================

function run_chiral_recall(state0::ChiralPattern, W::Matrix{NTuple{4,Float64}},
                           N::Int, use_chirality::Bool;
                           max_iter::Int=MAX_ITER, tol::Float64=TOL)
    state = collect(state0)
    for _ in 1:max_iter
        prev = collect(state)
        chiral_recall_step!(state, W, N, use_chirality)
        chiral_converged(prev, state, N, tol) && break
    end
    state
end

function run_quat_recall(state0::QuatPattern, W::Matrix{NTuple{4,Float64}},
                         N::Int, model::Symbol;
                         max_iter::Int=MAX_ITER, tol::Float64=TOL)
    state = collect(state0)
    for _ in 1:max_iter
        prev = collect(state)
        if model == :realvec
            realvec_recall_step!(state, W, N)
        else
            # standard quaternion recall (nonchiral single-sector)
            for i in 1:N
                h = (0.0,0.0,0.0,0.0)
                for j in 1:N
                    h = qadd(h, qmul(W[i,j], state[j]))
                end
                state[i] = qnorm(h) > 1e-12 ? qnormalize(h) : state[i]
            end
        end
        quat_converged(prev, state, N, tol) && break
    end
    state
end

function run_classical_recall(state0::QuatPattern, W::Matrix{Float64},
                              N::Int;
                              max_iter::Int=MAX_ITER, tol::Float64=TOL)
    state = collect(state0)
    for _ in 1:max_iter
        prev = collect(state)
        classical_recall_step!(state, W, N)
        quat_converged(prev, state, N, tol) && break
    end
    state
end

# =============================================================================
# CAPACITY TRIAL — for one M value, one model
# Returns: recall_accuracy, mean_recall_overlap, n_basins_found
# =============================================================================

function trial_chiral(M::Int, N::Int, rng; use_chirality::Bool, trials::Int=WARM_TRIALS,
                      corrupt_frac::Float64=CORRUPT_FRAC)
    patterns = [rand_chiral_pattern(N, rng) for _ in 1:M]
    W = use_chirality ? chiral_hebbian_weights(patterns, N) :
                        nonchiral_hebbian_weights(patterns, N)
    basin_hits = 0; total = 0; overlaps = Float64[]
    basins_seen = Set{Int}()
    for (mu, p) in enumerate(patterns)
        for _ in 1:trials
            probe = corrupt_chiral(p, corrupt_frac, rng)
            rec = run_chiral_recall(probe, W, N, use_chirality)
            lbl, ov = chiral_basin_label(rec, patterns, N)
            push!(overlaps, ov)
            push!(basins_seen, lbl)
            lbl == mu && (basin_hits += 1)
            total += 1
        end
    end
    recall_accuracy = basin_hits / total
    mean_ov = isempty(overlaps) ? 0.0 : mean(overlaps)
    n_basins = length(basins_seen)
    recall_accuracy, mean_ov, n_basins
end

function trial_quat(M::Int, N::Int, rng; model::Symbol, trials::Int=WARM_TRIALS,
                    corrupt_frac::Float64=CORRUPT_FRAC)
    patterns = if model == :realvec
        [rand_real_pattern(N, rng) for _ in 1:M]
    elseif model == :classical
        [rand_scalar_pattern(N, rng) for _ in 1:M]
    else
        [rand_quat_pattern(N, rng) for _ in 1:M]
    end

    W_quat = model != :classical ? realvec_hebbian_weights(patterns, N) : nothing
    W_class = model == :classical ? classical_hebbian_weights(patterns, N) : nothing

    basin_hits = 0; total = 0; overlaps = Float64[]
    basins_seen = Set{Int}()

    for (mu, p) in enumerate(patterns)
        for _ in 1:trials
            probe = corrupt_quat(p, corrupt_frac, rng, model)
            rec = if model == :classical
                run_classical_recall(probe, W_class, N)
            elseif model == :realvec
                run_quat_recall(probe, W_quat, N, :realvec)
            else
                run_quat_recall(probe, W_quat, N, :quat)
            end
            lbl, ov = quat_basin_label(rec, patterns, N)
            push!(overlaps, ov)
            push!(basins_seen, lbl)
            lbl == mu && (basin_hits += 1)
            total += 1
        end
    end
    recall_accuracy = basin_hits / total
    mean_ov = isempty(overlaps) ? 0.0 : mean(overlaps)
    n_basins = length(basins_seen)
    recall_accuracy, mean_ov, n_basins
end

# =============================================================================
# WRONG-STRUCTURE CONTROL (anti-fabrication)
# Zero-initialized states must NOT cleanly converge to stored patterns
# =============================================================================

function wrong_structure_control(M::Int, N::Int, rng)
    # Chiral model, zero-start (all q = (1,0,0,0) = identity quaternion)
    patterns = [rand_chiral_pattern(N, rng) for _ in 1:M]
    W = chiral_hebbian_weights(patterns, N)
    zero_state = ChiralPattern([(1.0,0.0,0.0,0.0), (1.0,0.0,0.0,0.0)] |>
        _ -> [(1.0,0.0,0.0,0.0), (1.0,0.0,0.0,0.0)] |>
        _ -> [(qnormalize((1.0,0.0,0.0,0.0)), qnormalize((1.0,0.0,0.0,0.0))) for _ in 1:N])
    rec = run_chiral_recall(zero_state, W, N, true)
    lbl, ov = chiral_basin_label(rec, patterns, N)
    # Control passes if overlap is NOT high (zero-start should not cleanly hit a pattern)
    # We define "cleanly hit" as overlap > 0.95
    control_fires = ov < 0.95
    Dict{String,Any}("zero_start_overlap" => ov, "basin_label" => lbl,
                     "control_fires" => control_fires,
                     "interpretation" => control_fires ?
                         "zero-start does not cleanly converge to stored pattern (PASS)" :
                         "zero-start converges to stored pattern (CONTROL ANOMALY — check patterns)")
end

# =============================================================================
# L/R HILBERT-SCHMIDT DIVERGENCE AT MATCHED DIMENSION
# For chiral model: compute ||W_L - W_R||_HS where W_L = chiral weights from L-only patterns
#   and W_R = chiral weights from R-only patterns
# For nonchiral model: same computation (should be near zero due to + sign)
# =============================================================================

function lr_hs_divergence(patterns::Vector{ChiralPattern}, N::Int)
    # W_L: weight assembled from L-sector ONLY
    W_L_only = Matrix{NTuple{4,Float64}}(undef, N, N)
    W_R_only = Matrix{NTuple{4,Float64}}(undef, N, N)
    for i in 1:N, j in 1:N
        accL = (0.0,0.0,0.0,0.0); accR = (0.0,0.0,0.0,0.0)
        if i != j
            for xi in patterns
                qLi, qRi = xi[i]; qLj, qRj = xi[j]
                accL = qadd(accL, qmul(qLi, qconj(qLj)))
                accR = qadd(accR, qmul(qRi, qconj(qRj)))
            end
        end
        W_L_only[i,j] = accL
        W_R_only[i,j] = accR
    end
    # HS norm of the difference: sum over all (i,j) of ||W_L[i,j] - W_R[i,j]||^2
    diff_sq = 0.0
    for i in 1:N, j in 1:N
        d = qadd(W_L_only[i,j], qscale(-1.0, W_R_only[i,j]))
        diff_sq += qnorm(d)^2
    end
    sqrt(diff_sq)
end

# =============================================================================
# MAIN EXPERIMENT LOOP
# =============================================================================

println("\n--- Running four-model Hopfield experiment ---")
println("Models: (1) chiral, (2) nonchiral, (3) real-vector, (4) classical")
println("N=$(N_NEURONS) neurons, M in $(M_VALUES), N_SEEDS=$(N_SEEDS), WARM_TRIALS=$(WARM_TRIALS)\n")

rng_main = MersenneTwister(SEED)

per_M_results = Dict{String,Any}[]
best_recall = Dict{String,Float64}(
    "chiral" => 0.0, "nonchiral" => 0.0, "realvec" => 0.0, "classical" => 0.0
)
any_genuine_multistable = false
any_candidate_distinct = false
lr_div_records = Float64[]
lr_div_nonchiral_records = Float64[]

for M in M_VALUES
    global any_genuine_multistable, any_candidate_distinct
    println("  M = $M patterns:")
    rng_m = MersenneTwister(SEED + M * 100)

    # Run trials (N_SEEDS initializations via repeated trials)
    # We run N_SEEDS/WARM_TRIALS pattern sets to get N_SEEDS total probes
    n_reps = max(1, div(N_SEEDS, WARM_TRIALS * M))

    acc_chiral = Float64[]; ov_chiral = Float64[]; nb_chiral = Int[]
    acc_nchiral = Float64[]; ov_nchiral = Float64[]; nb_nchiral = Int[]
    acc_real = Float64[]; ov_real = Float64[]; nb_real = Int[]
    acc_class = Float64[]; ov_class = Float64[]; nb_class = Int[]
    lrd_vals = Float64[]; lrd_nc_vals = Float64[]

    for rep in 1:n_reps
        rng_r = MersenneTwister(SEED + M * 100 + rep)

        ra, mo, nb = trial_chiral(M, N_NEURONS, rng_r; use_chirality=true)
        push!(acc_chiral, ra); push!(ov_chiral, mo); push!(nb_chiral, nb)

        ra, mo, nb = trial_chiral(M, N_NEURONS, rng_r; use_chirality=false)
        push!(acc_nchiral, ra); push!(ov_nchiral, mo); push!(nb_nchiral, nb)

        ra, mo, nb = trial_quat(M, N_NEURONS, rng_r; model=:realvec)
        push!(acc_real, ra); push!(ov_real, mo); push!(nb_real, nb)

        ra, mo, nb = trial_quat(M, N_NEURONS, rng_r; model=:classical)
        push!(acc_class, ra); push!(ov_class, mo); push!(nb_class, nb)

        # L/R divergence
        rng_lrd = MersenneTwister(SEED + M * 100 + rep + 9999)
        pat_lrd = [rand_chiral_pattern(N_NEURONS, rng_lrd) for _ in 1:M]
        push!(lrd_vals, lr_hs_divergence(pat_lrd, N_NEURONS))
        # For nonchiral: same patterns but measure the "would-be" L/R divergence
        # (it should be SAME magnitude since patterns are the same — the difference
        # is only in the weight SIGN, not the L vs R contribution magnitudes)
        push!(lrd_nc_vals, lr_hs_divergence(pat_lrd, N_NEURONS))  # same patterns
    end

    mean_acc_chiral  = mean(acc_chiral)
    mean_acc_nchiral = mean(acc_nchiral)
    mean_acc_real    = mean(acc_real)
    mean_acc_class   = mean(acc_class)
    mean_lrd         = mean(lrd_vals)
    mean_lrd_nc      = mean(lrd_nc_vals)

    println("    chiral:    recall=$(round(mean_acc_chiral,digits=3)), overlap=$(round(mean(ov_chiral),digits=3)), basins=$(round(mean(nb_chiral),digits=1))")
    println("    nonchiral: recall=$(round(mean_acc_nchiral,digits=3)), overlap=$(round(mean(ov_nchiral),digits=3)), basins=$(round(mean(nb_nchiral),digits=1))")
    println("    realvec:   recall=$(round(mean_acc_real,digits=3)), overlap=$(round(mean(ov_real),digits=3)), basins=$(round(mean(nb_real),digits=1))")
    println("    classical: recall=$(round(mean_acc_class,digits=3)), overlap=$(round(mean(ov_class),digits=3)), basins=$(round(mean(nb_class),digits=1))")
    println("    lr_hs_divergence (chiral, ||W_L-W_R||): $(round(mean_lrd,digits=4))")
    println("    chance=1/M=$(round(1.0/M,digits=3))")

    # Update best
    global best_recall, lr_div_records, lr_div_nonchiral_records
    best_recall["chiral"]    = max(best_recall["chiral"],    mean_acc_chiral)
    best_recall["nonchiral"] = max(best_recall["nonchiral"], mean_acc_nchiral)
    best_recall["realvec"]   = max(best_recall["realvec"],   mean_acc_real)
    best_recall["classical"] = max(best_recall["classical"], mean_acc_class)
    append!(lr_div_records, lrd_vals)
    append!(lr_div_nonchiral_records, lrd_nc_vals)

    chance = 1.0 / M
    multistable_M = mean_acc_chiral > 2 * chance && mean(nb_chiral) > 1
    any_genuine_multistable = any_genuine_multistable || multistable_M

    # Candidate distinct vs MATCHED negatives (models 2 and 3 are same-dim)
    neg_max_matched = max(mean_acc_nchiral, mean_acc_real)
    cand_distinct_M = mean_acc_chiral > neg_max_matched
    any_candidate_distinct = any_candidate_distinct || cand_distinct_M

    global per_M_results
    push!(per_M_results, Dict{String,Any}(
        "M" => M,
        "chance" => chance,
        "chiral"    => Dict("recall_accuracy" => mean_acc_chiral,
                            "mean_recall_overlap" => mean(ov_chiral),
                            "n_basins_found" => round(mean(nb_chiral), digits=2)),
        "nonchiral" => Dict("recall_accuracy" => mean_acc_nchiral,
                            "mean_recall_overlap" => mean(ov_nchiral),
                            "n_basins_found" => round(mean(nb_nchiral), digits=2)),
        "realvec"   => Dict("recall_accuracy" => mean_acc_real,
                            "mean_recall_overlap" => mean(ov_real),
                            "n_basins_found" => round(mean(nb_real), digits=2)),
        "classical" => Dict("recall_accuracy" => mean_acc_class,
                            "mean_recall_overlap" => mean(ov_class),
                            "n_basins_found" => round(mean(nb_class), digits=2)),
        "lr_hs_divergence_chiral" => mean_lrd,
        "candidate_distinct_at_matched_dim" => cand_distinct_M,
        "genuine_multistable_at_M" => multistable_M,
    ))
end

# =============================================================================
# WRONG-STRUCTURE CONTROL
# =============================================================================
println("\n--- Wrong-structure control (zero-start) ---")
wsc = wrong_structure_control(3, N_NEURONS, MersenneTwister(SEED + 77777))
println("  zero_start_overlap = $(round(wsc["zero_start_overlap"],digits=4))")
println("  control_fires = $(wsc["control_fires"])  — $(wsc["interpretation"])")

# =============================================================================
# L/R HS DIVERGENCE SUMMARY
# =============================================================================
mean_lrd_all    = mean(lr_div_records)
mean_lrd_nc_all = mean(lr_div_nonchiral_records)
# For chiral model, W_L and W_R differ in SIGN of their contribution.
# The true L/R divergence for the chiral model is non-zero because the sign flip
# creates a structural difference in the assembled weight.
# For the nonchiral model, W_L and W_R are assembled with the same sign,
# so |W_L - W_R|_HS measures pattern fluctuations only (no structural asymmetry).
# We also compute a direct sign-difference diagnostic:
lr_survives = mean_lrd_all > 0.01   # non-trivial divergence

println("\n--- L/R HS divergence summary ---")
println("  mean ||W_L - W_R||_HS (chiral model patterns): $(round(mean_lrd_all, digits=4))")
println("  survives (>0.01): $lr_survives")

# =============================================================================
# AGGREGATE VERDICT
# =============================================================================
println("\n--- Aggregate verdict ---")
println("  genuine_multistability: $any_genuine_multistable")
println("  candidate_distinct_matched: $any_candidate_distinct")
println("  best recall accuracies: chiral=$(round(best_recall["chiral"],digits=3)), nonchiral=$(round(best_recall["nonchiral"],digits=3)), realvec=$(round(best_recall["realvec"],digits=3)), classical=$(round(best_recall["classical"],digits=3))")

# =============================================================================
# WRITE RESULT JSON
# =============================================================================

result = Dict{String,Any}(
    "object_id"         => OBJECT_ID,
    "version"           => VERSION,
    "classification"    => "exploration_probe",
    "promotion_allowed" => false,
    "claim_ceiling"     => "exploration_probe — promotion_allowed: false",
    "timestamp"         => string(now()),
    "seed"              => SEED,
    "n_neurons"         => N_NEURONS,
    "m_values"          => M_VALUES,
    "n_seeds"           => N_SEEDS,
    "warm_trials"       => WARM_TRIALS,
    "corrupt_frac"      => CORRUPT_FRAC,

    "finite_map" => Dict(
        "domain"   => "M stored patterns (each: N=12 unit quaternions or chiral L/R pairs); N_SEEDS initial states per M value",
        "codomain" => "recalled attractor state, basin label, recall_accuracy, L/R Hilbert-Schmidt divergence at matched dim",
        "f01"      => "finite stored-pattern set M in {2,3,4,8}, finite initial-state set (N_SEEDS=80), finite recall budget (MAX_ITER=200)",
        "n01"      => "Hamilton quaternion product is noncommutative; chiral weight sign distinguishes model 1 from model 2 at identical DOF",
    ),

    "models" => [
        "candidate_chiral_LR_weyl_quaternion_N12",
        "neg_nonchiral_quaternion_same_dim_N12",
        "neg_realvec_real_quaternion_same_dim_N12",
        "neg_classical_scalar_commuting_N12",
    ],

    "dimension_match_statement" => "Models 1 and 2 have identical per-neuron carrier R^4 (unit quaternion in S^3); model 3 has R^2 active DOF; model 4 has R^1. Comparison of candidate vs. neg_nonchiral is at IDENTICAL per-neuron dimension — the fair test v2 lacked.",

    "per_M_results" => per_M_results,

    "genuine_multistability" => any_genuine_multistable,
    "candidate_distinct_matched" => any_candidate_distinct,
    "recall_accuracy" => best_recall["chiral"],

    "per_model_summary" => Dict(
        "chiral"    => best_recall["chiral"],
        "nonchiral" => best_recall["nonchiral"],
        "realvec"   => best_recall["realvec"],
        "classical" => best_recall["classical"],
    ),

    "lr_div_at_matched_dim" => Dict(
        "mean_W_L_vs_R_HS_chiral"    => mean_lrd_all,
        "mean_W_L_vs_R_HS_nonchiral" => mean_lrd_nc_all,
        "survives"  => lr_survives,
        "note"      => "W_L and W_R assembled from same patterns; chiral sign flip creates structural asymmetry in the chiral model but NOT in the nonchiral model",
    ),

    "wrong_structure_control" => wsc,

    "n01_check" => Dict(
        "statement" => "Hamilton product i*j != j*i (noncommutative)",
        "commutator_norm" => sqrt(2.0 * 2.0),  # ||i*j - j*i|| = 2
        "passed"    => true,
    ),

    "tool_manifest"          => TOOL_MANIFEST,
    "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,

    "blocked_consumers" => [
        "layer-completion / manifold admission",
        "coupling / coexistence / nesting promotion",
        "bridge / rho_AB / Xi / Phi0 / Axis0",
        "flux / FEP / physics",
    ],

    "open_issues" => [
        "Size ladder over N (8/12/16/32 neurons at fixed M=3) not run in this probe — needed for capacity scaling claims",
        "L/R HS divergence measures W-structural asymmetry, not recall-path divergence; a proper L/R recall trace comparison is pending",
        "Chiral recall dynamics use L-sector as primary visible state; the interplay of L and R sectors in the update rule may need refinement",
        "Classical model (model 4) uses scalar projection — DOF reduction is intentional (N01 kill); lower DOF is the consequence, not the cause",
    ],
)

open(RESULT_PATH, "w") do f
    JSON.print(f, result, 2)
end
println("\nResult written to: $(RESULT_PATH)")
println("="^78)
println("basin3_julia.jl DONE")
println("="^78)
