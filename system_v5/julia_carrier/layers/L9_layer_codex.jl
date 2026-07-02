using LinearAlgebra
import JSON

const ATOL = 1e-9
const OUTPATH = joinpath(@__DIR__, "L9_layer_codex_results.json")

function mat_rank(A; atol=ATOL)
    return rank(A; atol=atol)
end

function clifford_words(gs)
    d = size(gs[1], 1)
    words = Matrix{ComplexF64}[Matrix{ComplexF64}(I, d, d)]
    n = length(gs)
    for a in 1:n
        push!(words, gs[a])
    end
    for a in 1:n, b in a+1:n
        push!(words, gs[a] * gs[b])
    end
    for a in 1:n, b in a+1:n, c in b+1:n
        push!(words, gs[a] * gs[b] * gs[c])
    end
    top = gs[1]
    for a in 2:n
        top = top * gs[a]
    end
    push!(words, top)
    return words
end

function burnside_rank(gs)
    V = hcat([vec(w) for w in clifford_words(gs)]...)
    return mat_rank(V)
end

function commutant_dim(gs)
    d = size(gs[1], 1)
    I_d = Matrix{ComplexF64}(I, d, d)
    blocks = Matrix{ComplexF64}[]
    for g in gs
        push!(blocks, kron(transpose(g), I_d) - kron(I_d, g))
    end
    A = vcat(blocks...)
    return size(nullspace(A; atol=ATOL), 2)
end

function max_clifford_residual(gs, eta)
    d = size(gs[1], 1)
    I_d = Matrix{ComplexF64}(I, d, d)
    z = zeros(ComplexF64, d, d)
    maxres = 0.0
    for a in 1:length(gs), b in 1:length(gs)
        expected = a == b ? 2 * eta[a] * I_d : z
        maxres = max(maxres, maximum(abs.(gs[a] * gs[b] + gs[b] * gs[a] - expected)))
    end
    return maxres
end

function commutator_gap(gs)
    gaps = Float64[]
    for a in 1:length(gs), b in a+1:length(gs)
        push!(gaps, norm(gs[a] * gs[b] - gs[b] * gs[a]))
    end
    return maximum(gaps), gaps
end

function coeff_in_basis(M, basis)
    G = hcat([vec(b) for b in basis]...)
    x = G \ vec(M)
    return x
end

function rotor_matrix(R, basis)
    Rinv = inv(R)
    cols = Vector{Float64}[]
    for b in basis
        coeffs = coeff_in_basis(R * b * Rinv, basis)
        push!(cols, real.(coeffs))
    end
    return hcat(cols...)
end

function rotor_report(name, B, theta, basis)
    d = size(B, 1)
    I_d = Matrix{ComplexF64}(I, d, d)
    B_sq_residual = norm(B * B + I_d)
    R = cos(theta / 2) * I_d - sin(theta / 2) * B
    Rneg = -R
    M = rotor_matrix(R, basis)
    Mneg = rotor_matrix(Rneg, basis)
    orth_err = norm(transpose(M) * M - I(3))
    det_M = det(M)
    double_cover_gap = norm(M - Mneg)
    return Dict{String,Any}(
        "name" => name,
        "theta" => theta,
        "bivector_square_minus_I_residual" => B_sq_residual,
        "matrix" => [[M[i,j] for j in 1:size(M,2)] for i in 1:size(M,1)],
        "orthogonality_error" => orth_err,
        "det" => det_M,
        "double_cover_gap_R_vs_minus_R" => double_cover_gap,
        "passes_rotor_SO3_signature" => B_sq_residual < 1e-8 && orth_err < 1e-8 &&
                                        abs(det_M - 1.0) < 1e-8 && double_cover_gap < 1e-8,
    )
end

function von_neumann_entropy(rho; tol=1e-12)
    vals = real.(eigvals(Hermitian((rho + rho') / 2)))
    vals = [v for v in vals if v > tol]
    return isempty(vals) ? 0.0 : -sum(vals .* log2.(vals))
end

function partial_trace_second_qubit(rho4)
    out = zeros(ComplexF64, 2, 2)
    for a in 1:2, b in 1:2, s in 1:2
        out[a,b] += rho4[2*(a-1)+s, 2*(b-1)+s]
    end
    return out
end

function peps3d_complex(nx, ny, nz)
    id(x, y, z) = x + nx * (y - 1) + nx * ny * (z - 1)
    V = collect(1:(nx * ny * nz))
    E = Vector{Vector{Int}}()
    F = Vector{Vector{Int}}()
    C = Vector{Vector{Int}}()
    for z in 1:nz, y in 1:ny, x in 1:nx
        x < nx && push!(E, [id(x,y,z), id(x+1,y,z)])
        y < ny && push!(E, [id(x,y,z), id(x,y+1,z)])
        z < nz && push!(E, [id(x,y,z), id(x,y,z+1)])
    end
    for z in 1:nz, y in 1:ny-1, x in 1:nx-1
        push!(F, [id(x,y,z), id(x+1,y,z), id(x+1,y+1,z), id(x,y+1,z)])
    end
    for z in 1:nz-1, y in 1:ny, x in 1:nx-1
        push!(F, [id(x,y,z), id(x+1,y,z), id(x+1,y,z+1), id(x,y,z+1)])
    end
    for z in 1:nz-1, y in 1:ny-1, x in 1:nx
        push!(F, [id(x,y,z), id(x,y+1,z), id(x,y+1,z+1), id(x,y,z+1)])
    end
    for z in 1:nz-1, y in 1:ny-1, x in 1:nx-1
        push!(C, [id(x,y,z), id(x+1,y,z), id(x,y+1,z), id(x+1,y+1,z),
                  id(x,y,z+1), id(x+1,y,z+1), id(x,y+1,z+1), id(x+1,y+1,z+1)])
    end
    return Dict{String,Any}(
        "dims" => [nx, ny, nz],
        "V" => V,
        "E" => E,
        "F" => F,
        "C" => C,
        "counts" => Dict("V" => length(V), "E" => length(E), "F" => length(F), "C" => length(C)),
    )
end

function signature_for(name, gs)
    eta = [1.0, -1.0, -1.0, -1.0]
    gamma5 = im * gs[1] * gs[2] * gs[3] * gs[4]
    rank16 = burnside_rank(gs)
    commdim = commutant_dim(gs)
    cliffres = max_clifford_residual(gs, eta)
    n01gap, n01pairs = commutator_gap(gs)
    g5sq = norm(gamma5 * gamma5 - Matrix{ComplexF64}(I, 4, 4))
    spatial_basis = [gs[2], gs[3], gs[4]]
    rotors = [
        rotor_report("spatial_B12", gs[2] * gs[3], 0.73, spatial_basis),
        rotor_report("spatial_B23", gs[3] * gs[4], 0.73, spatial_basis),
        rotor_report("spatial_B31", gs[4] * gs[2], 0.73, spatial_basis),
    ]
    return Dict{String,Any}(
        "name" => name,
        "burnside_rank" => rank16,
        "burnside_target" => 16,
        "schur_commutant_dim" => commdim,
        "clifford_relation_max_residual" => cliffres,
        "gamma5_square_residual" => g5sq,
        "N01_noncommuting_gap_max_frobenius" => n01gap,
        "N01_pairwise_frobenius_gaps" => n01pairs,
        "faithful_irreducible_signature" => rank16 == 16 && commdim == 1 && cliffres < 1e-8 && g5sq < 1e-8,
        "rotor_reports" => rotors,
        "rotor_pass_count" => count(r -> r["passes_rotor_SO3_signature"], rotors),
    )
end

# Weyl/chiral representation of Cl(1,3), mostly-minus signature.
s0 = ComplexF64[1 0; 0 1]
s1 = ComplexF64[0 1; 1 0]
s2 = ComplexF64[0 -im; im 0]
s3 = ComplexF64[1 0; 0 -1]
z2 = zeros(ComplexF64, 2, 2)

g0 = [z2 s0; s0 z2]
g1 = [z2 s1; -s1 z2]
g2 = [z2 s2; -s2 z2]
g3 = [z2 s3; -s3 z2]
good_gammas = [g0, g1, g2, g3]
broken_gammas = [g0, g1, g2, g2]

good = signature_for("good_Cl_1_3_module", good_gammas)
broken = signature_for("broken_g3_equals_g2", broken_gammas)

red8_gammas = [[good_gammas[i] zeros(ComplexF64, 4, 4); zeros(ComplexF64, 4, 4) good_gammas[i]] for i in 1:4]
red8 = Dict{String,Any}(
    "name" => "reducible_direct_sum_rho_plus_rho",
    "burnside_rank" => burnside_rank(red8_gammas),
    "burnside_target" => 64,
    "schur_commutant_dim" => commutant_dim(red8_gammas),
)
red8["rejected_as_irreducible"] = !(red8["burnside_rank"] == 64 && red8["schur_commutant_dim"] == 1)

gamma5 = im * g0 * g1 * g2 * g3
psi = ComplexF64[1, 0, 1, im]
psi ./= norm(psi)
rho = psi * psi'
rho_chiral = partial_trace_second_qubit(rho)
q_gamma5 = real(psi' * gamma5 * psi)
entropy = Dict{String,Any}(
    "rho_trace" => real(tr(rho)),
    "rho_purity" => real(tr(rho * rho)),
    "dirac_state_entropy_bits" => von_neumann_entropy(rho),
    "chiral_reduced_entropy_bits" => von_neumann_entropy(rho_chiral),
    "gamma5_expectation" => q_gamma5,
    "note" => "QIT readouts are derived from the Julia-native spinor density after the Clifford module is built; they do not define the module.",
)

peps_stress = Dict{String,Any}()
for (label, dims) in Dict("8" => (2,2,2), "16" => (4,2,2), "32" => (4,4,2), "64" => (4,4,4))
    K = peps3d_complex(dims...)
    peps_stress[label] = Dict{String,Any}(
        "K" => K,
        "local_cell_payload" => "each v in V carries the same 4-component Dirac spinor module; each edge/face/cell records adjacency for later PEPS3D contraction",
        "local_burnside_rank" => good["burnside_rank"],
        "local_commutant_dim" => good["schur_commutant_dim"],
        "global_contraction_status" => "not_claimed_resource_blocker_global_4^N_state_not_constructed",
    )
end

dependency_forcing = Dict{String,Any}(
    "erasure" => "break Clifford anticommutator by setting g3 := g2",
    "burnside_rank_good_to_broken" => [good["burnside_rank"], broken["burnside_rank"]],
    "burnside_rank_delta" => good["burnside_rank"] - broken["burnside_rank"],
    "commutant_dim_good_to_broken" => [good["schur_commutant_dim"], broken["schur_commutant_dim"]],
    "clifford_residual_good_to_broken" => [good["clifford_relation_max_residual"], broken["clifford_relation_max_residual"]],
    "gamma5_sq_residual_good_to_broken" => [good["gamma5_square_residual"], broken["gamma5_square_residual"]],
    "rotor_pass_count_good_to_broken" => [good["rotor_pass_count"], broken["rotor_pass_count"]],
)
dependency_forcing["module_signature_collapsed"] =
    broken["burnside_rank"] < good["burnside_rank"] &&
    broken["schur_commutant_dim"] > good["schur_commutant_dim"] &&
    broken["clifford_relation_max_residual"] > 1e-8
dependency_forcing["rotor_signature_collapsed"] = broken["rotor_pass_count"] < good["rotor_pass_count"]

minimum_standard = Dict{String,Any}(
    "finite_map" => "finite gamma-word/module action map: ({16 Clifford words}, finite spinor set, PEPS3D local cells) -> {Burnside rank, Schur commutant dim, gamma5^2 residual, rotor SO3 readouts, derived density entropy}",
    "domain" => Dict(
        "operator_words" => "1, 4 generators, 6 bivectors, 4 trivectors, 1 top word",
        "spinor_state" => "psi in ComplexF64^4, normalized",
        "peps3d_anchor" => "K=(V,E,F,C) for site counts 8,16,32,64",
    ),
    "codomain_or_output" => "finite numeric signature and derived QIT readouts",
    "F01_witness" => Dict("finite_operator_word_count" => 16, "finite_site_counts" => [8,16,32,64]),
    "N01_witness" => Dict("gap" => good["N01_noncommuting_gap_max_frobenius"], "passes" => good["N01_noncommuting_gap_max_frobenius"] > 1e-8),
    "julia_native_spinor_density" => Dict("spinor_length" => length(psi), "rho_size" => collect(size(rho)), "uses_numpy" => false),
    "peps3d_embedding" => "present as finite K=(V,E,F,C) anchors for 8/16/32/64 local-cell stress; global PEPS contraction explicitly not claimed",
    "site_shell_stress" => "8/16/32/64 local-cell PEPS3D anchor stress present; global 4^N tensor contraction blocked/not claimed",
    "load_bearing_tool_manifest" => Dict(
        "LinearAlgebra" => "load_bearing: SVD/rank/nullspace/eigenspectrum decide Burnside rank, Schur commutant, rotor orthogonality, and entropy",
        "JSON" => "artifact writer only",
        "Z3" => "z3 omitted, not decorative; the decisive claims are measured matrix ranks/nullspaces and the broken-input verdict flips numerically",
    ),
    "non_vacuous_ablation" => dependency_forcing,
    "qit_readouts_derived" => entropy,
    "negative_controls" => Dict("broken_g3_equals_g2" => broken, "reducible_direct_sum" => red8),
    "blocked_consumers" => ["stacking", "L10 terrain", "L11 operator substage", "L12 entropy/cut promotion", "L13 gluing promotion", "Axis0", "flux", "FEP", "physics", "final manifold admission"],
    "promotion_allowed" => false,
)

booleans = Dict{String,Bool}(
    "good_clifford_module_signature" => good["faithful_irreducible_signature"],
    "gamma5_square_plus_one" => good["gamma5_square_residual"] < 1e-8,
    "N01_gap_nonzero" => good["N01_noncommuting_gap_max_frobenius"] > 1e-8,
    "broken_module_collapses" => dependency_forcing["module_signature_collapsed"],
    "broken_rotor_collapses" => dependency_forcing["rotor_signature_collapsed"],
    "reducible_control_rejected" => red8["rejected_as_irreducible"],
    "peps3d_anchors_present" => all(haskey(peps_stress[string(n)]["K"], "V") for n in [8,16,32,64]),
    "promotion_blocked" => minimum_standard["promotion_allowed"] == false,
)

all_pass = all(values(booleans))

results = Dict{String,Any}(
    "sim_id" => "L9_layer_codex",
    "name" => "L9 Clifford / quaternion module finite-QIT constraint-manifold PoC",
    "version" => "1.0",
    "summary" => Dict{String,Any}(
        "min_gaps" => Dict{String,Float64}(
            "burnside_rank_delta_gap" => Float64(dependency_forcing["burnside_rank_delta"]),
            "commutant_dim_delta_gap" => Float64(broken["schur_commutant_dim"] - good["schur_commutant_dim"]),
            "clifford_relation_residual_delta_gap" => Float64(broken["clifford_relation_max_residual"] - good["clifford_relation_max_residual"]),
            "gamma5_square_residual_delta_gap" => Float64(broken["gamma5_square_residual"] - good["gamma5_square_residual"]),
            "rotor_pass_count_delta_gap" => Float64(good["rotor_pass_count"] - broken["rotor_pass_count"]),
        ),
        "observable_signature" => Dict{String,Any}(
            "burnside_rank" => good["burnside_rank"],
            "schur_commutant_dim" => good["schur_commutant_dim"],
            "gamma5_square_residual" => good["gamma5_square_residual"],
            "rotor_pass_count" => good["rotor_pass_count"],
        ),
    ),
    "controls" => Dict{String,Any}(
        "positive" => Dict{String,Any}(
            "burnside_rank_delta_gap" => dependency_forcing["burnside_rank_delta"],
            "commutant_dim_delta_gap" => broken["schur_commutant_dim"] - good["schur_commutant_dim"],
            "clifford_relation_residual_delta_gap" => broken["clifford_relation_max_residual"] - good["clifford_relation_max_residual"],
            "gamma5_square_residual_delta_gap" => broken["gamma5_square_residual"] - good["gamma5_square_residual"],
            "rotor_pass_count_delta_gap" => good["rotor_pass_count"] - broken["rotor_pass_count"],
        ),
        "negative" => Dict{String,Any}(
            "broken_input_module_collapsed" => dependency_forcing["module_signature_collapsed"],
            "broken_input_rotor_collapsed" => dependency_forcing["rotor_signature_collapsed"],
            "reducible_control_rejected" => red8["rejected_as_irreducible"],
        ),
    ),
    "classification" => "L9_layer_codex_poc",
    "promotion_allowed" => false,
    "sim_execution_kind" => "nonclassical",
    "sim_class" => "geometry_probe",
    "fresh_rerun" => Dict("command" => "julia --project=\"/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier\" \"/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/layers/L9_layer_codex.jl\"", "result_path" => OUTPATH),
    "quoted_math_from_registry_or_request" => [
        "Registry L9: Clifford / quaternion module layer; Cl3 / Cl6 action, rotors, geometric product, quaternion maps.",
        "Registry minimum: finite_map, F01 witness, N01 witness, PEPS3D K=(V,E,F,C), stress, non-vacuous ablation, QIT derived readouts, controls, blocked consumers.",
        "Request math: Cl(1,3) faithful irreducible 4-dim module; Burnside image rank 16/16 = M4(C), Schur commutant dim 1; gamma5 = i g0g1g2g3, gamma5^2=+1.",
    ],
    "root_constraints_in_force" => ["F01 finite carrier/probe/operator/path set", "N01 noncommuting or order-sensitive operation/control"],
    "finite_map" => minimum_standard["finite_map"],
    "domain" => minimum_standard["domain"],
    "codomain_or_output" => minimum_standard["codomain_or_output"],
    "carrier_layer" => "Dirac spinor ComplexF64^4 local cell module",
    "geometry_layer" => "L9 Clifford/quaternion module",
    "carrier_realization" => "Julia-native ComplexF64 matrices/vectors; LinearAlgebra ranks/nullspaces/eigenspectra; no NumPy",
    "peps3d_embedding" => peps_stress,
    "spinor_state" => Dict("psi" => [[real(x), imag(x)] for x in psi], "density_trace" => entropy["rho_trace"], "density_purity" => entropy["rho_purity"]),
    "quaternion_action" => "spatial Clifford bivectors g_i*g_j act as quaternion/rotor generators; rotor SO3 signatures measured for B12,B23,B31",
    "dependency_receipts" => ["system_v5/ops/MANIFOLD_GEOMETRY_LAYER_STACK_NONCOMMUTATIVE_ORDER_20260528.md", "system_v5/READ ONLY Reference Docs/Formal constraints and geometry .md"],
    "downstream_blocks" => minimum_standard["blocked_consumers"],
    "allowed_claims" => ["local L9 PoC signature only", "broken Clifford dependency forcing collapses measured module/rotor signatures"],
    "promotion_blockers" => ["global PEPS3D contraction not constructed", "not a parent-complete stacking receipt", "promotion_allowed=false by request"],
    "tool_manifest" => minimum_standard["load_bearing_tool_manifest"],
    "tool_integration_depth" => Dict("LinearAlgebra" => "load_bearing", "JSON" => "supportive", "Z3" => "None"),
    "good_signature" => good,
    "dependency_forcing" => dependency_forcing,
    "negative_controls" => minimum_standard["negative_controls"],
    "qit_readouts" => entropy,
    "minimum_standard" => minimum_standard,
    "genuineness_booleans" => booleans,
    "all_pass" => all_pass,
    "honest_gaps" => ["No global PEPS3D tensor contraction is claimed; K=(V,E,F,C) is a finite local-cell anchor/stress only.", "No Z3 block was used because it would not be load-bearing for floating rank/nullspace measurements.", "This is not a layer-completion or stacking-admission claim."],
)

println("="^78)
println("L9_layer_codex — Clifford / quaternion module PoC")
println("="^78)
println("good Burnside rank: ", good["burnside_rank"], " / 16")
println("good Schur commutant dim: ", good["schur_commutant_dim"])
println("good gamma5^2 residual: ", good["gamma5_square_residual"])
println("broken Burnside rank: ", broken["burnside_rank"], " / 16")
println("broken Schur commutant dim: ", broken["schur_commutant_dim"])
println("broken Clifford residual: ", broken["clifford_relation_max_residual"])
println("rotor pass count good -> broken: ", good["rotor_pass_count"], " -> ", broken["rotor_pass_count"])
println("all_pass: ", all_pass)

open(OUTPATH, "w") do io
    JSON.print(io, results, 2)
end
println("results written to: ", OUTPATH)
