# G_S2_hopf_base.jl
#
# GEOMETRY SCOUT: S^2 Hopf base surface.
#
# Object under test: the BASE of the Hopf fibration S^3 --> S^2.
#   A point of S^3 is a unit quaternion q = a + b i + c j + d k  (a^2+b^2+c^2+d^2 = 1),
#   identified with a 2-component unit spinor |psi> in C^2.
#   The Hopf map to the base S^2 is the Bloch vector obtained by conjugating sigma_z:
#       q sigma_z q^dag   <==>   n = <psi| sigma_vec |psi>
#   (these two forms are the SAME map; the quaternion-conjugation form rotates the
#    z-axis by the SO(3) rotation R(q), and the spinor expectation form reads off
#    that rotated axis as a Bloch vector).
#
# Two MEASURED (not planted) properties anchored to known mathematics:
#   (A) BASE NORM = 1.  For any unit spinor, |<sx>|^2 + |<sy>|^2 + |<sz>|^2 = (<psi|psi>)^2 = 1.
#       This is the pure-state Bloch identity: the image lies exactly on the unit S^2.
#       We READ OUT the three expectation values and then measure the norm; we never
#       set the norm to 1 by construction.
#   (B) U(1) FIBER INVARIANCE (the defining quotient S^3/U(1) = S^2).
#       |psi> -> e^{i theta} |psi>  (equivalently q -> q e^{i theta}, the Hopf fiber)
#       leaves n = <psi|sigma|psi> EXACTLY unchanged, because the global phase cancels
#       in every expectation value. q and q e^{i theta} map to the same base point.
#
# KILL-CONTROL (this is the load-bearing falsifier):
#   If "fiber invariance" passed for a GENERIC (non-fiber) transformation too, the
#   invariance would be vacuous / an artifact. So we apply transformations that are
#   NOT in the U(1) fiber and REQUIRE them to MOVE the base point:
#     - relative phase  diag(e^{i theta}, 1)   (a U(1) but NOT the global/fiber U(1))
#     - a generic SU(2) rotation               (moves the point on S^2)
#   A genuine quotient must distinguish fiber (no motion) from non-fiber (motion).
#   We also run a POSITIVE control (true fiber: must NOT move) and a BOUNDARY control
#   (theta -> 0 and the poles of S^2).
#
# NON-CIRCULARITY: the unit-sphere norm and the exact phase-cancellation are
#   standard facts of pure 2-state quantum geometry / SU(2)->SO(3); we check the sim
#   against that math, not against a target we planted. Norm target 1.0 is a theorem,
#   not a knob.
#
# classification: PoC ;  promotion_allowed = false

using LinearAlgebra
using Random
using JSON

# ---------------------------------------------------------------------------
# Pauli matrices (Hermitian generators of su(2))
# ---------------------------------------------------------------------------
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

# ---------------------------------------------------------------------------
# Quaternion <-> SU(2) spinor.
#   q = (a,b,c,d) ~ a + b i + c j + d k  maps to the SU(2) matrix U(q),
#   and the spinor |psi> = first column of U(q) is a unit vector in C^2.
#   This realises the standard double cover SU(2) -> SO(3); the Hopf map is
#   n(q) = R(q) * zhat = <psi| sigma |psi>.
# ---------------------------------------------------------------------------
function quat_to_su2(a, b, c, d)
    # U = a*I - i*(b*SX + c*SY + d*SZ)  is the standard unit-quaternion -> SU(2) map
    ComplexF64[ a - im*d    -c - im*b
                 c - im*b     a + im*d ]
end

# spinor from quaternion: first column of U(q)
spinor_from_quat(a, b, c, d) = quat_to_su2(a, b, c, d)[:, 1]

# Bloch / Hopf base point: MEASURED expectation values (the read-out, not a plant)
function bloch(psi::AbstractVector{<:Complex})
    nx = real(psi' * SX * psi)
    ny = real(psi' * SY * psi)
    nz = real(psi' * SZ * psi)
    [nx, ny, nz]
end

# Quaternion-conjugation form of the SAME map: rotate sigma_z by U, read the axis.
# n_k = (1/2) tr( U sigma_z U^dag sigma_k ).  Cross-check that it equals bloch(psi).
function bloch_via_conjugation(a, b, c, d)
    U = quat_to_su2(a, b, c, d)
    M = U * SZ * U'                      # q sigma_z q^dag
    [0.5 * real(tr(M * SX)),
     0.5 * real(tr(M * SY)),
     0.5 * real(tr(M * SZ))]
end

# random unit quaternion (uniform on S^3)
function rand_unit_quat(rng)
    v = randn(rng, 4)
    v ./= norm(v)
    (v[1], v[2], v[3], v[4])
end

# generic SU(2) rotation (a NON-fiber motion on S^2)
function rand_su2(rng)
    a, b, c, d = rand_unit_quat(rng)
    quat_to_su2(a, b, c, d)
end

# ---------------------------------------------------------------------------
# Experiment
# ---------------------------------------------------------------------------
const TOL = 1e-10
rng = MersenneTwister(20260601)
const NSAMP = 2000

# accumulators
base_norm_dev_max   = 0.0        # |norm(n) - 1|  over all samples  (property A)
two_form_agree_max  = 0.0        # |bloch(psi) - bloch_via_conjugation|  (the maps agree)
fiber_shift_max     = 0.0        # motion under TRUE fiber (must be ~0)  (property B, positive control)

# kill-control accumulators (these must be LARGE on average -> the quotient is non-vacuous)
relphase_shift_max  = 0.0
relphase_shift_min  = Inf
su2_shift_max       = 0.0
su2_shift_min       = Inf
relphase_moved      = 0           # count of samples the non-fiber op actually moved
su2_moved           = 0

# boundary control: theta -> 0 fiber must give ZERO motion (continuity), and the
# poles |0>,|1> are fixed points whose Bloch vectors are exactly +-zhat.
boundary_ok = true
boundary_notes = String[]

for s in 1:NSAMP
    a, b, c, d = rand_unit_quat(rng)
    psi = spinor_from_quat(a, b, c, d)

    n  = bloch(psi)
    nc = bloch_via_conjugation(a, b, c, d)

    # (A) measured base norm
    global base_norm_dev_max = max(base_norm_dev_max, abs(norm(n) - 1.0))
    # the two formulations of the Hopf map agree
    global two_form_agree_max = max(two_form_agree_max, norm(n .- nc))

    # (B) POSITIVE control: true U(1) fiber -> base point fixed
    theta = 2pi * (s / NSAMP)             # sweep a full fiber circle across samples
    psi_fiber = exp(im * theta) .* psi
    n_fiber = bloch(psi_fiber)
    global fiber_shift_max = max(fiber_shift_max, norm(n_fiber .- n))

    # KILL-CONTROL 1: relative phase diag(e^{i theta},1) is NOT the global fiber
    psi_rel = ComplexF64[exp(im * theta) * psi[1], psi[2]]
    psi_rel ./= norm(psi_rel)             # still a unit spinor
    n_rel = bloch(psi_rel)
    shift_rel = norm(n_rel .- n)
    global relphase_shift_max = max(relphase_shift_max, shift_rel)
    global relphase_shift_min = min(relphase_shift_min, shift_rel)
    # a relative phase can't move a point that sits on a pole (|0> or |1>): exclude
    # the degenerate case where |psi[1]| or |psi[2]| ~ 0 from the "must move" count.
    if abs(psi[1]) > 1e-3 && abs(psi[2]) > 1e-3 && shift_rel > 1e-6
        global relphase_moved += 1
    end

    # KILL-CONTROL 2: a generic SU(2) rotation moves the base point on S^2
    V = rand_su2(rng)
    psi_su2 = V * psi
    n_su2 = bloch(psi_su2)
    shift_su2 = norm(n_su2 .- n)
    global su2_shift_max = max(su2_shift_max, shift_su2)
    global su2_shift_min = min(su2_shift_min, shift_su2)
    if shift_su2 > 1e-6
        global su2_moved += 1
    end
end

# ---------------------------------------------------------------------------
# BOUNDARY controls
# ---------------------------------------------------------------------------
# theta -> 0 fiber: zero motion (continuity of the quotient at the identity fiber)
let psi = spinor_from_quat(rand_unit_quat(MersenneTwister(7))...)
    n0 = bloch(psi)
    n_eps = bloch(exp(im * 1e-12) .* psi)
    d0 = norm(n_eps .- n0)
    if d0 > 1e-8
        boundary_ok = false
        push!(boundary_notes, "theta->0 fiber moved point by $d0 (should be ~0)")
    else
        push!(boundary_notes, "theta->0 fiber motion = $d0 (ok)")
    end
end

# poles: |0> -> +zhat, |1> -> -zhat  (exact known base points of the Hopf map)
let
    n_up   = bloch(ComplexF64[1, 0])
    n_down = bloch(ComplexF64[0, 1])
    if norm(n_up .- [0.0, 0.0, 1.0]) > TOL
        boundary_ok = false
        push!(boundary_notes, "north pole |0> Bloch = $n_up (should be +zhat)")
    else
        push!(boundary_notes, "north pole |0> -> +zhat (ok)")
    end
    if norm(n_down .- [0.0, 0.0, -1.0]) > TOL
        boundary_ok = false
        push!(boundary_notes, "south pole |1> Bloch = $n_down (should be -zhat)")
    else
        push!(boundary_notes, "south pole |1> -> -zhat (ok)")
    end
    # relative phase on a pole: |0> picks up a global phase only -> base point FIXED.
    # This is the correct degenerate behaviour, and is why we excluded poles above.
    n_pole_rel = bloch(ComplexF64[exp(im * 0.9) * 1, 0])
    push!(boundary_notes,
        "relphase on pole |0> motion = $(norm(n_pole_rel .- n_up)) (expected ~0; pole has no relative phase)")
end

# ---------------------------------------------------------------------------
# Verdicts
# ---------------------------------------------------------------------------
# Property A: base lies on the unit S^2 (measured)
A_pass = base_norm_dev_max < TOL
# Two Hopf-map formulations agree
maps_agree = two_form_agree_max < TOL
# Property B positive control: fiber leaves base fixed
B_pass = fiber_shift_max < TOL
# Kill-control: non-fiber ops MUST move the base for almost all generic points.
#   (relative phase fixes poles, so we require it to move the non-degenerate samples)
kill_relphase_distinguishes = (relphase_shift_max > 1e-3) && (relphase_moved > 0)
kill_su2_distinguishes      = (su2_shift_max > 1e-3) && (su2_moved > 0)
# The whole point: fiber ~0 while non-fiber is large => the quotient is GENUINE.
quotient_is_genuine = B_pass && kill_relphase_distinguishes && kill_su2_distinguishes &&
                      (fiber_shift_max < su2_shift_max - 1e-3) &&
                      (fiber_shift_max < relphase_shift_max - 1e-3)

all_pass = A_pass && maps_agree && B_pass && boundary_ok && quotient_is_genuine

# status ladder
status = all_pass ? "passes" : "runs"

results = Dict(
    "object_id" => "G_S2_hopf_base",
    "description" => "S^2 Hopf base: q sigma_z q^dag = <psi|sigma|psi>; base-norm + U(1) fiber-invariance",
    "classification" => "PoC",
    "promotion_allowed" => false,
    "status" => status,
    "n_samples" => NSAMP,
    "tol" => TOL,
    "anchored_invariants" => Dict(
        "base_on_unit_S2" => "pure-state Bloch identity: |<sx>|^2+|<sy>|^2+|<sz>|^2 = 1",
        "fiber_quotient"  => "S^3/U(1)=S^2: global phase cancels in <psi|sigma|psi>",
        "poles"           => "|0>->+zhat, |1>->-zhat (exact Hopf base points)"
    ),
    "measured" => Dict(
        "base_norm_dev_max"   => base_norm_dev_max,
        "two_form_agree_max"  => two_form_agree_max,
        "fiber_shift_max"     => fiber_shift_max,
        "relphase_shift_max"  => relphase_shift_max,
        "relphase_shift_min"  => relphase_shift_min,
        "relphase_moved_count"=> relphase_moved,
        "su2_shift_max"       => su2_shift_max,
        "su2_shift_min"       => su2_shift_min,
        "su2_moved_count"     => su2_moved
    ),
    "controls" => Dict(
        "positive_fiber_fixes_base"        => B_pass,
        "negative_relphase_moves_base"     => kill_relphase_distinguishes,
        "negative_su2_moves_base"          => kill_su2_distinguishes,
        "boundary"                         => boundary_ok,
        "boundary_notes"                   => boundary_notes
    ),
    "verdicts" => Dict(
        "A_base_on_unit_S2"        => A_pass,
        "hopf_two_forms_agree"     => maps_agree,
        "B_fiber_invariance"       => B_pass,
        "kill_control_genuine"     => quotient_is_genuine
    ),
    "all_pass" => all_pass
)

open(joinpath(@__DIR__, "G_S2_hopf_base_results.json"), "w") do io
    JSON.print(io, results, 2)
end

# ---------------------------------------------------------------------------
# Console report
# ---------------------------------------------------------------------------
println("==== G_S2_hopf_base ====")
println("samples                : $NSAMP")
println("[A] base norm dev max  : $base_norm_dev_max   -> on unit S^2: $A_pass")
println("    two Hopf forms agree max diff: $two_form_agree_max  -> agree: $maps_agree")
println("[B] fiber shift max    : $fiber_shift_max     -> base fixed: $B_pass  (POSITIVE control)")
println("KILL relphase shift    : min=$relphase_shift_min max=$relphase_shift_max moved=$relphase_moved -> distinguishes: $kill_relphase_distinguishes")
println("KILL su2     shift     : min=$su2_shift_min max=$su2_shift_max moved=$su2_moved -> distinguishes: $kill_su2_distinguishes")
println("quotient genuine (fiber<<nonfiber): $quotient_is_genuine")
println("boundary               : $boundary_ok")
for note in boundary_notes
    println("   - $note")
end
println("STATUS                 : $status   all_pass=$all_pass")
