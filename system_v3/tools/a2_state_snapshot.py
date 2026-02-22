#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path


_FIXED_ZIP_DATETIME = (1980, 1, 1, 0, 0, 0)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc_compact_timestamp() -> str:
    return time.strftime("%Y%m%d_%H%M%SZ", time.gmtime())


@dataclass(frozen=True)
class _ManifestEntry:
    rel_path: str
    byte_size: int
    sha256: str


def _iter_a2_state_files(a2_state_dir: Path) -> list[Path]:
    # Keep this conservative and deterministic: only known "brain" artifacts.
    allow_globs = [
        "INTENT_SUMMARY.md",
        "MODEL_CONTEXT.md",
        "memory.jsonl",
        "doc_index.json",
        "constraint_surface.json",
        "rosetta.json",
        "fuel_queue.json",
        "ingest/index_v1.json",
        "ingest/index_v1.sha256",
        "ingest/system_map_v1.md",
        "ingest/doc_cards/*.md",
    ]

    files: list[Path] = []
    for g in allow_globs:
        files.extend(a2_state_dir.glob(g))

    # Exclude OS noise deterministically.
    files = [p for p in files if p.is_file() and p.name != ".DS_Store"]
    files.sort(key=lambda p: p.as_posix())
    return files


def _build_manifest(a2_state_dir: Path, files: list[Path]) -> dict:
    entries: list[_ManifestEntry] = []
    for p in files:
        rel = p.relative_to(a2_state_dir).as_posix()
        entries.append(_ManifestEntry(rel_path=rel, byte_size=p.stat().st_size, sha256=_sha256_file(p)))

    manifest = {
        "schema": "A2_STATE_SNAPSHOT_MANIFEST_v1",
        "a2_state_root": a2_state_dir.as_posix(),
        "file_count": len(entries),
        "files": [
            {"rel_path": e.rel_path, "byte_size": e.byte_size, "sha256": e.sha256}
            for e in entries
        ],
    }
    return manifest


def _write_zip(zip_path: Path, a2_state_dir: Path, files: list[Path], manifest_bytes: bytes) -> None:
    # Deterministic: stable file ordering, fixed timestamps, fixed permissions.
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        # Include manifest first for quick inspection.
        zi = zipfile.ZipInfo("manifest.json", date_time=_FIXED_ZIP_DATETIME)
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = 0o644 << 16
        zf.writestr(zi, manifest_bytes)

        for p in files:
            rel = p.relative_to(a2_state_dir).as_posix()
            data = p.read_bytes()
            zi = zipfile.ZipInfo(rel, date_time=_FIXED_ZIP_DATETIME)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            zf.writestr(zi, data)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a2-state-dir", default="system_v3/a2_state")
    ap.add_argument("--out-dir", default="system_v3/a2_state/snapshots")
    ap.add_argument("--snapshot-id", default="")
    args = ap.parse_args(argv)

    a2_state_dir = Path(args.a2_state_dir).resolve()
    out_root = Path(args.out_dir).resolve()
    snapshot_id = args.snapshot_id.strip() or f"A2_STATE_SNAPSHOT__{_utc_compact_timestamp()}__v1"

    if not a2_state_dir.is_dir():
        raise SystemExit(f"missing a2_state_dir: {a2_state_dir}")

    files = _iter_a2_state_files(a2_state_dir)
    manifest = _build_manifest(a2_state_dir, files)
    manifest_bytes = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    manifest_sha256 = _sha256_bytes(manifest_bytes)

    out_dir = out_root / snapshot_id
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_bytes(manifest_bytes)
    (out_dir / "manifest.sha256").write_text(manifest_sha256 + "\n", encoding="utf-8")

    zip_path = out_dir / "a2_state_snapshot.zip"
    _write_zip(zip_path, a2_state_dir, files, manifest_bytes)
    (out_dir / "a2_state_snapshot.zip.sha256").write_text(_sha256_file(zip_path) + "\n", encoding="utf-8")

    # Print machine-usable output only.
    sys.stdout.write(json.dumps({"out_dir": out_dir.as_posix(), "manifest_sha256": manifest_sha256}) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

