#!/usr/bin/env julia
# object_id: foundation_mc_v1_admissibility_object_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: false

import Dates
import JSON
import SHA
import LinearAlgebra
import QuantumOptics
import CliffordAlgebras

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RUNG_ID = "foundation_mc_v1_admissibility_object"
const OBJECT_ID = "foundation_mc_v1_admissibility_object_julia"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_mc_v1_admissibility_object_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_mc_v1_admissibility_object_julia_results.json")
const ARTIFACT_PATH = joinpath(ROOT, "system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json")
const ARTIFACT_RECEIPT_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json")
const TOL = 1.0e-10

const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false
const reads_peer_result = false

const TOOL_MANIFEST = Dict{String,Any}(
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite 2D Hilbert-space density operators, projectors, and Born readouts for density/probe constraints"),
    "CliffordAlgebras" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Cl(6) carrier-surface construction and dimension/even-subalgebra readout"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive canon artifact and receipt serialization"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source and artifact fingerprinting"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive eigenvalue and norm checks for finite matrices/vectors"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "QuantumOptics" => "load_bearing",
    "CliffordAlgebras" => "load_bearing",
    "JSON" => "supportive",
    "SHA" => "supportive",
    "LinearAlgebra" => "supportive",
)

function sha256_file(path::String)
    isfile(path) || return nothing
    open(path, "r") do io
        return bytes2hex(SHA.sha256(io))
    end
end

function load_octonion_table()
    artifact = JSON.parsefile(ARTIFACT_PATH)
    receipt = JSON.parsefile(ARTIFACT_RECEIPT_PATH)
    oct = first(row for row in artifact["algebras"] if row["algebra"] == "octonion")
    dim = Int(oct["dim"])
    table = zeros(Int, dim, dim, dim)
    for k in 1:dim, i in 1:dim, j in 1:dim
        table[k, i, j] = Int(oct["C"][k][i][j])
    end
    artifact, receipt, table
end

function qop(basis, rows)
    QuantumOptics.DenseOperator(basis, ComplexF64[rows[1][1] rows[1][2]; rows[2][1] rows[2][2]])
end

function rho_rows(key::String)
    rows = Dict(
        "rho_z0" => [[1.0, 0.0], [0.0, 0.0]],
        "rho_z1" => [[0.0, 0.0], [0.0, 1.0]],
        "rho_xplus" => [[0.5, 0.5], [0.5, 0.5]],
        "rho_bad_trace" => [[0.6, 0.0], [0.0, 0.6]],
        "rho_bad_psd" => [[0.5, 0.6], [0.6, 0.5]],
    )
    rows[key]
end

function probes(basis)
    Dict(
        "P_z0" => qop(basis, [[1.0, 0.0], [0.0, 0.0]]),
        "P_z1" => qop(basis, [[0.0, 0.0], [0.0, 1.0]]),
        "P_xplus" => qop(basis, [[0.5, 0.5], [0.5, 0.5]]),
    )
end

function basis_vec(dim::Int, idx0::Int)
    v = zeros(Int, dim)
    v[idx0 + 1] = 1
    v
end

function multiply(table::Array{Int,3}, x::Vector{Int}, y::Vector{Int})
    dim = size(table, 1)
    out = zeros(Int, dim)
    for k in 1:dim, i in 1:dim, j in 1:dim
        out[k] += table[k, i, j] * x[i] * y[j]
    end
    out
end

function bracket_readouts(table::Array{Int,3}, triple::Vector{Int})
    x, y, z = [basis_vec(size(table, 1), idx) for idx in triple]
    left = multiply(table, multiply(table, x, y), z)
    right = multiply(table, x, multiply(table, y, z))
    assoc = left - right
    Dict{String,Any}(
        "left" => collect(left),
        "right" => collect(right),
        "associator" => collect(assoc),
        "associator_norm" => round(LinearAlgebra.norm(Float64.(assoc)); digits=12),
        "nonzero_components" => count(!=(0), assoc),
    )
end

function find_nonassoc_triple(table::Array{Int,3})
    dim = size(table, 1)
    for a in 1:(dim - 1), b in 1:(dim - 1), c in 1:(dim - 1)
        br = bracket_readouts(table, [a, b, c])
        br["associator_norm"] > TOL && return [a, b, c]
    end
    error("no nonassociative octonion triple found")
end

function support_spec(nonassoc_triple, assoc_triple)
    [
        Dict("id" => "s_z0_oct_left", "rho" => "rho_z0", "triple" => nonassoc_triple, "bracket" => "left", "support_index" => 0, "bounded_witness" => true, "composition" => ["Z", "X"]),
        Dict("id" => "s_z0_oct_right", "rho" => "rho_z0", "triple" => nonassoc_triple, "bracket" => "right", "support_index" => 1, "bounded_witness" => true, "composition" => ["Z", "X"]),
        Dict("id" => "s_z1_oct_left", "rho" => "rho_z1", "triple" => nonassoc_triple, "bracket" => "left", "support_index" => 2, "bounded_witness" => true, "composition" => ["Z", "X"]),
        Dict("id" => "s_xplus_oct_left", "rho" => "rho_xplus", "triple" => nonassoc_triple, "bracket" => "left", "support_index" => 3, "bounded_witness" => true, "composition" => ["Z", "X"]),
        Dict("id" => "s_bad_trace_oct_left", "rho" => "rho_bad_trace", "triple" => nonassoc_triple, "bracket" => "left", "support_index" => 4, "bounded_witness" => true, "composition" => ["Z", "X"]),
        Dict("id" => "s_bad_psd_oct_left", "rho" => "rho_bad_psd", "triple" => nonassoc_triple, "bracket" => "left", "support_index" => 5, "bounded_witness" => true, "composition" => ["Z", "X"]),
        Dict("id" => "s_bad_f01_unbounded_witness", "rho" => "rho_z0", "triple" => nonassoc_triple, "bracket" => "left", "support_index" => 99, "bounded_witness" => false, "composition" => ["Z", "X"]),
        Dict("id" => "s_commuting_control", "rho" => "rho_z0", "triple" => nonassoc_triple, "bracket" => "left", "support_index" => 7, "bounded_witness" => true, "composition" => ["Z", "Z"]),
        Dict("id" => "s_associative_bracket_control", "rho" => "rho_z0", "triple" => assoc_triple, "bracket" => "left", "support_index" => 8, "bounded_witness" => true, "composition" => ["Z", "X"]),
    ]
end

function trace_real(op)
    real(QuantumOptics.tr(op))
end

function measurement_stats(rho, probe_map)
    Dict(name => round(trace_real(probe * rho); digits=12) for (name, probe) in probe_map)
end

function seq_prob(rho, first, second)
    round(trace_real(second * first * rho * first); digits=12)
end

function order_report(rho, probe_map, composition)
    first = composition[1] == "Z" ? probe_map["P_z0"] : probe_map["P_xplus"]
    second = composition[2] == "Z" ? probe_map["P_z0"] : probe_map["P_xplus"]
    forward = seq_prob(rho, first, second)
    reverse = seq_prob(rho, second, first)
    Dict{String,Any}(
        "composition" => composition,
        "forward_probability" => forward,
        "reverse_probability" => reverse,
        "order_gap" => round(abs(forward - reverse); digits=12),
        "AB_not_BA_witness" => abs(forward - reverse) > TOL,
    )
end

function density_checks(rho, stats)
    data = QuantumOptics.dense(rho).data
    trace_value = real(LinearAlgebra.tr(data))
    hermitian_residual = LinearAlgebra.norm(data - data')
    evals = LinearAlgebra.eigvals(LinearAlgebra.Hermitian(data))
    min_eval = minimum(real.(evals))
    Dict{String,Any}(
        "trace" => round(trace_value; digits=12),
        "trace_eq_1" => abs(trace_value - 1.0) <= TOL,
        "hermitian_residual" => round(hermitian_residual; digits=12),
        "hermitian" => hermitian_residual <= TOL,
        "psd_min_eigenvalue" => round(min_eval; digits=12),
        "psd" => min_eval >= -TOL,
        "probe_bounds" => all(value -> -TOL <= value <= 1.0 + TOL, values(stats)),
    )
end

function entropy_from_z(stats)
    out = 0.0
    for p in [stats["P_z0"], stats["P_z1"]]
        p > TOL && (out -= p * log2(p))
    end
    round(out; digits=12)
end

function cl6_surface()
    cl6 = CliffordAlgebras.CliffordAlgebra(6, 0)
    dim = length(propertynames(cl6))
    even_dim = count(mask -> iseven(count_ones(UInt(mask))), 0:(2^6 - 1))
    Dict{String,Any}(
        "target" => "Cl(6)",
        "dimension" => dim,
        "expected_dimension" => 64,
        "even_subalgebra_dimension" => even_dim,
        "expected_even_subalgebra_dimension" => 32,
        "constructed_with" => "CliffordAlgebras.CliffordAlgebra(6,0)",
        "dimension_pass" => dim == 64 && even_dim == 32,
    )
end

function record_for(spec, table, basis, probe_map, support_size, cl6)
    rho = qop(basis, rho_rows(spec["rho"]))
    stats = measurement_stats(rho, probe_map)
    density = density_checks(rho, stats)
    order = order_report(rho, probe_map, spec["composition"])
    bracket = bracket_readouts(table, Vector{Int}(spec["triple"]))
    f01_ok = Bool(spec["bounded_witness"]) && 0 <= Int(spec["support_index"]) < support_size
    n01_ok = Bool(order["AB_not_BA_witness"])
    bracketing_ok = bracket["associator_norm"] > TOL
    carrier_ok = bracketing_ok && bracket["nonzero_components"] > 0 && Bool(cl6["dimension_pass"])
    admitted = density["trace_eq_1"] && density["hermitian"] && density["psd"] && density["probe_bounds"] && f01_ok && n01_ok && bracketing_ok && carrier_ok
    selected = bracket[spec["bracket"]]
    full_key = Dict{String,Any}(
        "density" => stats,
        "f01" => Dict("bounded_witness" => f01_ok, "support_index" => Int(spec["support_index"])),
        "n01" => Dict("composition" => spec["composition"], "order_gap" => order["order_gap"]),
        "bracketing" => Dict("label" => spec["bracket"], "readout" => selected, "associator_norm" => bracket["associator_norm"]),
        "carrier" => Dict("octonion_nonzero_components" => bracket["nonzero_components"], "cl6_dim" => cl6["dimension"]),
        "axes" => Dict("A_entropy_bits" => entropy_from_z(stats), "A_order_gap" => order["order_gap"], "A_associator_norm" => bracket["associator_norm"]),
    )
    flags = Dict(
        "density_probe_C" => density["trace_eq_1"] && density["hermitian"] && density["psd"] && density["probe_bounds"],
        "F01" => f01_ok,
        "N01" => n01_ok,
        "bracketing" => bracketing_ok,
        "carrier" => carrier_ok,
    )
    reasons = String[]
    for (name, ok) in [
        ("trace=1", density["trace_eq_1"]),
        ("Hermitian", density["hermitian"]),
        ("PSD", density["psd"]),
        ("probe_bounds", density["probe_bounds"]),
        ("F01", f01_ok),
        ("N01", n01_ok),
        ("bracketing_nonassociative", bracketing_ok),
        ("carrier_readout", carrier_ok),
    ]
        ok || push!(reasons, name)
    end
    Dict{String,Any}(
        "id" => spec["id"],
        "rho_key" => spec["rho"],
        "support_index" => spec["support_index"],
        "bounded_witness" => spec["bounded_witness"],
        "triple" => spec["triple"],
        "bracketing" => spec["bracket"],
        "density" => density,
        "probe_values" => stats,
        "composition" => order,
        "bracketing_readout" => bracket,
        "carrier_readout" => Dict("selected" => selected, "octonion" => bracket, "cl6_surface" => cl6),
        "constraint_flags" => flags,
        "admitted_under_Adm_C" => admitted,
        "rejection_reasons" => reasons,
        "full_probe_key" => full_key,
    )
end

function key_for(row, key_mode::String)
    key = deepcopy(row["full_probe_key"])
    if key_mode == "drop_bracketing"
        delete!(key, "bracketing")
        delete!(key, "carrier")
    elseif key_mode == "label_shuffle"
        dens = key["density"]
        key["density"] = Dict("P_z1" => dens["P_z0"], "P_z0" => dens["P_z1"], "P_xplus" => dens["P_xplus"])
    elseif key_mode == "carrier_erasure"
        key["bracketing"] = Dict("label" => "erased", "readout" => fill(0, 8), "associator_norm" => 0.0)
        key["carrier"] = Dict("octonion_nonzero_components" => 0, "cl6_dim" => 0)
    end
    key
end

function quotient(records, admitted_only::Bool; key_mode::String = "full")
    selected = [row for row in records if !admitted_only || row["admitted_under_Adm_C"]]
    classes = Dict{String,Dict{String,Any}}()
    for row in selected
        key = key_for(row, key_mode)
        key_s = JSON.json(key)
        if !haskey(classes, key_s)
            classes[key_s] = Dict("members" => String[], "key" => key)
        end
        push!(classes[key_s]["members"], row["id"])
    end
    ordered = Vector{Dict{String,Any}}()
    for (idx, key_s) in enumerate(sort(collect(keys(classes))))
        value = classes[key_s]
        push!(ordered, Dict("class_id" => "$(admitted_only ? "Adm" : "S")_q$(idx - 1)", "members" => sort(value["members"]), "key" => value["key"]))
    end
    signature = bytes2hex(SHA.sha256(JSON.json(ordered)))
    Dict{String,Any}(
        "admitted_only" => admitted_only,
        "key_mode" => key_mode,
        "class_count" => length(ordered),
        "classes" => ordered,
        "partition_member_ids" => sort(vcat([cls["members"] for cls in ordered]...)),
        "signature_sha256" => signature,
    )
end

function apply_control(records, control::String)
    mutated = deepcopy(records)
    key_mode = "full"
    for row in mutated
        flags = row["constraint_flags"]
        if control == "drop_F01"
            flags["F01"] = true
        elseif control == "drop_N01"
            flags["N01"] = true
        elseif control == "drop_bracketing"
            flags["bracketing"] = true
            key_mode = "drop_bracketing"
        elseif control == "label_shuffle"
            key_mode = "label_shuffle"
        elseif control == "carrier_erasure"
            flags["carrier"] = false
            key_mode = "carrier_erasure"
        elseif control == "commuting"
            flags["N01"] = false
            row["full_probe_key"]["n01"] = Dict("composition" => ["Z", "Z"], "order_gap" => 0.0)
        elseif control == "associative"
            flags["bracketing"] = false
            row["full_probe_key"]["bracketing"]["readout"] = fill(0, 8)
            row["full_probe_key"]["bracketing"]["associator_norm"] = 0.0
        else
            error("unknown control $control")
        end
        row["admitted_under_Adm_C"] = flags["density_probe_C"] && flags["F01"] && flags["N01"] && flags["bracketing"] && flags["carrier"]
    end
    mutated, key_mode
end

function control_report(records, q_adm)
    baseline = sort([row["id"] for row in records if row["admitted_under_Adm_C"]])
    out = Dict{String,Any}()
    for name in ["drop_F01", "drop_N01", "drop_bracketing", "label_shuffle", "carrier_erasure", "commuting", "associative"]
        mutated, key_mode = apply_control(records, name)
        q_mut = quotient(mutated, true; key_mode=key_mode)
        admitted = sort([row["id"] for row in mutated if row["admitted_under_Adm_C"]])
        out[name] = Dict{String,Any}(
            "admitted_before" => baseline,
            "admitted_after" => admitted,
            "admitted_changed" => admitted != baseline,
            "quotient_class_count_before" => q_adm["class_count"],
            "quotient_class_count_after" => q_mut["class_count"],
            "quotient_signature_before" => q_adm["signature_sha256"],
            "quotient_signature_after" => q_mut["signature_sha256"],
            "quotient_changed" => q_mut["signature_sha256"] != q_adm["signature_sha256"],
            "flips_value_coupled" => (admitted != baseline) || (q_mut["signature_sha256"] != q_adm["signature_sha256"]),
        )
    end
    out
end

function build_result()
    started = time()
    artifact, receipt, table = load_octonion_table()
    nonassoc_triple = find_nonassoc_triple(table)
    assoc_triple = [1, 2, 3]
    specs = support_spec(nonassoc_triple, assoc_triple)
    basis = QuantumOptics.SpinBasis(1 // 2)
    probe_map = probes(basis)
    cl6 = cl6_surface()
    records = [record_for(spec, table, basis, probe_map, length(specs), cl6) for spec in specs]
    q_s = quotient(records, false)
    q_adm = quotient(records, true)
    controls = control_report(records, q_adm)
    admitted = [row for row in records if row["admitted_under_Adm_C"]]
    axes_maps = Dict{String,Any}(
        "A_entropy_bits" => Dict(row["id"] => row["full_probe_key"]["axes"]["A_entropy_bits"] for row in admitted),
        "A_order_gap" => Dict(row["id"] => row["full_probe_key"]["axes"]["A_order_gap"] for row in admitted),
        "A_associator_norm" => Dict(row["id"] => row["full_probe_key"]["axes"]["A_associator_norm"] for row in admitted),
    )
    controls_ok = all(row -> row["flips_value_coupled"], values(controls))
    field_coverage = Dict(key => "present_in_object" for key in ["S", "C", "M/P", "~_M", "Adm_C", "composition", "bracketing", "local_path_rules", "carrier_readout_map", "axes_A_i", "controls", "receipts", "ceiling"])
    all_pass = artifact["proof_pass"] == true &&
               receipt["proof_pass"] == true &&
               cl6["dimension_pass"] == true &&
               length(admitted) == 4 &&
               q_adm["class_count"] == 4 &&
               controls_ok &&
               classification == "scratch_diagnostic" &&
               promotion_allowed == false &&
               formal_admission_allowed == false &&
               reads_peer_result == false
    Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "object_id" => OBJECT_ID,
        "rung_id" => RUNG_ID,
        "engine" => "julia",
        "backend" => "julia_strict_carrier_quantumoptics_cliffordalgebras",
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "reads_peer_result" => reads_peer_result,
        "ran" => true,
        "source_path" => SOURCE_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "generated_at" => Dates.format(Dates.now(Dates.UTC), Dates.DateFormat("yyyy-mm-ddTHH:MM:SSZ")),
        "active_project" => Base.active_project(),
        "julia_version" => string(VERSION),
        "canon_runtime" => Dict(
            "artifact_path" => ARTIFACT_PATH,
            "artifact_sha256" => sha256_file(ARTIFACT_PATH),
            "receipt_path" => ARTIFACT_RECEIPT_PATH,
            "receipt_artifact_sha256" => receipt["artifact_sha256"],
            "proof_tag" => artifact["proof_tag"],
            "proof_pass" => artifact["proof_pass"],
            "table_version" => artifact["table_version"],
            "bracket_convention" => "left",
        ),
        "field_coverage" => field_coverage,
        "M_C_v1" => Dict(
            "S" => Dict("size" => length(records), "elements" => records),
            "C" => Dict(
                "density_probe_constraints" => ["trace=1", "Hermitian", "PSD", "0<=Tr(P rho)<=1 for P in finite M_density"],
                "F01" => "bounded_witness=true and support_index in 0..|S|-1",
                "N01" => "Z_then_X and X_then_Z sequential local paths have an explicit unequal probability witness",
                "composition_rules" => ["sequential projective composition uses B*A*rho*A", "composition labels are local path labels inside S"],
                "bracketing_rules" => ["octonion readout keeps ((a*b)*c) and (a*(b*c)) distinct", "global reassociation is forbidden"],
                "carrier_rules" => ["consume canon algebra_structure_constants_v1 octonion C[k][i][j]", "construct Cl(6) surface with CliffordAlgebras"],
            ),
            "M_over_P" => Dict("P" => ["density", "composition", "bracketing", "carrier", "axes"], "full_probe_family" => ["P_z0", "P_z1", "P_xplus", "F01_support", "N01_order_gap", "octonion_left_right_readout", "Cl6_dim", "A_entropy_bits", "A_order_gap", "A_associator_norm"]),
            "quotient_S_mod_M" => q_s,
            "quotient_Adm_C_mod_M" => q_adm,
            "Adm_C_records" => [Dict("id" => row["id"], "admitted" => row["admitted_under_Adm_C"], "rejection_reasons" => row["rejection_reasons"]) for row in records],
            "composition" => Dict("local_paths" => ["Z_then_X", "X_then_Z", "Z_then_Z_control"]),
            "bracketing" => Dict("witness_triple" => nonassoc_triple, "associative_control_triple" => assoc_triple, "in_quotient" => true),
            "local_path_rules" => Dict("allowed_paths" => ["Z_then_X", "X_then_Z", "left_assoc", "right_assoc"], "forbidden" => ["implicit_reassociation", "carrier_erasure"]),
            "carrier_readout_map" => Dict(row["id"] => row["carrier_readout"] for row in admitted),
            "axes_A_i" => axes_maps,
            "controls" => controls,
            "receipts" => Dict("source_path" => SOURCE_PATH, "source_sha256" => sha256_file(SOURCE_PATH), "artifact_sha256" => sha256_file(ARTIFACT_PATH)),
            "ceiling" => Dict("classification" => classification, "promotion_allowed" => promotion_allowed, "formal_admission_allowed" => formal_admission_allowed),
        ),
        "negative_controls" => controls,
        "summary" => Dict(
            "support_size" => length(records),
            "admitted_count" => length(admitted),
            "quotient_S_class_count" => q_s["class_count"],
            "quotient_Adm_C_class_count" => q_adm["class_count"],
            "nonassoc_witness_triple" => nonassoc_triple,
            "controls_all_flip" => controls_ok,
            "cl6_dimension" => cl6["dimension"],
            "cl6_even_subalgebra_dimension" => cl6["even_subalgebra_dimension"],
            "all_pass" => all_pass,
        ),
        "all_pass" => all_pass,
        "packages_used" => ["QuantumOptics", "CliffordAlgebras", "JSON", "SHA", "LinearAlgebra"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "CliffordAlgebras"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "runtime_seconds" => round(time() - started; digits=6),
    )
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    s = result["summary"]
    println(
        "SCOUT_DONE all_pass=$(result["all_pass"]) " *
        "admitted=$(s["admitted_count"]) " *
        "adm_classes=$(s["quotient_Adm_C_class_count"]) " *
        "controls_flip=$(s["controls_all_flip"]) " *
        "cl6_dim=$(s["cl6_dimension"]) " *
        "reads_peer_result=$(result["reads_peer_result"])"
    )
    return result["all_pass"] ? 0 : 2
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end
