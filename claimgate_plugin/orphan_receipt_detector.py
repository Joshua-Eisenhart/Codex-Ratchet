#!/usr/bin/env python3
"""Detect claim receipts that have no durable ClaimGate-run evidence.

This DETECTS bypass; it does not PREVENT it.  At this enforcement level,
prevention is not possible: ``git commit --no-verify`` can skip the local
pre-commit hook.  CI must run this detector afterwards and fail if a receipt
cannot be tied to a durable gate record.

The durable record is now written: claimgate_plugin/hooks/post_receipt_gate.sh
appends one hash-chained line per gate run to
claimgate_plugin/results/gate_ledger.jsonl (see claimgate_plugin/gate_ledger.py).
A ledger line is accepted here only when it carries all of

    receipt_sha256 + gate_exit + timestamp + gate_source_digest + prev_line_sha256

the receipt digest matches the receipt file's bytes exactly, and the line sits in
an INTACT hash chain.

GATED, NOT PASSED.  A receipt is non-orphan when the gate demonstrably RAN on it,
whatever the verdict.  BLOCKED and PARKED runs count as gated and are reported
separately, because "gate refused this and it is still in the tree" is a finding
in its own right, and because a ledger that only recorded passes would leave
"never ran" and "ran and refused" indistinguishable — the exact hole the ledger
closes.

Chain verification is implemented HERE, deliberately duplicating the writer's
logic in gate_ledger.py rather than importing it.  A detector that asks the
component it audits whether that component is honest inherits the lie; this is
the same failure shape as CI config living in the repo it gates.

Ledger files are discovered independently of receipt JSON files, so a receipt can
never certify itself by adding metadata to its own body.

Exit: 0 no orphans and chains intact | 1 orphans present | 2 a ledger chain is
broken or unreadable.  Nonzero is a policy/infra disposition, never a scientific
verdict.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

REQUIRED_LEDGER_FIELDS = {
    "receipt_sha256",
    "gate_exit",
    "timestamp",
    "gate_source_digest",
    "prev_line_sha256",
}

LEDGER_SCHEMA = "claimgate_gate_ledger_v1"
GENESIS = hashlib.sha256(f"{LEDGER_SCHEMA}/genesis".encode()).hexdigest()

BLOCKING_DISPOSITIONS = {"BLOCKED", "PARKED", "INFRA_ERROR", "INCOMPLETE"}


def _pinned_fixture_paths(root: Path) -> set[str]:
    """The SAME digest-pinned manifest ci_receipt_sweep.py uses. Read once per run."""
    try:
        doc = json.loads((root / "claimgate_plugin" / "fixtures"
                          / "sweep_fixture_manifest.json").read_bytes())
        return {e["path"] for e in doc["fixtures"]}
    except (OSError, ValueError, KeyError, TypeError):
        return set()


def _is_excluded(path: Path, root: Path, pinned: set[str] | None = None) -> bool:
    """Only a fixture PINNED BY DIGEST in the shared manifest is excluded.

    This used to be `"hostile" in parts and "fixtures" in parts` — the same
    path-shape exclusion that made hostile-fixture laundering the cheapest bypass
    in the sweep. Fixing it there and leaving it here would have left the identical
    hole open one file over: any new claim dropped into a directory whose path
    contains both words never entered the orphan baseline at all.
    """
    if pinned is None:
        pinned = _pinned_fixture_paths(root)
    try:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        return False
    return rel in pinned


def _json_files(root: Path) -> Iterable[Path]:
    pinned = _pinned_fixture_paths(root)
    for path in root.rglob("*.json"):
        if path.is_file() and not _is_excluded(path, root, pinned):
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


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_chain(path: Path) -> tuple[bool, list[str], list[dict[str, Any]]]:
    """Independently re-walk a chained ledger file.

    Returns (intact, problems, records).  On ANY break the records are DISCARDED:
    a chain break means the file has been edited, and the tampered line is itself
    inside the still-verifying prefix (line i's edit breaks line i+1's pointer),
    so no prefix of a broken ledger is safe to trust.
    """
    problems: list[str] = []
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return False, [f"{path.name}: unreadable ({exc})"], []
    lines = [ln for ln in raw.split(b"\n") if ln.strip()]

    records: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            problems.append(f"{path.name} line {index}: unparseable ({exc})")
            return False, problems, []
        if not isinstance(record, dict):
            problems.append(f"{path.name} line {index}: not an object")
            return False, problems, []
        expected = GENESIS if index == 0 else _sha256(lines[index - 1])
        if record.get("prev_line_sha256") != expected:
            problems.append(
                f"{path.name} line {index}: CHAIN BREAK — prev_line_sha256="
                f"{str(record.get('prev_line_sha256'))[:16]}... but line {index - 1} "
                f"hashes to {expected[:16]}...  A line was edited, deleted or inserted.")
        if record.get("seq") != index:
            problems.append(
                f"{path.name} line {index}: seq={record.get('seq')} does not match position")
        records.append(record)

    head = path.with_name(path.stem + ".head.json")
    if head.exists():
        anchor = _load_object(head)
        if not isinstance(anchor, dict):
            problems.append(f"{head.name}: head anchor unreadable")
        else:
            if anchor.get("count") != len(lines):
                problems.append(
                    f"{head.name}: anchor count={anchor.get('count')} but ledger holds "
                    f"{len(lines)} line(s) — TAIL TRUNCATION or an unrecorded append")
            if lines and anchor.get("last_line_sha256") != _sha256(lines[-1]):
                problems.append(f"{head.name}: anchor last_line_sha256 does not match the final line")

    if problems:
        return False, problems, []
    return True, [], records


def _looks_chained(path: Path) -> bool:
    try:
        raw = path.read_bytes()
    except OSError:
        return False
    return b'"prev_line_sha256"' in raw


def collect_ledger_records(root: Path) -> tuple[list[dict[str, Any]], list[str], list[Path]]:
    """Read chained gate-ledger records. Never reads receipt bodies."""
    records: list[dict[str, Any]] = []
    problems: list[str] = []
    ledgers: list[Path] = []
    for path in sorted(root.rglob("*.jsonl")):
        if not path.is_file() or _is_excluded(path, root) or not _looks_chained(path):
            continue
        ledgers.append(path)
        intact, file_problems, file_records = verify_chain(path)
        problems.extend(file_problems)
        if intact:
            records.extend(file_records)
    return records, problems, ledgers


def _is_durable(record: dict[str, Any]) -> bool:
    if not REQUIRED_LEDGER_FIELDS <= record.keys():
        return False
    digest = record["receipt_sha256"]
    if not isinstance(digest, str) or len(digest) != 64:
        return False
    try:
        int(digest, 16)
    except ValueError:
        return False
    if not isinstance(record["gate_exit"], int) or isinstance(record["gate_exit"], bool):
        return False
    if not isinstance(record["gate_source_digest"], str) or not record["gate_source_digest"]:
        return False
    if not isinstance(record["timestamp"], str) or not record["timestamp"]:
        return False
    return True


def find_orphans(root: Path) -> dict[str, Any]:
    receipts = find_receipts(root)
    records, chain_problems, ledgers = collect_ledger_records(root)
    durable = [record for record in records if _is_durable(record)]

    # Last run wins per receipt digest: a receipt re-gated after a fix should read
    # as its current disposition, not its first one.
    latest: dict[str, dict[str, Any]] = {}
    for record in durable:
        key = str(record["receipt_sha256"]).lower()
        prior = latest.get(key)
        if prior is None or record.get("seq", -1) >= prior.get("seq", -1):
            latest[key] = record

    gated: list[tuple[Path, dict[str, Any]]] = []
    orphans: list[Path] = []
    for path in receipts:
        record = latest.get(_sha256(path.read_bytes()).lower())
        (gated.append((path, record)) if record else orphans.append(path))

    by_disposition: dict[str, int] = {}
    for record in durable:
        label = str(record.get("disposition") or "UNLABELLED")
        by_disposition[label] = by_disposition.get(label, 0) + 1

    refused = [(p, r) for p, r in gated
               if str(r.get("disposition")) in BLOCKING_DISPOSITIONS]

    return {
        "receipts": receipts,
        "ledgers": ledgers,
        "records": records,
        "durable": durable,
        "gated": gated,
        "orphans": orphans,
        "refused": refused,
        "by_disposition": by_disposition,
        "chain_problems": chain_problems,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path,
                        default=Path(__file__).resolve().parent.parent)
    # Default 0 = print EVERY orphan. claimgate_plugin/ci_orphan_ratchet.py wraps
    # this detector and states that its full output, every ORPHAN line included,
    # reaches the job log. A truncating default would quietly break that.
    parser.add_argument("--max-list", type=int, default=0,
                        help="orphan paths to print (0 = all, the default)")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    report = find_orphans(root)

    print(f"claim-bearing receipts: {len(report['receipts'])}")
    for path in report["ledgers"]:
        print(f"gate ledger: {path.relative_to(root)}")
    print(f"durable gate ledger records: {len(report['durable'])}"
          f" (of {len(report['records'])} chained line(s) read)")
    for label in sorted(report["by_disposition"]):
        print(f"  disposition {label}: {report['by_disposition'][label]}")

    for problem in report["chain_problems"]:
        print(f"LEDGER TAMPER {problem}")
    if report["chain_problems"]:
        print("A broken chain voids the whole ledger file: its records are NOT counted.")

    if not report["durable"]:
        print("NO DURABLE GATE-RUN RECORD CURRENTLY EXISTS; all discovered receipts are orphans.")
        print("Required minimal chained ledger line: "
              "receipt_sha256 + gate_exit + timestamp + gate_source_digest + prev_line_sha256")

    print(f"receipts with a durable gate record: {len(report['gated'])}")
    for path, record in report["gated"]:
        print(f"GATED {path.relative_to(root)} "
              f"[{record.get('disposition') or 'UNLABELLED'} exit={record.get('gate_exit')} "
              f"seq={record.get('seq')} gate_src={str(record.get('gate_source_digest'))[:12]}]")
    if report["refused"]:
        print(f"gated but REFUSED and still present in the tree: {len(report['refused'])}")
        for path, record in report["refused"]:
            print(f"REFUSED {path.relative_to(root)} [{record.get('disposition')}]")

    orphans = report["orphans"]
    print(f"orphan receipts: {len(orphans)}")
    shown = orphans if args.max_list == 0 else orphans[:args.max_list]
    for path in shown:
        print(f"ORPHAN {path.relative_to(root)}")
    if len(orphans) > len(shown):
        print(f"... and {len(orphans) - len(shown)} more "
              f"(--max-list 0 to print every orphan)")

    if report["chain_problems"]:
        return 2
    return 1 if orphans else 0


if __name__ == "__main__":
    raise SystemExit(main())
