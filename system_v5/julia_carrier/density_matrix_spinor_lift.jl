#!/usr/bin/env julia
# object_id: density_matrix_spinor_lift
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "density_matrix_spinor_lift"
const RESULT_PATH = joinpath(@__DIR__, "density_matrix_spinor_lift_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "density_matrix_spinor_lift_jax_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

dm(psi::Vector{ComplexF64}) = psi * psi'

function bloch_from_rho(rho::Matrix{ComplexF64})
    [real(tr(rho * SX)), real(tr(rho * SY)), real(tr(rho * SZ))]
end

function rho_from_bloch(r::Vector{Float64})
    0.5 .* (I2 .+ r[1] .* SX .+ r[2] .* SY .+ r[3] .* SZ)
end

function spinor_from_angles(theta::Float64, phi::Float64)
    ComplexF64[cos(theta / 2), exp(im * phi) * sin(theta / 2)]
end

function su2(axis::Vector{Float64}, theta::Float64)
    a = axis ./ norm(axis)
    generator = a[1] .* SX .+ a[2] .* SY .+ a[3] .* SZ
    cos(theta / 2) .* I2 .- im * sin(theta / 2) .* generator
end

function phase_factor(start::Vector{ComplexF64}, stop::Vector{ComplexF64})
    dot(start, stop) / dot(start, start)
end

function density_overlap(start::Matrix{ComplexF64}, stop::Matrix{ComplexF64})
    real(tr(start' * stop)) / real(tr(start' * start))
end

function partial_trace_ancilla(psi4::Vector{ComplexF64})
    psi_matrix = reshape(psi4, 2, 2)
    psi_matrix * psi_matrix'
end

function mixed_purification(rho::Matrix{ComplexF64})
    ev = eigen(Hermitian(rho))
    psi_matrix = zeros(ComplexF64, 2, 2)
    for i in 1:2
        psi_matrix[:, i] .= sqrt(max(ev.values[i], 0.0)) .* ev.vectors[:, i]
    end
    vec(psi_matrix)
end

function shared_scalars(values::Dict{String,Any}, verdicts::Dict{String,Any}, controls::Dict{String,Any})
    scalars = Dict{String,Any}()
    for key in [
        "trace_rho_residual", "hermitian_residual", "rho_reconstruction_residual", "bloch_norm",
        "idempotency_residual", "spinor_norm_residual", "hopf_s2_residual", "phase_invariance_residual",
        "base_holonomy_2pi", "lift_holonomy_2pi", "base_holonomy_4pi", "lift_holonomy_4pi",
        "rho_2pi_return_residual", "psi_2pi_sign_residual", "rho_4pi_return_residual",
        "psi_4pi_return_residual", "pure_spinor_manifold_dim", "base_sphere_dim", "fiber_dim", "mixed_bloch_norm", "mixed_purity",
        "mixed_rank", "mixed_idempotency_residual", "ancilla_purification_residual",
        "c4_purification_norm_residual",
    ]
        scalars[key] = Float64(values[key])
    end
    for key in ["rho_is_base_spinor_is_lift", "pure_states_are_S2", "purification_lands_on_unit_c4"]
        scalars["verdict_" * key] = (verdicts[key]::Bool) ? 1.0 : 0.0
    end
    scalars["control_mixed_no_single_s3_point"] = (controls["mixed_no_single_s3_point"]::Bool) ? 1.0 : 0.0
    scalars
end

function parity_block(result::Dict{String,Any})
    if !isfile(JAX_REFERENCE_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_REFERENCE_PATH,
            "peer_available" => false,
            "parity_max_diff" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => true,
            "stop_condition_fired" => true,
        )
    end
    peer = JSON.parsefile(JAX_REFERENCE_PATH)
    diffs = Dict{String,Any}()
    max_diff = 0.0
    worst_key = ""
    for (key, value) in result["shared_scalars"]
        if haskey(peer["shared_scalars"], key)
            diff = abs(Float64(value) - Float64(peer["shared_scalars"][key]))
            diffs[key] = diff
            if diff > max_diff
                max_diff = diff
                worst_key = key
            end
        end
    end
    Dict{String,Any}(
        "peer_result_path" => JAX_REFERENCE_PATH,
        "peer_available" => true,
        "parity_max_diff" => max_diff,
        "worst_key" => worst_key,
        "within_1e_9" => max_diff < TOL,
        "strict_divergence_gt_1e_6" => max_diff > STRICT_STOP_TOL,
        "stop_condition_fired" => max_diff > STRICT_STOP_TOL,
        "diffs" => diffs,
    )
end

function main()
    psi = spinor_from_angles(1.1, -0.7)
    rho = dm(psi)
    r = bloch_from_rho(rho)
    rho_rebuilt = rho_from_bloch(r)
    phase = exp(im * 0.83)
    rho_phase = dm(phase .* psi)

    axis = [0.2, -0.5, 0.84]
    u2 = su2(axis, 2.0 * pi)
    u4 = su2(axis, 4.0 * pi)
    psi2 = u2 * psi
    psi4 = u4 * psi
    rho2 = u2 * rho * u2'
    rho4 = u4 * rho * u4'

    mixed_r = 0.4 .* r
    mixed_rho = rho_from_bloch(mixed_r)
    mixed_eigs = eigvals(Hermitian(mixed_rho))
    mixed_rank = count(x -> x > TOL, mixed_eigs)
    psi4_mixed = mixed_purification(mixed_rho)
    mixed_from_ancilla = partial_trace_ancilla(psi4_mixed)

    values = Dict{String,Any}(
        "trace_rho_residual" => abs(real(tr(rho)) - 1.0),
        "hermitian_residual" => norm(rho - rho'),
        "rho_reconstruction_residual" => norm(rho - rho_rebuilt),
        "bloch_norm" => norm(r),
        "idempotency_residual" => norm(rho * rho - rho),
        "spinor_norm_residual" => abs(real(dot(psi, psi)) - 1.0),
        "hopf_s2_residual" => abs(norm(r) - 1.0),
        "phase_invariance_residual" => norm(rho_phase - rho),
        "base_holonomy_2pi" => density_overlap(rho, rho2),
        "lift_holonomy_2pi" => real(phase_factor(psi, psi2)),
        "base_holonomy_4pi" => density_overlap(rho, rho4),
        "lift_holonomy_4pi" => real(phase_factor(psi, psi4)),
        "rho_2pi_return_residual" => norm(rho2 - rho),
        "psi_2pi_sign_residual" => norm(psi2 + psi),
        "rho_4pi_return_residual" => norm(rho4 - rho),
        "psi_4pi_return_residual" => norm(psi4 - psi),
        "pure_spinor_manifold_dim" => Float64(2 * length(psi) - 1),
        "base_sphere_dim" => Float64(length(r) - 1),
        "fiber_dim" => Float64(2 * length(psi) - 1) - Float64(length(r) - 1),
        "mixed_bloch_norm" => norm(mixed_r),
        "mixed_purity" => real(tr(mixed_rho * mixed_rho)),
        "mixed_rank" => Float64(mixed_rank),
        "mixed_idempotency_residual" => norm(mixed_rho * mixed_rho - mixed_rho),
        "ancilla_purification_residual" => norm(mixed_from_ancilla - mixed_rho),
        "c4_purification_norm_residual" => abs(real(dot(psi4_mixed, psi4_mixed)) - 1.0),
    )
    controls = Dict{String,Any}(
        "mixed_no_single_s3_point" => values["mixed_bloch_norm"] < 1.0 - TOL &&
            values["mixed_purity"] < 1.0 - TOL &&
            values["mixed_rank"] == 2.0 &&
            values["mixed_idempotency_residual"] > TOL,
        "mixed_requires_ancilla_for_purification" => values["ancilla_purification_residual"] <= TOL,
    )
    verdicts = Dict{String,Any}(
        "rho_is_base_spinor_is_lift" => abs(values["base_holonomy_2pi"] - 1.0) <= TOL &&
            abs(values["lift_holonomy_2pi"] + 1.0) <= TOL &&
            values["fiber_dim"] == 1.0,
        "pure_states_are_S2" => values["hopf_s2_residual"] <= TOL && values["idempotency_residual"] <= TOL,
        "purification_lands_on_unit_c4" => values["c4_purification_norm_residual"] <= TOL &&
            values["ancilla_purification_residual"] <= TOL,
    )
    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "Density-matrix base to spinor-lift diagnostic only; no basin, admission, engine, Axis0, bridge, gravity, or 720-engine claim.",
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "tools" => ["Julia LinearAlgebra"],
        "tool_manifest" => Dict("Julia LinearAlgebra" => "load-bearing for density matrices, eigensystem rank control, residuals, and holonomy signs"),
        "TOOL_MANIFEST" => Dict("Julia LinearAlgebra" => "load-bearing for density matrices, eigensystem rank control, residuals, and holonomy signs"),
        "tool_integration_depth" => Dict("Julia LinearAlgebra" => "load_bearing"),
        "TOOL_INTEGRATION_DEPTH" => Dict("Julia LinearAlgebra" => "load_bearing"),
        "values" => values,
        "controls" => controls,
        "verdicts" => verdicts,
        "plain_sentence" => "The density matrix is the phase-forgetting base: lifting a pure boundary state to a spinor adds the U(1) fiber where the 2pi sign lives.",
    )
    result["shared_scalars"] = shared_scalars(values, verdicts, controls)
    result["parity"] = parity_block(result)
    result["stop_condition_fired"] = result["parity"]["stop_condition_fired"] ||
        !(controls["mixed_no_single_s3_point"]::Bool) ||
        !(controls["mixed_requires_ancilla_for_purification"]::Bool) ||
        !(verdicts["rho_is_base_spinor_is_lift"]::Bool) ||
        !(verdicts["pure_states_are_S2"]::Bool) ||
        !(verdicts["purification_lands_on_unit_c4"]::Bool)
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    if result["stop_condition_fired"]
        println("STOP_CONDITION_FIRED density_matrix_spinor_lift")
        exit(1)
    end
    println("density_matrix_spinor_lift julia wrote $(RESULT_PATH)")
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
