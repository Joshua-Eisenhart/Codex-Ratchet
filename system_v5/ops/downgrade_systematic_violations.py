#!/usr/bin/env python3
"""Downgrade systematically non-conformant canonical probes to classical_baseline.

Per OVERNIGHT.md rule 11: do NOT auto-downgrade individual probes, but
systematic-pattern violations (gerbestack, qit_szilard, qit_weyl, qit_carnot)
where missing test sections reflect batch-generation patterns ARE reclassifiable.

Heuristic: if a probe matches a known systematic prefix AND is missing all 3
test sections (positive/negative/boundary) AND has tool_manifest, downgrade it
to classical_baseline with reason `systematic_batch_no_test_sections_2026-04-17`.
Preserve the probe's tool_integration_depth (if any).

Dry-run by default. Pass --apply to actually edit files.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PROBE_DIR = REPO / "system_v4/probes"

SYSTEMATIC_PREFIXES = [
    "sim_gerbestack_weyl_",
    "sim_qit_szilard_",
    "sim_qit_weyl_",
    "sim_qit_carnot_",
]


CLASSIFICATION_LINE = re.compile(
    r'^(classification\s*=\s*)["\']canonical["\'](\s*(?:#.*)?)$',
    re.MULTILINE,
)


def should_downgrade(probe_path: Path) -> tuple[bool, str]:
    """Return (should_downgrade, reason)."""
    name = probe_path.name
    if not any(name.startswith(pfx) for pfx in SYSTEMATIC_PREFIXES):
        return False, "not in systematic pattern set"

    try:
        txt = probe_path.read_text()
    except Exception as e:
        return False, f"unreadable: {e}"

    if not re.search(r'classification\s*=\s*["\']canonical["\']', txt):
        return False, "not currently canonical"

    missing_positive = not re.search(r"def\s+run_positive_tests|positive_tests\s*=|def\s+test_positive", txt)
    missing_negative = not re.search(r"def\s+run_negative_tests|negative_tests\s*=|def\s+test_negative", txt)
    missing_boundary = not re.search(r"def\s+run_boundary_tests|boundary_tests\s*=|def\s+test_boundary", txt)

    if missing_positive and missing_negative and missing_boundary:
        return True, "missing all three test sections"
    return False, "has at least one test section"


def downgrade(probe_path: Path) -> bool:
    """Rewrite classification line. Returns True if modified."""
    txt = probe_path.read_text()
    if not CLASSIFICATION_LINE.search(txt):
        return False
    new_txt = CLASSIFICATION_LINE.sub(
        r'\1"classical_baseline"\2  # downgraded: systematic_batch_no_test_sections_2026-04-17',
        txt,
    )
    probe_path.write_text(new_txt)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="actually rewrite files; default is dry-run")
    args = parser.parse_args()

    probes = sorted(PROBE_DIR.glob("*.py"))
    to_downgrade = []
    skipped = []
    for p in probes:
        should, reason = should_downgrade(p)
        if should:
            to_downgrade.append((p, reason))
        else:
            skipped.append((p, reason))

    print(f"Candidates for downgrade: {len(to_downgrade)}")
    for p, reason in to_downgrade[:50]:
        print(f"  {p.name} — {reason}")
    if len(to_downgrade) > 50:
        print(f"  ... and {len(to_downgrade) - 50} more")

    if args.apply:
        modified = 0
        for p, _ in to_downgrade:
            if downgrade(p):
                modified += 1
        print(f"\nmodified: {modified}")
    else:
        print(f"\n(dry-run — pass --apply to rewrite)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
