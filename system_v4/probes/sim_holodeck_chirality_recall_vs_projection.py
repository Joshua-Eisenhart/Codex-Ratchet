#!/usr/bin/env python3
"""sim_holodeck_chirality_recall_vs_projection.

Thesis: recall direction (carrier -> observer) is not the same chirality
as projection direction (observer -> carrier). We model recall as a
rotor R and projection as R's reverse R~; test that they are distinct
unless the rotor is its own reverse (i.e. trivial/pi rotation).
"""
import numpy as np
import sys, os
from clifford import Cl
classification = "classical_baseline"  # auto-backfill
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _holodeck_common import build_manifest, write_results, summary_ok

layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
e12, e23, e31 = blades['e12'], blades['e23'], blades['e13']

TOOL_MANIFEST = build_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
TOOL_MANIFEST["clifford"]["used"] = True
TOOL_MANIFEST["clifford"]["reason"] = "rotor and reverse chirality"
TOOL_MANIFEST["numpy"]["used"] = True
TOOL_MANIFEST["numpy"]["reason"] = "angle arithmetic"


def rotor(angle, bivector):
    return np.cos(angle / 2) - np.sin(angle / 2) * bivector


def apply_rotor(R, v):
    return R * v * ~R


def run_positive_tests():
    r = {}
    theta = 0.7
    R = rotor(theta, e12)
    v = 1.0 * e1
    v_recall = apply_rotor(R, v)
    v_proj = apply_rotor(~R, v)
    # recall and projection differ for non-involutive rotor
    diff = (v_recall - v_proj).clean()
    r["recall_ne_projection"] = float(abs(diff)) > 1e-6
    # two recalls compose
    v_double = apply_rotor(R, v_recall)
    v_direct = apply_rotor(rotor(2 * theta, e12), v)
    r["composition"] = float(abs((v_double - v_direct).clean())) < 1e-6
    return r


def run_negative_tests():
    r = {}
    # Claim: recall == projection for arbitrary rotor (should be False)
    R = rotor(0.9, e12)
    v = 1.0 * e1
    r["recall_eq_projection_claim"] = float(abs((apply_rotor(R, v) - apply_rotor(~R, v)).clean())) < 1e-9
    return r


def run_boundary_tests():
    r = {}
    # identity rotor: recall == projection (both identity)
    R = rotor(0.0, e12)
    v = 1.0 * e2
    r["identity_rotor_same"] = float(abs((apply_rotor(R, v) - apply_rotor(~R, v)).clean())) < 1e-9
    # pi rotation: R = -bivector; R~ = +bivector; R v R~ = R~ v R (same action on perpendicular vec)
    R_pi = rotor(np.pi, e12)
    v = 1.0 * e3
    r["pi_rotation_same"] = float(abs((apply_rotor(R_pi, v) - apply_rotor(~R_pi, v)).clean())) < 1e-6
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_holodeck_chirality_recall_vs_projection",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["pass"] = summary_ok(results)
    path = write_results("sim_holodeck_chirality_recall_vs_projection", results)
    print(f"pass={results['pass']} -> {path}")
    sys.exit(0 if results["pass"] else 1)
