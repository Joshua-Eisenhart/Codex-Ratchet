# =============================================================================
# sl2c_spin13_chiral_gstructure  —  GENUINE isolated Julia sim (PoC)
#
# OBJECT: the Lorentzian spin G-structure  Spin(1,3) ≅ SL(2,C), whose two
#         INEQUIVALENT fundamental reps ARE the left/right Weyl chiralities:
#           left-handed  (1/2,0):  psi_L -> M psi_L
#           right-handed (0,1/2):  psi_R -> (M^dagger)^{-1} psi_R
#         This is the relativistic chirality-definer. The Euclidean version
#         (SU(2) = Spin(3)) is already simulated in g_su2_spin3_double_cover.jl;
#         this file is its Lorentzian lift.
#
# WHAT IS MEASURED (never planted to a target):
#   1. SL(2,C): M = exp(sum a_k (i sigma_k/2) + b_k (sigma_k/2)) (3 rotations
#      J_k = i sigma_k/2 anti-Hermitian, 3 boosts K_k = sigma_k/2 Hermitian).
#      det(M) is READ OUT and compared to 1 (anchor: det exp(X) = exp(tr X),
#      and tr of every generator is 0, so det = 1 by an INDEPENDENT identity).
#   2. THE TWO CHIRAL REPS coincide under ROTATIONS and differ under BOOSTS:
#      diff(M) = || M - (M^dagger)^{-1} || is READ OUT for pure rotations
#      (expect ~0: M unitary => (M^dagger)^{-1} = M) and pure boosts (expect > 0:
#      M Hermitian-positive => (M^dagger)^{-1} = M^{-1} != M). This split IS the
#      chirality. INEQUIVALENCE is further measured structurally: no single fixed
#      S satisfies S M S^{-1} = (M^dagger)^{-1} for all M (the left/right reps are
#      genuinely different irreps), tested by solving the linear intertwiner
#      conditions over a generating set and showing the only solution is S = 0.
#   3. DOUBLE COVER SL(2,C) -> SO(3,1): X = x_mu sigma^mu (Hermitian 2x2),
#      x -> M X M^dagger. The induced Lambda(M) on the 4-vector is READ OUT and
#      checked to preserve eta = diag(1,-1,-1,-1) (Lambda^T eta Lambda = eta) and
#      to be 2-to-1 (Lambda(M) = Lambda(-M)), with the spinor sign flip (M(2pi
#      rotation) = -M) living ONLY upstairs.
#   4. gamma5 / WEYL BASIS: in the chiral basis gamma5 = diag(-I2,+I2) splits the
#      Dirac (1/2,0)+(0,1/2) into the two Weyl blocks; P_L,P_R project them. The
#      Dirac spinor rep S(M) = diag(M, (M^dagger)^{-1}) is READ OUT; restricted to
#      ROTATIONS both blocks reduce to the SAME SU(2) element (the Euclidean
#      Spin(3) already simulated); under BOOSTS the two blocks differ. gamma5
#      commutes with S(M) for every M (chirality is a good quantum number of the
#      proper Lorentz group) and the L/R blocks are exactly M and (M^dagger)^{-1}.
#
# KILL-CONTROLS (must FIRE / give the null result, else the test is vacuous):
#   (a) ROTATION-vs-BOOST: under rotations the L and R reps COINCIDE
#       (diff ~ 0 -> chirality invisible to rotations); under boosts they DIFFER
#       (diff > 0 -> the boost is the chirality-distinguisher). Matches the
#       l2_weyl result that the gamma5 charge is rotation-invariant, boost-variant.
#   (b) WRONG REP: using M^dagger (not (M^dagger)^{-1}) or M^transpose for the
#       right-handed rep must FAIL: it does not preserve the epsilon_AB spinor
#       pairing (epsilon = [[0,1],[-1,0]], the SL(2,C)-invariant symplectic form,
#       satisfies M^T epsilon M = epsilon; the broken duals do NOT give a
#       consistent intertwiner) and/or breaks the SO(3,1) covariance of S(M).
#
# all_pass iff: det(M)=1; the two reps coincide under rotations and differ under
#   boosts; the reps are structurally INEQUIVALENT (only S=0 intertwines them);
#   SL(2,C)->SO(3,1) preserves eta and is 2-to-1; the gamma5/Weyl connection holds
#   (S(M) block-diag = (M,(M^dag)^{-1}), gamma5 commutes, rotation reduces both
#   blocks to one SU(2)); and BOTH kill-controls fire.
#
# HONEST: forced (standard rep theory, NOT novel) = SL(2,C)=Spin(1,3) double
#   cover; the (1/2,0)/(0,1/2) reps; eta preservation; epsilon-invariance. novel
#   = none. classification = PoC ; promotion_allowed = false.
#
# Tools: LinearAlgebra (carrier), Random, JSON. No Z3 (would be decorative here).
# =============================================================================

using LinearAlgebra
using Random
using JSON

Random.seed!(20260601)

# ----- Pauli basis -----------------------------------------------------------
const σ0 = ComplexF64[1 0; 0 1]
const σ1 = ComplexF64[0 1; 1 0]
const σ2 = ComplexF64[0 -im; im 0]
const σ3 = ComplexF64[1 0; 0 -1]
const SIGMA = (σ0, σ1, σ2, σ3)            # sigma^mu = (I, sigma_k)
const I2 = Matrix{ComplexF64}(I, 2, 2)
const I4 = Matrix{ComplexF64}(I, 4, 4)
const ETA = Float64[1 0 0 0; 0 -1 0 0; 0 0 -1 0; 0 0 0 -1]   # eta = diag(1,-1,-1,-1)
# epsilon_AB: the SL(2,C)-invariant symplectic spinor metric (M^T eps M = eps)
const EPS = ComplexF64[0 1; -1 0]

# sl(2,C) generators: 3 rotations J_k = i sigma_k/2 (anti-Hermitian), 3 boosts
# K_k = sigma_k/2 (Hermitian). All traceless => det(exp) = 1.
J(k) = im * SIGMA[k+1] / 2
K(k) = SIGMA[k+1] / 2

# build an SL(2,C) element from rotation params a (3-vec) and boost params b (3-vec)
function sl2c(a::Vector{<:Real}, b::Vector{<:Real})
    X = zeros(ComplexF64, 2, 2)
    for k in 1:3
        X += a[k] * J(k) + b[k] * K(k)
    end
    exp(X)
end

rand_rot(rng)   = sl2c(2π .* (rand(rng, 3) .- 0.5), zeros(3))          # pure rotation (unitary)
rand_boost(rng) = sl2c(zeros(3), 3.0 .* (rand(rng, 3) .- 0.5))         # pure boost (Hermitian pos.)
function rand_sl2c(rng)                                                # generic Lorentz
    sl2c(2π .* (rand(rng, 3) .- 0.5), 3.0 .* (rand(rng, 3) .- 0.5))
end

# the two chiral fundamental reps
rep_L(M) = M                              # (1/2,0)
rep_R(M) = inv(M')                        # (0,1/2) = (M^dagger)^{-1}
# wrong duals for the kill-control
rep_R_wrong_dagger(M)    = M'             # M^dagger  (NOT inverse) -- breaks the pairing
rep_R_wrong_transpose(M) = transpose(M)  # M^T

# Dirac (Weyl-basis) spinor rep: S(M) = diag(M, (M^dagger)^{-1}); gamma5=diag(-I,+I)
S_dirac(M) = ComplexF64[rep_L(M) zeros(ComplexF64,2,2); zeros(ComplexF64,2,2) rep_R(M)]
const GAMMA5 = ComplexF64[-I2 zeros(ComplexF64,2,2); zeros(ComplexF64,2,2) I2]
const P_L = (I4 - GAMMA5) / 2
const P_R = (I4 + GAMMA5) / 2

# X = x_mu sigma^mu (Hermitian 2x2); the bispinor of a 4-vector
xvec_to_X(x) = x[1]*σ0 + x[2]*σ1 + x[3]*σ2 + x[4]*σ3
# read out the 4-vector back from a Hermitian X:  x^mu = (1/2) tr(sigma^mu X)
# with the metric sign for spatial parts handled by the inverse map below.
function X_to_xvec(X)
    # sigma^mu basis is (I, s1, s2, s3); for Hermitian X, x0 = tr(X)/2,
    # x_k = tr(sigma_k X)/2.  (These are the contravariant components.)
    [real(0.5*tr(σ0*X)), real(0.5*tr(σ1*X)), real(0.5*tr(σ2*X)), real(0.5*tr(σ3*X))]
end

# the induced Lorentz transform: column j is the image of basis 4-vector e_j
function lorentz_Lambda(M)
    Λ = zeros(Float64, 4, 4)
    for j in 1:4
        e = zeros(4); e[j] = 1.0
        X = xvec_to_X(e)
        Xp = M * X * M'
        Λ[:, j] = X_to_xvec(Xp)
    end
    Λ
end

# =============================================================================
results = Dict{String,Any}()
results["object_id"] = "sl2c_spin13_chiral_gstructure"
results["object"] = "Spin(1,3) ~ SL(2,C): left/right Weyl reps + SO(3,1) double cover"
results["classification"] = "PoC"
results["promotion_allowed"] = false
results["seed"] = 20260601
results["tools"] = Dict("carrier" => "LinearAlgebra", "io" => "JSON", "z3" => "absent (decorative here)")

# =============================================================================
# 1. SL(2,C): det(M) = 1  (MEASURED, anchored to det exp(X) = exp(tr X))
# =============================================================================
n_det = 500
function check_det(n_det)
    max_det_err = 0.0
    max_tr_gen = 0.0
    rng = MersenneTwister(1)
    # generators are traceless -> the INDEPENDENT identity det exp(X)=exp(tr X)=1
    for k in 1:3
        max_tr_gen = max(max_tr_gen, abs(tr(J(k))), abs(tr(K(k))))
    end
    for _ in 1:n_det
        M = rand_sl2c(rng)
        max_det_err = max(max_det_err, abs(det(M) - 1))
    end
    max_det_err, max_tr_gen
end
max_det_err, max_tr_gen = check_det(n_det)
results["sl2c_det"] = Dict(
    "samples" => n_det,
    "max_det_minus_1" => max_det_err,
    "max_generator_trace" => max_tr_gen,
    "anchor" => "det exp(X) = exp(tr X); all sl(2,C) generators are traceless -> det M = 1",
    "pass" => max_det_err < 1e-10 && max_tr_gen < 1e-12,
)

# =============================================================================
# 2a. THE CHIRALITY: rotations coincide (L=R), boosts differ.  MEASURED.
#     diff(M) = || rep_L(M) - rep_R(M) ||  =  || M - (M^dagger)^{-1} ||
# =============================================================================
n_chi = 500
function rep_diff_stats(gen, n; rng_seed)
    rng = MersenneTwister(rng_seed)
    mx = 0.0; mn = Inf
    for _ in 1:n
        M = gen(rng)
        d = opnorm(rep_L(M) - rep_R(M))
        mx = max(mx, d); mn = min(mn, d)
    end
    mn, mx
end
rot_diff_min, rot_diff_max = rep_diff_stats(rand_rot,   n_chi; rng_seed=11)
boost_diff_min, boost_diff_max = rep_diff_stats(rand_boost, n_chi; rng_seed=12)
# sanity: a pure rotation IS unitary (so M = (M^dag)^{-1}); a pure boost IS Hermitian
rngU = MersenneTwister(13)
Usamp = rand_rot(rngU); Bsamp = rand_boost(rngU)
rot_is_unitary = opnorm(Usamp'*Usamp - I2) < 1e-10
boost_is_hermitian = opnorm(Bsamp - Bsamp') < 1e-10
chirality_pass = rot_diff_max < 1e-9 && boost_diff_min > 1e-3 &&
                 rot_is_unitary && boost_is_hermitian
results["chirality_rotation_vs_boost"] = Dict(
    "samples_each" => n_chi,
    "rotation_rep_diff_max" => rot_diff_max,        # ~0: L and R coincide on rotations
    "rotation_rep_diff_min" => rot_diff_min,
    "boost_rep_diff_min" => boost_diff_min,         # >0: L and R differ on boosts
    "boost_rep_diff_max" => boost_diff_max,
    "rotation_sample_unitary" => rot_is_unitary,
    "boost_sample_hermitian" => boost_is_hermitian,
    "chirality_split_measured" => chirality_pass,
    "interpretation" => "L=(M) and R=(M^dag)^{-1} COINCIDE under rotations (M unitary) " *
                        "and DIFFER under boosts (M Hermitian, (M^dag)^{-1}=M^{-1}!=M). " *
                        "The boost is the chirality-distinguisher.",
)

# =============================================================================
# 2b. STRUCTURAL INEQUIVALENCE: no fixed S with S M S^{-1} = (M^dag)^{-1} for all M.
#     Solve the linear intertwiner conditions S M = (M^dag)^{-1} S over a
#     generating set; the only common solution is S = 0 (=> no invertible S =>
#     the two 2-dim reps are genuinely inequivalent irreps).
#     Build the 4x4 linear map on vec(S) from L_M(S) = rep_R(M) S - S rep_L(M);
#     stack over generators; the joint nullspace must be {0}.
# =============================================================================
# vectorize: for A S B form, vec(A S B) = (B^T ⊗ A) vec(S)
kron_lhs(M) = kron(transpose(M), Matrix{ComplexF64}(I,2,2))         # vec(S M) = (M^T ⊗ I) vec(S)... careful below
# We want operator T_M(vec S) = vec( rep_R(M) S - S rep_L(M) ).
# vec(A S) = (I ⊗ A) vec(S) ;  vec(S B) = (B^T ⊗ I) vec(S).
T_of(M) = kron(I2, rep_R(M)) - kron(transpose(rep_L(M)), I2)
function intertwiner_nullspace_dim()
    rng = MersenneTwister(21)
    rows = Matrix{ComplexF64}(undef, 0, 4)
    # stack the intertwiner constraint for several independent group elements
    Ms = [rand_rot(rng), rand_boost(rng), rand_sl2c(rng), rand_sl2c(rng), rand_sl2c(rng)]
    for M in Ms
        rows = vcat(rows, T_of(M))
    end
    # nullspace dimension via SVD: count singular values ~ 0
    s = svdvals(rows)
    smax = maximum(s)
    nullity = count(x -> x < 1e-9 * max(smax, 1.0), s)
    # also the dimension of the column space we actually constrain is 4 (vec S in C^4)
    nullity, smax, minimum(s)
end
nullity_LR, sv_max, sv_min = intertwiner_nullspace_dim()
# control: the SAME machinery on M vs M (identical reps) must have nullity 4
# (every S commutes-as-intertwiner trivially? no: S M = M S has a >0 nullspace;
#  the honest control is L-vs-L i.e. rep_R replaced by rep_L: then S=I works,
#  nullity >= 1). We assert the L-vs-R joint nullity is 0 while L-vs-L is >=1.
function intertwiner_LL_nullity()
    rng = MersenneTwister(31)
    rows = Matrix{ComplexF64}(undef, 0, 4)
    Ms = [rand_rot(rng), rand_boost(rng), rand_sl2c(rng), rand_sl2c(rng), rand_sl2c(rng)]
    for M in Ms
        rows = vcat(rows, kron(I2, rep_L(M)) - kron(transpose(rep_L(M)), I2))
    end
    s = svdvals(rows)
    smax = maximum(s)
    count(x -> x < 1e-9 * max(smax, 1.0), s)
end
nullity_LL = intertwiner_LL_nullity()
inequivalence_pass = nullity_LR == 0 && nullity_LL >= 1
results["structural_inequivalence"] = Dict(
    "LR_intertwiner_nullspace_dim" => nullity_LR,   # 0 -> no S intertwines L and R
    "LL_intertwiner_nullspace_dim" => nullity_LL,   # >=1 -> control: L intertwines itself (S=I)
    "LR_singular_value_max" => sv_max,
    "LR_singular_value_min" => sv_min,
    "reps_inequivalent" => inequivalence_pass,
    "interpretation" => "Joint nullspace of S M = (M^dag)^{-1} S over a generating set is {0} " *
                        "(no invertible intertwiner) -> (1/2,0) and (0,1/2) are inequivalent irreps. " *
                        "Control L-vs-L has nullity>=1 (S=I works), so the test is not vacuous.",
)

# =============================================================================
# 3. DOUBLE COVER SL(2,C) -> SO(3,1): Lambda preserves eta, and is 2-to-1.
# =============================================================================
n_lam = 400
function check_lorentz(n_lam)
    rng = MersenneTwister(41)
    max_eta_err = 0.0
    max_det_err = 0.0
    max_2to1_err = 0.0
    max_recover_err = 0.0
    for _ in 1:n_lam
        M = rand_sl2c(rng)
        Λ = lorentz_Lambda(M)
        max_eta_err = max(max_eta_err, opnorm(transpose(Λ)*ETA*Λ - ETA))
        max_det_err = max(max_det_err, abs(det(Λ) - 1))     # proper (det +1) Lorentz
        # 2-to-1: M and -M give the SAME Lambda (since (-M)X(-M)^dag = M X M^dag)
        Λneg = lorentz_Lambda(-M)
        max_2to1_err = max(max_2to1_err, opnorm(Λ - Λneg))
        # covariance check: Lambda acting on a random 4-vector matches the bispinor map
        xr = randn(rng, 4)
        Xp = M * xvec_to_X(xr) * M'
        max_recover_err = max(max_recover_err, norm(X_to_xvec(Xp) - Λ*xr))
    end
    max_eta_err, max_det_err, max_2to1_err, max_recover_err
end
lam_eta_err, lam_det_err, lam_2to1_err, lam_cov_err = check_lorentz(n_lam)
# the spinor sign flip lives ONLY upstairs: a 2pi rotation gives M=-I but Lambda=I
M_2pi = sl2c([0.0, 0.0, 2π], zeros(3))      # 2pi rotation about z
spinor_2pi_is_minusI = opnorm(M_2pi + I2) < 1e-9
Λ_2pi = lorentz_Lambda(M_2pi)
lorentz_2pi_is_I = opnorm(Λ_2pi - Matrix{Float64}(I,4,4)) < 1e-9
double_cover_pass = lam_eta_err < 1e-9 && lam_det_err < 1e-9 &&
                    lam_2to1_err < 1e-12 && lam_cov_err < 1e-9 &&
                    spinor_2pi_is_minusI && lorentz_2pi_is_I
results["double_cover_SO31"] = Dict(
    "samples" => n_lam,
    "max_eta_preservation_err" => lam_eta_err,      # Lambda^T eta Lambda = eta
    "max_det_Lambda_minus_1" => lam_det_err,        # proper orthochronous (det +1)
    "max_2to1_err_M_vs_negM" => lam_2to1_err,       # 0: M and -M -> same Lambda
    "max_covariance_recover_err" => lam_cov_err,    # bispinor map = Lambda on 4-vectors
    "spinor_2pi_rotation_is_minus_I" => spinor_2pi_is_minusI,  # upstairs sign flip
    "lorentz_2pi_rotation_is_I" => lorentz_2pi_is_I,           # downstairs no flip
    "double_cover_measured" => double_cover_pass,
    "interpretation" => "x -> M X M^dag induces Lambda(M) in SO(3,1) (eta preserved, det +1). " *
                        "Lambda(M)=Lambda(-M) -> 2-to-1; the 2pi-rotation sign flip M=-I lives " *
                        "ONLY upstairs (Lambda=I downstairs).",
)

# =============================================================================
# 4. gamma5 / WEYL-BASIS connection.
#    S(M) = diag(M, (M^dag)^{-1}) is block-diagonal; gamma5 = diag(-I,+I).
#    - gamma5 commutes with S(M) (chirality is a good quantum number).
#    - P_L S(M) P_L block = M (the (1/2,0) rep); P_R S(M) P_R block = (M^dag)^{-1}.
#    - Restricted to ROTATIONS both blocks reduce to the SAME SU(2) element
#      (= the Euclidean Spin(3) already simulated). Under BOOSTS the blocks differ.
# =============================================================================
n_g5 = 400
function check_gamma5(n_g5)
    rng = MersenneTwister(51)
    max_g5_commute_err = 0.0
    max_block_L_err = 0.0
    max_block_R_err = 0.0
    max_rot_block_diff = 0.0      # rotations: L block == R block (both SU(2))
    min_boost_block_diff = Inf    # boosts: L block != R block
    rot_block_unitary = true
    for _ in 1:n_g5
        M = rand_sl2c(rng)
        S = S_dirac(M)
        max_g5_commute_err = max(max_g5_commute_err, opnorm(GAMMA5*S - S*GAMMA5))
        # extract blocks
        L_block = S[1:2, 1:2]; R_block = S[3:4, 3:4]
        max_block_L_err = max(max_block_L_err, opnorm(L_block - rep_L(M)))
        max_block_R_err = max(max_block_R_err, opnorm(R_block - rep_R(M)))
    end
    # rotations: both Weyl blocks are the SAME SU(2)
    rngr = MersenneTwister(52)
    for _ in 1:n_g5
        U = rand_rot(rngr)
        S = S_dirac(U)
        L_block = S[1:2,1:2]; R_block = S[3:4,3:4]
        max_rot_block_diff = max(max_rot_block_diff, opnorm(L_block - R_block))
        rot_block_unitary &= opnorm(L_block'*L_block - I2) < 1e-9
    end
    # boosts: the two Weyl blocks differ
    rngb = MersenneTwister(53)
    for _ in 1:n_g5
        B = rand_boost(rngb)
        S = S_dirac(B)
        L_block = S[1:2,1:2]; R_block = S[3:4,3:4]
        min_boost_block_diff = min(min_boost_block_diff, opnorm(L_block - R_block))
    end
    max_g5_commute_err, max_block_L_err, max_block_R_err,
    max_rot_block_diff, min_boost_block_diff, rot_block_unitary
end
g5_commute_err, blkL_err, blkR_err, rot_blk_diff, boost_blk_diff, rot_blk_unit =
    check_gamma5(n_g5)
gamma5_pass = g5_commute_err < 1e-9 && blkL_err < 1e-12 && blkR_err < 1e-12 &&
              rot_blk_diff < 1e-9 && boost_blk_diff > 1e-3 && rot_blk_unit
# gamma5 itself: gamma5^2 = I, P_L+P_R = I, P_L P_R = 0 (basis sanity, measured)
g5_sq_ok = opnorm(GAMMA5*GAMMA5 - I4) < 1e-12
proj_complete = opnorm(P_L + P_R - I4) < 1e-12
proj_orth = opnorm(P_L*P_R) < 1e-12
results["gamma5_weyl_connection"] = Dict(
    "samples" => n_g5,
    "gamma5_sq_is_I" => g5_sq_ok,
    "projectors_complete_PL_plus_PR_eq_I" => proj_complete,
    "projectors_orthogonal_PL_PR_eq_0" => proj_orth,
    "max_gamma5_commutes_with_S_err" => g5_commute_err,   # [gamma5, S(M)] = 0
    "max_L_block_minus_M_err" => blkL_err,                # P_L block = M
    "max_R_block_minus_Mdaginv_err" => blkR_err,          # P_R block = (M^dag)^{-1}
    "rotation_L_block_eq_R_block_diff" => rot_blk_diff,   # ~0: both blocks one SU(2)
    "boost_L_block_neq_R_block_min_diff" => boost_blk_diff, # >0: boost splits them
    "rotation_blocks_unitary" => rot_blk_unit,
    "gamma5_connection_measured" => gamma5_pass,
    "interpretation" => "S(M)=diag(M,(M^dag)^{-1}); gamma5=diag(-I,+I) commutes with S(M), " *
                        "splitting Dirac into the two Weyl reps. Restricted to rotations both " *
                        "blocks are the SAME SU(2) (Euclidean Spin(3)); boosts split them.",
)

# =============================================================================
# KILL-CONTROL (a): rotation-coincide vs boost-differ.  (Already measured in 2a;
#   restate as an explicit fired/null control.)
# =============================================================================
killA_pass = rot_diff_max < 1e-9 && boost_diff_min > 1e-3
results["killcontrol_a_rotation_vs_boost"] = Dict(
    "rotation_reps_coincide" => rot_diff_max < 1e-9,
    "boost_reps_differ" => boost_diff_min > 1e-3,
    "rotation_rep_diff_max" => rot_diff_max,
    "boost_rep_diff_min" => boost_diff_min,
    "killcontrol_a_fired" => killA_pass,
    "verdict" => killA_pass ?
        "KILL A FIRED (chirality invisible to rotations, visible to boosts)" :
        "KILL A FAILED (chirality not boost-distinguished -> vacuous)",
)

# =============================================================================
# KILL-CONTROL (b): WRONG right-rep must FAIL.
#   (i) epsilon-pairing: the genuine SL(2,C) invariant is M^T eps M = eps. The
#       correct dual rep (M^dag)^{-1} is the one consistent with raising/lowering
#       by epsilon: (M^dag)^{-1} = eps^* M^* eps^{-1}* ... we test the cleaner,
#       fully MEASURED statement that ties L and R together via epsilon:
#         the right rep must equal  eps (M^*) eps^{-1}   (= (M^dag)^{-1} for SL(2,C)).
#       The genuine rep satisfies this; M^dag and M^T do NOT (over boosts).
#   (ii) SO(3,1) covariance of the Dirac rep with the WRONG R block breaks the
#        block structure: gamma5 still commutes with diag(M, wrongR) only if
#        wrongR is some 2x2, but the rep is no longer the conjugate rep, so the
#        epsilon link M_L <-> M_R is broken. We MEASURE the epsilon link error.
# =============================================================================
n_kb = 400
function check_killB(n_kb)
    rng = MersenneTwister(61)
    epsinv = inv(EPS)
    # epsilon link error:  rep_R(M)  vs  eps * conj(M) * eps^{-1}
    err_genuine = 0.0
    err_wrong_dagger = 0.0
    err_wrong_transpose = 0.0
    # also: M^T eps M = eps must hold (SL(2,C) preserves the symplectic form)
    max_symplectic_err = 0.0
    for _ in 1:n_kb
        M = rand_sl2c(rng)
        link = EPS * conj(M) * epsinv          # the epsilon-conjugate of M
        err_genuine = max(err_genuine, opnorm(rep_R(M) - link))
        err_wrong_dagger = max(err_wrong_dagger, opnorm(rep_R_wrong_dagger(M) - link))
        err_wrong_transpose = max(err_wrong_transpose, opnorm(rep_R_wrong_transpose(M) - link))
        max_symplectic_err = max(max_symplectic_err, opnorm(transpose(M)*EPS*M - EPS))
    end
    err_genuine, err_wrong_dagger, err_wrong_transpose, max_symplectic_err
end
errG, errWD, errWT, symp_err = check_killB(n_kb)
# kill fires iff: genuine R matches the epsilon link (~0), BOTH wrong duals do NOT,
# and the symplectic form is preserved (so epsilon is genuinely the invariant).
killB_pass = errG < 1e-9 && errWD > 1e-3 && errWT > 1e-3 && symp_err < 1e-9
results["killcontrol_b_wrong_rep"] = Dict(
    "samples" => n_kb,
    "genuine_R_minus_epsilon_link_err" => errG,         # ~0: (M^dag)^{-1} = eps conj(M) eps^{-1}
    "wrong_dagger_R_minus_link_err" => errWD,           # >0: M^dag breaks it
    "wrong_transpose_R_minus_link_err" => errWT,        # >0: M^T breaks it
    "max_symplectic_MT_eps_M_err" => symp_err,          # ~0: M^T eps M = eps (eps is invariant)
    "killcontrol_b_fired" => killB_pass,
    "verdict" => killB_pass ?
        "KILL B FIRED (genuine (M^dag)^{-1} matches epsilon link; M^dag and M^T fail)" :
        "KILL B FAILED (wrong rep not distinguished -> pairing test vacuous)",
    "interpretation" => "(M^dag)^{-1} is the epsilon-conjugate rep eps conj(M) eps^{-1}, " *
                        "consistent with the invariant symplectic form M^T eps M = eps. " *
                        "M^dag and M^T do NOT match the link (fail over boosts).",
)

# =============================================================================
# HONEST OVERALL STATUS
# =============================================================================
checks = Dict(
    "sl2c_det_eq_1"               => results["sl2c_det"]["pass"],
    "chirality_rotation_vs_boost" => chirality_pass,
    "reps_inequivalent"           => inequivalence_pass,
    "double_cover_SO31_eta_2to1"  => double_cover_pass,
    "gamma5_weyl_connection"      => gamma5_pass,
    "gamma5_basis_sanity"         => g5_sq_ok && proj_complete && proj_orth,
    "killcontrol_a_fired"         => killA_pass,
    "killcontrol_b_fired"         => killB_pass,
)
all_pass = all(values(checks))
results["checks"] = checks
results["summary"] = Dict(
    "n_checks" => length(checks),
    "n_pass" => count(values(checks)),
    "all_pass" => all_pass,
    "ladder_status" => all_pass ? "passes" : "partial",
    "forced_standard_rep_theory" => "SL(2,C)=Spin(1,3) double cover; (1/2,0)/(0,1/2) reps; " *
                                    "eta preservation; epsilon-invariance",
    "novel" => "none (standard relativistic representation theory)",
    "headline" => "Spin(1,3) ~ SL(2,C): the two fundamental reps L=(M), R=(M^dag)^{-1} are " *
                  "MEASURABLY inequivalent (only S=0 intertwines them); they COINCIDE under " *
                  "rotations (M unitary) and DIFFER under boosts (the boost is the chirality- " *
                  "distinguisher); x->M X M^dag is a 2-to-1 cover onto SO(3,1) preserving eta; " *
                  "and gamma5=diag(-I,+I) splits the Dirac rep into exactly these two Weyl blocks.",
)

# ---- emit ----
open(joinpath(@__DIR__, "sl2c_spin13_chiral_gstructure_results.json"), "w") do io
    JSON.print(io, results, 2)
end

println("="^74)
println("sl2c_spin13_chiral_gstructure  —  checks: ",
        count(values(checks)), "/", length(checks))
println("="^74)
println("SL(2,C) det:   max|det M - 1| = ", round(max_det_err, sigdigits=3),
        "   max|tr(gen)| = ", round(max_tr_gen, sigdigits=3),
        "   (det exp(traceless)=1)")
println("CHIRALITY:     rotation rep diff max = ", round(rot_diff_max, sigdigits=3),
        "  (expect ~0; L=R on rotations)")
println("               boost    rep diff min = ", round(boost_diff_min, sigdigits=3),
        "  (expect >0; L!=R on boosts)")
println("INEQUIVALENT:  L-vs-R joint nullspace dim = ", nullity_LR,
        " (expect 0)   L-vs-L control = ", nullity_LL, " (expect >=1)")
println("DOUBLE COVER:  max|Lambda^T eta Lambda - eta| = ", round(lam_eta_err, sigdigits=3),
        "   max|det Lambda - 1| = ", round(lam_det_err, sigdigits=3))
println("               max|Lambda(M)-Lambda(-M)| = ", round(lam_2to1_err, sigdigits=3),
        " (2-to-1)   spinor(2pi)=-I: ", spinor_2pi_is_minusI,
        "  Lambda(2pi)=I: ", lorentz_2pi_is_I)
println("GAMMA5/WEYL:   max|[gamma5,S(M)]| = ", round(g5_commute_err, sigdigits=3),
        "   L block-M err = ", round(blkL_err, sigdigits=3),
        "   R block-(M^dag)^-1 err = ", round(blkR_err, sigdigits=3))
println("               rotation L-block=R-block diff = ", round(rot_blk_diff, sigdigits=3),
        " (~0)   boost L!=R min diff = ", round(boost_blk_diff, sigdigits=3), " (>0)")
println("KILL A:        ", results["killcontrol_a_rotation_vs_boost"]["verdict"])
println("KILL B:        genuine link err = ", round(errG, sigdigits=3),
        "  wrong-dag err = ", round(errWD, sigdigits=3),
        "  wrong-T err = ", round(errWT, sigdigits=3),
        "  symplectic err = ", round(symp_err, sigdigits=3))
println("               ", results["killcontrol_b_wrong_rep"]["verdict"])
println("-"^74)
println("ALL_PASS = ", all_pass, "   ladder = ", results["summary"]["ladder_status"])
