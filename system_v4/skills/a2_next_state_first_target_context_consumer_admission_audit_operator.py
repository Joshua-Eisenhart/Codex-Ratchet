"""
a2_next_state_first_target_context_consumer_admission_audit_operator.py

Audit-only admission check for whether the landed next-state bridge currently
has an explicit consumer contract inside the one-proven-target skill-improver
lane.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

CLUSTER_ID = "SKILL_CLUSTER::next-state-signal-adaptation"
SLICE_ID = "a2-next-state-first-target-context-consumer-admission-audit-operator"
OWNER_SKILL_ID = "skill-improver-operator"
OWNER_SKILL_SPEC = "system_v4/skill_specs/skill-improver-operator/SKILL.md"
OWNER_SKILL_SOURCE = "system_v4/skills/skill_improver_operator.py"

BRIDGE_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT__CURRENT__v1.json"
)
BRIDGE_PACKET_PATH = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_PACKET__CURRENT__v1.json"
)
TARGET_SELECTION_PACKET_PATH = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_PACKET__CURRENT__v1.json"
)
FIRST_TARGET_PROOF_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_FIRST_TARGET_PROOF_REPORT__CURRENT__v1.json"
)
SECOND_TARGET_PACKET_PATH = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_SECOND_TARGET_ADMISSION_PACKET__CURRENT__v1.json"
)

REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_REPORT__CURRENT__v1.json"
)
REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_REPORT__CURRENT__v1.md"
)
PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_PACKET__CURRENT__v1.json"
)

CONTEXT_CONTRACT_MARKERS = [
    "context_packet",
    "context_bridge_packet",
    "bridge_packet",
    "directive_topics",
    "selected_witness_indices",
    "context_notes",
]

DEFAULT_NON_GOALS = [
    "Do not mutate any target skill or witness surface from this slice.",
    "Do not invent a context seam if the current consumer contract does not expose one.",
    "Do not widen this into second-target admission, live learning, runtime import, or graph backfill.",
    "Do not treat a repo-held packet preview as proof that the consumer path is implemented.",
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


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _context_contract_summary(spec_text: str, source_text: str) -> dict[str, Any]:
    spec_lower = spec_text.lower()
    source_lower = source_text.lower()
    markers_in_spec = [marker for marker in CONTEXT_CONTRACT_MARKERS if marker in spec_lower]
    markers_in_source = [marker for marker in CONTEXT_CONTRACT_MARKERS if marker in source_lower]
    explicit_input_section = "inputs:" in spec_text and any(marker in spec_lower for marker in CONTEXT_CONTRACT_MARKERS)
    explicit_ctx_get = any(f'ctx.get("{marker}")' in source_text or f"ctx.get('{marker}')" in source_text for marker in CONTEXT_CONTRACT_MARKERS)
    return {
        "spec_exists": bool(spec_text),
        "source_exists": bool(source_text),
        "markers_in_spec": markers_in_spec,
        "markers_in_source": markers_in_source,
        "explicit_input_section": explicit_input_section,
        "explicit_ctx_get": explicit_ctx_get,
        "has_explicit_context_contract": bool(markers_in_spec) and explicit_ctx_get,
    }


def _next_step(issues: list[str], allow_consumer: bool) -> str:
    if allow_consumer:
        return "hold_consumer_as_audit_only"
    if "bridge packet is missing or not ok" in issues or "bridge report is missing or not ok" in issues:
        return "repair_bridge_inputs_first"
    if "bridge does not currently allow first-target context use" in issues:
        return "hold_context_bridge_as_audit_only"
    if "current owner skill does not expose an explicit context consumer contract" in issues:
        return "define_explicit_context_consumer_contract_first"
    if "first target proof is missing or not completed" in issues:
        return "hold_until_first_target_proof_exists"
    if "selected target and proven first target do not match" in issues:
        return "repair_first_target_alignment"
    if "second target gate is not currently held fail-closed" in issues:
        return "reconcile_second_target_gate_first"
    return "repair_bridge_inputs_first"


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    lines = [
        "# A2 Next-State First-Target Context Consumer Admission Audit",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- consumer_status: `{report.get('consumer_status', '')}`",
        f"- recommended_next_step: `{report.get('recommended_next_step', '')}`",
        "",
        "## Contract Summary",
        f"- owner_skill_id: `{report.get('owner_skill_id', '')}`",
        f"- selected_target_skill_id: `{report.get('selected_target_skill_id', '')}`",
        f"- proven_first_target_skill_id: `{report.get('proven_first_target_skill_id', '')}`",
        f"- explicit_context_contract: `{report.get('context_contract_summary', {}).get('has_explicit_context_contract', False)}`",
        "",
        "## Proposed Consumer Packet",
        f"- allowed_target_paths: `{report.get('proposed_consumer_packet_preview', {}).get('allowed_target_paths', [])}`",
        f"- selected_witness_indices: `{report.get('proposed_consumer_packet_preview', {}).get('selected_witness_indices', [])}`",
        "",
        "## Packet",
        f"- allow_context_consumer: `{packet.get('allow_context_consumer', False)}`",
        f"- allow_first_target_context_packet_only: `{packet.get('allow_first_target_context_packet_only', False)}`",
        f"- retain_general_gate: `{packet.get('retain_general_gate', False)}`",
        "",
        "## Issues",
    ]
    issues = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    lines.extend(issues)
    lines.append("")
    return "\n".join(lines)


def build_a2_next_state_first_target_context_consumer_admission_report(
    repo_root: str | Path = REPO_ROOT,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    bridge_report_path = _resolve_output_path(root, ctx.get("bridge_report_path"), BRIDGE_REPORT_PATH)
    bridge_packet_path = _resolve_output_path(root, ctx.get("bridge_packet_path"), BRIDGE_PACKET_PATH)
    target_selection_packet_path = _resolve_output_path(
        root, ctx.get("target_selection_packet_path"), TARGET_SELECTION_PACKET_PATH
    )
    first_target_proof_report_path = _resolve_output_path(
        root, ctx.get("first_target_proof_report_path"), FIRST_TARGET_PROOF_REPORT_PATH
    )
    second_target_packet_path = _resolve_output_path(
        root, ctx.get("second_target_packet_path"), SECOND_TARGET_PACKET_PATH
    )

    bridge_report = _safe_load_json(bridge_report_path)
    bridge_packet = _safe_load_json(bridge_packet_path)
    target_selection_packet = _safe_load_json(target_selection_packet_path)
    first_target_proof_report = _safe_load_json(first_target_proof_report_path)
    second_target_packet = _safe_load_json(second_target_packet_path)
    owner_skill_spec_text = _load_text(root / OWNER_SKILL_SPEC)
    owner_skill_source_text = _load_text(root / OWNER_SKILL_SOURCE)

    issues: list[str] = []
    if bridge_report.get("status") != "ok":
        issues.append("bridge report is missing or not ok")
    if bridge_packet.get("status") != "ok":
        issues.append("bridge packet is missing or not ok")
    if not bridge_packet.get("allow_first_target_context_only", False):
        issues.append("bridge does not currently allow first-target context use")
    if first_target_proof_report.get("status") != "ok" or not first_target_proof_report.get("proof_completed"):
        issues.append("first target proof is missing or not completed")
    if second_target_packet.get("retain_general_gate") is not True or second_target_packet.get("allow_second_target_admission") is not False:
        issues.append("second target gate is not currently held fail-closed")

    selected_target_skill_id = str(target_selection_packet.get("recommended_target_skill_id", "")).strip()
    selected_target_skill_path = str(target_selection_packet.get("recommended_target_skill_path", "")).strip()
    proven_first_target_skill_id = str(first_target_proof_report.get("target_skill_id", "")).strip()
    if selected_target_skill_id != proven_first_target_skill_id:
        issues.append("selected target and proven first target do not match")

    contract_summary = _context_contract_summary(owner_skill_spec_text, owner_skill_source_text)
    if not contract_summary["has_explicit_context_contract"]:
        issues.append("current owner skill does not expose an explicit context consumer contract")

    proposed_preview = {
        "owner_skill_id": OWNER_SKILL_ID,
        "selected_target_skill_id": selected_target_skill_id,
        "selected_target_skill_path": selected_target_skill_path,
        "allowed_target_paths": list(target_selection_packet.get("recommended_allowed_targets", [])),
        "selected_witness_indices": list(
            (bridge_report.get("context_bridge_preview", {}) or {}).get("selected_witness_indices", [])
        ),
        "directive_topics": list(
            (bridge_report.get("context_bridge_preview", {}) or {}).get("directive_topics", [])
        ),
        "forbidden_uses": list(
            (bridge_report.get("context_bridge_preview", {}) or {}).get("forbidden_uses", [])
        ),
        "missing_contract_fields": [] if contract_summary["has_explicit_context_contract"] else list(CONTEXT_CONTRACT_MARKERS),
    }

    allow_context_consumer = not issues
    consumer_status = (
        "candidate_first_target_context_consumer_admissible"
        if allow_context_consumer
        else "hold_no_explicit_first_target_context_consumer"
    )
    recommended_next_step = _next_step(issues, allow_context_consumer)

    report = {
        "schema": "A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_REPORT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": "ok",
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "source_family": "OpenClaw-RL-derived next-state bridge plus Ratchet-native skill-improver gate surfaces",
        "consumer_status": consumer_status,
        "recommended_next_step": recommended_next_step,
        "owner_skill_id": OWNER_SKILL_ID,
        "selected_target_skill_id": selected_target_skill_id,
        "selected_target_skill_path": selected_target_skill_path,
        "proven_first_target_skill_id": proven_first_target_skill_id,
        "bridge_report_path": str(bridge_report_path.relative_to(root)) if bridge_report_path.is_relative_to(root) else str(bridge_report_path),
        "bridge_packet_path": str(bridge_packet_path.relative_to(root)) if bridge_packet_path.is_relative_to(root) else str(bridge_packet_path),
        "target_selection_packet_path": str(target_selection_packet_path.relative_to(root)) if target_selection_packet_path.is_relative_to(root) else str(target_selection_packet_path),
        "first_target_proof_report_path": str(first_target_proof_report_path.relative_to(root)) if first_target_proof_report_path.is_relative_to(root) else str(first_target_proof_report_path),
        "second_target_packet_path": str(second_target_packet_path.relative_to(root)) if second_target_packet_path.is_relative_to(root) else str(second_target_packet_path),
        "context_contract_summary": contract_summary,
        "proposed_consumer_packet_preview": proposed_preview,
        "recommended_actions": [
            "Keep this slice audit-only and fail closed unless the owner skill exposes an explicit first-target context contract.",
            "Do not widen this result into live mutation, second-target admission, runtime import, or graph backfill.",
            "If a later consumer is built, keep it first-target-context-only and retain the general skill-improver gate.",
        ],
        "non_goals": list(DEFAULT_NON_GOALS),
        "issues": issues,
    }

    packet = {
        "schema": "A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": report["status"],
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "owner_skill_id": OWNER_SKILL_ID,
        "selected_target_skill_id": selected_target_skill_id,
        "proven_first_target_skill_id": proven_first_target_skill_id,
        "allow_context_consumer": allow_context_consumer,
        "allow_first_target_context_packet_only": allow_context_consumer,
        "allow_live_learning_claims": False,
        "allow_runtime_import_claims": False,
        "allow_second_target_context": False,
        "allow_graph_backfill_claims": False,
        "retain_general_gate": True,
        "recommended_next_step": recommended_next_step,
        "issues": issues,
    }
    return report, packet


def run_a2_next_state_first_target_context_consumer_admission_audit(
    ctx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report, packet = build_a2_next_state_first_target_context_consumer_admission_report(root, ctx)

    report_path = _resolve_output_path(root, ctx.get("report_path"), REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("markdown_path"), REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), PACKET_JSON)

    _write_json(report_path, report)
    _write_text(markdown_path, _render_markdown(report, packet))
    _write_json(packet_path, packet)

    return {
        "status": report["status"],
        "consumer_status": report["consumer_status"],
        "recommended_next_step": report["recommended_next_step"],
        "report_path": str(report_path),
        "markdown_path": str(markdown_path),
        "packet_path": str(packet_path),
    }


if __name__ == "__main__":
    report, packet = build_a2_next_state_first_target_context_consumer_admission_report(REPO_ROOT)
    assert report["cluster_id"] == CLUSTER_ID
    assert report["slice_id"] == SLICE_ID
    assert packet["allow_live_learning_claims"] is False
    print("PASS: a2_next_state_first_target_context_consumer_admission_audit_operator self-test")
