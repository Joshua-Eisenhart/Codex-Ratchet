# =====================================================================
# L0_path_quotient  —  GENUINE isolated Julia sim
# =====================================================================
# L0 = response / effect / PATH QUOTIENT.
#
# OBJECT
#   Carrier: a finite single-qubit register (Hilbert space C^2).
#   Operation paths S: all gate-sequences of bounded length drawn from a
#     finite generator set G (the single-qubit Clifford generators H, S).
#   Each path p maps a fixed input state rho_in -> rho_out(p) = U(p) rho_in U(p)'.
#   A "response probe" M is a CPTP read-out applied to rho_out(p). Two paths
#     p ~_M q  iff  the probe cannot distinguish their outputs to tolerance:
#     d_M(p,q) <= tol, where d_M is the distance between the probe-image
#     densities.   The quotient S/~_M is built by clustering on MEASURED
#     probe images, never by assigning a class to a path.
#
# WHY THIS IS NON-CIRCULAR (anchored to a KNOWN invariant)
#   Under a FAITHFUL probe (full state tomography on a maximally-informative
#   input ensemble), p ~ q  iff  U(p) = U(q) up to global phase. The set of
#   distinct single-qubit Clifford unitaries (mod global phase) is the
#   single-qubit Clifford group C_1, whose order in PU(2) is the KNOWN
#   integer 24. So the measured class count under the faithful probe MUST
#   equal 24 — a number fixed by group theory, NOT by this sim. If the sim
#   measured anything else, it would be WRONG, not "by construction right".
#
# CONTROLS
#   positive : faithful probe -> class count == 24 (the known invariant).
#   boundary : single-observable probe (measure <Z> only on one input) ->
#              strictly COARSER than faithful (fewer classes), strictly
#              FINER than trivial (more than one class).  Read out, not set.
#   negative : a path NOT in the generator span (a non-Clifford T gate path)
#              lands in a NEW faithful class not equal to any Clifford class.
#   KILL-CONTROL : TRIVIAL probe (depolarize-to-fixed-output channel) maps
#              every path to the SAME density -> exactly 1 class. If the
#              faithful probe ALSO gave 1 class (or gave 24 trivially) the
#              result would be an artifact. The kill-control PASSES only by
#              collapsing, and the faithful probe must NOT collapse.
#   anti-self-check: we additionally verify class count is invariant to tol
#              over a range, and that random relabeling of probe outputs
#              destroys the 24 (rate-matched-random control).
# =====================================================================

using LinearAlgebra
using Random
using JSON

const TOL = 1e-6

# ---------- single-qubit gates (2x2 complex) ----------
const I2 = ComplexF64[1 0; 0 1]
const H  = (1/sqrt(2)) * ComplexF64[1 1; 1 -1]
const S  = ComplexF64[1 0; 0 im]
const T  = ComplexF64[1 0; 0 exp(im*pi/4)]          # non-Clifford
const X  = ComplexF64[0 1; 1 0]
const Z  = ComplexF64[1 0; 0 -1]
const Y  = ComplexF64[0 -im; im 0]

# A path is a sequence of gate symbols; U(path) = product (left-applied).
function path_unitary(path::Vector{Symbol}, gates::Dict{Symbol,Matrix{ComplexF64}})
    U = Matrix{ComplexF64}(I, 2, 2)
    for g in path
        U = gates[g] * U
    end
    return U
end

# Enumerate all paths over generators of length 0..maxlen.
function enumerate_paths(generators::Vector{Symbol}, maxlen::Int)
    paths = Vector{Vector{Symbol}}()
    push!(paths, Symbol[])                    # empty path = identity
    frontier = [Symbol[]]
    for _ in 1:maxlen
        newfrontier = Vector{Vector{Symbol}}()
        for p in frontier, g in generators
            q = vcat(p, g)
            push!(paths, q)
            push!(newfrontier, q)
        end
        frontier = newfrontier
    end
    return paths
end

# ---------- response probes ----------
# A probe is a function: U (2x2 unitary) -> feature vector (Vector{Float64}).
# Two paths are ~_M iff their feature vectors agree to TOL.

# Fixed informationally-complete input ensemble: the 6 Pauli eigenstates.
const PAULI_STATES = let
    plus  = ComplexF64[1, 1]/sqrt(2)
    minus = ComplexF64[1,-1]/sqrt(2)
    iplus = ComplexF64[1, im]/sqrt(2)
    iminus= ComplexF64[1,-im]/sqrt(2)
    zup   = ComplexF64[1, 0]
    zdn   = ComplexF64[0, 1]
    [zup, zdn, plus, minus, iplus, iminus]
end

dm(psi) = psi * psi'                                   # density matrix of pure state

# FAITHFUL probe: full tomography. Feature = expectation of X,Y,Z on each of
# the 6 input states after applying U. This is informationally complete:
# it distinguishes U from V (mod global phase) iff they differ as channels.
function probe_faithful(U)::Vector{Float64}
    feats = Float64[]
    for psi in PAULI_STATES
        rho = U * dm(psi) * U'
        push!(feats, real(tr(rho * X)))
        push!(feats, real(tr(rho * Y)))
        push!(feats, real(tr(rho * Z)))
    end
    return feats
end

# BOUNDARY probe: a single observable <Z> measured on a single input |0>.
# Strictly less informative than faithful.
function probe_single_obs(U)::Vector{Float64}
    rho = U * dm(PAULI_STATES[1]) * U'                 # input |0>
    return Float64[real(tr(rho * Z))]
end

# TRIVIAL probe (KILL-CONTROL): the probe response is constant — it discards
# the output entirely (models a completely-depolarizing read-out: every path
# yields the maximally mixed image). Feature vector is the same for all paths.
function probe_trivial(U)::Vector{Float64}
    return Float64[0.0]                                # constant: zero info
end

# ---------- quotient construction (MEASURED, not assigned) ----------
# Cluster paths by L-inf distance of their probe-feature vectors <= tol.
# Greedy union-find over measured features. Returns (nclasses, labels, reps).
function build_quotient(paths, features::Vector{Vector{Float64}}; tol=TOL)
    n = length(paths)
    label = fill(0, n)
    reps = Vector{Vector{Float64}}()       # one representative feature per class
    nclass = 0
    for i in 1:n
        assigned = 0
        for (c, r) in enumerate(reps)
            if maximum(abs.(features[i] .- r)) <= tol
                assigned = c
                break
            end
        end
        if assigned == 0
            nclass += 1
            push!(reps, features[i])
            label[i] = nclass
        else
            label[i] = assigned
        end
    end
    return nclass, label, reps
end

# ---------- run ----------
function main()
    Random.seed!(20260601)
    gates = Dict{Symbol,Matrix{ComplexF64}}(
        :H=>H, :S=>S, :T=>T, :I=>I2)
    generators = [:H, :S]                  # Clifford generators
    maxlen = 7                             # enough to realize all 24 Cliffords
    paths = enumerate_paths(generators, maxlen)
    npaths = length(paths)

    Us = [path_unitary(p, gates) for p in paths]

    # measured feature vectors under each probe
    feat_faithful = [probe_faithful(U)   for U in Us]
    feat_single   = [probe_single_obs(U) for U in Us]
    feat_trivial  = [probe_trivial(U)    for U in Us]

    nc_faithful, lab_faithful, _ = build_quotient(paths, feat_faithful)
    nc_single,   lab_single,   _ = build_quotient(paths, feat_single)
    nc_trivial,  lab_trivial,  _ = build_quotient(paths, feat_trivial)

    # ---- KNOWN INVARIANT CHECK ----
    # single-qubit Clifford group order (mod global phase) = 24.
    KNOWN_CLIFFORD_ORDER = 24
    positive_pass = (nc_faithful == KNOWN_CLIFFORD_ORDER)

    # ---- boundary: strictly between trivial and faithful ----
    boundary_pass = (nc_single > nc_trivial) && (nc_single < nc_faithful)

    # ---- kill-control: trivial probe collapses to exactly 1 class ----
    kill_pass = (nc_trivial == 1) && (nc_faithful > 1)

    # ---- negative control: a non-Clifford T path is a NEW faithful class ----
    # Build a T-containing path and check its faithful feature is not within
    # tol of ANY Clifford-path representative.
    tpath = [:H, :T, :H]
    Ut = path_unitary(tpath, gates)
    ft = probe_faithful(Ut)
    # rebuild faithful reps
    _, _, faithful_reps = build_quotient(paths, feat_faithful)
    min_dist_to_clifford = minimum(maximum(abs.(ft .- r)) for r in faithful_reps)
    negative_pass = (min_dist_to_clifford > TOL)        # T is genuinely outside

    # ---- tol-robustness: faithful class count stable across tol scales ----
    tol_scan = [1e-9, 1e-8, 1e-7, 1e-6, 1e-5]
    counts_scan = [build_quotient(paths, feat_faithful; tol=t)[1] for t in tol_scan]
    tol_stable = all(c == KNOWN_CLIFFORD_ORDER for c in counts_scan)

    # ---- rate-matched-random control (anti-artifact) ----
    # If we shuffle the measured feature vectors across paths (destroying the
    # path->feature correspondence) the structure is gone; the class count of
    # the SHUFFLED features is still 24 (it's the same multiset of features),
    # BUT the per-path LABELS no longer respect group structure. The real test:
    # replace features with random vectors of the same dimension -> classes
    # should explode toward npaths (all distinct), proving 24 is not generic.
    rand_feats = [randn(length(feat_faithful[1])) for _ in 1:npaths]
    nc_random, _, _ = build_quotient(paths, rand_feats)
    random_control_distinct = (nc_random == npaths)     # random => all distinct
    # and: a constant feature => 1 class (sanity on clustering primitive)
    const_feats = [zeros(length(feat_faithful[1])) for _ in 1:npaths]
    nc_const, _, _ = build_quotient(paths, const_feats)
    cluster_primitive_ok = (nc_const == 1)

    # ---- class table (faithful) : class -> list of path strings ----
    classtab = Dict{Int,Vector{String}}()
    for (i, p) in enumerate(paths)
        c = lab_faithful[i]
        s = isempty(p) ? "I" : join(string.(p), "")
        push!(get!(classtab, c, String[]), s)
    end
    # compact table: class id, size, shortest representative
    class_table = [Dict("class"=>c,
                        "size"=>length(members),
                        "shortest_word"=>members[argmin(length.(members))])
                   for (c, members) in sort(collect(classtab); by=first)]

    all_pass = positive_pass && boundary_pass && kill_pass &&
               negative_pass && tol_stable && random_control_distinct &&
               cluster_primitive_ok

    results = Dict(
        "item" => "L0_path_quotient",
        "classification" => "PoC",
        "promotion_allowed" => false,
        "carrier" => "single-qubit (C^2)",
        "generators" => ["H","S"],
        "max_path_length" => maxlen,
        "S_size_total_paths" => npaths,
        "known_invariant" => Dict(
            "name" => "single-qubit Clifford group order (mod global phase)",
            "value" => 24,
            "source" => "group theory (Clifford C_1 in PU(2))"),
        "measured" => Dict(
            "classes_faithful_probe" => nc_faithful,
            "classes_single_obs_probe" => nc_single,
            "classes_trivial_probe" => nc_trivial,
            "classes_random_features" => nc_random,
            "classes_constant_features" => nc_const),
        "controls" => Dict(
            "positive_faithful_eq_24" => positive_pass,
            "boundary_single_between_trivial_and_faithful" => boundary_pass,
            "kill_control_trivial_collapses_to_1" => kill_pass,
            "negative_nonClifford_T_is_new_class" => negative_pass,
            "tol_robust_24_stable" => tol_stable,
            "rate_matched_random_all_distinct" => random_control_distinct,
            "cluster_primitive_const_eq_1" => cluster_primitive_ok),
        "diagnostics" => Dict(
            "tol" => TOL,
            "tol_scan" => tol_scan,
            "counts_scan" => counts_scan,
            "T_path_min_dist_to_clifford" => min_dist_to_clifford),
        "class_table_faithful" => class_table,
        "all_pass" => all_pass,
        "status_ladder" => "exists < runs < passes",
        "honest_note" =>
          "Class count 24 is READ OUT from measured probe indistinguishability " *
          "and CHECKED against the independently-known Clifford order 24; it is " *
          "not assigned. Trivial probe collapses to 1 (kill-control), single-obs " *
          "probe is strictly intermediate, random features give all-distinct.")

    open(joinpath(@__DIR__, "l0_path_quotient_results.json"), "w") do io
        JSON.print(io, results, 2)
    end

    println("=== L0_path_quotient ===")
    println("total paths |S|                 = ", npaths)
    println("classes (faithful probe)        = ", nc_faithful, "  [known invariant = 24]")
    println("classes (single-observable)     = ", nc_single)
    println("classes (trivial probe / KILL)  = ", nc_trivial)
    println("classes (random features ctrl)  = ", nc_random, "  [== |S| means generic]")
    println("classes (constant features)     = ", nc_const)
    println("--- controls ---")
    println("positive  faithful==24          : ", positive_pass)
    println("boundary  trivial<single<faith  : ", boundary_pass, "  (", nc_trivial, " < ", nc_single, " < ", nc_faithful, ")")
    println("KILL      trivial collapses->1  : ", kill_pass)
    println("negative  T path is new class   : ", negative_pass, "  (dist=", round(min_dist_to_clifford, digits=4), ")")
    println("tol-robust 24 stable over scan  : ", tol_stable, "  ", counts_scan)
    println("random-feat all distinct        : ", random_control_distinct)
    println("cluster prim const==1           : ", cluster_primitive_ok)
    println("ALL_PASS                        = ", all_pass)
    return all_pass
end

main()
