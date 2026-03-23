#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path


def _infer_repo_root(start: Path) -> Path:
    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent
    for _ in range(10):
        if (cur / "system_v3").is_dir():
            return cur
        cur = cur.parent
    return start.resolve()


def _resolve_repo_root(repo_root_raw: str) -> Path:
    raw = str(repo_root_raw or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    env = str(os.environ.get("CODEX_RATCHET_ROOT", "") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return _infer_repo_root(Path(__file__).resolve())


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_\\-]{0,63}$")


@dataclass(frozen=True)
class OutputRootFinding:
    kind: str  # "dir" | "zip"
    root: str  # filesystem path or zip prefix


def _find_output_roots_in_dir(base: Path) -> list[Path]:
    roots: list[Path] = []
    if base.is_file():
        return roots
    # Find directories literally named "output".
    for p in base.rglob("output"):
        if p.is_dir():
            roots.append(p)
    # Deterministic order, shortest paths first.
    roots = sorted(set(roots), key=lambda p: (len(p.parts), str(p).lower()))
    return roots


def _find_output_roots_in_zip(z: zipfile.ZipFile) -> list[str]:
    roots: set[str] = set()
    for name in z.namelist():
        parts = [p for p in name.split("/") if p]
        for i, seg in enumerate(parts):
            if seg == "output":
                prefix = "/".join(parts[: i + 1])
                roots.add(prefix)
                break
    return sorted(roots, key=lambda s: (len(s.split("/")), s.lower()))


def _zip_has_member(z: zipfile.ZipFile, member: str) -> bool:
    try:
        z.getinfo(member)
        return True
    except KeyError:
        return False


def _validate_topics_in_zip(z: zipfile.ZipFile, output_prefix: str) -> dict:
    # output_prefix like "wiggle_job_output/output"
    topics_prefix = output_prefix.rstrip("/") + "/topics/"
    has_topics_dir = any(n.startswith(topics_prefix) for n in z.namelist())

    slugs: set[str] = set()
    invalid_slugs: set[str] = set()
    empty_slug_topic_files: list[str] = []

    for name in z.namelist():
        if not name.startswith(topics_prefix):
            continue
        rel = name[len(topics_prefix) :]
        rel_parts = [p for p in rel.split("/") if p]
        if not rel_parts:
            continue
        # If the first segment looks like a topic file directly under topics/, that's an empty slug.
        first = rel_parts[0]
        if first.startswith("TOPIC_") and first.endswith(".md"):
            empty_slug_topic_files.append(name)
            continue
        slug = first
        slugs.add(slug)
        if slug in {".", ".."} or not SLUG_RE.match(slug):
            invalid_slugs.add(slug)

    return {
        "output_root": output_prefix,
        "has_topics_dir": bool(has_topics_dir),
        "topic_slug_count": len(slugs),
        "topic_slugs_sample": sorted(list(slugs))[:30],
        "invalid_slug_count": len(invalid_slugs),
        "invalid_slugs_sample": sorted(list(invalid_slugs))[:30],
        "empty_slug_topic_file_count": len(empty_slug_topic_files),
        "empty_slug_topic_files_sample": empty_slug_topic_files[:30],
    }


def _validate_topics_in_dir(output_root: Path) -> dict:
    topics_dir = output_root / "topics"
    has_topics_dir = topics_dir.is_dir()

    slugs: set[str] = set()
    invalid_slugs: set[str] = set()
    empty_slug_topic_files: list[str] = []

    if has_topics_dir:
        # Any TOPIC_*.md directly under topics/ indicates empty topic_slug in generation.
        for p in sorted(topics_dir.glob("TOPIC_*.md"), key=lambda x: x.name.lower()):
            empty_slug_topic_files.append(str(p))

        for p in sorted([d for d in topics_dir.iterdir() if d.is_dir()], key=lambda x: x.name.lower()):
            slug = p.name
            slugs.add(slug)
            if slug in {".", ".."} or not SLUG_RE.match(slug):
                invalid_slugs.add(slug)

    return {
        "output_root": str(output_root),
        "has_topics_dir": bool(has_topics_dir),
        "topic_slug_count": len(slugs),
        "topic_slugs_sample": sorted(list(slugs))[:30],
        "invalid_slug_count": len(invalid_slugs),
        "invalid_slugs_sample": sorted(list(invalid_slugs))[:30],
        "empty_slug_topic_file_count": len(empty_slug_topic_files),
        "empty_slug_topic_files_sample": empty_slug_topic_files[:30],
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fail-closed validation for A2 topic extraction outputs (empty slug, slug syntax, discovery topic-count)."
    )
    ap.add_argument("--repo-root", default="", help="Repo root (optional).")
    ap.add_argument("--path", required=True, help="A zip file or directory containing one or more output/ trees.")
    ap.add_argument("--mode", choices=["discovery", "focus"], default="discovery")
    ap.add_argument("--min-topic-slugs", type=int, default=10, help="Minimum topic slugs required (discovery mode).")
    ap.add_argument("--max-topic-slugs", type=int, default=0, help="Optional maximum topic slugs allowed (0 disables).")
    ap.add_argument("--json", action="store_true", help="Emit JSON only (no extra text).")
    args = ap.parse_args()

    _ = _resolve_repo_root(args.repo_root)  # reserved for future path normalizations; no side effects.
    target = Path(args.path).expanduser()

    findings: list[dict] = []

    if target.is_file() and target.suffix.lower() == ".zip":
        with zipfile.ZipFile(str(target), "r") as z:
            roots = _find_output_roots_in_zip(z)
            for r in roots:
                findings.append(_validate_topics_in_zip(z, r))
        source_kind = "zip"
    else:
        roots = _find_output_roots_in_dir(target)
        for r in roots:
            findings.append(_validate_topics_in_dir(r))
        source_kind = "dir"

    # Evaluate verdict
    reasons: list[str] = []
    for f in findings:
        if not f.get("has_topics_dir", False):
            reasons.append(f"TOPICS_DIR_MISSING:{f.get('output_root')}")
        if int(f.get("empty_slug_topic_file_count", 0)) > 0:
            reasons.append(f"EMPTY_TOPIC_SLUG_FILES:{f.get('output_root')}")
        if int(f.get("invalid_slug_count", 0)) > 0:
            reasons.append(f"INVALID_SLUGS:{f.get('output_root')}")
        if str(args.mode) == "discovery":
            if int(f.get("topic_slug_count", 0)) < int(args.min_topic_slugs):
                reasons.append(f"DISCOVERY_MIN_TOPIC_SLUGS_FAIL:{f.get('output_root')}")
        if int(args.max_topic_slugs) > 0:
            if int(f.get("topic_slug_count", 0)) > int(args.max_topic_slugs):
                reasons.append(f"MAX_TOPIC_SLUGS_EXCEEDED:{f.get('output_root')}")

    verdict = "PASS" if len(reasons) == 0 else "REJECT"
    report = {
        "schema": "A2_TOPIC_OUTPUTS_VALIDATION_REPORT_v1",
        "input_path": str(target),
        "input_kind": source_kind,
        "mode": str(args.mode),
        "min_topic_slugs": int(args.min_topic_slugs),
        "max_topic_slugs": int(args.max_topic_slugs),
        "output_roots_found": len(findings),
        "verdict": verdict,
        "reasons": sorted(set(reasons)),
        "findings": findings,
    }

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

