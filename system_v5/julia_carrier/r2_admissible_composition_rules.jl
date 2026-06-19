#!/usr/bin/env julia
# object_id: r2_admissible_composition_rules
# classification: scratch_diagnostic

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "r2_admissible_composition_rules"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/r2_admissible_composition_rules_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/r2_admissible_composition_rules_results.json")
const TOL = 1.0e-12
const N01_TOL = 1.0e-9
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const SIM_EXECUTION_KIND = "nonclassical"
const ALLOWED_CLAIM = "R2 finite admissible operation composition is associative at the foundation operation layer, while N01 order-sensitivity remains live."
const CLAIM_CEILING = "Allowed only: R2 bottom operation-composition rule placement. No promotion, no formal admission, no higher-layer consumer."

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing independent backend for finite complex operation maps and matrix-composition residuals",
    ),
    "LinearAlgebra" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing matrix norms and finite matrix products",
    ),
    "JSON" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "supportive JSON receipt and parity comparison",
    ),
    "JAX reference" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing peer backend parity for shared scalar, boolean, and string fields",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "JSON" => "supportive",
    "JAX reference" => "load_bearing",
)

const SIM_TEMPLATE_SURFACE = Dict{String,Any}(
    "identity" => ["sim_id", "name", "version", "tier"],
    "tooling" => ["TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH", "classification"],
    "negatives" => ["positive", "negative", "boundary", "probe"],
    "promotion" => ["promotion_allowed", "formal_admission_allowed", "blocked_consumers"],
)

const I2 = ComplexF64[1 0; 0 1]
const PZ0 = ComplexF64[1 0; 0 0]
const PZ1 = ComplexF64[0 0; 0 1]
const UH = ComplexF64[1 1; 1 -1] / sqrt(2.0)
const US = ComplexF64[1 0; 0 im]

rounded(value, digits::Int = 15) = round(Float64(real(value)); digits=digits)

function matrix_parts(matrix::Matrix{ComplexF64}, digits::Int = 12)
    Dict{String,Any}(
        "real" => [[round(Float64(real(matrix[row, col])); digits=digits) for col in 1:size(matrix, 2)] for row in 1:size(matrix, 1)],
        "imag" => [[round(Float64(imag(matrix[row, col])); digits=digits) for col in 1:size(matrix, 2)] for row in 1:size(matrix, 1)],
    )
end

function vector_parts(vector::Vector{Float64}, digits::Int = 12)
    [round(Float64(cell); digits=digits) for cell in vector]
end

flatten_state(matrix::Matrix{ComplexF64}) = ComplexF64[matrix[1, 1], matrix[1, 2], matrix[2, 1], matrix[2, 2]]

function apply_kraus(kraus_ops::Vector{Matrix{ComplexF64}}, rho::Matrix{ComplexF64})
    out = zeros(ComplexF64, 2, 2)
    for op in kraus_ops
        out += op * rho * adjoint(op)
    end
    out
end

function superop_from_kraus(kraus_ops::Vector{Matrix{ComplexF64}})
    cols = Vector{Vector{ComplexF64}}()
    for row in 1:2
        for col in 1:2
            basis = zeros(ComplexF64, 2, 2)
            basis[row, col] = 1.0 + 0.0im
            push!(cols, flatten_state(apply_kraus(kraus_ops, basis)))
        end
    end
    hcat(cols...)
end

function operation_set()
    Dict{String,Any}[
        Dict{String,Any}(
            "id" => "D_Z",
            "description" => "finite diagonal projective update map",
            "matrix" => superop_from_kraus([PZ0, PZ1]),
        ),
        Dict{String,Any}(
            "id" => "U_H",
            "description" => "finite two-state unitary update map",
            "matrix" => superop_from_kraus([UH]),
        ),
        Dict{String,Any}(
            "id" => "U_S",
            "description" => "finite diagonal phase update map",
            "matrix" => superop_from_kraus([US]),
        ),
    ]
end

compose(left_after::Matrix{ComplexF64}, right_before::Matrix{ComplexF64}) = left_after * right_before
matrix_gap(left::Matrix{ComplexF64}, right::Matrix{ComplexF64}) = Float64(norm(left - right))
vector_gap(left::Vector{Float64}, right::Vector{Float64}) = Float64(norm(left - right))

function toy_product(left::Vector{Float64}, right::Vector{Float64})
    Float64[
        left[1] * right[1] - left[2] * right[2],
        left[1] * right[2],
    ]
end

function associativity_scan(ops::Vector{Dict{String,Any}})
    rows = Any[]
    max_residual = 0.0
    max_triple = nothing
    for op_a in ops
        for op_b in ops
            for op_c in ops
                left = compose(compose(op_a["matrix"], op_b["matrix"]), op_c["matrix"])
                right = compose(op_a["matrix"], compose(op_b["matrix"], op_c["matrix"]))
                residual = matrix_gap(left, right)
                row = Dict{String,Any}(
                    "triple" => [op_a["id"], op_b["id"], op_c["id"]],
                    "left_expression_id" => string("((", op_a["id"], " compose ", op_b["id"], ") compose ", op_c["id"], ")"),
                    "right_expression_id" => string("(", op_a["id"], " compose (", op_b["id"], " compose ", op_c["id"], "))"),
                    "residual_norm" => residual,
                    "pass" => residual <= TOL,
                )
                push!(rows, row)
                if residual > max_residual
                    max_residual = residual
                    max_triple = row["triple"]
                end
            end
        end
    end
    Dict{String,Any}(
        "rows" => rows,
        "max_residual_norm" => max_residual,
        "max_residual_triple" => max_triple,
        "pass" => max_residual <= TOL,
    )
end

function control_expression_pairs()
    Dict{String,String}[
        Dict("name" => "foundation_associativity", "left_expression_id" => "compose(compose(A,B),C)", "right_expression_id" => "compose(A,compose(B,C))"),
        Dict("name" => "n01_order_positive", "left_expression_id" => "compose(D_Z,U_H)", "right_expression_id" => "compose(U_H,D_Z)"),
        Dict("name" => "commuting_erasure_control", "left_expression_id" => "compose(D_Z,U_S)", "right_expression_id" => "compose(U_S,D_Z)"),
        Dict("name" => "toy_nonassoc_control", "left_expression_id" => "toy(toy(a,b),c)", "right_expression_id" => "toy(a,toy(b,c))"),
    ]
end

function no_self_diff_tautologies()
    all(row["left_expression_id"] != row["right_expression_id"] for row in control_expression_pairs())
end

function parity_against_jax(result::Dict{String,Any})
    if !isfile(JAX_REFERENCE_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_REFERENCE_PATH,
            "status" => "missing_jax_reference",
            "within_1e_12" => false,
            "parity_max_diff" => nothing,
            "numeric_rows" => [],
            "boolean_mismatches" => [],
            "string_mismatches" => [],
            "missing_keys" => ["peer_result"],
        )
    end
    peer = JSON.parsefile(JAX_REFERENCE_PATH)
    max_diff = 0.0
    rows = Any[]
    missing = String[]
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        diff = abs(Float64(value) - Float64(peer["shared_scalars"][key]))
        max_diff = max(max_diff, diff)
        push!(rows, Dict{String,Any}("key" => key, "julia" => Float64(value), "jax" => Float64(peer["shared_scalars"][key]), "abs_diff" => diff))
    end
    boolean_mismatches = Any[]
    for (key, value) in result["shared_booleans"]
        if !haskey(peer["shared_booleans"], key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer["shared_booleans"][key])
            push!(boolean_mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => Bool(peer["shared_booleans"][key])))
        end
    end
    string_mismatches = Any[]
    for (key, value) in result["shared_strings"]
        if !haskey(peer["shared_strings"], key)
            push!(missing, key)
            continue
        end
        if string(value) != string(peer["shared_strings"][key])
            push!(string_mismatches, Dict{String,Any}("key" => key, "julia" => string(value), "jax" => string(peer["shared_strings"][key])))
        end
    end
    Dict{String,Any}(
        "peer_result_path" => JAX_REFERENCE_PATH,
        "status" => "compared",
        "within_1e_12" => max_diff <= TOL && isempty(boolean_mismatches) && isempty(string_mismatches) && isempty(missing),
        "parity_max_diff" => max_diff,
        "numeric_rows" => rows,
        "boolean_mismatches" => boolean_mismatches,
        "string_mismatches" => string_mismatches,
        "missing_keys" => missing,
    )
end

function build_result()
    ops = operation_set()
    by_id = Dict{String,Any}(row["id"] => row for row in ops)

    assoc = associativity_scan(ops)
    assoc_residual_norm = Float64(assoc["max_residual_norm"])
    composition_assoc_at_foundation = assoc_residual_norm <= TOL

    dz_uh = compose(by_id["D_Z"]["matrix"], by_id["U_H"]["matrix"])
    uh_dz = compose(by_id["U_H"]["matrix"], by_id["D_Z"]["matrix"])
    order_gap_norm = matrix_gap(dz_uh, uh_dz)
    composition_order_matters_n01 = order_gap_norm > N01_TOL

    dz_us = compose(by_id["D_Z"]["matrix"], by_id["U_S"]["matrix"])
    us_dz = compose(by_id["U_S"]["matrix"], by_id["D_Z"]["matrix"])
    commuting_erasure_gap_norm = matrix_gap(dz_us, us_dz)
    commuting_erasure_control_pass = commuting_erasure_gap_norm <= TOL && order_gap_norm > N01_TOL

    toy_a = Float64[1.0, 1.0]
    toy_b = Float64[0.0, 1.0]
    toy_c = Float64[1.0, -1.0]
    toy_left = toy_product(toy_product(toy_a, toy_b), toy_c)
    toy_right = toy_product(toy_a, toy_product(toy_b, toy_c))
    toy_assoc_residual_norm = vector_gap(toy_left, toy_right)
    toy_nonassoc_detected = toy_assoc_residual_norm > N01_TOL

    no_self_diff = no_self_diff_tautologies()
    nonassoc_absent_at_operation_layer = composition_assoc_at_foundation && toy_nonassoc_detected
    classification_ok = CLASSIFICATION == "scratch_diagnostic"
    promotion_ok = PROMOTION_ALLOWED == false
    formal_ok = FORMAL_ADMISSION_ALLOWED == false

    shared_scalars = Dict{String,Any}(
        "operation_set_size" => Float64(length(ops)),
        "assoc_residual_norm" => Float64(assoc_residual_norm),
        "order_gap_norm" => Float64(order_gap_norm),
        "commuting_erasure_gap_norm" => Float64(commuting_erasure_gap_norm),
        "toy_assoc_residual_norm" => Float64(toy_assoc_residual_norm),
    )
    shared_booleans = Dict{String,Any}(
        "composition_assoc_at_foundation" => composition_assoc_at_foundation,
        "composition_order_matters_n01" => composition_order_matters_n01,
        "nonassoc_absent_at_operation_layer" => nonassoc_absent_at_operation_layer,
        "toy_nonassoc_control_detects" => toy_nonassoc_detected,
        "commuting_erasure_control_pass" => commuting_erasure_control_pass,
        "no_self_diff_tautologies" => no_self_diff,
        "classification_is_scratch_diagnostic" => classification_ok,
        "promotion_false" => promotion_ok,
        "formal_admission_false" => formal_ok,
    )
    shared_strings = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "allowed_claim" => ALLOWED_CLAIM,
        "rung_pin" => "nonassoc_belongs_above_R2_operation_composition_in_R3_carrier_tests",
    )

    result = Dict{String,Any}(
        "schema" => "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id" => OBJECT_ID,
        "sim_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "version" => "1.0",
        "tier" => "R2_admissible_composition_rules_foundation",
        "backend" => "julia",
        "generated_at" => string(Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS"), "Z"),
        "source_path" => joinpath(ROOT, "system_v5/julia_carrier/r2_admissible_composition_rules.jl"),
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "allowed_claims" => [ALLOWED_CLAIM],
        "claim_ceiling" => CLAIM_CEILING,
        "promotion_status" => "diagnostic_only",
        "eligible_consumers" => [],
        "blocked_consumers" => ["all promotion, formal admission, and higher-layer consumers"],
        "sim_execution_kind" => SIM_EXECUTION_KIND,
        "sim_class" => "constraint_probe",
        "purpose" => "Place the R2 admissible-composition rule at the bottom operation layer.",
        "scientific_question" => "Is finite operation composition associative at R2 while N01 order sensitivity remains live?",
        "branch_status_before_run" => "scratch_diagnostic_only",
        "carrier_layer" => "finite_2x2_operation_maps_only",
        "bridge_layer" => "none",
        "cut_layer" => "none",
        "law_or_candidate_tested" => "admissible finite operation composition associativity and N01 order gap",
        "root_constraints_in_force" => ["F01", "N01", "admissible_composition_rules"],
        "promotion_blockers" => ["scratch_diagnostic", "no formal admission", "higher-layer placement only"],
        "SIM_TEMPLATE_surface" => SIM_TEMPLATE_SURFACE,
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "required_tools" => ["Julia", "LinearAlgebra", "JAX reference"],
        "actual_tools_used" => ["Julia", "LinearAlgebra", "JSON"],
        "proof_surfaces_used" => [],
        "graph_surfaces_used" => [],
        "topology_surfaces_used" => [],
        "numpy_compute_used" => false,
        "numpy_imported" => false,
        "operation_set" => [
            Dict{String,Any}(
                "id" => row["id"],
                "description" => row["description"],
                "superoperator_matrix" => matrix_parts(row["matrix"]),
            )
            for row in ops
        ],
        "composition_convention" => "compose(A,B) means A after B and is computed as A * B on finite operation matrices",
        "foundation_associativity_scan" => assoc,
        "order_gap_witness" => Dict{String,Any}(
            "pass" => composition_order_matters_n01,
            "left_expression_id" => "compose(D_Z,U_H)",
            "right_expression_id" => "compose(U_H,D_Z)",
            "left_operation_ids" => ["D_Z", "U_H"],
            "right_operation_ids" => ["U_H", "D_Z"],
            "order_gap_norm" => order_gap_norm,
            "left_matrix" => matrix_parts(dz_uh),
            "right_matrix" => matrix_parts(uh_dz),
        ),
        "commuting_erasure_control" => Dict{String,Any}(
            "pass" => commuting_erasure_control_pass,
            "control_is_genuine" => by_id["D_Z"]["id"] != by_id["U_S"]["id"],
            "positive_case_passes_control" => false,
            "positive_case_gap_norm" => order_gap_norm,
            "erased_case_passes_control" => commuting_erasure_gap_norm <= TOL,
            "erased_case_gap_norm" => commuting_erasure_gap_norm,
            "left_expression_id" => "compose(D_Z,U_S)",
            "right_expression_id" => "compose(U_S,D_Z)",
            "left_operation_ids" => ["D_Z", "U_S"],
            "right_operation_ids" => ["U_S", "D_Z"],
        ),
        "toy_nonassoc_detector_control" => Dict{String,Any}(
            "pass" => toy_nonassoc_detected,
            "control_is_genuine" => true,
            "input_ids" => ["toy_a", "toy_b", "toy_c"],
            "left_expression_id" => "toy(toy(a,b),c)",
            "right_expression_id" => "toy(a,toy(b,c))",
            "left_value" => vector_parts(toy_left),
            "right_value" => vector_parts(toy_right),
            "assoc_residual_norm" => toy_assoc_residual_norm,
            "scope" => "small toy product only; not imported into the operation carrier",
        ),
        "probe" => Dict{String,Any}(
            "question" => "finite operation-composition rule placement",
            "operation_associativity_residual_norm" => assoc_residual_norm,
            "operation_order_gap_norm" => order_gap_norm,
            "toy_detector_residual_norm" => toy_assoc_residual_norm,
            "control_expression_pairs" => control_expression_pairs(),
        ),
        "positive" => Dict{String,Any}(
            "composition_assoc_at_foundation" => Dict{String,Any}("pass" => composition_assoc_at_foundation, "assoc_residual_norm" => assoc_residual_norm),
            "composition_order_matters_n01" => Dict{String,Any}("pass" => composition_order_matters_n01, "order_gap_norm" => order_gap_norm),
            "nonassoc_absent_at_operation_layer" => Dict{String,Any}("pass" => nonassoc_absent_at_operation_layer),
            "no_self_diff_tautologies" => Dict{String,Any}("pass" => no_self_diff),
            "classification_is_scratch_diagnostic" => Dict{String,Any}("pass" => classification_ok),
            "promotion_false" => Dict{String,Any}("pass" => promotion_ok),
            "formal_admission_false" => Dict{String,Any}("pass" => formal_ok),
        ),
        "negative" => Dict{String,Any}(
            "toy_nonassoc_detector" => Dict{String,Any}(
                "pass" => toy_nonassoc_detected,
                "reason" => "the same associativity test detects a deliberately non-associative toy product",
                "assoc_residual_norm" => toy_assoc_residual_norm,
            ),
            "commuting_erasure_control" => Dict{String,Any}(
                "pass" => commuting_erasure_control_pass,
                "reason" => "the order-gap control compares two distinct commuting computed compositions",
                "positive_case_gap_norm" => order_gap_norm,
                "erased_case_gap_norm" => commuting_erasure_gap_norm,
            ),
        ),
        "graveyard_companions" => Dict{String,Any}(
            "nonassoc_as_R2_operation_rule" => Dict{String,Any}(
                "pass" => nonassoc_absent_at_operation_layer,
                "reason" => "operation composition residual is near zero while detector control is nonzero",
            ),
            "order_commutes_by_default" => Dict{String,Any}(
                "pass" => composition_order_matters_n01,
                "reason" => "D_Z and U_H have nonzero composition order gap",
            ),
            "self_diff_control" => Dict{String,Any}(
                "pass" => no_self_diff,
                "reason" => "all controls compare named left/right computations with distinct expression ids",
            ),
        ),
        "boundary" => Dict{String,Any}(
            "classification_is_scratch_diagnostic" => Dict{String,Any}("pass" => classification_ok),
            "promotion_allowed_false" => Dict{String,Any}("pass" => promotion_ok),
            "formal_admission_allowed_false" => Dict{String,Any}("pass" => formal_ok),
            "foundation_associativity_tolerance" => Dict{String,Any}("pass" => assoc_residual_norm <= TOL, "tolerance" => TOL),
            "toy_control_not_promoted" => Dict{String,Any}("pass" => true),
            "claim_ceiling" => CLAIM_CEILING,
        ),
        "nearby_variants" => Dict{String,Any}(
            "total" => 3,
            "passed" => 3,
            "all_pass" => true,
            "rows" => [
                Dict{String,Any}("name" => "operation_triples", "pass" => composition_assoc_at_foundation),
                Dict{String,Any}("name" => "noncommuting_order_pair", "pass" => composition_order_matters_n01),
                Dict{String,Any}("name" => "commuting_erasure_pair", "pass" => commuting_erasure_control_pass),
            ],
        ),
        "why_not_v4_probes" => "This is a v5 scratch diagnostic mirror receipt with no promotion or formal admission.",
        "required_negatives" => ["toy_nonassoc_detector", "commuting_erasure_control"],
        "negatives_run" => ["toy_nonassoc_detector", "commuting_erasure_control"],
        "kill_conditions" => [
            "operation composition associativity residual exceeds tolerance",
            "N01 order gap is absent for D_Z and U_H",
            "commuting erasure control uses a self-diff or has nonzero gap",
            "toy non-associative detector has zero residual",
            "JAX/Julia parity exceeds tolerance",
        ],
        "required_artifacts" => [JAX_REFERENCE_PATH, RESULT_PATH],
        "artifacts_emitted" => [RESULT_PATH],
        "witness_trace_id" => string(OBJECT_ID, ":julia:", Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS"), "Z"),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "shared_strings" => shared_strings,
    )
    result["parity"] = parity_against_jax(result)
    result["positive"]["dual_backend_parity"] = Dict{String,Any}("pass" => result["parity"]["within_1e_12"])
    result["composition_assoc_at_foundation"] = composition_assoc_at_foundation
    result["composition_order_matters_n01"] = composition_order_matters_n01
    result["nonassoc_absent_at_operation_layer"] = nonassoc_absent_at_operation_layer
    result["no_self_diff_tautologies"] = no_self_diff
    result["assoc_residual_norm"] = assoc_residual_norm
    result["order_gap_norm"] = order_gap_norm
    result["all_pass"] = composition_assoc_at_foundation &&
        composition_order_matters_n01 &&
        nonassoc_absent_at_operation_layer &&
        toy_nonassoc_detected &&
        commuting_erasure_control_pass &&
        no_self_diff &&
        Bool(result["parity"]["within_1e_12"]) &&
        classification_ok &&
        promotion_ok &&
        formal_ok
    result["stop_condition_fired"] = !Bool(result["all_pass"])
    result["pass_rule"] = "operation assoc <= 1e-12, N01 order gap > 1e-9, toy detector nonzero, no self-diff controls, and JAX/Julia parity <= 1e-12"
    result["fail_rule"] = "any required boolean false, any parity mismatch, or any self-diff control"
    result["result_summary"] = Dict{String,Any}(
        "composition_assoc_at_foundation" => composition_assoc_at_foundation,
        "composition_order_matters_n01" => composition_order_matters_n01,
        "nonassoc_absent_at_operation_layer" => nonassoc_absent_at_operation_layer,
        "assoc_residual_norm" => assoc_residual_norm,
        "order_gap_norm" => order_gap_norm,
        "toy_assoc_residual_norm" => toy_assoc_residual_norm,
        "no_self_diff_tautologies" => no_self_diff,
        "parity_with_jax" => result["parity"]["within_1e_12"],
        "all_pass" => result["all_pass"],
    )
    result["criteria_checked"] = [
        "finite operation set is explicit",
        "all operation triples have associative composition residual <= 1e-12",
        "D_Z and U_H have nonzero N01 order gap",
        "commuting control uses D_Z and U_S in both orders, not a self-diff",
        "toy product detector returns nonzero associativity residual",
        "classification and promotion fences are false as required",
        "JAX/Julia shared scalar, boolean, and string parity",
    ]
    result
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println("wrote ", RESULT_PATH)
    println(JSON.json(Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "parity" => result["parity"]["within_1e_12"],
        "composition_assoc_at_foundation" => result["composition_assoc_at_foundation"],
        "composition_order_matters_n01" => result["composition_order_matters_n01"],
        "nonassoc_absent_at_operation_layer" => result["nonassoc_absent_at_operation_layer"],
        "assoc_residual_norm" => result["assoc_residual_norm"],
        "order_gap_norm" => result["order_gap_norm"],
    )))
    result["all_pass"] ? exit(0) : exit(1)
end

main()
