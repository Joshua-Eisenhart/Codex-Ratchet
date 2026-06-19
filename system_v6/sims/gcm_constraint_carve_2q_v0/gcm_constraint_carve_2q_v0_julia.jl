#!/usr/bin/env julia
# Julia Graphs lane for gcm_constraint_carve_2q_v0.

using Dates
using Graphs
using JSON
using SHA

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "gcm_constraint_carve_2q_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const GRID_VALUES = [-1.0, -0.5, 0.0, 0.5, 1.0]
const EXPECTED_CANDIDATE_COUNT = 15783
const EXPECTED_DENSITY_COUNT = 1167
const EXPECTED_SURVIVOR_COUNT = 544
const EXPECTED_QUOTIENT_CLASS_COUNT = 8
const EXPECTED_ENTANGLED_SURVIVOR_COUNT = 16
const EXPECTED_MCT_SURVIVOR_COUNT = 272
const EXPECTED_ONE_Q_SURVIVOR_COUNT = 16

now_z()::String = Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
rel(path::String)::String = replace(relpath(path, ROOT), "\\" => "/")

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

scaled(v::Float64)::Int = Int(round(2.0 * v))
density_ok(coord)::Bool = sum(v * v for v in coord) <= 1.0 + 1.0e-12
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

function first_active_positive(coord)::Bool
    x, _y, z = coord
    if x != 0
        return x > 0
    end
    if z != 0
        return z > 0
    end
    return false
end

function bell_eigenvalues(corr)
    cx, cy, cz = corr
    return [
        (1 + cx - cy + cz) / 4,
        (1 - cx + cy + cz) / 4,
        (1 + cx + cy - cz) / 4,
        (1 - cx - cy - cz) / 4,
    ]
end

bell_valid(corr)::Bool = minimum(bell_eigenvalues(corr)) >= -1.0e-12
bell_entangled(corr)::Bool = bell_valid(corr) && maximum(bell_eigenvalues(corr)) > 0.5 + 1.0e-12

function grid_coords()
    rows = Any[]
    for x in GRID_VALUES, y in GRID_VALUES, z in GRID_VALUES
        push!(rows, (x, y, z))
    end
    return rows
end

function second_for_purification(first)
    r = sqrt(sum(v * v for v in first))
    return (0.0, 0.0, r)
end

function candidate_rows()
    grid = grid_coords()
    density_grid = [coord for coord in grid if density_ok(coord)]
    rows = Any[]
    for first in grid, second in grid
        push!(rows, Dict("candidate_id" => length(rows), "family" => "product_grid", "first" => first, "second" => second))
    end
    for corr in grid
        push!(rows, Dict("candidate_id" => length(rows), "family" => "bell_diagonal_grid", "first" => (0.0, 0.0, 0.0), "second" => (0.0, 0.0, 0.0), "corr" => corr))
    end
    for first in density_grid
        push!(rows, Dict("candidate_id" => length(rows), "family" => "purification_boundary", "first" => first, "second" => second_for_purification(first)))
    end
    return rows
end

function density_valid(row)::Bool
    family = row["family"]
    if family == "product_grid"
        return density_ok(row["first"]) && density_ok(row["second"])
    elseif family == "bell_diagonal_grid"
        return bell_valid(row["corr"])
    elseif family == "purification_boundary"
        return density_ok(row["first"])
    end
    error("unknown family")
end

function entangled(row)::Bool
    family = row["family"]
    if family == "product_grid"
        return false
    elseif family == "bell_diagonal_grid"
        return bell_entangled(row["corr"])
    elseif family == "purification_boundary"
        r2 = sum(v * v for v in row["first"])
        return r2 > 1.0e-12 && r2 < 1.0 - 1.0e-12
    end
    error("unknown family")
end

function passes_base(row)::Bool
    return density_valid(row) && active_probe_nonzero(row["first"]) && persistence_order_ok(row["first"])
end

function enrich_survivor!(row, survivor_id)
    row["survivor_id"] = survivor_id
    row["first_scaled"] = [scaled(v) for v in row["first"]]
    row["second_scaled"] = [scaled(v) for v in row["second"]]
    row["probe_signature"] = collect(probe_signature(row["first"]))
    row["entangled"] = entangled(row)
    return row
end

function survivors()
    rows = Any[]
    density_count = 0
    kill_counts = Dict{String, Int}()
    for row in candidate_rows()
        if density_valid(row)
            density_count += 1
        end
        if !density_valid(row)
            kill_counts["C1_finite_2q_density_carrier"] = get(kill_counts, "C1_finite_2q_density_carrier", 0) + 1
        elseif !active_probe_nonzero(row["first"])
            kill_counts["C2_probe_distinguishability_xz_local_adapter_pin"] = get(kill_counts, "C2_probe_distinguishability_xz_local_adapter_pin", 0) + 1
        elseif !persistence_order_ok(row["first"])
            kill_counts["C3_persistence_n01_order_gap"] = get(kill_counts, "C3_persistence_n01_order_gap", 0) + 1
        else
            push!(rows, enrich_survivor!(copy(row), length(rows)))
        end
    end
    return rows, density_count, kill_counts
end

function quotient_classes(rows)
    buckets = Dict{Tuple{Int, Int}, Vector{Any}}()
    for row in rows
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
        ))
    end
    return classes
end

function key_for(row)
    return string(row["family"], "|", join(row["first_scaled"], ","), "|", join(row["second_scaled"], ","))
end

function target_keys(row)
    x, y, z = row["first"]
    family = row["family"]
    second = row["second_scaled"]
    rows = [("hidden_probe_flip_first_qubit", string(family, "|", join([scaled(x), scaled(-y), scaled(z)], ","), "|", join(second, ",")))]
    if z == 0 && x != 0
        push!(rows, ("x_reflection_at_z_zero_first_qubit", string(family, "|", join([scaled(-x), scaled(-y), scaled(z)], ","), "|", join(second, ","))))
    end
    if x == 0 && z != 0
        push!(rows, ("z_reflection_at_x_zero_first_qubit", string(family, "|", join([scaled(x), scaled(-y), scaled(-z)], ","), "|", join(second, ","))))
    end
    return rows
end

function component_receipt(rows, classes)
    key_to_sid = Dict{String, Int}()
    for row in rows
        key_to_sid[key_for(row)] = row["survivor_id"]
    end
    class_for_survivor = Dict{Int, String}()
    for qrow in classes
        for sid in qrow["member_survivor_ids"]
            class_for_survivor[sid] = qrow["class_id"]
        end
    end
    g = SimpleGraph(length(rows))
    q_edges = Set{Tuple{String, String, String}}()
    for row in rows
        src = row["survivor_id"]
        for (update_name, target_key) in target_keys(row)
            if haskey(key_to_sid, target_key)
                dst = key_to_sid[target_key]
                add_edge!(g, src + 1, dst + 1)
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
        "component_count" => length(comps),
        "quotient_component_count" => length(q_comps),
        "node_count" => nv(g),
        "edge_count" => ne(g),
    )
end

function main()::Int
    mkpath(RESULT_DIR)
    rows, density_count, kill_counts = survivors()
    classes = quotient_classes(rows)
    components = component_receipt(rows, classes)
    entangled_count = count(row -> row["entangled"], rows)
    mct_count = count(row -> first_active_positive(row["first"]), rows)
    one_q_embed_count = count(row -> row["family"] == "product_grid" && row["second_scaled"] == [0, 0, 2], rows)
    all_pass = (
        length(candidate_rows()) == EXPECTED_CANDIDATE_COUNT &&
        density_count == EXPECTED_DENSITY_COUNT &&
        length(rows) == EXPECTED_SURVIVOR_COUNT &&
        length(classes) == EXPECTED_QUOTIENT_CLASS_COUNT &&
        entangled_count == EXPECTED_ENTANGLED_SURVIVOR_COUNT &&
        mct_count == EXPECTED_MCT_SURVIVOR_COUNT &&
        one_q_embed_count == EXPECTED_ONE_Q_SURVIVOR_COUNT
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
            "Graphs" => "SimpleGraph/add_edge!/connected_components over 2Q survivor and quotient adjacency"
        ),
        "reads_peer_result" => false,
        "candidate_count" => length(candidate_rows()),
        "density_count" => density_count,
        "survivor_count" => length(rows),
        "quotient_class_count" => length(classes),
        "component_count" => components["component_count"],
        "quotient_component_count" => components["quotient_component_count"],
        "entangled_survivor_count" => entangled_count,
        "embedded_1q_count" => one_q_embed_count,
        "mct_survivor_count" => mct_count,
        "kill_counts_by_constraint" => kill_counts,
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

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end
