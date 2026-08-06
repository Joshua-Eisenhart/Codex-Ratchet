# Independent Julia re-derivation of the DECISIVE integer observables in D1, D2, D4, D5.
# Nothing here reads a Python result. Exact rank is a hand-written fraction-free
# elimination over Rational{BigInt} -- not sympy, not an SVD.
# D5 uses Octonions.jl / Quaternions.jl, whose multiplication tables are written by
# their own authors, so the associator is not re-derived from my Cayley-Dickson code.

using LinearAlgebra
using JSON
using Graphs
using Octonions
using Quaternions

popcnt(x::Int) = count_ones(x)

function exact_rank(M::Matrix{Rational{BigInt}})
    A = copy(M); nr, nc = size(A); r = 0
    for c in 1:nc
        p = 0
        for i in (r+1):nr
            if A[i, c] != 0; p = i; break; end
        end
        p == 0 && continue
        r += 1
        A[[r, p], :] = A[[p, r], :]
        for i in 1:nr
            if i != r && A[i, c] != 0
                A[i, :] -= (A[i, c] / A[r, c]) * A[r, :]
            end
        end
    end
    return r
end

# ---- D1: diagonal-only vs pair field on the SAME diagonal data -------------------
function d1()
    J = 0:15
    variants = Dict(
        "all_ones"         => [1 for j in J],
        "even_parity_only" => [popcnt(j) % 2 == 0 ? 1 : 0 for j in J],
        "all_zeros"        => [0 for j in J],
    )
    out = Dict{String,Any}()
    for (name, d) in variants
        for (label, keep) in (("rival_A_diagonal_only", false), ("rival_B_pair_field", true))
            M = zeros(Rational{BigInt}, 16, 16)
            for j in J, k in J
                if j == k
                    M[j+1, k+1] = d[j+1]
                elseif keep && popcnt(j ⊻ k) == 1
                    M[j+1, k+1] = 1
                end
            end
            supp = count(!=(0), M)
            entry = Dict{String,Any}(
                "support_cardinality" => supp,
                "exact_rank" => exact_rank(M),
                "exact_determinant" => string(det(Matrix{Rational{BigInt}}(M))),
            )
            if supp > 0
                entry["H0_pair_bits"] = log2(supp)   # ABSENT when the support is empty
            end
            out["$(name)__$(label)"] = entry
        end
    end
    return out
end

# ---- D2 / D4: graph and complex observables -------------------------------------
hypercube_edges(n) = sort(unique([Tuple(sort([j, j ⊻ (1 << b)])) for j in 0:(2^n-1) for b in 0:(n-1)]))
circulant_edges(nv, steps) = sort(unique([Tuple(sort([i, mod(i + s, nv)])) for i in 0:(nv-1) for s in steps]))
torus_idx(x, y, a, b) = mod(x, a) * b + mod(y, b)
torus_edges(a, b) = sort(unique(vcat(
    [Tuple(sort([torus_idx(x, y, a, b), torus_idx(x + 1, y, a, b)])) for x in 0:(a-1) for y in 0:(b-1)],
    [Tuple(sort([torus_idx(x, y, a, b), torus_idx(x, y + 1, a, b)])) for x in 0:(a-1) for y in 0:(b-1)])))
torus_faces(a, b) = [[torus_idx(x, y, a, b), torus_idx(x + 1, y, a, b),
                      torus_idx(x + 1, y + 1, a, b), torus_idx(x, y + 1, a, b)]
                     for x in 0:(a-1) for y in 0:(b-1)]

function cube_squares(n)
    F = Vector{Vector{Int}}()
    for b1 in 0:(n-1), b2 in (b1+1):(n-1)
        m = (1 << b1) | (1 << b2)
        for v in 0:(2^n-1)
            (v & m) == 0 || continue
            push!(F, [v, v ⊻ (1 << b1), v ⊻ m, v ⊻ (1 << b2)])
        end
    end
    return F
end

function octahedron()
    F = [[a, b, c] for a in (0, 1) for b in (2, 3) for c in (4, 5)]
    E = sort(unique([Tuple(sort([f[i], f[mod1(i + 1, 3)]])) for f in F for i in 1:3]))
    return 6, E, F
end

function graph_obs(nv, edges)
    g = SimpleGraph(nv)
    for (u, w) in edges; add_edge!(g, u + 1, w + 1); end
    A = zeros(BigInt, nv, nv)
    for (u, w) in edges; A[u+1, w+1] = 1; A[w+1, u+1] = 1; end
    P = Matrix{BigInt}(I, nv, nv)
    traces = BigInt[]
    for _ in 1:8
        P = P * A
        push!(traces, sum(P[i, i] for i in 1:nv))
    end
    degs = sort([degree(g, v) for v in vertices(g)], rev=true)
    sum_d2 = sum(BigInt(d)^2 for d in degs)
    m = length(edges)
    A3 = A * A * A
    tri = sum(A3[i, i] for i in 1:nv) ÷ 6
    c4 = (traces[4] - 2 * sum_d2 + 2 * m) ÷ 8
    return Dict(
        "vertices" => nv, "edges" => m,
        "degree_sequence" => degs,
        "is_bipartite" => Graphs.is_bipartite(g),
        "triangle_count" => string(tri),
        "four_cycle_count" => string(c4),
        "adjacency_power_traces_1_to_8" => string.(traces),
    )
end

function complex_obs(nv, edges, faces)
    pos = Dict(e => i for (i, e) in enumerate(edges))
    d1m = zeros(Rational{BigInt}, nv, length(edges))
    for (c, (u, w)) in enumerate(edges)
        d1m[u+1, c] -= 1; d1m[w+1, c] += 1
    end
    d2m = zeros(Rational{BigInt}, length(edges), length(faces))
    for (c, cyc) in enumerate(faces)
        L = length(cyc)
        for i in 1:L
            u, w = cyc[i], cyc[mod1(i + 1, L)]
            key = Tuple(sort([u, w]))
            d2m[pos[key], c] += (u < w ? 1 : -1)
        end
    end
    r1, r2 = exact_rank(d1m), exact_rank(d2m)
    comp = d1m * d2m
    return Dict(
        "vertices" => nv, "edges" => length(edges), "faces" => length(faces),
        "euler_characteristic_V_minus_E_plus_F" => nv - length(edges) + length(faces),
        "rank_boundary_1" => r1, "rank_boundary_2" => r2,
        "d1_d2_max_abs_entry" => string(maximum(abs.(comp), init=0//1)),
        "betti_0_over_Q" => nv - r1,
        "betti_1_over_Q" => (length(edges) - r1) - r2,
        "betti_2_over_Q" => length(faces) - r2,
    )
end

# ---- D5: associator and commutator from third-party algebra packages ------------
function d5()
    ounits = [octo(1, 0, 0, 0, 0, 0, 0, 0), octo(0, 1, 0, 0, 0, 0, 0, 0),
              octo(0, 0, 1, 0, 0, 0, 0, 0), octo(0, 0, 0, 1, 0, 0, 0, 0),
              octo(0, 0, 0, 0, 1, 0, 0, 0), octo(0, 0, 0, 0, 0, 1, 0, 0),
              octo(0, 0, 0, 0, 0, 0, 1, 0), octo(0, 0, 0, 0, 0, 0, 0, 1)]
    qunits = [quat(1, 0, 0, 0), quat(0, 1, 0, 0), quat(0, 0, 1, 0), quat(0, 0, 0, 1)]
    zo, zq = zero(ounits[1]), zero(qunits[1])

    function scan(units, z)
        nc = 0; na = 0; fc = nothing; fa = nothing
        for a in units, b in units
            c = a * b - b * a
            if c != z
                nc += 1
                fc === nothing && (fc = string(c))
            end
        end
        for a in units, b in units, c in units
            d = (a * b) * c - a * (b * c)
            if d != z
                na += 1
                fa === nothing && (fa = string(d))
            end
        end
        return nc, na, fc, fa
    end

    onc, ona, ofc, ofa = scan(ounits, zo)
    qnc, qna, qfc, qfa = scan(qunits, zq)

    # M2(Int): associative by construction; the associator is COMPUTED anyway.
    mu = [reshape([i == r && j == c ? 1 : 0 for r in 1:2 for c in 1:2], 2, 2)' |> Matrix
          for i in 1:2 for j in 1:2]
    mu = Matrix{Int}[]
    for i in 1:2, j in 1:2
        m = zeros(Int, 2, 2); m[i, j] = 1; push!(mu, m)
    end
    Z2 = zeros(Int, 2, 2)
    mnc = count(!=(Z2), [a * b - b * a for a in mu for b in mu])
    mna = count(!=(Z2), [(a * b) * c - a * (b * c) for a in mu for b in mu for c in mu])

    # Jordan product on symmetric 2x2 rationals: commutative, associator computed.
    jb = [Rational{BigInt}[1 0; 0 0], Rational{BigInt}[0 0; 0 1], Rational{BigInt}[0 1; 1 0]]
    ZJ = zeros(Rational{BigInt}, 2, 2)
    jm(a, b) = (a * b + b * a) // 2
    jnc = count(!=(ZJ), [jm(a, b) - jm(b, a) for a in jb for b in jb])
    jna = count(!=(ZJ), [jm(jm(a, b), c) - jm(a, jm(b, c)) for a in jb for b in jb for c in jb])

    return Dict(
        "octonions_Octonions_jl" => Dict(
            "nonzero_commutator_witness_count" => onc,
            "nonzero_associator_witness_count" => ona,
            "basis_pairs_tested" => 64, "basis_triples_tested" => 512,
            "first_nonzero_commutator" => ofc, "first_nonzero_associator" => ofa),
        "quaternions_Quaternions_jl" => Dict(
            "nonzero_commutator_witness_count" => qnc,
            "nonzero_associator_witness_count" => qna,
            "basis_pairs_tested" => 16, "basis_triples_tested" => 64,
            "first_nonzero_commutator" => qfc, "first_nonzero_associator" => qfa),
        "M2_Int_matrix_units" => Dict(
            "nonzero_commutator_witness_count" => mnc,
            "nonzero_associator_witness_count" => mna,
            "basis_pairs_tested" => 16, "basis_triples_tested" => 64),
        "jordan_symmetric_2x2" => Dict(
            "nonzero_commutator_witness_count" => jnc,
            "nonzero_associator_witness_count" => jna,
            "basis_pairs_tested" => 9, "basis_triples_tested" => 27),
    )
end

q4 = hypercube_edges(4)
sv, se, sf = octahedron()
result = Dict(
    "lane" => "julia",
    "julia_version" => string(VERSION),
    "d1_root_support" => d1(),
    "d2_one_skeleton" => Dict(
        "A_cubical_4cube_1skeleton" => graph_obs(16, q4),
        "B_circulant_C16_1_2" => graph_obs(16, circulant_edges(16, (1, 2))),
        "B_circulant_C16_1_3" => graph_obs(16, circulant_edges(16, (1, 3))),
        "B_torus_grid_C4_box_C4" => graph_obs(16, torus_edges(4, 4)),
    ),
    "d2_two_cell_level" => Dict(
        "cubical_4cube_2skeleton_24_squares" => complex_obs(16, q4, cube_squares(4)),
        "torus_C4_box_C4_16_quads" => complex_obs(16, torus_edges(4, 4), torus_faces(4, 4)),
    ),
    "d4_sphere_vs_torus" => Dict(
        "finite_S2_octahedron" => complex_obs(sv, se, sf),
        "finite_T2_C4_box_C4_quads" => complex_obs(16, torus_edges(4, 4), torus_faces(4, 4)),
    ),
    "d5_algebra" => d5(),
)

here = dirname(abspath(@__FILE__))
path = joinpath(here, "results", "lane_julia.json")
open(path, "w") do io
    JSON.print(io, result, 1)
end
println(JSON.json(result, 1))
println(stderr, "WROTE $path")
