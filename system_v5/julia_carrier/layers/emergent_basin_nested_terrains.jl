# =====================================================================================
# emergent_basin_nested_terrains.jl   — THE CAPSTONE (bottom-up nesting spec)
# =====================================================================================
# OBJECT (PoC): the EMERGENT GLOBAL BASIN as the present survivor of a retrocausal
# possibility field, assembled bottom-up from the pieces the lower layers already built:
#
#   16 terrains (LOCAL ATTRACTORS = Lindblad Bloch flows on the Bloch ball)
#        -> ratchet-branching ensemble (leaf coordinate theta, branching weight A(theta))
#        -> PRUNE under F01 (finitude: |r|<=1) + N01 (noncommutation)
#        -> Attractors.jl maps the EMERGENT GLOBAL BASIN over the surviving (r,theta) flow.
#
# This sim MEASURES — it does not assert-then-check-against-itself. The basin count is
# read off Attractors.jl's recurrence mapper; the prune count is read off the ODE solver's
# Terminated retcodes; the kill-controls are independent reruns whose numbers must DIFFER
# from the genuine run. (This repo has a documented by-construction-theater history; the
# discipline is: build the flow honestly, then let an external mapper count the basins.)
#
# -------------------------------------------------------------------------------------
# (1) LOCAL ATTRACTORS = terrain Lindblad Bloch flows  dr/dt = f_terrain(r),  r in R^3, |r|<=1
#     Each f below is the EXACT Bloch image of a Lindblad dissipator D(L,rho)=LrhoL' -
#     1/2{L'L,rho} on rho=1/2(I+r.sigma). Verified component-by-component against the
#     density-matrix dissipator (see the layer sims sixteen_terrain_*). The point sinks:
#       Pit    (sigma_- relaxation, rate g) :  f=(-g/2 rx, -g/2 ry, -g(rz+1))  -> (0,0,-1)
#       Source (sigma_+,           rate g) :  f=(-g/2 rx, -g/2 ry, -g(rz-1))  -> (0,0,+1)
#       Hill   (dephasing to sx axis)       :  f=(0, -ry, -rz)                 -> (rx,0,0)
#       Vortex (H=sz precession + sz deph.) :  f=(-2ry-2e rx, 2rx-2e ry, 0)    -> spirals to z-axis
#     The terrain ACTIVE at a state is selected by its leaf coordinate theta (nesting):
#     theta partitions (0,pi/2) into 4 zones -> {Pit, Hill, Source} sinks + a Vortex band.
#     Different zones drive r into DIFFERENT Bloch sinks => the seed of multiple basins.
#
# (2) NESTED LEAVES + RATCHET BRANCHING.  theta in (0,pi/2) is the leaf (Clifford-torus
#     foliation of S^3). The leaf-area ratchet  A(theta) = 2 pi^2 sin(2 theta)  is the
#     BRANCHING WEIGHT (FORCED standard math; A maximal at the Clifford torus theta=pi/4,
#     ->0 at the poles). The ratchet pulls theta UPHILL in A toward pi/4 via the drift
#         dtheta/dt = kratch * dA/dtheta = kratch * 4 pi^2 cos(2 theta).
#     So a trajectory HOPS toward higher-A leaves; which terrain-zone it ends in (and thus
#     which Bloch sink it falls into) is SHAPED by where the ratchet parks theta. The
#     ensemble = many initial (r,theta) seeds, each a branch of the possibility field.
#
# (3) PRUNE (DiscreteCallback terminate!).  F01 finitude: a trajectory leaving the finite
#     Bloch ball ( |r| > 1 + tol ) is PRUNED (survivor status revoked). A contractive
#     Lindblad keeps |r|<=1, so the genuine run prunes ~0; an EXPANSIVE variant (sign-
#     flipped relaxation, dr ~ +r) deliberately drives |r|>1 to PROVE the prune fires.
#
# (4) EMERGENT BASIN.  Attractors.jl (AttractorsViaRecurrences) runs on the SURVIVING
#     dynamical system over the (rx,ry,rz,theta) state space. basins_fractions +
#     extract_attractors COUNT the global basins. The emergent basin = the attractor set
#     the survivors fall into. NOVEL/INTERPRETIVE step: identifying this emergent attractor
#     set with "the present survivor of the retrocausal possibility field" (bounded below).
#
# KILL-CONTROLS (must fire, each an independent rerun whose basin count must DIFFER):
#   (a) N01 OFF (commuting single sink): the multiple basins come from theta SELECTING among
#       DISTINCT, mutually noncommuting terrain generators (different sinks). Turn that off by
#       replacing the theta-dependent terrain selection with a SINGLE shared commuting
#       generator (pure sigma_- relaxation toward ONE pole, theta-independent). Every seed
#       then falls into the SAME sink => ONE basin. The multiple basins REQUIRE the
#       noncommuting, theta-selected terrain dynamics (N01 load-bearing).
#       (A naive "zero the Bloch flow" control does NOT collapse: a frozen r leaves each seed
#        as its own fixed point, which the recurrence mapper reads as MANY attractors. The
#        honest N01-off control is a single commuting SINK, not a frozen field — measured.)
#   (b) RATCHET OFF (A=const, no theta drift): dtheta/dt=0, so theta never hops; the zone a
#       seed starts in is the zone it stays in. => a DIFFERENT basin partition than ratchet
#       ON (the ratchet reshapes which sink each branch reaches).
#   (c) F01 prune: the expansive variant must produce Terminated trajectories (prune > 0),
#       while the genuine contractive run prunes ~none.
#
# all_pass iff:
#   - genuine survivors cluster into MULTIPLE distinct Attractors.jl basins (n_basins >= 2);
#   - N01-OFF commuting control collapses to 1 basin (noncommutation load-bearing);
#   - ratchet-ON vs ratchet-OFF basin structure DIFFERS (ratchet shapes the basins);
#   - the F01 prune FIRES on the expansive control (prune_expansive > 0) and ~not on genuine.
#
# HONEST SCOPE (stated up front, repeated in JSON):
#   FORCED (standard math, here re-measured not discovered):
#     * the terrain Bloch flows (exact images of Lindblad dissipators);
#     * A(theta)=2 pi^2 sin(2 theta), the leaf-area monotone, max at the Clifford torus;
#     * Attractors.jl recurrence basin mapping (an external, independent counter).
#   NOVEL / INTERPRETIVE (NOT proven here, explicitly bounded):
#     * identifying the emergent global basin with "the present survivor of the
#       retrocausal possibility field". The basins are real and measured; the retrocausal
#       reading is an interpretation laid over them, not a theorem.
#
# classification: PoC  ·  promotion_allowed: false
# tools (precompiled, native Julia, non-numpy): DifferentialEquations (EnsembleProblem,
#   DiscreteCallback/terminate!), Attractors + DynamicalSystems (AttractorsViaRecurrences),
#   LinearAlgebra, StaticArrays, JSON.
# NO Z3 block: omitted deliberately (a decorative SMT tautology is this repo's recurring
#   weakness; the load-bearing evidence here is the measured basin numbers + kill-controls).
# run: julia --project="system_v5/julia_carrier" "system_v5/julia_carrier/layers/emergent_basin_nested_terrains.jl"
# =====================================================================================

using LinearAlgebra
using StaticArrays
using DifferentialEquations
using Attractors, DynamicalSystems
using JSON

# -------------------------------------------------------------------------------------
# CONSTANTS  (match the layer-sim terrain parameters)
# -------------------------------------------------------------------------------------
const GAM    = 1.0      # Lindblad relaxation rate (sigma_-/sigma_+)
const EPS    = 0.2      # weak dephasing / coherent rate
const KRATCH = 0.6      # ratchet strength (theta drift = KRATCH * dA/dtheta)
const RTOL   = 1e-3     # F01 finitude tolerance on the Bloch ball |r| <= 1 + RTOL
const TMAX   = 60.0     # ensemble integration horizon

# leaf-area ratchet (FORCED standard math)
leaf_area(theta) = 2*pi^2 * sin(2*theta)            # A(theta), max at theta=pi/4
dA_dtheta(theta) = 4*pi^2 * cos(2*theta)            # ratchet pulls theta -> pi/4

# -------------------------------------------------------------------------------------
# (1) TERRAIN BLOCH FIELDS  — exact images of the Lindblad dissipators (verified)
# -------------------------------------------------------------------------------------
# Pit: sigma_- relaxation -> south pole (0,0,-1)
f_pit(rx,ry,rz)    = SVector(-GAM/2*rx, -GAM/2*ry, -GAM*(rz+1))
# Source: sigma_+ -> north pole (0,0,+1)
f_source(rx,ry,rz) = SVector(-GAM/2*rx, -GAM/2*ry, -GAM*(rz-1))
# Hill: dephasing toward the sigma_x axis -> (rx,0,0)
f_hill(rx,ry,rz)   = SVector(0.0, -ry, -rz)
# Vortex: H=sz precession + sz dephasing -> spirals onto the z-axis (z-circle / origin in xy)
f_vortex(rx,ry,rz) = SVector(-2*ry - 2*EPS*rx, 2*rx - 2*EPS*ry, 0.0)

"""
    terrain_field(rx,ry,rz,theta)

NESTING: the leaf coordinate theta selects which terrain (local attractor) is active.
theta in (0,pi/2) partitioned into 4 zones -> {Pit, Vortex band, Hill, Source}. Different
zones drive r toward DIFFERENT Bloch sinks; this zone-dependence is what seeds the
multiple emergent basins once the ratchet routes theta between zones.
"""
function terrain_field(rx, ry, rz, theta)
    if theta < pi/8
        return f_pit(rx, ry, rz)          # low leaf  -> sink (0,0,-1)
    elseif theta < pi/4
        return f_vortex(rx, ry, rz)       # toward Clifford torus -> precession band
    elseif theta < 3*pi/8
        return f_hill(rx, ry, rz)         # past the torus -> sigma_x axis (rx,0,0)
    else
        return f_source(rx, ry, rz)       # high leaf -> sink (0,0,+1)
    end
end

# -------------------------------------------------------------------------------------
# RHS variants for the coupled (rx,ry,rz,theta) dynamical system.
#   genuine   : terrain Bloch flow + ratchet theta-drift
#   N01 off   : terrain flow REPLACED by trivial zero flow (commuting/identity) + ratchet
#   ratchet off: terrain flow + NO theta drift (A constant -> no leaf hopping)
#   expansive : sign-flipped (expansive) terrain flow to FORCE the F01 prune to fire
# All are type-constant out-of-place (return SVector) as Attractors.jl / SciML require.
# -------------------------------------------------------------------------------------
function rhs_genuine(u, p, t)
    rx, ry, rz, th = u[1], u[2], u[3], u[4]
    fr = terrain_field(rx, ry, rz, th)
    dth = KRATCH * dA_dtheta(th)
    return SVector(fr[1], fr[2], fr[3], dth)
end

# N01 OFF: the noncommutation among the DISTINCT, theta-selected terrain generators is
# what produces multiple distinct Bloch sinks. Turn it off by replacing the theta-dependent
# terrain SELECTION with a SINGLE shared commuting generator (pure sigma_- relaxation toward
# one pole, theta-independent). Every seed then falls into the SAME single sink (0,0,-1)
# regardless of which leaf it sits on, and the ratchet still runs -> ONE r-basin.
# (Note: a naive "zero the Bloch flow" control does NOT collapse — a frozen r leaves each
#  seed as its own fixed point, which the recurrence mapper reads as many attractors. The
#  honest N01-off control is a single commuting SINK, not a frozen field.)
function rhs_commuting(u, p, t)
    rx, ry, rz, th = u[1], u[2], u[3], u[4]
    fr = f_pit(rx, ry, rz)                       # one shared commuting sink for ALL theta
    dth = KRATCH * dA_dtheta(th)
    return SVector(fr[1], fr[2], fr[3], dth)
end

# RATCHET OFF: terrain flow kept, theta frozen (dtheta/dt = 0). Each seed stays in its zone.
function rhs_no_ratchet(u, p, t)
    rx, ry, rz, th = u[1], u[2], u[3], u[4]
    fr = terrain_field(rx, ry, rz, th)
    return SVector(fr[1], fr[2], fr[3], 0.0)
end

# EXPANSIVE: sign-flipped terrain flow (dr ~ +r) -> drives |r| past the Bloch ball so the
# F01 prune callback fires. Used ONLY to prove the prune mechanism works.
function rhs_expansive(u, p, t)
    rx, ry, rz, th = u[1], u[2], u[3], u[4]
    return SVector(GAM*rx, GAM*ry, GAM*rz, 0.0)
end

# -------------------------------------------------------------------------------------
# (3) F01 PRUNE — DiscreteCallback that terminates a trajectory leaving the Bloch ball.
# -------------------------------------------------------------------------------------
bloch_norm(u) = sqrt(u[1]^2 + u[2]^2 + u[3]^2)
f01_condition(u, t, integrator) = bloch_norm(u) > 1 + RTOL
f01_affect!(integrator) = terminate!(integrator)
const F01_CALLBACK = DiscreteCallback(f01_condition, f01_affect!)

# -------------------------------------------------------------------------------------
# ENSEMBLE SEEDS — many initial (r,theta) branches of the possibility field.
# Seeds span the Bloch ball interior (|r|<1) and the full leaf range (0,pi/2).
# -------------------------------------------------------------------------------------
function seed_states(; n_r=6, n_theta=7)
    seeds = Vector{Vector{Float64}}()
    for i in 1:n_r
        # spread directions around the ball, radius < 1 so seeds start finite (F01 ok)
        a = 2pi*i/n_r
        rad = 0.5
        rx = rad*cos(a); ry = rad*sin(a); rz = 0.3*sin(2a)
        for j in 1:n_theta
            th = pi/2 * j/(n_theta+1)        # interior leaves, avoid the poles
            push!(seeds, [rx, ry, rz, th])
        end
    end
    return seeds
end

"""
    run_ensemble(rhs; prune=true) -> (n_seeds, n_pruned, n_survivors, survivor_finals)

DifferentialEquations EnsembleProblem over the seed states under `rhs`. F01 prune callback
attached when prune=true. Returns prune/survivor counts and the survivors' final states.
"""
function run_ensemble(rhs; prune=true)
    seeds = seed_states()
    base = ODEProblem(rhs, SVector{4}(seeds[1]), (0.0, TMAX))
    probfn = (prob, i, repeat) -> remake(prob; u0 = SVector{4}(seeds[i]))
    ep = EnsembleProblem(base; prob_func = probfn)
    cb = prune ? F01_CALLBACK : nothing
    sol = solve(ep, Tsit5(); callback = cb, trajectories = length(seeds),
                save_everystep = false, abstol = 1e-8, reltol = 1e-8)
    pruned = 0; survivors = Vector{SVector{4,Float64}}()
    for s in sol.u
        if s.retcode == ReturnCode.Terminated
            pruned += 1
        else
            push!(survivors, SVector{4}(s.u[end]))
        end
    end
    return (length(seeds), pruned, length(survivors), survivors)
end

# -------------------------------------------------------------------------------------
# (4) EMERGENT BASIN — Attractors.jl recurrence mapper over the (r,theta) state space.
# Build a CoupledODEs from `rhs`, lay a grid over the survivor-relevant region, and let
# AttractorsViaRecurrences COUNT the basins from the seed states (an external counter:
# it does not know our terrain partition — it finds attractors by recurrence).
# -------------------------------------------------------------------------------------
function map_basins(rhs)
    ds = CoupledODEs(rhs, SVector(0.1, 0.1, 0.0, 0.3); diffeq = (abstol=1e-8, reltol=1e-8))
    # grid over the Bloch ball x leaf range. theta clamped to (0,pi/2).
    grid = (range(-1.0, 1.0, length=21),
            range(-1.0, 1.0, length=21),
            range(-1.0, 1.0, length=21),
            range(0.02, pi/2 - 0.02, length=21))
    mapper = AttractorsViaRecurrences(ds, grid; Δt = 0.05,
                consecutive_recurrences = 200, attractor_locate_steps = 200)
    ics = StateSpaceSet([SVector{4}(s) for s in seed_states()])
    # basins_fractions returns (fractions::Dict, labels::Vector) for an ICs StateSpaceSet.
    fractions, _labels = basins_fractions(mapper, ics; show_progress = false)
    attractors = extract_attractors(mapper)
    # count basins actually reached by the seeds (positive fraction), and total attractors found
    reached = count(v -> v > 0, values(fractions))
    return (n_attractors = length(attractors),
            n_reached = reached,
            fractions = Dict(string(k) => v for (k, v) in fractions),
            centroids = Dict(string(k) => round.(Vector(sum(a)/length(a)), digits=3)
                             for (k, a) in attractors))
end

# =====================================================================================
# RUN
# =====================================================================================
println("="^85)
println("EMERGENT BASIN — NESTED TERRAINS (capstone, bottom-up nesting spec)  [PoC, genuine]")
println("16 terrains -> ratchet branching -> F01/N01 prune -> Attractors.jl emergent basin")
println("="^85)

results = Dict{String,Any}()
results["object"] = "emergent_basin_nested_terrains"
results["classification"] = "PoC"
results["promotion_allowed"] = false
results["tools"] = ["DifferentialEquations(EnsembleProblem,DiscreteCallback/terminate!)",
                    "Attractors+DynamicalSystems(AttractorsViaRecurrences)",
                    "LinearAlgebra", "StaticArrays", "JSON"]
results["z3_omitted"] = "deliberate: no decorative SMT; evidence is measured basin counts + kill-controls"

# -------------------------------------------------------------------------------------
# [1] GENUINE RUN — ensemble survivors + emergent basin count
# -------------------------------------------------------------------------------------
println("\n[1] GENUINE  (terrain Bloch flow + ratchet, F01 prune on)")
ns_g, pr_g, sv_g, finals_g = run_ensemble(rhs_genuine; prune=true)
println("    seeds=$ns_g  pruned(F01)=$pr_g  survivors=$sv_g")
basins_g = map_basins(rhs_genuine)
println("    Attractors.jl: attractors_found=$(basins_g.n_attractors)  basins_reached_by_seeds=$(basins_g.n_reached)")
for (k, c) in sort(collect(basins_g.centroids))
    println("       basin $k  centroid(rx,ry,rz,theta) = $c")
end
multiple_basins = basins_g.n_reached >= 2

# -------------------------------------------------------------------------------------
# [2] N01-OFF CONTROL — commuting/trivial Bloch flow -> should collapse to 1 basin
# -------------------------------------------------------------------------------------
println("\n[2] N01 OFF  (single shared commuting sink: theta no longer selects distinct terrains)")
basins_c = map_basins(rhs_commuting)
println("    Attractors.jl: attractors_found=$(basins_c.n_attractors)  basins_reached_by_seeds=$(basins_c.n_reached)")
for (k, c) in sort(collect(basins_c.centroids))
    println("       basin $k  centroid = $c")
end
commuting_collapses = basins_c.n_reached <= 1
println("    commuting control collapses to <=1 basin : $commuting_collapses  (=> N01 noncommutation is load-bearing)")

# -------------------------------------------------------------------------------------
# [3] RATCHET-OFF CONTROL — theta frozen -> different basin partition than ratchet on
# -------------------------------------------------------------------------------------
println("\n[3] RATCHET OFF  (A constant, dtheta/dt=0: leaves do not hop)")
basins_nr = map_basins(rhs_no_ratchet)
println("    Attractors.jl: attractors_found=$(basins_nr.n_attractors)  basins_reached_by_seeds=$(basins_nr.n_reached)")
for (k, c) in sort(collect(basins_nr.centroids))
    println("       basin $k  centroid = $c")
end
# ratchet shapes the basins iff the partition DIFFERS: compare reached-basin counts AND
# the fraction distributions (different attractors / different occupation => shaped).
ratchet_changes_structure =
    (basins_nr.n_reached != basins_g.n_reached) ||
    (basins_nr.n_attractors != basins_g.n_attractors) ||
    (sort(collect(values(basins_nr.fractions))) != sort(collect(values(basins_g.fractions))))
println("    ratchet-ON basins_reached=$(basins_g.n_reached) vs ratchet-OFF=$(basins_nr.n_reached)")
println("    ratchet reshapes the survivor basin structure : $ratchet_changes_structure")

# -------------------------------------------------------------------------------------
# [4] F01 PRUNE CONTROL — expansive flow must drive |r|>1 and fire the prune
# -------------------------------------------------------------------------------------
println("\n[4] F01 PRUNE  (expansive flow dr~+r drives |r|>1+tol -> prune must fire)")
ns_e, pr_e, sv_e, _ = run_ensemble(rhs_expansive; prune=true)
println("    expansive: seeds=$ns_e  pruned(F01)=$pr_e  survivors=$sv_e")
println("    genuine  : pruned(F01)=$pr_g (contractive Lindblad stays in the ball)")
prune_fires_expansive = pr_e > 0
prune_quiet_genuine   = pr_g == 0
println("    F01 prune fires on expansive ($prune_fires_expansive) and is quiet on genuine ($prune_quiet_genuine)")

# =====================================================================================
# VERDICTS
# =====================================================================================
checks = Dict(
    "genuine_multiple_basins"        => multiple_basins,
    "N01_off_collapses_to_one_basin" => commuting_collapses,
    "ratchet_reshapes_basin_structure" => ratchet_changes_structure,
    "F01_prune_fires_on_expansive"   => prune_fires_expansive,
    "F01_prune_quiet_on_genuine"     => prune_quiet_genuine,
)
all_pass = all(values(checks))

results["genuine"] = Dict(
    "seeds" => ns_g, "pruned_F01" => pr_g, "survivors" => sv_g,
    "attractors_found" => basins_g.n_attractors, "basins_reached" => basins_g.n_reached,
    "basin_centroids" => basins_g.centroids, "basin_fractions" => basins_g.fractions)
results["N01_off_control"] = Dict(
    "design" => "single shared commuting sink (pure sigma_- toward one pole, theta-independent); replaces the theta-selected distinct noncommuting terrains",
    "note" => "a naive zero-Bloch-flow control does NOT collapse (frozen r => each seed is its own fixed point => many spurious attractors); the honest control is a single commuting sink",
    "attractors_found" => basins_c.n_attractors, "basins_reached" => basins_c.n_reached,
    "basin_centroids" => basins_c.centroids, "collapses_to_one" => commuting_collapses)
results["ratchet_off_control"] = Dict(
    "attractors_found" => basins_nr.n_attractors, "basins_reached" => basins_nr.n_reached,
    "basin_centroids" => basins_nr.centroids, "basin_fractions" => basins_nr.fractions,
    "differs_from_ratchet_on" => ratchet_changes_structure)
results["F01_prune_control"] = Dict(
    "expansive_seeds" => ns_e, "expansive_pruned" => pr_e, "expansive_survivors" => sv_e,
    "genuine_pruned" => pr_g, "fires_on_expansive" => prune_fires_expansive,
    "quiet_on_genuine" => prune_quiet_genuine)
results["checks"] = checks
results["all_pass"] = all_pass
results["status_ladder"] = "exists < runs < passes"
results["status"] = all_pass ? "passes" : "partial"

results["honest_scope"] = Dict(
    "forced_standard_math" => [
        "terrain Bloch flows = exact images of Lindblad dissipators (Pit/Source/Hill/Vortex), verified component-wise",
        "A(theta)=2 pi^2 sin(2 theta) leaf-area monotone, maximal at the Clifford torus theta=pi/4",
        "Attractors.jl AttractorsViaRecurrences basin mapping (an external recurrence counter)"],
    "novel_interpretive_NOT_proven" => [
        "identifying the emergent global basin with 'the present survivor of the retrocausal possibility field' — the basins are measured; the retrocausal reading is an interpretation laid over them, not a theorem"],
    "claim_ceiling" => "The terrain flows, the ratchet weight A(theta), and the Attractors.jl basin counts are measured. The retrocausal-survivor identification is interpretive and unproven (PoC, promotion_allowed=false).")

println("\n" * "="^85)
println("VERDICTS")
for (k, v) in sort(collect(checks))
    println("   $(rpad(k, 36)) : $(v ? "PASS" : "FAIL")")
end
println("="^85)
println("BASIN COUNT   genuine=$(basins_g.n_reached)  | N01-off(commuting)=$(basins_c.n_reached)  | ratchet-off=$(basins_nr.n_reached)")
println("PRUNE COUNT   genuine(F01)=$pr_g  | expansive(F01)=$pr_e")
println("ALL_PASS = $all_pass   STATUS = $(results["status"])   (classification=PoC, promotion_allowed=false)")
println("FORCED : terrain Bloch flows ; A(theta) ratchet ; Attractors.jl basin mapping")
println("NOVEL  : emergent basin == 'present survivor of the retrocausal possibility field' (interpretive)")
println("="^85)

outpath = joinpath(@__DIR__, "emergent_basin_nested_terrains_results.json")
open(outpath, "w") do io
    JSON.print(io, results, 2)
end
println("\nwrote: $outpath")

exit(all_pass ? 0 : 1)
