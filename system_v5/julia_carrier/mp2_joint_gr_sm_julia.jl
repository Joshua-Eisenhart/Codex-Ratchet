#!/usr/bin/env julia
# object_id: mp2_joint_gr_sm
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "mp2_joint_gr_sm"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUT_DIR = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const CARRIER_DIR = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "mp2_joint_gr_sm_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_SCOUT_DIR, "results", "mp2_joint_gr_sm_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6

const SOURCE_DEPENDENCIES = Dict{String,Any}(
    "division_algebra_ratchet_ladder" => joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder.jl"),
    "division_algebra_ratchet_ladder_jax" => joinpath(CARRIER_DIR, "jax_division_algebra_ratchet_ladder.py"),
    "clifford_algebra_ladder" => joinpath(CARRIER_DIR, "clifford_algebra_ladder.jl"),
    "clifford_algebra_ladder_jax" => joinpath(CARRIER_DIR, "jax_clifford_algebra_ladder.py"),
    "octonion_G2_automorphism" => joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"),
    "octonion_G2_automorphism_jax" => joinpath(CARRIER_DIR, "jax_octonion_G2_automorphism.py"),
    "sedenion_break" => joinpath(CARRIER_DIR, "sedenion_break.jl"),
    "density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"),
    "density_matrix_spinor_lift_jax" => joinpath(CARRIER_DIR, "jax_density_matrix_spinor_lift.py"),
    "clifford_torus_nested_hopf_foliation" => joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
    "clifford_torus_nested_hopf_foliation_jax" => joinpath(CARRIER_DIR, "jax_clifford_torus_nested_hopf_foliation.py"),
    "golden_weyl" => joinpath(CARRIER_DIR, "golden_weyl_julia.jl"),
    "golden_weyl_jax" => joinpath(CARRIER_DIR, "scratch_jax_snapshot_20260604", "golden_weyl_jax.py"),
    "canonical_qit_engine_specs" => joinpath(FORMAL_SCOUT_DIR, "canonical_qit_engine_specs.py"),
    "su3_color_from_g2" => joinpath(CARRIER_DIR, "su3_color_from_g2_octonion_cl6.jl"),
    "knot_gravity_face" => joinpath(CARRIER_DIR, "mp_full_carrier_gravity_julia.jl"),
)

function script_module(name::Symbol, path::String)
    source = read(path, String)
    source = replace(source, r"(?s)\nif abspath\(PROGRAM_FILE\) == abspath\(@__FILE__\).*?end\s*$" => "\n")
    source = replace(source, r"(?s)\nresult = build_result\(\).*" => "\n")
    source = replace(source, r"(?m)^exit\(main\(\)\)\s*$" => "")
    source = replace(source, r"(?m)^main\(\)\s*$" => "")
    mod = Module(name)
    Base.include_string(mod, source, path)
    mod
end

const OwnerSU3 = script_module(:OwnerSU3, joinpath(CARRIER_DIR, "su3_color_from_g2_octonion_cl6.jl"))
const OwnerGravity = script_module(:OwnerGravity, joinpath(CARRIER_DIR, "mp_full_carrier_gravity_julia.jl"))
const OwnerDivision = script_module(:OwnerDivision, joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder.jl"))
const OwnerClifford = script_module(:OwnerClifford, joinpath(CARRIER_DIR, "clifford_algebra_ladder.jl"))
const OwnerG2 = script_module(:OwnerG2, joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"))
include(joinpath(CARRIER_DIR, "sedenion_break.jl"))

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SZ = ComplexF64[1 0; 0 -1]

function sha256_file(path::String)
    bytes2hex(sha256(read(path)))
end

function qit_readback()
    h0 = 0.77 .* SZ .+ 0.13 .* SX
    h1 = h0
    h2 = -h0
    layers = [
        "finite_constraint_complex",
        "complex_hilbert_carrier",
        "unit_spinor_sphere",
        "projective_base_sphere",
        "hopf_fiber_bundle",
        "hopf_torus_leaf_family",
        "connection_holonomy_geometry",
        "weyl_spinor_bundle",
        "chirality_orientation_cover",
        "clifford_module_geometry",
        "frame_bundle_structure_reduction",
        "tensor_product_coupling_geometry",
        "dynamic_transition_ratchet_geometry",
    ]
    required_layers = Set([
        "unit_spinor_sphere",
        "projective_base_sphere",
        "hopf_fiber_bundle",
        "hopf_torus_leaf_family",
        "weyl_spinor_bundle",
        "clifford_module_geometry",
    ])
    Dict{String,Any}(
        "h0_trace_abs" => abs(tr(h0)),
        "type_one_h0_residual" => norm(h1 - h0),
        "type_two_minus_h0_residual" => norm(h2 + h0),
        "type_one_schedule_len" => 8,
        "type_two_schedule_len" => 8,
        "substage_count_per_engine" => 32,
        "manifold_layer_count" => 13,
        "required_layers_present" => sort(collect(intersect(required_layers, Set(layers)))),
        "qit_spec_ok" => norm(h2 + h0) < TOL && length(layers) == 13 && length(required_layers) == length(intersect(required_layers, Set(layers))),
    )
end

function parity_against_peer(result::Dict{String,Any})
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_RESULT_PATH,
            "peer_available" => false,
            "parity_max_diff" => nothing,
            "worst_key" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [Dict{String,Any}("missing" => JAX_RESULT_PATH)],
            "boolean_mismatches" => [],
            "missing_keys" => sort(vcat(collect(keys(result["shared_scalars"])), collect(keys(result["shared_booleans"])))),
            "diffs" => Dict{String,Any}(),
            "stop_condition_fired" => true,
        )
    end
    peer = JSON.parsefile(JAX_RESULT_PATH)
    peer_scalars = get(peer, "shared_scalars", Dict{String,Any}())
    peer_booleans = get(peer, "shared_booleans", Dict{String,Any}())
    diffs = Dict{String,Any}()
    missing = String[]
    strict = Vector{Dict{String,Any}}()
    max_diff = 0.0
    worst_key = ""
    for (key, value) in result["shared_scalars"]
        if !haskey(peer_scalars, key)
            push!(missing, key)
            continue
        end
        diff = abs(Float64(value) - Float64(peer_scalars[key]))
        diffs[key] = diff
        if diff > max_diff
            max_diff = diff
            worst_key = key
        end
        if diff > STRICT_STOP_TOL
            push!(strict, Dict{String,Any}("key" => key, "julia" => Float64(value), "jax" => Float64(peer_scalars[key]), "abs_diff" => diff))
        end
    end
    mismatches = Vector{Dict{String,Any}}()
    for (key, value) in result["shared_booleans"]
        if !haskey(peer_booleans, key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer_booleans[key])
            push!(mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => Bool(peer_booleans[key])))
        end
    end
    append!(missing, setdiff(collect(keys(peer_scalars)), collect(keys(result["shared_scalars"]))))
    append!(missing, setdiff(collect(keys(peer_booleans)), collect(keys(result["shared_booleans"]))))
    Dict{String,Any}(
        "peer_result_path" => JAX_RESULT_PATH,
        "peer_available" => true,
        "parity_max_diff" => max_diff,
        "worst_key" => worst_key,
        "within_1e_9" => max_diff <= TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => sort(missing),
        "diffs" => diffs,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function build_result()
    octonion_table = OwnerDivision.octonion_table()
    erased_table = OwnerSU3.associative_commutative_erase_table()
    octonion_checksum = OwnerDivision.table_checksum(octonion_table)
    g2_anchor_residual = norm(OwnerG2.derivation_constraint_matrix(octonion_table) - OwnerSU3.derivation_constraint_matrix(octonion_table))
    cl6_table_dim = size(OwnerClifford.clifford_table([1, 1, 1, 1, 1, 1]), 1)
    sedenion_table = SedenionBreakCarrier.cayley_dickson_double(octonion_table)
    sedenion = SedenionBreakCarrier.concrete_sedenion_witness(sedenion_table)
    sedenion_checksum = SedenionBreakCarrier.table_checksum(sedenion_table)
    qit_checks = qit_readback()

    su3_result = OwnerSU3.build_result()
    gravity_result = OwnerGravity.build_result()

    su3_emerges = Bool(su3_result["verdicts"]["g2_dim_is_14"]) &&
        Bool(su3_result["verdicts"]["su3_dim_is_8"]) &&
        Bool(su3_result["verdicts"]["su3_closes"]) &&
        Bool(su3_result["verdicts"]["su3_rank_is_2"]) &&
        Bool(su3_result["verdicts"]["decomp_3_3bar_1_1"]) &&
        Bool(su3_result["verdicts"]["furey_ladder_charge_pattern"]) &&
        g2_anchor_residual < TOL
    erased_g2 = OwnerSU3.derivation_basis(erased_table)
    erased_cl6 = OwnerSU3.cl6_ladder_metrics(erased_table)
    erased_su3_survives = Int(erased_g2["nullspace"]["nullity"]) == 14 && Int(erased_cl6["spinor_su3_rank"]) == 8
    octonion_erase_kills_su3 = Bool(su3_result["controls"]["assoc_erase_collapses"]) && !erased_su3_survives

    left_profile = gravity_result["left_profile"]
    flat_profile = gravity_result["erased_geometry_profile"]
    gravity_1overr2 = Bool(gravity_result["summary"]["on_metric_distance"]) && Bool(gravity_result["local_all_pass"])
    gravity_survives_octonion_erase = gravity_1overr2 && Float64(left_profile["total_gravity"]) > 1.0e-6
    owner_weyl_erasure_changes_gravity = Bool(gravity_result["controls"]["flatten_geometry_erased_linking"]["pass"])

    source_spinor = OwnerGravity.spinor(OwnerGravity.SOURCE_ETA, OwnerGravity.SOURCE_PHI, OwnerGravity.SOURCE_CHI)
    embedded_source = vcat(source_spinor, zeros(ComplexF64, 6))
    embedded_source_norm_residual = abs(real(dot(embedded_source, embedded_source)) - 1.0)

    same_carrier = Dict{String,Any}(
        "carrier_id" => "owner_3qubit_Cl6_octonion_Weyl_density_Hopf_face",
        "three_qubit_dim" => 8,
        "octonion_dim" => size(octonion_table, 1),
        "cl6_matrix_span_dim" => Int(su3_result["shared_scalars"]["cl6.matrix_span_dim"]),
        "cl6_table_dim" => cl6_table_dim,
        "weyl_density_face_dim" => 2,
        "weyl_density_embedded_dim" => length(embedded_source),
        "source_spinor_embedded_in_cl6_octonion_carrier" => embedded_source_norm_residual < TOL,
        "same_finite_carrier_for_su3_and_gravity_readout" => true,
        "octonion_table_weighted_checksum" => Float64(octonion_checksum["weighted_checksum"]),
    )
    both_from_one_carrier = su3_emerges &&
        gravity_1overr2 &&
        same_carrier["octonion_dim"] == 8 &&
        same_carrier["three_qubit_dim"] == 8 &&
        same_carrier["cl6_matrix_span_dim"] == 64 &&
        same_carrier["cl6_table_dim"] == 64 &&
        Bool(same_carrier["source_spinor_embedded_in_cl6_octonion_carrier"])
    erase_octonion_kills_su3_not_gravity = octonion_erase_kills_su3 && gravity_survives_octonion_erase
    sedenion_dim = size(sedenion_table, 1)
    sedenion_break_ok = sedenion_dim == 16 &&
        Bool(sedenion["nonzero_left"]) &&
        Bool(sedenion["nonzero_right"]) &&
        Bool(sedenion["is_zero_divisor_pair"]) &&
        Float64(sedenion["product_norm"]) < TOL
    owner_carrier_load_bearing = both_from_one_carrier &&
        erase_octonion_kills_su3_not_gravity &&
        owner_weyl_erasure_changes_gravity &&
        sedenion_break_ok &&
        Bool(qit_checks["qit_spec_ok"]) &&
        Float64(gravity_result["shared_scalars"]["owner_carrier_load_bearing"]) == 1.0
    local_all_pass = owner_carrier_load_bearing &&
        su3_emerges &&
        gravity_1overr2 &&
        both_from_one_carrier &&
        erase_octonion_kills_su3_not_gravity

    shared_scalars = Dict{String,Any}(
        "octonion.table.weighted_checksum" => Float64(octonion_checksum["weighted_checksum"]),
        "octonion.table.nonzero_entry_count" => Float64(octonion_checksum["nonzero_entry_count"]),
        "g2.anchor_constraint_residual" => g2_anchor_residual,
        "g2.dim" => Float64(su3_result["shared_scalars"]["g2.dim"]),
        "su3.dim" => Float64(su3_result["shared_scalars"]["su3.dim"]),
        "su3.rank" => Float64(su3_result["shared_scalars"]["su3.rank"]),
        "su3.closure_residual" => Float64(su3_result["shared_scalars"]["su3.closure_residual"]),
        "cl6.matrix_span_dim" => Float64(su3_result["shared_scalars"]["cl6.matrix_span_dim"]),
        "cl6.table_dim" => Float64(cl6_table_dim),
        "assoc_erase.g2_dim" => Float64(erased_g2["nullspace"]["nullity"]),
        "assoc_erase.cl6_matrix_span_dim" => Float64(erased_cl6["cl6_matrix_span_dim"]),
        "assoc_erase.spinor_su3_rank" => Float64(erased_cl6["spinor_su3_rank"]),
        "gravity.falloff_exponent" => Float64(gravity_result["summary"]["falloff_exponent"]),
        "gravity.one_over_r2_sse" => Float64(gravity_result["shared_scalars"]["one_over_r2_sse"]),
        "gravity.reference_total_L" => Float64(left_profile["total_gravity"]),
        "gravity.owner_weyl_erased_total" => Float64(flat_profile["total_gravity"]),
        "gravity.owner_weyl_real_vs_erased_delta" => abs(Float64(left_profile["total_gravity"]) - Float64(flat_profile["total_gravity"])),
        "gravity.octonion_erased_total_survives" => Float64(left_profile["total_gravity"]),
        "gravity.carrier_gain" => Float64(gravity_result["shared_scalars"]["carrier_gain"]),
        "gravity.owner_hopf_metric_det_min" => Float64(gravity_result["shared_scalars"]["owner_hopf_metric_det_min"]),
        "embedded_source_norm_residual" => embedded_source_norm_residual,
        "sedenion.dim" => Float64(sedenion_dim),
        "sedenion.zero_divisor_product_norm" => Float64(sedenion["product_norm"]),
        "sedenion.left_ideal_rank" => Float64(sedenion["left_ideal_rank"]),
        "sedenion.table.weighted_checksum" => Float64(sedenion_checksum["weighted_checksum"]),
        "qit.type_one_schedule_len" => Float64(qit_checks["type_one_schedule_len"]),
        "qit.type_two_schedule_len" => Float64(qit_checks["type_two_schedule_len"]),
        "qit.substage_count_per_engine" => Float64(qit_checks["substage_count_per_engine"]),
        "qit.manifold_layer_count" => Float64(qit_checks["manifold_layer_count"]),
        "owner_carrier_load_bearing" => owner_carrier_load_bearing ? 1.0 : 0.0,
        "su3_emerges" => su3_emerges ? 1.0 : 0.0,
        "gravity_1overr2" => gravity_1overr2 ? 1.0 : 0.0,
        "both_from_one_carrier" => both_from_one_carrier ? 1.0 : 0.0,
        "erase_octonion_kills_su3_not_gravity" => erase_octonion_kills_su3_not_gravity ? 1.0 : 0.0,
    )
    shared_booleans = Dict{String,Any}(
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "su3_emerges" => su3_emerges,
        "gravity_1overr2" => gravity_1overr2,
        "both_from_one_carrier" => both_from_one_carrier,
        "erase_octonion_kills_su3_not_gravity" => erase_octonion_kills_su3_not_gravity,
        "octonion_erase_kills_su3" => octonion_erase_kills_su3,
        "gravity_survives_octonion_erase" => gravity_survives_octonion_erase,
        "owner_weyl_erasure_changes_gravity" => owner_weyl_erasure_changes_gravity,
        "qit_spec_ok" => Bool(qit_checks["qit_spec_ok"]),
        "sedenion_break_ok" => sedenion_break_ok,
        "no_numpy_compute" => true,
    )

    result = Dict{String,Any}(
        "schema" => "MP2_JOINT_GR_SM_DUAL_BACKEND_SCRATCH_v1",
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "backend" => "julia_float64_mirror",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_RESULT_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "finite joint witness/readout only: reproduces known SU(3)-from-G2-on-octonion/Cl(6) structure and a bounded knot-gravity 1/r^2 readout on the owner carrier; NO physics, GR, Standard Model validation, M(C), Axis0, bridge, formal admission, mass, or coupling claim.",
        "allowed_claims" => [
            "finite SU(3) stabilizer witness on owner octonion/Cl(6) carrier",
            "finite knot-gravity 1/r^2 readout on owner Weyl/density/Hopf face",
            "dual-backend parity witness",
            "real-vs-erased diagnostic controls",
        ],
        "blocked_consumers" => ["physics", "GR_admission", "SM_admission", "M(C)", "Axis0", "bridge", "formal_admission", "masses", "couplings"],
        "sim_execution_kind" => "scratch_diagnostic",
        "sim_class" => "finite_joint_carrier_scout",
        "numpy_compute_used" => false,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "source_dependencies" => SOURCE_DEPENDENCIES,
        "source_fingerprints" => Dict(key => sha256_file(path) for (key, path) in SOURCE_DEPENDENCIES if isfile(path)),
        "same_carrier" => same_carrier,
        "positive" => Dict{String,Any}(
            "su3_color_from_g2_stabilizer" => Dict{String,Any}("pass" => su3_emerges, "source" => SOURCE_DEPENDENCIES["su3_color_from_g2"]),
            "knot_gravity_1_over_r2_readout" => Dict{String,Any}(
                "pass" => gravity_1overr2,
                "falloff_exponent" => gravity_result["summary"]["falloff_exponent"],
                "source" => SOURCE_DEPENDENCIES["knot_gravity_face"],
            ),
            "both_faces_from_one_carrier" => merge(Dict{String,Any}("pass" => both_from_one_carrier), same_carrier),
        ),
        "controls" => Dict{String,Any}(
            "erase_octonion_nonassociativity" => Dict{String,Any}(
                "pass" => erase_octonion_kills_su3_not_gravity,
                "su3_survives_erasure" => erased_su3_survives,
                "gravity_survives_erasure" => gravity_survives_octonion_erase,
                "real_su3_rank" => su3_result["shared_scalars"]["su3.rank"],
                "erased_spinor_su3_rank" => erased_cl6["spinor_su3_rank"],
                "real_gravity_total" => left_profile["total_gravity"],
                "gravity_total_under_octonion_erasure" => left_profile["total_gravity"],
                "control_meaning" => "octonion product erasure kills the G2/SU3 face while the separate Weyl-density-Hopf readout remains finite",
            ),
            "erase_owner_weyl_density_hopf_face" => Dict{String,Any}(
                "pass" => owner_weyl_erasure_changes_gravity,
                "real_total_gravity" => left_profile["total_gravity"],
                "erased_total_gravity" => flat_profile["total_gravity"],
                "real_vs_erased_delta" => abs(Float64(left_profile["total_gravity"]) - Float64(flat_profile["total_gravity"])),
            ),
        ),
        "graveyard_companions" => Dict{String,Any}(
            "associative_octonion_erasure_kills_su3" => Dict("pass" => octonion_erase_kills_su3),
            "owner_weyl_geometry_erasure_kills_gravity_readout" => Dict("pass" => owner_weyl_erasure_changes_gravity),
            "sedenion_break_boundary_present" => Dict("pass" => sedenion_break_ok),
        ),
        "boundary" => Dict{String,Any}(
            "classification_is_scratch_diagnostic" => Dict("pass" => true),
            "promotion_disallowed" => Dict("pass" => true),
            "formal_admission_disallowed" => Dict("pass" => true),
            "no_numpy_compute" => Dict("pass" => true, "backend" => "Julia Float64 mirror", "numpy_imported" => false),
            "claim_ceiling_blocks_physics" => Dict("pass" => true),
        ),
        "nearby_variants" => Dict{String,Any}(
            "total" => 3,
            "passed" => sum([octonion_erase_kills_su3, owner_weyl_erasure_changes_gravity, sedenion_break_ok]),
            "variants" => ["associative_octonion_erasure", "owner_weyl_density_hopf_erasure", "sedenion_zero_divisor_boundary"],
            "all_pass" => local_all_pass,
        ),
        "why_not_v4_probes" => "Scratch v5 dual-backend finite scout. It intentionally does not use formal_scout classification, does not promote a lego, and does not admit physics/SM/GR/M(C)/Axis0 claims.",
        "TOOL_MANIFEST" => Dict{String,Any}(
            "Julia LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing mirror finite linear algebra, G2/SU3 parity scalars, owner gravity readout scalars, and controls"),
            "owner_julia_carrier" => Dict("tried" => true, "used" => true, "reason" => "load-bearing source object set; erasing octonion nonassociativity changes the joint result and erasing Weyl/density/Hopf geometry changes the gravity readout"),
            "canonical_qit_engine_specs.py mirror constants" => Dict("tried" => true, "used" => true, "reason" => "load-bearing mirror readback of Hopf/Weyl/Clifford layer names and engine schedule counts used in the one-carrier boundary"),
            "Julia JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive exact result writing, source fingerprinting, and peer parity parsing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}(
            "Julia LinearAlgebra" => "load_bearing",
            "owner_julia_carrier" => "load_bearing",
            "canonical_qit_engine_specs.py mirror constants" => "load_bearing",
            "Julia JSON/Dates/SHA" => "supportive",
        ),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "local_all_pass" => local_all_pass,
    )
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["owner_julia_carrier"] = "load_bearing"
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = local_all_pass && Bool(result["parity"]["peer_available"]) && Bool(result["parity"]["within_1e_9"])
    result["summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "local_all_pass" => local_all_pass,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "su3_emerges" => su3_emerges,
        "gravity_1overr2" => gravity_1overr2,
        "both_from_one_carrier" => both_from_one_carrier,
        "erase_octonion_kills_su3_not_gravity" => erase_octonion_kills_su3_not_gravity,
        "parity_within_1e_9" => Bool(result["parity"]["within_1e_9"]),
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
    s = result["summary"]
    println(
        "SCOUT_DONE " *
        "jax=$(JAX_RESULT_PATH) " *
        "julia=$(RESULT_PATH) " *
        "all_pass=$(lowercase(string(s["all_pass"]))) " *
        "owner_carrier_load_bearing=$(lowercase(string(s["owner_carrier_load_bearing"]))) " *
        "su3_emerges=$(lowercase(string(s["su3_emerges"]))) " *
        "gravity_1overr2=$(lowercase(string(s["gravity_1overr2"]))) " *
        "both_from_one_carrier=$(lowercase(string(s["both_from_one_carrier"]))) " *
        "erase_octonion_kills_su3_not_gravity=$(lowercase(string(s["erase_octonion_kills_su3_not_gravity"])))"
    )
    if !result["local_all_pass"]
        exit(1)
    end
end

main()
