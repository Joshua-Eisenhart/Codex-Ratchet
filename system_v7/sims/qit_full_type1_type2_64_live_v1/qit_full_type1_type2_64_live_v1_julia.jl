#!/usr/bin/env julia
# Julia graph/Z3 leg for qit_full_type1_type2_64_live_v1.
#
# Ceiling: SCRATCH_DIAGNOSTIC. This leg recomputes the atlas schedule counts,
# loop graph closure, and ordered-vs-bag signature polarity. It does not read
# peer result files.

using Dates
using Graphs
using JSON
using SHA
using Z3

const SIM_ID = "qit_full_type1_type2_64_live_v1"
const HERE = @__DIR__
const REPO = normpath(joinpath(HERE, "..", "..", ".."))
const RESULTS = joinpath(HERE, "results")
const SOURCE_PATH = joinpath(HERE, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULTS, "$(SIM_ID)_julia_results.json")

const CLASSIFICATION = "scratch_diagnostic"

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

function macro_rows()
    [
        Dict("object_id"=>"T1_outer_deductive", "engine_type"=>"Type-1", "sheet"=>"T1_IN", "loop"=>"outer", "topology"=>"Se", "token"=>"TiSe", "igt_result"=>"LOSE", "signed_operator"=>"Ti^", "precedence"=>"operator_first"),
        Dict("object_id"=>"T1_outer_deductive", "engine_type"=>"Type-1", "sheet"=>"T1_IN", "loop"=>"outer", "topology"=>"Ne", "token"=>"NeTi", "igt_result"=>"WIN", "signed_operator"=>"Ti_v", "precedence"=>"terrain_first"),
        Dict("object_id"=>"T1_outer_deductive", "engine_type"=>"Type-1", "sheet"=>"T1_IN", "loop"=>"outer", "topology"=>"Ni", "token"=>"NiFe", "igt_result"=>"LOSE", "signed_operator"=>"Fe_v", "precedence"=>"terrain_first"),
        Dict("object_id"=>"T1_outer_deductive", "engine_type"=>"Type-1", "sheet"=>"T1_IN", "loop"=>"outer", "topology"=>"Si", "token"=>"FeSi", "igt_result"=>"WIN", "signed_operator"=>"Fe^", "precedence"=>"operator_first"),
        Dict("object_id"=>"T1_inner_inductive", "engine_type"=>"Type-1", "sheet"=>"T1_IN", "loop"=>"inner", "topology"=>"Se", "token"=>"SeFi", "igt_result"=>"win", "signed_operator"=>"Fi_v", "precedence"=>"terrain_first"),
        Dict("object_id"=>"T1_inner_inductive", "engine_type"=>"Type-1", "sheet"=>"T1_IN", "loop"=>"inner", "topology"=>"Si", "token"=>"SiTe", "igt_result"=>"win", "signed_operator"=>"Te_v", "precedence"=>"terrain_first"),
        Dict("object_id"=>"T1_inner_inductive", "engine_type"=>"Type-1", "sheet"=>"T1_IN", "loop"=>"inner", "topology"=>"Ni", "token"=>"TeNi", "igt_result"=>"lose", "signed_operator"=>"Te^", "precedence"=>"operator_first"),
        Dict("object_id"=>"T1_inner_inductive", "engine_type"=>"Type-1", "sheet"=>"T1_IN", "loop"=>"inner", "topology"=>"Ne", "token"=>"FiNe", "igt_result"=>"lose", "signed_operator"=>"Fi^", "precedence"=>"operator_first"),
        Dict("object_id"=>"T2_outer_inductive", "engine_type"=>"Type-2", "sheet"=>"T2_OUT", "loop"=>"outer", "topology"=>"Se", "token"=>"FiSe", "igt_result"=>"WIN", "signed_operator"=>"Fi^", "precedence"=>"operator_first"),
        Dict("object_id"=>"T2_outer_inductive", "engine_type"=>"Type-2", "sheet"=>"T2_OUT", "loop"=>"outer", "topology"=>"Si", "token"=>"TeSi", "igt_result"=>"WIN", "signed_operator"=>"Te^", "precedence"=>"operator_first"),
        Dict("object_id"=>"T2_outer_inductive", "engine_type"=>"Type-2", "sheet"=>"T2_OUT", "loop"=>"outer", "topology"=>"Ni", "token"=>"NiTe", "igt_result"=>"LOSE", "signed_operator"=>"Te_v", "precedence"=>"terrain_first"),
        Dict("object_id"=>"T2_outer_inductive", "engine_type"=>"Type-2", "sheet"=>"T2_OUT", "loop"=>"outer", "topology"=>"Ne", "token"=>"NeFi", "igt_result"=>"LOSE", "signed_operator"=>"Fi_v", "precedence"=>"terrain_first"),
        Dict("object_id"=>"T2_inner_deductive", "engine_type"=>"Type-2", "sheet"=>"T2_OUT", "loop"=>"inner", "topology"=>"Se", "token"=>"SeTi", "igt_result"=>"lose", "signed_operator"=>"Ti_v", "precedence"=>"terrain_first"),
        Dict("object_id"=>"T2_inner_deductive", "engine_type"=>"Type-2", "sheet"=>"T2_OUT", "loop"=>"inner", "topology"=>"Ne", "token"=>"TiNe", "igt_result"=>"win", "signed_operator"=>"Ti^", "precedence"=>"operator_first"),
        Dict("object_id"=>"T2_inner_deductive", "engine_type"=>"Type-2", "sheet"=>"T2_OUT", "loop"=>"inner", "topology"=>"Ni", "token"=>"FeNi", "igt_result"=>"lose", "signed_operator"=>"Fe^", "precedence"=>"operator_first"),
        Dict("object_id"=>"T2_inner_deductive", "engine_type"=>"Type-2", "sheet"=>"T2_OUT", "loop"=>"inner", "topology"=>"Si", "token"=>"SiFe", "igt_result"=>"win", "signed_operator"=>"Fe_v", "precedence"=>"terrain_first")
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

function rows_by_object(rows)
    grouped = Dict(id => Any[] for id in object_ids(rows))
    for row in rows
        push!(grouped[row["object_id"]], row)
    end
    return grouped
end

function build_schedule(rows)
    schedule = Any[]
    idx = 0
    macro_idx = 0
    for row in rows
        for substage in 0:3
            push!(schedule, merge(row, Dict("slot_index"=>idx, "macro_index"=>macro_idx, "substage_index"=>substage, "chart_locked"=>substage == 0)))
            idx += 1
        end
        macro_idx += 1
    end
    return schedule
end

function ordered_signature(rows)
    join([join([row["topology"], row["token"], row["igt_result"], row["signed_operator"], row["precedence"], row["loop"], row["engine_type"]], "|") for row in rows], "->")
end

function bag_signature(rows)
    join(sort([row["topology"] for row in rows]), "|")
end

function loop_graph(rows)
    topo_idx = Dict("Se"=>1, "Ne"=>2, "Ni"=>3, "Si"=>4)
    g = SimpleDiGraph(4)
    topologies = [row["topology"] for row in rows]
    closed = vcat(topologies, [topologies[1]])
    for i in 1:(length(closed)-1)
        add_edge!(g, topo_idx[closed[i]], topo_idx[closed[i+1]])
    end
    return g
end

function z3_gate(object_count::Int, ordered_unique::Int, bag_unique::Int)::String
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    objects = Z3.IntVar("objects", ctx)
    ordered = Z3.IntVar("ordered_unique", ctx)
    bag = Z3.IntVar("bag_unique", ctx)
    Z3.add(solver, objects == Z3.IntVal(object_count, ctx))
    Z3.add(solver, ordered == Z3.IntVal(ordered_unique, ctx))
    Z3.add(solver, bag == Z3.IntVal(bag_unique, ctx))
    gate = Z3.And(Z3.Expr[
        objects == Z3.IntVal(4, ctx),
        ordered == objects,
        bag < objects
    ])
    Z3.add(solver, Z3.Not(gate))
    return string(Z3.check(solver))
end

function main()
    mkpath(RESULTS)
    rows = macro_rows()
    schedule = build_schedule(rows)
    grouped = rows_by_object(rows)
    ordered_sigs = Dict(id => ordered_signature(grouped[id]) for id in keys(grouped))
    bag_sigs = Dict(id => bag_signature(grouped[id]) for id in keys(grouped))
    graphs = Dict(id => Dict("vertices"=>nv(loop_graph(grouped[id])), "edges"=>ne(loop_graph(grouped[id]))) for id in keys(grouped))
    ordered_unique = length(Set(values(ordered_sigs)))
    bag_unique = length(Set(values(bag_sigs)))
    object_count = length(keys(grouped))
    z3_verdict = z3_gate(object_count, ordered_unique, bag_unique)
    all_pass = (
        length(schedule) == 64 &&
        length(rows) == 16 &&
        count(row -> row["engine_type"] == "Type-1", schedule) == 32 &&
        count(row -> row["engine_type"] == "Type-2", schedule) == 32 &&
        count(row -> row["chart_locked"], schedule) == 16 &&
        ordered_unique == object_count &&
        bag_unique < object_count &&
        all(info["edges"] == 4 for info in values(graphs)) &&
        z3_verdict == "unsat"
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
        "object_count" => object_count,
        "slot_count" => length(schedule),
        "macro_stage_count" => length(rows),
        "type1_slots" => count(row -> row["engine_type"] == "Type-1", schedule),
        "type2_slots" => count(row -> row["engine_type"] == "Type-2", schedule),
        "chart_locked_slots" => count(row -> row["chart_locked"], schedule),
        "ordered_unique_count" => ordered_unique,
        "bag_unique_count" => bag_unique,
        "loop_graphs" => graphs,
        "julia_z3" => Dict("ran"=>true, "verdict"=>z3_verdict, "load_bearing"=>true),
        "packages_used" => ["Graphs", "Z3", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "package_observables" => Dict(
            "Graphs" => "SimpleDiGraph loop closure with four directed edges per loop object",
            "Z3" => "UNSAT negation of ordered_unique=object_count and bag_unique<object_count gate"
        ),
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("tried"=>true, "used"=>true, "reason"=>"load-bearing directed loop closure graph for each object"),
            "Z3" => Dict("tried"=>true, "used"=>true, "reason"=>"load-bearing Julia-side structural polarity proof"),
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
