#!/usr/bin/env julia
# =====================================================================================
# substrate_effect_matched_band.jl  —  ITERATION 7. The Feynman/Popper FALSIFIER of
#   iteration 6's own verdict ("needs_geometric_carrier"), fired BEFORE that verdict is
#   accepted.
#
#   classification = substrate_effect_matched_band_poc ; promotion_allowed = false.
#   DENSITY-OPERATOR ONLY. NO PEPS, NO CTMRG, NO optimization. < 150 s.
# -------------------------------------------------------------------------------------
# OBJECT_ID: substrate_effect_matched_band
#
# THE FLAW iter-6 found in its OWN discriminator (READ from
#   substrate_effect_scale_ladder.jl + its results JSON, not invented):
#     At d=4,8 the genuine higher-Hopf rotor's commutator norm c_hopf = ||[U_hopf, H_Weyl]||
#     sits AT or BELOW the entire 2000-frame Haar-random SU(d) commutator distribution.
#     (d=4: c_hopf=1.456, random c_lo=1.163 -> only 7 frames within 10%; d=8:
#      c_hopf=2.295, random c_lo=3.086 -> c_hopf BELOW the whole band, 0 frames within 10%.)
#     Haar-random SU(d) frames are generically FAR from identity -> HIGH commutator with
#     H_Weyl. So the iter-5 RELATIVE commutator-matched band was EMPTY at d>2 and the
#     iter-5 discriminator could not run. THAT is the SOLE reason iter-6 reported
#     needs_geometric_carrier. It never compared the Hopf rotor to random frames of the
#     SAME (low) commutator norm — because Haar sampling cannot produce them.
#
# THE FIX / FALSIFIER (the ONLY change vs iter-6; everything else is reused verbatim):
#   Replace the Haar-random SU(d) band with a SCALE-SWEPT random ensemble
#       U_rand(s) = exp(-i * s * H_rand),   H_rand = random Hermitian (fixed, unit-ish),
#   with a TUNABLE scale s swept from near-0 (U ~ I, LOW commutator) up to O(1)
#   (HIGH commutator). This makes the random ensemble's ||[U_rand, H_Weyl]|| span a RANGE
#   that BRACKETS the genuine Hopf rotor's (low) c_hopf at each d. Now an equally-non-
#   commuting random frame DOES exist, the iter-5 relative commutator-matched band CAN
#   populate, and z(d) = (E_hopf - band_mean)/band_std can be recomputed against random
#   frames of the SAME commutator norm.
#
#   GENUINE objects reused verbatim from iter-5/iter-6 (read, NOT reinvented):
#     - clifford_gammas(d): Cl(3)/Cl(5)/Cl(7) Hermitian anticommuting gamma towers
#       (Spin(3)/Spin(5)/Spin(7)); anticommutation {Ga,Gb}=2 delta_ab MEASURED, not assumed.
#     - hopf_base / hopf_frame: Hopf moment map psi'.Gamma.psi -> base point; rotor
#       exp(-i ang/2 n.Gamma). The genuine higher-Hopf rotor frame U_hopf(d).
#     - hopf_h0: the genuine n.Gamma GKSL Hamiltonian part at the upper-op Hopf site.
#     - lowering_d: sigma_- lifted to dim d (GKSL jump / sink basin).
#     - gksl_step_evolve: the dissipative Weyl-L GKSL channel Phi_WeylL.
#     - substrate_effect / dressed: E(A) = max_rho ||U Phi(U' rho U) U' - Phi(rho)||_1.
#     - z3_separation_obstruction: the Z3 verdict-flip (flat => sep==0).
#   The DISTINCT psi_A (frame site) / psi_B (upper-op site) split is reused so c_hopf != 0.
#
# CLAIM CEILING: this object MEASURES whether a scale-swept random Hermitian-generator
#   ensemble can POPULATE a +/-10% commutator-matched band AROUND the genuine higher-Hopf
#   rotor at d in {2,4,8}, and IF SO recomputes z(d) = (E_hopf - band_mean)/band_std against
#   that properly-matched band. It tests whether iter-6's needs_geometric_carrier was a
#   genuine PEPS-bound or merely an artifact of Haar sampling missing the low-commutator
#   regime. It does NOT assert layer-completion, manifold admission, coupling, bridge
#   (rho_AB/Xi/Phi0/Axis0), flux, FEP, or physics. A populated band with a stable strongly-
#   negative z is a CANDIDATE geometric suppression fact, NOT a proven nesting layer.
#   promotion_allowed = false.
#
# THE TEST at d in {2,4,8}:
#   (1) PRECONDITION: does the bracketed scale-swept ensemble POPULATE the +/-10%
#       commutator-matched band around c_hopf? Report band_populated and n_matched at
#       each d. If it STILL cannot populate even with near-identity (s->0) sampling, report
#       WHY (the Hopf rotor's commutator structure is unreachable by any random Hermitian
#       generator at scale) -> needs_geometric_carrier_confirmed.
#   (2) With a populated band, recompute z(d) = (E_hopf - band_mean)/band_std. Does the
#       genuine Hopf rotor's substrate effect E_hopf DIFFER from commutator-matched random
#       frames of the SAME commutator norm?
#
# DECISIVE VERDICT (do NOT collapse a mixed series; partial verdicts are reported):
#   - band populates at d=4,8 AND z(d) stays strongly negative / non-zero and seed-stable
#       -> the geometry IS load-bearing as a SUPPRESSION at scale; the finite carrier DOES
#          settle it; iter-6's needs_geometric_carrier was PREMATURE.
#       verdict = substrate_suppression_real_at_scale_finite
#   - band populates and z(d) -> ~0 (Hopf indistinguishable from commutator-matched random)
#       -> iter-6's 'effect' was just the commutator MISMATCH; no geometric signal.
#       verdict = no_geometric_signal_finite
#   - band CANNOT be populated even with near-identity random sampling
#       -> the Hopf rotor's commutator structure is unreachable -> PEPS truly required.
#       verdict = needs_geometric_carrier_confirmed
#   - MIXED (e.g. band populates at d=4 but not d=8) -> reported as MIXED, partial verdict.
#
# ANTI-TAUTOLOGY (preserved at every d):
#   - FLAT control U=I -> E at the noise floor (effect vanishes with no geometry).
#   - BAND COVERAGE proof: report min/max of the scale-swept random commutator norms vs the
#     Hopf c_hopf, proving the bracket [c_rand_lo <= c_hopf <= c_rand_hi].
#   - SEED-STABLE: vary seed, check z-sign stable at each d.
#   - Z3 verdict-flip at the top populated level: genuine separation UNSAT vs flat SAT.
#   - explicit noise floor.
# =====================================================================================

using LinearAlgebra
using Random
using Statistics
import JSON
import Z3

const RESULT_PATH = joinpath(@__DIR__, "substrate_effect_matched_band_results.json")
const SEED   = 20260602
const N_RHO  = 20            # 20 + 1 (maximally-mixed) density operators per carrier
const N_RAND = 2000          # scale-swept random band size (iter-6 band size, verbatim)

# ---------- single-qubit primitives (iter-6 verbatim) ----------
const σ1 = ComplexF64[0 1; 1 0]
const σ2 = ComplexF64[0 -im; im 0]
const σ3 = ComplexF64[1 0; 0 -1]
const I2 = Matrix{ComplexF64}(I, 2, 2)
const SM1 = ComplexF64[0 0; 1 0]   # sigma_- lowering (sink) on one qubit

hs(A)         = sqrt(real(tr(A' * A)))   # Hilbert-Schmidt norm
trace_norm(M) = sum(svdvals(M))          # Schatten-1 (||.||_1) — the metric for E(A)

# =====================================================================================
# GENUINE GEOMETRY per carrier dim d (Clifford gamma towers; anticommutation checked).
# REUSED VERBATIM from substrate_effect_scale_ladder.jl (iter-6).
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
# GENUINE DISSIPATIVE WEYL-GKSL UPPER OP, lifted to dim d (iter-6 verbatim).
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
# random density operators (iter-6 verbatim).
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
# THE FIX: SCALE-SWEPT random unitary U = exp(-i * s * H_rand). H_rand is a random
# Hermitian generator (fixed per frame, normalized so its spectral scale is ~1), and the
# scale s is swept across [s_lo, s_hi]. s->0 gives U ~ I (low commutator with H_Weyl);
# s~O(1) gives a high commutator. The ENSEMBLE thus spans a RANGE of ||[U, H_Weyl]||
# that brackets the genuine Hopf rotor's (low) c_hopf. This is NOT a geometry frame; it
# is the commutator-bracketing control that Haar sampling could not provide.
# =====================================================================================
function rand_hermitian(rng, d)
    A = ComplexF64[randn(rng)+im*randn(rng) for _ in 1:d, _ in 1:d]
    H = (A + A') / 2
    # normalize to unit operator-norm scale so s sets the rotation magnitude directly
    nrm = opnorm(H)
    return nrm < 1e-12 ? H : H / nrm
end
# one scale-swept random unitary at scale s
scale_swept_frame(H_rand, s::Float64) = exp(-im * s * H_rand)

# =====================================================================================
# THE DRESSED CHANNEL and the substrate-effect functional E(A) (iter-6 verbatim).
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
# Z3 load-bearing verdict-flip (iter-6 verbatim): genuine nonzero separation -> UNSAT,
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
# CORE: for one carrier dim d, build the SCALE-SWEPT random ensemble that BRACKETS the
# genuine Hopf rotor's commutator norm, populate the +/-10% commutator-matched band, and
# recompute z(d). The frame site / upper-op site split (psi_A / psi_B) is iter-6 verbatim.
# =====================================================================================
function matched_band_level(d::Int, rng_seed::Int; n_band::Int=N_RAND)
    rng  = MersenneTwister(rng_seed)
    rhos = make_rhos(rng, N_RHO, d)

    # TWO DISTINCT genuine Hopf base spinors (iter-6 verbatim): frame site psi_A != upper-op
    # site psi_B so [U_hopf, H0] != 0 (c_hopf > 0).
    psi_B = ComplexF64[ (k % 2 == 1 ? cos(0.3*k+0.2) : sin(0.4*k+0.1)) +
                        im*(0.2*cos(0.5*k) - 0.1*sin(0.3*k)) for k in 1:d ]   # upper-op site
    psi_B /= norm(psi_B)
    psi_A = ComplexF64[ (k % 2 == 1 ? sin(0.55*k+1.1) : cos(0.27*k+0.6)) +
                        im*(0.35*sin(0.42*k+0.3) - 0.18*cos(0.6*k+0.9)) for k in 1:d ]  # frame site
    psi_A /= norm(psi_A)
    ang = 0.9                                    # iter-5 rotor angle

    g = clifford_gammas(d)
    anticomm_err = clifford_anticomm_err(g)      # genuine-Clifford witness (measured)

    # GENUINE upper op: dissipative Weyl-L GKSL lifted to dim d, at the upper-op Hopf site.
    H0 = hopf_h0(d, psi_B)
    Lm = lowering_d(d)
    PhiWeyl = rho -> gksl_step_evolve(rho, +H0, Lm)

    # genuine irreducible higher-Hopf frame at the DISTINCT frame site, and the flat control
    U_hopf, nhat, nbnorm = hopf_frame(d, psi_A, ang)
    U_flat   = Matrix{ComplexF64}(I, d, d)

    Eh_mean, Eh_max = substrate_effect(PhiWeyl, U_hopf, rhos)
    Ef_mean, Ef_max = substrate_effect(PhiWeyl, U_flat,  rhos)

    noise_floor = eps(Float64) * 1.0 * 4.0 * 16.0

    # commutator generator V = H0 (the GKSL Hamiltonian part) — the non-commutation axis.
    Vop = H0
    comm_norm(U) = hs(U*Vop - Vop*U)
    cg = comm_norm(U_hopf); Eg = Eh_max     # the genuine Hopf rotor's commutator + effect

    # =================================================================================
    # SCALE-SWEPT random band that BRACKETS c_hopf.
    # Sweep s on a log-uniform grid from s_lo (near-identity, low commutator) up to s_hi
    # (high commutator). At each frame: draw a fresh random Hermitian H_rand, draw s
    # log-uniform in [s_lo, s_hi], build U=exp(-i s H_rand), measure its commutator norm
    # and substrate effect. The ensemble's commutator norms span a RANGE around c_hopf.
    # s_lo is taken small enough that the LOWEST random commutator falls BELOW c_hopf
    # (so the bracket lower bound is satisfied); s_hi ~ O(1) so the band straddles upward.
    # =================================================================================
    rng_r = MersenneTwister(rng_seed + 777)
    s_lo = 1e-3                # near-identity floor (low commutator)
    s_hi = 1.5                 # O(1) ceiling (high commutator)
    log_lo, log_hi = log(s_lo), log(s_hi)
    rand_frames = Matrix{ComplexF64}[]
    rand_s = Float64[]
    for _ in 1:n_band
        Hr = rand_hermitian(rng_r, d)
        s  = exp(log_lo + (log_hi - log_lo)*rand(rng_r))   # log-uniform scale
        push!(rand_frames, scale_swept_frame(Hr, s))
        push!(rand_s, s)
    end
    rand_c = [comm_norm(U) for U in rand_frames]
    rand_E = [substrate_effect(PhiWeyl, U, rhos)[2] for U in rand_frames]
    rand_lo, rand_hi = minimum(rand_E), maximum(rand_E)
    rand_mean = mean(rand_E); rand_std = std(rand_E)
    rand_c_lo, rand_c_hi = minimum(rand_c), maximum(rand_c)

    # BAND COVERAGE / BRACKET PROOF: does the scale-swept commutator range straddle c_hopf?
    bracket_lo_ok = rand_c_lo <= cg     # a random frame MORE commuting than the Hopf rotor exists
    bracket_hi_ok = rand_c_hi >= cg     # a random frame LESS commuting than the Hopf rotor exists
    brackets_c_hopf = bracket_lo_ok && bracket_hi_ok

    # =================================================================================
    # +/-10% commutator-matched band around c_hopf (the iter-5 RELATIVE band, here at the
    # decisive 10% tolerance, plus 2% and 5% for the knob-robust check). With the
    # scale-swept ensemble the band CAN now populate where Haar sampling left it empty.
    # =================================================================================
    tol_results = Dict{String,Any}(); robust_flags = Bool[]
    ref_mean = NaN; ref_std = NaN; ref_n = 0; z_matched = NaN
    band_populated_10 = false
    for tolfrac in (0.02, 0.05, 0.10)
        tol = tolfrac * max(cg, 1e-9)
        idx = [k for k in 1:n_band if abs(rand_c[k] - cg) <= tol]
        if length(idx) >= 8
            Em = [rand_E[k] for k in idx]; em_mean = mean(Em); em_std = std(Em)
            zmt = em_std > 1e-12 ? (Eg - em_mean)/em_std : 0.0
            # 'outside' = Hopf effect lands outside the matched-random band (>1 std away AND
            # > 0.05 absolute) — i.e. carries structure beyond non-commutation.
            out = abs(Eg - em_mean) > (em_std + 1e-6) && abs(Eg - em_mean) > 0.05
            tol_results["tol_$(tolfrac)"] = Dict("n"=>length(idx), "E_matched_mean"=>em_mean,
                "E_matched_std"=>em_std, "abs_gap"=>abs(Eg-em_mean),
                "z_matched"=>zmt, "outside"=>out)
            push!(robust_flags, out)
            if tolfrac == 0.10                # decisive 10% band = the headline z(d)
                ref_mean = em_mean; ref_std = em_std; ref_n = length(idx)
                z_matched = zmt; band_populated_10 = true
            end
        else
            tol_results["tol_$(tolfrac)"] = Dict("n"=>length(idx), "outside"=>false,
                "note"=>"too few matched (<8) even with scale-swept bracketing")
            push!(robust_flags, false)
        end
    end
    outside_robust = all(robust_flags) && length(robust_flags) == 3

    # full-band z (signed): vs the entire scale-swept random commutator-norm distribution.
    z_full = rand_std > 1e-12 ? (Eg - rand_mean) / rand_std : 0.0

    E_finite = isfinite(Eg) && isfinite(rand_mean) && isfinite(rand_std) && rand_std > 1e-9

    return Dict{String,Any}(
        "d" => d,
        "carrier" => "C^$d ($(round(Int,log2(d)))-qubit density operators)",
        "clifford_anticomm_err" => anticomm_err,
        "clifford_genuine" => anticomm_err < 1e-9,
        "hopf_base_sphere" => "S^$(2*(d==2 ? 1 : d==4 ? 2 : 4))  (moment-map dim $(length(g)))",
        "hopf_base_norm" => nbnorm,
        "E_hopf_mean" => Eh_mean, "E_hopf_max" => Eg,
        "E_flat_max" => Ef_max, "flat_collapses" => Ef_max < noise_floor,
        "noise_floor" => noise_floor,
        "c_hopf" => cg,
        "scale_swept_band" => Dict(
            "n"=>n_band, "s_lo"=>s_lo, "s_hi"=>s_hi,
            "E_mean"=>rand_mean, "E_std"=>rand_std, "E_lo"=>rand_lo, "E_hi"=>rand_hi,
            "c_lo"=>rand_c_lo, "c_hi"=>rand_c_hi,
            "bracket_lo_ok"=>bracket_lo_ok, "bracket_hi_ok"=>bracket_hi_ok,
            "brackets_c_hopf"=>brackets_c_hopf,
            "note"=>"random U=exp(-i s H_rand), s log-uniform in [s_lo,s_hi]; commutator norm spans [c_lo,c_hi] which (if brackets_c_hopf) straddles the Hopf rotor c_hopf",
        ),
        "commutator_matched_10pct" => Dict(
            "c_hopf"=>cg, "E_hopf"=>Eg,
            "E_matched_mean"=>ref_mean, "E_matched_std"=>ref_std, "n_matched"=>ref_n,
            "band_populated"=>band_populated_10,
            "per_tolerance"=>tol_results, "outside_robust"=>outside_robust,
        ),
        # THE z-SERIES ENTRIES
        "z_matched_band" => z_matched,    # vs +/-10% commutator-matched scale-swept random
        "z_full_band"    => z_full,       # vs full scale-swept random band
        "band_populated" => band_populated_10,
        "brackets_c_hopf" => brackets_c_hopf,
        "E_finite" => E_finite,
    )
end

# =====================================================================================
# RUN
# =====================================================================================
function run()
    R = Dict{String,Any}()
    R["object_id"]         = "substrate_effect_matched_band"
    R["sim_id"]            = "substrate_effect_matched_band"
    R["name"]              = "Scale-swept commutator-matched band falsifier of iter-6 needs_geometric_carrier (density-operator only, NO PEPS)"
    R["version"]           = "1.0"
    R["classification"]    = "substrate_effect_matched_band_poc"
    R["promotion_allowed"] = false
    R["sim_execution_kind"]= "nonclassical_poc"
    R["sim_class"]         = "geometry_probe"
    R["script"]            = "substrate_effect_matched_band.jl"
    R["seed"]              = SEED
    R["n_rho"]             = N_RHO + 1
    R["n_random_band"]     = N_RAND
    R["non_numpy"]         = true
    R["bloch_free"]        = true
    R["carrier_layer"]     = "density operators in D(C^d), d in {2,4,8}; genuine higher-Hopf rotor frames (Spin(3)/Spin(5)/Spin(7)) from Clifford gamma towers (iter-6 verbatim); dissipative Weyl-L GKSL upper op lifted to dim d. NO CTMRG, NO PEPS, NO optimization."
    R["geometry_layer"]    = "Clifford gamma towers Cl(3)/Cl(5)/Cl(7) (anticommutation verified); Hopf moment map psi'.Gamma.psi -> base sphere; Spin rotor exp(-i ang/2 n.Gamma) (reused from substrate_effect_scale_ladder.jl / substrate_effect_frame_conjugation.jl)"
    R["finite_map"]        = "(carrier dim d, genuine Hopf frame U_hopf(d) in Spin(2k+1)) |-> dressed dissipative-Weyl channel Phi_B^A(rho)=U Phi_WeylL(U' rho U) U'; observable z(d)=(E_hopf - band_mean)/band_std over a SCALE-SWEPT commutator-matched random band U_rand=exp(-i s H_rand) bracketing c_hopf"
    R["domain"]            = "for each d in {2,4,8}: finite set of $(N_RHO+1) density operators; frame set {genuine Hopf rotor, flat=I, 2000 scale-swept random U=exp(-i s H_rand)}; upper op = Weyl-L GKSL lifted to dim d"
    R["codomain_or_output"]= "per-d band_populated flag + n_matched + bracket coverage (c_lo/c_hi vs c_hopf); z-vs-d series {z(2),z(4),z(8)} (10% matched-band and full-band); seed-robust z-sign; Z3 verdict-flip at top populated level"
    R["spinor_state"]      = "unit spinors on S^3/S^7/S^15 -> Hopf base via moment map; Spin(2k+1) rotor frames; GKSL state from Hopf-site Hamiltonian H0_d = n.Gamma"
    R["quaternion_action"] = "C^4 frame is Spin(5)=Sp(2) (quaternionic Hopf); C^8 is Spin(7) (octonionic Hopf); scale-swept control frames are exp(-i s H_rand), NOT geometry frames"
    R["dependency_receipts"] = [
        "layers/substrate_effect_scale_ladder.jl (iter-6 object under test; genuine Clifford gamma towers + Hopf rotors + Weyl-L GKSL + z/Z3 discipline reused verbatim; THIS object falsifies its needs_geometric_carrier verdict)",
        "layers/substrate_effect_scale_ladder_results.json (iter-6 result: c_hopf below Haar band at d>2 -> empty matched band)",
        "layers/substrate_effect_frame_conjugation.jl (iter-5 validated commutator-matched paired discriminator + dissipative Weyl-L GKSL upper op)",
        "layers/order_null_killtest.jl (genuine Weyl GKSL gksl_step_evolve + hopf_h0 + noise-floor/Z3 discipline)",
        "layers/G_hopf_fibration.jl (Hopf representative spinor / moment map)",
        "layers/clifford_rotor_spinor_network_entanglement.jl (Clifford gamma generators / SU(2) rotor)",
        "layers/L7_layer_bf.jl (per-sheet Weyl GKSL channel)",
    ]
    R["claim_ceiling"] = "MEASURES whether a scale-swept random Hermitian-generator ensemble U=exp(-i s H_rand) populates a +/-10% commutator-matched band around the genuine higher-Hopf rotor at d in {2,4,8}, and IF SO recomputes z(d)=(E_hopf-band_mean)/band_std against that properly-matched band. Tests whether iter-6's needs_geometric_carrier was a genuine PEPS-bound or an artifact of Haar sampling missing the low-commutator regime. Does NOT assert layer-completion / manifold admission / coupling / bridge / flux / FEP / physics. A populated band with stable strongly-negative z is a CANDIDATE geometric suppression fact, NOT a proven nesting layer. promotion_allowed=false."

    println("="^96)
    println("SUBSTRATE-EFFECT MATCHED BAND  (object_id=substrate_effect_matched_band)  ITER-7 FALSIFIER")
    println("  classification=substrate_effect_matched_band_poc  promotion_allowed=false")
    println("  fix: scale-swept random U=exp(-i s H_rand) brackets the Hopf rotor's LOW commutator")
    println("  question: was iter-6 needs_geometric_carrier real, or a Haar-sampling artifact?")
    println("="^96)

    dims = [2, 4, 8]
    levels = Dict{String,Any}()
    z_matched_series = Float64[]
    z_full_series    = Float64[]
    band_pop_series  = Bool[]
    bracket_series   = Bool[]
    n_matched_series = Int[]
    all_clifford_genuine = true
    all_flat_collapse    = true

    for d in dims
        lv = matched_band_level(d, SEED)
        levels["d$d"] = lv
        push!(z_matched_series, isnan(lv["z_matched_band"]) ? NaN : lv["z_matched_band"])
        push!(z_full_series, lv["z_full_band"])
        push!(band_pop_series, lv["band_populated"])
        push!(bracket_series, lv["brackets_c_hopf"])
        push!(n_matched_series, lv["commutator_matched_10pct"]["n_matched"])
        all_clifford_genuine &= lv["clifford_genuine"]
        all_flat_collapse    &= lv["flat_collapses"]

        sb = lv["scale_swept_band"]; cm = lv["commutator_matched_10pct"]
        println("-"^96)
        println("d=$d  carrier=", lv["carrier"], "  Hopf base=", lv["hopf_base_sphere"],
                "  clifford_anticomm_err=", round(lv["clifford_anticomm_err"],sigdigits=3))
        println("   c_hopf=", round(lv["c_hopf"],sigdigits=5),
                "   scale-swept random c in [", round(sb["c_lo"],sigdigits=4), ", ", round(sb["c_hi"],sigdigits=4),
                "]  brackets_c_hopf=", sb["brackets_c_hopf"],
                " (lo_ok=", sb["bracket_lo_ok"], " hi_ok=", sb["bracket_hi_ok"], ")")
        println("   E_hopf(max)=", round(lv["E_hopf_max"],sigdigits=5),
                "  E_flat(max)=", round(lv["E_flat_max"],sigdigits=3),
                "  flat_collapses=", lv["flat_collapses"])
        emm = cm["E_matched_mean"]; ems = cm["E_matched_std"]
        emm_s = (emm isa Number && !isnan(emm)) ? string(round(emm,sigdigits=4)) : "NA"
        ems_s = (ems isa Number && !isnan(ems)) ? string(round(ems,sigdigits=3)) : "NA"
        println("   +/-10% matched band: n_matched=", cm["n_matched"],
                "  band_populated=", cm["band_populated"],
                "  E_matched=", emm_s, "+/-", ems_s)
        zm = lv["z_matched_band"]; zf = lv["z_full_band"]
        println("   >> z_matched(d=$d)=", isnan(zm) ? "NA(band empty)" : round(zm,sigdigits=4),
                "   z_full(d=$d)=", round(zf,sigdigits=4),
                "   outside_robust=", cm["outside_robust"])
    end
    R["levels"] = levels

    # =====================================================================
    # PRECONDITION (Test 1): did the bracketed band populate at each d?
    # =====================================================================
    band_populated_all = all(band_pop_series)
    band_populated_high_d = band_pop_series[2] && band_pop_series[3]   # d=4 AND d=8
    R["precondition"] = Dict(
        "band_populated_per_d" => Dict("d2"=>band_pop_series[1], "d4"=>band_pop_series[2], "d8"=>band_pop_series[3]),
        "n_matched_per_d"      => Dict("d2"=>n_matched_series[1], "d4"=>n_matched_series[2], "d8"=>n_matched_series[3]),
        "brackets_c_hopf_per_d"=> Dict("d2"=>bracket_series[1], "d4"=>bracket_series[2], "d8"=>bracket_series[3]),
        "band_populated_all_d" => band_populated_all,
        "band_populated_high_d_d4_d8" => band_populated_high_d,
        "note" => "Test-1 precondition: a +/-10% commutator-matched band around the Hopf rotor must have >=8 scale-swept random frames before z(d) is a valid same-commutator comparison. brackets_c_hopf proves the scale-swept range straddles c_hopf.",
    )

    # =====================================================================
    # Test 2: z(d) recomputed against the populated matched band.
    # =====================================================================
    R["z_series"] = Dict(
        "dims" => dims,
        "z_matched_band" => z_matched_series,   # 10% commutator-matched scale-swept random
        "z_full_band"    => z_full_series,
        "band_populated_per_d" => band_pop_series,
        "n_matched_per_d" => n_matched_series,
        "definition" => "z(d) = (E_hopf(d) - band_mean(d)) / band_std(d) over the +/-10% commutator-matched SCALE-SWEPT random band U=exp(-i s H_rand). SIGNED: z<0 means the genuine Hopf rotor produces LESS substrate effect than scale-swept random frames of the SAME commutator norm.",
    )

    # =====================================================================
    # SEED-ROBUST: re-run with 2 fresh seeds, check band populates + z-sign stable.
    # =====================================================================
    seed_z = Dict{String,Any}(); seed_pop = Dict{String,Any}()
    sign_stable = Dict(d => true for d in dims)
    pop_stable  = Dict(d => true for d in dims)
    base_sign = Dict(d => (isfinite(z_matched_series[i]) ? sign(z_matched_series[i]) : NaN) for (i,d) in enumerate(dims))
    for sd in (SEED+11, SEED+23)
        zrow = Float64[]; prow = Bool[]
        for d in dims
            lv = matched_band_level(d, sd; n_band=800)
            zz = lv["z_matched_band"]
            push!(zrow, isnan(zz) ? NaN : zz)
            push!(prow, lv["band_populated"])
        end
        seed_z["seed_$sd"] = zrow; seed_pop["seed_$sd"] = prow
        for (i,d) in enumerate(dims)
            (isfinite(zrow[i]) && isfinite(z_matched_series[i]) && sign(zrow[i]) == base_sign[d]) || (sign_stable[d] = false)
            (prow[i] == band_pop_series[i]) || (pop_stable[d] = false)
        end
    end
    seed_robust_sign = sign_stable[4] && sign_stable[8]
    seed_robust_pop  = pop_stable[4] && pop_stable[8]
    R["seed_robust"] = Dict(
        "base_seed" => SEED, "base_z_matched" => z_matched_series,
        "extra_seeds" => [SEED+11, SEED+23],
        "z_matched_per_seed" => seed_z, "band_populated_per_seed" => seed_pop,
        "z_sign_stable_per_d" => Dict("d$d"=>sign_stable[d] for d in dims),
        "band_populated_stable_per_d" => Dict("d$d"=>pop_stable[d] for d in dims),
        "z_sign_robust_high_d_d4_d8" => seed_robust_sign,
        "band_pop_robust_high_d_d4_d8" => seed_robust_pop,
    )

    # =====================================================================
    # Z3 verdict-flip at the TOP POPULATED level: genuine separation UNSAT vs flat SAT.
    # =====================================================================
    # pick the highest d whose band populated; if none, fall back to d=8.
    top_d = band_pop_series[3] ? 8 : (band_pop_series[2] ? 4 : (band_pop_series[1] ? 2 : 8))
    top = levels["d$top_d"]; cm = top["commutator_matched_10pct"]
    top_sep = (cm["band_populated"] && !isnan(cm["E_matched_mean"])) ?
              abs(cm["E_hopf"] - cm["E_matched_mean"]) : 0.0
    top_sep = isnan(top_sep) ? 0.0 : top_sep
    z3_genuine = z3_separation_obstruction(top_sep)
    z3_flat    = z3_separation_obstruction(0.0)
    z3_load_bearing = (z3_genuine == "unsat") && (z3_flat == "sat") && (top_sep > 1e-3)
    R["z3_load_bearing"] = Dict(
        "level" => "d=$top_d (top populated)",
        "encoding" => "FREE int sep, FREE bool is_flat; law Or([Not(is_flat), sep==0]); assert is_flat=true + sep==IntVal(measured |E_hopf-E_matched_mean| over the 10% scale-swept matched band). genuine nonzero separation: unsat; flat zero: sat.",
        "measured_separation" => top_sep,
        "genuine_verdict" => z3_genuine,
        "flat_verdict" => z3_flat,
        "load_bearing_flip" => z3_load_bearing,
    )

    # =====================================================================
    # OVERALL VERDICT (do NOT collapse a mixed series; partial verdicts reported)
    # =====================================================================
    # z magnitude / non-zero check on the POPULATED high-d levels (d=4,d=8 are the iter-6
    # question). "strongly non-zero" = |z| > 1 (Hopf >1 matched-band std from the band).
    z4 = z_matched_series[2]; z8 = z_matched_series[3]
    z4_strong = isfinite(z4) && abs(z4) > 1.0
    z8_strong = isfinite(z8) && abs(z8) > 1.0
    z4_near0  = isfinite(z4) && abs(z4) < 0.5
    z8_near0  = isfinite(z8) && abs(z8) < 0.5

    overall = if !band_populated_high_d && !band_pop_series[2] && !band_pop_series[3]
        # band cannot be populated at either d=4 or d=8 even with near-identity sampling
        "needs_geometric_carrier_confirmed"
    elseif band_populated_high_d && z4_strong && z8_strong && seed_robust_sign
        # band populates AND z strongly non-zero AND seed-stable at d=4,8
        "substrate_suppression_real_at_scale_finite"
    elseif band_populated_high_d && z4_near0 && z8_near0
        # band populates but Hopf indistinguishable from commutator-matched random
        "no_geometric_signal_finite"
    elseif band_pop_series[2] != band_pop_series[3]
        # band populates at one high-d but not the other -> MIXED, held open
        "mixed_band_population_held_open"
    elseif band_populated_high_d
        # populated, but z not cleanly strong-and-stable or near-zero -> mixed magnitude
        "mixed_z_magnitude_held_open"
    else
        "mixed_band_population_held_open"
    end

    # the specific iter-6 falsification status
    iter6_premature = (overall == "substrate_suppression_real_at_scale_finite")
    iter6_confirmed = (overall == "needs_geometric_carrier_confirmed")

    R["verdict"] = Dict(
        "overall" => overall,
        "iter6_needs_geometric_carrier_premature" => iter6_premature,
        "iter6_needs_geometric_carrier_confirmed" => iter6_confirmed,
        "band_populated_per_d" => Dict("d2"=>band_pop_series[1], "d4"=>band_pop_series[2], "d8"=>band_pop_series[3]),
        "n_matched_per_d"      => n_matched_series,
        "brackets_c_hopf_per_d"=> bracket_series,
        "z_matched_series" => z_matched_series,
        "z_full_series" => z_full_series,
        "z4_strong_nonzero" => z4_strong, "z8_strong_nonzero" => z8_strong,
        "z4_near_zero" => z4_near0, "z8_near_zero" => z8_near0,
        "seed_robust_z_sign_high_d" => seed_robust_sign,
        "seed_robust_band_pop_high_d" => seed_robust_pop,
        "z3_load_bearing" => z3_load_bearing,
        "all_flat_controls_collapse" => all_flat_collapse,
        "all_clifford_genuine" => all_clifford_genuine,
        "interpretation" => "The ONLY change vs iter-6 is the random control: a SCALE-SWEPT ensemble U=exp(-i s H_rand) (s log-uniform in [1e-3, 1.5]) whose commutator norm RANGE brackets the genuine Hopf rotor's LOW commutator c_hopf, where Haar-random SU(d) sampling could not reach. If the +/-10% commutator-matched band now POPULATES at d=4 AND d=8 and z(d) stays strongly negative and seed-stable, the Hopf rotor produces LESS substrate effect than commutator-matched random frames -> the geometry is load-bearing as a SUPPRESSION at scale and iter-6's needs_geometric_carrier was PREMATURE (it had the wrong random comparison). If the band populates but z->0, iter-6's effect was just the commutator mismatch -> no_geometric_signal_finite. If even near-identity scale-swept sampling cannot populate the band, the Hopf rotor's commutator structure is genuinely unreachable -> needs_geometric_carrier_confirmed (PEPS required). MIXED band population (one high-d populates, the other does not) is held open as a partial verdict, NOT collapsed.",
        "decides" => "whether iter-6's needs_geometric_carrier is a genuine finite-carrier exhaustion (PEPS-bound) or an artifact of using Haar-random (not commutator-matched) frames as the comparison band. A scale-swept bracketing band that populates + a stable z settles the iter-6 question on the density-operator carrier without PEPS.",
    )

    # F01 / N01 witnesses
    R["F01_witness"] = Dict(
        "finite_carrier" => "density operators in D(C^d), d in {2,4,8}; finite frame set {genuine Hopf rotor, flat=I, 2000 scale-swept random exp(-i s H_rand)} per d",
        "finite_probe"   => "$(N_RHO+1) density operators per carrier (20 spinor-derived + 1 maximally-mixed)",
        "finite_operator"=> "dissipative Weyl-L GKSL channel lifted to dim d; genuine Spin(2k+1) Hopf rotor frames; scale-swept random unitary generators",
        "finite_path"    => "dressed compositions U Phi_WeylL(U' . U) U' at each d; z(d)=(E_hopf-band_mean)/band_std over the +/-10% commutator-matched scale-swept band",
    )
    R["N01_witness"] = Dict(
        "order_sensitive_control" => "frame conjugation does not commute with the dissipative upper op; [U, H0_d] != 0 drives the dressed-vs-bare gap. The scale-swept band brackets the magnitude of this non-commutation so the matched-band z isolates whether geometry carries structure BEYOND it. Geometric (non-temporal) substrate axis; temporal-order spine validated separately in order_null_killtest.jl.",
        "top_level_separation" => top_sep,
        "present_above_floor" => top_sep > 1e-3,
        "noise_floor" => eps(Float64) * 1.0 * 4.0 * 16.0,
    )

    R["required_negatives"] = ["flat_frame_U_eq_I_each_d", "scale_swept_commutator_matched_random_band_each_d", "bracket_coverage_proof_c_lo_le_c_hopf_le_c_hi"]
    R["negatives_run"]      = ["flat_frame_U_eq_I_each_d", "scale_swept_commutator_matched_random_band_each_d", "bracket_coverage_proof_c_lo_le_c_hopf_le_c_hi"]
    R["kill_conditions"]    = [
        "flat frame U=I must collapse E to floor at every d (anti-tautology)",
        "the scale-swept band must BRACKET c_hopf (c_lo <= c_hopf <= c_hi) else the matched comparison is not honest",
        "if the +/-10% band cannot populate even with near-identity (s->0) sampling => Hopf commutator structure unreachable => needs_geometric_carrier_confirmed",
        "if z(d)->0 with a populated band => Hopf indistinguishable from commutator-matched random => no geometric signal (iter-6 effect was commutator mismatch)",
        "z-sign must be seed-stable at d=4,8 else the suppression is a single-seed artifact",
    ]

    R["tool_manifest"] = Dict(
        "LinearAlgebra" => "load_bearing: svdvals (trace norm), HS norms, opnorm (Hermitian generator normalization), matrix exp (Spin rotors / GKSL / scale-swept random U=exp(-i s H_rand)), Clifford anticommutator check; every measured number flows through it.",
        "Statistics"    => "load_bearing: mean/std over the rho ensemble and the scale-swept commutator-matched band; the z(d) observable IS (E-mean)/std.",
        "Random"        => "load_bearing: random density operators AND the 2000-frame scale-swept random Hermitian generators + log-uniform scales that bracket c_hopf.",
        "Z3"            => "load_bearing: binds the measured top-populated-level separation to flat=>sep==0; verdict flips UNSAT->SAT on the flat control.",
        "JSON"          => "supportive: receipt emission.",
    )
    R["tool_integration_depth"] = Dict("LinearAlgebra"=>"load_bearing","Z3"=>"load_bearing","Random"=>"load_bearing","Statistics"=>"load_bearing","JSON"=>"supportive")
    R["downstream_blocks"] = ["layer-completion","manifold admission","pairwise nesting promotion","coupling","bridge/Xi/Phi0/Axis0","flux/FEP/physics","final_manifold_admission"]
    R["blocked_consumers"] = R["downstream_blocks"]
    R["root_constraints_in_force"] = [
        "F01 finite density-operator carrier / Hopf-rotor + scale-swept random frame set / Weyl GKSL ops / dressed paths at d in {2,4,8}",
        "N01 frame conjugation [U, H0_d] != 0 order-sensitive control (geometric substrate axis); scale-swept band brackets its magnitude",
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

    println("-"^96)
    println("PRECONDITION (Test 1): +/-10% commutator-matched band populated per d (d=2,4,8): ", band_pop_series,
            "   n_matched=", n_matched_series)
    println("   bracket c_lo <= c_hopf <= c_hi per d: ", bracket_series)
    println("z_matched series (C^2,C^4,C^8): ", round.(z_matched_series, sigdigits=4))
    println("z_full    series (C^2,C^4,C^8): ", round.(z_full_series, sigdigits=4))
    println("seed-robust z-sign high_d(d4,d8)=", seed_robust_sign, "  band-pop high_d=", seed_robust_pop)
    println("Z3 (d=$top_d top populated): genuine=", z3_genuine, " flat=", z3_flat, " flip=", z3_load_bearing)
    println("all flat collapse=", all_flat_collapse, "  all clifford genuine=", all_clifford_genuine)
    println("-"^96)
    println("OVERALL VERDICT: ", overall)
    println("  iter-6 needs_geometric_carrier PREMATURE: ", iter6_premature,
            "   CONFIRMED: ", iter6_confirmed)
    println("Wrote: ", RESULT_PATH)
    return R
end

run()
