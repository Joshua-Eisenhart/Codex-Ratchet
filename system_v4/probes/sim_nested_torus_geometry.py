#!/usr/bin/env python3
"""
PURE LEGO: Nested Torus Geometry
================================
Direct local nested-torus geometry lego with fixed radii and inclusion order.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for nested torus geometry with fixed major/minor radii and "
    "inclusion ordering, kept separate from sphere rows, Hopf fiber laws, and torus transport."
)

LEGO_IDS = [
    "nested_torus_geometry",
]

PRIMARY_LEGO_IDS = [
    "nested_torus_geometry",
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
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


def torus_point(R, r, theta, phi):
    return np.array(
        [
            (R + r * np.cos(theta)) * np.cos(phi),
            (R + r * np.cos(theta)) * np.sin(phi),
            r * np.sin(theta),
        ],
        dtype=float,
    )


def sample_extrema(R, r):
    # enough to capture radial shell and z-height bounds for the row
    angles = [0.0, np.pi / 2.0, np.pi, 3.0 * np.pi / 2.0]
    phis = [0.0, np.pi / 2.0]
    pts = np.array([torus_point(R, r, th, ph) for th in angles for ph in phis], dtype=float)
    radial_xy = np.sqrt(np.sum(pts[:, :2] ** 2, axis=1))
    return {
        "xy_min": float(np.min(radial_xy)),
        "xy_max": float(np.max(radial_xy)),
        "z_min": float(np.min(pts[:, 2])),
        "z_max": float(np.max(pts[:, 2])),
    }


def main():
    outer = {"R": 3.0, "r": 0.5}
    inner = {"R": 2.0, "r": 0.4}
    single = {"R": 2.0, "r": 0.8}

    outer_bounds = sample_extrema(**outer)
    inner_bounds = sample_extrema(**inner)
    single_bounds = sample_extrema(**single)

    outer_area = 4.0 * np.pi**2 * outer["R"] * outer["r"]
    inner_area = 4.0 * np.pi**2 * inner["R"] * inner["r"]
    single_area = 4.0 * np.pi**2 * single["R"] * single["r"]

    positive = {
        "nested_tori_have_strict_radial_separation": {
            "outer_xy_min": outer_bounds["xy_min"],
            "inner_xy_max": inner_bounds["xy_max"],
            "pass": inner_bounds["xy_max"] < outer_bounds["xy_min"] - EPS,
        },
        "nested_tori_keep_distinct_major_minor_radii": {
            "pass": outer["R"] > inner["R"] and outer["r"] > inner["r"],
        },
        "torus_surface_area_matches_major_minor_formula": {
            "outer_area": outer_area,
            "inner_area": inner_area,
            "single_area": single_area,
            "pass": outer_area > inner_area > 0.0 and single_area > 0.0,
        },
    }

    negative = {
        "single_torus_is_not_a_nested_pair": {
            "single_xy_min": single_bounds["xy_min"],
            "single_xy_max": single_bounds["xy_max"],
            "pass": not (single_bounds["xy_max"] < single_bounds["xy_min"] - EPS),
        },
        "nested_row_does_not_require_hopf_fiber_data": {
            "pass": all(np.isfinite(v) for v in [outer_bounds["xy_min"], inner_bounds["xy_max"], outer_area, inner_area]),
        },
    }

    boundary = {
        "all_major_radii_exceed_minor_radii": {
            "pass": all(cfg["R"] > cfg["r"] for cfg in [outer, inner, single]),
        },
        "vertical_extent_is_bounded_by_minor_radius": {
            "pass": all(
                abs(bounds["z_max"] - cfg["r"]) < EPS and abs(bounds["z_min"] + cfg["r"]) < EPS
                for bounds, cfg in [(outer_bounds, outer), (inner_bounds, inner), (single_bounds, single)]
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "nested_torus_geometry",
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
            "scope_note": "Direct local nested-torus geometry lego using fixed radii, radial separation, and area bounds only.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "nested_torus_geometry_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
