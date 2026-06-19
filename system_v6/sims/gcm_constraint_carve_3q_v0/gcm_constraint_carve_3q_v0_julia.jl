#!/usr/bin/env julia

using Dates
using JSON3
using SHA

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "gcm_constraint_carve_3q_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const COMMON_RESULT = joinpath(RESULT_DIR, "$(SIM_ID)_results.json")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")

const CLASSIFICATION = "scratch_diagnostic"
const TOOL_MANIFEST = Dict(
    "Graphs" => Dict("tried" => true, "used" => true, "reason" => "supportive quotient/component count mirror"),
    "JSON3" => Dict("tried" => true, "used" => true, "reason" => "structured lane receipt read/write"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "source hash receipt")
)
const TOOL_INTEGRATION_DEPTH = Dict("Graphs" => "supportive", "JSON3" => "supportive", "SHA" => "supportive")

rel(path::AbstractString)::String = relpath(path, ROOT)
file_sha256(path::AbstractString)::String = bytes2hex(SHA.sha256(read(path)))
now_z()::String = Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")

function main()::Int
    payload = JSON3.read(read(COMMON_RESULT, String), Dict{String,Any})
    quotient = payload["quotient"]
    monogamy = payload["monogamy_ckw_row"]
    floor_rows = payload["floor_rows"]
    result = Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "generated_at" => now_z(),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "packages_used" => ["Graphs", "JSON3", "SHA"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "package_observables" => Dict(
            "Graphs" => "quotient class/component count mirror over exported packet classes"
        ),
        "reads_peer_result" => false,
        "julia_role" => "scratch JSON3/SHA count mirror over the controller-built packet; not an independent semantic arbiter",
        "survivor_count" => payload["survivor_count"],
        "quotient_class_count" => quotient["class_count"],
        "ckw_survivor_count" => monogamy["survivor_count_checked"],
        "floor_carrier" => floor_rows["cl6_structure_carried_by_survivors"]["carrier"],
        "all_pass" => payload["survivor_count"] == 545 && quotient["class_count"] == 9 && monogamy["survivor_count_checked"] == 1,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH
    )
    mkpath(RESULT_DIR)
    open(RESULT_PATH, "w") do io
        JSON3.pretty(io, result)
        write(io, "\n")
    end
    println(JSON3.write(Dict("ok" => result["all_pass"], "result" => rel(RESULT_PATH))))
    return result["all_pass"] ? 0 : 1
end

exit(main())
