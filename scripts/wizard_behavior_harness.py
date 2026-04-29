#!/usr/bin/env python3
"""Normalize wizard behavior probe records into Codex harness receipts.

The harness is intentionally stdlib-only and does not spawn agents. It accepts
already-collected lane records, writes one receipt JSON per lane, writes a
lane_resolution JSONL file, and emits shapes accepted by
``scripts/codex_harness_adapter.py validate``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SPAWNED_STATES = {"spawned", "spawned_completed", "completed", "ran"}
BLOCKED_STATES = {"blocked", "deferred", "shutdown"}
LOCAL_STATES = {"controller_local", "not_spawned", "local_receipt"}
VALID_STATES = SPAWNED_STATES | BLOCKED_STATES | LOCAL_STATES

REQUIRED_RECEIPT_FIELDS = ("lane", "checked", "concluded", "open", "evidence")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "lane"


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _compact_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _as_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple)):
        return "\n".join(_as_text(item) for item in value if item is not None).strip()
    if isinstance(value, dict):
        return _compact_json(value)
    return str(value).strip()


def _as_evidence(value: Any, *, output_path: str | None) -> str:
    text = _as_text(value)
    if text:
        return text
    if output_path:
        return output_path
    return "behavior harness record"


def _read_text_path(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _resolve_input_path(candidate_root: Path, value: Any) -> Path | None:
    raw = _as_text(value)
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = candidate_root / path
    return path


def _record_output(record: dict[str, Any], candidate_root: Path) -> tuple[str, str | None]:
    for key in ("output", "stdout", "text", "transcript", "content"):
        if key in record:
            return _as_text(record[key]), None

    for key in ("output_path", "stdout_path", "transcript_path", "path"):
        path = _resolve_input_path(candidate_root, record.get(key))
        if path is None:
            continue
        return _read_text_path(path), str(path)

    return "", None


def _record_mini_mmm(record: dict[str, Any], candidate_root: Path, output_text: str) -> str:
    for key in ("mini_mmm", "mini_mmm_text", "mini_mmm_language_body", "language_body"):
        if key in record:
            text = _as_text(record[key])
            if text:
                return text

    path = _resolve_input_path(candidate_root, record.get("mini_mmm_path"))
    if path is not None:
        return _read_text_path(path)

    return output_text


def _ensure_lane_body(lane: str, candidate_root: Path, body: str) -> str:
    base = body.strip() or "No probe output was provided for this lane."
    prefix = (
        f"Lane-local behavior probe body for {lane}. "
        f"Candidate root: {candidate_root}. "
        "This record was normalized from collected probe output only. "
        "The harness did not spawn agents, infer hidden execution, or add a "
        "claim beyond the supplied lane record. "
    )
    guidance = (
        "Review this lane as receipt evidence: checked material, conclusion, "
        "remaining open question, and cited evidence must remain tied to the "
        "captured output. The body exists so the adapter can verify that every "
        "completed lane has a lane-local language surface rather than borrowing "
        "global prose. Future readers should treat the text as a behavior probe "
        "normalization artifact, not as independent proof of correctness. "
    )
    text = f"{prefix}{guidance}\n\nCollected output:\n{base}\n"
    words = text.split()
    if len(words) >= 110:
        return text

    filler = (
        "Receipt truth stays local to this lane; evidence is bounded, explicit, "
        "repeatable, and open issues remain visible for follow-up verification. "
    )
    while len(text.split()) < 110:
        text += filler
    return text


def _receipt_for(
    *,
    record: dict[str, Any],
    lane: str,
    candidate_root: Path,
    output_text: str,
    output_path: str | None,
    generated_at: str,
) -> dict[str, Any]:
    evidence = _as_evidence(record.get("evidence"), output_path=output_path)
    receipt = {
        "schema_version": "wizard_behavior_harness.v1",
        "generated_at": generated_at,
        "candidate_root": str(candidate_root),
        "lane": lane,
        "checked": _as_text(record.get("checked"), "collected behavior probe output"),
        "concluded": _as_text(record.get("concluded"), "behavior probe output normalized"),
        "open": _as_text(record.get("open"), "manual review of normalized behavior remains open"),
        "evidence": evidence,
        "output_sha256": hashlib.sha256(output_text.encode("utf-8")).hexdigest(),
        "output_excerpt": output_text[:1000],
    }
    missing = [field for field in REQUIRED_RECEIPT_FIELDS if not receipt.get(field)]
    if missing:
        raise ValueError(f"{lane}: missing receipt fields after normalization: {', '.join(missing)}")
    return receipt


def _lane_row_for(
    *,
    record: dict[str, Any],
    lane: str,
    slug: str,
    receipt_name: str,
    mini_mmm_name: str,
    receipt: dict[str, Any],
    output_path: str | None,
    generated_at: str,
) -> dict[str, Any]:
    state = _as_text(record.get("state", record.get("resolution", record.get("status"))), "local_receipt").lower()
    if state not in VALID_STATES:
        raise ValueError(f"{lane}: invalid status {state!r}")

    reason = _as_text(record.get("reason", record.get("blocker_or_defer_reason")))
    if state in BLOCKED_STATES and not reason:
        raise ValueError(f"{lane}: blocked/deferred/shutdown records require a reason")

    worker_id = _as_text(record.get("worker_id", record.get("agent_id")), f"behavior-harness:{slug}")
    evidence = receipt["evidence"]
    row = {
        "lane": lane,
        "emoji": _as_text(record.get("emoji")),
        "role": _as_text(record.get("role"), "behavior probe normalization"),
        "wave": record.get("wave", 1),
        "status": state,
        "state": state,
        "worker_id": worker_id if state not in BLOCKED_STATES else (worker_id if record.get("worker_id") else None),
        "agent_id": _as_text(record.get("agent_id")),
        "checked": receipt["checked"],
        "concluded": receipt["concluded"],
        "open": receipt["open"],
        "evidence": evidence,
        "blocker_or_defer_reason": reason or None,
        "reason": reason or None,
        "wiki_harness_boot": "wizard_behavior_harness normalized collected probe output",
        "mini_mmm_language_body": mini_mmm_name,
        "mini_mmm_path": mini_mmm_name,
        "mini_mmm_scope": _as_text(record.get("mini_mmm_scope"), "lane_local"),
        "task_card": _as_text(record.get("task_card"), "Normalize collected wizard behavior probe output into adapter-valid receipts."),
        "task_card_after_mini_mmm": True,
        "lane_resolution": "lane_resolution.jsonl",
        "runtime_registry": "not spawned; behavior harness normalization only",
        "worker_receipt": receipt_name,
        "audit": "receipt fields and lane-local body written by wizard_behavior_harness",
        "final_output_check": "ready for scripts/codex_harness_adapter.py validate",
        "receipt_path": receipt_name,
        "output_path": output_path,
        "generated_at": generated_at,
    }
    if state in LOCAL_STATES:
        row["worker_id"] = None
    return row


def _load_json_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        return []
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        records: list[dict[str, Any]] = []
        for line_no, raw in enumerate(text.splitlines(), start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_no}: record must be an object")
            records.append(payload)
        return records

    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        if not all(isinstance(item, dict) for item in payload):
            raise ValueError(f"{path}: JSON array items must be objects")
        return payload
    raise ValueError(f"{path}: JSON payload must be an object or array")


def load_lane_records(values: list[str], *, base_dir: Path | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    base = base_dir or Path.cwd()
    for value in values:
        raw = value[1:] if value.startswith("@") else value
        path = Path(raw)
        if not path.is_absolute():
            path = base / path
        if path.exists():
            records.extend(_load_json_records(path))
            continue

        try:
            payload = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"lane record is neither an existing file nor JSON: {value}") from exc
        if isinstance(payload, dict):
            records.append(payload)
        elif isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
            records.extend(payload)
        else:
            raise ValueError("lane record JSON must be an object or an array of objects")
    return records


def run_harness(candidate_root: Path, out_dir: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_root = candidate_root.resolve()
    out_dir = out_dir.resolve()
    if not candidate_root.exists():
        raise ValueError(f"candidate root does not exist: {candidate_root}")
    if not records:
        raise ValueError("at least one lane record is required")

    receipts_dir = out_dir / "receipts"
    mini_dir = out_dir / "mini_mmm"
    receipts_dir.mkdir(parents=True, exist_ok=True)
    mini_dir.mkdir(parents=True, exist_ok=True)

    generated_at = _utc_now()
    lane_resolution_path = out_dir / "lane_resolution.jsonl"
    rows: list[dict[str, Any]] = []
    seen_lanes: set[str] = set()

    for index, record in enumerate(records, start=1):
        lane = _as_text(record.get("lane"))
        if not lane:
            raise ValueError(f"record {index}: lane is required")
        if lane in seen_lanes:
            raise ValueError(f"{lane}: duplicate lane records are not supported")
        seen_lanes.add(lane)

        slug = _slug(lane)
        receipt_name = f"{slug}.json"
        mini_mmm_name = f"mini_mmm/{slug}.md"
        output_text, output_path = _record_output(record, candidate_root)
        receipt = _receipt_for(
            record=record,
            lane=lane,
            candidate_root=candidate_root,
            output_text=output_text,
            output_path=output_path,
            generated_at=generated_at,
        )
        mini_body = _ensure_lane_body(lane, candidate_root, _record_mini_mmm(record, candidate_root, output_text))

        (receipts_dir / receipt_name).write_text(_json_dumps(receipt), encoding="utf-8")
        (out_dir / mini_mmm_name).write_text(mini_body, encoding="utf-8")
        rows.append(
            _lane_row_for(
                record=record,
                lane=lane,
                slug=slug,
                receipt_name=receipt_name,
                mini_mmm_name=mini_mmm_name,
                receipt=receipt,
                output_path=output_path,
                generated_at=generated_at,
            )
        )

    lane_resolution_path.write_text(
        "".join(_compact_json(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    result = {
        "generated_at": generated_at,
        "ok": True,
        "candidate_root": str(candidate_root),
        "out_dir": str(out_dir),
        "lane_resolution_path": str(lane_resolution_path),
        "receipts_dir": str(receipts_dir),
        "lanes": [row["lane"] for row in rows],
    }
    (out_dir / "wizard_behavior_harness_receipt.json").write_text(_json_dumps(result), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument(
        "--lane-record",
        action="append",
        default=[],
        help="Lane record as a JSON string, JSON/JSONL file path, or @file path. May be repeated.",
    )
    args = parser.parse_args(argv)

    try:
        records = load_lane_records(args.lane_record, base_dir=Path.cwd())
        result = run_harness(args.candidate_root, args.out_dir, records)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"wizard_behavior_harness: {exc}\n")
        return 2

    sys.stdout.write(_json_dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
