#!/usr/bin/env julia

using Dates
using JSON
using QuantumOptics

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SRC_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_foundation_r1_n01_noncommutation_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_foundation_r1_n01_noncommutation_julia_result.json")
const RUNG_ID = "foundation_r1_n01_noncommutation"
const TOL = 1.0e-12

classification = "scratch_diagnostic"
promotion_allowed = false
formal_admission_allowed = false
reads_peer_result = false

TOOL_MANIFEST = Dict(
    "QuantumOptics" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing qubit basis, Pauli observables, operator products, state expectations, and finite probe quotient signatures",
    ),
    "JSON" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result receipt serialization",
    ),
    "Dates" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive generated_at timestamp",
    ),
)

TOOL_INTEGRATION_DEPTH = Dict(
    "QuantumOptics" => "load_bearing",
    "JSON" => "supportive",
    "Dates" => "supportive",
)

function vec_norm(values)
    return sqrt(sum(abs2, values))
end

function op_norm(op)
    return sqrt(sum(abs2, dense(op).data))
end

function expectation_signature(probes, ket)
    return [round(real(expect(probe, ket)); digits=12) for probe in probes]
end

function quotient_classes(probes, states)
    classes = Dict{String, Vector{String}}()
    signatures = Dict{String, Vector{Float64}}()
    for (name, ket) in states
        sig = expectation_signature(probes, ket)
        key = join(string.(sig), "|")
        if !haskey(classes, key)
            classes[key] = String[]
            signatures[key] = sig
        end
        push!(classes[key], name)
    end
    return [
        Dict("signature" => signatures[key], "members" => classes[key])
        for key in sort(collect(keys(classes)))
    ]
end

function build_result()
    basis = SpinBasis(1 // 2)
    z_probe = sigmaz(basis)
    x_probe = sigmax(basis)
    identity_probe = identityoperator(basis)

    ket_0 = spinup(basis)
    ket_1 = spindown(basis)
    ket_plus = (ket_0 + ket_1) / sqrt(2)
    ket_minus = (ket_0 - ket_1) / sqrt(2)
    ket_y_plus = Ket(basis, ComplexF64[1 / sqrt(2), im / sqrt(2)])
    ket_y_minus = Ket(basis, ComplexF64[1 / sqrt(2), -im / sqrt(2)])
    states = [
        ("ket_0", ket_0),
        ("ket_1", ket_1),
        ("ket_plus", ket_plus),
        ("ket_minus", ket_minus),
        ("ket_y_plus", ket_y_plus),
        ("ket_y_minus", ket_y_minus),
    ]

    noncommuting_probes = [z_probe, x_probe]
    commuting_probes = [z_probe, identity_probe]

    noncommutator = z_probe * x_probe - x_probe * z_probe
    commuting_commutator = z_probe * identity_probe - identity_probe * z_probe
    order_gap_noncommuting = vec_norm((noncommutator * ket_0).data)
    order_gap_commuting = vec_norm((commuting_commutator * ket_0).data)

    noncommuting_classes = quotient_classes(noncommuting_probes, states)
    commuting_classes = quotient_classes(commuting_probes, states)
    class_count_noncommuting = length(noncommuting_classes)
    class_count_commuting = length(commuting_classes)

    result = Dict(
        "schema" => "codex_ratchet.foundation_rung_leg.v1",
        "object_id" => "foundation_foundation_r1_n01_noncommutation_julia",
        "rung_id" => RUNG_ID,
        "engine" => "julia",
        "generated_at" => string(now(UTC), "Z"),
        "source_path" => SRC_PATH,
        "result_path" => RESULT_PATH,
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "reads_peer_result" => reads_peer_result,
        "active_project" => string(Base.active_project()),
        "julia_version" => string(VERSION),
        "packages_used" => ["QuantumOptics", "JSON", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics"],
        "M" => Dict(
            "noncommuting_probe_family" => ["Pauli_Z", "Pauli_X"],
            "commuting_control_family" => ["Pauli_Z", "Identity"],
            "fixture_states" => [name for (name, _) in states],
        ),
        "C" => Dict(
            "admissibility" => ["Hermitian density operator", "trace=1", "PSD", "normalized ket fixtures"],
            "rung_specific_constraint" => "[Z, X] != 0 over the probe family",
            "control_constraint" => "[Z, I] = 0 after commutative collapse",
        ),
        "quotient_summary" => Dict(
            "definition" => "rho ~_M sigma iff Tr(rho O)=Tr(sigma O) for every O in M",
            "noncommuting_coordinates" => ["<Z>", "<X>"],
            "commuting_control_coordinates" => ["<Z>", "<I>"],
            "fixture_class_count_noncommuting" => class_count_noncommuting,
            "fixture_class_count_commuting" => class_count_commuting,
            "noncommuting_classes" => noncommuting_classes,
            "commuting_control_classes" => commuting_classes,
            "strictly_finer_than_commuting_control" => class_count_noncommuting > class_count_commuting,
        ),
        "values" => Dict(
            "commutator_frobenius_norm" => op_norm(noncommutator),
            "commuting_control_commutator_frobenius_norm" => op_norm(commuting_commutator),
            "order_gap_noncommuting" => order_gap_noncommuting,
            "order_gap_commuting" => order_gap_commuting,
            "class_count_noncommuting" => class_count_noncommuting,
            "class_count_commuting" => class_count_commuting,
        ),
        "negative_control_flip" => Dict(
            "noncommuting_order_gap_positive" => order_gap_noncommuting > TOL,
            "commuting_order_gap_zero" => order_gap_commuting <= TOL,
            "commuting_control_coarser_quotient" => class_count_commuting < class_count_noncommuting,
            "flipped" => order_gap_noncommuting > TOL && order_gap_commuting <= TOL && class_count_commuting < class_count_noncommuting,
        ),
        "all_pass" => order_gap_noncommuting > TOL && order_gap_commuting <= TOL && class_count_commuting < class_count_noncommuting,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_manifest" => TOOL_MANIFEST,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
    )
    return result
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println("wrote: ", RESULT_PATH)
    vals = result["values"]
    println(
        "JULIA_N01_DONE all_pass=$(result["all_pass"]) " *
        "order_gap_noncommuting=$(vals["order_gap_noncommuting"]) " *
        "order_gap_commuting=$(vals["order_gap_commuting"]) " *
        "classes_noncommuting=$(vals["class_count_noncommuting"]) " *
        "classes_commuting=$(vals["class_count_commuting"])"
    )
    return result["all_pass"] ? 0 : 2
end

exit(main())
