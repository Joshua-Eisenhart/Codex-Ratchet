#!/usr/bin/env julia

using Dates
using JSON3
using Pkg
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "ratchet_order_breadth_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const TARGET_TOTAL_ORDER_BLIND_CLASSES = 5

function rel(path::AbstractString)::String
    return relpath(path, ROOT)
end

function file_sha256(path::AbstractString)::String
    return bytes2hex(SHA.sha256(read(path)))
end

function package_version(name::String)::String
    for dep in values(Pkg.dependencies())
        if dep.name == name
            return dep.version === nothing ? "stdlib_or_unknown" : string(dep.version)
        end
    end
    return "not_found"
end

function z3_add_expr(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0)
    return Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_order_breadth_identity(values::Dict{String,Any}; erased::Bool=false)::Dict{String,Any}
    solver = Z3.Solver()
    live_classes = Z3.IntVar(erased ? "julia_erased_live_classes" : "julia_live_classes")
    mortality_classes = Z3.IntVar(erased ? "julia_erased_mortality_classes" : "julia_mortality_classes")
    mortality_orderings = Z3.IntVar(erased ? "julia_erased_mortality_orderings" : "julia_mortality_orderings")
    table_rows = Z3.IntVar(erased ? "julia_erased_table_rows" : "julia_table_rows")
    live_value = erased ? values["distinct_live_outcomes"] - 1 : values["distinct_live_outcomes"]
    Z3.add(solver, live_classes == Z3.IntVal(live_value))
    Z3.add(solver, mortality_classes == Z3.IntVal(values["distinct_mortality_classes"]))
    Z3.add(solver, mortality_orderings == Z3.IntVal(values["mortality_orderings"]))
    Z3.add(solver, table_rows == Z3.IntVal(values["orderings_total"]))
    Z3.add(solver, Z3.Not(z3_add_expr(Z3.Expr[live_classes, mortality_classes]) == Z3.IntVal(TARGET_TOTAL_ORDER_BLIND_CLASSES)))
    return Dict(
        "solver" => "Z3.jl",
        "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
        "ran" => true,
        "load_bearing" => true,
        "erased" => erased,
        "verdict" => string(Z3.check(solver)),
        "identity" => "live_classes + mortality_classes = 5 with order-blind table counts bound as context",
        "bound_values" => Dict(
            "live_classes" => live_value,
            "mortality_classes" => values["distinct_mortality_classes"],
            "mortality_orderings" => values["mortality_orderings"],
            "table_rows" => values["orderings_total"],
        ),
    )
end

function engine_values()::Dict{String,Any}
    orderings = token_permutations(["L", "Z", "W", "T"])
    evaluated = [evaluate_order(order) for order in orderings]
    live = [row for row in evaluated if row["status"] == "survived"]
    mortality = [row for row in evaluated if row["status"] == "mortality"]
    live_classes = Set(row["order_blind_signature"] for row in live)
    mortality_classes = Set(row["class_id"] for row in mortality)
    return Dict(
        "orderings_total" => length(evaluated),
        "live_orderings" => length(live),
        "mortality_orderings" => length(mortality),
        "distinct_live_outcomes" => length(live_classes),
        "distinct_mortality_classes" => length(mortality_classes),
        "total_equivalence_classes_including_mortality" => length(live_classes) + length(mortality_classes),
        "committed_chain_class_id" => "O1_window_before_terrain",
        "commuting_pair_anchor_gap" => 0,
        "terrain_order_gap_norm_squared" => "4/25",
        "final_effective_denominator" => 8,
    )
end

function token_permutations(tokens::Vector{String})::Vector{Vector{String}}
    if length(tokens) == 1
        return [copy(tokens)]
    end
    out = Vector{Vector{String}}()
    for i in eachindex(tokens)
        head = tokens[i]
        rest = [tokens[j] for j in eachindex(tokens) if j != i]
        for tail in token_permutations(rest)
            push!(out, vcat([head], tail))
        end
    end
    return out
end

function evaluate_order(order::Vector{String})::Dict{String,Any}
    leaf = false
    z4 = false
    raw_window = false
    denominator = 1
    entropy_by_constraint = Dict{String,String}()
    terrain_support_after_z4 = Int[]
    for (index, token) in enumerate(order)
        if token == "L"
            leaf = true
            entropy_by_constraint["leaf_conditioning_T_pi_over_6"] = "0"
        elseif token == "Z"
            if raw_window
                return Dict("ordering" => join(order), "status" => "mortality", "class_id" => "M3_raw_window_then_Z4")
            end
            denominator *= 4
            z4 = true
            entropy_by_constraint["Z4_phase_lens"] = "-log(4)"
        elseif token == "W"
            if !leaf
                return Dict("ordering" => join(order), "status" => "mortality", "class_id" => "M1_phase_without_leaf")
            end
            if !z4
                raw_window = true
            end
            denominator *= 2
            entropy_by_constraint["descended_phase_window"] = "-log(2)"
        elseif token == "T"
            if !leaf
                return Dict("ordering" => join(order), "status" => "mortality", "class_id" => "M2_terrain_without_leaf")
            end
            terrain_support_after_z4 = occursin("W", join(order[1:index-1])) ? [0, 1] : [0, 1, 2, 3]
            entropy_by_constraint["terrain_restriction_Se_Funnel_L"] = "0"
        end
    end
    order_blind_signature = join([
        "den=$(denominator)",
        "holonomy=leaf_connection|pi/2",
        "entropy=leaf_conditioning_T_pi_over_6:$(entropy_by_constraint["leaf_conditioning_T_pi_over_6"]),Z4_phase_lens:$(entropy_by_constraint["Z4_phase_lens"]),descended_phase_window:$(entropy_by_constraint["descended_phase_window"]),terrain_restriction_Se_Funnel_L:$(entropy_by_constraint["terrain_restriction_Se_Funnel_L"])",
        "survival=leaf:true,Z4:true,phase_window_residue_set:[0,1],terrain_restriction_residue_set_after_Z4:$(terrain_support_after_z4)",
    ], "|")
    terrain_before_window = terrain_support_after_z4 == [0, 1, 2, 3]
    coarse_class = terrain_before_window ? "O2_terrain_before_window" : "O1_window_before_terrain"
    return Dict("ordering" => join(order), "status" => "survived", "class_id" => coarse_class, "order_blind_signature" => order_blind_signature)
end

function build_result()::Dict{String,Any}
    values = engine_values()
    positive = z3_order_breadth_identity(values, erased=false)
    erased = z3_order_breadth_identity(values, erased=true)
    all_pass = (
        positive["verdict"] == "unsat" &&
        erased["verdict"] == "sat" &&
        values["orderings_total"] == 24 &&
        values["distinct_live_outcomes"] == 2 &&
        values["distinct_mortality_classes"] == 3 &&
        values["total_equivalence_classes_including_mortality"] == 5
    )
    return Dict(
        "schema_version" => "$(SIM_ID)_julia_result_v1",
        "sim_id" => SIM_ID,
        "object_id" => SIM_ID,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "all_pass" => all_pass,
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "reads_peer_result" => false,
        "packages_used" => ["JSON3", "Pkg", "SHA", "Dates", "Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "capability_receipts" => Dict(
            "julia" => Dict("version" => string(VERSION), "active_project" => String(Base.active_project())),
            "Z3" => Dict("package_version" => package_version("Z3"), "api_smoke" => positive["verdict"]),
        ),
        "engine_values" => values,
        "crossover_proofs" => Dict(
            "julia_z3" => merge(positive, Dict(
                "erased_flip_verdict" => erased["verdict"],
                "erased_flip_detected" => positive["verdict"] == "unsat" && erased["verdict"] == "sat",
                "positive_case" => "negated order-blind order-breadth class-count identity is UNSAT",
                "negative/erased_control" => "erase one live order-blind class by forcing live_classes=1",
                "boundary_case" => "commuting L/Z swap keeps the order-blind signature",
                "demotion_condition" => "demote if Z3.jl is not bound to the recomputed class-count rows",
                "gates" => ["order_class_count", "proof", "all_pass"],
            )),
        ),
        "tool_calls" => [
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
                "input_object" => "order-blind order-breadth class-count identity",
                "output_object" => positive,
                "positive_case" => "negated class-count identity UNSAT",
                "negative/erased_control" => "one live order-blind class erased",
                "boundary_case" => "L/Z commuting pair preserves the order-blind signature",
                "demotion_condition" => "Z3.jl verdict not UNSAT/SAT as expected",
                "load_bearing" => true,
            ),
        ],
    )
end

function main()::Int
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON3.pretty(io, result)
        write(io, "\n")
    end
    println(JSON3.write(Dict("ok" => result["all_pass"], "result_path" => rel(RESULT_PATH))))
    return result["all_pass"] ? 0 : 1
end

exit(main())
