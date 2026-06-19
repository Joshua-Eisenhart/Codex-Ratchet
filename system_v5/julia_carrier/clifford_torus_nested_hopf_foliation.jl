#!/usr/bin/env julia
# object_id: clifford_torus_nested_hopf_foliation
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: Finite Hopf-torus foliation check inside S3 only. No basin,
# admission, engine, Axis0, bridge, gravity, or manifold-closure claim.

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "clifford_torus_nested_hopf_foliation"
const RESULT_PATH = joinpath(@__DIR__, "clifford_torus_nested_hopf_foliation_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "clifford_torus_nested_hopf_foliation_jax_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const COVERAGE_TOL = 1.0e-6
const PHASE_COUNT = 24
const VOLUME_STEPS = 16_384
const S3_SAMPLE_COUNT = 512
const ETA_BINS = 16

function torus_point(eta::Float64, phi::Float64, chi::Float64)
    z = cos(eta) * exp(im * phi)
    w = sin(eta) * exp(im * chi)
    z, w
end

s3_constraint_residual(z::ComplexF64, w::ComplexF64) = abs(abs2(z) + abs2(w) - 1.0)

function phase_grid()
    collect(range(0.0, 2pi, length = PHASE_COUNT + 1))[1:end-1]
end

function interior_torus_checks()
    etas = [pi / 10, pi / 6, pi / 4, pi / 3, 2pi / 5]
    phases = phase_grid()
    interior_s3_constraint_max_residual = 0.0
    eta_radius_max_residual = 0.0
    periodic_closure_max_residual = 0.0
    hopf_latitude_residual = 0.0
    torus_metric_det_min = Inf

    for eta in etas
        torus_metric_det_min = min(torus_metric_det_min, cos(eta)^2 * sin(eta)^2)
        for phi in phases, chi in phases
            z, w = torus_point(eta, phi, chi)
            interior_s3_constraint_max_residual = max(interior_s3_constraint_max_residual, s3_constraint_residual(z, w))
            eta_radius_max_residual = max(eta_radius_max_residual, abs(abs(z) - cos(eta)), abs(abs(w) - sin(eta)))
            z_phi, w_phi = torus_point(eta, phi + 2pi, chi)
            z_chi, w_chi = torus_point(eta, phi, chi + 2pi)
            periodic_closure_max_residual = max(periodic_closure_max_residual,
                abs(z_phi - z), abs(w_phi - w), abs(z_chi - z), abs(w_chi - w))
            hopf_latitude_residual = max(hopf_latitude_residual, abs((abs2(z) - abs2(w)) - cos(2eta)))
        end
    end
    Dict{String,Any}(
        "eta_values" => etas,
        "phase_count_per_circle" => PHASE_COUNT,
        "interior_s3_constraint_max_residual" => interior_s3_constraint_max_residual,
        "eta_radius_max_residual" => eta_radius_max_residual,
        "periodic_closure_max_residual" => periodic_closure_max_residual,
        "torus_metric_det_min" => torus_metric_det_min,
        "hopf_latitude_residual" => hopf_latitude_residual,
    )
end

function volume_check()
    deta = (pi / 2) / VOLUME_STEPS
    volume_estimate = 0.0
    for i in 0:(VOLUME_STEPS - 1)
        eta = (i + 0.5) * deta
        volume_estimate += 4pi^2 * cos(eta) * sin(eta) * deta
    end
    s3_volume_reference = 2pi^2
    Dict{String,Any}(
        "volume_steps" => VOLUME_STEPS,
        "volume_estimate" => volume_estimate,
        "s3_volume_reference" => s3_volume_reference,
        "foliation_volume_residual" => abs(volume_estimate - s3_volume_reference),
    )
end

function deterministic_s3_sample(k::Int)
    u = (k - 0.5) / S3_SAMPLE_COUNT
    eta = asin(sqrt(u))
    phi = 2pi * mod(k * 37, S3_SAMPLE_COUNT) / S3_SAMPLE_COUNT
    chi = 2pi * mod(k * 53, S3_SAMPLE_COUNT) / S3_SAMPLE_COUNT
    z, w = torus_point(eta, phi, chi)
    z, w, eta
end

function sample_reconstruction_check()
    sample_reconstruction_max_residual = 0.0
    min_eta = Inf
    max_eta = -Inf
    bins = zeros(Int, ETA_BINS)
    for k in 1:S3_SAMPLE_COUNT
        z, w, _ = deterministic_s3_sample(k)
        eta = atan(abs(w), abs(z))
        phi = angle(z)
        chi = angle(w)
        zr, wr = torus_point(eta, phi, chi)
        residual = norm([real(z - zr), imag(z - zr), real(w - wr), imag(w - wr)])
        sample_reconstruction_max_residual = max(sample_reconstruction_max_residual, residual)
        min_eta = min(min_eta, eta)
        max_eta = max(max_eta, eta)
        bin = clamp(floor(Int, eta / (pi / 2) * ETA_BINS) + 1, 1, ETA_BINS)
        bins[bin] += 1
    end
    Dict{String,Any}(
        "sample_count" => S3_SAMPLE_COUNT,
        "sample_reconstruction_max_residual" => sample_reconstruction_max_residual,
        "eta_min" => min_eta,
        "eta_max" => max_eta,
        "eta_endpoint_gap" => max(min_eta, pi / 2 - max_eta),
        "eta_bins" => bins,
        "eta_bin_min_count" => minimum(bins),
    )
end

function core_circle_checks()
    phases = phase_grid()
    core_circle_s3_residual = 0.0
    core_zero_radius_residual = 0.0
    for phi in phases
        z0, w0 = torus_point(0.0, phi, 0.0)
        z1, w1 = torus_point(pi / 2, 0.0, phi)
        core_circle_s3_residual = max(core_circle_s3_residual, s3_constraint_residual(z0, w0), s3_constraint_residual(z1, w1))
        core_zero_radius_residual = max(core_zero_radius_residual, abs(w0), abs(z1))
    end
    Dict{String,Any}(
        "core_circle_s3_residual" => core_circle_s3_residual,
        "core_zero_radius_residual" => core_zero_radius_residual,
    )
end

function clifford_torus_check()
    phases = phase_grid()
    eta = pi / 4
    clifford_equal_radius_residual = 0.0
    clifford_target_radius_residual = 0.0
    clifford_hopf_equator_residual = 0.0
    target = 1.0 / sqrt(2.0)
    for phi in phases, chi in phases
        z, w = torus_point(eta, phi, chi)
        clifford_equal_radius_residual = max(clifford_equal_radius_residual, abs(abs(z) - abs(w)))
        clifford_target_radius_residual = max(clifford_target_radius_residual, abs(abs(z) - target), abs(abs(w) - target))
        clifford_hopf_equator_residual = max(clifford_hopf_equator_residual, abs(abs2(z) - abs2(w)))
    end
    Dict{String,Any}(
        "eta" => eta,
        "clifford_equal_radius_residual" => clifford_equal_radius_residual,
        "clifford_target_radius_residual" => clifford_target_radius_residual,
        "clifford_hopf_equator_residual" => clifford_hopf_equator_residual,
    )
end

function flat_t2_control()
    phases = phase_grid()
    flat_t2_s3_constraint_min_residual = Inf
    flat_t2_s3_constraint_max_residual = 0.0
    for phi in phases, chi in phases
        z = exp(im * phi)
        w = exp(im * chi)
        residual = abs(abs2(z) + abs2(w) - 1.0)
        flat_t2_s3_constraint_min_residual = min(flat_t2_s3_constraint_min_residual, residual)
        flat_t2_s3_constraint_max_residual = max(flat_t2_s3_constraint_max_residual, residual)
    end
    Dict{String,Any}(
        "flat_t2_s3_constraint_min_residual" => flat_t2_s3_constraint_min_residual,
        "flat_t2_s3_constraint_max_residual" => flat_t2_s3_constraint_max_residual,
        "flat_t2_rejected" => flat_t2_s3_constraint_min_residual > 0.5,
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
    interior = interior_torus_checks()
    volume = volume_check()
    samples = sample_reconstruction_check()
    core = core_circle_checks()
    clifford = clifford_torus_check()
    flat = flat_t2_control()

    verdicts = Dict{String,Any}(
        "torus_is_constrained_slice" => interior["interior_s3_constraint_max_residual"] < TOL &&
            interior["eta_radius_max_residual"] < TOL &&
            interior["periodic_closure_max_residual"] < TOL &&
            interior["torus_metric_det_min"] > 0.0 &&
            interior["hopf_latitude_residual"] < TOL,
        "foliation_covers_S3" => volume["foliation_volume_residual"] < COVERAGE_TOL &&
            samples["sample_reconstruction_max_residual"] < TOL &&
            samples["eta_bin_min_count"] > 0 &&
            core["core_circle_s3_residual"] < TOL,
        "clifford_torus_equal_radius_slice" => clifford["clifford_equal_radius_residual"] < TOL &&
            clifford["clifford_target_radius_residual"] < TOL &&
            clifford["clifford_hopf_equator_residual"] < TOL,
        "flat_t2_control_pass" => flat["flat_t2_rejected"],
    )
    controls = Dict{String,Any}(
        "flat_t2_off_s3_control_ok" => flat["flat_t2_rejected"],
        "core_circles_control_ok" => core["core_circle_s3_residual"] < TOL && core["core_zero_radius_residual"] < TOL,
    )
    controls["control_miswired"] = !(controls["flat_t2_off_s3_control_ok"] && controls["core_circles_control_ok"])

    shared_scalars = Dict{String,Any}(
        "interior_s3_constraint_max_residual" => interior["interior_s3_constraint_max_residual"],
        "eta_radius_max_residual" => interior["eta_radius_max_residual"],
        "periodic_closure_max_residual" => interior["periodic_closure_max_residual"],
        "torus_metric_det_min" => interior["torus_metric_det_min"],
        "hopf_latitude_residual" => interior["hopf_latitude_residual"],
        "volume_estimate" => volume["volume_estimate"],
        "s3_volume_reference" => volume["s3_volume_reference"],
        "foliation_volume_residual" => volume["foliation_volume_residual"],
        "sample_reconstruction_max_residual" => samples["sample_reconstruction_max_residual"],
        "eta_endpoint_gap" => samples["eta_endpoint_gap"],
        "eta_bin_min_count" => samples["eta_bin_min_count"],
        "core_circle_s3_residual" => core["core_circle_s3_residual"],
        "core_zero_radius_residual" => core["core_zero_radius_residual"],
        "clifford_equal_radius_residual" => clifford["clifford_equal_radius_residual"],
        "clifford_target_radius_residual" => clifford["clifford_target_radius_residual"],
        "clifford_hopf_equator_residual" => clifford["clifford_hopf_equator_residual"],
        "flat_t2_s3_constraint_min_residual" => flat["flat_t2_s3_constraint_min_residual"],
        "flat_t2_s3_constraint_max_residual" => flat["flat_t2_s3_constraint_max_residual"],
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
        "claim_ceiling" => "Finite Hopf-torus foliation check inside S3 only; no basin, admission, engine, Axis0, bridge, gravity, or manifold-closure claim.",
        "sim_execution_kind" => "classical",
        "sim_class" => "hopf_torus_foliation_geometry_probe",
        "tol" => TOL,
        "coverage_tol" => COVERAGE_TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "parameterization" => "F(eta,phi,chi)=(cos(eta)*exp(i*phi), sin(eta)*exp(i*chi)); eta in (0,pi/2) gives Hopf tori, eta=0 and pi/2 give core circles.",
        "tool_manifest" => Dict{String,Any}(
            "Julia" => "load_bearing finite torus parameterization, volume quadrature, and reconstruction checks",
            "LinearAlgebra" => "load_bearing residual norms for reconstruction and embedded constraints",
            "JSON" => "supportive result serialization",
        ),
        "tool_integration_depth" => Dict{String,Any}(
            "Julia" => "load_bearing",
            "LinearAlgebra" => "load_bearing",
            "JSON" => "supportive",
        ),
        "interior_tori" => interior,
        "foliation_volume" => volume,
        "sample_reconstruction" => samples,
        "core_circles" => core,
        "clifford_torus" => clifford,
        "flat_t2_control" => flat,
        "verdicts" => verdicts,
        "controls" => controls,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "plain_sentence" => "A3 only shows that the Hopf latitude slices form a finite checked torus family inside S3, with the Clifford torus as the equal-radius slice; it does not promote any downstream manifold or admission claim.",
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["stop_condition_fired"] = controls["control_miswired"] ||
        !verdicts["torus_is_constrained_slice"] ||
        !verdicts["foliation_covers_S3"] ||
        !verdicts["clifford_torus_equal_radius_slice"] ||
        result["parity"]["stop_condition_fired"]
    result
end

function print_summary(result::Dict{String,Any})
    s = result["shared_scalars"]
    println("clifford_torus_nested_hopf_foliation - Julia full sim")
    println("torus_is_constrained_slice=", result["verdicts"]["torus_is_constrained_slice"],
        " interior_s3_constraint_max_residual=", s["interior_s3_constraint_max_residual"],
        " torus_metric_det_min=", s["torus_metric_det_min"])
    println("foliation_covers_S3=", result["verdicts"]["foliation_covers_S3"],
        " foliation_volume_residual=", s["foliation_volume_residual"],
        " sample_reconstruction_max_residual=", s["sample_reconstruction_max_residual"],
        " eta_bin_min_count=", s["eta_bin_min_count"])
    println("clifford_torus_equal_radius_slice=", result["verdicts"]["clifford_torus_equal_radius_slice"],
        " clifford_target_radius_residual=", s["clifford_target_radius_residual"])
    println("flat_t2_control_pass=", result["verdicts"]["flat_t2_control_pass"],
        " flat_t2_s3_constraint_min_residual=", s["flat_t2_s3_constraint_min_residual"])
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
    println("STOP: clifford_torus_nested_hopf_foliation control/verdict/parity condition failed.")
    exit(2)
end
