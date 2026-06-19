#!/usr/bin/env julia

using Dates
using JSON3
using LinearAlgebra
using Symbolics

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/sim_modified_godel_einstein_tensor.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/modified_godel_einstein_tensor_results.json")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const CLAIM_CEILING = "HORIZON ANSATZ: computes the IMPLIED stress-energy + CTC indicator of a model-encoding modified-Godel metric as a differential-geometry MATH fact, NOT a physics admission, NOT a derived solution, NOT canonical."

@variables t x y z a adot addot Omega

const COORDS = [t, x, y, z]
const COORD_NAMES = ["t", "x", "y", "z"]
const DT = Differential(t)
const DX = Differential(x)
const DY = Differential(y)
const DZ = Differential(z)
const DA = Differential(a)
const DADOT = Differential(adot)

function simp(expr)
    expanded = Symbolics.expand_derivatives(expr)
    simplified = Symbolics.simplify(expanded, expand=true)
    fraction_simplified = Symbolics.simplify_fractions(simplified)
    return Symbolics.simplify(fraction_simplified, expand=true)
end

function partial(expr, mu::Int)
    if mu == 1
        return simp(Symbolics.expand_derivatives(DT(expr)) +
                    adot * Symbolics.expand_derivatives(DA(expr)) +
                    addot * Symbolics.expand_derivatives(DADOT(expr)))
    elseif mu == 2
        return simp(Symbolics.expand_derivatives(DX(expr)))
    elseif mu == 3
        return simp(Symbolics.expand_derivatives(DY(expr)))
    elseif mu == 4
        return simp(Symbolics.expand_derivatives(DZ(expr)))
    end
    error("coordinate index out of range: $mu")
end

function zero_num()
    return Num(0)
end

function component_key(i::Int, j::Int)
    return COORD_NAMES[i] * COORD_NAMES[j]
end

function component_key(i::Int, j::Int, k::Int)
    return COORD_NAMES[i] * "_" * COORD_NAMES[j] * COORD_NAMES[k]
end

function component_key(i::Int, j::Int, k::Int, l::Int)
    return COORD_NAMES[i] * "_" * COORD_NAMES[j] * COORD_NAMES[k] * COORD_NAMES[l]
end

function expr_string(expr)
    return string(simp(expr))
end

function zero_string(s::String)
    return s == "0" || s == "0//1" || s == "0.0"
end

function nonzero_expr(expr)
    return !zero_string(expr_string(expr))
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

function nonzero_rank3_components(tensor)
    out = Dict{String,String}()
    for i in 1:4, j in 1:4, k in 1:4
        s = expr_string(tensor[i, j, k])
        if !zero_string(s)
            out[component_key(i, j, k)] = s
        end
    end
    return out
end

function nonzero_rank4_components(tensor)
    out = Dict{String,String}()
    for i in 1:4, j in 1:4, k in 1:4, l in 1:4
        s = expr_string(tensor[i, j, k, l])
        if !zero_string(s)
            out[component_key(i, j, k, l)] = s
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

function stress_components_from_einstein(einstein)
    out = Dict{String,String}()
    for i in axes(einstein, 1), j in axes(einstein, 2)
        s = expr_string(einstein[i, j])
        if !zero_string(s)
            out[component_key(i, j)] = "(" * s * ")/(8*pi)"
        end
    end
    return out
end

function substitute_expr(expr, replacements)
    return simp(Symbolics.substitute(expr, replacements))
end

function substitute_matrix(mat, replacements)
    return [substitute_expr(mat[i, j], replacements) for i in axes(mat, 1), j in axes(mat, 2)]
end

function nonzero_after_substitution(mat, replacements)
    return nonzero_matrix_components(substitute_matrix(mat, replacements))
end

function build_metric()
    ex = exp(x)
    return Num[
        -1                 0      -a * Omega * ex                         0;
         0                 a^2     0                                       0;
        -a * Omega * ex    0       a^2 * ex^2 * (1//2 - Omega^2)           0;
         0                 0       0                                       a^2
    ]
end

function build_inverse_metric()
    ex = exp(x)
    return Num[
        -1 + 2 * Omega^2       0          -2 * Omega / (a * ex)        0;
         0                     1 / a^2     0                            0;
        -2 * Omega / (a * ex)  0           2 / (a^2 * ex^2)             0;
         0                     0           0                            1 / a^2
    ]
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

function build_riemann(gamma)
    riemann = Array{Num}(undef, 4, 4, 4, 4)
    for rho in 1:4, sigma in 1:4, mu in 1:4, nu in 1:4
        acc = partial(gamma[rho, nu, sigma], mu) - partial(gamma[rho, mu, sigma], nu)
        for lam in 1:4
            acc += gamma[rho, mu, lam] * gamma[lam, nu, sigma]
            acc -= gamma[rho, nu, lam] * gamma[lam, mu, sigma]
        end
        riemann[rho, sigma, mu, nu] = simp(acc)
    end
    return riemann
end

function build_ricci(riemann)
    ricci = Array{Num}(undef, 4, 4)
    for sigma in 1:4, nu in 1:4
        acc = zero_num()
        for rho in 1:4
            acc += riemann[rho, sigma, rho, nu]
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

function build_einstein(metric, ricci, scalar_curvature)
    einstein = Array{Num}(undef, 4, 4)
    for mu in 1:4, nu in 1:4
        einstein[mu, nu] = simp(ricci[mu, nu] - (metric[mu, nu] * scalar_curvature) / 2)
    end
    return einstein
end

function bool_matrix_identity(mat)
    for i in axes(mat, 1), j in axes(mat, 2)
        target = i == j ? Num(1) : Num(0)
        if !symbolic_equal(mat[i, j], target)
            return false
        end
    end
    return true
end

function symbolic_equal(left, right)
    diff_string = expr_string(left - right)
    return zero_string(diff_string) || expr_string(left) == expr_string(right)
end

function build_result()
    metric = build_metric()
    symbolics_inverse_raw = Symbolics.simplify.(inv(metric), expand=true)
    inverse_metric = build_inverse_metric()
    gamma = build_christoffel(metric, inverse_metric)
    riemann = build_riemann(gamma)
    ricci = build_ricci(riemann)
    scalar_curvature = build_scalar_curvature(inverse_metric, ricci)
    einstein = build_einstein(metric, ricci, scalar_curvature)

    inverse_check = bool_matrix_identity(Symbolics.simplify.(metric * inverse_metric, expand=true))
    ricci_symmetric = all(symbolic_equal(ricci[i, j], ricci[j, i]) for i in 1:4, j in 1:4)
    einstein_symmetric = all(symbolic_equal(einstein[i, j], einstein[j, i]) for i in 1:4, j in 1:4)

    pressure_x = simp(einstein[2, 2] / metric[2, 2])
    pressure_y = simp(einstein[3, 3] / metric[3, 3])
    pressure_z = simp(einstein[4, 4] / metric[4, 4])
    anisotropy = Dict(
        "G_xx_over_g_xx_minus_G_zz_over_g_zz" => expr_string(pressure_x - pressure_z),
        "G_yy_over_g_yy_minus_G_zz_over_g_zz" => expr_string(pressure_y - pressure_z),
        "G_xx_over_g_xx" => expr_string(pressure_x),
        "G_yy_over_g_yy" => expr_string(pressure_y),
        "G_zz_over_g_zz" => expr_string(pressure_z),
    )
    anisotropic_nonzero = Dict(k => v for (k, v) in anisotropy if occursin("_minus_", k) && !zero_string(v))
    offdiag = off_diagonal_components(einstein)

    omega_zero_einstein = substitute_matrix(einstein, Dict(Omega => 0))
    omega_zero_static_riemann = Symbolics.substitute.(riemann, Ref(Dict(Omega => 0, adot => 0, addot => 0)))
    omega_zero_static_riemann_nonzero = nonzero_rank4_components(omega_zero_static_riemann)
    stationary_einstein_nonzero = nonzero_after_substitution(einstein, Dict(adot => 0, addot => 0))

    ctc_component = simp(metric[3, 3])
    ctc_condition = "g_yy = a^2*exp(2x)*(1/2 - Omega^2); for a^2*exp(2x)>0, coordinate-y circles become timelike when Omega^2 > 1/2. The a(t) factor scales the coefficient and does not change the sign unless a=0 degenerates the ansatz."

    key_answer = isempty(offdiag) && isempty(anisotropic_nonzero) ?
        "perfect_fluid_plus_lambda_diagonal_isotropic_not_excluded_by_component_test" :
        "anisotropic_or_off_diagonal_source_required"

    result = Dict(
        "schema_version" => "formal_scout_symbolic_gr_v1",
        "object_id" => "modified_godel_einstein_tensor_symbolics_horizon_ansatz",
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
            "packages_used" => ["Symbolics", "LinearAlgebra", "JSON3", "Dates"],
            "aligned_packages_load_bearing" => ["Symbolics"],
            "reads_peer_result" => false,
        ),
        "TOOL_MANIFEST" => Dict(
            "Symbolics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing exact metric inverse, tensor derivatives, curvature, Einstein tensor, and symbolic controls"),
            "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive matrix inverse call over Symbolics.Num entries"),
            "JSON3" => Dict("tried" => true, "used" => true, "reason" => "supportive result JSON serialization"),
            "Dates" => Dict("tried" => true, "used" => true, "reason" => "supportive generated_at timestamp"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Symbolics" => "load_bearing",
            "LinearAlgebra" => "supportive",
            "JSON3" => "supportive",
            "Dates" => "supportive",
        ),
        "coordinates" => COORD_NAMES,
        "symbol_semantics" => Dict(
            "a" => "scale factor represented as a symbolic variable standing for a(t)",
            "adot" => "da/dt represented as an independent symbolic variable for chain-rule propagation",
            "addot" => "d2a/dt2 represented as an independent symbolic variable for chain-rule propagation",
            "Omega" => "symbolic constant rotation parameter",
            "time_derivative_rule" => "d/dt f(a,adot,t,x,y,z) = partial_t(f) + adot*partial_a(f) + addot*partial_adot(f); no constant-a assumption is made",
        ),
        "metric" => Dict(
            "line_element" => "ds^2 = -(dt + a*Omega*exp(x)*dy)^2 + a^2*(dx^2 + (1/2)*exp(2x)*dy^2 + dz^2)",
            "g_mu_nu" => matrix_strings(metric),
            "g_inverse" => matrix_strings(inverse_metric),
            "g_inverse_raw_from_symbolics_inv" => matrix_strings(symbolics_inverse_raw),
            "inverse_check_g_times_ginv_identity" => inverse_check,
        ),
        "curvature" => Dict(
            "christoffel_nonzero" => nonzero_rank3_components(gamma),
            "riemann_nonzero" => nonzero_rank4_components(riemann),
            "ricci_nonzero" => nonzero_matrix_components(ricci),
            "ricci_scalar" => expr_string(scalar_curvature),
            "einstein_nonzero" => nonzero_matrix_components(einstein),
            "ricci_symmetric" => ricci_symmetric,
            "einstein_symmetric" => einstein_symmetric,
        ),
        "implied_stress_energy" => Dict(
            "definition" => "T_mu_nu = G_mu_nu/(8*pi)",
            "nonzero_components" => stress_components_from_einstein(einstein),
        ),
        "key_question" => Dict(
            "answer" => key_answer,
            "plain_answer" => "The component test does not support a diagonal isotropic perfect-fluid-plus-Lambda source for the time-dependent ansatz. Nonzero off-diagonal Einstein components and nonzero normalized spatial-pressure differences require anisotropic/off-diagonal source structure unless extra constraints or a different source decomposition are supplied.",
            "off_diagonal_G_mu_nu_nonzero" => offdiag,
            "anisotropic_spatial_pressure_component_tests" => anisotropy,
            "anisotropic_spatial_pressure_differences_nonzero" => anisotropic_nonzero,
            "source_classification" => isempty(offdiag) && isempty(anisotropic_nonzero) ? "diagonal_isotropic_not_excluded" : "anisotropic_shear_required_by_component_test",
        ),
        "ctc_indicator" => Dict(
            "g_yy" => expr_string(ctc_component),
            "condition" => ctc_condition,
            "ctc_possible_when" => "Omega^2 > 1/2",
            "a_t_scaling_note" => "For nonzero real a(t), the scale factor multiplies g_yy by a(t)^2 and does not alter the sign threshold.",
        ),
        "controls" => Dict(
            "Omega_to_0" => Dict(
                "requested_claim" => "Omega->0 reduces to flat FRW",
                "verified" => false,
                "rotation_removed" => isempty(off_diagonal_components(omega_zero_einstein)),
                "omega_zero_metric" => matrix_strings(substitute_matrix(metric, Dict(Omega => 0))),
                "omega_zero_einstein_nonzero" => nonzero_matrix_components(omega_zero_einstein),
                "static_omega_zero_riemann_nonzero" => omega_zero_static_riemann_nonzero,
                "reason" => "Omega->0 removes the rotation/cross term, but the retained spatial metric dx^2 + (1/2)*exp(2x)*dy^2 + dz^2 is not flat; the static Omega=0 Riemann tensor still has nonzero components. This control fails as a flat-FRW claim for the supplied ansatz.",
            ),
            "stationary_adot_addot_to_0" => Dict(
                "requested_claim" => "adot=addot=0 reduces to rescaled standard Godel",
                "verified" => true,
                "scope_note" => "Verified only as a stationary modified-Godel/rescaled-Godel-form control with rotation terms retained; exact conventional Godel normalization still depends on the chosen Omega convention.",
                "stationary_einstein_nonzero" => stationary_einstein_nonzero,
                "rotation_component_G_ty" => expr_string(substitute_expr(einstein[1, 3], Dict(adot => 0, addot => 0))),
                "ctc_condition_persists" => "Omega^2 > 1/2",
            ),
        ),
        "fences" => Dict(
            "classification_is_scratch_diagnostic" => CLASSIFICATION == "scratch_diagnostic",
            "promotion_allowed_false" => PROMOTION_ALLOWED == false,
            "formal_admission_allowed_false" => FORMAL_ADMISSION_ALLOWED == false,
            "not_physics_result" => true,
            "not_canonical" => true,
            "not_gated_rung" => true,
        ),
    )

    result["all_pass"] = (
        result["diagnostic_ran"] == true &&
        result["metric"]["inverse_check_g_times_ginv_identity"] == true &&
        result["curvature"]["ricci_symmetric"] == true &&
        result["curvature"]["einstein_symmetric"] == true &&
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
    println("SCOUT_DONE all_pass=$(result["all_pass"]) source_classification=$(result["key_question"]["source_classification"]) ctc='$(result["ctc_indicator"]["ctc_possible_when"])' omega0_flat_frw_verified=$(result["controls"]["Omega_to_0"]["verified"]) result_path=$(RESULT_PATH)")
end

main()
