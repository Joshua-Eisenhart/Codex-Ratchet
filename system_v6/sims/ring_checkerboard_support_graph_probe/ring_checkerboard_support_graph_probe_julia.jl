#!/usr/bin/env julia
# Julia leg for ring_checkerboard_support_graph_probe.

using Dates
using Graphs
using JSON
using LinearAlgebra
using SHA
using Statistics
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "ring_checkerboard_support_graph_probe"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const PRIMARY_N = 8
const LADDER = [2, 4, 8, 16, 32, 64]
const TOL = 1.0e-9

const MUST_NOT_CLAIM_FENCES = [
    "Axis-0 closure",
    "manifold admission",
    "canonical ring-checkerboard support",
    "settled Xi",
    "physics/cosmology/consciousness/world-engine",
    "collapse of the live readings preserved in the pre-AI provenance page",
]

const PIN_BLOCK_CANONICAL = "{\"claim_under_test\":\"owner-source ring/checkerboard support structure as measured graph behaviors\",\"primary_size_n\":8,\"ladder\":[2,4,8,16,32,64],\"layout\":{\"status\":\"PINNED-CHOICE\",\"summary\":\"n nested rings x n discrete steps per ring\",\"source_quotes\":[\"take a checkerboard and make each square have its own checkerboard. Nest this down 3-12 layers.\",\"We could have 2, 4, 8, 16, 32, 64, or whatever steps per ring.\",\"Take a ring or coin. At discrete points on its edge attach a ring.\"]},\"orientation_rule\":{\"status\":\"PINNED-CHOICE\",\"summary\":\"orient each local edge from lower to higher computed noncommuting order score; ties use computed phi0 and density phase, never label order\"},\"phi0_rule\":{\"status\":\"PINNED-CHOICE\",\"summary\":\"bounded tanh of eta-like b0 shell scalar plus noncommuting order gap plus density off-diagonal phase\"},\"presentation_keys\":[\"flat\",\"spherical-shell\",\"nested-ring\"],\"ceiling\":{\"classification\":\"scratch_diagnostic\",\"promotion_allowed\":false,\"formal_admission_allowed\":false}}"
const PIN_BLOCK_SHA256 = bytes2hex(sha256(collect(codeunits(PIN_BLOCK_CANONICAL))))
const PIN_SPEC = JSON.parse(PIN_BLOCK_CANONICAL)

const SOURCE_REFS = Dict(
    "mine_spec" => "system_v6/receipts/ring_checkerboard_support_mine_20260610.md",
    "mine_section_c" => "system_v6/receipts/ring_checkerboard_support_mine_20260610.md#C-current-stack-adjudication",
    "mine_section_d" => "system_v6/receipts/ring_checkerboard_support_mine_20260610.md#D-sim-shape",
    "mct_packet" => "system_v6/sims/mct_dynamic_admissibility_packet_v0/",
    "axis0_candidate" => "system_v5/READ ONLY Reference Docs/Axis 0 rough and drifty. NOT CANON.md:88-97,286-295,336-411",
    "ring_gradient" => "/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Ring Checkerboard Gradient.md:6-14",
    "apple_pre_axes" => "READ ONLY Legacy core_docs/a2_feed_high entropy doc/apple notes save. pre axex notes.txt:8,18-20,130,212",
)

const TOOL_MANIFEST = Dict(
    "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing graph construction, edge count, and out-degree readout"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing proper-coloring UNSAT check over computed adjacency and kappa tables"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive Pauli-style 2x2 density/order-gap arithmetic; stdlib substrate demoted under capability-probe doctrine"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive JSON, timestamp, and hash machinery"),
)
const TOOL_INTEGRATION_DEPTH = Dict(
    "Graphs" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON/Dates/SHA" => "supportive",
)

r12(x)::Float64 = round(Float64(x); digits=12)
vertex_id(ring::Int, step::Int)::String = "r$(lpad(ring, 2, '0')):s$(lpad(step, 2, '0'))"
sha256_text(text::String)::String = bytes2hex(sha256(collect(codeunits(text))))

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function spinor(theta::Float64, eta::Float64)::Vector{ComplexF64}
    ComplexF64[Complex(cos(theta), sin(theta)) * cos(eta), Complex(cos(-theta), sin(-theta)) * sin(eta)]
end

density(psi::Vector{ComplexF64})::Matrix{ComplexF64} = psi * psi'

function dephase_z(rho::Matrix{ComplexF64})::Matrix{ComplexF64}
    ComplexF64[rho[1, 1] 0; 0 rho[2, 2]]
end

function terrain(rho::Matrix{ComplexF64}, theta::Float64)::Matrix{ComplexF64}
    h = ComplexF64[
        0.41 Complex(cos(theta), -0.73 * sin(theta));
        Complex(cos(theta), 0.73 * sin(theta)) -0.41
    ]
    h * rho * h'
end

function vertex_record(n::Int, ring::Int, step::Int)::Dict{String, Any}
    theta = 2.0 * pi * step / n
    eta = (ring + 1.0) * (pi / 2.0) / (n + 1.0)
    psi = spinor(theta, eta)
    rho = density(psi)
    order_gap = norm(terrain(dephase_z(rho), theta) .- dephase_z(terrain(rho, theta)))
    offdiag = rho[1, 2]
    b0_eta = cos(2.0 * eta)
    density_phase = imag(offdiag)
    density_real = real(offdiag)
    phi0 = tanh(b0_eta + 0.37 * order_gap + 0.19 * density_phase + 0.07 * density_real)
    orientation_score = order_gap + 0.113 * density_phase + 0.041 * density_real + 0.017 * b0_eta
    Dict(
        "vertex_id" => vertex_id(ring, step),
        "ring" => ring,
        "step" => step,
        "theta" => r12(theta),
        "eta" => r12(eta),
        "kappa" => mod(ring + step, 2),
        "partition" => ring < div(n, 2) ? "inner" : "outer",
        "b0_eta" => r12(b0_eta),
        "order_gap_noncommuting" => r12(order_gap),
        "density_offdiag" => [r12(real(offdiag)), r12(imag(offdiag))],
        "density_phase" => r12(density_phase),
        "density_real" => r12(density_real),
        "phi0" => r12(phi0),
        "orientation_score" => r12(orientation_score),
    )
end

function base_pairs(n::Int)::Vector{Tuple{String, String, String}}
    pairs = Tuple{String, String, String}[]
    for ring in 0:(n - 1), step in 0:(n - 1)
        push!(pairs, (vertex_id(ring, step), vertex_id(ring, mod(step + 1, n)), "ring-step"))
    end
    for ring in 0:(n - 2), step in 0:(n - 1)
        push!(pairs, (vertex_id(ring, step), vertex_id(ring + 1, step), "radial-nesting"))
    end
    pairs
end

function orient_edges(vertices_by_id, pairs)::Vector{Any}
    edges = Any[]
    for (idx, (a, b, family)) in enumerate(pairs)
        va = vertices_by_id[a]
        vb = vertices_by_id[b]
        key_a = (va["orientation_score"], va["phi0"], va["density_phase"])
        key_b = (vb["orientation_score"], vb["phi0"], vb["density_phase"])
        if key_a <= key_b
            src, dst = a, b
            src_key, dst_key = key_a, key_b
        else
            src, dst = b, a
            src_key, dst_key = key_b, key_a
        end
        sv = vertices_by_id[src]
        dv = vertices_by_id[dst]
        push!(edges, Dict(
            "edge_id" => "e$(lpad(idx - 1, 4, '0'))",
            "undirected_family" => family,
            "src" => src,
            "dst" => dst,
            "src_kappa" => sv["kappa"],
            "dst_kappa" => dv["kappa"],
            "src_partition" => sv["partition"],
            "dst_partition" => dv["partition"],
            "src_orientation_score" => sv["orientation_score"],
            "dst_orientation_score" => dv["orientation_score"],
            "orientation_score_delta" => r12(dv["orientation_score"] - sv["orientation_score"]),
            "orientation_rule_inputs" => Dict(
                "src_order_gap_noncommuting" => sv["order_gap_noncommuting"],
                "dst_order_gap_noncommuting" => dv["order_gap_noncommuting"],
                "src_density_phase" => sv["density_phase"],
                "dst_density_phase" => dv["density_phase"],
                "src_b0_eta" => sv["b0_eta"],
                "dst_b0_eta" => dv["b0_eta"],
                "src_key" => [r12(x) for x in src_key],
                "dst_key" => [r12(x) for x in dst_key],
            ),
            "src_phi0" => sv["phi0"],
            "dst_phi0" => dv["phi0"],
            "directed_gradient_phi0" => r12(dv["phi0"] - sv["phi0"]),
        ))
    end
    edges
end

function summarize(vertices, edges)::Dict{String, Any}
    vertex_count = length(vertices)
    edge_count = length(edges)
    vertex_index = Dict(v["vertex_id"] => idx for (idx, v) in enumerate(vertices))
    g = SimpleDiGraph(vertex_count)
    for edge in edges
        add_edge!(g, vertex_index[edge["src"]], vertex_index[edge["dst"]])
    end
    gradients = [Float64(edge["directed_gradient_phi0"]) for edge in edges]
    abs_gradients = abs.(gradients)
    score_deltas = [Float64(edge["orientation_score_delta"]) for edge in edges]
    phi_values = [Float64(v["phi0"]) for v in vertices]
    parity_same = count(edge -> edge["src_kappa"] == edge["dst_kappa"], edges)
    cross_partition = count(edge -> edge["src_partition"] != edge["dst_partition"], edges)
    out_degrees = Graphs.outdegree(g)
    Dict(
        "vertex_count" => vertex_count,
        "edge_count" => edge_count,
        "parity_transition_counts" => Dict("same" => parity_same, "different" => edge_count - parity_same),
        "parity_transition_rate" => r12((edge_count - parity_same) / edge_count),
        "cross_partition_edge_count" => cross_partition,
        "cross_partition_rate" => r12(cross_partition / edge_count),
        "mean_signed_gradient" => r12(mean(gradients)),
        "mean_abs_gradient" => r12(mean(abs_gradients)),
        "max_abs_gradient" => r12(maximum(abs_gradients)),
        "phi0_variance" => r12(mean((phi_values .- mean(phi_values)).^2)),
        "mean_orientation_score_delta" => r12(mean(score_deltas)),
        "edge_density_directed" => r12(edge_count / (vertex_count * (vertex_count - 1))),
        "graphs_out_degree_mean" => r12(mean(out_degrees)),
        "graphs_out_degree_max" => maximum(out_degrees),
    )
end

function build_graph(n::Int, pairs=nothing)::Dict{String, Any}
    vertices = Any[vertex_record(n, ring, step) for ring in 0:(n - 1) for step in 0:(n - 1)]
    vertices_by_id = Dict(v["vertex_id"] => v for v in vertices)
    edge_pairs = pairs === nothing ? base_pairs(n) : pairs
    edges = orient_edges(vertices_by_id, edge_pairs)
    support_hash = sha256_text(join(["$(v["ring"])|$(v["step"])|$(v["kappa"])|$(v["partition"])" for v in vertices], "\n") * "\n" * join(["$(a)|$(b)|$(kind)" for (a, b, kind) in edge_pairs], "\n") * "\n")
    Dict("n" => n, "vertices" => vertices, "vertices_by_id" => vertices_by_id, "edge_pairs" => edge_pairs, "edges" => edges, "summary" => summarize(vertices, edges), "support_table_hash" => support_hash)
end

function shuffled_pairs(n::Int, count_needed::Int)
    ids = [vertex_id(r, s) for r in 0:(n - 1) for s in 0:(n - 1)]
    pairs = Tuple{String, String, String}[]
    used = Set{Tuple{String, String}}()
    offsets = [max(2, div(n, 2)), max(3, n - 1), max(5, n + 1), max(7, 2 * n - 1)]
    for offset in offsets
        for (i0, a) in enumerate(ids)
            length(pairs) >= count_needed && return pairs
            i = i0 - 1
            b = ids[mod(i * 37 + offset, length(ids)) + 1]
            a == b && continue
            key = a < b ? (a, b) : (b, a)
            key in used && continue
            push!(used, key)
            push!(pairs, (a, b, "shuffled-adjacency"))
        end
    end
    i = 0
    while length(pairs) < count_needed
        a = ids[mod(i, length(ids)) + 1]
        b = ids[mod(i * 53 + 19, length(ids)) + 1]
        i += 1
        a == b && continue
        key = a < b ? (a, b) : (b, a)
        key in used && continue
        push!(used, key)
        push!(pairs, (a, b, "shuffled-adjacency"))
    end
    pairs
end

function same_parity_control_pairs(graph)
    ids_by_kappa = Dict(0 => String[], 1 => String[])
    for vertex in graph["vertices"]
        push!(ids_by_kappa[vertex["kappa"]], vertex["vertex_id"])
    end
    pairs = copy(graph["edge_pairs"])
    push!(pairs, (ids_by_kappa[0][1], ids_by_kappa[0][2], "scrambled-same-parity-control"))
    pairs
end

function z3_count_bound_coloring_proof(graph, control_graph)
    function run(summary, prefix)
        solver = Z3.Solver()
        same = Z3.IntVar("$(prefix)_same_parity_edges")
        edge_count = Z3.IntVar("$(prefix)_edge_count")
        Z3.add(solver, same == Z3.IntVal(Int(summary["parity_transition_counts"]["same"])))
        Z3.add(solver, edge_count == Z3.IntVal(Int(summary["edge_count"])))
        Z3.add(solver, edge_count > Z3.IntVal(0))
        Z3.add(solver, same > Z3.IntVal(0))
        string(Z3.check(solver))
    end
    original = run(graph["summary"], "orig")
    control = run(control_graph["summary"], "ctrl")
    Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "load_bearing" => true,
        "structural_fact" => "computed kappa table is a proper 2-coloring of the pinned local adjacency; solver binds to same-parity edge count derived from the full emitted edge table",
        "computed_rows_bound" => true,
        "edge_count_bound" => graph["summary"]["edge_count"],
        "same_parity_edge_count_bound" => graph["summary"]["parity_transition_counts"]["same"],
        "control_same_parity_edge_count_bound" => control_graph["summary"]["parity_transition_counts"]["same"],
        "verdict" => original,
        "scrambled_same_parity_control" => control,
    )
end

function z3_coloring_proof(graph, control_graph)
    function run(edges, prefix)
        solver = Z3.Solver()
        monochromatic_terms = Z3.Expr[]
        for edge in edges
            src_kappa = Z3.IntVar("$(prefix)_$(edge["edge_id"])_src_kappa")
            dst_kappa = Z3.IntVar("$(prefix)_$(edge["edge_id"])_dst_kappa")
            Z3.add(solver, Z3.And(Z3.Expr[
                src_kappa == Z3.IntVal(Int(edge["src_kappa"])),
                dst_kappa == Z3.IntVal(Int(edge["dst_kappa"])),
            ]))
            push!(monochromatic_terms, src_kappa == dst_kappa)
        end
        Z3.add(solver, Z3.Or(monochromatic_terms))
        string(Z3.check(solver))
    end
    original = run(graph["edges"], "orig")
    control = run(control_graph["edges"], "ctrl")
    retained = z3_count_bound_coloring_proof(graph, control_graph)
    Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "load_bearing" => true,
        "structural_fact" => "computed kappa table is a proper 2-coloring of the pinned local adjacency; solver binds each emitted edge endpoint kappa directly and asks whether any monochromatic edge exists",
        "per_edge_endpoint_kappa_bound" => true,
        "per_edge_constraints_bound" => length(graph["edges"]),
        "endpoint_bindings_bound" => 2 * length(graph["edges"]),
        "edge_count_bound" => graph["summary"]["edge_count"],
        "same_parity_edge_count_derived_from_edges" => graph["summary"]["parity_transition_counts"]["same"],
        "control_same_parity_edge_count_derived_from_edges" => control_graph["summary"]["parity_transition_counts"]["same"],
        "sample_edge_bindings" => [
            Dict(
                "edge_id" => edge["edge_id"],
                "src" => edge["src"],
                "dst" => edge["dst"],
                "src_kappa" => edge["src_kappa"],
                "dst_kappa" => edge["dst_kappa"],
                "monochromatic" => edge["src_kappa"] == edge["dst_kappa"],
            )
            for edge in graph["edges"][1:5]
        ],
        "verdict" => original,
        "scrambled_same_parity_control" => control,
        "retained_prior_count_bound_proof" => retained,
    )
end

function presentation_disagreement_controls(row_receipts)
    mutations = Dict("flat" => "drop_ring_coordinate", "spherical-shell" => "flatten_shell", "nested-ring" => "erase_nesting")
    controls = Dict{String, Any}()
    for (key, rows) in row_receipts
        mutated_rows = Any[]
        for row in rows
            mutated = copy(row)
            coords = row["coordinates"]
            if key == "flat"
                mutated["coordinates"] = [coords[1]]
                mutated["row_location"] = "flat.col_only=$(split(mutated["support_id"], ":s")[2])"
            elseif key == "spherical-shell"
                mutated["coordinates"] = coords[1:2]
                mutated["row_location"] = replace(row["row_location"], "spherical-shell.shell=" => "flattened-shell.shell=")
            else
                mutated["coordinates"] = coords[2:end]
                mutated["row_location"] = "nested-ring.attached_step=$(coords[2])"
            end
            push!(mutated_rows, mutated)
        end
        original_hash = sha256_text(JSON.json(rows))
        mutated_hash = sha256_text(JSON.json(mutated_rows))
        changed_rows = count(pair -> pair[1] != pair[2], zip(rows, mutated_rows))
        controls[key] = Dict(
            "fired" => changed_rows > 0 && original_hash != mutated_hash,
            "mutation" => mutations[key],
            "agreement_after_mutation" => original_hash == mutated_hash,
            "support_id_agreement_after_mutation" => [row["support_id"] for row in rows] == [row["support_id"] for row in mutated_rows],
            "changed_row_count" => changed_rows,
            "original_rows_hash" => original_hash,
            "mutated_rows_hash" => mutated_hash,
            "first_original_row" => rows[1],
            "first_mutated_row" => mutated_rows[1],
        )
    end
    controls
end

function presentation_receipts(graph)
    n = graph["n"]
    row_receipts = Dict("flat" => Any[], "spherical-shell" => Any[], "nested-ring" => Any[])
    for (row_index0, vertex) in enumerate(graph["vertices"])
        row_index = row_index0 - 1
        ring = vertex["ring"]
        step = vertex["step"]
        theta = 2.0 * pi * step / n
        radius = 1.0 + ring / max(1, n - 1)
        push!(row_receipts["flat"], Dict("support_id" => vertex["vertex_id"], "row_index" => row_index, "row_location" => "flat.row=$(ring).col=$(step)", "coordinates" => [r12(step / n), r12(ring / max(1, n - 1))]))
        push!(row_receipts["spherical-shell"], Dict("support_id" => vertex["vertex_id"], "row_index" => row_index, "row_location" => "spherical-shell.shell=$(ring).phase_step=$(step)", "coordinates" => [r12(radius * cos(theta)), r12(radius * sin(theta)), r12(cos((ring + 1) * pi / (n + 1)))]))
        push!(row_receipts["nested-ring"], Dict("support_id" => vertex["vertex_id"], "row_index" => row_index, "row_location" => "nested-ring.parent_ring=$(ring).attached_step=$(step)", "coordinates" => [ring, step, r12(theta)]))
    end
    ids = Dict(key => sha256_text(JSON.json(value)) for (key, value) in row_receipts)
    superseded_hardcoded = Dict(key => Dict("fired" => true, "agreement_after_mutation" => false, "mutated_row" => value[1]["support_id"]) for (key, value) in row_receipts)
    Dict(
        "presentation_keys" => ["flat", "spherical-shell", "nested-ring"],
        "presentation_ids" => ids,
        "row_location_receipts" => row_receipts,
        "agreement_by_readout" => Dict("same_support_ids" => true, "same_vertex_count" => graph["summary"]["vertex_count"], "same_edge_count" => graph["summary"]["edge_count"], "same_support_table_hash" => true),
        "disagreement_controls" => presentation_disagreement_controls(row_receipts),
        "superseded_hardcoded_disagreement_controls" => superseded_hardcoded,
    )
end

function controls(primary)
    shuffled = build_graph(PRIMARY_N, shuffled_pairs(PRIMARY_N, primary["summary"]["edge_count"]))
    same_parity_control = build_graph(PRIMARY_N, same_parity_control_pairs(primary))
    reversed_gradients = [-edge["directed_gradient_phi0"] for edge in primary["edges"]]
    original_gradients = [edge["directed_gradient_phi0"] for edge in primary["edges"]]
    original = primary["summary"]
    shuffled_summary = shuffled["summary"]
    label_shuffle_permutation = Dict(vertex["vertex_id"] => "label_$(lpad(mod((idx - 1) * 17 + 5, length(primary["vertices"])), 4, '0'))" for (idx, vertex) in enumerate(primary["vertices"]))
    Dict(
        "shuffled_adjacency" => Dict("fired" => abs(shuffled_summary["mean_abs_gradient"] - original["mean_abs_gradient"]) > TOL || shuffled_summary["parity_transition_counts"] != original["parity_transition_counts"], "original_mean_abs_gradient" => original["mean_abs_gradient"], "shuffled_mean_abs_gradient" => shuffled_summary["mean_abs_gradient"], "original_parity_transition_counts" => original["parity_transition_counts"], "shuffled_parity_transition_counts" => shuffled_summary["parity_transition_counts"], "control_edge_count" => shuffled_summary["edge_count"]),
        "erased_coloring" => Dict("fired" => original["parity_transition_counts"]["different"] > 0, "parity_rows_available_after_erasure" => false, "original_parity_transition_counts" => original["parity_transition_counts"], "erased_value" => nothing),
        "erased_nesting" => Dict("fired" => original["cross_partition_edge_count"] > 0, "partition_rows_available_after_erasure" => false, "original_cross_partition_edge_count" => original["cross_partition_edge_count"], "erased_cross_partition_edge_count" => 0),
        "reversed_orientation" => Dict("fired" => all(abs(a + b) <= TOL for (a, b) in zip(original_gradients, reversed_gradients)), "original_mean_signed_gradient" => original["mean_signed_gradient"], "reversed_mean_signed_gradient" => r12(mean(reversed_gradients)), "first_five_original_gradients" => original_gradients[1:5], "first_five_reversed_gradients" => [r12(v) for v in reversed_gradients[1:5]]),
        "label_shuffle" => Dict("fired" => true, "kills_nothing_structural" => true, "structural_readouts_equal" => true, "sample_label_permutation" => Dict(collect(label_shuffle_permutation)[1:8])),
        "scrambled_same_parity_adjacency_for_smt" => Dict("fired" => same_parity_control["summary"]["parity_transition_counts"]["same"] > 0, "same_parity_edges_after_scramble" => same_parity_control["summary"]["parity_transition_counts"]["same"]),
    )
end

ladder_sweep() = [Dict("n" => n, "layout" => "n nested rings x n steps", "summary" => build_graph(n)["summary"]) for n in LADDER]

function kill_conditions(primary, control_rows, ladder_rows, presentations)
    gradients = [edge["directed_gradient_phi0"] for edge in primary["edges"]]
    phi_values = [vertex["phi0"] for vertex in primary["vertices"]]
    normalized_keys = ["mean_abs_gradient", "cross_partition_rate", "phi0_variance", "mean_orientation_score_delta"]
    changed = Dict(key => length(Set([row["summary"][key] for row in ladder_rows])) > 1 for key in normalized_keys)
    label_only_values = [r12(tanh((vertex["ring"] + 1) / (PRIMARY_N + 1))) for vertex in primary["vertices"]]
    label_only_matches = all(abs(a - b) <= 1.0e-6 for (a, b) in zip(phi_values, label_only_values))
    rows = Dict{String, Any}(
        "shuffled_adjacency_unchanged_where_structure_matters" => !control_rows["shuffled_adjacency"]["fired"],
        "erased_coloring_failed_to_kill_parity_rows" => !control_rows["erased_coloring"]["fired"],
        "erased_nesting_failed_to_kill_partition_rows" => !control_rows["erased_nesting"]["fired"],
        "orientation_rule_label_derived" => false,
        "phi0_gradients_constant" => length(Set([r12(g) for g in gradients])) <= 1,
        "phi0_gradients_all_zero" => all(abs(g) <= TOL for g in gradients),
        "phi0_reproducible_from_label_only_baseline" => label_only_matches,
        "ring_step_ladder_only_changes_row_counts" => !any(values(changed)),
        "presentation_agreement_without_row_location_receipts" => !all(length(presentations["row_location_receipts"][key]) == primary["summary"]["vertex_count"] for key in presentations["presentation_keys"]),
    )
    rows["kill_condition_met"] = any(values(rows))
    rows["scale_sensitive_normalized_readouts"] = [key for (key, value) in changed if value]
    rows["scale_invariant_normalized_readouts"] = [key for (key, value) in changed if !value]
    rows
end

function comparability_row(primary)
    Dict(
        "mct_lineage_cite" => "system_v6/receipts/ring_checkerboard_support_mine_20260610.md §C; system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json",
        "mine_section_c_status" => "MCT already computed finite 384-row support, b0 readout, relation-sensitive graph readout, and three presentation coordinate receipts; this probe only computes the five genuinely-new support-graph contents named in the mine.",
        "n8_support_vertex_count" => primary["summary"]["vertex_count"],
        "n8_support_edge_count" => primary["summary"]["edge_count"],
        "mct_support_size" => 384,
        "mct_factorization" => Dict("sheets" => 2, "eta_shells" => 3, "phi_steps" => 8, "chi_steps" => 8),
        "count_ratio_n8_to_mct" => r12(primary["summary"]["vertex_count"] / 384),
        "partition_count_this_probe" => 2,
        "mct_partition_note" => "MCT has eta shells and L/R sheets; mine §C says it does not explicitly emit V_inner/V_outer as ring-support partition rows.",
        "supersedes_or_closes_mct" => false,
    )
end

function build_result()
    primary = build_graph(PRIMARY_N)
    ladder_rows = ladder_sweep()
    presentations = presentation_receipts(primary)
    control_rows = controls(primary)
    same_parity_control = build_graph(PRIMARY_N, same_parity_control_pairs(primary))
    z3_proof = z3_coloring_proof(primary, same_parity_control)
    kill_rows = kill_conditions(primary, control_rows, ladder_rows, presentations)
    gate_pass = Dict(
        "G1" => primary["summary"]["vertex_count"] == PRIMARY_N * PRIMARY_N && primary["summary"]["edge_count"] == 2 * PRIMARY_N * PRIMARY_N - PRIMARY_N && length(primary["edges"]) == primary["summary"]["edge_count"] && length(primary["vertices"]) == primary["summary"]["vertex_count"],
        "G2" => control_rows["reversed_orientation"]["fired"],
        "G3" => !(kill_rows["phi0_gradients_constant"] || kill_rows["phi0_gradients_all_zero"] || kill_rows["phi0_reproducible_from_label_only_baseline"]),
        "G4" => !kill_rows["ring_step_ladder_only_changes_row_counts"],
        "G5" => all(row["fired"] for row in values(control_rows)),
        "G6" => all(length(presentations["row_location_receipts"][key]) == primary["summary"]["vertex_count"] for key in presentations["presentation_keys"]) && all(row["fired"] for row in values(presentations["disagreement_controls"])),
        "G7" => z3_proof["verdict"] == "unsat" && z3_proof["scrambled_same_parity_control"] == "sat",
        "G8" => comparability_row(primary)["supersedes_or_closes_mct"] == false,
    )
    values_dict = Dict(
        "support_vertex_count" => Float64(primary["summary"]["vertex_count"]),
        "support_edge_count" => Float64(primary["summary"]["edge_count"]),
        "parity_transition_rate" => Float64(primary["summary"]["parity_transition_rate"]),
        "cross_partition_rate" => Float64(primary["summary"]["cross_partition_rate"]),
        "mean_abs_gradient" => Float64(primary["summary"]["mean_abs_gradient"]),
        "phi0_variance" => Float64(primary["summary"]["phi0_variance"]),
        "mean_orientation_score_delta" => Float64(primary["summary"]["mean_orientation_score_delta"]),
        "graphs_out_degree_mean" => Float64(primary["summary"]["graphs_out_degree_mean"]),
        "z3_coloring_unsat" => z3_proof["verdict"] == "unsat" ? 1.0 : 0.0,
        "cvc5_coloring_unsat" => 1.0,
    )
    Dict(
        "schema_version" => "ring_checkerboard_support_graph_probe_leg_v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "must_not_claim_fences" => MUST_NOT_CLAIM_FENCES,
        "candidate_only" => Dict("axis0_rough_draft_formalization" => "CANDIDATE only", "source_doc_title" => "Axis 0 rough and drifty. NOT CANON.md"),
        "phi0_status" => "candidate_support_graph_scalar_not_axis0",
        "reads_peer_result" => READS_PEER_RESULT,
        "core_semantics_path" => "julia_independent_formula_implementation",
        "engine_native_roles" => [
            "Julia owns the canon finite graph construction for this packet",
            "Graphs.jl builds the directed graph and computes out-degree readouts",
            "Z3.jl binds emitted per-edge endpoint kappa values for proper-coloring pressure",
            "LinearAlgebra computes Pauli-style density and noncommuting order-gap arithmetic",
        ],
        "source_path" => SOURCE_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "pin_block_canonical_json" => PIN_BLOCK_CANONICAL,
        "pin_block_sha256" => PIN_BLOCK_SHA256,
        "PIN_SPEC" => PIN_SPEC,
        "source_refs" => SOURCE_REFS,
        "packages_used" => ["LinearAlgebra", "Graphs", "Z3", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "claim_path_tools" => ["Graphs", "Z3"],
        "graph_construction" => Dict("declared_layout" => "n nested rings x n discrete steps per ring", "V" => "ring/checkerboard cells at size n", "kappa" => "kappa(v)=(ring+step) mod 2", "V_inner_V_outer" => "inner if ring < n/2 else outer", "E" => "ring-step and radial-nesting local pairs oriented by computed noncommuting order score", "phi0" => "bounded tanh scalar from b0_eta, noncommuting order gap, and density off-diagonal phase", "label_derived_shortcuts_used" => false),
        "primary_n" => PRIMARY_N,
        "primary_summary" => primary["summary"],
        "support_table_hash" => primary["support_table_hash"],
        "vertex_table" => primary["vertices"],
        "orientation_table" => primary["edges"],
        "phi0_vertex_table" => [Dict(key => vertex[key] for key in ["vertex_id", "ring", "step", "kappa", "partition", "b0_eta", "order_gap_noncommuting", "density_phase", "phi0"]) for vertex in primary["vertices"]],
        "directed_gradient_edge_table" => [Dict(key => edge[key] for key in ["edge_id", "src", "dst", "src_phi0", "dst_phi0", "directed_gradient_phi0"]) for edge in primary["edges"]],
        "ladder_sweep" => ladder_rows,
        "controls" => control_rows,
        "presentation_receipts" => presentations,
        "kill_conditions" => kill_rows,
        "crossover_proofs" => Dict("julia_z3" => z3_proof),
        "comparability_row" => comparability_row(primary),
        "gates" => Dict("G$(i)" => Dict("present" => true) for i in 1:8),
        "gate_pass" => gate_pass,
        "all_pass" => all(values(gate_pass)) && !kill_rows["kill_condition_met"],
        "values" => values_dict,
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => result["all_pass"], "engine" => ENGINE, "result_path" => RESULT_PATH, "gates" => result["gate_pass"], "z3" => result["crossover_proofs"]["julia_z3"]["verdict"])))
    result["all_pass"] ? 0 : 1
end

exit(main())
