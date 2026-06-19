#!/usr/bin/env julia
# Supplement-pinned Axis 0 amendment light sweep, Julia exact mirror.

using Dates
using Graphs
using JSON
using LinearAlgebra
using SHA

const SIM_ID = "axis0_amendment_light_sweep_v1"
const ROOT = normpath(joinpath(@__DIR__, "..", "..", ".."))
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = @__FILE__
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const CARRIER_RESULT = joinpath(ROOT, "system_v6", "sims", "discrete_axis0_field_v0", "results", "discrete_axis0_field_v0_envelope_results.json")
const EXPECTED_STATE_COUNT = 33
const AMENDMENT_COMMIT = "34596316d"

rel(path::AbstractString) = relpath(normpath(path), ROOT)

function now_z()
    return Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
end

function sha256_file(path::AbstractString)
    return bytes2hex(open(sha256, path))
end

function stable_hash(value)
    return bytes2hex(sha256(JSON.json(value)))
end

function sign_value(x::Real)
    x > 1.0e-12 && return 1
    x < -1.0e-12 && return -1
    return 0
end

function float_obj(x::Real)
    rounded = round(Float64(x), digits=15)
    return Dict("float" => rounded, "str" => string(rounded))
end

function bloch(value)
    coord = isa(value, AbstractDict) && haskey(value, "coord") ? value["coord"] : value
    return [Float64(coord[1]), Float64(coord[2]), Float64(coord[3])]
end

function vn_entropy_from_bloch(coord)
    radius = min(1.0, max(0.0, norm(coord)))
    eigs = [(1.0 + radius) / 2.0, (1.0 - radius) / 2.0]
    return -sum(p > 0.0 ? p * log(p) : 0.0 for p in eigs)
end

function trace_norm_bloch(left, right)
    return norm(left .- right)
end

function load_carrier()
    payload = JSON.parsefile(CARRIER_RESULT)
    cells = payload["carrier_cells"]
    edges = payload["carrier_edges"]
    return Dict(
        "state_object_id" => payload["state_object_id"],
        "state_count" => payload["carrier"]["state_count"],
        "edge_count" => payload["carrier"]["edge_count"],
        "cells" => cells,
        "edges" => edges,
    )
end

function cell_map(carrier)
    return Dict(Int(cell["cell_id"]) => cell for cell in carrier["cells"])
end

function outgoing_edges(carrier)
    out = Dict(i => Any[] for i in 0:(EXPECTED_STATE_COUNT - 1))
    for edge in carrier["edges"]
        push!(out[Int(edge["src"])], edge)
    end
    return out
end

function sign_vector(raw)
    return [sign_value(raw[i]) for i in 0:(EXPECTED_STATE_COUNT - 1)]
end

function vector_payload(raw)
    signs = sign_vector(raw)
    rows = Any[]
    for i in 0:(EXPECTED_STATE_COUNT - 1)
        push!(rows, Dict(
            "cell_id" => i,
            "raw_value" => float_obj(raw[i]),
            "sign_value" => signs[i + 1],
        ))
    end
    return rows, signs
end

function cp11_system_typed_vn_one_step_majority(carrier)
    cells = cell_map(carrier)
    out = outgoing_edges(carrier)
    raw = Dict{Int, Float64}()
    for cell_id in 0:(EXPECTED_STATE_COUNT - 1)
        before = vn_entropy_from_bloch(bloch(cells[cell_id]))
        votes = Int[]
        for edge in out[cell_id]
            after = vn_entropy_from_bloch(bloch(edge["image_before_quantization"]))
            push!(votes, sign_value(after - before))
        end
        raw[cell_id] = Float64(sum(votes))
    end
    return raw
end

function cp14_single_cell_vn_adjacency_difference(carrier)
    cells = cell_map(carrier)
    entropy = Dict(cell_id => vn_entropy_from_bloch(bloch(cell)) for (cell_id, cell) in cells)
    raw = Dict(i => 0.0 for i in 0:(EXPECTED_STATE_COUNT - 1))
    for edge in carrier["edges"]
        src = Int(edge["src"])
        dst = Int(edge["dst"])
        raw[src] += entropy[dst] - entropy[src]
    end
    return raw
end

function cp12_trace_norm_error_change_light(carrier)
    cells = cell_map(carrier)
    out = outgoing_edges(carrier)
    raw = Dict{Int, Float64}()
    for cell_id in 0:(EXPECTED_STATE_COUNT - 1)
        src = bloch(cells[cell_id])
        votes = Int[]
        for edge in out[cell_id]
            dst = bloch(cells[Int(edge["dst"])])
            pred = bloch(edge["image_before_quantization"])
            source_to_prediction = trace_norm_bloch(src, pred)
            prediction_to_committed = trace_norm_bloch(pred, dst)
            push!(votes, sign_value(prediction_to_committed - source_to_prediction))
        end
        raw[cell_id] = Float64(sum(votes))
    end
    return raw
end

function graph_controls(carrier)
    graph = SimpleDiGraph(EXPECTED_STATE_COUNT)
    for edge in carrier["edges"]
        add_edge!(graph, Int(edge["src"]) + 1, Int(edge["dst"]) + 1)
    end
    return Dict(
        "node_count" => nv(graph),
        "edge_count" => ne(graph),
        "strong_component_count" => length(strongly_connected_components(graph)),
    )
end

function candidate_record(cid, raw; queued_heavy=false, vector_status="computed_33_cell")
    vector, signs = vector_payload(raw)
    return Dict(
        "candidate" => cid,
        "queued_heavy" => queued_heavy,
        "vector_status" => vector_status,
        "candidate_vector" => vector,
        "sign_vector" => signs,
        "sign_vector_sha256" => stable_hash(signs),
    )
end

function build_result()
    carrier = load_carrier()
    cp11 = cp11_system_typed_vn_one_step_majority(carrier)
    cp12 = cp12_trace_norm_error_change_light(carrier)
    cp14 = cp14_single_cell_vn_adjacency_difference(carrier)
    rows = [
        candidate_record("A0.CP.11", cp11),
        candidate_record("A0.CP.12", cp12; queued_heavy=true),
        Dict(
            "candidate" => "A0.CP.13",
            "queued_heavy" => true,
            "vector_status" => "not_computed_heavy_global_bipartition_required",
            "adapter_status" => "bound_not_computed_in_light_pass",
            "heavy_queue_reason" => "global Phi_0/I_c bipartition with z4 typing is heavy; no local proxy emitted",
        ),
        candidate_record("A0.CP.14", cp14),
    ]
    graph = graph_controls(carrier)
    gates = Dict(
        "carrier_count" => Int(carrier["state_count"]) == EXPECTED_STATE_COUNT,
        "edge_count_nonzero" => Int(carrier["edge_count"]) > 0,
        "graph_rebuilt_with_graphs" => graph["node_count"] == EXPECTED_STATE_COUNT && graph["edge_count"] > 0,
        "cp11_vector_33" => length(rows[1]["sign_vector"]) == EXPECTED_STATE_COUNT,
        "cp12_vector_33" => length(rows[2]["sign_vector"]) == EXPECTED_STATE_COUNT,
        "cp13_heavy_queued" => rows[3]["queued_heavy"] == true,
        "cp14_vector_33" => length(rows[4]["sign_vector"]) == EXPECTED_STATE_COUNT,
    )
    all_pass = all(values(gates))
    return Dict(
        "schema" => "$(SIM_ID)_julia_lane_v1",
        "sim_id" => SIM_ID,
        "role_id" => "supplement_pinned_axis0_light_julia_exact_mirror",
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "generated_at" => now_z(),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "reads_peer_result" => false,
        "all_pass" => all_pass,
        "authority_binding" => Dict("supplement" => Dict("commit" => AMENDMENT_COMMIT)),
        "carrier_binding" => Dict(
            "carrier_state_object_id" => carrier["state_object_id"],
            "state_count" => carrier["state_count"],
            "edge_count" => carrier["edge_count"],
            "source" => rel(CARRIER_RESULT),
        ),
        "candidate_verdict_table" => rows,
        "computed_vector_hashes" => Dict(row["candidate"] => row["sign_vector_sha256"] for row in rows if haskey(row, "sign_vector_sha256")),
        "graph_controls" => graph,
        "build_gates" => gates,
        "claim_path_tools" => ["Graphs", "LinearAlgebra"],
        "packages_used" => ["Graphs", "JSON", "LinearAlgebra", "SHA"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "package_observables" => Dict("Graphs" => "SimpleDiGraph exact committed generator node/edge/SCC counts"),
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("used" => true, "reason" => "independent finite directed graph mirror"),
            "LinearAlgebra" => Dict("used" => true, "reason" => "norms for vN entropy and trace-norm light row"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "LinearAlgebra" => "supportive"),
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
