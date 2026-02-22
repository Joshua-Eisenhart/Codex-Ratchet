#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


def normalize(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"`[^`]*`", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s


def tokens(s: str) -> List[str]:
    s = normalize(s)
    s = re.sub(r"[^a-z0-9_ ]+", " ", s)
    stop = {
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "from",
        "are",
        "not",
        "only",
        "must",
        "can",
        "all",
        "into",
        "its",
        "was",
        "use",
        "using",
        "when",
        "where",
        "what",
        "how",
    }
    return [t for t in s.split() if len(t) > 2 and t not in stop]


def cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    inter = set(a) & set(b)
    num = sum(a[k] * b[k] for k in inter)
    da = math.sqrt(sum(v * v for v in a.values()))
    db = math.sqrt(sum(v * v for v in b.values()))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


def split_paragraphs(text: str) -> List[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return [p for p in paras if not p.startswith("#")]


def main() -> int:
    root = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet")
    spec_dir = root / "system_v3/specs"
    reports_dir = spec_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / "content_redundancy_report.json"

    files = sorted([p for p in spec_dir.glob("*.md") if p.name[0:2].isdigit()])
    texts = {p.name: p.read_text(encoding="utf-8", errors="ignore") for p in files}

    # Duplicate headings
    heading_map: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
    for name, text in texts.items():
        for i, line in enumerate(text.splitlines(), 1):
            if line.startswith("#"):
                key = normalize(line.lstrip("# "))
                heading_map[key].append((name, i))
    duplicate_headings = []
    for h, locs in sorted(heading_map.items()):
        docs = sorted({d for d, _ in locs})
        if len(docs) > 1:
            duplicate_headings.append(
                {"heading": h, "locations": [{"file": d, "line": ln} for d, ln in locs]}
            )

    # Paragraph near-duplicates
    para_rows = []
    for name, text in texts.items():
        for idx, para in enumerate(split_paragraphs(text), 1):
            nt = tokens(para)
            if len(nt) < 8:
                continue
            para_rows.append((name, idx, para, Counter(nt)))

    near_duplicate_blocks = []
    for i in range(len(para_rows)):
        a_name, a_idx, a_para, a_vec = para_rows[i]
        for j in range(i + 1, len(para_rows)):
            b_name, b_idx, b_para, b_vec = para_rows[j]
            if a_name == b_name:
                continue
            sim = cosine(a_vec, b_vec)
            if sim >= 0.85:
                near_duplicate_blocks.append(
                    {
                        "similarity": round(sim, 4),
                        "a": {"file": a_name, "paragraph": a_idx},
                        "b": {"file": b_name, "paragraph": b_idx},
                    }
                )

    # Cross-owner overlap
    doc_vec = {name: Counter(tokens(text)) for name, text in texts.items()}
    cross_owner_overlap = []
    names = sorted(doc_vec)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            sim = cosine(doc_vec[a], doc_vec[b])
            if sim >= 0.70:
                cross_owner_overlap.append(
                    {"similarity": round(sim, 4), "a": a, "b": b}
                )

    # Recommended compactions from largest overlaps
    recommended_compactions = []
    for row in sorted(cross_owner_overlap, key=lambda x: x["similarity"], reverse=True)[:10]:
        recommended_compactions.append(
            {
                "a": row["a"],
                "b": row["b"],
                "reason": "high semantic overlap",
                "similarity": row["similarity"],
            }
        )

    report = {
        "duplicate_headings": duplicate_headings,
        "near_duplicate_blocks": sorted(
            near_duplicate_blocks, key=lambda x: x["similarity"], reverse=True
        ),
        "cross_owner_overlap": sorted(
            cross_owner_overlap, key=lambda x: x["similarity"], reverse=True
        ),
        "recommended_compactions": recommended_compactions,
        "thresholds": {
            "near_duplicate_block_cosine": 0.85,
            "cross_owner_overlap_cosine": 0.70,
        },
    }

    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "duplicate_headings": len(duplicate_headings),
        "near_duplicate_blocks": len(near_duplicate_blocks),
        "cross_owner_overlap": len(cross_owner_overlap),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
