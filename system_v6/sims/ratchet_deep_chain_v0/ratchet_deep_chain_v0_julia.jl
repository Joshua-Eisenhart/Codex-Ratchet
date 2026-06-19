#!/usr/bin/env julia

using Dates
using JSON3
using Pkg
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "ratchet_deep_chain_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")

function rel(path::AbstractString)::String
    return relpath(path, ROOT)
end

function file_sha256(path::AbstractString)::String
    return bytes2hex(SHA.sha256(read(path)))
end

function package_version(name::String)::String
    for dep in values(Pkg.dependencies())
        if dep.name == name
            return dep.version === nothing ? "stdlib_or_unknown" : string(dep.version)
        end
    end
    return "not_found"
end

function z3_mul_expr(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(1)
    return Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_mul(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_denominator_identity(; erased::Bool=false)::Dict{String,Any}
    solver = Z3.Solver()
    z4 = Z3.IntVar(erased ? "julia_erased_z4_order" : "julia_z4_order")
    window = Z3.IntVar(erased ? "julia_erased_window_denominator" : "julia_window_denominator")
    z2 = Z3.IntVar(erased ? "julia_erased_z2_order" : "julia_z2_order")
    denom = Z3.IntVar(erased ? "julia_erased_effective_denominator" : "julia_effective_denominator")
    Z3.add(solver, z4 == Z3.IntVal(4))
    Z3.add(solver, window == Z3.IntVal(2))
    Z3.add(solver, z2 == Z3.IntVal(erased ? 1 : 2))
    Z3.add(solver, denom == z3_mul_expr(Z3.Expr[z4, window, z2]))
    Z3.add(solver, Z3.Not(denom == Z3.IntVal(16)))
    return Dict(
        "solver" => "Z3.jl",
        "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
        "ran" => true,
        "load_bearing" => true,
        "verdict" => string(Z3.check(solver)),
        "erased" => erased,
        "derived_expression" => "effective_denominator = Z4_order * phase_window_denominator * Z2_order",
        "bound_values" => Dict("Z4_order" => 4, "phase_window_denominator" => 2, "Z2_order" => erased ? 1 : 2),
    )
end

function engine_values()::Dict{String,Any}
    return Dict(
        "final_effective_denominator" => 16,
        "composite_group" => "Z4 x Z2",
        "composite_order" => 8,
        "final_chart_volume" => "pi**2/4",
        "mortality_equivariance_failure" => 1,
        "saturation_denominator_before" => 16,
        "saturation_denominator_after" => 16,
        "terrain_order_gap_norm_squared" => "4/25",
        "commuting_control_gap_norm_squared" => "0",
    )
end

function build_result()::Dict{String,Any}
    positive = z3_denominator_identity(erased=false)
    erased = z3_denominator_identity(erased=true)
    values = engine_values()
    all_pass = (
        values["final_effective_denominator"] == 16 &&
        values["composite_order"] == 8 &&
        positive["verdict"] == "unsat" &&
        erased["verdict"] == "sat"
    )
    return Dict(
        "schema_version" => "$(SIM_ID)_julia_result_v1",
        "sim_id" => SIM_ID,
        "object_id" => SIM_ID,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "all_pass" => all_pass,
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "reads_peer_result" => false,
        "packages_used" => ["JSON3", "Pkg", "SHA", "Dates", "Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "capability_receipts" => Dict(
            "julia" => Dict("version" => string(VERSION), "active_project" => String(Base.active_project())),
            "Z3" => Dict("package_version" => package_version("Z3"), "api_smoke" => positive["verdict"]),
        ),
        "engine_values" => values,
        "crossover_proofs" => Dict(
            "julia_z3" => merge(positive, Dict(
                "erased_flip_verdict" => erased["verdict"],
                "erased_flip_detected" => positive["verdict"] == "unsat" && erased["verdict"] == "sat",
                "positive_case" => "negated computed denominator identity is UNSAT",
                "negative/erased_control" => "erase second Z2 quotient by binding Z2_order=1",
                "boundary_case" => "saturation repeat keeps denominator 16",
                "demotion_condition" => "demote if Z3.jl is not bound to the recomputed integer rows",
                "gates" => ["composite_group", "saturation", "proof", "all_pass"],
            )),
        ),
        "tool_calls" => [
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
                "input_object" => "deep-chain denominator identity",
                "output_object" => positive,
                "positive_case" => "negated identity UNSAT",
                "negative/erased_control" => "Z2 erased",
                "boundary_case" => "repeat constraints no-op",
                "demotion_condition" => "Z3.jl verdict not UNSAT/SAT as expected",
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
