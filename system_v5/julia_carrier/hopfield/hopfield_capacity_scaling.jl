#!/usr/bin/env julia
# =============================================================================
# hopfield_capacity_scaling.jl  —  CAPACITY LIFTS + N-SCALING for the
#   quaternionic Clifford-Hopfield associative memory.
#   object_id          = hopfield_capacity_scaling
#   classification     = hopfield_capacity_poc
#   promotion_allowed  = false
#   sim_execution_kind = nonclassical (geometric-algebra carrier; Cl(3,0)+ only, NO Bloch)
#
# JULIA side of a dual-engine build. This file REUSES the genuine quaternion
# carrier + recall machinery of clifford_hopfield.jl VERBATIM (qmul, qconj,
# qnormalize, hebbian_weights, recall, recall_overlap, basin_label, corrupt,
# the classical Euclidean-dot control, and the order-dependent-basin probe). It
# adds TWO capacity lifts + ONE N-scaling check. It does NOT modify the parent
# object or its artifacts.
#
# -----------------------------------------------------------------------------
# CLAIM CEILING (hard)
#   This object COMPUTES finite invariants on a Clifford carrier:
#     (i)   capacity (max_reliable_M) under a PSEUDO-INVERSE / projection weight
#           rule vs the Hebbian rule, for BOTH the quaternion carrier and the
#           Euclidean-dot classical control, at N=12;
#     (ii)  the N-scaling of capacity: N in {12,24,48}, max_reliable_M for
#           quaternion vs classical, and the quaternion/classical capacity RATIO;
#     (iii) the parent's order-dependent-basin + geometric-vs-classical controls,
#           kept so the carrier stays honest.
#   It does NOT assert layer-completion, manifold admission, coupling, bridge
#   (rho_AB / Xi / Phi0 / Axis0), flux, FEP, or physics. A pattern recovered here
#   is a CANDIDATE attractor survivor, not a proven object. promotion_allowed=false.
#
# -----------------------------------------------------------------------------
# THE TWO LIFTS + ONE SCALING (decisive questions)
#   LIFT 1 (pseudo-inverse / projection weights): replace the Hebbian outer-sum
#     with the projection rule W = Xi (Xi^H Xi)^-1 Xi^H over the stored patterns
#     (Personnaz / Kanter-Sompolinsky), carried genuinely on the quaternion
#     algebra via the SU(2) 2x2 matrix realization of each quaternion. Does
#     max_reliable_M rise above 1 at N=12? Reported for pseudo-inverse vs Hebbian,
#     BOTH quaternion and classical.
#   SCALING (the Feynman check): for N in {12,24,48}, max_reliable_M for
#     quaternion vs classical under the STRICT bar (mean recall overlap >= 0.95
#     AND basin-correct fraction >= 0.90, averaged over >= 10 corrupt-recall
#     trials/pattern at 30% corruption). DECISIVE: does the quaternion capacity
#     stay STRICTLY BELOW the classical one as N grows (-> "geometric product is
#     more constraining" survives as structural), or do they CONVERGE (-> the
#     gap was a small-N artifact)? Reported as the quaternion/classical capacity
#     RATIO vs N. Real numbers, brutally honest, whichever way they land.
#
# NO SMUGGLING: the pass-criteria (strict reliable bar) are the SAME ones the
# parent already published; they are not authored fresh to flatter this object.
# The pseudo-inverse rule is a textbook capacity-lift rule, not a tuned knob; if
# it does not lift, the run says so. The geometric-vs-classical and order-basin
# controls are kept VERBATIM so a wrong (erased/flat) structure still flips them.
#
# RUN: julia --project="system_v5/julia_carrier" \
#        "system_v5/julia_carrier/hopfield/hopfield_capacity_scaling.jl"
# =============================================================================

using LinearAlgebra
using Random
using Statistics
import JSON

const OBJECT_ID      = "hopfield_capacity_scaling"
const CLASSIFICATION = "hopfield_capacity_poc"
const HERE           = @__DIR__
const RESULT_PATH    = joinpath(HERE, "hopfield_capacity_scaling_results.json")
const SEED           = 20260602

# =============================================================================
# QUATERNION CARRIER (reused VERBATIM from clifford_hopfield.jl)
# Cl(3,0)+ realized on 2x2 SU(2). A quaternion is q = (w,x,y,z). Its matrix
# realization Q = w*I - i(x sx + y sy + z sz). Dynamics run on the 4-tuple
# Hamilton product; the matrix form is used to VERIFY the algebra AND to carry
# the pseudo-inverse (genuine 2x2-complex-block linear algebra over H).
# =============================================================================

const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const I2 = ComplexF64[1 0; 0 1]

qmat(q) = q[1]*I2 - im*(q[2]*SX + q[3]*SY + q[4]*SZ)

"Inverse map: a 2x2 SU(2)-form complex matrix -> quaternion 4-tuple.
 For Q = w*I - i(x sx + y sy + z sz):
   w = real(Q[1,1]);  z = -imag(Q[1,1]);  y = -real(Q[1,2]);  x = -imag(Q[1,2])."
function mat2quat(Q)
    w =  real(Q[1,1])
    z = -imag(Q[1,1])
    y = -real(Q[1,2])
    x = -imag(Q[1,2])
    (w, x, y, z)
end

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

"VERIFY the carrier algebra against the SU(2) matrix realization (0.0 target).
 ALSO verify the inverse map mat2quat(qmat(q))==q (round-trip), needed because the
 pseudo-inverse lift round-trips through the matrix representation."
function verify_quaternion_carrier()
    qi = (0.0,1.0,0.0,0.0); qj = (0.0,0.0,1.0,0.0); qk = (0.0,0.0,0.0,1.0)
    ij = qmul(qi, qj); ji = qmul(qj, qi); ii = qmul(qi, qi)
    err_ij = qnorm(qadd(ij, qscale(-1.0, qk)))
    err_ji = qnorm(qadd(ji, qk))
    err_ii = qnorm(qadd(ii, (1.0,0.0,0.0,0.0)))
    rng = MersenneTwister(1)
    mat_err = 0.0
    rt_err  = 0.0
    for _ in 1:200
        a = rand_unit_quat(rng); b = rand_unit_quat(rng)
        mat_err = max(mat_err, maximum(abs.(qmat(qmul(a,b)) - qmat(a)*qmat(b))))
        rt_err  = max(rt_err, qnorm(qadd(mat2quat(qmat(a)), qscale(-1.0, a))))
    end
    pauli_anticomm = maximum(abs.(SX*SY + SY*SX))
    pauli_square   = maximum(abs.(SX*SX - I2))
    Dict{String,Any}(
        "i_times_j_eq_k_err" => err_ij,
        "j_times_i_eq_minus_k_err" => err_ji,
        "i_squared_eq_minus_one_err" => err_ii,
        "hamilton_product_eq_matrix_product_maxerr" => mat_err,
        "mat2quat_roundtrip_maxerr" => rt_err,
        "pauli_anticommutator_sx_sy" => pauli_anticomm,
        "pauli_square_sx" => pauli_square,
        "noncommutative_ij_ne_ji" => err_ij < 1e-12 && qnorm(qadd(ij, qscale(-1.0,ji))) > 1.0,
        "carrier_verified" => max(err_ij,err_ji,err_ii,mat_err,rt_err,pauli_anticomm,pauli_square) < 1e-10,
    )
end

# =============================================================================
# QUATERNIONIC HOPFIELD NETWORK (recall machinery reused VERBATIM)
# =============================================================================

"HEBBIAN quaternion weight tensor (parent rule). W[i,j] = sum_mu xi_i (x) conj(xi_j)."
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

"One async sweep in DETERMINISTIC cyclic order (1..N). xi_i <- normalize(sum_j W_ij xi_j)."
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

"Run async dynamics to convergence (pure function of (state0, W))."
function recall(state0, W, N::Int; max_sweeps=200, tol=1e-10)
    state = collect(state0)
    sweeps = 0
    for s in 1:max_sweeps
        prev = copy(state)
        async_sweep!(state, W, N)
        sweeps = s
        moved = maximum(quat_geodesic(prev[i], state[i]) for i in 1:N)
        moved < tol && break
    end
    state, sweeps
end

"Recall overlap: mean cos-similarity (sign-folded), in [0,1] (1 = identical up to global S^3 sign)."
function recall_overlap(recovered, target, N::Int)
    s = 0.0
    for i in 1:N
        d = recovered[i][1]*target[i][1] + recovered[i][2]*target[i][2] +
            recovered[i][3]*target[i][3] + recovered[i][4]*target[i][4]
        s += abs(d)
    end
    s / N
end

config_distance(a, b, N::Int) = mean(quat_geodesic(a[i], b[i]) for i in 1:N)

function basin_label(recovered, patterns, N::Int)
    dists = [config_distance(recovered, p, N) for p in patterns]
    argmin(dists), minimum(dists)
end

"Corrupt a pattern: replace ~frac of neurons with fresh random unit quaternions."
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

random_patterns(M::Int, N::Int, rng) = [[rand_unit_quat(rng) for _ in 1:N] for _ in 1:M]

# =============================================================================
# LIFT 1 -- PSEUDO-INVERSE / PROJECTION WEIGHTS (the capacity-lift rule)
#
#   Real Hopfield projection rule (Personnaz / Kanter-Sompolinsky):
#       W = X (X^T X)^-1 X^T      (X = patterns as columns)
#   It makes every stored pattern an EXACT fixed point and is known to lift
#   capacity above the Hebbian ~0.14 N rule. We carry it on BOTH arms:
#
#   QUATERNION ARM: each neuron carries a unit quaternion = a 2x2 SU(2) block.
#     Build the N x M block matrix Xi whose (i,mu) block is qmat(xi^mu_i)
#     (2N x 2M complex). The projection weight is the 2N x 2N complex matrix
#         P = Xi * pinv(Xi)              ( = Xi (Xi^H Xi)^-1 Xi^H )
#     Read off W[i,j] as the quaternion of the (i,j) 2x2 block of P (mat2quat),
#     diag zeroed. The local field h_i = sum_j qmul(W[i,j], xi_j); update as in
#     the parent. The geometric (Hamilton) product is preserved in the update,
#     so this is the SAME carrier with a different (projection) weight rule.
#
#   CLASSICAL ARM: flatten each unit quaternion to R^4. X is 4N x M real; the
#     real projection weight is W_real = X * pinv(X) (4N x 4N), per-neuron 4x4
#     diagonal blocks zeroed; update v <- W_real v then renormalize to S^3.
#
#   pinv uses LinearAlgebra.pinv (SVD-based; tolerant to rank deficiency). For
#   M <= dimension this is the exact projector onto span(patterns).
# =============================================================================

"Quaternion projection (pseudo-inverse) weight tensor.
 Xi (2N x 2M complex) blocks = qmat(xi^mu_i); P = Xi*pinv(Xi); W[i,j]=mat2quat(P block), diag 0."
function projection_weights_quat(patterns, N::Int)
    M = length(patterns)
    Xi = zeros(ComplexF64, 2N, 2M)
    for mu in 1:M, i in 1:N
        Xi[(2i-1):(2i), (2mu-1):(2mu)] = qmat(patterns[mu][i])
    end
    P = Xi * pinv(Xi)                       # 2N x 2N projector onto column span
    W = Matrix{NTuple{4,Float64}}(undef, N, N)
    for i in 1:N, j in 1:N
        if i == j
            W[i,j] = (0.0,0.0,0.0,0.0)
        else
            blk = P[(2i-1):(2i), (2j-1):(2j)]
            W[i,j] = mat2quat(blk)
        end
    end
    W
end

# Classical (Euclidean-dot) machinery -- reused VERBATIM from the parent control.
flatten4N(cfg) = reduce(vcat, [collect(q) for q in cfg])
function unflatten4N(v, N)
    [qnormalize((v[4i-3], v[4i-2], v[4i-1], v[4i])) for i in 1:N]
end

"Classical HEBBIAN weights (parent control rule): W_real = sum_mu v v^T, diag blocks 0."
function classical_hebbian_weights(patterns, N::Int)
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

"Classical PROJECTION (pseudo-inverse) weights: W_real = X*pinv(X), diag blocks 0."
function classical_projection_weights(patterns, N::Int)
    M = length(patterns)
    X = zeros(Float64, 4N, M)
    for mu in 1:M
        X[:, mu] = flatten4N(patterns[mu])
    end
    W = X * pinv(X)
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

# =============================================================================
# CAPACITY TRIAL (strict bar reused VERBATIM: mean_ov>=0.95 AND basin_frac>=0.90)
# Generic over the weight rule + recall engine so the SAME bar judges all arms.
# `rule` :: :quat_hebbian | :quat_projection | :classical_hebbian | :classical_projection
# =============================================================================

function build_weights(rule::Symbol, patterns, N::Int)
    rule === :quat_hebbian        && return hebbian_weights(patterns, N)
    rule === :quat_projection     && return projection_weights_quat(patterns, N)
    rule === :classical_hebbian   && return classical_hebbian_weights(patterns, N)
    rule === :classical_projection&& return classical_projection_weights(patterns, N)
    error("unknown rule $rule")
end

is_classical(rule::Symbol) = (rule === :classical_hebbian || rule === :classical_projection)

"Capacity trial for one weight rule. Stores M random patterns, corrupts each,
 recalls, reports mean overlap + basin-correct fraction + reliable flag.
 STRICT bar: mean_ov >= ov_thresh AND basin_frac >= basin_thresh."
function capacity_trial(rule::Symbol, M::Int, N::Int, rng;
                        trials=10, corrupt_frac=0.30, ov_thresh=0.95, basin_thresh=0.90)
    patterns = random_patterns(M, N, rng)
    W = build_weights(rule, patterns, N)
    overlaps = Float64[]
    basin_hits = 0
    total = 0
    for (mu, p) in enumerate(patterns)
        for _ in 1:trials
            probe, _ = corrupt(p, corrupt_frac, rng)
            rec = if is_classical(rule)
                classical_recall(probe, W, N)
            else
                r, _ = recall(probe, W, N); r
            end
            push!(overlaps, recall_overlap(rec, p, N))
            lbl, _ = basin_label(rec, patterns, N)
            (lbl == mu) && (basin_hits += 1)
            total += 1
        end
    end
    mean_ov = mean(overlaps)
    basin_frac = basin_hits / total
    reliable = (mean_ov >= ov_thresh) && (basin_frac >= basin_thresh)
    Dict{String,Any}(
        "M" => M, "mean_recall_overlap" => mean_ov,
        "min_recall_overlap" => minimum(overlaps),
        "basin_correct_fraction" => basin_frac,
        "trials_per_pattern" => trials, "corrupt_frac" => corrupt_frac,
        "reliable" => reliable,
    )
end

"max_reliable_M for one rule at one N: scan M=1.. up to M_cap, stop early when
 BOTH the strict bar fails AND the basin fraction has dropped below 0.5 (clearly
 past capacity), to keep runtime bounded. Returns (max_reliable_M, ladder)."
function capacity_for_rule(rule::Symbol, N::Int, base_seed::Int;
                           M_cap::Int=12, trials=10)
    ladder = Dict{String,Any}[]
    max_reliable_M = 0
    consec_fail = 0
    for M in 1:M_cap
        rec = capacity_trial(rule, M, N, MersenneTwister(base_seed + 1000*M); trials=trials)
        push!(ladder, rec)
        if rec["reliable"]
            max_reliable_M = M
            consec_fail = 0
        else
            consec_fail += 1
        end
        # early stop: 3 consecutive failures past the last reliable M and basin clearly gone
        if consec_fail >= 3 && rec["basin_correct_fraction"] < 0.5
            break
        end
    end
    max_reliable_M, ladder
end

# =============================================================================
# CONTROL A (kept from parent) -- GEOMETRIC vs CLASSICAL basin difference
#   On a fixed M-store at N: compare quaternion-Hebbian basins to the classical
#   Euclidean-dot Hebbian basins. If identical -> Clifford is decorative (said so).
# =============================================================================

function geometric_vs_classical(patterns, N::Int, rng; trials=8, corrupt_frac=0.30)
    Wq = hebbian_weights(patterns, N)
    Wr = classical_hebbian_weights(patterns, N)
    basin_mismatch = 0
    total = 0
    cfg_dists = Float64[]
    for (mu, p) in enumerate(patterns)
        for _ in 1:trials
            probe, _ = corrupt(p, corrupt_frac, rng)
            recq, _ = recall(probe, Wq, N)
            recc = classical_recall(probe, Wr, N)
            lblq, _ = basin_label(recq, patterns, N)
            lblc, _ = basin_label(recc, patterns, N)
            (lblq != lblc) && (basin_mismatch += 1)
            push!(cfg_dists, config_distance(recq, recc, N))
            total += 1
        end
    end
    Dict{String,Any}(
        "basin_label_mismatch_fraction" => basin_mismatch/total,
        "mean_recovered_config_distance_quat_vs_classical" => mean(cfg_dists),
        "max_recovered_config_distance" => maximum(cfg_dists),
        "trials" => total,
    )
end

# =============================================================================
# CONTROL B (kept from parent) -- NONCOMMUTATIVE-ORDER (ratchet) basin probe
#   W assembled ELEMENTWISE: W[i,j]=qmul(A[i,j],B[i,j]) vs qmul(B[i,j],A[i,j]).
#   GEOMETRIC arm: full quaternion entries (qmul noncommutes per entry).
#   COMMUTING arm: entries in complex subalgebra (w,x,0,0) (qmul commutes) -> collapse.
#   ERASED metric control: B:=A -> distance exactly 0.
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

function order_basin_probe(N, rng; commuting=false, n_probes=12)
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
    for _ in 1:n_probes
        probe = [rand_unit_quat(rng) for _ in 1:N]
        recAB, _ = recall(probe, WAB, N)
        recBA, _ = recall(probe, WBA, N)
        d = config_distance(recAB, recBA, N)
        push!(basin_dists, d)
        (d > 0.05) && (label_flips += 1)
        recAA1, _ = recall(probe, WAA, N)
        recAA2, _ = recall(probe, WAA, N)
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
    )
end

# =============================================================================
# MAIN
# =============================================================================

function main()
    t0 = time()

    carrier = verify_quaternion_carrier()
    @assert carrier["carrier_verified"] "quaternion carrier failed verification (incl. mat2quat round-trip)"

    # =========================================================================
    # LIFT 1: PSEUDO-INVERSE vs HEBBIAN at N=12 (quaternion + classical)
    # =========================================================================
    N0 = 12
    lift_results = Dict{String,Any}()
    lift_rules = [
        ("quaternion_hebbian",    :quat_hebbian),
        ("quaternion_projection", :quat_projection),
        ("classical_hebbian",     :classical_hebbian),
        ("classical_projection",  :classical_projection),
    ]
    lift_capacity = Dict{String,Int}()
    for (name, rule) in lift_rules
        mr, ladder = capacity_for_rule(rule, N0, SEED + 300; M_cap=12, trials=10)
        lift_capacity[name] = mr
        lift_results[name] = Dict{String,Any}(
            "max_reliable_M" => mr,
            "capacity_ladder" => ladder,
        )
    end
    pseudoinverse_lifts_quaternion = lift_capacity["quaternion_projection"] > lift_capacity["quaternion_hebbian"]
    pseudoinverse_lifts_classical  = lift_capacity["classical_projection"]  > lift_capacity["classical_hebbian"]

    # =========================================================================
    # SCALING (the Feynman check): N in {12,24,48}, quaternion vs classical,
    # both weight rules. Capacity ratio quaternion/classical vs N.
    # =========================================================================
    Ns = [12, 24, 48]
    scaling = Dict{String,Any}[]
    for N in Ns
        # M_cap must EXCEED the highest capacity any arm can reach, else the scan
        # ceiling (not the carrier) sets the number and a fake "ratio=1.0" appears.
        # Classical projection capacity grows with the carrier dimension; scan well
        # past it. The early-stop in capacity_for_rule keeps runtime bounded once an
        # arm is clearly past capacity, so a generous cap costs little on weak arms.
        Mcap = N == 12 ? 16 : (N == 24 ? 24 : 28)
        mr_qh, _ = capacity_for_rule(:quat_hebbian,         N, SEED + 500 + N; M_cap=Mcap, trials=10)
        mr_qp, _ = capacity_for_rule(:quat_projection,      N, SEED + 500 + N; M_cap=Mcap, trials=10)
        mr_ch, _ = capacity_for_rule(:classical_hebbian,    N, SEED + 500 + N; M_cap=Mcap, trials=10)
        mr_cp, _ = capacity_for_rule(:classical_projection, N, SEED + 500 + N; M_cap=Mcap, trials=10)
        # quaternion-vs-classical ratio uses the BEST rule available to each arm
        q_best = max(mr_qh, mr_qp)
        c_best = max(mr_ch, mr_cp)
        ratio_best = c_best == 0 ? NaN : q_best / c_best
        ratio_hebbian = mr_ch == 0 ? NaN : mr_qh / mr_ch
        ratio_projection = mr_cp == 0 ? NaN : mr_qp / mr_cp
        # ceiling-hit guard: if any measured capacity equals M_cap, the scan stopped
        # at its own ceiling and the number is a LOWER BOUND, not the true capacity.
        ceiling_hit = (mr_qh == Mcap) || (mr_qp == Mcap) || (mr_ch == Mcap) || (mr_cp == Mcap)
        push!(scaling, Dict{String,Any}(
            "N" => N,
            "M_cap_scanned" => Mcap,
            "quaternion_hebbian_capacity" => mr_qh,
            "quaternion_projection_capacity" => mr_qp,
            "classical_hebbian_capacity" => mr_ch,
            "classical_projection_capacity" => mr_cp,
            "quaternion_best_capacity" => q_best,
            "classical_best_capacity" => c_best,
            "quaternion_over_classical_ratio_best" => ratio_best,
            "quaternion_over_classical_ratio_hebbian" => ratio_hebbian,
            "quaternion_over_classical_ratio_projection" => ratio_projection,
            "quaternion_strictly_below_classical_best" => q_best < c_best,
            "scan_hit_M_cap_ceiling" => ceiling_hit,
        ))
    end

    # decisive verdict on the scaling question
    ratios_best = [s["quaternion_over_classical_ratio_best"] for s in scaling if !isnan(s["quaternion_over_classical_ratio_best"])]
    quaternion_strictly_below_all_N = all(s["quaternion_strictly_below_classical_best"] for s in scaling)
    any_ceiling_hit = any(s["scan_hit_M_cap_ceiling"] for s in scaling)
    # convergence: ratio trends toward 1 as N grows (last >= first AND last within 15% of 1)
    ratio_trend_up = length(ratios_best) >= 2 && ratios_best[end] >= ratios_best[1]
    converging = length(ratios_best) >= 2 && ratio_trend_up && abs(ratios_best[end] - 1.0) <= 0.15

    if any_ceiling_hit
        scaling_verdict = "INCONCLUSIVE_SCAN_CEILING: at least one N hit its M_cap scan ceiling, so its capacity is a LOWER BOUND, not the measured value; the ratio at that N is contaminated. Raise M_cap and re-run before reading the convergence/structural-gap question. Reported, not hidden."
    elseif quaternion_strictly_below_all_N && !converging
        scaling_verdict = "STRUCTURAL_GAP: quaternion capacity stayed strictly below classical at every tested N and did not converge to parity -> 'geometric product is more constraining' SURVIVED this probe."
    elseif converging
        scaling_verdict = "SMALL_N_ARTIFACT_CANDIDATE: the quaternion/classical capacity ratio trended toward 1 as N grew -> the gap is consistent with a small-N artifact (not a structural penalty)."
    else
        scaling_verdict = "MIXED: quaternion capacity neither stayed uniformly below classical nor cleanly converged; the ratio is non-monotone over the tested N. Reported as-is; no structural claim admitted."
    end

    # =========================================================================
    # CONTROLS (kept from parent, on an N=12 M=3 store)
    # =========================================================================
    pats3 = random_patterns(3, N0, MersenneTwister(SEED + 11))
    gvc = geometric_vs_classical(pats3, N0, MersenneTwister(SEED + 13); trials=8)
    geometric_is_decorative = (gvc["basin_label_mismatch_fraction"] < 1e-6) &&
                              (gvc["mean_recovered_config_distance_quat_vs_classical"] < 1e-6)

    order_geo  = order_basin_probe(N0, MersenneTwister(SEED + 21); commuting=false, n_probes=16)
    order_flat = order_basin_probe(N0, MersenneTwister(SEED + 21); commuting=true,  n_probes=16)
    order_floor = 1e-6
    order_dependent_real = (order_geo["max_order_basin_distance"] > 50*order_floor) &&
                           (order_geo["assembly_noncommutativity_AB_minus_BA"] > 1e-9)
    commuting_control_flat = (order_flat["max_order_basin_distance"] < order_geo["max_order_basin_distance"]/10) &&
                             (order_flat["assembly_noncommutativity_AB_minus_BA"] < 1e-9)
    erased_metric_ok = (order_geo["erased_control_max_basin_distance"] < order_floor) &&
                       (order_geo["erased_control_assembly_noncomm"] < 1e-12)

    runtime = time() - t0

    # =========================================================================
    # RESULT JSON
    # =========================================================================
    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => false,
        "sim_execution_kind" => "nonclassical",
        "status_ladder" => "exists < runs < passes local rerun",
        "bloch_free" => true,
        "non_numpy" => true,
        "reuses_object" => "clifford_hopfield (carrier + recall machinery reused verbatim)",
        "seed" => SEED,
        "runtime_seconds" => runtime,

        "claim_ceiling" => string(
            "COMPUTES finite invariants on a Clifford carrier (Cl(3,0)+ ~ H ~ SU(2)): ",
            "(i) capacity (max_reliable_M) under a pseudo-inverse/projection weight rule ",
            "vs the Hebbian rule, quaternion AND classical, at N=12; (ii) the N-scaling of ",
            "capacity over N in {12,24,48} with the quaternion/classical ratio; (iii) the ",
            "parent's geometric-vs-classical + order-dependent-basin controls. Does NOT assert ",
            "layer-completion / manifold admission / coupling / bridge (rho_AB/Xi/Phi0/Axis0) / ",
            "flux / FEP / physics. A recovered pattern is a CANDIDATE attractor survivor. ",
            "promotion_allowed=false."),

        "F01_witness" => Dict(
            "finite_carrier" => "N quaternion neurons (N in {12,24,48}), each unit q in S^3 ~ Cl(3,0)+ ~ SU(2)",
            "finite_operator" => "weight rules: Hebbian W_ij=sum_mu xi_i (x) conj(xi_j); projection W=Xi pinv(Xi) (quaternion via 2x2 SU(2) blocks; classical via R^4 flatten); quaternion update xi_i <- normalize(sum_j W_ij xi_j)",
            "finite_probe" => "10 corruption seeds/pattern, 30% neuron replacement; 16 random starts for order probe",
            "finite_path" => "async sweeps in DETERMINISTIC cyclic neuron order (1..N) to fixed-point convergence",
        ),
        "N01_witness" => Dict(
            "noncommutative_product" => "quaternion Hamilton product (geometric product on Cl(3,0)+); i*j=k, j*i=-k; preserved in the update under BOTH weight rules",
            "order_sensitive_control" => "W assembled ELEMENTWISE qmul(A,B) vs qmul(B,A); basin distance above floor; commuting complex-subalgebra control collapses it; erased B:=A control is 0",
        ),

        "carrier_verification" => carrier,

        "lift_1_pseudoinverse_vs_hebbian_N12" => Dict{String,Any}(
            "N" => N0,
            "strict_bar" => "mean recall overlap >= 0.95 AND basin-correct fraction >= 0.90 over 10 corruption trials/pattern at 30% corruption",
            "per_rule" => lift_results,
            "capacity_summary" => lift_capacity,
            "pseudoinverse_lifts_quaternion_capacity" => pseudoinverse_lifts_quaternion,
            "pseudoinverse_lifts_classical_capacity" => pseudoinverse_lifts_classical,
            "quaternion_projection_capacity_above_1" => lift_capacity["quaternion_projection"] > 1,
            "interpretation" => string(
                "pseudoinverse(quaternion)=", lift_capacity["quaternion_projection"],
                " vs hebbian(quaternion)=", lift_capacity["quaternion_hebbian"],
                " ; pseudoinverse(classical)=", lift_capacity["classical_projection"],
                " vs hebbian(classical)=", lift_capacity["classical_hebbian"],
                ". If the projection rule does NOT raise max_reliable_M above the Hebbian value, ",
                "the weak capacity is the floor of THIS carrier+probe, not the update rule. ",
                "Reported as measured."),
        ),

        "scaling_N_quaternion_vs_classical" => Dict{String,Any}(
            "Ns" => Ns,
            "strict_bar" => "mean recall overlap >= 0.95 AND basin-correct fraction >= 0.90 over 10 corruption trials/pattern at 30% corruption",
            "per_N" => scaling,
            "ratios_best_quaternion_over_classical" => ratios_best,
            "quaternion_strictly_below_classical_all_N" => quaternion_strictly_below_all_N,
            "ratio_converging_toward_parity" => converging,
            "any_N_hit_scan_ceiling" => any_ceiling_hit,
            "decisive_verdict" => scaling_verdict,
        ),

        "control_A_geometric_vs_classical" => merge(gvc, Dict(
            "geometric_is_decorative" => geometric_is_decorative,
            "interpretation" => geometric_is_decorative ?
                "DECORATIVE: quaternion-product basins indistinguishable from the Euclidean-dot classical control on these patterns." :
                "LOAD-BEARING: quaternion-product basins differ from the Euclidean-dot classical control.",
        )),

        "control_B_order_dependent_basin" => Dict(
            "full_quaternion_arm" => order_geo,
            "commuting_complex_subalgebra_arm" => order_flat,
            "order_floor" => order_floor,
            "order_dependent_basin_real" => order_dependent_real,
            "commuting_control_collapses_to_floor" => commuting_control_flat,
            "erased_metric_control_is_zero" => erased_metric_ok,
            "load_bearing_flip" => order_dependent_real && commuting_control_flat && erased_metric_ok,
        ),

        "blocked_consumers" => [
            "layer-completion / manifold admission",
            "coupling / coexistence / nesting promotion",
            "bridge / rho_AB / Xi / Phi0 / Axis0",
            "flux / FEP / physics",
            "ratchet-edge admission or ratchet-thesis closure (analogy only)",
        ],

        "tool_manifest" => Dict(
            "LinearAlgebra" => "load_bearing: pinv (SVD pseudo-inverse) builds the projection weight rule on BOTH arms; SU(2)/Pauli realization verifies the carrier + the mat2quat round-trip the quaternion projection depends on.",
            "Random" => "load_bearing: random unit quaternions, corruption seeds, random starts (signatures measured, not planted).",
            "Statistics" => "supportive: means over corruption trials and probes.",
            "JSON" => "supportive: receipt emission.",
        ),
        "tool_integration_depth" => Dict(
            "LinearAlgebra" => "load_bearing",
            "Random" => "load_bearing",
            "Statistics" => "supportive",
            "JSON" => "supportive",
        ),
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
    end

    # ----- console summary -----
    println("="^78)
    println("hopfield_capacity_scaling  (object_id=$OBJECT_ID, classification=$CLASSIFICATION)")
    println("="^78)
    println("carrier verified (incl. mat2quat round-trip err=",
            round(carrier["mat2quat_roundtrip_maxerr"], sigdigits=3), "): ", carrier["carrier_verified"])
    println()
    println("LIFT 1 -- PSEUDO-INVERSE vs HEBBIAN at N=12 (max_reliable_M, strict bar):")
    println("  quaternion hebbian    = ", lift_capacity["quaternion_hebbian"])
    println("  quaternion projection = ", lift_capacity["quaternion_projection"],
            "   (lifts quaternion? ", pseudoinverse_lifts_quaternion, ")")
    println("  classical  hebbian    = ", lift_capacity["classical_hebbian"])
    println("  classical  projection = ", lift_capacity["classical_projection"],
            "   (lifts classical? ", pseudoinverse_lifts_classical, ")")
    println()
    println("SCALING -- N in {12,24,48} (max_reliable_M; ratio = quaternion_best/classical_best):")
    for s in scaling
        println("  N=", s["N"],
                "  q_heb=", s["quaternion_hebbian_capacity"],
                "  q_proj=", s["quaternion_projection_capacity"],
                "  c_heb=", s["classical_hebbian_capacity"],
                "  c_proj=", s["classical_projection_capacity"],
                "  | q_best=", s["quaternion_best_capacity"],
                "  c_best=", s["classical_best_capacity"],
                "  ratio=", round(s["quaternion_over_classical_ratio_best"], digits=3),
                "  q<c=", s["quaternion_strictly_below_classical_best"])
    end
    println("  ratios(best) vs N = ", round.(ratios_best, digits=3))
    println("  VERDICT: ", scaling_verdict)
    println()
    println("CONTROL A (geometric vs classical): decorative=", geometric_is_decorative,
            "  mismatch_frac=", round(gvc["basin_label_mismatch_fraction"], digits=3))
    println("CONTROL B (order-dependent basin): load_bearing_flip=",
            order_dependent_real && commuting_control_flat && erased_metric_ok,
            "  (real=", order_dependent_real, " commuting_flat=", commuting_control_flat,
            " erased_ok=", erased_metric_ok, ")")
    println()
    println("runtime = ", round(runtime, digits=2), " s")
    println("result  -> ", RESULT_PATH)
    return result
end

main()
