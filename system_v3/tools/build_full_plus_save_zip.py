#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
import zipfile
from pathlib import Path


_FIXED_ZIP_DATETIME = (1980, 1, 1, 0, 0, 0)
_REQUIRED_MEMBERS = [
    "THREAD_S_SAVE_SNAPSHOT_v2.txt",
    "DUMP_LEDGER_BODIES.txt",
    "DUMP_TERMS.txt",
    "DUMP_INDEX.txt",
    "REPORT_POLICY_STATE.txt",
    "PROVENANCE.txt",
]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _default_out_path(repo_root: Path) -> Path:
    stamp = time.strftime("%Y%m%d_%H%M%SZ", time.gmtime())
    return repo_root / "system_v3" / "runs" / "_save_exports" / f"FULL_PLUS_SAVE__{stamp}.zip"


def _write_zip_member(zf: zipfile.ZipFile, rel_path: str, data: bytes) -> None:
    zi = zipfile.ZipInfo(rel_path, date_time=_FIXED_ZIP_DATETIME)
    zi.compress_type = zipfile.ZIP_DEFLATED
    zi.external_attr = 0o644 << 16
    zf.writestr(zi, data)


def _read_required_members(source_dir: Path) -> dict[str, bytes]:
    payload: dict[str, bytes] = {}
    missing: list[str] = []
    for name in _REQUIRED_MEMBERS:
        path = source_dir / name
        if not path.is_file():
            missing.append(name)
            continue
        payload[name] = path.read_bytes()
    if missing:
        raise SystemExit(f"missing required FULL+ source members: {', '.join(missing)}")
    return payload


def _build_sha256sums(member_bytes: dict[str, bytes]) -> bytes:
    lines: list[str] = []
    for name in sorted(member_bytes.keys()):
        lines.append(f"{_sha256_bytes(member_bytes[name])}  {name}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _build_manifest(*, bundle_id: str, boot_id: str, member_bytes: dict[str, bytes], source_dir: Path) -> bytes:
    manifest = {
        "schema": "FULL_PLUS_SAVE_MANIFEST_v1",
        "save_level": "FULL+",
        "bundle_id": bundle_id,
        "created_utc": _utc_now(),
        "boot_id": boot_id,
        "source_dir": source_dir.as_posix(),
        "member_list": [f"restore/{name}" for name in sorted(member_bytes.keys())] + ["restore/SHA256SUMS.txt"],
        "member_sha256": {
            f"restore/{name}": _sha256_bytes(data)
            for name, data in sorted(member_bytes.items())
        },
    }
    return (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Build a semantic FULL+ restore ZIP from a Thread-B save source directory.")
    ap.add_argument("--source-dir", required=True, help="Directory containing the semantic Thread-B save members.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--out-zip", default="")
    args = ap.parse_args(argv)

    source_dir = Path(args.source_dir).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not source_dir.is_dir():
        raise SystemExit(f"missing source dir: {source_dir}")
    if not (repo_root / "system_v3").is_dir():
        raise SystemExit(f"missing system_v3 under repo_root: {repo_root}")

    member_bytes = _read_required_members(source_dir)
    boot_id = "UNKNOWN"
    provenance_bytes = member_bytes.get("PROVENANCE.txt", b"")
    for line in provenance_bytes.decode("utf-8", errors="ignore").splitlines():
        if line.strip().startswith("BOOT_ID:"):
            boot_id = line.split(":", 1)[1].strip() or "UNKNOWN"
            break
    readme_path = source_dir / "README.md"
    if boot_id == "UNKNOWN" and readme_path.is_file():
        for line in readme_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith("BOOT_ID:"):
                boot_id = line.split(":", 1)[1].strip() or "UNKNOWN"
                break

    bundle_id = f"FULL_PLUS_SAVE__{time.strftime('%Y%m%d_%H%M%SZ', time.gmtime())}"
    sha256sums = _build_sha256sums(member_bytes)
    manifest_bytes = _build_manifest(
        bundle_id=bundle_id,
        boot_id=boot_id,
        member_bytes=member_bytes,
        source_dir=source_dir,
    )

    out_zip = Path(args.out_zip).expanduser().resolve() if str(args.out_zip).strip() else _default_out_path(repo_root)
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name, data in sorted(member_bytes.items()):
            _write_zip_member(zf, f"restore/{name}", data)
        _write_zip_member(zf, "restore/SHA256SUMS.txt", sha256sums)
        _write_zip_member(zf, "meta/FULL_PLUS_SAVE_MANIFEST_v1.json", manifest_bytes)

    out_sha = _sha256_file(out_zip)
    out_zip.with_suffix(".zip.sha256").write_text(out_sha + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "schema": "FULL_PLUS_SAVE_RESULT_v1",
                "status": "PASS",
                "save_level": "FULL+",
                "out_zip": out_zip.as_posix(),
                "out_zip_sha256": out_sha,
                "bundle_id": bundle_id,
                "boot_id": boot_id,
                "source_dir": source_dir.as_posix(),
                "member_count": len(member_bytes) + 2,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
