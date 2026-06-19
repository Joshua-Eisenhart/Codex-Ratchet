#!/usr/bin/env julia
# Julia Graphs/Z3 leg for basin_rc_transition_graph_v0.

using Dates
using Graphs
using JSON
using LinearAlgebra
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "basin_rc_transition_graph_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const GRID_VALUES = [-1.0, -0.5, 0.0, 0.5, 1.0]
const TERRAIN_H = 0.5
const BASE_TERRAINS = ["Se_Funnel_L", "Ni_Pit_L", "Ni_Source_R", "Ne_Spiral_R"]
const BASE_OPERATORS = ["D_z", "R_x"]

const S5_PATH = joinpath(ROOT, "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json")
const S4_PATH = joinpath(ROOT, "system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json")

const TOOL_MANIFEST = Dict(
    "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing directed graph construction and SCC computation"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing terminal-class no-exit proof over computed edge/component rows"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive matrix exponential for terrain flow rows"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive parent loading, timestamping, and hashing"),
)
const TOOL_INTEGRATION_DEPTH = Dict(
    "Graphs" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON/Dates/SHA" => "supportive",
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

function stable_sha(value)::String
    bytes2hex(sha256(collect(codeunits(JSON.json(value)))))
end

function load_json(path::String)
    JSON.parsefile(path)
end

function parse_value(value)::Float64
    if value isa Number
        return Float64(value)
    end
    return Float64(eval(Meta.parse(String(value))))
end

function parse_matrix(rows)::Matrix{Float64}
    out = zeros(Float64, length(rows), length(rows[1]))
    for i in eachindex(rows)
        for j in eachindex(rows[i])
            out[i, j] = parse_value(rows[i][j])
        end
    end
    out
end

parse_vector(values)::Vector{Float64} = [parse_value(v) for v in values]

function state_cells(root_off::Bool=false)
    cells = Vector{Dict{String, Any}}()
    for x in GRID_VALUES, y in GRID_VALUES, z in GRID_VALUES
        r2 = x*x + y*y + z*z
        if root_off || r2 <= 1.0 + 1.0e-12
            push!(cells, Dict(
                "cell_id" => length(cells),
                "coord" => [x, y, z],
                "radius_squared" => round(r2; digits=12),
                "Adm_C" => r2 <= 1.0 + 1.0e-12,
                "conditioned_shell_member" => abs(z - 0.5) <= 1.0e-12 && abs((x*x + y*y) - 0.5) <= 1.0e-12,
            ))
        end
    end
    cells
end

function nearest_cell(point::Vector{Float64}, cells)::Int
    best = 0
    best_d2 = Inf
    for cell in cells
        coord = Vector{Float64}(cell["coord"])
        d2 = sum((point .- coord).^2)
        cid = Int(cell["cell_id"])
        if d2 < best_d2 - 1.0e-12 || (abs(d2 - best_d2) <= 1.0e-12 && cid < best)
            best = cid
            best_d2 = d2
        end
    end
    best
end

function terrain_affine(row)
    a = parse_matrix(row["pinned"]["A"])
    b = parse_vector(row["pinned"]["b"])
    aug = zeros(Float64, 4, 4)
    aug[1:3, 1:3] .= a
    aug[1:3, 4] .= b
    flow = exp(TERRAIN_H .* aug)
    return flow[1:3, 1:3], flow[1:3, 4]
end

function operator_affine(row)
    parse_matrix(row["pinned"]["M"]), parse_vector(row["pinned"]["c"])
end

function load_generators()
    s5 = load_json(S5_PATH)
    s4 = load_json(S4_PATH)
    generators = Any[]
    for name in BASE_TERRAINS
        m, c = terrain_affine(s5["bloch_generator_table"][name])
        push!(generators, Dict("name" => name, "kind" => "S5_terrain_flow", "h" => TERRAIN_H, "M" => m, "c" => c))
    end
    for name in BASE_OPERATORS
        m, c = operator_affine(s4["affine_channel_table"][name])
        push!(generators, Dict("name" => name, "kind" => "S4_operator_channel", "h" => "one_pinned_channel", "M" => m, "c" => c))
    end
    generators
end

function build_graph(generators)
    cells = state_cells(false)
    g = Graphs.SimpleDiGraph(length(cells))
    edge_rows = Any[]
    for cell in cells
        src = Int(cell["cell_id"])
        coord = Vector{Float64}(cell["coord"])
        for gen in generators
            image = Vector{Float64}(gen["M"] * coord + gen["c"])
            dst = nearest_cell(image, cells)
            Graphs.add_edge!(g, src + 1, dst + 1)
            push!(edge_rows, Dict("src" => src, "dst" => dst, "generator" => gen["name"]))
        end
    end
    comps_1 = Graphs.strongly_connected_components(g)
    comps = [sort([Int(v) - 1 for v in comp]) for comp in comps_1]
    sort!(comps, by = c -> (minimum(c), length(c)))
    comp_id = Dict{Int, Int}()
    for (idx0, comp) in enumerate(comps)
        for cell_id in comp
            comp_id[cell_id] = idx0 - 1
        end
    end
    class_rows = Any[]
    terminal_ids = Int[]
    for (idx0, comp) in enumerate(comps)
        cid = idx0 - 1
        comp_set = Set(comp)
        outgoing = Any[row for row in edge_rows if (row["src"] in comp_set) && !(row["dst"] in comp_set)]
        total = length(comp) * length(generators)
        internal = total - length(outgoing)
        terminal = isempty(outgoing)
        if terminal
            push!(terminal_ids, cid)
        end
        push!(class_rows, Dict(
            "class_id" => cid,
            "cells" => comp,
            "size" => length(comp),
            "terminal_closed" => terminal,
            "absent_exit_proof" => Dict("outgoing_edge_count" => length(outgoing), "checked_edge_count" => total, "no_exit" => terminal),
            "internal_transition_fraction" => round(internal / total; digits=12),
            "escape_transition_fraction" => round(length(outgoing) / total; digits=12),
            "leaky" => !isempty(outgoing),
            "outgoing_edges" => outgoing,
        ))
    end
    terminal_cells = Set{Int}()
    for tid in terminal_ids
        for cell_id in class_rows[tid + 1]["cells"]
            push!(terminal_cells, cell_id)
        end
    end
    boundary = sort(unique([
        row["src"] for row in edge_rows
        if comp_id[row["src"]] != comp_id[row["dst"]] || row["dst"] in terminal_cells
    ]))
    Dict(
        "cells" => cells,
        "edge_count" => length(edge_rows),
        "transition_edges" => edge_rows,
        "scc_count" => length(class_rows),
        "communicating_classes" => class_rows,
        "terminal_class_ids" => terminal_ids,
        "terminal_classes" => [class_rows[id + 1] for id in terminal_ids],
        "boundary_cells" => boundary,
        "component_id_by_cell" => Dict(string(k) => v for (k, v) in comp_id),
        "partition_signature" => Dict(
            "state_count" => length(cells),
            "scc_count" => length(class_rows),
            "terminal_sizes" => sort([class_rows[id + 1]["size"] for id in terminal_ids]),
            "class_sizes" => sort([row["size"] for row in class_rows]),
            "boundary_count" => length(boundary),
        ),
    )
end

function z3_or(terms::Vector{Z3.Expr})
    isempty(terms) && return Z3.BoolVal(false)
    length(terms) == 1 && return terms[1]
    return Z3.Or(terms)
end

function z3_no_exit(graph; erased_flip::Bool=false)::String
    terminal_ids = Set(graph["terminal_class_ids"])
    edge_rows = graph["transition_edges"]
    comp = Dict(parse(Int, k) => Int(v) for (k, v) in graph["component_id_by_cell"])
    terminal_edge_index = findfirst(row -> comp[row["src"]] in terminal_ids, edge_rows)
    outside_comp = first(comp[row["src"]] for row in edge_rows if comp[row["src"]] != comp[edge_rows[terminal_edge_index]["src"]])
    solver = Z3.Solver()
    terms = Z3.Expr[]
    for (idx0, row) in enumerate(edge_rows)
        idx = idx0 - 1
        src_terminal = Z3.IntVar("julia_src_terminal_$(idx)")
        src_comp = Z3.IntVar("julia_src_comp_$(idx)")
        dst_comp = Z3.IntVar("julia_dst_comp_$(idx)")
        Z3.add(solver, src_terminal == Z3.IntVal((comp[row["src"]] in terminal_ids) ? 1 : 0))
        Z3.add(solver, src_comp == Z3.IntVal(comp[row["src"]]))
        dst_value = erased_flip && idx0 == terminal_edge_index ? outside_comp : comp[row["dst"]]
        Z3.add(solver, dst_comp == Z3.IntVal(dst_value))
        push!(terms, Z3.And(Z3.Expr[src_terminal == Z3.IntVal(1), Z3.Not(src_comp == dst_comp)]))
    end
    Z3.add(solver, z3_or(terms))
    string(Z3.check(solver))
end

function build_result()
    generators = load_generators()
    graph = build_graph(generators)
    z3_verdict = z3_no_exit(graph)
    z3_erased = z3_no_exit(graph; erased_flip=true)
    graph_hash = stable_sha(Dict("edges" => graph["transition_edges"], "classes" => graph["communicating_classes"]))
    capability = [
        Dict("receipt_id" => "julia_Graphs_graph_partition", "tool" => "Graphs", "computed_what" => "finite R_C directed graph and SCC partition", "status" => "used"),
        Dict("receipt_id" => "julia_Z3_no_exit", "tool" => "Z3", "computed_what" => "terminal no-exit proof with erased flip", "status" => "used"),
    ]
    tool_calls = [
        Dict(
            "receipt_id" => "julia_Graphs_graph_partition",
            "tool" => "Graphs",
            "qualified_api/function" => "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.strongly_connected_components",
            "input_object" => "finite admitted Bloch cells and generator-labelled transition rows",
            "output_object" => "communicating classes and terminal classes",
            "positive_case" => "base R_C graph computes a closed terminal class",
            "negative/erased_control" => "Python mirror controls change partitions under root-off and generator erasures",
            "boundary_case" => "leaky nonterminal SCC retained as nonterminal",
            "demotion_condition" => "demote if SCCs are not computed from explicit edges",
            "gates" => ["basin_partition", "terminal_class", "all_pass"],
        ),
        Dict(
            "receipt_id" => "julia_Z3_no_exit",
            "tool" => "Z3",
            "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
            "input_object" => "computed edge rows with src/dst component ids and terminal flags",
            "output_object" => "UNSAT no-exit positive proof and SAT erased destination-component flip",
            "positive_case" => "no terminal source edge exits its terminal component",
            "negative/erased_control" => "one terminal edge destination component is flipped outside the terminal class",
            "boundary_case" => "nonterminal class may leak without becoming terminal",
            "demotion_condition" => "demote if solver checks only a precomputed no_exit boolean",
            "gates" => ["proof", "absent_exit_proof", "all_pass"],
        ),
    ]
    all_pass = (
        length(graph["cells"]) == 33 &&
        length(graph["terminal_classes"]) == 1 &&
        graph["terminal_classes"][1]["absent_exit_proof"]["no_exit"] == true &&
        z3_verdict == "unsat" &&
        z3_erased == "sat"
    )
    Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "object_id" => "$(SIM_ID)_$(ENGINE)",
        "engine" => ENGINE,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => false,
        "generated_at" => now_z(),
        "seed_ledger" => Dict("rng" => "none", "deterministic_tie_break" => "cell_id_ascending"),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "julia_project" => joinpath(ROOT, "system_v5", "julia_carrier", "Project.toml"),
        "packages_used" => ["Graphs", "Z3", "LinearAlgebra", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "package_versions" => Dict("julia" => string(VERSION), "Graphs" => string(pkgversion(Graphs)), "Z3" => string(pkgversion(Z3))),
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "capability_receipts" => capability,
        "tool_calls" => tool_calls,
        "one_to_one_tool_calls" => Dict("pass" => [row["receipt_id"] for row in capability] == [row["receipt_id"] for row in tool_calls]),
        "transition_graph" => graph,
        "crossover_proofs" => Dict(
            "julia_z3" => Dict(
                "ran" => true,
                "load_bearing" => true,
                "verdict" => z3_verdict,
                "erased_flip_verdict" => z3_erased,
                "proof_row" => Dict(
                    "edge_row_count" => length(graph["transition_edges"]),
                    "encoding" => "bind src_terminal, src_comp, dst_comp per computed edge; assert existence of a terminal exit",
                    "asserted_precomputed_boolean" => false,
                ),
            ),
        ),
        "partition_signature_sha256" => stable_sha(graph["partition_signature"]),
        "transition_graph_sha256" => graph_hash,
        "all_pass" => all_pass,
    )
end

function main()
    mkpath(RESULT_DIR)
    payload = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => payload["all_pass"], "result_path" => rel(RESULT_PATH))))
    return payload["all_pass"] ? 0 : 1
end

exit(main())
