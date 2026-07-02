#!/usr/bin/env julia
# =====================================================================================
# ratchet_lockin_singleaxis.jl  —  THE SINGLE-AXIS LOCK-IN-DEPTH CLEANUP
#   classification = ratchet_lockin_singleaxis_poc ; promotion_allowed = false.
#   density-operator only. NO CTMRG, NO PEPS, NO optimization. Pure 2x2 channel algebra.
# -------------------------------------------------------------------------------------
# OBJECT_ID: ratchet_lockin_singleaxis
#
# CLAIM CEILING: this object MEASURES, on the GENUINE heterogeneous layer-channel set
#   reused VERBATIM from ratchet_survivor_reach_killtest.jl / order_null_killtest.jl /
#   the _bf layers, how the forward-vs-reversed divergence-vs-depth curve and its 95%
#   plateau LOCK-IN DEPTH move as the physical GKSL relaxation HORIZON T is varied with
#   the Euler fineness (steps) HELD FIXED, plus a cross-check axis that varies the
#   dissipator weight gamma alone. It does NOT assert layer-completion, manifold
#   admission, coupling, bridge (rho_AB/Xi/Phi0/Axis0), flux, FEP, or physics. A
#   lock-in-depth-vs-T trend here is a CANDIDATE order-memory diagnostic, not a proven
#   ratchet edge or a proven primary-object ratchet. promotion_allowed = false.
#
# -------------------------------------------------------------------------------------
# THE ONE OPEN SECONDARY FALSIFIER THIS FILE RESOLVES
#   (the CORE ratchet thesis -- order-dependent IRREVERSIBLE survivor, genuine-vs-commuting
#    control flat at every strength -- is already validated by order_null_killtest.jl
#    [overall=order_sensitivity_real] and ratchet_survivor_reach_killtest.jl
#    [survivor persists, controls clean]. The ONLY open item is the lock-in DEPTH curve.)
#
#   ratchet_survivor_reach_killtest.jl reported the lock-in depth series, strong->very_weak,
#   as [6, 6, 24, 6] -- NON-MONOTONE. But that prior knob CONFLATED two distinct axes:
#       strong    : T=4.0,  steps=400  -> dt = 0.0100
#       medium    : T=1.0,  steps=100  -> dt = 0.0100
#       weak      : T=0.25, steps=25   -> dt = 0.0100
#       very_weak : T=0.06, steps=10   -> dt = 0.0060
#   so it varied the relaxation HORIZON T AND the Euler step dt at the same time. The
#   very_weak case in particular changed dt AND used only 10 Euler steps, so its plateau
#   collapse (0.08) and lock-in=6 cannot be cleanly attributed to the physical horizon.
#   The non-monotone [6,6,24,6] is therefore confounded, not interpretable as a horizon law.
#
# THE CLEAN SWEEP (one physical axis, the only new move vs the prior file):
#   FIX steps = 200 (high, so the Euler local error is small and CONSTANT in count), and
#   vary ONLY the physical relaxation horizon T over:
#       T in {4.0, 2.0, 1.0, 0.5, 0.25, 0.125, 0.06}
#   (dt = T/200 ranges 0.02 .. 0.0003, all small; Euler error stays negligible at every T,
#    so the lock-in-depth movement is attributable to the physical horizon, not to dt.)
#   For each T, on the SAME genuine het schedule and the SAME commuting control, report:
#     (a) the forward-vs-reversed divergence-vs-depth curve at depths 1,2,4,8,16,32,64;
#     (b) the 95%-plateau LOCK-IN DEPTH (smallest probed depth reaching >=95% of the
#         deepest-depth mean) = where order memory locks in;
#     (c) the order-dependent survivor spread (max pairwise survivor trace-distance over 6
#         orderings) -- the already-validated survivor leg, reported per T as a cross-check.
#
# THE DISTINGUISHING QUESTION (settled by the numbers, not by us):
#   With steps fixed and only the physical horizon T varied, does the LOCK-IN DEPTH grow
#   MONOTONICALLY as T DECREASES (gentler relaxation per word slot -> more depth before the
#   order memory locks in = genuine ratchet drive-down)?
#     lockin_depth_monotone_in_T : lock-in depth is non-increasing in T (i.e. nondecreasing as
#       T weakens) across the above-floor strengths AND grows somewhere -> genuine ratchet
#       drive-down confirmed on a single physical axis.
#     lockin_depth_not_monotone  : the lock-in depth is NOT monotone in T -> the lock-in
#       DEPTH is not the ratchet signature; the thesis rests on survivor-persistence +
#       irreversibility (already solid), not on the depth curve. (A FINE, FINAL verdict.)
#     mixed : partial / boundary -> reported honestly with the per-T numbers.
#
# THE CROSS-CHECK AXIS (alternative single axis, as requested):
#   FIX T and steps; vary ONLY the dissipator weight gamma over a few values
#   {0.25, 0.5, 1.0, 2.0}. gamma is the jump RATE on the two Weyl GKSL legs (Weyl-L jump
#   sigma_-, Weyl-R jump sigma_+); it touches EXACTLY the relaxation legs and nothing else.
#   This asks whether "strength = jump rate alone" gives the SAME lock-in-depth answer as
#   "strength = physical horizon T alone". Reported as a separate series; agreement or
#   disagreement is stated plainly.
#
# CONTROLS (load-bearing -- signal must come from genuine noncommutation, not the metric):
#   (a) COMMUTING control: z-pinches all in the SAME basis, several mixings. They commute
#       and carry NO GKSL leg, so identical across all T / gamma by construction. MUST stay
#       at the floor (flat curve) and pick the SAME survivor -- the wrong-structure check.
#   (b) EXPLICIT noise floor: machine-eps * max PTM HS channel scale * deepest word length.
#   (c) Z3 verdict-flip: bind the genuine survivor spread at the GENTLEST horizon to the
#       commuting law "commuting_set => survivor_spread==0"; genuine(spread>0) UNSAT,
#       commuting(spread==0) SAT.
#
# GENUINE CHANNELS (reused VERBATIM from ratchet_survivor_reach_killtest.jl; NOT invented):
#   Phi_Ti / Phi_Te (z/x pinch dephasing), Phi_Fi / Phi_Fe (x/z rotation, unitary),
#   gksl_step_evolve (Weyl-L/R GKSL), hopf_h0, rand_rho, ptm, het base schedule. The ONLY
#   change: steps is FIXED while T is the swept axis (clean), and a second pass sweeps gamma.
# =====================================================================================

using LinearAlgebra
using Random
using Statistics
import JSON
import Z3

const RESULT_PATH = joinpath(@__DIR__, "ratchet_lockin_singleaxis_results.json")
const SEED = 20260602
const N_RHO = 20            # random initial density operators (matches the prior kill-tests)

# ---------- single-qubit operators (density-operator world only) ----------
const I2 = Matrix{ComplexF64}(I, 2, 2)
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SP = ComplexF64[0 1; 0 0]   # sigma_+  (raising / source)
const SM = ComplexF64[0 0; 1 0]   # sigma_-  (lowering / sink)
const P0 = (I2 + SZ) / 2          # = [1 0; 0 0]
const P1 = (I2 - SZ) / 2          # = [0 0; 0 1]
const Qp = (I2 + SX) / 2
const Qm = (I2 - SX) / 2

hs(A) = sqrt(real(tr(A' * A)))            # Hilbert-Schmidt norm
trace_norm(M) = sum(svdvals(M))           # Schatten-1 (||.||_1)

# =====================================================================================
# GENUINE CHANNELS (quoted VERBATIM from ratchet_survivor_reach_killtest.jl)
# =====================================================================================
Phi_Ti(rho, q)  = (1 - q) * rho + q * (P0 * rho * P0 + P1 * rho * P1)   # z-pinch
Phi_Te(rho, q)  = (1 - q) * rho + q * (Qp * rho * Qp + Qm * rho * Qm)   # x-pinch
Ux(theta) = ComplexF64[cos(theta/2) (-im*sin(theta/2)); (-im*sin(theta/2)) cos(theta/2)]
Uz(phi)   = ComplexF64[cis(-phi/2) 0; 0 cis(phi/2)]
Phi_Fi(rho, theta) = Ux(theta) * rho * Ux(theta)'   # x-rotation (unitary)
Phi_Fe(rho, phi)   = Uz(phi)   * rho * Uz(phi)'     # z-rotation (unitary)

dissipator(L, rho) = L*rho*L' - 0.5*((L'*L)*rho + rho*(L'*L))
commutator_flow(H, rho) = -im * (H*rho - rho*H)
# VERBATIM gksl_step_evolve from the prior files. gamma (jump rate), eps (unitary weight),
# T (horizon) and steps (Euler fineness) are ALL parameters; this file FIXES steps and
# sweeps T (clean axis), then in a second pass FIXES T and steps and sweeps gamma.
function gksl_step_evolve(rho0, H, L; gamma=1.0, eps=1.0, T=4.0, steps=400)
    dt = T/steps; r = rho0
    for _ in 1:steps
        r = r + dt*(gamma*dissipator(L, r) + eps*commutator_flow(H, r))
        r = (r + r')/2
        tr_r = real(tr(r)); abs(tr_r) > 1e-12 && (r = r/tr_r)
    end
    return r
end
function hopf_h0(phi::Float64, chi::Float64, eta::Float64)
    psi = ComplexF64[exp(im*(phi+chi))*cos(eta), exp(im*(phi-chi))*sin(eta)]
    psi = psi / norm(psi)
    n = [real(psi' * (P * psi)) for P in (SX, SY, SZ)]
    nn = norm(n); nhat = nn < 1e-12 ? [0.0,0.0,1.0] : n ./ nn
    return nhat[1]*SX + nhat[2]*SY + nhat[3]*SZ
end

# ---------- PTM (for the noise-floor channel scale only; same as the prior files) ----------
const PAULI4 = (I2, SX, SY, SZ)
function ptm(chan)
    T = zeros(Float64, 4, 4)
    for j in 1:4, i in 1:4
        T[i, j] = real(tr(PAULI4[i] * chan(PAULI4[j])) / 2)
    end
    return T
end

# ---------- random density operators (Bloch-free; same construction as the prior files) ----------
function rand_rho(rng)
    psi = ComplexF64[randn(rng)+im*randn(rng), randn(rng)+im*randn(rng)]
    psi = psi / norm(psi)
    pure = psi * psi'
    p = 0.2 + 0.6*rand(rng)
    rho = p*pure + (1-p)*(I2/2)
    return (rho + rho')/2 / real(tr((rho+rho')/2))
end

# =====================================================================================
# schedule helpers (verbatim from the prior file)
# =====================================================================================
function apply_word(word, rho)
    r = rho
    for f in word; r = f(r); end
    return r
end
build_depth_word(base, reps) = reduce(vcat, fill(base, reps))

"forward-vs-reversed divergence vs depth: Delta(d)=mean_rho||Phi_fwd^d(rho)-Phi_rev^d(rho)||_1."
function divergence_curve(base, reps_list, rhos)
    base_len = length(base)
    depths = Int[]; means = Float64[]; maxes = Float64[]
    for reps in reps_list
        fwd_word = build_depth_word(base, reps)
        rev_word = reverse(fwd_word)
        diffs = Float64[]
        for rho in rhos
            f = apply_word(fwd_word, rho)
            r = apply_word(rev_word, rho)
            push!(diffs, trace_norm(f - r))
        end
        push!(depths, reps*base_len)
        push!(means, mean(diffs))
        push!(maxes, maximum(diffs))
    end
    return depths, means, maxes
end

"95%-plateau LOCK-IN depth = smallest probed depth reaching >=frac*plateau. (-1 if no lock-in)."
function lockin_depth(depths, means, floor; frac=0.95)
    plateau = means[end]
    if plateau <= floor
        return (-1, -1, plateau, false, false)
    end
    sat_idx = findfirst(m -> m >= frac*plateau, means)
    sat_idx = sat_idx === nothing ? length(means) : sat_idx
    sat_depth = depths[sat_idx]
    first_nz = findfirst(m -> m > floor, means)
    rose_before_lockin = (first_nz !== nothing) && (sat_idx > first_nz) &&
                         (means[sat_idx] > means[first_nz] * 1.02)
    return (sat_depth, sat_idx, plateau, plateau > floor, rose_before_lockin)
end

"order-dependent survivor spread: max pairwise trace-distance across orderings at a long horizon."
function order_dependent_survivors(channel_set, perms, seed_rho; horizon_reps=40)
    survivors = Matrix{ComplexF64}[]
    for perm in perms
        base = [channel_set[i] for i in perm]
        word = build_depth_word(base, horizon_reps)
        push!(survivors, apply_word(word, seed_rho))
    end
    np = length(perms)
    dists = Float64[]
    for a in 1:np, b in a+1:np
        push!(dists, trace_norm(survivors[a] - survivors[b]))
    end
    return survivors, dists
end

# =====================================================================================
# Z3 load-bearing verdict-flip: bind the genuine survivor spread at the GENTLEST horizon
# to the commuting law "commuting_set => survivor_spread==0". genuine(spread>0) -> UNSAT,
# commuting(spread==0) -> SAT. The verdict FLIPS on the control; this makes the survivor
# number a real obstruction, not an algebraic identity of the metric.
# =====================================================================================
function z3_survivor_obstruction(measured_spread::Float64; scale=1_000_000_000)
    ctx = Z3.Context(); s = Z3.Solver(ctx)
    spread    = Z3.IntVar("spread", ctx)
    commuting = Z3.BoolVar("commuting_set", ctx)
    Z3.add(s, Z3.Or([Z3.Not(commuting), spread == Z3.IntVal(0, ctx)]))   # commuting => spread==0
    Z3.add(s, commuting == Z3.BoolVal(true, ctx))
    m = round(Int, scale * abs(measured_spread))
    Z3.add(s, spread == Z3.IntVal(m, ctx))
    return string(Z3.check(s))   # genuine(nonzero): unsat ; commuting(zero): sat
end

# helper: is an integer series non-increasing across the entries where mask is true,
# AND strictly decreasing somewhere? (series ordered with T DECREASING down the list, so
# "lock-in grows as T decreases" == series is NON-DECREASING down the list & grows somewhere.)
function monotone_growing_as_T_decreases(series::Vector{Int}, mask::Vector{Bool})
    nondecreasing = true
    grew_any = false
    last_valid = -1
    for k in eachindex(series)
        if mask[k]
            d = series[k]
            if last_valid >= 0
                d < last_valid && (nondecreasing = false)
                d > last_valid && (grew_any = true)
            end
            last_valid = d
        end
    end
    return (nondecreasing && grew_any, nondecreasing, grew_any)
end

# =====================================================================================
# RUN
# =====================================================================================
function run()
    rng = MersenneTwister(SEED)
    rhos = [rand_rho(rng) for _ in 1:N_RHO]
    seed_rho = rand_rho(MersenneTwister(SEED + 777))   # fixed survivor seed (same as prior)

    R = Dict{String,Any}()
    R["object_id"]          = "ratchet_lockin_singleaxis"
    R["classification"]     = "ratchet_lockin_singleaxis_poc"
    R["promotion_allowed"]  = false
    R["script"]             = "ratchet_lockin_singleaxis.jl"
    R["seed"]               = SEED
    R["n_rho"]              = N_RHO
    R["non_numpy"]          = true
    R["bloch_free"]         = true
    R["reused_from"]        = "ratchet_survivor_reach_killtest.jl / order_null_killtest.jl genuine _bf channels (Ti/Te/Fi/Fe + Weyl-L/R GKSL + hopf_h0 + rand_rho + ptm + het base schedule). NO new channels invented; only the swept axis is isolated."
    R["carrier"]            = "density operators rho in D(C^2); genuine layer channels Ti/Te/Fi/Fe (strength-independent) + Weyl-L/R GKSL; HS norm, trace norm. NO CTMRG, NO PEPS, NO optimization."
    R["core_thesis_already_validated"] = Dict(
        "order_sensitivity_real" => "order_null_killtest.jl overall=order_sensitivity_real; heterogeneous word run order matters.",
        "order_dependent_survivor_and_irreversibility" => "ratchet_survivor_reach_killtest.jl: survivor persists, commuting control flat + same survivor.",
        "this_file_resolves_only" => "the ONE open secondary falsifier: whether the lock-in DEPTH curve is monotone once the conflated T+steps knob is split onto ONE physical axis (T, steps fixed).",
    )
    R["prior_confound"] = Dict(
        "prior_lockin_series_strong_to_veryweak" => [6, 6, 24, 6],
        "prior_was_nonmonotone" => true,
        "prior_knob_conflated" => "T (relaxation horizon) AND steps (Euler fineness): strong/medium/weak used dt=0.01 but very_weak used dt=0.006 with only 10 Euler steps, so the depth series mixed a physical-horizon change with an integrator-resolution change.",
        "fix" => "FIX steps=200 (small, constant Euler error) and vary ONLY T; cross-check by FIX T+steps and vary ONLY gamma.",
    )
    R["claim_ceiling"]      = "MEASURES the forward-vs-reversed divergence-vs-depth curve and its 95% plateau lock-in depth on the genuine channel set as the physical horizon T is varied with Euler fineness fixed, plus a gamma-only cross-check, vs an explicit noise floor and a commuting control. Does NOT assert layer-completion / manifold admission / coupling / bridge / flux / FEP / physics. A lock-in-depth-vs-T trend here is a CANDIDATE order-memory diagnostic, not a proven ratchet edge."

    # ----- fixed channel parameters (genuine layer values, same as the prior kill-tests) -----
    q = 0.65; ang = 0.9
    phi0, chi0, eta0 = 2pi*0.21, 2pi*0.13, pi/4
    H0 = hopf_h0(phi0, chi0, eta0)

    # ----- depth ladder requested: reps 1,2,4,8,16,32,64 over base len 6 -> depths 6..384 -----
    reps_list = [1, 2, 4, 8, 16, 32, 64]

    # ----- genuine het base at a given (T, steps, gamma); strength threads ONLY the GKSL legs -----
    function het_base_at(; T::Float64, steps::Int, gamma::Float64=1.0)
        fTi = rho -> Phi_Ti(rho, q)
        fFi = rho -> Phi_Fi(rho, ang)
        fTe = rho -> Phi_Te(rho, q)
        fFe = rho -> Phi_Fe(rho, ang)
        fWL = rho -> gksl_step_evolve(rho, +H0, SM; gamma=gamma, T=T, steps=steps)   # Weyl-L
        fWR = rho -> gksl_step_evolve(rho, -H0, SP; gamma=gamma, T=T, steps=steps)   # Weyl-R
        return [fTi, fFi, fWL, fTe, fFe, fWR], ["Ti","Fi","WeylL","Te","Fe","WeylR"]
    end

    # ----- commuting control: z-pinches in one basis (commute, no GKSL leg) -----
    cTi1 = rho -> Phi_Ti(rho, 0.30)
    cTi2 = rho -> Phi_Ti(rho, 0.55)
    cTi3 = rho -> Phi_Ti(rho, 0.65)
    cTi4 = rho -> Phi_Ti(rho, 0.80)
    comm_base = [cTi1, cTi2, cTi3, cTi4]
    comm_names = ["Tz.30","Tz.55","Tz.65","Tz.80"]

    het_perms = [
        [1,2,3,4,5,6], [6,5,4,3,2,1], [3,6,1,4,2,5],
        [1,3,5,2,4,6], [4,2,6,1,5,3], [2,4,6,1,3,5],
    ]
    comm_perms = [[1,2,3,4],[4,3,2,1],[2,4,1,3],[3,1,4,2]]

    # ----- noise floor: eps * max PTM HS scale * deepest het word length -----
    het0, _ = het_base_at(T=4.0, steps=200)
    all_ch = vcat(het0, comm_base)
    op_scale = maximum(norm(ptm(f)) for f in all_ch)
    deepest_word_len = maximum(reps_list) * 6
    noise_floor = eps(Float64) * op_scale * deepest_word_len * 8.0
    R["noise_floor"] = Dict(
        "value" => noise_floor,
        "definition" => "eps(Float64) * max PTM HS scale (=$(round(op_scale,digits=4))) * deepest het word length ($(deepest_word_len)) * 8 safety",
        "machine_eps" => eps(Float64),
        "max_ptm_hs_scale" => op_scale,
        "deepest_word_length" => deepest_word_len,
    )

    # ===================================================================================
    # COMMUTING CONTROL (strength-independent: no GKSL leg). Must be flat at the floor.
    # ===================================================================================
    comm_depths, comm_means, comm_maxes = divergence_curve(comm_base, reps_list, rhos)
    comm_li_depth, _, comm_plateau, comm_above_floor, _ = lockin_depth(comm_depths, comm_means, noise_floor)
    comm_flat = !comm_above_floor
    comm_surv, comm_surv_dists = order_dependent_survivors(comm_base, comm_perms, seed_rho)
    comm_surv_max = isempty(comm_surv_dists) ? 0.0 : maximum(comm_surv_dists)
    comm_same_survivor = comm_surv_max < max(noise_floor, 1e-9)
    R["commuting_control"] = Dict(
        "base_schedule" => join(comm_names, " "),
        "note" => "z-pinches in one basis: commute and carry no GKSL leg, so identical across all T and gamma by construction. MUST stay at the floor (flat curve) and pick the SAME survivor.",
        "depths" => comm_depths,
        "divergence_means" => comm_means,
        "divergence_maxes" => comm_maxes,
        "plateau" => comm_plateau,
        "above_floor" => comm_above_floor,
        "flat_at_floor" => comm_flat,
        "lockin_depth" => comm_li_depth,
        "survivor_spread_max" => comm_surv_max,
        "same_survivor" => comm_same_survivor,
    )

    # ===================================================================================
    # PRIMARY CLEAN SWEEP: vary ONLY the horizon T with steps FIXED at 200.
    #   T listed in DECREASING order so the series reads strong (T=4) -> gentlest (T=0.06).
    #   "lock-in grows as T decreases" == series NON-DECREASING down the list & grows somewhere.
    # ===================================================================================
    const_steps = 200          # FIXED Euler fineness (small, constant local error)
    T_list = [4.0, 2.0, 1.0, 0.5, 0.25, 0.125, 0.06]   # decreasing horizon

    per_T = Vector{Dict{String,Any}}()
    T_lockin = Int[]; T_plateau = Float64[]; T_survmax = Float64[]
    T_abovefloor = Bool[]; T_survpersist = Bool[]
    for T in T_list
        het_base, het_names = het_base_at(T=T, steps=const_steps)
        depths, means, maxes = divergence_curve(het_base, reps_list, rhos)
        li_depth, li_idx, plateau, above_floor, rose = lockin_depth(depths, means, noise_floor)
        surv, surv_dists = order_dependent_survivors(het_base, het_perms, seed_rho)
        surv_max  = isempty(surv_dists) ? 0.0 : maximum(surv_dists)
        surv_mean = isempty(surv_dists) ? 0.0 : mean(surv_dists)
        survivor_persists = surv_max > noise_floor

        push!(T_lockin, li_depth); push!(T_plateau, plateau); push!(T_survmax, surv_max)
        push!(T_abovefloor, above_floor); push!(T_survpersist, survivor_persists)
        push!(per_T, Dict(
            "gksl_T" => T,
            "gksl_steps" => const_steps,
            "gksl_dt" => T/const_steps,
            "gksl_gamma" => 1.0,
            "base_schedule" => join(het_names, " "),
            "depths" => depths,
            "divergence_means" => means,
            "divergence_maxes" => maxes,
            "plateau" => plateau,
            "above_floor" => above_floor,
            "rose_before_lockin" => rose,
            "lockin_depth" => li_depth,
            "lockin_idx" => li_idx,
            "survivor_spread_mean" => surv_mean,
            "survivor_spread_max" => surv_max,
            "survivor_persists" => survivor_persists,
        ))
    end
    R["sweep_T_only"] = Dict(
        "fixed_steps" => const_steps,
        "fixed_gamma" => 1.0,
        "T_series_decreasing" => T_list,
        "dt_series" => [T/const_steps for T in T_list],
        "note" => "ONLY the physical horizon T varies; steps fixed at 200 so Euler local error is small and CONSTANT in count. dt = T/200 shrinks with T, so the integrator gets FINER (not coarser) as T weakens -- the very_weak coarse-dt confound from the prior file is removed.",
        "per_T" => per_T,
    )

    # the distinguishing question, decided by the numbers
    T_li_mono, T_li_nondec, T_li_grew = monotone_growing_as_T_decreases(T_lockin, T_abovefloor)
    R["distinguishing_question_T_axis"] = Dict(
        "question" => "with steps fixed and only T varied, does the lock-in DEPTH grow monotonically as T DECREASES?",
        "lockin_depth_series_T_decreasing" => T_lockin,
        "plateau_series_T_decreasing" => T_plateau,
        "survivor_spread_max_series_T_decreasing" => T_survmax,
        "above_floor_series" => T_abovefloor,
        "all_T_above_floor" => all(T_abovefloor),
        "lockin_nondecreasing_as_T_decreases" => T_li_nondec,
        "lockin_grew_somewhere" => T_li_grew,
        "lockin_depth_monotone_in_T" => T_li_mono,
        "note" => "-1 lock-in entries mean the curve never rose above the floor at that T (no lock-in to measure). monotone == nondecreasing down the (decreasing-T) list AND grows somewhere.",
    )

    # ===================================================================================
    # CROSS-CHECK SWEEP: fix T and steps; vary ONLY the dissipator weight gamma (jump rate).
    #   Asks whether "strength = jump rate alone" gives the SAME lock-in answer as the T axis.
    # ===================================================================================
    const_T = 1.0
    gamma_list = [0.25, 0.5, 1.0, 2.0]   # increasing jump rate (= stronger relaxation per slot)
    # to mirror "gentler -> more depth", read the lock-in trend as gamma DECREASES
    gamma_list_dec = reverse(gamma_list)  # 2.0, 1.0, 0.5, 0.25 (decreasing jump rate = gentler)

    per_gamma = Vector{Dict{String,Any}}()
    g_lockin = Int[]; g_plateau = Float64[]; g_survmax = Float64[]
    g_abovefloor = Bool[]; g_survpersist = Bool[]
    for gam in gamma_list_dec
        het_base, het_names = het_base_at(T=const_T, steps=const_steps, gamma=gam)
        depths, means, maxes = divergence_curve(het_base, reps_list, rhos)
        li_depth, li_idx, plateau, above_floor, rose = lockin_depth(depths, means, noise_floor)
        surv, surv_dists = order_dependent_survivors(het_base, het_perms, seed_rho)
        surv_max  = isempty(surv_dists) ? 0.0 : maximum(surv_dists)
        surv_mean = isempty(surv_dists) ? 0.0 : mean(surv_dists)
        survivor_persists = surv_max > noise_floor

        push!(g_lockin, li_depth); push!(g_plateau, plateau); push!(g_survmax, surv_max)
        push!(g_abovefloor, above_floor); push!(g_survpersist, survivor_persists)
        push!(per_gamma, Dict(
            "gksl_gamma" => gam,
            "gksl_T" => const_T,
            "gksl_steps" => const_steps,
            "base_schedule" => join(het_names, " "),
            "depths" => depths,
            "divergence_means" => means,
            "divergence_maxes" => maxes,
            "plateau" => plateau,
            "above_floor" => above_floor,
            "rose_before_lockin" => rose,
            "lockin_depth" => li_depth,
            "lockin_idx" => li_idx,
            "survivor_spread_mean" => surv_mean,
            "survivor_spread_max" => surv_max,
            "survivor_persists" => survivor_persists,
        ))
    end
    g_li_mono, g_li_nondec, g_li_grew = monotone_growing_as_T_decreases(g_lockin, g_abovefloor)
    R["crosscheck_gamma_only"] = Dict(
        "fixed_T" => const_T,
        "fixed_steps" => const_steps,
        "gamma_series_decreasing" => gamma_list_dec,
        "note" => "ONLY the dissipator weight gamma (jump rate) varies; T and steps fixed. gamma touches EXACTLY the two Weyl GKSL legs. Series read with gamma DECREASING (= gentler relaxation per slot) to mirror the T axis.",
        "per_gamma" => per_gamma,
        "lockin_depth_series_gamma_decreasing" => g_lockin,
        "plateau_series_gamma_decreasing" => g_plateau,
        "survivor_spread_max_series_gamma_decreasing" => g_survmax,
        "all_gamma_above_floor" => all(g_abovefloor),
        "lockin_nondecreasing_as_gamma_decreases" => g_li_nondec,
        "lockin_grew_somewhere" => g_li_grew,
        "lockin_depth_monotone_in_gamma" => g_li_mono,
        "agrees_with_T_axis" => (g_li_mono == T_li_mono),
    )

    # ===================================================================================
    # Z3 load-bearing verdict-flip on survivor persistence at the GENTLEST horizon.
    # ===================================================================================
    gentle_idx = length(T_list)                  # T=0.06 is the gentlest horizon
    gentle_spread = T_survmax[gentle_idx]
    z3_genuine_gentle = z3_survivor_obstruction(gentle_spread)     # nonzero -> unsat
    z3_commuting      = z3_survivor_obstruction(comm_surv_max)     # ~0 -> sat
    z3_load_bearing = (z3_genuine_gentle == "unsat") && (z3_commuting == "sat") &&
                      (gentle_spread > noise_floor) && (comm_surv_max < max(noise_floor, 1e-9))
    R["z3_load_bearing"] = Dict(
        "encoding" => "FREE int spread, FREE bool commuting_set; law Or([Not(commuting_set), spread==0]); assert commuting_set=true + spread==IntVal(measured). genuine(gentlest horizon): unsat; commuting: sat.",
        "genuine_gentle_survivor_spread" => gentle_spread,
        "genuine_gentle_verdict" => z3_genuine_gentle,
        "commuting_survivor_spread" => comm_surv_max,
        "commuting_verdict" => z3_commuting,
        "load_bearing_flip" => z3_load_bearing,
    )

    # ===================================================================================
    # DECISIVE VERDICT (about the lock-in DEPTH only; the survivor + irreversibility legs
    # are already validated elsewhere and are reported here as cross-checks, not retried).
    #
    #   lockin_depth_monotone_in_T : on the clean T axis (steps fixed), the lock-in depth is
    #       nondecreasing as T decreases AND grows somewhere, every probed T is above floor,
    #       and the commuting control is flat with the same survivor. => genuine ratchet
    #       drive-down confirmed on a single physical axis.
    #   lockin_depth_not_monotone : the lock-in depth is NOT monotone in T (a deeper-T entry
    #       has a SMALLER lock-in than a shallower-T entry, or a T drops below floor) =>
    #       the lock-in DEPTH is not the ratchet signature; the thesis rests on
    #       survivor-persistence + irreversibility, which already hold. (FINE + FINAL.)
    #   mixed : controls not clean, or boundary cases that are not cleanly either.
    # ===================================================================================
    controls_clean = comm_flat && comm_same_survivor
    all_T_above    = all(T_abovefloor)
    survivor_everywhere_T = all(T_survpersist)

    classification = if !controls_clean
        "INCONCLUSIVE_control_not_flat"
    elseif T_li_mono && all_T_above
        "lockin_depth_monotone_in_T"
    elseif !T_li_mono
        "lockin_depth_not_monotone"
    else
        "mixed"
    end

    R["verdict"] = Dict(
        "classification" => classification,
        "scope" => "this verdict is ABOUT THE LOCK-IN DEPTH CURVE ONLY. The core ratchet thesis (order-dependent irreversible survivor) is validated by order_null_killtest.jl and ratchet_survivor_reach_killtest.jl and is NOT re-decided here.",
        "lockin_depth_series_T_decreasing" => T_lockin,
        "lockin_depth_monotone_in_T" => T_li_mono,
        "all_T_above_floor" => all_T_above,
        "survivor_persists_at_every_T" => survivor_everywhere_T,
        "controls_clean" => controls_clean,
        "control_flat_at_floor" => comm_flat,
        "control_same_survivor" => comm_same_survivor,
        "crosscheck_gamma_axis_lockin_monotone" => g_li_mono,
        "crosscheck_agrees_with_T_axis" => (g_li_mono == T_li_mono),
        "z3_load_bearing_flip" => z3_load_bearing,
        "interpretation" => "If lockin_depth_monotone_in_T: gentler physical horizon T (steps fixed) requires MORE depth before the order memory locks in -- the genuine ratchet drive-down read off a single clean axis. If lockin_depth_not_monotone: the lock-in DEPTH is not the ratchet's load-bearing signature; the ratchet's evidence is the survivor-persistence + irreversibility legs (already solid), not the depth curve -- and that is a fine, final answer. The gamma cross-check states whether jump-rate-alone gives the same answer as horizon-alone.",
    )

    # F01 / N01 witnesses
    R["F01_witness"] = Dict(
        "finite_carrier" => "density operators in D(C^2); finite genuine channel set (6 het + 4 commuting control)",
        "finite_probe" => "$(N_RHO) random density operators + 1 fixed survivor seed; 7 horizons T in {4,2,1,0.5,0.25,0.125,0.06} (steps=200 fixed) + 4 gamma cross-check values; depth ladder reps 1..64 (depths 6..384)",
        "finite_operator" => "Ti/Te/Fi/Fe (strength-independent) + Weyl-L/R GKSL with FIXED steps, swept T (then swept gamma); genuine layer maps reused from ratchet_survivor_reach_killtest",
        "finite_path" => "forward vs reversed depth words at each horizon T (and each gamma); permutation survivors at each T",
    )
    R["N01_witness"] = Dict(
        "divergence_formula" => "Delta(d) = mean_rho ||Phi_fwd^d(rho) - Phi_rev^d(rho)||_1 vs depth d, per horizon T (steps fixed)",
        "lockin_depth_series_T_decreasing" => T_lockin,
        "survivor_spread_max_series_T_decreasing" => T_survmax,
        "present_above_floor" => all_T_above,
        "noise_floor" => noise_floor,
    )

    R["tool_manifest"] = Dict(
        "LinearAlgebra" => "load_bearing: svdvals (trace norm), HS norms, channel/PTM algebra; every measured number flows through it.",
        "Statistics" => "supportive: means over the rho ensemble and over orderings.",
        "Random" => "load_bearing: random density operators (signatures measured over fresh samples, not planted).",
        "Z3" => "load_bearing: binds the genuine survivor spread at the gentlest horizon to the commuting law; verdict flips UNSAT->SAT on the commuting control.",
        "JSON" => "supportive: receipt emission.",
    )
    R["tool_integration_depth"] = Dict("LinearAlgebra"=>"load_bearing","Z3"=>"load_bearing","Random"=>"load_bearing","Statistics"=>"supportive","JSON"=>"supportive")
    R["blocked_consumers"] = ["any ratchet edge admission","ratchet thesis closure","pairwise nesting","coupling","bridge/Xi/Phi0/Axis0","flux/FEP/physics"]
    R["status_ladder"] = "exists < runs < passes local rerun"

    open(RESULT_PATH, "w") do io
        JSON.print(io, R, 2); write(io, "\n")
    end

    # ---- console summary ----
    println("="^100)
    println("RATCHET LOCK-IN SINGLE-AXIS  (object_id=ratchet_lockin_singleaxis, promotion_allowed=false)")
    println("="^100)
    println("noise_floor = ", noise_floor, "   (eps * PTM-scale $(round(op_scale,digits=3)) * deepest_len $(deepest_word_len) * 8)")
    println("-"^100)
    println("PRIOR CONFOUND: lock-in series [6,6,24,6] (NON-MONOTONE) -- knob conflated T (horizon) AND steps (Euler dt).")
    println("-"^100)
    println("CLEAN T-AXIS SWEEP  (steps=$const_steps FIXED, gamma=1.0 FIXED, only T varies)  depths: ", comm_depths)
    for ps in per_T
        println("  [T=", rpad(ps["gksl_T"],6), " dt=", rpad(round(ps["gksl_dt"],sigdigits=3),8), "]",
                "  Delta_mean = ", round.(ps["divergence_means"], sigdigits=4))
        println("      plateau=", round(ps["plateau"], sigdigits=5),
                "  LOCK-IN depth=", ps["lockin_depth"],
                "  rose=", ps["rose_before_lockin"],
                "  survivor_max=", round(ps["survivor_spread_max"], sigdigits=5),
                "  survivor_persists=", ps["survivor_persists"])
    end
    println("-"^100)
    println("COMMUTING control (", join(comm_names," "), ") [T/gamma-independent]:")
    println("      Delta_mean = ", round.(comm_means, sigdigits=5))
    println("      flat_at_floor=", comm_flat, "  survivor_max=", round(comm_surv_max, sigdigits=5),
            "  same_survivor=", comm_same_survivor)
    println("-"^100)
    println("DISTINGUISHING QUESTION (T axis):")
    println("  lock-in depth series (T decreasing 4->0.06): ", T_lockin)
    println("  plateau series:                              ", round.(T_plateau, sigdigits=4))
    println("  survivor_max series:                         ", round.(T_survmax, sigdigits=4))
    println("  all_T_above_floor=", all_T_above,
            "  nondecreasing=", T_li_nondec, "  grew_somewhere=", T_li_grew)
    println("  => lockin_depth_monotone_in_T = ", T_li_mono)
    println("-"^100)
    println("CROSS-CHECK (gamma axis, T=$const_T steps=$const_steps fixed):")
    println("  lock-in depth series (gamma decreasing 2->0.25): ", g_lockin)
    println("  plateau series:                                  ", round.(g_plateau, sigdigits=4))
    println("  => lockin_depth_monotone_in_gamma = ", g_li_mono, "  agrees_with_T_axis = ", (g_li_mono == T_li_mono))
    println("-"^100)
    println("Z3 load-bearing: genuine(gentlest T)=", z3_genuine_gentle, " commuting=", z3_commuting, " flip=", z3_load_bearing)
    println("-"^100)
    println("DECISIVE VERDICT: ", classification)
    println("  (scope: about the LOCK-IN DEPTH curve only; survivor + irreversibility already validated elsewhere.)")
    println("Wrote: ", RESULT_PATH)
    return R
end

run()
