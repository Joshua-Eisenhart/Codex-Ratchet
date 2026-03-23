#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
import zipfile
from pathlib import Path


FULL_PLUS_REQUIRED_MEMBERS = (
    "restore/THREAD_S_SAVE_SNAPSHOT_v2.txt",
    "restore/DUMP_LEDGER_BODIES.txt",
    "restore/DUMP_TERMS.txt",
    "restore/DUMP_INDEX.txt",
    "restore/REPORT_POLICY_STATE.txt",
    "restore/PROVENANCE.txt",
    "restore/SHA256SUMS.txt",
    "meta/FULL_PLUS_SAVE_MANIFEST_v1.json",
)

RUN_STATE_REQUIRED_FILES = (
    "state.json",
    "state.heavy.json",
    "sequence_state.json",
    "summary.json",
    "logs/events.000.jsonl",
    "tapes/export_tape.000.jsonl",
    "tapes/campaign_tape.000.jsonl",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _compact_ts() -> str:
    return time.strftime("%Y%m%d_%H%M%SZ", time.gmtime())


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _build_full_plus_inventory(zip_path: Path) -> tuple[list[dict], list[dict], str]:
    members: list[dict] = []
    integrity_witnesses: list[dict] = []
    restore_status = "FAIL"
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = set(zf.namelist())
            for name in FULL_PLUS_REQUIRED_MEMBERS:
                info = zf.getinfo(name) if name in names else None
                members.append(
                    {
                        "member_path": name,
                        "source_kind": "zip_member",
                        "required": True,
                        "present": info is not None,
                        "byte_size": int(info.file_size) if info else 0,
                        "sha256": hashlib.sha256(zf.read(name)).hexdigest() if info else "",
                    }
                )
            restore_status = "PASS" if all(row["present"] for row in members) else "FAIL"
    except zipfile.BadZipFile:
        restore_status = "FAIL"
    integrity_witnesses.append(
        {
            "path": str(zip_path),
            "sha256": _sha256_file(zip_path) if zip_path.exists() else "",
            "source_kind": "zip_file",
        }
    )
    sha_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    if sha_path.exists():
        integrity_witnesses.append({"path": str(sha_path), "sha256": _sha256_file(sha_path), "source_kind": "sidecar"})
    return members, integrity_witnesses, restore_status


def _build_run_inventory(run_dir: Path) -> tuple[list[dict], list[dict], str]:
    members: list[dict] = []
    integrity_witnesses: list[dict] = []
    for rel in RUN_STATE_REQUIRED_FILES:
        path = run_dir / rel
        members.append(
            {
                "member_path": rel,
                "source_kind": "run_file",
                "required": True,
                "present": path.exists(),
                "byte_size": int(path.stat().st_size) if path.exists() else 0,
                "sha256": _sha256_file(path) if path.exists() else "",
            }
        )
    for rel in ("state.json.sha256", "state.heavy.json.sha256"):
        path = run_dir / rel
        if path.exists():
            integrity_witnesses.append({"path": str(path), "sha256": _sha256_file(path), "source_kind": "sidecar"})
    summary = _read_json(run_dir / "summary.json")
    if summary:
        integrity_witnesses.append(
            {
                "path": str(run_dir / "summary.json"),
                "sha256": _sha256_file(run_dir / "summary.json"),
                "source_kind": "run_file",
            }
        )
    restore_status = "PASS" if all(row["present"] for row in members) else "FAIL"
    return members, integrity_witnesses, restore_status


def main() -> int:
    parser = argparse.ArgumentParser(description="Build PROJECT_SAVE_DOC_v1 from a semantic FULL+ zip and/or run surface.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--full-plus-zip", default="")
    parser.add_argument("--out-json", default="")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    run_dir = Path(args.run_dir).resolve() if str(args.run_dir).strip() else None
    full_plus_zip = Path(args.full_plus_zip).resolve() if str(args.full_plus_zip).strip() else None

    if run_dir is None and full_plus_zip is None:
        raise SystemExit("must provide at least one of --run-dir or --full-plus-zip")

    member_inventory: list[dict] = []
    integrity_witnesses: list[dict] = []
    source_pointers: list[str] = []
    restore_components: list[tuple[str, str]] = []

    if full_plus_zip is not None:
        source_pointers.append(str(full_plus_zip))
        members, witnesses, restore_status = _build_full_plus_inventory(full_plus_zip)
        member_inventory.extend(members)
        integrity_witnesses.extend(witnesses)
        restore_components.append(("FULL+", restore_status))

    if run_dir is not None:
        source_pointers.append(str(run_dir))
        members, witnesses, restore_status = _build_run_inventory(run_dir)
        member_inventory.extend(members)
        integrity_witnesses.extend(witnesses)
        restore_components.append(("RUN_STATE", restore_status))

    overall_status = "PASS" if restore_components and all(status == "PASS" for _, status in restore_components) else "FAIL"
    save_level = "FULL+" if full_plus_zip is not None else "RUN_STATE"
    if full_plus_zip is not None and run_dir is not None:
        save_level = "FULL+_WITH_RUN_STATE"

    payload = {
        "schema": "PROJECT_SAVE_DOC_v1",
        "project_save_id": f"PROJECT_SAVE__{_compact_ts()}",
        "created_utc": _utc_now(),
        "save_level": save_level,
        "source_pointers": source_pointers,
        "member_inventory": member_inventory,
        "integrity_witnesses": integrity_witnesses,
        "restore_sufficiency": {
            "status": overall_status,
            "reason": "all required members present" if overall_status == "PASS" else "missing required save members",
            "components": [{"component": name, "status": status} for name, status in restore_components],
        },
        "repo_root": str(repo_root),
    }

    out_path = Path(args.out_json).resolve() if str(args.out_json).strip() else None
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
