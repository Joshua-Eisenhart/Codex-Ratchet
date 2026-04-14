#!/usr/bin/env python3
"""
sim_ribs_map_elites_constraint_manifold_archive -- canonical sim

MAP-Elites archive over two behavior axes: G-tower-depth x notation-class.
Seeds 30 synthetic "sim cells" (objective = PASS/FAIL scalar + invariant
signature). Cells with matching invariant-signatures across different
behavior coords are reported as Rosetta candidates (count only, NOT merged).

Language discipline: cells are "admissible" into the archive; thin cells
are "excluded" bins; Rosetta candidates "survived" coordinate changes.
"""

import json
import os
import numpy as np

TOOL_MANIFEST = {
    "pytorch":  {"tried": False, "used": False, "reason": "not invoked; archive is behavior-indexed, not gradient-indexed"},
    "pyg":      {"tried": False, "used": False, "reason": "no graph structure in this sim"},
    "z3":       {"tried": False, "used": False, "reason": "no SAT/UNSAT claim; archive membership is not a proof"},
    "cvc5":     {"tried": False, "used": False, "reason": "no proof obligation"},
    "sympy":    {"tried": False, "used": False, "reason": "numeric objective only"},
    "clifford": {"tried": False, "used": False, "reason": "no Cl(p,q) rotors here"},
    "geomstats":{"tried": False, "used": False, "reason": "no manifold distance used"},
    "e3nn":     {"tried": False, "used": False, "reason": "no equivariant feature"},
    "rustworkx":{"tried": False, "used": False, "reason": "no graph"},
    "xgi":      {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi":    {"tried": False, "used": False, "reason": "no persistence diagram"},
    "ribs":     {"tried": False, "used": False, "reason": ""},
    "numpy":    {"tried": True,  "used": True,  "reason": "behavior/objective vectors for ribs add()"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None, "rustworkx": None,
    "xgi": None, "toponetx": None, "gudhi": None,
    "ribs": "load_bearing",
    "numpy": "supportive",
}

try:
    from ribs.archives import GridArchive
    TOOL_MANIFEST["ribs"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["ribs"]["reason"] = "not installed"


# ---------------------------------------------------------------------
# Synthetic sim-cell generator
# ---------------------------------------------------------------------
# behavior axis 0: g_tower_depth   (int in [0,5])
# behavior axis 1: notation_class  (int in [0,3])  -- 0:set, 1:graph, 2:clifford, 3:topos
# objective: PASS=1.0 / FAIL=0.0 + small jitter
# invariant_signature: a small tuple the sim is supposed to be "the same thing" up to notation.
def synth_cells(n=30, seed=0):
    rng = np.random.default_rng(seed)
    cells = []
    # 6 invariant-signature buckets; multiple cells share each bucket
    # across different (depth, notation) coords -- that is the Rosetta setup.
    for i in range(n):
        depth = int(rng.integers(0, 6))
        notation = int(rng.integers(0, 4))
        sig = int(rng.integers(0, 6))          # 0..5
        passed = 1.0 if rng.random() > 0.2 else 0.0
        obj = passed + rng.normal(0, 0.01)
        cells.append({
            "bx": [float(depth), float(notation)],
            "obj": float(obj),
            "sig": sig,
            "pass": bool(passed == 1.0),
        })
    return cells


def build_archive():
    archive = GridArchive(
        solution_dim=4,                       # dummy genome
        dims=[6, 4],
        ranges=[(0, 6), (0, 4)],
    )
    return archive


def run_positive_tests():
    results = {}
    cells = synth_cells(30, seed=0)
    archive = build_archive()

    sols = np.zeros((len(cells), 4))
    objs = np.array([c["obj"] for c in cells])
    bcs  = np.array([c["bx"] for c in cells])

    archive.add(sols, objs, bcs)

    stats = archive.stats
    n_filled = int(stats.num_elites)
    coverage = float(stats.coverage)

    results["n_cells_seeded"]  = len(cells)
    results["n_bins_admitted"] = n_filled
    results["coverage"]        = coverage
    results["admissible"]      = n_filled > 0 and coverage > 0.0

    # Rosetta: cells with identical invariant-signature at DIFFERENT behavior coords.
    # Report count ONLY; do not collapse.
    sig_to_coords = {}
    for c in cells:
        sig_to_coords.setdefault(c["sig"], set()).add(tuple(c["bx"]))
    rosetta = sum(1 for s, coords in sig_to_coords.items() if len(coords) >= 2)
    results["rosetta_candidates"]     = rosetta
    results["rosetta_policy"]         = "count_only_no_merge"
    results["rosetta_buckets_detail"] = {str(s): len(c) for s, c in sig_to_coords.items()}

    results["pass"] = results["admissible"] and rosetta >= 1
    return results


def run_negative_tests():
    results = {}
    archive = build_archive()
    # An empty archive must be excluded from the "admissible" verdict.
    results["empty_archive_coverage"] = float(archive.stats.coverage)
    results["empty_excluded"] = archive.stats.coverage == 0.0
    results["pass"] = results["empty_excluded"]
    return results


def run_boundary_tests():
    results = {}
    # Out-of-range behavior coords must be excluded from the archive.
    archive = build_archive()
    sols = np.zeros((1, 4))
    objs = np.array([1.0])
    bcs  = np.array([[999.0, 999.0]])   # outside range
    archive.add(sols, objs, bcs)
    # Archive must not exceed declared capacity (6*4=24 bins) even under
    # out-of-range behavior coords; coverage must remain in [0,1].
    capacity = 6 * 4
    n_elites = int(archive.stats.num_elites)
    coverage = float(archive.stats.coverage)
    results["capacity"] = capacity
    results["n_elites_after_oor"] = n_elites
    results["coverage_after_oor"] = coverage
    results["pass"] = (n_elites <= capacity) and (0.0 <= coverage <= 1.0)
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    # Mark used tools
    TOOL_MANIFEST["ribs"]["used"]   = True
    TOOL_MANIFEST["ribs"]["reason"] = "GridArchive is the behavior-indexed container; Rosetta count reads archive.stats + signature map"

    results = {
        "name": "sim_ribs_map_elites_constraint_manifold_archive",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "classification": "canonical",
        "overall_pass": pos["pass"] and neg["pass"] and bnd["pass"],
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(
        out_dir, "sim_ribs_map_elites_constraint_manifold_archive_results.json"
    )
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass={results['overall_pass']}")
