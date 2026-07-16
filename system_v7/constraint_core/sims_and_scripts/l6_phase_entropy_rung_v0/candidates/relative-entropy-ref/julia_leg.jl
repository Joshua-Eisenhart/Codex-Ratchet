using JSON
using LinearAlgebra
using QuantumOptics

const EXPECTED_ROW_COUNT = 18
const EXPECTED_REFERENCE_COUNT = 11
const EIGENVALUE_FLOOR = 1.0e-300
const QUBIT_BASIS = SpinBasis(1//2)

function row_density(row::Dict{String,Any})::Matrix{ComplexF64}
    angle = Float64(row["a"])
    orientation = Float64(row["orientation"])
    state = Ket(QUBIT_BASIS, ComplexF64[cos(angle), orientation * sin(angle)])
    return Matrix{ComplexF64}(dm(state).data)
end

function reference_density(reference::Dict{String,Any})::Matrix{ComplexF64}
    x, y, z = Float64.(reference["reference_bloch_vector"])
    matrix = ComplexF64[
        (1.0 + z) / 2.0 (x - im * y) / 2.0;
        (x + im * y) / 2.0 (1.0 - z) / 2.0
    ]
    return Matrix{ComplexF64}(Operator(QUBIT_BASIS, matrix).data)
end

function relative_entropy_nats(rho::Matrix{ComplexF64}, sigma::Matrix{ComplexF64})::Float64
    rho_eigenvalues = eigvals(Hermitian(rho))
    rho_log_rho = 0.0
    for eigenvalue in rho_eigenvalues
        value = Float64(real(eigenvalue))
        if value > EIGENVALUE_FLOOR
            rho_log_rho += value * log(value)
        end
    end

    sigma_decomposition = eigen(Hermitian(sigma))
    all(sigma_decomposition.values .> 0.0) || error("reference density operator is not positive definite")
    log_sigma = sigma_decomposition.vectors * Diagonal(log.(sigma_decomposition.values)) * sigma_decomposition.vectors'
    rho_log_sigma = real(tr(rho * log_sigma))
    return Float64(rho_log_rho - rho_log_sigma)
end

function main()::Nothing
    length(ARGS) == 3 || error("usage: julia_leg.jl <rows_v1.json> <references_v1.json> <out.json>")
    rows_path, references_path, output_path = ARGS
    rows = sort(JSON.parsefile(rows_path)["rows"], by = row -> Int(row["row_id"]))
    references = JSON.parsefile(references_path)["references"]
    length(rows) == EXPECTED_ROW_COUNT || error("expected $(EXPECTED_ROW_COUNT) rows, found $(length(rows))")
    length(references) == EXPECTED_REFERENCE_COUNT || error("expected $(EXPECTED_REFERENCE_COUNT) references, found $(length(references))")

    row_densities = [row_density(row) for row in rows]
    variants = Vector{Dict{String,Any}}()
    for reference in references
        sigma = reference_density(reference)
        push!(variants, Dict{String,Any}(
            "variant_id" => reference["variant_id"],
            "values" => [relative_entropy_nats(rho, sigma) for rho in row_densities],
        ))
    end

    output = Dict{String,Any}(
        "schema_version" => "l6_phase_entropy_candidate_leg/1.0",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "substrate" => "julia",
        "version" => string(VERSION),
        "julia_project" => Base.active_project(),
        "packages_used" => ["JSON", "LinearAlgebra", "QuantumOptics"],
        "dtype" => "Float64/ComplexF64",
        "variants" => variants,
    )
    open(output_path, "w") do io
        JSON.print(io, output, 2)
        write(io, '\n')
    end
    return nothing
end

main()
