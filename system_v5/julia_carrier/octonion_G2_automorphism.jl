#!/usr/bin/env julia
# object_id: octonion_G2_automorphism
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: Finite octonion derivation/automorphism diagnostic only. No
# basin, admission, engine, Axis0, bridge, gravity, or formal-admission claim.

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "octonion_G2_automorphism"
const RESULT_PATH = joinpath(@__DIR__, "octonion_G2_automorphism_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "octonion_G2_automorphism_jax_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const DIM = 8

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
end

function octonion_table()
    table = zeros(Float64, DIM, DIM, DIM)
    add_identity!(table, DIM)
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

function basis(dim::Int, idx0::Int)
    v = zeros(Float64, dim)
    v[idx0 + 1] = 1.0
    v
end

function multiply(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    out = zeros(Float64, DIM)
    @inbounds for c in 1:DIM, a in 1:DIM, b in 1:DIM
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

varidx(row::Int, col::Int) = row + (col - 1) * DIM

function derivation_constraint_matrix(table::Array{Float64,3})
    rows = DIM * DIM * DIM
    cols = DIM * DIM
    mat = zeros(Float64, rows, cols)
    row = 0
    for a in 1:DIM, b in 1:DIM, c in 1:DIM
        row += 1
        for k in 1:DIM
            mat[row, varidx(c, k)] += table[k, a, b]
            mat[row, varidx(k, a)] -= table[c, k, b]
            mat[row, varidx(k, b)] -= table[c, a, k]
        end
    end
    mat
end

function nullspace_data(mat::Matrix{Float64})
    decomp = svd(mat)
    rank_tol = max(size(mat)...) * eps(Float64) * maximum(decomp.S) * 100.0
    rank = count(>(rank_tol), decomp.S)
    v = Matrix(decomp.Vt')
    basis = v[:, (rank + 1):end]
    rank, rank_tol, basis, decomp.S
end

function derivation_residual(table::Array{Float64,3}, d::Matrix{Float64})
    max_seen = 0.0
    for a0 in 0:(DIM - 1), b0 in 0:(DIM - 1)
        ea = basis(DIM, a0)
        eb = basis(DIM, b0)
        left = d * multiply(table, ea, eb)
        right = multiply(table, d * ea, eb) + multiply(table, ea, d * eb)
        max_seen = max(max_seen, norm(left - right))
    end
    max_seen
end

function automorphism_residual(table::Array{Float64,3}, phi::Matrix{Float64})
    max_seen = 0.0
    for a0 in 0:(DIM - 1), b0 in 0:(DIM - 1)
        ea = basis(DIM, a0)
        eb = basis(DIM, b0)
        left = phi * multiply(table, ea, eb)
        right = multiply(table, phi * ea, phi * eb)
        max_seen = max(max_seen, norm(left - right))
    end
    max_seen
end

function deterministic_tracefree_map()
    d = zeros(Float64, DIM, DIM)
    for r in 2:DIM, c in 2:DIM
        raw = mod((r + 5) * (c + 11) * 37 + r^2 * 17 + c * 19, 101)
        d[r, c] = (Float64(raw) - 50.0) / 31.0
    end
    tr = sum(d[i, i] for i in 2:DIM) / 7.0
    for i in 2:DIM
        d[i, i] -= tr
    end
    d
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

function build_result()
    table = octonion_table()
    constraint = derivation_constraint_matrix(table)
    rank, rank_tol, ns, singular_values = nullspace_data(constraint)
    der_dim = size(ns, 2)
    d = reshape(ns[:, 1], DIM, DIM)
    d_residual = derivation_residual(table, d)
    phi = exp(0.375 .* d)
    phi_residual = automorphism_residual(table, phi)

    control_d = deterministic_tracefree_map()
    control_residual = derivation_residual(table, control_d)

    verdicts = Dict{String,Any}(
        "der_O_dim_is_14" => der_dim == 14,
        "automorphism_preserves_product" => phi_residual < TOL,
        "automorphism_invertible" => abs(det(phi)) > TOL,
    )
    controls = Dict{String,Any}(
        "random_tracefree_linear_map_not_derivation" => control_residual > TOL,
        "derivation_identity_action_zero" => norm(d * basis(DIM, 0)) < TOL,
        "derivation_tracefree" => abs(tr(d)) < TOL,
    )
    controls["control_miswired"] = !(controls["random_tracefree_linear_map_not_derivation"] &&
        controls["derivation_identity_action_zero"] && controls["derivation_tracefree"])

    shared_scalars = Dict{String,Any}(
        "constraint_rows" => size(constraint, 1),
        "constraint_cols" => size(constraint, 2),
        "constraint_rank" => rank,
        "der_O_dim" => der_dim,
        "rank_tol" => rank_tol,
        "smallest_nonzero_singular_value" => singular_values[rank],
        "largest_zero_singular_value" => singular_values[rank + 1],
        "derivation_residual" => d_residual,
        "derivation_norm" => norm(d),
        "derivation_trace_abs" => abs(tr(d)),
        "derivation_identity_action_norm" => norm(d * basis(DIM, 0)),
        "automorphism_product_residual" => phi_residual,
        "automorphism_det_abs" => abs(det(phi)),
        "random_tracefree_derivation_residual" => control_residual,
        "random_trace_abs" => abs(tr(control_d)),
    )
    shared_booleans = Dict{String,Any}()
    for (key, value) in verdicts
        shared_booleans["verdict.$key"] = value
    end
    for (key, value) in controls
        shared_booleans["control.$key"] = value
    end

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
        "claim_ceiling" => "Finite G2=Der(O) diagnostic only; no basin, admission, engine, Axis0, bridge, gravity, or formal-admission claim.",
        "sim_execution_kind" => "classical",
        "sim_class" => "octonion_exceptional_structure_probe",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "tool_manifest" => Dict{String,Any}(
            "Julia" => "load-bearing construction of the octonion multiplication table, derivation constraints, and automorphism residuals",
            "LinearAlgebra" => "load-bearing SVD nullspace, matrix exponential, determinant, and residual norms",
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
        "witness" => Dict{String,Any}(
            "automorphism_delta_norm" => norm(phi - Matrix{Float64}(I, DIM, DIM)),
            "derivation_matrix" => d,
            "automorphism_matrix" => phi,
            "control_tracefree_matrix" => control_d,
        ),
        "plain_sentence" => "The octonion multiplication table cuts the 64-dimensional linear-map space down to a 14-dimensional derivation algebra, and exponentiating one computed derivation gives a concrete product-preserving automorphism.",
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["stop_condition_fired"] = controls["control_miswired"] ||
        !verdicts["der_O_dim_is_14"] ||
        !verdicts["automorphism_preserves_product"] ||
        !verdicts["automorphism_invertible"] ||
        result["parity"]["stop_condition_fired"]
    result
end

function print_summary(result::Dict{String,Any})
    n = result["numbers"]
    println("octonion_G2_automorphism - Julia full sim")
    println("der_O_dim_is_14=", result["verdicts"]["der_O_dim_is_14"],
        " der_O_dim=", n["der_O_dim"],
        " constraint_rank=", n["constraint_rank"])
    println("automorphism_preserves_product=", result["verdicts"]["automorphism_preserves_product"],
        " automorphism_product_residual=", n["automorphism_product_residual"],
        " det_abs=", n["automorphism_det_abs"])
    println("random_tracefree_linear_map_not_derivation=", result["controls"]["random_tracefree_linear_map_not_derivation"],
        " random_tracefree_derivation_residual=", n["random_tracefree_derivation_residual"])
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
    println("STOP: octonion_G2_automorphism control/verdict/parity condition failed.")
    exit(2)
end
