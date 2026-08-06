#!/usr/bin/env julia
# Probe lane 2 — Julia leg. R0, R1, R2, R3, C1-C3 on the root strata, n = 4.
#
# usage: julia --startup-file=no lane_julia.jl {float32|float64}
#
# Deliberately NOT a transcription of either python leg:
#   popcount  : Base.count_ones
#   COHERENT  : built TWICE — once from count_ones, once as I + adjacency_matrix of
#               Graphs.grid([2,2,2,2]) — and the two constructions are compared on
#               invariants inside this lane.
#   det       : computed over Rational{BigInt} as well as in float, so this lane can
#               produce the EXACT integer determinant the float lanes cannot.
# Method provenance is recorded with `which`, so the receipt names the actual method
# each call resolved to rather than asserting a library was used.
#
# This lane reads NO other lane's output.

using LinearAlgebra
using Graphs
using JSON

const N = 4
const SIZE = 2^N
const MODE = length(ARGS) >= 1 ? ARGS[1] : "float32"
MODE in ("float32", "float64") || (println("unknown float mode $MODE"); exit(2))
const FT = MODE == "float64" ? Float64 : Float32
const HERE = dirname(abspath(@__FILE__))
const OUT = joinpath(HERE, "results", "lane_julia_$(MODE).json")

const LOG2_CALLS = Ref(0)
jlog2(x) = (LOG2_CALLS[] += 1; Float64(log2(FT(x))))

bit(j, i) = (j >> i) & 1

function pair_field(kind)
    F = zeros(Int, SIZE, SIZE)
    for j in 0:SIZE-1, k in 0:SIZE-1
        v = kind == "DIAG" ? (j == k ? 1 : 0) : (count_ones(xor(j, k)) <= 1 ? 1 : 0)
        F[j+1, k+1] = v
    end
    F
end

function invariants(F)
    Ff = FT.(F)
    Dict{String,Any}(
        "support_cardinality" => count(!iszero, F),
        "trace" => Int(tr(F)),
        "float_determinant" => Float64(det(Ff)),
        "exact_determinant_over_rationals" => string(det(Rational{BigInt}.(F))),
        "float_rank" => rank(Ff),
        "eigenvalues_sorted" => Float64.(sort(eigvals(Symmetric(Ff)))),
    )
end

# ------------------------------------------------------------------ R2 structure
function all_cells()
    out = Vector{NTuple{N,Int}}()          # 2 encodes '*'
    function rec(pref)
        if length(pref) == N
            push!(out, Tuple(pref)); return
        end
        for s in (0, 1, 2)
            rec(vcat(pref, s))
        end
    end
    rec(Int[])
    out
end

celldim(c) = count(==(2), c)

function boundary_matrices(bydim, index)
    mats = Dict{Int,Matrix{Int}}()
    for d in 1:N
        src, dst = bydim[d], bydim[d-1]
        M = zeros(Int, length(dst), length(src))
        for (jc, c) in enumerate(src)
            free = [i for i in 1:N if c[i] == 2]
            for (m, i) in enumerate(free)
                sgn = isodd(m) ? -1 : 1
                for (v, vs) in ((1, 1), (0, -1))
                    face = collect(c); face[i] = v
                    M[index[d-1][Tuple(face)], jc] += sgn * vs
                end
            end
        end
        mats[d] = M
    end
    mats
end

function release(u, members)
    d = Dict{String,Any}("quotient_class_id" => u,
                         "probe_family" => ["p_popcount"],
                         "constraint_set_ref" => "C0 = identity constraint (E_C = E)",
                         "fibre_cardinality" => length(members),
                         "fibre_members" => members)
    if length(members) >= 1
        d["kappa_ext_bits"] = jlog2(length(members))
    end
    d
end

function main()
    t0 = time()
    mkpath(dirname(OUT))
    J = collect(0:SIZE-1)

    # ---- R0
    r0 = Dict{String,Any}("index_set" => "J_4 = {0,1}^4 as Int 0..15",
                          "alphabet" => "binary", "n_bits" => N,
                          "cardinality" => length(J),
                          "distinct_addresses_measured" => length(unique(J)),
                          "bits_matrix_row_sums" => [sum(bit(j, i) for i in 0:N-1) for j in J])
    r0["H0_addr_bits"] = jlog2(length(J))

    # ---- R1, two constructions of COHERENT
    r1 = Dict{String,Any}()
    for kind in ("DIAG", "COHERENT")
        F = pair_field(kind)
        inv = invariants(F)
        inv["index_set_ref"] = "R0.J_4"
        inv["omega_cardinality"] = length(F)
        inv["H0_pair_bits"] = jlog2(inv["support_cardinality"])
        r1[kind] = inv
    end
    g = Graphs.grid([2, 2, 2, 2])
    Mg = Matrix{Int}(Graphs.adjacency_matrix(g)) + I
    invg = invariants(Mg)
    invg["graph_nv"] = nv(g)
    invg["graph_ne"] = ne(g)
    invg["H0_pair_bits"] = jlog2(invg["support_cardinality"])
    r1["COHERENT_from_Graphs_grid"] = invg
    r1["independent_construction_agreement"] = Dict{String,Any}(
        k => Dict{String,Any}("count_ones" => r1["COHERENT"][k], "graphs_grid" => invg[k],
                              "equal" => r1["COHERENT"][k] == invg[k])
        for k in ("support_cardinality", "trace", "exact_determinant_over_rationals",
                  "float_rank", "H0_pair_bits", "eigenvalues_sorted"))

    disc = Dict{String,Any}()
    for k in ("support_cardinality", "H0_pair_bits", "float_rank",
              "float_determinant", "exact_determinant_over_rationals", "trace")
        disc[k] = Dict{String,Any}("DIAG" => r1["DIAG"][k], "COHERENT" => r1["COHERENT"][k],
                                   "separates" => r1["DIAG"][k] != r1["COHERENT"][k])
    end
    disc["H0_addr_bits"] = Dict{String,Any}("DIAG" => r0["H0_addr_bits"],
                                            "COHERENT" => r0["H0_addr_bits"],
                                            "separates" => false)
    disc["log2_float_rank"] = Dict{String,Any}(
        "DIAG" => jlog2(r1["DIAG"]["float_rank"]),
        "COHERENT" => jlog2(r1["COHERENT"]["float_rank"]),
        "separates" => r1["DIAG"]["float_rank"] != r1["COHERENT"]["float_rank"])
    r1["discrimination"] = disc

    # ---- R2
    K = all_cells()
    bydim = Dict(d => [c for c in K if celldim(c) == d] for d in 0:N)
    index = Dict(d => Dict(c => i for (i, c) in enumerate(bydim[d])) for d in 0:N)
    mats = boundary_matrices(bydim, index)
    comp = Dict{String,Any}()
    for d in 2:N
        P = mats[d-1] * mats[d]
        comp["d$(d-1)_o_d$(d)"] = Dict{String,Any}("shape" => [size(P)...],
                                                   "max_abs_entry" => maximum(abs.(P)),
                                                   "eltype" => string(eltype(P)))
    end
    r2 = Dict{String,Any}("cell_counts_by_dim" => Dict(string(d) => length(bydim[d]) for d in 0:N),
                          "total_cells" => length(K),
                          "boundary_matrix_shapes" => Dict("d$d" => [size(mats[d])...] for d in 1:N),
                          "boundary_composition" => comp)

    # ---- R3 : matmul + elementwise contraction over all 81 cells
    Kord = vcat([bydim[d] for d in 0:N]...)
    inside = zeros(Int, length(Kord), SIZE)
    for (ci, c) in enumerate(Kord), j in J
        inside[ci, j+1] = all(c[i] == 2 || bit(j, i - 1) == c[i] for i in 1:N) ? 1 : 0
    end
    pcok = [count_ones(xor(j, k)) <= 1 ? 1 : 0 for j in J, k in J]
    ones_full = ones(Int, SIZE, SIZE)
    rest = vec(sum((inside * pcok) .* inside, dims=2))
    full = vec(sum((ones(Int, length(Kord), SIZE) * ones_full) .* ones(Int, length(Kord), SIZE), dims=2))
    insize = vec(sum(inside, dims=2))
    perfull, perrest, perin = Dict{String,Set{Int}}(), Dict{String,Set{Int}}(), Dict{String,Set{Int}}()
    for (ci, c) in enumerate(Kord)
        k = string(celldim(c))
        push!(get!(perfull, k, Set{Int}()), full[ci])
        push!(get!(perrest, k, Set{Int}()), rest[ci])
        push!(get!(perin, k, Set{Int}()), insize[ci])
    end
    function fold(m)
        out = Dict{String,Any}()
        for k in sort(collect(keys(m)))
            length(m[k]) == 1 || (println("non-uniform |R_c| within dim $k: $(m[k])"); exit(1))
            card = first(m[k])
            out[k] = Dict{String,Any}("relation_cardinality" => card, "kappa_bits" => jlog2(card))
        end
        out
    end
    r3 = Dict{String,Any}("projection_ref" => "pi : E -> K, cell label over {0,1,*}^4",
                          "subcube_sizes_by_dim" => Dict(k => sort(collect(v)) for (k, v) in perin),
                          "FULL_FIELD" => Dict{String,Any}("per_dim" => fold(perfull),
                                                           "E_cardinality" => sum(full)),
                          "RESTRICTED" => Dict{String,Any}("per_dim" => fold(perrest),
                                                           "E_cardinality" => sum(rest)))

    # ---- C1-C3
    q = [count_ones(j) for j in J]
    counts = [count(==(u), q) for u in 0:N+1]
    members = Dict(u => [j for j in J if count_ones(j) == u] for u in 0:N+1)
    before = LOG2_CALLS[]
    rel = Dict(string(u) => release(u, members[u]) for u in 0:N)
    empty = release(5, members[5])
    after = LOG2_CALLS[]
    c123 = Dict{String,Any}(
        "quotient" => "q(j) = Base.count_ones(j), Q = {0,1,2,3,4}",
        "probe_family" => ["p_popcount"],
        "fibre_cardinalities" => Dict(string(u) => counts[u+1] for u in 0:N),
        "fibre_cardinality_sum" => sum(counts[1:N+1]),
        "kappa_ext_bits" => Dict(string(u) => rel[string(u)]["kappa_ext_bits"] for u in 0:N),
        "releases" => rel,
        "empty_fibre_case" => Dict{String,Any}("quotient_value_probed" => 5,
                                               "engine_measured_count" => counts[N+2],
                                               "descriptor" => empty,
                                               "descriptor_keys" => sort(collect(keys(empty))),
                                               "kappa_key_present" => haskey(empty, "kappa_ext_bits")),
        "log2_calls_across_5_nonempty_and_1_empty_release" => after - before)

    prov = Dict{String,Any}(
        "det_float" => string(which(det, Tuple{Matrix{FT}})),
        "det_rational" => string(which(det, Tuple{Matrix{Rational{BigInt}}})),
        "rank" => string(which(rank, Tuple{Matrix{FT}})),
        "eigvals" => string(which(eigvals, Tuple{Symmetric{FT,Matrix{FT}}})),
        "tr" => string(which(tr, Tuple{Matrix{Int}})),
        "count_ones" => string(which(count_ones, Tuple{Int})),
        "matmul_int" => string(which(*, Tuple{Matrix{Int},Matrix{Int}})),
        "adjacency_matrix" => string(which(Graphs.adjacency_matrix, Tuple{Graphs.SimpleGraph{Int}})),
        "grid" => string(which(Graphs.grid, Tuple{Vector{Int}})),
        "log2" => string(which(log2, Tuple{FT})),
    )

    rec = Dict{String,Any}(
        "lane" => "julia_$(MODE)", "engine" => "julia",
        "julia_version" => string(VERSION),
        "julia_binary" => Base.julia_cmd()[1],
        "active_project" => Base.active_project(),
        "requested_float_mode" => MODE,
        "measured_float_type" => string(FT),
        "measured_log2_output_type" => string(typeof(log2(FT(80)))),
        "engine_method_provenance_from_which" => prov,
        "loaded_modules" => sort([string(m) for m in values(Base.loaded_modules)]),
        "n" => N, "R0" => r0, "R1" => r1, "R2" => r2, "R3" => r3, "C1_C3" => c123,
        "log2_calls_total" => LOG2_CALLS[],
        "wallclock_s" => round(time() - t0, digits=3))
    open(OUT, "w") do fh
        JSON.print(fh, rec, 1)
    end
    println(JSON.json(Dict("wrote" => OUT, "mode" => MODE,
                           "measured_log2_output_type" => rec["measured_log2_output_type"],
                           "exact_det_coherent" => r1["COHERENT"]["exact_determinant_over_rationals"],
                           "graphs_agreement" => Dict(k => v["equal"] for (k, v) in r1["independent_construction_agreement"]),
                           "wallclock_s" => rec["wallclock_s"]), 1))
    return 0
end

exit(main())
