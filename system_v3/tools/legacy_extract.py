#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
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
        [p for p in root.rglob("*.md") if p.is_file()],
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
    root = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet")
    legacy_roots = [
        root / "system_v2/specs/system_spec_pack_v2",
        root / "system_v2/work/system_specs",
    ]
    out_dir = root / "system_v3/specs/reports"
    out_dir.mkdir(parents=True, exist_ok=True)

    docs = []
    for lr in legacy_roots:
        for p in iter_legacy_files(lr):
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

    out_path = out_dir / "legacy_extract_report.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = {
        "doc_count": len(docs),
        "total_keyword_hits": sum(d["keyword_hit_count"] for d in docs),
        "total_role_hits": sum(d["role_hit_count"] for d in docs),
        "total_table_role_hits": sum(d["table_role_hit_count"] for d in docs),
        "report_path": str(out_path),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
