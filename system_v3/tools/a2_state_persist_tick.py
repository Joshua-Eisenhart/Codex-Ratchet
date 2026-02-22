#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
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


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_int(path: Path, default: int) -> int:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except FileNotFoundError:
        return default


def _store_int(path: Path, value: int) -> None:
    path.write_text(str(value) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class _ManifestEntry:
    rel_path: str
    byte_size: int
    sha256: str


def _iter_a2_state_files(a2_state_dir: Path) -> list[Path]:
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
    files = [p for p in files if p.is_file() and p.name != ".DS_Store"]
    files.sort(key=lambda p: p.as_posix())
    return files


def _build_manifest(a2_state_dir: Path, files: list[Path]) -> dict:
    entries: list[_ManifestEntry] = []
    total_bytes = 0
    for p in files:
        rel = p.relative_to(a2_state_dir).as_posix()
        size = p.stat().st_size
        total_bytes += size
        entries.append(_ManifestEntry(rel_path=rel, byte_size=size, sha256=_sha256_file(p)))

    manifest = {
        "schema": "A2_STATE_MANIFEST_v1",
        "file_count": len(entries),
        "total_bytes": total_bytes,
        "files": [
            {"rel_path": e.rel_path, "byte_size": e.byte_size, "sha256": e.sha256}
            for e in entries
        ],
    }
    return manifest


def _write_latest_zip(zip_path: Path, a2_state_dir: Path, files: list[Path], manifest_bytes: bytes) -> str:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
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

    return _sha256_file(zip_path)


def _append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def _load_shard_index(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except FileNotFoundError:
        return []
    return []


def _write_shard_index(path: Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def _maybe_shard_memory(a2_state_dir: Path, max_bytes: int, retain_shards: int) -> None:
    mem = a2_state_dir / "memory.jsonl"
    if not mem.exists():
        return
    if mem.stat().st_size <= max_bytes:
        return

    shard_dir = a2_state_dir / "memory_shards"
    shard_dir.mkdir(parents=True, exist_ok=True)
    index_path = shard_dir / "index_v1.json"
    index = _load_shard_index(index_path)
    next_n = 1
    if index:
        next_n = max(int(it.get("shard_n", 0)) for it in index) + 1

    shard_name = f"memory_shard_{next_n:06d}.jsonl"
    shard_path = shard_dir / shard_name
    mem.replace(shard_path)

    shard_sha = _sha256_file(shard_path)
    index.append({"shard_n": next_n, "rel_path": shard_name, "sha256": shard_sha, "byte_size": shard_path.stat().st_size})
    index.sort(key=lambda it: int(it["shard_n"]))
    _write_shard_index(index_path, index)
    (shard_dir / "index_v1.sha256").write_text(_sha256_file(index_path) + "\n", encoding="utf-8")

    # Start a new live memory.jsonl with an explicit shard-open marker.
    _append_jsonl(mem, {"ts": _utc_iso(), "type": "memory_shard_open", "prev_shard": shard_name, "prev_shard_sha256": shard_sha})

    if retain_shards > 0 and len(index) > retain_shards:
        drop = len(index) - retain_shards
        to_drop = index[:drop]
        keep = index[drop:]
        for it in to_drop:
            try:
                (shard_dir / it["rel_path"]).unlink()
            except FileNotFoundError:
                pass
        _write_shard_index(index_path, keep)
        (shard_dir / "index_v1.sha256").write_text(_sha256_file(index_path) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a2-state-dir", default="system_v3/a2_state")
    ap.add_argument("--write-latest-zip", action="store_true")
    ap.add_argument("--max-memory-bytes", type=int, default=1_000_000)
    ap.add_argument("--retain-shards", type=int, default=64)
    args = ap.parse_args(argv)

    repo_root = Path.cwd().resolve()
    a2_state_dir = (repo_root / args.a2_state_dir).resolve()
    if not a2_state_dir.is_dir():
        raise SystemExit(f"missing a2_state_dir: {a2_state_dir}")

    seq_path = a2_state_dir / "autosave_seq.txt"
    seq = _load_int(seq_path, 0) + 1
    _store_int(seq_path, seq)

    files = _iter_a2_state_files(a2_state_dir)
    manifest = _build_manifest(a2_state_dir, files)
    manifest_bytes = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    manifest_sha256 = _sha256_bytes(manifest_bytes)

    latest_zip_sha256 = None
    if args.write_latest_zip:
        latest_zip = a2_state_dir / "snapshots" / "a2_state_snapshot_latest.zip"
        latest_zip_sha256 = _write_latest_zip(latest_zip, a2_state_dir, files, manifest_bytes)
        (latest_zip.with_suffix(".zip.sha256")).write_text(latest_zip_sha256 + "\n", encoding="utf-8")

    event = {
        "ts": _utc_iso(),
        "type": "a2_autosave_tick",
        "seq": seq,
        "manifest_sha256": manifest_sha256,
        "file_count": int(manifest["file_count"]),
        "total_bytes": int(manifest["total_bytes"]),
    }
    if latest_zip_sha256 is not None:
        event["latest_zip_sha256"] = latest_zip_sha256

    _append_jsonl(a2_state_dir / "memory.jsonl", event)
    _maybe_shard_memory(a2_state_dir, max_bytes=int(args.max_memory_bytes), retain_shards=int(args.retain_shards))

    os.sys.stdout.write(json.dumps({"seq": seq, "manifest_sha256": manifest_sha256}) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(os.sys.argv[1:]))

