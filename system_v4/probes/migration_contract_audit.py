#!/usr/bin/env python3
"""
Advisory audit for standalone torch-family migration lanes.

This is intentionally non-blocking for now. It reports whether extracted
standalone torch module families have the minimum result metadata required to be
treated as migrated, and whether any promoted result claims lack a matching
standalone module surface.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "a2_state" / "sim_results"
TORCH_MODULES_DIR = ROOT / "torch_modules"
OUT_PATH = RESULTS_DIR / "migration_contract_audit_results.json"

REQUIRED_FIELDS = (
    "migration_family",
    "migration_registry_id",
    "migration_status",
    "tool_integration_depth",
)


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text())
    except Exception:  # noqa: BLE001
        return None
    return payload if isinstance(payload, dict) else None


def module_family_names() -> list[str]:
    families: list[str] = []
    for path in sorted(TORCH_MODULES_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        families.append(path.stem)
    return families


def result_path_for_family(family: str) -> Path:
    return RESULTS_DIR / f"torch_{family}_results.json"


def sim_path_for_family(family: str) -> Path:
    return ROOT / f"sim_torch_{family}.py"


def main() -> int:
    strict = "--strict" in sys.argv[1:]
    advisory_findings: list[dict[str, Any]] = []
    extracted_families = module_family_names()

    for family in extracted_families:
        result_path = result_path_for_family(family)
        sim_path = sim_path_for_family(family)

        if not sim_path.exists():
            advisory_findings.append({
                "kind": "standalone_module_missing_family_sim",
                "family": family,
                "sim_file": sim_path.name,
            })
            continue

        if not result_path.exists():
            advisory_findings.append({
                "kind": "standalone_module_missing_result_json",
                "family": family,
                "result_json": result_path.name,
            })
            continue

        payload = load_json(result_path)
        if payload is None:
            advisory_findings.append({
                "kind": "standalone_module_unreadable_result_json",
                "family": family,
                "result_json": result_path.name,
            })
            continue

        missing_fields = [field for field in REQUIRED_FIELDS if field not in payload]
        if missing_fields:
            advisory_findings.append({
                "kind": "standalone_module_missing_migration_metadata",
                "family": family,
                "result_json": result_path.name,
                "missing_fields": missing_fields,
            })
            continue

        if payload.get("migration_family") != family:
            advisory_findings.append({
                "kind": "standalone_module_family_mismatch",
                "family": family,
                "result_json": result_path.name,
                "expected": family,
                "actual": payload.get("migration_family"),
            })

        if not isinstance(payload.get("migration_registry_id"), int):
            advisory_findings.append({
                "kind": "standalone_module_registry_id_not_int",
                "family": family,
                "result_json": result_path.name,
                "actual": payload.get("migration_registry_id"),
            })

        if payload.get("migration_status") != "TORCH_TESTED":
            advisory_findings.append({
                "kind": "standalone_module_status_not_torch_tested",
                "family": family,
                "result_json": result_path.name,
                "actual": payload.get("migration_status"),
            })

        if not isinstance(payload.get("tool_integration_depth"), dict):
            advisory_findings.append({
                "kind": "standalone_module_tool_depth_missing_or_invalid",
                "family": family,
                "result_json": result_path.name,
                "actual_type": type(payload.get("tool_integration_depth")).__name__,
            })

    extracted_set = set(extracted_families)
    promoted_rows: list[dict[str, Any]] = []
    for result_path in sorted(RESULTS_DIR.glob("torch_*_results.json")):
        payload = load_json(result_path)
        if payload is None:
            continue
        family = payload.get("migration_family")
        status = payload.get("migration_status")
        if isinstance(family, str) and status is not None:
            promoted_rows.append({
                "result_json": result_path.name,
                "family": family,
                "migration_status": status,
            })
            if family not in extracted_set:
                advisory_findings.append({
                    "kind": "promoted_family_missing_standalone_module",
                    "family": family,
                    "result_json": result_path.name,
                    "migration_status": status,
                })

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "strict": strict,
        "summary": {
            "extracted_family_count": len(extracted_families),
            "promoted_result_count": len(promoted_rows),
            "advisory_finding_count": len(advisory_findings),
            "ok": len(advisory_findings) == 0,
        },
        "required_fields": list(REQUIRED_FIELDS),
        "extracted_families": extracted_families,
        "promoted_rows": promoted_rows,
        "advisory_findings": advisory_findings,
    }

    OUT_PATH.write_text(json.dumps(report, indent=2))
    print(f"Wrote {OUT_PATH}")
    print(f"extracted_family_count={len(extracted_families)}")
    print(f"promoted_result_count={len(promoted_rows)}")
    print(f"advisory_finding_count={len(advisory_findings)}")
    if strict and advisory_findings:
        print("MIGRATION CONTRACT AUDIT FAILED")
        return 1

    print("MIGRATION CONTRACT AUDIT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
