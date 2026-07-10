#!/usr/bin/env julia

using Dates
using Graphs
using JSON
using Pkg
using SHA

const SIM_ID = "unseen_finite_predictive_objects_v0"
const ENGINE = "julia"
const CLASSIFICATION = "scratch_diagnostic"
const EXPECTED_COMMIT = "8b082f333d7d3f767179fee9834e07f828a61d18"
const HERE = @__DIR__
const REPO = normpath(joinpath(HERE, "..", "..", ".."))
const SOURCE_PATH = @__FILE__
const SPEC_PATH = joinpath(HERE, "spec.json")
const PREREG_PATH = joinpath(HERE, "preregistration_receipt.json")
const MANIFEST_PATH = joinpath(HERE, "object_manifest.json")
const README_PATH = joinpath(HERE, "README.md")
const GENERATOR_PATH = joinpath(HERE, "generate_manifest.py")
const OBJECT_CARD_PATH = joinpath(HERE, "wizard_v4_3_object_card.json")
const CORRECTION_PATH = joinpath(HERE, "PREREGISTRATION_CORRECTION.md")
const RESULT_PATH = joinpath(HERE, "results", "julia_result.json")
const CANDIDATE_NAMESPACE = "ufpo-v0"
const STATE_COUNT = 4
const MAX_WORD_LENGTH = 8
const WORD_COORDINATE_COUNT = sum(2^length for length in 1:MAX_WORD_LENGTH)
const Machine = NTuple{STATE_COUNT, NTuple{3, Int}}

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

function state_signature(machine::Machine, state::Int)::Vector{Rational{Int}}
    signature = Rational{Int}[]
    sizehint!(signature, WORD_COORDINATE_COUNT)
    for length in 1:MAX_WORD_LENGTH, word in 0:(2^length - 1)
        push!(signature, word_probability(machine, state, word, length))
    end
    signature
end

function predictive_signature(machine::Machine)::Vector{Rational{Int}}
    signature = Rational{Int}[]
    sizehint!(signature, WORD_COORDINATE_COUNT)
    for length in 1:MAX_WORD_LENGTH, word in 0:(2^length - 1)
        total = sum(word_probability(machine, state, word, length) for state in 0:(STATE_COUNT - 1))
        push!(signature, total / STATE_COUNT)
    end
    signature
end

function signature_hash(signature::Vector{Rational{Int}})::String
    canonical_json_hash([[numerator(value), denominator(value)] for value in signature])
end

short_horizon_distance(left, right) = sum(abs(left[index] - right[index]) for index in 1:6)
long_horizon_distance(left, right) = sum(abs(left[index] - right[index]) for index in 7:length(left))

function rebuild_registry(start_counter::Int, stop_counter::Int)
    objects = Dict{String, Any}()
    signature_seen = Set{String}()
    rejected = Dict(
        "not_strongly_connected" => 0,
        "not_minimal" => 0,
        "machine_duplicate" => 0,
        "signature_duplicate" => 0,
    )
    for counter in start_counter:stop_counter
        machine = canonical_machine(candidate(counter))
        mhash = machine_hash(machine)
        if haskey(objects, mhash)
            rejected["machine_duplicate"] += 1
            continue
        end
        if graph_scc_count(machine) != 1
            rejected["not_strongly_connected"] += 1
            continue
        end
        state_signatures = [state_signature(machine, state) for state in 0:(STATE_COUNT - 1)]
        state_hashes = [signature_hash(signature) for signature in state_signatures]
        if length(Set(state_signatures)) != STATE_COUNT
            rejected["not_minimal"] += 1
            continue
        end
        signature = predictive_signature(machine)
        phash = signature_hash(signature)
        if phash in signature_seen
            rejected["signature_duplicate"] += 1
            continue
        end
        push!(signature_seen, phash)
        objects[mhash] = Dict(
            "counter" => counter,
            "machine" => machine,
            "machine_sha256" => mhash,
            "predictive_signature" => signature,
            "predictive_signature_sha256" => phash,
            "state_signature_sha256" => state_hashes,
        )
    end
    ordered = [objects[key] for key in sort(collect(keys(objects)))]
    ordered, rejected
end

function machine_from_json(rows)::Machine
    ntuple(index -> begin
        row = rows[index]
        (Int(row[1]), Int(row[2]), Int(row[3]))
    end, STATE_COUNT)
end

function manifest_rows(manifest)
    vcat(manifest["splits"]["train"], manifest["splits"]["validation"], manifest["splits"]["test"])
end

function selected_rows_match(selected, declared)::Bool
    length(selected) == length(declared) || return false
    for (rebuilt, row) in zip(selected, declared)
        machine = machine_from_json(row["machine"])
        rebuilt["counter"] == Int(row["counter"]) || return false
        rebuilt["machine"] == machine || return false
        rebuilt["machine_sha256"] == row["machine_sha256"] || return false
        rebuilt["predictive_signature_sha256"] == row["predictive_signature_sha256"] || return false
        rebuilt["state_signature_sha256"] == Vector{String}(row["state_signature_sha256"]) || return false
    end
    true
end

function reconstruct_short_horizon_matched_pairs(test_rows)
    signatures = Dict(row["machine_sha256"] => predictive_signature(machine_from_json(row["machine"])) for row in test_rows)
    remaining = String[row["machine_sha256"] for row in test_rows]
    pairs = Vector{Vector{String}}()
    while !isempty(remaining)
        left = popfirst!(remaining)
        best = remaining[1]
        best_key = (
            short_horizon_distance(signatures[left], signatures[best]),
            -long_horizon_distance(signatures[left], signatures[best]),
            best,
        )
        for candidate_hash in @view remaining[2:end]
            candidate_key = (
                short_horizon_distance(signatures[left], signatures[candidate_hash]),
                -long_horizon_distance(signatures[left], signatures[candidate_hash]),
                candidate_hash,
            )
            if isless(candidate_key, best_key)
                best = candidate_hash
                best_key = candidate_key
            end
        end
        deleteat!(remaining, findfirst(==(best), remaining))
        push!(pairs, [left, best])
    end
    pairs
end

function pair_measurements(test_rows, pairs)
    signatures = Dict(row["machine_sha256"] => predictive_signature(machine_from_json(row["machine"])) for row in test_rows)
    [Dict(
        "left_machine_sha256" => left,
        "right_machine_sha256" => right,
        "length_1_2_l1" => [numerator(short_horizon_distance(signatures[left], signatures[right])), denominator(short_horizon_distance(signatures[left], signatures[right]))],
        "length_3_8_l1" => [numerator(long_horizon_distance(signatures[left], signatures[right])), denominator(long_horizon_distance(signatures[left], signatures[right]))],
    ) for (left, right) in pairs]
end

function package_versions()
    Dict(
        "julia" => string(VERSION),
        "Graphs" => string(pkgversion(Graphs)),
        "JSON" => string(pkgversion(JSON)),
    )
end

function git_file_sha256(commit::String, path::String)
    bytes2hex(SHA.sha256(read(`git -C $REPO show $(commit):$(rel(path))`)))
end

function source_hash_receipt(prereg)
    actual = Dict(
        "spec_sha256" => sha256_file(SPEC_PATH),
        "preregistration_receipt_sha256" => sha256_file(PREREG_PATH),
        "object_manifest_sha256" => sha256_file(MANIFEST_PATH),
        "readme_sha256" => sha256_file(README_PATH),
        "manifest_generator_sha256" => sha256_file(GENERATOR_PATH),
        "wizard_v4_3_object_card_sha256" => sha256_file(OBJECT_CARD_PATH),
        "correction_sha256" => sha256_file(CORRECTION_PATH),
    )
    authoritative_commit = Dict(
        "spec_sha256" => git_file_sha256(EXPECTED_COMMIT, SPEC_PATH),
        "preregistration_receipt_sha256" => git_file_sha256(EXPECTED_COMMIT, PREREG_PATH),
        "object_manifest_sha256" => git_file_sha256(EXPECTED_COMMIT, MANIFEST_PATH),
        "readme_sha256" => git_file_sha256(EXPECTED_COMMIT, README_PATH),
        "manifest_generator_sha256" => git_file_sha256(EXPECTED_COMMIT, GENERATOR_PATH),
        "wizard_v4_3_object_card_sha256" => git_file_sha256(EXPECTED_COMMIT, OBJECT_CARD_PATH),
        "correction_sha256" => git_file_sha256(EXPECTED_COMMIT, CORRECTION_PATH),
    )
    receipt_bindings = Dict(
        "spec" => actual["spec_sha256"] == prereg["spec_sha256"],
        "object_manifest" => actual["object_manifest_sha256"] == prereg["object_manifest_sha256"],
        "readme" => actual["readme_sha256"] == prereg["readme_sha256"],
        "manifest_generator" => actual["manifest_generator_sha256"] == prereg["manifest_generator_sha256"],
        "wizard_v4_3_object_card" => actual["wizard_v4_3_object_card_sha256"] == prereg["wizard_v4_3_object_card_sha256"],
        "correction" => actual["correction_sha256"] == prereg["correction_sha256"],
    )
    commit_bindings = Dict(key => actual[key] == authoritative_commit[key] for key in keys(authoritative_commit))
    Dict(
        "actual" => actual,
        "authoritative_commit" => authoritative_commit,
        "receipt_bindings" => receipt_bindings,
        "authoritative_commit_bindings" => commit_bindings,
        "pass" => all(values(receipt_bindings)) && all(values(commit_bindings)),
    )
end

function build_result()
    spec = JSON.parsefile(SPEC_PATH)
    prereg = JSON.parsefile(PREREG_PATH)
    manifest = JSON.parsefile(MANIFEST_PATH)
    hash_receipt = source_hash_receipt(prereg)
    start_counter, stop_counter = Int.(spec["object_family"]["candidate_counter_interval"])
    rebuilt, rejected = rebuild_registry(start_counter, stop_counter)
    selected_count = sum(Int(spec["frozen_splits"][key]) for key in ("train_objects", "validation_objects", "test_objects"))
    selected = rebuilt[1:selected_count]
    declared = manifest_rows(manifest)
    split_hashes = Dict(key => String[row["machine_sha256"] for row in manifest["splits"][key]] for key in ("train", "validation", "test"))
    all_split_hashes = vcat(values(split_hashes)...)
    reconstructed_pairs = reconstruct_short_horizon_matched_pairs(manifest["splits"]["test"])
    declared_pairs = [Vector{String}(pair) for pair in manifest["hard_negative_test_pairs"]]
    measurements = pair_measurements(manifest["splits"]["test"], reconstructed_pairs)
    graph_negative_scc_count = graph_scc_count([(0, 1), (1, 0), (2, 3), (3, 2)])
    graph_boundary_scc_count = graph_scc_count([(0, 1), (1, 2), (2, 3), (3, 0)])
    current_commit = readchomp(`git -C $REPO rev-parse HEAD`)
    correction_commit_is_ancestor = success(`git -C $REPO merge-base --is-ancestor $EXPECTED_COMMIT HEAD`)
    expected_rejected = Dict(String(key) => Int(value) for (key, value) in manifest["rejected_counts"])
    original_spec_hash = String(prereg["original_frozen_spec_sha256"])
    selected_hashes = String[row["machine_sha256"] for row in selected]
    manifest_top_level_keys = Set([
        "accepted_candidate_count", "candidate_interval", "classification", "formal_admission_allowed",
        "hard_negative_test_pairs", "model_input_excludes_manifest_identity_fields", "promotion_allowed",
        "rejected_counts", "schema", "selection", "sim_id", "spec_sha256", "splits", "test_outcome_status",
    ])
    manifest_row_keys = Set(["counter", "machine", "machine_sha256", "predictive_signature_sha256", "state_signature_sha256"])

    gates = Dict(
        "correction_commit_is_ancestor" => correction_commit_is_ancestor,
        "current_v2_source_hashes" => hash_receipt["pass"],
        "spec_v2_schema" => spec["schema"] == "codex_ratchet.unseen_finite_predictive_objects_v0.spec.v2",
        "preregistration_v2_schema" => prereg["schema"] == "codex_ratchet.unseen_finite_predictive_objects_v0.preregistration.v2",
        "manifest_v1_schema" => manifest["schema"] == "codex_ratchet.unseen_finite_predictive_objects_v0.object_manifest.v1",
        "source_sim_id_and_classification" => spec["sim_id"] == prereg["sim_id"] == manifest["sim_id"] == SIM_ID && spec["classification"] == prereg["classification"] == manifest["classification"] == CLASSIFICATION,
        "source_admission_locks" => spec["promotion_allowed"] == prereg["promotion_allowed"] == manifest["promotion_allowed"] == false && spec["formal_admission_allowed"] == prereg["formal_admission_allowed"] == manifest["formal_admission_allowed"] == false,
        "correction_paths" => spec["engine_contract"]["correction_path"] == prereg["correction_path"] == rel(CORRECTION_PATH),
        "manifest_original_frozen_spec_binding" => manifest["spec_sha256"] == original_spec_hash == spec["engine_contract"]["original_frozen_spec_sha256"],
        "current_spec_distinct_from_original_frozen_spec" => hash_receipt["actual"]["spec_sha256"] == prereg["spec_sha256"] && hash_receipt["actual"]["spec_sha256"] != original_spec_hash,
        "immutable_manifest_hash" => hash_receipt["actual"]["object_manifest_sha256"] == prereg["object_manifest_sha256"] == "2894501dad5d689c00a2dd4ef7dc378803e5282f10f52122c064a6c028caa462",
        "superseded_preregistration_binding" => prereg["superseded_preregistration_sha256"] == "be65a924c48150a24866515fc256a3a191768d6908c287d7f3f7326a94e65e2f",
        "manifest_top_level_field_coverage" => Set(String.(keys(manifest))) == manifest_top_level_keys,
        "manifest_row_field_coverage" => all(Set(String.(keys(row))) == manifest_row_keys for row in declared),
        "object_family_semantics" => spec["object_family"]["kind"] == "minimal strongly connected four-state binary unifilar process" && Int(spec["object_family"]["state_count"]) == STATE_COUNT && Vector{Int}(spec["object_family"]["output_alphabet"]) == [0, 1] && Vector{Int}(spec["object_family"]["p_one_numerators_over_8"]) == [2, 3, 4, 5, 6] && spec["object_family"]["candidate_namespace"] == CANDIDATE_NAMESPACE && Int(spec["object_family"]["signature_coordinate_count"]) == WORD_COORDINATE_COUNT,
        "canonicalization_semantics" => spec["object_family"]["canonicalization"] == "lexicographically minimal machine tuple over all 24 state permutations" && spec["object_family"]["minimality_witness"] == "all four state-conditioned exact word-probability signatures through length eight are distinct" && spec["object_family"]["object_equivalence"] == "identical exact uniform-start word-probability vectors for lengths one through eight",
        "semantic_owner_and_disagreement_policy" => spec["engine_contract"]["semantic_owner"] == "Julia independent exact finite predictive equivalence verification and arbitration" && spec["engine_contract"]["julia_disagreement_policy"] == "any Julia disagreement with the frozen Python registry blocks the packet and every learner interpretation; the registry is not repaired after test sealing" && spec["engine_contract"]["peer_result_reads"] == false,
        "manifest_selection_semantics" => manifest["selection"] == "first 192 after canonical machine hash sort" && spec["frozen_splits"]["selection"] == "canonicalize and deduplicate the full counter interval, sort by canonical machine SHA-256, then take the first 192 objects without outcome-based replacement",
        "manifest_test_seal_semantics" => manifest["test_outcome_status"] == "machine registry and exact pair declarations frozen; no learned test metric exists" && manifest["model_input_excludes_manifest_identity_fields"] == true,
        "candidate_interval" => [start_counter, stop_counter] == Vector{Int}(manifest["candidate_interval"]),
        "accepted_candidate_count" => length(rebuilt) == Int(manifest["accepted_candidate_count"]) == Int(prereg["accepted_candidate_count"]),
        "rejected_counts" => rejected == expected_rejected,
        "selected_count" => length(selected) == Int(prereg["selected_object_count"]) == 192,
        "every_selected_semantic_field" => selected_rows_match(selected, declared),
        "canonical_state_permutation_form" => all(row["machine"] == canonical_machine(row["machine"]) for row in selected),
        "graphs_strong_connectivity" => all(graph_scc_count(row["machine"]) == 1 for row in selected),
        "minimality" => all(length(Set(state_signature(row["machine"], state) for state in 0:(STATE_COUNT - 1))) == STATE_COUNT for row in selected),
        "predictive_signature_coordinate_count" => all(length(row["predictive_signature"]) == WORD_COORDINATE_COUNT for row in selected),
        "predictive_signature_hashes" => all(signature_hash(row["predictive_signature"]) == row["predictive_signature_sha256"] for row in selected),
        "split_counts" => length(split_hashes["train"]) == Int(spec["frozen_splits"]["train_objects"]) == Int(prereg["split_counts"]["train"]) == 128 && length(split_hashes["validation"]) == Int(spec["frozen_splits"]["validation_objects"]) == Int(prereg["split_counts"]["validation"]) == 32 && length(split_hashes["test"]) == Int(spec["frozen_splits"]["test_objects"]) == Int(prereg["split_counts"]["test"]) == 32,
        "split_assignment_and_order" => split_hashes["train"] == selected_hashes[1:128] && split_hashes["validation"] == selected_hashes[129:160] && split_hashes["test"] == selected_hashes[161:192],
        "split_uniqueness" => length(all_split_hashes) == length(Set(all_split_hashes)) == 192,
        "short_horizon_matched_declaration_count" => length(declared_pairs) == Int(prereg["short_horizon_matched_test_pair_count"]) == 16,
        "short_horizon_matched_declarations" => reconstructed_pairs == declared_pairs,
        "short_horizon_matched_test_only_and_exhaustive" => Set(vcat(declared_pairs...)) == Set(split_hashes["test"]) && length(vcat(declared_pairs...)) == 32,
        "short_horizon_matched_measurements" => length(measurements) == 16 && all(row["length_1_2_l1"][2] > 0 && row["length_3_8_l1"][2] > 0 for row in measurements),
        "graphs_negative_control" => graph_negative_scc_count == 2,
        "graphs_boundary_control" => graph_boundary_scc_count == 1,
        "no_peer_result_reads" => true,
    )
    engine_all_pass = all(values(gates))
    capability_receipts = [
        Dict(
            "receipt_id" => "julia_Graphs_unifilar_strong_connectivity",
            "tool" => "Graphs",
            "computed_what" => "SCC counts for all 192 rebuilt selected machines plus disconnected and cycle controls",
            "status" => "used",
        ),
        Dict(
            "receipt_id" => "julia_SHA_exact_registry_hashes",
            "tool" => "SHA",
            "computed_what" => "source, canonical machine, exact state-signature, and exact predictive-signature SHA-256 values",
            "status" => "used",
        ),
    ]
    tool_calls = [
        Dict(
            "receipt_id" => "julia_Graphs_unifilar_strong_connectivity",
            "tool" => "Graphs",
            "qualified_api/function" => "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.strongly_connected_components",
            "input_object" => "four-state binary unifilar transition rows rebuilt from counters 0:4095",
            "output_object" => "SCC count per selected canonical machine",
            "positive_case" => "all 192 selected machines have one SCC",
            "negative/erased_control" => "two disconnected two-cycles have two SCCs",
            "boundary_case" => "one directed four-cycle has one SCC",
            "demotion_condition" => "any selected SCC count differs from one or either control misses its expected count",
            "gates" => ["graphs_strong_connectivity", "graphs_negative_control", "graphs_boundary_control", "engine_all_pass"],
        ),
        Dict(
            "receipt_id" => "julia_SHA_exact_registry_hashes",
            "tool" => "SHA",
            "qualified_api/function" => "SHA.sha256",
            "input_object" => "frozen source bytes and compact JSON encodings of canonical machines and Rational numerator-denominator vectors",
            "output_object" => "source, machine, state-signature, and predictive-signature SHA-256 values",
            "positive_case" => "all correction-era source hashes, original manifest binding, and all 192 selected exact signature hashes match",
            "negative/erased_control" => "a missing, altered, or provenance-misbound source fails current_v2_source_hashes",
            "boundary_case" => "length-one through length-eight signatures contain exactly 510 coordinates",
            "demotion_condition" => "any hash mismatch, coordinate-count mismatch, or noncanonical JSON input",
            "gates" => ["current_v2_source_hashes", "manifest_original_frozen_spec_binding", "every_selected_semantic_field", "predictive_signature_hashes", "engine_all_pass"],
        ),
    ]
    project_path = Base.active_project()
    project_dir = dirname(project_path)
    julia_manifest_path = joinpath(project_dir, "Manifest.toml")
    Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "object_id" => "$(SIM_ID)_$(ENGINE)",
        "engine" => ENGINE,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "generated_at" => now_z(),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "reads_peer_result" => false,
        "peer_result_paths_read" => String[],
        "correction_commit_provenance" => Dict(
            "correction_commit" => EXPECTED_COMMIT,
            "current_head" => current_commit,
            "correction_commit_is_ancestor" => correction_commit_is_ancestor,
            "blob_hashes_verified_against_correction_commit" => hash_receipt["pass"],
        ),
        "runtime" => Dict(
            "command" => "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v7/sims/unseen_finite_predictive_objects_v0/run_julia.jl",
            "julia_executable" => joinpath(Sys.BINDIR, Base.julia_exename()),
            "julia_version" => string(VERSION),
            "active_project" => project_path,
            "project_sha256" => sha256_file(project_path),
            "manifest_path" => julia_manifest_path,
            "manifest_sha256" => sha256_file(julia_manifest_path),
            "load_path" => copy(Base.LOAD_PATH),
            "package_versions" => package_versions(),
        ),
        "packages_used" => ["Graphs", "JSON", "SHA", "Dates", "Pkg"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing strong-connectivity gate and controls"),
            "SHA" => Dict("tried" => true, "used" => true, "reason" => "load-bearing frozen-source and exact-signature hash gates"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive frozen input and compact result serialization"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "SHA" => "load_bearing", "JSON" => "supportive"),
        "capability_receipts" => capability_receipts,
        "tool_calls" => tool_calls,
        "one_to_one_tool_calls" => Dict(
            "pass" => [row["receipt_id"] for row in capability_receipts] == [row["receipt_id"] for row in tool_calls],
            "receipt_ids" => [row["receipt_id"] for row in tool_calls],
        ),
        "hash_verification" => hash_receipt,
        "rebuild" => Dict(
            "candidate_count" => stop_counter - start_counter + 1,
            "accepted_candidate_count" => length(rebuilt),
            "rejected_counts" => rejected,
            "selected_object_count" => length(selected),
            "word_probability_arithmetic" => "Rational{Int}",
            "word_lengths" => [1, MAX_WORD_LENGTH],
            "signature_coordinate_count" => WORD_COORDINATE_COUNT,
            "state_permutations_checked_per_machine" => length(STATE_PERMUTATIONS),
            "short_horizon_matched_declarations_verified" => count(zip(reconstructed_pairs, declared_pairs)) do pair
                pair[1] == pair[2]
            end,
            "short_horizon_matched_declaration_count" => length(declared_pairs),
            "short_horizon_matched_measurement_sha256" => canonical_json_hash(measurements),
            "sealed_manifest_pair_key" => "hard_negative_test_pairs",
            "graphs_controls" => Dict("disconnected_two_cycles_scc_count" => graph_negative_scc_count, "directed_four_cycle_scc_count" => graph_boundary_scc_count),
        ),
        "gates" => gates,
        "engine_all_pass" => engine_all_pass,
        "all_pass" => engine_all_pass,
        "controller_status" => "pending_all_three_engine_assembly",
        "claim_status" => "red_ceiling_pending_controller",
        "claim_ceiling" => spec["accepted_red_ceiling"],
        "green_ceiling_not_claimed" => spec["accepted_green_ceiling"],
        "blocked_consumers" => spec["blocked_consumers"],
    )
end

function main()
    mkpath(dirname(RESULT_PATH))
    payload = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload)
        write(io, '\n')
    end
    println(JSON.json(Dict(
        "engine_all_pass" => payload["engine_all_pass"],
        "claim_status" => payload["claim_status"],
        "result_path" => rel(RESULT_PATH),
    )))
    payload["engine_all_pass"] ? 0 : 1
end

exit(main())
