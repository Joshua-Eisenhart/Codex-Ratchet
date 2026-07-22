# Phase 2 — Stage 1 (julia): the topological Ratchet.
#
# Builds the 4x4 Ring Checkerboard (toroidal, bipartite) as a Catlab
# SymmetricGraph, proves Gate M1 (bipartiteness) with Z3.jl — with a polarity
# control (a diagonal smuggling edge must flip the proof to unsat, showing the
# proof is load-bearing, not decorative) — and writes the adjacency mask as an
# immutable Arrow artifact for the JAX stage.
#
# The mask IS the constraint: constraints precede axioms. Every later vector
# field is multiplied by this matrix before it flows.
#
# Usage: julia --project=<carrier> catlab_ratchet.jl <output_path.arrow>
# Exit: 0 mask bound, 1 Gate M1 failure (fail closed).

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

"Gate M1: Z3 proves a 2-coloring exists (bipartite <=> no odd smuggling cycle)."
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

    # Gate M1 positive: the torus must be 2-colorable.
    status = gate_m1_bipartite(pairs)
    if status != "sat"
        println("[!] FATAL Gate M1: torus 2-coloring returned :$status (expected sat). Failing closed.")
        exit(1)
    end
    println("[*] Gate M1 PASSED: :sat — topology is strictly bipartite; diagonal smuggling structurally impossible.")

    # Polarity control: inject a diagonal smuggling edge (0,0)-(1,1); the same
    # proof MUST flip to unsat, or the proof is decorative.
    smuggled = vcat(pairs, [(min(idx(0,0), idx(1,1)), max(idx(0,0), idx(1,1)))])
    flip = gate_m1_bipartite(smuggled; label="torus+diagonal")
    if flip != "unsat"
        println("[!] FATAL Gate M1 polarity control: smuggling edge returned :$flip (expected unsat). Proof decorative. Failing closed.")
        exit(1)
    end
    println("[*] Gate M1 polarity control PASSED: diagonal edge -> :unsat (proof is load-bearing).")

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
        "pairs_digest" => bytes2hex(sha256(codeunits(pairs_str))),
        "n_vertices" => N,
        "n_edges" => length(pairs),
        "encoding" => "xor_per_edge_2coloring",
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
