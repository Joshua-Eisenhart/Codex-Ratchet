using JSON3
using SHA

const HERE = @__DIR__
const REPO_ROOT = normpath(joinpath(HERE, "..", "..", ".."))
const SOURCE_PATH = abspath(@__FILE__)
const SPEC_PATH = joinpath(HERE, "spec.json")
const CARD_PATH = joinpath(HERE, "wizard_v4_3_object_card.json")
const RECEIPT_PATH = joinpath(HERE, "preregistration_receipt.json")
const SIM_ID = "eca_observation_object_identifiability_v0"
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const TAG = "ECA-OBS-ID-V0"
const RING_SIZE = 9
const STATE_COUNT = 1 << RING_SIZE
const RULE_COUNT = 256
const EXPECTED_PAIR_COUNT = div(RULE_COUNT * (RULE_COUNT - 1), 2)
const EXPECTED_FIXTURE_COUNT = 531
const EXPECTED_QUERY_COUNT = 9636
const BUDGETS = (1, 2, 4, 8, 16)
const CLAIM_CEILING = "EXACT_JULIA_ECA_PARTIAL_OBSERVATION_OBJECT_IDENTIFIABILITY_CENSUS_LANE_ONLY"

sha256_bytes(bytes)::String = bytes2hex(SHA.sha256(bytes))
sha256_text(text::AbstractString)::String = sha256_bytes(codeunits(text))
sha256_file(path::AbstractString)::String = sha256_bytes(read(path))

function output_path()::String
    for index in eachindex(ARGS)
        if ARGS[index] == "--output"
            index < length(ARGS) || error("--output requires a path")
            return abspath(ARGS[index + 1])
        elseif startswith(ARGS[index], "--output=")
            return abspath(split(ARGS[index], "="; limit=2)[2])
        end
    end
    return joinpath(HERE, "results", "$(SIM_ID)_julia_results.json")
end

compact_int_list(values)::String = "[" * join(string.(values), ",") * "]"
compact_pair(pair)::String = "[$(pair[1]),$(pair[2])]"
compact_pair_list(values)::String = "[" * join(compact_pair.(values), ",") * "]"
compact_orbit_list(values)::String = "[" * join((compact_pair_list(orbit) for orbit in values), ",") * "]"

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

orbit_key(orbit::Vector{Tuple{Int,Int}})::String = join(("$(pair[1]),$(pair[2])" for pair in orbit), ";")
pair_orbit_key(rule_a::Int, rule_b::Int)::String = let pair = first(simultaneous_pair_orbit(rule_a, rule_b)); "$(pair[1]),$(pair[2])" end

function build_frozen_manifests()
    orbits = ordered_rule_orbits()
    blocks = Dict(
        "train" => orbits[1:52],
        "validation" => orbits[53:70],
        "test" => orbits[71:88],
    )
    rule_block = Dict{Int,String}()
    for (block, block_orbits) in blocks, orbit in block_orbits, rule in orbit
        rule_block[rule] = block
    end
    pair_orbits = Dict{String,Vector{Vector{Tuple{Int,Int}}}}()
    counts = Dict{String,Any}()
    for block in ("train", "validation", "test")
        raw_pairs = Tuple{Int,Int}[]
        unique_orbits = Dict{String,Vector{Tuple{Int,Int}}}()
        for rule_a in 0:(RULE_COUNT - 2), rule_b in (rule_a + 1):(RULE_COUNT - 1)
            if rule_block[rule_a] == block && rule_block[rule_b] == block
                push!(raw_pairs, (rule_a, rule_b))
                orbit = simultaneous_pair_orbit(rule_a, rule_b)
                unique_orbits[orbit_key(orbit)] = orbit
            end
        end
        ordered = sort!(collect(values(unique_orbits)); by=orbit -> Tuple(orbit))
        pair_orbits[block] = ordered
        counts[block] = Dict(
            "rule_orbits" => length(blocks[block]),
            "rules" => length(Set(rule for orbit in blocks[block] for rule in orbit)),
            "raw_pairs" => length(raw_pairs),
            "simultaneous_pair_orbits" => length(ordered),
        )
    end
    assignments = Tuple{String,Int}[
        ("BAAA", 507), ("AAAA", 313), ("BAAB", 81), ("BBBB", 99),
        ("ABBA", 265), ("BABB", 3), ("AAAB", 196), ("AABB", 227),
        ("BABA", 89), ("BBAB", 0), ("AABA", 339), ("BBAA", 268),
        ("BBBA", 49), ("ABAA", 118), ("ABBB", 147), ("ABAB", 478),
    ]
    queries = Tuple{Int,Int}[]
    for x in 0:(STATE_COUNT - 2), y in (x + 1):(STATE_COUNT - 1)
        if (count_ones(x), domain_walls(x)) == (count_ones(y), domain_walls(y))
            push!(queries, (x, y))
        end
    end
    rule_orbit_json = "[" * join((compact_int_list(orbit) for orbit in orbits), ",") * "]"
    pair_orbit_json = "{" * join(("\"$block\":" * compact_orbit_list(pair_orbits[block]) for block in ("test", "train", "validation")), ",") * "}"
    assignment_json = "[" * join(("[\"$(entry[1])\",$(entry[2])]" for entry in assignments), ",") * "]"
    query_json = compact_pair_list(queries)
    return (
        orbits=orbits,
        blocks=blocks,
        pair_orbits=pair_orbits,
        counts=counts,
        assignments=assignments,
        queries=queries,
        hashes=Dict(
            "rule_orbits" => sha256_text(rule_orbit_json),
            "pair_orbits" => sha256_text(pair_orbit_json),
            "assignments" => sha256_text(assignment_json),
            "queries" => sha256_text(query_json),
        ),
    )
end

function verify_frozen_inputs(manifests)
    spec = JSON3.read(read(SPEC_PATH, String))
    card = JSON3.read(read(CARD_PATH, String))
    receipt = JSON3.read(read(RECEIPT_PATH, String))
    statement = String(card["primary_object_card"]["object_statement"])
    expected = spec["rule_family_split"]["expected_counts"]
    tests = Dict(
        "sim_id_matches" => String(spec["sim_id"]) == String(receipt["sim_id"]) == SIM_ID,
        "spec_sha256_matches" => sha256_file(SPEC_PATH) == String(receipt["spec_sha256"]),
        "object_card_sha256_matches" => sha256_file(CARD_PATH) == String(receipt["object_card_sha256"]),
        "object_statement_sha256_matches" => sha256_text(statement) == String(card["primary_object_card"]["object_statement_sha256"]),
        "builder_absent_when_frozen" => !Bool(receipt["builder_sources_present_when_frozen"]),
        "carrier_matches" => Int(spec["carrier"]["ring_size"]) == RING_SIZE && Int(spec["carrier"]["state_count"]) == STATE_COUNT,
        "rule_orbit_count_matches" => length(manifests.orbits) == 88,
        "test_fixture_count_matches" => length(manifests.pair_orbits["test"]) == EXPECTED_FIXTURE_COUNT,
        "query_count_matches" => length(manifests.queries) == EXPECTED_QUERY_COUNT,
        "block_counts_match" => all(
            manifests.counts[block][field] == Int(expected[block][field])
            for block in ("train", "validation", "test")
            for field in ("rule_orbits", "rules", "raw_pairs", "simultaneous_pair_orbits")
        ),
        "rule_orbit_manifest_matches" => manifests.hashes["rule_orbits"] == String(spec["rule_family_split"]["rule_orbit_manifest_sha256"]),
        "pair_orbit_manifest_matches" => manifests.hashes["pair_orbits"] == String(spec["rule_family_split"]["same_block_pair_orbit_manifest_sha256"]),
        "assignment_manifest_matches" => manifests.hashes["assignments"] == String(spec["observation_packet"]["word_state_assignment_sha256"]),
        "query_manifest_matches" => manifests.hashes["queries"] == String(spec["query_universe"]["query_manifest_sha256"]),
        "budgets_match" => Tuple(Int.(spec["observation_packet"]["cumulative_trajectory_budgets"])) == BUDGETS,
    )
    all(values(tests)) || error("frozen preregistration verification failed: $(JSON3.write(tests))")
    return Dict(
        "passed" => true,
        "verified_before_transition_or_partition_computation" => true,
        "tests" => tests,
        "hashes" => Dict(
            "spec_sha256" => sha256_file(SPEC_PATH),
            "object_card_sha256" => sha256_file(CARD_PATH),
            "preregistration_receipt_sha256" => sha256_file(RECEIPT_PATH),
            "rule_orbit_manifest_sha256" => manifests.hashes["rule_orbits"],
            "same_block_pair_orbit_manifest_sha256" => manifests.hashes["pair_orbits"],
            "word_state_assignment_sha256" => manifests.hashes["assignments"],
            "query_manifest_sha256" => manifests.hashes["queries"],
        ),
    )
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

function refine_labels(labels::Vector{UInt16}, transition_a::Vector{UInt16}, transition_b::Vector{UInt16})::Vector{UInt16}
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

function exact_stable_partition(initial_labels::Vector{UInt16}, transition_a::Vector{UInt16}, transition_b::Vector{UInt16})::Vector{UInt16}
    labels = copy(initial_labels)
    for _ in 1:STATE_COUNT
        refined = refine_labels(labels, transition_a, transition_b)
        refined == labels && return labels
        labels = refined
    end
    error("partition refinement exceeded finite-state bound")
end

function precompute_partitions(transitions::Vector{Vector{UInt16}}, initial_labels::Vector{UInt16})
    labels_by_pair = Matrix{UInt16}(undef, STATE_COUNT, EXPECTED_PAIR_COUNT)
    pair_index = zeros(Int32, RULE_COUNT, RULE_COUNT)
    relation_hashes = Vector{String}(undef, EXPECTED_PAIR_COUNT)
    index = 0
    swap_failures = Tuple{Int,Int}[]
    for rule_a in 0:(RULE_COUNT - 2), rule_b in (rule_a + 1):(RULE_COUNT - 1)
        index += 1
        labels = exact_stable_partition(initial_labels, transitions[rule_a + 1], transitions[rule_b + 1])
        swapped = exact_stable_partition(initial_labels, transitions[rule_b + 1], transitions[rule_a + 1])
        labels == swapped || push!(swap_failures, (rule_a, rule_b))
        labels_by_pair[:, index] = labels
        pair_index[rule_a + 1, rule_b + 1] = Int32(index)
        pair_index[rule_b + 1, rule_a + 1] = Int32(index)
        relation_hashes[index] = sha256_text(JSON3.write(labels))
    end
    return labels_by_pair, pair_index, relation_hashes, swap_failures
end

function observed_transitions(rule_a::Int, rule_b::Int, assignments, budget::Int, transitions)
    observed_a = Tuple{Int,Int}[]
    observed_b = Tuple{Int,Int}[]
    for (word, initial_state) in assignments[1:budget]
        state = initial_state
        for token in word
            rule = token == 'A' ? rule_a : rule_b
            successor = Int(transitions[rule + 1][state + 1])
            push!(token == 'A' ? observed_a : observed_b, (state, successor))
            state = successor
        end
    end
    return observed_a, observed_b
end

function compatible_rules(observations, transitions)::Vector{Int}
    return [
        rule for rule in 0:(RULE_COUNT - 1)
        if all(Int(transitions[rule + 1][state + 1]) == successor for (state, successor) in observations)
    ]
end

function ordered_version_codes(compatible_a::Vector{Int}, compatible_b::Vector{Int})::Vector{UInt32}
    codes = UInt32[]
    sizehint!(codes, length(compatible_a) * length(compatible_b))
    for rule_a in compatible_a, rule_b in compatible_b
        rule_a != rule_b && push!(codes, UInt32(rule_a * RULE_COUNT + rule_b))
    end
    return codes
end

function effective_pair_indices(version_codes::Vector{UInt32}, pair_index::Matrix{Int32})::Vector{Int32}
    indices = Set{Int32}()
    for code in version_codes
        rule_a = Int(code) ÷ RULE_COUNT
        rule_b = Int(code) % RULE_COUNT
        push!(indices, pair_index[rule_a + 1, rule_b + 1])
    end
    return sort!(collect(indices))
end

vector_hash(vector::Vector{UInt8})::String = sha256_text(JSON3.write(vector))
int_list_hash(values::Vector{Int})::String = sha256_text(JSON3.write(values))
version_hash(values::Vector{UInt32})::String = sha256_text(JSON3.write(values))

function consensus_vector(effective_indices::Vector{Int32}, labels_by_pair::Matrix{UInt16}, queries)
    isempty(effective_indices) && error("empty effective hypothesis set")
    all_equal = trues(length(queries))
    any_equal = falses(length(queries))
    for pair_index in effective_indices
        labels = @view labels_by_pair[:, Int(pair_index)]
        for (query_index, (x, y)) in enumerate(queries)
            equal = labels[x + 1] == labels[y + 1]
            all_equal[query_index] &= equal
            any_equal[query_index] |= equal
        end
    end
    vector = Vector{UInt8}(undef, length(queries))
    for index in eachindex(vector)
        vector[index] = all_equal[index] ? UInt8(2) : (!any_equal[index] ? UInt8(1) : UInt8(0))
    end
    return vector
end

function budget_record(rule_a::Int, rule_b::Int, orbit_key::String, budget::Int, assignments, transitions, labels_by_pair, pair_index, relation_hashes, queries)
    observed_a, observed_b = observed_transitions(rule_a, rule_b, assignments, budget, transitions)
    compatible_a = compatible_rules(observed_a, transitions)
    compatible_b = compatible_rules(observed_b, transitions)
    version_codes = ordered_version_codes(compatible_a, compatible_b)
    effective_indices = effective_pair_indices(version_codes, pair_index)
    relation_count = length(Set(relation_hashes[Int(index)] for index in effective_indices))
    vector = consensus_vector(effective_indices, labels_by_pair, queries)
    identifiable_same = count(==(UInt8(2)), vector)
    identifiable_different = count(==(UInt8(1)), vector)
    unidentifiable = count(==(UInt8(0)), vector)
    consensus_condition = length(effective_indices) >= 8 && relation_count >= 2
    return Dict{String,Any}(
        "rule_A" => rule_a,
        "rule_B" => rule_b,
        "pair_orbit_key" => orbit_key,
        "trajectory_budget" => budget,
        "compatible_A_count" => length(compatible_a),
        "compatible_A_hash" => int_list_hash(compatible_a),
        "compatible_B_count" => length(compatible_b),
        "compatible_B_hash" => int_list_hash(compatible_b),
        "ordered_version_space_size" => length(version_codes),
        "effective_unordered_hypothesis_count" => length(effective_indices),
        "distinct_partition_relation_count" => relation_count,
        "whole_partition_identifiable" => relation_count == 1,
        "true_pair_in_version_space" => UInt32(rule_a * RULE_COUNT + rule_b) in version_codes,
        "system_identified" => length(version_codes) == 1,
        "identifiable_query_count" => identifiable_same + identifiable_different,
        "unidentifiable_query_count" => unidentifiable,
        "consensus_without_identification_query_count" => consensus_condition ? identifiable_same + identifiable_different : 0,
        "identifiable_same_count" => identifiable_same,
        "identifiable_different_count" => identifiable_different,
        "identifiability_vector_hash" => vector_hash(vector),
        "_compatible_A" => compatible_a,
        "_compatible_B" => compatible_b,
        "_version_codes" => version_codes,
        "_effective_indices" => effective_indices,
        "_identifiability_vector" => vector,
        "_observed_A" => observed_a,
        "_observed_B" => observed_b,
    )
end

function public_record(record::Dict{String,Any})
    return Dict(key => value for (key, value) in record if !startswith(key, "_"))
end

function brute_force_codes(observed_a, observed_b, transitions)::Vector{UInt32}
    codes = UInt32[]
    for rule_a in 0:(RULE_COUNT - 1), rule_b in 0:(RULE_COUNT - 1)
        rule_a == rule_b && continue
        a_ok = all(Int(transitions[rule_a + 1][state + 1]) == successor for (state, successor) in observed_a)
        b_ok = all(Int(transitions[rule_b + 1][state + 1]) == successor for (state, successor) in observed_b)
        a_ok && b_ok && push!(codes, UInt32(rule_a * RULE_COUNT + rule_b))
    end
    return codes
end

function boundary_controls(boundary_records, transitions, labels_by_pair, pair_index, relation_hashes, queries)
    factorization = Any[]
    swap = Any[]
    corruption = Any[]
    for record in boundary_records
        factorized = record["_version_codes"]
        brute = brute_force_codes(record["_observed_A"], record["_observed_B"], transitions)
        push!(factorization, Dict(
            "fixture" => [record["rule_A"], record["rule_B"]],
            "budget" => record["trajectory_budget"],
            "factorized_count" => length(factorized),
            "brute_force_count" => length(brute),
            "factorized_hash" => version_hash(factorized),
            "brute_force_hash" => version_hash(brute),
            "passed" => factorized == brute,
        ))
        swapped_a = compatible_rules(record["_observed_B"], transitions)
        swapped_b = compatible_rules(record["_observed_A"], transitions)
        swapped_codes = ordered_version_codes(swapped_a, swapped_b)
        expected_swapped = sort!(UInt32[(Int(code) % RULE_COUNT) * RULE_COUNT + (Int(code) ÷ RULE_COUNT) for code in factorized])
        swapped_effective = effective_pair_indices(swapped_codes, pair_index)
        swapped_vector = consensus_vector(swapped_effective, labels_by_pair, queries)
        push!(swap, Dict(
            "fixture" => [record["rule_A"], record["rule_B"]],
            "budget" => record["trajectory_budget"],
            "version_hypotheses_map" => sort(swapped_codes) == expected_swapped,
            "effective_unordered_hypotheses_preserved" => swapped_effective == record["_effective_indices"],
            "object_relation_preserved" => swapped_vector == record["_identifiability_vector"],
            "passed" => sort(swapped_codes) == expected_swapped && swapped_effective == record["_effective_indices"] && swapped_vector == record["_identifiability_vector"],
        ))
        corrupt_a = copy(record["_observed_A"])
        corrupt_b = copy(record["_observed_B"])
        target = isempty(corrupt_a) ? corrupt_b : corrupt_a
        state, successor = first(target)
        target[1] = (state, xor(successor, 1))
        corrupt_codes = ordered_version_codes(compatible_rules(corrupt_a, transitions), compatible_rules(corrupt_b, transitions))
        true_code = UInt32(record["rule_A"] * RULE_COUNT + record["rule_B"])
        push!(corruption, Dict(
            "fixture" => [record["rule_A"], record["rule_B"]],
            "budget" => record["trajectory_budget"],
            "corrupted_version_space_size" => length(corrupt_codes),
            "true_pair_excluded_or_space_empty" => isempty(corrupt_codes) || !(true_code in corrupt_codes),
            "passed" => isempty(corrupt_codes) || !(true_code in corrupt_codes),
        ))
    end
    return factorization, swap, corruption
end

function query_hash_controls(records, queries)
    source = findfirst(record -> length(unique(record["_identifiability_vector"])) > 1, records)
    source === nothing && error("no nonconstant identifiability vector available for query-order control")
    record = records[source]
    vector = record["_identifiability_vector"]
    shift = findfirst(offset -> circshift(vector, offset) != vector, 1:(length(vector) - 1))
    shift === nothing && error("nonconstant vector had no hash-sensitive cyclic permutation")
    permuted_vector = circshift(vector, shift)
    permuted_queries = circshift(queries, shift)
    mutated_vector = copy(vector)
    mutated_vector[1] = UInt8((Int(mutated_vector[1]) + 1) % 3)
    query_order = Dict(
        "fixture" => [record["rule_A"], record["rule_B"]],
        "budget" => record["trajectory_budget"],
        "cyclic_shift" => shift,
        "counts_preserved" => sort(countmap(vector)) == sort(countmap(permuted_vector)),
        "query_manifest_changes" => sha256_text(compact_pair_list(permuted_queries)) != sha256_text(compact_pair_list(queries)),
        "ordered_vector_hash_changes" => vector_hash(permuted_vector) != vector_hash(vector),
    )
    query_order["passed"] = all(Bool(query_order[key]) for key in ("counts_preserved", "query_manifest_changes", "ordered_vector_hash_changes"))
    mutation = Dict(
        "original_hash" => vector_hash(vector),
        "mutated_hash" => vector_hash(mutated_vector),
        "hash_changes" => vector_hash(vector) != vector_hash(mutated_vector),
    )
    mutation["passed"] = mutation["hash_changes"]
    return query_order, mutation
end

function countmap(items)
    counts = Dict{eltype(items),Int}()
    for value in items
        counts[value] = get(counts, value, 0) + 1
    end
    return collect(Base.values(counts))
end

function summarize_budgets(records)
    summaries = Dict{String,Any}()
    candidate_pass = Bool[]
    for budget in BUDGETS
        current = [record for record in records if record["trajectory_budget"] == budget]
        total_queries = length(current) * EXPECTED_QUERY_COUNT
        identifiable = sum(record["identifiable_query_count"] for record in current)
        qualifying = [record for record in current if record["effective_unordered_hypothesis_count"] >= 8 && record["distinct_partition_relation_count"] >= 2]
        consensus = sum((record["consensus_without_identification_query_count"] for record in qualifying); init=0)
        consensus_same = sum((record["identifiable_same_count"] for record in qualifying); init=0)
        consensus_different = sum((record["identifiable_different_count"] for record in qualifying); init=0)
        denominator = consensus_same + consensus_different
        conditions = Dict(
            "construction_valid" => all(record["ordered_version_space_size"] > 0 && record["true_pair_in_version_space"] for record in current),
            "global_identifiable_coverage_at_least_0_95" => identifiable / total_queries >= 0.95,
            "every_fixture_identifiable_coverage_at_least_0_80" => all(record["identifiable_query_count"] / EXPECTED_QUERY_COUNT >= 0.80 for record in current),
            "at_least_100_multi_hypothesis_multi_partition_fixtures" => length(qualifying) >= 100,
            "at_least_50000_consensus_without_identification_queries" => consensus >= 50000,
            "both_consensus_labels_at_least_0_20" => denominator > 0 && consensus_same / denominator >= 0.20 && consensus_different / denominator >= 0.20,
            "fewer_than_half_fixtures_system_identified" => count(record -> record["system_identified"], current) / length(current) < 0.50,
        )
        candidate = all(values(conditions))
        push!(candidate_pass, candidate)
        summaries[string(budget)] = Dict(
            "fixture_count" => length(current),
            "total_query_count" => total_queries,
            "identifiable_query_count" => identifiable,
            "unidentifiable_query_count" => total_queries - identifiable,
            "global_identifiable_coverage" => identifiable / total_queries,
            "minimum_fixture_identifiable_coverage" => minimum(record["identifiable_query_count"] / EXPECTED_QUERY_COUNT for record in current),
            "system_identified_fixture_count" => count(record -> record["system_identified"], current),
            "system_identified_fixture_rate" => count(record -> record["system_identified"], current) / length(current),
            "multi_hypothesis_multi_partition_fixture_count" => length(qualifying),
            "consensus_without_identification_query_count" => consensus,
            "consensus_identifiable_same_count" => consensus_same,
            "consensus_identifiable_different_count" => consensus_different,
            "consensus_same_fraction" => denominator == 0 ? nothing : consensus_same / denominator,
            "consensus_different_fraction" => denominator == 0 ? nothing : consensus_different / denominator,
            "candidate_conditions" => conditions,
            "consensus_candidate_budget" => candidate,
        )
    end
    earliest = nothing
    for index in 1:(length(BUDGETS) - 1)
        if candidate_pass[index] && candidate_pass[index + 1]
            earliest = BUDGETS[index]
            break
        end
    end
    return summaries, candidate_pass, earliest
end

function main()
    started_at = time()
    manifests = build_frozen_manifests()
    frozen = verify_frozen_inputs(manifests)

    initial_labels = canonical_initial_labels()
    transitions = [UInt16[eca_step(state, rule) for state in 0:(STATE_COUNT - 1)] for rule in 0:(RULE_COUNT - 1)]
    labels_by_pair, pair_index, relation_hashes, partition_swap_failures = precompute_partitions(transitions, initial_labels)

    fixtures = [first(orbit) for orbit in manifests.pair_orbits["test"]]
    fixture_keys = [pair_orbit_key(pair[1], pair[2]) for pair in fixtures]
    length(fixtures) == EXPECTED_FIXTURE_COUNT || error("fixture count drift")
    length(Set(fixtures)) == EXPECTED_FIXTURE_COUNT || error("duplicate fixture representatives")

    records = Dict{String,Any}[]
    sizehint!(records, EXPECTED_FIXTURE_COUNT * length(BUDGETS))
    monotonic_failures = String[]
    for (fixture_index, (rule_a, rule_b)) in enumerate(fixtures)
        previous_version = nothing
        previous_vector = nothing
        for budget in BUDGETS
            record = budget_record(rule_a, rule_b, fixture_keys[fixture_index], budget, manifests.assignments, transitions, labels_by_pair, pair_index, relation_hashes, manifests.queries)
            if previous_version !== nothing
                issubset(Set(record["_version_codes"]), Set(previous_version)) || push!(monotonic_failures, "$rule_a,$rule_b budget $budget version")
                current_ambiguous = record["_identifiability_vector"] .== UInt8(0)
                previous_ambiguous = previous_vector .== UInt8(0)
                all((.!current_ambiguous) .| previous_ambiguous) || push!(monotonic_failures, "$rule_a,$rule_b budget $budget ambiguity")
            end
            previous_version = record["_version_codes"]
            previous_vector = record["_identifiability_vector"]
            push!(records, record)
        end
    end

    boundary_records = [
        records[1], records[length(BUDGETS)],
        records[end - length(BUDGETS) + 1], records[end],
    ]
    factorization_controls, action_swap_controls, corruption_controls = boundary_controls(
        boundary_records, transitions, labels_by_pair, pair_index, relation_hashes, manifests.queries,
    )
    query_order_control, vector_mutation_control = query_hash_controls(records, manifests.queries)
    budget_summaries, candidate_pass, earliest_admitted = summarize_budgets(records)

    required_fields = String.(JSON3.read(read(SPEC_PATH, String))["required_budget_record_fields"])
    required_fields_present = all(all(haskey(record, field) for field in required_fields) for record in records)
    construction_valid = all(record["ordered_version_space_size"] > 0 && record["true_pair_in_version_space"] for record in records)
    system_id_dominated = any(budget_summaries[string(budget)]["system_identified_fixture_rate"] >= 0.90 for budget in BUDGETS)
    any_global_identifiable = any(budget_summaries[string(budget)]["global_identifiable_coverage"] >= 0.95 for budget in BUDGETS)
    regime = earliest_admitted !== nothing ? "PERCEPTION_LIKE_REGIME_ADMITTED_BY_EXACT_SCOUT" :
        (!any_global_identifiable ? "OBSERVATION_OBJECT_RELATION_UNIDENTIFIABLE" :
        (system_id_dominated ? "OBSERVATIONS_IDENTIFY_DYNAMICS_NOT_OBJECT_CONSENSUS" : "NO_STABLE_CONSENSUS_WITHOUT_IDENTIFICATION_WINDOW"))

    tests = Dict(
        "J1_frozen_hashes_and_manifests_verified_before_computation" => Bool(frozen["passed"]),
        "J2_all_32640_unordered_partitions_recomputed" => size(labels_by_pair) == (STATE_COUNT, EXPECTED_PAIR_COUNT) && all(pair_index[a + 1, b + 1] > 0 for a in 0:254 for b in (a + 1):255),
        "J3_all_531_test_fixtures_and_9636_queries_present" => length(fixtures) == EXPECTED_FIXTURE_COUNT && length(manifests.queries) == EXPECTED_QUERY_COUNT,
        "J4_all_required_record_fields_present" => required_fields_present && length(records) == EXPECTED_FIXTURE_COUNT * length(BUDGETS),
        "J5_nonempty_version_spaces_and_true_pair_inclusion" => construction_valid,
        "J6_version_and_ambiguity_monotonicity" => isempty(monotonic_failures),
        "J7_factorized_matches_bruteforce_boundaries" => all(Bool(control["passed"]) for control in factorization_controls),
        "J8_action_swap_preserves_hypotheses_and_object_relations" => isempty(partition_swap_failures) && all(Bool(control["passed"]) for control in action_swap_controls),
        "J9_corrupted_observation_excludes_true_version" => all(Bool(control["passed"]) for control in corruption_controls),
        "J10_query_order_and_vector_hash_controls" => Bool(query_order_control["passed"]) && Bool(vector_mutation_control["passed"]),
        "J11_closed_json_round_trip" => false,
    )
    scientific_pass = all(value for (key, value) in tests if key != "J11_closed_json_round_trip")
    result_path = output_path()
    public_records = public_record.(records)

    result = Dict{String,Any}(
        "schema" => "codex_ratchet.eca_observation_object_identifiability_v0.julia_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "semantic_role" => "independent_exact_transition_partition_version_space_and_query_consensus_ledger",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "ran" => true,
        "reads_peer_result" => false,
        "peer_result_files_read" => String[],
        "parent_result_files_read" => String[],
        "authority_files_read" => [relpath(SPEC_PATH, REPO_ROOT), relpath(CARD_PATH, REPO_ROOT), relpath(RECEIPT_PATH, REPO_ROOT)],
        "semantic_reference_source_read" => "system_v7/sims/eca_behavioral_refinement_depth_census_v1/run_julia.jl",
        "source_path" => relpath(SOURCE_PATH, REPO_ROOT),
        "result_path" => relpath(result_path, REPO_ROOT),
        "claim_ceiling" => CLAIM_CEILING,
        "claim_limits" => [
            "Julia lane only; no cross-runtime or controller claim",
            "finite N9 periodic ECA and fixed Hamming-weight/domain-wall probe only",
            "exact identifiability does not establish learnability or general perception",
            "no QIT stages, four substages, 64-stage schedule, MMM, ontology, Axis0, physics, life, or consciousness claim",
        ],
        "packages_used" => ["JSON3", "SHA"],
        "aligned_packages_load_bearing" => String[],
        "TOOL_MANIFEST" => Dict(
            "load_bearing" => ["JSON3.read", "JSON3.write", "SHA.sha256"],
            "supportive" => String[],
            "forbidden_bridges_absent" => ["PyCall", "PythonCall", "DLPack", "NumPy", "Python", "CSV", "pickle"],
        ),
        "tool_calls" => [
            Dict(
                "tool" => "JSON3",
                "qualified_api/function" => "JSON3.read and JSON3.write",
                "input_object" => "frozen spec/card/receipt, exact finite ledger, and final closed result",
                "output_object" => "parsed authority, deterministic relation/vector encodings, and auditable JSON receipt",
                "positive_case" => "frozen authority parses and final complete receipt round trips",
                "negative/erased_control" => "one identifiability code mutation changes its JSON-bound digest",
                "boundary_case" => "empty compatible-set and null-regime values serialize without coercion",
                "demotion_condition" => "authority parse, vector mutation, or final round trip fails",
                "gates" => ["all_pass", "provenance", "identifiability_vector"],
                "function_receipt" => vector_mutation_control,
            ),
            Dict(
                "tool" => "SHA",
                "qualified_api/function" => "SHA.sha256",
                "input_object" => "frozen files, manifests, compatible-rule sets, partition labels, and identifiability vectors",
                "output_object" => "authority, manifest, relation, version-space, and vector digests",
                "positive_case" => "all frozen hashes match before scientific computation",
                "negative/erased_control" => "query-order permutation and code mutation change ordered digests",
                "boundary_case" => "object relations may agree across distinct compatible dynamics",
                "demotion_condition" => "frozen hash drift or mutation-insensitive digest",
                "gates" => ["all_pass", "provenance", "relation_consensus"],
                "function_receipt" => Dict(
                    "frozen_hashes_passed" => Bool(frozen["passed"]),
                    "query_order_hash_control_passed" => Bool(query_order_control["passed"]),
                    "vector_mutation_hash_control_passed" => Bool(vector_mutation_control["passed"]),
                ),
            ),
        ],
        "runtime" => Dict(
            "julia_version" => string(VERSION),
            "active_project" => Base.active_project(),
            "load_path" => copy(Base.LOAD_PATH),
            "json3_version" => string(Base.pkgversion(JSON3)),
            "threads" => Threads.nthreads(),
        ),
        "hashes" => merge(frozen["hashes"], Dict(
            "run_julia_sha256" => sha256_file(SOURCE_PATH),
            "complete_partition_relation_hash_ledger_sha256" => sha256_text(JSON3.write(relation_hashes)),
            "test_fixture_representatives_sha256" => sha256_text(compact_pair_list(fixtures)),
        )),
        "frozen_input_receipt" => frozen,
        "carrier" => Dict("ring_size" => RING_SIZE, "state_count" => STATE_COUNT, "rule_count" => RULE_COUNT, "probe" => ["hamming_weight", "periodic_domain_walls"]),
        "complete_partition_recomputation" => Dict(
            "unordered_distinct_rule_pair_count" => EXPECTED_PAIR_COUNT,
            "action_swap_partition_failure_count" => length(partition_swap_failures),
            "partition_relation_hash_ledger_sha256" => sha256_text(JSON3.write(relation_hashes)),
        ),
        "fixture_count" => length(fixtures),
        "query_count_per_fixture" => length(manifests.queries),
        "trajectory_budgets" => collect(BUDGETS),
        "budget_record_count" => length(public_records),
        "budget_summaries" => budget_summaries,
        "perception_like_regime_admitted" => earliest_admitted !== nothing,
        "earliest_admitted_budget" => earliest_admitted,
        "regime_classification" => regime,
        "controls" => Dict(
            "factorized_vs_bruteforce_boundaries" => factorization_controls,
            "action_token_swap_boundaries" => action_swap_controls,
            "corrupted_observation_boundaries" => corruption_controls,
            "query_order_permutation" => query_order_control,
            "identifiability_vector_mutation" => vector_mutation_control,
        ),
        "invariants" => Dict(
            "monotonic_failure_count" => length(monotonic_failures),
            "monotonic_failure_examples" => first(monotonic_failures, min(20, length(monotonic_failures))),
            "partition_action_swap_failure_count" => length(partition_swap_failures),
            "partition_action_swap_failure_examples" => first(partition_swap_failures, min(20, length(partition_swap_failures))),
        ),
        "budget_records" => public_records,
        "tests" => tests,
        "scientific_pass_before_closed_json_gate" => scientific_pass,
        "closed_json_validation" => Dict("passed" => false),
        "elapsed_seconds_before_serialization" => time() - started_at,
        "all_pass" => false,
        "blocked_consumers" => JSON3.read(read(SPEC_PATH, String))["blocked_consumers"],
    )

    tentative = JSON3.read(JSON3.write(result))
    tentative_ok = String(tentative["sim_id"]) == SIM_ID && !Bool(tentative["all_pass"]) && length(tentative["budget_records"]) == EXPECTED_FIXTURE_COUNT * length(BUDGETS)
    tentative_ok || error("tentative JSON round trip failed")
    result["tests"]["J11_closed_json_round_trip"] = true
    result["closed_json_validation"] = Dict("passed" => true, "required_budget_record_fields" => required_fields)
    result["all_pass"] = scientific_pass

    final_json = JSON3.write(result)
    final_round_trip = JSON3.read(final_json)
    final_ok = String(final_round_trip["sim_id"]) == SIM_ID && Bool(final_round_trip["all_pass"]) == scientific_pass && Bool(final_round_trip["tests"]["J11_closed_json_round_trip"]) && length(final_round_trip["budget_records"]) == EXPECTED_FIXTURE_COUNT * length(BUDGETS)
    final_ok || error("final JSON round trip failed")

    mkpath(dirname(result_path))
    open(result_path, "w") do io
        write(io, final_json)
        write(io, '\n')
    end
    println(JSON3.write(Dict(
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "all_pass" => result["all_pass"],
        "result_path" => result_path,
        "elapsed_seconds" => time() - started_at,
        "regime_classification" => regime,
        "earliest_admitted_budget" => earliest_admitted,
    )))
end

main()
