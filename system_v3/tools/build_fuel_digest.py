#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path


DIRECT_TERM_RE = re.compile(r"\b(?:A0|A1|A2|SIM)\b")
VERSIONED_ID_RE = re.compile(r"\b([A-Z][A-Z0-9]+(?:_[A-Z0-9]+)*)(?:\s+v(\d+(?:\.\d+)?))\b")
BARE_STRUCTURED_ID_RE = re.compile(r"\b([A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+)\b")
THREAD_PHRASE_RE = re.compile(r"\bThread\s+([ABMS]|SIM)\b", re.IGNORECASE)
KEYWORD_RE = re.compile(
    r"\b(must|forbidden|never|must not|do not|cannot|can't|required|mandatory|disallow|deny-by-default|append-only)\b",
    re.IGNORECASE,
)
STRUCTURED_STOPWORDS = {
    "AUTHORITY",
    "BEGIN",
    "END",
    "HARD",
    "INPUT",
    "INPUTS",
    "INTENT",
    "OPTIONAL",
    "OUTPUT",
    "OUTPUTS",
    "PASS",
    "PURPOSE",
    "REFUSAL",
    "RESULT",
    "ROLE",
    "RULES",
    "STYLE",
    "UNKNOWN",
}
USEFUL_STRUCTURED_PREFIXES = (
    "AUDIT_",
    "BOOTPACK_",
    "CAMPAIGN_",
    "EXPORT_",
    "FUEL_",
    "OVERLAY_",
    "PROJECT_",
    "ROSETTA_",
    "SIM_",
    "TAPE_",
    "THREAD_",
)


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _compact_ts() -> str:
    return time.strftime("%Y%m%d_%H%M%SZ", time.gmtime())


def _candidate_type(token: str) -> str:
    if token in {"A0", "A1", "A2", "SIM"}:
        return "TERM"
    return "SPEC_ID"


def _normalize_term(token: str) -> str:
    return str(token).strip().lower().replace("-", "_").replace(" ", "_")


def _canonical_structured_id(base: str, version: str | None = None) -> str:
    base = str(base).strip().upper()
    if version:
        return f"{base}_v{str(version).strip()}"
    return base


def _looks_like_structured_id(token: str) -> bool:
    token = str(token).strip().upper()
    if not token or token in STRUCTURED_STOPWORDS:
        return False
    if token.startswith("THREAD_") or token.startswith("BOOTPACK_"):
        return True
    return any(token.startswith(prefix) for prefix in USEFUL_STRUCTURED_PREFIXES)


def _looks_like_heading(line: str) -> bool:
    stripped = str(line).strip()
    if not stripped or len(stripped.split()) > 5:
        return False
    letters = [ch for ch in stripped if ch.isalpha()]
    if not letters:
        return False
    upper_letters = [ch for ch in letters if ch.isupper()]
    return len(upper_letters) == len(letters)


def _extract_structured_tokens(line: str) -> list[str]:
    tokens: list[str] = []
    for base, version in VERSIONED_ID_RE.findall(line):
        candidate = _canonical_structured_id(base, version)
        if _looks_like_structured_id(candidate):
            tokens.append(candidate)
    for token in BARE_STRUCTURED_ID_RE.findall(line):
        candidate = _canonical_structured_id(token)
        if _looks_like_structured_id(candidate):
            tokens.append(candidate)
    for match in THREAD_PHRASE_RE.findall(line):
        candidate = _canonical_structured_id(f"THREAD_{str(match).upper()}")
        if _looks_like_structured_id(candidate):
            tokens.append(candidate)
    for token in DIRECT_TERM_RE.findall(line):
        tokens.append(token)
    ordered: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        ordered.append(token)
    return ordered


def _extract_claim_text(line: str) -> str:
    text = str(line).strip()
    if _looks_like_heading(text):
        return ""
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FUEL_DIGEST_v1 from a legacy extract report.")
    parser.add_argument("--legacy-report", default="")
    parser.add_argument("--source-file", action="append", default=[])
    parser.add_argument("--out-json", default="")
    parser.add_argument("--max-claims-per-doc", type=int, default=24)
    args = parser.parse_args()

    docs: list[dict] = []
    source_pointers: list[str] = []
    if str(args.legacy_report).strip():
        report_path = Path(args.legacy_report).resolve()
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        docs.extend(payload.get("docs", []) if isinstance(payload.get("docs"), list) else [])
        source_pointers.append(str(report_path))
    for raw_path in sorted(set(args.source_file)):
        path = Path(raw_path).resolve()
        keyword_hits = []
        role_hits = []
        for index, raw_line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            claim_text = _extract_claim_text(line)
            if claim_text and KEYWORD_RE.search(claim_text):
                keyword_hits.append({"line": index, "text": claim_text})
            structured_tokens = _extract_structured_tokens(line)
            if structured_tokens:
                role_hits.append({"line": index, "text": line, "tokens": structured_tokens})
        docs.append({"path": str(path), "keyword_hits": keyword_hits, "role_hits": role_hits})
        source_pointers.append(str(path))
    if not docs:
        raise SystemExit("must provide --legacy-report and/or at least one --source-file")

    extracted_claims: list[dict] = []
    kernel_candidate_suggestions: list[dict] = []
    overlay_mapping_suggestions: list[dict] = []

    claim_counter = 0
    candidate_counter = 0
    mapping_counter = 0
    for doc in sorted(docs, key=lambda row: str(row.get("path", ""))):
        path = str(doc.get("path", "")).strip()
        keyword_hits = doc.get("keyword_hits", []) if isinstance(doc.get("keyword_hits"), list) else []
        role_hits = doc.get("role_hits", []) if isinstance(doc.get("role_hits"), list) else []
        for row in keyword_hits[: int(args.max_claims_per_doc)]:
            if not isinstance(row, dict):
                continue
            claim_counter += 1
            extracted_claims.append(
                {
                    "claim_id": f"FC_{claim_counter:05d}",
                    "text": str(row.get("text", "")).strip(),
                    "source_pointer": f"{path}#L{int(row.get('line', 0) or 0)}",
                }
            )
        seen_doc_tokens: set[tuple[str, str]] = set()
        for row in role_hits:
            if not isinstance(row, dict):
                continue
            text = str(row.get("text", "")).strip()
            source_pointer = f"{path}#L{int(row.get('line', 0) or 0)}"
            explicit_tokens = row.get("tokens", []) if isinstance(row.get("tokens"), list) else []
            for token in sorted(set(str(tok).strip() for tok in explicit_tokens if str(tok).strip())):
                key = (source_pointer, token)
                if key in seen_doc_tokens:
                    continue
                seen_doc_tokens.add(key)
                candidate_counter += 1
                kernel_candidate_suggestions.append(
                    {
                        "candidate_id": f"KC_{candidate_counter:05d}",
                        "kernel_candidate": token if _candidate_type(token) == "SPEC_ID" else _normalize_term(token),
                        "candidate_type": _candidate_type(token),
                        "source_pointer": source_pointer,
                    }
                )
                mapping_counter += 1
                overlay_mapping_suggestions.append(
                    {
                        "mapping_id": f"OM_{mapping_counter:05d}",
                        "source_term": _normalize_term(token),
                        "kernel_anchor_candidate": token if _candidate_type(token) == "SPEC_ID" else _normalize_term(token),
                        "anchor_type": _candidate_type(token),
                        "source_pointer": source_pointer,
                    }
                )

    digest = {
        "schema": "FUEL_DIGEST_v1",
        "digest_id": f"FUEL_DIGEST__{_compact_ts()}",
        "created_utc": _utc_now(),
        "source_list": sorted(str(row.get("path", "")).strip() for row in docs if str(row.get("path", "")).strip()),
        "extracted_claims": extracted_claims,
        "kernel_candidate_suggestions": kernel_candidate_suggestions,
        "overlay_mapping_suggestions": overlay_mapping_suggestions,
        "source_pointers": sorted(set(source_pointers)),
    }
    out_path = Path(args.out_json).resolve() if str(args.out_json).strip() else None
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(digest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(digest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
