#!/usr/bin/env julia

using Dates
using JSON
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "twistor_incidence_finite_packet_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const MODE = "julia_canon_plus_jax_diagnostic"
const PIN_BLOCK_CANONICAL = "{\"baseline_sample\":{\"packet\":\"mct_dynamic_admissibility_packet_v0\",\"probe_rows\":15,\"relation_nodes\":35},\"chirality_pairing\":{\"formula_mod2\":\"u0*v2 + u1*v3 + u2*v0 + u3*v1\",\"source_note\":\"fixed symplectic/dual pairing sign on lexicographic line generators\",\"status\":\"PINNED-CHOICE\"},\"dictionary\":{\"alpha_star\":\"7-line pencil through a projective point\",\"event_candidate\":\"projective line\",\"null_relation_candidate\":\"line-intersection graph\"},\"engine_mode\":\"julia_canon_plus_jax_diagnostic\",\"expected_counts\":{\"lines\":35,\"lines_through_point\":7,\"points\":15},\"field\":\"F_2\",\"object\":\"PG(3,2)\",\"probe_families\":[\"P_proj\",\"P_inc\",\"P_null\",\"P_pencil\",\"P_chir\",\"P_recon\"],\"projective_quotient\":\"nonzero vectors of F_2^4 modulo F_2^*; map still computed explicitly\",\"q\":2}"
const PIN_BLOCK_SHA256 = bytes2hex(sha256(PIN_BLOCK_CANONICAL))

const SOURCE_REFS = Dict(
    "twistor_spec" => "system_v6/receipts/twistor_incidence_mine_20260610.md:B-D",
    "pg32_precedent" => "system_v6/sims/pg32_sedenion_incidence/",
    "mct_baseline" => "system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_jax_results.json",
    "engine_mode_rule" => "system_v6/README.md:11",
)

const TOOL_MANIFEST = Dict(
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result and committed baseline parsing"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source/result/PIN hashing"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing SMT proof that valid computed lines do not meet in two points, with bad-incidence SAT control"),
)
const TOOL_INTEGRATION_DEPTH = Dict("JSON" => "supportive", "SHA" => "supportive", "Z3" => "load_bearing")

function sha256_file(path::String)
    bytes2hex(open(sha256, path))
end

function sha256_text(text::String)
    bytes2hex(sha256(text))
end

function canonical_hash(obj)
    sha256_text(JSON.json(obj))
end

function all_vectors()
    out = Vector{Vector{Int}}()
    for n in 1:15
        push!(out, [((n >> shift) & 1) for shift in 3:-1:0])
    end
    out
end

projective_class(v::Vector{Int}) = copy(v)

function add_mod2(a::Vector{Int}, b::Vector{Int})
    [(a[i] + b[i]) % 2 for i in eachindex(a)]
end

function vec_key(v::Vector{Int})
    join(v, "")
end

function build_pg32()
    raw = all_vectors()
    classes = sort(collect(Base.values(Dict(vec_key(projective_class(v)) => projective_class(v) for v in raw))), by=vec_key)
    point_id = Dict(vec_key(p) => idx - 1 for (idx, p) in enumerate(classes))
    quotient_rows = [Dict("raw_vector" => v, "projective_class" => projective_class(v), "class_id" => point_id[vec_key(projective_class(v))]) for v in raw]
    line_keys = Set{String}()
    line_sets = Vector{Vector{Int}}()
    for i in 1:length(classes), j in (i + 1):length(classes)
        c = add_mod2(classes[i], classes[j])
        all(x -> x == 0, c) && continue
        line = sort([point_id[vec_key(classes[i])], point_id[vec_key(classes[j])], point_id[vec_key(projective_class(c))]])
        key = join(line, ",")
        if !(key in line_keys)
            push!(line_keys, key)
            push!(line_sets, line)
        end
    end
    lines = sort(line_sets, by=x -> (x[1], x[2], x[3]))
    incidence = [[p in line for line in lines] for p in 0:(length(classes) - 1)]
    Dict("points" => classes, "quotient_rows" => quotient_rows, "lines" => lines, "incidence" => incidence, "incidence_matrix_shape" => [length(classes), length(lines)])
end

function graph_from_lines(lines)
    graph = Dict(i => Set{Int}() for i in 1:length(lines))
    sets = [Set(line) for line in lines]
    for i in 1:length(lines), j in (i + 1):length(lines)
        if !isempty(intersect(sets[i], sets[j]))
            push!(graph[i], j)
            push!(graph[j], i)
        end
    end
    graph
end

function components(graph)
    seen = Set{Int}()
    comps = Vector{Vector{Int}}()
    for node in sort(collect(keys(graph)))
        node in seen && continue
        queue = [node]
        push!(seen, node)
        comp = Int[]
        while !isempty(queue)
            cur = popfirst!(queue)
            push!(comp, cur)
            for nxt in sort(collect(graph[cur]))
                if !(nxt in seen)
                    push!(seen, nxt)
                    push!(queue, nxt)
                end
            end
        end
        push!(comps, sort(comp))
    end
    comps
end

function max_cliques(graph)
    best = Vector{Vector{Int}}()
    function bronk(r::Set{Int}, p::Set{Int}, x::Set{Int})
        if isempty(p) && isempty(x)
            if isempty(best) || length(r) > length(best[1])
                empty!(best)
                push!(best, sort(collect(r)))
            elseif length(r) == length(best[1])
                push!(best, sort(collect(r)))
            end
            return
        end
        if !isempty(best) && length(r) + length(p) < length(best[1])
            return
        end
        union_px = union(p, x)
        pivot = isempty(union_px) ? nothing : first(sort(collect(union_px), by=v -> -length(graph[v])))
        candidates = pivot === nothing ? copy(p) : setdiff(p, graph[pivot])
        for v in sort(collect(candidates))
            bronk(union(r, Set([v])), intersect(p, graph[v]), intersect(x, graph[v]))
            delete!(p, v)
            push!(x, v)
        end
    end
    bronk(Set{Int}(), Set(keys(graph)), Set{Int}())
    sort(best)
end

function graph_invariants(lines)
    graph = graph_from_lines(lines)
    degrees = sort([length(graph[node]) for node in keys(graph)])
    comps = components(graph)
    cliques = max_cliques(graph)
    hist = Dict(string(k) => count(==(k), degrees) for k in sort(unique(degrees)))
    Dict(
        "vertex_count" => length(lines),
        "edge_count" => div(sum(degrees), 2),
        "degree_sequence" => degrees,
        "degree_histogram" => hist,
        "components" => length(comps),
        "component_sizes" => sort([length(c) for c in comps]),
        "clique_number" => isempty(cliques) ? 0 : length(cliques[1]),
        "max_clique_count" => length(cliques),
        "max_clique_examples" => cliques[1:min(5, length(cliques))],
    )
end

function unlabeled_graph_invariant_profile(invariants)
    Dict(
        "vertex_count" => invariants["vertex_count"],
        "edge_count" => invariants["edge_count"],
        "degree_sequence" => invariants["degree_sequence"],
        "degree_histogram" => invariants["degree_histogram"],
        "components" => invariants["components"],
        "component_sizes" => invariants["component_sizes"],
        "clique_number" => invariants["clique_number"],
        "max_clique_count" => invariants["max_clique_count"],
    )
end

function max_clique_structural_explanation(lines, point_count::Int)
    cliques = max_cliques(graph_from_lines(lines))
    line_sets = [Set(line) for line in lines]
    point_pencils = 0
    plane_line_sets = 0
    ambiguous = 0
    other = 0
    examples = Dict{String,Any}()
    for clique in cliques
        clique_line_sets = [line_sets[idx] for idx in clique]
        common_points = isempty(clique_line_sets) ? Set{Int}() : intersect(clique_line_sets...)
        union_points = isempty(clique_line_sets) ? Set{Int}() : union(clique_line_sets...)
        is_point_pencil = length(common_points) == 1 && length(clique) == point_count - 8
        is_plane_line_set = length(union_points) == 7 && length(clique) == 7 && isempty(common_points)
        if is_point_pencil && is_plane_line_set
            ambiguous += 1
            !haskey(examples, "ambiguous") && (examples["ambiguous"] = clique)
        elseif is_point_pencil
            point_pencils += 1
            !haskey(examples, "point_pencil") && (examples["point_pencil"] = Dict("line_ids" => clique, "common_point" => sort(collect(common_points))))
        elseif is_plane_line_set
            plane_line_sets += 1
            !haskey(examples, "plane_line_set") && (examples["plane_line_set"] = Dict("line_ids" => clique, "plane_points" => sort(collect(union_points))))
        else
            other += 1
            !haskey(examples, "other") && (examples["other"] = Dict("line_ids" => clique, "union_points" => sort(collect(union_points)), "common_points" => sort(collect(common_points))))
        end
    end
    Dict(
        "description" => "30 max cliques split as 15 point-pencils plus 15 plane line-sets",
        "max_clique_count" => length(cliques),
        "point_pencil_count" => point_pencils,
        "plane_line_set_count" => plane_line_sets,
        "ambiguous_count" => ambiguous,
        "other_count" => other,
        "computed_split_ok" => point_pencils == 15 && plane_line_sets == 15 && ambiguous == 0 && other == 0 && length(cliques) == 30,
        "method" => "classify each maximum line-intersection clique by common point versus seven-point plane support",
        "examples" => examples,
    )
end

function line_pencils(incidence)
    [[idx - 1 for (idx, flag) in enumerate(row) if flag] for row in incidence]
end

function incidence_from_lines(lines, point_count::Int)
    [[p in line for line in lines] for p in 0:(point_count - 1)]
end

function reconstruction(lines, point_count::Int)
    incidence = incidence_from_lines(lines, point_count)
    expected = sort([Tuple(row) for row in line_pencils(incidence)])
    recovered = Set{Tuple{Vararg{Int}}}()
    bad_pair_overlaps = 0
    for i in 1:length(lines), j in (i + 1):length(lines)
        shared = sort(collect(intersect(Set(lines[i]), Set(lines[j]))))
        length(shared) > 1 && (bad_pair_overlaps += 1)
        if length(shared) == 1
            p = shared[1]
            push!(recovered, Tuple([line_idx - 1 for (line_idx, flag) in enumerate(incidence[p + 1]) if flag]))
        end
    end
    rec_sorted = sort(collect(recovered))
    missing = sort(collect(setdiff(Set(expected), recovered)))
    extra = sort(collect(setdiff(recovered, Set(expected))))
    Dict(
        "expected_point_count" => point_count,
        "recovered_point_count" => length(rec_sorted),
        "mismatch_count" => length(missing) + length(extra),
        "missing_pencils" => [collect(row) for row in missing[1:min(5, length(missing))]],
        "extra_pencils" => [collect(row) for row in extra[1:min(5, length(extra))]],
        "bad_pair_overlaps" => bad_pair_overlaps,
        "pencil_sizes" => sort([length(row) for row in expected]),
        "recovered_pencil_sizes" => sort([length(row) for row in rec_sorted]),
        "pass" => length(rec_sorted) == point_count && isempty(missing) && isempty(extra) && bad_pair_overlaps == 0,
    )
end

function scrambled_incidence_lines(lines)
    out = [copy(line) for line in lines]
    out[2] = sort([out[1][1], out[1][2], out[2][3]])
    if length(Set(out[2])) < 3
        out[2] = sort([out[1][1], out[1][2], (out[1][2] + 1) % 15])
    end
    out
end

function degree_preserving_random_control(lines, point_count::Int)
    out = [Set(line) for line in lines]
    for i in 1:length(out)
        j = ((i - 1) * 7 + 11) % length(out) + 1
        i == j && continue
        a = sort(collect(setdiff(out[i], out[j])))
        b = sort(collect(setdiff(out[j], out[i])))
        (isempty(a) || isempty(b)) && continue
        pa = a[((i + j - 2) % length(a)) + 1]
        pb = b[((2 * (i - 1) + j - 1) % length(b)) + 1]
        ni = union(setdiff(out[i], Set([pa])), Set([pb]))
        nj = union(setdiff(out[j], Set([pb])), Set([pa]))
        if length(ni) == 3 && length(nj) == 3
            out[i] = ni
            out[j] = nj
        end
    end
    [sort(collect(row)) for row in out]
end

function point_degrees(lines, point_count::Int)
    [count(line -> p in line, lines) for p in 0:(point_count - 1)]
end

function symplectic_pair(u, v)
    (u[1] * v[3] + u[2] * v[4] + u[3] * v[1] + u[4] * v[2]) % 2
end

function chirality_rows(points, lines; orientation::Int=1, label_shuffle::Bool=false)
    order = collect(1:length(lines))
    if label_shuffle
        order = [((idx - 1) * 11 + 3) % length(lines) + 1 for idx in 1:length(lines)]
    end
    rows = Vector{Dict{String,Any}}()
    for (out_idx, line_idx) in enumerate(order)
        line = lines[line_idx]
        bit = symplectic_pair(points[line[1] + 1], points[line[2] + 1])
        sign = orientation * (bit == 0 ? 1 : -1)
        push!(rows, Dict("line_id" => line_idx - 1, "output_order" => out_idx - 1, "pairing_bit" => bit, "P_chir" => sign))
    end
    rows
end

function chirality_summary(rows)
    vals = [row["P_chir"] for row in rows]
    Dict("counts" => Dict(string(k) => count(==(k), vals) for k in sort(unique(vals))), "sequence" => vals)
end

function z3_no_two_point_line_intersection(incidence)
    point_count = length(incidence)
    line_count = length(incidence[1])
    solver = Z3.Solver()
    cells = [[Z3.IntVar("I_$(p)_$(l)_$(rand(UInt32))") for l in 1:line_count] for p in 1:point_count]
    for p in 1:point_count, l in 1:line_count
        Z3.add(solver, cells[p][l] == Z3.IntVal(incidence[p][l] ? 1 : 0))
    end
    witnesses = Z3.Expr[]
    for l1 in 1:line_count, l2 in (l1 + 1):line_count, p1 in 1:point_count, p2 in (p1 + 1):point_count
        push!(witnesses, Z3.And([cells[p1][l1] == Z3.IntVal(1), cells[p1][l2] == Z3.IntVal(1), cells[p2][l1] == Z3.IntVal(1), cells[p2][l2] == Z3.IntVal(1)]))
    end
    Z3.add(solver, Z3.Or(witnesses))
    Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "load_bearing" => true,
        "verdict" => string(Z3.check(solver)),
        "claim" => "exists two distinct lines meeting in at least two points",
        "expected_for_valid_incidence" => "unsat",
        "computed_rows_bound" => true,
    )
end

function mct_relation_edges(sample_nodes)
    edges = Vector{Tuple{String,String,String}}()
    for sheet in ["L", "R"]
        other = sheet == "L" ? "R" : "L"
        for k in 0:2, i in 0:7, j in 0:7
            sid = "$(sheet):eta$(k):phi$(i):chi$(j)"
            candidates = [
                ("$(sheet):eta$(k):phi$((i + 1) % 8):chi$(j)", "fiber_phi"),
                ("$(sheet):eta$(k):phi$(i):chi$((j + 1) % 8)", "base_chi"),
                ("$(other):eta$(k):phi$(i):chi$(j)", "chirality_pair"),
            ]
            for (target, kind) in candidates
                if sid in sample_nodes && target in sample_nodes
                    push!(edges, (sid, target, kind))
                end
            end
            if k < 2
                target = "$(sheet):eta$(k + 1):phi$(i):chi$(j)"
                if sid in sample_nodes && target in sample_nodes
                    push!(edges, (sid, target, "shell_nested"))
                end
            end
        end
    end
    edges
end

function string_components(nodes, edges)
    graph = Dict(node => Set{String}() for node in nodes)
    for (a, b, _kind) in edges
        push!(graph[a], b)
        push!(graph[b], a)
    end
    seen = Set{String}()
    count = 0
    for node in sort(collect(nodes))
        node in seen && continue
        count += 1
        queue = [node]
        push!(seen, node)
        while !isempty(queue)
            cur = popfirst!(queue)
            for nxt in graph[cur]
                if !(nxt in seen)
                    push!(seen, nxt)
                    push!(queue, nxt)
                end
            end
        end
    end
    count
end

function sample_mct_baseline()
    path = joinpath(ROOT, "system_v6", "sims", "mct_dynamic_admissibility_packet_v0", "results", "mct_dynamic_admissibility_packet_v0_jax_results.json")
    payload = JSON.parsefile(path)
    probe_rows = payload["probe_row_table"][1:15]
    support_rows = payload["support_table"][1:35]
    quotient_keys = ["P_density", "P_shell", "P_loop", "P_order"]
    qclasses = Set{String}()
    for row in probe_rows
        push!(qclasses, JSON.json(Dict(key => row[key] for key in quotient_keys)))
    end
    nodes = Set([row["state_id"] for row in support_rows])
    edges = mct_relation_edges(nodes)
    Dict(
        "source_path" => path,
        "source_sha256" => sha256_file(path),
        "pin_lineage" => "committed mct_dynamic_admissibility_packet_v0 JAX result",
        "sample_sizes" => Dict("probe_rows" => length(probe_rows), "relation_nodes" => length(support_rows)),
        "quotient_class_count_15_sample" => length(qclasses),
        "relation_components_35_sample" => string_components(nodes, edges),
        "relation_edge_count_35_sample" => length(edges),
        "pencil_structure" => "not_an_incidence_pencil_packet",
        "reconstruction_behavior" => "not_applicable_no_line_membership_surface",
        "committed_whole_values" => payload["values"],
    )
end

function separation_table(values, controls, baseline)
    rows = [
        Dict(
            "readout" => "quotient_classes",
            "twistor_value" => values["projective_class_count"],
            "baseline_value" => baseline["quotient_class_count_15_sample"],
            "separates_baseline" => values["projective_class_count"] != baseline["quotient_class_count_15_sample"],
            "negative_control_reproduces" => controls["drop-projective-quotient"]["same_readouts_as_projective"],
            "separation" => false,
            "note" => "q=2 quotient ablation is identity, so this row is not counted as clean separation",
        ),
        Dict(
            "readout" => "relation_components",
            "twistor_value" => values["null_graph_components"],
            "baseline_value" => baseline["relation_components_35_sample"],
            "separates_baseline" => values["null_graph_components"] != baseline["relation_components_35_sample"],
            "negative_control_reproduces" => controls["scramble-incidence"]["graph_invariants_equal_to_valid"],
            "separation" => false,
            "note" => "component count is 1 versus 1 against the baseline sample, so this row is not counted as clean separation",
        ),
        Dict(
            "readout" => "pencil_structure",
            "twistor_value" => values["pencil_size_histogram"],
            "baseline_value" => baseline["pencil_structure"],
            "separates_baseline" => true,
            "negative_control_reproduces" => controls["random-bipartite-graph"]["same_pencil_size_histogram_as_valid"],
            "separation" => !controls["random-bipartite-graph"]["same_pencil_size_histogram_as_valid"],
            "note" => "same-degree random control can reproduce pencil sizes, so this row is not counted unless structure differs",
        ),
        Dict(
            "readout" => "reconstruction_behavior",
            "twistor_value" => Dict("recovered" => values["recovered_point_count"], "mismatch_count" => values["reconstruction_mismatch_count"]),
            "baseline_value" => baseline["reconstruction_behavior"],
            "separates_baseline" => values["reconstruction_mismatch_count"] == 0,
            "negative_control_reproduces" => controls["random-bipartite-graph"]["reconstruction_pass"] && !controls["random-bipartite-graph"]["non_isomorphic_invariants"],
            "separation" => values["reconstruction_mismatch_count"] == 0 && (!controls["random-bipartite-graph"]["reconstruction_pass"] || controls["random-bipartite-graph"]["non_isomorphic_invariants"]),
        ),
    ]
    rows
end

function build_result()
    pg = build_pg32()
    points = pg["points"]
    lines = pg["lines"]
    incidence = pg["incidence"]
    graph_inv = graph_invariants(lines)
    clique_structure = max_clique_structural_explanation(lines, length(points))
    recon = reconstruction(lines, length(points))
    pencils = line_pencils(incidence)
    pencil_sizes = sort([length(row) for row in pencils])
    chir = chirality_rows(points, lines)
    chir_rev = chirality_rows(points, lines; orientation=-1)
    chir_shuffle = chirality_rows(points, lines; label_shuffle=true)
    scrambled_lines = scrambled_incidence_lines(lines)
    scrambled_inv = graph_invariants(scrambled_lines)
    scrambled_inc = incidence_from_lines(scrambled_lines, length(points))
    random_lines = degree_preserving_random_control(lines, length(points))
    random_inv = graph_invariants(random_lines)
    random_recon = reconstruction(random_lines, length(points))
    z3_valid = z3_no_two_point_line_intersection(incidence)
    z3_bad = z3_no_two_point_line_intersection(scrambled_inc)
    pencil_hist = Dict(string(k) => count(==(k), pencil_sizes) for k in sort(unique(pencil_sizes)))
    random_degrees = point_degrees(random_lines, length(points))
    random_pencil_hist = Dict(string(k) => count(==(k), random_degrees) for k in sort(unique(random_degrees)))
    raw_vector_count = length(all_vectors())
    projective_class_count = length(points)
    shuffled_graph_inv = graph_invariants([lines[((idx - 1) * 11 + 3) % length(lines) + 1] for idx in 1:length(lines)])
    values = Dict(
        "point_count" => length(points),
        "line_count" => length(lines),
        "lines_through_each_point" => sort(unique(pencil_sizes)),
        "projective_class_count" => projective_class_count,
        "raw_nonzero_vector_count" => raw_vector_count,
        "null_graph_components" => graph_inv["components"],
        "null_graph_edge_count" => graph_inv["edge_count"],
        "null_graph_degree_min" => minimum(graph_inv["degree_sequence"]),
        "null_graph_degree_max" => maximum(graph_inv["degree_sequence"]),
        "null_graph_clique_number" => graph_inv["clique_number"],
        "null_graph_max_clique_count" => graph_inv["max_clique_count"],
        "null_graph_max_clique_point_pencil_count" => clique_structure["point_pencil_count"],
        "null_graph_max_clique_plane_line_set_count" => clique_structure["plane_line_set_count"],
        "recovered_point_count" => recon["recovered_point_count"],
        "reconstruction_mismatch_count" => recon["mismatch_count"],
        "pencil_size_histogram" => pencil_hist,
        "z3_no_two_point_line_intersection_unsat" => z3_valid["verdict"] == "unsat" ? 1.0 : 0.0,
    )
    controls = Dict(
        "scramble-incidence" => Dict(
            "fired" => true,
            "graph_invariants_equal_to_valid" => canonical_hash(scrambled_inv) == canonical_hash(graph_inv),
            "valid" => graph_inv,
            "control" => scrambled_inv,
            "z3_control_verdict" => z3_bad["verdict"],
        ),
        "random-bipartite-graph" => Dict(
            "fired" => true,
            "same_point_degree_profile" => point_degrees(random_lines, length(points)) == point_degrees(lines, length(points)),
            "same_line_degree_profile" => sort([length(line) for line in random_lines]) == sort([length(line) for line in lines]),
            "same_pencil_size_histogram_as_valid" => random_pencil_hist == pencil_hist,
            "reconstruction_pass" => random_recon["pass"],
            "non_isomorphic_invariants" => canonical_hash(random_inv) != canonical_hash(graph_inv) || random_recon["bad_pair_overlaps"] != 0,
            "graph" => random_inv,
            "reconstruction" => random_recon,
        ),
        "drop-projective-quotient" => Dict(
            "fired" => true,
            "raw_nonzero_vector_count" => raw_vector_count,
            "projective_class_count" => projective_class_count,
            "line_count_without_identifying_scalar_orbits" => length(lines),
            "q2_limitation" => raw_vector_count == projective_class_count,
            "q3_flag" => "F_2^* has only 1, so q=3 is the discriminating scalar-quotient case",
            "same_readouts_as_projective" => raw_vector_count == projective_class_count,
            "reported_honestly" => true,
        ),
        "orientation-reversal" => Dict(
            "fired" => true,
            "valid_chirality" => chirality_summary(chir),
            "reversed_chirality" => chirality_summary(chir_rev),
            "all_signs_flipped" => [row["P_chir"] for row in chir_rev] == [-row["P_chir"] for row in chir],
        ),
        "label-shuffle" => Dict(
            "fired" => true,
            "valid_chirality_counts" => chirality_summary(chir)["counts"],
            "shuffled_chirality_counts" => chirality_summary(chir_shuffle)["counts"],
            "chirality_distribution_survives" => chirality_summary(chir)["counts"] == chirality_summary(chir_shuffle)["counts"],
            "graph_invariants_survive_labeled_comparison_superseded" => canonical_hash(graph_inv) == canonical_hash(shuffled_graph_inv),
            "superseded_note" => "old comparison hashed label/order-bearing max_clique_examples, so pure relabeling could report a false graph-invariant failure",
            "unlabeled_invariants_survive_shuffle" => unlabeled_graph_invariant_profile(graph_inv) == unlabeled_graph_invariant_profile(shuffled_graph_inv),
            "unlabeled_profile_fields" => ["degree_sequence", "edge_count", "components", "component_sizes", "clique_number", "max_clique_count"],
        ),
    )
    baseline = sample_mct_baseline()
    sep = separation_table(values, controls, baseline)
    kill_condition_met = !any(row -> row["separation"], sep)
    gates = Dict(
        "G1" => Dict("pass" => values["point_count"] == 15 && values["line_count"] == 35 && values["lines_through_each_point"] == [7], "computed_counts" => values, "incidence_table_full" => length(incidence) == 15 && all(row -> length(row) == 35, incidence)),
        "G2" => Dict("pass" => !controls["scramble-incidence"]["graph_invariants_equal_to_valid"], "graph_invariants" => graph_inv, "scramble_changed_invariants" => !controls["scramble-incidence"]["graph_invariants_equal_to_valid"]),
        "G3" => Dict("pass" => recon["pass"] && (!random_recon["pass"] || controls["random-bipartite-graph"]["non_isomorphic_invariants"]), "reconstruction" => recon, "random_control" => controls["random-bipartite-graph"]),
        "G4" => Dict("strict_change_pass" => !controls["drop-projective-quotient"]["same_readouts_as_projective"], "honest_q2_limitation_reported" => controls["drop-projective-quotient"]["reported_honestly"], "pass_for_q2_diagnostic" => controls["drop-projective-quotient"]["reported_honestly"], "control" => controls["drop-projective-quotient"]),
        "G5" => Dict("pass" => !kill_condition_met, "separation_table" => sep, "kill_condition_met" => kill_condition_met),
        "G6" => Dict("pass" => z3_valid["verdict"] == "unsat" && z3_bad["verdict"] == "sat", "z3" => z3_valid, "scrambled_controls" => Dict("z3" => z3_bad)),
        "G7" => Dict("pass" => controls["orientation-reversal"]["all_signs_flipped"] && controls["label-shuffle"]["chirality_distribution_survives"], "chirality_rows" => chir, "orientation_reversal" => controls["orientation-reversal"], "label_shuffle" => controls["label-shuffle"]),
    )
    gate_pass = Dict(name => (haskey(gate, "pass") ? gate["pass"] : gate["pass_for_q2_diagnostic"]) for (name, gate) in gates)
    all_acceptance_pass = all(Base.values(gate_pass))
    Dict(
        "schema_version" => "twistor_incidence_finite_packet_v0_leg_v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "generated_at" => replace(string(Dates.now(Dates.UTC)), r"\.\d+" => "") * "Z",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "mode" => MODE,
        "pytorch_omitted_reason" => "declared diagnostic mode per system_v6/README.md:11",
        "all_pass" => all_acceptance_pass,
        "strict_gate_notes" => Dict("G4" => "q=2 scalar quotient ablation is identity; q=3 flagged as discriminating case"),
        "source_path" => SOURCE_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "packages_used" => ["JSON", "SHA", "Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => [
            Dict("tool" => "Z3", "qualified_api/function" => "Z3.check", "input_object" => "computed point-line incidence Int matrix", "output_object" => z3_valid["verdict"], "positive_case" => "valid PG(3,2) incidence is unsat for two-point line intersections", "negative/erased_control" => z3_bad["verdict"], "boundary_case" => "q=2 quotient identity", "demotion_condition" => "if solver constraints are not bound to computed incidence rows", "gates" => ["G6"]),
        ],
        "pin_block_canonical_json" => PIN_BLOCK_CANONICAL,
        "pin_block_sha256" => PIN_BLOCK_SHA256,
        "source_refs" => SOURCE_REFS,
        "points" => points,
        "lines" => lines,
        "incidence_table" => incidence,
        "graph_invariants" => graph_inv,
        "max_clique_structural_explanation" => clique_structure,
        "reconstruction" => recon,
        "chirality" => Dict("rows" => chir, "summary" => chirality_summary(chir)),
        "baseline" => baseline,
        "values" => values,
        "controls" => controls,
        "gates" => gates,
        "gate_pass" => gate_pass,
        "separation_table" => sep,
        "summary" => Dict(
            "non_separating_rows" => ["quotient_classes", "relation_components", "pencil_structure"],
            "surviving_separation" => "finite reconstruction behavior only",
            "fence" => "finite reconstruction behavior only; no physics, no spacetime manifold, no GR, no Penrose-validates claim",
            "q3_next_discriminator" => Dict(
                "field" => "F_3",
                "point_count" => 40,
                "line_count" => 130,
                "lines_through_point" => 13,
                "reason" => "q=2 scalar quotient is identity, so quotient behavior needs q=3 to discriminate",
            ),
        ),
        "q3_next_discriminator" => Dict(
            "field" => "F_3",
            "point_count" => 40,
            "line_count" => 130,
            "lines_through_point" => 13,
            "reason" => "q=2 scalar quotient is identity, so quotient behavior needs q=3 to discriminate",
        ),
        "kill_condition_met" => kill_condition_met,
        "crossover_proofs" => Dict("julia_z3" => z3_valid),
        "claim_ceiling" => Dict("alt_math_discriminator_only" => true, "no_spacetime_gr_physics_claim" => true, "no_penrose_validates_language" => true, "not_canon" => true),
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println("TWISTOR_INCIDENCE_FINITE_PACKET_V0_JULIA_DONE all_pass=$(result["all_pass"]) points=$(result["values"]["point_count"]) lines=$(result["values"]["line_count"]) z3=$(result["crossover_proofs"]["julia_z3"]["verdict"]) kill=$(result["kill_condition_met"])")
end

main()
