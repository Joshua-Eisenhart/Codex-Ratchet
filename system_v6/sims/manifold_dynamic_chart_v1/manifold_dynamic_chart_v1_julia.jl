#!/usr/bin/env julia
# Julia Graphs lane for manifold_dynamic_chart_v1.

using Dates
using Graphs
using JSON
using LinearAlgebra
using SHA

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "manifold_dynamic_chart_v1"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const S5_PATH = joinpath(ROOT, "system_v6", "sims", "geo_s5_terrain_flows_v0", "results", "geo_s5_terrain_flows_v0_envelope_results.json")
const S4_PATH = joinpath(ROOT, "system_v6", "sims", "geo_s4_operator_stage_v0", "results", "geo_s4_operator_stage_v0_envelope_results.json")
const EXPECTED_STATE_COUNT = 33
const EXPECTED_EDGE_COUNT = 198
const WINDOW_T = 16
const GRID_VALUES = [-1.0, -0.5, 0.0, 0.5, 1.0]
const STATE_SCALE = 2
const TERRAIN_H = 0.5

const TOOL_MANIFEST = Dict(
    "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite transition graph construction and SCC computation"),
    "JSON/Dates/SHA/LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive parent-row parsing, timestamping, hashing, and matrix exponential"),
)
const TOOL_INTEGRATION_DEPTH = Dict(
    "Graphs" => "load_bearing",
    "JSON/Dates/SHA/LinearAlgebra" => "supportive",
)

function now_z()::String
    Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
end

function rel(path::String)::String
    replace(relpath(path, ROOT), "\\" => "/")
end

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function parse_expr(value)::Float64
    if value isa Number
        return Float64(value)
    end
    text = replace(String(value), "//" => "/")
    return Float64(eval(Meta.parse(text)))
end

function parse_matrix(rows)
    [[parse_expr(value) for value in row] for row in rows]
end

function parse_vector(values)
    [parse_expr(value) for value in values]
end

function matvec(matrix, vector)
    [sum(matrix[i][j] * vector[j] for j in 1:3) for i in 1:3]
end

function add_vec(left, right)
    [left[i] + right[i] for i in 1:3]
end

function state_cells()
    cells = Any[]
    for x in GRID_VALUES, y in GRID_VALUES, z in GRID_VALUES
        r2 = x*x + y*y + z*z
        if r2 <= 1.0 + 1.0e-12
            conditioned = abs(z - 0.5) <= 1.0e-12 && abs((x*x + y*y) - 0.5) <= 1.0e-12
            push!(cells, Dict(
                "cell_id" => length(cells),
                "coord" => [x, y, z],
                "coord_scaled" => [Int(round(STATE_SCALE * x)), Int(round(STATE_SCALE * y)), Int(round(STATE_SCALE * z))],
                "radius_squared" => round(r2; digits=12),
                "Adm_C" => true,
                "conditioned_shell_member" => conditioned,
            ))
        end
    end
    return cells
end

function affine_from_terrain(row)
    a_mat = parse_matrix(row["pinned"]["A"])
    b_vec = parse_vector(row["pinned"]["b"])
    aug = zeros(Float64, 4, 4)
    for i in 1:3
        for j in 1:3
            aug[i, j] = a_mat[i][j]
        end
        aug[i, 4] = b_vec[i]
    end
    flow = exp(TERRAIN_H .* aug)
    matrix = [[flow[i, j] for j in 1:3] for i in 1:3]
    offset = [flow[i, 4] for i in 1:3]
    return matrix, offset
end

function affine_from_operator(row)
    parse_matrix(row["pinned"]["M"]), parse_vector(row["pinned"]["c"])
end

function load_generators()
    s5 = JSON.parsefile(S5_PATH)
    s4 = JSON.parsefile(S4_PATH)
    generators = Any[]
    for name in ["Se_Funnel_L", "Ni_Pit_L", "Ni_Source_R", "Ne_Spiral_R"]
        matrix, offset = affine_from_terrain(s5["bloch_generator_table"][name])
        push!(generators, Dict("name" => name, "kind" => "S5_terrain_flow", "M" => matrix, "c" => offset))
    end
    for name in ["D_z", "R_x"]
        matrix, offset = affine_from_operator(s4["affine_channel_table"][name])
        push!(generators, Dict("name" => name, "kind" => "S4_operator_channel", "M" => matrix, "c" => offset))
    end
    return generators
end

function nearest_cell(point, cells)::Int
    best_id = 0
    best_d2 = Inf
    for cell in cells
        coord = cell["coord"]
        d2 = sum((point[i] - coord[i])^2 for i in 1:3)
        cid = Int(cell["cell_id"])
        if d2 < best_d2 - 1.0e-12 || (abs(d2 - best_d2) <= 1.0e-12 && cid < best_id)
            best_id = cid
            best_d2 = d2
        end
    end
    return best_id
end

function build_transition_graph()
    cells = state_cells()
    generators = load_generators()
    graph = Graphs.SimpleDiGraph(length(cells))
    edges = Any[]
    for cell in cells
        src = Int(cell["cell_id"])
        for generator in generators
            image = add_vec(matvec(generator["M"], cell["coord"]), generator["c"])
            dst = nearest_cell(image, cells)
            Graphs.add_edge!(graph, src + 1, dst + 1)
            push!(edges, Dict("src" => src, "dst" => dst, "generator" => generator["name"]))
        end
    end
    comps_1 = Graphs.strongly_connected_components(graph)
    comps = [sort([Int(v) - 1 for v in comp]) for comp in comps_1]
    return cells, generators, edges, comps
end

function entropy_for_cell(cell)::Float64
    r = sqrt(sum(Float64(x)^2 for x in cell["coord"]))
    vals = [(1.0 + r) / 2.0, (1.0 - r) / 2.0]
    entropy = 0.0
    for value in vals
        if value > 0.0
            entropy -= value * log(value)
        end
    end
    return round(entropy; digits=12)
end

function run_schedule(edges, cells)
    lookup = Dict{Tuple{Int, String}, Int}()
    for edge in edges
        lookup[(Int(edge["src"]), String(edge["generator"]))] = Int(edge["dst"])
    end
    base_schedule = ["Ne_Spiral_R", "R_x", "D_z", "Se_Funnel_L"]
    schedule = [base_schedule[mod1(i, length(base_schedule))] for i in 1:WINDOW_T]
    current = collect(0:(length(cells)-1))
    cells_by_t = Any[copy(current)]
    entropy_by_t = Any[[entropy_for_cell(cells[cid + 1]) for cid in current]]
    changed_counts = Int[]
    for generator in schedule
        before = copy(current)
        current = [lookup[(cid, generator)] for cid in current]
        push!(changed_counts, sum(before[i] != current[i] for i in eachindex(current)))
        push!(cells_by_t, copy(current))
        push!(entropy_by_t, [entropy_for_cell(cells[cid + 1]) for cid in current])
    end
    return cells_by_t, entropy_by_t, changed_counts
end

function build_result()
    cells, generators, edges, comps = build_transition_graph()
    cells_by_t, entropy_by_t, changed_counts = run_schedule(edges, cells)
    all_pass = (
        length(cells) == EXPECTED_STATE_COUNT &&
        length(edges) == EXPECTED_EDGE_COUNT &&
        length(cells_by_t) == WINDOW_T + 1 &&
        sum(changed_counts) > 0
    )
    Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "generated_at" => now_z(),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "packages_used" => ["Graphs", "JSON", "Dates", "SHA", "LinearAlgebra"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "package_observables" => Dict("Graphs" => "Graphs.SimpleDiGraph/add_edge!/strongly_connected_components finite Family A transition graph"),
        "reads_peer_result" => false,
        "computed_values" => Dict(
            "state_count" => length(cells),
            "edge_count" => length(edges),
            "scc_count" => length(comps),
            "trajectory_T" => length(cells_by_t) - 1,
            "state_row_count" => length(cells) * length(cells_by_t),
            "cells_by_t" => cells_by_t,
            "entropy_by_t" => entropy_by_t,
            "changed_counts" => changed_counts,
        ),
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "all_pass" => all_pass,
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => result["all_pass"], "result" => rel(RESULT_PATH))))
    return result["all_pass"] ? 0 : 1
end

exit(main())
