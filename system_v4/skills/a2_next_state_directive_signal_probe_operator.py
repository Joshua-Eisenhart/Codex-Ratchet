"""
a2_next_state_directive_signal_probe_operator.py

Bounded probe over the live witness corpus for next-state and directive signal
shape.

This slice follows the next-state-signal adaptation audit operator. It does not
learn, mutate, or train. It only inspects repo-held witness evidence and
reports whether the current corpus actually contains the kind of post-action
signal that the OpenClaw-derived translation would need.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

NEXT_STATE_AUDIT_REPORT = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.json"
)
WITNESS_CORPUS_PATH = "system_v4/a2_state/witness_corpus_v1.json"
READINESS_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json"
)

REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_REPORT__CURRENT__v1.json"
)
REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_REPORT__CURRENT__v1.md"
)
PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_PACKET__CURRENT__v1.json"
)

CLUSTER_ID = "SKILL_CLUSTER::next-state-signal-adaptation"
SLICE_ID = "a2-next-state-directive-signal-probe-operator"

DIRECTIVE_MARKERS = [
    "should",
    "must",
    "need to",
    "use ",
    "keep ",
    "replace",
    "remove",
    "fix",
    "avoid",
    "do not",
]

DEFAULT_NON_GOALS = [
    "Do not mutate witness entries or synthesize missing evidence.",
    "Do not treat intent/context entries alone as next-state proof.",
    "Do not widen this into a live improver or learning claim.",
    "Do not claim OpenClaw runtime or online RL behavior from this probe.",
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


def _load_witness_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(payload, list):
        return [entry for entry in payload if isinstance(entry, dict)]
    if isinstance(payload, dict):
        entries = payload.get("entries", [])
        if isinstance(entries, list):
            return [entry for entry in entries if isinstance(entry, dict)]
    return []


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _entry_notes(entry: dict[str, Any]) -> list[str]:
    witness = entry.get("witness", {}) if isinstance(entry.get("witness"), dict) else {}
    trace = witness.get("trace", []) if isinstance(witness.get("trace"), list) else []
    notes: list[str] = []
    for item in trace:
        if not isinstance(item, dict):
            continue
        raw_notes = item.get("notes", [])
        if isinstance(raw_notes, list):
            notes.extend(str(note) for note in raw_notes if str(note).strip())
    return notes


def _has_transition_evidence(entry: dict[str, Any]) -> bool:
    witness = entry.get("witness", {}) if isinstance(entry.get("witness"), dict) else {}
    kind = str(witness.get("kind", "")).strip().lower()
    if kind in {"positive", "negative", "counterexample"}:
        return True
    trace = witness.get("trace", []) if isinstance(witness.get("trace"), list) else []
    for item in trace:
        if not isinstance(item, dict):
            continue
        if str(item.get("before_hash", "")).strip() or str(item.get("after_hash", "")).strip():
            return True
    if witness.get("violations"):
        return True
    if witness.get("touched_boundaries"):
        return True
    return False


def _has_directive_signal(entry: dict[str, Any]) -> bool:
    witness = entry.get("witness", {}) if isinstance(entry.get("witness"), dict) else {}
    kind = str(witness.get("kind", "")).strip().lower()
    if kind in {"intent", "context"}:
        return False
    blob = " ".join(_entry_notes(entry)).lower()
    return any(marker in blob for marker in DIRECTIVE_MARKERS)


def _has_evaluative_signal(entry: dict[str, Any]) -> bool:
    witness = entry.get("witness", {}) if isinstance(entry.get("witness"), dict) else {}
    kind = str(witness.get("kind", "")).strip().lower()
    if kind in {"negative", "counterexample"}:
        return True
    if witness.get("violations"):
        return True
    return False


def _summarize_entry(index: int, entry: dict[str, Any]) -> dict[str, Any]:
    witness = entry.get("witness", {}) if isinstance(entry.get("witness"), dict) else {}
    return {
        "index": index,
        "recorded_at": entry.get("recorded_at", ""),
        "kind": witness.get("kind", ""),
        "has_transition_evidence": _has_transition_evidence(entry),
        "has_evaluative_signal": _has_evaluative_signal(entry),
        "has_directive_signal": _has_directive_signal(entry),
        "notes_preview": _entry_notes(entry)[:2],
    }


def _render_markdown(report: dict[str, Any]) -> str:
    sample_lines = [
        (
            f"- witness[{item['index']}]: kind={item['kind']} "
            f"transition={item['has_transition_evidence']} "
            f"evaluative={item['has_evaluative_signal']} "
            f"directive={item['has_directive_signal']}"
        )
        for item in report.get("sample_entries", [])
    ] or ["- none"]
    action_lines = [f"- {item}" for item in report.get("recommended_actions", [])]
    issue_lines = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    return "\n".join(
        [
            "# A2 Next-State Directive Signal Probe Report",
            "",
            f"- generated_utc: `{report['generated_utc']}`",
            f"- status: `{report['status']}`",
            f"- cluster_id: `{report['cluster_id']}`",
            f"- first_slice: `{report['first_slice']}`",
            f"- witness_entry_count: `{report['witness_entry_count']}`",
            f"- next_state_candidate_count: `{report['signal_counts']['next_state_candidate_count']}`",
            f"- directive_signal_count: `{report['signal_counts']['directive_signal_count']}`",
            f"- recommended_next_step: `{report['gate']['recommended_next_step']}`",
            "",
            "## Sample Entries",
            *sample_lines,
            "",
            "## Recommended Actions",
            *action_lines,
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def build_a2_next_state_directive_signal_probe_report(
    repo_root: str | Path = REPO_ROOT,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    next_state_audit_path = _resolve_output_path(root, ctx.get("next_state_audit_path"), NEXT_STATE_AUDIT_REPORT)
    witness_path = _resolve_output_path(root, ctx.get("witness_path"), WITNESS_CORPUS_PATH)
    readiness_report_path = _resolve_output_path(root, ctx.get("readiness_report_path"), READINESS_REPORT_PATH)

    issues: list[str] = []
    next_state_audit = _safe_load_json(next_state_audit_path)
    readiness_report = _safe_load_json(readiness_report_path)
    witness_entries = _load_witness_entries(witness_path)

    if next_state_audit.get("status") != "ok":
        issues.append("next-state adaptation audit report is missing or not ok")
    if not witness_entries:
        issues.append("witness corpus is missing or empty")
    if readiness_report.get("status") != "ok":
        issues.append("skill improver readiness report is missing or not ok")

    summaries = [_summarize_entry(index, entry) for index, entry in enumerate(witness_entries)]
    next_state_candidates = [item for item in summaries if item["has_transition_evidence"]]
    evaluative_signals = [item for item in summaries if item["has_evaluative_signal"]]
    directive_signals = [item for item in summaries if item["has_directive_signal"]]

    if not issues and not next_state_candidates:
        issues.append("no real post-action next-state candidates are present in the witness corpus")
    if not issues and next_state_candidates and not directive_signals:
        issues.append("next-state candidates exist but none currently contain directive-correction signal")

    if "next-state adaptation audit report is missing or not ok" in issues:
        next_step = "repair_next_state_probe_inputs"
    elif "witness corpus is missing or empty" in issues:
        next_step = "record_real_post_action_witnesses_first"
    elif "no real post-action next-state candidates are present in the witness corpus" in issues:
        next_step = "record_real_post_action_witnesses_first"
    elif "next-state candidates exist but none currently contain directive-correction signal" in issues:
        next_step = "capture_directive_corrections_in_witnesses"
    elif readiness_report.get("status") != "ok":
        next_step = "hold_until_improver_lane_ready"
    else:
        next_step = "candidate_next_state_improver_context_bridge"

    allow_pattern_follow_on = not issues and bool(next_state_candidates)
    allow_improver_follow_on = (
        not issues
        and bool(next_state_candidates)
        and bool(directive_signals)
        and readiness_report.get("status") == "ok"
    )

    report = {
        "schema": "A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_REPORT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": "ok" if allow_improver_follow_on else "attention_required",
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": CLUSTER_ID,
        "first_slice": SLICE_ID,
        "source_family": "OpenClaw-RL-derived next-state signal adaptation",
        "next_state_audit_path": str(next_state_audit_path.relative_to(root)) if next_state_audit_path.is_relative_to(root) else str(next_state_audit_path),
        "witness_path": str(witness_path.relative_to(root)) if witness_path.is_relative_to(root) else str(witness_path),
        "readiness_report_path": str(readiness_report_path.relative_to(root)) if readiness_report_path.is_relative_to(root) else str(readiness_report_path),
        "witness_entry_count": len(witness_entries),
        "signal_counts": {
            "next_state_candidate_count": len(next_state_candidates),
            "evaluative_signal_count": len(evaluative_signals),
            "directive_signal_count": len(directive_signals),
            "intent_or_context_only_count": sum(
                1 for item in summaries if item["kind"] in {"intent", "context"}
            ),
        },
        "sample_entries": summaries[:5],
        "gate": {
            "allow_pattern_follow_on": allow_pattern_follow_on,
            "allow_improver_follow_on": allow_improver_follow_on,
            "allow_live_learning_claims": False,
            "allow_runtime_import_claims": False,
            "recommended_next_step": next_step,
            "reason": (
                "current witness evidence includes real next-state and directive signal shape, but the slice remains audit-only"
                if allow_improver_follow_on
                else "current witness evidence does not yet earn an improver-context bridge or live-learning claim"
            ),
        },
        "recommended_actions": [
            "Keep this slice audit-only and use it to measure signal quality, not to mutate the system.",
            "Record real post-action witness entries with before/after hashes and corrective notes before widening the lane.",
            "Do not treat intent/context preservation by itself as next-state or directive-correction proof.",
        ],
        "non_goals": list(DEFAULT_NON_GOALS),
        "staged_output_targets": {
            "json_report": REPORT_JSON,
            "md_report": REPORT_MD,
            "packet_json": PACKET_JSON,
        },
        "issues": issues,
    }

    packet = {
        "schema": "A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": report["status"],
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": CLUSTER_ID,
        "first_slice": SLICE_ID,
        "allow_pattern_follow_on": allow_pattern_follow_on,
        "allow_improver_follow_on": allow_improver_follow_on,
        "allow_live_learning_claims": False,
        "allow_runtime_import_claims": False,
        "recommended_next_step": next_step,
        "issues": issues,
    }
    return report, packet


def run_a2_next_state_directive_signal_probe(ctx: dict[str, Any]) -> dict[str, Any]:
    repo_root = ctx.get("repo", REPO_ROOT)
    root = Path(repo_root).resolve()
    report, packet = build_a2_next_state_directive_signal_probe_report(root, ctx)

    report_path = _resolve_output_path(root, ctx.get("report_path"), REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("markdown_path"), REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), PACKET_JSON)

    _write_json(report_path, report)
    _write_text(markdown_path, _render_markdown(report))
    _write_json(packet_path, packet)

    report["report_path"] = str(report_path)
    report["markdown_path"] = str(markdown_path)
    report["packet_path"] = str(packet_path)
    return report


if __name__ == "__main__":
    report, packet = build_a2_next_state_directive_signal_probe_report(REPO_ROOT)
    assert report["cluster_id"] == CLUSTER_ID
    assert report["first_slice"] == SLICE_ID
    assert packet["allow_live_learning_claims"] is False
    print("PASS: a2_next_state_directive_signal_probe_operator self-test")
