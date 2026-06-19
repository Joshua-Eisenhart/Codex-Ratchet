#!/usr/bin/env julia

using Dates
using JSON
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s1_q4_finite_incidence_v0"
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
const Q = 4
const NONZERO_SCALARS = [1, 2, 3]
const SEEDS = Dict("finite_enumeration" => "deterministic_lexicographic", "scramble_control" => "deterministic_line_replacement_v1")
const PIN_BLOCK_CANONICAL = "{\"comparison_anchor_q2\":\"system_v6/sims/twistor_incidence_finite_packet_v0\",\"comparison_anchor_q3\":\"system_v6/sims/geo_s1_q3_finite_incidence_v0\",\"engine_mode\":\"julia_canon_plus_jax_diagnostic\",\"expected_counts\":{\"line_graph_degree\":100,\"line_graph_edges\":17850,\"lines\":357,\"lines_per_plane\":21,\"lines_through_point\":21,\"planes\":85,\"points\":85,\"points_per_line\":5,\"points_per_plane\":21,\"raw_nonzero_vectors\":255},\"field\":\"GF(4)\",\"field_model\":\"galois.GF(4), primitive polynomial x^2 + x + 1; integer labels 0,1,alpha,alpha+1\",\"object\":\"PG(3,4)\",\"probe_families\":[\"P_proj_q4\",\"P_inc_q4\",\"P_plane_q4\",\"P_null_q4\",\"P_recon_q4\",\"P_frobenius_q4\"],\"projective_quotient\":\"nonzero vectors of GF(4)^4 modulo GF(4)^*={1,alpha,alpha+1}; exact classes computed with galois.GF(4)\",\"q\":4}"
const PIN_BLOCK_SHA256 = bytes2hex(sha256(PIN_BLOCK_CANONICAL))

const TOOL_MANIFEST = Dict(
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result and q=2/q=3 anchor parsing"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source/result/PIN hashing"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing SMT polarity check over computed pair-line counts with scrambled SAT control"),
    "julia_gf4_stdlib" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent GF(4) arithmetic, quotient, row reduction, span construction, and Frobenius boundary"),
)
const TOOL_INTEGRATION_DEPTH = Dict("JSON" => "supportive", "SHA" => "supportive", "Z3" => "load_bearing", "julia_gf4_stdlib" => "load_bearing")

function sha256_file(path::String)
    bytes2hex(open(sha256, path))
end

gf4_add(a::Int, b::Int) = xor(a, b)

function gf4_mul(a::Int, b::Int)
    a0 = a & 1
    a1 = (a >> 1) & 1
    b0 = b & 1
    b1 = (b >> 1) & 1
    c0 = a0 * b0
    c1 = xor(a0 * b1, a1 * b0)
    c2 = a1 * b1
    # alpha^2 = alpha + 1, so c2*alpha^2 contributes c2 to both coefficients.
    r0 = xor(c0, c2)
    r1 = xor(c1, c2)
    r0 + 2 * r1
end

function gf4_pow2(a::Int)
    gf4_mul(a, a)
end

function gf4_inv(a::Int)
    a == 0 && error("zero has no inverse in GF(4)")
    for b in NONZERO_SCALARS
        gf4_mul(a, b) == 1 && return b
    end
    error("no inverse found")
end

function gf4_vec_scalar_mul(s::Int, v::Vector{Int})
    [gf4_mul(s, x) for x in v]
end

function gf4_vec_add(a::Vector{Int}, b::Vector{Int})
    [gf4_add(a[i], b[i]) for i in eachindex(a)]
end

function gf4_vec_add_scaled(acc::Vector{Int}, coeff::Int, vec::Vector{Int})
    gf4_vec_add(acc, gf4_vec_scalar_mul(coeff, vec))
end

function vec_key(v::Vector{Int})
    join(v, ",")
end

function projective_class(v::Vector{Int})
    all(x -> x == 0, v) && error("zero vector has no projective class")
    orbit = [gf4_vec_scalar_mul(s, v) for s in NONZERO_SCALARS]
    sort(orbit, by=vec_key)[1]
end

function all_nonzero_vectors()
    out = Vector{Vector{Int}}()
    for a in 0:3, b in 0:3, c in 0:3, d in 0:3
        v = [a, b, c, d]
        any(x -> x != 0, v) && push!(out, v)
    end
    out
end

function rank_gf4(rows::Vector{Vector{Int}})
    m = length(rows)
    n = length(rows[1])
    mat = zeros(Int, m, n)
    for i in 1:m, j in 1:n
        mat[i, j] = rows[i][j]
    end
    r = 1
    for c in 1:n
        pivot = findfirst(i -> mat[i, c] != 0, r:m)
        pivot === nothing && continue
        p = pivot + r - 1
        mat[r, :], mat[p, :] = copy(mat[p, :]), copy(mat[r, :])
        inv = gf4_inv(mat[r, c])
        mat[r, :] = [gf4_mul(inv, x) for x in mat[r, :]]
        for i in 1:m
            i == r && continue
            factor = mat[i, c]
            factor == 0 && continue
            scaled = [gf4_mul(factor, x) for x in mat[r, :]]
            mat[i, :] = [gf4_add(mat[i, j], scaled[j]) for j in 1:n]
        end
        r += 1
        r > m && break
    end
    r - 1
end

function span_projective_points(basis::Vector{Vector{Int}})
    classes = Dict{String,Vector{Int}}()
    ranges = ntuple(_ -> 0:(Q - 1), length(basis))
    for coeffs in Iterators.product(ranges...)
        any(!=(0), coeffs) || continue
        vec = [0, 0, 0, 0]
        for (coeff, base) in zip(coeffs, basis)
            vec = gf4_vec_add_scaled(vec, coeff, base)
        end
        cls = projective_class(vec)
        classes[vec_key(cls)] = cls
    end
    sort(collect(values(classes)), by=vec_key)
end

function build_pg34()
    raw = all_nonzero_vectors()
    class_map = Dict(vec_key(projective_class(v)) => projective_class(v) for v in raw)
    points = sort(collect(values(class_map)), by=vec_key)
    point_id = Dict(vec_key(p) => idx - 1 for (idx, p) in enumerate(points))
    quotient_rows = [
        Dict(
            "raw_vector" => v,
            "projective_class" => projective_class(v),
            "class_id" => point_id[vec_key(projective_class(v))],
            "scalar_orbit" => [gf4_vec_scalar_mul(s, v) for s in NONZERO_SCALARS],
        )
        for v in raw
    ]

    line_map = Dict{String,Vector{Int}}()
    for i in 1:length(points), j in (i + 1):length(points)
        rank_gf4([points[i], points[j]]) == 2 || continue
        line = sort([point_id[vec_key(p)] for p in span_projective_points([points[i], points[j]])])
        line_map[join(line, ",")] = line
    end
    lines = sort(collect(values(line_map)), by=x -> join(x, ","))

    plane_map = Dict{String,Vector{Int}}()
    for i in 1:length(points), j in (i + 1):length(points), k in (j + 1):length(points)
        rank_gf4([points[i], points[j], points[k]]) == 3 || continue
        plane = sort([point_id[vec_key(p)] for p in span_projective_points([points[i], points[j], points[k]])])
        plane_map[join(plane, ",")] = plane
    end
    planes = sort(collect(values(plane_map)), by=x -> join(x, ","))
    incidence = [[p in line for line in lines] for p in 0:(length(points) - 1)]
    plane_incidence = [[p in plane for plane in planes] for p in 0:(length(points) - 1)]
    Dict("points" => points, "quotient_rows" => quotient_rows, "lines" => lines, "planes" => planes, "incidence" => incidence, "plane_incidence" => plane_incidence)
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
            for nxt in graph[cur]
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

function graph_invariants(lines)
    graph = graph_from_lines(lines)
    degrees = sort([length(graph[node]) for node in keys(graph)])
    comps = components(graph)
    Dict(
        "vertex_count" => length(lines),
        "edge_count" => div(sum(degrees), 2),
        "degree_sequence" => degrees,
        "degree_histogram" => Dict(string(k) => count(==(k), degrees) for k in sort(unique(degrees))),
        "components" => length(comps),
        "component_sizes" => sort([length(c) for c in comps]),
        "degree_formula" => "(q+1)*(q^2+q) = 5*20 = 100",
        "edge_formula" => "357*100/2 = 17850",
    )
end

function line_pencils(incidence)
    [[idx - 1 for (idx, flag) in enumerate(row) if flag] for row in incidence]
end

function line_sets_in_planes(lines, planes)
    line_sets = [Set(line) for line in lines]
    [[idx - 1 for (idx, line) in enumerate(line_sets) if issubset(line, Set(plane))] for plane in planes]
end

function clique_family_check(lines, planes, incidence)
    graph0 = graph_from_lines(lines)
    graph = Dict(k - 1 => Set([v - 1 for v in vals]) for (k, vals) in graph0)
    stars = line_pencils(incidence)
    plane_line_sets = line_sets_in_planes(lines, planes)
    function is_clique(items)
        for i in 1:length(items), j in (i + 1):length(items)
            items[j] in graph[items[i]] || return false
        end
        true
    end
    star_sizes = sort([length(row) for row in stars])
    plane_line_sizes = sort([length(row) for row in plane_line_sets])
    unique_cliques = Set([Tuple(row) for row in vcat(stars, plane_line_sets)])
    Dict(
        "clique_number_structural" => Q^2 + Q + 1,
        "max_clique_count_structural" => length(unique_cliques),
        "point_star_count" => length(stars),
        "plane_line_set_count" => length(plane_line_sets),
        "point_star_sizes" => star_sizes,
        "plane_line_set_sizes" => plane_line_sizes,
        "all_point_stars_are_cliques" => all(is_clique, stars),
        "all_plane_line_sets_are_cliques" => all(is_clique, plane_line_sets),
        "unique_star_or_plane_clique_count" => length(unique_cliques),
        "computed_split_ok" => length(stars) == 85 && length(plane_line_sets) == 85 && length(unique_cliques) == 170 && star_sizes == fill(21, 85) && plane_line_sizes == fill(21, 85) && all(is_clique, stars) && all(is_clique, plane_line_sets),
        "method" => "construct all point-stars and all plane line-sets; verify each is a 21-line clique in the line-intersection graph",
    )
end

function pair_line_counts(lines, point_count::Int)
    counts = Dict((a, b) => 0 for a in 0:(point_count - 1) for b in (a + 1):(point_count - 1))
    for line in lines
        for a_i in 1:length(line), b_i in (a_i + 1):length(line)
            pair = (min(line[a_i], line[b_i]), max(line[a_i], line[b_i]))
            counts[pair] += 1
        end
    end
    counts
end

function incidence_from_lines(lines, point_count::Int)
    [[p in line for line in lines] for p in 0:(point_count - 1)]
end

function reconstruction(lines, point_count::Int)
    incidence = incidence_from_lines(lines, point_count)
    expected = Set([Tuple(row) for row in line_pencils(incidence)])
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
    missing = setdiff(expected, recovered)
    extra = setdiff(recovered, expected)
    Dict(
        "expected_point_count" => point_count,
        "recovered_point_count" => length(recovered),
        "mismatch_count" => length(missing) + length(extra),
        "bad_pair_overlaps" => bad_pair_overlaps,
        "pencil_sizes" => sort([length(row) for row in expected]),
        "recovered_pencil_sizes" => sort([length(row) for row in recovered]),
        "pass" => length(recovered) == point_count && isempty(missing) && isempty(extra) && bad_pair_overlaps == 0,
    )
end

function scrambled_incidence_lines(lines, point_count::Int)
    out = [copy(line) for line in lines]
    candidates = [p for p in 0:(point_count - 1) if !(p in out[1])][1:3]
    out[2] = sort([out[1][1], out[1][2], candidates...])
    out
end

function z3_pair_uniqueness(counts)
    solver = Z3.Solver()
    witnesses = [Z3.Not(Z3.IntVal(value) == Z3.IntVal(1)) for value in values(counts)]
    Z3.add(solver, Z3.Or(witnesses))
    Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "load_bearing" => true,
        "verdict" => string(Z3.check(solver)),
        "claim" => "exists a point pair whose computed incident-line count is not exactly one",
        "expected_for_valid_incidence" => "unsat",
        "computed_rows_bound" => true,
    )
end

function frobenius_boundary(points, lines, incidence)
    point_id = Dict(vec_key(p) => idx - 1 for (idx, p) in enumerate(points))
    function frob_vec(v)
        [gf4_pow2(x) for x in v]
    end
    frob_point_image = Dict(idx - 1 => point_id[vec_key(projective_class(frob_vec(p)))] for (idx, p) in enumerate(points))
    image_values = sort(collect(values(frob_point_image)))
    line_sets = Set([Tuple(line) for line in lines])
    line_images = Vector{Vector{Int}}()
    for line in lines
        push!(line_images, sort([frob_point_image[p] for p in line]))
    end
    incidence_preserved = true
    for (p_idx0, row) in enumerate(incidence)
        p_idx = p_idx0 - 1
        mapped_p = frob_point_image[p_idx]
        for (line_idx, flag) in enumerate(row)
            mapped_line = line_images[line_idx]
            incidence_preserved = incidence_preserved && ((mapped_p in mapped_line) == flag)
        end
    end
    moved_points = count(kv -> kv.first != kv.second, collect(frob_point_image))
    involution = all(frob_point_image[frob_point_image[idx]] == idx for idx in keys(frob_point_image))
    line_perm = Set([Tuple(row) for row in line_images]) == line_sets
    Dict(
        "map" => "coordinatewise Frobenius x -> x^2 over GF(4)",
        "field_label_squares" => Dict(string(x) => gf4_pow2(x) for x in 0:3),
        "point_permutation" => image_values == collect(0:(length(points) - 1)),
        "line_permutation" => line_perm,
        "incidence_preserved" => incidence_preserved,
        "nontrivial_on_projective_points" => moved_points > 0,
        "moved_projective_point_count" => moved_points,
        "involution_on_points" => involution,
        "boundary_case" => "char-2 Frobenius is nontrivial for GF(4), unlike prime-field q=2/q=3 rows",
        "pass" => image_values == collect(0:(length(points) - 1)) && line_perm && incidence_preserved && moved_points > 0 && involution,
    )
end

function load_anchor_q2()
    path = joinpath(ROOT, "system_v6", "sims", "twistor_incidence_finite_packet_v0", "results", "twistor_incidence_finite_packet_v0_envelope_results.json")
    payload = JSON.parsefile(path)
    values = payload["divergence"]["engine_values"]["jax"]
    Dict(
        "source_path" => path,
        "source_sha256" => sha256_file(path),
        "q" => 2,
        "raw_nonzero_vector_count" => values["raw_nonzero_vector_count"],
        "projective_class_count" => values["projective_class_count"],
        "point_count" => values["point_count"],
        "line_count" => values["line_count"],
        "null_graph_edge_count" => values["null_graph_edge_count"],
        "null_graph_degree" => values["null_graph_degree_min"],
        "recovered_point_count" => values["recovered_point_count"],
        "reconstruction_mismatch_count" => values["reconstruction_mismatch_count"],
        "surviving_separation" => payload["summary"]["surviving_separation"],
    )
end

function load_anchor_q3()
    path = joinpath(ROOT, "system_v6", "sims", "geo_s1_q3_finite_incidence_v0", "results", "geo_s1_q3_finite_incidence_v0_envelope_results.json")
    payload = JSON.parsefile(path)
    values = payload["divergence"]["engine_values"]["jax"]
    Dict(
        "source_path" => path,
        "source_sha256" => sha256_file(path),
        "q" => 3,
        "raw_nonzero_vector_count" => values["raw_nonzero_vector_count"],
        "projective_class_count" => values["projective_class_count"],
        "point_count" => values["point_count"],
        "line_count" => values["line_count"],
        "null_graph_edge_count" => values["null_graph_edge_count"],
        "null_graph_degree" => values["null_graph_degree_min"],
        "recovered_point_count" => values["recovered_point_count"],
        "reconstruction_mismatch_count" => values["reconstruction_mismatch_count"],
        "surviving_separation" => payload["summary"]["surviving_separation"],
    )
end

function build_result()
    pg = build_pg34()
    points = pg["points"]
    lines = pg["lines"]
    planes = pg["planes"]
    incidence = pg["incidence"]
    graph_inv = graph_invariants(lines)
    clique_check = clique_family_check(lines, planes, incidence)
    recon = reconstruction(lines, length(points))
    pair_counts = pair_line_counts(lines, length(points))
    scrambled_lines = scrambled_incidence_lines(lines, length(points))
    scrambled_counts = pair_line_counts(scrambled_lines, length(points))
    z3_valid = z3_pair_uniqueness(pair_counts)
    z3_bad = z3_pair_uniqueness(scrambled_counts)
    frob = frobenius_boundary(points, lines, incidence)
    q2_anchor = load_anchor_q2()
    q3_anchor = load_anchor_q3()
    pencil_sizes = sort([length(row) for row in line_pencils(incidence)])
    plane_line_sizes = sort([length(row) for row in line_sets_in_planes(lines, planes)])
    values_row = Dict(
        "raw_nonzero_vector_count" => length(pg["quotient_rows"]),
        "projective_class_count" => length(points),
        "point_count" => length(points),
        "line_count" => length(lines),
        "plane_count" => length(planes),
        "points_per_line_min" => minimum([length(line) for line in lines]),
        "points_per_line_max" => maximum([length(line) for line in lines]),
        "lines_through_point_min" => minimum(pencil_sizes),
        "lines_through_point_max" => maximum(pencil_sizes),
        "points_per_plane_min" => minimum([length(plane) for plane in planes]),
        "points_per_plane_max" => maximum([length(plane) for plane in planes]),
        "lines_per_plane_min" => minimum(plane_line_sizes),
        "lines_per_plane_max" => maximum(plane_line_sizes),
        "pair_count" => length(pair_counts),
        "pair_line_count_min" => minimum(collect(values(pair_counts))),
        "pair_line_count_max" => maximum(collect(values(pair_counts))),
        "null_graph_components" => graph_inv["components"],
        "null_graph_edge_count" => graph_inv["edge_count"],
        "null_graph_degree_min" => minimum(graph_inv["degree_sequence"]),
        "null_graph_degree_max" => maximum(graph_inv["degree_sequence"]),
        "null_graph_clique_number" => clique_check["clique_number_structural"],
        "null_graph_max_clique_count" => clique_check["max_clique_count_structural"],
        "null_graph_max_clique_point_pencil_count" => clique_check["point_star_count"],
        "null_graph_max_clique_plane_line_set_count" => clique_check["plane_line_set_count"],
        "recovered_point_count" => recon["recovered_point_count"],
        "reconstruction_mismatch_count" => recon["mismatch_count"],
        "frobenius_moved_projective_point_count" => frob["moved_projective_point_count"],
        "z3_pair_uniqueness_unsat" => z3_valid["verdict"] == "unsat" ? 1.0 : 0.0,
    )
    raw_to_projective_ratio = values_row["raw_nonzero_vector_count"] / values_row["projective_class_count"]
    q2_ratio = q2_anchor["raw_nonzero_vector_count"] / q2_anchor["projective_class_count"]
    q3_ratio = q3_anchor["raw_nonzero_vector_count"] / q3_anchor["projective_class_count"]
    controls = Dict(
        "drop-projective-quotient" => Dict(
            "fired" => true,
            "raw_nonzero_vector_count" => values_row["raw_nonzero_vector_count"],
            "projective_class_count" => values_row["projective_class_count"],
            "raw_to_projective_ratio" => raw_to_projective_ratio,
            "same_readouts_as_projective" => values_row["raw_nonzero_vector_count"] == values_row["projective_class_count"],
            "q4_discriminator_fired" => values_row["raw_nonzero_vector_count"] == 3 * values_row["projective_class_count"],
            "strictly_stronger_than_q3" => raw_to_projective_ratio > q3_ratio > q2_ratio,
        ),
        "scramble-incidence" => Dict(
            "fired" => true,
            "pair_line_count_min" => minimum(collect(values(scrambled_counts))),
            "pair_line_count_max" => maximum(collect(values(scrambled_counts))),
            "z3_control_verdict" => z3_bad["verdict"],
            "control_fired" => z3_bad["verdict"] == "sat",
        ),
        "frobenius-boundary" => frob,
    )
    separation_table = [
        Dict("readout" => "projective_scalar_quotient", "q2_value" => Dict("raw_nonzero_vectors" => q2_anchor["raw_nonzero_vector_count"], "projective_classes" => q2_anchor["projective_class_count"], "raw_to_projective_ratio" => q2_ratio), "q3_value" => Dict("raw_nonzero_vectors" => q3_anchor["raw_nonzero_vector_count"], "projective_classes" => q3_anchor["projective_class_count"], "raw_to_projective_ratio" => q3_ratio), "q4_value" => Dict("raw_nonzero_vectors" => values_row["raw_nonzero_vector_count"], "projective_classes" => values_row["projective_class_count"], "raw_to_projective_ratio" => raw_to_projective_ratio), "status_vs_q3" => raw_to_projective_ratio > q3_ratio ? "strengthens" : "weakens_or_flat", "separation" => controls["drop-projective-quotient"]["q4_discriminator_fired"], "note" => "q=4 is the first non-prime-field scalar quotient row; each projective point has three raw representatives."),
        Dict("readout" => "reconstruction_behavior", "q2_value" => Dict("recovered" => q2_anchor["recovered_point_count"], "mismatch_count" => q2_anchor["reconstruction_mismatch_count"]), "q3_value" => Dict("recovered" => q3_anchor["recovered_point_count"], "mismatch_count" => q3_anchor["reconstruction_mismatch_count"]), "q4_value" => Dict("recovered" => recon["recovered_point_count"], "mismatch_count" => recon["mismatch_count"]), "status_vs_q3" => recon["pass"] && recon["recovered_point_count"] > q3_anchor["recovered_point_count"] ? "strengthens" : "weakens_or_fails", "separation" => recon["pass"], "note" => "point-star reconstruction persists with zero mismatch and grows from q=2 count 15 to q=3 count 40 to q=4 count 85."),
        Dict("readout" => "line_intersection_graph_scale", "q2_value" => Dict("points" => q2_anchor["point_count"], "lines" => q2_anchor["line_count"], "degree" => q2_anchor["null_graph_degree"], "edges" => q2_anchor["null_graph_edge_count"]), "q3_value" => Dict("points" => q3_anchor["point_count"], "lines" => q3_anchor["line_count"], "degree" => q3_anchor["null_graph_degree"], "edges" => q3_anchor["null_graph_edge_count"]), "q4_value" => Dict("points" => values_row["point_count"], "lines" => values_row["line_count"], "degree" => values_row["null_graph_degree_min"], "edges" => values_row["null_graph_edge_count"]), "status_vs_q3" => values_row["line_count"] > q3_anchor["line_count"] && values_row["null_graph_degree_min"] > q3_anchor["null_graph_degree"] ? "strengthens" : "weakens_or_flat", "separation" => values_row["line_count"] == 357 && values_row["null_graph_degree_min"] == 100, "note" => "the incidence/intersection graph remains regular and connected over GF(4); this is a scale/invariant row, not a physics/null-light claim."),
        Dict("readout" => "char2_frobenius_boundary", "q2_value" => "prime field; Frobenius is identity on field elements", "q3_value" => "prime field; Frobenius x^3 is identity on field elements", "q4_value" => Dict("moved_projective_points" => frob["moved_projective_point_count"], "incidence_preserved" => frob["incidence_preserved"], "line_permutation" => frob["line_permutation"]), "status_vs_q3" => "new_boundary_not_like_for_like_strength", "separation" => frob["pass"], "note" => "GF(4) has nontrivial char-2 Frobenius x->x^2; it moves projective points while preserving incidence."),
    ]
    gates = Dict(
        "G1_pg34_counts" => Dict("pass" => values_row["point_count"] == 85 && values_row["line_count"] == 357 && values_row["plane_count"] == 85 && values_row["points_per_line_min"] == values_row["points_per_line_max"] == 5 && values_row["lines_through_point_min"] == values_row["lines_through_point_max"] == 21 && values_row["lines_per_plane_min"] == values_row["lines_per_plane_max"] == 21, "values" => values_row),
        "G2_pair_line_uniqueness" => Dict("pass" => values_row["pair_line_count_min"] == values_row["pair_line_count_max"] == 1, "z3" => z3_valid, "scrambled_controls" => Dict("z3" => z3_bad)),
        "G3_graph_invariants" => Dict("pass" => graph_inv["vertex_count"] == 357 && graph_inv["edge_count"] == 17850 && graph_inv["components"] == 1 && minimum(graph_inv["degree_sequence"]) == maximum(graph_inv["degree_sequence"]) == 100, "graph_invariants" => graph_inv, "clique_family_check" => clique_check),
        "G4_projective_quotient_boundary" => Dict("pass" => controls["drop-projective-quotient"]["q4_discriminator_fired"] && controls["drop-projective-quotient"]["strictly_stronger_than_q3"], "control" => controls["drop-projective-quotient"]),
        "G5_reconstruction_separation" => Dict("pass" => recon["pass"] && any(row -> row["readout"] == "reconstruction_behavior" && row["status_vs_q3"] == "strengthens", separation_table), "reconstruction" => recon, "separation_table" => separation_table),
        "G6_frobenius_boundary" => Dict("pass" => frob["pass"], "frobenius" => frob),
    )
    all_pass = all(row -> row["pass"], values(gates)) && controls["scramble-incidence"]["control_fired"]
    Dict(
        "schema_version" => "geo_s1_q4_finite_incidence_v0_leg_v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "generated_at" => replace(string(Dates.now(Dates.UTC)), r"\.\d+" => "") * "Z",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "mode" => MODE,
        "pytorch_omitted_reason" => "declared diagnostic mode; no graph/network/autograd claim path",
        "seeds" => SEEDS,
        "all_pass" => all_pass,
        "source_path" => SOURCE_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "packages_used" => ["JSON", "SHA", "Z3", "julia_gf4_stdlib"],
        "aligned_packages_load_bearing" => ["Z3", "julia_gf4_stdlib"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => [
            Dict(
                "tool" => "julia_gf4_stdlib",
                "qualified_api" => "geo_s1_q4_finite_incidence_v0_julia.gf4_add/gf4_mul/gf4_inv/rank_gf4/span_projective_points/projective_class/frobenius_boundary",
                "input_object" => "integer-labeled GF(4)^4 vectors with alpha^2 = alpha + 1 and GF(4)^* scalar orbits",
                "output_object" => "quotient-canonical PG(3,4) points, lines, planes, reconstruction, graph invariants, and Frobenius images",
                "positive_case" => "85 points, 357 lines, 85 planes, pair-line count 1/1, reconstruction mismatch 0, Frobenius incidence preserved",
                "negative_control" => "drop-projective-quotient raw/projective ratio 255/85 = 3.0 and scrambled-incidence pair-line min/max 0/2",
                "boundary_case" => "non-prime-field GF(4) char-2 Frobenius x -> x^2 moves 70 projective points while preserving incidence",
                "demotion_condition" => "if GF(4) arithmetic is replaced by integer mod-4 arithmetic or spans are not quotient-canonicalized by GF(4)^*",
                "gates" => ["G1_pg34_counts", "G3_graph_invariants", "G4_projective_quotient_boundary", "G5_reconstruction_separation", "G6_frobenius_boundary"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api" => "Z3.Solver/Z3.IntVal/Z3.Not/Z3.Or/Z3.add/Z3.check",
                "input_object" => "computed point-pair incident-line counts from the Julia GF(4) incidence enumeration",
                "output_object" => z3_valid["verdict"],
                "positive_case" => "valid PG(3,4) pair-line uniqueness makes existence of count != 1 unsat",
                "negative_control" => z3_bad["verdict"],
                "boundary_case" => "3570 unordered point pairs over GF(4) with scrambled-incidence SAT control",
                "demotion_condition" => "if solver constraints use formula constants instead of computed incident-line counts or omit the scrambled SAT control",
                "gates" => ["G2_pair_line_uniqueness"],
            ),
        ],
        "pin_block_canonical_json" => PIN_BLOCK_CANONICAL,
        "pin_block_sha256" => PIN_BLOCK_SHA256,
        "points" => points,
        "lines" => lines,
        "planes" => planes,
        "graph_invariants" => graph_inv,
        "clique_family_check" => clique_check,
        "reconstruction" => recon,
        "frobenius_boundary" => frob,
        "q2_anchor" => q2_anchor,
        "q3_anchor" => q3_anchor,
        "values" => values_row,
        "controls" => controls,
        "gates" => gates,
        "gate_pass" => Dict(name => row["pass"] for (name, row) in gates),
        "separation_table" => separation_table,
        "summary" => Dict(
            "finite_object" => "PG(3,4) projective points/lines/planes via independent GF(4) quotient",
            "twistor_candidate_result" => "incidence reconstruction persists; scalar-quotient boundary strengthens from q=3 ratio 2 to q=4 ratio 3",
            "char2_boundary" => "nontrivial Frobenius x->x^2 moves projective points but preserves incidence",
            "ceiling" => CLASSIFICATION,
            "fence" => "finite incidence discriminator only; no physics, spacetime, GR, bridge, axis, manifold, or Penrose-validation claim",
        ),
        "kill_condition_met" => !any(row -> row["separation"], separation_table),
        "crossover_proofs" => Dict("julia_z3" => z3_valid),
        "claim_ceiling" => Dict("alt_math_discriminator_only" => true, "no_spacetime_gr_physics_claim" => true, "no_penrose_validates_language" => true, "not_canon" => true),
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("GEO_S1_Q4_FINITE_INCIDENCE_V0_JULIA_DONE all_pass=$(result["all_pass"]) points=$(result["values"]["point_count"]) lines=$(result["values"]["line_count"]) planes=$(result["values"]["plane_count"]) z3=$(result["crossover_proofs"]["julia_z3"]["verdict"]) frob=$(result["frobenius_boundary"]["pass"])")
end

main()
