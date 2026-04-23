#!/usr/bin/env python3
"""Classical baseline: placement_law.
A 'placement law' = deterministic map from (site index, label) -> coordinate
on a lattice. Tests injectivity, translation equivariance, and conflict detection."""
import json, os, numpy as np
from _classical_baseline_common import TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH
classification = "classical_baseline"
NAME = "placement_law"

def place(site, label, L=8):
    # simple deterministic placement on L x L grid
    i = site % L; j = (site // L) % L
    return np.array([i, j]) + 0.1 * np.array([label % 3, (label // 3) % 3])

def run_positive_tests():
    r = {}
    # injectivity on small catalog
    coords = {}; inj = True
    for s in range(16):
        for lab in range(4):
            c = tuple(place(s, lab))
            if c in coords: inj = False
            coords[c] = (s, lab)
    r["injective_16x4"] = inj
    # translation equivariance: shifting site by L rows shifts y-coord predictably
    c0 = place(0, 0); c1 = place(8, 0)
    r["translation_equivariant"] = bool(np.allclose(c1 - c0, [0, 1]))
    # deterministic
    r["deterministic"] = bool(np.allclose(place(5, 2), place(5, 2)))
    return r

def run_negative_tests():
    r = {}
    # mismatched placement (two laws assigning same coord) -> conflict
    def bad_place(s, lab): return np.array([s % 4, 0.0])  # collapses label info
    coords = {}; collision = False
    for s in range(8):
        for lab in range(2):
            c = tuple(bad_place(s, lab))
            if c in coords: collision = True
            coords[c] = 1
    r["bad_law_has_collision"] = collision
    # different law -> different coords
    r["laws_distinguishable"] = bool(not np.allclose(place(3, 1), bad_place(3, 1)))
    return r

def run_boundary_tests():
    r = {}
    # L=1 degenerate
    c = place(0, 0, L=1)
    r["L1_finite"] = bool(np.all(np.isfinite(c)))
    # large site wraps modulo L
    r["wrap_mod_L"] = bool(np.allclose(place(0, 0, L=8), place(64, 0, L=8)))
    return r

if __name__ == "__main__":
    results = {"name": NAME, "classification": "classical_baseline",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": run_positive_tests(), "negative": run_negative_tests(),
               "boundary": run_boundary_tests(),
               "classical_captured": "injective deterministic lattice placement, translation equivariance",
               "innately_missing": "constraint-admissible placement, probe-dependent legal-placement set"}
    results["all_pass"] = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results", f"{NAME}_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"all_pass={results['all_pass']} -> {out}")
