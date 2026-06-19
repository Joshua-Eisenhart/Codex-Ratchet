#!/usr/bin/env julia
# object_id: J3O_spectral_OP2
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: Finite J3(O) spectral/OP2 diagnostic only. No basin,
# admission, engine, Axis0, bridge, gravity, or formal-admission claim.

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "J3O_spectral_OP2"
const RESULT_PATH = joinpath(@__DIR__, "J3O_spectral_OP2_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "J3O_spectral_OP2_jax_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const SAMPLE_COUNT = 8
const OFFDIAG_PAIRS = [(1, 2), (1, 3), (2, 3)]

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

function basis(dim::Int, idx0::Int)
    v = zeros(Float64, dim)
    v[idx0 + 1] = 1.0
    v
end

function multiply(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    out = zeros(Float64, 8)
    @inbounds for c in 1:8, a in 1:8, b in 1:8
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
    m = j3_zero()
    for i in 1:3
        m[i, i, 1] = 1.0
    end
    m
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

function j3_probe_coords(sample_idx::Int, side::Int)
    [0.25 * ((Float64(mod((sample_idx + 23) * (j + 11) * (side + 3) * 29 +
                          j^2 * 17 + sample_idx * 31 + side * 7, 113)) - 56.0) / 41.0) for j in 1:27]
end

function j3_matmul(table::Array{Float64,3}, a::Array{Float64,3}, b::Array{Float64,3})
    out = j3_zero()
    for i in 1:3, k in 1:3, j in 1:3
        out[i, k, :] .+= multiply(table, a[i, j, :], b[j, k, :])
    end
    out
end

function jordan(table::Array{Float64,3}, a::Array{Float64,3}, b::Array{Float64,3})
    0.5 .* (j3_matmul(table, a, b) .+ j3_matmul(table, b, a))
end

function j3_trace(a::Array{Float64,3})
    sum(a[i, i, 1] for i in 1:3)
end

function j3_residual(a::Array{Float64,3}, b::Array{Float64,3})
    norm(vec(a .- b))
end

function spectral_data(table::Array{Float64,3}, a::Array{Float64,3})
    a2 = jordan(table, a, a)
    a3 = jordan(table, a2, a)
    t = j3_trace(a)
    tr2 = j3_trace(a2)
    tr3 = j3_trace(a3)
    sigma2 = 0.5 * (t^2 - tr2)
    detv = (t^3 - 3.0 * t * tr2 + 2.0 * tr3) / 6.0
    Dict{String,Any}(
        "trace" => t,
        "trace_square" => tr2,
        "trace_cube" => tr3,
        "sigma2" => sigma2,
        "determinant" => detv,
        "A2" => a2,
        "A3" => a3,
    )
end

function characteristic_residual(table::Array{Float64,3}, a::Array{Float64,3})
    spec = spectral_data(table, a)
    ident = j3_identity()
    lhs = spec["A3"] .- spec["trace"] .* spec["A2"] .+ spec["sigma2"] .* a .- spec["determinant"] .* ident
    norm(vec(lhs)), spec
end

function primitive_idempotent(table::Array{Float64,3})
    u = basis(8, 1)
    p = j3_zero()
    p[1, 1, 1] = 0.5
    p[2, 2, 1] = 0.5
    p[1, 2, :] .= -0.5 .* u
    p[2, 1, :] .= oct_conj(p[1, 2, :])
    p
end

function rank2_idempotent()
    q = j3_zero()
    q[1, 1, 1] = 1.0
    q[2, 2, 1] = 1.0
    q
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
    max_ch_residual = 0.0
    representative_spec = nothing
    for sample_idx in 1:SAMPLE_COUNT
        a = j3_from_coords(j3_probe_coords(sample_idx, 31))
        residual, spec = characteristic_residual(table, a)
        max_ch_residual = max(max_ch_residual, residual)
        sample_idx == 1 && (representative_spec = spec)
    end

    p = primitive_idempotent(table)
    p2 = jordan(table, p, p)
    p_spec = spectral_data(table, p)
    p_idempotent_residual = j3_residual(p2, p)
    p_trace_residual = abs(p_spec["trace"] - 1.0)
    p_sigma2_abs = abs(p_spec["sigma2"])
    p_det_abs = abs(p_spec["determinant"])

    q = rank2_idempotent()
    q2 = jordan(table, q, q)
    q_spec = spectral_data(table, q)
    q_idempotent_residual = j3_residual(q2, q)
    q_not_pure = q_idempotent_residual < TOL && (abs(q_spec["trace"] - 1.0) > TOL || abs(q_spec["sigma2"]) > TOL)

    verdicts = Dict{String,Any}(
        "jordan_cubic_identity_holds" => max_ch_residual < TOL,
        "primitive_idempotent_is_pure_state" => p_idempotent_residual < TOL && p_trace_residual < TOL && p_sigma2_abs < TOL && p_det_abs < TOL,
    )
    controls = Dict{String,Any}(
        "rank2_idempotent_not_primitive_control_ok" => q_not_pure,
        "rank2_idempotent_trace_is_2" => abs(q_spec["trace"] - 2.0) < TOL,
        "rank2_idempotent_sigma2_nonzero" => abs(q_spec["sigma2"] - 1.0) < TOL,
    )
    controls["control_miswired"] = !(controls["rank2_idempotent_not_primitive_control_ok"] &&
        controls["rank2_idempotent_trace_is_2"] && controls["rank2_idempotent_sigma2_nonzero"])

    shared_scalars = Dict{String,Any}(
        "J3O_real_dim" => size(p, 1) + binomial(size(p, 1), 2) * size(p, 3),
        "sample_count" => SAMPLE_COUNT,
        "jordan_cubic_identity_max_residual" => max_ch_residual,
        "representative_trace" => representative_spec["trace"],
        "representative_sigma2" => representative_spec["sigma2"],
        "representative_determinant" => representative_spec["determinant"],
        "primitive_idempotent_residual" => p_idempotent_residual,
        "primitive_trace" => p_spec["trace"],
        "primitive_trace_residual" => p_trace_residual,
        "primitive_sigma2_abs" => p_sigma2_abs,
        "primitive_det_abs" => p_det_abs,
        "rank2_idempotent_residual" => q_idempotent_residual,
        "rank2_trace" => q_spec["trace"],
        "rank2_sigma2" => q_spec["sigma2"],
        "rank2_det_abs" => abs(q_spec["determinant"]),
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
        "claim_ceiling" => "Finite J3(O) spectral/OP2 diagnostic only; no basin, admission, engine, Axis0, bridge, gravity, or formal-admission claim.",
        "sim_execution_kind" => "classical",
        "sim_class" => "exceptional_jordan_spectral_probe",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "tool_manifest" => Dict{String,Any}(
            "Julia" => "load-bearing J3(O) Jordan product, spectral invariants, and idempotent checks",
            "LinearAlgebra" => "load-bearing residual norms for cubic identity and idempotence",
            "JSON" => "supportive result serialization",
        ),
        "tool_integration_depth" => Dict{String,Any}(
            "Julia" => "load_bearing",
            "LinearAlgebra" => "load_bearing",
            "JSON" => "supportive",
        ),
        "spectral_formula" => Dict{String,Any}(
            "trace" => "T(A)",
            "sigma2" => "(T(A)^2 - T(A^2))/2",
            "determinant" => "(T(A)^3 - 3*T(A)*T(A^2) + 2*T(A^3))/6",
            "powers" => "Jordan powers with A^2=A∘A and A^3=A^2∘A",
        ),
        "verdicts" => verdicts,
        "controls" => controls,
        "numbers" => shared_scalars,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "plain_sentence" => "The finite J3(O) Jordan product satisfies the rank-3 cubic identity on deterministic random elements, and a primitive trace-one idempotent behaves as an OP2 pure-state witness while a trace-two idempotent control is not primitive.",
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["stop_condition_fired"] = controls["control_miswired"] ||
        !verdicts["jordan_cubic_identity_holds"] ||
        !verdicts["primitive_idempotent_is_pure_state"] ||
        result["parity"]["stop_condition_fired"]
    result
end

function print_summary(result::Dict{String,Any})
    n = result["numbers"]
    println("J3O_spectral_OP2 - Julia full sim")
    println("jordan_cubic_identity_holds=", result["verdicts"]["jordan_cubic_identity_holds"],
        " jordan_cubic_identity_max_residual=", n["jordan_cubic_identity_max_residual"])
    println("primitive_idempotent_is_pure_state=", result["verdicts"]["primitive_idempotent_is_pure_state"],
        " primitive_idempotent_residual=", n["primitive_idempotent_residual"],
        " primitive_trace=", n["primitive_trace"],
        " primitive_sigma2_abs=", n["primitive_sigma2_abs"],
        " primitive_det_abs=", n["primitive_det_abs"])
    println("rank2_idempotent_not_primitive_control_ok=", result["controls"]["rank2_idempotent_not_primitive_control_ok"],
        " rank2_trace=", n["rank2_trace"],
        " rank2_sigma2=", n["rank2_sigma2"],
        " rank2_det_abs=", n["rank2_det_abs"])
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
    println("STOP: J3O_spectral_OP2 control/verdict/parity condition failed.")
    exit(2)
end
