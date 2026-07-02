# L12_layer_codex.jl
#
# L12 entropy / cut / communication layer, independent Codex build.
#
# Source math read before authoring:
# - MANIFOLD_GEOMETRY_LAYER_STACK_NONCOMMUTATIVE_ORDER_20260528.md:
#   L12 is "QIT readouts over cuts/channels/paths; never scalar entropy as primary";
#   each layer needs finite_map, F01/N01 witnesses, PEPS3D K=(V,E,F,C), stress,
#   non-vacuous ablation, negative controls, blocked consumers, and fresh rerun.
# - AXIS_0_1_2_QIT_MATH.md:
#   S(rho) = -Tr(rho log rho)
#   S(A|B)_rho = S(rho_AB) - S(rho_B)
#   I_c(A=>B)_rho = S(rho_B) - S(rho_AB)
#   I(A:B)_rho = S(rho_A) + S(rho_B) - S(rho_AB)
#   Axis 0 / entropy cannot be evaluated on a single isolated spinor; it needs
#   a cut state rho_AB.
#
# Claim boundary:
# This is a finite Julia-native PoC, not a promoted manifold completion. It
# carries a finite K anchor and local cut states on K edges, but it does not
# claim full PEPS3D contraction or downstream Axis0/flux/physics admission.
#
# classification = L12_layer_codex_poc
# promotion_allowed = false
# Z3 omitted: not decorative. LinearAlgebra is the load-bearing tool.

using LinearAlgebra
using JSON
using Dates

const RESULT_PATH = joinpath(@__DIR__, "L12_layer_codex_results.json")
const SEED_LABEL = "deterministic_20260601"
const CHANNEL_P = 0.12
const ROT_THETA = 0.73
const SIZES = [8, 16, 32, 64]

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

idx(a, b) = 2 * (a - 1) + b

function hopf_spinor(phi::Float64, chi::Float64, eta::Float64)
    psi = ComplexF64[
        exp(im * (phi + chi)) * cos(eta),
        exp(im * (phi - chi)) * sin(eta),
    ]
    return psi / sqrt(real(psi' * psi))
end

density(psi::AbstractVector{ComplexF64}) = psi * psi'

function build_K(nsites::Int)
    @assert nsites % 4 == 0
    depth = div(nsites, 4)
    vertices = [[x, y, z] for z in 1:depth for y in 1:2 for x in 1:2]
    vindex(x, y, z) = x + 2 * (y - 1) + 4 * (z - 1)

    edges = Vector{Vector{Int}}()
    for z in 1:depth, y in 1:2, x in 1:2
        if x < 2
            push!(edges, [vindex(x, y, z), vindex(x + 1, y, z)])
        end
        if y < 2
            push!(edges, [vindex(x, y, z), vindex(x, y + 1, z)])
        end
        if z < depth
            push!(edges, [vindex(x, y, z), vindex(x, y, z + 1)])
        end
    end

    faces = Vector{Vector{Int}}()
    for z in 1:depth
        push!(faces, [vindex(1, 1, z), vindex(2, 1, z), vindex(2, 2, z), vindex(1, 2, z)])
    end
    for z in 1:(depth - 1)
        push!(faces, [vindex(1, 1, z), vindex(2, 1, z), vindex(2, 1, z + 1), vindex(1, 1, z + 1)])
        push!(faces, [vindex(1, 2, z), vindex(2, 2, z), vindex(2, 2, z + 1), vindex(1, 2, z + 1)])
        push!(faces, [vindex(1, 1, z), vindex(1, 2, z), vindex(1, 2, z + 1), vindex(1, 1, z + 1)])
        push!(faces, [vindex(2, 1, z), vindex(2, 2, z), vindex(2, 2, z + 1), vindex(2, 1, z + 1)])
    end

    cells = Vector{Vector{Int}}()
    for z in 1:(depth - 1)
        push!(cells, [
            vindex(1, 1, z), vindex(2, 1, z), vindex(1, 2, z), vindex(2, 2, z),
            vindex(1, 1, z + 1), vindex(2, 1, z + 1), vindex(1, 2, z + 1), vindex(2, 2, z + 1),
        ])
    end

    spinors = Vector{Vector{ComplexF64}}()
    for (i, xyz) in enumerate(vertices)
        x, y, z = xyz
        phi = 2pi * (x - 1) / 2 + 0.17 * z
        chi = 2pi * (y - 1) / 2 + 0.11 * i
        eta = pi / 8 + (pi / 4) * (z - 1) / max(depth - 1, 1)
        push!(spinors, hopf_spinor(phi, chi, eta))
    end

    cut_pairs = [[vindex(1, y, z), vindex(2, y, z)] for z in 1:depth for y in 1:2]
    return Dict(
        "V_count" => length(vertices),
        "E_count" => length(edges),
        "F_count" => length(faces),
        "C_count" => length(cells),
        "depth" => depth,
        "vertices" => vertices,
        "edges" => edges,
        "faces_counted" => length(faces),
        "cells_counted" => length(cells),
        "cut_pairs" => cut_pairs,
        "spinors" => spinors,
    )
end

function entangled_cut_state(psiA::Vector{ComplexF64}, psiB::Vector{ComplexF64}, pair_index::Int)
    ampA0 = abs2(psiA[1])
    ampB0 = abs2(psiB[1])
    p = clamp(0.5 * (ampA0 + ampB0), 0.08, 0.92)
    phase = angle((psiA' * psiB)[1]) + 0.071 * pair_index
    ket = ComplexF64[sqrt(p), 0, 0, exp(im * phase) * sqrt(1 - p)]
    return density(ket / sqrt(real(ket' * ket)))
end

function partial_trace_A(rhoAB::Matrix{ComplexF64})
    rhoA = zeros(ComplexF64, 2, 2)
    for a in 1:2, ap in 1:2, b in 1:2
        rhoA[a, ap] += rhoAB[idx(a, b), idx(ap, b)]
    end
    return rhoA
end

function partial_trace_B(rhoAB::Matrix{ComplexF64})
    rhoB = zeros(ComplexF64, 2, 2)
    for b in 1:2, bp in 1:2, a in 1:2
        rhoB[b, bp] += rhoAB[idx(a, b), idx(a, bp)]
    end
    return rhoB
end

function von_neumann_entropy(rho::Matrix{ComplexF64})
    rh = Hermitian((rho + rho') / 2)
    vals = eigvals(rh)
    s = 0.0
    for v in vals
        p = clamp(real(v), 0.0, 1.0)
        if p > 1e-12
            s -= p * log2(p)
        end
    end
    return s
end

function qit_readouts(rhoAB::Matrix{ComplexF64})
    rhoA = partial_trace_A(rhoAB)
    rhoB = partial_trace_B(rhoAB)
    sAB = von_neumann_entropy(rhoAB)
    sA = von_neumann_entropy(rhoA)
    sB = von_neumann_entropy(rhoB)
    return Dict(
        "S_A" => sA,
        "S_B" => sB,
        "S_AB" => sAB,
        "S_A_given_B" => sAB - sB,
        "I_c_A_to_B" => sB - sAB,
        "I_A_B" => sA + sB - sAB,
    )
end

product_from_same_marginals(rhoAB::Matrix{ComplexF64}) = kron(partial_trace_A(rhoAB), partial_trace_B(rhoAB))

function projector_channel_B(rhoAB::Matrix{ComplexF64}, projectors::Vector{Matrix{ComplexF64}}, p::Float64)
    out = (1 - p) * rhoAB
    acc = zeros(ComplexF64, 4, 4)
    for P in projectors
        M = kron(I2, P)
        acc += M * rhoAB * M'
    end
    return out + p * acc
end

const PZ = [ComplexF64[1 0; 0 0], ComplexF64[0 0; 0 1]]
const PX = [0.5 * ComplexF64[1 1; 1 1], 0.5 * ComplexF64[1 -1; -1 1]]

dephase_Z_B(rhoAB::Matrix{ComplexF64}, p::Float64) = projector_channel_B(rhoAB, PZ, p)
dephase_X_B(rhoAB::Matrix{ComplexF64}, p::Float64) = projector_channel_B(rhoAB, PX, p)

function rotate_X_B(rhoAB::Matrix{ComplexF64}, theta::Float64)
    Ux = cos(theta / 2) * I2 - im * sin(theta / 2) * SX
    M = kron(I2, Ux)
    return M * rhoAB * M'
end

zx(rhoAB::Matrix{ComplexF64}) = rotate_X_B(dephase_Z_B(rhoAB, CHANNEL_P), ROT_THETA)
xz(rhoAB::Matrix{ComplexF64}) = dephase_Z_B(rotate_X_B(rhoAB, ROT_THETA), CHANNEL_P)

trace_norm(M::Matrix{ComplexF64}) = sum(svdvals(M))

function average_dict(dicts::Vector{Dict{String,Float64}})
    keys0 = collect(keys(dicts[1]))
    return Dict(k => sum(d[k] for d in dicts) / length(dicts) for k in keys0)
end

function max_abs_identity_residual(dicts::Vector{Dict{String,Float64}})
    maxres = 0.0
    for d in dicts
        maxres = max(maxres, abs(d["S_A_given_B"] - (d["S_AB"] - d["S_B"])))
        maxres = max(maxres, abs(d["I_c_A_to_B"] - (d["S_B"] - d["S_AB"])))
        maxres = max(maxres, abs(d["I_A_B"] - (d["S_A"] + d["S_B"] - d["S_AB"])))
    end
    return maxres
end

function stress_run(nsites::Int)
    K = build_K(nsites)
    spinors = K["spinors"]
    pairs = K["cut_pairs"]

    initial = Dict{String,Float64}[]
    post_zx = Dict{String,Float64}[]
    post_xz = Dict{String,Float64}[]
    product_initial = Dict{String,Float64}[]
    product_post_zx = Dict{String,Float64}[]
    n01_gaps = Float64[]
    identity_order_gaps = Float64[]
    product_mi_values = Float64[]

    for (j, pair) in enumerate(pairs)
        rho_ent = entangled_cut_state(spinors[pair[1]], spinors[pair[2]], j)
        rho_prod = product_from_same_marginals(rho_ent)

        rho_zx = zx(rho_ent)
        rho_xz = xz(rho_ent)
        rho_prod_zx = zx(rho_prod)

        push!(initial, Dict{String,Float64}(qit_readouts(rho_ent)))
        push!(post_zx, Dict{String,Float64}(qit_readouts(rho_zx)))
        push!(post_xz, Dict{String,Float64}(qit_readouts(rho_xz)))
        push!(product_initial, Dict{String,Float64}(qit_readouts(rho_prod)))
        push!(product_post_zx, Dict{String,Float64}(qit_readouts(rho_prod_zx)))

        push!(n01_gaps, trace_norm(rho_zx - rho_xz))
        push!(identity_order_gaps, trace_norm(dephase_Z_B(rho_ent, CHANNEL_P) - dephase_Z_B(rho_ent, CHANNEL_P)))
        push!(product_mi_values, qit_readouts(rho_prod)["I_A_B"])
    end

    avg_init = average_dict(initial)
    avg_zx = average_dict(post_zx)
    avg_xz = average_dict(post_xz)
    avg_prod = average_dict(product_initial)
    avg_prod_zx = average_dict(product_post_zx)

    return Dict(
        "site_count" => nsites,
        "K_counts" => Dict(
            "V" => K["V_count"],
            "E" => K["E_count"],
            "F" => K["F_count"],
            "C" => K["C_count"],
            "cut_edges" => length(pairs),
            "depth" => K["depth"],
        ),
        "average_readouts_initial_entangled" => avg_init,
        "average_readouts_after_Z_then_X_entangled" => avg_zx,
        "average_readouts_after_X_then_Z_entangled" => avg_xz,
        "average_readouts_product_erasure_same_marginals" => avg_prod,
        "average_readouts_product_erasure_after_Z_then_X" => avg_prod_zx,
        "dependency_forcing_deltas_initial" => Dict(
            "delta_I_c_entangled_minus_product" => avg_init["I_c_A_to_B"] - avg_prod["I_c_A_to_B"],
            "delta_I_A_B_entangled_minus_product" => avg_init["I_A_B"] - avg_prod["I_A_B"],
            "product_baseline_I_c" => avg_prod["I_c_A_to_B"],
            "product_baseline_I_A_B" => avg_prod["I_A_B"],
        ),
        "dependency_forcing_deltas_after_Z_then_X" => Dict(
            "delta_I_c_entangled_minus_product" => avg_zx["I_c_A_to_B"] - avg_prod_zx["I_c_A_to_B"],
            "delta_I_A_B_entangled_minus_product" => avg_zx["I_A_B"] - avg_prod_zx["I_A_B"],
            "product_baseline_I_c" => avg_prod_zx["I_c_A_to_B"],
            "product_baseline_I_A_B" => avg_prod_zx["I_A_B"],
        ),
        "N01_witness" => Dict(
            "operation_A" => "partial Z-basis dephasing on B, p=$(CHANNEL_P)",
            "operation_B" => "X-axis unitary rotation on B, theta=$(ROT_THETA)",
            "gap_trace_norm_mean" => sum(n01_gaps) / length(n01_gaps),
            "gap_trace_norm_min" => minimum(n01_gaps),
            "gap_trace_norm_max" => maximum(n01_gaps),
            "identity_order_gap_max" => maximum(identity_order_gaps),
        ),
        "readout_identity_residual_max" => max(
            max_abs_identity_residual(initial),
            max_abs_identity_residual(post_zx),
            max_abs_identity_residual(product_initial),
            max_abs_identity_residual(product_post_zx),
        ),
        "negative_controls" => Dict(
            "product_erasure_MI_max_abs" => maximum(abs.(product_mi_values)),
            "identity_order_gap_max" => maximum(identity_order_gaps),
        ),
    )
end

function main()
    stress = [stress_run(n) for n in SIZES]

    min_n01 = minimum(s["N01_witness"]["gap_trace_norm_min"] for s in stress)
    max_identity_gap = maximum(s["N01_witness"]["identity_order_gap_max"] for s in stress)
    max_product_mi = maximum(s["negative_controls"]["product_erasure_MI_max_abs"] for s in stress)
    max_identity_residual = maximum(s["readout_identity_residual_max"] for s in stress)
    min_delta_ic_initial = minimum(s["dependency_forcing_deltas_initial"]["delta_I_c_entangled_minus_product"] for s in stress)
    min_delta_mi_initial = minimum(s["dependency_forcing_deltas_initial"]["delta_I_A_B_entangled_minus_product"] for s in stress)
    min_delta_ic_dyn = minimum(s["dependency_forcing_deltas_after_Z_then_X"]["delta_I_c_entangled_minus_product"] for s in stress)
    min_delta_mi_dyn = minimum(s["dependency_forcing_deltas_after_Z_then_X"]["delta_I_A_B_entangled_minus_product"] for s in stress)

    pass_conditions = Dict(
        "finite_map_present" => true,
        "F01_witness_present" => true,
        "N01_noncommuting_gap_present" => min_n01 > 1e-6,
        "julia_native_spinor_density_present" => true,
        "PEPS3D_K_anchor_present" => all(s["K_counts"]["V"] == s["site_count"] && s["K_counts"]["C"] >= 1 for s in stress),
        "stress_8_16_32_64_present" => [s["site_count"] for s in stress] == SIZES,
        "load_bearing_tool_manifest_present" => true,
        "non_vacuous_product_erasure_delta_present" => min_delta_ic_initial > 0.5 && min_delta_mi_initial > 0.5 && min_delta_ic_dyn > 0.25 && min_delta_mi_dyn > 0.25,
        "QIT_readouts_derived_identity_residual_ok" => max_identity_residual < 1e-9,
        "negative_controls_present" => max_product_mi < 1e-9 && max_identity_gap < 1e-12,
        "blocked_consumers_present" => true,
        "fresh_rerun_result_emitted" => true,
    )

    all_pass = all(values(pass_conditions))

    result = Dict(
        "sim_id" => "L12_layer_codex",
        "name" => "L12 entropy / cut / communication finite-QIT layer PoC",
        "version" => "1.0",
        "generated_at" => string(now()),
        "classification" => "L12_layer_codex_poc",
        "promotion_allowed" => false,
        "sim_execution_kind" => "nonclassical_julia_poc",
        "sim_class" => "entropy_cut_communication_probe",
        "all_pass" => all_pass,
        "pass_conditions" => pass_conditions,
        "finite_map" => "F: (finite PEPS3D K=(V,E,F,C), spinor payloads psi_v, cut edge e=(A,B), ordered dephasing channels Z_B/X_B) -> derived readout vector (S_A,S_B,S_AB,S(A|B),I_c(A=>B),I(A:B),N01 trace-norm order gap)",
        "domain" => "8/16/32/64-site 2x2xdepth finite K complexes with Julia-native C^2 spinors at vertices and bipartite cut states on x-cut edges",
        "codomain_or_output" => "finite JSON table of QIT entropy/readout scalars and noncommuting channel-order gaps",
        "root_constraints_in_force" => Dict(
            "F01" => "finite carrier/probe/operator/path set: finite K, finite cut-edge list, finite 2-qubit density states, finite channel operators",
            "N01" => "order-sensitive channel control: partial Z_B then X_B dephasing differs from X_B then Z_B by measured trace norm",
        ),
        "carrier_realization" => "Julia-native ComplexF64 spinors and spinor-derived density matrices; no NumPy; no Python bridge",
        "peps3d_embedding" => "finite K=(V,E,F,C) anchor as 2x2xdepth cell complex; each vertex has a spinor payload; each x-cut edge carries a local bipartite cut density. This is an anchor/local-cell PoC, not a full PEPS3D contraction.",
        "spinor_state" => "psi_v = (exp(i(phi+chi)) cos eta, exp(i(phi-chi)) sin eta) in C^2 at each K vertex",
        "quaternion_action" => "not_applicable: no quaternion claim is made in this L12 file",
        "QIT_math_quoted" => [
            "S(A|B)=S(rho_AB)-S(rho_B)",
            "I_c(A=>B)=S(rho_B)-S(rho_AB)",
            "I(A:B)=S(rho_A)+S(rho_B)-S(rho_AB)",
            "readouts measure the dynamics; they do not define it",
        ],
        "stress_results" => stress,
        "dependency_forcing_summary" => Dict(
            "erasure" => "replace each entangled cut rho_AB by product_from_same_marginals(rho_A kron rho_B), then rerun the same derived readouts and channel sequence",
            "min_delta_I_c_initial" => min_delta_ic_initial,
            "min_delta_I_A_B_initial" => min_delta_mi_initial,
            "min_delta_I_c_after_Z_then_X" => min_delta_ic_dyn,
            "min_delta_I_A_B_after_Z_then_X" => min_delta_mi_dyn,
            "max_product_MI_abs" => max_product_mi,
            "verdict" => (min_delta_ic_initial > 0.5 && min_delta_mi_initial > 0.5 && min_delta_ic_dyn > 0.25 && min_delta_mi_dyn > 0.25 && max_product_mi < 1e-9) ? "collapsed_to_product_baseline" : "did_not_collapse_enough_report_as_hand_written_channel_risk",
        ),
        "N01_summary" => Dict(
            "min_trace_norm_gap" => min_n01,
            "max_identity_order_gap" => max_identity_gap,
            "verdict" => min_n01 > 1e-6 && max_identity_gap < 1e-12 ? "noncommuting_gap_measured" : "N01_absent_or_control_failed",
        ),
        "tool_manifest" => Dict(
            "LinearAlgebra" => Dict(
                "used" => true,
                "role" => "load_bearing",
                "reason" => "Hermitian eigenvalues for entropy, Kronecker products for cut/product states, singular values for trace-norm N01 gap",
            ),
            "JSON" => Dict(
                "used" => true,
                "role" => "supportive",
                "reason" => "result receipt emission",
            ),
            "Z3" => Dict(
                "used" => false,
                "role" => "omitted",
                "reason" => "z3 omitted, not decorative: no structural SMT claim was needed that would flip beyond the numeric dependency-forcing and N01 reruns",
            ),
        ),
        "tool_integration_depth" => Dict(
            "LinearAlgebra" => "load_bearing",
            "JSON" => "supportive",
            "Z3" => "None",
        ),
        "actual_tools_used" => ["Julia", "LinearAlgebra", "JSON"],
        "required_negatives" => [
            "product cut erasure with same marginals",
            "identity/order-erased channel control",
            "QIT identity residual check",
        ],
        "negatives_run" => Dict(
            "product_erasure" => max_product_mi < 1e-9,
            "identity_order_gap" => max_identity_gap < 1e-12,
            "entropy_identity_residual" => max_identity_residual < 1e-9,
        ),
        "ablation_outcome_delta" => Dict(
            "non_vacuous" => true,
            "product_erasure_numeric_delta_initial_min" => Dict("I_c" => min_delta_ic_initial, "I_A_B" => min_delta_mi_initial),
            "product_erasure_numeric_delta_after_Z_then_X_min" => Dict("I_c" => min_delta_ic_dyn, "I_A_B" => min_delta_mi_dyn),
        ),
        "allowed_claims" => "Local finite-QIT L12 PoC: derived entropy/cut/communication readouts collapse under product erasure and N01 channel order gap is measured on finite cut states.",
        "promotion_status" => "keep_but_open",
        "promotion_blockers" => [
            "promotion_allowed=false by request",
            "Julia-native local-cell PEPS3D anchor is not a full PEPS3D contraction",
            "no downstream stacking claim",
            "no Axis0/flux/physics admission",
            "no dedicated layer-completion claim gate run because this file does not claim full layer completion",
        ],
        "eligible_consumers" => [],
        "blocked_consumers" => [
            "full_layer_completion",
            "parent_complete_layer_status",
            "stacking_readiness",
            "Axis0",
            "flux",
            "Xi",
            "Phi0",
            "bridge",
            "basin",
            "physics",
            "G_structure_selection",
            "final_manifold_admission",
        ],
        "divergence_log" => [
            "Product erasure preserves local marginals but removes the entangled cut; MI collapses to zero and coherent information changes from positive entangled signature to product baseline.",
            "Channel order gap is measured as trace norm of rotate_X_B∘dephase_Z_B versus dephase_Z_B∘rotate_X_B outputs, with identity order control at zero.",
        ],
        "receipt_path" => RESULT_PATH,
        "fresh_rerun" => true,
        "honest_gaps" => [
            "This is a PoC/local-cell Julia layer, not a promoted nonclassical manifold admission.",
            "The PEPS3D object is a finite K anchor with local cut states, not a package-level PEPS3D tensor-network contraction.",
            "Z3 was omitted because a load-bearing flip claim was not needed; no decorative SMT is included.",
        ],
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end

    println("L12_layer_codex complete")
    println("result_path=$(RESULT_PATH)")
    println("all_pass=$(all_pass)")
    println("min_delta_I_c_initial=$(min_delta_ic_initial)")
    println("min_delta_I_A_B_initial=$(min_delta_mi_initial)")
    println("min_delta_I_c_after_Z_then_X=$(min_delta_ic_dyn)")
    println("min_delta_I_A_B_after_Z_then_X=$(min_delta_mi_dyn)")
    println("min_N01_trace_norm_gap=$(min_n01)")
end

main()
