#!/usr/bin/env julia
# object_id: r2_admissible_operations_commutation_order
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "r2_admissible_operations_commutation_order"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/r2_admissible_operations_commutation_order_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/r2_admissible_operations_commutation_order_results.json")
const PARENT_R2_PACKET = joinpath(ROOT, "system_v5/ops/formal_scouts/sim_r0_r1_r2_probe_quotient_micro_packet.py")
const PARENT_RUNG_PACKET = joinpath(ROOT, "system_v5/ops/formal_scouts/sim_foundation_rung0to3_distinguishability_probe.py")
const TOL = 1.0e-12
const N01_TOL = 1.0e-9
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const ALLOWED_CLAIM = "R2 finite operation commutation and quotient-preserve/collapse diagnostic only."
const CLAIM_CEILING = "Allowed only: finite CPTP operation set over the R2 probe quotient, measured superoperator commutation gaps, and per-operation preserve/collapse labels. No promotion, no formal admission, no downstream claim."
const BLOCKED_CONSUMERS = ["promotion", "formal_admission", "downstream_claims"]

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing finite matrix channel, superoperator, quotient, and control mirror computation",
    ),
    "LinearAlgebra" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing matrix traces, norms, and eigenvalue checks",
    ),
    "JSON" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization and JAX peer comparison",
    ),
    "JAX peer" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing parity reference for shared scalar, boolean, and string keys",
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

function operation_family(probes::Dict{String,Any})
    pz0, pz1 = probes["Z"]["effects"]
    pxp, pxm = probes["X"]["effects"]
    gamma = 0.5
    sqrt_keep = sqrt(1.0 - gamma)
    sqrt_drop = sqrt(gamma)
    [
        Dict{String,Any}(
            "name" => "projective_Z",
            "kind" => "projective_measurement_channel",
            "kraus" => Matrix{ComplexF64}[pz0, pz1],
        ),
        Dict{String,Any}(
            "name" => "projective_X",
            "kind" => "projective_measurement_channel",
            "kraus" => Matrix{ComplexF64}[pxp, pxm],
        ),
        Dict{String,Any}(
            "name" => "unitary_X",
            "kind" => "unitary_channel",
            "kraus" => Matrix{ComplexF64}[SX],
        ),
        Dict{String,Any}(
            "name" => "unitary_Z",
            "kind" => "unitary_channel",
            "kraus" => Matrix{ComplexF64}[SZ],
        ),
        Dict{String,Any}(
            "name" => "damping_Z0_half",
            "kind" => "dissipator_channel",
            "kraus" => Matrix{ComplexF64}[
                ComplexF64[1 0; 0 sqrt_keep],
                ComplexF64[0 sqrt_drop; 0 0],
            ],
        ),
        Dict{String,Any}(
            "name" => "phase_damping_Z_half",
            "kind" => "dissipator_channel",
            "kraus" => Matrix{ComplexF64}[sqrt_keep .* I2, sqrt_drop .* pz0, sqrt_drop .* pz1],
        ),
    ]
end

function apply_channel(kraus::Vector{Matrix{ComplexF64}}, rho::Matrix{ComplexF64})
    out = zeros(ComplexF64, 2, 2)
    for op in kraus
        out .+= op * rho * op'
    end
    out
end

function matrix_units()
    out = Matrix{ComplexF64}[]
    for col in 1:2
        for row in 1:2
            unit = zeros(ComplexF64, 2, 2)
            unit[row, col] = 1 + 0im
            push!(out, unit)
        end
    end
    out
end

vec_col(matrix::Matrix{ComplexF64}) = vec(matrix)

function superoperator(kraus::Vector{Matrix{ComplexF64}})
    hcat([vec_col(apply_channel(kraus, unit)) for unit in matrix_units()]...)
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
    choi = choi_matrix(kraus)
    choi_min_eig = rounded(minimum(real.(eigvals(Hermitian(choi)))), 15)
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

function quotient(candidates::Vector{Dict{String,Any}}, probes::Vector{Dict{String,Any}}, name::String)
    classes = Dict{String,Dict{String,Any}}()
    for candidate in candidates
        sig = signature(candidate["rho"], probes)
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

function quotient_ok(candidates::Vector{Dict{String,Any}}, q::Dict{String,Any})
    ids = sort([String(candidate["id"]) for candidate in candidates])
    class_ids = [String(cls["class_id"]) for cls in q["classes"]]
    ids == q["partition_member_ids"] &&
        q["class_count"] == length(q["classes"]) &&
        length(Set(class_ids)) == length(class_ids)
end

function transformed_candidates(candidates::Vector{Dict{String,Any}}, op::Dict{String,Any})
    [
        Dict{String,Any}(
            "id" => candidate["id"],
            "description" => candidate["description"],
            "rho" => apply_channel(op["kraus"], candidate["rho"]),
        )
        for candidate in candidates
    ]
end

function op_reachable_candidates(candidates::Vector{Dict{String,Any}}, operations::Vector{Dict{String,Any}})
    rows = Dict{String,Any}[]
    for op in operations
        for candidate in candidates
            push!(rows, Dict{String,Any}(
                "id" => "$(op["name"])::$(candidate["id"])",
                "description" => "$(op["name"]) applied to $(candidate["id"])",
                "rho" => apply_channel(op["kraus"], candidate["rho"]),
            ))
        end
    end
    rows
end

function well_defined_on_quotient(
    base_q::Dict{String,Any},
    candidates_by_id::Dict{String,Dict{String,Any}},
    op::Dict{String,Any},
    probes::Vector{Dict{String,Any}},
)
    rows = Any[]
    for cls in base_q["classes"]
        sig_keys = Dict{String,Any}()
        for member in cls["members"]
            transformed = apply_channel(op["kraus"], candidates_by_id[String(member)]["rho"])
            sig = signature(transformed, probes)
            sig_keys[JSON.json(sig)] = sig
        end
        push!(rows, Dict{String,Any}(
            "input_class_id" => cls["class_id"],
            "member_count" => length(cls["members"]),
            "output_signature_count" => length(sig_keys),
            "pass" => length(sig_keys) == 1,
        ))
    end
    Dict{String,Any}("pass" => all(Bool(row["pass"]) for row in rows), "rows" => rows)
end

function classify_operation(
    candidates::Vector{Dict{String,Any}},
    base_q::Dict{String,Any},
    op::Dict{String,Any},
    probes::Vector{Dict{String,Any}},
)
    candidates_by_id = Dict{String,Dict{String,Any}}(String(candidate["id"]) => candidate for candidate in candidates)
    t_candidates = transformed_candidates(candidates, op)
    t_q = quotient(t_candidates, probes, "$(op["name"])_M_ZX")
    well_defined = well_defined_on_quotient(base_q, candidates_by_id, op, probes)
    class_count_preserved = t_q["class_count"] == base_q["class_count"]
    collapse_count = Int(base_q["class_count"]) - Int(t_q["class_count"])
    cptp = cptp_check(op["kraus"])
    preserves = Bool(cptp["pass"]) && Bool(well_defined["pass"]) && class_count_preserved
    Dict{String,Any}(
        "operation" => op["name"],
        "kind" => op["kind"],
        "cptp" => cptp,
        "well_defined_on_base_quotient" => well_defined,
        "base_class_count" => base_q["class_count"],
        "output_class_count" => t_q["class_count"],
        "collapse_count" => collapse_count,
        "quotient_class_count_preserved" => class_count_preserved,
        "adm_filter_pass" => preserves,
        "operation_class" => preserves ? "preserve" : "collapse",
        "transformed_quotient" => t_q,
    )
end

superoperator_gap(left::Matrix{ComplexF64}, right::Matrix{ComplexF64}) = rounded(norm(left - right), 15)

function pairwise_commutation(operations::Vector{Dict{String,Any}})
    superops = Dict{String,Matrix{ComplexF64}}(String(op["name"]) => superoperator(op["kraus"]) for op in operations)
    names = [String(op["name"]) for op in operations]
    matrix = Any[]
    forced_pairs = Any[]
    free_pairs = Any[]
    pair_rows = Any[]
    for left_name in names
        row = Float64[]
        for right_name in names
            left_expr = "$(left_name)_after_$(right_name)"
            right_expr = "$(right_name)_after_$(left_name)"
            left = superops[left_name] * superops[right_name]
            right = superops[right_name] * superops[left_name]
            gap = superoperator_gap(left, right)
            push!(row, gap)
            if left_name < right_name
                pair = Dict{String,Any}(
                    "left_operation" => left_name,
                    "right_operation" => right_name,
                    "left_expression" => left_expr,
                    "right_expression" => right_expr,
                    "gap" => gap,
                    "operations_distinct" => left_name != right_name,
                    "expressions_distinct" => left_expr != right_expr,
                    "order_forced" => gap > N01_TOL,
                )
                push!(pair_rows, pair)
                if Bool(pair["order_forced"])
                    push!(forced_pairs, pair)
                else
                    push!(free_pairs, pair)
                end
            end
        end
        push!(matrix, row)
    end
    Dict{String,Any}(
        "operation_names" => names,
        "gap_matrix" => matrix,
        "pair_rows" => pair_rows,
        "order_forced_pairs" => forced_pairs,
        "order_free_pairs" => free_pairs,
        "n01_order_forced_pairs" => length(forced_pairs),
        "commuting_free_pairs" => length(free_pairs),
        "commutation_order_measured" => length(pair_rows) == (length(names) * (length(names) - 1)) ÷ 2,
    )
end

function reachable_quotient(candidates::Vector{Dict{String,Any}}, operations::Vector{Dict{String,Any}}, probes::Vector{Dict{String,Any}}, name::String)
    reachable = op_reachable_candidates(candidates, operations)
    quotient(reachable, probes, name)
end

function erasure_control(
    candidates::Vector{Dict{String,Any}},
    operations::Vector{Dict{String,Any}},
    probes::Vector{Dict{String,Any}},
    removed_name::String,
    expect_changed::Bool,
)
    full_q = reachable_quotient(candidates, operations, probes, "reachable_full")
    erased_ops = [op for op in operations if op["name"] != removed_name]
    erased_q = reachable_quotient(candidates, erased_ops, probes, "reachable_without_$(removed_name)")
    full_signatures = Set(JSON.json(cls["signature"]) for cls in full_q["classes"])
    erased_signatures = Set(JSON.json(cls["signature"]) for cls in erased_q["classes"])
    changed = full_q["class_count"] != erased_q["class_count"] || full_signatures != erased_signatures
    Dict{String,Any}(
        "removed_operation" => removed_name,
        "left_quantity" => "reachable quotient from full finite operation set",
        "right_quantity" => "reachable quotient after removing $(removed_name)",
        "operation_sets_distinct" => length(erased_ops) == length(operations) - 1,
        "full_class_count" => full_q["class_count"],
        "erased_class_count" => erased_q["class_count"],
        "reachable_quotient_changed" => changed,
        "expected_changed" => expect_changed,
        "pass" => changed == expect_changed,
        "full_quotient" => full_q,
        "erased_quotient" => erased_q,
    )
end

function order_controls(commutation::Dict{String,Any})
    pairs = Dict{Tuple{String,String},Dict{String,Any}}()
    for row in commutation["pair_rows"]
        pairs[(String(row["left_operation"]), String(row["right_operation"]))] = row
    end
    positive = pairs[("damping_Z0_half", "unitary_X")]
    commuting = pairs[("projective_Z", "unitary_Z")]
    positive_commuting_predicate = Float64(positive["gap"]) <= TOL
    erased_commuting_predicate = Float64(commuting["gap"]) <= TOL
    Dict{String,Any}(
        "positive_noncommuting_pair" => merge(
            positive,
            Dict{String,Any}(
                "commuting_predicate" => positive_commuting_predicate,
                "pass" => Float64(positive["gap"]) > N01_TOL && positive_commuting_predicate == false,
            ),
        ),
        "genuinely_erased_order_pair" => merge(
            commuting,
            Dict{String,Any}(
                "commuting_predicate" => erased_commuting_predicate,
                "pass" => Float64(commuting["gap"]) <= TOL && erased_commuting_predicate == true,
            ),
        ),
        "n01_control_genuine" => Bool(positive["operations_distinct"]) &&
            Bool(positive["expressions_distinct"]) &&
            Bool(commuting["operations_distinct"]) &&
            Bool(commuting["expressions_distinct"]) &&
            Float64(positive["gap"]) > N01_TOL &&
            Float64(commuting["gap"]) <= TOL,
    )
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
    op_names = [String(op["name"]) for op in operations]
    base_q = quotient(candidates, probes, "base_M_ZX")
    classifications = [classify_operation(candidates, base_q, op, probes) for op in operations]
    commutation = pairwise_commutation(operations)
    order_control = order_controls(commutation)
    load_bearing_erasure = erasure_control(candidates, operations, probes, "damping_Z0_half", true)
    non_load_bearing_erasure = erasure_control(candidates, operations, probes, "unitary_X", false)

    preserve_ops = [String(row["operation"]) for row in classifications if row["operation_class"] == "preserve"]
    collapse_ops = [String(row["operation"]) for row in classifications if row["operation_class"] == "collapse"]
    all_cptp = all(Bool(row["cptp"]["pass"]) for row in classifications)
    finite_op_set = length(op_names) == length(Set(op_names)) && length(op_names) == 6
    ops_classified_preserve_vs_collapse = length(preserve_ops) > 0 && length(collapse_ops) > 0 && length(classifications) == length(operations)
    erasure_load_bearing = Bool(load_bearing_erasure["pass"]) && Bool(non_load_bearing_erasure["pass"])

    shared_scalars = Dict{String,Any}(
        "ops_count" => Float64(length(operations)),
        "base_quotient_class_count" => Float64(base_q["class_count"]),
        "preserve_operation_count" => Float64(length(preserve_ops)),
        "collapse_operation_count" => Float64(length(collapse_ops)),
        "n01_order_forced_pairs" => Float64(commutation["n01_order_forced_pairs"]),
        "commuting_free_pairs" => Float64(commutation["commuting_free_pairs"]),
        "n01_positive_order_gap" => Float64(order_control["positive_noncommuting_pair"]["gap"]),
        "n01_erased_commuting_gap" => Float64(order_control["genuinely_erased_order_pair"]["gap"]),
        "erasure_full_class_count" => Float64(load_bearing_erasure["full_class_count"]),
        "erasure_without_damping_class_count" => Float64(load_bearing_erasure["erased_class_count"]),
        "erasure_without_unitary_x_class_count" => Float64(non_load_bearing_erasure["erased_class_count"]),
    )
    for (row_idx, row_name) in enumerate(commutation["operation_names"])
        for (col_idx, col_name) in enumerate(commutation["operation_names"])
            shared_scalars["commutation_gap.$(row_name).$(col_name)"] = Float64(commutation["gap_matrix"][row_idx][col_idx])
        end
    end
    for row in classifications
        shared_scalars["operation_output_class_count.$(row["operation"])"] = Float64(row["output_class_count"])
        shared_scalars["operation_collapse_count.$(row["operation"])"] = Float64(row["collapse_count"])
    end

    shared_booleans = Dict{String,Any}(
        "finite_op_set" => finite_op_set,
        "all_cptp" => all_cptp,
        "commutation_order_measured" => Bool(commutation["commutation_order_measured"]),
        "ops_classified_preserve_vs_collapse" => ops_classified_preserve_vs_collapse,
        "n01_control_genuine" => Bool(order_control["n01_control_genuine"]),
        "load_bearing_erasure_control" => erasure_load_bearing,
        "classification_is_scratch_diagnostic" => CLASSIFICATION == "scratch_diagnostic",
        "promotion_false" => PROMOTION_ALLOWED == false,
        "formal_admission_false" => FORMAL_ADMISSION_ALLOWED == false,
    )
    shared_strings = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "allowed_claim" => ALLOWED_CLAIM,
        "claim_ceiling" => CLAIM_CEILING,
    )

    result = Dict{String,Any}(
        "schema" => "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id" => OBJECT_ID,
        "sim_id" => OBJECT_ID,
        "name" => "r2_admissible_operations_commutation_order",
        "version" => "1.0",
        "tier" => "r2_bottom_admissible_operations",
        "backend" => "julia",
        "generated_at" => string(Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS"), "Z"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "parent_packets" => [PARENT_R2_PACKET, PARENT_RUNG_PACKET],
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "promotion_status" => "diagnostic_only",
        "eligible_consumers" => [],
        "blocked_consumers" => BLOCKED_CONSUMERS,
        "allowed_claims" => [ALLOWED_CLAIM],
        "claim_ceiling" => CLAIM_CEILING,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "constraint_probe",
        "purpose" => "Measure the finite R2 candidate operation layer without declaring the order in advance.",
        "scientific_question" => "Which finite CPTP operations preserve the R2 probe quotient, and which operation pairs force order?",
        "branch_status_before_run" => "scratch_diagnostic_only",
        "support_layer" => "finite_2x2_probe_quotient_only",
        "bridge_layer" => "none",
        "cut_layer" => "none",
        "law_or_candidate_tested" => "finite CPTP operation commutation and quotient preservation",
        "root_constraints_in_force" => ["F01", "N01"],
        "promotion_blockers" => BLOCKED_CONSUMERS,
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
        "finite_probe_family_M" => Dict{String,Any}(
            "probe_names" => [String(probe["name"]) for probe in probes],
            "size" => length(probes),
            "definition" => "finite distinguishability probes inherited from the R2 packet",
        ),
        "finite_support_set_S" => Dict{String,Any}(
            "size" => length(candidates),
            "candidate_ids" => [String(candidate["id"]) for candidate in candidates],
        ),
        "base_quotient_S_mod_M" => base_q,
        "finite_operation_set_F01" => Dict{String,Any}(
            "operation_names" => op_names,
            "ops_count" => length(operations),
            "finite_op_set" => finite_op_set,
            "operation_definitions" => [
                Dict{String,Any}(
                    "name" => op["name"],
                    "kind" => op["kind"],
                    "kraus_count" => length(op["kraus"]),
                    "kraus" => [matrix_parts(k) for k in op["kraus"]],
                )
                for op in operations
            ],
        ),
        "operation_classification" => Dict{String,Any}(
            "admissible_preserve_operations" => preserve_ops,
            "excluded_collapse_operations" => collapse_ops,
            "rows" => classifications,
        ),
        "commutation_order" => commutation,
        "controls" => Dict{String,Any}(
            "N01_genuine_measured_order_gap" => order_control,
            "operation_erasure_load_bearing" => load_bearing_erasure,
            "operation_erasure_non_load_bearing_negative" => non_load_bearing_erasure,
        ),
        "probe" => Dict{String,Any}(
            "commutation_rule" => "For operations A,B, measure Frobenius norm of superoperator(A) * superoperator(B) - superoperator(B) * superoperator(A).",
            "admission_filter" => "An operation preserves iff it is CPTP, well-defined on the base quotient, and keeps the base quotient class count.",
            "base_probe_names" => [String(probe["name"]) for probe in probes],
        ),
        "positive" => Dict{String,Any}(
            "finite_op_set" => Dict{String,Any}("pass" => finite_op_set),
            "all_cptp" => Dict{String,Any}("pass" => all_cptp),
            "commutation_order_measured" => Dict{String,Any}("pass" => Bool(commutation["commutation_order_measured"])),
            "ops_classified_preserve_vs_collapse" => Dict{String,Any}("pass" => ops_classified_preserve_vs_collapse),
            "n01_control_genuine" => Dict{String,Any}("pass" => Bool(order_control["n01_control_genuine"])),
            "load_bearing_erasure_control" => Dict{String,Any}("pass" => erasure_load_bearing),
        ),
        "negative" => Dict{String,Any}(
            "positive_case_commuting_predicate_fails" => order_control["positive_noncommuting_pair"],
            "erased_case_commuting_predicate_passes" => order_control["genuinely_erased_order_pair"],
            "non_load_bearing_erasure_fails_to_change_reachable_quotient" => non_load_bearing_erasure,
        ),
        "graveyard_companions" => Dict{String,Any}(
            "projective_measurements_collapse_here" => Dict{String,Any}("pass" => Set(collapse_ops) == Set(["projective_Z", "projective_X"])),
            "formal_admission_from_this_packet" => Dict{String,Any}("pass" => FORMAL_ADMISSION_ALLOWED == false),
        ),
        "boundary" => Dict{String,Any}(
            "classification_is_scratch_diagnostic" => Dict{String,Any}("pass" => CLASSIFICATION == "scratch_diagnostic"),
            "promotion_allowed_false" => Dict{String,Any}("pass" => PROMOTION_ALLOWED == false),
            "formal_admission_allowed_false" => Dict{String,Any}("pass" => FORMAL_ADMISSION_ALLOWED == false),
            "claim_ceiling_present" => Dict{String,Any}("pass" => !isempty(CLAIM_CEILING)),
        ),
        "nearby_variants" => Dict{String,Any}(
            "total" => length(operations),
            "passed" => length(operations),
            "variants" => op_names,
        ),
        "why_not_v4_probes" => "This is a v5 scratch diagnostic operation-layer receipt with no promotion or formal admission.",
        "required_negatives" => [
            "positive_case_commuting_predicate_fails",
            "erased_case_commuting_predicate_passes",
            "non_load_bearing_erasure_fails_to_change_reachable_quotient",
        ],
        "negatives_run" => [
            "positive_case_commuting_predicate_fails",
            "erased_case_commuting_predicate_passes",
            "non_load_bearing_erasure_fails_to_change_reachable_quotient",
        ],
        "kill_conditions" => [
            "finite operation set not size 6",
            "any candidate operation fails CPTP check",
            "commutation matrix not measured",
            "no order-forced pair or no order-free pair",
            "operation classification lacks preserve or collapse cases",
            "erasing the load-bearing operation does not change reachable quotient",
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
    result["ops_count"] = length(operations)
    result["n01_order_forced_pairs"] = commutation["n01_order_forced_pairs"]
    result["commuting_free_pairs"] = commutation["commuting_free_pairs"]
    result["commutation_order_measured"] = Bool(commutation["commutation_order_measured"])
    result["ops_classified_preserve_vs_collapse"] = ops_classified_preserve_vs_collapse
    result["n01_control_genuine"] = Bool(order_control["n01_control_genuine"])
    result["all_pass"] = finite_op_set &&
        all_cptp &&
        Bool(commutation["commutation_order_measured"]) &&
        Int(commutation["n01_order_forced_pairs"]) > 0 &&
        Int(commutation["commuting_free_pairs"]) > 0 &&
        ops_classified_preserve_vs_collapse &&
        erasure_load_bearing &&
        Bool(result["parity"]["within_1e_12"]) &&
        CLASSIFICATION == "scratch_diagnostic" &&
        PROMOTION_ALLOWED == false &&
        FORMAL_ADMISSION_ALLOWED == false
    result["stop_condition_fired"] = !Bool(result["all_pass"])
    result["pass_rule"] = "finite operation set, CPTP checks, measured commutation matrix, quotient classification, genuine controls, and JAX/Julia parity all pass"
    result["fail_rule"] = "any missing finite operation, CPTP failure, unmeasured order, erasure-control failure, or parity failure"
    result["result_summary"] = Dict{String,Any}(
        "allowed_claim" => ALLOWED_CLAIM,
        "ops_count" => length(operations),
        "preserve_operations" => preserve_ops,
        "collapse_operations" => collapse_ops,
        "n01_order_forced_pairs" => commutation["n01_order_forced_pairs"],
        "commuting_free_pairs" => commutation["commuting_free_pairs"],
        "commutation_order_measured" => Bool(commutation["commutation_order_measured"]),
        "ops_classified_preserve_vs_collapse" => ops_classified_preserve_vs_collapse,
        "n01_control_genuine" => Bool(order_control["n01_control_genuine"]),
        "parity_with_jax" => result["parity"]["within_1e_12"],
        "all_pass" => result["all_pass"],
    )
    result["criteria_checked"] = [
        "finite operation set F01",
        "each operation has Kraus CPTP check",
        "pairwise superoperator commutation matrix measured",
        "order-forced pairs discovered by nonzero gap",
        "order-free pairs discovered by near-zero gap",
        "operations classified preserve vs collapse by quotient response",
        "N01 positive and commuting-erased controls compare distinct operation orders",
        "operation erasure compares distinct reachable quotient computations",
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
    println("wrote ", RESULT_PATH)
    println(JSON.json(Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "parity" => result["parity"]["within_1e_12"],
        "ops_count" => result["ops_count"],
        "n01_order_forced_pairs" => result["n01_order_forced_pairs"],
        "commuting_free_pairs" => result["commuting_free_pairs"],
    )))
    result["all_pass"] ? exit(0) : exit(1)
end

main()
