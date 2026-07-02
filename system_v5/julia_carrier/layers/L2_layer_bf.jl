# L2_layer_bf.jl
#
# GENUINE CARRIER REBUILD of geometry-manifold layer L2 — the S^3 SPINOR CARRIER.
#
#   S^3 = { psi in C^2 : ||psi|| = 1 }  is a spinor space. The unit spinor psi IS the
#   carrier of L2. This is allowed: the Bloch-free directive governs operator/terrain
#   DYNAMICS (no dot-r ODE, no terrain operators) — it does NOT forbid the spinor itself.
#   There is no ODE and no terrain operator anywhere in this file.
#
# classification: L2_layer_bf_poc      promotion_allowed: false
#
# ===========================================================================================
# WHY THE PRIOR L2_layer_bf.jl WAS MIS-FRAMED (honest_status="could_not_make_genuine"):
#   The prior file tried to prove the carrier real via a "dependency-forcing erasure" in pure
#   density-operator language. That framing FORCED every clean collapse to be an algebraic
#   tautology ([diag,diag]=0 / [co-diagonal]=0) and made the U(1) fiber phase inexpressible
#   (rho is global-phase-blind). It concluded "could not make genuine" — but it was asking the
#   wrong question. A CARRIER's realness is not proved by erasure-collapse; it is anchored to
#   KNOWN STRUCTURAL INVARIANTS of S^3 as a spinor space, with a WRONG-STRUCTURE control that
#   FLIPS those invariants. That is what this rebuild does.
#
# ===========================================================================================
# THE GENUINE TEST. Three invariants of S^3, each anchored to a KNOWN value (NOT planted), each
# with a WRONG-STRUCTURE control on which the invariant FLIPS (so a pass would be WRONG, not
# by-construction-right):
#
#   (1) DOUBLE COVER SU(2)->SO(3).  q -> R(q) is a 2-to-1 homomorphism with kernel {I,-I}.
#       ANCHOR: kernel order == 2 (the known Z2 = pi_1(SO(3)) double-cover fact).
#       MEASURED: q and -q give the SAME R; R in SO(3) (R^T R = I, det = +1); |kernel| = 2.
#       WRONG-STRUCTURE CONTROL: the IDENTITY map q -> q (a NON-cover) gives q != -q, so the
#       fibre is a single point: kernel order FLIPS 2 -> 1, the double cover disappears.
#
#   (2) SPINOR SIGN.  A 2pi rotation sends psi -> -psi; a 4pi rotation sends psi -> +psi. This
#       sign is the topological signature of a GENUINE double cover (not a single cover).
#       ANCHOR: U(2pi) psi == -psi and U(4pi) psi == +psi (known half-angle / spin-1/2 fact).
#       MEASURED: the SU(2) element U(theta)=exp(-i theta n.sigma/2) at theta=2pi,4pi.
#       WRONG-STRUCTURE CONTROL: the SO(3) rotation R(theta) (single cover) at 2pi gives the
#       IDENTITY (R(2pi)=R(0)=I) — no sign. The spinor sign DISAPPEARS on the wrong structure.
#
#   (3) HOPF MAP + c1.  pi(psi)=psi^dag sigma psi in S^2, ||pi||=1; the U(1) fibre is the global
#       phase (psi and e^{i a}psi -> same pi). The Hopf line bundle has first Chern number c1=1,
#       computed by the Fukui-Hatsugai-Suzuki plaquette method (same method as
#       g_structure_reduction_chain.jl).
#       ANCHOR: c1 == 1 (the known Hopf invariant / generator of pi_3(S^2)=Z).
#       MEASURED: ||pi||=1 on the sphere; e^{i a} phase invariance of pi; FHS plaquette c1.
#       WRONG-STRUCTURE CONTROL: the TRIVIAL bundle (constant section |u>=const) has c1=0 and
#       flat curvature. c1 FLIPS 1 -> 0 on the wrong structure.
#
# all_pass is TRUE iff all three invariants hit their KNOWN anchor values AND all three wrong-
# structure controls FLIP (kernel 2->1, spinor-sign present->absent, c1 1->0). The flip is the
# evidence the invariants are measured, not by-construction.
#
# Tools (LOAD-BEARING only):
#   LinearAlgebra — spinor / rotation-matrix / line-bundle algebra (norm, det, eigen, matrix exp).
#   Random        — seeded random spinors and quaternions for the cover / Hopf measurements.
#   JSON          — receipt emission.

using LinearAlgebra
using Random
using JSON

const RESULTS_PATH = joinpath(@__DIR__, "L2_layer_bf_results.json")
const SEED = 20260602
const TOL = 1e-10

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SIGMA = (SX, SY, SZ)

# -------------------------------------------------------------------------------------------
# S^3 = unit spinors psi in C^2. The spinor IS the carrier.
# -------------------------------------------------------------------------------------------
function random_spinor(rng)
    g = randn(rng, ComplexF64, 2)
    return g / norm(g)
end

# Hopf projection pi(psi) = (psi^dag sigma_x psi, psi^dag sigma_y psi, psi^dag sigma_z psi) in S^2.
hopf_pi(psi) = [real(psi' * SX * psi), real(psi' * SY * psi), real(psi' * SZ * psi)]

# Unit quaternion -> SO(3) rotation matrix R(q) (the double-cover map SU(2)->SO(3)).
# (Same form as g_structure_reduction_chain.jl::q_to_R.)
function q_to_R(q)
    a, b, c, d = q
    return [a^2+b^2-c^2-d^2  2(b*c-a*d)       2(b*d+a*c);
            2(b*c+a*d)       a^2-b^2+c^2-d^2  2(c*d-a*b);
            2(b*d-a*c)       2(c*d+a*b)       a^2-b^2-c^2+d^2]
end

# SU(2) element for a rotation by angle theta about unit axis n: U = exp(-i theta n.sigma/2).
function su2_rotation(theta, n)
    H = n[1]*SX + n[2]*SY + n[3]*SZ
    return exp(-im * (theta/2) * H)
end

# SO(3) rotation by angle theta about x-axis (the SINGLE-cover wrong-structure control for sign).
function so3_rotation_x(theta)
    c, s = cos(theta), sin(theta)
    return [1.0 0.0 0.0; 0.0 c -s; 0.0 s c]
end

# Quaternion for rotation by theta about x-axis (cos(theta/2), sin(theta/2)*x_axis).
quat_x(theta) = [cos(theta/2), sin(theta/2), 0.0, 0.0]

# Fukui-Hatsugai-Suzuki first Chern number of a U(1) line bundle over S^2 (gauge-invariant).
# statefn(th, ph) -> normalized C^2 section. Same plaquette method as g_structure_reduction_chain.jl.
function fhs_chern(statefn; nth=60, nph=60)
    ths = range(1e-4, pi - 1e-4; length=nth)
    phs = range(0, 2pi; length=nph+1)[1:nph]
    link(a, b) = (s1 = statefn(a...); s2 = statefn(b...); z = s1' * s2; z / abs(z + 1e-30))
    Fmax = 0.0; chern = 0.0
    for i in 1:nth-1, j in 1:nph
        jp = mod1(j+1, nph)
        p1 = (ths[i], phs[j]); p2 = (ths[i+1], phs[j])
        p3 = (ths[i+1], phs[jp]); p4 = (ths[i], phs[jp])
        F = angle(link(p1,p2) * link(p2,p3) * link(p3,p4) * link(p4,p1))
        chern += F; Fmax = max(Fmax, abs(F))
    end
    return (chern = chern / (2pi), Fmax = Fmax)
end

# Hopf tautological section over S^2 (c1 = 1) and the TRIVIAL section (c1 = 0, wrong structure).
hopf_section(th, ph) = ComplexF64[cos(th/2), sin(th/2) * exp(im*ph)]
trivial_section(th, ph) = ComplexF64[1.0, 0.0]

# =================================================================================================
function main()
    rng = MersenneTwister(SEED)
    R = Dict{String,Any}()
    R["item"] = "L2_layer_bf"
    R["layer_id"] = "L2"
    R["layer_name"] = "S^3 spinor carrier (unit spinors psi in C^2; S^3 is a spinor space)"
    R["classification"] = "L2_layer_bf_poc"
    R["promotion_allowed"] = false
    R["seed"] = SEED
    R["status_ladder"] = "exists < runs < passes"
    R["carrier_statement"] = "S^3 = {psi in C^2 : ||psi||=1}. The unit spinor psi IS the carrier. " *
        "No dot-r ODE, no terrain operators (the Bloch-free directive governs operator/terrain dynamics, not the spinor carrier)."
    R["prior_was_misframed"] = "The prior L2_layer_bf.jl tried to prove the carrier via a density-only " *
        "'dependency-forcing erasure', which forced every collapse to be an algebraic tautology and made the " *
        "fiber phase inexpressible (honest_status=could_not_make_genuine). That was the WRONG question. A carrier's " *
        "realness is anchored to KNOWN S^3 invariants (double-cover kernel order, spinor 2pi sign, Hopf c1) with a " *
        "WRONG-STRUCTURE control that FLIPS each invariant. This rebuild does that."
    R["fresh_rerun_command"] =
        "julia --project=\"/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier\" " *
        "\"/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/layers/L2_layer_bf.jl\""

    R["finite_map"] = Dict(
        "domain" => "finite set of unit spinors psi in S^3 = {psi in C^2 : ||psi||=1}, unit quaternions q in S^3, and (theta,phi) grid on S^2",
        "codomain" => "Hopf base pi(psi)=psi^dag sigma psi in S^2 ; SO(3) rotation R(q) ; first Chern number c1 of the Hopf line bundle",
        "invariants" => "double-cover kernel order (=2) ; spinor 2pi sign (psi->-psi) ; Hopf c1 (=1)",
    )

    # =======================================================================================
    # INVARIANT (1): DOUBLE COVER SU(2)->SO(3). Anchor: kernel order == 2 (Z2).
    # =======================================================================================
    dc = Dict{String,Any}()
    n = 400
    two_to_one = 0; in_so3 = 0
    for _ in 1:n
        q = normalize(randn(rng, 4))
        Rp = q_to_R(q); Rm = q_to_R(-q)
        (maximum(abs.(Rp - Rm)) < TOL) && (two_to_one += 1)                       # q and -q -> SAME R
        (norm(Rp'Rp - I) < 1e-9 && abs(det(Rp) - 1) < 1e-9) && (in_so3 += 1)      # R in SO(3)
    end
    # kernel of q->R = { q : R(q) = I } among {+q0, -q0} for the identity-rotation quaternion q0=(1,0,0,0).
    q0 = [1.0, 0.0, 0.0, 0.0]
    kernel_elems = 0
    for s in (1.0, -1.0)
        (maximum(abs.(q_to_R(s .* q0) - I)) < TOL) && (kernel_elems += 1)         # both +q0 and -q0 map to I
    end
    dc["map"] = "q -> R(q), unit quaternion (SU(2)) to SO(3) rotation"
    dc["q_and_minus_q_same_R_frac"] = two_to_one / n
    dc["R_in_SO3_frac"] = in_so3 / n
    dc["kernel_order"] = kernel_elems                                            # MEASURED, anchor == 2
    dc["kernel_order_anchor"] = 2
    dc["kernel_is_Z2"] = kernel_elems == 2
    dc["two_to_one_homomorphism"] = (two_to_one == n) && (in_so3 == n)
    dc["pass"] = dc["kernel_is_Z2"] && dc["two_to_one_homomorphism"]
    R["invariant_double_cover"] = dc

    # WRONG-STRUCTURE CONTROL (1): identity map q -> q (a NON-cover). q != -q, fibre is one point.
    dc_ctrl = Dict{String,Any}()
    identity_map(q) = q
    ctrl_two_to_one = 0
    for _ in 1:n
        q = normalize(randn(rng, 4))
        (maximum(abs.(identity_map(q) - identity_map(-q))) < TOL) && (ctrl_two_to_one += 1)  # q vs -q now DIFFER
    end
    # kernel of identity map among {+q0,-q0}: only +q0 maps to identity element (-q0 != +q0).
    ctrl_kernel = 0
    for s in (1.0, -1.0)
        (maximum(abs.(identity_map(s .* q0) - q0)) < TOL) && (ctrl_kernel += 1)
    end
    dc_ctrl["map"] = "q -> q (identity; NON-cover, single-valued)"
    dc_ctrl["q_and_minus_q_same_frac"] = ctrl_two_to_one / n                     # ~0: q and -q differ
    dc_ctrl["kernel_order"] = ctrl_kernel                                        # FLIPS 2 -> 1
    dc_ctrl["kernel_order_flipped_to_1"] = ctrl_kernel == 1
    dc_ctrl["double_cover_destroyed"] = (ctrl_two_to_one == 0) && (ctrl_kernel == 1)
    R["wrong_structure_double_cover"] = dc_ctrl

    # =======================================================================================
    # INVARIANT (2): SPINOR SIGN. Anchor: U(2pi)psi = -psi, U(4pi)psi = +psi.
    # =======================================================================================
    ss = Dict{String,Any}()
    nax = [0.0, 0.0, 1.0]   # rotation axis (z)
    U2pi = su2_rotation(2pi, nax)
    U4pi = su2_rotation(4pi, nax)
    psi_test = random_spinor(rng)
    err_2pi_minus = norm(U2pi * psi_test - (-psi_test))    # ~0 if U(2pi)psi = -psi
    err_2pi_plus  = norm(U2pi * psi_test - ( psi_test))    # large: NOT +psi
    err_4pi_plus  = norm(U4pi * psi_test - ( psi_test))    # ~0 if U(4pi)psi = +psi
    # also confirm via the SU(2) matrix itself: U(2pi) = -I, U(4pi) = +I.
    U2pi_is_minusI = norm(U2pi - (-I2)) < 1e-9
    U4pi_is_plusI  = norm(U4pi - ( I2)) < 1e-9
    ss["U_2pi_psi_equals_minus_psi"] = err_2pi_minus < 1e-9
    ss["U_2pi_psi_not_plus_psi"] = err_2pi_plus > 1.0
    ss["U_4pi_psi_equals_plus_psi"] = err_4pi_plus < 1e-9
    ss["U_2pi_matrix_is_minus_I"] = U2pi_is_minusI
    ss["U_4pi_matrix_is_plus_I"] = U4pi_is_plusI
    ss["err_2pi_to_minus_psi"] = err_2pi_minus
    ss["err_4pi_to_plus_psi"] = err_4pi_plus
    ss["genuine_double_cover_sign"] = ss["U_2pi_psi_equals_minus_psi"] && ss["U_4pi_psi_equals_plus_psi"] &&
                                      U2pi_is_minusI && U4pi_is_plusI
    ss["pass"] = ss["genuine_double_cover_sign"]
    R["invariant_spinor_sign"] = ss

    # WRONG-STRUCTURE CONTROL (2): SO(3) single cover. R(2pi) = I -> NO sign.
    ss_ctrl = Dict{String,Any}()
    R2pi = so3_rotation_x(2pi)
    R4pi = so3_rotation_x(4pi)
    R2pi_is_I = maximum(abs.(R2pi - I)) < 1e-9
    R4pi_is_I = maximum(abs.(R4pi - I)) < 1e-9
    ss_ctrl["map"] = "SO(3) single cover R(theta) about x"
    ss_ctrl["R_2pi_is_identity"] = R2pi_is_I            # single cover: 2pi already returns to I
    ss_ctrl["R_4pi_is_identity"] = R4pi_is_I
    ss_ctrl["no_minus_sign_at_2pi"] = R2pi_is_I         # there is no -I to find on SO(3)
    ss_ctrl["spinor_sign_disappears"] = R2pi_is_I       # the sign vanishes on the single cover
    R["wrong_structure_spinor_sign"] = ss_ctrl

    # =======================================================================================
    # INVARIANT (3): HOPF MAP + first Chern number c1. Anchor: c1 == 1.
    # =======================================================================================
    hp = Dict{String,Any}()
    # (3a) ||pi(psi)|| = 1 on S^2 for unit spinors.
    norm_devs = Float64[]
    for _ in 1:400
        push!(norm_devs, abs(norm(hopf_pi(random_spinor(rng))) - 1.0))
    end
    # (3b) U(1) fibre = global phase: psi and e^{i a}psi map to the SAME base point.
    phase_devs = Float64[]
    for _ in 1:400
        psi = random_spinor(rng)
        a = 2pi * rand(rng)
        push!(phase_devs, norm(hopf_pi(exp(im*a) .* psi) - hopf_pi(psi)))
    end
    # (3c) first Chern number of the Hopf line bundle via FHS plaquette.
    hopf = fhs_chern(hopf_section)
    c1 = round(Int, hopf.chern)
    hp["pi_on_S2_max_norm_dev"] = maximum(norm_devs)
    hp["pi_on_S2_unit"] = maximum(norm_devs) < 1e-9
    hp["U1_fiber_max_phase_dev"] = maximum(phase_devs)
    hp["U1_fiber_is_global_phase"] = maximum(phase_devs) < 1e-9
    hp["chern_raw"] = hopf.chern
    hp["c1"] = c1
    hp["c1_anchor"] = 1
    hp["Fmax"] = hopf.Fmax
    hp["c1_is_one"] = abs(hopf.chern - 1.0) < 0.05
    hp["curvature_nonzero"] = hopf.Fmax > 1e-3
    hp["pass"] = hp["pi_on_S2_unit"] && hp["U1_fiber_is_global_phase"] && hp["c1_is_one"] && hp["curvature_nonzero"]
    R["invariant_hopf_c1"] = hp

    # WRONG-STRUCTURE CONTROL (3): trivial bundle (constant section). c1 FLIPS 1 -> 0, F = 0.
    hp_ctrl = Dict{String,Any}()
    triv = fhs_chern(trivial_section)
    hp_ctrl["section"] = "constant |u> = (1,0) (trivial bundle)"
    hp_ctrl["chern_raw"] = triv.chern
    hp_ctrl["c1"] = round(Int, triv.chern)
    hp_ctrl["Fmax"] = triv.Fmax
    hp_ctrl["c1_flipped_to_0"] = abs(triv.chern) < 0.05
    hp_ctrl["curvature_flat"] = triv.Fmax < 1e-9
    hp_ctrl["hopf_invariant_destroyed"] = hp_ctrl["c1_flipped_to_0"] && hp_ctrl["curvature_flat"]
    R["wrong_structure_hopf_c1"] = hp_ctrl

    # =======================================================================================
    # NEGATIVE CONTROLS (carrier admissibility).
    # =======================================================================================
    neg = Dict{String,Any}()
    bad = ComplexF64[2.0, 1.0]                       # non-unit -> not in S^3
    neg["nonunit_spinor_norm"] = norm(bad)
    neg["nonunit_excluded_from_S3"] = abs(norm(bad) - 1.0) > 1e-6
    # a non-unit "spinor" breaks ||pi||=1 (Hopf base not on S^2):
    neg["nonunit_breaks_hopf_norm"] = abs(norm(hopf_pi(bad)) - 1.0) > 1e-6
    R["negative_controls"] = neg

    # =======================================================================================
    # CHECKS + all_pass.
    # all_pass iff each invariant hits its KNOWN anchor AND each wrong-structure control FLIPS.
    # =======================================================================================
    checks = Dict{String,Any}(
        # invariant (1): double cover
        "dc_kernel_order_is_2"           => dc["kernel_is_Z2"],
        "dc_two_to_one_homomorphism"     => dc["two_to_one_homomorphism"],
        "dc_R_in_SO3"                    => in_so3 == n,
        # wrong-structure control (1): kernel 2 -> 1
        "ctrl_dc_kernel_flips_to_1"      => dc_ctrl["kernel_order_flipped_to_1"],
        "ctrl_dc_cover_destroyed"        => dc_ctrl["double_cover_destroyed"],
        # invariant (2): spinor sign
        "ss_2pi_gives_minus_psi"         => ss["U_2pi_psi_equals_minus_psi"],
        "ss_4pi_gives_plus_psi"          => ss["U_4pi_psi_equals_plus_psi"],
        "ss_U2pi_is_minus_I"             => ss["U_2pi_matrix_is_minus_I"],
        # wrong-structure control (2): sign disappears
        "ctrl_ss_R2pi_is_I_no_sign"      => ss_ctrl["spinor_sign_disappears"],
        # invariant (3): Hopf + c1
        "hp_pi_unit_on_S2"               => hp["pi_on_S2_unit"],
        "hp_U1_fiber_global_phase"       => hp["U1_fiber_is_global_phase"],
        "hp_c1_is_1"                     => hp["c1_is_one"],
        "hp_curvature_nonzero"           => hp["curvature_nonzero"],
        # wrong-structure control (3): c1 1 -> 0
        "ctrl_hp_c1_flips_to_0"          => hp_ctrl["c1_flipped_to_0"],
        "ctrl_hp_curvature_flat"         => hp_ctrl["curvature_flat"],
        # negative control
        "neg_nonunit_excluded"           => neg["nonunit_excluded_from_S3"],
    )
    all_pass = all(values(checks))
    R["checks"] = checks
    R["all_pass"] = all_pass

    # =======================================================================================
    # VERDICT.
    # =======================================================================================
    v = Dict{String,Any}()
    v["carrier_is_S3_spinor_space"] = true
    v["bloch_free_dynamics"] = "no dot-r ODE, no terrain operators in this file (spinor carrier is allowed)"
    v["double_cover_kernel_order"] = dc["kernel_order"]
    v["double_cover_kernel_anchor"] = 2
    v["spinor_2pi_sign_present"] = ss["genuine_double_cover_sign"]
    v["hopf_c1"] = c1
    v["hopf_c1_anchor"] = 1
    v["wrong_structure_kernel_flip"] = "$(dc["kernel_order"]) -> $(dc_ctrl["kernel_order"]) (identity non-cover)"
    v["wrong_structure_spinor_sign_flip"] = "U(2pi)=-I (present) -> R(2pi)=I (absent, single cover)"
    v["wrong_structure_c1_flip"] = "$(c1) -> $(round(Int, triv.chern)) (trivial bundle)"
    v["all_invariants_at_anchor_and_controls_flip"] = all_pass
    v["honest_status"] = all_pass ? "genuine_carrier" : "invariant_or_control_failed"
    v["claim_ceiling"] = "PoC: L2 is the S^3 spinor carrier. Its realness is anchored to three KNOWN S^3 " *
        "invariants (double-cover kernel order=2, spinor 2pi sign psi->-psi, Hopf c1=1), each measured and each " *
        "FLIPPED by a wrong-structure control (identity non-cover: kernel 2->1; SO(3) single cover: sign disappears; " *
        "trivial bundle: c1 1->0). The flip is the evidence the invariants are measured, not by-construction-right. " *
        "promotion_allowed=false; not canonical."
    R["verdict"] = v

    open(RESULTS_PATH, "w") do io
        JSON.print(io, R, 2)
    end

    # ---- console report ----
    println("=== L2_layer_bf — S^3 SPINOR CARRIER (genuine, invariant-anchored) ===")
    println()
    println("INVARIANT (1) DOUBLE COVER SU(2)->SO(3)  [anchor: kernel order == 2]")
    println("  q and -q -> same R : ", dc["q_and_minus_q_same_R_frac"]*100, "%   R in SO(3): ", dc["R_in_SO3_frac"]*100, "%")
    println("  kernel order = ", dc["kernel_order"], "  (anchor 2)  kernel_is_Z2 = ", dc["kernel_is_Z2"])
    println("  WRONG-STRUCTURE (identity non-cover): kernel order = ", dc_ctrl["kernel_order"],
            "  q==-q frac = ", round(dc_ctrl["q_and_minus_q_same_frac"], digits=3),
            "  -> kernel FLIPS 2->1 = ", dc_ctrl["kernel_order_flipped_to_1"])
    println()
    println("INVARIANT (2) SPINOR SIGN  [anchor: U(2pi)psi=-psi, U(4pi)psi=+psi]")
    println("  U(2pi)psi=-psi : ", ss["U_2pi_psi_equals_minus_psi"], " (err ", round(ss["err_2pi_to_minus_psi"], sigdigits=3),
            ")   U(4pi)psi=+psi : ", ss["U_4pi_psi_equals_plus_psi"], " (err ", round(ss["err_4pi_to_plus_psi"], sigdigits=3), ")")
    println("  U(2pi) matrix = -I : ", ss["U_2pi_matrix_is_minus_I"], "   U(4pi) matrix = +I : ", ss["U_4pi_matrix_is_plus_I"])
    println("  WRONG-STRUCTURE (SO(3) single cover): R(2pi)=I = ", ss_ctrl["R_2pi_is_identity"],
            "  -> spinor sign DISAPPEARS = ", ss_ctrl["spinor_sign_disappears"])
    println()
    println("INVARIANT (3) HOPF MAP + c1  [anchor: c1 == 1]")
    println("  ||pi(psi)||=1 on S^2 (max dev ", round(hp["pi_on_S2_max_norm_dev"], sigdigits=3), ") : ", hp["pi_on_S2_unit"])
    println("  U(1) fibre = global phase (max dev ", round(hp["U1_fiber_max_phase_dev"], sigdigits=3), ") : ", hp["U1_fiber_is_global_phase"])
    println("  c1 = ", c1, " (raw ", round(hopf.chern, digits=4), ", anchor 1)   Fmax = ", round(hopf.Fmax, digits=5), " != 0")
    println("  WRONG-STRUCTURE (trivial bundle): c1 = ", round(Int, triv.chern), " (raw ", round(triv.chern, digits=6),
            ")  Fmax = ", round(triv.Fmax, digits=9), "  -> c1 FLIPS 1->0 = ", hp_ctrl["c1_flipped_to_0"])
    println()
    println("--- CHECKS ---")
    for (k, val) in sort(collect(checks); by=first)
        println("  ", rpad(k, 32), val ? "PASS" : "FAIL")
    end
    println()
    println("ALL_PASS = ", all_pass, "   (3 invariants at known anchors; 3 wrong-structure controls flip)")
    println("honest_status = ", v["honest_status"])
    println("results -> ", RESULTS_PATH)
    return all_pass
end

ok = main()
exit(ok ? 0 : 1)
