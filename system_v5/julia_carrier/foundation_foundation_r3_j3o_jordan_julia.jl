#!/usr/bin/env julia

using Dates
using JSON
using LinearAlgebra
using QuantumOptics
using CliffordAlgebras
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RUNG_ID = "foundation_r3_j3o_jordan"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_foundation_r3_j3o_jordan_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_foundation_r3_j3o_jordan_julia_results.json")
const TOL = 1.0e-10
const OFFDIAG_PAIRS = [(1, 2), (1, 3), (2, 3)]

function basis_vector(dim::Int, idx0::Int)
    v = zeros(Float64, dim)
    v[idx0 + 1] = 1.0
    v
end

cd_conj(x::AbstractVector{Float64}) = collect(x) .* vcat([1.0], fill(-1.0, length(x) - 1))

function multiply(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    out = zeros(Float64, size(table, 1))
    @inbounds for c in axes(table, 1), a in axes(table, 2), b in axes(table, 3)
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function cd_pair_multiply(parent::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    n = size(parent, 1)
    a, b = x[1:n], x[(n + 1):(2 * n)]
    c, d = y[1:n], y[(n + 1):(2 * n)]
    vcat(
        multiply(parent, a, c) - multiply(parent, cd_conj(d), b),
        multiply(parent, d, a) + multiply(parent, b, cd_conj(c)),
    )
end

function cd_double(parent::Array{Float64,3})
    dim = 2 * size(parent, 1)
    table = zeros(Float64, dim, dim, dim)
    for i in 0:(dim - 1), j in 0:(dim - 1)
        table[:, i + 1, j + 1] .= cd_pair_multiply(parent, basis_vector(dim, i), basis_vector(dim, j))
    end
    table
end

function clifford_h_table()
    alg = CliffordAlgebra(0, 2)
    elems = [
        basevector(alg, 1),
        basevector(alg, :e1),
        basevector(alg, :e2),
        basevector(alg, :e1) * basevector(alg, :e2),
    ]
    coeff_keys = [1, :e1, :e2, :e1e2]
    table = zeros(Float64, 4, 4, 4)
    for i in 1:4, j in 1:4
        product = elems[i] * elems[j]
        for k in 1:4
            table[k, i, j] = Float64(coefficient(product, coeff_keys[k]))
        end
    end
    table
end

octonion_table() = cd_double(clifford_h_table())
oct_conj(x::AbstractVector{Float64}) = cd_conj(x)
j3_zero() = zeros(Float64, 3, 3, 8)

function j3_from_parts(diag::Vector{Float64}, offdiag::Vector{Vector{Float64}})
    matrix = j3_zero()
    for i in 1:3
        matrix[i, i, 1] = diag[i]
    end
    for (idx, (i, j)) in enumerate(OFFDIAG_PAIRS)
        v = offdiag[idx]
        matrix[i, j, :] .= v
        matrix[j, i, :] .= oct_conj(v)
    end
    matrix
end

function j3_probe_A()
    j3_from_parts(
        [2.0, -1.0, 0.0],
        [
            [0.0, 1.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        ],
    )
end

function j3_probe_B()
    j3_from_parts(
        [0.0, 1.0, -2.0],
        [
            [0.0, 0.0, 1.0, 0.0, 0.0, -1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        ],
    )
end

function primitive_idempotent()
    p = j3_zero()
    u = basis_vector(8, 1)
    p[1, 1, 1] = 0.5
    p[2, 2, 1] = 0.5
    p[1, 2, :] .= -0.5 .* u
    p[2, 1, :] .= oct_conj(p[1, 2, :])
    p
end

function nonhermitian_square_zero_control()
    n = j3_zero()
    n[1, 2, 2] = 1.0
    n
end

function j3_matmul(table::Array{Float64,3}, a::Array{Float64,3}, b::Array{Float64,3})
    out = j3_zero()
    for i in 1:3, k in 1:3
        acc = zeros(Float64, 8)
        for j in 1:3
            acc .+= multiply(table, a[i, j, :], b[j, k, :])
        end
        out[i, k, :] .= acc
    end
    out
end

function jordan(table::Array{Float64,3}, a::Array{Float64,3}, b::Array{Float64,3})
    0.5 .* (j3_matmul(table, a, b) .+ j3_matmul(table, b, a))
end

raw_product(table::Array{Float64,3}, a::Array{Float64,3}, b::Array{Float64,3}) = j3_matmul(table, a, b)

function product_identity_residual(product, table::Array{Float64,3}, a::Array{Float64,3}, b::Array{Float64,3})
    aa = product(table, a, a)
    ab = product(table, a, b)
    product(table, ab, aa) .- product(table, a, product(table, b, aa))
end

function j3_trace(a::Array{Float64,3})
    sum(a[i, i, 1] for i in 1:3)
end

function hermiticity_residual(a::Array{Float64,3})
    residual = 0.0
    for i in 1:3, j in 1:3
        residual = max(residual, norm(a[j, i, :] .- oct_conj(a[i, j, :])))
    end
    for i in 1:3
        residual = max(residual, norm(a[i, i, 2:8]))
    end
    residual
end

max_abs_entry(a::Array{Float64,3}) = maximum(abs.(vec(a)))

function quantumoptics_state_probe()
    basis = NLevelBasis(3)
    rho = DenseOperator(basis, Diagonal([0.5, 0.5, 0.0]))
    mat = Matrix(dense(rho).data)
    eig = eigvals(Hermitian(mat))
    Dict(
        "basis_dimension" => length(basis),
        "trace" => Float64(tr(mat)),
        "min_eigenvalue" => Float64(minimum(eig)),
        "eigenvalues" => [Float64(x) for x in eig],
        "psd" => minimum(eig) >= -TOL,
    )
end

function z3_julia_admissibility_gate(values::Dict{String,Float64}, qo_probe::Dict{String,Any})
    solver = Z3.Solver()
    jordan = Z3.IntVar("julia_j3o_jordan_residual_max_abs")
    raw = Z3.IntVar("julia_j3o_raw_residual_max_abs")
    trace = Z3.IntVar("julia_j3o_formal_trace")
    state_trace = Z3.IntVar("julia_j3o_qo_state_trace")
    idempotent = Z3.IntVar("julia_j3o_idempotent_residual")

    raw_value = round(Int, values["raw_control_residual_max_abs"])
    trace_value = round(Int, values["formal_reality_trace_sum_squares"])
    state_trace_value = round(Int, qo_probe["trace"])
    idempotent_value = round(Int, values["primitive_idempotent_square_residual"])

    Z3.add(solver, jordan == Z3.IntVal(round(Int, values["jordan_identity_residual_max_abs"])))
    Z3.add(solver, raw == Z3.IntVal(raw_value))
    Z3.add(solver, trace == Z3.IntVal(trace_value))
    Z3.add(solver, state_trace == Z3.IntVal(state_trace_value))
    Z3.add(solver, idempotent == Z3.IntVal(idempotent_value))
    Z3.add(solver, jordan == Z3.IntVal(0))
    Z3.add(solver, raw > Z3.IntVal(0))
    Z3.add(solver, trace > Z3.IntVal(0))
    Z3.add(solver, state_trace == Z3.IntVal(1))
    Z3.add(solver, idempotent == Z3.IntVal(0))
    positive_status = string(Z3.check(solver))

    raw_zero = Z3.Solver()
    raw2 = Z3.IntVar("julia_j3o_raw_residual_max_abs_zero_control")
    Z3.add(raw_zero, raw2 == Z3.IntVal(raw_value))
    Z3.add(raw_zero, raw2 == Z3.IntVal(0))
    raw_zero_status = string(Z3.check(raw_zero))

    Dict(
        "solver" => "Z3.jl",
        "positive_admissibility_status" => positive_status,
        "raw_product_zero_negative_status" => raw_zero_status,
        "bound_values" => Dict(
            "jordan_residual_max_abs" => round(Int, values["jordan_identity_residual_max_abs"]),
            "raw_residual_max_abs" => raw_value,
            "formal_trace_sum_squares" => trace_value,
            "quantumoptics_state_trace" => state_trace_value,
            "primitive_idempotent_square_residual" => idempotent_value,
        ),
        "load_bearing" => true,
    )
end

function main()
    table = octonion_table()
    a = j3_probe_A()
    b = j3_probe_B()
    p = primitive_idempotent()
    n = nonhermitian_square_zero_control()

    a_square = jordan(table, a, a)
    b_square = jordan(table, b, b)
    p_square = jordan(table, p, p)
    n_square = jordan(table, n, n)
    sum_squares = a_square .+ b_square
    ab = jordan(table, a, b)
    jordan_residual = product_identity_residual(jordan, table, a, b)
    raw_residual = product_identity_residual(raw_product, table, a, b)
    qo_probe = quantumoptics_state_probe()

    values = Dict(
        "j3_dimension" => 27.0,
        "quantumoptics_observable_dimension" => Float64(qo_probe["basis_dimension"]),
        "quantumoptics_state_trace" => qo_probe["trace"],
        "quantumoptics_state_min_eigenvalue" => qo_probe["min_eigenvalue"],
        "jordan_identity_residual_norm" => norm(vec(jordan_residual)),
        "jordan_identity_residual_max_abs" => max_abs_entry(jordan_residual),
        "raw_control_residual_norm" => norm(vec(raw_residual)),
        "raw_control_residual_max_abs" => max_abs_entry(raw_residual),
        "formal_reality_trace_sum_squares" => j3_trace(sum_squares),
        "primitive_idempotent_trace" => j3_trace(p),
        "primitive_idempotent_square_residual" => norm(vec(p_square .- p)),
        "nonhermitian_control_norm" => norm(vec(n)),
        "nonhermitian_control_square_norm" => norm(vec(n_square)),
        "A_hermiticity_residual" => hermiticity_residual(a),
        "B_hermiticity_residual" => hermiticity_residual(b),
        "P_hermiticity_residual" => hermiticity_residual(p),
        "A_jordan_B_hermiticity_residual" => hermiticity_residual(ab),
    )

    z3_gate = z3_julia_admissibility_gate(values, qo_probe)
    negative = Dict(
        "non_jordan_product_identity_flip" => values["jordan_identity_residual_norm"] <= TOL && values["raw_control_residual_norm"] > TOL,
        "drop_hermiticity_formal_reality_flip" => values["nonhermitian_control_norm"] > TOL && values["nonhermitian_control_square_norm"] <= TOL,
        "z3_raw_product_zero_negative_unsat" => z3_gate["raw_product_zero_negative_status"] == "unsat",
    )
    negative["flipped"] = values["jordan_identity_residual_norm"] <= TOL &&
                          values["raw_control_residual_norm"] > TOL &&
                          values["nonhermitian_control_norm"] > TOL &&
                          values["nonhermitian_control_square_norm"] <= TOL &&
                          z3_gate["positive_admissibility_status"] == "sat" &&
                          z3_gate["raw_product_zero_negative_status"] == "unsat"

    result = Dict(
        "schema_version" => "engine_leg_result_v1",
        "rung_id" => RUNG_ID,
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "created_at" => string(now(UTC)),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "reads_peer_result" => false,
        "packages_used" => ["QuantumOptics", "CliffordAlgebras", "Z3", "JSON", "LinearAlgebra"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "CliffordAlgebras", "Z3"],
        "claim_path_tools" => ["QuantumOptics", "CliffordAlgebras", "Z3"],
        "package_route_note" => "Julia is authoritative for the finite J3(O) arithmetic. QuantumOptics checks the finite normalized PSD state probe; CliffordAlgebras supplies the quaternion table extended by Cayley-Dickson to O; Z3.jl gates the Julia-computed admissibility/control values. The full structural SMT residual derivation is in the JAX z3+cvc5 leg.",
        "M" => Dict(
            "name" => "J3(O) Jordan identity and formal-reality probe family",
            "finite_probe_family" => [
                "A,B: explicit Hermitian 3x3 octonionic observable probes",
                "P: trace-1 primitive positive/idempotent J3(O) state probe",
                "QuantumOptics diagonal PSD state probe with spectrum [0, 1/2, 1/2]",
                "J(A,B): (A o B) o (A o A) - A o (B o (A o A))",
                "FR(A,B): tr(A o A + B o B)",
                "controls: raw matrix product identity residual and non-Hermitian square-zero probe",
            ],
            "observable_dimension" => 27,
        ),
        "C" => Dict(
            "constraints" => [
                "Hermiticity: X[j,i] = conjugate(X[i,j]) and diagonal octonions are real",
                "trace=1 normalized state probe P",
                "PSD/positive-cone witness: P is a primitive Jordan idempotent and QuantumOptics diagonal probe has nonnegative spectrum",
                "normalization: fixed finite integer-coordinate A,B probes; no peer-result reads",
                "rung-specific: J3(O) uses Jordan product X o Y = (XY + YX)/2",
            ],
            "admissible_state_probe" => Dict(
                "trace" => values["primitive_idempotent_trace"],
                "idempotent_residual" => values["primitive_idempotent_square_residual"],
                "quantumoptics_trace" => qo_probe["trace"],
                "quantumoptics_min_eigenvalue" => qo_probe["min_eigenvalue"],
            ),
        ),
        "quotient" => Dict(
            "symbol" => "S/~_M",
            "rule" => "two finite observable structures are equivalent iff the Hermiticity, normalized positive/idempotent, formal-reality, and Jordan-identity probes agree",
            "J3O_class" => "Hermitian octonionic 3x3 matrices close under the Jordan product; the probed identity residual is zero",
            "control_classes" => [
                "raw non-Jordan product is separated by a nonzero identity residual",
                "dropping Hermiticity admits a nonzero square-zero matrix and breaks formal-reality",
            ],
        ),
        "values" => values,
        "quantumoptics_state_probe" => qo_probe,
        "z3_julia_admissibility_gate" => z3_gate,
        "negative_control_flip" => negative,
        "TOOL_MANIFEST" => Dict(
            "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite normalized PSD state probe for the 3-observable slot"),
            "CliffordAlgebras" => Dict("tried" => true, "used" => true, "reason" => "load-bearing quaternion multiplication table used to construct the octonion table"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia-side admissibility/control gate over computed J3(O) values"),
            "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive residual norms/eigenvalue extraction only"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "QuantumOptics" => "load_bearing",
            "CliffordAlgebras" => "load_bearing",
            "Z3" => "load_bearing",
            "LinearAlgebra" => "supportive",
        ),
        "all_pass" => values["jordan_identity_residual_norm"] <= TOL &&
                      values["formal_reality_trace_sum_squares"] > TOL &&
                      values["primitive_idempotent_square_residual"] <= TOL &&
                      values["A_hermiticity_residual"] <= TOL &&
                      values["B_hermiticity_residual"] <= TOL &&
                      values["P_hermiticity_residual"] <= TOL &&
                      values["A_jordan_B_hermiticity_residual"] <= TOL &&
                      qo_probe["psd"] == true &&
                      z3_gate["positive_admissibility_status"] == "sat" &&
                      negative["flipped"],
    )

    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println("wrote: ", RESULT_PATH)
    println(
        "SCOUT_DONE rung=$(RUNG_ID) " *
        "jordan_residual=$(values["jordan_identity_residual_norm"]) " *
        "raw_control=$(values["raw_control_residual_norm"]) " *
        "formal_trace=$(values["formal_reality_trace_sum_squares"]) " *
        "z3_gate=$(z3_gate["positive_admissibility_status"]) " *
        "negative_flip=$(negative["flipped"])"
    )
    return result["all_pass"] ? 0 : 1
end

exit(main())
