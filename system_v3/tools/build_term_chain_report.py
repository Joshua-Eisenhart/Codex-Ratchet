#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


BOOTPACK_ROOT = _repo_root() / "system_v3" / "runtime" / "bootpack_b_kernel_v1"
if str(BOOTPACK_ROOT) not in sys.path:
    sys.path.insert(0, str(BOOTPACK_ROOT))

from state import DERIVED_ONLY_TERMS, L0_LEXEME_SET  # noqa: E402


TERM_SPLIT_RE = re.compile(r"[_\-\s]+")


def _normalize(literal: str) -> str:
    token = str(literal).strip().lower().replace("-", "_").replace(" ", "_")
    while "__" in token:
        token = token.replace("__", "_")
    return token.strip("_")


def _load_state(state_json: Path | None) -> tuple[str, dict, set[str], set[str]]:
    if state_json is None:
        return "provided text", {}, set(L0_LEXEME_SET), set(DERIVED_ONLY_TERMS)
    payload = json.loads(state_json.read_text(encoding="utf-8"))
    term_registry = payload.get("term_registry", {}) if isinstance(payload.get("term_registry"), dict) else {}
    l0 = set(payload.get("l0_lexeme_set", []) or []) or set(L0_LEXEME_SET)
    derived = set(payload.get("derived_only_terms", []) or []) or set(DERIVED_ONLY_TERMS)
    return str(state_json), term_registry, l0, derived


def main() -> int:
    parser = argparse.ArgumentParser(description="Build TERM_CHAIN_REPORT_v1.")
    parser.add_argument("--term", action="append", default=[])
    parser.add_argument("--terms-file", default="")
    parser.add_argument("--state-json", default="")
    parser.add_argument("--out-json", default="")
    args = parser.parse_args()

    terms = [str(x).strip() for x in args.term if str(x).strip()]
    if str(args.terms_file).strip():
        terms_path = Path(args.terms_file).resolve()
        for line in terms_path.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if text:
                terms.append(text)
    terms = sorted(set(terms))
    if not terms:
        raise SystemExit("must provide at least one --term or --terms-file")

    state_json = Path(args.state_json).resolve() if str(args.state_json).strip() else None
    source_pointer, term_registry, l0_lexemes, derived_only = _load_state(state_json)

    rows: list[dict] = []
    unknown_segment_total = 0
    for literal in terms:
        normalized = _normalize(literal)
        segments = [segment for segment in TERM_SPLIT_RE.split(normalized) if segment]
        segment_rows: list[dict] = []
        unknown_segments: list[str] = []
        for segment in segments:
            entry = term_registry.get(segment, {}) if isinstance(term_registry, dict) else {}
            state_value = str(entry.get("state", "")).strip()
            if state_value:
                status = state_value
            elif segment in l0_lexemes:
                status = "L0_LEXEME"
            elif segment in derived_only:
                status = "DERIVED_ONLY"
            else:
                status = "UNKNOWN"
                unknown_segments.append(segment)
            segment_rows.append({"segment": segment, "status": status})
        unknown_segment_total += len(unknown_segments)
        rows.append(
            {
                "literal": literal,
                "normalized_literal": normalized,
                "segments": segment_rows,
                "segment_count": len(segment_rows),
                "unknown_segments": unknown_segments,
                "source_pointer": source_pointer,
            }
        )

    report = {
        "schema": "TERM_CHAIN_REPORT_v1",
        "status": "PASS",
        "source_pointer": source_pointer,
        "term_count": len(rows),
        "unknown_segment_total": unknown_segment_total,
        "rows": rows,
    }
    out_path = Path(args.out_json).resolve() if str(args.out_json).strip() else None
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
