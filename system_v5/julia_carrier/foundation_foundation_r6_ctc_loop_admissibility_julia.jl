#!/usr/bin/env julia
# object_id: foundation_foundation_r6_ctc_loop_admissibility_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: false

using Dates
using Graphs
using JSON
using LinearAlgebra
using Z3

const RUNG_ID = "foundation_r6_ctc_loop_admissibility"
const OBJECT_ID = "foundation_foundation_r6_ctc_loop_admissibility_julia"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_foundation_r6_ctc_loop_admissibility_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_foundation_r6_ctc_loop_admissibility_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const EVENTS = ["A_prepare", "B_apply", "C_measure", "D_record"]
const BARE_EDGES = [(1, 2), (2, 3), (3, 4)]
const RETRO_EDGE = (4, 1)

function bool_or(ctx, terms::Vector{Z3.Expr})
    isempty(terms) ? Z3.BoolVal(false, ctx) : Z3.Or(terms)
end

function bool_and(ctx, terms::Vector{Z3.Expr})
    isempty(terms) ? Z3.BoolVal(true, ctx) : Z3.And(terms)
end

function edge_matrix(edges::Vector{Tuple{Int,Int}}, n::Int)
    mat = falses(n, n)
    for (src, dst) in edges
        mat[src, dst] = true
    end
    mat
end

function build_graph(edges::Vector{Tuple{Int,Int}}, n::Int)
    g = SimpleDiGraph(n)
    for (src, dst) in edges
        add_edge!(g, src, dst)
    end
    g
end

function has_closed_directed_loop_by_graphs(edges::Vector{Tuple{Int,Int}}, n::Int)
    g = build_graph(edges, n)
    mat = BitMatrix(adjacency_matrix(g) .!= 0)
    reach = transitive_reachability(mat)
    any(reach[i, i] for i in 1:n)
end

function transitive_reachability(mat::BitMatrix)
    n = size(mat, 1)
    reach = copy(mat)
    for k in 1:n, i in 1:n, j in 1:n
        reach[i, j] = reach[i, j] || (reach[i, k] && reach[k, j])
    end
    reach
end

function scenario_signature(edges::Vector{Tuple{Int,Int}}, n::Int)
    mat = edge_matrix(edges, n)
    reach = transitive_reachability(mat)
    edge_bits = Dict{String,Any}()
    for (idx, (src, dst)) in enumerate(vcat(BARE_EDGES, [RETRO_EDGE]))
        edge_bits["M_edge_$(idx)_$(EVENTS[src])_to_$(EVENTS[dst])"] = mat[src, dst]
    end
    Dict{String,Any}(
        "edge_probe_values" => edge_bits,
        "closed_directed_loop_probe" => any(reach[i, i] for i in 1:n),
    )
end

function quotient_classes(scenarios::Dict{String,Vector{Tuple{Int,Int}}}, n::Int)
    groups = Dict{String,Vector{String}}()
    signatures = Dict{String,Any}()
    for (name, edges) in scenarios
        sig = scenario_signature(edges, n)
        key = JSON.json(sig)
        signatures[name] = sig
        if !haskey(groups, key)
            groups[key] = String[]
        end
        push!(groups[key], name)
    end
    classes = Any[]
    for (idx, key) in enumerate(sort(collect(keys(groups))))
        push!(classes, Dict{String,Any}(
            "class_id" => "M_q$(idx - 1)",
            "signature" => JSON.parse(key),
            "members" => sort(groups[key]),
        ))
    end
    loop_groups = Dict("loop_admissible" => String[], "loop_excluded" => String[])
    for (name, sig) in signatures
        push!(loop_groups[sig["closed_directed_loop_probe"] ? "loop_admissible" : "loop_excluded"], name)
    end
    Dict{String,Any}(
        "full_M_class_count" => length(classes),
        "classes" => classes,
        "loop_admissibility_classes" => [
            Dict("class_id" => "loop_excluded", "loop_admissible" => false, "members" => sort(loop_groups["loop_excluded"])),
            Dict("class_id" => "loop_admissible", "loop_admissible" => true, "members" => sort(loop_groups["loop_admissible"])),
        ],
    )
end

function density_constraints(n::Int)
    details = Any[]
    for idx in 1:n
        v = zeros(Float64, n)
        v[idx] = 1.0
        rho = v * v'
        vals = eigvals(Symmetric(rho))
        push!(details, Dict{String,Any}(
            "id" => EVENTS[idx],
            "trace_residual" => abs(tr(rho) - 1.0),
            "hermitian_residual" => norm(rho - rho'),
            "min_eigenvalue" => minimum(vals),
            "normalization_residual" => abs(v' * v - 1.0),
            "psd" => minimum(vals) >= -1.0e-12,
        ))
    end
    Dict{String,Any}(
        "trace_one" => all(row["trace_residual"] <= 1.0e-12 for row in details),
        "hermitian" => all(row["hermitian_residual"] <= 1.0e-12 for row in details),
        "psd" => all(row["psd"] for row in details),
        "normalized" => all(row["normalization_residual"] <= 1.0e-12 for row in details),
        "details" => details,
    )
end

function z3_reachability_cycle_check(edges::Vector{Tuple{Int,Int}}, label::String)
    n = length(EVENTS)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    edge_values = edge_matrix(edges, n)
    edge_vars = [Z3.BoolVar("$(label)_edge_$(i)_$(j)", ctx) for i in 1:n, j in 1:n]
    for i in 1:n, j in 1:n
        Z3.add(solver, edge_vars[i, j] == Z3.BoolVal(edge_values[i, j], ctx))
    end

    prev = edge_vars
    reach_layers = Any[edge_vars]
    for depth in 2:n
        layer = [Z3.BoolVar("$(label)_reach_$(depth)_$(i)_$(j)", ctx) for i in 1:n, j in 1:n]
        for i in 1:n, j in 1:n
            extensions = Z3.Expr[Z3.And(Z3.Expr[edge_vars[i, k], prev[k, j]]) for k in 1:n]
            Z3.add(solver, layer[i, j] == Z3.Or(vcat(Z3.Expr[prev[i, j]], extensions)))
        end
        push!(reach_layers, layer)
        prev = layer
    end
    final_reach = reach_layers[end]
    Z3.add(solver, bool_or(ctx, Z3.Expr[final_reach[i, i] for i in 1:n]))
    Dict{String,Any}(
        "label" => label,
        "verdict" => string(Z3.check(solver)),
        "asserted_edge_equalities" => n * n,
        "derived_reachability_layers" => n,
        "cycle_assertion" => "exists event e with reachability[e,e] derived from bound directed edges",
    )
end

function build_result()
    n = length(EVENTS)
    bare_edges = copy(BARE_EDGES)
    retro_edges = vcat(BARE_EDGES, [RETRO_EDGE])
    dropped_forward_edges = [(1, 2), (3, 4), RETRO_EDGE]
    forced_commutative_edges = unique(vcat(BARE_EDGES, [(dst, src) for (src, dst) in BARE_EDGES]))
    scenarios = Dict(
        "bare_order" => bare_edges,
        "retrocausal_edge_installed" => retro_edges,
        "retro_edge_but_B_to_C_dropped" => dropped_forward_edges,
        "forced_commutative_bare_edges" => forced_commutative_edges,
    )
    constraints = density_constraints(n)
    quotient = quotient_classes(scenarios, n)
    graph_values = Dict(
        "bare_loop_admissible" => has_closed_directed_loop_by_graphs(bare_edges, n),
        "retrocausal_edge_loop_admissible" => has_closed_directed_loop_by_graphs(retro_edges, n),
        "drop_forward_edge_loop_admissible" => has_closed_directed_loop_by_graphs(dropped_forward_edges, n),
        "forced_commutative_loop_admissible" => has_closed_directed_loop_by_graphs(forced_commutative_edges, n),
    )
    z3_bare = z3_reachability_cycle_check(bare_edges, "bare")
    z3_retro = z3_reachability_cycle_check(retro_edges, "retro")
    z3_drop = z3_reachability_cycle_check(dropped_forward_edges, "drop_forward")
    all_pass = (
        READS_PEER_RESULT == false &&
        constraints["trace_one"] &&
        constraints["hermitian"] &&
        constraints["psd"] &&
        constraints["normalized"] &&
        graph_values["bare_loop_admissible"] == false &&
        graph_values["retrocausal_edge_loop_admissible"] == true &&
        graph_values["drop_forward_edge_loop_admissible"] == false &&
        graph_values["forced_commutative_loop_admissible"] == true &&
        z3_bare["verdict"] == "unsat" &&
        z3_retro["verdict"] == "sat" &&
        z3_drop["verdict"] == "unsat"
    )
    Dict{String,Any}(
        "schema_version" => "engine_leg_result_v1",
        "rung_id" => RUNG_ID,
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "active_project" => Base.active_project(),
        "julia_version" => string(VERSION),
        "packages_used" => ["Graphs", "Z3", "LinearAlgebra", "JSON", "Dates"],
        "aligned_packages_load_bearing" => ["Z3"],
        "claim_ceiling" => "Finite directed constraint-order diagnostic only. Closed directed loops are tested on a four-event order; no GR metric, cosmology, Godel, chronology-protection, or promotion claim.",
        "M" => Dict{String,Any}(
            "explicit_probe_family" => [
                "edge(A_prepare,B_apply)",
                "edge(B_apply,C_measure)",
                "edge(C_measure,D_record)",
                "edge(D_record,A_prepare)",
                "closed_directed_loop_exists",
            ],
            "measurement_object" => "finite directed graph of constraint-application events",
        ),
        "C" => Dict{String,Any}(
            "state_constraints" => ["trace=1", "PSD", "Hermiticity", "normalization"],
            "state_constraint_values" => constraints,
            "rung_specific_constraint" => "Bare admissibility order binds edges A->B->C->D and excludes a closed directed loop unless D->A is explicitly installed.",
            "acyclicity_constraint" => "No event may be reachable from itself in the derived transitive closure for the bare order.",
        ),
        "S" => Dict{String,Any}(
            "carrier" => "finite directed causal-order scenarios over four events",
            "events" => EVENTS,
            "scenario_ids" => sort(collect(keys(scenarios))),
        ),
        "S_quotient" => quotient,
        "values" => merge(graph_values, Dict(
            "bare_loop_int" => graph_values["bare_loop_admissible"] ? 1 : 0,
            "retro_loop_int" => graph_values["retrocausal_edge_loop_admissible"] ? 1 : 0,
            "full_M_class_count" => quotient["full_M_class_count"],
            "loop_admissibility_class_count" => length(quotient["loop_admissibility_classes"]),
        )),
        "z3" => Dict("bare" => z3_bare, "retrocausal_edge" => z3_retro, "drop_forward_edge" => z3_drop),
        "negative_control_flip" => Dict{String,Any}(
            "bare_assert_loop_verdict" => z3_bare["verdict"],
            "retrocausal_edge_assert_loop_verdict" => z3_retro["verdict"],
            "drop_forward_edge_after_retro_assert_loop_verdict" => z3_drop["verdict"],
            "force_commutativity_loop_admissible" => graph_values["forced_commutative_loop_admissible"],
            "sat_unsat_flip" => z3_bare["verdict"] == "unsat" && z3_retro["verdict"] == "sat" && z3_drop["verdict"] == "unsat",
            "quotient_changes_when_cycle_probe_dropped" => quotient["full_M_class_count"] > length(quotient["loop_admissibility_classes"]),
        ),
        "forced_vs_installed" => "INSTALLED",
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite directed graph construction and independent cycle check"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing derivation of reachability/cycle existence from bound edge variables"),
            "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive state-constraint diagnostics for finite event-basis density matrices"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization")
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "Z3" => "load_bearing", "LinearAlgebra" => "supportive", "JSON" => "supportive"),
        "all_pass" => all_pass,
    )
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    values = result["values"]
    println("FOUNDATION_R6_JULIA_DONE all_pass=$(result["all_pass"]) bare_loop=$(values["bare_loop_admissible"]) retro_loop=$(values["retrocausal_edge_loop_admissible"]) forced_vs_installed=$(result["forced_vs_installed"])")
    return result["all_pass"] ? 0 : 1
end

exit(main())
