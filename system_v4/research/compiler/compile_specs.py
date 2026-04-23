#!/usr/bin/env python3
"""
Research Compiler — Codex Ratchet
===================================
Compiles YAML problem specs into executable sim configs and constraint
summaries. This is the "front end" of the automated research pipeline:

  YAML spec → Compiler → (sim config, constraints, scoring rules)
                       → Runner → Evidence tokens → Graph
"""

import yaml
import json
import os
import sys
from pathlib import Path
from datetime import datetime, UTC

RESEARCH_DIR = Path(__file__).resolve().parent.parent
SPECS_DIR = RESEARCH_DIR / "problem_specs"
PROBES_DIR = RESEARCH_DIR.parent / "probes"
RESULTS_DIR = PROBES_DIR / "a2_state" / "sim_results"


def load_problem_specs(spec_file=None):
    """Load all problem specs from YAML files."""
    if spec_file:
        files = [Path(spec_file)]
    else:
        files = list(SPECS_DIR.glob("*.yaml"))

    problems = []
    for f in files:
        with open(f) as fh:
            content = fh.read()
        # Split multi-document YAML
        for doc in content.split("---"):
            doc = doc.strip()
            if not doc:
                continue
            try:
                spec = yaml.safe_load(doc)
                if spec and "problem_id" in spec:
                    spec["_source_file"] = str(f)
                    problems.append(spec)
            except yaml.YAMLError as e:
                print(f"  WARN: Failed to parse YAML in {f}: {e}")
    return problems


def compile_problem(spec):
    """Compile a single problem spec into a runnable config."""
    config = {
        "problem_id": spec["problem_id"],
        "goal": spec["goal"],
        "sim_file": spec.get("sim_file", ""),
        "sim_path": str(PROBES_DIR / spec.get("sim_file", "")),
        "result_artifact": str(RESULTS_DIR / spec.get("result_artifact", "")),
        "constraints": spec.get("constraints", []),
        "scoring": spec.get("scoring", {}),
        "negative_tests": spec.get("negative_tests", []),
        "witness": spec.get("witness", {}),
        "status": spec.get("status", "UNKNOWN"),
        "executable": (PROBES_DIR / spec.get("sim_file", "")).exists(),
    }
    return config


def compile_all(spec_file=None):
    """Compile all problem specs and produce a manifest."""
    problems = load_problem_specs(spec_file)
    print(f"{'='*72}")
    print(f"RESEARCH COMPILER — Codex Ratchet")
    print(f"  Specs loaded: {len(problems)}")
    print(f"{'='*72}")

    manifest = []
    for spec in problems:
        config = compile_problem(spec)
        executable = "✓" if config["executable"] else "✗"
        print(f"  [{executable}] {config['problem_id']:35s}  "
              f"sim={config['sim_file']:45s}  status={config['status']}")
        manifest.append(config)

    # Summary
    n_executable = sum(1 for c in manifest if c["executable"])
    n_solved = sum(1 for c in manifest if c["status"] == "SOLVED")
    print(f"\n  Executable: {n_executable}/{len(manifest)}")
    print(f"  Solved: {n_solved}/{len(manifest)}")

    # Write manifest
    os.makedirs(str(RESULTS_DIR), exist_ok=True)
    outpath = RESULTS_DIR / "research_manifest.json"
    with open(str(outpath), "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "n_problems": len(manifest),
            "n_executable": n_executable,
            "n_solved": n_solved,
            "problems": manifest,
        }, f, indent=2)
    print(f"  Manifest saved: {outpath}")

    return manifest


if __name__ == "__main__":
    compile_all()
