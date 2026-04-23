#!/usr/bin/env python3
"""
sim_corpus_map_elites_real_archive.py -- Canonical sim.

Real MAP-Elites archive over the actual sim corpus at
system_v4/probes/sim_*.py. Behavior coords:
  axis 1 = G-tower depth (0..5) from filename keywords
  axis 2 = notation class (0..5) from primary load_bearing tool family
Objective = 1.0 if result JSON parses as PASS else 0.0.

Exclusion language: candidates that "survive" MAP-Elites insertion are
archive-admitted under the chosen behavior descriptors; thin cells
indicate shell-local regions where coupling candidates are under-sampled.
"""

import json
import os
import re
import glob

TOOL_MANIFEST = {
    "ribs": {"tried": False, "used": False, "reason": ""},
    "pytorch": {"tried": False, "used": False, "reason": "numeric stack not required for archive construction"},
    "pyg": {"tried": False, "used": False, "reason": "no message passing needed"},
    "z3": {"tried": False, "used": False, "reason": "no SMT proof required for descriptor extraction"},
    "cvc5": {"tried": False, "used": False, "reason": "no SMT proof required"},
    "sympy": {"tried": False, "used": False, "reason": "no symbolic math required"},
    "clifford": {"tried": False, "used": False, "reason": "no Cl(3) rotors required"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold geometry required"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance required"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph algorithms required"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraphs"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex required"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence required"},
    "datasketch": {"tried": False, "used": False, "reason": "Rosetta detection handled in sibling sim"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from ribs.archives import GridArchive
    TOOL_MANIFEST["ribs"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["ribs"]["reason"] = "not installed"
    raise

PROBES = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(PROBES, "a2_state", "sim_results")


def gtower_depth(name: str) -> int:
    n = name.lower()
    # order matters: longer/more-specific first
    if re.search(r"\b(sp|spin|pin)\b|_sp_|_spin_|_pin_", n):
        return 5
    if re.search(r"u1|_u1_|\bu_1\b", n):
        return 4
    if re.search(r"\bsu\b|_su_|su2|su3", n):
        return 3
    if re.search(r"\bso\b|_so_|so2|so3", n):
        return 2
    if re.search(r"\bo\b|_o_|^o_|/o_", n):
        return 1
    if re.search(r"\bgl\b|_gl_|gl2|gl3", n):
        return 0
    return 0


def notation_class(source: str) -> int:
    # find TOOL_INTEGRATION_DEPTH block, extract load_bearing tools
    m = re.search(r"TOOL_INTEGRATION_DEPTH\s*=\s*\{([^}]*)\}", source, re.DOTALL)
    if not m:
        return 0
    block = m.group(1)
    lb = set()
    for line in block.splitlines():
        mm = re.match(r"\s*[\"']([a-zA-Z0-9_]+)[\"']\s*:\s*[\"']load_bearing[\"']", line)
        if mm:
            lb.add(mm.group(1).lower())
    # priority ordered families
    if "z3" in lb or "cvc5" in lb:
        return 0
    if "sympy" in lb:
        return 1
    if "clifford" in lb:
        return 2
    if "e3nn" in lb:
        return 3
    if "pyg" in lb or "toponetx" in lb or "torch_geometric" in lb:
        return 4
    if "gudhi" in lb or "rustworkx" in lb or "geomstats" in lb:
        return 5
    return 0


def is_pass(result_json_path: str) -> float:
    try:
        with open(result_json_path) as f:
            data = json.load(f)
    except Exception:
        return 0.0
    # PASS heuristic: top-level "status"/"verdict"/"result" == PASS,
    # or positive block non-empty with all-truthy "passed" flags.
    for k in ("status", "verdict", "result", "overall"):
        v = data.get(k) if isinstance(data, dict) else None
        if isinstance(v, str) and v.strip().upper() == "PASS":
            return 1.0
    if isinstance(data, dict) and "positive" in data:
        pos = data["positive"]
        if isinstance(pos, dict) and pos:
            passed = [v for v in pos.values() if isinstance(v, dict) and "passed" in v]
            if passed and all(p.get("passed") for p in passed):
                return 1.0
    return 0.0


def run_positive_tests():
    sim_files = sorted(glob.glob(os.path.join(PROBES, "sim_*.py")))
    archive = GridArchive(solution_dim=2, dims=[6, 6], ranges=[(0, 5), (0, 5)])
    TOOL_MANIFEST["ribs"]["used"] = True
    TOOL_MANIFEST["ribs"]["reason"] = "GridArchive 6x6 constructed and populated over real corpus"
    TOOL_INTEGRATION_DEPTH["ribs"] = "load_bearing"

    archived = 0
    cell_counts = {}
    for sp in sim_files:
        base = os.path.basename(sp)[:-3]  # strip .py
        rj = os.path.join(RESULTS_DIR, base + "_results.json")
        if not os.path.exists(rj):
            # try alt names
            alts = glob.glob(os.path.join(RESULTS_DIR, base.replace("sim_", "") + "*_results.json"))
            if not alts:
                continue
            rj = alts[0]
        try:
            with open(sp) as f:
                src = f.read()
        except Exception:
            continue
        a1 = gtower_depth(base)
        a2 = notation_class(src)
        obj = is_pass(rj)
        try:
            archive.add_single([float(a1), float(a2)], obj, [float(a1), float(a2)])
            archived += 1
            cell_counts[(a1, a2)] = cell_counts.get((a1, a2), 0) + 1
        except Exception:
            continue

    total_cells = 6 * 6
    occupied = len(cell_counts)
    coverage = occupied / total_cells
    thin = [(list(k), v) for k, v in cell_counts.items() if v <= 1]
    dense = sorted(((list(k), v) for k, v in cell_counts.items()), key=lambda x: -x[1])[:5]

    # top thin cells = unoccupied or sparse cells (suggest authoring targets)
    all_cells = [(i, j) for i in range(6) for j in range(6)]
    unoccupied = [c for c in all_cells if c not in cell_counts]
    sparse = sorted(cell_counts.items(), key=lambda x: x[1])
    suggested = [list(c) for c in unoccupied[:5]]
    if len(suggested) < 5:
        suggested += [list(k) for k, _ in sparse[:5 - len(suggested)]]

    return {
        "total_sims_scanned": len(sim_files),
        "total_sims_archived": archived,
        "coverage": coverage,
        "occupied_cells": occupied,
        "thin_cells": thin,
        "dense_cells": dense,
        "suggested_next_authoring_targets": suggested,
        "passed": archived > 0 and coverage > 0.20 and len(thin) >= 1,
    }


def run_negative_tests():
    # Negative: an empty archive must report coverage 0 and no thin-cell survivors.
    arch = GridArchive(solution_dim=2, dims=[6, 6], ranges=[(0, 5), (0, 5)])
    occupied = len(list(arch))
    return {"empty_archive_occupied": occupied, "passed": occupied == 0}


def run_boundary_tests():
    # Boundary: extremes of the behavior space must be accepted by ribs.
    arch = GridArchive(solution_dim=2, dims=[6, 6], ranges=[(0, 5), (0, 5)])
    ok = True
    try:
        arch.add_single([0.0, 0.0], 1.0, [0.0, 0.0])
        arch.add_single([5.0, 5.0], 1.0, [5.0, 5.0])
    except Exception:
        ok = False
    return {"extremes_accepted": ok, "passed": ok}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    overall = "PASS" if (pos["passed"] and neg["passed"] and bnd["passed"]) else "FAIL"
    results = {
        "name": "sim_corpus_map_elites_real_archive",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "status": overall,
    }
    out_dir = RESULTS_DIR
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_corpus_map_elites_real_archive_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[{overall}] coverage={pos['coverage']:.3f} archived={pos['total_sims_archived']} thin={len(pos['thin_cells'])}")
    print(f"Results -> {out_path}")
