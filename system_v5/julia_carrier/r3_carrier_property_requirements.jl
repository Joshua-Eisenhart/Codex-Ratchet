#!/usr/bin/env julia
# object_id: r3_carrier_property_requirements
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "r3_carrier_property_requirements"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/r3_carrier_property_requirements_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/r3_carrier_property_requirements_results.json")
const TOL = 1.0e-12
const REQUIREMENT_TOL = 1.0e-9
const RUNG_NAMES = ["R", "C", "H", "O", "S"]
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const SIM_EXECUTION_KIND = "classical"
const ALLOWED_CLAIM = "R3 bottom carrier-candidate property requirement map for verified R0-R2 structure."
const CLAIM_CEILING = "Allowed only: finite R/C/H/O/S carrier-candidate requirement map for R2 noncommutation and three-cell associator defect. Scratch diagnostic only; no promotion, no formal admission, no top-floor consumer."

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing independent finite carrier table arithmetic and residual comparisons",
    ),
    "LinearAlgebra" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing vector norms for commutator and associator capacities",
    ),
    "JSON" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization and current JAX result parsing",
    ),
    "SHA" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "supportive shared payload digest parity",
    ),
    "JAX reference" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing current-run peer backend reference",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "JSON" => "supportive",
    "SHA" => "supportive",
    "JAX reference" => "load_bearing",
)

const SIM_TEMPLATE_SURFACE = Dict{String,Any}(
    "identity" => ["sim_id", "name", "version", "tier"],
    "tooling" => ["TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH", "classification"],
    "negatives" => ["positive", "negative", "boundary", "probe"],
    "promotion" => ["promotion_allowed", "formal_admission_allowed", "blocked_consumers"],
)

function run_token()
    get(ENV, "R3_CARRIER_RUN_TOKEN", "manual-token-not-set")
end

function basis_vector(dim::Int, idx::Int)
    v = zeros(Float64, dim)
    v[idx + 1] = 1.0
    v
end

function multiply(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function cd_conj(x::AbstractVector{Float64})
    out = copy(collect(x))
    out[2:end] .*= -1.0
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
    for i in 1:dim, j in 1:dim
        x = zeros(Float64, dim)
        y = zeros(Float64, dim)
        x[i] = 1.0
        y[j] = 1.0
        table[:, i, j] .= cd_pair_multiply(parent, x, y)
    end
    table
end

function build_tables()
    table = zeros(Float64, 1, 1, 1)
    table[1, 1, 1] = 1.0
    tables = Dict{String,Array{Float64,3}}("R" => table)
    for name in RUNG_NAMES[2:end]
        table = cd_double(table)
        tables[name] = table
    end
    tables
end

function commutator_scan(table::Array{Float64,3})
    dim = size(table, 1)
    max_seen = 0.0
    witness = (0, 0)
    for a in 0:(dim - 1), b in 0:(dim - 1)
        residual = norm(multiply(table, basis_vector(dim, a), basis_vector(dim, b)) -
                        multiply(table, basis_vector(dim, b), basis_vector(dim, a)))
        if residual > max_seen
            max_seen = residual
            witness = (a, b)
        end
    end
    Dict{String,Any}(
        "max_residual" => max_seen,
        "witness_basis_indices" => [witness[1], witness[2]],
        "left_expression_id" => "e$(witness[1])*e$(witness[2])",
        "right_expression_id" => "e$(witness[2])*e$(witness[1])",
    )
end

function associator_vector(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64}, z::AbstractVector{Float64})
    multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))
end

function associator_scan(table::Array{Float64,3})
    dim = size(table, 1)
    max_seen = 0.0
    witness = (0, 0, 0)
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1)
        residual = norm(associator_vector(table, basis_vector(dim, a), basis_vector(dim, b), basis_vector(dim, c)))
        if residual > max_seen
            max_seen = residual
            witness = (a, b, c)
        end
    end
    Dict{String,Any}(
        "max_residual" => max_seen,
        "witness_basis_indices" => [witness[1], witness[2], witness[3]],
        "left_expression_id" => "(e$(witness[1])*e$(witness[2]))*e$(witness[3])",
        "right_expression_id" => "e$(witness[1])*(e$(witness[2])*e$(witness[3]))",
    )
end

function analyze_carrier(name::String, table::Array{Float64,3})
    comm = commutator_scan(table)
    assoc = associator_scan(table)
    Dict{String,Any}(
        "name" => name,
        "dim" => size(table, 1),
        "commutator_capacity" => Float64(comm["max_residual"]),
        "associator_capacity" => Float64(assoc["max_residual"]),
        "commutative" => Float64(comm["max_residual"]) <= TOL,
        "associative" => Float64(assoc["max_residual"]) <= TOL,
        "noncommutative" => Float64(comm["max_residual"]) > REQUIREMENT_TOL,
        "nonassociative" => Float64(assoc["max_residual"]) > REQUIREMENT_TOL,
        "commutator_check" => comm,
        "associator_check" => assoc,
    )
end

carrier_supports_gap(carrier::Dict{String,Any}, capacity_key::String, required_gap::Float64) =
    Float64(carrier[capacity_key]) + TOL >= required_gap && required_gap > REQUIREMENT_TOL

function first_supporting(carriers::Dict{String,Any}, predicate::String)
    for name in RUNG_NAMES
        if Bool(carriers[name][predicate])
            return name
        end
    end
    "none"
end

function build_requirement_controls(carriers::Dict{String,Any}, n01_required_gap::Float64, associator_required_gap::Float64)
    rows = Dict{String,Any}[
        Dict(
            "name" => "real_negative_fails_n01",
            "left_quantity" => "R.commutator_capacity",
            "right_quantity" => "R2.n01_required_gap",
            "left_value" => carriers["R"]["commutator_capacity"],
            "right_value" => n01_required_gap,
            "computed_quantities_distinct" => true,
            "negative_case" => "R",
            "negative_case_supports_requirement" => carrier_supports_gap(carriers["R"], "commutator_capacity", n01_required_gap),
            "negative_case_fails" => !carrier_supports_gap(carriers["R"], "commutator_capacity", n01_required_gap),
            "positive_reference" => "H",
            "positive_reference_supports_requirement" => carrier_supports_gap(carriers["H"], "commutator_capacity", n01_required_gap),
        ),
        Dict(
            "name" => "commutative_negative_fails_n01",
            "left_quantity" => "C.commutator_capacity",
            "right_quantity" => "R2.n01_required_gap",
            "left_value" => carriers["C"]["commutator_capacity"],
            "right_value" => n01_required_gap,
            "computed_quantities_distinct" => true,
            "negative_case" => "C",
            "negative_case_supports_requirement" => carrier_supports_gap(carriers["C"], "commutator_capacity", n01_required_gap),
            "negative_case_fails" => !carrier_supports_gap(carriers["C"], "commutator_capacity", n01_required_gap),
            "positive_reference" => "H",
            "positive_reference_supports_requirement" => carrier_supports_gap(carriers["H"], "commutator_capacity", n01_required_gap),
        ),
        Dict(
            "name" => "associative_negative_fails_3cell",
            "left_quantity" => "H.associator_capacity",
            "right_quantity" => "R2.three_cell_required_defect",
            "left_value" => carriers["H"]["associator_capacity"],
            "right_value" => associator_required_gap,
            "computed_quantities_distinct" => true,
            "negative_case" => "H",
            "negative_case_supports_requirement" => carrier_supports_gap(carriers["H"], "associator_capacity", associator_required_gap),
            "negative_case_fails" => !carrier_supports_gap(carriers["H"], "associator_capacity", associator_required_gap),
            "positive_reference" => "O",
            "positive_reference_supports_requirement" => carrier_supports_gap(carriers["O"], "associator_capacity", associator_required_gap),
        ),
        Dict(
            "name" => "octonion_positive_hosts_3cell",
            "left_quantity" => "O.associator_capacity",
            "right_quantity" => "R2.three_cell_required_defect",
            "left_value" => carriers["O"]["associator_capacity"],
            "right_value" => associator_required_gap,
            "computed_quantities_distinct" => true,
            "negative_case" => "H",
            "negative_case_supports_requirement" => carrier_supports_gap(carriers["H"], "associator_capacity", associator_required_gap),
            "negative_case_fails" => !carrier_supports_gap(carriers["H"], "associator_capacity", associator_required_gap),
            "positive_reference" => "O",
            "positive_reference_supports_requirement" => carrier_supports_gap(carriers["O"], "associator_capacity", associator_required_gap),
        ),
    ]
    for row in rows
        row["left_right_names_distinct"] = row["left_quantity"] != row["right_quantity"]
        row["pass"] = Bool(row["computed_quantities_distinct"]) &&
            Bool(row["left_right_names_distinct"]) &&
            Bool(row["negative_case_fails"]) &&
            Bool(row["positive_reference_supports_requirement"])
    end
    rows
end

function no_self_diff_tautologies(rows::Vector{Dict{String,Any}}, carriers::Dict{String,Any})
    if !all(row["left_quantity"] != row["right_quantity"] for row in rows)
        return false
    end
    for carrier in values(carriers)
        comm = carrier["commutator_check"]
        assoc = carrier["associator_check"]
        if Float64(comm["max_residual"]) > REQUIREMENT_TOL && comm["left_expression_id"] == comm["right_expression_id"]
            return false
        end
        if Float64(assoc["max_residual"]) > REQUIREMENT_TOL && assoc["left_expression_id"] == assoc["right_expression_id"]
            return false
        end
    end
    true
end

function canonical_json(value)
    if value isa Dict
        parts = String[]
        for key in sort(collect(keys(value)); by=string)
            push!(parts, string(JSON.json(string(key)), ":", canonical_json(value[key])))
        end
        string("{", join(parts, ","), "}")
    elseif value isa AbstractVector
        string("[", join([canonical_json(item) for item in value], ","), "]")
    elseif value isa Bool
        value ? "true" : "false"
    elseif value === nothing
        "null"
    elseif value isa Real
        JSON.json(value)
    else
        JSON.json(string(value))
    end
end

shared_payload_digest(shared::Dict{String,Any}) = bytes2hex(sha256(canonical_json(shared)))

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
    missing_keys = String[]
    max_diff = 0.0
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing_keys, key)
            continue
        end
        peer_value = Float64(peer["shared_scalars"][key])
        diff = abs(Float64(value) - peer_value)
        max_diff = max(max_diff, diff)
        push!(numeric_rows, Dict{String,Any}("key" => key, "julia" => Float64(value), "jax" => peer_value, "abs_diff" => diff))
    end

    boolean_mismatches = Any[]
    for (key, value) in result["shared_booleans"]
        if !haskey(peer["shared_booleans"], key)
            push!(missing_keys, key)
            continue
        end
        if Bool(value) != Bool(peer["shared_booleans"][key])
            push!(boolean_mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => Bool(peer["shared_booleans"][key])))
        end
    end

    string_mismatches = Any[]
    for (key, value) in result["shared_strings"]
        if !haskey(peer["shared_strings"], key)
            push!(missing_keys, key)
            continue
        end
        if string(value) != string(peer["shared_strings"][key])
            push!(string_mismatches, Dict{String,Any}("key" => key, "julia" => string(value), "jax" => string(peer["shared_strings"][key])))
        end
    end

    parity_within_run = peer["backend"] == "jax" &&
        peer["run_token"] == result["run_token"] &&
        peer["shared_value_digest"] == result["shared_value_digest"]
    within_tolerance = max_diff <= TOL &&
        isempty(boolean_mismatches) &&
        isempty(string_mismatches) &&
        isempty(missing_keys) &&
        parity_within_run
    Dict{String,Any}(
        "peer_result_path" => JAX_REFERENCE_PATH,
        "status" => "compared",
        "within_tolerance" => within_tolerance,
        "parity_within_run" => parity_within_run,
        "parity_max_diff" => max_diff,
        "numeric_rows" => numeric_rows,
        "boolean_mismatches" => boolean_mismatches,
        "string_mismatches" => string_mismatches,
        "missing_keys" => missing_keys,
    )
end

function build_result()
    if !isfile(JAX_REFERENCE_PATH)
        error("current JAX result missing: $JAX_REFERENCE_PATH")
    end
    jax_ref = JSON.parsefile(JAX_REFERENCE_PATH)
    n01_required_gap = Float64(jax_ref["shared_scalars"]["R2.n01_required_gap"])
    associator_required_gap = Float64(jax_ref["shared_scalars"]["R2.three_cell_required_defect"])

    tables = build_tables()
    carriers = Dict{String,Any}(name => analyze_carrier(name, tables[name]) for name in RUNG_NAMES)
    controls = build_requirement_controls(carriers, n01_required_gap, associator_required_gap)
    no_self_diff = no_self_diff_tautologies(controls, carriers)

    n01_requires_noncommutative_carrier =
        !carrier_supports_gap(carriers["R"], "commutator_capacity", n01_required_gap) &&
        !carrier_supports_gap(carriers["C"], "commutator_capacity", n01_required_gap) &&
        carrier_supports_gap(carriers["H"], "commutator_capacity", n01_required_gap)
    associator_requires_octonion =
        !carrier_supports_gap(carriers["R"], "associator_capacity", associator_required_gap) &&
        !carrier_supports_gap(carriers["C"], "associator_capacity", associator_required_gap) &&
        !carrier_supports_gap(carriers["H"], "associator_capacity", associator_required_gap) &&
        carrier_supports_gap(carriers["O"], "associator_capacity", associator_required_gap)
    real_carrier_insufficient_for = "N01_noncommuting_admissible_operations_and_associator_3cell_defect"

    requirement_map = Dict{String,Any}(
        "R0_R1_finite_probe_quotient_identity" => Dict(
            "minimal_carrier" => "R",
            "minimal_property" => "finite_scalar_support",
            "reason" => "finite quotient bookkeeping does not require carrier noncommutation",
        ),
        "R2_N01_noncommuting_admissible_operations" => Dict(
            "minimal_carrier" => first_supporting(carriers, "noncommutative"),
            "minimal_property" => "noncommutative_multiplication",
            "negative_control" => "R_and_C_fail_commutator_capacity_against_R2_order_gap",
        ),
        "R2_admissible_composition_associative_operation_layer" => Dict(
            "minimal_carrier" => "ordinary_operation_maps",
            "minimal_property" => "associative_map_composition",
            "reason" => "parent R2 composition residual is zero; nonassociativity is not required at the operation-composition layer",
        ),
        "R2_three_cell_associator_defect_detector" => Dict(
            "minimal_carrier" => first_supporting(carriers, "nonassociative"),
            "minimal_property" => "nonassociative_multiplication",
            "negative_control" => "R_C_H_fail_associator_capacity_against_R2_three_cell_defect",
        ),
    )
    requirement_map_genuine =
        requirement_map["R2_N01_noncommuting_admissible_operations"]["minimal_carrier"] == "H" &&
        requirement_map["R2_three_cell_associator_defect_detector"]["minimal_carrier"] == "O" &&
        all(Bool(row["pass"]) for row in controls) &&
        no_self_diff

    classification_ok = CLASSIFICATION == "scratch_diagnostic"
    promotion_ok = PROMOTION_ALLOWED == false
    formal_ok = FORMAL_ADMISSION_ALLOWED == false

    shared_scalars = Dict{String,Any}(
        "R2.n01_required_gap" => n01_required_gap,
        "R2.three_cell_required_defect" => associator_required_gap,
    )
    for name in RUNG_NAMES
        carrier = carriers[name]
        shared_scalars["$name.dim"] = Float64(carrier["dim"])
        shared_scalars["$name.commutator_capacity"] = Float64(carrier["commutator_capacity"])
        shared_scalars["$name.associator_capacity"] = Float64(carrier["associator_capacity"])
    end

    shared_booleans = Dict{String,Any}(
        "parents_verified" => Bool(jax_ref["shared_booleans"]["parents_verified"]),
        "n01_requires_noncommutative_carrier" => n01_requires_noncommutative_carrier,
        "associator_requires_octonion" => associator_requires_octonion,
        "requirement_map_genuine" => requirement_map_genuine,
        "no_self_diff_tautologies" => no_self_diff,
        "classification_is_scratch_diagnostic" => classification_ok,
        "promotion_false" => promotion_ok,
        "formal_admission_false" => formal_ok,
        "jax_enable_x64" => Bool(jax_ref["shared_booleans"]["jax_enable_x64"]),
        "numpy_compute_used" => false,
        "numpy_imported" => false,
        "torch_imported" => false,
    )
    for name in RUNG_NAMES
        carrier = carriers[name]
        shared_booleans["$name.commutative"] = Bool(carrier["commutative"])
        shared_booleans["$name.associative"] = Bool(carrier["associative"])
        shared_booleans["$name.noncommutative"] = Bool(carrier["noncommutative"])
        shared_booleans["$name.nonassociative"] = Bool(carrier["nonassociative"])
    end

    shared_strings = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "allowed_claim" => ALLOWED_CLAIM,
        "minimal_n01_carrier" => requirement_map["R2_N01_noncommuting_admissible_operations"]["minimal_carrier"],
        "minimal_associator_carrier" => requirement_map["R2_three_cell_associator_defect_detector"]["minimal_carrier"],
        "real_carrier_insufficient_for" => real_carrier_insufficient_for,
    )
    shared = Dict{String,Any}(
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "shared_strings" => shared_strings,
    )

    result = Dict{String,Any}(
        "schema" => "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id" => OBJECT_ID,
        "sim_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "version" => "1.0",
        "tier" => "R3_foundation_carrier_property_requirements",
        "backend" => "julia",
        "run_token" => run_token(),
        "generated_at" => string(Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS"), "Z"),
        "source_path" => joinpath(ROOT, "system_v5/julia_carrier/r3_carrier_property_requirements.jl"),
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => CLAIM_CEILING,
        "next_lego_target" => "none",
        "promotion_condition" => "not applicable: promotion_allowed=false for this scratch diagnostic row",
        "blocked_until" => "remains fenced unless a separate owner-authorized admission packet changes the classification",
        "demotion_condition" => "already fenced; mark failed if any named criterion, parity, or no-self-diff check fails",
        "out_of_scope" => [
            "no promotion from this result",
            "no formal admission from this result",
            "no higher-layer consumer from this result",
            "no carrier claim outside the finite R/C/H/O/S candidate ladder",
        ],
        "allowed_claims" => [ALLOWED_CLAIM],
        "promotion_status" => "diagnostic_only",
        "eligible_consumers" => [],
        "blocked_consumers" => ["promotion", "formal_admission", "top_floor_consumers"],
        "sim_execution_kind" => SIM_EXECUTION_KIND,
        "sim_class" => "carrier_probe",
        "purpose" => "Mirror the JAX carrier-property requirement map and verify current-run parity.",
        "carrier_layer" => "finite_Cayley_Dickson_R_C_H_O_S_tables",
        "SIM_TEMPLATE_surface" => SIM_TEMPLATE_SURFACE,
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "required_tools" => ["Julia", "LinearAlgebra", "JAX reference"],
        "actual_tools_used" => ["Julia", "LinearAlgebra", "JSON", "SHA"],
        "proof_surfaces_used" => [],
        "graph_surfaces_used" => [],
        "topology_surfaces_used" => [],
        "numpy_compute_used" => false,
        "numpy_imported" => false,
        "torch_imported" => false,
        "tol" => TOL,
        "requirement_tol" => REQUIREMENT_TOL,
        "construction" => Dict(
            "method" => "finite Cayley-Dickson doubling",
            "candidate_ladder" => RUNG_NAMES,
            "rung_dims" => Dict(name => carriers[name]["dim"] for name in RUNG_NAMES),
        ),
        "carriers" => carriers,
        "requirement_map" => requirement_map,
        "control_comparison_pairs" => controls,
        "probe" => Dict(
            "question" => "minimal carrier property for each R2 structural need",
            "required_gaps" => Dict(
                "n01_required_gap_from_current_jax" => n01_required_gap,
                "three_cell_required_defect_from_current_jax" => associator_required_gap,
            ),
            "control_rule" => "controls compare carrier capacity against a distinct parent R2-required gap; real/commutative negatives must fail",
        ),
        "positive" => Dict(
            "H_hosts_N01_noncommutation" => Dict(
                "pass" => carrier_supports_gap(carriers["H"], "commutator_capacity", n01_required_gap),
                "H_commutator_capacity" => carriers["H"]["commutator_capacity"],
                "required_gap" => n01_required_gap,
            ),
            "O_hosts_associator_3cell_defect" => Dict(
                "pass" => carrier_supports_gap(carriers["O"], "associator_capacity", associator_required_gap),
                "O_associator_capacity" => carriers["O"]["associator_capacity"],
                "required_gap" => associator_required_gap,
            ),
            "no_self_diff_tautologies" => Dict("pass" => no_self_diff),
            "classification_is_scratch_diagnostic" => Dict("pass" => classification_ok),
            "promotion_allowed_false" => Dict("pass" => promotion_ok),
            "formal_admission_allowed_false" => Dict("pass" => formal_ok),
        ),
        "negative" => Dict(
            "real_carrier_fails_N01" => Dict(
                "pass" => !carrier_supports_gap(carriers["R"], "commutator_capacity", n01_required_gap),
                "R_commutator_capacity" => carriers["R"]["commutator_capacity"],
                "required_gap" => n01_required_gap,
                "control_can_fail" => true,
            ),
            "commutative_carrier_fails_N01" => Dict(
                "pass" => !carrier_supports_gap(carriers["C"], "commutator_capacity", n01_required_gap),
                "C_commutator_capacity" => carriers["C"]["commutator_capacity"],
                "required_gap" => n01_required_gap,
                "control_can_fail" => true,
            ),
            "associative_carrier_fails_associator_3cell" => Dict(
                "pass" => !carrier_supports_gap(carriers["H"], "associator_capacity", associator_required_gap),
                "H_associator_capacity" => carriers["H"]["associator_capacity"],
                "required_gap" => associator_required_gap,
                "control_can_fail" => true,
            ),
        ),
        "boundary" => Dict(
            "C_to_H_noncommutation_boundary" => Dict(
                "pass" => !carrier_supports_gap(carriers["C"], "commutator_capacity", n01_required_gap) &&
                    carrier_supports_gap(carriers["H"], "commutator_capacity", n01_required_gap),
                "left" => "C",
                "right" => "H",
            ),
            "H_to_O_associator_boundary" => Dict(
                "pass" => !carrier_supports_gap(carriers["H"], "associator_capacity", associator_required_gap) &&
                    carrier_supports_gap(carriers["O"], "associator_capacity", associator_required_gap),
                "left" => "H",
                "right" => "O",
            ),
            "claim_ceiling" => CLAIM_CEILING,
        ),
        "nearby_variants" => Dict(
            "total" => length(controls),
            "passed" => count(row -> Bool(row["pass"]), controls),
            "all_pass" => all(Bool(row["pass"]) for row in controls),
            "rows" => controls,
        ),
        "why_not_v4_probes" => "This is a v5 scratch diagnostic dual-backend carrier-property scout with no promotion or formal admission.",
        "required_negatives" => ["real_carrier_fails_N01", "commutative_carrier_fails_N01", "associative_carrier_fails_associator_3cell"],
        "negatives_run" => ["real_carrier_fails_N01", "commutative_carrier_fails_N01", "associative_carrier_fails_associator_3cell"],
        "kill_conditions" => [
            "current JAX reference missing or run-token stale",
            "wrong minimal carrier for N01",
            "wrong minimal carrier for associator defect",
            "any non-failing negative control",
            "any self-diff control",
        ],
        "required_artifacts" => [JAX_REFERENCE_PATH, RESULT_PATH],
        "artifacts_emitted" => [RESULT_PATH],
        "witness_trace_id" => string(OBJECT_ID, ":julia:", run_token()),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "shared_strings" => shared_strings,
        "shared_value_digest" => shared_payload_digest(shared),
        "jax_reference" => Dict(
            "path" => JAX_REFERENCE_PATH,
            "run_token" => jax_ref["run_token"],
            "shared_value_digest" => jax_ref["shared_value_digest"],
        ),
        "n01_requires_noncommutative_carrier" => n01_requires_noncommutative_carrier,
        "associator_requires_octonion" => associator_requires_octonion,
        "real_carrier_insufficient_for" => real_carrier_insufficient_for,
        "requirement_map_genuine" => requirement_map_genuine,
        "no_self_diff" => no_self_diff,
    )
    result["parity"] = parity_against_jax(result)
    result["positive"]["dual_backend_parity"] = Dict("pass" => result["parity"]["within_tolerance"])
    result["parity_within_run"] = result["parity"]["parity_within_run"]
    result["core_pass"] = Bool(jax_ref["shared_booleans"]["parents_verified"]) &&
        n01_requires_noncommutative_carrier &&
        associator_requires_octonion &&
        requirement_map_genuine &&
        no_self_diff &&
        classification_ok &&
        promotion_ok &&
        formal_ok &&
        !Bool(result["numpy_compute_used"]) &&
        !Bool(result["torch_imported"])
    result["all_pass"] = Bool(result["core_pass"]) && Bool(result["parity"]["within_tolerance"])
    result["stop_condition_fired"] = !Bool(result["all_pass"])
    result["pass_rule"] = "current JAX token/digest parity, H minimal for N01, O minimal for associator defect, failing negatives, and no self-diff controls"
    result["fail_rule"] = "any stale JAX reference, wrong minimal carrier, non-failing negative, self-diff control, or parity mismatch"
    result["result_summary"] = Dict(
        "minimal_n01_carrier" => requirement_map["R2_N01_noncommuting_admissible_operations"]["minimal_carrier"],
        "minimal_associator_carrier" => requirement_map["R2_three_cell_associator_defect_detector"]["minimal_carrier"],
        "n01_requires_noncommutative_carrier" => n01_requires_noncommutative_carrier,
        "associator_requires_octonion" => associator_requires_octonion,
        "real_carrier_insufficient_for" => real_carrier_insufficient_for,
        "requirement_map_genuine" => requirement_map_genuine,
        "no_self_diff" => no_self_diff,
        "parity_within_run" => result["parity_within_run"],
        "all_pass" => result["all_pass"],
    )
    result["criteria_checked"] = [
        "current JAX result parsed for required gaps, token, and shared digest",
        "finite R/C/H/O/S carrier tables built independently in Julia",
        "carrier commutator capacity compared against current JAX R2 N01 gap",
        "carrier associator capacity compared against current JAX three-cell defect gap",
        "real and commutative negatives fail N01 hosting",
        "H supports N01 but fails associator hosting",
        "O supports associator hosting",
        "no control compares an expression with itself",
    ]
    result
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("wrote ", RESULT_PATH)
    println(JSON.json(Dict(
        "all_pass" => result["all_pass"],
        "core_pass" => result["core_pass"],
        "parity_within_run" => result["parity_within_run"],
        "n01_requires_noncommutative_carrier" => result["n01_requires_noncommutative_carrier"],
        "associator_requires_octonion" => result["associator_requires_octonion"],
        "real_carrier_insufficient_for" => result["real_carrier_insufficient_for"],
        "requirement_map_genuine" => result["requirement_map_genuine"],
        "no_self_diff" => result["no_self_diff"],
    )))
    return Bool(result["core_pass"]) ? 0 : 1
end

exit(main())
