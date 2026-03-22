"""
a2_next_state_improver_context_bridge_audit_operator.py

Audit-only bridge between current next-state witness signals and the bounded
skill-improver lane.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

CLUSTER_ID = "SKILL_CLUSTER::next-state-signal-adaptation"
SLICE_ID = "a2-next-state-improver-context-bridge-audit-operator"
OWNER_SKILL_ID = "skill-improver-operator"

PROBE_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_REPORT__CURRENT__v1.json"
)
PROBE_PACKET_PATH = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_PACKET__CURRENT__v1.json"
)
WITNESS_PATH = "system_v4/a2_state/witness_corpus_v1.json"
READINESS_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json"
)
FIRST_TARGET_PROOF_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_FIRST_TARGET_PROOF_REPORT__CURRENT__v1.json"
)
SECOND_TARGET_PACKET_PATH = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_SECOND_TARGET_ADMISSION_PACKET__CURRENT__v1.json"
)

REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT__CURRENT__v1.json"
)
REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT__CURRENT__v1.md"
)
PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_PACKET__CURRENT__v1.json"
)

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
    "Do not mutate witness entries or any skill-improver target from this slice.",
    "Do not treat this bridge as second-target admission or general mutation authority.",
    "Do not claim live learning, online training, or OpenClaw runtime behavior from this audit.",
    "Do not seed graph links or backfill kernel relations from this bridge result.",
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


def _first_trace_item(entry: dict[str, Any]) -> dict[str, Any]:
    witness = entry.get("witness", {}) if isinstance(entry.get("witness"), dict) else {}
    trace = witness.get("trace", []) if isinstance(witness.get("trace"), list) else []
    for item in trace:
        if isinstance(item, dict):
            return item
    return {}


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
    if str(witness.get("kind", "")).strip().lower() in {"intent", "context"}:
        return False
    blob = " ".join(_entry_notes(entry)).lower()
    return any(marker in blob for marker in DIRECTIVE_MARKERS)


def _bridge_role(entry: dict[str, Any]) -> str:
    tags = entry.get("tags", {}) if isinstance(entry.get("tags"), dict) else {}
    topic = str(tags.get("topic", "")).strip()
    skill = str(tags.get("skill", "")).strip()
    if topic == "skill_improver_gate" or skill == "a2-skill-improver-second-target-admission-audit-operator":
        return "retain_general_gate"
    if topic == "a2_refresh_sync" or skill == "a2-brain-surface-refresher":
        return "preserve_upper_loop_green"
    if topic == "graph_audit_sync":
        return "preserve_graph_registry_parity"
    return "generic_post_action_context"


def _bridge_candidate(index: int, entry: dict[str, Any]) -> dict[str, Any]:
    witness = entry.get("witness", {}) if isinstance(entry.get("witness"), dict) else {}
    tags = entry.get("tags", {}) if isinstance(entry.get("tags"), dict) else {}
    trace_item = _first_trace_item(entry)
    notes = _entry_notes(entry)
    return {
        "witness_index": index,
        "recorded_at": entry.get("recorded_at", ""),
        "kind": str(witness.get("kind", "")).strip(),
        "topic": str(tags.get("topic", "")).strip(),
        "skill": str(tags.get("skill", "")).strip(),
        "phase": str(tags.get("phase", "")).strip(),
        "bridge_role": _bridge_role(entry),
        "before_hash": str(trace_item.get("before_hash", "")).strip(),
        "after_hash": str(trace_item.get("after_hash", "")).strip(),
        "notes_preview": notes[:2],
    }


def _candidate_next_step(issues: list[str], allow_context_bridge: bool) -> str:
    if allow_context_bridge:
        return "hold_context_bridge_as_audit_only"
    if "next-state directive probe packet is missing or not ok" in issues:
        return "repair_next_state_bridge_inputs"
    if "next-state directive probe does not currently allow improver follow-on" in issues:
        return "record_real_post_action_witnesses_first"
    if "first target proof is missing or not completed" in issues:
        return "hold_until_first_target_proof_exists"
    if "second target admission packet is missing or not ok" in issues:
        return "repair_skill_improver_gate_inputs"
    if "second target lane is unexpectedly open; bridge slice expects one-proven-target hold" in issues:
        return "reconcile_skill_improver_general_gate"
    if "no directive-bearing post-action witness candidates are currently available for the bridge" in issues:
        return "record_real_post_action_witnesses_first"
    return "repair_next_state_bridge_inputs"


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    lines = [
        "# A2 Next-State Improver Context Bridge Audit",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- bridge_status: `{report.get('bridge_status', '')}`",
        f"- recommended_next_step: `{report.get('recommended_next_step', '')}`",
        f"- bridge_candidate_count: `{report.get('bridge_candidate_count', 0)}`",
        f"- first_proven_target_skill_id: `{report.get('first_proven_target_skill_id', '')}`",
        "",
        "## Bridge Preview",
        f"- owner_skill_id: `{report.get('context_bridge_preview', {}).get('owner_skill_id', '')}`",
        f"- retained_second_target_gate: `{report.get('context_bridge_preview', {}).get('retained_second_target_gate', '')}`",
        f"- selected_witness_indices: `{report.get('context_bridge_preview', {}).get('selected_witness_indices', [])}`",
        "",
        "## Bridge Candidates",
    ]
    for item in report.get("bridge_candidates", []):
        lines.append(
            f"- witness[{item.get('witness_index', -1)}]: role={item.get('bridge_role', '')}; "
            f"topic={item.get('topic', '') or 'none'}; skill={item.get('skill', '') or 'none'}"
        )
    if not report.get("bridge_candidates"):
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Packet",
            f"- allow_context_bridge: `{packet.get('allow_context_bridge', False)}`",
            f"- allow_first_target_context_only: `{packet.get('allow_first_target_context_only', False)}`",
            f"- allow_second_target_context: `{packet.get('allow_second_target_context', False)}`",
            f"- do_not_promote: `{packet.get('do_not_promote', False)}`",
            "",
            "## Issues",
        ]
    )
    issue_lines = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    lines.extend(issue_lines)
    lines.append("")
    return "\n".join(lines)


def build_a2_next_state_improver_context_bridge_audit_report(
    repo_root: str | Path = REPO_ROOT,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    probe_report_path = _resolve_output_path(root, ctx.get("probe_report_path"), PROBE_REPORT_PATH)
    probe_packet_path = _resolve_output_path(root, ctx.get("probe_packet_path"), PROBE_PACKET_PATH)
    witness_path = _resolve_output_path(root, ctx.get("witness_path"), WITNESS_PATH)
    readiness_report_path = _resolve_output_path(root, ctx.get("readiness_report_path"), READINESS_REPORT_PATH)
    first_target_proof_report_path = _resolve_output_path(
        root, ctx.get("first_target_proof_report_path"), FIRST_TARGET_PROOF_REPORT_PATH
    )
    second_target_packet_path = _resolve_output_path(
        root, ctx.get("second_target_packet_path"), SECOND_TARGET_PACKET_PATH
    )

    probe_report = _safe_load_json(probe_report_path)
    probe_packet = _safe_load_json(probe_packet_path)
    readiness_report = _safe_load_json(readiness_report_path)
    first_target_proof_report = _safe_load_json(first_target_proof_report_path)
    second_target_packet = _safe_load_json(second_target_packet_path)
    witness_entries = _load_witness_entries(witness_path)

    issues: list[str] = []
    if probe_report.get("status") != "ok":
        issues.append("next-state directive probe report is missing or not ok")
    if probe_packet.get("status") != "ok":
        issues.append("next-state directive probe packet is missing or not ok")
    if not probe_packet.get("allow_improver_follow_on", False):
        issues.append("next-state directive probe does not currently allow improver follow-on")
    if readiness_report.get("status") != "ok":
        issues.append("skill improver readiness report is missing or not ok")
    if not first_target_proof_report.get("proof_completed"):
        issues.append("first target proof is missing or not completed")
    if second_target_packet.get("status") != "ok":
        issues.append("second target admission packet is missing or not ok")
    if second_target_packet.get("allow_second_target_admission") is True:
        issues.append("second target lane is unexpectedly open; bridge slice expects one-proven-target hold")

    first_proven_target_skill_id = str(first_target_proof_report.get("target_skill_id", "")).strip()
    if not first_proven_target_skill_id:
        issues.append("first proven target skill id is missing")

    bridge_candidates = [
        _bridge_candidate(index, entry)
        for index, entry in enumerate(witness_entries)
        if _has_transition_evidence(entry) and _has_directive_signal(entry)
    ]
    if not bridge_candidates:
        issues.append("no directive-bearing post-action witness candidates are currently available for the bridge")

    allow_context_bridge = not issues and bool(bridge_candidates)
    recommended_next_step = _candidate_next_step(issues, allow_context_bridge)
    bridge_status = (
        "admissible_as_first_target_context_only"
        if allow_context_bridge
        else "hold_until_bridge_inputs_and_scope_are_clean"
    )

    context_bridge_preview = {
        "owner_skill_id": OWNER_SKILL_ID,
        "first_proven_target_skill_id": first_proven_target_skill_id,
        "allowed_target_skill_ids": [first_proven_target_skill_id] if first_proven_target_skill_id else [],
        "selected_witness_indices": [item["witness_index"] for item in bridge_candidates[:5]],
        "directive_topics": sorted({item["topic"] for item in bridge_candidates if item["topic"]}),
        "retained_second_target_gate": str(second_target_packet.get("gate_status", "")).strip(),
        "allowed_context_uses": [
            "bounded audit prompts or summaries for the one proven target only",
            "repair-context preservation for future maintenance-lane review",
            "repo-held bridge packets that remain nonoperative and do_not_promote",
        ],
        "forbidden_uses": [
            "second target admission",
            "live mutation or autonomous policy updates",
            "online learning or runtime import claims",
            "graph link seeding or graph backfill claims",
        ],
    }

    report = {
        "schema": "A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": "ok" if allow_context_bridge else "attention_required",
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "source_family": "OpenClaw-RL-derived next-state signal family plus Ratchet-native skill-improver truth maintenance",
        "bridge_status": bridge_status,
        "recommended_next_step": recommended_next_step,
        "probe_report_path": str(probe_report_path.relative_to(root)) if probe_report_path.is_relative_to(root) else str(probe_report_path),
        "probe_packet_path": str(probe_packet_path.relative_to(root)) if probe_packet_path.is_relative_to(root) else str(probe_packet_path),
        "witness_path": str(witness_path.relative_to(root)) if witness_path.is_relative_to(root) else str(witness_path),
        "readiness_report_path": str(readiness_report_path.relative_to(root)) if readiness_report_path.is_relative_to(root) else str(readiness_report_path),
        "first_target_proof_report_path": str(first_target_proof_report_path.relative_to(root)) if first_target_proof_report_path.is_relative_to(root) else str(first_target_proof_report_path),
        "second_target_packet_path": str(second_target_packet_path.relative_to(root)) if second_target_packet_path.is_relative_to(root) else str(second_target_packet_path),
        "owner_skill_id": OWNER_SKILL_ID,
        "first_proven_target_skill_id": first_proven_target_skill_id,
        "bridge_candidate_count": len(bridge_candidates),
        "bridge_candidates": bridge_candidates[:5],
        "context_bridge_preview": context_bridge_preview,
        "recommended_actions": [
            "Keep this slice audit-only and use it only to preserve bounded first-target context around real post-action witness signals.",
            "Retain the general skill-improver gate and the one-proven-target hold even when the bridge is admissible.",
            "Do not widen this bridge into graph seeding, live learning, or OpenClaw runtime claims.",
        ],
        "non_goals": list(DEFAULT_NON_GOALS),
        "issues": issues,
    }

    packet = {
        "schema": "A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": report["status"],
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "owner_skill_id": OWNER_SKILL_ID,
        "first_proven_target_skill_id": first_proven_target_skill_id,
        "allow_context_bridge": allow_context_bridge,
        "allow_first_target_context_only": allow_context_bridge,
        "allow_second_target_context": False,
        "allow_live_learning_claims": False,
        "allow_runtime_import_claims": False,
        "allow_graph_backfill_claims": False,
        "retained_second_target_gate": str(second_target_packet.get("gate_status", "")).strip(),
        "recommended_next_step": recommended_next_step,
        "issues": issues,
    }
    return report, packet


def run_a2_next_state_improver_context_bridge_audit(ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report, packet = build_a2_next_state_improver_context_bridge_audit_report(root, ctx)

    report_path = _resolve_output_path(root, ctx.get("report_path"), REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("markdown_path"), REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), PACKET_JSON)

    _write_json(report_path, report)
    _write_text(markdown_path, _render_markdown(report, packet))
    _write_json(packet_path, packet)

    return {
        "status": report["status"],
        "bridge_status": report["bridge_status"],
        "recommended_next_step": report["recommended_next_step"],
        "report_path": str(report_path),
        "markdown_path": str(markdown_path),
        "packet_path": str(packet_path),
    }


if __name__ == "__main__":
    report, packet = build_a2_next_state_improver_context_bridge_audit_report(REPO_ROOT)
    assert report["cluster_id"] == CLUSTER_ID
    assert report["slice_id"] == SLICE_ID
    assert packet["allow_live_learning_claims"] is False
    assert packet["allow_graph_backfill_claims"] is False
    print("PASS: a2_next_state_improver_context_bridge_audit_operator self-test")
