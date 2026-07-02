# =====================================================================================
# spacetime_from_entanglement_nested.jl
# =====================================================================================
# OBJECT (PoC): Spacetime-from-entanglement (Van Raamsdonk / Ryu-Takayanagi) on the
# NESTED-TORI substrate, reconstructed NON-CIRCULARLY. The emergent geometry — the
# ORDERING of the leaf regions and the DISTANCES between them — is the OUTPUT read off
# the entanglement, never planted as input.
#
# SUBSTRATE.  The nested Hopf/Clifford tori foliate S^3 ⊂ C^2 by flat 2-tori
#     T^2(theta) = { (cos(theta) e^{ia}, sin(theta) e^{ib}) : a,b ∈ [0,2pi) },
# at latitudes theta ∈ (0, pi/2). We take N "leaf" sites at a theta-grid and lay them on
# a 1D radial Dirac chain (the radial direction of the foliation: D_S3 splits as
# gamma^theta(d/dtheta + H/2) + D_T2(theta); gamma^theta d/dtheta is the inter-leaf
# kinetic / hopping term). The hopping amplitude between adjacent leaves is set by the
# foliation geometry t_i = sqrt(A(theta_i)A(theta_{i+1}))/A_max with A(theta)=2pi^2 sin2theta
# — a positive, foliation-derived modulation of a tight-binding chain. The chain is closed
# into a RING (periodic BC), matching the radial foliation closing the two degenerate
# Hopf cores (theta=0 and theta=pi/2) onto one cycle, and matching this repo's own
# entropy_is_geometry_free_fermion.jl convention. (The ring is a 1D PROXY for the radial
# S^3 direction; it is NOT the full S^3 — see the claim ceiling.)
#
# WHY A RING, AND TWO MEASURED PHYSICAL FACTS THAT SHAPE THE PROBE (honest, not bugs).
#   (i)  The half-filled nearest-neighbour chain is bipartite: its ground-state correlation
#        matrix has C[i,i+k]=0 for EVEN k≠0 (particle-hole / sublattice structure). So
#        SINGLE-SITE mutual information vanishes identically on even separations — a single
#        site is the wrong "region" for a clean emergent metric. We take the regions to be
#        CONTIGUOUS LEAF-BLOCKS (the task's "leaf regions" / "contiguous leaf-block"),
#        whose block MI decays smoothly. The even-sep single-site vanishing is REPORTED.
#   (ii) On a RING the emergent distance is naturally the RING (geodesic) distance
#        ring(p,q)=min(|p-q|, M-|p-q|): block MI decays monotonically in ring distance and
#        the geometry it reconstructs is a CYCLE. (We verified the OPEN chain instead shows
#        a U-shaped MI — high at BOTH ends — the standard open-boundary image effect; using
#        |i-j| there would falsely report non-monotonicity. The ring removes that artifact;
#        the emergent geometry is honestly a cycle, not a line with two free ends.)
#
# WHAT IS MEASURED, AND WHY IT IS NON-CIRCULAR.
#   1. Exact free-fermion ground state. C_ij = sum_{occ} u_i u_j (correlation matrix of
#      the half-filled Dirac sea). No state is assumed; C is the exact projector onto the
#      negative-energy one-body modes of the foliation-modulated chain.
#   2. Mutual information I(A:B) = S(A)+S(B)-S(AB) between contiguous leaf-BLOCKS, from the
#      Peschel correlation-matrix entropies. Measured, not assumed.
#   3. RECONSTRUCT THE GEOMETRY from d(A,B) = -log I(A,B) (Van Raamsdonk). The block
#      CYCLIC ORDER is recovered by a greedy nearest-neighbour walk on d ALONE (start at
#      any block, then always step to the nearest unused block). The recovered order is
#      compared to the true theta-cycle ONLY AFTERWARD, allowing rotation and reflection.
#      The block indices never enter the reconstruction; only the entanglement distances
#      do. This is the non-circular core: geometry OUT, not IN. We also verify block MI
#      decays monotonically in the RECONSTRUCTED ring distance.
#   4. AREA LAW. Entanglement entropy S(L) of a contiguous leaf-block scales with the cut
#      BOUNDARY (sub-volume), not the block VOLUME. For the critical RING the Calabrese-
#      Cardy form is S(L) ~ (c/3) log[(N/pi) sin(pi L/N)] — symmetric S(L)=S(N-L) — so the
#      log-fit is taken over the chord variable x=log[(N/pi)sin(pi L/N)] on L<=N/2 and must
#      beat the linear (volume) fit in L. S is a geometric area.
#
# KILL-CONTROLS (must fire — a clean negative here is the whole point):
#   (a) PRODUCT (unentangled) state: C is diagonal (each leaf empty or full) ⇒ I=0 for all
#       disjoint regions ⇒ d=-log I is +inf/undefined ⇒ NO reconstructable geometry. Remove
#       the entanglement, lose the geometry: the geometry GENUINELY comes from entanglement.
#   (b) VOLUME-LAW (maximally-mixed / infinite-temperature) state: C = (1/2) I ⇒ block
#       entropy S(L) = L log 2 EXACTLY (extensive, volume) ⇒ the linear fit beats the log
#       fit ⇒ it FAILS the area law. This distinguishes the genuine area-law ground state
#       from a non-geometric (thermal / volume-law) state.
#
# all_pass iff (every clause MEASURED, none planted):
#   - block I(A,B) > 0 for the ground state and DECAYS monotonically with RING distance;
#   - d = -log I RECOVERS the block CYCLE (greedy NN walk on d returns the theta-cycle,
#     all steps +/-1 mod M), each path step is the nearest unused block;
#   - block entropy follows the AREA / Calabrese-Cardy log law on the ring, not a volume
#     law (chord-log-fit rmse < linear-in-L fit rmse for the critical ground state);
#   - PRODUCT-state control gives I=0 ⇒ no reconstructable geometry (kill fires);
#   - VOLUME-LAW control FAILS the area law (linear fit beats log fit; kill fires).
#
# HONEST SCOPE.
#   FORCED (standard physics, here only re-MEASURED):
#     * MI-distance d=-log I and the c/3 log (area/boundary) law of a critical 1D
#       free-fermion chain; the even-separation single-site sublattice vanishing.
#   NOVEL / INTERPRETIVE (explicitly bounded, NOT proven):
#     * Calling the reconstructed 1D chain "the S^3 foliation". It is a 1D PROXY of the
#       RADIAL direction of the nested tori, NOT the full S^3 geometry. The reconstruction
#       recovers a 1D ORDERED METRIC LINE, read out from entanglement; promoting that to
#       "emergent S^3 spacetime" is interpretive and is NOT claimed here.
#
# classification: PoC  ·  promotion_allowed: false
# tools (non-numpy, native Julia): LinearAlgebra, JSON.
# NO Z3 block: omitted deliberately. A decorative SMT tautology is this repo's recurring
# weakness; the load-bearing evidence here is the measured numbers and the kill-controls.
# run: julia --project="system_v5/julia_carrier" "system_v5/julia_carrier/layers/spacetime_from_entanglement_nested.jl"
# =====================================================================================

using LinearAlgebra
using JSON

# =====================================================================================
# Foliation geometry: leaf areas set the hopping modulation of the radial Dirac chain.
# =====================================================================================
analytic_area(θ) = 2π^2 * sin(2θ)          # area of leaf T^2(theta); FORCED standard invariant

"Leaf theta-grid on (0, pi/2), interior points (endpoints are degenerate cores)."
leaf_thetas(N::Int) = collect(range(0, π/2, length=N+2))[2:end-1]

"""
    foliation_ring_hamiltonian(N) -> (H, thetas, hoppings)

Tight-binding (radial Dirac) Hamiltonian on N leaf sites closed into a RING (periodic BC).
Nearest-leaf hopping is the inter-leaf kinetic term gamma^theta d/dtheta; its amplitude is
MODULATED by the foliation geometry,  t_i = sqrt(A(theta_i) A(theta_{i+1})) / A_max ∈ (0,1],
A_max = A(pi/4) (the Clifford torus). The wrap bond closes the two degenerate Hopf cores
(theta=0, theta=pi/2) onto one cycle. A genuine foliation-derived ring — still a 1D PROXY
of the radial direction (claim ceiling below).
"""
function foliation_ring_hamiltonian(N::Int)
    θ = leaf_thetas(N)
    A = analytic_area.(θ)
    Amax = analytic_area(π/4)
    H = zeros(Float64, N, N)
    hoppings = Float64[]
    for i in 1:N
        ip = i % N + 1                        # periodic: site N bonds back to site 1
        t = sqrt(A[i] * A[ip]) / Amax         # foliation-set hopping in (0,1]
        push!(hoppings, t)
        H[i, ip] -= t
        H[ip, i] -= t
    end
    return H, θ, hoppings
end

"Exact ground-state correlation matrix C_ij = sum over occupied (negative-energy) modes."
function ground_correlation(H::AbstractMatrix)
    F = eigen(Symmetric(Matrix(H)))
    occ = findall(<(-1e-12), F.values)        # half-filled Dirac sea: negative-energy modes
    U = F.vectors[:, occ]
    C = U * transpose(U)
    return Matrix(Symmetric(0.5 * (C + transpose(C)))), length(occ)
end

# =====================================================================================
# Peschel entanglement entropy from a correlation matrix.
# =====================================================================================
"von Neumann entropy of the reduced state on `sites`, from the restricted correlation matrix."
function block_entropy(C::AbstractMatrix, sites::AbstractVector{Int})
    isempty(sites) && return 0.0
    ev = eigvals(Hermitian(Matrix(C[sites, sites])))
    s = 0.0
    eps = 1e-13
    for raw in ev
        n = clamp(real(raw), eps, 1 - eps)
        s -= n * log(n) + (1 - n) * log(1 - n)
    end
    return s
end

"Mutual information I(A:B) = S(A)+S(B)-S(AB) between two disjoint site-sets."
function region_mutual_information(C::AbstractMatrix, A::AbstractVector{Int}, B::AbstractVector{Int})
    sa = block_entropy(C, A); sb = block_entropy(C, B)
    sab = block_entropy(C, vcat(A, B))
    return sa + sb - sab
end

# =====================================================================================
# Block partition of the chain into M contiguous leaf-regions (the emergent "points").
# =====================================================================================
"Partition 1..N into M contiguous blocks of (nearly) equal length; returns vector of site-sets."
function leaf_blocks(N::Int, M::Int)
    edges = round.(Int, range(0, N, length=M+1))
    return [collect(edges[k]+1:edges[k+1]) for k in 1:M]
end

# =====================================================================================
# NON-CIRCULAR geometry reconstruction from the entanglement distance d = -log I.
# =====================================================================================
"""
    block_distance_matrix(C, blocks) -> (D, I)

D[p,q] = -log I(block_p : block_q), the Van Raamsdonk emergent distance; D[p,p]=0. I[p,q]
is the raw mutual information. When I<=0 (or numerically ~0) the distance is +Inf (no link).
"""
function block_distance_matrix(C::AbstractMatrix, blocks::Vector{Vector{Int}})
    M = length(blocks)
    I = zeros(Float64, M, M)
    D = zeros(Float64, M, M)
    for p in 1:M, q in p+1:M
        mi = region_mutual_information(C, blocks[p], blocks[q])
        I[p, q] = mi; I[q, p] = mi
        d = mi > 1e-13 ? -log(mi) : Inf
        D[p, q] = d; D[q, p] = d
    end
    return D, I
end

"Ring (geodesic) distance between block positions on the M-cycle."
ring_distance(p::Int, q::Int, M::Int) = min(abs(p - q), M - abs(p - q))

"""
    reconstruct_order(D, start) -> order

Recover a CYCLIC ordering from the DISTANCE MATRIX ALONE — the block indices are never used
as input. Greedy nearest-neighbour walk: start anywhere, then repeatedly step to the nearest
unused block. For a genuine emergent cycle this returns the true block cycle (up to rotation
and reflection).
"""
function reconstruct_order(D::AbstractMatrix; start::Int=1)
    M = size(D, 1)
    order = [start]
    used = falses(M); used[start] = true
    for _ in 2:M
        cur = order[end]
        best = 0; bestd = Inf
        for j in 1:M
            (used[j] || j == cur) && continue
            if D[cur, j] < bestd
                bestd = D[cur, j]; best = j
            end
        end
        push!(order, best); used[best] = true
    end
    return order
end

"""
Cyclic-recovery score: is the recovered walk a clean cycle of the true block ring?
The recovered order is a permutation of 1..M; the emergent geometry is a CYCLE, so a genuine
recovery has every consecutive step (including the wrap from last back to first) differing by
+/-1 mod M. Returns the FRACTION of the M cyclic steps that are +/-1 mod M (1.0 = exact
cycle up to rotation/reflection).
"""
function cyclic_recovery_score(order::Vector{Int})
    M = length(order)
    good = 0
    for k in 1:M
        nxt = order[k % M + 1]
        d = mod(nxt - order[k], M)
        (d == 1 || d == M - 1) && (good += 1)
    end
    return good / M
end

# =====================================================================================
# Linear fit (for the area-vs-volume law).
# =====================================================================================
function fit_line(xs::Vector{Float64}, ys::Vector{Float64})
    n = length(xs)
    xbar = sum(xs) / n; ybar = sum(ys) / n
    denom = sum((x - xbar)^2 for x in xs)
    slope = sum((xs[i] - xbar) * (ys[i] - ybar) for i in 1:n) / denom
    intercept = ybar - slope * xbar
    rmse = sqrt(sum((ys[i] - (slope * xs[i] + intercept))^2 for i in 1:n) / n)
    return (slope=slope, intercept=intercept, rmse=rmse)
end

# =====================================================================================
# KILL-CONTROL states (built as correlation matrices, same downstream code path).
# =====================================================================================
"PRODUCT (unentangled) state: diagonal C; alternating empty/full ⇒ I=0 for all regions."
function product_correlation(N::Int)
    C = zeros(Float64, N, N)
    for i in 1:N
        C[i, i] = isodd(i) ? 1.0 : 0.0
    end
    return C
end

"VOLUME-LAW (maximally mixed / infinite-temperature) state: C = (1/2) I ⇒ S(L)=L log2 exactly."
volume_law_correlation(N::Int) = 0.5 * Matrix{Float64}(I, N, N)

# =====================================================================================
# RUN
# =====================================================================================
println("="^82)
println("SPACETIME FROM ENTANGLEMENT — nested-tori radial chain, NON-CIRCULAR reconstruction")
println("="^82)

results = Dict{String,Any}()
results["object"] = "spacetime_from_entanglement_nested"
results["classification"] = "PoC"
results["promotion_allowed"] = false
results["tools"] = ["LinearAlgebra", "JSON"]
results["z3_omitted"] = "deliberate: no decorative SMT block; evidence is measured numbers + kill-controls"

N = 48
M = 12                                  # number of contiguous leaf-blocks (emergent "points")
H, θ, hoppings = foliation_ring_hamiltonian(N)
C, nocc = ground_correlation(H)
blocks = leaf_blocks(N, M)
println("\n[setup] N=$N leaf sites (PERIODIC ring) in M=$M contiguous blocks; theta in (0,pi/2).")
println("        occupied modes (half-filled Dirac sea): $nocc")
println("        hopping range t_i ∈ [$(round(minimum(hoppings),digits=4)), $(round(maximum(hoppings),digits=4))]")
println("        block sizes: $([length(b) for b in blocks])")

# Measured sublattice fact (reported, not hidden): single-site MI vanishes on even sep.
mid = N ÷ 2
even_site_mi = [region_mutual_information(C, [mid], [mid + k]) for k in (2, 4, 6)]
odd_site_mi  = [region_mutual_information(C, [mid], [mid + k]) for k in (1, 3, 5)]
println("        sublattice fact: single-site I at even sep (2,4,6) = $(round.(even_site_mi, sigdigits=2)) (≈0); " *
        "odd sep (1,3,5) = $(round.(odd_site_mi, sigdigits=3))")

# -------------------------------------------------------------------------------------
# (1) Block mutual information vs RING distance
# -------------------------------------------------------------------------------------
println("\n[1] MUTUAL INFORMATION  I(A:B)  between leaf-BLOCKS vs RING distance (measured, ground state)")
ref = 1                                   # reference block (any block on the ring)
mi_rows = Vector{Dict{String,Any}}()
# average block MI grouped by ring distance from the reference block
mi_by_ringdist = Float64[]
println("    ring_dist   mean I(block$ref : block@dist)        d = -log I")
for rd in 1:(M ÷ 2)
    qs = [q for q in 1:M if q != ref && ring_distance(ref, q, M) == rd]
    mis = [region_mutual_information(C, blocks[ref], blocks[q]) for q in qs]
    meanI = sum(mis) / length(mis)
    push!(mi_by_ringdist, meanI)
    dval = meanI > 1e-13 ? -log(meanI) : nothing
    push!(mi_rows, Dict("ring_distance"=>rd, "ref"=>ref, "q_blocks"=>qs, "I_values"=>mis,
                        "mean_I"=>meanI, "d_minus_log_meanI"=>dval))
    println("    $(rpad(rd,11)) $(rpad(round(meanI, sigdigits=6),24)) $(dval===nothing ? "Inf" : round(dval,digits=4))")
end
all_mi_positive = all(>(1e-12), mi_by_ringdist)
mi_decays = all(mi_by_ringdist[k] >= mi_by_ringdist[k+1] - 1e-12 for k in 1:length(mi_by_ringdist)-1)
println("    all block I>0 (adjacent + distant blocks entangled) : $all_mi_positive")
println("    block I decays monotonically with RING distance      : $mi_decays")

# -------------------------------------------------------------------------------------
# (2) NON-CIRCULAR geometry reconstruction from d = -log I
# -------------------------------------------------------------------------------------
println("\n[2] RECONSTRUCT GEOMETRY  d(A,B) = -log I(A,B)  (Van Raamsdonk) — cycle read from d ALONE")
D, Imat = block_distance_matrix(C, blocks)
recovered = reconstruct_order(D)
score = cyclic_recovery_score(recovered)
order_recovered = score >= 0.999          # exact cycle (up to rotation/reflection)
# adjacency: along the recovered path each step is the nearest unused block
adj_close = let
    ok = true
    for k in 1:length(recovered)-1
        a = recovered[k]; later = recovered[k+1:end]
        dmin = minimum(D[a, c] for c in later)
        ok &= isapprox(D[a, recovered[k+1]], dmin; atol=1e-9)
    end
    ok
end
# emergent distance vs RECONSTRUCTED ring distance is monotone non-decreasing (ref=recovered[1])
recpos = zeros(Int, M); for (p, s) in enumerate(recovered); recpos[s] = p; end
ref_blk = recovered[1]
by_recring = Dict{Int,Vector{Float64}}()
for q in 1:M
    q == ref_blk && continue
    rd = ring_distance(1, recpos[q], M)     # ring distance in the RECONSTRUCTED coordinate
    push!(get!(by_recring, rd, Float64[]), Imat[ref_blk, q])
end
rec_means = [sum(by_recring[rd]) / length(by_recring[rd]) for rd in sort(collect(keys(by_recring)))]
rec_monotone = all(rec_means[k] >= rec_means[k+1] - 1e-12 for k in 1:length(rec_means)-1)
distance_monotone = rec_monotone
println("    recovered block cycle (greedy NN walk on d) : $recovered")
println("    cyclic-recovery score (1.0 = exact cycle, all steps ±1 mod M) : $(round(score,digits=4)) -> recovered : $order_recovered")
println("    along recovered path, each step is the nearest unused block   : $adj_close")
println("    block I monotone-decreasing in RECONSTRUCTED ring distance    : $distance_monotone")

# -------------------------------------------------------------------------------------
# (3) AREA LAW vs VOLUME LAW — block entropy scaling (Calabrese-Cardy on the ring)
# -------------------------------------------------------------------------------------
println("\n[3] AREA LAW  S(L) of a contiguous leaf-block — Calabrese-Cardy log law vs volume (linear)")
# On a ring S(L)=S(N-L); fit the rising half L<=N/2 against the chord variable
# x = log[(N/pi) sin(pi L / N)] (the standard CFT form) vs the volume variable L.
block_Ls = collect(4:2:(N ÷ 2))
S_block = [block_entropy(C, collect(1:L)) for L in block_Ls]
chord = [log((N / π) * sin(π * L / N)) for L in block_Ls]
logfit = fit_line(chord, S_block)                         # S ~ (c/3) x  (boundary/area)
linfit = fit_line([float(L) for L in block_Ls], S_block)  # S ~ slope*L  (volume)
area_law = logfit.rmse < linfit.rmse
fitted_c = 3.0 * logfit.slope
println("    chord-log fit  S ~ (c/3)·log[(N/π)sin(πL/N)] : slope=$(round(logfit.slope,digits=4)) rmse=$(round(logfit.rmse,digits=5)) (c≈$(round(fitted_c,digits=3)))")
println("    linear (volume) fit  S ~ slope·L             : slope=$(round(linfit.slope,digits=4)) rmse=$(round(linfit.rmse,digits=5))")
println("    AREA (Calabrese-Cardy log) law beats VOLUME (linear) law : $area_law")

# -------------------------------------------------------------------------------------
# (4) KILL-CONTROL (a): PRODUCT state ⇒ I=0 ⇒ no reconstructable geometry
# -------------------------------------------------------------------------------------
println("\n[4] KILL-CONTROL (a) PRODUCT (unentangled) state — geometry must VANISH")
Cp = product_correlation(N)
Dp, Ip = block_distance_matrix(Cp, blocks)
prod_max_I = maximum(Ip[p, q] for p in 1:M for q in p+1:M)
prod_all_dist_inf = all(!isfinite(Dp[p, q]) for p in 1:M for q in p+1:M)
prod_kill = prod_max_I < 1e-12 && prod_all_dist_inf
println("    max off-diagonal block I in product state : $(round(prod_max_I, sigdigits=3))  (≈0 ⇒ no links)")
println("    all reconstructed block distances +Inf (no geometry) : $prod_all_dist_inf")
println("    KILL fires (entanglement removed ⇒ geometry gone) : $prod_kill")

# -------------------------------------------------------------------------------------
# (5) KILL-CONTROL (b): VOLUME-LAW (maximally mixed) state ⇒ fails the area law
# -------------------------------------------------------------------------------------
println("\n[5] KILL-CONTROL (b) VOLUME-LAW (maximally mixed) state — must FAIL the area law")
Cv = volume_law_correlation(N)
S_block_v = [block_entropy(Cv, collect(1:L)) for L in block_Ls]
logfit_v = fit_line(chord, S_block_v)                          # same chord variable as the area test
linfit_v = fit_line([float(L) for L in block_Ls], S_block_v)   # volume variable
vol_fails_area = linfit_v.rmse < logfit_v.rmse   # linear (volume) fit wins ⇒ NOT area-law
vol_is_extensive = isapprox(linfit_v.slope, log(2); atol=1e-6)   # S = L log2 exactly
println("    volume-law block entropy: chord-log-rmse=$(round(logfit_v.rmse,digits=5)) lin-rmse=$(round(linfit_v.rmse,digits=8))")
println("    volume-law linear slope = $(round(linfit_v.slope,digits=6))  (== log2=$(round(log(2),digits=6)) ⇒ S=L log2 extensive : $vol_is_extensive)")
println("    KILL fires (volume state FAILS area law, linear fit wins) : $vol_fails_area")

# =====================================================================================
# VERDICTS
# =====================================================================================
checks = Dict(
    "block_mutual_information_all_positive" => all_mi_positive,
    "block_mi_decays_with_ring_distance"   => mi_decays,
    "geometry_cycle_recovered_from_d"      => order_recovered,
    "recovered_path_steps_nearest_block"   => adj_close,
    "distance_monotone_in_recon_ring"      => distance_monotone,
    "entropy_area_law_beats_volume"        => area_law,
    "kill_product_state_no_geometry"       => prod_kill,
    "kill_volume_law_fails_area_law"       => vol_fails_area,
)
all_pass = all(values(checks))

results["setup"] = Dict("N"=>N, "M_blocks"=>M, "boundary"=>"periodic_ring", "n_occupied"=>nocc,
    "thetas"=>θ, "hoppings"=>hoppings, "block_sizes"=>[length(b) for b in blocks],
    "A_min"=>minimum(analytic_area.(θ)), "A_max"=>analytic_area(π/4),
    "single_site_even_sep_MI"=>even_site_mi, "single_site_odd_sep_MI"=>odd_site_mi,
    "sublattice_note"=>"single-site I vanishes on EVEN separations (bipartite half-filled chain); regions are contiguous blocks")
results["block_mutual_information"] = Dict("rows_by_ring_distance"=>mi_rows, "all_positive"=>all_mi_positive,
    "decays_with_ring_distance"=>mi_decays)
results["reconstruction"] = Dict(
    "recovered_cycle"=>recovered, "cyclic_recovery_score"=>score,
    "cycle_recovered"=>order_recovered, "path_steps_nearest_block"=>adj_close,
    "block_I_monotone_in_reconstructed_ring_distance"=>distance_monotone,
    "note"=>"cycle recovered from d=-log I ALONE; block indices never used as reconstruction input; theta-cycle compared only afterward, up to rotation and reflection")
results["area_law"] = Dict(
    "block_lengths_half_ring"=>block_Ls, "S_block"=>S_block,
    "chord_variable_def"=>"x = log[(N/pi) sin(pi L / N)] (Calabrese-Cardy)",
    "chord_log_fit"=>Dict("slope"=>logfit.slope, "intercept"=>logfit.intercept, "rmse"=>logfit.rmse),
    "linear_volume_fit"=>Dict("slope"=>linfit.slope, "intercept"=>linfit.intercept, "rmse"=>linfit.rmse),
    "fitted_c_from_3logslope"=>fitted_c, "area_law_beats_volume"=>area_law)
results["kill_product_state"] = Dict("max_offdiag_block_I"=>prod_max_I,
    "all_distances_infinite"=>prod_all_dist_inf, "kill_fires"=>prod_kill)
results["kill_volume_law"] = Dict("S_block"=>S_block_v,
    "chord_log_rmse"=>logfit_v.rmse, "lin_rmse"=>linfit_v.rmse, "lin_slope"=>linfit_v.slope,
    "exactly_L_log2_extensive"=>vol_is_extensive, "fails_area_law"=>vol_fails_area)
results["checks"] = checks
results["all_pass"] = all_pass
results["status_ladder"] = "exists < runs < passes"
results["status"] = all_pass ? "passes" : "partial"
results["honest_scope"] = Dict(
    "forced_standard_physics" => [
        "MI-distance d = -log I (Van Raamsdonk) and the c/3 Calabrese-Cardy log (area/boundary) law of a critical 1D free-fermion ring — re-measured, not discovered",
        "even-separation single-site MI vanishing on the bipartite half-filled chain (sublattice / particle-hole structure)",
        "ring (geodesic) distance min(|p-q|,M-|p-q|) is the natural emergent distance on the periodic chain"],
    "novel_interpretive_NOT_proven" => [
        "calling the reconstructed 1D ring 'the S^3 foliation': it is a 1D PROXY of the RADIAL direction of the nested tori, NOT the full S^3 geometry; promoting the recovered 1D cyclic metric to 'emergent S^3 spacetime' is interpretive and is NOT claimed here"],
    "claim_ceiling" => "Reconstruction recovers a 1D CYCLIC METRIC (block cycle + relative ring distances) read out from entanglement, non-circularly. This is the radial proxy of the foliation, not full emergent spacetime.")

println("\n" * "="^82)
println("VERDICTS")
for k in sort(collect(keys(checks)))
    println("   $(rpad(k,40)) : $(checks[k] ? "PASS" : "FAIL")")
end
println("="^82)
println("ALL_PASS = $all_pass    STATUS = $(results["status"])   (classification=PoC, promotion_allowed=false)")
println("FORCED : d=-log I MI-distance ; c/3 Calabrese-Cardy log area-law of the critical ring")
println("NOVEL  : reconstructed 1D cyclic metric = RADIAL PROXY of the foliation, NOT full S^3 (claim ceiling)")
println("="^82)

outpath = joinpath(@__DIR__, "spacetime_from_entanglement_nested_results.json")
open(outpath, "w") do io
    JSON.print(io, results, 2)
end
println("\nwrote: $outpath")
