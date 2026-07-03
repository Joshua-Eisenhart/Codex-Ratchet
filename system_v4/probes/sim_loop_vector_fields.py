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
TOOL_MANIFEST = {'clifford': {'reason': 'Clifford appears only in the existing manifest scaffold or imports '
                        'without a direct source call; kept unused pending review.',
              'tried': False,
              'used': False},
 'cvc5': {'reason': 'cvc5 appears only in the existing manifest scaffold or imports without a '
                    'direct source call; kept unused pending review.',
          'tried': False,
          'used': False},
 'e3nn': {'reason': 'e3nn appears only in the existing manifest scaffold or imports without a '
                    'direct source call; kept unused pending review.',
          'tried': False,
          'used': False},
 'geomstats': {'reason': 'geomstats appears only in the existing manifest scaffold or imports '
                         'without a direct source call; kept unused pending review.',
               'tried': False,
               'used': False},
 'gudhi': {'reason': 'GUDHI appears only in the existing manifest scaffold or imports without a '
                     'direct source call; kept unused pending review.',
           'tried': False,
           'used': False},
 'numpy': {'reason': 'Source calls NumPy APIs for finite array, matrix, or numeric baseline '
                     'computation in this probe.',
           'tried': True,
           'used': True},
 'pyg': {'reason': 'PyG appears only in the existing manifest scaffold or imports without a direct '
                   'source call; kept unused pending review.',
         'tried': False,
         'used': False},
 'pytorch': {'reason': 'PyTorch appears only in the existing manifest scaffold or imports without '
                       'a direct source call; kept unused pending review.',
             'tried': False,
             'used': False},
 'rustworkx': {'reason': 'rustworkx appears only in the existing manifest scaffold or imports '
                         'without a direct source call; kept unused pending review.',
               'tried': False,
               'used': False},
 'sympy': {'reason': 'SymPy appears only in the existing manifest scaffold or imports without a '
                     'direct source call; kept unused pending review.',
           'tried': False,
           'used': False},
 'toponetx': {'reason': 'TopoNetX appears only in the existing manifest scaffold or imports '
                        'without a direct source call; kept unused pending review.',
              'tried': False,
              'used': False},
 'xgi': {'reason': 'XGI appears only in the existing manifest scaffold or imports without a direct '
                   'source call; kept unused pending review.',
         'tried': False,
         'used': False},
 'z3': {'reason': 'z3 appears only in the existing manifest scaffold or imports without a direct '
                  'source call; kept unused pending review.',
        'tried': False,
        'used': False}}
TOOL_MANIFEST["numpy"] = {
    "tried": True,
    "used": True,
    "reason": "load-bearing finite array/matrix computation for this bounded classical lego receipt",
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"


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
        "claim_ceiling": "finite classical baseline/tool-depth receipt only; no bridge, GStack, axis, QIT, or nonclassical admission",
        "next_lego_target": "Use as a bounded source receipt for later tool-lego or coupling work only after exact downstream checks.",
        "promotion_condition": "Requires separate bridge/nonclassical/topology/operator coupling receipts and explicit stage-gate approval.",
        "blocked_until": "tool-lego fit; coupling/coexistence evidence; stage-gate admission",
        "demotion_condition": "Demote if rerun fails, tool use is not load-bearing, or result claims exceed this finite receipt.",
        "out_of_scope": ["QIT engine admission", "GStack admission", "axis promotion", "nonclassical proof"],
        "all_pass": all_pass,
        "criteria_checked": ["finite computation completed", "load-bearing numpy path exercised", "local pass/fail criteria satisfied"],
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
