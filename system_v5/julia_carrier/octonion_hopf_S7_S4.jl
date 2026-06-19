#!/usr/bin/env julia
# object_id: octonion_hopf_S7_S4
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: Finite Hopf-rung diagnostic only. No basin, admission,
# engine, Axis0, bridge, gravity, or formal-admission claim.

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "octonion_hopf_S7_S4"
const RESULT_PATH = joinpath(@__DIR__, "octonion_hopf_S7_S4_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "octonion_hopf_S7_S4_jax_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const SAMPLE_COUNT = 96

const FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

function probe_vector(dim::Int, sample_idx::Int, side::Int)
    [((Float64(mod((sample_idx + 17) * (j + 3) * (side + 5) * 37 +
                   (j + 1)^2 * 19 + sample_idx * 11 + side * 13, 101)) - 50.0) / 37.0) for j in 1:dim]
end

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

qconj(q::AbstractVector{Float64}) = [q[1], -q[2], -q[3], -q[4]]

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

function omul(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    out = zeros(Float64, 8)
    @inbounds for c in 1:8, a in 1:8, b in 1:8
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

oconj(o::AbstractVector{Float64}) = [o[1], -o[2], -o[3], -o[4], -o[5], -o[6], -o[7], -o[8]]
sqnorm(x::AbstractVector{Float64}) = sum(abs2, x)
linf(x::AbstractVector, y::AbstractVector) = maximum(abs.(x .- y))

function h_hopf(a::AbstractVector{Float64}, b::AbstractVector{Float64})
    vcat(2.0 .* qmul(a, qconj(b)), [sqnorm(a) - sqnorm(b)])
end

function o_hopf(table::Array{Float64,3}, a::AbstractVector{Float64}, b::AbstractVector{Float64})
    vcat(2.0 .* omul(table, a, oconj(b)), [sqnorm(a) - sqnorm(b)])
end

function unit_h_pairs()
    pairs = Vector{Tuple{Vector{Float64},Vector{Float64}}}()
    push!(pairs, ([1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]))
    push!(pairs, ([0.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]))
    for sample_idx in 1:SAMPLE_COUNT
        v = probe_vector(8, sample_idx, 19)
        v ./= norm(v)
        push!(pairs, (v[1:4], v[5:8]))
    end
    pairs
end

function unit_o_pairs()
    pairs = Vector{Tuple{Vector{Float64},Vector{Float64}}}()
    push!(pairs, ([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], zeros(Float64, 8)))
    push!(pairs, (zeros(Float64, 8), [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]))
    for sample_idx in 1:SAMPLE_COUNT
        v = probe_vector(16, sample_idx, 23)
        v ./= norm(v)
        push!(pairs, (v[1:8], v[9:16]))
    end
    pairs
end

function unit_quaternion_samples()
    samples = Vector{Vector{Float64}}()
    append!(samples, [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ])
    for sample_idx in 1:16
        v = probe_vector(4, sample_idx, 29)
        push!(samples, v ./ norm(v))
    end
    samples
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
    hpairs = unit_h_pairs()
    opairs = unit_o_pairs()
    units = unit_quaternion_samples()

    h_input_unit_error = 0.0
    h_s4_landing_error = 0.0
    h_fiber_residual = 0.0
    for (a, b) in hpairs
        out = h_hopf(a, b)
        h_input_unit_error = max(h_input_unit_error, abs(sqnorm(a) + sqnorm(b) - 1.0))
        h_s4_landing_error = max(h_s4_landing_error, abs(norm(out) - 1.0))
        for u in units
            out_u = h_hopf(qmul(a, u), qmul(b, u))
            h_fiber_residual = max(h_fiber_residual, linf(out, out_u))
        end
    end

    nonunit_a, nonunit_b = hpairs[end]
    nonunit_out = h_hopf(1.7 .* nonunit_a, 1.7 .* nonunit_b)
    nonunit_output_norm = norm(nonunit_out)
    nonunit_s4_norm_error = abs(nonunit_output_norm - 1.0)

    o_input_unit_error = 0.0
    o_s8_landing_error = 0.0
    for (a, b) in opairs
        out = o_hopf(table, a, b)
        o_input_unit_error = max(o_input_unit_error, abs(sqnorm(a) + sqnorm(b) - 1.0))
        o_s8_landing_error = max(o_s8_landing_error, abs(norm(out) - 1.0))
    end

    verdicts = Dict{String,Any}(
        "hopf_S7_S4_lands_on_S4" => h_s4_landing_error < TOL,
        "fiber_S3_invariant" => h_fiber_residual < TOL,
        "octonion_S15_S8_base_lands_on_S8" => o_s8_landing_error < TOL,
    )
    controls = Dict{String,Any}(
        "unit_H_pair_inputs_ok" => h_input_unit_error < TOL,
        "unit_O_pair_inputs_ok" => o_input_unit_error < TOL,
        "nonunit_H_pair_off_S4_control_ok" => nonunit_s4_norm_error > 0.5,
    )
    controls["control_miswired"] = !(controls["unit_H_pair_inputs_ok"] &&
        controls["unit_O_pair_inputs_ok"] && controls["nonunit_H_pair_off_S4_control_ok"])

    shared_scalars = Dict{String,Any}(
        "H_pair_sample_count" => length(hpairs),
        "H_fiber_unit_sample_count" => length(units),
        "H_input_unit_error" => h_input_unit_error,
        "H_S4_landing_max_norm_error" => h_s4_landing_error,
        "H_S3_fiber_invariance_max_linf" => h_fiber_residual,
        "nonunit_H_output_norm" => nonunit_output_norm,
        "nonunit_H_S4_norm_error" => nonunit_s4_norm_error,
        "O_pair_sample_count" => length(opairs),
        "O_input_unit_error" => o_input_unit_error,
        "O_S8_base_landing_max_norm_error" => o_s8_landing_error,
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
        "claim_ceiling" => "Finite Hopf-rung diagnostic only; no basin, admission, engine, Axis0, bridge, gravity, or formal-admission claim.",
        "sim_execution_kind" => "classical",
        "sim_class" => "hopf_geometry_rung_probe",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "rung_note" => "Standard Hopf fibrations: R:S1->S0, C:S3->S2, H:S7->S4, O:S15->S8. This sim verifies the H-Hopf S7->S4 map and only base-landing for the O-Hopf S15->S8 map.",
        "tool_manifest" => Dict{String,Any}(
            "Julia" => "load-bearing quaternion and octonion pair Hopf computations",
            "LinearAlgebra" => "load-bearing S4/S8 norms and fiber residuals",
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
        "plain_sentence" => "The quaternion Hopf map sends unit H-pairs on S7 to S4 and is invariant under right multiplication by unit quaternions, while the octonion-pair rung lands on S8 without making a fiber claim here.",
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["stop_condition_fired"] = controls["control_miswired"] ||
        !verdicts["hopf_S7_S4_lands_on_S4"] ||
        !verdicts["fiber_S3_invariant"] ||
        !verdicts["octonion_S15_S8_base_lands_on_S8"] ||
        result["parity"]["stop_condition_fired"]
    result
end

function print_summary(result::Dict{String,Any})
    n = result["numbers"]
    println("octonion_hopf_S7_S4 - Julia full sim")
    println("hopf_S7_S4_lands_on_S4=", result["verdicts"]["hopf_S7_S4_lands_on_S4"],
        " H_S4_landing_max_norm_error=", n["H_S4_landing_max_norm_error"])
    println("fiber_S3_invariant=", result["verdicts"]["fiber_S3_invariant"],
        " H_S3_fiber_invariance_max_linf=", n["H_S3_fiber_invariance_max_linf"])
    println("octonion_S15_S8_base_lands_on_S8=", result["verdicts"]["octonion_S15_S8_base_lands_on_S8"],
        " O_S8_base_landing_max_norm_error=", n["O_S8_base_landing_max_norm_error"])
    println("nonunit_H_pair_off_S4_control_ok=", result["controls"]["nonunit_H_pair_off_S4_control_ok"],
        " nonunit_H_output_norm=", n["nonunit_H_output_norm"])
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
    println("STOP: octonion_hopf_S7_S4 control/verdict/parity condition failed.")
    exit(2)
end
