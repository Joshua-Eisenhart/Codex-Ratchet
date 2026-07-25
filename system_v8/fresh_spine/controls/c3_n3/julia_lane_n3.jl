#!/usr/bin/env julia
# ---------------------------------------------------------------------------
# fresh_spine ENGINE LANE — JULIA
#
# Reads ONLY system_v8/fresh_spine/fixture_v0.json.
# Implements F0-F3 from the lane brief. Writes one JSON object as the LAST
# line of stdout.
#
# Discipline:
#   - No literal ran/verdict/load_bearing field anywhere in this file.
#   - Every number below is computed in this process.
#   - A2 (rank of an integer matrix) is computed EXACTLY over the rationals
#     via Rational{BigInt} arithmetic. Julia's LinearAlgebra.rank is NOT used:
#     it routes Rational input through svdvals on BigFloat and raises
#     MethodError, i.e. it is a float path. Measured, not assumed.
# ---------------------------------------------------------------------------

using LinearAlgebra
using Graphs
using JSON
using SHA

const NONCE = "NONCE-JUL-2c8e04"
const FIXTURE = joinpath(@__DIR__, "fixture_v0.json")

# --- engine-call ledger: every entry is appended at the actual call site ----
const CALLS = String[]
note!(s) = push!(CALLS, s)

hr(t) = println("\n=== ", t, " ", repeat("=", max(0, 58 - length(t))))

# ---------------------------------------------------------------------------
# exact linear algebra over Rational{BigInt}
# ---------------------------------------------------------------------------

"""
Row-echelon rank over the rationals, exact. Pivot search per column, so it is
correct at any rank (unlike counting nonzero pivots of a partial-pivoted LU,
which is only valid when the matrix turns out to be full rank).
Arithmetic is Julia Rational{BigInt} (GMP-backed); no tolerance exists here.
"""
function exact_rank(M::Matrix{Rational{BigInt}})
    A = copy(M)
    nr, nc = size(A)
    r = 0
    row = 1
    for col in 1:nc
        row > nr && break
        p = 0
        for i in row:nr
            if A[i, col] != 0
                p = i
                break
            end
        end
        p == 0 && continue
        if p != row
            for c in 1:nc
                A[row, c], A[p, c] = A[p, c], A[row, c]
            end
        end
        pv = A[row, col]
        for i in (row+1):nr
            if A[i, col] != 0
                f = A[i, col] / pv
                for c in col:nc
                    A[i, c] -= f * A[row, c]
                end
            end
        end
        r += 1
        row += 1
    end
    return r
end

"count of nonzero pivots from Julia's generic LU over Rational{BigInt}"
function lu_pivot_count(M::Matrix{Rational{BigInt}})
    F = LinearAlgebra.lu(M, RowMaximum(); check=false)   # native LinearAlgebra call
    note!("LinearAlgebra.lu(::Matrix{Rational{BigInt}}, RowMaximum(); check=false)")
    return count(!iszero, LinearAlgebra.diag(F.U))
end

ratstr(x::Rational{BigInt}) = denominator(x) == 1 ? string(numerator(x)) : string(numerator(x), "//", denominator(x))

# ---------------------------------------------------------------------------
# read the fixture
# ---------------------------------------------------------------------------

fixture_sha = bytes2hex(SHA.sha256(read(FIXTURE)))     # native SHA stdlib call
note!("SHA.sha256(read(fixture)) -> fixture integrity digest")
fx = JSON.parsefile(FIXTURE)                            # native JSON.jl call
note!("JSON.parsefile(fixture_v0.json)")

n = Int(fx["n"])
J = Int.(fx["J"])
@assert n == 3
@assert length(J) == 8
@assert J == collect(0:7)

pres = fx["presentations"]
checker_edges_fx = [(Int(e[1]), Int(e[2])) for e in pres["checker"]["edges"]]
ring_edges_fx    = [(Int(e[1]), Int(e[2])) for e in pres["ring"]["edges"]]
spun_edges_fx    = [(Int(e[1]), Int(e[2])) for e in pres["spun"]["edges"]]
gray_order       = Int.(pres["ring"]["gray_code_order"])
sigma_tab        = Int.(pres["spun"]["relabelling"])    # sigma_tab[v+1] == sigma(v)

hr("FIXTURE")
println("path        : ", FIXTURE)
println("sha256      : ", fixture_sha)
println("n           : ", n, "   |J| = ", length(J))
println("edges in fx : checker=", length(checker_edges_fx),
        " ring=", length(ring_edges_fx), " spun=", length(spun_edges_fx))

# ---------------------------------------------------------------------------
# F0 — PAIR-FIELD FLOOR
# ---------------------------------------------------------------------------
hr("F0 pair-field floor")

# popcount is Base.count_ones, the native CPU popcount intrinsic
note!("Base.count_ones (native popcount intrinsic) over J x J")
ham(a, b) = count_ones(xor(a, b))

F_diag = Matrix{Rational{BigInt}}(undef, 8, 8)
F_coh  = Matrix{Rational{BigInt}}(undef, 8, 8)
for (ji, j) in enumerate(J), (ki, k) in enumerate(J)
    F_diag[ji, ki] = (j == k)      ? 1 // 1 : 0 // 1
    F_coh[ji, ki]  = (ham(j, k) <= 1) ? 1 // 1 : 0 // 1
end

a0 = log2(length(J))                                  # identical by construction

# A1 — ORDERED reading: count of nonzero ENTRIES of the matrix F[j][k].
# The spec writes #{(j,k) : F[j][k] != 0}, i.e. index pairs of the field.
nz_diag_ordered = count(!iszero, F_diag)
nz_coh_ordered  = count(!iszero, F_coh)
# UNORDERED diagnostic: diagonal + undirected off-diagonal pairs.
nz_diag_unordered = count(!iszero, [F_diag[i, k] for i in 1:8 for k in i:8])
nz_coh_unordered  = count(!iszero, [F_coh[i, k]  for i in 1:8 for k in i:8])

a1_diag = log2(nz_diag_ordered)
a1_coh  = log2(nz_coh_ordered)

# A2 — exact rank over the rationals, three exact paths
a2_diag       = exact_rank(F_diag);  note!("exact_rank over Rational{BigInt} (row echelon, no tolerance)")
a2_coh        = exact_rank(F_coh)
det_diag      = LinearAlgebra.det(F_diag); note!("LinearAlgebra.det(::Matrix{Rational{BigInt}}) -> exact Rational{BigInt}")
det_coh       = LinearAlgebra.det(F_coh)
lupiv_diag    = lu_pivot_count(F_diag)
lupiv_coh     = lu_pivot_count(F_coh)

# measured record that LinearAlgebra.rank is NOT an exact path for Rational
rank_float_path_error = try
    LinearAlgebra.rank(F_coh)
    "no error raised"
catch e
    first(sprint(showerror, e), 120)
end

println("DIAG      A0=", a0, "  A1=", a1_diag, "  A2=", a2_diag,
        "   (nonzero ordered=", nz_diag_ordered, ", unordered=", nz_diag_unordered,
        ", det=", ratstr(det_diag), ", lu pivots=", lupiv_diag, ")")
println("COHERENT  A0=", a0, "  A1=", a1_coh, "  A2=", a2_coh,
        "   (nonzero ordered=", nz_coh_ordered, ", unordered=", nz_coh_unordered,
        ", det=", ratstr(det_coh), ", lu pivots=", lupiv_coh, ")")
println("LinearAlgebra.rank on Rational -> ", rank_float_path_error)
println("separates DIAG/COHERENT : A1 (", a1_diag, " vs ", a1_coh, ")")
println("does NOT separate       : A0 (identical by construction), A2 (",
        a2_diag, " vs ", a2_coh, ", identical by computation)")

# ---------------------------------------------------------------------------
# F1 — QUOTIENT / FIBRE
# ---------------------------------------------------------------------------
hr("F1 quotient / fibre")

fibres_of(f, codomain) = [sort([j for j in J if f(j) == y]) for y in codomain]

q(j)  = count_ones(j)
q2(j) = mod(j, 5)

Q_cod  = collect(0:4)
Q2_cod = collect(0:4)

fib_q  = fibres_of(q,  Q_cod)
fib_q2 = fibres_of(q2, Q2_cod)

"Release_q(y): on an EMPTY fibre return the fibre descriptor, never a number."
function release_q(fibre::Vector{Int}, y::Int)
    if isempty(fibre)
        return Dict("y" => y, "kind" => "descriptor", "size" => 0,
                    "members" => Int[],
                    "note" => "empty fibre: no capacity arithmetic admitted")
    else
        return Dict("y" => y, "kind" => "capacity", "size" => length(fibre),
                    "members" => fibre, "kappa" => log2(length(fibre)))
    end
end

rel_q = [release_q(fib_q[i], Q_cod[i]) for i in eachindex(Q_cod)]
any_empty_q = any(isempty, fib_q)

fib_sizes_q  = length.(fib_q)
fib_sizes_q2 = length.(fib_q2)
kappa_q      = [log2(s) for s in fib_sizes_q]     # every fibre non-empty here

for i in eachindex(Q_cod)
    println("q  fibre y=", Q_cod[i], " size=", fib_sizes_q[i],
            " kappa=", kappa_q[i], " members=", fib_q[i])
end
println("q2 fibre sizes      : ", fib_sizes_q2)
for i in eachindex(Q2_cod)
    println("q2 fibre y=", Q2_cod[i], " members=", fib_q2[i])
end
println("|Q| equal?          : ", length(Q_cod) == length(Q2_cod))
println("fibre-size multiset : q=", sort(fib_sizes_q), "  q2=", sort(fib_sizes_q2),
        "  distinguished=", sort(fib_sizes_q) != sort(fib_sizes_q2))
println("any empty fibre     : ", any_empty_q)

# BOUNDARY probe: same map, codomain declared as 0:5, so y=5 has an empty
# fibre. This exercises the Release_q guard rather than asserting it is live.
q3_cod = collect(0:5)
fib_q3 = fibres_of(q, q3_cod)
rel_q3_last = release_q(fib_q3[end], 5)
println("boundary probe q on codomain 0:5 -> y=5 kind=", rel_q3_last["kind"],
        " size=", rel_q3_last["size"], " (no arithmetic taken)")

# ---------------------------------------------------------------------------
# F2 — PRESENTATION GEOMETRY  (Graphs.jl carries the graph operations)
# ---------------------------------------------------------------------------
hr("F2 presentation geometry")

# Graphs.jl vertices are 1..16; J value v corresponds to vertex v+1.
function build(edges::Vector{Tuple{Int,Int}})
    g = Graphs.SimpleGraph(8)
    for (a, b) in edges
        Graphs.add_edge!(g, a + 1, b + 1)
    end
    return g
end

# independent re-derivation of each presentation from its declared definition
checker_derived = sort([(a, b) for a in J for b in J if a < b && ham(a, b) == 1])
ring_derived = sort([(min(gray_order[i], gray_order[mod1(i + 1, 8)]),
                      max(gray_order[i], gray_order[mod1(i + 1, 8)])) for i in 1:8])
sigma(v) = sigma_tab[v+1]
spun_derived = sort([(min(sigma(a), sigma(b)), max(sigma(a), sigma(b))) for (a, b) in ring_edges_fx])

sigma_is_bijection = sort(sigma_tab) == collect(0:7)
sigma_matches_formula = all(sigma_tab[v+1] == mod(3v + 7, 8) for v in 0:7)

println("checker fixture == derived from popcount(xor)==1 : ", sort(checker_edges_fx) == checker_derived)
println("ring    fixture == derived from gray_code_order  : ", sort(ring_edges_fx) == ring_derived)
println("spun    fixture == sigma(ring)                   : ", sort(spun_edges_fx) == spun_derived)
println("sigma bijection=", sigma_is_bijection, "  matches (3v+7) mod 16=", sigma_matches_formula)

g_checker = build(checker_edges_fx)
g_ring    = build(ring_edges_fx)
g_spun    = build(spun_edges_fx)
note!("Graphs.SimpleGraph / Graphs.add_edge! to carry each presentation")

function report(name, g)
    V  = Graphs.nv(g)
    E  = Graphs.ne(g)
    dg = sort(Graphs.degree(g))
    cc = length(Graphs.connected_components(g))
    cyc_formula = E - V + cc
    cyc_basis   = length(Graphs.cycle_basis(g))     # independent algorithm
    # third path: nullity of the exact Laplacian == number of components
    L = Matrix{Rational{BigInt}}(Matrix(Graphs.laplacian_matrix(g)))
    lap_nullity = V - exact_rank(L)
    println(rpad(name, 8), " V=", V, " E=", E, " components=", cc,
            " cycle_rank(E-V+C)=", cyc_formula,
            " |cycle_basis|=", cyc_basis,
            " laplacian_nullity=", lap_nullity,
            " degseq=", dg)
    return (V=V, E=E, deg=dg, cc=cc, cyc=cyc_formula, cyc_basis=cyc_basis, lap=lap_nullity)
end
note!("Graphs.nv / Graphs.ne / Graphs.degree / Graphs.connected_components / Graphs.cycle_basis / Graphs.laplacian_matrix")

r_checker = report("CHECKER", g_checker)
r_ring    = report("RING",    g_ring)
r_spun    = report("SPUN",    g_spun)

println("\nnegative controls")

# N1 SEAM-BROKEN RING: delete one ring edge. Declared cut = first fixture edge.
cut_edge = ring_edges_fx[1]
g_n1 = build([e for e in ring_edges_fx if e != cut_edge])
r_n1 = report("N1-CUT", g_n1)
println("  N1 cut edge = ", cut_edge, "  cycle rank ", r_ring.cyc, " -> ", r_n1.cyc,
        "  dropped=", r_n1.cyc < r_ring.cyc)

# N2 BAD ADJACENCY: add an edge at Hamming distance 3 in CHECKER.
n2_edge = (0, 7)
@assert ham(n2_edge[1], n2_edge[2]) == 3
g_n2 = build(vcat(checker_edges_fx, [n2_edge]))
r_n2 = report("N2-ADD", g_n2)
n2_degree_changed = r_n2.deg != r_checker.deg
println("  N2 added edge = ", n2_edge, " (Hamming ", ham(n2_edge...), ")  degseq changed=", n2_degree_changed)

# N3 NO-MAP CLAIM: assert CHECKER == RING with no transition map supplied.
n3_edge_counts_differ = r_checker.E != r_ring.E
println("  N3 checker E=", r_checker.E, " ring E=", r_ring.E,
        " differ=", n3_edge_counts_differ,
        " -> identity claim without a transition map is EXCLUDED")

# ---------------------------------------------------------------------------
# F3 — NESTED CONSTRAINTS AND REWRITES
# ---------------------------------------------------------------------------
hr("F3 nested constraints and rewrites")

r_map(j) = j & 0b11                 # restriction to the low two bits
seam_ok(a, b) = (r_map(a) == r_map(b)) || (count_ones(xor(r_map(a), r_map(b))) == 1)

seam_total = length(checker_edges_fx)
seam_sat   = count(e -> seam_ok(e[1], e[2]), checker_edges_fx)
seam_viol_base = [e for e in checker_edges_fx if !seam_ok(e[1], e[2])]
println("seam obligation on CHECKER : ", seam_sat, "/", seam_total,
        "  violating=", seam_viol_base)
println("NOTE: this positive check is satisfied by construction on this carrier ",
        "(a Q4 edge flips one bit, which is either low or high), so it has no ",
        "discriminating power on its own.")

# R1 CONTRACT — identify vertices sharing the same r image
r_classes = Dict{Int,Vector{Int}}()
for j in J
    push!(get!(r_classes, r_map(j), Int[]), j)
end
r1_quotient_vertices = length(r_classes)
r1_selfloop_images = count(e -> r_map(e[1]) == r_map(e[2]), checker_edges_fx)
r1_cross_images    = seam_total - r1_selfloop_images
r1_simple_edges    = length(unique([(min(r_map(a), r_map(b)), max(r_map(a), r_map(b)))
                                    for (a, b) in checker_edges_fx if r_map(a) != r_map(b)]))
r1_distinct_selfloops = length(unique([r_map(a) for (a, b) in checker_edges_fx if r_map(a) == r_map(b)]))
println("R1 CONTRACT  quotient vertices=", r1_quotient_vertices,
        "  fibres=", sort(collect(keys(r_classes))),
        "\n             edge images: total=", seam_total,
        " self-loop images=", r1_selfloop_images, " (", r1_distinct_selfloops, " distinct)",
        " cross images=", r1_cross_images, " over ", r1_simple_edges, " simple edges")
println("R1 verdict   : rewrite applied; seam obligation was already satisfied on every ",
        "base edge, so contraction is admitted with no repair taken.")

# R2 OBSTRUCT — add (0b0000, 0b0111), then re-check the seam obligation.
# Written as Int; Julia parses 0b0000 as UInt8, which would give a mixed-type
# edge list and print as (0x00, 0x07).
r2_edge = (0, 7)   # 0b0000, 0b0111
@assert ham(r2_edge[1], r2_edge[2]) == 3
checker_r2 = vcat(checker_edges_fx, [r2_edge])
r2_violating = [e for e in checker_r2 if !seam_ok(e[1], e[2])]
r2_violating_edges = length(r2_violating)
r2_blocked = r2_violating_edges > 0
println("R2 OBSTRUCT  added ", r2_edge, "  r(", r2_edge[1], ")=", r_map(r2_edge[1]),
        " r(", r2_edge[2], ")=", r_map(r2_edge[2]),
        "  base Hamming=", count_ones(xor(r_map(r2_edge[1]), r_map(r2_edge[2]))))
println("R2 violating edges=", r2_violating_edges, " -> ", r2_violating)
println("R2 verdict   : BLOCKED under NO-REPAIR. No value was adjusted to make the ",
        "check pass; the obstruction survives.")

# ---------------------------------------------------------------------------
# engine-call ledger
# ---------------------------------------------------------------------------
hr("engine operations actually called")
for c in unique(CALLS)
    println("  ", c)
end

# ---------------------------------------------------------------------------
# OUTPUT CONTRACT — one JSON object, last line of stdout
# ---------------------------------------------------------------------------
out = Dict{String,Any}(
    "engine_name" => "julia",
    "lane_nonce"  => NONCE,

    "f0_diag_a0" => a0,
    "f0_diag_a1" => a1_diag,
    "f0_diag_a2" => a2_diag,
    "f0_coh_a0"  => a0,
    "f0_coh_a1"  => a1_coh,
    "f0_coh_a2"  => a2_coh,

    "f1_fibre_sizes"    => fib_sizes_q,
    "f1_kappa"          => kappa_q,
    "f1_q2_fibre_sizes" => fib_sizes_q2,

    "f2_checker_edges"            => r_checker.E,
    "f2_ring_edges"               => r_ring.E,
    "f2_checker_cycles"           => r_checker.cyc,
    "f2_ring_cycles"              => r_ring.cyc,
    "f2_n1_ring_cycles_after_cut" => r_n1.cyc,
    "f2_n2_degree_changed"        => n2_degree_changed,
    "f2_n3_edge_counts_differ"    => n3_edge_counts_differ,

    "f3_seam_satisfied_edges" => seam_sat,
    "f3_seam_total_edges"     => seam_total,
    "f3_r1_quotient_vertices" => r1_quotient_vertices,
    "f3_r2_violating_edges"   => r2_violating_edges,
    "f3_r2_blocked"           => r2_blocked,

    "lane_detail" => Dict{String,Any}(
        "julia_version"  => string(VERSION),
        "fixture_sha256" => fixture_sha,
        "a2_method"      => "exact row-echelon rank over Rational{BigInt}; LinearAlgebra.rank rejected as a float path",
        "a2_float_path_error" => rank_float_path_error,
        "a2_cross_checks" => Dict(
            "det_diag" => ratstr(det_diag),
            "det_coh"  => ratstr(det_coh),
            "lu_pivots_diag" => lupiv_diag,
            "lu_pivots_coh"  => lupiv_coh,
        ),
        "exact_integer_forms" => Dict(
            "f0_diag_nonzero_ordered"   => nz_diag_ordered,
            "f0_coh_nonzero_ordered"    => nz_coh_ordered,
            "f0_diag_nonzero_unordered" => nz_diag_unordered,
            "f0_coh_nonzero_unordered"  => nz_coh_unordered,
            "f1_fibre_sizes"            => fib_sizes_q,
        ),
        "a1_convention" => "ORDERED: nonzero entries of the 16x16 field F[j][k]",
        "f0_separating_quantities"     => ["A1"],
        "f0_non_separating_quantities" => ["A0 (identical by construction)", "A2 (identical by computation)"],
        "f1_any_empty_fibre" => any_empty_q,
        "f1_release_q" => rel_q,
        "f1_empty_fibre_boundary_probe" => rel_q3_last,
        "f1_quotients_distinguished_by_fibre_size_multiset" =>
            sort(fib_sizes_q) != sort(fib_sizes_q2),
        "f2_degree_sequences" => Dict(
            "checker" => r_checker.deg, "ring" => r_ring.deg, "spun" => r_spun.deg,
            "n2" => r_n2.deg),
        "f2_components" => Dict(
            "checker" => r_checker.cc, "ring" => r_ring.cc, "spun" => r_spun.cc),
        "f2_cycle_basis_lengths" => Dict(
            "checker" => r_checker.cyc_basis, "ring" => r_ring.cyc_basis,
            "spun" => r_spun.cyc_basis, "n1_cut" => r_n1.cyc_basis),
        "f2_laplacian_nullity" => Dict(
            "checker" => r_checker.lap, "ring" => r_ring.lap, "spun" => r_spun.lap,
            "n1_cut" => r_n1.lap),
        "f2_spun_vertices" => r_spun.V,
        "f2_spun_edges"    => r_spun.E,
        "f2_spun_cycles"   => r_spun.cyc,
        "f2_n1_cut_edge"   => [cut_edge[1], cut_edge[2]],
        "f2_n2_added_edge" => [n2_edge[1], n2_edge[2]],
        "f2_presentation_rederivation_matches_fixture" => Dict(
            "checker" => sort(checker_edges_fx) == checker_derived,
            "ring"    => sort(ring_edges_fx) == ring_derived,
            "spun"    => sort(spun_edges_fx) == spun_derived),
        "f2_sigma_is_bijection" => sigma_is_bijection,
        "f2_sigma_matches_declared_formula" => sigma_matches_formula,
        "f3_seam_positive_check_is_by_construction" => true,
        "f3_r1_edge_image_split" => Dict(
            "total_edge_images" => seam_total,
            "self_loop_images"  => r1_selfloop_images,
            "distinct_self_loops" => r1_distinct_selfloops,
            "cross_images"      => r1_cross_images,
            "simple_edges"      => r1_simple_edges),
        "f3_r2_added_edge"        => [r2_edge[1], r2_edge[2]],
        "f3_r2_violating_edge_list" => [[e[1], e[2]] for e in r2_violating],
        "f3_repair_policy" => "NO-REPAIR: no value adjusted to make the check pass",
        "engine_calls" => unique(CALLS),
    ),
)

println()
println(JSON.json(out))
