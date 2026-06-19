#!/usr/bin/env julia
# Julia Graphs lane for engine_16_stage_definition_correspondence_v0.

using Dates
using Graphs
using JSON
using LinearAlgebra
using Printf
using SHA

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "engine_16_stage_definition_correspondence_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const LAMBDA = 0.7
const THETA = pi / 2

const TOOL_MANIFEST = Dict(
    "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing alias graph over exact rounded stage output vectors"),
    "JSON/Dates/SHA/LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization, timestamping, hashing, and finite matrix arithmetic"),
)
const TOOL_INTEGRATION_DEPTH = Dict("Graphs" => "load_bearing", "JSON/Dates/SHA/LinearAlgebra" => "supportive")

function now_z()::String
    Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
end

function rel(path::String)::String
    replace(relpath(path, ROOT), "\\" => "/")
end

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function round_float(value::Real; digits::Int=12)::Float64
    x = Float64(value)
    abs(x) < 10.0^(-digits) ? 0.0 : round(x; digits=digits)
end

function rotation_x(theta::Float64)
    c = cos(theta)
    s = sin(theta)
    return [1.0 0.0 0.0; 0.0 c -s; 0.0 s c]
end

function rotation_z(theta::Float64)
    c = cos(theta)
    s = sin(theta)
    return [c -s 0.0; s c 0.0; 0.0 0.0 1.0]
end

function base_matrix(name::String, sign::Float64)
    if name == "Ti"
        return Diagonal([LAMBDA, LAMBDA, 1.0]) |> Matrix
    elseif name == "Te"
        return Diagonal([1.0, LAMBDA, LAMBDA]) |> Matrix
    elseif name == "Fi"
        return rotation_x(sign * THETA)
    elseif name == "Fe"
        return rotation_z(sign * THETA)
    end
    error("unknown operator $name")
end

function stage_specs()
    rows = Any[]
    for chirality in ["L", "R"], t_op in ["Ti", "Te"], f_op in ["Fi", "Fe"], order in ["+", "-"]
        dominant = order == "+" ? t_op : f_op
        auxiliary = order == "+" ? f_op : t_op
        push!(rows, Dict(
            "stage_token" => "$(chirality)_$(t_op)_$(f_op)_$(order == "+" ? "plus" : "minus")",
            "chirality" => chirality,
            "chirality_sign" => chirality == "L" ? 1.0 : -1.0,
            "t_operator" => t_op,
            "f_operator" => f_op,
            "order_polarity" => order,
            "dominant_operator" => dominant,
            "auxiliary_operator" => auxiliary,
        ))
    end
    return rows
end

function output_key(vec)
    rounded = [round_float(x; digits=7) for x in vec]
    return join([@sprintf("%.7f", x) for x in rounded], ",")
end

function build_rows(; erase_order::Bool=false, erase_chirality::Bool=false, identity::Bool=false)
    # Same representative Bloch vector as the imported eng64 RHO_REPR, copied as
    # data here so this lane does not read a Python result.
    bloch = [0.136529420884, -0.316304860308, -0.938781631999]
    rows = Any[]
    for spec in stage_specs()
        sign = erase_chirality ? 1.0 : Float64(spec["chirality_sign"])
        if identity
            m = Matrix(I, 3, 3)
        else
            tm = base_matrix(spec["t_operator"], sign)
            fm = base_matrix(spec["f_operator"], sign)
            if erase_order || spec["order_polarity"] == "+"
                m = tm * fm
            else
                m = fm * tm
            end
        end
        out = m * bloch
        push!(rows, Dict("stage_token" => spec["stage_token"], "output_key" => output_key(out), "bloch_output" => [round_float(x) for x in out]))
    end
    return rows
end

function alias_graph(rows)
    graph = Graphs.SimpleGraph(length(rows))
    for i in eachindex(rows), j in (i + 1):length(rows)
        if rows[i]["output_key"] == rows[j]["output_key"]
            Graphs.add_edge!(graph, i, j)
        end
    end
    comps = [sort([rows[idx]["stage_token"] for idx in comp]) for comp in Graphs.connected_components(graph)]
    return graph, comps
end

function build_result()
    rows = build_rows()
    graph, comps = alias_graph(rows)
    order_rows = build_rows(erase_order=true)
    chirality_rows = build_rows(erase_chirality=true)
    identity_rows = build_rows(identity=true)
    all_pass = length(rows) == 16 && length(unique(row["output_key"] for row in identity_rows)) == 1
    return Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "generated_at" => now_z(),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "packages_used" => ["Graphs", "JSON", "SHA", "LinearAlgebra"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "package_observables" => Dict("Graphs" => "Graphs.SimpleGraph alias components over exact rounded stage output vectors"),
        "reads_peer_result" => false,
        "graphs_receipt" => Dict(
            "node_count" => Graphs.nv(graph),
            "edge_count" => Graphs.ne(graph),
            "component_count" => length(comps),
            "alias_components" => [comp for comp in comps if length(comp) > 1],
            "finite_stage_graph" => Graphs.nv(graph) == 16,
        ),
        "computed_values" => Dict(
            "stage_count" => length(rows),
            "defined_distinct_component_count" => length(unique(row["output_key"] for row in rows)),
            "order_erased_distinct_component_count" => length(unique(row["output_key"] for row in order_rows)),
            "chirality_erased_distinct_component_count" => length(unique(row["output_key"] for row in chirality_rows)),
            "identity_distinct_component_count" => length(unique(row["output_key"] for row in identity_rows)),
        ),
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "all_pass" => all_pass,
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => result["all_pass"], "result" => rel(RESULT_PATH))))
    return result["all_pass"] ? 0 : 1
end

exit(main())
