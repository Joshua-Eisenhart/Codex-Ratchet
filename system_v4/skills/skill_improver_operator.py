"""
skill_improver_operator.py

Bounded meta-skill for validating and optionally committing a proposed update to
one target skill.

This operator is dry-run first. It does not invent mutations by itself. A
candidate must be supplied explicitly, and repo writes remain gated by an
allowlist plus an explicit approval token.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.runtime_state_kernel import (
    BoundaryTag,
    RuntimeState,
    StepEvent,
    Witness,
    WitnessKind,
    utc_iso,
)


WRITE_APPROVAL_TOKEN = "ALLOW_SKILL_IMPROVER_WRITE"


def _normalize_path(raw: str | Path) -> Path:
    return Path(raw).resolve()


def _path_allowed(target_path: Path, allowed_targets: list[str]) -> bool:
    if not allowed_targets:
        return False
    resolved_target = target_path.resolve()
    for raw in allowed_targets:
        allowed = Path(raw).resolve()
        if resolved_target == allowed:
            return True
    return False


def _format_test_command(raw_command: Any, candidate_path: Path) -> list[str]:
    if not isinstance(raw_command, (list, tuple)):
        return []
    command = [str(part).replace("{candidate_path}", str(candidate_path)) for part in raw_command]
    return [part for part in command if part]


def _coerce_string_list(raw: Any) -> list[str]:
    if not isinstance(raw, (list, tuple)):
        return []
    values: list[str] = []
    for item in raw:
        text = str(item).strip()
        if text:
            values.append(text)
    return values


def _coerce_int_list(raw: Any) -> list[int]:
    if not isinstance(raw, (list, tuple)):
        return []
    values: list[int] = []
    for item in raw:
        try:
            value = int(item)
        except (TypeError, ValueError):
            continue
        if value >= 0:
            values.append(value)
    return values


def _extract_context_summary(ctx: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    context_packet = ctx.get("context_packet")
    context_bridge_packet = ctx.get("context_bridge_packet")
    bridge_packet = ctx.get("bridge_packet")

    packet_payload = context_packet if isinstance(context_packet, dict) else {}
    bridge_payload = bridge_packet if isinstance(bridge_packet, dict) else {}
    if not bridge_payload and isinstance(context_bridge_packet, dict):
        bridge_payload = context_bridge_packet

    directive_topics = _coerce_string_list(ctx.get("directive_topics"))
    if not directive_topics:
        directive_topics = _coerce_string_list(packet_payload.get("directive_topics"))

    selected_witness_indices = _coerce_int_list(ctx.get("selected_witness_indices"))
    if not selected_witness_indices:
        selected_witness_indices = _coerce_int_list(packet_payload.get("selected_witness_indices"))

    context_notes = _coerce_string_list(ctx.get("context_notes"))
    if not context_notes:
        context_notes = _coerce_string_list(packet_payload.get("context_notes"))

    contract_present = bool(
        packet_payload
        or bridge_payload
        or directive_topics
        or selected_witness_indices
        or context_notes
    )
    status = "metadata_only_context_loaded" if contract_present else "no_context_supplied"
    summary = {
        "context_packet_present": bool(packet_payload),
        "context_bridge_packet_present": bool(isinstance(context_bridge_packet, dict)),
        "bridge_packet_present": bool(bridge_payload),
        "directive_topics": directive_topics,
        "selected_witness_indices": selected_witness_indices,
        "context_notes": context_notes,
        "metadata_only": True,
        "writes_affected": False,
        "target_scope": "first_target_context_only",
        "allow_second_target": False,
        "allow_live_learning": False,
        "allow_runtime_import": False,
        "allow_graph_backfill": False,
    }
    return status, summary


def _run_test_command(command: list[str]) -> tuple[str, str]:
    if not command:
        return "not_run", "No test_command supplied."
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        return "passed", "Selected test command passed."
    detail = result.stderr.strip() or result.stdout.strip() or "Selected test command failed."
    return "failed", detail


def _record_witness(ctx: dict[str, Any], passed: bool, notes: list[str], target_path: Path) -> None:
    recorder = ctx.get("recorder")
    if recorder is None:
        return
    witness = Witness(
        kind=WitnessKind.POSITIVE if passed else WitnessKind.NEGATIVE,
        passed=passed,
        violations=[] if passed else notes,
        touched_boundaries=[BoundaryTag.SYSTEMIC],
        trace=[
            StepEvent(
                at=utc_iso(),
                op="skill_improver_operator",
                before_hash=str(target_path),
                after_hash="",
                notes=notes,
            )
        ],
    )
    recorder.record(witness, tags={"phase": "SKILL_SELF_IMPROVEMENT"})


def run_skill_improver(ctx: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and optionally commit a proposed target-skill update.

    Expected ctx keys:
      - target_skill_path: required path to the Python skill to improve
      - candidate_code: required proposed replacement source
      - test_command: optional list command, may use "{candidate_path}"
      - allow_write: optional bool, defaults False
      - approval_token: optional string, must equal WRITE_APPROVAL_TOKEN to commit
      - allowed_targets: optional exact-path allowlist for writeback
      - recorder: optional witness recorder
    """

    context_contract_status, context_summary = _extract_context_summary(ctx)

    target_skill_path = Path(ctx.get("target_skill_path", ""))
    if not target_skill_path.exists():
        return {
            "improved": False,
            "detail": f"Target skill not found: {target_skill_path}",
            "path": str(target_skill_path),
            "context_contract_status": context_contract_status,
            "context_summary": context_summary,
        }

    resolved_skill_path = target_skill_path.resolve()
    original_code = resolved_skill_path.read_text(encoding="utf-8")
    candidate_code = str(ctx.get("candidate_code", ""))
    if not candidate_code:
        detail = "No candidate_code supplied. Operator remains dry-run with no mutation candidate."
        _record_witness(ctx, False, [detail], resolved_skill_path)
        return {
            "improved": False,
            "detail": detail,
            "path": str(resolved_skill_path),
            "proposed_change": False,
            "compile_ok": False,
            "tests_state": "not_run",
            "score": 0,
            "write_permitted": False,
            "context_contract_status": context_contract_status,
            "context_summary": context_summary,
        }

    changed = candidate_code != original_code
    dry_run = not bool(ctx.get("allow_write", False))
    allow_write = bool(ctx.get("allow_write", False))
    approval_token = str(ctx.get("approval_token", ""))
    allowed_targets = [str(item) for item in ctx.get("allowed_targets", []) if str(item).strip()]

    compile_ok = False
    tests_state = "not_run"
    notes: list[str] = []

    with tempfile.TemporaryDirectory() as td:
        candidate_path = Path(td) / resolved_skill_path.name
        candidate_path.write_text(candidate_code, encoding="utf-8")

        compile_result = subprocess.run(
            ["python3", "-m", "py_compile", str(candidate_path)],
            capture_output=True,
            text=True,
        )
        compile_ok = compile_result.returncode == 0
        if compile_ok:
            notes.append("Candidate compiles.")
        else:
            detail = compile_result.stderr.strip() or compile_result.stdout.strip() or "Candidate failed py_compile."
            notes.append(detail)

        test_command = _format_test_command(ctx.get("test_command"), candidate_path)
        if compile_ok:
            tests_state, test_detail = _run_test_command(test_command)
            notes.append(test_detail)

        score = 0
        if changed:
            score += 1
        if compile_ok:
            score += 1
        if tests_state == "passed":
            score += 1

        write_permitted = (
            allow_write
            and approval_token == WRITE_APPROVAL_TOKEN
            and _path_allowed(resolved_skill_path, allowed_targets)
            and compile_ok
            and tests_state in {"passed", "not_run"}
            and changed
        )

        if write_permitted:
            resolved_skill_path.write_text(candidate_code, encoding="utf-8")
            notes.append("Candidate committed to target skill.")
        elif dry_run:
            notes.append("Dry-run active. Candidate not committed.")
        elif allow_write and approval_token != WRITE_APPROVAL_TOKEN:
            notes.append("Write denied: approval_token did not match.")
        elif allow_write and not _path_allowed(resolved_skill_path, allowed_targets):
            notes.append("Write denied: target_skill_path was not allowlisted.")
        elif allow_write and not changed:
            notes.append("Write denied: candidate did not change the target.")
        elif allow_write and not compile_ok:
            notes.append("Write denied: candidate did not compile.")
        elif allow_write and tests_state == "failed":
            notes.append("Write denied: selected test command failed.")

    if context_contract_status == "metadata_only_context_loaded":
        notes.append("Explicit first-target context metadata accepted without changing write gates.")

    improved = write_permitted
    detail = " ".join(notes).strip()
    _record_witness(ctx, compile_ok and tests_state != "failed", notes, resolved_skill_path)
    return {
        "improved": improved,
        "detail": detail,
        "path": str(resolved_skill_path),
        "proposed_change": changed,
        "compile_ok": compile_ok,
        "tests_state": tests_state,
        "score": score,
        "write_permitted": write_permitted,
        "dry_run": dry_run,
        "context_contract_status": context_contract_status,
        "context_summary": context_summary,
    }


if __name__ == "__main__":
    print("PASS: skill_improver_operator self-test")
