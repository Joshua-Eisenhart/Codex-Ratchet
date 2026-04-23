#!/usr/bin/env python3
"""
Unclassified result triage — scans sim_results/ for files missing classification.

Target tree: system_v4/probes/a2_state/sim_results  (the probe-local tree)
Note: system_v4/a2_state/sim_results is a separate legacy tree (not scanned here).

Reports:
  - Total result files scanned vs parseable vs classified vs unclassified
  - Breakdown by category (pure_lego, lego, negative, other)
  - Size tiers (tiny/medium/large)
  - Whether they have real test data, summaries, or numeric evidence
  - Suggests classification candidates based on content heuristics
  - Flags the secondary result tree for awareness

Exit code 1 if any unclassified results contain structured test data
AND a matching sim file (i.e., actionable triage items).
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PRIMARY_RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
SECONDARY_RESULTS_DIR = SCRIPT_DIR.parent / "a2_state" / "sim_results"
PROBES_DIR = SCRIPT_DIR

# Category tokens: order matters — first match wins
CATEGORY_RULES: list[tuple[str, ...]] = [
    ("pure_lego",),
    ("constrain_legos",),
    ("lego_",),  # non-pure lego (must come after pure_lego and constrain)
]
LATE_STAGE_TOKENS = ("bridge", "phi0", "axis0", "kernel", "bakeoff", "pipeline", "cascade")


def categorize_name(stem: str) -> str:
    """Categorize a result stem into a family bucket."""
    if "pure_lego" in stem:
        return "pure_lego"
    if "constrain_legos" in stem:
        return "constrain"
    if stem.startswith("lego_"):
        return "lego"
    # 'neg' is too broad — matches 'negative' but also 'negentropy', 'negotiate'
    # Use stricter prefix or substring checks:
    if stem.startswith("neg_") or stem.startswith("negative_"):
        return "negative"
    if any(tok in stem for tok in LATE_STAGE_TOKENS):
        return "late_stage"
    return "other"


def has_matching_sim(stem: str) -> bool:
    """Check if a sim_<stem>.py file exists in the probes directory."""
    return (PROBES_DIR / f"sim_{stem}.py").exists()


# Pre-compiled regex for numeric evidence detection.
# Matches JSON values that are floats with 3+ decimal digits,
# which indicates computed (not hand-typed) results.
_FLOAT_RE = re.compile(r'": -?\d+\.\d{3,}')


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
        "has_lego_ids": "lego_ids" in data or "primary_lego_ids" in data,
    }

    # Serialize once for numeric scan — this is O(n) on file size,
    # which is acceptable since the largest result is ~600KB.
    raw = json.dumps(data)
    floats = _FLOAT_RE.findall(raw)
    info["has_numeric"] = len(floats) > 5
    info["numeric_count"] = len(floats)

    return info


def suggest_classification(info: dict, size: int) -> str:
    """Suggest a classification based on content heuristics.

    Note: these are suggestions for human triage, not auto-classification.
    The suggestion is based on structural completeness, not correctness.
    """
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


def scan_tree(results_dir: Path) -> tuple[int, int, list[dict]]:
    """Scan a single result tree.

    Returns (total_files, total_parseable, unclassified_records).
    """
    all_json = sorted(results_dir.glob("*_results.json"))
    total_files = len(all_json)
    total_parseable = 0
    unclassified = []

    for fpath in all_json:
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
        except Exception:
            continue
        total_parseable += 1

        if data.get("classification") is not None:
            continue

        stem = fpath.stem.removesuffix("_results")
        size = fpath.stat().st_size
        category = categorize_name(stem)
        sim_exists = has_matching_sim(stem)
        info = analyze_content(data)
        suggestion = suggest_classification(info, size)

        unclassified.append({
            "file": fpath.name,
            "stem": stem,
            "size": size,
            "category": category,
            "has_sim": sim_exists,
            "key_count": len(data),
            "keys_sample": sorted(data.keys())[:8],
            **info,
            "suggestion": suggestion,
        })

    return total_files, total_parseable, unclassified


def print_report(
    total_files: int,
    total_parseable: int,
    unclassified: list[dict],
    results_dir: Path,
) -> int:
    """Print the triage report. Returns exit code."""
    classified = total_parseable - len(unclassified)

    print(f"Target: {results_dir}")
    print(f"  Result files on disk:  {total_files}")
    print(f"  Parseable JSON:        {total_parseable}")
    print(f"  Classified:            {classified}")
    print(f"  Unclassified:          {len(unclassified)}")
    print()

    if not unclassified:
        print("No unclassified results. Nothing to triage.")
        return 0

    # By category
    cat_counts = Counter(r["category"] for r in unclassified)
    print("By category:")
    for cat, count in cat_counts.most_common():
        print(f"  {cat:15s} {count}")
    print()

    # By size tier
    tiny = sum(1 for r in unclassified if r["size"] < 500)
    medium = sum(1 for r in unclassified if 500 <= r["size"] <= 10_000)
    large = sum(1 for r in unclassified if r["size"] > 10_000)
    print(f"By size: tiny(<500B)={tiny}  medium(0.5-10KB)={medium}  large(>10KB)={large}")
    print()

    # Sim coverage
    with_sim = sum(1 for r in unclassified if r["has_sim"])
    orphans = len(unclassified) - with_sim
    print(f"Has matching sim: {with_sim}   Orphan (no sim): {orphans}")
    print()

    # Content quality
    with_numeric = sum(1 for r in unclassified if r["has_numeric"])
    with_tests = sum(1 for r in unclassified if r["has_tests"])
    with_pos_neg = sum(1 for r in unclassified if r["has_positive"] and r["has_negative"])
    print(f"Has numeric evidence:  {with_numeric}")
    print(f"Has structured tests:  {with_tests}")
    print(f"Has pos+neg sections:  {with_pos_neg}")
    print()

    # Suggestion breakdown
    sugg_counts = Counter(r["suggestion"].split("(")[0].strip() for r in unclassified)
    print("Suggested classifications:")
    for sugg, count in sugg_counts.most_common():
        print(f"  {sugg}: {count}")
    print()

    # Top candidates for canonical
    candidates = [r for r in unclassified if "canonical" in r["suggestion"]]
    candidates.sort(key=lambda r: -r["size"])
    if candidates:
        print(f"=== TOP CANDIDATES FOR CANONICAL ({len(candidates)}) ===")
        for r in candidates[:20]:
            sim_mark = "✓" if r["has_sim"] else "✗"
            print(f"  {r['size']//1024:4d}KB  {sim_mark} sim  {r['file']}")
        if len(candidates) > 20:
            print(f"  ... +{len(candidates) - 20} more")
        print()

    # Pure lego unclassified
    pure_legos = [r for r in unclassified if r["category"] == "pure_lego"]
    if pure_legos:
        print(f"=== UNCLASSIFIED PURE LEGO ({len(pure_legos)}) ===")
        for r in sorted(pure_legos, key=lambda r: -r["size"]):
            sim_mark = "✓" if r["has_sim"] else "✗"
            sugg_short = r["suggestion"].split("(")[0].strip()
            print(f"  {r['size']//1024:4d}KB  {sim_mark} sim  {sugg_short:30s}  {r['file']}")
        print()

    # Actionable count: unclassified + numeric + has sim = should definitely be triaged
    actionable = sum(1 for r in unclassified if r["has_numeric"] and r["has_sim"])
    if actionable > 0:
        print(f"TRIAGE NEEDED: {actionable} unclassified results have numeric data AND a matching sim.")
        return 1
    else:
        print("No high-priority triage items.")
        return 0


def main() -> int:
    # ---- Primary tree (probe-local) ----
    if not PRIMARY_RESULTS_DIR.exists():
        print(f"ERROR: Primary results directory not found: {PRIMARY_RESULTS_DIR}")
        return 2

    total, parseable, unclassified = scan_tree(PRIMARY_RESULTS_DIR)

    # ---- Secondary tree awareness ----
    if SECONDARY_RESULTS_DIR.exists():
        sec_count = len(list(SECONDARY_RESULTS_DIR.glob("*.json")))
        print(f"NOTE: Secondary result tree exists at {SECONDARY_RESULTS_DIR}")
        print(f"      Contains {sec_count} files (NOT scanned by this tool).")
        print(f"      This is a legacy tree. Audit separately if needed.")
        print()

    return print_report(total, parseable, unclassified, PRIMARY_RESULTS_DIR)


if __name__ == "__main__":
    raise SystemExit(main())
