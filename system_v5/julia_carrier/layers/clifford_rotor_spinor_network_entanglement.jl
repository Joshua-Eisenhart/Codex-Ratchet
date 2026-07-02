#!/usr/bin/env julia
# =============================================================================
# clifford_rotor_spinor_network_entanglement
#   classification = clifford_rotor_spinor_network_entanglement_poc
#   promotion_allowed = false
#
# OBJECT UNDER TEST
#   A Clifford / quaternion rotor spinor network that CARRIES entanglement.
#   * Cl(3,0)~SU(2) and Cl(6,0) rotors act as the gauge on the spinor NODES.
#   * The spinor network is an ITensors MPS (Julia, NON-numpy). Each node is a
#     Clifford-rotor-prepared spinor; a nearest-neighbour coupling layer makes the
#     network ENTANGLED. The entanglement is MEASURED as the cut / Schmidt entropy.
#
# GENUINE BAR — two independent, falsifiable readouts (nothing planted):
#
#   (A) GEOMETRY / KNOWN TOPOLOGICAL-ALGEBRAIC INVARIANT  (Clifford module
#       faithfulness = Burnside image rank / irreducible module dimension):
#         Cl(3,0)⊗C ≅ M2(C): the unique irreducible complex module has dim 2,
#           so the 8 Clifford basis words span the FULL matrix algebra M2(C),
#           i.e. Burnside image rank = 2^2 = 4, Schur commutant dim = 1.
#         Cl(6,0)⊗C ≅ M8(C): irreducible complex module has dim 8,
#           Burnside image rank = 8^2 = 64, Schur commutant dim = 1.
#       These ranks are MEASURED from the explicit anticommuting-generator rep
#       (rank of the span of the basis words; nullspace dim of the commutant),
#       never hardcoded to a target, and cross-checked against the INDEPENDENT
#       CliffordAlgebras.jl construction (signature + generator squares).
#
#       WRONG-STRUCTURE CONTROLS that MUST FAIL the invariant (each a genuine
#       verdict flip, not cosmetic):
#         (W1) reducible rho⊕rho : a genuine Cl(n) rep (anticommutation still
#              holds) but NOT irreducible -> Burnside rank << d_full^2 and
#              commutant dim > 1. Faithful-onto-full-algebra test REJECTS it.
#         (W2) commuting / abelian generators (all equal) : breaks the Clifford
#              relation; the module collapses -> Burnside rank < d^2, commutant>1.
#         (W3) linear dependency e_n := e_{n-1} on Cl(6) : kernel appears ->
#              Burnside rank < 64, commutant > 1 (fires on Cl(6); honestly does
#              NOT fire on Cl(3) because M2(C) is already reached by 2 generators
#              -- that asymmetry is REPORTED, not hidden, and is why W1/W2 carry
#              the Cl(3) control).
#
#   (B) ENTANGLEMENT (load-bearing, MEASURED on the spinor network):
#         entangled Clifford-rotor spinor network : cut/Schmidt entropy > 0.5 bit,
#                                                    MPS bond dim > 1.
#         PRODUCT control (identical Clifford rotors, NO coupling layer) :
#                                                    cut/Schmidt entropy ~ 0, bond 1.
#       If the product control did not collapse the entropy, entanglement would
#       not be load-bearing. The rotor is a genuine SU(2) element (unitary,
#       det=+1); the entropy is carried by the network coupling, gauged by the
#       Clifford rotor on each node.
#
# NO BLOCH r-VECTOR anywhere: every quantity is a matrix rank / nullspace dim of a
#   measured complex matrix, or an SVD Schmidt spectrum of an MPS reduced state.
#   No expectation of Pauli operators against a density matrix is taken.
#
# Z3 NOTE: every headline number is a continuous-linear-algebra rank / SVD entropy,
#   not an integer identity over fixed literals. A Z3 block here would be a
#   decorative tautology (this codebase's recurring weakness), so Z3 is OMITTED.
#   The load is carried by the Clifford carrier + Burnside/Schur measurements +
#   ITensors Schmidt readout + the wrong-structure controls whose verdicts flip.
#
# LEARNED (read-only) from the JAX lego
#   system_v5/legos/clifford_quaternion_rotor_spinor_network_peps3d_pytorch_jax_quimb_sympy_z3.py
#   (Clifford rotor on MPS spinor network); the pattern is ADAPTED to Julia +
#   ITensors + CliffordAlgebras and re-anchored on a module-faithfulness invariant
#   with a wrong-structure control, NOT a planted number. The JAX file is NOT modified.
#
# RUN: julia --project="system_v5/julia_carrier" \
#        "system_v5/julia_carrier/layers/clifford_rotor_spinor_network_entanglement.jl"
# =============================================================================

using LinearAlgebra
using ITensors, ITensorMPS
using CliffordAlgebras
import JSON

const ATOL = 1e-9
const CLASSIFICATION = "clifford_rotor_spinor_network_entanglement_poc"

# -----------------------------------------------------------------------------
# PART A — CLIFFORD MODULE FAITHFULNESS INVARIANT (Burnside rank / Schur commutant)
# -----------------------------------------------------------------------------

"Explicit anticommuting Hermitian generators of Cl(n,0) as complex matrices, all
 squaring to +I. n=3 -> 2x2 Pauli; n=6 -> 8x8 Jordan-Wigner tower. Never library
 accessors: the rep is built here so the invariant is a measured READ-OUT."
function clifford_generators(n::Int)
    σ1 = ComplexF64[0 1; 1 0]; σ2 = ComplexF64[0 -im; im 0]; σ3 = ComplexF64[1 0; 0 -1]
    I2 = ComplexF64[1 0; 0 1]
    if n == 3
        return [σ1, σ2, σ3]
    elseif n == 6
        k3(a, b, c) = kron(kron(a, b), c)
        return [k3(σ1, I2, I2), k3(σ2, I2, I2),
                k3(σ3, σ1, I2), k3(σ3, σ2, I2),
                k3(σ3, σ3, σ1), k3(σ3, σ3, σ2)]
    else
        error("only Cl(3,0) and Cl(6,0) built here")
    end
end

"All 2^n Clifford basis words 1, e_i, e_i e_j, ... (subset-mask order)."
function clifford_words(gs::Vector{<:AbstractMatrix})
    d = size(gs[1], 1); n = length(gs)
    Id = Matrix{ComplexF64}(I, d, d)
    words = Matrix{ComplexF64}[Id]
    for mask in 1:(2^n - 1)
        w = copy(Id)
        for i in 1:n
            (mask >> (i - 1)) & 1 == 1 && (w = w * ComplexF64.(gs[i]))
        end
        push!(words, w)
    end
    words
end

"BURNSIDE image rank = dim_C span{words}. Faithful irreducible d-module -> d^2."
function burnside_rank(gs::Vector{<:AbstractMatrix})
    V = hcat([vec(w) for w in clifford_words(gs)]...)
    rank(V; atol = ATOL)
end

"SCHUR commutant dim = nullspace dim of [g^T⊗I - I⊗g] stacked. Irreducible <-> 1."
function commutant_dim(gs::Vector{<:AbstractMatrix})
    d = size(gs[1], 1); Id = Matrix{ComplexF64}(I, d, d)
    A = vcat([kron(transpose(ComplexF64.(g)), Id) - kron(Id, ComplexF64.(g)) for g in gs]...)
    size(nullspace(A; atol = ATOL), 2)
end

"Max residual of {e_i,e_j}=2 delta_ij over the generator set (0 = genuine Cl rep)."
function anticommutation_residual(gs::Vector{<:AbstractMatrix})
    n = length(gs); d = size(gs[1], 1); Id = Matrix{ComplexF64}(I, d, d)
    mx = 0.0
    for i in 1:n, j in 1:n
        anti = ComplexF64.(gs[i]) * ComplexF64.(gs[j]) + ComplexF64.(gs[j]) * ComplexF64.(gs[i])
        expected = (i == j ? 2 * Id : zeros(ComplexF64, d, d))
        mx = max(mx, maximum(abs.(anti .- expected)))
    end
    mx
end

"Independent anchor: CliffordAlgebras.jl signature + generator squares for Cl(n,0).
 We trust ONLY generator-level relations (correct in this build); higher-grade
 accessors are known-defective and are NOT relied on."
function package_anchor(n::Int)
    cl = CliffordAlgebra(n, 0)
    sig = collect(CliffordAlgebras.signature(cl))                       # (n,0,0)
    sqs = [Float64(CliffordAlgebras.scalar(getproperty(cl, s) * getproperty(cl, s)))
           for s in CliffordAlgebras.basesymbols(cl)]                   # all +1
    sig, sqs
end

"Measured module-faithfulness record for Cl(n,0) vs the KNOWN invariant d^2."
function module_invariant(n::Int)
    gs = clifford_generators(n)
    d = size(gs[1], 1)                          # irreducible module dim (READ from rep)
    br = burnside_rank(gs)                       # measured Burnside image rank
    cd = commutant_dim(gs)                       # measured Schur commutant dim
    ar = anticommutation_residual(gs)            # genuine Cl rep check
    sig, sqs = package_anchor(n)
    known_full_dim = d^2                         # KNOWN: dim of full matrix algebra M_d(C)
    faithful_full  = (br == known_full_dim)      # image = whole M_d(C) => faithful & onto
    irreducible    = (cd == 1)
    sig_anchor_ok  = (sig == [n, 0, 0]) && all(isapprox.(sqs, 1.0; atol = 1e-10))
    Dict{String,Any}(
        "n" => n,
        "module_dim_d_measured" => d,
        "burnside_image_rank_measured" => br,
        "known_full_matrix_algebra_dim_d2" => known_full_dim,
        "schur_commutant_dim_measured" => cd,
        "anticommutation_residual" => ar,
        "genuine_clifford_rep" => (ar < 1e-12),
        "package_signature" => sig,
        "package_generator_squares" => sqs,
        "package_anchor_matches" => sig_anchor_ok,
        "faithful_onto_full_algebra" => faithful_full,
        "irreducible_commutant_is_1" => irreducible,
        "invariant_confirmed" => faithful_full && irreducible && (ar < 1e-12) && sig_anchor_ok,
    )
end

"WRONG-STRUCTURE controls. Each must FAIL the invariant (verdict flip)."
function wrong_structure_controls()
    out = Dict{String,Any}()

    # W1 — reducible rho⊕rho (genuine Cl(3) rep, but NOT irreducible).
    g3 = clifford_generators(3)
    red(g) = ComplexF64[g zeros(ComplexF64, 2, 2); zeros(ComplexF64, 2, 2) g]
    red3 = [red(g) for g in g3]                     # 4x4, block-diagonal
    br1 = burnside_rank(red3); cd1 = commutant_dim(red3); ar1 = anticommutation_residual(red3)
    full1 = (2 * 2)^2                                # M4(C) would be 16; image is only 4
    W1_fails = (br1 != full1) && (cd1 > 1)
    out["W1_reducible_rho_plus_rho_C4"] = Dict(
        "still_genuine_clifford_rep" => (ar1 < 1e-12),
        "burnside_rank_measured" => br1, "full_M4_would_be" => full1,
        "commutant_dim_measured" => cd1,
        "invariant_fails_as_required" => W1_fails)

    # W2 — commuting / abelian generators (all sigma3): breaks the Clifford relation.
    σ3 = ComplexF64[1 0; 0 -1]
    comm3 = [σ3, σ3, σ3]
    br2 = burnside_rank(comm3); cd2 = commutant_dim(comm3); ar2 = anticommutation_residual(comm3)
    W2_fails = (br2 < 4) && (cd2 > 1) && (ar2 > 1e-9)
    out["W2_commuting_abelian_generators"] = Dict(
        "anticommutation_residual" => ar2, "breaks_clifford_relation" => (ar2 > 1e-9),
        "burnside_rank_measured" => br2, "irreducible_target_d2" => 4,
        "commutant_dim_measured" => cd2,
        "invariant_fails_as_required" => W2_fails)

    # W3 — linear dependency e6 := e5 on Cl(6): kernel appears -> rank < 64.
    g6 = clifford_generators(6)
    dep6 = [g6[1], g6[2], g6[3], g6[4], g6[5], g6[5]]   # e6 := e5
    br3 = burnside_rank(dep6); cd3 = commutant_dim(dep6)
    W3_fails = (br3 < 64) && (cd3 > 1)
    out["W3_linear_dependency_e6_eq_e5_Cl6"] = Dict(
        "burnside_rank_measured" => br3, "faithful_target_d2" => 64,
        "commutant_dim_measured" => cd3,
        "invariant_fails_as_required" => W3_fails)

    # HONEST asymmetry disclosure: e3:=e2 on Cl(3) does NOT fire (M2(C) already
    # reached by 2 generators). Reported, not hidden; W1/W2 carry the Cl(3) control.
    dep3 = [g3[1], g3[2], g3[2]]
    br3b = burnside_rank(dep3); cd3b = commutant_dim(dep3)
    out["disclosure_e3_eq_e2_Cl3_does_NOT_fire"] = Dict(
        "burnside_rank_measured" => br3b, "commutant_dim_measured" => cd3b,
        "note" => "M2(C) is already reached by sigma1,sigma2 (sigma1*sigma2=i*sigma3); " *
                  "dropping a dependent 3rd generator does not shrink the span, so this " *
                  "is NOT a valid faithfulness-kill for Cl(3). Cl(3) control is carried by W1+W2.",
        "honestly_does_not_fire" => (br3b == 4 && cd3b == 1))

    all_controls_fire = out["W1_reducible_rho_plus_rho_C4"]["invariant_fails_as_required"] &&
                        out["W2_commuting_abelian_generators"]["invariant_fails_as_required"] &&
                        out["W3_linear_dependency_e6_eq_e5_Cl6"]["invariant_fails_as_required"]
    out, all_controls_fire
end

# -----------------------------------------------------------------------------
# PART B — CLIFFORD-ROTOR SPINOR NETWORK + MEASURED ENTANGLEMENT (ITensors)
# -----------------------------------------------------------------------------

const _cl3 = CliffordAlgebra(:Cl3)

"SU(2) 2x2 spinor matrix of a Cl(3) even-subalgebra rotor R = exp(-theta/2 e_i e_j).
 The Clifford/quaternion gauge that dresses each spinor node. (e2e3 -> sigma_x so the
 rotor genuinely rotates the node spinor OFF the |0> axis -> superposition.)"
function clifford_rotor_su2(theta::Float64, i::Int, j::Int)
    B = getproperty(_cl3, Symbol("e$i")) * getproperty(_cl3, Symbol("e$j"))
    R = exp(-0.5 * theta * B)
    a = real(CliffordAlgebras.scalar(R))                         # cos(theta/2)
    c12 = real(R.e1e2); c23 = real(R.e2e3); c31 = real(R.e3e1)
    σx = ComplexF64[0 1; 1 0]; σy = ComplexF64[0 -im; im 0]; σz = ComplexF64[1 0; 0 -1]
    a * ComplexF64[1 0; 0 1] - im * (c12 * σz + c23 * σx + c31 * σy)
end

"Entangled Clifford-rotor spinor network: per-node rotor prep (the gauge), then a
 nearest-neighbour coupling layer that builds the network entanglement."
function build_entangled_spinor_network(s, N::Int)
    psi = MPS(s, "0")
    for q in 1:N
        R = clifford_rotor_su2(0.5 + 0.13 * q, 2, 3)             # e2e3 rotor (off-axis)
        G = ITensor(R, prime(s[q]), s[q])
        psi = apply(G, psi)
    end
    for i in 1:N-1
        psi = apply(op("CNOT", s, i, i + 1), psi; cutoff = 1e-14, maxdim = 64)
    end
    psi
end

"PRODUCT control: identical Clifford rotor prep, but NO coupling layer -> a pure
 tensor product of rotor-dressed spinors. Entanglement MUST collapse to ~0."
function build_product_spinor_network(s, N::Int)
    psi = MPS(s, "0")
    for q in 1:N
        R = clifford_rotor_su2(0.5 + 0.13 * q, 2, 3)
        G = ITensor(R, prime(s[q]), s[q])
        psi = apply(G, psi)
    end
    psi
end

"Cut / Schmidt von-Neumann entropy (bits) across the bond at site b, from the MPS
 SVD spectrum. Pure SVD Schmidt readout -- NO Bloch vector, NO Pauli expectation."
function cut_schmidt_entropy(psi, b::Int)
    orthogonalize!(psi, b)
    U, S, V = svd(psi[b], (linkind(psi, b - 1), siteind(psi, b)))
    sv = 0.0
    for n in 1:dim(S, 1)
        p = S[n, n]^2
        p > 1e-12 && (sv -= p * log2(p))
    end
    sv
end

"Verify each rotor is a genuine SU(2) element (unitary, det=+1)."
function rotor_is_su2()
    mx_u = 0.0; mx_d = 0.0
    for t in (0.3, 0.7, 1.1, 1.9)
        R = clifford_rotor_su2(t, 2, 3)
        mx_u = max(mx_u, maximum(abs.(R * R' - ComplexF64[1 0; 0 1])))
        mx_d = max(mx_d, abs(det(R) - 1.0))
    end
    mx_u < 1e-12 && mx_d < 1e-12, mx_u, mx_d
end

function entanglement_rows()
    rows = Dict{String,Any}[]
    for N in (6, 8, 12, 16)
        s = siteinds("Qubit", N)
        ent  = build_entangled_spinor_network(s, N)
        prod = build_product_spinor_network(s, N)
        e_ent  = cut_schmidt_entropy(ent, N ÷ 2)
        e_prod = cut_schmidt_entropy(prod, N ÷ 2)
        bond_ent  = maxlinkdim(ent)
        bond_prod = maxlinkdim(prod)
        ent_load_bearing = (e_ent > 0.5) && (e_prod < 1e-6) && (bond_ent > 1) && (bond_prod == 1)
        push!(rows, Dict{String,Any}(
            "N_nodes" => N,
            "entangled_cut_schmidt_entropy_bits" => round(e_ent, digits = 6),
            "entangled_mps_bond" => bond_ent,
            "product_control_cut_schmidt_entropy_bits" => round(e_prod, digits = 10),
            "product_control_mps_bond" => bond_prod,
            "entanglement_load_bearing" => ent_load_bearing))
    end
    rows
end

# -----------------------------------------------------------------------------
# RUN
# -----------------------------------------------------------------------------
function main()
    println("="^78)
    println("clifford_rotor_spinor_network_entanglement  (Julia / ITensors / CliffordAlgebras)")
    println("="^78)

    # PART A — invariant
    inv3 = module_invariant(3)
    inv6 = module_invariant(6)
    controls, controls_fire = wrong_structure_controls()

    println("\n[A] Clifford module faithfulness invariant (Burnside rank / Schur commutant):")
    for r in (inv3, inv6)
        println("    Cl($(r["n"]),0): module dim d=$(r["module_dim_d_measured"])  " *
                "Burnside rank=$(r["burnside_image_rank_measured"]) / known d^2=$(r["known_full_matrix_algebra_dim_d2"])  " *
                "commutant=$(r["schur_commutant_dim_measured"])  anti_resid=$(r["anticommutation_residual"])")
        println("        package anchor sig=$(r["package_signature"]) squares=$(r["package_generator_squares"]) " *
                "match=$(r["package_anchor_matches"])  ->  invariant_confirmed=$(r["invariant_confirmed"])")
    end
    println("\n    WRONG-STRUCTURE controls (must FAIL the invariant):")
    println("      W1 reducible rho+rho C^4 : Burnside=$(controls["W1_reducible_rho_plus_rho_C4"]["burnside_rank_measured"]) " *
            "(M4=16) commutant=$(controls["W1_reducible_rho_plus_rho_C4"]["commutant_dim_measured"]) " *
            "fails=$(controls["W1_reducible_rho_plus_rho_C4"]["invariant_fails_as_required"])")
    println("      W2 commuting/abelian     : Burnside=$(controls["W2_commuting_abelian_generators"]["burnside_rank_measured"]) " *
            "(d^2=4) commutant=$(controls["W2_commuting_abelian_generators"]["commutant_dim_measured"]) " *
            "breaks_clifford=$(controls["W2_commuting_abelian_generators"]["breaks_clifford_relation"]) " *
            "fails=$(controls["W2_commuting_abelian_generators"]["invariant_fails_as_required"])")
    println("      W3 e6:=e5 dependency Cl6 : Burnside=$(controls["W3_linear_dependency_e6_eq_e5_Cl6"]["burnside_rank_measured"]) " *
            "(d^2=64) commutant=$(controls["W3_linear_dependency_e6_eq_e5_Cl6"]["commutant_dim_measured"]) " *
            "fails=$(controls["W3_linear_dependency_e6_eq_e5_Cl6"]["invariant_fails_as_required"])")
    println("      (disclosure) e3:=e2 Cl3 does NOT fire (M2(C) already reached): " *
            "$(controls["disclosure_e3_eq_e2_Cl3_does_NOT_fire"]["honestly_does_not_fire"])")

    # PART B — entanglement
    su2_ok, su2_u, su2_d = rotor_is_su2()
    rows = entanglement_rows()
    println("\n[B] Clifford-rotor spinor network entanglement (ITensors Schmidt readout):")
    println("    rotor is genuine SU(2): unitary_resid=$(su2_u) det_resid=$(su2_d) -> $su2_ok")
    for r in rows
        println("    N=$(r["N_nodes"]): entangled cut S=$(r["entangled_cut_schmidt_entropy_bits"]) bond=$(r["entangled_mps_bond"]) " *
                "| product control S=$(r["product_control_cut_schmidt_entropy_bits"]) bond=$(r["product_control_mps_bond"]) " *
                "load_bearing=$(r["entanglement_load_bearing"])")
    end

    # VERDICT
    invariant_anchored = inv3["invariant_confirmed"] && inv6["invariant_confirmed"]
    entanglement_load_bearing = su2_ok && all(r["entanglement_load_bearing"] for r in rows)
    bloch_free = true   # no Bloch r-vector / Pauli-expectation anywhere; SVD Schmidt + rank/nullspace only
    all_pass = invariant_anchored && controls_fire && entanglement_load_bearing && bloch_free

    results = Dict{String,Any}(
        "object_id" => "clifford_rotor_spinor_network_entanglement",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => false,
        "carrier" => "ITensors MPS spinor network + CliffordAlgebras.jl rotor gauge + explicit Clifford rep (Julia, non-numpy)",
        "z3_used" => false,
        "z3_omission_reason" =>
            "Every headline number is a continuous linear-algebra rank/nullspace or an SVD " *
            "Schmidt entropy, not an integer identity over fixed literals. A Z3 block would be " *
            "a decorative tautology; load is carried by the Clifford carrier + Burnside/Schur " *
            "measurements + ITensors Schmidt readout + wrong-structure controls whose verdicts flip.",
        "bloch_free" => bloch_free,
        "bloch_free_note" =>
            "No Bloch r-vector and no Pauli expectation tr(rho*sigma) anywhere. Geometry side = " *
            "matrix rank / nullspace dim of measured complex matrices; entanglement side = SVD " *
            "Schmidt von-Neumann entropy of the MPS reduced state.",
        "geometry_invariant" => Dict(
            "anchor" => "Clifford module faithfulness: Burnside image rank = irreducible module dim^2 " *
                        "(Cl(3,0)⊗C≅M2(C) -> rank 4; Cl(6,0)⊗C≅M8(C) -> rank 64); Schur commutant dim = 1",
            "Cl3" => inv3,
            "Cl6" => inv6,
            "invariant_anchored" => invariant_anchored,
        ),
        "wrong_structure_controls" => controls,
        "wrong_structure_controls_all_fire" => controls_fire,
        "entanglement" => Dict(
            "rotor_is_su2" => su2_ok,
            "rotor_unitary_residual" => su2_u,
            "rotor_det_residual" => su2_d,
            "rows" => rows,
            "load_bearing" => entanglement_load_bearing,
        ),
        "verdict" => Dict(
            "invariant_anchored" => invariant_anchored,
            "wrong_structure_controls_fire" => controls_fire,
            "entanglement_load_bearing" => entanglement_load_bearing,
            "bloch_free" => bloch_free,
            "all_pass" => all_pass,
        ),
        "all_pass" => all_pass,
        "honest_status_ladder" => all_pass ? "passes local rerun (this run)" : "runs",
        "learned_from_jax_lego_readonly" =>
            "system_v5/legos/clifford_quaternion_rotor_spinor_network_peps3d_pytorch_jax_quimb_sympy_z3.py " *
            "(pattern adapted to Julia/ITensors; re-anchored on module-faithfulness invariant + wrong-structure " *
            "control; JAX file not modified).",
        "blocked_consumers" => ["layer_stacking", "g_structure_selection", "flux", "Xi/Phi0", "Axis0", "FEP", "physics"],
    )

    println("\n" * "="^78)
    println("VERDICT:")
    println("    invariant_anchored (Cl3+Cl6 Burnside=d^2, commutant=1) : $invariant_anchored")
    println("    wrong_structure_controls_fire (W1,W2,W3)               : $controls_fire")
    println("    entanglement_load_bearing (entangled>0.5, product~0)   : $entanglement_load_bearing")
    println("    bloch_free                                             : $bloch_free")
    println("    ALL_PASS                                               : $all_pass")
    println("="^78)

    outpath = joinpath(@__DIR__, "clifford_rotor_spinor_network_entanglement_results.json")
    open(outpath, "w") do io
        JSON.print(io, results, 2)
    end
    println("results -> ", outpath)
    return all_pass
end

main()
