#!/usr/bin/env python3
"""Audit every `classification=canonical` probe for SIM_TEMPLATE conformance.

Criteria for a probe to remain labeled `canonical` (per CLAUDE.md + harness/04):
1. `TOOL_MANIFEST` present (in source .py)
2. `TOOL_INTEGRATION_DEPTH` present (in source .py)
3. At least one tool tagged `load_bearing`
4. Positive test function present (`run_positive_tests` or similar)
5. Negative test function present
6. Boundary test function present

Outputs:
- `~/wiki/projects/codex-ratchet/canonical_conformance_audit.md` — per-probe report
- Exit code 0 if all conformant, 1 if any violations.

Does NOT downgrade automatically — produces a list for Tier A Hermes or owner to act on.
"""
from __future__ import annotations
import glob
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PROBE_DIR = REPO / "system_v4/probes"

CHECKS = [
    ("tool_manifest", r"TOOL_MANIFEST\s*=\s*\{"),
    ("integration_depth", r"TOOL_INTEGRATION_DEPTH\s*=\s*\{"),
    ("load_bearing", r'"load_bearing"|\bload_bearing\b'),
    ("positive_tests", r"def\s+run_positive_tests\s*\(|positive_tests\s*=|def\s+test_positive"),
    ("negative_tests", r"def\s+run_negative_tests\s*\(|negative_tests\s*=|def\s+test_negative"),
    ("boundary_tests", r"def\s+run_boundary_tests\s*\(|boundary_tests\s*=|def\s+test_boundary"),
]


def audit_one(path: Path) -> dict:
    try:
        txt = path.read_text()
    except Exception as e:
        return {"path": str(path), "error": str(e), "conformant": False}
    results = {}
    for label, pattern in CHECKS:
        results[label] = bool(re.search(pattern, txt))
    results["path"] = str(path)
    results["conformant"] = all(results[label] for label, _ in CHECKS)
    return results


def main() -> int:
    probes = sorted(PROBE_DIR.glob("*.py"))
    canonical = []
    for p in probes:
        name = p.name
        # Skip private helpers and __init__ — these aren't probes even if they mention canonical
        if name.startswith("_") or name == "__init__.py":
            continue
        try:
            txt = p.read_text()
        except Exception:
            continue
        if re.search(r'classification\s*=\s*["\']canonical["\']', txt):
            canonical.append(p)

    reports = [audit_one(p) for p in canonical]
    violations = [r for r in reports if not r["conformant"]]

    lines = [
        f"# Canonical Conformance Audit — 2026-04-17",
        f"",
        f"- canonical probes total: {len(canonical)}",
        f"- conformant: {len(reports) - len(violations)}",
        f"- violations: {len(violations)}",
        f"",
        "## Violations (per probe)",
        "",
    ]
    for v in violations[:200]:  # cap at 200 to keep report readable
        missing = [label for label, _ in CHECKS if not v.get(label)]
        rel = os.path.relpath(v["path"], REPO)
        lines.append(f"- `{rel}`: missing {', '.join(missing)}")
    if len(violations) > 200:
        lines.append(f"... and {len(violations) - 200} more")
    lines.append("")

    # Group violations by probe-name prefix to spot systematic patterns
    prefix_counts = {}
    for v in violations:
        name = os.path.basename(v["path"])
        # Extract first 3 tokens as prefix
        prefix = "_".join(name.split("_")[:3])
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
    lines.append("## Systematic patterns (top 20 prefix groups with violations)")
    lines.append("")
    for prefix, count in sorted(prefix_counts.items(), key=lambda x: -x[1])[:20]:
        lines.append(f"- `{prefix}_*`: {count}")
    lines.append("")

    out = REPO.parent.parent / "wiki/projects/codex-ratchet/canonical_conformance_audit.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))
    print(f"wrote: {out}")
    print(f"conformant: {len(reports) - len(violations)}/{len(canonical)}")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
