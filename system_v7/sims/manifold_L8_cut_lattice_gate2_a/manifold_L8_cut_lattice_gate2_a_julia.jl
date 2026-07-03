#!/usr/bin/env julia
# Gate 2 L8 cut lattice builder A, Julia parity leg.
#
# Ceiling: scratch_diagnostic; promotion_allowed=false.

using Dates
using JSON
using LinearAlgebra
using SHA

const SIM_ID = "manifold_L8_cut_lattice_gate2_a"
const HERE = @__DIR__
const REPO = abspath(joinpath(HERE, "..", "..", ".."))
const RESULTS = joinpath(HERE, "results")
const GATE1_RESULT = joinpath(REPO, "system_v7", "sims", "ratchet_formal_gates_v1", "results", "ratchet_formal_gates_v1_numpy_results.json")
const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false

const TOOL_MANIFEST = Dict(
    "Julia LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent density reconstruction, partial trace, finite cut spectra, and negativity calculations"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Gate 1 result JSON consumption and Julia result emission"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive result/source digesting")
)
const TOOL_INTEGRATION_DEPTH = Dict(
    "Julia LinearAlgebra" => "load_bearing",
    "JSON" => "load_bearing",
    "SHA" => "supportive"
)

const I2 = Matrix{ComplexF64}(I, 2, 2)
const PAULI = Dict(
    'I' => I2,
    'X' => ComplexF64[0 1; 1 0],
    'Y' => ComplexF64[0 -im; im 0],
    'Z' => ComplexF64[1 0; 0 -1],
)
const NQ = 3

function sha256_file(path::String)
    return bytes2hex(sha256(read(path)))
end

function now_iso()
    return Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
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
        for c in ("I", "X", "Y", "Z")
            rec(prefix * c, depth + 1)
        end
    end
    rec("", 0)
    return out
end

const STRINGS = pauli_strings(NQ)

function kron_label(label::String)
    mat = PAULI[label[1]]
    for i in 2:length(label)
        mat = kron(mat, PAULI[label[i]])
    end
    return mat
end

const PMATS = Dict(s => kron_label(s) for s in STRINGS)

function canonical_rho(rho)
    out = 0.5 .* (rho .+ rho')
    out ./= real(tr(out))
    out[abs.(out) .< 1e-14] .= 0
    return out
end

function rho_from_pvec(pv)
    rho = Matrix{ComplexF64}(I, 8, 8)
    for (idx, label) in enumerate(STRINGS)
        rho .+= Float64(pv[idx]) .* PMATS[label]
    end
    return canonical_rho(rho ./ 8.0)
end

function bits(index0::Int, n::Int=NQ)
    return Tuple((index0 >> (n - i)) & 1 for i in 1:n)
end

function index_from_bits(vals)
    out = 0
    for value in vals
        out = (out << 1) | Int(value)
    end
    return out
end

function partial_trace(rho, keep::Vector{Int})
    n = Int(round(log2(size(rho, 1))))
    drop = [i for i in 0:(n - 1) if !(i in keep)]
    dim = 2 ^ length(keep)
    out = zeros(ComplexF64, dim, dim)
    for row0 in 0:(2^n - 1)
        rb = bits(row0, n)
        rout = index_from_bits(Tuple(rb[i + 1] for i in keep)) + 1
        for col0 in 0:(2^n - 1)
            cb = bits(col0, n)
            if all(rb[i + 1] == cb[i + 1] for i in drop)
                cout = index_from_bits(Tuple(cb[i + 1] for i in keep)) + 1
                out[rout, cout] += rho[row0 + 1, col0 + 1]
            end
        end
    end
    return canonical_rho(out)
end

function subsystem_pvec(rho, width::Int)
    [real(tr(rho * kron_label(label))) for label in pauli_strings(width)]
end

function single_probe_signature_from_marginal(rho_sub, subset::Vector{Int}, target_qubit::Int, observable::String)
    local_index = findfirst(==(target_qubit), subset)
    if local_index === nothing
        return Float64[]
    end
    label = repeat("I", local_index - 1) * observable * repeat("I", length(subset) - local_index)
    return [round(Float64(real(tr(rho_sub * kron_label(label)))); digits=0)]
end

label_echo_accepts(pair) = get(pair, "parent_label", nothing) == get(pair, "claimed_marginal_parent_label", nothing)

function rounded_key(values; digits=12)
    out = Float64[]
    for v in values
        rv = round(Float64(v), digits=digits)
        push!(out, abs(rv) < 1e-12 ? 0.0 : rv)
    end
    return out
end

function eig_signature(rho; digits=12)
    vals = eigvals(Hermitian(0.5 .* (rho .+ rho')))
    vals = sort([clamp(real(v), 0.0, 1.0) for v in vals], rev=true)
    return [round(v, digits=digits) for v in vals]
end

function entropy_bits(rho)
    vals = eigvals(Hermitian(0.5 .* (rho .+ rho')))
    total = 0.0
    for v in vals
        vv = clamp(real(v), 0.0, 1.0)
        if vv > 1e-14
            total -= vv * log2(vv)
        end
    end
    return total
end

function partial_transpose_party(rho, party::Int)
    out = zeros(ComplexF64, 8, 8)
    for row0 in 0:7
        rb = collect(bits(row0))
        for col0 in 0:7
            cb = collect(bits(col0))
            rb2 = copy(rb)
            cb2 = copy(cb)
            rb2[party + 1], cb2[party + 1] = cb2[party + 1], rb2[party + 1]
            out[index_from_bits(Tuple(rb2)) + 1, index_from_bits(Tuple(cb2)) + 1] = rho[row0 + 1, col0 + 1]
        end
    end
    return 0.5 .* (out .+ out')
end

function negativity_for_cut(rho, party::Int)
    vals = eigvals(Hermitian(partial_transpose_party(rho, party)))
    return max(0.0, (sum(abs(real(v)) for v in vals) - 1.0) / 2.0)
end

function all_nonempty_subsets()
    return [[i for i in 0:(NQ - 1) if ((mask >> i) & 1) == 1] for mask in 1:(2^NQ - 1)]
end

function enumerate_l8_cuts()
    cuts = []
    for party in 0:(NQ - 1)
        right = [i for i in 0:(NQ - 1) if i != party]
        push!(cuts, Dict(
            "cut_id" => "q$(party)__q$(join(string.(right), ""))",
            "left" => [party],
            "right" => right,
            "party_indexed" => true,
            "unordered_bipartition" => true
        ))
    end
    expected = 2^(NQ - 1) - 1
    if length(cuts) != expected
        error("L8 unordered cut count mismatch")
    end
    return cuts
end

function quotient_class_count(signatures::Dict{String, Vector{Float64}})
    buckets = Dict{String, Vector{String}}()
    for (label, sig) in signatures
        key = JSON.json(sig)
        if !haskey(buckets, key)
            buckets[key] = String[]
        end
        push!(buckets[key], label)
    end
    return length(keys(buckets))
end

function quotient_class_sizes(signatures::Dict{String, Vector{Float64}})
    buckets = Dict{String, Vector{String}}()
    for (label, sig) in signatures
        key = JSON.json(sig)
        if !haskey(buckets, key)
            buckets[key] = String[]
        end
        push!(buckets[key], label)
    end
    return sort([length(v) for v in values(buckets)])
end

function strata_records(strata::Dict{String, Vector{String}})
    rows = []
    for (signature, members) in sort(collect(strata), by=x -> (length(x[2]), sort(x[2])[1]))
        sorted_members = sort(members)
        push!(rows, Dict(
            "size" => length(sorted_members),
            "representative" => sorted_members[1],
            "labels_sample" => sorted_members[1:min(5, length(sorted_members))],
            "eigenvalue_signature" => signature
        ))
    end
    return rows
end

function control_state(kind::String)
    vec = zeros(ComplexF64, 8)
    if kind == "product_000"
        vec[1] = 1.0
    elseif kind == "ghz"
        vec[1] = 1 / sqrt(2)
        vec[8] = 1 / sqrt(2)
    elseif kind == "w"
        vec[2] = 1 / sqrt(3)
        vec[3] = 1 / sqrt(3)
        vec[5] = 1 / sqrt(3)
    else
        error(kind)
    end
    return vec * vec'
end

function main()
    mkpath(RESULTS)
    gate1 = JSON.parsefile(GATE1_RESULT)
    spec = JSON.parsefile(joinpath(HERE, "spec.json"))
    projection = gate1["gates"]["observable_quotient_R4"]["projection"]
    states = []
    for row in gate1["carrier_states"]
        push!(states, Dict(
            "label" => row["label"],
            "family" => row["family"],
            "quotient_class" => Int(projection[row["label"]]),
            "rho" => rho_from_pvec(row["pvec"]),
            "pvec" => [Float64(v) for v in row["pvec"]]
        ))
    end
    labels = [s["label"] for s in states]
    state_by_label = Dict(s["label"] => s for s in states)
    cuts = enumerate_l8_cuts()
    subsets = all_nonempty_subsets()

    marginal_cache = Dict{Tuple{String, String}, Matrix{ComplexF64}}()
    marginal_signatures = Dict{String, Dict{String, Vector{Float64}}}()
    for subset in subsets
        marginal_signatures[JSON.json(subset)] = Dict{String, Vector{Float64}}()
    end
    for state in states
        for subset in subsets
            rho_sub = partial_trace(state["rho"], subset)
            marginal_cache[(state["label"], JSON.json(subset))] = rho_sub
            marginal_signatures[JSON.json(subset)][state["label"]] = rounded_key(subsystem_pvec(rho_sub, length(subset)))
        end
    end

    compatibility_checks = 0
    compatibility_failures = 0
    for state in states
        for parent in subsets
            parent_rho = marginal_cache[(state["label"], JSON.json(parent))]
            local_count = length(parent)
            for mask in 1:(2^local_count - 1)
                child = [parent[i] for i in 1:local_count if ((mask >> (i - 1)) & 1) == 1]
                local_keep = [findfirst(==(q), parent) - 1 for q in child]
                traced = partial_trace(parent_rho, local_keep)
                expected = marginal_cache[(state["label"], JSON.json(child))]
                compatibility_checks += 1
                if maximum(abs.(traced .- expected)) > 1e-10
                    compatibility_failures += 1
                end
            end
        end
    end

    cut_summaries = []
    roster_negativities = []
    for cut in cuts
        party = cut["left"][1]
        left = cut["left"]
        right = cut["right"]
        left_strata = Dict{String, Vector{String}}()
        right_strata = Dict{String, Vector{String}}()
        negs = Float64[]
        for state in states
            rho_left = marginal_cache[(state["label"], JSON.json(left))]
            rho_right = marginal_cache[(state["label"], JSON.json(right))]
            left_key = JSON.json(eig_signature(rho_left))
            right_key = JSON.json(eig_signature(rho_right))
            if !haskey(left_strata, left_key)
                left_strata[left_key] = String[]
            end
            if !haskey(right_strata, right_key)
                right_strata[right_key] = String[]
            end
            push!(left_strata[left_key], state["label"])
            push!(right_strata[right_key], state["label"])
            neg = negativity_for_cut(state["rho"], party)
            push!(negs, neg)
            push!(roster_negativities, Dict("label" => state["label"], "cut_id" => cut["cut_id"], "negativity" => neg))
        end
        push!(cut_summaries, merge(cut, Dict(
            "state_count" => length(states),
            "left_marginal_count" => length(states),
            "right_marginal_count" => length(states),
            "left_stratum_count" => length(keys(left_strata)),
            "right_stratum_count" => length(keys(right_strata)),
            "left_schmidt_strata" => strata_records(left_strata),
            "right_schmidt_strata" => strata_records(right_strata),
            "negativity_min" => minimum(negs),
            "negativity_max" => maximum(negs),
            "entropy_readout_families_declared" => ["S_A", "S_AB", "I_A_rest"],
            "schmidt_strata_basis" => "finite density-roster cut marginal eigenvalue signatures; not local-unitary equivalence"
        )))
    end

    extension_fibers = Dict{String, Any}()
    for subset in subsets
        key = JSON.json(subset)
        extension_fibers[key] = Dict(
            "subset" => subset,
            "fiber_count" => length(quotient_class_sizes(marginal_signatures[key])),
            "fiber_sizes" => quotient_class_sizes(marginal_signatures[key])
        )
    end

    full_signatures = Dict(s["label"] => rounded_key(s["pvec"]) for s in states)
    full_class_count = quotient_class_count(full_signatures)
    zii_idx = findfirst(==("ZII"), STRINGS)
    xii_idx = findfirst(==("XII"), STRINGS)
    coarse_signatures = Dict(s["label"] => rounded_key([s["pvec"][zii_idx]], digits=0) for s in states)
    coarse_x_signatures = Dict(s["label"] => rounded_key([s["pvec"][xii_idx]], digits=0) for s in states)
    coarse_class_count = quotient_class_count(coarse_signatures)
    coarse_x_class_count = quotient_class_count(coarse_x_signatures)

    epoch_cache_mismatches = []
    coarse_epoch_defs = [
        Dict("epoch_id" => "M_coarse_single_qubit_Z", "target_qubit" => 0, "observable" => "Z"),
        Dict("epoch_id" => "M_coarse_single_qubit_X", "target_qubit" => 0, "observable" => "X"),
    ]
    coarse_epoch_cached_signatures = Dict{Tuple{String, String, String}, Vector{Float64}}()
    for state in states
        for subset in subsets
            subset_key = JSON.json(subset)
            cached_full = marginal_signatures[subset_key][state["label"]]
            fresh_rho = rho_from_pvec(state["pvec"])
            fresh_full = rounded_key(subsystem_pvec(partial_trace(fresh_rho, subset), length(subset)))
            if cached_full != fresh_full
                push!(epoch_cache_mismatches, Dict("epoch" => "M_full_pauli_63", "label" => state["label"], "subset" => subset))
            end
            for epoch_def in coarse_epoch_defs
                cached_marginal = marginal_cache[(state["label"], subset_key)]
                coarse_cached = single_probe_signature_from_marginal(cached_marginal, subset, Int(epoch_def["target_qubit"]), String(epoch_def["observable"]))
                coarse_fresh = single_probe_signature_from_marginal(partial_trace(fresh_rho, subset), subset, Int(epoch_def["target_qubit"]), String(epoch_def["observable"]))
                coarse_epoch_cached_signatures[(state["label"], subset_key, String(epoch_def["epoch_id"]))] = coarse_cached
                if coarse_cached != coarse_fresh
                    push!(epoch_cache_mismatches, Dict("epoch" => epoch_def["epoch_id"], "label" => state["label"], "subset" => subset))
                end
            end
        end
    end

    epoch_mutation_self_tests = []
    mutation_state = states[1]
    mutation_subset = [0]
    mutation_subset_key = JSON.json(mutation_subset)
    original_full = marginal_signatures[mutation_subset_key][mutation_state["label"]]
    fresh_full = rounded_key(subsystem_pvec(partial_trace(rho_from_pvec(mutation_state["pvec"]), mutation_subset), length(mutation_subset)))
    corrupted_full = [v + 1.0 for v in original_full]
    push!(epoch_mutation_self_tests, Dict(
        "epoch" => "M_full_pauli_63",
        "label" => mutation_state["label"],
        "subset" => mutation_subset,
        "corrupted_compare_failed" => corrupted_full != fresh_full,
        "restored_compare_pass" => original_full == fresh_full,
    ))
    for epoch_def in coarse_epoch_defs
        original = coarse_epoch_cached_signatures[(mutation_state["label"], mutation_subset_key, String(epoch_def["epoch_id"]))]
        fresh = single_probe_signature_from_marginal(partial_trace(rho_from_pvec(mutation_state["pvec"]), mutation_subset), mutation_subset, Int(epoch_def["target_qubit"]), String(epoch_def["observable"]))
        corrupted = [v + 1.0 for v in original]
        push!(epoch_mutation_self_tests, Dict(
            "epoch" => epoch_def["epoch_id"],
            "label" => mutation_state["label"],
            "subset" => mutation_subset,
            "corrupted_compare_failed" => corrupted != fresh,
            "restored_compare_pass" => original == fresh,
        ))
    end
    epoch_mutation_self_test_pass = all(Bool(row["corrupted_compare_failed"]) && Bool(row["restored_compare_pass"]) for row in epoch_mutation_self_tests)

    product_negs = [negativity_for_cut(control_state("product_000"), cut["left"][1]) for cut in cuts]
    ghz_negs = [negativity_for_cut(control_state("ghz"), cut["left"][1]) for cut in cuts]
    w_negs = [negativity_for_cut(control_state("w"), cut["left"][1]) for cut in cuts]
    max_roster = roster_negativities[argmax([r["negativity"] for r in roster_negativities])]

    parent = states[1]
    bad_source = first(s for s in states[2:end] if maximum(abs.(marginal_cache[(s["label"], JSON.json([0]))] - marginal_cache[(parent["label"], JSON.json([0]))])) > 1e-10)
    label_echo_pair = Dict(
        "parent_label" => parent["label"],
        "claimed_marginal_parent_label" => parent["label"],
        "actual_marginal_source_label" => bad_source["label"],
    )
    label_echo_admits = label_echo_accepts(label_echo_pair)
    computed_trace_distance = Float64(norm(marginal_cache[(parent["label"], JSON.json([0]))] - marginal_cache[(bad_source["label"], JSON.json([0]))]))
    computed_trace_rejects = computed_trace_distance > 1e-10

    lineage_parent = [0, 1]
    lineage_child = [0]
    lineage_row = Dict(
        "parent_label" => parent["label"],
        "gate1_quotient_class" => Int(projection[parent["label"]]),
        "parent_subset" => lineage_parent,
        "child_subset" => lineage_child,
        "parent_rho" => marginal_cache[(parent["label"], JSON.json(lineage_parent))],
        "child_rho" => marginal_cache[(parent["label"], JSON.json(lineage_child))],
    )
    removed_lineage_row = copy(lineage_row)
    removed_lineage_row["parent_label"] = nothing

    function lineage_nesting_check(row)
        label = get(row, "parent_label", nothing)
        if !(label isa String) || !haskey(state_by_label, label)
            return false
        end
        if get(row, "gate1_quotient_class", nothing) != Int(projection[label])
            return false
        end
        parent_subset = row["parent_subset"]
        child_subset = row["child_subset"]
        if !all(q -> q in parent_subset, child_subset)
            return false
        end
        local_child = [findfirst(==(q), parent_subset) - 1 for q in child_subset]
        traced = partial_trace(row["parent_rho"], local_child)
        return maximum(abs.(traced - row["child_rho"])) <= 1e-10
    end
    with_lineage_passes = lineage_nesting_check(lineage_row)
    removed_lineage_passes = lineage_nesting_check(removed_lineage_row)

    controls = Dict(
        "product_separable_zero_negativity" => Dict("pass" => all(abs.(product_negs) .<= 1e-12), "values_by_cut" => product_negs),
        "entangled_finite_roster_nonzero_negativity" => Dict("pass" => max_roster["negativity"] > 1e-9, "label" => max_roster["label"], "cut_id" => max_roster["cut_id"], "negativity" => max_roster["negativity"]),
        "alternate_probe_family_changes_quotient" => Dict("pass" => full_class_count != coarse_class_count, "full_class_count" => full_class_count, "coarse_z_class_count" => coarse_class_count),
        "lineage_removed_rejected" => Dict(
            "pass" => with_lineage_passes && !removed_lineage_passes,
            "with_lineage_passes" => with_lineage_passes,
            "removed_lineage_passes" => removed_lineage_passes,
            "mutation_self_test" => "removed parent_label from a consumed Gate-1 state; the same ancestry+nested-trace checker rejected it",
            "parent_label" => parent["label"],
            "parent_subset" => lineage_parent,
            "child_subset" => lineage_child,
        ),
        "cut_lattice_control_divergence" => Dict(
            "pass" => product_negs != ghz_negs && ghz_negs != w_negs,
            "control_observable" => "entanglement_negativity",
            "spec_pin" => "GATE2_SPEC_EXTRACTION_20260703.md wave-1 disambiguation: W-state control observable is entanglement negativity",
            "product_negativities" => product_negs,
            "ghz_negativities" => ghz_negs,
            "w_negativities" => w_negs
        ),
        "label_echo_negative_control" => Dict(
            "pass" => label_echo_admits && computed_trace_rejects,
            "parent_label" => parent["label"],
            "inconsistent_marginal_source_label" => bad_source["label"],
            "cached_label_comparator" => "parent_label == claimed_marginal_parent_label",
            "cached_label_comparator_admits" => label_echo_admits,
            "computed_trace_distance" => computed_trace_distance,
            "computed_partial_trace_rejects" => computed_trace_rejects,
        ),
        "coarse_epoch_lift_not_promoted" => Dict("pass" => gate1["gates"]["xi_ref_quotient_lift"]["gate_pass"] == false, "gate1_status" => gate1["gates"]["xi_ref_quotient_lift"]["status"])
    )

    failures = String[]
    if length(cuts) != spec["cut_count_resolution"]["expected_cut_count"]
        push!(failures, "cut count formula did not match enumeration")
    end
    if compatibility_failures != 0
        push!(failures, "compatibility partial-trace law failed")
    end
    if !isempty(epoch_cache_mismatches)
        push!(failures, "epoch cache recompute mismatch")
    end
    if !epoch_mutation_self_test_pass
        push!(failures, "epoch cache mutation self-test did not fail closed")
    end
    for (name, row) in controls
        if row["pass"] != true
            push!(failures, "negative/control failed: $(name)")
        end
    end

    result = Dict(
        "schema" => "codex_ratchet.manifold_L8_cut_lattice_gate2_a.julia.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "source_path" => abspath(@__FILE__),
        "source_sha256" => sha256_file(abspath(@__FILE__)),
        "written_at" => now_iso(),
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "QUARANTINE_EXPLORATORY" => true,
        "scratch_diagnostic" => true,
        "claim_ceiling" => spec["claim_ceiling"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "reads_peer_result" => false,
        "input_gate1" => Dict(
            "path" => GATE1_RESULT,
            "sha256" => sha256_file(GATE1_RESULT),
            "global_all_pass" => gate1["all_pass"],
            "observable_quotient_R4_gate_pass" => gate1["gates"]["observable_quotient_R4"]["gate_pass"],
            "xi_ref_gate_pass" => gate1["gates"]["xi_ref_quotient_lift"]["gate_pass"],
            "gate1_reaudit_for_consumed_roster_clear" => gate1["gates"]["observable_quotient_R4"]["gate_pass"],
            "gate1_global_clear" => gate1["all_pass"]
        ),
        "cut_count_resolution" => merge(spec["cut_count_resolution"], Dict("actual_cut_count" => length(cuts), "asserted_against_enumeration" => length(cuts) == 3)),
        "open_choice_followed" => spec["owner_tunable_bundling_choice"],
        "enumeration_counts" => Dict(
            "finite_gate1_roster_states" => length(states),
            "gate1_full_quotient_classes_consumed" => gate1["gates"]["observable_quotient_R4"]["quotient_class_count"],
            "full_recomputed_quotient_classes" => full_class_count,
            "coarse_z_recomputed_quotient_classes" => coarse_class_count,
            "coarse_x_recomputed_quotient_classes" => coarse_x_class_count,
            "cut_count_unordered_bipartitions" => length(cuts),
            "nonempty_subset_lattice_nodes" => length(subsets),
            "per_cut_side_marginal_records" => length(states) * length(cuts) * 2,
            "compatibility_checks" => compatibility_checks,
            "extension_fiber_nodes" => length(extension_fibers),
            "extension_fiber_size_records" => sum(length(row["fiber_sizes"]) for row in values(extension_fibers))
        ),
        "cuts" => cut_summaries,
        "compatibility" => Dict("checks" => compatibility_checks, "failure_count" => compatibility_failures),
        "extension_fibers" => extension_fibers,
        "epoch_reprojection" => Dict(
            "epochs" => ["M_full_pauli_63", "M_coarse_single_qubit_Z", "M_coarse_single_qubit_X"],
            "full_class_count_matches_gate1" => full_class_count == gate1["gates"]["observable_quotient_R4"]["quotient_class_count"],
            "coarse_z_class_count" => coarse_class_count,
            "coarse_x_class_count" => coarse_x_class_count,
            "fresh_recompute_and_compare" => isempty(epoch_cache_mismatches),
            "mutation_self_tests_pass" => epoch_mutation_self_test_pass,
            "mutation_self_tests" => epoch_mutation_self_tests,
            "cache_mismatch_count" => length(epoch_cache_mismatches),
            "cache_mismatches" => epoch_cache_mismatches[1:min(10, length(epoch_cache_mismatches))]
        ),
        "negative_controls" => controls,
        "continuity_trap_guard" => Dict(
            "finite_roster_only" => true,
            "local_unitary_equivalence_used" => false,
            "max_stratum_representative_pool" => length(states),
            "fresh_recompute_and_compare" => isempty(epoch_cache_mismatches),
            "mutation_self_tests_pass" => epoch_mutation_self_test_pass,
            "pass" => isempty(epoch_cache_mismatches) && epoch_mutation_self_test_pass,
        ),
        "all_pass" => isempty(failures),
        "failures" => failures
    )
    out = joinpath(RESULTS, "$(SIM_ID)_julia_results.json")
    open(out, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict(
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "all_pass" => result["all_pass"],
        "cut_count" => length(cuts),
        "finite_roster_states" => length(states),
        "compatibility_checks" => compatibility_checks,
        "result_path" => out
    )))
    return isempty(failures) ? 0 : 1
end

exit(main())
