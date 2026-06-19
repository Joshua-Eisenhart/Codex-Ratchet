#!/usr/bin/env julia
# Julia Graphs lane for gcm_constraint_carve_v0.

using Dates
using Graphs
using JSON
using SHA

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "gcm_constraint_carve_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const GRID_VALUES = [-1.0, -0.5, 0.0, 0.5, 1.0]
const EXPECTED_CANDIDATE_COUNT = 125
const EXPECTED_DENSITY_COUNT = 33
const EXPECTED_SURVIVOR_COUNT = 8
const EXPECTED_QUOTIENT_CLASS_COUNT = 4

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

function order_gap(coord)::Float64
    x, y, z = coord
    left = (scaled(0.5 * x), scaled(y))
    right = (scaled(0.5 * x), scaled(0.5 * y))
    return sqrt(sum((left[i] - right[i])^2 for i in 1:2))
end

persistence_order_ok(coord)::Bool = order_gap(coord) >= 0.5

function residency_signature(coord)::String
    x, _y, z = coord
    if x == 0 && z == 0
        return "zero_active_probe_boundary_control"
    end
    if abs(z) > abs(x)
        return "dissipative_open_legal_zone"
    elseif abs(x) > abs(z)
        return "hamiltonian_circulation_legal_zone"
    end
    return "ambiguous_boundary_rejected_by_G7_pin"
end

function residency_ok(coord)::Bool
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

function passes_all(row)::Bool
    coord = row["coord"]
    return density_ok(coord) && active_probe_nonzero(coord) && persistence_order_ok(coord) && residency_ok(coord)
end

function target_keys(row)
    x, y, z = row["coord"]
    keys = [("hidden_probe_flip", (scaled(x), scaled(-y), scaled(z)))]
    if row["residency_signature"] == "hamiltonian_circulation_legal_zone"
        push!(keys, ("circulation_half_turn", (scaled(-x), scaled(-y), scaled(z))))
    end
    return keys
end

function build_survivors()
    survivors = Any[]
    density_count = 0
    for row in candidates()
        coord = row["coord"]
        if density_ok(coord)
            density_count += 1
        end
        if passes_all(row)
            row = copy(row)
            row["survivor_id"] = length(survivors)
            row["probe_signature"] = collect(probe_signature(coord))
            row["order_gap"] = order_gap(coord)
            row["residency_signature"] = residency_signature(coord)
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
            "region_signature" => members[1]["residency_signature"],
        ))
    end
    return classes
end

function component_receipt(survivors, classes)
    key_to_sid = Dict{Tuple{Int, Int, Int}, Int}()
    for row in survivors
        key_to_sid[Tuple(row["coord_scaled"])] = row["survivor_id"]
    end
    g = SimpleGraph(length(survivors))
    edges = Any[]
    for row in survivors
        src = row["survivor_id"]
        for (update_name, key) in target_keys(row)
            if haskey(key_to_sid, key)
                dst = key_to_sid[key]
                add_edge!(g, src + 1, dst + 1)
                push!(edges, Dict("src" => src, "dst" => dst, "update" => update_name))
            end
        end
    end
    comps = [sort([v - 1 for v in comp]) for comp in connected_components(g)]
    return Dict(
        "node_count" => nv(g),
        "edge_count" => ne(g),
        "component_count" => length(comps),
        "components" => comps,
        "edges" => edges,
        "class_count" => length(classes),
    )
end

function main()::Int
    mkpath(RESULT_DIR)
    survivors, density_count = build_survivors()
    classes = quotient_classes(survivors)
    components = component_receipt(survivors, classes)
    all_pass = (
        length(candidates()) == EXPECTED_CANDIDATE_COUNT &&
        density_count == EXPECTED_DENSITY_COUNT &&
        length(survivors) == EXPECTED_SURVIVOR_COUNT &&
        length(classes) == EXPECTED_QUOTIENT_CLASS_COUNT &&
        components["component_count"] == 3
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
            "Graphs" => "SimpleGraph/add_edge!/connected_components over survivor adjacency"
        ),
        "reads_peer_result" => false,
        "candidate_count" => length(candidates()),
        "density_count" => density_count,
        "survivor_count" => length(survivors),
        "quotient_class_count" => length(classes),
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
