#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.name == ".DS_Store":
            continue
        files.append(p)
    files.sort(key=lambda p: p.relative_to(root).as_posix())
    return files


def _layer_for_path(rel_path: str) -> tuple[str, str]:
    p = rel_path.lower()
    if p.startswith("core_docs/a1_refined_ratchet fuel/"):
        return ("A1_FUEL_RATCHET_FUEL", "READ_ONLY_SOURCE")
    if p.startswith("core_docs/a2_feed_high entropy doc/"):
        return ("A2_FUEL_HIGH_ENTROPY", "QUARANTINE_SOURCE")
    if p.startswith("core_docs/upgrade docs/"):
        return ("UPGRADE_DOCS", "READ_ONLY_SOURCE")
    if p.startswith("core_docs/a2_runtime_state archived old state/"):
        return ("A2_ARCHIVED_STATE", "READ_ONLY_SOURCE")
    if p.startswith("core_docs/"):
        return ("CORE_DOCS_OTHER", "READ_ONLY_SOURCE")
    return ("OTHER", "DERIVED_OR_WORKSPACE")


def build_doc_index(repo_root: Path, core_docs_dir: Path) -> dict:
    documents = []
    for p in _iter_files(core_docs_dir):
        rel = "core_docs/" + p.relative_to(core_docs_dir).as_posix()
        layer, canon_status = _layer_for_path(rel)
        documents.append(
            {
                "path": rel,
                "sha256": _sha256_file(p),
                "size_bytes": int(p.stat().st_size),
                "layer": layer,
                "canon_status": canon_status,
            }
        )
    documents.sort(key=lambda row: row["path"])
    return {
        "schema": "A2_DOC_INDEX_v1",
        "schema_version": 1,
        "generated_utc": _utc_iso(),
        "documents": documents,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--core-docs-dir", default="core_docs")
    ap.add_argument("--a2-state-dir", default="system_v3/a2_state")
    ap.add_argument("--backup-existing", action="store_true")
    args = ap.parse_args(argv)

    repo_root = Path.cwd().resolve()
    core_docs_dir = (repo_root / args.core_docs_dir).resolve()
    a2_state_dir = (repo_root / args.a2_state_dir).resolve()
    if not core_docs_dir.is_dir():
        raise SystemExit(f"missing core_docs dir: {core_docs_dir}")
    if not a2_state_dir.is_dir():
        raise SystemExit(f"missing a2_state dir: {a2_state_dir}")

    out_path = a2_state_dir / "doc_index.json"
    if args.backup_existing and out_path.exists():
        derived = repo_root / "system_v3" / "a2_derived_indices_noncanonical"
        derived.mkdir(parents=True, exist_ok=True)
        ts = _utc_iso().replace(":", "").replace("-", "")
        backup_path = derived / f"doc_index_backup__{ts}.json"
        backup_path.write_bytes(out_path.read_bytes())

    index = build_doc_index(repo_root, core_docs_dir)
    out_text = json.dumps(index, sort_keys=True, separators=(",", ":")) + "\n"
    out_path.write_text(out_text, encoding="utf-8")

    print(json.dumps({"schema": "A2_DOC_INDEX_REBUILD_RESULT_v1", "out": str(out_path), "doc_count": len(index["documents"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
