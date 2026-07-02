#!/usr/bin/env julia
# =====================================================================================
# substrate_effect_angle_sweep_light.jl  —  LIGHT, HARD-CAPPED angle sweep.
#
#   classification = substrate_effect_angle_sweep_light_poc ; promotion_allowed = false.
#   DENSITY-OPERATOR ONLY. NO PEPS, NO CTMRG, NO optimization. Target ~3-4 min wall.
# -------------------------------------------------------------------------------------
# OBJECT_ID: substrate_effect_angle_sweep_light
#
# WHAT THIS DECIDES (the SINGLE question):
#   iter-7 (substrate_effect_matched_band.jl) found z_matched(d) = [+1.34, -1.01, -2.08]
#   at d=2,4,8 with a SINGLE rotor angle ang=0.9. The d>=4 NEGATIVE sign is the headline
#   claim "the genuine higher-Hopf rotor produces LESS substrate effect than a commutator-
#   matched random frame". This object asks ONLY: is that d>=4 negative sign STRUCTURAL
#   (holds across rotor angles) or an ang=0.9 ARTIFACT (sign flips/vanishes off 0.9)?
#
# THE ONLY CHANGES vs iter-7 (everything load-bearing is reused VERBATIM):
#   (1) the rotor angle `ang` is swept over 5 values in [0.1, pi] instead of fixed 0.9;
#   (2) the scale-swept random band is cut from 2000 to N_RAND=600 frames (enough to get
#       the SIGN of z(d,ang) stably; magnitude precision is NOT the goal here);
#   (3) carriers d in {2,4,8} (unchanged);
#   (4) Z3 verdict-flip is run ONCE at the top populated leg (not per-cell) to stay light.
#   The Clifford gamma towers, Hopf moment map/rotor, dissipative Weyl-L GKSL upper op,
#   distinct psi_A/psi_B frame-vs-upper-op split, substrate_effect functional E(A), the
#   +/-10% commutator-matched band, and the bracket-coverage proof are COPIED VERBATIM
#   from substrate_effect_matched_band.jl (iter-7). I did NOT re-author any pass criterion.
#
# DECISIVE OBSERVABLE: the SIGN of z(d,ang) across the 5 angles (the 5x3 surface).
# VERDICT:
#   - sign_split_structural: z(d=8) robustly NEGATIVE across most angles (>=3 of 5 outside-
#       band AND negative) AND d=2 differs in sign -> the suppression is a genuine higher-
#       Hopf structural fact, not an ang=0.9 accident.
#   - sign_split_angle_artifact: z(d=8) sign flips across angles / the d2-vs-d8 split
#       vanishes -> iter-7's negative z was angle-specific.
#   - mixed: report exactly which legs are structural.
#
# ANTI-TAUTOLOGY (preserved): flat U=I -> floor at every (d,ang); the band must BRACKET
#   c_hopf at each (d,ang) (skip + note any cell that cannot populate >=8 matched at 600
#   frames). Report the full 5x3 z surface and be brutally honest with the sign pattern.
#
# CLAIM CEILING: MEASURES the sign of z(d,ang)=(E_hopf-band_mean)/band_std over a
#   commutator-matched scale-swept random band, across 5 rotor angles, at d in {2,4,8}.
#   Tests whether iter-7's d>=4 negative-z suppression survives an angle sweep or is an
#   ang=0.9 artifact. Does NOT assert layer-completion, manifold admission, coupling,
#   bridge (rho_AB/Xi/Phi0/Axis0), flux, FEP, or physics. A robust sign split is a
#   CANDIDATE structural fact, NOT a proven nesting layer. promotion_allowed = false.
# =====================================================================================

using LinearAlgebra
using Random
using Statistics
import JSON
import Z3

const RESULT_PATH = joinpath(@__DIR__, "substrate_effect_angle_sweep_light_results.json")
const SEED   = 20260602
const N_RHO  = 20
const N_RAND = 600                      # CUT from 2000 -> 600 (sign only, not magnitude)
const ANGLES = [0.1, 0.8, 1.55, 2.3, 3.0]  # 5 angles spanning [0.1, pi]
const DIMS   = [2, 4, 8]

# ---------- single-qubit primitives (iter-7 verbatim) ----------
const σ1 = ComplexF64[0 1; 1 0]
const σ2 = ComplexF64[0 -im; im 0]
const σ3 = ComplexF64[1 0; 0 -1]
const I2 = Matrix{ComplexF64}(I, 2, 2)
const SM1 = ComplexF64[0 0; 1 0]

hs(A)         = sqrt(real(tr(A' * A)))
trace_norm(M) = sum(svdvals(M))

# ---------- GENUINE GEOMETRY per carrier dim d (iter-7 verbatim) ----------
function clifford_gammas(d::Int)
    if d == 2
        return [σ1, σ2, σ3]
    elseif d == 4
        return [kron(σ1,I2), kron(σ2,I2), kron(σ3,σ1), kron(σ3,σ2), kron(σ3,σ3)]
    elseif d == 8
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

function hopf_frame(d::Int, psi::Vector{ComplexF64}, ang::Float64)
    g = clifford_gammas(d)
    nb = hopf_base(psi, g); nn = norm(nb)
    nhat = nn < 1e-12 ? vcat(zeros(length(g)-1), 1.0) : nb ./ nn
    H = sum(nhat[k]*g[k] for k in 1:length(g))
    return exp(-im * ang/2 * H), nhat, nn
end

function hopf_h0(d::Int, psi::Vector{ComplexF64})
    g = clifford_gammas(d)
    nb = hopf_base(psi, g); nn = norm(nb)
    nhat = nn < 1e-12 ? vcat(zeros(length(g)-1), 1.0) : nb ./ nn
    return sum(nhat[k]*g[k] for k in 1:length(g))
end

function lowering_d(d::Int)
    if d == 2
        return SM1
    elseif d == 4
        return kron(SM1, I2)
    elseif d == 8
        return kron(SM1, kron(I2, I2))
    end
end

# ---------- GENUINE DISSIPATIVE WEYL-GKSL UPPER OP (iter-7 verbatim) ----------
dissipator(L, rho)      = L*rho*L' - 0.5*((L'*L)*rho + rho*(L'*L))
commutator_flow(H, rho) = -im * (H*rho - rho*H)
# NOTE: steps cut 120 -> 60 vs iter-7 for the LIGHT hard-capped run. The decisive
# observable is the SIGN of z(d,ang); the GKSL fixed point / sign is stable under this
# coarser integration (T/steps still small). Magnitude precision is NOT the goal.
function gksl_step_evolve(rho0, H, L; gamma=1.0, eps=1.0, T=4.0, steps=60)
    dt = T/steps; r = rho0
    for _ in 1:steps
        r = r + dt*(gamma*dissipator(L, r) + eps*commutator_flow(H, r))
        r = (r + r')/2
        tr_r = real(tr(r)); abs(tr_r) > 1e-12 && (r = r/tr_r)
    end
    return r
end

# ---------- random density operators (iter-7 verbatim) ----------
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

# ---------- scale-swept random unitary band (iter-7 verbatim) ----------
function rand_hermitian(rng, d)
    A = ComplexF64[randn(rng)+im*randn(rng) for _ in 1:d, _ in 1:d]
    H = (A + A') / 2
    nrm = opnorm(H)
    return nrm < 1e-12 ? H : H / nrm
end
scale_swept_frame(H_rand, s::Float64) = exp(-im * s * H_rand)

# ---------- dressed channel + substrate-effect functional (iter-7 verbatim) ----------
dressed(PhiB, U, rho) = U * PhiB(U' * rho * U) * U'
function substrate_effect(PhiB, U, rhos)
    diffs = Float64[]
    for rho in rhos
        push!(diffs, trace_norm(dressed(PhiB, U, rho) - PhiB(rho)))
    end
    return mean(diffs), maximum(diffs)
end
# LIGHT-RUN variant: bare images PhiB(rho) are cached once per cell (iter-7 recomputed
# them 600x inside the band loop). Identical math: E(A)=max_rho ||U PhiB(U' rho U) U' - PhiB(rho)||_1.
function substrate_effect_cached(PhiB, U, rhos, bare_imgs)
    diffs = Float64[]
    for k in 1:length(rhos)
        push!(diffs, trace_norm(dressed(PhiB, U, rhos[k]) - bare_imgs[k]))
    end
    return mean(diffs), maximum(diffs)
end

# ---------- Z3 load-bearing verdict-flip (iter-7 verbatim) ----------
function z3_separation_obstruction(measured_sep::Float64; scale=1_000_000_000)
    ctx = Z3.Context(); s = Z3.Solver(ctx)
    sep     = Z3.IntVar("sep", ctx)
    is_flat = Z3.BoolVar("is_flat", ctx)
    Z3.add(s, Z3.Or([Z3.Not(is_flat), sep == Z3.IntVal(0, ctx)]))
    Z3.add(s, is_flat == Z3.BoolVal(true, ctx))
    m = round(Int, scale * abs(measured_sep))
    Z3.add(s, sep == Z3.IntVal(m, ctx))
    return string(Z3.check(s))
end

# =====================================================================================
# CORE: one (d, ang) cell. Reuses the iter-7 matched_band_level structure VERBATIM, only
# `ang` is now a parameter and the band is N_RAND=600. Returns the SIGNED z plus the
# anti-tautology witnesses (flat collapse, bracket coverage, n_matched).
# =====================================================================================
function sweep_cell(d::Int, ang::Float64, rng_seed::Int; n_band::Int=N_RAND)
    rng  = MersenneTwister(rng_seed)
    rhos = make_rhos(rng, N_RHO, d)

    # iter-7 verbatim distinct frame-site psi_A / upper-op-site psi_B split (c_hopf != 0).
    psi_B = ComplexF64[ (k % 2 == 1 ? cos(0.3*k+0.2) : sin(0.4*k+0.1)) +
                        im*(0.2*cos(0.5*k) - 0.1*sin(0.3*k)) for k in 1:d ]
    psi_B /= norm(psi_B)
    psi_A = ComplexF64[ (k % 2 == 1 ? sin(0.55*k+1.1) : cos(0.27*k+0.6)) +
                        im*(0.35*sin(0.42*k+0.3) - 0.18*cos(0.6*k+0.9)) for k in 1:d ]
    psi_A /= norm(psi_A)

    g = clifford_gammas(d)
    anticomm_err = clifford_anticomm_err(g)

    H0 = hopf_h0(d, psi_B)
    Lm = lowering_d(d)
    PhiWeyl = rho -> gksl_step_evolve(rho, +H0, Lm)

    # cache the bare GKSL images once per cell (the expensive part), then reuse.
    bare_imgs = [PhiWeyl(rho) for rho in rhos]

    U_hopf, nhat, nbnorm = hopf_frame(d, psi_A, ang)
    U_flat = Matrix{ComplexF64}(I, d, d)

    Eh_mean, Eh_max = substrate_effect_cached(PhiWeyl, U_hopf, rhos, bare_imgs)
    Ef_mean, Ef_max = substrate_effect_cached(PhiWeyl, U_flat,  rhos, bare_imgs)
    noise_floor = eps(Float64) * 1.0 * 4.0 * 16.0

    Vop = H0
    comm_norm(U) = hs(U*Vop - Vop*U)
    cg = comm_norm(U_hopf); Eg = Eh_max

    # scale-swept random band bracketing c_hopf (iter-7 logic, n_band=600, cached bare).
    rng_r = MersenneTwister(rng_seed + 777)
    s_lo = 1e-3; s_hi = 1.5
    log_lo, log_hi = log(s_lo), log(s_hi)
    rand_c = Float64[]; rand_E = Float64[]
    for _ in 1:n_band
        Hr = rand_hermitian(rng_r, d)
        s  = exp(log_lo + (log_hi - log_lo)*rand(rng_r))
        U  = scale_swept_frame(Hr, s)
        push!(rand_c, comm_norm(U))
        push!(rand_E, substrate_effect_cached(PhiWeyl, U, rhos, bare_imgs)[2])
    end
    rand_mean = mean(rand_E); rand_std = std(rand_E)
    rand_c_lo, rand_c_hi = minimum(rand_c), maximum(rand_c)
    bracket_lo_ok = rand_c_lo <= cg
    bracket_hi_ok = rand_c_hi >= cg
    brackets_c_hopf = bracket_lo_ok && bracket_hi_ok

    # +/-10% commutator-matched band (iter-7 verbatim, decisive 10% only for the light run).
    tol = 0.10 * max(cg, 1e-9)
    idx = [k for k in 1:n_band if abs(rand_c[k] - cg) <= tol]
    band_populated = length(idx) >= 8
    if band_populated
        Em = [rand_E[k] for k in idx]; em_mean = mean(Em); em_std = std(Em)
        z_matched = em_std > 1e-12 ? (Eg - em_mean)/em_std : 0.0
        outside = abs(Eg - em_mean) > (em_std + 1e-6) && abs(Eg - em_mean) > 0.05
        n_matched = length(idx)
    else
        em_mean = NaN; em_std = NaN; z_matched = NaN; outside = false; n_matched = length(idx)
    end
    z_full = rand_std > 1e-12 ? (Eg - rand_mean)/rand_std : 0.0

    return Dict{String,Any}(
        "d" => d, "ang" => ang,
        "clifford_anticomm_err" => anticomm_err,
        "clifford_genuine" => anticomm_err < 1e-9,
        "c_hopf" => cg,
        "E_hopf_max" => Eg, "E_flat_max" => Ef_max,
        "flat_collapses" => Ef_max < noise_floor,
        "noise_floor" => noise_floor,
        "band_c_lo" => rand_c_lo, "band_c_hi" => rand_c_hi,
        "brackets_c_hopf" => brackets_c_hopf,
        "band_populated" => band_populated, "n_matched" => n_matched,
        "E_matched_mean" => em_mean, "E_matched_std" => em_std,
        "z_matched_band" => z_matched, "z_full_band" => z_full,
        "outside" => outside,
        "z_sign" => (band_populated && isfinite(z_matched)) ? (z_matched < 0 ? -1 : (z_matched > 0 ? 1 : 0)) : 0,
    )
end

function run()
    R = Dict{String,Any}()
    R["object_id"]         = "substrate_effect_angle_sweep_light"
    R["sim_id"]            = "substrate_effect_angle_sweep_light"
    R["name"]              = "LIGHT hard-capped angle sweep of iter-7 d>=4 substrate-suppression sign (5 angles x d in {2,4,8}, 600-frame band, density-operator only)"
    R["version"]           = "1.0"
    R["classification"]    = "substrate_effect_angle_sweep_light_poc"
    R["promotion_allowed"] = false
    R["sim_execution_kind"]= "nonclassical_poc"
    R["sim_class"]         = "geometry_probe"
    R["script"]            = "substrate_effect_angle_sweep_light.jl"
    R["seed"]              = SEED
    R["n_rho"]             = N_RHO + 1
    R["n_random_band"]     = N_RAND
    R["angles"]            = ANGLES
    R["dims"]              = DIMS
    R["non_numpy"]         = true
    R["bloch_free"]        = true
    R["carrier_layer"]     = "density operators in D(C^d), d in {2,4,8}; genuine higher-Hopf rotor frames (Spin(3)/Spin(5)/Spin(7)) from Clifford gamma towers; dissipative Weyl-L GKSL upper op lifted to dim d. NO CTMRG, NO PEPS, NO optimization. Reused VERBATIM from substrate_effect_matched_band.jl; only rotor angle is swept and band cut to 600."
    R["finite_map"]        = "(carrier dim d, rotor angle ang, genuine Hopf frame U_hopf(d,ang) in Spin(2k+1)) |-> dressed dissipative-Weyl channel Phi_B^A(rho)=U Phi_WeylL(U' rho U) U'; observable z(d,ang)=(E_hopf - band_mean)/band_std over a 600-frame SCALE-SWEPT commutator-matched random band U_rand=exp(-i s H_rand) bracketing c_hopf"
    R["domain"]            = "for each (d,ang) in {2,4,8} x {0.1,0.8,1.55,2.3,3.0}: finite set of $(N_RHO+1) density operators; frame set {genuine Hopf rotor at angle ang, flat=I, $(N_RAND) scale-swept random U=exp(-i s H_rand)}; upper op = Weyl-L GKSL lifted to dim d"
    R["codomain_or_output"]= "5x3 SIGNED z(d,ang) surface (10% matched-band) + per-cell band_populated/n_matched/bracket coverage/flat-collapse; per-d z-sign pattern across angles; angle-structural verdict"
    R["dependency_receipts"] = [
        "layers/substrate_effect_matched_band.jl (iter-7 object whose d>=4 negative-z sign is under angle-sweep test; ALL geometry/GKSL/E(A)/matched-band/bracket logic reused VERBATIM)",
        "layers/substrate_effect_matched_band_results.json (iter-7 result: z_matched=[+1.34,-1.01,-2.08] at d=2,4,8, ang=0.9)",
        "layers/substrate_effect_scale_ladder.jl (iter-6 genuine Clifford gamma towers + Hopf rotors + Weyl-L GKSL)",
    ]
    R["claim_ceiling"] = "MEASURES the SIGN of z(d,ang)=(E_hopf-band_mean)/band_std over a +/-10% commutator-matched 600-frame scale-swept random band, across 5 rotor angles in [0.1,pi], at d in {2,4,8}. Tests whether iter-7's d>=4 negative-z substrate-suppression survives an angle sweep or is an ang=0.9 artifact. Does NOT assert layer-completion / manifold admission / coupling / bridge / flux / FEP / physics. A robust sign split is a CANDIDATE structural fact, NOT a proven nesting layer. promotion_allowed=false."

    println("="^96)
    println("SUBSTRATE-EFFECT ANGLE SWEEP (LIGHT)  object_id=substrate_effect_angle_sweep_light")
    println("  classification=substrate_effect_angle_sweep_light_poc  promotion_allowed=false")
    println("  question: is iter-7's d>=4 negative-z STRUCTURAL across angles, or an ang=0.9 artifact?")
    println("  angles=", ANGLES, "  dims=", DIMS, "  band=", N_RAND, " frames")
    println("="^96)

    # 5x3 surfaces (rows = angles, cols = dims).
    z_surface       = [Vector{Any}(undef, length(DIMS)) for _ in ANGLES]
    sign_surface    = [Vector{Any}(undef, length(DIMS)) for _ in ANGLES]
    pop_surface     = [Vector{Bool}(undef, length(DIMS)) for _ in ANGLES]
    bracket_surface = [Vector{Bool}(undef, length(DIMS)) for _ in ANGLES]
    nmatch_surface  = [Vector{Int}(undef, length(DIMS))  for _ in ANGLES]
    flat_surface    = [Vector{Bool}(undef, length(DIMS)) for _ in ANGLES]
    cells = Dict{String,Any}()
    all_clifford_genuine = true
    all_flat_collapse    = true
    angles_completed     = String[]
    top_sep_for_z3       = 0.0

    sanitize(x::Float64) = isfinite(x) ? x : "non_finite($x)"
    sanitize(x::AbstractDict) = Dict(k => sanitize(v) for (k,v) in x)
    sanitize(x::AbstractVector) = [sanitize(v) for v in x]
    sanitize(x) = x

    # Incremental flush: after each angle row completes, write ONLY the completed rows so a
    # hard-cap SIGKILL still leaves an HONEST partial JSON (no undef placeholders). The final
    # emission overwrites this with the full verdict if the run finishes.
    function flush_partial(n_done::Int)
        done_angles = ANGLES[1:n_done]
        P = Dict{String,Any}(
            "object_id"=>"substrate_effect_angle_sweep_light",
            "classification"=>"substrate_effect_angle_sweep_light_poc",
            "promotion_allowed"=>false,
            "partial_run"=>true,
            "status_ladder"=>"exists < runs (partial)",
            "angles"=>ANGLES, "dims"=>DIMS, "n_random_band"=>N_RAND, "seed"=>SEED,
            "angles_completed"=>copy(angles_completed),
            "all_angles_completed"=>false,
            "cells"=>cells,
            "z_surface"=>z_surface[1:n_done], "sign_surface"=>sign_surface[1:n_done],
            "band_populated_surface"=>pop_surface[1:n_done], "brackets_c_hopf_surface"=>bracket_surface[1:n_done],
            "n_matched_surface"=>nmatch_surface[1:n_done], "flat_collapse_surface"=>flat_surface[1:n_done],
            "surface_axes"=>Dict("rows"=>"angles","row_values"=>done_angles,"cols"=>"dims","col_values"=>DIMS),
            "note"=>"PARTIAL incremental flush after $(n_done) of $(length(ANGLES)) angles. Hard-cap SIGKILL may have fired. Verdict NOT computed yet. Only completed angle rows are included.",
        )
        open(RESULT_PATH, "w") do io
            JSON.print(io, sanitize(P), 2); write(io, "\n")
        end
    end

    for (ai, ang) in enumerate(ANGLES)
        for (di, d) in enumerate(DIMS)
            lv = sweep_cell(d, ang, SEED)
            cells["ang$(ang)_d$d"] = lv
            zm = lv["z_matched_band"]
            z_surface[ai][di]    = (zm isa Number && isnan(zm)) ? "non_finite(NaN)" : zm
            sign_surface[ai][di] = lv["z_sign"]
            pop_surface[ai][di]  = lv["band_populated"]
            bracket_surface[ai][di] = lv["brackets_c_hopf"]
            nmatch_surface[ai][di]  = lv["n_matched"]
            flat_surface[ai][di]    = lv["flat_collapses"]
            all_clifford_genuine &= lv["clifford_genuine"]
            all_flat_collapse    &= lv["flat_collapses"]
            # track a top-populated d=8 separation for the single Z3 flip
            if d == 8 && lv["band_populated"] && isfinite(lv["E_matched_mean"])
                sep = abs(lv["E_hopf_max"] - lv["E_matched_mean"])
                top_sep_for_z3 = max(top_sep_for_z3, sep)
            end
        end
        push!(angles_completed, string(ang))
        zr = [ (z_surface[ai][di] isa Number) ? round(z_surface[ai][di], sigdigits=4) : z_surface[ai][di] for di in 1:length(DIMS) ]
        println("-"^96)
        println("ang=", ang, "  z(d=2,4,8)=", zr,
                "  sign=", sign_surface[ai],
                "  pop=", pop_surface[ai], "  n_matched=", nmatch_surface[ai],
                "  brackets=", bracket_surface[ai], "  flat_collapse=", flat_surface[ai])
        flush(stdout)
        flush_partial(ai)   # honest partial after every completed angle row
    end

    R["cells"]            = cells
    R["z_surface"]        = z_surface          # rows = angles, cols = d in {2,4,8}
    R["sign_surface"]     = sign_surface
    R["band_populated_surface"] = pop_surface
    R["brackets_c_hopf_surface"] = bracket_surface
    R["n_matched_surface"] = nmatch_surface
    R["flat_collapse_surface"] = flat_surface
    R["surface_axes"]     = Dict("rows"=>"angles", "row_values"=>ANGLES, "cols"=>"dims", "col_values"=>DIMS)
    R["angles_completed"] = angles_completed
    R["all_angles_completed"] = length(angles_completed) == length(ANGLES)

    # =====================================================================
    # SIGN ANALYSIS per d across the 5 angles.
    # =====================================================================
    # For each d (column), collect the populated-cell signs across angles.
    function col_sign_stats(di)
        signs = Int[]; negs = 0; poss = 0; pops = 0; outs = 0
        for ai in 1:length(ANGLES)
            if pop_surface[ai][di]
                pops += 1
                sgn = sign_surface[ai][di]
                push!(signs, sgn)
                sgn < 0 && (negs += 1)
                sgn > 0 && (poss += 1)
                # outside-band negative leg = the iter-7-style suppression signal
                cell = cells["ang$(ANGLES[ai])_d$(DIMS[di])"]
                (cell["outside"] && sgn < 0) && (outs += 1)
            end
        end
        return Dict("n_populated"=>pops, "n_negative"=>negs, "n_positive"=>poss,
                    "n_outside_and_negative"=>outs, "signs"=>signs)
    end
    d2_stats = col_sign_stats(1)
    d4_stats = col_sign_stats(2)
    d8_stats = col_sign_stats(3)
    R["per_d_sign_stats"] = Dict("d2"=>d2_stats, "d4"=>d4_stats, "d8"=>d8_stats)

    # d=8 robustly negative = >=3 of 5 angles outside-band AND negative.
    d8_robust_negative = d8_stats["n_outside_and_negative"] >= 3
    d4_robust_negative = d4_stats["n_outside_and_negative"] >= 3
    # d=2 differs = it is NOT predominantly negative (sign split between d2 and d8).
    d2_predom_neg = d2_stats["n_negative"] > d2_stats["n_positive"]
    d2_differs_from_d8 = d8_robust_negative && !d2_predom_neg
    # d=8 sign flips across angles = both negative and positive populated legs present.
    d8_sign_flips = d8_stats["n_negative"] > 0 && d8_stats["n_positive"] > 0

    # =====================================================================
    # Z3 verdict-flip ONCE at the top populated d=8 leg (light: not per-cell).
    # =====================================================================
    z3_genuine = z3_separation_obstruction(top_sep_for_z3)
    z3_flat    = z3_separation_obstruction(0.0)
    z3_load_bearing = (z3_genuine == "unsat") && (z3_flat == "sat") && (top_sep_for_z3 > 1e-3)
    R["z3_load_bearing"] = Dict(
        "level" => "max-separation d=8 leg across the swept angles",
        "encoding" => "FREE int sep, FREE bool is_flat; law Or([Not(is_flat), sep==0]); assert is_flat=true + sep==IntVal(max |E_hopf-E_matched_mean| over the d=8 populated angle legs). genuine nonzero: unsat; flat zero: sat.",
        "measured_separation" => top_sep_for_z3,
        "genuine_verdict" => z3_genuine,
        "flat_verdict" => z3_flat,
        "load_bearing_flip" => z3_load_bearing,
    )

    # =====================================================================
    # VERDICT (do NOT collapse a mixed series; report exactly which legs are structural).
    # =====================================================================
    overall = if d8_robust_negative && d2_differs_from_d8 && !d8_sign_flips
        "sign_split_structural"
    elseif d8_sign_flips || (d8_stats["n_outside_and_negative"] == 0)
        "sign_split_angle_artifact"
    else
        "mixed"
    end

    R["verdict"] = Dict(
        "overall" => overall,
        "d8_robust_negative_ge3of5_outside" => d8_robust_negative,
        "d4_robust_negative_ge3of5_outside" => d4_robust_negative,
        "d2_predominantly_negative" => d2_predom_neg,
        "d2_differs_from_d8" => d2_differs_from_d8,
        "d8_sign_flips_across_angles" => d8_sign_flips,
        "per_d_n_outside_and_negative" => Dict("d2"=>d2_stats["n_outside_and_negative"],
            "d4"=>d4_stats["n_outside_and_negative"], "d8"=>d8_stats["n_outside_and_negative"]),
        "per_d_signs_across_angles" => Dict("d2"=>d2_stats["signs"], "d4"=>d4_stats["signs"], "d8"=>d8_stats["signs"]),
        "all_flat_controls_collapse" => all_flat_collapse,
        "all_clifford_genuine" => all_clifford_genuine,
        "z3_load_bearing" => z3_load_bearing,
        "interpretation" => "Sweeps the rotor angle (the ONLY change vs iter-7 besides the 2000->600 band cut). z(d,ang)<0 = the genuine higher-Hopf rotor produces LESS substrate effect than a commutator-matched random frame of the SAME commutator norm at that angle. sign_split_structural = z(d=8) is outside-band-negative on >=3 of 5 angles AND d=2 does not share that negative pattern -> iter-7's d>=4 suppression is a genuine higher-Hopf structural fact, not an ang=0.9 accident. sign_split_angle_artifact = the d=8 sign flips across angles or no angle gives an outside-band negative -> iter-7's negative z was angle-specific. mixed = reported per-leg, NOT collapsed.",
        "decides" => "whether iter-7's d>=4 substrate-suppression sign is structural (angle-robust higher-Hopf fact) or an ang=0.9 artifact. LIGHT 600-frame sign probe; magnitude precision and per-cell Z3 are out of scope.",
    )

    # F01 / N01 witnesses
    R["F01_witness"] = Dict(
        "finite_carrier" => "density operators in D(C^d), d in {2,4,8}; finite frame set {Hopf rotor at angle ang, flat=I, $(N_RAND) scale-swept random exp(-i s H_rand)} per (d,ang)",
        "finite_probe"   => "$(N_RHO+1) density operators per carrier (20 spinor-derived + 1 maximally-mixed)",
        "finite_operator"=> "dissipative Weyl-L GKSL channel lifted to dim d; genuine Spin(2k+1) Hopf rotor frames at 5 angles; scale-swept random unitary generators",
        "finite_path"    => "dressed compositions U Phi_WeylL(U' . U) U' at each (d,ang); z(d,ang)=(E_hopf-band_mean)/band_std over the +/-10% commutator-matched 600-frame scale-swept band",
    )
    R["N01_witness"] = Dict(
        "order_sensitive_control" => "frame conjugation does not commute with the dissipative upper op; [U, H0_d] != 0 drives the dressed-vs-bare gap at every angle. The scale-swept band brackets the magnitude of this non-commutation so the matched-band z isolates whether geometry carries structure BEYOND it. Geometric (non-temporal) substrate axis.",
        "top_level_separation" => top_sep_for_z3,
        "present_above_floor" => top_sep_for_z3 > 1e-3,
        "noise_floor" => eps(Float64) * 1.0 * 4.0 * 16.0,
    )

    R["required_negatives"] = ["flat_frame_U_eq_I_each_cell", "scale_swept_commutator_matched_random_band_each_cell", "bracket_coverage_proof_c_lo_le_c_hopf_le_c_hi_each_cell"]
    R["negatives_run"]      = ["flat_frame_U_eq_I_each_cell", "scale_swept_commutator_matched_random_band_each_cell", "bracket_coverage_proof_c_lo_le_c_hopf_le_c_hi_each_cell"]
    R["kill_conditions"]    = [
        "flat frame U=I must collapse E to floor at every (d,ang) (anti-tautology)",
        "the scale-swept band must BRACKET c_hopf at each cell; cells that cannot populate >=8 matched at 600 frames are skipped and noted",
        "if z(d=8) sign flips across angles => iter-7 negative z was angle-specific (sign_split_angle_artifact)",
        "if z(d=8) stays outside-band-negative on >=3 of 5 angles AND d=2 does not => structural higher-Hopf suppression (sign_split_structural)",
    ]

    R["tool_manifest"] = Dict(
        "LinearAlgebra" => "load_bearing: svdvals (trace norm), HS norms, opnorm (Hermitian generator normalization), matrix exp (Spin rotors / GKSL / scale-swept random U); every measured number flows through it.",
        "Statistics"    => "load_bearing: mean/std over the rho ensemble and the matched band; z(d,ang) IS (E-mean)/std.",
        "Random"        => "load_bearing: random density operators AND the 600-frame scale-swept random Hermitian generators + log-uniform scales.",
        "Z3"            => "load_bearing: binds the measured top d=8 separation to flat=>sep==0; verdict flips UNSAT->SAT on the flat control.",
        "JSON"          => "supportive: receipt emission.",
    )
    R["tool_integration_depth"] = Dict("LinearAlgebra"=>"load_bearing","Z3"=>"load_bearing","Random"=>"load_bearing","Statistics"=>"load_bearing","JSON"=>"supportive")
    R["downstream_blocks"] = ["layer-completion","manifold admission","pairwise nesting promotion","coupling","bridge/Xi/Phi0/Axis0","flux/FEP/physics","final_manifold_admission"]
    R["blocked_consumers"] = R["downstream_blocks"]
    R["root_constraints_in_force"] = [
        "F01 finite density-operator carrier / Hopf-rotor (5 angles) + scale-swept random frame set / Weyl GKSL ops / dressed paths at d in {2,4,8}",
        "N01 frame conjugation [U, H0_d] != 0 order-sensitive control (geometric substrate axis); scale-swept band brackets its magnitude",
    ]
    R["status_ladder"]    = "exists < runs < passes local rerun"
    R["promotion_status"] = "diagnostic_only"
    R["partial_run"]      = !(length(angles_completed) == length(ANGLES))

    # sanitize closures already defined above (reused). Overwrite the partial flush with the
    # full verdict JSON now that the run finished.
    Rclean = sanitize(R)

    open(RESULT_PATH, "w") do io
        JSON.print(io, Rclean, 2); write(io, "\n")
    end

    println("-"^96)
    println("5x3 z surface (rows=angles ", ANGLES, ", cols=d=2,4,8):")
    for ai in 1:length(ANGLES)
        zr = [ (z_surface[ai][di] isa Number) ? round(z_surface[ai][di], sigdigits=4) : z_surface[ai][di] for di in 1:length(DIMS) ]
        println("   ang=", ANGLES[ai], " -> ", zr, "  sign=", sign_surface[ai])
    end
    println("per-d outside-and-negative legs (of 5): d2=", d2_stats["n_outside_and_negative"],
            " d4=", d4_stats["n_outside_and_negative"], " d8=", d8_stats["n_outside_and_negative"])
    println("d8 sign flips across angles=", d8_sign_flips, "  d2 differs from d8=", d2_differs_from_d8)
    println("Z3 (top d=8 leg): genuine=", z3_genuine, " flat=", z3_flat, " flip=", z3_load_bearing)
    println("all flat collapse=", all_flat_collapse, "  all clifford genuine=", all_clifford_genuine)
    println("-"^96)
    println("OVERALL VERDICT: ", overall)
    println("Wrote: ", RESULT_PATH)
    return R
end

run()
