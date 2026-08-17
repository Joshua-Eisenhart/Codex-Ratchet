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
from typing import Any


RECEIPT_SCHEMA = "constraintbox.context-strategy-receipt.v1"
USER_DRAFT_SCHEMA = "constraintbox.user-mmm-draft.v1"
PROJECT_DRAFT_SCHEMA = "constraintbox.project-mmm-draft.v1"
QUOTE = re.compile(r"^\s*>\s?(.*\S)\s*$")
TOKEN = re.compile(r"(REFUSE_[A-Z0-9_]+|HOLD_[A-Z0-9_]+|[a-z]+(?:_[a-z0-9]+){1,6}\.v[0-9]+)")
HEADING = re.compile(r"^#{1,3}\s+")
NUMBERED_ENTRY = re.compile(r"^##\s+\d+\.")
PASTED_FLAG = re.compile(r"pasted material,\s*not typed", re.IGNORECASE)


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


def _extract_attributed_quotes(path: Path) -> list[dict[str, str]]:
    if path.suffix.lower() not in {".md", ".txt"}:
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    numbered = any(NUMBERED_ENTRY.match(line) for line in lines)
    speaker = "unattributed" if numbered else "owner_typed"
    quotes: list[dict[str, str]] = []
    for line in lines:
        if HEADING.match(line):
            if PASTED_FLAG.search(line):
                speaker = "owner_pasted"
            elif NUMBERED_ENTRY.match(line):
                speaker = "owner_typed"
            continue
        match = QUOTE.match(line)
        if match:
            quotes.append({"text": match.group(1).strip(), "speaker": speaker})
    return quotes


def _extract_tokens(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    found = TOKEN.findall(raw)
    # preserve order, drop dups
    seen: set[str] = set()
    out: list[str] = []
    for item in found:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


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

    prompt_quotes: list[dict[str, str]] = []
    prompt_bytes = 0
    prompt_index = []
    speaker_counts = {"owner_typed": 0, "owner_pasted": 0, "unattributed": 0}
    for path in prompt_files:
        raw = path.read_bytes()
        prompt_bytes += len(raw)
        quotes = _extract_attributed_quotes(path)
        prompt_quotes.extend(quotes)
        for item in quotes:
            speaker_counts[item["speaker"]] = speaker_counts.get(item["speaker"], 0) + 1
        prompt_index.append(
            {
                "path": str(path.relative_to(root) if path.is_relative_to(root) else path),
                "sha256": _sha256_bytes(raw),
                "bytes": len(raw),
                "quote_count": len(quotes),
                "owner_typed_count": sum(1 for item in quotes if item["speaker"] == "owner_typed"),
                "owner_pasted_count": sum(1 for item in quotes if item["speaker"] == "owner_pasted"),
                "unattributed_count": sum(1 for item in quotes if item["speaker"] == "unattributed"),
            }
        )

    output_tokens: list[str] = []
    output_bytes = 0
    output_index = []
    for path in output_files:
        raw = path.read_bytes()
        output_bytes += len(raw)
        tokens = _extract_tokens(path)
        output_tokens.extend(tokens)
        output_index.append(
            {
                "path": str(path.relative_to(root) if path.is_relative_to(root) else path),
                "sha256": _sha256_bytes(raw),
                "bytes": len(raw),
                "token_count": len(tokens),
            }
        )

    # unique preserve order; user MMM is typed owner voice only
    typed_quotes = [item["text"] for item in prompt_quotes if item["speaker"] == "owner_typed"]
    user_lines = list(dict.fromkeys(typed_quotes))[:40]
    project_lines = list(dict.fromkeys(output_tokens))[:40]
    prompt_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in prompt_files)
    output_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in output_files)
    user_lost = _source_bound(user_lines, prompt_text)
    project_lost = _source_bound(project_lines, output_text)
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
        "must_not_lose": [
            "Failure is its own full wave",
            "falsification is deductive",
            "induction keeps an antichain",
            "skills and MMMs matter more than wave labels",
        ],
    }
    project_draft = {
        "schema": PROJECT_DRAFT_SCHEMA,
        "surface_class": "PROPOSAL_A1",
        "promotion_allowed": False,
        "source": "project_outputs_only",
        "tokens": project_lines,
        "must_not_lose": [
            "finite_time_first_seed_validation.v1",
            "finite_probe_assignment_feasibility.v1",
            "bound_observation_quotient.v1",
            "solver-chosen obs are not bound rows",
        ],
    }
    # hard-coded must_not_lose still have to appear in some source or stay
    # as wave-carried killed premises, not as claimed quotes.

    out.parent.mkdir(parents=True, exist_ok=True)
    user_path = out.with_name("user_mmm.draft.json")
    project_path = out.with_name("project_mmm.draft.json")
    user_path.write_text(json.dumps(user_draft, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    project_path.write_text(
        json.dumps(project_draft, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    must_not_lose = [
        "keep prompt corpus and output corpus apart",
        "do not admit MMM drafts as packs",
        "do not import FEP as Light geometry",
        *user_draft["must_not_lose"],
        *project_draft["must_not_lose"],
    ]
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
        "user_quote_count": len(user_lines),
        "owner_typed_quote_count": speaker_counts["owner_typed"],
        "owner_pasted_quote_count": speaker_counts["owner_pasted"],
        "unattributed_quote_count": speaker_counts["unattributed"],
        "speaker_filter": "owner_typed",
        "project_token_count": len(project_lines),
        "must_not_lose": must_not_lose,
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
