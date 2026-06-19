#!/usr/bin/env julia
# Julia Graphs/Z3 reference lane for manifold_super_sim_v0.

using Dates
using Graphs
using JSON
using LinearAlgebra
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "manifold_super_sim_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const S5_PATH = joinpath(ROOT, "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json")
const S4_PATH = joinpath(ROOT, "system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json")

const GRID_VALUES = [-1.0, -0.5, 0.0, 0.5, 1.0]
const TERRAIN_H = 0.5
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const G0_NAMES = ["Se_Funnel_L", "Ni_Pit_L", "Ni_Source_R", "Ne_Spiral_R", "D_z", "R_x"]
const G1_NAMES = ["R_x", "R_z", "Ne_Spiral_R", "Ne_Vortex_L"]
const EXPECTED = Dict("G0" => 1, "G1" => 3)

function now_z()::String
    Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
end

rel(path::String)::String = replace(relpath(path, ROOT), "\\" => "/")

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function stable_sha(value)::String
    bytes2hex(sha256(collect(codeunits(JSON.json(value)))))
end

function parse_value(value)::Float64
    value isa Number && return Float64(value)
    return Float64(eval(Meta.parse(String(value))))
end

function parse_matrix(rows)::Matrix{Float64}
    out = zeros(Float64, length(rows), length(rows[1]))
    for i in eachindex(rows), j in eachindex(rows[i])
        out[i, j] = parse_value(rows[i][j])
    end
    out
end

parse_vector(values)::Vector{Float64} = [parse_value(v) for v in values]

function state_cells()
    cells = Vector{Dict{String, Any}}()
    for x in GRID_VALUES, y in GRID_VALUES, z in GRID_VALUES
        r2 = x*x + y*y + z*z
        if r2 <= 1.0 + 1.0e-12
            push!(cells, Dict("cell_id" => length(cells), "coord" => [x, y, z], "radius_squared" => round(r2; digits=12), "Adm_C" => true))
        end
    end
    cells
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

operator_affine(row) = (parse_matrix(row["pinned"]["M"]), parse_vector(row["pinned"]["c"]))

function load_generators()
    s5 = JSON.parsefile(S5_PATH)
    s4 = JSON.parsefile(S4_PATH)
    by_name = Dict{String, Any}()
    for name in sort(collect(keys(s5["bloch_generator_table"])))
        m, c = terrain_affine(s5["bloch_generator_table"][name])
        by_name[name] = Dict("name" => name, "kind" => "S5_terrain_flow", "h" => TERRAIN_H, "M" => m, "c" => c)
    end
    for name in sort(collect(keys(s4["affine_channel_table"])))
        m, c = operator_affine(s4["affine_channel_table"][name])
        by_name[name] = Dict("name" => name, "kind" => "S4_operator_channel", "h" => "one_pinned_channel", "M" => m, "c" => c)
    end
    by_name
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

function build_graph(generators)
    cells = state_cells()
    graph = Graphs.SimpleDiGraph(length(cells))
    edge_rows = Any[]
    for cell in cells
        src = Int(cell["cell_id"])
        coord = Vector{Float64}(cell["coord"])
        for gen in generators
            image = Vector{Float64}(gen["M"] * coord + gen["c"])
            dst = nearest_cell(image, cells)
            Graphs.add_edge!(graph, src + 1, dst + 1)
            push!(edge_rows, Dict("src" => src, "dst" => dst, "generator" => gen["name"]))
        end
    end
    comps = [sort([Int(v) - 1 for v in comp]) for comp in Graphs.strongly_connected_components(graph)]
    sort!(comps, by = c -> (minimum(c), length(c)))
    comp_id = Dict{Int, Int}()
    for (idx, comp) in enumerate(comps), cell_id in comp
        comp_id[cell_id] = idx - 1
    end
    class_rows = Any[]
    terminal_ids = Int[]
    for (idx, comp) in enumerate(comps)
        cid = idx - 1
        comp_set = Set(comp)
        outgoing = Any[row for row in edge_rows if row["src"] in comp_set && !(row["dst"] in comp_set)]
        terminal = isempty(outgoing)
        terminal && push!(terminal_ids, cid)
        push!(class_rows, Dict("class_id" => cid, "cells" => comp, "size" => length(comp), "terminal_closed" => terminal))
    end
    basin_map = Dict{String, Any}()
    for tid in terminal_ids
        tset = Set(class_rows[tid + 1]["cells"])
        may = Set{Int}()
        must = Set{Int}(tset)
        for cell in cells
            src = Int(cell["cell_id"])
            if any(Graphs.has_path(graph, src + 1, target + 1) for target in tset)
                push!(may, src)
            end
        end
        changed = true
        while changed
            changed = false
            for cell in cells
                src = Int(cell["cell_id"])
                src in must && continue
                succ = Set(Int(row["dst"]) for row in edge_rows if row["src"] == src)
                if !isempty(succ) && issubset(succ, must)
                    push!(must, src)
                    changed = true
                end
            end
        end
        basin_map[string(tid)] = Dict(
            "terminal_class_id" => tid,
            "can_reach_terminal" => Dict("size" => length(may), "cells" => sort(collect(may))),
            "sure_basin_omega_containment" => Dict("size" => length(must), "cells" => sort(collect(must))),
        )
    end
    Dict(
        "state_count" => length(cells),
        "terminal_classes" => [class_rows[id + 1] for id in terminal_ids],
        "basin_map" => basin_map,
        "partition_signature" => Dict(
            "state_count" => length(cells),
            "scc_count" => length(class_rows),
            "terminal_sizes" => sort([class_rows[id + 1]["size"] for id in terminal_ids]),
            "class_sizes" => sort([row["size"] for row in class_rows]),
        ),
    )
end

function row_for(set_id::String, graph)
    basins = collect(values(graph["basin_map"]))
    Dict(
        "set_id" => set_id,
        "state_count" => graph["state_count"],
        "terminal_class_count" => length(graph["terminal_classes"]),
        "terminal_class_sizes" => sort([row["size"] for row in graph["terminal_classes"]]),
        "may_basin_sizes" => sort([row["can_reach_terminal"]["size"] for row in basins]),
        "must_basin_sizes" => sort([row["sure_basin_omega_containment"]["size"] for row in basins]),
        "partition_signature" => graph["partition_signature"],
    )
end

function z3_identity(rows; erased_flip=false)
    solver = Z3.Solver()
    terms = Z3.Expr[]
    for (idx, row) in enumerate(rows)
        actual = Z3.IntVar("super_julia_actual_$(idx)")
        expected = Z3.IntVar("super_julia_expected_$(idx)")
        Z3.add(solver, actual == Z3.IntVal(row["terminal_class_count"]))
        expected_value = EXPECTED[row["set_id"]]
        if erased_flip && row["set_id"] == "G1"
            expected_value -= 1
        end
        Z3.add(solver, expected == Z3.IntVal(expected_value))
        push!(terms, Z3.Not(actual == expected))
    end
    Z3.add(solver, length(terms) == 1 ? terms[1] : Z3.Or(terms))
    string(Z3.check(solver))
end

function source_backing_probe()
    g = Graphs.SimpleDiGraph(3)
    Graphs.add_edge!(g, 1, 2)
    Graphs.add_edge!(g, 2, 3)
    solver = Z3.Solver()
    x = Z3.IntVar("super_julia_probe_component_count")
    Z3.add(solver, x == Z3.IntVal(length(Graphs.strongly_connected_components(g))))
    Z3.add(solver, Z3.Not(x == Z3.IntVal(3)))
    Dict("Graphs_vertex_count" => Graphs.nv(g), "Z3_component_identity" => string(Z3.check(solver)))
end

function build_result()
    by_name = load_generators()
    g0_graph = build_graph([by_name[n] for n in G0_NAMES])
    g1_graph = build_graph([by_name[n] for n in G1_NAMES])
    rows = [row_for("G0", g0_graph), row_for("G1", g1_graph)]
    z3_verdict = z3_identity(rows)
    z3_erased = z3_identity(rows; erased_flip=true)
    all_pass = (
        rows[1]["terminal_class_sizes"] == [1] &&
        rows[2]["terminal_class_sizes"] == [1, 14, 18] &&
        rows[2]["may_basin_sizes"] == [1, 14, 18] &&
        rows[2]["must_basin_sizes"] == [1, 14, 18] &&
        z3_verdict == "unsat" &&
        z3_erased == "sat"
    )
    capability = [
        Dict("receipt_id" => "julia_Graphs_super_finite_partition", "tool" => "Graphs", "computed_what" => "G0/G1 finite graph partitions from pinned generators", "status" => "used"),
        Dict("receipt_id" => "julia_Z3_super_partition_identity", "tool" => "Z3", "computed_what" => "computed partition identity with erased flip", "status" => "used"),
    ]
    tool_calls = [
        Dict("receipt_id" => "julia_Graphs_super_finite_partition", "tool" => "Graphs", "qualified_api/function" => "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.strongly_connected_components", "load_bearing" => true),
        Dict("receipt_id" => "julia_Z3_super_partition_identity", "tool" => "Z3", "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check", "load_bearing" => true),
    ]
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
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "packages_used" => ["Graphs", "Z3", "LinearAlgebra", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "package_observables" => Dict(
            "Graphs" => "partition_rows.G0/G1 terminal_class_sizes from Graphs SCCs",
            "Z3" => "crossover_proofs.julia_z3 partition identity",
        ),
        "package_versions" => Dict("julia" => string(VERSION), "Graphs" => string(pkgversion(Graphs)), "Z3" => string(pkgversion(Z3))),
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite graph construction and SCC partition"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing partition identity proof"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "Z3" => "load_bearing"),
        "claim_path_tools" => ["Graphs", "Z3"],
        "capability_receipts" => capability,
        "tool_calls" => tool_calls,
        "one_to_one_tool_calls" => Dict("pass" => length(capability) == length(tool_calls)),
        "source_backing_probe" => source_backing_probe(),
        "partition_rows" => Dict("G0" => rows[1], "G1" => rows[2]),
        "crossover_proofs" => Dict(
            "julia_z3" => Dict(
                "ran" => true,
                "load_bearing" => true,
                "verdict" => z3_verdict,
                "erased_flip_verdict" => z3_erased,
                "proof_row" => Dict("asserted_precomputed_boolean" => false, "bound_rows" => rows),
            ),
        ),
        "all_pass" => all_pass,
        "super_julia_signature_sha256" => stable_sha(Dict("rows" => rows, "z3" => [z3_verdict, z3_erased])),
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
    payload["all_pass"] ? 0 : 1
end

exit(main())

