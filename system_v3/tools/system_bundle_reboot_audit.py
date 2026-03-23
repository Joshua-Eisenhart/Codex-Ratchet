#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from extract_thread_s_snapshot_from_semantic_save import extract_snapshot_bytes, resolve_semantic_save_source


def _status(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def _check_exists(path: Path, check_id: str) -> dict:
    return {
        "check_id": check_id,
        "status": _status(path.exists()),
        "detail": str(path),
    }


def _spec_manifest_check(repo_root: Path) -> dict:
    manifest_path = repo_root / "system_v3/specs/00_MANIFEST.md"
    if not manifest_path.is_file():
        return {
            "check_id": "SPEC_MANIFEST_PRESENT",
            "status": "FAIL",
            "detail": str(manifest_path),
        }
    text = manifest_path.read_text(encoding="utf-8")
    required = [
        "72_SIM_CAMPAIGN_AND_SUITE_MODES__v1.md",
        "73_FULL_PLUS_SEMANTIC_SAVE_ZIP__v1.md",
        "74_A0_SAVE_REPORT_SURFACES__v1.md",
        "75_A2_MINING_AND_ROSETTA_ARTIFACT_PACKS__v1.md",
        "76_SYSTEM_BUNDLE_AND_REBOOT_PLAYBOOK__v1.md",
    ]
    missing = [name for name in required if name not in text]
    return {
        "check_id": "SPEC_MANIFEST_DISCOVERS_BUNDLE_SUPPLEMENTS",
        "status": _status(not missing),
        "detail": f"missing={missing}",
    }


def _run_prepare_tool(
    repo_root: Path,
    *,
    full_plus_zip: Path | None,
    project_save_doc: Path | None,
) -> dict:
    tool_path = repo_root / "system_v3/tools/prepare_b_restore_from_semantic_save.py"
    with tempfile.TemporaryDirectory(prefix="bundle_reboot_audit_") as tmp_dir:
        cmd = [sys.executable, str(tool_path), "--out-dir", str(Path(tmp_dir) / "prep")]
        if full_plus_zip is not None:
            cmd.extend(["--full-plus-zip", str(full_plus_zip)])
        if project_save_doc is not None:
            cmd.extend(["--project-save-doc", str(project_save_doc)])
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_root)
        detail = {
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
        if proc.returncode != 0:
            return {
                "check_id": "B_RESTORE_PREP_TOOL_RUNTIME",
                "status": "FAIL",
                "detail": json.dumps(detail, sort_keys=True),
            }
        try:
            payload = json.loads(proc.stdout.strip())
        except json.JSONDecodeError:
            return {
                "check_id": "B_RESTORE_PREP_TOOL_RUNTIME",
                "status": "FAIL",
                "detail": json.dumps(detail, sort_keys=True),
            }
        return {
            "check_id": "B_RESTORE_PREP_TOOL_RUNTIME",
            "status": _status(payload.get("status") == "PASS"),
            "detail": json.dumps(payload, sort_keys=True),
        }


def _runtime_checks(
    repo_root: Path,
    *,
    full_plus_zip: Path | None,
    project_save_doc: Path | None,
) -> list[dict]:
    if full_plus_zip is None and project_save_doc is None:
        return [
            {
                "check_id": "SEMANTIC_SAVE_RUNTIME_PROOF",
                "status": "SKIP",
                "detail": "no --full-plus-zip or --project-save-doc provided",
            }
        ]

    checks: list[dict] = []
    try:
        resolved_zip, _project_payload = resolve_semantic_save_source(
            full_plus_zip=full_plus_zip,
            project_save_doc=project_save_doc,
        )
        checks.append(
            {
                "check_id": "SEMANTIC_SAVE_SOURCE_RESOLVES",
                "status": "PASS",
                "detail": str(resolved_zip),
            }
        )
    except SystemExit as exc:
        checks.append(
            {
                "check_id": "SEMANTIC_SAVE_SOURCE_RESOLVES",
                "status": "FAIL",
                "detail": str(exc),
            }
        )
        return checks

    try:
        snapshot_bytes, extraction_report = extract_snapshot_bytes(
            full_plus_zip=full_plus_zip,
            project_save_doc=project_save_doc,
        )
        checks.append(
            {
                "check_id": "THREAD_S_SNAPSHOT_EXTRACTION_RUNTIME",
                "status": _status(bool(snapshot_bytes) and extraction_report.get("status") == "PASS"),
                "detail": json.dumps(extraction_report, sort_keys=True),
            }
        )
    except SystemExit as exc:
        checks.append(
            {
                "check_id": "THREAD_S_SNAPSHOT_EXTRACTION_RUNTIME",
                "status": "FAIL",
                "detail": str(exc),
            }
        )
        return checks

    checks.append(
        _run_prepare_tool(
            repo_root,
            full_plus_zip=full_plus_zip,
            project_save_doc=project_save_doc,
        )
    )
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit current system bundle and reboot readiness.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--full-plus-zip", default="")
    parser.add_argument("--project-save-doc", default="")
    parser.add_argument("--out-json", default="")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).expanduser().resolve()
    full_plus_zip = Path(args.full_plus_zip).expanduser().resolve() if str(args.full_plus_zip).strip() else None
    project_save_doc = Path(args.project_save_doc).expanduser().resolve() if str(args.project_save_doc).strip() else None

    required_specs = [
        "system_v3/specs/03_B_KERNEL_SPEC.md",
        "system_v3/specs/16_ZIP_SAVE_AND_TAPES_SPEC.md",
        "system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md",
        "system_v3/specs/28_A2_THREAD_BOOT__v1.md",
        "system_v3/specs/31_A1_THREAD_BOOT__v1.md",
        "system_v3/specs/40_PARALLEL_CODEX_THREAD_CONTROL__v1.md",
        "system_v3/specs/66_PARALLEL_CODEX_RUN_PLAYBOOK__v1.md",
        "system_v3/specs/72_SIM_CAMPAIGN_AND_SUITE_MODES__v1.md",
        "system_v3/specs/73_FULL_PLUS_SEMANTIC_SAVE_ZIP__v1.md",
        "system_v3/specs/74_A0_SAVE_REPORT_SURFACES__v1.md",
        "system_v3/specs/75_A2_MINING_AND_ROSETTA_ARTIFACT_PACKS__v1.md",
        "system_v3/specs/76_SYSTEM_BUNDLE_AND_REBOOT_PLAYBOOK__v1.md",
    ]
    required_tools = [
        "system_v3/tools/build_full_plus_save_zip.py",
        "system_v3/tools/audit_full_plus_save_zip.py",
        "system_v3/tools/build_project_save_doc.py",
        "system_v3/tools/audit_project_save_doc.py",
        "system_v3/tools/extract_thread_s_snapshot_from_semantic_save.py",
        "system_v3/tools/prepare_b_restore_from_semantic_save.py",
    ]

    checks: list[dict] = []
    for rel_path in required_specs:
        checks.append(_check_exists(repo_root / rel_path, f"REQUIRED_SURFACE::{rel_path}"))
    for rel_path in required_tools:
        checks.append(_check_exists(repo_root / rel_path, f"REQUIRED_TOOL::{rel_path}"))
    checks.append(_spec_manifest_check(repo_root))
    checks.extend(
        _runtime_checks(
            repo_root,
            full_plus_zip=full_plus_zip,
            project_save_doc=project_save_doc,
        )
    )

    hard_fail = any(check["status"] == "FAIL" for check in checks)
    status = "PASS" if not hard_fail else "FAIL"
    report = {
        "schema": "SYSTEM_BUNDLE_REBOOT_AUDIT_REPORT_v1",
        "status": status,
        "repo_root": str(repo_root),
        "project_save_doc": str(project_save_doc) if project_save_doc is not None else "",
        "full_plus_zip": str(full_plus_zip) if full_plus_zip is not None else "",
        "checks": checks,
        "errors": [] if status == "PASS" else ["SYSTEM_BUNDLE_REBOOT_AUDIT_FAILED"],
    }

    if str(args.out_json).strip():
        out_path = Path(args.out_json).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
