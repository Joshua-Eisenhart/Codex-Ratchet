module ExceptionalAlgebraCanon

export FANO_CYCLES, PROOF_TAGS, BASIN_LABELS,
       Octonion, Albert, basis_octonion, octonion_conj, norm2,
       mul_basis, associator, commutator, jacobiator,
       jordan, jordan_square, jordan_associator, jordan_identity_residual,
       quadratic_representation, albert_trace, albert_unit, primitive_idempotent

"""Single owned orientation convention. Indices 1:7 name imaginary units e1:7."""
const FANO_CYCLES = (
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
)

const PROOF_TAGS = Dict(
    "octonion_table" => "SOURCE_DEFINED_EXACT",
    "octonion_associator_e1_e2_e4" => "SOURCE_DEFINED_EXACT__EXPECTED_2E7",
    "octonion_norm_composition" => "FINITE_CROSS_VALIDATION_REQUIRED",
    "octonion_alternativity" => "FINITE_CROSS_VALIDATION_REQUIRED",
    "imaginary_octonion_malcev" => "FINITE_CROSS_VALIDATION_REQUIRED",
    "albert_jordan_identity" => "FINITE_CROSS_VALIDATION_REQUIRED",
    "exceptional_branch_ratchet_admission" => "NOT_ADMITTED",
)

"""Structural labels only. A label never licenses an empirical basin claim."""
const BASIN_LABELS = Dict(
    "terrain.left.Se" => "Funnel",
    "terrain.left.Ne" => "Vortex",
    "terrain.left.Ni" => "Pit",
    "terrain.left.Si" => "Hill",
    "terrain.right.Se" => "Cannon",
    "terrain.right.Ne" => "Spiral",
    "terrain.right.Ni" => "Source",
    "terrain.right.Si" => "Citadel",
    "engine.type1" => "Type1_left",
    "engine.type2" => "Type2_right",
)

struct Octonion
    c::NTuple{8,Float64}
end

Octonion(xs::AbstractVector{<:Real}) = length(xs) == 8 ? Octonion(ntuple(i -> Float64(xs[i]), 8)) : throw(ArgumentError("octonion needs 8 coefficients"))
Octonion(x::Real) = Octonion((Float64(x), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
Base.zero(::Type{Octonion}) = Octonion(0.0)
Base.zero(::Octonion) = Octonion(0.0)
Base.:+(a::Octonion, b::Octonion) = Octonion(ntuple(i -> a.c[i] + b.c[i], 8))
Base.:-(a::Octonion, b::Octonion) = Octonion(ntuple(i -> a.c[i] - b.c[i], 8))
Base.:-(a::Octonion) = Octonion(ntuple(i -> -a.c[i], 8))
Base.:*(s::Real, a::Octonion) = Octonion(ntuple(i -> Float64(s) * a.c[i], 8))
Base.:*(a::Octonion, s::Real) = s * a
Base.:/(a::Octonion, s::Real) = (1 / Float64(s)) * a
Base.isapprox(a::Octonion, b::Octonion; kwargs...) = all(isapprox(a.c[i], b.c[i]; kwargs...) for i in 1:8)

function basis_octonion(index::Integer)::Octonion
    0 <= index <= 7 || throw(ArgumentError("basis index must be 0:7"))
    Octonion(ntuple(i -> i == index + 1 ? 1.0 : 0.0, 8))
end

"""Return (sign, basis-index) for e_i*e_j, with e_0=1."""
function mul_basis(i::Integer, j::Integer)::Tuple{Int,Int}
    0 <= i <= 7 && 0 <= j <= 7 || throw(ArgumentError("basis indices must be 0:7"))
    i == 0 && return (1, Int(j))
    j == 0 && return (1, Int(i))
    i == j && return (-1, 0)
    for (a, b, c) in FANO_CYCLES
        for (u, v, w) in ((a, b, c), (b, c, a), (c, a, b))
            (i == u && j == v) && return (1, w)
            (i == v && j == u) && return (-1, w)
        end
    end
    error("incomplete Fano convention for ($i,$j)")
end

function Base.:*(a::Octonion, b::Octonion)::Octonion
    out = zeros(Float64, 8)
    for i in 0:7, j in 0:7
        sign, k = mul_basis(i, j)
        out[k + 1] += sign * a.c[i + 1] * b.c[j + 1]
    end
    Octonion(out)
end

octonion_conj(a::Octonion) = Octonion((a.c[1], ntuple(i -> -a.c[i + 1], 7)...))
norm2(a::Octonion) = sum(abs2, a.c)
associator(a::Octonion, b::Octonion, c::Octonion) = (a * b) * c - a * (b * c)
commutator(a::Octonion, b::Octonion) = a * b - b * a
jacobiator(a::Octonion, b::Octonion, c::Octonion) = commutator(commutator(a, b), c) + commutator(commutator(b, c), a) + commutator(commutator(c, a), b)

"""Hermitian 3x3 octonionic matrix: off=(x23,x31,x12)."""
struct Albert
    diag::NTuple{3,Float64}
    off::NTuple{3,Octonion}
end

Base.zero(::Type{Albert}) = Albert((0.0, 0.0, 0.0), (Octonion(0.0), Octonion(0.0), Octonion(0.0)))
Base.:+(x::Albert, y::Albert) = Albert(ntuple(i -> x.diag[i] + y.diag[i], 3), ntuple(i -> x.off[i] + y.off[i], 3))
Base.:-(x::Albert, y::Albert) = Albert(ntuple(i -> x.diag[i] - y.diag[i], 3), ntuple(i -> x.off[i] - y.off[i], 3))
Base.:*(s::Real, x::Albert) = Albert(ntuple(i -> Float64(s) * x.diag[i], 3), ntuple(i -> Float64(s) * x.off[i], 3))
Base.:*(x::Albert, s::Real) = s * x

function _matrix(x::Albert)::Matrix{Octonion}
    x23, x31, x12 = x.off
    [Octonion(x.diag[1]) x12 octonion_conj(x31);
     octonion_conj(x12) Octonion(x.diag[2]) x23;
     x31 octonion_conj(x23) Octonion(x.diag[3])]
end

function _matmul(a::Matrix{Octonion}, b::Matrix{Octonion})::Matrix{Octonion}
    out = fill(Octonion(0.0), 3, 3)
    for i in 1:3, j in 1:3
        value = Octonion(0.0)
        for k in 1:3
            value = value + a[i, k] * b[k, j]
        end
        out[i, j] = value
    end
    out
end

function _hermitian_from_matrix(m::Matrix{Octonion})::Albert
    diag = ntuple(i -> m[i, i].c[1], 3)
    Albert(diag, (m[2, 3], m[3, 1], m[1, 2]))
end

function jordan(x::Albert, y::Albert)::Albert
    a, b = _matrix(x), _matrix(y)
    _hermitian_from_matrix(0.5 .* (_matmul(a, b) + _matmul(b, a)))
end

jordan_square(x::Albert) = jordan(x, x)
jordan_associator(x::Albert, y::Albert, z::Albert) = jordan(jordan(x, y), z) - jordan(x, jordan(y, z))
jordan_identity_residual(x::Albert, y::Albert) = jordan(jordan(jordan_square(x), y), x) - jordan(jordan_square(x), jordan(y, x))
quadratic_representation(p::Albert, b::Albert) = 2 * jordan(p, jordan(p, b)) - jordan(jordan_square(p), b)
albert_trace(x::Albert) = sum(x.diag)
albert_unit() = Albert((1.0, 1.0, 1.0), (Octonion(0.0), Octonion(0.0), Octonion(0.0)))
function primitive_idempotent(index::Integer)::Albert
    1 <= index <= 3 || throw(ArgumentError("primitive idempotent index must be 1:3"))
    Albert(ntuple(i -> i == index ? 1.0 : 0.0, 3), (Octonion(0.0), Octonion(0.0), Octonion(0.0)))
end

end # module

