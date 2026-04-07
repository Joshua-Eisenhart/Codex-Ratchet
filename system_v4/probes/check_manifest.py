#!/usr/bin/env python3
"""
Manifest Checker -- Validates sim result JSON files against
ENFORCEMENT_AND_PROCESS_RULES.md canonical requirements.

No external dependencies beyond stdlib.

Exit code 0: all canonical files pass validation.
Exit code 1: at least one canonical file has violations.
"""

import json
import os
import sys
from datetime import datetime, timezone

# ── Configuration ──────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_RESULTS_DIR = os.path.join(SCRIPT_DIR, "a2_state", "sim_results")
REPORT_PATH = os.path.join(SIM_RESULTS_DIR, "MANIFEST_CHECK_REPORT.json")

# The 12 required tools from SIM_TEMPLATE.py / ENFORCEMENT_AND_PROCESS_RULES.md
REQUIRED_TOOLS = [
    "pytorch", "pyg",          # Computation layer
    "z3", "cvc5",              # Proof layer
    "sympy",                   # Symbolic layer
    "clifford", "geomstats", "e3nn",  # Geometry layer
    "rustworkx", "xgi",       # Graph layer
    "toponetx", "gudhi",      # Topology layer
]

VALID_CLASSIFICATIONS = {
    "classical_baseline",
    "canonical",
    "supporting",
    "audit",
}


# ── Checking logic ────────────────────────────────────────────────────

def check_file(filepath):
    """Validate a single JSON result file. Returns (info_dict, violations_list)."""
    violations = []
    info = {
        "file": os.path.basename(filepath),
        "has_tool_manifest": False,
        "has_classification": False,
        "classification": None,
        "has_positive": False,
        "has_negative": False,
        "is_canonical": False,
        "meets_canonical_requirements": False,
    }

    try:
        with open(filepath, "r") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        violations.append(f"JSON parse error: {exc}")
        return info, violations

    if not isinstance(data, dict):
        violations.append("Top-level JSON is not an object (dict)")
        return info, violations

    # ── tool_manifest ──
    if "tool_manifest" in data:
        info["has_tool_manifest"] = True
    else:
        violations.append("Missing 'tool_manifest' key")

    # ── classification ──
    if "classification" in data:
        info["has_classification"] = True
        info["classification"] = data["classification"]
        if data["classification"] not in VALID_CLASSIFICATIONS:
            violations.append(
                f"Unknown classification '{data['classification']}'; "
                f"expected one of {sorted(VALID_CLASSIFICATIONS)}"
            )
    else:
        violations.append("Missing 'classification' key")

    # ── positive / negative sections ──
    info["has_positive"] = "positive" in data
    info["has_negative"] = "negative" in data

    # ── canonical-specific checks ──
    is_canonical = data.get("classification") == "canonical"
    info["is_canonical"] = is_canonical

    if is_canonical:
        # Positive and negative sections are required for canonical
        if not info["has_positive"]:
            violations.append("Canonical sim missing 'positive' test section")
        if not info["has_negative"]:
            violations.append("Canonical sim missing 'negative' test section")

        # Full tool manifest check
        manifest = data.get("tool_manifest", {})
        if not manifest:
            violations.append("Canonical sim missing or empty 'tool_manifest'")
        else:
            # Check all 12 tools present
            missing_tools = [t for t in REQUIRED_TOOLS if t not in manifest]
            if missing_tools:
                violations.append(
                    f"Canonical tool_manifest missing tools: {missing_tools}"
                )

            # Check each tool entry structure and the tried+not-used+empty-reason rule
            for tool_name in REQUIRED_TOOLS:
                entry = manifest.get(tool_name)
                if entry is None:
                    continue  # already flagged above

                if not isinstance(entry, dict):
                    violations.append(
                        f"Tool '{tool_name}': entry is not a dict"
                    )
                    continue

                # Must have tried, used, reason keys
                for key in ("tried", "used", "reason"):
                    if key not in entry:
                        violations.append(
                            f"Tool '{tool_name}': missing '{key}' field"
                        )

                tried = entry.get("tried", False)
                used = entry.get("used", False)
                reason = entry.get("reason", "")

                # Violation: tried but not used with no explanation
                if tried and not used and not reason.strip():
                    violations.append(
                        f"Tool '{tool_name}': tried=True, used=False, "
                        f"but reason is empty (must justify omission)"
                    )

                # Violation: not tried and no explanation
                if not tried and not reason.strip():
                    violations.append(
                        f"Tool '{tool_name}': tried=False with empty reason "
                        f"(must explain why tool was not attempted)"
                    )

        # Determine if canonical file fully passes
        canonical_violations = [
            v for v in violations
            if "Canonical" in v or "Tool '" in v
        ]
        info["meets_canonical_requirements"] = len(canonical_violations) == 0

    return info, violations


# ── Main ──────────────────────────────────────────────────────────────

def main():
    if not os.path.isdir(SIM_RESULTS_DIR):
        print(f"ERROR: sim_results directory not found: {SIM_RESULTS_DIR}")
        sys.exit(1)

    json_files = sorted(
        f for f in os.listdir(SIM_RESULTS_DIR)
        if f.endswith(".json") and f != "MANIFEST_CHECK_REPORT.json"
    )

    total = len(json_files)
    files_with_manifest = 0
    files_without_manifest = 0
    files_with_classification = 0
    files_without_classification = 0
    canonical_count = 0
    canonical_pass = 0
    canonical_fail = 0
    all_violations = {}

    for fname in json_files:
        fpath = os.path.join(SIM_RESULTS_DIR, fname)
        info, violations = check_file(fpath)

        if info["has_tool_manifest"]:
            files_with_manifest += 1
        else:
            files_without_manifest += 1

        if info["has_classification"]:
            files_with_classification += 1
        else:
            files_without_classification += 1

        if info["is_canonical"]:
            canonical_count += 1
            if info["meets_canonical_requirements"]:
                canonical_pass += 1
            else:
                canonical_fail += 1

        if violations:
            all_violations[fname] = violations

    # ── Build report ──
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sim_results_dir": SIM_RESULTS_DIR,
        "summary": {
            "total_files_checked": total,
            "files_with_tool_manifest": files_with_manifest,
            "files_without_tool_manifest": files_without_manifest,
            "files_with_classification": files_with_classification,
            "files_without_classification": files_without_classification,
            "canonical_files": canonical_count,
            "canonical_passing": canonical_pass,
            "canonical_failing": canonical_fail,
            "total_files_with_violations": len(all_violations),
        },
        "violations": all_violations,
    }

    # ── Console output ──
    print("=" * 68)
    print("  MANIFEST CHECK REPORT")
    print("=" * 68)
    print()
    s = report["summary"]
    print(f"  Total JSON files checked       : {s['total_files_checked']}")
    print(f"  Files with tool_manifest       : {s['files_with_tool_manifest']}")
    print(f"  Files without tool_manifest    : {s['files_without_tool_manifest']}")
    print(f"  Files with classification      : {s['files_with_classification']}")
    print(f"  Files without classification   : {s['files_without_classification']}")
    print(f"  Canonical files                : {s['canonical_files']}")
    print(f"  Canonical PASSING              : {s['canonical_passing']}")
    print(f"  Canonical FAILING              : {s['canonical_failing']}")
    print(f"  Total files with violations    : {s['total_files_with_violations']}")
    print()

    if all_violations:
        print("-" * 68)
        print("  VIOLATIONS BY FILE")
        print("-" * 68)
        for fname, vlist in sorted(all_violations.items()):
            print(f"\n  {fname}:")
            for v in vlist:
                print(f"    - {v}")
        print()

    # ── Write report JSON ──
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w") as fh:
        json.dump(report, fh, indent=2)
    print(f"Report written to: {REPORT_PATH}")

    # ── Exit code ──
    if canonical_fail > 0:
        print("\nRESULT: FAIL -- canonical files with violations detected")
        sys.exit(1)
    else:
        if canonical_count == 0:
            print("\nRESULT: PASS (no canonical files found to validate)")
        else:
            print(f"\nRESULT: PASS -- all {canonical_pass} canonical files meet requirements")
        sys.exit(0)


if __name__ == "__main__":
    main()
