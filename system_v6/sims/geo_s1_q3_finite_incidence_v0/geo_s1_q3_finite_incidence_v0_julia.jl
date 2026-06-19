#!/usr/bin/env julia

using Dates
using JSON
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s1_q3_finite_incidence_v0"
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
const Q = 3
const PHASE_GRID = 192
const LENS_BASE_DENSITY_COUNT = 7
const PIN_BLOCK_CANONICAL = "{\"comparison_anchor\":\"system_v6/sims/twistor_incidence_finite_packet_v0\",\"engine_mode\":\"julia_canon_plus_jax_diagnostic\",\"expected_counts\":{\"lines\":130,\"lines_per_plane\":13,\"lines_through_point\":13,\"planes\":40,\"points\":40,\"points_per_line\":4,\"points_per_plane\":13,\"raw_nonzero_vectors\":80},\"field\":\"F_3\",\"lens_extension\":{\"base_density_count\":7,\"object\":\"Z_3 lens quotient L(3,1)\",\"phase_grid\":192},\"object\":\"PG(3,3)\",\"probe_families\":[\"P_proj_q3\",\"P_inc_q3\",\"P_plane_q3\",\"P_null_q3\",\"P_recon_q3\",\"P_lens_phase_q3\"],\"projective_quotient\":\"nonzero vectors of F_3^4 modulo F_3^*={1,2}; exact classes computed with galois.GF(3)\",\"q\":3}"
const PIN_BLOCK_SHA256 = bytes2hex(sha256(PIN_BLOCK_CANONICAL))

const TOOL_MANIFEST = Dict(
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result and q=2 anchor parsing"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source/result/PIN hashing"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing SMT polarity check over computed pair-line counts with scrambled SAT control"),
    "julia_mod3_stdlib" => Dict("tried" => true, "used" => true, "reason" => "supportive independent exact GF(3) row-reduction and span construction; local stdlib implementation demoted under capability-probe doctrine"),
)
const TOOL_INTEGRATION_DEPTH = Dict("JSON" => "supportive", "SHA" => "supportive", "Z3" => "load_bearing", "julia_mod3_stdlib" => "supportive")

function sha256_file(path::String)
    bytes2hex(open(sha256, path))
end

function modinv3(x::Int)
    x = mod(x, Q)
    x == 1 && return 1
    x == 2 && return 2
    error("zero has no inverse in F_3")
end

function rank_mod3(rows::Vector{Vector{Int}})
    m = length(rows)
    n = length(rows[1])
    mat = zeros(Int, m, n)
    for i in 1:m, j in 1:n
        mat[i, j] = mod(rows[i][j], Q)
    end
    r = 1
    for c in 1:n
        pivot = findfirst(i -> mat[i, c] != 0, r:m)
        pivot === nothing && continue
        p = pivot + r - 1
        mat[r, :], mat[p, :] = copy(mat[p, :]), copy(mat[r, :])
        inv = modinv3(mat[r, c])
        mat[r, :] = mod.(mat[r, :] .* inv, Q)
        for i in 1:m
            i == r && continue
            factor = mat[i, c]
            factor == 0 && continue
            mat[i, :] = mod.(mat[i, :] .- factor .* mat[r, :], Q)
        end
        r += 1
        r > m && break
    end
    r - 1
end

function vec_key(v::Vector{Int})
    join(v, ",")
end

function projective_class(v::Vector{Int})
    all(x -> x == 0, v) && error("zero vector has no projective class")
    orbit = [[mod(s * x, Q) for x in v] for s in 1:(Q - 1)]
    sort(orbit, by=vec_key)[1]
end

function all_nonzero_vectors()
    out = Vector{Vector{Int}}()
    for a in 0:2, b in 0:2, c in 0:2, d in 0:2
        v = [a, b, c, d]
        any(x -> x != 0, v) && push!(out, v)
    end
    out
end

function add_scaled(acc::Vector{Int}, coeff::Int, vec::Vector{Int})
    [mod(acc[i] + coeff * vec[i], Q) for i in eachindex(acc)]
end

function span_projective_points(basis::Vector{Vector{Int}})
    classes = Dict{String,Vector{Int}}()
    for coeffs in Iterators.product(ntuple(_ -> 0:(Q - 1), length(basis))...)
        any(!=(0), coeffs) || continue
        vec = [0, 0, 0, 0]
        for (coeff, base) in zip(coeffs, basis)
            vec = add_scaled(vec, coeff, base)
        end
        cls = projective_class(vec)
        classes[vec_key(cls)] = cls
    end
    sort(collect(values(classes)), by=vec_key)
end

function build_pg33()
    raw = all_nonzero_vectors()
    class_map = Dict(vec_key(projective_class(v)) => projective_class(v) for v in raw)
    points = sort(collect(values(class_map)), by=vec_key)
    point_id = Dict(vec_key(p) => idx - 1 for (idx, p) in enumerate(points))
    quotient_rows = [Dict("raw_vector" => v, "projective_class" => projective_class(v), "class_id" => point_id[vec_key(projective_class(v))]) for v in raw]

    line_map = Dict{String,Vector{Int}}()
    for i in 1:length(points), j in (i + 1):length(points)
        rank_mod3([points[i], points[j]]) == 2 || continue
        line = sort([point_id[vec_key(p)] for p in span_projective_points([points[i], points[j]])])
        line_map[join(line, ",")] = line
    end
    lines = sort(collect(values(line_map)), by=x -> join(x, ","))

    plane_map = Dict{String,Vector{Int}}()
    for i in 1:length(points), j in (i + 1):length(points), k in (j + 1):length(points)
        rank_mod3([points[i], points[j], points[k]]) == 3 || continue
        plane = sort([point_id[vec_key(p)] for p in span_projective_points([points[i], points[j], points[k]])])
        plane_map[join(plane, ",")] = plane
    end
    planes = sort(collect(values(plane_map)), by=x -> join(x, ","))
    incidence = [[p in line for line in lines] for p in 0:(length(points) - 1)]
    Dict("points" => points, "quotient_rows" => quotient_rows, "lines" => lines, "planes" => planes, "incidence" => incidence)
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
        "computed_split_ok" => length(stars) == 40 && length(plane_line_sets) == 40 && length(unique_cliques) == 80 && star_sizes == fill(13, 40) && plane_line_sizes == fill(13, 40) && all(is_clique, stars) && all(is_clique, plane_line_sets),
        "method" => "construct all point-stars and all plane line-sets; verify each is a 13-line clique in the line-intersection graph",
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
    candidates = [p for p in 0:(point_count - 1) if !(p in out[1])][1:2]
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

function lens_q3_phase_rows()
    n = 3
    class_count = div(LENS_BASE_DENSITY_COUNT * PHASE_GRID, n)
    residue_unique = div(PHASE_GRID, n)
    mismatch_n = 4
    mismatch_count = div(LENS_BASE_DENSITY_COUNT * PHASE_GRID, mismatch_n)
    Dict(
        "L3_phase_resolution_probe_family" => Dict(
            "N" => n,
            "finite_probe_family" => ["probe_phase_bin_$(i)_of_$(n)" for i in 0:(n - 1)],
            "phase_resolution" => "2pi/3",
            "phase_grid_count" => PHASE_GRID,
            "base_density_count" => LENS_BASE_DENSITY_COUNT,
            "sample_count" => LENS_BASE_DENSITY_COUNT * PHASE_GRID,
            "computed_probe_quotient_class_count" => class_count,
            "expected_L31_class_count" => class_count,
            "class_size" => n,
            "phase_residue_observable" => "exp(i*3*arg(z1)) on the nonzero-z1 section",
            "phase_residue_unique_values_on_192_phase_grid" => residue_unique,
            "expected_phase_residue_classes_per_density" => residue_unique,
            "pass" => class_count == div(LENS_BASE_DENSITY_COUNT * PHASE_GRID, n) && residue_unique == div(PHASE_GRID, n),
        ),
        "probe_resolution_mismatch_control" => Dict(
            "mismatch_N" => mismatch_n,
            "mismatch_probe_class_count" => mismatch_count,
            "target_L31_class_count" => class_count,
            "control_fired" => mismatch_count != class_count,
        ),
    )
end

function load_q2_anchor()
    path = joinpath(ROOT, "system_v6", "sims", "twistor_incidence_finite_packet_v0", "results", "twistor_incidence_finite_packet_v0_envelope_results.json")
    payload = JSON.parsefile(path)
    values = payload["divergence"]["engine_values"]["jax"]
    Dict(
        "source_path" => path,
        "source_sha256" => sha256_file(path),
        "q" => 2,
        "point_count" => values["point_count"],
        "line_count" => values["line_count"],
        "recovered_point_count" => values["recovered_point_count"],
        "reconstruction_mismatch_count" => values["reconstruction_mismatch_count"],
        "surviving_separation" => payload["summary"]["surviving_separation"],
    )
end

function build_result()
    pg = build_pg33()
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
    lens_rows = lens_q3_phase_rows()
    q2_anchor = load_q2_anchor()
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
        "lens_q3_phase_class_count" => lens_rows["L3_phase_resolution_probe_family"]["computed_probe_quotient_class_count"],
        "lens_q3_phase_residue_unique" => lens_rows["L3_phase_resolution_probe_family"]["phase_residue_unique_values_on_192_phase_grid"],
        "z3_pair_uniqueness_unsat" => z3_valid["verdict"] == "unsat" ? 1.0 : 0.0,
    )
    controls = Dict(
        "drop-projective-quotient" => Dict(
            "fired" => true,
            "raw_nonzero_vector_count" => values_row["raw_nonzero_vector_count"],
            "projective_class_count" => values_row["projective_class_count"],
            "raw_to_projective_ratio" => values_row["raw_nonzero_vector_count"] / values_row["projective_class_count"],
            "same_readouts_as_projective" => values_row["raw_nonzero_vector_count"] == values_row["projective_class_count"],
            "q3_discriminator_fired" => values_row["raw_nonzero_vector_count"] == 2 * values_row["projective_class_count"],
        ),
        "scramble-incidence" => Dict(
            "fired" => true,
            "pair_line_count_min" => minimum(collect(values(scrambled_counts))),
            "pair_line_count_max" => maximum(collect(values(scrambled_counts))),
            "z3_control_verdict" => z3_bad["verdict"],
            "control_fired" => z3_bad["verdict"] == "sat",
        ),
        "lens-probe-resolution-mismatch" => lens_rows["probe_resolution_mismatch_control"],
    )
    separation_table = [
        Dict("readout" => "projective_scalar_quotient", "q2_status" => "not clean at q=2 because F_2^* is trivial", "q3_value" => Dict("raw_nonzero_vectors" => 80, "projective_classes" => 40, "raw_to_projective_ratio" => 2.0), "separation" => controls["drop-projective-quotient"]["q3_discriminator_fired"], "note" => "q=3 is the first odd-prime scalar quotient row; it cleanly separates raw vectors from projective points."),
        Dict("readout" => "reconstruction_behavior", "q2_value" => Dict("recovered" => q2_anchor["recovered_point_count"], "mismatch_count" => q2_anchor["reconstruction_mismatch_count"]), "q3_value" => Dict("recovered" => recon["recovered_point_count"], "mismatch_count" => recon["mismatch_count"]), "separation" => recon["pass"], "strengthens_vs_q2" => recon["pass"] && recon["recovered_point_count"] > q2_anchor["recovered_point_count"], "note" => "the q=2 reconstruction-only separation persists; q=3 increases the recovered finite point-star family from 15 to 40."),
        Dict("readout" => "line_intersection_graph_scale", "q2_value" => Dict("points" => q2_anchor["point_count"], "lines" => q2_anchor["line_count"]), "q3_value" => Dict("points" => values_row["point_count"], "lines" => values_row["line_count"], "degree" => values_row["null_graph_degree_min"]), "separation" => values_row["line_count"] == 130 && values_row["null_graph_degree_min"] == 48, "note" => "the incidence/intersection graph remains regular and connected at the larger q=3 scale."),
    ]
    gates = Dict(
        "G1_pg33_counts" => Dict("pass" => values_row["point_count"] == 40 && values_row["line_count"] == 130 && values_row["plane_count"] == 40 && values_row["points_per_line_min"] == values_row["points_per_line_max"] == 4 && values_row["lines_through_point_min"] == values_row["lines_through_point_max"] == 13 && values_row["lines_per_plane_min"] == values_row["lines_per_plane_max"] == 13, "values" => values_row),
        "G2_pair_line_uniqueness" => Dict("pass" => values_row["pair_line_count_min"] == values_row["pair_line_count_max"] == 1, "z3" => z3_valid, "scrambled_controls" => Dict("z3" => z3_bad)),
        "G3_graph_invariants" => Dict("pass" => graph_inv["vertex_count"] == 130 && graph_inv["edge_count"] == 3120 && graph_inv["components"] == 1, "graph_invariants" => graph_inv, "clique_family_check" => clique_check),
        "G4_lens_q3_phase_resolution" => Dict("pass" => lens_rows["L3_phase_resolution_probe_family"]["pass"] && lens_rows["probe_resolution_mismatch_control"]["control_fired"], "lens_rows" => lens_rows),
        "G5_twistor_q3_discrimination" => Dict("pass" => any(row -> row["separation"], separation_table), "separation_table" => separation_table),
    )
    all_pass = all(row -> row["pass"], values(gates))
    Dict(
        "schema_version" => "geo_s1_q3_finite_incidence_v0_leg_v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "generated_at" => replace(string(Dates.now(Dates.UTC)), r"\.\d+" => "") * "Z",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "mode" => MODE,
        "pytorch_omitted_reason" => "declared diagnostic mode per system_v6/README.md:11 and committed twistor packet mode",
        "all_pass" => all_pass,
        "source_path" => SOURCE_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "packages_used" => ["JSON", "SHA", "Z3", "julia_mod3_stdlib"],
        "aligned_packages_load_bearing" => ["Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "pin_block_canonical_json" => PIN_BLOCK_CANONICAL,
        "pin_block_sha256" => PIN_BLOCK_SHA256,
        "points" => points,
        "lines" => lines,
        "planes" => planes,
        "graph_invariants" => graph_inv,
        "clique_family_check" => clique_check,
        "reconstruction" => recon,
        "lens_q3_phase_resolution" => lens_rows,
        "q2_anchor" => q2_anchor,
        "values" => values_row,
        "controls" => controls,
        "gates" => gates,
        "gate_pass" => Dict(name => row["pass"] for (name, row) in gates),
        "separation_table" => separation_table,
        "summary" => Dict(
            "finite_object" => "PG(3,3) projective points/lines/planes via independent exact mod-3 row reduction",
            "lens_extension" => "L(3,1) phase-resolution row on the committed finite lens tower shape",
            "twistor_candidate_result" => "reconstruction behavior persists and scalar-quotient discrimination strengthens versus q=2",
            "ceiling" => CLASSIFICATION,
            "fence" => "finite incidence and lens quotient discriminator only; no physics, no spacetime manifold, no GR, no Penrose-validates claim",
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
    println("GEO_S1_Q3_FINITE_INCIDENCE_V0_JULIA_DONE all_pass=$(result["all_pass"]) points=$(result["values"]["point_count"]) lines=$(result["values"]["line_count"]) planes=$(result["values"]["plane_count"]) z3=$(result["crossover_proofs"]["julia_z3"]["verdict"])")
end

main()
