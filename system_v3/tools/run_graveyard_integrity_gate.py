#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _status(flag: bool) -> str:
    return "PASS" if flag else "FAIL"


def _iter_json_records(path: Path) -> list[dict]:
    records: list[dict] = []
    if not path.exists():
        return records
    for file_path in sorted(path.rglob("*")):
        if not file_path.is_file():
            continue
        suffix = file_path.suffix.lower()
        if suffix == ".json":
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                records.append(data)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        records.append(item)
            continue
        if suffix == ".jsonl":
            for line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                raw = line.strip()
                if not raw:
                    continue
                try:
                    item = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    records.append(item)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate P5 graveyard-integrity gate.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--min-graveyard-records", type=int, default=1)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    reports_dir = run_dir / "reports"

    candidate_records: list[dict] = []
    for source_root in [run_dir / "b_reports", run_dir / "tapes", run_dir / "snapshots"]:
        candidate_records.extend(_iter_json_records(source_root))

    required_keys = {"candidate_id", "reason_tag", "raw_lines", "failure_class"}
    graveyard_records: list[dict] = []
    for record in candidate_records:
        if required_keys.issubset(record.keys()):
            graveyard_records.append(record)

    violations: list[str] = []
    if len(graveyard_records) < args.min_graveyard_records:
        violations.append("INSUFFICIENT_GRAVEYARD_RECORDS")

    failure_class_ok = all(
        str(record.get("failure_class", "")) in {"B_KILL", "SIM_KILL"}
        for record in graveyard_records
    )
    if not failure_class_ok:
        violations.append("INVALID_FAILURE_CLASS")

    integrity_checks = [
        {
            "check_id": "GRAVEYARD_RECORD_MIN",
            "status": _status(len(graveyard_records) >= args.min_graveyard_records),
            "detail": f"graveyard_records={len(graveyard_records)} min_required={args.min_graveyard_records}",
        },
        {
            "check_id": "GRAVEYARD_REQUIRED_KEYS",
            "status": _status(len(graveyard_records) > 0 or args.min_graveyard_records == 0),
            "detail": "records include candidate_id, reason_tag, raw_lines, failure_class",
        },
        {
            "check_id": "GRAVEYARD_FAILURE_CLASS_FENCE",
            "status": _status(failure_class_ok),
            "detail": "failure_class values are in {B_KILL, SIM_KILL}",
        },
    ]

    status = "PASS" if all(check["status"] == "PASS" for check in integrity_checks) else "FAIL"
    report = {
        "schema": "GRAVEYARD_INTEGRITY_REPORT_v1",
        "run_id": run_dir.name,
        "status": status,
        "integrity_checks": integrity_checks,
        "graveyard_record_count": len(graveyard_records),
        "violations": sorted(set(violations)),
        "updated_utc": "UNCHANGED_BY_GATE_EVAL",
    }
    out_path = reports_dir / "graveyard_integrity_report.json"
    _write_json(out_path, report)
    print(json.dumps({"status": status, "report_path": str(out_path)}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
