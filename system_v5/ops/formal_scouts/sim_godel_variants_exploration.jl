#!/usr/bin/env julia

using Dates
using JSON3
using Symbolics

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/sim_godel_variants_exploration.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/godel_variants_exploration_results.json")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const CLAIM_CEILING = "HORIZON ansatz EXPLORATION: implied stress-energy + CTC of 3 model-aligned Godel modifications as MATH facts; NOT physics, NOT canonical, NOT derived solutions."

@variables t x y z Omega
@variables ax ay az axd ayd azd axdd aydd azdd
@variables phi phid phidd

const COORD_NAMES = ["t", "x", "y", "z"]
const DT = Differential(t)
const DX = Differential(x)
const DY = Differential(y)
const DZ = Differential(z)
const DAX = Differential(ax)
const DAY = Differential(ay)
const DAZ = Differential(az)
const DAXD = Differential(axd)
const DAYD = Differential(ayd)
const DAZD = Differential(azd)
const DPHI = Differential(phi)
const DPHID = Differential(phid)

function zero_num()
    return Num(0)
end

function simp(expr)
    return Symbolics.expand_derivatives(expr)
end

function final_simp(expr)
    expanded = Symbolics.expand_derivatives(expr)
    return Symbolics.simplify(expanded, expand=false)
end

function partial(expr, mu::Int)
    if mu == 1
        raw = Symbolics.expand_derivatives(DT(expr))
        raw += axd * Symbolics.expand_derivatives(DAX(expr))
        raw += ayd * Symbolics.expand_derivatives(DAY(expr))
        raw += azd * Symbolics.expand_derivatives(DAZ(expr))
        raw += axdd * Symbolics.expand_derivatives(DAXD(expr))
        raw += aydd * Symbolics.expand_derivatives(DAYD(expr))
        raw += azdd * Symbolics.expand_derivatives(DAZD(expr))
        raw += phid * Symbolics.expand_derivatives(DPHI(expr))
        raw += phidd * Symbolics.expand_derivatives(DPHID(expr))
        return simp(raw)
    elseif mu == 2
        return simp(Symbolics.expand_derivatives(DX(expr)))
    elseif mu == 3
        return simp(Symbolics.expand_derivatives(DY(expr)))
    elseif mu == 4
        return simp(Symbolics.expand_derivatives(DZ(expr)))
    end
    error("coordinate index out of range: $mu")
end

function component_key(i::Int, j::Int)
    return COORD_NAMES[i] * COORD_NAMES[j]
end

function expr_string(expr)
    return string(final_simp(expr))
end

function zero_string(s::String)
    return s == "0" || s == "0//1" || s == "0.0"
end

function symbolic_equal(left, right)
    return zero_string(expr_string(left - right))
end

function matrix_strings(mat)
    return [[expr_string(mat[i, j]) for j in axes(mat, 2)] for i in axes(mat, 1)]
end

function nonzero_matrix_components(mat)
    out = Dict{String,String}()
    for i in axes(mat, 1), j in axes(mat, 2)
        s = expr_string(mat[i, j])
        if !zero_string(s)
            out[component_key(i, j)] = s
        end
    end
    return out
end

function off_diagonal_components(mat)
    out = Dict{String,String}()
    for i in axes(mat, 1), j in axes(mat, 2)
        if i != j
            s = expr_string(mat[i, j])
            if !zero_string(s)
                out[component_key(i, j)] = s
            end
        end
    end
    return out
end

function matmul_check(metric, inverse_metric)
    product = Symbolics.simplify.(metric * inverse_metric, expand=true)
    return all(symbolic_equal(product[i, j], i == j ? Num(1) : Num(0)) for i in 1:4, j in 1:4)
end

function build_christoffel(metric, inverse_metric)
    gamma = Array{Num}(undef, 4, 4, 4)
    for lam in 1:4, mu in 1:4, nu in 1:4
        acc = zero_num()
        for sig in 1:4
            acc += inverse_metric[lam, sig] * (
                partial(metric[sig, nu], mu) +
                partial(metric[sig, mu], nu) -
                partial(metric[mu, nu], sig)
            )
        end
        gamma[lam, mu, nu] = simp(acc / 2)
    end
    return gamma
end

function build_ricci(gamma)
    ricci = Array{Num}(undef, 4, 4)
    for sigma in 1:4, nu in 1:4
        acc = zero_num()
        for rho in 1:4
            acc += partial(gamma[rho, nu, sigma], rho) - partial(gamma[rho, rho, sigma], nu)
            for lam in 1:4
                acc += gamma[rho, rho, lam] * gamma[lam, nu, sigma]
                acc -= gamma[rho, nu, lam] * gamma[lam, rho, sigma]
            end
        end
        ricci[sigma, nu] = simp(acc)
    end
    return ricci
end

function build_scalar_curvature(inverse_metric, ricci)
    acc = zero_num()
    for mu in 1:4, nu in 1:4
        acc += inverse_metric[mu, nu] * ricci[mu, nu]
    end
    return simp(acc)
end

function build_einstein(metric, inverse_metric)
    gamma = build_christoffel(metric, inverse_metric)
    ricci = build_ricci(gamma)
    scalar_curvature = build_scalar_curvature(inverse_metric, ricci)
    einstein = Array{Num}(undef, 4, 4)
    for mu in 1:4, nu in 1:4
        einstein[mu, nu] = simp(ricci[mu, nu] - metric[mu, nu] * scalar_curvature / 2)
    end
    return Dict(
        "gamma" => gamma,
        "ricci" => ricci,
        "scalar_curvature" => scalar_curvature,
        "einstein" => einstein,
    )
end

function standard_godel_metric()
    ex = exp(x)
    return Num[
        -1                 0      -Omega * ex                         0;
         0                 1       0                                  0;
        -Omega * ex        0       ex^2 * (1//2 - Omega^2)             0;
         0                 0       0                                  1
    ]
end

function standard_godel_inverse()
    ex = exp(x)
    return Num[
        -1 + 2 * Omega^2       0          -2 * Omega / ex         0;
         0                     1           0                       0;
        -2 * Omega / ex        0           2 / exp(2x)             0;
         0                     0           0                       1
    ]
end

function bianchi_rotating_metric()
    ex = exp(x)
    return Num[
        -1                   0       -ax * Omega * ex                         0;
         0                   ax^2     0                                        0;
        -ax * Omega * ex     0        ex^2 * ((1//2) * ay^2 - ax^2 * Omega^2)  0;
         0                   0        0                                        az^2
    ]
end

function bianchi_rotating_inverse()
    ex = exp(x)
    return Num[
        -1 + 2 * ax^2 * Omega^2 / ay^2       0          -2 * ax * Omega / (ay^2 * ex)      0;
         0                                   1 / ax^2    0                                  0;
        -2 * ax * Omega / (ay^2 * ex)        0           2 / (ay^2 * exp(2x))               0;
         0                                   0           0                                  1 / az^2
    ]
end

function entropy_conformal_metric()
    return exp(2phi) .* standard_godel_metric()
end

function entropy_conformal_inverse()
    return exp(-2phi) .* standard_godel_inverse()
end

function implied_stress_components(einstein)
    out = Dict{String,String}()
    for (k, v) in nonzero_matrix_components(einstein)
        out[k] = "(" * v * ")/(8*pi)"
    end
    return out
end

function variant_common(name, line_element, metric, inverse_metric, ctc_condition, source_classification, notes)
    geom = build_einstein(metric, inverse_metric)
    einstein = geom["einstein"]
    return Dict(
        "name" => name,
        "line_element" => line_element,
        "metric" => Dict(
            "g_mu_nu" => matrix_strings(metric),
            "g_inverse" => matrix_strings(inverse_metric),
            "inverse_check_g_times_ginv_identity" => matmul_check(metric, inverse_metric),
        ),
        "curvature" => Dict(
            "ricci_nonzero" => nonzero_matrix_components(geom["ricci"]),
            "ricci_scalar" => expr_string(geom["scalar_curvature"]),
            "einstein_nonzero" => nonzero_matrix_components(einstein),
            "einstein_symmetric" => all(symbolic_equal(einstein[i, j], einstein[j, i]) for i in 1:4, j in 1:4),
            "off_diagonal_einstein_nonzero" => off_diagonal_components(einstein),
        ),
        "implied_stress_energy" => Dict(
            "definition" => "T_mu_nu = G_mu_nu/(8*pi) unless a Lambda decomposition is stated separately",
            "nonzero_components" => implied_stress_components(einstein),
            "source_classification" => source_classification,
        ),
        "ctc_indicator" => ctc_condition,
        "notes" => notes,
    )
end

function variant1()
    metric = standard_godel_metric()
    inverse_metric = standard_godel_inverse()
    result = variant_common(
        "variant_1_lambda_driven_de_sitter_godel",
        "ds^2 = -(dt + Omega*exp(x)*dy)^2 + dx^2 + (1/2)*exp(2x)*dy^2 + dz^2",
        metric,
        inverse_metric,
        Dict(
            "g_yy" => "exp(2x)*(1/2 - Omega^2)",
            "closed_y_curve_timelike_when" => "Omega^2 > 1/2, assuming y is periodically identified and exp(2x)>0",
            "boundary" => "Omega^2 = 1/2",
        ),
        "perfect_fluid_plus_Lambda",
        Dict(
            "normalization_warning" => "The prompt metric keeps the 1/2*exp(2x) dy^2 coefficient fixed while inserting Omega only in the rotation one-form. Symbolics therefore finds a clean isotropic perfect-fluid-plus-Lambda source only at the normalized Godel point Omega^2 = 1; generic Omega in this exact fixed-coefficient family is anisotropic.",
        ),
    )
    result["perfect_fluid_plus_lambda_decomposition"] = Dict(
        "comoving_one_form_u_mu" => ["-1", "0", "-Omega*exp(x)", "0"],
        "equation" => "G_mu_nu + Lambda*g_mu_nu = 8*pi*((rho+p)*u_mu*u_nu + p*g_mu_nu)",
        "generic_coordinate_equations" => Dict(
            "8pi_rho_from_tt_ty" => "(3*Omega^2 - 2 - 2*Lambda)/2",
            "8pi_p_from_xx" => "Omega^2/2 + Lambda",
            "8pi_p_from_zz" => "1 - Omega^2/2 + Lambda",
            "isotropic_pressure_condition" => "Omega^2 = 1 for the exact prompt metric",
        ),
        "clean_godel_point" => Dict(
            "Omega_relation_prompt_normalization" => "Omega^2 = 1",
            "rho" => "1/(8*pi)",
            "p" => "0",
            "Lambda" => "-1/2",
            "lambda_rho_relation" => "Lambda = -4*pi*rho",
            "rotation_rho_relation" => "With the physical rotation convention omega^2 = Omega^2/2, omega^2 = 4*pi*rho; in the prompt's fixed-coefficient Omega convention, Omega^2 = 8*pi*rho at the clean point.",
        ),
    )
    result["compact_human_readout"] = Dict(
        "einstein_nonzero" => Dict(
            "G_tt" => "(3*Omega^2 - 2)/2",
            "G_xx" => "Omega^2/2",
            "G_ty" => "Omega*(3*Omega^2 - 2)*exp(x)/2",
            "G_yt" => "Omega*(3*Omega^2 - 2)*exp(x)/2",
            "G_yy" => "3*Omega^2*(2*Omega^2 - 1)*exp(2x)/4",
            "G_zz" => "1 - Omega^2/2",
        ),
        "note" => "Compact algebraic readout of the same nonzero component keys emitted by the Symbolics tensor computation.",
    )
    return result
end

function variant2()
    metric = bianchi_rotating_metric()
    inverse_metric = bianchi_rotating_inverse()
    result = variant_common(
        "variant_2_bianchi_rotating_anisotropy_feature",
        "ds^2 = -(dt + ax*Omega*exp(x)*dy)^2 + ax^2*dx^2 + ay^2*(1/2)*exp(2x)*dy^2 + az^2*dz^2, with ax,ay,az and derivatives represented as independent symbols",
        metric,
        inverse_metric,
        Dict(
            "g_yy" => "exp(2x)*(ay^2/2 - ax^2*Omega^2)",
            "closed_y_curve_timelike_when" => "ax^2*Omega^2 > ay^2/2, assuming real nonzero scale factors, periodic y, and exp(2x)>0",
            "boundary" => "ax^2*Omega^2 = ay^2/2",
        ),
        "anisotropic_shear_offdiagonal_required",
        Dict(
            "derivative_semantics" => "d/dt uses axd,ayd,azd and axdd,aydd,azdd as independent symbolic time-derivative symbols.",
            "classification_rule" => "A tetrad-diagonal anisotropic rotating fluid may carry t-y structure from the rotation one-form, but generic t-x or x-y Einstein components are off-diagonal shear/momentum requirements beyond diagonal direction-dependent pressure.",
        ),
    )
    offdiag = result["curvature"]["off_diagonal_einstein_nonzero"]
    non_ty = Dict(k => v for (k, v) in offdiag if !(k in ["ty", "yt"]))
    result["anisotropic_closure_test"] = Dict(
        "off_diagonal_components_beyond_rotation_ty" => non_ty,
        "consistent_diagonal_anisotropic_fluid_without_shear" => isempty(non_ty),
        "verdict" => isempty(non_ty) ? "consistent_anisotropic_fluid" : "anisotropic_shear_offdiagonal_required",
    )
    result["implied_stress_energy"]["source_classification"] = result["anisotropic_closure_test"]["verdict"]
    result["compact_human_readout"] = Dict(
        "nonzero_einstein_component_keys" => ["G_tt", "G_tx", "G_ty", "G_xt", "G_xx", "G_xy", "G_yt", "G_yx", "G_yy", "G_zz"],
        "decisive_offdiagonal_shear_components" => Dict(
            "G_tx=G_xt" => "(Omega^2*ax^3*ay*azd - Omega^2*ax^3*ayd*az + 2*Omega^2*ax^2*axd*ay*az - ax*ay^2*ayd*az + axd*ay^3*az)/(ax*ay^3*az)",
            "G_xy=G_yx" => "Omega*ax*(2*Omega^2*ax^2*ay*azd - 2*Omega^2*ax^2*ayd*az + 4*Omega^2*ax*axd*ay*az - ay^3*azd - ay^2*ayd*az)*exp(x)/(2*ay^3*az)",
        ),
        "note" => "Full raw Symbolics expressions for all nonzero G_mu_nu components are in curvature.einstein_nonzero. The displayed t-x and x-y terms are enough to falsify a purely diagonal anisotropic pressure closure generically.",
    )
    return result
end

function variant3()
    metric = entropy_conformal_metric()
    inverse_metric = entropy_conformal_inverse()
    result = variant_common(
        "variant_3_entropy_conformal",
        "ds^2 = exp(2*phi(t)) * (-(dt + Omega*exp(x)*dy)^2 + dx^2 + (1/2)*exp(2x)*dy^2 + dz^2), with phi,phid,phidd represented as independent symbols",
        metric,
        inverse_metric,
        Dict(
            "g_yy" => "exp(2*phi)*exp(2x)*(1/2 - Omega^2)",
            "closed_y_curve_timelike_when" => "Omega^2 > 1/2 for finite real phi, assuming periodic y; the positive conformal factor preserves the sign of g_yy",
            "boundary" => "Omega^2 = 1/2",
            "conformal_causal_note" => "Strictly positive conformal rescaling preserves null cones and the timelike/spacelike sign of y-direction loops.",
        ),
        "scalar_field_sourced",
        Dict(
            "derivative_semantics" => "d/dt uses phid and phidd as independent symbolic time-derivative symbols.",
            "source_note" => "The phi-gradient and phi-acceleration terms give an effective scalar/entropy stress contribution on top of the stationary Godel tensor; no scalar equation of motion is asserted.",
        ),
    )
    result["compact_human_readout"] = Dict(
        "einstein_nonzero" => Dict(
            "G_tt" => "-(4*Omega^2*phid^2 + 8*Omega^2*phidd - 3*Omega^2 - 6*phid^2 + 2)/2",
            "G_tx" => "2*Omega^2*phid",
            "G_xt" => "2*Omega^2*phid",
            "G_ty" => "-Omega*(4*Omega^2*phid^2 + 8*Omega^2*phidd - 3*Omega^2 - 2*phid^2 - 4*phidd + 2)*exp(x)/2",
            "G_yt" => "-Omega*(4*Omega^2*phid^2 + 8*Omega^2*phidd - 3*Omega^2 - 2*phid^2 - 4*phidd + 2)*exp(x)/2",
            "G_xx" => "(4*Omega^2*phid^2 + 8*Omega^2*phidd + Omega^2 - 2*phid^2 - 4*phidd)/2",
            "G_xy" => "Omega*phid*(2*Omega^2 - 1)*exp(x)",
            "G_yx" => "Omega*phid*(2*Omega^2 - 1)*exp(x)",
            "G_yy" => "-(2*Omega^2 - 1)*(4*Omega^2*phid^2 + 8*Omega^2*phidd - 3*Omega^2 - 2*phid^2 - 4*phidd)*exp(2x)/4",
            "G_zz" => "(4*Omega^2*phid^2 + 8*Omega^2*phidd - Omega^2 - 2*phid^2 - 4*phidd + 2)/2",
        ),
        "note" => "Compact algebraic readout of the same nonzero component keys emitted by the Symbolics tensor computation.",
    )
    return result
end

function build_result()
    println("progress: variant1 start"); flush(stdout)
    v1 = variant1()
    println("progress: variant1 done"); flush(stdout)
    println("progress: variant2 start"); flush(stdout)
    v2 = variant2()
    println("progress: variant2 done"); flush(stdout)
    println("progress: variant3 start"); flush(stdout)
    v3 = variant3()
    println("progress: variant3 done"); flush(stdout)
    variants = [v1, v2, v3]
    cleanest = Dict(
        "winner" => "variant_1_lambda_driven_de_sitter_godel",
        "reason" => "It is the only ansatz that closes as a dust perfect-fluid plus Lambda source at a simple normalized Godel point. Variant 2 generically needs off-diagonal shear/momentum terms beyond diagonal anisotropic pressures, and Variant 3 introduces scalar/entropy derivative stress terms while preserving the CTC sign threshold.",
        "claim_scope" => CLAIM_CEILING,
    )
    result = Dict(
        "schema_version" => "formal_scout_symbolic_gr_godel_variants_v1",
        "task" => "godel_variants_exploration",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => CLAIM_CEILING,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "all_pass" => false,
        "diagnostic_ran" => true,
        "julia" => Dict(
            "ran" => true,
            "source_path" => SOURCE_PATH,
            "result_path" => RESULT_PATH,
            "project" => Base.active_project(),
            "packages_used" => ["Symbolics", "JSON3", "Dates"],
            "aligned_packages_load_bearing" => ["Symbolics"],
            "reads_peer_result" => false,
        ),
        "TOOL_MANIFEST" => Dict(
            "Symbolics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing symbolic metric inverse checks, Christoffel/Ricci/scalar curvature, Einstein tensor, and CTC sign expressions"),
            "JSON3" => Dict("tried" => true, "used" => true, "reason" => "supportive result JSON serialization"),
            "Dates" => Dict("tried" => true, "used" => true, "reason" => "supportive generated_at timestamp"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Symbolics" => "load_bearing",
            "JSON3" => "supportive",
            "Dates" => "supportive",
        ),
        "coordinates" => COORD_NAMES,
        "symbol_semantics" => Dict(
            "Omega" => "constant rotation parameter in the prompt metric",
            "ax_ay_az" => "Bianchi scale-factor symbols standing for ax(t), ay(t), az(t)",
            "axd_ayd_azd" => "first time derivatives represented as independent symbols",
            "axdd_aydd_azdd" => "second time derivatives represented as independent symbols",
            "phi_phid_phidd" => "entropy-conformal field and first/second time derivatives represented as independent symbols",
        ),
        "variants" => Dict(v["name"] => v for v in variants),
        "cleanest_source" => cleanest,
        "fences" => Dict(
            "classification_is_scratch_diagnostic" => CLASSIFICATION == "scratch_diagnostic",
            "promotion_allowed_false" => PROMOTION_ALLOWED == false,
            "formal_admission_allowed_false" => FORMAL_ADMISSION_ALLOWED == false,
            "not_physics_result" => true,
            "not_canonical" => true,
            "not_derived_solution" => true,
        ),
        "divergence_log" => [
            "This is a symbolic GR math diagnostic, not a physics admission.",
            "CTC checks use the local sign of g_yy for periodic y loops; global periodic identification is not proven here.",
            "Variant 1 uses the exact prompt metric. Its generic Omega family is not a standard rescaled Godel family unless the fixed spatial coefficient is normalized consistently.",
        ],
    )
    result["all_pass"] = (
        result["diagnostic_ran"] == true &&
        all(v["metric"]["inverse_check_g_times_ginv_identity"] == true for v in variants) &&
        all(v["curvature"]["einstein_symmetric"] == true for v in variants) &&
        result["fences"]["classification_is_scratch_diagnostic"] == true &&
        result["fences"]["promotion_allowed_false"] == true &&
        result["fences"]["formal_admission_allowed_false"] == true
    )
    return result
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON3.pretty(io, result)
        write(io, "\n")
    end
    summaries = [
        "$(v["name"]):$(v["implied_stress_energy"]["source_classification"]):$(v["ctc_indicator"]["closed_y_curve_timelike_when"])"
        for v in values(result["variants"])
    ]
    println("GODEL_VARIANTS_DONE all_pass=$(result["all_pass"]) cleanest=$(result["cleanest_source"]["winner"]) result_path=$(RESULT_PATH)")
    println(join(summaries, "\n"))
end

main()
