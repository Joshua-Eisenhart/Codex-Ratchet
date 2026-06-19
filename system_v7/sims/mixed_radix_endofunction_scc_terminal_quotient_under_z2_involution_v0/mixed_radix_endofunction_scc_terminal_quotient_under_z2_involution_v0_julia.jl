#!/usr/bin/env julia
# Julia leg: exact integer endofunction plus Graphs.jl SCC/condensation.
# The only shared input is spec.json. This file does not import the v6
# feedstock and does not read JAX or PyTorch results.

using Dates
using Graphs
using JSON
using SHA

const SIM_ID = "mixed_radix_endofunction_scc_terminal_quotient_under_z2_involution_v0"
const HERE = @__DIR__

function encode_coords(coords, shape)
    out = 0
    for idx in eachindex(shape)
        out = out * shape[idx] + coords[idx]
    end
    return Int(out)
end

function decode_id(state_id::Integer, shape)
    values = Int[]
    rest = Int(state_id)
    for modulus in reverse(shape)
        push!(values, rest % modulus)
        rest = div(rest, modulus)
    end
    return reverse(values)
end

function readout_sign(spec, orientation, d0, d1)
    word = spec["orientation_tables"][orientation]["radix_digit_0_word_rows"][d0 + 1][d1 + 1]
    component = spec["word_readout_components"][word][d0 + 1]
    return Int(spec["readout_sign_map"][component])
end

function base_next(spec, orientation, state_id)
    shape = Int.(spec["mixed_radix_shape"])
    d0, d1, d2, z = decode_id(state_id, shape)
    current = readout_sign(spec, orientation, d0, d1)
    nxt = readout_sign(spec, orientation, d0, (d1 + 1) % shape[2])
    next_d2 = (d2 + (d0 == 0 ? 1 : 3)) % shape[3]
    next_d0 = d0
    next_d1 = d1
    if next_d2 == 0
        inc = current != nxt ? 1 : 2
        next_d1 += inc
        while next_d1 >= shape[2]
            next_d1 -= shape[2]
            next_d0 = (next_d0 + 1) % shape[1]
        end
    end
    boundary = next_d0 != d0 || next_d1 != d1
    return encode_coords([next_d0, next_d1, next_d2, z], shape), boundary, readout_sign(spec, orientation, next_d0, next_d1)
end

function event_selected(spec, orientation, state_id)
    _, boundary, next_sign = base_next(spec, orientation, state_id)
    d0 = decode_id(state_id, Int.(spec["mixed_radix_shape"]))[1]
    orientation_sign = Int(spec["orientation_tables"][orientation]["orientation_sign"])
    orientation_row = (orientation_sign > 0 && d0 == 0) || (orientation_sign < 0 && d0 == 1)
    return boundary && orientation_row && orientation_sign * next_sign < 0
end

function apply_law(spec, orientation, state_id, law)
    shape = Int.(spec["mixed_radix_shape"])
    base_id, _, _ = base_next(spec, orientation, state_id)
    d0, d1, d2, _ = decode_id(base_id, shape)
    old_z = decode_id(state_id, shape)[4]
    event = event_selected(spec, orientation, state_id)
    next_z =
        law == "conserved_control" ? old_z :
        law == "parity_flipping_law" ? ((event && old_z == 0) ? 1 : old_z) :
        law == "reference_toggle_law" ? (event ? 1 - old_z : old_z) :
        error("unknown law $law")
    return encode_coords([d0, d1, d2, next_z], shape)
end

function transition_table(spec, orientation, law)
    return [apply_law(spec, orientation, state_id, law) for state_id in 0:63]
end

function scc_summary(table)
    n = length(table)
    g = SimpleDiGraph(n)
    for src in 0:(n - 1)
        add_edge!(g, src + 1, table[src + 1] + 1)
    end
    comps1 = strongly_connected_components(g)
    sort!(comps1, by = c -> (minimum(c), length(c)))
    classes = [sort([v - 1 for v in comp]) for comp in comps1]
    comp_id = Dict{Int,Int}()
    for (idx, members) in enumerate(classes)
        for member in members
            comp_id[member] = idx
        end
    end
    cond = condensation(g, comps1)
    outgoing = [Set{Int}() for _ in 1:length(classes)]
    for src in 0:(n - 1)
        a = comp_id[src]
        b = comp_id[table[src + 1]]
        if a != b
            push!(outgoing[a], b)
        end
    end
    terminal = [idx for idx in 1:length(classes) if isempty(outgoing[idx])]
    return Dict(
        "scc_count" => length(classes),
        "scc_classes" => classes,
        "quotient_classes" => classes,
        "quotient_class_count" => length(classes),
        "terminal_scc_count" => length(terminal),
        "terminal_scc_sizes" => sort([length(classes[idx]) for idx in terminal]),
        "terminal_scc_class_ids" => [idx - 1 for idx in terminal],
        "condensation_edge_count" => ne(cond)
    )
end

function sigma_table(shape)
    rows = Int[]
    for state_id in 0:63
        d0, d1, d2, z = decode_id(state_id, shape)
        push!(rows, encode_coords([d0, d1, d2, 1 - z], shape))
    end
    return rows
end

function direct_separators(table, sigma)
    rows = []
    for state_id in 0:(length(table) - 1)
        left = table[sigma[state_id + 1] + 1]
        right = sigma[table[state_id + 1] + 1]
        if left != right
            push!(rows, Dict("state_id" => state_id, "left_image" => left, "right_image" => right))
        end
    end
    return rows
end

function main()
    spec = JSON.parsefile(joinpath(HERE, "spec.json"))
    shape = Int.(spec["mixed_radix_shape"])
    laws = collect(keys(spec["update_law_identifiers"]))
    sort!(laws)
    orientations = ["map_plus", "map_minus"]
    sigma = sigma_table(shape)
    summaries = Dict()
    direct = Dict()
    for orientation in orientations
        summaries[orientation] = Dict()
        direct[orientation] = Dict()
        for law in laws
            table = transition_table(spec, orientation, law)
            summary = scc_summary(table)
            summary["endofunction_table"] = table
            summaries[orientation][law] = summary
            direct[orientation][law] = direct_separators(table, sigma)
        end
    end
    selected = Dict(orientation => summaries[orientation]["parity_flipping_law"] for orientation in orientations)
    src_sha = bytes2hex(sha256(read(joinpath(HERE, "$(SIM_ID)_julia.jl"), String)))
    result = Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "computation_style" => "julia_integer_endofunction_graphs_scc_condensation",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "does_not_self_upgrade" => true,
        "reads_peer_result" => false,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_sha256" => src_sha,
        "result_path" => "system_v7/sims/$(SIM_ID)/results/$(SIM_ID)_julia_results.json",
        "mixed_radix_shape" => shape,
        "finite_set_size" => 64,
        "state_labels" => [string(i) for i in 0:63],
        "transition_map" => Dict(k => v["endofunction_table"] for (k, v) in selected),
        "endofunction_table" => Dict(k => v["endofunction_table"] for (k, v) in selected),
        "scc_count" => Dict(k => v["scc_count"] for (k, v) in selected),
        "scc_classes" => Dict(k => v["scc_classes"] for (k, v) in selected),
        "quotient_classes" => Dict(k => v["quotient_classes"] for (k, v) in selected),
        "quotient_class_count" => Dict(k => v["quotient_class_count"] for (k, v) in selected),
        "terminal_scc_count" => Dict(k => v["terminal_scc_count"] for (k, v) in selected),
        "terminal_scc_sizes" => Dict(k => v["terminal_scc_sizes"] for (k, v) in selected),
        "involution_definition" => spec["involution_definition"],
        "involution_is_equivariant" => Dict(
            orientation => Dict(law => isempty(direct[orientation][law]) for law in laws)
            for orientation in orientations
        ),
        "per_orientation" => summaries,
        "lineage" => spec["lineage"],
        "legacy_project_labels" => spec["legacy_project_labels"],
        "legacy_paths" => spec["legacy_paths"],
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing strongly_connected_components and condensation on the exact integer endofunction graph"),
            "JSON/SHA/Dates" => Dict("tried" => true, "used" => true, "reason" => "supportive spec read, source hashing, timestamp")
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "JSON/SHA/Dates" => "supportive"),
        "packages_used" => ["Graphs", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["Graphs"]
    )
    out = joinpath(HERE, "results", "$(SIM_ID)_julia_results.json")
    open(out, "w") do io
        JSON.print(io, result, 2)
    end
    println("julia leg wrote $out")
    println(JSON.json(result["terminal_scc_sizes"]))
end

main()
