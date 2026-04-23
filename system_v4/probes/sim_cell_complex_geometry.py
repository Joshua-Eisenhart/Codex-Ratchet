#!/usr/bin/env python3
"""
PURE LEGO: Cell-Complex Geometry
================================
Direct local graph/topology lego.

Build a few bounded cell complexes from scratch and verify the basic algebraic
topology identities on them.
"""

import json
import pathlib

import numpy as np

from toponetx import CellComplex
classification = "classical_baseline"  # auto-backfill


EPS = 1e-8

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for cell-complex carrier geometry using bounded TopoNetX "
    "complexes and direct homology checks."
)

LEGO_IDS = [
    "cell_complex_geometry",
    "graph_geometry",
]

PRIMARY_LEGO_IDS = [
    "cell_complex_geometry",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- TopoNetX carries the local topology result"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "CellComplex construction, incidence matrices, and Hodge Laplacians are load-bearing here",
    },
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["toponetx"] = "load_bearing"


def build_circle():
    cc = CellComplex()
    for i in range(4):
        cc.add_cell([i, (i + 1) % 4], rank=1)
    return cc


def build_sphere():
    cc = CellComplex()
    faces = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]
    for face in faces:
        cc.add_cell(list(face), rank=2)
    return cc


def build_torus():
    cc = CellComplex()
    n = 3

    def vid(r, c):
        return (r % n) * n + (c % n)

    edge_set = set()
    for r in range(n):
        for c in range(n):
            edge_set.add(tuple(sorted((vid(r, c), vid(r, c + 1)))))
            edge_set.add(tuple(sorted((vid(r, c), vid(r + 1, c)))))

    for edge in sorted(edge_set):
        cc.add_cell(list(edge), rank=1)

    for r in range(n):
        for c in range(n):
            v00 = vid(r, c)
            v10 = vid(r + 1, c)
            v01 = vid(r, c + 1)
            v11 = vid(r + 1, c + 1)
            for tri in ([v00, v01, v11], [v00, v10, v11]):
                for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[0], tri[2])):
                    edge = tuple(sorted((a, b)))
                    if edge not in edge_set:
                        cc.add_cell(list(edge), rank=1)
                        edge_set.add(edge)
                cc.add_cell(tri, rank=2)
    return cc


def build_disconnected_edges():
    cc = CellComplex()
    cc.add_cell([0, 1], rank=1)
    cc.add_cell([2, 3], rank=1)
    return cc


def incidence(cc, rank):
    return cc.incidence_matrix(rank=rank, signed=True).toarray().astype(float)


def betti(cc):
    b1 = incidence(cc, 1)
    n0 = b1.shape[0]
    n1 = b1.shape[1]
    rank_b1 = int(np.linalg.matrix_rank(b1))
    if len(cc.shape) > 2 and cc.shape[2] > 0:
        b2 = incidence(cc, 2)
        n2 = b2.shape[1]
        rank_b2 = int(np.linalg.matrix_rank(b2))
    else:
        b2 = np.zeros((n1, 0))
        n2 = 0
        rank_b2 = 0
    return {
        "beta0": int(n0 - rank_b1),
        "beta1": int(n1 - rank_b1 - rank_b2),
        "beta2": int(n2 - rank_b2),
        "rank_B1": rank_b1,
        "rank_B2": rank_b2,
        "B1B2_zero": bool(np.allclose(b1 @ b2, 0.0, atol=EPS)),
    }


def zero_modes(cc, rank):
    lap = cc.hodge_laplacian_matrix(rank).toarray().astype(float)
    evals = np.linalg.eigvalsh(lap)
    return int(np.sum(np.abs(evals) < EPS)), [float(x) for x in evals]


def main():
    circle = build_circle()
    sphere = build_sphere()
    torus = build_torus()
    disconnected = build_disconnected_edges()

    circle_betti = betti(circle)
    sphere_betti = betti(sphere)
    torus_betti = betti(torus)
    disconnected_betti = betti(disconnected)

    circle_l1_nullity, circle_l1_eigs = zero_modes(circle, 1)
    sphere_l2_nullity, sphere_l2_eigs = zero_modes(sphere, 2)
    torus_l1_nullity, torus_l1_eigs = zero_modes(torus, 1)

    positive = {
        "circle_has_one_loop": {
            **circle_betti,
            "l1_zero_modes": circle_l1_nullity,
            "pass": (
                circle_betti["beta0"] == 1
                and circle_betti["beta1"] == 1
                and circle_betti["beta2"] == 0
                and circle_betti["B1B2_zero"]
                and circle_l1_nullity == 1
            ),
        },
        "sphere_has_one_2_cycle": {
            **sphere_betti,
            "l2_zero_modes": sphere_l2_nullity,
            "pass": (
                sphere_betti["beta0"] == 1
                and sphere_betti["beta1"] == 0
                and sphere_betti["beta2"] == 1
                and sphere_betti["B1B2_zero"]
                and sphere_l2_nullity == 1
            ),
        },
        "torus_has_two_independent_loops": {
            **torus_betti,
            "l1_zero_modes": torus_l1_nullity,
            "pass": (
                torus_betti["beta0"] == 1
                and torus_betti["beta1"] == 2
                and torus_betti["beta2"] == 1
                and torus_betti["B1B2_zero"]
                and torus_l1_nullity == 2
            ),
        },
    }

    negative = {
        "disconnected_edges_are_not_one_connected_carrier": {
            **disconnected_betti,
            "pass": disconnected_betti["beta0"] == 2 and disconnected_betti["beta1"] == 0,
        },
        "circle_is_not_torus": {
            "circle_beta1": circle_betti["beta1"],
            "torus_beta1": torus_betti["beta1"],
            "pass": circle_betti["beta1"] != torus_betti["beta1"],
        },
    }

    boundary = {
        "torus_hodge_kernel_matches_beta1": {
            "pass": torus_l1_nullity == torus_betti["beta1"],
            "torus_l1_eigs": torus_l1_eigs,
        },
        "sphere_hodge_kernel_matches_beta2": {
            "pass": sphere_l2_nullity == sphere_betti["beta2"],
            "sphere_l2_eigs": sphere_l2_eigs,
        },
        "circle_hodge_kernel_matches_beta1": {
            "pass": circle_l1_nullity == circle_betti["beta1"],
            "circle_l1_eigs": circle_l1_eigs,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "cell_complex_geometry",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": "Direct local cell-complex carrier lego on bounded circle, sphere, and torus exemplars.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "cell_complex_geometry_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
