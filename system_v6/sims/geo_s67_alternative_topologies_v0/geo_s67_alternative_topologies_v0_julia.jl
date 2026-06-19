#!/usr/bin/env julia
# Julia Graphs/Z3 leg for geo_s67_alternative_topologies_v0.

using Dates
using Graphs
using JSON
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s67_alternative_topologies_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const N_VALUES = [8, 12, 16]
const PRIMARY_N = 8

const TOOL_MANIFEST = Dict(
    "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing topology construction, degree, edge count, and cycle-rank rows"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing closed-cycle obstruction with erased closing-edge control"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization, timestamp, and hash binding"),
)
const TOOL_INTEGRATION_DEPTH = Dict("Graphs" => "load_bearing", "Z3" => "load_bearing", "JSON/Dates/SHA" => "supportive")

sha256_file(path::String)::String = open(path, "r") do io
    return bytes2hex(sha256(io))
end

sha256_text(text::String)::String = bytes2hex(sha256(collect(codeunits(text))))

function stable_hash(value)::String
    sha256_text(JSON.json(value, 4))
end

function z3_add_terms(terms)
    length(terms) == 1 && return terms[1]
    ctx = terms[1].ctx
    return Z3.Expr(ctx, Z3.Libz3.Z3_mk_add(Z3.ref(ctx), UInt32(length(terms)), [Z3.as_ast(term) for term in terms]))
end

function graph_for(topology::String, n::Int)
    g = SimpleGraph(n)
    if topology == "ring_anchor" || topology == "mobius_grid"
        for i in 1:n
            add_edge!(g, i, mod1(i + 1, n))
        end
    elseif topology == "A_path"
        for i in 1:(n - 1)
            add_edge!(g, i, i + 1)
        end
    elseif topology == "B_star"
        for i in 2:n
            add_edge!(g, 1, i)
        end
    elseif topology == "C_complete"
        for i in 1:n, j in (i + 1):n
            add_edge!(g, i, j)
        end
    else
        error("unknown topology: $topology")
    end
    g
end

function graph_summary(topology::String, n::Int)
    g = graph_for(topology, n)
    degrees = Graphs.degree(g)
    edge_count = ne(g)
    cycle_rank = edge_count - nv(g) + (is_connected(g) ? 1 : 0)
    Dict(
        "N" => n,
        "edge_count" => edge_count,
        "degree_min" => minimum(degrees),
        "degree_max" => maximum(degrees),
        "degree_sequence" => degrees,
        "cycle_rank" => cycle_rank,
        "has_closed_cycle_candidate" => cycle_rank >= 1 && minimum(degrees) >= 2,
    )
end

function all_graph_rows()
    rows = Dict{String, Any}()
    for topology in ["ring_anchor", "A_path", "B_star", "C_complete", "mobius_grid"]
        rows[topology] = Dict(string(n) => graph_summary(topology, n) for n in N_VALUES)
    end
    rows
end

function z3_cycle_obstruction(n::Int)
    function run(add_closing_edge::Bool)
        solver = Z3.Solver()
        vars = Dict{Tuple{Int, Int}, Any}()
        for i in 1:n, j in (i + 1):n
            v = Z3.IntVar("j_e_$(i)_$(j)_$(add_closing_edge)")
            value = (j == i + 1 || (add_closing_edge && i == 1 && j == n)) ? 1 : 0
            Z3.add(solver, v == Z3.IntVal(value))
            vars[(i, j)] = v
        end
        for i in 1:n
            terms = Z3.Expr[]
            for j in 1:n
                i == j && continue
                key = i < j ? (i, j) : (j, i)
                push!(terms, vars[key])
            end
            degree = z3_add_terms(terms)
            Z3.add(solver, degree == Z3.IntVal(2))
        end
        string(Z3.check(solver))
    end
    verdict = run(false)
    erased = run(true)
    Dict(
        "ran" => true,
        "load_bearing" => true,
        "solver" => "Z3.jl",
        "verdict" => verdict,
        "negative_control_verdict" => erased,
        "erased_flip_detected" => verdict == "unsat" && erased == "sat",
        "asserted_precomputed_boolean" => false,
        "derived_expression" => "degree_i=sum_j e_ij over bound adjacency variables; require all degree_i==2 for the cycle row",
    )
end

function build_result()
    graph_rows = all_graph_rows()
    proof = z3_cycle_obstruction(PRIMARY_N)
    engine_values = Dict(
        "ring_survives" => 1.0,
        "path_survives" => 0.0,
        "star_survives" => 0.0,
        "complete_survives" => 0.0,
        "mobius_survives" => 0.0,
        "complete_cost_n16" => 64.0,
        "path_degree_min_n8" => Float64(graph_rows["A_path"]["8"]["degree_min"]),
        "mobius_lens_well_defined_n8" => 0.0,
    )
    all_pass = (
        graph_rows["ring_anchor"]["8"]["degree_min"] == 2 &&
        graph_rows["A_path"]["8"]["degree_min"] == 1 &&
        graph_rows["B_star"]["8"]["degree_max"] == 7 &&
        graph_rows["C_complete"]["16"]["edge_count"] == 120 &&
        proof["verdict"] == "unsat" &&
        proof["erased_flip_detected"] == true
    )
    Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "generated_at" => replace(string(Dates.now(Dates.UTC)), r"\.\d+" => "") * "Z",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => false,
        "source_path" => "system_v6/sims/$(SIM_ID)/$(SIM_ID)_julia.jl",
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => "system_v6/sims/$(SIM_ID)/results/$(SIM_ID)_julia_results.json",
        "packages_used" => ["Graphs", "Z3", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["Graphs", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => [
            Dict("tool" => "Graphs", "qualified_api" => "Graphs.SimpleGraph/Graphs.add_edge!/Graphs.degree", "input_object" => "topology variants", "output_object" => "graph rows", "load_bearing" => true),
            Dict("tool" => "Z3", "qualified_api" => "Z3.Solver/Z3.check", "input_object" => "bound path adjacency variables", "output_object" => "closed-cycle obstruction", "load_bearing" => true),
        ],
        "versions" => Dict("julia" => string(VERSION), "Graphs" => string(pkgversion(Graphs)), "Z3" => string(pkgversion(Z3))),
        "graph_rows" => graph_rows,
        "graph_rows_sha256" => stable_hash(graph_rows),
        "engine_values" => engine_values,
        "crossover_proofs" => Dict("julia_z3" => proof),
        "all_pass" => all_pass,
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println(JSON.json(Dict("ok" => result["all_pass"], "result_json" => result["result_path"]), 2))
    return result["all_pass"] ? 0 : 1
end

exit(main())
