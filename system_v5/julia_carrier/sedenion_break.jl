module SedenionBreakCarrier

using LinearAlgebra

export FANO,
    add_identity!,
    basis,
    cayley_dickson_double,
    cayley_dickson_multiply,
    concrete_sedenion_witness,
    conjugate_cd,
    left_multiplication_matrix,
    multiply,
    pair_vector,
    prior_octonion_table,
    pure_imaginary_pairs,
    quaternion_table,
    table_checksum,
    terms_from_vector

const TOL = 1.0e-9
const FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

function setprod!(table::Array{Float64,3}, a::Int, b::Int, c::Int, s::Float64)
    table[c + 1, a + 1, b + 1] = s
end

function add_identity!(table::Array{Float64,3}, dim::Int)
    for a in 0:(dim - 1)
        setprod!(table, 0, a, a, 1.0)
        setprod!(table, a, 0, a, 1.0)
    end
    table
end

function quaternion_table()
    table = zeros(Float64, 4, 4, 4)
    add_identity!(table, 4)
    for a in 1:3
        setprod!(table, a, a, 0, -1.0)
    end
    for (i, j, k) in [(1, 2, 3)]
        for (a, b, c, s) in [
            (i, j, k, 1.0), (j, k, i, 1.0), (k, i, j, 1.0),
            (j, i, k, -1.0), (k, j, i, -1.0), (i, k, j, -1.0),
        ]
            setprod!(table, a, b, c, s)
        end
    end
    table
end

function prior_octonion_table()
    table = zeros(Float64, 8, 8, 8)
    add_identity!(table, 8)
    for a in 1:7
        setprod!(table, a, a, 0, -1.0)
    end
    for (i, j, k) in FANO
        for (a, b, c, s) in [
            (i, j, k, 1.0), (j, k, i, 1.0), (k, i, j, 1.0),
            (j, i, k, -1.0), (k, j, i, -1.0), (i, k, j, -1.0),
        ]
            setprod!(table, a, b, c, s)
        end
    end
    table
end

function basis(dim::Int, idx::Int)
    v = zeros(Float64, dim)
    v[idx + 1] = 1.0
    v
end

function multiply(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function conjugate_cd(x::AbstractVector{Float64})
    out = copy(collect(x))
    out[2:end] .*= -1.0
    out
end

function cayley_dickson_multiply(parent::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    n = size(parent, 1)
    a = x[1:n]
    b = x[(n + 1):(2 * n)]
    c = y[1:n]
    d = y[(n + 1):(2 * n)]
    first = multiply(parent, a, c) - multiply(parent, conjugate_cd(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, conjugate_cd(c))
    vcat(first, second)
end

function cayley_dickson_double(parent::Array{Float64,3})
    n = size(parent, 1)
    table = zeros(Float64, 2 * n, 2 * n, 2 * n)
    for i in 1:(2 * n), j in 1:(2 * n)
        x = zeros(Float64, 2 * n)
        y = zeros(Float64, 2 * n)
        x[i] = 1.0
        y[j] = 1.0
        table[:, i, j] .= cayley_dickson_multiply(parent, x, y)
    end
    table
end

function table_checksum(table::Array{Float64,3})
    dim = size(table, 1)
    checksum = 0.0
    nonzero = 0
    abs_sum = 0.0
    for c in 1:dim, a in 1:dim, b in 1:dim
        value = table[c, a, b]
        if abs(value) > 0.0
            nonzero += 1
            abs_sum += abs(value)
            checksum += value * (1_000_003.0 * c + 1_009.0 * a + b)
        end
    end
    Dict{String,Any}(
        "dim" => dim,
        "nonzero_entry_count" => nonzero,
        "sum_abs_entries" => abs_sum,
        "weighted_checksum" => checksum,
    )
end

function terms_from_vector(v::AbstractVector{Float64})
    terms = Vector{Dict{String,Any}}()
    for idx in 0:(length(v) - 1)
        value = v[idx + 1]
        if abs(value) > TOL
            push!(terms, Dict{String,Any}("basis_index" => idx, "coefficient" => value, "label" => "e$idx"))
        end
    end
    terms
end

function pair_vector(dim::Int, i::Int, j::Int; si::Float64 = 1.0, sj::Float64 = 1.0)
    v = zeros(Float64, dim)
    v[i + 1] = si
    v[j + 1] = sj
    v
end

function pure_imaginary_pairs(dim::Int)
    [(i, j) for i in 1:(dim - 1) for j in (i + 1):(dim - 1)]
end

function left_multiplication_matrix(table::Array{Float64,3}, seed::AbstractVector{Float64})
    dim = size(table, 1)
    matrix = zeros(Float64, dim, dim)
    for idx in 0:(dim - 1)
        matrix[:, idx + 1] .= multiply(table, basis(dim, idx), seed)
    end
    matrix
end

function concrete_sedenion_witness(table::Array{Float64,3})
    dim = size(table, 1)
    left = pair_vector(dim, 1, 10)
    right = pair_vector(dim, 5, 14)
    product = multiply(table, left, right)
    Dict{String,Any}(
        "statement" => "(e1 + e10) * (e5 + e14) = 0",
        "left_pair" => [1, 10],
        "right_pair" => [5, 14],
        "left_xor_label" => xor(1, 10),
        "right_xor_label" => xor(5, 14),
        "left_terms" => terms_from_vector(left),
        "right_terms" => terms_from_vector(right),
        "product_terms" => terms_from_vector(product),
        "product_norm" => norm(product),
        "nonzero_left" => norm(left) > TOL,
        "nonzero_right" => norm(right) > TOL,
        "is_zero_divisor_pair" => norm(product) < TOL && norm(left) > TOL && norm(right) > TOL,
        "left_ideal_rank" => rank(left_multiplication_matrix(table, left); atol = TOL),
    )
end

end
