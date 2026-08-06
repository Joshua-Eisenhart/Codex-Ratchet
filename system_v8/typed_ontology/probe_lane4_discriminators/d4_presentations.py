#!/usr/bin/env python3
"""D4 PRESENTATIONS discriminator.

Rival A: ONE common support carrying three declared maps (three presentations of
         one object, related by transition maps).
Rival B: THREE separate spaces that merely look alike.

Leg 1  checkerboard (4-cube 1-skeleton) vs ring (C16), without and with a
       declared transition map (the reflected Gray code).
Leg 2  chi(S^2) = 2 vs chi(T^2) = 0 on finite analogues, so a torus cannot
       silently pass as a sphere.
"""
import json
import os
import sys

import networkx as nx

from complexes import (graph_observables, homology_over_Q, hypercube_edges,
                       hypercube_squares, octahedron, torus_grid_edges,
                       torus_grid_faces)


def gray(i):
    return i ^ (i >> 1)


def main():
    q4_e = hypercube_edges(4)
    ring_e = sorted({tuple(sorted((i, (i + 1) % 16))) for i in range(16)})

    checkerboard = graph_observables(16, q4_e)
    ring = graph_observables(16, ring_e)
    raw_sep = sorted(k for k in checkerboard if checkerboard[k] != ring[k])

    # A DECLARED transition map: the reflected Gray code, ring vertex i -> address g(i).
    gmap = {i: gray(i) for i in range(16)}
    image_edges = sorted({tuple(sorted((gmap[u], gmap[w]))) for u, w in ring_e})
    q4_set = set(q4_e)
    hits = [e for e in image_edges if e in q4_set]
    transition = {
        "map": "reflected Gray code, ring vertex i -> address i xor (i >> 1)",
        "vertex_map_is_a_bijection": sorted(gmap.values()) == list(range(16)),
        "ring_edges": len(ring_e),
        "ring_edge_images_that_are_4cube_edges": len(hits),
        "ring_edge_images_that_are_not_4cube_edges": len(image_edges) - len(hits),
        "4cube_edges_covered_by_the_image": len(set(hits)),
        "4cube_edges_not_covered_by_the_image": len(q4_set - set(hits)),
        "edge_map_is_a_bijection": len(set(hits)) == len(q4_set),
        "image_is_a_proper_subcomplex": set(hits) < q4_set,
        "presentations_isomorphic_as_graphs":
            bool(nx.is_isomorphic(nx.Graph(q4_e), nx.Graph(ring_e))),
    }

    # A third presentation on the SAME support: the pair-field matrix incidence.
    third = {
        "presentation": "pair-field incidence F[j][k] = 1 iff popcount(j xor k) == 1",
        "support_cardinality": 2 * len(q4_e),
        "edges_recovered_from_the_support": len({tuple(sorted((j, k)))
                                                 for j in range(16) for k in range(16)
                                                 if bin(j ^ k).count("1") == 1}),
        "agrees_with_the_checkerboard_edge_set":
            {tuple(sorted((j, k))) for j in range(16) for k in range(16)
             if bin(j ^ k).count("1") == 1} == q4_set,
    }

    sphere_v, sphere_e, sphere_f = octahedron()
    sphere = homology_over_Q(len(sphere_v), sphere_e, sphere_f)
    torus = homology_over_Q(16, torus_grid_edges(4, 4), torus_grid_faces(4, 4))
    cube2 = homology_over_Q(16, q4_e, hypercube_squares(4))

    result = {
        "discriminator": "D4_presentations_common_support_vs_separate_spaces",
        "leg_1_checkerboard_vs_ring": {
            "checkerboard_observables": checkerboard,
            "ring_observables": ring,
            "observables_that_separate_without_any_transition_map": raw_sep,
            "with_a_declared_transition_map": transition,
            "third_presentation_on_the_same_support": third,
        },
        "leg_2_sphere_vs_torus": {
            "finite_S2_octahedron": sphere,
            "finite_T2_C4_box_C4_quads": torus,
            "cubical_4cube_2skeleton_for_reference": cube2,
            "euler_characteristics_differ":
                sphere["euler_characteristic_V_minus_E_plus_F"]
                != torus["euler_characteristic_V_minus_E_plus_F"],
            "betti_signatures": {
                "finite_S2": [sphere["betti_0_over_Q"], sphere["betti_1_over_Q"],
                              sphere["betti_2_over_Q"]],
                "finite_T2": [torus["betti_0_over_Q"], torus["betti_1_over_Q"],
                              torus["betti_2_over_Q"]],
            },
        },
    }
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "results", "d4_presentations.json")
    with open(path, "w") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
    print(json.dumps(result, indent=1, sort_keys=True))
    print(f"WROTE {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
