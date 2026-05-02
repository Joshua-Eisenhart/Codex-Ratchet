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


DONE_RE = re.compile(r"^#\s*(DONE|LEDGER_DONE|FAIL|SKIPPED|INELIGIBLE)\s+(\S+)\s+([A-Za-z0-9_./-]+)")
AS_PROBE_RE = re.compile(r"\bas\s+(sim_[A-Za-z0-9_]+)\b")
TODO_RE = re.compile(r"^#\s*TODO\s+(.+)$")
PACKET_START_RE = re.compile(r"^#\s*(MICRO|INTEGRATION_MICRO|BOUND):\s*(.*)$")
EXECUTABLE_TERMINAL_STATUSES = {"DONE", "FAIL", "SKIPPED", "INELIGIBLE"}
TERMINAL_STATUSES = EXECUTABLE_TERMINAL_STATUSES | {"LEDGER_DONE"}

QUEUE_PRESETS = {
    "tier-a": (
        "system_v5/ops/queue_tier_a.txt",
        "system_v5/ops/queue_tier_a_second_wave.txt",
    ),
    "all-c": (
        "system_v5/ops/queue_tier_a.txt",
        "system_v5/ops/queue_tier_a_second_wave.txt",
        "system_v5/ops/queue_tier_b.txt",
    ),
}

CURRENT_RECEIPT_CONTRACT_START = "2026-05-01"

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

MICRO_RUN_BOUNDARY_FIELDS = {
    "claim_ceiling",
    "next_lego_target",
    "promotion_condition",
    "blocked_until",
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

LEDGER_ONLY_PREFIXES = ("cap_rerun_", "manifest_repair_")

STAGE_ORDER = ["tools", "tool_integration", "lego", "coupling"]

CLAIM_TERM_RULES = {
    "bridge": (r"\bbridge(?:[- ]level)?(?:\s+claim|\s+readiness|\s+promotion)?\b",),
    "axis": (r"\baxis[- ]level\b", r"\baxis\s+claim\b", r"\baxis\s+promotion\b"),
    "engine": (r"\bengine[- ]level\b", r"\bengine\s+claim\b", r"\bengine\s+promotion\b"),
    "emergence": (r"\bemergence\b", r"\bemergent\b"),
    "scientific_coupling": (r"\bscientific\s+coupling\b",),
    "tier_d": (r"\btier[- _]d\b",),
}

CLAIM_SCAN_FIELDS = (
    "micro_claim",
    "why_this_lego",
    "positive_case",
    "function_surface",
    "integration_question",
    "bound_exit_condition",
)


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--queue",
        action="append",
        default=None,
        help="Queue file to inspect. Defaults to the selected queue preset.",
    )
    parser.add_argument(
        "--queue-preset",
        choices=sorted(QUEUE_PRESETS),
        default="tier-a",
        help="Queue preset to inspect when --queue is not provided.",
    )
    parser.add_argument(
        "--include-blocked-tier-d",
        action="store_true",
        help="Include Tier D queue rows in addition to the selected preset. Tier D remains blocked by stage gate unless explicitly allowed.",
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
        "--include-legacy",
        action="store_true",
        help="Include rows before the current receipt-contract window.",
    )
    parser.add_argument(
        "--include-superseded",
        action="store_true",
        help="Include older DONE/FAIL rows for the same queue item instead of checking only the latest terminal row.",
    )
    parser.add_argument(
        "--strict-scope",
        action="store_true",
        help="Require receipt scope ceiling fields as hard gates.",
    )
    parser.add_argument(
        "--require-run-boundary",
        action="store_true",
        help="Require claim_ceiling, next_lego_target, promotion_condition, and blocked_until in receipts and MICRO packets.",
    )
    parser.add_argument(
        "--require-executable-receipt",
        action="store_true",
        help="Fail ledger-only rows and supporting/audit JSON when executable sim evidence is required.",
    )
    parser.add_argument(
        "--include-ledger-done",
        action="store_true",
        help="Inspect LEDGER_DONE rows. They remain non-executable and fail executable receipt mode.",
    )
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help="Return nonzero when any selected row has a hard finding.",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow a strict clean run to pass even when no rows were selected.",
    )
    return parser.parse_args()


def default_queues(root: Path) -> list[Path]:
    return preset_queues(root, "tier-a", include_blocked_tier_d=False)


def preset_queues(
    root: Path,
    preset: str,
    *,
    include_blocked_tier_d: bool,
) -> list[Path]:
    queue_texts = list(QUEUE_PRESETS[preset])
    if include_blocked_tier_d:
        queue_texts.append("system_v5/ops/queue_tier_d.txt")
    return [root / queue for queue in queue_texts]


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


def selected(
    row: dict[str, Any],
    basenames: set[str],
    since: str | None,
    *,
    include_legacy: bool,
    include_ledger_done: bool = False,
) -> bool:
    if row.get("kind") == "missing_queue":
        return True
    status = row.get("status")
    if status == "LEDGER_DONE" and not include_ledger_done:
        return False
    if status not in TERMINAL_STATUSES:
        return False
    timestamp = row.get("timestamp")
    lower_bound = since
    if not lower_bound and not basenames and not include_legacy:
        lower_bound = CURRENT_RECEIPT_CONTRACT_START
    if lower_bound and isinstance(timestamp, str) and timestamp < lower_bound:
        return False
    if not basenames:
        return True
    names = {str(row.get("basename")), str(row.get("result_basename"))}
    return bool(names & basenames)


def latest_terminal_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    passthrough: list[dict[str, Any]] = []
    for row in rows:
        if row.get("kind") == "missing_queue":
            passthrough.append(row)
            continue
        key = (str(row.get("queue") or ""), str(row.get("basename") or ""))
        previous = latest.get(key)
        if previous is None or str(row.get("timestamp") or "") >= str(previous.get("timestamp") or ""):
            latest[key] = row
    return passthrough + list(latest.values())


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


def stage_index(stage: Any) -> int:
    try:
        return STAGE_ORDER.index(str(stage))
    except ValueError:
        return -1


def _stage_allows_claim(stage_gate: dict[str, Any], claim: str) -> bool:
    if not stage_gate.get("ok"):
        return False
    if claim == "tier_d":
        return stage_gate.get("allow_tier_d_launch") is True
    return stage_index(stage_gate.get("active_stage")) >= stage_index("coupling")


def _match_unblocked_claim(text: str, pattern: str) -> bool:
    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
        prefix = text[max(0, match.start() - 48):match.start()].lower()
        if re.search(r"\b(no|not|without|exclude|excludes|excluded|blocking|blocked)\b", prefix):
            continue
        if "out of scope" in prefix or "must not" in prefix or "do not" in prefix:
            continue
        return True
    return False


def _packet_required_fields(packet_type: str | None, *, require_run_boundary: bool) -> set[str]:
    if packet_type == "BOUND":
        return BOUND_REQUIRED_FIELDS
    if packet_type in {"MICRO", "INTEGRATION_MICRO"}:
        fields = set(MICRO_REQUIRED_FIELDS)
        if require_run_boundary:
            fields.update(MICRO_RUN_BOUNDARY_FIELDS)
        return fields
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


def _ledger_only_work_item(raw_basename: str) -> str | None:
    for prefix in LEDGER_ONLY_PREFIXES:
        if raw_basename.startswith(prefix):
            return raw_basename.removeprefix(prefix)
    return None


def reconcile_packet(
    packet: dict[str, Any] | None,
    *,
    root: Path,
    require_run_boundary: bool,
    stage_gate: dict[str, Any],
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
    facts["packet_run_boundary"] = {
        field: payload.get(field)
        for field in sorted(MICRO_RUN_BOUNDARY_FIELDS)
        if isinstance(payload.get(field), str) and payload.get(field).strip()
    }

    for field in sorted(
        _packet_required_fields(
            str(packet_type),
            require_run_boundary=require_run_boundary,
        )
    ):
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

    claim_texts = {
        field: str(payload.get(field) or "")
        for field in CLAIM_SCAN_FIELDS
        if not _field_empty(payload.get(field))
    }
    for field, text in claim_texts.items():
        folded = text.lower()
        for claim, patterns in CLAIM_TERM_RULES.items():
            if any(_match_unblocked_claim(folded, pattern) for pattern in patterns) and not _stage_allows_claim(stage_gate, claim):
                hard_findings.append(
                    {
                        "kind": "claim_ceiling_violation",
                        "severity": "hard",
                        "packet_type": packet_type,
                        "field": field,
                        "claim": claim,
                        "active_stage": stage_gate.get("active_stage"),
                    }
                )

    coupling_text = " ".join(claim_texts.values()).lower()
    if "coupling" in coupling_text and not declared_priors:
        hard_findings.append(
            {
                "kind": "claim_language_requires_prior_receipts",
                "severity": "hard",
                "packet_type": packet_type,
                "claim": "coupling",
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
    require_run_boundary: bool,
    require_executable_receipt: bool,
    stage_gate: dict[str, Any],
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
    packet_facts, packet_hard, packet_warnings = reconcile_packet(
        row.get("packet"),
        root=root,
        require_run_boundary=require_run_boundary,
        stage_gate=stage_gate,
    )
    facts.update(packet_facts)
    hard_findings.extend(packet_hard)
    warnings.extend(packet_warnings)

    raw_basename = str(row.get("basename") or "")
    result_name = str(result_basename or "")
    if row.get("status") in {"FAIL", "SKIPPED", "INELIGIBLE"}:
        status_kind = {
            "FAIL": "queue_row_failed",
            "SKIPPED": "queue_row_skipped",
            "INELIGIBLE": "queue_row_ineligible",
        }[str(row.get("status"))]
        hard_findings.append({"kind": status_kind, "severity": "hard"})
        return {"facts": facts, "hard_findings": hard_findings, "warnings": warnings, "ok": False}

    ledger_only_tool = _ledger_only_work_item(raw_basename)
    if ledger_only_tool:
        facts["ledger_only_work_item"] = True
        facts["ledger_only_tool"] = ledger_only_tool
        facts["executable_receipt"] = False
        facts["receipt_class"] = "ledger_only"
        exact_loopback = raw_basename in ledger_text
        tool_row_loopback = f"**{ledger_only_tool}**" in ledger_text
        facts["ledger_loopback_present"] = exact_loopback or tool_row_loopback
        facts["ledger_row_name_present"] = facts["ledger_loopback_present"]
        if require_executable_receipt:
            hard_findings.append(
                {
                    "kind": "ledger_only_not_executable_receipt",
                    "severity": "hard",
                    "basename": raw_basename,
                }
            )
        if not facts["ledger_loopback_present"]:
            hard_findings.append(
                {
                    "kind": "ledger_loopback_missing",
                    "severity": "hard",
                    "needles": [raw_basename, f"**{ledger_only_tool}**"],
                }
            )
        return {
            "facts": facts,
            "hard_findings": hard_findings,
            "warnings": warnings,
            "ok": not hard_findings,
        }

    if not result_path.exists():
        hard_findings.append(
            {"kind": "missing_result_json_for_done_row", "severity": "hard"}
        )
        return {"facts": facts, "hard_findings": hard_findings, "warnings": warnings, "ok": False}

    receipt = validate_result_path(
        result_path,
        root=root,
        strict_scope=strict_scope,
        require_executable=require_executable_receipt,
        require_run_boundary=require_run_boundary,
    )
    hard_findings.extend(receipt.get("hard_findings", []))
    warnings.extend(receipt.get("warnings", []))
    receipt_facts = receipt.get("facts", {})
    packet_run_boundary = facts.get("packet_run_boundary")
    if require_run_boundary and isinstance(packet_run_boundary, dict):
        for field, packet_value in sorted(packet_run_boundary.items()):
            receipt_value = receipt_facts.get(field)
            if (
                isinstance(packet_value, str)
                and packet_value.strip()
                and isinstance(receipt_value, str)
                and receipt_value.strip()
                and receipt_value != packet_value
            ):
                hard_findings.append(
                    {
                        "kind": "run_boundary_packet_result_mismatch",
                        "severity": "hard",
                        "field": field,
                        "packet_value": packet_value,
                        "result_value": receipt_value,
                    }
                )
    facts.update(receipt_facts)

    ledger_needles = {
        str(row.get("basename") or ""),
        str(result_basename or ""),
        str(result_path.name),
    }
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
                "needles": sorted(
                    needle for needle in (raw_basename, result_name) if needle
                ),
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
    if args.queue:
        queues = [Path(q) for q in args.queue]
        queue_preset = "custom"
    else:
        queues = preset_queues(
            root,
            args.queue_preset,
            include_blocked_tier_d=args.include_blocked_tier_d,
        )
        queue_preset = args.queue_preset
    ledger_path = Path(args.ledger)
    stage_gate_path = Path(args.stage_gate)
    ledger_text = read_text_or_empty(ledger_path)
    stage_gate = load_stage_gate(stage_gate_path)

    rows: list[dict[str, Any]] = []
    for queue in queues:
        rows.extend(parse_queue(queue, root))

    basenames = set(args.basename)
    selected_rows = [
        row
        for row in rows
        if selected(
            row,
            basenames,
            args.since,
            include_legacy=args.include_legacy,
            include_ledger_done=args.include_ledger_done,
        )
    ]
    if not args.include_superseded:
        selected_rows = latest_terminal_rows(selected_rows)

    records = [
        reconcile_row(
            row,
            root=root,
            ledger_text=ledger_text,
            strict_scope=args.strict_scope,
            require_run_boundary=args.require_run_boundary,
            require_executable_receipt=args.require_executable_receipt,
            stage_gate=stage_gate,
        )
        for row in selected_rows
    ]
    report = make_report(records)
    report.update({
        "queues": [relpath(path, root) for path in queues],
        "queue_preset": queue_preset,
        "include_blocked_tier_d": bool(args.include_blocked_tier_d),
        "ledger": relpath(ledger_path, root),
        "stage_gate": stage_gate,
        "selected_rows": len(selected_rows),
        "include_ledger_done": bool(args.include_ledger_done),
        "include_legacy": bool(args.include_legacy),
        "include_superseded": bool(args.include_superseded),
        "current_receipt_contract_start": CURRENT_RECEIPT_CONTRACT_START,
        "pending_todos": [row for row in rows if row.get("status") == "TODO"],
        "ledger_done_rows": [row for row in rows if row.get("status") == "LEDGER_DONE"],
    })

    if args.require_clean and not selected_rows:
        finding = {
            "kind": "strict_reconcile_selected_no_rows",
            "severity": "warning" if args.allow_empty else "hard",
            "message": "Strict reconciliation did not inspect any terminal queue rows.",
            "allow_empty": bool(args.allow_empty),
            "terminal_rows_available": sum(
                1
                for row in rows
                if row.get("status") in TERMINAL_STATUSES
            ),
        }
        report.setdefault("selection_findings", []).append(finding)
        if not args.allow_empty:
            report["hard_finding_count"] += 1
            report["all_pass"] = False

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
