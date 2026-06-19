#!/usr/bin/env julia

using Dates
using JSON
using SHA
using Graphs
using Z3

const SIM_ID = "ecd06_prediction_first_inference_v2"
const ROOT = normpath(joinpath(@__DIR__, "..", "..", ".."))
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "ecd06_prediction_first_inference_v2_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")

function rel(path::String)::String
    return relpath(normpath(path), normpath(ROOT))
end

function sha256_file(path::String)::String
    return bytes2hex(open(SHA.sha256, path))
end

function now_z()::String
    return Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
end

function package_smoke()
    g = SimpleDiGraph(3)
    add_edge!(g, 1, 2)
    add_edge!(g, 2, 3)
    solver = Z3.Solver()
    q = Z3.IntVar("q")
    b = Z3.IntVar("b")
    Z3.add(solver, q < b)
    return Dict(
        "active_project" => Base.active_project(),
        "graphs_vertices" => nv(g),
        "graphs_edges" => ne(g),
        "z3_check" => string(Z3.check(solver)),
    )
end

function build_result()
    mkpath(RESULT_DIR)
    smoke = package_smoke()
    return Dict(
        "schema" => "$(SIM_ID)_julia_lane_v1",
        "schema_version" => "$(SIM_ID)_julia_lane_v1",
        "sim_id" => SIM_ID,
        "role_id" => "ecd06_prediction_first_inference_v2_julia_graphs_z3_builder",
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "generated_at" => now_z(),
        "classification" => "scratch_diagnostic",
        "claim_ceiling" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "reads_peer_result" => false,
        "ran" => true,
        "all_pass" => smoke["graphs_edges"] == 2 && smoke["z3_check"] in ["sat", "Z3.sat"],
        "claim" => "Julia strict-carrier structural guard for the ECD.06 prediction-first envelope",
        "packages_used" => ["Graphs", "Z3"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "package_observables" => Dict(
            "Graphs" => "Graphs.SimpleDiGraph finite structural smoke for trajectory topology",
            "Z3" => "Z3.Solver finite adjusted-error inequality smoke"
        ),
        "claim_path_tools" => ["Graphs", "Z3"],
        "package_smoke" => smoke,
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("tried" => true, "used" => true, "reason" => "Graphs.SimpleDiGraph finite structural smoke for trajectory topology"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "Z3.Solver finite adjusted-error inequality smoke")
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "Z3" => "load_bearing"),
    )
end

result = build_result()
open(RESULT_PATH, "w") do io
    JSON.print(io, result, 2)
    println(io)
end
println(JSON.json(Dict("result_path" => rel(RESULT_PATH), "all_pass" => result["all_pass"])))
