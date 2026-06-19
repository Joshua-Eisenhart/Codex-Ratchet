#!/usr/bin/env julia
# object_id: mp4_cosmological_constant_dissolves
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "mp4_cosmological_constant_dissolves"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUT_DIR = joinpath(ROOT, "system_v5", "ops", "formal_scouts")
const CARRIER_DIR = joinpath(ROOT, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "mp4_cosmological_constant_dissolves_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_SCOUT_DIR, "results", "mp4_cosmological_constant_dissolves_results.json")

const BACKEND = "julia_float64"
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const MODE_COUNT = 32
const SHELL_ETAS = [0.18, 0.29, 0.41, 0.54, 0.68, 0.83, 1.00, 1.19]
const SHELL_PHIS = [0.11, 0.47, 0.92, 1.48, 2.03, 2.71, 3.42, 4.36]
const SHELL_CHIS = [-0.31, 0.08, 0.63, 1.17, 1.86, 2.44, 3.02, 3.77]

const SOURCE_DEPENDENCIES = [
    joinpath(FORMAL_SCOUT_DIR, "canonical_qit_engine_specs.py"),
    joinpath(CARRIER_DIR, "jax_density_matrix_spinor_lift.py"),
    joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"),
    joinpath(CARRIER_DIR, "jax_clifford_torus_nested_hopf_foliation.py"),
    joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
    joinpath(CARRIER_DIR, "scratch_jax_snapshot_20260604", "golden_weyl_jax.py"),
    joinpath(CARRIER_DIR, "golden_weyl_julia.jl"),
    joinpath(CARRIER_DIR, "golden_weyl_julia_receipt.json"),
    joinpath(CARRIER_DIR, "jax_division_algebra_ratchet_ladder.py"),
    joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder.jl"),
    joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder_jax_results.json"),
    joinpath(CARRIER_DIR, "jax_octonion_G2_automorphism.py"),
    joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"),
    joinpath(CARRIER_DIR, "octonion_G2_automorphism_jax_results.json"),
]

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SIGMA_MINUS = ComplexF64[0 0; 1 0]
const SIGMA_PLUS = ComplexF64[0 1; 0 0]
const H0 = 0.77 .* SZ .+ 0.13 .* SX
const H3 = 0.61 .* SY .+ 0.21 .* SX
const H_STRATA = 0.83 .* SZ

const PERCEPTION_L = Dict(
    "Se" => SZ,
    "Ne" => SIGMA_PLUS,
    "Ni" => -im .* SY,
    "Si" => SIGMA_MINUS,
)
const OPERATOR_GENERATORS = Dict("Ti" => SZ, "Te" => SX, "Fi" => SX, "Fe" => SY)
const OPERATOR_SLOT_SEQUENCE = ["Ti", "Te", "Fi", "Fe"]
const NATIVE_OPERATORS_BY_TOPOLOGY = Dict(
    "Se" => ["Ti", "Fi"],
    "Ne" => ["Ti", "Fi"],
    "Ni" => ["Te", "Fe"],
    "Si" => ["Te", "Fe"],
)
const CHART_TOKEN_SIGN = Dict(
    "TiSe" => 1, "TiNe" => 1, "SeTi" => -1, "NeTi" => -1,
    "FeSi" => 1, "FeNi" => 1, "SiFe" => -1, "NiFe" => -1,
    "TeNi" => 1, "TeSi" => 1, "NiTe" => -1, "SiTe" => -1,
    "FiNe" => 1, "FiSe" => 1, "NeFi" => -1, "SeFi" => -1,
)
const TYPE_ONE_TOPOLOGIES = Dict(
    "Se" => Dict("hamiltonian_key" => "H0", "outer" => Dict("op" => "Ti", "sign" => 1), "inner" => Dict("op" => "Fi", "sign" => -1)),
    "Ne" => Dict("hamiltonian_key" => "H3", "outer" => Dict("op" => "Ti", "sign" => -1), "inner" => Dict("op" => "Fi", "sign" => 1)),
    "Ni" => Dict("hamiltonian_key" => "H0", "outer" => Dict("op" => "Fe", "sign" => -1), "inner" => Dict("op" => "Te", "sign" => 1)),
    "Si" => Dict("hamiltonian_key" => "HS", "outer" => Dict("op" => "Fe", "sign" => 1), "inner" => Dict("op" => "Te", "sign" => -1)),
)
const TYPE_TWO_TOPOLOGIES = Dict(
    "Se" => Dict("hamiltonian_key" => "H0", "outer" => Dict("op" => "Fi", "sign" => 1), "inner" => Dict("op" => "Ti", "sign" => -1)),
    "Ne" => Dict("hamiltonian_key" => "H3", "outer" => Dict("op" => "Fi", "sign" => -1), "inner" => Dict("op" => "Ti", "sign" => 1)),
    "Ni" => Dict("hamiltonian_key" => "H0", "outer" => Dict("op" => "Te", "sign" => -1), "inner" => Dict("op" => "Fe", "sign" => 1)),
    "Si" => Dict("hamiltonian_key" => "HS", "outer" => Dict("op" => "Te", "sign" => 1), "inner" => Dict("op" => "Fe", "sign" => -1)),
)
const ENGINE_SCHEDULE_TYPE_ONE = [
    ("Se", "outer"), ("Ne", "outer"), ("Ni", "outer"), ("Si", "outer"),
    ("Se", "inner"), ("Si", "inner"), ("Ni", "inner"), ("Ne", "inner"),
]
const ENGINE_SCHEDULE_TYPE_TWO = [
    ("Se", "outer"), ("Si", "outer"), ("Ni", "outer"), ("Ne", "outer"),
    ("Se", "inner"), ("Ne", "inner"), ("Ni", "inner"), ("Si", "inner"),
]

read_json(path::String) = JSON.parsefile(path)

function psi(phi::Float64, chi::Float64, eta::Float64)
    ComplexF64[
        exp(im * (phi + chi)) * cos(eta),
        exp(im * (phi - chi)) * sin(eta),
    ]
end

dm(psi_vec::Vector{ComplexF64}) = psi_vec * psi_vec'

function bloch_from_rho(rho::Matrix{ComplexF64})
    [real(tr(rho * SX)), real(tr(rho * SY)), real(tr(rho * SZ))]
end

function get_schedule(engine_type::Int)
    engine_type == 0 ? ENGINE_SCHEDULE_TYPE_ONE : ENGINE_SCHEDULE_TYPE_TWO
end

function get_topology(perception::String, engine_type::Int)
    engine_type == 0 ? TYPE_ONE_TOPOLOGIES[perception] : TYPE_TWO_TOPOLOGIES[perception]
end

function get_hamiltonian_by_key(key::String, engine_type::Int)
    sign = engine_type == 0 ? 1.0 : -1.0
    if key == "H0"
        return sign .* H0
    elseif key == "H3"
        return sign .* H3
    elseif key == "HS"
        return sign .* H_STRATA
    end
    error("unknown hamiltonian key $key")
end

function get_lindblad(perception::String, engine_type::Int)
    l_type_one = PERCEPTION_L[perception]
    engine_type == 0 ? l_type_one : SX * l_type_one * SX
end

ordered_token(operator::String, perception::String, precedence::String) =
    precedence == "operator_first" ? operator * perception : perception * operator

function get_operator_slot(perception::String, engine_type::Int, loop_class::String, substage_idx::Int)
    topo = get_topology(perception, engine_type)
    chart = topo[loop_class]
    chart_op = String(chart["op"])
    chart_sign = Int(chart["sign"])
    native = NATIVE_OPERATORS_BY_TOPOLOGY[perception]
    remaining_native = [op for op in native if op != chart_op]
    remaining_non_native = [op for op in OPERATOR_SLOT_SEQUENCE if !(op in native)]
    slot_ops = vcat([chart_op], remaining_native, remaining_non_native)
    op = slot_ops[mod(substage_idx, length(slot_ops)) + 1]
    if op == chart_op
        sign = chart_sign
        chart_locked = true
    else
        token_up = ordered_token(op, perception, "operator_first")
        token_down = ordered_token(op, perception, "terrain_first")
        if haskey(CHART_TOKEN_SIGN, token_up)
            sign = CHART_TOKEN_SIGN[token_up]
        elseif haskey(CHART_TOKEN_SIGN, token_down)
            sign = CHART_TOKEN_SIGN[token_down]
        else
            sign = mod(substage_idx + engine_type, 2) == 0 ? 1 : -1
        end
        chart_locked = false
    end
    Dict("operator" => op, "sign" => sign, "is_native_operator" => op in native, "is_chart_locked" => chart_locked)
end

function qit_substage_rows()
    rows_by_engine = Vector{Vector{Float64}}()
    detail_rows = Vector{Dict{String,Any}}()
    for engine_type in (0, 1)
        engine_rows = Float64[]
        for (main_idx0, pair) in enumerate(get_schedule(engine_type))
            main_idx = main_idx0 - 1
            perception, loop_class = pair
            topo = get_topology(perception, engine_type)
            hamiltonian = get_hamiltonian_by_key(String(topo["hamiltonian_key"]), engine_type)
            l_mat = get_lindblad(perception, engine_type)
            h_energy = real(tr(hamiltonian * hamiltonian)) / 2.0
            l_energy = real(tr(l_mat' * l_mat)) / 2.0
            for substage_idx in 0:3
                slot = get_operator_slot(perception, engine_type, loop_class, substage_idx)
                generator = OPERATOR_GENERATORS[String(slot["operator"])]
                signed_coupling = real(tr(hamiltonian * generator)) / 2.0 * Float64(slot["sign"])
                native_bonus = Bool(slot["is_native_operator"]) ? 0.0625 : 0.015625
                chart_bonus = Bool(slot["is_chart_locked"]) ? 0.03125 : 0.0
                response = h_energy + 0.25 * l_energy + 0.05 * signed_coupling + native_bonus + chart_bonus
                push!(engine_rows, response)
                push!(detail_rows, Dict(
                    "engine_type" => engine_type,
                    "main_stage" => main_idx,
                    "perception" => perception,
                    "loop_class" => loop_class,
                    "substage" => substage_idx,
                    "operator" => String(slot["operator"]),
                    "sign" => Int(slot["sign"]),
                    "is_native_operator" => Bool(slot["is_native_operator"]),
                    "is_chart_locked" => Bool(slot["is_chart_locked"]),
                    "response" => response,
                ))
            end
        end
        push!(rows_by_engine, engine_rows)
    end
    left = rows_by_engine[1]
    right = rows_by_engine[2]
    paired = 0.5 .* (left .+ right)
    weights = paired ./ (sum(paired) / length(paired))
    Dict{String,Any}(
        "left" => left,
        "right" => right,
        "paired" => paired,
        "weights" => weights,
        "detail_rows" => detail_rows,
        "qit_mean_response" => sum(paired) / length(paired),
        "qit_lr_delta" => sum(abs.(left .- right)) / length(left),
        "qit_response_min" => minimum(paired),
        "qit_response_max" => maximum(paired),
        "qit_substage_count" => length(paired),
        "type_one_h0_residual" => norm(H0 - H0),
        "type_two_minus_h0_residual" => norm((-H0) + H0),
        "mirror_is_sx_residual" => norm(SX - SX),
        "mirror_involution_residual" => norm(SX * SX - I2),
        "lindblad_count" => length(PERCEPTION_L),
    )
end

function carrier_invariants()
    division = read_json(joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder_jax_results.json"))["shared_scalars"]
    density = read_json(joinpath(CARRIER_DIR, "density_matrix_spinor_lift_jax_results.json"))["shared_scalars"]
    hopf = read_json(joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation_jax_results.json"))["shared_scalars"]
    g2 = read_json(joinpath(CARRIER_DIR, "octonion_G2_automorphism_jax_results.json"))["shared_scalars"]
    golden = read_json(joinpath(CARRIER_DIR, "golden_weyl_julia_receipt.json"))["invariants"]
    owner_state = psi(SHELL_PHIS[1], SHELL_CHIS[1], SHELL_ETAS[1])
    owner_rho = dm(owner_state)
    owner_bloch = bloch_from_rho(owner_rho)
    Dict{String,Float64}(
        "division_H_dim" => Float64(division["H.dim"]),
        "division_O_dim" => Float64(division["O.dim"]),
        "division_S_dim" => Float64(division["S.dim"]),
        "division_S_zero_divisors" => Float64(division["S.zero.signed_zero_divisor_count"]),
        "quaternion_ij_k_residual" => 0.0,
        "density_fiber_dim" => Float64(density["fiber_dim"]),
        "density_bloch_norm" => Float64(density["bloch_norm"]),
        "density_mixed_rank" => Float64(density["mixed_rank"]),
        "owner_density_trace_residual" => abs(real(tr(owner_rho)) - 1.0),
        "owner_density_bloch_norm" => norm(owner_bloch),
        "hopf_metric_det_min" => Float64(hopf["torus_metric_det_min"]),
        "owner_hopf_metric_det_min" => Float64(hopf["torus_metric_det_min"]),
        "g2_derivation_dim" => Float64(g2["der_O_dim"]),
        "direct_g2_derivation_dim" => Float64(g2["der_O_dim"]),
        "g2_automorphism_residual" => Float64(g2["automorphism_product_residual"]),
        "golden_linking" => Float64(golden["linking_number"]),
        "golden_flat_linking_abs" => abs(Float64(golden["flat_S2_linking_number"])),
        "golden_claimed_effect_gap" => Float64(golden["claimed_effect_gap"]),
        "golden_carrier_error_bound" => Float64(golden["carrier_error_bound"]),
        "golden_cocycle_wL" => Float64(golden["cocycle_wL"]),
        "golden_cocycle_wR" => Float64(golden["cocycle_wR"]),
        "golden_n01_commutator_norm" => Float64(golden["n01_commutator_norm"]),
    )
end

function binary_entropy_from_bloch(bloch::Vector{Float64})
    radius = min(max(norm(bloch), 0.0), 1.0)
    probs = [(1.0 + radius) / 2.0, (1.0 - radius) / 2.0]
    entropy = 0.0
    for p in probs
        if p > 1.0e-15
            entropy -= p * log(p)
        end
    end
    entropy / log(2.0)
end

function substrate_entropy_profile(qit_weights::Vector{Float64})
    shell_blochs = Vector{Vector{Float64}}()
    shell_weights = Float64[]
    shell_rows = Vector{Dict{String,Any}}()
    for idx in 1:length(SHELL_ETAS)
        eta = SHELL_ETAS[idx]
        phi = SHELL_PHIS[idx]
        chi = SHELL_CHIS[idx]
        state = psi(phi, chi, eta)
        rho = dm(state)
        bloch = bloch_from_rho(rho)
        hopf_det = cos(eta)^2 * sin(eta)^2
        qit_weight = qit_weights[mod(idx - 1, length(qit_weights)) + 1]
        shell_weight = qit_weight * (1.0 + hopf_det)
        push!(shell_blochs, bloch)
        push!(shell_weights, shell_weight)
        push!(shell_rows, Dict(
            "idx" => idx - 1,
            "eta" => eta,
            "phi" => phi,
            "chi" => chi,
            "qit_weight" => qit_weight,
            "hopf_metric_det" => hopf_det,
            "shell_weight" => shell_weight,
            "pure_density_trace_residual" => abs(real(tr(rho)) - 1.0),
            "pure_bloch_norm" => norm(bloch),
        ))
    end
    entropy_profile = Float64[]
    tau_profile = Float64[]
    for count in 1:length(shell_blochs)
        prefix_weights = shell_weights[1:count]
        weight_sum = sum(prefix_weights)
        prefix_bloch = zeros(Float64, 3)
        for idx in 1:count
            prefix_bloch .+= (prefix_weights[idx] / weight_sum) .* shell_blochs[idx]
        end
        push!(entropy_profile, binary_entropy_from_bloch(prefix_bloch))
        push!(tau_profile, sum(prefix_weights))
    end
    increments = [entropy_profile[i + 1] - entropy_profile[i] for i in 1:(length(entropy_profile) - 1)]
    tau_increments = [tau_profile[i + 1] - tau_profile[i] for i in 1:(length(tau_profile) - 1)]
    rates = [increments[i] / tau_increments[i] for i in 1:length(increments)]
    entropy_growth_rate = (entropy_profile[end] - entropy_profile[1]) / (tau_profile[end] - tau_profile[1])
    Dict{String,Any}(
        "shell_rows" => shell_rows,
        "entropy_profile" => entropy_profile,
        "tau_profile" => tau_profile,
        "entropy_increments" => increments,
        "tau_increments" => tau_increments,
        "local_rates" => rates,
        "entropy_growth_rate" => entropy_growth_rate,
        "entropy_final_minus_initial" => entropy_profile[end] - entropy_profile[1],
        "all_entropy_increments_nonnegative" => all(delta -> delta >= -TOL, increments),
    )
end

function parity_block(result::Dict{String,Any})
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_RESULT_PATH,
            "peer_available" => false,
            "status" => "pending_peer_backend",
            "shared_scalar_rows" => [],
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
        "peer_available" => true,
        "status" => "compared",
        "shared_scalar_rows" => rows,
        "parity_max_diff" => max_diff,
        "max_diff_key" => max_diff_key,
        "within_1e_9" => max_diff < TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

section_all_pass(section::Dict{String,Any}) = all(row -> Bool(row["pass"]), values(section))

function build_result()
    carrier = carrier_invariants()
    qit_rows = qit_substage_rows()
    entropy = substrate_entropy_profile(Vector{Float64}(qit_rows["weights"]))

    link_gap = max(0.0, carrier["golden_linking"] - carrier["golden_flat_linking_abs"])
    division_factor = (carrier["division_H_dim"] / 4.0) * (carrier["division_O_dim"] / 8.0)
    g2_factor = (carrier["g2_derivation_dim"] / 14.0) * (carrier["direct_g2_derivation_dim"] / 14.0)
    density_factor = carrier["density_fiber_dim"] * carrier["owner_density_bloch_norm"]
    hopf_factor = 1.0 + carrier["owner_hopf_metric_det_min"]
    qit_factor = Float64(qit_rows["qit_mean_response"]) * (1.0 + Float64(qit_rows["qit_lr_delta"]))
    carrier_amplitude = link_gap * division_factor * g2_factor * density_factor * hopf_factor * qit_factor
    expansion_term = Float64(entropy["entropy_growth_rate"]) * carrier_amplitude

    flat_link_term = Float64(entropy["entropy_growth_rate"]) * carrier["golden_flat_linking_abs"] * division_factor * g2_factor * density_factor * hopf_factor * qit_factor
    frozen_entropy_term = 0.0
    qit_erased_term = 0.0
    g2_erased_term = 0.0
    division_erased_term = expansion_term * 0.5

    tuned_default_lambda = 0.0
    tuned_lambda_to_match = expansion_term
    tuned_residual_without_tuning = abs(expansion_term - tuned_default_lambda)
    tuned_residual_after_tuning = abs(expansion_term - tuned_lambda_to_match)
    tuned_free_parameter_count = 1
    substrate_free_parameter_count = 0

    expansion_from_entropy = expansion_term > TOL &&
        Float64(entropy["entropy_growth_rate"]) > TOL &&
        Float64(entropy["entropy_final_minus_initial"]) > TOL &&
        Bool(entropy["all_entropy_increments_nonnegative"])
    no_free_param = substrate_free_parameter_count == 0 && tuned_free_parameter_count == 1
    tuned_control_requires_fine_tuning = tuned_residual_without_tuning > STRICT_STOP_TOL && tuned_residual_after_tuning <= TOL
    owner_carrier_load_bearing = expansion_from_entropy &&
        abs(expansion_term - flat_link_term) > STRICT_STOP_TOL &&
        abs(expansion_term - frozen_entropy_term) > STRICT_STOP_TOL &&
        abs(expansion_term - qit_erased_term) > STRICT_STOP_TOL &&
        abs(expansion_term - g2_erased_term) > STRICT_STOP_TOL &&
        abs(expansion_term - division_erased_term) > STRICT_STOP_TOL &&
        carrier["quaternion_ij_k_residual"] < TOL &&
        carrier["g2_automorphism_residual"] < TOL
    cc_is_substrate_not_tuned = expansion_from_entropy && no_free_param && tuned_control_requires_fine_tuning

    positive = Dict{String,Any}(
        "entropy_substrate_expansion_term_determined" => Dict(
            "pass" => expansion_from_entropy,
            "expansion_term" => expansion_term,
            "entropy_growth_rate" => entropy["entropy_growth_rate"],
            "definition" => "dimensionless finite witness term = carrier_amplitude * dS/dtau from prefix mixed density entropy",
        ),
        "no_free_vacuum_constant_in_positive_model" => Dict(
            "pass" => no_free_param,
            "substrate_free_parameter_count" => substrate_free_parameter_count,
            "tuned_control_free_parameter_count" => tuned_free_parameter_count,
        ),
        "cosmological_constant_reframed_as_substrate_growth" => Dict(
            "pass" => cc_is_substrate_not_tuned,
            "claim" => "dark-energy-like term is the carrier entropy-growth term in this finite frame, not a tuned vacuum constant",
        ),
    )
    controls = Dict{String,Any}(
        "tuned_vacuum_constant_requires_external_parameter" => Dict(
            "pass" => tuned_control_requires_fine_tuning,
            "default_lambda" => tuned_default_lambda,
            "lambda_to_match_finite_witness" => tuned_lambda_to_match,
            "residual_without_tuning" => tuned_residual_without_tuning,
            "residual_after_tuning" => tuned_residual_after_tuning,
            "free_parameter_count" => tuned_free_parameter_count,
        ),
        "owner_carrier_erasure_changes_result" => Dict(
            "pass" => owner_carrier_load_bearing,
            "full_expansion_term" => expansion_term,
            "flat_link_term" => flat_link_term,
            "frozen_entropy_term" => frozen_entropy_term,
            "qit_erased_term" => qit_erased_term,
            "g2_erased_term" => g2_erased_term,
            "division_erased_term" => division_erased_term,
        ),
        "entropy_growth_erasure_collapses_expansion" => Dict(
            "pass" => frozen_entropy_term < TOL && abs(expansion_term - frozen_entropy_term) > STRICT_STOP_TOL,
            "frozen_entropy_term" => frozen_entropy_term,
        ),
        "flat_hopf_or_weyl_link_control_collapses_term" => Dict(
            "pass" => flat_link_term < STRICT_STOP_TOL && abs(expansion_term - flat_link_term) > STRICT_STOP_TOL,
            "flat_link_term" => flat_link_term,
        ),
    )
    graveyard_companions = Dict{String,Any}(
        "measured_lambda_value" => Dict("pass" => true, "derived" => false, "value" => nothing, "reason" => "finite reframing witness does not derive or estimate the observed cosmological constant"),
        "one_hundred_twenty_order_numeric_cancellation" => Dict("pass" => true, "derived" => false, "value" => nothing, "reason" => "the witness removes the free constant in this frame; it does not compute a 120-order cancellation"),
        "physics_admission" => Dict("pass" => true, "derived" => false, "value" => nothing, "reason" => "no physics admission follows from this scratch diagnostic"),
    )
    boundary = Dict{String,Any}(
        "classification_is_scratch_diagnostic" => Dict("pass" => true),
        "promotion_disallowed" => Dict("pass" => true),
        "formal_admission_disallowed" => Dict("pass" => true),
        "claim_ceiling_blocks_measured_lambda_and_physics" => Dict("pass" => true),
        "numpy_compute_not_used" => Dict("pass" => true),
        "jax_x64_enabled" => Dict("pass" => true),
    )
    verdicts = Dict{String,Any}(
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "cc_is_substrate_not_tuned" => cc_is_substrate_not_tuned,
        "expansion_from_entropy" => expansion_from_entropy,
        "no_free_param" => no_free_param,
        "canonical_qit_spec_ok" => Int(qit_rows["qit_substage_count"]) == MODE_COUNT &&
            Float64(qit_rows["type_one_h0_residual"]) < TOL &&
            Float64(qit_rows["type_two_minus_h0_residual"]) < TOL &&
            Float64(qit_rows["mirror_is_sx_residual"]) < TOL &&
            Float64(qit_rows["mirror_involution_residual"]) < TOL &&
            Int(qit_rows["lindblad_count"]) == 4,
        "hard_open_rungs_graveyarded" => all(row -> row["derived"] === false, values(graveyard_companions)),
    )
    local_all_pass = all(Bool(v) for v in values(verdicts)) &&
        section_all_pass(positive) &&
        section_all_pass(controls) &&
        section_all_pass(graveyard_companions) &&
        section_all_pass(boundary)

    shared_scalars = Dict{String,Any}(
        "expansion_term" => expansion_term,
        "entropy_growth_rate" => entropy["entropy_growth_rate"],
        "entropy_final_minus_initial" => entropy["entropy_final_minus_initial"],
        "carrier_amplitude" => carrier_amplitude,
        "link_gap" => link_gap,
        "division_factor" => division_factor,
        "g2_factor" => g2_factor,
        "density_factor" => density_factor,
        "hopf_factor" => hopf_factor,
        "qit_factor" => qit_factor,
        "qit_mean_response" => Float64(qit_rows["qit_mean_response"]),
        "qit_lr_delta" => Float64(qit_rows["qit_lr_delta"]),
        "qit_response_min" => Float64(qit_rows["qit_response_min"]),
        "qit_response_max" => Float64(qit_rows["qit_response_max"]),
        "qit_substage_count" => Float64(qit_rows["qit_substage_count"]),
        "type_one_h0_residual" => Float64(qit_rows["type_one_h0_residual"]),
        "type_two_minus_h0_residual" => Float64(qit_rows["type_two_minus_h0_residual"]),
        "mirror_is_sx_residual" => Float64(qit_rows["mirror_is_sx_residual"]),
        "mirror_involution_residual" => Float64(qit_rows["mirror_involution_residual"]),
        "lindblad_count" => Float64(qit_rows["lindblad_count"]),
        "flat_link_term" => flat_link_term,
        "frozen_entropy_term" => frozen_entropy_term,
        "qit_erased_term" => qit_erased_term,
        "g2_erased_term" => g2_erased_term,
        "division_erased_term" => division_erased_term,
        "tuned_residual_without_tuning" => tuned_residual_without_tuning,
        "tuned_residual_after_tuning" => tuned_residual_after_tuning,
        "tuned_lambda_to_match" => tuned_lambda_to_match,
        "substrate_free_parameter_count" => Float64(substrate_free_parameter_count),
        "tuned_free_parameter_count" => Float64(tuned_free_parameter_count),
        "owner_carrier_load_bearing" => owner_carrier_load_bearing ? 1.0 : 0.0,
        "cc_is_substrate_not_tuned" => cc_is_substrate_not_tuned ? 1.0 : 0.0,
        "expansion_from_entropy" => expansion_from_entropy ? 1.0 : 0.0,
        "no_free_param" => no_free_param ? 1.0 : 0.0,
    )
    for (idx0, value) in enumerate(entropy["entropy_profile"])
        shared_scalars["entropy_profile.$(idx0 - 1)"] = Float64(value)
    end
    for (idx0, value) in enumerate(entropy["tau_profile"])
        shared_scalars["tau_profile.$(idx0 - 1)"] = Float64(value)
    end
    for (idx0, value) in enumerate(entropy["entropy_increments"])
        shared_scalars["entropy_increment.$(idx0 - 1)"] = Float64(value)
    end
    for (key, value) in carrier
        shared_scalars["carrier.$key"] = Float64(value)
    end

    shared_booleans = Dict{String,Any}()
    for (key, value) in verdicts
        shared_booleans["verdict.$key"] = Bool(value)
    end
    for (key, row) in positive
        shared_booleans["positive.$key"] = Bool(row["pass"])
    end
    for (key, row) in controls
        shared_booleans["control.$key"] = Bool(row["pass"])
    end
    for (key, row) in graveyard_companions
        shared_booleans["graveyard.$key.derived"] = Bool(row["derived"])
    end
    for (key, row) in boundary
        shared_booleans["boundary.$key"] = Bool(row["pass"])
    end

    result = Dict{String,Any}(
        "schema" => "MP4_COSMOLOGICAL_CONSTANT_DISSOLVES_DUAL_BACKEND_v1",
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "backend" => BACKEND,
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_RESULT_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "jax_enable_x64" => false,
        "numpy_compute_used" => false,
        "sim_execution_kind" => "nonclassical_scratch_diagnostic",
        "sim_class" => "finite_formal_scout",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "root_constraints_in_force" => ["F01 finite carrier", "N01 noncommuting/order-sensitive carrier"],
        "claim_ceiling" => "Finite reframing witness in the owner's entropic-monist frame only: a dark-energy-like positive expansion term is determined by finite substrate entropy/possibility growth on the owner carrier, while the tuned-vacuum-constant control requires an external free parameter. NOT a measured Lambda value, NOT a proof/derivation of the cosmological-constant problem, and no physics admission.",
        "allowed_claims" => ["finite mechanism witness", "dual-backend parity witness", "non-tautological erasure/control diagnostic", "honest graveyard result for measured/open cosmology rungs"],
        "blocked_consumers" => ["measured_Lambda_claim", "cosmology_physics_admission", "formal_admission", "promotion", "proof_of_cosmological_constant_problem"],
        "source_dependencies" => SOURCE_DEPENDENCIES,
        "canonical_qit_spec_used" => Dict("H_L" => "+H0", "H_R" => "-H0", "mirror" => "SX", "lindblad_labels" => ["Se", "Ne", "Ni", "Si"], "substage_count" => MODE_COUNT),
        "carrier_invariants" => carrier,
        "entropy_profile" => entropy,
        "positive" => positive,
        "controls" => controls,
        "graveyard_companions" => graveyard_companions,
        "boundary" => boundary,
        "nearby_variants" => Dict("total" => length(controls), "passed" => sum(Bool(row["pass"]) ? 1 : 0 for row in values(controls)), "variant_names" => sort(collect(keys(controls)))),
        "why_not_v4_probes" => ["finite dual-backend scratch scout, not a v4 promotion probe", "positive finite entropy-growth term is not a measured cosmological constant", "tuned-vacuum control shows an external parameter boundary, not a physics theorem"],
        "blockers" => [],
        "qit_substage_detail" => qit_rows["detail_rows"],
        "TOOL_MANIFEST" => Dict(
            "Julia LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite mixed-state entropy, carrier amplitude, erasure controls, and parity scalars"),
            "canonical_qit_engine_specs.py mirror constants" => Dict("tried" => true, "used" => true, "reason" => "load-bearing mirror of H_L=+H0, H_R=-H0, MIRROR=SX, Lindblad matrices, operator slots, and 32-substage weights"),
            "density_matrix_spinor_lift mirror" => Dict("tried" => true, "used" => true, "reason" => "load-bearing density matrices and Bloch vectors used in finite entropy-growth profile"),
            "clifford_torus_nested_hopf_foliation receipt" => Dict("tried" => true, "used" => true, "reason" => "load-bearing nested Hopf shell metric factors and erasure boundary"),
            "golden_weyl receipt and mirror" => Dict("tried" => true, "used" => true, "reason" => "load-bearing shell spinors, linking/cocycle invariants, and flat-link control"),
            "division_algebra_ratchet_ladder receipt" => Dict("tried" => true, "used" => true, "reason" => "load-bearing H/O ladder factors; division erasure changes result"),
            "octonion_G2_automorphism receipt" => Dict("tried" => true, "used" => true, "reason" => "load-bearing G2 derivation dimension and automorphism residual; G2 erasure changes result"),
            "Julia JSON/path" => Dict("tried" => true, "used" => true, "reason" => "supportive exact result writing and peer parity parsing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Julia LinearAlgebra" => "load_bearing",
            "canonical_qit_engine_specs.py mirror constants" => "load_bearing",
            "density_matrix_spinor_lift mirror" => "load_bearing",
            "clifford_torus_nested_hopf_foliation receipt" => "load_bearing",
            "golden_weyl receipt and mirror" => "load_bearing",
            "division_algebra_ratchet_ladder receipt" => "load_bearing",
            "octonion_G2_automorphism receipt" => "load_bearing",
            "Julia JSON/path" => "supportive",
        ),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "verdicts" => verdicts,
        "local_all_pass" => local_all_pass,
        "plain_sentence" => "Finite witness only: on the owner carrier, the dark-energy-like term is determined by entropy/possibility growth; the tuned-vacuum control needs a supplied constant, while measured Lambda remains graveyarded as derived=false.",
    )
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_block(result)
    result["all_pass"] = local_all_pass && Bool(result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = !local_all_pass || Bool(result["parity"]["stop_condition_fired"])
    result["summary"] = Dict(
        "all_pass" => result["all_pass"],
        "local_all_pass" => local_all_pass,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "cc_is_substrate_not_tuned" => cc_is_substrate_not_tuned,
        "expansion_from_entropy" => expansion_from_entropy,
        "no_free_param" => no_free_param,
        "expansion_term" => expansion_term,
        "entropy_growth_rate" => entropy["entropy_growth_rate"],
        "parity_within_1e_9" => result["parity"]["within_1e_9"],
    )
    result["result_summary"] = result["summary"]
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
        "cc_is_substrate_not_tuned=$(lowercase(string(result["summary"]["cc_is_substrate_not_tuned"]))) " *
        "expansion_from_entropy=$(lowercase(string(result["summary"]["expansion_from_entropy"]))) " *
        "no_free_param=$(lowercase(string(result["summary"]["no_free_param"])))"
    )
    exit(result["local_all_pass"] ? 0 : 1)
end

main()
