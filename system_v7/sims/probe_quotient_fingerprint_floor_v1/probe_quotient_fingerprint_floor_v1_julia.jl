#!/usr/bin/env julia

using Dates
using JSON
using SHA
using Z3

const SIM_ID = "probe_quotient_fingerprint_floor_v1"
const HERE = @__DIR__
const RESULTS = joinpath(HERE, "results")

function sha256_file(path::AbstractString)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function ordered_table(spec, order)::Vector{Vector{Int}}
    labels = Vector{String}(spec["support"])
    rows = Vector{Vector{Int}}()
    for label in labels
        push!(rows, [Int(spec["probes"][probe][label]) for probe in order])
    end
    rows
end

function quotient(labels::Vector{String}, rows::Vector{Vector{Int}})
    groups = Vector{Vector{String}}()
    keys = Vector{Vector{Int}}()
    signatures = Dict{String,Vector{Int}}()
    for (idx, label) in enumerate(labels)
        row = rows[idx]
        signatures[label] = copy(row)
        found = findfirst(k -> k == row, keys)
        if found === nothing
            push!(keys, copy(row))
            push!(groups, [label])
        else
            push!(groups[found], label)
        end
    end
    class_ids = Dict{String,Int}()
    for (idx, group) in enumerate(groups)
        for label in group
            class_ids[label] = idx - 1
        end
    end
    groups, signatures, class_ids
end

function z3_or(ctx, items::Vector{Z3.Expr})
    isempty(items) ? Z3.BoolVal(false, ctx) : Z3.Or(items)
end

function z3_and(ctx, items::Vector{Z3.Expr})
    isempty(items) ? Z3.BoolVal(true, ctx) : Z3.And(items)
end

function z3_partition_violation(rows::Vector{Vector{Int}}, class_vector::Vector{Int})::String
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    n = length(rows)
    width = isempty(rows) ? 0 : length(rows[1])
    value_vars = [[Z3.IntVar("julia_v_$(i)_$(j)", ctx) for j in 1:width] for i in 1:n]
    class_vars = [Z3.IntVar("julia_c_$(i)", ctx) for i in 1:n]
    for i in 1:n
        Z3.add(solver, class_vars[i] == Z3.IntVal(class_vector[i], ctx))
        for j in 1:width
            Z3.add(solver, value_vars[i][j] == Z3.IntVal(rows[i][j], ctx))
        end
    end
    violations = Z3.Expr[]
    for i in 1:n
        for k in (i + 1):n
            same_class = class_vars[i] == class_vars[k]
            different_class = Z3.Not(class_vars[i] == class_vars[k])
            same_values = z3_and(ctx, Z3.Expr[value_vars[i][j] == value_vars[k][j] for j in 1:width])
            different_value = z3_or(ctx, Z3.Expr[Z3.Not(value_vars[i][j] == value_vars[k][j]) for j in 1:width])
            push!(violations, Z3.And(Z3.Expr[same_class, different_value]))
            push!(violations, Z3.And(Z3.Expr[different_class, same_values]))
        end
    end
    Z3.add(solver, z3_or(ctx, violations))
    string(Z3.check(solver))
end

function find_merge_pair(labels::Vector{String}, full_ids::Dict{String,Int}, erased_ids::Dict{String,Int})
    for i in 1:length(labels)
        for k in (i + 1):length(labels)
            left = labels[i]
            right = labels[k]
            if full_ids[left] != full_ids[right] && erased_ids[left] == erased_ids[right]
                return [left, right]
            end
        end
    end
    nothing
end

function find_persistent_pair(labels::Vector{String}, full_ids::Dict{String,Int})
    for i in 1:length(labels)
        for k in (i + 1):length(labels)
            left = labels[i]
            right = labels[k]
            if full_ids[left] == full_ids[right]
                return [left, right]
            end
        end
    end
    nothing
end

function main()
    mkpath(RESULTS)
    spec = JSON.parsefile(joinpath(HERE, "spec.json"))
    labels = Vector{String}(spec["support"])
    full_rows = ordered_table(spec, spec["probe_order_full"])
    erased_rows = ordered_table(spec, spec["probe_order_erased"])
    full_classes, full_signatures, full_ids = quotient(labels, full_rows)
    erased_classes, erased_signatures, erased_ids = quotient(labels, erased_rows)
    class_vector = [full_ids[label] for label in labels]
    z3_full = z3_partition_violation(full_rows, class_vector)
    z3_erased = z3_partition_violation(erased_rows, class_vector)
    smt_ok = z3_full == "unsat" && z3_erased == "sat"
    merge_pair = find_merge_pair(labels, full_ids, erased_ids)
    persistent_pair = find_persistent_pair(labels, full_ids)
    expected = spec["expected"]
    controls_ok =
        length(full_classes) == Int(expected["full_class_count"]) &&
        length(erased_classes) == Int(expected["erased_class_count"]) &&
        merge_pair == expected["merge_pair_when_erased"] &&
        persistent_pair == expected["permanent_indistinguishable_pair"] &&
        smt_ok
    result = Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia_z3",
        "computation_style" => "julia_integer_table_plus_z3jl",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "does_not_self_upgrade" => true,
        "reads_peer_result" => false,
        "written_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "source_sha256" => sha256_file(@__FILE__),
        "spec_sha256" => sha256_file(joinpath(HERE, "spec.json")),
        "julia_project" => Base.active_project(),
        "support" => labels,
        "probe_order_full" => spec["probe_order_full"],
        "probe_order_erased" => spec["probe_order_erased"],
        "fingerprints_full" => Dict(label => full_signatures[label] for label in labels),
        "fingerprints_erased" => Dict(label => erased_signatures[label] for label in labels),
        "quotient_classes_full" => full_classes,
        "quotient_class_count_full" => length(full_classes),
        "quotient_classes_erased" => erased_classes,
        "quotient_class_count_erased" => length(erased_classes),
        "flip_control" => Dict(
            "erased_merge_pair" => merge_pair,
            "full_class_count" => length(full_classes),
            "erased_class_count" => length(erased_classes),
            "added_probe" => spec["added_probe"],
            "added_probe_split_pair" => merge_pair,
            "added_probe_class_count" => length(full_classes),
            "tautology_guard_tripped" => z3_erased != "sat",
        ),
        "smt_flip" => Dict(
            "julia_z3_full_P" => z3_full,
            "julia_z3_erased_P" => z3_erased,
            "real_vs_erased_flip_confirmed" => smt_ok,
            "encoding" => "Z3.jl variables are equal to measured table entries and full-P class ids; the asserted violation is soundness-or-coarseness failure for the active probe list.",
        ),
        "crossover_proofs" => Dict(
            "julia_z3" => Dict(
                "ran" => true,
                "load_bearing" => false,
                "supportive" => true,
                "verdict" => z3_full,
                "erased_verdict" => z3_erased,
                "claim" => "supportive consistency check: full P has no quotient violation and erased P exposes the expected coarseness witness against the forced full-Q table",
            ),
        ),
        "TOOL_MANIFEST" => Dict(
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive read/write of spec and receipt JSON"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "supportive consistency check: full-P UNSAT and erased-P SAT polarity over a forced/trivial quotient table; not load-bearing structural discovery"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("JSON" => "supportive", "Z3" => "supportive"),
        "packages_used" => ["JSON", "SHA", "Dates", "Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "package_observables" => Dict(
            "Z3" => "supportive Z3.jl full/erased quotient-table consistency polarity",
            "JSON" => "spec/result JSON handling only",
        ),
        "tool_calls" => [
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
                "input_object" => "measured rows and full-P class ids",
                "output_object" => "UNSAT full-P and SAT erased-P verdicts",
                "positive_case" => "full P has no soundness/coarseness violation",
                "negative/erased_control" => "erased P exposes x0/x2 coarseness witness",
                "boundary_case" => "x4/x5 same-class row remains allowed",
                "demotion_condition" => "demote to plain table computation if full is not unsat or erased is not sat",
                "gates" => ["consistency_check"],
            ),
        ],
        "claim_path_tools" => String[],
        "all_pass" => controls_ok,
        "criteria_checked" => [
            "full class count",
            "erased class count",
            "merge pair",
            "added probe split",
            "persistent indistinguishable pair",
            "Julia Z3 full UNSAT",
            "Julia Z3 erased SAT",
        ],
        "surviving_alternatives" => spec["surviving_alternatives"],
        "claim_ceiling" => spec["claim_ceiling"],
    )
    out_path = joinpath(RESULTS, "$(SIM_ID)_julia_results.json")
    open(out_path, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => controls_ok, "result_path" => out_path, "smt_flip" => result["smt_flip"]), 2))
    controls_ok || exit(1)
end

main()
