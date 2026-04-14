#!/usr/bin/env python3
"""
Unclassified result triage — scans sim_results/ for files missing classification.

Reports:
  - Total unclassified results
  - Breakdown by category (pure_lego, lego, negative, other)
  - Size tiers (tiny/medium/large)
  - Whether they have real test data, summaries, or numeric evidence
  - Suggests classification candidates based on content heuristics

Exit code 1 if any unclassified results contain structured test data
(i.e., results that probably SHOULD be classified but aren't).
"""

import json
import glob
import os
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
PROBES_DIR = SCRIPT_DIR


def categorize_name(name: str) -> str:
    stem = name.replace("_results.json", "")
    if "pure_lego" in stem:
        return "pure_lego"
    if stem.startswith("lego_"):
        return "lego"
    if "neg" in stem or "negative" in stem:
        return "negative"
    if "constrain_legos" in stem:
        return "constrain"
    if any(tok in stem for tok in ["bridge", "phi0", "axis0", "kernel", "bakeoff"]):
        return "late_stage"
    return "other"


def has_matching_sim(stem: str) -> bool:
    return (PROBES_DIR / f"sim_{stem}.py").exists()


def analyze_content(data: dict) -> dict:
    """Heuristic content analysis of a result dict."""
    info = {
        "has_summary": "summary" in data,
        "has_tests": "results" in data or "test_results" in data or "tests" in data,
        "has_positive": "positive" in data,
        "has_negative": "negative" in data,
        "has_boundary": "boundary" in data,
        "has_tool_manifest": "tool_manifest" in data or "TOOL_MANIFEST" in data,
        "has_tool_depth": "tool_integration_depth" in data or "TOOL_INTEGRATION_DEPTH" in data,
        "has_numeric": False,
        "has_lego_ids": "lego_ids" in data or "primary_lego_ids" in data,
    }

    # Check for numeric evidence anywhere in the tree
    raw = json.dumps(data)
    # If it has floating-point numbers, it likely has computed results
    import re
    floats = re.findall(r'": -?\d+\.\d{3,}', raw)
    info["has_numeric"] = len(floats) > 5
    info["numeric_count"] = len(floats)

    return info


def suggest_classification(data: dict, info: dict, size: int) -> str:
    """Suggest a classification based on content heuristics."""
    if info["has_positive"] and info["has_negative"] and info["has_tool_manifest"]:
        if info["has_numeric"] and info["numeric_count"] > 20:
            return "SUGGEST: canonical (has pos/neg/tools/numeric)"
        return "SUGGEST: supporting (has structure but thin numeric)"
    if info["has_tests"] and info["has_numeric"]:
        return "SUGGEST: canonical (has tests + numeric)"
    if info["has_summary"] and info["has_numeric"]:
        return "SUGGEST: supporting (has summary + numeric)"
    if size < 500:
        return "SUGGEST: diagnostic_only (tiny file)"
    if info["has_numeric"]:
        return "SUGGEST: supporting (has numeric, missing structure)"
    return "SUGGEST: diagnostic_only (no clear evidence)"


def main() -> int:
    result_files = sorted(RESULTS_DIR.glob("*_results.json"))

    unclassified = []
    for fpath in result_files:
        try:
            data = json.loads(fpath.read_text())
        except Exception:
            continue
        if data.get("classification") is not None:
            continue

        stem = fpath.stem.replace("_results", "")
        size = fpath.stat().st_size
        category = categorize_name(fpath.name)
        has_sim = has_matching_sim(stem)
        info = analyze_content(data)
        suggestion = suggest_classification(data, info, size)

        unclassified.append({
            "file": fpath.name,
            "stem": stem,
            "size": size,
            "category": category,
            "has_sim": has_sim,
            "keys": sorted(data.keys())[:10],
            **info,
            "suggestion": suggestion,
        })

    # ---- Report ----
    print(f"Scanned {len(result_files)} result files in {RESULTS_DIR}")
    print(f"Unclassified: {len(unclassified)}")
    print()

    # By category
    cat_counts = Counter(r["category"] for r in unclassified)
    print("By category:")
    for cat, count in cat_counts.most_common():
        print(f"  {cat}: {count}")
    print()

    # By size tier
    tiny = sum(1 for r in unclassified if r["size"] < 500)
    medium = sum(1 for r in unclassified if 500 <= r["size"] <= 10000)
    large = sum(1 for r in unclassified if r["size"] > 10000)
    print(f"By size: tiny(<500B)={tiny}  medium(0.5-10KB)={medium}  large(>10KB)={large}")
    print()

    # Has matching sim?
    with_sim = sum(1 for r in unclassified if r["has_sim"])
    orphans = sum(1 for r in unclassified if not r["has_sim"])
    print(f"Has matching sim: {with_sim}  Orphan: {orphans}")
    print()

    # Content quality
    with_numeric = sum(1 for r in unclassified if r["has_numeric"])
    with_tests = sum(1 for r in unclassified if r["has_tests"])
    with_pos_neg = sum(1 for r in unclassified if r["has_positive"] and r["has_negative"])
    print(f"Has numeric evidence: {with_numeric}")
    print(f"Has structured tests: {with_tests}")
    print(f"Has pos+neg sections: {with_pos_neg}")
    print()

    # Suggestion breakdown
    sugg_counts = Counter(r["suggestion"].split("(")[0].strip() for r in unclassified)
    print("Suggested classifications:")
    for sugg, count in sugg_counts.most_common():
        print(f"  {sugg}: {count}")
    print()

    # Show top candidates for immediate classification
    candidates = [r for r in unclassified if "canonical" in r["suggestion"]]
    candidates.sort(key=lambda r: -r["size"])
    if candidates:
        print(f"=== TOP CANDIDATES FOR CANONICAL CLASSIFICATION ({len(candidates)}) ===")
        for r in candidates[:20]:
            sim_mark = "✓" if r["has_sim"] else "✗"
            print(f"  {r['size']//1024:4d}KB  {sim_mark} sim  {r['file']}")
        if len(candidates) > 20:
            print(f"  ... +{len(candidates) - 20} more")
        print()

    # Show pure_lego unclassified
    pure_legos = [r for r in unclassified if r["category"] == "pure_lego"]
    if pure_legos:
        print(f"=== UNCLASSIFIED PURE LEGO RESULTS ({len(pure_legos)}) ===")
        for r in pure_legos:
            sim_mark = "✓" if r["has_sim"] else "✗"
            sugg_short = r["suggestion"].split("(")[0].strip()
            print(f"  {r['size']//1024:4d}KB  {sim_mark} sim  {sugg_short:30s}  {r['file']}")
        print()

    # Exit code
    actionable = sum(1 for r in unclassified if r["has_numeric"] and r["has_sim"])
    if actionable > 0:
        print(f"TRIAGE NEEDED: {actionable} unclassified results have numeric data AND a matching sim.")
        return 1
    else:
        print("No high-priority triage items.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
