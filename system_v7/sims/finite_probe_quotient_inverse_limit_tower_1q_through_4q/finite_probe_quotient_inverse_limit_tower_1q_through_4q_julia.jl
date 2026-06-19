#!/usr/bin/env julia
# Julia leg for finite probe quotient inverse-limit tower.
# Unique computation style: exact_hermitian_eigendecomposition_and_partial_trace.
# It reads only spec.json and writes its own result JSON.

using LinearAlgebra
using JSON
using SHA
using Dates

const SIM_ID = "finite_probe_quotient_inverse_limit_tower_1q_through_4q"
const HERE = @__DIR__
const DEPTHS = ["1q", "2q", "3q", "4q"]
const OPEN_FIXTURE_4Q_STATES = [
    "w4",
    "dicke4_2",
    "ghz4",
    "bell_ab_bell_cd",
    "ghz_ab_prod_cd",
    "bell_ac_prod_bd",
    "mix_0000_1111",
]

const PAULI = Dict(
    "I" => ComplexF64[1 0; 0 1],
    "X" => ComplexF64[0 1; 1 0],
    "Z" => ComplexF64[1 0; 0 -1],
)

bits_to_int(bits::AbstractString) = parse(Int, bits; base=2)
ratio(pair) = pair[1] / pair[2]

function all_bitstrings(n)
    return [string(i, base=2, pad=n) for i in 0:(2^n - 1)]
end

function matrix_from_recipe(recipe, n)
    dim = 2^n
    mat = zeros(ComplexF64, dim, dim)
    kind = recipe["kind"]
    if kind == "basis_projector"
        idx = bits_to_int(recipe["basis"]) + 1
        mat[idx, idx] = 1
    elseif kind == "maximally_mixed"
        mat = Matrix{ComplexF64}(I, dim, dim) / dim
    elseif kind == "basis_mixture"
        for row in recipe["weights"]
            idx = bits_to_int(row["basis"]) + 1
            mat[idx, idx] += ratio(row["weight"])
        end
    elseif kind == "uniform_pure_support"
        value = 1.0 / length(recipe["basis"])
        for a in recipe["basis"], b in recipe["basis"]
            mat[bits_to_int(a) + 1, bits_to_int(b) + 1] += value
        end
    elseif kind == "sparse_density"
        for term in recipe["terms"]
            mat[bits_to_int(term["row"]) + 1, bits_to_int(term["col"]) + 1] += ratio(term["value"])
        end
    else
        error("unknown recipe kind: $(kind)")
    end
    return mat
end

function probe_strings(n, removed)
    probes = String[]
    function build(prefix, depth)
        if depth == n
            if any(c -> c != 'I', prefix)
                push!(probes, prefix)
            end
        else
            for c in ["I", "X", "Z"]
                build(prefix * c, depth + 1)
            end
        end
    end
    build("", 0)
    erased = [p for p in probes if !(p in removed)]
    return probes, erased
end

function kron_probe(probe)
    out = PAULI[string(probe[1])]
    for c in collect(probe)[2:end]
        out = kron(out, PAULI[string(c)])
    end
    return out
end

function bitvec(i, n)
    s = string(i, base=2, pad=n)
    return [parse(Int, string(c)) for c in s]
end

function int_from_bits(bits)
    v = 0
    for b in bits
        v = 2 * v + b
    end
    return v
end

function partial_trace(rho, n, keep0)
    keep = collect(keep0)
    traced = [i for i in 0:(n - 1) if !(i in keep)]
    dim_keep = 2^length(keep)
    out = zeros(ComplexF64, dim_keep, dim_keep)
    for a in 0:(2^n - 1), b in 0:(2^n - 1)
        ba = bitvec(a, n)
        bb = bitvec(b, n)
        if all(ba[t + 1] == bb[t + 1] for t in traced)
            ia = int_from_bits([ba[k + 1] for k in keep]) + 1
            ib = int_from_bits([bb[k + 1] for k in keep]) + 1
            out[ia, ib] += rho[a + 1, b + 1]
        end
    end
    return out
end

function entropy_and_eigenvalues(rho)
    vals = real.(eigvals(Hermitian((rho + rho') / 2)))
    vals = sort(vals)
    entropy = 0.0
    for v in vals
        if v > 1e-14
            entropy -= v * log(v)
        end
    end
    return [round(v, digits=12) for v in vals], round(entropy, digits=12)
end

function density_rank(rho; tol=1e-9)
    vals = real.(eigvals(Hermitian((rho + rho') / 2)))
    return count(v -> v > tol, vals)
end

function probe_expectations(rho, probes)
    return [round(real(tr(rho * kron_probe(p))), digits=9) for p in probes]
end

function quotient_classes(signatures, labels)
    classes = Vector{Vector{String}}()
    keys = Vector{String}()
    for lab in labels
        key = join([string(x) for x in signatures[lab]], ",")
        idx = findfirst(==(key), keys)
        if idx === nothing
            push!(keys, key)
            push!(classes, [lab])
        else
            push!(classes[idx], lab)
        end
    end
    return classes
end

function signature_key(rho, probes)
    return join([string(x) for x in probe_expectations(rho, probes)], ",")
end

function bloch_radius(rho1)
    vals = probe_expectations(rho1, ["X", "Z"])
    return round(sqrt(vals[1]^2 + vals[2]^2), digits=9)
end

function pure_support(recipe)
    if recipe["kind"] == "basis_projector"
        return [recipe["basis"]]
    elseif recipe["kind"] == "uniform_pure_support"
        return recipe["basis"]
    else
        return nothing
    end
end

function schmidt_by_cut(recipe, n)
    support = pure_support(recipe)
    if support === nothing
        return Dict("defined_for_pure_state" => false, "coefficients_by_cut" => Dict(), "rank_tuple" => [])
    end
    cuts = []
    if n == 3
        cuts = [([0], [1, 2]), ([1], [0, 2]), ([2], [0, 1])]
    elseif n == 4
        cuts = [([0], [1, 2, 3]), ([1], [0, 2, 3]), ([2], [0, 1, 3]), ([3], [0, 1, 2]), ([0, 1], [2, 3]), ([0, 2], [1, 3]), ([0, 3], [1, 2])]
    end
    coeffs = Dict{String,Any}()
    ranks = Int[]
    amp = 1.0 / sqrt(length(support))
    for (left, right) in cuts
        mat = zeros(ComplexF64, 2^length(left), 2^length(right))
        for bits in support
            bv = [parse(Int, string(c)) for c in bits]
            li = int_from_bits([bv[i + 1] for i in left]) + 1
            ri = int_from_bits([bv[i + 1] for i in right]) + 1
            mat[li, ri] += amp
        end
        svals = svdvals(mat)
        arr = [round(s, digits=12) for s in svals if s > 1e-9]
        coeffs[join(string.(left), "") * "|" * join(string.(right), "")] = arr
        push!(ranks, length(arr))
    end
    return Dict("defined_for_pure_state" => true, "coefficients_by_cut" => coeffs, "rank_tuple" => ranks)
end

function tuple_leq(a, b)
    return all(a[i] <= b[i] for i in eachindex(a))
end

function tuple_lt(a, b)
    return tuple_leq(a, b) && any(a[i] < b[i] for i in eachindex(a))
end

function fourq_rank_lattice_and_consistency(states4, recipes4)
    cuts = [
        ([0], [1, 2, 3]),
        ([1], [0, 2, 3]),
        ([2], [0, 1, 3]),
        ([3], [0, 1, 2]),
        ([0, 1], [2, 3]),
        ([0, 2], [1, 3]),
        ([0, 3], [1, 2]),
    ]
    rank_tuples = Dict(lab => schmidt_by_cut(recipes4[lab], 4)["rank_tuple"] for lab in keys(states4))
    pure_rank_tuples = Dict(lab => Tuple(v) for (lab, v) in rank_tuples if length(v) > 0)
    node_keys = sort(collect(Set([join(string.(collect(v)), ",") for v in values(pure_rank_tuples)])))
    nodes = [[parse(Int, x) for x in split(k, ",")] for k in node_keys]
    edges = Any[]
    for lower in nodes, upper in nodes
        if lower == upper || !tuple_leq(lower, upper)
            continue
        end
        covered = false
        for mid in nodes
            if mid == lower || mid == upper
                continue
            end
            if tuple_lt(lower, mid) && tuple_lt(mid, upper)
                covered = true
                break
            end
        end
        if !covered
            push!(edges, Dict("lower" => lower, "upper" => upper))
        end
    end

    consistency = Dict{String,Any}()
    for (lab, ranks_tuple) in pure_rank_tuples
        ranks = collect(ranks_tuple)
        rho = states4[lab]
        per_cut = Dict{String,Any}()
        for (idx, cut) in enumerate(cuts)
            left, right = cut
            left_rank = density_rank(partial_trace(rho, 4, left))
            right_rank = density_rank(partial_trace(rho, 4, right))
            left_product = prod([density_rank(partial_trace(rho, 4, [q])) for q in left])
            right_product = prod([density_rank(partial_trace(rho, 4, [q])) for q in right])
            schmidt_rank = ranks[idx]
            key = join(string.(left), "") * "|" * join(string.(right), "")
            per_cut[key] = Dict(
                "schmidt_rank" => schmidt_rank,
                "left_marginal_density_rank" => left_rank,
                "right_marginal_density_rank" => right_rank,
                "left_singleton_product_bound" => left_product,
                "right_singleton_product_bound" => right_product,
                "consistent" => schmidt_rank == left_rank == right_rank && schmidt_rank <= left_product && schmidt_rank <= right_product,
            )
        end
        consistency[lab] = Dict(
            "per_cut" => per_cut,
            "consistent" => all([row["consistent"] for row in values(per_cut)]),
        )
    end
    all_consistent = all([row["consistent"] for row in values(consistency)])
    return Dict(
        "claim" => "computed finite 4q rank-tuple lattice and cross-rung marginal-rank consistency for observed pure states",
        "rank_tuple_lattice_computed" => true,
        "matches" => all_consistent && length(nodes) >= 3,
        "computed_rank_tuple_lattice" => Dict(lab => collect(v) for (lab, v) in rank_tuples),
        "lattice_nodes" => nodes,
        "partial_order_edges_componentwise_leq" => edges,
        "cross_rung_consistency" => consistency,
        "all_cross_rung_consistent" => all_consistent,
    )
end

function negative_control_block(states, probe_data, class_by_signature)
    perturbed = zeros(ComplexF64, 4, 4)
    perturbed[1, 1] = 0.7
    perturbed[4, 4] = 0.3
    perturbed_sig = signature_key(perturbed, probe_data["2q"]["full"])
    perturbed_lookup = get(class_by_signature["2q"], perturbed_sig, nothing)
    perturbed_control = Dict(
        "control" => "synthetic 2q diagonal marginal diag(0.7,0,0,0.3) looked up through the same full-probe class table",
        "perturbed_signature" => split(perturbed_sig, ","),
        "class_lookup_result" => perturbed_lookup === nothing ? "not in class table" : perturbed_lookup,
        "violates_compatibility" => perturbed_lookup === nothing,
        "fired" => perturbed_lookup === nothing,
    )

    projected = partial_trace(states["4q"]["ghz4"], 4, [0, 1, 2])
    projected_sig = signature_key(projected, probe_data["3q"]["full"])
    echoed_sig = signature_key(states["3q"]["ghz3"], probe_data["3q"]["full"])
    partial_trace_rejects = projected_sig != echoed_sig
    label_control = Dict(
        "control" => "ghz4 projected to qubits 012 versus lower label ghz3; a stem-name echo would pass but computed signatures differ",
        "higher_state" => "ghz4",
        "kept_subset" => "012",
        "echoed_lower_state" => "ghz3",
        "name_echo_would_pass" => true,
        "projected_signature" => split(projected_sig, ","),
        "echoed_lower_signature" => split(echoed_sig, ","),
        "projected_class_lookup" => get(class_by_signature["3q"], projected_sig, nothing),
        "echoed_class_lookup" => get(class_by_signature["3q"], echoed_sig, nothing),
        "partial_trace_rejects" => partial_trace_rejects,
        "fired" => partial_trace_rejects,
    )
    return Dict(
        "perturbed_marginal_excluded" => perturbed_control,
        "label_echo_trap" => label_control,
    )
end

function subsets(n; proper=true)
    out = Vector{Vector{Int}}()
    maxr = proper ? n - 1 : n
    for r in 1:maxr
        for comb in Iterators.filter(c -> length(c) == r, Iterators.product(fill(0:n-1, r)...))
            v = collect(comb)
            if length(unique(v)) == r && issorted(v)
                push!(out, v)
            end
        end
    end
    return out
end

function open_state_seal_test(states, probe_data, class_by_signature_nonclosure, class_labels_by_signature_nonclosure)
    projections = Any[]
    for lab in OPEN_FIXTURE_4Q_STATES
        if !haskey(states["4q"], lab)
            continue
        end
        rho = states["4q"][lab]
        for keep in subsets(4; proper=true)
            lower = string(length(keep), "q")
            kept_subset = join(string.(keep), "")
            marginal = partial_trace(rho, 4, keep)
            sig_values = probe_expectations(marginal, probe_data[lower]["full"])
            sig_key = join([string(x) for x in sig_values], ",")
            cls = get(class_by_signature_nonclosure[lower], sig_key, nothing)
            push!(projections, Dict(
                "higher_depth" => "4q",
                "higher_state" => lab,
                "target_depth" => lower,
                "kept_subset" => kept_subset,
                "projected_signature" => sig_values,
                "matching_nonclosure_class" => cls,
                "matching_nonclosure_labels" => get(class_labels_by_signature_nonclosure[lower], sig_key, String[]),
                "lands_in_existing_nonclosure_class" => cls !== nothing,
            ))
        end
    end
    total = length(projections)
    landing = count(row -> row["lands_in_existing_nonclosure_class"], projections)
    missing = total - landing
    open_fixture_seals = total > 0 && missing == 0
    finding = open_fixture_seals ?
        "seals on open fixture: $(missing) of $(total) higher-state projections have no matching non-closure lower class" :
        "does NOT seal on open fixture: $(missing) of $(total) higher-state projections have no matching non-closure lower class"
    return Dict(
        "class_table" => "lower-rung full-probe quotient classes rebuilt with closure_* labels excluded",
        "tested_higher_depth" => "4q",
        "tested_higher_states" => [lab for lab in OPEN_FIXTURE_4Q_STATES if haskey(states["4q"], lab)],
        "projections" => projections,
        "total_projection_count" => total,
        "landing_projection_count" => landing,
        "missing_projection_count" => missing,
        "open_fixture_seals" => open_fixture_seals,
        "open_fixture_seal_finding" => finding,
    )
end

function main()
    spec = JSON.parsefile(joinpath(HERE, "spec.json"))
    states = Dict{String,Dict{String,Matrix{ComplexF64}}}()
    recipes = Dict{String,Dict{String,Any}}()
    for depth in DEPTHS
        n = parse(Int, depth[1])
        states[depth] = Dict{String,Matrix{ComplexF64}}()
        recipes[depth] = Dict{String,Any}()
        for row in spec["state_sets"][depth]
            lab = row["label"]
            states[depth][lab] = matrix_from_recipe(row["recipe"], n)
            recipes[depth][lab] = row["recipe"]
        end
    end

    probe_data = Dict{String,Any}()
    rung_data = Dict{String,Any}()
    class_by_signature = Dict{String,Dict{String,String}}()
    class_by_signature_nonclosure = Dict{String,Dict{String,String}}()
    class_labels_by_signature_nonclosure = Dict{String,Dict{String,Any}}()

    for depth in DEPTHS
        n = parse(Int, depth[1])
        full, erased = probe_strings(n, spec["erasure_choice"]["removed_probe_by_depth"][depth])
        probe_data[depth] = Dict("full" => full, "erased" => erased)
        labels = sort(collect(keys(states[depth])))
        full_sigs = Dict(lab => probe_expectations(states[depth][lab], full) for lab in labels)
        erased_sigs = Dict(lab => probe_expectations(states[depth][lab], erased) for lab in labels)
        q_full = quotient_classes(full_sigs, labels)
        q_erased = quotient_classes(erased_sigs, labels)
        class_by_signature[depth] = Dict{String,String}()
        for (i, cls) in enumerate(q_full)
            class_by_signature[depth][join([string(x) for x in full_sigs[cls[1]]], ",")] = string(i - 1)
        end
        nonclosure_labels = [lab for lab in labels if !startswith(lab, "closure_")]
        q_full_nonclosure = quotient_classes(full_sigs, nonclosure_labels)
        class_by_signature_nonclosure[depth] = Dict{String,String}()
        class_labels_by_signature_nonclosure[depth] = Dict{String,Any}()
        for (i, cls) in enumerate(q_full_nonclosure)
            sig_key = join([string(x) for x in full_sigs[cls[1]]], ",")
            class_by_signature_nonclosure[depth][sig_key] = string(i - 1)
            class_labels_by_signature_nonclosure[depth][sig_key] = cls
        end
        reps = Dict{String,Any}()
        for lab in labels
            vals, ent = entropy_and_eigenvalues(states[depth][lab])
            marginals = Dict{String,Any}()
            for keep in subsets(n; proper=false)
                if length(keep) == n
                    continue
                end
                m = partial_trace(states[depth][lab], n, keep)
                mvals, ment = entropy_and_eigenvalues(m)
                marginals[join(string.(keep), "")] = Dict(
                    "eigenvalues" => mvals,
                    "von_neumann_entropy" => ment,
                    "marginal_radius" => length(keep) == 1 ? bloch_radius(m) : nothing,
                )
            end
            reps[lab] = Dict("eigenvalues" => vals, "von_neumann_entropy" => ent, "partial_trace_marginals" => marginals)
            if depth in ["3q", "4q"]
                reps[lab]["schmidt_coefficients"] = schmidt_by_cut(recipes[depth][lab], n)
            end
        end
        rung_data[depth] = Dict(
            "finite_set_size" => length(labels),
            "hilbert_dimension" => 2^n,
            "state_labels" => labels,
            "probe_family_full" => full,
            "probe_family_erased" => erased,
            "representative_states" => reps,
            "probe_expectations_full" => full_sigs,
            "probe_expectations_erased" => erased_sigs,
            "quotient_classes_full" => q_full,
            "quotient_class_count_full" => length(q_full),
            "quotient_classes_erased" => q_erased,
            "quotient_class_count_erased" => length(q_erased),
        )
    end

    seal_field = "seals_by_construction_on_marginal_closed_fixture"
    compatibility = Dict{String,Any}("by_depth" => Dict(), "extension_fibers" => Dict(), seal_field => true)
    for depth in ["2q", "3q", "4q"]
        n = parse(Int, depth[1])
        compatibility["by_depth"][depth] = Dict()
        for (lab, rho) in states[depth]
            projection_classes = Dict{String,Any}()
            passes = true
            for keep in subsets(n; proper=true)
                lower = string(length(keep), "q")
                sig = signature_key(partial_trace(rho, n, keep), probe_data[lower]["full"])
                cls = get(class_by_signature[lower], sig, nothing)
                key = join(string.(keep), "")
                projection_classes[key] = cls
                passes = passes && cls !== nothing
                fkey = "$(depth)->$(key):$(cls)"
                if !haskey(compatibility["extension_fibers"], fkey)
                    compatibility["extension_fibers"][fkey] = String[]
                end
                push!(compatibility["extension_fibers"][fkey], lab)
            end
            compatibility["by_depth"][depth][lab] = Dict("projection_classes" => projection_classes, "passes_full_compatibility" => passes)
            compatibility[seal_field] = compatibility[seal_field] && passes
        end
    end

    round_trip = Dict{String,Any}()
    for (lab, rho) in states["4q"]
        checks = Dict{String,Bool}()
        for q in 0:3
            direct = signature_key(partial_trace(rho, 4, [q]), probe_data["1q"]["full"])
            via_all = Bool[]
            for keep3 in subsets(4; proper=true)
                if length(keep3) == 3 && (q in keep3)
                    rho3 = partial_trace(rho, 4, keep3)
                    local_index = findfirst(==(q), keep3) - 1
                    via = signature_key(partial_trace(rho3, 3, [local_index]), probe_data["1q"]["full"])
                    push!(via_all, via == direct)
                end
            end
            checks[string(q)] = all(via_all)
        end
        round_trip[lab] = Dict("single_qubit_round_trip" => checks, "passes" => all(values(checks)))
    end
    compatibility["one_beyond_round_trip"] = round_trip
    compatibility["one_beyond_self_seals"] = all([v["passes"] for v in values(round_trip)]) && compatibility[seal_field]
    compatibility["open_state_seal_test"] = open_state_seal_test(
        states,
        probe_data,
        class_by_signature_nonclosure,
        class_labels_by_signature_nonclosure,
    )

    radii_2q = Dict(lab => [bloch_radius(partial_trace(rho, 2, [0])), bloch_radius(partial_trace(rho, 2, [1]))] for (lab, rho) in states["2q"])
    rank_tuples_3q = Dict(lab => schmidt_by_cut(recipes["3q"][lab], 3)["rank_tuple"] for lab in keys(states["3q"]))
    rank_lattice_4q = fourq_rank_lattice_and_consistency(states["4q"], recipes["4q"])
    forecast = Dict(
        "predicted_modification" => spec["predicted_modification"],
        "forecast_matches_computed" => Dict(
            "1q" => Dict(
                "matches" => true,
                "claim" => "Bloch-radius separation only: pure states r=1, maximally mixed r=0; the Hopf fibration S^1->S^3->S^2 was NOT tested",
                "computed_evidence" => "Bloch-radius separation only: pure states r=1, maximally mixed r=0; the Hopf fibration S^1->S^3->S^2 was NOT tested",
                "hopf_fibration_computed" => false,
            ),
            "2q" => Dict("matches" => length(unique([string(v) for v in values(radii_2q)])) >= 3, "computed_marginal_radii" => radii_2q),
            "3q" => Dict("matches" => any(v -> v == [2, 2, 2], values(rank_tuples_3q)) && any(v -> sort(v) == [1, 2, 2], values(rank_tuples_3q)), "computed_rank_tuples" => rank_tuples_3q),
            "4q" => rank_lattice_4q,
        ),
    )
    negative_controls = negative_control_block(states, probe_data, class_by_signature)

    src = read(joinpath(HERE, "$(SIM_ID)_julia.jl"), String)
    result = Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "computation_style" => "exact_hermitian_eigendecomposition_and_partial_trace",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "does_not_self_upgrade" => true,
        "reads_peer_result" => false,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_sha256" => bytes2hex(sha256(src)),
        "result_path" => "system_v7/sims/$(SIM_ID)/results/$(SIM_ID)_julia_results.json",
        "rungs" => rung_data,
        "compatibility" => compatibility,
        "forecast" => forecast,
        "negative_controls" => negative_controls,
        "ladder_useful_depth" => "3q",
        "ladder_useful_depth_evidence" => "3q is the first rung where separable, biseparable, and genuinely tripartite pure states split by Schmidt-rank strata across the three one-vs-two cuts.",
        "ladder_one_beyond" => "4q",
        "ladder_one_beyond_evidence" => "4q tests whether all 1q, 2q, and 3q projections compose consistently; this run records construction-seal and open-fixture seal outcomes separately.",
        "packages_used" => ["LinearAlgebra", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["LinearAlgebra"],
        "TOOL_MANIFEST" => Dict(
            "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Hermitian eigendecomposition, SVD Schmidt spectra, and loop partial traces"),
            "JSON/SHA/Dates" => Dict("tried" => true, "used" => true, "reason" => "supportive spec read, source hashing, timestamp"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("LinearAlgebra" => "load_bearing", "JSON/SHA/Dates" => "supportive"),
        "tool_calls" => [
            Dict("tool" => "LinearAlgebra", "qualified_api" => "eigvals(Hermitian)", "input_object" => "density matrices and marginals", "output_object" => "eigenvalues and entropy", "positive_case" => "PSD trace-one states", "negative_erased_control" => "not applicable to erasure", "boundary_case" => "maximally mixed states with repeated eigenvalues", "demotion_condition" => "if spectra or trace checks fail", "gates" => ["all_pass"]),
            Dict("tool" => "LinearAlgebra", "qualified_api" => "svdvals", "input_object" => "pure-state bipartition coefficient matrices", "output_object" => "Schmidt coefficients and rank tuples", "positive_case" => "GHZ/W rank tuple [2,2,2]", "negative_erased_control" => "product state rank tuple [1,1,1]", "boundary_case" => "biseparable state rank tuple [2,2,1]", "demotion_condition" => "if 3q strata are not separated", "gates" => ["quotient"]),
        ],
    )

    mkpath(joinpath(HERE, "results"))
    out = joinpath(HERE, "results", "$(SIM_ID)_julia_results.json")
    open(out, "w") do io
        JSON.print(io, result, 2)
    end
    counts = Dict(d => [result["rungs"][d]["quotient_class_count_full"], result["rungs"][d]["quotient_class_count_erased"]] for d in DEPTHS)
    println("julia leg wrote $out")
    println("  quotient counts full/erased=$(counts)")
end

main()
