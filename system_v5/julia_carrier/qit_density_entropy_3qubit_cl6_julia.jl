#!/usr/bin/env julia
# object_id: qit_density_entropy_3qubit_cl6_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using QuantumOptics

const OBJECT_ID = "qit_density_entropy_3qubit_cl6_julia"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "qit_density_entropy_3qubit_cl6_julia.jl")
const RESULT_DIR = joinpath(ROOT, "system_v5", "julia_carrier", "results")
const RESULT_PATH = joinpath(RESULT_DIR, "qit_density_entropy_3qubit_cl6_julia_results.json")
const N_QUBITS = 3
const DIM = 2^N_QUBITS
const MIXING_P = 0.3

function ghz_state(b::SpinBasis)
    zero = spindown(b)
    one = spinup(b)
    return (tensor(zero, zero, zero) + tensor(one, one, one)) / sqrt(2.0)
end

function pinned_density_operator(p::Float64)
    qubit = SpinBasis(1 // 2)
    hilbert = tensor(qubit, qubit, qubit)
    psi = ghz_state(qubit)
    pure_density = dm(psi)
    max_mixed = identityoperator(hilbert) / DIM
    return (1.0 - p) * pure_density + p * max_mixed
end

function main()
    rho = pinned_density_operator(MIXING_P)
    vn_entropy = Float64(real(entropy_vn(rho)))
    eigenvalues = sort(Float64.(real.(eigenstates(rho)[1])))

    mkpath(RESULT_DIR)
    result = Dict{String,Any}(
        "rho_spec" => Dict{String,Any}(
            "state" => "GHZ_3qubit",
            "formula" => "(1-p)|psi><psi| + p*I8/8",
            "p" => MIXING_P,
            "basis" => "computational e0..e7, |000>=e0, |111>=e7",
            "dephasing" => false,
            "entropy_base" => "e",
        ),
        "vn_entropy" => vn_entropy,
        "eigenvalues" => eigenvalues,
        "engine" => "julia",
        "package" => "QuantumOptics",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "reads_peer_result" => false,
        "object_id" => OBJECT_ID,
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "active_project" => Base.active_project(),
        "entropy_call" => "QuantumOptics.entropy_vn(rho)",
        "eigenvalue_call" => "QuantumOptics.eigenstates(rho)[1]",
        "TOOL_MANIFEST" => Dict{String,Any}(
            "QuantumOptics" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "load-bearing construction of the 3-qubit tensor SpinBasis, GHZ Ket, density Operator, maximally mixed Operator, entropy_vn, and eigenstates",
            ),
            "Julia JSON/Dates stdlib path support" => Dict{String,Any}(
                "tried" => true,
                "used" => true,
                "reason" => "supportive result serialization and timestamping",
            ),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}(
            "QuantumOptics" => "load_bearing",
            "Julia JSON/Dates stdlib path support" => "supportive",
        ),
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end

    println("wrote ", RESULT_PATH)
    println("vn_entropy=", vn_entropy)
    println("eigenvalues=", eigenvalues)
    println("entropy_call=QuantumOptics.entropy_vn(rho)")
end

main()
