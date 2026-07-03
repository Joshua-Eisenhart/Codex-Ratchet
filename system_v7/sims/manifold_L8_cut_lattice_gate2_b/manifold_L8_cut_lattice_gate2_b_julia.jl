#!/usr/bin/env julia
# Gate 2 Builder B: Julia leg for the L8 cut lattice over the Gate 1 roster.

using Dates
using JSON
using LinearAlgebra
using SHA

const SIM_ID = "manifold_L8_cut_lattice_gate2_b"
const HERE = @__DIR__
const RESULTS = joinpath(HERE, "results")
const GATE1 = abspath(joinpath(HERE, "..", "ratchet_formal_gates_v1", "results", "ratchet_formal_gates_v1_numpy_results.json"))
const OUT = joinpath(RESULTS, SIM_ID * "_julia_results.json")
const N = 3
const TOL = 1e-9
const ROUND_FULL = 12

const I2 = ComplexF64[1 0; 0 1]
const X = ComplexF64[0 1; 1 0]
const Y = ComplexF64[0 -im; im 0]
const Z = ComplexF64[1 0; 0 -1]
const PAULI = Dict('I'=>I2, 'X'=>X, 'Y'=>Y, 'Z'=>Z)

roundn(x, d) = round(Float64(real(x)); digits=d)

function sha_obj(obj)
    bytes2hex(sha256(JSON.json(obj)))
end

function pauli_matrix(label::AbstractString)
    out = ComplexF64[1;;]
    for ch in collect(label)
        out = kron(out, PAULI[ch])
    end
    out
end

function pauli_strings(width::Int)
    out = String[]
    function rec(prefix::String, depth::Int)
        if depth == width
            if prefix != repeat("I", width)
                push!(out, prefix)
            end
            return
        end
        for ch in ("I", "X", "Y", "Z")
            rec(prefix * ch, depth + 1)
        end
    end
    rec("", 0)
    out
end

function reduced_full_pauli_signature(rho::Matrix{ComplexF64}; digits::Int=ROUND_FULL)
    width = Int(round(log2(size(rho, 1))))
    values = Float64[]
    for label in pauli_strings(width)
        value = round(Float64(real(tr(rho * pauli_matrix(label)))); digits=digits)
        push!(values, abs(value) <= 10.0^(-digits) ? 0.0 : value)
    end
    values
end

single_pauli_signature_from_density(rho::Matrix{ComplexF64}, label::String) = [Int(round(Float64(real(tr(rho * pauli_matrix(label))))))]

label_echo_accepts(pair) = get(pair, "parent_label", nothing) == get(pair, "claimed_marginal_parent_label", nothing)

function density_from_pvec(pvec, labels)
    dim = 2^N
    rho = Matrix{ComplexF64}(I, dim, dim)
    for (coeff, label) in zip(pvec, labels)
        rho .+= Float64(coeff) .* pauli_matrix(String(label))
    end
    rho ./= dim
    (rho + rho') ./ 2
end

function combinations_vec(xs::Vector{Int}, r::Int)
    out = Vector{Vector{Int}}()
    function rec(start::Int, cur::Vector{Int})
        if length(cur) == r
            push!(out, copy(cur))
            return
        end
        for i in start:length(xs)
            push!(cur, xs[i])
            rec(i + 1, cur)
            pop!(cur)
        end
    end
    rec(1, Int[])
    out
end

function cuts(n::Int)
    [[party] for party in 0:n-1]
end

function all_nonempty_subsets(axes::Vector{Int})
    out = Vector{Vector{Int}}()
    for r in 1:length(axes)
        append!(out, combinations_vec(axes, r))
    end
    out
end

bits_of(x::Int, len::Int) = [((x >> (len - 1 - p)) & 1) for p in 0:len-1]

function compose_index(n::Int, axes_a::Vector{Int}, avals::Vector{Int}, axes_b::Vector{Int}, bvals::Vector{Int})
    idx = 0
    for (axis, bit) in zip(axes_a, avals)
        idx |= bit << (n - 1 - axis)
    end
    for (axis, bit) in zip(axes_b, bvals)
        idx |= bit << (n - 1 - axis)
    end
    idx
end

function partial_trace(rho::Matrix{ComplexF64}, n::Int, keep::Vector{Int})
    traced = [axis for axis in 0:n-1 if !(axis in keep)]
    d_keep = 2^length(keep)
    d_trace = 2^length(traced)
    out = zeros(ComplexF64, d_keep, d_keep)
    for ar in 0:d_keep-1
        ar_bits = bits_of(ar, length(keep))
        for ac in 0:d_keep-1
            ac_bits = bits_of(ac, length(keep))
            acc = 0.0 + 0.0im
            for bt in 0:d_trace-1
                b_bits = bits_of(bt, length(traced))
                row = compose_index(n, keep, ar_bits, traced, b_bits)
                col = compose_index(n, keep, ac_bits, traced, b_bits)
                acc += rho[row + 1, col + 1]
            end
            out[ar + 1, ac + 1] = acc
        end
    end
    (out + out') ./ 2
end

function partial_transpose_matrix(rho::Matrix{ComplexF64}, n::Int, axes_a::Vector{Int})
    axes_b = [axis for axis in 0:n-1 if !(axis in axes_a)]
    d_a = 2^length(axes_a)
    d_b = 2^length(axes_b)
    mat = zeros(ComplexF64, d_a * d_b, d_a * d_b)
    for ar in 0:d_a-1, br in 0:d_b-1, ac in 0:d_a-1, bc in 0:d_b-1
        ar_bits = bits_of(ar, length(axes_a))
        br_bits = bits_of(br, length(axes_b))
        ac_bits = bits_of(ac, length(axes_a))
        bc_bits = bits_of(bc, length(axes_b))
        row = ar * d_b + br
        col = ac * d_b + bc
        src_r = compose_index(n, axes_a, ar_bits, axes_b, br_bits)
        src_c = compose_index(n, axes_a, ac_bits, axes_b, bc_bits)
        mat[row + 1, col + 1] = rho[src_r + 1, src_c + 1]
    end
    pt = zeros(ComplexF64, d_a * d_b, d_a * d_b)
    for ar in 0:d_a-1, br in 0:d_b-1, ac in 0:d_a-1, bc in 0:d_b-1
        pt[ar * d_b + br + 1, ac * d_b + bc + 1] = mat[ac * d_b + br + 1, ar * d_b + bc + 1]
    end
    (pt + pt') ./ 2
end

function negativity(rho::Matrix{ComplexF64}, n::Int, axes_a::Vector{Int})
    ev = eigvals(Hermitian(partial_transpose_matrix(rho, n, axes_a)))
    sum(abs.(filter(x -> x < -TOL, real.(ev))))
end

rank_from_eigs(rho::Matrix{ComplexF64}) = count(x -> x > TOL, eigvals(Hermitian(rho)))

function entropy_bits(rho::Matrix{ComplexF64})
    ev = filter(x -> x > TOL, real.(eigvals(Hermitian(rho))))
    isempty(ev) ? 0.0 : Float64(-sum(ev .* log2.(ev)))
end

function matrix_payload(mat::Matrix{ComplexF64}; digits::Int=12)
    [[[round(Float64(real(z)); digits=digits), round(Float64(imag(z)); digits=digits)] for z in row] for row in eachrow(mat)]
end

matrix_hash(mat::Matrix{ComplexF64}) = sha_obj(matrix_payload(mat))

function basis_state(n::Int, index::Int)
    v = zeros(ComplexF64, 2^n)
    v[index + 1] = 1.0
    v
end

pure_density(psi::Vector{ComplexF64}) = psi * psi'
ghz_state(n::Int) = (basis_state(n, 0) + basis_state(n, 2^n - 1)) ./ sqrt(2)

function w_state(n::Int)
    v = zeros(ComplexF64, 2^n)
    for axis in 0:n-1
        v[(1 << (n - 1 - axis)) + 1] = 1 / sqrt(n)
    end
    v
end

function bell_high_axes_then_zero(n::Int)
    v = zeros(ComplexF64, 2^n)
    v[1] = 1 / sqrt(2)
    v[((1 << (n - 1)) | (1 << (n - 2))) + 1] = 1 / sqrt(2)
    v
end

cut_key(cut::Vector{Int}) = join(string.(cut), "|") * "__" * join([string(x) for x in 0:N-1 if !(x in cut)], "|")

function cut_side_records(cut::Vector{Int})
    right = [axis for axis in 0:N-1 if !(axis in cut)]
    [("left", copy(cut)), ("right", right)]
end

function sorted_label_key(labels)
    join(sort(String.(labels)), "\u001f")
end

function projection_from_grouped_labels(grouped; cached_classes=nothing)
    projection = Dict{String,Int}()
    sorted_groups = sort([sort(labels) for labels in values(grouped)], by=x -> (length(x), join(x, "\u001f")))
    for (idx, labels) in enumerate(sorted_groups)
        class_id = cached_classes === nothing ? idx - 1 : get(cached_classes, join(labels, "\u001f"), idx - 1)
        for label in labels
            projection[label] = Int(class_id)
        end
    end
    projection
end

function recompute_full_projection(carrier_states, gate, pauli_labels)
    grouped = Dict{String,Vector{String}}()
    fresh_grouped = Dict{String,Vector{String}}()
    for state in carrier_states
        key = join([string(round(Float64(x); digits=ROUND_FULL)) for x in state["pvec"]], ",")
        if !haskey(grouped, key)
            grouped[key] = String[]
        end
        push!(grouped[key], String(state["label"]))
        rho = density_from_pvec(state["pvec"], pauli_labels)
        fresh_key = JSON.json(reduced_full_pauli_signature(rho))
        if !haskey(fresh_grouped, fresh_key)
            fresh_grouped[fresh_key] = String[]
        end
        push!(fresh_grouped[fresh_key], String(state["label"]))
    end
    cached = Dict{String,Int}()
    for c in gate["classes"]
        cached[sorted_label_key(c["labels"])] = Int(c["class_id"])
    end
    pvec_projection = projection_from_grouped_labels(grouped; cached_classes=cached)
    fresh = projection_from_grouped_labels(fresh_grouped; cached_classes=cached)
    cached_projection = Dict(String(k)=>Int(v) for (k, v) in gate["projection"])
    corrupted_cached_projection = copy(cached_projection)
    first_label = sort(collect(keys(corrupted_cached_projection)))[1]
    corrupted_cached_projection[first_label] = corrupted_cached_projection[first_label] + 999
    Dict(
        "epoch_id"=>gate["probe_epoch_id"],
        "fresh_class_count"=>length(grouped),
        "cached_class_count"=>Int(gate["quotient_class_count"]),
        "fresh_projection_matches_cached"=>fresh == cached_projection,
        "pvec_projection_matches_cached"=>pvec_projection == cached_projection,
        "independent_density_projection_matches_pvec"=>fresh == pvec_projection,
        "mutation_self_test"=>Dict(
            "corrupted_cached_projection_compare_failed"=>corrupted_cached_projection != fresh,
            "restored_cached_projection_compare_pass"=>cached_projection == fresh,
        ),
        "singleton_classes"=>all(length(v) == 1 for v in values(grouped)),
    )
end

function recompute_coarse_projection(carrier_states, pauli_labels, epoch_id::String, pauli_label::String; cached_gate=nothing)
    pauli_index = findfirst(==(pauli_label), pauli_labels)
    grouped = Dict{Int,Vector{String}}()
    fresh_grouped = Dict{String,Vector{String}}()
    for state in carrier_states
        key = Int(round(Float64(state["pvec"][pauli_index])))
        if !haskey(grouped, key)
            grouped[key] = String[]
        end
        push!(grouped[key], String(state["label"]))
        rho = density_from_pvec(state["pvec"], pauli_labels)
        fresh_key = JSON.json(single_pauli_signature_from_density(rho, pauli_label))
        if !haskey(fresh_grouped, fresh_key)
            fresh_grouped[fresh_key] = String[]
        end
        push!(fresh_grouped[fresh_key], String(state["label"]))
    end
    cached = nothing
    if cached_gate !== nothing
        cached = Dict{String,Int}()
        for c in cached_gate["classes"]
            cached[sorted_label_key(c["labels"])] = Int(c["class_id"])
        end
    end
    pvec_projection = projection_from_grouped_labels(grouped; cached_classes=cached)
    fresh = projection_from_grouped_labels(fresh_grouped; cached_classes=cached)
    cached_projection = cached_gate === nothing ? projection_from_grouped_labels(grouped) : Dict(String(k)=>Int(v) for (k, v) in cached_gate["projection"])
    corrupted_cached_projection = copy(cached_projection)
    first_label = sort(collect(keys(corrupted_cached_projection)))[1]
    corrupted_cached_projection[first_label] = corrupted_cached_projection[first_label] + 999
    Dict(
        "epoch_id"=>epoch_id,
        "pauli_label"=>pauli_label,
        "fresh_class_count"=>length(grouped),
        "cached_class_count"=>cached_gate === nothing ? length(grouped) : Int(cached_gate["quotient_class_count"]),
        "fresh_projection_matches_cached"=>fresh == cached_projection,
        "pvec_projection_matches_cached"=>pvec_projection == cached_projection,
        "independent_density_projection_matches_pvec"=>fresh == pvec_projection,
        "mutation_self_test"=>Dict(
            "corrupted_cached_projection_compare_failed"=>corrupted_cached_projection != fresh,
            "restored_cached_projection_compare_pass"=>cached_projection == fresh,
        ),
        "fresh_group_sizes"=>sort([length(v) for v in values(grouped)]),
        "cached_group_sizes"=>cached_gate === nothing ? sort([length(v) for v in values(grouped)]) : sort([Int(c["size"]) for c in cached_gate["classes"]]),
    )
end

function main()
    mkpath(RESULTS)
    gate1 = JSON.parsefile(GATE1)
    carrier_states = gate1["carrier_states"]
    pauli_labels = String.(gate1["carrier_summary"]["pauli_strings"])
    zii_index = findfirst(==("ZII"), pauli_labels)
    cut_list = cuts(N)
    expected_cut_count = 2^(N - 1) - 1
    ordered_subset_count = 2^N - 2

    rosters = Vector{Dict{String,Any}}()
    for state in carrier_states
        rho = density_from_pvec(state["pvec"], pauli_labels)
        push!(rosters, Dict(
            "label"=>String(state["label"]),
            "family"=>String(state["family"]),
            "quotient_class"=>Int(state["quotient_class"]),
            "rho"=>rho,
        ))
    end
    roster_by_label = Dict(item["label"]=>item for item in rosters)

    per_state_cut = Vector{Dict{String,Any}}()
    roster_negativities = Float64[]
    for item in rosters
        for cut in cut_list
            neg = negativity(item["rho"], N, cut)
            push!(roster_negativities, neg)
            for (side, side_subset) in cut_side_records(cut)
                marginal = partial_trace(item["rho"], N, side_subset)
                eigsig = [round(Float64(x); digits=12) for x in sort(real.(eigvals(Hermitian(marginal))), rev=true)]
                push!(per_state_cut, Dict(
                    "label"=>item["label"],
                    "quotient_class"=>item["quotient_class"],
                    "cut"=>cut,
                    "cut_label"=>cut_key(cut),
                    "side"=>side,
                    "side_subset"=>side_subset,
                    "marginal_trace"=>round(Float64(real(tr(marginal))); digits=12),
                    "marginal_rank"=>rank_from_eigs(marginal),
                    "marginal_entropy_bits"=>round(entropy_bits(marginal); digits=12),
                    "marginal_eigenvalue_signature"=>eigsig,
                    "parent_negativity"=>round(neg; digits=12),
                    "marginal_hash"=>matrix_hash(marginal),
                    "computed_by"=>"explicit_partial_trace",
                ))
            end
        end
    end

    schmidt_strata_by_cut = Dict{String,Any}()
    for cut in cut_list
        ck = cut_key(cut)
        schmidt_strata_by_cut[ck] = Dict{String,Any}()
        for (side, _side_subset) in cut_side_records(cut)
            buckets = Dict{String,Vector{String}}()
            for row in per_state_cut
                if row["cut_label"] == ck && row["side"] == side
                    key = JSON.json(row["marginal_eigenvalue_signature"])
                    if !haskey(buckets, key)
                        buckets[key] = String[]
                    end
                    push!(buckets[key], row["label"])
                end
            end
            schmidt_strata_by_cut[ck][side] = [
                Dict(
                    "size"=>length(sort(members)),
                    "representative"=>sort(members)[1],
                    "labels_sample"=>sort(members)[1:min(5, length(members))],
                    "eigenvalue_signature"=>signature,
                )
                for (signature, members) in sort(collect(buckets), by=x -> (length(x[2]), join(sort(x[2]), "\u001f")))
            ]
        end
    end

    subset_classes = Dict{String,Any}()
    for subset in all_nonempty_subsets(collect(0:N-1))
        signatures = Dict{String,Vector{String}}()
        matrix_signatures = Dict{String,Vector{String}}()
        for item in rosters
            marginal = partial_trace(item["rho"], N, subset)
            key = JSON.json(reduced_full_pauli_signature(marginal))
            if !haskey(signatures, key)
                signatures[key] = String[]
            end
            push!(signatures[key], item["label"])
            matrix_key = matrix_hash(marginal)
            if !haskey(matrix_signatures, matrix_key)
                matrix_signatures[matrix_key] = String[]
            end
            push!(matrix_signatures[matrix_key], item["label"])
        end
        subset_classes[string(subset)] = Dict(
            "subset"=>subset,
            "quotient_basis"=>"reduced_full_pauli_expectation_tuple",
            "quotient_class_count"=>length(signatures),
            "class_sizes"=>sort([length(v) for v in values(signatures)]),
            "diagnostic_matrix_hash_object"=>Dict(
                "basis"=>"rounded_reduced_density_matrix_payload_hash",
                "class_count"=>length(matrix_signatures),
                "class_sizes"=>sort([length(v) for v in values(matrix_signatures)]),
            ),
        )
    end

    extension_fibers = Vector{Dict{String,Any}}()
    for parent in all_nonempty_subsets(collect(0:N-1))
        for sub in all_nonempty_subsets(parent)
            sub_local = [findfirst(==(x), parent) - 1 for x in sub]
            for item in rosters
                rho_parent = partial_trace(item["rho"], N, parent)
                rho_sub_via_parent = partial_trace(rho_parent, length(parent), sub_local)
                rho_sub_direct = partial_trace(item["rho"], N, sub)
                compatible = norm(rho_sub_via_parent - rho_sub_direct) <= TOL
                push!(extension_fibers, Dict(
                    "parent_label"=>item["label"],
                    "A"=>parent,
                    "B_subset_A"=>sub,
                    "compatible_by_computed_trace"=>compatible,
                ))
            end
        end
    end

    product = pure_density(basis_state(N, 0))
    ghz = pure_density(ghz_state(N))
    w = pure_density(w_state(N))
    bell = pure_density(bell_high_axes_then_zero(N))
    product_neg = [negativity(product, N, cut) for cut in cut_list]
    ghz_neg = [negativity(ghz, N, cut) for cut in cut_list]
    w_neg = [negativity(w, N, cut) for cut in cut_list]
    bell_neg = [negativity(bell, N, cut) for cut in cut_list]

    true_parent = rosters[1]
    inconsistent_parent = rosters[2]
    seam_cut = cut_list[1]
    true_marginal = partial_trace(true_parent["rho"], N, seam_cut)
    inconsistent_marginal = partial_trace(inconsistent_parent["rho"], N, seam_cut)
    computed_distance = Float64(norm(true_marginal - inconsistent_marginal))
    label_echo_pair = Dict(
        "parent_label"=>true_parent["label"],
        "claimed_marginal_parent_label"=>true_parent["label"],
        "actual_marginal_source_label"=>inconsistent_parent["label"],
    )
    label_echo_admits = label_echo_accepts(label_echo_pair)
    perturbed = copy(true_marginal)
    perturbed[1, 1] += 0.01
    perturbed[end, end] -= 0.01
    perturbed_distance = Float64(norm(true_marginal - perturbed))

    lineage_parent = [0, 1]
    lineage_child = [0]
    lineage_row = Dict(
        "parent_label"=>true_parent["label"],
        "gate1_quotient_class"=>Int(true_parent["quotient_class"]),
        "parent_subset"=>lineage_parent,
        "child_subset"=>lineage_child,
        "parent_rho"=>partial_trace(true_parent["rho"], N, lineage_parent),
        "child_rho"=>partial_trace(true_parent["rho"], N, lineage_child),
    )
    removed_lineage_row = copy(lineage_row)
    removed_lineage_row["parent_label"] = nothing

    function lineage_nesting_check(row)
        label = get(row, "parent_label", nothing)
        if !(label isa String) || !haskey(roster_by_label, label)
            return false
        end
        if get(row, "gate1_quotient_class", nothing) != Int(roster_by_label[label]["quotient_class"])
            return false
        end
        parent_subset = row["parent_subset"]
        child_subset = row["child_subset"]
        if !all(q -> q in parent_subset, child_subset)
            return false
        end
        local_child = [findfirst(==(axis), parent_subset) - 1 for axis in child_subset]
        traced = partial_trace(row["parent_rho"], length(parent_subset), local_child)
        return norm(traced - row["child_rho"]) <= TOL
    end
    with_lineage_passes = lineage_nesting_check(lineage_row)
    removed_lineage_passes = lineage_nesting_check(removed_lineage_row)

    full_epoch = gate1["gates"]["observable_quotient_R4"]
    coarse_epoch = gate1["gates"]["coarse_probe_quotient_R4_epoch"]
    full_reprojection = recompute_full_projection(carrier_states, full_epoch, pauli_labels)
    coarse_reprojection = recompute_coarse_projection(carrier_states, pauli_labels, "M_coarse_single_qubit_Z", "ZII"; cached_gate=coarse_epoch)
    coarse_xii_reprojection = recompute_coarse_projection(carrier_states, pauli_labels, "M_coarse_single_qubit_X", "XII")
    epoch_mutation_self_tests = [
        merge(Dict("epoch"=>"M_full_pauli_63"), full_reprojection["mutation_self_test"]),
        merge(Dict("epoch"=>"M_coarse_single_qubit_Z"), coarse_reprojection["mutation_self_test"]),
        merge(Dict("epoch"=>"M_coarse_single_qubit_X"), coarse_xii_reprojection["mutation_self_test"]),
    ]
    epoch_mutation_self_tests_pass = all(
        Bool(row["corrupted_cached_projection_compare_failed"]) && Bool(row["restored_cached_projection_compare_pass"])
        for row in epoch_mutation_self_tests
    )

    coarse_spreads = Vector{Dict{String,Any}}()
    for klass in coarse_epoch["classes"]
        labels = String.(klass["labels"])
        for cut in cut_list
            hashes = String[]
            for label in labels
                row = only(filter(x -> x["label"] == label && x["cut"] == cut && x["side"] == "left", per_state_cut))
                push!(hashes, row["marginal_hash"])
            end
            push!(coarse_spreads, Dict(
                "coarse_class"=>Int(klass["class_id"]),
                "cut"=>cut,
                "representative_marginal_hash_count"=>length(Set(hashes)),
                "representative_independent"=>length(Set(hashes)) == 1,
            ))
        end
    end
    coarse_rep_independence_failed = any(!x["representative_independent"] for x in coarse_spreads)

    controls = Dict(
        "product_negativity_zero"=>Dict("pass"=>maximum(product_neg) <= TOL, "values"=>[round(x; digits=12) for x in product_neg]),
        "entangled_control_nonzero"=>Dict(
            "pass"=>maximum(ghz_neg) > 0.1,
            "ghz_values"=>[round(x; digits=12) for x in ghz_neg],
            "roster_max_negativity"=>round(maximum(roster_negativities); digits=12),
            "roster_has_nonzero_negativity"=>maximum(roster_negativities) > TOL,
        ),
        "perturbed_marginal_fails"=>Dict("pass"=>perturbed_distance > TOL, "distance_from_true"=>perturbed_distance),
        "alternate_probe_family_changes_quotient"=>Dict(
            "pass"=>Int(full_epoch["quotient_class_count"]) != Int(coarse_epoch["quotient_class_count"]),
            "full_class_count"=>Int(full_epoch["quotient_class_count"]),
            "coarse_class_count"=>Int(coarse_epoch["quotient_class_count"]),
        ),
        "lineage_removed_rejected"=>Dict(
            "pass"=>with_lineage_passes && !removed_lineage_passes,
            "with_lineage_passes"=>with_lineage_passes,
            "removed_lineage_passes"=>removed_lineage_passes,
            "mutation_self_test"=>"removed parent_label from a consumed Gate-1 state; the same ancestry+nested-trace checker rejected it",
            "parent_label"=>true_parent["label"],
            "parent_subset"=>lineage_parent,
            "child_subset"=>lineage_child,
        ),
        "cut_lattice_control_divergence"=>Dict(
            "pass"=>product_neg != ghz_neg && ghz_neg != w_neg,
            "control_observable"=>"entanglement_negativity",
            "spec_pin"=>"GATE2_SPEC_EXTRACTION_20260703.md wave-1 disambiguation: W-state control observable is entanglement negativity",
            "product_negativities"=>[round(x; digits=12) for x in product_neg],
            "ghz_negativities"=>[round(x; digits=12) for x in ghz_neg],
            "w_negativities"=>[round(x; digits=12) for x in w_neg],
            "bell_negativities"=>[round(x; digits=12) for x in bell_neg],
        ),
        "label_echo_negative_control"=>Dict(
            "parent_label"=>true_parent["label"],
            "claimed_marginal_parent_label"=>true_parent["label"],
            "actual_marginal_source_label"=>inconsistent_parent["label"],
            "cut"=>seam_cut,
            "cached_label_comparator"=>"parent_label == claimed_marginal_parent_label",
            "cached_label_comparator_admits"=>label_echo_admits,
            "label_echo_would_pass"=>label_echo_admits,
            "computed_trace_distance"=>computed_distance,
            "computed_trace_rejects"=>computed_distance > TOL,
            "pass"=>label_echo_admits && computed_distance > TOL,
        ),
        "coarse_epoch_not_full_proof"=>Dict(
            "pass"=>coarse_rep_independence_failed,
            "representative_independence_failed"=>coarse_rep_independence_failed,
            "coarse_status"=>"control_only_demoted_not_full_quotient_proof",
        ),
    )

    cut_formula = Dict(
        "chosen_formula"=>"2^(n-1)-1",
        "n"=>N,
        "expected_count"=>expected_cut_count,
        "enumerated_count"=>length(cut_list),
        "assertion_pass"=>length(cut_list) == expected_cut_count,
        "ordered_nontrivial_subset_count_rejected"=>ordered_subset_count,
        "why"=>"Contract L8 says bipartitions and pins 3Q:3; ordered non-trivial party subsets would give 6 and is not the contract count.",
        "cuts_party_indexed"=>cut_list,
        "quotient_acts_on"=>"states_only",
        "cut_labels_quotiented"=>false,
    )

    negative_passes = [Bool(v["pass"]) for v in values(controls)]
    extension_all = all(Bool(x["compatible_by_computed_trace"]) for x in extension_fibers)
    all_pass = Bool(cut_formula["assertion_pass"]) &&
        all(negative_passes) &&
        Bool(full_reprojection["fresh_projection_matches_cached"]) &&
        Bool(coarse_reprojection["fresh_projection_matches_cached"]) &&
        Bool(coarse_xii_reprojection["fresh_projection_matches_cached"]) &&
        epoch_mutation_self_tests_pass &&
        extension_all

    result = Dict(
        "schema"=>"codex_ratchet.manifold_L8_cut_lattice_gate2_b.julia_result.v1",
        "sim_id"=>SIM_ID,
        "generated_at"=>Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "julia"=>Dict(
            "ran"=>true,
            "source_path"=>"system_v7/sims/manifold_L8_cut_lattice_gate2_b/manifold_L8_cut_lattice_gate2_b_julia.jl",
            "packages_used"=>["JSON", "LinearAlgebra", "SHA"],
            "aligned_packages_load_bearing"=>["LinearAlgebra"],
            "reads_peer_result"=>false,
            "active_project"=>Base.active_project(),
        ),
        "classification"=>"scratch_diagnostic",
        "promotion_allowed"=>false,
        "formal_admission_allowed"=>false,
        "claim_ceiling"=>"L8 cut-lattice builder diagnostic over the finite Gate 1 roster; no L9/L10 bundle, no LU-equivalence, no admission claim.",
        "gate1_input"=>"system_v7/sims/ratchet_formal_gates_v1/results/ratchet_formal_gates_v1_numpy_results.json",
        "cut_formula"=>cut_formula,
        "open_choice_followed"=>Dict("bundle_L9_L10"=>"OPEN-CHOICE followed: not bundled", "coarse_epoch_role"=>"control-only"),
        "enumeration"=>Dict(
            "sampling"=>false,
            "full_enumeration"=>true,
            "state_count"=>length(rosters),
            "cut_count"=>length(cut_list),
            "state_cut_pair_count"=>length(rosters) * length(cut_list),
            "per_cut_side_marginal_records"=>length(per_state_cut),
            "extension_compatibility_checks"=>length(extension_fibers),
            "extension_compatibility_all_pass"=>extension_all,
            "finite_roster_only"=>true,
            "lu_equivalence_used"=>false,
        ),
        "epoch_reprojection"=>Dict(
            "full_pauli"=>full_reprojection,
            "coarse_zii"=>coarse_reprojection,
            "coarse_xii"=>coarse_xii_reprojection,
            "epoch_family"=>["M_full_pauli_63", "M_coarse_single_qubit_Z", "M_coarse_single_qubit_X"],
            "fresh_recompute_compare_pass"=>Bool(full_reprojection["fresh_projection_matches_cached"]) && Bool(coarse_reprojection["fresh_projection_matches_cached"]) && Bool(coarse_xii_reprojection["fresh_projection_matches_cached"]),
            "mutation_self_tests_pass"=>epoch_mutation_self_tests_pass,
            "mutation_self_tests"=>epoch_mutation_self_tests,
            "representative_lookup_used_for_marginals"=>false,
        ),
        "subset_quotient_summaries"=>subset_classes,
        "per_state_cut_marginals"=>per_state_cut,
        "schmidt_strata_by_cut"=>schmidt_strata_by_cut,
        "coarse_representative_marginal_spreads"=>coarse_spreads,
        "extension_fibers_summary"=>Dict(
            "compatibility_edge_records"=>length(extension_fibers),
            "fiber_sizes_by_subset"=>Dict(subset=>row["class_sizes"] for (subset, row) in subset_classes),
            "all_computed_compatible"=>extension_all,
        ),
        "continuity_trap_guard"=>Dict(
            "finite_roster_only"=>true,
            "local_unitary_equivalence_used"=>false,
            "fresh_recompute_compare_pass"=>Bool(full_reprojection["fresh_projection_matches_cached"]) && Bool(coarse_reprojection["fresh_projection_matches_cached"]) && Bool(coarse_xii_reprojection["fresh_projection_matches_cached"]),
            "mutation_self_tests_pass"=>epoch_mutation_self_tests_pass,
            "pass"=>Bool(full_reprojection["fresh_projection_matches_cached"]) && Bool(coarse_reprojection["fresh_projection_matches_cached"]) && Bool(coarse_xii_reprojection["fresh_projection_matches_cached"]) && epoch_mutation_self_tests_pass,
        ),
        "negative_controls"=>controls,
        "summary"=>Dict(
            "all_pass"=>all_pass,
            "max_roster_negativity"=>round(maximum(roster_negativities); digits=12),
            "controls_passed"=>count(identity, negative_passes),
            "controls_total"=>length(negative_passes),
        ),
        "TOOL_MANIFEST"=>Dict(
            "julia"=>Dict("used"=>true, "reason"=>"load-bearing independent finite density matrices, partial traces, eigenspectra, negativity controls"),
            "json"=>Dict("used"=>true, "reason"=>"load-bearing consumption of Gate 1 result roster"),
        ),
        "TOOL_INTEGRATION_DEPTH"=>Dict("julia"=>"load_bearing", "json"=>"load_bearing"),
    )
    open(OUT, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("WROTE ", OUT)
    println(JSON.json(result["summary"]))
end

main()
