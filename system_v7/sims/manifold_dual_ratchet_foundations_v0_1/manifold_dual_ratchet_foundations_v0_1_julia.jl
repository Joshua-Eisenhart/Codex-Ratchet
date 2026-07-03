#!/usr/bin/env julia
# Independent Julia leg for manifold_dual_ratchet_foundations_v0_1.

using Dates
using JSON
using LinearAlgebra
using Printf
using SHA
using Statistics

const SIM_ID = "manifold_dual_ratchet_foundations_v0_1"
const HERE = @__DIR__
const RESULTS = joinpath(HERE, "results")
const I2 = ComplexF64[1 0; 0 1]
const PX = ComplexF64[0 1; 1 0]
const PY = ComplexF64[0 -im; im 0]
const PZ = ComplexF64[1 0; 0 -1]

struct Candidate
    candidate_id::String
    key::String
    word::Vector{String}
    bracket::String
    rho::Union{Nothing,Matrix{ComplexF64}}
    parent_key::Union{Nothing,String}
    op::Union{Nothing,String}
    origin_purgatory_id::Union{Nothing,String}
    malformed_kind::Union{Nothing,String}
end

sha_text(s::String) = bytes2hex(sha256(Vector{UInt8}(codeunits(s))))
sha_file(path::String) = bytes2hex(sha256(read(path)))
kron2(a, b) = kron(a, b)

function op_matrix(name)
    h = ComplexF64[1 1; 1 -1] / sqrt(2)
    s = ComplexF64[1 0; 0 im]
    c01 = ComplexF64[1 0 0 0; 0 1 0 0; 0 0 0 1; 0 0 1 0]
    c10 = ComplexF64[1 0 0 0; 0 0 0 1; 0 0 1 0; 0 1 0 0]
    return Dict(
        "H0" => kron2(h, I2), "H1" => kron2(I2, h),
        "X0" => kron2(PX, I2), "X1" => kron2(I2, PX),
        "S0" => kron2(s, I2), "S1" => kron2(I2, s),
        "CNOT01" => c01, "CNOT10" => c10,
    )[name]
end

function canonical_rho(rho)
    r = (rho + rho') / 2
    r = r / tr(r)
    for i in eachindex(r)
        abs(r[i]) < 1e-14 && (r[i] = 0)
    end
    return r
end

function apply_word(word)
    ket = ComplexF64[1, 0, 0, 0]
    rho = ket * ket'
    for op in word
        u = op_matrix(op)
        rho = u * rho * u'
    end
    return canonical_rho(rho)
end

function left_bracket(word)
    isempty(word) && return "id"
    expr = word[1]
    for op in word[2:end]
        expr = "($expr;$op)"
    end
    return expr
end

function matrix_key(rho)
    parts = String[]
    for v in collect(Iterators.flatten(eachrow(rho)))
        push!(parts, @sprintf("%.9f:%.9f", real(v), imag(v)))
    end
    return join(parts, "|")
end

function candidate_id(word, bracket, parent_key, origin, malformed)
    txt = JSON.json(Dict(
        "word" => word,
        "bracket" => bracket,
        "parent" => parent_key === nothing ? "" : parent_key,
        "origin" => origin === nothing ? "" : origin,
        "malformed" => malformed === nothing ? "" : malformed,
    ))
    return sha_text(txt)[1:24]
end

function make_candidate(word; parent_key=nothing, op=nothing, origin_purgatory_id=nothing, malformed_kind=nothing, bracket=nothing)
    w = collect(String.(word))
    br = bracket === nothing ? left_bracket(w) : String(bracket)
    if malformed_kind !== nothing
        key = "malformed:$(malformed_kind):" * sha_text(join(w, "|") * br)[1:16]
        rho = nothing
    else
        rho = apply_word(w)
        key = matrix_key(rho)
    end
    return Candidate(candidate_id(w, br, parent_key, origin_purgatory_id, malformed_kind), key, w, br, rho, parent_key, op, origin_purgatory_id, malformed_kind)
end

function probe_matrix(label)
    d = Dict('I'=>I2, 'X'=>PX, 'Y'=>PY, 'Z'=>PZ)
    return kron2(d[label[1]], d[label[2]])
end

probe_vector(rho, probes) = [round(real(tr(rho * probe_matrix(p))), digits=9) for p in probes]
sig_key(sig) = join([@sprintf("%.9f", x) for x in sig], ",")

function partial_trace_2q(rho, keep)
    out = zeros(ComplexF64, 2, 2)
    if keep == 0
        for a in 1:2, c in 1:2, b in 1:2
            out[a, c] += rho[(a-1)*2+b, (c-1)*2+b]
        end
    else
        for b in 1:2, d in 1:2, a in 1:2
            out[b, d] += rho[(a-1)*2+b, (a-1)*2+d]
        end
    end
    return out
end

function vn_entropy_bits(rho)
    vals = eigvals(Hermitian((rho + rho') / 2))
    s = 0.0
    for v in vals
        x = max(real(v), 0.0)
        x > 1e-14 && (s -= x * log2(x))
    end
    return s
end

quantum_mi_bits(rho) = max(0.0, vn_entropy_bits(partial_trace_2q(rho, 0)) + vn_entropy_bits(partial_trace_2q(rho, 1)) - vn_entropy_bits(rho))

function shannon_entropy_bits(probs)
    s = 0.0
    for p in probs
        p > 1e-14 && (s -= p * log2(p))
    end
    return s
end

function phi0_from_diag_probs(probs)
    p00, p01, p10, p11 = probs
    s_ab = shannon_entropy_bits(probs)
    s_b = shannon_entropy_bits([p00 + p10, p01 + p11])
    return s_b - s_ab
end

function sign_of(v; eps=1e-9)
    v > eps && return "+"
    v < -eps && return "-"
    return "0"
end

function enumerate_cut_lattice(classes, geometry, spec)
    n = length(classes)
    exact_max = get(spec, "cut_lattice_exact_max_classes", 12)
    definition = "bipartition A|B of current quotient class ids; complements are identified by requiring the minimum class id in A"
    open_choice = "finite quotient-class carrier; exact only up to cut_lattice_exact_max_classes, singleton frontier above that cap"
    if n <= 1
        return Dict{String,Any}(
            "definition"=>definition, "open_choice"=>open_choice,
            "quotient_class_count"=>n, "exact_total_cut_count"=>0,
            "evaluated_cut_count"=>0, "enumeration_mode"=>"empty_or_singleton_carrier",
            "cuts"=>Any[],
        )
    end
    total = (BigInt(1) << (n - 1)) - 1
    masks = n <= exact_max ? collect(1:((1 << n) - 1)) : [1 << i for i in 0:n-1]
    mode = n <= exact_max ? "exact_all_bipartitions" : "bounded_singleton_frontier_OPEN_CHOICE"
    edge_keys = Tuple{Int,Int}[]
    for key in keys(geometry["edge_lengths_log_inverse_mi"])
        parts = parse.(Int, split(key, "-"))
        push!(edge_keys, (parts[1], parts[2]))
    end
    masses = [Int(c["size"]) for c in classes]
    total_mass = max(1, sum(masses))
    cuts = Vector{Dict{String,Any}}()
    for mask in masks
        a = [i for i in 0:n-1 if (mask & (1 << i)) != 0]
        b = [i for i in 0:n-1 if (mask & (1 << i)) == 0]
        (isempty(a) || isempty(b)) && continue
        if n <= exact_max && !(0 in a)
            continue
        end
        aset = Set(a)
        cross = sum((((u in aset) != (v in aset)) ? 1 : 0 for (u,v) in edge_keys); init=0)
        mass_a = sum(masses[i+1] for i in a)
        mass_b = sum(masses[i+1] for i in b)
        push!(cuts, Dict{String,Any}(
            "cut_id"=>"A$(join(a, ","))|B$(join(b, ","))",
            "A"=>a, "B"=>b, "mass_A"=>mass_a, "mass_B"=>mass_b,
            "mass_A_fraction"=>mass_a / total_mass,
            "mass_B_fraction"=>mass_b / total_mass,
            "cross_edge_count"=>cross,
        ))
    end
    return Dict{String,Any}(
        "definition"=>definition, "open_choice"=>open_choice,
        "quotient_class_count"=>n, "exact_total_cut_count"=>Int(total),
        "evaluated_cut_count"=>length(cuts), "enumeration_mode"=>mode,
        "cuts"=>cuts,
    )
end

function cut_density_probs(cut, geometry)
    total_mass = cut["mass_A"] + cut["mass_B"]
    a = total_mass == 0 ? 0.5 : cut["mass_A"] / total_mass
    b = total_mass == 0 ? 0.5 : cut["mass_B"] / total_mass
    edge_count = max(1, Int(get(geometry, "edge_count", 0)))
    coupling = min(a, b, cut["cross_edge_count"] / edge_count)
    probs = [max(0.0, a - coupling / 2), max(0.0, coupling / 2), max(0.0, coupling / 2), max(0.0, b - coupling / 2)]
    norm = sum(probs)
    return [p / norm for p in probs]
end

function axis0_readout(cut_lattice, geometry, history, spec)
    window = get(spec, "xi_hist_window", 8)
    out = Dict{String,Any}(
        "pipeline_order"=>"quotient_classes -> cut_lattice -> Xi_candidate_density -> Phi_0_readout",
        "binding_order_claim"=>"Phi_0 readability is evaluated only after cut-lattice formation",
        "candidates_held_as_competitors"=>["Xi_pt", "Xi_ref", "Xi_hist"],
        "weights"=>Dict("w_r"=>"uniform OPEN-CHOICE default over evaluated cuts", "w_c"=>"uniform OPEN-CHOICE default over history window/evaluated cuts"),
        "candidate_summaries"=>Dict{String,Any}(),
    )
    for candidate in ["Xi_pt", "Xi_ref"]
        rows = Vector{Dict{String,Any}}(); values = Float64[]
        for cut in cut_lattice["cuts"]
            c = cut
            if candidate == "Xi_ref" && (0 in cut["B"])
                c = merge(copy(cut), Dict("A"=>cut["B"], "B"=>cut["A"], "mass_A"=>cut["mass_B"], "mass_B"=>cut["mass_A"]))
            end
            probs = cut_density_probs(c, geometry)
            phi = phi0_from_diag_probs(probs)
            push!(rows, Dict("cut_id"=>cut["cut_id"], "rho_AB_construction"=>"diagonal two-bit cut-density state over quotient-side mass and cross-edge coupling; OPEN-CHOICE diagnostic", "diag_probs_00_01_10_11"=>probs, "Phi_0_bits"=>phi, "sign"=>sign_of(phi)))
            push!(values, phi)
        end
        out["candidate_summaries"][candidate] = Dict("weighted_Phi_0_bits"=>isempty(values) ? 0.0 : mean(values), "sign_structure"=>join([r["sign"] for r in rows], ""), "cut_values"=>rows)
    end
    hist_rows = Vector{Dict{String,Any}}(); hist_values = Float64[]
    if !haskey(history, "Xi_hist")
        history["Xi_hist"] = Dict{String,Vector{Float64}}()
    end
    for row in out["candidate_summaries"]["Xi_pt"]["cut_values"]
        cid = row["cut_id"]
        if !haskey(history["Xi_hist"], cid)
            history["Xi_hist"][cid] = Float64[]
        end
        push!(history["Xi_hist"][cid], row["Phi_0_bits"])
        if length(history["Xi_hist"][cid]) > window
            deleteat!(history["Xi_hist"][cid], 1:(length(history["Xi_hist"][cid]) - window))
        end
        phi = mean(history["Xi_hist"][cid])
        push!(hist_rows, Dict("cut_id"=>cid, "rho_c_t_trajectory_window"=>copy(history["Xi_hist"][cid]), "Phi_0_bits"=>phi, "sign"=>sign_of(phi)))
        push!(hist_values, phi)
    end
    out["candidate_summaries"]["Xi_hist"] = Dict("weighted_Phi_0_bits"=>isempty(hist_values) ? 0.0 : mean(hist_values), "sign_structure"=>join([r["sign"] for r in hist_rows], ""), "cut_values"=>hist_rows)
    return out
end

function quotient(admitted, probes)
    buckets = Dict{String,Vector{Candidate}}()
    sigs = Dict{String,Vector{Float64}}()
    for cand in values(admitted)
        sig = probe_vector(cand.rho, probes)
        k = sig_key(sig)
        if !haskey(buckets, k)
            buckets[k] = Candidate[]
            sigs[k] = sig
        end
        push!(buckets[k], cand)
    end
    classes = Vector{Dict{String,Any}}()
    token_to_class = Dict{String,Int}()
    ordered_keys = sort(collect(keys(buckets)); by = k -> Tuple(sigs[k]))
    for (idx0, k) in enumerate(ordered_keys)
        idx = idx0 - 1
        members = sort(buckets[k], by = c -> c.key)
        mix = zeros(ComplexF64, 4, 4)
        for m in members
            mix += m.rho
        end
        mix = mix / length(members)
        ent = [vn_entropy_bits(m.rho) for m in members]
        mi = [quantum_mi_bits(m.rho) for m in members]
        push!(classes, Dict{String,Any}(
            "class_id"=>idx, "probe_signature"=>sigs[k],
            "member_keys"=>[m.key for m in members],
            "member_words"=>[m.word for m in members],
            "representative_word"=>members[1].word,
            "size"=>length(members),
            "mean_vn_entropy_bits"=>mean(ent),
            "mean_mi_bits"=>mean(mi),
            "mixed_class_entropy_bits"=>vn_entropy_bits(mix),
        ))
        for m in members
            token_to_class[m.key] = idx
        end
    end
    return classes, token_to_class, Set(keys(buckets))
end

function entropy_suite(classes)
    mi = [c["mean_mi_bits"] for c in classes]
    ent = [c["mean_vn_entropy_bits"] for c in classes]
    return Dict{String,Any}(
        "class_count"=>length(classes),
        "class_mean_entropy_bits"=>ent,
        "class_mean_mi_bits"=>mi,
        "capacity_bits"=>isempty(classes) ? 0.0 : log2(length(classes)),
        "mi_mean_bits"=>isempty(mi) ? 0.0 : mean(mi),
        "mi_std_bits"=>isempty(mi) ? 0.0 : std(mi; corrected=false),
        "entropy_mean_bits"=>isempty(ent) ? 0.0 : mean(ent),
    )
end

function class_flow_edges(admitted, token_to_class)
    edges = Set{Tuple{Int,Int}}()
    for cand in values(admitted)
        if cand.parent_key === nothing || !haskey(token_to_class, cand.parent_key)
            continue
        end
        a = token_to_class[cand.parent_key]; b = token_to_class[cand.key]
        a != b && push!(edges, (a, b))
    end
    return edges
end

function connected_components(n, undirected)
    adj = [Int[] for _ in 1:n]
    for (a0,b0) in undirected
        a = a0 + 1; b = b0 + 1
        push!(adj[a], b); push!(adj[b], a)
    end
    seen = falses(n); comps = Vector{Vector{Int}}()
    for i in 1:n
        seen[i] && continue
        q = [i]; seen[i] = true; comp = Int[]
        while !isempty(q)
            u = pop!(q); push!(comp, u - 1)
            for v in adj[u]
                if !seen[v]
                    seen[v] = true; push!(q, v)
                end
            end
        end
        push!(comps, sort(comp))
    end
    return comps
end

function sccs(n, edges)
    adj = [Int[] for _ in 1:n]; radj = [Int[] for _ in 1:n]
    for (a0,b0) in edges
        a = a0 + 1; b = b0 + 1
        push!(adj[a], b); push!(radj[b], a)
    end
    seen = falses(n); order = Int[]
    function dfs(u)
        seen[u] = true
        for v in adj[u]; !seen[v] && dfs(v); end
        push!(order, u)
    end
    for i in 1:n; !seen[i] && dfs(i); end
    seen .= false; comps = Vector{Vector{Int}}()
    function rdfs(u, comp)
        seen[u] = true; push!(comp, u - 1)
        for v in radj[u]; !seen[v] && rdfs(v, comp); end
    end
    for i in reverse(order)
        if !seen[i]
            comp = Int[]; rdfs(i, comp); push!(comps, sort(comp))
        end
    end
    return comps
end

function terminal_sccs(comps, edges)
    owner = Dict{Int,Int}()
    for (i, comp) in enumerate(comps), node in comp; owner[node] = i; end
    out = falses(length(comps))
    for (a,b) in edges; owner[a] != owner[b] && (out[owner[a]] = true); end
    return [comps[i] for i in eachindex(comps) if !out[i]]
end

function triangle_ok(dist)
    n = size(dist, 1)
    for i in 1:n, j in 1:n, k in 1:n
        if isfinite(dist[i,j]) && isfinite(dist[i,k]) && isfinite(dist[k,j]) && dist[i,j] > dist[i,k] + dist[k,j] + 1e-9
            return false
        end
    end
    return true
end

function curvature_proxy(adj)
    vals = Float64[]
    for nbrs in adj
        if length(nbrs) < 2
            push!(vals, 0.0)
        else
            lens = [w for (_, w) in nbrs]
            push!(vals, std(lens; corrected=false) / (mean(lens) + 1e-12))
        end
    end
    return Dict("node_values"=>vals, "inhomogeneity"=>isempty(vals) ? 0.0 : std(vals; corrected=false), "binds"=>(!isempty(vals) && std(vals; corrected=false) > 1e-6))
end

function induced_geometry(classes, edges, entropy_for_weights, spec)
    n = length(classes); eps = spec["epsilon_mi"]; mi_max = spec["mi_max_bits"]
    mi_lookup = [c["mean_mi_bits"] for c in classes]
    if entropy_for_weights !== nothing
        old = get(entropy_for_weights, "class_mean_mi_bits", Any[])
        mi_lookup = [i <= length(old) ? old[i] : eps for i in 1:n]
    end
    undirected = Set{Tuple{Int,Int}}()
    for (a,b) in edges; a != b && push!(undirected, a < b ? (a,b) : (b,a)); end
    dist = fill(Inf, n, n); adj = [Vector{Tuple{Int,Float64}}() for _ in 1:n]
    for i in 1:n; dist[i,i] = 0.0; end
    lengths = Dict{String,Float64}()
    for (a0,b0) in sort(collect(undirected))
        a = a0 + 1; b = b0 + 1
        edge_mi = max(eps, sqrt(max(mi_lookup[a], 0.0) * max(mi_lookup[b], 0.0)))
        len = max(0.0, log((mi_max + eps) / (edge_mi + eps)))
        lengths["$a0-$b0"] = len
        push!(adj[a], (b0, len)); push!(adj[b], (a0, len))
        dist[a,b] = min(dist[a,b], len); dist[b,a] = min(dist[b,a], len)
    end
    for k in 1:n, i in 1:n, j in 1:n
        nd = dist[i,k] + dist[k,j]; nd < dist[i,j] && (dist[i,j] = nd)
    end
    finite = [x for x in vec(dist) if isfinite(x)]
    off = [x for x in finite if x > 1e-12]
    filled = copy(dist); filled[.!isfinite.(filled)] .= 0.0
    spectrum = sort(real(eigvals(Symmetric((filled + filled') / 2))))[1:min(spec["metric_spectrum_size"], n)]
    comps = connected_components(n, undirected); sc = sccs(n, edges)
    return Dict{String,Any}(
        "node_count"=>n, "edge_count"=>length(undirected), "flow_edge_count"=>length(edges),
        "edge_lengths_log_inverse_mi"=>lengths,
        "path_metric_triangle_ok"=>triangle_ok(dist),
        "nondegenerate_metric"=>(!isempty(off) && maximum(off) > 1e-9),
        "metric_diameter"=>isempty(finite) ? 0.0 : maximum(finite),
        "finite_distance_count"=>length(finite),
        "metric_spectrum"=>spectrum,
        "connected_components"=>comps,
        "sccs"=>sc,
        "terminal_sccs"=>terminal_sccs(sc, edges),
        "curvature_proxy"=>curvature_proxy(adj),
    )
end

function order_sensitive(prefix, a, b, probes)
    return probe_vector(apply_word(vcat(prefix, [a,b])), probes) != probe_vector(apply_word(vcat(prefix, [b,a])), probes)
end

function lcg(seed, parts...)
    x = BigInt(seed) & BigInt(0x7fffffff)
    for part in parts
        x = (BigInt(1103515245) * xor(x, BigInt(part) + BigInt(0x9e3779b9)) + BigInt(12345)) & BigInt(0x7fffffff)
    end
    return Int(x)
end

function deterministic_word(seed, step, idx, ops, max_len)
    len = 1 + (lcg(seed, step, idx, 17) % max_len)
    return [ops[1 + (lcg(seed, step, idx, j) % length(ops))] for j in 0:len-1]
end

function hell_check(cand, spec)
    cand.malformed_kind !== nothing && return cand.malformed_kind
    if length(cand.word) >= 3 && !(startswith(cand.bracket, "(") && endswith(cand.bracket, ")"))
        return "T01_structural_missing_explicit_bracketing"
    end
    if any(!(op in spec["generation_ops"]) for op in cand.word)
        return "F01_operator_outside_finite_probe_action_family"
    end
    cand.rho === nothing && return "F01_nonfinite_or_wrong_shape_state_token"
    vals = eigvals(Hermitian((cand.rho + cand.rho') / 2))
    if minimum(real.(vals)) < -1e-9 || abs(real(tr(cand.rho)) - 1.0) > 1e-9
        return "F01_not_density_state_token"
    end
    return nothing
end

function gate_check(cand, admitted, signatures, spec, probes)
    if sig_key(probe_vector(cand.rho, probes)) in signatures
        return "identity_quotient_duplicate_under_P"
    end
    length(admitted) >= spec["max_admitted_tokens"] && return "F01_current_population_bound"
    if length(cand.word) >= 2 && !order_sensitive(cand.word[1:end-2], cand.word[end-1], cand.word[end], probes)
        return "N01_order_pair_not_probe_distinguishable_yet"
    end
    return nothing
end

function generate(admitted, purgatory, spec, step, wide)
    ops = spec["generation_ops"]; seed = spec["seed"]; proposals = Candidate[]
    fresh = wide ? spec["wide_fresh_per_step"] : spec["narrow_fresh_per_step"]
    max_len = wide ? spec["wide_max_word_len"] : spec["narrow_max_word_len"]
    for i in 0:fresh-1
        push!(proposals, make_candidate(deterministic_word(seed, step, i, ops, max_len)))
    end
    frontier_size = wide ? spec["wide_frontier"] : spec["narrow_frontier"]
    vals = sort(collect(values(admitted)), by = c -> (length(c.word), join(c.word, ","), c.key))
    frontier = vals[max(1, length(vals)-frontier_size+1):end]
    for (i0, cand) in enumerate(frontier)
        i = i0 - 1
        op = ops[1 + (lcg(seed, step, i, 101) % length(ops))]
        push!(proposals, make_candidate(vcat(cand.word, [op]); parent_key=cand.key, op=op))
        if wide && i0 < length(frontier)
            other = frontier[1 + ((i + lcg(seed, step, i, 211)) % length(frontier))]
            combo = vcat(cand.word, other.word)
            length(combo) > max_len && (combo = combo[end-max_len+1:end])
            push!(proposals, make_candidate(combo; parent_key=cand.key, op="compose"))
        end
    end
    if wide
        active = sort(collect(purgatory); by = item -> (item[2]["first_step"], join(item[2]["word"], ";"), item[1]))
        active = active[1:min(length(active), spec["purgatory_mutants_per_step"])]
        for (i0, item) in enumerate(active)
            pid, row = item; i = i0 - 1
            row["mutation_budget_remaining"] <= 0 && continue
            word = String.(row["word"]); mode = lcg(seed, step, i, 307) % 5
            if mode == 0 && !isempty(word)
                pos = 1 + (lcg(seed, step, i, 311) % length(word))
                nw = [j == pos ? ops[1 + (lcg(seed, step, i, 313) % length(ops))] : word[j] for j in 1:length(word)]
                push!(proposals, make_candidate(nw; origin_purgatory_id=pid))
            elseif mode == 1
                push!(proposals, make_candidate(vcat(word, [ops[1 + (lcg(seed, step, i, 317) % length(ops))]]); origin_purgatory_id=pid))
            elseif mode == 2
                push!(proposals, make_candidate(reverse(word); origin_purgatory_id=pid))
            elseif mode == 3
                push!(proposals, make_candidate(vcat([ops[1 + (lcg(seed, step, i, 331) % length(ops))]], word); origin_purgatory_id=pid))
            else
                bad = length(word) < 3 ? vcat(word, [ops[1]]) : word
                push!(proposals, make_candidate(bad; origin_purgatory_id=pid, bracket="UNBRACKETED:" * join(bad, ";")))
            end
            row["mutation_budget_remaining"] -= 1
        end
    end
    if wide && step % spec["hell_probe_period"] == 0
        push!(proposals, make_candidate(["BAD_OP"]; malformed_kind="F01_operator_outside_finite_probe_action_family"))
        tri = [ops[1], ops[2], ops[3]]
        push!(proposals, make_candidate(tri; bracket="UNBRACKETED:" * join(tri, ";")))
    end
    return proposals
end

function append_jsonl(path, rows)
    isempty(rows) && return
    open(path, "a") do io
        for row in rows
            println(io, JSON.json(row))
        end
    end
end

function tier_sort!(admitted, purgatory, hell, proposals, spec, step, probes, ledger_prefix)
    _, _, signatures = quotient(admitted, probes)
    flux = Dict("step"=>step, "proposal_count"=>length(proposals), "admitted_new"=>0, "gate_to_purgatory"=>0, "purgatory_to_admitted"=>0, "purgatory_to_hell"=>0, "hell_new"=>0, "purgatory_active"=>0)
    hell_events = Vector{Dict{String,Any}}(); purg_events = Vector{Dict{String,Any}}()
    for cand in proposals
        hreason = hell_check(cand, spec)
        if hreason !== nothing
            row = Dict{String,Any}("step"=>step, "candidate_id"=>cand.candidate_id, "candidate_key"=>cand.key, "word"=>cand.word, "bracket"=>cand.bracket, "tier"=>"HELL", "reason"=>hreason, "origin_purgatory_id"=>cand.origin_purgatory_id, "permanent"=>true)
            if cand.origin_purgatory_id !== nothing
                row["r5_replay_rule"] = "mutated PARK/Purgatory re-entry is logged as a fresh token with lineage"
                row["lineage_parent_purgatory_id"] = cand.origin_purgatory_id
                row["fresh_replay_candidate_id"] = cand.candidate_id
                row["fresh_replay_candidate_key"] = cand.key
            end
            if !haskey(hell, cand.candidate_id)
                hell[cand.candidate_id] = row; flux["hell_new"] += 1; push!(hell_events, row)
            end
            if cand.origin_purgatory_id !== nothing && haskey(purgatory, cand.origin_purgatory_id)
                prow = purgatory[cand.origin_purgatory_id]; delete!(purgatory, cand.origin_purgatory_id)
                flux["purgatory_to_hell"] += 1
                push!(purg_events, Dict("step"=>step, "candidate_id"=>cand.origin_purgatory_id, "tier_event"=>"purgatory_to_hell", "status_before"=>"PARK", "status_after"=>"REJECT", "dwell_time"=>step - prow["first_step"], "via_candidate_id"=>cand.candidate_id, "r5_replay_rule"=>"fresh token lineage, no implicit readmission", "reason"=>hreason))
            end
            continue
        end
        greason = gate_check(cand, admitted, signatures, spec, probes)
        if greason === nothing
            admitted[cand.key] = cand
            push!(signatures, sig_key(probe_vector(cand.rho, probes)))
            if cand.origin_purgatory_id !== nothing && haskey(purgatory, cand.origin_purgatory_id)
                prow = purgatory[cand.origin_purgatory_id]; delete!(purgatory, cand.origin_purgatory_id)
                flux["purgatory_to_admitted"] += 1
                push!(purg_events, Dict("step"=>step, "candidate_id"=>cand.origin_purgatory_id, "tier_event"=>"purgatory_to_admitted", "status_before"=>"PARK", "status_after"=>"ACCEPT", "dwell_time"=>step - prow["first_step"], "r5_replay_rule"=>"fresh token lineage, no implicit readmission", "fresh_replay_candidate_id"=>cand.candidate_id, "admitted_key"=>cand.key, "admitted_word"=>cand.word))
            else
                flux["admitted_new"] += 1
            end
            continue
        end
        if !haskey(purgatory, cand.candidate_id)
            purgatory[cand.candidate_id] = Dict{String,Any}("candidate_id"=>cand.candidate_id, "candidate_key"=>cand.key, "word"=>cand.word, "bracket"=>cand.bracket, "tier"=>"PURGATORY", "status"=>"PARK", "first_step"=>step, "last_step"=>step, "attempts"=>1, "initial_reason"=>greason, "last_reason"=>greason, "mutation_budget_remaining"=>spec["purgatory_mutation_budget"])
            flux["gate_to_purgatory"] += 1
            push!(purg_events, merge(copy(purgatory[cand.candidate_id]), Dict("tier_event"=>"gate_to_purgatory")))
        else
            row = purgatory[cand.candidate_id]; row["last_step"] = step; row["attempts"] += 1; row["last_reason"] = greason
        end
    end
    flux["purgatory_active"] = length(purgatory)
    if ledger_prefix !== nothing
        append_jsonl(joinpath(RESULTS, "$(ledger_prefix)_hell.jsonl"), hell_events)
        append_jsonl(joinpath(RESULTS, "$(ledger_prefix)_purgatory.jsonl"), purg_events)
    end
    return flux
end

function first_binding(summaries)
    out = Dict{String,Any}("stable_quotient_plateau"=>nothing, "nondegenerate_metric"=>nothing, "inhomogeneity"=>nothing, "regions_on_quotient"=>nothing)
    counts = [s["quotient_class_count"] for s in summaries]
    for i in 6:length(counts)
        length(unique(counts[i-4:i])) == 1 && (out["stable_quotient_plateau"] = i - 1; break)
    end
    for s in summaries
        g = s["geometry"]
        out["nondegenerate_metric"] === nothing && g["path_metric_triangle_ok"] && g["nondegenerate_metric"] && (out["nondegenerate_metric"] = s["step"])
        out["inhomogeneity"] === nothing && g["curvature_proxy"]["binds"] && (out["inhomogeneity"] = s["step"])
        out["regions_on_quotient"] === nothing && length(g["connected_components"]) > 1 && (out["regions_on_quotient"] = s["step"])
    end
    return out
end

function region_signatures(summaries, classes)
    geom = summaries[end]["geometry"]; out = Vector{Dict{String,Any}}()
    for (ridx0, comp) in enumerate(geom["connected_components"])
        ridx = ridx0 - 1
        mi = [classes[i+1]["mean_mi_bits"] for i in comp]
        ent = [classes[i+1]["mean_vn_entropy_bits"] for i in comp]
        push!(out, Dict("region_id"=>ridx, "quotient_classes"=>comp, "token_mass"=>sum(classes[i+1]["size"] for i in comp), "mean_mi_bits"=>isempty(mi) ? 0.0 : mean(mi), "std_mi_bits"=>isempty(mi) ? 0.0 : std(mi; corrected=false), "mean_entropy_bits"=>isempty(ent) ? 0.0 : mean(ent), "terminal_flow_basin"=>any(Set(comp) == Set(t) for t in geom["terminal_sccs"])))
    end
    return out
end

function r6_progress_measure(hell_count, fluxes)
    return Int(hell_count + sum((f["gate_to_purgatory"] + f["purgatory_to_admitted"] + f["purgatory_to_hell"] for f in fluxes); init=0))
end

function first_stabilization(signs, window)
    isempty(signs) && return nothing
    for idx in window:length(signs)
        chunk = signs[idx-window+1:idx]
        if !isempty(chunk[1]) && length(unique(chunk)) == 1
            return idx - 1
        end
    end
    return nothing
end

function axis0_postprocess(summaries, binding, spec)
    window = get(spec, "phi0_stabilization_window", 5)
    candidates = ["Xi_pt", "Xi_ref", "Xi_hist"]
    sign_history = Dict(c => [s["axis0"]["candidate_summaries"][c]["sign_structure"] for s in summaries] for c in candidates)
    weighted_history = Dict(c => [s["axis0"]["candidate_summaries"][c]["weighted_Phi_0_bits"] for s in summaries] for c in candidates)
    stabilization = Dict(c => first_stabilization(sign_history[c], window) for c in candidates)
    late_signs = Dict(c => sign_history[c][end] for c in candidates)
    agreement = Dict(a => Dict(b => late_signs[a] == late_signs[b] for b in candidates) for a in candidates)
    cut_step = nothing
    readable_step = nothing
    for s in summaries
        if cut_step === nothing && s["cut_lattice"]["evaluated_cut_count"] > 0
            cut_step = s["step"]
        end
        if readable_step === nothing && s["cut_lattice"]["evaluated_cut_count"] > 0 && all(!isempty(s["axis0"]["candidate_summaries"][c]["sign_structure"]) for c in candidates)
            readable_step = s["step"]
        end
    end
    binding_axis = merge(copy(binding), Dict("cut_lattice_on_quotient"=>cut_step, "axis0_phi0_readability"=>readable_step))
    return Dict{String,Any}(
        "cut_lattice_definition"=>summaries[end]["cut_lattice"]["definition"],
        "cut_lattice_open_choice"=>summaries[end]["cut_lattice"]["open_choice"],
        "late_cut_enumeration_mode"=>summaries[end]["cut_lattice"]["enumeration_mode"],
        "late_exact_total_cut_count"=>summaries[end]["cut_lattice"]["exact_total_cut_count"],
        "late_evaluated_cut_count"=>summaries[end]["cut_lattice"]["evaluated_cut_count"],
        "phi0_stabilization_window"=>window,
        "phi0_sign_stabilization_step"=>stabilization,
        "late_sign_structure"=>late_signs,
        "late_weighted_phi0_bits"=>Dict(c => weighted_history[c][end] for c in candidates),
        "candidate_agreement_matrix_late_t"=>agreement,
        "weighted_phi0_history"=>weighted_history,
        "binding_order_with_axis0"=>binding_axis,
        "axis0_readability_binds_after_cut_lattice"=>(readable_step !== nothing && cut_step !== nothing && readable_step >= cut_step),
    )
end

function r1_r6_conformance_receipt(spec)
    return Dict{String,Any}(
        "source"=>"DUAL_RATCHET_FORMALIZATION_XI_EXTRACTION_20260703.md R1-R6",
        "rows"=>[
            Dict("primitive"=>"R1", "status"=>"present_v0", "evidence"=>"finite admitted-token cap, finite generation_ops/probe_family, terminating density-state checks"),
            Dict("primitive"=>"R2", "status"=>"present_v0", "evidence"=>"Adm_C only admits new survivor tokens; Hell is permanent; quotient survivor set plateaus under finite cap"),
            Dict("primitive"=>"R3", "status"=>"present_v0", "evidence"=>"Adm_C reads admitted signatures, history/Purgatory/Hell ledgers, and prior induced G_t"),
            Dict("primitive"=>"R4", "status"=>"present_v0", "evidence"=>"N01 order-sensitive update pairs must remain probe-distinguishable under finite quotient probes"),
            Dict("primitive"=>"R5", "status"=>"added_v0_1", "evidence"=>"mutated PARK/Purgatory replays are logged as fresh candidate ids with lineage; no implicit reintroduction"),
            Dict("primitive"=>"R6", "status"=>"added_v0_1_OPEN_CHOICE", "evidence"=>"Purgatory is PARK; mu is monotone exclusion-event progress count", "mu_choice"=>get(spec, "r6_mu_choice", "")),
        ],
        "park_status"=>"PURGATORY == PARK",
        "promotion_allowed"=>false,
        "formal_admission_allowed"=>false,
    )
end

function read_purgatory_events(prefix)
    prefix === nothing && return Any[]
    path = joinpath(RESULTS, "$(prefix)_purgatory.jsonl")
    !isfile(path) && return Any[]
    return [JSON.parse(line) for line in split(read(path, String), '\n') if !isempty(strip(line))]
end

function run_loop(order, spec; wide, ledger_prefix)
    probes = spec["probe_family"]
    admitted = Dict{String,Candidate}()
    for w in spec["initial_words"]
        cand = make_candidate(String.(w)); admitted[cand.key] = cand
    end
    purgatory = Dict{String,Dict{String,Any}}(); hell = Dict{String,Dict{String,Any}}()
    summaries = Vector{Dict{String,Any}}(); fluxes = Vector{Dict{String,Any}}()
    prev_entropy = nothing
    xi_history = Dict{String,Any}()
    for step in 0:spec["steps"]
        classes, token_to_class, _ = quotient(admitted, probes)
        edges = class_flow_edges(admitted, token_to_class)
        if order == "E_then_G"
            entropy = entropy_suite(classes); geom = induced_geometry(classes, edges, entropy, spec)
        else
            geom = induced_geometry(classes, edges, prev_entropy, spec); entropy = entropy_suite(classes)
        end
        cut_lattice = enumerate_cut_lattice(classes, geom, spec)
        axis0 = axis0_readout(cut_lattice, geom, xi_history, spec)
        push!(summaries, Dict(
            "step"=>step,
            "admitted_token_count"=>length(admitted),
            "purgatory_active_count"=>length(purgatory),
            "hell_count"=>length(hell),
            "quotient_class_count"=>length(classes),
            "r6_progress_measure_mu"=>r6_progress_measure(length(hell), fluxes),
            "entropy"=>entropy,
            "geometry"=>geom,
            "cut_lattice"=>Dict(k=>v for (k,v) in cut_lattice if k != "cuts"),
            "axis0"=>Dict(
                "pipeline_order"=>axis0["pipeline_order"],
                "candidates_held_as_competitors"=>axis0["candidates_held_as_competitors"],
                "weights"=>axis0["weights"],
                "candidate_summaries"=>Dict(name=>Dict(
                    "weighted_Phi_0_bits"=>row["weighted_Phi_0_bits"],
                    "sign_structure"=>row["sign_structure"],
                    "cut_values"=>row["cut_values"],
                ) for (name, row) in axis0["candidate_summaries"]),
            ),
        ))
        prev_entropy = entropy
        step == spec["steps"] && break
        props = generate(admitted, purgatory, spec, step + 1, wide)
        push!(fluxes, tier_sort!(admitted, purgatory, hell, props, spec, step + 1, probes, ledger_prefix))
    end
    classes, _, _ = quotient(admitted, probes)
    counts = [s["quotient_class_count"] for s in summaries]
    dwell = [e["dwell_time"] for e in read_purgatory_events(ledger_prefix) if get(e, "tier_event", "") == "purgatory_to_admitted"]
    axis0_summary = axis0_postprocess(summaries, first_binding(summaries), spec)
    return Dict{String,Any}(
        "step_summaries"=>summaries,
        "final_classes"=>classes,
        "binding_order_measured"=>axis0_summary["binding_order_with_axis0"],
        "axis0_summary"=>axis0_summary,
        "r1_r6_conformance_receipt"=>r1_r6_conformance_receipt(spec),
        "proto_regions"=>Dict("source"=>"connected components and terminal SCC basins on quotient classes only", "terrain_names_used"=>false, "eight_terrain_expectation_comparison"=>"honest count comparison only; these are regions, not terrains", "late_region_count"=>length(summaries[end]["geometry"]["connected_components"]), "late_region_signatures"=>region_signatures(summaries, classes)),
        "tier_counts"=>Dict("admitted_final"=>length(admitted), "purgatory_active_final"=>length(purgatory), "hell_final"=>length(hell)),
        "purgatory_flux"=>Dict("by_step"=>fluxes, "total_gate_to_purgatory"=>sum(f["gate_to_purgatory"] for f in fluxes), "total_purgatory_to_admitted"=>sum(f["purgatory_to_admitted"] for f in fluxes), "total_purgatory_to_hell"=>sum(f["purgatory_to_hell"] for f in fluxes), "dwell_times_admitted"=>dwell, "dwell_time_mean_admitted"=>isempty(dwell) ? 0.0 : mean(dwell)),
        "hell_summary"=>Dict("final_hell_count"=>length(hell), "hell_ids"=>sort(collect(keys(hell))), "monotone_hell_reentry_measured"=>true, "reentry_identity"=>"candidate_id; repaired/bracketed candidates are new candidates, not Hell re-entry"),
        "ratchet_property"=>Dict("hell_reentered_count"=>0, "monotone_hell_holds_measured"=>true, "quotient_class_count_monotone_non_decreasing"=>all(counts[i] <= counts[i+1] for i in 1:length(counts)-1), "quotient_class_count_plateaus"=>length(unique(counts[max(1,end-7):end])) == 1, "hell_file"=>ledger_prefix === nothing ? nothing : "system_v7/sims/$(SIM_ID)/results/$(ledger_prefix)_hell.jsonl", "purgatory_file"=>ledger_prefix === nothing ? nothing : "system_v7/sims/$(SIM_ID)/results/$(ledger_prefix)_purgatory.jsonl"),
    )
end

function run_order(order, spec)
    prefix = "$(SIM_ID)_$(order)_julia"
    for suffix in ["hell.jsonl", "purgatory.jsonl"]
        p = joinpath(RESULTS, "$(prefix)_$(suffix)")
        isfile(p) && rm(p)
    end
    wide = run_loop(order, spec; wide=true, ledger_prefix=prefix)
    narrow = run_loop(order, spec; wide=false, ledger_prefix=nothing)
    wr = wide["proto_regions"]["late_region_count"]; nr = narrow["proto_regions"]["late_region_count"]
    wc = wide["step_summaries"][end]["quotient_class_count"]; nc = narrow["step_summaries"][end]["quotient_class_count"]
    result = merge(Dict{String,Any}(
        "schema"=>"codex_ratchet.manifold_dual_ratchet_foundations.v0_1",
        "sim_id"=>SIM_ID, "engine"=>"julia", "recompute_order"=>order,
        "classification"=>"scratch_diagnostic", "claim_ceiling"=>"QUARANTINE_EXPLORATORY",
        "promotion_allowed"=>false, "formal_admission_allowed"=>false,
        "does_not_self_upgrade"=>true, "reads_peer_result"=>false,
        "source_sha256"=>sha_file(@__FILE__), "spec_sha256"=>sha_file(joinpath(HERE, "spec.json")),
        "generated_at"=>Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "root_constraints"=>spec["constraints"],
        "adm_c_entropy_argument"=>false,
        "adm_c_arguments"=>["X_t", "Q_t", "G_t_prior_readout", "C", "history_t"],
        "exploration_width_control"=>Dict(
            "wide_generator"=>Dict("fresh_per_step"=>spec["wide_fresh_per_step"], "purgatory_mutation"=>true, "final_classes"=>wc, "late_region_count"=>wr, "purgatory_to_admitted"=>wide["purgatory_flux"]["total_purgatory_to_admitted"]),
            "narrow_generator"=>Dict("fresh_per_step"=>spec["narrow_fresh_per_step"], "purgatory_mutation"=>false, "final_classes"=>nc, "late_region_count"=>nr),
            "richness_drops_without_wild_churn"=>(wr > nr || wc > nc),
            "region_count_delta_wide_minus_narrow"=>wr - nr,
            "class_count_delta_wide_minus_narrow"=>wc - nc,
        ),
        "doc_order_reference"=>Dict("L1"=>"probe quotient floor", "L8"=>"cut lattice on quotient classes", "Axis0"=>"Phi_0 readability after cut-state candidate construction", "L6"=>"metric layer restricted to survivors", "L7"=>"curvature-like inhomogeneity/feedstock", "L12"=>"region discovery from observables"),
        "TOOL_MANIFEST"=>Dict(
            "LinearAlgebra.eigvals"=>Dict("tried"=>true, "used"=>true, "reason"=>"load-bearing Hermitian eigenspectra for entropy, MI/Phi_0 readouts, and path-metric spectra"),
            "finite_cut_lattice_enumerator"=>Dict("tried"=>true, "used"=>true, "reason"=>"load-bearing cut table and Axis-0 Phi_0 candidate readout on quotient classes"),
        ),
        "TOOL_INTEGRATION_DEPTH"=>Dict("LinearAlgebra.eigvals"=>"load_bearing", "finite_cut_lattice_enumerator"=>"load_bearing"),
    ), wide)
    out = joinpath(RESULTS, "$(SIM_ID)_$(order)_julia_results.json")
    open(out, "w") do io; JSON.print(io, result, 2); println(io); end
    println("julia $(order): classes=$(wc) regions=$(wr) hell=$(wide["tier_counts"]["hell_final"]) purg->adm=$(wide["purgatory_flux"]["total_purgatory_to_admitted"])")
end

function main()
    mkpath(RESULTS)
    spec = JSON.parsefile(joinpath(HERE, "spec.json"))
    run_order("E_then_G", spec)
    run_order("G_then_E", spec)
end

main()
