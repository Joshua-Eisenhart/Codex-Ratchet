#!/usr/bin/env julia
# object_id: foundation_rung0to3_distinguishability
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "foundation_rung0to3_distinguishability"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_rung0to3_distinguishability_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/foundation_rung0to3_distinguishability_results.json")
const TOL = 1.0e-12
const CLASSIFICATION = "scratch_diagnostic"
const CLAIM_CEILING = "rungs 0-3 finite distinguishability structure built bottom-up from F01+N01+(a=a iff a~b) grounded in owner docs; density matrix = quotient S/~_M; the FOUNDATION of the model; NOT geometry, NOT carrier, NOT physics, NOT canonical."

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing mirror for finite density matrices, finite POVM statistics, quotient classes, and order-gap controls",
    ),
    "LinearAlgebra" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing matrix traces, norms, projectors, and sequential probe statistics",
    ),
    "JSON" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization and JAX peer comparison",
    ),
    "numpy" => Dict{String,Any}(
        "tried" => false,
        "used" => false,
        "reason" => "not part of the Julia mirror and not used for compute",
    ),
    "pytorch" => Dict{String,Any}(
        "tried" => false,
        "used" => false,
        "reason" => "not used: explicit user fence requires JAX plus Julia mirror",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "JSON" => "supportive",
    "numpy" => nothing,
    "pytorch" => nothing,
)

rounded(value::Real, digits::Int = 12) = round(Float64(value); digits = digits)

function ket(values::Vector{ComplexF64})
    vec = copy(values)
    vec ./ sqrt(real(dot(vec, vec)))
end

density(psi::Vector{ComplexF64}) = psi * psi'
projector(psi::Vector{ComplexF64}) = density(psi)

function make_projective_probe(name::String, vectors::Vector{Vector{ComplexF64}})
    Dict{String,Any}(
        "name" => name,
        "outcome_labels" => ["$(name)_$(idx - 1)" for idx in eachindex(vectors)],
        "effects" => [projector(vec) for vec in vectors],
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
        "Z_relabel" => make_projective_probe("Z_relabel", [ks["z1"], ks["z0"]]),
        "X" => make_projective_probe("X", [ks["x_plus"], ks["x_minus"]]),
        "Y" => make_projective_probe("Y", [ks["y_plus"], ks["y_minus"]]),
    )
end

function candidate_configurations()
    ks = base_kets()
    rhos = Dict{String,Matrix{ComplexF64}}(name => density(vec) for (name, vec) in ks)
    mixed_z = 0.5 .* rhos["z0"] .+ 0.5 .* rhos["z1"]
    mixed_x = 0.5 .* rhos["x_plus"] .+ 0.5 .* rhos["x_minus"]
    [
        Dict{String,Any}("id" => "pure_z0", "description" => "one pure state", "rho" => rhos["z0"]),
        Dict{String,Any}("id" => "pure_z1", "description" => "orthogonal pure state", "rho" => rhos["z1"]),
        Dict{String,Any}("id" => "pure_x_plus", "description" => "finite superposition pure state", "rho" => rhos["x_plus"]),
        Dict{String,Any}("id" => "pure_x_minus", "description" => "finite superposition pure state", "rho" => rhos["x_minus"]),
        Dict{String,Any}("id" => "pure_y_plus", "description" => "finite phase-offset pure state", "rho" => rhos["y_plus"]),
        Dict{String,Any}("id" => "pure_y_minus", "description" => "finite phase-offset pure state", "rho" => rhos["y_minus"]),
        Dict{String,Any}(
            "id" => "ensemble_z_mixed",
            "description" => "50/50 ensemble over pure_z0 and pure_z1",
            "rho" => mixed_z,
            "ensemble" => Any[Any["pure_z0", 0.5], Any["pure_z1", 0.5]],
        ),
        Dict{String,Any}(
            "id" => "ensemble_x_mixed",
            "description" => "50/50 ensemble over pure_x_plus and pure_x_minus",
            "rho" => mixed_x,
            "ensemble" => Any[Any["pure_x_plus", 0.5], Any["pure_x_minus", 0.5]],
        ),
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

function quotient_ok(candidates::Vector{Dict{String,Any}}, q::Dict{String,Any})
    ids = sort([String(candidate["id"]) for candidate in candidates])
    class_ids = [String(cls["class_id"]) for cls in q["classes"]]
    ids == q["partition_member_ids"] &&
        q["class_count"] == length(q["classes"]) &&
        length(Set(class_ids)) == length(class_ids)
end

function sequential_joint_stats(rho::Matrix{ComplexF64}, first::Dict{String,Any}, second::Dict{String,Any})
    stats = Float64[]
    for p_first in first["effects"]
        post_first = p_first * rho * p_first
        for p_second in second["effects"]
            push!(stats, rounded(real(tr(p_second * post_first)), 12))
        end
    end
    stats
end

function sequential_joint_distribution(rho::Matrix{ComplexF64}, first::Dict{String,Any}, second::Dict{String,Any})
    rows = Any[]
    for (first_label, p_first) in zip(first["outcome_labels"], first["effects"])
        post_first = p_first * rho * p_first
        for (second_label, p_second) in zip(second["outcome_labels"], second["effects"])
            push!(rows, Dict{String,Any}(
                "first_probe" => first["name"],
                "first_outcome" => first_label,
                "second_probe" => second["name"],
                "second_outcome" => second_label,
                "probability" => rounded(real(tr(p_second * post_first)), 12),
            ))
        end
    end
    rows
end

function sequential_order_gap(left::Vector{Any}, reversed_order::Vector{Any})
    left_by_pair = Dict{Tuple{String,String},Float64}()
    for row in left
        left_by_pair[(String(row["first_outcome"]), String(row["second_outcome"]))] = Float64(row["probability"])
    end
    right_by_pair = Dict{Tuple{String,String},Float64}()
    for row in reversed_order
        right_by_pair[(String(row["second_outcome"]), String(row["first_outcome"]))] = Float64(row["probability"])
    end
    all_keys = union(Set(keys(left_by_pair)), Set(keys(right_by_pair)))
    sum(abs(get(left_by_pair, key, 0.0) - get(right_by_pair, key, 0.0)) for key in all_keys)
end

function max_projector_commutator_norm(first::Dict{String,Any}, second::Dict{String,Any})
    gaps = Float64[]
    for p_first in first["effects"]
        for p_second in second["effects"]
            push!(gaps, rounded(norm(p_first * p_second - p_second * p_first), 15))
        end
    end
    maximum(gaps)
end

l1_gap(left::Vector{Float64}, right::Vector{Float64}) = sum(abs(a - b) for (a, b) in zip(left, right))

function density_probe_witness(
    candidates::Vector{Dict{String,Any}},
    probes::Vector{Dict{String,Any}},
    left_id::String,
    right_id::String,
)
    by_id = Dict{String,Dict{String,Any}}(String(candidate["id"]) => candidate for candidate in candidates)
    left = by_id[left_id]
    right = by_id[right_id]
    rho_gap = rounded(norm(left["rho"] - right["rho"]), 15)
    tested = Any[]
    for probe in probes
        left_stats = measurement_stats(left["rho"], probe)
        right_stats = measurement_stats(right["rho"], probe)
        probe_gap = maximum(abs(a - b) for (a, b) in zip(left_stats, right_stats))
        push!(tested, Dict{String,Any}(
            "probe" => probe["name"],
            "left_stats" => left_stats,
            "right_stats" => right_stats,
            "max_gap" => probe_gap,
            "separates" => probe_gap > TOL,
        ))
    end
    tested_probe_max_gap = maximum(Float64(row["max_gap"]) for row in tested)
    Dict{String,Any}(
        "left_id" => left_id,
        "right_id" => right_id,
        "same_density_frobenius_gap" => rho_gap,
        "tested_probe_max_gap" => tested_probe_max_gap,
        "probe_rows" => tested,
        "separating_probes" => [String(row["probe"]) for row in tested if Bool(row["separates"])],
        "density_is_equivalence_class" => rho_gap <= TOL && tested_probe_max_gap <= TOL,
    )
end

function density_matrix_witness(candidates::Vector{Dict{String,Any}}, probes::Vector{Dict{String,Any}})
    by_id = Dict{String,Dict{String,Any}}(String(candidate["id"]) => candidate for candidate in candidates)
    left = by_id["ensemble_z_mixed"]
    right = by_id["ensemble_x_mixed"]
    witness = density_probe_witness(candidates, probes, "ensemble_z_mixed", "ensemble_x_mixed")
    Dict{String,Any}(
        "ensemble_A" => left["ensemble"],
        "ensemble_B" => right["ensemble"],
        "same_density_frobenius_gap" => witness["same_density_frobenius_gap"],
        "tested_probe_max_gap" => witness["tested_probe_max_gap"],
        "probe_rows" => witness["probe_rows"],
        "separating_probes" => witness["separating_probes"],
        "no_povm_separates_reason" => "Born statistics depend only on rho via Tr(E rho); identical rho gives identical statistics for every finite effect E.",
        "density_is_equivalence_class" => witness["density_is_equivalence_class"],
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
    probes = probe_family()
    candidates = candidate_configurations()
    coarse_m = Dict{String,Any}[probes["Z"]]
    enlarged_m = Dict{String,Any}[probes["Z"], probes["X"], probes["Y"]]
    empty_m = Dict{String,Any}[]

    q_coarse = quotient(candidates, coarse_m, "M_Z")
    q_enlarged = quotient(candidates, enlarged_m, "M_ZXY")
    q_empty = quotient(candidates, empty_m, "M_empty")

    f01_resolution_change = Float64(q_enlarged["class_count"] - q_coarse["class_count"])
    finite_quotient_built = all(quotient_ok(candidates, q) for q in [q_coarse, q_enlarged, q_empty])
    f01_load_bearing = length(coarse_m) < length(enlarged_m) &&
        q_coarse["class_count"] < q_enlarged["class_count"] &&
        f01_resolution_change > 0.0
    empty_probe_collapses_identity = q_empty["class_count"] == 1 && length(q_empty["classes"][1]["members"]) == length(candidates)

    rho0 = first(candidate["rho"] for candidate in candidates if candidate["id"] == "pure_z0")
    z_then_x_rows = sequential_joint_distribution(rho0, probes["Z"], probes["X"])
    x_then_z_rows = sequential_joint_distribution(rho0, probes["X"], probes["Z"])
    z_then_x = Float64[row["probability"] for row in z_then_x_rows]
    x_then_z = Float64[row["probability"] for row in x_then_z_rows]
    z_then_z_relabel_rows = sequential_joint_distribution(rho0, probes["Z"], probes["Z_relabel"])
    z_relabel_then_z_rows = sequential_joint_distribution(rho0, probes["Z_relabel"], probes["Z"])
    z_then_z_relabel = Float64[row["probability"] for row in z_then_z_relabel_rows]
    z_relabel_then_z = Float64[row["probability"] for row in z_relabel_then_z_rows]
    n01_order_gap = sequential_order_gap(z_then_x_rows, x_then_z_rows)
    commuting_order_gap = sequential_order_gap(z_then_z_relabel_rows, z_relabel_then_z_rows)
    commuting_raw_order_gap = l1_gap(z_then_z_relabel, z_relabel_then_z)
    commuting_projector_commutator_max_norm = max_projector_commutator_norm(probes["Z"], probes["Z_relabel"])
    noncommuting_projector_commutator_max_norm = max_projector_commutator_norm(probes["Z"], probes["X"])
    commuting_control_now_empirical = probes["Z"]["name"] != probes["Z_relabel"]["name"] &&
        commuting_projector_commutator_max_norm <= TOL &&
        commuting_order_gap <= TOL &&
        commuting_raw_order_gap > TOL
    n01_gate_not_tautological = commuting_control_now_empirical && n01_order_gap > 1.0e-9
    n01_load_bearing = n01_order_gap > 1.0e-9 && commuting_control_now_empirical

    density_witness = density_matrix_witness(candidates, enlarged_m)
    density_is_equivalence_class = Bool(density_witness["density_is_equivalence_class"])
    density_negative_control = density_probe_witness(candidates, enlarged_m, "pure_z0", "pure_x_plus")
    density_negative_control_separates = Bool(
        density_negative_control["same_density_frobenius_gap"] > TOL &&
        density_negative_control["tested_probe_max_gap"] > TOL &&
        !Bool(density_negative_control["density_is_equivalence_class"])
    )

    shared_scalars = Dict{String,Any}(
        "S_size" => Float64(length(candidates)),
        "M_coarse_probe_count" => Float64(length(coarse_m)),
        "M_enlarged_probe_count" => Float64(length(enlarged_m)),
        "coarse_class_count" => Float64(q_coarse["class_count"]),
        "enlarged_class_count" => Float64(q_enlarged["class_count"]),
        "empty_class_count" => Float64(q_empty["class_count"]),
        "f01_resolution_change" => f01_resolution_change,
        "n01_order_gap" => n01_order_gap,
        "commuting_order_gap" => commuting_order_gap,
        "commuting_raw_order_gap" => commuting_raw_order_gap,
        "commuting_projector_commutator_max_norm" => commuting_projector_commutator_max_norm,
        "noncommuting_projector_commutator_max_norm" => noncommuting_projector_commutator_max_norm,
        "density_same_rho_gap" => Float64(density_witness["same_density_frobenius_gap"]),
        "density_tested_probe_max_gap" => Float64(density_witness["tested_probe_max_gap"]),
        "density_negative_control_rho_gap" => Float64(density_negative_control["same_density_frobenius_gap"]),
        "density_negative_control_probe_max_gap" => Float64(density_negative_control["tested_probe_max_gap"]),
    )
    shared_booleans = Dict{String,Any}(
        "finite_quotient_built" => finite_quotient_built,
        "F01_load_bearing" => f01_load_bearing,
        "N01_load_bearing" => n01_load_bearing,
        "commuting_control_now_empirical" => commuting_control_now_empirical,
        "n01_gate_not_tautological" => n01_gate_not_tautological,
        "empty_probe_collapses_identity" => empty_probe_collapses_identity,
        "density_is_equivalence_class" => density_is_equivalence_class,
        "density_negative_control_separates" => density_negative_control_separates,
        "classification_is_scratch_diagnostic" => CLASSIFICATION == "scratch_diagnostic",
        "promotion_false" => true,
        "formal_admission_false" => true,
    )
    shared_strings = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "claim_ceiling" => CLAIM_CEILING,
    )
    result = Dict{String,Any}(
        "schema" => "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id" => OBJECT_ID,
        "sim_id" => OBJECT_ID,
        "name" => "foundation_rung0to3_distinguishability",
        "backend" => "julia",
        "generated_at" => string(Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS"), "Z"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => CLAIM_CEILING,
        "promotion_status" => "diagnostic_only",
        "eligible_consumers" => [],
        "blocked_consumers" => ["all promotion, formal admission, geometry, carrier, physics, or canonical consumers"],
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "constraint_probe",
        "jax_enable_x64" => nothing,
        "numpy_compute_used" => false,
        "numpy_imported" => false,
        "root_constraints_in_force" => ["F01", "N01", "a=a iff a~b"],
        "owner_doc_grounding" => [
            "OWNER_THESIS_AND_COSMOLOGY.md:13-32",
            "OWNER_THESIS_AND_COSMOLOGY.md:485-492",
            "NOMINALISM_IN_THIS_SYSTEM.md:199-223",
            "CONSTRAINT_SURFACE_AND_PROCESS.md:16-26",
        ],
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "required_tools" => ["JAX peer", "Julia", "LinearAlgebra"],
        "actual_tools_used" => ["Julia", "LinearAlgebra", "JSON"],
        "proof_surfaces_used" => [],
        "graph_surfaces_used" => [],
        "topology_surfaces_used" => [],
        "S" => Dict{String,Any}(
            "definition" => "finite set of candidate configurations represented by 2x2 density matrices",
            "size" => length(candidates),
            "candidate_ids" => [candidate["id"] for candidate in candidates],
            "candidate_descriptions" => Dict{String,Any}(candidate["id"] => candidate["description"] for candidate in candidates),
        ),
        "M" => Dict{String,Any}(
            "coarse" => ["Z"],
            "enlarged_approx_informationally_complete" => ["Z", "X", "Y"],
            "empty" => [],
            "all_probe_families_are_finite" => true,
        ),
        "indistinguishability_relation" => "a ~_M b iff every probe in M returns identical outcome statistics on a and b",
        "identity_rule_operationalization" => "a's identity is its class in S/~_M; empty M collapses all candidates to one no-contrast class",
        "quotient_S_mod_M_coarse" => q_coarse,
        "quotient_S_mod_M_enlarged" => q_enlarged,
        "quotient_S_mod_M_empty" => q_empty,
        "density_matrix_as_equivalence_class" => density_witness,
        "controls" => Dict{String,Any}(
            "F01_load_bearing" => Dict{String,Any}(
                "pass" => f01_load_bearing,
                "coarse_class_count" => q_coarse["class_count"],
                "enlarged_class_count" => q_enlarged["class_count"],
                "resolution_change" => f01_resolution_change,
                "interpretation" => "finite M bounds identity resolution; enlarging finite M refines the quotient",
            ),
            "N01_load_bearing" => Dict{String,Any}(
                "pass" => n01_load_bearing,
                "noncommuting_probe_order" => "Z_then_X vs X_then_Z",
                "noncommuting_order_gap" => n01_order_gap,
                "noncommuting_projector_commutator_max_norm" => noncommuting_projector_commutator_max_norm,
                "commuting_probe_order" => "Z_then_Z_relabel vs Z_relabel_then_Z",
                "commuting_order_gap" => commuting_order_gap,
                "commuting_raw_order_gap" => commuting_raw_order_gap,
                "commuting_projector_commutator_max_norm" => commuting_projector_commutator_max_norm,
                "commuting_control_now_empirical" => commuting_control_now_empirical,
                "n01_gate_not_tautological" => n01_gate_not_tautological,
                "Z_then_X_joint_stats" => z_then_x,
                "X_then_Z_joint_stats" => x_then_z,
                "Z_then_X_joint_distribution" => z_then_x_rows,
                "X_then_Z_joint_distribution" => x_then_z_rows,
                "Z_then_Z_relabel_joint_distribution" => z_then_z_relabel_rows,
                "Z_relabel_then_Z_joint_distribution" => z_relabel_then_z_rows,
            ),
            "empty_probe_collapses_identity" => Dict{String,Any}(
                "pass" => empty_probe_collapses_identity,
                "class_count" => q_empty["class_count"],
            ),
            "density_is_equivalence_class" => Dict{String,Any}(
                "pass" => density_is_equivalence_class,
                "witness" => density_witness,
                "negative_control" => Dict{String,Any}(
                    "pass" => density_negative_control_separates,
                    "expected_density_witness_pass" => false,
                    "actual_density_witness_pass" => density_negative_control["density_is_equivalence_class"],
                    "witness" => density_negative_control,
                ),
            ),
        ),
        "positive" => Dict{String,Any}(
            "finite_quotient_built" => Dict{String,Any}("pass" => finite_quotient_built),
            "F01_load_bearing" => Dict{String,Any}("pass" => f01_load_bearing),
            "N01_load_bearing" => Dict{String,Any}("pass" => n01_load_bearing),
            "empty_probe_collapses_identity" => Dict{String,Any}("pass" => empty_probe_collapses_identity),
            "density_is_equivalence_class" => Dict{String,Any}("pass" => density_is_equivalence_class),
            "density_negative_control_separates" => Dict{String,Any}("pass" => density_negative_control_separates),
        ),
        "negative" => Dict{String,Any}(
            "empty_probe_no_identity_control" => "with no contrast, quotient has one class over all candidates",
            "commuting_probe_order_control" => "distinct commuting sequential probes Z and relabeled diagonal Z have near-zero label-aligned order gap",
            "density_witness_negative_control" => "pure_z0 and pure_x_plus do not share rho and are separated by finite probes; the density-equivalence witness must fail",
        ),
        "graveyard_companions" => Dict{String,Any}(
            "over_resolved_identity_under_larger_finite_M" => f01_load_bearing,
            "commutative_order_control_kills_N01_gap" => commuting_control_now_empirical,
            "distinct_ensemble_decomposition_not_identity_split" => density_is_equivalence_class,
            "density_witness_not_always_true" => density_negative_control_separates,
        ),
        "boundary" => Dict{String,Any}(
            "classification_is_scratch_diagnostic" => CLASSIFICATION == "scratch_diagnostic",
            "promotion_allowed_false" => true,
            "formal_admission_allowed_false" => true,
            "claim_ceiling" => CLAIM_CEILING,
        ),
        "nearby_variants" => Dict{String,Any}(
            "coarse_probe_family" => "Z only",
            "enlarged_probe_family" => "Z, X, Y",
            "empty_probe_family" => "no probes",
            "commuting_order_control" => "Z with relabeled diagonal Z",
            "density_negative_control_pair" => "pure_z0 vs pure_x_plus",
        ),
        "why_not_v4_probes" => "Built on the SIM_TEMPLATE result shape but emitted as a v5 scratch diagnostic mirror receipt; no promotion claim.",
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "shared_strings" => shared_strings,
    )
    result["parity"] = parity_against_jax(result)
    result["finite_quotient_built"] = finite_quotient_built
    result["F01_load_bearing"] = f01_load_bearing
    result["N01_load_bearing"] = n01_load_bearing
    result["empty_probe_collapses_identity"] = empty_probe_collapses_identity
    result["density_is_equivalence_class"] = density_is_equivalence_class
    result["commuting_control_now_empirical"] = commuting_control_now_empirical
    result["n01_gate_not_tautological"] = n01_gate_not_tautological
    result["density_negative_control_separates"] = density_negative_control_separates
    result["n01_order_gap"] = n01_order_gap
    result["commuting_order_gap"] = commuting_order_gap
    result["f01_resolution_change"] = f01_resolution_change
    result["all_pass"] = finite_quotient_built &&
        f01_load_bearing &&
        n01_load_bearing &&
        commuting_control_now_empirical &&
        n01_gate_not_tautological &&
        empty_probe_collapses_identity &&
        density_is_equivalence_class &&
        density_negative_control_separates &&
        Bool(result["parity"]["within_1e_12"]) &&
        CLASSIFICATION == "scratch_diagnostic"
    result["stop_condition_fired"] = !Bool(result["all_pass"])
    result["result_summary"] = Dict{String,Any}(
        "finite_quotient_built" => finite_quotient_built,
        "F01_load_bearing" => f01_load_bearing,
        "N01_load_bearing" => n01_load_bearing,
        "commuting_control_now_empirical" => commuting_control_now_empirical,
        "n01_gate_not_tautological" => n01_gate_not_tautological,
        "empty_probe_collapses_identity" => empty_probe_collapses_identity,
        "density_is_equivalence_class" => density_is_equivalence_class,
        "density_negative_control_separates" => density_negative_control_separates,
        "parity_with_jax" => result["parity"]["within_1e_12"],
        "all_pass" => result["all_pass"],
    )
    result["criteria_checked"] = [
        "finite quotient S/~_M built",
        "F01 finite-probe resolution control refines quotient",
        "N01 sequential noncommuting probe order gap with commuting control",
        "N01 commuting control uses distinct commuting probes, not duplicate calls",
        "empty probe family collapses identity",
        "two distinct pure-state ensembles realize the same density class",
        "density witness negative control separates non-equal pure states",
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
        "n01_order_gap" => result["n01_order_gap"],
        "f01_resolution_change" => result["f01_resolution_change"],
    )))
    result["all_pass"] ? exit(0) : exit(1)
end

main()
