#!/usr/bin/env julia

"""
Julia leg for the hardened Gap K tensor-chain fit diagnostic.

This file deliberately regenerates every fixture from the same public integer
formula as the Python leg. It never reads Python state or Python results. The
JSON returned on stdout is a bounded, non-promoting function receipt for
ITensors and ITensorMPS; it is not a Canon or scientific-admission artifact.
"""

using ITensors
using ITensorMPS
using JSON3
using LinearAlgebra
using SHA

const N_QUBITS = 6
const CUT = 3
const MAX_SCHMIDT_RANK = 2^CUT

function normalize_state!(state)
    state ./= sqrt(sum(abs2, state))
    return state
end

function primary_state()
    shape = ntuple(_ -> 2, N_QUBITS)
    state = zeros(ComplexF64, shape)
    for bits in Iterators.product(ntuple(_ -> 0:1, N_QUBITS)...)
        index = sum(bits[j] << (N_QUBITS - j) for j in 1:N_QUBITS)
        weight = sum(bits)
        real_part = mod(37 * (index + 1)^2 + 11 * (weight + 1) + 5, 101) - 50
        imag_part = mod(29 * (index + 3)^2 + 7 * (weight + 2) + 13, 103) - 51
        state[Tuple(bits .+ 1)...] = complex(real_part, imag_part)
    end
    return normalize_state!(state)
end

function ghz_state()
    state = zeros(ComplexF64, ntuple(_ -> 2, N_QUBITS))
    state[ntuple(_ -> 1, N_QUBITS)...] = inv(sqrt(2.0))
    state[ntuple(_ -> 2, N_QUBITS)...] = inv(sqrt(2.0))
    return state
end

function product_state()
    state = zeros(ComplexF64, ntuple(_ -> 2, N_QUBITS))
    state[ntuple(_ -> 1, N_QUBITS)...] = 1.0
    return state
end

function tampered_state()
    state = primary_state()
    # Bits 101101: a deterministic, non-boundary coefficient perturbation.
    state[2, 1, 2, 2, 1, 2] *= 1.2 * cis(0.123)
    return normalize_state!(state)
end

function padded_descending(values)
    result = sort(Float64.(abs.(values)); rev=true)
    append!(result, zeros(Float64, MAX_SCHMIDT_RANK - length(result)))
    return result[1:MAX_SCHMIDT_RANK]
end

function state_checksum(state)
    weighted_real = 0.0
    weighted_imag = 0.0
    support = 0
    magnitudes = Float64[]
    selected = Dict{String, Any}()

    for index in 0:(2^N_QUBITS - 1)
        bits = [Int((index >> (N_QUBITS - j)) & 1) for j in 1:N_QUBITS]
        value = state[Tuple(bits .+ 1)...]
        weighted_real += (index + 1) * real(value)
        weighted_imag += (index + 1) * imag(value)
        magnitude = abs(value)
        push!(magnitudes, magnitude)
        support += magnitude > 1.0e-15 ? 1 : 0
        if index in (0, 37, 63)
            selected[string(index)] = Dict("real" => real(value), "imag" => imag(value))
        end
    end

    return Dict(
        "weighted_real" => weighted_real,
        "weighted_imag" => weighted_imag,
        "support" => support,
        "min_magnitude" => minimum(magnitudes),
        "max_magnitude" => maximum(magnitudes),
        "magnitude_spread" => maximum(magnitudes) - minimum(magnitudes),
        "selected_amplitudes" => selected,
    )
end

function measure_with_itensors(state)
    sites = siteinds("Qubit", N_QUBITS)
    psi = MPS(state, sites; cutoff=0.0, maxdim=MAX_SCHMIDT_RANK)
    state_norm = real(inner(psi, psi))
    bond_dimensions = linkdims(psi)

    reconstructed = Array(contract(psi), sites...)
    reconstruction_error = maximum(abs.(reconstructed .- state))

    orthogonalize!(psi, CUT)
    left_link = linkind(psi, CUT - 1)
    physical_index = siteind(psi, CUT)
    _, singular_tensor, _ = svd(
        psi[CUT],
        (left_link, physical_index);
        cutoff=0.0,
        maxdim=MAX_SCHMIDT_RANK,
    )
    singular_values = padded_descending([
        abs(singular_tensor[n, n])
        for n in 1:min(ITensors.dims(singular_tensor)...)
    ])
    probabilities = singular_values .^ 2
    entropy_bits = -sum(p > 0.0 ? p * log2(p) : 0.0 for p in probabilities)
    entropy_nats = -sum(p > 0.0 ? p * log(p) : 0.0 for p in probabilities)

    dense_matrix = reshape(state, 2^CUT, 2^(N_QUBITS - CUT))
    dense_singular_values = padded_descending(svdvals(dense_matrix))

    return Dict(
        "state_checksum" => state_checksum(state),
        "mps_norm_squared" => state_norm,
        "mps_bond_dimensions" => bond_dimensions,
        "mps_reconstruction_max_abs_error" => reconstruction_error,
        "mps_singular_values" => singular_values,
        "schmidt_probabilities" => probabilities,
        "entropy_bits" => entropy_bits,
        "entropy_nats" => entropy_nats,
        "dense_oracle_singular_values" => dense_singular_values,
        "mps_vs_dense_spectrum_max_abs" => maximum(abs.(singular_values .- dense_singular_values)),
    )
end

function dimension_negative_control()
    state = primary_state()
    wrong_sites = siteinds("Qubit", N_QUBITS - 1)
    try
        MPS(state, wrong_sites; cutoff=0.0, maxdim=MAX_SCHMIDT_RANK)
        return Dict(
            "rejected" => false,
            "exception_type" => nothing,
            "message" => "wrong-site-count input was unexpectedly accepted",
        )
    catch error
        return Dict(
            "rejected" => true,
            "exception_type" => string(typeof(error)),
            "message" => sprint(showerror, error),
        )
    end
end

function package_metadata(package_module)
    return Dict(
        "version" => string(pkgversion(package_module)),
        "module_path" => string(pathof(package_module)),
    )
end

function main()
    result = Dict(
        "schema_version" => "gap_k_tensor_chain_v2_julia_leg_v1",
        "classification" => "tool_lego_fit_probe",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "runtime" => Dict(
            "julia_version" => string(VERSION),
            "executable" => joinpath(Sys.BINDIR, Base.julia_exename()),
            "active_project" => Base.active_project(),
            "load_path" => collect(Base.LOAD_PATH),
            "depot_path" => collect(Base.DEPOT_PATH),
            "packages" => Dict(
                "ITensors" => package_metadata(ITensors),
                "ITensorMPS" => package_metadata(ITensorMPS),
                "JSON3" => package_metadata(JSON3),
            ),
        ),
        "source_sha256" => bytes2hex(sha256(read(@__FILE__))),
        "state_generation" => Dict(
            "independent_of_python_results" => true,
            "state_exchange" => "none; both legs regenerate the declared fixture formula",
            "primary_formula" => "a_k=((37(k+1)^2+11(w+1)+5) mod 101-50)+i*((29(k+3)^2+7(w+2)+13) mod 103-51), then L2 normalize",
        ),
        "cases" => Dict(
            "primary" => measure_with_itensors(primary_state()),
            "tampered" => measure_with_itensors(tampered_state()),
            "ghz_control" => measure_with_itensors(ghz_state()),
            "product_control" => measure_with_itensors(product_state()),
        ),
        "dimension_negative" => dimension_negative_control(),
        "tool_api_calls" => [
            "ITensorMPS.MPS(::AbstractArray, sites; cutoff=0.0, maxdim=8)",
            "ITensorMPS.inner(::MPS, ::MPS)",
            "ITensorMPS.contract(::MPS)",
            "ITensorMPS.orthogonalize!(::MPS, 3)",
            "ITensors.svd(::ITensor, left_indices; cutoff=0.0, maxdim=8)",
            "ITensorMPS.MPS wrong-dimension rejection",
        ],
    )
    print(JSON3.write(result))
end

main()
