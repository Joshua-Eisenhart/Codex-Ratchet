# =============================================================================
# cocycle_third_section.jl
# -----------------------------------------------------------------------------
# Third independently-authored nested Weyl-on-nested-Hopf-tori cocycle section.
#
# Claim ceiling:
#   classification = cocycle_third_poc
#   promotion_allowed = false
#
# Reused primitives only, reimplemented locally to avoid include-time side
# effects from the executable primitive scripts:
#   - gamma5 Weyl split from l2_weyl_chirality_gamma5_genuine.jl
#   - nested Hopf torus foliation S3pt(theta,a,b) from G_nested_hopf_tori.jl
#   - FHS link/plaquette Wilson flux from s3_hopf_spinor_network_entanglement.jl
#
# The section is intentionally not a global phase or diagonal torus cycle:
#   theta depends on eta, while the relative Hopf-torus phase winds around x.
#   A nonseparable zero-mean twist deforms the local curvature density without
#   changing the net x winding. Controls verify that global-phase-only and
#   diagonal-cycle variants collapse.
# =============================================================================

using LinearAlgebra
using JSON

const CLASSIFICATION = "cocycle_third_poc"
const PROMOTION_ALLOWED = false
const RESULT_PATH = joinpath(@__DIR__, "cocycle_third_section_results.json")

# -- gamma5 Weyl split primitive ------------------------------------------------
const sigma0 = ComplexF64[1 0; 0 1]
const sigma1 = ComplexF64[0 1; 1 0]
const sigma2 = ComplexF64[0 -im; im 0]
const sigma3 = ComplexF64[1 0; 0 -1]
const Z2 = zeros(ComplexF64, 2, 2)
const g0 = [Z2 sigma0; sigma0 Z2]
const g1 = [Z2 sigma1; -sigma1 Z2]
const g2 = [Z2 sigma2; -sigma2 Z2]
const g3 = [Z2 sigma3; -sigma3 Z2]
const gamma5 = im * g0 * g1 * g2 * g3

# -- nested Hopf torus foliation primitive -------------------------------------
# S^3 subset C^2: (z1,z2) = (cos(theta) exp(i a), sin(theta) exp(i b)).
function nested_hopf_spinor(theta::Float64, a::Float64, b::Float64)
    v = ComplexF64[cos(theta) * cis(a), sin(theta) * cis(b)]
    return v / norm(v)
end

function s3pt(theta::Float64, a::Float64, b::Float64)
    return [
        cos(theta) * cos(a),
        cos(theta) * sin(a),
        sin(theta) * cos(b),
        sin(theta) * sin(b),
    ]
end

# -- FHS link / plaquette primitive --------------------------------------------
function fhs_link(psi_a::Vector{ComplexF64}, psi_b::Vector{ComplexF64})
    z = dot(psi_a, psi_b)
    az = abs(z)
    return az < 1e-14 ? ComplexF64(1.0) : z / az
end

function plaquette_flux(p00::Vector{ComplexF64}, p10::Vector{ComplexF64},
                        p11::Vector{ComplexF64}, p01::Vector{ComplexF64})
    return angle(fhs_link(p00, p10) * fhs_link(p10, p11) *
                 fhs_link(p11, p01) * fhs_link(p01, p00))
end

function mixed_winding(section_fn; eta_band::Float64, neta::Int=82, nx::Int=144)
    etas = collect(range(-eta_band, eta_band, length=neta + 1))
    xs = [2pi * j / nx for j in 0:nx-1]
    psi = Array{Vector{ComplexF64}}(undef, neta + 1, nx)
    for i in 1:(neta + 1), j in 1:nx
        psi[i, j] = section_fn(etas[i], xs[j])
    end
    total = 0.0
    max_abs_plaquette = 0.0
    for i in 1:neta, j in 1:nx
        jp = j % nx + 1
        f = plaquette_flux(psi[i, j], psi[i + 1, j], psi[i + 1, jp], psi[i, jp])
        total += f
        max_abs_plaquette = max(max_abs_plaquette, abs(f))
    end
    return total / (2pi), max_abs_plaquette
end

function mixed_product_winding(section_a, section_b; eta_band::Float64, neta::Int=82, nx::Int=144)
    etas = collect(range(-eta_band, eta_band, length=neta + 1))
    xs = [2pi * j / nx for j in 0:nx-1]
    a = Array{Vector{ComplexF64}}(undef, neta + 1, nx)
    b = Array{Vector{ComplexF64}}(undef, neta + 1, nx)
    for i in 1:(neta + 1), j in 1:nx
        a[i, j] = section_a(etas[i], xs[j])
        b[i, j] = section_b(etas[i], xs[j])
    end
    total = 0.0
    max_abs_plaquette = 0.0
    for i in 1:neta, j in 1:nx
        jp = j % nx + 1
        u12 = fhs_link(a[i, j], a[i + 1, j]) * fhs_link(b[i, j], b[i + 1, j])
        u23 = fhs_link(a[i + 1, j], a[i + 1, jp]) * fhs_link(b[i + 1, j], b[i + 1, jp])
        u34 = fhs_link(a[i + 1, jp], a[i, jp]) * fhs_link(b[i + 1, jp], b[i, jp])
        u41 = fhs_link(a[i, jp], a[i, j]) * fhs_link(b[i, jp], b[i, j])
        f = angle(u12 * u23 * u34 * u41)
        total += f
        max_abs_plaquette = max(max_abs_plaquette, abs(f))
    end
    return total / (2pi), max_abs_plaquette
end

# -- third section --------------------------------------------------------------
# eta moves through genuinely nested leaves. The x cycle is a torus cycle; the
# relative phase winds with chirality-dependent sign. The eta*x twist has zero
# net x winding but proves the local section is not a diagonal/global-phase-only
# cycle.
theta_nested(eta::Float64) = pi / 4 + 0.245 * tanh(0.86 * eta) + 0.018 * sin(2.0 * eta)
theta_mid(eta::Float64) = pi / 4
twist(eta::Float64, x::Float64) = 0.23 * sin(eta) * sin(2.0 * x) + 0.07 * sin(2.0 * eta) * cos(3.0 * x)

function third_weyl_section(eta::Float64, x::Float64; chirality::Symbol=:L, decoupled_eta::Bool=false)
    theta = decoupled_eta ? theta_mid(eta) : theta_nested(eta)
    # a carries a nontrivial torus cycle, not just a gauge factor.
    a = 0.31 * sin(eta) + 0.11 * sin(x + eta)
    rel = x + twist(eta, x)
    b = chirality == :L ? a + rel : a - rel
    return nested_hopf_spinor(theta, a, b)
end

left_section(eta, x) = third_weyl_section(eta, x; chirality=:L)
right_section(eta, x) = third_weyl_section(eta, x; chirality=:R)
left_decoupled(eta, x) = third_weyl_section(eta, x; chirality=:L, decoupled_eta=true)
right_decoupled(eta, x) = third_weyl_section(eta, x; chirality=:R, decoupled_eta=true)
erased_right_section(eta, x) = left_section(eta, x)

function global_phase_only_section(eta::Float64, x::Float64)
    theta = theta_nested(eta)
    # Same phase on both Hopf components: relative phase is constant.
    phase = x + 0.2 * sin(eta) + twist(eta, x)
    return nested_hopf_spinor(theta, phase, phase)
end

function diagonal_cycle_section(eta::Float64, x::Float64)
    theta = theta_nested(eta)
    # Diagonal torus cycle a == b. This has moving leaves but no relative
    # Hopf-torus phase, so the mixed eta-x curvature should collapse.
    return nested_hopf_spinor(theta, x + 0.13 * sin(eta), x + 0.13 * sin(eta))
end

function dirac_lift(two_spinor::Vector{ComplexF64}; chirality::Symbol)
    if chirality == :L
        return ComplexF64[two_spinor[1], two_spinor[2], 0, 0]
    elseif chirality == :R
        return ComplexF64[0, 0, two_spinor[1], two_spinor[2]]
    else
        error("chirality must be :L or :R")
    end
end

function gamma5_charge(spinor4::Vector{ComplexF64})
    return real(dot(spinor4, gamma5 * spinor4))
end

function analytic_band_prediction(eta_band::Float64)
    hi = sin(theta_nested(eta_band))^2
    lo = sin(theta_nested(-eta_band))^2
    # Sign convention is measured by the FHS routine; this is the expected
    # magnitude from integral d(sin^2(theta)) wedge d(relative_phase).
    return abs(hi - lo)
end

function band_row(eta_band::Float64; neta::Int=82, nx::Int=144)
    w_l, p_l = mixed_winding(left_section; eta_band=eta_band, neta=neta, nx=nx)
    w_r, p_r = mixed_winding(right_section; eta_band=eta_band, neta=neta, nx=nx)
    w_glue, p_glue = mixed_product_winding(left_section, right_section; eta_band=eta_band, neta=neta, nx=nx)
    w_dec_l, p_dec_l = mixed_winding(left_decoupled; eta_band=eta_band, neta=neta, nx=nx)
    w_dec_r, p_dec_r = mixed_winding(right_decoupled; eta_band=eta_band, neta=neta, nx=nx)
    w_erased_r, p_erased_r = mixed_winding(erased_right_section; eta_band=eta_band, neta=neta, nx=nx)
    w_erased_glue, p_erased_glue = mixed_product_winding(left_section, erased_right_section; eta_band=eta_band, neta=neta, nx=nx)
    w_global, p_global = mixed_winding(global_phase_only_section; eta_band=eta_band, neta=neta, nx=nx)
    w_diag, p_diag = mixed_winding(diagonal_cycle_section; eta_band=eta_band, neta=neta, nx=nx)
    return Dict(
        "eta_band" => eta_band,
        "w_L" => w_l,
        "w_R" => w_r,
        "abs_w_L" => abs(w_l),
        "abs_w_R" => abs(w_r),
        "abs_band_delta" => abs(abs(w_l) - abs(w_r)),
        "signs_opposite" => sign(w_l) == -sign(w_r),
        "partial_solid_angle_prediction_abs" => analytic_band_prediction(eta_band),
        "glued_product_control_w" => w_glue,
        "glued_product_control_abs" => abs(w_glue),
        "eta_decoupled_control_w_L" => w_dec_l,
        "eta_decoupled_control_w_R" => w_dec_r,
        "eta_decoupled_control_abs_max" => max(abs(w_dec_l), abs(w_dec_r)),
        "erased_chirality_R_copy_w" => w_erased_r,
        "erased_chirality_same_sign" => sign(w_l) == sign(w_erased_r),
        "erased_chirality_glued_product_w" => w_erased_glue,
        "global_phase_only_control_w" => w_global,
        "global_phase_only_control_abs" => abs(w_global),
        "diagonal_cycle_control_w" => w_diag,
        "diagonal_cycle_control_abs" => abs(w_diag),
        "max_abs_plaquette" => Dict(
            "L" => p_l,
            "R" => p_r,
            "glued_product" => p_glue,
            "eta_decoupled_L" => p_dec_l,
            "eta_decoupled_R" => p_dec_r,
            "erased_R" => p_erased_r,
            "erased_glued_product" => p_erased_glue,
            "global_phase_only" => p_global,
            "diagonal_cycle" => p_diag,
        ),
    )
end

function main()
    println("="^78)
    println("cocycle_third_section: nested gamma5-chiral lift over Hopf-torus foliation")
    println("="^78)

    base_band = 0.55
    bands = [0.35, base_band, 0.75, 0.95]
    rows = [band_row(b) for b in bands]
    base = rows[findfirst(r -> isapprox(r["eta_band"], base_band; atol=1e-12), rows)]

    l4 = dirac_lift(left_section(0.17, 1.1); chirality=:L)
    r4 = dirac_lift(right_section(0.17, 1.1); chirality=:R)
    gamma5_ok = isapprox(gamma5_charge(l4), -1.0; atol=1e-12) &&
                isapprox(gamma5_charge(r4), 1.0; atol=1e-12)

    theta_values = [theta_nested(e) for e in range(-maximum(bands), maximum(bands), length=41)]
    theta_interior = all(0.0 < t < pi / 2 for t in theta_values)
    s3_norm_max_err = maximum(abs(norm(s3pt(theta_nested(e), x, x + twist(e, x))) - 1.0)
                              for e in range(-base_band, base_band, length=23)
                              for x in range(0, 2pi, length=25)[1:end-1])

    reproduces = base["signs_opposite"] &&
                 base["glued_product_control_abs"] < 1e-6 &&
                 base["eta_decoupled_control_abs_max"] < 1e-6 &&
                 base["erased_chirality_same_sign"]
    verdict = reproduces ? "third_section_reproduces" : "third_section_differs"

    checks = Dict(
        "gamma5_LR_lift_charges" => gamma5_ok,
        "theta_stays_inside_non_degenerate_nested_leaves" => theta_interior,
        "s3_embedding_unit_norm" => s3_norm_max_err < 1e-12,
        "opposite_sign_L_R" => base["signs_opposite"],
        "glued_product_control_collapses" => base["glued_product_control_abs"] < 1e-6,
        "eta_decoupled_control_collapses" => base["eta_decoupled_control_abs_max"] < 1e-6,
        "erased_chirality_same_sign" => base["erased_chirality_same_sign"],
        "global_phase_only_control_collapses" => base["global_phase_only_control_abs"] < 1e-6,
        "diagonal_cycle_control_collapses" => base["diagonal_cycle_control_abs"] < 1e-6,
    )

    result = Dict(
        "name" => "cocycle_third_section",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "chiral_nested_hopf_mixed_cocycle_presence_probe",
        "root_constraints_in_force" => [
            "F01 finite eta-band x torus-cycle lattice over nested Hopf-torus leaves",
            "N01 order-sensitive eta<->torus Wilson plaquette from FHS link products",
        ],
        "finite_map" => "finite lattice (eta_i,x_j) -> normalized Hopf-torus spinor -> U(1) FHS plaquette flux -> mixed Wilson winding",
        "domain" => "eta bands [-B,B] crossed with periodic torus cycle x in [0,2pi), using nondegenerate nested leaves theta(eta) in (0,pi/2)",
        "codomain_or_output" => "mixed eta<->torus Wilson-plaquette winding for gamma5-left and gamma5-right Weyl blocks plus controls",
        "carrier_layer" => "nested_hopf_tori_gamma5_chiral_lift",
        "geometry_layer" => "S3 nested Hopf tori foliation with torus angles a,b and relative phase b-a",
        "carrier_realization" => "Julia ComplexF64 spinors; 2-component Hopf-torus spinors lifted into 4-component gamma5 Weyl blocks",
        "peps3d_embedding" => "finite eta-x plaquette lattice treated as local PEPS3D-compatible cell anchors; no PEPS3D promotion claimed",
        "spinor_state" => "normalized ComplexF64 Hopf spinors and gamma5-left/right Dirac lifts",
        "quaternion_action" => "not_applicable",
        "dependency_receipts" => [
            "system_v5/julia_carrier/layers/l2_weyl_chirality_gamma5_genuine.jl",
            "system_v5/julia_carrier/layers/G_nested_hopf_tori.jl",
            "system_v5/julia_carrier/layers/s3_hopf_spinor_network_entanglement.jl",
        ],
        "downstream_blocks" => ["flux", "Xi", "Phi0", "Axis0", "bridge", "basin", "physics", "manifold_completion"],
        "allowed_claims" => "presence-only third-section cocycle reproduction if controls pass; no monopole bar, no completion, no promotion",
        "promotion_blockers" => [
            "PoC only",
            "ComplexF64 Julia carrier, not torch-native PEPS3D implementation",
            "partial solid angle |w| < 0.5",
            "no full proof packet or formal theorem",
        ],
        "required_tools" => ["LinearAlgebra", "JSON"],
        "actual_tools_used" => ["LinearAlgebra", "JSON"],
        "tool_manifest" => Dict(
            "LinearAlgebra" => Dict("used" => true, "reason" => "normalized spinor carrier and gamma5 charge checks"),
            "JSON" => Dict("used" => true, "reason" => "writes audit receipt"),
        ),
        "TOOL_MANIFEST" => Dict(
            "LinearAlgebra" => Dict("used" => true, "reason" => "normalized spinor carrier and gamma5 charge checks"),
            "JSON" => Dict("used" => true, "reason" => "writes audit receipt"),
        ),
        "tool_integration_depth" => Dict("LinearAlgebra" => "load_bearing", "JSON" => "supportive"),
        "TOOL_INTEGRATION_DEPTH" => Dict("LinearAlgebra" => "load_bearing", "JSON" => "supportive"),
        "required_negatives" => [
            "glued-product L*R control",
            "eta-decoupled control",
            "erased-chirality R=copy(L) control",
            "global-phase-only control",
            "diagonal-cycle control",
        ],
        "negatives_run" => [
            "glued-product L*R control",
            "eta-decoupled control",
            "erased-chirality R=copy(L) control",
            "global-phase-only control",
            "diagonal-cycle control",
        ],
        "kill_conditions" => [
            "L/R signs not opposite",
            "glued-product control >= 1e-6",
            "eta-decoupled control >= 1e-6",
            "erased chirality fails to produce same sign",
        ],
        "witness_trace_id" => "cocycle_third_section_eta_x_fhs_v1",
        "base_eta_band" => base_band,
        "base_result" => base,
        "band_dependence" => rows,
        "checks" => checks,
        "all_pass" => all(values(checks)) && reproduces,
        "verdict" => verdict,
        "honest_status" => "passes local rerun if this script exits 0 and JSON matches printed verdict",
        "claim_ceiling" => "Presence-bar hardening only: opposite-sign mixed cocycle with collapsing controls. This is not a >=0.5 monopole-strength claim and not construction-independent proof by itself.",
    )

    println("base eta band: ", base_band)
    println("w_L = ", base["w_L"], " |w_L| = ", base["abs_w_L"])
    println("w_R = ", base["w_R"], " |w_R| = ", base["abs_w_R"])
    println("glued-product control |w| = ", base["glued_product_control_abs"])
    println("eta-decoupled control max |w| = ", base["eta_decoupled_control_abs_max"])
    println("erased-chirality R=copy(L) w = ", base["erased_chirality_R_copy_w"],
            " same_sign = ", base["erased_chirality_same_sign"])
    println("global-phase-only control |w| = ", base["global_phase_only_control_abs"])
    println("diagonal-cycle control |w| = ", base["diagonal_cycle_control_abs"])
    println("\nband dependence:")
    for row in rows
        println("  B=", row["eta_band"],
                " w_L=", row["w_L"],
                " w_R=", row["w_R"],
                " |w|=", row["abs_w_L"],
                " glue=", row["glued_product_control_abs"],
                " dec=", row["eta_decoupled_control_abs_max"])
    end
    println("\nVERDICT: ", verdict)

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
    end
    println("wrote: ", RESULT_PATH)
end

main()
