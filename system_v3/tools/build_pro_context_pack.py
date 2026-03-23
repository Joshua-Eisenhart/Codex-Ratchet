#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
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


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# Extract doc references like:
# - system_v3/specs/03_B_KERNEL_SPEC.md
# - core_docs/upgrade docs/BOOTPACK_THREAD_B_v3.9.13.md
# Hyphen must be escaped or placed at end of the character class.
DOC_REF_RE = re.compile(r"(?P<path>(?:system_v3|core_docs)/[A-Za-z0-9_ ./\\-]+\\.(?:md|json|txt))")


@dataclass(frozen=True)
class SelectedFile:
    relpath: str
    abspath: Path
    sha256: str
    bytes: int
    why: str


def _parse_spec_manifest_order(manifest_text: str) -> list[str]:
    # Parse lines like: 1. `system_v3/specs/01_REQUIREMENTS_LEDGER.md`
    paths: list[str] = []
    for line in manifest_text.splitlines():
        m = re.search(r"`(?P<p>system_v3/specs/[^`]+)`", line)
        if m:
            paths.append(m.group("p").strip())
    return paths


def _extract_doc_refs(text: str) -> set[str]:
    refs: set[str] = set()
    for m in DOC_REF_RE.finditer(text):
        p = m.group("path").strip()
        p = re.sub(r"\\s+", " ", p).strip()
        refs.add(p)
    return refs


def _safe_relpath(repo_root: Path, abspath: Path) -> str:
    return abspath.resolve().relative_to(repo_root.resolve()).as_posix()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build a lean Pro context pack (docs only) for thread extraction without guessing. Seeds from spec manifest + explicit doc references."
    )
    ap.add_argument("--repo-root", default="", help="Repo root (optional).")
    ap.add_argument("--out-dir", required=True, help="Output directory to create (will be overwritten if exists).")
    ap.add_argument("--max-mb", type=int, default=25, help="Soft size cap (MB) for included files (docs only).")
    ap.add_argument(
        "--include-upgrade-docs",
        action="store_true",
        help="Include core_docs/upgrade docs/{BOOTPACK_THREAD_A,BOOTPACK_THREAD_B,MEGABOOT_RATCHET_SUITE} if present.",
    )
    ap.add_argument(
        "--include-canon-lock-core",
        action="store_true",
        help="Include work/to_send_to_pro/tmp__PRO_THREAD_DELTA__v2/.../CANON_LOCK/CORE/* if present.",
    )
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve() if str(args.repo_root).strip() else _infer_repo_root(Path(__file__))
    out_dir = Path(args.out_dir).expanduser().resolve()

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    max_bytes = int(args.max_mb) * 1024 * 1024

    selections: list[SelectedFile] = []
    selected_paths: set[str] = set()

    def add_rel(rel: str, why: str) -> None:
        rel_norm = rel.strip().replace("\\\\", "/")
        if not rel_norm:
            return
        abs_path = (repo_root / rel_norm).resolve()
        if not abs_path.exists() or not abs_path.is_file():
            return
        relp = _safe_relpath(repo_root, abs_path)
        if relp in selected_paths:
            return
        sha = _sha256_file(abs_path)
        b = abs_path.stat().st_size
        selections.append(SelectedFile(relpath=relp, abspath=abs_path, sha256=sha, bytes=b, why=why))
        selected_paths.add(relp)

    # Seed 1: spec manifest + deterministic read order.
    spec_manifest_rel = "system_v3/specs/00_MANIFEST.md"
    spec_manifest = repo_root / spec_manifest_rel
    if spec_manifest.exists():
        add_rel(spec_manifest_rel, "seed:spec_manifest")
        manifest_text = spec_manifest.read_text(encoding="utf-8", errors="replace")
        for p in _parse_spec_manifest_order(manifest_text):
            add_rel(p, "seed:spec_manifest_read_order")

    # Seed 2: a few repo navigation docs if present.
    for p in [
        "system_v3/00_CANONICAL_ENTRYPOINTS_v1.md",
        "system_v3/01_OPERATIONS_RUNBOOK_v1.md",
        "system_v3/WORKSPACE_LAYOUT_v1.md",
        "system_v3/tools/chatgpt_pro_claw_playwright/README.md",
        "system_v3/specs/30_CHATUI_CLAW_PLAYWRIGHT_PROTOCOL_v1.md",
    ]:
        add_rel(p, "seed:ops_and_claw")

    # Seed 3: optional canon-lock core docs (already curated elsewhere in this repo).
    if args.include_canon_lock_core:
        canon_lock_dir = repo_root / "work/to_send_to_pro/tmp__PRO_THREAD_DELTA__v2/PRO_THREAD_DELTA__v2/CANON_LOCK/CORE"
        if canon_lock_dir.is_dir():
            for f in sorted(canon_lock_dir.glob("*.md"), key=lambda x: x.name.lower()):
                add_rel(_safe_relpath(repo_root, f), "seed:canon_lock_core")

    # Seed 4: optional upgrade docs (bootpacks + megaboot).
    if args.include_upgrade_docs:
        for p in [
            "core_docs/upgrade docs/BOOTPACK_THREAD_A_v2.60.md",
            "core_docs/upgrade docs/BOOTPACK_THREAD_B_v3.9.13.md",
            "core_docs/upgrade docs/MEGABOOT_RATCHET_SUITE_v7.4.9-PROJECTS 2.md",
        ]:
            add_rel(p, "seed:upgrade_docs")

    # Expand: follow explicit doc references inside selected markdowns (1 hop).
    md_files = [s for s in selections if s.abspath.suffix.lower() == ".md"]
    for s in md_files:
        txt = s.abspath.read_text(encoding="utf-8", errors="replace")
        for ref in sorted(_extract_doc_refs(txt)):
            add_rel(ref, f"ref_in:{s.relpath}")

    # Enforce size cap by trimming lowest-priority “ref_in:*” additions first.
    # Priority order: seed:* > ref_in:*
    def prio(why: str) -> int:
        if why.startswith("seed:"):
            return 0
        if why.startswith("ref_in:"):
            return 1
        return 2

    selections_sorted = sorted(selections, key=lambda s: (prio(s.why), -min(s.bytes, 10_000_000), s.relpath))
    kept: list[SelectedFile] = []
    total = 0
    for s in selections_sorted:
        if total + s.bytes > max_bytes and not s.why.startswith("seed:"):
            continue
        kept.append(s)
        total += s.bytes

    # Copy files into out_dir under the same relative paths.
    for s in kept:
        dst = out_dir / s.relpath
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(s.abspath), str(dst))

    inventory = {
        "schema": "PRO_CONTEXT_PACK_INVENTORY_v1",
        "repo_root": str(repo_root),
        "max_mb": int(args.max_mb),
        "kept_file_count": len(kept),
        "total_bytes": total,
        "files": [
            {"path": s.relpath, "sha256": s.sha256, "bytes": s.bytes, "why": s.why}
            for s in sorted(kept, key=lambda x: (prio(x.why), x.relpath))
        ],
    }
    # Use a real newline, not a literal backslash-n sequence.
    (out_dir / "CONTEXT_PACK_INVENTORY.json").write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    readme = [
        "# PRO_CONTEXT_PACK (auto-built; lean)",
        "",
        "This pack is built by `system_v3/tools/build_pro_context_pack.py`.",
        "It includes only documents selected via deterministic seeds + explicit in-doc references (1 hop).",
        "",
        "## Included inventory",
        "- See `CONTEXT_PACK_INVENTORY.json`.",
        "",
        "## Important",
        "- This pack does not decide canon/fuel. It only supplies documents for a Pro reading pass.",
        "",
    ]
    (out_dir / "00_READ_FIRST.md").write_text("\\n".join(readme) + "\\n", encoding="utf-8")

    print(json.dumps({"out_dir": str(out_dir), "kept_file_count": len(kept), "total_bytes": total}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
