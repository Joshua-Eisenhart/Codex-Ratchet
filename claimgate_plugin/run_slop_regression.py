#!/usr/bin/env python3
"""Regression runner for the six narrow slop-gate signatures.

Each declared fixture directory has a recorded expected disposition. A move in
either direction fails the regression. The real-code census is descriptive:
its counts are evidence for narrowing signatures, never an invented threshold.
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "claimgate_plugin"
FIXTURES = PLUGIN / "fixtures" / "slop"
GATE = PLUGIN / "slop_gate.py"
PYTHON = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
SUMMARY = PLUGIN / "results" / "slop_regression_v1.json"

CASES = [
    ("S1_positive", "S1", FIXTURES / "S1_positive", "TRIP"),
    ("S1_negative", "S1", FIXTURES / "S1_negative", "CLEAN"),
    ("S2_positive", "S2", FIXTURES / "S2_positive", "TRIP"),
    ("S2_negative", "S2", FIXTURES / "S2_negative", "CLEAN"),
    ("S3_positive", "S3", FIXTURES / "S3_positive", "TRIP"),
    ("S3_negative", "S3", FIXTURES / "S3_negative", "CLEAN"),
    ("S4_positive", "S4", FIXTURES / "S4_positive", "TRIP"),
    ("S4_negative", "S4", FIXTURES / "S4_negative", "CLEAN"),
    ("S5_positive", "S5", FIXTURES / "S5_positive", "TRIP"),
    ("S5_negative", "S5", FIXTURES / "S5_negative", "CLEAN"),
    ("S6_positive", "S6", FIXTURES / "S6_positive", "TRIP"),
    ("S6_negative", "S6", FIXTURES / "S6_negative", "CLEAN"),
]


def run_gate(paths: list[Path]) -> tuple[int, list[dict[str, Any]], str]:
    proc = subprocess.run(
        [str(PYTHON), str(GATE), "--json", *map(str, paths)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        findings = json.loads(proc.stdout)
        if not isinstance(findings, list):
            raise ValueError("gate JSON is not a list")
    except (json.JSONDecodeError, ValueError) as exc:
        return proc.returncode, [], f"{type(exc).__name__}: {exc}; stderr={proc.stderr[-400:]}"
    return proc.returncode, findings, proc.stderr


def census() -> dict[str, Any]:
    files = sorted(PLUGIN.glob("*.py"))
    files += sorted((ROOT / "constraint_box" / "src" / "constraintbox").glob("*.py"))
    test_files = sorted((ROOT / "constraint_box" / "tests").glob("*.py"))
    files += test_files
    rc, findings, error = run_gate(files)
    test_paths = {str(path.resolve()) for path in test_files}
    test_findings = [
        item for item in findings
        if str(Path(item["path"]).resolve()) in test_paths
    ]
    by_signature: dict[str, dict[str, Any]] = {}
    counts = Counter(item["signature_id"] for item in findings)
    for sid in [f"S{i}" for i in range(1, 7)]:
        locations = [
            {
                "path": item["path"],
                "line": item["line"],
                "excerpt": item["excerpt"],
                "why": item["why"],
            }
            for item in findings
            if item["signature_id"] == sid
        ]
        by_signature[sid] = {"count": counts[sid], "locations": locations}
    by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in findings:
        by_file[item["path"]].append(item)
    return {
        "scope": [
            str(PLUGIN / "*.py"),
            str(ROOT / "constraint_box" / "src" / "constraintbox" / "*.py"),
            str(ROOT / "constraint_box" / "tests" / "*.py"),
        ],
        "files_scanned": len(files),
        "gate_exit": rc,
        "gate_error": error or None,
        "findings_total": len(findings),
        "by_signature": by_signature,
        "by_file": dict(sorted(by_file.items())),
        "constraint_box_tests": {
            "scope": str(ROOT / "constraint_box" / "tests" / "*.py"),
            "files_scanned": len(test_files),
            "findings_total": len(test_findings),
            "by_signature": dict(Counter(
                item["signature_id"] for item in test_findings
            )),
            "locations": test_findings,
        },
    }


def main(argv: list[str]) -> int:
    if argv:
        print("usage: run_slop_regression.py", file=sys.stderr)
        return 2
    rows: list[dict[str, Any]] = []
    deviations: list[dict[str, Any]] = []
    if not CASES:
        deviations.append({
            "id": "coverage",
            "expected": "ONE_OR_MORE_CASES",
            "actual": "NONE_DECLARED",
            "reason": "NO_CASES_DECLARED",
        })
    for case_id, sid, fixture_dir, expected in CASES:
        fixture_files = sorted(fixture_dir.glob("*.py")) if fixture_dir.is_dir() else []
        if not fixture_files:
            row = {
                "id": case_id, "sid": sid, "fixture_dir": str(fixture_dir),
                "expected": expected, "actual": "MISSING", "matched": False,
                "gate_exit": None, "findings": [],
            }
            deviations.append({
                "id": case_id, "sid": sid, "expected": expected,
                "actual": "MISSING", "reason": "FIXTURE_MISSING",
            })
        else:
            rc, findings, error = run_gate([fixture_dir])
            own = [item for item in findings if item.get("signature_id") == sid]
            actual = "TRIP" if findings else "CLEAN"
            matched = (expected == "TRIP" and rc == 1 and bool(own)) or (
                expected == "CLEAN" and rc == 0 and not findings
            )
            row = {
                "id": case_id, "sid": sid, "fixture_dir": str(fixture_dir),
                "fixture_files": len(fixture_files), "expected": expected,
                "actual": actual, "matched": matched, "gate_exit": rc,
                "gate_error": error or None, "findings": findings,
                "signature_counts": dict(Counter(item["signature_id"] for item in findings)),
            }
            if not matched:
                deviations.append({
                    "id": case_id, "sid": sid, "expected": expected,
                    "actual": actual,
                    "reason": "SIGNATURE_MISSED" if expected == "TRIP" else "FALSE_POSITIVE",
                    "gate_exit": rc,
                    "findings": findings,
                })
        rows.append(row)
        print(f"  {case_id:<12} expected={expected:<5} actual={row['actual']:<7} matched={row['matched']}")

    real_census = census()
    caught_ids = sorted({
        row["sid"] for row in rows
        if row["expected"] == "TRIP" and row["matched"]
    })
    negative_total = sum(
        row.get("fixture_files", 0) for row in rows if row["expected"] == "CLEAN"
    )
    negative_clean = sum(
        row.get("fixture_files", 0)
        for row in rows if row["expected"] == "CLEAN" and row["matched"]
    )
    positive_files = sum(
        row.get("fixture_files", 0) for row in rows if row["expected"] == "TRIP"
    )
    print(
        f"\nrun_slop_regression: signatures caught {len(caught_ids)}/6; "
        f"negative fixtures clean {negative_clean}/{negative_total}; "
        f"deviations {len(deviations)}"
    )
    print(f"real-code census: {real_census['findings_total']} suspect(s) across {real_census['files_scanned']} files")
    test_census = real_census["constraint_box_tests"]
    print(
        "constraint_box tests census: "
        f"{test_census['findings_total']} suspect(s) across "
        f"{test_census['files_scanned']} files"
    )
    for sid, data in real_census["by_signature"].items():
        print(f"  {sid}: {data['count']}")
        for item in data["locations"]:
            print(f"    {item['path']}:{item['line']}")
    summary = {
        "probe": "claimgate_slop_regression_v1",
        "classification": "static_signature_regression",
        "promotion_allowed": False,
        "exit_convention": (
            "0 means every declared fixture matched; 1 means a deviation; "
            "2 means usage error. Census findings are reported, not threshold-gated."
        ),
        "cases_declared": len(CASES),
        "fixture_files": {
            "positive": positive_files,
            "negative": negative_total,
            "total": positive_files + negative_total,
        },
        "signatures_caught": {"caught": len(caught_ids), "total": 6, "ids": caught_ids},
        "negatives_clean": {"clean": negative_clean, "total": negative_total},
        "results": rows,
        "deviations": deviations,
        "census": real_census,
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 1 if deviations else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
