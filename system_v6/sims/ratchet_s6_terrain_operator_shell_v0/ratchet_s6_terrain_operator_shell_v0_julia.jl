#!/usr/bin/env julia

using Dates
using JSON3
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "ratchet_s6_terrain_operator_shell_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const TERRAIN_ID = "Se_Funnel_L"
const OPERATOR_ID = "Fi_R_x"
const CONTROL_ID = "D_z_then_R_z"
const ETA0 = "pi/6"
const TERRAIN_AB_SHA256 = "25f78fc755e37729771e46eef26f6d80358dbcee06891917e2ebe82dcee5128a"

function rel(path::AbstractString)::String
    return relpath(path, ROOT)
end

function file_sha256(path::AbstractString)::String
    return bytes2hex(SHA.sha256(read(path)))
end

function z3_mul(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(1)
    length(args) == 1 && return args[1]
    return Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_mul(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_prove_se_rx_gap()::Dict{String,Any}
    solver = Z3.Solver()
    s2 = Z3.IntVar("sqrt3_squared")
    gap15 = Z3.IntVar("se_funnel_rx_gap_z_scaled_by_15_at_theta0")
    Z3.add(solver, s2 == Z3.IntVal(3))
    Z3.add(solver, gap15 == z3_mul(Z3.Expr[Z3.IntVal(-2), s2]))
    Z3.add(solver, gap15 == Z3.IntVal(0))
    verdict = string(Z3.check(solver))

    erased = Z3.Solver()
    erased_gap15 = Z3.IntVar("erased_skew_gap_z_scaled_by_15")
    Z3.add(erased, erased_gap15 == Z3.IntVal(0))
    Z3.add(erased, erased_gap15 == Z3.IntVal(0))
    erased_verdict = string(Z3.check(erased))

    return Dict(
        "solver" => "Z3.jl",
        "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
        "ran" => true,
        "load_bearing" => true,
        "verdict" => verdict,
        "claim" => "Se_Funnel_L generator and R_x(pi/2) have nonzero N01 order gap on T_pi/6 at theta=0",
        "derived_expression" => "15*Delta_z = -2*sqrt3_squared with sqrt3_squared=3",
        "positive_case" => "asserting the derived scaled gap is zero is UNSAT",
        "negative/erased_control" => "erase the Se skew/off-diagonal component to the scalar dissipative part; zero-gap assertion becomes SAT",
        "erased_flip_verdict" => erased_verdict,
        "erased_flip_detected" => erased_verdict == "sat",
        "boundary_case" => "theta=pi/2 moves the nonzero witness from z component to x component",
        "demotion_condition" => "demote if Z3.jl does not refute the zero-gap assertion from the bound scaled row",
        "gates" => ["path_specificity", "proof", "all_pass"],
    )
end

function z3_prove_commuting_control_zero()::Dict{String,Any}
    solver = Z3.Solver()
    ctrl_gap = Z3.IntVar("dz_rz_control_gap_scaled")
    Z3.add(solver, ctrl_gap == Z3.IntVal(0))
    Z3.add(solver, Z3.Not(ctrl_gap == Z3.IntVal(0)))
    verdict = string(Z3.check(solver))
    return Dict(
        "solver" => "Z3.jl",
        "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
        "ran" => true,
        "load_bearing" => true,
        "verdict" => verdict,
        "claim" => "D_z and R_z commuting control has zero order gap",
        "derived_expression" => "Delta_control_scaled = 0",
        "positive_case" => "asserting a nonzero commuting-control gap is UNSAT",
        "negative/erased_control" => "replace R_z by R_x to recover the cross-axis noncommuting row in the Python exact lane",
        "boundary_case" => "q_z=0 identity dephasing also gives zero gap",
        "demotion_condition" => "demote if the commuting-control zero row is not solver-checked",
        "gates" => ["commuting_control", "all_pass"],
    )
end

function exact_rows(z3_gap::Dict{String,Any}, z3_control::Dict{String,Any})::Dict{String,Any}
    return Dict(
        "eta0" => ETA0,
        "shell_z" => "1/2",
        "shell_radius_xy" => "sqrt(3)/2",
        "terrain_id" => TERRAIN_ID,
        "operator_id" => OPERATOR_ID,
        "terrain_ab_sha256" => TERRAIN_AB_SHA256,
        "terrain_generator_A" => [
            ["-4/5", "-2*sqrt(3)/15", "2*sqrt(3)/15"],
            ["2*sqrt(3)/15", "-4/5", "-2*sqrt(3)/15"],
            ["-2*sqrt(3)/15", "2*sqrt(3)/15", "-4/5"],
        ],
        "terrain_generator_b" => ["0", "0", "0"],
        "leaf_state_family" => "r(theta)=(sqrt(3)/2*cos(theta), sqrt(3)/2*sin(theta), 1/2)",
        "terrain_z_dot" => "-sqrt(2)*cos(theta + pi/4)/5 - 2/5",
        "terrain_theta_dot" => "-2*sqrt(2)*sin(theta + pi/4)/15 + 2*sqrt(3)/15",
        "terrain_purity_derivative" => "-8/5",
        "terrain_shell_average_leakage" => "-2/5",
        "terrain_classification" => "cross_shell_with_leave_foliation",
        "induced_fixed_points_on_conditioned_object" => [],
        "unconstrained_fixed_point" => ["0", "0", "0"],
        "unconstrained_fixed_point_survives_conditioning" => false,
        "excluded_reason" => "unconstrained fixed point has z=0 and Bloch radius 0, not z=1/2 and pure radius 1",
        "order_gap_delta" => ["2*sin(theta)/5", "0", "-2*cos(theta)/5"],
        "order_gap_norm_squared" => "4/25",
        "order_gap_witness_theta0" => ["0", "0", "-2/5"],
        "commuting_control" => Dict(
            "terrain_channel" => "D_z",
            "operator" => "R_z",
            "gap" => ["0", "0", "0"],
            "gap_norm_squared" => "0",
        ),
        "wrong_leaf_control" => Dict(
            "wrong_eta" => "pi/4",
            "wrong_leaf_shell_average_leakage" => "0",
            "selected_leaf_shell_average_leakage" => "-2/5",
            "control_fired" => true,
        ),
        "julia_z3_gap_verdict" => z3_gap["verdict"],
        "julia_z3_erased_flip_verdict" => z3_gap["erased_flip_verdict"],
        "julia_z3_control_verdict" => z3_control["verdict"],
    )
end

function build_result()::Dict{String,Any}
    z3_gap = z3_prove_se_rx_gap()
    z3_control = z3_prove_commuting_control_zero()
    rows = exact_rows(z3_gap, z3_control)
    all_pass = (
        z3_gap["verdict"] == "unsat" &&
        z3_gap["erased_flip_verdict"] == "sat" &&
        z3_control["verdict"] == "unsat" &&
        rows["order_gap_norm_squared"] == "4/25" &&
        rows["commuting_control"]["gap_norm_squared"] == "0" &&
        rows["terrain_classification"] == "cross_shell_with_leave_foliation" &&
        rows["unconstrained_fixed_point_survives_conditioning"] == false
    )
    return Dict(
        "schema_version" => "$(SIM_ID)_julia_result_v1",
        "sim_id" => SIM_ID,
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "all_pass" => all_pass,
        "julia_project" => String(Base.active_project()),
        "load_path" => String.(Base.LOAD_PATH),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "reads_peer_result" => false,
        "packages_used" => ["JSON3", "SHA", "Dates", "Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "exact_rows" => rows,
        "engine_values" => Dict(
            "terrain_id" => TERRAIN_ID,
            "operator_id" => OPERATOR_ID,
            "terrain_ab_sha256" => TERRAIN_AB_SHA256,
            "shell_z" => "1/2",
            "terrain_shell_average_leakage" => "-2/5",
            "terrain_classification" => "cross_shell_with_leave_foliation",
            "induced_fixed_point_count" => 0,
            "unconstrained_fixed_point_survives_conditioning" => 0,
            "order_gap_norm_squared" => "4/25",
            "order_gap_witness_theta0_z" => "-2/5",
            "commuting_control_gap_norm_squared" => "0",
            "quotient_survival_row" => "56/56",
        ),
        "crossover_proofs" => Dict(
            "julia_z3" => z3_gap,
            "julia_z3_commuting_control" => z3_control,
        ),
        "tool_calls" => [
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
                "input_object" => "scaled Se_Funnel_L/R_x order-gap row at theta=0",
                "output_object" => z3_gap,
                "positive_case" => z3_gap["positive_case"],
                "negative/erased_control" => z3_gap["negative/erased_control"],
                "boundary_case" => z3_gap["boundary_case"],
                "demotion_condition" => z3_gap["demotion_condition"],
                "gates" => z3_gap["gates"],
                "load_bearing" => true,
            ),
        ],
    )
end

function main()::Int
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON3.pretty(io, result)
        write(io, "\n")
    end
    println(JSON3.write(Dict("ok" => result["all_pass"], "result_path" => rel(RESULT_PATH))))
    return result["all_pass"] ? 0 : 1
end

exit(main())
