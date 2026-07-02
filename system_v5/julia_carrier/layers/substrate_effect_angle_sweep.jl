#!/usr/bin/env julia
# =====================================================================================
# substrate_effect_angle_sweep.jl  —  ITERATION 8. Caps the finite-carrier substrate arc:
#   resolves whether the d=2-POSITIVE / d>=4-NEGATIVE substrate-suppression SIGN SPLIT
#   found in iteration 7 (substrate_effect_matched_band.jl, fixed ang=0.9) is STRUCTURAL
#   (the higher-Hopf irreducibility switching the suppression on at d>=4) or an
#   ANGLE-SPECIFIC ACCIDENT of the one Weyl rotor angle ang=0.9.
#
#   classification = substrate_effect_angle_sweep_poc ; promotion_allowed = false.
#   DENSITY-OPERATOR ONLY. NO PEPS, NO CTMRG, NO optimization. < 200 s.
# -------------------------------------------------------------------------------------
# OBJECT_ID: substrate_effect_angle_sweep
#
# THE ITER-7 RESULT BEING PRESSURE-TESTED (READ from
#   substrate_effect_matched_band_results.json, NOT invented):
#     At the SINGLE fixed Weyl rotor angle ang=0.9, the +/-10% commutator-matched
#     scale-swept band z(d) = (E_hopf - band_mean)/band_std came out:
#       z(d=2) = +1.341  (POSITIVE: genuine Hopf rotor MORE substrate effect than matched random)
#       z(d=4) = -1.008  (NEGATIVE: LESS effect than matched random -> "suppression")
#       z(d=8) = -2.084  (NEGATIVE, stronger)
#     i.e. a SIGN SPLIT at the carrier dimension: d=2 positive, d>=4 negative. iter-7 read
#     this as "substrate_suppression_real_at_scale_finite" and seed-stable. BUT iter-7
#     swept only the random-band SCALE; it FIXED the geometry rotor angle at ang=0.9. The
#     open question iter-7 could NOT answer with one angle: is the d>=4 negative sign a
#     genuine higher-Hopf structural fact, or did ang=0.9 happen to land in a negative pocket?
#
# THE ONLY NEW THING vs iter-7 (everything else is reused VERBATIM):
#   Sweep the Weyl upper-op / Hopf rotor angle `ang` across N_ANG values spanning [0.1, pi]
#   (iter-7 fixed ang=0.9), at carriers d in {2,4,8}. At each (d, ang): populate the same
#   +/-10% commutator-matched scale-swept band, compute z_matched(d, ang) with the iter-7
#   discriminator VERBATIM. A secondary GKSL-strength (gamma) axis of 3 values is added as a
#   robustness check; the angle axis is the load-bearing one.
#
#   GENUINE objects reused VERBATIM from iter-7 / iter-6 / iter-5 (read, NOT reinvented):
#     - clifford_gammas(d): Cl(3)/Cl(5)/Cl(7) Hermitian anticommuting gamma towers
#       (Spin(3)/Spin(5)/Spin(7)); anticommutation {Ga,Gb}=2 delta_ab MEASURED.
#     - hopf_base / hopf_frame: Hopf moment map psi'.Gamma.psi -> base point; genuine rotor
#       exp(-i ang/2 n.Gamma). (THE ONLY thing this object varies is the `ang` argument.)
#     - hopf_h0: the genuine n.Gamma GKSL Hamiltonian part at the upper-op Hopf site.
#     - lowering_d: sigma_- lifted to dim d (GKSL jump / sink basin).
#     - gksl_step_evolve: the dissipative Weyl-L GKSL channel Phi_WeylL.
#     - rand_hermitian / scale_swept_frame: the scale-swept random control U=exp(-i s H_rand).
#     - substrate_effect / dressed: E(A) = max_rho ||U Phi(U' rho U) U' - Phi(rho)||_1.
#     - z3_separation_obstruction: the Z3 verdict-flip (flat => sep==0).
#   The DISTINCT psi_A (frame site) / psi_B (upper-op site) split is reused so c_hopf != 0.
#
# CLAIM CEILING: this object MEASURES the SIGN of z_matched(d, ang) over a grid of carrier
#   dim d in {2,4,8} and rotor angle ang in [0.1, pi], to decide whether iter-7's d>=4 negative
#   "suppression" sign holds across angles (structural) or flips with angle (an ang=0.9
#   accident). It does NOT assert layer-completion, manifold admission, coupling, bridge
#   (rho_AB/Xi/Phi0/Axis0), flux, FEP, or physics. A robustly-negative z(d=8) across angles
#   is a CANDIDATE higher-Hopf structural-suppression fact on the density-operator carrier,
#   NOT a proven nesting layer. promotion_allowed = false.
#
# THE DECISIVE OBSERVABLE: the SIGN of z_matched(d, ang). Report the full z(d, ang) surface and:
#   - frac_split = fraction of swept angles where (z(d=2)>0 AND z(d>=4)<0) holds (iter-7 pattern).
#   - Is the d>=4 NEGATIVE sign STABLE across angles, or does it flip with ang?
#   - Is the d=2 POSITIVE sign stable across angles?
#
# VERDICT (do NOT collapse a mixed surface):
#   - sign_split_structural: z(d=8) is robustly negative across MOST angles
#       (frac_neg_d8_populated >= ~0.7) AND the d=2/d>=4 sign difference persists across angles
#       -> iter-7's suppression is a genuine higher-Hopf structural fact, not an ang=0.9 accident.
#   - sign_split_angle_artifact: z(d=8) sign flips with angle / the split vanishes at most angles
#       -> iter-7's negative z was angle-specific; no robust geometric suppression.
#   - mixed_*: e.g. d=8 robust-negative across angles but d=4 sign-unstable -> report exactly
#       which legs are structural and which wander.
#
# ANTI-TAUTOLOGY (preserved at every (d,ang)):
#   - FLAT control U=I -> E at the noise floor at every angle (effect vanishes with no geometry).
#   - BAND COVERAGE: band populated + scale-swept range brackets c_hopf at every (d,ang)
#     (report coverage; SKIP any (d,ang) where the band can't populate, noting it).
#   - SEED-STABLE: vary seed, check the sign of z(d=8) stable across angles.
#   - Z3 verdict-flip at one representative (d=8, ang).
#   - explicit noise floor.
# =====================================================================================

using LinearAlgebra
using Random
using Statistics
import JSON
import Z3

const RESULT_PATH = joinpath(@__DIR__, "substrate_effect_angle_sweep_results.json")
const SEED   = 20260602
const N_RHO  = 20            # 20 + 1 (maximally-mixed) density operators per carrier
const N_RAND = 2000          # scale-swept random band size (iter-7 verbatim)
const N_ANG  = 12            # angle sweep resolution (load-bearing axis)

# ---------- single-qubit primitives (iter-7 verbatim) ----------
const σ1 = ComplexF64[0 1; 1 0]
const σ2 = ComplexF64[0 -im; im 0]
const σ3 = ComplexF64[1 0; 0 -1]
const I2 = Matrix{ComplexF64}(I, 2, 2)
const SM1 = ComplexF64[0 0; 1 0]   # sigma_- lowering (sink) on one qubit

hs(A)         = sqrt(real(tr(A' * A)))   # Hilbert-Schmidt norm
trace_norm(M) = sum(svdvals(M))          # Schatten-1 (||.||_1) — the metric for E(A)

# =====================================================================================
# GENUINE GEOMETRY per carrier dim d (Clifford gamma towers; anticommutation checked).
# REUSED VERBATIM from substrate_effect_matched_band.jl (iter-7).
# =====================================================================================
function clifford_gammas(d::Int)
    if d == 2          # Cl(3): n.sigma  (complex Hopf S^3->S^2)
        return [σ1, σ2, σ3]
    elseif d == 4      # Cl(5): Spin(5)=Sp(2)  (quaternionic Hopf S^7->S^4)
        return [kron(σ1,I2), kron(σ2,I2), kron(σ3,σ1), kron(σ3,σ2), kron(σ3,σ3)]
    elseif d == 8      # Cl(7): Spin(7)  (octonionic Hopf S^15->S^8)
        return [kron(σ1,I2,I2), kron(σ2,I2,I2),
                kron(σ3,σ1,I2), kron(σ3,σ2,I2),
                kron(σ3,σ3,σ1), kron(σ3,σ3,σ2), kron(σ3,σ3,σ3)]
    else
        error("ladder built only for d in {2,4,8}")
    end
end

function clifford_anticomm_err(g)
    n = length(g)
    maximum(norm(g[a]*g[b] + g[b]*g[a] - (a==b ? 2*Matrix{ComplexF64}(I,size(g[a])...) : zero(g[a])))
            for a in 1:n, b in 1:n)
end

function hopf_base(psi::Vector{ComplexF64}, g)
    p = psi / norm(psi)
    [real(p' * (G * p)) for G in g]
end

# GENUINE Hopf frame at dim d: rotor exp(-i ang/2 n.Gamma) at a genuine Hopf base point.
# ang is the ONLY swept variable in this object.
function hopf_frame(d::Int, psi::Vector{ComplexF64}, ang::Float64)
    g = clifford_gammas(d)
    nb = hopf_base(psi, g); nn = norm(nb)
    nhat = nn < 1e-12 ? vcat(zeros(length(g)-1), 1.0) : nb ./ nn
    H = sum(nhat[k]*g[k] for k in 1:length(g))   # H^2 = I (reflection at the base point)
    return exp(-im * ang/2 * H), nhat, nn
end

# Hopf-site base Hamiltonian H0_d = n.Gamma (the genuine GKSL Hamiltonian part at dim d).
function hopf_h0(d::Int, psi::Vector{ComplexF64})
    g = clifford_gammas(d)
    nb = hopf_base(psi, g); nn = norm(nb)
    nhat = nn < 1e-12 ? vcat(zeros(length(g)-1), 1.0) : nb ./ nn
    return sum(nhat[k]*g[k] for k in 1:length(g))
end

# lowering operator sigma_- lifted to dim d (on the TOP qubit) — GKSL jump (sink basin).
function lowering_d(d::Int)
    if d == 2
        return SM1
    elseif d == 4
        return kron(SM1, I2)
    elseif d == 8
        return kron(SM1, kron(I2, I2))
    end
end

# =====================================================================================
# GENUINE DISSIPATIVE WEYL-GKSL UPPER OP, lifted to dim d (iter-7 verbatim).
# gamma = GKSL dissipative strength (secondary swept axis); eps = Hamiltonian strength.
# =====================================================================================
dissipator(L, rho)      = L*rho*L' - 0.5*((L'*L)*rho + rho*(L'*L))
commutator_flow(H, rho) = -im * (H*rho - rho*H)
function gksl_step_evolve(rho0, H, L; gamma=1.0, eps=1.0, T=4.0, steps=120)
    dt = T/steps; r = rho0
    for _ in 1:steps
        r = r + dt*(gamma*dissipator(L, r) + eps*commutator_flow(H, r))
        r = (r + r')/2
        tr_r = real(tr(r)); abs(tr_r) > 1e-12 && (r = r/tr_r)
    end
    return r
end

# =====================================================================================
# random density operators (iter-7 verbatim).
# =====================================================================================
function rand_rho(rng, d)
    psi = ComplexF64[randn(rng)+im*randn(rng) for _ in 1:d]
    psi /= norm(psi)
    pure = psi * psi'
    Id = Matrix{ComplexF64}(I, d, d)
    p = 0.2 + 0.6*rand(rng)
    rho = p*pure + (1-p)*(Id/d)
    return (rho + rho')/2 / real(tr((rho+rho')/2))
end
make_rhos(rng, n, d) = vcat([rand_rho(rng, d) for _ in 1:n], [Matrix{ComplexF64}(I, d, d)/d])

# =====================================================================================
# SCALE-SWEPT random control U = exp(-i * s * H_rand) (iter-7 verbatim). H_rand is a random
# Hermitian generator normalized to unit operator-norm; s log-uniform so the ENSEMBLE's
# ||[U, H_Weyl]|| range brackets the (low) Hopf rotor commutator c_hopf. This is the
# commutator-bracketing control, NOT a geometry frame.
# =====================================================================================
function rand_hermitian(rng, d)
    A = ComplexF64[randn(rng)+im*randn(rng) for _ in 1:d, _ in 1:d]
    H = (A + A') / 2
    nrm = opnorm(H)
    return nrm < 1e-12 ? H : H / nrm
end
scale_swept_frame(H_rand, s::Float64) = exp(-im * s * H_rand)

# =====================================================================================
# THE DRESSED CHANNEL and the substrate-effect functional E(A) (iter-7 verbatim).
# =====================================================================================
dressed(PhiB, U, rho) = U * PhiB(U' * rho * U) * U'
function substrate_effect(PhiB, U, rhos)
    diffs = Float64[]
    for rho in rhos
        push!(diffs, trace_norm(dressed(PhiB, U, rho) - PhiB(rho)))
    end
    return mean(diffs), maximum(diffs)
end

# =====================================================================================
# Z3 load-bearing verdict-flip (iter-7 verbatim): genuine nonzero separation -> UNSAT,
# flat zero separation -> SAT.
# =====================================================================================
function z3_separation_obstruction(measured_sep::Float64; scale=1_000_000_000)
    ctx = Z3.Context(); s = Z3.Solver(ctx)
    sep     = Z3.IntVar("sep", ctx)
    is_flat = Z3.BoolVar("is_flat", ctx)
    Z3.add(s, Z3.Or([Z3.Not(is_flat), sep == Z3.IntVal(0, ctx)]))   # flat => sep==0
    Z3.add(s, is_flat == Z3.BoolVal(true, ctx))
    m = round(Int, scale * abs(measured_sep))
    Z3.add(s, sep == Z3.IntVal(m, ctx))
    return string(Z3.check(s))    # genuine(nonzero): unsat ; flat(zero): sat
end

# =====================================================================================
# CORE: one (d, ang, gamma) cell. The iter-7 matched_band_level discriminator VERBATIM,
# parameterized on ang (the swept geometry angle) and gamma (the secondary GKSL strength).
# Returns z_matched, band_populated, brackets_c_hopf, flat_collapses + supporting numbers.
# The frame site / upper-op site split (psi_A / psi_B) is iter-7 verbatim.
# =====================================================================================
function angle_cell(d::Int, ang::Float64, rng_seed::Int; gamma::Float64=1.0, n_band::Int=N_RAND)
    rng  = MersenneTwister(rng_seed)
    rhos = make_rhos(rng, N_RHO, d)

    # TWO DISTINCT genuine Hopf base spinors (iter-7 verbatim): frame site psi_A != upper-op
    # site psi_B so [U_hopf, H0] != 0 (c_hopf > 0).
    psi_B = ComplexF64[ (k % 2 == 1 ? cos(0.3*k+0.2) : sin(0.4*k+0.1)) +
                        im*(0.2*cos(0.5*k) - 0.1*sin(0.3*k)) for k in 1:d ]   # upper-op site
    psi_B /= norm(psi_B)
    psi_A = ComplexF64[ (k % 2 == 1 ? sin(0.55*k+1.1) : cos(0.27*k+0.6)) +
                        im*(0.35*sin(0.42*k+0.3) - 0.18*cos(0.6*k+0.9)) for k in 1:d ]  # frame site
    psi_A /= norm(psi_A)

    g = clifford_gammas(d)
    anticomm_err = clifford_anticomm_err(g)      # genuine-Clifford witness (measured)

    # GENUINE upper op: dissipative Weyl-L GKSL lifted to dim d, at the upper-op Hopf site.
    H0 = hopf_h0(d, psi_B)
    Lm = lowering_d(d)
    PhiWeyl = rho -> gksl_step_evolve(rho, +H0, Lm; gamma=gamma)

    # genuine irreducible higher-Hopf frame at the DISTINCT frame site at THIS ang, + flat ctrl
    U_hopf, nhat, nbnorm = hopf_frame(d, psi_A, ang)
    U_flat   = Matrix{ComplexF64}(I, d, d)

    Eh_mean, Eh_max = substrate_effect(PhiWeyl, U_hopf, rhos)
    Ef_mean, Ef_max = substrate_effect(PhiWeyl, U_flat,  rhos)

    noise_floor = eps(Float64) * 1.0 * 4.0 * 16.0

    # commutator generator V = H0 (the GKSL Hamiltonian part) — the non-commutation axis.
    Vop = H0
    comm_norm(U) = hs(U*Vop - Vop*U)
    cg = comm_norm(U_hopf); Eg = Eh_max     # the genuine Hopf rotor's commutator + effect

    # SCALE-SWEPT random band that BRACKETS c_hopf (iter-7 verbatim).
    rng_r = MersenneTwister(rng_seed + 777)
    s_lo = 1e-3
    s_hi = 1.5
    log_lo, log_hi = log(s_lo), log(s_hi)
    rand_c = Float64[]; rand_E = Float64[]
    for _ in 1:n_band
        Hr = rand_hermitian(rng_r, d)
        s  = exp(log_lo + (log_hi - log_lo)*rand(rng_r))
        U  = scale_swept_frame(Hr, s)
        push!(rand_c, comm_norm(U))
        push!(rand_E, substrate_effect(PhiWeyl, U, rhos)[2])
    end
    rand_mean = mean(rand_E); rand_std = std(rand_E)
    rand_c_lo, rand_c_hi = minimum(rand_c), maximum(rand_c)

    bracket_lo_ok = rand_c_lo <= cg
    bracket_hi_ok = rand_c_hi >= cg
    brackets_c_hopf = bracket_lo_ok && bracket_hi_ok

    # +/-10% commutator-matched band around c_hopf (iter-7 decisive tolerance, verbatim).
    tol = 0.10 * max(cg, 1e-9)
    idx = [k for k in 1:n_band if abs(rand_c[k] - cg) <= tol]
    band_populated = length(idx) >= 8
    z_matched = NaN; em_mean = NaN; em_std = NaN
    if band_populated
        Em = [rand_E[k] for k in idx]
        em_mean = mean(Em); em_std = std(Em)
        z_matched = em_std > 1e-12 ? (Eg - em_mean)/em_std : 0.0
    end

    z_full = rand_std > 1e-12 ? (Eg - rand_mean) / rand_std : 0.0

    return Dict{String,Any}(
        "d" => d, "ang" => ang, "gamma" => gamma,
        "clifford_anticomm_err" => anticomm_err,
        "clifford_genuine" => anticomm_err < 1e-9,
        "E_hopf_max" => Eg, "E_hopf_mean" => Eh_mean,
        "E_flat_max" => Ef_max, "flat_collapses" => Ef_max < noise_floor,
        "noise_floor" => noise_floor,
        "c_hopf" => cg,
        "rand_c_lo" => rand_c_lo, "rand_c_hi" => rand_c_hi,
        "brackets_c_hopf" => brackets_c_hopf,
        "n_matched" => length(idx),
        "band_populated" => band_populated,
        "E_matched_mean" => em_mean, "E_matched_std" => em_std,
        "z_matched" => z_matched,
        "z_full" => z_full,
    )
end

# =====================================================================================
# RUN
# =====================================================================================
function run()
    R = Dict{String,Any}()
    R["object_id"]         = "substrate_effect_angle_sweep"
    R["sim_id"]            = "substrate_effect_angle_sweep"
    R["name"]              = "Angle sweep of the iter-7 d=2-positive / d>=4-negative substrate-suppression sign split: structural or ang=0.9 accident? (density-operator only, NO PEPS)"
    R["version"]           = "1.0"
    R["classification"]    = "substrate_effect_angle_sweep_poc"
    R["promotion_allowed"] = false
    R["sim_execution_kind"]= "nonclassical_poc"
    R["sim_class"]         = "geometry_probe"
    R["script"]            = "substrate_effect_angle_sweep.jl"
    R["seed"]              = SEED
    R["n_rho"]             = N_RHO + 1
    R["n_random_band"]     = N_RAND
    R["n_angles"]          = N_ANG
    R["non_numpy"]         = true
    R["bloch_free"]        = true
    R["carrier_layer"]     = "density operators in D(C^d), d in {2,4,8}; genuine higher-Hopf rotor frames (Spin(3)/Spin(5)/Spin(7)) from Clifford gamma towers (iter-7 verbatim) swept across rotor angle ang in [0.1, pi]; dissipative Weyl-L GKSL upper op lifted to dim d. NO CTMRG, NO PEPS, NO optimization."
    R["geometry_layer"]    = "Clifford gamma towers Cl(3)/Cl(5)/Cl(7) (anticommutation verified); Hopf moment map psi'.Gamma.psi -> base sphere; Spin rotor exp(-i ang/2 n.Gamma) with ang SWEPT (reused verbatim from substrate_effect_matched_band.jl; only ang varies)"
    R["finite_map"]        = "(carrier dim d, rotor angle ang) |-> genuine Hopf frame U_hopf(d, ang) in Spin(2k+1) |-> dressed dissipative-Weyl channel Phi_B^A(rho)=U Phi_WeylL(U' rho U) U'; observable z_matched(d, ang)=(E_hopf - band_mean)/band_std over the iter-7 scale-swept +/-10% commutator-matched random band bracketing c_hopf"
    R["domain"]            = "grid (d in {2,4,8}) x (ang: $(N_ANG) values in [0.1, pi]); plus secondary gamma in {0.5,1.0,1.5}; per cell: $(N_RHO+1) density operators; frame set {Hopf rotor at ang, flat=I, $(N_RAND) scale-swept random U=exp(-i s H_rand)}; upper op = Weyl-L GKSL lifted to dim d"
    R["codomain_or_output"]= "full z_matched(d, ang) surface; per-d sign-stability of z across angles; frac_split (z(d=2)>0 AND z(d>=4)<0); frac_neg_d8_populated; seed-robust sign of z(d=8) across angles; Z3 verdict-flip at one representative (d=8, ang)"
    R["spinor_state"]      = "unit spinors on S^3/S^7/S^15 -> Hopf base via moment map; Spin(2k+1) rotor frames at swept ang; GKSL state from Hopf-site Hamiltonian H0_d = n.Gamma"
    R["quaternion_action"] = "C^4 frame is Spin(5)=Sp(2) (quaternionic Hopf); C^8 is Spin(7) (octonionic Hopf); scale-swept control frames are exp(-i s H_rand), NOT geometry frames"
    R["dependency_receipts"] = [
        "layers/substrate_effect_matched_band.jl (iter-7 object under test; genuine Clifford gamma towers + Hopf rotors + Weyl-L GKSL + scale-swept matched band + z/Z3 discipline reused VERBATIM; THIS object sweeps the ang it fixed at 0.9)",
        "layers/substrate_effect_matched_band_results.json (iter-7 result: z(2)=+1.341, z(4)=-1.008, z(8)=-2.084 at ang=0.9 -> the sign split this object pressure-tests across angles)",
        "layers/substrate_effect_scale_ladder.jl (iter-6 genuine Clifford gamma towers + Hopf rotors + Weyl-L GKSL)",
        "layers/substrate_effect_frame_conjugation.jl (iter-5 validated commutator-matched paired discriminator + dissipative Weyl-L GKSL upper op)",
        "layers/order_null_killtest.jl (genuine Weyl GKSL gksl_step_evolve + hopf_h0 + noise-floor/Z3 discipline)",
        "layers/G_hopf_fibration.jl (Hopf representative spinor / moment map)",
        "layers/clifford_rotor_spinor_network_entanglement.jl (Clifford gamma generators / SU(2) rotor)",
        "layers/L7_layer_bf.jl (per-sheet Weyl GKSL channel)",
    ]
    R["claim_ceiling"] = "MEASURES the SIGN of z_matched(d, ang) over a grid of carrier dim d in {2,4,8} and rotor angle ang in [0.1, pi] to decide whether iter-7's d>=4 negative 'suppression' sign holds across angles (structural) or flips with angle (an ang=0.9 accident). Does NOT assert layer-completion / manifold admission / coupling / bridge / flux / FEP / physics. A robustly-negative z(d=8) across angles is a CANDIDATE higher-Hopf structural-suppression fact on the density-operator carrier, NOT a proven nesting layer. promotion_allowed=false."

    println("="^100)
    println("SUBSTRATE-EFFECT ANGLE SWEEP  (object_id=substrate_effect_angle_sweep)  ITER-8")
    println("  classification=substrate_effect_angle_sweep_poc  promotion_allowed=false")
    println("  question: is iter-7's d=2-positive / d>=4-negative SIGN SPLIT structural, or an ang=0.9 accident?")
    println("  sweep: ang in [0.1, pi] ($(N_ANG) values) at d in {2,4,8}; iter-7 discriminator VERBATIM")
    println("="^100)

    dims   = [2, 4, 8]
    angles = collect(range(0.1, stop=pi, length=N_ANG))

    # ============================================================================
    # MAIN SWEEP (gamma=1.0, base seed): z_matched(d, ang) surface.
    # ============================================================================
    surface = Dict{String,Any}()         # surface["d8"] = vector of z over angles
    pop_surface = Dict{String,Any}()     # band populated per (d,ang)
    bracket_surface = Dict{String,Any}()
    flat_collapse_surface = Dict{String,Any}()
    chopf_surface = Dict{String,Any}()
    cells = Dict{String,Any}()
    all_clifford_genuine = true

    z_by_d = Dict(d => Float64[] for d in dims)
    pop_by_d = Dict(d => Bool[] for d in dims)
    bracket_by_d = Dict(d => Bool[] for d in dims)
    flat_by_d = Dict(d => Bool[] for d in dims)
    chopf_by_d = Dict(d => Float64[] for d in dims)

    for (ai, ang) in enumerate(angles)
        for d in dims
            cell = angle_cell(d, ang, SEED; gamma=1.0)
            cells["d$(d)_a$(ai)"] = cell
            push!(z_by_d[d], cell["band_populated"] ? cell["z_matched"] : NaN)
            push!(pop_by_d[d], cell["band_populated"])
            push!(bracket_by_d[d], cell["brackets_c_hopf"])
            push!(flat_by_d[d], cell["flat_collapses"])
            push!(chopf_by_d[d], cell["c_hopf"])
            all_clifford_genuine &= cell["clifford_genuine"]
        end
    end

    for d in dims
        surface["d$d"] = z_by_d[d]
        pop_surface["d$d"] = pop_by_d[d]
        bracket_surface["d$d"] = bracket_by_d[d]
        flat_collapse_surface["d$d"] = flat_by_d[d]
        chopf_surface["d$d"] = chopf_by_d[d]
    end

    # print the surface
    println("-"^100)
    println("z_matched(d, ang) SURFACE  (NaN = band could not populate at that (d,ang)):")
    print(lpad("ang", 8))
    for d in dims; print(lpad("z(d=$d)", 12)); end
    print("   ", lpad("pop[2,4,8]", 14), lpad("brk[2,4,8]", 14))
    println()
    for (ai, ang) in enumerate(angles)
        print(lpad(round(ang, sigdigits=3), 8))
        for d in dims
            z = z_by_d[d][ai]
            print(lpad(isnan(z) ? "NaN" : string(round(z, sigdigits=4)), 12))
        end
        popstr = "[" * join([pop_by_d[d][ai] ? "1" : "0" for d in dims], ",") * "]"
        brkstr = "[" * join([bracket_by_d[d][ai] ? "1" : "0" for d in dims], ",") * "]"
        print("   ", lpad(popstr, 14), lpad(brkstr, 14))
        println()
    end

    R["angles"] = angles
    R["z_matched_surface"] = surface
    R["band_populated_surface"] = pop_surface
    R["brackets_c_hopf_surface"] = bracket_surface
    R["flat_collapse_surface"] = flat_collapse_surface
    R["c_hopf_surface"] = chopf_surface

    # ============================================================================
    # SIGN ANALYSIS over the angle sweep (the decisive observable).
    # ============================================================================
    # per-d: over the POPULATED angles, fraction with z<0, z>0, and sign stability.
    function leg_stats(zs::Vector{Float64}, pops::Vector{Bool})
        pop_idx = [i for i in eachindex(zs) if pops[i] && isfinite(zs[i])]
        n_pop = length(pop_idx)
        if n_pop == 0
            return Dict("n_populated"=>0, "frac_neg"=>NaN, "frac_pos"=>NaN,
                        "all_neg"=>false, "all_pos"=>false, "sign_stable"=>false,
                        "z_min"=>NaN, "z_max"=>NaN, "z_mean"=>NaN)
        end
        zp = [zs[i] for i in pop_idx]
        n_neg = count(<(0), zp); n_pos = count(>(0), zp)
        return Dict("n_populated"=>n_pop,
                    "frac_neg"=>n_neg/n_pop, "frac_pos"=>n_pos/n_pop,
                    "all_neg"=>(n_neg==n_pop), "all_pos"=>(n_pos==n_pop),
                    "sign_stable"=>(n_neg==n_pop || n_pos==n_pop),
                    "z_min"=>minimum(zp), "z_max"=>maximum(zp), "z_mean"=>mean(zp))
    end

    leg2 = leg_stats(z_by_d[2], pop_by_d[2])
    leg4 = leg_stats(z_by_d[4], pop_by_d[4])
    leg8 = leg_stats(z_by_d[8], pop_by_d[8])

    # frac_split: fraction of swept angles where (z(d=2)>0 AND z(d=4)<0 AND z(d=8)<0) holds,
    # over angles where ALL THREE bands populated (the iter-7 sign-split pattern). Also a
    # looser version requiring only z(d=2)>0 AND z(d>=4)<0 for the d>=4 legs that populated.
    n_split_strict = 0; n_all3_pop = 0
    n_split_loose = 0; n_loose_eligible = 0
    for ai in eachindex(angles)
        p2 = pop_by_d[2][ai] && isfinite(z_by_d[2][ai])
        p4 = pop_by_d[4][ai] && isfinite(z_by_d[4][ai])
        p8 = pop_by_d[8][ai] && isfinite(z_by_d[8][ai])
        if p2 && p4 && p8
            n_all3_pop += 1
            if z_by_d[2][ai] > 0 && z_by_d[4][ai] < 0 && z_by_d[8][ai] < 0
                n_split_strict += 1
            end
        end
        # loose: d=2 positive AND every populated high-d leg negative
        if p2
            highs = Float64[]
            p4 && push!(highs, z_by_d[4][ai]); p8 && push!(highs, z_by_d[8][ai])
            if !isempty(highs)
                n_loose_eligible += 1
                (z_by_d[2][ai] > 0 && all(<(0), highs)) && (n_split_loose += 1)
            end
        end
    end
    frac_split_strict = n_all3_pop > 0 ? n_split_strict / n_all3_pop : NaN
    frac_split_loose  = n_loose_eligible > 0 ? n_split_loose / n_loose_eligible : NaN

    R["sign_analysis"] = Dict(
        "leg_d2" => leg2, "leg_d4" => leg4, "leg_d8" => leg8,
        "frac_split_strict" => frac_split_strict,
        "n_split_strict" => n_split_strict, "n_all3_populated" => n_all3_pop,
        "frac_split_loose" => frac_split_loose,
        "n_split_loose" => n_split_loose, "n_loose_eligible" => n_loose_eligible,
        "definition" => "frac_split_strict = fraction of angles (where all of d=2,4,8 bands populated) with z(d=2)>0 AND z(d=4)<0 AND z(d=8)<0 (iter-7 pattern). leg_dX.frac_neg = fraction of populated angles where z(d=X)<0. sign_stable = z(d=X) keeps one sign across all populated angles.",
    )

    println("-"^100)
    println("LEG STATS over populated angles:")
    for (d, lg) in ((2,leg2),(4,leg4),(8,leg8))
        println("  d=$d: n_pop=", lg["n_populated"],
                "  frac_neg=", isnan(lg["frac_neg"]) ? "NA" : round(lg["frac_neg"],sigdigits=3),
                "  frac_pos=", isnan(lg["frac_pos"]) ? "NA" : round(lg["frac_pos"],sigdigits=3),
                "  sign_stable=", lg["sign_stable"],
                "  z in [", isnan(lg["z_min"]) ? "NA" : round(lg["z_min"],sigdigits=4), ", ",
                            isnan(lg["z_max"]) ? "NA" : round(lg["z_max"],sigdigits=4), "]")
    end
    println("  frac_split_strict (z2>0 & z4<0 & z8<0) = ",
            isnan(frac_split_strict) ? "NA" : round(frac_split_strict,sigdigits=3),
            "  (", n_split_strict, "/", n_all3_pop, ")")
    println("  frac_split_loose  (z2>0 & all high-d<0) = ",
            isnan(frac_split_loose) ? "NA" : round(frac_split_loose,sigdigits=3),
            "  (", n_split_loose, "/", n_loose_eligible, ")")

    # ============================================================================
    # SECONDARY gamma axis (GKSL dissipative strength): is the d=8 sign robust to gamma too?
    # 3 gamma values x angles, d=8 only (the load-bearing suppression leg) + d=2 control.
    # ============================================================================
    gammas = [0.5, 1.0, 1.5]
    gamma_surface = Dict{String,Any}()
    gamma_frac_neg_d8 = Dict{String,Any}()
    gamma_frac_pos_d2 = Dict{String,Any}()
    for gam in gammas
        z8row = Float64[]; pop8row = Bool[]
        z2row = Float64[]; pop2row = Bool[]
        for ang in angles
            c8 = angle_cell(8, ang, SEED; gamma=gam, n_band=800)
            push!(z8row, c8["band_populated"] ? c8["z_matched"] : NaN); push!(pop8row, c8["band_populated"])
            c2 = angle_cell(2, ang, SEED; gamma=gam, n_band=800)
            push!(z2row, c2["band_populated"] ? c2["z_matched"] : NaN); push!(pop2row, c2["band_populated"])
        end
        gamma_surface["gamma_$gam"] = Dict("z_d8"=>z8row, "pop_d8"=>pop8row, "z_d2"=>z2row, "pop_d2"=>pop2row)
        l8 = leg_stats(z8row, pop8row); l2 = leg_stats(z2row, pop2row)
        gamma_frac_neg_d8["gamma_$gam"] = l8["frac_neg"]
        gamma_frac_pos_d2["gamma_$gam"] = l2["frac_pos"]
    end
    R["gamma_axis"] = Dict(
        "gammas" => gammas,
        "surface" => gamma_surface,
        "frac_neg_d8_per_gamma" => gamma_frac_neg_d8,
        "frac_pos_d2_per_gamma" => gamma_frac_pos_d2,
        "note" => "secondary GKSL-strength robustness axis (d=8 suppression leg + d=2 control). Angle axis is load-bearing; this checks the d=8 negative sign is not gamma=1.0-specific.",
    )
    println("-"^100)
    println("SECONDARY gamma axis (d=8 frac_neg / d=2 frac_pos across angles):")
    for gam in gammas
        println("  gamma=$gam:  d=8 frac_neg=",
                isnan(gamma_frac_neg_d8["gamma_$gam"]) ? "NA" : round(gamma_frac_neg_d8["gamma_$gam"],sigdigits=3),
                "   d=2 frac_pos=",
                isnan(gamma_frac_pos_d2["gamma_$gam"]) ? "NA" : round(gamma_frac_pos_d2["gamma_$gam"],sigdigits=3))
    end

    # ============================================================================
    # SEED ROBUSTNESS: re-run the d=8 angle sweep at 2 fresh seeds; is the sign of
    # z(d=8, ang) stable per angle? Also d=2.
    # ============================================================================
    seed_d8 = Dict{String,Any}(); seed_d2 = Dict{String,Any}()
    base_sign8 = [isfinite(z_by_d[8][ai]) ? sign(z_by_d[8][ai]) : NaN for ai in eachindex(angles)]
    base_sign2 = [isfinite(z_by_d[2][ai]) ? sign(z_by_d[2][ai]) : NaN for ai in eachindex(angles)]
    sign8_match_counts = zeros(Int, 2); sign8_total = zeros(Int, 2)
    sign2_match_counts = zeros(Int, 2); sign2_total = zeros(Int, 2)
    for (si, sd) in enumerate((SEED+11, SEED+23))
        z8row = Float64[]; z2row = Float64[]
        for (ai, ang) in enumerate(angles)
            c8 = angle_cell(8, ang, sd; gamma=1.0, n_band=800)
            c2 = angle_cell(2, ang, sd; gamma=1.0, n_band=800)
            z8 = c8["band_populated"] ? c8["z_matched"] : NaN
            z2 = c2["band_populated"] ? c2["z_matched"] : NaN
            push!(z8row, z8); push!(z2row, z2)
            if isfinite(z8) && isfinite(base_sign8[ai])
                sign8_total[si] += 1
                (sign(z8) == base_sign8[ai]) && (sign8_match_counts[si] += 1)
            end
            if isfinite(z2) && isfinite(base_sign2[ai])
                sign2_total[si] += 1
                (sign(z2) == base_sign2[ai]) && (sign2_match_counts[si] += 1)
            end
        end
        seed_d8["seed_$sd"] = z8row; seed_d2["seed_$sd"] = z2row
    end
    seed_d8_frac_match = [sign8_total[i] > 0 ? sign8_match_counts[i]/sign8_total[i] : NaN for i in 1:2]
    seed_d2_frac_match = [sign2_total[i] > 0 ? sign2_match_counts[i]/sign2_total[i] : NaN for i in 1:2]
    R["seed_robust"] = Dict(
        "extra_seeds" => [SEED+11, SEED+23],
        "base_z_d8" => z_by_d[8], "base_z_d2" => z_by_d[2],
        "z_d8_per_seed" => seed_d8, "z_d2_per_seed" => seed_d2,
        "d8_sign_match_frac_per_seed" => seed_d8_frac_match,
        "d2_sign_match_frac_per_seed" => seed_d2_frac_match,
        "note" => "fraction of populated angles where the sign of z(d, ang) at the fresh seed matches the base-seed sign. >=~0.9 => the per-angle sign is seed-stable.",
    )
    seed_d8_stable = all(x -> isfinite(x) && x >= 0.85, seed_d8_frac_match)
    seed_d2_stable = all(x -> isfinite(x) && x >= 0.85, seed_d2_frac_match)
    println("-"^100)
    println("SEED ROBUSTNESS (per-angle sign match vs base seed):")
    println("  d=8 sign-match frac per extra seed: ", round.(seed_d8_frac_match, sigdigits=3), "  stable(>=0.85)=", seed_d8_stable)
    println("  d=2 sign-match frac per extra seed: ", round.(seed_d2_frac_match, sigdigits=3), "  stable(>=0.85)=", seed_d2_stable)

    # ============================================================================
    # Z3 verdict-flip at one representative (d=8, ang ~ 0.9 i.e. the iter-7 angle nearest).
    # ============================================================================
    rep_ai = argmin(abs.(angles .- 0.9))
    rep_ang = angles[rep_ai]
    rep_cell = cells["d8_a$rep_ai"]
    rep_sep = (rep_cell["band_populated"] && isfinite(rep_cell["E_matched_mean"])) ?
              abs(rep_cell["E_hopf_max"] - rep_cell["E_matched_mean"]) : 0.0
    rep_sep = isfinite(rep_sep) ? rep_sep : 0.0
    z3_genuine = z3_separation_obstruction(rep_sep)
    z3_flat    = z3_separation_obstruction(0.0)
    z3_load_bearing = (z3_genuine == "unsat") && (z3_flat == "sat") && (rep_sep > 1e-3)
    R["z3_load_bearing"] = Dict(
        "level" => "d=8, ang=$(round(rep_ang,sigdigits=3)) (nearest to iter-7 ang=0.9)",
        "encoding" => "FREE int sep, FREE bool is_flat; law Or([Not(is_flat), sep==0]); assert is_flat=true + sep==IntVal(measured |E_hopf-E_matched_mean| over the 10% scale-swept matched band). genuine nonzero separation: unsat; flat zero: sat.",
        "measured_separation" => rep_sep,
        "genuine_verdict" => z3_genuine,
        "flat_verdict" => z3_flat,
        "load_bearing_flip" => z3_load_bearing,
    )
    println("-"^100)
    println("Z3 (d=8, ang=", round(rep_ang,sigdigits=3), "): genuine=", z3_genuine, " flat=", z3_flat, " flip=", z3_load_bearing)

    # ============================================================================
    # ANTI-TAUTOLOGY rollups: flat collapse + bracket coverage across the whole grid.
    # ============================================================================
    all_flat_collapse = all(all(flat_by_d[d]) for d in dims)
    all_bracket = all(all(bracket_by_d[d]) for d in dims)
    # band-population coverage per d
    pop_frac = Dict("d$d" => count(pop_by_d[d]) / length(pop_by_d[d]) for d in dims)
    R["anti_tautology"] = Dict(
        "all_flat_controls_collapse" => all_flat_collapse,
        "all_brackets_c_hopf" => all_bracket,
        "band_population_fraction_per_d" => pop_frac,
        "all_clifford_genuine" => all_clifford_genuine,
        "note" => "flat U=I must collapse E to floor at EVERY (d,ang); scale-swept range must bracket c_hopf at EVERY (d,ang); any (d,ang) with band_populated=false is SKIPPED in the sign stats and noted (NaN in the surface).",
    )
    println("-"^100)
    println("ANTI-TAUTOLOGY: all flat collapse=", all_flat_collapse,
            "  all bracket c_hopf=", all_bracket,
            "  all clifford genuine=", all_clifford_genuine)
    println("  band-population fraction per d: ", pop_frac)

    # ============================================================================
    # VERDICT (do NOT collapse a mixed surface).
    # ============================================================================
    # d=8 robustly negative across angles? require: most populated angles negative AND
    # seed-stable per-angle sign AND enough populated angles to judge.
    d8_pop_enough = leg8["n_populated"] >= max(4, ceil(Int, 0.5*N_ANG))
    d8_robust_neg = d8_pop_enough && isfinite(leg8["frac_neg"]) && leg8["frac_neg"] >= 0.7 && seed_d8_stable
    d8_robust_pos = d8_pop_enough && isfinite(leg8["frac_pos"]) && leg8["frac_pos"] >= 0.7 && seed_d8_stable
    d8_sign_wanders = d8_pop_enough && isfinite(leg8["frac_neg"]) && leg8["frac_neg"] > 0.3 && leg8["frac_neg"] < 0.7

    d4_pop_enough = leg4["n_populated"] >= max(4, ceil(Int, 0.5*N_ANG))
    d4_robust_neg = d4_pop_enough && isfinite(leg4["frac_neg"]) && leg4["frac_neg"] >= 0.7
    d4_sign_wanders = d4_pop_enough && isfinite(leg4["frac_neg"]) && leg4["frac_neg"] > 0.3 && leg4["frac_neg"] < 0.7

    d2_pop_enough = leg2["n_populated"] >= max(4, ceil(Int, 0.5*N_ANG))
    d2_robust_pos = d2_pop_enough && isfinite(leg2["frac_pos"]) && leg2["frac_pos"] >= 0.7 && seed_d2_stable
    d2_sign_wanders = d2_pop_enough && isfinite(leg2["frac_pos"]) && leg2["frac_pos"] > 0.3 && leg2["frac_pos"] < 0.7

    # the headline split: d=2 positive-stable AND d>=4 negative-stable, persisting across angles
    split_persists = d2_robust_pos && d4_robust_neg && d8_robust_neg

    overall = if !d8_pop_enough
        # not enough populated angles at d=8 to judge structurality
        "insufficient_d8_population_held_open"
    elseif split_persists
        "sign_split_structural"
    elseif d8_robust_neg && d2_robust_pos && !d4_robust_neg
        # d=8 structural-negative + d=2 structural-positive but d=4 leg wanders/flips
        "mixed_d8_structural_neg_d4_unstable"
    elseif d8_robust_neg && !d2_robust_pos
        # d=8 negative is structural but d=2 is not cleanly positive across angles
        "mixed_d8_structural_neg_d2_unstable"
    elseif d8_sign_wanders || (isfinite(leg8["frac_neg"]) && leg8["frac_neg"] < 0.5)
        # d=8 sign flips with angle / mostly not negative -> iter-7 negative was angle-specific
        "sign_split_angle_artifact"
    else
        "mixed_held_open"
    end

    R["verdict"] = Dict(
        "overall" => overall,
        "iter7_sign_split_at_ang_0p9" => Dict("z_d2"=>1.341, "z_d4"=>-1.008, "z_d8"=>-2.084,
            "note"=>"the single-angle (ang=0.9) iter-7 result this object sweeps; read from substrate_effect_matched_band_results.json"),
        "d8_robust_negative_across_angles" => d8_robust_neg,
        "d8_robust_positive_across_angles" => d8_robust_pos,
        "d8_sign_wanders" => d8_sign_wanders,
        "d4_robust_negative_across_angles" => d4_robust_neg,
        "d4_sign_wanders" => d4_sign_wanders,
        "d2_robust_positive_across_angles" => d2_robust_pos,
        "d2_sign_wanders" => d2_sign_wanders,
        "split_persists_across_angles" => split_persists,
        "frac_split_strict" => frac_split_strict,
        "frac_split_loose" => frac_split_loose,
        "leg_frac_neg" => Dict("d2"=>leg2["frac_neg"], "d4"=>leg4["frac_neg"], "d8"=>leg8["frac_neg"]),
        "leg_frac_pos" => Dict("d2"=>leg2["frac_pos"], "d4"=>leg4["frac_pos"], "d8"=>leg8["frac_pos"]),
        "leg_z_range" => Dict(
            "d2"=>[leg2["z_min"], leg2["z_max"]],
            "d4"=>[leg4["z_min"], leg4["z_max"]],
            "d8"=>[leg8["z_min"], leg8["z_max"]]),
        "seed_d8_sign_stable" => seed_d8_stable,
        "seed_d2_sign_stable" => seed_d2_stable,
        "z3_load_bearing" => z3_load_bearing,
        "all_flat_controls_collapse" => all_flat_collapse,
        "all_brackets_c_hopf" => all_bracket,
        "all_clifford_genuine" => all_clifford_genuine,
        "interpretation" => "The ONLY change vs iter-7 is the rotor angle: ang is swept across $(N_ANG) values in [0.1, pi] (iter-7 fixed ang=0.9), at d in {2,4,8}, with the iter-7 scale-swept commutator-matched-band z discriminator VERBATIM. If z(d=8) stays negative across MOST angles (frac_neg>=0.7) AND is seed-stable per-angle AND the d=2-positive / d>=4-negative split persists -> the iter-7 suppression is a genuine higher-Hopf STRUCTURAL fact, not an ang=0.9 accident (sign_split_structural). If z(d=8) FLIPS sign with angle / is mostly non-negative -> iter-7's negative was angle-specific (sign_split_angle_artifact). MIXED outcomes (e.g. d=8 structural-negative but d=4 wanders, or d=2 not cleanly positive) are reported EXACTLY as which legs are structural and which wander, NOT collapsed into a clean verdict.",
        "decides" => "whether 'genuine geometry suppresses the substrate effect at scale' (iter-7) is a robust finite-carrier fact across rotor angles or an artifact of the single ang=0.9. Caps the finite-carrier substrate arc on the density-operator carrier without PEPS.",
    )

    # F01 / N01 witnesses
    R["F01_witness"] = Dict(
        "finite_carrier" => "density operators in D(C^d), d in {2,4,8}; finite frame set {genuine Hopf rotor at swept ang, flat=I, $(N_RAND) scale-swept random exp(-i s H_rand)} per (d,ang)",
        "finite_probe"   => "$(N_RHO+1) density operators per carrier (20 spinor-derived + 1 maximally-mixed)",
        "finite_operator"=> "dissipative Weyl-L GKSL channel lifted to dim d; genuine Spin(2k+1) Hopf rotor frames at $(N_ANG) swept angles; scale-swept random unitary generators",
        "finite_path"    => "dressed compositions U Phi_WeylL(U' . U) U' at each (d,ang); z_matched(d,ang)=(E_hopf-band_mean)/band_std over the +/-10% commutator-matched scale-swept band",
    )
    R["N01_witness"] = Dict(
        "order_sensitive_control" => "frame conjugation does not commute with the dissipative upper op; [U(ang), H0_d] != 0 co-varies with the dressed-vs-bare gap. The scale-swept band brackets the magnitude of this non-commutation at each angle so z(d,ang) isolates whether geometry carries structure BEYOND it. Geometric (non-temporal) substrate axis; temporal-order spine validated separately in order_null_killtest.jl.",
        "representative_separation" => rep_sep,
        "present_above_floor" => rep_sep > 1e-3,
        "noise_floor" => eps(Float64) * 1.0 * 4.0 * 16.0,
    )

    R["required_negatives"] = ["flat_frame_U_eq_I_each_d_ang", "scale_swept_commutator_matched_random_band_each_d_ang", "bracket_coverage_proof_c_lo_le_c_hopf_le_c_hi_each_d_ang", "seed_resample_sign_each_angle"]
    R["negatives_run"]      = ["flat_frame_U_eq_I_each_d_ang", "scale_swept_commutator_matched_random_band_each_d_ang", "bracket_coverage_proof_c_lo_le_c_hopf_le_c_hi_each_d_ang", "seed_resample_sign_each_angle"]
    R["kill_conditions"]    = [
        "flat frame U=I must collapse E to floor at every (d,ang) (anti-tautology)",
        "the scale-swept band must BRACKET c_hopf (c_lo <= c_hopf <= c_hi) at every populated (d,ang) else the matched comparison is not honest",
        "any (d,ang) where the +/-10% band cannot populate is SKIPPED (NaN in surface) and counted, NOT silently dropped",
        "if z(d=8) sign FLIPS with angle (frac_neg < 0.7) => iter-7's negative was an ang=0.9 accident => sign_split_angle_artifact",
        "if z(d=8) sign is NOT seed-stable per angle => the suppression is a single-seed artifact, not structural",
    ]

    R["tool_manifest"] = Dict(
        "LinearAlgebra" => "load_bearing: svdvals (trace norm), HS norms, opnorm (Hermitian generator normalization), matrix exp (Spin rotors at swept ang / GKSL / scale-swept random U=exp(-i s H_rand)), Clifford anticommutator check; every measured z(d,ang) flows through it.",
        "Statistics"    => "load_bearing: mean/std over the rho ensemble and the scale-swept commutator-matched band; z(d,ang) IS (E-mean)/std; the sign analysis is over those numbers.",
        "Random"        => "load_bearing: random density operators AND the scale-swept random Hermitian generators + log-uniform scales that bracket c_hopf at each angle; plus the 2 resample seeds.",
        "Z3"            => "load_bearing: binds the representative (d=8) separation to flat=>sep==0; verdict flips UNSAT->SAT on the flat control.",
        "JSON"          => "supportive: receipt emission.",
    )
    R["tool_integration_depth"] = Dict("LinearAlgebra"=>"load_bearing","Z3"=>"load_bearing","Random"=>"load_bearing","Statistics"=>"load_bearing","JSON"=>"supportive")
    R["downstream_blocks"] = ["layer-completion","manifold admission","pairwise nesting promotion","coupling","bridge/Xi/Phi0/Axis0","flux/FEP/physics","final_manifold_admission"]
    R["blocked_consumers"] = R["downstream_blocks"]
    R["root_constraints_in_force"] = [
        "F01 finite density-operator carrier / Hopf-rotor (swept ang) + scale-swept random frame set / Weyl GKSL ops / dressed paths at d in {2,4,8}",
        "N01 frame conjugation [U(ang), H0_d] != 0 order-sensitive control (geometric substrate axis); scale-swept band brackets its magnitude at each angle",
    ]
    R["status_ladder"]    = "exists < runs < passes local rerun"
    R["promotion_status"] = "diagnostic_only"

    # JSON spec rejects NaN/Inf: sanitize any non-finite Float to a string sentinel.
    sanitize(x::Float64) = isfinite(x) ? x : "non_finite($x)"
    sanitize(x::AbstractDict) = Dict(k => sanitize(v) for (k,v) in x)
    sanitize(x::AbstractVector) = [sanitize(v) for v in x]
    sanitize(x) = x
    Rclean = sanitize(R)

    open(RESULT_PATH, "w") do io
        JSON.print(io, Rclean, 2); write(io, "\n")
    end

    println("="^100)
    println("OVERALL VERDICT: ", overall)
    println("  d=8 robust-negative across angles=", d8_robust_neg,
            "   d=4 robust-negative=", d4_robust_neg,
            "   d=2 robust-positive=", d2_robust_pos)
    println("  split persists across angles=", split_persists,
            "   frac_split_strict=", isnan(frac_split_strict) ? "NA" : round(frac_split_strict,sigdigits=3))
    println("Wrote: ", RESULT_PATH)
    return R
end

run()
