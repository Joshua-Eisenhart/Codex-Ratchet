#!/usr/bin/env julia
# object_id: r0_r1_r2_probe_quotient_micro_packet
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "r0_r1_r2_probe_quotient_micro_packet"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/r0_r1_r2_probe_quotient_micro_packet_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/r0_r1_r2_probe_quotient_micro_packet_results.json")
const TOL = 1.0e-12
const N01_TOL = 1.0e-9
const CLASSIFICATION = "scratch_diagnostic"
const ALLOWED_CLAIM = "finite probe-relative quotient packet exists/runs at scratch level."
const BLOCKED_CLAIMS = [
    "M(C) admission",
    "Axis0",
    "QIT engine",
    "physics",
    "SM",
    "GR",
    "alpha",
    "gravity",
    "chirality doctrine",
    "chemistry",
    "biology",
    "consciousness",
    "final manifold",
]
const CLAIM_CEILING = string(
    "Allowed only: finite probe-relative quotient packet exists/runs at scratch level. Blocked: ",
    join(BLOCKED_CLAIMS, "; "),
    ".",
)

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing mirror backend for finite support, finite probes, Adm_C filter, quotient classes, and controls",
    ),
    "LinearAlgebra" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing matrix traces, norms, eigenvalue checks, and sequential finite probe statistics",
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
    "pytorch" => Dict{String,Any}(
        "tried" => false,
        "used" => false,
        "reason" => "not used: explicit packet request forbids adding torch for the stale C8 rule",
    ),
    "numpy" => Dict{String,Any}(
        "tried" => false,
        "used" => false,
        "reason" => "not part of the Julia mirror and not used for compute",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "JSON" => "supportive",
    "JAX peer" => "load_bearing",
    "pytorch" => nothing,
    "numpy" => nothing,
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
        Dict{String,Any}("id" => "pure_z0", "description" => "pure finite support state z0", "rho" => rhos["z0"]),
        Dict{String,Any}("id" => "pure_z1", "description" => "pure finite support state z1", "rho" => rhos["z1"]),
        Dict{String,Any}("id" => "pure_x_plus", "description" => "pure finite support state x_plus", "rho" => rhos["x_plus"]),
        Dict{String,Any}("id" => "pure_x_minus", "description" => "pure finite support state x_minus", "rho" => rhos["x_minus"]),
        Dict{String,Any}("id" => "pure_y_plus", "description" => "pure finite support state y_plus", "rho" => rhos["y_plus"]),
        Dict{String,Any}("id" => "pure_y_minus", "description" => "pure finite support state y_minus", "rho" => rhos["y_minus"]),
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

l1_gap(left::Vector{Float64}, right::Vector{Float64}) = sum(abs(a - b) for (a, b) in zip(left, right))

function density_valid(rho::Matrix{ComplexF64})
    trace_gap = abs(rounded(real(tr(rho)), 15) - 1.0)
    hermitian_gap = rounded(norm(rho - rho'), 15)
    min_eig = rounded(minimum(real.(eigvals(Hermitian(rho)))), 15)
    Dict{String,Any}(
        "trace_gap" => trace_gap,
        "hermitian_gap" => hermitian_gap,
        "min_eigenvalue" => min_eig,
        "pass" => trace_gap <= TOL && hermitian_gap <= TOL && min_eig >= -TOL,
    )
end

function probe_valid(probe::Dict{String,Any}, candidates::Vector{Dict{String,Any}})
    effect_sum = zeros(ComplexF64, 2, 2)
    for effect in probe["effects"]
        effect_sum .+= effect
    end
    completeness_gap = rounded(norm(effect_sum - I2), 15)
    min_effect_eig = minimum(
        rounded(minimum(real.(eigvals(Hermitian(effect)))), 15)
        for effect in probe["effects"]
    )
    stat_rows = [measurement_stats(candidate["rho"], probe) for candidate in candidates]
    probability_rows_ok = all(
        abs(sum(row) - 1.0) <= TOL && all((-TOL <= value <= 1.0 + TOL) for value in row)
        for row in stat_rows
    )
    Dict{String,Any}(
        "probe" => probe["name"],
        "finite_outcome_count" => length(probe["effects"]),
        "completeness_gap" => completeness_gap,
        "min_effect_eigenvalue" => min_effect_eig,
        "probability_rows_ok" => probability_rows_ok,
        "pass" => completeness_gap <= TOL && min_effect_eig >= -TOL && probability_rows_ok,
    )
end

function composition_gap(candidate::Dict{String,Any}, first::Dict{String,Any}, second::Dict{String,Any})
    left = sequential_joint_stats(candidate["rho"], first, second)
    right = sequential_joint_stats(candidate["rho"], second, first)
    gap = l1_gap(left, right)
    Dict{String,Any}(
        "candidate_id" => candidate["id"],
        "first_then_second" => left,
        "second_then_first" => right,
        "order_gap_l1" => gap,
        "pass" => gap > N01_TOL,
    )
end

function reject_reason(finite_density_check::Dict{String,Any}, finite_probe_stats_ok::Bool, order::Dict{String,Any})
    if !Bool(finite_density_check["pass"])
        return "failed_finite_density_rule"
    end
    if !finite_probe_stats_ok
        return "failed_finite_probe_probability_rule"
    end
    if !Bool(order["pass"])
        return "failed_N01_order_gap_rule"
    end
    "failed_unclassified_rule"
end

function compute_adm_c(
    candidates::Vector{Dict{String,Any}},
    active_probes::Vector{Dict{String,Any}},
    first::Dict{String,Any},
    second::Dict{String,Any},
    label::String,
)
    probe_checks = Dict{String,Any}(check["probe"] => check for check in [probe_valid(probe, candidates) for probe in active_probes])
    rows = Any[]
    for candidate in candidates
        finite_density_check = density_valid(candidate["rho"])
        finite_probe_stats_ok = all(
            abs(sum(measurement_stats(candidate["rho"], probe)) - 1.0) <= TOL
            for probe in active_probes
        )
        order = composition_gap(candidate, first, second)
        passes = Bool(finite_density_check["pass"]) &&
            all(Bool(check["pass"]) for check in values(probe_checks)) &&
            finite_probe_stats_ok &&
            Bool(order["pass"])
        push!(rows, Dict{String,Any}(
            "id" => candidate["id"],
            "pass" => passes,
            "checks" => Dict{String,Any}(
                "F01_finite_density" => finite_density_check["pass"],
                "admissible_probe_stats" => finite_probe_stats_ok,
                "N01_order_gap_gt_threshold" => order["pass"],
            ),
            "density_check" => finite_density_check,
            "composition_order_gap_l1" => order["order_gap_l1"],
            "reject_reason" => passes ? nothing : reject_reason(finite_density_check, finite_probe_stats_ok, order),
        ))
    end
    members = [String(row["id"]) for row in rows if Bool(row["pass"])]
    non_members = [String(row["id"]) for row in rows if !Bool(row["pass"])]
    Dict{String,Any}(
        "name" => label,
        "membership_rule" => "s in S is in Adm_C iff rho_s is finite/normalized/positive, each active finite probe returns a valid finite probability row, and the active ordered composition witness has L1 order gap > 1e-9 for s",
        "active_probe_names" => [probe["name"] for probe in active_probes],
        "active_composition_witness" => "$(first["name"])_then_$(second["name"]) vs $(second["name"])_then_$(first["name"])",
        "member_count" => length(members),
        "members" => members,
        "non_members" => non_members,
        "membership_rows" => rows,
        "computed" => true,
    )
end

function finite_support_set(candidates::Vector{Dict{String,Any}})
    entries = Any[]
    for candidate in candidates
        entry = Dict{String,Any}(
            "id" => candidate["id"],
            "description" => candidate["description"],
            "rho" => matrix_parts(candidate["rho"]),
        )
        if haskey(candidate, "ensemble")
            entry["ensemble"] = candidate["ensemble"]
        end
        push!(entries, entry)
    end
    Dict{String,Any}(
        "definition" => "explicit finite support set S of candidate 2x2 matrix configurations",
        "size" => length(candidates),
        "entries" => entries,
    )
end

function finite_probe_family(probes::Vector{Dict{String,Any}})
    Dict{String,Any}(
        "definition" => "explicit finite probe family M; each probe has two finite effects",
        "size" => length(probes),
        "probe_names" => [probe["name"] for probe in probes],
        "entries" => [
            Dict{String,Any}(
                "name" => probe["name"],
                "outcome_labels" => probe["outcome_labels"],
                "effects" => [matrix_parts(effect) for effect in probe["effects"]],
            )
            for probe in probes
        ],
    )
end

function density_matrix_witness(candidates::Vector{Dict{String,Any}}, probes::Vector{Dict{String,Any}})
    by_id = Dict{String,Dict{String,Any}}(String(candidate["id"]) => candidate for candidate in candidates)
    left = by_id["ensemble_z_mixed"]
    right = by_id["ensemble_x_mixed"]
    rho_gap = rounded(norm(left["rho"] - right["rho"]), 15)
    tested_gaps = Float64[]
    for probe in probes
        left_stats = measurement_stats(left["rho"], probe)
        right_stats = measurement_stats(right["rho"], probe)
        push!(tested_gaps, maximum(abs(a - b) for (a, b) in zip(left_stats, right_stats)))
    end
    Dict{String,Any}(
        "ensemble_A" => left["ensemble"],
        "ensemble_B" => right["ensemble"],
        "same_density_frobenius_gap" => rho_gap,
        "tested_probe_max_gap" => maximum(tested_gaps),
        "reason" => "For the finite probes used here, equal rho gives equal Tr(E rho) rows.",
        "density_is_equivalence_class" => rho_gap <= TOL && maximum(tested_gaps) <= TOL,
    )
end

function active_constraints(probes::Vector{Dict{String,Any}})
    Dict{String,Any}(
        "C_name" => "F01 + N01 + admissible_probe_rules + admissible_composition_rules",
        "constraint_names" => [
            "F01_finite_support_set",
            "F01_finite_probe_family",
            "N01_noncommuting_order_sensitive_composition",
            "admissible_probe_rules",
            "admissible_composition_rules",
        ],
        "constraints" => [
            Dict{String,Any}("name" => "F01_finite_support_set", "rule" => "S is an explicit finite list of candidate configurations."),
            Dict{String,Any}("name" => "F01_finite_probe_family", "rule" => "M is an explicit finite list of finite-outcome probes.", "active_M" => [probe["name"] for probe in probes]),
            Dict{String,Any}("name" => "N01_noncommuting_order_sensitive_composition", "rule" => "At least one active ordered probe composition has nonzero L1 order gap on Adm_C.", "witness" => "Z_then_X vs X_then_Z"),
            Dict{String,Any}("name" => "admissible_probe_rules", "rule" => "Each effect list is finite, sums to identity within tolerance, and yields finite probability rows on S."),
            Dict{String,Any}("name" => "admissible_composition_rules", "rule" => "Only named finite probes in M may be sequentially composed; the finite outcome product is evaluated in both orders."),
        ],
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
    active_m = Dict{String,Any}[probes["Z"], probes["X"]]
    f01_erased_m = Dict{String,Any}[probes["Z"], probes["X"], probes["Y"]]
    empty_m = Dict{String,Any}[]

    adm_c = compute_adm_c(candidates, active_m, probes["Z"], probes["X"], "Adm_C")
    adm_set = Set(String.(adm_c["members"]))
    adm_candidates = Dict{String,Any}[candidate for candidate in candidates if String(candidate["id"]) in adm_set]
    q_active = quotient(candidates, active_m, "M_ZX")
    q_adm_active = quotient(adm_candidates, active_m, "Adm_C_M_ZX")
    q_f01_erased = quotient(candidates, f01_erased_m, "M_ZXY")
    q_empty = quotient(candidates, empty_m, "M_empty")

    n01_witness_rows = [composition_gap(candidate, probes["Z"], probes["X"]) for candidate in candidates]
    n01_order_gap = maximum(Float64(row["order_gap_l1"]) for row in n01_witness_rows)
    n01_control_fires = n01_order_gap > N01_TOL && adm_c["member_count"] > 0

    n01_erased_rows = Any[]
    for candidate in candidates
        noncommuting_gap = composition_gap(candidate, probes["Z"], probes["X"])["order_gap_l1"]
        erased_commuting_gap = composition_gap(candidate, probes["Z"], probes["Z"])["order_gap_l1"]
        push!(n01_erased_rows, Dict{String,Any}("id" => candidate["id"], "noncommuting_order_gap_l1" => noncommuting_gap, "order_erased_gap_l1" => erased_commuting_gap))
    end
    n01_noncommuting_gap_max = maximum(Float64(row["noncommuting_order_gap_l1"]) for row in n01_erased_rows)
    n01_erasure_gap = maximum(Float64(row["order_erased_gap_l1"]) for row in n01_erased_rows)
    n01_erasure_control_fires = n01_noncommuting_gap_max > N01_TOL && n01_erasure_gap <= TOL

    commutative_adm = compute_adm_c(candidates, active_m, probes["Z"], probes["Z"], "Adm_C_commutative_replacement")
    commutative_replacement_gap = maximum(
        Float64(composition_gap(candidate, probes["Z"], probes["Z"])["order_gap_l1"]) for candidate in candidates
    )
    q_commutative_replacement = quotient(candidates, Dict{String,Any}[probes["Z"]], "M_Z_commutative_replacement")
    commutative_replacement_fires = commutative_replacement_gap <= TOL &&
        commutative_adm["member_count"] == 0 &&
        q_commutative_replacement["class_count"] < q_active["class_count"]

    f01_control_fires = q_f01_erased["class_count"] > q_active["class_count"]
    probe_erasure_fires = q_empty["class_count"] == 1 && length(q_empty["classes"][1]["members"]) == length(candidates)
    quotient_built = all(quotient_ok(candidates, q) for q in [q_active, q_f01_erased, q_empty, q_commutative_replacement]) &&
        quotient_ok(adm_candidates, q_adm_active)
    adm_c_computed = Bool(adm_c["computed"]) && adm_c["member_count"] == length(adm_candidates) && adm_c["member_count"] > 0
    density_witness = density_matrix_witness(candidates, f01_erased_m)
    density_is_equivalence_class = Bool(density_witness["density_is_equivalence_class"])
    blocked_consumers_listed = BLOCKED_CLAIMS == [
        "M(C) admission",
        "Axis0",
        "QIT engine",
        "physics",
        "SM",
        "GR",
        "alpha",
        "gravity",
        "chirality doctrine",
        "chemistry",
        "biology",
        "consciousness",
        "final manifold",
    ]

    shared_scalars = Dict{String,Any}(
        "S_size" => Float64(length(candidates)),
        "M_active_probe_count" => Float64(length(active_m)),
        "M_f01_erased_proxy_probe_count" => Float64(length(f01_erased_m)),
        "Adm_C_size" => Float64(adm_c["member_count"]),
        "quotient_active_class_count" => Float64(q_active["class_count"]),
        "quotient_adm_c_class_count" => Float64(q_adm_active["class_count"]),
        "quotient_f01_erased_class_count" => Float64(q_f01_erased["class_count"]),
        "quotient_empty_class_count" => Float64(q_empty["class_count"]),
        "quotient_commutative_replacement_class_count" => Float64(q_commutative_replacement["class_count"]),
        "n01_order_gap" => Float64(n01_order_gap),
        "n01_erasure_order_gap" => Float64(n01_erasure_gap),
        "commutative_replacement_order_gap" => Float64(commutative_replacement_gap),
        "density_same_rho_gap" => Float64(density_witness["same_density_frobenius_gap"]),
        "density_tested_probe_max_gap" => Float64(density_witness["tested_probe_max_gap"]),
    )
    shared_booleans = Dict{String,Any}(
        "adm_c_computed" => adm_c_computed,
        "quotient_built" => quotient_built,
        "F01_control_fires" => f01_control_fires,
        "N01_control_fires" => n01_control_fires,
        "N01_erasure_control_fires" => n01_erasure_control_fires,
        "probe_erasure_fires" => probe_erasure_fires,
        "commutative_replacement_fires" => commutative_replacement_fires,
        "density_is_equivalence_class" => density_is_equivalence_class,
        "blocked_consumers_listed" => blocked_consumers_listed,
        "classification_is_scratch_diagnostic" => CLASSIFICATION == "scratch_diagnostic",
        "promotion_false" => true,
        "formal_admission_false" => true,
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
        "name" => "r0_r1_r2_probe_quotient_micro_packet",
        "version" => "1.0",
        "tier" => "r0_r1_r2_bottom_probe_quotient",
        "backend" => "julia",
        "generated_at" => string(Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS"), "Z"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "allowed_claims" => [ALLOWED_CLAIM],
        "claim_ceiling" => CLAIM_CEILING,
        "blocked_claims" => BLOCKED_CLAIMS,
        "promotion_status" => "diagnostic_only",
        "eligible_consumers" => [],
        "blocked_consumers" => BLOCKED_CLAIMS,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "constraint_probe",
        "purpose" => "Build the smallest bottom-level finite probe-relative quotient packet with computed Adm_C.",
        "scientific_question" => "Does the finite support/probe packet compute Adm_C and S/~_M with explicit controls at scratch level?",
        "branch_status_before_run" => "scratch_diagnostic_only",
        "carrier_layer" => "finite_2x2_matrix_support_only",
        "bridge_layer" => "none",
        "cut_layer" => "none",
        "law_or_candidate_tested" => "finite probe-relative quotient with computed C-admissible subset",
        "root_constraints_in_force" => ["F01", "N01"],
        "promotion_blockers" => BLOCKED_CLAIMS,
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
        "finite_support_set_S" => finite_support_set(candidates),
        "active_constraints_C" => active_constraints(active_m),
        "finite_probe_family_M" => finite_probe_family(active_m),
        "computed_admissible_subset_Adm_C" => adm_c,
        "quotient_S_mod_~M" => q_active,
        "quotient_Adm_C_mod_~M" => q_adm_active,
        "F01_erasure_control" => Dict{String,Any}(
            "pass" => f01_control_fires,
            "control" => "enlarge active finite M toward the withheld complete finite proxy M_ZXY",
            "active_class_count" => q_active["class_count"],
            "erased_proxy_class_count" => q_f01_erased["class_count"],
            "quotient_changed" => q_f01_erased["class_count"] != q_active["class_count"],
            "Adm_C_changed" => false,
            "erased_proxy_quotient" => q_f01_erased,
        ),
        "N01_erasure_control" => Dict{String,Any}(
            "pass" => n01_erasure_control_fires,
            "control" => "remove order sensitivity by comparing each finite sequence only with itself",
            "max_order_erased_gap_l1" => n01_erasure_gap,
            "composition_structure_collapses" => n01_erasure_gap <= TOL,
            "rows" => n01_erased_rows,
        ),
        "probe_erasure_control" => Dict{String,Any}(
            "pass" => probe_erasure_fires,
            "control" => "empty M",
            "quotient" => q_empty,
        ),
        "commutative_operation_replacement_control" => Dict{String,Any}(
            "pass" => commutative_replacement_fires,
            "control" => "replace active noncommuting X operation with commuting Z operation",
            "replacement_order_gap_l1" => commutative_replacement_gap,
            "Adm_C_response" => commutative_adm,
            "quotient_response" => q_commutative_replacement,
        ),
        "probe" => Dict{String,Any}(
            "indistinguishability_relation" => "a ~_M b iff every probe in finite M returns identical finite outcome rows on a and b",
            "identity_rule" => "identity is the quotient class in S/~_M at this finite probe resolution",
            "active_probe_checks" => [probe_valid(probe, candidates) for probe in active_m],
            "n01_witness_rows" => n01_witness_rows,
            "density_matrix_as_class_witness" => density_witness,
        ),
        "positive" => Dict{String,Any}(
            "adm_c_computed" => Dict{String,Any}("pass" => adm_c_computed),
            "quotient_built" => Dict{String,Any}("pass" => quotient_built),
            "F01_control_fires" => Dict{String,Any}("pass" => f01_control_fires),
            "N01_control_fires" => Dict{String,Any}("pass" => n01_control_fires, "n01_order_gap" => n01_order_gap),
            "probe_erasure_fires" => Dict{String,Any}("pass" => probe_erasure_fires),
            "commutative_replacement_fires" => Dict{String,Any}("pass" => commutative_replacement_fires),
            "density_is_equivalence_class" => Dict{String,Any}("pass" => density_is_equivalence_class),
        ),
        "negative" => Dict{String,Any}(
            "N01_erasure_control" => "order-erased comparison has zero order gap",
            "empty_probe_control" => "empty finite probe family collapses S to one quotient class",
            "commutative_replacement_control" => "Z replacing X removes the active N01 order-gap witness and empties Adm_C under the packet rule",
        ),
        "graveyard_companions" => Dict{String,Any}(
            "M_empty_identity_claim" => probe_erasure_fires,
            "commutative_replacement_keeps_N01" => false,
            "formal_admission_from_this_packet" => false,
        ),
        "boundary" => Dict{String,Any}(
            "classification_is_scratch_diagnostic" => CLASSIFICATION == "scratch_diagnostic",
            "promotion_allowed_false" => true,
            "formal_admission_allowed_false" => true,
            "allowed_claim" => ALLOWED_CLAIM,
            "blocked_claims" => BLOCKED_CLAIMS,
        ),
        "nearby_variants" => Dict{String,Any}(
            "active_M" => ["Z", "X"],
            "F01_erasure_proxy_M" => ["Z", "X", "Y"],
            "probe_erasure_M" => [],
            "commutative_replacement" => "Z replaces X in the composition witness",
        ),
        "why_not_v4_probes" => "This is a v5 formal scout scratch diagnostic mirror packet with no promotion or formal admission.",
        "required_negatives" => ["N01_erasure_control", "probe_erasure_control", "commutative_operation_replacement_control"],
        "negatives_run" => ["N01_erasure_control", "probe_erasure_control", "commutative_operation_replacement_control"],
        "kill_conditions" => [
            "Adm_C not computed",
            "quotient not a partition",
            "F01 control does not change quotient",
            "N01 order-gap absent",
            "empty M does not collapse quotient",
            "commutative replacement does not remove the order-gap witness",
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
    result["adm_c_computed"] = adm_c_computed
    result["quotient_built"] = quotient_built
    result["F01_control_fires"] = f01_control_fires
    result["N01_control_fires"] = n01_control_fires
    result["N01_erasure_control_fires"] = n01_erasure_control_fires
    result["probe_erasure_fires"] = probe_erasure_fires
    result["commutative_replacement_fires"] = commutative_replacement_fires
    result["n01_order_gap"] = n01_order_gap
    result["blocked_consumers_listed"] = blocked_consumers_listed
    result["all_pass"] = adm_c_computed &&
        quotient_built &&
        f01_control_fires &&
        n01_control_fires &&
        n01_erasure_control_fires &&
        probe_erasure_fires &&
        commutative_replacement_fires &&
        density_is_equivalence_class &&
        blocked_consumers_listed &&
        Bool(result["parity"]["within_1e_12"]) &&
        CLASSIFICATION == "scratch_diagnostic"
    result["stop_condition_fired"] = !Bool(result["all_pass"])
    result["pass_rule"] = "all shared packet booleans true and JAX/Julia parity within 1e-12"
    result["fail_rule"] = "any packet boolean false, missing peer parity, or parity over 1e-12"
    result["result_summary"] = Dict{String,Any}(
        "allowed_claim" => ALLOWED_CLAIM,
        "adm_c_computed" => adm_c_computed,
        "quotient_built" => quotient_built,
        "F01_control_fires" => f01_control_fires,
        "N01_control_fires" => n01_control_fires,
        "probe_erasure_fires" => probe_erasure_fires,
        "commutative_replacement_fires" => commutative_replacement_fires,
        "n01_order_gap" => n01_order_gap,
        "blocked_consumers_listed" => blocked_consumers_listed,
        "parity_with_jax" => result["parity"]["within_1e_12"],
        "all_pass" => result["all_pass"],
    )
    result["criteria_checked"] = [
        "finite_support_set_S explicit",
        "active_constraints_C explicit",
        "finite_probe_family_M explicit",
        "computed_admissible_subset_Adm_C computed",
        "quotient_S_mod_~M built",
        "F01_erasure_control fires",
        "N01_erasure_control fires",
        "probe_erasure_control fires",
        "commutative_operation_replacement_control fires",
        "JAX/Julia parity",
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
        "adm_c_computed" => result["adm_c_computed"],
        "quotient_built" => result["quotient_built"],
        "n01_order_gap" => result["n01_order_gap"],
    )))
    result["all_pass"] ? exit(0) : exit(1)
end

main()
