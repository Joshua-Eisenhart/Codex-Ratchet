#!/usr/bin/env python3
"""D2 ROOT GEOMETRY discriminator, n = 4.

Rival A: recursive CUBICAL complex (the 4-cube K, cells over {0,1,*}^4).
Rival B: a general finite cell complex with the SAME vertex and edge counts.

Three rivals are built at 16 vertices / 32 edges so the comparison is not rigged:
  R_circ12  circulant C16(1,2)  -- 4-regular, has triangles
  R_circ13  circulant C16(1,3)  -- 4-regular, bipartite, triangle-free
  R_torus   C4 box C4           -- 4-regular, bipartite, triangle-free
The question the brief asks is whether recursive cubical structure does UNIQUE
work. It is answered at two levels: the 1-skeleton alone, and the 2-cells.
"""
import json
import os
import sys

import networkx as nx

from complexes import (circulant_edges, graph_observables, homology_over_Q,
                       hypercube_edges, hypercube_squares, torus_grid_edges,
                       torus_grid_faces)


def main():
    q4_e = hypercube_edges(4)
    rivals = {
        "A_cubical_4cube_1skeleton": q4_e,
        "B_circulant_C16_1_2": circulant_edges(16, (1, 2)),
        "B_circulant_C16_1_3": circulant_edges(16, (1, 3)),
        "B_torus_grid_C4_box_C4": torus_grid_edges(4, 4),
    }
    obs = {name: graph_observables(16, e) for name, e in rivals.items()}

    ref = obs["A_cubical_4cube_1skeleton"]
    separation = {}
    for name in rivals:
        if name.startswith("A_"):
            continue
        sep = sorted(k for k in ref if ref[k] != obs[name][k])
        same = sorted(k for k in ref if ref[k] == obs[name][k])
        separation[name] = {
            "observables_that_separate_from_the_4cube": sep,
            "observables_that_do_not_separate_from_the_4cube": same,
        }

    # Graph isomorphism, decided by networkx, not asserted.
    def g(edges):
        G = nx.Graph()
        G.add_nodes_from(range(16))
        G.add_edges_from(edges)
        return G

    iso = {name: bool(nx.is_isomorphic(g(q4_e), g(e)))
           for name, e in rivals.items() if not name.startswith("A_")}

    # 2-cell level: the SAME 1-skeleton carrying two different face sets.
    cub_faces = hypercube_squares(4)
    tor_faces = torus_grid_faces(4, 4)
    cubical_complex = homology_over_Q(16, q4_e, cub_faces)
    torus_complex = homology_over_Q(16, torus_grid_edges(4, 4), tor_faces)

    # Are the torus quads a SUBSET of the cubical squares, under the iso?
    iso_map = None
    if iso.get("B_torus_grid_C4_box_C4"):
        gm = nx.algorithms.isomorphism.GraphMatcher(g(torus_grid_edges(4, 4)), g(q4_e))
        if gm.is_isomorphic():
            iso_map = dict(gm.mapping)
    faces_as_sets = lambda F: {frozenset(c) for c in F}
    pushed = None
    if iso_map:
        pushed = faces_as_sets([[iso_map[v] for v in c] for c in tor_faces])
    result = {
        "discriminator": "D2_root_geometry_cubical_vs_general_cell_complex",
        "matched_counts": {"vertices": 16, "edges": 32},
        "one_skeleton_observables": obs,
        "one_skeleton_separation_vs_cubical": separation,
        "graph_isomorphic_to_the_4cube_1skeleton": iso,
        "two_cell_level": {
            "cubical_4cube_2skeleton_24_squares": cubical_complex,
            "torus_C4_box_C4_16_quads": torus_complex,
            "cubical_square_count": len(cub_faces),
            "torus_quad_count": len(tor_faces),
            "torus_quads_are_a_subset_of_the_cubical_squares_under_the_isomorphism":
                (pushed <= faces_as_sets(cub_faces)) if pushed is not None else None,
            "torus_quads_landing_on_a_cubical_square":
                len(pushed & faces_as_sets(cub_faces)) if pushed is not None else None,
        },
    }
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "results", "d2_root_geometry.json")
    with open(path, "w") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
    print(json.dumps(result, indent=1, sort_keys=True))
    print(f"WROTE {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
