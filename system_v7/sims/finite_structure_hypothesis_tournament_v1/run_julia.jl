using Graphs
using JSON3
using SHA
using Pkg

const HERE = @__DIR__
const REPO_ROOT = normpath(joinpath(HERE, "..", "..", ".."))
const SPEC_PATH = joinpath(HERE, "spec.json")
const PREREG_PATH = joinpath(HERE, "preregistration_receipt.json")
const RESULT_PATH = joinpath(HERE, "results", "julia_result.json")
const SOURCE_PATH = abspath(@__FILE__)
const EXPECTED_SPEC_SHA256 = "060177cae89e23e19f05c6ed7f10fe729bb636db14e0d1caaab66770872efae3"
const EXPECTED_PROJECT = "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml"
const HORIZON = 3

sha256_bytes(bytes)::String = bytes2hex(SHA.sha256(bytes))
sha256_file(path::AbstractString)::String = sha256_bytes(read(path))
sha256_text(value::AbstractString)::String = sha256_bytes(codeunits(value))

function rational_string(value::Rational)::String
    denominator(value) == 1 && return string(numerator(value))
    return "$(numerator(value))/$(denominator(value))"
end

function all_permutations(n::Int)::Vector{Vector{Int}}
    n >= 0 || throw(DomainError(n, "carrier size must be nonnegative"))
    output = Vector{Vector{Int}}()
    function visit(prefix::Vector{Int}, remaining::Vector{Int})
        if isempty(remaining)
            push!(output, copy(prefix))
            return
        end
        for index in eachindex(remaining)
            value = remaining[index]
            next_remaining = vcat(remaining[1:(index - 1)], remaining[(index + 1):end])
            visit(vcat(prefix, value), next_remaining)
        end
    end
    visit(Int[], collect(0:(n - 1)))
    sort!(output; by=permutation -> join(permutation, ","))
    return output
end

permutation_key(permutation::Vector{Int})::String = join(permutation, ",")

function matrix_from_mask(n::Int, mask::Int)::BitMatrix
    matrix = falses(n, n)
    for source in 0:(n - 1), target in 0:(n - 1)
        bit = source * n + target
        matrix[source + 1, target + 1] = ((mask >> bit) & 1) == 1
    end
    return matrix
end

function matrix_from_bits(n::Int, bits::AbstractString)::BitMatrix
    length(bits) == n * n || error("adjacency bitstring length mismatch")
    matrix = falses(n, n)
    for source in 0:(n - 1), target in 0:(n - 1)
        matrix[source + 1, target + 1] = bits[source * n + target + 1] == '1'
    end
    return matrix
end

function matrix_bits(matrix::AbstractMatrix{Bool})::String
    n = size(matrix, 1)
    size(matrix, 2) == n || error("adjacency matrix must be square")
    return join(matrix[source, target] ? "1" : "0" for source in 1:n for target in 1:n)
end

function relabel_matrix(matrix::AbstractMatrix{Bool}, permutation::Vector{Int})::BitMatrix
    n = size(matrix, 1)
    output = falses(n, n)
    for source in 0:(n - 1), target in 0:(n - 1)
        output[permutation[source + 1] + 1, permutation[target + 1] + 1] = matrix[source + 1, target + 1]
    end
    return output
end

function canonical_matrix_bits(matrix::AbstractMatrix{Bool})::String
    n = size(matrix, 1)
    return minimum(matrix_bits(relabel_matrix(matrix, permutation)) for permutation in all_permutations(n))
end

function support_from_kernel(kernel::Matrix{Rational{Int}})::BitMatrix
    n = size(kernel, 1)
    support = falses(n, n)
    for source in 1:n, target in 1:n
        support[source, target] = kernel[source, target] > 0
    end
    return support
end

function relabel_kernel(kernel::Matrix{Rational{Int}}, permutation::Vector{Int})::Matrix{Rational{Int}}
    n = size(kernel, 1)
    output = fill(0 // 1, n, n)
    for source in 0:(n - 1), target in 0:(n - 1)
        output[permutation[source + 1] + 1, permutation[target + 1] + 1] = kernel[source + 1, target + 1]
    end
    return output
end

function kernel_key(kernel::Matrix{Rational{Int}})::String
    return join((rational_string(kernel[source, target]) for source in axes(kernel, 1) for target in axes(kernel, 2)), ",")
end

function canonical_kernel_key(kernel::Matrix{Rational{Int}})::String
    n = size(kernel, 1)
    return minimum(kernel_key(relabel_kernel(kernel, permutation)) for permutation in all_permutations(n))
end

function kernel_rows(kernel::Matrix{Rational{Int}})::Vector{Vector{String}}
    return [[rational_string(kernel[source, target]) for target in axes(kernel, 2)] for source in axes(kernel, 1)]
end

function make_kernel(kind::String, n::Int)::Matrix{Rational{Int}}
    n > 0 || throw(DomainError(n, "probability kernels require a nonempty carrier"))
    kernel = fill(0 // 1, n, n)
    if kind == "K0"
        fill!(kernel, 1 // n)
    elseif kind == "Klazy"
        if n == 1
            kernel[1, 1] = 1 // 1
        else
            for source in 1:n, target in 1:n
                kernel[source, target] = source == target ? 1 // 2 : 1 // (2 * (n - 1))
            end
        end
    elseif kind == "Kbiased"
        for source in 1:n, target in 1:n
            kernel[source, target] = (2 * target) // (n * (n + 1))
        end
    elseif kind == "Kidentity"
        for state in 1:n
            kernel[state, state] = 1 // 1
        end
    else
        error("unknown kernel kind: $kind")
    end
    all(sum(kernel[source, :]) == 1 // 1 for source in 1:n) || error("kernel row normalization failed")
    return kernel
end

function candidate_automorphisms(
    n::Int;
    matrix::Union{Nothing,BitMatrix}=nothing,
    kernel::Union{Nothing,Matrix{Rational{Int}}}=nothing,
    constants::Vector{Int}=Int[],
)::Vector{Vector{Int}}
    automorphisms = Vector{Vector{Int}}()
    for permutation in all_permutations(n)
        matrix_ok = matrix === nothing || relabel_matrix(matrix, permutation) == matrix
        kernel_ok = kernel === nothing || relabel_kernel(kernel, permutation) == kernel
        constants_ok = all(permutation[value + 1] == value for value in constants)
        matrix_ok && kernel_ok && constants_ok && push!(automorphisms, permutation)
    end
    return automorphisms
end

function canonical_partition(groups)::Vector{Vector{Int}}
    normalized = [sort!(Int.(collect(group))) for group in groups]
    sort!(normalized; by=group -> (first(group), length(group), join(group, ",")))
    return normalized
end

function partition_from_keys(keys)::Vector{Vector{Int}}
    groups = Dict{String,Vector{Int}}()
    for (index, key) in enumerate(keys)
        push!(get!(groups, string(key), Int[]), index - 1)
    end
    return canonical_partition(values(groups))
end

function partition_labels(partition::Vector{Vector{Int}}, n::Int)::Vector{Int}
    labels = fill(-1, n)
    for (class_index, group) in enumerate(partition), state in group
        labels[state + 1] = class_index - 1
    end
    all(label -> label >= 0, labels) || error("partition does not cover carrier")
    return labels
end

function automorphism_orbits(n::Int, automorphisms::Vector{Vector{Int}})::Vector{Vector{Int}}
    unassigned = Set(0:(n - 1))
    groups = Vector{Vector{Int}}()
    while !isempty(unassigned)
        seed = minimum(unassigned)
        orbit = sort!(unique(permutation[seed + 1] for permutation in automorphisms))
        push!(groups, orbit)
        foreach(state -> delete!(unassigned, state), orbit)
    end
    return canonical_partition(groups)
end

function graph_scc_cycle_receipt(support::BitMatrix)::Dict{String,Any}
    n = size(support, 1)
    graph = Graphs.SimpleDiGraph(n)
    for source in 1:n, target in 1:n
        support[source, target] && Graphs.add_edge!(graph, source, target)
    end
    components = canonical_partition([[vertex - 1 for vertex in component] for component in Graphs.strongly_connected_components(graph)])
    package_cycle = falses(n)
    for component in components
        if length(component) > 1
            package_cycle[component .+ 1] .= true
        else
            state = first(component)
            package_cycle[state + 1] = support[state + 1, state + 1]
        end
    end

    reach = copy(support)
    for pivot in 1:n, source in 1:n, target in 1:n
        reach[source, target] = reach[source, target] || (reach[source, pivot] && reach[pivot, target])
    end
    independent_cycle = [reach[state, state] for state in 1:n]
    return Dict(
        "sccs" => components,
        "cycle_membership" => Bool.(package_cycle),
        "independent_cycle_membership" => independent_cycle,
        "package_independent_parity" => Bool.(package_cycle) == independent_cycle,
        "persistent_support" => all(package_cycle),
        "edge_count" => Graphs.ne(graph),
    )
end

function strong_bisimulation_partition(support::BitMatrix)::Vector{Vector{Int}}
    n = size(support, 1)
    partition = [collect(0:(n - 1))]
    while true
        labels = partition_labels(partition, n)
        signatures = String[]
        for state in 0:(n - 1)
            target_classes = sort!(unique(labels[target + 1] for target in 0:(n - 1) if support[state + 1, target + 1]))
            push!(signatures, "$(labels[state + 1])|$(join(target_classes, ','))")
        end
        refined = partition_from_keys(signatures)
        refined == partition && return refined
        partition = refined
    end
end

function local_probe_partition(support::BitMatrix)::Vector{Vector{Int}}
    n = size(support, 1)
    outdegrees = [sum(support[state, :]) for state in 1:n]
    indegrees = [sum(support[:, state]) for state in 1:n]
    fingerprints = String[]
    for state in 1:n
        successor_outdegrees = sort!([outdegrees[target] for target in 1:n if support[state, target]])
        predecessor_indegrees = sort!([indegrees[source] for source in 1:n if support[source, state]])
        push!(fingerprints, join((
            support[state, state] ? "1" : "0",
            string(indegrees[state]),
            string(outdegrees[state]),
            join(successor_outdegrees, ":"),
            join(predecessor_indegrees, ":"),
        ), "|"))
    end
    return partition_from_keys(fingerprints)
end

function kernel_row_partition(kernel::Matrix{Rational{Int}})::Vector{Vector{Int}}
    return partition_from_keys([join((rational_string(value) for value in kernel[row, :]), ",") for row in axes(kernel, 1)])
end

function partition_refines(left::Vector{Vector{Int}}, right::Vector{Vector{Int}})::Bool
    return all(any(issubset(Set(left_group), Set(right_group)) for right_group in right) for left_group in left)
end

function same_partition_relation(partition::Vector{Vector{Int}}, left::Int, right::Int)::Bool
    return any(left in group && right in group for group in partition)
end

function partition_disagreement_witness(left::Vector{Vector{Int}}, right::Vector{Vector{Int}}, n::Int)
    for a in 0:(n - 1), b in (a + 1):(n - 1)
        left_same = same_partition_relation(left, a, b)
        right_same = same_partition_relation(right, a, b)
        left_same != right_same && return Dict("states" => [a, b], "left_same" => left_same, "right_same" => right_same)
    end
    return nothing
end

function distinction_comparison(partitions::Dict{String,Vector{Vector{Int}}}, n::Int)::Vector{Dict{String,Any}}
    names = sort!(collect(keys(partitions)))
    output = Vector{Dict{String,Any}}()
    for left_index in eachindex(names), right_index in (left_index + 1):length(names)
        left_name, right_name = names[left_index], names[right_index]
        left, right = partitions[left_name], partitions[right_name]
        equal = left == right
        push!(output, Dict(
            "left" => left_name,
            "right" => right_name,
            "equal" => equal,
            "left_refines_right" => partition_refines(left, right),
            "right_refines_left" => partition_refines(right, left),
            "disagreement_witness" => equal ? nothing : partition_disagreement_witness(left, right, n),
        ))
    end
    return output
end

function signature_key(semantic_type::String, named_constants::Vector{Int})::Vector{Int}
    has_relation = semantic_type in ("static_relation", "transition_relation") ? 1 : 0
    has_transition = semantic_type in ("transition_relation", "markov_kernel") ? 1 : 0
    has_probability = semantic_type == "markov_kernel" ? 1 : 0
    return [has_relation, has_transition, has_probability, length(named_constants)]
end

function stochastic_key(kernel::Matrix{Rational{Int}})::Tuple{Rational{Int},Rational{Int}}
    n = size(kernel, 1)
    source_dependence = sum(abs(kernel[source, target] - kernel[1, target]) for source in 2:n for target in 1:n; init=0 // 1)
    destination_bias = sum(abs(sum(kernel[source, target] for source in 1:n) // n - 1 // n) for target in 1:n; init=0 // 1)
    return source_dependence, destination_bias
end

function shannon_entropy(row)::Float64
    return -sum(Float64(value) * log2(Float64(value)) for value in row if value > 0; init=0.0)
end

function conditional_entropy(kernel::Matrix{Rational{Int}})::Float64
    return sum(shannon_entropy(kernel[row, :]) for row in axes(kernel, 1)) / size(kernel, 1)
end

function candidate_record(
    id::String,
    n::Int,
    semantic_type::String;
    matrix::Union{Nothing,BitMatrix}=nothing,
    presentation_matrix::Union{Nothing,BitMatrix}=matrix,
    kernel::Union{Nothing,Matrix{Rational{Int}}}=nothing,
    named_constants::Vector{Int}=Int[],
    aliases::Vector{String}=String[id],
    family::String,
    labelled_multiplicity::Union{Nothing,Int}=nothing,
)::Dict{String,Any}
    support = matrix === nothing ? (kernel === nothing ? nothing : support_from_kernel(kernel)) : matrix
    automorphisms = candidate_automorphisms(n; matrix=matrix, kernel=kernel, constants=named_constants)
    partitions = Dict{String,Vector{Vector{Int}}}(
        "automorphism_orbits" => automorphism_orbits(n, automorphisms),
    )
    if support !== nothing
        partitions["local_probe_equivalence"] = local_probe_partition(support)
    end
    if semantic_type == "transition_relation"
        partitions["strong_bisimulation"] = strong_bisimulation_partition(support)
    end
    if semantic_type == "markov_kernel"
        partitions["kernel_row_equivalence"] = kernel_row_partition(kernel)
    end

    graphs_receipt = semantic_type in ("transition_relation", "markov_kernel") ? graph_scc_cycle_receipt(support) : nothing
    serial = graphs_receipt === nothing ? nothing : all(sum(support[state, :]) >= 1 for state in 1:n)
    persistent = graphs_receipt === nothing ? nothing : Bool(graphs_receipt["persistent_support"])
    branching = graphs_receipt === nothing ? nothing : n > 1 && all(sum(support[state, :]) >= 2 for state in 1:n)
    exploratory = graphs_receipt === nothing ? nothing : persistent && branching
    unbiased = kernel === nothing ? nothing : all(kernel[source, target] == 1 // n for source in 1:n for target in 1:n)

    exact_stochastic_key = kernel === nothing ? nothing : stochastic_key(kernel)
    identity = if semantic_type == "empty_signature"
        "$n|$semantic_type|empty|$(join(named_constants, ','))"
    elseif kernel !== nothing
        "$n|$semantic_type|$(kernel_key(kernel))|$(join(named_constants, ','))"
    else
        "$n|$semantic_type|$(matrix_bits(matrix))|$(join(named_constants, ','))"
    end

    return Dict{String,Any}(
        "id" => id,
        "aliases" => sort!(unique(aliases)),
        "registry_identity" => identity,
        "registry_identity_sha256" => sha256_text(identity),
        "carrier_size" => n,
        "semantic_type" => semantic_type,
        "family" => family,
        "named_constants" => named_constants,
        "canonical_adjacency" => matrix === nothing ? nothing : matrix_bits(matrix),
        "source_presentation_adjacency" => presentation_matrix === nothing ? nothing : matrix_bits(presentation_matrix),
        "presentation_canonicalization_verified" => matrix === nothing || (presentation_matrix !== nothing && canonical_matrix_bits(presentation_matrix) == matrix_bits(matrix)),
        "support_adjacency" => support === nothing ? nothing : matrix_bits(support),
        "exact_kernel_rows" => kernel === nothing ? nothing : kernel_rows(kernel),
        "labelled_multiplicity" => labelled_multiplicity,
        "signature_commitment_key" => signature_key(semantic_type, named_constants),
        "stochastic_neutrality_key" => exact_stochastic_key === nothing ? nothing : [rational_string(exact_stochastic_key[1]), rational_string(exact_stochastic_key[2])],
        "automorphism_order" => length(automorphisms),
        "automorphism_permutations" => automorphisms,
        "automorphism_keys" => sort!(permutation_key.(automorphisms)),
        "graphs_cycle_receipt" => graphs_receipt,
        "viability" => Dict(
            "V_registered" => true,
            "V_serial" => serial,
            "V_persistent_support" => persistent,
            "V_branching" => branching,
            "V_exploratory_support" => exploratory,
            "V_unbiased_stochastic" => unbiased,
        ),
        "distinction_partitions" => partitions,
        "distinction_comparisons" => distinction_comparison(partitions, n),
        "_matrix" => matrix,
        "_kernel" => kernel,
        "_support" => support,
        "_stochastic_key" => exact_stochastic_key,
    )
end

function output_candidate(candidate::Dict{String,Any})::Dict{String,Any}
    return Dict(key => value for (key, value) in candidate if !startswith(key, "_"))
end

function exhaustive_relation_candidates(n::Int, semantic_type::String)
    class_counts = Dict{String,Int}()
    for mask in 0:((1 << (n * n)) - 1)
        canonical = canonical_matrix_bits(matrix_from_mask(n, mask))
        class_counts[canonical] = get(class_counts, canonical, 0) + 1
    end
    candidates = Vector{Dict{String,Any}}()
    orbit_stabilizer_pass = true
    universal_bits = repeat("1", n * n)
    for bits in sort!(collect(keys(class_counts)))
        matrix = matrix_from_bits(n, bits)
        id = if bits == universal_bits
            semantic_type == "static_relation" ? "J_$n" : "C_$n"
        else
            prefix = semantic_type == "static_relation" ? "R" : "T"
            "$(prefix)_$(n)_$(bits)"
        end
        aliases = bits == universal_bits ? [id, semantic_type == "static_relation" ? "J_n@n=$n" : "C_n@n=$n"] : [id]
        candidate = candidate_record(
            id,
            n,
            semantic_type;
            matrix=matrix,
            aliases=aliases,
            family=semantic_type == "static_relation" ? "all_static_binary_relations" : "all_binary_transition_supports",
            labelled_multiplicity=class_counts[bits],
        )
        orbit_stabilizer_pass &= class_counts[bits] == factorial(n) ÷ Int(candidate["automorphism_order"])
        push!(candidates, candidate)
    end
    return candidates, Dict(
        "labelled_count" => sum(values(class_counts)),
        "isomorphism_class_count" => length(class_counts),
        "class_multiplicity_sum" => sum(values(class_counts)),
        "orbit_stabilizer_pass" => orbit_stabilizer_pass,
    )
end

function add_or_alias_kernel!(registry::Vector{Dict{String,Any}}, n::Int, kind::String)
    kernel = make_kernel(kind, n)
    identity = "$n|markov_kernel|$(kernel_key(kernel))|"
    alias = "$(kind)_$n"
    for candidate in registry
        if candidate["registry_identity"] == identity
            append!(candidate["aliases"], [alias, "$(kind)_n@n=$n"])
            candidate["aliases"] = sort!(unique(String.(candidate["aliases"])))
            return false
        end
    end
    push!(registry, candidate_record(
        alias,
        n,
        "markov_kernel";
        kernel=kernel,
        aliases=[alias, "$(kind)_n@n=$n"],
        family="named_kernel_family",
    ))
    return true
end

function build_registry()
    registry = Vector{Dict{String,Any}}()
    counts = Dict{String,Any}()
    relation_census = Dict{String,Any}()
    for n in 1:3
        push!(registry, candidate_record("U_$n", n, "empty_signature"; aliases=["U_$n", "U_n@n=$n"], family="root_presentations"))
        static_candidates, static_census = exhaustive_relation_candidates(n, "static_relation")
        transition_candidates, transition_census = exhaustive_relation_candidates(n, "transition_relation")
        append!(registry, static_candidates)
        append!(registry, transition_candidates)
        relation_census[string(n)] = Dict("static" => static_census, "transition" => transition_census)
        for kind in ("K0", "Klazy", "Kbiased", "Kidentity")
            add_or_alias_kernel!(registry, n, kind)
        end
    end

    n = 4
    push!(registry, candidate_record("U_4", n, "empty_signature"; aliases=["U_4", "U_n@n=4"], family="root_presentations"))
    empty = falses(n, n)
    universal = trues(n, n)
    identity = falses(n, n)
    for state in 1:n
        identity[state, state] = true
    end
    cycle = falses(n, n)
    for state in 0:(n - 1)
        cycle[state + 1, mod(state + 1, n) + 1] = true
    end
    terminal = falses(n, n)
    terminal[1, 2] = terminal[2, 3] = terminal[3, 4] = terminal[4, 4] = true
    cycle_presentation = copy(cycle)
    terminal_presentation = copy(terminal)
    cycle = matrix_from_bits(n, canonical_matrix_bits(cycle))
    terminal = matrix_from_bits(n, canonical_matrix_bits(terminal))

    push!(registry, candidate_record("R4_empty", n, "static_relation"; matrix=empty, aliases=["R4_empty", "empty relation"], family="named_relation_controls_at_n4"))
    push!(registry, candidate_record("J_4", n, "static_relation"; matrix=universal, aliases=["J_4", "J_n@n=4", "universal relation"], family="named_relation_controls_at_n4"))
    push!(registry, candidate_record("C_4", n, "transition_relation"; matrix=universal, aliases=["C_4", "C_n@n=4"], family="root_presentations"))
    push!(registry, candidate_record("T4_identity", n, "transition_relation"; matrix=identity, aliases=["T4_identity", "identity loops"], family="named_relation_controls_at_n4"))
    push!(registry, candidate_record("T4_cycle", n, "transition_relation"; matrix=cycle, presentation_matrix=cycle_presentation, aliases=["T4_cycle", "directed four-cycle"], family="named_relation_controls_at_n4"))
    push!(registry, candidate_record("T4_terminal", n, "transition_relation"; matrix=terminal, presentation_matrix=terminal_presentation, aliases=["T4_terminal", "terminal path 0->1->2->3 with 3->3"], family="named_relation_controls_at_n4"))
    push!(registry, candidate_record("J4_c0", n, "static_relation"; matrix=universal, named_constants=[0], aliases=["J4_c0", "universal relation with named constant c0=0"], family="named_relation_controls_at_n4"))
    push!(registry, candidate_record("J4_c0_c1", n, "static_relation"; matrix=universal, named_constants=[0, 1], aliases=["J4_c0_c1", "universal relation with named constants c0=0 and c1=1"], family="named_relation_controls_at_n4"))
    for kind in ("K0", "Klazy", "Kbiased", "Kidentity")
        add_or_alias_kernel!(registry, n, kind)
    end

    identities = String.(getindex.(registry, "registry_identity"))
    counts["total_registry_candidates"] = length(registry)
    counts["unique_registry_identities"] = length(unique(identities))
    counts["registry_identity_unique"] = length(registry) == length(unique(identities))
    counts["by_carrier_size"] = Dict(string(n) => count(candidate -> candidate["carrier_size"] == n, registry) for n in 1:4)
    counts["by_semantic_type"] = Dict(kind => count(candidate -> candidate["semantic_type"] == kind, registry) for kind in ("empty_signature", "static_relation", "transition_relation", "markov_kernel"))
    counts["relation_census"] = relation_census
    counts["kernel_alias_collapse"] = Dict(
        string(n) => Dict(
            "named_presentations" => 4,
            "registry_identities" => count(candidate -> candidate["carrier_size"] == n && candidate["semantic_type"] == "markov_kernel", registry),
        ) for n in 1:4
    )
    return registry, counts
end

function candidate_by_id(registry, id::String)
    matches = [candidate for candidate in registry if candidate["id"] == id]
    length(matches) == 1 || error("candidate id lookup failed for $id")
    return first(matches)
end

function preorder_applicable(candidate::Dict{String,Any}, preorder::String)::Bool
    preorder == "signature_commitment" && return true
    preorder == "automorphism_freedom" && return true
    preorder == "support_freedom" && return candidate["_support"] !== nothing
    preorder == "stochastic_neutrality" && return candidate["_kernel"] !== nothing
    error("unknown preorder $preorder")
end

function weak_or_equal(left::Dict{String,Any}, right::Dict{String,Any}, preorder::String)::Bool
    left["carrier_size"] == right["carrier_size"] || return false
    preorder_applicable(left, preorder) && preorder_applicable(right, preorder) || return false
    if preorder == "signature_commitment"
        return all(left["signature_commitment_key"] .<= right["signature_commitment_key"])
    elseif preorder == "support_freedom"
        return all(left["_support"] .| .!right["_support"])
    elseif preorder == "automorphism_freedom"
        return issubset(Set(right["automorphism_keys"]), Set(left["automorphism_keys"]))
    elseif preorder == "stochastic_neutrality"
        left_key, right_key = left["_stochastic_key"], right["_stochastic_key"]
        return left_key[1] <= right_key[1] && left_key[2] <= right_key[2]
    end
    error("unknown preorder $preorder")
end

function mss_arm(registry, n::Int, arm_id::String, preorder::String, viability::String)::Dict{String,Any}
    candidates = [candidate for candidate in registry if candidate["carrier_size"] == n && preorder_applicable(candidate, preorder) && candidate["viability"][viability] === true]
    unassigned = Set(String(candidate["id"]) for candidate in candidates)
    classes = Vector{Vector{String}}()
    by_id = Dict(String(candidate["id"]) => candidate for candidate in candidates)
    while !isempty(unassigned)
        seed_id = minimum(unassigned)
        seed = by_id[seed_id]
        equivalence_class = sort!([candidate_id for candidate_id in unassigned if weak_or_equal(seed, by_id[candidate_id], preorder) && weak_or_equal(by_id[candidate_id], seed, preorder)])
        push!(classes, equivalence_class)
        foreach(candidate_id -> delete!(unassigned, candidate_id), equivalence_class)
    end
    sort!(classes; by=group -> join(group, "|"))

    frontier = Vector{Vector{String}}()
    for equivalence_class in classes
        candidate = by_id[first(equivalence_class)]
        dominated = any(other_class -> begin
            other_class == equivalence_class && return false
            other = by_id[first(other_class)]
            weak_or_equal(other, candidate, preorder) && !weak_or_equal(candidate, other, preorder)
        end, classes)
        !dominated && push!(frontier, equivalence_class)
    end
    status = isempty(frontier) ? "NO_SURVIVOR" : length(frontier) == 1 ? "singleton_equivalence_class" : "plural_incomparable_classes"
    return Dict(
        "arm_id" => arm_id,
        "carrier_size" => n,
        "preorder" => preorder,
        "viability" => viability,
        "applicable_viable_candidate_count" => length(candidates),
        "viable_equivalence_classes" => classes,
        "frontier_classes" => frontier,
        "frontier_status" => status,
    )
end

function all_mss_arms(registry, spec)::Vector{Dict{String,Any}}
    results = Vector{Dict{String,Any}}()
    for n in 1:4, arm in spec["mss_arms"]
        push!(results, mss_arm(registry, n, String(arm["id"]), String(arm["preorder"]), String(arm["viability"])))
    end
    return results
end

function append_chain_receipt()::Dict{String,Any}
    n = 4
    universal = trues(n, n)
    steps = [
        ("A0", nothing, Int[], 24),
        ("A1", universal, Int[], 24),
        ("A2", universal, [0], 6),
        ("A3", universal, [0, 1], 2),
    ]
    records = Vector{Dict{String,Any}}()
    sets = Vector{Set{String}}()
    for (id, matrix, constants, expected_order) in steps
        automorphisms = candidate_automorphisms(n; matrix=matrix, constants=constants)
        keys = sort!(permutation_key.(automorphisms))
        push!(sets, Set(keys))
        push!(records, Dict("id" => id, "named_constants" => constants, "aut_order" => length(keys), "expected_aut_order" => expected_order, "aut_permutations" => automorphisms, "order_pass" => length(keys) == expected_order))
    end
    adjacent = Vector{Dict{String,Any}}()
    for index in 1:(length(records) - 1)
        subset = issubset(sets[index + 1], sets[index])
        strict = sets[index + 1] != sets[index]
        expected_strict = index > 1
        push!(adjacent, Dict(
            "from" => records[index]["id"],
            "to" => records[index + 1]["id"],
            "next_subset_previous" => subset,
            "strict" => strict,
            "expected_strict" => expected_strict,
            "append_subgroup_query_direct_status" => subset ? "unsat" : "sat",
            "append_strictness_query_direct_status" => strict ? "sat" : "unsat",
            "pass" => subset && strict == expected_strict,
        ))
    end
    b2 = candidate_automorphisms(n; matrix=universal, constants=[1])
    b2_set = Set(permutation_key.(b2))
    replacement_witness_key = minimum(collect(setdiff(b2_set, sets[3])))
    replacement_witness = parse.(Int, split(replacement_witness_key, ","))
    replacement_replay = permutation_key(replacement_witness) in b2_set && !(permutation_key(replacement_witness) in sets[3])
    return Dict(
        "steps" => records,
        "adjacent_checks" => adjacent,
        "replacement_control" => Dict(
            "B2_named_constants" => [1],
            "B2_aut_order" => length(b2),
            "B2_subset_A2" => issubset(b2_set, sets[3]),
            "direct_status" => isempty(setdiff(b2_set, sets[3])) ? "unsat" : "sat",
            "witness_permutation" => replacement_witness,
            "witness_replay_pass" => replacement_replay,
            "pass" => !issubset(b2_set, sets[3]) && replacement_replay,
        ),
        "carrier_growth_subgroup_comparison" => "REFUSED_NOT_TYPED",
        "all_pass" => all(record["order_pass"] for record in records) && all(check["pass"] for check in adjacent) && replacement_replay,
    )
end

function external_gate_receipt()::Dict{String,Any}
    n = 3
    all_masks = collect(0:((1 << (n * n)) - 1))
    gate_functions = [
        ("none", matrix -> true, 512),
        ("reflexive", matrix -> all(matrix[index, index] for index in 1:n), 64),
        ("reflexive_and_symmetric", matrix -> all(matrix[index, index] for index in 1:n) && matrix == transpose(matrix), 8),
        ("universal", matrix -> all(matrix), 1),
    ]
    baseline = Dict{Int,String}()
    for mask in all_masks
        matrix = matrix_from_mask(n, mask)
        automorphisms = sort!(permutation_key.(candidate_automorphisms(n; matrix=matrix)))
        baseline[mask] = sha256_text("$(matrix_bits(matrix))|$(join(automorphisms, ';'))")
    end
    stages = Vector{Dict{String,Any}}()
    previous = Set(all_masks)
    for (name, gate, expected) in gate_functions
        admitted = Set(mask for mask in all_masks if gate(matrix_from_mask(n, mask)))
        unchanged = all(mask -> begin
            matrix = matrix_from_mask(n, mask)
            automorphisms = sort!(permutation_key.(candidate_automorphisms(n; matrix=matrix)))
            baseline[mask] == sha256_text("$(matrix_bits(matrix))|$(join(automorphisms, ';'))")
        end, admitted)
        digest = sha256_text(join(("$mask:$(baseline[mask])" for mask in sort!(collect(admitted))), "|"))
        push!(stages, Dict(
            "gate" => name,
            "model_count" => length(admitted),
            "expected_model_count" => expected,
            "subset_previous" => issubset(admitted, previous),
            "survivor_internal_digest_unchanged" => unchanged,
            "admitted_ledger_sha256" => digest,
            "pass" => length(admitted) == expected && issubset(admitted, previous) && unchanged,
        ))
        previous = admitted
    end
    return Dict(
        "stages" => stages,
        "external_filtering_not_internal_symmetry_breaking" => true,
        "all_pass" => all(stage["pass"] for stage in stages),
    )
end

function entropy_capacity_receipt(registry)::Dict{String,Any}
    per_size = Vector{Dict{String,Any}}()
    for n in 1:4
        k0 = candidate_by_id(registry, "K0_$n")
        kernel = k0["_kernel"]
        uniform = fill(1 // n, n)
        after = [sum(uniform[source] * kernel[source, target] for source in 1:n) for target in 1:n]
        exact_stationary = after == uniform
        push!(per_size, Dict(
            "carrier_size" => n,
            "K0_fixed_n_state_entropy_change_exact" => exact_stationary ? "0" : "nonzero",
            "K0_fixed_n_state_entropy_change_float" => shannon_entropy(after) - shannon_entropy(uniform),
            "K0_one_step_conditional_entropy" => log2(n),
            "K0_one_step_conditional_entropy_formula" => "log2($n)",
            "K0_path_entropy_horizon_$HORIZON" => HORIZON * log2(n),
            "C_support_path_capacity_horizon_$HORIZON" => HORIZON * log2(n),
            "C_support_path_count_per_start" => n^HORIZON,
            "fixed_n_pass" => exact_stationary && isapprox(conditional_entropy(kernel), log2(n); atol=1.0e-14, rtol=0.0),
        ))
    end
    cross_size = Vector{Dict{String,Any}}()
    for n in 1:3
        old_extended = vcat(fill(1 // n, n), 0 // 1)
        new_uniform = fill(1 // (n + 1), n + 1)
        total_variation = sum(abs(old_extended[index] - new_uniform[index]) for index in 1:(n + 1)) // 2
        push!(cross_size, Dict(
            "from_n" => n,
            "to_n" => n + 1,
            "inclusion" => collect(0:(n - 1)),
            "capacity_change" => log2(n + 1) - log2(n),
            "capacity_change_formula" => "log2($(n + 1))-log2($n)",
            "uniform_inclusion_total_variation_exact" => rational_string(total_variation),
            "uniform_inclusion_total_variation_expected" => rational_string(1 // (n + 1)),
            "pass" => total_variation == 1 // (n + 1) && total_variation > 0,
        ))
    end
    counts = [512, 64, 8, 1]
    compression = [Dict(
        "before" => counts[index],
        "after" => counts[index + 1],
        "log2_model_set_change" => log2(counts[index + 1]) - log2(counts[index]),
        "nonpositive" => counts[index + 1] <= counts[index],
    ) for index in 1:(length(counts) - 1)]
    return Dict(
        "per_size" => per_size,
        "cross_size_explicit_inclusions" => cross_size,
        "external_model_set_compression" => compression,
        "causal_status" => "readouts_only_no_search_adjacency_mobility_acceptance_or_coupling",
        "all_pass" => all(row["fixed_n_pass"] for row in per_size) && all(row["pass"] for row in cross_size) && all(row["nonpositive"] for row in compression),
    )
end

function relabel_invariance_receipt(registry)::Dict{String,Any}
    cases = 0
    failures = Vector{Dict{String,Any}}()
    for candidate in registry
        n = Int(candidate["carrier_size"])
        matrix, kernel = candidate["_matrix"], candidate["_kernel"]
        matrix === nothing && kernel === nothing && continue
        base_canonical = matrix === nothing ? canonical_kernel_key(kernel) : canonical_matrix_bits(matrix)
        base_viability = candidate["viability"]
        base_shapes = Dict(name => sort!(length.(partition)) for (name, partition) in candidate["distinction_partitions"])
        for permutation in all_permutations(n)
            cases += 1
            transformed_matrix = matrix === nothing ? nothing : relabel_matrix(matrix, permutation)
            transformed_kernel = kernel === nothing ? nothing : relabel_kernel(kernel, permutation)
            transformed = candidate_record(
                "control",
                n,
                String(candidate["semantic_type"]);
                matrix=transformed_matrix,
                kernel=transformed_kernel,
                named_constants=[permutation[value + 1] for value in candidate["named_constants"]],
                aliases=["control"],
                family="relabel_control",
            )
            transformed_canonical = transformed_matrix === nothing ? canonical_kernel_key(transformed_kernel) : canonical_matrix_bits(transformed_matrix)
            transformed_shapes = Dict(name => sort!(length.(partition)) for (name, partition) in transformed["distinction_partitions"])
            pass = base_canonical == transformed_canonical && base_viability == transformed["viability"] && base_shapes == transformed_shapes
            !pass && push!(failures, Dict("candidate_id" => candidate["id"], "permutation" => permutation))
        end
    end
    return Dict("cases" => cases, "failures" => failures, "pass" => isempty(failures), "all_pass" => isempty(failures), "frontier_equivalence_note" => "canonical registry identity is unchanged, so the relabelled representative maps to the same MSS class")
end

function controls_receipt(registry, counts, append_chain, external_gates, entropy_readouts)::Dict{String,Any}
    n0_refusal = false
    n0_error = ""
    try
        make_kernel("K0", 0)
    catch error_value
        n0_refusal = error_value isa DomainError
        n0_error = string(typeof(error_value))
    end

    jc = Vector{Dict{String,Any}}()
    for n in 1:4
        j = candidate_by_id(registry, "J_$n")
        c = candidate_by_id(registry, "C_$n")
        support_equal = j["support_adjacency"] == c["support_adjacency"]
        semantic_separate = j["registry_identity"] != c["registry_identity"] && j["semantic_type"] != c["semantic_type"]
        push!(jc, Dict("carrier_size" => n, "support_equal" => support_equal, "semantic_registry_separate" => semantic_separate, "label_blind_path_count_equal" => n^HORIZON == n^HORIZON, "pass" => support_equal && semantic_separate))
    end

    k0_3 = candidate_by_id(registry, "K0_3")
    klazy_3 = candidate_by_id(registry, "Klazy_3")
    kernel_contrast = Dict(
        "carrier_size" => 3,
        "support_equal_full" => k0_3["support_adjacency"] == klazy_3["support_adjacency"] == repeat("1", 9),
        "automorphism_sets_equal_full" => k0_3["automorphism_keys"] == klazy_3["automorphism_keys"] && length(k0_3["automorphism_keys"]) == 6,
        "source_dependence_exact" => [k0_3["stochastic_neutrality_key"][1], klazy_3["stochastic_neutrality_key"][1]],
        "conditional_entropies" => [conditional_entropy(k0_3["_kernel"]), conditional_entropy(klazy_3["_kernel"])],
    )
    kernel_contrast["pass"] = kernel_contrast["support_equal_full"] && kernel_contrast["automorphism_sets_equal_full"] && kernel_contrast["source_dependence_exact"][1] != kernel_contrast["source_dependence_exact"][2] && kernel_contrast["conditional_entropies"][1] != kernel_contrast["conditional_entropies"][2]

    t4_cycle = candidate_by_id(registry, "T4_cycle")
    t4_terminal = candidate_by_id(registry, "T4_terminal")
    graphs_control = Dict(
        "positive_cycle_persistent" => t4_cycle["viability"]["V_persistent_support"],
        "negative_terminal_serial" => t4_terminal["viability"]["V_serial"],
        "negative_terminal_not_persistent" => !t4_terminal["viability"]["V_persistent_support"],
        "boundary_n1_loop_persistent" => candidate_by_id(registry, "C_1")["viability"]["V_persistent_support"],
        "boundary_n1_empty_not_persistent" => !candidate_by_id(registry, "T_1_0")["viability"]["V_persistent_support"],
        "package_independent_all_candidates" => all(candidate["graphs_cycle_receipt"] === nothing || candidate["graphs_cycle_receipt"]["package_independent_parity"] for candidate in registry),
    )
    graphs_control["pass"] = all(values(graphs_control))

    n1_branching = all(candidate["viability"]["V_branching"] !== true for candidate in registry if candidate["carrier_size"] == 1)
    relation_counts_pass = all(begin
        census = counts["relation_census"][string(n)]
        expected = 1 << (n * n)
        census["static"]["labelled_count"] == expected && census["transition"]["labelled_count"] == expected && census["static"]["orbit_stabilizer_pass"] && census["transition"]["orbit_stabilizer_pass"]
    end for n in 1:3)
    relabel = relabel_invariance_receipt(registry)
    n1_kernel = candidate_by_id(registry, "K0_1")
    n2_kernel = candidate_by_id(registry, "K0_2")
    expected_n1_aliases = Set(["K0_1", "Klazy_1", "Kbiased_1", "Kidentity_1", "K0_n@n=1", "Klazy_n@n=1", "Kbiased_n@n=1", "Kidentity_n@n=1"])
    expected_n2_collapsed_aliases = Set(["K0_2", "Klazy_2", "K0_n@n=2", "Klazy_n@n=2"])
    kernel_collision_pass = counts["by_carrier_size"] == Dict("1" => 6, "2" => 24, "3" => 213, "4" => 13) &&
        Set(String.(n1_kernel["aliases"])) == expected_n1_aliases &&
        issubset(expected_n2_collapsed_aliases, Set(String.(n2_kernel["aliases"]))) &&
        counts["kernel_alias_collapse"]["1"]["registry_identities"] == 1 &&
        counts["kernel_alias_collapse"]["2"]["registry_identities"] == 3

    return Dict(
        "relation_exhaustive_counts_and_orbit_stabilizer" => Dict("pass" => relation_counts_pass),
        "registry_identity_unique_aliases_deduplicated" => Dict("pass" => counts["registry_identity_unique"], "kernel_alias_collapse" => counts["kernel_alias_collapse"]),
        "named_kernel_exact_identity_collisions" => Dict(
            "pass" => kernel_collision_pass,
            "expected_registry_counts_n1_n2_n3" => [6, 24, 213],
            "actual_registry_counts_n1_n2_n3" => [counts["by_carrier_size"][string(n)] for n in 1:3],
            "n1_collapsed_aliases" => sort!(collect(expected_n1_aliases)),
            "n2_K0_Klazy_collapsed_aliases" => sort!(collect(expected_n2_collapsed_aliases)),
        ),
        "independent_carrier_relabeling" => relabel,
        "n0_K0_refusal" => Dict("pass" => n0_refusal, "error_type" => n0_error),
        "n1_no_branching" => Dict("pass" => n1_branching),
        "J_C_encoding_semantic_separation" => Dict("cases" => jc, "pass" => all(case["pass"] for case in jc)),
        "K0_Klazy_full_support_symmetry_but_distinct_memory_entropy" => kernel_contrast,
        "Graphs_SCC_cycle_controls" => graphs_control,
        "fixed_carrier_append" => Dict("pass" => append_chain["all_pass"]),
        "external_gate_internal_immutability" => Dict("pass" => external_gates["all_pass"]),
        "typed_entropy_capacity" => Dict("pass" => entropy_readouts["all_pass"]),
    )
end

function tool_receipts()::Vector{Dict{String,Any}}
    return [
        Dict(
            "tool" => "Graphs",
            "qualified_api/function" => "Graphs.SimpleDiGraph, Graphs.add_edge!, Graphs.strongly_connected_components",
            "input_object" => "every independently constructed transition-support and positive-kernel-support graph",
            "output_object" => "exact SCC partitions and per-state directed-cycle membership used by V_persistent_support",
            "positive_case" => "the named directed four-cycle has every state in one persistent SCC",
            "negative/erased_control" => "the serial terminal-path control fails persistence; replacing SCC cycle membership with seriality would incorrectly pass it",
            "boundary_case" => "the n=1 self-loop passes persistence while the n=1 empty transition support fails",
            "demotion_condition" => "any package/independent transitive-closure mismatch or named control mismatch forces all_pass false",
            "gates" => ["all_pass", "V_persistent_support", "V_exploratory_support", "MSS frontiers"],
            "load_bearing" => true,
        ),
        Dict(
            "tool" => "JSON3",
            "qualified_api/function" => "JSON3.read and JSON3.write",
            "input_object" => "frozen spec, green preregistration, and closed Julia result",
            "output_object" => "source-bound input objects and round-tripped result receipt",
            "positive_case" => "spec/preregistration parse and final required fields round-trip",
            "negative/erased_control" => "spec hash or preregistration binding drift aborts before enumeration",
            "boundary_case" => "nothing-valued inapplicable partitions and viability predicates remain explicit JSON nulls",
            "demotion_condition" => "closed receipt parse or required-field parity fails",
            "gates" => ["all_pass", "provenance", "result emission"],
            "load_bearing" => true,
        ),
        Dict(
            "tool" => "SHA",
            "qualified_api/function" => "SHA.sha256",
            "input_object" => "frozen spec, Julia source, registry identities, and survivor ledgers",
            "output_object" => "spec/source provenance and deterministic identity/ledger digests",
            "positive_case" => "the exact amended spec hash is bound before any candidate is built",
            "negative/erased_control" => "one-byte frozen-spec drift aborts execution",
            "boundary_case" => "empty-signature identity has an explicit digest despite carrying no relation bytes",
            "demotion_condition" => "any frozen hash mismatch forces no result emission",
            "gates" => ["all_pass", "provenance", "registry identity"],
            "load_bearing" => true,
        ),
    ]
end

function runtime_receipt()::Dict{String,Any}
    dependencies = Pkg.dependencies()
    versions = Dict{String,String}()
    for name in ("Graphs", "JSON3")
        package = first(package for package in values(dependencies) if package.name == name)
        versions[name] = string(package.version)
    end
    return Dict(
        "julia_version" => string(VERSION),
        "active_project" => Base.active_project(),
        "expected_project" => EXPECTED_PROJECT,
        "load_path" => copy(Base.LOAD_PATH),
        "kernel" => string(Sys.KERNEL),
        "architecture" => string(Sys.ARCH),
        "packages" => versions,
        "canonical_carrier_direct_check" => Base.active_project() == EXPECTED_PROJECT && Base.LOAD_PATH == ["@", "@stdlib"] && haskey(versions, "Graphs") && haskey(versions, "JSON3"),
    )
end

function main()
    spec_hash = sha256_file(SPEC_PATH)
    spec_hash == EXPECTED_SPEC_SHA256 || error("frozen amended spec hash mismatch: $spec_hash")
    spec = JSON3.read(read(SPEC_PATH, String))
    preregistration = JSON3.read(read(PREREG_PATH, String))
    Bool(preregistration["all_pass"]) || error("preregistration is red")
    String(preregistration["spec_sha256"]) == spec_hash || error("preregistration does not bind amended spec")
    String(spec["spec_status"]) == "frozen_before_execution_amendment_1" || error("unexpected spec freeze status")
    Int(spec["execution_bounds"]["internal_path_horizon"]) == HORIZON || error("horizon drift")

    runtime = runtime_receipt()
    Bool(runtime["canonical_carrier_direct_check"]) || error("strict canonical carrier runtime check failed")
    registry, candidate_counts = build_registry()
    append_chain = append_chain_receipt()
    external_gates = external_gate_receipt()
    entropy_readouts = entropy_capacity_receipt(registry)
    mss_results = all_mss_arms(registry, spec)
    controls = controls_receipt(registry, candidate_counts, append_chain, external_gates, entropy_readouts)

    all_graphs_parity = all(candidate["graphs_cycle_receipt"] === nothing || candidate["graphs_cycle_receipt"]["package_independent_parity"] for candidate in registry)
    exact_pass = candidate_counts["registry_identity_unique"] &&
        all_graphs_parity &&
        append_chain["all_pass"] &&
        external_gates["all_pass"] &&
        entropy_readouts["all_pass"] &&
        all(receipt["pass"] for receipt in values(controls))

    source_hash = sha256_file(SOURCE_PATH)
    result = Dict{String,Any}(
        "schema_version" => "finite_structure_hypothesis_tournament.julia_result.v1",
        "all_pass" => false,
        "scientific_checks_before_closed_json" => exact_pass,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => String(spec["claim_ceiling"]),
        "blocked_consumers" => String.(collect(spec["blocked_consumers"])),
        "command" => [
            "env",
            "JULIA_LOAD_PATH=@:@stdlib",
            "/opt/homebrew/bin/julia",
            "--startup-file=no",
            "--project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier",
            "system_v7/sims/finite_structure_hypothesis_tournament_v1/run_julia.jl",
        ],
        "cwd" => pwd(),
        "runner_identity" => Dict(
            "engine" => "julia",
            "executable" => "/opt/homebrew/bin/julia",
            "semantic_role" => "exact finite carrier and Graphs SCC viability owner",
            "reads_peer_result" => false,
        ),
        "runtime" => runtime,
        "source_path" => relpath(SOURCE_PATH, REPO_ROOT),
        "result_path" => relpath(RESULT_PATH, REPO_ROOT),
        "source_sha256" => source_hash,
        "spec_path" => relpath(SPEC_PATH, REPO_ROOT),
        "spec_sha256" => spec_hash,
        "preregistration_path" => relpath(PREREG_PATH, REPO_ROOT),
        "preregistration_sha256" => sha256_file(PREREG_PATH),
        "input_provenance" => Dict(
            "spec_read_directly" => true,
            "preregistration_green" => true,
            "peer_result_files_read" => String[],
            "random_seeds" => Int[],
        ),
        "engine_contract" => Dict(
            "mode" => "julia_canon_jax_workhorse_smt_crossover",
            "lane" => "julia",
            "pytorch" => "not_scoped_by_mode",
            "ratchet_epochs_run" => 0,
            "search_steps_run" => 0,
        ),
        "packages_used" => ["Graphs", "JSON3", "SHA", "Pkg"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "tool_receipts" => tool_receipts(),
        "preflight_notes" => Dict(
            "worktree_runtime_doctor" => Dict(
                "status" => "red_preserved_non_claim_path",
                "finding" => "the doctor selected the isolated worktree's uninstantiated Julia carrier and reported modules missing",
                "action" => "no install and no carrier mutation; executed only under the explicitly frozen canonical main carrier",
            ),
            "canonical_carrier_direct_functional_check" => Dict(
                "status" => "green",
                "project" => Base.active_project(),
                "Graphs_version" => runtime["packages"]["Graphs"],
                "JSON3_version" => runtime["packages"]["JSON3"],
            ),
        ),
        "candidate_counts" => candidate_counts,
        "candidates" => [output_candidate(candidate) for candidate in registry],
        "mss_arms" => mss_results,
        "fixed_carrier_internal_append_chain" => append_chain,
        "external_constraint_controls" => external_gates,
        "entropy_capacity_readouts" => entropy_readouts,
        "controls" => controls,
        "clock_separation" => Dict(
            "candidate_internal" => "installed_only_for_transition_relation_and_markov_kernel",
            "frozen_search" => "not_installed",
            "ratchet_context" => "not_run",
        ),
        "logic_scope" => Dict(
            "generation" => ["carrier_size", "semantic_type", "adjacency", "exact_kernel", "named_constants"],
            "selection" => ["declared_preorder", "declared_viability", "mutual_preorder_quotient"],
            "downstream_target_tokens_used_by_generation_or_selection" => String[],
        ),
        "closed_json_validation" => Dict("passed" => false),
    )

    tentative = JSON3.read(JSON3.write(result))
    required_fields = String.(collect(spec["required_result_fields"]))
    closed_ok = all(field -> haskey(tentative, field), required_fields) &&
        String(tentative["source_sha256"]) == source_hash &&
        String(tentative["spec_sha256"]) == spec_hash &&
        !Bool(tentative["all_pass"])
    result["closed_json_validation"] = Dict("passed" => closed_ok, "required_fields" => required_fields)
    result["all_pass"] = exact_pass && closed_ok
    result["result_core_sha256"] = sha256_text(JSON3.write(result))
    final_json = JSON3.write(result)
    final = JSON3.read(final_json)
    final_ok = Bool(final["all_pass"]) == Bool(result["all_pass"]) && Bool(final["closed_json_validation"]["passed"]) && String(final["spec_sha256"]) == EXPECTED_SPEC_SHA256
    final_ok || error("final closed JSON validation failed")

    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        write(io, final_json)
        write(io, "\n")
    end
    println(JSON3.write(Dict(
        "engine" => "julia",
        "all_pass" => result["all_pass"],
        "candidate_count" => candidate_counts["total_registry_candidates"],
        "spec_sha256" => spec_hash,
        "source_sha256" => source_hash,
        "result_path" => RESULT_PATH,
    )))
end

main()
