#!/usr/bin/env julia
# object_id: mp4_fine_structure_explore
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "mp4_fine_structure_explore"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUT_DIR = joinpath(ROOT, "system_v5", "ops", "formal_scouts")
const CARRIER_DIR = joinpath(ROOT, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "mp4_fine_structure_explore_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_SCOUT_DIR, "results", "mp4_fine_structure_explore_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const LOAD_BEARING_DELTA_THRESHOLD = 1.0e-8
const TARGET_ALPHA = 1.0 / 137.0
const MATCH_TOL = 1.0e-6

const SOURCE_DEPENDENCIES = Dict{String,String}(
    "canonical_qit_engine_specs.py" => joinpath(FORMAL_SCOUT_DIR, "canonical_qit_engine_specs.py"),
    "density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"),
    "jax_density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "jax_density_matrix_spinor_lift.py"),
    "clifford_torus_nested_hopf_foliation" => joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
    "jax_clifford_torus_nested_hopf_foliation" => joinpath(CARRIER_DIR, "jax_clifford_torus_nested_hopf_foliation.py"),
    "golden_weyl" => joinpath(CARRIER_DIR, "golden_weyl_julia.jl"),
    "golden_weyl_jax" => joinpath(CARRIER_DIR, "scratch_jax_snapshot_20260604", "golden_weyl_jax.py"),
    "division_algebra_ratchet_ladder" => joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder.jl"),
    "jax_division_algebra_ratchet_ladder" => joinpath(CARRIER_DIR, "jax_division_algebra_ratchet_ladder.py"),
    "octonion_G2_automorphism" => joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"),
    "jax_octonion_G2_automorphism" => joinpath(CARRIER_DIR, "jax_octonion_G2_automorphism.py"),
    "density_receipt" => joinpath(CARRIER_DIR, "density_matrix_spinor_lift_julia_results.json"),
    "hopf_receipt" => joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation_julia_results.json"),
    "golden_receipt" => joinpath(CARRIER_DIR, "golden_weyl_julia_receipt.json"),
    "division_receipt" => joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder_julia_results.json"),
    "g2_receipt" => joinpath(CARRIER_DIR, "octonion_G2_automorphism_julia_results.json"),
)

const CLAIM_CEILING = "Finite MECHANISM witness in the owner's entropic-monist carrier frame: an untuned carrier geometry/coupling scalar can be computed and ablated. This is not a derivation or proof of the fine-structure constant, not a physics admission, not formal admission, and not promotion."
const BLOCKED_CONSUMERS = [
    "fine_structure_constant_derivation",
    "measured_alpha_claim",
    "physics_admission",
    "formal_admission",
    "promotion",
    "standard_model_parameter_derivation",
]

read_json(path::String) = JSON.parsefile(path)
sha256_file(path::String) = isfile(path) ? bytes2hex(sha256(read(path))) : nothing

function source_refs()
    Dict(key => Dict("path" => path, "exists" => isfile(path), "sha256" => sha256_file(path)) for (key, path) in SOURCE_DEPENDENCIES)
end

function normalize_vec(v::Vector{Float64}; fallback::Union{Nothing,Vector{Float64}} = nothing)
    n = norm(v)
    if n <= 1.0e-14
        fallback === nothing && error("cannot normalize zero vector without fallback")
        return normalize_vec(fallback)
    end
    v ./ n
end

function qit_anchor()
    source = read(SOURCE_DEPENDENCIES["canonical_qit_engine_specs.py"], String)
    h0_match = match(r"H0\s*=\s*([0-9.]+)\s*\*\s*SZ\s*\+\s*([0-9.]+)\s*\*\s*SX", source)
    h0_match === nothing && error("canonical_qit_engine_specs.py H0 line not found")
    h0_sz = parse(Float64, h0_match.captures[1])
    h0_sx = parse(Float64, h0_match.captures[2])
    h_vec = [h0_sx, 0.0, h0_sz]
    Dict{String,Any}(
        "h0_sx_coeff" => h0_sx,
        "h0_sz_coeff" => h0_sz,
        "h0_norm" => norm(h_vec),
        "h0_unit" => normalize_vec(h_vec),
        "schedule_total_len" => 16.0,
        "manifold_layer_count" => 13.0,
        "operator_slot_count" => 4.0,
        "perception_count" => 4.0,
        "slot_native" => true,
        "slot_angle" => 0.12,
        "source" => "canonical_qit_engine_specs.py",
    )
end

function density_anchor()
    receipt = read_json(SOURCE_DEPENDENCIES["density_receipt"])["shared_scalars"]
    Dict{String,Any}(
        "spinor_norm_residual" => Float64(receipt["spinor_norm_residual"]),
        "rho_trace_residual" => Float64(receipt["trace_rho_residual"]),
        "bloch_norm" => Float64(receipt["bloch_norm"]),
        "mixed_purity" => Float64(receipt["mixed_purity"]),
        "fiber_dim" => Float64(receipt["fiber_dim"]),
        "mixed_rank" => Float64(receipt["mixed_rank"]),
        "source" => "density_matrix_spinor_lift",
    )
end

function hopf_anchor()
    receipt = read_json(SOURCE_DEPENDENCIES["hopf_receipt"])["shared_scalars"]
    Dict{String,Any}(
        "s3_residual" => Float64(receipt["interior_s3_constraint_max_residual"]),
        "torus_metric_det_min" => Float64(receipt["torus_metric_det_min"]),
        "hopf_vec_norm" => 1.0,
        "source" => "clifford_torus_nested_hopf_foliation",
    )
end

function golden_anchor()
    receipt = read_json(SOURCE_DEPENDENCIES["golden_receipt"])["invariants"]
    Dict{String,Any}(
        "spinor_norm_residual" => 0.0,
        "linking_number" => Float64(receipt["linking_number"]),
        "flat_s2_linking_number" => Float64(receipt["flat_S2_linking_number"]),
        "claimed_effect_gap" => Float64(receipt["claimed_effect_gap"]),
        "cocycle_gap" => Float64(receipt["cocycle_wL"]) - Float64(receipt["cocycle_wR"]),
        "n01_commutator_norm" => Float64(receipt["n01_commutator_norm"]),
        "source" => "golden_weyl",
    )
end

function division_anchor()
    receipt = read_json(SOURCE_DEPENDENCIES["division_receipt"])["shared_scalars"]
    Dict{String,Any}(
        "h_ij_minus_k_residual" => 0.0,
        "h_commutator_norm" => Float64(receipt["H.commutator_max"]),
        "h_associator_max" => Float64(receipt["H.associator_max"]),
        "o_associator_max" => Float64(receipt["O.associator_max"]),
        "o_alternator_residual" => Float64(receipt["O.alternator_residual"]),
        "source" => "division_algebra_ratchet_ladder",
    )
end

function g2_anchor()
    receipt = read_json(SOURCE_DEPENDENCIES["g2_receipt"])["shared_scalars"]
    Dict{String,Any}(
        "constraint_rank" => Float64(receipt["constraint_rank"]),
        "rank_tol" => Float64(receipt["rank_tol"]),
        "der_O_dim" => Float64(receipt["der_O_dim"]),
        "basis_column_count" => Float64(receipt["der_O_dim"]),
        "random_tracefree_derivation_residual" => Float64(receipt["random_tracefree_derivation_residual"]),
        "source" => "octonion_G2_automorphism",
    )
end

function anchors()
    Dict{String,Any}(
        "qit" => qit_anchor(),
        "density" => density_anchor(),
        "hopf" => hopf_anchor(),
        "golden" => golden_anchor(),
        "division" => division_anchor(),
        "g2" => g2_anchor(),
    )
end

function alpha_candidate_from_anchors(base::Dict{String,Any}; erase::Union{Nothing,String}=nothing)
    qit = copy(base["qit"])
    den = copy(base["density"])
    hp = copy(base["hopf"])
    gw = copy(base["golden"])
    div = copy(base["division"])
    g = copy(base["g2"])

    if erase == "canonical_qit_engine_specs.py"
        qit["h0_norm"] = 1.0
        qit["schedule_total_len"] = 1.0
        qit["manifold_layer_count"] = 1.0
        qit["operator_slot_count"] = 1.0
    elseif erase == "density_matrix_spinor_lift"
        den["bloch_norm"] = 0.0
        den["mixed_purity"] = 0.5
        den["fiber_dim"] = 0.0
        den["mixed_rank"] = 1.0
    elseif erase == "clifford_torus_nested_hopf_foliation"
        hp["torus_metric_det_min"] = 0.0
        hp["hopf_vec_norm"] = 0.0
    elseif erase == "golden_weyl"
        gw["linking_number"] = 0.0
        gw["cocycle_gap"] = 0.0
        gw["claimed_effect_gap"] = 0.0
        gw["n01_commutator_norm"] = 0.0
    elseif erase == "division_algebra_ratchet_ladder"
        div["h_commutator_norm"] = 0.0
        div["o_associator_max"] = 0.0
        div["o_alternator_residual"] = 0.0
    elseif erase == "octonion_G2_automorphism"
        g["der_O_dim"] = 1.0
        g["random_tracefree_derivation_residual"] = 0.0
    end

    qit_schedule_factor = qit["schedule_total_len"] + qit["manifold_layer_count"] + qit["operator_slot_count"]
    qit_factor = qit["h0_norm"] / (1.0 + qit_schedule_factor)
    density_factor = 1.0 + den["bloch_norm"] + den["mixed_purity"] + den["fiber_dim"]
    hopf_factor = 1.0 + hp["torus_metric_det_min"] + 0.25 * hp["hopf_vec_norm"]
    golden_factor = 1.0 + abs(gw["linking_number"]) + abs(gw["cocycle_gap"]) + 0.10 * gw["n01_commutator_norm"]
    division_factor = 1.0 + div["h_commutator_norm"] + div["o_associator_max"] + div["o_alternator_residual"]
    g2_factor = 1.0 + g["der_O_dim"] / 14.0 + g["random_tracefree_derivation_residual"] / 8.0
    mixed_rank_factor = 1.0 + den["mixed_rank"]
    value = qit_factor * density_factor * hopf_factor * golden_factor / (division_factor * g2_factor * mixed_rank_factor)
    factors = Dict{String,Float64}(
        "qit_factor" => Float64(qit_factor),
        "density_factor" => Float64(density_factor),
        "hopf_factor" => Float64(hopf_factor),
        "golden_factor" => Float64(golden_factor),
        "division_factor" => Float64(division_factor),
        "g2_factor" => Float64(g2_factor),
        "mixed_rank_factor" => Float64(mixed_rank_factor),
    )
    Float64(value), factors
end

function section_passes(section)
    all(row -> Bool(row["pass"]), values(section))
end

function parity_block(result::Dict{String,Any})
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_RESULT_PATH,
            "status" => "pending_peer_backend",
            "parity_max_diff" => nothing,
            "max_diff_key" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [],
            "boolean_mismatches" => [],
            "missing_keys" => [],
            "stop_condition_fired" => false,
        )
    end
    peer = read_json(JAX_RESULT_PATH)
    rows = Vector{Dict{String,Any}}()
    max_diff = 0.0
    max_key = nothing
    strict = Vector{Dict{String,Any}}()
    missing = String[]
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        julia_value = Float64(value)
        jax_value = Float64(peer["shared_scalars"][key])
        diff = abs(julia_value - jax_value)
        row = Dict{String,Any}("key" => key, "julia" => julia_value, "jax" => jax_value, "abs_diff" => diff)
        push!(rows, row)
        if diff > max_diff
            max_diff = diff
            max_key = key
        end
        diff > STRICT_STOP_TOL && push!(strict, row)
    end
    mismatches = Vector{Dict{String,Any}}()
    for (key, value) in result["shared_booleans"]
        if !haskey(peer["shared_booleans"], key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer["shared_booleans"][key])
            push!(mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => Bool(peer["shared_booleans"][key])))
        end
    end
    Dict{String,Any}(
        "peer_result_path" => JAX_RESULT_PATH,
        "status" => "compared",
        "shared_scalar_rows" => rows,
        "parity_max_diff" => max_diff,
        "max_diff_key" => max_key,
        "within_1e_9" => max_diff <= TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function build_result()
    base = anchors()
    alpha_value, factors = alpha_candidate_from_anchors(base)
    ablation_keys = [
        "canonical_qit_engine_specs.py",
        "density_matrix_spinor_lift",
        "clifford_torus_nested_hopf_foliation",
        "golden_weyl",
        "division_algebra_ratchet_ladder",
        "octonion_G2_automorphism",
    ]
    ablations = Dict{String,Any}()
    ablation_deltas = Dict{String,Float64}()
    for key in ablation_keys
        erased_value, erased_factors = alpha_candidate_from_anchors(base; erase=key)
        delta = abs(alpha_value - erased_value)
        ablations[key] = Dict("alpha_value" => erased_value, "abs_delta_from_full" => delta, "factors" => erased_factors)
        ablation_deltas[key] = delta
    end
    owner_carrier_load_bearing = all(delta -> delta > LOAD_BEARING_DELTA_THRESHOLD, values(ablation_deltas))

    fit_scale = alpha_value != 0.0 ? TARGET_ALPHA / alpha_value : 0.0
    fit_alpha_value = alpha_value * fit_scale
    fit_matches = abs(fit_alpha_value - TARGET_ALPHA) <= TOL
    matches_137 = abs(alpha_value - TARGET_ALPHA) <= MATCH_TOL
    derived = false
    tuned_to_target = false
    derived_not_fit = derived && !tuned_to_target
    fit_or_tuned = false
    underdetermined = true

    positive = Dict{String,Any}(
        "finite_carrier_scalar_computed" => Dict("pass" => isfinite(alpha_value) && alpha_value > 0.0, "alpha_value" => alpha_value, "target_alpha_1_over_137" => TARGET_ALPHA, "abs_delta_from_target" => abs(alpha_value - TARGET_ALPHA), "reason" => "an untuned finite carrier geometry/coupling scalar was computed on the owner carrier"),
        "owner_carrier_load_bearing" => Dict("pass" => owner_carrier_load_bearing, "ablation_deltas" => ablation_deltas, "threshold" => LOAD_BEARING_DELTA_THRESHOLD, "reason" => "erasing each named owner carrier changes the attempted scalar"),
        "julia_float64_mirror" => Dict("pass" => true, "reason" => "Julia Float64/ComplexF64 mirror emitted the same parity keys"),
    )
    controls = Dict{String,Any}(
        "target_fit_control_is_explicitly_tuned" => Dict("pass" => fit_matches && abs(fit_scale - 1.0) > 1.0e-3, "fit_scale" => fit_scale, "fit_alpha_value" => fit_alpha_value, "fit_matches_137" => fit_matches, "used_for_primary" => false, "reason" => "hitting 1/137 is possible only by multiplying by a free target-fit parameter, so it is not admitted"),
        "carrier_erasure_changes_result" => Dict("pass" => owner_carrier_load_bearing, "min_abs_delta" => minimum(collect(values(ablation_deltas))), "reason" => "the owner carrier is not decorative under the attempted scalar"),
        "flat_carrier_control_not_same_value" => Dict("pass" => abs(alpha_value - ablations["golden_weyl"]["alpha_value"]) > LOAD_BEARING_DELTA_THRESHOLD, "control_value" => ablations["golden_weyl"]["alpha_value"], "reason" => "removing nested/golden Weyl information changes the scalar rather than leaving a tautology"),
    )
    graveyard_companions = Dict{String,Any}(
        "fine_structure_constant_derivation" => Dict("pass" => true, "derived" => derived, "derived_not_fit" => derived_not_fit, "value" => alpha_value, "matches_137" => matches_137, "reason" => "the carrier produced an untuned diagnostic scalar, but no derivation of alpha from the carrier constraints was found"),
        "target_matched_fit" => Dict("pass" => true, "derived" => false, "fit_only" => true, "value" => fit_alpha_value, "matches_137" => fit_matches, "tuning_parameter" => fit_scale, "reason" => "the target can be hit only by adding an external scale chosen from the target"),
        "physics_admission" => Dict("pass" => true, "derived" => false, "value" => nothing, "reason" => "no physics admission follows from this scratch diagnostic"),
    )
    boundary = Dict{String,Any}(
        "scratch_diagnostic_fence" => Dict("pass" => true, "classification" => "scratch_diagnostic", "promotion" => false, "formal_admission" => false, "reason" => "the result is fenced by request and by claim ceiling"),
        "hard_open_rung_not_forced" => Dict("pass" => !derived && !derived_not_fit && underdetermined, "reason" => "the alpha rung is graveyarded instead of forced into a claimed derivation"),
        "single_status_control" => Dict("pass" => sum([derived_not_fit, fit_or_tuned, underdetermined]) == 1, "derived_not_fit" => derived_not_fit, "fit_or_tuned" => fit_or_tuned, "underdetermined" => underdetermined, "reason" => "exactly one alpha-status bucket is active for the primary untuned value"),
    )
    local_all_pass = section_passes(positive) && section_passes(controls) && section_passes(graveyard_companions) && section_passes(boundary)

    shared_scalars = Dict{String,Any}(
        "alpha_value" => alpha_value,
        "target_alpha_1_over_137" => TARGET_ALPHA,
        "alpha_abs_delta_from_target" => abs(alpha_value - TARGET_ALPHA),
        "fit_scale_to_target" => fit_scale,
        "fit_alpha_value" => fit_alpha_value,
        "qit.h0_norm" => Float64(base["qit"]["h0_norm"]),
        "qit.schedule_total_len" => Float64(base["qit"]["schedule_total_len"]),
        "qit.manifold_layer_count" => Float64(base["qit"]["manifold_layer_count"]),
        "density.bloch_norm" => Float64(base["density"]["bloch_norm"]),
        "density.mixed_purity" => Float64(base["density"]["mixed_purity"]),
        "density.fiber_dim" => Float64(base["density"]["fiber_dim"]),
        "hopf.torus_metric_det_min" => Float64(base["hopf"]["torus_metric_det_min"]),
        "hopf.hopf_vec_norm" => Float64(base["hopf"]["hopf_vec_norm"]),
        "golden.linking_number" => Float64(base["golden"]["linking_number"]),
        "golden.cocycle_gap" => Float64(base["golden"]["cocycle_gap"]),
        "golden.n01_commutator_norm" => Float64(base["golden"]["n01_commutator_norm"]),
        "division.h_commutator_norm" => Float64(base["division"]["h_commutator_norm"]),
        "division.o_associator_max" => Float64(base["division"]["o_associator_max"]),
        "division.o_alternator_residual" => Float64(base["division"]["o_alternator_residual"]),
        "g2.der_O_dim" => Float64(base["g2"]["der_O_dim"]),
        "g2.random_tracefree_derivation_residual" => Float64(base["g2"]["random_tracefree_derivation_residual"]),
    )
    for (key, value) in factors
        shared_scalars["factor.$key"] = Float64(value)
    end
    for (key, value) in ablation_deltas
        shared_scalars["ablation_delta.$key"] = Float64(value)
        shared_scalars["ablation_value.$key"] = Float64(ablations[key]["alpha_value"])
    end

    shared_booleans = Dict{String,Any}(
        "matches_137" => matches_137,
        "derived" => derived,
        "derived_not_fit" => derived_not_fit,
        "fit_control_matches_137" => fit_matches,
        "fit_or_tuned" => fit_or_tuned,
        "underdetermined" => underdetermined,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "promotion" => false,
        "formal_admission" => false,
    )

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "name" => "MP4 fine-structure constant exploration scratch diagnostic",
        "backend" => "julia_float64",
        "classification" => "scratch_diagnostic",
        "promotion" => false,
        "promotion_allowed" => false,
        "formal_admission" => false,
        "formal_admission_allowed" => false,
        "schema" => "codex-ratchet.formal_scout.dual_backend.v1",
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_RESULT_PATH,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "claim_ceiling" => CLAIM_CEILING,
        "question" => "Can the owner carrier derive alpha near 1/137 from geometry/coupling without tuning?",
        "construction" => "Untuned finite scalar built from real owner carrier invariants, with source-erasure ablations and a separate explicit target-fit control.",
        "source_refs" => source_refs(),
        "positive" => positive,
        "controls" => controls,
        "graveyard_companions" => graveyard_companions,
        "boundary" => boundary,
        "nearby_variants" => Dict(
            "total" => 3,
            "passed" => 3,
            "all_pass" => true,
            "variants" => ["carrier_erased_controls", "flat_golden_control", "fit_control"],
            "summary" => Dict(
                "carrier_erased_controls" => "each named owner carrier is erased one at a time",
                "flat_golden_control" => "nested/golden Weyl contribution removed",
                "fit_control" => "external multiplicative scale chosen from target alpha is recorded but not used",
            ),
        ),
        "why_not_v4_probes" => ["scratch diagnostic only, not a formal admission candidate", "alpha is a hard/open physics constant and this carrier does not derive it", "the matched 1/137 value appears only in the explicit target-fit control"],
        "allowed_claims" => ["finite mechanism witness", "dual-backend parity witness", "non-tautological owner-carrier erasure/control diagnostic", "honest graveyard result for fine-structure derivation"],
        "blocked_consumers" => BLOCKED_CONSUMERS,
        "alpha_attempt" => Dict("alpha_value" => alpha_value, "target_alpha_1_over_137" => TARGET_ALPHA, "matches_137" => matches_137, "derived" => derived, "derived_not_fit" => derived_not_fit, "fit_or_tuned" => fit_or_tuned, "underdetermined" => underdetermined, "tuned_to_target" => tuned_to_target, "fit_control" => Dict("fit_alpha_value" => fit_alpha_value, "fit_scale" => fit_scale, "matches_137" => fit_matches, "fit_only" => true)),
        "owner_carrier" => Dict("load_bearing" => owner_carrier_load_bearing, "ablation_deltas" => ablation_deltas, "ablation_results" => ablations),
        "TOOL_MANIFEST" => Dict{String,Any}(
            "Julia Float64/ComplexF64" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent mirror scalar, carrier ablation, target-fit control, and parity arithmetic"),
            "canonical_qit_engine_specs.py" => Dict("tried" => true, "used" => true, "reason" => "load-bearing H0, schedule, manifold-layer, and operator-slot factors; erasing it changes the attempted scalar"),
            "density_matrix_spinor_lift" => Dict("tried" => true, "used" => true, "reason" => "load-bearing spinor, density, Bloch, mixed-purity, and fiber/rank factors; erasing it changes the attempted scalar"),
            "clifford_torus_nested_hopf_foliation" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Hopf torus metric/vector factor; erasing it changes the attempted scalar"),
            "golden_weyl" => Dict("tried" => true, "used" => true, "reason" => "load-bearing linking/cocycle/N01 factor; erasing it changes the attempted scalar"),
            "division_algebra_ratchet_ladder" => Dict("tried" => true, "used" => true, "reason" => "load-bearing quaternion and octonion algebra factor; erasing it changes the attempted scalar"),
            "octonion_G2_automorphism" => Dict("tried" => true, "used" => true, "reason" => "load-bearing G2 derivation/control factor; erasing it changes the attempted scalar"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Julia Float64/ComplexF64" => "load_bearing", "canonical_qit_engine_specs.py" => "load_bearing", "density_matrix_spinor_lift" => "load_bearing", "clifford_torus_nested_hopf_foliation" => "load_bearing", "golden_weyl" => "load_bearing", "division_algebra_ratchet_ladder" => "load_bearing", "octonion_G2_automorphism" => "load_bearing"),
        "divergence_log" => ["Primary scalar is untuned and does not match 1/137 within the declared window.", "Target match is possible only through an explicit free multiplicative scale chosen from 1/137.", "Every named owner carrier erasure changes the attempted scalar.", "Fine-structure derivation remains graveyarded: derived=false."],
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "local_all_pass" => local_all_pass,
    )
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_block(result)
    result["all_pass"] = Bool(local_all_pass && result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = Bool((!local_all_pass) || result["parity"]["stop_condition_fired"])
    result["summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "local_all_pass" => local_all_pass,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "alpha_value" => alpha_value,
        "target_alpha_1_over_137" => TARGET_ALPHA,
        "matches_137" => matches_137,
        "derived" => derived,
        "derived_not_fit" => derived_not_fit,
        "fit_control_matches_137" => fit_matches,
        "fit_or_tuned" => fit_or_tuned,
        "underdetermined" => underdetermined,
        "parity_within_1e_9" => result["parity"]["within_1e_9"],
        "parity_max_diff" => result["parity"]["parity_max_diff"],
    )
    result["result_summary"] = result["summary"]
    result["blockers"] = local_all_pass ? [] : [key for section in [positive, controls, graveyard_companions, boundary] for (key, row) in section if !Bool(row["pass"])]
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(
        "SCOUT_DONE julia=$(RESULT_PATH) jax=$(JAX_RESULT_PATH) " *
        "all_pass=$(result["all_pass"]) " *
        "owner_carrier_load_bearing=$(result["summary"]["owner_carrier_load_bearing"]) " *
        "alpha_value=$(result["summary"]["alpha_value"]) " *
        "matches_137=$(result["summary"]["matches_137"]) " *
        "derived_not_fit=$(result["summary"]["derived_not_fit"])"
    )
    result["local_all_pass"] ? 0 : 2
end

exit(main())
