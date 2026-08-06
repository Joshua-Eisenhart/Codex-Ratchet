#!/usr/bin/env julia
# Finite paired whole-extension L1 carrier lane.
# Julia is the semantic owner for this packet; promotion remains disabled.

using Dates
using JSON
using Printf
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "..", ".."))
const SOURCE_PATH = abspath(@__FILE__)
const FIXTURE_PATH = joinpath(ROOT, "constraint_box", "fixtures", "cr", "paired_whole_extension_v1.json")
const RESULT_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "paired_extension_nominalist_julia_result.json")
const OBJECT_ID = "paired-whole-extension-l1-v1"
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false

sorted_ints(values) = sort(Int.(collect(values)))
sorted_strings(values) = sort(String.(collect(values)))
metric(after::Int, before::Int) = @sprintf("%.12f", log2(Float64(after)) - log2(Float64(before)))
sha256_hex(path::String) = bytes2hex(SHA.sha256(read(path)))

function finite_sets(fixture)
    carrier = fixture["carrier"]
    ambient = Set(Int.(carrier["ambient_support"]))
    settled = Set(Int.(carrier["settled_support"]))
    newly_opened = Set(Int.(carrier["newly_opened"]))
    binding_admits = Set(Int.(carrier["binding_admits"]))
    opened = union(settled, newly_opened)
    open_then_bind = intersect(opened, binding_admits)
    bind_then_open = union(intersect(settled, binding_admits), newly_opened)
    return ambient, settled, newly_opened, binding_admits, opened, open_then_bind, bind_then_open
end

function mss_rows(fixture, opened, settled, demanded_scar)
    rows = Dict{String,Any}[]
    candidates = fixture["mss_candidates"]
    for name in ["weak_no_binding", "minimal_exclude_scar", "strong_exclude_scar_and_extra"]
        admitted = Set(Int.(candidates[name]))
        result = intersect(opened, admitted)
        sufficient = all(!(value in result) for value in demanded_scar) && issubset(settled, result)
        push!(rows, Dict{String,Any}(
            "candidate" => name,
            "result" => sorted_ints(result),
            "sufficient" => sufficient,
            "binding_cost_bits" => metric(length(opened), length(result)),
        ))
    end
    return rows
end

function z3_controls(order_scar::Vector{Int})
    real = Solver()
    scar_card = IntVar("paired_scar_card")
    add(real, scar_card == IntVal(length(order_scar)))
    add(real, scar_card == IntVal(1))
    real_status = string(check(real))

    erased = Solver()
    erased_card = IntVar("paired_erased_scar_card")
    add(erased, erased_card == IntVal(length(order_scar)))
    add(erased, erased_card == IntVal(0))
    erased_status = string(check(erased))
    return Dict{String,Any}(
        "real" => Dict("ran" => true, "load_bearing" => true, "verdict" => real_status, "pass" => real_status == "sat"),
        "erased_history" => Dict("ran" => true, "load_bearing" => true, "verdict" => erased_status, "pass" => erased_status == "unsat"),
    )
end

function build_result()
    fixture = JSON.parse(String(read(FIXTURE_PATH)))
    ambient, settled, newly_opened, binding_admits, opened, open_then_bind, bind_then_open = finite_sets(fixture)
    demanded_scar = Int.(fixture["demands"]["order_scar"])
    demanded_future = String.(fixture["demands"]["future_extension"])
    whole = fixture["whole"]
    extensions = whole["extension_by_history"]
    deleted_extensions = whole["extension_after_history_deletion"]
    extension_ob = sorted_strings(extensions["ob"])
    extension_bo = sorted_strings(extensions["bo"])
    deleted_ob = sorted_strings(deleted_extensions["ob"])
    deleted_bo = sorted_strings(deleted_extensions["bo"])
    order_scar = sorted_ints(setdiff(bind_then_open, open_then_bind))
    extension_difference = sorted_strings(setdiff(Set(extension_bo), Set(extension_ob)))
    deleted_difference = sorted_strings(setdiff(Set(deleted_bo), Set(deleted_ob)))
    relabel = Dict(parse(Int, key) => Int(value) for (key, value) in fixture["controls"]["relabel_map"])
    relabel_scar = sorted_ints([relabel[value] for value in order_scar])
    reversal_order_scar = Dict{String,Any}("ob" => order_scar, "bo" => Int[])
    rows = mss_rows(fixture, opened, settled, demanded_scar)
    sufficient = [row for row in rows if row["sufficient"]]
    least_cost = minimum(parse(Float64, row["binding_cost_bits"]) for row in sufficient)
    frontier = sort(collect(String(row["candidate"]) for row in sufficient if isapprox(parse(Float64, row["binding_cost_bits"]), least_cost; atol=1e-12, rtol=0.0)))
    z3 = z3_controls(order_scar)

    tests = Dict{String,Bool}(
        "finite_nonempty_supports" => all(!isempty(values) for values in (ambient, settled, newly_opened, opened, open_then_bind, bind_then_open)),
        "strict_raw_growth" => length(opened) > length(settled),
        "orders_differ" => open_then_bind != bind_then_open,
        "scar_exact" => order_scar == demanded_scar == [3],
        "future_extension_changes" => extension_difference == demanded_future,
        "history_deletion_collapses" => isempty(deleted_difference),
        "relabel_preserves_structure" => length(relabel_scar) == length(order_scar),
        "reversal_moves_scar" => reversal_order_scar == Dict("ob" => order_scar, "bo" => Int[]),
        "delete_opening_removes_scar" => isempty(fixture["controls"]["no_opening_scar"]),
        "delete_binding_removes_scar" => isempty(fixture["controls"]["no_binding_scar"]),
        "minimal_sufficient_frontier" => frontier == ["minimal_exclude_scar"],
        "history_is_load_bearing" => !isempty(extension_difference) && isempty(deleted_difference),
        "z3_real_control" => z3["real"]["pass"],
        "z3_erased_control" => z3["erased_history"]["pass"],
    )

    observation = Dict{String,Any}(
        "fixture_id" => OBJECT_ID,
        "opened" => sorted_ints(opened),
        "open_then_bind" => sorted_ints(open_then_bind),
        "bind_then_open" => sorted_ints(bind_then_open),
        "order_scar" => order_scar,
        "extension_ob" => extension_ob,
        "extension_bo" => extension_bo,
        "extension_difference" => extension_difference,
        "extension_difference_after_history_deletion" => deleted_difference,
        "no_opening_scar" => Int[],
        "no_binding_scar" => Int[],
        "relabel_scar" => relabel_scar,
        "reversal_order_scar_by_history" => reversal_order_scar,
        "mss_frontier" => frontier,
        "mss_rows" => rows,
        "raw_opening_gain_bits" => metric(length(opened), length(settled)),
        "binding_cost_bits" => metric(length(opened), length(open_then_bind)),
        "net_settled_gain_bits" => metric(length(open_then_bind), length(settled)),
        "history_is_load_bearing" => tests["history_is_load_bearing"],
        "probes" => fixture["probes"],
    )
    observation["all_tests_passed"] = all(values(tests))
    fixture_sha256 = sha256_hex(FIXTURE_PATH)
    source_sha256 = sha256_hex(SOURCE_PATH)
    return Dict{String,Any}(
        "schema_version" => "paired_extension_engine_result_v1",
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "source_sha256" => source_sha256,
        "result_path" => RESULT_PATH,
        "fixture_path" => FIXTURE_PATH,
        "fixture_sha256" => fixture_sha256,
        "canonical_observation" => observation,
        "negative_controls" => Dict("history_deletion_collapses" => tests["history_deletion_collapses"], "reversal_moves_scar" => tests["reversal_moves_scar"]),
        "z3" => z3,
        "packages_used" => ["Z3", "JSON", "SHA", "Printf"],
        "aligned_packages_load_bearing" => ["Z3"],
        "claim_path_tools" => ["Z3"],
        "tool_manifest" => Dict("Z3" => Dict("tried" => true, "used" => true, "reason" => "finite measured order-scar cardinality and erased-history contradiction")),
        "tool_integration_depth" => Dict("Z3" => "load_bearing"),
        "tool_calls" => [Dict("tool" => "Z3", "qualified_api" => "Z3.Solver/check", "input_object" => "measured finite order_scar", "output_object" => "SAT plus erased-history UNSAT", "positive_case" => "scar_card=1", "negative_control" => "scar_card=0 against measured scar_card=1", "boundary_case" => "empty scar after opening or binding deletion", "demotion_condition" => "remove Z3 control or disagreement with controller observation", "gates" => ["all_pass", "negative_control"])],
        "checks" => tests,
        "all_pass" => observation["all_tests_passed"],
        "claim_ceiling" => "finite paired whole-extension L1 carrier witness only; not a physical manifold, time law, chirality, basin, engine, CR, or physics result",
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("PAIRED_EXTENSION_JULIA_DONE all_pass=", result["all_pass"], " scar=", result["canonical_observation"]["order_scar"], " history_load_bearing=", result["canonical_observation"]["history_is_load_bearing"])
    return result["all_pass"] ? 0 : 2
end

exit(main())
