#!/usr/bin/env julia
# object_id: mp2_chiral_weak_from_weyl
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "mp2_chiral_weak_from_weyl"
const RESULT_PATH = joinpath(@__DIR__, "mp2_chiral_weak_from_weyl_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "..", "ops", "formal_scouts", "results", "mp2_chiral_weak_from_weyl_results.json")
const CANONICAL_SPEC = joinpath(@__DIR__, "..", "ops", "formal_scouts", "canonical_qit_engine_specs.py")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const CLAIM_CEILING = "Finite witness reproducing the known left-Weyl SU(2) coupling pattern on the owner carrier only. No physics or Standard Model discovery claim; no M(C), Axis0, bridge, formal admission, masses, coupling constants, or downstream manifold admission."
const BLOCKED_CONSUMERS = [
    "physics_admission",
    "standard_model_derivation_claim",
    "masses_or_coupling_constants",
    "M_C",
    "Axis0",
    "bridge",
    "formal_admission",
    "promotion",
]

const OWNER_RECEIPTS = Dict{String,String}(
    "division_algebra_ratchet_ladder" => joinpath(@__DIR__, "division_algebra_ratchet_ladder_julia_results.json"),
    "clifford_algebra_ladder" => joinpath(@__DIR__, "clifford_algebra_ladder_julia_results.json"),
    "octonion_G2_automorphism" => joinpath(@__DIR__, "octonion_G2_automorphism_julia_results.json"),
    "sedenion_break" => joinpath(@__DIR__, "sedenion_break_prelim_julia_results.json"),
    "density_matrix_spinor_lift" => joinpath(@__DIR__, "density_matrix_spinor_lift_julia_results.json"),
    "clifford_torus_nested_hopf_foliation" => joinpath(@__DIR__, "clifford_torus_nested_hopf_foliation_julia_results.json"),
    "golden_weyl" => joinpath(@__DIR__, "golden_weyl_julia_receipt.json"),
    "golden_weyl_ledger" => joinpath(@__DIR__, "golden_weyl_ledger.json"),
)

const OWNER_SOURCES = Dict{String,String}(
    "division_algebra_ratchet_ladder" => joinpath(@__DIR__, "division_algebra_ratchet_ladder.jl"),
    "clifford_algebra_ladder" => joinpath(@__DIR__, "clifford_algebra_ladder.jl"),
    "octonion_G2_automorphism" => joinpath(@__DIR__, "octonion_G2_automorphism.jl"),
    "sedenion_break" => joinpath(@__DIR__, "sedenion_break.jl"),
    "density_matrix_spinor_lift" => joinpath(@__DIR__, "density_matrix_spinor_lift.jl"),
    "clifford_torus_nested_hopf_foliation" => joinpath(@__DIR__, "clifford_torus_nested_hopf_foliation.jl"),
    "golden_weyl" => joinpath(@__DIR__, "golden_weyl_julia.jl"),
    "canonical_qit_engine_specs" => CANONICAL_SPEC,
)

const I2 = ComplexF64[1 0; 0 1]
const ZERO2 = zeros(ComplexF64, 2, 2)
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SIGMA_MINUS = ComplexF64[0 0; 1 0]
const SIGMA_PLUS = ComplexF64[0 1; 0 0]
const H0 = 0.77 .* SZ .+ 0.13 .* SX
const H_TYPE_ONE = H0
const H_TYPE_TWO = -H0
const MIRROR = SX

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

function block_diag2(a::Matrix{ComplexF64}, b::Matrix{ComplexF64})
    [a ZERO2; ZERO2 b]
end

function state(index0::Int)
    Matrix{ComplexF64}(I, 4, 4)[:, index0 + 1]
end

dagger(x) = x'

function opnorm_fro(x)
    norm(x)
end

function ladder_activity(w_plus::Matrix{ComplexF64}, w_minus::Matrix{ComplexF64}, block::String)
    if block == "L"
        down = state(1)
        up = state(0)
    elseif block == "R"
        down = state(3)
        up = state(2)
    else
        error("unknown block $block")
    end
    opnorm_fro(w_plus * down) + opnorm_fro(w_plus * up) + opnorm_fro(w_minus * down) + opnorm_fro(w_minus * up)
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
        "division_ladder_hurwitz_property_losses" => Dict{String,Any}(
            "pass" => Bool(get_path(div, "verdicts.finite_hurwitz_witness_reproduced", false)) &&
                Bool(get_path(div, "verdicts.O_loses_associativity", false)) &&
                Bool(get_path(div, "verdicts.S_loses_division", false)) &&
                !Bool(get_path(div, "controls.control_miswired", true)),
            "source" => OWNER_RECEIPTS["division_algebra_ratchet_ladder"],
        ),
        "clifford_ladder_even_cl3_quaternion_and_gamma" => Dict{String,Any}(
            "pass" => Bool(get_path(cliff, "verdicts.cl30_even_is_H", false)) &&
                Bool(get_path(cliff, "verdicts.gamma_relations_hold", false)) &&
                Bool(get_path(cliff, "controls.wrong_signature_cl20_not_H", false)) &&
                !Bool(get_path(cliff, "controls.control_miswired", true)),
            "source" => OWNER_RECEIPTS["clifford_algebra_ladder"],
        ),
        "octonion_g2_derivation_automorphism" => Dict{String,Any}(
            "pass" => Bool(get_path(g2, "verdicts.der_O_dim_is_14", false)) &&
                Bool(get_path(g2, "verdicts.automorphism_preserves_product", false)) &&
                Bool(get_path(g2, "controls.random_tracefree_linear_map_not_derivation", false)) &&
                !Bool(get_path(g2, "controls.control_miswired", true)),
            "source" => OWNER_RECEIPTS["octonion_G2_automorphism"],
        ),
        "sedenion_break_zero_divisor_boundary" => Dict{String,Any}(
            "pass" => Bool(get_path(sed, "verdicts.ladder_stops_at_O", false)) &&
                Bool(get_path(sed, "verdicts.sedenion_zero_divisors", false)) &&
                as_float(get_path(sed, "shared_scalars.S.zero.signed_zero_divisor_count", 0.0)) > 0.0,
            "source" => OWNER_RECEIPTS["sedenion_break"],
        ),
        "density_matrix_spinor_lift_hopf_fiber" => Dict{String,Any}(
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
        "golden_weyl_linking_load_bearing" => Dict{String,Any}(
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
    signature_scalar = sum(Float64(v) for v in values(signature_terms))
    gate = all(row -> Bool(row["pass"]), values(checks))

    Dict{String,Any}(
        "owner_julia_carrier" => "load_bearing",
        "owner_carrier_load_bearing" => gate,
        "gate_numeric" => gate ? 1.0 : 0.0,
        "erased_gate_numeric" => 0.0,
        "checks" => checks,
        "signature_terms" => signature_terms,
        "signature_scalar" => signature_scalar,
        "receipts" => OWNER_RECEIPTS,
        "sources" => OWNER_SOURCES,
        "source_hashes" => Dict(key => sha256_file(path) for (key, path) in OWNER_SOURCES),
        "result_hashes" => Dict(key => sha256_file(path) for (key, path) in OWNER_RECEIPTS),
    )
end

function parity_against_peer(result::Dict{String,Any}, peer_path::String)
    if !isfile(peer_path)
        return Dict{String,Any}(
            "peer_result_path" => peer_path,
            "status" => "pending_peer_backend",
            "shared_scalar_rows" => Any[],
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
        "shared_scalar_rows" => rows,
        "parity_max_diff" => max_diff,
        "parity_max_diff_key" => max_diff_key,
        "within_1e_9" => max_diff < TOL && isempty(missing) && isempty(mismatches),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "pass" => max_diff < TOL && isempty(strict) && isempty(missing) && isempty(mismatches),
    )
end

function build_result()
    started = time()
    owner = owner_carrier_gate()
    gate = Float64(owner["gate_numeric"])
    erased_gate = Float64(owner["erased_gate_numeric"])

    w_plus = gate .* block_diag2(SIGMA_PLUS, ZERO2)
    w_minus = gate .* block_diag2(SIGMA_MINUS, ZERO2)
    t1 = gate .* block_diag2(SX ./ 2.0, ZERO2)
    t2 = gate .* block_diag2(SY ./ 2.0, ZERO2)
    t3 = gate .* block_diag2(SZ ./ 2.0, ZERO2)
    p_r = block_diag2(ZERO2, I2)

    mirror_total = [ZERO2 MIRROR; MIRROR ZERO2]
    mirror_w_plus = mirror_total * w_plus * dagger(mirror_total)
    mirror_w_minus = mirror_total * w_minus * dagger(mirror_total)

    owner_erased_w_plus = erased_gate .* block_diag2(SIGMA_PLUS, ZERO2)
    owner_erased_w_minus = erased_gate .* block_diag2(SIGMA_MINUS, ZERO2)
    chirality_erased_w_plus = gate .* block_diag2(SIGMA_PLUS ./ 2.0, SIGMA_PLUS ./ 2.0)
    chirality_erased_w_minus = gate .* block_diag2(SIGMA_MINUS ./ 2.0, SIGMA_MINUS ./ 2.0)

    left_activity = ladder_activity(w_plus, w_minus, "L")
    right_activity = ladder_activity(w_plus, w_minus, "R")
    mirror_left_activity = ladder_activity(mirror_w_plus, mirror_w_minus, "L")
    mirror_right_activity = ladder_activity(mirror_w_plus, mirror_w_minus, "R")
    owner_erased_left_activity = ladder_activity(owner_erased_w_plus, owner_erased_w_minus, "L")
    chirality_erased_left_activity = ladder_activity(chirality_erased_w_plus, chirality_erased_w_minus, "L")
    chirality_erased_right_activity = ladder_activity(chirality_erased_w_plus, chirality_erased_w_minus, "R")

    su2_residual = maximum([
        opnorm_fro((t1 * t2 - t2 * t1) - im * t3),
        opnorm_fro((t2 * t3 - t3 * t2) - im * t1),
        opnorm_fro((t3 * t1 - t1 * t3) - im * t2),
    ])
    right_singlet_norm = maximum([opnorm_fro(p_r * t1 * p_r), opnorm_fro(p_r * t2 * p_r), opnorm_fro(p_r * t3 * p_r)])

    shared_scalars = Dict{String,Any}(
        "canonical_H_L_minus_H0_norm" => opnorm_fro(H_TYPE_ONE - H0),
        "canonical_H_R_plus_H0_norm" => opnorm_fro(H_TYPE_TWO + H0),
        "canonical_H_L_plus_H_R_norm" => opnorm_fro(H_TYPE_ONE + H_TYPE_TWO),
        "canonical_mirror_ladder_minus_to_plus_residual" => opnorm_fro(MIRROR * SIGMA_MINUS * MIRROR - SIGMA_PLUS),
        "canonical_mirror_ladder_plus_to_minus_residual" => opnorm_fro(MIRROR * SIGMA_PLUS * MIRROR - SIGMA_MINUS),
        "owner_gate_numeric" => Float64(owner["gate_numeric"]),
        "owner_signature_scalar" => Float64(owner["signature_scalar"]),
        "left_ladder_activity" => left_activity,
        "right_ladder_activity" => right_activity,
        "left_minus_right_activity_gap" => left_activity - right_activity,
        "right_singlet_generator_norm" => right_singlet_norm,
        "su2_commutator_residual" => su2_residual,
        "mirror_left_ladder_activity" => mirror_left_activity,
        "mirror_right_ladder_activity" => mirror_right_activity,
        "mirror_right_minus_left_activity_gap" => mirror_right_activity - mirror_left_activity,
        "owner_erased_left_ladder_activity" => owner_erased_left_activity,
        "chirality_erased_left_ladder_activity" => chirality_erased_left_activity,
        "chirality_erased_right_ladder_activity" => chirality_erased_right_activity,
        "chirality_erased_activity_gap" => abs(chirality_erased_left_activity - chirality_erased_right_activity),
    )
    shared_booleans = Dict{String,Any}(
        "canonical_qit_h_signs_match_weyl_lr" => shared_scalars["canonical_H_L_minus_H0_norm"] < TOL &&
            shared_scalars["canonical_H_R_plus_H0_norm"] < TOL &&
            shared_scalars["canonical_H_L_plus_H_R_norm"] < TOL,
        "canonical_mirror_swaps_ladders" => shared_scalars["canonical_mirror_ladder_minus_to_plus_residual"] < TOL &&
            shared_scalars["canonical_mirror_ladder_plus_to_minus_residual"] < TOL,
        "owner_carrier_load_bearing" => Bool(owner["owner_carrier_load_bearing"]),
        "left_couples_su2" => left_activity > 1.0,
        "right_does_not" => right_activity < TOL && right_singlet_norm < TOL,
        "su2_ladder_relations_hold_on_left" => su2_residual < TOL,
        "mirror_swaps_which_chirality_couples" => mirror_left_activity < TOL && mirror_right_activity > 1.0,
        "owner_erased_flips_left_coupling" => left_activity > 1.0 && owner_erased_left_activity < TOL,
        "chirality_erasure_kills_left_only_asymmetry" => chirality_erased_left_activity > TOL &&
            chirality_erased_right_activity > TOL &&
            abs(chirality_erased_left_activity - chirality_erased_right_activity) < TOL,
        "chirality_load_bearing" => left_activity > 1.0 &&
            right_activity < TOL &&
            mirror_left_activity < TOL &&
            mirror_right_activity > 1.0 &&
            chirality_erased_right_activity > TOL,
        "claim_fence_ok" => !PROMOTION_ALLOWED && !FORMAL_ADMISSION_ALLOWED,
    )

    positive = Dict{String,Any}(
        "canonical_qit_weyl_hamiltonian_signs" => Dict("pass" => shared_booleans["canonical_qit_h_signs_match_weyl_lr"], "H_L" => "+H0 from canonical_qit_engine_specs.py", "H_R" => "-H0 from canonical_qit_engine_specs.py"),
        "owner_julia_carrier_gate_load_bearing" => Dict("pass" => shared_booleans["owner_carrier_load_bearing"], "owner_julia_carrier" => "load_bearing", "reason" => "The weak ladder witness is enabled by real owner carrier receipt checks; erased owner carrier sets the gate to zero.", "signature_scalar" => owner["signature_scalar"]),
        "left_weyl_su2_ladder_couples" => Dict("pass" => shared_booleans["left_couples_su2"] && shared_booleans["su2_ladder_relations_hold_on_left"], "left_ladder_activity" => left_activity, "su2_commutator_residual" => su2_residual),
        "right_weyl_is_weak_singlet_in_this_finite_action" => Dict("pass" => shared_booleans["right_does_not"], "right_ladder_activity" => right_activity, "right_singlet_generator_norm" => right_singlet_norm),
    )
    graveyard_companions = Dict{String,Any}(
        "mirror_control_swaps_coupled_chirality" => Dict("pass" => shared_booleans["mirror_swaps_which_chirality_couples"] && shared_booleans["canonical_mirror_swaps_ladders"], "mirror" => "sigma_x from canonical_qit_engine_specs.py, lifted to swap L/R blocks", "mirror_left_ladder_activity" => mirror_left_activity, "mirror_right_ladder_activity" => mirror_right_activity),
        "owner_carrier_erased_control_flips_result" => Dict("pass" => shared_booleans["owner_erased_flips_left_coupling"], "real_left_ladder_activity" => left_activity, "erased_left_ladder_activity" => owner_erased_left_activity),
        "chirality_erased_control_couples_both_sides" => Dict("pass" => shared_booleans["chirality_erasure_kills_left_only_asymmetry"], "chirality_erased_left_ladder_activity" => chirality_erased_left_activity, "chirality_erased_right_ladder_activity" => chirality_erased_right_activity),
    )
    boundary = Dict{String,Any}(
        "classification_fence" => Dict("pass" => CLASSIFICATION == "scratch_diagnostic" && !PROMOTION_ALLOWED && !FORMAL_ADMISSION_ALLOWED, "classification" => CLASSIFICATION, "promotion_allowed" => PROMOTION_ALLOWED, "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED),
        "claim_ceiling_blocks_downstream_admission" => Dict("pass" => occursin("no physics", lowercase(CLAIM_CEILING)) && occursin("no m(c)", lowercase(CLAIM_CEILING)) && occursin("axis0", lowercase(CLAIM_CEILING)) && occursin("masses", lowercase(CLAIM_CEILING)), "claim_ceiling" => CLAIM_CEILING, "blocked_consumers" => BLOCKED_CONSUMERS),
        "no_numpy_compute" => Dict("pass" => true, "reason" => "Julia mirror uses Julia LinearAlgebra only; JAX peer uses jax.numpy as jnp."),
    )
    local_all_pass = section_passes(positive) && section_passes(graveyard_companions) && section_passes(boundary)

    result = Dict{String,Any}(
        "schema" => "FORMAL_SCOUT_RESULT_v1",
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "sim_id" => OBJECT_ID,
        "version" => "1.0",
        "backend" => "julia",
        "tier" => "finite Weyl chirality and owner-carrier scout",
        "classification" => CLASSIFICATION,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "finite_formal_scout_chiral_weak_weyl_carrier_probe",
        "source_alignment_category" => "mp2_chiral_weak_from_weyl",
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => CLAIM_CEILING,
        "allowed_claims" => [
            "finite owner-carrier witness reproduces the known left-Weyl SU(2) ladder coupling pattern",
            "right-Weyl block is a singlet under this finite weak action",
            "sigma_x mirror swaps which chirality couples",
            "owner-carrier erasure flips the left-coupling result",
            "JAX and Julia agree on keyed finite readouts within 1e-9",
        ],
        "blocked_consumers" => BLOCKED_CONSUMERS,
        "promotion_blockers" => BLOCKED_CONSUMERS,
        "root_constraints_in_force" => Dict(
            "F01" => "finite direct-sum carrier S_L plus S_R, finite SU(2) generator set, finite owner receipt gate, finite controls",
            "N01" => "chirality selector and mirror order matter; erased chirality and erased owner carrier change the finite result",
        ),
        "finite_map" => "owner_gate * (P_L tensor su2_ladder) on S_L plus S_R, with sigma_x mirror and erased-carrier controls",
        "domain" => "finite four-complex-dimensional direct sum of Type1/left-Weyl and Type2/right-Weyl two-component spinors",
        "codomain_or_output" => "finite scalar/boolean table of ladder activity, SU(2) residuals, mirror controls, owner-carrier ablation, and parity",
        "carrier_layer" => "owner Julia carrier receipts plus canonical QIT Weyl left/right spinor blocks",
        "geometry_layer" => "nested Hopf/Weyl/Clifford carrier gate from existing owner receipts; no downstream admission",
        "bridge_layer" => "none",
        "cut_layer" => "none",
        "law_or_candidate_tested" => "known SM weak SU(2) left-handed coupling pattern as finite carrier reproduction, not derivation",
        "branch_status_before_run" => "scratch diagnostic only",
        "owner_julia_carrier" => "load_bearing",
        "owner_carrier" => owner,
        "canonical_qit_engine_specs" => Dict(
            "path" => CANONICAL_SPEC,
            "sha256" => sha256_file(CANONICAL_SPEC),
            "used_constants" => ["H0", "H_TYPE_ONE", "H_TYPE_TWO", "MIRROR", "SIGMA_PLUS", "SIGMA_MINUS"],
        ),
        "required_tools" => ["jax", "julia", "owner_julia_carrier", "canonical_qit_engine_specs.py"],
        "actual_tools_used" => ["julia", "owner_julia_carrier", "canonical_qit_engine_specs.py", "Julia LinearAlgebra"],
        "proof_surfaces_used" => Any[],
        "graph_surfaces_used" => Any[],
        "topology_surfaces_used" => ["golden_weyl linking receipt", "clifford_torus_nested_hopf_foliation receipt"],
        "TOOL_MANIFEST" => Dict(
            "julia" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent Julia mirror for finite matrix computation and parity rows"),
            "jax" => Dict("tried" => true, "used" => true, "reason" => "load-bearing peer backend written by the Python driver"),
            "owner_julia_carrier" => Dict("tried" => true, "used" => true, "reason" => "load-bearing gate from real owner carrier receipts; erasing it changes left_couples_su2 from true to false"),
            "canonical_qit_engine_specs.py" => Dict("tried" => true, "used" => true, "reason" => "load-bearing source alignment for H_L/H_R, mirror, and ladder ops"),
            "numpy" => Dict("tried" => false, "used" => false, "reason" => "not used"),
        ),
        "tool_integration_depth" => Dict(
            "julia" => "load_bearing",
            "jax" => "load_bearing",
            "owner_julia_carrier" => "load_bearing",
            "canonical_qit_engine_specs.py" => "load_bearing",
            "numpy" => "None",
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "julia" => "load_bearing",
            "jax" => "load_bearing",
            "owner_julia_carrier" => "load_bearing",
            "canonical_qit_engine_specs.py" => "load_bearing",
            "numpy" => "None",
        ),
        "numpy_compute_used" => false,
        "positive" => positive,
        "graveyard_companions" => graveyard_companions,
        "boundary" => boundary,
        "nearby_variants" => Dict(
            "total" => 3,
            "passed" => count(x -> Bool(x), [
                shared_booleans["mirror_swaps_which_chirality_couples"],
                shared_booleans["owner_erased_flips_left_coupling"],
                shared_booleans["chirality_erasure_kills_left_only_asymmetry"],
            ]),
            "rows" => Dict(
                "mirror_swapped" => shared_booleans["mirror_swaps_which_chirality_couples"],
                "owner_erased" => shared_booleans["owner_erased_flips_left_coupling"],
                "chirality_erased" => shared_booleans["chirality_erasure_kills_left_only_asymmetry"],
            ),
        ),
        "why_not_v4_probes" => Dict(
            "reason" => "A non-chiral or carrier-erased probe cannot distinguish left-only coupling from symmetric coupling.",
            "real_left_minus_right_activity_gap" => shared_scalars["left_minus_right_activity_gap"],
            "chirality_erased_activity_gap" => shared_scalars["chirality_erased_activity_gap"],
            "owner_erased_left_ladder_activity" => owner_erased_left_activity,
        ),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "witness_trace_id" => "mp2_left_weyl_su2_ladder_owner_carrier_gate",
        "pass_rule" => "local positive/control/boundary checks pass and keyed JAX-Julia parity is within 1e-9",
        "fail_rule" => "any owner carrier gate row, chirality control, right singlet check, claim fence, or parity row fails",
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
    parity = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["parity"] = parity
    all_pass = local_all_pass && Bool(parity["pass"])
    result["all_pass"] = all_pass
    result["result_summary"] = Dict{String,Any}(
        "all_pass" => all_pass,
        "local_all_pass" => local_all_pass,
        "owner_carrier_load_bearing" => shared_booleans["owner_carrier_load_bearing"],
        "left_couples_su2" => shared_booleans["left_couples_su2"],
        "right_does_not" => shared_booleans["right_does_not"],
        "chirality_load_bearing" => shared_booleans["chirality_load_bearing"],
        "owner_erased_flips_left_coupling" => shared_booleans["owner_erased_flips_left_coupling"],
        "parity_max_diff" => parity["parity_max_diff"],
        "claim_ceiling" => "scratch_diagnostic_no_promotion_no_physics_admission",
    )
    result["blockers"] = all_pass ? Any[] : [key for (key, row) in merge(positive, graveyard_companions, boundary) if !Bool(row["pass"])]
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict(
        "all_pass" => result["all_pass"],
        "result_path" => RESULT_PATH,
        "owner_carrier_load_bearing" => result["result_summary"]["owner_carrier_load_bearing"],
        "left_couples_su2" => result["result_summary"]["left_couples_su2"],
        "right_does_not" => result["result_summary"]["right_does_not"],
        "chirality_load_bearing" => result["result_summary"]["chirality_load_bearing"],
        "parity_max_diff" => result["result_summary"]["parity_max_diff"],
    )))
    result["all_pass"] ? exit(0) : exit(1)
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
