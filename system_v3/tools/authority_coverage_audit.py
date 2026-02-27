#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple


ROOT = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet")

NORMATIVE_RE = re.compile(
    r"(?i)\b("
    r"HARD|MUST\s+NOT|MUST|FORBIDDEN|NEVER|DO\s+NOT|CANNOT|CAN'T|REQUIRED|MANDATORY|DENY[- ]BY[- ]DEFAULT|APPEND[- ]ONLY"
    r")\b"
)

WORD_RE = re.compile(r"[A-Za-z0-9_+]{2,}")

STOP_TOKENS = {
    "HARD",
    "MUST",
    "MUSTNOT",
    "NOT",
    "FORBIDDEN",
    "NEVER",
    "DO",
    "CANNOT",
    "CANT",
    "REQUIRED",
    "MANDATORY",
    "DENY",
    "BY",
    "DEFAULT",
    "APPEND",
    "ONLY",
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def iter_authority_sources() -> List[Path]:
    sources: List[Path] = []
    # core_docs was reorganized; keep authority sources in the new canonical locations.
    sources.append(ROOT / "core_docs/upgrade docs/MEGABOOT_RATCHET_SUITE_v7.4.9-PROJECTS 2.md")
    upgrade_dir = ROOT / "core_docs/upgrade docs"
    if upgrade_dir.exists():
        sources.extend(sorted(upgrade_dir.glob("*.md"), key=lambda p: str(p).lower()))
    return [p for p in sources if p.exists() and p.is_file()]


def iter_v3_spec_docs() -> List[Path]:
    spec_dir = ROOT / "system_v3/specs"
    return sorted([p for p in spec_dir.glob("*.md") if p.is_file()], key=lambda p: str(p).lower())


def normalize_token(tok: str) -> str:
    return tok.strip().strip("_")


def extract_tokens(line: str) -> List[str]:
    out: List[str] = []
    for raw in WORD_RE.findall(line):
        tok = normalize_token(raw)
        if not tok:
            continue
        t = tok.upper()
        if t in STOP_TOKENS:
            continue
        keep = False
        # High-signal tokens: IDs, constants, or explicitly whitelisted short forms.
        if "+" in tok or "_" in tok or any(ch.isdigit() for ch in tok):
            keep = True
        elif t in {"MIN", "ZIP", "ASCII", "LF"}:
            keep = True
        if keep:
            out.append(tok)
    # deterministic unique preserving order
    seen: Set[str] = set()
    uniq: List[str] = []
    for t in out:
        if t in seen:
            continue
        seen.add(t)
        uniq.append(t)
    return uniq


@dataclass(frozen=True)
class NormLine:
    path: str
    line: int
    text: str
    tokens: Tuple[str, ...]


def extract_normative_lines(p: Path) -> List[NormLine]:
    text = read_text(p)
    out: List[NormLine] = []
    for i, raw in enumerate(text.splitlines(), 1):
        s = raw.rstrip("\n")
        if not s.strip():
            continue
        if NORMATIVE_RE.search(s):
            toks = tuple(extract_tokens(s))
            out.append(NormLine(path=str(p), line=i, text=s.strip(), tokens=toks))
    return out


def token_search_re(tok: str) -> re.Pattern[str]:
    # Avoid \b because tokens can include '+'; treat word chars as [A-Za-z0-9_].
    return re.compile(r"(?i)(?<![A-Za-z0-9_])" + re.escape(tok) + r"(?![A-Za-z0-9_])")


def build_authority_token_hits(tokens: List[str], v3_docs: List[Path]) -> Dict[str, List[str]]:
    compiled = [(t, token_search_re(t)) for t in tokens]
    hits: Dict[str, Set[str]] = {t: set() for t in tokens}
    for p in v3_docs:
        text = read_text(p)
        for t, cre in compiled:
            if cre.search(text):
                hits[t].add(str(p))
    return {t: sorted(list(ds), key=lambda x: x.lower()) for t, ds in sorted(hits.items()) if ds}


def main() -> int:
    out_dir = ROOT / "system_v3/specs/reports"
    out_dir.mkdir(parents=True, exist_ok=True)

    authority_sources = iter_authority_sources()
    v3_docs = iter_v3_spec_docs()

    norm_lines: List[NormLine] = []
    token_counts: Dict[str, int] = {}

    sources_meta = []
    for p in authority_sources:
        b = p.read_bytes()
        sources_meta.append({"path": str(p), "sha256": sha256_bytes(b), "size_bytes": len(b)})
        for nl in extract_normative_lines(p):
            norm_lines.append(nl)
            for t in nl.tokens:
                token_counts[t] = token_counts.get(t, 0) + 1

    # deterministic
    norm_lines = sorted(norm_lines, key=lambda x: (x.path.lower(), x.line))
    authority_tokens = sorted(token_counts.keys(), key=lambda x: x.lower())
    v3_token_hits = build_authority_token_hits(authority_tokens, v3_docs)
    covered: Set[str] = set(v3_token_hits.keys())
    missing_tokens = sorted([t for t in authority_tokens if t not in covered], key=lambda x: x.lower())

    gap_lines = []
    for nl in norm_lines:
        missing = [t for t in nl.tokens if t in missing_tokens]
        if missing:
            gap_lines.append(
                {
                    "path": nl.path,
                    "line": nl.line,
                    "text": nl.text,
                    "missing_tokens": missing,
                }
            )

    extract_report = {
        "authority_sources": sources_meta,
        "normative_line_count": len(norm_lines),
        "normative_lines": [
            {"path": nl.path, "line": nl.line, "text": nl.text, "tokens": list(nl.tokens)} for nl in norm_lines
        ],
        "token_counts": {k: token_counts[k] for k in sorted(token_counts.keys(), key=lambda x: x.lower())},
        "v3_token_hits": v3_token_hits,
        "v3_scanned_docs": [str(p) for p in v3_docs],
    }

    gap_report = {
        "authority_sources": [m["path"] for m in sources_meta],
        "v3_scanned_docs": [str(p) for p in v3_docs],
        "missing_tokens": missing_tokens,
        "gap_line_count": len(gap_lines),
        "gap_lines": gap_lines[:500],
        "truncated": len(gap_lines) > 500,
    }

    out_extract = out_dir / "authority_extract_report.json"
    out_gap = out_dir / "authority_gap_report.json"
    out_extract.write_text(json.dumps(extract_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_gap.write_text(json.dumps(gap_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = {
        "authority_sources": len(authority_sources),
        "v3_docs": len(v3_docs),
        "normative_lines": len(norm_lines),
        "unique_tokens_in_normative_lines": len(token_counts),
        "missing_tokens": len(missing_tokens),
        "gap_lines": len(gap_lines),
        "reports": {"extract": str(out_extract), "gaps": str(out_gap)},
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
