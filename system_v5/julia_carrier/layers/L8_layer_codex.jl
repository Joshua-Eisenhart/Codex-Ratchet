# L8_layer_codex.jl
#
# Layer L8: chirality orientation cover.
#
# Read anchors used for this build:
# - Registry: L8 is "chirality orientation cover" with "L/R sheet,
#   gamma5 / Pin / Spin / reflection controls".
# - Registry status: L7/L8 are partial; L8 "needs Pin/Spin/reflection controls".
# - Agent contract: nonclassical manifold steps require an explicit finite map,
#   F01/N01 witnesses, spinor or spinor-derived density, PEPS3D K=(V,E,F,C)
#   anchor, negative controls, blocked consumers, and dependency-forcing erasure.
#
# This is a Julia-native finite-QIT POC, not promotion evidence:
# classification=L8_layer_codex_poc, promotion_allowed=false.

using LinearAlgebra
using JSON
using Dates

const RESULTS_PATH = joinpath(@__DIR__, "L8_layer_codex_results.json")
const TOL = 1e-9

const I2 = ComplexF64[1 0; 0 1]
const Z2 = zeros(ComplexF64, 2, 2)
const SX = ComplexF64[0 1; 1 0]
const SZ = ComplexF64[1 0; 0 -1]

# Chiral/Weyl basis. gamma5 eigenvalue -1 is the L sheet, +1 is the R sheet.
const I4 = Matrix{ComplexF64}(I, 4, 4)
const GAMMA5 = Diagonal(ComplexF64[-1, -1, 1, 1]) |> Matrix
const REFLECT_LR = [Z2 I2; I2 Z2]  # Pin-style reflection/parity control: swaps L <-> R.

function blockdiag2(a, b)
    return [a zeros(ComplexF64, size(a, 1), size(b, 2));
            zeros(ComplexF64, size(b, 1), size(a, 2)) b]
end

function spin3_rotation(theta)
    # A finite Spin(3) control in the chiral carrier: block diagonal SU(2).
    u = cos(theta / 2) .* I2 .- im * sin(theta / 2) .* SZ
    return blockdiag2(u, u)
end

function normalize_spinor(psi)
    n = sqrt(real(psi' * psi))
    @assert n > 0
    return psi ./ n
end

function local_two_spinor(ix, iy, iz, n)
    # Deterministic finite set of unit C^2 spinors; no randomness, no numpy.
    a = 0.37 + 0.11 * ix + 0.07 * iy + 0.03 * iz
    b = 0.19 + 0.05 * ix - 0.09 * iy + 0.13 * iz + 0.01 * n
    eta = 0.25 + 0.5 * abs(sin(a))
    return ComplexF64[exp(im * a) * cos(eta), exp(im * b) * sin(eta)]
end

left_spinor(u2) = normalize_spinor(ComplexF64[u2[1], u2[2], 0, 0])
right_spinor(u2) = normalize_spinor(ComplexF64[0, 0, u2[1], u2[2]])
density(psi) = psi * psi'

function charge(g5, rho)
    return real(tr(g5 * rho))
end

function vnentropy(rho)
    vals = eigvals(Hermitian((rho + rho') ./ 2))
    s = 0.0
    for x in real.(vals)
        p = max(x, 0.0)
        if p > 1e-12
            s -= p * log(p)
        end
    end
    return s
end

function trace_distance(rho, sigma)
    vals = svdvals(rho - sigma)
    return 0.5 * sum(vals)
end

function make_K(nx, ny, nz)
    vertices = Vector{Vector{Int}}()
    index = Dict{Tuple{Int,Int,Int},Int}()
    for z in 1:nz, y in 1:ny, x in 1:nx
        push!(vertices, [x, y, z])
        index[(x, y, z)] = length(vertices)
    end

    edges = Vector{Vector{Int}}()
    for z in 1:nz, y in 1:ny, x in 1:nx
        v = index[(x, y, z)]
        if x < nx; push!(edges, [v, index[(x + 1, y, z)]]); end
        if y < ny; push!(edges, [v, index[(x, y + 1, z)]]); end
        if z < nz; push!(edges, [v, index[(x, y, z + 1)]]); end
    end

    faces = Vector{Vector{Int}}()
    for z in 1:nz, y in 1:ny, x in 1:(nx - 1), yy in y:(ny - 1)
        if yy == y
            push!(faces, [index[(x, y, z)], index[(x + 1, y, z)],
                          index[(x + 1, y + 1, z)], index[(x, y + 1, z)]])
        end
    end
    for z in 1:nz, x in 1:nx, y in 1:(ny - 1), zz in z:(nz - 1)
        if zz == z
            push!(faces, [index[(x, y, z)], index[(x, y + 1, z)],
                          index[(x, y + 1, z + 1)], index[(x, y, z + 1)]])
        end
    end
    for y in 1:ny, z in 1:nz, x in 1:(nx - 1), zz in z:(nz - 1)
        if zz == z
            push!(faces, [index[(x, y, z)], index[(x + 1, y, z)],
                          index[(x + 1, y, z + 1)], index[(x, y, z + 1)]])
        end
    end

    cells = Vector{Vector{Int}}()
    for z in 1:(nz - 1), y in 1:(ny - 1), x in 1:(nx - 1)
        push!(cells, [index[(x, y, z)], index[(x + 1, y, z)],
                      index[(x, y + 1, z)], index[(x + 1, y + 1, z)],
                      index[(x, y, z + 1)], index[(x + 1, y, z + 1)],
                      index[(x, y + 1, z + 1)], index[(x + 1, y + 1, z + 1)]])
    end

    return Dict(
        "dims" => [nx, ny, nz],
        "V" => vertices,
        "E" => edges,
        "F" => faces,
        "C" => cells,
    )
end

function K_counts(K)
    return Dict("V" => length(K["V"]), "E" => length(K["E"]),
                "F" => length(K["F"]), "C" => length(K["C"]),
                "dims" => K["dims"])
end

function layer_map(psi, g5, spin_op, reflect_op)
    rho = density(psi)
    rho_spin = density(spin_op * psi)
    rho_reflect = density(reflect_op * psi)
    return Dict(
        "orientation_charge" => charge(g5, rho),
        "spin_charge" => charge(g5, rho_spin),
        "reflection_charge" => charge(g5, rho_reflect),
        "pure_entropy" => vnentropy(rho),
    )
end

function run_for_K(n, dims)
    K = make_K(dims...)
    theta = 0.71
    spin = spin3_rotation(theta)
    reflect = REFLECT_LR
    no_reflect = I4
    erased_g5 = I4

    original_sep = Float64[]
    erased_sep = Float64[]
    reflect_flip = Float64[]
    reflect_erased_flip = Float64[]
    spin_preserve_err = Float64[]
    quotient_signed_charge = Float64[]
    pure_entropies = Float64[]
    quotient_entropies = Float64[]
    quotient_trace_distances = Float64[]
    n01_state_order_gaps = Float64[]

    for (i, coord) in enumerate(K["V"])
        ix, iy, iz = coord
        u = local_two_spinor(ix, iy, iz, n)
        psiL = left_spinor(u)
        psiR = right_spinor(u)
        rhoL = density(psiL)
        rhoR = density(psiR)

        qL = charge(GAMMA5, rhoL)
        qR = charge(GAMMA5, rhoR)
        push!(original_sep, abs(qR - qL))

        qL_erased = charge(erased_g5, rhoL)
        qR_erased = charge(erased_g5, rhoR)
        push!(erased_sep, abs(qR_erased - qL_erased))

        mapped = layer_map(psiL, GAMMA5, spin, reflect)
        push!(spin_preserve_err, abs(mapped["spin_charge"] - mapped["orientation_charge"]))
        push!(reflect_flip, abs(mapped["reflection_charge"] - mapped["orientation_charge"]))

        mapped_no_reflect = layer_map(psiL, GAMMA5, spin, no_reflect)
        push!(reflect_erased_flip, abs(mapped_no_reflect["reflection_charge"] - mapped_no_reflect["orientation_charge"]))

        # Reflection quotient: L and R are gauge-identified; gamma5 is not invariant under
        # this identification, so the signed orientation observable cannot descend.
        rho_quot = (rhoL + rhoR) ./ 2
        push!(quotient_signed_charge, abs(charge(GAMMA5, rho_quot)))
        push!(pure_entropies, mapped["pure_entropy"])
        push!(quotient_entropies, vnentropy(rho_quot))
        push!(quotient_trace_distances, trace_distance(rhoL, rhoR))

        # N01 as order sensitivity: gamma5 after reflection differs from reflection after gamma5.
        order_gap = norm(GAMMA5 * (reflect * psiL) - reflect * (GAMMA5 * psiL))
        push!(n01_state_order_gaps, order_gap)
    end

    comm_spin = norm(GAMMA5 * spin - spin * GAMMA5)
    comm_reflect = norm(GAMMA5 * reflect - reflect * GAMMA5)
    anticomm_reflect = norm(GAMMA5 * reflect + reflect * GAMMA5)
    erased_comm_reflect = norm(erased_g5 * reflect - reflect * erased_g5)
    reflection_gamma5_conjugation_delta = norm(reflect' * GAMMA5 * reflect + GAMMA5)

    return Dict(
        "site_count" => n,
        "K_counts" => K_counts(K),
        "finite_map" => "f_n:(v,s,psi_vs; gamma5, Spin3(theta), Pin_reflection)->(orientation_charge, spin_charge, reflection_charge, entropy), with v in PEPS3D K_n and s in {L,R}",
        "domain_size" => 2 * length(K["V"]),
        "codomain" => "finite real readout tuple per oriented sheet plus aggregate collapse certificates",
        "orientation_charge_separation_mean" => sum(original_sep) / length(original_sep),
        "orientation_charge_separation_min" => minimum(original_sep),
        "gamma5_erased_separation_mean" => sum(erased_sep) / length(erased_sep),
        "gamma5_erased_separation_max" => maximum(erased_sep),
        "reflection_flip_gap_mean" => sum(reflect_flip) / length(reflect_flip),
        "reflection_flip_gap_min" => minimum(reflect_flip),
        "reflection_removed_flip_gap_mean" => sum(reflect_erased_flip) / length(reflect_erased_flip),
        "spin_preserve_err_max" => maximum(spin_preserve_err),
        "reflection_quotient_signed_charge_max" => maximum(quotient_signed_charge),
        "qit_entropy_pure_max" => maximum(pure_entropies),
        "qit_entropy_reflection_quotient_mean" => sum(quotient_entropies) / length(quotient_entropies),
        "qit_trace_distance_L_R_mean" => sum(quotient_trace_distances) / length(quotient_trace_distances),
        "n01_state_order_gap_mean" => sum(n01_state_order_gaps) / length(n01_state_order_gaps),
        "n01_state_order_gap_min" => minimum(n01_state_order_gaps),
        "operator_commutators" => Dict(
            "norm_commutator_gamma5_spin3" => comm_spin,
            "norm_commutator_gamma5_reflection" => comm_reflect,
            "norm_anticommutator_gamma5_reflection" => anticomm_reflect,
            "norm_commutator_identity_erased_gamma5_reflection" => erased_comm_reflect,
            "norm_reflection_conjugates_gamma5_to_minus_gamma5" => reflection_gamma5_conjugation_delta,
        ),
    )
end

function stress_suite()
    dims_by_n = Dict(
        8 => (2, 2, 2),
        16 => (2, 2, 4),
        32 => (2, 4, 4),
        64 => (4, 4, 4),
    )
    rows = Dict{String,Any}()
    for n in [8, 16, 32, 64]
        rows[string(n)] = run_for_K(n, dims_by_n[n])
    end
    return rows
end

stress = stress_suite()

function all_stress(predicate)
    return all(predicate(stress[string(n)]) for n in [8, 16, 32, 64])
end

dependency_erasures = Dict(
    "gamma5_orientation_control_removed" => Dict(
        "present_signature_mean_by_sites" => Dict(string(n) => stress[string(n)]["orientation_charge_separation_mean"] for n in [8, 16, 32, 64]),
        "erased_signature_mean_by_sites" => Dict(string(n) => stress[string(n)]["gamma5_erased_separation_mean"] for n in [8, 16, 32, 64]),
        "collapsed" => all_stress(r -> r["orientation_charge_separation_min"] > 1.99 && r["gamma5_erased_separation_max"] < TOL),
        "interpretation" => "Replacing gamma5 by identity reruns the L/R readout and makes both sheets have trace 1, so the oriented cover separation is zero.",
    ),
    "reflection_control_removed" => Dict(
        "present_reflection_flip_gap_by_sites" => Dict(string(n) => stress[string(n)]["reflection_flip_gap_mean"] for n in [8, 16, 32, 64]),
        "removed_reflection_flip_gap_by_sites" => Dict(string(n) => stress[string(n)]["reflection_removed_flip_gap_mean"] for n in [8, 16, 32, 64]),
        "collapsed" => all_stress(r -> r["reflection_flip_gap_min"] > 1.99 && r["reflection_removed_flip_gap_mean"] < TOL),
        "interpretation" => "Replacing the L/R reflection by identity removes the Pin-style sheet swap; the reflection signature becomes absent.",
    ),
    "reflection_quotient_LR_identification" => Dict(
        "quotient_signed_charge_max_by_sites" => Dict(string(n) => stress[string(n)]["reflection_quotient_signed_charge_max"] for n in [8, 16, 32, 64]),
        "gamma5_descends_to_reflection_quotient" => false,
        "gauge_invariance_violation" => "P' * gamma5 * P = -gamma5, so gamma5 is not invariant under the reflection quotient.",
        "collapsed" => all_stress(r -> r["reflection_quotient_signed_charge_max"] < TOL),
        "interpretation" => "Identifying L with its reflected R partner makes the signed gamma5 orientation charge average to zero; the oriented double cover trivializes in the quotient.",
    ),
    "pin_vs_spin_distinction" => Dict(
        "spin_commutator_max_by_sites" => Dict(string(n) => stress[string(n)]["operator_commutators"]["norm_commutator_gamma5_spin3"] for n in [8, 16, 32, 64]),
        "reflection_commutator_by_sites" => Dict(string(n) => stress[string(n)]["operator_commutators"]["norm_commutator_gamma5_reflection"] for n in [8, 16, 32, 64]),
        "erased_gamma5_reflection_commutator_by_sites" => Dict(string(n) => stress[string(n)]["operator_commutators"]["norm_commutator_identity_erased_gamma5_reflection"] for n in [8, 16, 32, 64]),
        "collapsed_when_gamma5_erased" => all_stress(r -> r["operator_commutators"]["norm_commutator_gamma5_spin3"] < TOL &&
                                                          r["operator_commutators"]["norm_commutator_gamma5_reflection"] > 3.99 &&
                                                          r["operator_commutators"]["norm_commutator_identity_erased_gamma5_reflection"] < TOL),
        "interpretation" => "Spin(3) rotations commute with gamma5, while the Pin-style reflection is gamma5-order-sensitive. Erasing gamma5 collapses that distinction.",
    ),
)

minimum_standard = Dict(
    "finite_map_domain_to_codomain" => "present",
    "F01_witness" => "present: finite PEPS3D K_n with n in {8,16,32,64}, finite operators {gamma5, Spin3(theta), Pin_reflection}",
    "N01_witness" => "present: measured gamma5/reflection order gap and nonzero commutator",
    "julia_native_spinor_density" => "present: ComplexF64 spinors and psi*psi' densities",
    "PEPS3D_anchor" => "present as finite combinatorial K=(V,E,F,C) with local spinor/density payload; no tensor-network contraction claimed",
    "stress_8_16_32_64" => "present",
    "load_bearing_tool_manifest" => "present",
    "non_vacuous_ablation" => "present: gamma5 erasure, reflection removal, reflection quotient all rerun numerically",
    "QIT_entropy_readouts_derived" => "present: von Neumann entropy and trace distance are derived from rho after finite map",
    "negative_controls" => "present: gamma5 identity erasure, reflection identity erasure, Spin(3) rotation control",
    "blocked_consumers" => ["L9_plus_stack", "terrain", "flux", "Xi", "Phi0", "Axis0", "bridge", "basin", "physics"],
    "fresh_rerun" => "present: this script writes a fresh result on execution",
    "z3" => "z3 omitted, not decorative",
)

pass_checks = Dict(
    "orientation_cover_nontrivial_before_erasure" => all_stress(r -> r["orientation_charge_separation_min"] > 1.99),
    "gamma5_erasure_collapses_cover" => dependency_erasures["gamma5_orientation_control_removed"]["collapsed"],
    "reflection_removal_collapses_reflection_signature" => dependency_erasures["reflection_control_removed"]["collapsed"],
    "reflection_quotient_trivializes_signed_cover" => dependency_erasures["reflection_quotient_LR_identification"]["collapsed"],
    "spin_vs_pin_distinction_collapses_when_gamma5_erased" => dependency_erasures["pin_vs_spin_distinction"]["collapsed_when_gamma5_erased"],
    "n01_order_gap_nonzero" => all_stress(r -> r["n01_state_order_gap_min"] > 1.99),
    "spin3_preserves_chirality" => all_stress(r -> r["spin_preserve_err_max"] < TOL),
    "qit_entropy_is_derived_and_nontrivial_in_reflection_quotient" => all_stress(r -> r["qit_entropy_pure_max"] < TOL &&
                                                                                     r["qit_entropy_reflection_quotient_mean"] > 0.69),
)

all_pass = all(values(pass_checks))

results = Dict(
    "sim_id" => "L8_layer_codex",
    "name" => "chirality orientation cover finite-QIT POC",
    "version" => "1.0",
    "generated_at" => string(now(UTC)),
    "classification" => "L8_layer_codex_poc",
    "promotion_allowed" => false,
    "promotion_status" => all_pass ? "keep_but_open" : "diagnostic_only",
    "sim_execution_kind" => "nonclassical",
    "sim_class" => "geometry_probe",
    "layer" => "L8 chirality orientation cover",
    "quoted_math_anchors" => [
        "registry L8: chirality orientation cover; L/R sheet, gamma5 / Pin / Spin / reflection controls",
        "registry L8 state: partial; sheet_collapsed load-bearing; needs Pin/Spin/reflection controls",
        "agent gate: explicit finite map, F01/N01, spinor/density, PEPS3D K=(V,E,F,C), controls, blocked consumers",
    ],
    "finite_map" => "f_n:(v,s,psi_vs; gamma5, Spin3(theta), Pin_reflection)->(orientation_charge, spin_charge, reflection_charge, entropy)",
    "domain" => "Union over n={8,16,32,64} of finite PEPS3D K_n vertices times orientation sheet s in {L,R}; local Dirac spinor psi_vs in C^4",
    "codomain_or_output" => "finite orientation-cover signature, Pin/Spin sensitivity metrics, ablation collapse certificates, derived QIT entropy/readouts",
    "carrier_realization" => "Julia ComplexF64 chiral-basis Dirac spinors; rho=psi*psi'",
    "spinor_state" => "L sheet: gamma5 eigenvalue -1 subspace; R sheet: gamma5 eigenvalue +1 subspace",
    "peps3d_embedding" => "finite K=(V,E,F,C) anchors for 8,16,32,64 vertices; spinor/density payload attached to each vertex and sheet",
    "quaternion_action" => "not_applicable: no quaternion language used in this L8 POC",
    "root_constraints_in_force" => Dict(
        "F01" => "finite carrier/probe/operator/path registry: finite K_n and finite operators gamma5, Spin3(theta), Pin reflection",
        "N01" => "order-sensitive gamma5/reflection control: gamma5*P != P*gamma5 measured on operators and states",
    ),
    "stress" => stress,
    "dependency_erasures" => dependency_erasures,
    "minimum_standard" => minimum_standard,
    "pass_checks" => pass_checks,
    "all_pass" => all_pass,
    "tool_manifest" => Dict(
        "LinearAlgebra" => Dict(
            "used" => true,
            "role" => "load_bearing",
            "reason" => "constructs finite spinor/density operators, applies Spin/Pin controls, measures norms, eigenspectrum entropy, and trace distance",
        ),
        "JSON" => Dict(
            "used" => true,
            "role" => "supportive",
            "reason" => "emits the result receipt",
        ),
        "Z3" => Dict(
            "used" => false,
            "role" => "omitted",
            "reason" => "z3 omitted, not decorative: no structural SMT claim is needed beyond measured finite LinearAlgebra operator identities",
        ),
    ),
    "tool_integration_depth" => Dict(
        "LinearAlgebra" => "load_bearing",
        "JSON" => "supportive",
        "Z3" => "None",
    ),
    "actual_tools_used" => ["Julia", "LinearAlgebra", "JSON"],
    "negative_controls" => [
        "gamma5 replaced by identity",
        "Pin reflection replaced by identity",
        "Spin(3) block rotation control commutes with gamma5",
        "reflection quotient identifies L/R and blocks descended signed gamma5 observable",
    ],
    "divergence_log" => [
        "No classical baseline promoted; gamma5-erased identity control collapses orientation readout.",
        "No dense-state closure or numpy bridge used.",
    ],
    "allowed_claims" => [
        "local finite L8 POC exhibits an orientation double-cover signature on a finite chiral spinor carrier",
        "gamma5/reflection dependency erasures collapse the measured signature in this finite model",
    ],
    "promotion_blockers" => [
        "No full tensor-network PEPS contraction or bond optimization, only K=(V,E,F,C) anchoring",
        "No lower-layer dependency receipt chain admitted in this file",
        "No Z3/cvc5 proof layer; omitted rather than decorative",
        "classification intentionally POC and promotion_allowed=false",
    ],
    "eligible_consumers" => [],
    "blocked_consumers" => minimum_standard["blocked_consumers"],
)

open(RESULTS_PATH, "w") do io
    JSON.print(io, results, 2)
    write(io, "\n")
end

println("L8_layer_codex built and ran")
println("results_path=", RESULTS_PATH)
println("classification=", results["classification"])
println("promotion_allowed=", results["promotion_allowed"])
println("all_pass=", results["all_pass"])
println("gamma5_erasure_collapsed=", dependency_erasures["gamma5_orientation_control_removed"]["collapsed"])
println("reflection_removal_collapsed=", dependency_erasures["reflection_control_removed"]["collapsed"])
println("reflection_quotient_collapsed=", dependency_erasures["reflection_quotient_LR_identification"]["collapsed"])
println("pin_spin_distinction_collapsed_when_gamma5_erased=", dependency_erasures["pin_vs_spin_distinction"]["collapsed_when_gamma5_erased"])
