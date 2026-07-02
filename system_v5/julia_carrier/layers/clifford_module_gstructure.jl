# =============================================================================
# clifford_module_gstructure — CLIFFORD-MODULE G-structure candidate (PoC)
# -----------------------------------------------------------------------------
# Object under test: the Dirac spinor space S as an IRREDUCIBLE module over the
# spacetime Clifford algebra Cl(1,3). The G-structure claim is that the 4-dim
# complex Dirac representation is the *minimal faithful irreducible* Cl(1,3)-
# module, and that gamma5 (built from the EVEN subalgebra) splits it into the
# two 2-dim Weyl submodules.
#
# ANCHORED INVARIANT (computed, not asserted):
#   dim of the irreducible complex Cl(1,3) module = 4.
#   Reason: Cl(1,3) ≅ M2(H) as a real algebra (real irreducible module H^2 ~ R^8);
#   its complexification Cl(1,3) ⊗ C ≅ M4(C), whose unique irreducible complex
#   module is C^4 — the Dirac spinor. The sim MEASURES dim = 4 via two
#   independent representation-theoretic tests (Burnside image rank, Schur
#   commutant dim), never by hardcoding "4".
#
# HONEST CONTRACT — this codebase fabricates by-construction theater, so every
# structural claim here is a READ-OUT of a measured rank / nullspace, with a
# kill-control that would falsify it if it passed:
#
#   (1) FAITHFUL.  The algebra map Cl(1,3) -> M4(C), w |-> rho(w), is injective.
#       MEASURED: the 16 Clifford basis words {1, g_mu, g_mu g_nu, ..., g_5}
#       map to 16 LINEARLY INDEPENDENT 4x4 matrices (span rank = 16 = dim Cl(1,3)).
#       A non-faithful action has a kernel -> span rank < 16.
#
#   (2) IRREDUCIBLE (dim 4).  Two independent witnesses, both COMPUTED:
#       (2a) BURNSIDE: the image rho(Cl(1,3)) is ALL of M4(C) iff the span of the
#            16 words has rank 16 = dim_C M4(C). Surjectivity onto the full matrix
#            algebra is equivalent to irreducibility of a 4-dim faithful module.
#       (2b) SCHUR commutant: dim{ X : X gamma_mu = gamma_mu X for all mu } = 1
#            (only scalars). dim > 1 <=> the module is reducible.
#       Both must agree: rank 16 AND commutant dim 1 => irreducible, dim 4.
#
#   (3) WEYL SPLIT under the EVEN subalgebra.  gamma5 = i g0 g1 g2 g3 commutes
#       with every EVEN-grade element (bilinears g_mu g_nu) and anticommutes with
#       every ODD-grade generator g_mu (MEASURED commutator/anticommutator norms).
#       Therefore its +-1 eigenspaces (each rank 2) are INVARIANT submodules under
#       Cl^0(1,3) but are SWAPPED by odd elements. We MEASURE: even-subalgebra
#       cross-block leak = 0 (invariant), odd-element cross-block leak > 0 (swap),
#       and that each 2-dim eigenspace is itself IRREDUCIBLE under Cl^0 (Burnside
#       rank = 4 = M2(C) on each block).
#
# KILL-CONTROLS (each must GENUINELY fire on a wrong-structure action):
#   (K1) REDUCIBLE action  rho ⊕ rho  on C^8: a direct sum of two copies of the
#        Dirac rep. Its image is block-diagonal (rank 16, NOT 64 = M8(C)) and its
#        commutant is 4-dimensional (multiplicity-2 endomorphisms), so BOTH the
#        Burnside and Schur tests REJECT irreducibility. If they did not, the
#        irreducibility test would be vacuous.
#   (K2) NON-FAITHFUL action: replace g3 := g2 (a linear dependency among the
#        generators). The Clifford map collapses: span rank < 16 (kernel exists)
#        and commutant dim > 1. The faithfulness test REJECTS it.
#   Each kill is a *different* action of the SAME generator count, so the
#   discrimination is carried by the MEASURED rank/commutant, not a dimension
#   coincidence.
#
# NON-CIRCULAR ANCHOR (checked against the package, not against itself):
#   CliffordAlgebras.CliffordAlgebra(1,3) is an INDEPENDENT construction. We read
#   out its KNOWN invariants — signature (1,3,0); generator squares
#   (e1^2=+1, e2,3,4^2=-1); pseudoscalar I^2 = -1 — and check our explicit 4x4
#   gammas reproduce the SAME Clifford relation {g_mu,g_nu} = 2 eta_mu_nu and that
#   the package's I^2 = -1 PREDICTS our gamma5^2 = (i)^2 (-1) = +1.
#
# Z3 NOTE: every claim here is a rank / nullspace dimension of a measured complex
#   matrix, decided by floating-point linear algebra over a continuous span — not
#   an integer identity over fixed literals. A Z3 block would be a decorative
#   tautology (this codebase's recurring weakness), so Z3 is OMITTED. The load is
#   carried by the Clifford carrier + the rank/commutant measurements + the
#   kill-controls whose verdicts genuinely flip.
#
# classification: PoC ; promotion_allowed = false
# =============================================================================

using LinearAlgebra
using CliffordAlgebras
using Random
import JSON

const ATOL = 1e-9

# -----------------------------------------------------------------------------
# Representation-theory measurement helpers — every number is a READ-OUT.
# -----------------------------------------------------------------------------

# Clifford basis words of a set of n generators: 1, g_mu, g_mu g_nu (mu<nu),
# triples, and the top product. For n=4 this is 1+4+6+4+1 = 16 words.
function clifford_words(gs::Vector{<:AbstractMatrix})
    d = size(gs[1], 1)
    n = length(gs)
    Id = Matrix{ComplexF64}(I, d, d)
    words = Matrix{ComplexF64}[Id]
    for mu in 1:n
        push!(words, ComplexF64.(gs[mu]))
    end
    for mu in 1:n, nu in mu+1:n
        push!(words, ComplexF64.(gs[mu]) * ComplexF64.(gs[nu]))
    end
    for mu in 1:n, nu in mu+1:n, rho in nu+1:n
        push!(words, ComplexF64.(gs[mu]) * ComplexF64.(gs[nu]) * ComplexF64.(gs[rho]))
    end
    if n >= 4
        top = ComplexF64.(gs[1])
        for k in 2:n
            top = top * ComplexF64.(gs[k])
        end
        push!(words, top)
    end
    return words
end

# BURNSIDE rank: dim_C span{ words }. For a faithful irreducible d-dim module this
# equals d^2 (= dim M_d(C)); for the reducible/degenerate kills it is strictly less.
function burnside_rank(gs::Vector{<:AbstractMatrix})
    words = clifford_words(gs)
    V = hcat([vec(w) for w in words]...)
    return rank(V; atol = ATOL)
end

# SCHUR commutant dimension: dim{ X : X g_mu = g_mu X for all mu }.
# Solve (g_mu^T ⊗ I - I ⊗ g_mu) vec(X) = 0, stacked over mu; nullspace dim.
function commutant_dim(gs::Vector{<:AbstractMatrix})
    d = size(gs[1], 1)
    Id = Matrix{ComplexF64}(I, d, d)
    rows = Matrix{ComplexF64}[]
    for g in gs
        gC = ComplexF64.(g)
        push!(rows, kron(transpose(gC), Id) - kron(Id, gC))
    end
    A = vcat(rows...)
    return size(nullspace(A; atol = ATOL), 2)
end

# Burnside rank for a 2x2 even-subalgebra block (used to test the Weyl irreps).
function burnside_rank_2x2(mats::Vector{<:AbstractMatrix})
    Id = Matrix{ComplexF64}(I, 2, 2)
    span = Matrix{ComplexF64}[Id]
    for m in mats
        push!(span, ComplexF64.(m))
    end
    for a in mats, b in mats
        push!(span, ComplexF64.(a) * ComplexF64.(b))
    end
    V = hcat([vec(m) for m in span]...)
    return rank(V; atol = ATOL)
end

# -----------------------------------------------------------------------------
# 1. BUILD the explicit 4x4 irreducible Dirac (Weyl/chiral basis) rep of Cl(1,3).
#    Mostly-minus signature (+,-,-,-): g0^2=+I, g_k^2=-I.
# -----------------------------------------------------------------------------
σ0 = ComplexF64[1 0; 0 1]
σ1 = ComplexF64[0 1; 1 0]
σ2 = ComplexF64[0 -im; im 0]
σ3 = ComplexF64[1 0; 0 -1]
Z2 = zeros(ComplexF64, 2, 2)

g0 = [Z2 σ0; σ0 Z2]
g1 = [Z2 σ1; -σ1 Z2]
g2 = [Z2 σ2; -σ2 Z2]
g3 = [Z2 σ3; -σ3 Z2]
gammas = [g0, g1, g2, g3]
I4 = Matrix{ComplexF64}(I, 4, 4)
eta = [1.0, -1.0, -1.0, -1.0]               # diag of Minkowski metric, Cl(1,3)

# gamma5 from the EVEN subalgebra (it is the normalized top even product i*g0g1g2g3)
gamma5 = im * g0 * g1 * g2 * g3

# MEASURE the defining Clifford relation {g_mu, g_nu} = 2 eta_mu_nu (not planted).
clifford_ok = true
max_clifford_residual = 0.0
for mu in 1:4, nu in 1:4
    anti = gammas[mu] * gammas[nu] + gammas[nu] * gammas[mu]
    expected = (mu == nu ? 2 * eta[mu] * I4 : zeros(ComplexF64, 4, 4))
    resid = maximum(abs.(anti .- expected))
    global max_clifford_residual = max(max_clifford_residual, resid)
    global clifford_ok &= (resid < 1e-12)
end

println("="^74)
println("clifford_module_gstructure — Dirac spinor as irreducible Cl(1,3)-module")
println("="^74)
println("[1] Built explicit 4x4 Cl(1,3) rep (Weyl basis).")
println("    Clifford {g_mu,g_nu}=2 eta measured ok : ", clifford_ok,
        "  (max resid ", max_clifford_residual, ")")

# -----------------------------------------------------------------------------
# 2. NON-CIRCULAR ANCHOR: independent CliffordAlgebras.CliffordAlgebra(1,3).
# -----------------------------------------------------------------------------
cl = CliffordAlgebra(1, 3)
sig = collect(CliffordAlgebras.signature(cl))                  # (1,3,0)
gen_squares = [Float64(CliffordAlgebras.scalar(getproperty(cl, s) * getproperty(cl, s)))
               for s in CliffordAlgebras.basesymbols(cl)]      # [+1,-1,-1,-1]
Ipseudo = cl.e1 * cl.e2 * cl.e3 * cl.e4
Isq_scalar = Float64(CliffordAlgebras.scalar(Ipseudo * Ipseudo))  # -1 for Cl(1,3)
pkg_pseudoscalar_sq_is_minus1 = isapprox(Isq_scalar, -1.0; atol = 1e-10)

# package I^2 = -1 PREDICTS our gamma5^2 = i^2 * I^2 = (-1)(-1) = +1
predicted_g5sq = (im^2) * Isq_scalar                            # = +1
our_g5sq_resid = maximum(abs.(gamma5 * gamma5 .- I4))
our_g5sq_is_I = our_g5sq_resid < 1e-12
crosscheck_ok = isapprox(predicted_g5sq, ComplexF64(1, 0); atol = 1e-10) && our_g5sq_is_I

# the package's signature/squares must match the explicit rep's signature/squares.
# g_mu^2 = eta_mu * I, so the (1,1) entry reads off the square scalar (+1,-1,-1,-1).
our_squares = Float64[ real((gammas[mu]*gammas[mu])[1,1]) for mu in 1:4 ]
signature_matches_pkg = isapprox(our_squares, gen_squares; atol = 1e-10)

println("[2] Non-circular anchor (CliffordAlgebras Cl(1,3)):")
println("    package signature (p,q,r)       = ", sig)
println("    package gen squares e_i^2       = ", gen_squares)
println("    our    gen squares g_mu^2       = ", our_squares,
        "   (match: ", signature_matches_pkg, ")")
println("    package pseudoscalar I^2 = -1   : ", pkg_pseudoscalar_sq_is_minus1,
        "  (scalar ", Isq_scalar, ")")
println("    package predicts gamma5^2 = ", real(predicted_g5sq),
        "  ; our gamma5^2 = I measured: ", our_g5sq_is_I, "  -> crosscheck ", crosscheck_ok)

# -----------------------------------------------------------------------------
# 3. FAITHFUL + IRREDUCIBLE (dim 4) — the anchored invariant, MEASURED.
# -----------------------------------------------------------------------------
module_dim = size(gammas[1], 1)                 # = 4 (READ from the matrices)
dirac_rank = burnside_rank(gammas)              # want 16 = dim M4(C) = dim Cl(1,3)
dirac_comm = commutant_dim(gammas)              # want 1 (Schur: irreducible)

faithful = (dirac_rank == 16)                   # image dim = dim Cl(1,3) => injective
irreducible = (dirac_rank == 16) && (dirac_comm == 1)
dim_is_4 = (module_dim == 4)
# the anchored invariant: irreducible complex Cl(1,3)-module has dim 4.
# We confirm sqrt(burnside_rank) = module_dim (full matrix algebra M_d) and d = 4.
matrix_algebra_full = (dirac_rank == module_dim^2)
invariant_dim4_confirmed = irreducible && faithful && dim_is_4 && matrix_algebra_full

println("[3] Faithfulness + irreducibility (the dim-4 invariant), MEASURED:")
println("    module dim (read from rep)      = ", module_dim)
println("    Burnside image rank             = ", dirac_rank, " / 16   (faithful & full M4: ", matrix_algebra_full, ")")
println("    Schur commutant dim             = ", dirac_comm, "      (irreducible iff 1)")
println("    => FAITHFUL: ", faithful, " ; IRREDUCIBLE: ", irreducible,
        " ; dim-4 invariant confirmed: ", invariant_dim4_confirmed)

# -----------------------------------------------------------------------------
# 4. WEYL SPLIT under the EVEN subalgebra Cl^0(1,3).
# -----------------------------------------------------------------------------
g5_diag = real.(diag(gamma5))
weyl_chiral_form = isapprox(gamma5, Diagonal(g5_diag); atol = 1e-12) &&
                   sort(round.(Int, g5_diag)) == [-1, -1, 1, 1]
PL = (I4 - gamma5) / 2          # projector onto left  Weyl submodule (gamma5 = -1)
PR = (I4 + gamma5) / 2          # projector onto right Weyl submodule (gamma5 = +1)
rankPL = rank(PL; atol = ATOL)
rankPR = rank(PR; atol = ATOL)
weyl_each_dim2 = (rankPL == 2) && (rankPR == 2)

# even-subalgebra generators = bilinears g_mu g_nu ; they must COMMUTE with gamma5
bivs = Matrix{ComplexF64}[]
for mu in 1:4, nu in mu+1:4
    push!(bivs, gammas[mu] * gammas[nu])
end
max_even_comm = maximum(maximum(abs.(b * gamma5 - gamma5 * b)) for b in bivs)
even_commutes = max_even_comm < 1e-12
# odd generators must ANTICOMMUTE with gamma5 (swap L<->R)
max_odd_anti = maximum(maximum(abs.(gammas[mu] * gamma5 + gamma5 * gammas[mu])) for mu in 1:4)
odd_anticommutes = max_odd_anti < 1e-12

# invariance: even subalgebra does NOT leak across the split; odd elements DO.
max_even_leak = maximum(max(maximum(abs.(PR * b * PL)), maximum(abs.(PL * b * PR))) for b in bivs)
even_invariant = max_even_leak < 1e-12
odd_leak = maximum(maximum(abs.(PR * gammas[mu] * PL)) for mu in 1:4)
odd_connects = odd_leak > 1e-9

# each 2-dim Weyl block is itself IRREDUCIBLE under Cl^0 (Burnside rank 4 = M2(C))
Lblocks = [b[1:2, 1:2] for b in bivs]
Rblocks = [b[3:4, 3:4] for b in bivs]
left_weyl_rank = burnside_rank_2x2(Lblocks)
right_weyl_rank = burnside_rank_2x2(Rblocks)
weyl_blocks_irreducible = (left_weyl_rank == 4) && (right_weyl_rank == 4)

weyl_split_ok = weyl_chiral_form && weyl_each_dim2 && even_commutes && odd_anticommutes &&
                even_invariant && odd_connects && weyl_blocks_irreducible

println("[4] Weyl split under even subalgebra Cl^0(1,3):")
println("    gamma5 = diag", g5_diag, "  chiral form: ", weyl_chiral_form)
println("    dim left/right Weyl submodule   = ", rankPL, " / ", rankPR, "  (each 2: ", weyl_each_dim2, ")")
println("    even subalg commutes w/ gamma5  : ", even_commutes, "  (max |[.,g5]| = ", max_even_comm, ")")
println("    odd gen anticommutes w/ gamma5  : ", odd_anticommutes, "  (max |{.,g5}| = ", max_odd_anti, ")")
println("    even-subalg cross-block leak    = ", max_even_leak, "  (invariant submodules: ", even_invariant, ")")
println("    odd-element cross-block leak    = ", odd_leak, "  (swaps L<->R: ", odd_connects, ")")
println("    Weyl blocks irreducible (M2):   L=", left_weyl_rank, "/4  R=", right_weyl_rank,
        "/4  (", weyl_blocks_irreducible, ")")

# -----------------------------------------------------------------------------
# 5. KILL-CONTROL K1: REDUCIBLE action rho ⊕ rho on C^8 must FAIL irreducibility.
# -----------------------------------------------------------------------------
red8 = [ [gammas[mu] zeros(ComplexF64, 4, 4); zeros(ComplexF64, 4, 4) gammas[mu]] for mu in 1:4 ]
# this still satisfies the Clifford relations (it is a genuine Cl(1,3) rep) but is reducible
red8_clifford_ok = all(maximum(abs.(red8[mu]*red8[nu] + red8[nu]*red8[mu] -
                        (mu == nu ? 2*eta[mu]*Matrix{ComplexF64}(I,8,8) : zeros(ComplexF64,8,8)))) < 1e-12
                        for mu in 1:4, nu in 1:4)
red8_rank = burnside_rank(red8)          # 16, NOT 64 = M8(C)
red8_comm = commutant_dim(red8)          # 4, NOT 1
red8_is_irreducible = (red8_rank == 64) && (red8_comm == 1)
K1_fires = red8_clifford_ok && !red8_is_irreducible    # genuine rep, but irreducibility test REJECTS it

println("[5] KILL-CONTROL K1 (reducible rho⊕rho on C^8):")
println("    still a valid Clifford rep      : ", red8_clifford_ok)
println("    Burnside rank = ", red8_rank, " / 64 (M8)   commutant dim = ", red8_comm, " (want >1)")
println("    irreducibility test REJECTS it  : ", !red8_is_irreducible, "  -> K1 fires: ", K1_fires)

# -----------------------------------------------------------------------------
# 6. KILL-CONTROL K2: NON-FAITHFUL action g3 := g2 must FAIL faithfulness.
# -----------------------------------------------------------------------------
bad = [g0, g1, g2, g2]                   # linear dependency among generators
bad_rank = burnside_rank(bad)            # < 16 (kernel) -> not faithful
bad_comm = commutant_dim(bad)            # > 1
bad_faithful = (bad_rank == 16)
bad_irreducible = (bad_rank == 16) && (bad_comm == 1)
# also: it is NOT even a valid Cl(1,3) rep ({g2,g2}=2 g2^2 != 0 in an off-diagonal slot)
bad_clifford_resid = maximum(abs.(bad[3]*bad[4] + bad[4]*bad[3] - zeros(ComplexF64,4,4)))  # mu=3,nu=4 should be 0
bad_breaks_clifford = bad_clifford_resid > 1e-9
K2_fires = (!bad_faithful) && (!bad_irreducible)

println("[6] KILL-CONTROL K2 (non-faithful g3:=g2):")
println("    Burnside rank = ", bad_rank, " / 16   commutant dim = ", bad_comm, " (want >1)")
println("    faithfulness test REJECTS it    : ", !bad_faithful,
        " ; irreducibility REJECTS it: ", !bad_irreducible)
println("    (also breaks Clifford relation  : ", bad_breaks_clifford,
        ", resid ", bad_clifford_resid, ")  -> K2 fires: ", K2_fires)

# -----------------------------------------------------------------------------
# 7. POSITIVE / NEGATIVE / BOUNDARY controls on the module action.
# -----------------------------------------------------------------------------
Random.seed!(20260601)
# POSITIVE: random spinor acted on by a random Clifford word stays in C^4, and the
#           action is nonzero (the module is genuinely acted on, not trivial).
psi = randn(ComplexF64, 4); psi ./= norm(psi)
acted = g0 * g1 * psi
positive_action_nonzero = norm(acted) > 1e-6
# POSITIVE: a left-Weyl spinor stays left under the EVEN subalgebra (eigenspace invariant)
psiL = ComplexF64[1, 0, 0, 0]
even_image_L = (g1 * g2) * psiL
psiL_stays_left = norm(PR * even_image_L) < 1e-12 && norm(PL * even_image_L) > 1e-9
# NEGATIVE: a left-Weyl spinor is moved to the RIGHT block by an ODD generator
odd_image_L = g0 * psiL
psiL_moved_right = norm(PR * odd_image_L) > 1e-9
# BOUNDARY: an equal L/R superposition has zero chiral charge q = psi^dag gamma5 psi
psi_mix = ComplexF64[1, 0, 1, 0] / sqrt(2)
q_mix = real(psi_mix' * gamma5 * psi_mix)
boundary_zero_charge = isapprox(q_mix, 0.0; atol = 1e-12)
controls_ok = positive_action_nonzero && psiL_stays_left && psiL_moved_right && boundary_zero_charge

println("[7] Module-action controls:")
println("    POSITIVE: nonzero action on random spinor : ", positive_action_nonzero)
println("    POSITIVE: left spinor stays left under even: ", psiL_stays_left)
println("    NEGATIVE: odd gen moves left -> right      : ", psiL_moved_right)
println("    BOUNDARY: L/R superposition q = ", q_mix, " (zero charge: ", boundary_zero_charge, ")")
println("    controls ok: ", controls_ok)

# -----------------------------------------------------------------------------
# 8. HONEST verdict on the exists < runs < passes ladder.
# -----------------------------------------------------------------------------
booleans = Dict(
    "clifford_relation_measured"        => clifford_ok,
    "noncircular_signature_matches_pkg" => signature_matches_pkg,
    "noncircular_pseudoscalar_minus1"   => pkg_pseudoscalar_sq_is_minus1,
    "noncircular_gamma5_crosscheck"     => crosscheck_ok,
    "faithful_measured"                 => faithful,
    "irreducible_measured"              => irreducible,
    "dim4_invariant_confirmed"          => invariant_dim4_confirmed,
    "weyl_split_under_even_subalgebra"  => weyl_split_ok,
    "killcontrol_K1_reducible_fires"    => K1_fires,
    "killcontrol_K2_nonfaithful_fires"  => K2_fires,
    "module_action_controls"            => controls_ok,
)
all_pass = all(values(booleans))
honest_status = all_pass ? "passes local rerun (this run)" : "runs"

results = Dict{String,Any}(
    "object_id" => "clifford_module_gstructure",
    "geometry_scout" => "Clifford-module G-structure: Dirac spinor as irreducible Cl(1,3)-module",
    "classification" => "PoC",
    "promotion_allowed" => false,
    "carrier" => "LinearAlgebra (explicit 4x4 rep) + CliffordAlgebras.jl Cl(1,3) (independent anchor), non-numpy",
    "z3_used" => false,
    "z3_omission_reason" =>
        "Every claim is a rank/nullspace dimension of a measured complex matrix decided " *
        "by linear algebra over a continuous span, not an integer identity over literals. " *
        "A Z3 block would be a decorative tautology (this codebase's recurring weakness). " *
        "Load is carried by the Clifford carrier + Burnside/Schur measurements + kill-controls.",
    "anchored_invariant" => Dict(
        "statement" => "dim of the irreducible complex Cl(1,3)-module = 4 (Cl(1,3)⊗C ≅ M4(C); M2(H) on H^2 ~ C^4)",
        "module_dim_measured" => module_dim,
        "burnside_image_rank" => dirac_rank,
        "is_full_matrix_algebra_M(dim)^2" => matrix_algebra_full,
        "schur_commutant_dim" => dirac_comm,
        "confirmed" => invariant_dim4_confirmed,
    ),
    "construction" => Dict(
        "signature_pqr_package" => sig,
        "generator_squares_ours" => our_squares,
        "generator_squares_package" => gen_squares,
        "clifford_relation_max_residual" => max_clifford_residual,
        "clifford_relation_ok" => clifford_ok,
        "gamma5_diag" => g5_diag,
        "gamma5_sq_residual" => our_g5sq_resid,
    ),
    "noncircular_anchor" => Dict(
        "package" => "CliffordAlgebras.CliffordAlgebra(1,3)",
        "signature_matches" => signature_matches_pkg,
        "pseudoscalar_sq_scalar" => Isq_scalar,
        "pseudoscalar_sq_is_minus1" => pkg_pseudoscalar_sq_is_minus1,
        "package_predicted_gamma5_sq" => real(predicted_g5sq),
        "our_gamma5_sq_is_I" => our_g5sq_is_I,
        "crosscheck_ok" => crosscheck_ok,
    ),
    "faithful_irreducible" => Dict(
        "module_dim" => module_dim,
        "burnside_rank" => dirac_rank,
        "burnside_target_M4" => 16,
        "schur_commutant_dim" => dirac_comm,
        "faithful" => faithful,
        "irreducible" => irreducible,
    ),
    "weyl_split" => Dict(
        "gamma5_diag" => g5_diag,
        "chiral_form" => weyl_chiral_form,
        "dim_left" => rankPL,
        "dim_right" => rankPR,
        "each_dim2" => weyl_each_dim2,
        "max_even_commutator_with_g5" => max_even_comm,
        "even_commutes" => even_commutes,
        "max_odd_anticommutator_with_g5" => max_odd_anti,
        "odd_anticommutes" => odd_anticommutes,
        "max_even_cross_block_leak" => max_even_leak,
        "even_subalgebra_invariant" => even_invariant,
        "odd_cross_block_leak" => odd_leak,
        "odd_connects_L_R" => odd_connects,
        "left_weyl_burnside_rank_M2" => left_weyl_rank,
        "right_weyl_burnside_rank_M2" => right_weyl_rank,
        "weyl_blocks_irreducible" => weyl_blocks_irreducible,
        "weyl_split_ok" => weyl_split_ok,
    ),
    "killcontrol_K1_reducible" => Dict(
        "action" => "rho ⊕ rho on C^8 (genuine but reducible Cl(1,3) rep)",
        "valid_clifford_rep" => red8_clifford_ok,
        "burnside_rank" => red8_rank,
        "burnside_target_M8" => 64,
        "commutant_dim" => red8_comm,
        "irreducibility_test_rejects" => !red8_is_irreducible,
        "K1_fires" => K1_fires,
    ),
    "killcontrol_K2_nonfaithful" => Dict(
        "action" => "g3 := g2 (linear dependency among generators)",
        "burnside_rank" => bad_rank,
        "burnside_target_M4" => 16,
        "commutant_dim" => bad_comm,
        "faithfulness_test_rejects" => !bad_faithful,
        "irreducibility_test_rejects" => !bad_irreducible,
        "also_breaks_clifford_relation" => bad_breaks_clifford,
        "K2_fires" => K2_fires,
    ),
    "module_action_controls" => Dict(
        "positive_nonzero_action" => positive_action_nonzero,
        "positive_left_stays_left_under_even" => psiL_stays_left,
        "negative_odd_moves_left_to_right" => psiL_moved_right,
        "boundary_superposition_zero_charge" => q_mix,
        "controls_ok" => controls_ok,
    ),
    "genuineness_booleans" => booleans,
    "all_pass" => all_pass,
    "honest_status_ladder" => honest_status,
)

println("\n" * "="^74)
println("GENUINENESS BOOLEANS:")
for k in sort(collect(keys(booleans)))
    println("    ", rpad(k, 36), " : ", booleans[k])
end
println("ALL PASS              : ", all_pass)
println("HONEST LADDER STATUS  : ", honest_status)
println("="^74)

outpath = joinpath(@__DIR__, "clifford_module_gstructure_results.json")
open(outpath, "w") do io
    JSON.print(io, results, 2)
end
println("results written to: ", outpath)
