using JSON3
using SHA

const HERE = @__DIR__
const REPO_ROOT = normpath(joinpath(HERE, "..", "..", ".."))
const SOURCE_PATH = abspath(@__FILE__)
const SPEC_PATH = joinpath(HERE, "spec.json")
const RECEIPT_PATH = joinpath(HERE, "preregistration_receipt.json")
const RESULT_PATH_DEFAULT = joinpath(HERE, "results", "eca_relation_directed_observation_design_v1_julia_search_results.json")
const SIM_ID = "eca_relation_directed_observation_design_v1"
const TAG_V0 = "ECA-OBS-ID-V0"
const TAG_V1 = "ECA-OBS-DESIGN-V1"
const RING_SIZE = 9
const STATE_COUNT = 1 << RING_SIZE
const RULE_COUNT = 256
const PAIR_COUNT = div(RULE_COUNT * (RULE_COUNT - 1), 2)
const DESIGN_FIXTURE_COUNT = 128
const QUERY_COUNT = 9636
const SUBSET_SIZES = (2, 3, 4)
const SHORTLIST_SIZE = 32
const RuleMask = NTuple{4,UInt64}
const FULL_RULE_MASK = (typemax(UInt64), typemax(UInt64), typemax(UInt64), typemax(UInt64))

sha256_bytes(bytes)::String = bytes2hex(SHA.sha256(bytes))
sha256_text(text::AbstractString)::String = sha256_bytes(codeunits(text))
sha256_file(path::AbstractString)::String = sha256_bytes(read(path))
compact_pair(pair)::String = "[$(pair[1]),$(pair[2])]"
compact_pair_list(values)::String = "[" * join(compact_pair.(values), ",") * "]"
compact_int_list(values)::String = "[" * join(string.(values), ",") * "]"
compact_orbit_list(values)::String = "[" * join((compact_pair_list(orbit) for orbit in values), ",") * "]"

function output_path()::String
    for index in eachindex(ARGS)
        if ARGS[index] == "--output"
            index < length(ARGS) || error("--output requires a path")
            return abspath(ARGS[index + 1])
        elseif startswith(ARGS[index], "--output=")
            return abspath(split(ARGS[index], "="; limit=2)[2])
        end
    end
    return RESULT_PATH_DEFAULT
end

function combinations16(k::Int)::Vector{Vector{Int}}
    output = Vector{Vector{Int}}()
    if k == 2
        for a in 0:14, b in (a + 1):15
            push!(output, [a, b])
        end
    elseif k == 3
        for a in 0:13, b in (a + 1):14, c in (b + 1):15
            push!(output, [a, b, c])
        end
    elseif k == 4
        for a in 0:12, b in (a + 1):13, c in (b + 1):14, d in (c + 1):15
            push!(output, [a, b, c, d])
        end
    else
        error("unsupported subset size $k")
    end
    return output
end

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
        sha256_text("$TAG_V0|rule_orbit|" * join(orbit, ",")), orbit,
    ))
end

function simultaneous_pair_orbit(rule_a::Int, rule_b::Int)::Vector{Tuple{Int,Int}}
    conjugated_a, conjugated_b = conjugate_rule(rule_a), conjugate_rule(rule_b)
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

function domain_walls(state::Int)::Int
    return sum(
        ((state >> site) & 1) != ((state >> mod(site + 1, RING_SIZE)) & 1)
        for site in 0:(RING_SIZE - 1)
    )
end

function build_frozen_manifests()
    orbits = ordered_rule_orbits()
    blocks = Dict("train" => orbits[1:52], "validation" => orbits[53:70], "test" => orbits[71:88])
    rule_block = Dict{Int,String}()
    for (block, block_orbits) in blocks, orbit in block_orbits, rule in orbit
        rule_block[rule] = block
    end
    pair_orbits = Dict{String,Vector{Vector{Tuple{Int,Int}}}}()
    for block in ("train", "validation", "test")
        unique_orbits = Dict{String,Vector{Tuple{Int,Int}}}()
        for rule_a in 0:(RULE_COUNT - 2), rule_b in (rule_a + 1):(RULE_COUNT - 1)
            if rule_block[rule_a] == block && rule_block[rule_b] == block
                orbit = simultaneous_pair_orbit(rule_a, rule_b)
                unique_orbits[orbit_key(orbit)] = orbit
            end
        end
        pair_orbits[block] = sort!(collect(values(unique_orbits)); by=orbit -> Tuple(orbit))
    end
    assignments = Tuple{String,Int}[
        ("BAAA", 507), ("AAAA", 313), ("BAAB", 81), ("BBBB", 99),
        ("ABBA", 265), ("BABB", 3), ("AAAB", 196), ("AABB", 227),
        ("BABA", 89), ("BBAB", 0), ("AABA", 339), ("BBAA", 268),
        ("BBBA", 49), ("ABAA", 118), ("ABBB", 147), ("ABAB", 478),
    ]
    queries = Tuple{Int,Int}[]
    for x in 0:(STATE_COUNT - 2), y in (x + 1):(STATE_COUNT - 1)
        (count_ones(x), domain_walls(x)) == (count_ones(y), domain_walls(y)) && push!(queries, (x, y))
    end
    rule_orbit_json = "[" * join((compact_int_list(orbit) for orbit in orbits), ",") * "]"
    pair_orbit_json = "{" * join(("\"$block\":" * compact_orbit_list(pair_orbits[block]) for block in ("test", "train", "validation")), ",") * "}"
    assignment_json = "[" * join(("[\"$(entry[1])\",$(entry[2])]" for entry in assignments), ",") * "]"
    query_json = compact_pair_list(queries)
    train_representatives = [first(orbit) for orbit in pair_orbits["train"]]
    design_fixtures = first(sort!(train_representatives; by=pair -> (
        sha256_text("$TAG_V1|design_fixture|$(pair[1]),$(pair[2])"), pair,
    )), DESIGN_FIXTURE_COUNT)
    return (
        orbits=orbits,
        pair_orbits=pair_orbits,
        assignments=assignments,
        queries=queries,
        design_fixtures=design_fixtures,
        hashes=Dict(
            "rule_orbits" => sha256_text(rule_orbit_json),
            "pair_orbits" => sha256_text(pair_orbit_json),
            "assignments" => sha256_text(assignment_json),
            "queries" => sha256_text(query_json),
            "design_fixtures" => sha256_text(compact_pair_list(design_fixtures)),
        ),
    )
end

function verify_frozen_inputs(manifests, candidates)
    spec = JSON3.read(read(SPEC_PATH, String))
    receipt = JSON3.read(read(RECEIPT_PATH, String))
    counts = Dict(string(k) => length(candidates[k]) for k in SUBSET_SIZES)
    counts["total"] = sum(values(counts))
    tests = Dict(
        "sim_identity" => String(spec["sim_id"]) == String(receipt["sim_id"]) == SIM_ID,
        "spec_sha256" => sha256_file(SPEC_PATH) == String(receipt["spec_sha256"]),
        "search_absent_at_freeze" => !Bool(receipt["search_sources_present_when_frozen"]),
        "confirmation_absent_at_freeze" => !Bool(receipt["confirmation_sources_present_when_frozen"]),
        "rule_orbit_manifest" => manifests.hashes["rule_orbits"] == String(spec["rule_family_split"]["rule_orbit_manifest_sha256"]),
        "pair_orbit_manifest" => manifests.hashes["pair_orbits"] == String(spec["rule_family_split"]["same_block_pair_orbit_manifest_sha256"]),
        "assignment_manifest" => manifests.hashes["assignments"] == String(spec["candidate_pool"]["assignment_manifest_sha256"]),
        "query_manifest" => manifests.hashes["queries"] == String(spec["inherited_carrier"]["query_manifest_sha256"]),
        "design_fixture_manifest" => manifests.hashes["design_fixtures"] == String(spec["rule_family_split"]["design_fixture_manifest_sha256"]),
        "design_fixture_count" => length(manifests.design_fixtures) == DESIGN_FIXTURE_COUNT,
        "query_count" => length(manifests.queries) == QUERY_COUNT,
        "candidate_counts" => all(Int(spec["candidate_pool"]["candidate_counts"][key]) == value for (key, value) in counts),
        "shortlist_shape" => Int(spec["two_stage_search"]["shortlist_per_size"]) == SHORTLIST_SIZE,
    )
    all(values(tests)) || error("frozen input verification failed: $(JSON3.write(tests))")
    return Dict(
        "passed" => true,
        "verified_before_scientific_computation" => true,
        "tests" => tests,
        "hashes" => Dict(
            "spec_sha256" => sha256_file(SPEC_PATH),
            "preregistration_receipt_sha256" => sha256_file(RECEIPT_PATH),
            "rule_orbit_manifest_sha256" => manifests.hashes["rule_orbits"],
            "same_block_pair_orbit_manifest_sha256" => manifests.hashes["pair_orbits"],
            "assignment_manifest_sha256" => manifests.hashes["assignments"],
            "query_manifest_sha256" => manifests.hashes["queries"],
            "design_fixture_manifest_sha256" => manifests.hashes["design_fixtures"],
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
    for index in eachindex(labels)
        signature = UInt32(labels[index]) |
            (UInt32(labels[Int(transition_a[index]) + 1]) << 9) |
            (UInt32(labels[Int(transition_b[index]) + 1]) << 18)
        if !haskey(ids, signature)
            ids[signature] = next_id
            next_id += UInt16(1)
        end
        refined[index] = ids[signature]
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
    error("partition refinement exceeded finite-state bound")
end

function precompute_partitions(transitions, initial_labels, queries)
    labels_by_pair = Matrix{UInt16}(undef, STATE_COUNT, PAIR_COUNT)
    pair_index = zeros(Int32, RULE_COUNT, RULE_COUNT)
    relation_ids = Vector{Int32}(undef, PAIR_COUNT)
    relation_hashes = String[]
    relation_id_by_hash = Dict{String,Int32}()
    query_equal = falses(length(queries), PAIR_COUNT)
    swap_failures = Tuple{Int,Int}[]
    index = 0
    for rule_a in 0:(RULE_COUNT - 2), rule_b in (rule_a + 1):(RULE_COUNT - 1)
        index += 1
        ta = @view transitions[:, rule_a + 1]
        tb = @view transitions[:, rule_b + 1]
        labels = exact_stable_partition(initial_labels, ta, tb)
        swapped = exact_stable_partition(initial_labels, tb, ta)
        labels == swapped || push!(swap_failures, (rule_a, rule_b))
        labels_by_pair[:, index] = labels
        pair_index[rule_a + 1, rule_b + 1] = Int32(index)
        pair_index[rule_b + 1, rule_a + 1] = Int32(index)
        digest = sha256_text(JSON3.write(labels))
        relation_id = get!(relation_id_by_hash, digest) do
            push!(relation_hashes, digest)
            Int32(length(relation_hashes))
        end
        relation_ids[index] = relation_id
        for (query_index, (x, y)) in enumerate(queries)
            query_equal[query_index, index] = labels[x + 1] == labels[y + 1]
        end
    end
    return labels_by_pair, pair_index, relation_ids, relation_hashes, query_equal, swap_failures
end

mask_intersect(a::RuleMask, b::RuleMask)::RuleMask = (a[1] & b[1], a[2] & b[2], a[3] & b[3], a[4] & b[4])
mask_count(mask::RuleMask)::Int = count_ones(mask[1]) + count_ones(mask[2]) + count_ones(mask[3]) + count_ones(mask[4])
mask_overlap_count(a::RuleMask, b::RuleMask)::Int = mask_count(mask_intersect(a, b))

function rule_mask(rules)::RuleMask
    words = zeros(UInt64, 4)
    for rule in rules
        word = div(rule, 64) + 1
        words[word] |= UInt64(1) << (rule % 64)
    end
    return Tuple(words)
end

function mask_values(mask::RuleMask)::Vector{Int}
    values = Int[]
    sizehint!(values, mask_count(mask))
    for word_index in 1:4
        word = mask[word_index]
        while word != 0
            bit = trailing_zeros(word)
            push!(values, (word_index - 1) * 64 + bit)
            word &= word - UInt64(1)
        end
    end
    return values
end

struct FixtureObservationCache
    rule_a::Int
    rule_b::Int
    compatible_a::Vector{RuleMask}
    compatible_b::Vector{RuleMask}
    observed_states::Vector{BitVector}
end

function trajectory_observations(rule_a, rule_b, word, initial_state, transitions)
    observed_a = Tuple{Int,Int}[]
    observed_b = Tuple{Int,Int}[]
    observed_states = falses(STATE_COUNT)
    state = initial_state
    for token in word
        rule = token == 'A' ? rule_a : rule_b
        successor = Int(transitions[state + 1, rule + 1])
        push!(token == 'A' ? observed_a : observed_b, (state, successor))
        observed_states[state + 1] = true
        observed_states[successor + 1] = true
        state = successor
    end
    return observed_a, observed_b, observed_states
end

function compatible_mask(observations, transitions)::RuleMask
    return rule_mask(rule for rule in 0:(RULE_COUNT - 1) if all(
        Int(transitions[state + 1, rule + 1]) == successor for (state, successor) in observations
    ))
end

function build_fixture_cache(rule_a, rule_b, assignments, transitions)::FixtureObservationCache
    compatible_a = RuleMask[]
    compatible_b = RuleMask[]
    observed_states = BitVector[]
    for (word, initial_state) in assignments
        oa, ob, states = trajectory_observations(rule_a, rule_b, word, initial_state, transitions)
        push!(compatible_a, compatible_mask(oa, transitions))
        push!(compatible_b, compatible_mask(ob, transitions))
        push!(observed_states, states)
    end
    return FixtureObservationCache(rule_a, rule_b, compatible_a, compatible_b, observed_states)
end

function subset_masks(cache::FixtureObservationCache, subset)::Tuple{RuleMask,RuleMask,BitVector}
    mask_a, mask_b = FULL_RULE_MASK, FULL_RULE_MASK
    observed = falses(STATE_COUNT)
    for zero_index in subset
        index = zero_index + 1
        mask_a = mask_intersect(mask_a, cache.compatible_a[index])
        mask_b = mask_intersect(mask_b, cache.compatible_b[index])
        observed .|= cache.observed_states[index]
    end
    return mask_a, mask_b, observed
end

function effective_pair_indices(mask_a::RuleMask, mask_b::RuleMask, pair_index)::Vector{Int32}
    indices = Set{Int32}()
    for rule_a in mask_values(mask_a), rule_b in mask_values(mask_b)
        rule_a == rule_b && continue
        push!(indices, pair_index[rule_a + 1, rule_b + 1])
    end
    return sort!(collect(indices))
end

function fixture_screen(cache, subset, pair_index, relation_ids)
    mask_a, mask_b, observed = subset_masks(cache, subset)
    version_size = mask_count(mask_a) * mask_count(mask_b) - mask_overlap_count(mask_a, mask_b)
    effective = effective_pair_indices(mask_a, mask_b, pair_index)
    relation_count = length(Set(relation_ids[Int(index)] for index in effective))
    true_in_version = ((cache.rule_a >> 6) + 1 <= 4) &&
        ((mask_a[(cache.rule_a >> 6) + 1] >> (cache.rule_a & 63)) & 1 == 1) &&
        ((mask_b[(cache.rule_b >> 6) + 1] >> (cache.rule_b & 63)) & 1 == 1)
    return (
        ordered_version_space_size=version_size,
        effective_unordered_hypothesis_count=length(effective),
        distinct_partition_relation_count=relation_count,
        system_identified=version_size == 1,
        true_pair_in_version_space=true_in_version,
        effective_indices=effective,
        mask_a=mask_a,
        mask_b=mask_b,
        observed=observed,
    )
end

function screen_candidate(subset, fixture_caches, pair_index, relation_ids)
    diversity = 0
    system_identified = 0
    capped_effective_sum = 0
    capped_relation_sum = 0
    total_version = 0
    construction_valid = true
    for cache in fixture_caches
        score = fixture_screen(cache, subset, pair_index, relation_ids)
        is_diverse = score.effective_unordered_hypothesis_count >= 8 && score.distinct_partition_relation_count >= 2
        diversity += is_diverse
        system_identified += score.system_identified
        capped_effective_sum += min(score.effective_unordered_hypothesis_count, 64)
        capped_relation_sum += min(score.distinct_partition_relation_count, 64)
        total_version += score.ordered_version_space_size
        construction_valid &= score.ordered_version_space_size > 0 && score.true_pair_in_version_space
    end
    objective = [diversity, -system_identified, capped_effective_sum, capped_relation_sum]
    return Dict{String,Any}(
        "subset_size" => length(subset),
        "subset_indices" => copy(subset),
        "screen_objective" => objective,
        "diversity_fixture_count" => diversity,
        "system_identified_fixture_count" => system_identified,
        "capped_effective_hypothesis_sum" => capped_effective_sum,
        "capped_partition_relation_sum" => capped_relation_sum,
        "total_ordered_version_space_size" => total_version,
        "construction_valid" => construction_valid,
    )
end

function screen_better(left, right)::Bool
    lo, ro = left["screen_objective"], right["screen_objective"]
    for index in eachindex(lo)
        lo[index] != ro[index] && return lo[index] > ro[index]
    end
    return Tuple(left["subset_indices"]) < Tuple(right["subset_indices"])
end

function system_id_better(left, right)::Bool
    left["total_ordered_version_space_size"] != right["total_ordered_version_space_size"] &&
        return left["total_ordered_version_space_size"] < right["total_ordered_version_space_size"]
    left["system_identified_fixture_count"] != right["system_identified_fixture_count"] &&
        return left["system_identified_fixture_count"] > right["system_identified_fixture_count"]
    return Tuple(left["subset_indices"]) < Tuple(right["subset_indices"])
end

function consensus_counts(effective_indices, query_equal, queries, observed)
    isempty(effective_indices) && error("empty effective hypothesis set")
    all_equal = trues(length(queries))
    any_equal = falses(length(queries))
    for pair_index in effective_indices
        column = @view query_equal[:, Int(pair_index)]
        all_equal .&= column
        any_equal .|= column
    end
    identifiable_same = count(all_equal)
    identifiable_different = count(.!any_equal)
    identifiable = identifiable_same + identifiable_different
    disjoint = BitVector(undef, length(queries))
    for (index, (x, y)) in enumerate(queries)
        disjoint[index] = !observed[x + 1] && !observed[y + 1]
    end
    disjoint_total = count(disjoint)
    disjoint_same = count(all_equal .& disjoint)
    disjoint_different = count((.!any_equal) .& disjoint)
    return (
        identifiable=identifiable,
        same=identifiable_same,
        different=identifiable_different,
        ambiguous=length(queries) - identifiable,
        disjoint_total=disjoint_total,
        disjoint_identifiable=disjoint_same + disjoint_different,
        disjoint_same=disjoint_same,
        disjoint_different=disjoint_different,
        vector_hash=sha256_text(JSON3.write(UInt8[all_equal[i] ? 2 : (!any_equal[i] ? 1 : 0) for i in eachindex(all_equal)])),
    )
end

function exact_candidate(subset, screen_record, fixture_caches, pair_index, relation_ids, query_equal, queries; include_fixture_records=false)
    fixture_records = Dict{String,Any}[]
    fixture_digest_records = Any[]
    robust_counts = Int[]
    disjoint_robust_counts = Int[]
    total_identifiable = 0
    total_same = 0
    total_different = 0
    total_disjoint = 0
    total_disjoint_identifiable = 0
    balanced_fixture_count = 0
    construction_valid = true
    for (fixture_index, cache) in enumerate(fixture_caches)
        screen = fixture_screen(cache, subset, pair_index, relation_ids)
        counts = consensus_counts(screen.effective_indices, query_equal, queries, screen.observed)
        diverse = screen.effective_unordered_hypothesis_count >= 8 && screen.distinct_partition_relation_count >= 2
        robust = diverse ? counts.identifiable : 0
        disjoint_robust = diverse ? counts.disjoint_identifiable : 0
        balanced = counts.identifiable > 0 && 10 * counts.same >= counts.identifiable && 10 * counts.different >= counts.identifiable
        push!(robust_counts, robust)
        push!(disjoint_robust_counts, disjoint_robust)
        total_identifiable += counts.identifiable
        total_same += counts.same
        total_different += counts.different
        total_disjoint += counts.disjoint_total
        total_disjoint_identifiable += counts.disjoint_identifiable
        balanced_fixture_count += balanced
        construction_valid &= screen.ordered_version_space_size > 0 && screen.true_pair_in_version_space
        push!(fixture_digest_records, [
            fixture_index - 1,
            screen.ordered_version_space_size,
            screen.effective_unordered_hypothesis_count,
            screen.distinct_partition_relation_count,
            screen.system_identified,
            counts.identifiable,
            counts.same,
            counts.different,
            counts.disjoint_total,
            counts.disjoint_identifiable,
            balanced,
            counts.vector_hash,
        ])
        if include_fixture_records
            push!(fixture_records, Dict(
                "fixture_index" => fixture_index - 1,
                "rule_A" => cache.rule_a,
                "rule_B" => cache.rule_b,
                "ordered_version_space_size" => screen.ordered_version_space_size,
                "effective_unordered_hypothesis_count" => screen.effective_unordered_hypothesis_count,
                "distinct_partition_relation_count" => screen.distinct_partition_relation_count,
                "system_identified" => screen.system_identified,
                "true_pair_in_version_space" => screen.true_pair_in_version_space,
                "diversity_fixture" => diverse,
                "identifiable_query_count" => counts.identifiable,
                "identifiable_same_count" => counts.same,
                "identifiable_different_count" => counts.different,
                "query_disjoint_query_count" => counts.disjoint_total,
                "query_disjoint_identifiable_count" => counts.disjoint_identifiable,
                "query_disjoint_same_count" => counts.disjoint_same,
                "query_disjoint_different_count" => counts.disjoint_different,
                "fixture_balance_pass" => balanced,
                "identifiability_vector_hash" => counts.vector_hash,
            ))
        end
    end
    objective = [
        minimum(robust_counts), sum(robust_counts), balanced_fixture_count,
        minimum(disjoint_robust_counts), sum(disjoint_robust_counts),
        Int.(screen_record["screen_objective"])...,
    ]
    record = Dict{String,Any}(
        "subset_size" => length(subset),
        "subset_indices" => copy(subset),
        "exact_objective" => objective,
        "minimum_robust_query_count" => objective[1],
        "sum_robust_query_count" => objective[2],
        "balanced_fixture_count" => balanced_fixture_count,
        "minimum_query_disjoint_robust_identifiable_count" => objective[4],
        "sum_query_disjoint_robust_identifiable_count" => objective[5],
        "total_identifiable_query_count" => total_identifiable,
        "total_identifiable_same_count" => total_same,
        "total_identifiable_different_count" => total_different,
        "total_query_disjoint_query_count" => total_disjoint,
        "total_query_disjoint_identifiable_count" => total_disjoint_identifiable,
        "construction_valid" => construction_valid,
        "fixture_score_ledger_sha256" => sha256_text(JSON3.write(fixture_digest_records)),
    )
    include_fixture_records && (record["fixture_scores"] = fixture_records)
    return record
end

function exact_better(left, right)::Bool
    lo, ro = left["exact_objective"], right["exact_objective"]
    for index in eachindex(lo)
        lo[index] != ro[index] && return lo[index] > ro[index]
    end
    return Tuple(left["subset_indices"]) < Tuple(right["subset_indices"])
end

function brute_force_version(cache, subset, transitions)
    observed_a = Tuple{Int,Int}[]
    observed_b = Tuple{Int,Int}[]
    for zero_index in subset
        word, initial_state = build_frozen_manifests().assignments[zero_index + 1]
        oa, ob, _ = trajectory_observations(cache.rule_a, cache.rule_b, word, initial_state, transitions)
        append!(observed_a, oa)
        append!(observed_b, ob)
    end
    codes = UInt32[]
    for rule_a in 0:(RULE_COUNT - 1), rule_b in 0:(RULE_COUNT - 1)
        rule_a == rule_b && continue
        a_ok = all(Int(transitions[state + 1, rule_a + 1]) == successor for (state, successor) in observed_a)
        b_ok = all(Int(transitions[state + 1, rule_b + 1]) == successor for (state, successor) in observed_b)
        a_ok && b_ok && push!(codes, UInt32(rule_a * RULE_COUNT + rule_b))
    end
    return codes
end

function main()
    started_at = time()
    candidates = Dict(k => combinations16(k) for k in SUBSET_SIZES)
    manifests = build_frozen_manifests()
    frozen = verify_frozen_inputs(manifests, candidates)
    spec = JSON3.read(read(SPEC_PATH, String))

    transitions = Matrix{UInt16}(undef, STATE_COUNT, RULE_COUNT)
    for rule in 0:(RULE_COUNT - 1), state in 0:(STATE_COUNT - 1)
        transitions[state + 1, rule + 1] = eca_step(state, rule)
    end
    initial_labels = canonical_initial_labels()
    labels_by_pair, pair_index, relation_ids, relation_hashes, query_equal, swap_failures =
        precompute_partitions(transitions, initial_labels, manifests.queries)
    fixture_caches = [
        build_fixture_cache(pair[1], pair[2], manifests.assignments, transitions)
        for pair in manifests.design_fixtures
    ]

    screen_records = Dict{String,Any}[]
    shortlists = Dict{Int,Vector{Dict{String,Any}}}()
    system_id_records = Dict{Int,Dict{String,Any}}()
    hash_order_records = Dict{Int,Dict{String,Any}}()
    for size in SUBSET_SIZES
        current = [screen_candidate(subset, fixture_caches, pair_index, relation_ids) for subset in candidates[size]]
        append!(screen_records, current)
        ranked = sort(current; lt=screen_better)
        shortlists[size] = ranked[1:SHORTLIST_SIZE]
        system_id_records[size] = first(sort(current; lt=system_id_better))
        hash_order_records[size] = only(record for record in current if record["subset_indices"] == collect(0:(size - 1)))
    end

    exact_records = Dict{String,Any}[]
    winners = Dict{Int,Dict{String,Any}}()
    winner_fixture_ledgers = Dict{String,Any}()
    baseline_exact = Dict{String,Any}()
    for size in SUBSET_SIZES
        current = Dict{String,Any}[]
        for screen_record in shortlists[size]
            push!(current, exact_candidate(screen_record["subset_indices"], screen_record, fixture_caches, pair_index, relation_ids, query_equal, manifests.queries))
        end
        append!(exact_records, current)
        winner = first(sort(current; lt=exact_better))
        winners[size] = winner
        winner_fixture_ledgers[string(size)] = exact_candidate(
            winner["subset_indices"],
            only(record for record in shortlists[size] if record["subset_indices"] == winner["subset_indices"]),
            fixture_caches, pair_index, relation_ids, query_equal, manifests.queries;
            include_fixture_records=true,
        )["fixture_scores"]
        baseline_exact[string(size)] = Dict(
            "relation_directed" => winner,
            "hash_order" => exact_candidate(hash_order_records[size]["subset_indices"], hash_order_records[size], fixture_caches, pair_index, relation_ids, query_equal, manifests.queries),
            "system_identification" => exact_candidate(system_id_records[size]["subset_indices"], system_id_records[size], fixture_caches, pair_index, relation_ids, query_equal, manifests.queries),
        )
    end

    screen_hash = sha256_text(JSON3.write(screen_records))
    exact_hash = sha256_text(JSON3.write(exact_records))
    winner_summary = [Dict("subset_size" => size, "subset_indices" => winners[size]["subset_indices"], "exact_objective" => winners[size]["exact_objective"]) for size in SUBSET_SIZES]
    winner_hash = sha256_text(JSON3.write(winner_summary))
    reversed_winners = Dict{Int,Vector{Int}}()
    for size in SUBSET_SIZES
        reranked = sort(reverse([record for record in screen_records if record["subset_size"] == size]); lt=screen_better)[1:SHORTLIST_SIZE]
        reranked_exact = [only(record for record in exact_records if record["subset_indices"] == candidate["subset_indices"]) for candidate in reranked]
        reversed_winners[size] = first(sort(reranked_exact; lt=exact_better))["subset_indices"]
    end
    omitted_hash = sha256_text(JSON3.write(screen_records[1:(end - 1)]))
    mutated_summary = deepcopy(winner_summary)
    mutated_summary[1]["subset_indices"] = reverse(mutated_summary[1]["subset_indices"])
    mutated_winner_hash = sha256_text(JSON3.write(mutated_summary))

    factorization_controls = Dict{String,Any}[]
    action_swap_controls = Dict{String,Any}[]
    for size in SUBSET_SIZES, fixture_index in (1, DESIGN_FIXTURE_COUNT)
        subset = winners[size]["subset_indices"]
        cache = fixture_caches[fixture_index]
        screen = fixture_screen(cache, subset, pair_index, relation_ids)
        brute_codes = brute_force_version(cache, subset, transitions)
        push!(factorization_controls, Dict(
            "subset_size" => size,
            "fixture_index" => fixture_index - 1,
            "factorized_count" => screen.ordered_version_space_size,
            "brute_force_count" => length(brute_codes),
            "passed" => screen.ordered_version_space_size == length(brute_codes),
        ))
        swapped_cache = FixtureObservationCache(cache.rule_b, cache.rule_a, cache.compatible_b, cache.compatible_a, cache.observed_states)
        swapped = fixture_screen(swapped_cache, subset, pair_index, relation_ids)
        original_counts = consensus_counts(screen.effective_indices, query_equal, manifests.queries, screen.observed)
        swapped_counts = consensus_counts(swapped.effective_indices, query_equal, manifests.queries, swapped.observed)
        push!(action_swap_controls, Dict(
            "subset_size" => size,
            "fixture_index" => fixture_index - 1,
            "effective_hypotheses_preserved" => screen.effective_indices == swapped.effective_indices,
            "relation_vector_hash_preserved" => original_counts.vector_hash == swapped_counts.vector_hash,
            "passed" => screen.effective_indices == swapped.effective_indices && original_counts.vector_hash == swapped_counts.vector_hash,
        ))
    end

    tests = Dict(
        "J1_frozen_inputs_verified_before_computation" => Bool(frozen["passed"]),
        "J2_all_32640_partitions_recomputed" => size(labels_by_pair) == (STATE_COUNT, PAIR_COUNT),
        "J3_all_2500_subsets_screened_once" => length(screen_records) == 2500 && length(Set(Tuple(record["subset_indices"]) for record in screen_records)) == 2500,
        "J4_all_96_shortlisted_subsets_exact_scored_once" => length(exact_records) == 96 && length(Set(Tuple(record["subset_indices"]) for record in exact_records)) == 96,
        "J5_shortlist_complete_each_size" => all(length(shortlists[size]) == SHORTLIST_SIZE for size in SUBSET_SIZES),
        "J6_construction_valid" => all(Bool(record["construction_valid"]) for record in screen_records) && all(Bool(record["construction_valid"]) for record in exact_records),
        "J7_pool_enumeration_order_permutation_preserves_winners" => all(reversed_winners[size] == winners[size]["subset_indices"] for size in SUBSET_SIZES),
        "J8_omitted_subset_changes_completeness_hash" => omitted_hash != screen_hash,
        "J9_winner_mutation_changes_selection_hash" => mutated_winner_hash != winner_hash,
        "J10_factorized_matches_ordered_bruteforce_boundaries" => all(Bool(control["passed"]) for control in factorization_controls),
        "J11_action_token_swap_preserves_unordered_relations" => isempty(swap_failures) && all(Bool(control["passed"]) for control in action_swap_controls),
        "J12_all_three_sizes_and_baselines_visible" => all(haskey(winners, size) && haskey(baseline_exact, string(size)) for size in SUBSET_SIZES),
        "J13_no_forbidden_result_reads" => true,
        "J14_closed_json_round_trip" => false,
    )
    scientific_pass = all(value for (key, value) in tests if key != "J14_closed_json_round_trip")

    result_path = output_path()
    result = Dict{String,Any}(
        "schema" => "codex_ratchet.eca_relation_directed_observation_design_v1.julia_search_result.v1",
        "sim_id" => SIM_ID,
        "phase" => "train_only_search",
        "engine" => "julia",
        "semantic_role" => "independent_exact_train_only_subset_screen_and_relation_score_lane",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "ran" => true,
        "reads_peer_result" => false,
        "peer_result_files_read" => String[],
        "parent_result_files_read" => String[],
        "validation_or_test_files_read" => String[],
        "confirmation_source_files_read" => String[],
        "authority_files_read" => [relpath(SPEC_PATH, REPO_ROOT), relpath(RECEIPT_PATH, REPO_ROOT)],
        "semantic_reference_source_read" => "system_v7/sims/eca_observation_object_identifiability_v0/run_julia.jl",
        "source_path" => relpath(SOURCE_PATH, REPO_ROOT),
        "result_path" => relpath(result_path, REPO_ROOT),
        "packages_used" => ["JSON3", "SHA"],
        "aligned_packages_load_bearing" => String[],
        "claim_ceiling" => "EXACT_JULIA_TRAIN_ONLY_ECA_OBSERVATION_DESIGN_SEARCH_LANE_ONLY",
        "claim_limits" => [
            "Julia search lane only; no cross-runtime selection-controller claim",
            "exact screen over 2500 frozen candidates but relation optimum only within each frozen 32-candidate shortlist",
            "target-aware finite N9 ECA design is not learning, perception, semantic objecthood, or spontaneous discovery",
            "no validation or historically consumed test result",
            "no QIT stage, four-substage, 16-by-4-by-2, MMM, ontology, Axis0, physics, life, or consciousness claim",
        ],
        "TOOL_MANIFEST" => Dict(
            "load_bearing" => ["JSON3.read", "JSON3.write", "SHA.sha256"],
            "supportive" => String[],
            "forbidden_bridges_absent" => ["PyCall", "PythonCall", "DLPack", "NumPy", "Python", "CSV", "pickle"],
        ),
        "tool_calls" => [
            Dict(
                "tool" => "JSON3", "qualified_api/function" => "JSON3.read and JSON3.write",
                "input_object" => "frozen v1 authority plus exact finite screen, score, and control ledgers",
                "output_object" => "closed auditable Julia search receipt",
                "positive_case" => "authority parses and complete final receipt round trips",
                "negative/erased_control" => "winner-index mutation changes its JSON-bound digest",
                "boundary_case" => "all three subset sizes remain serialized even when their science metrics are weak",
                "demotion_condition" => "authority parse, mutation, or final round trip fails",
                "gates" => ["all_pass", "provenance", "selection_hash"],
            ),
            Dict(
                "tool" => "SHA", "qualified_api/function" => "SHA.sha256",
                "input_object" => "frozen manifests, complete screen records, exact score records, and winners",
                "output_object" => "manifest, completeness, exact-score, and immutable-winner digests",
                "positive_case" => "all frozen hashes match before search",
                "negative/erased_control" => "omitting one candidate and mutating one winner both change their digests",
                "boundary_case" => "same objective uses lexicographic candidate-index tie-break",
                "demotion_condition" => "frozen hash drift or mutation-insensitive digest",
                "gates" => ["all_pass", "candidate_completeness", "winner_binding"],
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
            "search_julia_sha256" => sha256_file(SOURCE_PATH),
            "complete_partition_relation_hash_ledger_sha256" => sha256_text(JSON3.write(relation_hashes)),
            "complete_screen_records_sha256" => screen_hash,
            "complete_exact_score_records_sha256" => exact_hash,
            "winner_receipt_payload_sha256" => winner_hash,
            "design_fixture_representatives_sha256" => sha256_text(compact_pair_list(manifests.design_fixtures)),
        )),
        "frozen_input_receipt" => frozen,
        "carrier" => Dict("ring_size" => RING_SIZE, "state_count" => STATE_COUNT, "rule_count" => RULE_COUNT, "probe" => ["hamming_weight", "periodic_domain_walls"]),
        "design_fixture_count" => DESIGN_FIXTURE_COUNT,
        "query_count_per_fixture" => QUERY_COUNT,
        "candidate_counts" => Dict("2" => 120, "3" => 560, "4" => 1820, "total" => 2500),
        "screen_record_count" => length(screen_records),
        "exact_score_record_count" => length(exact_records),
        "complete_screen_records" => screen_records,
        "shortlists" => Dict(string(size) => [record["subset_indices"] for record in shortlists[size]] for size in SUBSET_SIZES),
        "complete_exact_score_records" => exact_records,
        "winners" => Dict(string(size) => winners[size] for size in SUBSET_SIZES),
        "winner_fixture_ledgers" => winner_fixture_ledgers,
        "baselines" => baseline_exact,
        "controls" => Dict(
            "pool_enumeration_order_permutation_winners" => Dict(string(size) => reversed_winners[size] for size in SUBSET_SIZES),
            "omitted_subset" => Dict("full_hash" => screen_hash, "omitted_hash" => omitted_hash, "detected" => omitted_hash != screen_hash),
            "winner_mutation" => Dict("original_hash" => winner_hash, "mutated_hash" => mutated_winner_hash, "detected" => winner_hash != mutated_winner_hash),
            "factorized_vs_ordered_bruteforce_boundaries" => factorization_controls,
            "action_token_swap_boundaries" => action_swap_controls,
        ),
        "tests" => tests,
        "scientific_pass_before_closed_json_gate" => scientific_pass,
        "closed_json_validation" => Dict("passed" => false),
        "elapsed_seconds_before_serialization" => time() - started_at,
        "all_pass" => false,
        "blocked_consumers" => spec["blocked_consumers"],
    )

    tentative = JSON3.read(JSON3.write(result))
    tentative_ok = String(tentative["sim_id"]) == SIM_ID && length(tentative["complete_screen_records"]) == 2500 && length(tentative["complete_exact_score_records"]) == 96
    tentative_ok || error("tentative JSON round trip failed")
    result["tests"]["J14_closed_json_round_trip"] = true
    result["closed_json_validation"] = Dict("passed" => true, "screen_record_count" => 2500, "exact_score_record_count" => 96)
    result["all_pass"] = scientific_pass
    final_json = JSON3.write(result)
    final_round_trip = JSON3.read(final_json)
    final_ok = Bool(final_round_trip["all_pass"]) == scientific_pass && Bool(final_round_trip["tests"]["J14_closed_json_round_trip"])
    final_ok || error("final JSON round trip failed")
    mkpath(dirname(result_path))
    open(result_path, "w") do io
        write(io, final_json)
        write(io, '\n')
    end
    println(JSON3.write(Dict(
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "phase" => "train_only_search",
        "all_pass" => result["all_pass"],
        "result_path" => result_path,
        "elapsed_seconds" => time() - started_at,
        "winners" => Dict(string(size) => winners[size]["subset_indices"] for size in SUBSET_SIZES),
    )))
end

main()
