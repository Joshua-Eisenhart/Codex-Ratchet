#!/usr/bin/env julia
# =====================================================================================
# ratchet_survivor_reach_killtest.jl  —  THE SATURATION-vs-ARTIFACT KILL-TEST
#   classification = ratchet_survivor_reach_killtest_poc ; promotion_allowed = false.
#   density-operator only. NO CTMRG, NO PEPS, NO optimization. Pure 2x2 channel algebra.
# -------------------------------------------------------------------------------------
# OBJECT_ID: ratchet_survivor_reach_killtest
#
# CLAIM CEILING: this object MEASURES, over the GENUINE heterogeneous layer-channel set
#   reused VERBATIM from ratchet_accumulation_killtest.jl / order_null_killtest.jl / the
#   _bf layers, how the forward-vs-reversed divergence-vs-depth curve and its SATURATION
#   DEPTH (lock-in depth) move as the GKSL relaxation STRENGTH is weakened, and whether the
#   order-dependent survivor persists at each strength. It does NOT assert layer-completion,
#   manifold admission, coupling, bridge (rho_AB/Xi/Phi0/Axis0), flux, FEP, or physics.
#   A saturation-depth-vs-strength scaling here is a CANDIDATE order-memory lock-in
#   diagnostic, not a proven ratchet edge or a proven primary-object ratchet.
#   promotion_allowed = false.
#
# -------------------------------------------------------------------------------------
# THE ONE OPEN FALSIFIER THIS FILE RESOLVES (from ratchet_accumulation_killtest.jl):
#   That prior file found the genuine channel stack is IRREVERSIBLE + picks an
#   ORDER-DEPENDENT SURVIVOR (2/3 ratchet signatures, controls clean), BUT the
#   forward-vs-reversed divergence SATURATED at ~0.3528 from depth ~6 onward instead of
#   accumulating monotonically. Its strong GKSL setting (T=4, steps=400) drove every word
#   to its attractor by the first probed depth.
#   OPEN QUESTION: is that saturation
#     (A) the genuine ratchet REACHING ITS SURVIVOR (drive-down-till-you-cant, then lock
#         in — the intended ratchet behavior), distinguishable because a GENTLER GKSL step
#         should require MORE depth before locking in (saturation depth grows as strength
#         weakens), while STILL saturating to a survivor and STILL picking an order-dependent
#         survivor; OR
#     (B) an ARTIFACT of strong GKSL relaxation — in which case weakening GKSL either makes
#         the divergence go FLAT/near-zero at every depth (no order effect to accumulate) or
#         grow without ever locking in (no survivor).
#
# -------------------------------------------------------------------------------------
# THE DECISIVE SWEEP (the only new move vs the prior file):
#   Make the GKSL step STRENGTH a tunable (T, steps) parameter and re-run the
#   forward-vs-reversed divergence-vs-depth curve at depths 1,2,4,8,16,32,64 at FOUR
#   strengths on the SAME genuine het schedule and the SAME commuting control:
#     strong    : T=4.0,  steps=400   (the prior setting)
#     medium    : T=1.0,  steps=100
#     weak      : T=0.25, steps=25
#     very_weak : T=0.06, steps=10
#   The non-GKSL genuine channels (z/x pinch, x/z rotation) are strength-INDEPENDENT by
#   construction; only the two Weyl GKSL channels (Weyl-L H=+H0 jump sigma_-, Weyl-R
#   H=-H0 jump sigma_+) carry (T, steps). So the strength knob touches EXACTLY the
#   relaxation legs and nothing else — the right knob for the open question.
#   For each strength report:
#     (a) the divergence-vs-depth curve;
#     (b) the SATURATION DEPTH = the smallest probed depth whose mean reaches >= 95% of the
#         plateau (the deepest-depth mean) — i.e. where order memory LOCKS IN;
#     (c) whether the order-dependent-survivor signature persists at that strength.
#
# DISTINGUISHING PREDICTIONS (settled by the numbers, not by us):
#   GENUINE ratchet-to-survivor -> saturation depth INCREASES as strength weakens, the curve
#     STILL saturates to a survivor, and the order-dependent survivor PERSISTS at every
#     strength -> verdict ratchet_reaches_survivor.
#   ARTIFACT -> weaker GKSL leaves divergence flat/near-zero at all depths (no order effect)
#     OR growing without locking in (no survivor) -> verdict saturation_was_artifact.
#   Anything in between -> mixed, reported honestly with the per-strength numbers.
#
# REFRAME OBSERVABLE: treat the SATURATION DEPTH itself as the ratchet observable
#   (the lock-in depth) and report how it scales across the four strengths.
#
# CONTROLS (load-bearing — the signal must come from genuine noncommutation, not the metric):
#   (a) COMMUTING control: z-pinches all in the SAME basis at several strengths. These
#       commute; the control MUST be flat at the floor at EVERY GKSL strength. (The commuting
#       control has NO GKSL leg, so it is identical across strengths by construction; that it
#       stays at the floor is still the wrong-structure check that the metric is not
#       manufacturing divergence.)
#   (b) EXPLICIT noise floor: machine-eps * PTM HS channel scale * deepest word length.
#   (c) Z3 verdict-flip: bind the genuine survivor-persistence at the weakest strength to the
#       commuting law "commuting_set => survivor_spread==0"; genuine(spread>0) UNSAT,
#       commuting(spread==0) SAT.
#
# GENUINE CHANNELS (reused VERBATIM from ratchet_accumulation_killtest.jl; NOT invented):
#   Phi_Ti / Phi_Te (z/x pinch dephasing), Phi_Fi / Phi_Fe (x/z rotation, unitary),
#   gksl_step_evolve (Weyl-L/R GKSL), hopf_h0, rand_rho, ptm. Only difference: the GKSL
#   step's (T, steps) are threaded through as the strength parameter instead of fixed.
# =====================================================================================

using LinearAlgebra
using Random
using Statistics
import JSON
import Z3

const RESULT_PATH = joinpath(@__DIR__, "ratchet_survivor_reach_killtest_results.json")
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
# GENUINE CHANNELS (quoted VERBATIM from ratchet_accumulation_killtest.jl)
# =====================================================================================
Phi_Ti(rho, q)  = (1 - q) * rho + q * (P0 * rho * P0 + P1 * rho * P1)   # z-pinch
Phi_Te(rho, q)  = (1 - q) * rho + q * (Qp * rho * Qp + Qm * rho * Qm)   # x-pinch
Ux(theta) = ComplexF64[cos(theta/2) (-im*sin(theta/2)); (-im*sin(theta/2)) cos(theta/2)]
Uz(phi)   = ComplexF64[cis(-phi/2) 0; 0 cis(phi/2)]
Phi_Fi(rho, theta) = Ux(theta) * rho * Ux(theta)'   # x-rotation (unitary)
Phi_Fe(rho, phi)   = Uz(phi)   * rho * Uz(phi)'     # z-rotation (unitary)

dissipator(L, rho) = L*rho*L' - 0.5*((L'*L)*rho + rho*(L'*L))
commutator_flow(H, rho) = -im * (H*rho - rho*H)
# VERBATIM gksl_step_evolve from the prior file. T and steps were ALREADY parameters here;
# the only new thing this file does is sweep them as the GKSL STRENGTH knob.
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
# schedule application helpers
# =====================================================================================
"Apply a word (vector of closures) left-to-right to rho."
function apply_word(word, rho)
    r = rho
    for f in word; r = f(r); end
    return r
end

"Repeat the base schedule `reps` times, then apply forward; the depth d = reps*length(base)."
build_depth_word(base, reps) = reduce(vcat, fill(base, reps))

# =====================================================================================
# ACCUMULATION / DIVERGENCE curve at a list of repetition counts.
#   At each reps the FORWARD word is the base schedule repeated; the REVERSED word is the
#   reverse of that SAME repeated word. Divergence = mean_rho ||Phi_fwd(rho)-Phi_rev(rho)||_1.
# =====================================================================================
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

# =====================================================================================
# SATURATION DEPTH (the reframe observable = lock-in depth).
#   plateau = the deepest-depth mean. saturation depth = the SMALLEST probed depth whose
#   mean has reached >= frac * plateau. Returns the depth (Int) and the index. If the curve
#   never exceeds the floor, returns (-1, -1) (no lock-in / nothing to lock).
#   We also report whether the curve is monotone-rising into the plateau vs already flat.
# =====================================================================================
function saturation_depth(depths, means, floor; frac=0.95)
    plateau = means[end]
    if plateau <= floor
        return (-1, -1, plateau, false, false)
    end
    # smallest depth reaching frac of plateau
    sat_idx = findfirst(m -> m >= frac*plateau, means)
    sat_idx = sat_idx === nothing ? length(means) : sat_idx
    sat_depth = depths[sat_idx]
    # is the curve still RISING before lock-in (later >> earlier) or already flat at depth 1?
    first_nz = findfirst(m -> m > floor, means)
    rose_before_lockin = (first_nz !== nothing) && (sat_idx > first_nz) &&
                         (means[sat_idx] > means[first_nz] * 1.02)
    above_floor = plateau > floor
    return (sat_depth, sat_idx, plateau, above_floor, rose_before_lockin)
end

# =====================================================================================
# ORDER-DEPENDENT SURVIVOR at a given GKSL strength: run several DIFFERENT orderings of the
#   channel set to a long horizon from a FIXED seed; pairwise trace-distance between the
#   survivors. Large -> order picks the survivor; ~0 -> same survivor regardless of order.
#   The GKSL strength is threaded into the Weyl channels via the closures passed in.
# =====================================================================================
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
# Z3 load-bearing verdict-flip: bind the genuine survivor spread at the WEAKEST strength to
# the commuting law "commuting_set => survivor_spread==0". For the genuine set the spread is
# nonzero at the weak strength (order still picks a survivor), so asserting commuting_set=true
# contradicts spread==measured>0 -> UNSAT. For the commuting control the spread is ~0 -> SAT.
# The verdict FLIPS on the control; this is what makes the survivor-persistence number a real
# obstruction rather than an algebraic identity of the metric.
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

# =====================================================================================
# RUN
# =====================================================================================
function run()
    rng = MersenneTwister(SEED)
    rhos = [rand_rho(rng) for _ in 1:N_RHO]
    seed_rho = rand_rho(MersenneTwister(SEED + 777))   # fixed seed for survivor test (same as prior)

    R = Dict{String,Any}()
    R["object_id"]          = "ratchet_survivor_reach_killtest"
    R["classification"]     = "ratchet_survivor_reach_killtest_poc"
    R["promotion_allowed"]  = false
    R["script"]             = "ratchet_survivor_reach_killtest.jl"
    R["seed"]               = SEED
    R["n_rho"]              = N_RHO
    R["non_numpy"]          = true
    R["bloch_free"]         = true
    R["reused_from"]        = "ratchet_accumulation_killtest.jl (genuine channels, same as order_null_killtest.jl / L7/L10/L11 _bf layers). NO new channels invented; only the GKSL (T,steps) strength is swept."
    R["carrier"]            = "density operators rho in D(C^2); genuine layer channels Ti/Te/Fi/Fe (strength-independent) + Weyl-L/R GKSL (strength = (T,steps)); HS norm, trace norm. NO CTMRG, NO PEPS, NO optimization."
    R["open_falsifier_resolved"] = "Is the depth~6 divergence saturation seen in ratchet_accumulation_killtest.jl the genuine ratchet REACHING its survivor (lock-in depth grows as GKSL weakens, survivor persists) or an ARTIFACT of strong GKSL relaxation (flat at all strengths / no survivor)?"
    R["claim_ceiling"]      = "MEASURES the forward-vs-reversed divergence-vs-depth curve, its saturation (lock-in) depth, and order-dependent survivor persistence on the genuine channel set across four GKSL relaxation strengths, vs an explicit noise floor and a commuting control. Does NOT assert layer-completion / manifold admission / coupling / bridge / flux / FEP / physics. A saturation-depth-vs-strength scaling here is a CANDIDATE order-memory lock-in diagnostic, not a proven ratchet edge."

    # ----- fixed channel parameters (genuine layer values, same as the prior kill-tests) -----
    q = 0.65; ang = 0.9
    phi0, chi0, eta0 = 2pi*0.21, 2pi*0.13, pi/4
    H0 = hopf_h0(phi0, chi0, eta0)
    rot_jump = exp(-im*1.3*(SY+0.5*SZ)/norm(SY+0.5*SZ))

    # ----- the four GKSL strengths -----
    strengths = [
        ("strong",    4.0,  400),   # the prior setting
        ("medium",    1.0,  100),
        ("weak",      0.25, 25),
        ("very_weak", 0.06, 10),
    ]

    # ----- depth ladder requested: 1,2,4,8,16,32,64 reps over the base -----
    reps_list = [1, 2, 4, 8, 16, 32, 64]

    # ----- genuine channels at a given strength (closures rho -> rho; strength threads ONLY GKSL) -----
    function het_base_at(T, steps)
        fTi = rho -> Phi_Ti(rho, q)
        fFi = rho -> Phi_Fi(rho, ang)
        fTe = rho -> Phi_Te(rho, q)
        fFe = rho -> Phi_Fe(rho, ang)
        fWL = rho -> gksl_step_evolve(rho, +H0, SM; T=T, steps=steps)   # Weyl-L
        fWR = rho -> gksl_step_evolve(rho, -H0, SP; T=T, steps=steps)   # Weyl-R
        # genuine het base schedule (same spine as the prior file): pinch + rotation + GKSL
        return [fTi, fFi, fWL, fTe, fFe, fWR], ["Ti","Fi","WeylL","Te","Fe","WeylR"]
    end

    # ----- commuting control: z-pinches ALL in the same basis at different strengths.
    #   These commute and carry NO GKSL leg, so they are identical across GKSL strengths by
    #   construction. The wrong-structure / erased control. -----
    cTi1 = rho -> Phi_Ti(rho, 0.30)
    cTi2 = rho -> Phi_Ti(rho, 0.55)
    cTi3 = rho -> Phi_Ti(rho, 0.65)
    cTi4 = rho -> Phi_Ti(rho, 0.80)
    comm_base = [cTi1, cTi2, cTi3, cTi4]
    comm_names = ["Tz.30","Tz.55","Tz.65","Tz.80"]

    # ----- permutations for the survivor test (same as the prior het file's perms) -----
    het_perms = [
        [1,2,3,4,5,6], [6,5,4,3,2,1], [3,6,1,4,2,5],
        [1,3,5,2,4,6], [4,2,6,1,5,3], [2,4,6,1,3,5],
    ]
    comm_perms = [[1,2,3,4],[4,3,2,1],[2,4,1,3],[3,1,4,2]]

    # ----- noise floor: eps * max PTM HS scale * deepest het word length (base 6, reps 64) -----
    het0, _ = het_base_at(4.0, 400)
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
    # COMMUTING CONTROL curve (strength-independent: no GKSL leg). Computed once; must be flat
    # at the floor — proves the divergence metric does not manufacture order memory.
    # ===================================================================================
    comm_depths, comm_means, comm_maxes = divergence_curve(comm_base, reps_list, rhos)
    comm_sat_depth, _, comm_plateau, comm_above_floor, _ = saturation_depth(comm_depths, comm_means, noise_floor)
    comm_flat = !comm_above_floor   # below floor at deepest depth => flat
    comm_surv, comm_surv_dists = order_dependent_survivors(comm_base, comm_perms, seed_rho)
    comm_surv_max = isempty(comm_surv_dists) ? 0.0 : maximum(comm_surv_dists)
    comm_same_survivor = comm_surv_max < max(noise_floor, 1e-9)
    R["commuting_control"] = Dict(
        "base_schedule" => join(comm_names, " "),
        "note" => "z-pinches in one basis: commute and carry no GKSL leg, so identical across all GKSL strengths by construction. MUST stay at the floor (flat curve) and pick the SAME survivor at every strength.",
        "depths" => comm_depths,
        "divergence_means" => comm_means,
        "divergence_maxes" => comm_maxes,
        "plateau" => comm_plateau,
        "above_floor" => comm_above_floor,
        "flat_at_floor" => comm_flat,
        "saturation_depth" => comm_sat_depth,
        "survivor_spread_max" => comm_surv_max,
        "same_survivor" => comm_same_survivor,
    )

    # ===================================================================================
    # THE DECISIVE SWEEP: genuine het curve + saturation depth + survivor persistence at each
    # of the four GKSL strengths.
    # ===================================================================================
    per_strength = Vector{Dict{String,Any}}()
    sat_depths_by_strength = Dict{String,Int}()
    plateau_by_strength = Dict{String,Float64}()
    survivor_max_by_strength = Dict{String,Float64}()
    survivor_persists_by_strength = Dict{String,Bool}()
    above_floor_by_strength = Dict{String,Bool}()
    rose_by_strength = Dict{String,Bool}()

    for (label, T, steps) in strengths
        het_base, het_names = het_base_at(T, steps)
        depths, means, maxes = divergence_curve(het_base, reps_list, rhos)
        sat_depth, sat_idx, plateau, above_floor, rose = saturation_depth(depths, means, noise_floor)
        surv, surv_dists = order_dependent_survivors(het_base, het_perms, seed_rho)
        surv_max  = isempty(surv_dists) ? 0.0 : maximum(surv_dists)
        surv_mean = isempty(surv_dists) ? 0.0 : mean(surv_dists)
        survivor_persists = surv_max > noise_floor

        sat_depths_by_strength[label]        = sat_depth
        plateau_by_strength[label]           = plateau
        survivor_max_by_strength[label]      = surv_max
        survivor_persists_by_strength[label] = survivor_persists
        above_floor_by_strength[label]       = above_floor
        rose_by_strength[label]              = rose

        push!(per_strength, Dict(
            "strength_label" => label,
            "gksl_T" => T,
            "gksl_steps" => steps,
            "base_schedule" => join(het_names, " "),
            "depths" => depths,
            "divergence_means" => means,
            "divergence_maxes" => maxes,
            "plateau" => plateau,
            "above_floor" => above_floor,
            "rose_before_lockin" => rose,
            "saturation_depth_lockin" => sat_depth,
            "saturation_idx" => sat_idx,
            "survivor_spread_mean" => surv_mean,
            "survivor_spread_max" => surv_max,
            "survivor_persists" => survivor_persists,
            "note" => "saturation_depth = smallest probed depth reaching >=95% of the plateau (lock-in depth). survivor_persists = pairwise survivor trace-distance (max over 6 orderings) above floor.",
        ))
    end
    R["sweep"] = per_strength

    # ===================================================================================
    # REFRAME: saturation (lock-in) depth as the ratchet observable, ordered strong->very_weak.
    # ===================================================================================
    order_labels = [s[1] for s in strengths]   # strong, medium, weak, very_weak
    sat_depth_series = [sat_depths_by_strength[l] for l in order_labels]
    plateau_series   = [plateau_by_strength[l] for l in order_labels]
    survivor_series  = [survivor_max_by_strength[l] for l in order_labels]
    # does the lock-in depth INCREASE as strength weakens? compare consecutive (only over
    # strengths whose plateau is above floor; a -1 lock-in depth means nothing locked in).
    valid = [above_floor_by_strength[l] for l in order_labels]
    lockin_grows = false
    lockin_nondecreasing = true
    last_valid = -1
    grew_any = false
    for (k, l) in enumerate(order_labels)
        if valid[k]
            d = sat_depths_by_strength[l]
            if last_valid >= 0
                if d < last_valid; lockin_nondecreasing = false; end
                if d > last_valid; grew_any = true; end
            end
            last_valid = d
        end
    end
    lockin_grows = lockin_nondecreasing && grew_any
    R["reframe_lockin_depth_vs_strength"] = Dict(
        "order" => order_labels,
        "saturation_depth_series" => sat_depth_series,
        "plateau_series" => plateau_series,
        "survivor_spread_max_series" => survivor_series,
        "all_strengths_above_floor" => all(valid),
        "lockin_depth_nondecreasing_as_strength_weakens" => lockin_nondecreasing,
        "lockin_depth_grew_somewhere" => grew_any,
        "lockin_depth_grows_as_strength_weakens" => lockin_grows,
        "note" => "saturation_depth_series ordered strong->medium->weak->very_weak. GENUINE ratchet-to-survivor predicts this series is nondecreasing AND grows somewhere (gentler step => more depth to lock in). -1 entries mean no lock-in (plateau below floor) at that strength.",
    )

    # ===================================================================================
    # Z3 load-bearing verdict-flip on survivor persistence at the WEAKEST strength.
    # ===================================================================================
    weak_label = "very_weak"
    weak_spread = survivor_max_by_strength[weak_label]
    z3_genuine_weak = z3_survivor_obstruction(weak_spread)         # nonzero -> unsat
    z3_commuting    = z3_survivor_obstruction(comm_surv_max)       # ~0 -> sat
    z3_load_bearing = (z3_genuine_weak == "unsat") && (z3_commuting == "sat") &&
                      (weak_spread > noise_floor) && (comm_surv_max < max(noise_floor, 1e-9))
    R["z3_load_bearing"] = Dict(
        "encoding" => "FREE int spread, FREE bool commuting_set; law Or([Not(commuting_set), spread==0]); assert commuting_set=true + spread==IntVal(measured). genuine(weakest strength): unsat; commuting: sat.",
        "genuine_weak_survivor_spread" => weak_spread,
        "genuine_weak_verdict" => z3_genuine_weak,
        "commuting_survivor_spread" => comm_surv_max,
        "commuting_verdict" => z3_commuting,
        "load_bearing_flip" => z3_load_bearing,
    )

    # ===================================================================================
    # DECISIVE VERDICT
    #   ratchet_reaches_survivor : (1) every strength's curve is above floor and saturates to
    #       a plateau; (2) the lock-in depth is nondecreasing as strength weakens AND grows
    #       somewhere (gentler step => more depth before lock-in); (3) the order-dependent
    #       survivor persists at EVERY strength; (4) commuting control flat + same survivor.
    #   saturation_was_artifact : weakening GKSL drives the divergence below the floor at some
    #       strength (no order effect to accumulate) OR the survivor stops persisting (no
    #       survivor) at some strength.
    #   mixed : signals partially hold (e.g. survivor persists everywhere but lock-in depth
    #       does not grow, or it grows but a strength dips below floor).
    # ===================================================================================
    all_above_floor   = all(valid)
    survivor_everywhere = all(survivor_persists_by_strength[l] for l in order_labels)
    controls_clean    = comm_flat && comm_same_survivor

    artifact = (!all_above_floor) || (!survivor_everywhere)
    genuine  = all_above_floor && survivor_everywhere && lockin_grows && controls_clean

    classification = if !controls_clean
        "INCONCLUSIVE_control_not_flat"
    elseif genuine
        "ratchet_reaches_survivor"
    elseif artifact
        "saturation_was_artifact"
    else
        "mixed"
    end

    R["verdict"] = Dict(
        "classification" => classification,
        "all_strengths_above_floor" => all_above_floor,
        "survivor_persists_at_every_strength" => survivor_everywhere,
        "lockin_depth_grows_as_strength_weakens" => lockin_grows,
        "controls_clean" => controls_clean,
        "control_flat_at_floor" => comm_flat,
        "control_same_survivor" => comm_same_survivor,
        "z3_load_bearing_flip" => z3_load_bearing,
        "saturation_depth_series_strong_to_veryweak" => sat_depth_series,
        "survivor_spread_max_series_strong_to_veryweak" => survivor_series,
        "interpretation" => "ratchet_reaches_survivor requires: every GKSL strength above floor and saturating, lock-in depth nondecreasing AND growing as strength weakens, the order-dependent survivor persisting at every strength, and the commuting control flat with the same survivor. saturation_was_artifact if weakening GKSL drives divergence below the floor or kills the survivor at any strength. mixed if signals partially hold. This settles whether the depth~6 saturation in ratchet_accumulation_killtest.jl is genuine survivor lock-in (ratchet drive-down) or an artifact of strong relaxation.",
    )

    # F01 / N01 witnesses
    R["F01_witness"] = Dict(
        "finite_carrier" => "density operators in D(C^2); finite genuine channel set (6 het + 4 commuting control)",
        "finite_probe" => "$(N_RHO) random density operators + 1 fixed survivor seed; 4 GKSL strengths; depth ladder 6,12,24,48,96,192,384 (reps 1..64)",
        "finite_operator" => "Ti/Te/Fi/Fe (strength-independent) + Weyl-L/R GKSL with tunable (T,steps); genuine layer maps reused from ratchet_accumulation_killtest",
        "finite_path" => "forward vs reversed depth words at each GKSL strength; permutation survivors at each strength",
    )
    R["N01_witness"] = Dict(
        "divergence_formula" => "Delta(d) = mean_rho ||Phi_fwd^d(rho) - Phi_rev^d(rho)||_1 vs depth d, per GKSL strength",
        "saturation_depth_lockin_series_strong_to_veryweak" => sat_depth_series,
        "survivor_spread_max_series_strong_to_veryweak" => survivor_series,
        "present_above_floor" => all_above_floor,
        "noise_floor" => noise_floor,
    )

    R["tool_manifest"] = Dict(
        "LinearAlgebra" => "load_bearing: svdvals (trace norm), HS norms, channel/PTM algebra; every measured number flows through it.",
        "Statistics" => "supportive: means over the rho ensemble and over orderings.",
        "Random" => "load_bearing: random density operators (signatures measured over fresh samples, not planted).",
        "Z3" => "load_bearing: binds the genuine survivor spread at the weakest strength to the commuting law; verdict flips UNSAT->SAT on the commuting control.",
        "JSON" => "supportive: receipt emission.",
    )
    R["tool_integration_depth"] = Dict("LinearAlgebra"=>"load_bearing","Z3"=>"load_bearing","Random"=>"load_bearing","Statistics"=>"supportive","JSON"=>"supportive")
    R["blocked_consumers"] = ["any ratchet edge admission","ratchet thesis closure","pairwise nesting","coupling","bridge/Xi/Phi0/Axis0","flux/FEP/physics"]
    R["status_ladder"] = "exists < runs < passes local rerun"

    open(RESULT_PATH, "w") do io
        JSON.print(io, R, 2); write(io, "\n")
    end

    # ---- console summary ----
    println("="^96)
    println("RATCHET SURVIVOR-REACH KILL-TEST  (object_id=ratchet_survivor_reach_killtest, promotion_allowed=false)")
    println("="^96)
    println("noise_floor = ", noise_floor, "   (eps * PTM-scale $(round(op_scale,digits=3)) * deepest_len $(deepest_word_len) * 8)")
    println("-"^96)
    println("DECISIVE SWEEP  forward-vs-reversed divergence vs depth, per GKSL strength")
    println("  depths (reps 1..64 over base len 6): ", comm_depths)
    for ps in per_strength
        println("  [", rpad(ps["strength_label"],10), " T=", ps["gksl_T"], " steps=", ps["gksl_steps"], "]")
        println("     Delta_mean = ", round.(ps["divergence_means"], sigdigits=5))
        println("     plateau=", round(ps["plateau"], sigdigits=5),
                "  lock-in depth=", ps["saturation_depth_lockin"],
                "  rose_before_lockin=", ps["rose_before_lockin"],
                "  survivor_max=", round(ps["survivor_spread_max"], sigdigits=5),
                "  survivor_persists=", ps["survivor_persists"])
    end
    println("-"^96)
    println("COMMUTING control (", join(comm_names," "), ") [strength-independent]:")
    println("     Delta_mean = ", round.(comm_means, sigdigits=5))
    println("     flat_at_floor=", comm_flat, "  survivor_max=", round(comm_surv_max, sigdigits=5),
            "  same_survivor=", comm_same_survivor)
    println("-"^96)
    println("REFRAME  lock-in depth vs strength (strong->medium->weak->very_weak): ", sat_depth_series)
    println("     plateau series:        ", round.(plateau_series, sigdigits=5))
    println("     survivor_max series:   ", round.(survivor_series, sigdigits=5))
    println("     lock-in depth grows as strength weakens = ", lockin_grows,
            "  (nondecreasing=", lockin_nondecreasing, " grew_somewhere=", grew_any, ")")
    println("-"^96)
    println("Z3 load-bearing: genuine(weakest)=", z3_genuine_weak, " commuting=", z3_commuting, " flip=", z3_load_bearing)
    println("-"^96)
    println("all_strengths_above_floor=", all_above_floor,
            "  survivor_persists_everywhere=", survivor_everywhere,
            "  controls_clean=", controls_clean)
    println("DECISIVE VERDICT: ", classification)
    println("Wrote: ", RESULT_PATH)
    return R
end

run()
