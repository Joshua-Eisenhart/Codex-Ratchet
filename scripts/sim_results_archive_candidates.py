#!/usr/bin/env python3
"""Build a dry-run archive manifest for generated sim result JSONs.

This script intentionally does not move files. The sim_results tree is still a
canonical receipt surface, so cleanup must start with a conservative manifest.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "system_v4" / "probes" / "a2_state" / "sim_results"
OUT_JSON = ROOT / "system_v5" / "evidence" / "sim_results_archive_candidate_manifest.json"
SAFETY_WINDOW_SECONDS = 72 * 60 * 60
MAX_SCAN_BYTES = 2_000_000
REFERENCE_TOKEN_RE = re.compile(r"[A-Za-z0-9_./:@+-]+")
TEXT_SCAN_PATHS = (
    "README.md",
    "REPO_LAYOUT.md",
    "scripts",
    "system_v4/tests",
    "system_v5/docs",
    "system_v5/tests",
    "system_v5/evidence/a2_state_manifest_2026-05-10.json",
    "system_v5/evidence/tool_function_receipt_matrix.json",
    "visualizer",
)
RUNTIME_JSON_SCAN_PATHS = (
    "system_v5/ops/wizard_admissions",
    "system_v5/ops/wizard_admission_receipts",
    "system_v4/probes/a2_state/queue",
)


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def run_git_z(root: Path, args: list[str], stdin: bytes | None = None) -> list[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        input=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode not in {0, 1}:
        return []
    return [item for item in proc.stdout.decode("utf-8", errors="replace").split("\0") if item]


def git_tracked_paths(root: Path, scope: str) -> set[str]:
    return set(run_git_z(root, ["ls-files", "-z", "--", scope]))


def git_ignored_paths(root: Path, paths: list[str]) -> set[str]:
    if not paths:
        return set()
    payload = "\0".join(paths).encode("utf-8") + b"\0"
    return set(run_git_z(root, ["check-ignore", "-z", "--stdin"], stdin=payload))


def result_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.glob("*.json") if path.is_file())


def scan_files(root: Path, paths: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for item in paths:
        path = root / item
        if not path.exists():
            continue
        if path.is_file():
            files.append(path)
            continue
        for child in path.rglob("*"):
            if not child.is_file():
                continue
            if RESULT_ROOT in child.parents:
                continue
            if child.suffix.lower() in {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip"}:
                continue
            files.append(child)
    return files


def text_scan_files(root: Path) -> list[Path]:
    return scan_files(root, TEXT_SCAN_PATHS)


def runtime_json_scan_files(root: Path) -> list[Path]:
    return [
        path
        for path in scan_files(root, RUNTIME_JSON_SCAN_PATHS)
        if ".json" in path.name
    ]


def token_variants(token: str) -> set[str]:
    stripped = token.strip().strip("\"'`,:;()[]{}")
    if not stripped:
        return set()
    path = Path(stripped)
    variants = {stripped, path.name}
    if path.suffix:
        variants.add(path.stem)
    return {variant for variant in variants if variant}


def reference_tokens(text: str) -> set[str]:
    """Extract only result-like tokens without running a broad path regex."""
    if "_results" not in text and "sim_results" not in text:
        return set()
    tokens: set[str] = set()
    for raw in REFERENCE_TOKEN_RE.findall(text):
        if "_results" not in raw and "sim_results" not in raw:
            continue
        tokens.update(token_variants(raw))
    return tokens


def read_limited_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_SCAN_BYTES:
            return None
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.read(MAX_SCAN_BYTES)
    except OSError:
        return None


def reference_index(
    root: Path,
    candidate_files: list[Path],
    *,
    include_runtime_reference_scan: bool,
) -> dict[str, list[str]]:
    candidate_keys: set[str] = set()
    for path in candidate_files:
        candidate_keys.add(path.name)
        candidate_keys.add(path.stem)
        candidate_keys.add(rel(path, root))

    references: dict[str, list[str]] = defaultdict(list)
    for path in text_scan_files(root):
        text = read_limited_text(path)
        if text is None:
            continue
        source = rel(path, root)
        for variant in reference_tokens(text) & candidate_keys:
            if len(references[variant]) < 5:
                references[variant].append(source)
    if include_runtime_reference_scan:
        for path in runtime_json_scan_files(root):
            text = read_limited_text(path)
            if text is None:
                continue
            source = rel(path, root)
            for variant in reference_tokens(text) & candidate_keys:
                if len(references[variant]) < 5:
                    references[variant].append(source)
    return dict(references)


def reference_hits(path: Path, root: Path, refs: dict[str, list[str]]) -> list[str]:
    hits: list[str] = []
    for key in (rel(path, root), path.name, path.stem):
        for source in refs.get(key, []):
            if source not in hits:
                hits.append(source)
    return hits[:10]


def build_manifest(
    *,
    root: Path = ROOT,
    now: float | None = None,
    tracked_paths: set[str] | None = None,
    ignored_paths: set[str] | None = None,
    include_runtime_reference_scan: bool = False,
) -> dict[str, Any]:
    now = time.time() if now is None else now
    result_root = root / "system_v4" / "probes" / "a2_state" / "sim_results"
    files = result_files(result_root)
    rel_paths = [rel(path, root) for path in files]
    tracked = tracked_paths if tracked_paths is not None else git_tracked_paths(root, rel(result_root, root))
    ignored = ignored_paths if ignored_paths is not None else git_ignored_paths(root, rel_paths)
    refs = reference_index(
        root,
        files,
        include_runtime_reference_scan=include_runtime_reference_scan,
    )

    rows: list[dict[str, Any]] = []
    for path in files:
        rel_path = rel(path, root)
        stat = path.stat()
        age = max(0.0, now - stat.st_mtime)
        hits = reference_hits(path, root, refs)
        blockers: list[str] = []
        if rel_path in tracked:
            blockers.append("tracked_file")
        if rel_path not in ignored:
            blockers.append("not_gitignored")
        if age < SAFETY_WINDOW_SECONDS:
            blockers.append("inside_72h_safety_window")
        if hits:
            blockers.append("referenced_by_current_surface")
        if not include_runtime_reference_scan and not blockers:
            blockers.append("runtime_reference_scan_not_run")
        decision = "MOVE_TO_ARCHIVE_CANDIDATE" if not blockers else "KEEP_OR_REVIEW"
        rows.append(
            {
                "path": rel_path,
                "decision": decision,
                "blockers": blockers,
                "reference_hits": hits,
                "age_seconds": age,
                "bytes": stat.st_size,
            }
        )

    blocker_counts = Counter(blocker for row in rows for blocker in row["blockers"])
    decision_counts = Counter(row["decision"] for row in rows)
    candidates = [row for row in rows if row["decision"] == "MOVE_TO_ARCHIVE_CANDIDATE"]
    return {
        "schema": "sim_results_archive_candidate_manifest.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "boundary": {
            "dry_run_only": True,
            "moves_files": False,
            "safety_window_seconds": SAFETY_WINDOW_SECONDS,
            "max_scan_bytes": MAX_SCAN_BYTES,
            "candidate_rule": (
                "ignored && not tracked && older than 72h && not referenced by scanned docs, "
                "scripts, tests, evidence manifests, admissions, receipts, or queues"
            ),
            "runtime_reference_scan_included": include_runtime_reference_scan,
            "fail_closed_when_runtime_scan_skipped": True,
        },
        "summary": {
            "result_file_count": len(rows),
            "tracked_count": sum(1 for row in rows if "tracked_file" in row["blockers"]),
            "ignored_count": sum(1 for row in rows if "not_gitignored" not in row["blockers"]),
            "candidate_count": len(candidates),
            "candidate_bytes": sum(int(row["bytes"]) for row in candidates),
            "decision_counts": dict(decision_counts),
            "blocker_counts": dict(blocker_counts),
        },
        "scan_paths": {
            "text": list(TEXT_SCAN_PATHS),
            "runtime_json": list(RUNTIME_JSON_SCAN_PATHS),
            "runtime_json_status": (
                "scanned" if include_runtime_reference_scan else "skipped_fail_closed"
            ),
        },
        "candidate_samples": candidates[:50],
        "blocked_samples": [row for row in rows if row["blockers"]][:50],
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", default=str(OUT_JSON))
    parser.add_argument(
        "--include-runtime-reference-scan",
        action="store_true",
        help="Also scan admissions/receipt/queue JSON references. Slower; default skips fail-closed.",
    )
    args = parser.parse_args()
    manifest = build_manifest(
        include_runtime_reference_scan=args.include_runtime_reference_scan,
    )
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = manifest["summary"]
    print(f"wrote {out}")
    print(
        "result_file_count={result_file_count} candidate_count={candidate_count} "
        "candidate_bytes={candidate_bytes}".format(**summary)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
