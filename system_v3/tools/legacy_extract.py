#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List


KEYWORD_RE = re.compile(
    r"\b(hard|must|forbidden|never|must not|do not|cannot|can't|required|mandatory|disallow|deny-by-default|append-only)\b",
    re.IGNORECASE,
)

ROLE_RE = re.compile(
    r"(\bA0\b|\bA1\b|\bA2\b|\bB\b|\bSIM\b|\bTHREAD_[A-Z0-9_]+\b|\bTHREAD_S_SAVE_SNAPSHOT\b|\bEXPORT_BLOCK\b|\bSIM_EVIDENCE\b)",
    re.IGNORECASE,
)

TABLE_ROLE_RE = re.compile(r"^\|\s*(A0|A1|A2|B|SIM)\s*\|", re.IGNORECASE)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def read_bytes(p: Path) -> bytes:
    return p.read_bytes()


def iter_legacy_files(root: Path) -> List[Path]:
    return sorted(
        [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".md", ".txt"}],
        key=lambda x: str(x).lower(),
    )


def extract_lines(text: str) -> Dict[str, List[Dict[str, str]]]:
    keyword_hits: List[Dict[str, str]] = []
    role_hits: List[Dict[str, str]] = []
    table_role_hits: List[Dict[str, str]] = []

    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\n")
        s = line.strip()
        if not s:
            continue

        if TABLE_ROLE_RE.search(s):
            table_role_hits.append({"line": i, "text": s})

        if KEYWORD_RE.search(s):
            keyword_hits.append({"line": i, "text": s})

        # role lines are noisier; keep only bullets/headings/table rows
        if ROLE_RE.search(s) and (s.startswith("#") or s.startswith("-") or s.startswith("|")):
            role_hits.append({"line": i, "text": s})

    return {
        "keyword_hits": keyword_hits,
        "role_hits": role_hits,
        "table_role_hits": table_role_hits,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Extract high-signal lines from legacy spec surfaces for migration.")
    parser.add_argument(
        "--repo-root",
        default="",
        help="Repository root. If omitted, uses $CODEX_RATCHET_ROOT, else infers from script path.",
    )
    parser.add_argument(
        "--legacy-root",
        action="append",
        default=[],
        help="Optional legacy source root(s) to scan recursively for .md/.txt files.",
    )
    parser.add_argument(
        "--source-file",
        action="append",
        default=[],
        help="Optional explicit legacy source file(s) to include.",
    )
    parser.add_argument(
        "--report-json",
        default="",
        help="Optional explicit output path for the extract report JSON.",
    )
    parser.add_argument(
        "--emit-fuel-digest-json",
        default="",
        help="If set, also emit FUEL_DIGEST_v1 from the scanned source files.",
    )
    parser.add_argument(
        "--max-fuel-claims-per-doc",
        type=int,
        default=24,
        help="Forwarded to build_fuel_digest.py when --emit-fuel-digest-json is set.",
    )
    args = parser.parse_args()

    raw = str(args.repo_root or "").strip()
    if raw:
        root = Path(raw).expanduser().resolve()
    else:
        env = str(os.environ.get("CODEX_RATCHET_ROOT", "") or "").strip()
        if env:
            root = Path(env).expanduser().resolve()
        else:
            cur = Path(__file__).resolve()
            root = cur
            for _ in range(10):
                if (root / "system_v3").is_dir():
                    break
                root = root.parent
            root = root.resolve()

    requested_roots = [Path(raw).expanduser().resolve() for raw in args.legacy_root if str(raw).strip()]
    legacy_roots = requested_roots or [
        root / "system_v2/specs/system_spec_pack_v2",
        root / "system_v2/work/system_specs",
    ]
    explicit_files = [Path(raw).expanduser().resolve() for raw in args.source_file if str(raw).strip()]
    out_dir = root / "system_v3/specs/reports"
    out_dir.mkdir(parents=True, exist_ok=True)

    docs = []
    seen_paths: set[Path] = set()
    for lr in legacy_roots:
        if not lr.exists():
            continue
        for p in iter_legacy_files(lr):
            if p in seen_paths:
                continue
            seen_paths.add(p)
            b = read_bytes(p)
            text = b.decode("utf-8", errors="ignore")
            extracted = extract_lines(text)
            docs.append(
                {
                    "path": str(p),
                    "sha256": sha256_bytes(b),
                    "size_bytes": len(b),
                    "keyword_hit_count": len(extracted["keyword_hits"]),
                    "role_hit_count": len(extracted["role_hits"]),
                    "table_role_hit_count": len(extracted["table_role_hits"]),
                    "keyword_hits": extracted["keyword_hits"][:200],
                    "role_hits": extracted["role_hits"][:200],
                    "table_role_hits": extracted["table_role_hits"][:200],
                    "truncated": {
                        "keyword_hits": len(extracted["keyword_hits"]) > 200,
                        "role_hits": len(extracted["role_hits"]) > 200,
                        "table_role_hits": len(extracted["table_role_hits"]) > 200,
                    },
                }
            )
    for p in explicit_files:
        if not p.is_file() or p in seen_paths:
            continue
        seen_paths.add(p)
        b = read_bytes(p)
        text = b.decode("utf-8", errors="ignore")
        extracted = extract_lines(text)
        docs.append(
            {
                "path": str(p),
                "sha256": sha256_bytes(b),
                "size_bytes": len(b),
                "keyword_hit_count": len(extracted["keyword_hits"]),
                "role_hit_count": len(extracted["role_hits"]),
                "table_role_hit_count": len(extracted["table_role_hits"]),
                "keyword_hits": extracted["keyword_hits"][:200],
                "role_hits": extracted["role_hits"][:200],
                "table_role_hits": extracted["table_role_hits"][:200],
                "truncated": {
                    "keyword_hits": len(extracted["keyword_hits"]) > 200,
                    "role_hits": len(extracted["role_hits"]) > 200,
                    "table_role_hits": len(extracted["table_role_hits"]) > 200,
                },
            }
        )

    report = {
        "sources": [str(p) for p in legacy_roots],
        "doc_count": len(docs),
        "docs": docs,
    }

    out_path = Path(args.report_json).expanduser().resolve() if str(args.report_json).strip() else out_dir / "legacy_extract_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = {
        "doc_count": len(docs),
        "total_keyword_hits": sum(d["keyword_hit_count"] for d in docs),
        "total_role_hits": sum(d["role_hit_count"] for d in docs),
        "total_table_role_hits": sum(d["table_role_hit_count"] for d in docs),
        "report_path": str(out_path),
    }
    if str(args.emit_fuel_digest_json).strip():
        fuel_digest_path = Path(args.emit_fuel_digest_json).expanduser().resolve()
        fuel_digest_path.parent.mkdir(parents=True, exist_ok=True)
        build_cmd = [
            "python3",
            str(root / "system_v3/tools/build_fuel_digest.py"),
            "--out-json",
            str(fuel_digest_path),
            "--max-claims-per-doc",
            str(int(args.max_fuel_claims_per_doc)),
        ]
        for path in sorted(str(p) for p in seen_paths):
            build_cmd.extend(["--source-file", path])
        subprocess.run(build_cmd, check=True)
        summary["fuel_digest_path"] = str(fuel_digest_path)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
