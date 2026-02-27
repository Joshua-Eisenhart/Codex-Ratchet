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


def _first_header_line(path: Path) -> str:
    # Deterministic best-effort: first non-empty line for small text-like files.
    if path.suffix.lower() in {".md", ".txt", ".py", ".json"}:
        try:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                text = line.strip("\ufeff").rstrip("\n")
                if text.strip():
                    return text
        except Exception:
            return ""
    return ""


def _doc_type_guess(rel_path: str) -> str:
    p = rel_path.lower()
    if "a1_refined_ratchet fuel/constraint ladder/" in p:
        return "a1_constraint_ladder_doc"
    if "a1_refined_ratchet fuel/sims/simpy/" in p and p.endswith(".py"):
        return "a1_sim_script"
    if "a1_refined_ratchet fuel/sims/simson/" in p and p.endswith(".json"):
        return "a1_sim_result_json"
    if "a1_refined_ratchet fuel/sims/" in p:
        return "a1_sim_support_doc"
    if "a1_refined_ratchet fuel/" in p:
        return "a1_ratchet_fuel_doc"
    if "a2_feed_high entropy doc/" in p:
        return "a2_high_entropy_doc"
    if "a2_runtime_state archived old state/" in p:
        return "a2_archived_state_doc"
    if "upgrade docs/" in p:
        return "upgrade_doc"
    return "core_doc"


def _doc_id_for_path(rel_path: str) -> str:
    return "DOC_" + hashlib.sha256(rel_path.encode("utf-8")).hexdigest()[:12].upper()


def _iter_core_docs(core_docs_dir: Path) -> list[Path]:
    files: list[Path] = []
    for p in core_docs_dir.rglob("*"):
        if not p.is_file():
            continue
        if p.name == ".DS_Store":
            continue
        files.append(p)
    files.sort(key=lambda p: p.relative_to(core_docs_dir).as_posix())
    return files


def build_index(core_docs_dir: Path) -> dict:
    docs = []
    for p in _iter_core_docs(core_docs_dir):
        rel = p.relative_to(core_docs_dir).as_posix()
        full_rel = f"core_docs/{rel}"
        docs.append(
            {
                "path": full_rel,
                "doc_id": _doc_id_for_path(full_rel),
                "doc_type_guess": _doc_type_guess(full_rel),
                "first_header_line": _first_header_line(p),
                "byte_size": int(p.stat().st_size),
                "sha256": _sha256_file(p),
            }
        )
    return {
        "schema": "DOC_INDEX_v1",
        "generated_utc": _utc_iso(),
        "doc_count": len(docs),
        "docs": docs,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--core-docs-dir", default="core_docs")
    ap.add_argument("--out", default="system_v3/a2_state/ingest/index_v1.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    repo_root = Path.cwd().resolve()
    core_docs_dir = (repo_root / args.core_docs_dir).resolve()
    out_path = (repo_root / args.out).resolve()

    if not core_docs_dir.is_dir():
        raise SystemExit(f"missing core_docs dir: {core_docs_dir}")

    index = build_index(core_docs_dir)
    out_text = json.dumps(index, sort_keys=True, separators=(",", ":")) + "\n"
    out_sha = hashlib.sha256(out_text.encode("utf-8")).hexdigest()

    if args.dry_run:
        print(json.dumps({"schema": "DOC_INDEX_REINDEX_DRY_RUN_v1", "doc_count": index["doc_count"], "out_sha256": out_sha}, sort_keys=True))
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out_text, encoding="utf-8")
    sha_path = out_path.with_suffix(".sha256")
    sha_path.write_text(f"{out_sha}  {out_path.name}\n", encoding="utf-8")

    print(json.dumps({"schema": "DOC_INDEX_REINDEX_RESULT_v1", "out": str(out_path), "doc_count": index["doc_count"], "sha256": out_sha}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
