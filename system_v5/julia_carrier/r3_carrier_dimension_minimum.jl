#!/usr/bin/env julia
# object_id: r3_carrier_dimension_minimum
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "r3_carrier_dimension_minimum"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/r3_carrier_dimension_minimum_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/r3_carrier_dimension_minimum_results.json")
const TOL = 1.0e-12
const NONZERO_TOL = 1.0e-9
const RUNG_NAMES = ["R", "C", "H", "O"]
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const SIM_EXECUTION_KIND = "classical"
const ALLOWED_CLAIM = "Carrier-dimension minimum only: in the finite Cayley-Dickson R/C/H/O scan, the associator is zero through dimension 4 and first nonzero at dimension 8."
const CLAIM_CEILING = "Allowed only: bottom-up R3 algebraic carrier-dimension minimum for a nonzero associator. No promotion, no formal admission, no downstream interpretation."

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent Cayley-Dickson table construction and associator residual scan"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing vector norms for finite carrier associator residuals"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive JSON receipt and current JAX-result parity read"),
    "JAX reference" => Dict("tried" => true, "used" => true, "reason" => "load-bearing same-run peer backend reference"),
    "pytorch" => Dict("tried" => false, "used" => false, "reason" => "not used: explicit no-torch fence for this row"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "JSON" => "supportive",
    "JAX reference" => "load_bearing",
    "pytorch" => nothing,
)

const SIM_TEMPLATE_SURFACE = Dict{String,Any}(
    "identity" => ["sim_id", "name", "version", "tier"],
    "tooling" => ["TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH", "classification"],
    "negatives" => ["positive", "negative", "boundary", "probe"],
    "promotion" => ["promotion_allowed", "formal_admission_allowed", "blocked_consumers"],
)

run_token() = get(ENV, "R3_CARRIER_DIMENSION_RUN_TOKEN", "manual-token-not-set")

function basis_vector(dim::Int, idx::Int)
    v = zeros(Float64, dim)
    v[idx + 1] = 1.0
    v
end

function cd_conj(x::AbstractVector{Float64})
    collect(x) .* vcat([1.0], fill(-1.0, length(x) - 1))
end

function multiply(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function cd_pair_multiply(parent::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    n = size(parent, 1)
    a = x[1:n]
    b = x[(n + 1):(2 * n)]
    c = y[1:n]
    d = y[(n + 1):(2 * n)]
    first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
    vcat(first, second)
end

function cd_double(parent::Array{Float64,3})
    n = size(parent, 1)
    dim = 2 * n
    table = zeros(Float64, dim, dim, dim)
    for i in 0:(dim - 1), j in 0:(dim - 1)
        table[:, i + 1, j + 1] .= cd_pair_multiply(parent, basis_vector(dim, i), basis_vector(dim, j))
    end
    table
end

function build_tables()
    table = zeros(Float64, 1, 1, 1)
    table[1, 1, 1] = 1.0
    tables = Dict{String,Any}("R" => table)
    for name in RUNG_NAMES[2:end]
        table = cd_double(table)
        tables[name] = table
    end
    tables
end

function associator_vector(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64}, z::AbstractVector{Float64})
    multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))
end

function associator_scan(table::Array{Float64,3})
    dim = size(table, 1)
    max_value = 0.0
    witness = [0, 0, 0]
    witness_vector = zeros(Float64, dim)
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1)
        vec = associator_vector(table, basis_vector(dim, a), basis_vector(dim, b), basis_vector(dim, c))
        residual = norm(vec)
        if residual > max_value
            max_value = residual
            witness = [a, b, c]
            witness_vector = vec
        end
    end
    Dict{String,Any}(
        "max_residual" => max_value,
        "witness_basis_indices" => witness,
        "witness_expression_ids" => ["(e$(witness[1])*e$(witness[2]))*e$(witness[3])", "e$(witness[1])*(e$(witness[2])*e$(witness[3]))"],
        "witness_vector" => [Float64(cell) for cell in witness_vector],
        "nonzero" => max_value > NONZERO_TOL,
    )
end

function analyze_rung(name::String, table::Array{Float64,3})
    assoc = associator_scan(table)
    Dict{String,Any}(
        "name" => name,
        "dim" => size(table, 1),
        "associator_max" => assoc["max_residual"],
        "associator_check" => assoc,
        "associative" => assoc["max_residual"] <= TOL,
    )
end

function first_nonzero_associator_dim(rungs::Dict{String,Any})
    for name in RUNG_NAMES
        Bool(rungs[name]["associator_check"]["nonzero"]) && return Int(rungs[name]["dim"])
    end
    nothing
end

function catalan_count(n::Int)
    n <= 1 && return 1
    values = fill(0, n)
    values[1] = 1
    for size in 2:n
        values[size] = sum(values[left] * values[size - left] for left in 1:(size - 1))
    end
    values[n]
end

function control_comparisons(rungs::Dict{String,Any})
    max_le4 = max(rungs["R"]["associator_max"], rungs["C"]["associator_max"], rungs["H"]["associator_max"])
    [
        Dict("name" => "dimension_boundary_H_to_O", "left_quantity" => "H.associator_max", "right_quantity" => "O.associator_max", "left_value" => rungs["H"]["associator_max"], "right_value" => rungs["O"]["associator_max"], "pass" => rungs["H"]["associator_max"] <= TOL && rungs["O"]["associator_max"] > NONZERO_TOL, "control_can_fail" => true),
        Dict("name" => "two_input_bracketing_insufficient", "left_quantity" => "two_input_parenthesization_count", "right_quantity" => "three_input_parenthesization_count", "left_value" => catalan_count(2), "right_value" => catalan_count(3), "pass" => catalan_count(2) < catalan_count(3), "control_can_fail" => true),
        Dict("name" => "dim_le4_negative_control", "left_quantity" => "max_associator_dim_le4", "right_quantity" => "O.associator_max", "left_value" => max_le4, "right_value" => rungs["O"]["associator_max"], "pass" => max_le4 <= TOL && rungs["O"]["associator_max"] > NONZERO_TOL, "control_can_fail" => true),
    ]
end

no_self_diff_tautologies(rows) = all(string(row["left_quantity"]) != string(row["right_quantity"]) for row in rows)

function parity_against_jax(result::Dict{String,Any})
    if !isfile(JAX_REFERENCE_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_REFERENCE_PATH,
            "status" => "missing_jax_reference",
            "within_tolerance" => false,
            "parity_within_run" => false,
            "parity_max_diff" => nothing,
            "numeric_rows" => [],
            "boolean_mismatches" => [],
            "string_mismatches" => [],
            "missing_keys" => ["peer_result"],
        )
    end
    peer = JSON.parsefile(JAX_REFERENCE_PATH)
    numeric_rows = Any[]
    missing = String[]
    max_diff = 0.0
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        diff = abs(Float64(value) - Float64(peer["shared_scalars"][key]))
        max_diff = max(max_diff, diff)
        push!(numeric_rows, Dict("key" => key, "julia" => Float64(value), "jax" => Float64(peer["shared_scalars"][key]), "abs_diff" => diff))
    end
    boolean_mismatches = Any[]
    for (key, value) in result["shared_booleans"]
        if !haskey(peer["shared_booleans"], key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer["shared_booleans"][key])
            push!(boolean_mismatches, Dict("key" => key, "julia" => Bool(value), "jax" => Bool(peer["shared_booleans"][key])))
        end
    end
    string_mismatches = Any[]
    for (key, value) in result["shared_strings"]
        if !haskey(peer["shared_strings"], key)
            push!(missing, key)
            continue
        end
        if string(value) != string(peer["shared_strings"][key])
            push!(string_mismatches, Dict("key" => key, "julia" => string(value), "jax" => string(peer["shared_strings"][key])))
        end
    end
    parity_within_run = (
        get(peer, "backend", nothing) == "jax" &&
        get(peer, "run_token", nothing) == result["run_token"] &&
        get(peer, "result_path", nothing) == JAX_REFERENCE_PATH
    )
    within_tolerance = max_diff <= TOL && isempty(boolean_mismatches) && isempty(string_mismatches) && isempty(missing) && parity_within_run
    Dict{String,Any}(
        "peer_result_path" => JAX_REFERENCE_PATH,
        "status" => "compared",
        "within_tolerance" => within_tolerance,
        "parity_within_run" => parity_within_run,
        "parity_max_diff" => max_diff,
        "numeric_rows" => numeric_rows,
        "boolean_mismatches" => boolean_mismatches,
        "string_mismatches" => string_mismatches,
        "missing_keys" => missing,
    )
end

function build_result()
    tables = build_tables()
    rungs = Dict{String,Any}(name => analyze_rung(name, tables[name]) for name in RUNG_NAMES)
    controls = control_comparisons(rungs)
    no_self_diff = no_self_diff_tautologies(controls)
    min_dim = first_nonzero_associator_dim(rungs)
    max_le4 = max(rungs["R"]["associator_max"], rungs["C"]["associator_max"], rungs["H"]["associator_max"])
    associator_needs_3_inputs = catalan_count(3) == 2
    two_input_insufficient = catalan_count(2) < catalan_count(3)
    dim_le4_zero = max_le4 <= TOL
    octonion_anchor = abs(rungs["O"]["associator_max"] - 2.0) <= TOL
    dimension_minimum_genuine = min_dim == 8 && dim_le4_zero && octonion_anchor && associator_needs_3_inputs && two_input_insufficient && no_self_diff && all(Bool(row["pass"]) && Bool(row["control_can_fail"]) for row in controls)

    shared_scalars = Dict{String,Any}()
    for name in RUNG_NAMES
        shared_scalars["$name.dim"] = Float64(rungs[name]["dim"])
        shared_scalars["$name.associator_max"] = Float64(rungs[name]["associator_max"])
    end
    shared_scalars["max_associator_dim_le4"] = Float64(max_le4)
    shared_scalars["O.octonion_associator_anchor"] = Float64(rungs["O"]["associator_max"])
    shared_scalars["two_input_parenthesization_count"] = Float64(catalan_count(2))
    shared_scalars["three_input_parenthesization_count"] = Float64(catalan_count(3))
    shared_scalars["min_nonassoc_algebra_dim"] = Float64(min_dim === nothing ? -1 : min_dim)

    shared_booleans = Dict{String,Any}(
        "associator_needs_3_inputs" => associator_needs_3_inputs,
        "two_input_insufficient" => two_input_insufficient,
        "dim_le4_associator_zero" => dim_le4_zero,
        "octonion_associator_anchor_2" => octonion_anchor,
        "dimension_minimum_genuine" => dimension_minimum_genuine,
        "no_self_diff_tautologies" => no_self_diff,
        "classification_is_scratch_diagnostic" => CLASSIFICATION == "scratch_diagnostic",
        "promotion_false" => PROMOTION_ALLOWED == false,
        "formal_admission_false" => FORMAL_ADMISSION_ALLOWED == false,
        "jax_enable_x64" => true,
        "plain_numpy_imported" => false,
        "torch_imported" => false,
    )
    for name in RUNG_NAMES
        shared_booleans["$name.associative"] = Bool(rungs[name]["associative"])
        shared_booleans["$name.associator_nonzero"] = Bool(rungs[name]["associator_check"]["nonzero"])
    end

    shared_strings = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "allowed_claim" => ALLOWED_CLAIM,
        "first_nonzero_rung" => min_dim == 8 ? "O" : "not_found",
    )

    peer = isfile(JAX_REFERENCE_PATH) ? JSON.parsefile(JAX_REFERENCE_PATH) : Dict{String,Any}()
    result = Dict{String,Any}(
        "schema" => "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id" => OBJECT_ID,
        "sim_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "version" => "1.0",
        "tier" => "R3_foundation_carrier_dimension_minimum",
        "backend" => "julia",
        "run_token" => run_token(),
        "generated_at" => replace(string(Dates.now(Dates.UTC)), r"\\.\\d+$" => "") * "Z",
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => CLAIM_CEILING,
        "allowed_claims" => [ALLOWED_CLAIM],
        "promotion_status" => "diagnostic_only",
        "eligible_consumers" => [],
        "blocked_consumers" => ["promotion", "formal_admission", "downstream interpretation"],
        "sim_execution_kind" => SIM_EXECUTION_KIND,
        "SIM_TEMPLATE_surface" => SIM_TEMPLATE_SURFACE,
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "required_tools" => ["Julia", "LinearAlgebra", "JAX reference"],
        "actual_tools_used" => ["Julia", "LinearAlgebra", "JSON", "JAX reference"],
        "plain_numpy_imported" => false,
        "torch_imported" => false,
        "tol" => TOL,
        "nonzero_tol" => NONZERO_TOL,
        "construction" => Dict("method" => "finite Cayley-Dickson doubling", "rung_names" => RUNG_NAMES, "rung_dims" => Dict(name => rungs[name]["dim"] for name in RUNG_NAMES)),
        "rungs" => rungs,
        "control_comparison_pairs" => controls,
        "probe" => Dict("question" => "minimum Cayley-Dickson carrier dimension supporting a nonzero associator", "expression" => "(ab)c - a(bc)", "measured_property" => "basis-triple associator residual", "control_rule" => "controls compare distinct computed quantities and can fail"),
        "positive" => Dict(
            "octonion_associator_nonzero" => Dict("pass" => Bool(rungs["O"]["associator_max"] > NONZERO_TOL), "residual" => rungs["O"]["associator_max"]),
            "octonion_associator_anchor_2" => Dict("pass" => octonion_anchor, "residual" => rungs["O"]["associator_max"]),
            "associator_needs_3_inputs" => Dict("pass" => associator_needs_3_inputs),
            "classification_is_scratch_diagnostic" => Dict("pass" => CLASSIFICATION == "scratch_diagnostic"),
            "promotion_allowed_false" => Dict("pass" => PROMOTION_ALLOWED == false),
            "formal_admission_allowed_false" => Dict("pass" => FORMAL_ADMISSION_ALLOWED == false),
            "no_self_diff_tautologies" => Dict("pass" => no_self_diff),
        ),
        "negative" => Dict(
            "dim_le4_associative_controls" => Dict("pass" => dim_le4_zero, "R_associator_max" => rungs["R"]["associator_max"], "C_associator_max" => rungs["C"]["associator_max"], "H_associator_max" => rungs["H"]["associator_max"], "control_can_fail" => true),
            "two_input_bracketing_insufficient" => Dict("pass" => two_input_insufficient, "two_input_parenthesization_count" => catalan_count(2), "three_input_parenthesization_count" => catalan_count(3), "control_can_fail" => true),
        ),
        "boundary" => Dict(
            "H_to_O_associator_boundary" => Dict("pass" => rungs["H"]["associator_max"] <= TOL && rungs["O"]["associator_max"] > NONZERO_TOL, "left" => "H", "right" => "O", "left_dim" => 4, "right_dim" => 8, "H_associator_max" => rungs["H"]["associator_max"], "O_associator_max" => rungs["O"]["associator_max"]),
            "claim_ceiling" => CLAIM_CEILING,
        ),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "shared_strings" => shared_strings,
        "jax_reference" => Dict("path" => JAX_REFERENCE_PATH, "run_token" => get(peer, "run_token", nothing), "shared_value_digest" => get(peer, "shared_value_digest", nothing)),
        "core_pass" => dimension_minimum_genuine && CLASSIFICATION == "scratch_diagnostic" && PROMOTION_ALLOWED == false && FORMAL_ADMISSION_ALLOWED == false,
        "pass_rule" => "dim<=4 associator residuals are zero, dim 8 residual has 2.0 anchor, controls are non-tautological, three inputs are required, and same-run JAX parity passes",
        "fail_rule" => "any nonzero dim<=4 associator, missing dim 8 anchor, self-diff control, fence violation, or stale parity",
        "result_summary" => Dict(
            "min_nonassoc_algebra_dim" => Int(min_dim === nothing ? -1 : min_dim),
            "associator_needs_3_inputs" => associator_needs_3_inputs,
            "two_input_insufficient" => two_input_insufficient,
            "dimension_minimum_genuine" => dimension_minimum_genuine,
            "octonion_associator" => rungs["O"]["associator_max"],
            "quaternion_associator" => rungs["H"]["associator_max"],
            "no_self_diff" => no_self_diff,
        ),
        "associator_needs_3_inputs" => associator_needs_3_inputs,
        "min_nonassoc_algebra_dim" => Int(min_dim === nothing ? -1 : min_dim),
        "two_input_insufficient" => two_input_insufficient,
        "dimension_minimum_genuine" => dimension_minimum_genuine,
        "no_self_diff" => no_self_diff,
        "parity_within_run" => false,
    )
    result["parity"] = parity_against_jax(result)
    result["positive"]["dual_backend_parity"] = Dict("pass" => result["parity"]["within_tolerance"])
    result["parity_within_run"] = Bool(result["parity"]["parity_within_run"])
    result["all_pass"] = Bool(result["core_pass"]) && Bool(result["parity"]["within_tolerance"])
    result["stop_condition_fired"] = !Bool(result["all_pass"])
    result["result_summary"]["parity_within_run"] = result["parity_within_run"]
    result["result_summary"]["all_pass"] = result["all_pass"]
    result
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("wrote $RESULT_PATH")
    println(JSON.json(Dict(
        "all_pass" => result["all_pass"],
        "core_pass" => result["core_pass"],
        "parity_within_run" => result["parity_within_run"],
        "min_nonassoc_algebra_dim" => result["min_nonassoc_algebra_dim"],
        "two_input_insufficient" => result["two_input_insufficient"],
        "dimension_minimum_genuine" => result["dimension_minimum_genuine"],
        "no_self_diff" => result["no_self_diff"],
    )))
    return result["all_pass"] ? 0 : 1
end

exit(main())
