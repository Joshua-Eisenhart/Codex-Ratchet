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
_DEFAULT_EXCLUDE_PATTERNS = [
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
_DEFAULT_SYSTEM_SAVE_EXCLUDE_PREFIXES = [
    "system_v3/runs",
    "archive",
    "system_v3/a2_state/snapshots",
]


@dataclass(frozen=True)
class _ManifestEntry:
    rel_path: str
    byte_size: int
    sha256: str


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


def _normalize_posix(path: Path) -> str:
    return path.as_posix()


def _matches_prefix(rel_path: str, prefixes: list[str]) -> bool:
    for prefix in prefixes:
        if rel_path == prefix or rel_path.startswith(prefix + "/"):
            return True
    return False


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


def _build_system_save_file_list(
    repo_root: Path,
    profile: str,
    include_run_ids: list[str],
    only_path_prefixes: list[str],
    extra_exclude_prefixes: list[str],
    include_default_roots: bool,
) -> list[Path]:
    if not include_default_roots:
        return []
    roots = [
        repo_root / "core_docs",
        repo_root / "system_v3",
    ]
    exclude_prefixes = list(_DEFAULT_SYSTEM_SAVE_EXCLUDE_PREFIXES)
    exclude_prefixes.extend(extra_exclude_prefixes)
    if profile == "debug":
        selected_run_prefixes = [f"system_v3/runs/{rid}" for rid in include_run_ids]
        selected_run_prefixes.extend(["system_v3/runs/_CURRENT_RUN.txt", "system_v3/runs/_CURRENT_STATE"])
        exclude_prefixes = [
            "system_v3/runs/LEGACY__MIGRATED__",
            "archive",
            "system_v3/a2_state/snapshots",
        ]
        exclude_prefixes.extend(extra_exclude_prefixes)
    exclude_patterns = list(_DEFAULT_EXCLUDE_PATTERNS)
    if profile == "bootstrap":
        exclude_patterns.extend(_NONRUN_ARCHIVE_EXCLUDE_PATTERNS)

    out: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for p in _iter_files_under(root):
            rel = _normalize_posix(p.relative_to(repo_root))
            if _is_excluded(rel, exclude_prefixes, exclude_patterns):
                continue
            if only_path_prefixes and not _matches_prefix(rel, only_path_prefixes):
                continue
            if profile == "debug" and rel.startswith("system_v3/runs/"):
                keep = False
                for prefix in selected_run_prefixes:
                    if rel == prefix or rel.startswith(prefix + "/"):
                        keep = True
                        break
                if not keep:
                    continue
            out.append(p)
    out.sort(key=lambda p: p.as_posix())
    return out


def _collect_explicit_include_files(repo_root: Path, relpaths: list[str]) -> list[Path]:
    out: list[Path] = []
    for rel in relpaths:
        rel = str(rel).strip().strip("/")
        if not rel:
            continue
        target = (repo_root / rel).resolve()
        try:
            target.relative_to(repo_root)
        except ValueError as exc:
            raise SystemExit(f"include_relpath_outside_repo:{rel}") from exc
        if not target.exists():
            raise SystemExit(f"missing_include_relpath:{rel}")
        if target.is_file():
            out.append(target)
            continue
        for p in _iter_files_under(target):
            out.append(p)
    out.sort(key=lambda p: p.as_posix())
    return out


def _read_job_zip_entries(job_zip: Path) -> list[tuple[str, bytes]]:
    entries: list[tuple[str, bytes]] = []
    with zipfile.ZipFile(job_zip, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            rel = str(info.filename)
            if _is_excluded(rel, [], _DEFAULT_EXCLUDE_PATTERNS):
                continue
            data = zf.read(info.filename)
            entries.append((rel, data))
    entries.sort(key=lambda it: it[0])
    return entries


def _build_manifest(
    *,
    repo_root: Path,
    profile: str,
    include_run_ids: list[str],
    include_default_roots: bool,
    only_path_prefixes: list[str],
    exclude_path_prefixes: list[str],
    include_relpaths: list[str],
    system_files: list[Path],
    job_zip: Path,
    job_entries: list[tuple[str, bytes]],
    extra_entries: list[tuple[str, bytes]],
) -> dict:
    files: list[_ManifestEntry] = []
    for p in system_files:
        rel = _normalize_posix(p.relative_to(repo_root))
        files.append(_ManifestEntry(rel_path=rel, byte_size=p.stat().st_size, sha256=_sha256_file(p)))
    for rel, data in job_entries:
        files.append(_ManifestEntry(rel_path=rel, byte_size=len(data), sha256=_sha256_bytes(data)))
    for rel, data in extra_entries:
        files.append(_ManifestEntry(rel_path=rel, byte_size=len(data), sha256=_sha256_bytes(data)))
    files.sort(key=lambda e: e.rel_path)

    return {
        "schema": "PRO_BOOT_JOB_MANIFEST_v1",
        "profile": profile,
        "include_run_ids": include_run_ids,
        "include_default_roots": include_default_roots,
        "only_path_prefixes": only_path_prefixes,
        "exclude_path_prefixes": exclude_path_prefixes,
        "include_relpaths": include_relpaths,
        "job_zip": job_zip.name,
        "job_zip_sha256": _sha256_file(job_zip),
        "file_count": len(files),
        "files": [{"rel_path": e.rel_path, "byte_size": e.byte_size, "sha256": e.sha256} for e in files],
    }


def _write_zip(*, out_zip: Path, repo_root: Path, system_files: list[Path], job_entries: list[tuple[str, bytes]], extra_entries: list[tuple[str, bytes]], manifest_bytes: bytes) -> None:
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zi = zipfile.ZipInfo("PRO_BOOT_JOB_MANIFEST_v1.json", date_time=_FIXED_ZIP_DATETIME)
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = 0o644 << 16
        zf.writestr(zi, manifest_bytes)

        for p in system_files:
            rel = _normalize_posix(p.relative_to(repo_root))
            data = p.read_bytes()
            zi = zipfile.ZipInfo(rel, date_time=_FIXED_ZIP_DATETIME)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            zf.writestr(zi, data)

        for rel, data in job_entries:
            zi = zipfile.ZipInfo(rel, date_time=_FIXED_ZIP_DATETIME)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            zf.writestr(zi, data)

        for rel, data in extra_entries:
            zi = zipfile.ZipInfo(rel, date_time=_FIXED_ZIP_DATETIME)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            zf.writestr(zi, data)


def _default_out_path(repo_root: Path, job_zip: Path) -> Path:
    ts = _utc_compact_timestamp()
    # Keep batch-first name if present; otherwise prefix with PRO_BOOT_JOB.
    base = job_zip.stem
    if base.startswith("BATCH_") or base.startswith("RUN_"):
        name = f"{base}__PRO_BOOT__{ts}.zip"
    else:
        name = f"PRO_BOOT_JOB__{base}__{ts}.zip"
    return repo_root / "work" / "to_send_to_pro" / "jobs" / name


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=["bootstrap", "debug"], default="bootstrap")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--out-zip", default="")
    ap.add_argument("--job-zip", required=True)
    ap.add_argument("--include-run-id", action="append", default=[], help="Run ID to include in debug profile. May be repeated.")
    ap.add_argument(
        "--only-path-prefix",
        action="append",
        default=[],
        help="Restrict default repo boot files to these relative path prefixes. May be repeated.",
    )
    ap.add_argument(
        "--exclude-path-prefix",
        action="append",
        default=[],
        help="Additional relative path prefixes to exclude from the default repo boot set. May be repeated.",
    )
    ap.add_argument(
        "--include-relpath",
        action="append",
        default=[],
        help="Additional repo-relative file or directory to include explicitly (for narrow controller packs). May be repeated.",
    )
    ap.add_argument(
        "--no-default-system-save",
        action="store_true",
        help="Use only explicit include-relpaths and skip the default core_docs/system_v3 boot roots.",
    )
    args = ap.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    profile = str(args.profile)
    include_run_ids = sorted(set(str(v).strip() for v in args.include_run_id if str(v).strip()))
    only_path_prefixes = sorted(set(str(v).strip().strip("/") for v in args.only_path_prefix if str(v).strip()))
    exclude_path_prefixes = sorted(set(str(v).strip().strip("/") for v in args.exclude_path_prefix if str(v).strip()))
    include_relpaths = sorted(set(str(v).strip().strip("/") for v in args.include_relpath if str(v).strip()))
    include_default_roots = not bool(args.no_default_system_save)

    job_zip = Path(args.job_zip).resolve()
    if not job_zip.is_file():
        raise SystemExit(f"missing job_zip: {job_zip}")

    if not (repo_root / "system_v3").is_dir():
        raise SystemExit(f"missing system_v3 under repo_root: {repo_root}")
    if not (repo_root / "core_docs").is_dir():
        raise SystemExit(f"missing core_docs under repo_root: {repo_root}")
    if profile == "debug" and not include_run_ids:
        raise SystemExit("debug profile requires at least one --include-run-id")

    system_files = _build_system_save_file_list(
        repo_root,
        profile=profile,
        include_run_ids=include_run_ids,
        only_path_prefixes=only_path_prefixes,
        extra_exclude_prefixes=exclude_path_prefixes,
        include_default_roots=include_default_roots,
    )
    explicit_include_files = _collect_explicit_include_files(repo_root, include_relpaths)
    deduped: dict[str, Path] = {}
    for p in system_files + explicit_include_files:
        rel = _normalize_posix(p.relative_to(repo_root))
        deduped[rel] = p
    system_files = [deduped[k] for k in sorted(deduped)]
    job_entries = _read_job_zip_entries(job_zip)

    runme = "\n".join(
        [
            "# PRO_BOOT_JOB bundle v1",
            "Status: ACTIVE",
            "",
            "This zip contains:",
            "- `system_v3/` (system save)",
            "- `core_docs/` (fuel, including `core_docs/a1_refined_Ratchet Fuel/`)",
            "- the attached job bundle contents (batch/task scaffold).",
            "",
            "How to run in a fresh Pro thread:",
            "1) Attach this zip.",
            "2) Say: `run` (or nothing).",
            "3) Follow the job's own `meta/README.md` + `tasks/*.task.md` order.",
            "",
            "Do not smooth contradictions. Fail closed if a required file is missing.",
            "",
            "Boot pack scope:",
            f"- profile: {profile}",
            f"- include_default_roots: {include_default_roots}",
            f"- only_path_prefixes: {only_path_prefixes or ['<default-root-scope>']}",
            f"- exclude_path_prefixes: {exclude_path_prefixes or []}",
            f"- include_relpaths: {include_relpaths or []}",
            "",
        ]
    ).encode("utf-8")
    extra_entries = [("00_RUN_ME_FIRST__PRO_BOOT_JOB__v1.md", runme)]

    manifest = _build_manifest(
            repo_root=repo_root,
            profile=profile,
            include_run_ids=include_run_ids,
            include_default_roots=include_default_roots,
            only_path_prefixes=only_path_prefixes,
            exclude_path_prefixes=exclude_path_prefixes,
            include_relpaths=include_relpaths,
            system_files=system_files,
            job_zip=job_zip,
            job_entries=job_entries,
        extra_entries=extra_entries,
    )
    manifest_bytes = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    manifest_sha256 = _sha256_bytes(manifest_bytes)

    out_zip = Path(args.out_zip).resolve() if str(args.out_zip).strip() else _default_out_path(repo_root, job_zip=job_zip)
    _write_zip(
        out_zip=out_zip,
        repo_root=repo_root,
        system_files=system_files,
        job_entries=job_entries,
        extra_entries=extra_entries,
        manifest_bytes=manifest_bytes,
    )
    out_sha = _sha256_file(out_zip)
    out_zip.with_suffix(".zip.sha256").write_text(out_sha + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "schema": "PRO_BOOT_JOB_RESULT_v1",
                "profile": profile,
                "out_zip": out_zip.as_posix(),
                "out_zip_sha256": out_sha,
                "manifest_sha256": manifest_sha256,
                "job_zip": job_zip.as_posix(),
                "job_zip_sha256": _sha256_file(job_zip),
                "file_count": int(manifest["file_count"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
