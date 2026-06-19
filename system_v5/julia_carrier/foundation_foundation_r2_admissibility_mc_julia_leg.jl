#!/usr/bin/env julia
# object_id: foundation_r2_admissibility_mc_julia_leg
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: false

using Dates
using JSON
using LinearAlgebra
using QuantumOptics
using SHA

const OBJECT_ID = "foundation_r2_admissibility_mc_julia_leg"
const RESULT_PATH = joinpath(@__DIR__, "results", "foundation_foundation_r2_admissibility_mc_julia_leg_results.json")
const TOL = 1.0e-10

classification = "scratch_diagnostic"
promotion_allowed = false
formal_admission_allowed = false
reads_peer_result = false

function sha256_file(path::String)
    isfile(path) || return nothing
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function mat2(rows)
    ComplexF64[rows[1][1] rows[1][2]; rows[2][1] rows[2][2]]
end

function op(basis, rows)
    DenseOperator(basis, mat2(rows))
end

function realtrace(operator)
    real(tr(dense(operator).data))
end

function state_record(basis, name::String, rows; admitted_candidate::Bool)
    rho = op(basis, rows)
    data = dense(rho).data
    probes = Dict(
        "P_z0" => op(basis, [[1, 0], [0, 0]]),
        "P_z1" => op(basis, [[0, 0], [0, 1]]),
        "P_xplus" => op(basis, [[0.5, 0.5], [0.5, 0.5]]),
    )
    probs = Dict(k => realtrace(p * rho) for (k, p) in probes)
    evals = eigvals(Hermitian(data))
    trace_value = tr(data)
    hermitian_residual = norm(data - data')
    det_value = real(det(data))
    violations = String[]
    abs(real(trace_value) - 1.0) <= TOL && abs(imag(trace_value)) <= TOL || push!(violations, "trace=1")
    hermitian_residual <= TOL || push!(violations, "Hermiticity")
    minimum(evals) >= -TOL || push!(violations, "PSD")
    for (probe, prob) in sort(collect(probs))
        (-TOL <= prob <= 1.0 + TOL) || push!(violations, "Born bound $probe")
    end
    Dict{String,Any}(
        "name" => name,
        "matrix" => [[string(data[i, j]) for j in 1:2] for i in 1:2],
        "trace_real" => real(trace_value),
        "trace_imag" => imag(trace_value),
        "determinant" => det_value,
        "min_eigenvalue" => minimum(evals),
        "eigenvalues" => collect(real.(evals)),
        "hermitian_residual" => hermitian_residual,
        "probe_probabilities" => probs,
        "quotient_key_M" => join([string(round(probs[k]; digits=10)) for k in ["P_z0", "P_z1", "P_xplus"]], "|"),
        "violations" => violations,
        "admitted_under_C" => isempty(violations),
        "expected_admitted_candidate" => admitted_candidate,
    )
end

function quotient_classes(records, keys)
    classes = Dict{String,Vector{String}}()
    for r in records
        r["admitted_under_C"] || continue
        key = join([string(round(r["probe_probabilities"][k]; digits=10)) for k in keys], "|")
        if !haskey(classes, key)
            classes[key] = String[]
        end
        push!(classes[key], r["name"])
    end
    classes
end

function build_result()
    started = time()
    basis = SpinBasis(1 // 2)
    states = [
        state_record(basis, "rho_z0", [[1, 0], [0, 0]]; admitted_candidate=true),
        state_record(basis, "rho_z1", [[0, 0], [0, 1]]; admitted_candidate=true),
        state_record(basis, "rho_xplus", [[0.5, 0.5], [0.5, 0.5]]; admitted_candidate=true),
        state_record(basis, "rho_yplus", [[0.5, 0.0 - 0.5im], [0.0 + 0.5im, 0.5]]; admitted_candidate=true),
        state_record(basis, "rho_yminus", [[0.5, 0.0 + 0.5im], [0.0 - 0.5im, 0.5]]; admitted_candidate=true),
        state_record(basis, "rho_convex_mix_z0_xplus_0p4_0p6", [[0.7, 0.3], [0.3, 0.3]]; admitted_candidate=true),
        state_record(basis, "excluded_non_psd_imag_coherence", [[0.5, 0.0 + 0.6im], [0.0 - 0.6im, 0.5]]; admitted_candidate=false),
        state_record(basis, "excluded_trace_1p2", [[0.6, 0], [0, 0.6]]; admitted_candidate=false),
        state_record(basis, "excluded_probe_prob_gt_1", [[0.5, 0.6], [0.6, 0.5]]; admitted_candidate=false),
    ]
    admitted = [r for r in states if r["admitted_under_C"]]
    excluded = [r for r in states if !r["admitted_under_C"]]
    closure_source = Dict(r["name"] => r for r in admitted)
    mix = closure_source["rho_convex_mix_z0_xplus_0p4_0p6"]
    convex_closure = Dict{String,Any}(
        "mixture" => "0.4*rho_z0 + 0.6*rho_xplus",
        "admitted" => mix["admitted_under_C"],
        "probe_probabilities" => mix["probe_probabilities"],
        "min_eigenvalue" => mix["min_eigenvalue"],
    )
    q_full = quotient_classes(states, ["P_z0", "P_z1", "P_xplus"])
    q_drop_pplus = quotient_classes(states, ["P_z0", "P_z1"])
    all_pass = all(r -> r["admitted_under_C"] == r["expected_admitted_candidate"], states) &&
               convex_closure["admitted"] &&
               length(keys(q_drop_pplus)) < length(keys(q_full))

    Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "reads_peer_result" => reads_peer_result,
        "ran" => true,
        "engine" => "julia",
        "backend" => "julia_quantumoptics_authoritative",
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "source_sha256" => sha256_file(@__FILE__),
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "active_project" => Base.active_project(),
        "julia_version" => string(VERSION),
        "M_probe_family" => [
            Dict("id" => "P_z0", "projector" => "|0><0|"),
            Dict("id" => "P_z1", "projector" => "|1><1|"),
            Dict("id" => "P_xplus", "projector" => "|+><+|"),
        ],
        "C_constraints" => ["trace=1", "PSD", "Hermiticity", "0 <= Tr(P rho) <= 1 for every P in M"],
        "states" => states,
        "admitted_names" => [r["name"] for r in admitted],
        "excluded" => [Dict("name" => r["name"], "violations" => r["violations"]) for r in excluded],
        "convex_closure" => convex_closure,
        "quotient_summary" => Dict(
            "relation" => "rho ~_M sigma iff all finite probe probabilities match",
            "full_M_classes" => q_full,
            "drop_P_xplus_classes" => q_drop_pplus,
            "full_M_class_count" => length(keys(q_full)),
            "drop_P_xplus_class_count" => length(keys(q_drop_pplus)),
            "drop_probe_coarsens_quotient" => length(keys(q_drop_pplus)) < length(keys(q_full)),
        ),
        "negative_controls" => Dict(
            "drop_P_xplus_coarsens_quotient" => length(keys(q_drop_pplus)) < length(keys(q_full)),
            "excluded_non_psd_imag_coherence_violation" => "PSD",
        ),
        "all_pass" => all_pass,
        "TOOL_MANIFEST" => Dict(
            "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite Hilbert basis, DenseOperator projectors/states, and Born expectations Tr(P rho) for M and C"),
            "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive eigenvalue/determinant checks on QuantumOptics operator data"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization"),
            "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source fingerprint"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "QuantumOptics" => "load_bearing",
            "LinearAlgebra" => "supportive",
            "JSON" => "supportive",
            "SHA" => "supportive",
        ),
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
    println("result_path=", RESULT_PATH)
    println(
        "SCOUT_DONE all_pass=$(result["all_pass"]) " *
        "admitted=$(length(result["admitted_names"])) " *
        "excluded=$(length(result["excluded"])) " *
        "full_M_classes=$(result["quotient_summary"]["full_M_class_count"]) " *
        "drop_P_xplus_classes=$(result["quotient_summary"]["drop_P_xplus_class_count"]) " *
        "reads_peer_result=$(result["reads_peer_result"])"
    )
    return result["all_pass"] ? 0 : 1
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end
