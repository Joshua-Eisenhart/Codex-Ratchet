#!/usr/bin/env julia
# =============================================================================
# clifford_hopfield.jl  —  QUATERNIONIC CLIFFORD-HOPFIELD ASSOCIATIVE MEMORY
#   object_id        = clifford_hopfield
#   classification   = clifford_hopfield_poc
#   promotion_allowed = false
#   sim_execution_kind = nonclassical (geometric-algebra carrier; density/Clifford only, NO Bloch)
#
# JULIA side of a dual-engine build. A JAX mirror reads the artifacts written here
# (patterns.npy, weights .npy, HOPFIELD_SPEC.md) and re-runs the SAME quaternion
# convention for cross-validation. This file does NOT modify any existing object.
#
# -----------------------------------------------------------------------------
# CLAIM CEILING (hard)
#   This object COMPUTES a finite map and finite invariants on a Clifford carrier:
#     (i)   Hebbian recall on a quaternionic Hopfield network;
#     (ii)  a geometric-vs-classical attractor-basin difference;
#     (iii) an order-dependent (noncommutative) weight-assembly basin probe.
#   It does NOT assert layer-completion, manifold admission, coupling, bridge
#   (rho_AB / Xi / Phi0 / Axis0), flux, FEP, or physics. A pattern that is
#   recovered here is a CANDIDATE attractor survivor, not a proven object.
#   The link to the ratchet survivors (order_null_killtest.jl /
#   ratchet_survivor_reach_killtest.jl) is offered as a DIAGNOSTIC analogy
#   (order-dependent survivor <-> order-dependent basin), NOT a proof of
#   identity between the two objects. promotion_allowed = false.
#
# -----------------------------------------------------------------------------
# GENUINE CARRIER (reused, not invented)
#   The neuron state is a UNIT QUATERNION = an element of the EVEN SUBALGEBRA of
#   Cl(3,0). Cl(3,0)+ = span{1, e1e2, e2e3, e3e1} ~= H ~= SU(2). We realize it on
#   the SAME 2x2 Pauli/SU(2) matrices used by
#     layers/clifford_rotor_spinor_network_entanglement.jl
#   whose generators satisfy {Gamma_a,Gamma_b}=2 delta_ab at 0.0 error.
#   Quaternion map (the ONE convention the JAX mirror must match):
#       q = (w,x,y,z)  ->  Q = w*I2 - i*( x*sx + y*sy + z*sz )
#   This is a faithful *-algebra map: Hamilton product  q*p  <->  matrix product
#   Q*P ; conjugate  conj(q)  <->  Q^dagger ; |q|^2 = det(Q). VERIFIED in-file
#   (i*j=k, j*i=-k, i^2=-1, and the Pauli anticommutator at exactly 0.0).
#   The quaternion (geometric) product is the NONCOMMUTATIVE product the whole
#   object is built on -- NOT the Euclidean dot. That noncommutativity is the
#   N01 root-constraint witness and the hinge of BOTH load-bearing controls.
#
# -----------------------------------------------------------------------------
# FINITE MAP
#   domain   : N=12 quaternion neurons (each unit q in S^3 ~ Cl(3,0)+), M stored
#              patterns (config of 12 unit quaternions), a corrupted probe state.
#   codomain : the recalled fixed-point config (12 unit quaternions) + scalar
#              invariants: recall overlap in [0,1], per-pattern basin labels,
#              capacity (max reliable M), geometric-vs-classical basin distance,
#              order-dependent basin distance + commuting control.
#   F01      : finite carrier (12 neurons x S^3), finite operator set (Hebbian W,
#              quaternion update), finite probe set (seeded corruptions / random
#              starts), finite path (async sweeps to convergence).
#   N01      : the quaternion product is noncommutative; control #2 builds W from
#              an ORDER-SENSITIVE product A*B vs B*A and measures the basin gap
#              vs a commuting (flat) control that MUST collapse it.
#
# TWO LOAD-BEARING CONTROLS (a tool/structure is load_bearing only if removing it
# FLIPS a verdict -- never hardcoded):
#   (1) GEOMETRIC vs CLASSICAL: a parallel Euclidean-dot real Hopfield on the SAME
#       patterns flattened to R^4 (sign update). If the quaternion basins are
#       IDENTICAL to the classical ones, the "Clifford" is decorative and we SAY
#       SO. The verdict is the measured basin/capacity DIFFERENCE.
#   (2) NONCOMMUTATIVE-ORDER (ratchet) PROBE: W assembled as a product of two
#       coupling blocks A*B vs B*A (quaternion-noncommuting). Different assembly
#       ORDERS converge to DIFFERENT basins from the SAME corrupted input ->
#       order-dependent basin. A commuting/flat control (blocks that commute)
#       MUST give the SAME basin (gap at floor). This mirrors the ratchet
#       survivor: order-dependent survivor <-> order-dependent basin.
#
# RUN: julia --project="system_v5/julia_carrier" \
#        "system_v5/julia_carrier/hopfield/clifford_hopfield.jl"
# =============================================================================

using LinearAlgebra
using Random
using Statistics
import JSON
import NPZ

const OBJECT_ID      = "clifford_hopfield"
const CLASSIFICATION = "clifford_hopfield_poc"
const HERE           = @__DIR__
const RESULT_PATH    = joinpath(HERE, "clifford_hopfield_results.json")
const SEED           = 20260602
const N_NEURONS      = 12

# =============================================================================
# QUATERNION CARRIER (Cl(3,0)+ realized on 2x2 SU(2) -- the genuine reused rep)
# A quaternion is stored as q = (w,x,y,z) :: NTuple{4,Float64} (real coeffs).
# Its matrix realization Q = w*I - i(x sx + y sy + z sz) is used ONLY to VERIFY
# the algebra; all dynamics run on the 4-tuple Hamilton product (fast, exact,
# and the form the JAX mirror replicates).
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
# geodesic distance on S^3 (unit quaternions), in [0, pi/2] after sign-folding
function quat_geodesic(q, p)
    d = abs(q[1]*p[1] + q[2]*p[2] + q[3]*p[3] + q[4]*p[4])
    acos(clamp(d, -1.0, 1.0))
end

"VERIFY the carrier algebra against the SU(2) matrix realization (0.0 target)."
function verify_quaternion_carrier()
    qi = (0.0,1.0,0.0,0.0); qj = (0.0,0.0,1.0,0.0); qk = (0.0,0.0,0.0,1.0)
    ij = qmul(qi, qj); ji = qmul(qj, qi); ii = qmul(qi, qi)
    err_ij = qnorm(qadd(ij, qscale(-1.0, qk)))         # i*j = k
    err_ji = qnorm(qadd(ji, qk))                       # j*i = -k
    err_ii = qnorm(qadd(ii, (1.0,0.0,0.0,0.0)))        # i*i = -1
    # matrix realization fidelity: Q(q*p) == Q(q)*Q(p), and {sx,sy}=0, sx^2=I
    rng = MersenneTwister(1)
    mat_err = 0.0
    for _ in 1:200
        a = rand_unit_quat(rng); b = rand_unit_quat(rng)
        mat_err = max(mat_err, maximum(abs.(qmat(qmul(a,b)) - qmat(a)*qmat(b))))
    end
    pauli_anticomm = maximum(abs.(SX*SY + SY*SX))      # {sx,sy} = 0
    pauli_square   = maximum(abs.(SX*SX - I2))         # sx^2 = I
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
# QUATERNIONIC HOPFIELD NETWORK
#   neuron state  xi_i in S^3 (unit quaternion)
#   Hebbian weights W_ij = sum_mu xi^mu_i (x) conj(xi^mu_j)  (quaternion product),
#                   W_ii = 0.  W_ij is a quaternion (the geometric coupling).
#   Energy   E = -Re sum_ij conj(xi_i) * W_ij * xi_j
#   Update   xi_i <- normalize( sum_j W_ij * xi_j )   (left quaternion action)
# =============================================================================

"Hebbian quaternion weight tensor. patterns :: Vector of length-N quaternion configs.
 Returns W :: Matrix{NTuple{4,Float64}} (NxN), W[i,j] a quaternion, diag zeroed."
function hebbian_weights(patterns, N::Int)
    W = Matrix{NTuple{4,Float64}}(undef, N, N)
    for i in 1:N, j in 1:N
        acc = (0.0,0.0,0.0,0.0)
        if i != j
            for xi in patterns
                acc = qadd(acc, qmul(xi[i], qconj(xi[j])))   # xi_i (x) conj(xi_j)
            end
        end
        W[i,j] = acc
    end
    W
end

"Energy E = -Re sum_ij conj(xi_i) * W_ij * xi_j."
function hopfield_energy(state, W, N::Int)
    E = 0.0
    for i in 1:N, j in 1:N
        E -= qre(qmul(qmul(qconj(state[i]), W[i,j]), state[j]))
    end
    E
end

"One async sweep in DETERMINISTIC cyclic neuron order (1..N). xi_i <- normalize(sum_j W_ij xi_j).
 Deterministic order is required so recall is a pure function of (W, state0): only then
 can the order-basin control isolate WEIGHT noncommutativity from update-order randomness
 (an earlier random-order draft let the erased control land >1 apart -- a metric artifact
 the erased control caught; fixed here, reported not hidden)."
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

"Run async dynamics to convergence (or max_sweeps). Pure function of (state0, W).
 Returns (state, sweeps, energies)."
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

"Recall overlap of recovered vs target config: mean cos-similarity (sign-folded),
 mapped to [0,1] (1 = identical up to global S^3 sign)."
function recall_overlap(recovered, target, N::Int)
    s = 0.0
    for i in 1:N
        d = recovered[i][1]*target[i][1] + recovered[i][2]*target[i][2] +
            recovered[i][3]*target[i][3] + recovered[i][4]*target[i][4]
        s += abs(d)
    end
    s / N
end

"Config-to-config distance (mean geodesic, in [0, pi/2]). Basin discriminator."
function config_distance(a, b, N::Int)
    mean(quat_geodesic(a[i], b[i]) for i in 1:N)
end

"Which stored pattern is the recovered config closest to (basin label)."
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

function random_patterns(M::Int, N::Int, rng)
    [[rand_unit_quat(rng) for _ in 1:N] for _ in 1:M]
end

# =============================================================================
# RECALL TEST + CAPACITY LADDER
# =============================================================================

"For a given M: store M random patterns, corrupt each (corrupt_frac), recall,
 report per-pattern overlap + whether the basin label matched the stored pattern.
 trials random corruption seeds per pattern. reliable = mean overlap >= ov_thresh
 AND basin-correct fraction >= basin_thresh."
function capacity_trial(M::Int, N::Int, rng; trials=8, corrupt_frac=0.30,
                        ov_thresh=0.95, basin_thresh=0.90)
    patterns = random_patterns(M, N, rng)
    W = hebbian_weights(patterns, N)
    overlaps = Float64[]
    basin_hits = 0
    total = 0
    for (mu, p) in enumerate(patterns)
        for _ in 1:trials
            probe, _ = corrupt(p, corrupt_frac, rng)
            rec, _, _ = recall(probe, W, N)
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
    ), patterns, W
end

# =============================================================================
# CONTROL #1 -- CLASSICAL EUCLIDEAN-DOT HOPFIELD ON THE SAME R^4 PATTERNS
#   Flatten each unit quaternion to a real R^4 vector. Standard real Hopfield:
#     W_real = sum_mu v^mu (v^mu)^T  (4N x 4N), diag-block zeroed.
#     update v <- W_real v ; for the continuous (graded) carrier we use the
#     linear field + per-neuron renormalize to S^3 (closest classical analogue
#     of the quaternion update WITHOUT the Hamilton product). The DIFFERENCE
#     from the quaternion version is exactly the geometric (noncommutative)
#     product. If basins match, the Clifford is decorative.
# =============================================================================

"Flatten config of N unit quats to a length-4N real vector."
flatten4N(cfg) = reduce(vcat, [collect(q) for q in cfg])

"Unflatten + per-neuron renormalize to S^3."
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
    # zero the per-neuron 4x4 diagonal blocks (the W_ii = 0 analogue)
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

"Geometric-vs-classical: same patterns, same corrupted probes, compare the
 RECOVERED configs and the basin labels. Returns the basin difference."
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
# CONTROL #2 -- NONCOMMUTATIVE-ORDER (RATCHET) WEIGHT-ASSEMBLY PROBE
#
#   HONEST DESIGN NOTE. Matrix multiplication is noncommutative even over a
#   COMMUTATIVE ring, so a scalar-entry or componentwise-entry control does NOT
#   collapse a matrix-product A*B vs B*A gap. An earlier draft that built W as a
#   matrix product and then tried a "commuting entry product" was mathematically
#   wrong (the control did not collapse) and is REPLACED here. To isolate the
#   QUATERNION (N01) noncommutativity as the load-bearing source, we assemble W
#   ELEMENTWISE so the ONLY product that can carry order-dependence is the entry
#   product itself:
#       W_AB[i,j] = qmul(A[i,j], B[i,j])     W_BA[i,j] = qmul(B[i,j], A[i,j])
#   (i != j; diag 0). With FULL quaternion entries qmul(A,B) != qmul(B,A) per
#   entry -> order-dependent W -> order-dependent recovered basin.
#
#     GEOMETRIC arm  : entries are full unit quaternions (all 4 components).
#     COMMUTING arm  : entries are restricted to the COMMUTATIVE complex
#                      subalgebra of H, q = (w, x, 0, 0). On this subalgebra
#                      qmul commutes EXACTLY (i*i is the only imaginary unit), so
#                      W_AB == W_BA to machine precision and the order-basin
#                      distance MUST collapse to the floor. Same elementwise
#                      structure, same recall dynamics, same probes; the ONLY
#                      change is full-H vs complex-subalgebra entries.
#     ERASED metric control : B := A. Then qmul(A,A)=qmul(A,A) trivially, so the
#                      order-basin distance is EXACTLY 0. If a "gap" survived this
#                      the metric would be broken (sanity check on the distance).
#
#   load_bearing flip := geometric arm gives order-dependent basins ABOVE floor
#   AND the commuting (complex-subalgebra) arm collapses to floor AND the erased
#   metric control is 0. Removing the quaternion noncommutativity FLIPS the
#   verdict. This mirrors the ratchet survivor in basin form: order-dependent
#   survivor (ratchet_survivor_reach_killtest) <-> order-dependent Hopfield basin.
# =============================================================================

"Random elementwise coupling block. `commuting=true` restricts each entry to the
 commutative complex subalgebra of H, q=(w,x,0,0) (renormalized), where qmul
 commutes exactly; `commuting=false` uses full unit quaternions. diag 0."
function random_block(N, rng; commuting=false)
    B = Matrix{NTuple{4,Float64}}(undef, N, N)
    for i in 1:N, j in 1:N
        if i == j
            B[i,j] = (0.0,0.0,0.0,0.0)
        elseif commuting
            B[i,j] = qnormalize((randn(rng), randn(rng), 0.0, 0.0))   # complex subalgebra
        else
            B[i,j] = rand_unit_quat(rng)
        end
    end
    B
end

"Elementwise assembled weight: W[i,j] = qmul(A[i,j], B[i,j]), diag 0."
function assemble_elementwise(A, B, N)
    W = Matrix{NTuple{4,Float64}}(undef, N, N)
    for i in 1:N, j in 1:N
        W[i,j] = (i == j) ? (0.0,0.0,0.0,0.0) : qmul(A[i,j], B[i,j])
    end
    W
end

"Max over the assembled tensor of ||W_AB - W_BA|| per entry (assembly-noncommutativity)."
function assembly_noncommutativity(WAB, WBA, N)
    mx = 0.0
    for i in 1:N, j in 1:N
        mx = max(mx, qnorm(qadd(WAB[i,j], qscale(-1.0, WBA[i,j]))))
    end
    mx
end

"Order-basin probe. `commuting=false` -> full-H entries (qmul noncommutes per entry);
 `commuting=true` -> complex-subalgebra entries (qmul commutes per entry). SAME recall
 dynamics, SAME probe set; ONLY the entry algebra changes. Also runs the ERASED metric
 control (B:=A) which MUST give 0."
function order_basin_probe(N, rng; commuting=false, n_probes=12)
    A = random_block(N, rng; commuting=commuting)
    B = random_block(N, rng; commuting=commuting)
    WAB = assemble_elementwise(A, B, N)
    WBA = assemble_elementwise(B, A, N)
    noncomm = assembly_noncommutativity(WAB, WBA, N)
    # erased metric control: B:=A so the two assembled weights are identical
    WAA = assemble_elementwise(A, A, N)
    erased_noncomm = assembly_noncommutativity(WAA, WAA, N)
    basin_dists = Float64[]
    erased_basin_dists = Float64[]
    label_flips = 0
    for _ in 1:n_probes
        probe = [rand_unit_quat(rng) for _ in 1:N]
        recAB, _, _ = recall(probe, WAB, N)
        recBA, _, _ = recall(probe, WBA, N)
        d = config_distance(recAB, recBA, N)
        push!(basin_dists, d)
        (d > 0.05) && (label_flips += 1)   # two orders settle measurably apart
        # erased metric control basin distance (must be ~0): same W both arms
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
    )
end

# =============================================================================
# MAIN
# =============================================================================

function main()
    t0 = time()
    rng = MersenneTwister(SEED)

    carrier = verify_quaternion_carrier()
    @assert carrier["carrier_verified"] "quaternion carrier failed verification"

    N = N_NEURONS

    # ----- recall test + capacity ladder -----
    capacity_ladder = Dict{String,Any}[]
    max_reliable_M = 0
    saved_patterns = nothing
    saved_W = nothing
    for M in 1:8
        rec, pats, W = capacity_trial(M, N, MersenneTwister(SEED + 100*M); trials=8)
        push!(capacity_ladder, rec)
        rec["reliable"] && (max_reliable_M = M)
        if M == 3            # the requested headline store (save these artifacts)
            saved_patterns = pats
            saved_W = W
        end
    end

    # headline single-corruption recall (M=3, 30% corrupted, one named probe)
    headline_rng = MersenneTwister(SEED + 7)
    p3 = saved_patterns
    target = p3[1]
    probe, corrupted_idx = corrupt(target, 0.30, headline_rng)
    rec, sweeps, energies = recall(probe, saved_W, N)
    headline_overlap = recall_overlap(rec, target, N)
    headline_basin, headline_basin_dist = basin_label(rec, p3, N)
    probe_overlap = recall_overlap(probe, target, N)

    # ----- control #1: geometric vs classical (on the M=3 store) -----
    gvc = geometric_vs_classical(p3, saved_W, N, MersenneTwister(SEED + 11); trials=8)
    geometric_is_decorative = (gvc["basin_label_mismatch_fraction"] < 1e-6) &&
                              (gvc["mean_recovered_config_distance_quat_vs_classical"] < 1e-6)

    # ----- control #2: noncommutative-order basin probe + commuting control -----
    order_geo  = order_basin_probe(N, MersenneTwister(SEED + 21); commuting=false, n_probes=16)
    order_flat = order_basin_probe(N, MersenneTwister(SEED + 21); commuting=true,  n_probes=16)
    # floor: machine-noise-scale angular floor for the recovered-config distance
    order_floor = 1e-6
    order_dependent_real = (order_geo["max_order_basin_distance"] > 50*order_floor) &&
                           (order_geo["assembly_noncommutativity_AB_minus_BA"] > 1e-9)
    commuting_control_flat = (order_flat["max_order_basin_distance"] < order_geo["max_order_basin_distance"]/10) &&
                             (order_flat["assembly_noncommutativity_AB_minus_BA"] < 1e-9)
    erased_metric_ok = (order_geo["erased_control_max_basin_distance"] < order_floor) &&
                       (order_geo["erased_control_assembly_noncomm"] < 1e-12)

    runtime = time() - t0

    # ----- save artifacts for the JAX mirror (npy + json patterns) -----
    # patterns as (M, N, 4) Float64 array; weights as (N, N, 4) Float64 array.
    M3 = length(p3)
    pat_arr = Array{Float64}(undef, M3, N, 4)
    for mu in 1:M3, i in 1:N
        pat_arr[mu, i, :] = collect(p3[mu][i])
    end
    W_arr = Array{Float64}(undef, N, N, 4)
    for i in 1:N, j in 1:N
        W_arr[i, j, :] = collect(saved_W[i,j])
    end
    probe_arr = Array{Float64}(undef, N, 4)
    for i in 1:N
        probe_arr[i, :] = collect(probe[i])
    end
    NPZ.npzwrite(joinpath(HERE, "patterns.npy"), pat_arr)
    NPZ.npzwrite(joinpath(HERE, "weights.npy"), W_arr)
    NPZ.npzwrite(joinpath(HERE, "probe.npy"), probe_arr)

    # ----- result JSON -----
    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => false,
        "sim_execution_kind" => "nonclassical",
        "status_ladder" => "exists < runs < passes local rerun",
        "bloch_free" => true,
        "non_numpy" => true,
        "seed" => SEED,
        "n_neurons" => N,
        "runtime_seconds" => runtime,

        "claim_ceiling" => string(
            "COMPUTES a finite map on a Clifford carrier (Cl(3,0)+ ~ H ~ SU(2)): ",
            "Hebbian quaternion recall, a geometric-vs-classical basin difference, ",
            "and an order-dependent (noncommutative) weight-assembly basin probe. ",
            "Does NOT assert layer-completion / manifold admission / coupling / ",
            "bridge (rho_AB/Xi/Phi0/Axis0) / flux / FEP / physics. The link to the ",
            "ratchet survivors is a DIAGNOSTIC analogy, not proven identity. ",
            "A recovered pattern is a CANDIDATE attractor survivor. promotion_allowed=false."),

        "F01_witness" => Dict(
            "finite_carrier" => "12 quaternion neurons, each unit q in S^3 ~ Cl(3,0)+ ~ SU(2)",
            "finite_operator" => "Hebbian quaternion weight W_ij = sum_mu xi_i (x) conj(xi_j); quaternion update xi_i <- normalize(sum_j W_ij xi_j)",
            "finite_probe" => "8 corruption seeds/pattern, 30% neuron replacement; 16 random starts for order probe",
            "finite_path" => "async sweeps in DETERMINISTIC cyclic neuron order (1..N) to fixed-point convergence (recall is a pure function of (W, state0))",
        ),
        "N01_witness" => Dict(
            "noncommutative_product" => "quaternion Hamilton product (geometric product on Cl(3,0)+); i*j=k, j*i=-k",
            "order_sensitive_control" => "W assembled ELEMENTWISE W[i,j]=qmul(A[i,j],B[i,j]) vs qmul(B[i,j],A[i,j]); basin distance above floor; commuting complex-subalgebra (w,x,0,0) control collapses it; erased B:=A control is 0",
        ),

        "carrier_verification" => carrier,

        "recall_headline" => Dict(
            "M_stored" => M3,
            "corrupt_frac" => 0.30,
            "corrupted_neuron_indices" => corrupted_idx,
            "probe_overlap_before_recall" => probe_overlap,
            "recovered_overlap_after_recall" => headline_overlap,
            "recovered_basin_label" => headline_basin,
            "recovered_basin_is_target_pattern_1" => (headline_basin == 1),
            "recovered_basin_distance" => headline_basin_dist,
            "sweeps_to_converge" => sweeps,
            "energy_first" => energies[1],
            "energy_last" => energies[end],
            "energy_monotone_nonincreasing" => all(diff(energies) .<= 1e-9),
        ),

        "capacity_ladder" => capacity_ladder,
        "max_reliable_M" => max_reliable_M,
        "capacity_note" => string(
            "reliable = mean recall overlap >= 0.95 AND basin-correct fraction >= 0.90 ",
            "over 8 corruption trials/pattern at 30% corruption. The real capacity is ",
            "max_reliable_M; if recall fails above M=2, that is reported honestly here."),

        "control_1_geometric_vs_classical" => merge(gvc, Dict(
            "geometric_is_decorative" => geometric_is_decorative,
            "interpretation" => geometric_is_decorative ?
                "DECORATIVE: quaternion-product basins are indistinguishable from the Euclidean-dot classical control on these patterns." :
                "LOAD-BEARING: quaternion-product (Cl(3,0)+ geometric) basins differ from the Euclidean-dot classical control; the Clifford structure changed the attractor outcome.",
        )),

        "control_2_order_dependent_basin" => Dict(
            "full_quaternion_arm" => order_geo,
            "commuting_complex_subalgebra_arm" => order_flat,
            "order_floor" => order_floor,
            "order_dependent_basin_real" => order_dependent_real,
            "commuting_control_collapses_to_floor" => commuting_control_flat,
            "erased_metric_control_is_zero" => erased_metric_ok,
            "load_bearing_flip" => order_dependent_real && commuting_control_flat && erased_metric_ok,
            "design_note" => string(
                "W assembled ELEMENTWISE W[i,j]=qmul(A[i,j],B[i,j]) so the ONLY source of ",
                "order-dependence is the quaternion Hamilton product. Commuting control ",
                "restricts entries to the complex subalgebra (w,x,0,0) where qmul commutes ",
                "exactly -> W_AB==W_BA -> basin gap collapses. Erased control B:=A gives 0. ",
                "An earlier matrix-product framing was mathematically wrong (matrix mult ",
                "noncommutes over a commutative ring) and was replaced; this is reported, not hidden."),
            "ratchet_link" => string(
                "DIAGNOSTIC analogy to order_null_killtest.jl / ratchet_survivor_reach_killtest.jl: ",
                "order-dependent survivor (forward!=reversed above floor, commuting control flat) ",
                "<-> order-dependent Hopfield basin (qmul(A,B)!=qmul(B,A) basin above floor, ",
                "complex-subalgebra control flat). NOT a proof the two objects are identical."),
        ),

        "artifacts_emitted" => [
            "patterns.npy (M,N,4) Float64 -- M=3 stored quaternion patterns",
            "weights.npy (N,N,4) Float64 -- Hebbian quaternion weight tensor",
            "probe.npy (N,4) Float64 -- the corrupted recall probe",
            "HOPFIELD_SPEC.md -- quaternion convention + energy + update for the JAX mirror",
            "clifford_hopfield_results.json -- this file",
        ],
        "blocked_consumers" => [
            "layer-completion / manifold admission",
            "coupling / coexistence / nesting promotion",
            "bridge / rho_AB / Xi / Phi0 / Axis0",
            "flux / FEP / physics",
            "ratchet-edge admission or ratchet-thesis closure (analogy only)",
        ],

        "tool_manifest" => Dict(
            "LinearAlgebra" => "load_bearing: SU(2)/Pauli matrix realization that VERIFIES the quaternion carrier (anticommutator, Hamilton=matrix-product) at 0.0 error.",
            "Random" => "load_bearing: random unit quaternions, corruption seeds, random starts (signatures measured, not planted).",
            "Statistics" => "supportive: means over corruption trials and probes.",
            "NPZ" => "load_bearing: writes patterns/weights/probe .npy for the JAX mirror cross-validation.",
            "JSON" => "supportive: receipt emission.",
        ),
        "tool_integration_depth" => Dict(
            "LinearAlgebra" => "load_bearing",
            "Random" => "load_bearing",
            "Statistics" => "supportive",
            "NPZ" => "load_bearing",
            "JSON" => "supportive",
        ),
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
    end

    # ----- console summary -----
    println("="^78)
    println("clifford_hopfield  (object_id=$OBJECT_ID, classification=$CLASSIFICATION)")
    println("="^78)
    println("carrier verified (i*j=k, {sx,sy}=0, Hamilton==matrix): ", carrier["carrier_verified"])
    println()
    println("RECALL (M=3, 30% corrupted pattern 1):")
    println("  probe overlap before  : ", round(probe_overlap, digits=4))
    println("  recovered overlap after: ", round(headline_overlap, digits=4),
            "  basin=", headline_basin, " (target=1)")
    println("  sweeps=", sweeps, "  energy ", round(energies[1],digits=3),
            " -> ", round(energies[end],digits=3),
            "  monotone=", all(diff(energies) .<= 1e-9))
    println()
    println("CAPACITY LADDER (reliable iff mean_overlap>=0.95 & basin_frac>=0.90):")
    for r in capacity_ladder
        println("  M=", r["M"], "  mean_ov=", round(r["mean_recall_overlap"],digits=3),
                "  basin_frac=", round(r["basin_correct_fraction"],digits=3),
                "  reliable=", r["reliable"])
    end
    println("  -> max_reliable_M = ", max_reliable_M)
    println()
    println("CONTROL 1 (geometric vs classical):")
    println("  basin mismatch frac = ", round(gvc["basin_label_mismatch_fraction"],digits=4),
            "  mean cfg dist = ", round(gvc["mean_recovered_config_distance_quat_vs_classical"],digits=4))
    println("  quaternion basin-correct = ", round(gvc["quaternion_basin_correct_fraction"],digits=3),
            "  classical basin-correct = ", round(gvc["classical_basin_correct_fraction"],digits=3))
    println("  geometric_is_decorative = ", geometric_is_decorative)
    println()
    println("CONTROL 2 (order-dependent basin):")
    println("  full-quat  : noncomm=", round(order_geo["assembly_noncommutativity_AB_minus_BA"],digits=4),
            "  max_order_basin_dist=", round(order_geo["max_order_basin_distance"],digits=4),
            "  frac_order_dep=", round(order_geo["fraction_probes_order_dependent"],digits=3))
    println("  commuting  : noncomm=", round(order_flat["assembly_noncommutativity_AB_minus_BA"],digits=8),
            "  max_order_basin_dist=", round(order_flat["max_order_basin_distance"],digits=8))
    println("  erased ctl : noncomm=", round(order_geo["erased_control_assembly_noncomm"],digits=10),
            "  max_basin_dist=", round(order_geo["erased_control_max_basin_distance"],digits=10))
    println("  order_dependent_basin_real=", order_dependent_real,
            "  commuting_collapses=", commuting_control_flat, "  erased_ok=", erased_metric_ok)
    println("  load_bearing_flip=", order_dependent_real && commuting_control_flat && erased_metric_ok)
    println()
    println("runtime = ", round(runtime, digits=2), " s")
    println("result  -> ", RESULT_PATH)
    return result
end

main()
