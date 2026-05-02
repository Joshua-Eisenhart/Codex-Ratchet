#!/usr/bin/env python3
"""Reconcile queue DONE rows against result receipts and ledger loopback.

This is a controller-side admission check.  It does not run sims, mutate queues,
or update the ledger.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from receipt_schema import (
    load_json,
    make_report,
    relpath,
    repo_root,
    result_dir,
    summary_all_pass,
    validate_result_path,
)


DONE_RE = re.compile(r"^#\s*(DONE|FAIL)\s+(\S+)\s+([A-Za-z0-9_./-]+)")
AS_PROBE_RE = re.compile(r"\bas\s+(sim_[A-Za-z0-9_]+)\b")
TODO_RE = re.compile(r"^#\s*TODO\s+(.+)$")
PACKET_START_RE = re.compile(r"^#\s*(MICRO|INTEGRATION_MICRO|BOUND):\s*(.*)$")

MICRO_REQUIRED_FIELDS = {
    "tool_target",
    "function_surface",
    "micro_claim",
    "lego_target",
    "function_receipt",
    "prior_function_receipts",
    "why_this_lego",
    "positive_case",
    "negative_case",
    "boundary_case",
    "demotion_condition",
    "out_of_scope",
}

BOUND_REQUIRED_FIELDS = {
    "tool_target",
    "integration_question",
    "anchor_lego",
    "why_this_lego",
    "loopback_target",
    "expected_outcome_classification",
    "bound_exit_condition",
    "out_of_scope",
}


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--queue",
        action="append",
        default=None,
        help="Queue file to inspect. Defaults to Tier A and Tier A second wave.",
    )
    parser.add_argument(
        "--ledger",
        default=str(
            root
            / "system_v5"
            / "docs"
            / "plans"
            / "plans"
            / "TOOL_CAPABILITY_AND_INTEGRATION_LEDGER.md"
        ),
        help="Ledger markdown file used for loopback text checks.",
    )
    parser.add_argument(
        "--stage-gate",
        default=str(root / "system_v5" / "ops" / "stage_gate.json"),
        help="Machine-readable stage gate JSON.",
    )
    parser.add_argument(
        "--basename",
        action="append",
        default=[],
        help="Limit reconciliation to a queue basename or result basename. Repeatable.",
    )
    parser.add_argument(
        "--since",
        default=None,
        help="Limit DONE/FAIL rows to timestamps lexically >= this value.",
    )
    parser.add_argument(
        "--strict-scope",
        action="store_true",
        help="Require receipt scope ceiling fields as hard gates.",
    )
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help="Return nonzero when any selected row has a hard finding.",
    )
    return parser.parse_args()


def default_queues(root: Path) -> list[Path]:
    return [
        root / "system_v5" / "ops" / "queue_tier_a.txt",
        root / "system_v5" / "ops" / "queue_tier_a_second_wave.txt",
    ]


def _result_basename(raw_basename: str, line: str) -> str:
    match = AS_PROBE_RE.search(line)
    if match and raw_basename.startswith("int_"):
        return match.group(1)
    return raw_basename.removesuffix(".py").removesuffix("_results.json")


def parse_queue(path: Path, root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return [{
            "queue": relpath(path, root),
            "kind": "missing_queue",
            "hard_findings": [{"kind": "missing_queue", "severity": "hard"}],
        }]

    packet_pending: dict[str, Any] | None = None
    packet_kind: str | None = None
    packet_start_line: int | None = None
    packet_lines: list[str] = []

    def finish_packet() -> None:
        nonlocal packet_pending, packet_kind, packet_start_line, packet_lines
        text = "\n".join(packet_lines)
        parsed = None
        error = None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            error = f"{exc.__class__.__name__}: {exc}"
        packet_pending = {
            "type": packet_kind,
            "line": packet_start_line,
            "payload": parsed,
            "parse_error": error,
        }
        packet_kind = None
        packet_start_line = None
        packet_lines = []

    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        packet_start = PACKET_START_RE.match(line)
        if packet_start:
            packet_kind = packet_start.group(1)
            packet_start_line = lineno
            packet_lines = [packet_start.group(2)]
            if packet_start.group(2).strip().endswith("}"):
                finish_packet()
            continue

        if packet_kind is not None:
            content = line[1:].lstrip() if line.startswith("#") else line
            packet_lines.append(content)
            if content.strip().endswith("}"):
                finish_packet()
            continue

        done = DONE_RE.match(line)
        if done:
            status, timestamp, raw_basename = done.groups()
            rows.append({
                "queue": relpath(path, root),
                "line": lineno,
                "status": status,
                "timestamp": timestamp,
                "basename": raw_basename,
                "result_basename": _result_basename(raw_basename, line),
                "raw": line,
                "packet": packet_pending,
            })
            packet_pending = None
            continue
        todo = TODO_RE.match(line)
        if todo:
            rows.append({
                "queue": relpath(path, root),
                "line": lineno,
                "status": "TODO",
                "basename": todo.group(1).strip(),
                "result_basename": None,
                "raw": line,
                "packet": packet_pending,
            })
            packet_pending = None
    return rows


def selected(row: dict[str, Any], basenames: set[str], since: str | None) -> bool:
    if row.get("kind") == "missing_queue":
        return True
    if row.get("status") not in {"DONE", "FAIL"}:
        return False
    timestamp = row.get("timestamp")
    if since and isinstance(timestamp, str) and timestamp < since:
        return False
    if not basenames:
        return True
    names = {str(row.get("basename")), str(row.get("result_basename"))}
    return bool(names & basenames)


def read_text_or_empty(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def load_stage_gate(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}
    return {
        "ok": True,
        "active_stage": payload.get("active_stage"),
        "allow_default_queue_late_stage": payload.get("allow_default_queue_late_stage"),
        "allow_tier_d_launch": payload.get("allow_tier_d_launch"),
    }


def _packet_required_fields(packet_type: str | None) -> set[str]:
    if packet_type == "BOUND":
        return BOUND_REQUIRED_FIELDS
    if packet_type in {"MICRO", "INTEGRATION_MICRO"}:
        return MICRO_REQUIRED_FIELDS
    return set()


def _field_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0
    return False


def _declared_prior_paths(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [str(path) for path in value.values()]
    if isinstance(value, list):
        return [str(path) for path in value]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _resolve_prior(path_text: str, root: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    candidate = root / path
    if candidate.exists():
        return candidate
    if "/" not in path_text and not path_text.endswith("_results.json"):
        return result_dir(root) / f"{path_text}_results.json"
    return candidate


def reconcile_packet(
    packet: dict[str, Any] | None,
    *,
    root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    facts: dict[str, Any] = {"packet_type": None, "packet_line": None, "packet_prior_receipts": []}
    hard_findings: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if not packet:
        warnings.append({"kind": "missing_queue_packet", "severity": "warning"})
        return facts, hard_findings, warnings

    packet_type = packet.get("type")
    facts["packet_type"] = packet_type
    facts["packet_line"] = packet.get("line")
    parse_error = packet.get("parse_error")
    payload = packet.get("payload")
    if parse_error:
        hard_findings.append(
            {"kind": "malformed_queue_packet_json", "severity": "hard", "error": parse_error}
        )
        return facts, hard_findings, warnings
    if not isinstance(payload, dict):
        hard_findings.append(
            {"kind": "queue_packet_non_object", "severity": "hard", "packet_type": packet_type}
        )
        return facts, hard_findings, warnings

    for field in sorted(_packet_required_fields(str(packet_type))):
        if field not in payload:
            hard_findings.append(
                {
                    "kind": "queue_packet_required_field_empty",
                    "severity": "hard",
                    "packet_type": packet_type,
                    "field": field,
                }
            )
        elif field != "prior_function_receipts" and _field_empty(payload.get(field)):
            hard_findings.append(
                {
                    "kind": "queue_packet_required_field_empty",
                    "severity": "hard",
                    "packet_type": packet_type,
                    "field": field,
                }
            )

    declared_priors = _declared_prior_paths(payload.get("prior_function_receipts"))
    if not declared_priors and payload.get("function_receipt") != "new":
        hard_findings.append(
            {
                "kind": "queue_packet_prior_receipts_empty_without_new_receipt",
                "severity": "hard",
                "packet_type": packet_type,
            }
        )

    for declared in declared_priors:
        if declared == "new":
            continue
        resolved = _resolve_prior(declared, root)
        prior_fact: dict[str, Any] = {
            "declared": declared,
            "path": relpath(resolved, root),
            "exists": resolved.exists(),
            "all_pass": None,
            "classification": None,
        }
        facts["packet_prior_receipts"].append(prior_fact)
        if not resolved.exists():
            hard_findings.append(
                {
                    "kind": "queue_packet_prior_receipt_missing",
                    "severity": "hard",
                    "prior": declared,
                }
            )
            continue
        try:
            prior_payload = load_json(resolved)
        except (OSError, json.JSONDecodeError) as exc:
            hard_findings.append(
                {
                    "kind": "queue_packet_prior_receipt_unreadable",
                    "severity": "hard",
                    "prior": relpath(resolved, root),
                    "error": f"{exc.__class__.__name__}: {exc}",
                }
            )
            continue
        if not isinstance(prior_payload, dict):
            hard_findings.append(
                {
                    "kind": "queue_packet_prior_receipt_non_object",
                    "severity": "hard",
                    "prior": relpath(resolved, root),
                }
            )
            continue
        prior_fact["all_pass"] = summary_all_pass(prior_payload)
        prior_fact["classification"] = prior_payload.get("classification")
        if prior_fact["all_pass"] is not True:
            hard_findings.append(
                {
                    "kind": "queue_packet_prior_receipt_not_all_pass",
                    "severity": "hard",
                    "prior": relpath(resolved, root),
                }
            )
        if prior_fact["classification"] != "canonical":
            hard_findings.append(
                {
                    "kind": "queue_packet_prior_receipt_not_canonical",
                    "severity": "hard",
                    "prior": relpath(resolved, root),
                    "classification": prior_fact["classification"],
                }
            )

    return facts, hard_findings, warnings


def reconcile_row(
    row: dict[str, Any],
    *,
    root: Path,
    ledger_text: str,
    strict_scope: bool,
) -> dict[str, Any]:
    hard_findings: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    result_basename = row.get("result_basename")
    if row.get("kind") == "missing_queue":
        hard = row.get("hard_findings", [{"kind": "missing_queue", "severity": "hard"}])
        return {
            "facts": {"queue": row.get("queue"), "status": "MISSING_QUEUE"},
            "hard_findings": hard,
            "warnings": [],
            "ok": False,
        }

    result_path = result_dir(root) / f"{result_basename}_results.json"

    facts = {
        "queue": row.get("queue"),
        "line": row.get("line"),
        "status": row.get("status"),
        "timestamp": row.get("timestamp"),
        "basename": row.get("basename"),
        "result_basename": result_basename,
        "result_json": relpath(result_path, root),
        "ledger_loopback_present": False,
    }
    packet_facts, packet_hard, packet_warnings = reconcile_packet(row.get("packet"), root=root)
    facts.update(packet_facts)
    hard_findings.extend(packet_hard)
    warnings.extend(packet_warnings)

    if row.get("status") == "FAIL":
        hard_findings.append({"kind": "queue_row_failed", "severity": "hard"})
        return {"facts": facts, "hard_findings": hard_findings, "warnings": warnings, "ok": False}

    if not result_path.exists():
        hard_findings.append(
            {"kind": "missing_result_json_for_done_row", "severity": "hard"}
        )
        return {"facts": facts, "hard_findings": hard_findings, "warnings": warnings, "ok": False}

    receipt = validate_result_path(result_path, root=root, strict_scope=strict_scope)
    hard_findings.extend(receipt.get("hard_findings", []))
    warnings.extend(receipt.get("warnings", []))
    facts.update(receipt.get("facts", {}))

    ledger_needles = {
        str(row.get("basename") or ""),
        str(result_basename or ""),
        str(result_path.name),
    }
    raw_basename = str(row.get("basename") or "")
    result_name = str(result_basename or "")
    alias_used = bool(raw_basename and result_name and raw_basename != result_name)
    facts["alias_used"] = alias_used
    if alias_used:
        facts["ledger_loopback_present"] = (
            raw_basename in ledger_text
            and (result_name in ledger_text or result_path.name in ledger_text)
        )
        facts["ledger_row_name_present"] = raw_basename in ledger_text
    else:
        facts["ledger_loopback_present"] = any(
            needle and needle in ledger_text for needle in ledger_needles
        )
        facts["ledger_row_name_present"] = facts["ledger_loopback_present"]
    if not facts["ledger_loopback_present"]:
        hard_findings.append(
            {
                "kind": "ledger_loopback_missing",
                "severity": "hard",
                "needles": sorted(needle for needle in ledger_needles if needle),
            }
        )
    elif not facts["ledger_row_name_present"]:
        hard_findings.append(
            {
                "kind": "ledger_row_name_missing",
                "severity": "hard",
                "needles": sorted(needle for needle in required_ledger_needles if needle),
            }
        )

    return {
        "facts": facts,
        "hard_findings": hard_findings,
        "warnings": warnings,
        "ok": not hard_findings,
    }


def main() -> int:
    args = parse_args()
    root = repo_root()
    queues = [Path(q) for q in args.queue] if args.queue else default_queues(root)
    ledger_path = Path(args.ledger)
    stage_gate_path = Path(args.stage_gate)
    ledger_text = read_text_or_empty(ledger_path)

    rows: list[dict[str, Any]] = []
    for queue in queues:
        rows.extend(parse_queue(queue, root))

    basenames = set(args.basename)
    selected_rows = [row for row in rows if selected(row, basenames, args.since)]

    records = [
        reconcile_row(row, root=root, ledger_text=ledger_text, strict_scope=args.strict_scope)
        for row in selected_rows
    ]
    report = make_report(records)
    report.update({
        "queues": [relpath(path, root) for path in queues],
        "ledger": relpath(ledger_path, root),
        "stage_gate": load_stage_gate(stage_gate_path),
        "selected_rows": len(selected_rows),
        "pending_todos": [row for row in rows if row.get("status") == "TODO"],
    })

    if basenames:
        missing = sorted(basenames - {
            str(row.get("basename")) for row in selected_rows
        } - {
            str(row.get("result_basename")) for row in selected_rows
        })
        if missing:
            report["hard_finding_count"] += len(missing)
            report["all_pass"] = False
            report.setdefault("selection_findings", []).extend(
                {"kind": "requested_basename_not_found", "basename": item}
                for item in missing
            )

    print(json.dumps(report, indent=2, sort_keys=True))
    if args.require_clean:
        return 0 if report["all_pass"] else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
