#!/usr/bin/env julia

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "mobius_two_engine_holonomy_probe"
const RESULT_PATH = joinpath(@__DIR__, "mobius_two_engine_holonomy_probe_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "mobius_two_engine_holonomy_probe_jax_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

function su2(axis::Vector{Float64}, theta::Float64)
    a = axis ./ norm(axis)
    generator = a[1] .* SX .+ a[2] .* SY .+ a[3] .* SZ
    cos(theta / 2.0) .* I2 .- im * sin(theta / 2.0) .* generator
end

function spinor_from_angles(theta::Float64, phi::Float64)
    ComplexF64[cos(theta / 2.0), exp(im * phi) * sin(theta / 2.0)]
end

function frame_holonomy(frame::Matrix{ComplexF64}, transport::Matrix{ComplexF64})
    numerator = tr(frame' * transport * frame)
    denominator = tr(frame' * frame)
    real(numerator / denominator)
end

function spinor_return_sign(start::Vector{ComplexF64}, stop::Vector{ComplexF64})
    real(dot(start, stop) / dot(start, start))
end

function mobius_band_normal(theta::Float64)
    Float64[
        cos(theta / 2.0) * cos(theta),
        cos(theta / 2.0) * sin(theta),
        sin(theta / 2.0),
    ]
end

function cylinder_normal(theta::Float64)
    Float64[cos(theta), sin(theta), 0.0]
end

approx(value::Float64, target::Float64; tol::Float64=TOL) = abs(value - target) <= tol

function shared_scalars(values::Dict{String,Any}, verdicts::Dict{String,Any}, controls::Dict{String,Any})
    keys = [
        "mobius_holonomy_2pi",
        "mobius_holonomy_4pi",
        "mobius_band_frame_2pi",
        "mobius_band_frame_4pi",
        "cylinder_holonomy_2pi",
        "cylinder_holonomy_4pi",
        "spinor_720_tie_2pi",
        "spinor_720_tie_4pi",
        "spinor_720_holonomy_2pi",
        "spinor_720_holonomy_4pi",
        "mobius_vs_spinor_z2_diff_2pi",
        "mobius_vs_spinor_z2_diff_4pi",
        "cylinder_vs_mobius_2pi_gap",
        "two_engine_frame_residual_2pi",
        "two_engine_frame_residual_4pi",
        "spinor_2pi_sign_residual",
        "spinor_4pi_return_residual",
    ]
    scalars = Dict{String,Any}()
    for key in keys
        scalars[key] = Float64(values[key])
    end
    for key in [
        "mobius_orientation_flips_at_2pi",
        "mobius_restores_at_4pi",
        "two_engine_is_mobius_not_cylinder",
        "spinor_720_tie_matches_mobius",
        "cylinder_control_no_flip",
    ]
        scalars["verdict_" * key] = (verdicts[key]::Bool) ? 1.0 : 0.0
    end
    for key in [
        "cylinder_control_flips",
        "real_mobius_band_frame_flips",
        "spinor_tie_reproduces_minus_one",
    ]
        scalars["control_" * key] = (controls[key]::Bool) ? 1.0 : 0.0
    end
    scalars
end

function compare_booleans(local_result::Dict{String,Any}, peer)
    mismatches = String[]
    for block in ["controls", "verdicts"]
        if !haskey(peer, block)
            push!(mismatches, block * ".__missing_block__")
            continue
        end
        for (key, value) in local_result[block]
            if !haskey(peer[block], key) || Bool(peer[block][key]) != Bool(value)
                push!(mismatches, block * "." * key)
            end
        end
    end
    mismatches
end

function parity_block(result::Dict{String,Any})
    if !isfile(JAX_REFERENCE_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_REFERENCE_PATH,
            "peer_result_found" => false,
            "peer_available" => false,
            "missing_keys" => collect(keys(result["shared_scalars"])),
            "extra_peer_keys" => String[],
            "boolean_mismatches" => String[],
            "parity_max_diff" => nothing,
            "worst_key" => nothing,
            "parity_pass" => false,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => true,
            "stop_condition_fired" => true,
        )
    end
    peer = JSON.parsefile(JAX_REFERENCE_PATH)
    local_keys = Set(collect(keys(result["shared_scalars"])))
    peer_keys = haskey(peer, "shared_scalars") ? Set(collect(keys(peer["shared_scalars"]))) : Set{String}()
    missing_keys = sort(collect(setdiff(local_keys, peer_keys)))
    extra_peer_keys = sort(collect(setdiff(peer_keys, local_keys)))
    diffs = Dict{String,Any}()
    max_diff = 0.0
    worst_key = ""
    for key in sort(collect(intersect(local_keys, peer_keys)))
        diff = abs(Float64(result["shared_scalars"][key]) - Float64(peer["shared_scalars"][key]))
        diffs[key] = diff
        if diff > max_diff
            max_diff = diff
            worst_key = key
        end
    end
    boolean_mismatches = compare_booleans(result, peer)
    parity_pass = isempty(missing_keys) && isempty(extra_peer_keys) && isempty(boolean_mismatches) && max_diff < TOL
    strict_divergence = !isempty(missing_keys) || !isempty(extra_peer_keys) || !isempty(boolean_mismatches) || max_diff > STRICT_STOP_TOL
    Dict{String,Any}(
        "peer_result_path" => JAX_REFERENCE_PATH,
        "peer_result_found" => true,
        "peer_available" => true,
        "missing_keys" => missing_keys,
        "extra_peer_keys" => extra_peer_keys,
        "boolean_mismatches" => boolean_mismatches,
        "parity_max_diff" => max_diff,
        "worst_key" => worst_key,
        "parity_pass" => parity_pass,
        "within_1e_9" => max_diff < TOL && isempty(missing_keys) && isempty(extra_peer_keys),
        "strict_divergence_gt_1e_6" => strict_divergence,
        "stop_condition_fired" => !parity_pass,
        "diffs" => diffs,
    )
end

function main()
    axis = [0.2, -0.5, 0.84]
    theta_2pi = 2.0 * pi
    theta_4pi = 4.0 * pi
    two_engine_frame = I2
    u2 = su2(axis, theta_2pi)
    u4 = su2(axis, theta_4pi)

    psi = spinor_from_angles(1.1, -0.7)
    psi2 = u2 * psi
    psi4 = u4 * psi

    m0 = mobius_band_normal(0.0)
    c0 = cylinder_normal(0.0)

    values = Dict{String,Any}(
        "theta_2pi" => theta_2pi,
        "theta_4pi" => theta_4pi,
        "axis" => axis ./ norm(axis),
        "mobius_holonomy_2pi" => frame_holonomy(two_engine_frame, u2),
        "mobius_holonomy_4pi" => frame_holonomy(two_engine_frame, u4),
        "mobius_band_frame_2pi" => dot(m0, mobius_band_normal(theta_2pi)) / dot(m0, m0),
        "mobius_band_frame_4pi" => dot(m0, mobius_band_normal(theta_4pi)) / dot(m0, m0),
        "cylinder_holonomy_2pi" => dot(c0, cylinder_normal(theta_2pi)) / dot(c0, c0),
        "cylinder_holonomy_4pi" => dot(c0, cylinder_normal(theta_4pi)) / dot(c0, c0),
        "spinor_720_tie_2pi" => spinor_return_sign(psi, psi2),
        "spinor_720_tie_4pi" => spinor_return_sign(psi, psi4),
        "spinor_720_holonomy_2pi" => spinor_return_sign(psi, psi2),
        "spinor_720_holonomy_4pi" => spinor_return_sign(psi, psi4),
        "two_engine_frame_residual_2pi" => norm(u2 + I2),
        "two_engine_frame_residual_4pi" => norm(u4 - I2),
        "spinor_2pi_sign_residual" => norm(psi2 + psi),
        "spinor_4pi_return_residual" => norm(psi4 - psi),
    )
    values["mobius_vs_spinor_z2_diff_2pi"] = abs(values["mobius_holonomy_2pi"] - values["spinor_720_tie_2pi"])
    values["mobius_vs_spinor_z2_diff_4pi"] = abs(values["mobius_holonomy_4pi"] - values["spinor_720_tie_4pi"])
    values["cylinder_vs_mobius_2pi_gap"] = abs(values["cylinder_holonomy_2pi"] - values["mobius_holonomy_2pi"])

    controls = Dict{String,Any}(
        "cylinder_control_flips" => approx(values["cylinder_holonomy_2pi"], -1.0),
        "cylinder_control_no_flip" => approx(values["cylinder_holonomy_2pi"], 1.0),
        "real_mobius_band_frame_flips" => approx(values["mobius_band_frame_2pi"], -1.0) &&
            approx(values["mobius_band_frame_4pi"], 1.0),
        "spinor_tie_reproduces_minus_one" => approx(values["spinor_720_tie_2pi"], -1.0),
    )
    verdicts = Dict{String,Any}(
        "mobius_orientation_flips_at_2pi" => approx(values["mobius_holonomy_2pi"], -1.0),
        "mobius_restores_at_4pi" => approx(values["mobius_holonomy_4pi"], 1.0),
        "cylinder_control_no_flip" => controls["cylinder_control_no_flip"],
        "spinor_720_tie_matches_mobius" => controls["spinor_tie_reproduces_minus_one"] &&
            approx(values["mobius_vs_spinor_z2_diff_2pi"], 0.0) &&
            approx(values["mobius_vs_spinor_z2_diff_4pi"], 0.0),
    )
    verdicts["two_engine_is_mobius_not_cylinder"] = verdicts["mobius_orientation_flips_at_2pi"] &&
        verdicts["mobius_restores_at_4pi"] &&
        verdicts["cylinder_control_no_flip"] &&
        verdicts["spinor_720_tie_matches_mobius"] &&
        !(controls["cylinder_control_flips"]::Bool)

    result = Dict{String,Any}(
        "sim_id" => OBJECT_ID,
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "version" => "1.0.0",
        "backend" => "julia",
        "backend_roles" => Dict(
            "julia" => "reference/exact SU(2) and real-frame holonomy computation using native LinearAlgebra",
            "jax" => "x64 mirror/stress computation using jax.numpy only",
        ),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "Finite two-engine Mobius/Z2 holonomy witness only; no engine admission, Axis0, gravity, bridge, basin, or canonical proof claim.",
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "transport_search",
        "carrier_layer" => "two_engine_left_right_spinor_frame",
        "geometry_layer" => "Mobius Z2 holonomy versus orientable cylinder control",
        "allowed_claims" => ["scratch diagnostic Mobius/non-orientable sign witness", "spinor 720 Z2 tie"],
        "blocked_consumers" => ["engine admission", "Axis0", "gravity", "bridge", "basin", "canonical proof"],
        "promotion_status" => "diagnostic_only",
        "numpy_compute_used" => false,
        "tools" => ["Julia LinearAlgebra"],
        "tool_manifest" => Dict(
            "Julia LinearAlgebra" => "load-bearing for SU(2) frame matrices, vector inner products, residual norms, and holonomy sign extraction",
            "Julia Dates/JSON" => "supportive for timestamped result serialization only",
        ),
        "TOOL_MANIFEST" => Dict(
            "Julia LinearAlgebra" => "load-bearing for SU(2) frame matrices, vector inner products, residual norms, and holonomy sign extraction",
            "Julia Dates/JSON" => "supportive for timestamped result serialization only",
        ),
        "tool_integration_depth" => Dict("Julia LinearAlgebra" => "load_bearing", "Julia Dates/JSON" => "supportive"),
        "TOOL_INTEGRATION_DEPTH" => Dict("Julia LinearAlgebra" => "load_bearing", "Julia Dates/JSON" => "supportive"),
        "values" => values,
        "controls" => controls,
        "verdicts" => verdicts,
        "plain_sentence" => "The two-engine left/right frame carries the Mobius non-orientable Z2 signature: one traversal flips the orientation sign, two traversals restore it, while the cylinder control does not flip.",
    )
    result["shared_scalars"] = shared_scalars(values, verdicts, controls)
    result["parity"] = parity_block(result)
    result["stop_condition_fired"] = result["parity"]["stop_condition_fired"] ||
        controls["cylinder_control_flips"] ||
        !(verdicts["mobius_orientation_flips_at_2pi"]::Bool) ||
        !(verdicts["mobius_restores_at_4pi"]::Bool) ||
        !(verdicts["two_engine_is_mobius_not_cylinder"]::Bool)

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    if result["stop_condition_fired"]
        println("STOP_CONDITION_FIRED mobius_two_engine_holonomy_probe julia")
        exit(1)
    end
    println("mobius_two_engine_holonomy_probe julia wrote $(RESULT_PATH)")
end

main()
