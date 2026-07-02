#!/usr/bin/env julia
# =====================================================================================
# deflation_substrate_band.jl
#
# Direct deflation control for the substrate-suppression matched-band observable.
#
# classification = deflation_substrate_poc ; promotion_allowed = false.
# Density-operator carrier only. No PEPS/CTMRG/optimization. No layer completion claim.
#
# Question:
#   substrate_effect_matched_band.jl found that the genuine higher-Hopf rotor has z<0
#   at d>=4 against a commutator-matched scale-swept random band. V2 separately showed
#   that a single fixed Hopf base with only spin^c/connection lift variation can
#   reproduce the holonomy-law form. This file tests the matched-band z observable
#   directly under that same deflation control.
#
# Reused, intentionally same formulas as substrate_effect_matched_band.jl:
#   - Clifford gamma towers for d in {2,4,8}
#   - Hopf moment-map rotor exp(-i angle/2 n.Gamma)
#   - dissipative Weyl-L GKSL upper op
#   - E(U)=max_rho ||U Phi(U' rho U) U' - Phi(rho)||_1
#   - scale-swept random band U_rand=exp(-i s H_rand)
#   - +/-10% commutator-matched z=(E - band_mean)/band_std
#   - flat control and Z3 flat=>sep==0 verdict flip
#
# Deflated family:
#   For each d, fix ONE Hopf base (the same frame-site base used for the genuine rotor)
#   and vary only the spin^c/connection lift index m:
#       U_m = exp(-i * ETA_BASE * m * H_fixed),  H_fixed=n_fixed.Gamma
#   No shell eta ladder and no multi-shell nesting are varied in this family.
#
# Verdict:
#   substrate_deflated  : at d=4 and d=8 at least one valid single-base lift has
#                         bracketed/populated matched band and z<0 outside the band.
#   substrate_survives  : genuine d>=4 z<0 outside the band, but no valid single-base
#                         lift reproduces that suppression at either high dimension.
#   mixed               : only one high dimension reproduces, or the genuine side itself
#                         is not decisive in the fresh run.
# =====================================================================================

using LinearAlgebra
using Random
using Statistics
import JSON
import Z3

const RESULT_PATH = joinpath(@__DIR__, "deflation_substrate_band_results.json")
const SEED = 20260602
const N_RHO = 20
const N_RAND = 2000
const ETA_BASE = pi / 4
const SPIN_LIFTS = [1, 2, 3, 4, 5, 6, 7]

const sigma1 = ComplexF64[0 1; 1 0]
const sigma2 = ComplexF64[0 -im; im 0]
const sigma3 = ComplexF64[1 0; 0 -1]
const I2 = Matrix{ComplexF64}(I, 2, 2)
const SM1 = ComplexF64[0 0; 1 0]

hs(A) = sqrt(real(tr(A' * A)))
trace_norm(M) = sum(svdvals(M))

function clifford_gammas(d::Int)
    if d == 2
        return [sigma1, sigma2, sigma3]
    elseif d == 4
        return [kron(sigma1, I2), kron(sigma2, I2), kron(sigma3, sigma1),
                kron(sigma3, sigma2), kron(sigma3, sigma3)]
    elseif d == 8
        return [kron(sigma1, I2, I2), kron(sigma2, I2, I2),
                kron(sigma3, sigma1, I2), kron(sigma3, sigma2, I2),
                kron(sigma3, sigma3, sigma1), kron(sigma3, sigma3, sigma2),
                kron(sigma3, sigma3, sigma3)]
    else
        error("deflation substrate band built only for d in {2,4,8}")
    end
end

function clifford_anticomm_err(g)
    n = length(g)
    maximum(norm(g[a] * g[b] + g[b] * g[a] -
                 (a == b ? 2 * Matrix{ComplexF64}(I, size(g[a])...) : zero(g[a])))
            for a in 1:n, b in 1:n)
end

function hopf_base(psi::Vector{ComplexF64}, g)
    p = psi / norm(psi)
    [real(p' * (G * p)) for G in g]
end

function hopf_generator(d::Int, psi::Vector{ComplexF64})
    g = clifford_gammas(d)
    nb = hopf_base(psi, g)
    nn = norm(nb)
    nhat = nn < 1e-12 ? vcat(zeros(length(g) - 1), 1.0) : nb ./ nn
    H = sum(nhat[k] * g[k] for k in 1:length(g))
    return H, nhat, nn
end

function hopf_frame(d::Int, psi::Vector{ComplexF64}, angle::Float64)
    H, nhat, nn = hopf_generator(d, psi)
    return exp(-im * angle / 2 * H), nhat, nn
end

function fixed_base_lift_frame(d::Int, psi_fixed::Vector{ComplexF64}, m_lift::Int)
    H, nhat, nn = hopf_generator(d, psi_fixed)
    return exp(-im * ETA_BASE * m_lift * H), nhat, nn
end

function hopf_h0(d::Int, psi::Vector{ComplexF64})
    H, _, _ = hopf_generator(d, psi)
    return H
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

dissipator(L, rho) = L * rho * L' - 0.5 * ((L' * L) * rho + rho * (L' * L))
commutator_flow(H, rho) = -im * (H * rho - rho * H)

function gksl_step_evolve(rho0, H, L; gamma=1.0, eps=1.0, T=4.0, steps=120)
    dt = T / steps
    r = rho0
    for _ in 1:steps
        r = r + dt * (gamma * dissipator(L, r) + eps * commutator_flow(H, r))
        r = (r + r') / 2
        tr_r = real(tr(r))
        abs(tr_r) > 1e-12 && (r = r / tr_r)
    end
    return r
end

function rand_rho(rng, d)
    psi = ComplexF64[randn(rng) + im * randn(rng) for _ in 1:d]
    psi /= norm(psi)
    pure = psi * psi'
    Id = Matrix{ComplexF64}(I, d, d)
    p = 0.2 + 0.6 * rand(rng)
    rho = p * pure + (1 - p) * (Id / d)
    return (rho + rho') / 2 / real(tr((rho + rho') / 2))
end

make_rhos(rng, n, d) = vcat([rand_rho(rng, d) for _ in 1:n],
                            [Matrix{ComplexF64}(I, d, d) / d])

function rand_hermitian(rng, d)
    A = ComplexF64[randn(rng) + im * randn(rng) for _ in 1:d, _ in 1:d]
    H = (A + A') / 2
    nrm = opnorm(H)
    return nrm < 1e-12 ? H : H / nrm
end

scale_swept_frame(H_rand, s::Float64) = exp(-im * s * H_rand)

dressed(PhiB, U, rho) = U * PhiB(U' * rho * U) * U'

function substrate_effect(PhiB, U, rhos)
    diffs = Float64[]
    for rho in rhos
        push!(diffs, trace_norm(dressed(PhiB, U, rho) - PhiB(rho)))
    end
    return mean(diffs), maximum(diffs)
end

function z3_separation_obstruction(measured_sep::Float64; scale=1_000_000_000)
    ctx = Z3.Context()
    s = Z3.Solver(ctx)
    sep = Z3.IntVar("sep", ctx)
    is_flat = Z3.BoolVar("is_flat", ctx)
    Z3.add(s, Z3.Or([Z3.Not(is_flat), sep == Z3.IntVal(0, ctx)]))
    Z3.add(s, is_flat == Z3.BoolVal(true, ctx))
    m = round(Int, scale * abs(measured_sep))
    Z3.add(s, sep == Z3.IntVal(m, ctx))
    return string(Z3.check(s))
end

function source_spinors(d::Int)
    psi_B = ComplexF64[(k % 2 == 1 ? cos(0.3 * k + 0.2) : sin(0.4 * k + 0.1)) +
                       im * (0.2 * cos(0.5 * k) - 0.1 * sin(0.3 * k)) for k in 1:d]
    psi_A = ComplexF64[(k % 2 == 1 ? sin(0.55 * k + 1.1) : cos(0.27 * k + 0.6)) +
                       im * (0.35 * sin(0.42 * k + 0.3) - 0.18 * cos(0.6 * k + 0.9)) for k in 1:d]
    return psi_A / norm(psi_A), psi_B / norm(psi_B)
end

function build_scale_swept_band(d::Int, PhiWeyl, rhos, comm_norm, rng_seed::Int; n_band::Int=N_RAND)
    rng_r = MersenneTwister(rng_seed + 777)
    s_lo = 1e-3
    s_hi = 1.5
    log_lo, log_hi = log(s_lo), log(s_hi)
    rand_frames = Matrix{ComplexF64}[]
    rand_s = Float64[]
    for _ in 1:n_band
        Hr = rand_hermitian(rng_r, d)
        s = exp(log_lo + (log_hi - log_lo) * rand(rng_r))
        push!(rand_frames, scale_swept_frame(Hr, s))
        push!(rand_s, s)
    end
    rand_c = [comm_norm(U) for U in rand_frames]
    rand_E = [substrate_effect(PhiWeyl, U, rhos)[2] for U in rand_frames]
    return Dict{String,Any}(
        "rand_c" => rand_c,
        "rand_E" => rand_E,
        "n" => n_band,
        "s_lo" => s_lo,
        "s_hi" => s_hi,
        "c_lo" => minimum(rand_c),
        "c_hi" => maximum(rand_c),
        "E_lo" => minimum(rand_E),
        "E_hi" => maximum(rand_E),
        "E_mean" => mean(rand_E),
        "E_std" => std(rand_E),
    )
end

function matched_stats(label::String, U, PhiWeyl, rhos, band, comm_norm; noise_floor::Float64)
    E_mean, E_max = substrate_effect(PhiWeyl, U, rhos)
    cg = comm_norm(U)
    rand_c = band["rand_c"]
    rand_E = band["rand_E"]
    n_band = band["n"]
    rand_c_lo = band["c_lo"]
    rand_c_hi = band["c_hi"]
    bracket_lo_ok = rand_c_lo <= cg
    bracket_hi_ok = rand_c_hi >= cg
    brackets_c = bracket_lo_ok && bracket_hi_ok

    tol_results = Dict{String,Any}()
    robust_flags = Bool[]
    ref_mean = NaN
    ref_std = NaN
    ref_n = 0
    ref_abs_gap = NaN
    z_matched = NaN
    outside_10 = false
    band_populated_10 = false

    for tolfrac in (0.02, 0.05, 0.10)
        tol = tolfrac * max(cg, 1e-9)
        idx = [k for k in 1:n_band if abs(rand_c[k] - cg) <= tol]
        if length(idx) >= 8
            Em = [rand_E[k] for k in idx]
            em_mean = mean(Em)
            em_std = std(Em)
            zmt = em_std > 1e-12 ? (E_max - em_mean) / em_std : 0.0
            out = abs(E_max - em_mean) > (em_std + 1e-6) && abs(E_max - em_mean) > 0.05
            tol_results["tol_$(tolfrac)"] = Dict(
                "n" => length(idx),
                "E_matched_mean" => em_mean,
                "E_matched_std" => em_std,
                "abs_gap" => abs(E_max - em_mean),
                "z_matched" => zmt,
                "outside" => out,
            )
            push!(robust_flags, out)
            if tolfrac == 0.10
                ref_mean = em_mean
                ref_std = em_std
                ref_n = length(idx)
                ref_abs_gap = abs(E_max - em_mean)
                z_matched = zmt
                outside_10 = out
                band_populated_10 = true
            end
        else
            tol_results["tol_$(tolfrac)"] = Dict(
                "n" => length(idx),
                "outside" => false,
                "note" => "too few matched (<8) under the scale-swept bracketing band",
            )
            push!(robust_flags, false)
        end
    end

    rand_std = band["E_std"]
    z_full = rand_std > 1e-12 ? (E_max - band["E_mean"]) / rand_std : 0.0
    outside_robust = all(robust_flags) && length(robust_flags) == 3

    return Dict{String,Any}(
        "label" => label,
        "E_mean" => E_mean,
        "E_max" => E_max,
        "E_flat_floor" => E_max < noise_floor,
        "c" => cg,
        "bracket_lo_ok" => bracket_lo_ok,
        "bracket_hi_ok" => bracket_hi_ok,
        "brackets_c" => brackets_c,
        "band_populated" => band_populated_10,
        "n_matched" => ref_n,
        "E_matched_mean" => ref_mean,
        "E_matched_std" => ref_std,
        "abs_gap" => ref_abs_gap,
        "z_matched_band" => z_matched,
        "z_full_band" => z_full,
        "outside_10pct" => outside_10,
        "outside_robust" => outside_robust,
        "per_tolerance" => tol_results,
    )
end

function decisive_suppression(stat)
    z = stat["z_matched_band"]
    return stat["brackets_c"] && stat["band_populated"] &&
           (z isa Number) && isfinite(z) && z < 0.0 && stat["outside_10pct"]
end

function level(d::Int, rng_seed::Int)
    rng = MersenneTwister(rng_seed)
    rhos = make_rhos(rng, N_RHO, d)
    psi_A, psi_B = source_spinors(d)
    g = clifford_gammas(d)
    anticomm_err = clifford_anticomm_err(g)
    H0 = hopf_h0(d, psi_B)
    Lm = lowering_d(d)
    PhiWeyl = rho -> gksl_step_evolve(rho, +H0, Lm)
    Vop = H0
    comm_norm(U) = hs(U * Vop - Vop * U)
    noise_floor = eps(Float64) * 1.0 * 4.0 * 16.0

    band = build_scale_swept_band(d, PhiWeyl, rhos, comm_norm, rng_seed)
    U_flat = Matrix{ComplexF64}(I, d, d)
    U_genuine, nhat_genuine, nbnorm_genuine = hopf_frame(d, psi_A, 0.9)

    genuine = matched_stats("genuine_hopf_rotor", U_genuine, PhiWeyl, rhos, band, comm_norm; noise_floor=noise_floor)
    flat = matched_stats("flat_identity", U_flat, PhiWeyl, rhos, band, comm_norm; noise_floor=noise_floor)

    deflated = Any[]
    for m in SPIN_LIFTS
        U_m, nhat_m, nbnorm_m = fixed_base_lift_frame(d, psi_A, m)
        st = matched_stats("singlebase_spin_lift_m$m", U_m, PhiWeyl, rhos, band, comm_norm; noise_floor=noise_floor)
        st["spin_lift"] = m
        st["eta_base"] = ETA_BASE
        st["single_fixed_base_norm"] = nbnorm_m
        st["connection_lift_formula"] = "U_m = exp(-i * ETA_BASE * m * H_fixed), H_fixed=n_fixed.Gamma, ETA_BASE=pi/4"
        push!(deflated, st)
    end

    valid_deflated = [st for st in deflated if st["brackets_c"] && st["band_populated"]]
    suppressed_deflated = [st for st in valid_deflated if decisive_suppression(st)]
    best_deflated = if !isempty(valid_deflated)
        valid_deflated[argmin([st["z_matched_band"] for st in valid_deflated])]
    else
        deflated[argmin([st["c"] for st in deflated])]
    end

    return Dict{String,Any}(
        "d" => d,
        "carrier" => "C^$d ($(round(Int, log2(d)))-qubit density operators)",
        "clifford_anticomm_err" => anticomm_err,
        "clifford_genuine" => anticomm_err < 1e-9,
        "noise_floor" => noise_floor,
        "hopf_base_norm_genuine_frame_site" => nbnorm_genuine,
        "fixed_base_policy" => "single fixed Hopf frame-site base psi_A(d) is held fixed across m; only spin^c/connection lift index m varies",
        "scale_swept_band" => Dict(
            "n" => band["n"],
            "s_lo" => band["s_lo"],
            "s_hi" => band["s_hi"],
            "c_lo" => band["c_lo"],
            "c_hi" => band["c_hi"],
            "E_lo" => band["E_lo"],
            "E_hi" => band["E_hi"],
            "E_mean" => band["E_mean"],
            "E_std" => band["E_std"],
            "note" => "same scale-swept random ensemble is reused for genuine and all single-base lift variants at this d; matched comparison still keys on each frame's own c=||[U,H0]||",
        ),
        "flat" => flat,
        "genuine" => genuine,
        "deflated_lifts" => deflated,
        "best_deflated_by_min_z" => best_deflated,
        "valid_deflated_lift_count" => length(valid_deflated),
        "suppressed_deflated_lift_count" => length(suppressed_deflated),
        "suppressed_deflated_lifts" => [st["spin_lift"] for st in suppressed_deflated],
        "genuine_reproduces_suppression" => decisive_suppression(genuine),
        "deflated_reproduces_suppression" => !isempty(suppressed_deflated),
        "side_by_side" => Dict(
            "genuine_z" => genuine["z_matched_band"],
            "genuine_E" => genuine["E_max"],
            "genuine_c" => genuine["c"],
            "genuine_n_matched" => genuine["n_matched"],
            "genuine_outside" => genuine["outside_10pct"],
            "best_deflated_m" => get(best_deflated, "spin_lift", "none"),
            "best_deflated_z" => best_deflated["z_matched_band"],
            "best_deflated_E" => best_deflated["E_max"],
            "best_deflated_c" => best_deflated["c"],
            "best_deflated_n_matched" => best_deflated["n_matched"],
            "best_deflated_outside" => best_deflated["outside_10pct"],
        ),
    )
end

function z3_report_for_stat(stat, label::String, d::Int)
    sep = (stat["band_populated"] && (stat["E_matched_mean"] isa Number) && isfinite(stat["E_matched_mean"])) ?
          abs(stat["E_max"] - stat["E_matched_mean"]) : 0.0
    genuine = z3_separation_obstruction(sep)
    flat = z3_separation_obstruction(0.0)
    return Dict{String,Any}(
        "label" => label,
        "d" => d,
        "measured_separation" => sep,
        "genuine_or_deflated_verdict" => genuine,
        "flat_verdict" => flat,
        "load_bearing_flip" => genuine == "unsat" && flat == "sat" && sep > 1e-3,
        "encoding" => "assert flat=>sep==0, is_flat=true, and sep=round(1e9*|E_frame-E_matched_mean|); nonzero separation flips UNSAT while flat zero stays SAT",
    )
end

function run()
    println("="^96)
    println("DEFLATION SUBSTRATE BAND")
    println("  classification=deflation_substrate_poc  promotion_allowed=false")
    println("  observable: z=(E_frame - commutator-matched band mean)/std")
    println("  deflated family: one fixed Hopf base, vary only spin^c/connection lift m")
    println("="^96)

    dims = [2, 4, 8]
    levels = Dict{String,Any}()
    high_genuine = Bool[]
    high_deflated = Bool[]

    for d in dims
        lv = level(d, SEED)
        levels["d$d"] = lv
        if d in (4, 8)
            push!(high_genuine, lv["genuine_reproduces_suppression"])
            push!(high_deflated, lv["deflated_reproduces_suppression"])
        end
        sb = lv["side_by_side"]
        println("-"^96)
        println("d=$d  flat_E=", round(lv["flat"]["E_max"], sigdigits=4),
                " flat_floor=", lv["flat"]["E_flat_floor"],
                " band_c=[", round(lv["scale_swept_band"]["c_lo"], sigdigits=4),
                ", ", round(lv["scale_swept_band"]["c_hi"], sigdigits=4), "]")
        println("   genuine: z=", round(sb["genuine_z"], sigdigits=5),
                " E=", round(sb["genuine_E"], sigdigits=5),
                " c=", round(sb["genuine_c"], sigdigits=5),
                " n=", sb["genuine_n_matched"],
                " outside=", sb["genuine_outside"])
        println("   best single-base lift m=", sb["best_deflated_m"],
                ": z=", round(sb["best_deflated_z"], sigdigits=5),
                " E=", round(sb["best_deflated_E"], sigdigits=5),
                " c=", round(sb["best_deflated_c"], sigdigits=5),
                " n=", sb["best_deflated_n_matched"],
                " outside=", sb["best_deflated_outside"],
                " suppressed_lifts=", lv["suppressed_deflated_lifts"])
    end

    genuine_high_all = all(high_genuine)
    deflated_high_all = all(high_deflated)
    deflated_high_any = any(high_deflated)
    overall = if genuine_high_all && deflated_high_all
        "substrate_deflated"
    elseif genuine_high_all && !deflated_high_any
        "substrate_survives"
    else
        "mixed"
    end

    top_d = 8
    top = levels["d$top_d"]
    z3_genuine = z3_report_for_stat(top["genuine"], "genuine_hopf_rotor", top_d)
    z3_deflated = z3_report_for_stat(top["best_deflated_by_min_z"], "best_singlebase_lift", top_d)

    R = Dict{String,Any}(
        "object_id" => "deflation_substrate_band",
        "sim_id" => "deflation_substrate_band",
        "name" => "Single-base spin^c/connection-lift deflation control for substrate matched-band z",
        "version" => "1.0",
        "classification" => "deflation_substrate_poc",
        "promotion_allowed" => false,
        "promotion_status" => "diagnostic_only",
        "sim_execution_kind" => "nonclassical_poc",
        "sim_class" => "geometry_deflation_control",
        "script" => "layers/deflation_substrate_band.jl",
        "seed" => SEED,
        "n_rho" => N_RHO + 1,
        "n_random_band" => N_RAND,
        "spin_lifts_varied" => SPIN_LIFTS,
        "eta_base" => ETA_BASE,
        "non_numpy" => true,
        "bloch_free" => true,
        "finite_map" => "(carrier dim d, frame U) |-> dressed dissipative-Weyl channel Phi_B^A(rho)=U Phi_WeylL(U' rho U) U'; observable z=(E_frame-band_mean)/band_std over a +/-10% commutator-matched scale-swept random band. Genuine U is the existing Hopf rotor; deflated U_m fixes the Hopf base and varies only spin^c/connection lift m.",
        "domain" => "for each d in {2,4,8}: 21 density operators; upper op Weyl-L GKSL lifted to d; frames {genuine Hopf rotor, flat=I, single-base spin lifts m=1..7, 2000 scale-swept random controls}",
        "codomain_or_output" => "side-by-side genuine-vs-deflated matched-band z numbers, band bracket/population flags, flat floor control, Z3 flat=>sep==0 flip",
        "carrier_layer" => "density operators in D(C^d), d in {2,4,8}; Spin(3)/Spin(5)/Spin(7) Clifford gamma towers; fixed-base lift family is finite and does not vary shell eta or layer order",
        "geometry_layer" => "genuine Hopf rotor plus single fixed Hopf-base connection lifts over the same Clifford generator; scale-swept random band is not geometry",
        "spinor_state" => "unit spinors on S^3/S^7/S^15 read through the Hopf moment map; fixed-base deflation holds psi_A(d) constant and varies only m",
        "quaternion_action" => "d=4 uses Spin(5)=Sp(2) quaternionic Hopf generator; deflated m-lifts are connection choices on one fixed base, not a multi-shell nesting",
        "root_constraints_in_force" => [
            "F01 finite density-operator carrier / finite frame set / Weyl GKSL ops / dressed paths at d in {2,4,8}",
            "N01 frame conjugation [U,H0_d] != 0 order-sensitive control; matched band brackets this commutator magnitude",
        ],
        "dependency_receipts" => [
            "layers/substrate_effect_matched_band.jl (genuine Hopf rotor, scale-swept matched-band discriminator, flat/Z3 controls reused)",
            "layers/substrate_effect_matched_band_results.json (existing genuine d>=4 matched-band z<0 suppression target)",
            "layers/substrate_effect_scale_ladder.jl + _results.json (earlier Haar-band failure and scale ladder context)",
            "layers/weyl_on_nested_hopf_tori_V2.jl + _results.json (single-base spin^c lift deflation pattern for the holonomy-law observable)",
        ],
        "claim_ceiling" => "Tests only whether the substrate matched-band z<0 observable can be reproduced by a single fixed Hopf base with spin^c/connection lift variation. Does not admit nesting, layer completion, manifold admission, bridge, Axis0, flux, FEP, or physics. promotion_allowed=false.",
        "levels" => levels,
        "verdict" => Dict(
            "overall" => overall,
            "genuine_high_d_reproduces_suppression" => Dict("d4" => high_genuine[1], "d8" => high_genuine[2]),
            "deflated_high_d_reproduces_suppression" => Dict("d4" => high_deflated[1], "d8" => high_deflated[2]),
            "definition_substrate_deflated" => "single-base lift family has at least one bracketed/populated z<0 outside-band lift at both d=4 and d=8",
            "definition_substrate_survives" => "genuine d=4/d=8 suppression is present but no valid single-base lift reproduces it at either high dimension",
            "interpretation" => "If substrate_deflated, this observable is not evidence that the matched-band suppression needs genuine multi-shell nesting; it can be generated by ordinary fixed-base connection-lift geometry. If substrate_survives, the single-base lift control fails and the matched-band observable remains nesting-dependent. mixed keeps the split explicit.",
        ),
        "z3_load_bearing" => Dict(
            "genuine_top_d8" => z3_genuine,
            "best_deflated_top_d8" => z3_deflated,
        ),
        "required_negatives" => ["flat_frame_U_eq_I_each_d", "scale_swept_commutator_matched_random_band_brackets_c", "Z3_flat_implies_zero_separation_flip"],
        "negatives_run" => ["flat_frame_U_eq_I_each_d", "scale_swept_commutator_matched_random_band_brackets_c", "Z3_flat_implies_zero_separation_flip"],
        "kill_conditions" => [
            "flat frame must collapse E to floor at every d",
            "decisive genuine or deflated comparison must have c bracketed by the scale-swept random band and >=8 frames in the +/-10% matched band",
            "z<0 without outside_10pct is not counted as reproduction",
            "deflated reproduction must occur at both d=4 and d=8 for substrate_deflated",
        ],
        "tool_manifest" => Dict(
            "LinearAlgebra" => "load_bearing: matrix exp, svdvals trace norm, HS norms, opnorm Hermitian normalization, Clifford anticommutator checks",
            "Random" => "load_bearing: density operators and scale-swept random Hermitian generators",
            "Statistics" => "load_bearing: mean/std and z scores over matched bands",
            "Z3" => "load_bearing: flat=>sep==0 verdict flip on measured separation",
            "JSON" => "supportive: result receipt emission",
        ),
        "tool_integration_depth" => Dict("LinearAlgebra" => "load_bearing", "Random" => "load_bearing", "Statistics" => "load_bearing", "Z3" => "load_bearing", "JSON" => "supportive"),
        "downstream_blocks" => ["layer-completion", "manifold admission", "pairwise nesting promotion", "coupling", "bridge/Xi/Phi0/Axis0", "flux/FEP/physics", "final_manifold_admission"],
        "blocked_consumers" => ["layer-completion", "manifold admission", "pairwise nesting promotion", "coupling", "bridge/Xi/Phi0/Axis0", "flux/FEP/physics", "final_manifold_admission"],
        "status_ladder" => "exists < runs < passes local rerun",
    )

    sanitize(x::Float64) = isfinite(x) ? x : "non_finite($x)"
    sanitize(x::AbstractDict) = Dict(k => sanitize(v) for (k, v) in x)
    sanitize(x::AbstractVector) = [sanitize(v) for v in x]
    sanitize(x) = x

    open(RESULT_PATH, "w") do io
        JSON.print(io, sanitize(R), 2)
        write(io, "\n")
    end

    println("-"^96)
    println("VERDICT: ", overall)
    println("  genuine high-d suppression: d4=", high_genuine[1], " d8=", high_genuine[2])
    println("  deflated high-d suppression: d4=", high_deflated[1], " d8=", high_deflated[2])
    println("  Z3 genuine d8 flip=", z3_genuine["load_bearing_flip"],
            "  Z3 best-deflated d8 flip=", z3_deflated["load_bearing_flip"])
    println("Wrote: ", RESULT_PATH)
    return R
end

run()
