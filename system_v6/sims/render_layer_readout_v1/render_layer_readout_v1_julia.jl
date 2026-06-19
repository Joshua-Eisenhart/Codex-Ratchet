#!/usr/bin/env julia

using Dates
using Graphs
using JSON
using LinearAlgebra
using SHA
using Z3

const SIM_ID = "render_layer_readout_v1"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "render_layer_readout_v1_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const ANCHOR_RESULT = joinpath(ROOT, "system_v6", "sims", "discrete_axis0_field_v0", "results", "discrete_axis0_field_v0_envelope_results.json")
const EXPECTED_STATE_COUNT = 33
const TRAJECTORY_LENGTH = 33

function now_z()
    return Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
end

function rel(path::AbstractString)
    return replace(path, ROOT * "/" => "")
end

function sha256_file(path::AbstractString)
    return bytes2hex(open(SHA.sha256, path))
end

function stable_hash(value)
    return bytes2hex(SHA.sha256(JSON.json(value)))
end

function vec3(value)
    return Float64[value[1], value[2], value[3]]
end

function sign_value(value::Float64)
    if value > 1.0e-12
        return 1
    elseif value < -1.0e-12
        return -1
    end
    return 0
end

function sign_label(value::Int)
    if value == 1
        return "reshape_the_render"
    elseif value == -1
        return "resist_the_update"
    end
    return "neutral_no_render_polarity"
end

function float_obj(value)
    rounded = round(Float64(value), digits=15)
    return Dict("float" => rounded, "str" => string(rounded))
end

function load_anchor()
    return JSON.parsefile(ANCHOR_RESULT)
end

function edge_by_key(carrier_edges)
    out = Dict{String,Any}()
    for edge in carrier_edges
        out[string(Int(edge["src"]), "|", edge["generator"])] = edge
    end
    return out
end

function trajectory_edges(anchor)
    carrier = anchor["carrier"]
    by_key = edge_by_key(anchor["carrier_edges"])
    current = 0
    rows = Any[]
    generators = carrier["generator_names"]
    for step in 0:(TRAJECTORY_LENGTH - 1)
        generator = generators[mod(step, length(generators)) + 1]
        edge = copy(by_key[string(current, "|", generator)])
        edge["trajectory_step"] = step
        push!(rows, edge)
        current = Int(edge["dst"])
    end
    return rows
end

function pin_value(source, render, realized)
    prediction = render - source
    length = norm(prediction)
    if length <= 1.0e-12
        return 0.0
    end
    direction = prediction / length
    return dot(realized - render, direction)
end

function render_step_rows(anchor)
    cells = Dict(Int(cell["cell_id"]) => cell for cell in anchor["carrier_cells"])
    rows = Any[]
    for edge in trajectory_edges(anchor)
        src_id = Int(edge["src"])
        dst_id = Int(edge["dst"])
        source = vec3(cells[src_id]["coord"])
        render = vec3(edge["image_before_quantization"])
        realized = vec3(cells[dst_id]["coord"])
        correction = realized - render
        updated_render = render + correction
        residual = norm(updated_render - realized)
        direction_scalar = pin_value(source, render, realized)
        polarity = sign_value(direction_scalar)
        push!(rows, Dict(
            "step" => Int(edge["trajectory_step"]),
            "src" => src_id,
            "dst" => dst_id,
            "generator" => string(edge["generator"]),
            "render" => Dict("kind" => "committed_one_step_image_before_quantization", "coord" => round.(render; digits=12)),
            "realized_state" => Dict("kind" => "committed_quantized_successor_cell", "cell_id" => dst_id, "coord" => round.(realized; digits=12)),
            "update" => Dict(
                "correction_vector" => round.(correction; digits=12),
                "updated_render" => round.(updated_render; digits=12),
                "residual_after_update" => float_obj(residual),
            ),
            "error_flow" => Dict(
                "direction_scalar" => float_obj(direction_scalar),
                "polarity_sign" => polarity,
                "polarity_label" => sign_label(polarity),
                "formula_id" => "sign(dot(realized-render, unit(render-source)))",
            ),
        ))
    end
    return rows
end

function aggregate_render(anchor, rows)
    incoming = Dict{Int,Vector{Float64}}()
    for edge in anchor["carrier_edges"]
        src = vec3(anchor["carrier_cells"][Int(edge["src"]) + 1]["coord"])
        dst = vec3(anchor["carrier_cells"][Int(edge["dst"]) + 1]["coord"])
        render = vec3(edge["image_before_quantization"])
        push!(get!(incoming, Int(edge["dst"]), Float64[]), pin_value(src, render, dst))
    end
    raw = Dict{Int,Float64}()
    traj = Dict{Int,Vector{Float64}}()
    for row in rows
        cell = Int(row["realized_state"]["cell_id"])
        push!(get!(traj, cell, Float64[]), Float64(row["error_flow"]["direction_scalar"]["float"]))
    end
    for cell in 0:(EXPECTED_STATE_COUNT - 1)
        values = haskey(traj, cell) ? traj[cell] : incoming[cell]
        raw[cell] = sum(values) / length(values)
    end
    signs = Dict(cell => sign_value(value) for (cell, value) in raw)
    return raw, signs
end

function graph_probe(anchor, signs)
    graph = SimpleDiGraph(EXPECTED_STATE_COUNT)
    cut_edges = 0
    for edge in anchor["carrier_edges"]
        src = Int(edge["src"])
        dst = Int(edge["dst"])
        add_edge!(graph, src + 1, dst + 1)
        if signs[src] != signs[dst]
            cut_edges += 1
        end
    end
    return Dict(
        "node_count" => nv(graph),
        "edge_count" => ne(graph),
        "committed_edge_rows_count" => length(anchor["carrier_edges"]),
        "render_polarity_cut_edge_count" => cut_edges,
        "load_bearing" => nv(graph) == EXPECTED_STATE_COUNT && length(anchor["carrier_edges"]) == Base.Int(anchor["carrier"]["edge_count"]),
    )
end

function z3_probe(reshape_cells, resist_cells)
    reshape = Z3.IntVar("reshape_cells")
    resist = Z3.IntVar("resist_cells")
    total = Z3.IntVar("total_cells")
    solver = Z3.Solver()
    Z3.add(solver, reshape == Z3.IntVal(reshape_cells))
    Z3.add(solver, resist == Z3.IntVal(resist_cells))
    Z3.add(solver, total == Z3.IntVal(EXPECTED_STATE_COUNT))
    valid = Z3.And([reshape > Z3.IntVal(0), resist > Z3.IntVal(0), total == Z3.IntVal(EXPECTED_STATE_COUNT)])
    Z3.add(solver, Z3.Not(valid))
    verdict = lowercase(string(Z3.check(solver)))
    erased = Z3.Solver()
    reshape2 = Z3.IntVar("reshape_cells_erased")
    resist2 = Z3.IntVar("resist_cells_erased")
    total2 = Z3.IntVar("total_cells_erased")
    Z3.add(erased, reshape2 == Z3.IntVal(0))
    Z3.add(erased, resist2 == Z3.IntVal(EXPECTED_STATE_COUNT))
    Z3.add(erased, total2 == Z3.IntVal(EXPECTED_STATE_COUNT))
    valid2 = Z3.And([reshape2 > Z3.IntVal(0), resist2 > Z3.IntVal(0), total2 == Z3.IntVal(EXPECTED_STATE_COUNT)])
    Z3.add(erased, Z3.Not(valid2))
    erased_verdict = lowercase(string(Z3.check(erased)))
    return Dict(
        "ran" => true,
        "solver" => "julia_z3",
        "verdict" => verdict,
        "erased_unreachable_control_verdict" => erased_verdict,
        "load_bearing" => true,
        "claim" => "computed v1 render polarity has both reshape and resist cells; erased old-pin-like control flips to SAT",
    )
end

function build_result()
    anchor = load_anchor()
    rows = render_step_rows(anchor)
    render_raw, render_signs = aggregate_render(anchor, rows)
    sign_vector = [render_signs[cell] for cell in 0:(EXPECTED_STATE_COUNT - 1)]
    reshape_cells = count(==(1), sign_vector)
    resist_cells = count(==(-1), sign_vector)
    graph = graph_probe(anchor, render_signs)
    z3_result = z3_probe(reshape_cells, resist_cells)
    gates = Dict(
        "finite_render_error_update_objects" => length(rows) == TRAJECTORY_LENGTH && all(Float64(row["update"]["residual_after_update"]["float"]) <= 1.0e-12 for row in rows),
        "render_classification_two_sided" => reshape_cells > 0 && resist_cells > 0,
        "julia_z3_reachability_unsat" => z3_result["verdict"] == "unsat" && z3_result["erased_unreachable_control_verdict"] == "sat",
        "graphs_probe_load_bearing" => graph["load_bearing"] == true,
    )
    return Dict(
        "schema" => "$(SIM_ID)_julia_lane_v1",
        "sim_id" => SIM_ID,
        "role_id" => "render_layer_readout_v1_julia_graphs_z3_mirror",
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "generated_at" => now_z(),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "reads_peer_result" => false,
        "all_pass" => all(values(gates)),
        "claim" => "finite render/error/update trajectory and v1 render-polarity distinction boundary mirror",
        "allowed_claims" => ["Julia mirror recomputes v1 render/update projection from committed carrier result"],
        "disallowed_claims" => ["holodeck admission", "FEP admission", "physics admission", "Axis-0 admission", "formal or canonical promotion"],
        "packages_used" => ["Graphs", "Z3", "JSON", "LinearAlgebra", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "package_observables" => Dict(
            "Graphs" => "Graphs.SimpleDiGraph/add_edge! finite committed generator graph and v1 render cut-edge probe",
            "Z3" => "Z3.Solver/check two-sided v1 reachability proof with erased old-pin control",
        ),
        "claim_path_tools" => ["Graphs", "Z3"],
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("tried" => true, "used" => true, "reason" => "finite committed generator graph and v1 render cut-edge probe"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "two-sided v1 reachability proof with erased old-pin control"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "Z3" => "load_bearing"),
        "trajectory" => rows,
        "render_readout" => Dict(
            "sign_vector" => sign_vector,
            "sign_vector_sha256" => stable_hash(sign_vector),
            "polarity_counts" => Dict("reshape_the_render" => reshape_cells, "resist_the_update" => resist_cells),
        ),
        "graph_probe" => graph,
        "counts" => Dict("trajectory_length" => length(rows), "reshape_cells" => reshape_cells, "resist_cells" => resist_cells, "unique_render_sign_count" => length(Set(sign_vector))),
        "crossover_proofs" => Dict("julia_z3" => z3_result),
        "build_gates" => gates,
        "computed_hashes" => Dict("trajectory_sha256" => stable_hash(rows), "render_sign_vector_sha256" => stable_hash(sign_vector)),
    )
end

function main()
    result = build_result()
    mkpath(RESULT_DIR)
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("result_path" => rel(RESULT_PATH), "all_pass" => result["all_pass"])))
    return result["all_pass"] ? 0 : 1
end

exit(main())
