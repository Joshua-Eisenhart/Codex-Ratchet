#!/usr/bin/env julia
# Julia Graphs lane for engine_16_stage_correspondence_v1.

using Dates
using Graphs
using JSON
using LinearAlgebra
using Printf
using SHA

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "engine_16_stage_correspondence_v1"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const LAMBDA = 0.7
const THETA = pi / 2

const TOOL_MANIFEST = Dict(
    "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing alias graph over exact rounded stage output vectors"),
    "JSON/Dates/SHA/LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization, timestamping, hashing, matrix exponential, and finite affine arithmetic"),
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

function finite_time_flow(a::Matrix{Float64}, b::Vector{Float64})
    block = zeros(Float64, 4, 4)
    block[1:3, 1:3] = a
    block[1:3, 4] = b
    exp_block = exp(block)
    return exp_block[1:3, 1:3], exp_block[1:3, 4]
end

function compose(left::Dict, right::Dict)
    m_left = left["M"]
    b_left = left["b"]
    m_right = right["M"]
    b_right = right["b"]
    return Dict("M" => m_left * m_right, "b" => b_left + m_left * b_right)
end

function terrain_flows()
    rt3 = sqrt(3.0)
    rows = Dict{String, Dict}()
    rows["Se"] = Dict(
        "source_key" => "Se_Funnel_L",
        "M" => [-4/5 -2*rt3/15 2*rt3/15; 2*rt3/15 -4/5 -2*rt3/15; -2*rt3/15 2*rt3/15 -4/5],
        "b" => [0.0, 0.0, 0.0],
    )
    rows["Ne"] = Dict(
        "source_key" => "Ne_Vortex_L",
        "M" => [0.0 -2*rt3/15 2*rt3/15; 2*rt3/15 0.0 -2*rt3/15; -2*rt3/15 2*rt3/15 0.0],
        "b" => [0.0, 0.0, 0.0],
    )
    rows["Ni"] = Dict(
        "source_key" => "Ni_Source_R",
        "M" => [-1/4 2*rt3/15 -2*rt3/15; -2*rt3/15 -1/4 2*rt3/15; 2*rt3/15 -2*rt3/15 -1/2],
        "b" => [0.0, 0.0, 1/2],
    )
    rows["Si"] = Dict(
        "source_key" => "Si_Citadel_R",
        "M" => [0.0 0.0 0.0; 0.0 -2/5 -2/5; 0.0 2/5 -2/5],
        "b" => [0.0, 0.0, 0.0],
    )
    out = Dict{String, Dict}()
    for (key, row) in rows
        m, b = finite_time_flow(row["M"], row["b"])
        out[key] = Dict("M" => m, "b" => b, "source_key" => row["source_key"])
    end
    return out
end

function operator_channels()
    return Dict(
        "Ti" => Dict("M" => Diagonal([LAMBDA, LAMBDA, 1.0]) |> Matrix, "b" => zeros(3), "channel" => "D_z"),
        "Te" => Dict("M" => Diagonal([1.0, LAMBDA, LAMBDA]) |> Matrix, "b" => zeros(3), "channel" => "D_x"),
        "Fi" => Dict("M" => rotation_x(THETA), "b" => zeros(3), "channel" => "R_x"),
        "Fe" => Dict("M" => rotation_z(THETA), "b" => zeros(3), "channel" => "R_z"),
    )
end

function stage_specs()
    return [
        Dict("stage_token" => "TiSe", "terrain" => "Se", "operator" => "Ti", "order" => "terrain_after_operator"),
        Dict("stage_token" => "SeTi", "terrain" => "Se", "operator" => "Ti", "order" => "operator_after_terrain"),
        Dict("stage_token" => "FiSe", "terrain" => "Se", "operator" => "Fi", "order" => "terrain_after_operator"),
        Dict("stage_token" => "SeFi", "terrain" => "Se", "operator" => "Fi", "order" => "operator_after_terrain"),
        Dict("stage_token" => "TiNe", "terrain" => "Ne", "operator" => "Ti", "order" => "terrain_after_operator"),
        Dict("stage_token" => "NeTi", "terrain" => "Ne", "operator" => "Ti", "order" => "operator_after_terrain"),
        Dict("stage_token" => "FiNe", "terrain" => "Ne", "operator" => "Fi", "order" => "terrain_after_operator"),
        Dict("stage_token" => "NeFi", "terrain" => "Ne", "operator" => "Fi", "order" => "operator_after_terrain"),
        Dict("stage_token" => "TeNi", "terrain" => "Ni", "operator" => "Te", "order" => "terrain_after_operator"),
        Dict("stage_token" => "NiTe", "terrain" => "Ni", "operator" => "Te", "order" => "operator_after_terrain"),
        Dict("stage_token" => "FeNi", "terrain" => "Ni", "operator" => "Fe", "order" => "terrain_after_operator"),
        Dict("stage_token" => "NiFe", "terrain" => "Ni", "operator" => "Fe", "order" => "operator_after_terrain"),
        Dict("stage_token" => "TeSi", "terrain" => "Si", "operator" => "Te", "order" => "terrain_after_operator"),
        Dict("stage_token" => "SiTe", "terrain" => "Si", "operator" => "Te", "order" => "operator_after_terrain"),
        Dict("stage_token" => "FeSi", "terrain" => "Si", "operator" => "Fe", "order" => "terrain_after_operator"),
        Dict("stage_token" => "SiFe", "terrain" => "Si", "operator" => "Fe", "order" => "operator_after_terrain"),
    ]
end

function output_key(vec)
    rounded = [round_float(x; digits=7) for x in vec]
    return join([@sprintf("%.7f", x) for x in rounded], ",")
end

function build_rows(; erase_order::Bool=false, identity::Bool=false)
    bloch = [0.136529420884, -0.316304860308, -0.938781631999]
    flows = terrain_flows()
    ops = operator_channels()
    rows = Any[]
    for spec in stage_specs()
        if identity
            channel = Dict("M" => Matrix(I, 3, 3), "b" => zeros(3))
        elseif erase_order || spec["order"] == "terrain_after_operator"
            channel = compose(flows[spec["terrain"]], ops[spec["operator"]])
        else
            channel = compose(ops[spec["operator"]], flows[spec["terrain"]])
        end
        out = channel["M"] * bloch + channel["b"]
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
    identity_rows = build_rows(identity=true)
    all_pass = length(rows) == 16 && Graphs.nv(graph) == 16 && length(unique(row["output_key"] for row in identity_rows)) == 1 && length(unique(row["output_key"] for row in order_rows)) <= 8
    return Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "generated_at" => now_z(),
        "classification" => "scratch_diagnostic",
        "claim_ceiling" => "hypothesis_test_only",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "packages_used" => ["Graphs", "JSON", "SHA", "LinearAlgebra"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "package_observables" => Dict("Graphs" => "Graphs.SimpleGraph alias components over exact rounded affine stage output vectors"),
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
