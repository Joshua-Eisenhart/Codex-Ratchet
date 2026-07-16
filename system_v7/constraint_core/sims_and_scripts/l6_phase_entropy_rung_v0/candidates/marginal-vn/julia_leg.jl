using JSON
using LinearAlgebra
using QuantumOptics

const EXPECTED_ROW_COUNT = 18
const EIGENVALUE_FLOOR = 1.0e-300
const TWO_QUBIT_BASIS = tensor(SpinBasis(1//2), SpinBasis(1//2))

const VARIANT_GRID = [
    (variant_id = "mvn_bits_from_radius", route = :from_radius, log_base = :bits),
    (variant_id = "mvn_nats_from_radius", route = :from_radius, log_base = :nats),
    (variant_id = "mvn_bits_from_purity", route = :from_purity, log_base = :bits),
    (variant_id = "mvn_nats_from_purity", route = :from_purity, log_base = :nats),
    (variant_id = "mvn_bits_from_negativity", route = :from_negativity, log_base = :bits),
    (variant_id = "mvn_nats_from_negativity", route = :from_negativity, log_base = :nats),
    (variant_id = "mvn_bits_from_state", route = :from_state, log_base = :bits),
    (variant_id = "mvn_nats_from_state", route = :from_state, log_base = :nats),
]

function input_rows(payload::Dict{String,Any})
    if haskey(payload, "rows")
        return payload["rows"]
    elseif haskey(payload, "fixture_observations")
        return payload["fixture_observations"]
    elseif haskey(payload, "row_blocks") && haskey(payload["row_blocks"], "fixture_observations")
        return payload["row_blocks"]["fixture_observations"]
    end
    error("input JSON does not contain fixture rows")
end

function diagonal_marginal(row::Dict{String,Any}, route::Symbol)::Matrix{Float64}
    p = if route === :from_radius
        (1.0 + Float64(row["shell_radius"])) / 2.0
    elseif route === :from_purity
        purity = Float64(row["purity"])
        (1.0 + sqrt(max(0.0, 2.0 * purity - 1.0))) / 2.0
    elseif route === :from_negativity
        negativity = Float64(row["negativity"])
        (1.0 + sqrt(max(0.0, 1.0 - 4.0 * negativity^2))) / 2.0
    else
        error("unknown diagonal reconstruction route: $(route)")
    end

    return Float64[p 0.0; 0.0 1.0 - p]
end

function entropy_from_eigensolver(row::Dict{String,Any}, route::Symbol, log_base::Symbol)::Float64
    rho = diagonal_marginal(row, route)
    eigenvalues = eigvals(Hermitian(rho))
    entropy_nats = 0.0
    for raw_eigenvalue in eigenvalues
        eigenvalue = max(Float64(raw_eigenvalue), 0.0)
        if eigenvalue > EIGENVALUE_FLOOR
            entropy_nats -= eigenvalue * log(eigenvalue)
        end
    end
    return log_base === :bits ? entropy_nats / log(2.0) : entropy_nats
end

function entropy_from_quantum_state(row::Dict{String,Any}, log_base::Symbol)::Float64
    a = Float64(row["a"])
    orientation = Float64(row["orientation"])
    amplitudes = ComplexF64[
        cos(a),
        0.0,
        0.0,
        orientation * sin(a),
    ]
    state = Ket(TWO_QUBIT_BASIS, amplitudes)
    rho_ab = dm(state)
    rho_a = ptrace(rho_ab, [2])
    entropy_nats = Float64(real(QuantumOptics.entropy_vn(rho_a)))
    return log_base === :bits ? entropy_nats / log(2.0) : entropy_nats
end

function variant_values(rows, route::Symbol, log_base::Symbol)::Vector{Float64}
    if route === :from_state
        return [entropy_from_quantum_state(row, log_base) for row in rows]
    end
    return [entropy_from_eigensolver(row, route, log_base) for row in rows]
end

function main()::Nothing
    length(ARGS) == 2 || error("usage: julia_leg.jl <rows_v1.json> <out.json>")
    input_path, output_path = ARGS
    payload = JSON.parsefile(input_path)
    rows = sort(input_rows(payload), by = row -> Int(row["row_id"]))
    length(rows) == EXPECTED_ROW_COUNT || error("expected $(EXPECTED_ROW_COUNT) rows, found $(length(rows))")

    variants = Vector{Dict{String,Any}}()
    for variant in VARIANT_GRID
        push!(variants, Dict{String,Any}(
            "variant_id" => variant.variant_id,
            "values" => variant_values(rows, variant.route, variant.log_base),
        ))
    end

    output = Dict{String,Any}(
        "schema_version" => "l6_phase_entropy_candidate_leg/1.0",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "substrate" => "julia",
        "version" => string(VERSION),
        "variants" => variants,
    )

    open(output_path, "w") do io
        JSON.print(io, output, 2)
        write(io, '\n')
    end
    return nothing
end

main()
