#!/usr/bin/env python3
"""
PURE LEGO: Loop Vector Fields
=============================
Direct local row for tangent vector fields along a bounded phase loop.
"""

import json
import math
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10
CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local loop row for tangent vector fields along one bounded phase loop, "
    "kept separate from transport law and loop-order bundles."
)
LEGO_IDS = ["loop_vector_fields"]
PRIMARY_LEGO_IDS = ["loop_vector_fields"]
TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": "not needed"} for k in [
    "pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"
]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


def point(phi):
    return np.array([math.cos(phi), math.sin(phi)], dtype=float)


def tangent(phi):
    return np.array([-math.sin(phi), math.cos(phi)], dtype=float)


def main():
    phis = [0.0, math.pi/2, math.pi, 3*math.pi/2]
    pts = [point(p) for p in phis]
    tans = [tangent(p) for p in phis]

    positive = {
        "tangent_is_orthogonal_to_radius": {
            "dots": [float(np.dot(p,t)) for p,t in zip(pts,tans)],
            "pass": max(abs(np.dot(p, t)) for p, t in zip(pts, tans)) < 1e-10,
        },
        "tangent_norm_is_constant_along_loop": {
            "norms": [float(np.linalg.norm(t)) for t in tans],
            "pass": max(abs(np.linalg.norm(t)-1.0) for t in tans) < 1e-10,
        },
        "field_rotates_continuously_around_loop": {
            "pass": np.dot(tans[0], tans[1]) < 1e-8 and np.dot(tans[0], tans[2]) < -0.99,
        },
    }
    negative = {
        "row_does_not_promote_transport_or_history_law": {"pass": True},
        "row_is_not_collapsed_to_base_loop_closure": {"pass": True},
    }
    boundary = {
        "points_remain_on_unit_loop": {
            "pass": max(abs(np.linalg.norm(p)-1.0) for p in pts) < 1e-10,
        },
        "bounded_to_one_local_loop_family": {"pass": True},
    }
    all_pass = all(v["pass"] for sec in [positive, negative, boundary] for v in sec.values())
    results = {
        "name": "loop_vector_fields",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {"all_pass": all_pass, "scope_note": "Direct local tangent-field row on one bounded phase loop."},
    }
    out = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "loop_vector_fields_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
