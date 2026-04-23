"""
a2_next_state_first_target_context_consumer_proof_operator.py

Metadata-only proof slice for the admitted next-state first-target context
consumer seam inside skill-improver-operator.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.skill_improver_operator import run_skill_improver

CLUSTER_ID = "SKILL_CLUSTER::next-state-signal-adaptation"
SLICE_ID = "a2-next-state-first-target-context-consumer-proof-operator"
OWNER_SKILL_ID = "skill-improver-operator"

CONSUMER_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_REPORT__CURRENT__v1.json"
)
CONSUMER_PACKET_PATH = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_PACKET__CURRENT__v1.json"
)
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

REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_PROOF_REPORT__CURRENT__v1.json"
)
REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_PROOF_REPORT__CURRENT__v1.md"
)
PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_PROOF_PACKET__CURRENT__v1.json"
)

DEFAULT_NON_GOALS = [
    "Do not write to the selected target skill from this slice.",
    "Do not widen this proof into second-target admission, live learning, runtime import, or graph backfill.",
    "Do not treat a metadata-only context proof as authority to bypass the general skill-improver gate.",
    "Do not claim this slice creates a general-purpose next-state consumer lane.",
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


def _relative_or_str(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _next_step(issues: list[str], proof_completed: bool) -> str:
    if proof_completed:
        return "hold_consumer_proof_as_metadata_only"
    if "consumer admission packet is missing or not ok" in issues:
        return "repair_consumer_admission_first"
    if "context bridge packet is missing or not ok" in issues:
        return "repair_context_bridge_first"
    if "selected target and proven first target do not match" in issues:
        return "repair_first_target_alignment"
    if "skill-improver proof did not load metadata-only context" in issues:
        return "repair_owner_context_contract"
    if "skill-improver proof unexpectedly widened write permission" in issues:
        return "repair_write_gate_before_any_reuse"
    return "repair_consumer_admission_first"


def _context_packet(
    consumer_report: dict[str, Any],
    bridge_report: dict[str, Any],
    selected_target_skill_id: str,
) -> dict[str, Any]:
    preview = consumer_report.get("proposed_consumer_packet_preview", {})
    bridge_preview = bridge_report.get("context_bridge_preview", {})
    return {
        "owner_skill_id": OWNER_SKILL_ID,
        "selected_target_skill_id": selected_target_skill_id,
        "directive_topics": list(preview.get("directive_topics", [])),
        "selected_witness_indices": list(preview.get("selected_witness_indices", [])),
        "context_notes": list(bridge_preview.get("allowed_context_uses", [])),
        "forbidden_uses": list(preview.get("forbidden_uses", [])),
        "metadata_only": True,
        "first_target_context_only": True,
        "retain_general_gate": True,
    }


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    proof = report.get("skill_improver_result", {})
    lines = [
        "# A2 Next-State First-Target Context Consumer Proof Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- selected_target_skill_id: `{report.get('selected_target_skill_id', '')}`",
        f"- proof_completed: `{report.get('proof_completed', False)}`",
        f"- recommended_next_step: `{report.get('recommended_next_step', '')}`",
        "",
        "## Skill Improver Result",
        f"- context_contract_status: `{proof.get('context_contract_status', '')}`",
        f"- compile_ok: `{proof.get('compile_ok')}`",
        f"- tests_state: `{proof.get('tests_state', '')}`",
        f"- write_permitted: `{proof.get('write_permitted')}`",
        f"- proposed_change: `{proof.get('proposed_change')}`",
        "",
        "## Packet",
        f"- allow_metadata_only_context_consumer_proof: `{packet.get('allow_metadata_only_context_consumer_proof', False)}`",
        f"- allow_write: `{packet.get('allow_write', False)}`",
        f"- retain_general_gate: `{packet.get('retain_general_gate', False)}`",
        "",
        "## Issues",
    ]
    issues = [f"- {item}" for item in report.get("issues", [])] or ["- none"]
    lines.extend(issues)
    lines.append("")
    return "\n".join(lines)


def build_a2_next_state_first_target_context_consumer_proof_report(
    repo_root: str | Path = REPO_ROOT,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()

    consumer_report_path = _resolve_output_path(root, ctx.get("consumer_report_path"), CONSUMER_REPORT_PATH)
    consumer_packet_path = _resolve_output_path(root, ctx.get("consumer_packet_path"), CONSUMER_PACKET_PATH)
    bridge_report_path = _resolve_output_path(root, ctx.get("bridge_report_path"), BRIDGE_REPORT_PATH)
    bridge_packet_path = _resolve_output_path(root, ctx.get("bridge_packet_path"), BRIDGE_PACKET_PATH)
    target_selection_packet_path = _resolve_output_path(
        root, ctx.get("target_selection_packet_path"), TARGET_SELECTION_PACKET_PATH
    )
    first_target_proof_report_path = _resolve_output_path(
        root, ctx.get("first_target_proof_report_path"), FIRST_TARGET_PROOF_REPORT_PATH
    )

    consumer_report = _safe_load_json(consumer_report_path)
    consumer_packet = _safe_load_json(consumer_packet_path)
    bridge_report = _safe_load_json(bridge_report_path)
    bridge_packet = _safe_load_json(bridge_packet_path)
    target_selection_packet = _safe_load_json(target_selection_packet_path)
    first_target_proof_report = _safe_load_json(first_target_proof_report_path)

    issues: list[str] = []
    if consumer_report.get("status") != "ok":
        issues.append("consumer admission report is missing or not ok")
    if consumer_packet.get("status") != "ok":
        issues.append("consumer admission packet is missing or not ok")
    if consumer_packet.get("allow_context_consumer") is not True:
        issues.append("consumer admission does not currently allow the first-target context consumer seam")
    if bridge_report.get("status") != "ok":
        issues.append("context bridge report is missing or not ok")
    if bridge_packet.get("status") != "ok":
        issues.append("context bridge packet is missing or not ok")
    if bridge_packet.get("allow_context_bridge") is not True:
        issues.append("context bridge does not currently allow first-target context reuse")

    selected_target_skill_id = str(target_selection_packet.get("recommended_target_skill_id", "")).strip()
    selected_target_skill_path = str(target_selection_packet.get("recommended_target_skill_path", "")).strip()
    selected_target_smoke_path = str(target_selection_packet.get("recommended_target_smoke_path", "")).strip()
    proven_first_target_skill_id = str(first_target_proof_report.get("target_skill_id", "")).strip()
    if not selected_target_skill_id or not selected_target_skill_path:
        issues.append("selected target is missing from the target-selection packet")
    if first_target_proof_report.get("status") != "ok" or not first_target_proof_report.get("proof_completed"):
        issues.append("first target proof is missing or not completed")
    if selected_target_skill_id != proven_first_target_skill_id:
        issues.append("selected target and proven first target do not match")

    target_skill_path = (root / selected_target_skill_path).resolve() if selected_target_skill_path else Path()
    if selected_target_skill_path and not target_skill_path.exists():
        issues.append("selected target skill path does not exist")
    test_command = target_selection_packet.get("recommended_test_command")
    if not isinstance(test_command, list) or not test_command:
        issues.append("selected target test command is missing")

    skill_improver_result: dict[str, Any] = {}
    context_packet = _context_packet(consumer_report, bridge_report, selected_target_skill_id)
    bridge_preview = bridge_report.get("context_bridge_preview", {})
    if not issues:
        original_code = target_skill_path.read_text(encoding="utf-8")
        skill_improver_result = run_skill_improver(
            {
                "target_skill_path": str(target_skill_path),
                "candidate_code": original_code,
                "test_command": test_command,
                "allow_write": False,
                "allowed_targets": list(target_selection_packet.get("recommended_allowed_targets", [])),
                "context_packet": context_packet,
                "context_bridge_packet": bridge_packet,
                "bridge_packet": bridge_packet,
                "directive_topics": list(context_packet.get("directive_topics", [])),
                "selected_witness_indices": list(context_packet.get("selected_witness_indices", [])),
                "context_notes": list(context_packet.get("context_notes", [])),
            }
        )
        if skill_improver_result.get("context_contract_status") != "metadata_only_context_loaded":
            issues.append("skill-improver proof did not load metadata-only context")
        if skill_improver_result.get("compile_ok") is not True:
            issues.append("skill-improver proof did not compile cleanly")
        if skill_improver_result.get("tests_state") != "passed":
            issues.append("skill-improver proof did not preserve the selected target smoke")
        if skill_improver_result.get("write_permitted") is not False:
            issues.append("skill-improver proof unexpectedly widened write permission")

    proof_completed = not issues
    recommended_next_step = _next_step(issues, proof_completed)
    report = {
        "schema": "A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_PROOF_REPORT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": "ok" if proof_completed else "attention_required",
        "audit_only": True,
        "proof_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "source_family": "OpenClaw-RL-derived next-state bridge plus Ratchet-native skill-improver gate surfaces",
        "selected_target_skill_id": selected_target_skill_id,
        "selected_target_skill_path": selected_target_skill_path,
        "selected_target_smoke_path": selected_target_smoke_path,
        "proven_first_target_skill_id": proven_first_target_skill_id,
        "owner_skill_id": OWNER_SKILL_ID,
        "consumer_report_path": _relative_or_str(consumer_report_path, root),
        "consumer_packet_path": _relative_or_str(consumer_packet_path, root),
        "bridge_report_path": _relative_or_str(bridge_report_path, root),
        "bridge_packet_path": _relative_or_str(bridge_packet_path, root),
        "target_selection_packet_path": _relative_or_str(target_selection_packet_path, root),
        "first_target_proof_report_path": _relative_or_str(first_target_proof_report_path, root),
        "context_packet_preview": context_packet,
        "bridge_preview": {
            "directive_topics": list(bridge_preview.get("directive_topics", [])),
            "selected_witness_indices": list(bridge_preview.get("selected_witness_indices", [])),
            "retained_second_target_gate": bridge_packet.get("retained_second_target_gate", ""),
        },
        "skill_improver_result": skill_improver_result,
        "proof_completed": proof_completed,
        "recommended_next_step": recommended_next_step,
        "recommended_actions": [
            "Keep this slice metadata-only and dry-run only.",
            "Retain the general skill-improver gate and the one-proven-target hold.",
            "Do not widen this proof into graph backfill, second-target admission, runtime import, or live learning.",
        ],
        "non_goals": list(DEFAULT_NON_GOALS),
        "issues": issues,
    }

    packet = {
        "schema": "A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_PROOF_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": report["status"],
        "audit_only": True,
        "nonoperative": True,
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "selected_target_skill_id": selected_target_skill_id,
        "owner_skill_id": OWNER_SKILL_ID,
        "allow_metadata_only_context_consumer_proof": proof_completed,
        "allow_first_target_only": True,
        "allow_first_target_context_packet_only": True,
        "allow_write": False,
        "retain_general_gate": True,
        "allow_second_target_context": False,
        "allow_live_learning_claims": False,
        "allow_runtime_import_claims": False,
        "allow_graph_backfill_claims": False,
        "do_not_promote": True,
        "recommended_next_step": recommended_next_step,
        "issues": list(issues),
    }
    return report, packet


def run_a2_next_state_first_target_context_consumer_proof(
    ctx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report_path = _resolve_output_path(root, ctx.get("report_json_path"), REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("report_md_path"), REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), PACKET_JSON)

    report, packet = build_a2_next_state_first_target_context_consumer_proof_report(root, ctx)
    _write_json(report_path, report)
    _write_json(packet_path, packet)
    _write_text(markdown_path, _render_markdown(report, packet))

    return {
        "status": report["status"],
        "proof_completed": report["proof_completed"],
        "recommended_next_step": report["recommended_next_step"],
        "report_json_path": str(report_path),
        "report_md_path": str(markdown_path),
        "packet_path": str(packet_path),
    }


if __name__ == "__main__":
    result = run_a2_next_state_first_target_context_consumer_proof({"repo_root": REPO_ROOT})
    print(json.dumps(result, indent=2, sort_keys=True))
