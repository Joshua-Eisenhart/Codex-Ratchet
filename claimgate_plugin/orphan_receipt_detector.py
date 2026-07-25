#!/usr/bin/env python3
"""Detect claim receipts that have no durable ClaimGate-run evidence.

This DETECTS bypass; it does not PREVENT it.  At this enforcement level,
prevention is not possible: ``git commit --no-verify`` can skip the local
pre-commit hook.  CI must run this detector afterwards and fail if a receipt
cannot be tied to a durable gate record.

The current post-receipt gate runs several checks, but does not itself write a
durable record.  The minimal record it should start writing is one chained
ledger line containing:

    receipt_sha256 + gate_exit + timestamp + gate_source_digest

The detector accepts a ledger record only when all four fields are present,
the receipt digest matches exactly, and the gate-source digest is present.
Ledger files are intentionally discovered independently of receipt JSON files
so a receipt cannot certify itself by adding metadata to its own body.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


REQUIRED_LEDGER_FIELDS = {"receipt_sha256", "gate_exit", "timestamp", "gate_source_digest"}


def _is_excluded(path: Path) -> bool:
    parts = set(path.parts)
    return "hostile" in parts and "fixtures" in parts


def _json_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.json"):
        if path.is_file() and not _is_excluded(path):
            yield path


def _load_object(path: Path) -> Any:
    try:
        return json.loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def find_receipts(root: Path) -> list[Path]:
    """Return every parseable JSON object with a top-level classification."""
    receipts = []
    for path in _json_files(root):
        obj = _load_object(path)
        if isinstance(obj, dict) and "classification" in obj:
            receipts.append(path)
    return sorted(receipts)


def _ledger_records(root: Path) -> list[dict[str, Any]]:
    """Read possible JSON/JSONL ledger records, never receipt bodies."""
    records: list[dict[str, Any]] = []
    candidates = list(root.rglob("*.jsonl")) + list(root.rglob("*ledger*.json"))
    for path in candidates:
        if not path.is_file() or _is_excluded(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            parsed = json.loads(text)
            values = parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            values = []
            for line in text.splitlines():
                try:
                    values.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        records.extend(v for v in values if isinstance(v, dict))
    return records


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_orphans(root: Path) -> tuple[list[Path], int, int]:
    receipts = find_receipts(root)
    records = _ledger_records(root)
    durable_records = [
        record for record in records
        if REQUIRED_LEDGER_FIELDS <= record.keys()
        and isinstance(record["receipt_sha256"], str)
        and isinstance(record["gate_source_digest"], str)
        and record["gate_source_digest"]
    ]
    valid_bindings = {
        str(record["receipt_sha256"]).lower()
        for record in durable_records
    }
    orphans = [path for path in receipts if _digest(path).lower() not in valid_bindings]
    return orphans, len(receipts), len(durable_records)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    orphans, receipt_count, ledger_count = find_orphans(root)

    print(f"claim-bearing receipts: {receipt_count}")
    print(f"durable gate ledger records: {ledger_count}")
    if ledger_count == 0:
        print("NO DURABLE GATE-RUN RECORD CURRENTLY EXISTS; all discovered receipts are orphans.")
        print("Required minimal chained ledger line: receipt_sha256 + gate_exit + timestamp + gate_source_digest")
    print(f"orphan receipts: {len(orphans)}")
    for path in orphans:
        print(f"ORPHAN {path.relative_to(root)}")
    return 1 if orphans else 0


if __name__ == "__main__":
    raise SystemExit(main())
