#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path


VERSION_SUFFIX_RE = re.compile(r"_v\d+(?:\.\d+)?$", re.IGNORECASE)
VERSIONED_ID_RE = re.compile(r"\b([A-Z][A-Z0-9]+(?:_[A-Z0-9]+)*)(?:\s+v(\d+(?:\.\d+)?))\b")
BARE_STRUCTURED_ID_RE = re.compile(r"\b([A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+)\b")
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


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _compact_ts() -> str:
    return time.strftime("%Y%m%d_%H%M%SZ", time.gmtime())


def _norm(text: str) -> str:
    value = str(text).strip().lower().replace("-", "_").replace(" ", "_")
    value = VERSION_SUFFIX_RE.sub("", value)
    return value.strip("_")


def _canonical_structured_id(base: str, version: str | None = None) -> str:
    base = str(base).strip().upper()
    if version:
        return f"{base}_v{str(version).strip()}"
    return base


def _looks_like_structured_id(token: str) -> bool:
    token = str(token).strip().upper()
    if not token or token in STRUCTURED_STOPWORDS:
        return False
    return "_" in token or token.startswith("BOOTPACK_")


def _extract_repo_structured_ids(text: str) -> set[str]:
    tokens: set[str] = set()
    for base, version in VERSIONED_ID_RE.findall(text):
        candidate = _canonical_structured_id(base, version)
        if _looks_like_structured_id(candidate):
            tokens.add(candidate)
    for token in BARE_STRUCTURED_ID_RE.findall(text):
        candidate = _canonical_structured_id(token)
        if _looks_like_structured_id(candidate):
            tokens.add(candidate)
    return tokens


def _register_anchor(anchor_map: dict[str, str], token: str) -> None:
    token = str(token).strip()
    if not token:
        return
    canonical = token
    normalized = _norm(canonical)
    if not normalized:
        return
    anchor_map.setdefault(normalized, canonical)
    if canonical.lower().endswith(".md"):
        anchor_map.setdefault(_norm(Path(canonical).stem), canonical)
    if "_v" in canonical.lower():
        anchor_map.setdefault(_norm(VERSION_SUFFIX_RE.sub("", canonical)), canonical)


def _load_state(path: Path | None) -> tuple[dict[str, str], dict[str, str]]:
    if path is None:
        return {}, {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    heavy_path = path.with_name("state.heavy.json")
    if heavy_path.exists():
        heavy_payload = json.loads(heavy_path.read_text(encoding="utf-8"))
        if isinstance(heavy_payload.get("spec_meta"), dict):
            payload["spec_meta"] = heavy_payload.get("spec_meta")
    term_registry = payload.get("term_registry", {}) if isinstance(payload.get("term_registry"), dict) else {}
    spec_meta = payload.get("spec_meta", {}) if isinstance(payload.get("spec_meta"), dict) else {}
    known_terms: dict[str, str] = {}
    known_specs: dict[str, str] = {}
    for key in term_registry.keys():
        _register_anchor(known_terms, str(key))
    for key in spec_meta.keys():
        _register_anchor(known_specs, str(key))
    return known_terms, known_specs


def _load_repo_anchors(repo_root: Path) -> dict[str, str]:
    known_specs: dict[str, str] = {}
    schema_dir = repo_root / "system_v3" / "specs" / "schemas"
    if schema_dir.exists():
        for path in sorted(schema_dir.glob("*.json")):
            _register_anchor(known_specs, path.stem)
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            title = str(payload.get("title", "")).strip()
            if title:
                _register_anchor(known_specs, title)
    spec_dir = repo_root / "system_v3" / "specs"
    if spec_dir.exists():
        for path in sorted(spec_dir.glob("*.md")):
            _register_anchor(known_specs, path.stem)
            try:
                tokens = _extract_repo_structured_ids(path.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
            for token in tokens:
                _register_anchor(known_specs, token)
    return known_specs


def _resolve_anchor(
    source_term: str,
    kernel_candidate: str,
    declared_anchor_type: str,
    known_terms: dict[str, str],
    known_specs: dict[str, str],
) -> tuple[str, str, str, str]:
    ordered_candidates = [kernel_candidate, source_term]
    if declared_anchor_type == "TERM":
        for candidate in ordered_candidates:
            normalized = _norm(candidate)
            if normalized in known_terms:
                return known_terms[normalized], "TERM", "BOUND", ""
        for candidate in ordered_candidates:
            normalized = _norm(candidate)
            if normalized in known_specs:
                return known_specs[normalized], "SPEC_ID", "BOUND", ""
    else:
        for candidate in ordered_candidates:
            normalized = _norm(candidate)
            if normalized in known_specs:
                return known_specs[normalized], "SPEC_ID", "BOUND", ""
        for candidate in ordered_candidates:
            normalized = _norm(candidate)
            if normalized in known_terms:
                return known_terms[normalized], "TERM", "BOUND", ""
    return "", declared_anchor_type, "UNKNOWN", kernel_candidate


def main() -> int:
    parser = argparse.ArgumentParser(description="Build ROSETTA_MAP_v1 from one or more fuel digests.")
    parser.add_argument("--fuel-digest-json", action="append", required=True)
    parser.add_argument("--state-json", default="")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out-json", default="")
    args = parser.parse_args()

    state_json = Path(args.state_json).resolve() if str(args.state_json).strip() else None
    repo_root = Path(args.repo_root).resolve()
    known_terms, state_specs = _load_state(state_json)
    known_specs = _load_repo_anchors(repo_root)
    known_specs.update(state_specs)
    merged_entries: dict[tuple[str, str, str, str], dict] = {}
    source_pointers: list[str] = []

    for raw_path in sorted(set(args.fuel_digest_json)):
        path = Path(raw_path).resolve()
        source_pointers.append(str(path))
        payload = json.loads(path.read_text(encoding="utf-8"))
        suggestions = payload.get("overlay_mapping_suggestions", []) if isinstance(payload.get("overlay_mapping_suggestions"), list) else []
        for row in suggestions:
            if not isinstance(row, dict):
                continue
            source_term = str(row.get("source_term", "")).strip()
            kernel_anchor = str(row.get("kernel_anchor_candidate", "")).strip()
            anchor_type = str(row.get("anchor_type", "")).strip() or "TERM"
            resolved_anchor, resolved_type, status, fallback_candidate = _resolve_anchor(
                source_term,
                kernel_anchor,
                anchor_type,
                known_terms,
                known_specs,
            )
            key = (
                source_term,
                resolved_type,
                resolved_anchor if status == "BOUND" else fallback_candidate,
                status,
            )
            pointer = str(row.get("source_pointer", "")).strip()
            entry = merged_entries.get(key)
            if entry is None:
                entry = {
                    "source_term": source_term,
                    "kernel_anchor": resolved_anchor if status == "BOUND" else "",
                    "anchor_type": resolved_type,
                    "status": status,
                    "kernel_candidate": "" if status == "BOUND" else fallback_candidate,
                    "source_pointers": [],
                }
                merged_entries[key] = entry
            if pointer and pointer not in entry["source_pointers"]:
                entry["source_pointers"].append(pointer)

    entries: list[dict] = []
    for index, key in enumerate(
        sorted(
            merged_entries.keys(),
            key=lambda row: (
                row[0],
                row[1],
                row[2],
                row[3],
            ),
        ),
        start=1,
    ):
        entry = merged_entries[key]
        entry["entry_id"] = f"RM_{index:05d}"
        entry["source_pointers"] = sorted(entry["source_pointers"])
        entries.append(entry)
    payload = {
        "schema": "ROSETTA_MAP_v1",
        "map_id": f"ROSETTA_MAP__{_compact_ts()}",
        "created_utc": _utc_now(),
        "entries": entries,
        "source_pointers": source_pointers,
    }
    out_path = Path(args.out_json).resolve() if str(args.out_json).strip() else None
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
