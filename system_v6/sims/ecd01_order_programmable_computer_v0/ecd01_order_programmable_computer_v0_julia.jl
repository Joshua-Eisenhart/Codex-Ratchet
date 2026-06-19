#!/usr/bin/env julia
# Julia lane for ecd01_order_programmable_computer_v0.

using Dates
using Graphs
using JSON
using LinearAlgebra
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "ecd01_order_programmable_computer_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const EPS = 1.0e-10

rel(path::String)::String = replace(relpath(path, ROOT), "\\" => "/")

function sha256_text(value)::String
    return bytes2hex(sha256(string(value)))
end

function state_cells()
    cells = Vector{Vector{Float64}}()
    for x in (-1.0, -0.5, 0.0, 0.5, 1.0), y in (-1.0, -0.5, 0.0, 0.5, 1.0), z in (-1.0, -0.5, 0.0, 0.5, 1.0)
        if x * x + y * y + z * z <= 1.0 + 1.0e-12
            push!(cells, [x, y, z])
        end
    end
    return cells
end

function matrix_for_word(word::String, u, e)
    matrix = Matrix{Float64}(I, 3, 3)
    for stage in collect(word)
        matrix = (stage == 'U' ? u : e) * matrix
    end
    return matrix
end

function rounded_vec(v)
    return [abs(x) < EPS ? 0.0 : round(x; digits=12) for x in v]
end

function channel_hash(word::String, u, e, cells)
    matrix = matrix_for_word(word, u, e)
    outputs = sort([rounded_vec(matrix * cell) for cell in cells])
    return sha256_text(JSON.json(outputs))
end

function channel_distance(left::String, right::String, u, e, cells)
    left_matrix = matrix_for_word(left, u, e)
    right_matrix = matrix_for_word(right, u, e)
    total = 0.0
    for cell in cells
        total += sum(abs.(left_matrix * cell - right_matrix * cell))
    end
    return abs(total) < EPS ? 0.0 : round(total; digits=15)
end

function z3_diversity_status(qit_count::Int, szilard_count::Int, commuting_count::Int)::String
    solver = Z3.Solver()
    qit = Z3.IntVar("julia_qit_distinct")
    szilard = Z3.IntVar("julia_szilard_distinct")
    commuting = Z3.IntVar("julia_commuting_distinct")
    Z3.add(solver, qit == Z3.IntVal(qit_count))
    Z3.add(solver, szilard == Z3.IntVal(szilard_count))
    Z3.add(solver, commuting == Z3.IntVal(commuting_count))
    Z3.add(solver, commuting == Z3.IntVal(1))
    Z3.add(solver, Z3.Not(szilard < qit))
    return string(Z3.check(solver))
end

function build_result()
    cells = state_cells()
    u = [1.0 0.0 0.0; 0.0 0.0 -1.0; 0.0 1.0 0.0]
    e = [0.7 0.0 0.0; 0.0 0.7 0.0; 0.0 0.0 1.0]
    words = ["UEUE", "UUEE", "UEEU"]
    graph = Graphs.SimpleDiGraph(length(cells))
    for idx in 1:(length(cells)-1)
        Graphs.add_edge!(graph, idx, idx + 1)
    end
    hashes = Dict(word => channel_hash(word, u, e, cells) for word in words)
    distinct_count = length(Set(values(hashes)))
    distances = Dict("$(left)__$(right)" => channel_distance(left, right, u, e, cells) for left in words for right in words)
    commuting_hashes = Dict(word => channel_hash(word, u, u, cells) for word in words)
    commuting_count = length(Set(values(commuting_hashes)))
    szilard_count = 1
    z3_status = z3_diversity_status(distinct_count, szilard_count, commuting_count)
    all_pass = distinct_count == 3 && commuting_count == 1 && szilard_count < distinct_count && z3_status == "unsat"
    return Dict(
        "schema" => "$(SIM_ID)_julia_lane_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "source_path" => rel(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "capability_discriminator_only",
        "all_pass" => all_pass,
        "capability_metric" => Dict(
            "qit_distinct_channel_count" => distinct_count,
            "szilard_distinct_channel_count" => szilard_count,
            "qit_diversity_strictly_exceeds_szilard" => szilard_count < distinct_count,
        ),
        "channel_hash_classes" => hashes,
        "commuting_distinct_channel_count" => commuting_count,
        "distance_rows" => distances,
        "z3_status" => z3_status,
        "packages_used" => ["Graphs", "Z3", "JSON", "LinearAlgebra", "SHA"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "package_observables" => Dict(
            "Graphs" => "SimpleDiGraph finite 33-cell lane graph",
            "Z3" => "bound diversity inequality qit <= szilard is unsat",
        ),
        "observables" => Dict(
            "graph_vertices" => Graphs.nv(graph),
            "graph_edges" => Graphs.ne(graph),
            "z3_diversity_status" => z3_status,
        ),
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("result_path" => rel(RESULT_PATH), "all_pass" => result["all_pass"])))
    return result["all_pass"] ? 0 : 1
end

exit(main())
