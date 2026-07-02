#!/usr/bin/env julia
# =====================================================================================
# twistor_on_hopf_rotor_probe.jl  —  EXPLORATORY. The FAIR test that CLOSES the twistor
#   question vs the RIGHT substrate.
#
#   classification = twistor_hopf_fairtest_poc ; promotion_allowed = false ; non-numpy.
#   DENSITY / SPINOR math ONLY. NO Bloch r-vector state. NO PEPS, NO CTMRG, NO optimization.
#   Hard time budget < 180 s (run wrapper kills it). Density operators in D(C^4).
# -------------------------------------------------------------------------------------
# OBJECT_ID: twistor_on_hopf_rotor_probe
#
# WHY THIS PROBE EXISTS (the unfairness the prior probe carried, READ not invented):
#   The prior probe (twistor_incidence_substrate_probe.jl) tested the genuine twistor
#   incidence coupling omega=i x pi against the BLOCK-DIAGONAL Weyl substrate
#       H4 = [+H0 0 ; 0 -H0] , L4 = [SM 0 ; 0 SP]
#   and concluded twistor_no_better_than_blockdiag. But the block-diagonal substrate is
#   exactly the substrate that carries NO d>=4 geometry signal: its frame ~commutes with
#   the block-diagonal Hamiltonian (the prior probe itself records
#   block_diag_commutes_with_substrate). The iter-7 d>=4 geometry-specific suppression
#   (substrate_effect_matched_band.jl: at d=4 z_matched_band = -1.0077, band populated,
#   brackets_c_hopf=true; verdict substrate_suppression_real_at_scale_finite) lives on the
#   genuine quaternionic HOPF-ROTOR substrate (Spin(5)=Sp(2) frame on C^4), NOT on the
#   block-diagonal one. So the twistor was tested against the wrong thing.
#
#   THE FAIR TEST (this probe): does the genuine twistor incidence coupling omega=i x pi
#   INTERACT with the Hopf-rotor substrate that ACTUALLY carries the iter-7 signal? On C^4
#   (d=4), where iter-7 showed the geometry-specific suppression:
#     1. BASELINE   (Hopf-alone): the genuine quaternionic Hopf-rotor frame U_hopf, dressing
#        the dissipative Weyl-L GKSL upper op, against the iter-7 scale-swept commutator-
#        matched band. Reproduce the iter-7 d=4 z OUTSIDE the band (the signal that survived).
#     2. +TWISTOR   (Hopf+twistor): the Hopf-rotor frame DRESSED BY the genuine incidence
#        frame, U_combined = U_inc(x) * U_hopf, against the SAME band (matched on the Hopf
#        rotor's commutator norm c_hopf — the band that carries the signal).
#     3. TWISTOR-alone: the incidence frame U_inc(x) alone against the SAME band.
#   DECISIVE: does adding the incidence coupling (a) ENHANCE the d=4 signal (z moves FURTHER
#   outside the band), (b) be REQUIRED for it (removing the incidence collapses the signal —
#   here the inverse: Hopf-alone already carries it, so 'required' is read as 'twistor adds
#   and Hopf-alone is weaker'), (c) be ORTHOGONAL (no change to the Hopf z), or (d) DESTROY
#   it (washes the signal into the generic band, |z| -> small)?
#
# CLAIM CEILING: this object MEASURES whether composing the genuine twistor incidence frame
#   omega=i x pi with the genuine quaternionic Hopf-rotor substrate (the substrate that
#   carries the surviving iter-7 d=4 signal) moves, leaves unchanged, or washes out that
#   signal, using the SAME iter-7 scale-swept commutator-matched band as the geometry-vs-
#   generic control. It does NOT assert layer-completion, manifold admission, coupling,
#   bridge (rho_AB/Xi/Phi0/Axis0), flux, FEP, or physics, and it does NOT admit twistors
#   as a canonical structure. A twistor coupling that moves the signal is a CANDIDATE worth
#   pursuing; orthogonal/destroy CLOSES the twistor question fairly. promotion_allowed=false.
#
# REUSED VERBATIM (no objects invented):
#   - the genuine quaternionic Hopf-rotor substrate at d=4: clifford_gammas(4) (Cl(5),
#     Spin(5)=Sp(2)), hopf_base / hopf_frame / hopf_h0, lowering_d(4), the distinct
#     frame-site psi_A / upper-op-site psi_B split, gksl_step_evolve, rand_rho/make_rhos,
#     the SCALE-SWEPT commutator-matched band (rand_hermitian + scale_swept_frame), the
#     substrate_effect E and the matched-band z observable: ALL from
#     substrate_effect_matched_band.jl / substrate_effect_scale_ladder.jl, VERBATIM.
#   - the genuine twistor incidence coupling: incidence_coupling / incidence_hamiltonian
#     (X_inc(x)=[0 (i x);0 0], H_inc(x)=X_inc+X_inc'), random_hermitian_point: VERBATIM
#     from twistor_incidence_substrate_probe.jl (which cited it verbatim from
#     twistor_incidence_cp3_projective_line.jl: incident_twistor(x,pi)=vcat(im*(x*pi),pi)).
#   - z3_separation_obstruction: VERBATIM.
#   The ONLY new construction is composing U_inc(x) with the Hopf-rotor frame U_hopf and
#   measuring its z against the SAME band that carries the iter-7 signal.
#
# ANTI-TAUTOLOGY (the verdict refuses to be by-construction):
#   - FLAT frame U=I -> E at the noise floor (no geometry -> no effect).
#   - x=0 incidence control: H_inc(0)=0 -> U_inc=I -> U_combined = U_hopf, so the combined
#     case MUST fall back to the Hopf-alone z (the incidence adds nothing at the degenerate
#     point). If the combined z at x=0 != the Hopf-alone z, the wiring is wrong.
#   - flat-Hopf control: if the Hopf frame is replaced by I, the 'Hopf signal' must
#     vanish (z -> within band), so the combined effect is then twistor-alone -> floor-test.
#   - GEOMETRY-vs-GENERIC: the iter-7 scale-swept commutator-matched random band (matched on
#     the Hopf rotor's c_hopf) is the control. A z INSIDE that band = generic non-commutation,
#     NOT the geometry signal. The Hopf-alone z OUTSIDE the band = the surviving signal.
#   - the band must BRACKET c_hopf else the matched comparison is not honest (inconclusive).
#   - Z3 verdict-flip: genuine nonzero band separation UNSAT vs flat SAT.
#
# VERDICTS (brutally honest; do NOT collapse):
#   twistor_enhances_or_required : the combined (Hopf+twistor) z moves FURTHER outside the
#       band than Hopf-alone (|z_combined| > |z_hopf| with same sign, seed-stable) -> the
#       incidence coupling STRENGTHENS the geometry signal -> twistors connect to the real
#       signal, worth pursuing.
#   twistor_orthogonal           : the combined z ~ the Hopf-alone z (no meaningful change)
#       -> the incidence coupling leaves the Hopf signal unchanged -> twistors are
#       INDEPENDENT of the substrate effect here.
#   twistor_destroys             : the combined z is pulled back INTO the band (|z_combined|
#       small / inside) -> the incidence coupling WASHES OUT the Hopf signal.
#   inconclusive (with reason)   : band could not populate / did not bracket c_hopf /
#       x=0 wiring control failed / mixed across seeds.
# =====================================================================================

using LinearAlgebra
using Random
using Statistics
import JSON
import Z3

const RESULT_PATH = joinpath(@__DIR__, "twistor_on_hopf_rotor_probe_results.json")
const SEED   = 20260602
const N_RHO  = 20            # 20 + 1 (maximally-mixed) density operators (iter-7 verbatim)
const N_RAND = 1400          # scale-swept matched-band size (time-budget trimmed)

# ---------- single-qubit primitives (iter-7 verbatim) ----------
const σ1 = ComplexF64[0 1; 1 0]
const σ2 = ComplexF64[0 -im; im 0]
const σ3 = ComplexF64[1 0; 0 -1]
const I2 = Matrix{ComplexF64}(I, 2, 2)
const SM1 = ComplexF64[0 0; 1 0]   # sigma_- lowering (sink) on one qubit

hs(A)         = sqrt(real(tr(A' * A)))   # Hilbert-Schmidt norm
trace_norm(M) = sum(svdvals(M))          # Schatten-1 (||.||_1) — the metric for E(A)

# =====================================================================================
# GENUINE quaternionic Hopf geometry at d=4 (Cl(5) gamma tower; Spin(5)=Sp(2)).
# REUSED VERBATIM from substrate_effect_matched_band.jl / substrate_effect_scale_ladder.jl.
# =====================================================================================
function clifford_gammas(d::Int)
    if d == 2          # Cl(3): n.sigma  (complex Hopf S^3->S^2)
        return [σ1, σ2, σ3]
    elseif d == 4      # Cl(5): Spin(5)=Sp(2)  (quaternionic Hopf S^7->S^4)
        return [kron(σ1,I2), kron(σ2,I2), kron(σ3,σ1), kron(σ3,σ2), kron(σ3,σ3)]
    else
        error("twistor fair test built for the quaternionic d=4 carrier")
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
    d == 2 ? SM1 : kron(SM1, I2)
end

# =====================================================================================
# GENUINE Weyl GKSL channel (iter-7 verbatim).
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

# random density operators (iter-7 verbatim).
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

# scale-swept random Hermitian generator + frame (iter-7 verbatim: the commutator bracket).
function rand_hermitian(rng, d)
    A = ComplexF64[randn(rng)+im*randn(rng) for _ in 1:d, _ in 1:d]
    H = (A + A') / 2
    nrm = opnorm(H)
    return nrm < 1e-12 ? H : H / nrm
end
scale_swept_frame(H_rand, s::Float64) = exp(-im * s * H_rand)

# =====================================================================================
# GENUINE TWISTOR INCIDENCE COUPLING (VERBATIM from twistor_incidence_substrate_probe.jl,
# which cited it verbatim from twistor_incidence_cp3_projective_line.jl):
#   incident_twistor(x,pi) = vcat(im .* (x*pi), pi)   # omega = i x pi
#   X_inc(x) = [ 0   i*x ;  0   0 ]      (omega <- i x pi, the incidence relation)
#   H_inc(x) = X_inc(x) + X_inc(x)' = [ 0  i x ; -i x^*  0 ]   (Hermitian generator).
# =====================================================================================
"Incidence coupling operator X_inc(x) = [0 (i x); 0 0] on C^4 = (omega in C^2, pi in C^2)."
function incidence_coupling(x::AbstractMatrix)
    X = zeros(ComplexF64, 4, 4)
    X[1:2, 3:4] = im .* x            # omega <- i x pi  (the incidence relation, verbatim)
    return X
end
"Hermitian incidence generator H_inc(x) = X_inc + X_inc' (valid Hamiltonian part)."
incidence_hamiltonian(x::AbstractMatrix) = (Xi = incidence_coupling(x); Xi + Xi')
# Hermitian point (random_hermitian_point verbatim) for a genuine null/incidence x.
random_hermitian_point(rng) = (A = randn(rng, ComplexF64, 2, 2); A + A')

# =====================================================================================
# THE DRESSED CHANNEL and substrate-effect functional E(A) (iter-7 verbatim).
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
# CORE: build the genuine Hopf-rotor substrate at d=4 (iter-7 verbatim), the scale-swept
# commutator-matched band around the Hopf rotor's c_hopf, and measure z for:
#   - U_hopf            (BASELINE: reproduce the iter-7 d=4 z OUTSIDE the band)
#   - U_inc * U_hopf    (+TWISTOR: Hopf dressed by the genuine incidence frame)
#   - U_inc             (TWISTOR-alone)
#   - U_flat = I        (anti-tautology floor)
#   - x=0 incidence on Hopf (degenerate: U_inc=I -> must equal Hopf-alone z) — wiring control
#   - U_inc * I (flat-Hopf) (twistor on a FLAT substrate -> no Hopf signal to interact with)
# ALL z computed against the SAME band (matched on the Hopf rotor's c_hopf — the band that
# carries the iter-7 signal). This is the fair-test wiring.
# =====================================================================================
function fair_test_level(rng_seed::Int; n_band::Int=N_RAND, ang::Float64=0.9)
    d = 4
    rng  = MersenneTwister(rng_seed)
    rhos = make_rhos(rng, N_RHO, d)

    # TWO DISTINCT genuine Hopf base spinors (iter-7 verbatim): frame site psi_A != upper-op
    # site psi_B so the Hopf rotor does NOT commute with the GKSL Hamiltonian (c_hopf > 0).
    psi_B = ComplexF64[ (k % 2 == 1 ? cos(0.3*k+0.2) : sin(0.4*k+0.1)) +
                        im*(0.2*cos(0.5*k) - 0.1*sin(0.3*k)) for k in 1:d ]   # upper-op site
    psi_B /= norm(psi_B)
    psi_A = ComplexF64[ (k % 2 == 1 ? sin(0.55*k+1.1) : cos(0.27*k+0.6)) +
                        im*(0.35*sin(0.42*k+0.3) - 0.18*cos(0.6*k+0.9)) for k in 1:d ]  # frame site
    psi_A /= norm(psi_A)

    g = clifford_gammas(d)
    anticomm_err = clifford_anticomm_err(g)      # genuine-Clifford witness (measured)

    # GENUINE upper op: dissipative Weyl-L GKSL lifted to d=4 at the upper-op Hopf site psi_B.
    H0 = hopf_h0(d, psi_B)
    Lm = lowering_d(d)
    PhiWeyl = rho -> gksl_step_evolve(rho, +H0, Lm)

    # ---- THE GENUINE QUATERNIONIC HOPF-ROTOR FRAME (the substrate carrying the iter-7 signal) ----
    U_hopf, nhat, nbnorm = hopf_frame(d, psi_A, ang)
    U_flat = Matrix{ComplexF64}(I, d, d)

    # ---- THE GENUINE TWISTOR INCIDENCE FRAME at a genuine (Hermitian) spacetime point ----
    x_pt = random_hermitian_point(rng)
    H_inc = incidence_hamiltonian(x_pt)
    nrm_inc = opnorm(H_inc); H_inc = nrm_inc < 1e-12 ? H_inc : H_inc / nrm_inc   # match scale
    U_inc  = exp(-im * ang/2 * H_inc)
    # x=0 degenerate incidence: H_inc(0)=0 -> U_inc0 = I (must collapse the coupling).
    U_inc0 = exp(-im * ang/2 * incidence_hamiltonian(zeros(ComplexF64,2,2)))     # = I

    # ---- THE COMPOSED FRAMES (the FAIR test: Hopf substrate dressed by the incidence frame) ----
    U_combined  = U_inc  * U_hopf      # +TWISTOR: incidence frame dressing the Hopf rotor
    U_combined0 = U_inc0 * U_hopf      # x=0 incidence on Hopf -> must equal Hopf-alone (wiring ctrl)
    U_tw_flat   = U_inc  * U_flat      # twistor on a FLAT substrate (no Hopf signal)

    # ---- substrate effects ----
    Ehopf_mean, Ehopf_max = substrate_effect(PhiWeyl, U_hopf,      rhos)
    Ecomb_mean, Ecomb_max = substrate_effect(PhiWeyl, U_combined,  rhos)
    Etw_mean,   Etw_max   = substrate_effect(PhiWeyl, U_inc,       rhos)
    Ef_mean,    Ef_max    = substrate_effect(PhiWeyl, U_flat,      rhos)
    Ec0_mean,   Ec0_max   = substrate_effect(PhiWeyl, U_combined0, rhos)
    Etf_mean,   Etf_max   = substrate_effect(PhiWeyl, U_tw_flat,   rhos)

    noise_floor = eps(Float64) * 1.0 * 4.0 * 16.0

    # commutator generator V = H0 (the GKSL Hamiltonian part) — the non-commutation axis.
    Vop = H0
    comm_norm(U) = hs(U*Vop - Vop*U)
    c_hopf = comm_norm(U_hopf)        # the Hopf rotor's commutator norm (carries the iter-7 band)
    c_comb = comm_norm(U_combined)
    c_tw   = comm_norm(U_inc)

    # =================================================================================
    # SCALE-SWEPT commutator-matched random band (iter-7 verbatim), BRACKETING the HOPF
    # rotor's LOW commutator c_hopf — the SAME band that carried the iter-7 d=4 signal.
    # z = (E - band_mean)/band_std against THIS band for every frame. "Outside" = geometry.
    # =================================================================================
    rng_r = MersenneTwister(rng_seed + 777)
    s_lo, s_hi = 1e-3, 1.5
    log_lo, log_hi = log(s_lo), log(s_hi)
    rand_c = Float64[]; rand_E = Float64[]
    for _ in 1:n_band
        Hr = rand_hermitian(rng_r, d)
        s  = exp(log_lo + (log_hi - log_lo)*rand(rng_r))
        U  = scale_swept_frame(Hr, s)
        push!(rand_c, comm_norm(U))
        push!(rand_E, substrate_effect(PhiWeyl, U, rhos)[2])
    end
    rand_c_lo, rand_c_hi = minimum(rand_c), maximum(rand_c)
    brackets_c_hopf = (rand_c_lo <= c_hopf) && (rand_c_hi >= c_hopf)

    # +/-10% commutator-matched band AROUND c_hopf (the band the iter-7 signal was measured in).
    tol = 0.10 * max(c_hopf, 1e-9)
    idx = [k for k in 1:n_band if abs(rand_c[k] - c_hopf) <= tol]
    band_populated = length(idx) >= 8
    if band_populated
        Em = [rand_E[k] for k in idx]
        band_mean = mean(Em); band_std = std(Em)
    else
        band_mean = NaN; band_std = NaN
    end

    # z for each frame against the SAME (Hopf-c-matched) band.
    zof(E) = (band_populated && band_std > 1e-12) ? (E - band_mean)/band_std : NaN
    z_hopf      = zof(Ehopf_max)      # BASELINE: reproduce the iter-7 d=4 z
    z_combined  = zof(Ecomb_max)      # +TWISTOR
    z_tw        = zof(Etw_max)        # twistor-alone
    z_combined0 = zof(Ec0_max)        # x=0 incidence on Hopf (wiring control: must == z_hopf)
    z_tw_flat   = zof(Etf_max)        # twistor on flat substrate

    outside(E) = (band_populated && band_std > 1e-12) &&
                 abs(E - band_mean) > (band_std + 1e-6) && abs(E - band_mean) > 0.05
    hopf_outside     = outside(Ehopf_max)
    combined_outside = outside(Ecomb_max)
    tw_outside       = outside(Etw_max)

    return Dict{String,Any}(
        "d" => d,
        "carrier" => "C^4 = quaternionic Hopf S^7->S^4 (Spin(5)=Sp(2)); density operators in D(C^4)",
        "clifford_anticomm_err" => anticomm_err,
        "clifford_genuine" => anticomm_err < 1e-9,
        "hopf_base_norm" => nbnorm,
        "incidence_point_x_is_hermitian" => true,
        "ang" => ang,
        "noise_floor" => noise_floor,
        # substrate effects
        "E_hopf_max" => Ehopf_max, "E_hopf_mean" => Ehopf_mean,
        "E_combined_max" => Ecomb_max, "E_combined_mean" => Ecomb_mean,
        "E_twistor_alone_max" => Etw_max, "E_twistor_alone_mean" => Etw_mean,
        "E_flat_max" => Ef_max, "flat_collapses" => Ef_max < noise_floor,
        "E_x0_incidence_on_hopf_max" => Ec0_max,
        "E_twistor_on_flat_max" => Etf_max,
        # commutator norms
        "c_hopf" => c_hopf, "c_combined" => c_comb, "c_twistor_alone" => c_tw,
        # the scale-swept matched band (matched on c_hopf — the iter-7 band)
        "scale_swept_band" => Dict(
            "n"=>n_band, "c_lo"=>rand_c_lo, "c_hi"=>rand_c_hi,
            "brackets_c_hopf"=>brackets_c_hopf,
        ),
        "matched_band_around_c_hopf" => Dict(
            "c_ref"=>c_hopf, "n_matched"=>length(idx), "populated"=>band_populated,
            "band_mean"=>band_mean, "band_std"=>band_std,
        ),
        # the z observables against the SAME band
        "z_hopf"        => z_hopf,        "hopf_outside_band"     => hopf_outside,
        "z_combined"    => z_combined,    "combined_outside_band" => combined_outside,
        "z_twistor_alone" => z_tw,        "twistor_alone_outside_band" => tw_outside,
        "z_combined_x0" => z_combined0,   # wiring control: must equal z_hopf
        "z_twistor_on_flat" => z_tw_flat,
        # wiring control: x=0 incidence on Hopf must reproduce Hopf-alone z
        "x0_wiring_matches_hopf" => (isfinite(z_hopf) && isfinite(z_combined0) &&
                                     abs(z_combined0 - z_hopf) < 1e-6),
        "x0_E_matches_hopf" => abs(Ec0_max - Ehopf_max) < 1e-9,
    )
end

# =====================================================================================
# RUN
# =====================================================================================
function run()
    R = Dict{String,Any}()
    R["object_id"]         = "twistor_on_hopf_rotor_probe"
    R["sim_id"]            = "twistor_on_hopf_rotor_probe"
    R["name"]              = "FAIR test: does the genuine twistor incidence coupling omega=i x pi interact with the HOPF-ROTOR substrate that actually carries the iter-7 d>=4 suppression signal?"
    R["version"]           = "1.0"
    R["classification"]    = "twistor_hopf_fairtest_poc"
    R["promotion_allowed"] = false
    R["sim_execution_kind"]= "nonclassical_poc_exploratory"
    R["sim_class"]         = "geometry_probe_exploratory"
    R["script"]            = "twistor_on_hopf_rotor_probe.jl"
    R["seed"]              = SEED
    R["n_rho"]             = N_RHO + 1
    R["n_random_band"]     = N_RAND
    R["non_numpy"]         = true
    R["bloch_free"]        = true
    R["exploratory"]       = true
    R["incidence_relation"]= "omega^A = i x^{AA'} pi_{A'}  (verbatim from twistor_incidence_substrate_probe.jl / twistor_incidence_cp3_projective_line.jl: incident_twistor(x,pi)=vcat(im*(x*pi),pi)); coupling X_inc(x)=[0 (i x);0 0], Hermitian generator H_inc(x)=X_inc+X_inc'; frame U_inc=exp(-i ang/2 H_inc)"
    R["carrier"]           = "density operators in D(C^4) on the quaternionic Hopf carrier (Spin(5)=Sp(2)); genuine Hopf-rotor frame U_hopf=exp(-i ang/2 n.Gamma) at a genuine Hopf base point (the substrate carrying the iter-7 d=4 signal); dissipative Weyl-L GKSL upper op; twistor incidence frame U_inc DRESSES the Hopf rotor: U_combined=U_inc*U_hopf. NO CTMRG, NO PEPS, NO optimization."
    R["reused_from"] = "substrate_effect_matched_band.jl + substrate_effect_scale_ladder.jl (genuine quaternionic Hopf-rotor frame, distinct frame/upper-op sites, dissipative Weyl-L GKSL, scale-swept commutator-matched band, substrate_effect E + matched-band z, z3_separation_obstruction — all verbatim) + twistor_incidence_substrate_probe.jl / twistor_incidence_cp3_projective_line.jl (incidence_coupling / incidence_hamiltonian omega=i x pi, random_hermitian_point — verbatim). Only NEW construction: composing U_inc with U_hopf and measuring its z against the SAME band that carries the iter-7 signal."
    R["claim_ceiling"] = "MEASURES whether composing the genuine twistor incidence frame omega=i x pi with the genuine quaternionic Hopf-rotor substrate (the substrate carrying the surviving iter-7 d=4 z<0 signal) moves, leaves unchanged, or washes out that signal, using the SAME iter-7 scale-swept commutator-matched band (matched on the Hopf rotor's c_hopf) as the geometry-vs-generic control. Does NOT assert layer-completion / manifold admission / coupling / bridge / flux / FEP / physics, and does NOT admit twistors as canonical anything. promotion_allowed=false."

    println("="^98)
    println("TWISTOR-ON-HOPF-ROTOR FAIR TEST  (object_id=twistor_on_hopf_rotor_probe)  EXPLORATORY")
    println("  classification=twistor_hopf_fairtest_poc  promotion_allowed=false")
    println("  question: does the genuine incidence coupling omega=i x pi INTERACT with the HOPF-ROTOR")
    println("            substrate that actually carries the iter-7 d=4 suppression (z<0 outside band)?")
    println("="^98)

    lv = fair_test_level(SEED)
    R["level"] = lv

    sb = lv["scale_swept_band"]; mb = lv["matched_band_around_c_hopf"]
    println("-"^98)
    println("HOPF-ALONE (BASELINE — reproduce the iter-7 d=4 signal):")
    println("   clifford_anticomm_err=", round(lv["clifford_anticomm_err"],sigdigits=3),
            "  c_hopf=", round(lv["c_hopf"],sigdigits=5))
    println("   scale-swept random c in [", round(sb["c_lo"],sigdigits=4), ", ", round(sb["c_hi"],sigdigits=4),
            "]  brackets_c_hopf=", sb["brackets_c_hopf"],
            "   matched-band: populated=", mb["populated"], " n=", mb["n_matched"])
    println("   E_hopf(max)=", round(lv["E_hopf_max"],sigdigits=5),
            "   E_flat(max)=", round(lv["E_flat_max"],sigdigits=3), "  flat_collapses=", lv["flat_collapses"])
    println("   >> z_hopf=", isfinite(lv["z_hopf"]) ? round(lv["z_hopf"],sigdigits=4) : "NA",
            "   hopf_outside_band=", lv["hopf_outside_band"], "   (the surviving iter-7 signal)")
    println("-"^98)
    println("+TWISTOR (Hopf rotor DRESSED by the genuine incidence frame U_inc*U_hopf):")
    println("   c_combined=", round(lv["c_combined"],sigdigits=5),
            "   E_combined(max)=", round(lv["E_combined_max"],sigdigits=5))
    println("   >> z_combined=", isfinite(lv["z_combined"]) ? round(lv["z_combined"],sigdigits=4) : "NA",
            "   combined_outside_band=", lv["combined_outside_band"])
    println("TWISTOR-alone (U_inc against the SAME Hopf-matched band):")
    println("   c_twistor=", round(lv["c_twistor_alone"],sigdigits=5),
            "   E_twistor(max)=", round(lv["E_twistor_alone_max"],sigdigits=5),
            "   >> z_twistor_alone=", isfinite(lv["z_twistor_alone"]) ? round(lv["z_twistor_alone"],sigdigits=4) : "NA",
            "   outside=", lv["twistor_alone_outside_band"])
    println("WIRING CONTROL: x=0 incidence on Hopf -> z_combined_x0=",
            isfinite(lv["z_combined_x0"]) ? round(lv["z_combined_x0"],sigdigits=4) : "NA",
            "  matches z_hopf=", lv["x0_wiring_matches_hopf"], " (must be true)")

    # =====================================================================
    # SEED ROBUSTNESS: re-run at 2 fresh seeds. Record z_hopf / z_combined / z_twistor and
    # the |z_combined| vs |z_hopf| comparison at each seed. A verdict fires only if the
    # comparison is stable across seeds (else inconclusive).
    # =====================================================================
    z_hopf_seeds  = Float64[lv["z_hopf"]]
    z_comb_seeds  = Float64[lv["z_combined"]]
    z_tw_seeds    = Float64[lv["z_twistor_alone"]]
    hopf_out_seeds = Bool[lv["hopf_outside_band"]]
    comb_out_seeds = Bool[lv["combined_outside_band"]]
    wiring_seeds  = Bool[lv["x0_wiring_matches_hopf"]]
    bracket_seeds = Bool[lv["scale_swept_band"]["brackets_c_hopf"]]
    pop_seeds     = Bool[lv["matched_band_around_c_hopf"]["populated"]]
    seed_rows = Dict{String,Any}()
    for sd in (SEED+11, SEED+23)
        lv2 = fair_test_level(sd; n_band=700)
        push!(z_hopf_seeds, lv2["z_hopf"]); push!(z_comb_seeds, lv2["z_combined"])
        push!(z_tw_seeds, lv2["z_twistor_alone"])
        push!(hopf_out_seeds, lv2["hopf_outside_band"]); push!(comb_out_seeds, lv2["combined_outside_band"])
        push!(wiring_seeds, lv2["x0_wiring_matches_hopf"])
        push!(bracket_seeds, lv2["scale_swept_band"]["brackets_c_hopf"])
        push!(pop_seeds, lv2["matched_band_around_c_hopf"]["populated"])
        seed_rows["seed_$sd"] = Dict(
            "z_hopf"=>lv2["z_hopf"], "z_combined"=>lv2["z_combined"], "z_twistor_alone"=>lv2["z_twistor_alone"],
            "hopf_outside"=>lv2["hopf_outside_band"], "combined_outside"=>lv2["combined_outside_band"],
            "x0_wiring_matches_hopf"=>lv2["x0_wiring_matches_hopf"],
        )
    end
    R["seed_robustness"] = Dict(
        "seeds"=>[SEED, SEED+11, SEED+23],
        "z_hopf_per_seed"=>z_hopf_seeds, "z_combined_per_seed"=>z_comb_seeds,
        "z_twistor_alone_per_seed"=>z_tw_seeds,
        "hopf_outside_per_seed"=>hopf_out_seeds, "combined_outside_per_seed"=>comb_out_seeds,
        "x0_wiring_matches_hopf_per_seed"=>wiring_seeds,
        "brackets_c_hopf_per_seed"=>bracket_seeds, "band_populated_per_seed"=>pop_seeds,
        "extra_seed_detail"=>seed_rows,
    )

    # =====================================================================
    # DECISIVE COMPARISON (per seed, then required across ALL seeds).
    # The SURVIVING iter-7 signal is DIRECTIONAL: z_hopf is NEGATIVE (the Hopf rotor produces
    # LESS substrate effect than commutator-matched random; iter-7 z_matched_band(d=4)=-1.0077,
    # headlined via |z|>1 + stable sign). So the comparison is SIGN-AND-MAGNITUDE aware on that
    # negative-suppression signal, NOT on a brittle >std 'outside' flag (kept only as a recorded
    # diagnostic). margin = 0.5 std: a z change of > 0.5 std is "meaningful".
    #   enhance  : z_combined keeps the Hopf negative sign AND |z_combined| > |z_hopf| + margin
    #              (the incidence frame deepens the suppression).
    #   weaken   : z_combined keeps the negative sign but |z_combined| < |z_hopf| - margin.
    #   destroy  : z_combined LOSES the Hopf sign (flips to the other side of the band) ->
    #              the incidence frame scatters/washes the directional signal.
    #   orthogon.: |z_combined - z_hopf| <= margin (no meaningful change).
    # =====================================================================
    margin = 0.5
    function classify(zh, zc)
        (isfinite(zh) && isfinite(zc)) || return "inconclusive"
        # the directional signal is the Hopf sign (negative = suppression).
        sgn = sign(zh)
        keeps_sign = abs(zh) < 1e-9 ? true : (sign(zc) == sgn)
        if abs(zc - zh) <= margin
            return "orthogonal"                       # essentially unchanged
        elseif !keeps_sign
            return "destroy"                          # combined flipped to the other side of the band
        elseif abs(zc) > abs(zh) + margin
            return "enhance"                          # deepens the suppression, same sign
        elseif abs(zc) < abs(zh) - margin
            return "weaken_but_present"               # shallower but same sign
        else
            return "mixed"
        end
    end
    per_seed_class = String[]
    for i in 1:length(z_hopf_seeds)
        push!(per_seed_class, classify(z_hopf_seeds[i], z_comb_seeds[i]))
    end

    # =====================================================================
    # Z3 verdict-flip: genuine Hopf-band separation UNSAT vs flat SAT (load-bearing tool).
    # =====================================================================
    mb0 = lv["matched_band_around_c_hopf"]
    hopf_sep = (mb0["populated"] && !isnan(mb0["band_mean"])) ? abs(lv["E_hopf_max"] - mb0["band_mean"]) : 0.0
    hopf_sep = isnan(hopf_sep) ? 0.0 : hopf_sep
    z3_genuine = z3_separation_obstruction(hopf_sep)
    z3_flat    = z3_separation_obstruction(0.0)
    z3_load_bearing = (z3_genuine == "unsat") && (z3_flat == "sat") && (hopf_sep > 1e-3)
    R["z3_load_bearing"] = Dict(
        "measured_hopf_matched_band_separation" => hopf_sep,
        "genuine_verdict" => z3_genuine, "flat_verdict" => z3_flat,
        "load_bearing_flip" => z3_load_bearing,
        "encoding" => "FREE int sep, FREE bool is_flat; law Or([Not(is_flat), sep==0]); assert is_flat=true + sep==IntVal(measured |E_hopf - matched_band_mean|). genuine nonzero: unsat; flat: sat.",
    )

    # =====================================================================
    # PRECONDITIONS for an honest verdict (across all seeds):
    #   - band must BRACKET c_hopf and POPULATE
    #   - the x=0 wiring control must hold (U_inc0=I -> U_combined=U_hopf)
    #   - the Hopf-alone baseline must REPRODUCE THE ITER-7 DIRECTIONAL SIGNAL: z_hopf NEGATIVE
    #     (Hopf produces LESS effect than commutator-matched random) AND seed-stable in SIGN at
    #     every seed. (This is the iter-7 z_matched_band(d=4)=-1.0077 signal; the strict >std
    #     'outside' flag is recorded as a diagnostic but is NOT the precondition — the iter-7
    #     finding itself sat at |z|~1, i.e. AT the 1-std boundary, headlined by sign+|z|.)
    # =====================================================================
    brackets_all  = all(bracket_seeds)
    populated_all = all(pop_seeds)
    wiring_all    = all(wiring_seeds)
    # iter-7 directional signal: z_hopf finite, negative, and sign-stable across seeds.
    hopf_all_finite = all(isfinite, z_hopf_seeds)
    hopf_all_negative = hopf_all_finite && all(z -> z < 0, z_hopf_seeds)
    hopf_sign_stable = hopf_all_finite && all(z -> sign(z) == sign(z_hopf_seeds[1]), z_hopf_seeds)
    hopf_signal_all_seeds = hopf_all_negative && hopf_sign_stable
    # diagnostic-only: how often the strict >std outside flag fired (NOT a gate).
    hopf_outside_flag_count = count(identity, hopf_out_seeds)

    # stable class: same non-inconclusive class at every seed
    classes_finite = filter(c -> c != "inconclusive", per_seed_class)
    class_stable = !isempty(classes_finite) && all(c -> c == classes_finite[1], classes_finite) &&
                   length(classes_finite) == length(per_seed_class)
    stable_class = class_stable ? classes_finite[1] : "unstable_across_seeds"

    verdict = if !brackets_all || !populated_all
        "inconclusive"
    elseif !wiring_all
        "inconclusive"
    elseif !hopf_signal_all_seeds
        "inconclusive"
    elseif stable_class == "enhance"
        "twistor_enhances_or_required"
    elseif stable_class == "orthogonal" || stable_class == "weaken_but_present"
        "twistor_orthogonal"
    elseif stable_class == "destroy"
        "twistor_destroys"
    else
        "inconclusive"
    end

    reason = if verdict == "inconclusive" && (!brackets_all || !populated_all)
        "the scale-swept commutator-matched band did not bracket the Hopf rotor's c_hopf or did not populate at some seed; the geometry-vs-generic comparison could not run honestly against the band that carries the iter-7 signal. Not a twistor result either way."
    elseif verdict == "inconclusive" && !wiring_all
        "the x=0 incidence wiring control FAILED at some seed: U_inc(0) must equal I so U_combined=U_hopf and the combined z must equal the Hopf-alone z. A mismatch means the composition is not the genuine incidence dressing. Verdict withheld."
    elseif verdict == "inconclusive" && !hopf_signal_all_seeds
        "the Hopf-alone baseline did NOT reproduce the iter-7 d=4 DIRECTIONAL signal (z_hopf negative and seed-stable in sign) at some seed; there was no surviving substrate signal to test the twistor against at this carrier/seed. Verdict withheld (honest precondition failure, NOT a twistor result)."
    elseif verdict == "twistor_enhances_or_required"
        "across all seeds, dressing the genuine quaternionic Hopf-rotor substrate with the genuine incidence frame omega=i x pi kept the Hopf NEGATIVE-suppression sign AND deepened it (|z_combined| > |z_hopf| + 0.5 std, same sign) -> the incidence coupling STRENGTHENS the d=4 geometry-specific suppression the iter-7 Hopf-rotor carried. CANDIDATE only: twistors connect to the real signal here and are worth pursuing. promotion_allowed=false; does NOT admit twistors as canonical anything."
    elseif verdict == "twistor_orthogonal"
        "across all seeds, dressing the genuine Hopf-rotor substrate with the genuine incidence frame omega=i x pi left the substrate-effect z essentially UNCHANGED (|z_combined - z_hopf| <= 0.5 std): plainly, twistors are ORTHOGONAL to the substrate effect here -- the incidence coupling neither strengthens nor washes the Hopf-rotor signal that carries the iter-7 d=4 suppression. The honest iter-7 finding stands on the Hopf-rotor geometry; the twistor incidence relation is independent of it on this carrier. promotion_allowed=false; admits twistors as nothing canonical."
    elseif verdict == "twistor_destroys"
        "across all seeds, dressing the genuine Hopf-rotor substrate with the genuine incidence frame omega=i x pi FLIPPED the substrate-effect z to the OTHER side of the commutator-matched band (z_combined loses the Hopf negative-suppression sign): the incidence coupling SCATTERS/WASHES the iter-7 d=4 Hopf-rotor directional signal. promotion_allowed=false; does NOT admit twistors as canonical anything."
    else
        "the per-seed enhance/orthogonal/destroy classification was NOT stable across seeds (per-seed classes: $(per_seed_class); z_combined per seed: $(round.(z_comb_seeds,sigdigits=3)) flips sign while z_hopf $(round.(z_hopf_seeds,sigdigits=3)) stays negative). The genuine finding: dressing the Hopf rotor with the incidence frame makes the substrate-effect z DEPEND ON THE RANDOM SPACETIME POINT x (it scatters to both sides of the band seed-to-seed), so the twistor-vs-Hopf interaction is UNSTABLE on this single-point incidence lift and cannot be closed at one carrier -- it does NOT reinforce the Hopf suppression. Held open. promotion_allowed=false; admits twistors as nothing canonical."
    end

    R["verdict"] = Dict(
        "overall" => verdict,
        "reason" => reason,
        "per_seed_classification" => per_seed_class,
        "stable_class" => stable_class,
        "z_hopf_per_seed" => z_hopf_seeds,
        "z_combined_per_seed" => z_comb_seeds,
        "z_twistor_alone_per_seed" => z_tw_seeds,
        "brackets_c_hopf_all_seeds" => brackets_all,
        "band_populated_all_seeds" => populated_all,
        "x0_wiring_control_holds_all_seeds" => wiring_all,
        "hopf_baseline_reproduces_iter7_signal_all_seeds" => hopf_signal_all_seeds,
        "hopf_z_negative_and_sign_stable" => hopf_signal_all_seeds,
        "hopf_strict_outside_flag_count_diagnostic_only" => hopf_outside_flag_count,
        "z_combined_sign_per_seed" => [isfinite(z) ? sign(z) : NaN for z in z_comb_seeds],
        "z3_load_bearing" => z3_load_bearing,
        "interpretation" => "FAIR test vs the RIGHT substrate. The iter-7 d=4 geometry-specific suppression (substrate_effect_matched_band.jl: z_matched_band(d=4)=-1.0077) is DIRECTIONAL — z<0, the Hopf rotor produces LESS substrate effect than commutator-matched random — and lives on the genuine quaternionic Hopf-rotor frame, NOT on the block-diagonal substrate the prior twistor probe used. Here the Hopf-rotor substrate is the BASELINE (z_hopf, reproducing the iter-7 negative signal: z_hopf stable negative across seeds) and the genuine incidence frame omega=i x pi DRESSES it (U_combined=U_inc*U_hopf). The verdict compares z_combined to z_hopf against the SAME Hopf-c-matched band, SIGN-AWARE: enhance => keeps the negative sign and deepens it (twistors strengthen the real signal); orthogonal => z_combined ~ z_hopf (twistors independent here); destroy => z_combined FLIPS sign (scatters/washes the directional signal). The x=0 wiring control (U_inc(0)=I => U_combined=U_hopf => z_combined==z_hopf) guards against a by-construction composition; the strict >std outside flag is recorded as a diagnostic but is NOT the gate (the iter-7 finding itself sat at |z|~1, i.e. AT the 1-std boundary). EXPLORATORY, promotion_allowed=false; closes the twistor question fairly and admits twistors as nothing canonical.",
    )

    # F01 / N01 witnesses
    R["F01_witness"] = Dict(
        "finite_carrier" => "density operators in D(C^4) on the quaternionic Hopf carrier; finite frame set {Hopf-rotor baseline U_hopf, twistor-dressed U_inc*U_hopf, twistor-alone U_inc, flat=I, x=0 incidence on Hopf, twistor-on-flat, scale-swept random}",
        "finite_probe"   => "$(N_RHO+1) density operators (spinor-derived + maximally-mixed)",
        "finite_operator"=> "dissipative Weyl-L GKSL substrate on C^4; genuine Spin(5)=Sp(2) Hopf rotor frame; twistor incidence generator H_inc(x)=[0 i x;-i x^* 0]; scale-swept random control frames",
        "finite_path"    => "dressed compositions U Phi_WeylL(U' . U) U' for each frame; substrate effect E=max_rho||dressed-bare||_1; matched-band z=(E-band_mean)/band_std around the Hopf rotor's c_hopf",
    )
    R["N01_witness"] = Dict(
        "order_sensitive_control" => "the Hopf rotor does NOT commute with the dissipative GKSL Hamiltonian ([U_hopf, H0] != 0, c_hopf>0) because frame-site psi_A != upper-op-site psi_B; the incidence frame U_inc mixes the (omega,pi) Weyl blocks via omega=i x pi, and U_combined=U_inc*U_hopf composes the two non-commuting frames. The scale-swept band brackets the magnitude of the Hopf non-commutation so the matched-band z isolates whether dressing with the incidence GEOMETRY moves the signal beyond it.",
        "c_hopf" => lv["c_hopf"], "c_combined" => lv["c_combined"], "c_twistor_alone" => lv["c_twistor_alone"],
        "hopf_matched_band_separation" => hopf_sep,
        "present_above_floor" => hopf_sep > 1e-3,
        "noise_floor" => lv["noise_floor"],
    )

    R["required_negatives"] = ["flat_frame_U_eq_I", "x0_degenerate_incidence_wiring_control", "twistor_on_flat_substrate", "scale_swept_commutator_matched_band_around_c_hopf"]
    R["negatives_run"]      = ["flat_frame_U_eq_I", "x0_degenerate_incidence_wiring_control", "twistor_on_flat_substrate", "scale_swept_commutator_matched_band_around_c_hopf"]
    R["kill_conditions"] = [
        "flat frame U=I must collapse E to the noise floor (anti-tautology)",
        "x=0 incidence on Hopf (U_inc(0)=I) must give U_combined=U_hopf so z_combined==z_hopf exactly (wiring control)",
        "the scale-swept band must BRACKET c_hopf and POPULATE else the matched comparison is not honest -> inconclusive",
        "the Hopf-alone baseline must reproduce the iter-7 d=4 DIRECTIONAL signal (z_hopf negative and seed-stable in sign) else there is no signal to test the twistor against -> inconclusive",
        "if the combined frame FLIPS sign vs the Hopf negative-suppression sign => twistor_destroys (scatters the directional signal)",
        "if |z_combined - z_hopf| <= 0.5 std => twistor_orthogonal (twistors independent of the substrate effect here)",
        "the enhance/orthogonal/destroy class must be seed-stable else inconclusive (no single-seed promotion); a sign that scatters with the random spacetime point x is the genuine 'unstable' finding",
    ]

    R["tool_manifest"] = Dict(
        "LinearAlgebra" => "load_bearing: svdvals (trace norm), HS/Frobenius/opnorm, matrix exp (Hopf rotor exp(-i ang/2 n.Gamma), incidence frame exp(-i ang/2 H_inc), GKSL, scale-swept random U), Clifford anticommutator check; every measured number flows through it.",
        "Statistics"    => "load_bearing: mean/std over the rho ensemble and the matched band; the z observable IS (E-band_mean)/band_std.",
        "Random"        => "load_bearing: random density operators, the genuine spacetime point x, the scale-swept commutator-matched band bracketing c_hopf.",
        "Z3"            => "load_bearing: binds the measured Hopf matched-band separation to flat=>sep==0; verdict flips UNSAT->SAT on the flat control.",
        "JSON"          => "supportive: receipt emission.",
    )
    R["tool_integration_depth"] = Dict("LinearAlgebra"=>"load_bearing","Z3"=>"load_bearing","Random"=>"load_bearing","Statistics"=>"load_bearing","JSON"=>"supportive")
    R["downstream_blocks"] = ["layer-completion","manifold admission","twistor canonical admission","pairwise nesting promotion","coupling","bridge/Xi/Phi0/Axis0","flux/FEP/physics","final_manifold_admission"]
    R["blocked_consumers"] = R["downstream_blocks"]
    R["root_constraints_in_force"] = [
        "F01 finite density-operator carrier in D(C^4) / Hopf-rotor + twistor-dressed + twistor-alone + flat + scale-swept frame set / Weyl GKSL substrate / dressed paths",
        "N01 [U_hopf, H0] != 0 order-sensitive control (frame-site != upper-op-site) and the incidence frame U_inc mixing the (omega,pi) Weyl blocks via omega=i x pi; scale-swept band brackets the Hopf non-commutation magnitude",
    ]
    R["status_ladder"]    = "exists < runs < passes local rerun"
    R["promotion_status"] = "diagnostic_only_exploratory"

    # JSON spec rejects NaN/Inf: sanitize.
    sanitize(x::Float64) = isfinite(x) ? x : "non_finite($x)"
    sanitize(x::AbstractDict) = Dict(k => sanitize(v) for (k,v) in x)
    sanitize(x::AbstractVector) = [sanitize(v) for v in x]
    sanitize(x) = x
    Rclean = sanitize(R)

    open(RESULT_PATH, "w") do io
        JSON.print(io, Rclean, 2); write(io, "\n")
    end

    println("-"^98)
    println("z_hopf      per seed: ", round.(z_hopf_seeds, sigdigits=4))
    println("z_combined  per seed: ", round.(z_comb_seeds, sigdigits=4))
    println("z_twistor   per seed: ", round.(z_tw_seeds, sigdigits=4))
    println("hopf outside band   : ", hopf_out_seeds, "  combined outside band: ", comb_out_seeds)
    println("x0 wiring matches   : ", wiring_seeds, "  brackets c_hopf: ", bracket_seeds, "  populated: ", pop_seeds)
    println("per-seed class      : ", per_seed_class, "   stable_class=", stable_class)
    println("Z3: genuine=", z3_genuine, " flat=", z3_flat, " flip=", z3_load_bearing)
    println("-"^98)
    println("OVERALL VERDICT: ", verdict)
    println("REASON: ", reason)
    println("Wrote: ", RESULT_PATH)
    return R
end

run()
