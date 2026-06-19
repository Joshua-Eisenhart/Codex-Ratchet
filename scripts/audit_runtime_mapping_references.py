#!/usr/bin/env python3
"""Audit active Codex Ratchet runtime mapping references.

The current contract is:
- Python command path: /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
- physical Python env: /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main
- Julia carrier: JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=...

Historical receipts may mention old paths. Active skills, task cards, scripts,
and current docs should not present those old paths as the command target.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
OLD_PHYSICAL_PY = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
ALIAS_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
HOMEBREW_PY = "/opt/homebrew/bin/python3"
LOCAL_PY = "/usr/local/bin/python3"
JULIA_CARRIER_CMD = (
    "/opt/homebrew/bin/julia --startup-file=no "
    "--project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier"
)
STRICT_JULIA_PREFIX = "JULIA_LOAD_PATH=@:@stdlib"

ACTIVE_PATHS = [
    REPO / "AGENTS.md",
    REPO / "CODEX.md",
    REPO / "CLAUDE.md",
    REPO / "Makefile",
    REPO / "scripts",
    REPO / "system_v5/docs",
    REPO / "system_v5/codex_skills",
    REPO / ".claude/skills",
    REPO / ".claude/agents",
    Path("/Users/joshuaeisenhart/.codex/skills"),
    Path("/Users/joshuaeisenhart/.codex-second/skills"),
    Path("/Users/joshuaeisenhart/.hermes/skills/software-development"),
    Path("/Users/joshuaeisenhart/wiki/hermes-current"),
]

REFERENCE_PARTS = {
    "archive_old",
    "references",
    "session_20260606_physics_excavation",
    "rollout_summaries",
}

TEXT_SUFFIXES = {".md", ".txt", ".py", ".sh", ".json", ".toml", ".yaml", ".yml"}
ALLOW_OLD_PY_TERMS = re.compile(
    r"physical target|physical env|dated receipt|historical|older|receipt compatibility|"
    r"old path|supersession|do not use|wrong interpreter|wrong env|not current|"
    r"global default-project observations|observed on|partial/different|diverge badly|"
    r"common explicit interpreters|audit target|scan target|bad mapping to demote|"
    r"for py in|stale note|stale",
    re.IGNORECASE,
)


def iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            files.append(path)
            continue
        for child in path.rglob("*"):
            if not child.is_file():
                continue
            if child.suffix not in TEXT_SUFFIXES:
                continue
            if "__pycache__" in child.parts:
                continue
            if child.resolve() == Path(__file__).resolve():
                continue
            files.append(child)
    return sorted(set(files))


def classify_path(path: Path) -> str:
    parts = set(path.parts)
    if parts & REFERENCE_PARTS:
        return "reference_or_historical"
    if "/wiki/hermes-current/" in str(path):
        return "active"
    return "active"


def scan_line(path: Path, line_no: int, line: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    rel = str(path)
    try:
        rel = str(path.relative_to(REPO))
    except ValueError:
        pass
    path_class = classify_path(path)

    def add(kind: str, severity: str, note: str) -> None:
        findings.append(
            {
                "path": rel,
                "line": line_no,
                "kind": kind,
                "severity": severity,
                "path_class": path_class,
                "note": note,
                "excerpt": line.strip()[:260],
            }
        )

    if OLD_PHYSICAL_PY in line and ALIAS_PY not in line and not ALLOW_OLD_PY_TERMS.search(line):
        if path.name == "RUNTIME_LIBRARY_LOCATION_MAP_20260608.md":
            return findings
        severity = "warn" if path_class == "reference_or_historical" else "fail"
        add("old_physical_python_as_command", severity, "Prefer sim-stack alias for active commands.")
    if (HOMEBREW_PY in line or LOCAL_PY in line) and not ALLOW_OLD_PY_TERMS.search(line):
        severity = "warn" if path_class == "reference_or_historical" else "fail"
        add("homebrew_or_local_python_as_canonical", severity, "Homebrew/local Python is not current sim-stack authority.")
    if (
        JULIA_CARRIER_CMD in line
        and STRICT_JULIA_PREFIX not in line
        and not ALLOW_OLD_PY_TERMS.search(line)
    ):
        severity = "warn" if path_class == "reference_or_historical" else "fail"
        add("julia_carrier_without_strict_load_path", severity, "Carrier checks must use JULIA_LOAD_PATH=@:@stdlib.")
    if "/opt/homebrew/bin/julia --startup-file=no -e" in line and not ALLOW_OLD_PY_TERMS.search(line):
        severity = "warn" if path_class == "reference_or_historical" else "fail"
        add("global_default_julia_probe", severity, "Default-project Julia probe is not carrier truth.")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    parser.add_argument("--include-warnings", action="store_true", help="print warnings in text mode")
    args = parser.parse_args()

    findings: list[dict[str, Any]] = []
    for path in iter_files(ACTIVE_PATHS):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            findings.extend(scan_line(path, line_no, line))

    failures = [f for f in findings if f["severity"] == "fail"]
    warnings = [f for f in findings if f["severity"] == "warn"]
    report = {
        "schema": "runtime_mapping_reference_audit.v1",
        "repo": str(REPO),
        "alias_python": ALIAS_PY,
        "physical_python": OLD_PHYSICAL_PY,
        "strict_julia_prefix": STRICT_JULIA_PREFIX,
        "summary": {
            "ok": not failures,
            "failure_count": len(failures),
            "warning_count": len(warnings),
            "file_count": len(iter_files(ACTIVE_PATHS)),
        },
        "failures": failures,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(
            f"ok={summary['ok']} failure_count={summary['failure_count']} "
            f"warning_count={summary['warning_count']} file_count={summary['file_count']}"
        )
        shown = failures + (warnings if args.include_warnings else [])
        for item in shown:
            print(f"{item['severity'].upper()} {item['kind']} {item['path']}:{item['line']} {item['excerpt']}")

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
