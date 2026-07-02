# =============================================================================
# twistor_incidence_cp3_projective_line.jl
#
# GEOMETRY SCOUT item: G_twistor_incidence
#
# OBJECT: The twistor incidence relation. A twistor is Z = (omega^A, pi_{A'}) in C^4,
#   a pair of 2-spinors. For a spacetime point x (2x2 complex matrix x^{AA'}), the
#   incidence relation is
#                       omega^A = i * x^{AA'} * pi_{A'} .
#   Geometric claim (KNOWN twistor theory): for a FIXED spacetime point x, the set of
#   incident twistors is a 2-complex-dimensional LINEAR subspace of C^4. Projectivized,
#   that subspace is a CP^1 -- a PROJECTIVE LINE in CP^3 (twistor space PT = CP^3).
#
# WHAT IS GENUINELY MEASURED (never planted to a target):
#   (1) INCIDENCE RESIDUAL ||omega - i x pi||: a built incident twistor has residual ~ 0;
#       a NON-incident twistor (omega decoupled from pi) has a LARGE residual. (kill-control)
#   (2) RANK of the spanned subspace of incident twistors == 2   (read out by SVD); a
#       non-incident twistor appended to the incident basis raises the rank 2 -> 3 (off-line).
#   (3) NULL-SEPARATION INTERSECTION GEOMETRY (the real twistor invariant, NOT a tautology):
#       for two spacetime points x1, x2, the incident lines L(x1), L(x2) in CP^3 INTERSECT
#       iff x1, x2 are NULL-separated. MEASURED: intersection_dim of the two 2-planes (via
#       principal angles / SVD of Q1^* Q2) == 2 - rank(x1 - x2) == dim ker(x1-x2). For
#       det(x1-x2) != 0 (timelike/spacelike) the lines are DISJOINT (intersection_dim 0);
#       for det(x1-x2) == 0 (lightlike, x1!=x2) they MEET in one point (intersection_dim 1).
#       This is read out from the measured subspaces and anchored to the standard
#       Penrose null <-> incidence-line-intersection fact; it is NOT true by construction
#       (a generic pair of 2-planes in C^4 meets only at 0).
#
# WHAT IS *NOT* A HEADLINE INVARIANT (kept, but honestly demoted — see notes in-file):
#   - Plucker/Klein-quadric relation p01 p23 - p02 p13 + p03 p12 == 0 is a TAUTOLOGY for ANY
#     4x2 matrix (any two columns span a decomposable 2-plane), so it carries NO information
#     about the incidence structure. We still print it for transparency but it is DECORATIVE.
#   - Linear-combo "line closure" residual ~ 0 only confirms that pi -> i x pi is a LINEAR
#     map; it holds for any linear map and does not test the specific i*x*pi structure.
#     Printed as a linearity sanity check, NOT counted toward the verdict.
#
# CONTROLS:
#   positive : incident twistors built from x give residual ~0 and rank 2.
#   negative : a NON-incident twistor (random omega) has large incidence residual and,
#              added to the incident basis, raises the rank to 3 (it is OFF the line).
#   boundary : x = 0 (degenerate point) forces omega = 0 -> incident set is the pi-plane
#              {(0,pi)}, still rank 2. Distinct line, still valid.
#   geometry : null-separated pairs MEET (intersection_dim 1), generic pairs are DISJOINT
#              (intersection_dim 0); measured intersection_dim == 2 - rank(x1-x2) every pair.
#   KILL     : (a) a wrong-structure pair where omega is chosen INDEPENDENTLY of pi
#                  (rate-matched random) must FAIL incidence (NULL result). If it passed
#                  too, the incidence test would be vacuous/by-construction.
#              (b) three GENERIC (non-incident) twistors span rank 3, NOT 2 -> a generic
#                  triple is NOT a line; only the incidence constraint collapses to a line.
#              (c) a clearly NON-null pair must NEVER intersect (intersection_dim 0); if it
#                  did, the null<->intersection geometry would be vacuous.
#
# Z3 (load-bearing, structural): over the rationals/reals, assert the incidence residual
#   for a fixed integer (x, pi) is exactly zero (SAT realizable) while a perturbed twistor
#   with omega -> omega + delta, delta != 0, makes "residual == 0" UNSAT. Verdicts must
#   FLIP between the genuine and the perturbed case; if they don't, the proof is decorative.
#
# NON-CIRCULARITY: rank==2 and the null<->intersection geometry are read from the MEASURED
#   subspaces and anchored to FIXED mathematical facts (a generic pair of 2-planes in C^4
#   meets only at 0; null separation det(x1-x2)=0 <=> shared incident twistor). No target is
#   planted. The Plucker relation is NOT used as evidence (it is a tautology; see above).
#
# classification: tool_lego_fit_probe / PoC ; promotion_allowed = false
# =============================================================================

using LinearAlgebra
using Random
using JSON
using Z3
import Z3: Expr, as_ast, ref

# Z3.jl wrapper only defines == and isless on Expr (no +,*). Use the raw C API so the
# incidence product omega = i*x*pi is computed SYMBOLICALLY INSIDE Z3 (not number-matched).
z3mul(a::Expr, b::Expr) = Expr(a.ctx, Z3.Z3_mk_mul(ref(a.ctx), 2, [as_ast(a), as_ast(b)]))
z3add(a::Expr, b::Expr) = Expr(a.ctx, Z3.Z3_mk_add(ref(a.ctx), 2, [as_ast(a), as_ast(b)]))

const I2 = ComplexF64[1 0; 0 1]

# ----------------------------------------------------------------------------
# Core: build an incident twistor Z = (omega, pi) for spacetime point x and spinor pi.
#   omega = i * x * pi   (omega, pi in C^2  =>  Z in C^4)
# ----------------------------------------------------------------------------
incident_twistor(x::AbstractMatrix, pi::AbstractVector) = vcat(im .* (x * pi), pi)

# incidence residual of an arbitrary twistor Z=(omega,pi) wrt point x: || omega - i x pi ||
function incidence_residual(x::AbstractMatrix, Z::AbstractVector)
    omega = Z[1:2]; pi = Z[3:4]
    return norm(omega .- im .* (x * pi))
end

# numerical rank via SVD with relative tolerance
function numrank(M::AbstractMatrix; rtol=1e-9)
    s = svdvals(M)
    smax = isempty(s) ? 0.0 : maximum(s)
    tol = rtol * max(smax, 1.0)
    return count(>(tol), s)
end

# Plucker coords of the 2-plane spanned by columns of a 4x2 matrix B (2x2 minors).
# Order indices (0,1,2,3); p_ij = det of rows (i,j). Klein quadric / line in CP^3:
#   p01 p23 - p02 p13 + p03 p12 == 0  for ANY decomposable bivector (i.e. an actual plane).
function plucker_relation(B::AbstractMatrix)
    minor(i, j) = B[i, 1] * B[j, 2] - B[j, 1] * B[i, 2]
    p01 = minor(1, 2); p02 = minor(1, 3); p03 = minor(1, 4)
    p12 = minor(2, 3); p13 = minor(2, 4); p23 = minor(3, 4)
    rel = p01 * p23 - p02 * p13 + p03 * p12
    return (rel, (; p01, p02, p03, p12, p13, p23))
end

# random Hermitian-ish 2x2 complex matrix as a spacetime point x^{AA'}
function random_x(rng)
    A = randn(rng, ComplexF64, 2, 2)
    return A  # general complex point (complexified Minkowski); incidence is linear in x regardless
end

# Hermitian 2x2 spacetime point: x^{AA'} = x^+ . For Hermitian x, det(x) is the (real)
# Minkowski norm; det(x1-x2)=0 is the LIGHTLIKE/null-separation condition.
function random_hermitian_point(rng)
    A = randn(rng, ComplexF64, 2, 2)
    return A + A'
end

random_spinor(rng) = randn(rng, ComplexF64, 2)

# Incident-twistor basis for point x: columns span L(x) = { (i x pi, pi) : pi in C^2 } in C^4.
incidence_basis(x::AbstractMatrix) = vcat(im .* x, Matrix{ComplexF64}(I, 2, 2))   # 4x2

# Dimension of the intersection of two 2-dim subspaces (column spaces of B1,B2) in C^4,
# measured via principal angles: SVD of Q1^* Q2 gives the principal cosines; a singular
# value == 1 means a shared direction. count(==1) = dim of the intersection.
function intersection_dim(B1::AbstractMatrix, B2::AbstractMatrix; tol=1e-7)
    Q1 = Matrix(qr(B1).Q)[:, 1:2]
    Q2 = Matrix(qr(B2).Q)[:, 1:2]
    s = svdvals(Q1' * Q2)
    return count(>(1 - tol), s), (isempty(s) ? 0.0 : maximum(s))
end

# ----------------------------------------------------------------------------
results = Dict{String,Any}()
results["object_id"] = "G_twistor_incidence"
results["title"] = "Twistor incidence: a spacetime point <-> a projective line in CP^3"
results["classification"] = "tool_lego_fit_probe"
results["promotion_allowed"] = false
results["incidence_relation"] = "omega^A = i x^{AA'} pi_{A'}  (Z=(omega,pi) in C^4, twistor space PT=CP^3)"
results["anchored_invariant"] = "Penrose null<->intersection: incident lines L(x1),L(x2) meet in CP^3 iff det(x1-x2)=0 (null-separated); measured intersection_dim == 2 - rank(x1-x2)"
results["decorative_invariants_demoted"] = [
    "Plucker/Klein-quadric relation p01 p23 - p02 p13 + p03 p12 == 0 (tautology for ANY 4x2; carries no incidence info)",
    "linear-combo line-closure residual ~ 0 (only confirms linearity of pi -> i x pi; not the specific structure)",
]

rng = MersenneTwister(20260601)

# =============================================================================
# TEST 1 (POSITIVE): for fixed x, the incident twistors built as (i x pi, pi) have
#   MEASURED incidence residual ~ 0 and span a MEASURED rank-2 subspace (an SVD readout).
#   The Plucker relation and the linear-combo closure are ALSO printed but are explicitly
#   DEMOTED (decorative): Plucker=0 is a tautology for any 4x2; closure=0 only shows the
#   map pi -> i x pi is linear. Neither is counted toward the verdict.
# =============================================================================
pos = Dict{String,Any}()
n_points = 40
n_per_point = 8           # many incident twistors per point (more than enough to span)
ranks = Int[]
incident_resids = Float64[]   # GENUINE: residual of the BUILT incident twistors (should be ~0)
plucker_abs = Float64[]       # demoted (tautology)
max_combo_resid = 0.0         # demoted (linearity only)

for _ in 1:n_points
    x = random_x(rng)
    # build a stack of incident twistors from independent random pi
    cols = [incident_twistor(x, random_spinor(rng)) for _ in 1:n_per_point]
    M = reduce(hcat, cols)                       # 4 x n_per_point
    push!(ranks, numrank(M))

    # GENUINE: each built twistor must actually satisfy omega = i x pi (residual ~ 0)
    for c in cols
        push!(incident_resids, incidence_residual(x, c))
    end

    # DEMOTED sanity outputs (NOT verdict inputs):
    U = svd(M).U[:, 1:2]                          # 4x2 orthonormal basis of the spanned plane
    rel, _ = plucker_relation(U)
    push!(plucker_abs, abs(rel))
    for _ in 1:5
        Z1 = incident_twistor(x, random_spinor(rng))
        Z2 = incident_twistor(x, random_spinor(rng))
        a = randn(rng, ComplexF64); b = randn(rng, ComplexF64)
        Zc = a .* Z1 .+ b .* Z2
        global max_combo_resid = max(max_combo_resid, incidence_residual(x, Zc))
    end
end

pos["n_spacetime_points"] = n_points
pos["incident_twistors_per_point"] = n_per_point
pos["max_incidence_residual_of_built_twistors"] = maximum(incident_resids)   # GENUINE
pos["incidence_residual_is_zero"] = maximum(incident_resids) < 1e-8           # GENUINE
pos["measured_rank_min"] = minimum(ranks)
pos["measured_rank_max"] = maximum(ranks)
pos["expected_rank"] = 2
pos["rank_all_equal_2"] = all(==(2), ranks)                                   # GENUINE (SVD readout)
# --- demoted/decorative (printed, not scored) ---
pos["DEMOTED_max_abs_plucker_relation"] = maximum(plucker_abs)
pos["DEMOTED_plucker_is_tautology_for_any_4x2"] = true
pos["DEMOTED_max_incidence_residual_of_linear_combos"] = max_combo_resid
pos["DEMOTED_closure_only_confirms_linearity"] = true
# verdict uses ONLY the genuinely-measured quantities:
pos["pass"] = pos["incidence_residual_is_zero"] && pos["rank_all_equal_2"]
results["test1_positive"] = pos
println("TEST1 positive: maxIncidenceResid=", round(pos["max_incidence_residual_of_built_twistors"], sigdigits=3),
        "  rank in [", pos["measured_rank_min"], ",", pos["measured_rank_max"], "]",
        "  (demoted: maxPluckerRel=", round(pos["DEMOTED_max_abs_plucker_relation"], sigdigits=3),
        ", maxComboResid=", round(pos["DEMOTED_max_incidence_residual_of_linear_combos"], sigdigits=3), ")",
        "  => PASS=", pos["pass"])

# =============================================================================
# TEST 2 (NEGATIVE / OFF-LINE): a NON-incident twistor has large residual and,
#         appended to the incident basis, raises the rank from 2 to 3 (off the line).
# =============================================================================
neg = Dict{String,Any}()
offline_resids = Float64[]
ranks_with_offline = Int[]
for _ in 1:n_points
    x = random_x(rng)
    M = reduce(hcat, [incident_twistor(x, random_spinor(rng)) for _ in 1:n_per_point])
    # genuinely non-incident twistor: pick pi, then pick omega INDEPENDENTLY (not i x pi)
    pi = random_spinor(rng)
    omega_bad = random_spinor(rng)               # decoupled from pi -> off the incident plane
    Zbad = vcat(omega_bad, pi)
    push!(offline_resids, incidence_residual(x, Zbad))
    push!(ranks_with_offline, numrank(hcat(M, Zbad)))
end
neg["min_incidence_residual_of_offline_twistor"] = minimum(offline_resids)
neg["offline_residual_is_large"] = minimum(offline_resids) > 1e-6
neg["rank_with_offline_min"] = minimum(ranks_with_offline)
neg["rank_with_offline_max"] = maximum(ranks_with_offline)
neg["offline_raises_rank_to_3"] = all(==(3), ranks_with_offline)
neg["pass"] = neg["offline_residual_is_large"] && neg["offline_raises_rank_to_3"]
results["test2_negative_offline"] = neg
println("TEST2 negative(off-line): minResid=", round(neg["min_incidence_residual_of_offline_twistor"], sigdigits=3),
        "  rankWithOffline in [", neg["rank_with_offline_min"], ",", neg["rank_with_offline_max"],
        "]  => PASS=", neg["pass"])

# =============================================================================
# TEST 3 (BOUNDARY): x = 0. Incidence forces omega = 0. Incident set = {(0,pi)} =
#         the pi-plane: still a rank-2 subspace, still a projective line in CP^3,
#         but a DIFFERENT line (the "line at infinity" pi-plane). Boundary, not failure.
# =============================================================================
bnd = Dict{String,Any}()
x0 = zeros(ComplexF64, 2, 2)
M0 = reduce(hcat, [incident_twistor(x0, random_spinor(rng)) for _ in 1:n_per_point])
relU0, _ = plucker_relation(svd(M0).U[:, 1:2])
# verify all omega components are exactly 0 (since x=0)
omega_block_norm = norm(M0[1:2, :])
bnd["x_is_zero"] = true
bnd["omega_block_norm"] = omega_block_norm
bnd["omega_forced_zero"] = omega_block_norm < 1e-12
bnd["measured_rank"] = numrank(M0)
bnd["rank_is_2"] = numrank(M0) == 2
bnd["DEMOTED_abs_plucker_relation"] = abs(relU0)   # decorative tautology, not scored
# verdict uses ONLY the genuinely-measured quantities (omega forced to 0, rank 2):
bnd["pass"] = bnd["omega_forced_zero"] && bnd["rank_is_2"]
results["test3_boundary_x_zero"] = bnd
println("TEST3 boundary(x=0): omegaNorm=", round(omega_block_norm, sigdigits=3),
        "  rank=", bnd["measured_rank"], "  (demoted pluckerRel=", round(bnd["DEMOTED_abs_plucker_relation"], sigdigits=3), ")",
        "  => PASS=", bnd["pass"])

# =============================================================================
# TEST 4 (GEOMETRY -- the genuinely-measured headline replacing the Plucker tautology):
#   NULL-SEPARATION <-> INTERSECTION. Two Hermitian spacetime points x1, x2 give incident
#   lines L(x1), L(x2) in CP^3. A common nonzero twistor (omega,pi) needs i x1 pi = i x2 pi,
#   i.e. (x1-x2) pi = 0 -> nonzero pi exists IFF det(x1-x2)=0 (null separation).
#   MEASURED: intersection_dim of the two 2-planes (principal angles / SVD of Q1^* Q2).
#     generic (det != 0): intersection_dim 0 (lines DISJOINT).
#     null    (det == 0): intersection_dim 1 (lines MEET in one point).
#   Cross-check (anchor, not planted): measured intersection_dim == 2 - rank(x1-x2) every pair.
# =============================================================================
geo = Dict{String,Any}()
n_geo = 60
generic_intersection_dims = Int[]
generic_abs_det = Float64[]
null_intersection_dims = Int[]
null_abs_det = Float64[]
identity_mismatches = 0          # count of pairs where measured intersection_dim != 2 - rank(x1-x2)

for _ in 1:n_geo
    # GENERIC pair (two independent Hermitian points; det(x1-x2) generically != 0 -> spacelike/timelike)
    x1 = random_hermitian_point(rng); x2 = random_hermitian_point(rng)
    kdim, _ = intersection_dim(incidence_basis(x1), incidence_basis(x2))
    push!(generic_intersection_dims, kdim)
    push!(generic_abs_det, abs(det(x1 - x2)))
    global identity_mismatches += (kdim == (2 - numrank(x1 - x2)) ? 0 : 1)

    # NULL pair: x2 = x1 + v v^* (rank-1 Hermitian increment -> det(x1-x2)=det(-v v^*)=0 -> lightlike)
    y1 = random_hermitian_point(rng)
    v  = random_spinor(rng)
    y2 = y1 + v * v'
    kdimN, _ = intersection_dim(incidence_basis(y1), incidence_basis(y2))
    push!(null_intersection_dims, kdimN)
    push!(null_abs_det, abs(det(y1 - y2)))
    global identity_mismatches += (kdimN == (2 - numrank(y1 - y2)) ? 0 : 1)
end

geo["n_pairs_each_class"] = n_geo
geo["generic_max_abs_det_x1_minus_x2"] = maximum(generic_abs_det)
geo["generic_min_abs_det_x1_minus_x2"] = minimum(generic_abs_det)
geo["generic_intersection_dim_max"] = maximum(generic_intersection_dims)
geo["generic_lines_disjoint"] = all(==(0), generic_intersection_dims)         # GENUINE: non-null -> disjoint
geo["null_max_abs_det_x1_minus_x2"] = maximum(null_abs_det)                    # ~0 (lightlike)
geo["null_separation_holds"] = maximum(null_abs_det) < 1e-8
geo["null_intersection_dim_min"] = minimum(null_intersection_dims)
geo["null_intersection_dim_max"] = maximum(null_intersection_dims)
geo["null_lines_meet_in_one_point"] = all(==(1), null_intersection_dims)       # GENUINE: null -> meet
geo["intersection_dim_equals_2_minus_rank_all_pairs"] = (identity_mismatches == 0)  # anchor identity
geo["pass"] = geo["generic_lines_disjoint"] && geo["null_separation_holds"] &&
              geo["null_lines_meet_in_one_point"] && geo["intersection_dim_equals_2_minus_rank_all_pairs"]
results["test4_null_separation_intersection"] = geo
println("TEST4 geometry: generic det in [", round(geo["generic_min_abs_det_x1_minus_x2"], sigdigits=3), ",",
        round(geo["generic_max_abs_det_x1_minus_x2"], sigdigits=3), "] -> interDim<=", geo["generic_intersection_dim_max"],
        "  |  null det<=", round(geo["null_max_abs_det_x1_minus_x2"], sigdigits=3),
        " -> interDim in [", geo["null_intersection_dim_min"], ",", geo["null_intersection_dim_max"], "]",
        "  (interDim==2-rank: ", geo["intersection_dim_equals_2_minus_rank_all_pairs"], ")",
        "  => PASS=", geo["pass"])

# =============================================================================
# KILL-CONTROL A: rate-matched RANDOM pairs (omega random, pi random, NO incidence
#   constraint, same x). If such pairs ALSO satisfied incidence, the relation would be
#   vacuous. Expect: incidence FAILS (residual large) and a triple of generic twistors
#   spans rank 3 (NOT 2) -> a generic triple is NOT a projective line.
# =============================================================================
killA = Dict{String,Any}()
random_pair_resids = Float64[]
generic_triple_ranks = Int[]
for _ in 1:n_points
    x = random_x(rng)
    # rate-matched random twistor (4 random complex entries), check incidence wrt x
    Zr = randn(rng, ComplexF64, 4)
    push!(random_pair_resids, incidence_residual(x, Zr))
    # three GENERIC (independent random) twistors -> generic 2-planes union, rank should be 3
    G = reduce(hcat, [randn(rng, ComplexF64, 4) for _ in 1:3])
    push!(generic_triple_ranks, numrank(G))
end
killA["min_residual_of_random_pairs"] = minimum(random_pair_resids)
killA["random_pairs_fail_incidence"] = minimum(random_pair_resids) > 1e-6   # MUST be true (null result)
killA["generic_triple_rank_min"] = minimum(generic_triple_ranks)
killA["generic_triple_rank_max"] = maximum(generic_triple_ranks)
killA["generic_triple_is_rank3_not_a_line"] = all(==(3), generic_triple_ranks)
# kill-control PASSES (i.e. is healthy) iff the wrong structure gives the NULL result:
killA["kill_control_healthy"] = killA["random_pairs_fail_incidence"] && killA["generic_triple_is_rank3_not_a_line"]
results["kill_control_A_random_pairs"] = killA
println("KILL-A: minRandResid=", round(killA["min_residual_of_random_pairs"], sigdigits=3),
        "  genericTripleRank in [", killA["generic_triple_rank_min"], ",", killA["generic_triple_rank_max"],
        "]  => HEALTHY(wrong-structure gives null)=", killA["kill_control_healthy"])

# =============================================================================
# KILL-CONTROL B: "broken incidence" map omega = i*x*pi + noise. As noise grows, the
#   stacked twistors should leave the rank-2 line (rank -> 3/4) and Plucker rel -> nonzero.
#   This shows the rank-2 / line result is a property of the EXACT incidence map, not an
#   artifact of stacking any structured columns.
# =============================================================================
killB = Dict{String,Any}()
noise_levels = [0.0, 1e-3, 1e-1, 1.0]
killB_rows = []
for eps in noise_levels
    x = random_x(rng)
    cols = ComplexF64[]
    M = Matrix{ComplexF64}(undef, 4, n_per_point)
    for j in 1:n_per_point
        pi = random_spinor(rng)
        omega = im .* (x * pi) .+ eps .* randn(rng, ComplexF64, 2)
        M[:, j] = vcat(omega, pi)
    end
    rel, _ = plucker_relation(svd(M).U[:, 1:2])
    push!(killB_rows, Dict("noise" => eps, "rank" => numrank(M), "abs_plucker_rel" => abs(rel)))
end
killB["rows"] = killB_rows
# healthy iff: zero noise -> rank 2 & plucker 0 ; large noise -> rank > 2 (line broken)
killB["zero_noise_is_line"] = killB_rows[1]["rank"] == 2 && killB_rows[1]["abs_plucker_rel"] < 1e-8
killB["large_noise_breaks_line"] = killB_rows[end]["rank"] > 2
killB["kill_control_healthy"] = killB["zero_noise_is_line"] && killB["large_noise_breaks_line"]
results["kill_control_B_noise_sweep"] = killB
println("KILL-B noise sweep: ", [(r["noise"], r["rank"], round(r["abs_plucker_rel"], sigdigits=2)) for r in killB_rows],
        "  => HEALTHY=", killB["kill_control_healthy"])

# =============================================================================
# Z3 LOAD-BEARING: structural proof of the incidence map omega = i*x*pi over the
#   integers. The matrix-vector product x*pi is computed SYMBOLICALLY INSIDE Z3 (raw
#   Z3_mk_mul/Z3_mk_add), NOT precomputed and number-matched -- so Z3 actually verifies
#   the relation omega = i*x*pi, not a tautology.
#
#   Encoding: x is real -> i*x*pi has real part 0 and imag part = x*pi. Unknowns are the
#   x entries, pi entries, and omega real/imag components. We pin x and pi to a fixed
#   integer instance, assert o_re == 0 and o_im == (x*pi computed in Z3), then test a
#   candidate omega value:
#       genuine omega = (i*x*pi)  -> SAT   (the incidence equations are consistent)
#       perturbed omega (1 entry off) -> UNSAT (off the incidence subspace / off the line)
#   Verdicts MUST FLIP; if they do not, the proof is decorative, not load-bearing.
# =============================================================================
z3res = Dict{String,Any}()

# fixed integer instance: x = [[2,0],[1,3]] (real), pi = [1,1].
#   x*pi = (2*1+0*1, 1*1+3*1) = (2, 4)   =>  i*x*pi = (2i, 4i)
#   genuine omega: re=(0,0), im=(2,4).
function z3_incidence_sat(omega_im1::Int, omega_im2::Int)
    ctx = Z3.Context()
    Zi(v) = Z3.IntVal(v, ctx)

    x11 = Z3.IntVar("x11", ctx); x12 = Z3.IntVar("x12", ctx)
    x21 = Z3.IntVar("x21", ctx); x22 = Z3.IntVar("x22", ctx)
    p1  = Z3.IntVar("p1", ctx);  p2  = Z3.IntVar("p2", ctx)
    o_re1 = Z3.IntVar("o_re1", ctx); o_re2 = Z3.IntVar("o_re2", ctx)
    o_im1 = Z3.IntVar("o_im1", ctx); o_im2 = Z3.IntVar("o_im2", ctx)

    s = Z3.Solver(ctx)
    # pin the instance
    Z3.add(s, x11 == Zi(2)); Z3.add(s, x12 == Zi(0))
    Z3.add(s, x21 == Zi(1)); Z3.add(s, x22 == Zi(3))
    Z3.add(s, p1 == Zi(1));  Z3.add(s, p2 == Zi(1))

    # incidence equations: omega = i*(x*pi). x*pi computed IN Z3.
    #   (x*pi)_1 = x11*p1 + x12*p2 ; (x*pi)_2 = x21*p1 + x22*p2
    Z3.add(s, o_re1 == Zi(0))                                   # i*(real) has zero real part
    Z3.add(s, o_re2 == Zi(0))
    Z3.add(s, o_im1 == z3add(z3mul(x11, p1), z3mul(x12, p2)))   # symbolic x*pi
    Z3.add(s, o_im2 == z3add(z3mul(x21, p1), z3mul(x22, p2)))

    # candidate omega imag components under test
    Z3.add(s, o_im1 == Zi(omega_im1))
    Z3.add(s, o_im2 == Zi(omega_im2))

    return string(Z3.check(s)) == "sat"
end

z3_genuine_sat = z3_incidence_sat(2, 4)    # genuine i*x*pi  -> expect SAT
z3_perturb_sat = z3_incidence_sat(2, 5)    # off-line (o_im2=5 != 4) -> expect UNSAT

z3res["instance"] = "x=[[2,0],[1,3]], pi=[1,1]; x*pi computed inside Z3 -> i*x*pi=(2i,4i)"
z3res["xpi_computed_inside_z3"] = true
z3res["genuine_omega_sat"] = z3_genuine_sat        # expect true
z3res["perturbed_omega_sat"] = z3_perturb_sat      # expect false
z3res["verdicts_flip"] = (z3_genuine_sat == true) && (z3_perturb_sat == false)
z3res["load_bearing"] = z3res["verdicts_flip"]     # load-bearing iff the proof distinguishes
results["z3_structural_proof"] = z3res
println("Z3: genuine SAT=", z3_genuine_sat, "  perturbed SAT=", z3_perturb_sat,
        "  => verdicts flip / load-bearing=", z3res["verdicts_flip"])

# =============================================================================
# OVERALL HONEST STATUS
# =============================================================================
all_genuine_pass = pos["pass"] && neg["pass"] && bnd["pass"] && geo["pass"]
all_kills_healthy = killA["kill_control_healthy"] && killB["kill_control_healthy"] && z3res["load_bearing"]

results["summary"] = Dict(
    "positive_pass" => pos["pass"],
    "negative_offline_pass" => neg["pass"],
    "boundary_pass" => bnd["pass"],
    "null_intersection_geometry_pass" => geo["pass"],
    "kill_A_healthy" => killA["kill_control_healthy"],
    "kill_B_healthy" => killB["kill_control_healthy"],
    "z3_load_bearing" => z3res["load_bearing"],
    "all_genuine_tests_pass" => all_genuine_pass,
    "all_kill_controls_healthy" => all_kills_healthy,
    "genuinely_measured_headline_invariants" => [
        "incidence residual ||omega - i x pi|| ~ 0 for built incident twistors (and LARGE for non-incident)",
        "rank of incident subspace == 2 by SVD (off-line twistor raises it to 3)",
        "null-separation <-> intersection: generic pairs DISJOINT, null pairs MEET; intersection_dim == 2 - rank(x1-x2)",
    ],
    "decorative_invariants_removed_from_verdict" => [
        "Plucker/Klein-quadric relation (tautology for any 4x2)",
        "linear-combo line-closure residual (only confirms map linearity)",
    ],
    "honest_status" => (all_genuine_pass && all_kills_healthy) ? "passes" : "partial_or_fail",
    "ladder" => "exists < runs < passes",
)

println("\n==== SUMMARY ====")
for (k, v) in results["summary"]
    println("  ", k, " = ", v)
end

# write results
outpath = joinpath(@__DIR__, "twistor_incidence_cp3_projective_line_results.json")
open(outpath, "w") do io
    JSON.print(io, results, 2)
end
println("\nwrote ", outpath)
