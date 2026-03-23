#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path


_REQUIRED_MEMBERS = [
    "THREAD_S_SAVE_SNAPSHOT_v2.txt",
    "DUMP_LEDGER_BODIES.txt",
    "DUMP_TERMS.txt",
    "DUMP_INDEX.txt",
    "REPORT_POLICY_STATE.txt",
    "PROVENANCE.txt",
    "SHA256SUMS.txt",
]
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _status(flag: bool) -> str:
    return "PASS" if flag else "FAIL"


def _resolve_member(names: set[str], rel_name: str) -> str:
    for candidate in (f"restore/{rel_name}", rel_name):
        if candidate in names:
            return candidate
    return ""


def _parse_sha256sums(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if "  " not in line:
            continue
        digest, rel = line.split("  ", 1)
        digest = digest.strip()
        rel = rel.strip()
        if _HEX64_RE.fullmatch(digest):
            out[rel] = digest
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Audit a semantic FULL+ restore ZIP.")
    ap.add_argument("--zip", required=True)
    ap.add_argument("--out-json", default="")
    args = ap.parse_args(argv)

    zip_path = Path(args.zip).expanduser().resolve()
    if not zip_path.is_file():
        raise SystemExit(f"missing zip: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(zf.namelist())
        manifest_name = _resolve_member(names, "FULL_PLUS_SAVE_MANIFEST_v1.json")
        if not manifest_name and "meta/FULL_PLUS_SAVE_MANIFEST_v1.json" in names:
            manifest_name = "meta/FULL_PLUS_SAVE_MANIFEST_v1.json"

        resolved_required = {name: _resolve_member(names, name) for name in _REQUIRED_MEMBERS}
        missing_required = sorted(name for name, resolved in resolved_required.items() if not resolved)

        snapshot_ok = False
        snapshot_name = resolved_required.get("THREAD_S_SAVE_SNAPSHOT_v2.txt", "")
        if snapshot_name:
            snapshot_text = zf.read(snapshot_name).decode("utf-8", errors="ignore")
            snapshot_ok = "BEGIN THREAD_S_SAVE_SNAPSHOT v2" in snapshot_text and (
                "AXIOM_HYP " in snapshot_text or "PROBE_HYP " in snapshot_text or "SPEC_HYP " in snapshot_text
            )

        sha_ok = False
        bad_hash_members: list[str] = []
        sha_name = resolved_required.get("SHA256SUMS.txt", "")
        if sha_name:
            sha_map = _parse_sha256sums(zf.read(sha_name).decode("utf-8", errors="ignore"))
            expected_cover = [name for name in _REQUIRED_MEMBERS if name != "SHA256SUMS.txt"]
            for rel_name in expected_cover:
                member_name = resolved_required.get(rel_name, "")
                if not member_name:
                    continue
                data = zf.read(member_name)
                if sha_map.get(rel_name, "") != _sha256_bytes(data):
                    bad_hash_members.append(rel_name)
            sha_ok = not bad_hash_members and all(name in sha_map for name in expected_cover)

        manifest_ok = False
        manifest_errors: list[str] = []
        if manifest_name:
            try:
                manifest = json.loads(zf.read(manifest_name).decode("utf-8"))
            except Exception:
                manifest = {}
            if manifest.get("schema") != "FULL_PLUS_SAVE_MANIFEST_v1":
                manifest_errors.append("bad_schema")
            if manifest.get("save_level") != "FULL+":
                manifest_errors.append("bad_save_level")
            member_list = manifest.get("member_list", [])
            if not isinstance(member_list, list):
                manifest_errors.append("bad_member_list")
                member_list = []
            for rel_name in _REQUIRED_MEMBERS:
                expected = f"restore/{rel_name}"
                if expected not in member_list:
                    manifest_errors.append(f"missing_manifest_member:{expected}")
            manifest_ok = not manifest_errors

        checks = [
            {
                "check_id": "FULL_PLUS_REQUIRED_MEMBERS",
                "status": _status(not missing_required),
                "detail": f"missing_required={missing_required}",
            },
            {
                "check_id": "FULL_PLUS_SNAPSHOT_VALID",
                "status": _status(snapshot_ok),
                "detail": f"snapshot_member={snapshot_name or 'MISSING'}",
            },
            {
                "check_id": "FULL_PLUS_SHA256SUMS_VALID",
                "status": _status(sha_ok),
                "detail": f"bad_hash_members={bad_hash_members}",
            },
            {
                "check_id": "FULL_PLUS_MANIFEST_VALID",
                "status": _status(manifest_ok),
                "detail": f"manifest_errors={manifest_errors}",
            },
        ]

    status = "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL"
    report = {
        "schema": "FULL_PLUS_SAVE_AUDIT_REPORT_v1",
        "status": status,
        "zip_path": zip_path.as_posix(),
        "checks": checks,
        "errors": [] if status == "PASS" else ["FULL_PLUS_SAVE_AUDIT_FAILED"],
    }

    if str(args.out_json).strip():
        out_path = Path(args.out_json).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
