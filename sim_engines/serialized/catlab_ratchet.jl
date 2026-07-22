# Stage 1 (julia): CARRIER CALIBRATION — one authored carrier candidate.
#
# CLAIM CEILING (webui audit 2026-07-22): C4 x C4 is a finite 16-vertex
# 4-regular bipartite graph. That is the ENTIRE licensed conclusion. This is
# NOT the Ratchet, not physics genesis, not noncommutation, not entropy
# closure, not the constraint manifold — one authored carrier/control among
# candidates. The mask governs only whichever vector field later multiplies it.
#
# Method: exact Catlab construction + TWO independent bipartiteness witnesses
# (deterministic BFS 2-coloring, and an SMT 2-colorability witness with an
# odd-cycle polarity control showing the solver call is not decorative).
#
# Usage: julia --project=<carrier> catlab_ratchet.jl <output_path.arrow>
# Exit: 0 mask bound, 1 calibration failure (fail closed).

using Catlab
using Catlab.Graphs
using Arrow
using Z3
using JSON
using SHA

const GRID = 4
const N = GRID * GRID

# 2D -> 1D with modulo arithmetic: the modulo IS the Ring (periodic torus).
idx(r, c) = mod(r, GRID) * GRID + mod(c, GRID) + 1

function build_ring_checkerboard()
    println("[+] Constructing Ring Checkerboard topology (N=$N, $(GRID)x$(GRID) torus)")
    g = SymmetricGraph(N)
    for r in 0:(GRID - 1), c in 0:(GRID - 1)
        add_edge!(g, idx(r, c), idx(r, c + 1))  # right (wraps)
        add_edge!(g, idx(r, c), idx(r + 1, c))  # down (wraps)
    end
    return g
end

"Undirected edge pairs extracted FROM the Catlab graph (it is load-bearing)."
function edge_pairs(g)
    pairs = Set{Tuple{Int,Int}}()
    for e in edges(g)
        u, v = src(g, e), tgt(g, e)
        push!(pairs, (min(u, v), max(u, v)))
    end
    return sort(Base.collect(pairs))  # Base-qualified: Catlab exports a clashing `collect`
end

"Independent witness 1: deterministic BFS 2-coloring (no solver involved)."
function bfs_bipartite(pairs)
    adj = Dict{Int,Vector{Int}}()
    for (u, v) in pairs
        push!(get!(adj, u, Int[]), v)
        push!(get!(adj, v, Int[]), u)
    end
    color = Dict{Int,Int}(1 => 0)
    queue = [1]
    while !isempty(queue)
        u = popfirst!(queue)
        for w in get(adj, u, Int[])
            if !haskey(color, w)
                color[w] = 1 - color[u]
                push!(queue, w)
            elseif color[w] == color[u]
                return false
            end
        end
    end
    return length(color) == N  # connected + properly 2-colored
end

"Independent witness 2: SMT 2-colorability (sat <=> bipartite)."
function gate_m1_bipartite(pairs; label="torus")
    # Z3-qualified throughout: Catlab/GATlab export clashing Context/Solver names.
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    colors = [Z3.BoolVar("node_$i", ctx) for i in 1:N]  # Z3.jl signature: (name, ctx)
    for (u, v) in pairs
        Z3.add(solver, Z3.Not(Z3.Iff(colors[u], colors[v])))  # XOR: endpoints differ
    end
    return string(Z3.check(solver))
end

function execute(output_path::String)
    g = build_ring_checkerboard()
    pairs = edge_pairs(g)
    println("[+] Catlab graph: $(nv(g)) vertices, $(length(pairs)) undirected edges")

    # Witness 1: deterministic BFS 2-coloring — the primary check (a fixed
    # graph does not need a solver to establish bipartiteness).
    if !bfs_bipartite(pairs)
        println("[!] FATAL calibration: BFS 2-coloring failed. Failing closed.")
        exit(1)
    end
    println("[*] carrier calibration: BFS 2-coloring OK — C4xC4 is bipartite (claim ceiling: carrier property only).")

    # Witness 2: SMT 2-colorability, cross-checking witness 1.
    status = gate_m1_bipartite(pairs)
    if status != "sat"
        println("[!] FATAL calibration: SMT witness returned :$status, disagreeing with BFS. Failing closed.")
        exit(1)
    end
    println("[*] carrier calibration: SMT witness :sat agrees with BFS.")

    # Polarity control: a diagonal edge creates an odd cycle; the SMT call
    # must flip to unsat or the solver call is decorative.
    smuggled = vcat(pairs, [(min(idx(0,0), idx(1,1)), max(idx(0,0), idx(1,1)))])
    flip = gate_m1_bipartite(smuggled; label="torus+diagonal")
    if flip != "unsat"
        println("[!] FATAL calibration polarity control: odd-cycle fixture returned :$flip (expected unsat). Failing closed.")
        exit(1)
    end
    println("[*] calibration polarity control: odd-cycle fixture -> :unsat (solver call not decorative).")

    # Dense Float64 mask (x64 is non-negotiable) built from the Catlab edges.
    A = zeros(Float64, N, N)
    for (u, v) in pairs
        A[u, v] = 1.0
        A[v, u] = 1.0
    end

    # Immutable Arrow artifact — a NamedTuple of columns is a Tables.jl table.
    cols = NamedTuple{Tuple(Symbol.("dim_", 1:N))}(Tuple(Vector(A[:, j]) for j in 1:N))
    Arrow.write(output_path, cols)
    println("[+] Immutable Ratchet artifact bound to: $output_path")

    # Sidecar M1 receipt — binds the PROOF to the artifact (referee finding:
    # a proof living only in process stdout pins nothing; ClaimGate needs it
    # in the ledger). pairs_digest ties the proved edge set to these bytes.
    pairs_str = join(["$(u)-$(v)" for (u, v) in pairs], ";")
    receipt = Dict(
        "m1_status" => status,
        "m1_polarity" => flip,
        "bfs_bipartite" => true,
        "pairs_digest" => bytes2hex(sha256(codeunits(pairs_str))),
        "n_vertices" => N,
        "n_edges" => length(pairs),
        "encoding" => "xor_per_edge_2coloring",
        "claim_ceiling" => "carrier property only — C4xC4 is a finite 16-vertex 4-regular bipartite graph; establishes nothing about noncommutation, smuggling, the Ratchet, or the manifold",
    )
    open(output_path * ".receipt.json", "w") do io
        JSON.print(io, receipt)
    end
    println("[+] M1 receipt bound to: $(output_path).receipt.json")
end

if abspath(PROGRAM_FILE) == @__FILE__
    length(ARGS) == 1 || (println("usage: catlab_ratchet.jl <output_path.arrow>"); exit(2))
    execute(ARGS[1])
end
