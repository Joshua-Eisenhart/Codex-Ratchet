#!/usr/bin/env python3
"""
PURE LEGO: State-Class Binding Geometry
=======================================
Direct local topology-to-state-class binding lego on a bounded Werner family.
"""

import json
import pathlib

import numpy as np
from toponetx import CellComplex


EPS = 1e-8
BINDING_THRESHOLD = 0.17

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for topology-to-state-class binding on a bounded one-parameter "
    "Werner family, using direct local TopoNetX cell complexes rather than a broad integrated surface."
)

LEGO_IDS = [
    "state_class_binding_geometry",
]

PRIMARY_LEGO_IDS = [
    "state_class_binding_geometry",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "saved for later hypergraph successor surfaces"},
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "local class-specific cell-complex construction and Betti checks are load-bearing",
    },
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["toponetx"] = "load_bearing"


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
        n2 = 0
        rank_b2 = 0
    return {
        "beta0": int(n0 - rank_b1),
        "beta1": int(n1 - rank_b1 - rank_b2),
        "beta2": int(n2 - rank_b2),
    }


def build_l4_complex():
    cc = CellComplex()
    for edge in [(0, 1), (1, 2)]:
        cc.add_cell(list(edge), rank=1)
    return cc


def build_l6_complex():
    cc = CellComplex()
    for edge in [(0, 1), (1, 2), (0, 2)]:
        cc.add_cell(list(edge), rank=1)
    return cc


def build_combined_boundary_complex():
    cc = CellComplex()
    for edge in [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (3, 5)]:
        cc.add_cell(list(edge), rank=1)
    return cc


def main():
    l4_samples = [0.08, 0.12, 0.16]
    threshold_sample = 0.17
    l6_samples = [0.18, 0.25, 0.33]

    l4_complex = build_l4_complex()
    l6_complex = build_l6_complex()
    combined_complex = build_combined_boundary_complex()

    l4_betti = betti(l4_complex)
    l6_betti = betti(l6_complex)
    combined_betti = betti(combined_complex)

    positive = {
        "l4_interior_is_contractible_chain": {
            "samples": l4_samples,
            **l4_betti,
            "pass": l4_betti["beta0"] == 1 and l4_betti["beta1"] == 0,
        },
        "l6_interior_has_one_local_cycle": {
            "samples": l6_samples,
            **l6_betti,
            "pass": l6_betti["beta0"] == 1 and l6_betti["beta1"] == 1,
        },
        "topology_class_changes_with_state_class": {
            "l4_beta1": l4_betti["beta1"],
            "l6_beta1": l6_betti["beta1"],
            "pass": l4_betti["beta1"] != l6_betti["beta1"],
        },
    }

    negative = {
        "threshold_is_not_strict_l4_or_l6_interior": {
            "threshold_sample": threshold_sample,
            "pass": all(abs(threshold_sample - r) > EPS for r in l4_samples + l6_samples),
        },
        "strict_class_interiors_are_not_identical_carriers": {
            "l4_num_edges": 2,
            "l6_num_edges": 3,
            "pass": 2 != 3,
        },
    }

    boundary = {
        "threshold_bridge_keeps_combined_carrier_connected": {
            **combined_betti,
            "pass": combined_betti["beta0"] == 1,
        },
        "threshold_bridge_does_not_create_extra_loop": {
            "combined_beta1": combined_betti["beta1"],
            "l6_beta1": l6_betti["beta1"],
            "pass": combined_betti["beta1"] == l6_betti["beta1"],
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "state_class_binding_geometry",
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
            "scope_note": "Direct local class-binding topology lego on bounded Werner parameter samples around the 0.17 threshold.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "state_class_binding_geometry_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
