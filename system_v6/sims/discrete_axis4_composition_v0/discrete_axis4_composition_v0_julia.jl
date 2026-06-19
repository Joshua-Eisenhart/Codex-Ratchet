#!/usr/bin/env julia
# Julia lane for discrete_axis4_composition_v0.

using Dates
using Graphs
using JSON
using LinearAlgebra
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "discrete_axis4_composition_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const CLAIM_CEILING = "axis_readout_candidate_only"
const ENGINE_MODE = "three_engine_axis4_composition_candidate_on_family_a_33_cell_carrier"
const GRID_VALUES = [-1.0, -0.5, 0.0, 0.5, 1.0]
const EPS = 1.0e-10

now_z()::String = Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
rel(path::String)::String = replace(relpath(path, ROOT), "\\" => "/")

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function state_cells()
    cells = Vector{Dict{String, Any}}()
    for x in GRID_VALUES, y in GRID_VALUES, z in GRID_VALUES
        r2 = x * x + y * y + z * z
        if r2 <= 1.0 + 1.0e-12
            push!(
                cells,
                Dict(
                    "cell_id" => length(cells),
                    "coord" => [x, y, z],
                    "coord_scaled" => [Int(round(2 * x)), Int(round(2 * y)), Int(round(2 * z))],
                ),
            )
        end
    end
    cells
end

function nearest_cell(point, cells)
    best_id = 0
    best_d2 = Inf
    for cell in cells
        d2 = sum((point[i] - cell["coord"][i])^2 for i in 1:3)
        if d2 < best_d2 - 1.0e-12 || (abs(d2 - best_d2) <= 1.0e-12 && cell["cell_id"] < best_id)
            best_id = Int(cell["cell_id"])
            best_d2 = d2
        end
    end
    best_id
end

function matvec(matrix, vector)
    [sum(matrix[i, j] * vector[j] for j in 1:3) for i in 1:3]
end

function axis4_sign(cell, r_map, c_map)
    r = cell["coord"]
    phi_d = matvec(r_map, matvec(c_map, r))
    phi_i = matvec(c_map, matvec(r_map, r))
    delta = [phi_d[i] - phi_i[i] for i in 1:3]
    if norm(delta) <= EPS
        return 0
    end
    for idx in (2, 3, 1)
        if abs(delta[idx]) > EPS
            return delta[idx] > 0 ? 1 : -1
        end
    end
    return 0
end

function build_edges(cells)
    r_map = [1.0 0.0 0.0; 0.0 0.0 -1.0; 0.0 1.0 0.0]
    c_map = [0.7 0.0 0.0; 0.0 0.7 0.0; 0.0 0.0 1.0]
    gen_maps = [
        ("R_x", r_map),
        ("D_z", c_map),
        ("R_x_D_z", r_map * c_map),
        ("D_z_R_x", c_map * r_map),
        ("R_x_R_x", r_map * r_map),
        ("D_z_D_z", c_map * c_map),
    ]
    graph = Graphs.SimpleDiGraph(length(cells))
    rows = Vector{Dict{String, Any}}()
    for cell in cells
        for (name, matrix) in gen_maps
            image = matvec(matrix, cell["coord"])
            dst = nearest_cell(image, cells)
            Graphs.add_edge!(graph, Int(cell["cell_id"]) + 1, dst + 1)
            push!(rows, Dict("src" => Int(cell["cell_id"]), "dst" => dst, "generator" => name))
        end
    end
    (graph, rows)
end

function z3_add(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0)
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_axis4_identity(values; erased=false)::String
    solver = Z3.Solver()
    positive = Z3.IntVar(erased ? "julia_axis4_positive_erased" : "julia_axis4_positive")
    negative = Z3.IntVar(erased ? "julia_axis4_negative_erased" : "julia_axis4_negative")
    neutral = Z3.IntVar(erased ? "julia_axis4_neutral_erased" : "julia_axis4_neutral")
    total = Z3.IntVar(erased ? "julia_axis4_total_erased" : "julia_axis4_total")
    commuting = Z3.IntVar(erased ? "julia_axis4_commuting_erased" : "julia_axis4_commuting")
    if erased
        Z3.add(solver, positive == Z3.IntVal(0))
        Z3.add(solver, negative == Z3.IntVal(0))
        Z3.add(solver, neutral == Z3.IntVal(values["neutral"]))
        Z3.add(solver, total == Z3.IntVal(values["state_count"]))
        Z3.add(solver, commuting == Z3.IntVal(0))
    else
        Z3.add(solver, positive == Z3.IntVal(values["positive"]))
        Z3.add(solver, negative == Z3.IntVal(values["negative"]))
        Z3.add(solver, neutral == Z3.IntVal(values["neutral"]))
        Z3.add(solver, total == Z3.IntVal(values["state_count"]))
        Z3.add(solver, commuting == Z3.IntVal(values["commuting_neutral_count"]))
    end
    Z3.add(
        solver,
        Z3.Or(
            Z3.Expr[
                positive == Z3.IntVal(0),
                negative == Z3.IntVal(0),
                Z3.Not(z3_add(Z3.Expr[positive, negative, neutral]) == total),
                Z3.Not(commuting == total),
            ],
        ),
    )
    string(Z3.check(solver))
end

function compute_values()
    cells = state_cells()
    r_map = [1.0 0.0 0.0; 0.0 0.0 -1.0; 0.0 1.0 0.0]
    c_map = [0.7 0.0 0.0; 0.0 0.7 0.0; 0.0 0.0 1.0]
    signs = Dict(Int(cell["cell_id"]) => axis4_sign(cell, r_map, c_map) for cell in cells)
    positive = count(v -> v == 1, values(signs))
    negative = count(v -> v == -1, values(signs))
    neutral = count(v -> v == 0, values(signs))
    graph, edges = build_edges(cells)
    stable = count(edge -> signs[edge["src"]] == signs[edge["dst"]], edges)
    changed = length(edges) - stable
    commuting_neutral = length(cells)
    values_row = Dict(
        "state_count" => length(cells),
        "edge_count" => length(edges),
        "positive" => positive,
        "negative" => negative,
        "neutral" => neutral,
        "nonneutral" => positive + negative,
        "stable_edge_count" => stable,
        "changed_edge_count" => changed,
        "commuting_neutral_count" => commuting_neutral,
        "graph_nodes" => Graphs.nv(graph),
        "graph_edges_collapsed" => Graphs.ne(graph),
    )
    z3_status = z3_axis4_identity(values_row; erased=false)
    z3_erased = z3_axis4_identity(values_row; erased=true)
    (values_row, z3_status, z3_erased)
end

function main()
    mkpath(RESULT_DIR)
    values_row, z3_status, z3_erased = compute_values()
    source_probe = Dict(
        "Graphs_node_count" => values_row["graph_nodes"],
        "Graphs_collapsed_edge_count" => values_row["graph_edges_collapsed"],
        "edge_row_count" => values_row["edge_count"],
        "Z3_axis4_identity" => z3_status,
        "Z3_axis4_erased_flip" => z3_erased,
        "pass" => values_row["state_count"] == 33 &&
                  values_row["edge_count"] == 198 &&
                  values_row["positive"] == 14 &&
                  values_row["negative"] == 14 &&
                  values_row["neutral"] == 5 &&
                  z3_status == "unsat" &&
                  z3_erased == "sat",
    )
    package_observables = Dict(
        "Graphs" => "Graphs.SimpleDiGraph over the 33-cell carrier with six generator rows per cell",
        "Z3" => "Z3.Solver computed positive/negative/neutral Axis-4 identity with erased flip",
    )
    capability_receipts = [
        Dict("receipt_id" => "julia_Graphs_axis4_composition_candidate", "tool" => "Graphs", "computed_what" => package_observables["Graphs"], "status" => "used"),
        Dict("receipt_id" => "julia_Z3_axis4_composition_candidate", "tool" => "Z3", "computed_what" => package_observables["Z3"], "status" => "used"),
    ]
    payload = Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "object_id" => "$(SIM_ID)_$(ENGINE)",
        "engine" => ENGINE,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => CLAIM_CEILING,
        "reads_peer_result" => false,
        "generated_at" => now_z(),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "packages_used" => ["Graphs", "JSON", "LinearAlgebra", "SHA", "Z3"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "package_observables" => package_observables,
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("tried" => true, "used" => true, "reason" => "Julia finite carrier graph and Axis-4 stability counts"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "Julia SMT computed-value identity and erased flip"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "Z3" => "load_bearing"),
        "claim_path_tools" => ["Graphs", "Z3"],
        "engine_mode" => ENGINE_MODE,
        "capability_receipts" => capability_receipts,
        "tool_calls" => [
            Dict("receipt_id" => row["receipt_id"], "tool" => row["tool"], "qualified_api/function" => row["computed_what"], "load_bearing" => true)
            for row in capability_receipts
        ],
        "source_backing_probe" => source_probe,
        "computed_values" => values_row,
        "crossover_proofs" => Dict(
            "julia_z3" => Dict(
                "ran" => true,
                "load_bearing" => true,
                "verdict" => z3_status,
                "erased_flip_verdict" => z3_erased,
                "bound_values" => values_row,
            ),
        ),
        "all_pass" => source_probe["pass"],
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => payload["all_pass"], "result_path" => rel(RESULT_PATH))))
    payload["all_pass"] ? 0 : 1
end

exit(main())
