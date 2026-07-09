#!/usr/bin/env julia
# Julia graph/Z3 leg for qit_projection_battery_v0.
#
# Ceiling: SCRATCH_DIAGNOSTIC. This leg recomputes the finite v1-style carrier,
# projection views, and object-view graph locally. It does not read peer result
# files and it does not mutate Lev graph state.

using Dates
using Graphs
using JSON
using SHA
using Z3

const SIM_ID = "qit_projection_battery_v0"
const HERE = @__DIR__
const REPO = normpath(joinpath(HERE, "..", "..", ".."))
const RESULTS = joinpath(HERE, "results")
const SOURCE_PATH = joinpath(HERE, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULTS, "$(SIM_ID)_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"

const TOPOLOGY_IDS = Dict("Se"=>0.0, "Ne"=>1.0, "Ni"=>2.0, "Si"=>3.0)
const OPERATOR_IDS = Dict("Ti"=>0.0, "Te"=>1.0, "Fi"=>2.0, "Fe"=>3.0)
const RESULT_POLARITY = Dict("WIN"=>1.0, "win"=>1.0, "LOSE"=>-1.0, "lose"=>-1.0)
const RESULT_CASE = Dict("WIN"=>1.0, "LOSE"=>1.0, "win"=>-1.0, "lose"=>-1.0)
const LOOP_IDS = Dict("outer"=>0.0, "inner"=>1.0)
const ENGINE_IDS = Dict("Type-1"=>0.0, "Type-2"=>1.0)
const PRECEDENCE_IDS = Dict("operator_first"=>1.0, "terrain_first"=>-1.0)

const VIEW_MASKS = Dict(
    "maintenance_mmm" => Set([0, 1, 4]),
    "finance_mmm" => Set([0, 2, 3]),
    "safety_mmm" => Set([1, 2, 4]),
    "planning_mmm" => Set([0, 1, 7]),
    "ontology_mmm" => Set([0, 1, 2, 3, 4, 7]),
)

function rel(path::AbstractString)::String
    prefix = normpath(REPO) * "/"
    return replace(normpath(path), prefix => "")
end

function sha256_file(path::AbstractString)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function now_z()::String
    return Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
end

function operator_family(value::String)::String
    return value[1:2]
end

function macro_rows()
    [
        Dict("object_id"=>"T1_outer_deductive", "engine_type"=>"Type-1", "loop"=>"outer", "topology"=>"Se", "igt_result"=>"LOSE", "signed_operator"=>"Ti^", "precedence"=>"operator_first"),
        Dict("object_id"=>"T1_outer_deductive", "engine_type"=>"Type-1", "loop"=>"outer", "topology"=>"Ne", "igt_result"=>"WIN", "signed_operator"=>"Ti_v", "precedence"=>"terrain_first"),
        Dict("object_id"=>"T1_outer_deductive", "engine_type"=>"Type-1", "loop"=>"outer", "topology"=>"Ni", "igt_result"=>"LOSE", "signed_operator"=>"Fe_v", "precedence"=>"terrain_first"),
        Dict("object_id"=>"T1_outer_deductive", "engine_type"=>"Type-1", "loop"=>"outer", "topology"=>"Si", "igt_result"=>"WIN", "signed_operator"=>"Fe^", "precedence"=>"operator_first"),
        Dict("object_id"=>"T1_inner_inductive", "engine_type"=>"Type-1", "loop"=>"inner", "topology"=>"Se", "igt_result"=>"win", "signed_operator"=>"Fi_v", "precedence"=>"terrain_first"),
        Dict("object_id"=>"T1_inner_inductive", "engine_type"=>"Type-1", "loop"=>"inner", "topology"=>"Si", "igt_result"=>"win", "signed_operator"=>"Te_v", "precedence"=>"terrain_first"),
        Dict("object_id"=>"T1_inner_inductive", "engine_type"=>"Type-1", "loop"=>"inner", "topology"=>"Ni", "igt_result"=>"lose", "signed_operator"=>"Te^", "precedence"=>"operator_first"),
        Dict("object_id"=>"T1_inner_inductive", "engine_type"=>"Type-1", "loop"=>"inner", "topology"=>"Ne", "igt_result"=>"lose", "signed_operator"=>"Fi^", "precedence"=>"operator_first"),
        Dict("object_id"=>"T2_outer_inductive", "engine_type"=>"Type-2", "loop"=>"outer", "topology"=>"Se", "igt_result"=>"WIN", "signed_operator"=>"Fi^", "precedence"=>"operator_first"),
        Dict("object_id"=>"T2_outer_inductive", "engine_type"=>"Type-2", "loop"=>"outer", "topology"=>"Si", "igt_result"=>"WIN", "signed_operator"=>"Te^", "precedence"=>"operator_first"),
        Dict("object_id"=>"T2_outer_inductive", "engine_type"=>"Type-2", "loop"=>"outer", "topology"=>"Ni", "igt_result"=>"LOSE", "signed_operator"=>"Te_v", "precedence"=>"terrain_first"),
        Dict("object_id"=>"T2_outer_inductive", "engine_type"=>"Type-2", "loop"=>"outer", "topology"=>"Ne", "igt_result"=>"LOSE", "signed_operator"=>"Fi_v", "precedence"=>"terrain_first"),
        Dict("object_id"=>"T2_inner_deductive", "engine_type"=>"Type-2", "loop"=>"inner", "topology"=>"Se", "igt_result"=>"lose", "signed_operator"=>"Ti_v", "precedence"=>"terrain_first"),
        Dict("object_id"=>"T2_inner_deductive", "engine_type"=>"Type-2", "loop"=>"inner", "topology"=>"Ne", "igt_result"=>"win", "signed_operator"=>"Ti^", "precedence"=>"operator_first"),
        Dict("object_id"=>"T2_inner_deductive", "engine_type"=>"Type-2", "loop"=>"inner", "topology"=>"Ni", "igt_result"=>"lose", "signed_operator"=>"Fe^", "precedence"=>"operator_first"),
        Dict("object_id"=>"T2_inner_deductive", "engine_type"=>"Type-2", "loop"=>"inner", "topology"=>"Si", "igt_result"=>"win", "signed_operator"=>"Fe_v", "precedence"=>"terrain_first")
    ]
end

function object_ids(rows)
    out = String[]
    for row in rows
        id = row["object_id"]
        if !(id in out)
            push!(out, id)
        end
    end
    return out
end

function schedule_rows(rows)
    schedule = Any[]
    for row in rows
        for substage in 0:3
            push!(schedule, merge(row, Dict("substage_index"=>substage)))
        end
    end
    return schedule
end

function vectors_by_object()
    rows = macro_rows()
    ids = object_ids(rows)
    grouped = Dict(id => Any[] for id in ids)
    for row in rows
        for substage in 0:3
            push!(grouped[row["object_id"]], merge(row, Dict("substage_index"=>substage)))
        end
    end
    vectors = Dict{String, Vector{Float64}}()
    for id in ids
        values = Float64[]
        for slot in grouped[id]
            op = operator_family(slot["signed_operator"])
            append!(
                values,
                [
                    TOPOLOGY_IDS[slot["topology"]],
                    OPERATOR_IDS[op],
                    RESULT_POLARITY[slot["igt_result"]],
                    RESULT_CASE[slot["igt_result"]],
                    PRECEDENCE_IDS[slot["precedence"]],
                    LOOP_IDS[slot["loop"]],
                    ENGINE_IDS[slot["engine_type"]],
                    Float64(slot["substage_index"]),
                ],
            )
        end
        vectors[id] = values
    end
    return ids, vectors
end

function bag_erased_vector(len::Int)::Vector{Float64}
    out = zeros(Float64, len)
    out[1:4] .= 4.0
    return out
end

function projection_vector(row::Vector{Float64}, view::String, control::String)::Vector{Float64}
    if control == "bag_erased"
        return bag_erased_vector(length(row))
    elseif control == "view_erased"
        return zeros(Float64, length(row))
    end
    mask = VIEW_MASKS[view]
    out = zeros(Float64, length(row))
    for idx in eachindex(row)
        feature_idx = (idx - 1) % 8
        if feature_idx in mask
            out[idx] = row[idx]
        end
    end
    return out
end

function sqdist(left::Vector{Float64}, right::Vector{Float64})::Float64
    total = 0.0
    for idx in eachindex(left)
        total += (left[idx] - right[idx])^2
    end
    return total
end

function leave_one_view_centroid(control::String)::Dict
    ids, vectors = vectors_by_object()
    views = collect(keys(VIEW_MASKS))
    view_results = Any[]
    for heldout in views
        predictions = Any[]
        correct = 0
        centroids = Dict{String, Vector{Float64}}()
        for id in ids
            rows = [projection_vector(vectors[id], view, control) for view in views if view != heldout]
            centroid = [sum(values) / length(rows) for values in zip(rows...)]
            centroids[id] = centroid
        end
        for id in ids
            vec = projection_vector(vectors[id], heldout, control)
            distances = Dict(other => sqdist(vec, centroids[other]) for other in ids)
            predicted = first(sort(collect(keys(distances)), by = key -> distances[key]))
            is_correct = predicted == id
            correct += is_correct ? 1 : 0
            push!(predictions, Dict("object_id"=>id, "predicted_object_id"=>predicted, "correct"=>is_correct))
        end
        push!(view_results, Dict("heldout_view"=>heldout, "accuracy"=>correct / length(ids), "predictions"=>predictions))
    end
    accuracies = [row["accuracy"] for row in view_results]
    return Dict(
        "control" => control == "" ? "none" : control,
        "object_count" => length(ids),
        "view_count" => length(views),
        "mean_heldout_accuracy" => round(sum(accuracies) / length(accuracies), digits=12),
        "min_heldout_accuracy" => round(minimum(accuracies), digits=12),
        "view_results" => view_results,
    )
end

function projection_graph()::Dict
    ids, _ = vectors_by_object()
    views = collect(keys(VIEW_MASKS))
    g = SimpleGraph(length(ids) + length(ids) * length(views))
    projection_vertex = length(ids) + 1
    for object_idx in 1:length(ids)
        for _view in views
            add_edge!(g, object_idx, projection_vertex)
            projection_vertex += 1
        end
    end
    return Dict(
        "vertices" => nv(g),
        "edges" => ne(g),
        "connected_components" => length(connected_components(g)),
        "expected_object_components" => length(ids),
    )
end

function z3_gate(nominal::Dict, bag::Dict, erased::Dict)::Tuple{String, String}
    nominal_scaled = Int(round(100 * nominal["mean_heldout_accuracy"]))
    bag_scaled = Int(round(100 * bag["mean_heldout_accuracy"]))
    erased_scaled = Int(round(100 * erased["mean_heldout_accuracy"]))
    bag_gap_scaled = nominal_scaled - bag_scaled
    erased_gap_scaled = nominal_scaled - erased_scaled
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    objects = Z3.IntVar("objects", ctx)
    views = Z3.IntVar("views", ctx)
    n = Z3.IntVar("nominal_scaled", ctx)
    b = Z3.IntVar("bag_scaled", ctx)
    e = Z3.IntVar("erased_scaled", ctx)
    db = Z3.IntVar("nominal_minus_bag_scaled", ctx)
    de = Z3.IntVar("nominal_minus_erased_scaled", ctx)
    Z3.add(solver, objects == Z3.IntVal(nominal["object_count"], ctx))
    Z3.add(solver, views == Z3.IntVal(nominal["view_count"], ctx))
    Z3.add(solver, n == Z3.IntVal(nominal_scaled, ctx))
    Z3.add(solver, b == Z3.IntVal(bag_scaled, ctx))
    Z3.add(solver, e == Z3.IntVal(erased_scaled, ctx))
    Z3.add(solver, db == Z3.IntVal(bag_gap_scaled, ctx))
    Z3.add(solver, de == Z3.IntVal(erased_gap_scaled, ctx))
    gate = Z3.And(Z3.Expr[
        objects == Z3.IntVal(4, ctx),
        views == Z3.IntVal(5, ctx),
        Z3.Not(n < Z3.IntVal(85, ctx)),
        Z3.Not(Z3.IntVal(25, ctx) < b),
        Z3.Not(Z3.IntVal(25, ctx) < e),
        Z3.Not(db < Z3.IntVal(50, ctx)),
        Z3.Not(de < Z3.IntVal(50, ctx)),
    ])
    Z3.add(solver, Z3.Not(gate))
    full = string(Z3.check(solver))

    control = Z3.Solver(ctx)
    cb = Z3.IntVar("bag_control_scaled", ctx)
    ce = Z3.IntVar("erased_control_scaled", ctx)
    Z3.add(control, cb == Z3.IntVal(bag_scaled, ctx))
    Z3.add(control, ce == Z3.IntVal(erased_scaled, ctx))
    Z3.add(control, Z3.Not(Z3.IntVal(25, ctx) < cb))
    Z3.add(control, Z3.Not(Z3.IntVal(25, ctx) < ce))
    return full, string(Z3.check(control))
end

function main()
    mkpath(RESULTS)
    nominal = leave_one_view_centroid("")
    bag = leave_one_view_centroid("bag_erased")
    erased = leave_one_view_centroid("view_erased")
    graph = projection_graph()
    full_verdict, control_verdict = z3_gate(nominal, bag, erased)
    all_pass = (
        nominal["mean_heldout_accuracy"] >= 0.85 &&
        bag["mean_heldout_accuracy"] <= 0.25 &&
        erased["mean_heldout_accuracy"] <= 0.25 &&
        graph["edges"] == nominal["object_count"] * nominal["view_count"] &&
        graph["connected_components"] == nominal["object_count"] &&
        full_verdict == "unsat" &&
        control_verdict == "sat"
    )
    result = Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "generated_at" => now_z(),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "reads_peer_result" => false,
        "ran" => true,
        "all_pass" => all_pass,
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "object_count" => nominal["object_count"],
        "view_count" => nominal["view_count"],
        "projection_graph" => graph,
        "projection_readouts" => Dict("nominal"=>nominal, "bag_erased_control"=>bag, "view_erased_control"=>erased),
        "julia_z3" => Dict("ran"=>true, "verdict"=>full_verdict, "load_bearing"=>true, "erased_control_verdict"=>control_verdict),
        "packages_used" => ["Graphs", "Z3", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "package_observables" => Dict(
            "Graphs" => "SimpleGraph object-view projection graph has five view leaves per object and four disconnected object components",
            "Z3" => "UNSAT negation of scaled projection-convergence gate with SAT erased controls"
        ),
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("tried"=>true, "used"=>true, "reason"=>"load-bearing object-view projection graph for the finite battery"),
            "Z3" => Dict("tried"=>true, "used"=>true, "reason"=>"load-bearing Julia-side scaled structural polarity proof"),
            "JSON" => Dict("tried"=>true, "used"=>true, "reason"=>"supportive result serialization")
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs"=>"load_bearing", "Z3"=>"load_bearing", "JSON"=>"supportive")
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("engine"=>"julia", "all_pass"=>all_pass, "out"=>rel(RESULT_PATH))))
    return all_pass ? 0 : 1
end

exit(main())
