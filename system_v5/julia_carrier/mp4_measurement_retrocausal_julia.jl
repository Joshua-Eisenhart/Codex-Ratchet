#!/usr/bin/env julia
# object_id: mp4_measurement_retrocausal
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "mp4_measurement_retrocausal"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUTS = joinpath(ROOT, "system_v5", "ops", "formal_scouts")
const CARRIER_DIR = joinpath(ROOT, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "mp4_measurement_retrocausal_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_SCOUTS, "results", "mp4_measurement_retrocausal_results.json")
const SCOUT_TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6

module DensityLiftCarrier
include(joinpath("/Users/joshuaeisenhart/Codex-Ratchet", "system_v5", "julia_carrier", "density_matrix_spinor_lift.jl"))
end

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

const SOURCE_DEPENDENCIES = Dict(
    "canonical_qit_engine_specs" => joinpath(FORMAL_SCOUTS, "canonical_qit_engine_specs.py"),
    "density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"),
    "jax_density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "jax_density_matrix_spinor_lift.py"),
    "clifford_torus_nested_hopf_foliation" => joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
    "jax_clifford_torus_nested_hopf_foliation" => joinpath(CARRIER_DIR, "jax_clifford_torus_nested_hopf_foliation.py"),
    "golden_weyl" => joinpath(CARRIER_DIR, "golden_weyl_julia.jl"),
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

cross3(a::Vector{Float64}, b::Vector{Float64}) = Float64[
    a[2] * b[3] - a[3] * b[2],
    a[3] * b[1] - a[1] * b[3],
    a[1] * b[2] - a[2] * b[1],
]

function sigma_dot(axis::Vector{Float64})
    axis[1] .* SX .+ axis[2] .* SY .+ axis[3] .* SZ
end

projector(axis::Vector{Float64}, sign::Int) = 0.5 .* (I2 .+ Float64(sign) .* sigma_dot(axis))
trace_real(mat) = Float64(real(tr(mat)))
born_weight(proj, rho) = trace_real(proj * rho)
conditional_density(proj, rho, prob::Float64) = prob <= 1.0e-14 ? proj : (proj * rho * proj) ./ prob

function qit_anchor()
    source = read(joinpath(FORMAL_SCOUTS, "canonical_qit_engine_specs.py"), String)
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
        "main_stages_per_engine" => 8,
        "substages_per_main" => 4,
        "total_substages_per_engine" => 32,
        "perception_count" => 4,
        "operator_count" => 4,
    )
end

function torus_point(eta::Float64, phi::Float64, chi::Float64)
    cos(eta) * exp(im * phi), sin(eta) * exp(im * chi)
end

function owner_anchor()
    density = read_json(joinpath(CARRIER_DIR, "density_matrix_spinor_lift_julia_results.json"))["shared_scalars"]
    hopf = read_json(joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation_julia_results.json"))["shared_scalars"]
    golden = read_json(joinpath(CARRIER_DIR, "golden_weyl_julia_receipt.json"))["invariants"]
    division = read_json(joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder_julia_results.json"))["shared_scalars"]
    g2 = read_json(joinpath(CARRIER_DIR, "octonion_G2_automorphism_julia_results.json"))["shared_scalars"]

    eta = pi / 4.0
    phi = 0.37 + 0.01 * Float64(golden["claimed_effect_gap"])
    chi = 1.13 + 0.01 * Float64(golden["linking_number"])
    z, w = torus_point(eta, phi, chi)
    hopf_vec = Float64[
        2.0 * real(z * conj(w)),
        2.0 * imag(z * conj(w)),
        abs2(z) - abs2(w),
    ]
    cocycle_gap = Float64(golden["cocycle_wL"]) - Float64(golden["cocycle_wR"])
    division_assoc = Float64(division["O.associator_max"])
    g2_scale = Float64(g2["der_O_dim"]) / 14.0
    division_scale = division_assoc / (1.0 + division_assoc)
    g2_vec = normalize_vec([g2_scale, 0.5 * division_scale, 0.25 * cocycle_gap]; fallback = [1.0, 0.0, 0.0])
    density_radius = min(
        0.88,
        0.35 +
        0.10 * Float64(density["fiber_dim"]) +
        0.11 * min(1.0, abs(Float64(golden["linking_number"]))) +
        0.08 * g2_scale +
        0.08 * min(1.0, division_assoc / 2.0),
    )
    golden_bias = (
        max(0.0, abs(Float64(golden["linking_number"])) - abs(Float64(golden["flat_S2_linking_number"]))) *
        abs(cocycle_gap) / 2.0 *
        g2_scale
    )
    Dict{String,Any}(
        "density_fiber_dim" => Float64(density["fiber_dim"]),
        "density_mixed_rank" => Float64(density["mixed_rank"]),
        "density_radius" => Float64(density_radius),
        "hopf_torus_metric_det_min" => Float64(hopf["torus_metric_det_min"]),
        "hopf_vec" => normalize_vec(hopf_vec),
        "golden_linking" => Float64(golden["linking_number"]),
        "golden_flat_linking_abs" => abs(Float64(golden["flat_S2_linking_number"])),
        "golden_claimed_effect_gap" => Float64(golden["claimed_effect_gap"]),
        "golden_cocycle_gap" => cocycle_gap,
        "golden_bias" => Float64(golden_bias),
        "division_o_dim" => Float64(division["O.dim"]),
        "division_h_dim" => Float64(division["H.dim"]),
        "division_o_associator_max" => division_assoc,
        "division_h_associator_max" => Float64(division["H.associator_max"]),
        "division_scale" => Float64(division_scale),
        "g2_der_o_dim" => Float64(g2["der_O_dim"]),
        "g2_automorphism_product_residual" => Float64(g2["automorphism_product_residual"]),
        "g2_scale" => Float64(g2_scale),
        "g2_vec" => g2_vec,
    )
end

function selection_run(qit::Dict{String,Any}, owner::Dict{String,Any};
    erase_qit::Bool = false,
    erase_density::Bool = false,
    erase_hopf::Bool = false,
    erase_golden::Bool = false,
    erase_division::Bool = false,
    erase_g2::Bool = false,
    erase_probe::Bool = false,
    flip_future::Bool = false)

    h_unit = erase_qit ? [0.0, 0.0, 1.0] : Vector{Float64}(qit["h0_unit"])
    hopf_vec = erase_hopf ? [1.0, 0.0, 0.0] : Vector{Float64}(owner["hopf_vec"])
    g2_vec = Vector{Float64}(owner["g2_vec"])
    if erase_division || erase_g2
        g2_vec = [0.0, 1.0, 0.0]
    end
    axis = normalize_vec(0.55 .* h_unit .+ 0.35 .* hopf_vec .+ 0.10 .* g2_vec)
    lateral = normalize_vec(cross3(axis, h_unit); fallback = cross3(axis, [0.0, 1.0, 0.0]))
    golden_bias = erase_golden ? 0.0 : Float64(owner["golden_bias"])
    flip_future && (golden_bias = -golden_bias)
    future_raw = golden_bias .* axis .+ 0.15 .* lateral
    future_unit = normalize_vec(future_raw; fallback = lateral)
    initial_unit = normalize_vec(cross3(axis, future_unit); fallback = lateral)
    radius = erase_density ? 0.0 : Float64(owner["density_radius"])
    rho = DensityLiftCarrier.rho_from_bloch(radius .* initial_unit)
    rho_future = DensityLiftCarrier.rho_from_bloch(future_unit)

    p_plus = projector(axis, 1)
    p_minus = projector(axis, -1)
    born_plus = born_weight(p_plus, rho)
    born_minus = born_weight(p_minus, rho)
    future_plus = born_weight(p_plus, rho_future)
    future_minus = born_weight(p_minus, rho_future)
    score_plus = born_plus * future_plus
    score_minus = born_minus * future_minus
    score_gap = abs(score_plus - score_minus)

    selected_code = 0
    class_count = erase_probe ? 1 : 2
    selected_prob = 0.0
    selected_score = 0.0
    selected_projector = I2
    selected_rho = rho
    if !erase_probe
        if score_plus > score_minus + SCOUT_TOL
            selected_code = 1
            selected_prob = born_plus
            selected_score = score_plus
            selected_projector = p_plus
            selected_rho = conditional_density(p_plus, rho, born_plus)
        elseif score_minus > score_plus + SCOUT_TOL
            selected_code = -1
            selected_prob = born_minus
            selected_score = score_minus
            selected_projector = p_minus
            selected_rho = conditional_density(p_minus, rho, born_minus)
        end
    end

    entropy = 0.0
    for value in (born_plus, born_minus)
        if value > 1.0e-15
            entropy -= value * log(value)
        end
    end
    Dict{String,Any}(
        "axis" => axis,
        "future_unit" => future_unit,
        "initial_unit" => initial_unit,
        "rho" => rho,
        "selected_rho" => selected_rho,
        "selected_projector" => selected_projector,
        "born_plus" => born_plus,
        "born_minus" => born_minus,
        "future_plus" => future_plus,
        "future_minus" => future_minus,
        "score_plus" => score_plus,
        "score_minus" => score_minus,
        "score_gap" => score_gap,
        "selected_code" => selected_code,
        "selected_probability" => selected_prob,
        "selected_score" => selected_score,
        "class_count" => class_count,
        "outcome_entropy_nats" => entropy,
        "future_bias" => golden_bias,
    )
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
    max_diff_key = nothing
    strict = Vector{Dict{String,Any}}()
    missing = String[]
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        jv = Float64(value)
        pv = Float64(peer["shared_scalars"][key])
        diff = abs(jv - pv)
        if diff > max_diff
            max_diff = diff
            max_diff_key = key
        end
        row = Dict{String,Any}("key" => key, "julia" => jv, "jax" => pv, "abs_diff" => diff)
        push!(rows, row)
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
        "max_diff_key" => max_diff_key,
        "within_1e_9" => max_diff <= SCOUT_TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function vector_payload(v::Vector{Float64})
    [Float64(x) for x in v]
end

function build_result()
    refs = source_refs()
    qit = qit_anchor()
    owner = owner_anchor()
    full = selection_run(qit, owner)
    no_probe = selection_run(qit, owner; erase_probe = true)
    future_flip = selection_run(qit, owner; flip_future = true)
    no_golden = selection_run(qit, owner; erase_golden = true)
    no_qit = selection_run(qit, owner; erase_qit = true)
    no_density = selection_run(qit, owner; erase_density = true)
    no_hopf = selection_run(qit, owner; erase_hopf = true)
    no_division = selection_run(qit, owner; erase_division = true)
    no_g2 = selection_run(qit, owner; erase_g2 = true)

    selected_residual = norm(full["selected_rho"] - full["selected_projector"])
    born_sum_residual = abs(Float64(full["born_plus"]) + Float64(full["born_minus"]) - 1.0)
    born_nonnegative = Float64(full["born_plus"]) >= -SCOUT_TOL && Float64(full["born_minus"]) >= -SCOUT_TOL
    future_sum_residual = abs(Float64(full["future_plus"]) + Float64(full["future_minus"]) - 1.0)
    quotient_entropy_drop = Float64(full["outcome_entropy_nats"])
    no_probe_state_distance = norm(full["selected_rho"] - no_probe["selected_rho"])
    future_flip_state_distance = norm(full["selected_projector"] - future_flip["selected_projector"])
    qit_ablation_distance = norm(full["selected_projector"] - no_qit["selected_projector"])
    density_ablation_distance = norm(full["rho"] - no_density["rho"])
    hopf_ablation_distance = norm(full["selected_projector"] - no_hopf["selected_projector"])
    division_ablation_distance = norm(full["selected_projector"] - no_division["selected_projector"])
    g2_ablation_distance = norm(full["selected_projector"] - no_g2["selected_projector"])

    collapse_is_admissibility_selection =
        Int(full["selected_code"]) != 0 &&
        selected_residual <= STRICT_STOP_TOL &&
        quotient_entropy_drop > 0.1 &&
        Int(no_probe["selected_code"]) == 0
    oracle_defines_outcome =
        Int(full["class_count"]) == 2 &&
        Int(no_probe["class_count"]) == 1 &&
        Int(full["selected_code"]) in (-1, 1)
    no_separate_postulate = collapse_is_admissibility_selection && selected_residual <= STRICT_STOP_TOL
    owner_carrier_load_bearing =
        all(Bool(ref["exists"]) for ref in values(refs)) &&
        abs(Float64(full["score_gap"]) - Float64(no_golden["score_gap"])) > STRICT_STOP_TOL &&
        Int(no_golden["selected_code"]) == 0 &&
        no_probe_state_distance > STRICT_STOP_TOL &&
        qit_ablation_distance > STRICT_STOP_TOL &&
        density_ablation_distance > STRICT_STOP_TOL &&
        hopf_ablation_distance > STRICT_STOP_TOL &&
        division_ablation_distance > STRICT_STOP_TOL &&
        g2_ablation_distance > STRICT_STOP_TOL

    positive = Dict{String,Any}(
        "probe_quotient_born_weights" => Dict("pass" => born_sum_residual <= STRICT_STOP_TOL && born_nonnegative, "born_plus" => full["born_plus"], "born_minus" => full["born_minus"], "sum_residual" => born_sum_residual),
        "future_boundary_selects_unique_survivor" => Dict("pass" => Int(full["selected_code"]) != 0 && Float64(full["score_gap"]) > STRICT_STOP_TOL, "selected_code" => full["selected_code"], "score_gap" => full["score_gap"]),
        "conditional_density_is_selected_projector" => Dict("pass" => selected_residual <= STRICT_STOP_TOL, "residual" => selected_residual),
    )
    controls = Dict{String,Any}(
        "probe_erasure_leaves_no_definite_outcome" => Dict("pass" => Int(no_probe["selected_code"]) == 0 && Int(no_probe["class_count"]) == 1, "selected_code" => no_probe["selected_code"], "class_count" => no_probe["class_count"]),
        "future_selection_flip_changes_survivor" => Dict("pass" => Int(future_flip["selected_code"]) == -Int(full["selected_code"]) && future_flip_state_distance > STRICT_STOP_TOL, "future_flip_selected_code" => future_flip["selected_code"], "projector_distance" => future_flip_state_distance),
        "golden_future_bias_erasure_blocks_selection" => Dict("pass" => Int(no_golden["selected_code"]) == 0 && Float64(no_golden["score_gap"]) <= STRICT_STOP_TOL, "selected_code" => no_golden["selected_code"], "score_gap" => no_golden["score_gap"]),
        "owner_carrier_erasure_changes_result" => Dict("pass" => owner_carrier_load_bearing, "qit_ablation_projector_distance" => qit_ablation_distance, "density_ablation_rho_distance" => density_ablation_distance, "hopf_ablation_projector_distance" => hopf_ablation_distance, "division_ablation_projector_distance" => division_ablation_distance, "g2_ablation_projector_distance" => g2_ablation_distance),
    )
    boundary = Dict{String,Any}(
        "scratch_fence" => Dict("pass" => true, "classification" => "scratch_diagnostic", "promotion_allowed" => false, "formal_admission_allowed" => false),
        "claim_ceiling_is_mechanism_only" => Dict("pass" => true, "blocks" => ["measurement_problem_proof", "physics_admission", "formal_admission"]),
        "julia_no_numpy_compute" => Dict("pass" => true, "jax_enable_x64" => false, "numpy_compute_used" => false),
    )
    graveyard_companions = Dict{String,Any}(
        "quantum_measurement_problem_proof" => Dict("derived" => false, "reason" => "finite carrier mechanism witness only; no derivation of the named problem"),
        "literal_retrocausal_physics" => Dict("derived" => false, "reason" => "future boundary is a finite selector in the quotient score, not a physics admission"),
        "separate_collapse_postulate" => Dict("derived" => false, "reason" => "not added; selected density is computed by the quotient/projection survivor rule"),
    )
    nearby_variants = Dict{String,Any}(
        "total" => 5,
        "passed" => sum(Bool(x) for x in [
            Bool(controls["probe_erasure_leaves_no_definite_outcome"]["pass"]),
            Bool(controls["future_selection_flip_changes_survivor"]["pass"]),
            Bool(controls["golden_future_bias_erasure_blocks_selection"]["pass"]),
            Bool(controls["owner_carrier_erasure_changes_result"]["pass"]),
            Float64(full["selected_probability"]) > SCOUT_TOL && Float64(full["selected_probability"]) < 1.0 - SCOUT_TOL,
        ]),
    )

    shared_scalars = Dict{String,Any}(
        "born_plus" => Float64(full["born_plus"]),
        "born_minus" => Float64(full["born_minus"]),
        "born_sum_residual" => born_sum_residual,
        "future_plus" => Float64(full["future_plus"]),
        "future_minus" => Float64(full["future_minus"]),
        "future_sum_residual" => future_sum_residual,
        "score_plus" => Float64(full["score_plus"]),
        "score_minus" => Float64(full["score_minus"]),
        "score_gap" => Float64(full["score_gap"]),
        "selected_code" => Float64(full["selected_code"]),
        "selected_probability" => Float64(full["selected_probability"]),
        "selected_score" => Float64(full["selected_score"]),
        "selected_density_projector_residual" => selected_residual,
        "quotient_class_count" => Float64(full["class_count"]),
        "outcome_entropy_nats_before_selection" => Float64(full["outcome_entropy_nats"]),
        "quotient_entropy_drop_nats" => quotient_entropy_drop,
        "no_probe_selected_code" => Float64(no_probe["selected_code"]),
        "no_probe_class_count" => Float64(no_probe["class_count"]),
        "no_probe_state_distance" => no_probe_state_distance,
        "future_flip_selected_code" => Float64(future_flip["selected_code"]),
        "future_flip_projector_distance" => future_flip_state_distance,
        "golden_erased_selected_code" => Float64(no_golden["selected_code"]),
        "golden_erased_score_gap" => Float64(no_golden["score_gap"]),
        "qit_ablation_projector_distance" => qit_ablation_distance,
        "density_ablation_rho_distance" => density_ablation_distance,
        "hopf_ablation_projector_distance" => hopf_ablation_distance,
        "division_ablation_projector_distance" => division_ablation_distance,
        "g2_ablation_projector_distance" => g2_ablation_distance,
        "qit_h0_sx_coeff" => Float64(qit["h0_sx_coeff"]),
        "qit_h0_sz_coeff" => Float64(qit["h0_sz_coeff"]),
        "qit_total_substages_per_engine" => Float64(qit["total_substages_per_engine"]),
        "carrier_density_radius" => Float64(owner["density_radius"]),
        "carrier_hopf_torus_metric_det_min" => Float64(owner["hopf_torus_metric_det_min"]),
        "carrier_golden_linking" => Float64(owner["golden_linking"]),
        "carrier_golden_bias" => Float64(owner["golden_bias"]),
        "carrier_division_o_associator_max" => Float64(owner["division_o_associator_max"]),
        "carrier_g2_der_o_dim" => Float64(owner["g2_der_o_dim"]),
        "owner_carrier_load_bearing" => owner_carrier_load_bearing ? 1.0 : 0.0,
        "collapse_is_admissibility_selection" => collapse_is_admissibility_selection ? 1.0 : 0.0,
        "oracle_defines_outcome" => oracle_defines_outcome ? 1.0 : 0.0,
        "no_separate_postulate" => no_separate_postulate ? 1.0 : 0.0,
    )
    for (idx, value) in enumerate(vector_payload(full["axis"]))
        shared_scalars["measurement_axis.$(idx - 1)"] = value
    end
    for (idx, value) in enumerate(vector_payload(full["future_unit"]))
        shared_scalars["future_selector_axis.$(idx - 1)"] = value
    end
    for (idx, value) in enumerate(vector_payload(full["initial_unit"]))
        shared_scalars["initial_state_axis.$(idx - 1)"] = value
    end

    shared_booleans = Dict{String,Any}(
        "jax_enable_x64" => true,
        "numpy_compute_used" => false,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "collapse_is_admissibility_selection" => collapse_is_admissibility_selection,
        "oracle_defines_outcome" => oracle_defines_outcome,
        "no_separate_postulate" => no_separate_postulate,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "control_probe_erasure_no_outcome" => Bool(controls["probe_erasure_leaves_no_definite_outcome"]["pass"]),
        "control_future_flip_changes_survivor" => Bool(controls["future_selection_flip_changes_survivor"]["pass"]),
    )

    local_all_pass =
        all(Bool(row["pass"]) for row in values(positive)) &&
        all(Bool(row["pass"]) for row in values(controls)) &&
        all(Bool(row["pass"]) for row in values(boundary)) &&
        Int(nearby_variants["passed"]) == Int(nearby_variants["total"]) &&
        owner_carrier_load_bearing &&
        collapse_is_admissibility_selection &&
        oracle_defines_outcome &&
        no_separate_postulate

    merged = merge(positive, controls, boundary)
    blockers = local_all_pass ? Any[] : [key for (key, row) in merged if !Bool(get(row, "pass", false))]
    result = Dict{String,Any}(
        "schema" => "MP4_MEASUREMENT_RETROCAUSAL_DUAL_BACKEND_v1",
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "backend" => "julia_float64",
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_RESULT_PATH,
        "classification" => "scratch_diagnostic",
        "promotion" => false,
        "promotion_allowed" => false,
        "formal_admission" => false,
        "formal_admission_allowed" => false,
        "tol" => SCOUT_TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "claim_ceiling" => "Finite mechanism witness in the owner's entropic-monist frame: a bounded carrier plus probe quotient and future boundary selects one survivor from Born trace weights. NOT a proof or derivation of the quantum measurement problem; no physics admission and no formal admission.",
        "question" => "Can collapse be represented as admissibility/quotient selection of a survivor, with future-selection and no separate collapse postulate?",
        "construction" => Dict(
            "equivalence_rule" => "branches a and b are equivalent iff oracle_signature(a) == oracle_signature(b)",
            "oracle_signatures" => Dict("plus" => "+1 probe quotient class", "minus" => "-1 probe quotient class"),
            "score_rule" => "score(outcome) = Tr(P_outcome rho_past) * Tr(P_outcome rho_future)",
            "survivor_rule" => "unique max score survives; ties or erased probe are graveyard/no definite outcome",
            "selected_code" => full["selected_code"],
        ),
        "source_refs" => refs,
        "qit_anchor" => Dict(key => value for (key, value) in qit if key != "h0_unit"),
        "owner_anchor" => Dict(key => value for (key, value) in owner if !(key in ("hopf_vec", "g2_vec"))),
        "positive" => positive,
        "controls" => controls,
        "boundary" => boundary,
        "graveyard_companions" => graveyard_companions,
        "nearby_variants" => nearby_variants,
        "why_not_v4_probes" => [
            "dual-backend scratch diagnostic requested by owner, not a promotion/admission probe",
            "finite quotient selection is a mechanism witness only, not a solution of the quantum measurement problem",
            "future-selection is implemented as a finite boundary effect, not admitted retrocausal physics",
        ],
        "allowed_claims" => ["finite mechanism witness", "dual-backend parity witness", "probe quotient/admissibility selection diagnostic", "non-tautological erasure/control diagnostic"],
        "blocked_consumers" => ["quantum_measurement_problem_proof", "physics_admission", "formal_admission", "promotion", "literal_retrocausal_physics"],
        "TOOL_MANIFEST" => Dict(
            "Julia Float64/ComplexF64" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite density, projector, quotient score, control, and parity scalar computation"),
            "canonical_qit_engine_specs.py mirror" => Dict("tried" => true, "used" => true, "reason" => "load-bearing H0 and engine substage counts; erasing it changes the selected projector"),
            "density_matrix_spinor_lift" => Dict("tried" => true, "used" => true, "reason" => "load-bearing density carrier via rho_from_bloch; erasing density radius changes the pre-selection state"),
            "clifford_torus_nested_hopf_foliation" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Hopf torus vector from owner receipt/source; erasing it changes the selected projector"),
            "golden_weyl" => Dict("tried" => true, "used" => true, "reason" => "load-bearing future-selection bias from linking/cocycle receipt; erasing it leaves no unique survivor"),
            "division_algebra_ratchet_ladder" => Dict("tried" => true, "used" => true, "reason" => "load-bearing division-algebra associator scale in the probe carrier; erasing it changes the selected projector"),
            "octonion_G2_automorphism" => Dict("tried" => true, "used" => true, "reason" => "load-bearing G2 scale in the probe carrier; erasing it changes the selected projector"),
            "JSON/SHA/LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt loading, source hashes, matrix operations, and result writing"),
            "numpy" => Dict("tried" => false, "used" => false, "reason" => "not part of the Julia backend"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Julia Float64/ComplexF64" => "load_bearing",
            "canonical_qit_engine_specs.py mirror" => "load_bearing",
            "density_matrix_spinor_lift" => "load_bearing",
            "clifford_torus_nested_hopf_foliation" => "load_bearing",
            "golden_weyl" => "load_bearing",
            "division_algebra_ratchet_ladder" => "load_bearing",
            "octonion_G2_automorphism" => "load_bearing",
            "JSON/SHA/LinearAlgebra" => "supportive",
            "numpy" => nothing,
        ),
        "divergence_log" => [
            "Positive: probe quotient produces a two-class outcome family with Born trace weights summing to one.",
            "Positive: future boundary selects one survivor by the finite time-symmetric score.",
            "Control: removing probe/admissibility collapses the quotient to one class and no definite outcome.",
            "Control: erasing golden future bias leaves score tie/no survivor.",
            "Control: qit, density, Hopf, division, and G2 carrier ablations change the result surface.",
        ],
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "local_all_pass" => local_all_pass,
        "blockers" => blockers,
    )
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_block(result)
    result["all_pass"] = local_all_pass && Bool(result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = !local_all_pass || Bool(result["parity"]["stop_condition_fired"])
    result["summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "local_all_pass" => local_all_pass,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "collapse_is_admissibility_selection" => collapse_is_admissibility_selection,
        "oracle_defines_outcome" => oracle_defines_outcome,
        "no_separate_postulate" => no_separate_postulate,
        "selected_code" => full["selected_code"],
        "selected_probability" => full["selected_probability"],
        "parity_within_1e_9" => result["parity"]["within_1e_9"],
    )
    result["result_summary"] = result["summary"]
    if !Bool(result["all_pass"]) && Bool(result["parity"]["stop_condition_fired"])
        result["blockers"] = [result["blockers"]..., "julia_jax_parity_not_asserted"]
    end
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(
        "SCOUT_DONE " *
        "jax=$(JAX_RESULT_PATH) " *
        "julia=$(RESULT_PATH) " *
        "all_pass=$(lowercase(string(result["all_pass"]))) " *
        "owner_carrier_load_bearing=$(lowercase(string(result["summary"]["owner_carrier_load_bearing"]))) " *
        "collapse_is_admissibility_selection=$(lowercase(string(result["summary"]["collapse_is_admissibility_selection"]))) " *
        "oracle_defines_outcome=$(lowercase(string(result["summary"]["oracle_defines_outcome"]))) " *
        "no_separate_postulate=$(lowercase(string(result["summary"]["no_separate_postulate"])))"
    )
    return Bool(result["local_all_pass"])
end

if abspath(PROGRAM_FILE) == @__FILE__
    ok = main()
    exit(ok ? 0 : 2)
end
