#!/usr/bin/env julia
# Julia/Graphs lane for gcm_nesting_tower_le2q_v0.

using Dates
using Graphs
using JSON
using Pkg
using SHA

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "gcm_nesting_tower_le2q_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const ONE_Q_REGISTRY_PATH = joinpath(ROOT, "system_v6", "sims", "gcm_object_id_freeze_v0", "results", "gcm_object_id_freeze_v0_registry.json")
const TWO_Q_REGISTRY_PATH = joinpath(ROOT, "system_v6", "sims", "gcm_2q_freeze_and_cut_v0", "results", "gcm_2q_freeze_and_cut_v0_registry.json")
const EXPECTED_2Q_SURVIVOR_COUNT = 544
const EXPECTED_EXACT_COMPATIBLE_2Q_COUNT = 256

now_z()::String = Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
rel(path::String)::String = replace(relpath(path, ROOT), "\\" => "/")

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function write_json(path::String, payload)
    mkpath(dirname(path))
    open(path, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
end

function pkg_version(name::String)::String
    for (_uuid, dep) in Pkg.dependencies()
        if dep.name == name && dep.version !== nothing
            return string(dep.version)
        end
    end
    return "unknown"
end

sgn(v)::Int = v < 0 ? -1 : v > 0 ? 1 : 0
coord_key(coord)::String = join([string(Int(v)) for v in coord], ",")
probe_key(coord)::String = string(sgn(Int(coord[1]))) * "," * string(sgn(Int(coord[3])))

function one_q_indexes(one_q)
    by_coord = Dict{String,String}()
    by_sig = Dict{String,Vector{String}}()
    ids = String[]
    for row in one_q["frozen_registry"]["survivors"]
        sid = row["survivor_id"]
        push!(ids, sid)
        by_coord[coord_key(row["coord_scaled"])] = sid
        key = probe_key(row["coord_scaled"])
        if !haskey(by_sig, key)
            by_sig[key] = String[]
        end
        push!(by_sig[key], sid)
    end
    for key in keys(by_sig)
        sort!(by_sig[key])
    end
    return by_coord, by_sig, ids
end

function tower_counts(one_q, two_q)
    by_coord, by_sig, one_ids = one_q_indexes(one_q)
    two_rows = two_q["frozen_2q_registry"]["survivors"]
    exact_count = 0
    exact_orphans = 0
    probe_rows = 0
    probe_orphans = 0
    probe_triples = 0
    product_exact = 0
    entangled_probe_rows = 0
    exact_a_fiber_counts = Dict(id => 0 for id in one_ids)

    vertex_count = length(two_rows) + length(one_ids)
    graph = SimpleGraph(vertex_count)
    one_vertex = Dict(one_ids[idx] => length(two_rows) + idx for idx in eachindex(one_ids))

    for (idx, row) in enumerate(two_rows)
        a_coord = coord_key(row["first_bloch_scaled"])
        b_coord = coord_key(row["second_bloch_scaled"])
        a_sig = probe_key(row["first_bloch_scaled"])
        b_sig = probe_key(row["second_bloch_scaled"])
        a_exact = get(by_coord, a_coord, nothing)
        b_exact = get(by_coord, b_coord, nothing)
        a_probe = get(by_sig, a_sig, String[])
        b_probe = get(by_sig, b_sig, String[])
        exact_ok = a_exact !== nothing && b_exact !== nothing
        probe_ok = !isempty(a_probe) && !isempty(b_probe)
        if a_exact !== nothing
            exact_a_fiber_counts[a_exact] += 1
            add_edge!(graph, idx, one_vertex[a_exact])
        end
        exact_count += exact_ok ? 1 : 0
        exact_orphans += exact_ok ? 0 : 1
        probe_rows += probe_ok ? 1 : 0
        probe_orphans += probe_ok ? 0 : 1
        probe_triples += probe_ok ? length(a_probe) * length(b_probe) : 0
        product_exact += (exact_ok && row["family"] == "product_grid") ? 1 : 0
        entangled_probe_rows += (probe_ok && row["entangled"] == true) ? 1 : 0
    end

    components = connected_components(graph)
    fiber_component_sizes = sort([length(comp) for comp in components])
    return Dict(
        "exact_tower_cardinality" => exact_count,
        "exact_orphan_2q_count" => exact_orphans,
        "probe_compatible_2q_count" => probe_rows,
        "probe_orphan_2q_count" => probe_orphans,
        "probe_tower_cardinality" => probe_triples,
        "product_exact_subtower_count" => product_exact,
        "entangled_probe_compatible_2q_count" => entangled_probe_rows,
        "exact_A_fiber_component_count" => length(components),
        "exact_A_fiber_component_sizes" => fiber_component_sizes,
        "exact_A_fiber_counts" => exact_a_fiber_counts,
    )
end

function build_result()
    one_q = JSON.parsefile(ONE_Q_REGISTRY_PATH)
    two_q = JSON.parsefile(TWO_Q_REGISTRY_PATH)
    counts = tower_counts(one_q, two_q)
    all_pass = (
        counts["exact_tower_cardinality"] == EXPECTED_EXACT_COMPATIBLE_2Q_COUNT &&
        counts["exact_tower_cardinality"] + counts["exact_orphan_2q_count"] == EXPECTED_2Q_SURVIVOR_COUNT &&
        counts["probe_compatible_2q_count"] + counts["probe_orphan_2q_count"] == EXPECTED_2Q_SURVIVOR_COUNT &&
        counts["product_exact_subtower_count"] == 16 * 16 &&
        counts["entangled_probe_compatible_2q_count"] == 16 &&
        counts["exact_A_fiber_component_count"] == 16 &&
        all(v == 34 for v in values(counts["exact_A_fiber_counts"]))
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
        "packages_used" => ["Graphs", "JSON"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "package_versions" => Dict("Graphs" => pkg_version("Graphs")),
        "package_observables" => Dict(
            "Graphs" => "SimpleGraph/add_edge!/connected_components encodes exact A-fiber incidence over 544 2Q survivors and 16 1Q bases",
        ),
        "reads_peer_result" => false,
        "graphs_receipt" => Dict(
            "exact_A_fiber_component_count" => counts["exact_A_fiber_component_count"],
            "exact_A_fiber_component_sizes" => counts["exact_A_fiber_component_sizes"],
        ),
        "exact_tower_cardinality" => counts["exact_tower_cardinality"],
        "probe_tower_cardinality" => counts["probe_tower_cardinality"],
        "probe_orphan_2q_count" => counts["probe_orphan_2q_count"],
        "exact_orphan_2q_count" => counts["exact_orphan_2q_count"],
        "product_exact_subtower_count" => counts["product_exact_subtower_count"],
        "all_pass" => all_pass,
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing exact A-fiber incidence graph"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive registry parsing and result writing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "JSON" => "supportive"),
    )
    write_json(RESULT_PATH, result)
    return result
end

function main()
    result = build_result()
    println(JSON.json(Dict("ok" => result["all_pass"], "result" => rel(RESULT_PATH))))
    return result["all_pass"] ? 0 : 1
end

exit(main())
