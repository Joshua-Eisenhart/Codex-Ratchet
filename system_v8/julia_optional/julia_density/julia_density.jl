using JSON
using LinearAlgebra
using QuantumOptics

function entropy_bits(values)
    -sum(value > 0.0 ? value * log2(value) : 0.0 for value in values)
end

function assert_agreement(label, primary, crosscheck)
    isapprox(primary, crosscheck; rtol=1.0e-13, atol=1.0e-14) ||
        error("$label disagreement: QuantumOptics=$primary LinearAlgebra=$crosscheck")
end

function main()
    length(ARGS) == 1 || error("usage: julia_density.jl FIXTURE")
    fixture = JSON.parsefile(ARGS[1])
    raw_matrix = Matrix{ComplexF64}(
        reduce(vcat, permutedims.(fixture["rho"]))
    )
    size(raw_matrix) == (2, 2) || error("rho must be a 2x2 matrix")

    basis = QuantumOptics.NLevelBasis(size(raw_matrix, 1))
    rho = QuantumOptics.DenseOperator(basis, basis, raw_matrix)
    qo_trace = Float64(real(QuantumOptics.tr(rho)))
    qo_eigenvalues = sort(Float64.(real.(QuantumOptics.eigenenergies(rho))))

    la_trace = Float64(real(LinearAlgebra.tr(raw_matrix)))
    la_eigenvalues = sort(
        Float64.(LinearAlgebra.eigvals(LinearAlgebra.Hermitian(raw_matrix)))
    )
    assert_agreement("trace", qo_trace, la_trace)
    assert_agreement("spectrum", qo_eigenvalues, la_eigenvalues)

    diagonal_values = LinearAlgebra.diag(rho.data)
    dephased_matrix = Matrix(LinearAlgebra.Diagonal(diagonal_values))
    dephased_rho = QuantumOptics.DenseOperator(basis, basis, dephased_matrix)
    qo_dephased_eigenvalues = sort(
        Float64.(real.(QuantumOptics.eigenenergies(dephased_rho)))
    )
    la_dephased_eigenvalues = sort(
        Float64.(
            LinearAlgebra.eigvals(LinearAlgebra.Hermitian(dephased_matrix))
        )
    )
    assert_agreement(
        "dephased spectrum",
        qo_dephased_eigenvalues,
        la_dephased_eigenvalues,
    )

    rank = count(value -> value > 1.0e-12, qo_eigenvalues)
    observed = Dict(
        "trace" => qo_trace,
        "eigenvalues" => qo_eigenvalues,
        "rank" => rank,
        "hartley_bits" => log2(rank),
        "von_neumann_bits" => entropy_bits(qo_eigenvalues),
        "dephased_entropy_bits" => entropy_bits(qo_dephased_eigenvalues),
    )
    witness = Dict(
        "julia_version" => string(VERSION),
        "quantumoptics_version" => string(Base.pkgversion(QuantumOptics)),
        "observed" => observed,
        "dispatch" => [
            "QuantumOptics.NLevelBasis",
            "QuantumOptics.DenseOperator",
            "QuantumOptics.tr",
            "QuantumOptics.eigenenergies",
            "LinearAlgebra.tr",
            "LinearAlgebra.eigvals",
            "LinearAlgebra.Hermitian",
            "LinearAlgebra.diag",
        ],
    )
    JSON.print(stdout, witness)
    println()
end

main()
