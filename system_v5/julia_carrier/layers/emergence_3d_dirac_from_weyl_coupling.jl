# ======================================================================
# emergence_3d_dirac_from_weyl_coupling.jl
#   classification: PoC   ·   promotion_allowed: false
#   tools (all non-numpy): LinearAlgebra, Random, JSON.  NO Z3 (see note).
# ----------------------------------------------------------------------
# EMERGENCE TEST (grounded by a grok+gemini council):
#   The 3D Dirac spinor EMERGES only when LEFT and RIGHT Weyl spinors on
#   adjacent nested-tori leaves are COUPLED. It is NOT present in the
#   isolated (decoupled) chiral leaves.
#
# RADIAL DIRAC DECOMPOSITION (the forced math anchor):
#   On S^3 the radial Dirac operator splits as
#         D_S3 = gamma^theta (d/dtheta + H/2) + D_T2(theta).
#   The inter-leaf piece gamma^theta d/dtheta is what links one leaf to the
#   adjacent leaf. In the chiral (Weyl) basis gamma^theta is OFF-DIAGONAL
#   between the upper (L) and lower (R) 2-blocks, so the radial hop combines
#   a 2-component L Weyl on one leaf with a 2-component R Weyl on the
#   adjacent leaf into a 4-component Dirac spinor.
#
# CONSTRUCTION (1D chain of leaves in theta):
#   - Each leaf carries a 2-component WEYL spinor with a definite chirality
#     (gamma5 eigenvalue): leaf j even -> LEFT (chi=-1), j odd -> RIGHT (+1).
#   - On-leaf Weyl Hamiltonian (2-component, chiral):  h = chi_j * (k . sigma).
#     A single Weyl block is GAPLESS (eigs +-|k|) and has NO mass term.
#   - Inter-leaf coupling C = gamma^theta * t links adjacent leaves; in the
#     chiral basis this is the off-diagonal L<->R hop = a Dirac mass channel.
#
# EMERGENT OBSERVABLES (exist ONLY when L and R are coupled):
#   (E1) SPECTRAL GAP.  Decoupled chiral leaves are gapless (Weyl cones touch
#        zero). Coupling L<->R gaps the spectrum: eigs -> +-sqrt(k^2 + m^2),
#        m = t. Gap = 2|m| > 0 ONLY with coupling.  MEASURED from the
#        Hermitian chain Hamiltonian's eigenvalues.
#   (E2) DIRAC MASS BILINEAR  mbar = psi^dag gamma0 psi.  In the chiral basis
#        gamma0 is purely off-diagonal (couples L and R), so for ANY pure-
#        chirality (single-leaf) state mbar = 0 exactly. A nonzero mbar
#        REQUIRES a state with BOTH L and R weight -- which only the coupled
#        ground state has.  MEASURED on the actual ground state.
#
# KILL-CONTROL (the emergence test):
#   t = 0 (decoupled): purely WEYL -> gap = 0, ground-state mbar = 0, the
#        gamma0 expectation in any single-leaf state is structurally 0.
#   t != 0 (coupled):  Dirac structure EMERGES -> gap > 0, ground-state
#        mbar != 0.  The emergent structure VANISHES when the coupling is
#        removed and APPEARS when it is restored.
#
# WHY NO Z3:  this codebase's recurring weakness is decorative Z3 wired to
#   tautologies. The emergence claim here is a SPECTRAL fact (a gap opens /
#   closes as the coupling is toggled) and a bilinear that is structurally
#   zero for single-chirality states. The honest, load-bearing evidence is
#   the MEASURED eigenvalue gap and bilinear with a real toggle, not an
#   exact-integer SMT clause. So Z3 is OMITTED rather than added decoratively.
#
# HONESTY LEDGER:
#   FORCED      : the radial Dirac decomposition D_S3 = gamma^theta(d_theta+H/2)
#                 + D_T2; that a single 2-component Weyl block has no mass term
#                 (gamma0 off-diagonal in chiral basis); gap = +-sqrt(k^2+m^2).
#   INTERPRETIVE: calling the 1D theta-chain "the S^3 radial direction" is a
#                 model identification, not a measured fact. We flag it.
# ======================================================================

using LinearAlgebra
using Random
using JSON

results = Dict{String,Any}()
results["object"]            = "emergence_3d_dirac_from_LR_weyl_leaf_coupling"
results["classification"]    = "PoC"
results["promotion_allowed"] = false
results["tools"]             = ["LinearAlgebra", "Random", "JSON"]
results["z3_omitted_reason"] = "Emergence is a measured spectral gap + structurally-zero " *
    "chiral bilinear under a real coupling toggle; an exact-integer SMT clause would be " *
    "decorative here. Z3 deliberately omitted (codebase's documented decorative-Z3 weakness)."

# ======================================================================
# 0. Chiral-basis gamma matrices (carrier: LinearAlgebra), 2-comp blocks
#    Weyl (chiral) basis:  gamma0 = [[0 I];[I 0]],  gamma^k = [[0 s_k];[-s_k 0]],
#    gamma5 = diag(-I, +I)  (upper block = LEFT chirality -1, lower = RIGHT +1).
# ======================================================================
s0 = ComplexF64[1 0; 0 1]
sx = ComplexF64[0 1; 1 0]
sy = ComplexF64[0 -im; im 0]
sz = ComplexF64[1 0; 0 -1]
Z2 = zeros(ComplexF64, 2, 2)
sigma = [sx, sy, sz]

g0 = [Z2 s0; s0 Z2]
g1 = [Z2 sx; -sx Z2]
g2 = [Z2 sy; -sy Z2]
g3 = [Z2 sz; -sz Z2]
gammas = [g0, g1, g2, g3]
I4 = Matrix{ComplexF64}(I, 4, 4)
metric = [1.0, -1.0, -1.0, -1.0]
gamma5 = im * g0 * g1 * g2 * g3                       # diag(-1,-1,+1,+1)

# gamma^theta: the RADIAL gamma. In the chiral split it must be the off-diagonal
# L<->R operator (this is what makes the radial hop a Dirac mass channel). The
# canonical radial gamma is gamma0 in the chiral basis (off-diagonal block I).
gamma_theta = g0

# ---- MEASURE the algebra so the carrier is genuine, not asserted -----
max_clifford_residual = 0.0
for mu in 1:4, nu in 1:4
    anti = gammas[mu]*gammas[nu] + gammas[nu]*gammas[mu]
    expected = (mu == nu ? 2*metric[mu]*I4 : zeros(ComplexF64,4,4))
    global max_clifford_residual = max(max_clifford_residual, maximum(abs.(anti .- expected)))
end
clifford_ok = max_clifford_residual < 1e-12
g5_diag = real.(diag(gamma5))
weyl_split_ok = isapprox(gamma5, Diagonal(g5_diag); atol=1e-12) &&
                sort(round.(Int, g5_diag)) == [-1,-1,1,1]
# gamma_theta off-diagonal between L (rows 1:2) and R (rows 3:4)?
gtheta_LL = maximum(abs.(gamma_theta[1:2,1:2]))
gtheta_RR = maximum(abs.(gamma_theta[3:4,3:4]))
gtheta_LR = maximum(abs.(gamma_theta[1:2,3:4]))
gamma_theta_couples_LR = (gtheta_LL < 1e-12) && (gtheta_RR < 1e-12) && (gtheta_LR > 0.5)

results["carrier"] = Dict(
    "basis" => "chiral/Weyl",
    "clifford_algebra_ok" => clifford_ok,
    "max_clifford_residual" => max_clifford_residual,
    "gamma5_diag" => g5_diag,
    "weyl_chirality_split_ok" => weyl_split_ok,
    "gamma_theta_is_gamma0_offdiagonal" => gamma_theta_couples_LR,
    "gamma_theta_LL_block_norm" => gtheta_LL,
    "gamma_theta_RR_block_norm" => gtheta_RR,
    "gamma_theta_LR_block_norm" => gtheta_LR,
)
println("[0] Carrier (chiral-basis gammas, LinearAlgebra):")
println("    Clifford {g,g}=2eta ok        : ", clifford_ok, "  (resid ", max_clifford_residual, ")")
println("    gamma5 = diag", g5_diag, "  Weyl L/R split: ", weyl_split_ok)
println("    gamma^theta off-diag (L<->R)  : ", gamma_theta_couples_LR,
        "  (LL=", gtheta_LL, " RR=", gtheta_RR, " LR=", gtheta_LR, ")")

# ======================================================================
# 1. ON-LEAF WEYL MODE is genuinely chiral (gamma5 eigenvalue, no mass term)
#    A 2-component Weyl spinor lives in ONE chirality block. We verify:
#    (a) the L block has gamma5 = -1, the R block has gamma5 = +1 (chiral);
#    (b) the on-leaf Weyl Hamiltonian h = chi*(k.sigma) has NO mass term:
#        a 2-component h is traceless and gapless (eigs +-|k|, touches 0).
# ======================================================================
# embed a 2-component Weyl spinor of chirality chi into the 4-spinor
embed_L(w2) = ComplexF64[w2[1], w2[2], 0, 0]          # upper block = LEFT (gamma5=-1)
embed_R(w2) = ComplexF64[0, 0, w2[1], w2[2]]          # lower block = RIGHT (gamma5=+1)

q5(psi4) = real(psi4' * gamma5 * psi4)                # chiral charge

Random.seed!(20260601)
maxabs_chi_L = 0.0; maxabs_chi_R = 0.0
for _ in 1:500
    w = randn(ComplexF64, 2); w ./= norm(w)
    global maxabs_chi_L = max(maxabs_chi_L, abs(q5(embed_L(w)) - (-1.0)))
    global maxabs_chi_R = max(maxabs_chi_R, abs(q5(embed_R(w)) - (+1.0)))
end
onleaf_L_is_left  = maxabs_chi_L < 1e-12
onleaf_R_is_right = maxabs_chi_R < 1e-12

# on-leaf 2-component Weyl Hamiltonian gaplessness (single Weyl = no mass)
weyl_kvec = [0.7, -0.4, 0.3]
hW(chi, k) = chi * (k[1]*sx + k[2]*sy + k[3]*sz)      # 2x2 Weyl Hamiltonian
eW_L = sort(real.(eigvals(hW(-1, weyl_kvec))))
eW_R = sort(real.(eigvals(hW(+1, weyl_kvec))))
kabs = norm(weyl_kvec)
weyl_gapless = abs((eW_L[2]-eW_L[1]) - 2kabs) < 1e-10 &&   # eigs are +-|k|
               abs((eW_R[2]-eW_R[1]) - 2kabs) < 1e-10
weyl_traceless = abs(tr(hW(-1, weyl_kvec))) < 1e-12        # no mass term on the diagonal

results["on_leaf_weyl"] = Dict(
    "even_leaf_is_LEFT_chirality_-1"  => onleaf_L_is_left,
    "odd_leaf_is_RIGHT_chirality_+1"  => onleaf_R_is_right,
    "max_chiral_charge_dev_L" => maxabs_chi_L,
    "max_chiral_charge_dev_R" => maxabs_chi_R,
    "weyl_eigs_pm_abs_k_gapless" => weyl_gapless,
    "weyl_hamiltonian_traceless_no_mass" => weyl_traceless,
    "weyl_kabs" => kabs,
)
println("\n[1] On-leaf modes are genuinely Weyl (chiral, no mass term):")
println("    even leaf gamma5=-1 (LEFT)  : ", onleaf_L_is_left, "  (dev ", maxabs_chi_L, ")")
println("    odd  leaf gamma5=+1 (RIGHT) : ", onleaf_R_is_right, "  (dev ", maxabs_chi_R, ")")
println("    2-comp Weyl gapless (+-|k|) : ", weyl_gapless, "  (|k|=", round(kabs,digits=4), ")")
println("    Weyl Hamiltonian traceless  : ", weyl_traceless, "  (single Weyl has NO mass term)")

# ======================================================================
# 2. BUILD THE theta-CHAIN HAMILTONIAN and MEASURE the emergent gap.
#    L leaves on even sites carry a LEFT 2-spinor (upper block), R leaves on
#    odd sites carry a RIGHT 2-spinor (lower block). The inter-leaf radial hop
#    C = (t/2) * gamma^theta links adjacent leaves. We work in a fixed
#    transverse momentum k (the D_T2(theta) sector) to read the gap cleanly.
#
#    Two-leaf primitive (one L leaf + one adjacent R leaf) is exactly the
#    4-component Dirac block:
#         H2 = [ h_L            m_coup ;
#                m_coup^dag     h_R    ]
#    with on-leaf chiral pieces h_L = -(k.sigma), h_R = +(k.sigma) embedded in
#    their blocks, and m_coup = t * (off-diagonal gamma^theta block) = t*I.
#    Decoupled (t=0): block-diagonal Weyl, gapless. Coupled: Dirac, gapped.
# ======================================================================
"Two-leaf (L<->R) Dirac block at transverse momentum kvec, coupling t."
function two_leaf_H(kvec, t)
    ksig = kvec[1]*sx + kvec[2]*sy + kvec[3]*sz        # 2x2
    hL = -ksig                                          # LEFT Weyl block (chi=-1)
    hR = +ksig                                          # RIGHT Weyl block (chi=+1)
    mcoup = t * s0                                       # radial hop = off-diag gamma^theta block
    H = zeros(ComplexF64, 4, 4)
    H[1:2,1:2] = hL
    H[3:4,3:4] = hR
    H[1:2,3:4] = mcoup
    H[3:4,1:2] = mcoup'
    return H
end

kvec = [0.6, 0.2, -0.5]
ka   = norm(kvec)
tcoup = 0.9                          # the Dirac mass scale m = t
k_node = [0.0, 0.0, 0.0]             # the Weyl NODE: where the gap opens from zero

H_dec = two_leaf_H(kvec, 0.0)        # DECOUPLED: pure Weyl
H_cpl = two_leaf_H(kvec, tcoup)      # COUPLED: Dirac emerges

hermitian_ok = maximum(abs.(H_cpl - H_cpl')) < 1e-12 && maximum(abs.(H_dec - H_dec')) < 1e-12
ev_dec = sort(real.(eigvals(H_dec)))
ev_cpl = sort(real.(eigvals(H_cpl)))

# emergent observable E1: the spectral gap (smallest |E_+ - E_-| across zero)
# the gap of a Dirac block is 2*min positive eigenvalue magnitude; for a
# particle-hole-symmetric spectrum it's eigvals[3]-eigvals[2].
gap_dec = ev_dec[3] - ev_dec[2]
gap_cpl = ev_cpl[3] - ev_cpl[2]

# analytic anchors (FORCED): decoupled Weyl eigs = {-|k|,-|k|,+|k|,+|k|} (gapless);
# coupled Dirac eigs = +-sqrt(|k|^2 + t^2) (gapped, gap = 2|t| at k=0, here 2*?)
dirac_E = sqrt(ka^2 + tcoup^2)
ev_cpl_matches_dirac = isapprox(ev_cpl, sort([-dirac_E,-dirac_E,dirac_E,dirac_E]); atol=1e-8)
ev_dec_matches_weyl  = isapprox(ev_dec, sort([-ka,-ka,ka,ka]); atol=1e-8)

# --- THE BAND-TOUCHING POINT k=0 (the Weyl NODE): this is where "gap opens
#     from zero" is the physically true statement. At fixed k!=0 the Weyl
#     spectrum is already +-|k| (gapped by 2|k|); only AT THE NODE k=0 is the
#     decoupled Weyl system gapless (all eigs 0), and the coupling opens a gap
#     2|t| = the Dirac mass gap. We measure the gap here for the kill-control.
H_node_dec = two_leaf_H([0.0,0.0,0.0], 0.0)
H_node_cpl = two_leaf_H([0.0,0.0,0.0], tcoup)
ev_node_dec = sort(real.(eigvals(H_node_dec)))
ev_node_cpl = sort(real.(eigvals(H_node_cpl)))
node_gap_dec = ev_node_dec[3] - ev_node_dec[2]      # want 0 (gapless Weyl node)
node_gap_cpl = ev_node_cpl[3] - ev_node_cpl[2]      # want 2|t| (Dirac mass gap)
node_gap_matches_2t = isapprox(node_gap_cpl, 2*abs(tcoup); atol=1e-8)

results["two_leaf_spectrum"] = Dict(
    "kabs" => ka,
    "t_coupling" => tcoup,
    "hermitian_ok" => hermitian_ok,
    "eigs_decoupled_fixed_k" => ev_dec,
    "eigs_coupled_fixed_k" => ev_cpl,
    "gap_decoupled_fixed_k" => gap_dec,
    "gap_coupled_fixed_k" => gap_cpl,
    "decoupled_matches_gapless_weyl_pm_k" => ev_dec_matches_weyl,
    "coupled_matches_dirac_pm_sqrt_k2_t2" => ev_cpl_matches_dirac,
    "dirac_energy_sqrt_k2_t2" => dirac_E,
    "node_gap_decoupled_k0" => node_gap_dec,
    "node_gap_coupled_k0" => node_gap_cpl,
    "node_gap_coupled_equals_2t" => node_gap_matches_2t,
)
println("\n[2] Two-leaf (L<->R) spectrum  [k=", kvec, ", t=", tcoup, "]:")
println("    Hermitian Hamiltonian       : ", hermitian_ok)
println("    DECOUPLED eigs (Weyl)       : ", round.(ev_dec, digits=5), "  gap=", round(gap_dec,digits=6))
println("    COUPLED   eigs (Dirac)      : ", round.(ev_cpl, digits=5), "  gap=", round(gap_cpl,digits=6))
println("    decoupled == +-|k| (fixed k): ", ev_dec_matches_weyl, "  (NOTE: gapped by 2|k| at k!=0)")
println("    coupled   == +-sqrt(k^2+t^2): ", ev_cpl_matches_dirac, "  (E=", round(dirac_E,digits=5), ")")
println("    AT THE WEYL NODE k=0:  decoupled gap=", round(node_gap_dec,digits=6),
        " (gapless)  ->  coupled gap=", round(node_gap_cpl,digits=6), " = 2|t|: ", node_gap_matches_2t)

# ======================================================================
# 3. FULL theta-CHAIN (N leaves) -- the radial direction as a 1D lattice.
#    Sites alternate L,R,L,R,...; radial hop t couples site j to j+1 via the
#    off-diagonal gamma^theta block. We build the (2N)x(2N) Hermitian chain
#    and read the gap at the band center as a function of the coupling.
# ======================================================================
"N-leaf radial Dirac chain. chi[j] in {-1,+1}; on-leaf h_j = chi_j*(k.sigma);
 radial hop between adjacent leaves = t * (2x2 identity, the gamma^theta block)."
function chain_H(kvec, t, N)
    ksig = kvec[1]*sx + kvec[2]*sy + kvec[3]*sz
    H = zeros(ComplexF64, 2N, 2N)
    for j in 1:N
        chi = isodd(j) ? -1.0 : +1.0          # leaf 1 LEFT, leaf 2 RIGHT, ...
        blk = (2j-1):(2j)
        H[blk, blk] = chi * ksig
    end
    for j in 1:N-1
        a = (2j-1):(2j); b = (2j+1):(2j+2)
        H[a, b] = t * s0                       # radial hop leaf j -> j+1
        H[b, a] = (t * s0)'
    end
    return H
end

Nleaf = 8
center = Nleaf                                  # 2N eigs; indices N and N+1 straddle 0
# at fixed working k (informational; gapped by ~2|k| even decoupled)
Hc_dec = chain_H(kvec, 0.0, Nleaf)
Hc_cpl = chain_H(kvec, tcoup, Nleaf)
chain_herm_ok = maximum(abs.(Hc_cpl - Hc_cpl')) < 1e-12
evc_dec = sort(real.(eigvals(Hc_dec)))
evc_cpl = sort(real.(eigvals(Hc_cpl)))
chain_gap_dec = evc_dec[center+1] - evc_dec[center]
chain_gap_cpl = evc_cpl[center+1] - evc_cpl[center]
# AT THE WEYL NODE k=0: chain is gapless when decoupled, gaps when coupled
Hcn_dec = chain_H(k_node, 0.0, Nleaf)
Hcn_cpl = chain_H(k_node, tcoup, Nleaf)
evcn_dec = sort(real.(eigvals(Hcn_dec)))
evcn_cpl = sort(real.(eigvals(Hcn_cpl)))
chain_node_gap_dec = evcn_dec[center+1] - evcn_dec[center]
chain_node_gap_cpl = evcn_cpl[center+1] - evcn_cpl[center]

results["full_chain"] = Dict(
    "N_leaves" => Nleaf,
    "hermitian_ok" => chain_herm_ok,
    "central_gap_decoupled_fixed_k" => chain_gap_dec,
    "central_gap_coupled_fixed_k" => chain_gap_cpl,
    "central_node_gap_decoupled_k0" => chain_node_gap_dec,
    "central_node_gap_coupled_k0" => chain_node_gap_cpl,
    "min_abs_eig_decoupled" => minimum(abs.(evc_dec)),
    "min_abs_eig_coupled" => minimum(abs.(evc_cpl)),
)
println("\n[3] Full ", Nleaf, "-leaf radial chain:")
println("    central node-gap k=0 DECOUPLED (Weyl): ", round(chain_node_gap_dec, digits=8), " (gapless)")
println("    central node-gap k=0 COUPLED  (Dirac): ", round(chain_node_gap_cpl, digits=8), " (gap opens)")

# ======================================================================
# 4. EMERGENT OBSERVABLE E2: Dirac mass bilinear  mbar = psi^dag gamma0 psi.
#    In the chiral basis gamma0 = gamma^theta couples L and R, so:
#      - for ANY pure-chirality (single-leaf) state, mbar = 0 EXACTLY;
#      - the COUPLED ground state has both L and R weight -> mbar != 0.
#    We MEASURE mbar on (a) pure-L, pure-R single-leaf states (must be 0),
#    and (b) the actual two-leaf ground states, decoupled vs coupled.
# ======================================================================
mbar(psi4) = real(psi4' * g0 * psi4)            # = psi^dag gamma0 psi (the Dirac scalar)

# (a) structural-zero check: pure chirality -> mbar = 0
maxabs_mbar_pure = 0.0
for _ in 1:500
    w = randn(ComplexF64, 2); w ./= norm(w)
    global maxabs_mbar_pure = max(maxabs_mbar_pure, abs(mbar(embed_L(w))), abs(mbar(embed_R(w))))
end
pure_chirality_mbar_zero = maxabs_mbar_pure < 1e-12

# (b) ground-state mbar: decoupled vs coupled
gs(H) = (F = eigen(Hermitian(H)); v = F.vectors[:, argmin(real.(F.values))]; v ./ norm(v))
psi_gs_dec = gs(H_dec)
psi_gs_cpl = gs(H_cpl)
mbar_gs_dec = mbar(psi_gs_dec)
mbar_gs_cpl = mbar(psi_gs_cpl)
# how much L/R mixing does each ground state carry?
LR_weight(psi4) = (normL = norm(psi4[1:2]); normR = norm(psi4[3:4]); (normL, normR))
wL_dec, wR_dec = LR_weight(psi_gs_dec)
wL_cpl, wR_cpl = LR_weight(psi_gs_cpl)

results["dirac_mass_bilinear"] = Dict(
    "pure_chirality_mbar_is_zero" => pure_chirality_mbar_zero,
    "max_abs_mbar_pure_single_leaf" => maxabs_mbar_pure,
    "mbar_ground_state_decoupled" => mbar_gs_dec,
    "mbar_ground_state_coupled" => mbar_gs_cpl,
    "ground_state_LR_weights_decoupled" => [wL_dec, wR_dec],
    "ground_state_LR_weights_coupled" => [wL_cpl, wR_cpl],
)
println("\n[4] Dirac mass bilinear  mbar = psi^dag gamma0 psi:")
println("    pure-chirality single-leaf mbar = 0 (structural): ", pure_chirality_mbar_zero,
        "  (max |mbar| ", maxabs_mbar_pure, ")")
println("    ground-state mbar  DECOUPLED: ", round(mbar_gs_dec, digits=8),
        "   (L,R weights ", round.([wL_dec,wR_dec],digits=4), ")")
println("    ground-state mbar  COUPLED  : ", round(mbar_gs_cpl, digits=8),
        "   (L,R weights ", round.([wL_cpl,wR_cpl],digits=4), ")")

# ======================================================================
# 5. KILL-CONTROL (the emergence test): sweep the coupling t from 0 up and
#    confirm BOTH emergent observables are ZERO at t=0 and grow with t.
#    Emergence fires iff: node-gap(t=0)=0 AND node-gap(t>0)>0, mbar_gs(t=0)=0
#    AND mbar_gs(t>0) != 0, both monotone in t.
#
#    IMPORTANT (honest): the GAP is measured AT THE WEYL NODE k=0. At fixed
#    k!=0 the decoupled Weyl spectrum is already +-|k| (gapped by 2|k|), so
#    "gap opens from zero" is only true at the node. The Dirac MASS BILINEAR
#    mbar, by contrast, is structurally 0 at t=0 for ANY k (single-chirality
#    ground state) and turns on only with L<->R coupling -- so it is the
#    momentum-independent emergence witness. We report both.
# ======================================================================
ts = [0.0, 0.1, 0.3, 0.6, 0.9, 1.4]
sweep = Dict{String,Any}[]
node_gaps = Float64[]; mbars = Float64[]
for t in ts
    Hn = two_leaf_H(k_node, t)               # gap measured at the node
    evn = sort(real.(eigvals(Hn)))
    gn  = evn[3] - evn[2]
    Hk = two_leaf_H(kvec, t)                 # mass bilinear measured at the working k
    mb = mbar(gs(Hk))
    push!(node_gaps, gn); push!(mbars, abs(mb))
    push!(sweep, Dict("t"=>t, "node_gap_k0"=>gn, "abs_mbar_ground"=>abs(mb)))
end
gap_zero_at_decoupled     = node_gaps[1] < 1e-10
gap_positive_when_coupled = all(node_gaps[2:end] .> 1e-6)
gap_monotone_in_t         = all(diff(node_gaps) .> -1e-9)        # nondecreasing
mbar_zero_at_decoupled    = mbars[1] < 1e-10
mbar_nonzero_when_coupled = all(mbars[2:end] .> 1e-6)

kill_control_fires = gap_zero_at_decoupled && gap_positive_when_coupled &&
                     gap_monotone_in_t &&
                     mbar_zero_at_decoupled && mbar_nonzero_when_coupled

results["kill_control_coupling_sweep"] = Dict(
    "sweep" => sweep,
    "gap_zero_at_t0" => gap_zero_at_decoupled,
    "gap_positive_when_coupled" => gap_positive_when_coupled,
    "gap_monotone_in_t" => gap_monotone_in_t,
    "mbar_zero_at_t0" => mbar_zero_at_decoupled,
    "mbar_nonzero_when_coupled" => mbar_nonzero_when_coupled,
    "kill_control_fires" => kill_control_fires,
)
println("\n[5] KILL-CONTROL: coupling sweep t = ", ts, "   (gap @ Weyl node k=0)")
for s in sweep
    println("    t=", rpad(s["t"],4), "  node_gap=", rpad(round(s["node_gap_k0"],digits=6),10),
            "  |mbar_gs|=", round(s["abs_mbar_ground"], digits=6))
end
println("    node-gap=0 at t=0 (Weyl) and >0 when coupled (Dirac): ",
        gap_zero_at_decoupled, " / ", gap_positive_when_coupled)
println("    mbar=0 at t=0 and mbar!=0 when coupled              : ",
        mbar_zero_at_decoupled, " / ", mbar_nonzero_when_coupled)
println("    KILL-CONTROL FIRES (Dirac emerges from L/R coupling): ", kill_control_fires)

# ======================================================================
# 6. NEGATIVE / WRONG-STRUCTURE control: a coupling that DOES NOT link the two
#    chiralities (a diagonal intra-block "coupling") must NOT open the gap nor
#    produce a Dirac mass. This confirms the emergence is specifically L<->R
#    (the off-diagonal gamma^theta channel), not any perturbation at all.
# ======================================================================
"Two-leaf H with a WRONG (intra-block, chirality-preserving) coupling of strength t."
function two_leaf_H_wrong(kvec, t)
    ksig = kvec[1]*sx + kvec[2]*sy + kvec[3]*sz
    H = zeros(ComplexF64, 4, 4)
    H[1:2,1:2] = -ksig + t*sz          # diagonal (intra-L) perturbation, NOT an L<->R hop
    H[3:4,3:4] =  ksig + t*sz
    return H
end
Hw = two_leaf_H_wrong(kvec, tcoup)
evw = sort(real.(eigvals(Hw)))
gap_wrong = evw[3] - evw[2]
mbar_wrong = mbar(gs(Hw))
# a chirality-preserving perturbation leaves gamma0 expectation 0 (still block-pure-ish)
wrong_no_dirac_mass = abs(mbar_wrong) < 1e-10
# and it does NOT open a gap straddling zero the way the L<->R coupling does:
# (it just shifts the two Weyl cones; the band-center crossing can persist).
# The decisive emergent contrast is the Dirac MASS BILINEAR being zero here.
results["negative_wrong_coupling"] = Dict(
    "description" => "intra-block (chirality-preserving) perturbation t*sz, NOT an L<->R hop",
    "eigs" => evw,
    "gap" => gap_wrong,
    "mbar_ground" => mbar_wrong,
    "wrong_coupling_gives_no_dirac_mass" => wrong_no_dirac_mass,
)
println("\n[6] NEGATIVE control (chirality-PRESERVING coupling, NOT L<->R):")
println("    eigs=", round.(evw,digits=5), "  gap=", round(gap_wrong,digits=6),
        "  mbar_gs=", round(mbar_wrong,digits=8))
println("    wrong coupling gives NO Dirac mass (mbar=0): ", wrong_no_dirac_mass)

# ======================================================================
# 7. HONEST VERDICT
# ======================================================================
genuineness = Dict(
    "carrier_clifford_measured"          => clifford_ok,
    "weyl_chirality_split_measured"      => weyl_split_ok,
    "gamma_theta_couples_L_R"            => gamma_theta_couples_LR,
    "on_leaf_modes_are_chiral_weyl"      => onleaf_L_is_left && onleaf_R_is_right,
    "single_weyl_has_no_mass_term"       => weyl_gapless && weyl_traceless,
    "node_decoupled_is_gapless_weyl"     => node_gap_dec < 1e-10,
    "node_coupled_gap_is_2t_dirac"       => node_gap_matches_2t,
    "fixed_k_coupled_is_dirac_disp"      => ev_cpl_matches_dirac,
    "pure_chirality_mbar_structurally_0" => pure_chirality_mbar_zero,
    "coupled_ground_state_has_dirac_mass"=> abs(mbar_gs_cpl) > 1e-6,
    "kill_control_fires"                 => kill_control_fires,
    "wrong_coupling_no_dirac_mass"       => wrong_no_dirac_mass,
)
all_pass = all(values(genuineness))

results["genuineness_booleans"] = genuineness
results["honesty_ledger"] = Dict(
    "forced" => "Radial Dirac decomposition D_S3 = gamma^theta(d_theta + H/2) + D_T2; " *
                "single 2-component Weyl block is gapless and has no mass term (gamma0 " *
                "off-diagonal in chiral basis); coupled spectrum = +-sqrt(k^2 + t^2).",
    "interpretive" => "Calling the 1D theta-chain 'the S^3 radial direction' is a model " *
                "identification, not a measured fact. The emergence of the gap / Dirac mass " *
                "under L<->R coupling IS measured; the geometric naming is interpretive.",
)
results["emergent_numbers"] = Dict(
    "node_gap_k0_decoupled_weyl" => node_gap_dec,
    "node_gap_k0_coupled_dirac"  => node_gap_cpl,
    "fixed_k_gap_decoupled" => gap_dec,
    "fixed_k_gap_coupled"   => gap_cpl,
    "mbar_ground_decoupled" => mbar_gs_dec,
    "mbar_ground_coupled"   => mbar_gs_cpl,
)
results["all_pass"] = all_pass
results["honest_status_ladder"] = all_pass ? "passes" : "runs"

println("\n========================================")
println("EMERGENT OBSERVABLE (coupled vs decoupled):")
println("    node gap (k=0) : DECOUPLED ", round(node_gap_dec,digits=6),
        "  ->  COUPLED ", round(node_gap_cpl,digits=6), "  (= 2|t| Dirac mass gap)")
println("    Dirac mass mbar: DECOUPLED ", round(mbar_gs_dec,digits=6),
        "  ->  COUPLED ", round(mbar_gs_cpl,digits=6))
println("KILL-CONTROL FIRES: ", kill_control_fires)
println("----------------------------------------")
println("GENUINENESS BOOLEANS:")
for k in sort(collect(keys(genuineness)))
    println("    ", rpad(k,38), " : ", genuineness[k])
end
println("ALL_PASS: ", all_pass)
println("HONEST LADDER STATUS: ", all_pass ? "passes" : "runs")
println("========================================")

outpath = joinpath(@__DIR__, "emergence_3d_dirac_from_weyl_coupling_results.json")
open(outpath, "w") do io
    JSON.print(io, results, 2)
end
println("\nWrote: ", outpath)
