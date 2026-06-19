#!/usr/bin/env julia
# Julia Graphs lane for gcm_constraint_carve_v1.

using Dates
using Graphs
using JSON
using SHA

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "gcm_constraint_carve_v1"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const GRID_VALUES = [-1.0, -0.5, 0.0, 0.5, 1.0]
const EXPECTED_CANDIDATE_COUNT = 125
const EXPECTED_DENSITY_COUNT = 33
const EXPECTED_SURVIVOR_COUNT = 16
const EXPECTED_QUOTIENT_CLASS_COUNT = 8
const EXPECTED_V0_REGRESSION_SURVIVOR_COUNT = 8

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

scaled(v::Float64)::Int = Int(round(2.0 * v))
radius2(coord)::Float64 = sum(v * v for v in coord)
density_ok(coord)::Bool = radius2(coord) <= 1.0 + 1.0e-12
probe_signature(coord)::Tuple{Int, Int} = (scaled(coord[1]), scaled(coord[3]))
active_probe_nonzero(coord)::Bool = probe_signature(coord) != (0, 0)

function dz_after_rx(coord)
    x, y, z = coord
    return (0.5 * x, -0.5 * z, y)
end

function rx_after_dz(coord)
    x, y, z = coord
    return (0.5 * x, -z, 0.5 * y)
end

function order_gap(coord)::Float64
    left = probe_signature(dz_after_rx(coord))
    right = probe_signature(rx_after_dz(coord))
    return sqrt(sum((left[i] - right[i])^2 for i in 1:2))
end

persistence_order_ok(coord)::Bool = order_gap(coord) >= 0.5

function first_active_coordinate_positive(coord)::Bool
    x, _y, z = coord
    if x != 0
        return x > 0
    end
    if z != 0
        return z > 0
    end
    return false
end

function rejected_v0_c4(coord)::Bool
    x, _y, z = coord
    return !(x != 0 && z != 0)
end

function candidates()
    rows = Any[]
    for x in GRID_VALUES, y in GRID_VALUES, z in GRID_VALUES
        coord = [x, y, z]
        push!(rows, Dict(
            "candidate_id" => length(rows),
            "coord" => coord,
            "coord_scaled" => [scaled(x), scaled(y), scaled(z)],
            "radius_squared" => round(radius2(coord); digits=12),
        ))
    end
    return rows
end

function passes_v1(row)::Bool
    coord = row["coord"]
    return density_ok(coord) && active_probe_nonzero(coord) && persistence_order_ok(coord)
end

function passes_v0_regression(row)::Bool
    return passes_v1(row) && rejected_v0_c4(row["coord"])
end

function target_keys(row)
    x, y, z = row["coord"]
    keys = [("hidden_probe_flip", (scaled(x), scaled(-y), scaled(z)))]
    if z == 0 && x != 0
        push!(keys, ("x_reflection_at_z_zero", (scaled(-x), scaled(-y), scaled(z))))
    end
    if x == 0 && z != 0
        push!(keys, ("z_reflection_at_x_zero", (scaled(x), scaled(-y), scaled(-z))))
    end
    return keys
end

function build_survivors(predicate)
    survivors = Any[]
    density_count = 0
    for row in candidates()
        coord = row["coord"]
        if density_ok(coord)
            density_count += 1
        end
        if predicate(row)
            row = copy(row)
            row["survivor_id"] = length(survivors)
            row["probe_signature"] = collect(probe_signature(coord))
            row["order_gap"] = order_gap(coord)
            push!(survivors, row)
        end
    end
    return survivors, density_count
end

function quotient_classes(survivors)
    buckets = Dict{Tuple{Int, Int}, Vector{Any}}()
    for row in survivors
        key = Tuple(row["probe_signature"])
        if !haskey(buckets, key)
            buckets[key] = Any[]
        end
        push!(buckets[key], row)
    end
    classes = Any[]
    for key in sort(collect(keys(buckets)))
        members = sort(buckets[key], by = row -> row["survivor_id"])
        push!(classes, Dict(
            "class_id" => "Q$(length(classes))",
            "probe_signature" => collect(key),
            "member_survivor_ids" => [row["survivor_id"] for row in members],
            "member_candidate_ids" => [row["candidate_id"] for row in members],
        ))
    end
    return classes
end

function component_receipt(survivors, classes)
    key_to_sid = Dict{Tuple{Int, Int, Int}, Int}()
    for row in survivors
        key_to_sid[Tuple(row["coord_scaled"])] = row["survivor_id"]
    end
    class_for_survivor = Dict{Int, String}()
    for qrow in classes
        for sid in qrow["member_survivor_ids"]
            class_for_survivor[sid] = qrow["class_id"]
        end
    end
    g = SimpleGraph(length(survivors))
    q_edges = Set{Tuple{String, String, String}}()
    edges = Any[]
    for row in survivors
        src = row["survivor_id"]
        for (update_name, key) in target_keys(row)
            if haskey(key_to_sid, key)
                dst = key_to_sid[key]
                add_edge!(g, src + 1, dst + 1)
                push!(edges, Dict("src" => src, "dst" => dst, "update" => update_name))
                push!(q_edges, (class_for_survivor[src], class_for_survivor[dst], update_name))
            end
        end
    end
    comps = [sort([v - 1 for v in comp]) for comp in connected_components(g)]
    q_nodes = sort([row["class_id"] for row in classes])
    q_index = Dict(node => idx for (idx, node) in enumerate(q_nodes))
    qg = SimpleGraph(length(q_nodes))
    for (src, dst, _name) in q_edges
        add_edge!(qg, q_index[src], q_index[dst])
    end
    q_comps = [sort([q_nodes[v] for v in comp]) for comp in connected_components(qg)]
    return Dict(
        "node_count" => nv(g),
        "edge_count" => ne(g),
        "component_count" => length(comps),
        "components" => comps,
        "edges" => edges,
        "quotient_component_count" => length(q_comps),
        "quotient_components" => q_comps,
        "class_count" => length(classes),
    )
end

function main()::Int
    mkpath(RESULT_DIR)
    survivors, density_count = build_survivors(passes_v1)
    classes = quotient_classes(survivors)
    components = component_receipt(survivors, classes)
    v0_survivors, _ = build_survivors(passes_v0_regression)
    v0_classes = quotient_classes(v0_survivors)
    mct_survivors = [row for row in survivors if first_active_coordinate_positive(row["coord"])]
    mct_classes = quotient_classes(mct_survivors)
    all_pass = (
        length(candidates()) == EXPECTED_CANDIDATE_COUNT &&
        density_count == EXPECTED_DENSITY_COUNT &&
        length(survivors) == EXPECTED_SURVIVOR_COUNT &&
        length(classes) == EXPECTED_QUOTIENT_CLASS_COUNT &&
        length(v0_survivors) == EXPECTED_V0_REGRESSION_SURVIVOR_COUNT &&
        length(mct_survivors) == 8 &&
        length(mct_classes) == 4
    )
    result = Dict(
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
        "packages_used" => ["Graphs", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "package_observables" => Dict(
            "Graphs" => "SimpleGraph/add_edge!/connected_components over survivor and quotient adjacency"
        ),
        "reads_peer_result" => false,
        "candidate_count" => length(candidates()),
        "density_count" => density_count,
        "survivor_count" => length(survivors),
        "quotient_class_count" => length(classes),
        "component_count" => components["component_count"],
        "quotient_component_count" => components["quotient_component_count"],
        "v0_regression_survivor_count" => length(v0_survivors),
        "v0_regression_quotient_class_count" => length(v0_classes),
        "mct_survivor_count" => length(mct_survivors),
        "mct_quotient_class_count" => length(mct_classes),
        "component_receipt" => components,
        "all_pass" => all_pass,
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite graph components"),
            "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization and hashing")
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Graphs" => "load_bearing",
            "JSON/Dates/SHA" => "supportive"
        ),
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => all_pass, "result" => rel(RESULT_PATH))))
    return all_pass ? 0 : 1
end

exit(main())
