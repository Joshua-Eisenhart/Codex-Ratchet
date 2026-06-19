#!/usr/bin/env julia

using Dates
using Graphs
using JSON3
using Manifolds
using SHA
using Statistics
using Z3

const ROOT = abspath(joinpath(@__DIR__, "..", "..", ".."))
const SIM_ID = "geo_network_shell_coordinate_v0"
const ENGINE = "julia"
const RESULT_DIR = joinpath(@__DIR__, "results")
const SOURCE_PATH = joinpath(@__DIR__, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-10
const Z3_SCALE = 10^12
const PIN_SPEC = "geo_network_shell_coordinate_v0|G4-static-network-level-shell-coordinate|inputs=committed stage_lifted_spinor_shell_n3_v0,n4_v0,n5_v0,n6_v0,n7_v0,n8_v0 results read-only|coordinates=degree_weighted_shell_centroid_spread_v0,degree_squared_shell_centroid_v0,edge_gradient_shell_energy_v0,unweighted_shell_mean_spread_alt_v0|julia_load_bearing_rows=frechet_karcher_shell_mean_degree_weighted_v0,z3_smt_degenerate_conflation_v0|controls=collapsed_shell,permuted_site_labels,moved_single_site,degenerate_unweighted_conflation|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
const SOURCE_RESULTS = Dict(
    "n3" => joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n3_v0", "results", "stage_lifted_spinor_shell_n3_v0_jax_results.json"),
    "n4" => joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n4_v0", "results", "stage_lifted_spinor_shell_n4_v0_jax_results.json"),
    "n5" => joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n5_v0", "results", "stage_lifted_spinor_shell_n5_v0_jax_results.json"),
    "n6" => joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n6_v0", "results", "stage_lifted_spinor_shell_n6_v0_jax_results.json"),
    "n7" => joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n7_v0", "results", "stage_lifted_spinor_shell_n7_v0_jax_results.json"),
    "n8" => joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n8_v0", "results", "stage_lifted_spinor_shell_n8_v0_jax_results.json"),
)

sha256_text(text) = bytes2hex(sha256(codeunits(text)))
function sha256_file(path)
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end
r12(value) = round(Float64(value), digits=12)
rel(path) = relpath(path, ROOT)

function load_source(path)
    payload = JSON3.read(read(path, String))
    Dict(
        "all_pass" => payload["all_pass"],
        "classification" => String(payload["classification"]),
        "promotion_allowed" => payload["promotion_allowed"],
        "formal_admission_allowed" => payload["formal_admission_allowed"],
        "sites" => payload["rows"]["P2_support_object"]["sites"],
        "edges" => payload["rows"]["P2_support_object"]["edges"],
        "aggregate_leakage" => payload["rows"]["P8_shell_leakage"]["aggregate_leakage"],
        "source_result_path" => rel(path),
        "source_result_sha256" => sha256_file(path),
    )
end

function graph_degrees(site_ids, edges)
    index = Dict(site_id => i for (i, site_id) in enumerate(site_ids))
    graph = SimpleGraph(length(site_ids))
    for edge in edges
        add_edge!(graph, index[String(edge["src"])], index[String(edge["dst"])])
    end
    Float64.(degree(graph))
end

function coordinate_values(z_values, deg_values, edges, site_ids)
    z = Float64.(z_values)
    deg = Float64.(deg_values)
    deg2 = deg .* deg
    z_bar_degree = sum(deg .* z) / sum(deg)
    sigma_degree = sqrt(sum(deg .* ((z .- z_bar_degree) .^ 2)) / sum(deg))
    z_bar_degree2 = sum(deg2 .* z) / sum(deg2)
    z_bar_unweighted = mean(z)
    sigma_unweighted = std(z, corrected=false)
    index = Dict(site_id => i for (i, site_id) in enumerate(site_ids))
    edge_terms = [((z[index[String(edge["src"])]] - z[index[String(edge["dst"])]]) ^ 2) for edge in edges]
    edge_energy = isempty(edge_terms) ? 0.0 : mean(edge_terms)
    Dict(
        "degree_weighted_shell_centroid_spread_v0" => Dict("z_bar" => r12(z_bar_degree), "sigma_z" => r12(sigma_degree), "weight_rule" => "support_graph_degree"),
        "degree_squared_shell_centroid_v0" => Dict("z_bar" => r12(z_bar_degree2), "weight_rule" => "support_graph_degree_squared"),
        "edge_gradient_shell_energy_v0" => Dict("edge_mean_delta_z_squared" => r12(edge_energy), "edge_count" => length(edges)),
        "unweighted_shell_mean_spread_alt_v0" => Dict("z_bar" => r12(z_bar_unweighted), "sigma_z" => r12(sigma_unweighted), "degeneracy_status" => "alternative_control_only"),
    )
end

function sphere_point(site)
    eta = Float64(site["eta"])
    theta = Float64(site["theta"])
    [sin(2.0 * eta) * cos(theta), sin(2.0 * eta) * sin(theta), cos(2.0 * eta)]
end

function torus_point(site)
    [Float64(site["eta"]), Float64(site["theta"])]
end

function manifold_coordinate_row(sites, deg, coords)
    sphere = Manifolds.Sphere(2)
    torus = Manifolds.Torus(2)
    sphere_pts = [sphere_point(site) for site in sites]
    torus_pts = [torus_point(site) for site in sites]
    weights = Float64.(deg)
    sphere_mean = Manifolds.mean(sphere, sphere_pts, weights)
    torus_mean = Manifolds.mean(torus, torus_pts, weights)
    frechet_z = Float64(sphere_mean[3])
    chart_z = Float64(coords["degree_weighted_shell_centroid_spread_v0"]["z_bar"])
    divergence = frechet_z - chart_z
    unequal_degree = length(unique(r12.(weights))) > 1
    Dict(
        "row_id" => "frechet_karcher_shell_mean_degree_weighted_v0",
        "manifold" => "Sphere(2)",
        "torus_companion_manifold" => "Torus(2)",
        "api" => "Manifolds.mean(Manifolds.Sphere(2), pts, support_graph_degree_weights)",
        "torus_api" => "Manifolds.mean(Manifolds.Torus(2), pts, support_graph_degree_weights)",
        "point_rule" => "sphere_point=(sin(2eta)cos(theta),sin(2eta)sin(theta),cos(2eta)); torus_point=(eta,theta)",
        "weight_rule" => "support_graph_degree",
        "weights" => r12.(weights),
        "sphere_mean_point" => r12.(sphere_mean),
        "torus_mean_eta_theta" => r12.(torus_mean),
        "frechet_karcher_z_bar" => r12(frechet_z),
        "chart_space_weighted_z_bar" => r12(chart_z),
        "frechet_minus_chart_z_bar" => r12(divergence),
        "abs_divergence" => r12(abs(divergence)),
        "curvature_divergence_detected" => abs(divergence) > 1.0e-6,
        "gates" => ["julia_load_bearing_rows", "all_pass"],
        "fired" => isfinite(frechet_z) && all(isfinite, sphere_mean) && all(isfinite, torus_mean) && (unequal_degree ? abs(divergence) > 1.0e-6 : true),
    )
end

function z3_add(args::Vector{Z3.Expr})
    ctx = args[1].ctx
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_add(Z3.ref(ctx), length(args), map(Z3.as_ast, args)))
end

function z3_mul(args::Vector{Z3.Expr})
    ctx = args[1].ctx
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_mul(Z3.ref(ctx), length(args), map(Z3.as_ast, args)))
end

function z3_sum(args::Vector{Z3.Expr})
    length(args) == 1 ? args[1] : z3_add(args)
end

function z3_scaled_int(value)
    Int(round(Float64(value) * Z3_SCALE))
end

function z3_unweighted_sum_expr(solver, prefix, z_values)
    terms = Z3.Expr[]
    for (i, z) in enumerate(z_values)
        z_var = Z3.IntVar("$(prefix)_z_$i")
        Z3.add(solver, z_var == Z3.IntVal(z3_scaled_int(z)))
        push!(terms, z_var)
    end
    z3_sum(terms)
end

function z3_weighted_sum_expr(solver, prefix, z_values, weights)
    terms = Z3.Expr[]
    for (i, (z, w)) in enumerate(zip(z_values, weights))
        z_var = Z3.IntVar("$(prefix)_z_$i")
        w_var = Z3.IntVar("$(prefix)_w_$i")
        Z3.add(solver, z_var == Z3.IntVal(z3_scaled_int(z)))
        Z3.add(solver, w_var == Z3.IntVal(Int(round(w))))
        push!(terms, z3_mul([w_var, z_var]))
    end
    z3_sum(terms)
end

function z3_equality_status(kind, z_values, swapped, weights)
    solver = Z3.Solver()
    if kind == "unweighted"
        left = z3_unweighted_sum_expr(solver, "orig_unweighted", z_values)
        right = z3_unweighted_sum_expr(solver, "swap_unweighted", swapped)
    else
        left = z3_weighted_sum_expr(solver, "orig_weighted", z_values, weights)
        right = z3_weighted_sum_expr(solver, "swap_weighted", swapped, weights)
    end
    Z3.add(solver, left == right)
    string(Z3.check(solver))
end

function z3_smt_conflation_receipt(z_values, deg, swapped, coords, swapped_coords)
    weights = Int.(round.(deg))
    erased_weights = ones(Int, length(weights))
    perm = reverse(collect(eachindex(z_values)))
    permuted_z = z_values[perm]
    permuted_swapped = swapped[perm]
    permuted_weights = weights[perm]
    unweighted_status = z3_equality_status("unweighted", z_values, swapped, weights)
    weighted_status = z3_equality_status("weighted", z_values, swapped, weights)
    erased_status = z3_equality_status("weighted", z_values, swapped, erased_weights)
    permuted_status = z3_equality_status("weighted", permuted_z, permuted_swapped, permuted_weights)
    Dict(
        "row_id" => "z3_smt_degenerate_conflation_v0",
        "solver" => "Z3.jl",
        "api" => "Z3.Solver / Z3.IntVar / Z3.IntVal / Z3.check",
        "scaled_integer_precision" => Z3_SCALE,
        "raw_values_bound" => true,
        "raw_weights_bound" => true,
        "unweighted_original_z_bar" => coords["unweighted_shell_mean_spread_alt_v0"]["z_bar"],
        "unweighted_swapped_z_bar" => swapped_coords["unweighted_shell_mean_spread_alt_v0"]["z_bar"],
        "weighted_original_z_bar" => coords["degree_weighted_shell_centroid_spread_v0"]["z_bar"],
        "weighted_swapped_z_bar" => swapped_coords["degree_weighted_shell_centroid_spread_v0"]["z_bar"],
        "weighted_delta_abs" => r12(abs(coords["degree_weighted_shell_centroid_spread_v0"]["z_bar"] - swapped_coords["degree_weighted_shell_centroid_spread_v0"]["z_bar"])),
        "unweighted_equality_status" => unweighted_status,
        "weighted_equality_status" => weighted_status,
        "erased_weights_equality_status" => erased_status,
        "permuted_control_weighted_equality_status" => permuted_status,
        "expected" => Dict(
            "unweighted_equality_status" => "sat",
            "weighted_equality_status" => "unsat",
            "erased_weights_equality_status" => "sat",
            "permuted_control_weighted_equality_status" => "unsat",
        ),
        "gates" => ["degenerate_unweighted_conflation", "all_pass"],
        "fired" => unweighted_status == "sat" && weighted_status == "unsat" && erased_status == "sat" && permuted_status == "unsat",
    )
end

function controls_for(z_values, deg, edges, site_ids, coords)
    shell = length(z_values) > 1 ? z_values[2] : z_values[1]
    collapsed = coordinate_values(fill(shell, length(z_values)), deg, edges, site_ids)
    perm = reverse(collect(eachindex(z_values)))
    relabel = Dict(site_ids[i] => site_ids[perm[i]] for i in eachindex(site_ids))
    perm_site_ids = [relabel[site_id] for site_id in site_ids]
    perm_edges = [Dict("src" => relabel[String(edge["src"])], "dst" => relabel[String(edge["dst"])]) for edge in edges]
    perm_coords = coordinate_values(z_values, graph_degrees(perm_site_ids, perm_edges), perm_edges, perm_site_ids)
    moved = copy(z_values)
    moved[1] = max(-1.0, min(1.0, moved[1] - 0.2))
    moved_coords = coordinate_values(moved, deg, edges, site_ids)
    degenerate = degenerate_control(z_values, deg, edges, site_ids, coords)
    Dict(
        "collapsed_shell" => Dict(
            "fired" => abs(collapsed["degree_weighted_shell_centroid_spread_v0"]["sigma_z"]) <= TOL && abs(collapsed["degree_weighted_shell_centroid_spread_v0"]["z_bar"] - shell) <= TOL,
            "mutation" => "set every site z to one shell value",
            "expected_centroid" => r12(shell),
            "observed" => collapsed["degree_weighted_shell_centroid_spread_v0"],
        ),
        "permuted_site_labels" => Dict("fired" => coords == perm_coords, "mutation" => "reverse site labels and relabel support edges consistently", "observed_invariant" => perm_coords),
        "moved_single_site" => Dict(
            "fired" => abs(coords["degree_weighted_shell_centroid_spread_v0"]["z_bar"] - moved_coords["degree_weighted_shell_centroid_spread_v0"]["z_bar"]) > 1.0e-6 || abs(coords["edge_gradient_shell_energy_v0"]["edge_mean_delta_z_squared"] - moved_coords["edge_gradient_shell_energy_v0"]["edge_mean_delta_z_squared"]) > 1.0e-6,
            "mutation" => "move q0 shell coordinate by -0.2 within [-1,1]",
            "observed" => moved_coords,
        ),
        "degenerate_unweighted_conflation" => degenerate,
    )
end

function degenerate_control(z_values, deg, edges, site_ids, coords)
    degree_values = r12.(deg)
    if length(unique(degree_values)) == 1
        return Dict(
            "fired" => true,
            "degenerate_witness_applicable" => false,
            "reason" => "all support-graph degrees are equal, so degree weighting intentionally collapses to the unweighted alternative for this source row",
            "packet_discriminator_source" => "n4",
        )
    end
    swapped = copy(z_values)
    if length(swapped) >= 3
        swapped[2], swapped[3] = swapped[3], swapped[2]
    end
    swapped_coords = coordinate_values(swapped, deg, edges, site_ids)
    unweighted_same = abs(coords["unweighted_shell_mean_spread_alt_v0"]["z_bar"] - swapped_coords["unweighted_shell_mean_spread_alt_v0"]["z_bar"]) <= TOL
    weighted_diff = abs(coords["degree_weighted_shell_centroid_spread_v0"]["z_bar"] - swapped_coords["degree_weighted_shell_centroid_spread_v0"]["z_bar"]) > 1.0e-6
    z3_receipt = z3_smt_conflation_receipt(z_values, deg, swapped, coords, swapped_coords)
    Dict(
        "fired" => unweighted_same && weighted_diff && z3_receipt["fired"],
        "degenerate_witness_applicable" => true,
        "mutation" => "swap two unequal-degree site shell coordinates",
        "unweighted_mean_conflates" => unweighted_same,
        "degree_weighted_separates" => weighted_diff,
        "swapped_observed" => swapped_coords,
        "z3_smt_row" => z3_receipt,
    )
end

function source_coordinates(label, source)
    sites = sort(collect(source["sites"]); by = row -> String(row["site_id"]))
    site_ids = [String(site["site_id"]) for site in sites]
    z_values = [Float64(site["z"]) for site in sites]
    deg = graph_degrees(site_ids, source["edges"])
    coords = coordinate_values(z_values, deg, source["edges"], site_ids)
    manifold_row = manifold_coordinate_row(sites, deg, coords)
    controls = controls_for(z_values, deg, source["edges"], site_ids, coords)
    Dict(
        "source_label" => label,
        "site_count" => length(site_ids),
        "edge_count" => length(source["edges"]),
        "site_ids" => site_ids,
        "z_values" => r12.(z_values),
        "degrees" => r12.(deg),
        "aggregate_leakage_context" => source["aggregate_leakage"],
        "network_shell_coordinates" => coords,
        "julia_load_bearing_rows" => Dict("frechet_karcher_shell_mean_degree_weighted_v0" => manifold_row),
        "controls" => controls,
        "all_controls_fired" => all(control -> control["fired"], values(controls)) && manifold_row["fired"],
    )
end

function tool_call(tool, function_name, gates; input_object="committed n3/n4/n5/n6/n7/n8 per-site z coordinates plus support graph edges", output_object="named static network-level shell coordinate/control row", positive_case="degree weighted coordinates are finite and label independent", negative_control="unweighted mean conflation and moved-site controls recomputed", boundary_case="n3/n6/n7/n8 equal-degree graphs and n4/n5 unequal-degree graphs", demotion_condition="if the package function is not called in the current rerun, demote to supportive")
    Dict(
        "tool" => tool,
        "qualified_api/function" => function_name,
        "input_object" => input_object,
        "output_object" => output_object,
        "positive_case" => positive_case,
        "negative/erased_control" => negative_control,
        "boundary_case" => boundary_case,
        "demotion_condition" => demotion_condition,
        "gates" => gates,
    )
end

function build_result()
    sources = Dict(label => load_source(path) for (label, path) in SOURCE_RESULTS)
    rows = Dict(label => source_coordinates(label, source) for (label, source) in sources)
    all_pass = all(source -> source["all_pass"] == true, values(sources)) && all(row -> row["all_controls_fired"] == true, values(rows))
    Dict(
        "schema_version" => "geo_network_shell_coordinate_result_v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "role_id" => "julia_graphs_canon_network_coordinate_builder",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "all_pass" => all_pass,
        "reads_peer_result" => READS_PEER_RESULT,
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "input_source_results" => Dict(label => Dict("path" => source["source_result_path"], "sha256" => source["source_result_sha256"]) for (label, source) in sources),
        "rows" => rows,
        "adjudication" => Dict(
            "non_degenerate_after_controls" => ["degree_weighted_shell_centroid_spread_v0", "edge_gradient_shell_energy_v0"],
            "alternative_not_crowned" => "unweighted_shell_mean_spread_alt_v0 is reported; n4/n5 fail the unequal-degree conflation controls, while n6/n7/n8 are equal-degree boundary rows.",
        ),
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing graph degree computation for network-level coordinate"),
            "Manifolds" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Frechet/Karcher mean on Sphere(2) and Torus(2), compared against chart-space weighted z_bar"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing SMT derivation of unweighted conflation vs weighted separation from bound finite values"),
            "Statistics" => Dict("tried" => true, "used" => true, "reason" => "supportive mean/spread arithmetic"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "Manifolds" => "load_bearing", "Z3" => "load_bearing", "Statistics" => "supportive"),
        "packages_used" => ["Graphs", "JSON3", "Manifolds", "SHA", "Statistics", "Z3"],
        "aligned_packages_load_bearing" => ["Manifolds", "Z3"],
        "claim_path_tools" => ["Graphs", "Manifolds", "Z3"],
        "tool_calls" => [
            tool_call("Graphs", "Graphs.SimpleGraph / Graphs.add_edge! / Graphs.degree", ["degree_weighted_shell_centroid_spread_v0", "degenerate_unweighted_conflation"], demotion_condition="if Graphs.degree is not called in the current rerun, demote to supportive"),
            tool_call("Manifolds", "Manifolds.Sphere / Manifolds.Torus / Manifolds.mean", ["frechet_karcher_shell_mean_degree_weighted_v0", "all_pass"], input_object="per-site shell manifold points from eta/theta/z plus support-graph degree weights", output_object="Frechet/Karcher mean z coordinate and Torus companion mean", positive_case="n4/n5 Sphere(2) Frechet z differs from chart-space weighted z_bar where curvature matters; n6/n7/n8 compute the same row as equal-degree boundaries", negative_control="like-for-like chart-space weighted z_bar comparison and n3/n6/n7/n8 equal-degree boundary rows", boundary_case="n3/n6/n7/n8 equal-degree shell rows plus n4/n5 unequal-degree curved shell rows", demotion_condition="if Manifolds.mean does not gate all_pass/divergence, demote to supportive"),
            tool_call("Z3", "Z3.Solver / Z3.IntVar / Z3.IntVal / Z3.check", ["z3_smt_degenerate_conflation_v0", "degenerate_unweighted_conflation"], input_object="scaled finite z values for original and swapped configurations plus support-graph degree weights", output_object="SAT/UNSAT equality statuses for unweighted, weighted, erased-weight, and permuted controls", positive_case="unweighted equality is SAT while weighted equality is UNSAT", negative_control="erased weights flip equality to SAT; permuted paired control preserves weighted UNSAT", boundary_case="n4/n5 unequal-degree swap rows", demotion_condition="if equality statuses are not produced by Z3.check over bound raw values, demote to supportive"),
        ],
        "capability_receipts" => [
            Dict("tool" => "Graphs", "function" => "Graphs.degree", "status" => "called_in_current_rerun"),
            Dict("tool" => "Manifolds", "function" => "Manifolds.mean", "status" => "called_in_current_rerun"),
            Dict("tool" => "Z3", "function" => "Z3.check", "status" => "called_in_current_rerun"),
        ],
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON3.pretty(io, result)
        write(io, "\n")
    end
    println(JSON3.write(Dict("ok" => result["all_pass"], "result" => rel(RESULT_PATH))))
    return result["all_pass"] ? 0 : 1
end

exit(main())
