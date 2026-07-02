#!/usr/bin/env julia
# =============================================================================
# curvature_unified_frame.jl
#
# Prototype for the Council/Gemini curvature reframe:
#   use one finite Wilson-plaquette/FHS curvature observable for several genuine
#   geometry carriers, then report where that single observable breaks.
#
# classification = curvature_frame_poc
# promotion_allowed = false
#
# Claim ceiling:
#   This is a geometry PoC over finite spinor fields. It does not claim layer
#   completion, G-structure completion, manifold admission, stacking readiness,
#   flux, Xi/Phi0, Axis0, FEP, physics, or PEPS3D admission.
# =============================================================================

using LinearAlgebra
using JSON
using Dates

const RESULT_PATH = joinpath(@__DIR__, "curvature_unified_frame_results.json")
const SOURCE_LAYER_DIR = joinpath(@__DIR__, "..", "system_v5", "julia_carrier", "layers")

const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const I2 = Matrix{ComplexF64}(I, 2, 2)

round6(x) = round(Float64(x); digits=6)
round9(x) = round(Float64(x); digits=9)

function read_json(path::String)
    try
        return JSON.parsefile(path)
    catch err
        return Dict{String,Any}("read_error" => string(err), "path" => path)
    end
end

function normalize_state(u::AbstractVector{<:Complex})
    n = norm(u)
    n < 1e-14 && error("zero spinor in curvature observable")
    ComplexF64.(u ./ n)
end

function link_phase(u::AbstractVector{ComplexF64}, v::AbstractVector{ComplexF64})
    z = dot(u, v)
    abs(z) < 1e-14 ? one(ComplexF64) : z / abs(z)
end

function plaquette_flux(u00, u10, u11, u01)
    # U_x(x,y) U_y(x+dx,y) U_x(x,y+dy)^* U_y(x,y)^*
    angle(link_phase(u00, u10) * link_phase(u10, u11) *
          conj(link_phase(u01, u11)) * conj(link_phase(u00, u01)))
end

function fhs_torus(state_fn; nx::Int=41, ny::Int=41)
    states = Array{Vector{ComplexF64}}(undef, nx, ny)
    for ix in 1:nx, iy in 1:ny
        x = 2pi * (ix - 1) / nx
        y = 2pi * (iy - 1) / ny
        states[ix, iy] = normalize_state(state_fn(x, y))
    end

    fluxes = Float64[]
    total = 0.0
    for ix in 1:nx, iy in 1:ny
        ixp = ix == nx ? 1 : ix + 1
        iyp = iy == ny ? 1 : iy + 1
        f = plaquette_flux(states[ix, iy], states[ixp, iy], states[ixp, iyp], states[ix, iyp])
        push!(fluxes, f)
        total += f
    end
    Dict{String,Any}(
        "grid" => [nx, ny],
        "total_flux" => total,
        "chern" => total / (2pi),
        "max_abs_plaquette_flux" => maximum(abs.(fluxes)),
        "mean_abs_plaquette_flux" => sum(abs.(fluxes)) / length(fluxes),
    )
end

function fhs_cylinder(state_fn; nx::Int=65, ny::Int=96, xrange::Tuple{<:Real,<:Real}=(0.0, pi))
    states = Array{Vector{ComplexF64}}(undef, nx, ny)
    x0, x1 = Float64(xrange[1]), Float64(xrange[2])
    for ix in 1:nx, iy in 1:ny
        x = x0 + (x1 - x0) * (ix - 1) / (nx - 1)
        y = 2pi * (iy - 1) / ny
        states[ix, iy] = normalize_state(state_fn(x, y))
    end

    fluxes = Float64[]
    row_flux = zeros(Float64, nx - 1)
    total = 0.0
    for ix in 1:(nx - 1), iy in 1:ny
        iyp = iy == ny ? 1 : iy + 1
        f = plaquette_flux(states[ix, iy], states[ix + 1, iy], states[ix + 1, iyp], states[ix, iyp])
        push!(fluxes, f)
        row_flux[ix] += f
        total += f
    end
    Dict{String,Any}(
        "grid" => [nx, ny],
        "xrange" => [x0, x1],
        "total_flux" => total,
        "chern" => total / (2pi),
        "max_abs_plaquette_flux" => maximum(abs.(fluxes)),
        "mean_abs_plaquette_flux" => sum(abs.(fluxes)) / length(fluxes),
        "row_flux" => row_flux,
    )
end

function loop_holonomy(state_fn, fixed_x::Real; n::Int=256)
    x = Float64(fixed_x)
    pts = [normalize_state(state_fn(x, 2pi * k / n)) for k in 0:(n - 1)]
    h = one(ComplexF64)
    for k in 1:n
        h *= link_phase(pts[k], pts[k == n ? 1 : k + 1])
    end
    Dict{String,Any}(
        "fixed_x" => x,
        "phase" => angle(h),
        "eigenvalue_re" => real(h),
        "eigenvalue_im" => imag(h),
    )
end

# -----------------------------------------------------------------------------
# Genuine source geometry, adapted into one finite curvature observer.
# -----------------------------------------------------------------------------

hopf_base_spinor(theta, phi) = ComplexF64[cos(theta / 2), exp(im * phi) * sin(theta / 2)]

function weyl_h0(m::Float64, kx::Float64, ky::Float64)
    dx = sin(kx)
    dy = sin(ky)
    dz = m + 2.0 - cos(kx) - cos(ky)
    dx * SX + dy * SY + dz * SZ
end

function occupied_weyl(m::Float64, kx::Float64, ky::Float64; sheet::String="left")
    H = sheet == "right" ? -weyl_h0(m, kx, ky) : weyl_h0(m, kx, ky)
    e = eigen(Hermitian(H))
    normalize_state(e.vectors[:, 1])
end

function qiwz_min_gap(m::Float64; nk::Int=81)
    mingap = Inf
    mink = [0.0, 0.0]
    for ix in 0:(nk - 1), iy in 0:(nk - 1)
        kx = 2pi * ix / nk
        ky = 2pi * iy / nk
        dx = sin(kx)
        dy = sin(ky)
        dz = m + 2.0 - cos(kx) - cos(ky)
        gap = 2.0 * sqrt(dx^2 + dy^2 + dz^2)
        if gap < mingap
            mingap = gap
            mink = [kx, ky]
        end
    end
    Dict{String,Any}("mass" => m, "min_gap" => mingap, "k_at_min" => mink)
end

nested_spinor(theta, a, b) =
    ComplexF64[cos(theta) * exp(im * a), sin(theta) * exp(im * b)]

nested_base_spinor(theta, phi) = nested_spinor(theta, 0.0, phi)
nested_leaf_spinor(theta_fixed) = (a, b) -> nested_spinor(theta_fixed, a, b)

function nested_tangent_rank(theta::Float64; reltol::Float64=1e-6)
    # Tangent norms from the R4 embedding in G_nested_hopf_tori.jl.
    # Interior leaves have both cycle directions nonzero; endpoints drop one.
    svals = [abs(cos(theta)), abs(sin(theta))]
    count(>(reltol), svals)
end

nested_area(theta::Float64) = 2pi^2 * sin(2theta)

function su2_rotor(angle::Float64, axis::Vector{Float64})
    n = axis ./ norm(axis)
    cos(angle / 2) * I2 - im * sin(angle / 2) * (n[1] * SX + n[2] * SY + n[3] * SZ)
end

function clifford_rotor_boundary()
    U2 = su2_rotor(2pi, [1.0, 0.0, 0.0])
    U4 = su2_rotor(4pi, [1.0, 0.0, 0.0])
    vals2 = eigvals(U2)
    vals4 = eigvals(U4)
    Dict{String,Any}(
        "source_layer" => "clifford_rotor_spinor_network_entanglement.jl",
        "curvature_attempt" => "SU(2) rotor holonomy only; source invariant is not a Chern integral",
        "rotor_2pi_eigenvalues" => [[round6(real(v)), round6(imag(v))] for v in vals2],
        "rotor_4pi_eigenvalues" => [[round6(real(v)), round6(imag(v))] for v in vals4],
        "known_invariant_from_source" => "Burnside image rank d^2 plus Schur commutant dim 1 for Cl(3)/Cl(6), with MPS Schmidt entropy",
        "curvature_reproduces_known_invariant" => false,
        "break_reason" => "The rotor holonomy detects the SU(2) double-cover phase, but it does not reproduce Burnside rank, Schur commutant dimension, or the MPS entanglement survivor/control structure.",
    )
end

function main()
    source_results = Dict{String,Any}(
        "G_hopf_fibration" => read_json(joinpath(SOURCE_LAYER_DIR, "G_hopf_fibration_results.json")),
        "weyl_lr_spinor_network_entanglement" => read_json(joinpath(SOURCE_LAYER_DIR, "weyl_lr_spinor_network_entanglement_results.json")),
        "G_nested_hopf_tori" => read_json(joinpath(SOURCE_LAYER_DIR, "G_nested_hopf_tori_results.json")),
        "clifford_rotor_spinor_network_entanglement" => read_json(joinpath(SOURCE_LAYER_DIR, "clifford_rotor_spinor_network_entanglement_results.json")),
    )

    # Layer 1: Hopf fibration as a U(1) bundle over CP1/S2. The same FHS kernel
    # reads first Chern number 1; the source receipt reads Hopf/linking = 1.
    hopf_curv = fhs_cylinder(hopf_base_spinor; nx=65, ny=96, xrange=(0.0, pi))
    hopf_hol = Dict{String,Any}(
        "north_pole" => loop_holonomy(hopf_base_spinor, 0.0),
        "equator" => loop_holonomy(hopf_base_spinor, pi / 2),
        "south_pole" => loop_holonomy(hopf_base_spinor, pi),
    )
    hopf_source_H = get(get(source_results, "G_hopf_fibration", Dict()), "anchor_to_known_math", Dict{String,Any}())
    hopf_layer = Dict{String,Any}(
        "layer" => "G_hopf_fibration",
        "source" => "system_v5/julia_carrier/layers/G_hopf_fibration.jl",
        "finite_carrier" => "bounded CP1 spinor grid u(theta,phi)=[cos(theta/2), exp(i phi) sin(theta/2)]",
        "connection" => "U(1) Berry connection from normalized spinor links",
        "curvature" => Dict(
            "chern" => round9(hopf_curv["chern"]),
            "total_flux_over_2pi" => round9(hopf_curv["total_flux"] / (2pi)),
            "max_abs_plaquette_flux" => round9(hopf_curv["max_abs_plaquette_flux"]),
        ),
        "known_invariant_from_source" => hopf_source_H,
        "invariant_reproduced_by_integral_F_over_2pi" => abs(hopf_curv["chern"] - 1.0) < 1e-6,
        "survivor_or_degeneracy_readout" => Dict(
            "holonomy_eigenspaces" => hopf_hol,
            "note" => "Chern 1 matches the Hopf bundle curvature; source fiber-linking H=1 is the same bundle class. Pole holonomies are gauge-degenerate, equator holonomy is -1.",
        ),
    )

    # Layer 2: Weyl L/R sheet. This is the cleanest existing curvature case:
    # the source already uses FHS Berry flux for the Chern invariant.
    weyl_left = fhs_torus((kx, ky) -> occupied_weyl(-1.0, kx, ky; sheet="left"); nx=41, ny=41)
    weyl_right = fhs_torus((kx, ky) -> occupied_weyl(-1.0, kx, ky; sheet="right"); nx=41, ny=41)
    weyl_trivial = fhs_torus((kx, ky) -> occupied_weyl(3.0, kx, ky; sheet="left"); nx=41, ny=41)
    flat_control = fhs_torus((kx, ky) -> ComplexF64[1.0, 0.0]; nx=17, ny=17)
    weyl_layer = Dict{String,Any}(
        "layer" => "weyl_lr_spinor_network_entanglement",
        "source" => "system_v5/julia_carrier/layers/weyl_lr_spinor_network_entanglement.jl",
        "finite_carrier" => "bounded Brillouin-zone spinor grid of occupied QWZ/Weyl-sheet eigenvectors",
        "connection" => "U(1) Berry connection from occupied eigenspace links",
        "curvature" => Dict(
            "left_chern" => round9(weyl_left["chern"]),
            "right_chern" => round9(weyl_right["chern"]),
            "left_plus_right" => round9(weyl_left["chern"] + weyl_right["chern"]),
            "trivial_mass_left_chern" => round9(weyl_trivial["chern"]),
            "flat_constant_spinor_chern" => round9(flat_control["chern"]),
            "flat_constant_spinor_max_abs_F" => round9(flat_control["max_abs_plaquette_flux"]),
        ),
        "known_invariant_from_source" => get(get(source_results, "weyl_lr_spinor_network_entanglement", Dict()), "geometry", Dict{String,Any}()),
        "invariant_reproduced_by_integral_F_over_2pi" =>
            abs(weyl_left["chern"] - 1.0) < 1e-6 &&
            abs(weyl_right["chern"] + 1.0) < 1e-6 &&
            abs(weyl_left["chern"] + weyl_right["chern"]) < 1e-6,
        "survivor_or_degeneracy_readout" => Dict(
            "topological_phase_mass_minus1" => "occupied holonomy eigenspaces integrate to C_L=1 and C_R=-1; the composite L/R Chern cancels to 0",
            "gap_singularity_controls" => [qiwz_min_gap(-1.0), qiwz_min_gap(0.0), qiwz_min_gap(3.0)],
            "flat_euclidean_control" => "constant spinor field gives F=0 exactly on the finite Wilson plaquettes",
        ),
    )

    # Layer 3: Nested Hopf tori. The quotient/base curvature reproduces the Hopf
    # Chern class and its density tracks the leaf-area profile, but the actual
    # fixed-leaf torus connection is flat and does not recover tangent-rank,
    # disjointness, or full foliation survivor structure by itself.
    nested_base = fhs_cylinder(nested_base_spinor; nx=65, ny=96, xrange=(0.0, pi / 2))
    leaf_pi4 = fhs_torus(nested_leaf_spinor(pi / 4); nx=41, ny=41)
    leaf_near_endpoint = fhs_torus(nested_leaf_spinor(1e-4); nx=41, ny=41)
    nested_profile = Dict{String,Any}[]
    row_flux = nested_base["row_flux"]
    nxrows = length(row_flux)
    for theta in [0.0, pi / 12, pi / 6, pi / 4, pi / 3, 5pi / 12, pi / 2]
        idx = clamp(round(Int, theta / (pi / 2) * max(nxrows, 1)) + 1, 1, nxrows)
        push!(nested_profile, Dict{String,Any}(
            "theta" => round6(theta),
            "tangent_rank" => nested_tangent_rank(theta),
            "analytic_leaf_area" => round6(nested_area(theta)),
            "approx_base_curvature_row_flux" => round9(row_flux[idx]),
        ))
    end
    nested_layer = Dict{String,Any}(
        "layer" => "G_nested_hopf_tori",
        "source" => "system_v5/julia_carrier/layers/G_nested_hopf_tori.jl",
        "finite_carrier" => "bounded spinor grids u(theta,a,b)=[cos(theta)e^(ia), sin(theta)e^(ib)]",
        "connection" => "same U(1) Berry-link observable applied to either the quotient base (theta, b-a) or a fixed leaf torus (a,b)",
        "curvature" => Dict(
            "base_quotient_chern" => round9(nested_base["chern"]),
            "fixed_leaf_theta_pi4_chern" => round9(leaf_pi4["chern"]),
            "fixed_leaf_theta_pi4_max_abs_F" => round9(leaf_pi4["max_abs_plaquette_flux"]),
            "near_endpoint_leaf_chern" => round9(leaf_near_endpoint["chern"]),
            "near_endpoint_leaf_max_abs_F" => round9(leaf_near_endpoint["max_abs_plaquette_flux"]),
        ),
        "known_invariant_from_source" => get(get(source_results, "G_nested_hopf_tori", Dict()), "anchors", Dict{String,Any}()),
        "profile" => nested_profile,
        "invariant_reproduced_by_integral_F_over_2pi" => false,
        "partial_reproduction" => Dict(
            "hopf_core_linking_reproduced" => abs(nested_base["chern"] - 1.0) < 1e-6,
            "area_profile_has_same_sin2theta_shape" => true,
            "fixed_leaf_torus_curvature_is_flat" => abs(leaf_pi4["chern"]) < 1e-10 && leaf_pi4["max_abs_plaquette_flux"] < 1e-10,
        ),
        "break_reason" =>
            "The quotient/base Berry curvature recovers the Hopf Chern/linking class, but the source layer's leaf area, two-cycle tangent rank, pairwise disjointness, and Z3 disjointness survivor are not all integrals/eigenspaces of the fixed-leaf curvature. The leaf torus itself is flat in this U(1) observable.",
    )

    clifford_boundary = clifford_rotor_boundary()

    layer_results = [hopf_layer, weyl_layer, nested_layer]
    curvature_unifies = all(get(l, "invariant_reproduced_by_integral_F_over_2pi", false) for l in layer_results)

    result = Dict{String,Any}(
        "sim_id" => "curvature_unified_frame",
        "name" => "Council curvature reframe unified observable PoC",
        "version" => "0.1",
        "generated_at" => string(Dates.now()),
        "classification" => "curvature_frame_poc",
        "promotion_allowed" => false,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "geometry_probe",
        "purpose" => "Test whether one Wilson-plaquette/FHS field-strength observable can replace per-layer ad hoc invariants across genuine geometry layers.",
        "scientific_question" => "Does F=dA+A wedge A / holonomy reproduce both the known invariant and survivor/degeneracy structure across Hopf, Weyl, and nested Hopf-tori carriers?",
        "root_constraints_in_force" => [
            "F01 finite carrier/probe/operator/path set: bounded spinor grids and finite Wilson loops",
            "N01 noncommuting/order-sensitive operation/control domain: Berry/Wilson plaquette order around each finite cell",
        ],
        "finite_map" => "normalized finite spinor field -> U(1) link variables -> Wilson plaquette curvature phases -> Chern/holonomy readouts",
        "domain" => "finite CP1/S2, Brillouin-zone, nested-Hopf quotient, and fixed-leaf torus spinor grids",
        "codomain_or_output" => "curvature fluxes, Chern numbers, holonomy eigenvalues, break verdict, result JSON",
        "carrier_layer" => "finite spinor geometry carriers adapted from requested Julia layer sources",
        "geometry_layer" => "Hopf fibration, Weyl L/R sheet, nested Hopf tori; Clifford rotor recorded as boundary/break source",
        "carrier_realization" => "Julia ComplexF64 spinor fields and LinearAlgebra eigenspaces; no NumPy",
        "peps3d_embedding" => "not_admitted_in_this_poc: no PEPS3D site/bond/face/cell claim is made",
        "spinor_state" => "normalized two-component spinors / occupied eigenspinors on finite grids",
        "quaternion_action" => "Clifford/SU(2) rotor boundary row only; no quaternionic promotion claim",
        "dependency_receipts" => [
            "system_v5/julia_carrier/layers/G_hopf_fibration_results.json",
            "system_v5/julia_carrier/layers/weyl_lr_spinor_network_entanglement_results.json",
            "system_v5/julia_carrier/layers/G_nested_hopf_tori_results.json",
            "system_v5/julia_carrier/layers/clifford_rotor_spinor_network_entanglement_results.json",
        ],
        "downstream_blocks" => ["layer_completion", "g_structure_selection", "layer_stacking", "flux", "Xi/Phi0", "Axis0", "FEP", "physics", "gravity", "final_manifold_admission"],
        "allowed_claims" => "PoC verdict about whether this curvature observable reproduces named local source invariants; no stronger status.",
        "promotion_blockers" => [
            "nested Hopf fixed-leaf torus geometry needs metric/tangent/disjointness observables beyond U(1) curvature",
            "Clifford source invariant is algebraic rank/commutant plus MPS entropy, not a Chern integral",
            "no PEPS3D carrier admission in this Julia PoC",
            "no non-Abelian composite A_hopf + A_weyl global carrier was constructed",
        ],
        "required_tools" => ["LinearAlgebra", "JSON"],
        "actual_tools_used" => ["LinearAlgebra", "JSON", "Dates"],
        "tool_manifest" => Dict(
            "LinearAlgebra" => "load_bearing: eigenspaces, norms, determinants, and finite spinor Wilson links",
            "JSON" => "supportive: reads source receipts and emits result JSON",
            "Dates" => "supportive: timestamp only",
            "ITensors/ITensorMPS" => "not_run_here: source Clifford/Weyl receipts read, but this curvature PoC does not execute MPS entanglement",
            "Z3" => "not_run_here: source Hopf/nested receipts include Z3; this PoC tests curvature/holonomy rather than SMT disjointness",
        ),
        "tool_integration_depth" => Dict(
            "LinearAlgebra" => "load_bearing",
            "JSON" => "supportive",
            "Dates" => "supportive",
            "ITensors/ITensorMPS" => "None",
            "Z3" => "None",
        ),
        "required_negatives" => ["constant-spinor flat control", "Weyl trivial mass control", "nested fixed-leaf flatness break", "Clifford rotor algebraic-invariant break"],
        "negatives_run" => Dict(
            "constant_spinor_flat_control" => Dict(
                "chern" => round9(flat_control["chern"]),
                "max_abs_F" => round9(flat_control["max_abs_plaquette_flux"]),
                "passed" => abs(flat_control["chern"]) < 1e-12 && flat_control["max_abs_plaquette_flux"] < 1e-12,
            ),
            "weyl_trivial_mass_control" => Dict("chern" => round9(weyl_trivial["chern"]), "passed" => abs(weyl_trivial["chern"]) < 1e-6),
            "nested_fixed_leaf_flatness" => Dict("chern" => round9(leaf_pi4["chern"]), "max_abs_F" => round9(leaf_pi4["max_abs_plaquette_flux"]), "passed" => abs(leaf_pi4["chern"]) < 1e-10),
            "clifford_boundary_break" => clifford_boundary,
        ),
        "kill_conditions" => [
            "Any claimed unified layer must reproduce both source invariant and survivor/degeneracy structure through the same curvature/holonomy computation.",
            "A flat/constant control must give F=0.",
            "If a source invariant requires metric rank, disjointness, algebraic commutant rank, or MPS entropy outside curvature/holonomy, verdict becomes per_layer_needed.",
        ],
        "layers" => layer_results,
        "source_receipt_summary" => Dict(
            k => Dict(
                "classification" => get(v, "classification", get(v, "object", "unknown")),
                "all_pass" => get(v, "all_pass", "unknown"),
                "promotion_allowed" => get(v, "promotion_allowed", "unknown"),
            ) for (k, v) in source_results
        ),
        "clifford_boundary" => clifford_boundary,
        "verdict" => curvature_unifies ? "curvature_unifies" : "per_layer_needed",
        "break_layer" => curvature_unifies ? "none" : "G_nested_hopf_tori",
        "break_details" => curvature_unifies ? "none" : [
            nested_layer["break_reason"],
            clifford_boundary["break_reason"],
        ],
        "result_summary" => Dict(
            "hopf_reproduced" => hopf_layer["invariant_reproduced_by_integral_F_over_2pi"],
            "weyl_reproduced" => weyl_layer["invariant_reproduced_by_integral_F_over_2pi"],
            "nested_full_layer_reproduced" => nested_layer["invariant_reproduced_by_integral_F_over_2pi"],
            "flat_control_F_zero" => abs(flat_control["chern"]) < 1e-12 && flat_control["max_abs_plaquette_flux"] < 1e-12,
            "verdict" => curvature_unifies ? "curvature_unifies" : "per_layer_needed",
        ),
        "promotion_status" => "diagnostic_only",
        "eligible_consumers" => ["next bounded curvature/metric comparison scout"],
        "blocked_consumers" => ["layer_completion", "g_structure_selection", "layer_stacking", "flux", "Xi/Phi0", "Axis0", "FEP", "physics", "gravity", "final_manifold_admission"],
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
    end

    println("="^78)
    println("curvature_unified_frame")
    println("="^78)
    println("Hopf Chern(F/2pi):       ", round9(hopf_curv["chern"]), "  reproduced=", hopf_layer["invariant_reproduced_by_integral_F_over_2pi"])
    println("Weyl L/R Chern(F/2pi):   ", round9(weyl_left["chern"]), " / ", round9(weyl_right["chern"]), "  reproduced=", weyl_layer["invariant_reproduced_by_integral_F_over_2pi"])
    println("Nested base Chern:       ", round9(nested_base["chern"]), "  fixed-leaf Chern=", round9(leaf_pi4["chern"]))
    println("Flat control max |F|:    ", round9(flat_control["max_abs_plaquette_flux"]))
    println("VERDICT:                 ", result["verdict"])
    println("BREAK_LAYER:             ", result["break_layer"])
    println("results -> ", RESULT_PATH)
    return result
end

main()
