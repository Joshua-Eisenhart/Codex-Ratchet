#!/usr/bin/env python3
"""Compute a producer's ClaimGate standing from recorded ledger outcomes.

Identity is resolved from the receipt named by each ledger line using the same
precedence as ``claim_verify.py``: ``produced_by``, then ``builder``, then
``author``. Missing or unreadable receipts are UNRESOLVED; readable receipts
without one of those fields are ANONYMOUS.

HONEST CEILING: the identity is a string the producer wrote into its own
receipt. It is trivially forgeable: any producer can type another producer's
name, or a fresh name each run. This module raises the cost of a bad record from
zero to "pick a new name every run, and be treated as unknown-strictest every
time". It is not authentication.

The ledger is parsed as an outcome record; its hash chain is not verified here.
This module is read-only and deliberately does not import ``gate_ledger`` or
call its append path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True


PLUGIN_DIR = Path(__file__).resolve().parent
REPO_ROOT = PLUGIN_DIR.parent
DEFAULT_LEDGER = PLUGIN_DIR / "results" / "gate_ledger.jsonl"
REGISTRY_PATH = PLUGIN_DIR / "gate_registry.json"

TIER_ORDER = ("tier0", "tier1", "tier2", "tier3", "tier4")
CLEAN_RUN_MINIMUM = 3
ANONYMOUS = "ANONYMOUS"
UNRESOLVED = "UNRESOLVED"

DISPOSITION_CLASSES = {
    "PASS": "admitting",
    "ADMITTED_PENDING_DEPTH": "admitting",
    "ADMITTED_FLOOR_PARKED": "admitting",
    "BLOCKED": "refusing",
    "PARKED": "non_verdict",
    "INCOMPLETE": "non_verdict",
    "INFRA_ERROR": "non_verdict",
}

# Controller-owned escalation policy. Lists are cumulative requirements through
# the named floor. CLEAN_ESTABLISHED adds nothing; gate_registry remains the
# complete source of claim-kind requirements for that band.
TIER_FLOOR_POLICY = {
    "CLEAN_ESTABLISHED": {
        "floor_tiers": [],
        "reason": f"at least {CLEAN_RUN_MINIMUM} admitting runs, no refusals, and no unearned passes",
    },
    "REFUSAL_RECORDED": {
        "floor_tiers": ["tier0", "tier1"],
        "reason": "at least one recorded refusal; the lowest tier alone is insufficient",
    },
    "UNEARNED_PASS_RECORDED": {
        "floor_tiers": ["tier0", "tier1", "tier2"],
        "reason": "a later refusal took back an earlier admission for the same unchanged receipt",
    },
    "UNKNOWN_STRICTEST": {
        "floor_tiers": list(TIER_ORDER),
        "reason": (
            f"unknown, anonymous, unresolved, non-verdict-only, or fewer than "
            f"{CLEAN_RUN_MINIMUM} clean runs; new identities are strictest"
        ),
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _receipt_path(raw: Any, root: Path) -> Path | None:
    if not isinstance(raw, str) or not raw:
        return None
    path = Path(raw)
    return path if path.is_absolute() else root / path


def _identity(receipt: Any) -> str:
    if not isinstance(receipt, dict):
        return ANONYMOUS
    value = receipt.get("produced_by") or receipt.get("builder") or receipt.get("author")
    if value is None or not str(value).strip():
        return ANONYMOUS
    name = str(value).strip()
    # Controller buckets must not be forgeable by declaring their display name.
    return f"NAMED:{name}" if name in {ANONYMOUS, UNRESOLVED} else name


def _empty_producer(name: str) -> dict[str, Any]:
    return {
        "producer": name,
        "admitting": 0,
        "refusing": 0,
        "non_verdict": 0,
        "unclassified": 0,
        "recorded_disposition_counts": {
            "admitting": 0,
            "refusing": 0,
            "non_verdict": 0,
            "unclassified": 0,
        },
        "unearned_pass_count": 0,
        "unearned_passes": [],
        "changed_receipt_transitions": [],
        "changed_current_receipts": [],
        "lines": [],
    }


def _band(record: dict[str, Any]) -> tuple[str, str]:
    if record["producer"] in {ANONYMOUS, UNRESOLVED}:
        band = "UNKNOWN_STRICTEST"
    elif record["unearned_pass_count"]:
        band = "UNEARNED_PASS_RECORDED"
    elif record["refusing"]:
        band = "REFUSAL_RECORDED"
    elif (
        record["admitting"] >= CLEAN_RUN_MINIMUM
        and record["refusing"] == 0
        and record["unearned_pass_count"] == 0
    ):
        band = "CLEAN_ESTABLISHED"
    else:
        band = "UNKNOWN_STRICTEST"
    return band, TIER_FLOOR_POLICY[band]["reason"]


def compute_standings(
    ledger: str | Path = DEFAULT_LEDGER, root: str | Path = REPO_ROOT
) -> dict[str, Any]:
    """Return per-producer standing without writing or chain-verifying the ledger."""
    ledger_path = Path(ledger)
    root_path = Path(root).resolve()
    if not ledger_path.is_absolute():
        ledger_path = root_path / ledger_path
    producers: dict[str, dict[str, Any]] = {}
    parsed: list[dict[str, Any]] = []
    unresolved_lines = 0
    anonymous_lines = 0

    with ledger_path.open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"ledger line {line_number} is invalid JSON: {exc}") from exc
            if not isinstance(entry, dict):
                raise ValueError(f"ledger line {line_number} is not an object")

            receipt_path = _receipt_path(entry.get("receipt_path"), root_path)
            identity = UNRESOLVED
            receipt_status = "unresolved"
            sha_agreement: bool | None = None
            current_sha: str | None = None
            if receipt_path is not None:
                try:
                    receipt_bytes = receipt_path.read_bytes()
                    receipt = json.loads(receipt_bytes)
                except (OSError, UnicodeError, json.JSONDecodeError):
                    pass
                else:
                    identity = _identity(receipt)
                    receipt_status = "anonymous" if identity == ANONYMOUS else "resolved"
                    current_sha = hashlib.sha256(receipt_bytes).hexdigest()
                    recorded_sha = entry.get("receipt_sha256")
                    sha_agreement = (
                        isinstance(recorded_sha, str)
                        and bool(recorded_sha)
                        and current_sha == recorded_sha
                    )

            unresolved_lines += identity == UNRESOLVED
            anonymous_lines += identity == ANONYMOUS
            producer = producers.setdefault(identity, _empty_producer(identity))
            disposition = entry.get("disposition")
            classification = DISPOSITION_CLASSES.get(disposition, "unclassified")
            producer["recorded_disposition_counts"][classification] += 1
            usable_evidence = sha_agreement is True
            line_record = {
                "line": line_number,
                "seq": entry.get("seq"),
                "receipt_path": entry.get("receipt_path"),
                "receipt_sha256": entry.get("receipt_sha256"),
                "current_receipt_sha256": current_sha,
                "sha256_agreement": sha_agreement,
                "receipt_status": receipt_status,
                "disposition": disposition,
                "classification": classification,
                "used_as_outcome_evidence": usable_evidence,
            }
            producer["lines"].append(line_record)
            parsed.append({**line_record, "producer": identity})
            if usable_evidence:
                producer[classification] += 1
            elif sha_agreement is False:
                producer["changed_current_receipts"].append(
                    {
                        "seq": entry.get("seq"),
                        "receipt_path": entry.get("receipt_path"),
                        "recorded_sha256": entry.get("receipt_sha256"),
                        "current_sha256": current_sha,
                        "disposition_excluded": disposition,
                    }
                )

    by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for line in parsed:
        path = line.get("receipt_path")
        if isinstance(path, str) and path:
            by_path[path].append(line)
    for receipt_path, lines in by_path.items():
        seen_unearned: set[tuple[Any, ...]] = set()
        seen_changed: set[tuple[Any, ...]] = set()
        admitting = [line for line in lines if line["classification"] == "admitting"]
        refusing = [line for line in lines if line["classification"] == "refusing"]
        for admitted in admitting:
            for refused in refusing:
                seq_a, seq_r = admitted.get("seq"), refused.get("seq")
                if not isinstance(seq_a, int) or not isinstance(seq_r, int) or seq_r <= seq_a:
                    continue
                same_identity = admitted["producer"] == refused["producer"]
                same_sha = admitted.get("receipt_sha256") == refused.get("receipt_sha256")
                if not same_sha:
                    key = (
                        seq_a,
                        seq_r,
                        receipt_path,
                        admitted.get("receipt_sha256"),
                        refused.get("receipt_sha256"),
                        refused["producer"],
                    )
                    if key in seen_changed:
                        continue
                    seen_changed.add(key)
                    transition = {
                        "seq_admitted": seq_a,
                        "seq_refused": seq_r,
                        "receipt_path": receipt_path,
                        "admitted_sha256": admitted.get("receipt_sha256"),
                        "refused_sha256": refused.get("receipt_sha256"),
                        "reading": "changed receipt, not an unearned pass",
                    }
                    producers[refused["producer"]]["changed_receipt_transitions"].append(transition)
                elif (
                    same_identity
                    and admitted["used_as_outcome_evidence"]
                    and refused["used_as_outcome_evidence"]
                ):
                    key = (seq_a, seq_r, receipt_path, refused["producer"])
                    if key in seen_unearned:
                        continue
                    seen_unearned.add(key)
                    producers[refused["producer"]]["unearned_passes"].append(
                        {
                            "seq_admitted": seq_a,
                            "seq_refused": seq_r,
                            "receipt_path": receipt_path,
                        }
                    )

    for producer in producers.values():
        producer["unearned_pass_count"] = len(producer["unearned_passes"])
        band, reason = _band(producer)
        producer["standing_band"] = band
        producer["floor_tiers"] = list(TIER_FLOOR_POLICY[band]["floor_tiers"])
        producer["reason"] = reason

    return {
        "ledger": str(ledger_path),
        "root": str(root_path),
        "chain_verified": False,
        "clean_run_minimum": CLEAN_RUN_MINIMUM,
        "disposition_classes": DISPOSITION_CLASSES,
        "unresolved_lines": unresolved_lines,
        "anonymous_lines": anonymous_lines,
        "producers": dict(sorted(producers.items())),
    }


def _registry_requirements(claim_kind: str) -> tuple[list[str], bool]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    claim = (registry.get("claim_kinds") or {}).get(claim_kind)
    if not isinstance(claim, dict):
        return [], False
    tiers = claim.get("required_tiers", [])
    if not isinstance(tiers, list) or any(tier not in TIER_ORDER for tier in tiers):
        raise ValueError(f"registry claim kind {claim_kind!r} has invalid required_tiers")
    return list(tiers), True


def floor_detail(
    claim_kind: str,
    producer: str,
    ledger: str | Path = DEFAULT_LEDGER,
    root: str | Path = REPO_ROOT,
) -> dict[str, Any]:
    standings = compute_standings(ledger, root)
    record = standings["producers"].get(producer)
    if record is None:
        band = "UNKNOWN_STRICTEST"
        reason = "producer has no ledger history; new identities receive the strictest floor"
    else:
        band = record["standing_band"]
        reason = record["reason"]
    floor_tiers = list(TIER_FLOOR_POLICY[band]["floor_tiers"])
    registry_tiers, registered = _registry_requirements(claim_kind)
    if not registered:
        floor_tiers = list(TIER_FLOOR_POLICY["UNKNOWN_STRICTEST"]["floor_tiers"])
        band = "UNKNOWN_STRICTEST"
        reason = f"claim kind {claim_kind!r} is unregistered; strictest floor applies"

    effective = list(registry_tiers)
    for tier in floor_tiers:
        if tier not in effective:
            effective.append(tier)
    effective.sort(key=TIER_ORDER.index)
    if not set(registry_tiers).issubset(effective):
        raise AssertionError("producer floor removed a tier required by gate_registry")
    return {
        "claim_kind": claim_kind,
        "claim_kind_registered": registered,
        "producer": producer,
        "registry_tiers": registry_tiers,
        "floor_tiers": floor_tiers,
        "effective_tiers": effective,
        "standing_band": band,
        "reason": reason,
    }


def required_tiers(
    claim_kind: str, producer: str, ledger: str | Path = DEFAULT_LEDGER
) -> list[str]:
    """Return the order-preserving registry-plus-floor union."""
    return floor_detail(claim_kind, producer, ledger)["effective_tiers"]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only ClaimGate producer standing")
    sub = parser.add_subparsers(dest="command", required=True)
    standing = sub.add_parser("standing")
    standing.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    standing.add_argument("--root", type=Path, default=REPO_ROOT)
    floor = sub.add_parser("floor")
    floor.add_argument("--claim-kind", required=True)
    floor.add_argument("--producer", required=True)
    floor.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    floor.add_argument("--root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "standing":
            body = compute_standings(args.ledger, args.root)
        else:
            body = floor_detail(
                args.claim_kind, args.producer, args.ledger, args.root
            )
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"producer_standing: infra failure: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(body, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
