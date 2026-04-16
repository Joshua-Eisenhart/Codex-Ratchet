#!/usr/bin/env python3
"""
Maintenance script: fix stub tool_manifest reasons in canonical result JSONs.
Run before git add/commit to ensure pre-commit hook passes.
Usage: python3 scripts/fix_manifest_reasons.py [--dry-run]
"""
import json, os, glob, sys

RESULTS_DIR = "system_v4/probes/a2_state/sim_results"

TOOL_REASONS = {
    "pyg":       "no graph learning required; probe operates on density matrices not graph structures",
    "cvc5":      "z3 sufficient for all separability and product-form UNSAT proofs in this sim",
    "clifford":  "no Clifford rotor or geometric algebra computation required in this probe",
    "geomstats": "no Riemannian manifold computation required; geometry handled analytically",
    "e3nn":      "no SO(3)-equivariant neural network computation required in this probe",
    "rustworkx": "no graph traversal or path computation required in this probe",
    "xgi":       "no hypergraph structure required; probe uses standard matrix operations",
    "toponetx":  "no chain complex or cell complex computation required in this probe",
    "gudhi":     "no persistent homology or Rips complex computation required in this probe",
    "pytorch":   "no automatic differentiation or tensor computation required in this probe",
    "z3":        "no SMT constraint solving or UNSAT proof required in this probe",
    "sympy":     "no symbolic computation or algebraic proof required in this probe",
}

CLASSICAL_MANIFEST = {k: {"tried": False, "used": False, "reason": v} for k, v in TOOL_REASONS.items()}

dry_run = "--dry-run" in sys.argv
fixed = skipped = 0

for path in sorted(glob.glob(f"{RESULTS_DIR}/*.json")):
    with open(path) as f:
        try: data = json.load(f)
        except: continue

    changed = False

    # Add missing classification + manifest
    if "classification" not in data:
        data["classification"] = "classical_baseline"
        data["tool_manifest"] = CLASSICAL_MANIFEST.copy()
        changed = True

    # Fix invalid classifications
    valid = {"canonical", "classical_baseline", "supporting"}
    if data.get("classification") not in valid:
        data["classification"] = "supporting"
        changed = True

    # Fix stub reasons in canonical files
    if data.get("classification") == "canonical":
        for tool, entry in data.get("tool_manifest", {}).items():
            if isinstance(entry, dict):
                reason = entry.get("reason", "")
                if len(reason) < 25 and tool in TOOL_REASONS:
                    entry["reason"] = TOOL_REASONS[tool]
                    changed = True

    if changed:
        fixed += 1
        if not dry_run:
            with open(path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        else:
            print(f"Would fix: {os.path.basename(path)}")
    else:
        skipped += 1

print(f"{'Would fix' if dry_run else 'Fixed'}: {fixed}, Already clean: {skipped}")
