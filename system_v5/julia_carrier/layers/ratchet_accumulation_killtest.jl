#!/usr/bin/env julia
# =====================================================================================
# ratchet_accumulation_killtest.jl  —  THE SUFFICIENT-CONDITION RATCHET KILL-TEST
#   classification = ratchet_accumulation_killtest_poc ; promotion_allowed = false.
#   density-operator only. NO CTMRG, NO PEPS, NO optimization. Pure 2x2 channel algebra.
# -------------------------------------------------------------------------------------
# OBJECT_ID: ratchet_accumulation_killtest
# CLAIM CEILING: this object MEASURES, over the GENUINE heterogeneous layer-channel set
#   reused verbatim from order_null_killtest.jl / the _bf layers, three ratchet
#   signatures against an explicit noise floor and a commuting control:
#     (1) ACCUMULATION   — forward-vs-reversed trace-distance as a function of depth d.
#     (2) IRREVERSIBILITY — can the reversed-order schedule recover the initial state.
#     (3) ORDER-DEPENDENT SURVIVOR — do different orderings reach different fixed states.
#   It does NOT assert layer-completion, manifold admission, coupling, bridge
#   (rho_AB/Xi/Phi0/Axis0), flux, FEP, or physics. A channel stack that shows a ratchet
#   signature here is a CANDIDATE order-memory interface, not a proven ratchet edge or a
#   proven primary-object ratchet. promotion_allowed = false.
#
# -------------------------------------------------------------------------------------
# WHY THIS IS A SEPARATE TEST FROM order_null_killtest.jl (the NECESSARY-vs-SUFFICIENT gap):
#   order_null_killtest.jl ESTABLISHED the NECESSARY condition: for the genuine channel
#   set the per-pair RUN ORDER genuinely changes the output (24/28 pairs order_sensitivity_
#   real, het-word reversed-vs-forward gap 0.354, 0 order_null pairs). That is per-pair
#   noncommutation. It does NOT establish the SUFFICIENT RATCHET condition. A set of
#   channels can be pairwise-noncommuting and yet:
#     - the forward-vs-reversed divergence can SATURATE (bounded) with depth instead of
#       ACCUMULATING — no growing order memory;
#     - the reversed order can still RECOVER the initial state (the order effect is a
#       reversible reshuffling, not an irreversible drive);
#     - all orderings can relax to the SAME fixed point (the channels share an attractor,
#       so order does not pick the survivor).
#   A genuine RATCHET requires at least one of: monotone accumulation, irreversibility,
#   or an order-dependent survivor, ABOVE the floor, WITH the commuting control flat.
#   This file tests each on the same genuine channels and classifies brutally.
#
# GENUINE CHANNELS (reused VERBATIM from order_null_killtest.jl, which read them from the
#   verified _bf layers; NOT invented here):
#   L11_layer_bf.jl  Ti/Te/Fi/Fe:
#     Phi_Ti(rho,q) = (1-q)rho + q(P0 rho P0 + P1 rho P1)     z-pinch (dephasing)
#     Phi_Te(rho,q) = (1-q)rho + q(Qp rho Qp + Qm rho Qm)     x-pinch (dephasing)
#     Phi_Fi(rho,th)= Ux(th) rho Ux(th)'                       x-rotation (unitary)
#     Phi_Fe(rho,ph)= Uz(ph) rho Uz(ph)'                       z-rotation (unitary)
#   L7_layer_bf.jl / L10_layer_bf.jl Weyl GKSL (H_L=+H0/H_R=-H0, sigma_-/sigma_+ jumps):
#     gksl_step_evolve : rho -> finite-time Euler+Hermitize+renorm CPTP map
#       Weyl-L: H=+H0, jump sigma_-  ;  Weyl-R: H=-H0, jump sigma_+
#   L10_layer_bf.jl terrain Ni R-sheet channel + its rotated-jump partner (file N01 pair).
#
# CONTROLS (load-bearing — the signal must come from genuine noncommutation, not the metric):
#   (a) COMMUTING control: a channel set that all dephase in the SAME basis (z-pinch at
#       several strengths). These channels commute. The control MUST show NO accumulation
#       (flat depth curve), recoverable (irreversibility residual at floor), and the SAME
#       survivor for every ordering. If a "ratchet signature" survives this control, the
#       metric is manufacturing it. This is the wrong-structure / erased control.
#   (b) EXPLICIT noise floor: machine-eps * PTM HS channel scale * depth, NOT a literal.
#   (c) Z3 verdict-flip: bind the measured forward-vs-reversed accumulation slope to the
#       commuting law "commuting_set => slope==0"; genuine set UNSAT, commuting set SAT.
# =====================================================================================

using LinearAlgebra
using Random
using Statistics
import JSON
import Z3

const RESULT_PATH = joinpath(@__DIR__, "ratchet_accumulation_killtest_results.json")
const SEED = 20260602
const N_RHO = 20            # random initial density operators (matches order_null_killtest)

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
# GENUINE CHANNELS (quoted VERBATIM from order_null_killtest.jl)
# =====================================================================================
Phi_Ti(rho, q)  = (1 - q) * rho + q * (P0 * rho * P0 + P1 * rho * P1)   # z-pinch
Phi_Te(rho, q)  = (1 - q) * rho + q * (Qp * rho * Qp + Qm * rho * Qm)   # x-pinch
Ux(theta) = ComplexF64[cos(theta/2) (-im*sin(theta/2)); (-im*sin(theta/2)) cos(theta/2)]
Uz(phi)   = ComplexF64[cis(-phi/2) 0; 0 cis(phi/2)]
Phi_Fi(rho, theta) = Ux(theta) * rho * Ux(theta)'   # x-rotation (unitary)
Phi_Fe(rho, phi)   = Uz(phi)   * rho * Uz(phi)'     # z-rotation (unitary)

dissipator(L, rho) = L*rho*L' - 0.5*((L'*L)*rho + rho*(L'*L))
commutator_flow(H, rho) = -im * (H*rho - rho*H)
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

# ---------- PTM (for the noise-floor channel scale only; same as order_null_killtest) ----------
const PAULI4 = (I2, SX, SY, SZ)
function ptm(chan)
    T = zeros(Float64, 4, 4)
    for j in 1:4, i in 1:4
        T[i, j] = real(tr(PAULI4[i] * chan(PAULI4[j])) / 2)
    end
    return T
end

# ---------- random density operators (Bloch-free; same construction as order_null_killtest) ----------
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
# (1) ACCUMULATION: forward-vs-reversed trace-distance as a function of depth.
#   At each depth d the FORWARD word is the base schedule repeated; the REVERSED word is
#   the reverse of that SAME repeated word. Divergence = mean_rho ||Phi_fwd(rho)-Phi_rev(rho)||_1.
#   GROWS monotonically -> accumulating order memory. SATURATES/bounded -> no accumulation.
# =====================================================================================
function accumulation_curve(base, depths_reps, rhos)
    curve = Vector{Dict{String,Any}}()
    means = Float64[]
    for reps in depths_reps
        fwd_word = build_depth_word(base, reps)
        rev_word = reverse(fwd_word)
        diffs = Float64[]
        for rho in rhos
            f = apply_word(fwd_word, rho)
            r = apply_word(rev_word, rho)
            push!(diffs, trace_norm(f - r))
        end
        m = mean(diffs); push!(means, m)
        push!(curve, Dict(
            "depth" => reps*length(base),
            "reps" => reps,
            "fwd_rev_tracedist_mean" => m,
            "fwd_rev_tracedist_max" => maximum(diffs),
        ))
    end
    return curve, means
end

# =====================================================================================
# (2) IRREVERSIBILITY (order-discriminating form).
#   The task's literal "recover the initial state" reads ||Phi_reversed(Phi_forward(rho))
#   - rho||_1. By itself that quantity does NOT separate a ratchet from a commuting set:
#   even for COMMUTING channels Phi_reversed == Phi_forward (same composite), so
#   Phi_reversed(Phi_forward(rho)) = Phi_forward(Phi_forward(rho)) which is generally NOT
#   rho (the pinches relax the state). So "non-recoverable" is true even for commuting
#   channels — the raw residual is dominated by the channels' own relaxation, not by order.
#   The order-discriminating quantity is whether REVERSING the order on the second leg
#   changes the result vs NOT reversing it:
#        order_residual = mean_rho ||Phi_reversed(Phi_forward(rho)) - Phi_forward(Phi_forward(rho))||_1
#   This is EXACTLY 0 for a commuting set (reversed==forward) and nonzero only when the
#   reversed leg lands somewhere a second forward leg would not — i.e. order is
#   irreversibly written into the state. We report BOTH the raw "recover rho" residual
#   (the task's literal number) AND this order-discriminating residual.
# =====================================================================================
function irreversibility_residual(base, rhos)
    fwd_word = base
    rev_word = reverse(base)
    raw = Float64[]          # task-literal: ||Phi_rev(Phi_fwd(rho)) - rho||_1
    order_disc = Float64[]   # discriminating: ||Phi_rev(Phi_fwd(rho)) - Phi_fwd(Phi_fwd(rho))||_1
    for rho in rhos
        driven   = apply_word(fwd_word, rho)
        back_rev = apply_word(rev_word, driven)
        back_fwd = apply_word(fwd_word, driven)
        push!(raw, trace_norm(back_rev - rho))
        push!(order_disc, trace_norm(back_rev - back_fwd))
    end
    return mean(raw), maximum(raw), mean(order_disc), maximum(order_disc)
end

# =====================================================================================
# (3) ORDER-DEPENDENT SURVIVOR: run several DIFFERENT orderings (permutations) of the
#   channel set, each repeated to a long horizon (deep), to their long-time state from a
#   FIXED seed. Pairwise trace-distance between the survivors of different orderings:
#   large -> order picks the survivor (ratchet basin); ~0 -> same survivor regardless of
#   order (no ratchet). We use a fixed seed so the survivor depends only on the order.
# =====================================================================================
function order_dependent_survivors(channel_set, perms, seed_rho; horizon_reps=40)
    survivors = Matrix{ComplexF64}[]
    for perm in perms
        base = [channel_set[i] for i in perm]
        word = build_depth_word(base, horizon_reps)
        push!(survivors, apply_word(word, seed_rho))
    end
    # pairwise trace-distance between survivors of different orderings
    np = length(perms)
    dists = Float64[]
    pairs = Tuple{Int,Int}[]
    for a in 1:np, b in a+1:np
        push!(dists, trace_norm(survivors[a] - survivors[b]))
        push!(pairs, (a, b))
    end
    return survivors, dists, pairs
end

# =====================================================================================
# monotonicity test on a depth curve: strictly nondecreasing within tol, and a real GROW
# (last >> first) vs SATURATE (curve flat after rising). Reports both.
# =====================================================================================
function classify_curve(means, floor)
    n = length(means)
    above = means[end] > floor
    # monotone-nondecreasing (within a small slack of the floor for rounding)
    monotone = all(means[k+1] >= means[k] - max(floor, 1e-12) for k in 1:n-1)
    # growth ratio last vs first nonzero
    first_nz = findfirst(x -> x > floor, means)
    growth_ratio = (first_nz === nothing) ? 0.0 : means[end] / means[first_nz]
    # saturation: is the second half nearly flat (range / max < 5%)?
    half = max(1, div(n, 2))
    tail = means[half:end]
    tail_range = maximum(tail) - minimum(tail)
    tail_rel = maximum(tail) > floor ? tail_range / maximum(tail) : 0.0
    saturates = above && tail_rel < 0.05 && !(growth_ratio > 1.10)
    accumulates = above && monotone && growth_ratio > 1.10
    return (above=above, monotone=monotone, growth_ratio=growth_ratio,
            tail_rel=tail_rel, saturates=saturates, accumulates=accumulates)
end

# =====================================================================================
# Z3 load-bearing: bind the measured accumulation growth (scaled int) to the commuting
# law "commuting_set => growth==0" (no accumulation for a commuting set). For the genuine
# set the growth is nonzero, so asserting commuting_set=true contradicts growth==measured>0
# -> UNSAT. For the commuting control the growth is ~0 -> SAT. Verdict FLIPS on the control.
# =====================================================================================
function z3_accumulation_obstruction(measured_growth::Float64; scale=1_000_000_000)
    ctx = Z3.Context(); s = Z3.Solver(ctx)
    growth   = Z3.IntVar("growth", ctx)
    commuting = Z3.BoolVar("commuting_set", ctx)
    Z3.add(s, Z3.Or([Z3.Not(commuting), growth == Z3.IntVal(0, ctx)]))   # commuting => growth==0
    Z3.add(s, commuting == Z3.BoolVal(true, ctx))
    m = round(Int, scale * abs(measured_growth))
    Z3.add(s, growth == Z3.IntVal(m, ctx))
    return string(Z3.check(s))   # genuine(nonzero): unsat ; commuting(zero): sat
end

# =====================================================================================
# RUN
# =====================================================================================
function run()
    rng = MersenneTwister(SEED)
    rhos = [rand_rho(rng) for _ in 1:N_RHO]
    seed_rho = rand_rho(MersenneTwister(SEED + 777))   # fixed seed for survivor test

    R = Dict{String,Any}()
    R["object_id"]          = "ratchet_accumulation_killtest"
    R["classification"]     = "ratchet_accumulation_killtest_poc"
    R["promotion_allowed"]  = false
    R["script"]             = "ratchet_accumulation_killtest.jl"
    R["seed"]               = SEED
    R["n_rho"]              = N_RHO
    R["non_numpy"]          = true
    R["bloch_free"]         = true
    R["reused_from"]        = "order_null_killtest.jl (genuine channels read from L7/L10/L11 _bf layers); NO new channels invented."
    R["carrier"]            = "density operators rho in D(C^2); genuine layer channels Ti/Te/Fi/Fe + Weyl-L/R GKSL + Ni-terrain GKSL; HS norm, trace norm. NO CTMRG, NO PEPS, NO optimization."
    R["claim_ceiling"]      = "MEASURES three ratchet signatures (accumulation-vs-depth, irreversibility residual, order-dependent survivor trace-distances) on the genuine channel set vs an explicit noise floor and a commuting control. Does NOT assert layer-completion / manifold admission / coupling / bridge / flux / FEP / physics. A ratchet signature here is a CANDIDATE order-memory interface, not a proven ratchet edge."

    # ----- fixed channel parameters (genuine layer values, same as order_null_killtest) -----
    q = 0.65; ang = 0.9
    phi0, chi0, eta0 = 2pi*0.21, 2pi*0.13, pi/4
    H0 = hopf_h0(phi0, chi0, eta0)

    # ----- genuine channels as closures rho -> rho (verbatim from order_null_killtest) -----
    fTi = rho -> Phi_Ti(rho, q)
    fTe = rho -> Phi_Te(rho, q)
    fFi = rho -> Phi_Fi(rho, ang)
    fFe = rho -> Phi_Fe(rho, ang)
    fWL = rho -> gksl_step_evolve(rho, +H0, SM)
    fWR = rho -> gksl_step_evolve(rho, -H0, SP)
    rot_jump = exp(-im*1.3*(SY+0.5*SZ)/norm(SY+0.5*SZ))
    fTerr  = rho -> gksl_step_evolve(rho, -H0, SP; gamma=1.0, eps=1.0)
    fTerrR = rho -> gksl_step_evolve(rho, -H0, rot_jump*SP*rot_jump'; gamma=1.0, eps=1.0)

    # The GENUINE heterogeneous base schedule: pinch + rotation + GKSL (the het word from
    # order_null_killtest, whose reversed-vs-forward gap was 0.354). This is the spine.
    het_base = [fTi, fFi, fWL, fTe, fFe, fWR]
    het_names = ["Ti", "Fi", "WeylL", "Te", "Fe", "WeylR"]

    # The COMMUTING control: dephasings ALL in the SAME (z) basis at different strengths.
    # z-pinches commute with each other; this is the wrong-structure / erased control.
    cTi1 = rho -> Phi_Ti(rho, 0.30)
    cTi2 = rho -> Phi_Ti(rho, 0.55)
    cTi3 = rho -> Phi_Ti(rho, 0.65)
    cTi4 = rho -> Phi_Ti(rho, 0.80)
    comm_base = [cTi1, cTi2, cTi3, cTi4]
    comm_names = ["Tz.30", "Tz.55", "Tz.65", "Tz.80"]

    # ===================================================================================
    # noise floor: eps * max PTM HS scale * the deepest depth probed. Explicit, not literal.
    # ===================================================================================
    all_ch = [fTi, fFi, fWL, fTe, fFe, fWR, cTi1, cTi2, cTi3, cTi4]
    op_scale = maximum(norm(ptm(f)) for f in all_ch)
    depths_reps = [1, 2, 4, 8, 16]    # base length 6 (het) / 4 (comm); depth d = reps*len
    max_depth_word_len = maximum(depths_reps) * 6
    noise_floor = eps(Float64) * op_scale * max_depth_word_len * 8.0
    R["noise_floor"] = Dict(
        "value" => noise_floor,
        "definition" => "eps(Float64) * max PTM HS scale (=$(round(op_scale,digits=4))) * deepest word length ($(max_depth_word_len)) * 8 safety",
        "machine_eps" => eps(Float64),
        "max_ptm_hs_scale" => op_scale,
        "deepest_word_length" => max_depth_word_len,
    )

    # ===================================================================================
    # (1) ACCUMULATION — depth curve (d = 2,4,8,16,32 over base length, requested ladder)
    #   het base len 6: reps 1,2,4,8,16 -> word lengths 6,12,24,48,96; the REQUESTED depth
    #   ladder d=2,4,8,16,32 is realized on a length-2 het sub-base too, reported separately.
    # ===================================================================================
    het_curve, het_means = accumulation_curve(het_base, depths_reps, rhos)
    comm_curve, comm_means = accumulation_curve(comm_base, depths_reps, rhos)

    # Also the EXACT requested d = 2,4,8,16,32 ladder on a minimal het 2-channel sub-base
    # (Ti, WeylR) so the depth axis is literally 2,4,8,16,32 single-channel applications.
    sub_base = [fTi, fWR]
    sub_reps = [1, 2, 4, 8, 16]   # depth d = 2,4,8,16,32 (base length 2)
    sub_curve, sub_means = accumulation_curve(sub_base, sub_reps, rhos)
    comm_sub_base = [cTi1, cTi2]   # two commuting z-pinches
    comm_sub_curve, comm_sub_means = accumulation_curve(comm_sub_base, sub_reps, rhos)

    het_class = classify_curve(het_means, noise_floor)
    comm_class = classify_curve(comm_means, noise_floor)
    sub_class = classify_curve(sub_means, noise_floor)
    comm_sub_class = classify_curve(comm_sub_means, noise_floor)

    R["accumulation"] = Dict(
        "genuine_heterogeneous" => Dict(
            "base_schedule" => join(het_names, " "),
            "curve" => het_curve,
            "means" => het_means,
            "above_floor" => het_class.above,
            "monotone_nondecreasing" => het_class.monotone,
            "growth_ratio_last_over_first" => het_class.growth_ratio,
            "tail_relative_range" => het_class.tail_rel,
            "saturates" => het_class.saturates,
            "accumulates" => het_class.accumulates,
        ),
        "commuting_control" => Dict(
            "base_schedule" => join(comm_names, " "),
            "curve" => comm_curve,
            "means" => comm_means,
            "above_floor" => comm_class.above,
            "accumulates" => comm_class.accumulates,
            "note" => "MUST be flat at the floor (z-pinches commute) — proves accumulation is from genuine noncommutation.",
        ),
        "requested_depth_ladder_2_4_8_16_32" => Dict(
            "genuine_sub_base" => "Ti WeylR (len2; depth d = reps*2 = 2,4,8,16,32)",
            "depths" => [r*2 for r in sub_reps],
            "curve" => sub_curve,
            "means" => sub_means,
            "accumulates" => sub_class.accumulates,
            "saturates" => sub_class.saturates,
            "growth_ratio" => sub_class.growth_ratio,
            "commuting_sub_base" => "Tz.30 Tz.55 (len2; same depth ladder)",
            "commuting_means" => comm_sub_means,
            "commuting_accumulates" => comm_sub_class.accumulates,
        ),
    )

    # ===================================================================================
    # (2) IRREVERSIBILITY (order-discriminating)
    # ===================================================================================
    het_raw_mean, het_raw_max, het_ord_mean, het_ord_max = irreversibility_residual(het_base, rhos)
    comm_raw_mean, comm_raw_max, comm_ord_mean, comm_ord_max = irreversibility_residual(comm_base, rhos)
    # The order-discriminating residual is the load-bearing one: it MUST be ~0 for the
    # commuting control (reversed==forward) and nonzero only when reversing the order
    # genuinely writes a different state. The raw "recover rho" residual is reported as the
    # task's literal number but is NOT used for the verdict because it is dominated by the
    # channels' own relaxation (nonzero even for commuting channels).
    het_irreversible = het_ord_mean > noise_floor
    comm_recoverable = comm_ord_max < max(noise_floor, 1e-9)   # order leg leaves NO residue
    R["irreversibility"] = Dict(
        "genuine_heterogeneous" => Dict(
            "word" => join(het_names, " "),
            "raw_recover_rho_residual_mean" => het_raw_mean,
            "raw_recover_rho_residual_max" => het_raw_max,
            "order_discriminating_residual_mean" => het_ord_mean,
            "order_discriminating_residual_max" => het_ord_max,
            "irreversible" => het_irreversible,
            "note" => "order_discriminating = ||Phi_rev(Phi_fwd(rho)) - Phi_fwd(Phi_fwd(rho))||_1; nonzero => reversing the order on the second leg lands somewhere a forward leg would not (order written into state). raw_recover = the task's literal ||Phi_rev(Phi_fwd(rho)) - rho||_1 (relaxation-dominated, not used for verdict).",
        ),
        "commuting_control" => Dict(
            "word" => join(comm_names, " "),
            "raw_recover_rho_residual_mean" => comm_raw_mean,
            "order_discriminating_residual_mean" => comm_ord_mean,
            "order_discriminating_residual_max" => comm_ord_max,
            "recoverable" => comm_recoverable,
            "note" => "commuting z-pinches: reversed order == forward order as a composite, so the order-discriminating residual is EXACTLY 0 — the null. (The raw recover-rho residual is nonzero here too, which is why the raw number cannot be the discriminator.)",
        ),
    )

    # ===================================================================================
    # (3) ORDER-DEPENDENT SURVIVOR — several different permutations of the genuine channel
    #   set to a long horizon from a fixed seed; pairwise trace-distance of the survivors.
    # ===================================================================================
    het_perms = [
        [1,2,3,4,5,6],   # Ti Fi WeylL Te Fe WeylR
        [6,5,4,3,2,1],   # reversed
        [3,6,1,4,2,5],   # GKSL-first-ish interleave
        [1,3,5,2,4,6],   # odd-even split
        [4,2,6,1,5,3],   # another scramble
        [2,4,6,1,3,5],   # rotations early
    ]
    het_surv, het_surv_dists, het_surv_pairs = order_dependent_survivors(het_base, het_perms, seed_rho)
    comm_perms = [
        [1,2,3,4],
        [4,3,2,1],
        [2,4,1,3],
        [3,1,4,2],
    ]
    comm_surv, comm_surv_dists, comm_surv_pairs = order_dependent_survivors(comm_base, comm_perms, seed_rho)

    het_surv_max = isempty(het_surv_dists) ? 0.0 : maximum(het_surv_dists)
    het_surv_mean = isempty(het_surv_dists) ? 0.0 : mean(het_surv_dists)
    comm_surv_max = isempty(comm_surv_dists) ? 0.0 : maximum(comm_surv_dists)
    order_picks_survivor = het_surv_max > noise_floor
    comm_same_survivor = comm_surv_max < max(noise_floor, 1e-9)
    R["order_dependent_survivor"] = Dict(
        "genuine_heterogeneous" => Dict(
            "n_orderings" => length(het_perms),
            "horizon_reps" => 40,
            "pairwise_survivor_tracedist_mean" => het_surv_mean,
            "pairwise_survivor_tracedist_max" => het_surv_max,
            "pairwise_survivor_tracedist_all" => het_surv_dists,
            "order_picks_survivor" => order_picks_survivor,
            "note" => "different orderings of the genuine channels to a long-time state from one fixed seed; large pairwise trace-distance => the order selects which survivor is admitted (ratchet basin).",
        ),
        "commuting_control" => Dict(
            "n_orderings" => length(comm_perms),
            "pairwise_survivor_tracedist_max" => comm_surv_max,
            "pairwise_survivor_tracedist_all" => comm_surv_dists,
            "same_survivor" => comm_same_survivor,
            "note" => "commuting z-pinches: every ordering composes to the same map, so every survivor is identical — the null.",
        ),
    )

    # ===================================================================================
    # Z3 load-bearing verdict-flip: the accumulation growth is real, not an algebraic
    # identity. Bind genuine het growth (unsat under commuting law) vs commuting growth (sat).
    # ===================================================================================
    het_growth = max(0.0, het_means[end] - het_means[1])    # absolute accumulation over depth
    comm_growth = max(0.0, comm_means[end] - comm_means[1])
    z3_genuine = z3_accumulation_obstruction(het_growth)    # nonzero -> unsat
    z3_commuting = z3_accumulation_obstruction(comm_growth) # ~0 -> sat
    z3_load_bearing = (z3_genuine == "unsat") && (z3_commuting == "sat") &&
                      (het_growth > noise_floor) && (comm_growth < max(noise_floor, 1e-9))
    R["z3_load_bearing"] = Dict(
        "encoding" => "FREE int growth, FREE bool commuting_set; law Or([Not(commuting_set), growth==0]); assert commuting_set=true + growth==IntVal(measured). genuine: unsat; commuting: sat.",
        "genuine_accumulation_growth" => het_growth,
        "genuine_verdict" => z3_genuine,
        "commuting_accumulation_growth" => comm_growth,
        "commuting_verdict" => z3_commuting,
        "load_bearing_flip" => z3_load_bearing,
    )

    # ===================================================================================
    # DECISIVE VERDICT
    #   ratchet_accumulates : genuine accumulates monotonically above floor (commuting flat)
    #   irreversible        : genuine irreversibility residual above floor (controls recoverable)
    #   order_dependent_survivor : genuine survivors differ above floor (commuting identical)
    #   classify the stack:
    #     ratchet_accumulates                 : accumulation AND/OR irrev AND/OR survivor true
    #     no_accumulation_just_perpair        : pairs noncommute (necessary, established) but
    #                                            NONE of the three sufficient signatures hold
    #     mixed                               : some signatures hold, some do not
    # ===================================================================================
    sig_accum = het_class.accumulates && !comm_class.accumulates
    sig_irrev = het_irreversible && comm_recoverable
    sig_surv  = order_picks_survivor && comm_same_survivor
    n_sig = count([sig_accum, sig_irrev, sig_surv])
    controls_clean = !comm_class.accumulates && comm_recoverable && comm_same_survivor

    classification = if !controls_clean
        "INCONCLUSIVE_control_not_flat"
    elseif n_sig == 3
        "ratchet_accumulates"
    elseif n_sig == 0
        "no_accumulation_just_perpair"
    else
        "mixed"
    end

    R["verdict"] = Dict(
        "classification" => classification,
        "signature_accumulation" => sig_accum,
        "signature_irreversibility" => sig_irrev,
        "signature_order_dependent_survivor" => sig_surv,
        "n_signatures_present" => n_sig,
        "controls_clean" => controls_clean,
        "control_accumulates" => comm_class.accumulates,
        "control_recoverable" => comm_recoverable,
        "control_same_survivor" => comm_same_survivor,
        "z3_load_bearing_flip" => z3_load_bearing,
        "interpretation" => "necessary condition (per-pair noncommutation) was established by order_null_killtest.jl. This test asks the SUFFICIENT question: does the order effect ACCUMULATE (monotone depth growth), become IRREVERSIBLE (non-recoverable), and/or pick an ORDER-DEPENDENT SURVIVOR, with the commuting control flat. ratchet_accumulates requires all three above floor with controls clean; no_accumulation_just_perpair means the noncommutation does not aggregate into a ratchet; mixed means some signatures hold.",
    )

    # F01 / N01 witnesses
    R["F01_witness"] = Dict(
        "finite_carrier" => "density operators in D(C^2); finite genuine channel set (6 het + 4 commuting control)",
        "finite_probe" => "$(N_RHO) random density operators + 1 fixed survivor seed",
        "finite_operator" => "Ti/Te/Fi/Fe + Weyl-L/R GKSL + Ni-terrain GKSL (genuine layer maps, reused from order_null_killtest)",
        "finite_path" => "depth-ladder forward vs reversed words; forward-then-reversed recovery; permutation survivors",
    )
    R["N01_witness"] = Dict(
        "accumulation_formula" => "Delta(d) = mean_rho ||Phi_fwd^d(rho) - Phi_rev^d(rho)||_1 as a function of depth d",
        "het_accumulation_growth" => het_growth,
        "het_irreversibility_order_discriminating_residual" => het_ord_mean,
        "het_order_dependent_survivor_max" => het_surv_max,
        "present_above_floor" => (het_growth > noise_floor) || (het_ord_mean > noise_floor) || (het_surv_max > noise_floor),
        "noise_floor" => noise_floor,
    )

    R["tool_manifest"] = Dict(
        "LinearAlgebra" => "load_bearing: svdvals (trace norm), HS norms, channel/PTM algebra; every measured number flows through it.",
        "Statistics" => "supportive: means over the rho ensemble and over depth.",
        "Random" => "load_bearing: random density operators (signatures measured over fresh samples, not planted).",
        "Z3" => "load_bearing: binds the measured accumulation growth to the commuting law; verdict flips UNSAT->SAT on the commuting control.",
        "JSON" => "supportive: receipt emission.",
    )
    R["tool_integration_depth"] = Dict("LinearAlgebra"=>"load_bearing","Z3"=>"load_bearing","Random"=>"load_bearing","Statistics"=>"supportive","JSON"=>"supportive")
    R["blocked_consumers"] = ["any ratchet edge admission","ratchet thesis closure","pairwise nesting","coupling","bridge/Xi/Phi0/Axis0","flux/FEP/physics"]
    R["status_ladder"] = "exists < runs < passes local rerun"

    open(RESULT_PATH, "w") do io
        JSON.print(io, R, 2); write(io, "\n")
    end

    # ---- console summary ----
    println("="^90)
    println("RATCHET ACCUMULATION KILL-TEST  (object_id=ratchet_accumulation_killtest, promotion_allowed=false)")
    println("="^90)
    println("noise_floor = ", noise_floor, "   (eps * PTM-scale $(round(op_scale,digits=3)) * deepest_len $(max_depth_word_len) * 8)")
    println("-"^90)
    println("(1) ACCUMULATION  forward-vs-reversed trace-distance vs depth")
    println("    GENUINE het base (", join(het_names," "), "):")
    for row in het_curve
        println("       depth ", lpad(row["depth"],3), "  Delta_mean = ", round(row["fwd_rev_tracedist_mean"], sigdigits=5))
    end
    println("       accumulates=", het_class.accumulates, "  saturates=", het_class.saturates,
            "  monotone=", het_class.monotone, "  growth_ratio=", round(het_class.growth_ratio, sigdigits=4))
    println("    COMMUTING control (", join(comm_names," "), "):")
    for row in comm_curve
        println("       depth ", lpad(row["depth"],3), "  Delta_mean = ", round(row["fwd_rev_tracedist_mean"], sigdigits=5))
    end
    println("       accumulates=", comm_class.accumulates, " (must be false)")
    println("    requested ladder d=2,4,8,16,32 (Ti WeylR): means=", round.(sub_means, sigdigits=4))
    println("-"^90)
    println("(2) IRREVERSIBILITY  order-discriminating ||Phi_rev(Phi_fwd(rho)) - Phi_fwd(Phi_fwd(rho))||_1")
    println("    GENUINE het  order_resid_mean=", round(het_ord_mean, sigdigits=5), "  irreversible=", het_irreversible,
            "   [raw recover-rho resid=", round(het_raw_mean, sigdigits=5), "]")
    println("    COMMUTING    order_resid_mean=", round(comm_ord_mean, sigdigits=5), "  recoverable=", comm_recoverable,
            "   [raw recover-rho resid=", round(comm_raw_mean, sigdigits=5), "]")
    println("-"^90)
    println("(3) ORDER-DEPENDENT SURVIVOR  pairwise trace-distance of long-time survivors")
    println("    GENUINE het  survivor_dist_max=", round(het_surv_max, sigdigits=5), "  order_picks_survivor=", order_picks_survivor)
    println("    COMMUTING    survivor_dist_max=", round(comm_surv_max, sigdigits=5), "  same_survivor=", comm_same_survivor)
    println("-"^90)
    println("Z3 load-bearing: genuine=", z3_genuine, " commuting=", z3_commuting, " flip=", z3_load_bearing)
    println("-"^90)
    println("SIGNATURES:  accumulation=", sig_accum, "  irreversibility=", sig_irrev, "  order_survivor=", sig_surv,
            "  (", n_sig, "/3)")
    println("CONTROLS clean (commuting flat+recoverable+same-survivor): ", controls_clean)
    println("DECISIVE VERDICT: ", classification)
    println("Wrote: ", RESULT_PATH)
    return R
end

run()
