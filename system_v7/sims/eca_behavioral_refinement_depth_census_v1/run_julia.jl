using JSON3
using SHA

const HERE = @__DIR__
const REPO_ROOT = normpath(joinpath(HERE, "..", "..", ".."))
const SOURCE_PATH = abspath(@__FILE__)
const SPEC_PATH = joinpath(HERE, "spec.json")
const CARD_PATH = joinpath(HERE, "wizard_v4_3_object_card.json")
const RECEIPT_PATH = joinpath(HERE, "preregistration_receipt.json")
const SIM_ID = "eca_behavioral_refinement_depth_census_v1"
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const RING_SIZE = 9
const STATE_COUNT = 1 << RING_SIZE
const RULE_COUNT = 256
const EXPECTED_PAIR_COUNT = div(RULE_COUNT * (RULE_COUNT - 1), 2)
const HIDDEN_BATCH_TAG = "ECA9-DEPTH-V1"
const DEPTH_SIX = 6
const CLAIM_CEILING = "EXACT_FINITE_PROBE_RELATIVE_ECA_PAIR_REFINEMENT_DEPTH_CENSUS_N9_JULIA_LANE_ONLY"

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

function verify_frozen_inputs()
    spec = JSON3.read(read(SPEC_PATH, String))
    card = JSON3.read(read(CARD_PATH, String))
    receipt = JSON3.read(read(RECEIPT_PATH, String))
    statement = String(card["primary_object_card"]["object_statement"])
    tests = Dict(
        "sim_id_matches" => String(spec["sim_id"]) == String(receipt["sim_id"]) == SIM_ID,
        "spec_sha256_matches" => sha256_file(SPEC_PATH) == String(receipt["spec_sha256"]),
        "object_card_sha256_matches" => sha256_file(CARD_PATH) == String(receipt["object_card_sha256"]),
        "object_statement_sha256_matches" => sha256_text(statement) == String(card["primary_object_card"]["object_statement_sha256"]),
        "builder_absent_when_frozen" => !Bool(receipt["builder_sources_present_when_frozen"]),
        "ring_size_matches" => Int(spec["carrier"]["ring_size"]) == RING_SIZE,
        "pair_count_matches" => Int(spec["carrier"]["unordered_distinct_rule_pair_count"]) == EXPECTED_PAIR_COUNT,
        "hidden_batch_tag_matches" => String(spec["downstream_hidden_batch_split"]["salt"]) == HIDDEN_BATCH_TAG,
    )
    all(values(tests)) || error("frozen preregistration verification failed: $(JSON3.write(tests))")
    return Dict(
        "passed" => true,
        "verified_before_computation" => true,
        "tests" => tests,
        "hashes" => Dict(
            "spec_sha256" => sha256_file(SPEC_PATH),
            "object_card_sha256" => sha256_file(CARD_PATH),
            "preregistration_receipt_sha256" => sha256_file(RECEIPT_PATH),
        ),
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

function rotate_left_state(state::Int)::Int
    return ((state << 1) & (STATE_COUNT - 1)) | (state >> (RING_SIZE - 1))
end

function rotate_right_state(state::Int)::Int
    return (state >> 1) | ((state & 1) << (RING_SIZE - 1))
end

function reflect_state(state::Int)::Int
    reflected = 0
    for site in 0:(RING_SIZE - 1)
        reflected |= ((state >> site) & 1) << mod(-site, RING_SIZE)
    end
    return reflected
end

function complement_state(state::Int)::Int
    return xor(state, STATE_COUNT - 1)
end

function domain_walls(state::Int)::Int
    return sum(
        ((state >> site) & 1) != ((state >> mod(site + 1, RING_SIZE)) & 1)
        for site in 0:(RING_SIZE - 1)
    )
end

function canonical_initial_labels()::Vector{UInt16}
    labels = Vector{UInt16}(undef, STATE_COUNT)
    ids = Dict{Tuple{Int,Int},UInt16}()
    next_id = UInt16(0)
    for state in 0:(STATE_COUNT - 1)
        signature = (count_ones(state), domain_walls(state))
        label = get(ids, signature, typemax(UInt16))
        if label == typemax(UInt16)
            label = next_id
            ids[signature] = label
            next_id += UInt16(1)
        end
        labels[state + 1] = label
    end
    return labels
end

function refine_labels(
    labels::Vector{UInt16},
    transition_a::Vector{UInt16},
    transition_b::Vector{UInt16},
)::Vector{UInt16}
    refined = Vector{UInt16}(undef, length(labels))
    ids = Dict{UInt32,UInt16}()
    next_id = UInt16(0)
    for state in eachindex(labels)
        signature = UInt32(labels[state]) |
            (UInt32(labels[Int(transition_a[state]) + 1]) << 9) |
            (UInt32(labels[Int(transition_b[state]) + 1]) << 18)
        label = get(ids, signature, typemax(UInt16))
        if label == typemax(UInt16)
            label = next_id
            ids[signature] = label
            next_id += UInt16(1)
        end
        refined[state] = label
    end
    return refined
end

function class_sizes(labels::Vector{UInt16})::Vector{Int}
    sizes = zeros(Int, Int(maximum(labels)) + 1)
    for label in labels
        sizes[Int(label) + 1] += 1
    end
    return sizes
end

class_count(labels::Vector{UInt16})::Int = Int(maximum(labels)) + 1
surviving_ordered_pair_count(labels::Vector{UInt16})::Int = sum(abs2, class_sizes(labels))
partition_hash(labels::Vector{UInt16})::String = sha256_text(JSON3.write(labels))

function quotient_congruent(
    labels::Vector{UInt16},
    transition_a::Vector{UInt16},
    transition_b::Vector{UInt16},
)::Bool
    count = class_count(labels)
    target_a = fill(typemax(UInt16), count)
    target_b = fill(typemax(UInt16), count)
    for state in eachindex(labels)
        source = Int(labels[state]) + 1
        a = labels[Int(transition_a[state]) + 1]
        b = labels[Int(transition_b[state]) + 1]
        if target_a[source] == typemax(UInt16)
            target_a[source] = a
            target_b[source] = b
        elseif target_a[source] != a || target_b[source] != b
            return false
        end
    end
    return true
end

function exact_refinement(
    initial_labels::Vector{UInt16},
    transition_a::Vector{UInt16},
    transition_b::Vector{UInt16},
)
    labels = copy(initial_labels)
    class_trajectory = [class_count(labels)]
    survivor_trajectory = [surviving_ordered_pair_count(labels)]
    strict_depth = 0

    for _ in 1:length(labels)
        refined = refine_labels(labels, transition_a, transition_b)
        if refined == labels
            stable_survivors = last(survivor_trajectory)
            depth_six_survivors = survivor_trajectory[min(DEPTH_SIX, strict_depth) + 1]
            return (
                labels=labels,
                strict_depth=strict_depth,
                first_equality_round=strict_depth + 1,
                class_trajectory=class_trajectory,
                survivor_trajectory=survivor_trajectory,
                depth_six_changed_ordered_pair_count=depth_six_survivors - stable_survivors,
            )
        end
        strict_depth += 1
        labels = refined
        push!(class_trajectory, class_count(labels))
        push!(survivor_trajectory, surviving_ordered_pair_count(labels))
    end
    error("partition refinement exceeded finite-state bound")
end

transition_encoding(transition::Vector{UInt16})::String = JSON3.write(transition)
transition_pair_hash(encoding_a::String, encoding_b::String)::String = sha256_text("[$encoding_a,$encoding_b]")

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

function rule_transforms(rule::Int)::NTuple{4,Int}
    conjugated = conjugate_rule(rule)
    return (rule, reflect_rule(rule), conjugated, reflect_rule(conjugated))
end

function simultaneous_pair_orbit(rule_a::Int, rule_b::Int)::Vector{Tuple{Int,Int}}
    transforms_a = rule_transforms(rule_a)
    transforms_b = rule_transforms(rule_b)
    orbit = Set{Tuple{Int,Int}}()
    for index in 1:4
        a, b = transforms_a[index], transforms_b[index]
        push!(orbit, a < b ? (a, b) : (b, a))
    end
    return sort!(collect(orbit))
end

function pair_orbit_key(rule_a::Int, rule_b::Int)::String
    canonical = first(simultaneous_pair_orbit(rule_a, rule_b))
    return "$(canonical[1]),$(canonical[2])"
end

orbit_order_hash(key::String)::String = sha256_text("$HIDDEN_BATCH_TAG|pair_orbit|$key")

function hidden_batch_map()
    keys = Set{String}()
    for rule_a in 0:(RULE_COUNT - 2), rule_b in (rule_a + 1):(RULE_COUNT - 1)
        push!(keys, pair_orbit_key(rule_a, rule_b))
    end
    ordered_keys = sort!(collect(keys); by=key -> (orbit_order_hash(key), key))
    batch_by_key = Dict(key => (isodd(index) ? "A" : "B") for (index, key) in enumerate(ordered_keys))
    return ordered_keys, batch_by_key
end

function orientation_receipt(transitions::Vector{Vector{UInt16}})
    rule_170_expected = UInt16[rotate_right_state(state) for state in 0:(STATE_COUNT - 1)]
    rule_240_expected = UInt16[rotate_left_state(state) for state in 0:(STATE_COUNT - 1)]
    return Dict(
        "rule_170_is_right_neighbor_rotation" => transitions[171] == rule_170_expected,
        "rule_240_is_left_neighbor_rotation" => transitions[241] == rule_240_expected,
        "passed" => transitions[171] == rule_170_expected && transitions[241] == rule_240_expected,
    )
end

function partition_equivariant(labels::Vector{UInt16}, permutation::Vector{Int})::Bool
    forward = Dict{UInt16,UInt16}()
    reverse = Dict{UInt16,UInt16}()
    for state in eachindex(labels)
        source = labels[state]
        target = labels[permutation[state] + 1]
        get(forward, source, target) == target || return false
        get(reverse, target, source) == source || return false
        forward[source] = target
        reverse[target] = source
    end
    return true
end

function carrier_symmetry_receipt(transitions::Vector{Vector{UInt16}}, initial_labels::Vector{UInt16})
    rotation_equivariance = true
    reflection_conjugacy = true
    complement_conjugacy = true
    for rule in 0:(RULE_COUNT - 1), state in 0:(STATE_COUNT - 1)
        rotation_equivariance &= Int(transitions[rule + 1][rotate_left_state(state) + 1]) == rotate_left_state(Int(transitions[rule + 1][state + 1]))
        reflection_conjugacy &= Int(transitions[reflect_rule(rule) + 1][reflect_state(state) + 1]) == reflect_state(Int(transitions[rule + 1][state + 1]))
        complement_conjugacy &= Int(transitions[conjugate_rule(rule) + 1][complement_state(state) + 1]) == complement_state(Int(transitions[rule + 1][state + 1]))
    end
    rotation_permutation = [rotate_left_state(state) for state in 0:(STATE_COUNT - 1)]
    reflection_permutation = [reflect_state(state) for state in 0:(STATE_COUNT - 1)]
    complement_permutation = [complement_state(state) for state in 0:(STATE_COUNT - 1)]
    probe_rotation_equivariance = partition_equivariant(initial_labels, rotation_permutation)
    probe_reflection_equivariance = partition_equivariant(initial_labels, reflection_permutation)
    probe_complement_equivariance = partition_equivariant(initial_labels, complement_permutation)
    passed = rotation_equivariance && reflection_conjugacy && complement_conjugacy && probe_rotation_equivariance && probe_reflection_equivariance && probe_complement_equivariance
    return Dict(
        "rotation_equivariance" => rotation_equivariance,
        "reflection_rule_conjugacy" => reflection_conjugacy,
        "black_white_rule_conjugacy" => complement_conjugacy,
        "probe_rotation_partition_equivariance" => probe_rotation_equivariance,
        "probe_reflection_partition_equivariance" => probe_reflection_equivariance,
        "probe_black_white_partition_equivariance" => probe_complement_equivariance,
        "passed" => passed,
    )
end

function synthetic_depth_fixture(depth::Int)
    depth >= 0 || error("synthetic depth must be nonnegative")
    if depth == 0
        labels = UInt16[0, 0, 1, 1]
        transition = UInt16[0, 1, 2, 3]
    else
        labels = vcat(fill(UInt16(0), depth + 1), UInt16[1])
        transition = UInt16[min(index + 1, depth + 1) for index in 0:(depth + 1)]
    end
    identity = UInt16[index for index in 0:(length(labels) - 1)]
    exact = exact_refinement(labels, transition, identity)
    return Dict(
        "expected_strict_depth" => depth,
        "observed_strict_depth" => exact.strict_depth,
        "first_equality_round" => exact.first_equality_round,
        "passed" => exact.strict_depth == depth && exact.first_equality_round == depth + 1,
    )
end

function sha_and_json_receipt(labels::Vector{UInt16}, encoding_a::String, encoding_b::String)
    partition_original = partition_hash(labels)
    mutated_labels = copy(labels)
    mutated_labels[1] = UInt16(Int(maximum(labels)) + 1)
    partition_mutated = partition_hash(mutated_labels)
    transition_original = transition_pair_hash(encoding_a, encoding_b)
    transition_mutated = transition_pair_hash(encoding_a * "0", encoding_b)
    boundary_json = JSON3.write(Int[])
    boundary_round_trip = JSON3.read(boundary_json)
    passed = partition_original != partition_mutated && transition_original != transition_mutated && length(boundary_round_trip) == 0
    return Dict(
        "partition_hash_changes_under_label_mutation" => partition_original != partition_mutated,
        "transition_hash_changes_under_encoding_mutation" => transition_original != transition_mutated,
        "empty_vector_json_boundary_round_trip" => length(boundary_round_trip) == 0,
        "passed" => passed,
    )
end

function trajectory_valid(depth::Int, classes::Vector{Int}, survivors::Vector{Int})::Bool
    return length(classes) == depth + 1 &&
        length(survivors) == depth + 1 &&
        (depth == 0 || all(diff(classes) .> 0)) &&
        (depth == 0 || all(diff(survivors) .< 0))
end

function trajectory_mutation_receipt(depth::Int, classes::Vector{Int}, survivors::Vector{Int})
    mutated = copy(classes)
    push!(mutated, last(mutated))
    return Dict(
        "original_valid" => trajectory_valid(depth, classes, survivors),
        "mutated_trajectory_rejected" => !trajectory_valid(depth, mutated, survivors),
        "passed" => trajectory_valid(depth, classes, survivors) && !trajectory_valid(depth, mutated, survivors),
    )
end

function pair_signature(record::Dict{String,Any})
    return (
        record["strict_refinement_depth"],
        record["first_equality_round"],
        record["class_count_trajectory"],
        record["surviving_ordered_pair_count_trajectory"],
        record["stable_class_count"],
        record["depth_six_changed_ordered_pair_count"],
    )
end

function depth_six_baseline_mcc(record::Dict{String,Any})::Float64
    survivors = record["surviving_ordered_pair_count_trajectory"]
    depth = record["strict_refinement_depth"]
    predicted_positive = survivors[min(DEPTH_SIX, depth) + 1]
    true_positive = last(survivors)
    false_positive = predicted_positive - true_positive
    true_negative = STATE_COUNT * STATE_COUNT - predicted_positive
    denominator = sqrt(float(predicted_positive) * float(true_positive) * float(true_negative + false_positive) * float(true_negative))
    return denominator == 0.0 ? 0.0 : (true_positive * true_negative) / denominator
end

function main()
    started_at = time()
    frozen_input_receipt = verify_frozen_inputs()
    initial_labels = canonical_initial_labels()
    transitions = [UInt16[eca_step(state, rule) for state in 0:(STATE_COUNT - 1)] for rule in 0:(RULE_COUNT - 1)]
    transition_encodings = transition_encoding.(transitions)
    ordered_orbit_keys, batch_by_key = hidden_batch_map()
    orientation = orientation_receipt(transitions)
    carrier_symmetry = carrier_symmetry_receipt(transitions, initial_labels)
    synthetic_depths = [synthetic_depth_fixture(depth) for depth in (0, 1, 2, 6)]

    records = Vector{Dict{String,Any}}()
    sizehint!(records, EXPECTED_PAIR_COUNT)
    depth_histogram = Dict{Int,Int}()
    examples_by_depth = Dict{Int,Vector{Vector{Int}}}()
    maximum_depth = -1
    invariant_failures = String[]
    swap_failures = String[]
    sha_json_control = nothing
    trajectory_control = nothing

    for rule_a in 0:(RULE_COUNT - 2), rule_b in (rule_a + 1):(RULE_COUNT - 1)
        transition_a = transitions[rule_a + 1]
        transition_b = transitions[rule_b + 1]
        exact = exact_refinement(initial_labels, transition_a, transition_b)
        swapped = exact_refinement(initial_labels, transition_b, transition_a)
        classes = exact.class_trajectory
        survivors = exact.survivor_trajectory
        depth = exact.strict_depth

        trajectory_valid(depth, classes, survivors) || push!(invariant_failures, "$rule_a,$rule_b trajectory")
        quotient_congruent(exact.labels, transition_a, transition_b) || push!(invariant_failures, "$rule_a,$rule_b quotient congruence")
        exact.depth_six_changed_ordered_pair_count >= 0 || push!(invariant_failures, "$rule_a,$rule_b depth-six delta negative")
        if exact.labels != swapped.labels || classes != swapped.class_trajectory || survivors != swapped.survivor_trajectory
            push!(swap_failures, "$rule_a,$rule_b")
        end

        orbit_key = pair_orbit_key(rule_a, rule_b)
        record = Dict{String,Any}(
            "rule_a" => rule_a,
            "rule_b" => rule_b,
            "strict_refinement_depth" => depth,
            "first_equality_round" => exact.first_equality_round,
            "class_count_trajectory" => classes,
            "surviving_ordered_pair_count_trajectory" => survivors,
            "stable_class_count" => last(classes),
            "partition_hash" => partition_hash(exact.labels),
            "transition_pair_hash" => transition_pair_hash(transition_encodings[rule_a + 1], transition_encodings[rule_b + 1]),
            "simultaneous_pair_orbit_key" => orbit_key,
            "hidden_batch" => batch_by_key[orbit_key],
            "depth_six_changed_ordered_pair_count" => exact.depth_six_changed_ordered_pair_count,
        )
        push!(records, record)
        depth_histogram[depth] = get(depth_histogram, depth, 0) + 1
        examples = get!(examples_by_depth, depth, Vector{Vector{Int}}())
        length(examples) < 8 && push!(examples, [rule_a, rule_b])
        maximum_depth = max(maximum_depth, depth)
        sha_json_control === nothing && (sha_json_control = sha_and_json_receipt(exact.labels, transition_encodings[rule_a + 1], transition_encodings[rule_b + 1]))
        trajectory_control === nothing && (trajectory_control = trajectory_mutation_receipt(depth, classes, survivors))
    end

    pair_order_pass = length(records) == EXPECTED_PAIR_COUNT &&
        all(record["rule_a"] < record["rule_b"] for record in records) &&
        length(Set((record["rule_a"], record["rule_b"]) for record in records)) == EXPECTED_PAIR_COUNT

    records_by_orbit = Dict{String,Vector{Dict{String,Any}}}()
    for record in records
        push!(get!(records_by_orbit, record["simultaneous_pair_orbit_key"], Dict{String,Any}[]), record)
    end
    orbit_failures = String[]
    for (key, members) in records_by_orbit
        reference = pair_signature(first(members))
        all(pair_signature(member) == reference for member in members) || push!(orbit_failures, key)
        all(member["hidden_batch"] == first(members)["hidden_batch"] for member in members) || push!(orbit_failures, "$key batch")
    end

    batch_pair_counts = Dict(
        "A" => count(record -> record["hidden_batch"] == "A", records),
        "B" => count(record -> record["hidden_batch"] == "B", records),
    )
    qualifying = [record for record in records if record["strict_refinement_depth"] >= 7]
    qualifying_orbits = Set(record["simultaneous_pair_orbit_key"] for record in qualifying)
    qualifying_orbits_by_batch = Dict(
        "A" => count(key -> batch_by_key[key] == "A", qualifying_orbits),
        "B" => count(key -> batch_by_key[key] == "B", qualifying_orbits),
    )
    total_changed = sum(record["depth_six_changed_ordered_pair_count"] for record in qualifying)
    total_depth_six_equivalent = sum(record["surviving_ordered_pair_count_trajectory"][DEPTH_SIX + 1] for record in qualifying)
    aggregate_changed_mass = total_depth_six_equivalent == 0 ? 0.0 : total_changed / total_depth_six_equivalent
    per_fixture_changed_mass = [
        record["depth_six_changed_ordered_pair_count"] / record["surviving_ordered_pair_count_trajectory"][DEPTH_SIX + 1]
        for record in qualifying
    ]
    depth_six_macro_mcc = isempty(qualifying) ? 0.0 : sum(depth_six_baseline_mcc(record) for record in qualifying) / length(qualifying)

    tests = Dict(
        "J1_frozen_hashes_verified_before_computation" => Bool(frozen_input_receipt["passed"]),
        "J2_all_32640_pairs_exactly_once" => pair_order_pass,
        "J3_strict_trajectory_and_quotient_invariants" => isempty(invariant_failures),
        "J4_action_swap_invariance_all_pairs" => isempty(swap_failures),
        "J5_eca_orientation" => Bool(orientation["passed"]),
        "J6_rotation_probe_and_simultaneous_rule_symmetries" => Bool(carrier_symmetry["passed"]) && isempty(orbit_failures),
        "J7_strict_depth_synthetic_conventions" => all(Bool(fixture["passed"]) for fixture in synthetic_depths),
        "J8_sha_and_json_function_controls" => Bool(sha_json_control["passed"]),
        "J9_trajectory_mutation_detected" => Bool(trajectory_control["passed"]),
        "J10_hidden_batch_orbit_closure" => length(ordered_orbit_keys) == 8808 && length(records_by_orbit) == 8808 && batch_pair_counts == Dict("A" => 16319, "B" => 16321),
        "J11_closed_json_round_trip" => false,
    )
    scientific_pass = all(value for (key, value) in tests if key != "J11_closed_json_round_trip")
    result_path = output_path()

    result = Dict{String,Any}(
        "schema" => "codex_ratchet.eca_behavioral_refinement_depth_census_v1.julia_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "semantic_role" => "independent_exact_full_state_n9_census",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "ran" => true,
        "reads_peer_result" => false,
        "peer_result_files_read" => String[],
        "authority_files_read" => [relpath(SPEC_PATH, REPO_ROOT), relpath(CARD_PATH, REPO_ROOT), relpath(RECEIPT_PATH, REPO_ROOT)],
        "source_path" => relpath(SOURCE_PATH, REPO_ROOT),
        "result_path" => relpath(result_path, REPO_ROOT),
        "ring_size" => RING_SIZE,
        "state_count" => STATE_COUNT,
        "rule_pair_contract" => "all unordered distinct ECA pairs 0 <= rule_a < rule_b <= 255",
        "refinement_contract" => "P_(d+1)(x)=canon(P_d(x),P_d(T_a(x)),P_d(T_b(x))); strict depth counts changed partitions",
        "depth_six_changed_ordered_pair_count_contract" => "surviving ordered state pairs after six strict refinements minus surviving ordered state pairs in the stable partition; zero when strict depth <= 6",
        "claim_ceiling" => CLAIM_CEILING,
        "claim_limits" => [
            "Julia lane only until independent JAX and controller receipts close",
            "finite periodic binary ring n=9 and fixed Hamming-weight/domain-wall probe only",
            "exact census does not establish learned perception",
            "runtime execution does not establish unique engine intelligence, QIT stages, four substages, the 64-stage schedule, MMMs, or ontology formation",
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
                "input_object" => "frozen preregistration surfaces, finite ledger, empty-vector boundary object, and final receipt",
                "output_object" => "parsed frozen authority, deterministic hash encodings, and closed result JSON",
                "positive_case" => "frozen fields parse and the complete result survives final round trip",
                "negative/erased_control" => "trajectory mutation is rejected and changed label encoding changes the bound SHA digest",
                "boundary_case" => "an empty vector round trips with length zero",
                "demotion_condition" => "frozen input parse, boundary round trip, or final closed-result parse fails",
                "gates" => ["all_pass", "partition", "provenance"],
                "function_receipt" => sha_json_control,
            ),
            Dict(
                "tool" => "SHA",
                "qualified_api/function" => "SHA.sha256",
                "input_object" => "frozen source surfaces, canonical stable labels, transition pairs, source bytes, and hidden-orbit ordering keys",
                "output_object" => "authority, partition, transition-pair, source, and split-order hashes",
                "positive_case" => "frozen hashes match before computation and exact finite objects receive deterministic digests",
                "negative/erased_control" => "label and transition encoding mutations change their digests",
                "boundary_case" => "distinct rule pairs may share a behavioral partition hash without sharing a transition-pair hash",
                "demotion_condition" => "a frozen authority hash drifts or either executed mutation is hash-insensitive",
                "gates" => ["all_pass", "partition", "provenance", "hidden_batch"],
                "function_receipt" => Dict(
                    "frozen_input_hashes_passed" => Bool(frozen_input_receipt["passed"]),
                    "partition_mutation_detected" => Bool(sha_json_control["partition_hash_changes_under_label_mutation"]),
                    "transition_mutation_detected" => Bool(sha_json_control["transition_hash_changes_under_encoding_mutation"]),
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
        "hashes" => merge(frozen_input_receipt["hashes"], Dict(
            "run_julia_sha256" => sha256_file(SOURCE_PATH),
            "ordered_orbit_keys_sha256" => sha256_text(JSON3.write(ordered_orbit_keys)),
        )),
        "frozen_input_receipt" => frozen_input_receipt,
        "probe" => ["hamming_weight", "periodic_domain_walls"],
        "pair_count" => length(records),
        "maximum_strict_refinement_depth" => maximum_depth,
        "strict_refinement_depth_histogram" => Dict(string(key) => depth_histogram[key] for key in sort!(collect(keys(depth_histogram)))),
        "example_rule_pairs_by_depth" => Dict(string(key) => examples_by_depth[key] for key in sort!(collect(keys(examples_by_depth)))),
        "split_receipt" => Dict(
            "unique_pair_orbit_count" => length(ordered_orbit_keys),
            "hidden_batch_pair_counts" => batch_pair_counts,
            "hidden_batch_orbit_counts" => Dict("A" => 4404, "B" => 4404),
            "ordered_orbit_keys_sha256" => sha256_text(JSON3.write(ordered_orbit_keys)),
            "all_orbit_members_share_batch" => isempty(orbit_failures),
        ),
        "downstream_v2_admission_readout" => Dict(
            "qualifying_fixture_count_depth_at_least_7" => length(qualifying),
            "qualifying_symmetry_orbit_count" => length(qualifying_orbits),
            "qualifying_orbits_by_hidden_batch" => qualifying_orbits_by_batch,
            "total_depth_six_changed_ordered_pair_count" => total_changed,
            "total_depth_six_equivalent_ordered_pair_count" => total_depth_six_equivalent,
            "aggregate_depth_six_changed_target_mass" => aggregate_changed_mass,
            "minimum_per_qualifying_fixture_changed_target_mass" => (isempty(per_fixture_changed_mass) ? 0.0 : minimum(per_fixture_changed_mass)),
            "all_qualifying_fixtures_meet_minimum_0_01_changed_mass" => !isempty(per_fixture_changed_mass) && all(mass >= 0.01 for mass in per_fixture_changed_mass),
            "depth_six_baseline_macro_mcc" => depth_six_macro_mcc,
            "depth_six_baseline_maximum_allowed_macro_mcc" => 0.35,
            "admission_is_not_learning_success" => true,
        ),
        "orientation_receipt" => orientation,
        "carrier_symmetry_receipt" => carrier_symmetry,
        "synthetic_depth_receipts" => synthetic_depths,
        "sha_json_mutation_receipt" => sha_json_control,
        "trajectory_mutation_receipt" => trajectory_control,
        "invariants" => Dict(
            "pair_order_and_uniqueness_pass" => pair_order_pass,
            "trajectory_and_quotient_failure_count" => length(invariant_failures),
            "trajectory_and_quotient_failure_examples" => first(invariant_failures, min(20, length(invariant_failures))),
            "action_swap_failure_count" => length(swap_failures),
            "action_swap_failure_examples" => first(swap_failures, min(20, length(swap_failures))),
            "simultaneous_orbit_failure_count" => length(orbit_failures),
            "simultaneous_orbit_failure_examples" => first(orbit_failures, min(20, length(orbit_failures))),
        ),
        "pairs" => records,
        "tests" => tests,
        "scientific_pass_before_closed_json_gate" => scientific_pass,
        "closed_json_validation" => Dict("passed" => false),
        "elapsed_seconds_before_serialization" => time() - started_at,
        "all_pass" => false,
    )

    tentative = JSON3.read(JSON3.write(result))
    tentative_ok = String(tentative["sim_id"]) == SIM_ID && !Bool(tentative["all_pass"]) && length(tentative["pairs"]) == EXPECTED_PAIR_COUNT
    tentative_ok || error("tentative JSON round trip failed")
    result["tests"]["J11_closed_json_round_trip"] = true
    result["closed_json_validation"] = Dict(
        "passed" => true,
        "required_pair_fields" => [
            "rule_a", "rule_b", "strict_refinement_depth", "first_equality_round",
            "class_count_trajectory", "surviving_ordered_pair_count_trajectory",
            "stable_class_count", "partition_hash", "transition_pair_hash",
            "simultaneous_pair_orbit_key", "hidden_batch",
            "depth_six_changed_ordered_pair_count",
        ],
    )
    result["all_pass"] = scientific_pass

    final_json = JSON3.write(result)
    final_round_trip = JSON3.read(final_json)
    final_ok = String(final_round_trip["sim_id"]) == SIM_ID && Bool(final_round_trip["all_pass"]) == scientific_pass && Bool(final_round_trip["tests"]["J11_closed_json_round_trip"]) && length(final_round_trip["pairs"]) == EXPECTED_PAIR_COUNT
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
        "maximum_strict_refinement_depth" => maximum_depth,
        "qualifying_symmetry_orbit_count" => length(qualifying_orbits),
    )))
end

main()
