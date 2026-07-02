# Phase-2.1 — branch/prune possibility field on GENUINE Dirac spinors with a real gamma5 chirality constraint.
# (Rev 2: corrected after adversarial audit. The earlier "frame-invariance proves genuine chirality" headline was
#  RETRACTED as overclaimed -- see HONEST LIMITS below. The genuine-selector proof is now the rate-matched-random
#  and inverted-sign controls.)
#
# State = Dirac 4-spinor psi in C^4 (|psi|=1) on the spinor sphere. Chirality = the genuine gamma5 chiral charge
# q(psi)=Re(psi'*gamma5*psi), gamma5 = i*g0*g1*g2*g3 DERIVED from the Weyl-basis Dirac generators. Prune = forbid
# the left-chiral sector (q<0): a future whose chiral charge crosses below -0.01 is pruned (monotone latch).
#
# WHAT PROVES CHIRALITY IS THE GENUINE BASIN SELECTOR (the real discriminator, from the audit):
#   - rate-matched RANDOM prune (remove the same number of futures at random) does NOT empty the forbidden basins
#     {3,4}; only the gamma5 prune does (it removes 124/124 forbidden-bound futures). => the gamma5 CHARGE, not the
#     prune rate or flow geometry, selects which basins die.
#   - inverted-sign prune (prune q>+0.99, keeping left-chiral) flips survivors to the forbidden basins {3,4}.
#
# HONEST LIMITS (verified by audit, stated not hidden):
#   - The gamma5 prune is BIT-IDENTICAL under a unitary spatial rotation U=exp(a*g1*g2/2) (rotation-covariant by
#     construction: gamma5 commutes with even products AND U is unitary so it preserves |psi|=1 and q). This is
#     REPORTED, not used as proof of genuineness: a non-chirality quadratic form psi'g0psi is EQUALLY rotation-
#     invariant, so rotation-invariance does not by itself single out chirality.
#   - The gamma5 charge is NOT invariant under a Lorentz BOOST exp(a*g0*g1/2) (non-unitary; it does not preserve
#     |psi|=1): the charge shifts and the prune set changes. So "Lorentz-invariant" is too strong; the correct
#     statement is "invariant under unitary spatial rotations on the normalized-spinor carrier."
#   - CliffordAlgebras Cl(1,3) is a SUPPORTIVE cross-witness only: removing it leaves all_pass=true unchanged. The
#     gamma5 genuineness is proven by the Dirac matrices themselves (gg.clifford re-derives the Clifford relations).
#
# classification = julia_branch_prune_dirac_poc ; promotion_allowed = false. Not canonical, not a bridge claim.

using LinearAlgebra, Random, CliffordAlgebras
import JSON

const OUT = joinpath(@__DIR__, "branch_prune_dirac_gamma5_chirality_object_results.json")
const C4 = Matrix{ComplexF64}(I, 4, 4)

# --- Genuine Dirac gamma matrices (Weyl/chiral basis); gamma5 DERIVED from their product ---
const I2 = Matrix{ComplexF64}(I, 2, 2); const Z2 = zeros(ComplexF64, 2, 2)
const SX = ComplexF64[0 1; 1 0]; const SY = ComplexF64[0 -im; im 0]; const SZ = ComplexF64[1 0; 0 -1]
blk(A, B, C, D) = [A B; C D]
const G0 = blk(Z2, I2, I2, Z2)
const G1 = blk(Z2, SX, -SX, Z2)
const G2 = blk(Z2, SY, -SY, Z2)
const G3 = blk(Z2, SZ, -SZ, Z2)
const GAMMAS = (G0, G1, G2, G3)
const G5 = im * G0 * G1 * G2 * G3          # = diag(-I2, +I2); DERIVED, not hand-set
const ETA = ComplexF64[1 0 0 0; 0 -1 0 0; 0 0 -1 0; 0 0 0 -1]

const SROT  = G1 * G2 / 2                   # spatial rotation generator (anti-Hermitian -> unitary U)
const SBOOST = G0 * G1 / 2                  # boost generator (Hermitian -> NON-unitary U)
rot_U(a)   = exp(a * SROT)
boost_U(a) = exp(a * SBOOST)

chiral_charge(psi) = real(psi' * G5 * psi)       # genuine gamma5 chiral charge in [-1,1]
quad_g0(psi)       = real(psi' * G0 * psi)        # non-chirality quadratic form (rotation-invariant control)

function gamma5_genuine()
    g5sq = maximum(abs.(G5 * G5 - C4)) < 1e-12
    anti = all(maximum(abs.(G5 * g + g * G5)) < 1e-12 for g in GAMMAS)
    clff = all(maximum(abs.(GAMMAS[m+1]*GAMMAS[n+1] + GAMMAS[n+1]*GAMMAS[m+1] - 2*ETA[m+1,n+1]*C4)) < 1e-12
               for m in 0:3, n in 0:3)
    rot_commute = maximum(abs.(G5 * SROT - SROT * G5)) < 1e-12
    rot_unitary = maximum(abs.(rot_U(0.7)' * rot_U(0.7) - C4)) < 1e-10
    boost_nonunitary = maximum(abs.(boost_U(0.7)' * boost_U(0.7) - C4)) > 1e-3   # honest: boost is NOT unitary
    (g5sq=g5sq, anti=anti, clifford=clff, rot_commute=rot_commute,
     rot_unitary=rot_unitary, boost_nonunitary=boost_nonunitary)
end

function clifford_crosscheck()  # SUPPORTIVE only (removing it leaves all_pass unchanged)
    cl = CliffordAlgebra(1, 3); g = (cl.e1, cl.e2, cl.e3, cl.e4)
    g5cl = g[1] * g[2] * g[3] * g[4]
    (pseudoscalar_sq=real(CliffordAlgebras.scalar(g5cl * g5cl)),
     anticommutes=all(abs(CliffordAlgebras.norm(g5cl*x + x*g5cl)) < 1e-10 for x in g))
end

# --- 4 target Dirac spinors: 2 RIGHT-chiral (q>0, ALLOWED), 2 LEFT-chiral (q<0, FORBIDDEN) ---
nrm(v) = v / norm(v)
const TARGETS = Vector{ComplexF64}[
    nrm(ComplexF64[0, 0, 1, 0.3]), nrm(ComplexF64[0, 0, 0.3, 1]),   # 1,2 allowed
    nrm(ComplexF64[1, 0.3, 0, 0]), nrm(ComplexF64[0.3, 1, 0, 0]),   # 3,4 forbidden
]
const ALLOWED = [1, 2]; const FORBIDDEN = [3, 4]
nearest(psi, T) = argmax(k -> abs2(T[k]' * psi), 1:length(T))
flow_step(psi, T) = (tk = T[nearest(psi, T)]; 2.0 * (tk - (psi' * tk) * psi))

# prune iff `prune_charge(psi) < thresh` ever (monotone latch). prune_charge=nothing -> no prune.
function evolve(psi0, T, prune_charge, thresh)
    psi = copy(psi0); pruned = false
    for _ in 1:round(Int, TMAX / DT)
        k1 = flow_step(psi, T); k2 = flow_step(nrm(psi + 0.5DT*k1), T)
        k3 = flow_step(nrm(psi + 0.5DT*k2), T); k4 = flow_step(nrm(psi + DT*k3), T)
        psi = nrm(psi + (DT/6)*(k1 + 2k2 + 2k3 + k4))
        if prune_charge !== nothing && prune_charge(psi) < thresh; pruned = true; break; end
    end
    (psi=psi, pruned=pruned)
end

const N = 600; const TMAX = 12.0; const DT = 0.01

function build_inits(N)
    rng = MersenneTwister(2026); inits = Vector{ComplexF64}[]
    while length(inits) < N
        psi = nrm(ComplexF64[randn(rng)+im*randn(rng) for _ in 1:4])
        chiral_charge(psi) > 0.1 && push!(inits, psi)
    end
    inits
end

function classify(inits, T, prune_charge, thresh=-0.01)
    survivors = Int[]; pruned_idx = Int[]; maxdrift = 0.0
    for (i, psi0) in enumerate(inits)
        r = evolve(psi0, T, prune_charge, thresh)
        maxdrift = max(maxdrift, abs(norm(r.psi) - 1))
        r.pruned ? push!(pruned_idx, i) : push!(survivors, nearest(r.psi, T))
    end
    (populated=sort(unique(survivors)), n_survivors=length(survivors),
     pruned=length(pruned_idx), pruned_idx=pruned_idx, maxdrift=maxdrift)
end

# Rate-matched RANDOM prune: remove K random futures (uncorrelated with chirality), classify the rest by no-prune fate.
function classify_random(inits, T, K, seed)
    doomed = Set(randperm(MersenneTwister(seed), length(inits))[1:K])
    survivors = [nearest(evolve(inits[i], T, nothing, 0.0).psi, T) for i in 1:length(inits) if !(i in doomed)]
    sort(unique(survivors))
end

println("verifying gamma5 genuineness ...")
gg = gamma5_genuine(); cc = clifford_crosscheck()
println("  g5^2=I:$(gg.g5sq) anticommute:$(gg.anti) clifford:$(gg.clifford) rot_commute:$(gg.rot_commute) boost_nonunitary:$(gg.boost_nonunitary) Cl13_ps^2=$(cc.pseudoscalar_sq)")

const BASE = build_inits(N)
const Ur = rot_U(0.7);  const Ub = boost_U(0.7)
const BASE_ROT = [Ur * psi for psi in BASE];   const TARGETS_ROT = [Ur * t for t in TARGETS]
const BASE_BST = [nrm(Ub * psi) for psi in BASE]; const TARGETS_BST = [nrm(Ub * t) for t in TARGETS]

println("runs ...")
A       = classify(BASE, TARGETS, nothing)                       # no prune
Bg5     = classify(BASE, TARGETS, chiral_charge)                 # gamma5 chirality prune
Cctrl   = classify(BASE, TARGETS, _ -> 1.0)                      # trivial control (never fires)
rot_g5  = classify(BASE_ROT, TARGETS_ROT, chiral_charge)         # rotation frame (should be bit-identical)
bst_g5  = classify(BASE_BST, TARGETS_BST, chiral_charge)         # boost frame (honest: NOT identical)
inv     = classify(BASE, TARGETS, psi -> -chiral_charge(psi), -0.99)  # inverted-sign prune (q>0.99)
rand_pop = classify_random(BASE, TARGETS, Bg5.pruned, 11)        # rate-matched random prune
quad_lab = classify(BASE, TARGETS, quad_g0, -0.99)               # quadratic-form prune, lab
quad_rot = classify(BASE_ROT, TARGETS_ROT, quad_g0, -0.99)       # quadratic-form prune, rotated (control)

checks = Dict(
    "gamma5_genuine"                 => gg.g5sq && gg.anti && gg.clifford && gg.rot_commute && gg.rot_unitary,
    "A_reaches_forbidden"            => !isempty(intersect(A.populated, FORBIDDEN)),
    "B_kills_all_forbidden"          => isempty(intersect(Bg5.populated, FORBIDDEN)),
    "B_preserves_allowed"            => issubset(intersect(A.populated, ALLOWED), Bg5.populated),
    "control_C_equals_A"             => Cctrl.populated == A.populated && Cctrl.pruned == 0,
    "B_pruned_some_A_none"           => Bg5.pruned > 0 && A.pruned == 0,
    # THE GENUINE-SELECTOR PROOF (chirality, not rate or geometry, selects which basins die):
    "rate_matched_random_KEEPS_forbidden" => !isempty(intersect(rand_pop, FORBIDDEN)),
    "inverted_sign_flips_to_forbidden"     => isempty(intersect(inv.populated, ALLOWED)) && !isempty(intersect(inv.populated, FORBIDDEN)),
    "norm_drift_small"               => max(A.maxdrift, Bg5.maxdrift) < 1e-3,
)
all_pass = all(values(checks))

# REPORTED honest properties (NOT gates): rotation-covariance, boost-variance, quadratic-form rotation-invariance.
reported = Dict(
    "gamma5_prune_rotation_covariant" => (rot_g5.pruned_idx == Bg5.pruned_idx && rot_g5.populated == Bg5.populated),
    "gamma5_prune_boost_CHANGES"      => (bst_g5.pruned != Bg5.pruned || bst_g5.pruned_idx != Bg5.pruned_idx),
    "quad_form_ALSO_rotation_invariant" => (quad_rot.pruned == quad_lab.pruned),  # rotation-inv is generic, not chirality-specific
    "lab_B_pruned" => Bg5.pruned, "rot_B_pruned" => rot_g5.pruned, "boost_B_pruned" => bst_g5.pruned,
)

result = Dict(
    "name" => "branch_prune_dirac_gamma5_chirality_object",
    "classification" => "julia_branch_prune_dirac_poc", "promotion_allowed" => false,
    "tool_integration" => Dict("dirac_matrices" => "load_bearing", "CliffordAlgebras" => "supportive_crosscheck_only",
                               "note" => "removing CliffordAlgebras leaves all_pass=true; gg.clifford re-derives the relations"),
    "claim_ceiling" => "PoC: branch/prune possibility field on genuine Dirac 4-spinors; the prune is the real gamma5 " *
                       "chiral charge. GENUINE-SELECTOR proof: a rate-matched random prune does NOT empty the forbidden " *
                       "basins while the gamma5 prune does, and an inverted-sign prune flips survivors to the forbidden " *
                       "basins -> chirality (not rate/geometry) selects which basins die. LIMITS: gamma5 charge is invariant " *
                       "under unitary spatial rotations only, NOT Lorentz boosts; CliffordAlgebras is supportive, not " *
                       "load-bearing. promotion_allowed=false; not canonical/bridge.",
    "gamma5_verification" => Dict("g5_sq_eq_I"=>gg.g5sq, "anticommutes"=>gg.anti, "clifford_relations"=>gg.clifford,
                                  "rotation_commute"=>gg.rot_commute, "rot_unitary"=>gg.rot_unitary,
                                  "boost_nonunitary"=>gg.boost_nonunitary, "Cl13_pseudoscalar_sq"=>cc.pseudoscalar_sq),
    "branch_prune" => Dict("A"=>A.populated, "B_gamma5"=>Bg5.populated, "C_control"=>Cctrl.populated,
                           "B_pruned"=>Bg5.pruned, "inverted_survivors"=>inv.populated, "random_prune_survivors"=>rand_pop),
    "reported_limits" => reported,
    "max_norm_drift" => round(max(A.maxdrift, Bg5.maxdrift); digits=12),
    "checks" => checks, "all_pass" => all_pass,
)
open(OUT, "w") do io; JSON.print(io, result, 2); end

println("\n=== branch/prune Dirac gamma5 v2.1 (rev 2) ===")
println("branch/prune:  A=$(A.populated)  B(gamma5)=$(Bg5.populated)  C=$(Cctrl.populated)  pruned=$(Bg5.pruned)")
println("SELECTOR proof: rate-matched random prune survivors=$rand_pop  (forbidden {3,4} must SURVIVE)")
println("                inverted-sign prune survivors=$(inv.populated)  (must flip to {3,4})")
println("reported limit: rotation B pruned=$(rot_g5.pruned) idx==lab? $(rot_g5.pruned_idx==Bg5.pruned_idx) | boost B pruned=$(bst_g5.pruned) (NOT invariant) | quad-form rot-invariant? $(quad_rot.pruned==quad_lab.pruned)")
for (k, v) in sort(collect(checks); by=first); println(rpad(k, 36), v ? "PASS" : "FAIL"); end
println("ALL_PASS = $all_pass")
exit(all_pass ? 0 : 1)
