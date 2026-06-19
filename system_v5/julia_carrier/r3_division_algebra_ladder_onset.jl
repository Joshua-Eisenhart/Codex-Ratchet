#!/usr/bin/env julia
# object_id: r3_division_algebra_ladder_onset
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "r3_division_algebra_ladder_onset"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/r3_division_algebra_ladder_onset_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/r3_division_algebra_ladder_onset_results.json")
const TOL = 1.0e-12
const ONSET_TOL = 1.0e-9
const RUNG_NAMES = ["R", "C", "H", "O", "S"]
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const SIM_EXECUTION_KIND = "classical"
const ALLOWED_CLAIM = "Finite R/C/H/O/S carrier-candidate property-onset map over the verified R0-R2 foundation surface; scratch diagnostic only."
const CLAIM_CEILING = "Allowed only: bottom-up finite carrier-candidate algebra property onset map. No promotion, no formal admission, no downstream scientific claim."

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent Cayley-Dickson table construction and property residual computation"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing vector norms for finite carrier property residuals"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive JSON receipt and current JAX-result parity read"),
    "JAX reference" => Dict("tried" => true, "used" => true, "reason" => "load-bearing peer backend parity over the current same-token JAX output"),
    "pytorch" => Dict("tried" => false, "used" => false, "reason" => "not used: explicit user fence for this row says no torch"),
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

function run_token()
    get(ENV, "R3_DIVISION_RUN_TOKEN", "manual-token-not-set")
end

function basis_vector(dim::Int, idx::Int)
    v = zeros(Float64, dim)
    v[idx + 1] = 1.0
    v
end

function cd_conj(x::AbstractVector{Float64})
    signs = vcat([1.0], fill(-1.0, length(x) - 1))
    collect(x) .* signs
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

function table_checksum(table::Array{Float64,3})
    dim = size(table, 1)
    nonzero = 0
    abs_sum = 0.0
    checksum = 0.0
    for c in 1:dim, a in 1:dim, b in 1:dim
        value = table[c, a, b]
        if abs(value) > 0.0
            nonzero += 1
        end
        abs_sum += abs(value)
        checksum += value * (1_000_003.0 * c + 1_009.0 * a + b)
    end
    Dict{String,Any}(
        "nonzero_entry_count" => nonzero,
        "sum_abs_entries" => abs_sum,
        "weighted_checksum" => checksum,
    )
end

function commutator_scan(table::Array{Float64,3})
    dim = size(table, 1)
    max_value = 0.0
    witness = [0, 0]
    for a in 0:(dim - 1), b in 0:(dim - 1)
        residual = norm(table[:, a + 1, b + 1] - table[:, b + 1, a + 1])
        if residual > max_value
            max_value = residual
            witness = [a, b]
        end
    end
    Dict{String,Any}(
        "max_residual" => max_value,
        "witness_basis_indices" => witness,
        "witness_expression_ids" => ["e$(witness[1])*e$(witness[2])", "e$(witness[2])*e$(witness[1])"],
    )
end

function associator_vector(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64}, z::AbstractVector{Float64})
    multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))
end

function associator_scan(table::Array{Float64,3})
    dim = size(table, 1)
    max_value = 0.0
    witness = [0, 0, 0]
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1)
        residual = norm(associator_vector(table, basis_vector(dim, a), basis_vector(dim, b), basis_vector(dim, c)))
        if residual > max_value
            max_value = residual
            witness = [a, b, c]
        end
    end
    Dict{String,Any}(
        "max_residual" => max_value,
        "witness_basis_indices" => witness,
        "witness_expression_ids" => ["(e$(witness[1])*e$(witness[2]))*e$(witness[3])", "e$(witness[1])*(e$(witness[2])*e$(witness[3]))"],
    )
end

function pair_vector(dim::Int, i::Int, j::Int, si::Float64 = 1.0, sj::Float64 = 1.0)
    v = zeros(Float64, dim)
    v[i + 1] = si
    v[j + 1] = sj
    v
end

function deterministic_probe(dim::Int, sample_idx::Int, side::Int)
    Float64[
        (Float64(mod((sample_idx + 17) * (j + 3) * (side + 5) * 37 + (j + 1)^2 * 19 + sample_idx * 11 + side * 13, 101)) - 50.0) / 37.0
        for j in 1:dim
    ]
end

function alternativity_scan(table::Array{Float64,3})
    dim = size(table, 1)
    xs = [basis_vector(dim, idx) for idx in 0:(dim - 1)]
    ys = [basis_vector(dim, idx) for idx in 0:(dim - 1)]
    if dim <= 8
        for i in 0:(dim - 1), j in (i + 1):(dim - 1)
            push!(xs, pair_vector(dim, i, j, 1.0, 1.0))
            push!(xs, pair_vector(dim, i, j, 1.0, -1.0))
        end
        for idx in 1:4
            push!(xs, deterministic_probe(dim, idx, 7))
        end
    else
        push!(xs, pair_vector(dim, 1, 10, -1.0, -1.0))
        ys = [basis_vector(dim, 4)]
    end
    max_value = 0.0
    witness = Dict{String,Any}("kind" => "none", "residual" => 0.0)
    for (ix0, x) in enumerate(xs), (iy0, y) in enumerate(ys)
        ix = ix0 - 1
        iy = iy0 - 1
        xxy = norm(associator_vector(table, x, x, y))
        if xxy > max_value
            max_value = xxy
            witness = Dict("kind" => "(x*x)*y - x*(x*y)", "x_probe_index" => ix, "y_probe_index" => iy, "residual" => xxy)
        end
        xyy = norm(associator_vector(table, x, y, y))
        if xyy > max_value
            max_value = xyy
            witness = Dict("kind" => "(x*y)*y - x*(y*y)", "x_probe_index" => ix, "y_probe_index" => iy, "residual" => xyy)
        end
    end
    Dict{String,Any}("max_residual" => max_value, "witness" => witness, "probe_count" => length(xs) * length(ys))
end

squared_norm(x::AbstractVector{Float64}) = dot(x, x)

function zero_divisor_vectors(dim::Int)
    dim < 16 && return nothing
    (pair_vector(dim, 1, 10, -1.0, -1.0), pair_vector(dim, 4, 15, -1.0, 1.0))
end

function norm_division_scan(table::Array{Float64,3})
    dim = size(table, 1)
    probes = [basis_vector(dim, idx) for idx in 0:(dim - 1)]
    for idx in 1:6
        push!(probes, deterministic_probe(dim, idx, 1))
    end
    zero_pair = zero_divisor_vectors(dim)
    if zero_pair !== nothing
        push!(probes, zero_pair[1])
        push!(probes, zero_pair[2])
    end
    max_residual = 0.0
    witness = Dict{String,Any}("kind" => "none", "residual" => 0.0)
    for (ix0, x) in enumerate(probes), (iy0, y) in enumerate(probes)
        product = multiply(table, x, y)
        product_norm = squared_norm(product)
        norm_product = squared_norm(x) * squared_norm(y)
        residual = abs(product_norm - norm_product)
        if residual > max_residual
            max_residual = residual
            witness = Dict(
                "kind" => "squared_norm_multiplicativity",
                "left_probe_index" => ix0 - 1,
                "right_probe_index" => iy0 - 1,
                "product_squared_norm" => product_norm,
                "factor_squared_norm_product" => norm_product,
                "residual" => residual,
            )
        end
    end
    if zero_pair === nothing
        zero_report = Dict{String,Any}("checked" => false, "has_zero_divisor_witness" => false, "product_squared_norm" => nothing, "factor_squared_norm_product" => nothing)
    else
        left, right = zero_pair
        product = multiply(table, left, right)
        product_norm = squared_norm(product)
        factor_norm_product = squared_norm(left) * squared_norm(right)
        zero_report = Dict{String,Any}(
            "checked" => true,
            "has_zero_divisor_witness" => product_norm <= TOL && factor_norm_product > ONSET_TOL,
            "product_squared_norm" => product_norm,
            "factor_squared_norm_product" => factor_norm_product,
            "left_terms" => ["-e1", "-e10"],
            "right_terms" => ["-e4", "e15"],
        )
    end
    Dict{String,Any}(
        "max_residual" => max_residual,
        "witness" => witness,
        "zero_divisor" => zero_report,
        "norm_multiplicative" => max_residual <= TOL,
        "norm_division" => max_residual <= TOL && !Bool(zero_report["has_zero_divisor_witness"]),
    )
end

function analyze_rung(name::String, table::Array{Float64,3})
    comm = commutator_scan(table)
    assoc = associator_scan(table)
    alt = alternativity_scan(table)
    norm_division = norm_division_scan(table)
    Dict{String,Any}(
        "name" => name,
        "dim" => size(table, 1),
        "commutator_max" => comm["max_residual"],
        "associator_max" => assoc["max_residual"],
        "alternativity_residual" => alt["max_residual"],
        "norm_multiplicativity_residual" => norm_division["max_residual"],
        "has_zero_divisor_witness" => Bool(norm_division["zero_divisor"]["has_zero_divisor_witness"]),
        "commutator_check" => comm,
        "associator_check" => assoc,
        "alternativity_check" => alt,
        "norm_division_check" => norm_division,
        "table_checksum" => table_checksum(table),
        "properties" => Dict{String,Any}(
            "commutative" => comm["max_residual"] <= TOL,
            "associative" => assoc["max_residual"] <= TOL,
            "alternative" => alt["max_residual"] <= TOL,
            "norm_multiplicative" => norm_division["max_residual"] <= TOL,
            "norm_division" => Bool(norm_division["norm_division"]),
        ),
    )
end

function first_lost(rungs::Dict{String,Any}, key::String)
    for name in RUNG_NAMES
        !Bool(rungs[name]["properties"][key]) && return name
    end
    "not_lost"
end

function control_pairs(rungs::Dict{String,Any})
    [
        Dict("name" => "commutativity_onset", "left_quantity" => "C.commutator_max", "right_quantity" => "H.commutator_max", "left_value" => rungs["C"]["commutator_max"], "right_value" => rungs["H"]["commutator_max"], "negative_case" => "H", "negative_property_value" => rungs["H"]["properties"]["commutative"], "negative_case_fails" => !Bool(rungs["H"]["properties"]["commutative"])),
        Dict("name" => "associativity_onset", "left_quantity" => "H.associator_max", "right_quantity" => "O.associator_max", "left_value" => rungs["H"]["associator_max"], "right_value" => rungs["O"]["associator_max"], "negative_case" => "O", "negative_property_value" => rungs["O"]["properties"]["associative"], "negative_case_fails" => !Bool(rungs["O"]["properties"]["associative"])),
        Dict("name" => "norm_division_onset", "left_quantity" => "O.norm_multiplicativity_residual", "right_quantity" => "S.norm_multiplicativity_residual", "left_value" => rungs["O"]["norm_multiplicativity_residual"], "right_value" => rungs["S"]["norm_multiplicativity_residual"], "negative_case" => "S", "negative_property_value" => rungs["S"]["properties"]["norm_division"], "negative_case_fails" => !Bool(rungs["S"]["properties"]["norm_division"])),
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
    parity_within_run = get(peer, "run_token", nothing) == result["run_token"]
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
    onsets = Dict{String,Any}(
        "commutativity_lost_at" => first_lost(rungs, "commutative"),
        "associativity_lost_at" => first_lost(rungs, "associative"),
        "alternativity_lost_at" => first_lost(rungs, "alternative"),
        "norm_division_lost_at" => first_lost(rungs, "norm_division"),
    )
    controls = control_pairs(rungs)
    no_self_diff = no_self_diff_tautologies(controls)
    onset_map_ok = onsets["commutativity_lost_at"] == "H" && onsets["associativity_lost_at"] == "O" && onsets["alternativity_lost_at"] == "S" && onsets["norm_division_lost_at"] == "S"
    quaternion_associator_zero = rungs["H"]["associator_max"] <= TOL
    octonion_assoc_residual = rungs["O"]["associator_max"]
    octonion_assoc_anchor = abs(octonion_assoc_residual - 2.0) <= TOL
    negative_controls_fail = all(Bool(row["negative_case_fails"]) for row in controls)
    ladder_onset_genuine = onset_map_ok && negative_controls_fail && no_self_diff && octonion_assoc_anchor

    shared_scalars = Dict{String,Any}()
    for name in RUNG_NAMES
        rung = rungs[name]
        prefix = "$name."
        for key in ["dim", "commutator_max", "associator_max", "alternativity_residual", "norm_multiplicativity_residual"]
            shared_scalars[prefix * key] = Float64(rung[key])
        end
        checksum = rung["table_checksum"]
        shared_scalars[prefix * "nonzero_entry_count"] = Float64(checksum["nonzero_entry_count"])
        shared_scalars[prefix * "sum_abs_entries"] = Float64(checksum["sum_abs_entries"])
        shared_scalars[prefix * "weighted_checksum"] = Float64(checksum["weighted_checksum"])
    end
    shared_scalars["O.octonion_assoc_residual"] = Float64(octonion_assoc_residual)
    shared_scalars["S.zero_divisor_product_squared_norm"] = Float64(rungs["S"]["norm_division_check"]["zero_divisor"]["product_squared_norm"])
    shared_scalars["S.zero_divisor_factor_squared_norm_product"] = Float64(rungs["S"]["norm_division_check"]["zero_divisor"]["factor_squared_norm_product"])

    shared_booleans = Dict{String,Any}(
        "onset_map_ok" => onset_map_ok,
        "quaternion_associator_zero" => quaternion_associator_zero,
        "octonion_assoc_anchor" => octonion_assoc_anchor,
        "negative_controls_fail" => negative_controls_fail,
        "no_self_diff_tautologies" => no_self_diff,
        "ladder_onset_genuine" => ladder_onset_genuine,
        "classification_is_scratch_diagnostic" => CLASSIFICATION == "scratch_diagnostic",
        "promotion_false" => PROMOTION_ALLOWED == false,
        "formal_admission_false" => FORMAL_ADMISSION_ALLOWED == false,
        "jax_enable_x64" => true,
        "plain_numpy_imported" => false,
        "torch_imported" => false,
    )
    for name in RUNG_NAMES
        for (key, value) in rungs[name]["properties"]
            shared_booleans["$name.property.$key"] = Bool(value)
        end
        shared_booleans["$name.has_zero_divisor_witness"] = Bool(rungs[name]["has_zero_divisor_witness"])
    end

    shared_strings = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "allowed_claim" => ALLOWED_CLAIM,
        "commutativity_lost_at" => onsets["commutativity_lost_at"],
        "associativity_lost_at" => onsets["associativity_lost_at"],
        "alternativity_lost_at" => onsets["alternativity_lost_at"],
        "norm_division_lost_at" => onsets["norm_division_lost_at"],
    )

    result = Dict{String,Any}(
        "schema" => "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id" => OBJECT_ID,
        "sim_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "version" => "1.0",
        "tier" => "R3_foundation_carrier_candidate_onset",
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
        "blocked_consumers" => ["promotion", "formal_admission", "downstream scientific claims"],
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
        "onset_tol" => ONSET_TOL,
        "construction" => Dict("method" => "finite Cayley-Dickson doubling", "rung_names" => RUNG_NAMES, "rung_dims" => Dict(name => rungs[name]["dim"] for name in RUNG_NAMES)),
        "rungs" => rungs,
        "onset_map" => onsets,
        "control_comparison_pairs" => controls,
        "probe" => Dict("question" => "property onset in the R/C/H/O/S carrier-candidate ladder", "measured_properties" => ["commutativity", "associativity", "alternativity", "norm_multiplicativity", "norm_division"], "control_rule" => "every control compares two named computed quantities and includes a negative case that fails the property"),
        "positive" => Dict(
            "R_C_commutative" => Dict("pass" => Bool(rungs["R"]["properties"]["commutative"]) && Bool(rungs["C"]["properties"]["commutative"])),
            "H_associative" => Dict("pass" => quaternion_associator_zero, "quaternion_associator_max" => rungs["H"]["associator_max"]),
            "O_norm_division_before_S" => Dict("pass" => rungs["O"]["properties"]["norm_division"]),
            "classification_is_scratch_diagnostic" => Dict("pass" => CLASSIFICATION == "scratch_diagnostic"),
            "promotion_allowed_false" => Dict("pass" => PROMOTION_ALLOWED == false),
            "formal_admission_allowed_false" => Dict("pass" => FORMAL_ADMISSION_ALLOWED == false),
            "no_self_diff_tautologies" => Dict("pass" => no_self_diff),
        ),
        "negative" => Dict(
            "H_commutativity_negative_case" => Dict("pass" => !Bool(rungs["H"]["properties"]["commutative"]), "commutator_max" => rungs["H"]["commutator_max"], "control_can_fail" => true),
            "O_associativity_negative_case" => Dict("pass" => !Bool(rungs["O"]["properties"]["associative"]), "octonion_assoc_residual" => octonion_assoc_residual, "control_can_fail" => true),
            "S_norm_division_negative_case" => Dict("pass" => !Bool(rungs["S"]["properties"]["norm_division"]), "norm_multiplicativity_residual" => rungs["S"]["norm_multiplicativity_residual"], "zero_divisor" => rungs["S"]["norm_division_check"]["zero_divisor"], "control_can_fail" => true),
        ),
        "boundary" => Dict(
            "C_to_H_commutativity_boundary" => Dict("pass" => Bool(rungs["C"]["properties"]["commutative"]) && !Bool(rungs["H"]["properties"]["commutative"]), "left" => "C", "right" => "H"),
            "H_to_O_associativity_boundary" => Dict("pass" => Bool(rungs["H"]["properties"]["associative"]) && !Bool(rungs["O"]["properties"]["associative"]), "left" => "H", "right" => "O"),
            "O_to_S_norm_division_boundary" => Dict("pass" => Bool(rungs["O"]["properties"]["norm_division"]) && !Bool(rungs["S"]["properties"]["norm_division"]), "left" => "O", "right" => "S"),
            "claim_ceiling" => CLAIM_CEILING,
        ),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "shared_strings" => shared_strings,
    )
    peer = isfile(JAX_REFERENCE_PATH) ? JSON.parsefile(JAX_REFERENCE_PATH) : Dict{String,Any}()
    result["jax_reference"] = Dict(
        "path" => JAX_REFERENCE_PATH,
        "run_token" => get(peer, "run_token", nothing),
        "shared_value_digest" => get(peer, "shared_value_digest", nothing),
    )
    result["parity"] = parity_against_jax(result)
    result["positive"]["dual_backend_parity"] = Dict("pass" => result["parity"]["within_tolerance"])
    core_pass = onset_map_ok && quaternion_associator_zero && octonion_assoc_anchor && negative_controls_fail && ladder_onset_genuine && no_self_diff && CLASSIFICATION == "scratch_diagnostic" && PROMOTION_ALLOWED == false && FORMAL_ADMISSION_ALLOWED == false
    result["core_pass"] = core_pass
    result["all_pass"] = core_pass && Bool(result["parity"]["within_tolerance"])
    result["stop_condition_fired"] = !Bool(result["all_pass"])
    result["pass_rule"] = "onset map H/O/S as specified, quaternion associator zero, octonion associator 2.0, negative controls fail as expected, no self-diff controls, and within-run JAX parity"
    result["fail_rule"] = "any wrong onset, missing negative failure, self-diff control, fence violation, or parity mismatch"
    result["result_summary"] = Dict(
        "commutativity_lost_at" => onsets["commutativity_lost_at"],
        "associativity_lost_at" => onsets["associativity_lost_at"],
        "norm_division_lost_at" => onsets["norm_division_lost_at"],
        "octonion_assoc_residual" => octonion_assoc_residual,
        "quaternion_assoc_residual" => rungs["H"]["associator_max"],
        "ladder_onset_genuine" => ladder_onset_genuine,
        "no_self_diff" => no_self_diff,
        "parity_within_run" => result["parity"]["parity_within_run"],
        "all_pass" => result["all_pass"],
    )
    result["commutativity_lost_at"] = onsets["commutativity_lost_at"]
    result["associativity_lost_at"] = onsets["associativity_lost_at"]
    result["norm_division_lost_at"] = onsets["norm_division_lost_at"]
    result["octonion_assoc_residual"] = octonion_assoc_residual
    result["ladder_onset_genuine"] = ladder_onset_genuine
    result["no_self_diff"] = no_self_diff
    result["parity_within_run"] = result["parity"]["parity_within_run"]
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
        "commutativity_lost_at" => result["commutativity_lost_at"],
        "associativity_lost_at" => result["associativity_lost_at"],
        "norm_division_lost_at" => result["norm_division_lost_at"],
        "octonion_assoc_residual" => result["octonion_assoc_residual"],
        "no_self_diff" => result["no_self_diff"],
    )))
    return result["core_pass"] ? 0 : 1
end

exit(main())
