# =====================================================================
# G_Pin3_Spin3_chirality  —  GEOMETRY SCOUT (isolated, genuine PoC)
#
# CLAIM UNDER TEST
#   Pin(3) double-covers O(3); Spin(3) (= even subalgebra units) double-
#   covers SO(3). The chirality / parity split is whether a group element
#   lifts a reflection (odd grade, improper, det = -1) or a rotation
#   (even grade, proper, det = +1). The two Pin groups Pin+ / Pin- differ
#   only in the sign of r^2 for a reflection generator r:
#       Pin+  (built in Cl(3,0,0)):  r^2 = +1
#       Pin-  (built in Cl(0,3,0)):  r^2 = -1
#
# HONESTY DISCIPLINE (anti-theater)
#   * Every claimed property (det sign, orthogonality, 2->1 cover, the
#     Pin sign) is MEASURED by reading out the induced 3x3 action on the
#     basis vectors e1,e2,e3 of the actual Clifford algebra. NOTHING is
#     planted to equal a target.
#   * The det = +/-1 chirality split is checked against the KNOWN math
#     invariant det(O(3) element) in {+1,-1}, and against the standard
#     fact that SO(3) = ker(det) (the even/proper sector). Anchored to
#     math, not to itself.
#   * KILL-CONTROL: a "wrong-structure" sandwich (even element used as if
#     it were a reflection, i.e. the twisted conjugation that an even
#     element induces) must give det = +1, NOT det = -1. If the wrong
#     structure ALSO produced an improper map, the chirality split would
#     be an artifact of the sandwich formula rather than of the odd
#     (reflection) sector. We require it to FAIL (give the null/proper
#     result).
#   * Z3 is LOAD-BEARING: it encodes the sign-group homomorphism THEORY over
#     FREE variables (p,d in {-1,+1}, law d==p), pins ONLY the MEASURED parity,
#     and lets the solver DERIVE the det. The UNSAT/SAT verdict then flips on the
#     measured det relative to the theory -- a broken or out-of-group readout
#     returns SAT. (The earlier decorative form fed both sides as literals and
#     only compared two numbers; it was removed.)
#   * The 2*pi double-cover sign is MEASURED from the geometric product of two
#     genuine pi-rotation rotors, NOT read off cos(pi). Each pi rotor induces a
#     real 180deg SO(3) rotation (kill-anchor: NOT the identity).
#
# classification = PoC ; promotion_allowed = false
# =====================================================================

using CliffordAlgebras
using LinearAlgebra
using Random
using JSON
import Z3

const RESULTS = Dict{String,Any}()
RESULTS["classification"] = "PoC"
RESULTS["promotion_allowed"] = false
RESULTS["item"] = "G_Pin3_Spin3_chirality"
RESULTS["tools"] = Dict("CliffordAlgebras"=>true, "LinearAlgebra"=>true, "Z3"=>true)

Random.seed!(20260601)

# ----------------------------------------------------------------------
# Helpers: read out the induced O(3) action of a Clifford versor.
# A versor u acts on a vector v by the twisted (graded) conjugation
#       Ad_tw(u) v = (-1)^{grade(u)} * u * v * u^{-1}
# This is the standard Pin -> O(n) homomorphism: even versors give the
# untwisted conjugation (rotations, det=+1); odd versors (single unit
# vectors = reflections) give MINUS the conjugation (reflections, det=-1).
# We MEASURE the 3x3 matrix by sending each basis vector e_j through it
# and reading the grade-1 coefficients of the image. No targets planted.
# ----------------------------------------------------------------------

# grade-1 coefficient vector [c_e1, c_e2, c_e3] read from a multivector
function vec3(mv)
    g1 = CliffordAlgebras.grade(mv, 1)
    return Float64[g1.e1, g1.e2, g1.e3]
end

# inverse of a unit versor: u^{-1} = reverse(u) / (u * reverse(u)).scalar
function versor_inverse(u)
    ur = CliffordAlgebras.reverse(u)
    nrm = CliffordAlgebras.scalar(u * ur)
    @assert abs(nrm) > 1e-12 "degenerate versor (norm ~ 0)"
    return ur * (1.0 / nrm)
end

# the parity sign (-1)^grade for a *homogeneous* versor; we detect parity
# by reading which grades are populated, never by assuming it.
function versor_parity_sign(u)
    cl = u  # multivector carries its algebra
    has_even = false; has_odd = false
    for k in 0:3
        gk = CliffordAlgebras.grade(u, k)
        # nonzero if any grade-k coefficient survives
        nz = any(abs.(CliffordAlgebras.vector(gk)) .> 1e-10)
        if nz
            (k % 2 == 0) ? (has_even = true) : (has_odd = true)
        end
    end
    @assert !(has_even && has_odd) "versor is not homogeneous (mixed parity)"
    return has_odd ? -1 : +1
end

# measure the 3x3 matrix of the induced action of versor u, using the
# twisted conjugation with the MEASURED parity sign.
function induced_O3(u, basis::Vector)
    s = versor_parity_sign(u)
    uinv = versor_inverse(u)
    cols = Vector{Vector{Float64}}()
    for ej in basis
        img = u * ej * uinv          # conjugation
        img = (s == -1) ? -img : img # twist for odd versors
        push!(cols, vec3(img))
    end
    return hcat(cols...)             # 3x3, column j = image of e_j
end

# ----------------------------------------------------------------------
# Build both Pin worlds:  Pin+ in Cl(3,0,0),  Pin- in Cl(0,3,0)
# ----------------------------------------------------------------------
function build_world(sig::Tuple{Int,Int})
    p, q = sig
    cl = CliffordAlgebra(p, q, 0)
    e1 = cl.e1; e2 = cl.e2; e3 = cl.e3
    return cl, [e1, e2, e3]
end

clp, basis_p = build_world((3, 0))   # Pin+ ambient (e_i^2 = +1)
clm, basis_m = build_world((0, 3))   # Pin- ambient (e_i^2 = -1)

# ======================================================================
# (A) PIN SIGN  —  the defining Pin+ / Pin- distinction (MEASURED r^2)
# ======================================================================
# A reflection generator is a unit grade-1 vector r. r^2 = scalar.
r_plus  = basis_p[1]                    # e1 in Cl(3,0,0)
r_minus = basis_m[1]                    # e1 in Cl(0,3,0)
rsq_plus  = CliffordAlgebras.scalar(r_plus  * r_plus)
rsq_minus = CliffordAlgebras.scalar(r_minus * r_minus)

RESULTS["pin_sign"] = Dict(
    "Pin+_r2_measured" => rsq_plus,
    "Pin-_r2_measured" => rsq_minus,
    "expected_Pin+"    => +1,
    "expected_Pin-"    => -1,
    "distinguishes"    => (rsq_plus != rsq_minus),
)

# ======================================================================
# (B) SPIN(3) = EVEN PART  double-covers SO(3)  (MEASURED)
# ======================================================================
# Spin element: R = exp(-theta/2 * B) for a unit bivector B. We use the
# series via the closed form on a unit bivector: B^2 = -1, so
#   R = cos(theta/2) - sin(theta/2) B.
cl = clp; e1 = basis_p[1]; e2 = basis_p[2]; e3 = basis_p[3]
B12 = e1 * e2                         # unit bivector, B12^2 = -1
@assert CliffordAlgebras.scalar(B12 * B12) == -1

# random rotation angle, MEASURED action read out
spin_tests = []
det_rot_all_plus_one = true
ortho_max_err = 0.0
for trial in 1:6
    theta = 2π * rand()
    R = cos(theta/2) * cl.𝟏 - sin(theta/2) * B12
    M = induced_O3(R, basis_p)
    d = det(M)
    orth_err = opnorm(M' * M - I)
    global ortho_max_err = max(ortho_max_err, orth_err)
    # compare to the analytic SO(3) rotation about e3 by theta
    Mexp = [cos(theta) -sin(theta) 0.0;
            sin(theta)  cos(theta) 0.0;
            0.0         0.0        1.0]
    match_err = opnorm(M - Mexp)
    if abs(d - 1.0) > 1e-9
        global det_rot_all_plus_one = false
    end
    push!(spin_tests, Dict(
        "theta"=>theta, "det"=>d, "ortho_err"=>orth_err,
        "match_analytic_SO3_err"=>match_err,
        "parity_sign"=>versor_parity_sign(R)))
end

# 2 -> 1 COVER (the defining Spin double-cover fact), MEASURED:
#   (1) R and -R induce the SAME SO(3) element
#   (2) a full 2*pi rotation gives R = -1 (NOT +1) yet the IDENTITY in SO(3)
theta = 2π * rand()
R     = cos(theta/2) * cl.𝟏 - sin(theta/2) * B12
Rneg  = -R
M_R    = induced_O3(R,    basis_p)
M_Rneg = induced_O3(Rneg, basis_p)
double_cover_same = opnorm(M_R - M_Rneg)        # MEASURE: should be ~0

# --- the 2*pi versor sign, built so the -1 is MEASURED, not forced by cos(pi) ---
# OLD (by-construction) form: cos(pi)*1 - sin(pi)*B12 collapses ALGEBRAICALLY to
# the scalar -1 (sin(pi)=0 nulls the bivector). Reading -1 back was just reading
# cos(pi) — no Clifford content. INSTEAD we compose TWO genuine pi-rotation rotors
# via the Clifford product. A pi rotation (half-angle pi/2) is the rotor
#   R_pi = cos(pi/2) - sin(pi/2) B12 = -B12  (a pure grade-2 bivector versor),
# whose induced SO(3) map is a genuine 180deg rotation (NOT identity). Multiplying
# two of them with the actual geometric product MEASURES the cover sign: the
# product lands on the scalar -1 while the composed SO(3) action is the identity.
R_pi  = cos(π/2) * cl.𝟏 - sin(π/2) * B12        # = -B12, genuine bivector rotor
M_pi  = induced_O3(R_pi, basis_p)               # MEASURE: a real 180deg rotation
pi_rotation_not_identity = opnorm(M_pi - I)     # MEASURE: ~2, NOT identity (kill-anchor)
R_2pi = R_pi * R_pi                             # geometric product of two pi rotors
M_2pi = induced_O3(R_2pi, basis_p)
R_2pi_scalar = CliffordAlgebras.scalar(R_2pi)   # MEASURE (via clifford product): -1
R_2pi_bivec  = sqrt(sum(abs2, CliffordAlgebras.vector(CliffordAlgebras.grade(R_2pi, 2))))
identity_err_2pi = opnorm(M_2pi - I)            # MEASURE: SO(3) identity

RESULTS["spin_even_rotations"] = Dict(
    "all_det_plus_one"     => det_rot_all_plus_one,
    "max_ortho_err"        => ortho_max_err,
    "tests"                => spin_tests,
    "double_cover_R_vs_negR_O3_diff" => double_cover_same,
    "pi_rotor_SO3_not_identity"      => pi_rotation_not_identity,  # ~2: genuine 180deg
    "two_pi_versor_scalar_measured"  => R_2pi_scalar,   # = -1, from R_pi*R_pi product
    "two_pi_versor_bivec_residual"   => R_2pi_bivec,     # ~0: product lands on scalar
    "two_pi_rotation_SO3_identity_err" => identity_err_2pi,
)

# ======================================================================
# (C) PIN REFLECTIONS  double-cover O(3)  (MEASURED det = -1)
# ======================================================================
# A single unit vector r reflects across the hyperplane normal to r.
# Read out the 3x3 map; det MUST be -1 (improper).  Anchor: a reflection
# in O(3) has det = -1 by the known invariant.
refl_tests = []
det_refl_all_minus_one = true
for trial in 1:6
    # random unit reflection axis
    a = randn(3); a ./= norm(a)
    r = a[1]*e1 + a[2]*e2 + a[3]*e3        # grade-1, |r|=1 in Cl(3,0,0)
    rn = CliffordAlgebras.scalar(r * CliffordAlgebras.reverse(r))
    @assert abs(rn - 1.0) < 1e-9
    M = induced_O3(r, basis_p)
    d = det(M)
    orth_err = opnorm(M' * M - I)
    if abs(d + 1.0) > 1e-9
        global det_refl_all_minus_one = false
    end
    push!(refl_tests, Dict(
        "axis"=>a, "det"=>d, "ortho_err"=>orth_err,
        "parity_sign"=>versor_parity_sign(r)))
end

# even/odd split: product of TWO reflections is even -> det = +1 (rotation)
a1 = [1.0,0,0]; a2 = randn(3); a2 ./= norm(a2)
r1 = a1[1]*e1 + a1[2]*e2 + a1[3]*e3
r2 = a2[1]*e1 + a2[2]*e2 + a2[3]*e3
two_refl = r1 * r2                          # even versor
M_two = induced_O3(two_refl, basis_p)
det_two_refl = det(M_two)                   # MEASURE: should be +1
parity_two_refl = versor_parity_sign(two_refl)

# three reflections -> odd -> det = -1
a3 = randn(3); a3 ./= norm(a3)
r3 = a3[1]*e1 + a3[2]*e2 + a3[3]*e3
three_refl = r1 * r2 * r3
M_three = induced_O3(three_refl, basis_p)
det_three_refl = det(M_three)               # MEASURE: should be -1
parity_three_refl = versor_parity_sign(three_refl)

RESULTS["pin_reflections"] = Dict(
    "all_det_minus_one"      => det_refl_all_minus_one,
    "tests"                  => refl_tests,
    "two_reflections_det"    => det_two_refl,
    "two_reflections_parity" => parity_two_refl,
    "three_reflections_det"  => det_three_refl,
    "three_reflections_parity" => parity_three_refl,
)

# ======================================================================
# (D) KILL-CONTROL — wrong-structure sandwich must give the NULL result
# ======================================================================
# Genuine reflection: r ODD, twisted conjugation gives det = -1.
# WRONG STRUCTURE 1: take the SAME unit vector r but apply the EVEN
#   (untwisted) conjugation v -> r v r^{-1} *without* the (-1) twist.
#   This is what an even element would induce. It must give det = +1
#   (a rotation by pi, i.e. point reflection composed... a proper map),
#   NOT the improper reflection. If it ALSO gave -1, the det = -1 would
#   be an artifact of the sandwich rather than of the odd sector.
# WRONG STRUCTURE 2: a generic EVEN versor (rotor) forced through the
#   reflection (twisted, odd) formula must NOT give a proper rotation;
#   the twist on an even element produces det = -1, i.e. it does NOT
#   reproduce SO(3). This shows the parity sign is load-bearing.
function induced_O3_forced(u, basis, force_sign::Int)
    uinv = versor_inverse(u)
    cols = Vector{Vector{Float64}}()
    for ej in basis
        img = u * ej * uinv
        img = (force_sign == -1) ? -img : img
        push!(cols, vec3(img))
    end
    return hcat(cols...)
end

# WS1: genuine odd reflection r1, but FORCED even (sign +1)
M_ws1 = induced_O3_forced(r1, basis_p, +1)
det_ws1 = det(M_ws1)        # MEASURE: untwisted conj of a vector -> +1 (proper)
genuine_refl_det = det(induced_O3(r1, basis_p))  # MEASURE: -1

# WS2: genuine even rotor two_refl, but FORCED odd (sign -1)
M_ws2 = induced_O3_forced(two_refl, basis_p, -1)
det_ws2 = det(M_ws2)        # MEASURE: twisted conj of even -> -1 (improper)
genuine_rot_det = det(induced_O3(two_refl, basis_p))  # MEASURE: +1

# WRONG STRUCTURE 3 (non-versor): a NON-Clifford generic linear map is
#   NOT in O(3) at all. If "being an O(3) element" were an artifact of the
#   readout, a random map would also land orthogonal. It must NOT: its
#   ortho-error must be large. This anchors that O(3) membership of the
#   Clifford versors is a MEASURED constraint, not a labeling convention.
Random.seed!(424242)
M_nonversor = randn(3, 3)
nonversor_ortho_err = opnorm(M_nonversor' * M_nonversor - I)   # MEASURE: O(1), >> 0
versor_ortho_err    = opnorm(induced_O3(r1, basis_p)' * induced_O3(r1, basis_p) - I)
# kill: non-versor must be non-orthogonal (>> machine eps) while the genuine
# versor is orthogonal to machine precision. We require >=10 orders of
# magnitude separation, so this is a real measured gap, not a tuned threshold.
kill_nonversor_fails_O3 = nonversor_ortho_err > 1e-2 &&
                          versor_ortho_err    < 1e-10 &&
                          nonversor_ortho_err > 1e8 * max(versor_ortho_err, eps())

# KILL-CONTROL PASS CONDITION:
#   wrong-structure dets must DIFFER from the genuine dets (sign flips),
#   proving the chirality (det sign) tracks the PARITY, not the formula;
#   AND a non-versor must fail O(3) membership while the versor passes.
kill_ws1_distinct = abs(det_ws1 - genuine_refl_det) > 1.0   # +1 vs -1
kill_ws2_distinct = abs(det_ws2 - genuine_rot_det)  > 1.0   # -1 vs +1
kill_control_pass = kill_ws1_distinct && kill_ws2_distinct && kill_nonversor_fails_O3

RESULTS["kill_control"] = Dict(
    "nonversor_ortho_err"     => nonversor_ortho_err,
    "versor_ortho_err"        => versor_ortho_err,
    "kill_nonversor_fails_O3" => kill_nonversor_fails_O3,
    "ws1_forced_even_on_reflection_det" => det_ws1,
    "genuine_reflection_det"            => genuine_refl_det,
    "ws2_forced_odd_on_rotor_det"       => det_ws2,
    "genuine_rotor_det"                 => genuine_rot_det,
    "ws1_flips"                         => kill_ws1_distinct,
    "ws2_flips"                         => kill_ws2_distinct,
    "kill_control_pass"                 => kill_control_pass,
    "note" => "parity sign is load-bearing: wrong parity -> wrong chirality (det)",
)

# ======================================================================
# (E) NEGATIVE / BOUNDARY controls
# ======================================================================
# NEGATIVE: identity versor (scalar 1) -> det = +1, identity map.
M_id = induced_O3(cl.𝟏, basis_p)
neg_identity_det = det(M_id)
neg_identity_err = opnorm(M_id - I)

# BOUNDARY: a reflection axis nearly degenerate (small but nonzero) still
# normalizes to a unit reflection -> still det = -1 (boundary of validity
# is |r| -> 0, which we exclude via the @assert; here we test |r| tiny
# then renormalized).
a_small = [1e-6, 0.0, 0.0]; a_small ./= norm(a_small)
r_small = a_small[1]*e1 + a_small[2]*e2 + a_small[3]*e3
det_boundary = det(induced_O3(r_small, basis_p))

RESULTS["controls"] = Dict(
    "negative_identity_det"  => neg_identity_det,
    "negative_identity_err"  => neg_identity_err,
    "boundary_renormalized_reflection_det" => det_boundary,
)

# ======================================================================
# (F) Z3 — LOAD-BEARING structural check of the parity->det homomorphism
# ======================================================================
# DECORATIVE FORM REMOVED. The old block fed BOTH parity and det in as integer
# LITERALS and asked Not(p==d): the SAT/UNSAT verdict then depended only on the
# two literals (feeding garbage (5,7) was still UNSAT; equal garbage (7,7) was
# UNSAT). That carries zero Clifford content and is not load-bearing.
#
# LOAD-BEARING FORM: encode the O(3) determinant-homomorphism THEORY over FREE
# sign variables --  p,d each constrained to the sign group {-1,+1}, with the
# homomorphism law d == p  --  then pin ONLY the MEASURED parity and let Z3
# DERIVE the det. We assert (d != measured_det) and read the verdict:
#   UNSAT  => the theory FORCES d == measured_det: the measurement obeys the law.
#   SAT    => the theory admits a det != measured_det: the measurement VIOLATES
#             the homomorphism (broken / out-of-group readout) -> NOT proven.
# This verdict FLIPS on the measured det value (a broken det=-1 against parity=+1,
# or a degenerate det=0, returns SAT), so it is genuinely coupled to the geometry.
z3_results = Dict{String,Any}()

# theory: p,d in {-1,+1}, law d==p; pin measured parity, test it forces measured det
function theory_forces_det(measured_parity::Int, measured_det::Int)
    ctx = Z3.Context(); s = Z3.Solver(ctx)
    p = Z3.Const("p", Z3.IntSort(ctx)); d = Z3.Const("d", Z3.IntSort(ctx))
    Z3.add(s, Z3.Or([p == Z3.IntVal(1, ctx), p == Z3.IntVal(-1, ctx)]))  # sign group
    Z3.add(s, Z3.Or([d == Z3.IntVal(1, ctx), d == Z3.IntVal(-1, ctx)]))  # sign group
    Z3.add(s, d == p)                                                    # homomorphism law
    Z3.add(s, p == Z3.IntVal(measured_parity, ctx))                      # ONLY measured input
    Z3.add(s, Z3.Not(d == Z3.IntVal(measured_det, ctx)))                 # negate measured output
    return string(Z3.check(s)) == "unsat"
end

# (F1) genuine versors: measured (parity, det) must be FORCED by the theory (UNSAT).
z3_results["rotation_parity_forces_det_unsat"]   =
    theory_forces_det(parity_two_refl,    Int(round(det_two_refl)))
z3_results["reflection_parity_forces_det_unsat"] =
    theory_forces_det(versor_parity_sign(r1), Int(round(genuine_refl_det)))
z3_results["three_refl_parity_forces_det_unsat"] =
    theory_forces_det(parity_three_refl,  Int(round(det_three_refl)))

# (F2) Pin sign distinction, also load-bearing: encode r^2 in {-1,+1} for a
#      reflection generator and the FACT that a Cl(p,q) generator squares to the
#      signature sign. Pin only the AMBIENT signature, let Z3 derive r^2, and
#      check it matches the MEASURED r^2 (flips if the measurement is wrong).
function signature_forces_rsq(ambient_sign::Int, measured_rsq::Int)
    ctx = Z3.Context(); s = Z3.Solver(ctx)
    sg = Z3.Const("sg", Z3.IntSort(ctx)); rr = Z3.Const("rr", Z3.IntSort(ctx))
    Z3.add(s, Z3.Or([sg == Z3.IntVal(1, ctx), sg == Z3.IntVal(-1, ctx)]))
    Z3.add(s, Z3.Or([rr == Z3.IntVal(1, ctx), rr == Z3.IntVal(-1, ctx)]))
    Z3.add(s, rr == sg)                              # e_i^2 = signature sign
    Z3.add(s, sg == Z3.IntVal(ambient_sign, ctx))    # ONLY the ambient signature
    Z3.add(s, Z3.Not(rr == Z3.IntVal(measured_rsq, ctx)))
    return string(Z3.check(s)) == "unsat"
end
z3_results["pin_plus_rsq_forced_unsat"]  = signature_forces_rsq(+1, Int(round(rsq_plus)))
z3_results["pin_minus_rsq_forced_unsat"] = signature_forces_rsq(-1, Int(round(rsq_minus)))
# and the Pin signs genuinely DIFFER (measured, not literal-compared):
z3_results["pin_signs_distinct_measured"] = (Int(round(rsq_plus)) != Int(round(rsq_minus)))

# (F3) KILL (load-bearing): for the WRONG-structure forced maps the measured parity
#      no longer forces the forced det -> theory_forces_det returns FALSE (SAT).
#      The kill PASSES iff the genuine pairs are forced (UNSAT) but the wrong ones
#      are NOT forced (SAT) -- i.e. the solver SEES the violation.
ws1_forced = theory_forces_det(versor_parity_sign(r1),       Int(round(det_ws1)))  # expect false (SAT)
ws2_forced = theory_forces_det(versor_parity_sign(two_refl), Int(round(det_ws2)))  # expect false (SAT)
z3_results["kill_ws1_violates_law_sat"] = !ws1_forced   # true when Z3 reports the violation
z3_results["kill_ws2_violates_law_sat"] = !ws2_forced

RESULTS["z3"] = z3_results

# ======================================================================
# VERDICT
# ======================================================================
checks = Dict{String,Bool}(
    "pin_sign_distinguishes"        => RESULTS["pin_sign"]["distinguishes"] &&
                                       isapprox(rsq_plus, 1.0) && isapprox(rsq_minus, -1.0),
    "spin_rotations_proper"         => det_rot_all_plus_one && ortho_max_err < 1e-8,
    "spin_match_analytic"           => all(t["match_analytic_SO3_err"] < 1e-8 for t in spin_tests),
    "double_cover_R_negR_same"      => double_cover_same < 1e-8,
    # 2pi cover: the -1 is MEASURED from the product of two genuine pi rotors,
    # each of which is a real 180deg rotation (kill-anchor: NOT identity).
    "pi_rotor_is_real_rotation"     => pi_rotation_not_identity > 1.0,
    "two_pi_versor_is_minus_one"    => isapprox(R_2pi_scalar, -1.0; atol=1e-8) &&
                                       R_2pi_bivec < 1e-8,
    "two_pi_SO3_is_identity"        => identity_err_2pi < 1e-8,
    "reflections_improper"          => det_refl_all_minus_one,
    "two_refl_even_proper"          => isapprox(det_two_refl, 1.0; atol=1e-8) && parity_two_refl == 1,
    "three_refl_odd_improper"       => isapprox(det_three_refl, -1.0; atol=1e-8) && parity_three_refl == -1,
    "kill_control_pass"             => kill_control_pass,
    "kill_nonversor_fails_O3"       => kill_nonversor_fails_O3,
    "neg_identity_proper"           => isapprox(neg_identity_det, 1.0; atol=1e-8) && neg_identity_err < 1e-12,
    "boundary_refl_improper"        => isapprox(det_boundary, -1.0; atol=1e-8),
    # Z3 (load-bearing): theory derives det from measured parity, matches measurement
    "z3_pin_plus_rsq_forced"        => z3_results["pin_plus_rsq_forced_unsat"],
    "z3_pin_minus_rsq_forced"       => z3_results["pin_minus_rsq_forced_unsat"],
    "z3_pin_signs_distinct"         => z3_results["pin_signs_distinct_measured"],
    "z3_rotation_forces_det"        => z3_results["rotation_parity_forces_det_unsat"],
    "z3_reflection_forces_det"      => z3_results["reflection_parity_forces_det_unsat"],
    "z3_three_refl_forces_det"      => z3_results["three_refl_parity_forces_det_unsat"],
    "z3_kill_ws1_violation_seen"    => z3_results["kill_ws1_violates_law_sat"],
    "z3_kill_ws2_violation_seen"    => z3_results["kill_ws2_violates_law_sat"],
)
RESULTS["checks"] = checks
all_pass = all(values(checks))
RESULTS["all_pass"] = all_pass
RESULTS["status_ladder"] = all_pass ? "passes" : "runs"

# Honest status string
n_pass = count(values(checks)); n_tot = length(checks)
RESULTS["honest_status"] = "ran to completion; $n_pass/$n_tot structural checks passed"

# ---- report to stdout ----
println("="^66)
println("G_Pin3_Spin3_chirality — Pin(3)/Spin(3) chirality split (PoC)")
println("="^66)
println("PIN SIGN (measured r^2):")
println("  Pin+  r^2 = $rsq_plus   (expect +1)")
println("  Pin-  r^2 = $rsq_minus   (expect -1)   distinguishes = $(RESULTS["pin_sign"]["distinguishes"])")
println()
println("SPIN(3) = even part, double-covers SO(3):")
println("  all rotation dets = +1 : $det_rot_all_plus_one  (max ortho err $(round(ortho_max_err,sigdigits=3)))")
println("  R vs -R same SO(3)     : diff = $(round(double_cover_same,sigdigits=3))  (2->1 cover)")
println("  pi rotor SO(3) map     : |M_pi - I| = $(round(pi_rotation_not_identity,sigdigits=4))  (real 180deg, NOT identity)")
println("  2pi = (pi rotor)^2     : versor scalar = $R_2pi_scalar (= -1, MEASURED via product;")
println("                           bivec residual = $(round(R_2pi_bivec,sigdigits=3)))  SO(3) id err = $(round(identity_err_2pi,sigdigits=3))")
println()
println("PIN reflections double-cover O(3):")
println("  all reflection dets = -1 : $det_refl_all_minus_one")
println("  2 reflections (even) det = $det_two_refl  parity = $parity_two_refl")
println("  3 reflections (odd)  det = $det_three_refl  parity = $parity_three_refl")
println()
println("KILL-CONTROL (wrong-structure must flip chirality):")
println("  WS1 forced-even on reflection: det = $det_ws1  (genuine = $genuine_refl_det)  flips=$kill_ws1_distinct")
println("  WS2 forced-odd on rotor:       det = $det_ws2  (genuine = $genuine_rot_det)  flips=$kill_ws2_distinct")
println("  WS3 non-versor ortho-err = $(round(nonversor_ortho_err,sigdigits=3)) (versor = $(round(versor_ortho_err,sigdigits=3)))  fails_O3=$kill_nonversor_fails_O3")
println("  kill_control_pass = $kill_control_pass")
println()
println("Z3 LOAD-BEARING checks (theory derives det from measured parity; verdict flips on broken input):")
for (k,v) in sort(collect(z3_results); by=first); println("  $k = $v"); end
println()
println("CONTROLS: neg identity det=$neg_identity_det  boundary refl det=$det_boundary")
println()
println("CHECKS: $n_pass/$n_tot passed")
for (k,v) in sort(collect(checks); by=first)
    println("  ", v ? "PASS" : "FAIL", "  ", k)
end
println()
println("ALL_PASS = $all_pass   status = $(RESULTS["status_ladder"])")
println("honest_status: $(RESULTS["honest_status"])")

# ---- write results json ----
outpath = joinpath(@__DIR__, "pin3_spin3_chirality_clifford_object_results.json")
open(outpath, "w") do io
    JSON.print(io, RESULTS, 2)
end
println("\nwrote $outpath")
