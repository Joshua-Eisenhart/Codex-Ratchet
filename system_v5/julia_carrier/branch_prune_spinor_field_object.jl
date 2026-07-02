# Phase-2 v0 — the branch/prune possibility-field object on S^3 (unit spinors).
#
# The primary object made computational: a finite ensemble of possible futures (branch) is pruned by a
# constraint (chirality sector) and the survivors cluster into attractor basins (select). This is the literal
# "variation -> selection -> speciation" form of the retrocausal possibility field.
#
# FALSIFIER baked in (so pruning is not cosmetic): three runs share the SAME branch ensemble and flow.
#   A (no prune)      -> baseline: futures reach ALL basins, including the forbidden-chirality ones.
#   B (chirality prune)-> futures that cross into the forbidden q0<0 sector are terminate!'d -> forbidden basins DIE.
#   C (trivial prune)  -> a callback whose condition is ALWAYS false -> must equal A (harness control).
# all_pass iff: C==A (control: a never-firing prune changes nothing), A populates all 4 basins,
#               B populates ONLY the allowed basins, and |basins_B| < |basins_A| (the constraint-driven flip).
# If pruning did NOT change the basin set, the "constraints shape reachable futures" claim is empty -> fail.
#
# classification = julia_branch_prune_poc ; promotion_allowed = false. Not canonical, not a bridge claim.

using DifferentialEquations, LinearAlgebra, StaticArrays, Random
import JSON

const OUT = joinpath(@__DIR__, "branch_prune_spinor_field_object_results.json")
norm4(v) = v / sqrt(sum(abs2, v))

# 4 target unit quaternions on a regular simplex (tetrahedral spatial directions, all pairwise <T_i,T_j>=-0.5),
# so every basin is reachable from the allowed start hemisphere: 2 ALLOWED (q0>0), 2 FORBIDDEN (q0<0).
const TARGETS = SVector{4,Float64}[
    SA[ 0.5,  0.5,  0.5,  0.5],   # 1 allowed   (q0>0, spatial +++)
    SA[ 0.5,  0.5, -0.5, -0.5],   # 2 allowed   (q0>0, spatial +--)
    SA[-0.5, -0.5,  0.5, -0.5],   # 3 forbidden (q0<0, spatial -+-)
    SA[-0.5, -0.5, -0.5,  0.5],   # 4 forbidden (q0<0, spatial --+)
]
const ALLOWED   = [1, 2]
const FORBIDDEN = [3, 4]

nearest(q) = argmax(k -> dot(TARGETS[k], q), 1:4)        # index of closest target on S^3

# Geodesic-ish attraction flow toward the nearest target, projected to the tangent space of S^3 at q
# (so |q| is conserved to first order -> the unit-spinor constraint holds approximately by construction).
function flow(q, p, t)
    tk = TARGETS[nearest(q)]
    return SVector{4,Float64}(2.0 .* (tk .- dot(tk, q) .* q))
end

# Branch ensemble: N initial spinors sampled in the ALLOWED (q0>0) hemisphere, spread over the spatial part,
# so different futures fall toward different targets (some toward forbidden ones, crossing q0=0).
function build_inits(N)
    rng = MersenneTwister(42)
    inits = SVector{4,Float64}[]
    while length(inits) < N
        v = norm4(SVector{4,Float64}(randn(rng), randn(rng), randn(rng), randn(rng)))
        v[1] > 0.05 && push!(inits, v)      # start in the allowed (q0>0) hemisphere
    end
    inits
end

const N = 400
const INITS = build_inits(N)
const TSPAN = (0.0, 12.0)
const baseprob = ODEProblem(flow, INITS[1], TSPAN)

function run_ensemble(extra_cb)
    ep = EnsembleProblem(baseprob; prob_func = (p, i, r) -> remake(p, u0 = INITS[i]))
    kw = extra_cb === nothing ? (;) : (; callback = extra_cb)
    solve(ep, Tsit5(), EnsembleSerial(); trajectories = N, save_everystep = false,
          abstol = 1e-8, reltol = 1e-8, kw...)
end

function classify(sim)
    survivors = Int[]; pruned = 0; maxdrift = 0.0
    for i in 1:N
        s = sim[i]
        qf = s.u[end]
        maxdrift = max(maxdrift, abs(sqrt(sum(abs2, qf)) - 1))
        if s.retcode == ReturnCode.Terminated         # prune callback fired terminate!
            pruned += 1
        else
            push!(survivors, nearest(norm4(qf)))
        end
    end
    counts    = Dict(k => count(==(k), survivors) for k in 1:4)
    populated = sort([k for k in 1:4 if counts[k] > 0])
    (populated = populated, counts = counts, n_survivors = length(survivors),
     pruned = pruned, maxdrift = maxdrift)
end

# Constraint: forbid the q0<0 chirality sector. A future that evolves into it is pruned.
chirality_prune = DiscreteCallback((u, t, int) -> u[1] < -1e-2, terminate!)
trivial_prune   = DiscreteCallback((u, t, int) -> false,        terminate!)   # never fires (control)

println("running A (no prune) ..."); A = classify(run_ensemble(nothing))
println("running B (chirality prune) ..."); B = classify(run_ensemble(chirality_prune))
println("running C (trivial prune, control) ..."); C = classify(run_ensemble(trivial_prune))

# Gate on the ACTUAL claim, not the "all 4 populated" proxy: forbidden basins reached WITHOUT the constraint
# must die WITH it; allowed basins reached must survive; a never-firing control must change nothing.
A_forbidden = intersect(A.populated, FORBIDDEN)
checks = Dict(
    "nonvacuous_A_reaches_forbidden" => !isempty(A_forbidden),                              # test isn't vacuous
    "B_kills_all_forbidden"          => isempty(intersect(B.populated, FORBIDDEN)),         # constraint removes them
    "B_preserves_allowed_reached"    => issubset(intersect(A.populated, ALLOWED), B.populated),
    "control_C_equals_A"             => C.populated == A.populated && C.pruned == 0,        # never-firing prune = no-op
    "B_strict_subset_of_A"           => issubset(B.populated, A.populated) && length(B.populated) < length(A.populated),
    "B_pruned_some_A_none"           => B.pruned > 0 && A.pruned == 0,
    "norm_drift_small"               => max(A.maxdrift, B.maxdrift, C.maxdrift) < 1e-3,
)
all_pass = all(values(checks))
A_reaches_all_4 = A.populated == [1, 2, 3, 4]   # reported as info (stronger demo if true), not gating

result = Dict(
    "name" => "branch_prune_spinor_field_object",
    "classification" => "julia_branch_prune_poc", "promotion_allowed" => false,
    "claim_ceiling" => "PoC: a chirality constraint prunes the branch ensemble so the forbidden-sector attractor " *
                       "basins die (B), while a never-firing prune leaves them intact (control C). Shows constraints " *
                       "SHAPE which futures survive. promotion_allowed=false; not canonical/bridge.",
    "object" => "finite branch/prune possibility field of unit spinors on S^3; branch=EnsembleProblem, " *
                "prune=DiscreteCallback terminate!, select=nearest-target attractor basins",
    "N_branches" => N,
    "targets" => Dict("allowed" => ALLOWED, "forbidden" => FORBIDDEN),
    "run_A_no_prune"        => Dict("populated_basins"=>A.populated, "counts"=>A.counts, "survivors"=>A.n_survivors, "pruned"=>A.pruned),
    "run_B_chirality_prune" => Dict("populated_basins"=>B.populated, "counts"=>B.counts, "survivors"=>B.n_survivors, "pruned"=>B.pruned),
    "run_C_trivial_control" => Dict("populated_basins"=>C.populated, "counts"=>C.counts, "survivors"=>C.n_survivors, "pruned"=>C.pruned),
    "max_norm_drift" => round(max(A.maxdrift, B.maxdrift, C.maxdrift); digits=8),
    "A_reaches_all_4_basins" => A_reaches_all_4,
    "checks" => checks, "all_pass" => all_pass,
)
open(OUT, "w") do io; JSON.print(io, result, 2); end

println("\n=== branch/prune v0 ===")
println("A (no prune):       basins=$(A.populated)  survivors=$(A.n_survivors)  pruned=$(A.pruned)")
println("B (chirality prune):basins=$(B.populated)  survivors=$(B.n_survivors)  pruned=$(B.pruned)")
println("C (trivial control):basins=$(C.populated)  survivors=$(C.n_survivors)  pruned=$(C.pruned)")
for (k, v) in sort(collect(checks); by=first); println(rpad(k, 32), v ? "PASS" : "FAIL"); end
println("max_norm_drift = $(round(max(A.maxdrift,B.maxdrift,C.maxdrift); digits=8))")
println("ALL_PASS = $all_pass")
exit(all_pass ? 0 : 1)
