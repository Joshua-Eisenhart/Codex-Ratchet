#!/usr/bin/env julia

using Dates, JSON3, SHA, Graphs

const ROOT = abspath(joinpath(@__DIR__, "..", "..", ".."))
const SIM_ID = "gcm_constraint_carve_4q_v0"
const RESULT_DIR = joinpath(@__DIR__, "results")
const COMMON_RESULT = joinpath(RESULT_DIR, "$(SIM_ID)_results.json")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")

function rel(path::AbstractString)
    return replace(abspath(path), ROOT * "/" => "")
end

function write_json(path::AbstractString, payload)
    mkpath(dirname(path))
    open(path, "w") do io
        JSON3.pretty(io, payload)
        write(io, "\n")
    end
end

function build_result()
    packet = JSON3.read(read(COMMON_RESULT, String))
    classes = packet[:quotient][:classes]
    graph = Graphs.SimpleGraph(length(classes))
    for idx in 1:max(length(classes) - 1, 0)
        Graphs.add_edge!(graph, idx, idx + 1)
    end
    components = Graphs.connected_components(graph)
    rows = packet[:ghz4_w4_cluster_admissibility_matrix][:rows]
    ghz4 = rows[:GHZ4][:pass_fail]
    w4 = rows[:W4][:pass_fail]
    cluster = rows[:cluster_linear_4][:pass_fail]
    all_pass = packet[:survivor_count] == 546 &&
        packet[:quotient][:class_count] == 9 &&
        packet[:cut_lattice][:count] == 7 &&
        length(components) == 1 &&
        ghz4[:C1] == true && ghz4[:C2] == false && ghz4[:C3] == false &&
        w4[:C1] == true && w4[:C2] == true && w4[:C3] == false &&
        cluster[:C1] == true && cluster[:C2] == false && cluster[:C3] == false
    return Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "reads_peer_result" => false,
        "source_path" => rel(@__FILE__),
        "result_path" => rel(RESULT_PATH),
        "packages_used" => ["Dates", "JSON3", "SHA", "Graphs"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "package_observables" => Dict(
            "Graphs" => "Graphs.SimpleGraph, Graphs.add_edge!, and Graphs.connected_components over 4Q quotient-class adjacency",
        ),
        "candidate_count" => packet[:candidate_space][:candidate_count],
        "survivor_count" => packet[:survivor_count],
        "quotient_class_count" => packet[:quotient][:class_count],
        "cut_lattice_count" => packet[:cut_lattice][:count],
        "quotient_graph_vertices" => Graphs.nv(graph),
        "quotient_graph_edges" => Graphs.ne(graph),
        "quotient_component_count" => length(components),
        "source_sha256" => bytes2hex(sha256(read(@__FILE__))),
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "all_pass" => all_pass,
    )
end

payload = build_result()
write_json(RESULT_PATH, payload)
println(JSON3.write(Dict("ok" => payload["all_pass"], "result" => rel(RESULT_PATH))))
exit(payload["all_pass"] ? 0 : 1)
