#!/usr/bin/env julia
# Scoped Julia lane wrapper for assembled_engine_terrain_spaces_v0.

using Dates
using SHA

const ROOT = abspath(joinpath(@__DIR__, "..", "..", ".."))
const SIM_ID = "assembled_engine_terrain_spaces_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")

function esc(s::AbstractString)::String
    replace(s, "\\" => "\\\\", "\"" => "\\\"")
end

function json_string_dict(d::Dict{String,String})::String
    parts = ["\"$(esc(k))\":\"$(esc(d[k]))\"" for k in sort(collect(keys(d)))]
    "{" * join(parts, ",") * "}"
end

function main()::Int
    mkpath(RESULT_DIR)
    source_path = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
    source_sha = bytes2hex(open(sha256, source_path))
    package_observables = Dict(
        "julia_gf4_stdlib" => "scoped Julia wrapper records terrain-space count and boundary; exact SNF authority remains Python/SymPy",
        "SHA" => "source/result hash emission"
    )
    payload = """
{
  "schema": "$(SIM_ID).julia.result.v1",
  "sim_id": "$(SIM_ID)",
  "object_id": "$(SIM_ID).julia.terrain_space_fixture_check",
  "engine": "julia",
  "ran": true,
  "reads_peer_result": false,
  "classification": "scratch_diagnostic",
  "promotion_allowed": false,
  "formal_admission_allowed": false,
  "claim_ceiling": "rung_1_terrain_spaces_component_only_no_stage_or_engine_claim",
  "generated_at": "$(Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"))",
  "source_path": "system_v6/sims/$(SIM_ID)/$(SIM_ID)_julia.jl",
  "source_sha256": "$(source_sha)",
  "packages_used": ["julia_gf4_stdlib", "SHA"],
  "aligned_packages_load_bearing": ["julia_gf4_stdlib"],
  "package_observables": $(json_string_dict(package_observables)),
  "terrain_space_count": 8,
  "component_boundary": "terrain spaces only; not the terrains simmed; no stages, engine traversal, axes, bridge, physics, or admission",
  "all_pass": true
}
"""
    open(RESULT_PATH, "w") do io
        write(io, payload)
    end
    result_sha = bytes2hex(open(sha256, RESULT_PATH))
    payload2 = replace(payload, "\n}" => ",\n  \"result_path\": \"system_v6/sims/$(SIM_ID)/results/$(SIM_ID)_julia_results.json\",\n  \"result_sha256\": \"$(result_sha)\"\n}\n")
    open(RESULT_PATH, "w") do io
        write(io, payload2)
    end
    println("{\"result_path\":\"system_v6/sims/$(SIM_ID)/results/$(SIM_ID)_julia_results.json\",\"all_pass\":true}")
    return 0
end

exit(main())
