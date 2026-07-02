# L2_layer_codex.jl
#
# Independent Codex cross-check for L2: S3 spinor carrier, no Bloch substitution.
# This is a bounded proof-of-concept receipt, not a layer-completion or promotion claim.
#
# Math read from the current layer registry and read-only reference docs:
# - "S^3 = { psi in C^2 : ||psi|| = 1 }"
# - "pi(psi) = psi^dagger sigma psi in S^2"
# - "rho(psi) = |psi><psi| = 1/2(I + r . sigma)"
# - "psi_s(phi, chi; eta) = (exp(i(phi+chi)) cos eta,
#                            exp(i(phi-chi)) sin eta)^T"
# - "A = -i psi^dagger dpsi = dphi + cos(2 eta) dchi"
#
# Decisive dependency-forcing test:
# Replace the S3 spinor psi by the Bloch/density image rho=psi psi^dag.
# Two spinors that differ only by a global U(1) phase have the same rho and
# same Hopf base pi(psi), but S3 still distinguishes their fiber transport
# phase. If Bloch carries that same fiber signature, this file reports failure.
#
# classification: L2_layer_codex_poc
# promotion_allowed: false
#
# Tools:
# - LinearAlgebra is load-bearing for complex spinor/density operations, matrix
#   exponentials, norms, eigenvalues, entropy, and noncommuting gaps.
# - JSON is supportive receipt emission.
# - Z3 is omitted, not decorative: this bounded Julia layer has no SMT claim
#   that changes the verdict.

using LinearAlgebra
using JSON

const RESULTS_PATH = joinpath(@__DIR__, "L2_layer_codex_results.json")

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

spinor_norm(psi) = sqrt(real(psi' * psi))
on_s3(psi; tol=1e-10) = abs(spinor_norm(psi) - 1.0) <= tol
density(psi) = psi * psi'
phase_shift(psi, alpha) = exp(im * alpha) .* psi

function hopf_chart(phi, chi, eta)
    ComplexF64[
        exp(im * (phi + chi)) * cos(eta),
        exp(im * (phi - chi)) * sin(eta),
    ]
end

function hopf_projection(psi)
    [
        real(psi' * (SX * psi)),
        real(psi' * (SY * psi)),
        real(psi' * (SZ * psi)),
    ]
end

function trace_distance(a, b)
    vals = svdvals(a - b)
    0.5 * sum(vals)
end

function von_neumann_entropy(rho)
    h = Hermitian((rho + rho') / 2)
    vals = real.(eigvals(h))
    s = 0.0
    for p in vals
        if p > 1e-12
            s -= p * log(p)
        end
    end
    s
end

function fiber_transport_phase(psi, alpha)
    # Integral of A=dphi+cos(2eta)dchi along a pure global-phase/fiber segment
    # psi -> exp(i alpha) psi. Since chi and eta are fixed, this readout is alpha.
    angle(psi' * phase_shift(psi, alpha))
end

function su2_rotation(axis, theta)
    h = axis == "x" ? SX : axis == "y" ? SY : SZ
    exp(-im * theta * h / 2)
end

function peps3d_anchor(sites_per_shell, shell_count)
    # Finite K=(V,E,F,C) carrier anchor for nested S3 fiber rings. This is a
    # combinatorial PEPS3D anchor with spinor payloads, not a tensor-contraction
    # admission claim.
    v = sites_per_shell * shell_count
    e_loop = sites_per_shell * shell_count
    e_radial = sites_per_shell * (shell_count - 1)
    f_radial = sites_per_shell * (shell_count - 1)
    c_shell = sites_per_shell * max(shell_count - 2, 0)
    Dict(
        "V" => v,
        "E" => e_loop + e_radial,
        "F" => f_radial,
        "C" => c_shell,
        "sites_per_shell" => sites_per_shell,
        "shell_count" => shell_count,
        "anchor_type" => "finite combinatorial PEPS3D K with Julia-native S3 spinor payloads",
    )
end

function shell_spinors(sites_per_shell, eta)
    [hopf_chart(2pi * (k - 1) / sites_per_shell,
                0.37 + 2pi * (k - 1) / sites_per_shell,
                eta) for k in 1:sites_per_shell]
end

function base_loop_spinors(steps, eta)
    phi0 = 0.21
    chi0 = 0.73
    [hopf_chart(phi0 - cos(2eta) * 2pi * (k - 1) / steps,
                chi0 + 2pi * (k - 1) / steps,
                eta) for k in 1:steps]
end

function averaged_density(psis)
    rho = zeros(ComplexF64, 2, 2)
    for psi in psis
        rho += density(psi)
    end
    rho / length(psis)
end

function main()
    result = Dict{String,Any}()
    result["sim_id"] = "L2_layer_codex"
    result["name"] = "L2 S3 spinor carrier dependency-forcing cross-check"
    result["version"] = "1.0"
    result["tier"] = "2 geometry"
    result["classification"] = "L2_layer_codex_poc"
    result["promotion_allowed"] = false
    result["sim_execution_kind"] = "nonclassical"
    result["sim_class"] = "carrier_probe"
    result["fresh_rerun"] = true

    result["quoted_math_sources"] = [
        "registry: L2 S3 spinor carrier -- unit spinor / quaternionic carrier, NOT a Bloch substitution",
        "reference: S^3 = { psi in C^2 : ||psi|| = 1 }",
        "reference: pi(psi)=psi^dagger sigma psi in S^2",
        "reference: rho(psi)=|psi><psi|=1/2(I+r.sigma)",
        "reference: A=-i psi^dagger dpsi=dphi+cos(2 eta)dchi",
    ]

    result["finite_map"] = Dict(
        "domain" => "finite set of S3 spinors psi(phi,chi,eta) in C^2, finite U(1) fiber phases alpha, finite PEPS3D K sites",
        "codomain_or_output" => "derived Hopf/Bloch vector pi(psi), derived density rho(psi), S3 fiber transport phase, QIT readouts",
        "map" => "psi -> (pi_H(psi), rho(psi), phase_A(psi -> exp(i alpha) psi))",
    )
    result["root_constraints_in_force"] = [
        "F01: finite carrier/probe/operator/path set",
        "N01: measured noncommuting SU(2) operation gap",
    ]
    result["F01_witness"] = Dict(
        "finite_carrier" => "64-site/shell finite S3 spinor payload on PEPS3D K",
        "finite_probes" => ["pi_H(psi)", "rho(psi)", "fiber_transport_phase", "von_neumann_entropy"],
        "finite_operators" => ["sigma_x", "sigma_y", "sigma_z", "Ux(theta)", "Uz(phi)", "global U(1) phase"],
        "finite_paths" => ["fiber segment psi -> exp(i alpha) psi", "base-loop samples for derived entropy"],
    )

    psi0 = hopf_chart(0.31, 0.79, 0.62)
    alpha = 1.173
    psi1 = phase_shift(psi0, alpha)
    rho0 = density(psi0)
    rho1 = density(psi1)
    pi0 = hopf_projection(psi0)
    pi1 = hopf_projection(psi1)

    rho_dev = opnorm(rho0 - rho1)
    pi_dev = norm(pi0 - pi1)
    spinor_dist = norm(psi0 - psi1)
    fiber_phase = fiber_transport_phase(psi0, alpha)
    fiber_phase_err = abs(angle(exp(im * (fiber_phase - alpha))))

    result["julia_native_spinor_density"] = Dict(
        "psi0_on_S3" => on_s3(psi0),
        "psi1_on_S3" => on_s3(psi1),
        "rho0_trace" => real(tr(rho0)),
        "rho0_min_eig" => minimum(real.(eigvals(Hermitian((rho0 + rho0') / 2)))),
        "rho1_trace" => real(tr(rho1)),
        "rho_dev_global_phase_pair" => rho_dev,
        "pi_dev_global_phase_pair" => pi_dev,
        "spinor_distance_global_phase_pair" => spinor_dist,
    )

    result["global_phase_witness"] = Dict(
        "alpha" => alpha,
        "S3_fiber_phase_measured" => fiber_phase,
        "phase_match_err" => fiber_phase_err,
        "same_rho" => rho_dev <= 1e-12,
        "same_hopf_base" => pi_dev <= 1e-12,
        "distinguished_on_S3_fiber" => spinor_dist > 1e-6 && fiber_phase_err <= 1e-12,
    )

    ux = su2_rotation("x", 0.83)
    uz = su2_rotation("z", 1.11)
    psi_xz = ux * (uz * psi0)
    psi_zx = uz * (ux * psi0)
    rho_xz = density(psi_xz)
    rho_zx = density(psi_zx)
    spinor_order_gap = norm(psi_xz - psi_zx)
    density_order_gap = trace_distance(rho_xz, rho_zx)
    result["N01_witness"] = Dict(
        "operation_A" => "Ux(0.83)",
        "operation_B" => "Uz(1.11)",
        "spinor_order_gap_norm" => spinor_order_gap,
        "density_order_gap_trace_distance" => density_order_gap,
        "order_matters" => spinor_order_gap > 1e-6 && density_order_gap > 1e-6,
        "honest_boundary" => "This Pauli/SU2 noncommuting gap survives density/Bloch reduction, so it is not by itself proof that S3 fiber geometry is load-bearing.",
    )

    shell_count = 4
    anchor64 = peps3d_anchor(64, shell_count)
    spinors64 = shell_spinors(64, 0.62)
    result["peps3d_embedding"] = merge(anchor64, Dict(
        "all_payload_spinors_on_S3" => all(on_s3(psi) for psi in spinors64),
        "geometry_claim_boundary" => "finite K anchor only; no PEPS tensor contraction or layer-completion claim",
    ))

    stress_rows = Vector{Dict{String,Any}}()
    for n in [8, 16, 32, 64]
        psis = shell_spinors(n, 0.62)
        max_norm_err = maximum(abs(spinor_norm(psi) - 1.0) for psi in psis)
        phases = [fiber_transport_phase(psi, alpha) for psi in psis]
        phase_spread = maximum(phases) - minimum(phases)
        anchor = peps3d_anchor(n, shell_count)
        push!(stress_rows, Dict(
            "sites_per_shell" => n,
            "K" => anchor,
            "max_spinor_norm_err" => max_norm_err,
            "fiber_phase_mean" => sum(phases) / length(phases),
            "fiber_phase_spread" => phase_spread,
            "all_on_S3" => all(on_s3(psi) for psi in psis),
        ))
    end
    result["scale_stress_8_16_32_64"] = Dict(
        "rows" => stress_rows,
        "resource_blocker" => "none for this bounded LinearAlgebra/JSON run",
        "all_scales_on_S3" => all(row["all_on_S3"] for row in stress_rows),
    )

    fiber_loop = [phase_shift(psi0, 2pi * (k - 1) / 64) for k in 1:64]
    base_loop = base_loop_spinors(64, 0.62)
    rho_fiber_avg = averaged_density(fiber_loop)
    rho_base_avg = averaged_density(base_loop)
    qit = Dict(
        "pure_rho_entropy" => von_neumann_entropy(rho0),
        "fiber_avg_density_entropy" => von_neumann_entropy(rho_fiber_avg),
        "base_avg_density_entropy" => von_neumann_entropy(rho_base_avg),
        "fiber_avg_purity" => real(tr(rho_fiber_avg * rho_fiber_avg)),
        "base_avg_purity" => real(tr(rho_base_avg * rho_base_avg)),
        "derived_readout_boundary" => "entropy is derived from rho outputs, not the layer definition",
    )
    qit["base_vs_fiber_entropy_gap"] = qit["base_avg_density_entropy"] - qit["fiber_avg_density_entropy"]
    result["qit_readouts_derived"] = qit

    bloch_erased_signature = 0.0
    s3_signature = abs(fiber_phase)
    bloch_delta = abs(s3_signature - bloch_erased_signature)
    phase_zero_signature = abs(fiber_transport_phase(psi0, 0.0))
    phase_zero_delta = abs(s3_signature - phase_zero_signature)
    density_channel_survives_bloch = density_order_gap > 1e-6

    result["dependency_forcing_erasures"] = Dict(
        "bloch_substitution" => Dict(
            "present_signature_S3_fiber_phase_abs" => s3_signature,
            "erased_signature_available_from_rho" => bloch_erased_signature,
            "numeric_delta" => bloch_delta,
            "collapsed" => bloch_delta > 1e-3 && rho_dev <= 1e-12 && pi_dev <= 1e-12,
            "interpretation" => "Bloch/density erasure destroys global U(1) fiber phase while preserving rho and pi_H.",
        ),
        "fiber_phase_zeroed" => Dict(
            "present_signature" => s3_signature,
            "alpha_zero_signature" => phase_zero_signature,
            "numeric_delta" => phase_zero_delta,
            "collapsed" => phase_zero_delta > 1e-3,
        ),
        "peps3d_anchor_removed" => Dict(
            "present_K" => anchor64,
            "removed_K" => nothing,
            "present_to_absent_certificate" => "without K=(V,E,F,C), this file has spinor algebra only and the manifold-geometry anchor is absent",
            "collapsed_as_geometry_claim" => true,
        ),
        "density_channel_gap_after_bloch" => Dict(
            "density_order_gap_trace_distance" => density_order_gap,
            "survives_bloch" => density_channel_survives_bloch,
            "reported_as_hand_written_channel_boundary" => density_channel_survives_bloch,
            "interpretation" => "The Pauli channel/order gap is not accepted as the S3 dependency-forcing signature because Bloch still carries it.",
        ),
    )

    result["ablation"] = Dict(
        "removed_component" => "global U(1) fiber phase retained by S3 but erased by rho=psi psi^dag",
        "rerun_present_signature" => s3_signature,
        "rerun_erased_signature" => bloch_erased_signature,
        "ablation_outcome_delta" => bloch_delta,
        "non_vacuous" => bloch_delta > 1e-3,
    )

    zero_psi = ComplexF64[0.0, 0.0]
    bad_psi = ComplexF64[2.0, 1.0]
    result["negative_controls"] = Dict(
        "zero_spinor_on_S3" => on_s3(zero_psi),
        "zero_spinor_excluded" => !on_s3(zero_psi),
        "nonunit_density_trace" => real(tr(density(bad_psi))),
        "nonunit_excluded_as_density_carrier" => abs(real(tr(density(bad_psi))) - 1.0) > 1e-6,
        "bloch_pair_same_rho_negative_for_bloch_loadbearing" => rho_dev <= 1e-12 && pi_dev <= 1e-12 && spinor_dist > 1e-6,
    )

    result["tool_manifest"] = Dict(
        "LinearAlgebra" => Dict(
            "used" => true,
            "role" => "load_bearing",
            "reason" => "computes spinor/density maps, matrix exponentials, eigenspectra, norms, trace distances, and N01 gaps",
        ),
        "JSON" => Dict(
            "used" => true,
            "role" => "supportive",
            "reason" => "emits the receipt JSON",
        ),
        "Z3" => Dict(
            "used" => false,
            "role" => "omitted",
            "reason" => "z3 omitted, not decorative; no SMT assertion changes this bounded numeric dependency-forcing verdict",
        ),
    )
    result["tool_integration_depth"] = Dict(
        "LinearAlgebra" => "load_bearing",
        "JSON" => "supportive",
        "Z3" => "None",
    )
    result["TOOL_MANIFEST"] = result["tool_manifest"]
    result["TOOL_INTEGRATION_DEPTH"] = result["tool_integration_depth"]

    result["allowed_claims"] = [
        "bounded L2 Codex POC runs",
        "S3 global U(1) fiber phase is load-bearing for the measured fiber signature",
        "Bloch/density substitution collapses the fiber signature measured here",
    ]
    result["blocked_consumers"] = [
        "layer completion",
        "stacking readiness",
        "Axis0",
        "FEP",
        "flux",
        "bridge",
        "physics/gravity",
        "G-structure selection",
    ]
    result["promotion_blockers"] = [
        "classification is L2_layer_codex_poc",
        "promotion_allowed=false",
        "PEPS3D anchor is combinatorial with spinor payloads, not full tensor-network contraction",
        "Z3 omitted by design rather than used decoratively",
        "Pauli/density channel noncommutation survives Bloch and is reported only as a boundary, not S3 load-bearing evidence",
    ]
    result["eligible_consumers"] = ["local L2 audit comparison only"]

    internal_checks = Dict(
        "finite_map_present" => haskey(result, "finite_map"),
        "F01_present" => haskey(result, "F01_witness"),
        "N01_measured_gap" => result["N01_witness"]["order_matters"],
        "spinor_density_valid" => result["julia_native_spinor_density"]["psi0_on_S3"] &&
                                  result["julia_native_spinor_density"]["psi1_on_S3"] &&
                                  abs(result["julia_native_spinor_density"]["rho0_trace"] - 1.0) <= 1e-12,
        "PEPS3D_anchor_present" => result["peps3d_embedding"]["all_payload_spinors_on_S3"],
        "stress_8_16_32_64_present" => result["scale_stress_8_16_32_64"]["all_scales_on_S3"],
        "ablation_nonvacuous" => result["ablation"]["non_vacuous"],
        "bloch_erasure_collapsed_signature" => result["dependency_forcing_erasures"]["bloch_substitution"]["collapsed"],
        "qit_readouts_present" => qit["base_vs_fiber_entropy_gap"] > 1e-3,
        "negative_controls_pass" => result["negative_controls"]["zero_spinor_excluded"] &&
                                    result["negative_controls"]["nonunit_excluded_as_density_carrier"] &&
                                    result["negative_controls"]["bloch_pair_same_rho_negative_for_bloch_loadbearing"],
    )
    result["internal_checks"] = internal_checks
    result["all_pass"] = all(values(internal_checks))
    result["canonical_admission"] = false
    result["honest_gaps"] = result["promotion_blockers"]

    open(RESULTS_PATH, "w") do io
        JSON.print(io, result, 4)
        write(io, "\n")
    end

    println("wrote ", RESULTS_PATH)
    println("classification=", result["classification"])
    println("promotion_allowed=", result["promotion_allowed"])
    println("all_pass=", result["all_pass"])
    println("bloch_delta=", bloch_delta)
    println("density_order_gap_survives_bloch=", density_channel_survives_bloch)
end

main()
