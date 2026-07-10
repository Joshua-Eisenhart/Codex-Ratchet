#!/usr/bin/env julia

using Graphs
using JSON3
using SHA

const HERE = @__DIR__
const REPO_ROOT = normpath(joinpath(HERE, "..", "..", ".."))
const SPEC_PATH = joinpath(HERE, "spec.json")
const PREREGISTRATION_PATH = joinpath(HERE, "preregistration_receipt.json")
const RESULT_PATH = joinpath(HERE, "results", "finite_probe_behavioral_object_engine_v0_julia_results.json")
const SOURCE_PATH = abspath(@__FILE__)

const SIM_ID = "finite_probe_behavioral_object_engine_v0"
const EXPECTED_SPEC_SHA256 = "73dfcce77e1f4001b3b2341817a449f96f898bc77c025323d1ca04ee3b3a1146"
const CLASSIFICATION = "scratch_diagnostic"
const RING_SIZE = 6
const STATE_COUNT = 1 << RING_SIZE
const RULE_A = 30
const RULE_B = 110
const MAX_REFINEMENT_DEPTH = 6

sha256_file(path::String) = open(path, "r") do io
    bytes2hex(SHA.sha256(io))
end

sha256_text(value::String) = bytes2hex(SHA.sha256(codeunits(value)))

bit_at(state::Int, site::Int) = (state >> mod(site, RING_SIZE)) & 1

function eca_step(state::Int, rule::Int)::Int
    next_state = 0
    for site in 0:(RING_SIZE - 1)
        left = bit_at(state, site - 1)
        center = bit_at(state, site)
        right = bit_at(state, site + 1)
        neighborhood = (left << 2) | (center << 1) | right
        next_state |= ((rule >> neighborhood) & 1) << site
    end
    next_state
end

function rotate_state(state::Int, shift::Int)::Int
    rotated = 0
    for site in 0:(RING_SIZE - 1)
        rotated |= bit_at(state, site) << mod(site + shift, RING_SIZE)
    end
    rotated
end

hamming_weight(state::Int) = count_ones(state)

function domain_walls(state::Int)::Int
    count(bit_at(state, site) != bit_at(state, site + 1) for site in 0:(RING_SIZE - 1))
end

function canonical_partition(cells)::Vector{Vector{Int}}
    normalized = [sort(unique(Int.(collect(cell)))) for cell in cells if !isempty(cell)]
    sort!(normalized; by=Tuple)
    normalized
end

function observation_partition(observation)::Vector{Vector{Int}}
    buckets = Dict{Any,Vector{Int}}()
    for state in 0:(STATE_COUNT - 1)
        push!(get!(buckets, observation(state), Int[]), state)
    end
    canonical_partition(values(buckets))
end

function class_ids(partition::Vector{Vector{Int}})::Vector{Int}
    ids = fill(0, STATE_COUNT)
    for (class_index, cell) in enumerate(partition), state in cell
        ids[state + 1] = class_index
    end
    all(>(0), ids) || error("partition does not cover all six-bit states")
    ids
end

function refine_partition(
    partition::Vector{Vector{Int}},
    action_a::Vector{Int},
    action_b::Vector{Int},
)::Vector{Vector{Int}}
    ids = class_ids(partition)
    refined = Vector{Vector{Int}}()
    for cell in partition
        buckets = Dict{NTuple{3,Int},Vector{Int}}()
        for state in cell
            signature = (
                ids[state + 1],
                ids[action_a[state + 1] + 1],
                ids[action_b[state + 1] + 1],
            )
            push!(get!(buckets, signature, Int[]), state)
        end
        append!(refined, values(buckets))
    end
    canonical_partition(refined)
end

function refinement_history(
    initial::Vector{Vector{Int}},
    action_a::Vector{Int},
    action_b::Vector{Int},
    max_depth::Int,
)::Vector{Vector{Vector{Int}}}
    history = [initial]
    for _ in 1:max_depth
        push!(history, refine_partition(last(history), action_a, action_b))
    end
    history
end

function first_stable_depth(history::Vector{Vector{Vector{Int}}})
    for depth in 1:(length(history) - 1)
        history[depth + 1] == history[depth] && return depth - 1
    end
    nothing
end

function rotation_orbits()::Vector{Vector{Int}}
    seen = falses(STATE_COUNT)
    cells = Vector{Vector{Int}}()
    for state in 0:(STATE_COUNT - 1)
        seen[state + 1] && continue
        orbit = sort(unique(rotate_state(state, shift) for shift in 0:(RING_SIZE - 1)))
        seen[orbit .+ 1] .= true
        push!(cells, orbit)
    end
    canonical_partition(cells)
end

function quotient_congruence(
    partition::Vector{Vector{Int}},
    action_a::Vector{Int},
    action_b::Vector{Int},
)
    ids = class_ids(partition)
    induced_a = Int[]
    induced_b = Int[]
    conflicts_a = Vector{Dict{String,Any}}()
    conflicts_b = Vector{Dict{String,Any}}()
    for (class_index, cell) in enumerate(partition)
        destinations_a = sort(unique(ids[action_a[state + 1] + 1] for state in cell))
        destinations_b = sort(unique(ids[action_b[state + 1] + 1] for state in cell))
        if length(destinations_a) == 1
            push!(induced_a, only(destinations_a) - 1)
        else
            push!(induced_a, -1)
            push!(conflicts_a, Dict(
                "source_class" => class_index - 1,
                "states" => cell,
                "destination_classes" => destinations_a .- 1,
            ))
        end
        if length(destinations_b) == 1
            push!(induced_b, only(destinations_b) - 1)
        else
            push!(induced_b, -1)
            push!(conflicts_b, Dict(
                "source_class" => class_index - 1,
                "states" => cell,
                "destination_classes" => destinations_b .- 1,
            ))
        end
    end
    (
        congruent=isempty(conflicts_a) && isempty(conflicts_b),
        induced_a=induced_a,
        induced_b=induced_b,
        conflicts_a=conflicts_a,
        conflicts_b=conflicts_b,
    )
end

function graph_receipt(induced_a::Vector{Int}, induced_b::Vector{Int})
    all(>=(0), induced_a) || error("cannot construct quotient graph from conflicting A map")
    all(>=(0), induced_b) || error("cannot construct quotient graph from conflicting B map")
    class_count = length(induced_a)
    graph = Graphs.SimpleDiGraph(class_count)
    labeled_edges = Vector{Dict{String,Any}}()
    expected_edges = Set{Tuple{Int,Int}}()
    for source in 0:(class_count - 1)
        for (action, destination) in (("A", induced_a[source + 1]), ("B", induced_b[source + 1]))
            Graphs.add_edge!(graph, source + 1, destination + 1)
            push!(expected_edges, (source + 1, destination + 1))
            push!(labeled_edges, Dict("source_class" => source, "action" => action, "destination_class" => destination))
        end
    end
    graph_edges = Set((Graphs.src(edge), Graphs.dst(edge)) for edge in Graphs.edges(graph))
    components = [sort(component .- 1) for component in Graphs.strongly_connected_components(graph)]
    sort!(components; by=Tuple)

    boundary_graph = Graphs.SimpleDiGraph(1)
    boundary_components = Graphs.strongly_connected_components(boundary_graph)
    boundary_pass = Graphs.nv(boundary_graph) == 1 && Graphs.ne(boundary_graph) == 0 && boundary_components == [[1]]
    passed = Graphs.nv(graph) == class_count && graph_edges == expected_edges &&
        sort(vcat(components...)) == collect(0:(class_count - 1)) && boundary_pass
    Dict{String,Any}(
        "vertex_count" => Graphs.nv(graph),
        "edge_count" => Graphs.ne(graph),
        "labeled_edges" => labeled_edges,
        "strongly_connected_components" => components,
        "boundary_singleton_graph_pass" => boundary_pass,
        "passed" => passed,
    )
end

function canonical_cycle(cycle::Vector{Int})::Vector{Int}
    candidates = [vcat(cycle[offset:end], cycle[1:(offset - 1)]) for offset in eachindex(cycle)]
    sort(candidates; by=Tuple)[1]
end

function attractor_cycle(transition::Vector{Int}, start::Int)::Vector{Int}
    path = Int[]
    first_index = Dict{Int,Int}()
    state = start
    while !haskey(first_index, state)
        first_index[state] = length(path) + 1
        push!(path, state)
        state = transition[state + 1]
    end
    canonical_cycle(path[first_index[state]:end])
end

function functional_graph_receipt(transition::Vector{Int})
    basins = Dict{String,Vector{Int}}()
    cycles = Dict{String,Vector{Int}}()
    for state in 0:(STATE_COUNT - 1)
        cycle = attractor_cycle(transition, state)
        key = join(cycle, ",")
        cycles[key] = cycle
        push!(get!(basins, key, Int[]), state)
    end
    records = [Dict{String,Any}(
        "cycle" => cycles[key],
        "period" => length(cycles[key]),
        "basin_size" => length(basins[key]),
        "basin_states" => sort(basins[key]),
    ) for key in keys(basins)]
    sort!(records; by=row -> Tuple(row["cycle"]))
    Dict{String,Any}(
        "attractor_count" => length(records),
        "sorted_basin_sizes" => sort(Int[row["basin_size"] for row in records]),
        "attractors" => records,
        "all_states_assigned_once" => sum(Int[row["basin_size"] for row in records]) == STATE_COUNT,
    )
end

function relabel_permutation(shift::Int)
    relabel = [rotate_state(state, shift) for state in 0:(STATE_COUNT - 1)]
    inverse = fill(0, STATE_COUNT)
    for state in 0:(STATE_COUNT - 1)
        inverse[relabel[state + 1] + 1] = state
    end
    relabel, inverse
end

function conjugate_transition(transition::Vector{Int}, relabel::Vector{Int}, inverse::Vector{Int})
    [relabel[transition[inverse[state + 1] + 1] + 1] for state in 0:(STATE_COUNT - 1)]
end

function pullback_partition(partition::Vector{Vector{Int}}, inverse::Vector{Int})
    canonical_partition([[inverse[state + 1] for state in cell] for cell in partition])
end

function mutated_transition_control(
    stable_partition::Vector{Vector{Int}},
    action_a::Vector{Int},
    action_b::Vector{Int},
)
    ids = class_ids(stable_partition)
    source_cell = first(cell for cell in stable_partition if length(cell) > 1)
    mutated_state = first(source_cell)
    original_destination_class = ids[action_a[mutated_state + 1] + 1]
    replacement_state = first(state for state in 0:(STATE_COUNT - 1) if ids[state + 1] != original_destination_class)
    mutated_a = copy(action_a)
    original_destination = mutated_a[mutated_state + 1]
    mutated_a[mutated_state + 1] = replacement_state
    receipt = quotient_congruence(stable_partition, mutated_a, action_b)
    Dict{String,Any}(
        "mutated_action" => "A",
        "mutated_state" => mutated_state,
        "original_destination" => original_destination,
        "replacement_destination" => replacement_state,
        "original_destination_class" => original_destination_class - 1,
        "replacement_destination_class" => ids[replacement_state + 1] - 1,
        "quotient_broken" => !receipt.congruent && !isempty(receipt.conflicts_a),
        "conflicts_A" => receipt.conflicts_a,
    )
end

function read_preregistered_inputs()
    spec_hash = sha256_file(SPEC_PATH)
    spec_hash == EXPECTED_SPEC_SHA256 || error("preregistered spec hash drift: expected $EXPECTED_SPEC_SHA256, got $spec_hash")
    spec = JSON3.read(read(SPEC_PATH, String))
    preregistration = JSON3.read(read(PREREGISTRATION_PATH, String))
    String(spec["schema"]) == "codex_ratchet.finite_probe_behavioral_object_engine.spec.v1" || error("unexpected spec schema")
    String(spec["sim_id"]) == SIM_ID || error("unexpected spec sim_id")
    String(preregistration["schema"]) == "codex_ratchet.preregistration_receipt.v1" || error("unexpected preregistration schema")
    String(preregistration["sim_id"]) == SIM_ID || error("unexpected preregistration sim_id")
    Bool(preregistration["registered_before_builder_source"]) || error("builder source was not preregistered")
    String(preregistration["spec_sha256"]) == spec_hash || error("preregistration receipt does not bind the current spec")
    String(spec["classification"]) == CLASSIFICATION || error("classification ceiling drift")
    !Bool(spec["promotion_allowed"]) || error("promotion ceiling drift")
    !Bool(spec["formal_admission_allowed"]) || error("formal-admission ceiling drift")
    !Bool(spec["stage_movement_allowed"]) || error("stage-movement ceiling drift")
    spec, preregistration, spec_hash
end

function tool_manifest()
    Dict{String,Any}(
        "Graphs" => Dict(
            "tried" => true,
            "used" => true,
            "relevant" => true,
            "reason" => "load-bearing SimpleDiGraph quotient construction, exact edge verification, and strongly_connected_components receipt",
        ),
        "JSON3" => Dict(
            "tried" => true,
            "used" => true,
            "relevant" => true,
            "reason" => "load-bearing preregistration parsing and closed result round-trip validation before emission",
        ),
        "SHA" => Dict(
            "tried" => true,
            "used" => true,
            "relevant" => true,
            "reason" => "load-bearing fail-closed spec, receipt, source, and result-core provenance hashes",
        ),
        "Z3" => Dict(
            "tried" => false,
            "used" => false,
            "relevant" => false,
            "reason" => "the preregistered claim asks for direct exhaustive finite congruence, not an SMT proof claim",
        ),
        "JAX" => Dict(
            "tried" => false,
            "used" => false,
            "relevant" => false,
            "reason" => "independent peer lane; reading or invoking it would violate standalone Julia semantic ownership",
        ),
        "PyTorch" => Dict(
            "tried" => false,
            "used" => false,
            "relevant" => false,
            "reason" => "independent learned-perception peer lane; it cannot arbitrate exact quotient or basin semantics",
        ),
    )
end

function tool_integration_depth()
    Dict(
        "Graphs" => "load_bearing",
        "JSON3" => "load_bearing",
        "SHA" => "load_bearing",
    )
end

function tool_calls()
    [
        Dict(
            "tool" => "Graphs",
            "qualified_api/function" => "Graphs.SimpleDiGraph",
            "input_object" => "14-class exact quotient vertex set",
            "output_object" => "directed quotient graph",
            "positive_case" => "stable congruent partition constructs one vertex per behavioral class",
            "negative/erased_control" => "depth-zero and one-transition-mutated incongruent partitions are rejected before graph construction",
            "boundary_case" => "one-vertex zero-edge graph remains one SCC",
            "demotion_condition" => "vertex or edge set differs from the exact induced A/B maps",
            "gates" => ["quotient", "all_pass"],
        ),
        Dict(
            "tool" => "Graphs",
            "qualified_api/function" => "Graphs.add_edge!",
            "input_object" => "exact induced A and B class transitions",
            "output_object" => "union quotient edge set with separately retained action labels",
            "positive_case" => "every induced transition is present",
            "negative/erased_control" => "incongruent source classes have no accepted induced edge",
            "boundary_case" => "duplicate A/B source-destination pairs collapse only in the union graph while labels remain in the receipt",
            "demotion_condition" => "Graphs edge set differs from the independently enumerated transition pairs",
            "gates" => ["quotient", "all_pass"],
        ),
        Dict(
            "tool" => "Graphs",
            "qualified_api/function" => "Graphs.strongly_connected_components",
            "input_object" => "exact quotient union graph",
            "output_object" => "complete SCC partition of quotient classes",
            "positive_case" => "SCCs cover each quotient class exactly once",
            "negative/erased_control" => "missing graph vertices fail the coverage gate",
            "boundary_case" => "singleton graph SCC is exactly [0] after external zero-based conversion",
            "demotion_condition" => "SCC output does not cover the exact quotient vertex set",
            "gates" => ["quotient", "all_pass"],
        ),
        Dict(
            "tool" => "JSON3",
            "qualified_api/function" => "JSON3.read",
            "input_object" => "spec.json, preregistration_receipt.json, and tentative closed result bytes",
            "output_object" => "schema-checked preregistration objects and round-trip result object",
            "positive_case" => "registered fixture values and ceilings parse and gate exact tests",
            "negative/erased_control" => "schema, sim_id, ceiling, or spec-hash drift throws before result emission",
            "boundary_case" => "empty peer_result_files_read remains an empty JSON array",
            "demotion_condition" => "parsed expected values or round-trip fields differ from the in-memory exact result",
            "gates" => ["all_pass", "divergence", "quotient"],
        ),
        Dict(
            "tool" => "JSON3",
            "qualified_api/function" => "JSON3.write",
            "input_object" => "self-contained Julia result dictionary",
            "output_object" => "closed JSON result bytes",
            "positive_case" => "tentative and final bytes round-trip with schema, sim_id, and all_pass intact",
            "negative/erased_control" => "no file is written if either round-trip validation fails",
            "boundary_case" => "nothing values and empty arrays serialize as closed JSON null/array values",
            "demotion_condition" => "result cannot be parsed back or required fields are absent",
            "gates" => ["all_pass"],
        ),
        Dict(
            "tool" => "SHA",
            "qualified_api/function" => "SHA.sha256",
            "input_object" => "preregistered inputs, Julia source, and serialized result core",
            "output_object" => "hexadecimal provenance hashes",
            "positive_case" => "spec hash equals the preregistered frozen hash",
            "negative/erased_control" => "any spec drift aborts before finite analysis",
            "boundary_case" => "source and preregistration files are independently hashed",
            "demotion_condition" => "frozen spec hash or receipt binding fails",
            "gates" => ["all_pass"],
        ),
    ]
end

function main()
    spec, preregistration, spec_hash = read_preregistered_inputs()
    expected = spec["expected_controller_fixture_values"]

    action_a = [eca_step(state, RULE_A) for state in 0:(STATE_COUNT - 1)]
    action_b = [eca_step(state, RULE_B) for state in 0:(STATE_COUNT - 1)]
    initial_two_probe = observation_partition(state -> (hamming_weight(state), domain_walls(state)))
    initial_weight_only = observation_partition(state -> hamming_weight(state))
    two_probe_history = refinement_history(initial_two_probe, action_a, action_b, MAX_REFINEMENT_DEPTH)
    weight_only_history = refinement_history(initial_weight_only, action_a, action_b, MAX_REFINEMENT_DEPTH)
    stable_partition = last(two_probe_history)
    independent_rotation_orbits = rotation_orbits()

    stable_quotient = quotient_congruence(stable_partition, action_a, action_b)
    stable_quotient.congruent || error("stable behavioral partition is not an exact A/B congruence")
    false_quotient = quotient_congruence(initial_two_probe, action_a, action_b)
    quotient_graph = graph_receipt(stable_quotient.induced_a, stable_quotient.induced_b)

    a_after_b = [action_a[action_b[state + 1] + 1] for state in 0:(STATE_COUNT - 1)]
    b_after_a = [action_b[action_a[state + 1] + 1] for state in 0:(STATE_COUNT - 1)]
    a_after_b_receipt = functional_graph_receipt(a_after_b)
    b_after_a_receipt = functional_graph_receipt(b_after_a)
    noncommuting_states = [state for state in 0:(STATE_COUNT - 1) if a_after_b[state + 1] != b_after_a[state + 1]]

    relabel, inverse = relabel_permutation(1)
    relabeled_a = conjugate_transition(action_a, relabel, inverse)
    relabeled_b = conjugate_transition(action_b, relabel, inverse)
    relabeled_history = refinement_history(initial_two_probe, relabeled_a, relabeled_b, MAX_REFINEMENT_DEPTH)
    relabeled_stable_pullback = pullback_partition(last(relabeled_history), inverse)
    relabeled_a_after_b = [relabeled_a[relabeled_b[state + 1] + 1] for state in 0:(STATE_COUNT - 1)]
    relabeled_b_after_a = [relabeled_b[relabeled_a[state + 1] + 1] for state in 0:(STATE_COUNT - 1)]
    relabeled_a_after_b_receipt = functional_graph_receipt(relabeled_a_after_b)
    relabeled_b_after_a_receipt = functional_graph_receipt(relabeled_b_after_a)
    mutation_control = mutated_transition_control(stable_partition, action_a, action_b)

    two_probe_counts = length.(two_probe_history)
    weight_only_counts = length.(weight_only_history)
    expected_two_probe_counts = Int.(collect(expected["behavioral_class_count_by_depth_two_probe"]))
    expected_weight_only_counts = Int.(collect(expected["behavioral_class_count_by_depth_weight_only"]))
    expected_a_b_basins = Int.(collect(expected["A_after_B_sorted_basin_sizes"]))
    expected_b_a_basins = Int.(collect(expected["B_after_A_sorted_basin_sizes"]))

    relabel_control_pass = relabeled_stable_pullback == stable_partition &&
        relabeled_a_after_b_receipt["sorted_basin_sizes"] == a_after_b_receipt["sorted_basin_sizes"] &&
        relabeled_b_after_a_receipt["sorted_basin_sizes"] == b_after_a_receipt["sorted_basin_sizes"] &&
        relabeled_a_after_b_receipt["attractor_count"] == a_after_b_receipt["attractor_count"] &&
        relabeled_b_after_a_receipt["attractor_count"] == b_after_a_receipt["attractor_count"]

    tests = Dict{String,Bool}(
        "T1_behavioral_objects" => two_probe_counts == expected_two_probe_counts && first_stable_depth(two_probe_history) == 1,
        "T2_rotation_identity" => stable_partition == independent_rotation_orbits,
        "T3_semiconjugacy" => stable_quotient.congruent && !isempty(false_quotient.conflicts_a) &&
            !isempty(false_quotient.conflicts_b) && Bool(quotient_graph["passed"]),
        "T4_order_teeth" => length(noncommuting_states) == Int(expected["action_noncommuting_state_count"]) &&
            a_after_b_receipt["sorted_basin_sizes"] != b_after_a_receipt["sorted_basin_sizes"],
        "T5_attractor_structure" => a_after_b_receipt["attractor_count"] == Int(expected["A_after_B_attractor_count"]) &&
            b_after_a_receipt["attractor_count"] == Int(expected["B_after_A_attractor_count"]) &&
            a_after_b_receipt["sorted_basin_sizes"] == expected_a_b_basins &&
            b_after_a_receipt["sorted_basin_sizes"] == expected_b_a_basins &&
            Bool(a_after_b_receipt["all_states_assigned_once"]) && Bool(b_after_a_receipt["all_states_assigned_once"]),
        "T6_probe_ablation" => weight_only_counts == expected_weight_only_counts &&
            first_stable_depth(weight_only_history) > first_stable_depth(two_probe_history) &&
            length(initial_weight_only) < length(initial_two_probe),
        "T7_relabel_control" => relabel_control_pass,
        "T9_engine_removal" => false,
    )
    controls = Dict{String,Any}(
        "depth_zero_false_quotient" => Dict(
            "passed" => !false_quotient.congruent && !isempty(false_quotient.conflicts_a) && !isempty(false_quotient.conflicts_b),
            "class_count" => length(initial_two_probe),
            "conflicts_A" => false_quotient.conflicts_a,
            "conflicts_B" => false_quotient.conflicts_b,
        ),
        "weight_only_probe_ablation" => Dict(
            "passed" => tests["T6_probe_ablation"],
            "class_count_by_depth" => weight_only_counts,
            "first_stable_depth" => first_stable_depth(weight_only_history),
        ),
        "cyclic_state_relabeling" => Dict(
            "passed" => relabel_control_pass,
            "shift" => 1,
            "pulled_back_stable_partition" => relabeled_stable_pullback,
            "A_after_B_sorted_basin_sizes" => relabeled_a_after_b_receipt["sorted_basin_sizes"],
            "B_after_A_sorted_basin_sizes" => relabeled_b_after_a_receipt["sorted_basin_sizes"],
        ),
        "action_reversal" => Dict(
            "passed" => tests["T4_order_teeth"],
            "differing_states" => noncommuting_states,
            "differing_state_count" => length(noncommuting_states),
        ),
        "mutated_transition_breaks_original_quotient" => mutation_control,
    )
    controls_pass = all(Bool(controls[name]["passed"]) for name in (
        "depth_zero_false_quotient",
        "weight_only_probe_ablation",
        "cyclic_state_relabeling",
        "action_reversal",
    )) && Bool(mutation_control["quotient_broken"])
    scientific_pass = all(values(tests)) && controls_pass

    manifest = tool_manifest()
    integration_depth = tool_integration_depth()
    state_table = [Dict(
        "state" => state,
        "bits_site_5_to_0" => bitstring(UInt8(state))[3:8],
        "weight" => hamming_weight(state),
        "domain_walls" => domain_walls(state),
        "A_rule30_successor" => action_a[state + 1],
        "B_rule110_successor" => action_b[state + 1],
        "behavioral_class" => class_ids(stable_partition)[state + 1] - 1,
        "rotation_canonical" => minimum(rotate_state(state, shift) for shift in 0:(RING_SIZE - 1)),
    ) for state in 0:(STATE_COUNT - 1)]

    result = Dict{String,Any}(
        "schema" => "codex_ratchet.finite_probe_behavioral_object_engine.julia_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "semantic_role" => "semantic_owner",
        "ran" => true,
        "source_path" => relpath(SOURCE_PATH, REPO_ROOT),
        "result_path" => relpath(RESULT_PATH, REPO_ROOT),
        "reads_peer_result" => false,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "stage_movement_allowed" => false,
        "claim_ceiling" => String(spec["claim_ceiling"]),
        "blocked_consumers" => String.(collect(spec["blocked_consumers"])),
        "all_pass" => false,
        "scientific_pass_before_closed_json_gate" => scientific_pass,
        "closed_json_validation" => Dict("passed" => false, "phase" => "tentative_round_trip"),
        "input_provenance" => Dict(
            "spec_path" => relpath(SPEC_PATH, REPO_ROOT),
            "preregistration_receipt_path" => relpath(PREREGISTRATION_PATH, REPO_ROOT),
            "registered_at" => String(preregistration["registered_at"]),
            "registered_before_builder_source" => Bool(preregistration["registered_before_builder_source"]),
            "independent_spec_read" => true,
            "peer_result_files_read" => String[],
        ),
        "hashes" => Dict(
            "spec_sha256" => spec_hash,
            "expected_spec_sha256" => EXPECTED_SPEC_SHA256,
            "preregistration_receipt_sha256" => sha256_file(PREREGISTRATION_PATH),
            "run_julia_sha256" => sha256_file(SOURCE_PATH),
        ),
        "engine_contract" => Dict(
            "mode" => "julia_semantic_owner_lane",
            "role" => "semantic_owner",
            "required_packages" => ["Graphs", "JSON3"],
            "removal_demotion" => "without this exact Julia receipt, behavioral-object, quotient-congruence, SCC, cycle, and basin claims are not gated",
        ),
        "foreign_runtime_manifest" => Dict(
            "julia" => Dict(
                "project" => Base.active_project(),
                "version" => string(VERSION),
                "packages" => Dict("Graphs" => string(Base.pkgversion(Graphs)), "JSON3" => string(Base.pkgversion(JSON3))),
                "role" => "semantic_owner",
            ),
            "jax" => Dict("role" => "independent_batched_exhaustive_peer", "read" => false),
            "pytorch" => Dict("role" => "independent_learned_perception_peer", "read" => false),
            "tensor_exchange" => "none",
        ),
        "packages_used" => ["Graphs", "JSON3", "SHA"],
        "aligned_packages_load_bearing" => ["Graphs", "JSON3"],
        "TOOL_MANIFEST" => manifest,
        "TOOL_INTEGRATION_DEPTH" => integration_depth,
        "tool_manifest" => manifest,
        "tool_integration_depth" => integration_depth,
        "tool_calls" => tool_calls(),
        "fixture" => Dict(
            "ring_size" => RING_SIZE,
            "state_count" => STATE_COUNT,
            "state_encoding" => "integer 0..63, bit i is ring site i",
            "ECA_neighborhood_order" => "left-center-right encoded as 4*left+2*center+right; rule bit at that index",
            "A_rule" => RULE_A,
            "B_rule" => RULE_B,
            "state_table" => state_table,
        ),
        "behavioral_refinement" => Dict(
            "two_probe_class_count_by_depth" => two_probe_counts,
            "two_probe_first_stable_depth" => first_stable_depth(two_probe_history),
            "two_probe_partitions_by_depth" => two_probe_history,
            "stable_partition" => stable_partition,
            "weight_only_class_count_by_depth" => weight_only_counts,
            "weight_only_first_stable_depth" => first_stable_depth(weight_only_history),
            "weight_only_partitions_by_depth" => weight_only_history,
        ),
        "presentation_symmetry" => Dict(
            "group" => "cyclic rotations C6",
            "independently_computed_rotation_orbits" => independent_rotation_orbits,
            "equals_stable_behavioral_partition" => stable_partition == independent_rotation_orbits,
        ),
        "exact_quotient" => Dict(
            "congruent" => stable_quotient.congruent,
            "induced_A_rule30" => stable_quotient.induced_a,
            "induced_B_rule110" => stable_quotient.induced_b,
            "graph" => quotient_graph,
        ),
        "functional_graphs" => Dict(
            "A_after_B" => a_after_b_receipt,
            "B_after_A" => b_after_a_receipt,
            "noncommuting_states" => noncommuting_states,
            "noncommuting_state_count" => length(noncommuting_states),
        ),
        "controls" => controls,
        "tests" => tests,
        "test_scope" => Dict(
            "julia_gated" => ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T9_exact_object_and_basin_only"],
            "excluded_peer_test" => "T8 learned reidentification belongs only to the independent PyTorch lane",
            "peer_controls_not_run" => ["shuffled PyTorch targets", "erased ring edges for PyG"],
        ),
        "divergence_log" => [
            "The depth-zero two-probe partition is non-congruent under both A and B.",
            "Weight-only observation starts strictly coarser and stabilizes later.",
            "A_after_B and B_after_A differ on the preregistered finite state count and have different basin signatures.",
            "A single deterministic transition mutation breaks the original stable quotient.",
            "No JAX, PyTorch, controller result, or peer result artifact is read.",
        ],
        "witness_trace" => Dict(
            "trace_id" => "finite_probe_behavioral_object_engine_v0_julia_exact_trace_v1",
            "inputs" => [relpath(SPEC_PATH, REPO_ROOT), relpath(PREREGISTRATION_PATH, REPO_ROOT)],
            "transforms" => [
                "enumerate all 64 six-bit ring states",
                "apply synchronous ECA rules 30 and 110",
                "refine exact probe partitions through depth six",
                "compute C6 rotation orbits independently",
                "check exact quotient congruence",
                "construct Graphs.SimpleDiGraph quotient and SCCs",
                "enumerate exact cycles and basins for both composite schedules",
                "run preregistered controls and JSON3 round-trip gate",
            ],
            "negatives_run" => collect(keys(controls)),
            "final_classification" => CLASSIFICATION,
        ),
        "lego_contract" => Dict(
            "tier" => 1,
            "purpose" => "finite behavioral-object and exact-attractor instrument probe",
            "scientific_question" => "whether exact finite observations refine to a symmetry-identical congruence with order-sensitive attractor basins",
            "sim_execution_kind" => "classical",
            "sim_class" => "constraint_probe",
            "root_constraints_in_force" => ["finite bounded carrier", "order-sensitive action compositions"],
            "carrier_layer" => "all 64 states of a periodic six-site binary ring",
            "geometry_layer" => "cyclic presentation symmetry C6 only",
            "bridge_layer" => "none",
            "cut_layer" => "none",
            "law_or_candidate_tested" => "exact behavioral refinement and semiconjugate quotient under ECA rules 30 and 110",
            "branch_status_before_run" => "preregistered scratch diagnostic",
            "required_tools" => ["Graphs", "JSON3"],
            "actual_tools_used" => ["Graphs", "JSON3", "SHA"],
            "proof_surfaces_used" => ["exact exhaustive finite congruence", "exact functional-graph enumeration"],
            "graph_surfaces_used" => ["Graphs.SimpleDiGraph", "Graphs.strongly_connected_components"],
            "topology_surfaces_used" => String[],
            "required_inputs" => ["spec.json", "preregistration_receipt.json"],
            "data_or_artifact_dependencies" => String[],
            "required_negatives" => [
                "depth-zero false quotient",
                "weight-only probe ablation",
                "cyclic state relabeling",
                "action reversal",
                "one mutated transition that must break the original quotient",
            ],
            "negatives_run" => collect(keys(controls)),
            "kill_conditions" => ["fixture mismatch", "non-congruent stable quotient", "rotation-orbit mismatch", "control false-green", "closed JSON failure"],
            "required_artifacts" => [relpath(RESULT_PATH, REPO_ROOT)],
            "artifacts_emitted" => [relpath(RESULT_PATH, REPO_ROOT)],
            "witness_trace_id" => "finite_probe_behavioral_object_engine_v0_julia_exact_trace_v1",
            "pass_rule" => "all Julia-scoped preregistered tests, controls, provenance gates, Graphs gates, and JSON3 closed-result gate pass",
            "fail_rule" => "any mismatch keeps all_pass false or aborts before result emission",
            "promotion_status" => "diagnostic_only",
            "eligible_consumers" => ["bounded controller comparison for this exact fixture"],
            "blocked_consumers" => String.(collect(spec["blocked_consumers"])),
        ),
    )

    result_core = JSON3.write(result)
    result["hashes"]["result_core_sha256"] = sha256_text(result_core)
    tentative = JSON3.write(result)
    tentative_round_trip = JSON3.read(tentative)
    tentative_ok = String(tentative_round_trip["schema"]) == String(result["schema"]) &&
        String(tentative_round_trip["sim_id"]) == SIM_ID &&
        !Bool(tentative_round_trip["all_pass"]) &&
        isempty(collect(tentative_round_trip["input_provenance"]["peer_result_files_read"]))
    tentative_ok || error("JSON3 tentative closed-result round-trip gate failed")

    result["closed_json_validation"] = Dict(
        "passed" => true,
        "phase" => "tentative_and_final_round_trip",
        "required_fields" => ["schema", "sim_id", "engine", "all_pass", "hashes", "TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH", "tool_calls"],
    )
    result["all_pass"] = scientific_pass && tentative_ok
    final_json = JSON3.write(result)
    final_round_trip = JSON3.read(final_json)
    final_ok = String(final_round_trip["schema"]) == String(result["schema"]) &&
        String(final_round_trip["sim_id"]) == SIM_ID &&
        Bool(final_round_trip["all_pass"]) == Bool(result["all_pass"]) &&
        Bool(final_round_trip["closed_json_validation"]["passed"])
    final_ok || error("JSON3 final closed-result round-trip gate failed")

    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        write(io, final_json)
        write(io, "\n")
    end
    println(JSON3.write(Dict(
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "all_pass" => result["all_pass"],
        "result_path" => RESULT_PATH,
    )))
end

main()
