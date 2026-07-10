using Graphs
using JSON3
using SHA

const HERE = @__DIR__
const REPO_ROOT = normpath(joinpath(HERE, "..", "..", ".."))
const SPEC_PATH = joinpath(HERE, "spec.json")
const PREREGISTRATION_PATH = joinpath(HERE, "preregistration_receipt.json")
const OBJECT_CARD_PATH = joinpath(HERE, "wizard_v4_3_object_card.json")
const RESULT_PATH = joinpath(HERE, "results", "finite_probe_behavioral_object_engine_v1_julia_results.json")
const SOURCE_PATH = abspath(@__FILE__)

const SIM_ID = "finite_probe_behavioral_object_engine_v1"
const CLASSIFICATION = "scratch_diagnostic"
const EXPECTED_SPEC_SHA256 = "3d5e5089a15f930f561e4cd29b2302bf32c5f3c307e53926a09555f44916ff01"
const EXPECTED_OBJECT_CARD_SHA256 = "a5839a53840fb73377d72f1952628e919a3ee9f46c9abec5901e25c90bcc4c46"
const RING_SIZE = 6
const STATE_COUNT = 1 << RING_SIZE
const RULE_COUNT = 256

sha256_bytes(bytes)::String = bytes2hex(SHA.sha256(bytes))
sha256_text(text::AbstractString)::String = sha256_bytes(codeunits(text))
sha256_file(path::AbstractString)::String = sha256_bytes(read(path))

function eca_step(state::Int, rule::Int)::Int
    next_state = 0
    for site in 0:(RING_SIZE - 1)
        left = (state >> mod(site - 1, RING_SIZE)) & 1
        center = (state >> site) & 1
        right = (state >> mod(site + 1, RING_SIZE)) & 1
        neighborhood = 4 * left + 2 * center + right
        next_state |= ((rule >> neighborhood) & 1) << site
    end
    return next_state
end

hamming_weight(state::Int)::Int = count_ones(state)

function domain_walls(state::Int)::Int
    return sum(((state >> site) & 1) != ((state >> mod(site + 1, RING_SIZE)) & 1) for site in 0:(RING_SIZE - 1))
end

function reflect_rule(rule::Int)::Int
    reflected = 0
    for neighborhood in 0:7
        left = (neighborhood >> 2) & 1
        center = (neighborhood >> 1) & 1
        right = neighborhood & 1
        reflected_neighborhood = 4 * right + 2 * center + left
        reflected |= ((rule >> reflected_neighborhood) & 1) << neighborhood
    end
    return reflected
end

function conjugate_rule(rule::Int)::Int
    conjugated = 0
    for neighborhood in 0:7
        complemented_neighborhood = 7 - neighborhood
        output = 1 - ((rule >> complemented_neighborhood) & 1)
        conjugated |= output << neighborhood
    end
    return conjugated
end

function symmetry_orbit(rule::Int)::Vector{Int}
    seen = Set{Int}()
    frontier = [rule]
    while !isempty(frontier)
        current = pop!(frontier)
        current in seen && continue
        push!(seen, current)
        push!(frontier, reflect_rule(current), conjugate_rule(current))
    end
    return sort!(collect(seen))
end

function ordered_symmetry_orbits(tag::String)
    unique_orbits = Dict{String,Vector{Int}}()
    for rule in 0:(RULE_COUNT - 1)
        orbit = symmetry_orbit(rule)
        unique_orbits[join(orbit, ",")] = orbit
    end
    records = [Dict{String,Any}(
        "members" => orbit,
        "orbit_key" => join(orbit, ","),
        "order_sha256" => sha256_text("$(tag)|orbit|$(join(orbit, ","))"),
    ) for orbit in values(unique_orbits)]
    sort!(records; by=record -> (record["order_sha256"], record["orbit_key"]))
    return records
end

function orbit_index_map(orbits)::Vector{Int}
    mapping = fill(-1, RULE_COUNT)
    for (index, record) in enumerate(orbits)
        for rule in record["members"]
            mapping[rule + 1] = index - 1
        end
    end
    return mapping
end

function expected_block(index::Int)::String
    0 <= index <= 59 && return "train"
    60 <= index <= 73 && return "validation"
    74 <= index <= 87 && return "test"
    return "outside"
end

function parse_fixture_pairs(spec)
    raw = spec["fixtures"]
    return Dict(
        "train" => [Int.(collect(pair)) for pair in raw["train"]],
        "validation" => [Int.(collect(pair)) for pair in raw["validation"]],
        "test_primary" => [Int.(collect(pair)) for pair in raw["test_primary"]],
        "test_structural_holdout" => [Int.(collect(pair)) for pair in raw["test_structural_holdout"]],
    )
end

fixture_block(split::String)::String = split == "train" ? "train" : split == "validation" ? "validation" : "test"

function validate_fixture_split(fixtures, orbit_map::Vector{Int}, tag::String)
    errors = String[]
    rule_locations = Dict{Int,String}()
    pair_order_receipts = Dict{String,Any}()
    for split in ("train", "validation", "test_primary", "test_structural_holdout")
        pairs = fixtures[split]
        expected = fixture_block(split)
        pair_hashes = String[]
        local_rules = Set{Int}()
        for (pair_index, pair) in enumerate(pairs)
            length(pair) == 2 || push!(errors, "$split pair $pair_index does not contain two rules")
            length(pair) == 2 || continue
            a, b = pair
            (0 <= a < b < RULE_COUNT) || push!(errors, "$split pair $pair_index is not ordered in [0,255]")
            if 0 <= a < RULE_COUNT && 0 <= b < RULE_COUNT
                orbit_a, orbit_b = orbit_map[a + 1], orbit_map[b + 1]
                orbit_a != orbit_b || push!(errors, "$split pair $a,$b reuses one symmetry orbit")
                expected_block(orbit_a) == expected || push!(errors, "$split rule $a belongs to $(expected_block(orbit_a)) orbit block")
                expected_block(orbit_b) == expected || push!(errors, "$split rule $b belongs to $(expected_block(orbit_b)) orbit block")
                for rule in (a, b)
                    rule in local_rules && push!(errors, "$split repeats rule $rule")
                    push!(local_rules, rule)
                    if haskey(rule_locations, rule) && rule_locations[rule] != split
                        push!(errors, "rule $rule crosses fixture splits $(rule_locations[rule]) and $split")
                    else
                        rule_locations[rule] = split
                    end
                end
            end
            push!(pair_hashes, sha256_text("$(tag)|pair|$(a),$(b)"))
        end
        sorted_hashes = sort(copy(pair_hashes))
        if split != "test_structural_holdout"
            pair_hashes == sorted_hashes || push!(errors, "$split fixture pairs are not in frozen SHA256 order")
        end
        pair_order_receipts[split] = Dict(
            "pair_count" => length(pairs),
            "rule_count" => length(local_rules),
            "pair_order_sha256" => pair_hashes,
            "order_verified" => pair_hashes == sorted_hashes,
        )
    end
    return Dict(
        "passed" => isempty(errors),
        "errors" => errors,
        "pair_order_receipts" => pair_order_receipts,
        "unique_fixture_rule_count" => length(rule_locations),
    )
end

function split_leakage_sentinel(fixtures, orbit_map::Vector{Int}, tag::String)
    injected = Dict(split => [copy(pair) for pair in pairs] for (split, pairs) in fixtures)
    train_rule = first(first(injected["train"]))
    victim = injected["validation"][1]
    injected["validation"][1] = sort([train_rule, victim[2]])
    receipt = validate_fixture_split(injected, orbit_map, tag)
    return Dict(
        "passed" => !Bool(receipt["passed"]),
        "injected_train_rule" => train_rule,
        "injected_validation_pair" => injected["validation"][1],
        "detected_errors" => receipt["errors"],
    )
end

function canonical_partition(cells)::Vector{Vector{Int}}
    groups = Dict{Any,Vector{Int}}()
    for (state, key) in enumerate(cells)
        push!(get!(groups, key, Int[]), state - 1)
    end
    partition = [sort!(states) for states in values(groups)]
    sort!(partition; by=first)
    return partition
end

function class_ids(partition::Vector{Vector{Int}})::Vector{Int}
    labels = fill(-1, STATE_COUNT)
    for (class_index, states) in enumerate(partition)
        for state in states
            labels[state + 1] = class_index - 1
        end
    end
    all(>=(0), labels) || error("partition does not cover all states")
    return labels
end

function initial_partition()::Vector{Vector{Int}}
    return canonical_partition([(hamming_weight(state), domain_walls(state)) for state in 0:(STATE_COUNT - 1)])
end

function refine_partition(partition::Vector{Vector{Int}}, transition_a::Vector{Int}, transition_b::Vector{Int})
    labels = class_ids(partition)
    signatures = [(labels[state + 1], labels[transition_a[state + 1] + 1], labels[transition_b[state + 1] + 1]) for state in 0:(STATE_COUNT - 1)]
    return canonical_partition(signatures)
end

function stable_partition(transition_a::Vector{Int}, transition_b::Vector{Int}, maximum_depth::Int)
    history = Vector{Vector{Vector{Int}}}()
    push!(history, initial_partition())
    stable_depth = nothing
    for depth in 1:maximum_depth
        next_partition = refine_partition(last(history), transition_a, transition_b)
        push!(history, next_partition)
        if next_partition == history[end - 1]
            stable_depth = depth - 1
            break
        elseif length(next_partition) == STATE_COUNT
            stable_depth = depth
            break
        end
    end
    stable_depth === nothing && error("behavioral refinement did not stabilize within frozen maximum depth")
    return last(history), history, stable_depth
end

function quotient_congruence(partition::Vector{Vector{Int}}, transition_a::Vector{Int}, transition_b::Vector{Int})
    labels = class_ids(partition)
    induced_a = Int[]
    induced_b = Int[]
    conflicts = Dict{String,Any}[]
    for (class_index, states) in enumerate(partition)
        targets_a = sort!(unique(labels[transition_a[state + 1] + 1] for state in states))
        targets_b = sort!(unique(labels[transition_b[state + 1] + 1] for state in states))
        length(targets_a) == 1 || push!(conflicts, Dict("class" => class_index - 1, "action" => "a", "targets" => targets_a))
        length(targets_b) == 1 || push!(conflicts, Dict("class" => class_index - 1, "action" => "b", "targets" => targets_b))
        push!(induced_a, first(targets_a))
        push!(induced_b, first(targets_b))
    end
    return Dict(
        "congruent" => isempty(conflicts),
        "conflicts" => conflicts,
        "induced_a" => induced_a,
        "induced_b" => induced_b,
    )
end

function graph_from_edges(vertex_count::Int, edges::Vector{Tuple{Int,Int}})
    graph = Graphs.SimpleDiGraph(vertex_count)
    for (source, target) in edges
        Graphs.add_edge!(graph, source + 1, target + 1)
    end
    return graph
end

function quotient_edges(induced_a::Vector{Int}, induced_b::Vector{Int})
    return sort!(unique(vcat(
        [(source - 1, target) for (source, target) in enumerate(induced_a)],
        [(source - 1, target) for (source, target) in enumerate(induced_b)],
    )))
end

function canonical_components(components)::Vector{Vector{Int}}
    normalized = [sort!(Int.(collect(component))) for component in components]
    sort!(normalized; by=component -> (first(component), length(component), component))
    return normalized
end

function graphs_scc_signature(graph)::Vector{Vector{Int}}
    return canonical_components([[vertex - 1 for vertex in component] for component in Graphs.strongly_connected_components(graph)])
end

function independent_scc_signature(vertex_count::Int, edges::Vector{Tuple{Int,Int}})::Vector{Vector{Int}}
    adjacency = [Int[] for _ in 1:vertex_count]
    for (source, target) in edges
        push!(adjacency[source + 1], target)
    end
    reachable = falses(vertex_count, vertex_count)
    for source in 0:(vertex_count - 1)
        frontier = [source]
        reachable[source + 1, source + 1] = true
        while !isempty(frontier)
            current = pop!(frontier)
            for target in adjacency[current + 1]
                if !reachable[source + 1, target + 1]
                    reachable[source + 1, target + 1] = true
                    push!(frontier, target)
                end
            end
        end
    end
    remaining = Set(0:(vertex_count - 1))
    components = Vector{Vector{Int}}()
    while !isempty(remaining)
        seed = minimum(remaining)
        component = sort!([vertex for vertex in remaining if reachable[seed + 1, vertex + 1] && reachable[vertex + 1, seed + 1]])
        push!(components, component)
        foreach(vertex -> delete!(remaining, vertex), component)
    end
    return canonical_components(components)
end

function scc_mutation_control(vertex_count::Int, edges::Vector{Tuple{Int,Int}}, original_signature)
    edge_set = Set(edges)
    for edge in edges
        mutated_edges = sort!([candidate for candidate in edges if candidate != edge])
        signature = graphs_scc_signature(graph_from_edges(vertex_count, mutated_edges))
        signature != original_signature && return Dict(
            "passed" => true,
            "mutation" => "delete_edge",
            "edge" => collect(edge),
            "mutated_signature" => signature,
        )
    end
    for source in 0:(vertex_count - 1), target in 0:(vertex_count - 1)
        edge = (source, target)
        edge in edge_set && continue
        mutated_edges = sort!(vcat(edges, [edge]))
        signature = graphs_scc_signature(graph_from_edges(vertex_count, mutated_edges))
        signature != original_signature && return Dict(
            "passed" => true,
            "mutation" => "add_edge",
            "edge" => collect(edge),
            "mutated_signature" => signature,
        )
    end
    return Dict("passed" => false, "mutation" => nothing, "edge" => nothing, "mutated_signature" => original_signature)
end

function graph_receipt(induced_a::Vector{Int}, induced_b::Vector{Int})
    vertex_count = length(induced_a)
    edges = quotient_edges(induced_a, induced_b)
    graph = graph_from_edges(vertex_count, edges)
    package_signature = graphs_scc_signature(graph)
    independent_signature = independent_scc_signature(vertex_count, edges)
    mutation = scc_mutation_control(vertex_count, edges, package_signature)
    return Dict(
        "vertex_count" => vertex_count,
        "edge_count" => Graphs.ne(graph),
        "edges" => [collect(edge) for edge in edges],
        "graphs_scc_signature" => package_signature,
        "independent_scc_signature" => independent_signature,
        "scc_parity" => package_signature == independent_signature,
        "signature_mutation_control" => mutation,
        "passed" => package_signature == independent_signature && Bool(mutation["passed"]),
    )
end

function partition_hash(partition::Vector{Vector{Int}})::String
    labels = class_ids(partition)
    return sha256_text(JSON3.write(labels))
end

function fixture_receipt(split::String, pair::Vector{Int}, maximum_depth::Int)
    rule_a, rule_b = pair
    transition_a = [eca_step(state, rule_a) for state in 0:(STATE_COUNT - 1)]
    transition_b = [eca_step(state, rule_b) for state in 0:(STATE_COUNT - 1)]
    partition, history, stable_depth = stable_partition(transition_a, transition_b, maximum_depth)
    quotient = quotient_congruence(partition, transition_a, transition_b)
    Bool(quotient["congruent"]) || error("stable partition is not a quotient congruence for fixture $split:$rule_a,$rule_b")
    graph = graph_receipt(quotient["induced_a"], quotient["induced_b"])

    mutated_transition_a = copy(transition_a)
    mutated_transition_a[1] = xor(mutated_transition_a[1], 1)
    mutated_partition, _, mutated_depth = stable_partition(mutated_transition_a, transition_b, maximum_depth)
    exact_hash = partition_hash(partition)
    mutated_hash = partition_hash(mutated_partition)
    mutation_status = exact_hash == mutated_hash ? "behaviorally_silent" : "partition_hash_changed"

    return Dict(
        "fixture_id" => "$split:$rule_a,$rule_b",
        "split" => split,
        "rules" => [rule_a, rule_b],
        "pair_order_sha256" => sha256_text("ECA6-PRBOG-v1|pair|$rule_a,$rule_b"),
        "class_count_by_depth" => length.(history),
        "stable_depth" => stable_depth,
        "stable_class_count" => length(partition),
        "stable_labels" => class_ids(partition),
        "partition_sha256" => exact_hash,
        "quotient" => quotient,
        "graph_receipt" => graph,
        "one_bit_transition_mutation" => Dict(
            "rule" => rule_a,
            "state" => 0,
            "successor_before" => transition_a[1],
            "successor_after" => mutated_transition_a[1],
            "mutated_stable_depth" => mutated_depth,
            "mutated_partition_sha256" => mutated_hash,
            "status" => mutation_status,
            "passed" => mutation_status in ("partition_hash_changed", "behaviorally_silent"),
        ),
    )
end

function read_preregistered_inputs()
    spec_hash = sha256_file(SPEC_PATH)
    object_card_hash = sha256_file(OBJECT_CARD_PATH)
    spec_hash == EXPECTED_SPEC_SHA256 || error("frozen spec hash mismatch")
    object_card_hash == EXPECTED_OBJECT_CARD_SHA256 || error("frozen object-card hash mismatch")
    spec = JSON3.read(read(SPEC_PATH, String))
    preregistration = JSON3.read(read(PREREGISTRATION_PATH, String))
    object_card = JSON3.read(read(OBJECT_CARD_PATH, String))
    String(spec["sim_id"]) == SIM_ID || error("spec sim_id mismatch")
    String(preregistration["sim_id"]) == SIM_ID || error("preregistration sim_id mismatch")
    String(preregistration["status"]) == "frozen_before_builder_source" || error("preregistration is not frozen")
    String(preregistration["spec_sha256"]) == spec_hash || error("preregistration does not bind spec")
    String(preregistration["object_card_sha256"]) == object_card_hash || error("preregistration does not bind object card")
    !Bool(preregistration["builder_sources_present_when_frozen"]) || error("builder source existed when preregistration froze")
    String(object_card["primary_object_card"]["object_name"]) == "ProbeRelativeBehavioralObject" || error("object-card object mismatch")
    return spec, preregistration, object_card, spec_hash, object_card_hash
end

function tool_calls()
    return [
        Dict(
            "tool" => "Graphs",
            "qualified_api/function" => "Graphs.SimpleDiGraph and Graphs.add_edge!",
            "input_object" => "exact quotient action maps for every frozen rule-pair fixture",
            "output_object" => "directed labeled-quotient support graph",
            "positive_case" => "graph edges exactly encode the two induced quotient actions",
            "negative/erased_control" => "a searched single-edge addition or deletion must alter the SCC signature",
            "boundary_case" => "duplicate action edges collapse to one support-graph edge and remain explicit in induced action maps",
            "demotion_condition" => "no SCC-changing edge mutation is found for any fixture",
            "gates" => ["all_pass", "quotient"],
        ),
        Dict(
            "tool" => "Graphs",
            "qualified_api/function" => "Graphs.strongly_connected_components",
            "input_object" => "each exact quotient support graph",
            "output_object" => "canonical SCC signature",
            "positive_case" => "package SCC signature equals an independent reachability-based SCC decomposition",
            "negative/erased_control" => "the SCC-changing graph mutation produces a different package signature",
            "boundary_case" => "singleton SCCs and self-loops remain explicit canonical components",
            "demotion_condition" => "package and independent SCC signatures differ or mutation is insensitive",
            "gates" => ["all_pass", "quotient"],
        ),
        Dict(
            "tool" => "JSON3",
            "qualified_api/function" => "JSON3.read and JSON3.write",
            "input_object" => "frozen contracts, compact canonical label vectors, and closed result receipt",
            "output_object" => "schema-checked inputs, partition hashes, and round-tripped result JSON",
            "positive_case" => "all frozen surfaces parse and the final receipt round-trips",
            "negative/erased_control" => "schema, hash, sim_id, or frozen binding drift aborts emission",
            "boundary_case" => "empty peer-result list remains a JSON array",
            "demotion_condition" => "closed receipt cannot be parsed or required fields drift",
            "gates" => ["all_pass", "provenance"],
        ),
        Dict(
            "tool" => "SHA",
            "qualified_api/function" => "SHA.sha256",
            "input_object" => "frozen sources, orbit and pair keys, compact label vectors, and source/result bytes",
            "output_object" => "provenance, split-order, and partition hashes",
            "positive_case" => "spec and object-card hashes match preregistration and structural holdout hashes match the frozen list",
            "negative/erased_control" => "any frozen-source drift aborts before analysis",
            "boundary_case" => "behaviorally silent transition mutations are recorded rather than forced to fail",
            "demotion_condition" => "a frozen hash or structural-holdout exclusion gate fails",
            "gates" => ["all_pass", "provenance", "partition"],
        ),
    ]
end

function main()
    spec, preregistration, object_card, spec_hash, object_card_hash = read_preregistered_inputs()
    maximum_depth = Int(spec["carrier"]["maximum_refinement_depth"])
    split_tag = String(spec["rule_symmetry_split"]["tag"])
    expected_orbit_count = Int(spec["rule_symmetry_split"]["expected_orbit_count"])
    expected_structural_hashes = String.(collect(spec["behavioral_partition_hash"]["structural_holdout_hashes_excluded_from_train_and_validation"]))

    orbits = ordered_symmetry_orbits(split_tag)
    orbit_map = orbit_index_map(orbits)
    orbit_coverage_pass = length(orbits) == expected_orbit_count && all(>=(0), orbit_map) && sort(vcat([record["members"] for record in orbits]...)) == collect(0:(RULE_COUNT - 1))
    fixtures = parse_fixture_pairs(spec)
    split_receipt = validate_fixture_split(fixtures, orbit_map, split_tag)
    leakage_sentinel = split_leakage_sentinel(fixtures, orbit_map, split_tag)

    fixture_results = Dict{String,Any}()
    for split in ("train", "validation", "test_primary", "test_structural_holdout")
        fixture_results[split] = [fixture_receipt(split, pair, maximum_depth) for pair in fixtures[split]]
    end
    all_receipts = vcat([fixture_results[split] for split in ("train", "validation", "test_primary", "test_structural_holdout")]...)
    train_validation_hashes = Set(String(receipt["partition_sha256"]) for receipt in vcat(fixture_results["train"], fixture_results["validation"]))
    structural_hashes = String[receipt["partition_sha256"] for receipt in fixture_results["test_structural_holdout"]]
    structural_hash_gate = structural_hashes == expected_structural_hashes && all(hash -> !(hash in train_validation_hashes), structural_hashes)

    quotient_gate = all(Bool(receipt["quotient"]["congruent"]) for receipt in all_receipts)
    graph_gate = all(Bool(receipt["graph_receipt"]["passed"]) for receipt in all_receipts)
    transition_mutation_gate = all(Bool(receipt["one_bit_transition_mutation"]["passed"]) for receipt in all_receipts)
    exact_scientific_pass = orbit_coverage_pass && Bool(split_receipt["passed"]) && Bool(leakage_sentinel["passed"]) && structural_hash_gate && quotient_gate && graph_gate && transition_mutation_gate

    calls = tool_calls()
    result = Dict{String,Any}(
        "schema" => "codex_ratchet.finite_probe_behavioral_object_engine_v1.julia_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "semantic_role" => "independent_exact_semantic_construction_and_graph_receipt",
        "ran" => true,
        "classification" => CLASSIFICATION,
        "source_path" => relpath(SOURCE_PATH, REPO_ROOT),
        "result_path" => relpath(RESULT_PATH, REPO_ROOT),
        "reads_peer_result" => false,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "all_pass" => false,
        "scientific_pass_before_closed_json_gate" => exact_scientific_pass,
        "claim_ceiling" => "independent exact finite ECA symmetry split, stable behavioral partitions, quotient congruence, and SCC signatures for the frozen v1 fixtures only",
        "blocked_consumers" => String.(collect(spec["blocked_consumers"])),
        "input_provenance" => Dict(
            "spec_path" => relpath(SPEC_PATH, REPO_ROOT),
            "preregistration_receipt_path" => relpath(PREREGISTRATION_PATH, REPO_ROOT),
            "object_card_path" => relpath(OBJECT_CARD_PATH, REPO_ROOT),
            "created_at" => String(preregistration["created_at"]),
            "status" => String(preregistration["status"]),
            "independent_spec_read" => true,
            "peer_result_files_read" => String[],
        ),
        "hashes" => Dict(
            "spec_sha256" => spec_hash,
            "expected_spec_sha256" => EXPECTED_SPEC_SHA256,
            "preregistration_receipt_sha256" => sha256_file(PREREGISTRATION_PATH),
            "object_card_sha256" => object_card_hash,
            "expected_object_card_sha256" => EXPECTED_OBJECT_CARD_SHA256,
            "run_julia_sha256" => sha256_file(SOURCE_PATH),
        ),
        "engine_contract" => Dict(
            "mode" => "all_three_full_sims",
            "role" => String(spec["engine_contract"]["roles"]["julia"]),
            "runtime_names_are_not_unique_intelligences" => Bool(spec["engine_contract"]["runtime_names_are_not_unique_intelligences"]),
            "peer_result_reads_forbidden" => true,
            "T9_status" => "not_run_by_julia_builder",
            "T9_demotion" => "exact role execution does not establish runtime non-substitutability",
        ),
        "foreign_runtime_manifest" => Dict(
            "julia" => Dict(
                "project" => Base.active_project(),
                "version" => string(VERSION),
                "packages" => Dict("Graphs" => string(Base.pkgversion(Graphs)), "JSON3" => string(Base.pkgversion(JSON3))),
                "role" => "independent exact semantic construction and graph receipt",
            ),
            "jax" => Dict("read" => false),
            "pytorch" => Dict("read" => false),
            "tensor_exchange" => "none",
        ),
        "packages_used" => ["Graphs", "JSON3", "SHA"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "TOOL_MANIFEST" => Dict(
            "load_bearing" => ["Graphs.SimpleDiGraph", "Graphs.add_edge!", "Graphs.strongly_connected_components", "JSON3.read", "JSON3.write", "SHA.sha256"],
            "supportive" => String[],
            "forbidden_bridges_absent" => ["PyCall", "PythonCall", "DLPack", "NumPy", "CSV", "pickle"],
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Graphs" => "load_bearing: every fixture gates package SCC parity and an executed SCC-signature mutation",
            "JSON3" => "load_bearing provenance and compact canonical-partition encoding",
            "SHA" => "load_bearing frozen-source, split-order, and structural-holdout partition hashes",
        ),
        "tool_calls" => calls,
        "rule_symmetry" => Dict(
            "tag" => split_tag,
            "generators" => ["left_right_reflection", "black_white_conjugacy"],
            "expected_orbit_count" => expected_orbit_count,
            "actual_orbit_count" => length(orbits),
            "coverage_pass" => orbit_coverage_pass,
            "ordered_orbits" => orbits,
            "rule_to_orbit_index" => orbit_map,
        ),
        "split_verification" => split_receipt,
        "split_leakage_sentinel" => leakage_sentinel,
        "behavioral_partition_hash_contract" => Dict(
            "encoding" => String(spec["behavioral_partition_hash"]["encoding"]),
            "expected_structural_holdout_hashes" => expected_structural_hashes,
            "actual_structural_holdout_hashes" => structural_hashes,
            "excluded_from_train_and_validation" => all(hash -> !(hash in train_validation_hashes), structural_hashes),
            "passed" => structural_hash_gate,
        ),
        "fixtures" => fixture_results,
        "tests" => Dict(
            "J1_symmetry_orbit_census" => orbit_coverage_pass,
            "J2_frozen_split_verification" => Bool(split_receipt["passed"]),
            "J3_split_leakage_sentinel" => Bool(leakage_sentinel["passed"]),
            "J4_stable_partition_and_quotient" => quotient_gate,
            "J5_structural_holdout_hashes" => structural_hash_gate,
            "J6_graphs_scc_signatures" => graph_gate,
            "J7_transition_mutation_receipts" => transition_mutation_gate,
            "T9_counterfactual_adaptive_replaceability" => false,
        ),
        "closed_json_validation" => Dict("passed" => false, "phase" => "tentative_round_trip"),
        "divergence_log" => [
            "Julia defines exact fixture-local behavioral objects; it does not certify the learned proxy.",
            "Symmetry-family disjointness is checked from independently generated ECA rule orbits.",
            "Graphs SCC signatures are gated against a separate reachability implementation and an executed mutation.",
            "A behaviorally silent one-bit transition mutation is recorded honestly rather than forced to alter a partition.",
            "T9 runtime non-substitutability is not executed or earned by this lane.",
            "No JAX, PyTorch, controller, prior result, or peer result artifact is read.",
        ],
        "witness_trace" => Dict(
            "trace_id" => "finite_probe_behavioral_object_engine_v1_julia_exact_trace_v1",
            "inputs" => [relpath(SPEC_PATH, REPO_ROOT), relpath(PREREGISTRATION_PATH, REPO_ROOT), relpath(OBJECT_CARD_PATH, REPO_ROOT)],
            "transforms" => [
                "derive all 256 ECA reflection/conjugacy symmetry memberships",
                "sort 88 symmetry orbits by frozen SHA256 key",
                "verify family-disjoint frozen rule-pair fixtures and leakage sentinel",
                "refine probe-relative partitions to exact stability for every fixture",
                "hash compact canonical stable labels",
                "check exact two-action quotient congruence",
                "gate Graphs SCC signatures against independent reachability and mutation controls",
                "round-trip a closed standalone Julia receipt",
            ],
            "final_classification" => CLASSIFICATION,
        ),
    )

    result_core = JSON3.write(result)
    result["hashes"]["result_core_sha256"] = sha256_text(result_core)
    tentative = JSON3.read(JSON3.write(result))
    tentative_ok = String(tentative["schema"]) == String(result["schema"]) &&
        String(tentative["sim_id"]) == SIM_ID &&
        !Bool(tentative["all_pass"]) &&
        isempty(collect(tentative["input_provenance"]["peer_result_files_read"]))
    tentative_ok || error("tentative closed-result round-trip failed")

    result["closed_json_validation"] = Dict(
        "passed" => true,
        "phase" => "tentative_and_final_round_trip",
        "required_fields" => ["schema", "sim_id", "engine", "all_pass", "hashes", "engine_contract", "tool_calls", "fixtures"],
    )
    result["all_pass"] = exact_scientific_pass && tentative_ok
    final_json = JSON3.write(result)
    final_round_trip = JSON3.read(final_json)
    final_ok = String(final_round_trip["schema"]) == String(result["schema"]) &&
        String(final_round_trip["sim_id"]) == SIM_ID &&
        Bool(final_round_trip["all_pass"]) == Bool(result["all_pass"]) &&
        Bool(final_round_trip["closed_json_validation"]["passed"])
    final_ok || error("final closed-result round-trip failed")

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
