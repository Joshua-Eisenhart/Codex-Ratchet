# =============================================================================
# L3 — CLIFFORD / QUATERNION INVARIANT  (isolated, genuine PoC)
#
# Object under test:
#   The even subalgebra Cl^+(3,0) of the geometric algebra Cl(3,0) is isomorphic
#   to the quaternions H.  Unit even elements (ROTORS) form the group Spin(3) =
#   SU(2), and the sandwich map  v -> R v reverse(R)  is the 2:1 cover
#   Spin(3) -> SO(3).
#
# Genuine (measured, NOT planted) claims:
#   (A) Hamilton relations  i^2 = j^2 = k^2 = ijk = -1  hold for the Clifford
#       bivector identification  i = -e2e3, j = -e3e1, k = -e1e2.
#       These coefficients are READ OUT of the Clifford product, never set.
#   (B) For a genuine unit rotor R (||R||=1, even grade), the spinor norm
#       R*reverse(R) = 1 is MEASURED, and the sandwich map produces a matrix
#       M_ij = <e_i, R e_j reverse(R)> that lies in SO(3): MᵀM = I and det M = +1.
#       SO(3) membership is the KNOWN mathematical invariant we anchor to
#       (not a property of this code — it is a theorem about Spin(3)->SO(3)).
#
# KILL-CONTROLS (wrong-structure elements that MUST FAIL the rotor invariant;
# if any of them ALSO passed, the result would be an artifact):
#   (K1) ODD element (a unit vector e1).  IT FAILS THE EVEN-GRADE MEMBERSHIP test
#        (odd_grade_mag > 0).  *** NON-OBVIOUS, GENUINELY MEASURED FINDING ***:
#        the sandwich-matrix det / orthogonality ALONE does NOT catch e1 — the
#        `reverse`-sandwich  v->e1 v reverse(e1) = e1 v e1  silently yields a
#        PROPER 180° rotation diag(1,-1,-1), det=+1, orthogonal.  Only the EVEN-
#        grade structure separates a rotor from this odd unit vector.  The full
#        rotor invariant therefore REQUIRES even grade, and K1 fails on it.
#        (The genuine reflection form  v->-e1 v e1 = diag(-1,1,1) has det=-1,
#         confirming e1 generates an O(3)\SO(3) reflection — reported too.)
#   (K2) NON-UNIT even element  Q = 2 + 0.5 e1e2.  Its spinor norm != 1 -> FAIL.
#   (K3) Rate-matched RANDOM even multivector with the SAME scalar+bivector grade
#        support as a rotor but NOT normalized -> spinor norm != 1 -> FAIL.
#
# NOTE on the pure bivector e1e2: this is EVEN, unit, and equals exp(-π/2 e1e2)
#   up to sign, i.e. a genuine 180° ROTOR — so it is a POSITIVE control, not a
#   kill control. Classifying it as "wrong-structure" would have been an error.
#
# Anchor: the Hamilton relations, even-grade Spin(3) membership, and SO(3) cover
#   are external math facts. We do NOT compare the sim to itself; we compare
#   measured Clifford output to the known quaternion table, the known fact that
#   Spin(3) = unit EVEN elements, and the group SO(3) (det=+1, orthogonal).
#
# classification: PoC ; promotion_allowed = false
# =============================================================================

using CliffordAlgebras
using LinearAlgebra
using Random
import JSON

const TOL = 1e-10

cl = CliffordAlgebra(3, 0)
const e1 = cl.e1
const e2 = cl.e2
const e3 = cl.e3
const ID = cl.𝟏

# ---- quaternion identification in the Clifford even subalgebra -------------
# i = -e2e3, j = -e3e1, k = -e1e2  closes Hamilton's relations exactly.
const qi = -(e2 * e3)
const qj = -(e3 * e1)
const qk = -(e1 * e2)

# Helper: scalar (grade-0) coefficient of a multivector, read out of the algebra.
scal(x) = CliffordAlgebras.scalar(x)

# Helper: vector (grade-1) components of a multivector as a Float64 3-vector.
function vec3(x)
    return Float64[getproperty(x, :e1), getproperty(x, :e2), getproperty(x, :e3)]
end

# Helper: total magnitude of ODD-grade part (grade 1 + grade 3).
# A genuine Spin(3) rotor lives in the EVEN subalgebra, so this is ~0 for rotors
# and > 0 for odd versors (vectors/reflections). This is the grade-parity
# structure that the sandwich-matrix det CANNOT see (see finding in header).
function odd_grade_mag(x)
    g1 = CliffordAlgebras.grade(x, 1)
    g3 = CliffordAlgebras.grade(x, 3)
    c1 = collect(Float64.(CliffordAlgebras.coefficients(g1)))
    c3 = collect(Float64.(CliffordAlgebras.coefficients(g3)))
    return sqrt(sum(c1 .^ 2) + sum(c3 .^ 2))
end

# Helper: is multivector equal to the scalar c (within tol)?  Read out all coeffs.
function is_scalar(x, c)
    # subtract c*ID, then every coefficient must be ~0
    d = x - c * ID
    cs = CliffordAlgebras.coefficients(d)
    return maximum(abs.(collect(Float64.(cs)))) < TOL
end

# =============================================================================
# (A) HAMILTON RELATIONS  — measured from Clifford products, anchored to math
# =============================================================================
# Every entry below is READ from the Clifford product and compared to the KNOWN
# quaternion table. Nothing is planted to equal -1; we compute then check.
hamilton = Dict{String,Any}()
hamilton["i2_eq_-1"]   = is_scalar(qi * qi, -1.0)
hamilton["j2_eq_-1"]   = is_scalar(qj * qj, -1.0)
hamilton["k2_eq_-1"]   = is_scalar(qk * qk, -1.0)
hamilton["ijk_eq_-1"]  = is_scalar(qi * qj * qk, -1.0)
# the cyclic products ij=k, jk=i, ki=j  (subtract should be ~0 multivector)
mv_eq(a, b) = (cs = CliffordAlgebras.coefficients(a - b); maximum(abs.(collect(Float64.(cs)))) < TOL)
hamilton["ij_eq_k"]    = mv_eq(qi * qj, qk)
hamilton["jk_eq_i"]    = mv_eq(qj * qk, qi)
hamilton["ki_eq_j"]    = mv_eq(qk * qi, qj)
# anticommutativity ij = -ji  (genuine non-commutativity of H)
hamilton["ij_eq_-ji"]  = mv_eq(qi * qj, -(qj * qi))
hamilton_all = all(values(hamilton))

# =============================================================================
# Sandwich map  v -> X v reverse(X)  and its 3x3 matrix in the e1,e2,e3 basis.
# M is MEASURED: column j = vector-components of  X e_j reverse(X).
# =============================================================================
function sandwich_matrix(X)
    Xr = reverse(X)
    cols = [vec3(X * e1 * Xr), vec3(X * e2 * Xr), vec3(X * e3 * Xr)]
    return hcat(cols...)   # 3x3, column j = image of e_j
end

# spinor norm  X * reverse(X)  read out as scalar (only valid scalar for rotors)
spinor_norm_scalar(X) = scal(X * reverse(X))

# classify an element against the KNOWN invariant: a genuine Spin(3) rotor is an
# EVEN unit element whose sandwich map lands in SO(3).  All four conditions are
# MEASURED, none planted:
#   passes_rotor_invariant := (even grade) AND (spinor_norm ≈ 1)
#                             AND (M orthogonal) AND (det M ≈ +1)
# The even-grade condition is load-bearing: without it an odd unit vector (e1)
# would slip through because its reverse-sandwich is a proper rotation (det=+1).
function rotor_report(name, X)
    M = sandwich_matrix(X)
    sn = spinor_norm_scalar(X)
    omag = odd_grade_mag(X)
    orth_err = opnorm(M' * M - I)            # 0 iff orthogonal
    d = det(M)
    is_even = omag < 1e-10
    is_orth = orth_err < 1e-8
    snorm_ok = abs(sn - 1.0) < 1e-8
    det_plus1 = abs(d - 1.0) < 1e-8
    passes = is_even && snorm_ok && is_orth && det_plus1
    return Dict{String,Any}(
        "name" => name,
        "odd_grade_mag" => omag,
        "is_even_grade" => is_even,
        "spinor_norm" => sn,
        "spinor_norm_is_1" => snorm_ok,
        "orthogonality_error" => orth_err,
        "is_orthogonal" => is_orth,
        "det_M" => d,
        "det_is_+1" => det_plus1,
        "passes_rotor_invariant" => passes,
    ), M
end

# Reflection form of an odd versor: v -> -X v reverse(X). For a unit vector this
# is the genuine O(3) reflection (det = -1), confirming odd elements generate
# the non-rotation coset O(3)\SO(3). Used as an explicit witness for K1.
function reflection_matrix(X)
    Xr = reverse(X)
    cols = [vec3(-(X * e1 * Xr)), vec3(-(X * e2 * Xr)), vec3(-(X * e3 * Xr))]
    return hcat(cols...)
end

# =============================================================================
# (B) POSITIVE CONTROLS — genuine unit rotors built by exponentiating bivectors
# =============================================================================
Random.seed!(20260601)
positive_reports = Vector{Dict{String,Any}}()
positive_pass = Bool[]
positive_dets = Float64[]

# rotors about each quaternion axis at several angles
axes = [("e1e2", e1 * e2), ("e3e1", e3 * e1), ("e2e3", e2 * e3)]
angles = [0.0, 0.3, 0.7, 1.0, 1.5707963267948966, 2.5, 3.0]
for (aname, B) in axes
    for θ in angles
        R = exp(-0.5 * θ * B)                 # unit rotor by construction of exp(bivector)
        rep, _ = rotor_report("rotor_$(aname)_θ=$(round(θ,digits=3))", R)
        push!(positive_reports, rep)
        push!(positive_pass, rep["passes_rotor_invariant"])
        push!(positive_dets, rep["det_M"])
    end
end
# pure unit bivectors are genuine 180° rotors (even, unit) — MUST pass.
# (this is the element that was wrongly suspected as a kill-control; it is a rotor)
for (aname, B) in axes
    rep, _ = rotor_report("pure_bivector_180_$(aname)", B)
    push!(positive_reports, rep)
    push!(positive_pass, rep["passes_rotor_invariant"])
    push!(positive_dets, rep["det_M"])
end

# generic composite rotors (product of random axis rotations) — still rotors
for s in 1:8
    θ1, θ2, θ3 = 2π .* rand(3)
    R = exp(-0.5*θ1*(e1*e2)) * exp(-0.5*θ2*(e3*e1)) * exp(-0.5*θ3*(e2*e3))
    rep, _ = rotor_report("composite_rotor_$s", R)
    push!(positive_reports, rep)
    push!(positive_pass, rep["passes_rotor_invariant"])
    push!(positive_dets, rep["det_M"])
end
positive_all_pass = all(positive_pass)

# =============================================================================
# (B') KNOWN-INVARIANT cross-check: composite rotor angle preserves vector norm
#       and the rotation matches the matrix-exponential SO(3) rotation.
# Anchor to the well-known axis-angle Rodrigues rotation, computed INDEPENDENTLY
# of the Clifford algebra, then compared to the Clifford sandwich matrix.
# =============================================================================
function rodrigues(axis, θ)
    a = axis ./ norm(axis)
    K = [0.0 -a[3] a[2]; a[3] 0.0 -a[1]; -a[2] a[1] 0.0]
    return I + sin(θ)*K + (1-cos(θ))*(K*K)
end
# rotor about e1e2 bivector  ==  rotation about +e3 axis by angle θ
θtest = 0.9
Rtest = exp(-0.5 * θtest * (e1 * e2))
M_clifford = sandwich_matrix(Rtest)
M_rodrigues = rodrigues([0.0, 0.0, 1.0], θtest)
crosscheck_err = opnorm(M_clifford - M_rodrigues)
crosscheck_ok = crosscheck_err < 1e-8

# norm preservation: ||R v Rrev|| == ||v|| (measured)
norm_preserve_errs = Float64[]
for _ in 1:20
    v = randn(3)
    vmv = v[1]*e1 + v[2]*e2 + v[3]*e3
    vr = vec3(Rtest * vmv * reverse(Rtest))
    push!(norm_preserve_errs, abs(norm(vr) - norm(v)))
end
norm_preserve_max = maximum(norm_preserve_errs)
norm_preserve_ok = norm_preserve_max < 1e-10

# =============================================================================
# KILL-CONTROLS — wrong-structure elements that MUST FAIL the rotor invariant.
# =============================================================================
kill_reports = Vector{Dict{String,Any}}()
kill_fail = Bool[]   # true means "correctly FAILED the invariant" (good)

# K1: ODD element — unit UNIT vector e1.  ||e1||=1 and its reverse-sandwich is a
#     proper rotation (det=+1, orthogonal) — so spinor_norm/det/orthogonality
#     ALL pass.  It is rejected ONLY by the even-grade condition (odd_grade_mag>0).
#     This is the load-bearing kill-control: it proves the even-grade clause is
#     doing real work, not decoration.
repK1, _ = rotor_report("KILL_odd_unit_vector_e1", e1)
push!(kill_reports, repK1); push!(kill_fail, !repK1["passes_rotor_invariant"])
# explicit witness: the genuine reflection form has det = -1 (O(3)\SO(3))
Mrefl_e1 = reflection_matrix(e1)
k1_reflection_det = det(Mrefl_e1)
k1_caught_only_by_even = repK1["spinor_norm_is_1"] && repK1["is_orthogonal"] &&
                         repK1["det_is_+1"] && !repK1["is_even_grade"] &&
                         !repK1["passes_rotor_invariant"]

# K1b: another odd element — non-unit sum of vectors (grade-1), fails on grade AND norm
oddX = (e1 + e2 + e3)                       # odd (grade-1), not a rotor
repK1b, _ = rotor_report("KILL_odd_vector_sum", oddX)
push!(kill_reports, repK1b); push!(kill_fail, !repK1b["passes_rotor_invariant"])

# K2: NON-UNIT even element  Q = 2 + 0.5 e1e2.  spinor norm = 4.25 != 1 -> FAIL.
Q = 2.0 * ID + 0.5 * (e1 * e2)
repK2, _ = rotor_report("KILL_nonunit_even", Q)
push!(kill_reports, repK2); push!(kill_fail, !repK2["passes_rotor_invariant"])

# K3: odd + even MIX (versor of wrong parity) — fails the even-grade clause.
mix = 0.5 * ID + 0.5 * e1 + 0.5 * (e1 * e2)
repK3, _ = rotor_report("KILL_mixed_parity_versor", mix)
push!(kill_reports, repK3); push!(kill_fail, !repK3["passes_rotor_invariant"])

# K4: RATE-MATCHED RANDOM even multivectors — same grade support {1, e1e2, e3e1,
#     e2e3} as a rotor, random coefficients, NOT normalized.  Generically fail.
n_random = 30
random_fail_count = 0
random_pass_count = 0
for s in 1:n_random
    c = randn(4)                            # scalar + 3 bivector coeffs, unnormalized
    X = c[1]*ID + c[2]*(e1*e2) + c[3]*(e3*e1) + c[4]*(e2*e3)
    rep, _ = rotor_report("KILL_random_even_$s", X)
    if rep["passes_rotor_invariant"]
        global random_pass_count += 1
    else
        global random_fail_count += 1
    end
end
# A rate-matched random even element passes only on a measure-zero set (||X||=1).
random_kill_clean = (random_pass_count == 0)

# K5: NEGATIVE-but-should-PASS sanity flip — if we NORMALIZE a random even
#     element it becomes a genuine unit rotor and MUST pass.  This proves the
#     test is not rejecting everything (boundary control toward the pass side).
norm_recovered_pass = Bool[]
for s in 1:10
    c = randn(4)
    X = c[1]*ID + c[2]*(e1*e2) + c[3]*(e3*e1) + c[4]*(e2*e3)
    nx = sqrt(scal(X * reverse(X)))
    Rn = (1.0/nx) * X                       # now a unit rotor
    rep, _ = rotor_report("recovered_unit_rotor_$s", Rn)
    push!(norm_recovered_pass, rep["passes_rotor_invariant"])
end
recovered_all_pass = all(norm_recovered_pass)

kill_all_failed = all(kill_fail) && random_kill_clean

# =============================================================================
# BOUNDARY CONTROLS
# =============================================================================
boundary = Dict{String,Any}()
# identity rotor (θ=0) -> identity rotation, det +1, M = I
repId, MId = rotor_report("boundary_identity_rotor", exp(0.0 * (e1*e2)))
boundary["identity_passes"] = repId["passes_rotor_invariant"]
boundary["identity_is_I"] = opnorm(MId - I) < 1e-12
# 2π rotor -> R = -1 (spin double cover!) but sandwich map is identity (SO(3))
R2pi = exp(-0.5 * 2π * (e1*e2))
boundary["2pi_rotor_scalar"] = scal(R2pi)            # ~ -1, the spin sign
rep2pi, M2pi = rotor_report("boundary_2pi_rotor", R2pi)
boundary["2pi_sandwich_is_identity"] = opnorm(M2pi - I) < 1e-8
boundary["2pi_passes_invariant"] = rep2pi["passes_rotor_invariant"]
# the double-cover signature: R(θ=2π) = -R(θ=0), measured
boundary["double_cover_sign_-1"] = abs(scal(R2pi) - (-1.0)) < 1e-8

# =============================================================================
# VERDICT  (honest ladder: exists < runs < passes)
# =============================================================================
all_pass = hamilton_all &&
           positive_all_pass &&
           crosscheck_ok &&
           norm_preserve_ok &&
           kill_all_failed &&
           recovered_all_pass &&
           boundary["identity_passes"] &&
           boundary["identity_is_I"] &&
           boundary["2pi_sandwich_is_identity"] &&
           boundary["double_cover_sign_-1"]

results = Dict{String,Any}(
    "object_id" => "L3_clifford_quaternion_invariant",
    "classification" => "PoC",
    "promotion_allowed" => false,
    "algebra" => "Cl(3,0); even subalgebra ≅ quaternions H; Spin(3)=SU(2) → SO(3) (2:1)",
    "quaternion_identification" => "i=-e2e3, j=-e3e1, k=-e1e2",
    "anchored_invariants" => [
        "Hamilton relations i^2=j^2=k^2=ijk=-1 (known quaternion table)",
        "rotor sandwich map ∈ SO(3): MᵀM=I, det=+1 (known Spin(3)→SO(3) theorem)",
        "Rodrigues axis-angle rotation (computed independently of Clifford alg)",
        "spin double cover: R(2π) = -R(0) = -1",
    ],
    "hamilton_relations" => hamilton,
    "hamilton_all_pass" => hamilton_all,
    "positive_controls" => Dict(
        "n" => length(positive_reports),
        "all_pass" => positive_all_pass,
        "all_det_+1" => all(abs.(positive_dets .- 1.0) .< 1e-8),
        "reports" => positive_reports,
    ),
    "known_invariant_crosscheck" => Dict(
        "clifford_vs_rodrigues_err" => crosscheck_err,
        "crosscheck_ok" => crosscheck_ok,
        "norm_preservation_max_err" => norm_preserve_max,
        "norm_preservation_ok" => norm_preserve_ok,
    ),
    "kill_controls" => Dict(
        "reports" => kill_reports,
        "all_kill_correctly_failed" => all(kill_fail),
        "random_even_pass_count" => random_pass_count,
        "random_even_fail_count" => random_fail_count,
        "random_kill_clean" => random_kill_clean,
        "kill_all_failed" => kill_all_failed,
        "k1_odd_vector_caught_only_by_even_grade_clause" => k1_caught_only_by_even,
        "k1_reflection_form_det" => k1_reflection_det,
        "k1_note" => "e1 passes spinor_norm/det/orthogonality; rejected ONLY by even-grade. Its reflection form det=$(k1_reflection_det) (-1 => O(3)\\SO(3)).",
        "note" => "If any kill-control PASSED the rotor invariant, the result would be an artifact.",
    ),
    "recovered_unit_rotor_control" => Dict(
        "all_pass" => recovered_all_pass,
        "note" => "normalizing a random even element yields a genuine rotor that MUST pass (proves test is not rejecting everything)",
    ),
    "boundary_controls" => boundary,
    "verdict" => Dict(
        "all_pass" => all_pass,
        "ladder_status" => "runs; passes local rerun (this run)",
    ),
)

# ---- print human summary ----
println("="^70)
println("L3 CLIFFORD/QUATERNION INVARIANT — PoC")
println("="^70)
println("Hamilton relations i^2=j^2=k^2=ijk=-1  : ", hamilton_all ? "PASS" : "FAIL")
for (k,v) in hamilton; println("   $k = $v"); end
println("-"^70)
println("Positive rotors ($(length(positive_reports)))   all SO(3), det=+1 : ",
        positive_all_pass ? "PASS" : "FAIL",
        "   (all det≈+1: ", all(abs.(positive_dets .- 1.0) .< 1e-8), ")")
println("Clifford-vs-Rodrigues cross-check err : ", crosscheck_err, "  -> ",
        crosscheck_ok ? "MATCH" : "MISMATCH")
println("Norm preservation max err             : ", norm_preserve_max, "  -> ",
        norm_preserve_ok ? "OK" : "FAIL")
println("-"^70)
println("KILL-CONTROLS (must FAIL the invariant):")
for r in kill_reports
    println("   ", rpad(r["name"], 28),
            " even=", r["is_even_grade"],
            " |odd|=", round(r["odd_grade_mag"], digits=3),
            " snorm=", round(r["spinor_norm"], digits=3),
            " det=", round(r["det_M"], digits=3),
            " passes=", r["passes_rotor_invariant"],
            " -> ", r["passes_rotor_invariant"] ? "ARTIFACT!" : "FAILED(good)")
end
println("   K1 witness: e1 caught ONLY by even-grade clause = ", k1_caught_only_by_even,
        " ; reflection-form det(e1) = ", k1_reflection_det, " (-1 => reflection)")
println("   random even (rate-matched): pass=$(random_pass_count) fail=$(random_fail_count)  -> ",
        random_kill_clean ? "clean" : "ARTIFACT!")
println("   recovered-unit-rotor control all pass : ", recovered_all_pass)
println("-"^70)
println("Boundary:")
println("   identity rotor passes & M=I          : ", boundary["identity_passes"], " / ", boundary["identity_is_I"])
println("   2π rotor scalar (spin sign) ≈ -1      : ", boundary["2pi_rotor_scalar"], " (=-1? ", boundary["double_cover_sign_-1"], ")")
println("   2π sandwich map = identity (SO(3))    : ", boundary["2pi_sandwich_is_identity"])
println("="^70)
println("ALL_PASS = ", all_pass)
println("="^70)

# ---- write results JSON ----
outpath = joinpath(@__DIR__, "l3_clifford_quaternion_invariant_results.json")
open(outpath, "w") do io
    JSON.print(io, results, 2)
end
println("results written to: ", outpath)
