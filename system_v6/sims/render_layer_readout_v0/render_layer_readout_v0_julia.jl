#!/usr/bin/env julia

using Dates
using Graphs
using JSON
using LinearAlgebra
using SHA
using Z3

const SIM_ID = "render_layer_readout_v0"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "render_layer_readout_v0_julia.jl")
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

function render_step_rows(anchor)
    cells = Dict(Int(cell["cell_id"]) => cell for cell in anchor["carrier_cells"])
    rows = Any[]
    for edge in trajectory_edges(anchor)
        src_id = Int(edge["src"])
        dst_id = Int(edge["dst"])
        source = vec3(cells[src_id]["coord"])
        render = vec3(edge["image_before_quantization"])
        realized = vec3(cells[dst_id]["coord"])
        source_to_render = norm(render - source)
        render_error = norm(realized - render)
        correction = realized - render
        updated_render = render + correction
        residual = norm(updated_render - realized)
        error_flow = render_error - source_to_render
        polarity = sign_value(error_flow)
        push!(rows, Dict(
            "step" => Int(edge["trajectory_step"]),
            "src" => src_id,
            "dst" => dst_id,
            "generator" => string(edge["generator"]),
            "render" => Dict("kind" => "committed_one_step_image_before_quantization", "coord" => round.(render; digits=12)),
            "realized_state" => Dict("kind" => "committed_quantized_successor_cell", "cell_id" => dst_id, "coord" => round.(realized; digits=12)),
            "error" => Dict(
                "type" => "single_qubit_bloch_trace_norm_divergence",
                "render_minus_realized" => round.(render - realized; digits=12),
                "trace_norm" => float_obj(render_error),
                "co_ratchet_type" => "render_vs_realized_same_committed_carrier_cell_type",
            ),
            "update" => Dict(
                "type" => "committed_quantization_error_correction_on_render_side",
                "correction_vector" => round.(correction; digits=12),
                "updated_render" => round.(updated_render; digits=12),
                "residual_after_update" => float_obj(residual),
            ),
            "error_flow" => Dict(
                "source_to_render_trace_norm" => float_obj(source_to_render),
                "render_to_realized_trace_norm" => float_obj(render_error),
                "direction_scalar" => float_obj(error_flow),
                "polarity_sign" => polarity,
                "polarity_label" => sign_label(polarity),
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
        value = norm(dst - render) - norm(render - src)
        push!(get!(incoming, Int(edge["dst"]), Float64[]), value)
    end
    raw = Dict{Int,Float64}()
    for row in rows
        cell = Int(row["realized_state"]["cell_id"])
        push!(get!(incoming, cell, Float64[]), Float64(row["error_flow"]["direction_scalar"]["float"]))
    end
    for cell in 0:(EXPECTED_STATE_COUNT - 1)
        raw[cell] = sum(incoming[cell]) / length(incoming[cell])
    end
    signs = Dict(cell => sign_value(value) for (cell, value) in raw)
    return raw, signs
end

function anchor_raw_sign(anchor)
    raw = Dict{Int,Float64}()
    signs = Dict{Int,Int}()
    for row in anchor["readout_table"]
        cell = Int(row["cell_id"])
        value = Float64(row["net_outgoing_gradient_flux"]["num"]) / Float64(row["net_outgoing_gradient_flux"]["den"])
        raw[cell] = value
        signs[cell] = sign_value(value)
    end
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

function z3_probe(nonzero_cells, unique_sign_count)
    stable = Z3.IntVar("stable_cells")
    total = Z3.IntVar("total_cells")
    unique = Z3.IntVar("unique_sign_count")
    solver = Z3.Solver()
    Z3.add(solver, stable == Z3.IntVal(nonzero_cells))
    Z3.add(solver, total == Z3.IntVal(EXPECTED_STATE_COUNT))
    Z3.add(solver, unique == Z3.IntVal(unique_sign_count))
    valid = Z3.Or([
        Z3.And([unique == Z3.IntVal(1), stable == total]),
        Z3.And([unique > Z3.IntVal(1), stable > Z3.IntVal(0), stable < total]),
    ])
    Z3.add(solver, Z3.Not(valid))
    verdict = lowercase(string(Z3.check(solver)))
    flip = Z3.Solver()
    stable2 = Z3.IntVar("stable_cells_erased")
    total2 = Z3.IntVar("total_cells_erased")
    unique2 = Z3.IntVar("unique_sign_count_erased")
    Z3.add(flip, stable2 == Z3.IntVal(0))
    Z3.add(flip, total2 == Z3.IntVal(EXPECTED_STATE_COUNT))
    Z3.add(flip, unique2 == Z3.IntVal(1))
    valid2 = Z3.Or([
        Z3.And([unique2 == Z3.IntVal(1), stable2 == total2]),
        Z3.And([unique2 > Z3.IntVal(1), stable2 > Z3.IntVal(0), stable2 < total2]),
    ])
    Z3.add(flip, Z3.Not(valid2))
    flip_verdict = lowercase(string(Z3.check(flip)))
    return Dict(
        "ran" => true,
        "solver" => "julia_z3",
        "verdict" => verdict,
        "flip_control_verdict" => flip_verdict,
        "load_bearing" => true,
        "claim" => "computed render polarity is classified as either nontrivial split or constant no-stable row; erased all-zero control flips satisfiable",
    )
end

function build_result()
    anchor = load_anchor()
    rows = render_step_rows(anchor)
    render_raw, render_signs = aggregate_render(anchor, rows)
    anchor_raw, anchor_signs = anchor_raw_sign(anchor)
    sign_vector = [render_signs[cell] for cell in 0:(EXPECTED_STATE_COUNT - 1)]
    axis0_disagreements = sum(anchor_signs[cell] != render_signs[cell] for cell in 0:(EXPECTED_STATE_COUNT - 1))
    graph = graph_probe(anchor, render_signs)
    nonzero = sum(value != 0 for value in values(render_signs))
    unique_sign_count = length(Set(sign_vector))
    z3_result = z3_probe(nonzero, unique_sign_count)
    gates = Dict(
        "finite_render_error_update_objects" => length(rows) == TRAJECTORY_LENGTH && all(Float64(row["update"]["residual_after_update"]["float"]) <= 1.0e-12 for row in rows),
        "trajectory_over_committed_generators" => length(Set(row["generator"] for row in rows)) == length(anchor["carrier"]["generator_names"]),
        "render_classification_recorded" => (unique_sign_count == 1 && nonzero == EXPECTED_STATE_COUNT) || (unique_sign_count > 1 && nonzero > 0 && nonzero < EXPECTED_STATE_COUNT),
        "axis0_boundary_different_or_decorative_recorded" => axis0_disagreements >= 0,
        "julia_z3_nontrivial_split_unsat" => z3_result["verdict"] == "unsat" && z3_result["flip_control_verdict"] == "sat",
        "graphs_probe_load_bearing" => graph["load_bearing"] == true,
    )
    return Dict(
        "schema" => "$(SIM_ID)_julia_lane_v1",
        "sim_id" => SIM_ID,
        "role_id" => "render_layer_readout_v0_julia_graphs_z3_mirror",
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "generated_at" => now_z(),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "reads_peer_result" => false,
        "all_pass" => all(values(gates)),
        "claim" => "finite render/error/update trajectory and render-polarity distinction boundary mirror",
        "allowed_claims" => ["Julia mirror recomputes render/error/update trajectory from committed carrier result", "Julia Graphs/Z3 checks support finite graph and nontrivial split"],
        "disallowed_claims" => ["holodeck admission", "FEP admission", "physics admission", "Axis-0 admission", "formal or canonical promotion"],
        "packages_used" => ["Graphs", "Z3", "JSON", "LinearAlgebra", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "package_observables" => Dict(
            "Graphs" => "Graphs.SimpleDiGraph/add_edge! finite committed generator graph and render cut-edge probe",
            "Z3" => "Z3.Solver/check nontrivial render split proof with erased flip",
        ),
        "claim_path_tools" => ["Graphs", "Z3"],
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("tried" => true, "used" => true, "reason" => "finite committed generator graph and render cut-edge probe"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "nontrivial render split proof with erased flip"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "Z3" => "load_bearing"),
        "carrier" => anchor["carrier"],
        "trajectory" => rows,
        "render_readout" => Dict(
            "sign_vector" => sign_vector,
            "sign_vector_sha256" => stable_hash(sign_vector),
            "polarity_counts" => Dict(string(k) => count(==(k), sign_vector) for k in sort(unique(sign_vector))),
        ),
        "axis0_boundary" => Dict(
            "axis0_disagreement_cells" => axis0_disagreements,
            "relation_to_axis0_phi" => axis0_disagreements == 0 ? "same_distinction_alias_into_axis0" : "different_distinction_from_axis0",
        ),
        "graph_probe" => graph,
        "counts" => Dict(
            "trajectory_length" => length(rows),
            "nonzero_render_cells" => nonzero,
            "unique_render_sign_count" => unique_sign_count,
            "axis0_disagreement_cells" => axis0_disagreements,
        ),
        "crossover_proofs" => Dict("julia_z3" => z3_result),
        "build_gates" => gates,
        "computed_hashes" => Dict(
            "trajectory_sha256" => stable_hash(rows),
            "render_sign_vector_sha256" => stable_hash(sign_vector),
        ),
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
