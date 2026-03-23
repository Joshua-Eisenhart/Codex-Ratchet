#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
import zipfile
from pathlib import Path


REQUIRED_FULL_PLUS_MEMBERS = (
    "THREAD_S_SAVE_SNAPSHOT_v2.txt",
    "DUMP_LEDGER_BODIES.txt",
    "DUMP_TERMS.txt",
    "DUMP_INDEX.txt",
    "REPORT_POLICY_STATE.txt",
    "PROVENANCE.txt",
    "SHA256SUMS.txt",
)


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _resolve_member(names: set[str], rel_name: str) -> str:
    for candidate in (f"restore/{rel_name}", rel_name):
        if candidate in names:
            return candidate
    return ""


def _load_project_save_doc(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "PROJECT_SAVE_DOC_v1":
        raise SystemExit(f"unexpected project save schema: {path}")
    return payload


def _resolve_full_plus_zip_from_project_save(project_save_doc: dict) -> Path | None:
    for raw in project_save_doc.get("source_pointers", []) if isinstance(project_save_doc.get("source_pointers"), list) else []:
        candidate = Path(str(raw)).expanduser().resolve()
        if candidate.is_file() and candidate.suffix.lower() == ".zip":
            return candidate
    return None


def _validate_semantic_full_plus(zip_path: Path) -> tuple[dict[str, str], list[str]]:
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(zf.namelist())
        resolved = {name: _resolve_member(names, name) for name in REQUIRED_FULL_PLUS_MEMBERS}
        missing = sorted(name for name, member in resolved.items() if not member)
        snapshot_member = resolved.get("THREAD_S_SAVE_SNAPSHOT_v2.txt", "")
        if snapshot_member:
            text = zf.read(snapshot_member).decode("utf-8", errors="ignore")
            if "BEGIN THREAD_S_SAVE_SNAPSHOT v2" not in text or "END THREAD_S_SAVE_SNAPSHOT v2" not in text:
                missing.append("THREAD_S_SAVE_SNAPSHOT_v2.txt:invalid_container")
        return resolved, missing


def resolve_semantic_save_source(*, full_plus_zip: Path | None = None, project_save_doc: Path | None = None) -> tuple[Path, dict | None]:
    project_payload = _load_project_save_doc(project_save_doc) if project_save_doc is not None else None
    if project_payload is not None:
        restore = project_payload.get("restore_sufficiency", {}) if isinstance(project_payload.get("restore_sufficiency"), dict) else {}
        if str(restore.get("status", "")).strip() != "PASS":
            raise SystemExit(f"project save restore_sufficiency is not PASS: {project_save_doc}")
    if full_plus_zip is None and project_payload is not None:
        full_plus_zip = _resolve_full_plus_zip_from_project_save(project_payload)
        if full_plus_zip is None:
            raise SystemExit(f"could not resolve a semantic FULL+ zip from project save: {project_save_doc}")
    if full_plus_zip is None:
        raise SystemExit("no semantic FULL+ source resolved")
    return full_plus_zip, project_payload


def extract_snapshot_bytes(*, full_plus_zip: Path | None = None, project_save_doc: Path | None = None) -> tuple[bytes, dict]:
    full_plus_zip, _project_payload = resolve_semantic_save_source(full_plus_zip=full_plus_zip, project_save_doc=project_save_doc)

    resolved_members, errors = _validate_semantic_full_plus(full_plus_zip)
    if errors:
        raise SystemExit(f"semantic FULL+ validation failed for {full_plus_zip}: {errors}")

    with zipfile.ZipFile(full_plus_zip, "r") as zf:
        snapshot_member = resolved_members["THREAD_S_SAVE_SNAPSHOT_v2.txt"]
        snapshot_bytes = zf.read(snapshot_member)

    report = {
        "schema": "THREAD_S_SNAPSHOT_EXTRACTION_REPORT_v1",
        "status": "PASS",
        "created_utc": _utc_now(),
        "project_save_doc": str(project_save_doc) if project_save_doc is not None else "",
        "full_plus_zip": str(full_plus_zip),
        "snapshot_member": resolved_members["THREAD_S_SAVE_SNAPSHOT_v2.txt"],
        "snapshot_sha256": _sha256_bytes(snapshot_bytes),
    }
    return snapshot_bytes, report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Extract THREAD_S_SAVE_SNAPSHOT v2 from a semantic FULL+ save source.")
    ap.add_argument("--project-save-doc", default="")
    ap.add_argument("--full-plus-zip", default="")
    ap.add_argument("--out-txt", default="")
    ap.add_argument("--out-json", default="")
    args = ap.parse_args(argv)

    project_save_path = Path(args.project_save_doc).expanduser().resolve() if str(args.project_save_doc).strip() else None
    full_plus_zip = Path(args.full_plus_zip).expanduser().resolve() if str(args.full_plus_zip).strip() else None

    if project_save_path is None and full_plus_zip is None:
        raise SystemExit("must provide --project-save-doc and/or --full-plus-zip")
    snapshot_bytes, report = extract_snapshot_bytes(full_plus_zip=full_plus_zip, project_save_doc=project_save_path)

    if str(args.out_txt).strip():
        out_txt = Path(args.out_txt).expanduser().resolve()
        out_txt.parent.mkdir(parents=True, exist_ok=True)
        out_txt.write_bytes(snapshot_bytes)
        report["snapshot_path"] = str(out_txt)
    if str(args.out_json).strip():
        out_json = Path(args.out_json).expanduser().resolve()
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
