#!/usr/bin/env python3
"""Validate visible Wizard output against collapse-prone FULL claims."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


CANONICAL_HEADER = re.compile(
    r"^🧙 Wizard v(?P<version>4\.[12]) \| (?P<status>FULL|PARTIAL|BLOCKED) \| "
    r"waves:(?P<waves>\d+/\d+)(?: [^|]+)? \| "
    r"parents:(?P<parents>\d+/\d+) \| "
    r"children:(?P<children>\d+/\d+)(?: [^|]+)? \|",
    re.MULTILINE,
)


def validate_output(text: str) -> list[str]:
    failures: list[str] = []
    match = CANONICAL_HEADER.search(text)
    if "FULL" in text and not match:
        failures.append("full_claim_not_canonical")
    if match and match.group("status") == "FULL":
        if match.group("version") == "4.2":
            if match.group("parents") != "14/14":
                failures.append("full_without_14_parents_including_management")
        elif match.group("parents") != "9/9":
            failures.append("full_without_9_parents")
        child_done, child_required = (int(part) for part in match.group("children").split("/", 1))
        if child_required == 0 or child_done != child_required:
            failures.append("full_without_complete_children")
        required_sections = (
            "## ✨ Answer",
            "## 🧭 Context + Strategy",
            "## 🏛️ Council Results",
            "## ✅ Compiled Move",
            "## 🧭 Follow-Up Options",
            "## 🧙 Footer",
        )
        for section in required_sections:
            if section not in text:
                failures.append("missing_section:" + section)
    if "## 🏛️ Council Results" in text:
        for council in ("Decision", "Failure", "Follow-Up"):
            if council not in text:
                failures.append("missing_council:" + council)
    if match and match.group("version") == "4.2" and "Management" not in text:
        failures.append("missing_management_results")
    if "Failure" in text and "Premortem" not in text:
        failures.append("failure_council_without_premortem")
    if "## 🧙 Footer" in text and "🧙 Time/value:" not in text:
        failures.append("footer_missing_time_value")
    if "## 🧭 Context + Strategy" in text:
        for anchor in ("Current Prompt", "Larger Context", "Strategy State", "Local Overoptimization Risk"):
            if anchor not in text:
                failures.append("context_strategy_missing:" + anchor)
        for anchor in ("Strategy Memory Effect", "Rejected Local Move"):
            if anchor not in text:
                failures.append("context_strategy_missing:" + anchor)
    decision_markers = ("Decision:", "Decision Delta", "what changed", "After premortem", "Strategy Memory Effect")
    if match and match.group("status") == "FULL":
        if not any(marker in text for marker in decision_markers):
            failures.append("missing_decision_density")
        if "valid input" in text and "Decision:" not in text:
            failures.append("topology_validity_without_decision")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", help="Output file path. Reads stdin when omitted.")
    args = parser.parse_args()
    text = Path(args.path).read_text(encoding="utf-8") if args.path else sys.stdin.read()
    failures = validate_output(text)
    if failures:
        print("wizard_output_gate: fail")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("wizard_output_gate: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
