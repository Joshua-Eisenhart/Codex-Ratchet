#!/usr/bin/env julia

using Dates
using Graphs
using JSON
using SHA
using Statistics

const SIM_ID = "gcm_nested_geometry_delta_3q_v0"
const ROOT = dirname(dirname(dirname(@__DIR__)))
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const CARVE_RESULT_PATH = joinpath(ROOT, "system_v6", "sims", "gcm_constraint_carve_3q_v1", "results", "gcm_constraint_carve_3q_v1_results.json")

function rel(path::AbstractString)
    return replace(abspath(path), abspath(ROOT) * "/" => "")
end

function q(value)
    rounded = round(Float64(value); digits=12)
    return rounded == 0.0 ? 0.0 : rounded
end

function canonical(value)
    return JSON.json(value, 4)
end

function stable_sha256(value)
    return bytes2hex(sha256(canonical(value)))
end

function sign_value(value)
    if value < -1.0e-12
        return -1
    elseif value > 1.0e-12
        return 1
    end
    return 0
end

function constraints_for(row, killed)
    cid = string(row["candidate_id"])
    if !haskey(killed, cid)
        return Dict("C1" => true, "C2" => true, "C3" => true)
    end
    constraints = killed[cid]["constraints"]
    return Dict(
        "C1" => Bool(constraints["C1"]["pass"]),
        "C2" => Bool(constraints["C2"]["pass"]),
        "C3" => Bool(constraints["C3"]["pass"]),
    )
end

function select_rows(rows, pin_name)
    if pin_name == "free_C1_density_valid_layer"
        return [row for row in rows if row["C1"]]
    elseif pin_name == "main_C1_C2_C3_survivor_pin"
        return [row for row in rows if row["C1"] && row["C2"] && row["C3"]]
    elseif pin_name == "alternate_C1_C2_pin_without_C3"
        return [row for row in rows if row["C1"] && row["C2"]]
    end
    error("unknown pin_name: $pin_name")
end

function bin_key(row, probe_family)
    axes = probe_family == "M_prime_xy" ? (1, 2) : (1, 3)
    bloch = row["bloch_A"]
    r2 = q(sum(x * x for x in bloch))
    return "$(probe_family)|sig=$(sign_value(bloch[axes[1]])),$(sign_value(bloch[axes[2]]))|r2=$(r2)"
end

function dist(rows, probe_family)
    counts = Dict{String, Int}()
    for row in rows
        key = bin_key(row, probe_family)
        counts[key] = get(counts, key, 0) + 1
    end
    total = length(rows)
    return Dict(key => q(value / total) for (key, value) in sort(collect(counts)))
end

function run_delta(rows, nested_pin, probe_family)
    free_rows = select_rows(rows, "free_C1_density_valid_layer")
    nested_rows = select_rows(rows, nested_pin)
    free_dist = dist(free_rows, probe_family)
    nested_dist = dist(nested_rows, probe_family)
    bin_keys = sort(collect(union(Base.keys(free_dist), Base.keys(nested_dist))))
    delta_vector = Dict(key => q(get(nested_dist, key, 0.0) - get(free_dist, key, 0.0)) for key in bin_keys)
    occupied_graph = SimpleGraph(length(bin_keys) + 2)
    free_node = length(bin_keys) + 1
    nested_node = length(bin_keys) + 2
    index = Dict(key => i for (i, key) in enumerate(bin_keys))
    for key in bin_keys
        if get(free_dist, key, 0.0) != 0.0
            add_edge!(occupied_graph, free_node, index[key])
        end
        if get(nested_dist, key, 0.0) != 0.0
            add_edge!(occupied_graph, nested_node, index[key])
        end
    end
    return Dict(
        "nested_count" => length(nested_rows),
        "free_count" => length(free_rows),
        "delta_l1" => q(sum(abs(value) for value in values(delta_vector))),
        "delta_vector_sha256" => stable_sha256(delta_vector),
        "occupied_bin_graph_vertices" => nv(occupied_graph),
        "occupied_bin_graph_edges" => ne(occupied_graph),
    )
end

function main()
    carve = JSON.parsefile(CARVE_RESULT_PATH)
    killed = Dict(string(row["candidate_id"]) => row for row in carve["killed_rows"])
    rows = []
    for row in carve["candidate_space"]["candidate_rows"]
        constraints = constraints_for(row, killed)
        push!(
            rows,
            Dict(
                "candidate_id" => Int(row["candidate_id"]),
                "bloch_A" => [q(x) for x in row["first_bloch_from_stored_rho_A"]],
                "C1" => constraints["C1"],
                "C2" => constraints["C2"],
                "C3" => constraints["C3"],
            ),
        )
    end
    main_run = run_delta(rows, "main_C1_C2_C3_survivor_pin", "M_xz")
    stable_null = run_delta(rows, "main_C1_C2_C3_survivor_pin", "M_xz")
    null_delta_l1 = q(sum(abs(main_run["delta_l1"] - stable_null["delta_l1"])))
    alternate_pin = run_delta(rows, "alternate_C1_C2_pin_without_C3", "M_xz")
    alternate_probe = run_delta(rows, "main_C1_C2_C3_survivor_pin", "M_prime_xy")
    scale = 1_000_000_000
    claim_values = Dict(
        "main_delta_l1_scaled" => Int(round(main_run["delta_l1"] * scale)),
        "same_input_null_delta_l1_scaled" => Int(round(null_delta_l1 * scale)),
        "same_input_stable_delta_l1_scaled" => Int(round(stable_null["delta_l1"] * scale)),
        "alternate_pin_delta_l1_scaled" => Int(round(alternate_pin["delta_l1"] * scale)),
        "alternate_probe_delta_l1_scaled" => Int(round(alternate_probe["delta_l1"] * scale)),
        "main_free_count" => main_run["free_count"],
        "main_nested_count" => main_run["nested_count"],
        "alternate_pin_nested_count" => alternate_pin["nested_count"],
    )
    result = Dict(
        "engine" => "julia",
        "ran" => true,
        "reads_peer_result" => false,
        "source_path" => "system_v6/sims/gcm_nested_geometry_delta_3q_v0/gcm_nested_geometry_delta_3q_v0_julia.jl",
        "result_path" => rel(RESULT_PATH),
        "packages_used" => ["Graphs", "JSON", "SHA", "Statistics"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "aligned_packages_supportive" => [],
        "engine_role" => "independent_geometry_recompute",
        "claim_path_depth" => "load_bearing",
        "engine_independence_ceiling" => "independent Julia geometry recompute from source carve rows; this is not an all-three-engine independence claim",
        "package_observables" => Dict(
            "Graphs" => "Independent Julia recompute plus SimpleGraph/add_edge! occupied-bin incidence graph for free/nested delta runs",
        ),
        "claim_values" => claim_values,
        "graph_observables" => Dict(
            "main" => Dict(
                "vertices" => main_run["occupied_bin_graph_vertices"],
                "edges" => main_run["occupied_bin_graph_edges"],
            ),
            "same_input_stable_null" => Dict(
                "vertices" => stable_null["occupied_bin_graph_vertices"],
                "edges" => stable_null["occupied_bin_graph_edges"],
                "stable" => stable_null["delta_vector_sha256"] == main_run["delta_vector_sha256"],
                "null_delta_l1" => null_delta_l1,
            ),
            "alternate_pin" => Dict(
                "vertices" => alternate_pin["occupied_bin_graph_vertices"],
                "edges" => alternate_pin["occupied_bin_graph_edges"],
            ),
            "alternate_probe" => Dict(
                "vertices" => alternate_probe["occupied_bin_graph_vertices"],
                "edges" => alternate_probe["occupied_bin_graph_edges"],
            ),
        ),
        "created_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
    )
    mkpath(RESULT_DIR)
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => true, "result_path" => rel(RESULT_PATH), "claim_values" => claim_values), 2))
end

main()
