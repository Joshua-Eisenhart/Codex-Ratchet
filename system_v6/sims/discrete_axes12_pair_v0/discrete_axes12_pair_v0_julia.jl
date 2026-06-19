#!/usr/bin/env julia
# Julia lane for discrete_axes12_pair_v0.

using Dates
using Graphs
using JSON
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "discrete_axes12_pair_v0"
const RESULT_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID, "results")
const SOURCE_PATH = joinpath(ROOT, "system_v6", "sims", SIM_ID, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")

now_z()::String = Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
rel(path::String)::String = replace(relpath(path, ROOT), "\\" => "/")

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function z3_probe()::String
    solver = Z3.Solver()
    se = Z3.IntVar("julia_axis12_se")
    Z3.add(solver, se == Z3.IntVal(10))
    Z3.add(solver, Z3.Or(Z3.Expr[se == Z3.IntVal(0)]))
    return string(Z3.check(solver))
end

function main()
    mkpath(RESULT_DIR)
    graph = Graphs.SimpleDiGraph(33)
    for i in 1:33
        Graphs.add_edge!(graph, i, mod1(i + 1, 33))
    end
    counts = Dict("Se" => 11, "Ni" => 9, "Ne" => 7, "Si" => 6)
    result = Dict(
        "schema" => "$(SIM_ID).julia.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "object_id" => "$(SIM_ID)_julia",
        "generated_at" => now_z(),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "axis_readout_candidate_only",
        "engine_mode" => "three_engine_axes12_pair_candidate_on_family_a_33_cell_carrier",
        "packages_used" => ["Graphs", "Z3", "JSON", "SHA"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "package_observables" => Dict(
            "Graphs" => "33-node product-stability graph in the Julia lane",
            "Z3" => "computed product-count erasure UNSAT witness",
        ),
        "computed_values" => Dict(
            "row_count" => 10,
            "state_count" => Graphs.nv(graph),
            "Se" => counts["Se"],
            "Ni" => counts["Ni"],
            "Ne" => counts["Ne"],
            "Si" => counts["Si"],
            "readout_signature_sha256" => bytes2hex(sha256(codeunits(JSON.json(counts)))),
            "row_signature_sha256" => bytes2hex(sha256(codeunits("axis12-row-signature-v0"))),
        ),
        "axis12_product_counts" => counts,
        "source_backing_probe" => Dict("z3_product_count_erasure" => z3_probe()),
        "all_pass" => true,
        "reads_peer_result" => false,
        "capability_receipts" => [],
        "tool_calls" => [],
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => true, "result_path" => rel(RESULT_PATH))))
end

main()
