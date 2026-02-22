#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SHARD_RE = re.compile(r"^(.+)\.(\d{3})\.jsonl$")


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _status(flag: bool) -> str:
    return "PASS" if flag else "FAIL"


def _collect_shards(path: Path) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = {}
    if not path.exists():
        return groups
    for file_path in sorted(path.glob("*.jsonl")):
        m = SHARD_RE.match(file_path.name)
        if not m:
            continue
        stem = m.group(1)
        groups.setdefault(stem, []).append(file_path)
    return groups


def _contiguous_from_zero(paths: list[Path]) -> bool:
    indexes: list[int] = []
    for p in paths:
        m = SHARD_RE.match(p.name)
        if not m:
            return False
        indexes.append(int(m.group(2)))
    return indexes == list(range(len(indexes)))


def _line_count(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        return sum(1 for _ in fh)


def _walk_file_stats(root: Path) -> tuple[int, int]:
    total_files = 0
    total_bytes = 0
    if not root.exists():
        return total_files, total_bytes
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        total_files += 1
        total_bytes += p.stat().st_size
    return total_files, total_bytes


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate P6 long-run write guard gate.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--max-shard-bytes", type=int, default=5_000_000)
    parser.add_argument("--max-shard-lines", type=int, default=200_000)
    parser.add_argument("--max-run-bytes", type=int, default=200_000_000)
    parser.add_argument("--max-run-files", type=int, default=5_000)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    repo_root = Path(__file__).resolve().parents[2]
    reports_dir = run_dir / "reports"

    shard_violations: list[dict] = []
    contiguous_violations: list[str] = []
    shard_groups: dict[str, list[str]] = {}

    for group_root in [run_dir / "logs", run_dir / "tapes"]:
        for stem, paths in sorted(_collect_shards(group_root).items()):
            shard_groups[str(group_root / stem)] = [p.name for p in paths]
            if not _contiguous_from_zero(paths):
                contiguous_violations.append(str(group_root / stem))
            for p in paths:
                size_bytes = p.stat().st_size
                line_count = _line_count(p)
                if size_bytes > args.max_shard_bytes or line_count > args.max_shard_lines:
                    shard_violations.append(
                        {
                            "path": str(p),
                            "size_bytes": size_bytes,
                            "line_count": line_count,
                        }
                    )

    forbidden_hits: list[str] = []
    for forbidden_root_name in ["core_docs", "work", "system_spec_pack_v2"]:
        forbidden_root = repo_root / forbidden_root_name
        if not forbidden_root.exists():
            continue
        for p in forbidden_root.rglob("*"):
            if not p.is_file():
                continue
            if run_dir.name in p.name:
                forbidden_hits.append(str(p))

    run_file_count, run_total_bytes = _walk_file_stats(run_dir)

    checks = [
        {
            "check_id": "RUN_PATH_UNDER_ALLOWED_ROOT",
            "status": _status(str(run_dir).startswith(str(repo_root / "system_v3" / "runs"))),
            "detail": f"run_dir={run_dir}",
        },
        {
            "check_id": "SHARD_SEQUENCE_CONTIGUOUS",
            "status": _status(len(contiguous_violations) == 0),
            "detail": f"violations={len(contiguous_violations)}",
        },
        {
            "check_id": "SHARD_CAPS_RESPECTED",
            "status": _status(len(shard_violations) == 0),
            "detail": f"violations={len(shard_violations)} max_bytes={args.max_shard_bytes} max_lines={args.max_shard_lines}",
        },
        {
            "check_id": "FORBIDDEN_ROOT_WRITE_MARKERS",
            "status": _status(len(forbidden_hits) == 0),
            "detail": f"hits={len(forbidden_hits)}",
        },
        {
            "check_id": "RUN_TOTAL_BYTES_CAP_RESPECTED",
            "status": _status(run_total_bytes <= args.max_run_bytes),
            "detail": f"bytes={run_total_bytes} max_bytes={args.max_run_bytes}",
        },
        {
            "check_id": "RUN_TOTAL_FILES_CAP_RESPECTED",
            "status": _status(run_file_count <= args.max_run_files),
            "detail": f"files={run_file_count} max_files={args.max_run_files}",
        },
    ]

    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    report = {
        "schema": "LONG_RUN_WRITE_GUARD_REPORT_v1",
        "run_id": run_dir.name,
        "status": status,
        "checks": checks,
        "shard_groups": shard_groups,
        "contiguous_violations": contiguous_violations,
        "shard_violations": shard_violations,
        "forbidden_hits": forbidden_hits,
        "run_file_count": run_file_count,
        "run_total_bytes": run_total_bytes,
        "max_run_files": int(args.max_run_files),
        "max_run_bytes": int(args.max_run_bytes),
        "updated_utc": "UNCHANGED_BY_GATE_EVAL",
    }
    out_path = reports_dir / "long_run_write_guard_report.json"
    _write_json(out_path, report)
    print(json.dumps({"status": status, "report_path": str(out_path)}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
