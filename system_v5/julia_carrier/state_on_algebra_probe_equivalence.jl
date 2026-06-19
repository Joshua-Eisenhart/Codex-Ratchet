#!/usr/bin/env julia
# object_id: state_on_algebra_probe_equivalence
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: Finite state-on-algebra/probe-equivalence diagnostic only. No
# basin, admission, engine, Axis0, bridge, gravity, or manifold-closure claim.

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "state_on_algebra_probe_equivalence"
const RESULT_PATH = joinpath(@__DIR__, "state_on_algebra_probe_equivalence_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "state_on_algebra_probe_equivalence_jax_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const STRUCTURE_PROBE_COUNT = 12

const FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]
const OFFDIAG_PAIRS = [(1, 2), (1, 3), (2, 3)]

function paulis()
    id = ComplexF64[1 0; 0 1]
    sx = ComplexF64[0 1; 1 0]
    sy = ComplexF64[0 -im; im 0]
    sz = ComplexF64[1 0; 0 -1]
    id, sx, sy, sz
end

function omega_m2(rho::AbstractMatrix{ComplexF64}, x::AbstractMatrix{ComplexF64})
    tr(rho * x)
end

function complex_sample_matrices()
    id, sx, sy, sz = paulis()
    samples = Matrix{ComplexF64}[id, sx, sy, sz]
    push!(samples, ComplexF64[0.2+0.1im -0.4+0.3im; 0.7-0.2im 0.5+0.6im])
    push!(samples, ComplexF64[-0.1+0.8im 0.25-0.35im; -0.2+0.15im 0.4-0.45im])
    samples
end

function reconstruct_hermitian_from_probes(expectations::Vector{Float64}, probes::Vector{Matrix{ComplexF64}})
    n = length(probes)
    gram = zeros(Float64, n, n)
    for i in 1:n, j in 1:n
        gram[i, j] = real(tr(probes[i] * probes[j]))
    end
    coeffs = gram \ expectations
    out = zeros(ComplexF64, 2, 2)
    for i in 1:n
        out .+= coeffs[i] .* probes[i]
    end
    out
end

function von_neumann_entropy(rho::Matrix{ComplexF64})
    vals = eigvals(Hermitian(rho))
    total = 0.0
    for λ in vals
        x = max(Float64(real(λ)), 0.0)
        x > TOL && (total -= x * log(x))
    end
    total
end

function m2c_checks()
    id, sx, sy, sz = paulis()
    probes = Matrix{ComplexF64}[id, sx, sy, sz]
    nonspanning = Matrix{ComplexF64}[id, sz]
    rx, ry, rz = 0.35, -0.22, 0.41
    rho = 0.5 .* (id .+ rx .* sx .+ ry .* sy .+ rz .* sz)
    rho_plus = 0.5 .* (id .+ 0.20 .* sx)
    rho_minus = 0.5 .* (id .- 0.20 .* sx)

    trace_residual = abs(real(tr(rho)) - 1.0)
    hermitian_residual = norm(rho - rho')
    min_eigenvalue = minimum(real.(eigvals(Hermitian(rho))))
    normalization_residual = abs(omega_m2(rho, id) - 1.0)

    samples = complex_sample_matrices()
    positivity_vals = [real(omega_m2(rho, x' * x)) for x in samples]
    positivity_min = minimum(positivity_vals)

    a = samples[end - 1]
    b = samples[end]
    α = 0.3 - 0.2im
    β = -0.4 + 0.7im
    linearity = abs(omega_m2(rho, α .* a .+ β .* b) - (α * omega_m2(rho, a) + β * omega_m2(rho, b)))
    star_preservation = maximum(abs(omega_m2(rho, x') - conj(omega_m2(rho, x))) for x in samples)

    expectations = [real(omega_m2(rho, p)) for p in probes]
    reconstructed = reconstruct_hermitian_from_probes(expectations, probes)
    spanning_reconstruction_residual = norm(reconstructed - rho)
    spanning_reconstructed_pair_max_abs_diff = maximum(abs(real(omega_m2(reconstructed, p)) - real(omega_m2(rho, p))) for p in probes)
    full_probe_distinct_gap = maximum(abs(real(omega_m2(rho_plus, p)) - real(omega_m2(rho_minus, p))) for p in probes)
    nonspanning_collision_max_abs_diff = maximum(abs(real(omega_m2(rho_plus, p)) - real(omega_m2(rho_minus, p))) for p in nonspanning)
    nonspanning_state_frobenius_gap = norm(rho_plus - rho_minus)

    coarse_expectations = [real(omega_m2(rho, p)) for p in nonspanning]
    rho_coarse = reconstruct_hermitian_from_probes(coarse_expectations, nonspanning)
    entropy_full = von_neumann_entropy(rho)
    entropy_coarse = von_neumann_entropy(rho_coarse)
    entropy_gap = abs(entropy_coarse - entropy_full)

    bad_trace = ComplexF64[0.7 0; 0 0.7]
    bad_positive = ComplexF64[1.2 0; 0 -0.2]
    bad_trace_normalization_residual = abs(real(omega_m2(bad_trace, id)) - 1.0)
    bad_positive_min = minimum(real(omega_m2(bad_positive, x' * x)) for x in [id, ComplexF64[0 0; 0 1]])

    Dict{String,Any}(
        "state_valid" => trace_residual < TOL && hermitian_residual < TOL && min_eigenvalue >= -TOL &&
            abs(normalization_residual) < TOL && positivity_min >= -TOL && linearity < TOL && star_preservation < TOL,
        "spanning_separates" => spanning_reconstruction_residual < TOL && full_probe_distinct_gap > 1.0e-3,
        "nonspanning_collision" => nonspanning_collision_max_abs_diff < TOL && nonspanning_state_frobenius_gap > 1.0e-3,
        "entropy_is_readout" => entropy_full > 0.0 && entropy_gap > 1.0e-3,
        "bad_controls_ok" => bad_trace_normalization_residual > 1.0e-3 && bad_positive_min < -1.0e-3,
        "numbers" => Dict{String,Any}(
            "trace_residual" => trace_residual,
            "hermitian_residual" => hermitian_residual,
            "min_eigenvalue" => min_eigenvalue,
            "normalization_residual" => abs(normalization_residual),
            "linearity_max_residual" => linearity,
            "star_preservation_residual" => star_preservation,
            "positivity_min_AstarA" => positivity_min,
            "spanning_reconstruction_frobenius_residual" => spanning_reconstruction_residual,
            "spanning_reconstructed_pair_max_abs_diff" => spanning_reconstructed_pair_max_abs_diff,
            "full_probe_distinct_gap" => full_probe_distinct_gap,
            "nonspanning_collision_max_abs_diff" => nonspanning_collision_max_abs_diff,
            "nonspanning_state_frobenius_gap" => nonspanning_state_frobenius_gap,
            "entropy_full" => entropy_full,
            "entropy_coarse" => entropy_coarse,
            "entropy_coarsening_gap_abs" => entropy_gap,
            "bad_trace_normalization_residual" => bad_trace_normalization_residual,
            "bad_positive_min_AstarA" => bad_positive_min,
        ),
    )
end

qbasis(idx::Int) = [i == idx ? 1.0 : 0.0 for i in 1:4]
qreal(x::Float64) = [x, 0.0, 0.0, 0.0]
qzero() = zeros(Float64, 4)
qconj(q::AbstractVector{Float64}) = [q[1], -q[2], -q[3], -q[4]]
qnorm2(q::AbstractVector{Float64}) = sum(abs2, q)

function qmul(x::AbstractVector{Float64}, y::AbstractVector{Float64})
    a, b, c, d = x
    e, f, g, h = y
    [
        a * e - b * f - c * g - d * h,
        a * f + b * e + c * h - d * g,
        a * g - b * h + c * e + d * f,
        a * h + b * g - c * f + d * e,
    ]
end

function qmat_zero()
    zeros(Float64, 2, 2, 4)
end

function qmat_identity()
    out = qmat_zero()
    out[1, 1, :] .= qreal(1.0)
    out[2, 2, :] .= qreal(1.0)
    out
end

function qmat_z()
    out = qmat_zero()
    out[1, 1, :] .= qreal(1.0)
    out[2, 2, :] .= qreal(-1.0)
    out
end

function qmat_offdiag(q::AbstractVector{Float64})
    out = qmat_zero()
    out[1, 2, :] .= q
    out[2, 1, :] .= qconj(q)
    out
end

function qmat_mul(a::Array{Float64,3}, b::Array{Float64,3})
    out = qmat_zero()
    for i in 1:2, k in 1:2, j in 1:2
        out[i, k, :] .+= qmul(a[i, j, :], b[j, k, :])
    end
    out
end

function qmat_adj(a::Array{Float64,3})
    out = qmat_zero()
    for i in 1:2, j in 1:2
        out[i, j, :] .= qconj(a[j, i, :])
    end
    out
end

qmat_real_trace(a::Array{Float64,3}) = a[1, 1, 1] + a[2, 2, 1]
qmat_inner(a::Array{Float64,3}, b::Array{Float64,3}) = qmat_real_trace(qmat_mul(a, b))
qmat_residual(a::Array{Float64,3}, b::Array{Float64,3}) = norm(vec(a .- b))

function qmat_sample_matrices()
    samples = Array{Float64,3}[qmat_identity(), qmat_z()]
    for i in 1:4
        push!(samples, qmat_offdiag(qbasis(i)))
    end
    row = qmat_zero()
    row[1, 1, :] .= qreal(0.2)
    row[1, 2, :] .= [0.1, -0.4, 0.3, 0.2]
    row[2, 1, :] .= [-0.2, 0.5, -0.1, 0.4]
    row[2, 2, :] .= [0.6, -0.3, 0.2, -0.5]
    push!(samples, row)
    neg = qmat_zero()
    neg[1, 1, :] .= qreal(1.0)
    neg[1, 2, :] .= -1.0 .* qbasis(2)
    push!(samples, neg)
    samples
end

function qmat_density(a::Float64, q::Vector{Float64})
    out = qmat_zero()
    out[1, 1, :] .= qreal(a)
    out[2, 2, :] .= qreal(1.0 - a)
    out[1, 2, :] .= q
    out[2, 1, :] .= qconj(q)
    out
end

function omega_h(rho::Array{Float64,3}, x::Array{Float64,3})
    qmat_inner(rho, x)
end

function reconstruct_qhermitian(expectations::Vector{Float64}, probes::Vector{Array{Float64,3}})
    n = length(probes)
    gram = zeros(Float64, n, n)
    for i in 1:n, j in 1:n
        gram[i, j] = qmat_inner(probes[i], probes[j])
    end
    coeffs = gram \ expectations
    out = qmat_zero()
    for i in 1:n
        out .+= coeffs[i] .* probes[i]
    end
    out
end

function quaternionic_checks()
    probes = Array{Float64,3}[qmat_identity(), qmat_z()]
    for i in 1:4
        push!(probes, qmat_offdiag(qbasis(i)))
    end
    nonspanning = probes[1:3]

    q = [0.08, 0.05, -0.03, 0.04]
    rho = qmat_density(0.55, q)
    trace_residual = abs(qmat_real_trace(rho) - 1.0)
    hermitian_residual = qmat_residual(rho, qmat_adj(rho))
    determinant_margin = 0.55 * 0.45 - qnorm2(q)
    positivity_vals = [omega_h(rho, qmat_mul(qmat_adj(x), x)) for x in qmat_sample_matrices()]
    positivity_min = minimum(positivity_vals)

    expectations = [omega_h(rho, p) for p in probes]
    reconstructed = reconstruct_qhermitian(expectations, probes)
    reconstruction_residual = qmat_residual(reconstructed, rho)

    rho_plus = qmat_density(0.5, [0.0, 0.1, 0.0, 0.0])
    rho_minus = qmat_density(0.5, [0.0, -0.1, 0.0, 0.0])
    full_probe_distinct_gap = maximum(abs(omega_h(rho_plus, p) - omega_h(rho_minus, p)) for p in probes)
    nonspanning_collision_max_abs_diff = maximum(abs(omega_h(rho_plus, p) - omega_h(rho_minus, p)) for p in nonspanning)
    nonspanning_state_gap = qmat_residual(rho_plus, rho_minus)

    bad_rho = qmat_density(0.5, [0.0, 0.8, 0.0, 0.0])
    bad_positive_min = minimum(omega_h(bad_rho, qmat_mul(qmat_adj(x), x)) for x in qmat_sample_matrices())

    Dict{String,Any}(
        "state_valid" => trace_residual < TOL && hermitian_residual < TOL && determinant_margin > TOL && positivity_min >= -TOL,
        "spanning_separates" => reconstruction_residual < TOL && full_probe_distinct_gap > 1.0e-3,
        "nonspanning_collision" => nonspanning_collision_max_abs_diff < TOL && nonspanning_state_gap > 1.0e-3,
        "bad_controls_ok" => bad_positive_min < -1.0e-3,
        "numbers" => Dict{String,Any}(
            "trace_residual" => trace_residual,
            "hermitian_residual" => hermitian_residual,
            "determinant_margin" => determinant_margin,
            "positivity_min_XstarX" => positivity_min,
            "spanning_reconstruction_residual" => reconstruction_residual,
            "full_probe_distinct_gap" => full_probe_distinct_gap,
            "nonspanning_collision_max_abs_diff" => nonspanning_collision_max_abs_diff,
            "nonspanning_state_frobenius_gap" => nonspanning_state_gap,
            "bad_positive_min_XstarX" => bad_positive_min,
        ),
    )
end

function setprod!(table::Array{Float64,3}, a::Int, b::Int, c::Int, s::Float64)
    table[c + 1, a + 1, b + 1] = s
end

function add_identity!(table::Array{Float64,3}, dim::Int)
    for a in 0:(dim - 1)
        setprod!(table, 0, a, a, 1.0)
        setprod!(table, a, 0, a, 1.0)
    end
end

function octonion_table()
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

function obasis(dim::Int, idx::Int)
    v = zeros(Float64, dim)
    v[idx + 1] = 1.0
    v
end

function omul(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function oct_conj(x::AbstractVector{Float64})
    out = copy(collect(x))
    out[2:end] .*= -1.0
    out
end

function j3_zero()
    zeros(Float64, 3, 3, 8)
end

function j3_identity()
    out = j3_zero()
    for i in 1:3
        out[i, i, 1] = 1.0
    end
    out
end

function j3_from_coords(coords::AbstractVector{Float64})
    @assert length(coords) == 27
    matrix = j3_zero()
    for i in 1:3
        matrix[i, i, 1] = coords[i]
    end
    idx = 4
    for (i, j) in OFFDIAG_PAIRS
        v = collect(coords[idx:(idx + 7)])
        matrix[i, j, :] .= v
        matrix[j, i, :] .= oct_conj(v)
        idx += 8
    end
    matrix
end

function j3_coords_basis(idx0::Int)
    coords = zeros(Float64, 27)
    coords[idx0 + 1] = 1.0
    j3_from_coords(coords)
end

function j3_probe_coords(sample_idx::Int, side::Int)
    [((Float64(mod((sample_idx + 23) * (j + 11) * (side + 3) * 29 +
                   j^2 * 17 + sample_idx * 31 + side * 7, 113)) - 56.0) / 41.0) for j in 1:27]
end

function j3_matmul(table::Array{Float64,3}, a::Array{Float64,3}, b::Array{Float64,3})
    out = j3_zero()
    for i in 1:3, k in 1:3, j in 1:3
        out[i, k, :] .+= omul(table, a[i, j, :], b[j, k, :])
    end
    out
end

function jordan(table::Array{Float64,3}, a::Array{Float64,3}, b::Array{Float64,3})
    0.5 .* (j3_matmul(table, a, b) .+ j3_matmul(table, b, a))
end

function j3_trace(a::Array{Float64,3})
    sum(a[i, i, 1] for i in 1:3)
end

function j3_trace_square_expected(a::Array{Float64,3})
    total = 0.0
    for i in 1:3
        total += a[i, i, 1]^2
    end
    for (i, j) in OFFDIAG_PAIRS
        total += 2.0 * sum(abs2, a[i, j, :])
    end
    total
end

function j3_probe_family()
    matrices = Array{Float64,3}[]
    for idx0 in 0:26
        push!(matrices, j3_coords_basis(idx0))
    end
    for sample_idx in 1:STRUCTURE_PROBE_COUNT
        push!(matrices, j3_from_coords(j3_probe_coords(sample_idx, 5)))
    end
    matrices
end

function j3_state_checks()
    table = octonion_table()
    probes = j3_probe_family()
    identity = j3_identity()
    omega(a::Array{Float64,3}) = j3_trace(a) / 3.0
    normalization_residual = abs(omega(identity) - 1.0)
    min_square = Inf
    max_trace_square_residual = 0.0
    for a in probes
        square = jordan(table, a, a)
        value = omega(square)
        min_square = min(min_square, value)
        max_trace_square_residual = max(max_trace_square_residual, abs(j3_trace(square) - j3_trace_square_expected(a)))
    end
    p = j3_zero()
    u = obasis(8, 1)
    p[1, 1, 1] = 0.5
    p[2, 2, 1] = 0.5
    p[1, 2, :] .= -0.5 .* u
    p[2, 1, :] .= oct_conj(p[1, 2, :])
    rank1_idempotent_residual = norm(vec(jordan(table, p, p) .- p))
    bad_normalization_residual = abs((j3_trace(identity) / 2.0) - 1.0)
    Dict{String,Any}(
        "state_valid" => normalization_residual < TOL && min_square >= -TOL && max_trace_square_residual < TOL,
        "bad_controls_ok" => bad_normalization_residual > 1.0e-3,
        "numbers" => Dict{String,Any}(
            "identity_normalization_residual" => normalization_residual,
            "positivity_min_square" => min_square,
            "trace_square_max_residual" => max_trace_square_residual,
            "rank1_idempotent_residual" => rank1_idempotent_residual,
            "bad_normalization_residual" => bad_normalization_residual,
        ),
    )
end

function parity_against_peer(result::Dict{String,Any}, peer_path::String)
    if !isfile(peer_path)
        return Dict{String,Any}(
            "peer_result_path" => peer_path,
            "status" => "pending_peer_backend",
            "shared_scalar_rows" => [],
            "max_diff_key" => nothing,
            "parity_max_diff" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [Dict{String,Any}("missing" => peer_path)],
            "boolean_mismatches" => [],
            "missing_keys" => [],
            "stop_condition_fired" => true,
        )
    end
    peer = JSON.parsefile(peer_path)
    rows = Vector{Dict{String,Any}}()
    max_diff = 0.0
    max_diff_key = nothing
    strict = Vector{Dict{String,Any}}()
    missing = String[]
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        jv = Float64(value)
        pv = Float64(peer["shared_scalars"][key])
        diff = abs(jv - pv)
        if diff > max_diff
            max_diff = diff
            max_diff_key = key
        end
        row = Dict{String,Any}("key" => key, "julia" => jv, "jax" => pv, "abs_diff" => diff)
        push!(rows, row)
        diff > STRICT_STOP_TOL && push!(strict, row)
    end
    mismatches = Vector{Dict{String,Any}}()
    for (key, value) in result["shared_booleans"]
        if !haskey(peer["shared_booleans"], key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer["shared_booleans"][key])
            push!(mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => Bool(peer["shared_booleans"][key])))
        end
    end
    Dict{String,Any}(
        "peer_result_path" => peer_path,
        "status" => "compared",
        "shared_scalar_rows" => rows,
        "max_diff_key" => max_diff_key,
        "parity_max_diff" => max_diff,
        "within_1e_9" => max_diff < TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function prefix_numbers(prefix::String, numbers::Dict{String,Any})
    Dict{String,Any}("$prefix.$key" => value for (key, value) in numbers)
end

function build_result()
    m2c = m2c_checks()
    h = quaternionic_checks()
    j3o = j3_state_checks()

    verdicts = Dict{String,Any}(
        "state_on_algebra_valid_M2C" => Bool(m2c["state_valid"]),
        "state_on_algebra_valid_H" => Bool(h["state_valid"]),
        "state_on_algebra_valid_J3O" => Bool(j3o["state_valid"]),
        "state_on_algebra_valid_all" => Bool(m2c["state_valid"]) && Bool(h["state_valid"]) && Bool(j3o["state_valid"]),
        "probe_relative_identity" => Bool(m2c["spanning_separates"]) && Bool(m2c["nonspanning_collision"]) &&
            Bool(h["spanning_separates"]) && Bool(h["nonspanning_collision"]),
        "entropy_is_readout" => Bool(m2c["entropy_is_readout"]),
    )
    controls = Dict{String,Any}(
        "M2C_bad_functionals_fail" => Bool(m2c["bad_controls_ok"]),
        "H_bad_functional_fails" => Bool(h["bad_controls_ok"]),
        "J3O_bad_normalization_fails" => Bool(j3o["bad_controls_ok"]),
    )
    controls["control_miswired"] = !(controls["M2C_bad_functionals_fail"] &&
                                     controls["H_bad_functional_fails"] &&
                                     controls["J3O_bad_normalization_fails"])
    shared_scalars = merge(
        prefix_numbers("M2C", m2c["numbers"]),
        prefix_numbers("H", h["numbers"]),
        prefix_numbers("J3O", j3o["numbers"]),
    )
    shared_booleans = Dict{String,Any}()
    for (key, value) in verdicts
        shared_booleans["verdict.$key"] = value
    end
    for (key, value) in controls
        isa(value, Bool) && (shared_booleans["control.$key"] = value)
    end
    all_verdicts = all(Bool(v) for v in values(verdicts))

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia_full_sim",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "Finite state-on-algebra/probe-equivalence diagnostic only; no basin, admission, engine, Axis0, bridge, gravity, or manifold-closure claim.",
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "state_probe_equivalence_probe",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "question" => "Can state-on-algebra be computed as a positive normalized probe-functional across M2(C), quaternionic 2x2 observables, and J3(O), with identity only relative to the probe family?",
        "tool_manifest" => Dict{String,Any}(
            "Julia" => "load_bearing complex, quaternionic, and octonionic finite algebra construction",
            "LinearAlgebra" => "load_bearing eigenvalue, norm, reconstruction, and entropy computations",
            "JSON" => "supportive result serialization",
        ),
        "tool_integration_depth" => Dict{String,Any}(
            "Julia" => "load_bearing",
            "LinearAlgebra" => "load_bearing",
            "JSON" => "supportive",
        ),
        "verdicts" => verdicts,
        "controls" => controls,
        "numbers" => shared_scalars,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "algebras" => Dict{String,Any}(
            "M2C" => Dict("basis" => "Hermitian Pauli probe basis I,X,Y,Z", "state" => "density matrix rho"),
            "H" => Dict("basis" => "2x2 quaternionic Hermitian basis I,Z,offdiag{1,i,j,k}", "state" => "positive trace-one quaternionic Hermitian matrix"),
            "J3O" => Dict("basis" => "3x3 octonionic Hermitian Jordan algebra coordinates", "state" => "normalized trace functional omega(A)=Tr(A)/3"),
        ),
        "plain_sentence" => "A state can be computed as a positive normalized functional on M2(C), quaternionic 2x2 observables, and J3(O); probe identity changes when the probe family is coarsened, and entropy is only a downstream readout of rho.",
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["stop_condition_fired"] = controls["control_miswired"] || !all_verdicts || result["parity"]["stop_condition_fired"]
    result
end

function print_summary(result::Dict{String,Any})
    s = result["shared_scalars"]
    println("state_on_algebra_probe_equivalence - Julia full sim")
    println("classification: ", result["classification"], " | promotion_allowed: ", result["promotion_allowed"], " | formal_admission_allowed: ", result["formal_admission_allowed"])
    println("state_on_algebra_valid_M2C=", result["verdicts"]["state_on_algebra_valid_M2C"],
        " min_eigen=", s["M2C.min_eigenvalue"],
        " positivity_min=", s["M2C.positivity_min_AstarA"])
    println("state_on_algebra_valid_H=", result["verdicts"]["state_on_algebra_valid_H"],
        " determinant_margin=", s["H.determinant_margin"],
        " positivity_min=", s["H.positivity_min_XstarX"])
    println("state_on_algebra_valid_J3O=", result["verdicts"]["state_on_algebra_valid_J3O"],
        " positivity_min_square=", s["J3O.positivity_min_square"],
        " trace_square_residual=", s["J3O.trace_square_max_residual"])
    println("probe_relative_identity=", result["verdicts"]["probe_relative_identity"],
        " M2C_nonspan_collision=", s["M2C.nonspanning_collision_max_abs_diff"],
        " H_nonspan_collision=", s["H.nonspanning_collision_max_abs_diff"])
    println("entropy_is_readout=", result["verdicts"]["entropy_is_readout"],
        " entropy_full=", s["M2C.entropy_full"],
        " entropy_coarse=", s["M2C.entropy_coarse"],
        " gap=", s["M2C.entropy_coarsening_gap_abs"])
    println("controls=", JSON.json(result["controls"]))
    println("parity_status=", result["parity"]["status"],
        " parity_max_diff=", result["parity"]["parity_max_diff"],
        " within_1e-9=", result["parity"]["within_1e_9"])
    println(result["plain_sentence"])
    println("wrote: ", result["result_path"])
end

result = build_result()
open(RESULT_PATH, "w") do io
    JSON.print(io, result, 2)
    write(io, "\n")
end
print_summary(result)

if result["stop_condition_fired"]
    println("STOP: state_on_algebra_probe_equivalence control/verdict/parity stop condition fired.")
    exit(2)
end
