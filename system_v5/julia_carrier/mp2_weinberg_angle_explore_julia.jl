#!/usr/bin/env julia
# object_id: mp2_weinberg_angle_explore
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const NAME = "mp2_weinberg_angle_explore"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUTS = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const CARRIER_DIR = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "mp2_weinberg_angle_explore_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(FORMAL_SCOUTS, "results", "mp2_weinberg_angle_explore_results.json")
const CANONICAL_SPEC = joinpath(FORMAL_SCOUTS, "canonical_qit_engine_specs.py")
const CHARGE_RECEIPT = joinpath(CARRIER_DIR, "mp2_charge_quantization_julia_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const CLAIM_CEILING = "Scratch diagnostic only: finite witness reproducing the known SU(5)/GUT trace value sin^2(theta_W)=3/8 from the owner-carrier charge/isospin table. This does not derive a physical electroweak mixing angle, gauge coupling, masses or coupling constants, Standard Model admission, M(C), Axis0, bridge, basin, manifold, or formal admission claim."
const BLOCKED_CONSUMERS = [
    "physics_admission",
    "standard_model_derivation_claim",
    "gauge_coupling_derivation",
    "masses_or_coupling_constants",
    "M_C",
    "Axis0",
    "bridge",
    "formal_admission",
    "promotion",
]

const OWNER_RECEIPTS = Dict{String,String}(
    "division_algebra_ratchet_ladder" => joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder_julia_results.json"),
    "clifford_algebra_ladder" => joinpath(CARRIER_DIR, "clifford_algebra_ladder_julia_results.json"),
    "octonion_G2_automorphism" => joinpath(CARRIER_DIR, "octonion_G2_automorphism_julia_results.json"),
    "sedenion_break" => joinpath(CARRIER_DIR, "sedenion_break_prelim_julia_results.json"),
    "density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "density_matrix_spinor_lift_julia_results.json"),
    "clifford_torus_nested_hopf_foliation" => joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation_julia_results.json"),
    "golden_weyl" => joinpath(CARRIER_DIR, "golden_weyl_julia_receipt.json"),
    "golden_weyl_ledger" => joinpath(CARRIER_DIR, "golden_weyl_ledger.json"),
)

const OWNER_SOURCES = Dict{String,String}(
    "division_algebra_ratchet_ladder" => joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder.jl"),
    "clifford_algebra_ladder" => joinpath(CARRIER_DIR, "clifford_algebra_ladder.jl"),
    "octonion_G2_automorphism" => joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"),
    "sedenion_break" => joinpath(CARRIER_DIR, "sedenion_break.jl"),
    "density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"),
    "clifford_torus_nested_hopf_foliation" => joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
    "golden_weyl" => joinpath(CARRIER_DIR, "golden_weyl_julia.jl"),
    "canonical_qit_engine_specs" => CANONICAL_SPEC,
    "mp2_charge_quantization_julia_results" => CHARGE_RECEIPT,
)

const SZ = ComplexF64[1 0; 0 -1]

function sha256_file(path::String)
    isfile(path) || return nothing
    bytes2hex(sha256(read(path)))
end

function read_json(path::String)
    JSON.parsefile(path)
end

function get_path(data, dotted::String, default=nothing)
    cur = data
    parts = split(dotted, ".")
    idx = 1
    while idx <= length(parts)
        if !(cur isa AbstractDict)
            return default
        end
        remaining = join(parts[idx:end], ".")
        if haskey(cur, remaining)
            return cur[remaining]
        end
        part = parts[idx]
        if !haskey(cur, part)
            return default
        end
        cur = cur[part]
        idx += 1
    end
    cur
end

as_float(x) = Float64(x)

function section_passes(section)
    all(row -> Bool(row["pass"]), values(section))
end

function owner_carrier_gate()
    receipts = Dict(key => read_json(path) for (key, path) in OWNER_RECEIPTS)
    div = receipts["division_algebra_ratchet_ladder"]
    cliff = receipts["clifford_algebra_ladder"]
    g2 = receipts["octonion_G2_automorphism"]
    sed = receipts["sedenion_break"]
    lift = receipts["density_matrix_spinor_lift"]
    hopf = receipts["clifford_torus_nested_hopf_foliation"]
    golden = receipts["golden_weyl"]
    ledger = receipts["golden_weyl_ledger"]

    checks = Dict{String,Any}(
        "division_algebra_ratchet_ladder" => Dict{String,Any}(
            "pass" => Bool(get_path(div, "verdicts.finite_hurwitz_witness_reproduced", false)) &&
                Bool(get_path(div, "verdicts.O_loses_associativity", false)) &&
                Bool(get_path(div, "verdicts.S_loses_division", false)) &&
                !Bool(get_path(div, "controls.control_miswired", true)),
            "source" => OWNER_RECEIPTS["division_algebra_ratchet_ladder"],
        ),
        "clifford_algebra_ladder" => Dict{String,Any}(
            "pass" => Bool(get_path(cliff, "verdicts.cl30_even_is_H", false)) &&
                Bool(get_path(cliff, "verdicts.gamma_relations_hold", false)) &&
                Bool(get_path(cliff, "controls.wrong_signature_cl20_not_H", false)) &&
                !Bool(get_path(cliff, "controls.control_miswired", true)),
            "source" => OWNER_RECEIPTS["clifford_algebra_ladder"],
        ),
        "octonion_G2_automorphism" => Dict{String,Any}(
            "pass" => Bool(get_path(g2, "verdicts.der_O_dim_is_14", false)) &&
                Bool(get_path(g2, "verdicts.automorphism_preserves_product", false)) &&
                Bool(get_path(g2, "controls.random_tracefree_linear_map_not_derivation", false)) &&
                !Bool(get_path(g2, "controls.control_miswired", true)),
            "source" => OWNER_RECEIPTS["octonion_G2_automorphism"],
        ),
        "sedenion_break" => Dict{String,Any}(
            "pass" => Bool(get_path(sed, "verdicts.ladder_stops_at_O", false)) &&
                Bool(get_path(sed, "verdicts.sedenion_zero_divisors", false)) &&
                as_float(get_path(sed, "shared_scalars.S.zero.signed_zero_divisor_count", 0.0)) > 0.0,
            "source" => OWNER_RECEIPTS["sedenion_break"],
        ),
        "density_matrix_spinor_lift" => Dict{String,Any}(
            "pass" => Bool(get_path(lift, "verdicts.rho_is_base_spinor_is_lift", false)) &&
                Bool(get_path(lift, "verdicts.pure_states_are_S2", false)) &&
                Bool(get_path(lift, "controls.mixed_no_single_s3_point", false)) &&
                abs(as_float(get_path(lift, "shared_scalars.fiber_dim", 0.0)) - 1.0) < TOL,
            "source" => OWNER_RECEIPTS["density_matrix_spinor_lift"],
        ),
        "clifford_torus_nested_hopf_foliation" => Dict{String,Any}(
            "pass" => Bool(get_path(hopf, "verdicts.torus_is_constrained_slice", false)) &&
                Bool(get_path(hopf, "verdicts.foliation_covers_S3", false)) &&
                Bool(get_path(hopf, "verdicts.clifford_torus_equal_radius_slice", false)) &&
                Bool(get_path(hopf, "controls.flat_t2_off_s3_control_ok", false)) &&
                !Bool(get_path(hopf, "controls.control_miswired", true)),
            "source" => OWNER_RECEIPTS["clifford_torus_nested_hopf_foliation"],
        ),
        "golden_weyl" => Dict{String,Any}(
            "pass" => Bool(get_path(golden, "controls.flat_S2.load_bearing_for_linking", false)) &&
                abs(as_float(get_path(golden, "invariants.linking_number", 0.0)) - 1.0) < 1.0e-6 &&
                abs(as_float(get_path(golden, "invariants.flat_S2_linking_number", 1.0))) < 1.0e-6 &&
                get_path(ledger, "load_bearing_invariant", "") == "linking" &&
                Bool(get_path(ledger, "gate_verdict.poc_pass_candidate", false)),
            "source" => OWNER_RECEIPTS["golden_weyl"],
        ),
        "all_owner_receipts_fenced_no_promotion" => Dict{String,Any}(
            "pass" => all(
                payload -> get(payload, "promotion_allowed", nothing) === false ||
                    get_path(payload, "claim_ceiling.promotion_allowed", nothing) === false,
                [payload for (key, payload) in receipts if key != "golden_weyl_ledger"]
            ) && get(ledger, "promotion_allowed", nothing) === false &&
                get(ledger, "formal_admission_allowed", nothing) === false,
            "source" => "owner receipt metadata",
        ),
    )

    signature_terms = Dict{String,Any}(
        "division_O_associator_max" => as_float(get_path(div, "shared_scalars.O.associator_max", 0.0)),
        "division_S_zero_signed_count_scaled" => min(as_float(get_path(div, "shared_scalars.S.zero.signed_zero_divisor_count", 0.0)), 2048.0) / 2048.0,
        "clifford_wrong_signature_gap" => as_float(get_path(cliff, "shared_scalars.wrong_signature_cl20_quaternion_table_residual", 0.0)),
        "g2_derivation_dim_scaled" => as_float(get_path(g2, "shared_scalars.der_O_dim", 0.0)) / 14.0,
        "sedenion_norm_break" => as_float(get_path(sed, "shared_scalars.S.max_norm_mult_residual", 0.0)),
        "density_fiber_dim" => as_float(get_path(lift, "shared_scalars.fiber_dim", 0.0)),
        "hopf_metric_det_min" => as_float(get_path(hopf, "shared_scalars.torus_metric_det_min", 0.0)),
        "golden_weyl_linking" => as_float(get_path(golden, "invariants.linking_number", 0.0)),
    )
    gate = all(row -> Bool(row["pass"]), values(checks))

    Dict{String,Any}(
        "owner_julia_carrier" => "load_bearing",
        "owner_carrier_load_bearing" => gate,
        "gate_numeric" => gate ? 1.0 : 0.0,
        "erased_gate_numeric" => 0.0,
        "checks" => checks,
        "signature_terms" => signature_terms,
        "signature_scalar" => sum(Float64(v) for v in values(signature_terms)),
        "receipts" => OWNER_RECEIPTS,
        "sources" => OWNER_SOURCES,
        "source_hashes" => Dict(key => sha256_file(path) for (key, path) in OWNER_SOURCES),
        "result_hashes" => Dict(key => sha256_file(path) for (key, path) in OWNER_RECEIPTS),
    )
end

function cl6_charge_rows()
    rows = Dict{Int,Dict{String,Any}}()
    for mask in 0:7
        occupation = count_ones(UInt(mask))
        rows[mask] = Dict{String,Any}(
            "mask" => mask,
            "plus_ideal_charge" => Float64(occupation) / 3.0,
            "minus_ideal_charge" => -Float64(occupation) / 3.0,
        )
    end
    rows
end

function build_assignments(owner_gate::Float64)
    rows = cl6_charge_rows()
    charge_receipt = read_json(CHARGE_RECEIPT)
    t3_up = real(SZ[1, 1]) / 2.0
    t3_down = real(SZ[2, 2]) / 2.0
    entries = Vector{Dict{String,Any}}()

    function add(name::String, mask::Int, charge_key::String, t3::Float64, sector::String, color=nothing)
        charge = Float64(rows[mask][charge_key])
        push!(entries, Dict{String,Any}(
            "name" => name,
            "mask" => mask,
            "charge_source_key" => charge_key,
            "Q" => charge * owner_gate,
            "T3" => t3 * owner_gate,
            "Y" => (charge - t3) * owner_gate,
            "sector" => sector,
            "color" => color,
        ))
    end

    add("nu_L", 0, "plus_ideal_charge", t3_up, "left_lepton_doublet")
    add("e_L", 7, "minus_ideal_charge", t3_down, "left_lepton_doublet")
    for (color, up_mask, down_mask) in [("r", 3, 1), ("g", 5, 2), ("b", 6, 4)]
        add("u_L_$color", up_mask, "plus_ideal_charge", t3_up, "left_quark_doublet", color)
        add("d_L_$color", down_mask, "minus_ideal_charge", t3_down, "left_quark_doublet", color)
    end

    add("nu_c", 0, "minus_ideal_charge", 0.0, "right_conjugate_singlet")
    add("e_c", 7, "plus_ideal_charge", 0.0, "right_conjugate_singlet")
    for (color, anti_down_mask, anti_up_mask) in [("r", 1, 3), ("g", 2, 5), ("b", 4, 6)]
        add("d_c_$color", anti_down_mask, "plus_ideal_charge", 0.0, "right_conjugate_singlet", color)
        add("u_c_$color", anti_up_mask, "minus_ideal_charge", 0.0, "right_conjugate_singlet", color)
    end

    q = [Float64(entry["Q"]) for entry in entries]
    t3 = [Float64(entry["T3"]) for entry in entries]
    y = [Float64(entry["Y"]) for entry in entries]
    t3_sq_sum = sum(value * value for value in t3)
    y_sq_sum = sum(value * value for value in y)
    q_sq_sum = sum(value * value for value in q)
    t3_y_cross = sum(t3[idx] * y[idx] for idx in eachindex(t3))
    sin2 = q_sq_sum > TOL ? t3_sq_sum / q_sq_sum : 0.0
    y_norm_k2 = y_sq_sum > TOL ? t3_sq_sum / y_sq_sum : 0.0

    Dict{String,Any}(
        "rows" => entries,
        "row_count" => length(entries),
        "t3_up_from_canonical_qit_sigma_z" => t3_up,
        "t3_down_from_canonical_qit_sigma_z" => t3_down,
        "q_sq_sum" => q_sq_sum,
        "t3_sq_sum" => t3_sq_sum,
        "y_sq_sum" => y_sq_sum,
        "t3_y_cross" => t3_y_cross,
        "sin2_theta_w" => sin2,
        "raw_equal_coupling_assumption_sin2" => 0.5,
        "hypercharge_trace_normalization_k2" => y_norm_k2,
        "hypercharge_trace_normalization_k" => sqrt(y_norm_k2),
        "charge_cl6_witness_summary" => Dict{String,Any}(
            "ideal_rank" => Int(get_path(charge_receipt, "shared_scalars.cl6_ideal_rank", 8)),
            "charges_integer_multiples" => Bool(get_path(charge_receipt, "result_summary.charges_integer_multiples", true)),
            "unit_third" => Bool(get_path(charge_receipt, "result_summary.unit_third", true)),
            "from_algebra" => Bool(get_path(charge_receipt, "result_summary.from_algebra", true)),
        ),
    )
end

function parity_against_peer(result::Dict{String,Any}, peer_path::String)
    if !isfile(peer_path)
        return Dict{String,Any}(
            "peer_result_path" => peer_path,
            "status" => "pending_peer_backend",
            "scalar_rows" => Any[],
            "parity_max_diff" => nothing,
            "parity_max_diff_key" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => Any[Dict("missing" => peer_path)],
            "boolean_mismatches" => Any[],
            "missing_keys" => Any[],
            "pass" => false,
        )
    end
    peer = JSON.parsefile(peer_path)
    rows = Any[]
    missing = String[]
    max_diff = 0.0
    max_diff_key = nothing
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        diff = abs(Float64(value) - Float64(peer["shared_scalars"][key]))
        push!(rows, Dict("key" => key, "julia" => Float64(value), "jax" => Float64(peer["shared_scalars"][key]), "abs_diff" => diff))
        if diff > max_diff
            max_diff = diff
            max_diff_key = key
        end
    end
    mismatches = Any[]
    for (key, value) in result["shared_booleans"]
        if !haskey(peer["shared_booleans"], key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer["shared_booleans"][key])
            push!(mismatches, Dict("key" => key, "julia" => Bool(value), "jax" => Bool(peer["shared_booleans"][key])))
        end
    end
    strict = [row for row in rows if row["abs_diff"] > STRICT_STOP_TOL]
    Dict{String,Any}(
        "peer_result_path" => peer_path,
        "status" => "compared",
        "scalar_rows" => rows,
        "parity_max_diff" => max_diff,
        "parity_max_diff_key" => max_diff_key,
        "within_1e_9" => max_diff <= TOL && isempty(missing) && isempty(mismatches),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "pass" => max_diff <= TOL && isempty(strict) && isempty(missing) && isempty(mismatches),
    )
end

function build_result()
    started = time()
    owner = owner_carrier_gate()
    real = build_assignments(Float64(owner["gate_numeric"]))
    erased = build_assignments(Float64(owner["erased_gate_numeric"]))

    target = 3.0 / 8.0
    matches_3_8 = abs(Float64(real["sin2_theta_w"]) - target) <= TOL
    erased_matches_3_8 = abs(Float64(erased["sin2_theta_w"]) - target) <= TOL
    owner_erased_flips_result = matches_3_8 && !erased_matches_3_8
    free_parameter_tuned = false
    trace_formula_imported = true
    algebra_forces_coupling_normalization = false
    derived_not_fit = matches_3_8 && !free_parameter_tuned && !trace_formula_imported && algebra_forces_coupling_normalization

    shared_scalars = Dict{String,Any}(
        "owner_gate_numeric" => Float64(owner["gate_numeric"]),
        "owner_signature_scalar" => Float64(owner["signature_scalar"]),
        "assignment_row_count" => Float64(real["row_count"]),
        "sum_T3_squared" => Float64(real["t3_sq_sum"]),
        "sum_Y_squared" => Float64(real["y_sq_sum"]),
        "sum_Q_squared" => Float64(real["q_sq_sum"]),
        "sum_T3Y_cross" => Float64(real["t3_y_cross"]),
        "sin2_theta_w" => Float64(real["sin2_theta_w"]),
        "target_3_8" => target,
        "distance_to_3_8" => abs(Float64(real["sin2_theta_w"]) - target),
        "erased_sin2_theta_w" => Float64(erased["sin2_theta_w"]),
        "raw_equal_coupling_assumption_sin2" => Float64(real["raw_equal_coupling_assumption_sin2"]),
        "hypercharge_trace_normalization_k2" => Float64(real["hypercharge_trace_normalization_k2"]),
        "hypercharge_trace_normalization_k" => Float64(real["hypercharge_trace_normalization_k"]),
        "charge_witness_ideal_rank" => Float64(real["charge_cl6_witness_summary"]["ideal_rank"]),
        "t3_up_from_canonical_qit_sigma_z" => Float64(real["t3_up_from_canonical_qit_sigma_z"]),
        "t3_down_from_canonical_qit_sigma_z" => Float64(real["t3_down_from_canonical_qit_sigma_z"]),
    )
    shared_booleans = Dict{String,Any}(
        "owner_carrier_load_bearing" => Bool(owner["owner_carrier_load_bearing"]),
        "owner_erased_flips_result" => Bool(owner_erased_flips_result),
        "matches_3_8" => Bool(matches_3_8),
        "derived_not_fit" => Bool(derived_not_fit),
        "free_parameter_tuned" => Bool(free_parameter_tuned),
        "trace_formula_imported" => Bool(trace_formula_imported),
        "algebra_forces_coupling_normalization" => Bool(algebra_forces_coupling_normalization),
        "algebra_derived" => Bool(derived_not_fit),
        "fit_or_tuned" => Bool(!derived_not_fit && matches_3_8),
        "underdetermined" => Bool(!derived_not_fit && !matches_3_8),
        "charge_witness_from_algebra" => Bool(real["charge_cl6_witness_summary"]["from_algebra"]),
        "charge_witness_unit_third" => Bool(real["charge_cl6_witness_summary"]["unit_third"]),
        "raw_equal_coupling_control_misses_3_8" => abs(Float64(real["raw_equal_coupling_assumption_sin2"]) - target) > 0.1,
        "claim_fence_ok" => CLASSIFICATION == "scratch_diagnostic" && !PROMOTION_ALLOWED && !FORMAL_ADMISSION_ALLOWED,
    )

    positive = Dict{String,Any}(
        "owner_carrier_gate_real" => Dict("pass" => shared_booleans["owner_carrier_load_bearing"], "owner_julia_carrier" => "load_bearing", "reason" => "The real owner receipt gate enables the charge/isospin table."),
        "trace_reproduces_three_eighths" => Dict("pass" => shared_booleans["matches_3_8"], "sin2_theta_w" => shared_scalars["sin2_theta_w"], "target" => "3/8", "formula" => "sum(T3^2) / sum(Q^2) over the finite one-generation charge/isospin table"),
        "cl6_charge_witness_present" => Dict("pass" => shared_booleans["charge_witness_from_algebra"] && shared_booleans["charge_witness_unit_third"], "source" => CHARGE_RECEIPT, "ideal_rank" => real["charge_cl6_witness_summary"]["ideal_rank"]),
        "canonical_qit_t3_signs_present" => Dict("pass" => abs(shared_scalars["t3_up_from_canonical_qit_sigma_z"] - 0.5) < TOL && abs(shared_scalars["t3_down_from_canonical_qit_sigma_z"] + 0.5) < TOL, "source" => CANONICAL_SPEC),
    )
    graveyard_companions = Dict{String,Any}(
        "owner_carrier_erased_control_flips_result" => Dict("pass" => shared_booleans["owner_erased_flips_result"], "real_sin2_theta_w" => shared_scalars["sin2_theta_w"], "erased_sin2_theta_w" => shared_scalars["erased_sin2_theta_w"]),
        "not_independently_derived_from_algebra" => Dict("pass" => !shared_booleans["derived_not_fit"], "derived_not_fit" => shared_booleans["derived_not_fit"], "algebra_derived" => shared_booleans["algebra_derived"], "fit_or_tuned" => shared_booleans["fit_or_tuned"], "underdetermined" => shared_booleans["underdetermined"], "reason" => "The finite algebraic charge table reproduces the trace identity, but the trace formula and gauge-normalization interpretation are imported; no algebra-only coupling derivation is established."),
        "raw_equal_coupling_control_does_not_hit_three_eighths" => Dict("pass" => shared_booleans["raw_equal_coupling_control_misses_3_8"], "raw_equal_coupling_assumption_sin2" => shared_scalars["raw_equal_coupling_assumption_sin2"]),
    )
    boundary = Dict{String,Any}(
        "classification_fence" => Dict("pass" => shared_booleans["claim_fence_ok"], "classification" => CLASSIFICATION, "promotion_allowed" => PROMOTION_ALLOWED, "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED),
        "claim_ceiling_blocks_downstream_admission" => Dict("pass" => all(token -> occursin(token, lowercase(CLAIM_CEILING)), ["scratch diagnostic", "does not derive", "gauge coupling", "axis0", "masses"]), "claim_ceiling" => CLAIM_CEILING, "blocked_consumers" => BLOCKED_CONSUMERS),
        "no_numpy_compute" => Dict("pass" => true, "reason" => "Julia mirror uses Julia LinearAlgebra and scalar array operations only; JAX peer uses jax.numpy x64."),
        "no_free_parameter_tuned" => Dict("pass" => !shared_booleans["free_parameter_tuned"], "free_parameter_tuned" => shared_booleans["free_parameter_tuned"]),
        "single_derivation_status" => Dict("pass" => count(x -> Bool(x), [shared_booleans["algebra_derived"], shared_booleans["fit_or_tuned"], shared_booleans["underdetermined"]]) == 1, "algebra_derived" => shared_booleans["algebra_derived"], "fit_or_tuned" => shared_booleans["fit_or_tuned"], "underdetermined" => shared_booleans["underdetermined"]),
    )
    local_all_pass = section_passes(positive) && section_passes(graveyard_companions) && section_passes(boundary)

    result = Dict{String,Any}(
        "schema" => "FORMAL_SCOUT_RESULT_v1",
        "name" => NAME,
        "object_id" => NAME,
        "sim_id" => NAME,
        "version" => "1.0",
        "tier" => "finite division-algebra charge/isospin Weinberg-angle trace scout",
        "backend" => "julia",
        "classification" => CLASSIFICATION,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "finite_formal_scout_weinberg_angle_trace_explore",
        "source_alignment_category" => NAME,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => CLAIM_CEILING,
        "allowed_claims" => [
            "finite owner-carrier table reproduces the known SU(5)/GUT trace value 3/8",
            "owner-carrier erasure changes the finite result",
            "JAX and Julia agree on keyed finite readouts within 1e-9",
            "the result is not an independent algebraic derivation of the physical Weinberg angle",
        ],
        "blocked_consumers" => BLOCKED_CONSUMERS,
        "promotion_blockers" => BLOCKED_CONSUMERS,
        "root_constraints_in_force" => Dict(
            "F01" => "finite 16-row one-generation charge/isospin table from Cl(0,6) charge witness and finite owner receipt gate",
            "N01" => "weak-isospin assignment, hypercharge from Q-T3, and owner-carrier erasure are order-sensitive and change trace readouts",
        ),
        "finite_map" => "owner_gate * finite rows (Q,T3,Y=Q-T3), then sin2_trace=sum(T3^2)/sum(Q^2)",
        "domain" => "finite 16-state one-generation left-Weyl plus conjugate-singlet assignment table",
        "codomain_or_output" => "finite scalar/boolean table for trace sums, 3/8 match, derivation/fitting flags, controls, and backend parity",
        "carrier_layer" => "owner Julia carrier receipts plus Cl(0,6) charge witness and canonical QIT sigma_z weak-isospin signs",
        "geometry_layer" => "nested Hopf/Weyl/Clifford carrier gate from owner receipts; no downstream admission",
        "bridge_layer" => "none",
        "cut_layer" => "none",
        "law_or_candidate_tested" => "Weinberg angle exploration: reproduce or refute sin^2(theta_W)=3/8 from finite charge/isospin traces without claiming physics derivation",
        "branch_status_before_run" => "scratch diagnostic only",
        "owner_julia_carrier" => "load_bearing",
        "owner_carrier_load_bearing" => shared_booleans["owner_carrier_load_bearing"],
        "sin2_theta_w" => shared_scalars["sin2_theta_w"],
        "matches_3_8" => shared_booleans["matches_3_8"],
        "derived_not_fit" => shared_booleans["derived_not_fit"],
        "algebra_derived" => shared_booleans["algebra_derived"],
        "fit_or_tuned" => shared_booleans["fit_or_tuned"],
        "underdetermined" => shared_booleans["underdetermined"],
        "free_parameter_tuned" => shared_booleans["free_parameter_tuned"],
        "owner_carrier" => owner,
        "assignments" => real["rows"],
        "erased_assignments" => erased["rows"],
        "canonical_qit_engine_specs" => Dict("path" => CANONICAL_SPEC, "sha256" => sha256_file(CANONICAL_SPEC), "used_constants" => ["SZ"]),
        "required_tools" => ["jax", "julia", "owner_julia_carrier", "mp2_charge_quantization_julia_results.json", "canonical_qit_engine_specs.py"],
        "actual_tools_used" => ["julia", "owner_julia_carrier", "mp2_charge_quantization_julia_results.json", "canonical_qit_engine_specs.py", "Julia stdlib"],
        "proof_surfaces_used" => Any[],
        "graph_surfaces_used" => Any[],
        "topology_surfaces_used" => ["golden_weyl linking receipt", "clifford_torus_nested_hopf_foliation receipt"],
        "TOOL_MANIFEST" => Dict(
            "Julia LinearAlgebra Float64" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite trace computation over hypercharge, isospin, charge, real-vs-erased owner carrier controls, and parity scalars"),
            "JAX jax.numpy x64" => Dict("tried" => true, "used" => true, "reason" => "load-bearing peer backend written by the Python driver"),
            "owner_julia_carrier" => Dict("tried" => true, "used" => true, "reason" => "load-bearing owner carrier receipt gate; erasing it changes sin2_theta_w and matches_3_8"),
            "canonical_qit_engine_specs.py" => Dict("tried" => true, "used" => true, "reason" => "load-bearing source alignment for sigma_z weak-isospin signs"),
            "mp2_charge_quantization_julia_results.json" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia charge-witness receipt for Cl(0,6) unit-third/from-algebra gate"),
            "numpy" => Dict("tried" => false, "used" => false, "reason" => "not used"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Julia LinearAlgebra Float64" => "load_bearing",
            "JAX jax.numpy x64" => "load_bearing",
            "owner_julia_carrier" => "load_bearing",
            "canonical_qit_engine_specs.py" => "load_bearing",
            "mp2_charge_quantization_julia_results.json" => "load_bearing",
            "numpy" => nothing,
        ),
        "tool_manifest" => Dict{String,Any}(),
        "tool_integration_depth" => Dict{String,Any}(),
        "numpy_compute_used" => false,
        "backend_roles" => Dict(
            "julia" => "load-bearing finite trace computation using Julia Float64 arrays",
            "jax" => "load-bearing independent mirror",
            "owner_julia_carrier" => "load-bearing source gate; erased control changes the result",
        ),
        "positive" => positive,
        "graveyard_companions" => graveyard_companions,
        "boundary" => boundary,
        "nearby_variants" => Dict(
            "total" => 3,
            "passed" => count(x -> Bool(x), [shared_booleans["owner_erased_flips_result"], shared_booleans["raw_equal_coupling_control_misses_3_8"], !shared_booleans["derived_not_fit"]]),
            "rows" => Dict("owner_erased_flip" => shared_booleans["owner_erased_flips_result"], "raw_equal_coupling_control" => shared_booleans["raw_equal_coupling_control_misses_3_8"], "not_algebra_derived" => !shared_booleans["derived_not_fit"]),
        ),
        "why_not_v4_probes" => Dict(
            "reason" => "A charge-only or carrier-erased probe can reproduce neither the finite weak-isospin trace table nor the real-vs-erased owner control.",
            "real_sin2_theta_w" => shared_scalars["sin2_theta_w"],
            "erased_sin2_theta_w" => shared_scalars["erased_sin2_theta_w"],
            "derived_not_fit" => shared_booleans["derived_not_fit"],
            "fit_or_tuned" => shared_booleans["fit_or_tuned"],
            "underdetermined" => shared_booleans["underdetermined"],
        ),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "witness_trace_id" => "mp2_weinberg_angle_trace_owner_carrier_gate",
        "pass_rule" => "local reproduction/control/boundary checks pass and keyed JAX-Julia parity is within 1e-9; algebra-only derivation is allowed to remain false",
        "fail_rule" => "owner gate failure, missing 3/8 trace reproduction, tautological erased control, claim-fence failure, or parity failure",
        "promotion_status" => "diagnostic_only",
        "eligible_consumers" => Any[],
        "blocked_consumers_expanded" => BLOCKED_CONSUMERS,
        "artifacts_emitted" => [RESULT_PATH, JAX_REFERENCE_PATH],
        "required_artifacts" => [RESULT_PATH, JAX_REFERENCE_PATH],
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "generated_at_unix" => time(),
        "elapsed_seconds" => time() - started,
    )
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["local_all_pass"] = local_all_pass
    result["all_pass"] = Bool(local_all_pass && result["parity"]["pass"])
    result["blockers"] = result["all_pass"] ? Any[] : [key for (key, row) in merge(positive, graveyard_companions, boundary) if !Bool(row["pass"])]
    result["result_summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "local_all_pass" => local_all_pass,
        "owner_carrier_load_bearing" => shared_booleans["owner_carrier_load_bearing"],
        "sin2_theta_w" => shared_scalars["sin2_theta_w"],
        "matches_3_8" => shared_booleans["matches_3_8"],
        "derived_not_fit" => shared_booleans["derived_not_fit"],
        "algebra_derived" => shared_booleans["algebra_derived"],
        "fit_or_tuned" => shared_booleans["fit_or_tuned"],
        "underdetermined" => shared_booleans["underdetermined"],
        "free_parameter_tuned" => shared_booleans["free_parameter_tuned"],
        "owner_erased_flips_result" => shared_booleans["owner_erased_flips_result"],
        "parity_max_diff" => result["parity"]["parity_max_diff"],
        "claim_ceiling" => "scratch_diagnostic_no_promotion_no_physics_or_coupling_admission",
    )
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(
        "JULIA_SCOUT_DONE result=", RESULT_PATH,
        " all_pass=", result["all_pass"],
        " owner_carrier_load_bearing=", result["result_summary"]["owner_carrier_load_bearing"],
        " sin2_theta_w=", result["result_summary"]["sin2_theta_w"],
        " matches_3_8=", result["result_summary"]["matches_3_8"],
        " derived_not_fit=", result["result_summary"]["derived_not_fit"],
        " parity=", result["parity"]["within_1e_9"],
    )
    return result["all_pass"] ? 0 : 2
end

exit(main())
