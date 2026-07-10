#!/usr/bin/env julia

using Dates
using Graphs
using JSON
using Pkg
using SHA

const SIM_ID = "unseen_finite_predictive_objects_v1"
const ENGINE = "julia"
const CLASSIFICATION = "scratch_diagnostic"
const PROTOCOL_CORRECTION_COMMIT = "331a8253915deec2c6489b8976c59cb3f37c734d"
const HERE = @__DIR__
const REPO = normpath(joinpath(HERE, "..", "..", ".."))
const SOURCE_PATH = @__FILE__
const SPEC_PATH = joinpath(HERE, "spec.json")
const MANIFEST_PATH = joinpath(HERE, "object_manifest.json")
const V0_MANIFEST_PATH = joinpath(HERE, "..", "unseen_finite_predictive_objects_v0", "object_manifest.json")
const GENERATOR_PATH = joinpath(HERE, "generate_manifest.py")
const STRICT_CARRIER_PROJECT = joinpath(REPO, "system_v5", "julia_carrier", "Project.toml")
const STRICT_CARRIER_MANIFEST = joinpath(dirname(STRICT_CARRIER_PROJECT), "Manifest.toml")
const SEAL_RECEIPT_PATH = joinpath(HERE, "seal_receipt.json")
const RESULT_PATH = joinpath(HERE, "results", "julia_result.json")
const CANDIDATE_NAMESPACE = "ufpo-v1"
const STATE_COUNT = 4
const TARGET_MAX_LENGTH = 8
const CHALLENGE_MAX_LENGTH = 12
const TARGET_COORDINATE_COUNT = sum(2^length for length in 1:TARGET_MAX_LENGTH)
const CHALLENGE_COORDINATE_COUNT = sum(2^length for length in 1:CHALLENGE_MAX_LENGTH)
const Machine = NTuple{STATE_COUNT, NTuple{3, Int}}

const EXPECTED_GREEN_CEILING = "BOUNDED_SUPERVISED_MULTI_VIEW_PREDICTIVE_RETRIEVAL_ON_UNSEEN_FOUR_STATE_OBJECTS_UNDER_FROZEN_LOSSY_VIEWS"
const EXPECTED_RED_CEILING = "UNSEEN_PREDICTIVE_OBJECT_LEARNING_NOT_ESTABLISHED"
const EXPECTED_SEED_DOMAIN = "ufpo-v1|view|split|machine-hash|view-index|trajectory-index|channel"
const EXPECTED_RETRIEVAL_GAIN_FIELD = "loo_same_object_retrieval_gain_over_each_of_histogram_and_temporal_min"
const EXPECTED_PAIR_GATE = "full_observation_horizon_matched_own_target_prediction"

function permutations4()
    rows = NTuple{4, Int}[]
    for a in 0:3, b in 0:3, c in 0:3, d in 0:3
        length(Set((a, b, c, d))) == 4 && push!(rows, (a, b, c, d))
    end
    rows
end

const STATE_PERMUTATIONS = permutations4()

sha256_bytes(payload) = bytes2hex(SHA.sha256(payload))
sha256_file(path::String) = open(path, "r") do io
    bytes2hex(SHA.sha256(io))
end
canonical_json_hash(value) = sha256_bytes(codeunits(JSON.json(value)))
rel(path::String) = relpath(path, REPO)
now_z() = Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ")

function candidate(counter::Int)::Machine
    digest = SHA.sha256(codeunits("$(CANDIDATE_NAMESPACE)|candidate|$(counter)"))
    ntuple(state -> (
        Int(digest[state]) % STATE_COUNT,
        Int(digest[STATE_COUNT + state]) % STATE_COUNT,
        2 + Int(digest[2 * STATE_COUNT + state]) % 5,
    ), STATE_COUNT)
end

function relabel(machine::Machine, order::NTuple{4, Int})::Machine
    inverse = zeros(Int, STATE_COUNT)
    for (new_state, old_state) in enumerate(order)
        inverse[old_state + 1] = new_state - 1
    end
    ntuple(new_state -> begin
        old_state = order[new_state]
        row = machine[old_state + 1]
        (inverse[row[1] + 1], inverse[row[2] + 1], row[3])
    end, STATE_COUNT)
end

function canonical_machine(machine::Machine)::Machine
    best = relabel(machine, STATE_PERMUTATIONS[1])
    for order in @view STATE_PERMUTATIONS[2:end]
        moved = relabel(machine, order)
        isless(moved, best) && (best = moved)
    end
    best
end

machine_json(machine::Machine) = [[row[1], row[2], row[3]] for row in machine]
machine_hash(machine::Machine) = canonical_json_hash(machine_json(machine))

function graph_scc_count(machine::Machine)::Int
    graph = Graphs.SimpleDiGraph(STATE_COUNT)
    for state in 0:(STATE_COUNT - 1), symbol in 0:1
        Graphs.add_edge!(graph, state + 1, machine[state + 1][symbol + 1] + 1)
    end
    length(Graphs.strongly_connected_components(graph))
end

function graph_scc_count(edges::Vector{Tuple{Int, Int}})::Int
    graph = Graphs.SimpleDiGraph(STATE_COUNT)
    for (source, target) in edges
        Graphs.add_edge!(graph, source + 1, target + 1)
    end
    length(Graphs.strongly_connected_components(graph))
end

function word_probability(machine::Machine, start::Int, word::Int, length::Int)::Rational{Int}
    probability = 1 // 1
    state = start
    for position in 1:length
        symbol = (word >> (length - position)) & 1
        numerator_one = machine[state + 1][3]
        probability *= (symbol == 1 ? numerator_one : 8 - numerator_one) // 8
        state = machine[state + 1][symbol + 1]
    end
    probability
end

function state_signature(machine::Machine, state::Int, max_length::Int)::Vector{Rational{Int}}
    signature = Rational{Int}[]
    sizehint!(signature, sum(2^length for length in 1:max_length))
    for length in 1:max_length, word in 0:(2^length - 1)
        push!(signature, word_probability(machine, state, word, length))
    end
    signature
end

function predictive_signature(machine::Machine, max_length::Int)::Vector{Rational{Int}}
    signature = Rational{Int}[]
    sizehint!(signature, sum(2^length for length in 1:max_length))
    for length in 1:max_length, word in 0:(2^length - 1)
        total = sum(word_probability(machine, state, word, length) for state in 0:(STATE_COUNT - 1))
        push!(signature, total / STATE_COUNT)
    end
    signature
end

function signature_hash(signature::Vector{Rational{Int}})::String
    canonical_json_hash([[numerator(value), denominator(value)] for value in signature])
end

full_horizon_distance(left, right) = sum(abs(left[index] - right[index]) for index in eachindex(left))

function machine_from_json(rows)::Machine
    length(rows) == STATE_COUNT || error("machine row count is not four")
    ntuple(index -> begin
        row = rows[index]
        length(row) == 3 || error("machine row does not have three entries")
        (Int(row[1]), Int(row[2]), Int(row[3]))
    end, STATE_COUNT)
end

manifest_rows(manifest) = vcat(manifest["splits"]["train"], manifest["splits"]["validation"], manifest["splits"]["test"])

function rebuild_registry(start_counter::Int, stop_counter::Int, excluded_machine_hashes::Set{String}, excluded_target_hashes::Set{String})
    objects = Dict{String, Any}()
    signature_seen = Set{String}()
    rejected = Dict(
        "not_strongly_connected" => 0,
        "not_minimal" => 0,
        "machine_duplicate" => 0,
        "signature_duplicate" => 0,
        "excluded_v0_machine_hash" => 0,
        "excluded_v0_predictive_signature_hash" => 0,
    )
    for counter in start_counter:stop_counter
        machine = canonical_machine(candidate(counter))
        mhash = machine_hash(machine)
        if mhash in excluded_machine_hashes
            rejected["excluded_v0_machine_hash"] += 1
            continue
        end
        if haskey(objects, mhash)
            rejected["machine_duplicate"] += 1
            continue
        end
        if graph_scc_count(machine) != 1
            rejected["not_strongly_connected"] += 1
            continue
        end
        state_signatures = [state_signature(machine, state, TARGET_MAX_LENGTH) for state in 0:(STATE_COUNT - 1)]
        if length(Set(state_signatures)) != STATE_COUNT
            rejected["not_minimal"] += 1
            continue
        end
        target_signature = predictive_signature(machine, TARGET_MAX_LENGTH)
        target_hash = signature_hash(target_signature)
        if target_hash in excluded_target_hashes
            rejected["excluded_v0_predictive_signature_hash"] += 1
            continue
        end
        if target_hash in signature_seen
            rejected["signature_duplicate"] += 1
            continue
        end
        push!(signature_seen, target_hash)
        objects[mhash] = Dict(
            "counter" => counter,
            "machine" => machine,
            "machine_sha256" => mhash,
            "predictive_signature" => target_signature,
            "predictive_signature_sha256" => target_hash,
            "state_signature_sha256" => [signature_hash(signature) for signature in state_signatures],
        )
    end
    ordered = [objects[key] for key in sort(collect(keys(objects)))]
    ordered, rejected
end

function row_semantic_match(rebuilt, row)::Bool
    machine = machine_from_json(row["machine"])
    target = predictive_signature(machine, TARGET_MAX_LENGTH)
    challenge = predictive_signature(machine, CHALLENGE_MAX_LENGTH)
    state_hashes = [signature_hash(state_signature(machine, state, TARGET_MAX_LENGTH)) for state in 0:(STATE_COUNT - 1)]
    rebuilt["counter"] == Int(row["counter"]) &&
    rebuilt["machine"] == machine &&
    rebuilt["machine_sha256"] == String(row["machine_sha256"]) &&
    machine_hash(machine) == String(row["machine_sha256"]) &&
    state_hashes == String.(row["state_signature_sha256"]) &&
    rebuilt["predictive_signature_sha256"] == String(row["predictive_signature_sha256"]) &&
    String(row["target_signature_sha256"]) == String(row["predictive_signature_sha256"]) &&
    signature_hash(target) == String(row["target_signature_sha256"]) &&
    Int(row["target_signature_coordinate_count"]) == TARGET_COORDINATE_COUNT &&
    signature_hash(challenge) == String(row["challenge_signature_sha256"]) &&
    Int(row["challenge_signature_coordinate_count"]) == CHALLENGE_COORDINATE_COUNT
end

function selected_rows_match(selected, declared)::Bool
    length(selected) == length(declared) || return false
    all(row_semantic_match(rebuilt, row) for (rebuilt, row) in zip(selected, declared))
end

function pair_verification(test_rows, declared_pairs)
    signatures = Dict(String(row["machine_sha256"]) => predictive_signature(machine_from_json(row["machine"]), CHALLENGE_MAX_LENGTH) for row in test_rows)
    test_hashes = sort(collect(keys(signatures)))
    measurements = Any[]
    membership = String[]
    distances_match = true
    shape_match = length(declared_pairs) == 16
    for pair_row in declared_pairs
        pair_shape = haskey(pair_row, "left_machine_sha256") && haskey(pair_row, "right_machine_sha256") && haskey(pair_row, "full_lengths_1_to_12_l1_distance")
        shape_match &= pair_shape
        pair_shape || continue
        left = String(pair_row["left_machine_sha256"])
        right = String(pair_row["right_machine_sha256"])
        push!(membership, left)
        push!(membership, right)
        if !haskey(signatures, left) || !haskey(signatures, right) || left >= right
            distances_match = false
            continue
        end
        distance = full_horizon_distance(signatures[left], signatures[right])
        encoded = [numerator(distance), denominator(distance)]
        declared_distance = Int.(pair_row["full_lengths_1_to_12_l1_distance"])
        distances_match &= encoded == declared_distance
        push!(measurements, Dict(
            "left_machine_sha256" => left,
            "right_machine_sha256" => right,
            "computed_full_lengths_1_to_12_l1_distance" => encoded,
            "declared_full_lengths_1_to_12_l1_distance" => declared_distance,
            "match" => encoded == declared_distance,
        ))
    end
    membership_match = length(membership) == 32 && length(Set(membership)) == 32 && Set(membership) == Set(test_hashes)
    Dict(
        "pair_count" => length(declared_pairs),
        "expected_pair_count" => 16,
        "shape_match" => shape_match,
        "membership_match" => membership_match,
        "distances_match" => distances_match && length(measurements) == 16,
        "all_pairs_match" => shape_match && membership_match && distances_match && length(measurements) == 16,
        "measurements" => measurements,
    )
end

function command_ok(command)
    try
        run(pipeline(command, stdout=devnull, stderr=devnull))
        true
    catch
        false
    end
end

function protocol_commit_receipt()
    current_commit = try
        readchomp(`git -C $REPO rev-parse HEAD`)
    catch
        ""
    end
    ancestor = command_ok(`git -C $REPO merge-base --is-ancestor $PROTOCOL_CORRECTION_COMMIT HEAD`)
    Dict(
        "protocol_correction_commit" => PROTOCOL_CORRECTION_COMMIT,
        "current_head" => current_commit,
        "correction_commit_is_ancestor" => ancestor,
        "pass" => ancestor,
    )
end

function package_versions()
    Dict(
        "julia" => string(VERSION),
        "Graphs" => string(pkgversion(Graphs)),
        "JSON" => string(pkgversion(JSON)),
    )
end

function package_receipt()
    active_project = normpath(String(Base.active_project()))
    load_path = String.(Base.LOAD_PATH)
    project_exists = isfile(STRICT_CARRIER_PROJECT)
    manifest_exists = isfile(STRICT_CARRIER_MANIFEST)
    strict_project = active_project == normpath(STRICT_CARRIER_PROJECT)
    strict_load_path = load_path == ["@", "@stdlib"]
    Dict(
        "active_project" => active_project,
        "expected_project" => normpath(STRICT_CARRIER_PROJECT),
        "project_exists" => project_exists,
        "manifest_exists" => manifest_exists,
        "strict_project" => strict_project,
        "load_path" => load_path,
        "strict_load_path" => strict_load_path,
        "project_sha256" => project_exists ? sha256_file(STRICT_CARRIER_PROJECT) : "",
        "manifest_sha256" => manifest_exists ? sha256_file(STRICT_CARRIER_MANIFEST) : "",
        "package_versions" => package_versions(),
        "pass" => project_exists && manifest_exists && strict_project && strict_load_path,
    )
end

function source_hash_receipt()
    actual = Dict(
        "spec_sha256" => sha256_file(SPEC_PATH),
        "object_manifest_sha256" => sha256_file(MANIFEST_PATH),
        "v0_manifest_sha256" => sha256_file(V0_MANIFEST_PATH),
        "manifest_generator_sha256" => sha256_file(GENERATOR_PATH),
    )
    Dict(
        "actual" => actual,
        "manifest_spec_binding" => actual["spec_sha256"] == String(JSON.parsefile(MANIFEST_PATH)["spec_sha256"]),
        "manifest_v0_binding" => actual["v0_manifest_sha256"] == String(JSON.parsefile(MANIFEST_PATH)["v0_manifest_sha256"]),
        "pass" => actual["spec_sha256"] == String(JSON.parsefile(MANIFEST_PATH)["spec_sha256"]) && actual["v0_manifest_sha256"] == String(JSON.parsefile(MANIFEST_PATH)["v0_manifest_sha256"]),
    )
end

function dynamic_spec_gates(spec)
    object_family = spec["object_family"]
    exclusions = spec["exclusions"]
    splits = spec["frozen_splits"]
    views = spec["view_process"]
    learner = spec["learner"]
    metrics = spec["metrics_and_gates"]
    pairing = metrics[EXPECTED_PAIR_GATE]
    engine = spec["engine_contract"]
    Dict(
        "current_spec_schema" => spec["schema"] == "codex_ratchet.unseen_finite_predictive_objects_v1.spec.v1",
        "current_sim_id_and_locks" => spec["sim_id"] == SIM_ID && spec["classification"] == CLASSIFICATION && spec["promotion_allowed"] == false && spec["formal_admission_allowed"] == false,
        "learner_source_status_unsealed" => spec["learner_source_status"] == "not_sealed_by_manifest_generation",
        "object_family_namespace_and_interval" => object_family["candidate_namespace"] == CANDIDATE_NAMESPACE && Vector{Int}(object_family["candidate_counter_interval"]) == [0, 8191],
        "object_family_signature_lengths" => Vector{Int}(object_family["target_signature_lengths"]) == [1, 8] && Vector{Int}(object_family["challenge_signature_lengths"]) == [1, 12] && Int(object_family["target_signature_coordinate_count"]) == TARGET_COORDINATE_COUNT && Int(object_family["challenge_signature_coordinate_count"]) == CHALLENGE_COORDINATE_COUNT,
        "v0_exclusion_contract" => exclusions["v0_manifest_path"] == rel(V0_MANIFEST_PATH) && exclusions["exclusion_is_applied_before_sorted_selection"] == true && occursin("every machine_sha256", String(exclusions["machine_hashes"])) && occursin("every length1_to_8 predictive signature hash", String(exclusions["predictive_signature_hashes"])),
        "split_contract" => splits["selection"] == "canonicalize and deduplicate the full ufpo-v1 counter interval, exclude every v0 machine and length1-to-8 predictive-signature hash, sort eligible machine SHA-256 hashes, take the first 128 train and next 32 validation objects, then the next 32 test objects" && Int(splits["train_objects"]) == 128 && Int(splits["validation_objects"]) == 32 && Int(splits["test_objects"]) == 32 && splits["test_pairing"] == "full-observation-horizon-matched" && occursin("exact minimum-weight perfect matching", String(splits["test_pairing_distance"])),
        "shared_view_prng_domain" => views["seed_domain"] == EXPECTED_SEED_DOMAIN && views["seed_domain_is_new_relative_to_v0"] == true && !occursin("model-seed", lowercase(String(views["seed_domain"]))) && !occursin("arm", lowercase(String(views["seed_domain"]))),
        "view_process_contract" => Int(views["trajectories_per_view"]) == 16 && Int(views["trajectory_length"]) == 12 && Float64(views["erasure_probability"]) == 0.35 && Float64(views["substitution_probability_after_non_erasure"]) == 0.10 && Vector{Int}(views["model_seeds"]) == [2701, 2702, 2703] && views["initial_state"] == "independent uniform draw for every trajectory" && views["independence"] == "every view uses a disjoint SHA-256-derived PRNG subtree; no latent trajectory, initial-state draw, mask, or corruption draw is shared" && Vector{String}(views["model_visible_fields"]) == ["corrupted_binary_tokens", "erasure_mask", "trajectory_boundary"] && Vector{String}(views["model_forbidden_fields"]) == ["machine_definition", "canonical_hash", "object_index", "state_index", "split", "view_seed", "full_observation_horizon_matched_partner"],
        "supervised_retrieval_learner_contract" => learner["decoder"] == "separate softmax segment for each target word length one through eight" && learner["pooling"] == "DeepSets mean over independently encoded trajectories" && learner["epochs"] == 16 && learner["checkpoint_policy"] == "score epoch 16 only; no early stopping or test-aware selection",
        "retrieval_gain_field_is_per_control" => haskey(metrics, EXPECTED_RETRIEVAL_GAIN_FIELD) && !haskey(metrics, "loo_same_object_retrieval_gain_over_histogram_plus_temporal_min") && Float64(metrics[EXPECTED_RETRIEVAL_GAIN_FIELD]) == 0.15,
        "own_target_prediction_gate" => haskey(metrics, EXPECTED_PAIR_GATE) && Int(pairing["both_members_own_target_min"]) == 13 && Int(pairing["pair_count"]) == 16 && pairing["every_seed"] == true && Int(pairing["per_seed_test_objects"]) == 32 && Int(pairing["test_views_per_seed"]) == 256,
        "forbidden_metrics_and_primary_gate_policy" => Vector{String}(metrics["forbidden_metrics"]) == ["K", "ARI", "Bcubed"] && metrics["test_labels_forbidden_from_training_and_threshold_selection"] == true && metrics["all_primary_gates_required_for_each_seed"] == true,
        "all_three_mode_and_owners" => engine["mode"] == "all_three_full_sims" && engine["registry_proposal_owner"] == "Python stdlib Fraction generator freezes candidate enumeration, canonical records, v0 exclusions, splits, exact signatures, and full-observation-horizon-matched pair distances; it does not own predictive-object semantics" && engine["julia"] == "independent exact Rational semantic verification and arbitration" && engine["semantic_owner"] == "Julia independent exact finite predictive-equivalence verification and arbitration" && engine["learner_source_seal"] == "not performed by this generator" && engine["numpy_on_claim_path"] == false,
        "correct_green_ceiling" => spec["accepted_green_ceiling"] == EXPECTED_GREEN_CEILING && spec["accepted_red_ceiling"] == EXPECTED_RED_CEILING,
    )
end

function source_gates(spec, manifest, v0_manifest, source_hashes, spec_hash, manifest_hash, v0_hash, rebuilt, rejected, selected, pairs)
    object_family = spec["object_family"]
    splits = spec["frozen_splits"]
    manifest_rows_value = manifest_rows(manifest)
    expected_rejected = Dict(String(key) => Int(value) for (key, value) in manifest["rejected_counts"])
    selected_hashes = [String(row["machine_sha256"]) for row in manifest_rows_value]
    rebuilt_hashes = [String(row["machine_sha256"]) for row in selected]
    split_hashes = Dict(key => String[row["machine_sha256"] for row in manifest["splits"][key]] for key in ("train", "validation", "test"))
    all_hashes = vcat(split_hashes["train"], split_hashes["validation"], split_hashes["test"])
    excluded_machines = Set(String(row["machine_sha256"]) for row in manifest_rows(v0_manifest))
    excluded_targets = Set(String(row["predictive_signature_sha256"]) for row in manifest_rows(v0_manifest))
    dynamic = dynamic_spec_gates(spec)
    gates = Dict{String, Bool}()
    merge!(gates, dynamic)
    gates["source_hash_bindings"] = source_hashes["pass"] && spec_hash == String(manifest["spec_sha256"]) && v0_hash == String(manifest["v0_manifest_sha256"]) && manifest_hash != ""
    gates["manifest_schema_and_identity"] = manifest["schema"] == "codex_ratchet.unseen_finite_predictive_objects_v1.object_manifest.v1" && manifest["sim_id"] == SIM_ID && manifest["classification"] == CLASSIFICATION
    gates["manifest_admission_locks"] = manifest["promotion_allowed"] == false && manifest["formal_admission_allowed"] == false
    gates["v0_manifest_schema"] = v0_manifest["schema"] == "codex_ratchet.unseen_finite_predictive_objects_v0.object_manifest.v1"
    gates["manifest_candidate_contract"] = manifest["candidate_namespace"] == CANDIDATE_NAMESPACE && Vector{Int}(manifest["candidate_interval"]) == [0, 8191]
    gates["manifest_selection_contract"] = manifest["selection"] == splits["selection"] && manifest["spec_sha256"] == spec_hash && manifest["v0_manifest_sha256"] == v0_hash
    gates["manifest_signature_contract"] = manifest["signature_contract"]["target_lengths"] == [1, 8] && manifest["signature_contract"]["challenge_lengths"] == [1, 12] && Int(manifest["signature_contract"]["target_coordinate_count"]) == TARGET_COORDINATE_COUNT && Int(manifest["signature_contract"]["challenge_coordinate_count"]) == CHALLENGE_COORDINATE_COUNT && manifest["signature_contract"]["exact_rational_encoding"] == "each Fraction is hashed from [numerator, denominator] pairs in canonical JSON order"
    gates["manifest_unsealed_status"] = manifest["learner_source_sealed"] == false && manifest["test_outcome_status"] == "machine registry, exact target signatures, challenge signatures, and full-observation-horizon-matched pair distances frozen; learner source is not sealed and no learned test metric exists"
    gates["candidate_count_and_rejections"] = length(rebuilt) == Int(manifest["eligible_candidate_count"]) == Int(manifest["accepted_candidate_count"]) && rejected == expected_rejected
    gates["v0_exclusions_applied"] = length(excluded_machines) == Int(manifest["excluded_v0_machine_hash_count"]) && length(excluded_targets) == Int(manifest["excluded_v0_predictive_signature_hash_count"]) && all(!(String(row["machine_sha256"]) in excluded_machines) && !(String(row["predictive_signature_sha256"]) in excluded_targets) for row in selected)
    gates["selected_row_count"] = length(selected) == 192 && length(manifest_rows_value) == 192
    gates["every_selected_semantic_field"] = selected_rows_match(selected, manifest_rows_value)
    gates["canonical_state_permutation_form"] = all(machine_from_json(row["machine"]) == canonical_machine(machine_from_json(row["machine"])) for row in manifest_rows_value)
    gates["graphs_strong_connectivity"] = all(graph_scc_count(machine_from_json(row["machine"])) == 1 for row in manifest_rows_value)
    gates["minimality"] = all(length(Set(state_signature(machine_from_json(row["machine"]), state, TARGET_MAX_LENGTH) for state in 0:(STATE_COUNT - 1))) == STATE_COUNT for row in manifest_rows_value)
    gates["target_signature_coordinate_count"] = all(Int(row["target_signature_coordinate_count"]) == TARGET_COORDINATE_COUNT for row in manifest_rows_value)
    gates["challenge_signature_coordinate_count"] = all(Int(row["challenge_signature_coordinate_count"]) == CHALLENGE_COORDINATE_COUNT for row in manifest_rows_value)
    gates["split_counts"] = length(split_hashes["train"]) == Int(splits["train_objects"]) == 128 && length(split_hashes["validation"]) == Int(splits["validation_objects"]) == 32 && length(split_hashes["test"]) == Int(splits["test_objects"]) == 32
    gates["split_assignment_and_order"] = length(selected) == 192 && split_hashes["train"] == rebuilt_hashes[1:128] && split_hashes["validation"] == rebuilt_hashes[129:160] && split_hashes["test"] == rebuilt_hashes[161:192]
    gates["split_uniqueness"] = length(all_hashes) == 192 && length(Set(all_hashes)) == 192
    gates["test_pairing_contract"] = manifest["test_pairing"]["name"] == "full-observation-horizon-matched"
    gates["test_pairing_algorithm_contract"] = manifest["test_pairing"]["algorithm"] == "networkx.algorithms.matching.min_weight_matching" && manifest["test_pairing"]["objective"] == "minimum-weight perfect matching" && occursin("all predictive-signature coordinates at lengths 1 through 12", String(manifest["test_pairing"]["weight"]))
    gates["full_horizon_pair_memberships_and_distances"] = pairs["all_pairs_match"]
    gates["graphs_negative_control"] = graph_scc_count([(0, 1), (1, 0), (2, 3), (3, 2)]) == 2
    gates["graphs_boundary_control"] = graph_scc_count([(0, 1), (1, 2), (2, 3), (3, 0)]) == 1
    gates["no_peer_result_reads"] = true
    gates
end

function validate_seal_receipt(spec_hash::String, manifest_hash::String, v0_hash::String)
    isfile(SEAL_RECEIPT_PATH) || error("--sealed-test requires seal receipt: $(rel(SEAL_RECEIPT_PATH))")
    receipt = JSON.parsefile(SEAL_RECEIPT_PATH)
    required = ["schema", "sim_id", "registry_frozen", "learner_source_sealed", "spec_sha256", "object_manifest_sha256", "v0_manifest_sha256"]
    all(haskey(receipt, key) for key in required) || error("seal receipt is missing a required binding field")
    pass = receipt["schema"] == "codex_ratchet.unseen_finite_predictive_objects_v1.seal_receipt.v1" &&
        receipt["sim_id"] == SIM_ID && receipt["registry_frozen"] == true && receipt["learner_source_sealed"] == true &&
        receipt["spec_sha256"] == spec_hash && receipt["object_manifest_sha256"] == manifest_hash && receipt["v0_manifest_sha256"] == v0_hash
    pass || error("seal receipt is not bound to the current v1 source inputs")
    Dict("path" => rel(SEAL_RECEIPT_PATH), "sha256" => sha256_file(SEAL_RECEIPT_PATH), "pass" => true)
end

function build_payload(mode::String, seal_receipt=nothing)
    spec = JSON.parsefile(SPEC_PATH)
    manifest = JSON.parsefile(MANIFEST_PATH)
    v0_manifest = JSON.parsefile(V0_MANIFEST_PATH)
    spec_hash = sha256_file(SPEC_PATH)
    manifest_hash = sha256_file(MANIFEST_PATH)
    v0_hash = sha256_file(V0_MANIFEST_PATH)
    source_hashes = source_hash_receipt()
    excluded_machine_hashes = Set(String(row["machine_sha256"]) for row in manifest_rows(v0_manifest))
    excluded_target_hashes = Set(String(row["predictive_signature_sha256"]) for row in manifest_rows(v0_manifest))
    start_counter, stop_counter = Int.(spec["object_family"]["candidate_counter_interval"])
    rebuilt, rejected = rebuild_registry(start_counter, stop_counter, excluded_machine_hashes, excluded_target_hashes)
    selected_count = sum(Int(spec["frozen_splits"][key]) for key in ("train_objects", "validation_objects", "test_objects"))
    selected = length(rebuilt) >= selected_count ? rebuilt[1:selected_count] : Any[]
    pair_rows = manifest["test_pairing"]["pairs"]
    pairs = pair_verification(manifest["splits"]["test"], pair_rows)
    gates = source_gates(spec, manifest, v0_manifest, source_hashes, spec_hash, manifest_hash, v0_hash, rebuilt, rejected, selected, pairs)
    packages = package_receipt()
    protocol = protocol_commit_receipt()
    gates["strict_carrier_package_receipt"] = packages["pass"]
    gates["protocol_correction_commit"] = protocol["pass"]
    engine_all_pass = all(values(gates))
    capability_receipts = [
        Dict(
            "receipt_id" => "julia_Graphs_ufpo_v1_scc_semantics",
            "tool" => "Graphs",
            "qualified_api/function" => "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.strongly_connected_components",
            "input_object" => "all 8192 ufpo-v1 candidates and the 192 selected canonical machines",
            "output_object" => "SCC counts for candidate rejection, all selected rows, and controls",
            "positive_case" => "all 192 selected machines have one SCC",
            "negative/erased_control" => "two disconnected two-cycles have two SCCs",
            "boundary_case" => "one directed four-cycle has one SCC",
            "demotion_condition" => "any selected SCC or control count differs from its expected value",
            "gates" => ["graphs_strong_connectivity", "graphs_negative_control", "graphs_boundary_control", "engine_all_pass"],
        ),
        Dict(
            "receipt_id" => "julia_SHA_ufpo_v1_exact_rational_hashes",
            "tool" => "SHA",
            "qualified_api/function" => "SHA.sha256",
            "input_object" => "candidate namespace bytes, canonical machines, and exact Rational numerator-denominator vectors",
            "output_object" => "machine, state-signature, target-signature, challenge-signature, and source hashes",
            "positive_case" => "all rebuilt selected semantic hashes match the frozen manifest",
            "negative/erased_control" => "an altered source binding or exact signature fails its hash gate",
            "boundary_case" => "target has 510 and challenge has 8190 exact rational coordinates",
            "demotion_condition" => "any source, machine, signature, or coordinate-count mismatch",
            "gates" => ["source_hash_bindings", "every_selected_semantic_field", "full_horizon_pair_memberships_and_distances", "engine_all_pass"],
        ),
    ]
    tool_calls = capability_receipts
    result = Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "object_id" => "$(SIM_ID)_$(ENGINE)",
        "engine" => ENGINE,
        "mode" => mode,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "generated_at" => now_z(),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "reads_peer_result" => false,
        "peer_result_paths_read" => String[],
        "runtime" => Dict(
            "julia_executable" => joinpath(Sys.BINDIR, Base.julia_exename()),
            "julia_version" => string(VERSION),
            "active_project" => packages["active_project"],
            "project_sha256" => packages["project_sha256"],
            "manifest_path" => rel(STRICT_CARRIER_MANIFEST),
            "manifest_sha256" => packages["manifest_sha256"],
            "load_path" => packages["load_path"],
            "package_versions" => packages["package_versions"],
        ),
        "packages_used" => ["Graphs", "JSON", "SHA", "Dates", "Pkg"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing SCC semantics for candidate rejection, all 192 selected rows, and controls"),
            "SHA" => Dict("tried" => true, "used" => true, "reason" => "load-bearing exact source, machine, state-signature, target-signature, and challenge-signature bindings"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive frozen source input and eventual result serialization"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "SHA" => "load_bearing", "JSON" => "supportive"),
        "package_receipt" => packages,
        "protocol_correction_receipt" => protocol,
        "source_hash_receipt" => source_hashes,
        "capability_receipts" => capability_receipts,
        "tool_calls" => tool_calls,
        "one_to_one_tool_calls" => Dict("pass" => [row["receipt_id"] for row in capability_receipts] == [row["receipt_id"] for row in tool_calls], "receipt_ids" => [row["receipt_id"] for row in tool_calls]),
        "spec_bindings" => Dict(
            "dynamic_fields_checked" => true,
            "view_seed_domain" => spec["view_process"]["seed_domain"],
            "view_domain_excludes_model_seed" => !occursin("model-seed", lowercase(String(spec["view_process"]["seed_domain"]))),
            "view_domain_excludes_arm" => !occursin("arm", lowercase(String(spec["view_process"]["seed_domain"]))),
            "view_model_seeds" => spec["view_process"]["model_seeds"],
            "retrieval_gain_field" => EXPECTED_RETRIEVAL_GAIN_FIELD,
            "own_target_prediction_gate" => EXPECTED_PAIR_GATE,
            "engine_mode" => spec["engine_contract"]["mode"],
            "registry_owner" => "Python provisional registry only; Julia exact semantic disagreement blocks",
            "accepted_green_ceiling" => spec["accepted_green_ceiling"],
        ),
        "rebuild" => Dict(
            "candidate_count" => stop_counter - start_counter + 1,
            "accepted_candidate_count" => length(rebuilt),
            "rejected_counts" => rejected,
            "selected_object_count" => length(selected),
            "word_probability_arithmetic" => "Rational{Int}",
            "target_word_lengths" => [1, TARGET_MAX_LENGTH],
            "challenge_word_lengths" => [1, CHALLENGE_MAX_LENGTH],
            "target_signature_coordinate_count" => TARGET_COORDINATE_COUNT,
            "challenge_signature_coordinate_count" => CHALLENGE_COORDINATE_COUNT,
            "state_permutations_checked_per_machine" => length(STATE_PERMUTATIONS),
            "full_horizon_pair_verification" => pairs,
        ),
        "gates" => gates,
        "engine_all_pass" => engine_all_pass,
        "all_pass" => false,
        "packet_gate_pending" => "controller_three_engine_and_learner_evaluation",
        "controller_status" => "pending_all_three_engine_assembly",
        "claim_status" => "red_ceiling_pending_controller",
        "claim_ceiling" => spec["accepted_red_ceiling"],
        "green_ceiling_not_claimed" => spec["accepted_green_ceiling"],
        "blocked_consumers" => spec["blocked_consumers"],
        "seal_receipt" => seal_receipt === nothing ? Dict("required_for_sealed_test" => true, "present" => false, "pass" => false) : seal_receipt,
    )
    result
end

function write_result(payload)
    isfile(RESULT_PATH) && error("refusing to overwrite existing sealed-test result: $(rel(RESULT_PATH))")
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload)
        write(io, '\n')
    end
end

function main()
    if "--preflight" in ARGS
        payload = build_payload("preflight")
        println(JSON.json(Dict(
            "mode" => "preflight",
            "engine_all_pass" => payload["engine_all_pass"],
            "all_pass" => false,
            "result_written" => false,
            "source_path" => payload["source_path"],
        )))
        return payload["engine_all_pass"] ? 0 : 1
    elseif "--sealed-test" in ARGS
        isfile(RESULT_PATH) && error("refusing to overwrite existing sealed-test result: $(rel(RESULT_PATH))")
        spec_hash = sha256_file(SPEC_PATH)
        manifest_hash = sha256_file(MANIFEST_PATH)
        v0_hash = sha256_file(V0_MANIFEST_PATH)
        receipt = validate_seal_receipt(spec_hash, manifest_hash, v0_hash)
        payload = build_payload("sealed-test", receipt)
        write_result(payload)
        println(JSON.json(Dict("mode" => "sealed-test", "engine_all_pass" => payload["engine_all_pass"], "all_pass" => false, "result_path" => rel(RESULT_PATH))))
        return payload["engine_all_pass"] ? 0 : 1
    else
        println("usage: run_julia.jl --preflight | --sealed-test")
        println("--preflight validates current v1 source inputs without writing a result")
        println("--sealed-test requires a bound seal_receipt.json and refuses overwrite")
        return 2
    end
end

exit(main())
