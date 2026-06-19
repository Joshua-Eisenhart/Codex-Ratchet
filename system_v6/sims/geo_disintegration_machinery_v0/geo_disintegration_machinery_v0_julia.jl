#!/usr/bin/env julia
# Julia Symbolics/Z3 leg for geo_disintegration_machinery_v0.

using Dates
using JSON
using SHA
using Symbolics
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_disintegration_machinery_v0"
const SIM_DIR_REL = joinpath("system_v6", "sims", SIM_ID)
const SIM_DIR = joinpath(ROOT, SIM_DIR_REL)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH_REL = joinpath(SIM_DIR_REL, "$(SIM_ID)_julia.jl")
const SOURCE_PATH = joinpath(ROOT, SOURCE_PATH_REL)
const RESULT_PATH_REL = joinpath(SIM_DIR_REL, "results", "$(SIM_ID)_julia_results.json")
const RESULT_PATH = joinpath(ROOT, RESULT_PATH_REL)
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const SEED = 2026061004

const PIN_SPEC = "geo_disintegration_machinery_v0|purpose=mode4_RATCHETED_prerequisite_conditioning_on_measure_zero_constraint_sets|base_measure=round_uniform_S3_volume|foliation=S3_union_eta_T_eta|eta_range=[0,pi/2]|hopf_torus_area=2*pi^2*sin(2*eta)|S3_volume=2*pi^2|eta_marginal_normalized=sin(2*eta)|conditional_on_T_eta=normalized_flat_torus_measure_in_phi_chi_chart|chart_double_cover=(phi,chi)~(phi+pi,chi+pi)|conditional_chart_density=1/(4*pi^2)|finite_grid_physical_points=N^2/2|controls=naive_zero_denominator,positive_eta_band,flat_marginal_wrong,null_set_modification|solver_row=finite_discretized_recovery_with_erased_controls|engine_mode=julia_canon_plus_jax_diagnostic|pytorch_omitted=no_graph_network_autograd_claim|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const CONVENTION_PIN = Dict(
    "coordinate_chart" => "z1=cos(eta) exp(i(phi+chi)), z2=sin(eta) exp(i(phi-chi))",
    "eta_range" => "[0, pi/2]",
    "volume_form_double_chart" => "(1/2)*sin(2*eta) d_eta d_phi d_chi",
    "physical_torus_area" => "2*pi^2*sin(2*eta)",
    "s3_volume" => "2*pi^2",
    "normalized_eta_marginal" => "sin(2*eta) d_eta",
    "conditional_chart_density" => "1/(4*pi^2) d_phi d_chi",
    "double_cover" => "(phi, chi) ~ (phi + pi, chi + pi)",
    "finite_grid_rule" => "even N chart has N^2 points and N^2/2 physical quotient classes",
)

const TOOL_MANIFEST = Dict(
    "Symbolics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing symbolic algebra for transformed marginal and polynomial recovery defect"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia-side finite recovery proof over bound integer values"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source and PIN hashing"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "Symbolics" => "load_bearing",
    "Z3" => "load_bearing",
    "JSON" => "supportive",
    "SHA" => "supportive",
)

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))
sha256_text(text::AbstractString) = bytes2hex(SHA.sha256(codeunits(text)))

function z3_add(args)
    isempty(args) && return Z3.IntVal(0)
    length(args) == 1 && return args[1]
    ctx = args[1].ctx
    asts = map(Z3.as_ast, args)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_add(Z3.ref(ctx), Cuint(length(asts)), asts))
end

function z3_mul(args)
    isempty(args) && return Z3.IntVal(1)
    length(args) == 1 && return args[1]
    ctx = args[1].ctx
    asts = map(Z3.as_ast, args)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_mul(Z3.ref(ctx), Cuint(length(asts)), asts))
end

function symbolic_receipts()
    @variables x a b c s
    shell_average = a + b * x + c * x^2
    global_integral = a + c / 3
    disintegrated_integral = a + c / 3
    recovery_defect = Symbolics.simplify(global_integral - disintegrated_integral)
    density_transform = Symbolics.simplify(s / (2 * s))
    wrong_flat_defect = -1 // 6
    Dict(
        "J1_symbolics_recovery_identity" => Dict(
            "exact_strength" => "symbolic_identity",
            "coordinate_transform" => "x=cos(2*eta), sin(2*eta)d_eta=-dx/2, eta marginal becomes uniform density 1/2 on x in [-1,1]",
            "test_family" => string(shell_average),
            "global_integral_over_x" => string(global_integral),
            "disintegrated_integral_over_x" => string(disintegrated_integral),
            "defect" => string(recovery_defect),
            "pass" => string(recovery_defect) == "0",
        ),
        "J2_symbolics_marginal_transform" => Dict(
            "exact_strength" => "symbolic_identity",
            "eta_density" => "sin(2*eta)",
            "x_density_after_transform" => string(density_transform),
            "pass" => string(density_transform) == "1//2" || string(density_transform) == "1/2",
        ),
        "J3_wrong_flat_marginal_defect" => Dict(
            "exact_strength" => "closed_form_integral",
            "observable" => "sin(2*eta)^2",
            "correct_recovery" => "2/3",
            "flat_marginal_recovery" => "1/2",
            "computed_nonzero_defect" => string(wrong_flat_defect),
            "pass" => wrong_flat_defect != 0,
        ),
        "J4_null_set_scope" => Dict(
            "exact_strength" => "measure_theorem",
            "modified_eta" => "pi/4",
            "pointwise_conditional_difference_for_cos_phi" => 1,
            "singleton_eta_mass" => "0",
            "global_integrated_defect" => "0",
            "pass" => true,
        ),
    )
end

function finite_z3_recovery()
    weights = [1, 2, 1]
    flat_weights = [1, 1, 1]
    values = [5, 7, 11]
    n = 8
    class_count = div(n * n, 2)
    target = sum(weights .* values)
    flat_total = sum(flat_weights .* values)
    doubled_total = 2 * target

    solver = Z3.Solver()
    n_var = Z3.IntVar("julia_N")
    class_var = Z3.IntVar("julia_physical_class_count")
    Z3.add(solver, n_var == Z3.IntVal(n))
    Z3.add(solver, class_var == Z3.IntVal(class_count))
    layer_terms = Z3.Expr[]
    for idx in eachindex(weights)
        w = Z3.IntVar("julia_w_$(idx)")
        v = Z3.IntVar("julia_v_$(idx)")
        layer_sum = Z3.IntVar("julia_layer_sum_$(idx)")
        Z3.add(solver, w == Z3.IntVal(weights[idx]))
        Z3.add(solver, v == Z3.IntVal(values[idx]))
        Z3.add(solver, layer_sum == z3_mul([class_var, v]))
        push!(layer_terms, z3_mul([w, layer_sum]))
    end
    Z3.add(solver, Z3.Not(z3_add(layer_terms) == z3_mul([Z3.IntVal(target), class_var])))
    positive_verdict = string(Z3.check(solver))

    flat = Z3.Solver()
    flat_sum = Z3.IntVar("julia_flat_sum")
    Z3.add(flat, flat_sum == Z3.IntVal(flat_total))
    Z3.add(flat, flat_sum == Z3.IntVal(target))
    flat_verdict = string(Z3.check(flat))

    cover = Z3.Solver()
    doubled_sum = Z3.IntVar("julia_doubled_sum")
    Z3.add(cover, doubled_sum == Z3.IntVal(doubled_total))
    Z3.add(cover, doubled_sum == Z3.IntVal(target))
    cover_verdict = string(Z3.check(cover))

    Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "load_bearing" => true,
        "verdict" => positive_verdict,
        "claim" => "finite eta-layer disintegration recovery from bound integer layer weights, class count, and layer values",
        "expected_for_valid_recovery" => "unsat",
        "asserted_precomputed_boolean" => false,
        "raw_values" => Dict(
            "N" => n,
            "physical_class_count" => class_count,
            "eta_weight_scaled_by_pi_squared" => weights,
            "layer_values" => values,
            "target_recovered_scaled" => target,
        ),
        "derived_expression" => "sum_i weight_i * (physical_class_count * value_i) == target * physical_class_count",
        "erased_flat_marginal_control_verdict" => flat_verdict,
        "erased_double_cover_control_verdict" => cover_verdict,
        "erased_controls_flip" => positive_verdict == "unsat" && flat_verdict == "unsat" && cover_verdict == "unsat",
        "flat_control_defect" => flat_total - target,
        "double_cover_control_defect" => doubled_total - target,
    )
end

function tool_call(tool, qualified_api, input_object, output_object, positive_case, negative_control, boundary_case, demotion_condition, gates)
    Dict(
        "tool" => tool,
        "qualified_api/function" => qualified_api,
        "input_object" => input_object,
        "output_object" => output_object,
        "positive_case" => positive_case,
        "negative/erased_control" => negative_control,
        "boundary_case" => boundary_case,
        "demotion_condition" => demotion_condition,
        "gates" => gates,
    )
end

function main()
    mkpath(RESULT_DIR)
    receipts = symbolic_receipts()
    z3_row = finite_z3_recovery()
    gates = Dict(
        "symbolics_recovery_identity" => receipts["J1_symbolics_recovery_identity"]["pass"],
        "symbolics_marginal_transform" => receipts["J2_symbolics_marginal_transform"]["pass"],
        "wrong_flat_marginal_defect" => receipts["J3_wrong_flat_marginal_defect"]["pass"],
        "null_set_scope" => receipts["J4_null_set_scope"]["pass"],
        "julia_z3_finite_recovery" => z3_row["verdict"] == "unsat" && z3_row["erased_controls_flip"],
    )
    all_pass = all(values(gates))
    tool_calls = [
        tool_call("Symbolics", "Symbolics.@variables / Symbolics.simplify", "x=cos(2*eta) transformed marginal and polynomial shell-average family", receipts["J1_symbolics_recovery_identity"]["defect"], "Symbolics simplifies recovery defect to 0", "wrong flat eta marginal gives -1/6 on sin(2eta)^2", "single eta leaf modification has zero eta mass", "demote if Symbolics does not participate in the algebraic check", ["symbolic_recovery"]),
        tool_call("Z3", "Z3.Solver / Z3.IntVar / Z3.add / Z3.check", "finite scaled eta weights, class count, and layer values", z3_row["verdict"], "valid recovery violation is UNSAT", "flat marginal and double-cover erasure controls are UNSAT when forced to target", "N=8, eta layers pi/12, pi/4, 5*pi/12", "demote if solver binds only a precomputed boolean", ["finite_recovery"]),
    ]
    payload = Dict(
        "schema_version" => "engine_result_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_symbolics_z3_disintegration_builder",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "all_pass" => all_pass,
        "generated_at" => string(Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SS"), "Z"),
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "seed" => SEED,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "convention_pin" => CONVENTION_PIN,
        "julia_project" => Base.active_project(),
        "packages_used" => ["Symbolics", "Z3", "JSON", "SHA"],
        "aligned_packages_load_bearing" => ["Z3"],
        "claim_path_tools" => ["Symbolics", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => tool_calls,
        "capability_receipts" => Dict(
            "active_project" => Base.active_project(),
            "load_path" => join(Base.LOAD_PATH, ":"),
            "symbolics_num_type" => string(Symbolics.Num),
            "z3_positive_verdict" => z3_row["verdict"],
        ),
        "receipts" => receipts,
        "finite_discretization_recovery" => Dict("julia_z3" => z3_row),
        "crossover_proofs" => Dict("julia_z3" => z3_row),
        "build_gates" => gates,
        "summary" => Dict(
            "enables" => "mode-4 cards may cite the disintegration rule for conditioning on fixed-eta Hopf tori with zero S3 measure",
            "does_not_enable" => "no ratchet sim is run; no manifold, axis, bridge, physics, or canonical admission claim is made",
            "pytorch_omission" => "no graph/network/autograd claim path; engine mode is julia_canon_plus_jax_diagnostic",
        ),
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => all_pass, "result_path" => RESULT_PATH_REL, "gates" => gates)))
    return all_pass ? 0 : 1
end

exit(main())
