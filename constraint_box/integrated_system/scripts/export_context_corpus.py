#!/usr/bin/env python3
"""Export the prompt/plan/progress strata from a verified project ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "constraintbox.context-corpus-export.v1"
KEEP_TYPES = frozenset(
    {
        "OWNER_PROMPT",
        "OWNER_DIRECTIVE",
        "OWNER_DIRECTIVE_IMPORTED",
        "ASSISTANT_OBSERVATION",
        "INTERFACE_CONTRACT",
        "PLAN_REVISION",
        "PLAN_REVISION_IMPORTED",
        "PLAN_UPDATE",
        "PROGRESS_UPDATE",
        "PROGRESS_IMPORTED",
        "STRATEGY_CONTEXT_DELTA",
        "VERIFICATION_RESULT",
        "CHECKPOINT_EMITTED",
        "CAMPAIGN_ASSESSMENT",
        "MAINTENANCE_RECEIPT",
    }
)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_and_verify_ledger(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    previous = "0" * 64
    for index, line in enumerate(path.read_bytes().splitlines(), start=1):
        if not line:
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"ledger row {index} is not an object")
        body = {key: value for key, value in row.items() if key != "line_sha256"}
        observed = sha256_bytes(canonical_json_bytes(body))
        if row.get("line_sha256") != observed:
            raise ValueError(f"ledger row {index} digest mismatch")
        if row.get("previous_sha256") != previous:
            raise ValueError(f"ledger row {index} chain mismatch")
        if row.get("sequence") != len(rows) + 1:
            raise ValueError(f"ledger row {index} sequence mismatch")
        previous = observed
        rows.append(row)
    if not rows:
        raise ValueError("ledger is empty")
    return rows


def export_rows(
    rows: Iterable[dict[str, Any]], keep_types: frozenset[str] = KEEP_TYPES
) -> list[dict[str, Any]]:
    selected = []
    for row in rows:
        event = row.get("event")
        if not isinstance(event, dict) or event.get("event_type") not in keep_types:
            continue
        material = event.get("material")
        if not isinstance(material, dict) or not isinstance(material.get("text"), str):
            raise ValueError(f"selected event lacks inline text: {event.get('event_id')}")
        selected.append(
            {
                "source_sequence": row["sequence"],
                "source_previous_sha256": row["previous_sha256"],
                "source_line_sha256": row["line_sha256"],
                "event": event,
            }
        )
    return selected


def write_export(
    ledger: Path,
    output: Path,
    summary_path: Path,
    expected_head: str | None = None,
) -> dict[str, Any]:
    raw_ledger = ledger.read_bytes()
    rows = load_and_verify_ledger(ledger)
    source_head = rows[-1]["line_sha256"]
    if expected_head is not None and source_head != expected_head:
        raise ValueError(
            f"ledger head mismatch: expected {expected_head}, observed {source_head}"
        )
    selected = export_rows(rows)
    output_bytes = b"".join(canonical_json_bytes(row) + b"\n" for row in selected)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(output_bytes)
    counts = Counter(row["event"]["event_type"] for row in selected)
    summary = {
        "schema": SCHEMA,
        "source_ledger_original_path": str(ledger.resolve()),
        "source_ledger_required_at_runtime": False,
        "source_ledger_sha256": sha256_bytes(raw_ledger),
        "source_event_count": len(rows),
        "source_head_sha256": source_head,
        "selected_event_count": len(selected),
        "selected_event_types": dict(sorted(counts.items())),
        "selected_text_bytes": sum(
            len(row["event"]["material"]["text"].encode("utf-8"))
            for row in selected
        ),
        "output": os.path.relpath(output.resolve(), summary_path.parent.resolve()),
        "output_sha256": sha256_bytes(output_bytes),
        "output_bytes": len(output_bytes),
        "excluded_strata": [
            "SOURCE_SNAPSHOT_IMPORTED",
            "SOURCE_DELTA_IMPORTED",
            "EVIDENCE_ARTIFACT_IMPORTED",
            "object_store_bytes",
        ],
        "claim_ceiling": (
            "verbatim prompt, assistant-observation, plan, progress, and verification "
            "projection from a verified ledger chain; not the full ledger/object store, "
            "not canon, and not semantic admission"
        ),
        "promotion_allowed": False,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--expected-head")
    args = parser.parse_args()
    try:
        summary = write_export(
            args.ledger, args.output, args.summary, args.expected_head
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "disposition": "REFUSE_CONTEXT_CORPUS_EXPORT",
                    "detail": f"{type(exc).__name__}:{exc}",
                    "promotion_allowed": False,
                },
                sort_keys=True,
            )
        )
        return 2
    print(
        json.dumps(
            {
                "disposition": "CONTEXT_CORPUS_EXPORTED_LOCAL",
                **summary,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
