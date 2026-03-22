"""
outer_session_ledger.py

Bounded Leviathan-derived session durability slice for Ratchet.

This operator does not host or execute an outside runtime. It observes local
session continuity surfaces, emits one repo-held current-state ledger, appends a
small event record, and writes an audit report about resumability.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from system_v4.skills.ratchet_prompt_stack import RATCHET_CATALOG


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SESSIONS_ROOT = "system_v4/a2_state/stack_sessions"
OUTER_SESSION_LEDGER_STATE = "system_v4/a2_state/OUTER_SESSION_LEDGER_STATE__CURRENT__v1.json"
OUTER_SESSION_LEDGER_EVENTS = "system_v4/a2_state/OUTER_SESSION_LEDGER_EVENTS__APPEND_ONLY__v1.jsonl"
OUTER_SESSION_LEDGER_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/OUTER_SESSION_LEDGER_REPORT__CURRENT__v1.json"
)
OUTER_SESSION_LEDGER_REPORT_MD = (
    "system_v4/a2_state/audit_logs/OUTER_SESSION_LEDGER_REPORT__CURRENT__v1.md"
)

DEFAULT_NON_GOALS = [
    "Do not claim FlowMind runtime hosting inside Ratchet.",
    "Do not claim A2 replacement or memory-law replacement.",
    "Do not mutate canonical A2, graph truth, or outside host state.",
    "Do not claim full Leviathan integration from one continuity slice.",
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve_output_path(root: Path, raw: Any, default_rel: str) -> Path:
    if not raw:
        return root / default_rel
    path = Path(str(raw))
    return path if path.is_absolute() else root / path


def _safe_load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _session_files(sessions_root: Path) -> list[Path]:
    if not sessions_root.exists():
        return []
    return sorted(sessions_root.glob("*/session.json"))


def _stack_step_count(stack_id: str) -> int:
    stack = RATCHET_CATALOG.get(stack_id)
    return len(stack.steps) if stack else 0


def _next_step_title(stack_id: str, active_step_index: int) -> str:
    stack = RATCHET_CATALOG.get(stack_id)
    if not stack:
        return ""
    if 0 <= active_step_index < len(stack.steps):
        return stack.steps[active_step_index].title
    return ""


def _session_summary(session_path: Path) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    session = _safe_load_json(session_path)
    if not session:
        return {}, [f"unreadable session payload: {session_path}"]

    session_id = str(session.get("session_id", "")).strip()
    stack_id = str(session.get("stack_id", "")).strip()
    status = str(session.get("status", "")).strip() or "unknown"
    active_step_index = int(session.get("active_step_index", 0) or 0)
    active_step_id = str(session.get("active_step_id", "")).strip()
    completed_step_ids = session.get("completed_step_ids", [])
    receipts = session.get("report_receipts", [])
    manifest_path = str(session.get("manifest_path", "") or "").strip()
    last_receipt = receipts[-1] if isinstance(receipts, list) and receipts else {}

    if not session_id:
        issues.append(f"session missing session_id: {session_path}")
    if not stack_id:
        issues.append(f"session missing stack_id: {session_path}")

    total_steps = _stack_step_count(stack_id)
    resume_supported = bool(active_step_id) and status not in {"completed", "failed"}
    latest_report_path = str(last_receipt.get("report_path", "")).strip()
    latest_report_exists = bool(latest_report_path) and Path(latest_report_path).exists()
    if latest_report_path and not latest_report_exists:
        issues.append(f"latest report path missing on disk: {latest_report_path}")

    checkpoint = {
        "active_step_index": active_step_index,
        "active_step_id": active_step_id,
        "last_receipt_step_id": str(last_receipt.get("step_id", "")).strip(),
        "last_receipt_recorded_at": str(last_receipt.get("recorded_at", "")).strip(),
        "receipt_count": len(receipts) if isinstance(receipts, list) else 0,
    }
    handoff = {
        "summary": (
            f"Session {session_id or '<unknown>'} is {status} at "
            f"{active_step_id or 'no-active-step'}."
        ),
        "next_steps": [active_step_id] if active_step_id else [],
        "next_step_title": _next_step_title(stack_id, active_step_index),
        "blockers": [issue for issue in issues if "missing" in issue or "unreadable" in issue],
    }

    summary = {
        "session_id": session_id,
        "stack_id": stack_id,
        "stack_title": str(session.get("stack_title", "")).strip(),
        "status": status,
        "project_dir": str(session.get("project_dir", "")).strip(),
        "created_at": str(session.get("created_at", "")).strip(),
        "updated_at": str(session.get("updated_at", "")).strip(),
        "current_step_index": active_step_index,
        "current_step_id": active_step_id,
        "total_steps": total_steps,
        "completed_step_count": len(completed_step_ids) if isinstance(completed_step_ids, list) else 0,
        "completed_step_ids": completed_step_ids if isinstance(completed_step_ids, list) else [],
        "resume_supported": resume_supported,
        "validation_status": str(session.get("validation_status", "")).strip() or "unknown",
        "manifest_path": manifest_path,
        "manifest_exists": bool(manifest_path) and Path(manifest_path).exists(),
        "session_path": str(session_path),
        "latest_report_path": latest_report_path,
        "latest_report_exists": latest_report_exists,
        "latest_report_digest": str(last_receipt.get("report_digest", "")).strip(),
        "last_receipt_id": (
            f"{session_id}:{last_receipt.get('step_id', '')}:{last_receipt.get('recorded_at', '')}"
            if last_receipt
            else ""
        ),
        "checkpoint": checkpoint,
        "handoff": handoff,
        "artifact_refs": [
            str(session_path),
            manifest_path,
            latest_report_path,
        ],
    }
    return summary, issues


def _select_latest_session(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    def _key(item: dict[str, Any]) -> tuple[str, str]:
        return (str(item.get("updated_at", "")), str(item.get("session_id", "")))

    return sorted(summaries, key=_key)[-1]


def _render_markdown(report: dict[str, Any]) -> str:
    latest = report.get("latest_session", {})
    issues = report.get("issues", [])
    next_actions = report.get("recommended_next_actions", [])
    return "\n".join(
        [
            "# Outer Session Ledger Report",
            "",
            f"- generated_utc: `{report.get('generated_utc', '')}`",
            f"- status: `{report.get('status', '')}`",
            f"- cluster_id: `{report.get('cluster_id', '')}`",
            f"- first_slice: `{report.get('first_slice', '')}`",
            f"- source_family: `{report.get('source_family', '')}`",
            f"- host_kind: `{report.get('host_kind', '')}`",
            f"- sessions_found: `{report.get('sessions_found', 0)}`",
            f"- observer_only: `{report.get('observer_only', False)}`",
            "",
            "## Latest Session",
            f"- session_id: `{latest.get('session_id', '')}`",
            f"- stack_id: `{latest.get('stack_id', '')}`",
            f"- status: `{latest.get('status', '')}`",
            f"- current_step: `{latest.get('current_step_id', '')}`",
            f"- total_steps: `{latest.get('total_steps', 0)}`",
            f"- receipt_count: `{latest.get('checkpoint', {}).get('receipt_count', 0)}`",
            f"- resume_supported: `{latest.get('resume_supported', False)}`",
            "",
            "## Recommended Next Actions",
            *[f"- {item}" for item in next_actions],
            "",
            "## Issues",
            *([f"- {item}" for item in issues] or ["- none"]),
            "",
        ]
    )


def build_outer_session_ledger(
    repo_root: str | Path = REPO_ROOT,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    root = Path(repo_root).resolve()
    ctx = ctx or {}
    sessions_root = _resolve_output_path(root, ctx.get("sessions_root"), DEFAULT_SESSIONS_ROOT)
    host_kind = str(ctx.get("host_kind", "ratchet_prompt_stack")).strip() or "ratchet_prompt_stack"
    issues: list[str] = []

    session_summaries: list[dict[str, Any]] = []
    for session_path in _session_files(sessions_root):
        summary, session_issues = _session_summary(session_path)
        if summary:
            session_summaries.append(summary)
        issues.extend(session_issues)

    if not session_summaries:
        issues.append(f"no session.json files found under {sessions_root}")

    latest_session = _select_latest_session(session_summaries) if session_summaries else {}
    status = "ok" if session_summaries and not issues else "attention_required"

    recommended_next_actions = [
        "Keep this slice repo-held and observer-only; do not widen to runtime hosting.",
        "Use the ledger state/report as continuity evidence before any outside-shell claims.",
        "If the next imported continuation stays external, keep pi-mono as the remaining broader control-shell seam.",
    ]

    report = {
        "schema": "OUTER_SESSION_LEDGER_REPORT_v1",
        "generated_utc": _utc_iso(),
        "status": status,
        "cluster_id": "SKILL_CLUSTER::outer-session-durability",
        "import_label": "FlowMind Session Durability Bridge",
        "first_slice": "outer-session-ledger",
        "source_family": "lev-os/leviathan",
        "host_kind": host_kind,
        "observer_only": True,
        "sessions_root": str(sessions_root),
        "sessions_found": len(session_summaries),
        "latest_session": latest_session,
        "issues": issues,
        "recommended_next_actions": recommended_next_actions,
        "non_goals": DEFAULT_NON_GOALS,
    }

    state = {
        "schema": "OUTER_SESSION_LEDGER_STATE_v1",
        "generated_utc": report["generated_utc"],
        "source_family": "lev-os/leviathan",
        "import_label": "FlowMind Session Durability Bridge",
        "host_kind": host_kind,
        "sessions_root": str(sessions_root),
        "observed_session_count": len(session_summaries),
        "session_id": latest_session.get("session_id", ""),
        "program_ref": latest_session.get("stack_id", ""),
        "status": latest_session.get("status", "no_sessions"),
        "current_step_index": latest_session.get("current_step_index", 0),
        "current_step_id": latest_session.get("current_step_id", ""),
        "total_steps": latest_session.get("total_steps", 0),
        "checkpoint": latest_session.get("checkpoint", {}),
        "handoff": latest_session.get("handoff", {}),
        "artifact_refs": latest_session.get("artifact_refs", []),
        "created_utc": latest_session.get("created_at", ""),
        "updated_utc": latest_session.get("updated_at", ""),
        "last_receipt_id": latest_session.get("last_receipt_id", ""),
        "resume_supported": latest_session.get("resume_supported", False),
        "first_error": issues[0] if issues else "",
    }

    event = {
        "observed_at": report["generated_utc"],
        "cluster_id": report["cluster_id"],
        "first_slice": report["first_slice"],
        "source_family": report["source_family"],
        "host_kind": host_kind,
        "session_id": state["session_id"],
        "program_ref": state["program_ref"],
        "status": state["status"],
        "current_step_id": state["current_step_id"],
        "receipt_count": state["checkpoint"].get("receipt_count", 0),
        "resume_supported": state["resume_supported"],
        "first_error": state["first_error"],
    }
    return state, report, event


def run_outer_session_ledger(ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    repo = Path(str(ctx.get("repo", REPO_ROOT))).resolve()
    state_path = _resolve_output_path(repo, ctx.get("state_path"), OUTER_SESSION_LEDGER_STATE)
    events_path = _resolve_output_path(repo, ctx.get("events_path"), OUTER_SESSION_LEDGER_EVENTS)
    report_json_path = _resolve_output_path(repo, ctx.get("report_json_path"), OUTER_SESSION_LEDGER_REPORT_JSON)
    report_md_path = _resolve_output_path(repo, ctx.get("report_md_path"), OUTER_SESSION_LEDGER_REPORT_MD)

    state, report, event = build_outer_session_ledger(repo, ctx)
    _write_json(state_path, state)
    _write_json(report_json_path, report)
    report_md_path.parent.mkdir(parents=True, exist_ok=True)
    report_md_path.write_text(_render_markdown(report), encoding="utf-8")
    _append_jsonl(events_path, event)

    return {
        **report,
        "state_path": str(state_path),
        "events_path": str(events_path),
        "report_json_path": str(report_json_path),
        "report_md_path": str(report_md_path),
    }


if __name__ == "__main__":
    emitted = run_outer_session_ledger({})
    assert emitted["first_slice"] == "outer-session-ledger"
    print("PASS: outer-session-ledger")
