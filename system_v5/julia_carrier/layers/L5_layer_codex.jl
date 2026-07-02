# L5_layer_codex.jl
#
# GEOMETRY-MANIFOLD LAYER L5 : nested Hopf tori / torus leaf family
#
# Registry read: system_v5/ops/MANIFOLD_GEOMETRY_LAYER_STACK_NONCOMMUTATIVE_ORDER_20260528.md
# Reference read: system_v5/READ ONLY Reference Docs/Formal constraints and geometry .md
# Reference read: system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md
#
# Quoted controlling math used here:
#   T_eta_k = {(e^{i phi} cos eta_k, e^{i chi} sin eta_k)}
#   A(eta) = 2 pi^2 sin(2 eta)
#   T_eta = {(e^{i alpha} cos eta, e^{i beta} sin eta): alpha,beta in S^1} subset S^3
#
# classification = L5_layer_codex_poc ; promotion_allowed = false ; NON-numpy.
#
# This is a local Julia proof-of-concept, not layer completion or admission. It
# carries the below-geometry explicitly enough to test the dependency-forcing
# erasure requested by the user: collapse torus index k to one eta and rerun the
# signature. If the nested leaf-area / density-entropy ladder survives, this file
# must report failure.

using LinearAlgebra
using JSON

const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const I2 = Matrix{ComplexF64}(I, 2, 2)
const TOL = 1.0e-9

struct PEPS3DAnchor
    k_shells::Int
    nphi::Int
    nchi::Int
    V::Int
    E::Int
    F::Int
    C::Int
    euler::Int
end

function peps3d_anchor(k_shells::Int, nphi::Int, nchi::Int)
    grid = k_shells * nphi * nchi
    torus_edges = 2 * grid
    radial_edges = (k_shells - 1) * nphi * nchi
    torus_faces = grid
    radial_faces = 2 * (k_shells - 1) * nphi * nchi
    cells = (k_shells - 1) * nphi * nchi
    V = grid
    E = torus_edges + radial_edges
    F = torus_faces + radial_faces
    C = cells
    PEPS3DAnchor(k_shells, nphi, nchi, V, E, F, C, V - E + F - C)
end

function anchor_dict(K::PEPS3DAnchor)
    Dict(
        "K_tuple" => Dict("V" => K.V, "E" => K.E, "F" => K.F, "C" => K.C),
        "k_shells" => K.k_shells,
        "nphi" => K.nphi,
        "nchi" => K.nchi,
        "euler_V_minus_E_plus_F_minus_C" => K.euler,
        "geometry_claim" => "finite torus-leaf stack with torus plaquettes, radial leaf edges/faces, and 3-cells between adjacent eta leaves",
        "peps3d_role" => "anchor only: finite PEPS3D-style K=(V,E,F,C) carrier for the L5 leaf family; no PEPSKit tensor contraction claimed"
    )
end

leaf_area(eta::Float64) = 2.0 * pi^2 * sin(2.0 * eta)

function eta_ladder(k_shells::Int)
    lo = 0.08
    hi = 0.72
    if k_shells == 1
        return [0.5 * (lo + hi)]
    end
    [lo + (hi - lo) * (j - 1) / (k_shells - 1) for j in 1:k_shells]
end

function spinor(phi::Float64, chi::Float64, eta::Float64)
    ComplexF64[cis(phi) * cos(eta), cis(chi) * sin(eta)]
end

function density(psi::Vector{ComplexF64})
    psi * psi'
end

function leaf_density(eta::Float64, nphi::Int, nchi::Int)
    rho = zeros(ComplexF64, 2, 2)
    for a in 0:(nphi - 1)
        phi = 2.0 * pi * a / nphi
        for b in 0:(nchi - 1)
            chi = 2.0 * pi * b / nchi
            rho .+= density(spinor(phi, chi, eta))
        end
    end
    rho ./ (nphi * nchi)
end

function vn_entropy(rho::Matrix{ComplexF64})
    herm = Hermitian((rho + rho') / 2)
    vals = eigvals(herm)
    total = 0.0
    for raw in vals
        p = max(real(raw), 0.0)
        if p > 1.0e-12
            total -= p * log(p)
        end
    end
    total
end

function purity(rho::Matrix{ComplexF64})
    real(tr(rho * rho))
end

function unique_count_rounded(xs::Vector{Float64}; digits::Int=12)
    length(unique(round.(xs; digits=digits)))
end

function range_value(xs::Vector{Float64})
    maximum(xs) - minimum(xs)
end

function mean_value(xs::Vector{Float64})
    sum(xs) / length(xs)
end

function std_value(xs::Vector{Float64})
    m = mean_value(xs)
    sqrt(sum((x - m)^2 for x in xs) / length(xs))
end

function increasing_strict(xs::Vector{Float64})
    all(xs[i] < xs[i + 1] for i in 1:(length(xs) - 1))
end

function unitary(axis::Symbol, theta::Float64)
    sigma = axis == :x ? SX : axis == :y ? SY : SZ
    cos(theta / 2.0) * I2 - im * sin(theta / 2.0) * sigma
end

function apply_unitary(U::Matrix{ComplexF64}, rho::Matrix{ComplexF64})
    U * rho * U'
end

function order_gap_for_density(rho::Matrix{ComplexF64})
    Ux = unitary(:x, 0.71)
    Uz = unitary(:z, 0.43)
    ab = apply_unitary(Ux, apply_unitary(Uz, rho))
    ba = apply_unitary(Uz, apply_unitary(Ux, rho))
    norm(ab - ba)
end

function abelian_control_gap_for_density(rho::Matrix{ComplexF64})
    U1 = unitary(:x, 0.71)
    U2 = unitary(:x, 0.43)
    ab = apply_unitary(U1, apply_unitary(U2, rho))
    ba = apply_unitary(U2, apply_unitary(U1, rho))
    norm(ab - ba)
end

function l5_signature(k_shells::Int, nphi::Int, nchi::Int; collapse_eta::Bool=false)
    etas = eta_ladder(k_shells)
    if collapse_eta
        collapsed = mean_value(etas)
        etas = fill(collapsed, k_shells)
    end
    areas = leaf_area.(etas)
    rhos = [leaf_density(eta, nphi, nchi) for eta in etas]
    entropies = [vn_entropy(rho) for rho in rhos]
    purities = [purity(rho) for rho in rhos]
    order_gaps = [order_gap_for_density(rho) for rho in rhos]
    abelian_gaps = [abelian_control_gap_for_density(rho) for rho in rhos]

    Dict(
        "k_shells" => k_shells,
        "nphi" => nphi,
        "nchi" => nchi,
        "eta_values" => etas,
        "eta_distinct_count" => unique_count_rounded(etas),
        "eta_range" => range_value(etas),
        "eta_strictly_increasing" => collapse_eta ? false : increasing_strict(etas),
        "leaf_areas" => areas,
        "leaf_area_distinct_count" => unique_count_rounded(areas),
        "leaf_area_range" => range_value(areas),
        "leaf_area_std" => std_value(areas),
        "leaf_area_ladder_strictly_increasing" => collapse_eta ? false : increasing_strict(areas),
        "density_trace_max_error" => maximum(abs(real(tr(rho)) - 1.0) for rho in rhos),
        "density_hermitian_max_error" => maximum(norm(rho - rho') for rho in rhos),
        "density_purities" => purities,
        "derived_von_neumann_entropies" => entropies,
        "derived_entropy_range" => range_value(entropies),
        "derived_entropy_std" => std_value(entropies),
        "N01_order_gap_mean" => mean_value(order_gaps),
        "N01_order_gap_min" => minimum(order_gaps),
        "N01_order_gap_max" => maximum(order_gaps),
        "abelian_negative_control_gap_max" => maximum(abelian_gaps)
    )
end

function stress_row(k_shells::Int)
    nphi = 8
    nchi = 8
    present = l5_signature(k_shells, nphi, nchi; collapse_eta=false)
    collapsed = l5_signature(k_shells, nphi, nchi; collapse_eta=true)
    K = peps3d_anchor(k_shells, nphi, nchi)

    area_delta = present["leaf_area_range"] - collapsed["leaf_area_range"]
    entropy_delta = present["derived_entropy_range"] - collapsed["derived_entropy_range"]
    eta_delta = present["eta_range"] - collapsed["eta_range"]
    distinct_delta = present["eta_distinct_count"] - collapsed["eta_distinct_count"]
    collapsed_ok = area_delta > 1.0e-6 &&
                   entropy_delta > 1.0e-6 &&
                   eta_delta > 1.0e-6 &&
                   distinct_delta == k_shells - 1 &&
                   collapsed["leaf_area_range"] < 1.0e-12 &&
                   collapsed["derived_entropy_range"] < 1.0e-12

    Dict(
        "shells" => k_shells,
        "peps3d_anchor" => anchor_dict(K),
        "present_signature" => present,
        "collapsed_k_to_single_eta_signature" => collapsed,
        "dependency_forcing_collapse" => Dict(
            "erasure" => "collapse torus index k to one eta and rerun",
            "eta_range_delta" => eta_delta,
            "distinct_eta_delta" => distinct_delta,
            "leaf_area_range_present" => present["leaf_area_range"],
            "leaf_area_range_collapsed" => collapsed["leaf_area_range"],
            "leaf_area_range_delta" => area_delta,
            "derived_entropy_range_present" => present["derived_entropy_range"],
            "derived_entropy_range_collapsed" => collapsed["derived_entropy_range"],
            "derived_entropy_range_delta" => entropy_delta,
            "collapsed" => collapsed_ok,
            "interpretation" => collapsed_ok ?
                "The L5 nested leaf-family signature is forced by k/eta geometry for this finite stress size." :
                "The L5 signature survived k-erasure; that would be hand-written-channel behavior."
        )
    )
end

function reversed_order_control(k_shells::Int)
    etas = reverse(eta_ladder(k_shells))
    areas = leaf_area.(etas)
    Dict(
        "control" => "reverse eta order",
        "eta_strictly_increasing" => increasing_strict(etas),
        "leaf_area_ladder_strictly_increasing" => increasing_strict(areas),
        "area_range_survives_but_nested_order_fails" => range_value(areas) > 1.0e-6 && !increasing_strict(etas),
        "meaning" => "area values alone are not enough; L5 requires nested eta_1 < eta_2 < ... < eta_K"
    )
end

stress_sizes = [8, 16, 32, 64]
stress = [stress_row(k) for k in stress_sizes]
primary = stress[end]
primary_present = primary["present_signature"]
primary_collapsed = primary["collapsed_k_to_single_eta_signature"]
primary_collapse = primary["dependency_forcing_collapse"]
neg_order = reversed_order_control(64)

all_dependency_erasures_collapsed = all(row["dependency_forcing_collapse"]["collapsed"] for row in stress)
n01_ok = primary_present["N01_order_gap_min"] > 1.0e-6 &&
         primary_present["abelian_negative_control_gap_max"] < 1.0e-10
densities_ok = primary_present["density_trace_max_error"] < 1.0e-10 &&
               primary_present["density_hermitian_max_error"] < 1.0e-10
peps_ok = all(row["peps3d_anchor"]["euler_V_minus_E_plus_F_minus_C"] == 0 for row in stress)
stress_ok = length(stress) == 4 && all(row["shells"] in stress_sizes for row in stress)
negative_controls_ok = neg_order["area_range_survives_but_nested_order_fails"] &&
                       primary_present["abelian_negative_control_gap_max"] < 1.0e-10

all_pass = all_dependency_erasures_collapsed &&
           n01_ok &&
           densities_ok &&
           peps_ok &&
           stress_ok &&
           negative_controls_ok

results = Dict(
    "sim_id" => "L5_layer_codex",
    "name" => "L5 nested Hopf tori / torus leaf family dependency-forcing POC",
    "version" => "1.0",
    "classification" => "L5_layer_codex_poc",
    "promotion_allowed" => false,
    "all_pass" => all_pass,
    "status" => all_pass ? "passes local rerun as bounded POC; not admitted; promotion blocked" : "partial_or_failed_poc",
    "fresh_rerun" => true,
    "run_epoch_seconds" => floor(Int, time()),
    "wizard_or_subagent_note" => "No subagents or collaborative mode were used, per current user hard constraint.",
    "quoted_math" => Dict(
        "registry" => "K=(V,E,F,C); psi_v in S^3 subset C^2; T_eta_k = {(e^{i phi} cos eta_k, e^{i chi} sin eta_k)}",
        "reference_torus_family" => "T_eta={(e^{i alpha} cos eta, e^{i beta} sin eta): alpha,beta in S^1} subset S^3",
        "user_area_law" => "A(eta)=2 pi^2 sin(2 eta); nested eta_1<eta_2<...<eta_K"
    ),
    "finite_map" => Dict(
        "domain" => "finite PEPS3D K=(V,E,F,C) torus-leaf stack with k in {1..K}, phi/chi finite grids, eta_k ladder, Julia ComplexF64 spinors psi(k,phi,chi) in S^3 subset C^2, Pauli rotation probes",
        "map" => "F: (K, eta_k, phi_i, chi_j) -> {T_eta_k spinors, leaf area A(eta_k), averaged density rho_k, derived entropy S(rho_k), N01 order gaps}",
        "codomain_or_output" => "finite L5 signature record: eta ladder, leaf-area ladder, density/entropy ladder, PEPS3D counts, ablation/collapse certificate"
    ),
    "root_constraints_in_force" => [
        "F01 finite carrier/probe/operator/path set: finite K shells, finite phi/chi samples, finite spinor/density set, finite Pauli operator probes",
        "N01 noncommuting/order-sensitive operation: measured Ux∘Uz versus Uz∘Ux density gap with same-axis abelian negative control"
    ],
    "F01_witness" => Dict(
        "finite_shell_stress" => stress_sizes,
        "finite_phi_samples_per_shell" => 8,
        "finite_chi_samples_per_shell" => 8,
        "primary_site_count" => 64 * 8 * 8,
        "primary_peps3d_anchor" => primary["peps3d_anchor"],
        "finite_operator_set" => ["sigma_x", "sigma_z", "Ux(0.71)", "Uz(0.43)"]
    ),
    "N01_witness" => Dict(
        "measured_noncommuting_gap_mean_primary" => primary_present["N01_order_gap_mean"],
        "measured_noncommuting_gap_min_primary" => primary_present["N01_order_gap_min"],
        "measured_noncommuting_gap_max_primary" => primary_present["N01_order_gap_max"],
        "abelian_same_axis_negative_control_gap_max" => primary_present["abelian_negative_control_gap_max"],
        "noncommuting_gap_present" => n01_ok
    ),
    "julia_native_spinor_density" => Dict(
        "spinor_type" => "Vector{ComplexF64}",
        "density_type" => "Matrix{ComplexF64}",
        "numpy_used" => false,
        "density_trace_max_error_primary" => primary_present["density_trace_max_error"],
        "density_hermitian_max_error_primary" => primary_present["density_hermitian_max_error"]
    ),
    "peps3d_anchor" => primary["peps3d_anchor"],
    "stress_8_16_32_64" => stress,
    "ablation" => Dict(
        "kind" => "removed_and_rerun_numeric_delta",
        "required_erasure" => "collapse torus index k to a single eta",
        "primary_erasure_result" => primary_collapse,
        "all_stress_sizes_collapsed" => all_dependency_erasures_collapsed,
        "hand_written_channel_warning_triggered" => !all_dependency_erasures_collapsed
    ),
    "qit_readouts_derived" => Dict(
        "source" => "rho_k is derived from finite spinor samples on T_eta_k; entropy is read out from rho_k, not used as a primary geometric object",
        "primary_entropy_range_present" => primary_present["derived_entropy_range"],
        "primary_entropy_range_collapsed" => primary_collapsed["derived_entropy_range"],
        "primary_density_purity_minmax_present" => [minimum(primary_present["density_purities"]), maximum(primary_present["density_purities"])]
    ),
    "negative_controls" => Dict(
        "same_axis_abelian_order_control" => Dict(
            "gap_max" => primary_present["abelian_negative_control_gap_max"],
            "passed" => primary_present["abelian_negative_control_gap_max"] < 1.0e-10
        ),
        "reverse_eta_order_control" => neg_order,
        "single_eta_collapse_control" => primary_collapse
    ),
    "tool_manifest" => Dict(
        "LinearAlgebra" => "load-bearing: Hermitian eigvals produce derived von Neumann entropy; matrix norms/traces test density and N01 order gaps",
        "JSON" => "artifact emission only",
        "Z3" => "z3 omitted, not decorative: L5 decisive claim is numeric dependency erasure of the measured eta/area/entropy ladder, not an SMT structural theorem in this POC"
    ),
    "tool_integration_depth" => Dict(
        "LinearAlgebra" => "load_bearing",
        "JSON" => "supportive",
        "Z3" => "None"
    ),
    "divergence_log" => [
        "single eta erasure rerun collapses eta range, leaf-area range, and derived entropy range to zero",
        "reversed eta order preserves area range but fails eta_1 < eta_2 < ... < eta_K, so unordered areas do not count as L5 nesting",
        "same-axis unitary control collapses the N01 order gap"
    ],
    "blocked_consumers" => [
        "flux",
        "Xi",
        "Phi0",
        "Axis0",
        "bridge",
        "basin",
        "physics",
        "terrain generator promotion",
        "layer completion",
        "G-structure admission"
    ],
    "eligible_consumers" => [
        "bounded follow-up L5 audits that preserve classification=L5_layer_codex_poc and promotion_allowed=false"
    ],
    "honest_gaps" => [
        "No PEPSKit tensor contraction or full tensor-network optimization is claimed; K=(V,E,F,C) is a finite carrier anchor only.",
        "No Z3 theorem is included because a non-decorative SMT encoding was not needed for the numeric erasure claim.",
        "This is Julia-native per request, not torch-native; repo nonclassical promotion remains blocked.",
        "No layer-completion claim gate was run because this file does not claim L5 completion or admission."
    ],
    "verification" => Dict(
        "classification_exact" => "L5_layer_codex_poc",
        "promotion_allowed_false" => true,
        "all_dependency_erasures_collapsed" => all_dependency_erasures_collapsed,
        "N01_noncommuting_gap_present_and_control_absent" => n01_ok,
        "densities_valid" => densities_ok,
        "peps3d_anchor_present" => peps_ok,
        "stress_8_16_32_64_present" => stress_ok,
        "negative_controls_pass" => negative_controls_ok
    )
)

outpath = joinpath(@__DIR__, "L5_layer_codex_results.json")
open(outpath, "w") do io
    JSON.print(io, results, 2)
    println(io)
end

println("L5_layer_codex")
println("classification=L5_layer_codex_poc promotion_allowed=false")
println("dependency erasure: collapse k->single eta")
println("primary area range: present=", primary_present["leaf_area_range"], " collapsed=", primary_collapsed["leaf_area_range"], " delta=", primary_collapse["leaf_area_range_delta"])
println("primary entropy range: present=", primary_present["derived_entropy_range"], " collapsed=", primary_collapsed["derived_entropy_range"], " delta=", primary_collapse["derived_entropy_range_delta"])
println("N01 gap mean=", primary_present["N01_order_gap_mean"], " abelian_control_max=", primary_present["abelian_negative_control_gap_max"])
println("ALL_PASS=", all_pass)
println("wrote ", outpath)
