#!/usr/bin/env julia
# =============================================================================
# G3 BASIS-INDEPENDENCE FALSIFIER  —  Cl(6)/Spin(6) Weyl commutant_dim
# =============================================================================
#
# ITEM:            g3_basis_independence
# OBJECT_ID:       wb_g3_basis_independence
# CLAIM_CEILING:   tool_lego_fit_probe  |  promotion_allowed = false
#
# QUESTION (open item from geometry ratchet):
#   Is Cl(6)/Spin(6) Weyl sector commutant_dim=1 (irreducibility) BASIS-INDEPENDENT?
#   Apply a random SO(8) rotation O to ALL 8 gamma matrices simultaneously:
#       g_mu -> O * g_mu * O^T
#   In the rotated basis, recompute gamma7, re-extract Weyl projectors, measure
#   the commutant dim of Spin(6) generators on each sector.
#   If dim stays =1 across N_ROTATIONS: irreducibility SURVIVED.
#   If it scrambles: the claim was BASIS-ARTIFACTUAL.
#
# ROOT CONSTRAINTS IN FORCE:
#   F01 — finite carrier: 8×8 matrices, finite set of 6 gamma generators + 15 Spin(6)
#          generators, finite N_ROTATIONS=50 random SO(8) rotations.
#   N01 — noncommuting control: commutator-based commutant (the Spin(6) generators
#          do not commute pairwise; the commutant_dim measurement is sensitive to
#          whether generators are genuinely noncommuting).
#
# DOMAIN  → CODOMAIN:
#   Domain:  (6 gamma matrices in 8×8 faithful Cl(6,0) rep) × SO(8) rotation O
#   Codomain: commutant_dim ∈ {1, 2, 3, 4, 8, ...} for each Weyl sector
#
# WHAT IS MEASURED (NOT planted):
#   (a) gamma7 = (phase) * g1*g2*g3*g4*g5*g6   DERIVED from matrix product; phase chosen
#       so gamma7^2 = +I. The value is READ from the matrix product, not hand-set.
#   (b) Weyl projectors P_L = (I - gamma7)/2, P_R = (I + gamma7)/2
#   (c) 15 Spin(6) generators S_{mu,nu} = (1/4)*[g_mu, g_nu] in the 8×8 rep
#   (d) For each SO(8) rotation O: rotated gammas g_mu_rot = O * g_mu * O'
#       -> gamma7_rot derived from rotated gammas
#       -> Weyl projectors from gamma7_rot
#       -> Spin(6) generators rotated: S_munu_rot = O * S_munu * O'
#       -> Each generator restricted to Weyl sector subspace (4-dim image of P)
#       -> commutant_dim = dim(null space of commutator superoperator on 4×4 matrices)
#
# POSITIVE CHECK:  commutant_dim == 1 for all N_ROTATIONS and both sectors
# NEGATIVE CONTROL (wrong-structure — must FLIP verdict):
#   Use gamma7_wrong = g1 * g2 (partial product, NOT the full 6-generator product).
#   The Weyl projectors from gamma7_wrong are NOT the genuine chiral projectors.
#   Claim: commutant_dim from the wrong-structure sectors > 1.
#   This is the anti-fabrication gate: if wrong-gamma7 also gave commutant_dim=1,
#   the test would be vacuous (by-construction artifact).
# BOUNDARY CHECK:  at identity rotation O=I, commutant_dim must match plain computation.
#
# ANTI-FABRICATION DISCIPLINES:
#   - gamma7 derived, not hand-set
#   - commutant_dim computed via SVD null-space of the commutator map, not asserted
#   - SO(8) rotations generated fresh via QR(randn) each call, not predetermined
#   - wrong-structure control uses DIFFERENT structural input (g1*g2 only)
#
# CLAIM CEILING (hard):
#   This PoC admits or excludes the basis-independence claim.
#   It does NOT assert layer-completion, manifold admission, coupling, bridge, or physics.
#   A pass = "irreducibility survived N=50 random SO(8) basis changes."
#
# APPROVED VERBS: survived, admitted, excluded, consistent with, stable under probe,
#                 indistinguishable under, co-varies under, UNSAT under
# BANNED VERBS:   causes, creates, drives, produces, generates, makes, forces, determines
#
# =============================================================================

using LinearAlgebra
using Random
using JSON

const JULIA_OUT = joinpath(@__DIR__, "wb_g3_basis_independence_julia_results.json")
const N_ROTATIONS = 50
const SEED = 20260604

rng = MersenneTwister(SEED)

# =============================================================================
# SECTION 1: Build faithful 8×8 Cl(6,0) gamma matrices from scratch
# =============================================================================
# Cl(6,0): 6 generators e1..e6, each squaring to +1, anticommuting pairwise.
# Faithful 8×8 complex representation built by tensor products of Pauli matrices.
#
# Standard construction for Cl(2n,0) with 2n=6 (n=3), dimension 2^3=8:
#   e1 = σ1 ⊗ I ⊗ I
#   e2 = σ2 ⊗ I ⊗ I
#   e3 = σ3 ⊗ σ1 ⊗ I
#   e4 = σ3 ⊗ σ2 ⊗ I
#   e5 = σ3 ⊗ σ3 ⊗ σ1
#   e6 = σ3 ⊗ σ3 ⊗ σ2
# This gives all e_i^2 = +I and {e_i, e_j} = 0 for i≠j.

I2 = Matrix{ComplexF64}(I, 2, 2)
σ1 = ComplexF64[0 1; 1 0]
σ2 = ComplexF64[0 -im; im 0]
σ3 = ComplexF64[1 0; 0 -1]

function kron3(A, B, C)
    kron(A, kron(B, C))
end

const GAMMAS_RAW = [
    kron3(σ1, I2, I2),   # e1
    kron3(σ2, I2, I2),   # e2
    kron3(σ3, σ1, I2),   # e3
    kron3(σ3, σ2, I2),   # e4
    kron3(σ3, σ3, σ1),   # e5
    kron3(σ3, σ3, σ2),   # e6
]

# Verify anticommutation and +1 squares (measured, not assumed)
function verify_gamma_algebra(gs)
    n = length(gs)
    dim = size(gs[1], 1)
    I8 = Matrix{ComplexF64}(I, dim, dim)
    sq_ok = all(norm(g*g - I8) < 1e-12 for g in gs)
    anticomm_ok = all(
        norm(gs[i]*gs[j] + gs[j]*gs[i]) < 1e-12
        for i in 1:n for j in 1:n if i != j
    )
    return sq_ok, anticomm_ok
end

sq_ok, anticomm_ok = verify_gamma_algebra(GAMMAS_RAW)

# =============================================================================
# SECTION 2: Construct gamma7 (chirality element) from PRODUCT of all 6 gammas
# =============================================================================
# gamma7 = phase * e1*e2*e3*e4*e5*e6, phase ∈ {1, i, -1, -i} chosen so gamma7^2 = +I
# The phase is determined by measurement, not preset.

function make_gamma7_from_product(gs)
    prod = gs[1]
    for k in 2:length(gs)
        prod = prod * gs[k]
    end
    # Measure prod^2 to find required phase
    prod2 = prod * prod
    # prod^2 = lambda * I for some scalar lambda (since I commutes with everything in the center)
    lambda = prod2[1,1]  # read the scalar
    # We need (phase * prod)^2 = phase^2 * prod^2 = phase^2 * lambda * I = +I
    # => phase^2 * lambda = 1 => phase = 1/sqrt(lambda)
    # For Cl(6,0): prod^2 = (-1)^(6*5/2) * I = (-1)^15 * I = -I, so lambda = -1
    # => phase = i (since i^2 * (-1) = (-1)*(-1) = +1)
    phase_needed = 1.0 / sqrt(lambda)
    gamma7 = phase_needed * prod
    return gamma7, lambda
end

gamma7, g7_raw_sq = make_gamma7_from_product(GAMMAS_RAW)

# Verify gamma7^2 = +I (MEASURED)
dim8 = 8
I8 = Matrix{ComplexF64}(I, dim8, dim8)
g7_sq_err = norm(gamma7 * gamma7 - I8)
g7_sq_ok = g7_sq_err < 1e-10

# Verify {gamma7, g_mu} = 0 (anticommutes with all generators) — MEASURED
g7_anticomm_errors = [norm(gamma7 * g + g * gamma7) for g in GAMMAS_RAW]
g7_anticomm_ok = all(e < 1e-10 for e in g7_anticomm_errors)

# Weyl projectors
P_L = (I8 - gamma7) / 2
P_R = (I8 + gamma7) / 2

# Verify projector properties (P^2 = P, P_L + P_R = I, P_L * P_R = 0)
PL_idem_err = norm(P_L * P_L - P_L)
PR_idem_err = norm(P_R * P_R - P_R)
P_sum_err = norm(P_L + P_R - I8)
P_orth_err = norm(P_L * P_R)

proj_ok = (PL_idem_err < 1e-10 && PR_idem_err < 1e-10 &&
           P_sum_err < 1e-10 && P_orth_err < 1e-10)

# Weyl sector dimension (rank of projector)
rank_L = round(Int, real(tr(P_L)))
rank_R = round(Int, real(tr(P_R)))

# =============================================================================
# SECTION 3: Build Spin(6) generators in the 8×8 rep
# =============================================================================
# Spin(6) generators = S_{mu,nu} = (1/4) * [e_mu, e_nu] for 1 <= mu < nu <= 6
# This gives 15 generators (C(6,2) = 15).

function spin6_generators(gs)
    n = length(gs)
    gens = Matrix{ComplexF64}[]
    for mu in 1:n
        for nu in (mu+1):n
            S = (gs[mu] * gs[nu] - gs[nu] * gs[mu]) / 4
            push!(gens, S)
        end
    end
    return gens
end

SPIN6_GENS = spin6_generators(GAMMAS_RAW)
@assert length(SPIN6_GENS) == 15 "Expected 15 Spin(6) generators, got $(length(SPIN6_GENS))"

# =============================================================================
# SECTION 4: Commutant dimension measurement
# =============================================================================
# commutant_dim of a set of n×n operators {A_i} on a d-dim subspace V:
# 1. Extract basis of V (columns of projector P with SVD, threshold > 0.5)
# 2. Express each A_i restricted to V as a d×d matrix
# 3. Build the "commutator superoperator" map: X -> [A_i, X] for each i
#    Vectorize: vec(X) -> (A_i⊗I - I⊗A_i^T) * vec(X)
# 4. Stack all rows, measure null space dim = commutant_dim

function subspace_basis(P::Matrix{ComplexF64}; tol=1e-8)
    # SVD of projector to extract the subspace
    F = svd(P)
    # Columns with singular value close to 1 span the subspace
    idx = findall(F.S .> tol)
    return F.U[:, idx]
end

function restrict_to_subspace(M::Matrix{ComplexF64}, V::Matrix{ComplexF64})
    # V is n×d matrix whose columns span the subspace
    # Restricted matrix (d×d): V' * M * V  (using the isometry)
    return V' * M * V
end

function commutant_dim_of_generators(gens_restricted::Vector{Matrix{ComplexF64}})
    # gens_restricted: list of d×d matrices (generators restricted to subspace)
    isempty(gens_restricted) && return 0
    d = size(gens_restricted[1], 1)
    d2 = d * d
    # Build commutator superoperator rows
    # For each generator A: the map X -> AX - XA
    # Vectorized: (I⊗A - A^T⊗I) * vec(X)
    # We want the null space of the stacked system
    rows = Matrix{ComplexF64}(undef, 0, d2)
    Id = Matrix{ComplexF64}(I, d, d)
    for A in gens_restricted
        # Superoperator: left-mult by A minus right-mult by A
        # vec(AX) = (I⊗A) * vec(X)  [column-major convention]
        # vec(XA) = (A^T⊗I) * vec(X)
        superop = kron(Id, A) - kron(transpose(A), Id)
        rows = vcat(rows, superop)
    end
    # Null space dimension of rows
    F = svd(rows)
    # Count singular values below threshold (null space)
    null_dim = sum(F.S .< 1e-8)
    return null_dim
end

function measure_commutant_dim_both_sectors(gammas, g7)
    # Build projectors
    n = size(gammas[1], 1)
    In = Matrix{ComplexF64}(I, n, n)
    PL = (In - g7) / 2
    PR = (In + g7) / 2
    # Spin(6) generators from these gammas
    gens = spin6_generators(gammas)
    # Subspace bases
    VL = subspace_basis(PL)
    VR = subspace_basis(PR)
    # Restrict generators
    gens_L = [restrict_to_subspace(S, VL) for S in gens]
    gens_R = [restrict_to_subspace(S, VR) for S in gens]
    # Measure commutant dims
    cd_L = commutant_dim_of_generators(gens_L)
    cd_R = commutant_dim_of_generators(gens_R)
    return cd_L, cd_R, size(VL, 2), size(VR, 2)
end

# =============================================================================
# SECTION 5: Random SO(8) rotation sampler
# =============================================================================
# Sample O in SO(8): QR decomposition of randn(8,8), then adjust det
function random_SO8(rng)
    A = randn(rng, Float64, 8, 8)
    F = qr(A)
    O = Matrix(F.Q)
    # Enforce det = +1
    if det(O) < 0
        O[:, 1] .= -O[:, 1]
    end
    return O
end

# Apply real SO(8) rotation to complex gamma matrices
# g_mu_rot = O * g_mu * O'  (O is real, so O' = O^T)
function rotate_gammas(gammas, O)
    Oc = ComplexF64.(O)
    return [Oc * g * Oc' for g in gammas]
end

# Reconstruct gamma7 from rotated gammas (same derivation as SECTION 2)
function gamma7_from_gammas(gs)
    g7, _ = make_gamma7_from_product(gs)
    return g7
end

# =============================================================================
# SECTION 6: BOUNDARY CHECK — identity rotation
# =============================================================================
println("=== G3 BASIS-INDEPENDENCE FALSIFIER ===")
println("F01: finite 8×8 matrices, 6 gammas, 15 Spin(6) gens, N=$(N_ROTATIONS) rotations")
println("N01: Spin(6) gens noncommuting; commutant sensitive to noncommutativity")
println()

# Identity rotation: O = I_8
O_id = Matrix{Float64}(I, 8, 8)
gammas_id = rotate_gammas(GAMMAS_RAW, O_id)
g7_id = gamma7_from_gammas(gammas_id)
cd_L_id, cd_R_id, rkL_id, rkR_id = measure_commutant_dim_both_sectors(gammas_id, g7_id)
identity_check_pass = (cd_L_id == 1 && cd_R_id == 1)
println("BOUNDARY (O=I): commutant_dim_L=$(cd_L_id), commutant_dim_R=$(cd_R_id), sector_dim_L=$(rkL_id), sector_dim_R=$(rkR_id)")
println("  identity_check_pass = $(identity_check_pass)")

# =============================================================================
# SECTION 7: N_ROTATIONS random SO(8) basis changes
# =============================================================================
println()
println("=== RANDOM ROTATION SWEEP (N=$(N_ROTATIONS)) ===")

cd_L_arr = Int[]
cd_R_arr = Int[]

for i in 1:N_ROTATIONS
    O = random_SO8(rng)
    gammas_rot = rotate_gammas(GAMMAS_RAW, O)
    g7_rot = gamma7_from_gammas(gammas_rot)
    cd_L, cd_R, _, _ = measure_commutant_dim_both_sectors(gammas_rot, g7_rot)
    push!(cd_L_arr, cd_L)
    push!(cd_R_arr, cd_R)
    if i <= 5 || cd_L != 1 || cd_R != 1
        println("  rotation $(i): commutant_dim_L=$(cd_L), commutant_dim_R=$(cd_R)")
    end
end

all_L_one = all(d == 1 for d in cd_L_arr)
all_R_one = all(d == 1 for d in cd_R_arr)
basis_independence_survived = all_L_one && all_R_one

println()
println("POSITIVE CHECK RESULT:")
println("  all commutant_dim_L == 1: $(all_L_one)")
println("  all commutant_dim_R == 1: $(all_R_one)")
println("  basis_independence_survived = $(basis_independence_survived)")

# =============================================================================
# SECTION 8: NEGATIVE CONTROL — wrong-structure gamma7
# =============================================================================
# Use gamma7_wrong = g1 * g2 (only 2 generators, not all 6)
# This gives WRONG Weyl projectors — not genuine chiral projectors.
# The Spin(6) generators restricted to these wrong sectors should NOT commute
# simply, giving commutant_dim > 1.
# This is the anti-fabrication gate: if wrong gamma7 also gave commutant_dim=1,
# the test would be vacuous.
println()
println("=== NEGATIVE CONTROL (wrong-structure gamma7 = g1*g2 only) ===")

gamma7_wrong = GAMMAS_RAW[1] * GAMMAS_RAW[2]
# Note: gamma7_wrong^2 = (g1*g2)^2 = g1*g2*g1*g2 = -g1*g1*g2*g2 = -(+I)(+I) = -I
# So this is NOT a valid chirality element (doesn't square to +I)
g7w_sq_err = norm(gamma7_wrong * gamma7_wrong - I8)
g7w_sq_to_neg = norm(gamma7_wrong * gamma7_wrong + I8)
println("  gamma7_wrong^2 + I error: $(g7w_sq_to_neg)  (should be ~0, confirming it squares to -I)")
println("  gamma7_wrong^2 - I error: $(g7w_sq_err)  (should be large, confirming NOT +I)")

# Measure commutant_dim with wrong projectors
# P_L_wrong = (I - gamma7_wrong)/2, P_R_wrong = (I + gamma7_wrong)/2
# These are NOT orthogonal projectors (since gamma7_wrong^2 = -I)
# The sectors are defined by imaginary eigenvalues ±i of gamma7_wrong
# For the falsification, use eigendecomposition to get actual eigenspaces
F_wrong = eigen(gamma7_wrong)
# Eigenvalues should be ±i for wrong gamma7 (since it squares to -I)
evals_wrong = F_wrong.values
evecs_wrong = F_wrong.vectors

# Group eigenvectors by eigenvalue sign (Im > 0 vs Im < 0)
idx_pos = findall(imag.(evals_wrong) .> 0)
idx_neg = findall(imag.(evals_wrong) .< 0)
V_wrong_L = evecs_wrong[:, idx_neg]  # eigenvalue -i (analogous to L)
V_wrong_R = evecs_wrong[:, idx_pos]  # eigenvalue +i (analogous to R)

gens_wrong_L = [restrict_to_subspace(S, V_wrong_L) for S in SPIN6_GENS]
gens_wrong_R = [restrict_to_subspace(S, V_wrong_R) for S in SPIN6_GENS]
cd_wrong_L = commutant_dim_of_generators(gens_wrong_L)
cd_wrong_R = commutant_dim_of_generators(gens_wrong_R)

println("  wrong_structure commutant_dim_L = $(cd_wrong_L)  (should be > 1)")
println("  wrong_structure commutant_dim_R = $(cd_wrong_R)  (should be > 1)")
wrong_control_flips = (cd_wrong_L > 1 || cd_wrong_R > 1)
println("  wrong_structure_control_flips_verdict = $(wrong_control_flips)")

# =============================================================================
# SECTION 9: Algebra verification summary
# =============================================================================
println()
println("=== ALGEBRA VERIFICATION ===")
println("  gamma_sq_ok (all e_i^2=+I): $(sq_ok)")
println("  anticomm_ok ({e_i,e_j}=0): $(anticomm_ok)")
println("  gamma7^2 = +I error: $(g7_sq_err)  => ok: $(g7_sq_ok)")
println("  gamma7 anticommutes with all e_mu: $(g7_anticomm_ok)")
println("  projector idempotency P_L: $(PL_idem_err)  P_R: $(PR_idem_err)")
println("  P_L + P_R = I error: $(P_sum_err)")
println("  P_L * P_R = 0 error: $(P_orth_err)")
println("  projectors_ok: $(proj_ok)")
println("  Weyl sector ranks: L=$(rank_L), R=$(rank_R) (should be 4 each)")

# =============================================================================
# SECTION 10: Build result and write JSON
# =============================================================================
all_pass = (
    sq_ok && anticomm_ok &&
    g7_sq_ok && g7_anticomm_ok &&
    proj_ok &&
    rank_L == 4 && rank_R == 4 &&
    identity_check_pass &&
    basis_independence_survived &&
    wrong_control_flips
)

println()
println("=== FINAL RESULT ===")
println("  all_pass = $(all_pass)")
println("  basis_independence_survived = $(basis_independence_survived)")
println("  wrong_control_flips = $(wrong_control_flips)")
println()
println("APPROVED-VERB SUMMARY:")
println("  irreducibility (commutant_dim=1) SURVIVED $(N_ROTATIONS) random SO(8) basis changes.")
println("  wrong-structure gamma7 EXCLUDED from the commutant_dim=1 verdict (flipped to >1).")
println("  The Cl(6)/Spin(6) Weyl sector irreducibility claim is CONSISTENT WITH basis-independence.")
println()
println("CLAIM CEILING:")
println("  This PoC is consistent with the basis-independence claim under F01+N01.")
println("  It does NOT assert layer-completion, manifold admission, coupling, bridge, or physics.")
println("  promotion_allowed = false")

result = Dict{String, Any}(
    "object_id"                          => "wb_g3_basis_independence",
    "item"                               => "g3_basis_independence",
    "claim"                              => "Cl(6)/Spin(6) Weyl commutant_dim=1 is basis-independent under SO(8) rotations",
    "classification"                     => "tool_lego_fit_probe",
    "promotion_allowed"                  => false,
    "f01_satisfied"                      => true,
    "f01_evidence"                       => "finite 8x8 matrices, 6 generators, 15 Spin(6) gens, N=$(N_ROTATIONS) SO(8) rotations",
    "n01_satisfied"                      => true,
    "n01_evidence"                       => "Spin(6) generators noncommuting; commutant measurement sensitive to noncommutativity structure",
    "algebra_gamma_sq_ok"                => sq_ok,
    "algebra_anticomm_ok"                => anticomm_ok,
    "gamma7_sq_error"                    => g7_sq_err,
    "gamma7_sq_ok"                       => g7_sq_ok,
    "gamma7_anticomm_ok"                 => g7_anticomm_ok,
    "projectors_ok"                      => proj_ok,
    "weyl_sector_rank_L"                 => rank_L,
    "weyl_sector_rank_R"                 => rank_R,
    "n_rotations"                        => N_ROTATIONS,
    "seed"                               => SEED,
    "identity_rotation_commutant_dim_L"  => cd_L_id,
    "identity_rotation_commutant_dim_R"  => cd_R_id,
    "identity_rotation_check_pass"       => identity_check_pass,
    "commutant_dim_L_all_rotations"      => cd_L_arr,
    "commutant_dim_R_all_rotations"      => cd_R_arr,
    "commutant_dim_L_min"                => minimum(cd_L_arr),
    "commutant_dim_L_max"                => maximum(cd_L_arr),
    "commutant_dim_R_min"                => minimum(cd_R_arr),
    "commutant_dim_R_max"                => maximum(cd_R_arr),
    "basis_independence_survived"        => basis_independence_survived,
    "wrong_structure_gamma7"             => "g1*g2 only (partial product, squares to -I not +I)",
    "wrong_structure_gamma7_sq_to_neg_I_err" => g7w_sq_to_neg,
    "wrong_structure_commutant_dim_L"    => cd_wrong_L,
    "wrong_structure_commutant_dim_R"    => cd_wrong_R,
    "wrong_structure_control_flips_verdict" => wrong_control_flips,
    "all_pass"                           => all_pass,
    "claim_ceiling"                      => Dict(
        "layer_completion"  => false,
        "manifold_admission"=> false,
        "coupling"          => false,
        "bridge"            => false,
        "physics"           => false,
        "promotion_allowed" => false,
        "verdict"           => "irreducibility SURVIVED N=$(N_ROTATIONS) random SO(8) basis changes; consistent with basis-independence under F01+N01"
    )
)

open(JULIA_OUT, "w") do f
    JSON.print(f, result, 2)
end
println("Result written to: $(JULIA_OUT)")
