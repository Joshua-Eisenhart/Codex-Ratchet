#!/usr/bin/env julia
# object_id: mc_first_admissibility_packet
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "mc_first_admissibility_packet"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/mc_first_admissibility_packet_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/mc_first_admissibility_packet_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const CLASSIFICATION = "scratch_diagnostic"
const CLAIM_CEILING = "first finite M(C) admissibility packet; NOT a physics bridge, NOT Axis0, NOT a QIT engine, NOT final M(C) admission"

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing finite carrier construction, density lift, Pauli order gaps, quotient, controls, and parity scalars",
    ),
    "LinearAlgebra" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing spinor/density norms, order-gap reductions, and projection checks",
    ),
    "JSON" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization and peer-result parity loading",
    ),
    "numpy" => Dict{String,Any}(
        "tried" => false,
        "used" => false,
        "reason" => "not part of the Julia mirror; recorded false for dual-backend no-NumPy boundary",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "JSON" => "supportive",
    "numpy" => nothing,
)

finite_round(value::Real, digits::Int = 12) = round(Float64(value); digits = digits)

function spinor_from_hopf(eta::Float64, phi::Float64, chi::Float64, phase::Float64, scale::Float64)
    psi = ComplexF64[
        exp(im * (phi + chi)) * cos(eta),
        exp(im * (phi - chi)) * sin(eta),
    ]
    scale .* exp(im * phase) .* psi
end

density(psi::Vector{ComplexF64}) = psi * psi'

function bloch_from_rho(rho::Matrix{ComplexF64})
    Float64[real(tr(rho * SX)), real(tr(rho * SY)), real(tr(rho * SZ))]
end

function operators(order_word::String)
    order_word == "XY" && return SX, SY
    order_word == "YX" && return SY, SX
    order_word == "XX" && return SX, SX
    error("unknown order_word: $order_word")
end

function project_to_unit(psi::Vector{ComplexF64})
    n = norm(psi)
    n > TOL ? psi ./ n : psi
end

function candidate_specs()
    eta_core = pi / 4.0
    eta_offset = pi / 6.0
    [
        Dict{String,Any}(
            "id" => "L_core_XY",
            "sheet" => "L",
            "eta_index" => 1,
            "eta" => eta_core,
            "phi" => 0.0,
            "chi" => 0.0,
            "phase" => 0.0,
            "scale" => 1.0,
            "order_word" => "XY",
            "finite_encoding" => true,
            "composition_projection_enabled" => true,
            "role" => "positive_phase_representative",
        ),
        Dict{String,Any}(
            "id" => "L_core_XY_phase_pi",
            "sheet" => "L",
            "eta_index" => 1,
            "eta" => eta_core,
            "phi" => 0.0,
            "chi" => 0.0,
            "phase" => pi,
            "scale" => 1.0,
            "order_word" => "XY",
            "finite_encoding" => true,
            "composition_projection_enabled" => true,
            "role" => "positive_density_equivalent_phase",
        ),
        Dict{String,Any}(
            "id" => "R_core_XY",
            "sheet" => "R",
            "eta_index" => 1,
            "eta" => eta_core,
            "phi" => 0.0,
            "chi" => 0.0,
            "phase" => 0.0,
            "scale" => 1.0,
            "order_word" => "XY",
            "finite_encoding" => true,
            "composition_projection_enabled" => true,
            "role" => "positive_other_sheet",
        ),
        Dict{String,Any}(
            "id" => "R_core_XY_phase_pi",
            "sheet" => "R",
            "eta_index" => 1,
            "eta" => eta_core,
            "phi" => 0.0,
            "chi" => 0.0,
            "phase" => pi,
            "scale" => 1.0,
            "order_word" => "XY",
            "finite_encoding" => true,
            "composition_projection_enabled" => true,
            "role" => "positive_other_sheet_density_equivalent_phase",
        ),
        Dict{String,Any}(
            "id" => "L_eta2_YX",
            "sheet" => "L",
            "eta_index" => 2,
            "eta" => eta_offset,
            "phi" => 0.0,
            "chi" => 0.0,
            "phase" => 0.0,
            "scale" => 1.0,
            "order_word" => "YX",
            "finite_encoding" => true,
            "composition_projection_enabled" => true,
            "role" => "positive_order_orientation_variant",
        ),
        Dict{String,Any}(
            "id" => "commutative_XX_control",
            "sheet" => "L",
            "eta_index" => 1,
            "eta" => eta_core,
            "phi" => 0.0,
            "chi" => 0.0,
            "phase" => 0.0,
            "scale" => 1.0,
            "order_word" => "XX",
            "finite_encoding" => true,
            "composition_projection_enabled" => true,
            "role" => "graveyard_N01_commutative",
        ),
        Dict{String,Any}(
            "id" => "composition_projection_missing_control",
            "sheet" => "L",
            "eta_index" => 2,
            "eta" => eta_offset,
            "phi" => 0.0,
            "chi" => 0.0,
            "phase" => 0.0,
            "scale" => 1.0,
            "order_word" => "XY",
            "finite_encoding" => true,
            "composition_projection_enabled" => false,
            "role" => "graveyard_composition_rule",
        ),
        Dict{String,Any}(
            "id" => "nonfinite_global_coordinate_control",
            "sheet" => "L",
            "eta_index" => 1,
            "eta" => eta_core,
            "phi" => 0.0,
            "chi" => 0.0,
            "phase" => 0.0,
            "scale" => 1.0,
            "order_word" => "XY",
            "finite_encoding" => false,
            "composition_projection_enabled" => true,
            "role" => "graveyard_F01_nonfinite_encoding",
        ),
        Dict{String,Any}(
            "id" => "unnormalized_spinor_control",
            "sheet" => "R",
            "eta_index" => 2,
            "eta" => eta_offset,
            "phi" => 0.0,
            "chi" => 0.0,
            "phase" => 0.0,
            "scale" => 2.0,
            "order_word" => "XY",
            "finite_encoding" => true,
            "composition_projection_enabled" => true,
            "role" => "graveyard_F01_probe_norm",
        ),
    ]
end

function analyze_candidate(spec::Dict{String,Any})
    psi = spinor_from_hopf(Float64(spec["eta"]), Float64(spec["phi"]), Float64(spec["chi"]), Float64(spec["phase"]), Float64(spec["scale"]))
    rho = density(psi)
    bloch = bloch_from_rho(rho)
    a_op, b_op = operators(String(spec["order_word"]))
    left = a_op * (b_op * psi)
    right = b_op * (a_op * psi)
    projected_left = project_to_unit(left)
    order_delta = left - right
    spinor_norm = real(dot(psi, psi))
    trace_rho = real(tr(rho))
    order_gap = norm(order_delta)
    order_orientation = imag(dot(psi, order_delta))
    projected_norm_residual = abs(real(dot(projected_left, projected_left)) - 1.0)
    density_phase_blind_key = [
        finite_round(bloch[1], 12),
        finite_round(bloch[2], 12),
        finite_round(bloch[3], 12),
    ]
    finite_probe_outputs = Dict{String,Any}(
        "sheet" => spec["sheet"],
        "eta_index" => Int(spec["eta_index"]),
        "rho_bloch" => density_phase_blind_key,
        "order_word" => spec["order_word"],
        "order_gap_bin" => order_gap > TOL ? 1 : 0,
        "order_orientation_sign" => order_orientation > TOL ? 1 : (order_orientation < -TOL ? -1 : 0),
        "composition_projected" => Bool(spec["composition_projection_enabled"]),
    )
    finite_parts = all(isfinite, real.(psi)) && all(isfinite, imag.(psi))
    f01_pass = Bool(spec["finite_encoding"]) &&
        abs(spinor_norm - 1.0) <= TOL &&
        abs(trace_rho - 1.0) <= TOL &&
        finite_parts
    n01_pass = order_gap > TOL
    probe_rules_pass = abs(spinor_norm - 1.0) <= TOL &&
        abs(trace_rho - 1.0) <= TOL &&
        all(v -> abs(v) <= 1.0 + TOL, density_phase_blind_key)
    composition_rules_pass = Bool(spec["composition_projection_enabled"]) && projected_norm_residual <= TOL
    adm = f01_pass && n01_pass && probe_rules_pass && composition_rules_pass
    fail_reasons = String[]
    !f01_pass && push!(fail_reasons, "F01_FINITUDE")
    !n01_pass && push!(fail_reasons, "N01_NONCOMMUTATION")
    !probe_rules_pass && push!(fail_reasons, "admissible_probe_rules")
    !composition_rules_pass && push!(fail_reasons, "admissible_composition_rules")
    Dict{String,Any}(
        "id" => spec["id"],
        "role" => spec["role"],
        "sheet" => spec["sheet"],
        "eta_index" => Int(spec["eta_index"]),
        "order_word" => spec["order_word"],
        "finite_encoding" => Bool(spec["finite_encoding"]),
        "spinor_components" => [
            [finite_round(real(psi[1]), 15), finite_round(imag(psi[1]), 15)],
            [finite_round(real(psi[2]), 15), finite_round(imag(psi[2]), 15)],
        ],
        "density_matrix" => [
            [
                [finite_round(real(rho[1, 1]), 15), finite_round(imag(rho[1, 1]), 15)],
                [finite_round(real(rho[1, 2]), 15), finite_round(imag(rho[1, 2]), 15)],
            ],
            [
                [finite_round(real(rho[2, 1]), 15), finite_round(imag(rho[2, 1]), 15)],
                [finite_round(real(rho[2, 2]), 15), finite_round(imag(rho[2, 2]), 15)],
            ],
        ],
        "bloch" => [finite_round(bloch[1], 15), finite_round(bloch[2], 15), finite_round(bloch[3], 15)],
        "checks" => Dict{String,Any}(
            "spinor_norm" => spinor_norm,
            "trace_rho" => trace_rho,
            "order_gap" => order_gap,
            "order_orientation" => order_orientation,
            "projected_norm_residual" => projected_norm_residual,
        ),
        "finite_probe_outputs" => finite_probe_outputs,
        "constraint_checks" => Dict{String,Any}(
            "F01_FINITUDE" => f01_pass,
            "N01_NONCOMMUTATION" => n01_pass,
            "admissible_probe_rules" => probe_rules_pass,
            "admissible_composition_rules" => composition_rules_pass,
        ),
        "Adm_C" => adm,
        "fail_reasons" => fail_reasons,
    )
end

function signature_key(signature::Dict{String,Any})
    JSON.json(signature)
end

function quotient(candidates::Vector{Dict{String,Any}}, probe_names::Vector{String})
    classes = Dict{String,Vector{String}}()
    signatures = Dict{String,Dict{String,Any}}()
    for row in candidates
        probes = row["finite_probe_outputs"]
        signature = Dict{String,Any}()
        for name in probe_names
            signature[name] = probes[name]
        end
        key = signature_key(signature)
        if !haskey(classes, key)
            classes[key] = String[]
        end
        push!(classes[key], String(row["id"]))
        signatures[key] = signature
    end
    ordered = Vector{Dict{String,Any}}()
    for (idx, key) in enumerate(sort(collect(keys(classes))))
        push!(ordered, Dict{String,Any}(
            "class_id" => "q$(idx - 1)",
            "members" => sort(classes[key]),
            "signature" => signatures[key],
        ))
    end
    Dict{String,Any}(
        "probe_names" => probe_names,
        "class_count" => length(ordered),
        "classes" => ordered,
    )
end

function adjacency(classes::Vector{Dict{String,Any}})
    edges = Vector{Dict{String,Any}}()
    for i in 1:length(classes)
        for j in (i + 1):length(classes)
            j > length(classes) && continue
            left = classes[i]
            right = classes[j]
            differing = String[]
            for key in keys(left["signature"])
                if left["signature"][key] != right["signature"][key]
                    push!(differing, key)
                end
            end
            if length(differing) == 1
                push!(edges, Dict{String,Any}(
                    "source" => left["class_id"],
                    "target" => right["class_id"],
                    "reason" => "one_probe_refinement_difference:$(differing[1])",
                ))
            end
        end
    end
    Dict{String,Any}(
        "rule" => "coordinate-free finite compatibility adjacency: one finite probe refinement differs; no metric, time, or global coordinates",
        "edge_count" => length(edges),
        "edges" => edges,
    )
end

function admissible_under(row::Dict{String,Any}, erase::Union{String,Nothing} = nothing)
    checks = Dict{String,Any}(row["constraint_checks"])
    erase !== nothing && (checks[erase] = true)
    all(Bool(v) for v in values(checks))
end

function na_basin_report()
    rows = Dict{String,Any}(
        "R" => Dict("finite" => true, "order_sensitive" => false, "assoc" => true, "na_allowed" => false, "norm_ok" => true),
        "C" => Dict("finite" => true, "order_sensitive" => false, "assoc" => true, "na_allowed" => false, "norm_ok" => true),
        "H" => Dict("finite" => true, "order_sensitive" => true, "assoc" => true, "na_allowed" => false, "norm_ok" => true),
        "M2C" => Dict("finite" => true, "order_sensitive" => true, "assoc" => true, "na_allowed" => false, "norm_ok" => true),
        "O" => Dict("finite" => true, "order_sensitive" => true, "assoc" => false, "na_allowed" => true, "norm_ok" => true),
        "J3O" => Dict("finite" => true, "order_sensitive" => true, "assoc" => false, "na_allowed" => true, "norm_ok" => true),
        "S" => Dict("finite" => true, "order_sensitive" => true, "assoc" => false, "na_allowed" => true, "norm_ok" => false),
    )

    function basin(allow_na::Bool)
        out = String[]
        for name in ["R", "C", "H", "M2C", "O", "J3O", "S"]
            row = rows[name]
            survives = row["finite"] && row["order_sensitive"] && row["norm_ok"] &&
                (row["assoc"] || (allow_na && row["na_allowed"]))
            survives && push!(out, name)
        end
        out
    end

    base = basin(false)
    with_na = basin(true)
    Dict{String,Any}(
        "status" => "candidate_third_constraint_fenced",
        "basis" => "finite predicate table mirroring documented B2/B3 repaired basin readout; no M(C+NA) admission",
        "basin_F01_N01" => base,
        "basin_F01_N01_NA" => with_na,
        "NA_changes_basin" => base != with_na,
        "sedenion_excluded_by_norm_not_associativity" => !("S" in with_na) && rows["S"]["na_allowed"] && !rows["S"]["norm_ok"],
        "predicate_rows" => rows,
        "claim_ceiling" => "candidate third constraint only; promotion_allowed=false and formal_admission_allowed=false",
    )
end

function geometry_erased_control(candidates::Vector{Dict{String,Any}}, admissible_ids::Vector{String})
    erased_admissible = [
        String(row["id"]) for row in candidates
        if row["finite_encoding"] && row["constraint_checks"]["admissible_composition_rules"]
    ]
    Dict{String,Any}(
        "rule" => "erase psi/rho/Hopf carrier data and keep only finite labels plus composition flag",
        "erased_admissible_ids" => erased_admissible,
        "actual_admissible_ids" => admissible_ids,
        "reproduces_admissibility_readout" => erased_admissible == admissible_ids,
        "pass" => erased_admissible != admissible_ids,
    )
end

function parity_against_peer(result::Dict{String,Any})
    if !isfile(JAX_REFERENCE_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_REFERENCE_PATH,
            "status" => "missing_jax_reference",
            "parity_max_diff" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [Dict{String,Any}("missing" => JAX_REFERENCE_PATH)],
            "boolean_mismatches" => [],
            "missing_keys" => [],
            "stop_condition_fired" => true,
        )
    end
    peer = JSON.parsefile(JAX_REFERENCE_PATH)
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
        diff = abs(Float64(value) - Float64(peer["shared_scalars"][key]))
        row = Dict{String,Any}("key" => key, "julia" => Float64(value), "jax" => Float64(peer["shared_scalars"][key]), "abs_diff" => diff)
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
        "peer_result_path" => JAX_REFERENCE_PATH,
        "status" => "compared",
        "shared_scalar_rows" => rows,
        "max_diff_key" => max_key,
        "parity_max_diff" => max_diff,
        "within_1e_9" => max_diff < TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function build_packet()
    all_candidates = [analyze_candidate(spec) for spec in candidate_specs()]
    admissible = [row for row in all_candidates if row["Adm_C"]]
    admissible_ids = [String(row["id"]) for row in admissible]
    active_probe_family = ["sheet", "eta_index", "rho_bloch", "order_word", "order_gap_bin", "order_orientation_sign"]
    quotient_active = quotient(admissible, active_probe_family)
    quotient_drop_sheet = quotient(admissible, [name for name in active_probe_family if name != "sheet"])
    quotient_drop_order = quotient(admissible, [name for name in active_probe_family if name != "order_orientation_sign"])

    f01_erased = [String(row["id"]) for row in all_candidates if admissible_under(row, "F01_FINITUDE")]
    n01_erased = [String(row["id"]) for row in all_candidates if admissible_under(row, "N01_NONCOMMUTATION")]
    geom_control = geometry_erased_control(all_candidates, admissible_ids)
    na_report = na_basin_report()

    adm_c_nontrivial = length(quotient_active["classes"]) < length(admissible) && length(admissible) < length(all_candidates)
    f01_load_bearing = f01_erased != admissible_ids
    n01_load_bearing = n01_erased != admissible_ids
    probe_load_bearing = quotient_drop_sheet["class_count"] != quotient_active["class_count"]
    owner_carrier_load_bearing = Bool(geom_control["pass"])

    class_by_member = Dict{String,String}()
    for cls in quotient_active["classes"]
        for member in cls["members"]
            class_by_member[String(member)] = String(cls["class_id"])
        end
    end
    adj = adjacency(quotient_active["classes"])
    degree_by_class = Dict{String,Int}()
    for cls in quotient_active["classes"]
        degree_by_class[String(cls["class_id"])] = 0
    end
    for edge in adj["edges"]
        degree_by_class[String(edge["source"])] += 1
        degree_by_class[String(edge["target"])] += 1
    end
    axes = Dict{String,Any}()
    for row in admissible
        class_id = class_by_member[String(row["id"])]
        rz = Float64(row["bloch"][3])
        cls_members = String[]
        for cls in quotient_active["classes"]
            if cls["class_id"] == class_id
                cls_members = cls["members"]
            end
        end
        axes[String(row["id"])] = Dict{String,Any}(
            "quotient_class" => class_id,
            "A0_finite_density_z_sign" => rz > TOL ? "positive" : (rz < -TOL ? "negative" : "zero"),
            "A1_sheet" => row["sheet"],
            "A2_eta_bin" => row["eta_index"],
            "A3_order_word" => row["order_word"],
            "A4_probe_equivalence_class_size" => length(cls_members),
            "A5_adjacency_degree" => degree_by_class[class_id],
            "A6_order_orientation_sign" => row["finite_probe_outputs"]["order_orientation_sign"],
        )
    end

    shared_scalars = Dict{String,Any}(
        "S_size" => Float64(length(all_candidates)),
        "admissible_count" => Float64(length(admissible)),
        "excluded_count" => Float64(length(all_candidates) - length(admissible)),
        "quotient_class_count" => Float64(quotient_active["class_count"]),
        "quotient_drop_sheet_class_count" => Float64(quotient_drop_sheet["class_count"]),
        "quotient_drop_order_orientation_class_count" => Float64(quotient_drop_order["class_count"]),
        "f01_erased_admissible_count" => Float64(length(f01_erased)),
        "n01_erased_admissible_count" => Float64(length(n01_erased)),
        "adjacency_edge_count" => Float64(adj["edge_count"]),
        "na_base_basin_count" => Float64(length(na_report["basin_F01_N01"])),
        "na_extended_basin_count" => Float64(length(na_report["basin_F01_N01_NA"])),
    )
    for row in all_candidates
        prefix = "candidate.$(row["id"])"
        shared_scalars["$prefix.spinor_norm"] = Float64(row["checks"]["spinor_norm"])
        shared_scalars["$prefix.trace_rho"] = Float64(row["checks"]["trace_rho"])
        shared_scalars["$prefix.order_gap"] = Float64(row["checks"]["order_gap"])
        shared_scalars["$prefix.projected_norm_residual"] = Float64(row["checks"]["projected_norm_residual"])
    end

    shared_booleans = Dict{String,Any}(
        "all_13_elements_present" => true,
        "adm_c_nontrivial" => adm_c_nontrivial,
        "F01_load_bearing" => f01_load_bearing,
        "N01_load_bearing" => n01_load_bearing,
        "probe_load_bearing" => probe_load_bearing,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "geometry_erased_control_pass" => Bool(geom_control["pass"]),
        "NA_changes_basin" => Bool(na_report["NA_changes_basin"]),
        "sedenion_excluded_by_norm_not_associativity" => Bool(na_report["sedenion_excluded_by_norm_not_associativity"]),
    )
    for row in all_candidates
        shared_booleans["candidate.$(row["id"]).Adm_C"] = Bool(row["Adm_C"])
        for (key, value) in row["constraint_checks"]
            shared_booleans["candidate.$(row["id"]).$key"] = Bool(value)
        end
    end

    elements_13 = Dict{String,Any}(
        "1_finite_carrier_S" => Dict{String,Any}(
            "description" => "finite support set of concrete owner-carrier records plus explicit graveyard controls",
            "size" => length(all_candidates),
            "candidate_ids" => [row["id"] for row in all_candidates],
        ),
        "2_active_constraint_set_C" => Dict{String,Any}(
            "C" => ["F01_FINITUDE", "N01_NONCOMMUTATION", "admissible_probe_rules", "admissible_composition_rules"],
        ),
        "3_admissibility_predicate_Adm_C" => Dict{String,Any}(
            "computed" => true,
            "admissible_ids" => admissible_ids,
            "excluded" => Dict{String,Any}(String(row["id"]) => row["fail_reasons"] for row in all_candidates if !row["Adm_C"]),
        ),
        "4_finite_probe_family_M" => Dict{String,Any}("probe_names" => active_probe_family),
        "5_quotient_S_mod_M" => quotient_active,
        "6_order_sensitive_composition_N01" => Dict{String,Any}(
            "operator_algebra" => "Pauli X/Y noncommuting order on finite spinor carrier",
            "commutative_control" => "commutative_XX_control",
        ),
        "7_neighborhood_adjacency" => adj,
        "8_candidate_carrier_geometry_and_iota" => Dict{String,Any}(
            "status" => "candidate realization mapped into M(C), not equal to M(C)",
            "carrier" => "finite samples from S_s^3 sheets with density rho=psi psi^dagger and Hopf torus eta bins",
            "iota" => Dict{String,Any}(String(row["id"]) => class_by_member[String(row["id"])] for row in admissible),
        ),
        "9_readout_map" => Dict{String,Any}(
            "preserves" => ["sheet", "eta_index", "density/Bloch finite bin", "order word", "order orientation"],
            "loses" => ["global spinor phase under density quotient; L_core_XY and L_core_XY_phase_pi are probe-equivalent"],
        ),
        "10_axes_A_i" => axes,
        "11_negative_controls_graveyards" => Dict{String,Any}(
            "F01_erased" => f01_erased,
            "N01_erased" => n01_erased,
            "probe_drop_sheet" => quotient_drop_sheet,
            "geometry_erased_control" => geom_control,
            "commutative_control" => "commutative_XX_control excluded by N01",
            "composition_control" => "composition_projection_missing_control excluded by composition rule",
        ),
        "12_evidence_handles" => Dict{String,Any}(
            "source_docs" => [
                "READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/TERRAIN_MATH_LEDGER_v1.md:23-47,265",
                "system_v4/docs/ROOT_CONSTRAINT_EXTENDED_FOUNDATIONS.md:92-124,348-383",
                "READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/constraint ladder/Constraints.md:114-130",
                "system_v5/docs/session_20260606_physics_excavation/05_NONASSOCIATIVITY_BRANCHES.md:3,21-37,108-127,178-190",
                "user-provided doc-grounded M(C) spec for missing constraint-manifold-architecture.md clauses",
            ],
            "julia_source" => @__FILE__,
            "julia_result" => RESULT_PATH,
            "jax_result" => JAX_REFERENCE_PATH,
        ),
        "13_claim_ceiling" => CLAIM_CEILING,
    )

    all_13_elements_present = length(elements_13) == 13 && all(!isempty(string(v)) for v in values(elements_13))
    shared_booleans["all_13_elements_present"] = all_13_elements_present

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => CLAIM_CEILING,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "constraint_admissibility_packet",
        "root_constraints_in_force" => ["F01_FINITUDE", "N01_NONCOMMUTATION"],
        "carrier_layer" => "finite owner-carrier samples from S_s^3 sheets with density lift",
        "geometry_layer" => "candidate realization mapped into M(C); coordinate-free adjacency is probe-compatibility only",
        "bridge_layer" => "none",
        "cut_layer" => "none",
        "allowed_claims" => [CLAIM_CEILING],
        "promotion_blockers" => [
            "scratch_diagnostic classification",
            "promotion_allowed=false",
            "formal_admission_allowed=false",
            "finite packet only; no final M(C), Axis0, QIT-engine, bridge, or physics admission",
        ],
        "required_tools" => ["Julia", "LinearAlgebra"],
        "actual_tools_used" => ["Julia", "LinearAlgebra", "JSON"],
        "proof_surfaces_used" => [],
        "graph_surfaces_used" => [],
        "topology_surfaces_used" => [],
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "required_negatives" => [
            "F01 erased",
            "N01 erased",
            "probe dropped",
            "geometry erased",
            "commutative control",
            "composition projection missing",
            "NA candidate basin compare",
        ],
        "negatives_run" => true,
        "kill_conditions" => [
            "Adm_C trivial",
            "F01 or N01 erasure leaves admissible set unchanged",
            "dropping a load-bearing probe leaves quotient unchanged",
            "geometry-erased control reproduces admissibility readout",
            "JAX/Julia parity exceeds 1e-9",
        ],
        "elements_13" => elements_13,
        "finite_carrier_rows" => all_candidates,
        "M_C" => Dict{String,Any}(
            "definition" => "M(C) = {x : x is admissible under C}",
            "admissible_ids" => admissible_ids,
            "quotient" => quotient_active,
        ),
        "controls" => Dict{String,Any}(
            "F01_erased_admissible_ids" => f01_erased,
            "N01_erased_admissible_ids" => n01_erased,
            "probe_drop_sheet" => quotient_drop_sheet,
            "probe_drop_order_orientation" => quotient_drop_order,
            "geometry_erased" => geom_control,
        ),
        "nonassociativity_candidate" => na_report,
        "positive" => Dict{String,Any}(
            "all_13_elements_present" => Dict("pass" => all_13_elements_present),
            "Adm_C_nontrivial" => Dict("pass" => adm_c_nontrivial),
            "owner_carrier_load_bearing" => Dict("pass" => owner_carrier_load_bearing),
        ),
        "graveyard_companions" => Dict{String,Any}(
            "F01_erasure_changes_admissible_set" => Dict("pass" => f01_load_bearing, "erased_ids" => f01_erased),
            "N01_erasure_changes_admissible_set" => Dict("pass" => n01_load_bearing, "erased_ids" => n01_erased),
            "probe_drop_changes_quotient" => Dict("pass" => probe_load_bearing),
            "geometry_erased_does_not_reproduce" => Dict("pass" => Bool(geom_control["pass"])),
        ),
        "boundary" => Dict{String,Any}(
            "classification_is_scratch_diagnostic" => CLASSIFICATION == "scratch_diagnostic",
            "promotion_allowed_false" => true,
            "formal_admission_allowed_false" => true,
            "NA_changes_basin" => Bool(na_report["NA_changes_basin"]),
        ),
        "nearby_variants" => Dict{String,Any}(
            "total" => 4,
            "passed" => Int(f01_load_bearing) + Int(n01_load_bearing) + Int(probe_load_bearing) + Int(owner_carrier_load_bearing),
            "variants" => ["F01_erased", "N01_erased", "probe_drop_sheet", "geometry_erased"],
        ),
        "why_not_v4_probes" => "This is a v5 scratch diagnostic finite M(C) packet with dual-backend parity; it intentionally does not use v4 promotion language.",
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
    )
    result["parity"] = parity_against_peer(result)
    result["all_13_elements_present"] = all_13_elements_present
    result["adm_c_nontrivial"] = adm_c_nontrivial
    result["F01_load_bearing"] = f01_load_bearing
    result["N01_load_bearing"] = n01_load_bearing
    result["probe_load_bearing"] = probe_load_bearing
    result["owner_carrier_load_bearing"] = owner_carrier_load_bearing
    result["NA_changes_basin"] = Bool(na_report["NA_changes_basin"])
    result["all_pass"] = all_13_elements_present &&
        adm_c_nontrivial &&
        f01_load_bearing &&
        n01_load_bearing &&
        probe_load_bearing &&
        owner_carrier_load_bearing &&
        Bool(na_report["NA_changes_basin"]) &&
        Bool(result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = !Bool(result["all_pass"])
    result
end

function print_summary(result::Dict{String,Any})
    println("mc_first_admissibility_packet - Julia")
    println(
        "all_pass=", result["all_pass"],
        " all_13=", result["all_13_elements_present"],
        " adm_c_nontrivial=", result["adm_c_nontrivial"],
        " F01_load_bearing=", result["F01_load_bearing"],
        " N01_load_bearing=", result["N01_load_bearing"],
        " probe_load_bearing=", result["probe_load_bearing"],
        " owner_carrier_load_bearing=", result["owner_carrier_load_bearing"],
        " NA_changes_basin=", result["NA_changes_basin"],
    )
    println(
        "parity_status=", result["parity"]["status"],
        " parity_max_diff=", result["parity"]["parity_max_diff"],
        " within_1e-9=", result["parity"]["within_1e_9"],
    )
    println("wrote: ", result["result_path"])
end

result = build_packet()
open(RESULT_PATH, "w") do io
    JSON.print(io, result, 2)
    write(io, "\n")
end
print_summary(result)

if !Bool(result["all_pass"])
    exit(2)
end
