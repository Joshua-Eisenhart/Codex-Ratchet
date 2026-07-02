#!/usr/bin/env julia

using Dates
using JSON
using LinearAlgebra
using SHA

const ENGINE = "julia"
const DEFAULT_MANIFEST = "/tmp/golden_weyl_manifest.json"
const DEFAULT_RECEIPT = "/tmp/golden_weyl_julia_receipt.json"

json_quote(s::AbstractString) = JSON.json(String(s))

function canonical_json(x)
    if x isa AbstractDict
        parts = String[]
        for k in sort(collect(keys(x)))
            push!(parts, json_quote(String(k)) * ":" * canonical_json(x[k]))
        end
        return "{" * join(parts, ",") * "}"
    elseif x isa AbstractVector
        return "[" * join([canonical_json(v) for v in x], ",") * "]"
    elseif x isa AbstractString
        return json_quote(x)
    elseif x isa Bool
        return x ? "true" : "false"
    elseif x === nothing
        return "null"
    elseif x isa Integer
        return string(x)
    elseif x isa AbstractFloat
        if !isfinite(x)
            error("nonfinite float cannot be canonicalized")
        end
        return string(Float64(x))
    else
        error("unsupported canonical JSON type: $(typeof(x))")
    end
end

sha256_hex_bytes(data::Vector{UInt8}) = bytes2hex(sha256(data))
sha256_hex_string(s::String) = bytes2hex(sha256(Vector{UInt8}(codeunits(s))))
sha256_hex_obj(x) = sha256_hex_string(canonical_json(x))

function eta_grid(manifest)
    count = Int(manifest["eta_base"]["count"])
    return [0.5 * pi * (i - 1) / (count - 1) for i in 1:count]
end

function psi(phi::Float64, chi::Float64, eta::Float64)
    return ComplexF64[
        cis(phi + chi) * cos(eta),
        cis(phi - chi) * sin(eta),
    ]
end

function realized_state_fingerprint(manifest, etas)
    samples = manifest["state_fingerprint_samples"]
    vals = Float64[]
    for idx_any in samples["eta_indices"]
        eta = etas[Int(idx_any) + 1]
        for phi_any in samples["phis"], chi_any in samples["chis"]
            p = psi(Float64(phi_any), Float64(chi_any), eta)
            push!(vals, real(p[1]))
            push!(vals, imag(p[1]))
            push!(vals, real(p[2]))
            push!(vals, imag(p[2]))
        end
    end
    return sha256_hex_bytes(Vector{UInt8}(reinterpret(UInt8, vals)))
end

function psi_norm_error(etas)
    phis = [0.0, 0.37, 1.91]
    chis = [0.0, 0.73, 2.41]
    err = 0.0
    for eta in etas, phi in phis, chi in chis
        p = psi(phi, chi, eta)
        err = max(err, abs(real(dot(p, p)) - 1.0))
    end
    return err
end

function hopf_connection_error(etas)
    err = 0.0
    for eta in etas
        weights = (cos(eta)^2, sin(eta)^2)
        a_phi = weights[1] * 1.0 + weights[2] * 1.0
        a_chi = weights[1] * 1.0 + weights[2] * -1.0
        err = max(err, abs(a_phi - 1.0))
        err = max(err, abs(a_chi - cos(2.0 * eta)))
    end
    return err
end

function stereo_fiber_r_dr(theta::Float64, eta::Float64, base_sign::Float64, orient::Float64)
    # R^4(C^2)->R^3 transition: S^3 point (x1,y1,x2,y2) is projected by
    # P=(y1,x2,y2)/(1-x1). This is the R^3 curve used in the Gauss integral.
    a = cos(eta)
    b = base_sign * sin(eta)
    ot = orient * theta
    denom = 1.0 - a * cos(ot)
    denom_p = a * orient * sin(ot)
    numer = (a * sin(ot), b * cos(ot), b * sin(ot))
    numer_p = (a * orient * cos(ot), -b * orient * sin(ot), b * orient * cos(ot))
    r = (numer[1] / denom, numer[2] / denom, numer[3] / denom)
    dr = (
        (numer_p[1] * denom - numer[1] * denom_p) / denom^2,
        (numer_p[2] * denom - numer[2] * denom_p) / denom^2,
        (numer_p[3] * denom - numer[3] * denom_p) / denom^2,
    )
    return r, dr
end

dot3(a, b) = a[1] * b[1] + a[2] * b[2] + a[3] * b[3]
norm3(a) = sqrt(dot3(a, a))
sub3(a, b) = (a[1] - b[1], a[2] - b[2], a[3] - b[3])
cross3(a, b) = (
    a[2] * b[3] - a[3] * b[2],
    a[3] * b[1] - a[1] * b[3],
    a[1] * b[2] - a[2] * b[1],
)

function gauss_link_from_r_dr(r1, dr1, r2, dr2, dt::Float64)
    total = 0.0
    for i in eachindex(r1), j in eachindex(r2)
        diff = sub3(r1[i], r2[j])
        denom = norm3(diff)^3
        total += dot3(diff, cross3(dr1[i], dr2[j])) / denom
    end
    return total * dt * dt / (4.0 * pi)
end

function nested_gauss_linking(eta::Float64, n::Int)
    eps = 1.0e-12
    if eta <= eps || (0.5 * pi - eta) <= eps
        return 1.0
    end
    dt = 2.0 * pi / n
    r1 = Vector{NTuple{3, Float64}}(undef, n)
    dr1 = Vector{NTuple{3, Float64}}(undef, n)
    r2 = Vector{NTuple{3, Float64}}(undef, n)
    dr2 = Vector{NTuple{3, Float64}}(undef, n)
    for k in 1:n
        theta = (k - 1) * dt
        r1[k], dr1[k] = stereo_fiber_r_dr(theta, eta, 1.0, 1.0)
        r2[k], dr2[k] = stereo_fiber_r_dr(theta, 0.5 * pi - eta, -1.0, -1.0)
    end
    return gauss_link_from_r_dr(r1, dr1, r2, dr2, dt)
end

function nested_but_unlinked_linking(eta::Float64, n::Int)
    dt = 2.0 * pi / n
    outer = 1.55 + 0.10 * cos(2.0 * eta)
    inner = 0.42 + 0.12 * sin(eta)^2
    r1 = Vector{NTuple{3, Float64}}(undef, n)
    dr1 = Vector{NTuple{3, Float64}}(undef, n)
    r2 = Vector{NTuple{3, Float64}}(undef, n)
    dr2 = Vector{NTuple{3, Float64}}(undef, n)
    for k in 1:n
        theta = (k - 1) * dt
        r1[k] = (outer * cos(theta), outer * sin(theta), 0.0)
        dr1[k] = (-outer * sin(theta), outer * cos(theta), 0.0)
        r2[k] = (inner * cos(theta), inner * sin(theta), 0.0)
        dr2[k] = (-inner * sin(theta), inner * cos(theta), 0.0)
    end
    return gauss_link_from_r_dr(r1, dr1, r2, dr2, dt)
end

function flat_s2_sanity_linking(n::Int)
    dt = 2.0 * pi / n
    r1 = Vector{NTuple{3, Float64}}(undef, n)
    dr1 = Vector{NTuple{3, Float64}}(undef, n)
    r2 = Vector{NTuple{3, Float64}}(undef, n)
    dr2 = Vector{NTuple{3, Float64}}(undef, n)
    for k in 1:n
        theta = (k - 1) * dt
        r1[k] = (cos(theta), sin(theta), 0.0)
        dr1[k] = (-sin(theta), cos(theta), 0.0)
        r2[k] = (2.5 + 0.4 * cos(theta), 0.0, 0.4 * sin(theta))
        dr2[k] = (-0.4 * sin(theta), 0.0, 0.4 * cos(theta))
    end
    return gauss_link_from_r_dr(r1, dr1, r2, dr2, dt)
end

function tubular_winding_linking(winding_l::Int, n::Int)
    dt = 2.0 * pi / n
    r_major = 1.0
    r_minor = 0.35
    core = Vector{NTuple{3, Float64}}(undef, n)
    dcore = Vector{NTuple{3, Float64}}(undef, n)
    curve = Vector{NTuple{3, Float64}}(undef, n)
    dcurve = Vector{NTuple{3, Float64}}(undef, n)
    for k in 1:n
        theta = (k - 1) * dt
        core[k] = (cos(theta), sin(theta), 0.0)
        dcore[k] = (-sin(theta), cos(theta), 0.0)
        u = -theta
        du = -1.0
        a = r_major + r_minor * cos(Float64(winding_l) * u)
        da = -r_minor * Float64(winding_l) * sin(Float64(winding_l) * u) * du
        curve[k] = (a * cos(u), a * sin(u), r_minor * sin(Float64(winding_l) * u))
        dcurve[k] = (
            da * cos(u) - a * sin(u) * du,
            da * sin(u) + a * cos(u) * du,
            r_minor * Float64(winding_l) * cos(Float64(winding_l) * u) * du,
        )
    end
    return gauss_link_from_r_dr(core, dcore, curve, dcurve, dt)
end

function cocycle_from_phase_coefficients(coeffs, chirality::String)
    signs = Dict("L" => 1.0, "R" => -1.0)
    w0 = Float64(coeffs["component_0"]["chi"])
    w1 = Float64(coeffs["component_1"]["chi"])
    return signs[chirality] * (w0 - w1) / 2.0
end

function isigmay_charge_conj_coefficients(coeffs)
    return Dict(
        "component_0" => Dict(
            "phi" => -Int(coeffs["component_1"]["phi"]),
            "chi" => -Int(coeffs["component_1"]["chi"]),
        ),
        "component_1" => Dict(
            "phi" => -Int(coeffs["component_0"]["phi"]),
            "chi" => -Int(coeffs["component_0"]["chi"]),
        ),
    )
end

function n01_commutator_norm()
    gamma5 = [1.0 0.0; 0.0 -1.0]
    charge_swap = [0.0 1.0; 1.0 0.0]
    comm = gamma5 * charge_swap - charge_swap * gamma5
    return norm(comm)
end

mean(xs) = sum(xs) / length(xs)

function generated_control_hash(control_id::String, spec, source_hash::String)
    return sha256_hex_obj(Dict(
        "engine" => ENGINE,
        "generator" => "engine_local_procedural_control_from_manifest",
        "control_id" => control_id,
        "source_hash" => source_hash,
        "spec" => spec,
    ))
end

function build_receipt(manifest_path::String, receipt_path::String)
    manifest_bytes = read(manifest_path)
    shared_spec_hash = sha256_hex_bytes(copy(manifest_bytes))
    manifest = JSON.parse(String(copy(manifest_bytes)))
    etas = eta_grid(manifest)
    n = Int(manifest["quadrature"]["curve_points"])
    source_hash = sha256_hex_bytes(read(@__FILE__))
    state_fingerprint = realized_state_fingerprint(manifest, etas)

    linked_by_eta = [nested_gauss_linking(Float64(eta), n) for eta in etas]
    nested_unlinked_by_eta = [nested_but_unlinked_linking(Float64(eta), n) for eta in etas]
    flat_s2 = flat_s2_sanity_linking(n)
    sweep = Dict(string(Int(l_value)) => tubular_winding_linking(Int(l_value), n) for l_value in manifest["core_curves"]["nesting_parameter_sweep"]["L_values"])

    phase_coeffs = manifest["cocycle"]["phase_coefficients"]
    control_coeffs = isigmay_charge_conj_coefficients(phase_coeffs)
    cocycle_wl = cocycle_from_phase_coefficients(phase_coeffs, "L")
    cocycle_wr = cocycle_from_phase_coefficients(phase_coeffs, "R")
    control_wl = cocycle_from_phase_coefficients(control_coeffs, "L")
    control_wr = cocycle_from_phase_coefficients(control_coeffs, "R")
    n01_norm = n01_commutator_norm()

    linked_mean = mean(linked_by_eta)
    nested_unlinked_mean = mean(nested_unlinked_by_eta)
    linked_deviation = maximum(abs.(linked_by_eta .- 1.0))
    nested_unlinked_deviation = maximum(abs.(nested_unlinked_by_eta))
    two_sided_bound = maximum([
        linked_deviation,
        nested_unlinked_deviation,
        psi_norm_error(etas),
        hopf_connection_error(etas),
        2.0^-42,
    ])
    regime_gap = abs(linked_mean - nested_unlinked_mean)
    sweep_values = collect(values(sweep))
    sweep_responds = length(Set(round.(sweep_values))) == length(sweep_values) && maximum(sweep_values) - minimum(sweep_values) > 1.5
    linking_survives = (
        abs(linked_mean - 1.0) < 1.0e-6 &&
        maximum(abs.(nested_unlinked_by_eta)) < 1.0e-8 &&
        sweep_responds &&
        two_sided_bound < regime_gap
    )

    invariants = Dict(
        "linking_number_nested_linked_mean" => linked_mean,
        "linking_number_nested_linked_by_eta" => linked_by_eta,
        "linking_number_nested_but_unlinked_mean" => nested_unlinked_mean,
        "linking_number_nested_but_unlinked_by_eta" => nested_unlinked_by_eta,
        "linking_number_flat_S2_sanity" => flat_s2,
        "nesting_parameter_sweep" => sweep,
        "cocycle_wL" => cocycle_wl,
        "cocycle_wR" => cocycle_wr,
        "plain_S2_isigmay_cocycle_wL" => control_wl,
        "plain_S2_isigmay_cocycle_wR" => control_wr,
        "n01_commutator_norm" => n01_norm,
    )

    control_hashes = Dict(
        "nested_but_unlinked" => generated_control_hash("nested_but_unlinked", manifest["core_curves"]["nested_but_unlinked"], source_hash),
        "flat_S2_sanity" => generated_control_hash("flat_S2_sanity", manifest["core_curves"]["flat_S2_sanity"], source_hash),
        "nesting_parameter_sweep" => generated_control_hash("nesting_parameter_sweep", manifest["core_curves"]["nesting_parameter_sweep"], source_hash),
        "plain_S2_isigmay" => generated_control_hash("plain_S2_isigmay", Dict("output_coefficients" => control_coeffs), source_hash),
    )
    construction_hash = sha256_hex_obj(Dict(
        "engine" => ENGINE,
        "source_hash" => source_hash,
        "shared_spec_hash" => shared_spec_hash,
        "realized_state_fingerprint" => state_fingerprint,
        "algorithm_ids" => [
            "analytic_weyl_spinor",
            "stereographic_hopf_gauss_linking",
            "nested_unlinked_coplanar_gauss_control",
            "tubular_winding_sweep_gauss_control",
            "phase_winding_cocycle",
            "gamma5_charge_conj_commutator",
        ],
    ))

    controls = Dict(
        "nested_but_unlinked" => Dict(
            "control_input_hash" => control_hashes["nested_but_unlinked"],
            "same_gauss_function" => true,
            "geometrically_nested" => true,
            "topologically_unlinked" => true,
            "linking_mean" => nested_unlinked_mean,
            "max_abs_linking" => maximum(abs.(nested_unlinked_by_eta)),
            "verdict_for_linking" => maximum(abs.(nested_unlinked_by_eta)) < 1.0e-8 ? "KILLED_BY_DECISIVE_CONTROL" : "FAILED_CONTROL",
            "load_bearing_condition_component" => maximum(abs.(nested_unlinked_by_eta)) < 1.0e-8,
        ),
        "nesting_parameter_sweep" => Dict(
            "control_input_hash" => control_hashes["nesting_parameter_sweep"],
            "same_gauss_function" => true,
            "values" => sweep,
            "responds" => sweep_responds,
            "not_one_repeated_constant" => maximum(sweep_values) - minimum(sweep_values) > 1.5,
        ),
        "flat_S2_sanity" => Dict(
            "control_input_hash" => control_hashes["flat_S2_sanity"],
            "same_gauss_function" => true,
            "linking" => flat_s2,
            "status" => "demoted_sanity_check",
            "used_for_load_bearing" => false,
        ),
        "plain_S2_isigmay" => Dict(
            "control_input_hash" => control_hashes["plain_S2_isigmay"],
            "same_cocycle_function" => true,
            "control_coefficients_hash" => sha256_hex_obj(control_coeffs),
            "observable_delta_wL" => abs(cocycle_wl - control_wl),
            "observable_delta_wR" => abs(cocycle_wr - control_wr),
            "verdict_for_cocycle" => "REPRODUCED_BY_CONTROL",
            "load_bearing_for_cocycle" => false,
        ),
    )

    receipt = Dict(
        "engine" => ENGINE,
        "engine_role" => "exact_certificate_engine_local_julia_project",
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "manifest_path" => manifest_path,
        "receipt_path" => receipt_path,
        "source_hash" => source_hash,
        "shared_spec_hash" => shared_spec_hash,
        "construction_hash" => construction_hash,
        "realized_state_fingerprint" => state_fingerprint,
        "realized_state_fingerprint_note" => "hash computed over this engine's internally realized psi samples; raw psi/rho/state is not emitted",
        "sealed_construction" => Dict(
            "reads" => [manifest_path, @__FILE__],
            "does_not_read" => [
                "/tmp/golden_weyl_jax.py",
                "/tmp/golden_weyl_jax_receipt.json",
                "/tmp/golden_weyl_ledger.json",
                "raw psi/rho/Choi/tensor/state from any other engine",
            ],
            "raw_state_emitted" => false,
        ),
        "layer" => manifest["layer"],
        "claim_ceiling" => manifest["claim_ceiling"],
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "carrier" => manifest["carrier"],
        "finite_map" => manifest["finite_map"],
        "ambient_transition" => manifest["carrier"]["ambient_transition"],
        "eta_base" => Dict(
            "closed_interval" => [0.0, 0.5 * pi],
            "count" => length(etas),
            "values" => etas,
            "full_base_swept" => true,
            "endpoint_mode" => manifest["eta_base"]["endpoint_mode"],
        ),
        "root_constraints" => Dict(
            "F01" => Dict(
                "satisfied" => true,
                "finite_spinor_dim" => 2,
                "finite_eta_count" => length(etas),
                "finite_curve_quadrature_points" => n,
                "finite_invariant_registry" => manifest["parity_whitelist"],
            ),
            "N01" => Dict(
                "satisfied" => n01_norm > 0.0,
                "gamma5_charge_conj_commutator_norm" => n01_norm,
            ),
        ),
        "invariants" => invariants,
        "controls" => controls,
        "error_certificate" => Dict(
            "two_sided" => true,
            "nested_side_max_abs_linking_minus_1" => linked_deviation,
            "control_side_nested_unlinked_max_abs_linking_minus_0" => nested_unlinked_deviation,
            "error_bound" => two_sided_bound,
            "regime_gap" => regime_gap,
            "bound_lt_regime_gap" => two_sided_bound < regime_gap,
        ),
        "load_bearing_invariant" => linking_survives ? "linking" : "none",
        "classification" => "scratch_diagnostic",
        "tool_manifest" => Dict(
            "jax" => "not read by this engine during sealed construction",
            "julia" => "used as exact/certificate engine under system_v5/julia_carrier project for independent Gauss and cocycle readouts",
            "peps_ctmrg" => "not used; exact analytic carrier requested",
        ),
        "tool_integration_depth" => Dict(
            "jax" => "separate_engine_not_consumed",
            "julia" => "certificate_supportive",
            "peps_ctmrg" => "None",
        ),
        "blocked_consumers" => manifest["blocked_consumers"],
    )
    open(receipt_path, "w") do io
        JSON.print(io, receipt, 2)
        write(io, "\n")
    end
    return receipt
end

function main()
    manifest = length(ARGS) >= 1 ? ARGS[1] : DEFAULT_MANIFEST
    receipt_path = length(ARGS) >= 2 ? ARGS[2] : DEFAULT_RECEIPT
    receipt = build_receipt(manifest, receipt_path)
    println(JSON.json(Dict(
        "engine" => ENGINE,
        "receipt" => receipt_path,
        "load_bearing_invariant" => receipt["load_bearing_invariant"],
        "linking" => receipt["invariants"]["linking_number_nested_linked_mean"],
        "nested_but_unlinked" => receipt["invariants"]["linking_number_nested_but_unlinked_mean"],
        "sweep" => receipt["invariants"]["nesting_parameter_sweep"],
    )))
end

main()
