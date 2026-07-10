using JSON3
using SHA

const HERE = @__DIR__
const REPO_ROOT = normpath(joinpath(HERE, "..", "..", ".."))
const SOURCE_PATH = abspath(@__FILE__)
const SIM_ID = "eca_behavioral_refinement_depth_census_v0"
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const RING_SIZES = (6, 7, 8)
const RULE_COUNT = 256
const EXPECTED_PAIR_COUNT = div(RULE_COUNT * (RULE_COUNT - 1), 2)
const CLAIM_CEILING = "EXACT_FINITE_PROBE_RELATIVE_ECA_PAIR_REFINEMENT_DEPTH_CENSUS_N6_TO_N8"

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

function eca_step(state::Int, rule::Int, ring_size::Int)::Int
    next_state = 0
    for site in 0:(ring_size - 1)
        left = (state >> mod(site - 1, ring_size)) & 1
        center = (state >> site) & 1
        right = (state >> mod(site + 1, ring_size)) & 1
        neighborhood = 4 * left + 2 * center + right
        next_state |= ((rule >> neighborhood) & 1) << site
    end
    return next_state
end

function rotate_left_state(state::Int, ring_size::Int)::Int
    mask = (1 << ring_size) - 1
    return ((state << 1) & mask) | (state >> (ring_size - 1))
end

function rotate_right_state(state::Int, ring_size::Int)::Int
    return (state >> 1) | ((state & 1) << (ring_size - 1))
end

function domain_walls(state::Int, ring_size::Int)::Int
    return sum(
        ((state >> site) & 1) != ((state >> mod(site + 1, ring_size)) & 1)
        for site in 0:(ring_size - 1)
    )
end

function canonical_initial_labels(ring_size::Int)::Vector{Int}
    state_count = 1 << ring_size
    labels = Vector{Int}(undef, state_count)
    ids = Dict{Tuple{Int,Int},Int}()
    next_id = 0
    for state in 0:(state_count - 1)
        signature = (count_ones(state), domain_walls(state, ring_size))
        label = get(ids, signature, -1)
        if label == -1
            label = next_id
            ids[signature] = label
            next_id += 1
        end
        labels[state + 1] = label
    end
    return labels
end

function refine_labels(
    labels::Vector{Int},
    transition_a::Vector{Int},
    transition_b::Vector{Int},
)::Vector{Int}
    state_count = length(labels)
    refined = Vector{Int}(undef, state_count)
    ids = Dict{NTuple{3,Int},Int}()
    next_id = 0
    for state in 0:(state_count - 1)
        signature = (
            labels[state + 1],
            labels[transition_a[state + 1] + 1],
            labels[transition_b[state + 1] + 1],
        )
        label = get(ids, signature, -1)
        if label == -1
            label = next_id
            ids[signature] = label
            next_id += 1
        end
        refined[state + 1] = label
    end
    return refined
end

function class_sizes(labels::Vector{Int})::Vector{Int}
    sizes = zeros(Int, maximum(labels) + 1)
    for label in labels
        sizes[label + 1] += 1
    end
    return sizes
end

class_count(labels::Vector{Int})::Int = maximum(labels) + 1
surviving_ordered_pair_count(labels::Vector{Int})::Int = sum(abs2, class_sizes(labels))
partition_hash(labels::Vector{Int})::String = sha256_text(JSON3.write(labels))

function quotient_congruent(
    labels::Vector{Int},
    transition_a::Vector{Int},
    transition_b::Vector{Int},
)::Bool
    count = class_count(labels)
    target_a = fill(-1, count)
    target_b = fill(-1, count)
    for state in 0:(length(labels) - 1)
        source = labels[state + 1] + 1
        a = labels[transition_a[state + 1] + 1]
        b = labels[transition_b[state + 1] + 1]
        if target_a[source] == -1
            target_a[source] = a
            target_b[source] = b
        elseif target_a[source] != a || target_b[source] != b
            return false
        end
    end
    return true
end

function exact_refinement(
    initial_labels::Vector{Int},
    transition_a::Vector{Int},
    transition_b::Vector{Int},
)
    labels = copy(initial_labels)
    class_trajectory = [class_count(labels)]
    survivor_trajectory = [surviving_ordered_pair_count(labels)]
    strict_depth = 0
    maximum_rounds = length(labels)

    for _ in 1:maximum_rounds
        refined = refine_labels(labels, transition_a, transition_b)
        if refined == labels
            return (
                labels=labels,
                strict_depth=strict_depth,
                first_equality_round=strict_depth + 1,
                class_trajectory=class_trajectory,
                survivor_trajectory=survivor_trajectory,
            )
        end
        strict_depth += 1
        labels = refined
        push!(class_trajectory, class_count(labels))
        push!(survivor_trajectory, surviving_ordered_pair_count(labels))
    end
    error("partition refinement exceeded finite-state bound")
end

function transition_encoding(transition::Vector{Int})::String
    return JSON3.write(transition)
end

function transition_pair_hash(encoding_a::String, encoding_b::String)::String
    return sha256_text("[$encoding_a,$encoding_b]")
end

function orientation_receipt(transitions::Vector{Vector{Int}}, ring_size::Int)
    rule_170_expected = [rotate_right_state(state, ring_size) for state in 0:((1 << ring_size) - 1)]
    rule_240_expected = [rotate_left_state(state, ring_size) for state in 0:((1 << ring_size) - 1)]
    return Dict(
        "rule_170_is_right_neighbor_rotation" => transitions[171] == rule_170_expected,
        "rule_240_is_left_neighbor_rotation" => transitions[241] == rule_240_expected,
        "passed" => transitions[171] == rule_170_expected && transitions[241] == rule_240_expected,
    )
end

function sha_mutation_receipt(labels::Vector{Int}, transition_encoding_a::String, transition_encoding_b::String)
    original_partition_hash = partition_hash(labels)
    mutated_labels = copy(labels)
    mutated_labels[1] = maximum(labels) + 1
    mutated_partition_hash = partition_hash(mutated_labels)
    original_transition_hash = transition_pair_hash(transition_encoding_a, transition_encoding_b)
    mutated_transition_hash = transition_pair_hash(transition_encoding_a * "0", transition_encoding_b)
    return Dict(
        "partition_hash_changes_under_label_mutation" => original_partition_hash != mutated_partition_hash,
        "transition_hash_changes_under_encoding_mutation" => original_transition_hash != mutated_transition_hash,
        "passed" => original_partition_hash != mutated_partition_hash && original_transition_hash != mutated_transition_hash,
    )
end

function ring_census(ring_size::Int)
    state_count = 1 << ring_size
    initial_labels = canonical_initial_labels(ring_size)
    transitions = [
        [eca_step(state, rule, ring_size) for state in 0:(state_count - 1)]
        for rule in 0:(RULE_COUNT - 1)
    ]
    transition_encodings = transition_encoding.(transitions)
    orientation = orientation_receipt(transitions, ring_size)

    records = Vector{Dict{String,Any}}()
    sizehint!(records, EXPECTED_PAIR_COUNT)
    depth_histogram = Dict{Int,Int}()
    examples_by_depth = Dict{Int,Vector{Vector{Int}}}()
    maximum_depth = -1
    invariant_failures = String[]
    sha_control = nothing

    for rule_a in 0:(RULE_COUNT - 2), rule_b in (rule_a + 1):(RULE_COUNT - 1)
        exact = exact_refinement(initial_labels, transitions[rule_a + 1], transitions[rule_b + 1])
        depth = exact.strict_depth
        classes = exact.class_trajectory
        survivors = exact.survivor_trajectory
        congruent = quotient_congruent(exact.labels, transitions[rule_a + 1], transitions[rule_b + 1])

        length(classes) == depth + 1 || push!(invariant_failures, "$rule_a,$rule_b class trajectory length")
        length(survivors) == depth + 1 || push!(invariant_failures, "$rule_a,$rule_b survivor trajectory length")
        if depth > 0 && !all(diff(classes) .> 0)
            push!(invariant_failures, "$rule_a,$rule_b class monotonicity")
        end
        if depth > 0 && !all(diff(survivors) .< 0)
            push!(invariant_failures, "$rule_a,$rule_b survivor monotonicity")
        end
        congruent || push!(invariant_failures, "$rule_a,$rule_b quotient congruence")

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
        )
        push!(records, record)
        depth_histogram[depth] = get(depth_histogram, depth, 0) + 1
        examples = get!(examples_by_depth, depth, Vector{Vector{Int}}())
        length(examples) < 8 && push!(examples, [rule_a, rule_b])
        maximum_depth = max(maximum_depth, depth)
        sha_control === nothing && (sha_control = sha_mutation_receipt(exact.labels, transition_encodings[rule_a + 1], transition_encodings[rule_b + 1]))
    end

    pair_order_pass = length(records) == EXPECTED_PAIR_COUNT && all(
        record["rule_a"] < record["rule_b"] for record in records
    ) && length(Set((record["rule_a"], record["rule_b"]) for record in records)) == EXPECTED_PAIR_COUNT
    histogram_total_pass = sum(values(depth_histogram)) == EXPECTED_PAIR_COUNT
    internal_invariants_pass = isempty(invariant_failures)
    all_pass = Bool(orientation["passed"]) && pair_order_pass && histogram_total_pass && internal_invariants_pass && Bool(sha_control["passed"])

    return Dict{String,Any}(
        "ring_size" => ring_size,
        "state_count" => state_count,
        "probe" => ["hamming_weight", "periodic_domain_walls"],
        "pair_count" => length(records),
        "maximum_strict_refinement_depth" => maximum_depth,
        "strict_refinement_depth_histogram" => Dict(string(key) => depth_histogram[key] for key in sort!(collect(keys(depth_histogram)))),
        "example_rule_pairs_by_depth" => Dict(string(key) => examples_by_depth[key] for key in sort!(collect(keys(examples_by_depth)))),
        "orientation_receipt" => orientation,
        "sha_mutation_receipt" => sha_control,
        "invariants" => Dict(
            "expected_pair_count" => EXPECTED_PAIR_COUNT,
            "pair_order_and_uniqueness_pass" => pair_order_pass,
            "histogram_total_pass" => histogram_total_pass,
            "partition_trajectory_and_congruence_pass" => internal_invariants_pass,
            "failure_count" => length(invariant_failures),
            "failure_examples" => first(invariant_failures, min(20, length(invariant_failures))),
        ),
        "all_pass" => all_pass,
        "pairs" => records,
    )
end

function tool_calls()
    return [
        Dict(
            "tool" => "JSON3",
            "qualified_api/function" => "JSON3.write and JSON3.read",
            "input_object" => "canonical label vectors, transition vectors, and complete census receipt",
            "output_object" => "deterministic hash encodings and round-tripped standalone result JSON",
            "positive_case" => "all required fields and all_pass survive final JSON round trip",
            "negative/erased_control" => "a changed label vector produces a different partition hash",
            "boundary_case" => "depth-zero trajectories contain exactly the initial partition",
            "demotion_condition" => "closed result fails to parse or required fields drift",
            "gates" => ["all_pass", "partition", "provenance"],
        ),
        Dict(
            "tool" => "SHA",
            "qualified_api/function" => "SHA.sha256",
            "input_object" => "canonical partition labels, exact transition pairs, and source bytes",
            "output_object" => "partition, transition-pair, and source hashes",
            "positive_case" => "stable labels and exact transition maps receive deterministic hashes",
            "negative/erased_control" => "label and transition encoding mutations must change their hashes",
            "boundary_case" => "distinct rule pairs may honestly share one behavioral partition hash",
            "demotion_condition" => "either executed hash mutation is insensitive",
            "gates" => ["all_pass", "partition", "provenance"],
        ),
    ]
end

function main()
    started_at = time()
    rings = [ring_census(ring_size) for ring_size in RING_SIZES]
    scientific_pass = all(Bool(ring["all_pass"]) for ring in rings)
    result_path = output_path()

    result = Dict{String,Any}(
        "schema" => "codex_ratchet.eca_behavioral_refinement_depth_census_v0.julia_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "semantic_role" => "independent_exact_full_state_census",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "ran" => true,
        "reads_peer_result" => false,
        "peer_result_files_read" => String[],
        "source_path" => relpath(SOURCE_PATH, REPO_ROOT),
        "result_path" => relpath(result_path, REPO_ROOT),
        "ring_sizes" => collect(RING_SIZES),
        "rule_pair_contract" => "all unordered distinct ECA pairs 0 <= rule_a < rule_b <= 255",
        "refinement_contract" => "P_(d+1)(x)=canon(P_d(x),P_d(T_a(x)),P_d(T_b(x))); strict depth counts changed partitions",
        "claim_ceiling" => CLAIM_CEILING,
        "claim_limits" => [
            "finite periodic binary rings n=6,7,8 only",
            "fixed probe (Hamming weight, periodic domain walls) only",
            "exact census does not establish learned perception",
            "runtime execution does not establish unique engine intelligence or non-substitutability",
            "does not establish QIT stages, four substages, the 64-stage schedule, MMMs, or ontology formation",
        ],
        "packages_used" => ["JSON3", "SHA"],
        "aligned_packages_load_bearing" => String[],
        "TOOL_MANIFEST" => Dict(
            "load_bearing" => ["JSON3.write", "JSON3.read", "SHA.sha256"],
            "supportive" => String[],
            "forbidden_bridges_absent" => ["PyCall", "PythonCall", "DLPack", "NumPy", "Python", "CSV", "pickle"],
        ),
        "tool_calls" => tool_calls(),
        "runtime" => Dict(
            "julia_version" => string(VERSION),
            "active_project" => Base.active_project(),
            "json3_version" => string(Base.pkgversion(JSON3)),
            "threads" => Threads.nthreads(),
        ),
        "hashes" => Dict("run_julia_sha256" => sha256_file(SOURCE_PATH)),
        "rings" => rings,
        "tests" => Dict(
            "J1_all_32640_pairs_per_ring" => all(ring["pair_count"] == EXPECTED_PAIR_COUNT for ring in rings),
            "J2_deterministic_pair_order_and_uniqueness" => all(Bool(ring["invariants"]["pair_order_and_uniqueness_pass"]) for ring in rings),
            "J3_strict_trajectory_invariants_and_quotient_congruence" => all(Bool(ring["invariants"]["partition_trajectory_and_congruence_pass"]) for ring in rings),
            "J4_eca_orientation_compatible_with_v1_julia" => all(Bool(ring["orientation_receipt"]["passed"]) for ring in rings),
            "J5_sha_mutation_controls" => all(Bool(ring["sha_mutation_receipt"]["passed"]) for ring in rings),
            "J6_closed_json_round_trip" => false,
        ),
        "scientific_pass_before_closed_json_gate" => scientific_pass,
        "closed_json_validation" => Dict("passed" => false),
        "elapsed_seconds_before_serialization" => time() - started_at,
        "all_pass" => false,
    )

    tentative = JSON3.read(JSON3.write(result))
    tentative_ok = String(tentative["sim_id"]) == SIM_ID && !Bool(tentative["all_pass"]) && length(tentative["rings"]) == length(RING_SIZES)
    tentative_ok || error("tentative JSON round trip failed")
    result["tests"]["J6_closed_json_round_trip"] = true
    result["closed_json_validation"] = Dict(
        "passed" => true,
        "required_fields" => ["schema", "sim_id", "engine", "classification", "claim_ceiling", "rings", "tests", "all_pass"],
    )
    result["all_pass"] = scientific_pass

    final_json = JSON3.write(result)
    final_round_trip = JSON3.read(final_json)
    final_ok = String(final_round_trip["sim_id"]) == SIM_ID && Bool(final_round_trip["all_pass"]) == scientific_pass && Bool(final_round_trip["tests"]["J6_closed_json_round_trip"])
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
        "maximum_depth_by_ring" => Dict(string(ring["ring_size"]) => ring["maximum_strict_refinement_depth"] for ring in rings),
    )))
end

main()
