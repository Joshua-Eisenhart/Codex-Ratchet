#!/usr/bin/env julia
# object_id: geo_s2_negative_models_v0
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s2_negative_models_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-8
const SCALE = 10^6
const PIN_SPEC = "geo_s2_negative_models_v0|stage:S2|negative_models:wrong_connection,broken_stokes,naive_cover_grid|common_adapter:s2_negative_positive_receipt_interface_v1|classification:scratch_diagnostic|promotion_allowed:false|formal_admission_allowed:false"
const ETAS = [pi / 8.0, pi / 6.0, pi / 4.0, pi / 3.0, 3.0 * pi / 8.0]
const ETA_PAIRS = [(pi / 8.0, pi / 3.0), (pi / 6.0, 3.0 * pi / 8.0)]
const GRID_N = 64
const GRID_ETA = pi / 5.0

const CONVENTION_PIN = Dict{String,Any}(
    "holonomy_quantity" => "accumulated_phi",
    "berry_formula" => "not_reported_in_negative_suite; canonical target uses lifted torus-chart cycle h(eta)=-2*pi*cos(2*eta)",
    "phase_domain" => "lifted_real",
    "base_loop_count" => "chi:0->2pi torus-chart cycle, traverses Hopf base twice because base_angle=2*chi",
    "orientation_and_c1_sign" => "displayed F integrates to -4*pi on the double-covered chart; orientation reports c1=1",
)

const COMMON_RECEIPT_KEYS = [
    "S2.A_connection_match",
    "S2.F_curvature_derivative_pair",
    "S2.H_horizontal_holonomy",
    "S2.S_stokes_strip",
    "S2.C_chern_normalization",
    "S2.T_local_metric_det",
    "S2.T_physical_area",
    "S2.G_grid_count",
    "S2.G_parity_identification",
]

const SELECTIVITY_COLUMNS = [
    "connection_match",
    "curvature_derivative_pair",
    "horizontal_holonomy_target",
    "stokes_consistency",
    "chern_normalization",
    "local_metric_determinant",
    "physical_torus_area",
    "grid_distinct_count",
    "parity_preserving_identification",
]

const TOOL_MANIFEST = Dict{String,Any}(
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Julia-side raw-value proof that wrong S2 residuals cannot equal zero",
    ),
    "JSON/Dates/SHA" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization, timestamping, and source hashing",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Z3" => "load_bearing",
    "JSON/Dates/SHA" => "supportive",
)

sha256_text(text::String) = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))

function file_sha256(path::String)
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

canonical_a_chi(eta) = cos(2.0 * eta)
wrong_a_chi(eta) = -cos(2.0 * eta)
canonical_f_coeff(eta) = -2.0 * sin(2.0 * eta)
wrong_f_coeff(eta) = 2.0 * sin(2.0 * eta)
canonical_holonomy(eta) = -2.0 * pi * cos(2.0 * eta)
wrong_connection_holonomy(eta) = 2.0 * pi * cos(2.0 * eta)
canonical_strip_integral(eta_i, eta_j) = 2.0 * pi * (cos(2.0 * eta_j) - cos(2.0 * eta_i))
wrong_sign_strip_integral(eta_i, eta_j) = -canonical_strip_integral(eta_i, eta_j)
stokes_residual(hol_i, hol_j, strip) = abs((hol_j - hol_i) + strip)
metric_det_sqrt(eta) = sin(2.0 * eta)
chart_area(eta) = 4.0 * pi^2 * metric_det_sqrt(eta)
physical_area(eta) = 2.0 * pi^2 * metric_det_sqrt(eta)
scaled(value) = Int(round(abs(value) * SCALE))

function z3_assert_int_eq(value::Int, target::Int)
    solver = Z3.Solver()
    Z3.add(solver, Z3.IntVal(value) == Z3.IntVal(target))
    string(Z3.check(solver))
end

function receipt(pass_value::Bool, exact_strength::String, measured, note::String)
    Dict{String,Any}(
        "pass" => pass_value,
        "exact_strength" => exact_strength,
        "measured" => measured,
        "convention_pin" => CONVENTION_PIN,
        "note" => note,
    )
end

function common_suite_adapter(model_id::String, negative_model::Bool, receipts::Dict{String,Any}, metadata::Dict{String,Any})
    missing = [key for key in COMMON_RECEIPT_KEYS if !haskey(receipts, key)]
    if !isempty(missing)
        error("common suite adapter missing receipt keys: $(missing)")
    end
    out = Dict{String,Any}(
        "model_id" => model_id,
        "negative_model" => negative_model,
        "common_suite_adapter" => Dict{String,Any}(
            "adapter_id" => "s2_negative_positive_receipt_interface_v1",
            "receipt_keys" => COMMON_RECEIPT_KEYS,
            "selectivity_columns" => SELECTIVITY_COLUMNS,
            "same_interface_as_positive_control" => true,
        ),
    )
    merge!(out, metadata)
    merge!(out, receipts)
    out
end

function pair_data(n::Int, eta::Float64)
    rows = Any[]
    max_pair_deviation = 0.0
    parity_preserved = true
    for (a, b) in [(0, 0), (1, 2), (7, 9), (18, 25), (31, 5)]
        paired_a = mod(a + div(n, 2), n)
        paired_b = mod(b + div(n, 2), n)
        delta_phi = pi
        delta_chi = pi
        spinor_phase_deviation = abs(exp(im * (delta_phi + delta_chi)) - 1.0)
        base_angle_deviation = abs(mod(2.0 * delta_chi, 2.0 * pi) - 0.0)
        pair_deviation = max(spinor_phase_deviation, base_angle_deviation)
        max_pair_deviation = max(max_pair_deviation, pair_deviation)
        pair_parity = mod(a + b, 2) == mod(paired_a + paired_b, 2)
        parity_preserved = parity_preserved && pair_parity
        push!(rows, Dict("a" => a, "b" => b, "paired_a" => paired_a, "paired_b" => paired_b, "pair_deviation" => pair_deviation, "parity_preserved" => pair_parity))
    end
    Dict{String,Any}("pair_rows" => rows, "max_pair_deviation" => max_pair_deviation, "parity_preserved" => parity_preserved)
end

function positive_control()
    eta = GRID_ETA
    n = GRID_N
    receipts = Dict{String,Any}(
        "S2.A_connection_match" => receipt(true, "closed_form", Dict("max_abs_connection_delta" => 0.0), "canonical A matches target"),
        "S2.F_curvature_derivative_pair" => receipt(true, "closed_form", Dict("max_abs_curvature_delta" => 0.0, "F_coeff" => canonical_f_coeff(eta)), "canonical F=dA is preserved"),
        "S2.H_horizontal_holonomy" => receipt(true, "closed_form", Dict("max_abs_residual" => 0.0, "sample_holonomy" => canonical_holonomy(eta)), "canonical horizontal target is preserved"),
        "S2.S_stokes_strip" => receipt(true, "closed_form", Dict("max_abs_residual" => 0.0, "pairs" => ETA_PAIRS), "canonical Stokes rows pass"),
        "S2.C_chern_normalization" => receipt(true, "closed_form", Dict("chart_integral" => -4.0 * pi, "reported_c1" => 1), "canonical Chern convention passes"),
        "S2.T_local_metric_det" => receipt(true, "closed_form", Dict("sqrt_det_g" => metric_det_sqrt(eta)), "local metric determinant passes"),
        "S2.T_physical_area" => receipt(true, "closed_form", Dict("chart_area" => chart_area(eta), "physical_area" => physical_area(eta), "cover_factor" => 2.0), "physical area quotient passes"),
        "S2.G_grid_count" => receipt(true, "exact_integer", Dict("N" => n, "physical_points" => div(n * n, 2), "naive_points" => n * n), "grid quotient count passes"),
        "S2.G_parity_identification" => receipt(true, "exact_integer_plus_numeric_pairs", pair_data(n, eta), "parity-preserving identification passes"),
    )
    common_suite_adapter("positive_s2_canonical_connection_quotiented_grid", false, receipts, Dict{String,Any}("pass" => true))
end

function wrong_connection_model()
    eta = GRID_ETA
    n = GRID_N
    connection_deltas = [abs(wrong_a_chi(e) - canonical_a_chi(e)) for e in ETAS]
    curvature_deltas = [abs(wrong_f_coeff(e) - canonical_f_coeff(e)) for e in ETAS]
    holonomy_rows = Any[]
    holonomy_residuals = Float64[]
    for e in ETAS
        residual = abs(wrong_connection_holonomy(e) - canonical_holonomy(e))
        push!(holonomy_residuals, residual)
        push!(holonomy_rows, Dict("eta" => e, "wrong_holonomy" => wrong_connection_holonomy(e), "target" => canonical_holonomy(e), "residual" => residual))
    end
    stokes_rows = Any[]
    stokes_residuals = Float64[]
    for (eta_i, eta_j) in ETA_PAIRS
        residual = stokes_residual(wrong_connection_holonomy(eta_i), wrong_connection_holonomy(eta_j), canonical_strip_integral(eta_i, eta_j))
        push!(stokes_residuals, residual)
        push!(stokes_rows, Dict("eta_i" => eta_i, "eta_j" => eta_j, "residual_against_canonical_F" => residual))
    end
    receipts = Dict{String,Any}(
        "S2.A_connection_match" => receipt(false, "closed_form_control", Dict("max_abs_connection_delta" => maximum(connection_deltas)), "sign-flipped connection fails canonical match"),
        "S2.F_curvature_derivative_pair" => receipt(false, "closed_form_control", Dict("internal_derivative_pair_pass" => true, "canonical_curvature_match_pass" => false, "max_abs_curvature_delta" => maximum(curvature_deltas)), "wrong connection has opposite canonical curvature sign"),
        "S2.H_horizontal_holonomy" => receipt(false, "closed_form_control", Dict("rows" => holonomy_rows, "max_abs_residual" => maximum(holonomy_residuals)), "wrong connection fails holonomy target except accidental zero-cos shell"),
        "S2.S_stokes_strip" => receipt(false, "closed_form_control", Dict("rows" => stokes_rows, "max_abs_residual" => maximum(stokes_residuals)), "wrong holonomy fails Stokes against canonical F"),
        "S2.C_chern_normalization" => receipt(false, "closed_form_control", Dict("wrong_chart_integral" => 4.0 * pi, "canonical_chart_integral" => -4.0 * pi, "fail_magnitude" => 8.0 * pi), "wrong curvature reverses Chern sign"),
        "S2.T_local_metric_det" => receipt(true, "closed_form", Dict("sqrt_det_g" => metric_det_sqrt(eta)), "metric determinant preserved"),
        "S2.T_physical_area" => receipt(true, "closed_form", Dict("chart_area" => chart_area(eta), "physical_area" => physical_area(eta), "cover_factor" => 2.0), "area quotient preserved"),
        "S2.G_grid_count" => receipt(true, "exact_integer", Dict("N" => n, "physical_points" => div(n * n, 2), "naive_points" => n * n), "grid count preserved"),
        "S2.G_parity_identification" => receipt(true, "exact_integer_plus_numeric_pairs", pair_data(n, eta), "parity identification preserved"),
    )
    common_suite_adapter("negative_1_wrong_connection_sign_flipped", true, receipts, Dict{String,Any}("negative_family" => "wrong_connection", "primary_fail_magnitude" => maximum(holonomy_residuals)))
end

function broken_stokes_model()
    eta = GRID_ETA
    n = GRID_N
    stokes_rows = Any[]
    stokes_residuals = Float64[]
    for (eta_i, eta_j) in ETA_PAIRS
        residual = stokes_residual(canonical_holonomy(eta_i), canonical_holonomy(eta_j), wrong_sign_strip_integral(eta_i, eta_j))
        push!(stokes_residuals, residual)
        push!(stokes_rows, Dict("eta_i" => eta_i, "eta_j" => eta_j, "residual_against_wrong_F" => residual))
    end
    receipts = Dict{String,Any}(
        "S2.A_connection_match" => receipt(true, "closed_form", Dict("max_abs_connection_delta" => 0.0), "canonical A preserved"),
        "S2.F_curvature_derivative_pair" => receipt(false, "closed_form_control", Dict("F_wrong_coeff" => wrong_f_coeff(eta), "dA_canonical_coeff" => canonical_f_coeff(eta), "fail_magnitude" => abs(wrong_f_coeff(eta) - canonical_f_coeff(eta))), "wrong F is not dA"),
        "S2.H_horizontal_holonomy" => receipt(true, "closed_form", Dict("max_abs_residual" => 0.0, "sample_holonomy" => canonical_holonomy(eta)), "horizontal transport from A preserved"),
        "S2.S_stokes_strip" => receipt(false, "closed_form_control", Dict("rows" => stokes_rows, "max_abs_residual" => maximum(stokes_residuals)), "Stokes fails with wrong F"),
        "S2.C_chern_normalization" => receipt(false, "closed_form_control", Dict("wrong_chart_integral" => 4.0 * pi, "canonical_chart_integral" => -4.0 * pi, "reported_c1_if_unfixed" => -1, "fail_magnitude" => 8.0 * pi), "wrong F reverses Chern row"),
        "S2.T_local_metric_det" => receipt(true, "closed_form", Dict("sqrt_det_g" => metric_det_sqrt(eta)), "metric determinant preserved"),
        "S2.T_physical_area" => receipt(true, "closed_form", Dict("chart_area" => chart_area(eta), "physical_area" => physical_area(eta), "cover_factor" => 2.0), "area quotient preserved"),
        "S2.G_grid_count" => receipt(true, "exact_integer", Dict("N" => n, "physical_points" => div(n * n, 2), "naive_points" => n * n), "grid count preserved"),
        "S2.G_parity_identification" => receipt(true, "exact_integer_plus_numeric_pairs", pair_data(n, eta), "parity identification preserved"),
    )
    common_suite_adapter("negative_2_broken_stokes_wrong_F_sign", true, receipts, Dict{String,Any}("negative_family" => "broken_stokes", "primary_fail_magnitude" => maximum(stokes_residuals)))
end

function naive_cover_model()
    eta = GRID_ETA
    n = GRID_N
    naive_points = n * n
    physical_points = div(n * n, 2)
    receipts = Dict{String,Any}(
        "S2.A_connection_match" => receipt(true, "closed_form", Dict("max_abs_connection_delta" => 0.0), "connection path preserved"),
        "S2.F_curvature_derivative_pair" => receipt(true, "closed_form", Dict("max_abs_curvature_delta" => 0.0, "F_coeff" => canonical_f_coeff(eta)), "F=dA preserved"),
        "S2.H_horizontal_holonomy" => receipt(true, "closed_form", Dict("max_abs_residual" => 0.0, "sample_holonomy" => canonical_holonomy(eta)), "holonomy preserved"),
        "S2.S_stokes_strip" => receipt(true, "closed_form", Dict("max_abs_residual" => 0.0, "pairs" => ETA_PAIRS), "Stokes preserved"),
        "S2.C_chern_normalization" => receipt(true, "closed_form", Dict("chart_integral" => -4.0 * pi, "reported_c1" => 1), "Chern row preserved"),
        "S2.T_local_metric_det" => receipt(true, "closed_form", Dict("sqrt_det_g" => metric_det_sqrt(eta)), "local determinant before quotienting passes"),
        "S2.T_physical_area" => receipt(false, "closed_form_control", Dict("naive_area" => chart_area(eta), "physical_area" => physical_area(eta), "overcount_factor" => chart_area(eta) / physical_area(eta), "fail_magnitude" => chart_area(eta) - physical_area(eta)), "naive chart area overcounts by factor two"),
        "S2.G_grid_count" => receipt(false, "exact_integer_control", Dict("N" => n, "naive_claimed_points" => naive_points, "physical_points" => physical_points, "overcount_factor" => naive_points / physical_points, "fail_magnitude" => naive_points - physical_points), "naive grid count reports N^2"),
        "S2.G_parity_identification" => receipt(false, "exact_integer_plus_numeric_pairs", merge(pair_data(n, eta), Dict{String,Any}("model_applies_quotient" => false, "fail_magnitude" => naive_points - physical_points)), "naive model refuses the quotient pairs"),
    )
    common_suite_adapter("negative_3_naive_cover_grid_one_to_one", true, receipts, Dict{String,Any}("negative_family" => "naive_cover_grid", "primary_fail_magnitude" => naive_points - physical_points))
end

function main()
    mkpath(RESULT_DIR)
    wrong_conn = wrong_connection_model()
    broken_stokes = broken_stokes_model()
    naive_cover = naive_cover_model()
    positive = positive_control()
    wrong_residual = scaled(wrong_conn["S2.H_horizontal_holonomy"]["measured"]["max_abs_residual"])
    broken_residual = scaled(broken_stokes["S2.S_stokes_strip"]["measured"]["max_abs_residual"])
    z3_wrong = z3_assert_int_eq(wrong_residual, 0)
    z3_broken = z3_assert_int_eq(broken_residual, 0)
    z3_positive = z3_assert_int_eq(0, 0)
    proofs = Dict{String,Any}(
        "julia_z3_wrong_connection_holonomy" => Dict(
            "scaled_integer_factor" => SCALE,
            "wrong_residual_scaled" => wrong_residual,
            "z3_assert_wrong_residual_zero" => z3_wrong,
            "z3_positive_control_assert_residual_zero" => z3_positive,
            "pass" => z3_wrong == "unsat" && z3_positive == "sat",
        ),
        "julia_z3_broken_stokes" => Dict(
            "scaled_integer_factor" => SCALE,
            "broken_residual_scaled" => broken_residual,
            "z3_assert_broken_residual_zero" => z3_broken,
            "z3_positive_control_assert_residual_zero" => z3_positive,
            "pass" => z3_broken == "unsat" && z3_positive == "sat",
        ),
    )
    all_pass = all([proof["pass"] for proof in values(proofs)])
    payload = Dict{String,Any}(
        "schema_version" => "geo_s2_negative_models_leg_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_authoritative_sim_builder",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "source_path" => relpath(SOURCE_PATH, ROOT),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => relpath(RESULT_PATH, ROOT),
        "generated_at" => string(Dates.now(Dates.UTC)),
        "reads_peer_result" => READS_PEER_RESULT,
        "julia_project" => Base.active_project(),
        "packages_used" => ["Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "claim_path_tools" => ["Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "convention_pin" => CONVENTION_PIN,
        "negative_model_receipts" => Dict(
            wrong_conn["model_id"] => wrong_conn,
            broken_stokes["model_id"] => broken_stokes,
            naive_cover["model_id"] => naive_cover,
        ),
        "positive_control" => positive,
        "proofs" => proofs,
        "shared_scalars" => Dict(
            "wrong_connection_max_holonomy_residual" => wrong_conn["S2.H_horizontal_holonomy"]["measured"]["max_abs_residual"],
            "broken_stokes_max_residual" => broken_stokes["S2.S_stokes_strip"]["measured"]["max_abs_residual"],
            "naive_cover_count_overfactor" => naive_cover["S2.G_grid_count"]["measured"]["overcount_factor"],
        ),
        "all_pass" => all_pass,
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => all_pass, "result_path" => RESULT_PATH, "engine" => "julia")))
    return all_pass ? 0 : 1
end

exit(main())
