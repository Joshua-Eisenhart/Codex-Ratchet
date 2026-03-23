#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _status(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit PROJECT_SAVE_DOC_v1.")
    parser.add_argument("--doc-json", required=True)
    parser.add_argument("--out-json", default="")
    args = parser.parse_args()

    doc_path = Path(args.doc_json).resolve()
    payload = json.loads(doc_path.read_text(encoding="utf-8"))

    member_inventory = payload.get("member_inventory", []) if isinstance(payload.get("member_inventory"), list) else []
    required_rows = [row for row in member_inventory if isinstance(row, dict) and bool(row.get("required"))]
    required_paths = [str(row.get("member_path", "")).strip() for row in required_rows]
    unique_required_paths = set(required_paths)
    restore = payload.get("restore_sufficiency", {}) if isinstance(payload.get("restore_sufficiency"), dict) else {}
    restore_status = str(restore.get("status", "")).strip()
    required_present = all(bool(row.get("present")) for row in required_rows)

    checks = [
        {
            "check_id": "PROJECT_SAVE_SCHEMA",
            "status": _status(payload.get("schema") == "PROJECT_SAVE_DOC_v1"),
            "detail": f"schema={payload.get('schema', '')}",
        },
        {
            "check_id": "SOURCE_POINTERS_PRESENT",
            "status": _status(isinstance(payload.get("source_pointers"), list) and len(payload.get("source_pointers", [])) >= 1),
            "detail": f"source_pointer_count={len(payload.get('source_pointers', []) or [])}",
        },
        {
            "check_id": "REQUIRED_MEMBER_INVENTORY_PRESENT",
            "status": _status(len(required_rows) >= 1),
            "detail": f"required_member_count={len(required_rows)}",
        },
        {
            "check_id": "REQUIRED_MEMBER_PATHS_UNIQUE",
            "status": _status(len(required_paths) == len(unique_required_paths)),
            "detail": f"required_paths={required_paths}",
        },
        {
            "check_id": "RESTORE_SUFFICIENCY_EXPLICIT",
            "status": _status(bool(restore_status) and bool(str(restore.get("reason", "")).strip())),
            "detail": f"restore_status={restore_status}",
        },
        {
            "check_id": "RESTORE_SUFFICIENCY_CONSISTENT",
            "status": _status((restore_status == "PASS") == required_present),
            "detail": f"restore_status={restore_status} required_present={required_present}",
        },
        {
            "check_id": "INTEGRITY_WITNESSES_PRESENT",
            "status": _status(isinstance(payload.get("integrity_witnesses"), list) and len(payload.get("integrity_witnesses", [])) >= 1),
            "detail": f"integrity_witness_count={len(payload.get('integrity_witnesses', []) or [])}",
        },
    ]

    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    report = {
        "schema": "AUDIT_PROJECT_SAVE_DOC_REPORT_v1",
        "status": status,
        "doc_path": str(doc_path),
        "checks": checks,
        "errors": [] if status == "PASS" else ["PROJECT_SAVE_DOC_AUDIT_FAILED"],
    }
    out_path = Path(args.out_json).resolve() if str(args.out_json).strip() else None
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
