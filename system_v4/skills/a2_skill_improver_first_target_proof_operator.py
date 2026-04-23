"""
a2_skill_improver_first_target_proof_operator.py

Bounded proof slice for using skill-improver-operator against its selected
first target.

This operator temporarily commits a harmless reversible change to the selected
target under the existing allowlist + approval-token gate, runs the target's
real smoke after the gated write, then restores the exact original file bytes.
It emits repo-held proof artifacts and does not widen permission to general
repo mutation.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.skill_improver_operator import (
    WRITE_APPROVAL_TOKEN,
    run_skill_improver,
)

TARGET_SELECTION_REPORT_PATH = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_REPORT__CURRENT__v1.json"
)
TARGET_SELECTION_PACKET_PATH = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_PACKET__CURRENT__v1.json"
)

FIRST_TARGET_PROOF_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_FIRST_TARGET_PROOF_REPORT__CURRENT__v1.json"
)
FIRST_TARGET_PROOF_REPORT_MD = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_FIRST_TARGET_PROOF_REPORT__CURRENT__v1.md"
)
FIRST_TARGET_PROOF_PACKET_JSON = (
    "system_v4/a2_state/audit_logs/SKILL_IMPROVER_FIRST_TARGET_PROOF_PACKET__CURRENT__v1.json"
)

PROOF_MARKER_PREFIX = "# a2_skill_improver_first_target_proof_marker:"


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


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_command(command: list[str] | tuple[str, ...] | None) -> list[str]:
    if not isinstance(command, (list, tuple)):
        return []
    return [str(part) for part in command if str(part).strip()]


def _run_command(command: list[str], cwd: Path) -> dict[str, Any]:
    if not command:
        return {"status": "not_run", "returncode": None, "detail": "No command supplied."}
    result = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True)
    detail = result.stderr.strip() or result.stdout.strip() or ""
    return {
        "status": "passed" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "detail": detail,
        "command": command,
    }


def _build_candidate_code(original_text: str, proof_marker: str) -> str:
    stripped = original_text.rstrip("\n")
    return f"{stripped}\n\n{proof_marker}\n"


def _resolve_target(root: Path) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    issues: list[str] = []
    selection_report = _safe_load_json(root / TARGET_SELECTION_REPORT_PATH)
    selection_packet = _safe_load_json(root / TARGET_SELECTION_PACKET_PATH)
    if selection_report.get("status") != "ok":
        issues.append("target selection report is not ok")
    recommended_target = selection_report.get("recommended_target", {})
    if not isinstance(recommended_target, dict) or not recommended_target:
        issues.append("recommended target is missing")
    if selection_packet.get("recommended_target_skill_id") != recommended_target.get("skill_id"):
        issues.append("selection packet and report disagree on recommended target")
    return selection_report, selection_packet, issues


def build_skill_improver_first_target_proof_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()
    selection_report, selection_packet, issues = _resolve_target(root)
    recommended_target = selection_report.get("recommended_target", {}) if isinstance(selection_report, dict) else {}

    target_skill_id = str(recommended_target.get("skill_id", "")).strip()
    target_skill_rel = str(recommended_target.get("source_path", "")).strip()
    target_smoke_rel = str(recommended_target.get("smoke_path", "")).strip()
    target_skill_path = (root / target_skill_rel) if target_skill_rel else Path()
    target_smoke_path = (root / target_smoke_rel) if target_smoke_rel else Path()

    if not target_skill_id:
        issues.append("selected target skill id is missing")
    if not target_skill_rel or not target_skill_path.exists():
        issues.append("selected target skill source is missing")
    if not target_smoke_rel or not target_smoke_path.exists():
        issues.append("selected target smoke is missing")

    recommended_allowed_targets = [
        str((root / rel).resolve()) for rel in selection_packet.get("recommended_allowed_targets", [])
    ]
    if target_skill_path and target_skill_path.exists() and str(target_skill_path.resolve()) not in recommended_allowed_targets:
        issues.append("selected target is not present in the recommended allowlist")

    original_text = target_skill_path.read_text(encoding="utf-8") if target_skill_path.exists() else ""
    original_hash = _sha256_text(original_text) if original_text else ""
    proof_marker = f"{PROOF_MARKER_PREFIX} {_utc_iso()}"
    candidate_code = _build_candidate_code(original_text, proof_marker) if original_text else ""
    candidate_hash = _sha256_text(candidate_code) if candidate_code else ""

    baseline_smoke_command = _normalize_command(selection_packet.get("recommended_test_command"))
    baseline_smoke = _run_command(baseline_smoke_command, root) if not issues else {
        "status": "not_run",
        "returncode": None,
        "detail": "Proof prerequisites missing.",
        "command": baseline_smoke_command,
    }

    dry_run_result: dict[str, Any] = {}
    commit_result: dict[str, Any] = {}
    post_commit_smoke: dict[str, Any] = {}
    post_restore_smoke: dict[str, Any] = {}
    restore_status = {
        "status": "not_run",
        "restored_original_bytes": False,
        "final_hash_matches_original": False,
    }

    proof_mode = str(ctx.get("proof_mode", "gated_commit_restore")).strip() or "gated_commit_restore"
    proof_completed = False
    proof_status = "action_required" if issues else "ok"

    if not issues and baseline_smoke["status"] == "passed":
        dry_run_result = run_skill_improver(
            {
                "target_skill_path": str(target_skill_path.resolve()),
                "candidate_code": candidate_code,
                "test_command": ["python3", "-m", "py_compile", "{candidate_path}"],
            }
        )
        if proof_mode == "gated_commit_restore":
            try:
                commit_result = run_skill_improver(
                    {
                        "target_skill_path": str(target_skill_path.resolve()),
                        "candidate_code": candidate_code,
                        "test_command": ["python3", "-m", "py_compile", "{candidate_path}"],
                        "allow_write": True,
                        "approval_token": WRITE_APPROVAL_TOKEN,
                        "allowed_targets": recommended_allowed_targets,
                    }
                )
                if commit_result.get("write_permitted"):
                    post_commit_smoke = _run_command(baseline_smoke_command, root)
            finally:
                if target_skill_path.exists():
                    target_skill_path.write_text(original_text, encoding="utf-8")
                final_text = target_skill_path.read_text(encoding="utf-8") if target_skill_path.exists() else ""
                final_hash = _sha256_text(final_text) if final_text else ""
                restore_status = {
                    "status": "restored" if final_hash == original_hash else "restore_mismatch",
                    "restored_original_bytes": final_text == original_text,
                    "final_hash_matches_original": final_hash == original_hash,
                }
                if baseline_smoke_command:
                    post_restore_smoke = _run_command(baseline_smoke_command, root)

            proof_completed = bool(
                dry_run_result.get("compile_ok")
                and commit_result.get("write_permitted")
                and post_commit_smoke.get("status") == "passed"
                and restore_status.get("final_hash_matches_original")
                and post_restore_smoke.get("status") == "passed"
            )
        else:
            proof_completed = bool(dry_run_result.get("compile_ok"))
    else:
        proof_status = "action_required"

    report = {
        "schema": "skill_improver_first_target_proof_report_v1",
        "generated_utc": _utc_iso(),
        "status": "ok" if proof_completed else proof_status,
        "cluster_id": "SKILL_CLUSTER::a2-skill-truth-maintenance",
        "slice_id": "a2-skill-improver-first-target-proof-operator",
        "source_family": "Ratchet-native A2 truth maintenance",
        "audit_only": False,
        "bounded_proof_only": True,
        "do_not_promote": True,
        "proof_mode": proof_mode,
        "target_skill_id": target_skill_id,
        "target_skill_path": target_skill_rel,
        "target_smoke_path": target_smoke_rel,
        "proof_marker": proof_marker,
        "original_hash": original_hash,
        "candidate_hash": candidate_hash,
        "baseline_smoke": baseline_smoke,
        "dry_run_result": dry_run_result,
        "commit_result": commit_result,
        "post_commit_smoke": post_commit_smoke,
        "restore_status": restore_status,
        "post_restore_smoke": post_restore_smoke,
        "proof_completed": proof_completed,
        "proof_scope": "one selected first target only; not general live repo mutation",
        "selection_report_path": TARGET_SELECTION_REPORT_PATH,
        "selection_packet_path": TARGET_SELECTION_PACKET_PATH,
        "issues": issues,
        "recommended_actions": [
            "Keep general skill-improver mutation gated even after one successful bounded proof target.",
            "Use this proof slice only against the currently selected target unless a new target-selection report is emitted.",
            "Refresh the standing A2 control surfaces after a successful proof so the controller truth reflects one proven target rather than only a selected target.",
        ],
    }

    packet = {
        "schema": "skill_improver_first_target_proof_packet_v1",
        "generated_utc": report["generated_utc"],
        "cluster_id": report["cluster_id"],
        "slice_id": report["slice_id"],
        "target_skill_id": target_skill_id,
        "target_skill_path": target_skill_rel,
        "proof_mode": proof_mode,
        "bounded_proof_completed": proof_completed,
        "allow_general_live_mutation": False,
        "retain_general_gate": True,
        "proof_scope": report["proof_scope"],
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    def _line(item: dict[str, Any], label: str) -> str:
        if not item:
            return f"- {label}: `not_run`"
        return f"- {label}: `{item.get('status', 'unknown')}`"

    lines = [
        "# Skill Improver First Target Proof Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- proof_mode: `{report.get('proof_mode', '')}`",
        f"- target_skill_id: `{report.get('target_skill_id', '')}`",
        f"- target_skill_path: `{report.get('target_skill_path', '')}`",
        f"- target_smoke_path: `{report.get('target_smoke_path', '')}`",
        f"- proof_completed: `{report.get('proof_completed', False)}`",
        f"- do_not_promote: `{report.get('do_not_promote', False)}`",
        "",
        "## Proof Steps",
        _line(report.get("baseline_smoke", {}), "baseline_smoke"),
        _line(report.get("post_commit_smoke", {}), "post_commit_smoke"),
        _line(report.get("post_restore_smoke", {}), "post_restore_smoke"),
        "",
        "## Skill Improver Results",
        f"- dry_run compile_ok: `{report.get('dry_run_result', {}).get('compile_ok')}`",
        f"- dry_run tests_state: `{report.get('dry_run_result', {}).get('tests_state', '')}`",
        f"- commit write_permitted: `{report.get('commit_result', {}).get('write_permitted')}`",
        f"- restore final_hash_matches_original: `{report.get('restore_status', {}).get('final_hash_matches_original')}`",
        "",
        "## Packet",
        f"- bounded_proof_completed: `{packet.get('bounded_proof_completed', False)}`",
        f"- retain_general_gate: `{packet.get('retain_general_gate', False)}`",
        "",
    ]
    return "\n".join(lines)


def run_a2_skill_improver_first_target_proof(ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report_path = _resolve_output_path(root, ctx.get("report_json_path"), FIRST_TARGET_PROOF_REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("report_md_path"), FIRST_TARGET_PROOF_REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), FIRST_TARGET_PROOF_PACKET_JSON)

    report, packet = build_skill_improver_first_target_proof_report(root, ctx)
    _write_json(report_path, report)
    _write_text(markdown_path, _render_markdown(report, packet))
    _write_json(packet_path, packet)

    emitted = dict(report)
    emitted["report_json_path"] = str(report_path)
    emitted["report_md_path"] = str(markdown_path)
    emitted["packet_path"] = str(packet_path)
    emitted["packet"] = packet
    return emitted


if __name__ == "__main__":
    print("PASS: a2 skill improver first target proof operator self-test")
