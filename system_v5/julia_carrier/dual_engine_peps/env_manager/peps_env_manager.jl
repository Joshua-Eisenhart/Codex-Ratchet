module PEPSEnvManagerInfra

using SHA
using PEPSKit
using TensorKit

export PEPSEnvManager,
    build_site_tensor,
    build_single_site_peps,
    peps_state_hash,
    peps_state_hash_timed,
    get_env,
    get_env_cow,
    invalidate!,
    manager_snapshot,
    couple_layers

const PERM_PUR_DL_TO_PNESW = (1, 2, 3, 4, 5)
const DEFAULT_CTM_TOL = 1.0e-6
const DEFAULT_CTM_MINITER = 1
const DEFAULT_CTM_MAXITER = 50
const DEFAULT_CTM_VERBOSITY = 0
const DEFAULT_CTM_TRUNC = (; alg = :fixedspace)

mutable struct PEPSEnvManager
    peps_ref::Any
    cached_env::Any
    state_hash::Union{Nothing,String}
    recompute_count::Int
    cached_chi::Union{Nothing,Int}
    last_status::Symbol
    last_hash_seconds::Float64
    last_recompute_seconds::Float64
    last_miss_reason::String
    last_info::Any
end

PEPSEnvManager() = PEPSEnvManager(
    nothing,
    nothing,
    nothing,
    0,
    nothing,
    :empty,
    0.0,
    0.0,
    "empty_cache",
    nothing,
)

function build_site_tensor(A_raw::Array{<:Number,5})
    A = permutedims(A_raw, PERM_PUR_DL_TO_PNESW)
    p = size(A, 1)
    D = size(A, 2)
    @assert size(A) == (p, D, D, D, D) "expected square virtual dims, got $(size(A))"
    Pp = ComplexSpace(p)
    V = ComplexSpace(D)
    return TensorMap(ComplexF64.(A), Pp ← V ⊗ V ⊗ dual(V) ⊗ dual(V))
end

build_single_site_peps(A_raw::Array{<:Number,5}) = InfinitePEPS(build_site_tensor(A_raw))

function _peps_tensor_cells(peps)
    if :A in fieldnames(typeof(peps))
        return getfield(peps, :A)
    end
    error("Unsupported PEPS object: expected a PEPSKit InfinitePEPS-like object with field :A")
end

function _write_i64!(io::IO, x::Integer)
    write(io, Int64(x))
    return nothing
end

function _write_string!(io::IO, s::AbstractString)
    _write_i64!(io, ncodeunits(s))
    write(io, s)
    return nothing
end

function _write_dense_array!(io::IO, tensor)
    dense = Array{ComplexF64}(convert(Array, tensor))
    _write_string!(io, string(eltype(dense)))
    _write_i64!(io, ndims(dense))
    for d in size(dense)
        _write_i64!(io, d)
    end
    write(io, collect(reinterpret(UInt8, vec(dense))))
    return nothing
end

function peps_state_hash(peps)::String
    cells = _peps_tensor_cells(peps)
    io = IOBuffer()
    _write_string!(io, "PEPSEnvManager.state_hash.v1")
    _write_string!(io, string(typeof(peps)))
    _write_i64!(io, ndims(cells))
    for d in size(cells)
        _write_i64!(io, d)
    end
    for I in CartesianIndices(cells)
        _write_i64!(io, I.I[1])
        _write_i64!(io, I.I[2])
        tensor = cells[I]
        _write_string!(io, string(typeof(tensor)))
        _write_dense_array!(io, tensor)
    end
    return bytes2hex(sha256(take!(io)))
end

function peps_state_hash_timed(peps)
    t0 = time()
    h = peps_state_hash(peps)
    return h, time() - t0
end

function _miss_reason(mgr::PEPSEnvManager, state_hash::String, chi::Int)
    mgr.cached_env === nothing && return "empty_cache"
    mgr.state_hash != state_hash && return "state_hash_changed"
    mgr.cached_chi != chi && return "chi_changed"
    return "unknown"
end

function _run_leading_boundary(peps; chi::Int,
        tol::Real = DEFAULT_CTM_TOL,
        miniter::Int = DEFAULT_CTM_MINITER,
        maxiter::Int = DEFAULT_CTM_MAXITER,
        verbosity::Int = DEFAULT_CTM_VERBOSITY,
        trunc = DEFAULT_CTM_TRUNC)
    env0 = CTMRGEnv(peps, ComplexSpace(chi))
    return leading_boundary(env0, peps;
        tol = tol,
        miniter = miniter,
        maxiter = maxiter,
        trunc = trunc,
        verbosity = verbosity)
end

function get_env(mgr::PEPSEnvManager, peps; chi::Int,
        tol::Real = DEFAULT_CTM_TOL,
        miniter::Int = DEFAULT_CTM_MINITER,
        maxiter::Int = DEFAULT_CTM_MAXITER,
        verbosity::Int = DEFAULT_CTM_VERBOSITY,
        trunc = DEFAULT_CTM_TRUNC)
    state_hash, hash_seconds = peps_state_hash_timed(peps)
    mgr.last_hash_seconds = hash_seconds

    if mgr.cached_env !== nothing && mgr.state_hash == state_hash && mgr.cached_chi == chi
        mgr.peps_ref = peps
        mgr.last_status = :hit
        mgr.last_recompute_seconds = 0.0
        mgr.last_miss_reason = ""
        return mgr.cached_env
    end

    miss_reason = _miss_reason(mgr, state_hash, chi)
    t0 = time()
    env, info = _run_leading_boundary(peps;
        chi = chi,
        tol = tol,
        miniter = miniter,
        maxiter = maxiter,
        verbosity = verbosity,
        trunc = trunc)
    recompute_seconds = time() - t0

    mgr.peps_ref = peps
    mgr.cached_env = env
    mgr.state_hash = state_hash
    mgr.cached_chi = chi
    mgr.recompute_count += 1
    mgr.last_status = :miss
    mgr.last_hash_seconds = hash_seconds
    mgr.last_recompute_seconds = recompute_seconds
    mgr.last_miss_reason = miss_reason
    mgr.last_info = info
    return mgr.cached_env
end

function get_env_cow(mgr::PEPSEnvManager, peps; kwargs...)
    next_mgr = PEPSEnvManager(
        mgr.peps_ref,
        mgr.cached_env,
        mgr.state_hash,
        mgr.recompute_count,
        mgr.cached_chi,
        mgr.last_status,
        mgr.last_hash_seconds,
        mgr.last_recompute_seconds,
        mgr.last_miss_reason,
        mgr.last_info,
    )
    env = get_env(next_mgr, peps; kwargs...)
    return env, next_mgr
end

function invalidate!(mgr::PEPSEnvManager)
    mgr.peps_ref = nothing
    mgr.cached_env = nothing
    mgr.state_hash = nothing
    mgr.cached_chi = nothing
    mgr.last_status = :invalidated
    mgr.last_hash_seconds = 0.0
    mgr.last_recompute_seconds = 0.0
    mgr.last_miss_reason = "invalidated"
    mgr.last_info = nothing
    return mgr
end

function manager_snapshot(mgr::PEPSEnvManager)
    return Dict{String,Any}(
        "has_peps_ref" => mgr.peps_ref !== nothing,
        "has_cached_env" => mgr.cached_env !== nothing,
        "state_hash" => mgr.state_hash,
        "cached_chi" => mgr.cached_chi,
        "recompute_count" => mgr.recompute_count,
        "last_status" => string(mgr.last_status),
        "last_hash_seconds" => mgr.last_hash_seconds,
        "last_recompute_seconds" => mgr.last_recompute_seconds,
        "last_miss_reason" => mgr.last_miss_reason,
    )
end

function _spin_half_sz_operator()
    P = ComplexSpace(2)
    return LocalOperator(
        fill(P, 1, 1),
        (CartesianIndex(1, 1),) => TensorMap(ComplexF64[1 0; 0 -1], P, P),
    )
end

function _safe_expectation(peps, op, env)
    try
        return real(expectation_value(peps, op, env)), ""
    catch e
        return nothing, sprint(showerror, e)
    end
end

function couple_layers(
        mgr_a::PEPSEnvManager,
        peps_a,
        mgr_b::PEPSEnvManager,
        peps_b;
        chi::Int,
        coupling_strength::Real = 1.0,
        tol::Real = DEFAULT_CTM_TOL,
        miniter::Int = DEFAULT_CTM_MINITER,
        maxiter::Int = DEFAULT_CTM_MAXITER,
        verbosity::Int = DEFAULT_CTM_VERBOSITY,
        trunc = DEFAULT_CTM_TRUNC)
    env_a = get_env(mgr_a, peps_a;
        chi = chi,
        tol = tol,
        miniter = miniter,
        maxiter = maxiter,
        verbosity = verbosity,
        trunc = trunc)
    status_a = string(mgr_a.last_status)
    count_a = mgr_a.recompute_count

    env_b = get_env(mgr_b, peps_b;
        chi = chi,
        tol = tol,
        miniter = miniter,
        maxiter = maxiter,
        verbosity = verbosity,
        trunc = trunc)
    status_b = string(mgr_b.last_status)
    count_b = mgr_b.recompute_count

    sz = _spin_half_sz_operator()
    mz_a, err_a = _safe_expectation(peps_a, sz, env_a)
    mz_b, err_b = _safe_expectation(peps_b, sz, env_b)
    inter_layer_energy = (mz_a === nothing || mz_b === nothing) ?
        nothing : Float64(coupling_strength) * mz_a * mz_b

    return Dict{String,Any}(
        "stub_scope" => "pseudo-3D environment-manager wiring only; not a 3D tensor-network contraction",
        "operator_owner_label" => "NiTe/SeTi",
        "operator_math_stub" => "J_perp * sigma_z(layer_1) tensor sigma_z(layer_2), evaluated as a mean-field product of single-layer CTMRG readouts",
        "coupling_strength" => Float64(coupling_strength),
        "layer_a" => Dict(
            "env_status" => status_a,
            "recompute_count" => count_a,
            "onsite_sz" => mz_a,
            "expectation_error" => err_a,
        ),
        "layer_b" => Dict(
            "env_status" => status_b,
            "recompute_count" => count_b,
            "onsite_sz" => mz_b,
            "expectation_error" => err_b,
        ),
        "energy_terms" => Dict(
            "inter_layer_stub" => inter_layer_energy,
        ),
        "pepskit_gap" => "PEPSKit exposes per-layer InfinitePEPS CTMRGEnv caching and expectation_value, but not a native stacked-2D/pseudo-3D cross-layer environment object in this local API probe.",
        "promotion_allowed" => false,
    )
end

end
