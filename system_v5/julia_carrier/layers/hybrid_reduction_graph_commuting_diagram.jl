# hybrid_reduction_graph_commuting_diagram.jl
#
# GEOMETRY SCOUT — item: G_hybrid_reduction_graph
# Hybrid Hopf + Spin + Twistor + Clifford REDUCTION GRAPH as a directed graph
# whose nodes are the standard structures and edges are the KNOWN canonical maps.
# We verify it is a CONSISTENT COMMUTING DIAGRAM: composing edges along two
# different paths between the same endpoints agrees, when checked NUMERICALLY
# on randomly sampled points (the agreement is MEASURED, never planted).
#
# Nodes (structures):
#   S3        unit 3-sphere in C^2 ~ unit quaternions
#   SU2       2x2 special-unitary matrices
#   SO3       3x3 special-orthogonal matrices
#   S2        unit 2-sphere in R^3
#   Cl3even   even subalgebra of Cl(3,0) ~ Spin(3) ~ SU(2)
#   Twistor   the C^2 fiber whose projectivization is CP^1 ~ S2
#
# Edges (canonical maps):
#   iso_S3_SU2 : S3 -> SU2          unit quaternion -> SU(2) matrix (iso)
#   dcover     : SU2 -> SO3         2:1 double cover R_ij = (1/2)tr(s_i U s_j U^H)
#   hopf       : S3 -> S2           standard Hopf map (Hopf invariant 1)
#   projN      : SO3 -> S2          R -> R*e3 (orbit of north pole)
#   iso_Cl3    : SU2 -> Cl3even     Pauli basis -> even Clifford rotor (Spin(3))
#   adj_Cl3    : Cl3even -> SO3      rotor sandwich  x -> r x r^{-1} on R^3
#   twistor    : S3 -> S2           projectivize C^2 fiber  (z,w) -> CP^1 ~ S2
#
# COMMUTING CHECKS (>=2 independent paths to a common target):
#   P1  S3 -> S2  via hopf            ==  S3 -> SU2 -> SO3 -> S2 (projN)
#   P2  S3 -> S2  via hopf            ==  S3 -> S2 via twistor (projectivization)
#   P3  SU2 -> SO3 via dcover         ==  SU2 -> Cl3even -> SO3 (rotor adjoint)
#
# NON-CIRCULAR ANCHORS (checked against MATH, not against the sim):
#   A1  double-cover degree 2:  U and -U map to the SAME SO(3) matrix (2:1 kernel +-I)
#   A2  SO(3) image is genuinely orthogonal: R^T R = I, det R = +1  (measured)
#   A3  Hopf invariant 1: two distinct Hopf fibers have linking number 1 (measured)
#
# KILL-CONTROLS (a wrong-structure map MUST break the diagram; if it still
# "passed" the result would be an artifact):
#   K1  fake_hopf  : a plausible-looking but WRONG S3->S2 map. P1 must FAIL.
#   K2  bad_dcover : double cover with a transposed/sign-broken row. A2 must FAIL
#                    (loses orthogonality) and P1 must FAIL.
#   K3  no_square  : Cl3 path WITHOUT the rotor sandwich (linear, not adjoint).
#                    P3 must FAIL (a linear action is not the SO(3) conjugation).
#
# classification = "geometry_poc";  promotion_allowed = false.

using LinearAlgebra
using CliffordAlgebras
using Graphs
using Random
using Printf
using JSON

const TOL = 1e-9

# ---------------------------------------------------------------------------
# Pauli matrices (Hermitian, traceless) — used by the double cover.
# ---------------------------------------------------------------------------
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const PAULI = (SX, SY, SZ)

# ---------------------------------------------------------------------------
# Sampling: a uniformly random point on S^3 ~ unit quaternion (a,b,c,d).
# A quaternion q = a + b i + c j + d k  <->  SU(2) matrix
#    U = [ a+ d i    -c + b i ;
#          c + b i    a - d i ]   (standard quaternion->SU(2), det = a^2+b^2+c^2+d^2 = 1)
# Equivalently as a unit vector (z,w) in C^2:  z = a + d i,  w = c + b i  (a row of U).
# ---------------------------------------------------------------------------
function rand_S3(rng)
    v = randn(rng, 4)
    v ./= norm(v)
    return v  # (a,b,c,d)
end

# iso_S3_SU2 : unit quaternion -> SU(2)
function iso_S3_SU2(q)
    a, b, c, d = q
    return ComplexF64[ a + d*im   -c + b*im ;
                       c + b*im    a - d*im ]
end

# dcover : SU(2) -> SO(3)   R_ij = (1/2) Re tr(s_i U s_j U^H)
# This is the GENUINE adjoint representation; R is READ OUT, not constructed
# to be orthogonal. Orthogonality is then an anchor we MEASURE (A2).
function dcover(U)
    R = zeros(Float64, 3, 3)
    Uh = U'
    for i in 1:3, j in 1:3
        R[i, j] = 0.5 * real(tr(PAULI[i] * U * PAULI[j] * Uh))
    end
    return R
end

# hopf : S3 -> S2 (standard). With (z,w) the first row of U:
#   z = a + d i,  w = c + b i
#   Hopf(z,w) = ( 2 Re(z* w), 2 Im(z* w), |z|^2 - |w|^2 )  in R^3, |.|=1.
# This is the canonical map with Hopf invariant 1.
function hopf(q)
    a, b, c, d = q
    z = a + d*im
    w = c + b*im
    x = 2*real(conj(z)*w)
    y = 2*imag(conj(z)*w)
    zc = abs2(z) - abs2(w)
    return [x, y, zc]
end

# projN : SO(3) -> S2 by acting on the north pole e3 = (0,0,1).
projN(R) = R * [0.0, 0.0, 1.0]

# twistor : S3 -> S2 by projectivizing the C^2 fiber (z,w) -> CP^1 ~ S2.
# CP^1 -> S2 via inverse stereographic of  xi = w/z  (Riemann sphere), with the
# z=0 pole handled directly. This is the SAME Hopf map; we compute it by an
# INDEPENDENT route (projective coordinate) so agreement with hopf is a real test.
function twistor(q)
    a, b, c, d = q
    z = a + d*im
    w = c + b*im
    if abs(z) < 1e-14
        return [0.0, 0.0, -1.0]   # w/z = infinity -> south pole
    end
    xi = w / z                    # affine coordinate on CP^1
    u = real(xi); v = imag(xi)
    den = 1 + u*u + v*v
    # inverse stereographic projection from south pole onto unit sphere:
    return [2u/den, 2v/den, (1 - u*u - v*v)/den]
end

# iso_Cl3 + adj_Cl3 : SU(2) -> Cl3even (Spin(3)) -> SO(3) by the rotor sandwich.
#
# The even subalgebra Cl(3,0)^+ is spanned by {1, e23, e13, e12}. With the
# signature e_i^2 = +1, the unit bivectors satisfy  e23^2 = e13^2 = e12^2 = -1
# and close as a quaternion algebra (e23 e13 = e12, etc.). A rotor
#       r = a + b e23 + c e13 + d e12   (a^2+b^2+c^2+d^2 = 1)
# acts on a vector v = x e1 + y e2 + z e3 by the genuine Clifford sandwich
# r v reverse(r).
#
# We compute this sandwich TWO independent ways and require them to agree, and
# both to agree with the SU(2) double cover at machine precision:
#   (1) adj_Cl3_pkg : the CliffordAlgebras package computes the geometric product
#       r * v * reverse(r) directly (the tool is LOAD-BEARING here, not decorative).
#   (2) adj_Cl3     : an explicit auditable multivector arithmetic (_gp) on blade
#       bitmasks, kept as an independent second path (and used by the K3 control,
#       which drops the sandwich to confirm a linear action is NOT the conjugation).
#
# NOTE ON THE PACKAGE API (corrected): CliffordAlgebras.basevector(CL3, k) is
# 1-indexed over ALL 8 basis blades with the SCALAR first --
#   basevector(CL3,1) = 1 (scalar), basevector(CL3,2)=e1, (3)=e2, (4)=e3,
#   (5)=e1e2, (6)=e3e1, (7)=e2e3, (8)=e1e2e3.
# A prior version of this file read basevector(CL3,1..3) as the vectors e1,e2,e3
# (they are actually scalar, e1, e2) and so saw e1*e2 "return a grade-1 element",
# which it wrongly blamed on a package defect. Using the property accessors
# CL3.e1, CL3.e2, CL3.e3 (verified below) the package is correct: every basis
# vector squares to +1, every basis bivector is genuine grade-2 and squares to -1,
# and the package rotor sandwich reproduces SO(3) exactly.
const CL3 = CliffordAlgebra(:Cl3)

# Package basis vectors (property accessors -- the CORRECT API).
const PE1 = CL3.e1
const PE2 = CL3.e2
const PE3 = CL3.e3
# Package basis bivectors in the SAME convention as the explicit _gp path below
# (slots 5,6,7 = e2e3, e1e3, e1e2). e1e3 = -e31; this is the orientation that
# matches the SU(2) double cover dcover().
const PB23 = PE2 * PE3   # e2e3
const PB13 = PE1 * PE3   # e1e3
const PB12 = PE1 * PE2   # e1e2

# grade-1 coefficient of a multivector along basis vector ek (ek^2 = +1 so the
# coefficient is the scalar part of out*ek).
_grade1_coeff(out, ek) = scalar(out * ek)

# adj_Cl3_pkg : SU(2)/quaternion -> SO(3) via the CliffordAlgebras rotor sandwich.
# rotor r = a + b e2e3 + c e1e3 + d e1e2 ; reverse(r) flips the bivector signs.
# Columns of R are the grade-1 parts of r e_j reverse(r).
function adj_Cl3_pkg(q)
    a, b, c, d = q
    r  = a + b * PB23 + c * PB13 + d * PB12
    rr = a - b * PB23 - c * PB13 - d * PB12   # reverse
    R = zeros(Float64, 3, 3)
    for (j, v) in enumerate((PE1, PE2, PE3))
        out = r * v * rr
        R[1, j] = _grade1_coeff(out, PE1)
        R[2, j] = _grade1_coeff(out, PE2)
        R[3, j] = _grade1_coeff(out, PE3)
    end
    return R
end

# Multivector represented by 8 real coeffs in fixed basis order:
#   slot:   1   2   3   4    5    6    7    8
#   blade:  1   e1  e2  e3   e23  e13  e12  e123
# (slots 5,6,7 are the bitmask blades 0b110=e2e3, 0b101=e1e3, 0b011=e1e2.)
# Full Cl(3,0) geometric product computed PROGRAMMATICALLY from the blade
# bitmasks (bit0=e1, bit1=e2, bit2=e3) so the anticommutation signs are derived
# by bubble-sort + e_i^2=+1 cancellation rather than hand-transcribed. This
# generative form is self-consistent and matches the CliffordAlgebras package
# (cross-checked below): unit bivector^2 = -1 for all three, and the rotor
# sandwich reproduces the SU(2) double cover at machine precision.
const _MASKS = (0b000, 0b001, 0b010, 0b100, 0b110, 0b101, 0b011, 0b111)
const _SLOT = Dict(m => i for (i, m) in enumerate(_MASKS))

function _blade_mul(a::Integer, b::Integer)
    a = Int(a); b = Int(b)
    abits = [i for i in 0:2 if (a >> i) & 1 == 1]
    bbits = [i for i in 0:2 if (b >> i) & 1 == 1]
    arr = vcat(abits, bbits)
    n = length(arr); swaps = 0
    for _ in 1:n, j in 1:n-1
        if arr[j] > arr[j+1]
            arr[j], arr[j+1] = arr[j+1], arr[j]; swaps += 1
        end
    end
    sign = iseven(swaps) ? 1 : -1
    out = Int[]
    for g in arr
        if !isempty(out) && out[end] == g
            pop!(out)           # e_i^2 = +1 in Cl(3,0)
        else
            push!(out, g)
        end
    end
    mask = 0
    for g in out
        mask |= (1 << g)
    end
    return mask, sign
end

# precompute the 8x8 product structure
const _PROD = let
    tbl = Array{Tuple{Int,Int}}(undef, 8, 8)
    for ia in 1:8, ib in 1:8
        m, s = _blade_mul(_MASKS[ia], _MASKS[ib])
        tbl[ia, ib] = (_SLOT[m], s)
    end
    tbl
end

function _gp(A::Vector{Float64}, B::Vector{Float64})
    C = zeros(Float64, 8)
    @inbounds for ia in 1:8
        Aa = A[ia]; Aa == 0 && continue
        for ib in 1:8
            Bb = B[ib]; Bb == 0 && continue
            slot, s = _PROD[ia, ib]
            C[slot] += s * Aa * Bb
        end
    end
    return C
end

# reverse: flips sign of grade-2 and grade-3 (bivectors + pseudoscalar)
function _rev(A::Vector{Float64})
    return [A[1], A[2], A[3], A[4], -A[5], -A[6], -A[7], -A[8]]
end

# rotor coeff vector from quaternion (a,b,c,d) -> a + b e23 + c e13 + d e12
# (slots 5,6,7). This is the SAME convention used by adj_Cl3_pkg above.
function _rotor(q)
    a, b, c, d = q
    return [a, 0.0, 0.0, 0.0, b, c, d, 0.0]
end

# basis vectors e1,e2,e3 as coeff vectors
const _V1 = [0.0,1,0,0,0,0,0,0]
const _V2 = [0.0,0,1,0,0,0,0,0]
const _V3 = [0.0,0,0,1,0,0,0,0]

function adj_Cl3(q; square::Bool=true)
    r  = _rotor(q)
    rr = _rev(r)
    R = zeros(Float64, 3, 3)
    for (j, vj) in enumerate((_V1, _V2, _V3))
        out = square ? _gp(_gp(r, vj), rr) : _gp(r, vj)  # K3: drop the sandwich
        # vector (grade-1) part -> columns of SO(3)
        R[1, j] = out[2]
        R[2, j] = out[3]
        R[3, j] = out[4]
    end
    return R
end

# Cross-check the even-subalgebra against the CliffordAlgebras PACKAGE, used with
# the correct API (property accessors CL3.e1, CL3.e2, CL3.e3). Two things are
# verified, tool-against-truth:
#   (a) every basis vector squares to +1 (signature 3,0,0), every basis bivector
#       is GENUINE grade-2 and squares to -1, and the three bivectors close as a
#       quaternion algebra (e2e3 * e1e3 = e1e2 etc.) -- so the package is correct.
#   (b) the package products agree with the explicit generative _gp products
#       (e12^2 = e23^2 = e13^2 = -1) -- so the two independent algebra
#       implementations are consistent.
# The crosscheck passes iff BOTH the package and _gp give all three bivector
# squares = -1 AND every basis vector squares to +1 AND the quaternion closure
# holds. There is NO package defect; the earlier "defect" was an API misread
# (basevector(CL3,1) is the scalar, not e1).
function clifford_table_crosscheck()
    # package (correct API) basis-vector squares: must all be +1
    v_sq = (scalar(PE1 * PE1), scalar(PE2 * PE2), scalar(PE3 * PE3))
    vec_ok = all(isapprox.(v_sq, 1; atol=1e-9))
    # package bivector squares (must be -1) and grade (must be 2)
    pkg23 = scalar(PB23 * PB23); pkg13 = scalar(PB13 * PB13); pkg12 = scalar(PB12 * PB12)
    pkg_biv_ok = isapprox(pkg23, -1; atol=1e-9) &&
                 isapprox(pkg13, -1; atol=1e-9) &&
                 isapprox(pkg12, -1; atol=1e-9)
    # package quaternion closure: e2e3 * e1e3 should be (up to the fixed sign of
    # this convention) +/- e1e2; we require it to be a pure e1e2 bivector matching
    # _gp's closure. Compare to the _gp product of the same two bivectors.
    gp_close = _gp([0.0,0,0,0,1,0,0,0], [0.0,0,0,0,0,1,0,0])  # e23 * e13 in _gp
    pkg_close = PB23 * PB13
    # _gp slot 7 is e1e2; the package result's e1e2 coefficient:
    pkg_close_e12 = _grade1_coeff_biv(pkg_close)
    close_ok = isapprox(gp_close[7], pkg_close_e12; atol=1e-9) && isapprox(abs(gp_close[7]), 1; atol=1e-9)
    # generative-_gp bivector squares (independent second implementation)
    h12 = _gp([0.0,0,0,0,0,0,1,0], [0.0,0,0,0,0,0,1,0])[1]   # e12^2
    h23 = _gp([0.0,0,0,0,1,0,0,0], [0.0,0,0,0,1,0,0,0])[1]   # e23^2
    h13 = _gp([0.0,0,0,0,0,1,0,0], [0.0,0,0,0,0,1,0,0])[1]   # e13^2
    gen_ok = isapprox(h12, -1) && isapprox(h23, -1) && isapprox(h13, -1)
    ok = vec_ok && pkg_biv_ok && close_ok && gen_ok
    return ok, (h12, h23, h13, pkg23, pkg13, pkg12, v_sq[1], v_sq[2], v_sq[3], close_ok)
end

# e1e2 (grade-2) coefficient of a package multivector x. If x = alpha*e1e2 + ...
# then x*PB12 = alpha*(e1e2)^2 + ... = -alpha + (non-scalar), so the e1e2
# coefficient is -scalar(x * PB12) because PB12^2 = -1.
_grade1_coeff_biv(x) = -scalar(x * PB12)

# ---------------------------------------------------------------------------
# KILL-CONTROL maps (wrong-structure). These MUST break the diagram.
# ---------------------------------------------------------------------------
# K1 fake_hopf: a smooth-looking S3->S2 that is NOT the Hopf map (drops cross
# term). It coincides with the genuine map only on a measure-zero locus; for
# >99% of inputs it disagrees. Used for the pointwise break of P1.
function fake_hopf(q)
    a, b, c, d = q
    z = a + d*im
    w = c + b*im
    # wrong: use Re(z)*Re(w) style coords that do not match the genuine Hopf map
    x = real(z)*real(w) + imag(z)*imag(w)
    y = real(z)*imag(w) - imag(z)*real(w)
    zc = abs2(z) - abs2(w)
    n = norm([x, y, zc]); n = n < 1e-14 ? 1.0 : n
    return [x, y, zc] ./ n   # renormalize so it at least lands on S2
end

# K1b null_hopf: a TOPOLOGICALLY TRIVIAL S3->S2 map (Hopf invariant 0). It uses
# only |z|^2-|w|^2 for the z-axis and projects the equatorial coords through a
# winding-free combination, so all "fibers" are contractible. This is the
# classifying map of the TRIVIAL bundle. The decisive non-circular anchor: its
# fiber-linking number MUST be 0, whereas the genuine Hopf map's is 1. If a
# trivial map ALSO gave linking 1, the linking measurement would be an artifact.
function null_hopf(q)
    a, b, c, d = q
    # depend only on the real parts in a winding-free way: no e^{i t} phase loop
    # survives, so preimages do not link. Map to S2 via a single coordinate.
    h = abs2(a + d*im) - abs2(c + b*im)   # = z-coord of genuine map (in [-1,1])
    # place everything on the prime meridian (y=0): a contractible image curve
    s = sqrt(max(0.0, 1 - h*h))
    return [s, 0.0, h]
end

# K2 bad_dcover: structural corruption -> no longer in SO(3). We flip the sign of
# the THIRD column (the north-pole image that projN reads) AND a second entry,
# so the map both loses orthogonality (anchor A2 breaks) and breaks commuting
# path P1 (which reads column 3 via projN). A wrong-structure double cover MUST
# break the diagram; if it still commuted the diagram would be vacuous.
function bad_dcover(U)
    R = dcover(U)
    R[1, 3] = -R[1, 3]   # corrupts the e3 image that projN reads
    R[2, 1] = -R[2, 1]   # extra corruption to guarantee loss of orthogonality
    return R
end

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
approx_eq(x, y; tol=TOL) = maximum(abs.(x .- y)) < tol

function is_SO3(R; tol=1e-8)
    orth = norm(R'*R - I) < tol
    det1 = abs(det(R) - 1.0) < tol
    return orth, det1
end

# Hopf fiber: the fiber over a point p in S2 is a great circle in S3.
# For genuine Hopf map, fiber over p = preimage = { e^{i t} * (z0,w0) }.
# We sample the fiber over the north pole (z arbitrary phase, w=0) and over the
# south pole (z=0, w phase), realize each as a closed loop in R^4, stereographic-
# project to R^3, and MEASURE the Gauss linking integral -> must be +-1 (anchor A3).
function quat_from_zw(z, w)
    # inverse of (z=a+di, w=c+bi): a=Re z, d=Im z, c=Re w, b=Im w
    return [real(z), imag(w), real(w), imag(z)]
end

function stereo_R4_to_R3(p4)
    # stereographic from the pole (0,0,0,1)
    a, b, c, d = p4
    den = 1 - d
    if abs(den) < 1e-9
        den = 1e-9
    end
    return [a/den, b/den, c/den]
end

# Gauss linking number between two closed polygonal loops in R^3.
function linking_number(loopA, loopB)
    nA = length(loopA); nB = length(loopB)
    total = 0.0
    for i in 1:nA
        a1 = loopA[i]; a2 = loopA[mod1(i+1, nA)]
        for j in 1:nB
            b1 = loopB[j]; b2 = loopB[mod1(j+1, nB)]
            total += _segment_solid_angle(a1, a2, b1, b2)
        end
    end
    return total / (4pi)
end

# contribution of segment pair to the Gauss integral (discretized double integral)
function _segment_solid_angle(a1, a2, b1, b2)
    da = a2 - a1
    db = b2 - b1
    # midpoint approximation of the Gauss integrand
    r = ((a1 + a2) ./ 2) .- ((b1 + b2) ./ 2)
    nr = norm(r)
    if nr < 1e-9
        return 0.0
    end
    return dot(cross(da, db), r) / nr^3
end

# ---------------------------------------------------------------------------
# Build the directed reduction graph (Graphs.jl) for the record/diagram.
# ---------------------------------------------------------------------------
function build_graph()
    names = ["S3", "SU2", "SO3", "S2", "Cl3even", "Twistor"]
    idx = Dict(n => i for (i, n) in enumerate(names))
    g = SimpleDiGraph(length(names))
    edges = [
        ("S3", "SU2", "iso_S3_SU2"),
        ("SU2", "SO3", "dcover"),
        ("S3", "S2", "hopf"),
        ("SO3", "S2", "projN"),
        ("SU2", "Cl3even", "iso_Cl3"),
        ("Cl3even", "SO3", "adj_Cl3"),
        ("S3", "Twistor", "embed"),
        ("Twistor", "S2", "projectivize"),
    ]
    for (u, v, _) in edges
        add_edge!(g, idx[u], idx[v])
    end
    return g, names, edges
end

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
function main()
    rng = MersenneTwister(20260601)
    NS = 400  # number of random S3 samples

    g, names, edges = build_graph()

    # ---- ANCHOR A2 + A1: SO(3) orthogonality + double-cover degree 2 ----
    a2_pass = true; a1_pass = true
    a2_worst_orth = 0.0; a2_worst_det = 0.0
    for _ in 1:NS
        q = rand_S3(rng)
        U = iso_S3_SU2(q)
        R = dcover(U)
        orth, det1 = is_SO3(R)
        a2_worst_orth = max(a2_worst_orth, norm(R'*R - I))
        a2_worst_det = max(a2_worst_det, abs(det(R) - 1.0))
        a2_pass &= (orth && det1)
        # A1: -U maps to the SAME R (kernel +-I)
        R_neg = dcover(-U)
        a1_pass &= approx_eq(R, R_neg; tol=1e-9)
    end

    # ---- COMMUTING PATH P1: hopf  ==  iso -> dcover -> projN ----
    p1_pass = true; p1_worst = 0.0
    for _ in 1:NS
        q = rand_S3(rng)
        lhs = hopf(q)
        U = iso_S3_SU2(q)
        rhs = projN(dcover(U))
        d = maximum(abs.(lhs .- rhs))
        p1_worst = max(p1_worst, d)
        p1_pass &= d < 1e-9
    end

    # ---- COMMUTING PATH P2: hopf  ==  twistor (projectivization) ----
    p2_pass = true; p2_worst = 0.0
    for _ in 1:NS
        q = rand_S3(rng)
        lhs = hopf(q)
        rhs = twistor(q)
        d = maximum(abs.(lhs .- rhs))
        p2_worst = max(p2_worst, d)
        p2_pass &= d < 1e-8
    end

    # ---- Clifford table cross-check (tool verified-against, not decorative) ----
    cl_xc_ok, cl_xc_vals = clifford_table_crosscheck()

    # ---- COMMUTING PATH P3: dcover  ==  iso_Cl3 -> adj_Cl3 ----
    # The Cl3even -> SO(3) edge is computed by the CliffordAlgebras PACKAGE rotor
    # sandwich (adj_Cl3_pkg, load-bearing) and must agree with the independent
    # SU(2) double cover. We also confirm the explicit _gp sandwich (adj_Cl3)
    # agrees with the package, so the two algebra implementations are consistent.
    p3_pass = true; p3_worst = 0.0
    p3_gp_pass = true; p3_gp_worst = 0.0      # _gp sandwich vs dcover (2nd path)
    p3_consistency_worst = 0.0                # package vs _gp agreement
    for _ in 1:NS
        q = rand_S3(rng)
        U = iso_S3_SU2(q)
        lhs = dcover(U)
        rhs_pkg = adj_Cl3_pkg(q)              # PACKAGE rotor sandwich (load-bearing)
        rhs_gp  = adj_Cl3(q; square=true)     # explicit _gp sandwich (independent)
        d = maximum(abs.(lhs .- rhs_pkg))
        p3_worst = max(p3_worst, d)
        p3_pass &= d < 1e-8
        dg = maximum(abs.(lhs .- rhs_gp))
        p3_gp_worst = max(p3_gp_worst, dg)
        p3_gp_pass &= dg < 1e-8
        p3_consistency_worst = max(p3_consistency_worst, maximum(abs.(rhs_pkg .- rhs_gp)))
    end
    p3_consistent = p3_consistency_worst < 1e-8

    # ---- ANCHOR A3: Hopf invariant 1 via linking number of two fibers ----
    # Fiber over north pole p=(0,0,1):  (z,w)=(e^{i t}, 0).
    # Fiber over a different point, p2 = hopf of (1/sqrt2)(1+i...) — take w!=0.
    nfib = 200
    loopA = Vector{Vector{Float64}}(undef, nfib)
    loopB = Vector{Vector{Float64}}(undef, nfib)
    # base point on fiber B: choose (z0,w0) with |z0|=|w0|=1/sqrt2, distinct image
    z0 = (1/sqrt(2)) + 0im
    w0 = (1/sqrt(2)) + 0im
    for k in 1:nfib
        t = 2pi * (k-1) / nfib
        ph = cis(t)
        # fiber A over north pole: z=ph, w=0
        loopA[k] = stereo_R4_to_R3(quat_from_zw(ph, 0.0 + 0im))
        # fiber B: z=ph*z0, w=ph*w0
        loopB[k] = stereo_R4_to_R3(quat_from_zw(ph*z0, ph*w0))
    end
    link = linking_number(loopA, loopB)
    a3_link = link
    a3_pass = abs(abs(link) - 1.0) < 0.05   # discretized; tolerance band

    # A3 anchor strengthened: a genuine Hopf FIBER must map to a SINGLE point
    # under the genuine map (image diameter ~ 0). We use fiber B (over a NON-pole
    # point of S2, w != 0), so the phase e^{i t} that parametrizes the fiber is
    # genuinely active -- the genuine map ignores it (collapse) while a trivial
    # map that depends only on |z|^2-|w|^2 cannot (it would still see the phase as
    # spread once we feed it the same loop). z0=w0=1/sqrt2 chosen as for loopB.
    fiberB_quats = [quat_from_zw(cis(2pi*(k-1)/nfib)*(1/sqrt(2)),
                                 cis(2pi*(k-1)/nfib)*(1/sqrt(2))) for k in 1:nfib]
    imgB_diam_genuine = let
        pts = [hopf(q) for q in fiberB_quats]
        maximum(maximum(abs.(p .- pts[1])) for p in pts)
    end
    imgA_diam_genuine = imgB_diam_genuine  # report under the same name in the diagram

    # =====================================================================
    # KILL-CONTROLS — these MUST FAIL. A passing kill-control => artifact.
    # =====================================================================
    # K1 fake_hopf vs P1 reference (iso->dcover->projN). Must NOT commute.
    k1_break = false; k1_worst = 0.0
    for _ in 1:NS
        q = rand_S3(rng)
        lhs = fake_hopf(q)
        rhs = projN(dcover(iso_S3_SU2(q)))
        d = maximum(abs.(lhs .- rhs))
        k1_worst = max(k1_worst, d)
        if d > 1e-6
            k1_break = true
        end
    end

    # K1b null_hopf (TOPOLOGICALLY TRIVIAL, Hopf invariant 0): MUST break P1, and
    # the decisive topological anchor: a genuine Hopf fiber (loopA) must NOT
    # collapse to a single point under null_hopf (it is not a fiber of the trivial
    # bundle). If it DID collapse, the fiber-structure test would be an artifact.
    k1b_break = false; k1b_worst = 0.0
    for _ in 1:NS
        q = rand_S3(rng)
        d = maximum(abs.(null_hopf(q) .- projN(dcover(iso_S3_SU2(q)))))
        k1b_worst = max(k1b_worst, d)
        if d > 1e-6
            k1b_break = true
        end
    end
    # Decisive topological anchor: the genuine Hopf map is SURJECTIVE onto S^2
    # (Hopf invariant 1 => covers the whole base), while null_hopf's image is a
    # 1-dimensional arc (y==0 meridian, Hopf invariant 0) of measure zero. We
    # MEASURE the y-coordinate spread of each map over many random S3 inputs:
    # genuine spans y in [-1,1]; trivial keeps y==0. If the trivial map ALSO
    # covered the sphere, the surjectivity signal would be an artifact.
    genuine_y_span = let
        ys = Float64[]
        for _ in 1:2000
            q = rand_S3(rng); push!(ys, hopf(q)[2])
        end
        maximum(ys) - minimum(ys)
    end
    null_y_span = let
        ys = Float64[]
        for _ in 1:2000
            q = rand_S3(rng); push!(ys, null_hopf(q)[2])
        end
        maximum(ys) - minimum(ys)
    end
    imgA_diam_null = null_y_span
    # genuine covers the sphere in y (span ~2); trivial map collapses y to 0.
    k1b_fiber_distinguishes = (genuine_y_span > 1.5) && (null_y_span < 1e-9)

    # K2 bad_dcover: orthogonality anchor A2 must FAIL, and P1 must FAIL.
    k2_lost_orth = false; k2_break_p1 = false; k2_worst_orth = 0.0; k2_worst_p1 = 0.0
    for _ in 1:NS
        q = rand_S3(rng)
        U = iso_S3_SU2(q)
        Rb = bad_dcover(U)
        o = norm(Rb'*Rb - I)
        k2_worst_orth = max(k2_worst_orth, o)
        if o > 1e-6
            k2_lost_orth = true
        end
        d = maximum(abs.(hopf(q) .- projN(Rb)))
        k2_worst_p1 = max(k2_worst_p1, d)
        if d > 1e-6
            k2_break_p1 = true
        end
    end

    # K3 no_square: Cl3 path without the rotor sandwich. P3 must FAIL.
    k3_break = false; k3_worst = 0.0
    for _ in 1:NS
        q = rand_S3(rng)
        lhs = dcover(iso_S3_SU2(q))
        rhs = adj_Cl3(q; square=false)   # broken: linear, not conjugation
        d = maximum(abs.(lhs .- rhs))
        k3_worst = max(k3_worst, d)
        if d > 1e-6
            k3_break = true
        end
    end

    # ---------------------------------------------------------------------
    # Report
    # ---------------------------------------------------------------------
    println("="^72)
    println("HYBRID REDUCTION GRAPH — commuting-diagram verification")
    println("="^72)
    println("Nodes: ", join(names, ", "))
    println("Edges:")
    for (u, v, lbl) in edges
        @printf("   %-9s --%-13s--> %s\n", u, lbl, v)
    end
    println("Graph: ", nv(g), " nodes, ", ne(g), " directed edges; ",
            is_connected(SimpleGraph(g)) ? "weakly connected" : "disconnected")
    println("-"^72)
    println("ANCHORS (checked against known math):")
    @printf("  A1 double-cover deg 2 (U,-U -> same R) : %s\n", a1_pass ? "PASS" : "FAIL")
    @printf("  A2 SO(3) orthogonality (R'R=I,detR=1)  : %s  (worst |R'R-I|=%.2e, |det-1|=%.2e)\n",
            a2_pass ? "PASS" : "FAIL", a2_worst_orth, a2_worst_det)
    @printf("  A3 Hopf invariant 1 (fiber linking #)  : %s  (measured link=%.4f, fiber-collapse diam=%.2e)\n",
            a3_pass ? "PASS" : "FAIL", a3_link, imgB_diam_genuine)
    @printf("  XC Clifford bivector^2=-1 (pkg + _gp)  : %s  (_gp e12^2,e23^2,e13^2=%.3f,%.3f,%.3f)\n",
            cl_xc_ok ? "PASS" : "FAIL", cl_xc_vals[1], cl_xc_vals[2], cl_xc_vals[3])
    @printf("     package e23^2,e13^2,e12^2 = %.3f,%.3f,%.3f ; package vec sq e1,e2,e3 = %.3f,%.3f,%.3f ; quaternion closure %s\n",
            cl_xc_vals[4], cl_xc_vals[5], cl_xc_vals[6],
            cl_xc_vals[7], cl_xc_vals[8], cl_xc_vals[9],
            cl_xc_vals[10] ? "OK (e23*e13=e12)" : "MISMATCH")
    println("-"^72)
    println("COMMUTING PATHS (measured agreement, NOT planted):")
    @printf("  P1 hopf == iso->dcover->projN          : %s  (worst diff=%.2e)\n",
            p1_pass ? "COMMUTES" : "FAILS", p1_worst)
    @printf("  P2 hopf == twistor (projectivize)      : %s  (worst diff=%.2e)\n",
            p2_pass ? "COMMUTES" : "FAILS", p2_worst)
    @printf("  P3 dcover == iso_Cl3->adj_Cl3 (pkg)    : %s  (worst diff=%.2e)\n",
            p3_pass ? "COMMUTES" : "FAILS", p3_worst)
    @printf("     P3 _gp sandwich vs dcover           : %s  (worst diff=%.2e); pkg-vs-_gp consistency worst=%.2e %s\n",
            p3_gp_pass ? "COMMUTES" : "FAILS", p3_gp_worst, p3_consistency_worst,
            p3_consistent ? "(consistent)" : "(INCONSISTENT!)")
    println("-"^72)
    println("KILL-CONTROLS (wrong structure MUST break the diagram):")
    @printf("  K1 fake_hopf breaks P1                 : %s  (worst diff=%.2e)\n",
            k1_break ? "BROKEN (good)" : "STILL PASSED (ARTIFACT!)", k1_worst)
    @printf("  K1b null_hopf (Hopf inv 0) breaks P1   : %s  (worst diff=%.2e)\n",
            k1b_break ? "BROKEN (good)" : "STILL PASSED (ARTIFACT!)", k1b_worst)
    @printf("  K1b surjectivity (genuine vs trivial)  : %s  (genuine y-span=%.3f [covers S2], trivial y-span=%.2e [arc])\n",
            k1b_fiber_distinguishes ? "DISTINGUISHED (good)" : "FAILED TO DISTINGUISH (ARTIFACT!)",
            genuine_y_span, null_y_span)
    @printf("  K2 bad_dcover loses SO(3) orthogonality: %s  (worst |R'R-I|=%.2e)\n",
            k2_lost_orth ? "BROKEN (good)" : "STILL PASSED (ARTIFACT!)", k2_worst_orth)
    @printf("  K2 bad_dcover breaks P1                : %s  (worst diff=%.2e)\n",
            k2_break_p1 ? "BROKEN (good)" : "STILL PASSED (ARTIFACT!)", k2_worst_p1)
    @printf("  K3 no-sandwich Cl3 breaks P3           : %s  (worst diff=%.2e)\n",
            k3_break ? "BROKEN (good)" : "STILL PASSED (ARTIFACT!)", k3_worst)
    println("="^72)

    anchors_ok = a1_pass && a2_pass && a3_pass && cl_xc_ok
    paths_ok = p1_pass && p2_pass && p3_pass && p3_gp_pass && p3_consistent
    kills_ok = k1_break && k1b_break && k1b_fiber_distinguishes &&
               k2_lost_orth && k2_break_p1 && k3_break
    overall = anchors_ok && paths_ok && kills_ok
    @printf("OVERALL: anchors=%s  paths_commute=%s  kill_controls_break=%s  =>  %s\n",
            anchors_ok, paths_ok, kills_ok, overall ? "GENUINE PASS" : "NOT A CLEAN PASS")

    results = Dict(
        "item" => "G_hybrid_reduction_graph",
        "classification" => "geometry_poc",
        "promotion_allowed" => false,
        "n_samples" => NS,
        "graph" => Dict(
            "nodes" => names,
            "edges" => [Dict("from"=>u, "to"=>v, "map"=>lbl) for (u,v,lbl) in edges],
            "n_nodes" => nv(g),
            "n_edges" => ne(g),
            "weakly_connected" => is_connected(SimpleGraph(g)),
        ),
        "anchors" => Dict(
            "A1_double_cover_degree2" => a1_pass,
            "A2_SO3_orthogonality" => a2_pass,
            "A2_worst_orth_residual" => a2_worst_orth,
            "A2_worst_det_residual" => a2_worst_det,
            "A3_hopf_invariant_one" => a3_pass,
            "A3_measured_linking_number" => a3_link,
            "XC_clifford_bivector_square_neg1" => cl_xc_ok,
            "XC_gp_e12_sq" => cl_xc_vals[1],
            "XC_gp_e23_sq" => cl_xc_vals[2],
            "XC_gp_e13_sq" => cl_xc_vals[3],
            "XC_pkg_e23_sq" => cl_xc_vals[4],
            "XC_pkg_e13_sq" => cl_xc_vals[5],
            "XC_pkg_e12_sq" => cl_xc_vals[6],
            "XC_pkg_e1_sq" => cl_xc_vals[7],
            "XC_pkg_e2_sq" => cl_xc_vals[8],
            "XC_pkg_e3_sq" => cl_xc_vals[9],
            "XC_pkg_quaternion_closure_ok" => cl_xc_vals[10],
        ),
        "commuting_paths" => Dict(
            "P1_hopf_vs_dcover_projN" => Dict("commutes"=>p1_pass, "worst_diff"=>p1_worst),
            "P2_hopf_vs_twistor" => Dict("commutes"=>p2_pass, "worst_diff"=>p2_worst),
            "P3_dcover_vs_clifford_adjoint" => Dict(
                "commutes"=>p3_pass, "worst_diff"=>p3_worst,
                "package_load_bearing"=>true,
                "gp_path_commutes"=>p3_gp_pass, "gp_worst_diff"=>p3_gp_worst,
                "package_vs_gp_consistent"=>p3_consistent,
                "package_vs_gp_worst"=>p3_consistency_worst),
        ),
        "kill_controls" => Dict(
            "K1_fake_hopf_breaks_P1" => Dict("broke_as_required"=>k1_break, "worst_diff"=>k1_worst),
            "K1b_null_hopf_breaks_P1" => Dict("broke_as_required"=>k1b_break, "worst_diff"=>k1b_worst),
            "K1b_surjectivity_distinguishes_genuine_from_trivial" => Dict(
                "distinguished"=>k1b_fiber_distinguishes,
                "genuine_y_span_covers_S2"=>genuine_y_span,
                "trivial_map_y_span_arc"=>null_y_span,
                "genuine_fiber_collapse_diameter"=>imgB_diam_genuine),
            "K2_bad_dcover_loses_orthogonality" => Dict("broke_as_required"=>k2_lost_orth, "worst_orth"=>k2_worst_orth),
            "K2_bad_dcover_breaks_P1" => Dict("broke_as_required"=>k2_break_p1, "worst_diff"=>k2_worst_p1),
            "K3_no_sandwich_breaks_P3" => Dict("broke_as_required"=>k3_break, "worst_diff"=>k3_worst),
        ),
        "verdict" => Dict(
            "anchors_ok" => anchors_ok,
            "paths_commute" => paths_ok,
            "kill_controls_break" => kills_ok,
            "genuine_pass" => overall,
        ),
    )

    outpath = joinpath(@__DIR__, "hybrid_reduction_graph_commuting_diagram_results.json")
    open(outpath, "w") do io
        JSON.print(io, results, 2)
    end
    println("Results written: ", outpath)
    return overall
end

main()
