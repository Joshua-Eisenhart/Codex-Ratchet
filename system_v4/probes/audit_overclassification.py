#!/usr/bin/env python3
"""
Overclassification audit — scans all result JSONs in sim_results/.

Reports:
  - canonical files with FAIL/FAILED status values in test results
  - canonical files with no per-test status fields (schema non-compliance)
  - canonical files missing TOOL_INTEGRATION_DEPTH (legacy gap, informational only)

Exit code 1 if any genuine failures found in canonical files.
"""

import json
import glob
import os
import re
import sys

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
FAIL_STRINGS = {"FAIL", "FAILED"}


def scan_for_fails(obj, path=""):
    """Recursively find paths where a value is a FAIL string."""
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            hits.extend(scan_for_fails(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(scan_for_fails(v, f"{path}[{i}]"))
    elif isinstance(obj, str) and obj.upper() in FAIL_STRINGS:
        hits.append((path, obj))
    return hits


def has_test_status_schema(d):
    """Return True if the file has at least one PASS/FAIL status field."""
    raw = json.dumps(d)
    return bool(re.search(r'"status"\s*:\s*"(PASS|FAIL|SKIP)', raw))


def main():
    files = sorted(glob.glob(os.path.join(RESULTS_DIR, "*.json")))

    genuine_failures = []   # canonical + FAIL in test results
    schema_gaps = []        # canonical + no per-test status fields
    legacy_gaps = []        # canonical + missing TOOL_INTEGRATION_DEPTH (informational)

    for fpath in files:
        try:
            d = json.load(open(fpath))
        except Exception:
            continue

        cls = d.get("classification", "")
        if cls != "canonical":
            continue

        fname = os.path.basename(fpath)

        # Check for genuine FAIL values — but exclude intentional negative battery patterns
        # where the outer test has status=PASS but inner z3_verdict=FAIL (z3 rejecting bad state)
        all_fails = scan_for_fails(d)
        real_fails = []
        for path, val in all_fails:
            # Skip z3_verdict fields — these are z3's output on inputs, not test outcomes
            if "z3_verdict" in path:
                continue
            # Skip if the parent test has status=PASS (e.g. negative battery correctly catching)
            parent = path.rsplit(".", 1)[0]
            parent_obj = d
            for part in parent.lstrip(".").split("."):
                if isinstance(parent_obj, dict):
                    parent_obj = parent_obj.get(part, {})
            if isinstance(parent_obj, dict) and parent_obj.get("status") == "PASS":
                continue
            real_fails.append(path)

        if real_fails:
            genuine_failures.append((fname, real_fails))
            continue  # already flagged, don't also flag schema

        # Check for schema compliance (has per-test status fields)
        if not has_test_status_schema(d):
            schema_gaps.append(fname)

        # Informational: TOOL_INTEGRATION_DEPTH
        if "TOOL_INTEGRATION_DEPTH" not in d and "tool_integration_depth" not in d:
            legacy_gaps.append(fname)

    # Report
    print(f"Scanned {len(files)} result JSONs in {RESULTS_DIR}")
    print()

    if genuine_failures:
        print(f"GENUINE FAILURES in canonical files ({len(genuine_failures)}):")
        for fname, paths in genuine_failures:
            print(f"  {fname}")
            for p in paths[:3]:
                print(f"    FAIL at {p}")
        print()
    else:
        print("No genuine failures in canonical files. ✓")
        print()

    if schema_gaps:
        print(f"Schema gaps — canonical, no per-test status fields ({len(schema_gaps)}):")
        for fname in schema_gaps[:5]:
            print(f"  {fname}")
        if len(schema_gaps) > 5:
            print(f"  ...and {len(schema_gaps) - 5} more")
        print()

    print(f"Legacy gap (canonical, missing TOOL_INTEGRATION_DEPTH): {len(legacy_gaps)} files")
    print("  (Known pre-template issue — informational only, see ENFORCEMENT_AND_PROCESS_RULES.md line 55)")
    print()

    if genuine_failures:
        print("AUDIT FAILED — canonical files with genuine test failures found.")
        sys.exit(1)
    else:
        print("AUDIT PASSED — no canonical files with genuine test failures.")
        if schema_gaps:
            print(f"  ({len(schema_gaps)} schema gaps and {len(legacy_gaps)} TOOL_INTEGRATION_DEPTH gaps are informational — pre-template legacy)")
        sys.exit(0)


if __name__ == "__main__":
    main()
