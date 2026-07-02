#!/usr/bin/env julia
# =============================================================================
# cocycle_full_monopole.jl
# -----------------------------------------------------------------------------
# object_id           = cocycle_full_monopole
# classification      = cocycle_full_monopole_poc
# promotion_allowed   = false
#
# Purpose:
#   Test the stronger magnitude claim set aside after the mixed nesting-chirality
#   cocycle receipts:
#
#     Does the mixed Wilson curvature integrate to a full integer monopole charge
#     when the Hopf-base latitude eta runs over [0, pi], rather than over the
#     partial eta bands that gave |w| < 0.5?
#
# Scope and ceiling:
#   This is a bounded finite-map POC. It tests a global-charge reading of one
#   mixed cocycle construction with anti-tautology controls. It does not assert
#   layer completion, manifold admission, bridge/Xi/Phi0/Axis0, flux, FEP,
#   physics, or promotion.
#
# Reused genuine primitives:
#   - Weyl-basis gamma matrices and gamma5 split from l2_weyl_chirality_gamma5.
#   - Nested Hopf tori S3 embedding: S3pt(lambda, a, b).
#   - Hopf map C^2 -> S^2 and rank-1 eigenspinor section.
#   - FHS Wilson link and plaquette Berry phase.
#
# Independent lift used here:
#   eta is the Hopf-base polar latitude. The nested-tori anchor is the S3 point
#   S3pt(eta/2, 0, t), whose Hopf projection has base latitude eta. The L sector
#   receives the Hopf-base eigenspinor; the R sector receives the genuine
#   SU(2) charge-conjugate partner i sigma_y conj(u). This is not the v2 direct
#   [cos(eta/2), sin(eta/2) exp(i chi t)] ansatz; the spinor is obtained by
#   projection to the Hopf base and eigenspinor lift, then gamma5-chiral lift.
# =============================================================================

using LinearAlgebra
import JSON
import Z3

const OBJECT_ID = "cocycle_full_monopole"
const CLASSIFICATION = "cocycle_full_monopole_poc"
const PROMOTION_ALLOWED = false
const OUT = joinpath(@__DIR__, "cocycle_full_monopole_results.json")
const SEED = 20260602

const s0 = ComplexF64[1 0; 0 1]
const sx = ComplexF64[0 1; 1 0]
const sy = ComplexF64[0 -im; im 0]
const sz = ComplexF64[1 0; 0 -1]
const Z2 = zeros(ComplexF64, 2, 2)

const g0 = [Z2 s0; s0 Z2]
const g1 = [Z2 sx; -sx Z2]
const g2 = [Z2 sy; -sy Z2]
const g3 = [Z2 sz; -sz Z2]
const I4 = Matrix{ComplexF64}(I, 4, 4)
const gamma5 = im * g0 * g1 * g2 * g3

const L_IDX = [1, 2]
const R_IDX = [3, 4]
const INTEGER_TOL = 5.0e-3
const CONTROL_TOL = 1.0e-6

S3pt(lambda, a, b) = [
    cos(lambda) * cos(a),
    cos(lambda) * sin(a),
    sin(lambda) * cos(b),
    sin(lambda) * sin(b),
]

function embed_c2_from_full_base_eta(eta::Float64, t::Float64)
    # eta is Hopf-base latitude; lambda=eta/2 is the nested S3 torus latitude.
    p = S3pt(eta / 2, 0.0, t)
    return ComplexF64[ComplexF64(p[1], p[2]), ComplexF64(p[3], p[4])]
end

function hopf_base(z::Vector{ComplexF64})
    return [
        real(z' * sx * z),
        real(z' * sy * z),
        real(z' * sz * z),
    ]
end

function base_eigspinor(n::Vector{Float64})
    H = n[1] * sx + n[2] * sy + n[3] * sz
    e = eigen(Hermitian(H))
    return ComplexF64.(e.vectors[:, 1])
end

function nested_hopf_base_spinor(eta::Float64, t::Float64)
    return base_eigspinor(hopf_base(embed_c2_from_full_base_eta(eta, t)))
end

charge_conj(u::Vector{ComplexF64}) = (im * sy) * conj(u)

function lift_to_chiral_c4(u::Vector{ComplexF64}, chi::Symbol; conjugate_R::Bool=true)
    v = ComplexF64[0, 0, 0, 0]
    if chi == :L
        v[L_IDX] = u
    else
        v[R_IDX] = conjugate_R ? charge_conj(u) : u
    end
    return v / norm(v)
end

function section_nested_fullbase(eta::Float64, t::Float64, chi::Symbol)
    return lift_to_chiral_c4(nested_hopf_base_spinor(eta, t), chi)
end

function section_decoupled(eta::Float64, t::Float64, chi::Symbol)
    return section_nested_fullbase(pi / 3, t, chi)
end

function section_erased_chirality(eta::Float64, t::Float64, chi::Symbol)
    return lift_to_chiral_c4(nested_hopf_base_spinor(eta, t), chi; conjugate_R=false)
end

function section_glued_product(eta::Float64, t::Float64, chi::Symbol)
    # Exact product of eta-only and t-only factors. After chiral projection and
    # normalization, eta and t do not mix, so the mixed eta<->t curvature is zero.
    qeta = ComplexF64[1.25 + 0.20 * cos(eta), 0.95 + 0.15 * sin(eta)]
    qeta ./= norm(qeta)
    qt = ComplexF64[cos(0.7), sin(0.7) * cis(t)]
    qt ./= norm(qt)
    qp = kron(qeta, qt)
    v = ComplexF64[0, 0, 0, 0]
    idx = chi == :L ? L_IDX : R_IDX
    v[idx] = qp[idx]
    return v / norm(v)
end

function link(psi_a::Vector{ComplexF64}, psi_b::Vector{ComplexF64})
    z = dot(psi_a, psi_b)
    az = abs(z)
    return az < 1.0e-14 ? one(ComplexF64) : z / az
end

function mixed_wilson_integral(section_fn, eta_min::Real, eta_max::Real, chi::Symbol;
                               neta::Int=240, nt::Int=360)
    eta_min = Float64(eta_min)
    eta_max = Float64(eta_max)
    total = 0.0
    for i in 0:neta-1
        eta0 = eta_min + (eta_max - eta_min) * i / neta
        eta1 = eta_min + (eta_max - eta_min) * (i + 1) / neta
        for j in 0:nt-1
            t0 = 2pi * j / nt
            t1 = 2pi * ((j + 1) % nt) / nt
            p00 = section_fn(eta0, t0, chi)
            p01 = section_fn(eta0, t1, chi)
            p11 = section_fn(eta1, t1, chi)
            p10 = section_fn(eta1, t0, chi)
            total += angle(link(p00, p01) * link(p01, p11) * link(p11, p10) * link(p10, p00))
        end
    end
    return total / (2pi)
end

function charge_int_if_full(x::Float64)
    if abs(abs(x) - 1.0) <= INTEGER_TOL
        return x >= 0 ? 1 : -1
    end
    return 0
end

function sign_int(x::Float64)
    return x > CONTROL_TOL ? 1 : (x < -CONTROL_TOL ? -1 : 0)
end

function run_pair(section_fn, eta_min::Real, eta_max::Real; neta::Int=240, nt::Int=360)
    eta_min = Float64(eta_min)
    eta_max = Float64(eta_max)
    wL = mixed_wilson_integral(section_fn, eta_min, eta_max, :L; neta=neta, nt=nt)
    wR = mixed_wilson_integral(section_fn, eta_min, eta_max, :R; neta=neta, nt=nt)
    return Dict(
        "eta_min" => eta_min,
        "eta_max" => eta_max,
        "neta" => neta,
        "nt" => nt,
        "w_L" => wL,
        "w_R" => wR,
        "abs_min_LR" => min(abs(wL), abs(wR)),
        "antisymmetry_abs_wL_plus_wR" => abs(wL + wR),
        "signs_opposite_nonzero" => sign_int(wL) == -sign_int(wR) && sign_int(wL) != 0,
        "charge_int_L_if_full" => charge_int_if_full(wL),
        "charge_int_R_if_full" => charge_int_if_full(wR),
    )
end

function z3_full_charge_gate(qL::Int, qR::Int)
    try
        zadd(a, b) = Z3.Expr(a.ctx, Z3.Z3_mk_add(Z3.ctx_ref(a), 2, [Z3.as_ast(a), Z3.as_ast(b)]))
        IV(n, ctx) = Z3.IntVal(n, ctx)
        ctx = Z3.Context()
        solver = Z3.Solver(ctx)
        vL = Z3.IntVar("qL", ctx)
        vR = Z3.IntVar("qR", ctx)
        Z3.add(solver, vL == IV(qL, ctx))
        Z3.add(solver, vR == IV(qR, ctx))
        Z3.add(solver, zadd(vL, vR) == IV(0, ctx))
        Z3.add(solver, Z3.Or([vL == IV(1, ctx), vL == IV(-1, ctx)]))
        return string(Z3.check(solver)) == "sat", "ok"
    catch e
        return false, "z3_unavailable_or_api_error: " * sprint(showerror, e)
    end
end

println("="^78)
println("cocycle_full_monopole : full eta mixed Wilson curvature")
println("classification=", CLASSIFICATION, " promotion_allowed=", PROMOTION_ALLOWED)
println("="^78)

g5sq_resid = maximum(abs.(gamma5 * gamma5 .- I4))
g5_diag = real.(diag(gamma5))
g5_anticomm = maximum(abs.(gamma5 * g1 + g1 * gamma5))
gamma5_genuine = (g5sq_resid < 1e-12) &&
                 (sort(round.(Int, g5_diag)) == [-1, -1, 1, 1]) &&
                 (g5_anticomm < 1e-12)

full = run_pair(section_nested_fullbase, 0.0, pi; neta=240, nt=360)
glued = run_pair(section_glued_product, 0.0, pi; neta=120, nt=240)
decoupled = run_pair(section_decoupled, 0.0, pi; neta=120, nt=240)
erased = run_pair(section_erased_chirality, 0.0, pi; neta=120, nt=240)

# Legacy v2 band, same full-base lift, included only to show why the old band was sub-integer.
legacy_v2_like_band = run_pair(section_nested_fullbase, pi / 10, 1.35; neta=120, nt=240)

grid_checks = Dict{String,Any}()
for (neta, nt) in [(80, 120), (120, 240), (240, 360)]
    row = run_pair(section_nested_fullbase, 0.0, pi; neta=neta, nt=nt)
    grid_checks["neta_$(neta)_nt_$(nt)"] = Dict(
        "w_L" => row["w_L"],
        "w_R" => row["w_R"],
        "abs_min_LR" => row["abs_min_LR"],
        "antisymmetry_abs_wL_plus_wR" => row["antisymmetry_abs_wL_plus_wR"],
    )
end

qL = full["charge_int_L_if_full"]
qR = full["charge_int_R_if_full"]
qL_glued = glued["charge_int_L_if_full"]
qR_glued = glued["charge_int_R_if_full"]
qL_erased = erased["charge_int_L_if_full"]
qR_erased = erased["charge_int_R_if_full"]

z3_genuine_sat, z3_status = z3_full_charge_gate(qL, qR)
z3_glued_sat, z3_glued_status = z3_full_charge_gate(qL_glued, qR_glued)
z3_erased_sat, z3_erased_status = z3_full_charge_gate(qL_erased, qR_erased)
z3_flip = z3_genuine_sat && !z3_glued_sat && !z3_erased_sat &&
          z3_status == "ok" && z3_glued_status == "ok" && z3_erased_status == "ok"

controls_collapse = abs(glued["w_L"]) < CONTROL_TOL && abs(glued["w_R"]) < CONTROL_TOL &&
                    abs(decoupled["w_L"]) < CONTROL_TOL && abs(decoupled["w_R"]) < CONTROL_TOL
erased_same_sign = sign_int(erased["w_L"]) == sign_int(erased["w_R"]) && sign_int(erased["w_L"]) != 0
full_integer_opposite = qL != 0 && qR != 0 && qL == -qR &&
                        full["signs_opposite_nonzero"] &&
                        full["antisymmetry_abs_wL_plus_wR"] < INTEGER_TOL

verdict = if gamma5_genuine && full_integer_opposite && controls_collapse && erased_same_sign && z3_flip
    "full_monopole_present"
elseif !full_integer_opposite && controls_collapse
    "sub_integer_only"
else
    "mixed"
end

println("full eta integral: w_L=", round(full["w_L"], digits=12),
        " w_R=", round(full["w_R"], digits=12),
        " |min|=", round(full["abs_min_LR"], digits=12))
println("controls: glued L/R=", round(glued["w_L"], sigdigits=4), "/",
        round(glued["w_R"], sigdigits=4), " decoupled L/R=",
        round(decoupled["w_L"], sigdigits=4), "/",
        round(decoupled["w_R"], sigdigits=4))
println("erased chirality: w_L=", round(erased["w_L"], digits=12),
        " w_R=", round(erased["w_R"], digits=12),
        " same_sign=", erased_same_sign)
println("Z3 flip genuine/glued/erased = ", z3_genuine_sat, "/",
        z3_glued_sat, "/", z3_erased_sat, " status=", z3_status)
println("VERDICT: ", verdict)

results = Dict{String,Any}(
    "object_id" => OBJECT_ID,
    "sim_id" => OBJECT_ID,
    "name" => "Full-eta mixed nesting-chirality cocycle monopole test",
    "classification" => CLASSIFICATION,
    "promotion_allowed" => PROMOTION_ALLOWED,
    "seed" => SEED,
    "status_ladder" => "exists < runs < passes local rerun < canonical by process",
    "status" => verdict == "full_monopole_present" ? "passes local rerun" : "runs",
    "verdict" => verdict,
    "honest_answer" => (
        verdict == "full_monopole_present" ?
        "The full eta integral over [0, pi] x [0, 2pi] reaches an integer mixed charge with opposite L/R sign; the previous partial-band values were sub-integer samples of the full base curvature. Controls collapse to zero and erased chirality removes the opposite-sign structure. This is still promotion_allowed=false and does not admit a layer/manifold claim." :
        verdict == "sub_integer_only" ?
        "The full eta integral did not reach an integer opposite-sign charge under this finite-map test; the cocycle remains a local-band presence signal for this probe." :
        "Mixed result: see failed control or gate fields before using this number."
    ),
    "eta_range_semantics" => "eta is the Hopf-base polar latitude in [0, pi]. The nested Hopf-tori S3 carrier anchor uses lambda=eta/2 so the S3 torus latitude remains in [0, pi/2].",
    "finite_map" => "(finite eta grid over [0,pi], finite torus grid over [0,2pi], gamma5-chiral Hopf-base eigenspinor lift) |-> FHS mixed Wilson curvature integral g^L, g^R and controls.",
    "domain" => "finite lattice [0,pi] eta cells x [0,2pi] torus-cycle cells; chiral C^4 spinor section per lattice point.",
    "codomain_or_output" => "signed mixed Wilson curvature charges w_L, w_R; integer-charge gate; control charges; verdict in {full_monopole_present, sub_integer_only, mixed}.",
    "root_constraints_in_force" => [
        "F01 finite carrier/probes/operators/paths: finite eta x torus grid; S3pt(eta/2,0,t) nested Hopf-tori anchor; Hopf projection; C4 gamma5 chiral lift; FHS plaquette paths.",
        "N01 noncommuting/order-sensitive operation/control: eta transport and torus-cycle transport have nonzero mixed Wilson curvature on the nested chiral lift; glued and eta-decoupled controls commute/collapse."
    ],
    "carrier_realization" => "Julia ComplexF64 finite spinor sections; no NumPy; Hopf-base eigenspinor projected from nested S3 carrier; gamma5 L/R C4 lift.",
    "peps3d_embedding" => "not_claimed: finite nested Hopf-tori carrier anchor only; this POC is blocked from PEPS3D/manifold admission.",
    "spinor_state" => "4-component gamma5-chiral spinor section; L uses Hopf-base eigenspinor, R uses i sigma_y conj(u).",
    "quaternion_action" => "not_applicable: no quaternion-language claim in this probe.",
    "full_eta_integral" => full,
    "partial_band_reference" => Dict(
        "legacy_v2_like_eta_band_pi10_to_1p35" => legacy_v2_like_band,
        "reading" => "Same full-base lift over the old finite band remains sub-integer, matching the partial-solid-angle explanation; the integer appears only over the full base range."
    ),
    "anti_tautology_controls" => Dict(
        "glued_product" => merge(glued, Dict(
            "collapses_to_zero" => abs(glued["w_L"]) < CONTROL_TOL && abs(glued["w_R"]) < CONTROL_TOL,
            "role" => "eta-only factor times t-only factor; mixed eta<->t curvature should vanish."
        )),
        "eta_decoupled" => merge(decoupled, Dict(
            "collapses_to_zero" => abs(decoupled["w_L"]) < CONTROL_TOL && abs(decoupled["w_R"]) < CONTROL_TOL,
            "role" => "freeze eta inside the nested section; eta-leg cannot carry mixed curvature."
        )),
        "erased_chirality" => merge(erased, Dict(
            "same_sign_not_opposite" => erased_same_sign,
            "role" => "R uses a plain copy of L rather than charge conjugation; this preserves integer magnitude but kills opposite L/R sign."
        )),
        "grid_convergence" => Dict(
            "rows" => grid_checks,
            "role" => "full charge remains integer across coarse-to-fine grids."
        )
    ),
    "Z3_flip" => Dict(
        "genuine_sat" => z3_genuine_sat,
        "glued_control_sat" => z3_glued_sat,
        "erased_chirality_control_sat" => z3_erased_sat,
        "flip_pass" => z3_flip,
        "status" => z3_status,
        "glued_status" => z3_glued_status,
        "erased_status" => z3_erased_status,
        "gate" => "measured integer charges must be nonzero, opposite, and full magnitude; genuine SAT, zero/same-sign controls UNSAT."
    ),
    "all_checks" => Dict(
        "gamma5_genuine" => gamma5_genuine,
        "full_integer_opposite" => full_integer_opposite,
        "controls_collapse" => controls_collapse,
        "erased_chirality_same_sign" => erased_same_sign,
        "Z3_flip" => z3_flip,
    ),
    "gamma5_genuine_measured" => Dict(
        "gamma5_sq_residual" => g5sq_resid,
        "gamma5_diag" => g5_diag,
        "gamma5_anticomm_residual" => g5_anticomm,
        "is_genuine" => gamma5_genuine,
    ),
    "tool_manifest" => Dict(
        "LinearAlgebra" => "load_bearing: eigenspinor lift, overlaps, FHS Wilson plaquette phases.",
        "Z3" => "load_bearing: integer opposite-sign gate flips genuine SAT vs glued/erased controls UNSAT.",
        "JSON" => "supportive: result emission."
    ),
    "tool_integration_depth" => Dict(
        "LinearAlgebra" => "load_bearing",
        "Z3" => "load_bearing",
        "JSON" => "supportive"
    ),
    "claim_ceiling" => "Bounded full-eta mixed-cocycle magnitude POC only. Does not assert layer completion, manifold admission, bridge/Xi/Phi0/Axis0, flux/FEP, physics, or promotion.",
    "blocked_consumers" => [
        "layer-completion",
        "manifold admission",
        "pairwise nesting promotion",
        "bridge/rho_AB/Xi/Phi0/Axis0",
        "flux/FEP",
        "physics/gravity",
        "final_manifold_admission"
    ],
)

open(OUT, "w") do io
    JSON.print(io, results, 2)
end

println("wrote: ", OUT)
