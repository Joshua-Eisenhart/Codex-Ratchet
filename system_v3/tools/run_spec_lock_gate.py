#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate P0 spec-lock gate and write report.")
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    repo_root = Path(__file__).resolve().parents[2]
    spec_lint_cmd = ["python3", str(repo_root / "system_v3" / "tools" / "spec_lint.py")]
    cp = subprocess.run(spec_lint_cmd, check=False, capture_output=True, text=True)

    if cp.returncode != 0:
        report = {
            "schema": "SPEC_LOCK_REPORT_v1",
            "run_id": run_dir.name,
            "status": "FAIL",
            "checks": [
                {
                    "check_id": "SPEC_LINT_EXECUTION",
                    "status": "FAIL",
                    "detail": "spec_lint.py returned non-zero",
                }
            ],
            "updated_utc": "UNCHANGED_BY_GATE_EVAL",
        }
        _write_json(run_dir / "reports" / "spec_lock_report.json", report)
        print(json.dumps({"status": "FAIL", "reason": "spec_lint_nonzero"}, sort_keys=True))
        return 2

    lint = json.loads(cp.stdout)
    checks = [
        {
            "check_id": "OWNER_COLLISION_ZERO",
            "status": "PASS" if lint.get("owner_collision_count", 1) == 0 else "FAIL",
            "detail": f"owner_collision_count={lint.get('owner_collision_count')}",
        },
        {
            "check_id": "ORPHAN_REQUIREMENTS_ZERO",
            "status": "PASS" if lint.get("orphan_requirements_count", 1) == 0 else "FAIL",
            "detail": f"orphan_requirements_count={lint.get('orphan_requirements_count')}",
        },
        {
            "check_id": "MISSING_OWNER_CLAUSE_ZERO",
            "status": "PASS" if lint.get("missing_owner_clause_count", 1) == 0 else "FAIL",
            "detail": f"missing_owner_clause_count={lint.get('missing_owner_clause_count')}",
        },
    ]
    status = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    report = {
        "schema": "SPEC_LOCK_REPORT_v1",
        "run_id": run_dir.name,
        "status": status,
        "checks": checks,
        "lint_snapshot": lint,
        "updated_utc": "UNCHANGED_BY_GATE_EVAL",
    }
    _write_json(run_dir / "reports" / "spec_lock_report.json", report)
    print(json.dumps({"status": status, "report_path": str(run_dir / "reports" / "spec_lock_report.json")}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
