#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate P1 artifact grammar gate and write report.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--fixture-pack", default="system_v3/conformance/fixtures_v1")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    repo_root = Path(__file__).resolve().parents[2]
    fixture_pack = (repo_root / args.fixture_pack).resolve()

    checks = []

    spec17 = repo_root / "system_v3" / "specs" / "17_BOOTPACK_THREAD_B_v3.9.13_ENFORCEABLE_CONTRACT_EXTRACT_FOR_IMPLEMENTATION_v1.md"
    checks.append(
        {
            "check_id": "SPEC17_PRESENT",
            "status": "PASS" if spec17.exists() else "FAIL",
            "detail": str(spec17),
        }
    )

    runner_tool = repo_root / "system_v3" / "tools" / "run_conformance_fixture_matrix.py"
    checks.append(
        {
            "check_id": "CONFORMANCE_RUNNER_PRESENT",
            "status": "PASS" if runner_tool.exists() else "FAIL",
            "detail": str(runner_tool),
        }
    )

    expected_path = fixture_pack / "expected_outcomes.json"
    manifest_path = fixture_pack / "manifest.json"
    checks.append(
        {
            "check_id": "FIXTURE_MANIFEST_PRESENT",
            "status": "PASS" if manifest_path.exists() else "FAIL",
            "detail": str(manifest_path),
        }
    )
    checks.append(
        {
            "check_id": "FIXTURE_EXPECTED_PRESENT",
            "status": "PASS" if expected_path.exists() else "FAIL",
            "detail": str(expected_path),
        }
    )

    fixture_row_count = 0
    missing_fixture_paths = []
    if expected_path.exists():
        expected_obj = json.loads(expected_path.read_text(encoding="utf-8"))
        rows = expected_obj.get("expected_outcomes", [])
        fixture_row_count = len(rows)
        for row in rows:
            artifact_path = fixture_pack / row.get("artifact_path", "")
            if not artifact_path.exists():
                missing_fixture_paths.append(str(artifact_path))

    checks.append(
        {
            "check_id": "FIXTURE_ARTIFACTS_PRESENT",
            "status": "PASS" if len(missing_fixture_paths) == 0 else "FAIL",
            "detail": f"missing_count={len(missing_fixture_paths)}",
        }
    )

    status = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    report = {
        "schema": "ARTIFACT_GRAMMAR_REPORT_v1",
        "run_id": run_dir.name,
        "status": status,
        "checks": checks,
        "fixture_row_count": fixture_row_count,
        "missing_fixture_paths": missing_fixture_paths,
        "updated_utc": "UNCHANGED_BY_GATE_EVAL",
    }
    out_path = run_dir / "reports" / "artifact_grammar_report.json"
    _write_json(out_path, report)
    print(json.dumps({"status": status, "report_path": str(out_path)}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
