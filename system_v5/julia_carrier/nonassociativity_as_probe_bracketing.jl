#!/usr/bin/env julia
# object_id: nonassociativity_as_probe_bracketing
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: Finite bracketing/probe diagnostic only. No basin,
# admission, engine, Axis0, bridge, gravity, or formal-admission claim.

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "nonassociativity_as_probe_bracketing"
const RESULT_PATH = joinpath(@__DIR__, "nonassociativity_as_probe_bracketing_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "nonassociativity_as_probe_bracketing_jax_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const SAMPLE_COUNT = 64

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

function probe_vector(dim::Int, sample_idx::Int, side::Int)
    [((Float64(mod((sample_idx + 17) * (j + 3) * (side + 5) * 37 +
                   (j + 1)^2 * 19 + sample_idx * 11 + side * 13, 101)) - 50.0) / 37.0) for j in 1:dim]
end

function multiply(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function conj_alg(x::AbstractVector{Float64})
    out = copy(collect(x))
    out[2:end] .*= -1.0
    out
end

function associator(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64}, z::AbstractVector{Float64})
    multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))
end

function probe_readout(table::Array{Float64,3}, m::AbstractVector{Float64}, v::AbstractVector{Float64})
    multiply(table, conj_alg(m), v)[1]
end

function probe_metrics(table::Array{Float64,3}, assoc::AbstractVector{Float64})
    dim = size(table, 1)
    values = [probe_readout(table, basis(dim, idx0), assoc) for idx0 in 0:(dim - 1)]
    basis_reconstructed_norm = sqrt(sum(abs2, values))
    assoc_norm = norm(assoc)
    basis_max = maximum(abs.(values))
    best_idx0 = argmax(abs.(values)) - 1
    optimal_value = assoc_norm > TOL ? abs(probe_readout(table, assoc ./ assoc_norm, assoc)) : 0.0
    Dict{String,Any}(
        "assoc_norm" => assoc_norm,
        "basis_max_probe_abs" => basis_max,
        "basis_reconstructed_norm" => basis_reconstructed_norm,
        "basis_reconstruction_error" => abs(basis_reconstructed_norm - assoc_norm),
        "best_basis_probe_index0" => best_idx0,
        "optimal_unit_probe_abs" => optimal_value,
        "optimal_unit_probe_norm_error" => abs(optimal_value - assoc_norm),
    )
end

function analyze_table(name::String, table::Array{Float64,3})
    dim = size(table, 1)
    max_assoc_norm = 0.0
    max_basis_probe = 0.0
    max_optimal_probe = 0.0
    max_basis_reconstruction_error = 0.0
    max_optimal_probe_norm_error = 0.0
    witness = Dict{String,Any}("kind" => "none")
    for sample_idx in 1:SAMPLE_COUNT
        x = probe_vector(dim, sample_idx, 3)
        y = probe_vector(dim, sample_idx, 5)
        z = probe_vector(dim, sample_idx, 7)
        assoc = associator(table, x, y, z)
        metrics = probe_metrics(table, assoc)
        if metrics["assoc_norm"] > max_assoc_norm
            max_assoc_norm = metrics["assoc_norm"]
            witness = Dict{String,Any}(
                "sample_idx" => sample_idx,
                "assoc_norm" => metrics["assoc_norm"],
                "best_basis_probe_index0" => metrics["best_basis_probe_index0"],
                "basis_max_probe_abs" => metrics["basis_max_probe_abs"],
                "optimal_unit_probe_abs" => metrics["optimal_unit_probe_abs"],
            )
        end
        max_basis_probe = max(max_basis_probe, metrics["basis_max_probe_abs"])
        max_optimal_probe = max(max_optimal_probe, metrics["optimal_unit_probe_abs"])
        max_basis_reconstruction_error = max(max_basis_reconstruction_error, metrics["basis_reconstruction_error"])
        max_optimal_probe_norm_error = max(max_optimal_probe_norm_error, metrics["optimal_unit_probe_norm_error"])
    end
    alt_xxy = 0.0
    alt_xyy = 0.0
    for sample_idx in 1:SAMPLE_COUNT
        x = probe_vector(dim, sample_idx, 11)
        y = probe_vector(dim, sample_idx, 13)
        alt_xxy = max(alt_xxy, norm(associator(table, x, x, y)))
        alt_xyy = max(alt_xyy, norm(associator(table, x, y, y)))
    end
    Dict{String,Any}(
        "name" => name,
        "max_assoc_norm" => max_assoc_norm,
        "max_basis_probe_abs" => max_basis_probe,
        "max_optimal_unit_probe_abs" => max_optimal_probe,
        "max_basis_reconstruction_error" => max_basis_reconstruction_error,
        "max_optimal_unit_probe_norm_error" => max_optimal_probe_norm_error,
        "alternativity_xxy_max_norm" => alt_xxy,
        "alternativity_xyy_max_norm" => alt_xyy,
        "witness" => witness,
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

function build_result()
    h = analyze_table("H", quaternion_table())
    o = analyze_table("O", octonion_table())

    verdicts = Dict{String,Any}(
        "H_bracketing_probe_indistinguishable" => h["max_assoc_norm"] < TOL && h["max_basis_probe_abs"] < TOL,
        "O_bracketing_probe_distinguishable" => o["max_assoc_norm"] > STRICT_STOP_TOL &&
            o["max_basis_probe_abs"] > TOL && o["max_optimal_unit_probe_norm_error"] < TOL,
    )
    controls = Dict{String,Any}(
        "H_associativity_control_ok" => h["max_assoc_norm"] < TOL,
        "O_general_nonassociativity_control_ok" => o["max_assoc_norm"] > STRICT_STOP_TOL,
        "O_alternativity_control_ok" => max(o["alternativity_xxy_max_norm"], o["alternativity_xyy_max_norm"]) < TOL,
    )
    controls["control_miswired"] = !(controls["H_associativity_control_ok"] &&
        controls["O_general_nonassociativity_control_ok"] && controls["O_alternativity_control_ok"])

    shared_scalars = Dict{String,Any}(
        "sample_count" => SAMPLE_COUNT,
        "H_max_assoc_norm" => h["max_assoc_norm"],
        "H_max_basis_probe_abs" => h["max_basis_probe_abs"],
        "H_max_basis_reconstruction_error" => h["max_basis_reconstruction_error"],
        "H_max_optimal_unit_probe_abs" => h["max_optimal_unit_probe_abs"],
        "O_max_assoc_norm" => o["max_assoc_norm"],
        "O_max_basis_probe_abs" => o["max_basis_probe_abs"],
        "O_max_optimal_unit_probe_abs" => o["max_optimal_unit_probe_abs"],
        "O_max_basis_reconstruction_error" => o["max_basis_reconstruction_error"],
        "O_max_optimal_unit_probe_norm_error" => o["max_optimal_unit_probe_norm_error"],
        "O_alternativity_xxy_max_norm" => o["alternativity_xxy_max_norm"],
        "O_alternativity_xyy_max_norm" => o["alternativity_xyy_max_norm"],
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
        "claim_ceiling" => "Finite bracketing/probe diagnostic only; no basin, admission, engine, Axis0, bridge, gravity, or formal-admission claim.",
        "sim_execution_kind" => "classical",
        "sim_class" => "probe_relative_bracketing_concept_probe",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "probe_note" => "Basis probes f_M(v)=Re(conj(M)v) recover the associator components; sqrt(sum basis readouts^2)=||associator||. The optimal unit probe M=assoc/||assoc|| attains ||assoc|| when assoc is nonzero.",
        "tool_manifest" => Dict{String,Any}(
            "Julia" => "load-bearing quaternion/octonion multiplication, associators, and probe readouts",
            "LinearAlgebra" => "load-bearing associator norms and probe reconstruction norms",
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
            "H" => h["witness"],
            "O" => o["witness"],
        ),
        "plain_sentence" => "Quaternion bracketings are probe-indistinguishable because the associator vanishes, while generic octonion bracketings have a nonzero associator resolved by component probes and by the optimal unit probe; alternativity still kills repeated-input associators.",
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["stop_condition_fired"] = controls["control_miswired"] ||
        !verdicts["H_bracketing_probe_indistinguishable"] ||
        !verdicts["O_bracketing_probe_distinguishable"] ||
        result["parity"]["stop_condition_fired"]
    result
end

function print_summary(result::Dict{String,Any})
    n = result["numbers"]
    println("nonassociativity_as_probe_bracketing - Julia full sim")
    println("H_bracketing_probe_indistinguishable=", result["verdicts"]["H_bracketing_probe_indistinguishable"],
        " H_max_assoc_norm=", n["H_max_assoc_norm"],
        " H_max_basis_probe_abs=", n["H_max_basis_probe_abs"])
    println("O_bracketing_probe_distinguishable=", result["verdicts"]["O_bracketing_probe_distinguishable"],
        " O_max_assoc_norm=", n["O_max_assoc_norm"],
        " O_max_basis_probe_abs=", n["O_max_basis_probe_abs"],
        " O_max_optimal_unit_probe_abs=", n["O_max_optimal_unit_probe_abs"])
    println("O_alternativity_control_ok=", result["controls"]["O_alternativity_control_ok"],
        " O_alternativity_xxy_max_norm=", n["O_alternativity_xxy_max_norm"],
        " O_alternativity_xyy_max_norm=", n["O_alternativity_xyy_max_norm"])
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
    println("STOP: nonassociativity_as_probe_bracketing control/verdict/parity condition failed.")
    exit(2)
end
