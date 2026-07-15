#!/usr/bin/env julia

using Dates
using Graphs
using JSON3
using SHA

const SIM_DIR = @__DIR__
const SOURCE_PATH = abspath(@__FILE__)
const RESULT_PATH = joinpath(SIM_DIR, "results", "julia_results.json")

function relation_from_edges(n::Int, edges)
    relation = falses(n, n)
    for i in 1:n
        relation[i, i] = true
    end
    for edge in edges
        i, j = edge[1] + 1, edge[2] + 1
        relation[i, j] = true
        relation[j, i] = true
    end
    relation
end

function relation_from_mask(n::Int, mask::Int)
    relation = falses(n, n)
    for i in 1:n
        relation[i, i] = true
    end
    bit = 0
    for i in 1:n-1, j in i+1:n
        value = ((mask >> bit) & 1) == 1
        relation[i, j] = value
        relation[j, i] = value
        bit += 1
    end
    relation
end

function is_transitive(relation)
    n = size(relation, 1)
    for i in 1:n, j in 1:n, k in 1:n
        if relation[i, j] && relation[j, k] && !relation[i, k]
            return false
        end
    end
    true
end

function graph_closure(relation)
    n = size(relation, 1)
    graph = SimpleGraph(n)
    for i in 1:n-1, j in i+1:n
        relation[i, j] && add_edge!(graph, i, j)
    end
    components = sort(connected_components(graph), by=minimum)
    labels = zeros(Int, n)
    for (label, component) in enumerate(components)
        for vertex in component
            labels[vertex] = label - 1
        end
    end
    closure = [labels[i] == labels[j] for i in 1:n, j in 1:n]
    closure, labels
end

function census(n::Int)
    total = 1 << div(n * (n - 1), 2)
    equivalences = 0
    for mask in 0:total-1
        equivalences += is_transitive(relation_from_mask(n, mask)) ? 1 : 0
    end
    Dict(
        "tolerances" => total,
        "equivalences" => equivalences,
        "nontransitive" => total - equivalences,
    )
end

function contains_relation(candidate, raw)
    all((!raw[i, j]) || candidate[i, j] for i in axes(raw, 1), j in axes(raw, 2))
end

function added_pair_count(candidate, raw)
    n = size(raw, 1)
    count = 0
    for i in 1:n-1, j in i+1:n
        if candidate[i, j] && !raw[i, j]
            count += 1
        end
    end
    count
end

function class_labels(relation)
    n = size(relation, 1)
    representatives = Int[]
    labels = zeros(Int, n)
    for i in 1:n
        found = findfirst(rep -> relation[i, :] == relation[rep, :], representatives)
        if found === nothing
            push!(representatives, i)
            labels[i] = length(representatives) - 1
        else
            labels[i] = found - 1
        end
    end
    labels
end

function mss_antichain(raw)
    n = size(raw, 1)
    total = 1 << div(n * (n - 1), 2)
    candidates = Any[]
    for mask in 0:total-1
        relation = relation_from_mask(n, mask)
        if is_transitive(relation) && contains_relation(relation, raw)
            labels = class_labels(relation)
            push!(candidates, Dict(
                "labels" => labels,
                "added_pair_count" => added_pair_count(relation, raw),
                "quotient_class_count" => length(unique(labels)),
            ))
        end
    end
    survivors = Any[]
    for candidate in candidates
        dominated = any(
            other !== candidate &&
            other["added_pair_count"] <= candidate["added_pair_count"] &&
            other["quotient_class_count"] <= candidate["quotient_class_count"] &&
            (other["added_pair_count"] < candidate["added_pair_count"] ||
             other["quotient_class_count"] < candidate["quotient_class_count"])
            for other in candidates
        )
        !dominated && push!(survivors, candidate)
    end
    sort!(survivors, by=x -> (x["added_pair_count"], x["quotient_class_count"], x["labels"]))
    candidates, survivors
end

function coface_loss(labels, demand_edges)
    sum(
        (labels[edge[1] + 1] == labels[edge[2] + 1] ? 1 : 0 for edge in demand_edges);
        init=0,
    )
end

function nested_bool(matrix)
    [[Bool(matrix[i, j]) for j in axes(matrix, 2)] for i in axes(matrix, 1)]
end

function drive_record()
    raw = relation_from_edges(4, [[0, 1], [2, 3]])
    closure, proposal = graph_closure(raw)
    initial = [0, 0, 0, 0]
    demand = [[1, 2]]
    scrambled = [[0, 1]]
    initial_loss = coface_loss(initial, demand)
    proposal_loss = coface_loss(proposal, demand)
    drive = initial_loss - proposal_loss
    reverse_drive = proposal_loss - initial_loss
    null_drive = coface_loss(initial, []) - coface_loss(proposal, [])
    universal = fill(0, length(initial))
    universal_drive = initial_loss - coface_loss(universal, demand)
    scrambled_drive = coface_loss(initial, scrambled) - coface_loss(proposal, scrambled)
    flat_drive = coface_loss(proposal, demand) - coface_loss(proposal, demand)
    _, survivors = mss_antichain(raw)
    Dict(
        "raw_closure" => nested_bool(closure),
        "initial_labels" => initial,
        "proposal_labels" => proposal,
        "initial_coface_loss" => initial_loss,
        "proposal_coface_loss" => proposal_loss,
        "drive" => drive,
        "decision" => drive > 0 ? "COMMIT_TOOTH" : "HOLD",
        "controls" => Dict(
            "reverse_drive" => reverse_drive,
            "reverse_decision" => reverse_drive > 0 ? "COMMIT_TOOTH" : "HOLD",
            "null_drive" => null_drive,
            "null_decision" => null_drive > 0 ? "COMMIT_TOOTH" : "HOLD",
            "universal_proposal_drive" => universal_drive,
            "universal_proposal_decision" => universal_drive > 0 ? "COMMIT_TOOTH" : "HOLD",
            "scrambled_drive" => scrambled_drive,
            "scrambled_decision" => scrambled_drive > 0 ? "COMMIT_TOOTH" : "HOLD",
            "flat_drive" => flat_drive,
            "flat_decision" => flat_drive > 0 ? "COMMIT_TOOTH" : "HOLD",
        ),
        "mss_antichain" => survivors,
    )
end

function main()
    expected = Dict(
        "1" => Dict("tolerances" => 1, "equivalences" => 1, "nontransitive" => 0),
        "2" => Dict("tolerances" => 2, "equivalences" => 2, "nontransitive" => 0),
        "3" => Dict("tolerances" => 8, "equivalences" => 5, "nontransitive" => 3),
        "4" => Dict("tolerances" => 64, "equivalences" => 15, "nontransitive" => 49),
        "5" => Dict("tolerances" => 1024, "equivalences" => 52, "nontransitive" => 972),
    )
    observed = Dict(string(n) => census(n) for n in 1:5)
    chain = relation_from_edges(3, [[0, 1], [1, 2]])
    chain_closure, chain_labels = graph_closure(chain)
    drive = drive_record()
    controls = drive["controls"]
    all_pass = observed == expected && !is_transitive(chain) && chain_closure[1, 3] &&
        chain_labels == [0, 0, 0] && drive["proposal_labels"] == [0, 0, 1, 1] &&
        drive["drive"] == 1 && drive["decision"] == "COMMIT_TOOTH" &&
        controls["reverse_drive"] < 0 && controls["null_drive"] == 0 &&
        controls["universal_proposal_drive"] == 0 && controls["scrambled_drive"] == 0 &&
        length(drive["mss_antichain"]) == 2
    result = Dict(
        "schema" => "codex_ratchet.tolerance_to_equivalence.engine_result.v1",
        "sim_id" => "tolerance_to_equivalence_ratchet_rung_v0",
        "engine" => "julia",
        "generated_at" => string(now(UTC)),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict(
                "used" => true,
                "reason" => "Graphs.jl connected components execute the independent Julia closure lane",
            ),
            "JSON3" => Dict(
                "used" => true,
                "reason" => "JSON3 emits the source-bound engine receipt",
            ),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "JSON3" => "supportive"),
        "reads_peer_result" => false,
        "source_path" => relpath(SOURCE_PATH, dirname(dirname(dirname(SIM_DIR)))),
        "source_sha256" => bytes2hex(sha256(read(SOURCE_PATH))),
        "runtime" => Dict("julia_version" => string(VERSION), "active_project" => Base.active_project()),
        "packages_used" => ["Graphs", "JSON3", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "census" => observed,
        "transitivity_witness" => Dict(
            "raw_transitive" => is_transitive(chain),
            "closure_labels" => chain_labels,
            "forced_endpoint_related" => chain_closure[1, 3],
            "closure_matrix" => nested_bool(chain_closure),
        ),
        "drive_fixture" => drive,
        "all_pass" => all_pass,
        "claim_ceiling" => "one frozen finite tolerance-to-equivalence scratch rung only",
    )
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON3.pretty(io, result)
        write(io, '\n')
    end
    drive_value = drive["drive"]
    survivor_count = length(drive["mss_antichain"])
    println("JULIA_TOLERANCE_RUNG_DONE all_pass=$(lowercase(string(all_pass))) drive=$(drive_value) mss=$(survivor_count)")
    all_pass ? 0 : 2
end

exit(main())
