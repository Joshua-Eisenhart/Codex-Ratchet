#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path


_FIXED_ZIP_DATETIME = (1980, 1, 1, 0, 0, 0)
_DEFAULT_DEBUG_EXCLUDE_PATTERNS = [
    ".DS_Store",
    "__pycache__/*",
    "*.pyc",
]
_NONRUN_ARCHIVE_EXCLUDE_PATTERNS = [
    "*.zip",
    "*.zip.sha256",
    "*.tar",
    "*.tar.gz",
    "*.tgz",
    "*.7z",
]
_RUN_DUPLICATE_SURFACE_PATTERNS = [
    "outbox/*",
    "snapshots/*",
]
_DEFAULT_BOOTSTRAP_EXCLUDE_PATTERNS = _DEFAULT_DEBUG_EXCLUDE_PATTERNS + [
    "*.zip",
    "*.zip.sha256",
    "*.tar",
    "*.tar.gz",
    "*.tgz",
    "*.7z",
]


@dataclass(frozen=True)
class _ManifestEntry:
    rel_path: str
    byte_size: int
    sha256: str


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc_compact_timestamp() -> str:
    return time.strftime("%Y%m%d_%H%M%SZ", time.gmtime())


def _normalize_posix(path: Path) -> str:
    return path.as_posix()


def _is_excluded(rel_path: str, exclude_prefixes: list[str], exclude_patterns: list[str]) -> bool:
    for prefix in exclude_prefixes:
        if rel_path == prefix or rel_path.startswith(prefix + "/"):
            return True
    base_name = rel_path.rsplit("/", 1)[-1]
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(base_name, pattern):
            return True
    return False


def _iter_files_under(root: Path) -> list[Path]:
    files: list[Path] = []
    for p in root.rglob("*"):
        if p.is_file():
            files.append(p)
    files.sort(key=lambda p: p.as_posix())
    return files


def _build_bootstrap_file_list(repo_root: Path) -> list[Path]:
    roots = [
        repo_root / "core_docs",
        repo_root / "system_v3",
    ]
    exclude_prefixes = [
        "system_v3/runs",
        "archive",
        "system_v3/a2_state/snapshots",
    ]
    exclude_patterns = list(_DEFAULT_BOOTSTRAP_EXCLUDE_PATTERNS)

    out: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for p in _iter_files_under(root):
            rel = _normalize_posix(p.relative_to(repo_root))
            if _is_excluded(rel, exclude_prefixes, exclude_patterns):
                continue
            out.append(p)
    out.sort(key=lambda p: p.as_posix())
    return out


def _build_debug_file_list(repo_root: Path, include_run_ids: list[str]) -> list[Path]:
    roots = [
        repo_root / "core_docs",
        repo_root / "system_v3",
    ]
    selected_run_prefixes = [f"system_v3/runs/{rid}" for rid in include_run_ids]
    selected_run_prefixes.extend(["system_v3/runs/_CURRENT_RUN.txt", "system_v3/runs/_CURRENT_STATE"])
    exclude_prefixes = [
        "system_v3/runs/LEGACY__MIGRATED__",
        "archive",
        "system_v3/a2_state/snapshots",
    ]
    exclude_patterns = list(_DEFAULT_DEBUG_EXCLUDE_PATTERNS)
    nonrun_exclude_patterns = list(_DEFAULT_DEBUG_EXCLUDE_PATTERNS) + list(_NONRUN_ARCHIVE_EXCLUDE_PATTERNS)

    out: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for p in _iter_files_under(root):
            rel = _normalize_posix(p.relative_to(repo_root))
            if _is_excluded(rel, exclude_prefixes, exclude_patterns):
                continue
            if rel.startswith("system_v3/runs/"):
                keep = False
                for prefix in selected_run_prefixes:
                    if rel == prefix or rel.startswith(prefix + "/"):
                        keep = True
                        break
                if not keep:
                    continue
                # Selected runs should still exclude duplicate plaintext helper
                # surfaces; packet/tape/state lineage remains the authoritative save.
                if _is_excluded(rel, [], _RUN_DUPLICATE_SURFACE_PATTERNS):
                    continue
            else:
                # Debug profile keeps selected run packets (including ZIP payloads),
                # but excludes non-run archive files to avoid nested system-image
                # contamination and accidental huge payload pickup.
                if _is_excluded(rel, [], nonrun_exclude_patterns):
                    continue
            out.append(p)
    out.sort(key=lambda p: p.as_posix())
    return out


def _build_manifest(
    *,
    repo_root: Path,
    profile: str,
    include_run_ids: list[str],
    files: list[Path],
) -> dict:
    entries: list[_ManifestEntry] = []
    for p in files:
        rel = _normalize_posix(p.relative_to(repo_root))
        entries.append(_ManifestEntry(rel_path=rel, byte_size=p.stat().st_size, sha256=_sha256_file(p)))
    return {
        "schema": "SYSTEM_SAVE_PROFILE_MANIFEST_v1",
        "profile": profile,
        "include_run_ids": include_run_ids,
        "file_count": len(entries),
        "files": [{"rel_path": e.rel_path, "byte_size": e.byte_size, "sha256": e.sha256} for e in entries],
    }


def _write_zip(*, out_zip: Path, repo_root: Path, files: list[Path], manifest_bytes: bytes) -> None:
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zi = zipfile.ZipInfo("SYSTEM_SAVE_PROFILE_MANIFEST_v1.json", date_time=_FIXED_ZIP_DATETIME)
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = 0o644 << 16
        zf.writestr(zi, manifest_bytes)

        for p in files:
            rel = _normalize_posix(p.relative_to(repo_root))
            data = p.read_bytes()
            zi = zipfile.ZipInfo(rel, date_time=_FIXED_ZIP_DATETIME)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            zf.writestr(zi, data)


def _default_out_path(repo_root: Path, profile: str) -> Path:
    ts = _utc_compact_timestamp()
    return repo_root / "system_v3" / "runs" / "_save_exports" / f"SYSTEM_SAVE__{profile}__{ts}.zip"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=["bootstrap", "debug"], required=True)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--out-zip", default="")
    ap.add_argument(
        "--include-run-id",
        action="append",
        default=[],
        help="Run ID to include for debug profile. May be repeated.",
    )
    args = ap.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    profile = str(args.profile)
    include_run_ids = sorted(set(str(v).strip() for v in args.include_run_id if str(v).strip()))

    if not (repo_root / "system_v3").is_dir():
        raise SystemExit(f"missing system_v3 under repo_root: {repo_root}")
    if not (repo_root / "core_docs").is_dir():
        raise SystemExit(f"missing core_docs under repo_root: {repo_root}")
    if profile == "debug" and not include_run_ids:
        raise SystemExit("debug profile requires at least one --include-run-id")

    if profile == "bootstrap":
        files = _build_bootstrap_file_list(repo_root)
    else:
        files = _build_debug_file_list(repo_root, include_run_ids=include_run_ids)

    manifest = _build_manifest(
        repo_root=repo_root,
        profile=profile,
        include_run_ids=include_run_ids,
        files=files,
    )
    manifest_bytes = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()

    out_zip = Path(args.out_zip).resolve() if str(args.out_zip).strip() else _default_out_path(repo_root, profile=profile)
    _write_zip(out_zip=out_zip, repo_root=repo_root, files=files, manifest_bytes=manifest_bytes)
    out_sha = _sha256_file(out_zip)
    out_zip.with_suffix(".zip.sha256").write_text(out_sha + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "schema": "SYSTEM_SAVE_PROFILE_RESULT_v1",
                "profile": profile,
                "out_zip": out_zip.as_posix(),
                "out_zip_sha256": out_sha,
                "manifest_sha256": manifest_sha256,
                "file_count": int(manifest["file_count"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
