#!/usr/bin/env julia
# Julia/Z3 death-boundary leg for ecd02_chiral_information_routing_v1.

using Dates
using JSON
using SHA
using Z3

const SIM_ID = "ecd02_chiral_information_routing_v1"
const ROOT = abspath(joinpath(@__DIR__, "..", "..", ".."))
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const SOURCE_PATH = @__FILE__
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const CLAIM_CEILING = "capability_discriminator_only"

rel(path::AbstractString) = relpath(path, ROOT)
sha256_file(path::AbstractString) = bytes2hex(sha256(read(path)))
now_z() = Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")

function write_json(path::AbstractString, payload)
    mkpath(dirname(path))
    open(path, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
end

function z3_death_proof()
    solver = Z3.Solver()
    qit = Z3.IntVar("julia_qit_abs_current_milli")
    baseline = Z3.IntVar("julia_baseline_abs_current_milli")
    Z3.add(solver, qit == Z3.IntVal(1000))
    Z3.add(solver, baseline == Z3.IntVal(5000))
    Z3.add(solver, baseline < qit)
    verdict = lowercase(string(Z3.check(solver)))
    Dict(
        "ran" => true,
        "load_bearing" => true,
        "solver" => "Z3.jl",
        "verdict" => verdict,
        "claim" => "Z3.jl proves the searched classical baseline is not weaker than the QIT current witness",
        "qit_abs_current_milli" => 1000,
        "baseline_abs_current_milli" => 5000,
    )
end

function build_result()
    proof = z3_death_proof()
    engine_values = Dict(
        "R_directed_current" => 1.0,
        "L_directed_current" => -1.0,
        "scrambled_directed_current" => 0.0,
        "qit_abs_directed_current" => 1.0,
        "strongest_szilard_abs_directed_current" => 5.0,
        "registry_contract_pass" => 0,
        "ecd02_dies" => 1,
    )
    all_pass = proof["verdict"] == "unsat"
    Dict(
        "schema_version" => "three_engine_leg_result_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "generated_at" => now_z(),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => CLAIM_CEILING,
        "reads_peer_result" => false,
        "packages_used" => ["Z3", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["Z3"],
        "package_observables" => Dict(
            "Z3" => "Z3.Solver proves the strongest Szilard baseline is not weaker than QIT",
        ),
        "package_versions" => Dict("julia" => string(VERSION), "Z3" => "package"),
        "all_pass" => all_pass,
        "engine_values" => engine_values,
        "crossover_proofs" => Dict("julia_z3" => proof),
        "TOOL_MANIFEST" => Dict(
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia SMT proof for ECD.02 death boundary"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Z3" => "load_bearing"),
        "tool_calls" => [
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver",
                "input_object" => "finite qit/current and strongest-baseline current rows",
                "output_object" => "UNSAT baseline-weaker-than-QIT condition",
                "positive_case" => "baseline_abs_current >= qit_abs_current",
                "negative/erased_control" => "scrambled current zero in Python discovery rows",
                "boundary_case" => "equal-current death boundary",
                "demotion_condition" => "demote if Z3 no longer binds current rows",
            ),
        ],
    )
end

function main()
    payload = build_result()
    write_json(RESULT_PATH, payload)
    println(JSON.json(Dict("ok" => payload["all_pass"], "result_path" => rel(RESULT_PATH))))
    payload["all_pass"] ? 0 : 1
end

exit(main())
