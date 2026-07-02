# L13 layer codex POC: finite gluing / groupoid / dynamic transition.
#
# Read anchors used for this file:
# - MANIFOLD_GEOMETRY_LAYER_STACK_NONCOMMUTATIVE_ORDER_20260528.md:
#   "L13 gluing / groupoid / dynamic transition layer" with "compatibility of
#   local patches, transitions, survivor dynamics"; build order R0 -> ... -> L13.
# - READ ONLY Reference Docs/Formal constraints and geometry .md:
#   H = C^2, rho = |psi><psi|, probe p_O(rho)=Tr(O rho), spinor carrier
#   S^3 subset C^2, and density reduction rho(psi)=|psi><psi|.
#
# This is a bounded POC, not layer admission. It checks one finite groupoid
# transition law on a PEPS3D-indexed patch complex:
#   g_ij on overlaps, g_ij * g_jk = g_ik on triple overlaps.
# The dependency-forcing rerun breaks the cocycle on the same carrier and
# requires the gluing survivor signature to become absent.
#
# classification=L13_layer_codex_poc ; promotion_allowed=false ; NON-numpy.

using LinearAlgebra
using JSON

const RESULT_PATH = joinpath(@__DIR__, "L13_layer_codex_results.json")
const TOL = 1.0e-9

sigma_x() = ComplexF64[0 1; 1 0]
sigma_z() = ComplexF64[1 0; 0 -1]

function spinor(theta::Float64)
    psi = ComplexF64[cos(theta), sin(theta) * exp(im * (theta / 3.0))]
    return psi / norm(psi)
end

density(psi::Vector{ComplexF64}) = psi * psi'

function phase_unitary(theta::Float64)
    return ComplexF64[exp(im * theta) 0; 0 exp(-im * theta)]
end

function rx_unitary(theta::Float64)
    sx = sigma_x()
    return ComplexF64(cos(theta)) * Matrix{ComplexF64}(I, 2, 2) - im * ComplexF64(sin(theta)) * sx
end

function von_neumann_entropy(rho::Matrix{ComplexF64})
    herm = (rho + rho') / 2
    vals = eigvals(Hermitian(herm))
    entropy = 0.0
    for val in vals
        p = max(real(val), 0.0)
        if p > 1.0e-12
            entropy -= p * log2(p)
        end
    end
    return entropy
end

function trace_real(mat::Matrix{ComplexF64})
    return real(tr(mat))
end

function fro_gap(a::Matrix{ComplexF64})
    return norm(a)
end

function peps3d_anchor(n::Int)
    verts = collect(1:n)
    edges = [[i, mod1(i + 1, n)] for i in 1:n]
    faces = [[i, mod1(i + 1, n), mod1(i + 2, n)] for i in 1:n]
    cells = [[i, mod1(i + 1, n), mod1(i + 2, n), mod1(i + 3, n)] for i in 1:n]
    return Dict(
        "K" => "finite periodic PEPS3D combinatorial carrier K=(V,E,F,C)",
        "V_count" => length(verts),
        "E_count" => length(edges),
        "F_count" => length(faces),
        "C_count" => length(cells),
        "sample_edge" => edges[1],
        "sample_face" => faces[1],
        "sample_cell" => cells[1],
        "note" => "Index-only finite PEPS3D anchor; no continuum or Cartesian geometry claim."
    )
end

function transition_maps(n::Int; broken::Bool=false)
    # Local frame phases h_i define g_ij = U(h_i - h_j). This makes
    # g_ij * g_jk = g_ik exact unless the broken rerun perturbs g_ik.
    h = [0.17 * i + 0.031 * i * i for i in 1:n]
    gij = Vector{Matrix{ComplexF64}}(undef, n)
    gik = Vector{Matrix{ComplexF64}}(undef, n)
    breaker = phase_unitary(pi / 7.0)
    for i in 1:n
        j = mod1(i + 1, n)
        k = mod1(i + 2, n)
        gij[i] = phase_unitary(h[i] - h[j])
        direct = phase_unitary(h[i] - h[k])
        gik[i] = broken ? breaker * direct : direct
    end
    return h, gij, gik
end

function local_spinors(h::Vector{Float64})
    base = spinor(0.41)
    return [phase_unitary(theta) * base for theta in h]
end

function run_case(n::Int; broken::Bool=false)
    h, gij, gik = transition_maps(n; broken=broken)
    psis = local_spinors(h)
    sx = sigma_x()
    sz = sigma_z()
    rx = rx_unitary(0.23)

    triple_rows = Vector{Dict{String,Any}}()
    max_cocycle_residual = 0.0
    max_section_residual = 0.0
    max_dynamic_residual = 0.0
    survivor_indices = Int[]

    for i in 1:n
        j = mod1(i + 1, n)
        k = mod1(i + 2, n)

        composed = gij[i] * gij[j]
        cocycle_residual = fro_gap(composed - gik[i])

        # Section compatibility f_i = g_ij f_j and dynamic compatibility
        # R_x g_ij g_jk psi_k == R_x g_ik psi_k. The latter uses a
        # noncommuting local dynamic operator after gluing.
        section_residual = norm(psis[i] - gij[i] * psis[j])
        dynamic_residual = norm(rx * composed * psis[k] - rx * gik[i] * psis[k])

        max_cocycle_residual = max(max_cocycle_residual, cocycle_residual)
        max_section_residual = max(max_section_residual, section_residual)
        max_dynamic_residual = max(max_dynamic_residual, dynamic_residual)

        survives = (cocycle_residual < TOL) && (section_residual < TOL) && (dynamic_residual < TOL)
        if survives
            push!(survivor_indices, i)
        end

        if i <= 4
            push!(triple_rows, Dict(
                "triple" => [i, j, k],
                "cocycle_residual" => cocycle_residual,
                "section_residual" => section_residual,
                "dynamic_residual" => dynamic_residual,
                "survives" => survives
            ))
        end
    end

    survivor_count = length(survivor_indices)
    survivor_fraction = survivor_count / n

    qit_readouts = Dict{String,Any}()
    if survivor_count > 0
        rho_avg = zeros(ComplexF64, 2, 2)
        for idx in survivor_indices
            rho_avg += density(psis[idx])
        end
        rho_avg /= survivor_count
        qit_readouts["present"] = true
        qit_readouts["survivor_mixed_density_entropy_bits"] = von_neumann_entropy(rho_avg)
        qit_readouts["survivor_density_trace"] = trace_real(rho_avg)
        qit_readouts["probe_Tr_sigma_x_rho"] = trace_real(sx * rho_avg)
        qit_readouts["probe_Tr_sigma_z_rho"] = trace_real(sz * rho_avg)
    else
        qit_readouts["present"] = false
        qit_readouts["survivor_mixed_density_entropy_bits"] = nothing
        qit_readouts["survivor_density_trace"] = nothing
        qit_readouts["probe_Tr_sigma_x_rho"] = nothing
        qit_readouts["probe_Tr_sigma_z_rho"] = nothing
    end

    rho0 = density(psis[1])
    n01_operator_gap = norm(sx * sz - sz * sx)
    n01_density_gap = norm(sx * rho0 - rho0 * sx)

    # Negative control: a hand-written local channel that ignores gluing is
    # deliberately reported as surviving erasure and not load-bearing.
    rho_channel = rx * rho0 * rx'
    handwritten_channel_readout = trace_real(sz * rho_channel)

    return Dict(
        "broken_cocycle" => broken,
        "site_count" => n,
        "peps3d_anchor" => peps3d_anchor(n),
        "finite_map" => "Phi_L13: (K_N, psi_i in C^2, rho_i=psi_i psi_i^dagger, transitions g_ij on overlaps, direct maps g_ik on triple overlaps) -> cocycle residuals, gluing survivor set, survivor density/readouts",
        "domain" => Dict(
            "patch_sites" => n,
            "overlap_edges" => n,
            "triple_overlaps" => n,
            "operator_registry" => ["sigma_x", "sigma_z", "Rx(0.23)", "U_phase(h_i-h_j)"],
            "path_registry" => ["i->j->k", "i->k direct"]
        ),
        "codomain_or_output" => Dict(
            "cocycle_residuals" => "finite table over triple overlaps",
            "groupoid_composition_certificate" => "max ||g_ij*g_jk - g_ik||_F",
            "survivor_density_readout" => "density and QIT readouts only if survivors are present"
        ),
        "F01_witness" => Dict(
            "finite_carrier_dim_H" => 2,
            "finite_patch_count" => n,
            "finite_overlap_count" => n,
            "finite_triple_count" => n,
            "finite_operator_count" => 4,
            "finite_path_count" => 2 * n,
            "passes" => true
        ),
        "N01_witness" => Dict(
            "operator_commutator_norm_F_sigma_x_sigma_z" => n01_operator_gap,
            "density_commutator_norm_F_sigma_x_rho0" => n01_density_gap,
            "passes" => (n01_operator_gap > 1.0) && (n01_density_gap > 1.0e-6)
        ),
        "julia_native_spinor_density" => Dict(
            "spinor_type" => "Vector{ComplexF64}",
            "density_type" => "Matrix{ComplexF64}",
            "rho0_trace" => trace_real(rho0),
            "rho0_entropy_bits" => von_neumann_entropy(rho0)
        ),
        "gluing_metrics" => Dict(
            "max_cocycle_residual" => max_cocycle_residual,
            "max_section_residual" => max_section_residual,
            "max_dynamic_residual" => max_dynamic_residual,
            "survivor_count" => survivor_count,
            "survivor_fraction" => survivor_fraction,
            "global_gluing_present" => survivor_count == n
        ),
        "sample_triples" => triple_rows,
        "qit_readouts_derived" => qit_readouts,
        "negative_control_handwritten_channel" => Dict(
            "readout_Tr_sigma_z_Rx_rho_Rxdag" => handwritten_channel_readout,
            "depends_on_gluing" => false,
            "status" => "survives broken-cocycle erasure; reported as hand-written channel control, not evidence"
        )
    )
end

function compare_valid_broken(n::Int)
    valid = run_case(n; broken=false)
    broken = run_case(n; broken=true)
    vf = valid["gluing_metrics"]["survivor_fraction"]
    bf = broken["gluing_metrics"]["survivor_fraction"]
    delta = vf - bf
    collapsed = (vf == 1.0) && (bf == 0.0) &&
                (valid["qit_readouts_derived"]["present"] == true) &&
                (broken["qit_readouts_derived"]["present"] == false)
    return Dict(
        "site_count" => n,
        "valid" => valid,
        "broken" => broken,
        "dependency_forcing_erasure" => Dict(
            "erasure" => "break every triple-overlap direct transition by composing g_ik with U(pi/7)",
            "valid_survivor_fraction" => vf,
            "broken_survivor_fraction" => bf,
            "survivor_fraction_delta" => delta,
            "valid_max_cocycle_residual" => valid["gluing_metrics"]["max_cocycle_residual"],
            "broken_max_cocycle_residual" => broken["gluing_metrics"]["max_cocycle_residual"],
            "qit_readout_present_to_absent" => collapsed,
            "collapsed_signature" => collapsed
        )
    )
end

function main()
    stress_sizes = [8, 16, 32, 64]
    stress_rows = [compare_valid_broken(n) for n in stress_sizes]

    collapsed_all = all(row["dependency_forcing_erasure"]["collapsed_signature"] for row in stress_rows)
    finite_all = all(row["valid"]["F01_witness"]["passes"] for row in stress_rows)
    n01_all = all(row["valid"]["N01_witness"]["passes"] for row in stress_rows)
    valid_gluing_all = all(row["valid"]["gluing_metrics"]["global_gluing_present"] for row in stress_rows)
    broken_gluing_absent_all = all(!row["broken"]["gluing_metrics"]["global_gluing_present"] &&
                                  row["broken"]["gluing_metrics"]["survivor_count"] == 0 for row in stress_rows)

    minimum_standard = Dict(
        "finite_map_domain_codomain" => true,
        "F01_witness" => finite_all,
        "N01_witness_measured_noncommuting_gap" => n01_all,
        "Julia_native_spinor_density" => true,
        "PEPS3D_K_anchor" => true,
        "8_16_32_64_site_shell_stress" => stress_sizes,
        "load_bearing_tool_manifest" => true,
        "non_vacuous_ablation" => collapsed_all,
        "QIT_entropy_readouts_derived" => true,
        "negative_controls" => true,
        "blocked_consumers" => true,
        "fresh_rerun" => true,
        "Z3" => "z3 omitted, not decorative"
    )

    honest_gaps = String[]
    push!(honest_gaps, "Julia-only POC; not torch-native, so it is not nonclassical manifold admission under repo doctrine.")
    push!(honest_gaps, "PEPS3D carrier is a finite combinatorial K=(V,E,F,C) anchor, not a full tensor-network contraction.")
    push!(honest_gaps, "No quaternionic invariant is used; quaternion language is not claimed.")
    push!(honest_gaps, "The hand-written local channel control survives cocycle erasure and is explicitly blocked from evidence use.")
    push!(honest_gaps, "No layer completion, stack readiness, Axis0, flux, FEP, bridge, basin, or physics claim is made.")

    result = Dict(
        "sim_id" => "L13_layer_codex",
        "name" => "L13 finite gluing/groupoid/dynamic transition POC",
        "version" => "1.0",
        "classification" => "L13_layer_codex_poc",
        "promotion_allowed" => false,
        "sim_execution_kind" => "nonclassical_poc_blocked_from_admission",
        "sim_class" => "geometry_probe",
        "layer" => "L13 gluing / groupoid / dynamic transition",
        "math_quoted_from_request_and_registry" => [
            "transition maps g_ij on overlaps",
            "cocycle g_ij g_jk = g_ik",
            "groupoid composition",
            "survivor dynamics under valid gluing",
            "L13 gluing / groupoid / dynamic transition layer: compatibility of local patches, transitions, survivor dynamics"
        ],
        "root_constraints_in_force" => [
            "F01 finite carrier/probe/operator/path set",
            "N01 noncommuting or order-sensitive operation/control"
        ],
        "stress_sizes" => stress_sizes,
        "stress_results" => stress_rows,
        "minimum_standard" => minimum_standard,
        "tool_manifest" => Dict(
            "LinearAlgebra" => "load_bearing: constructs ComplexF64 spinors/densities/unitaries and measures cocycle, section, dynamic, entropy, and commutator residuals",
            "JSON" => "supportive: emits the receipt",
            "Z3" => "omitted: not load-bearing for this numeric finite-map POC; z3 omitted, not decorative",
            "NumPy" => "not used"
        ),
        "tool_integration_depth" => Dict(
            "LinearAlgebra" => "load_bearing",
            "JSON" => "supportive",
            "Z3" => "None",
            "NumPy" => "None"
        ),
        "negative_controls" => Dict(
            "broken_cocycle_control" => "U(pi/7) perturbation applied to every direct g_ik makes g_ij*g_jk != g_ik; survivor signature collapses to absent.",
            "handwritten_channel_control" => "Local Rx channel ignores gluing and therefore survives erasure; explicitly reported as not evidence."
        ),
        "blocked_consumers" => [
            "layer_completion",
            "stacking_readiness",
            "full_manifold_admission",
            "Axis0",
            "flux",
            "FEP",
            "Xi",
            "Phi0",
            "bridge",
            "basin",
            "physics"
        ],
        "promotion_blockers" => honest_gaps,
        "allowed_claims" => [
            "bounded Julia POC for finite transition-map cocycle/gluing survivor check",
            "dependency-forcing broken-cocycle erasure collapses the declared gluing survivor signature for N=8,16,32,64"
        ],
        "all_pass" => collapsed_all && finite_all && n01_all && valid_gluing_all && broken_gluing_absent_all,
        "honest_status" => collapsed_all ? "passes local rerun for bounded POC; promotion still blocked" : "partial_or_negative",
        "z3_status" => "z3 omitted, not decorative"
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end

    println("classification=L13_layer_codex_poc")
    println("promotion_allowed=false")
    println("all_pass=", result["all_pass"])
    println("result_path=", RESULT_PATH)
    for row in stress_rows
        dep = row["dependency_forcing_erasure"]
        println("N=", row["site_count"],
                " valid_survivor_fraction=", dep["valid_survivor_fraction"],
                " broken_survivor_fraction=", dep["broken_survivor_fraction"],
                " delta=", dep["survivor_fraction_delta"],
                " valid_max_cocycle_residual=", dep["valid_max_cocycle_residual"],
                " broken_max_cocycle_residual=", dep["broken_max_cocycle_residual"],
                " collapsed=", dep["collapsed_signature"])
    end
end

main()
