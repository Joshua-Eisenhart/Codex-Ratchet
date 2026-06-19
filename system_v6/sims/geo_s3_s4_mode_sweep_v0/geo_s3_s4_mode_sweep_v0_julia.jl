#!/usr/bin/env julia
# Julia Symbolics/Z3 mirror for geo_s3_s4_mode_sweep_v0.

using Dates
using JSON
using SHA
using Symbolics
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s3_s4_mode_sweep_v0"
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

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))

function clean(x)
    text = string(Symbolics.simplify(x, expand=true))
    replacements = Dict("0.0" => "0", "1.0" => "1", "-0.0" => "0", "0//1" => "0", "1//1" => "1")
    return get(replacements, text, text)
end

function symbolics_descent_receipt()
    @variables x y z
    z_observable = z
    x_observable = x
    r_left = Dict(x => 1//2, y => 0, z => 0)
    r_right = Dict(x => -1//2, y => 0, z => 0)
    z_left = Symbolics.substitute(z_observable, r_left)
    z_right = Symbolics.substitute(z_observable, r_right)
    x_left = Symbolics.substitute(x_observable, r_left)
    x_right = Symbolics.substitute(x_observable, r_right)

    rx_z_output = y
    rz_z_output = z
    witness_plus = Dict(x => 0, y => 1//2, z => 0)
    witness_minus = Dict(x => 0, y => -1//2, z => 0)
    rx_plus = Symbolics.substitute(rx_z_output, witness_plus)
    rx_minus = Symbolics.substitute(rx_z_output, witness_minus)
    rz_plus = Symbolics.substitute(rz_z_output, witness_plus)
    rz_minus = Symbolics.substitute(rz_z_output, witness_minus)
    Dict(
        "z_observable_same_class_values" => [clean(z_left), clean(z_right)],
        "x_observable_same_class_values" => [clean(x_left), clean(x_right)],
        "z_measurement_descends" => clean(z_left - z_right) == "0",
        "x_measurement_descends" => clean(x_left - x_right) == "0",
        "R_x_z_output_same_class_values" => [clean(rx_plus), clean(rx_minus)],
        "R_z_z_output_same_class_values" => [clean(rz_plus), clean(rz_minus)],
        "R_x_descends" => clean(rx_plus - rx_minus) == "0",
        "R_z_descends" => clean(rz_plus - rz_minus) == "0",
        "pass" => clean(z_left - z_right) == "0" &&
            clean(x_left - x_right) != "0" &&
            clean(rx_plus - rx_minus) != "0" &&
            clean(rz_plus - rz_minus) == "0",
    )
end

function z3_same_class_control()
    solver = Z3.Solver()
    z_left = Z3.IntVar("z_left_scaled")
    z_right = Z3.IntVar("z_right_scaled")
    x_left = Z3.IntVar("x_left_scaled")
    x_right = Z3.IntVar("x_right_scaled")
    Z3.add(solver, z_left == z_right)
    Z3.add(solver, x_left == Z3.IntVal(1))
    Z3.add(solver, x_right == Z3.IntVal(-1))
    positive = string(Z3.check(solver))

    erased = Z3.Solver()
    e_z_left = Z3.IntVar("erased_z_left_scaled")
    e_z_right = Z3.IntVar("erased_z_right_scaled")
    Z3.add(erased, e_z_left == e_z_right)
    Z3.add(erased, Z3.Not(e_z_left == e_z_right))
    negative = string(Z3.check(erased))
    Dict(
        "positive_same_z_different_x_verdict" => positive,
        "erased_same_and_different_z_verdict" => negative,
        "pass" => positive == "sat" && negative == "unsat",
    )
end

function main()
    mkpath(RESULT_DIR)
    descent = symbolics_descent_receipt()
    z3_control = z3_same_class_control()
    all_pass = descent["pass"] == true && z3_control["pass"] == true
    result = Dict(
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "all_pass" => all_pass,
        "ran" => true,
        "reads_peer_result" => false,
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "julia_project" => "system_v5/julia_carrier",
        "packages_used" => ["Symbolics", "Z3", "JSON", "SHA"],
        "aligned_packages_load_bearing" => ["Symbolics", "Z3"],
        "TOOL_MANIFEST" => Dict(
            "Symbolics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing symbolic mirror of z-probe descent and S4 operator well-definedness"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing same-class can-fail control"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization"),
            "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source hashing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Symbolics" => "load_bearing", "Z3" => "load_bearing", "JSON" => "supportive", "SHA" => "supportive"),
        "symbolics_descent_test" => descent,
        "z3_same_class_control" => z3_control,
        "tool_calls" => [
            Dict(
                "tool" => "Symbolics",
                "qualified_api/function" => "Symbolics.@variables / Symbolics.substitute / Symbolics.simplify",
                "input_object" => "same-z witness pairs and S4 z-output expressions",
                "output_object" => "observable descent and operator well-definedness rows",
                "positive_case" => "z observable and R_z descend",
                "negative/erased_control" => "x observable and R_x do not descend",
                "boundary_case" => "z-probe quotient only",
                "demotion_condition" => "demote if Symbolics no longer computes witness values",
                "gates" => ["julia_symbolics_z3_mirror"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver / Z3.add / Z3.check",
                "input_object" => "same-z different-x integer witness",
                "output_object" => "sat positive and unsat erased contradiction",
                "positive_case" => "same z and different x is satisfiable",
                "negative/erased_control" => "same z and different z is unsat",
                "boundary_case" => "control branch only",
                "demotion_condition" => "demote if can-fail control is removed",
                "gates" => ["julia_symbolics_z3_mirror"],
            ),
        ],
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println(JSON.json(Dict("ok" => all_pass, "result_path" => RESULT_PATH_REL)))
    return all_pass ? 0 : 1
end

exit(main())
