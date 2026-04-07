#!/usr/bin/env python3
"""Regenerate SIM_MANIFEST.json by scanning the actual file tree."""

import json
import os
from collections import Counter
from datetime import date
from pathlib import Path

SIM_DIR = Path(__file__).parent / "a2_state" / "sim_results"
MANIFEST_PATH = SIM_DIR / "SIM_MANIFEST.json"


def classify(filename: str) -> str:
    fn = filename.lower()

    # Order matters: more specific checks first
    if fn.startswith("layer") and "formal" in fn:
        return "formal_canonical"
    if fn.startswith("pure_lego"):
        return "pure_lego"
    if fn.startswith("constrain_legos"):
        return "constraint_filter"
    if "constraint_manifold" in fn:
        return "constraint_manifold"
    if "deep_" in fn:
        return "deep_sim"
    if "entropy_type_sweep" in fn:
        return "entropy_sweep"
    if "evolution" in fn:
        return "cross_field"
    if "fep_compression" in fn:
        return "cross_field"
    if "geometric_engine" in fn or "unified_engine" in fn:
        return "geometric_canonical"
    if "negative" in fn or "ablation" in fn or "propagation" in fn:
        return "negative_battery"
    if fn.startswith("layer"):
        return "legacy_superseded"

    return "numpy_evidence"


def main():
    classifications = {}
    counts = Counter()

    for root, _dirs, files in os.walk(SIM_DIR):
        for fname in sorted(files):
            if not fname.endswith(".json"):
                continue
            if fname == "SIM_MANIFEST.json":
                continue

            full = Path(root) / fname
            # Use path relative to SIM_DIR so subdirectory files are keyed distinctly
            rel = str(full.relative_to(SIM_DIR))
            size = full.stat().st_size
            cls = classify(fname)

            classifications[rel] = {
                "classification": cls,
                "size_bytes": size,
            }
            counts[cls] += 1

    manifest = {
        "manifest_version": str(date.today()),
        "total_files": len(classifications),
        "counts": dict(sorted(counts.items())),
        "classifications": dict(sorted(classifications.items())),
    }

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest written: {MANIFEST_PATH}")
    print(f"Total JSON files catalogued: {len(classifications)}")
    print()
    print("Counts by classification:")
    for cls, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {cls:25s} {n:>4d}")


if __name__ == "__main__":
    main()
