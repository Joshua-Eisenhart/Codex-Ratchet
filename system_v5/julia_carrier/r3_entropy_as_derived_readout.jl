#!/usr/bin/env julia
# object_id: r3_entropy_as_derived_readout
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using Printf
using UUIDs

const OBJECT_ID = "r3_entropy_as_derived_readout"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const DEFAULT_JAX_REFERENCE_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/r3_entropy_as_derived_readout_results.json")
const DEFAULT_RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/r3_entropy_as_derived_readout_julia_results.json")
const PARENT_RESULTS = [
    joinpath(ROOT, "system_v5/ops/formal_scouts/results/foundation_rung0to3_distinguishability_results.json"),
    joinpath(ROOT, "system_v5/ops/formal_scouts/results/r0_r1_r2_probe_quotient_micro_packet_results.json"),
    joinpath(ROOT, "system_v5/ops/formal_scouts/results/r2_admissible_operations_commutation_order_results.json"),
    joinpath(ROOT, "system_v5/ops/formal_scouts/results/r2_admissible_composition_rules_results.json"),
]
const TOL = 1.0e-12
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const SIM_EXECUTION_KIND = "nonclassical"
const ALLOWED_CLAIM = "R3 entropy is a downstream readout of the verified finite R2 probe-relative distinguishability quotient."
const BLOCKED_CLAIMS = [
    "formal_admission",
    "promotion",
    "physics_claim",
    "top_floor_claim",
]
const CLAIM_CEILING = "Allowed only: finite quotient/signature entropy readout at scratch level. The primitive remains distinguishability under M; entropy is not primitive."

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing independent x64-equivalent finite density, quotient, von-Neumann entropy, Shannon entropy, and control mirror",
    ),
    "LinearAlgebra" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing matrix traces, eigenvalues, norms, and finite projective probe statistics",
    ),
    "JSON" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization and current JAX receipt ingestion",
    ),
    "JAX peer" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing within-run parity reference passed by the JAX driver",
    ),
    "numpy" => Dict{String,Any}(
        "tried" => false,
        "used" => false,
        "reason" => "not part of the Julia mirror and not used for compute",
    ),
    "pytorch" => Dict{String,Any}(
        "tried" => false,
        "used" => false,
        "reason" => "not used: this diagnostic is fenced to JAX plus Julia and no torch",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "JSON" => "supportive",
    "JAX peer" => "load_bearing",
    "numpy" => nothing,
    "pytorch" => nothing,
)

const SIM_TEMPLATE_SURFACE = Dict{String,Any}(
    "identity" => ["sim_id", "name", "version", "tier"],
    "tooling" => ["TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH", "classification"],
    "negatives" => ["positive", "negative", "boundary", "probe"],
    "promotion" => ["promotion_allowed", "formal_admission_allowed", "blocked_consumers"],
)

const I2 = ComplexF64[1 0; 0 1]

rounded(value::Real, digits::Int = 12) = round(Float64(value); digits = digits)

function matrix_parts(matrix::Matrix{ComplexF64}, digits::Int = 12)
    Dict{String,Any}(
        "real" => [[round(Float64(cell); digits = digits) for cell in row] for row in eachrow(real.(matrix))],
        "imag" => [[round(Float64(cell); digits = digits) for cell in row] for row in eachrow(imag.(matrix))],
    )
end

function ket(values::Vector{ComplexF64})
    vec = copy(values)
    vec ./ sqrt(real(dot(vec, vec)))
end

density(psi::Vector{ComplexF64}) = psi * psi'

function make_projective_probe(name::String, vectors::Vector{Vector{ComplexF64}})
    Dict{String,Any}(
        "name" => name,
        "outcome_labels" => ["$(name)_$(idx - 1)" for idx in eachindex(vectors)],
        "effects" => [density(vec) for vec in vectors],
    )
end

function make_blind_probe()
    Dict{String,Any}(
        "name" => "BLIND_I",
        "outcome_labels" => ["BLIND_I_0"],
        "effects" => Matrix{ComplexF64}[I2],
    )
end

function base_kets()
    s2 = sqrt(2.0)
    Dict{String,Vector{ComplexF64}}(
        "z0" => ket(ComplexF64[1 + 0im, 0 + 0im]),
        "z1" => ket(ComplexF64[0 + 0im, 1 + 0im]),
        "x_plus" => ket(ComplexF64[1 + 0im, 1 + 0im]),
        "x_minus" => ket(ComplexF64[1 + 0im, -1 + 0im]),
        "y_plus" => ComplexF64[1 + 0im, 0 + 1im] ./ s2,
        "y_minus" => ComplexF64[1 + 0im, 0 - 1im] ./ s2,
    )
end

function probe_family()
    ks = base_kets()
    Dict{String,Any}(
        "Z" => make_projective_probe("Z", [ks["z0"], ks["z1"]]),
        "X" => make_projective_probe("X", [ks["x_plus"], ks["x_minus"]]),
        "Y" => make_projective_probe("Y", [ks["y_plus"], ks["y_minus"]]),
        "BLIND_I" => make_blind_probe(),
    )
end

function candidate_configurations()
    ks = base_kets()
    rhos = Dict{String,Matrix{ComplexF64}}(name => density(vec) for (name, vec) in ks)
    mixed_z = 0.5 .* rhos["z0"] .+ 0.5 .* rhos["z1"]
    mixed_x = 0.5 .* rhos["x_plus"] .+ 0.5 .* rhos["x_minus"]
    [
        Dict{String,Any}("id" => "pure_z0", "description" => "pure finite support state z0", "rho" => rhos["z0"]),
        Dict{String,Any}("id" => "pure_z1", "description" => "pure finite support state z1", "rho" => rhos["z1"]),
        Dict{String,Any}("id" => "pure_x_plus", "description" => "pure finite support state x_plus", "rho" => rhos["x_plus"]),
        Dict{String,Any}("id" => "pure_x_minus", "description" => "pure finite support state x_minus", "rho" => rhos["x_minus"]),
        Dict{String,Any}("id" => "pure_y_plus", "description" => "pure finite support state y_plus", "rho" => rhos["y_plus"]),
        Dict{String,Any}("id" => "pure_y_minus", "description" => "pure finite support state y_minus", "rho" => rhos["y_minus"]),
        Dict{String,Any}("id" => "ensemble_z_mixed", "description" => "50/50 ensemble over z states", "rho" => mixed_z),
        Dict{String,Any}("id" => "ensemble_x_mixed", "description" => "50/50 ensemble over x states", "rho" => mixed_x),
    ]
end

function measurement_stats(rho::Matrix{ComplexF64}, probe::Dict{String,Any})
    [rounded(real(tr(effect * rho)), 12) for effect in probe["effects"]]
end

function signature(candidate::Dict{String,Any}, probes::Vector{Dict{String,Any}})
    [measurement_stats(candidate["rho"], probe) for probe in probes]
end

function quotient(candidates::Vector{Dict{String,Any}}, probes::Vector{Dict{String,Any}}, name::String)
    classes = Dict{String,Dict{String,Any}}()
    for candidate in candidates
        sig = signature(candidate, probes)
        key = JSON.json(sig)
        if !haskey(classes, key)
            classes[key] = Dict{String,Any}("members" => String[], "signature" => sig)
        end
        push!(classes[key]["members"], String(candidate["id"]))
    end
    ordered = Vector{Dict{String,Any}}()
    for (idx, key) in enumerate(sort(collect(keys(classes))))
        push!(ordered, Dict{String,Any}(
            "class_id" => "$(name)_q$(idx - 1)",
            "members" => sort(classes[key]["members"]),
            "signature" => classes[key]["signature"],
            "size" => length(classes[key]["members"]),
        ))
    end
    assigned = sort([member for cls in ordered for member in cls["members"]])
    Dict{String,Any}(
        "name" => name,
        "probe_names" => [String(probe["name"]) for probe in probes],
        "class_count" => length(ordered),
        "classes" => ordered,
        "partition_member_ids" => assigned,
    )
end

function shannon_entropy(probabilities::Vector{Float64})
    total = 0.0
    for value in probabilities
        if value > TOL
            total -= value * log(value)
        end
    end
    rounded(total, 15)
end

function von_neumann_entropy(rho::Matrix{ComplexF64})
    eigenvalues = real.(eigvals(Hermitian(rho)))
    total = 0.0
    for value in eigenvalues
        if value > TOL
            total -= value * log(value)
        end
    end
    rounded(total, 15)
end

function quotient_ok(candidates::Vector{Dict{String,Any}}, q::Dict{String,Any})
    ids = sort([String(candidate["id"]) for candidate in candidates])
    class_ids = [String(cls["class_id"]) for cls in q["classes"]]
    ids == q["partition_member_ids"] &&
        q["class_count"] == length(q["classes"]) &&
        length(Set(class_ids)) == length(class_ids)
end

function entropy_readout(candidates::Vector{Dict{String,Any}}, probes::Vector{Dict{String,Any}}, name::String)
    q = quotient(candidates, probes, name)
    candidates_by_id = Dict{String,Dict{String,Any}}(String(candidate["id"]) => candidate for candidate in candidates)
    class_probabilities = [Float64(cls["size"]) / length(candidates) for cls in q["classes"]]
    class_rows = Any[]
    class_mean_vn_values = Float64[]
    class_probe_entropy_values = Float64[]
    for cls in q["classes"]
        vn_values = [von_neumann_entropy(candidates_by_id[String(member)]["rho"]) for member in cls["members"]]
        signature_entropies = [shannon_entropy(Float64.(row)) for row in cls["signature"]]
        mean_vn = sum(vn_values) / length(vn_values)
        mean_probe_entropy = isempty(signature_entropies) ? 0.0 : sum(signature_entropies) / length(signature_entropies)
        push!(class_mean_vn_values, mean_vn)
        push!(class_probe_entropy_values, mean_probe_entropy)
        push!(class_rows, Dict{String,Any}(
            "class_id" => cls["class_id"],
            "members" => cls["members"],
            "size" => cls["size"],
            "prior_probability" => Float64(cls["size"]) / length(candidates),
            "signature" => cls["signature"],
            "signature_shannon_entropies" => signature_entropies,
            "mean_probe_outcome_shannon_entropy" => mean_probe_entropy,
            "member_von_neumann_entropies" => Dict(zip(cls["members"], vn_values)),
            "mean_von_neumann_entropy" => mean_vn,
        ))
    end
    class_vn_range = maximum(class_mean_vn_values) - minimum(class_mean_vn_values)
    class_probe_entropy_range = isempty(class_probe_entropy_values) ? 0.0 : maximum(class_probe_entropy_values) - minimum(class_probe_entropy_values)
    Dict{String,Any}(
        "name" => name,
        "probe_names" => [String(probe["name"]) for probe in probes],
        "quotient" => q,
        "class_probability_distribution" => class_probabilities,
        "quotient_class_shannon_entropy" => shannon_entropy(class_probabilities),
        "class_rows" => class_rows,
        "unweighted_mean_class_von_neumann_entropy" => sum(class_mean_vn_values) / length(class_mean_vn_values),
        "unweighted_mean_class_probe_outcome_shannon_entropy" => isempty(class_probe_entropy_values) ? 0.0 : sum(class_probe_entropy_values) / length(class_probe_entropy_values),
        "class_mean_von_neumann_entropy_range" => class_vn_range,
        "class_probe_outcome_entropy_range" => class_probe_entropy_range,
        "entropy_signature" => Float64[
            Float64(q["class_count"]),
            shannon_entropy(class_probabilities),
            class_vn_range,
            class_probe_entropy_range,
        ],
    )
end

l1_gap(left::Vector{Float64}, right::Vector{Float64}) = sum(abs(a - b) for (a, b) in zip(left, right))

function read_parent_receipts()
    rows = Any[]
    for path in PARENT_RESULTS
        exists = isfile(path)
        data = exists ? JSON.parsefile(path) : Dict{String,Any}()
        push!(rows, Dict{String,Any}(
            "path" => path,
            "exists" => exists,
            "classification" => get(data, "classification", nothing),
            "all_pass" => get(data, "all_pass", nothing),
            "promotion_allowed" => get(data, "promotion_allowed", nothing),
            "formal_admission_allowed" => get(data, "formal_admission_allowed", nothing),
            "parity" => get(get(data, "parity", Dict{String,Any}()), "within_1e_12", nothing),
        ))
    end
    Dict{String,Any}(
        "rows" => rows,
        "pass" => all(
            Bool(row["exists"]) &&
                row["classification"] == "scratch_diagnostic" &&
                row["all_pass"] == true &&
                row["promotion_allowed"] == false &&
                row["formal_admission_allowed"] == false
            for row in rows
        ),
    )
end

function no_self_diff_tautologies(control_pairs::Vector{Dict{String,String}})
    all(
        row["left_expression_id"] != row["right_expression_id"] &&
            row["left_quantity_id"] != row["right_quantity_id"]
        for row in control_pairs
    )
end

function parity_against_jax(result::Dict{String,Any}, jax_data, jax_reference_path::String)
    max_diff = 0.0
    rows = Any[]
    missing = String[]
    for (key, value) in result["shared_scalars"]
        peer_scalars = get(jax_data, "shared_scalars", Dict{String,Any}())
        if !haskey(peer_scalars, key)
            push!(missing, key)
            continue
        end
        diff = abs(Float64(value) - Float64(peer_scalars[key]))
        max_diff = max(max_diff, diff)
        push!(rows, Dict{String,Any}("key" => key, "julia" => Float64(value), "jax" => Float64(peer_scalars[key]), "abs_diff" => diff))
    end
    boolean_mismatches = Any[]
    for (key, value) in result["shared_booleans"]
        peer_booleans = get(jax_data, "shared_booleans", Dict{String,Any}())
        if !haskey(peer_booleans, key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer_booleans[key])
            push!(boolean_mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => Bool(peer_booleans[key])))
        end
    end
    string_mismatches = Any[]
    for (key, value) in result["shared_strings"]
        peer_strings = get(jax_data, "shared_strings", Dict{String,Any}())
        if !haskey(peer_strings, key)
            push!(missing, key)
            continue
        end
        if string(value) != string(peer_strings[key])
            push!(string_mismatches, Dict{String,Any}("key" => key, "julia" => string(value), "jax" => string(peer_strings[key])))
        end
    end
    within_run = get(jax_data, "within_run_id", "")
    Dict{String,Any}(
        "peer_result_path" => jax_reference_path,
        "status" => "compared",
        "within_1e_12" => max_diff <= TOL && isempty(boolean_mismatches) && isempty(string_mismatches) && isempty(missing),
        "parity_max_diff" => max_diff,
        "numeric_rows" => rows,
        "boolean_mismatches" => boolean_mismatches,
        "string_mismatches" => string_mismatches,
        "missing_keys" => missing,
        "parity_within_run" => result["jax_reference_within_run_id"] == within_run && result["jax_reference_path"] == jax_reference_path,
    )
end

function build_result(jax_reference_path::String, result_path::String)
    jax_data = isfile(jax_reference_path) ? JSON.parsefile(jax_reference_path) : Dict{String,Any}()
    probes_by_name = probe_family()
    candidates = candidate_configurations()
    m_empty = Dict{String,Any}[]
    m_blind = Dict{String,Any}[probes_by_name["BLIND_I"]]
    m_coarse = Dict{String,Any}[probes_by_name["Z"]]
    m_fine = Dict{String,Any}[probes_by_name["Z"], probes_by_name["X"], probes_by_name["Y"]]

    readouts = Dict{String,Any}(
        "M_empty" => entropy_readout(candidates, m_empty, "M_empty"),
        "M_blind" => entropy_readout(candidates, m_blind, "M_blind"),
        "M_Z" => entropy_readout(candidates, m_coarse, "M_Z"),
        "M_ZXY" => entropy_readout(candidates, m_fine, "M_ZXY"),
    )
    parents = read_parent_receipts()

    positive_resolution_gap = l1_gap(readouts["M_Z"]["entropy_signature"], readouts["M_ZXY"]["entropy_signature"])
    negative_resolution_gap = l1_gap(readouts["M_empty"]["entropy_signature"], readouts["M_blind"]["entropy_signature"])
    positive_negative_signature_gap = l1_gap(readouts["M_ZXY"]["entropy_signature"], readouts["M_blind"]["entropy_signature"])
    quotient_entropy_resolution_delta = readouts["M_ZXY"]["quotient_class_shannon_entropy"] - readouts["M_Z"]["quotient_class_shannon_entropy"]
    vn_entropy_range = readouts["M_ZXY"]["class_mean_von_neumann_entropy_range"]

    entropy_covaries_with_resolution =
        readouts["M_Z"]["quotient"]["class_count"] < readouts["M_ZXY"]["quotient"]["class_count"] &&
        quotient_entropy_resolution_delta > TOL &&
        positive_resolution_gap > TOL
    negative_case_positive_control_fails =
        readouts["M_empty"]["quotient"]["class_count"] == 1 &&
        readouts["M_blind"]["quotient"]["class_count"] == 1 &&
        negative_resolution_gap <= TOL
    trivial_quotient_entropy_degenerate =
        readouts["M_empty"]["quotient_class_shannon_entropy"] <= TOL &&
        readouts["M_blind"]["quotient_class_shannon_entropy"] <= TOL &&
        readouts["M_empty"]["class_mean_von_neumann_entropy_range"] <= TOL &&
        readouts["M_blind"]["class_mean_von_neumann_entropy_range"] <= TOL &&
        readouts["M_blind"]["unweighted_mean_class_probe_outcome_shannon_entropy"] <= TOL
    positive_negative_entropy_signature_distinct = positive_negative_signature_gap > TOL
    entropy_is_readout_not_primitive =
        Bool(parents["pass"]) &&
        entropy_covaries_with_resolution &&
        positive_negative_entropy_signature_distinct &&
        trivial_quotient_entropy_degenerate
    all_quotients_built = all(quotient_ok(candidates, row["quotient"]) for row in values(readouts))

    control_pairs = Dict{String,String}[
        Dict(
            "name" => "positive_resolution_covariance",
            "left_expression_id" => "entropy_signature(M_Z)",
            "right_expression_id" => "entropy_signature(M_ZXY)",
            "left_quantity_id" => "M_Z_entropy_signature",
            "right_quantity_id" => "M_ZXY_entropy_signature",
        ),
        Dict(
            "name" => "negative_no_distinguishability_fails_covariance",
            "left_expression_id" => "entropy_signature(M_empty)",
            "right_expression_id" => "entropy_signature(M_blind)",
            "left_quantity_id" => "M_empty_entropy_signature",
            "right_quantity_id" => "M_blind_entropy_signature",
        ),
        Dict(
            "name" => "positive_vs_negative_signature",
            "left_expression_id" => "entropy_signature(M_ZXY)",
            "right_expression_id" => "entropy_signature(M_blind)",
            "left_quantity_id" => "M_ZXY_entropy_signature",
            "right_quantity_id" => "M_blind_entropy_signature",
        ),
    ]
    no_self_diff = no_self_diff_tautologies(control_pairs)

    shared_scalars = Dict{String,Any}(
        "S_size" => Float64(length(candidates)),
        "M_empty_class_count" => Float64(readouts["M_empty"]["quotient"]["class_count"]),
        "M_blind_class_count" => Float64(readouts["M_blind"]["quotient"]["class_count"]),
        "M_Z_class_count" => Float64(readouts["M_Z"]["quotient"]["class_count"]),
        "M_ZXY_class_count" => Float64(readouts["M_ZXY"]["quotient"]["class_count"]),
        "M_empty_quotient_shannon_entropy" => Float64(readouts["M_empty"]["quotient_class_shannon_entropy"]),
        "M_blind_quotient_shannon_entropy" => Float64(readouts["M_blind"]["quotient_class_shannon_entropy"]),
        "M_Z_quotient_shannon_entropy" => Float64(readouts["M_Z"]["quotient_class_shannon_entropy"]),
        "M_ZXY_quotient_shannon_entropy" => Float64(readouts["M_ZXY"]["quotient_class_shannon_entropy"]),
        "quotient_entropy_resolution_delta" => Float64(quotient_entropy_resolution_delta),
        "positive_resolution_signature_l1_gap" => Float64(positive_resolution_gap),
        "negative_resolution_signature_l1_gap" => Float64(negative_resolution_gap),
        "positive_negative_entropy_signature_l1_gap" => Float64(positive_negative_signature_gap),
        "M_ZXY_class_mean_vn_entropy_range" => Float64(vn_entropy_range),
        "M_ZXY_class_probe_outcome_entropy_range" => Float64(readouts["M_ZXY"]["class_probe_outcome_entropy_range"]),
        "M_blind_mean_class_probe_outcome_shannon_entropy" => Float64(readouts["M_blind"]["unweighted_mean_class_probe_outcome_shannon_entropy"]),
    )
    shared_booleans = Dict{String,Any}(
        "parent_receipts_verified" => Bool(parents["pass"]),
        "all_quotients_built" => all_quotients_built,
        "entropy_is_readout_not_primitive" => entropy_is_readout_not_primitive,
        "entropy_covaries_with_resolution" => entropy_covaries_with_resolution,
        "negative_case_positive_control_fails" => negative_case_positive_control_fails,
        "trivial_quotient_entropy_degenerate" => trivial_quotient_entropy_degenerate,
        "positive_negative_entropy_signature_distinct" => positive_negative_entropy_signature_distinct,
        "no_self_diff_tautologies" => no_self_diff,
        "classification_is_scratch_diagnostic" => CLASSIFICATION == "scratch_diagnostic",
        "promotion_false" => PROMOTION_ALLOWED == false,
        "formal_admission_false" => FORMAL_ADMISSION_ALLOWED == false,
        "jax_enable_x64" => get(jax_data, "jax_enable_x64", false) == true,
        "numpy_compute_used" => false,
        "torch_compute_used" => false,
    )
    shared_strings = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "allowed_claim" => ALLOWED_CLAIM,
        "claim_ceiling" => get(jax_data, "claim_ceiling", CLAIM_CEILING),
        "entropy_placement" => "downstream_of_probe_relative_distinguishability_quotient",
    )

    generated_at = string(Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS"), "Z")
    result = Dict{String,Any}(
        "schema" => "codex_ratchet.julia_carrier.scratch_diagnostic.v1",
        "object_id" => OBJECT_ID,
        "sim_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "version" => "1.0",
        "tier" => "R3_entropy_as_derived_readout",
        "backend" => "julia",
        "within_run_id" => string(uuid4()),
        "generated_at" => generated_at,
        "source_path" => @__FILE__,
        "result_path" => result_path,
        "jax_reference_path" => jax_reference_path,
        "jax_reference_within_run_id" => get(jax_data, "within_run_id", ""),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "allowed_claims" => [ALLOWED_CLAIM],
        "blocked_claims" => BLOCKED_CLAIMS,
        "claim_ceiling" => get(jax_data, "claim_ceiling", CLAIM_CEILING),
        "promotion_status" => "diagnostic_only",
        "eligible_consumers" => [],
        "blocked_consumers" => BLOCKED_CLAIMS,
        "sim_execution_kind" => SIM_EXECUTION_KIND,
        "sim_class" => "constraint_probe",
        "purpose" => "Julia recomputation of entropy only after the finite R2 distinguishability quotient exists.",
        "root_constraints_in_force" => ["F01", "N01", "R2_probe_relative_distinguishability_quotient"],
        "SIM_TEMPLATE_surface" => SIM_TEMPLATE_SURFACE,
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "required_tools" => ["Julia", "LinearAlgebra", "JAX peer"],
        "actual_tools_used" => ["Julia", "LinearAlgebra", "JSON", "JAX peer"],
        "numpy_compute_used" => false,
        "numpy_imported" => false,
        "torch_compute_used" => false,
        "torch_imported" => false,
        "verified_parent_receipts" => parents,
        "finite_support_set_S" => Dict{String,Any}(
            "size" => length(candidates),
            "candidate_ids" => [candidate["id"] for candidate in candidates],
            "rho_matrices" => Dict(candidate["id"] => matrix_parts(candidate["rho"]) for candidate in candidates),
        ),
        "probe_families_M" => Dict{String,Any}(
            "M_empty" => [],
            "M_blind" => ["BLIND_I"],
            "M_Z" => ["Z"],
            "M_ZXY" => ["Z", "X", "Y"],
        ),
        "entropy_definitions" => Dict{String,Any}(
            "von_neumann" => "S(rho) = -tr(rho log rho), computed from density eigenvalues after quotient state data exists",
            "shannon_probe_outcome" => "H(p_M) = -sum p_i log p_i over finite probe-outcome rows",
            "shannon_quotient_class" => "H(S/~_M) over uniform candidate prior pushed through the quotient classes",
            "placement" => "all entropy fields consume quotient/signature/density data; no entropy value defines identity or admissibility",
        ),
        "entropy_readouts" => readouts,
        "controls" => Dict{String,Any}(
            "resolution_covariance_positive" => Dict{String,Any}(
                "pass" => entropy_covaries_with_resolution,
                "left_probe_family" => "M_Z",
                "right_probe_family" => "M_ZXY",
                "left_entropy_signature" => readouts["M_Z"]["entropy_signature"],
                "right_entropy_signature" => readouts["M_ZXY"]["entropy_signature"],
                "entropy_signature_l1_gap" => positive_resolution_gap,
                "quotient_entropy_delta" => quotient_entropy_resolution_delta,
            ),
            "no_distinguishability_negative_fails_positive_control" => Dict{String,Any}(
                "pass" => negative_case_positive_control_fails,
                "positive_predicate_passes" => false,
                "left_probe_family" => "M_empty",
                "right_probe_family" => "M_blind",
                "families_are_distinct" => true,
                "left_entropy_signature" => readouts["M_empty"]["entropy_signature"],
                "right_entropy_signature" => readouts["M_blind"]["entropy_signature"],
                "entropy_signature_l1_gap" => negative_resolution_gap,
            ),
            "trivial_quotient_entropy_degenerate" => Dict{String,Any}(
                "pass" => trivial_quotient_entropy_degenerate,
                "M_empty_class_count" => readouts["M_empty"]["quotient"]["class_count"],
                "M_blind_class_count" => readouts["M_blind"]["quotient"]["class_count"],
            ),
            "positive_negative_entropy_signature_distinct" => Dict{String,Any}(
                "pass" => positive_negative_entropy_signature_distinct,
                "entropy_signature_l1_gap" => positive_negative_signature_gap,
            ),
            "no_self_diff_tautologies" => Dict{String,Any}(
                "pass" => no_self_diff,
                "control_expression_pairs" => control_pairs,
            ),
        ),
        "probe" => Dict{String,Any}(
            "primitive" => "probe-relative distinguishability quotient S/~_M",
            "downstream_readout" => "entropy computed only from quotient class distribution, class density rows, and probe-outcome signatures",
            "readout_order" => ["finite S", "finite M", "quotient S/~_M", "entropy readout"],
            "positive_family_pair" => ["M_Z", "M_ZXY"],
            "negative_family_pair" => ["M_empty", "M_blind"],
        ),
        "positive" => Dict{String,Any}(
            "parent_receipts_verified" => Dict("pass" => Bool(parents["pass"])),
            "all_quotients_built" => Dict("pass" => all_quotients_built),
            "entropy_covaries_with_resolution" => Dict("pass" => entropy_covaries_with_resolution),
            "entropy_is_readout_not_primitive" => Dict("pass" => entropy_is_readout_not_primitive),
            "positive_negative_entropy_signature_distinct" => Dict("pass" => positive_negative_entropy_signature_distinct),
            "no_self_diff_tautologies" => Dict("pass" => no_self_diff),
        ),
        "negative" => Dict{String,Any}(
            "no_distinguishability_positive_control_fails" => Dict{String,Any}(
                "pass" => negative_case_positive_control_fails,
                "positive_predicate_passes" => false,
                "left_quantity" => "entropy_signature(M_empty)",
                "right_quantity" => "entropy_signature(M_blind)",
                "entropy_signature_l1_gap" => negative_resolution_gap,
            ),
            "trivial_quotient_entropy_degenerate" => Dict{String,Any}(
                "pass" => trivial_quotient_entropy_degenerate,
                "reason" => "one quotient class and no nonzero quotient/probe-outcome entropy in the no-distinguishability controls",
            ),
        ),
        "boundary" => Dict{String,Any}(
            "classification_is_scratch_diagnostic" => Dict("pass" => CLASSIFICATION == "scratch_diagnostic"),
            "promotion_allowed_false" => Dict("pass" => PROMOTION_ALLOWED == false),
            "formal_admission_allowed_false" => Dict("pass" => FORMAL_ADMISSION_ALLOWED == false),
            "claim_ceiling_present" => Dict("pass" => !isempty(CLAIM_CEILING)),
            "blind_probe_is_distinct_from_empty_probe" => Dict(
                "pass" => length(m_blind) != length(m_empty) && readouts["M_blind"]["quotient"]["class_count"] == 1,
            ),
        ),
        "why_not_v4_probes" => "This is a v5 scratch diagnostic bottom-up formal-scout receipt with no promotion or formal admission.",
        "required_negatives" => ["no_distinguishability_positive_control_fails", "trivial_quotient_entropy_degenerate"],
        "negatives_run" => ["no_distinguishability_positive_control_fails", "trivial_quotient_entropy_degenerate"],
        "required_artifacts" => [jax_reference_path, result_path],
        "artifacts_emitted" => [result_path],
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "shared_strings" => shared_strings,
        "result_summary" => Dict{String,Any}(
            "entropy_is_readout_not_primitive" => entropy_is_readout_not_primitive,
            "entropy_covaries_with_resolution" => entropy_covaries_with_resolution,
            "trivial_quotient_entropy_degenerate" => trivial_quotient_entropy_degenerate,
            "no_self_diff_tautologies" => no_self_diff,
            "vn_entropy_range" => @sprintf("%.12g", vn_entropy_range),
            "all_pass" => false,
        ),
    )
    parity = parity_against_jax(result, jax_data, jax_reference_path)
    result["parity"] = parity
    result["positive"]["dual_backend_parity"] = Dict("pass" => parity["within_1e_12"])
    result["positive"]["parity_within_run"] = Dict("pass" => parity["parity_within_run"])
    required = [
        Bool(shared_booleans["parent_receipts_verified"]),
        Bool(shared_booleans["all_quotients_built"]),
        Bool(shared_booleans["entropy_is_readout_not_primitive"]),
        Bool(shared_booleans["entropy_covaries_with_resolution"]),
        Bool(shared_booleans["negative_case_positive_control_fails"]),
        Bool(shared_booleans["trivial_quotient_entropy_degenerate"]),
        Bool(shared_booleans["positive_negative_entropy_signature_distinct"]),
        Bool(shared_booleans["no_self_diff_tautologies"]),
        Bool(parity["within_1e_12"]),
        Bool(parity["parity_within_run"]),
        CLASSIFICATION == "scratch_diagnostic",
        PROMOTION_ALLOWED == false,
        FORMAL_ADMISSION_ALLOWED == false,
    ]
    result["all_pass"] = all(required)
    result["stop_condition_fired"] = !Bool(result["all_pass"])
    result["result_summary"]["all_pass"] = result["all_pass"]
    result["result_summary"]["parity_with_jax"] = parity["within_1e_12"]
    result["result_summary"]["parity_within_run"] = parity["parity_within_run"]
    result
end

function main()
    jax_reference_path = length(ARGS) >= 1 ? ARGS[1] : DEFAULT_JAX_REFERENCE_PATH
    result_path = length(ARGS) >= 2 ? ARGS[2] : DEFAULT_RESULT_PATH
    result = build_result(jax_reference_path, result_path)
    mkpath(dirname(result_path))
    open(result_path, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println("wrote $(result_path)")
    println(JSON.json(Dict(
        "all_pass" => result["all_pass"],
        "parity" => result["parity"]["within_1e_12"],
        "parity_within_run" => result["parity"]["parity_within_run"],
        "entropy_is_readout_not_primitive" => result["shared_booleans"]["entropy_is_readout_not_primitive"],
        "entropy_covaries_with_resolution" => result["shared_booleans"]["entropy_covaries_with_resolution"],
        "trivial_quotient_entropy_degenerate" => result["shared_booleans"]["trivial_quotient_entropy_degenerate"],
        "no_self_diff_tautologies" => result["shared_booleans"]["no_self_diff_tautologies"],
        "vn_entropy_range" => result["result_summary"]["vn_entropy_range"],
    )))
    return result["all_pass"] ? 0 : 1
end

exit(main())
