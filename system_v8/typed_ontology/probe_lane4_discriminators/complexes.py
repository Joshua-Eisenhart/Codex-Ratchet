"""Shared exact finite-complex machinery for D2 and D4. No floats.

A 2-complex here is (V, E, F) with E a list of ordered vertex pairs and F a list
of vertex cycles (length 3 or 4). Boundary matrices are exact integer sympy
matrices; d1 d2 = 0 is MEASURED, never assumed.
"""
import sympy

N = 4
J = list(range(2 ** N))


def popcount(x):
    return bin(x).count("1")


def hypercube_edges(n=N):
    return sorted({tuple(sorted((j, j ^ (1 << b)))) for j in range(2 ** n) for b in range(n)})


def circulant_edges(nv, steps):
    return sorted({tuple(sorted((i, (i + s) % nv))) for i in range(nv) for s in steps})


def torus_grid_edges(a=4, b=4):
    """C_a box C_b on vertices a*x + y  (x in Z_a, y in Z_b)."""
    idx = lambda x, y: (x % a) * b + (y % b)
    e = set()
    for x in range(a):
        for y in range(b):
            e.add(tuple(sorted((idx(x, y), idx(x + 1, y)))))
            e.add(tuple(sorted((idx(x, y), idx(x, y + 1)))))
    return sorted(e)


def torus_grid_faces(a=4, b=4):
    idx = lambda x, y: (x % a) * b + (y % b)
    return [[idx(x, y), idx(x + 1, y), idx(x + 1, y + 1), idx(x, y + 1)]
            for x in range(a) for y in range(b)]


def hypercube_squares(n=N):
    """The CANONICAL cubical 2-cells: fix n-2 coords, free two coords b1 < b2.
    Cycle order v, v^b1, v^b1^b2, v^b2 so the boundary is a genuine 4-cycle."""
    faces = []
    for b1 in range(n):
        for b2 in range(b1 + 1, n):
            m = (1 << b1) | (1 << b2)
            for v in range(2 ** n):
                if v & m:
                    continue  # one representative per 2-cell: both free bits 0
                faces.append([v, v ^ (1 << b1), v ^ m, v ^ (1 << b2)])
    return faces


def octahedron():
    """Finite S^2: 6 vertices, 12 edges, 8 triangles."""
    v = list(range(6))  # 0,1 = +-x ; 2,3 = +-y ; 4,5 = +-z
    faces = []
    for a in (0, 1):
        for b in (2, 3):
            for c in (4, 5):
                faces.append([a, b, c])
    edges = sorted({tuple(sorted(p)) for f in faces for p in
                    [(f[0], f[1]), (f[1], f[2]), (f[2], f[0])]})
    return v, edges, faces


def boundary_1(nv, edges):
    """d1 : C_1 -> C_0, column per edge, -1 at tail, +1 at head."""
    M = sympy.zeros(nv, len(edges))
    for c, (u, w) in enumerate(edges):
        M[u, c] -= 1
        M[w, c] += 1
    return M


def boundary_2(edges, faces):
    """d2 : C_2 -> C_1, signed by traversal direction around each face cycle."""
    pos = {e: i for i, e in enumerate(edges)}
    M = sympy.zeros(len(edges), len(faces))
    for c, cyc in enumerate(faces):
        for i in range(len(cyc)):
            u, w = cyc[i], cyc[(i + 1) % len(cyc)]
            key = tuple(sorted((u, w)))
            if key not in pos:
                raise ValueError(f"face edge {(u, w)} absent from the edge list")
            M[pos[key], c] += 1 if u < w else -1
    return M


def homology_over_Q(nv, edges, faces):
    d1 = boundary_1(nv, edges)
    d2 = boundary_2(edges, faces)
    r1, r2 = int(d1.rank()), int(d2.rank())
    comp = d1 * d2
    return {
        "vertices": nv,
        "edges": len(edges),
        "faces": len(faces),
        "euler_characteristic_V_minus_E_plus_F": nv - len(edges) + len(faces),
        "rank_boundary_1": r1,
        "rank_boundary_2": r2,
        "d1_d2_max_abs_entry": int(max((abs(x) for x in comp), default=0)),
        "betti_0_over_Q": nv - r1,
        "betti_1_over_Q": (len(edges) - r1) - r2,
        "betti_2_over_Q": len(faces) - r2,
    }


def graph_observables(nv, edges):
    import networkx as nx

    G = nx.Graph()
    G.add_nodes_from(range(nv))
    G.add_edges_from(edges)
    A = sympy.zeros(nv, nv)
    for u, w in edges:
        A[u, w] = 1
        A[w, u] = 1
    lam = sympy.Symbol("lam")
    cp = sympy.Poly(A.charpoly(lam).as_expr(), lam)
    charpoly = cp.all_coeffs()
    irreducible_factors = sorted(str(sympy.expand(f)) for f, _ in sympy.factor_list(cp.as_expr())[1])
    A3, A4 = A * A * A, A * A * A * A
    tr = lambda M: int(sum(M[i, i] for i in range(nv)))
    deg = sorted((d for _, d in G.degree()), reverse=True)
    m = len(edges)
    sum_d2 = sum(d * d for d in deg)
    # tr(A^4) = 2*sum d^2 - 2m + 8*C4   (back-and-forth, spur, and genuine 4-cycles)
    four_cycles = (tr(A4) - 2 * sum_d2 + 2 * m) // 8
    girths = sorted(len(c) for c in nx.cycle_basis(G)) if m else []
    return {
        "vertices": nv,
        "edges": m,
        "degree_sequence": deg,
        "is_regular": len(set(deg)) == 1,
        "is_bipartite": bool(nx.is_bipartite(G)),
        "triangle_count": tr(A3) // 6,
        "shortest_cycle_in_a_cycle_basis": girths[0] if girths else 0,
        "cycle_rank_E_minus_V_plus_components": m - nv + nx.number_connected_components(G),
        "four_cycle_count": four_cycles,
        "adjacency_charpoly_coeffs_exact": [int(c) for c in charpoly],
        "adjacency_charpoly_irreducible_factors": irreducible_factors,
    }
