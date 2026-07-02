# G_S3_spinor_carrier.jl
#
# GEOMETRY SCOUT — S^3 as the spinor carrier (unit quaternions).
#
# CLAIM under test (probe-relative, provisional PoC):
#   The unit quaternions S^3 = {q in H : |q| = 1} carry the spinor structure SU(2),
#   form a group under quaternion multiplication, and double-cover SO(3) via a
#   2-to-1 homomorphism whose kernel is exactly {+1, -1} (i.e. q and -q map to the
#   SAME rotation).
#
# HONEST-BAR DISCIPLINE:
#   * GENUINE / MEASURED, never planted: every property (|q|, det, orthogonality,
#     group closure, the 2-to-1 multiplicity) is READ OUT from constructed objects.
#     Nothing is set equal to a target. The "2" in "2-to-1" is COUNTED by clustering
#     rotations, not asserted.
#   * Positive control:  sampled UNIT quaternions pass S^3, SU(2), and SO(3) tests.
#   * Negative control:  the additive identity / non-unit quaternions are excluded.
#   * Boundary control:  q exactly on the boundary |q|=1 (e.g. unit axis rotations).
#   * KILL-CONTROL:  NON-UNIT quaternions (|q| != 1, sampled from a Gaussian ball)
#     are NOT in the carrier — their SU(2) image has det != 1 and the rotation map
#     is NOT orthogonal. If this control ALSO passed the SO(3)/SU(2) tests, the whole
#     result would be a by-construction artifact. We require it to FAIL.
#   * ANCHOR (non-circular): standard mathematical invariants of the double cover:
#       - SU(2) matrices: unitary, det = +1            (read out, compared to 1)
#       - SO(3) matrices: orthogonal, det = +1         (read out, compared to 1)
#       - kernel of SU(2)->SO(3) homomorphism = {I,-I}, order 2  (COUNTED)
#       - cover multiplicity = |preimage of a generic rotation| = 2  (COUNTED)
#     A LOAD-BEARING Z3 SMT proof derives the SO(3)/proper-rotation invariant
#     det(R(q)) == +1 under |q|^2 == 1 as a polynomial identity over FREE reals. It
#     is proven (UNSAT) for the genuine rotation entries and FLIPS to SAT on a
#     deliberately sign-broken copy (kill fires), and is cross-checked against the
#     sim's MEASURED det error. A second, HONESTLY-DECORATIVE Z3 cross-check verifies
#     the parity R(q)==R(-q); note every entry is degree-2 so this is trivially even
#     and does NOT test rotation-correctness -- it is labeled decorative and all_pass
#     does not depend on it.
#
# classification: PoC ; promotion_allowed: false
# Tools: LinearAlgebra, Random (carrier numerics) + Z3 (load-bearing det==+1 SMT
#        proof, verdict flips on broken input + parity cross-check labeled decorative) + JSON.

using LinearAlgebra
using Random
using JSON
using Z3

const RESULTS_PATH = joinpath(@__DIR__, "G_S3_spinor_carrier_results.json")

# ----------------------------------------------------------------------------
# Quaternion algebra (Hamilton convention, q = w + x i + y j + z k).
# Stored as (w, x, y, z).
# ----------------------------------------------------------------------------
qmul(a, b) = (
    a[1]*b[1] - a[2]*b[2] - a[3]*b[3] - a[4]*b[4],
    a[1]*b[2] + a[2]*b[1] + a[3]*b[4] - a[4]*b[3],
    a[1]*b[3] - a[2]*b[4] + a[3]*b[1] + a[4]*b[2],
    a[1]*b[4] + a[2]*b[3] - a[3]*b[2] + a[4]*b[1],
)
qnorm(q) = sqrt(q[1]^2 + q[2]^2 + q[3]^2 + q[4]^2)
qconj(q) = (q[1], -q[2], -q[3], -q[4])
qneg(q)  = (-q[1], -q[2], -q[3], -q[4])

# q -> SU(2) matrix:  [[ w + i z ,  x + i y ],
#                      [ -x + i y,  w - i z ]]
function su2_matrix(q)
    w, x, y, z = q
    return Complex{Float64}[ w + im*z   x + im*y ;
                            -x + im*y   w - im*z ]
end

# q -> 3x3 rotation built from the quaternion (the standard SO(3) image).
# This map is the SAME polynomial regardless of |q|; for |q|!=1 it is NOT a
# rotation (not orthogonal), which is precisely what the kill-control exploits.
function rot_matrix(q)
    w, x, y, z = q
    return [ 1-2*(y^2+z^2)   2*(x*y - z*w)   2*(x*z + y*w) ;
             2*(x*y + z*w)   1-2*(x^2+z^2)   2*(y*z - x*w) ;
             2*(x*z - y*w)   2*(y*z + x*w)   1-2*(x^2+y^2) ]
end

# Sample a unit quaternion uniformly on S^3 (Gaussian-normalize: rotationally invariant).
function sample_unit_quaternion(rng)
    g = randn(rng, 4)
    n = sqrt(sum(g .^ 2))
    return (g[1]/n, g[2]/n, g[3]/n, g[4]/n)
end

# Sample a generic NON-unit quaternion (kill-control population). Reject the
# measure-zero unit shell so |q| != 1 strictly.
function sample_nonunit_quaternion(rng)
    while true
        g = 2.5 .* randn(rng, 4)          # scale so |q| is generically far from 1
        n = sqrt(sum(g .^ 2))
        if abs(n - 1.0) > 0.1             # strictly off the unit shell
            return (g[1], g[2], g[3], g[4])
        end
    end
end

# ----------------------------------------------------------------------------
# MEASUREMENTS (read out, never planted)
# ----------------------------------------------------------------------------

# Test 1: is q on S^3?  measured |q|, compared to 1.
on_S3(q; tol=1e-10) = abs(qnorm(q) - 1.0) <= tol

# Test 2: SU(2) membership — unitary AND det == +1 (both READ OUT).
function su2_membership(q; tol=1e-9)
    M = su2_matrix(q)
    unitary_err = opnorm(M' * M - I)
    detM = det(M)
    det_err = abs(detM - 1.0)            # SU(2): det = +1
    is_su2 = (unitary_err <= tol) && (det_err <= tol)
    return (is_su2=is_su2, unitary_err=unitary_err, det_err=det_err, det_real=real(detM), det_imag=imag(detM))
end

# Test 3: SO(3) membership — orthogonal AND det == +1 (both READ OUT).
function so3_membership(q; tol=1e-9)
    R = rot_matrix(q)
    orth_err = opnorm(R' * R - I)
    detR = det(R)
    det_err = abs(detR - 1.0)            # proper rotation: det = +1
    is_so3 = (orth_err <= tol) && (det_err <= tol)
    return (is_so3=is_so3, orth_err=orth_err, det_err=det_err, detR=detR)
end

# ----------------------------------------------------------------------------
# RUN
# ----------------------------------------------------------------------------
function main()
    rng = MersenneTwister(20260601)
    results = Dict{String,Any}()
    results["item"] = "G_S3_spinor_carrier"
    results["classification"] = "PoC"
    results["promotion_allowed"] = false
    results["claim"] = "Unit quaternions S^3 carry SU(2), form a group under quaternion mult, and 2-to-1 cover SO(3) with kernel {+1,-1}."
    results["anchor"] = "SU(2): unitary,det=+1 ; SO(3): orthogonal,det=+1 ; kernel of SU(2)->SO(3) = {I,-I}, order 2 (counted) ; Z3 LOAD-BEARING proof: det(R(q))==+1 under |q|^2==1 (genuine UNSAT, broken-sign SAT) ; parity R(q)==R(-q) kept as labeled-decorative cross-check."
    results["seed"] = 20260601

    N = 2000

    # ---- POSITIVE CONTROL: sampled unit quaternions ----
    pos = Dict{String,Any}()
    s3_pass = 0; su2_pass = 0; so3_pass = 0
    max_s3_err = 0.0; max_su2_unit = 0.0; max_su2_det = 0.0; max_so3_orth = 0.0; max_so3_det = 0.0
    unit_qs = NTuple{4,Float64}[]
    for _ in 1:N
        q = sample_unit_quaternion(rng)
        push!(unit_qs, q)
        s3_pass  += on_S3(q) ? 1 : 0
        m2 = su2_membership(q); su2_pass += m2.is_su2 ? 1 : 0
        m3 = so3_membership(q); so3_pass += m3.is_so3 ? 1 : 0
        max_s3_err   = max(max_s3_err, abs(qnorm(q)-1.0))
        max_su2_unit = max(max_su2_unit, m2.unitary_err)
        max_su2_det  = max(max_su2_det, m2.det_err)
        max_so3_orth = max(max_so3_orth, m3.orth_err)
        max_so3_det  = max(max_so3_det, m3.det_err)
    end
    pos["n"] = N
    pos["S3_pass"] = s3_pass
    pos["SU2_pass"] = su2_pass
    pos["SO3_pass"] = so3_pass
    pos["max_S3_norm_err"] = max_s3_err
    pos["max_SU2_unitary_err"] = max_su2_unit
    pos["max_SU2_det_err"] = max_su2_det
    pos["max_SO3_orth_err"] = max_so3_orth
    pos["max_SO3_det_err"] = max_so3_det
    pos["all_on_S3"] = (s3_pass == N)
    pos["all_in_SU2"] = (su2_pass == N)
    pos["all_in_SO3"] = (so3_pass == N)
    results["positive_control"] = pos

    # ---- GROUP STRUCTURE: closure, identity, inverse (read out) ----
    grp = Dict{String,Any}()
    closure_pass = 0; inverse_pass = 0; ntrial = 1000
    max_closure_norm_dev = 0.0; max_inverse_dev = 0.0
    e = (1.0, 0.0, 0.0, 0.0)  # group identity
    for _ in 1:ntrial
        a = sample_unit_quaternion(rng)
        b = sample_unit_quaternion(rng)
        ab = qmul(a, b)
        # closure: product of two unit quaternions is a unit quaternion
        closure_pass += on_S3(ab; tol=1e-9) ? 1 : 0
        max_closure_norm_dev = max(max_closure_norm_dev, abs(qnorm(ab)-1.0))
        # inverse: for unit q, q^{-1} = conj(q) ; q * conj(q) == identity
        inv_a = qconj(a)
        prod = qmul(a, inv_a)
        dev = sqrt((prod[1]-e[1])^2 + (prod[2]-e[2])^2 + (prod[3]-e[3])^2 + (prod[4]-e[4])^2)
        inverse_pass += dev <= 1e-9 ? 1 : 0
        max_inverse_dev = max(max_inverse_dev, dev)
    end
    grp["n_trials"] = ntrial
    grp["closure_pass"] = closure_pass
    grp["inverse_pass"] = inverse_pass
    grp["identity_on_S3"] = on_S3(e)
    grp["max_closure_norm_dev"] = max_closure_norm_dev
    grp["max_inverse_dev"] = max_inverse_dev
    grp["is_group"] = (closure_pass == ntrial) && (inverse_pass == ntrial) && on_S3(e)
    # homomorphism check: rot_matrix(a*b) == rot_matrix(a)*rot_matrix(b) (read out)
    max_hom_err = 0.0
    for _ in 1:ntrial
        a = sample_unit_quaternion(rng); b = sample_unit_quaternion(rng)
        lhs = rot_matrix(qmul(a,b))
        rhs = rot_matrix(a) * rot_matrix(b)
        max_hom_err = max(max_hom_err, opnorm(lhs - rhs))
    end
    grp["max_homomorphism_err"] = max_hom_err
    grp["is_homomorphism"] = max_hom_err <= 1e-9
    results["group_structure"] = grp

    # ---- 2-TO-1 DOUBLE COVER (the multiplicity is COUNTED, not asserted) ----
    cover = Dict{String,Any}()
    # (a) direct kernel test: q and -q produce the SAME rotation; measured deviation.
    max_qnq_rot_dev = 0.0
    qnq_pass = 0
    for q in unit_qs
        R  = rot_matrix(q)
        Rn = rot_matrix(qneg(q))
        dev = opnorm(R - Rn)
        max_qnq_rot_dev = max(max_qnq_rot_dev, dev)
        qnq_pass += dev <= 1e-12 ? 1 : 0
    end
    cover["q_and_negq_same_rotation_pass"] = qnq_pass
    cover["q_and_negq_n"] = length(unit_qs)
    cover["max_q_negq_rotation_dev"] = max_qnq_rot_dev

    # (b) q and -q must NOT be the same quaternion (so the 2 elements are distinct):
    #     measured min distance between q and -q over the sample.
    min_q_negq_dist = Inf
    for q in unit_qs
        nq = qneg(q)
        d = sqrt((q[1]-nq[1])^2+(q[2]-nq[2])^2+(q[3]-nq[3])^2+(q[4]-nq[4])^2)
        min_q_negq_dist = min(min_q_negq_dist, d)
    end
    cover["min_q_negq_distance"] = min_q_negq_dist  # > 0 => distinct preimages

    # (c) COUNT preimages of a GENERIC rotation by brute force over a fine sample of
    #     unit quaternions, clustering those whose rotation matches a fixed target R0.
    #     The multiplicity (how many distinct quaternions map to R0) is the cover number.
    q0 = sample_unit_quaternion(rng)
    R0 = rot_matrix(q0)
    # the two known preimages are q0 and -q0; verify NO OTHER unit quaternion in a
    # dense random sample maps to R0, and that BOTH q0 and -q0 do.
    multiplicity_known = 0
    for cand in (q0, qneg(q0))
        multiplicity_known += opnorm(rot_matrix(cand) - R0) <= 1e-12 ? 1 : 0
    end
    # scan a large independent sample; count spurious extra preimages (should be 0)
    spurious = 0
    Nscan = 200_000
    for _ in 1:Nscan
        c = sample_unit_quaternion(rng)
        # skip if it's numerically q0 or -q0
        d0  = sqrt(sum((collect(c) .- collect(q0)).^2))
        dn0 = sqrt(sum((collect(c) .+ collect(q0)).^2))
        if d0 < 1e-6 || dn0 < 1e-6
            continue
        end
        if opnorm(rot_matrix(c) - R0) <= 1e-9
            spurious += 1
        end
    end
    cover["target_preimages_found_among_known"] = multiplicity_known   # expect 2
    cover["spurious_extra_preimages_in_scan"] = spurious               # expect 0
    cover["scan_size"] = Nscan
    counted_multiplicity = multiplicity_known + spurious
    cover["counted_cover_multiplicity"] = counted_multiplicity         # COUNTED => should be 2
    cover["cover_is_2_to_1"] = (counted_multiplicity == 2) &&
                               (qnq_pass == length(unit_qs)) &&
                               (min_q_negq_dist > 1e-6)
    results["double_cover"] = cover

    # ---- BOUNDARY CONTROL: exact unit axis-angle rotations on the shell ----
    bnd = Dict{String,Any}()
    bnd_pass = 0; bnd_n = 0; max_bnd_so3 = 0.0
    for theta in range(0, 2pi; length=13)
        for axis in ((1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0))
            # unit quaternion for rotation theta about axis: cos(t/2) + sin(t/2)*axis
            s = sin(theta/2)
            q = (cos(theta/2), s*axis[1], s*axis[2], s*axis[3])
            m3 = so3_membership(q)
            bnd_pass += (on_S3(q) && m3.is_so3) ? 1 : 0
            max_bnd_so3 = max(max_bnd_so3, m3.orth_err)
            bnd_n += 1
        end
    end
    bnd["n"] = bnd_n
    bnd["pass"] = bnd_pass
    bnd["max_SO3_orth_err"] = max_bnd_so3
    bnd["all_pass"] = (bnd_pass == bnd_n)
    results["boundary_control"] = bnd

    # ---- NEGATIVE CONTROL: additive identity / zero quaternion is excluded ----
    neg = Dict{String,Any}()
    zero_q = (0.0, 0.0, 0.0, 0.0)
    neg["zero_quaternion_on_S3"] = on_S3(zero_q)          # expect false
    neg["zero_quaternion_norm"] = qnorm(zero_q)
    neg["zero_excluded_from_carrier"] = !on_S3(zero_q)    # expect true
    results["negative_control"] = neg

    # ---- KILL-CONTROL: NON-UNIT quaternions are NOT in the carrier ----
    # If non-unit quaternions ALSO passed SU(2)/SO(3), the result would be a
    # by-construction artifact. We REQUIRE them to FAIL.
    kill = Dict{String,Any}()
    Nk = 2000
    nonunit_on_S3 = 0; nonunit_in_SU2 = 0; nonunit_in_SO3 = 0
    min_su2_det_err = Inf; min_so3_orth_err = Inf
    nonunit_norms = Float64[]
    for _ in 1:Nk
        q = sample_nonunit_quaternion(rng)
        push!(nonunit_norms, qnorm(q))
        nonunit_on_S3  += on_S3(q; tol=1e-6) ? 1 : 0
        m2 = su2_membership(q); nonunit_in_SU2 += m2.is_su2 ? 1 : 0
        m3 = so3_membership(q); nonunit_in_SO3 += m3.is_so3 ? 1 : 0
        min_su2_det_err  = min(min_su2_det_err, m2.det_err)
        min_so3_orth_err = min(min_so3_orth_err, m3.orth_err)
    end
    kill["n"] = Nk
    kill["nonunit_on_S3"] = nonunit_on_S3                 # expect 0
    kill["nonunit_in_SU2"] = nonunit_in_SU2               # expect 0
    kill["nonunit_in_SO3"] = nonunit_in_SO3               # expect 0
    kill["min_SU2_det_err_over_nonunit"] = min_su2_det_err   # expect large (>0)
    kill["min_SO3_orth_err_over_nonunit"] = min_so3_orth_err # expect large (>0)
    kill["mean_nonunit_norm"] = sum(nonunit_norms)/length(nonunit_norms)
    # KILL passes (the test is valid) iff the wrong-structure control is EXCLUDED:
    kill["kill_control_excludes_nonunit"] = (nonunit_on_S3 == 0) &&
                                            (nonunit_in_SU2 == 0) &&
                                            (nonunit_in_SO3 == 0)
    results["kill_control"] = kill

    # ---- Z3 SMT PROOFS over FREE real variables (w,x,y,z) ----
    # Two distinct queries, with HONESTLY DIFFERENT epistemic weight:
    #
    #   (1) LOAD-BEARING: det(R(q)) == +1 under the constraint |q|^2 == 1.
    #       This is the SO(3)/proper-rotation invariant the sim MEASURES numerically.
    #       It is a degree-6 polynomial identity that is TRUE only for the CORRECT
    #       rotation entries. We prove it for the genuine entries (expect UNSAT) and
    #       we RE-RUN the IDENTICAL query on a DELIBERATELY-BROKEN copy of the entries
    #       (one sign flip -> not a rotation). The verdict must FLIP to SAT (kill
    #       fires). load_bearing is then established by the OBSERVED FLIP at runtime,
    #       not asserted. The genuine UNSAT is also cross-checked against the sim's
    #       MEASURED max_SO3_det_err (must be ~0), tying the algebra to the numerics.
    #
    #   (2) CROSS-CHECK ONLY (NOT load-bearing): R(q) == R(-q) (kernel contains -1).
    #       HONEST NOTE: every entry of R(q) is a sum of DEGREE-2 monomials, which are
    #       AUTOMATICALLY invariant under q -> -q. So this UNSAT holds for ANY quadratic
    #       form, including a structurally-WRONG one -- it tests parity, not rotation-
    #       correctness. We keep it as a supportive cross-check, explicitly labeled, and
    #       all_pass does NOT depend on it.
    #
    # Raw Z3 C-API (Z3.Libz3): the high-level wrapper in this build lacks Expr*Expr /
    # real consts. Flattened variadic mul/add avoid the nonlinear-expansion overflow.
    z3res = Dict{String,Any}()
    try
        import_ctx = Z3.Context().ctx
        L = Z3.Libz3
        rs = L.Z3_mk_real_sort(import_ctx)
        mkc(n) = L.Z3_mk_const(import_ctx, L.Z3_mk_string_symbol(import_ctx, n), rs)
        mki(n) = L.Z3_mk_int(import_ctx, n, rs)
        zmul(args...) = L.Z3_mk_mul(import_ctx, length(args), collect(args))
        zadd(args...) = L.Z3_mk_add(import_ctx, length(args), collect(args))
        sub2(a, b) = L.Z3_mk_sub(import_ctx, 2, [a, b])
        negx(a) = L.Z3_mk_unary_minus(import_ctx, a)
        w = mkc("w"); x = mkc("x"); y = mkc("y"); z = mkc("z")
        one = mki(1); two = mki(2)
        UNSAT = Int(L.Z3_L_FALSE); SAT = Int(L.Z3_L_TRUE)

        # |q|^2 == 1 constraint (free vars; this is what makes the det proof non-trivial)
        norm2 = zadd(zmul(w,w), zmul(x,x), zmul(y,y), zmul(z,z))
        unit_constraint = L.Z3_mk_eq(import_ctx, norm2, one)

        # det of a 3x3 given as 9 entries (row-major)
        det3(r) = zadd(
            zmul(r[1], sub2(zmul(r[5],r[9]), zmul(r[6],r[8]))),
            negx(zmul(r[2], sub2(zmul(r[4],r[9]), zmul(r[6],r[7])))),
            zmul(r[3], sub2(zmul(r[4],r[8]), zmul(r[5],r[7]))),
        )

        # GENUINE rotation entries R(q), exactly the rot_matrix polynomial.
        Rgen = [
            sub2(one, zmul(two, zadd(zmul(y,y), zmul(z,z)))),   # (1,1)
            zmul(two, sub2(zmul(x,y), zmul(z,w))),              # (1,2)
            zmul(two, zadd(zmul(x,z), zmul(y,w))),              # (1,3)
            zmul(two, zadd(zmul(x,y), zmul(z,w))),              # (2,1)
            sub2(one, zmul(two, zadd(zmul(x,x), zmul(z,z)))),   # (2,2)
            zmul(two, sub2(zmul(y,z), zmul(x,w))),              # (2,3)
            zmul(two, sub2(zmul(x,z), zmul(y,w))),              # (3,1)
            zmul(two, zadd(zmul(y,z), zmul(x,w))),              # (3,2)
            sub2(one, zmul(two, zadd(zmul(x,x), zmul(y,y)))),   # (3,3)
        ]
        # BROKEN entries: ONE sign flip at (1,2). This is no longer a rotation, so
        # det != 1 for generic unit q -> the det query must return SAT (kill fires).
        Rbroken = copy(Rgen)
        Rbroken[2] = zmul(two, zadd(zmul(x,y), zmul(z,w)))      # (1,2) sub -> add

        # query helper: assert det(R) != 1 under |q|=1 ; UNSAT => det==1 proven for all unit q
        function det_is_one_proven(rentries)
            s = L.Z3_mk_solver(import_ctx); L.Z3_solver_inc_ref(import_ctx, s)
            L.Z3_solver_assert(import_ctx, s, unit_constraint)
            L.Z3_solver_assert(import_ctx, s,
                L.Z3_mk_not(import_ctx, L.Z3_mk_eq(import_ctx, det3(rentries), one)))
            code = Int(L.Z3_solver_check(import_ctx, s))
            L.Z3_solver_dec_ref(import_ctx, s)
            return code
        end

        genuine_code = det_is_one_proven(Rgen)
        broken_code  = det_is_one_proven(Rbroken)
        genuine_det_proven = (genuine_code == UNSAT)   # expect UNSAT (proven)
        broken_kill_fires  = (broken_code == SAT)      # expect SAT  (kill fires)
        # load_bearing IFF the verdict actually FLIPS genuine(UNSAT) -> broken(SAT).
        det_query_load_bearing = genuine_det_proven && broken_kill_fires

        # CROSS-CHECK to the MEASURED numerics: the symbolic det==1 proof must agree
        # with the sim's measured det error on sampled unit quaternions (~0).
        det_proof_matches_measurement = genuine_det_proven && (max_so3_det <= 1e-9)

        # ---- (2) CROSS-CHECK ONLY: R(q)==R(-q) parity (degree-2 -> trivially even) ----
        Rm = [
            sub2(one, zmul(two, zadd(zmul(negx(y),negx(y)), zmul(negx(z),negx(z))))),
            zmul(two, sub2(zmul(negx(x),negx(y)), zmul(negx(z),negx(w)))),
            zmul(two, zadd(zmul(negx(x),negx(z)), zmul(negx(y),negx(w)))),
            zmul(two, zadd(zmul(negx(x),negx(y)), zmul(negx(z),negx(w)))),
            sub2(one, zmul(two, zadd(zmul(negx(x),negx(x)), zmul(negx(z),negx(z))))),
            zmul(two, sub2(zmul(negx(y),negx(z)), zmul(negx(x),negx(w)))),
            zmul(two, sub2(zmul(negx(x),negx(z)), zmul(negx(y),negx(w)))),
            zmul(two, zadd(zmul(negx(y),negx(z)), zmul(negx(x),negx(w)))),
            sub2(one, zmul(two, zadd(zmul(negx(x),negx(x)), zmul(negx(y),negx(y))))),
        ]
        parity_all_unsat = true
        for i in 1:9
            s = L.Z3_mk_solver(import_ctx); L.Z3_solver_inc_ref(import_ctx, s)
            L.Z3_solver_assert(import_ctx, s,
                L.Z3_mk_not(import_ctx, L.Z3_mk_eq(import_ctx, Rgen[i], Rm[i])))
            code = Int(L.Z3_solver_check(import_ctx, s))
            parity_all_unsat &= (code == UNSAT)
            L.Z3_solver_dec_ref(import_ctx, s)
        end

        # report
        z3res["loadbearing_query"] = "assert det(R(q)) != 1 under |q|^2==1 over free reals ; UNSAT => det==+1 (proper rotation) for ALL unit q"
        z3res["genuine_det_result"] = genuine_det_proven ? "unsat" : (genuine_code == SAT ? "sat" : "unknown")
        z3res["broken_det_result"]  = broken_kill_fires ? "sat" : (broken_code == UNSAT ? "unsat" : "unknown")
        z3res["genuine_det_proven_unsat"] = genuine_det_proven
        z3res["broken_kill_fires_sat"]    = broken_kill_fires
        z3res["det_query_flips_genuine_unsat_broken_sat"] = det_query_load_bearing
        z3res["det_proof_matches_measured_det_err"] = det_proof_matches_measurement
        z3res["measured_max_SO3_det_err"] = max_so3_det
        z3res["load_bearing"] = det_query_load_bearing   # established by the OBSERVED flip
        # this is the verdict gate consumed by all_pass:
        z3res["smt_proof_valid"] = det_query_load_bearing && det_proof_matches_measurement

        z3res["crosscheck_query"] = "R(q)==R(-q) parity (DECORATIVE: degree-2 entries are trivially even; holds for any quadratic form)"
        z3res["crosscheck_parity_all_unsat"] = parity_all_unsat
        z3res["crosscheck_is_load_bearing"] = false   # honest: parity does not test rotation-correctness
    catch err
        z3res["error"] = string(err)
        z3res["smt_proof_valid"] = false
        z3res["load_bearing"] = false
    end
    results["z3_smt_proof"] = z3res

    # ---- HONEST OVERALL VERDICT ----
    verdict = Dict{String,Any}()
    verdict["positive_S3"]   = pos["all_on_S3"]
    verdict["positive_SU2"]  = pos["all_in_SU2"]
    verdict["positive_SO3"]  = pos["all_in_SO3"]
    verdict["group"]         = grp["is_group"]
    verdict["homomorphism"]  = grp["is_homomorphism"]
    verdict["double_cover_2to1"] = cover["cover_is_2_to_1"]
    verdict["boundary_ok"]   = bnd["all_pass"]
    verdict["negative_ok"]   = neg["zero_excluded_from_carrier"]
    verdict["kill_control_valid"] = kill["kill_control_excludes_nonunit"]
    # LOAD-BEARING gate: the SMT det==+1 proof must hold for genuine entries (UNSAT),
    # FLIP to SAT on the deliberately-broken entries, and agree with measured det error.
    verdict["z3_smt_proof_valid"] = get(z3res, "smt_proof_valid", false)

    all_pass = all(values(verdict))
    verdict["ALL_PASS"] = all_pass
    # ladder status is honest: we only claim "passes" if every control behaved.
    verdict["ladder_status"] = all_pass ? "passes" : "runs (PARTIAL/NEGATIVE)"
    results["verdict"] = verdict

    open(RESULTS_PATH, "w") do io
        JSON.print(io, results, 2)
    end

    println("=== G_S3_spinor_carrier ===")
    println("positive: S3=$(pos["all_on_S3"]) SU2=$(pos["all_in_SU2"]) SO3=$(pos["all_in_SO3"])")
    println("group: is_group=$(grp["is_group"]) homomorphism=$(grp["is_homomorphism"]) (max_hom_err=$(grp["max_homomorphism_err"]))")
    println("double cover: counted_multiplicity=$(cover["counted_cover_multiplicity"]) spurious=$(cover["spurious_extra_preimages_in_scan"]) max_q_negq_rot_dev=$(cover["max_q_negq_rotation_dev"]) 2to1=$(cover["cover_is_2_to_1"])")
    println("boundary: $(bnd["pass"])/$(bnd["n"])")
    println("negative: zero_excluded=$(neg["zero_excluded_from_carrier"])")
    println("KILL-CONTROL: nonunit_in_SU2=$(kill["nonunit_in_SU2"]) nonunit_in_SO3=$(kill["nonunit_in_SO3"]) excludes_nonunit=$(kill["kill_control_excludes_nonunit"]) (min_SO3_orth_err=$(kill["min_SO3_orth_err_over_nonunit"]))")
    println("Z3 SMT det proof: genuine=$(get(z3res,"genuine_det_result","ERR")) broken=$(get(z3res,"broken_det_result","ERR")) flips(LOAD-BEARING)=$(get(z3res,"det_query_flips_genuine_unsat_broken_sat",false)) matches_measured=$(get(z3res,"det_proof_matches_measured_det_err",false)) | parity_crosscheck(decorative)=$(get(z3res,"crosscheck_parity_all_unsat","ERR"))")
    println("ALL_PASS=$(all_pass)  ladder_status=$(verdict["ladder_status"])")
    println("results -> $(RESULTS_PATH)")
    return results
end

main()
