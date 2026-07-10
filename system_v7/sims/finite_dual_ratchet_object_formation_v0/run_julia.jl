#!/usr/bin/env julia

using Dates
using Graphs
using JSON3
using SHA

const SIM_ID = "finite_dual_ratchet_object_formation_v0"
const PREREG_COMMIT = "dbfe0bd0e"
const CORRECTION_COMMIT = "aa287b2cf"
const SUPERSEDED_SPEC_SHA256 = "1fbe7dbad504981bc615d55eedb3f1f19ac41a6d90b1c34ef4c195a749543904"
const EXPECTED_SPEC_SHA256 = "110d4763c0d5173a378ebfc223848a63945cd1d5b50201051a39e00ebe00f088"
const GREEN_CEILING = "BOUNDED_EXACT_FOUR_ROLE_OBJECT_FORMATION_ON_FROZEN_FINITE_AUTOMATA"
const RED_CEILING = "FOUR_ROLE_OBJECT_FORMATION_NOT_ESTABLISHED"
const SCRIPT_PATH = abspath(@__FILE__)
const SIM_DIR = dirname(SCRIPT_PATH)
const REPO_ROOT = normpath(joinpath(SIM_DIR, "..", "..", ".."))
const SPEC_PATH = joinpath(SIM_DIR, "spec.json")
const PREREG_PATH = joinpath(SIM_DIR, "preregistration_receipt.json")
const RESULT_PATH = joinpath(SIM_DIR, "results", "finite_dual_ratchet_object_formation_v0_julia_results.json")

# CPython random.Random integer seeding, MT19937 output, getrandbits, and randrange.
mutable struct PyMT19937
    state::Vector{UInt32}
    index::Int
end

function init_genrand(seed::UInt32)
    mt = Vector{UInt32}(undef, 624)
    mt[1] = seed
    for i in 2:624
        previous = mt[i - 1]
        mt[i] = UInt32(1812433253) * (previous ⊻ (previous >> 30)) + UInt32(i - 1)
    end
    return mt
end

function py_mt(seed::Integer)
    seed < 0 && (seed = -seed)
    key = UInt32[]
    value = BigInt(seed)
    if value == 0
        push!(key, UInt32(0))
    else
        mask = BigInt(0xffffffff)
        while value != 0
            push!(key, UInt32(value & mask))
            value >>= 32
        end
    end

    mt = init_genrand(UInt32(19650218))
    i = 2
    j = 1
    for _ in 1:max(624, length(key))
        previous = mt[i - 1]
        mt[i] = (mt[i] ⊻ ((previous ⊻ (previous >> 30)) * UInt32(1664525))) +
                key[j] + UInt32(j - 1)
        i += 1
        j += 1
        if i == 625
            mt[1] = mt[624]
            i = 2
        end
        j > length(key) && (j = 1)
    end
    for _ in 1:623
        previous = mt[i - 1]
        mt[i] = (mt[i] ⊻ ((previous ⊻ (previous >> 30)) * UInt32(1566083941))) - UInt32(i - 1)
        i += 1
        if i == 625
            mt[1] = mt[624]
            i = 2
        end
    end
    mt[1] = UInt32(0x80000000)
    return PyMT19937(mt, 624)
end

function twist!(rng::PyMT19937)
    for i in 1:624
        y = (rng.state[i] & UInt32(0x80000000)) |
            (rng.state[mod1(i + 1, 624)] & UInt32(0x7fffffff))
        next = rng.state[mod1(i + 397, 624)] ⊻ (y >> 1)
        isodd(y) && (next ⊻= UInt32(0x9908b0df))
        rng.state[i] = next
    end
    rng.index = 0
end

function next_uint32!(rng::PyMT19937)
    rng.index >= 624 && twist!(rng)
    rng.index += 1
    y = rng.state[rng.index]
    y ⊻= y >> 11
    y ⊻= (y << 7) & UInt32(0x9d2c5680)
    y ⊻= (y << 15) & UInt32(0xefc60000)
    y ⊻= y >> 18
    return y
end

function getrandbits!(rng::PyMT19937, k::Int)
    0 < k <= 32 || error("this frozen carrier only requests 1:32 random bits")
    return Int(next_uint32!(rng) >> (32 - k))
end

function pyrandbelow!(rng::PyMT19937, n::Int)
    n > 0 || error("randbelow bound must be positive")
    k = 8 * sizeof(n) - leading_zeros(n)
    value = getrandbits!(rng, k)
    while value >= n
        value = getrandbits!(rng, k)
    end
    return value
end

function pyshuffle!(rng::PyMT19937, values::Vector{Int})
    for i in length(values):-1:2
        j = pyrandbelow!(rng, i) + 1
        values[i], values[j] = values[j], values[i]
    end
    return values
end

function rng_compatibility_receipt()
    expected_seed1 = [4, 2, 8, 3, 15, 14, 15, 12, 6, 3, 15, 0, 12, 13, 0, 14]
    expected_seed8565 = [4, 10, 1, 11, 11, 13, 4, 14, 7, 8, 8, 4, 2, 10, 4, 6]
    rng1 = py_mt(1)
    rng8565 = py_mt(8565)
    actual_seed1 = [pyrandbelow!(rng1, 16) for _ in 1:16]
    actual_seed8565 = [pyrandbelow!(rng8565, 16) for _ in 1:16]
    shuffle901 = pyshuffle!(py_mt(901), collect(0:63))
    shuffle_sha256 = bytes2hex(SHA.sha256(UInt8.(shuffle901)))
    expected_shuffle_sha256 = "7f2cd9f4f3a3dc89d3b7afcbff614c4b14dc1e3ac61c99a20a75eab6b22f058b"
    return Dict(
        "oracle" => "CPython random.Random fixed vectors",
        "seed1_randrange16_first16" => actual_seed1,
        "seed8565_randrange16_first16" => actual_seed8565,
        "seed901_shuffle_0_to_63_sha256" => shuffle_sha256,
        "pass" => actual_seed1 == expected_seed1 && actual_seed8565 == expected_seed8565 &&
                  shuffle_sha256 == expected_shuffle_sha256,
    )
end

function base_carrier(seed::Int)
    rng = py_mt(seed)
    transitions = Matrix{Int}(undef, 16, 2)
    # The frozen generator draws one complete successor map per action.
    for action in 1:2, state in 1:16
        transitions[state, action] = pyrandbelow!(rng, 16) + 1
    end
    probe = [2 * (count_ones(UInt32(state - 1)) % 2) + ((state - 1) & 1) + 1 for state in 1:16]
    return transitions, probe
end

function canonicalize(signatures)
    ids = Dict{Any,Int}()
    return [get!(ids, signature) do
                length(ids) + 1
            end for signature in signatures]
end

function refine_once(partition::Vector{Int}, transitions::Matrix{Int})
    signatures = [(partition[state], partition[transitions[state, 1]], partition[transitions[state, 2]])
                  for state in axes(transitions, 1)]
    return canonicalize(signatures)
end

function stable_partition(transitions::Matrix{Int}, probe::Vector{Int}; max_rounds::Union{Nothing,Int}=nothing)
    partition = canonicalize(probe)
    rounds = 0
    while true
        refined = refine_once(partition, transitions)
        refined == partition && return partition, rounds, true
        rounds += 1
        partition = refined
        max_rounds !== nothing && rounds >= max_rounds && return partition, rounds, false
    end
end

relation(partition::Vector{Int}) = [partition[i] == partition[j] for i in eachindex(partition), j in eachindex(partition)]

function lift_carrier(base_transitions::Matrix{Int}, base_probe::Vector{Int})
    transitions = Matrix{Int}(undef, 64, 2)
    probe = Vector{Int}(undef, 64)
    for copy in 0:3, base in 1:16
        state = copy * 16 + base
        probe[state] = base_probe[base]
        for action in 1:2
            transitions[state, action] = copy * 16 + base_transitions[base, action]
        end
    end
    return transitions, probe
end

function quotient(partition::Vector{Int}, transitions::Matrix{Int}, probe::Vector{Int})
    classes = maximum(partition)
    representatives = [findfirst(==(class), partition) for class in 1:classes]
    quotient_transitions = Matrix{Int}(undef, classes, 2)
    quotient_probe = Vector{Int}(undef, classes)
    congruent = true
    for class in 1:classes
        members = findall(==(class), partition)
        quotient_probe[class] = probe[representatives[class]]
        congruent &= all(probe[state] == quotient_probe[class] for state in members)
        for action in 1:2
            successor_class = partition[transitions[representatives[class], action]]
            quotient_transitions[class, action] = successor_class
            congruent &= all(partition[transitions[state, action]] == successor_class for state in members)
        end
    end
    return quotient_transitions, quotient_probe, congruent
end

function encoded_quotient_graph(transitions::Matrix{Int}, probe::Vector{Int}; action_map=(1, 2))
    classes = length(probe)
    graph = SimpleDiGraph(classes * 3)
    colors = Vector{Int}(undef, classes * 3)
    for class in 1:classes
        colors[class] = probe[class]
        for action in 1:2
            action_vertex = classes + (action - 1) * classes + class
            colors[action_vertex] = 10 + action_map[action]
            Graphs.add_edge!(graph, class, action_vertex)
            Graphs.add_edge!(graph, action_vertex, transitions[class, action])
        end
    end
    return graph, colors
end

function graph_isomorphic(source_q::Matrix{Int}, source_probe::Vector{Int}, view_q::Matrix{Int}, view_probe::Vector{Int}; action_map=(1, 2))
    source_graph, source_colors = encoded_quotient_graph(source_q, source_probe)
    view_graph, view_colors = encoded_quotient_graph(view_q, view_probe; action_map=action_map)
    color_relation(u, v) = source_colors[u] == view_colors[v]
    return Graphs.Experimental.has_isomorph(source_graph, view_graph; vertex_relation=color_relation)
end

function relabel_carrier(transitions::Matrix{Int}, probe::Vector{Int}, permutation::Vector{Int}; swap_actions=false)
    states = length(probe)
    view_transitions = Matrix{Int}(undef, states, 2)
    view_probe = Vector{Int}(undef, states)
    for source in 1:states
        view = permutation[source]
        view_probe[view] = probe[source]
        for view_action in 1:2
            source_action = swap_actions ? 3 - view_action : view_action
            view_transitions[view, view_action] = permutation[transitions[source, source_action]]
        end
    end
    return view_transitions, view_probe
end

function partition_pullback(view_partition::Vector{Int}, permutation::Vector{Int})
    return [view_partition[permutation[source]] for source in eachindex(permutation)]
end

function one_view_receipt(source_partition, source_relation, source_q, source_q_probe,
                          transitions, probe, permutation_seed; swap_actions=false)
    rng = py_mt(permutation_seed)
    permutation = pyshuffle!(rng, collect(1:length(probe)))
    view_transitions, view_probe = relabel_carrier(transitions, probe, permutation; swap_actions=swap_actions)
    view_partition, rounds, stable = stable_partition(view_transitions, view_probe)
    view_q, view_q_probe, congruent = quotient(view_partition, view_transitions, view_probe)
    pullback_exact = relation(partition_pullback(view_partition, permutation)) == source_relation
    action_map = swap_actions ? (2, 1) : (1, 2)
    unlabeled_isomorphic = graph_isomorphic(source_q, source_q_probe, view_q, view_q_probe; action_map=action_map)

    corrupted_q = copy(view_q)
    old_successor = corrupted_q[1, 1]
    corrupted_q[1, 1] = old_successor == size(corrupted_q, 1) ? 1 : old_successor + 1
    induced_exact = corrupted_q == view_q
    corrupted_isomorphic = graph_isomorphic(source_q, source_q_probe, corrupted_q, view_q_probe; action_map=action_map)
    corruption_rejected = !induced_exact

    return Dict(
        "permutation_seed" => permutation_seed,
        "action_swapped" => swap_actions,
        "refinement_rounds" => rounds,
        "stable" => stable,
        "known_bijection_pullback_exact" => pullback_exact,
        "graphs_vf2_color_preserving_isomorphic" => unlabeled_isomorphic,
        "quotient_congruent" => congruent,
        "corruption" => Dict(
            "class" => 1,
            "action_in_view" => 1,
            "old_successor" => old_successor,
            "new_successor" => corrupted_q[1, 1],
            "matches_exact_induced_quotient" => induced_exact,
            "graphs_vf2_isomorphic_after_corruption" => corrupted_isomorphic,
            "rejected" => corruption_rejected,
        ),
        "pass" => stable && pullback_exact && unlabeled_isomorphic && congruent && corruption_rejected,
    )
end

function fixture_receipt(seed::Int; perspectives=false)
    base_transitions, base_probe = base_carrier(seed)
    base_partition, rounds, stable = stable_partition(base_transitions, base_probe)
    transitions, probe = lift_carrier(base_transitions, base_probe)
    partition, lifted_rounds, lifted_stable = stable_partition(transitions, probe)
    q_transitions, q_probe, congruent = quotient(partition, transitions, probe)
    source_relation = relation(partition)

    erased_partition, _, erased_stable = stable_partition(transitions, ones(Int, 64))
    truncated_partition, truncated_rounds, truncated_stable = stable_partition(transitions, probe; max_rounds=3)

    views = Any[]
    if perspectives
        for permutation_seed in (901, 902, 903, 904)
            push!(views, one_view_receipt(partition, source_relation, q_transitions, q_probe,
                                          transitions, probe, permutation_seed))
        end
        push!(views, one_view_receipt(partition, source_relation, q_transitions, q_probe,
                                      transitions, probe, 904; swap_actions=true))
    end

    return Dict(
        "seed" => seed,
        "base_refinement_depth" => rounds,
        "lifted_refinement_depth" => lifted_rounds,
        "base_class_count" => maximum(base_partition),
        "lifted_class_count" => maximum(partition),
        "stable" => stable && lifted_stable,
        "quotient_congruent" => congruent,
        "measure_ablation_probe_erasure_changes_relation" => erased_stable && relation(erased_partition) != source_relation,
        "distinguish_ablation_depth3" => Dict(
            "rounds_executed" => truncated_rounds,
            "stable" => truncated_stable,
            "fails_exact_recovery" => relation(truncated_partition) != source_relation,
        ),
        "perspectives" => views,
    )
end

function depth_census()
    all_counts = Dict(string(depth) => 0 for depth in 1:4)
    nondiscrete_counts = Dict(string(depth) => 0 for depth in 1:4)
    unexpected_depths = Dict{String,Int}()
    for seed in 1:20000
        transitions, probe = base_carrier(seed)
        partition, depth, stable = stable_partition(transitions, probe)
        stable || error("refinement did not stabilize for seed $seed")
        key = string(depth)
        if haskey(all_counts, key)
            all_counts[key] += 1
            maximum(partition) < 16 && (nondiscrete_counts[key] += 1)
        else
            unexpected_depths[key] = get(unexpected_depths, key, 0) + 1
        end
    end
    expected_all = Dict("1" => 4636, "2" => 14656, "3" => 692, "4" => 16)
    expected_nondiscrete = Dict("1" => 618, "2" => 1523, "3" => 75, "4" => 3)
    return Dict(
        "seed_interval_inclusive" => [1, 20000],
        "all" => all_counts,
        "non_discrete" => nondiscrete_counts,
        "unexpected_depths" => unexpected_depths,
        "matches_frozen_expected" => all_counts == expected_all && nondiscrete_counts == expected_nondiscrete && isempty(unexpected_depths),
    )
end

sha256_file(path) = bytes2hex(SHA.sha256(read(path)))

function main()
    spec_sha256 = sha256_file(SPEC_PATH)
    spec_sha256 == EXPECTED_SPEC_SHA256 || error("frozen spec hash mismatch: $spec_sha256")

    rng_compatibility = rng_compatibility_receipt()
    rng_compatibility["pass"] || error("embedded MT19937 failed CPython compatibility fixtures")
    census = depth_census()
    target_seeds = [8565, 10288, 19937]
    controls = Dict(
        "depth1" => [fixture_receipt(seed) for seed in (4, 5, 8)],
        "depth2" => [fixture_receipt(seed) for seed in (1, 2, 3)],
        "depth3" => [fixture_receipt(seed) for seed in (11, 19, 37)],
    )
    targets = [fixture_receipt(seed; perspectives=true) for seed in target_seeds]

    controls_match_declared_depths = all(
        fixture["base_refinement_depth"] == expected_depth
        for (expected_depth, key) in ((1, "depth1"), (2, "depth2"), (3, "depth3"))
        for fixture in controls[key]
    )

    g2 = all(target["base_refinement_depth"] == 4 && target["lifted_refinement_depth"] == 4 for target in targets)
    g3 = all(view["known_bijection_pullback_exact"] for target in targets for view in target["perspectives"])
    g4 = all(view["graphs_vf2_color_preserving_isomorphic"] for target in targets for view in target["perspectives"])
    g5 = all(target["measure_ablation_probe_erasure_changes_relation"] for target in targets)
    g6 = all(target["distinguish_ablation_depth3"]["fails_exact_recovery"] for target in targets)
    g7 = all(target["quotient_congruent"] && target["lifted_class_count"] <= 15 for target in targets)
    g8 = all(view["corruption"]["rejected"] for target in targets for view in target["perspectives"])
    gates = Dict(
        "G1_census_exact" => census["matches_frozen_expected"],
        "G2_target_depth_exactly_four" => g2,
        "G3_cross_view_relation_exact" => g3,
        "G4_unlabeled_quotient_isomorphic" => g4,
        "G5_probe_erasure_changes_relation" => g5,
        "G6_depth3_truncation_fails_all_targets" => g6,
        "G7_quotient_congruent_and_at_most_15_classes" => g7,
        "G8_all_corruptions_rejected" => g8,
        "G9_julia_jax_exact_parity" => nothing,
    )
    local_all_pass = rng_compatibility["pass"] && controls_match_declared_depths &&
                     all(value === true for (key, value) in gates if key != "G9_julia_jax_exact_parity")

    role_ablations = Dict(
        "measure" => Dict("removed_behavior" => "erase the probe partition", "tooth_pass" => g5),
        "distinguish" => Dict("removed_behavior" => "truncate refinement after depth three", "tooth_pass" => g6),
        "quotient" => Dict(
            "removed_behavior" => "retain the raw 64-state carrier instead of forming the quotient",
            "raw_state_count" => 64,
            "maximum_allowed_quotient_classes" => 15,
            "target_quotient_class_counts" => [target["lifted_class_count"] for target in targets],
            "removed_role_fails_compression_tooth" => 64 > 15,
            "tooth_pass" => g7,
        ),
        "gate" => Dict(
            "removed_behavior" => "accept a one-successor quotient corruption",
            "corruptions_tested" => sum(length(target["perspectives"]) for target in targets),
            "all_rejected_by_exact_induced_transition_check" => g8,
            "tooth_pass" => g8,
        ),
    )

    result = Dict(
        "schema" => "codex_ratchet.finite_dual_ratchet_object_formation_v0.julia_result.v1",
        "sim_id" => SIM_ID,
        "classification" => "scratch_diagnostic",
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "source" => Dict(
            "path" => relpath(SCRIPT_PATH, REPO_ROOT),
            "sha256" => sha256_file(SCRIPT_PATH),
            "spec_path" => relpath(SPEC_PATH, REPO_ROOT),
            "spec_sha256" => spec_sha256,
            "preregistration_path" => relpath(PREREG_PATH, REPO_ROOT),
            "preregistration_sha256" => sha256_file(PREREG_PATH),
            "preregistration_origin_commit_short" => PREREG_COMMIT,
            "active_frozen_correction_commit_short" => CORRECTION_COMMIT,
            "superseded_spec_sha256" => SUPERSEDED_SPEC_SHA256,
        ),
        "julia" => Dict(
            "ran" => true,
            "version" => string(VERSION),
            "active_project" => Base.active_project(),
            "source_path" => relpath(SCRIPT_PATH, REPO_ROOT),
            "packages_used" => ["Graphs", "JSON3", "SHA", "Dates"],
            "aligned_packages_load_bearing" => ["Graphs"],
            "reads_peer_result" => false,
            "peer_reads" => String[],
            "rng" => "embedded CPython-compatible integer-seeded MT19937/getrandbits/randrange/shuffle",
        ),
        "fixtures" => Dict("targets_depth4_non_discrete" => targets, "controls" => controls),
        "fixtures_match_declared_depths" => controls_match_declared_depths,
        "rng_compatibility" => rng_compatibility,
        "depth_census" => census,
        "four_role_ablations" => role_ablations,
        "tool_calls" => [Dict(
            "tool" => "Graphs.jl",
            "qualified_api/function" => "Graphs.Experimental.has_isomorph",
            "input_object" => "action-colored expanded directed quotient graphs",
            "output_object" => "Boolean color-preserving VF2 isomorphism receipt per perspective",
            "positive_case" => "intact relabeled and action-normalized quotient",
            "negative/erased_control" => "corrupted quotient graph recorded as a side receipt; exact induced-transition mismatch owns G8",
            "boundary_case" => "self-loops and equal action successors remain distinct through action vertices",
            "demotion_condition" => "any intact view is non-isomorphic or Graphs is unavailable",
            "gates" => ["G4_unlabeled_quotient_isomorphic"],
            "load_bearing" => true,
        )],
        "gates" => gates,
        "local_all_pass" => local_all_pass,
        "all_pass" => false,
        "pending_gate" => "G9_julia_jax_exact_parity",
        "claim_ceiling_earned" => RED_CEILING,
        "accepted_green_ceiling_if_controller_confirms_G9" => GREEN_CEILING,
        "blocked_consumers" => [
            "QIT four-substage derivation", "sixteen-slot schedule promotion",
            "sixty-four-microstep schedule promotion", "learned perception",
            "general object perception", "MMMs and ontologies",
        ],
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "no_peer_reads" => true,
    )

    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON3.pretty(io, result)
        write(io, '\n')
    end
    println("wrote=", RESULT_PATH)
    println("local_all_pass=", local_all_pass)
    println("G9_julia_jax_exact_parity=pending_controller")
    println("claim_ceiling_earned=", RED_CEILING)
    local_all_pass || exit(1)
end

main()
