#!/usr/bin/env python3
"""Inventory prompt vs output corpora and draft two proposal-only MMMs.

This is the deterministic floor of cb-context-strategy-wave.
It does not admit packs, merge corpora, or claim a model read the drafts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


RECEIPT_SCHEMA = "constraintbox.context-strategy-receipt.v1"
USER_DRAFT_SCHEMA = "constraintbox.user-mmm-draft.v1"
PROJECT_DRAFT_SCHEMA = "constraintbox.project-mmm-draft.v1"
QUOTE = re.compile(r"^\s*>\s?(.*\S)\s*$")
# Keep reason codes, and accept schema identifiers whose components are
# separated by dots *or* hyphens.  The old expression only matched lower-case
# underscore names and silently discarded ids such as
# ``constraintbox.repo-consolidation.v1``.
TOKEN = re.compile(
    r"(REFUSE_[A-Z0-9_]+|HOLD_[A-Z0-9_]+|"
    r"[A-Za-z][A-Za-z0-9]*(?:[._-][A-Za-z0-9]+)+\.v[0-9]+)"
)
HEADING = re.compile(r"^#{1,3}\s+")
NUMBERED_ENTRY = re.compile(r"^##\s+\d+\.")
PASTED_FLAG = re.compile(r"pasted material,\s*not typed", re.IGNORECASE)

JSONL_OWNER_EVENT_TYPES = frozenset(
    {"OWNER_PROMPT", "OWNER_DIRECTIVE", "OWNER_DIRECTIVE_IMPORTED"}
)
JSONL_OWNER_SOURCE_KINDS = frozenset({"owner_verbatim", "owner_aligned_plan"})
PSEUDO_OWNER_PREFIXES = ("<recommended_plugins>", "# AGENTS.md instructions")
REPRESENTATIVE_LIMIT = 40


class JSONLParseError(ValueError):
    """A JSONL row failed the minimum source-custody shape."""

    def __init__(self, path: Path, line_number: int, detail: str) -> None:
        self.path = path
        self.line_number = line_number
        self.detail = detail
        super().__init__(f"{path}:{line_number}: {detail}")


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _collect_files(root: Path, declared: list[Path]) -> list[Path]:
    files: list[Path] = []
    for item in declared:
        path = item if item.is_absolute() else (root / item)
        if path.is_file():
            files.append(path.resolve())
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix.lower() in {
                    ".md",
                    ".txt",
                    ".json",
                    ".jsonl",
                }:
                    if "__pycache__" in child.parts:
                        continue
                    files.append(child.resolve())
    return sorted(set(files))


def _extract_quotes(path: Path) -> list[str]:
    return [item["text"] for item in _extract_attributed_quotes(path)]


def _extract_attributed_quotes(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() not in {".md", ".txt"}:
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    numbered = any(NUMBERED_ENTRY.match(line) for line in lines)
    speaker = "unattributed" if numbered else "owner_typed"
    quotes: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if HEADING.match(line):
            if PASTED_FLAG.search(line):
                speaker = "owner_pasted"
            elif NUMBERED_ENTRY.match(line):
                speaker = "owner_typed"
            continue
        match = QUOTE.match(line)
        if match:
            quotes.append(
                {
                    "text": match.group(1).strip(),
                    "speaker": speaker,
                    "line_number": line_number,
                }
            )
    return quotes


def _extract_tokens(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    return _extract_tokens_text(raw)


def _extract_tokens_text(raw: str) -> list[str]:
    found = TOKEN.findall(raw)
    # preserve order, drop dups
    seen: set[str] = set()
    out: list[str] = []
    for item in found:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _source_ref(
    *,
    path: Path,
    root: Path,
    line_number: int | None = None,
    event: dict[str, Any] | None = None,
    source_line_sha256: str | None = None,
) -> dict[str, Any]:
    """Return a compact, exact locator for one source item.

    A representative is allowed to be bounded, but it may not become an
    unattributed string.  Keep the event id, source object, material digest,
    and source line digest together so a later reader can recover the exact
    bytes or identify which upstream artifact supplied them.
    """

    ref: dict[str, Any] = {
        "path": str(path.relative_to(root) if path.is_relative_to(root) else path),
    }
    if line_number is not None:
        ref["line_number"] = line_number
    if event is not None:
        source = event.get("source")
        material = event.get("material")
        if event.get("event_id") is not None:
            ref["event_id"] = event["event_id"]
        if event.get("event_type") is not None:
            ref["event_type"] = event["event_type"]
        if source is not None:
            ref["source"] = source
        if isinstance(material, dict) and material.get("sha256"):
            ref["material_sha256"] = material["sha256"]
        if event.get("source_sequence") is not None:
            ref["source_sequence"] = event["source_sequence"]
    if source_line_sha256:
        ref["source_line_sha256"] = source_line_sha256
    return ref


def _parse_jsonl(path: Path, root: Path) -> list[dict[str, Any]]:
    """Parse a project-event JSONL file without silently skipping rows.

    The current context corpus wraps each event as ``{"event": {...}}``.
    Strictness here is deliberately about custody shape, not about a specific
    event vocabulary: new event types remain project material unless they are
    explicitly owner events or owner-sourced.
    """

    records: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8", errors="strict").splitlines(), start=1
    ):
        if not raw_line.strip():
            raise JSONLParseError(path, line_number, "blank line is not a JSONL event")
        try:
            row = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise JSONLParseError(path, line_number, f"invalid JSON: {exc.msg}") from exc
        if not isinstance(row, dict) or not isinstance(row.get("event"), dict):
            raise JSONLParseError(path, line_number, "row must contain an event object")
        event = row["event"]
        event_type = event.get("event_type")
        if not isinstance(event_type, str) or not event_type:
            raise JSONLParseError(path, line_number, "event.event_type must be a non-empty string")
        material = event.get("material")
        if not isinstance(material, dict) or not isinstance(material.get("text"), str):
            raise JSONLParseError(path, line_number, "event.material.text must be a string")
        source = event.get("source")
        if source is not None and not isinstance(source, (dict, str)):
            raise JSONLParseError(path, line_number, "event.source must be an object or string")
        text = material["text"]
        computed_material_digest = _sha256_bytes(text.encode("utf-8"))
        supplied_material_digest = material.get("sha256")
        if supplied_material_digest is not None and supplied_material_digest != computed_material_digest:
            raise JSONLParseError(path, line_number, "event.material.sha256 does not match text bytes")
        supplied_byte_length = material.get("byte_length")
        if supplied_byte_length is not None and supplied_byte_length != len(text.encode("utf-8")):
            raise JSONLParseError(path, line_number, "event.material.byte_length does not match text bytes")
        # Keep the original event and raw source line digest.  The event's
        # material digest is preserved as supplied; if absent, compute one so
        # every extracted record remains independently bound to exact bytes.
        material_digest = supplied_material_digest or computed_material_digest
        source_ref = _source_ref(
            path=path,
            root=root,
            line_number=line_number,
            event=event,
            source_line_sha256=row.get("source_line_sha256")
            or _sha256_bytes(raw_line.encode("utf-8")),
        )
        for field in ("source_sequence", "source_previous_sha256"):
            if row.get(field) is not None:
                source_ref[field] = row[field]
        records.append(
            {
                "text": text,
                "event": event,
                "event_type": event_type,
                "source_line": line_number,
                "source_line_sha256": row.get("source_line_sha256")
                or _sha256_bytes(raw_line.encode("utf-8")),
                "material_sha256": material_digest,
                "source_ref": source_ref,
            }
        )
    return records


def _is_pseudo_owner(text: str) -> bool:
    stripped = text.lstrip()
    return any(stripped.startswith(prefix) for prefix in PSEUDO_OWNER_PREFIXES)


def _jsonl_owner_record(record: dict[str, Any]) -> bool:
    event = record["event"]
    event_type = record["event_type"]
    source = event.get("source")
    source_kind = source.get("kind") if isinstance(source, dict) else source
    role = source.get("role") if isinstance(source, dict) else None
    # Imported owner directives and aligned plans are retained as project
    # context by default.  They are not typed owner voice unless the event's
    # source explicitly proves owner/user origin.
    return (
        event_type in {"OWNER_PROMPT", "OWNER_DIRECTIVE"}
        and (source_kind in JSONL_OWNER_SOURCE_KINDS or role == "user")
    )


def _unique_records(records: Iterable[dict[str, Any]], key: str = "text") -> list[dict[str, Any]]:
    """Deduplicate by content while keeping the first exact source reference."""

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for record in records:
        value = str(record[key])
        if value in seen:
            continue
        seen.add(value)
        unique.append(record)
    return unique


def _select_representatives(
    records: list[dict[str, Any]], limit: int = REPRESENTATIVE_LIMIT
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Select deterministic, evenly spaced representatives over source order."""

    unique = _unique_records(records)
    if len(unique) <= limit:
        selected = unique
    else:
        # Integer arithmetic avoids platform-dependent floating point choices.
        indices = [(i * (len(unique) - 1)) // (limit - 1) for i in range(limit)]
        selected = [unique[index] for index in indices]
    return selected, {
        "method": "unique_content_evenly_spaced_source_order",
        "limit": limit,
        "available_unique": len(unique),
        "selected_count": len(selected),
        "coverage_fraction": (len(selected) / len(unique)) if unique else 0.0,
    }


def _source_digest(records: Iterable[dict[str, Any]]) -> str:
    refs = [record["source_ref"] for record in records]
    return _sha256_bytes(json.dumps(refs, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _source_bound(phrases: list[str], corpus_text: str) -> list[str]:
    lost = []
    for phrase in phrases:
        if len(phrase) < 12:
            continue
        if phrase not in corpus_text:
            lost.append(phrase)
    return lost


def run_wave(
    *,
    root: Path,
    prompt_paths: list[Path],
    output_paths: list[Path],
    out: Path,
    admit: bool = False,
    merge: bool = False,
) -> dict[str, Any]:
    root = root.expanduser().resolve()
    if merge:
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "status": "REFUSE",
            "reason": "REFUSE_MERGED_CORPORA",
            "promotion_allowed": False,
            "admission_disposition": "rejected",
        }
        _write(out, receipt)
        return receipt
    if admit:
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "status": "REFUSE",
            "reason": "REFUSE_DRAFT_AS_LAW",
            "promotion_allowed": False,
            "admission_disposition": "rejected",
        }
        _write(out, receipt)
        return receipt

    prompt_files = _collect_files(root, prompt_paths)
    output_files = _collect_files(root, output_paths)
    overlap = {str(path) for path in prompt_files} & {str(path) for path in output_files}
    if overlap:
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "status": "HOLD",
            "reason": "HOLD_CORPUS_OVERLAP",
            "overlap": sorted(overlap),
            "promotion_allowed": False,
            "admission_disposition": "rejected",
        }
        _write(out, receipt)
        return receipt
    if not prompt_files or not output_files:
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "status": "HOLD",
            "reason": "HOLD_CORPUS_MISSING",
            "prompt_file_count": len(prompt_files),
            "output_file_count": len(output_files),
            "promotion_allowed": False,
            "admission_disposition": "rejected",
        }
        _write(out, receipt)
        return receipt

    prompt_quotes: list[dict[str, Any]] = []
    owner_records: list[dict[str, Any]] = []
    project_records: list[dict[str, Any]] = []
    project_token_records: list[dict[str, Any]] = []
    jsonl_index: list[dict[str, Any]] = []
    pseudo_owner_count = 0
    prompt_bytes = 0
    prompt_index = []
    speaker_counts = {"owner_typed": 0, "owner_pasted": 0, "unattributed": 0}
    for path in prompt_files:
        raw = path.read_bytes()
        prompt_bytes += len(raw)
        quotes: list[dict[str, Any]] = []
        jsonl_rows: list[dict[str, Any]] = []
        if path.suffix.lower() == ".jsonl":
            try:
                jsonl_rows = _parse_jsonl(path, root)
            except (JSONLParseError, UnicodeError) as exc:
                receipt = {
                    "schema": RECEIPT_SCHEMA,
                    "status": "HOLD",
                    "reason": "HOLD_JSONL_PARSE",
                    "error": str(exc),
                    "path": str(path),
                    "promotion_allowed": False,
                    "admission_disposition": "rejected",
                }
                _write(out, receipt)
                return receipt
            for record in jsonl_rows:
                if _is_pseudo_owner(record["text"]):
                    pseudo_owner_count += 1
                    continue
                if _jsonl_owner_record(record):
                    owner_record = dict(record)
                    owner_record["speaker"] = "owner_typed"
                    owner_records.append(owner_record)
                    prompt_quotes.append(owner_record)
                    speaker_counts["owner_typed"] += 1
                else:
                    project_records.append(record)
            jsonl_index.append(
                {
                    "path": str(path.relative_to(root) if path.is_relative_to(root) else path),
                    "sha256": _sha256_bytes(raw),
                    "bytes": len(raw),
                    "row_count": len(jsonl_rows),
                    "owner_event_count": sum(
                        1
                        for item in jsonl_rows
                        if _jsonl_owner_record(item) and not _is_pseudo_owner(item["text"])
                    ),
                    "project_event_count": sum(
                        1
                        for item in jsonl_rows
                        if not _jsonl_owner_record(item)
                        and not _is_pseudo_owner(item["text"])
                    ),
                    "pseudo_owner_excluded_count": sum(
                        1 for item in jsonl_rows if _is_pseudo_owner(item["text"])
                    ),
                }
            )
        else:
            quotes = _extract_attributed_quotes(path)
            for item in quotes:
                record = {
                    "text": item["text"],
                    "speaker": item["speaker"],
                    "source_ref": _source_ref(
                        path=path,
                        root=root,
                        line_number=item.get("line_number"),
                    ),
                    "material_sha256": _sha256_bytes(item["text"].encode("utf-8")),
                }
                prompt_quotes.append(record)
                if item["speaker"] == "owner_typed":
                    owner_records.append(record)
                speaker_counts[item["speaker"]] = speaker_counts.get(item["speaker"], 0) + 1
        prompt_index.append(
            {
                "path": str(path.relative_to(root) if path.is_relative_to(root) else path),
                "sha256": _sha256_bytes(raw),
                "bytes": len(raw),
                "quote_count": len(quotes),
                "jsonl_row_count": len(jsonl_rows),
                "owner_typed_count": (
                    sum(1 for item in quotes if item["speaker"] == "owner_typed")
                    + sum(
                        1
                        for item in jsonl_rows
                        if _jsonl_owner_record(item) and not _is_pseudo_owner(item["text"])
                    )
                ),
                "owner_pasted_count": sum(1 for item in quotes if item["speaker"] == "owner_pasted"),
                "unattributed_count": sum(1 for item in quotes if item["speaker"] == "unattributed"),
            }
        )

    output_bytes = 0
    output_index = []
    for path in output_files:
        raw = path.read_bytes()
        output_bytes += len(raw)
        tokens: list[str] = []
        jsonl_rows: list[dict[str, Any]] = []
        if path.suffix.lower() == ".jsonl":
            try:
                jsonl_rows = _parse_jsonl(path, root)
            except (JSONLParseError, UnicodeError) as exc:
                receipt = {
                    "schema": RECEIPT_SCHEMA,
                    "status": "HOLD",
                    "reason": "HOLD_JSONL_PARSE",
                    "error": str(exc),
                    "path": str(path),
                    "promotion_allowed": False,
                    "admission_disposition": "rejected",
                }
                _write(out, receipt)
                return receipt
            for record in jsonl_rows:
                if _is_pseudo_owner(record["text"]):
                    pseudo_owner_count += 1
                    continue
                if _jsonl_owner_record(record):
                    owner_record = dict(record)
                    owner_record["speaker"] = "owner_typed"
                    owner_records.append(owner_record)
                    prompt_quotes.append(owner_record)
                    speaker_counts["owner_typed"] += 1
                else:
                    project_records.append(record)
                    tokens.extend(_extract_tokens_text(record["text"]))
            jsonl_index.append(
                {
                    "path": str(path.relative_to(root) if path.is_relative_to(root) else path),
                    "sha256": _sha256_bytes(raw),
                    "bytes": len(raw),
                    "row_count": len(jsonl_rows),
                    "owner_event_count": sum(
                        1
                        for item in jsonl_rows
                        if _jsonl_owner_record(item) and not _is_pseudo_owner(item["text"])
                    ),
                    "project_event_count": sum(
                        1
                        for item in jsonl_rows
                        if not _jsonl_owner_record(item)
                        and not _is_pseudo_owner(item["text"])
                    ),
                    "pseudo_owner_excluded_count": sum(
                        1 for item in jsonl_rows if _is_pseudo_owner(item["text"])
                    ),
                }
            )
        else:
            raw_text = raw.decode("utf-8", errors="replace")
            tokens = _extract_tokens_text(raw_text)
            project_records.append(
                {
                    "text": raw_text,
                    "source_ref": _source_ref(path=path, root=root),
                    "material_sha256": _sha256_bytes(raw),
                }
            )
        output_index.append(
            {
                "path": str(path.relative_to(root) if path.is_relative_to(root) else path),
                "sha256": _sha256_bytes(raw),
                "bytes": len(raw),
                "jsonl_row_count": len(jsonl_rows),
                "token_count": len(tokens),
            }
        )

    # JSONL rows can carry both corpora in one source file.  Markdown keeps the
    # older quote behavior: only explicitly typed owner quotes become user
    # material; pasted and unattributed quotes stay inventory-only.
    owner_records = [item for item in owner_records if item.get("speaker") == "owner_typed"]
    owner_selected, owner_selection = _select_representatives(owner_records)
    typed_quotes = [item["text"] for item in owner_selected]
    user_lines = list(dict.fromkeys(typed_quotes))

    # Extract project tokens from event material rather than serialised JSONL
    # wrappers.  Retain one source reference per first-seen token.
    token_records: list[dict[str, Any]] = []
    for record in project_records:
        for token in _extract_tokens_text(record["text"]):
            token_records.append(
                {
                    "token": token,
                    "text": token,
                    "source_ref": record["source_ref"],
                }
            )
    project_token_records = _unique_records(token_records, key="token")
    project_selected, project_selection = _select_representatives(project_token_records)
    project_lines = [item["token"] for item in project_selected]
    prompt_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in prompt_files)
    output_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in output_files)
    owner_material_text = "\n".join(record["text"] for record in owner_records)
    project_material_text = "\n".join(record["text"] for record in project_records)
    # JSONL escapes embedded newlines in the outer row, so binding against the
    # raw file would produce false loss.  Bind representatives to the exact
    # decoded material bytes instead; markdown still has the same source text.
    user_lost = _source_bound(user_lines, owner_material_text or prompt_text)
    project_lost = _source_bound(project_lines, project_material_text or output_text)
    if not owner_records or not project_token_records:
        empty = []
        if not owner_records:
            empty.append("owner")
        if not project_token_records:
            empty.append("project")
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "status": "HOLD",
            "reason": (
                "HOLD_CONTEXT_EXTRACTION_EMPTY"
                if len(empty) > 1
                else f"HOLD_{empty[0].upper()}_EXTRACTION_EMPTY"
            ),
            "empty_extractions": empty,
            "owner_material_count": len(owner_records),
            "project_material_count": len(project_records),
            "project_token_count": len(project_token_records),
            "pseudo_owner_excluded_count": pseudo_owner_count,
            "jsonl_index": jsonl_index,
            "promotion_allowed": False,
            "admission_disposition": "rejected",
        }
        _write(out, receipt)
        return receipt
    if user_lost or project_lost:
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "status": "HOLD",
            "reason": "HOLD_SOURCE_LOST",
            "user_lost": user_lost,
            "project_lost": project_lost,
            "promotion_allowed": False,
            "admission_disposition": "rejected",
        }
        _write(out, receipt)
        return receipt

    user_draft = {
        "schema": USER_DRAFT_SCHEMA,
        "surface_class": "PROPOSAL_A1",
        "promotion_allowed": False,
        "source": "user_prompts_only",
        "speaker_filter": "owner_typed",
        "distinctions": user_lines,
        "distinction_sources": [item["source_ref"] for item in owner_selected],
        "selection": owner_selection,
    }
    project_draft = {
        "schema": PROJECT_DRAFT_SCHEMA,
        "surface_class": "PROPOSAL_A1",
        "promotion_allowed": False,
        "source": "project_outputs_only",
        "tokens": project_lines,
        "token_sources": [item["source_ref"] for item in project_selected],
        "selection": project_selection,
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    user_path = out.with_name("user_mmm.draft.json")
    project_path = out.with_name("project_mmm.draft.json")
    user_path.write_text(json.dumps(user_draft, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    project_path.write_text(
        json.dumps(project_draft, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "captured_at": _now(),
        "status": "CONTEXT_SNAPSHOT_READY",
        "promotion_allowed": False,
        "admission_disposition": "demote_RUNTIME_ONLY",
        "prompt_file_count": len(prompt_files),
        "output_file_count": len(output_files),
        "prompt_bytes": prompt_bytes,
        "output_bytes": output_bytes,
        "prompt_corpus_digest": _sha256_bytes(
            json.dumps(prompt_index, sort_keys=True).encode("utf-8")
        ),
        "output_corpus_digest": _sha256_bytes(
            json.dumps(output_index, sort_keys=True).encode("utf-8")
        ),
        "user_mmm_draft": str(user_path),
        "project_mmm_draft": str(project_path),
        "user_mmm_draft_digest": _sha256_path(user_path),
        "project_mmm_draft_digest": _sha256_path(project_path),
        "jsonl_index": jsonl_index,
        "owner_material_count": len(owner_records),
        "project_material_count": len(project_records),
        "owner_source_digest": _source_digest(owner_records),
        "project_source_digest": _source_digest(project_records),
        "pseudo_owner_excluded_count": pseudo_owner_count,
        "user_quote_count": len(user_lines),
        "owner_typed_quote_count": speaker_counts["owner_typed"],
        "owner_pasted_quote_count": speaker_counts["owner_pasted"],
        "unattributed_quote_count": speaker_counts["unattributed"],
        "speaker_filter": "owner_typed",
        "project_token_count": len(project_lines),
        "selection": {
            "owner": owner_selection,
            "project": project_selection,
        },
        "custody_statements": [
            "prompt and output corpora remain separate",
            "representatives retain exact source references and digests",
            "drafts remain proposal-only and are not packs or authority",
        ],
        "mmm_read_proved": False,
        "active_inference": {
            "kind": "language_model_of_corpora",
            "not": ["light_geometry", "fep", "spinor"],
            "user_predicts": "user distinctions in prompts",
            "project_predicts": "receipt vocabulary in outputs",
            "residual": "new source bytes the draft cannot quote",
        },
        "claim_ceiling": (
            "context inventory and proposal-only MMM drafts; "
            "not pack admission; not Light geometry; not promotion"
        ),
    }
    _write(out, receipt)
    return receipt


def _write(path: Path, receipt: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CB context-strategy inventory")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--prompt-path", action="append", type=Path, required=True)
    parser.add_argument("--output-path", action="append", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--admit", action="store_true")
    parser.add_argument("--merge", action="store_true")
    args = parser.parse_args(argv)
    receipt = run_wave(
        root=args.root,
        prompt_paths=list(args.prompt_path),
        output_paths=list(args.output_path),
        out=args.out,
        admit=args.admit,
        merge=args.merge,
    )
    print(json.dumps({"status": receipt.get("status"), "reason": receipt.get("reason")}, sort_keys=True))
    return 0 if receipt.get("status") == "CONTEXT_SNAPSHOT_READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
