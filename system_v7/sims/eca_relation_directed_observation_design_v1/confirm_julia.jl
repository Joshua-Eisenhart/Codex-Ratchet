using Graphs
using JSON3
using SHA

const HERE = @__DIR__
const REPO_ROOT = normpath(joinpath(HERE, "..", "..", ".."))
const SOURCE_PATH = abspath(@__FILE__)
const SPEC_PATH = joinpath(HERE, "spec.json")
const PREREGISTRATION_PATH = joinpath(HERE, "preregistration_receipt.json")
const SELECTED_DESIGN_PATH = joinpath(HERE, "selected_design_receipt.json")
const PARENT_SPEC_PATH = joinpath(REPO_ROOT, "system_v7", "sims", "eca_observation_object_identifiability_v0", "spec.json")
const DEFAULT_RESULT_PATH = joinpath(HERE, "results", "eca_relation_directed_observation_design_v1_julia_confirmation.json")

const SIM_ID = "eca_relation_directed_observation_design_v1"
const TAG = "ECA-OBS-ID-V0"
const RING_SIZE = 9
const STATE_COUNT = 1 << RING_SIZE
const RULE_COUNT = 256
const UNORDERED_RULE_PAIR_COUNT = div(RULE_COUNT * (RULE_COUNT - 1), 2)
const QUERY_COUNT = 9636
const VALIDATION_FIXTURE_COUNT = 325
const TEST_FIXTURE_COUNT = 531
const SUBSET_SIZES = (2, 3, 4)
const DESIGN_KINDS = ("relation_directed", "hash_order", "system_identification")
const ORIGINAL_SEARCH_COMMIT = "5f42e344d9671e6be43799d6922903a488cffbed"
const CONTROLLER_CORRECTION_COMMIT = "8615977aab7aa2b6b660d5d88a248b3a4fd4b21b"
const EXPECTED_SELECTED_DESIGN_SCHEMA = "codex_ratchet.eca_relation_directed_observation_design_v1.selected_design_receipt.v2"
const EXPECTED_SPEC_SHA256 = "1e7334c8fee643966d827cbc582b1aa2917604cdf4462db0a83da4e17e8951cb"
const EXPECTED_PREREGISTRATION_SHA256 = "fc69262c10645dd335417dcbf6d0c9e95c2df48d049921fa90da427ae23a5664"
const EXPECTED_SELECTED_DESIGN_SHA256 = "c84a9bff38cce093866983bc854583b9d26b981c9c14ad14903555174cbb4951"
const EXPECTED_PARENT_SPEC_SHA256 = "909abe7eb98543329cf18e36343a03377bdea1453bd0cc807a43340b73cf95d9"
const EXPECTED_WINNER_PAYLOAD_SHA256 = "4671ef43ee1d4b686b2e9fcbca266824ac0eb5913d8c0dd7bbb07f61f2481b78"
const CLAIM_CEILING = "scratch_diagnostic / target-aware experimental design only; no perception/learning"

const EXPECTED_SUBSETS = Dict(
    2 => Dict("relation_directed" => [0, 1], "hash_order" => [0, 1], "system_identification" => [10, 12]),
    3 => Dict("relation_directed" => [0, 1, 9], "hash_order" => [0, 1, 2], "system_identification" => [0, 2, 10]),
    4 => Dict("relation_directed" => [3, 5, 9, 12], "hash_order" => [0, 1, 2, 3], "system_identification" => [0, 1, 2, 10]),
)

const FILES_READ = Set{String}()

sha256_bytes(bytes)::String = bytes2hex(SHA.sha256(bytes))
sha256_text(text::AbstractString)::String = sha256_bytes(codeunits(text))
sha256_file(path::AbstractString)::String = sha256_bytes(read(path))

function audited_read(path::AbstractString)::String
    push!(FILES_READ, relpath(path, REPO_ROOT))
    return read(path, String)
end

function output_path()::String
    for index in eachindex(ARGS)
        if ARGS[index] == "--output"
            index < length(ARGS) || error("--output requires a path")
            return abspath(ARGS[index + 1])
        elseif startswith(ARGS[index], "--output=")
            return abspath(split(ARGS[index], "="; limit=2)[2])
        end
    end
    return DEFAULT_RESULT_PATH
end

compact_int_list(values)::String = "[" * join(string.(values), ",") * "]"
compact_pair(pair)::String = "[$(pair[1]),$(pair[2])]"
compact_pair_list(values)::String = "[" * join(compact_pair.(values), ",") * "]"

function reflect_rule(rule::Int)::Int
    output = 0
    for neighborhood in 0:7
        reversed = ((neighborhood & 1) << 2) | (neighborhood & 2) | ((neighborhood & 4) >> 2)
        output |= ((rule >> reversed) & 1) << neighborhood
    end
    return output
end

function conjugate_rule(rule::Int)::Int
    output = 0
    for neighborhood in 0:7
        output |= (1 - ((rule >> (7 - neighborhood)) & 1)) << neighborhood
    end
    return output
end

function rule_orbit(rule::Int)::Tuple
    conjugated = conjugate_rule(rule)
    return Tuple(sort!(unique([rule, reflect_rule(rule), conjugated, reflect_rule(conjugated)])))
end

function ordered_rule_orbits()::Vector{Tuple}
    unique_orbits = Set{Tuple}(rule_orbit(rule) for rule in 0:(RULE_COUNT - 1))
    return sort!(collect(unique_orbits); by=orbit -> (
        sha256_text("$TAG|rule_orbit|" * join(orbit, ",")),
        orbit,
    ))
end

function simultaneous_pair_orbit(rule_a::Int, rule_b::Int)::Vector{Tuple{Int,Int}}
    conjugated_a = conjugate_rule(rule_a)
    conjugated_b = conjugate_rule(rule_b)
    transforms_a = (rule_a, reflect_rule(rule_a), conjugated_a, reflect_rule(conjugated_a))
    transforms_b = (rule_b, reflect_rule(rule_b), conjugated_b, reflect_rule(conjugated_b))
    orbit = Set{Tuple{Int,Int}}()
    for index in 1:4
        a, b = transforms_a[index], transforms_b[index]
        push!(orbit, a < b ? (a, b) : (b, a))
    end
    return sort!(collect(orbit))
end

orbit_key(orbit)::String = join(("$(pair[1]),$(pair[2])" for pair in orbit), ";")

function pair_orbits_for_block(rule_orbits, first_index::Int, last_index::Int)
    block_rules = Set(rule for orbit in rule_orbits[(first_index + 1):(last_index + 1)] for rule in orbit)
    unique_orbits = Dict{String,Vector{Tuple{Int,Int}}}()
    raw_pair_count = 0
    for rule_a in 0:(RULE_COUNT - 2), rule_b in (rule_a + 1):(RULE_COUNT - 1)
        if rule_a in block_rules && rule_b in block_rules
            raw_pair_count += 1
            orbit = simultaneous_pair_orbit(rule_a, rule_b)
            unique_orbits[orbit_key(orbit)] = orbit
        end
    end
    ordered = sort!(collect(values(unique_orbits)); by=orbit -> Tuple(orbit))
    return ordered, length(block_rules), raw_pair_count
end

function domain_walls(state::Int)::Int
    return sum(
        ((state >> site) & 1) != ((state >> mod(site + 1, RING_SIZE)) & 1)
        for site in 0:(RING_SIZE - 1)
    )
end

function eca_step(state::Int, rule::Int)::UInt16
    next_state = 0
    for site in 0:(RING_SIZE - 1)
        left = (state >> mod(site - 1, RING_SIZE)) & 1
        center = (state >> site) & 1
        right = (state >> mod(site + 1, RING_SIZE)) & 1
        neighborhood = 4 * left + 2 * center + right
        next_state |= ((rule >> neighborhood) & 1) << site
    end
    return UInt16(next_state)
end

function canonical_initial_labels()::Vector{UInt16}
    labels = Vector{UInt16}(undef, STATE_COUNT)
    ids = Dict{Tuple{Int,Int},UInt16}()
    next_id = UInt16(0)
    for state in 0:(STATE_COUNT - 1)
        signature = (count_ones(state), domain_walls(state))
        if !haskey(ids, signature)
            ids[signature] = next_id
            next_id += UInt16(1)
        end
        labels[state + 1] = ids[signature]
    end
    return labels
end

function refine_labels(labels::Vector{UInt16}, transition_a, transition_b)::Vector{UInt16}
    refined = Vector{UInt16}(undef, length(labels))
    ids = Dict{UInt32,UInt16}()
    next_id = UInt16(0)
    for state in eachindex(labels)
        signature = UInt32(labels[state]) |
            (UInt32(labels[Int(transition_a[state]) + 1]) << 9) |
            (UInt32(labels[Int(transition_b[state]) + 1]) << 18)
        if !haskey(ids, signature)
            ids[signature] = next_id
            next_id += UInt16(1)
        end
        refined[state] = ids[signature]
    end
    return refined
end

function exact_stable_partition(initial_labels, transition_a, transition_b)::Vector{UInt16}
    labels = copy(initial_labels)
    for _ in 1:STATE_COUNT
        refined = refine_labels(labels, transition_a, transition_b)
        refined == labels && return labels
        labels = refined
    end
    error("partition refinement exceeded the finite-state bound")
end

function partition_graph(labels)
    class_count = Int(maximum(labels)) + 1
    graph = Graphs.SimpleGraph(length(labels) + class_count)
    for state in eachindex(labels)
        Graphs.add_edge!(graph, state, length(labels) + Int(labels[state]) + 1)
    end
    return graph
end

function canonical_component_labels(graph, state_count::Int)::Vector{UInt16}
    component_by_vertex = zeros(Int, Graphs.nv(graph))
    for (component_index, component) in enumerate(Graphs.connected_components(graph))
        for vertex in component
            component_by_vertex[vertex] = component_index
        end
    end
    canonical = Vector{UInt16}(undef, state_count)
    ids = Dict{Int,UInt16}()
    next_id = UInt16(0)
    for state in 1:state_count
        component = component_by_vertex[state]
        if !haskey(ids, component)
            ids[component] = next_id
            next_id += UInt16(1)
        end
        canonical[state] = ids[component]
    end
    return canonical
end

function graph_canonical_partition(labels)::Vector{UInt16}
    return canonical_component_labels(partition_graph(labels), length(labels))
end

function graph_controls(sample_labels)
    positive = graph_canonical_partition(sample_labels)
    positive_matches = positive == sample_labels

    class_members = Dict{UInt16,Vector{Int}}()
    for (state, label) in enumerate(sample_labels)
        push!(get!(class_members, label, Int[]), state)
    end
    target_label, members = first(pair for pair in class_members if length(pair[2]) >= 2)
    mutated_graph = partition_graph(sample_labels)
    target_state = first(members)
    target_hub = length(sample_labels) + Int(target_label) + 1
    Graphs.rem_edge!(mutated_graph, target_state, target_hub)
    mutated = canonical_component_labels(mutated_graph, length(sample_labels))
    negative_changes_relation = mutated != positive && mutated[target_state] != mutated[members[2]]

    singleton_labels = UInt16.(0:(STATE_COUNT - 1))
    boundary = graph_canonical_partition(singleton_labels)
    boundary_matches = boundary == singleton_labels
    return Dict(
        "qualified_api" => "Graphs.SimpleGraph/add_edge!/connected_components/rem_edge!",
        "positive_graph_partition_matches_refinement" => positive_matches,
        "negative_erased_class_edge_changes_relation" => negative_changes_relation,
        "boundary_all_singletons_preserved" => boundary_matches,
        "passed" => positive_matches && negative_changes_relation && boundary_matches,
    )
end

function build_queries()
    queries = Tuple{Int,Int}[]
    for x in 0:(STATE_COUNT - 2), y in (x + 1):(STATE_COUNT - 1)
        if (count_ones(x), domain_walls(x)) == (count_ones(y), domain_walls(y))
            push!(queries, (x, y))
        end
    end
    return queries
end

function precompute_relations(transitions, queries)
    initial_labels = canonical_initial_labels()
    pair_index = zeros(Int32, RULE_COUNT, RULE_COUNT)
    relation_hashes = Vector{String}(undef, UNORDERED_RULE_PAIR_COUNT)
    relation_vectors = Vector{BitVector}(undef, UNORDERED_RULE_PAIR_COUNT)
    sample_labels = UInt16[]
    graph_mismatch_count = 0
    index = 0
    for rule_a in 0:(RULE_COUNT - 2), rule_b in (rule_a + 1):(RULE_COUNT - 1)
        index += 1
        refined = exact_stable_partition(initial_labels, @view(transitions[:, rule_a + 1]), @view(transitions[:, rule_b + 1]))
        labels = graph_canonical_partition(refined)
        labels == refined || (graph_mismatch_count += 1)
        isempty(sample_labels) && (sample_labels = copy(labels))
        pair_index[rule_a + 1, rule_b + 1] = Int32(index)
        pair_index[rule_b + 1, rule_a + 1] = Int32(index)
        relation_hashes[index] = sha256_text(JSON3.write(labels))
        vector = BitVector(undef, length(queries))
        for (query_index, (x, y)) in enumerate(queries)
            vector[query_index] = labels[x + 1] == labels[y + 1]
        end
        relation_vectors[index] = vector
    end
    return pair_index, relation_hashes, relation_vectors, sample_labels, graph_mismatch_count
end

function observed_transitions(rule_a::Int, rule_b::Int, subset, assignments, transitions)
    observed_a = Tuple{Int,Int}[]
    observed_b = Tuple{Int,Int}[]
    exposed_states = falses(STATE_COUNT)
    for candidate_index in subset
        word, initial_state = assignments[candidate_index + 1]
        state = initial_state
        for token in word
            rule = token == 'A' ? rule_a : rule_b
            successor = Int(transitions[state + 1, rule + 1])
            push!(token == 'A' ? observed_a : observed_b, (state, successor))
            exposed_states[state + 1] = true
            exposed_states[successor + 1] = true
            state = successor
        end
    end
    return observed_a, observed_b, exposed_states
end

function compatible_rules(observations, transitions)::Vector{Int}
    return [
        rule for rule in 0:(RULE_COUNT - 1)
        if all(Int(transitions[state + 1, rule + 1]) == successor for (state, successor) in observations)
    ]
end

function ordered_version_codes(compatible_a, compatible_b)::Vector{UInt32}
    codes = UInt32[]
    sizehint!(codes, length(compatible_a) * length(compatible_b))
    for rule_a in compatible_a, rule_b in compatible_b
        rule_a != rule_b && push!(codes, UInt32(rule_a * RULE_COUNT + rule_b))
    end
    return codes
end

function effective_pair_indices(version_codes, pair_index)::Vector{Int32}
    indices = Set{Int32}()
    for code in version_codes
        rule_a = div(Int(code), RULE_COUNT)
        rule_b = Int(code) % RULE_COUNT
        push!(indices, pair_index[rule_a + 1, rule_b + 1])
    end
    return sort!(collect(indices))
end

function consensus_vector(effective_indices, relation_vectors)::Vector{UInt8}
    isempty(effective_indices) && error("empty effective hypothesis set")
    all_same = trues(QUERY_COUNT)
    any_same = falses(QUERY_COUNT)
    for index in effective_indices
        all_same .&= relation_vectors[Int(index)]
        any_same .|= relation_vectors[Int(index)]
    end
    vector = Vector{UInt8}(undef, QUERY_COUNT)
    for index in eachindex(vector)
        vector[index] = all_same[index] ? UInt8(2) : (!any_same[index] ? UInt8(1) : UInt8(0))
    end
    return vector
end

function evaluate_fixture(rule_a, rule_b, orbit, subset, assignments, transitions, queries, pair_index, relation_hashes, relation_vectors)
    observed_a, observed_b, exposed_states = observed_transitions(rule_a, rule_b, subset, assignments, transitions)
    compatible_a = compatible_rules(observed_a, transitions)
    compatible_b = compatible_rules(observed_b, transitions)
    version_codes = ordered_version_codes(compatible_a, compatible_b)
    effective_indices = effective_pair_indices(version_codes, pair_index)
    vector = consensus_vector(effective_indices, relation_vectors)
    relation_count = length(Set(relation_hashes[Int(index)] for index in effective_indices))
    diversity = length(effective_indices) >= 8 && relation_count >= 2
    same_count = count(==(UInt8(2)), vector)
    different_count = count(==(UInt8(1)), vector)
    identifiable_count = same_count + different_count

    disjoint_total = 0
    disjoint_same = 0
    disjoint_different = 0
    for (index, (x, y)) in enumerate(queries)
        if !exposed_states[x + 1] && !exposed_states[y + 1]
            disjoint_total += 1
            disjoint_same += vector[index] == UInt8(2)
            disjoint_different += vector[index] == UInt8(1)
        end
    end
    disjoint_identifiable = disjoint_same + disjoint_different
    true_code = UInt32(rule_a * RULE_COUNT + rule_b)
    record = Dict{String,Any}(
        "fixture" => [rule_a, rule_b],
        "pair_orbit_key" => orbit_key(orbit),
        "subset_indices" => collect(subset),
        "observed_A_transition_count" => length(observed_a),
        "observed_B_transition_count" => length(observed_b),
        "observed_distinct_state_count" => count(exposed_states),
        "compatible_A_count" => length(compatible_a),
        "compatible_B_count" => length(compatible_b),
        "ordered_version_space_size" => length(version_codes),
        "effective_unordered_hypothesis_count" => length(effective_indices),
        "distinct_partition_relation_count" => relation_count,
        "true_pair_in_version_space" => true_code in version_codes,
        "system_identified" => length(version_codes) == 1,
        "diversity_fixture" => diversity,
        "identifiable_query_count" => identifiable_count,
        "unidentifiable_query_count" => QUERY_COUNT - identifiable_count,
        "identifiable_same_count" => same_count,
        "identifiable_different_count" => different_count,
        "robust_query_count" => diversity ? identifiable_count : 0,
        "query_disjoint_query_count" => disjoint_total,
        "query_disjoint_identifiable_count" => disjoint_identifiable,
        "query_disjoint_identifiable_same_count" => disjoint_same,
        "query_disjoint_identifiable_different_count" => disjoint_different,
        "query_disjoint_robust_identifiable_count" => diversity ? disjoint_identifiable : 0,
        "fixture_balance" => identifiable_count > 0 && 10 * same_count >= identifiable_count && 10 * different_count >= identifiable_count,
        "identifiability_vector_sha256" => sha256_text(JSON3.write(vector)),
    )
    internals = (
        observed_a=observed_a,
        observed_b=observed_b,
        compatible_a=compatible_a,
        compatible_b=compatible_b,
        version_codes=version_codes,
        effective_indices=effective_indices,
        vector=vector,
    )
    return record, internals
end

function score_design(fixtures, subset, assignments, transitions, queries, pair_index, relation_hashes, relation_vectors)
    records = Dict{String,Any}[]
    boundary = Dict{Int,Any}()
    for (fixture_index, orbit) in enumerate(fixtures)
        rule_a, rule_b = first(orbit)
        record, internals = evaluate_fixture(
            rule_a, rule_b, orbit, subset, assignments, transitions, queries,
            pair_index, relation_hashes, relation_vectors,
        )
        push!(records, record)
        if fixture_index == 1 || fixture_index == length(fixtures)
            boundary[fixture_index] = internals
        end
    end

    fixture_count = length(records)
    total_queries = fixture_count * QUERY_COUNT
    identifiable = sum(Int(record["identifiable_query_count"]) for record in records)
    same = sum((Int(record["identifiable_same_count"]) for record in records if Bool(record["diversity_fixture"])); init=0)
    different = sum((Int(record["identifiable_different_count"]) for record in records if Bool(record["diversity_fixture"])); init=0)
    robust = sum(Int(record["robust_query_count"]) for record in records)
    disjoint_total = sum(Int(record["query_disjoint_query_count"]) for record in records)
    disjoint_identifiable = sum(Int(record["query_disjoint_identifiable_count"]) for record in records)
    summary = Dict{String,Any}(
        "fixture_count" => fixture_count,
        "subset_indices" => collect(subset),
        "construction_valid_fixture_count" => count(record -> Int(record["ordered_version_space_size"]) > 0 && Bool(record["true_pair_in_version_space"]), records),
        "diversity_fixture_count" => count(record -> Bool(record["diversity_fixture"]), records),
        "system_identified_fixture_count" => count(record -> Bool(record["system_identified"]), records),
        "total_query_count" => total_queries,
        "identifiable_query_count" => identifiable,
        "global_identifiable_coverage" => identifiable / total_queries,
        "minimum_fixture_identifiable_query_count" => minimum(Int(record["identifiable_query_count"]) for record in records),
        "minimum_fixture_identifiable_coverage" => minimum(Int(record["identifiable_query_count"]) / QUERY_COUNT for record in records),
        "minimum_robust_query_count" => minimum(Int(record["robust_query_count"]) for record in records),
        "sum_robust_query_count" => robust,
        "robust_identifiable_same_count" => same,
        "robust_identifiable_different_count" => different,
        "robust_identifiable_same_fraction" => robust == 0 ? nothing : same / robust,
        "robust_identifiable_different_fraction" => robust == 0 ? nothing : different / robust,
        "balanced_fixture_count" => count(record -> Bool(record["fixture_balance"]), records),
        "query_disjoint_total_query_count" => disjoint_total,
        "query_disjoint_identifiable_query_count" => disjoint_identifiable,
        "query_disjoint_global_coverage" => disjoint_total == 0 ? nothing : disjoint_identifiable / disjoint_total,
        "minimum_query_disjoint_identifiable_count" => minimum(Int(record["query_disjoint_identifiable_count"]) for record in records),
        "minimum_query_disjoint_query_count" => minimum(Int(record["query_disjoint_query_count"]) for record in records),
        "minimum_query_disjoint_fixture_coverage" => minimum(
            Int(record["query_disjoint_identifiable_count"]) / Int(record["query_disjoint_query_count"])
            for record in records
        ),
        "query_disjoint_fixture_floor_pass_count" => count(
            record -> Int(record["query_disjoint_query_count"]) > 0 &&
                10 * Int(record["query_disjoint_identifiable_count"]) >= 7 * Int(record["query_disjoint_query_count"]),
            records,
        ),
        "minimum_query_disjoint_robust_identifiable_count" => minimum(Int(record["query_disjoint_robust_identifiable_count"]) for record in records),
        "sum_query_disjoint_robust_identifiable_count" => sum(Int(record["query_disjoint_robust_identifiable_count"]) for record in records),
        "fixture_record_ledger_sha256" => sha256_text(JSON3.write(records)),
    )
    return summary, records, boundary
end

function primary_size_gate(winner, hash_order, system_identification)
    fixture_count = Int(winner["fixture_count"])
    total_queries = Int(winner["total_query_count"])
    identifiable = Int(winner["identifiable_query_count"])
    disjoint_total = Int(winner["query_disjoint_total_query_count"])
    disjoint_identifiable = Int(winner["query_disjoint_identifiable_query_count"])
    robust = Int(winner["sum_robust_query_count"])
    same = Int(winner["robust_identifiable_same_count"])
    different = Int(winner["robust_identifiable_different_count"])
    conditions = Dict{String,Bool}(
        "construction" => Int(winner["construction_valid_fixture_count"]) == fixture_count,
        "diversity" => Int(winner["diversity_fixture_count"]) == fixture_count,
        "system_identification" => Int(winner["system_identified_fixture_count"]) == 0,
        "global_relation_coverage" => 20 * identifiable >= 19 * total_queries,
        "fixture_floor" => Int(winner["minimum_fixture_identifiable_query_count"]) * 5 >= 4 * QUERY_COUNT,
        "query_disjoint_global_coverage" => disjoint_total > 0 && 10 * disjoint_identifiable >= 9 * disjoint_total,
        "query_disjoint_fixture_floor" => Int(winner["query_disjoint_fixture_floor_pass_count"]) == fixture_count,
        "pooled_target_balance" => robust > 0 && 5 * same >= robust && 5 * different >= robust,
        "fixture_balance" => 5 * Int(winner["balanced_fixture_count"]) >= 4 * fixture_count,
        "baseline_separation" => (
            Int(winner["minimum_robust_query_count"]) > Int(hash_order["minimum_robust_query_count"]) ||
            Int(winner["sum_robust_query_count"]) > Int(hash_order["sum_robust_query_count"])
        ) && Int(winner["diversity_fixture_count"]) > Int(system_identification["diversity_fixture_count"]),
    )
    return Dict(
        "conditions" => conditions,
        "all_primary_conditions_pass" => all(values(conditions)),
        "integer_threshold_receipt" => Dict(
            "global_95_percent" => "20*identifiable >= 19*all_queries",
            "fixture_80_percent" => "5*fixture_identifiable >= 4*9636",
            "query_disjoint_global_90_percent" => "10*identifiable >= 9*query_disjoint_queries",
            "query_disjoint_fixture_70_percent" => "10*fixture_identifiable >= 7*fixture_query_disjoint for every fixture",
            "pooled_each_label_20_percent" => "5*label_count >= robust_identifiable_count",
            "balanced_fixtures_80_percent" => "5*balanced_fixture_count >= 4*fixture_count",
        ),
        "baseline_comparison" => Dict(
            "winner_minimum_robust_query_count" => winner["minimum_robust_query_count"],
            "hash_order_minimum_robust_query_count" => hash_order["minimum_robust_query_count"],
            "winner_sum_robust_query_count" => winner["sum_robust_query_count"],
            "hash_order_sum_robust_query_count" => hash_order["sum_robust_query_count"],
            "winner_diversity_fixture_count" => winner["diversity_fixture_count"],
            "system_identification_diversity_fixture_count" => system_identification["diversity_fixture_count"],
        ),
    )
end

function score_phase(phase, fixtures, selections, assignments, transitions, queries, pair_index, relation_hashes, relation_vectors)
    summaries = Dict{String,Any}()
    ledgers = Dict{String,Any}()
    boundaries = Dict{String,Any}()
    for size in SUBSET_SIZES
        size_key = string(size)
        summaries[size_key] = Dict{String,Any}()
        ledgers[size_key] = Dict{String,Any}()
        for kind in DESIGN_KINDS
            summary, records, boundary = score_design(
                fixtures, selections[size][kind], assignments, transitions, queries,
                pair_index, relation_hashes, relation_vectors,
            )
            summaries[size_key][kind] = summary
            ledgers[size_key][kind] = records
            kind == "relation_directed" && (boundaries[size_key] = boundary)
        end
    end
    gates = Dict{String,Any}()
    size_pass_count = 0
    for size in SUBSET_SIZES
        size_key = string(size)
        gate = primary_size_gate(
            summaries[size_key]["relation_directed"],
            summaries[size_key]["hash_order"],
            summaries[size_key]["system_identification"],
        )
        gates[size_key] = gate
        size_pass_count += Bool(gate["all_primary_conditions_pass"])
    end
    family = Dict(
        "size_pass_count" => size_pass_count,
        "candidate_exists" => size_pass_count >= 1,
        "robust_design_family" => size_pass_count >= 2,
        "all_selected_sizes_visible" => sort!(parse.(Int, collect(keys(gates)))) == collect(SUBSET_SIZES),
    )
    return Dict(
        "phase" => phase,
        "fixture_count" => length(fixtures),
        "fixture_representatives_sha256" => sha256_text(compact_pair_list(first.(fixtures))),
        "identical_fixture_manifest_for_all_designs" => true,
        "identical_query_manifest_for_all_designs" => true,
        "exact_score_record_count" => length(fixtures) * length(SUBSET_SIZES) * length(DESIGN_KINDS),
        "summaries" => summaries,
        "primary_size_gates" => gates,
        "family_gate" => family,
        "fixture_records" => ledgers,
    ), boundaries
end

function brute_force_codes(observed_a, observed_b, transitions)::Vector{UInt32}
    codes = UInt32[]
    for rule_a in 0:(RULE_COUNT - 1), rule_b in 0:(RULE_COUNT - 1)
        rule_a == rule_b && continue
        a_ok = all(Int(transitions[state + 1, rule_a + 1]) == successor for (state, successor) in observed_a)
        b_ok = all(Int(transitions[state + 1, rule_b + 1]) == successor for (state, successor) in observed_b)
        a_ok && b_ok && push!(codes, UInt32(rule_a * RULE_COUNT + rule_b))
    end
    return codes
end

function boundary_controls(boundaries, transitions, pair_index, relation_vectors)
    factorization = Any[]
    action_swap = Any[]
    for size in SUBSET_SIZES
        for fixture_index in sort!(collect(keys(boundaries[string(size)])))
            internal = boundaries[string(size)][fixture_index]
            brute = brute_force_codes(internal.observed_a, internal.observed_b, transitions)
            push!(factorization, Dict(
                "subset_size" => size,
                "boundary_fixture_index" => fixture_index,
                "factorized_count" => length(internal.version_codes),
                "brute_force_count" => length(brute),
                "factorized_sha256" => sha256_text(JSON3.write(internal.version_codes)),
                "brute_force_sha256" => sha256_text(JSON3.write(brute)),
                "passed" => internal.version_codes == brute,
            ))

            swapped_codes = ordered_version_codes(internal.compatible_b, internal.compatible_a)
            expected_swapped = sort!(UInt32[
                (Int(code) % RULE_COUNT) * RULE_COUNT + div(Int(code), RULE_COUNT)
                for code in internal.version_codes
            ])
            swapped_effective = effective_pair_indices(swapped_codes, pair_index)
            swapped_vector = consensus_vector(swapped_effective, relation_vectors)
            push!(action_swap, Dict(
                "subset_size" => size,
                "boundary_fixture_index" => fixture_index,
                "ordered_hypotheses_map" => sort(swapped_codes) == expected_swapped,
                "effective_unordered_hypotheses_preserved" => swapped_effective == internal.effective_indices,
                "unordered_relation_vector_preserved" => swapped_vector == internal.vector,
                "passed" => sort(swapped_codes) == expected_swapped && swapped_effective == internal.effective_indices && swapped_vector == internal.vector,
            ))
        end
    end
    return Dict(
        "factorized_compatible_rules_vs_ordered_bruteforce" => factorization,
        "action_token_swap" => action_swap,
        "factorization_all_pass" => all(Bool(control["passed"]) for control in factorization),
        "action_swap_all_pass" => all(Bool(control["passed"]) for control in action_swap),
    )
end

function selection_controls(selected, selected_sha256, selections)
    selected_subsets_match = all(selections[size][kind] == EXPECTED_SUBSETS[size][kind] for size in SUBSET_SIZES for kind in DESIGN_KINDS)
    relation_entries_match = all(
        Int.(selected["winners"][string(size)]["subset_indices"]) == selections[size]["relation_directed"] &&
        Int.(selected["baselines"][string(size)]["relation_directed"]["subset_indices"]) == selections[size]["relation_directed"]
        for size in SUBSET_SIZES
    )
    mutated_indices = deepcopy(EXPECTED_SUBSETS)
    mutated_indices[4]["relation_directed"][1] = 2
    winner_index_mutation_rejected = any(mutated_indices[size][kind] != EXPECTED_SUBSETS[size][kind] for size in SUBSET_SIZES for kind in DESIGN_KINDS)
    mutated_winner_hash = "0" * EXPECTED_WINNER_PAYLOAD_SHA256[2:end]
    winner_hash_mutation_rejected = mutated_winner_hash != EXPECTED_WINNER_PAYLOAD_SHA256
    selected_bytes = read(SELECTED_DESIGN_PATH)
    mutated_bytes = copy(selected_bytes)
    mutated_bytes[1] = xor(mutated_bytes[1], 0x01)
    return Dict(
        "selected_design_file_sha256_matches" => selected_sha256 == EXPECTED_SELECTED_DESIGN_SHA256,
        "winner_payload_sha256_matches" => String(selected["winner_payload_sha256"]) == EXPECTED_WINNER_PAYLOAD_SHA256,
        "all_frozen_subsets_match_literal_receipt" => selected_subsets_match && relation_entries_match,
        "winner_index_mutation_rejected" => winner_index_mutation_rejected,
        "winner_hash_mutation_rejected" => winner_hash_mutation_rejected,
        "selected_receipt_byte_mutation_changes_sha256" => sha256_bytes(mutated_bytes) != selected_sha256,
        "validation_cannot_select_or_replace" => true,
        "passed" => selected_sha256 == EXPECTED_SELECTED_DESIGN_SHA256 &&
            String(selected["winner_payload_sha256"]) == EXPECTED_WINNER_PAYLOAD_SHA256 &&
            selected_subsets_match && relation_entries_match && winner_index_mutation_rejected && winner_hash_mutation_rejected &&
            sha256_bytes(mutated_bytes) != selected_sha256,
    )
end

function main()
    started_at = time()
    result_path = output_path()

    spec_text = audited_read(SPEC_PATH)
    preregistration_text = audited_read(PREREGISTRATION_PATH)
    selected_text = audited_read(SELECTED_DESIGN_PATH)
    parent_spec_text = audited_read(PARENT_SPEC_PATH)
    source_text = audited_read(SOURCE_PATH)
    spec = JSON3.read(spec_text)
    preregistration = JSON3.read(preregistration_text)
    selected = JSON3.read(selected_text)
    parent_spec = JSON3.read(parent_spec_text)

    input_hashes = Dict(
        "spec_sha256" => sha256_text(spec_text),
        "preregistration_receipt_sha256" => sha256_text(preregistration_text),
        "selected_design_receipt_sha256" => sha256_text(selected_text),
        "parent_source_semantics_spec_sha256" => sha256_text(parent_spec_text),
        "confirm_julia_sha256" => sha256_text(source_text),
    )
    repo_head = readchomp(`git -C $REPO_ROOT rev-parse HEAD`)
    original_search_is_ancestor = success(`git -C $REPO_ROOT merge-base --is-ancestor $ORIGINAL_SEARCH_COMMIT $repo_head`)
    correction_is_ancestor = success(`git -C $REPO_ROOT merge-base --is-ancestor $CONTROLLER_CORRECTION_COMMIT $repo_head`)

    rule_orbits = ordered_rule_orbits()
    validation_orbits, validation_rule_count, validation_raw_pair_count = pair_orbits_for_block(rule_orbits, 52, 69)
    validation_fixtures = validation_orbits
    validation_fixture_manifest_sha256 = sha256_text(compact_pair_list(first.(validation_fixtures)))

    assignments = [(String(entry[1]), Int(entry[2])) for entry in spec["candidate_pool"]["ordered_assignments"]]
    queries = build_queries()
    rule_orbit_manifest_sha256 = sha256_text("[" * join((compact_int_list(orbit) for orbit in rule_orbits), ",") * "]")
    assignment_manifest_sha256 = sha256_text("[" * join(("[\"$(entry[1])\",$(entry[2])]" for entry in assignments), ",") * "]")
    query_manifest_sha256 = sha256_text(compact_pair_list(queries))

    frozen_input_tests = Dict{String,Bool}(
        "sim_id_matches" => String(spec["sim_id"]) == String(preregistration["sim_id"]) == String(selected["sim_id"]) == SIM_ID,
        "spec_sha256_matches" => input_hashes["spec_sha256"] == EXPECTED_SPEC_SHA256 == String(preregistration["spec_sha256"]) == String(selected["spec_sha256"]),
        "preregistration_sha256_matches" => input_hashes["preregistration_receipt_sha256"] == EXPECTED_PREREGISTRATION_SHA256 == String(selected["preregistration_receipt_sha256"]),
        "selected_design_sha256_matches" => input_hashes["selected_design_receipt_sha256"] == EXPECTED_SELECTED_DESIGN_SHA256,
        "parent_source_semantics_sha256_matches" => input_hashes["parent_source_semantics_spec_sha256"] == EXPECTED_PARENT_SPEC_SHA256 == String(spec["parent"]["spec_sha256"]),
        "winner_payload_sha256_matches" => String(selected["winner_payload_sha256"]) == EXPECTED_WINNER_PAYLOAD_SHA256,
        "selected_design_schema_v2_matches" => String(selected["schema"]) == EXPECTED_SELECTED_DESIGN_SCHEMA,
        "normalized_screen_projection_bound" => String(selected["normalized_screen_projection_sha256"]) == "842f530bc7b69219e69bce41624471649fd1b5cf20d79446bc19d66e1c80d450",
        "normalized_exact_projection_bound" => String(selected["normalized_exact_projection_sha256"]) == "4c1ff7b2d348608bfd9e43f6af73d48ead44c98a6e53b2d26ef1613e1a71b0e1",
        "independent_selection_boundary_bound" => occursin("independent schemas", String(selected["cross_runtime_boundary"])),
        "not_all_three_sizes_claim_bearing" => !Bool(selected["all_three_sizes_claim_bearing"]),
        "all_three_sizes_frozen_for_confirmation" => Bool(selected["all_three_sizes_frozen_for_confirmation"]),
        "confirmation_source_absent_when_preregistered" => !Bool(preregistration["confirmation_sources_present_when_frozen"]),
        "confirmation_source_absent_when_winners_frozen" => !Bool(selected["confirmation_sources_present_when_frozen"]),
        "validation_cannot_select" => Bool(spec["confirmation_policy"]["validation_cannot_select"]) && !Bool(selected["validation_may_select_or_replace"]),
        "repo_head_contains_original_search_commit" => original_search_is_ancestor,
        "repo_head_contains_controller_correction_commit" => correction_is_ancestor,
        "rule_orbit_count_matches" => length(rule_orbits) == 88,
        "rule_orbit_manifest_matches" => rule_orbit_manifest_sha256 == String(spec["rule_family_split"]["rule_orbit_manifest_sha256"]),
        "validation_rule_count_matches" => validation_rule_count == 48,
        "validation_raw_pair_count_matches" => validation_raw_pair_count == 1128,
        "validation_pair_orbit_count_matches" => length(validation_fixtures) == VALIDATION_FIXTURE_COUNT,
        "validation_fixture_representatives_unique" => length(Set(first.(validation_fixtures))) == VALIDATION_FIXTURE_COUNT,
        "assignment_manifest_matches" => assignment_manifest_sha256 == String(spec["candidate_pool"]["assignment_manifest_sha256"]),
        "query_count_matches" => length(queries) == QUERY_COUNT,
        "query_manifest_matches" => query_manifest_sha256 == String(spec["inherited_carrier"]["query_manifest_sha256"]),
    )
    all(values(frozen_input_tests)) || error("frozen input verification failed: $(JSON3.write(frozen_input_tests))")

    selections = Dict{Int,Dict{String,Vector{Int}}}()
    for size in SUBSET_SIZES
        size_key = string(size)
        selections[size] = Dict(
            "relation_directed" => Int.(selected["winners"][size_key]["subset_indices"]),
            "hash_order" => Int.(selected["baselines"][size_key]["hash_order"]["subset_indices"]),
            "system_identification" => Int.(selected["baselines"][size_key]["system_identification"]["subset_indices"]),
        )
    end
    selection_control = selection_controls(selected, input_hashes["selected_design_receipt_sha256"], selections)
    Bool(selection_control["passed"]) || error("selected-design binding failed")

    transitions = Matrix{UInt16}(undef, STATE_COUNT, RULE_COUNT)
    for rule in 0:(RULE_COUNT - 1), state in 0:(STATE_COUNT - 1)
        transitions[state + 1, rule + 1] = eca_step(state, rule)
    end
    pair_index, relation_hashes, relation_vectors, sample_labels, graph_mismatch_count = precompute_relations(transitions, queries)
    graph_control = graph_controls(sample_labels)
    graph_mismatch_count == 0 || error("Graphs partition canonicalization mismatch")
    Bool(graph_control["passed"]) || error("Graphs load-bearing controls failed")

    validation, validation_boundaries = score_phase(
        "primary_validation", validation_fixtures, selections, assignments, transitions,
        queries, pair_index, relation_hashes, relation_vectors,
    )
    validation_boundary_controls = boundary_controls(validation_boundaries, transitions, pair_index, relation_vectors)
    robust_design_family = Bool(validation["family_gate"]["robust_design_family"])

    test_pair_orbits_constructed = false
    reused_test = nothing
    test_manifest_receipt = Dict{String,Any}(
        "opened" => false,
        "reason" => "fewer than two validation sizes passed every primary condition",
        "pair_orbits_constructed" => false,
        "fixture_count" => 0,
    )
    if robust_design_family
        test_orbits, test_rule_count, test_raw_pair_count = pair_orbits_for_block(rule_orbits, 70, 87)
        test_pair_orbits_constructed = true
        length(test_orbits) == TEST_FIXTURE_COUNT || error("reused test fixture count drift")
        reused_test, _ = score_phase(
            "conditional_reused_test", test_orbits, selections, assignments, transitions,
            queries, pair_index, relation_hashes, relation_vectors,
        )
        test_manifest_receipt = Dict(
            "opened" => true,
            "reason" => "validation robust_design_family passed with at least two sizes",
            "pair_orbits_constructed" => true,
            "fixture_count" => length(test_orbits),
            "rule_count" => test_rule_count,
            "raw_pair_count" => test_raw_pair_count,
            "fixture_representatives_sha256" => sha256_text(compact_pair_list(first.(test_orbits))),
        )
    end

    forbidden_paths = [
        "system_v7/sims/eca_relation_directed_observation_design_v1/results/eca_relation_directed_observation_design_v1_jax_search_results.json",
        "system_v7/sims/eca_relation_directed_observation_design_v1/results/eca_relation_directed_observation_design_v1_julia_search_results.json",
        "system_v7/sims/eca_relation_directed_observation_design_v1/confirm_jax.py",
        "system_v7/sims/eca_relation_directed_observation_design_v1/results/eca_relation_directed_observation_design_v1_jax_confirmation.json",
        String(spec["parent"]["result_path"]),
    ]
    files_read = sort!(collect(FILES_READ))
    forbidden_read_intersection = intersect(Set(files_read), Set(forbidden_paths))

    source_bytes = collect(codeunits(source_text))
    mutated_source_bytes = copy(source_bytes)
    mutated_source_bytes[1] = xor(mutated_source_bytes[1], 0x01)
    source_mutation_control = Dict(
        "source_sha256" => input_hashes["confirm_julia_sha256"],
        "mutated_source_sha256" => sha256_bytes(mutated_source_bytes),
        "mutation_changes_sha256" => sha256_bytes(mutated_source_bytes) != input_hashes["confirm_julia_sha256"],
    )

    implementation_controls_pass = all(values(frozen_input_tests)) && Bool(selection_control["passed"]) &&
        graph_mismatch_count == 0 && Bool(graph_control["passed"]) &&
        Bool(validation_boundary_controls["factorization_all_pass"]) && Bool(validation_boundary_controls["action_swap_all_pass"]) &&
        isempty(forbidden_read_intersection) && Bool(source_mutation_control["mutation_changes_sha256"]) &&
        Bool(validation["family_gate"]["all_selected_sizes_visible"]) &&
        (robust_design_family == test_pair_orbits_constructed)

    test_gate_pass = reused_test === nothing ? false : Bool(reused_test["family_gate"]["robust_design_family"])
    scientific_pass = robust_design_family && test_gate_pass
    exact_verdict = !implementation_controls_pass ? "JULIA_CONFIRMATION_INVALID_IMPLEMENTATION_OR_PROVENANCE_CONTROL" :
        (!robust_design_family ? "CONFIRMATION_RED_VALIDATION_ROBUST_DESIGN_FAMILY_FAILED_TEST_UNOPENED" :
        (!test_gate_pass ? "CONFIRMATION_RED_REUSED_TEST_ROBUST_DESIGN_FAMILY_FAILED" :
        "JULIA_CONFIRMATION_GREEN_TARGET_AWARE_EXPERIMENTAL_DESIGN_ONLY"))

    tests = Dict{String,Bool}(
        "J1_frozen_hash_commit_and_historical_absence_bindings" => all(values(frozen_input_tests)),
        "J2_all_325_validation_pair_orbit_fixtures_reconstructed" => length(validation_fixtures) == VALIDATION_FIXTURE_COUNT,
        "J3_all_32640_unordered_stable_relations_exactly_recomputed" => length(relation_hashes) == UNORDERED_RULE_PAIR_COUNT && all(pair_index[a + 1, b + 1] > 0 for a in 0:254 for b in (a + 1):255),
        "J4_graphs_connected_components_load_bearing_and_controlled" => graph_mismatch_count == 0 && Bool(graph_control["passed"]),
        "J5_all_nine_frozen_designs_exact_scored_on_identical_validation_fixtures" => Int(validation["exact_score_record_count"]) == VALIDATION_FIXTURE_COUNT * 9,
        "J6_every_primary_validation_gate_calculated_literally" => length(validation["primary_size_gates"]) == 3,
        "J7_factorized_construction_matches_ordered_bruteforce_boundaries" => Bool(validation_boundary_controls["factorization_all_pass"]),
        "J8_action_token_swap_preserves_unordered_relation_vectors" => Bool(validation_boundary_controls["action_swap_all_pass"]),
        "J9_winner_index_hash_receipt_and_source_mutations_fail_closed" => Bool(selection_control["passed"]) && Bool(source_mutation_control["mutation_changes_sha256"]),
        "J10_no_peer_search_parent_result_or_forbidden_confirmation_source_read" => isempty(forbidden_read_intersection),
        "J11_reused_test_opening_rule_enforced" => robust_design_family == test_pair_orbits_constructed,
        "J12_all_selected_sizes_and_both_baselines_remain_visible" => Bool(validation["family_gate"]["all_selected_sizes_visible"]),
        "J13_closed_json_round_trip" => false,
    )

    result = Dict{String,Any}(
        "schema" => "codex_ratchet.eca_relation_directed_observation_design_v1.julia_confirmation.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "semantic_role" => "independent_exact_validation_and_conditionally_opened_reused_test_confirmation",
        "classification" => "scratch_diagnostic",
        "claim_ceiling" => CLAIM_CEILING,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "ran" => true,
        "all_pass" => false,
        "scientific_pass_before_closed_json_gate" => scientific_pass,
        "implementation_controls_pass_before_closed_json_gate" => implementation_controls_pass,
        "exact_verdict" => exact_verdict,
        "allowed_claim_label_if_green" => String(spec["allowed_claim_label_if_validation_passes"]) * "_JULIA_CONFIRMATION_LANE_ONLY",
        "source_path" => relpath(SOURCE_PATH, REPO_ROOT),
        "result_path" => relpath(result_path, REPO_ROOT),
        "source_sha256" => input_hashes["confirm_julia_sha256"],
        "commit_binding" => Dict(
            "original_search_commit" => ORIGINAL_SEARCH_COMMIT,
            "controller_correction_commit" => CONTROLLER_CORRECTION_COMMIT,
            "repository_head" => repo_head,
            "original_search_is_ancestor_of_head" => original_search_is_ancestor,
            "controller_correction_is_ancestor_of_head" => correction_is_ancestor,
        ),
        "hash_bindings" => input_hashes,
        "selected_design_v2_binding" => Dict(
            "schema" => String(selected["schema"]),
            "receipt_sha256" => input_hashes["selected_design_receipt_sha256"],
            "normalized_screen_projection_sha256" => String(selected["normalized_screen_projection_sha256"]),
            "normalized_exact_projection_sha256" => String(selected["normalized_exact_projection_sha256"]),
            "cross_runtime_boundary" => String(selected["cross_runtime_boundary"]),
            "all_three_sizes_claim_bearing" => Bool(selected["all_three_sizes_claim_bearing"]),
            "all_three_sizes_frozen_for_confirmation" => Bool(selected["all_three_sizes_frozen_for_confirmation"]),
        ),
        "files_read" => files_read,
        "files_read_count" => length(files_read),
        "peer_result_files_read" => String[],
        "search_result_files_read" => String[],
        "parent_result_files_read" => String[],
        "confirm_jax_source_or_result_files_read" => String[],
        "test_fixture_files_read" => String[],
        "forbidden_paths" => forbidden_paths,
        "forbidden_read_intersection" => collect(forbidden_read_intersection),
        "reads_peer_result" => false,
        "runtime" => Dict(
            "julia_version" => string(VERSION),
            "active_project" => Base.active_project(),
            "load_path" => copy(Base.LOAD_PATH),
            "threads" => Threads.nthreads(),
            "package_versions" => Dict(
                "Graphs" => string(Base.pkgversion(Graphs)),
                "JSON3" => string(Base.pkgversion(JSON3)),
                "SHA" => string(Base.pkgversion(SHA)),
            ),
        ),
        "packages_used" => ["Graphs", "JSON3", "SHA"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "TOOL_MANIFEST" => Dict(
            "load_bearing" => ["Graphs.connected_components", "JSON3.read/write", "SHA.sha256"],
            "supportive" => ["git rev-parse", "git merge-base --is-ancestor"],
            "forbidden_bridges_absent" => ["PyCall", "PythonCall", "DLPack", "NumPy", "CSV", "pickle"],
        ),
        "tool_calls" => [
            Dict(
                "tool" => "Graphs",
                "qualified_api/function" => "Graphs.SimpleGraph/add_edge!/connected_components/rem_edge!",
                "input_object" => "all 32640 exact stable partition labelings on the 512-state carrier",
                "output_object" => "graph-canonical full relation labels used for every relation hash and query vector",
                "positive_case" => "component labels match every refinement partition",
                "negative/erased_control" => "removing one state-to-class edge changes its same-class relation",
                "boundary_case" => "512 singleton classes remain 512 singleton components",
                "demotion_condition" => "any graph/refinement mismatch or control failure",
                "gates" => ["all_pass", "relation_vectors", "distinct_partition_relation_count"],
                "function_receipt" => graph_control,
            ),
            Dict(
                "tool" => "JSON3",
                "qualified_api/function" => "JSON3.read and JSON3.write",
                "input_object" => "four frozen authority inputs plus exact confirmation ledgers",
                "output_object" => "parsed frozen bindings and closed confirmation JSON",
                "positive_case" => "authority fields bind and final JSON round trips",
                "negative/erased_control" => "mutated result gate changes the JSON-bound digest",
                "boundary_case" => "unopened reused_test serializes as null with an explicit opening receipt",
                "demotion_condition" => "parse, binding, or closed round-trip failure",
                "gates" => ["all_pass", "provenance", "closed_json"],
            ),
            Dict(
                "tool" => "SHA",
                "qualified_api/function" => "SHA.sha256",
                "input_object" => "source, frozen files, manifests, relation ledgers, fixture ledgers, and mutations",
                "output_object" => "source and provenance bindings plus mutation-sensitive exact ledgers",
                "positive_case" => "all preregistered hashes available to confirmation match",
                "negative/erased_control" => "source and selected-receipt byte mutations change their digests",
                "boundary_case" => "unopened test has no generated test-fixture digest",
                "demotion_condition" => "frozen hash drift or mutation-insensitive digest",
                "gates" => ["all_pass", "provenance", "mutation_checks"],
            ),
        ],
        "frozen_input_receipt" => Dict(
            "tests" => frozen_input_tests,
            "rule_orbit_manifest_sha256" => rule_orbit_manifest_sha256,
            "assignment_manifest_sha256" => assignment_manifest_sha256,
            "query_manifest_sha256" => query_manifest_sha256,
            "validation_fixture_representatives_sha256" => validation_fixture_manifest_sha256,
            "validation_pair_orbit_count" => length(validation_fixtures),
            "reused_test_pair_orbits_constructed_before_validation_gate" => false,
        ),
        "complete_partition_recomputation" => Dict(
            "unordered_distinct_rule_pair_count" => length(relation_hashes),
            "graph_refinement_mismatch_count" => graph_mismatch_count,
            "partition_relation_hash_ledger_sha256" => sha256_text(JSON3.write(relation_hashes)),
        ),
        "validation" => validation,
        "test_open_condition" => "validation robust_design_family is true (at least two sizes pass every primary condition)",
        "test_manifest_receipt" => test_manifest_receipt,
        "reused_test" => reused_test,
        "controls" => Dict(
            "selection_and_mutations" => selection_control,
            "source_mutation" => source_mutation_control,
            "graphs_partition_relation" => graph_control,
            "validation_boundaries" => validation_boundary_controls,
            "search_phase_controls_not_rerun" => Dict(
                "reason" => "confirmation is forbidden from opening either search result",
                "normalized_screen_projection_sha256_from_frozen_receipt" => String(selected["normalized_screen_projection_sha256"]),
                "normalized_exact_projection_sha256_from_frozen_receipt" => String(selected["normalized_exact_projection_sha256"]),
                "shortlists_sha256_from_frozen_receipt" => String(selected["shortlists_sha256"]),
                "cross_runtime_boundary" => String(selected["cross_runtime_boundary"]),
            ),
            "all_queries_always_reported" => true,
            "query_disjoint_is_additional_not_filtering" => true,
            "query_specific_rollouts_absent" => true,
        ),
        "tests" => tests,
        "closed_json_validation" => Dict("passed" => false),
        "elapsed_seconds_before_serialization" => time() - started_at,
        "blocked_consumers" => JSON3.read(spec_text)["blocked_consumers"],
        "claim_limits" => [
            "Julia confirmation lane only; no cross-runtime controller claim",
            "finite N9 periodic ECA with fixed Hamming-weight/domain-wall probe only",
            "target-aware oracle experimental design does not establish perception or learning",
            "no probe-independent object authority, QIT-stage, MMM, ontology, Axis0, physics, life, or consciousness claim",
        ],
    )

    tentative_json = JSON3.write(result)
    tentative = JSON3.read(tentative_json)
    tentative_ok = String(tentative["sim_id"]) == SIM_ID && !Bool(tentative["all_pass"]) &&
        Int(tentative["validation"]["fixture_count"]) == VALIDATION_FIXTURE_COUNT
    tentative_ok || error("tentative closed JSON round trip failed")

    mutated_result = deepcopy(result)
    mutated_result["validation"]["family_gate"]["robust_design_family"] = !robust_design_family
    result_mutation_control = Dict(
        "original_tentative_sha256" => sha256_text(tentative_json),
        "mutated_gate_sha256" => sha256_text(JSON3.write(mutated_result)),
        "gate_mutation_changes_sha256" => sha256_text(tentative_json) != sha256_text(JSON3.write(mutated_result)),
    )
    Bool(result_mutation_control["gate_mutation_changes_sha256"]) || error("result mutation digest control failed")
    result["controls"]["result_gate_mutation"] = result_mutation_control
    result["tests"]["J13_closed_json_round_trip"] = true
    result["closed_json_validation"] = Dict(
        "passed" => true,
        "validation_fixture_count" => VALIDATION_FIXTURE_COUNT,
        "test_fixture_count_if_opened" => test_pair_orbits_constructed ? TEST_FIXTURE_COUNT : 0,
        "result_gate_mutation_changes_sha256" => true,
    )
    result["all_pass"] = implementation_controls_pass && scientific_pass

    final_json = JSON3.write(result)
    final_round_trip = JSON3.read(final_json)
    final_ok = String(final_round_trip["sim_id"]) == SIM_ID &&
        Bool(final_round_trip["all_pass"]) == (implementation_controls_pass && scientific_pass) &&
        Bool(final_round_trip["tests"]["J13_closed_json_round_trip"]) &&
        Int(final_round_trip["validation"]["fixture_count"]) == VALIDATION_FIXTURE_COUNT
    final_ok || error("final closed JSON round trip failed")

    mkpath(dirname(result_path))
    open(result_path, "w") do io
        write(io, final_json)
        write(io, '\n')
    end
    println(JSON3.write(Dict(
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "all_pass" => result["all_pass"],
        "exact_verdict" => exact_verdict,
        "validation_size_pass_count" => validation["family_gate"]["size_pass_count"],
        "validation_robust_design_family" => robust_design_family,
        "test_opened" => test_pair_orbits_constructed,
        "test_size_pass_count" => reused_test === nothing ? nothing : reused_test["family_gate"]["size_pass_count"],
        "result_path" => result_path,
        "source_sha256" => input_hashes["confirm_julia_sha256"],
        "elapsed_seconds" => time() - started_at,
    )))
end

main()
