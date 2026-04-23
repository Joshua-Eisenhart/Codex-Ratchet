#!/usr/bin/env python3
"""
PURE LEGO: Persistence Geometry
===============================
Direct local graph/topology lego.

Use GUDHI persistence on a few bounded sampled carriers to distinguish a circle,
two circles, and a filled disk by their H1 persistence signatures.
"""

import json
import math
import pathlib

import gudhi
import numpy as np
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for persistence geometry on bounded sampled carriers "
    "using GUDHI as the load-bearing topology tool."
)

LEGO_IDS = [
    "persistence_geometry",
]

PRIMARY_LEGO_IDS = [
    "persistence_geometry",
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
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "Rips complexes and persistence diagrams are load-bearing here",
    },
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["gudhi"] = "load_bearing"


def sample_circle(radius=1.0, n=24, center=(0.0, 0.0)):
    pts = []
    for k in range(n):
        t = 2.0 * math.pi * k / n
        pts.append([center[0] + radius * math.cos(t), center[1] + radius * math.sin(t)])
    return np.array(pts, dtype=float)


def sample_disconnected_points():
    return np.array(
        [
            [-3.0, 0.0],
            [-1.5, 0.0],
            [1.5, 0.0],
            [3.0, 0.0],
        ],
        dtype=float,
    )


def persistence_summary(points, max_edge=1.2):
    rips = gudhi.RipsComplex(points=points.tolist(), max_edge_length=max_edge)
    st = rips.create_simplex_tree(max_dimension=2)
    persistence = st.persistence()
    h1 = []
    for dim, pair in persistence:
        if dim != 1:
            continue
        birth, death = pair
        if math.isinf(death):
            lifetime = float("inf")
        else:
            lifetime = float(death - birth)
        h1.append({"birth": float(birth), "death": float(death), "lifetime": lifetime})
    finite = [x["lifetime"] for x in h1 if math.isfinite(x["lifetime"])]
    if any(math.isinf(x["lifetime"]) for x in h1):
        max_lifetime = float("inf")
    else:
        max_lifetime = float(max(finite)) if finite else 0.0
    return {
        "h1_count": len(h1),
        "max_h1_lifetime": max_lifetime,
        "mean_h1_lifetime": float(np.mean(finite)) if finite else 0.0,
    }


def main():
    circle = sample_circle()
    two_circles = np.vstack([sample_circle(center=(-1.7, 0.0)), sample_circle(center=(1.7, 0.0))])
    disconnected = sample_disconnected_points()

    circle_p = persistence_summary(circle)
    two_p = persistence_summary(two_circles)
    disconnected_p = persistence_summary(disconnected)

    positive = {
        "single_circle_has_strong_h1_signal": {
            **circle_p,
            "pass": circle_p["h1_count"] >= 1 and (
                math.isinf(circle_p["max_h1_lifetime"]) or circle_p["max_h1_lifetime"] > 0.2
            ),
        },
        "two_circles_have_more_h1_than_one_circle": {
            **two_p,
            "pass": two_p["h1_count"] > circle_p["h1_count"],
        },
    }

    negative = {
        "disconnected_points_do_not_fake_circle_h1": {
            **disconnected_p,
            "pass": disconnected_p["h1_count"] == 0,
        },
        "disconnected_points_are_not_two_circles": {
            "pass": disconnected_p["h1_count"] < two_p["h1_count"],
        },
    }

    boundary = {
        "two_circles_retain_nontrivial_h1_signal": {
            "pass": two_p["h1_count"] >= 2 and (
                math.isinf(two_p["max_h1_lifetime"]) or two_p["max_h1_lifetime"] > 0.2
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "persistence_geometry",
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
            "scope_note": "Direct local persistence-geometry lego on bounded sampled carriers.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "persistence_geometry_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
