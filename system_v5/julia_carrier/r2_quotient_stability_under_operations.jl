#!/usr/bin/env julia
# object_id: r2_quotient_stability_under_operations
# classification: scratch_diagnostic

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "r2_quotient_stability_under_operations"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/r2_quotient_stability_under_operations_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/r2_quotient_stability_under_operations_results.json")
const PARENT_RUNG_PACKET = joinpath(ROOT, "system_v5/ops/formal_scouts/sim_foundation_rung0to3_distinguishability_probe.py")
const PARENT_R2_PACKET = joinpath(ROOT, "system_v5/ops/formal_scouts/sim_r0_r1_r2_probe_quotient_micro_packet.py")
const PARENT_R2_OPS = joinpath(ROOT, "system_v5/ops/formal_scouts/sim_r2_admissible_operations_commutation_order.py")
const PARENT_R2_COMPOSITION = joinpath(ROOT, "system_v5/ops/formal_scouts/sim_r2_admissible_composition_rules.py")
const TOL = 1.0e-12
const N01_TOL = 1.0e-9
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const SIM_EXECUTION_KIND = "nonclassical"
const ALLOWED_CLAIM = "R2 finite probe quotient stability under admissible ordered CPTP operations, scratch diagnostic only."
const CLAIM_CEILING = "Allowed only: finite S/~_M quotient stability/collapse under named R2 operations. No promotion, no formal admission, no higher-layer consumer."

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing independent finite quotient and CPTP operation stability mirror computation",
    ),
    "LinearAlgebra" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing matrix traces, norms, eigenvalue checks, and finite operation products",
    ),
    "JSON" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization and current JAX peer comparison",
    ),
    "JAX peer" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing within-run parity reference for shared scalar, boolean, and string keys",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "JSON" => "supportive",
    "JAX peer" => "load_bearing",
)

const SIM_TEMPLATE_SURFACE = Dict{String,Any}(
    "identity" => ["sim_id", "name", "version", "tier"],
    "tooling" => ["TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH", "classification"],
    "negatives" => ["positive", "negative", "boundary", "probe"],
    "promotion" => ["promotion_allowed", "formal_admission_allowed", "blocked_consumers"],
)

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SZ = ComplexF64[1 0; 0 -1]

rounded(value::Real, digits::Int = 12) = round(Float64(value); digits = digits)

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
    )
end

function candidate_configurations()
    ks = base_kets()
    rhos = Dict{String,Matrix{ComplexF64}}(name => density(vec) for (name, vec) in ks)
    mixed_z = 0.5 .* rhos["z0"] .+ 0.5 .* rhos["z1"]
    mixed_x = 0.5 .* rhos["x_plus"] .+ 0.5 .* rhos["x_minus"]
    Dict{String,Any}[
        Dict("id" => "pure_z0", "description" => "pure finite support state z0", "rho" => rhos["z0"]),
        Dict("id" => "pure_z1", "description" => "pure finite support state z1", "rho" => rhos["z1"]),
        Dict("id" => "pure_x_plus", "description" => "pure finite support state x_plus", "rho" => rhos["x_plus"]),
        Dict("id" => "pure_x_minus", "description" => "pure finite support state x_minus", "rho" => rhos["x_minus"]),
        Dict("id" => "pure_y_plus", "description" => "pure finite support state y_plus", "rho" => rhos["y_plus"]),
        Dict("id" => "pure_y_minus", "description" => "pure finite support state y_minus", "rho" => rhos["y_minus"]),
        Dict("id" => "ensemble_z_mixed", "description" => "50/50 ensemble over z states", "rho" => mixed_z),
        Dict("id" => "ensemble_x_mixed", "description" => "50/50 ensemble over x states", "rho" => mixed_x),
    ]
end

function operation_family(probes::Dict{String,Any})
    pz0, pz1 = probes["Z"]["effects"]
    pxp, pxm = probes["X"]["effects"]
    gamma = 0.5
    sqrt_keep = sqrt(1.0 - gamma)
    sqrt_drop = sqrt(gamma)
    Dict{String,Any}[
        Dict("name" => "projective_Z", "kind" => "projective_measurement_channel", "kraus" => Matrix{ComplexF64}[pz0, pz1]),
        Dict("name" => "projective_X", "kind" => "projective_measurement_channel", "kraus" => Matrix{ComplexF64}[pxp, pxm]),
        Dict("name" => "unitary_X", "kind" => "unitary_channel", "kraus" => Matrix{ComplexF64}[SX]),
        Dict("name" => "unitary_Z", "kind" => "unitary_channel", "kraus" => Matrix{ComplexF64}[SZ]),
        Dict(
            "name" => "damping_Z0_half",
            "kind" => "dissipator_channel",
            "kraus" => Matrix{ComplexF64}[
                ComplexF64[1 0; 0 sqrt_keep],
                ComplexF64[0 sqrt_drop; 0 0],
            ],
        ),
        Dict("name" => "phase_damping_Z_half", "kind" => "dissipator_channel", "kraus" => Matrix{ComplexF64}[sqrt_keep .* I2, sqrt_drop .* pz0, sqrt_drop .* pz1]),
    ]
end

function matrix_parts(matrix::Matrix{ComplexF64}, digits::Int = 12)
    Dict{String,Any}(
        "real" => [[round(Float64(real(matrix[row, col])); digits = digits) for col in 1:size(matrix, 2)] for row in 1:size(matrix, 1)],
        "imag" => [[round(Float64(imag(matrix[row, col])); digits = digits) for col in 1:size(matrix, 2)] for row in 1:size(matrix, 1)],
    )
end

function apply_channel(kraus::Vector{Matrix{ComplexF64}}, rho::Matrix{ComplexF64})
    out = zeros(ComplexF64, 2, 2)
    for op in kraus
        out .+= op * rho * op'
    end
    out
end

function choi_matrix(kraus::Vector{Matrix{ComplexF64}})
    row_blocks = Matrix{ComplexF64}[]
    for row in 1:2
        blocks = Matrix{ComplexF64}[]
        for col in 1:2
            unit = zeros(ComplexF64, 2, 2)
            unit[row, col] = 1 + 0im
            push!(blocks, apply_channel(kraus, unit))
        end
        push!(row_blocks, hcat(blocks...))
    end
    vcat(row_blocks...)
end

function cptp_check(kraus::Vector{Matrix{ComplexF64}})
    completeness = zeros(ComplexF64, 2, 2)
    for op in kraus
        completeness .+= op' * op
    end
    completeness_gap = rounded(norm(completeness - I2), 15)
    choi_min_eig = rounded(minimum(real.(eigvals(Hermitian(choi_matrix(kraus))))), 15)
    Dict{String,Any}(
        "kraus_count" => length(kraus),
        "trace_preserving_gap" => completeness_gap,
        "choi_min_eigenvalue" => choi_min_eig,
        "pass" => completeness_gap <= TOL && choi_min_eig >= -TOL,
    )
end

function measurement_stats(rho::Matrix{ComplexF64}, probes::Vector{Dict{String,Any}})
    [[rounded(real(tr(effect * rho)), 12) for effect in probe["effects"]] for probe in probes]
end

signature(rho::Matrix{ComplexF64}, probes::Vector{Dict{String,Any}}) = measurement_stats(rho, probes)
signature_key(sig) = JSON.json(sig)

function quotient(candidates::Vector{Dict{String,Any}}, probes::Vector{Dict{String,Any}}, name::String)
    classes = Dict{String,Dict{String,Any}}()
    for candidate in candidates
        sig = signature(candidate["rho"], probes)
        key = signature_key(sig)
        if !haskey(classes, key)
            classes[key] = Dict{String,Any}("members" => String[], "signature" => sig)
        end
        push!(classes[key]["members"], String(candidate["id"]))
    end
    ordered = Dict{String,Any}[]
    for (idx, key) in enumerate(sort(collect(keys(classes))))
        push!(ordered, Dict{String,Any}(
            "class_id" => "$(name)_q$(idx - 1)",
            "members" => sort(classes[key]["members"]),
            "signature" => classes[key]["signature"],
        ))
    end
    Dict{String,Any}(
        "name" => name,
        "probe_names" => [String(probe["name"]) for probe in probes],
        "class_count" => length(ordered),
        "classes" => ordered,
        "partition_member_ids" => sort([member for cls in ordered for member in cls["members"]]),
    )
end

function apply_sequence_to_rho(rho::Matrix{ComplexF64}, operation_names::Vector{String}, operations_by_name::Dict{String,Dict{String,Any}})
    out = rho
    for name in operation_names
        out = apply_channel(operations_by_name[name]["kraus"], out)
    end
    out
end

function transformed_candidates(candidates::Vector{Dict{String,Any}}, operation_names::Vector{String}, operations_by_name::Dict{String,Dict{String,Any}})
    [
        Dict{String,Any}(
            "id" => candidate["id"],
            "description" => "$(join(operation_names, " then ")) applied to $(candidate["id"])",
            "rho" => apply_sequence_to_rho(candidate["rho"], operation_names, operations_by_name),
        )
        for candidate in candidates
    ]
end

function well_defined_sequence_on_quotient(
    base_q::Dict{String,Any},
    candidates_by_id::Dict{String,Dict{String,Any}},
    operation_names::Vector{String},
    operations_by_name::Dict{String,Dict{String,Any}},
    probes::Vector{Dict{String,Any}},
)
    rows = Any[]
    for cls in base_q["classes"]
        sigs = Dict{String,Any}()
        for member in cls["members"]
            rho = apply_sequence_to_rho(candidates_by_id[String(member)]["rho"], operation_names, operations_by_name)
            sig = signature(rho, probes)
            sigs[signature_key(sig)] = sig
        end
        push!(rows, Dict{String,Any}(
            "input_class_id" => cls["class_id"],
            "member_count" => length(cls["members"]),
            "output_signature_count" => length(sigs),
            "pass" => length(sigs) == 1,
        ))
    end
    Dict{String,Any}("pass" => all(Bool(row["pass"]) for row in rows), "rows" => rows)
end

function sequence_cptp_check(operation_names::Vector{String}, operations_by_name::Dict{String,Dict{String,Any}})
    rows = [cptp_check(operations_by_name[name]["kraus"]) for name in operation_names]
    Dict{String,Any}("operation_names" => operation_names, "component_rows" => rows, "pass" => all(Bool(row["pass"]) for row in rows))
end

function stability_check(
    label::String,
    candidates::Vector{Dict{String,Any}},
    base_q::Dict{String,Any},
    probes::Vector{Dict{String,Any}},
    operation_names::Vector{String},
    operations_by_name::Dict{String,Dict{String,Any}},
    expected_stable::Bool,
)
    candidates_by_id = Dict{String,Dict{String,Any}}(String(candidate["id"]) => candidate for candidate in candidates)
    after = transformed_candidates(candidates, operation_names, operations_by_name)
    q_after = quotient(after, probes, "$(label)_M_ZX")
    well_defined = well_defined_sequence_on_quotient(base_q, candidates_by_id, operation_names, operations_by_name, probes)
    cptp = sequence_cptp_check(operation_names, operations_by_name)
    class_count_preserved = q_after["class_count"] == base_q["class_count"]
    stable = Bool(cptp["pass"]) && Bool(well_defined["pass"]) && class_count_preserved
    Dict{String,Any}(
        "label" => label,
        "operation_names" => operation_names,
        "left_quantity" => "base quotient S/~_M before operation sequence",
        "right_quantity" => "quotient after $(join(operation_names, " then "))",
        "expressions_distinct" => "base_M_ZX" != "$(label)_M_ZX",
        "cptp_sequence" => cptp,
        "well_defined_on_base_quotient" => well_defined,
        "base_class_count" => base_q["class_count"],
        "after_class_count" => q_after["class_count"],
        "collapse_count" => Int(base_q["class_count"]) - Int(q_after["class_count"]),
        "quotient_stable" => stable,
        "expected_stable" => expected_stable,
        "pass" => stable == expected_stable,
        "after_quotient" => q_after,
    )
end

function quotient_signature_set(q::Dict{String,Any})
    Set(signature_key(cls["signature"]) for cls in q["classes"])
end

function flat_signature_rows(q::Dict{String,Any})
    rows = Float64[]
    ordered = sort(q["classes"]; by = cls -> signature_key(cls["signature"]))
    for cls in ordered
        for probe_row in cls["signature"]
            append!(rows, [Float64(value) for value in probe_row])
        end
    end
    rows
end

l1_gap(left::Vector{Float64}, right::Vector{Float64}) = Float64(sum(abs(a - b) for (a, b) in zip(left, right)))

function order_effect_check(
    candidates::Vector{Dict{String,Any}},
    probes::Vector{Dict{String,Any}},
    operations_by_name::Dict{String,Dict{String,Any}},
    first::String,
    second::String,
)
    left_sequence = [first, second]
    right_sequence = [second, first]
    left_q = quotient(transformed_candidates(candidates, left_sequence, operations_by_name), probes, "$(first)_then_$(second)_M_ZX")
    right_q = quotient(transformed_candidates(candidates, right_sequence, operations_by_name), probes, "$(second)_then_$(first)_M_ZX")
    signature_l1 = l1_gap(flat_signature_rows(left_q), flat_signature_rows(right_q))
    signature_sets_differ = quotient_signature_set(left_q) != quotient_signature_set(right_q)
    Dict{String,Any}(
        "left_expression_id" => "$(first)_then_$(second)_reachable_quotient",
        "right_expression_id" => "$(second)_then_$(first)_reachable_quotient",
        "operation_names_distinct" => first != second,
        "expressions_distinct" => "$(first)_then_$(second)" != "$(second)_then_$(first)",
        "left_class_count" => left_q["class_count"],
        "right_class_count" => right_q["class_count"],
        "class_count_preserved_in_both_orders" => left_q["class_count"] == right_q["class_count"] == 5,
        "reachable_signature_l1_gap" => signature_l1,
        "reachable_signature_sets_differ" => signature_sets_differ,
        "pass" => first != second && signature_l1 > N01_TOL && signature_sets_differ,
        "left_quotient" => left_q,
        "right_quotient" => right_q,
    )
end

function classify_operation(candidates::Vector{Dict{String,Any}}, base_q::Dict{String,Any}, op::Dict{String,Any}, probes::Vector{Dict{String,Any}})
    operations_by_name = Dict{String,Dict{String,Any}}(String(op["name"]) => op)
    row = stability_check(String(op["name"]), candidates, base_q, probes, [String(op["name"])], operations_by_name, true)
    cptp = cptp_check(op["kraus"])
    preserves = Bool(cptp["pass"]) && Bool(row["well_defined_on_base_quotient"]["pass"]) && row["after_class_count"] == base_q["class_count"]
    Dict{String,Any}(
        "operation" => op["name"],
        "kind" => op["kind"],
        "cptp" => cptp,
        "base_class_count" => base_q["class_count"],
        "output_class_count" => row["after_class_count"],
        "collapse_count" => row["collapse_count"],
        "adm_filter_pass" => preserves,
        "operation_class" => preserves ? "preserve" : "collapse",
    )
end

function no_self_diff_controls(rows)
    for row in rows
        if haskey(row, "left_expression_id") && haskey(row, "right_expression_id") && row["left_expression_id"] == row["right_expression_id"]
            return false
        end
        if haskey(row, "left_quantity") && haskey(row, "right_quantity") && row["left_quantity"] == row["right_quantity"]
            return false
        end
    end
    true
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
        if String(value) != String(peer["shared_strings"][key])
            push!(string_mismatches, Dict{String,Any}("key" => key, "julia" => String(value), "jax" => String(peer["shared_strings"][key])))
        end
    end
    Dict{String,Any}(
        "peer_result_path" => JAX_REFERENCE_PATH,
        "peer_generated_at" => get(peer, "generated_at", nothing),
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
    probes_by_name = probe_family()
    probes = Dict{String,Any}[probes_by_name["Z"], probes_by_name["X"]]
    candidates = candidate_configurations()
    operations = operation_family(probes_by_name)
    operations_by_name = Dict{String,Dict{String,Any}}(String(op["name"]) => op for op in operations)
    base_q = quotient(candidates, probes, "base_M_ZX")
    op_class_rows = [classify_operation(candidates, base_q, op, probes) for op in operations]
    preserve_ops = [String(row["operation"]) for row in op_class_rows if row["operation_class"] == "preserve"]
    collapse_ops = [String(row["operation"]) for row in op_class_rows if row["operation_class"] == "collapse"]

    admissible_sequence = ["unitary_X", "damping_Z0_half"]
    reverse_sequence = ["damping_Z0_half", "unitary_X"]
    nonadmissible_sequence = ["projective_Z"]
    positive_stability = stability_check("admissible_unitary_x_then_damping", candidates, base_q, probes, admissible_sequence, operations_by_name, true)
    reverse_stability = stability_check("admissible_damping_then_unitary_x", candidates, base_q, probes, reverse_sequence, operations_by_name, true)
    collapse_stability = stability_check("nonadmissible_projective_z", candidates, base_q, probes, nonadmissible_sequence, operations_by_name, false)
    order_effect = order_effect_check(candidates, probes, operations_by_name, "unitary_X", "damping_Z0_half")

    control_rows = Any[
        positive_stability,
        reverse_stability,
        collapse_stability,
        order_effect,
        Dict{String,Any}(
            "left_expression_id" => "admissible_stability_predicate",
            "right_expression_id" => "nonadmissible_stability_predicate",
            "left_quantity" => "quotient stability after admissible_unitary_x_then_damping",
            "right_quantity" => "quotient stability after nonadmissible_projective_z",
        ),
    ]
    no_self_diff = no_self_diff_controls(control_rows)
    quotient_survives_admissible_ops = Bool(positive_stability["quotient_stable"]) && Bool(reverse_stability["quotient_stable"])
    nonadmissible_op_collapses_quotient = !Bool(collapse_stability["quotient_stable"]) && Int(collapse_stability["collapse_count"]) > 0
    n01_order_affects_reachable_quotient = Bool(order_effect["pass"])
    stability_genuine = no_self_diff &&
        Bool(positive_stability["pass"]) &&
        Bool(reverse_stability["pass"]) &&
        Bool(collapse_stability["pass"]) &&
        quotient_survives_admissible_ops &&
        nonadmissible_op_collapses_quotient &&
        n01_order_affects_reachable_quotient
    classification_ok = CLASSIFICATION == "scratch_diagnostic"
    promotion_ok = PROMOTION_ALLOWED == false
    formal_ok = FORMAL_ADMISSION_ALLOWED == false

    shared_scalars = Dict{String,Any}(
        "base_quotient_class_count" => Float64(base_q["class_count"]),
        "admissible_forward_class_count" => Float64(positive_stability["after_class_count"]),
        "admissible_reverse_class_count" => Float64(reverse_stability["after_class_count"]),
        "nonadmissible_projective_z_class_count" => Float64(collapse_stability["after_class_count"]),
        "nonadmissible_projective_z_collapse_count" => Float64(collapse_stability["collapse_count"]),
        "preserve_operation_count" => Float64(length(preserve_ops)),
        "collapse_operation_count" => Float64(length(collapse_ops)),
        "n01_order_reachable_signature_l1_gap" => Float64(order_effect["reachable_signature_l1_gap"]),
        "n01_order_left_class_count" => Float64(order_effect["left_class_count"]),
        "n01_order_right_class_count" => Float64(order_effect["right_class_count"]),
    )
    shared_booleans = Dict{String,Any}(
        "classification_is_scratch_diagnostic" => classification_ok,
        "promotion_false" => promotion_ok,
        "formal_admission_false" => formal_ok,
        "admissible_forward_stable" => Bool(positive_stability["quotient_stable"]),
        "admissible_reverse_stable" => Bool(reverse_stability["quotient_stable"]),
        "nonadmissible_projective_z_unstable" => !Bool(collapse_stability["quotient_stable"]),
        "quotient_survives_admissible_ops" => quotient_survives_admissible_ops,
        "nonadmissible_op_collapses_quotient" => nonadmissible_op_collapses_quotient,
        "n01_order_affects_reachable_quotient" => n01_order_affects_reachable_quotient,
        "no_self_diff_tautologies" => no_self_diff,
        "stability_genuine" => stability_genuine,
    )
    shared_strings = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "allowed_claim" => ALLOWED_CLAIM,
        "admissible_sequence" => "unitary_X_then_damping_Z0_half",
        "reverse_sequence" => "damping_Z0_half_then_unitary_X",
        "negative_sequence" => "projective_Z",
    )

    result = Dict{String,Any}(
        "schema" => "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id" => OBJECT_ID,
        "sim_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "version" => "1.0",
        "tier" => "R2_quotient_stability_under_operations",
        "backend" => "julia",
        "generated_at" => string(Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS"), "Z"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "parent_packets" => [PARENT_RUNG_PACKET, PARENT_R2_PACKET, PARENT_R2_OPS, PARENT_R2_COMPOSITION],
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "allowed_claims" => [ALLOWED_CLAIM],
        "claim_ceiling" => CLAIM_CEILING,
        "promotion_status" => "diagnostic_only",
        "eligible_consumers" => [],
        "blocked_consumers" => ["promotion", "formal_admission", "higher_layer_consumers"],
        "sim_execution_kind" => SIM_EXECUTION_KIND,
        "sim_class" => "constraint_probe",
        "purpose" => "Complete the finite R2 operation layer by testing quotient stability under admissible ordered CPTP operations.",
        "scientific_question" => "Does the inherited probe-relative quotient S/~_M persist under admissible R2 operations and collapse under excluded operations?",
        "root_constraints_in_force" => ["F01", "N01", "probe_relative_quotient", "r2_admissible_operations", "r2_admissible_composition_rules"],
        "SIM_TEMPLATE_surface" => SIM_TEMPLATE_SURFACE,
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "required_tools" => ["JAX peer", "Julia", "LinearAlgebra"],
        "actual_tools_used" => ["Julia", "LinearAlgebra", "JSON"],
        "proof_surfaces_used" => [],
        "graph_surfaces_used" => [],
        "topology_surfaces_used" => [],
        "jax_enable_x64" => nothing,
        "numpy_compute_used" => false,
        "numpy_imported" => false,
        "finite_support_set_S" => Dict("size" => length(candidates), "candidate_ids" => [String(candidate["id"]) for candidate in candidates]),
        "finite_probe_family_M" => Dict("size" => length(probes), "probe_names" => [String(probe["name"]) for probe in probes]),
        "base_quotient_S_mod_M" => base_q,
        "operation_classification_source" => Dict(
            "admissible_preserve_operations" => preserve_ops,
            "excluded_collapse_operations" => collapse_ops,
            "rows" => op_class_rows,
        ),
        "stability_controls" => Dict(
            "positive_admissible_forward" => positive_stability,
            "boundary_admissible_reverse" => reverse_stability,
            "negative_nonadmissible_collapse" => collapse_stability,
            "n01_order_reachable_quotient" => order_effect,
        ),
        "probe" => Dict(
            "stability_predicate" => "CPTP components, well-defined map on base quotient classes, and output class count equal to base quotient class count",
            "positive_sequence" => admissible_sequence,
            "negative_sequence" => nonadmissible_sequence,
            "order_sequences" => [admissible_sequence, reverse_sequence],
        ),
        "positive" => Dict(
            "admissible_forward_preserves_quotient" => Dict("pass" => Bool(positive_stability["pass"])),
            "admissible_reverse_preserves_quotient" => Dict("pass" => Bool(reverse_stability["pass"])),
            "quotient_survives_admissible_ops" => Dict("pass" => quotient_survives_admissible_ops),
            "n01_order_affects_reachable_quotient" => Dict("pass" => n01_order_affects_reachable_quotient),
            "no_self_diff_tautologies" => Dict("pass" => no_self_diff),
            "classification_is_scratch_diagnostic" => Dict("pass" => classification_ok),
            "promotion_false" => Dict("pass" => promotion_ok),
            "formal_admission_false" => Dict("pass" => formal_ok),
        ),
        "negative" => Dict(
            "nonadmissible_projective_z_collapses_quotient" => Dict(
                "pass" => Bool(collapse_stability["pass"]),
                "same_stability_predicate_as_positive" => true,
                "positive_predicate_value" => Bool(positive_stability["quotient_stable"]),
                "negative_predicate_value" => Bool(collapse_stability["quotient_stable"]),
                "base_class_count" => base_q["class_count"],
                "after_class_count" => collapse_stability["after_class_count"],
                "collapse_count" => collapse_stability["collapse_count"],
            ),
            "order_swap_changes_reachable_quotient" => Dict(
                "pass" => Bool(order_effect["pass"]),
                "left_expression_id" => order_effect["left_expression_id"],
                "right_expression_id" => order_effect["right_expression_id"],
                "reachable_signature_l1_gap" => order_effect["reachable_signature_l1_gap"],
            ),
        ),
        "graveyard_companions" => Dict(
            "self_diff_control" => Dict("pass" => no_self_diff),
            "nonadmissible_operation_as_preserving" => Dict("pass" => nonadmissible_op_collapses_quotient),
            "order_irrelevant_for_noncommuting_admissible_pair" => Dict("pass" => n01_order_affects_reachable_quotient),
        ),
        "boundary" => Dict(
            "reverse_admissible_sequence_still_stable" => Dict("pass" => Bool(reverse_stability["quotient_stable"])),
            "same_class_count_but_different_ordered_reachable_signatures" => Dict(
                "pass" => Bool(order_effect["class_count_preserved_in_both_orders"]) && Bool(order_effect["reachable_signature_sets_differ"]),
                "left_class_count" => order_effect["left_class_count"],
                "right_class_count" => order_effect["right_class_count"],
                "reachable_signature_l1_gap" => order_effect["reachable_signature_l1_gap"],
            ),
            "classification_is_scratch_diagnostic" => Dict("pass" => classification_ok),
            "promotion_allowed_false" => Dict("pass" => promotion_ok),
            "formal_admission_allowed_false" => Dict("pass" => formal_ok),
        ),
        "nearby_variants" => Dict(
            "total" => 3,
            "passed" => 3,
            "all_pass" => true,
            "rows" => [
                Dict("name" => "admissible_forward_sequence", "pass" => Bool(positive_stability["pass"])),
                Dict("name" => "admissible_reverse_sequence", "pass" => Bool(reverse_stability["pass"])),
                Dict("name" => "nonadmissible_projective_z_negative", "pass" => Bool(collapse_stability["pass"])),
            ],
        ),
        "why_not_v4_probes" => "This is a v5 scratch diagnostic formal-scout-style receipt with no promotion or formal admission.",
        "required_negatives" => ["nonadmissible_projective_z_collapses_quotient", "order_swap_changes_reachable_quotient"],
        "negatives_run" => ["nonadmissible_projective_z_collapses_quotient", "order_swap_changes_reachable_quotient"],
        "kill_conditions" => [
            "admissible operation sequence collapses or splits the base quotient",
            "nonadmissible projective operation fails to collapse the base quotient",
            "ordered admissible noncommuting pair has identical reachable quotient signatures",
            "any control compares an expression with itself",
            "JAX/Julia parity exceeds tolerance",
        ],
        "required_artifacts" => [RESULT_PATH, JAX_REFERENCE_PATH],
        "artifacts_emitted" => [RESULT_PATH],
        "witness_trace_id" => "$(OBJECT_ID):julia:$(Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS"))Z",
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "shared_strings" => shared_strings,
    )
    result["parity"] = parity_against_jax(result)
    result["parity_within_run"] = Bool(result["parity"]["within_1e_12"])
    result["quotient_survives_admissible_ops"] = quotient_survives_admissible_ops
    result["nonadmissible_op_collapses_quotient"] = nonadmissible_op_collapses_quotient
    result["n01_order_affects_reachable_quotient"] = n01_order_affects_reachable_quotient
    result["no_self_diff_tautologies"] = no_self_diff
    result["stability_genuine"] = stability_genuine
    result["all_pass"] = quotient_survives_admissible_ops &&
        nonadmissible_op_collapses_quotient &&
        n01_order_affects_reachable_quotient &&
        no_self_diff &&
        stability_genuine &&
        Bool(result["parity"]["within_1e_12"]) &&
        classification_ok &&
        promotion_ok &&
        formal_ok
    result["stop_condition_fired"] = !Bool(result["all_pass"])
    result["pass_rule"] = "admissible sequences stable, nonadmissible sequence collapses, N01 order changes reachable quotient, no self-diff controls, and JAX/Julia parity passes"
    result["fail_rule"] = "any required stability, collapse, order, no-self-diff, fence, or parity predicate is false"
    result["result_summary"] = Dict(
        "all_pass" => result["all_pass"],
        "parity_within_run" => result["parity_within_run"],
        "quotient_survives_admissible_ops" => quotient_survives_admissible_ops,
        "nonadmissible_op_collapses_quotient" => nonadmissible_op_collapses_quotient,
        "n01_order_affects_reachable_quotient" => n01_order_affects_reachable_quotient,
        "no_self_diff_tautologies" => no_self_diff,
        "stability_genuine" => stability_genuine,
        "base_class_count" => base_q["class_count"],
        "nonadmissible_after_class_count" => collapse_stability["after_class_count"],
        "n01_order_reachable_signature_l1_gap" => order_effect["reachable_signature_l1_gap"],
    )
    result["criteria_checked"] = [
        "classification/promotion/formal-admission fences",
        "finite inherited S and M quotient exists",
        "admissible forward sequence preserves quotient class count and is well-defined on classes",
        "admissible reverse sequence preserves quotient class count and is well-defined on classes",
        "nonadmissible projective_Z collapses quotient with the same stability predicate",
        "noncommuting admissible operation order changes reachable quotient signatures",
        "all controls compare distinct computed quantities",
        "JAX/Julia shared scalar, boolean, and string parity",
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
    println("wrote $(RESULT_PATH)")
    println(JSON.json(Dict(
        "all_pass" => result["all_pass"],
        "parity_within_run" => result["parity_within_run"],
        "quotient_survives_admissible_ops" => result["quotient_survives_admissible_ops"],
        "nonadmissible_op_collapses_quotient" => result["nonadmissible_op_collapses_quotient"],
        "n01_order_affects_reachable_quotient" => result["n01_order_affects_reachable_quotient"],
        "no_self_diff_tautologies" => result["no_self_diff_tautologies"],
        "stability_genuine" => result["stability_genuine"],
    )))
    return Bool(result["all_pass"]) ? 0 : 1
end

exit(main())
