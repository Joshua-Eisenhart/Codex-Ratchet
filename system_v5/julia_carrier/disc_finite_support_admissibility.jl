#!/usr/bin/env julia
# object_id: disc_finite_support_admissibility
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "disc_finite_support_admissibility"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_CARRIER_PATH = joinpath(ROOT, "system_v5/julia_carrier/mc_first_admissibility_packet_julia_results.json")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/disc_finite_support_admissibility_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/disc_finite_support_admissibility_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const CLASSIFICATION = "scratch_diagnostic"
const CLAIM_CEILING = "finite-support/state-on-algebra base-layer discriminator only; promotion=false, formal_admission=false; no final M(C), manifold closure, Axis0, bridge, engine, or physics claim"

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing mirror recomputation of owner carrier density, F01, N01, quotient, controls, and parity scalars",
    ),
    "LinearAlgebra" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing state norms, traces, and finite Pauli order gaps",
    ),
    "JSON" => Dict{String,Any}(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization and peer-result parity loading",
    ),
    "numpy" => Dict{String,Any}(
        "tried" => false,
        "used" => false,
        "reason" => "not part of the Julia mirror; recorded false for the no-NumPy dual-backend boundary",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "JSON" => "supportive",
    "numpy" => nothing,
)

finite_round(value::Real, digits::Int = 12) = round(Float64(value); digits = digits)

function complex_from_pair(pair)
    ComplexF64(Float64(pair[1]), Float64(pair[2]))
end

function operators(order_word::String)
    order_word == "XY" && return SX, SY
    order_word == "YX" && return SY, SX
    order_word == "XX" && return SX, SX
    error("unknown order_word: $order_word")
end

function bloch_from_rho(rho::Matrix{ComplexF64})
    Float64[real(tr(rho * SX)), real(tr(rho * SY)), real(tr(rho * SZ))]
end

function load_owner_carrier()
    data = JSON.parsefile(SOURCE_CARRIER_PATH)
    rows = get(data, "finite_carrier_rows", [])
    isempty(rows) && error("missing finite_carrier_rows in $SOURCE_CARRIER_PATH")
    data
end

function recompute_row(row)
    psi = ComplexF64[complex_from_pair(pair) for pair in row["spinor_components"]]
    rho = psi * psi'
    bloch = bloch_from_rho(rho)
    a_op, b_op = operators(String(row["order_word"]))
    left = a_op * (b_op * psi)
    right = b_op * (a_op * psi)
    delta = left - right
    spinor_norm = real(dot(psi, psi))
    trace_rho = real(tr(rho))
    order_gap = norm(delta)
    order_orientation = imag(dot(psi, delta))
    all_finite = all(isfinite, real.(psi)) && all(isfinite, imag.(psi))
    bloch_tuple = [finite_round(bloch[1], 12), finite_round(bloch[2], 12), finite_round(bloch[3], 12)]
    probes = Dict{String,Any}(row["finite_probe_outputs"])
    order_sign = order_orientation > TOL ? 1 : (order_orientation < -TOL ? -1 : 0)
    computed_probe_outputs = Dict{String,Any}(
        "sheet" => String(row["sheet"]),
        "eta_index" => Int(row["eta_index"]),
        "rho_bloch" => bloch_tuple,
        "order_word" => String(row["order_word"]),
        "order_gap_bin" => order_gap > TOL ? 1 : 0,
        "order_orientation_sign" => order_sign,
        "composition_projected" => Bool(probes["composition_projected"]),
        "support_kind" => Bool(row["finite_encoding"]) ? "finite_support" : "continuous_or_nonfinite_proxy",
    )
    f01_pass = Bool(row["finite_encoding"]) && abs(spinor_norm - 1.0) <= TOL && abs(trace_rho - 1.0) <= TOL && all_finite
    n01_pass = order_gap > TOL
    probe_rules_pass = abs(spinor_norm - 1.0) <= TOL &&
        abs(trace_rho - 1.0) <= TOL &&
        all(v -> abs(v) <= 1.0 + TOL, bloch_tuple) &&
        computed_probe_outputs["sheet"] in ["L", "R"] &&
        computed_probe_outputs["eta_index"] in [1, 2] &&
        computed_probe_outputs["order_word"] in ["XY", "YX", "XX"]
    composition_rules_pass = Bool(probes["composition_projected"])
    adm_c = f01_pass && n01_pass && probe_rules_pass && composition_rules_pass
    fail_reasons = String[]
    !f01_pass && push!(fail_reasons, "F01_FINITUDE")
    !n01_pass && push!(fail_reasons, "N01_NONCOMMUTATION")
    !probe_rules_pass && push!(fail_reasons, "state_on_algebra_probe_rules")
    !composition_rules_pass && push!(fail_reasons, "composition_rules")
    Dict{String,Any}(
        "id" => String(row["id"]),
        "role" => String(row["role"]),
        "support_kind" => computed_probe_outputs["support_kind"],
        "finite_probe_outputs" => computed_probe_outputs,
        "checks" => Dict{String,Any}(
            "spinor_norm" => spinor_norm,
            "trace_rho" => trace_rho,
            "order_gap" => order_gap,
            "order_orientation" => order_orientation,
            "bloch" => bloch_tuple,
        ),
        "constraint_checks" => Dict{String,Any}(
            "F01_FINITUDE" => f01_pass,
            "N01_NONCOMMUTATION" => n01_pass,
            "state_on_algebra_probe_rules" => probe_rules_pass,
            "composition_rules" => composition_rules_pass,
        ),
        "Adm_C" => adm_c,
        "fail_reasons" => fail_reasons,
    )
end

function admissible_under(row, erase::Union{String,Nothing} = nothing)
    checks = Dict{String,Any}(row["constraint_checks"])
    erase == "F01" && (checks["F01_FINITUDE"] = true)
    erase == "N01" && (checks["N01_NONCOMMUTATION"] = true)
    all(Bool(v) for v in values(checks))
end

function signature_values(row, probe_names::Vector{String})
    probes = row["finite_probe_outputs"]
    Any[probes[name] for name in probe_names]
end

function quotient(rows::Vector{Dict{String,Any}}, probe_names::Vector{String})
    classes = Dict{String,Vector{String}}()
    signatures = Dict{String,Vector{Any}}()
    for row in rows
        values = signature_values(row, probe_names)
        key = JSON.json(values)
        if !haskey(classes, key)
            classes[key] = String[]
        end
        push!(classes[key], String(row["id"]))
        signatures[key] = values
    end
    ordered = Vector{Dict{String,Any}}()
    for (idx, key) in enumerate(sort(collect(keys(classes))))
        push!(ordered, Dict{String,Any}(
            "class_id" => "q$(idx - 1)",
            "members" => sort(classes[key]),
            "signature" => signatures[key],
        ))
    end
    assigned = sort([member for cls in ordered for member in cls["members"]])
    Dict{String,Any}(
        "probe_names" => probe_names,
        "class_count" => length(ordered),
        "classes" => ordered,
        "partition_member_ids" => assigned,
    )
end

function quotient_well_defined(rows::Vector{Dict{String,Any}}, q::Dict{String,Any})
    source_ids = sort([String(row["id"]) for row in rows])
    class_ids = [String(cls["class_id"]) for cls in q["classes"]]
    !isempty(rows) &&
        q["partition_member_ids"] == source_ids &&
        length(class_ids) == length(Set(class_ids)) &&
        q["class_count"] == length(q["classes"])
end

function layer_verdict(f01_changes::Bool, n01_changes::Bool, quotient_ok::Bool, trivial_collapses::Bool, owner_load_bearing::Bool)
    if f01_changes && n01_changes && quotient_ok && trivial_collapses && owner_load_bearing
        return "REAL_LAYER"
    end
    if !f01_changes && !n01_changes
        return "CONVENTION"
    end
    if quotient_ok && !trivial_collapses
        return "GENERIC"
    end
    if f01_changes || n01_changes || owner_load_bearing
        return "PARTIAL"
    end
    "OPEN"
end

function parity_against_peer(result::Dict{String,Any})
    if !isfile(JAX_REFERENCE_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_REFERENCE_PATH,
            "status" => "missing_jax_reference",
            "within_1e_9" => false,
            "parity_max_diff" => nothing,
            "strict_divergence_gt_1e_6" => [Dict{String,Any}("missing" => JAX_REFERENCE_PATH)],
            "boolean_mismatches" => [],
            "string_mismatches" => [],
            "missing_keys" => [],
            "stop_condition_fired" => true,
        )
    end
    peer = JSON.parsefile(JAX_REFERENCE_PATH)
    max_diff = 0.0
    max_key = nothing
    rows = Vector{Dict{String,Any}}()
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
    boolean_mismatches = Vector{Dict{String,Any}}()
    for (key, value) in result["shared_booleans"]
        if !haskey(peer["shared_booleans"], key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer["shared_booleans"][key])
            push!(boolean_mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => Bool(peer["shared_booleans"][key])))
        end
    end
    string_mismatches = Vector{Dict{String,Any}}()
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
        "shared_scalar_rows" => rows,
        "max_diff_key" => max_key,
        "parity_max_diff" => max_diff,
        "within_1e_9" => max_diff < TOL && isempty(strict) && isempty(boolean_mismatches) && isempty(string_mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => boolean_mismatches,
        "string_mismatches" => string_mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(boolean_mismatches) || !isempty(string_mismatches) || !isempty(missing),
    )
end

function build_result()
    carrier = load_owner_carrier()
    rows = [recompute_row(row) for row in carrier["finite_carrier_rows"]]
    admissible = [row for row in rows if row["Adm_C"]]
    admissible_ids = [String(row["id"]) for row in admissible]
    f01_erased_ids = [String(row["id"]) for row in rows if admissible_under(row, "F01")]
    n01_erased_ids = [String(row["id"]) for row in rows if admissible_under(row, "N01")]
    active_probe_family = ["sheet", "eta_index", "rho_bloch", "order_word", "order_gap_bin", "order_orientation_sign"]
    q_s = quotient(rows, active_probe_family)
    q_adm = quotient(admissible, active_probe_family)
    q_trivial = quotient(admissible, String[])
    q_layer_erased = quotient(admissible, ["support_kind"])
    q_ok = quotient_well_defined(rows, q_s) && quotient_well_defined(admissible, q_adm)
    adm_depends_on_finitude = f01_erased_ids != admissible_ids
    erase_finitude_changes_adm = adm_depends_on_finitude
    erase_n01_changes_adm = n01_erased_ids != admissible_ids
    trivial_probe_family_collapses = q_trivial["class_count"] == 1 && q_adm["class_count"] > 1
    owner_real_carrier_load_bearing = q_layer_erased["class_count"] != q_adm["class_count"]
    n01_load_bearing = erase_n01_changes_adm
    verdict = layer_verdict(
        adm_depends_on_finitude,
        n01_load_bearing,
        q_ok,
        trivial_probe_family_collapses,
        owner_real_carrier_load_bearing,
    )
    shared_scalars = Dict{String,Any}(
        "S_size" => Float64(length(rows)),
        "admissible_count" => Float64(length(admissible)),
        "f01_erased_admissible_count" => Float64(length(f01_erased_ids)),
        "n01_erased_admissible_count" => Float64(length(n01_erased_ids)),
        "S_quotient_class_count" => Float64(q_s["class_count"]),
        "Adm_quotient_class_count" => Float64(q_adm["class_count"]),
        "trivial_probe_class_count" => Float64(q_trivial["class_count"]),
        "layer_erased_quotient_class_count" => Float64(q_layer_erased["class_count"]),
    )
    for row in rows
        prefix = "candidate.$(row["id"])"
        shared_scalars["$prefix.spinor_norm"] = Float64(row["checks"]["spinor_norm"])
        shared_scalars["$prefix.trace_rho"] = Float64(row["checks"]["trace_rho"])
        shared_scalars["$prefix.order_gap"] = Float64(row["checks"]["order_gap"])
    end
    shared_booleans = Dict{String,Any}(
        "jax_enable_x64" => true,
        "source_carrier_all_pass" => Bool(carrier["all_pass"]),
        "quotient_well_defined" => q_ok,
        "adm_depends_on_finitude" => adm_depends_on_finitude,
        "erase_finitude_changes_adm" => erase_finitude_changes_adm,
        "erase_n01_changes_adm" => erase_n01_changes_adm,
        "n01_load_bearing" => n01_load_bearing,
        "trivial_probe_family_collapses" => trivial_probe_family_collapses,
        "owner_real_carrier_load_bearing" => owner_real_carrier_load_bearing,
        "classification_is_scratch_diagnostic" => CLASSIFICATION == "scratch_diagnostic",
        "promotion_false" => true,
        "formal_admission_false" => true,
    )
    for row in rows
        shared_booleans["candidate.$(row["id"]).Adm_C"] = Bool(row["Adm_C"])
        for (key, value) in row["constraint_checks"]
            shared_booleans["candidate.$(row["id"]).$key"] = Bool(value)
        end
    end
    shared_strings = Dict{String,Any}(
        "layer_verdict" => verdict,
        "admissible_ids" => join(admissible_ids, ","),
        "f01_erased_ids" => join(f01_erased_ids, ","),
        "n01_erased_ids" => join(n01_erased_ids, ","),
    )
    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "source_carrier_path" => SOURCE_CARRIER_PATH,
        "source_carrier_object_id" => carrier["object_id"],
        "classification" => CLASSIFICATION,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => CLAIM_CEILING,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "manifold_layer_discriminator",
        "root_constraints_in_force" => ["F01_FINITUDE", "N01_NONCOMMUTATION"],
        "carrier_layer" => "finite support / state-on-algebra base layer over owner mc_first_admissibility_packet rows",
        "geometry_layer" => "none; quotient is finite probe equivalence only",
        "bridge_layer" => "none",
        "cut_layer" => "none",
        "allowed_claims" => [CLAIM_CEILING],
        "promotion_blockers" => [
            "scratch_diagnostic classification",
            "promotion_allowed=false",
            "formal_admission_allowed=false",
            "single finite discriminator row only",
            "does not admit final M(C), a full manifold, a bridge, Axis0, engine, or physics claim",
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
        "S" => Dict{String,Any}(
            "definition" => "finite admissibility space loaded from the real mc_first_admissibility_packet owner carrier",
            "size" => length(rows),
            "candidate_ids" => [row["id"] for row in rows],
        ),
        "C" => Dict{String,Any}(
            "constraints" => ["F01_FINITUDE", "N01_NONCOMMUTATION", "state_on_algebra_probe_rules", "composition_rules"],
            "F01" => "finite support row, normalized finite state, finite result witness",
            "N01" => "nonzero order gap in the finite Pauli probe algebra",
            "probe_rules" => "state-on-algebra trace/positivity proxy via finite Bloch probes plus explicit sheet/eta/order labels",
            "composition_rules" => "owner carrier composition projection remains enabled",
        ),
        "Adm_C" => Dict{String,Any}(
            "predicate" => "F01 and N01 and state_on_algebra_probe_rules and composition_rules",
            "admissible_ids" => admissible_ids,
            "excluded" => Dict{String,Any}(String(row["id"]) => row["fail_reasons"] for row in rows if !Bool(row["Adm_C"])),
        ),
        "quotient_S_mod_M" => q_s,
        "quotient_Adm_mod_M" => q_adm,
        "controls" => Dict{String,Any}(
            "erase_F01_support_to_continuous" => Dict{String,Any}(
                "admissible_ids" => f01_erased_ids,
                "changes_admissible_set" => erase_finitude_changes_adm,
            ),
            "erase_N01_commutative_probe_algebra" => Dict{String,Any}(
                "admissible_ids" => n01_erased_ids,
                "changes_admissible_set" => erase_n01_changes_adm,
            ),
            "trivial_probe_family" => Dict{String,Any}(
                "quotient" => q_trivial,
                "collapses" => trivial_probe_family_collapses,
            ),
            "erase_owner_layer_structure" => Dict{String,Any}(
                "quotient" => q_layer_erased,
                "changes_result" => owner_real_carrier_load_bearing,
            ),
        ),
        "positive" => Dict{String,Any}(
            "adm_depends_on_finitude" => Dict("pass" => adm_depends_on_finitude),
            "n01_load_bearing" => Dict("pass" => n01_load_bearing),
            "quotient_well_defined" => Dict("pass" => q_ok),
            "owner_real_carrier_load_bearing" => Dict("pass" => owner_real_carrier_load_bearing),
        ),
        "graveyard_companions" => Dict{String,Any}(
            "continuous_support_proxy_admitted_only_when_F01_erased" => "nonfinite_global_coordinate_control" in f01_erased_ids,
            "commutative_control_admitted_only_when_N01_erased" => "commutative_XX_control" in n01_erased_ids,
            "trivial_probe_family_collapses_quotient" => trivial_probe_family_collapses,
        ),
        "boundary" => Dict{String,Any}(
            "classification_is_scratch_diagnostic" => CLASSIFICATION == "scratch_diagnostic",
            "promotion_allowed_false" => true,
            "formal_admission_allowed_false" => true,
            "claim_ceiling" => CLAIM_CEILING,
        ),
        "nearby_variants" => Dict{String,Any}(
            "total" => 4,
            "passed" => Int(adm_depends_on_finitude) + Int(n01_load_bearing) + Int(trivial_probe_family_collapses) + Int(owner_real_carrier_load_bearing),
            "variants" => ["F01_erased", "N01_erased", "trivial_probe_family", "owner_layer_structure_erased"],
        ),
        "why_not_v4_probes" => "v5 scratch diagnostic dual-backend discriminator row; no v4 promotion language is claimed.",
        "finite_carrier_rows" => rows,
        "layer_verdict" => verdict,
        "adm_depends_on_finitude" => adm_depends_on_finitude,
        "erase_finitude_changes_adm" => erase_finitude_changes_adm,
        "erase_n01_changes_adm" => erase_n01_changes_adm,
        "quotient_well_defined" => q_ok,
        "n01_load_bearing" => n01_load_bearing,
        "owner_real_carrier_load_bearing" => owner_real_carrier_load_bearing,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "shared_strings" => shared_strings,
    )
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = Bool(carrier["all_pass"]) &&
        q_ok &&
        adm_depends_on_finitude &&
        n01_load_bearing &&
        trivial_probe_family_collapses &&
        owner_real_carrier_load_bearing &&
        CLASSIFICATION == "scratch_diagnostic" &&
        Bool(result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = !Bool(result["all_pass"])
    result
end

function print_summary(result::Dict{String,Any})
    println("disc_finite_support_admissibility - Julia")
    println(
        "all_pass=", result["all_pass"],
        " layer_verdict=", result["layer_verdict"],
        " adm_depends_on_finitude=", result["adm_depends_on_finitude"],
        " erase_finitude_changes_adm=", result["erase_finitude_changes_adm"],
        " erase_n01_changes_adm=", result["erase_n01_changes_adm"],
        " quotient_well_defined=", result["quotient_well_defined"],
        " n01_load_bearing=", result["n01_load_bearing"],
        " owner_real_carrier_load_bearing=", result["owner_real_carrier_load_bearing"],
    )
    println(
        "parity_status=", result["parity"]["status"],
        " parity_max_diff=", result["parity"]["parity_max_diff"],
        " within_1e-9=", result["parity"]["within_1e_9"],
    )
    println("wrote: ", result["result_path"])
end

result = build_result()
open(RESULT_PATH, "w") do io
    JSON.print(io, result, 2)
    write(io, "\n")
end
print_summary(result)

if !Bool(result["all_pass"])
    exit(2)
end
