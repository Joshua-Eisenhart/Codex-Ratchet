# L1_layer_codex.jl
#
# Layer: L1 spinor/density carrier.
# Classification: L1_layer_codex_poc. promotion_allowed=false.
#
# Math read from local authority/reference docs:
# - "Hilbert carrier H = C^2" and
#   "D(C^2)={rho in B(C^2): rho >= 0, Tr(rho)=1}".
# - "rho = 1/2(I + r.sigma)".
# - "Spinor carrier S^3={psi in C^2: ||psi||=1}".
# - "rho(psi)=|psi><psi|=1/2(I+r.sigma)".
#
# Dependency forcing under test:
# erase below-geometry by keeping only diag(rho), the classical probabilities.
# The off-diagonal coherence and the state-carried N01 gap ||[sigma_z,rho]||_F
# must collapse. If they do not, this file reports a partial/negative.
#
# Z3 omitted deliberately: the decisive checks here are direct finite matrix
# measurements and removed-and-rerun deltas. An SMT wrapper would be decorative.

using LinearAlgebra
using JSON

const RESULT_PATH = joinpath(@__DIR__, "L1_layer_codex_results.json")
const TOL = 1.0e-10

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const PAULI = [SX, SY, SZ]

outer_density(psi::Vector{ComplexF64}) = psi * psi'
dephase(rho::Matrix{ComplexF64}) = ComplexF64[rho[1, 1] 0; 0 rho[2, 2]]
coherence_abs(rho::Matrix{ComplexF64}) = abs(rho[1, 2])
n01_state_gap(rho::Matrix{ComplexF64}) = norm(SZ * rho - rho * SZ)
probe_readouts(rho::Matrix{ComplexF64}) = [real(tr(P * rho)) for P in PAULI]
purity(rho::Matrix{ComplexF64}) = real(tr(rho * rho))

function entropy_vn(rho::Matrix{ComplexF64})
    vals = real.(eigvals(Hermitian(rho)))
    total = 0.0
    for x in vals
        if x > 1e-12
            total -= x * log(x)
        end
    end
    return total
end

function hopf_spinor(phi::Float64, chi::Float64, eta::Float64)
    psi = ComplexF64[
        cis(phi + chi) * cos(eta),
        cis(phi - chi) * sin(eta),
    ]
    return psi / norm(psi)
end

function site_spinor(i::Int, n::Int)
    # Deterministic finite site field: no random source, no NumPy, no planted
    # target values. eta avoids 0 and pi/2 so coherence is genuinely present.
    phi = 2pi * (i - 1) / max(n, 1)
    chi = pi * ((3i + 1) % max(n, 2)) / max(n, 2)
    eta = pi / 6 + (pi / 5) * ((i - 1) / max(n - 1, 1))
    return hopf_spinor(phi, chi, eta)
end

function cube_K()
    vertices = collect(1:8)
    edges = [
        [1, 2], [2, 3], [3, 4], [4, 1],
        [5, 6], [6, 7], [7, 8], [8, 5],
        [1, 5], [2, 6], [3, 7], [4, 8],
    ]
    faces = [
        [1, 2, 3, 4], [5, 6, 7, 8],
        [1, 2, 6, 5], [2, 3, 7, 6],
        [3, 4, 8, 7], [4, 1, 5, 8],
    ]
    cells = [[1, 2, 3, 4, 5, 6, 7, 8]]
    return Dict("V" => vertices, "E" => edges, "F" => faces, "C" => cells)
end

function summarize_carrier(n::Int)
    psis = [site_spinor(i, n) for i in 1:n]
    rhos = [outer_density(psi) for psi in psis]
    erased = [dephase(rho) for rho in rhos]

    coherences = coherence_abs.(rhos)
    erased_coherences = coherence_abs.(erased)
    gaps = n01_state_gap.(rhos)
    erased_gaps = n01_state_gap.(erased)
    entropies = entropy_vn.(rhos)
    erased_entropies = entropy_vn.(erased)
    purities = purity.(rhos)
    erased_purities = purity.(erased)
    bloch = probe_readouts.(rhos)
    erased_bloch = probe_readouts.(erased)

    return Dict(
        "site_count" => n,
        "spinor_norm_max_error" => maximum(abs(norm(psi) - 1.0) for psi in psis),
        "rho_trace_max_error" => maximum(abs(real(tr(rho)) - 1.0) for rho in rhos),
        "rho_min_eigenvalue" => minimum(minimum(real.(eigvals(Hermitian(rho)))) for rho in rhos),
        "rho_bloch_roundtrip_max_error" => maximum(begin
            r = bloch[k]
            reconstructed = 0.5 * (I2 + r[1] * SX + r[2] * SY + r[3] * SZ)
            norm(reconstructed - rhos[k])
        end for k in eachindex(rhos)),
        "coherence_max" => maximum(coherences),
        "coherence_mean" => sum(coherences) / length(coherences),
        "erased_coherence_max" => maximum(erased_coherences),
        "n01_gap_max" => maximum(gaps),
        "n01_gap_mean" => sum(gaps) / length(gaps),
        "erased_n01_gap_max" => maximum(erased_gaps),
        "erased_n01_gap_mean" => sum(erased_gaps) / length(erased_gaps),
        "n01_gap_mean_delta_removed_and_rerun" =>
            (sum(gaps) / length(gaps)) - (sum(erased_gaps) / length(erased_gaps)),
        "coherence_collapsed" => maximum(coherences) > 1e-6 && maximum(erased_coherences) < TOL,
        "n01_collapsed" => maximum(gaps) > 1e-6 && maximum(erased_gaps) < TOL,
        "entropy_pure_mean" => sum(entropies) / length(entropies),
        "entropy_erased_mean" => sum(erased_entropies) / length(erased_entropies),
        "entropy_delta_erased_minus_pure" =>
            (sum(erased_entropies) / length(erased_entropies)) -
            (sum(entropies) / length(entropies)),
        "purity_pure_mean" => sum(purities) / length(purities),
        "purity_erased_mean" => sum(erased_purities) / length(erased_purities),
        "example_bloch" => bloch[1],
        "example_erased_bloch" => erased_bloch[1],
    )
end

function main()
    primary = summarize_carrier(8)
    stress = Dict(string(n) => summarize_carrier(n) for n in [8, 16, 32, 64])

    basis0 = ComplexF64[1, 0]
    basis1 = ComplexF64[0, 1]
    rho0 = outer_density(basis0)
    rho1 = outer_density(basis1)
    identity_gap = norm(I2 * primary["n01_gap_max"] - primary["n01_gap_max"] * I2)

    operator_pair_gap = norm(SX * SZ - SZ * SX)
    diagonal_negative_gaps = [n01_state_gap(rho0), n01_state_gap(rho1)]

    collapse_all =
        primary["coherence_collapsed"] &&
        primary["n01_collapsed"] &&
        all(row["coherence_collapsed"] && row["n01_collapsed"] for row in values(stress))

    carrier_valid =
        primary["spinor_norm_max_error"] < TOL &&
        primary["rho_trace_max_error"] < TOL &&
        primary["rho_min_eigenvalue"] > -TOL &&
        primary["rho_bloch_roundtrip_max_error"] < 1e-9

    negative_controls_ok =
        maximum(diagonal_negative_gaps) < TOL &&
        identity_gap < TOL &&
        operator_pair_gap > 1e-6

    ablation_nonvacuous =
        primary["n01_gap_mean_delta_removed_and_rerun"] > 1e-6 &&
        primary["coherence_collapsed"] &&
        primary["n01_collapsed"]

    all_pass = carrier_valid && collapse_all && negative_controls_ok && ablation_nonvacuous

    honest_gaps = String[]
    if !all_pass
        push!(honest_gaps, "At least one minimum-standard check failed; inspect check_summary.")
    end
    push!(honest_gaps, "PEPS3D is a finite K=(V,E,F,C) carrier anchor with spinor payloads, not a PEPSKit contraction or promotion receipt.")
    push!(honest_gaps, "This is L1-only PoC evidence; no stacking, flux, Axis0, FEP, bridge, terrain, or full-manifold admission is claimed.")
    push!(honest_gaps, "Z3 omitted, not decorative; no load-bearing SMT variable was needed for the finite matrix collapse check.")

    result = Dict(
        "script" => "layers/L1_layer_codex.jl",
        "result_path" => RESULT_PATH,
        "classification" => "L1_layer_codex_poc",
        "promotion_allowed" => false,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "carrier_probe",
        "fresh_rerun_command" =>
            "julia --project=\"/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier\" \"/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/layers/L1_layer_codex.jl\"",
        "non_numpy" => true,
        "imports" => ["LinearAlgebra", "JSON"],
        "z3" => "z3 omitted, not decorative",
        "finite_map" =>
            "finite PEPS3D site set V carrying psi_v in C^2, ||psi_v||=1 -> rho_v=psi_v psi_v^dag in D(C^2) -> finite readouts {Tr(sigma_i rho_v), |rho_12|, ||[sigma_z,rho_v]||_F, S(rho_v)}; erasure E(rho)=diag(rho)",
        "domain" =>
            "K=(V,E,F,C) cube anchor with V=8 sites; each site carries one Julia-native ComplexF64 spinor psi_v in C^2",
        "codomain_or_output" =>
            "finite JSON receipt of density validity, Bloch/Pauli readouts, coherence, N01 commutator gaps, entropy/purity, erasure deltas, and stress rows",
        "root_constraints_in_force" => [
            "F01 finite carrier/probe/operator/path set: finite sites, finite Pauli operator set, finite erasure/control paths",
            "N01 order-sensitive state/operator relation: sigma_z*rho != rho*sigma_z exactly when rho carries off-diagonal coherence",
        ],
        "F01_witness" => Dict(
            "carrier" => "C^2 spinor per finite PEPS3D site",
            "probe_registry" => ["sigma_x", "sigma_y", "sigma_z", "coherence_abs", "commutator_gap", "entropy_vn"],
            "operator_registry" => ["I", "sigma_x", "sigma_y", "sigma_z"],
            "path_registry" => ["identity", "density_reduction", "dephase_erasure"],
            "finite_site_stress" => [8, 16, 32, 64],
        ),
        "N01_witness" => Dict(
            "measured_gap" => "||sigma_z*rho - rho*sigma_z||_F",
            "primary_gap_max" => primary["n01_gap_max"],
            "primary_gap_mean" => primary["n01_gap_mean"],
            "erased_gap_max" => primary["erased_n01_gap_max"],
            "erased_gap_mean" => primary["erased_n01_gap_mean"],
            "collapsed_under_diagonal_erasure" => primary["n01_collapsed"],
            "operator_pair_control_sigma_x_sigma_z_gap" => operator_pair_gap,
            "operator_pair_control_note" => "Pauli operators still do not commute algebraically; the state-carried L1 N01 structure collapses when rho is diagonal.",
        ),
        "carrier_realization" =>
            "Julia-native ComplexF64 spinor psi and Matrix{ComplexF64} density rho; no NumPy and no Python bridge",
        "spinor_state" => Dict(
            "psi_in_C2_norm_one" => true,
            "rho_equals_psi_psi_dagger" => true,
            "rho_equals_half_I_plus_r_dot_sigma_checked" => primary["rho_bloch_roundtrip_max_error"] < 1e-9,
        ),
        "peps3d_embedding" => Dict(
            "K" => cube_K(),
            "anchor_type" => "finite cube cell complex with spinor payload at each vertex",
            "geometry_claim_ceiling" => "carrier anchor only; no PEPS contraction or stacking admission",
        ),
        "quaternion_action" => "not_applicable: L1 request is spinor/density; no quaternion map claim is made",
        "dependency_forcing" => Dict(
            "erasure" => "rho -> diag(rho), keep only classical probabilities",
            "coherence_before_max" => primary["coherence_max"],
            "coherence_after_max" => primary["erased_coherence_max"],
            "coherence_collapsed" => primary["coherence_collapsed"],
            "n01_before_max" => primary["n01_gap_max"],
            "n01_after_max" => primary["erased_n01_gap_max"],
            "n01_collapsed" => primary["n01_collapsed"],
            "all_dependency_forcing_erasures_collapsed" => collapse_all,
        ),
        "ablation_outcome_delta" => Dict(
            "kind" => "removed_and_rerun_numeric_delta",
            "removed" => "off-diagonal coherence by dephasing rho",
            "n01_mean_gap_delta" => primary["n01_gap_mean_delta_removed_and_rerun"],
            "nonvacuous" => ablation_nonvacuous,
        ),
        "qit_readouts_derived" => Dict(
            "pure_density_entropy_mean" => primary["entropy_pure_mean"],
            "dephased_density_entropy_mean" => primary["entropy_erased_mean"],
            "entropy_delta_dephased_minus_pure" => primary["entropy_delta_erased_minus_pure"],
            "pure_density_purity_mean" => primary["purity_pure_mean"],
            "dephased_density_purity_mean" => primary["purity_erased_mean"],
            "note" => "Entropy and purity are derived readouts of rho; they do not define L1.",
        ),
        "negative_controls" => Dict(
            "basis_density_sigma_z_commutator_gaps" => diagonal_negative_gaps,
            "basis_density_gaps_zero" => maximum(diagonal_negative_gaps) < TOL,
            "identity_control_gap" => identity_gap,
            "identity_gap_zero" => identity_gap < TOL,
            "operator_pair_sigma_x_sigma_z_gap_nonzero" => operator_pair_gap,
        ),
        "scale_stress_8_16_32_64" => stress,
        "tool_manifest" => Dict(
            "LinearAlgebra" => "load_bearing: norm, eigvals, Hermitian, traces, and finite matrix commutators decide all carrier validity and collapse checks",
            "JSON" => "load_bearing: emits auditable result receipt",
            "Z3" => "omitted: z3 omitted, not decorative",
        ),
        "tool_integration_depth" => Dict(
            "LinearAlgebra" => "load_bearing",
            "JSON" => "load_bearing",
            "Z3" => "None",
        ),
        "actual_tools_used" => ["LinearAlgebra", "JSON"],
        "required_tools" => ["LinearAlgebra", "JSON"],
        "proof_surfaces_used" => ["direct finite matrix equality/inequality measurements"],
        "graph_surfaces_used" => ["finite K=(V,E,F,C) cell anchor only"],
        "topology_surfaces_used" => ["finite cell-complex carrier anchor only"],
        "divergence_log" => [],
        "promotion_status" => "keep_but_open",
        "allowed_claims" => [
            "L1 spinor-to-density carrier runs in Julia over finite ComplexF64 matrices",
            "diagonal erasure collapses off-diagonal coherence and state-carried N01 gap",
            "QIT entropy/purity are derived readouts on this carrier",
        ],
        "eligible_consumers" => [
            "bounded L2 S3 spinor carrier probes that preserve promotion_allowed=false",
            "local audit scripts checking L1 carrier fields",
        ],
        "blocked_consumers" => [
            "L2-L13 stacking readiness",
            "flux",
            "Xi",
            "Phi0",
            "Axis0",
            "FEP",
            "bridge",
            "physics/gravity",
            "final manifold admission",
        ],
        "promotion_blockers" => honest_gaps,
        "honest_gaps" => honest_gaps,
        "check_summary" => Dict(
            "carrier_valid" => carrier_valid,
            "dependency_forcing_collapses_all" => collapse_all,
            "negative_controls_ok" => negative_controls_ok,
            "ablation_nonvacuous" => ablation_nonvacuous,
            "all_pass" => all_pass,
        ),
        "all_pass" => all_pass,
        "status" => all_pass ? "passes local rerun" : "runs_with_honest_gaps",
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
    end

    println("L1_layer_codex built=true")
    println("result_path=", RESULT_PATH)
    println("classification=L1_layer_codex_poc promotion_allowed=false")
    println("coherence collapse: ", primary["coherence_max"], " -> ", primary["erased_coherence_max"],
            " collapsed=", primary["coherence_collapsed"])
    println("N01 gap collapse: ", primary["n01_gap_max"], " -> ", primary["erased_n01_gap_max"],
            " collapsed=", primary["n01_collapsed"])
    println("all_pass=", all_pass)
end

main()
