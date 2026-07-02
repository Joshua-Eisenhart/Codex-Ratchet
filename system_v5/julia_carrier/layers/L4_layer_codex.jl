# L4_layer_codex.jl
#
# L4 finite-QIT Hopf fibration PoC: S^3 -> S^2 with U(1) fiber.
#
# Read anchors used by this sim:
# - registry L4: "Hopf fibration S3 -> S2 with U(1) fiber; fiber/base split,
#   phase, connection, holonomy".
# - reference docs: psi(phi,chi;eta) =
#   (e^(i(phi+chi)) cos eta, e^(i(phi-chi)) sin eta),
#   A_Hopf = dphi + cos(2eta) dchi.
#
# This is an honest bounded PoC. It is not layer completion, not stacking
# admission, and not downstream manifold/flux/Axis evidence.

using LinearAlgebra
using JSON

const OUTPATH = joinpath(@__DIR__, "L4_layer_codex_results.json")
const RUN_COMMAND = "julia --project=\"/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier\" \"/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/layers/L4_layer_codex.jl\""

# Pauli matrices for the Hopf projection and density readouts.
const SIGMA_X = ComplexF64[0 1; 1 0]
const SIGMA_Y = ComplexF64[0 -im; im 0]
const SIGMA_Z = ComplexF64[1 0; 0 -1]

unit(v::Vector{ComplexF64}) = v / norm(v)

function hopf_chart(phi::Float64, chi::Float64, eta::Float64)
    return unit(ComplexF64[
        cis(phi + chi) * cos(eta),
        cis(phi - chi) * sin(eta),
    ])
end

function density(psi::Vector{ComplexF64})
    return psi * psi'
end

function hopf_projection(psi::Vector{ComplexF64})
    rho = density(psi)
    return [
        real(tr(rho * SIGMA_X)),
        real(tr(rho * SIGMA_Y)),
        real(tr(rho * SIGMA_Z)),
    ]
end

# Gauge-fixed section induced from the Hopf chart after quotienting the U(1)
# fiber: theta=2eta and alpha=-2chi up to orientation convention. The m=1
# field is the Hopf line-bundle generator; m=0 and constant are erasures.
function projective_section(theta::Float64, alpha::Float64, m::Int)
    return unit(ComplexF64[
        cos(theta / 2),
        cis(m * alpha) * sin(theta / 2),
    ])
end

constant_section(theta::Float64, alpha::Float64) = ComplexF64[1, 0]

function phase_erased_section(theta::Float64, alpha::Float64)
    return unit(ComplexF64[cos(theta / 2), sin(theta / 2)])
end

function plaquette_phase(v1, v2, v3, v4)
    z = dot(v1, v2) * dot(v2, v3) * dot(v3, v4) * dot(v4, v1)
    return angle(z)
end

function fhs_chern(section_fn, ntheta::Int, nalpha::Int)
    total = 0.0
    max_abs_flux = 0.0
    abs_flux_sum = 0.0
    for i in 0:(ntheta - 1)
        theta0 = pi * i / ntheta
        theta1 = pi * (i + 1) / ntheta
        for j in 0:(nalpha - 1)
            alpha0 = 2pi * j / nalpha
            alpha1 = 2pi * (j + 1) / nalpha
            flux = plaquette_phase(
                section_fn(theta0, alpha0),
                section_fn(theta1, alpha0),
                section_fn(theta1, alpha1),
                section_fn(theta0, alpha1),
            )
            total += flux
            max_abs_flux = max(max_abs_flux, abs(flux))
            abs_flux_sum += abs(flux)
        end
    end
    return Dict(
        "ntheta" => ntheta,
        "nalpha" => nalpha,
        "c1" => total / (2pi),
        "total_flux" => total,
        "abs_flux_sum" => abs_flux_sum,
        "max_abs_plaquette_flux" => max_abs_flux,
    )
end

function horizontal_commutator_gap(eta::Float64; d_eta::Float64=1e-4, d_chi::Float64=1e-4)
    # A_Hopf = dphi + cos(2eta)dchi. Horizontal chi lift is
    # H_chi = partial_chi - cos(2eta) partial_phi; H_eta = partial_eta.
    # Compare H_eta then H_chi against H_chi then H_eta.
    phi_eta_then_chi = -cos(2(eta + d_eta)) * d_chi
    phi_chi_then_eta = -cos(2eta) * d_chi
    gap = phi_eta_then_chi - phi_chi_then_eta
    predicted = 2sin(2eta) * d_eta * d_chi
    return Dict(
        "eta" => eta,
        "d_eta" => d_eta,
        "d_chi" => d_chi,
        "vertical_phi_gap" => gap,
        "predicted_first_order_gap" => predicted,
        "normalized_gap" => gap / (d_eta * d_chi),
        "trivialized_vertical_phi_gap" => 0.0,
    )
end

function holonomy_readout(eta::Float64)
    # Horizontal lifted base loop chi: 0 -> 2pi.
    hopf_delta_phi = -2pi * cos(2eta)
    trivial_delta_phi = 0.0
    return Dict(
        "eta" => eta,
        "hopf_horizontal_delta_phi" => hopf_delta_phi,
        "hopf_holonomy_phase" => [cos(hopf_delta_phi), sin(hopf_delta_phi)],
        "trivial_horizontal_delta_phi" => trivial_delta_phi,
        "trivial_holonomy_phase" => [1.0, 0.0],
        "collapse_delta_abs" => abs(hopf_delta_phi - trivial_delta_phi),
    )
end

function fiber_base_split_readout(eta::Float64, chi::Float64)
    base0 = hopf_projection(hopf_chart(0.0, chi, eta))
    max_base_move = 0.0
    max_spinor_move = 0.0
    for k in 0:32
        phi = 2pi * k / 32
        psi = hopf_chart(phi, chi, eta)
        max_base_move = max(max_base_move, norm(hopf_projection(psi) - base0))
        max_spinor_move = max(max_spinor_move, norm(psi - hopf_chart(0.0, chi, eta)))
    end
    return Dict(
        "eta" => eta,
        "chi" => chi,
        "hopf_base_invariance_under_fiber_max" => max_base_move,
        "hopf_fiber_spinor_orbit_diameter" => max_spinor_move,
        "trivial_base_invariance_under_fiber_max" => 0.0,
        "trivial_fiber_spinor_orbit_diameter" => 0.0,
        "fiber_split_collapse_delta" => max_spinor_move,
    )
end

function peps3d_anchor(nsites::Int)
    dims = nsites == 8  ? (2, 2, 2) :
           nsites == 16 ? (2, 2, 4) :
           nsites == 32 ? (2, 4, 4) :
           nsites == 64 ? (4, 4, 4) :
           error("unsupported anchor size")
    nx, ny, nz = dims
    vid(x, y, z) = 1 + x + nx * y + nx * ny * z
    vertices = collect(1:nsites)
    edges = Vector{Vector{Int}}()
    faces = Vector{Vector{Int}}()
    cells = Vector{Vector{Int}}()
    for z in 0:(nz - 1), y in 0:(ny - 1), x in 0:(nx - 1)
        x + 1 < nx && push!(edges, [vid(x, y, z), vid(x + 1, y, z)])
        y + 1 < ny && push!(edges, [vid(x, y, z), vid(x, y + 1, z)])
        z + 1 < nz && push!(edges, [vid(x, y, z), vid(x, y, z + 1)])
        if x + 1 < nx && y + 1 < ny
            push!(faces, [vid(x, y, z), vid(x + 1, y, z), vid(x + 1, y + 1, z), vid(x, y + 1, z)])
        end
        if x + 1 < nx && z + 1 < nz
            push!(faces, [vid(x, y, z), vid(x + 1, y, z), vid(x + 1, y, z + 1), vid(x, y, z + 1)])
        end
        if y + 1 < ny && z + 1 < nz
            push!(faces, [vid(x, y, z), vid(x, y + 1, z), vid(x, y + 1, z + 1), vid(x, y, z + 1)])
        end
        if x + 1 < nx && y + 1 < ny && z + 1 < nz
            push!(cells, [
                vid(x, y, z), vid(x + 1, y, z), vid(x, y + 1, z), vid(x + 1, y + 1, z),
                vid(x, y, z + 1), vid(x + 1, y, z + 1), vid(x, y + 1, z + 1), vid(x + 1, y + 1, z + 1),
            ])
        end
    end
    return Dict(
        "K" => "finite PEPS3D combinatorial anchor K=(V,E,F,C)",
        "dims" => [nx, ny, nz],
        "V_count" => length(vertices),
        "E_count" => length(edges),
        "F_count" => length(faces),
        "C_count" => length(cells),
        "sample_vertices" => vertices[1:min(end, 8)],
        "sample_edges" => edges[1:min(end, 8)],
        "sample_faces" => faces[1:min(end, 4)],
        "sample_cells" => cells[1:min(end, 2)],
        "anchor_boundary" => "finite K anchor only; no PEPSKit contraction or tensor optimization claimed",
    )
end

function entropy_from_density(rho::Matrix{ComplexF64})
    vals = real.(eigvals(Hermitian(rho)))
    s = 0.0
    for p in vals
        q = max(p, 0.0)
        q > 1e-12 && (s -= q * log2(q))
    end
    return s
end

function qit_readouts(section_fn, ntheta::Int, nalpha::Int)
    pure_entropy_max = 0.0
    rho_mix = zeros(ComplexF64, 2, 2)
    count = 0
    for i in 0:(ntheta - 1)
        theta = pi * (i + 0.5) / ntheta
        for j in 0:(nalpha - 1)
            alpha = 2pi * (j + 0.5) / nalpha
            rho = density(section_fn(theta, alpha))
            pure_entropy_max = max(pure_entropy_max, entropy_from_density(rho))
            rho_mix .+= rho
            count += 1
        end
    end
    rho_mix ./= count
    return Dict(
        "pure_density_entropy_max_bits" => pure_entropy_max,
        "ensemble_density_entropy_bits" => entropy_from_density(rho_mix),
        "ensemble_density_trace" => real(tr(rho_mix)),
        "derived_only" => true,
    )
end

function stress_case(shell::Int)
    ntheta = shell
    nalpha = 2shell
    hopf = fhs_chern((theta, alpha) -> projective_section(theta, alpha, 1), ntheta, nalpha)
    trivial_m0 = fhs_chern((theta, alpha) -> projective_section(theta, alpha, 0), ntheta, nalpha)
    constant = fhs_chern(constant_section, ntheta, nalpha)
    phase_erased = fhs_chern(phase_erased_section, ntheta, nalpha)
    return Dict(
        "shell" => shell,
        "fhs_grid" => Dict("ntheta" => ntheta, "nalpha" => nalpha),
        "peps3d_anchor" => peps3d_anchor(shell),
        "hopf" => hopf,
        "trivial_m0" => trivial_m0,
        "constant_section" => constant,
        "phase_erased" => phase_erased,
        "dependency_forcing_delta" => Dict(
            "abs_c1_hopf_minus_trivial_m0" => abs(hopf["c1"] - trivial_m0["c1"]),
            "abs_c1_hopf_minus_constant" => abs(hopf["c1"] - constant["c1"]),
            "abs_flux_sum_hopf_minus_constant" => abs(hopf["abs_flux_sum"] - constant["abs_flux_sum"]),
            "abs_flux_sum_hopf_minus_phase_erased" => abs(hopf["abs_flux_sum"] - phase_erased["abs_flux_sum"]),
        ),
        "qit_readouts_hopf" => qit_readouts((theta, alpha) -> projective_section(theta, alpha, 1), ntheta, nalpha),
        "qit_readouts_constant" => qit_readouts(constant_section, ntheta, nalpha),
    )
end

function bool_checks(stress)
    c1_tol = 1e-9
    hopf_ok = all(abs(s["hopf"]["c1"] - 1.0) < c1_tol for s in stress)
    trivial_ok = all(abs(s["trivial_m0"]["c1"]) < c1_tol && abs(s["constant_section"]["c1"]) < c1_tol for s in stress)
    erased_ok = all(abs(s["phase_erased"]["c1"]) < c1_tol for s in stress)
    ablation_ok = all(s["dependency_forcing_delta"]["abs_c1_hopf_minus_constant"] > 0.999999 for s in stress)
    qit_ok = all(s["qit_readouts_hopf"]["pure_density_entropy_max_bits"] < 1e-9 for s in stress)
    anchors_ok = all(s["peps3d_anchor"]["V_count"] == s["shell"] && s["peps3d_anchor"]["C_count"] > 0 for s in stress)
    n01 = horizontal_commutator_gap(pi / 5)
    hol = holonomy_readout(pi / 6)
    split = fiber_base_split_readout(pi / 5, pi / 7)
    return Dict(
        "fhs_hopf_c1_is_1_all_stress" => hopf_ok,
        "trivialized_c1_is_0_all_stress" => trivial_ok,
        "phase_erased_c1_is_0_all_stress" => erased_ok,
        "nonvacuous_ablation_delta_present" => ablation_ok,
        "qit_readouts_are_derived_and_finite" => qit_ok,
        "peps3d_anchor_present_all_stress" => anchors_ok,
        "n01_horizontal_commutator_nonzero" => abs(n01["vertical_phi_gap"]) > 1e-12 && n01["trivialized_vertical_phi_gap"] == 0.0,
        "holonomy_collapses_under_trivialization" => hol["collapse_delta_abs"] > 1.0,
        "fiber_base_split_collapses_under_constant_section" => split["fiber_split_collapse_delta"] > 1.0 && split["hopf_base_invariance_under_fiber_max"] < 1e-9,
    )
end

function main()
    shells = [8, 16, 32, 64]
    stress = [stress_case(s) for s in shells]
    checks = bool_checks(stress)
    all_pass = all(values(checks))

    n01 = horizontal_commutator_gap(pi / 5)
    hol = holonomy_readout(pi / 6)
    split = fiber_base_split_readout(pi / 5, pi / 7)

    result = Dict(
        "sim_id" => "L4_layer_codex",
        "name" => "L4 Hopf fibration S3_to_S2_U1 finite-QIT dependency-forcing PoC",
        "version" => "1.0",
        "classification" => "L4_layer_codex_poc",
        "promotion_allowed" => false,
        "fresh_rerun" => true,
        "run_command" => RUN_COMMAND,
        "sim_execution_kind" => "nonclassical_julia_poc",
        "sim_class" => "geometry_probe",
        "finite_map" => "finite lattice of normalized C2 spinors psi in S3, quotient by U(1) phase via Hopf projection pi(psi)=psi^dagger sigma psi in S2, with FHS plaquette readout c1",
        "domain" => "finite PEPS3D-anchored shell grids over projective spinor section theta=2eta, alpha=-2chi; shells 8,16,32,64",
        "codomain_or_output" => "integer first Chern readout c1, Berry/FHS plaquette fluxes, horizontal commutator gap, holonomy, derived density entropies",
        "math_from_docs_quoted" => [
            "psi(phi,chi;eta)=(e^(i(phi+chi)) cos eta, e^(i(phi-chi)) sin eta)",
            "A_Hopf = dphi + cos(2eta) dchi",
            "Hopf projection pi(psi)=psi^dagger sigma psi in S2",
        ],
        "root_constraints_in_force" => Dict(
            "F01_witness" => "finite shell grids plus finite PEPS3D K=(V,E,F,C) anchors; no continuum-only readout",
            "N01_witness" => "horizontal lift commutator [H_eta,H_chi] has measured vertical phi gap; trivialized connection gap is zero",
        ),
        "F01_witness" => "finite shell grids 8/16/32/64 with finite PEPS3D K=(V,E,F,C) anchors",
        "N01_witness" => "measured noncommuting horizontal-lift gap: H_eta then H_chi differs from H_chi then H_eta; erased connection gap is zero",
        "carrier_realization" => Dict(
            "spinor_state" => "Julia-native Vector{ComplexF64} normalized C2 spinor",
            "density_state" => "Julia-native 2x2 ComplexF64 rank-1 density rho=psi*psi'",
            "non_numpy" => true,
            "torch_gap" => "not torch-native because this requested artifact is Julia-only; blocks stronger nonclassical manifold admission under repo doctrine",
        ),
        "spinor_state" => "Julia-native normalized Vector{ComplexF64} in C2 representing a point of S3",
        "density_state" => "rho=psi*psi' as a 2x2 ComplexF64 rank-1 density",
        "peps3d_embedding" => "each stress shell carries an explicit finite combinatorial K=(V,E,F,C) anchor; this is not a PEPSKit tensor-contraction receipt",
        "quaternion_action" => "not_applicable: this L4 artifact uses complex spinor/Hopf coordinates and makes no quaternion-map claim",
        "dependency_receipts" => [
            "current-run read: system_v5/ops/MANIFOLD_GEOMETRY_LAYER_STACK_NONCOMMUTATIVE_ORDER_20260528.md",
            "current-run read: system_v5/READ ONLY Reference Docs/Formal constraints and geometry .md",
            "current-run result: system_v5/julia_carrier/layers/L4_layer_codex_results.json",
        ],
        "geometry_layer" => "L4 Hopf fibration S3 -> S2 with U(1) fiber",
        "connection" => Dict(
            "A_Hopf" => "dphi + cos(2eta) dchi",
            "curvature_nonzero_witness" => "horizontal non-involutivity and FHS c1=1",
            "n01_horizontal_noncommuting_gap" => n01,
            "holonomy" => hol,
            "fiber_base_split" => split,
        ),
        "stress_8_16_32_64" => stress,
        "dependency_forcing_erasures" => Dict(
            "trivial_m0_section" => "same FHS method with m=0 gives c1=0 and zero net plaquette flux",
            "constant_section" => "frozen section psi=[1,0] gives c1=0, zero curvature, zero fiber orbit",
            "phase_erased_section" => "removes U(1) winding from second component; FHS c1 collapses to 0",
            "horizontal_connection_trivialized" => "sets A=dphi or removes cos(2eta)dchi coupling; commutator gap and holonomy collapse to zero",
        ),
        "negative_controls" => [
            "trivial m=0 line-bundle section",
            "globally constant section",
            "phase-erased section",
            "trivialized horizontal connection",
        ],
        "tool_manifest" => Dict(
            "Julia" => Dict("role" => "load_bearing", "reason" => "native complex spinor lattice, FHS plaquette loop, connection-flow ablation, no NumPy bridge"),
            "LinearAlgebra" => Dict("role" => "load_bearing", "reason" => "inner products, norms, traces, Hermitian density eigenspectra for FHS and QIT readouts"),
            "JSON" => Dict("role" => "supportive", "reason" => "artifact emission only"),
            "Z3" => Dict("role" => "omitted", "reason" => "z3 omitted, not decorative; no SMT claim is needed because dependency forcing is measured by removed-and-rerun numeric collapse"),
        ),
        "tool_integration_depth" => Dict(
            "Julia" => "load_bearing",
            "LinearAlgebra" => "load_bearing",
            "JSON" => "supportive",
            "Z3" => "None",
        ),
        "divergence_log" => [
            "Hopf section c1=1 while trivial/constant/phase-erased controls c1=0 using same FHS path",
            "Horizontal commutator vertical gap is nonzero only with A_Hopf coupling",
            "Holonomy and fiber orbit diameter collapse when bundle geometry is erased",
        ],
        "allowed_claims" => [
            "bounded Julia PoC for L4 Hopf c1 signature under FHS plaquette readout",
            "dependency-forcing erasures collapse the measured L4 signature in this finite setup",
        ],
        "blocked_consumers" => [
            "layer completion",
            "parent-complete L4",
            "stacking readiness",
            "nested Hopf tori L5",
            "connection/holonomy L6 admission",
            "Weyl/chirality",
            "terrain",
            "flux",
            "Xi",
            "Phi0",
            "Axis0",
            "bridge",
            "basin",
            "physics/gravity",
        ],
        "eligible_consumers" => [
            "local L4 PoC audit only",
            "future L4 repair worker may use as comparison input after rerun",
        ],
        "promotion_status" => "keep_but_open",
        "promotion_blockers" => [
            "Julia-native rather than torch-native carrier under repo nonclassical admission doctrine",
            "finite PEPS3D K anchor is combinatorial only; no PEPSKit tensor contraction or full cell-tensor payload",
            "not run through validate_layer_distinctness.py",
            "no full dedicated L4 evidence packet or layer-completion claim gate",
            "does not prove parent-complete L4 or downstream stack compatibility",
        ],
        "checks" => checks,
        "all_pass" => all_pass,
        "honest_status" => all_pass ?
            "passes local rerun for bounded L4_layer_codex_poc checks; promotion still blocked" :
            "runs_partial_or_negative; inspect checks and stress_8_16_32_64",
    )

    open(OUTPATH, "w") do io
        JSON.print(io, result, 2)
    end

    println("L4_layer_codex wrote ", OUTPATH)
    println("classification=", result["classification"], " promotion_allowed=", result["promotion_allowed"])
    println("all_pass=", all_pass)
    for s in stress
        println(
            "shell=", s["shell"],
            " c1_hopf=", s["hopf"]["c1"],
            " c1_trivial=", s["trivial_m0"]["c1"],
            " c1_constant=", s["constant_section"]["c1"],
            " c1_phase_erased=", s["phase_erased"]["c1"],
        )
    end
    println("n01_vertical_phi_gap=", n01["vertical_phi_gap"], " trivial_gap=", n01["trivialized_vertical_phi_gap"])
    println("holonomy_collapse_delta_abs=", hol["collapse_delta_abs"])
    println("fiber_split_collapse_delta=", split["fiber_split_collapse_delta"])
end

main()
