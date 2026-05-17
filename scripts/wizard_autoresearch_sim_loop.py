#!/usr/bin/env python3
"""Bounded Wizard/autoresearch sim loop with strict sim-admission boundaries.

This loop keeps "accepted QIT/engine evidence only from controller-read canonical artifacts".
It never treats runner output, Claude prose, or artifact proxies as sim promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_INDEX = REPO_ROOT / "system_v5" / "evidence" / "qit_engine_evidence_index.json"


def run(command: list[str], *, cwd: Path = REPO_ROOT) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    return {"command": command, "returncode": proc.returncode, "stdout": proc.stdout[-4000:]}


def qit_evidence_index_command(evidence_index: Path, *, skip_external_scan: bool = False) -> list[str]:
    command = [sys.executable, "scripts/qit_engine_evidence_index.py", "--out", str(evidence_index)]
    if skip_external_scan:
        command.append("--skip-external-scan")
    return command


def evidence_counts(evidence_index: Path | None = None) -> dict[str, Any]:
    evidence_index = evidence_index or EVIDENCE_INDEX
    if not evidence_index.exists():
        return {"accepted": 0, "admitted_micro_entries": 0, "missing_or_invalid_admission": 0, "next_acceptance_targets": []}
    payload = json.loads(evidence_index.read_text(encoding="utf-8"))
    summary = payload.get("summary") or {}
    return {
        "accepted": int(summary.get("accepted") or 0),
        "admitted_micro_entries": int(summary.get("admitted_micro_entries") or 0),
        "missing_or_invalid_admission": int(summary.get("missing_or_invalid_admission") or 0),
        "next_acceptance_targets": payload.get("next_acceptance_targets") or [],
    }


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def argv_sha256(argv: list[str] | None) -> str:
    payload = json.dumps(argv or [], separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stage_gate_summary(stage_gate: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(stage_gate.get("stdout") or "{}")
    except json.JSONDecodeError:
        return {
            "returncode": stage_gate.get("returncode"),
            "parse_error": True,
            "status": "parse_error",
            "active_stage": None,
            "all_pass": False,
            "allowed_claims": [],
            "blocked_claims": [],
        }
    decisions = payload.get("decisions") or {}
    allowed_claims = sorted(claim for claim, item in decisions.items() if item.get("allowed"))
    blocked_claims = sorted(claim for claim, item in decisions.items() if not item.get("allowed"))
    return {
        "returncode": stage_gate.get("returncode"),
        "parse_error": False,
        "status": "passed" if payload.get("all_pass") else "failed",
        "active_stage": payload.get("active_stage"),
        "all_pass": bool(payload.get("all_pass")),
        "allowed_claims": allowed_claims,
        "blocked_claims": blocked_claims,
    }


def first_actionable_acceptance_target(targets: list[dict[str, Any]]) -> dict[str, Any] | None:
    for target in targets:
        action = str(target.get("next_action") or "")
        if action and not action.startswith("do_not_promote"):
            return target
    return targets[0] if targets else None


def qit_evidence_summary(evidence_index: Path) -> dict[str, Any]:
    if not evidence_index.exists():
        return {
            "exists": False,
            "parse_error": False,
            "status": "missing_index",
            "status_reason": "missing_index",
            "operational_status": "missing_index",
            "summary": {},
            "scanned_result_count": 0,
            "qit_signal_result_count": 0,
            "qit_signal_filter": {"tokens": [], "fields": []},
            "scan_sample": {"scanned_result_files": [], "qit_signal_result_files": [], "sample_limit": 20},
            "out_of_scope_qit_result_scan": {
                "status": "missing_index",
                "external_result_count": 0,
                "external_qit_signal_count": 0,
                "sample": [],
            },
            "next_acceptance_target_count": 0,
        }
    try:
        payload = json.loads(evidence_index.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "exists": True,
            "parse_error": True,
            "status": "invalid_json",
            "status_reason": "invalid_json",
            "operational_status": "invalid_json",
            "summary": {},
            "scanned_result_count": 0,
            "qit_signal_result_count": 0,
            "qit_signal_filter": {"tokens": [], "fields": []},
            "scan_sample": {"scanned_result_files": [], "qit_signal_result_files": [], "sample_limit": 20},
            "out_of_scope_qit_result_scan": {
                "status": "invalid_json",
                "external_result_count": 0,
                "external_qit_signal_count": 0,
                "sample": [],
            },
            "next_acceptance_target_count": 0,
        }
    operational_status = payload.get("operational_status")
    summary = payload.get("summary") or {}
    external_scan = payload.get("out_of_scope_qit_result_scan") or {}
    triage = external_scan.get("triage") or {}
    next_acceptance_targets = payload.get("next_acceptance_targets") or []
    return {
        "exists": True,
        "parse_error": False,
        "status": operational_status,
        "status_reason": payload.get("status_reason"),
        "operational_status": operational_status,
        "summary": summary,
        "scanned_result_count": summary.get("scanned_result_count", 0),
        "qit_signal_result_count": summary.get("qit_signal_result_count", 0),
        "qit_signal_filter": payload.get("qit_signal_filter") or {"tokens": [], "fields": []},
        "scan_sample": payload.get("scan_sample")
        or {"scanned_result_files": [], "qit_signal_result_files": [], "sample_limit": 20},
        "out_of_scope_qit_result_scan": external_scan
        or {
            "status": "not_reported",
            "external_result_count": 0,
            "external_qit_signal_count": 0,
            "sample": [],
        },
        "out_of_scope_qit_triage_summary": {
            "bucket_counts": triage.get("bucket_counts") or {},
            "provisional_rerun_target_count": int(triage.get("provisional_rerun_target_count") or 0),
            "first_provisional_target": (triage.get("provisional_rerun_targets") or [None])[0],
            "triage_boundary": triage.get("triage_boundary"),
        },
        "next_acceptance_target_count": len(next_acceptance_targets),
        "next_acceptance_targets": next_acceptance_targets,
        "first_next_acceptance_target": first_actionable_acceptance_target(next_acceptance_targets),
    }


def helper_process_summary(helper: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(helper.get("stdout") or "{}")
    except json.JSONDecodeError:
        return {
            "returncode": helper.get("returncode"),
            "parse_error": True,
            "status": "parse_error",
            "all_pass": False,
            "helper_process_count": None,
            "guard": None,
        }
    all_pass = bool(payload.get("all_pass"))
    return {
        "returncode": helper.get("returncode"),
        "parse_error": False,
        "status": "passed" if all_pass else "failed",
        "all_pass": all_pass,
        "helper_process_count": payload.get("helper_process_count"),
        "guard": payload.get("guard"),
    }


def manifest_artifact_status(iteration_manifest: list[dict[str, Any]]) -> dict[str, Any]:
    path_keys = ["preflight_receipt", "council_receipt", "goal_loop_receipt", "premortem", "qit_index_stdout", "stage_gate_stdout"]
    missing: list[dict[str, Any]] = []
    checked = 0
    for item in iteration_manifest:
        for key in path_keys:
            value = item.get(key)
            if not value:
                continue
            checked += 1
            if not Path(str(value)).exists():
                missing.append({"iteration": item.get("iteration"), "field": key, "path": value})
    if checked == 0:
        status = "not_started"
    elif missing:
        status = "missing_artifacts"
    else:
        status = "complete"
    return {
        "status": status,
        "checked_paths": checked,
        "missing_paths": len(missing),
        "missing": missing[:20],
    }


def run_classification(run_status: str, latest_decision: dict[str, Any], iteration_manifest: list[dict[str, Any]]) -> str:
    if not iteration_manifest:
        return "initialized"
    if latest_decision.get("runner_launch_allowed"):
        return "runner_launch_allowed"
    if latest_decision.get("blockers"):
        return "blocked"
    if run_status == "complete":
        return "complete_no_blockers"
    return "in_progress_no_blockers"


def manifest_next_action(latest_decision: dict[str, Any], iteration_manifest: list[dict[str, Any]]) -> str:
    blockers = set(latest_decision.get("blockers", []))
    if "accepted_qit_engine_evidence_zero" in blockers:
        latest_iteration = iteration_manifest[-1] if iteration_manifest else {}
        qit_summary = latest_iteration.get("qit_evidence_summary") or {}
        first_target = qit_summary.get("first_next_acceptance_target")
        if first_target:
            next_action = str(first_target.get("next_action") or "")
            if next_action == "create_or_repair_wizard_sim_admission":
                return "create_or_repair_wizard_sim_admission"
            return next_action or "admit_or_repair_micro_qit_evidence_before_runner_launch"
        triage_summary = qit_summary.get("out_of_scope_qit_triage_summary") or {}
        bucket_counts = triage_summary.get("bucket_counts") or {}
        if bucket_counts.get("source_bound_repaired_source_rerun_candidate"):
            return "rerun_repaired_source_under_canonical_micro_result_surface"
        if bucket_counts.get("source_bound_contract_repair_candidate"):
            return "repair_source_bound_qit_contract_then_rerun_canonical_micro_result"
        if bucket_counts.get("source_bound_micro_rerun_candidate"):
            return "rerun_source_bound_qit_micro_result_then_create_strict_admission"
        external_scan = qit_summary.get("out_of_scope_qit_result_scan") or {}
        if int(external_scan.get("external_qit_signal_count") or 0) > 0:
            return "triage_out_of_scope_qit_receipts_then_rerun_or_admit_micro_qit_evidence"
        return "repair_or_admit_micro_qit_evidence_before_runner_launch"
    matrix_blockers = sorted(blocker for blocker in blockers if blocker.startswith("wizard_matrix_failed:"))
    if matrix_blockers:
        return f"repair_wizard_matrix_route:{matrix_blockers[0].split(':', 1)[1]}"
    if latest_decision.get("runner_launch_allowed"):
        return "runner_launch_allowed"
    if latest_decision.get("runner_launch_blockers"):
        return "repair_runner_launch_blockers"
    if not iteration_manifest:
        return "continue_first_iteration"
    if blockers:
        return "repair_blockers_before_continuing"
    return "continue_next_iteration"


def manifest_preflight_summary(iteration_manifest: list[dict[str, Any]]) -> dict[str, Any]:
    if not iteration_manifest:
        return {
            "status": "not_started",
            "latest_all_pass": None,
            "all_completed_pass": None,
            "completed_count": 0,
            "failed_iterations": [],
        }
    failed_iterations = [item.get("iteration") for item in iteration_manifest if not item.get("preflight_all_pass")]
    return {
        "status": "failed" if failed_iterations else "passed",
        "latest_all_pass": bool(iteration_manifest[-1].get("preflight_all_pass")),
        "all_completed_pass": not failed_iterations,
        "completed_count": len(iteration_manifest),
        "failed_iterations": failed_iterations,
    }


def manifest_matrix_summary(iteration_manifest: list[dict[str, Any]]) -> dict[str, Any]:
    if not iteration_manifest:
        return {
            "status": "not_started",
            "latest_route_count": 0,
            "latest_all_accepted": None,
            "latest_routes": {},
            "completed_count": 0,
            "attempted_count": 0,
            "skipped_count": 0,
            "failed_iterations": [],
        }
    latest_routes = iteration_manifest[-1].get("matrix_route_summaries") or {}
    attempted_items = [
        item
        for item in iteration_manifest
        if item.get("matrix_route_count", 0) > 0 or bool(item.get("matrix_route_summaries"))
    ]
    failed_iterations = [item.get("iteration") for item in attempted_items if item.get("matrix_all_accepted") is False]
    if not attempted_items:
        status = "not_attempted"
    elif failed_iterations:
        status = "failed"
    elif all(item.get("matrix_all_accepted") is True for item in attempted_items):
        status = "accepted"
    else:
        status = "incomplete"
    return {
        "status": status,
        "latest_route_count": len(latest_routes),
        "latest_all_accepted": iteration_manifest[-1].get("matrix_all_accepted"),
        "latest_routes": latest_routes,
        "completed_count": len(iteration_manifest),
        "attempted_count": len(attempted_items),
        "skipped_count": len(iteration_manifest) - len(attempted_items),
        "failed_iterations": failed_iterations,
    }


def manifest_runner_summary(runner_requested: bool, latest_decision: dict[str, Any]) -> dict[str, Any]:
    launch_blockers = latest_decision.get("runner_launch_blockers", [])
    if not runner_requested:
        next_required_step = "request_runner_when_admissible"
    elif latest_decision.get("runner_launch_allowed"):
        next_required_step = "run_parallel_admitted_workers"
    elif "accepted_qit_engine_evidence_zero" in launch_blockers:
        next_required_step = "admit_or_repair_micro_qit_evidence"
    elif launch_blockers:
        next_required_step = "repair_runner_launch_blockers"
    elif runner_requested:
        next_required_step = "continue_runner_preflight"
    else:
        next_required_step = "request_runner_when_admissible"
    return {
        "requested": bool(runner_requested),
        "launch_allowed": bool(latest_decision.get("runner_launch_allowed")),
        "status": latest_decision.get("runner_status"),
        "launch_blockers": launch_blockers,
        "next_required_step": next_required_step,
    }


def manifest_admission_summary(latest_decision: dict[str, Any], latest_iteration: dict[str, Any]) -> dict[str, Any]:
    stage_summary = latest_iteration.get("stage_gate_summary") or {}
    qit_summary = latest_iteration.get("qit_evidence_summary") or {}
    qit_counts = qit_summary.get("summary") or {}
    external_scan = qit_summary.get("out_of_scope_qit_result_scan") or {}
    triage_summary = qit_summary.get("out_of_scope_qit_triage_summary") or {}
    bucket_counts = triage_summary.get("bucket_counts") or {}
    first_provisional_target = triage_summary.get("first_provisional_target")
    next_acceptance_targets = qit_summary.get("next_acceptance_targets") or []
    first_next_acceptance_target = qit_summary.get("first_next_acceptance_target")
    external_qit_signal_count = int(external_scan.get("external_qit_signal_count") or 0)
    accepted_qit_entries = qit_counts.get("accepted")
    decision_blockers = latest_decision.get("blockers", [])
    runner_launch_blockers = latest_decision.get("runner_launch_blockers", [])
    qit_zero_blocked = "accepted_qit_engine_evidence_zero" in set(decision_blockers + runner_launch_blockers)
    if not latest_iteration:
        status = "not_started"
    elif stage_summary.get("all_pass") is False:
        status = "stage_gate_failed"
    elif accepted_qit_entries == 0 or qit_zero_blocked:
        status = "blocked_no_accepted_qit_entries"
    elif latest_decision.get("runner_launch_allowed"):
        status = "runner_launch_allowed"
    elif latest_decision.get("runner_launch_blockers") or latest_decision.get("blockers"):
        status = "blocked"
    else:
        status = "ready_for_next_micro_step"
    if status == "not_started":
        next_required_step = "complete_first_preflight_iteration"
    elif status == "stage_gate_failed":
        next_required_step = "repair_stage_gate_before_runner_launch"
    elif status == "blocked_no_accepted_qit_entries":
        if next_acceptance_targets:
            action = str((first_next_acceptance_target or {}).get("next_action") or "")
            if action == "create_or_repair_wizard_sim_admission":
                next_required_step = "create_or_repair_wizard_sim_admission"
            else:
                next_required_step = action or "admit_or_repair_micro_qit_evidence"
        elif bucket_counts.get("source_bound_repaired_source_rerun_candidate"):
            next_required_step = "rerun_repaired_source_under_canonical_micro_result_surface"
        elif bucket_counts.get("source_bound_contract_repair_candidate"):
            next_required_step = "repair_source_bound_qit_contract_before_rerun"
        elif bucket_counts.get("source_bound_micro_rerun_candidate"):
            next_required_step = "rerun_source_bound_qit_micro_before_admission"
        else:
            next_required_step = (
                "triage_out_of_scope_qit_receipts_for_micro_admission"
                if external_qit_signal_count
                else "admit_or_repair_micro_qit_evidence"
            )
    elif status == "runner_launch_allowed":
        next_required_step = "run_parallel_admitted_workers"
    elif status == "blocked":
        next_required_step = "repair_decision_or_runner_blockers"
    else:
        next_required_step = "continue_next_micro_step"
    return {
        "status": status,
        "next_required_step": next_required_step,
        "active_stage": stage_summary.get("active_stage"),
        "stage_gate_all_pass": stage_summary.get("all_pass"),
        "allowed_claims": stage_summary.get("allowed_claims", []),
        "blocked_claims": stage_summary.get("blocked_claims", []),
        "qit_operational_status": qit_summary.get("operational_status"),
        "accepted_qit_entries": accepted_qit_entries,
        "out_of_scope_qit_signal_result_count": external_qit_signal_count,
        "out_of_scope_qit_scan_status": external_scan.get("status"),
        "out_of_scope_qit_triage_bucket_counts": bucket_counts,
        "out_of_scope_qit_provisional_target_count": triage_summary.get("provisional_rerun_target_count", 0),
        "out_of_scope_qit_first_provisional_target": first_provisional_target,
        "next_acceptance_target_count": len(next_acceptance_targets),
        "first_next_acceptance_target": first_next_acceptance_target,
        "canonical_micro_rerun_command": canonical_micro_rerun_command(first_provisional_target),
        "tmp_admission_rehearsal_command": tmp_admission_rehearsal_command(first_provisional_target),
        "runner_launch_allowed": bool(latest_decision.get("runner_launch_allowed")),
        "runner_launch_blockers": runner_launch_blockers,
        "decision_blockers": decision_blockers,
    }


def canonical_micro_rerun_command(target: dict[str, Any] | None) -> list[str] | None:
    if not target:
        return None
    source_path = target.get("source_path")
    if not source_path:
        return None
    return [
        "env",
        "SIM_RESULTS_DIR=system_v4/probes/a2_state/sim_results",
        "NUMBA_CACHE_DIR=/tmp/codex-numba",
        "MPLCONFIGDIR=/tmp/codex-mpl",
        "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
        str(source_path),
    ]


def tmp_admission_rehearsal_command(target: dict[str, Any] | None) -> list[str] | None:
    if not target:
        return None
    name = str(target.get("name") or "")
    source_path = target.get("source_path")
    if not name or not source_path:
        return None
    result = f"system_v4/probes/a2_state/sim_results/{name}_results.json"
    out_dir = f"/tmp/codex_ratchet_qit_admission_rehearsal_{name}"
    return [
        "make",
        "qit-admission-rehearsal",
        f"BASENAME={name}",
        f"RESULT={result}",
        f"SIM_PATH={source_path}",
        f"OUT_DIR={out_dir}",
    ]


def manifest_controller_consistency(next_action: str, admission_summary: dict[str, Any]) -> dict[str, Any]:
    expected_next_action_by_step = {
        "complete_first_preflight_iteration": "continue_first_iteration",
        "admit_or_repair_micro_qit_evidence": "repair_or_admit_micro_qit_evidence_before_runner_launch",
        "create_or_repair_wizard_sim_admission": "create_or_repair_wizard_sim_admission",
        "triage_out_of_scope_qit_receipts_for_micro_admission": "triage_out_of_scope_qit_receipts_then_rerun_or_admit_micro_qit_evidence",
        "rerun_repaired_source_under_canonical_micro_result_surface": "rerun_repaired_source_under_canonical_micro_result_surface",
        "repair_source_bound_qit_contract_before_rerun": "repair_source_bound_qit_contract_then_rerun_canonical_micro_result",
        "rerun_source_bound_qit_micro_before_admission": "rerun_source_bound_qit_micro_result_then_create_strict_admission",
        "run_parallel_admitted_workers": "runner_launch_allowed",
        "continue_next_micro_step": "continue_next_iteration",
    }
    next_required_step = admission_summary.get("next_required_step")
    expected_next_action = expected_next_action_by_step.get(next_required_step)
    if expected_next_action is None and next_required_step == "repair_decision_or_runner_blockers":
        consistent = next_action.startswith("repair_wizard_matrix_route:") or next_action in {
            "repair_blockers_before_continuing",
            "repair_runner_launch_blockers",
        }
    else:
        consistent = expected_next_action == next_action
    return {
        "next_action_matches_admission": bool(consistent),
        "next_action": next_action,
        "admission_next_required_step": next_required_step,
        "expected_next_action": expected_next_action,
    }


def manifest_claim_boundary_summary(admission_summary: dict[str, Any]) -> dict[str, Any]:
    blocked_claims = admission_summary.get("blocked_claims", [])
    allowed_claims = admission_summary.get("allowed_claims", [])
    promoted_claims: list[str] = []
    return {
        "promoted_claims": promoted_claims,
        "promoted_count": len(promoted_claims),
        "allowed_claims": allowed_claims,
        "blocked_claims": blocked_claims,
        "late_stage_claims_blocked": [
            claim for claim in ["bridge", "axis", "engine", "scientific_coupling", "tier_d"] if claim in blocked_claims
        ],
        "claim_boundary_status": "no_claims_promoted",
    }


def manifest_overall_readiness(
    admission_summary: dict[str, Any],
    controller_consistency: dict[str, Any],
    claim_boundary_summary: dict[str, Any],
    artifact_status: dict[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    if artifact_status.get("status") == "missing_artifacts":
        blockers.append("missing_artifacts")
    if not controller_consistency.get("next_action_matches_admission"):
        blockers.append("controller_admission_drift")
    if claim_boundary_summary.get("promoted_count", 0):
        blockers.append("unexpected_claim_promotion")
    if admission_summary.get("status") == "blocked_no_accepted_qit_entries":
        blockers.append("accepted_qit_engine_evidence_zero")
    elif admission_summary.get("status") == "blocked":
        blockers.extend(admission_summary.get("decision_blockers") or ["admission_blocked"])
    if admission_summary.get("runner_launch_allowed"):
        status = "runner_launch_allowed" if not blockers else "blocked"
    elif blockers:
        status = "blocked"
    elif admission_summary.get("status") == "not_started":
        status = "not_started"
    else:
        status = "ready_for_next_micro_step"
    return {
        "status": status,
        "blockers": blockers,
        "next_required_step": admission_summary.get("next_required_step"),
        "runner_launch_allowed": bool(admission_summary.get("runner_launch_allowed")),
        "components": {
            "artifact_status": artifact_status.get("status"),
            "admission_status": admission_summary.get("status"),
            "controller_consistent": bool(controller_consistency.get("next_action_matches_admission")),
            "claim_boundary_status": claim_boundary_summary.get("claim_boundary_status"),
        },
    }


def write_run_manifest(
    out_dir: Path,
    *,
    run_tag: str,
    run_started_at: str,
    iterations_requested: int,
    evidence_index: Path,
    matrix_enabled: bool,
    gemini_requested: bool,
    haiku_requested: bool,
    runner_requested: bool,
    run_config: dict[str, Any] | None,
    argv: list[str] | None,
    latest_decision: dict[str, Any],
    iteration_manifest: list[dict[str, Any]],
    run_status: str,
) -> Path:
    latest_iteration = iteration_manifest[-1] if iteration_manifest else {}
    next_action = manifest_next_action(latest_decision, iteration_manifest)
    admission_summary = manifest_admission_summary(latest_decision, latest_iteration)
    controller_consistency = manifest_controller_consistency(next_action, admission_summary)
    claim_boundary_summary = manifest_claim_boundary_summary(admission_summary)
    artifact_status = manifest_artifact_status(iteration_manifest)
    manifest = {
        "schema": "wizard_autoresearch_run_manifest",
        "schema_version": 1,
        "run_status": run_status,
        "run_tag": run_tag,
        "run_started_at": run_started_at,
        "manifest_updated_at": datetime.now(timezone.utc).isoformat(),
        "out_dir": str(out_dir),
        "iterations_requested": iterations_requested,
        "iterations_completed": len(iteration_manifest),
        "evidence_index": str(evidence_index),
        "run_mode": {
            "matrix_enabled": matrix_enabled,
            "gemini_requested": bool(gemini_requested),
            "haiku_requested": bool(haiku_requested),
            "runner_requested": bool(runner_requested),
        },
        "run_config": run_config or {},
        "argv": argv or [],
        "argv_sha256": argv_sha256(argv),
        "final_decision": latest_decision,
        "final_blockers": latest_decision.get("blockers", []),
        "run_classification": run_classification(run_status, latest_decision, iteration_manifest),
        "next_action": next_action,
        "runner_summary": manifest_runner_summary(runner_requested, latest_decision),
        "preflight_summary": manifest_preflight_summary(iteration_manifest),
        "matrix_summary": manifest_matrix_summary(iteration_manifest),
        "admission_summary": admission_summary,
        "controller_consistency": controller_consistency,
        "claim_boundary_summary": claim_boundary_summary,
        "artifact_status": artifact_status,
        "overall_readiness": manifest_overall_readiness(
            admission_summary,
            controller_consistency,
            claim_boundary_summary,
            artifact_status,
        ),
        "latest_iteration_summary": {
            "iteration": latest_iteration.get("iteration"),
            "completed_at": latest_iteration.get("completed_at"),
            "blockers": latest_iteration.get("blockers", []),
            "preflight_all_pass": latest_iteration.get("preflight_all_pass"),
            "goal_exit_eligible": latest_iteration.get("goal_exit_eligible"),
            "runner_launch_allowed": latest_iteration.get("runner_launch_allowed"),
            "helper_process_summary": latest_iteration.get("helper_process_summary"),
            "qit_evidence_summary": latest_iteration.get("qit_evidence_summary"),
            "stage_gate_summary": latest_iteration.get("stage_gate_summary"),
        },
        "latest_helper_process_summary": latest_iteration.get("helper_process_summary"),
        "latest_qit_evidence_summary": latest_iteration.get("qit_evidence_summary"),
        "latest_stage_gate_summary": latest_iteration.get("stage_gate_summary"),
        "iterations": iteration_manifest,
    }
    path = out_dir / "run_manifest.json"
    write_json_atomic(path, manifest)
    return path


def write_council_receipts(
    out_dir: Path,
    *,
    iteration: int,
    decision: dict[str, Any],
    premortem: dict[str, Any],
    external: dict[str, Any],
    matrix_receipts: dict[str, Any] | None = None,
    matrix_enabled: bool = True,
    gemini_enabled: bool = False,
    haiku_enabled: bool = False,
) -> Path:
    matrix_receipts = matrix_receipts or {}
    matrix_route_summaries = {
        route: {
            "status": route_receipt.get("status"),
            "counts": route_receipt.get("counts") or {},
            "model_family_statuses": route_receipt.get("model_family_statuses") or {},
            "receipt_path": route_receipt.get("receipt_path"),
        }
        for route, route_receipt in matrix_receipts.items()
    }
    parent_skill_lanes = ["codex-autoresearch", "tool:preflight"]
    disabled_parent_skill_lanes: list[str] = []
    child_skill_lanes = ["tool:helper_process_audit.py"]
    disabled_skill_lanes: list[str] = []
    if matrix_enabled:
        parent_skill_lanes.extend(["premortem", "claude-bridge"])
        child_skill_lanes.extend(["claude-bridge:sonnet-high", "claude-bridge:opus-audit"])
        if gemini_enabled:
            child_skill_lanes.append("gemini:audit")
        else:
            disabled_skill_lanes.append("gemini:audit")
        if haiku_enabled:
            child_skill_lanes.append("claude-bridge:haiku")
        else:
            disabled_skill_lanes.append("claude-bridge:haiku")
    else:
        disabled_parent_skill_lanes.extend(["premortem", "claude-bridge"])
        disabled_skill_lanes.extend(["claude-bridge:sonnet-high", "claude-bridge:opus-audit", "gemini:audit", "claude-bridge:haiku"])
    disabled_parent_skill_lanes.append("cdo")
    matrix_route_statuses = [receipt.get("status") for receipt in matrix_receipts.values()]
    matrix_all_accepted = bool(matrix_route_statuses) and all(status in {"accepted", "completed"} for status in matrix_route_statuses)
    follow_up_route_accepted = any(
        route.startswith("follow") and receipt.get("status") in {"accepted", "completed"}
        for route, receipt in matrix_receipts.items()
    )
    external_follow_up_evidence = bool(
        external.get("follow_up_parent_receipts")
        or external.get("follow_up_child_receipts")
        or external.get("external_native_child_receipts")
    )
    follow_up_evidence_exists = follow_up_route_accepted or external_follow_up_evidence
    failure_route_status = (matrix_receipts.get("failure.premortem") or {}).get("status")
    failure_route_accepted = failure_route_status in {"accepted", "completed"}
    failure_status = "completed" if matrix_enabled and premortem.get("ok") and failure_route_accepted else ("skipped" if not matrix_enabled else "blocked")
    if not matrix_enabled:
        follow_up_status = "deferred"
    elif not matrix_all_accepted:
        follow_up_status = "blocked"
    elif follow_up_evidence_exists:
        follow_up_status = "completed"
    else:
        follow_up_status = "deferred"
    management_parents = ["manager_rerouter", "sim_loop_state_gate"]
    disabled_management_parents: list[str] = []
    if matrix_enabled:
        management_parents.extend(["route_truth_join", "premortem_follow_up_join_gate"])
    else:
        disabled_management_parents.extend(["route_truth_join", "premortem_follow_up_join_gate"])
    receipt = {
        "schema": "wizard_council_receipt",
        "iteration": iteration,
        "run_mode": {
            "matrix_enabled": matrix_enabled,
            "gemini_enabled": gemini_enabled and matrix_enabled,
            "haiku_enabled": haiku_enabled and matrix_enabled,
            "matrix_route_count": len(matrix_receipts),
            "matrix_all_accepted": matrix_all_accepted,
        },
        "councils": ["decision", "failure", "follow_up"],
        "parent_skill_lanes": parent_skill_lanes,
        "disabled_parent_skill_lanes": disabled_parent_skill_lanes,
        "child_skill_lanes": child_skill_lanes,
        "disabled_skill_lanes": disabled_skill_lanes,
        "parent_receipts": {
            "decision": {"status": "completed", "decision": decision},
            "failure": {"status": failure_status, "premortem": premortem},
            "follow_up": {
                "status": follow_up_status,
                "next": decision.get("action"),
                "evidence_required": True,
                "evidence_present": follow_up_evidence_exists,
            },
        },
        "child_receipts": [],
        "management_parents": management_parents,
        "disabled_management_parents": disabled_management_parents,
        "matrix_receipts": matrix_receipts,
        "matrix_route_summaries": matrix_route_summaries,
        "external_native_parent_receipts": external.get("external_native_parent_receipts", []),
        "external_native_child_receipts": external.get("external_native_child_receipts", []),
        "native_codex_parent": "requires spawn_agent receipt with agent_id and completed status",
        "artifact_proxy_receipts": external.get("artifact_proxy_receipts", []),
        "mass_parent_child_fanout_boundary": "native Codex parent/child receipts must not be replaced by artifact proxies",
    }
    path = out_dir / f"wizard_council_receipt_{iteration:02d}.json"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def decide_next(
    taxonomy: dict[str, Any],
    counts: dict[str, Any],
    preflight_results: list[dict[str, Any]],
    *,
    run_runner: bool,
    parallel_runner_authorized: bool,
    opus: dict[str, Any] | None = None,
    matrix_receipts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    opus = opus or {"status": "skipped"}
    matrix_receipts = matrix_receipts or {}
    blockers: list[str] = []
    runner_launch_blockers: list[str] = []
    if counts.get("accepted", 0) == 0:
        blockers.append("accepted_qit_engine_evidence_zero")
        if run_runner:
            runner_launch_blockers.append("accepted_qit_engine_evidence_zero")
    if taxonomy.get("summary", {}).get("runner_taxonomy_disagreement_count", 0):
        blockers.append("runner_taxonomy_disagreements_need_packet_or_taxonomy_reconcile")
    if opus.get("status") == "blocked" or opus.get("returncode", 0):
        blockers.append("opus_audit_failed")
        if run_runner:
            runner_launch_blockers.append("opus_audit_failed")
    for route, route_receipt in matrix_receipts.items():
        if route_receipt.get("status") not in {"accepted", "completed"}:
            blockers.append(f"wizard_matrix_failed:{route}")
            if run_runner:
                runner_launch_blockers.append(f"wizard_matrix_failed:{route}")
    if run_runner and not parallel_runner_authorized:
        runner_launch_blockers.append("parallel_runner_authorized_deferred")
    if run_runner and any(item.get("returncode") for item in preflight_results):
        runner_launch_blockers.append("preflight_failed")

    allowed = bool(run_runner and parallel_runner_authorized and not runner_launch_blockers)
    if allowed:
        runner_status = "allowed"
    elif run_runner:
        runner_status = "authorized_deferred"
    else:
        runner_status = "not_requested"
    return {
        "action": "run_parallel_admitted_workers" if allowed else "draft_or_repair_packets_parallel",
        "blockers": sorted(set(blockers)),
        "runner_launch_blockers": sorted(set(runner_launch_blockers)),
        "runner_launch_allowed": allowed,
        "runner_status": runner_status,
    }


def runner_deferred_receipt(decision: dict[str, Any]) -> dict[str, Any]:
    status = str(decision.get("runner_status") or "authorized_deferred")
    if status == "not_requested":
        return {
            "authorization_status": "not_requested",
            "outcome_status": "not_executed",
            "execution_mode": "none",
            "dry_run": False,
            "authorized_deferred": False,
            "launch_blockers": [],
        }
    return {
        "authorization_status": status,
        "outcome_status": "not_executed",
        "execution_mode": "none",
        "dry_run": False,
        "authorized_deferred": True,
        "launch_blockers": decision.get("runner_launch_blockers") or [],
    }


def build_ralph_goal_loop(
    *,
    objective_ref: str,
    objective_text: str,
    iteration: int,
    counts: dict[str, Any] | None = None,
    premortem: dict[str, Any] | None = None,
    decision: dict[str, Any] | None = None,
    opus: dict[str, Any] | None = None,
    evidence_index_path: Path | None = None,
    preflight_receipt_path: Path | None = None,
) -> dict[str, Any]:
    counts = counts or evidence_counts()
    decision = decision or {}
    blockers = list(dict.fromkeys((decision.get("blockers") or []) + (["opus_audit_failed"] if (opus or {}).get("status") == "blocked" else [])))
    requirements = [
        {
            "requirement": "QIT engine evidence is accepted only from canonical artifacts",
            "status": "covered" if counts.get("accepted", 0) else "open",
            "evidence": counts,
        },
        {
            "requirement": "strict admission blocks promotion",
            "status": "covered",
            "evidence": {"next_acceptance_targets": counts.get("next_acceptance_targets", [])},
        },
    ]
    uncovered = [item["requirement"] for item in requirements if item["status"] != "covered"]
    return {
        "ralph_goal_loop": "run_audit_learn_premortem_harden",
        "objective_ref": objective_ref,
        "objective_text": objective_text,
        "iteration": iteration,
        "prompt_to_artifact_checklist": requirements,
        "completion_audit": {
            "blockers": blockers,
            "uncovered_requirements": uncovered,
            "next_acceptance_targets": counts.get("next_acceptance_targets", []),
            "decision": decision,
            "qit_evidence_counts": counts,
            "qit_evidence_index": str(evidence_index_path or EVIDENCE_INDEX),
            "preflight_receipt": str(preflight_receipt_path) if preflight_receipt_path else None,
        },
        "goal_exit_eligible": not blockers and not uncovered,
        "cdo_scheduler": {
            "turn_count": iteration,
            "total_agents": 0,
            "next_turn_strategy": "repair missing official sim gates before broad runner launch",
            "exit_eligible": False,
            "note": "final synthesis is blocked until scheduler metrics are met",
        },
    }


def load_external_council_receipts(path: str | None) -> dict[str, Any]:
    if not path:
        return {"external_native_parent_receipts": [], "external_native_child_receipts": [], "artifact_proxy_receipts": []}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        "external_native_parent_receipts": payload.get("external_native_parent_receipts", []),
        "external_native_child_receipts": payload.get("external_native_child_receipts", []),
        "artifact_proxy_receipts": payload.get("artifact_proxy_receipts", []),
    }


def is_native_codex_receipt(receipt: dict[str, Any]) -> bool:
    return receipt.get("runtime") == "codex-native" and bool(receipt.get("agent_id")) and receipt.get("status") == "completed"


def visible_header(native_child_ids: list[str]) -> dict[str, str]:
    validated_native_child_ids = native_child_ids
    accepted_artifact_proxy_receipt_ids: list[str] = []
    return {
        "children": f"{len(native_child_ids)}/0 blocked",
        "accepted_child_receipt_ids": native_child_ids,
        "validated_native_child_ids": validated_native_child_ids,
        "accepted_artifact_proxy_receipt_ids": accepted_artifact_proxy_receipt_ids,
        "counts_as_native_codex_child": "spawn_agent receipt only",
    }


def latest_matrix_receipt(out_dir: Path) -> dict[str, Any]:
    receipts = sorted(out_dir.rglob("matrix_receipt.json"), key=lambda path: path.stat().st_mtime)
    if not receipts:
        return {"status": "missing", "receipt_path": None}
    payload = json.loads(receipts[-1].read_text(encoding="utf-8"))
    payload["receipt_path"] = str(receipts[-1])
    return payload


def run_wizard_matrix(
    *,
    route: str,
    only_children: str,
    prompt: str,
    out_dir: Path,
    attempt_gemini: bool,
    include_haiku: bool,
) -> dict[str, Any]:
    route_out = out_dir / "wizard_matrix" / route
    command = [
        sys.executable,
        "scripts/wizard_child_matrix.py",
        "--route",
        route,
        "--prompt",
        prompt,
        "--followup-prompt",
        "Repair the highest-risk blocker for long Wizard sim-goal execution.",
        "--payoff",
        "Prove the Wizard can invoke premortem, Claude Bridge, and route-truth checks before official sim work.",
        "--use-when",
        "Before long /goal resume or official sim runner work.",
        "--stop-if",
        "No accepted Claude or Gemini receipt completes, or the route repeats only known orchestration claims.",
        "--boundary",
        "No repo edits from matrix children; receipts only under /tmp or run-local artifacts.",
        "--cwd",
        str(REPO_ROOT),
        "--out-dir",
        str(route_out),
        "--only-children",
        only_children,
        "--sonnet-timeout-sec",
        "260",
        "--opus-timeout-sec",
        "320",
        "--haiku-timeout-sec",
        "160",
        "--gemini-timeout-sec",
        "150",
        "--sonnet-budget",
        "1.5",
        "--opus-budget",
        "2.0",
        "--haiku-budget",
        "0.5",
        "--haiku-count",
        "1" if include_haiku else "0",
        "--global-max-active",
        "4",
        "--max-concurrency",
        "2",
    ]
    if attempt_gemini:
        command.append("--attempt-gemini")
    result = run(command)
    receipt = latest_matrix_receipt(route_out)
    if "status" in receipt:
        status = receipt.get("status")
    elif receipt.get("receipt_path"):
        status = "invalid_schema"
    else:
        status = "failed" if result["returncode"] else "completed"
    return {
        "status": status,
        "returncode": result["returncode"],
        "receipt_path": receipt.get("receipt_path"),
        "counts": receipt.get("counts"),
        "model_family_statuses": receipt.get("model_family_statuses"),
        "stdout": result["stdout"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--run-tag", default="")
    parser.add_argument("--out-dir", help="Override run output directory. Use /tmp for disposable loop probes.")
    parser.add_argument("--evidence-index-out", help="Override QIT evidence index write path for disposable loop probes.")
    parser.add_argument("--opus-audit", action="store_true")
    parser.add_argument("--run-runner", action="store_true")
    parser.add_argument("--dry-runner", action="store_true", help="When --run-runner is allowed, rehearse with make parallel-runner-dry instead of launching live workers.")
    parser.add_argument("--skip-wizard-matrix", action="store_true")
    parser.add_argument("--attempt-gemini", action="store_true", default=True)
    parser.add_argument("--skip-gemini", action="store_true")
    parser.add_argument("--include-haiku", action="store_true")
    parser.add_argument("--runner-minutes", type=int, default=1)
    parser.add_argument("--lane-a-parallel", type=int, default=2)
    parser.add_argument("--lane-b-parallel", type=int, default=4)
    parser.add_argument("--external-council-receipts")
    args = parser.parse_args()

    run_started_at = datetime.now(timezone.utc).isoformat()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out_dir) if args.out_dir else REPO_ROOT / "runs" / f"wizard_autoresearch_{args.run_tag or stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    evidence_index = Path(args.evidence_index_out) if args.evidence_index_out else EVIDENCE_INDEX
    external = load_external_council_receipts(args.external_council_receipts)
    run_config = {
        "runner_minutes": args.runner_minutes,
        "lane_a_parallel": args.lane_a_parallel,
        "lane_b_parallel": args.lane_b_parallel,
        "opus_audit_requested": bool(args.opus_audit),
        "external_council_receipts": args.external_council_receipts or "",
        "evidence_index_out": str(evidence_index),
    }

    matrix_requested = not args.skip_wizard_matrix
    gemini_requested = matrix_requested and args.attempt_gemini and not args.skip_gemini
    latest_decision: dict[str, Any] = {}
    iteration_manifest: list[dict[str, Any]] = []
    write_run_manifest(
        out_dir,
        run_tag=args.run_tag or stamp,
        run_started_at=run_started_at,
        iterations_requested=args.iterations,
        evidence_index=evidence_index,
        matrix_enabled=matrix_requested,
        gemini_requested=gemini_requested,
        haiku_requested=args.include_haiku,
        runner_requested=args.run_runner,
        run_config=run_config,
        argv=sys.argv,
        latest_decision=latest_decision,
        iteration_manifest=iteration_manifest,
        run_status="in_progress",
    )
    for iteration in range(1, args.iterations + 1):
        premortem_path = out_dir / f"premortem_{iteration:02d}.json"
        qit_index_stdout_path = out_dir / f"qit_index_write_{iteration:02d}.out"
        stage_gate_stdout_path = out_dir / f"stage_gate_{iteration:02d}.out"
        premortem = {
            "ok": None,
            "status": "skipped",
            "path": str(premortem_path),
            "frame": "six months later the long Wizard goal run failed because route truth, context, or sim gates drifted",
        }
        matrix_receipts: dict[str, Any] = {}
        if not args.skip_wizard_matrix:
            matrix_receipts["failure.premortem"] = run_wizard_matrix(
                route="failure.premortem",
                only_children="skill.premortem",
                prompt=(
                    "Premortem the Wizard long-goal harness: it must run for 10 hours to days, "
                    "preserve context, invoke skills including claude-bridge and premortem, keep sim gates strict, "
                    "avoid browser automation, and avoid false FULL claims. Return YAML receipts only."
                ),
                out_dir=out_dir,
                attempt_gemini=gemini_requested,
                include_haiku=args.include_haiku,
            )
            matrix_receipts["manager.route_truth"] = run_wizard_matrix(
                route="manager.route_truth",
                only_children="manager.lineage_audit",
                prompt=(
                    "Audit route truth for the Wizard long-goal harness: separate Codex-native, Claude Bridge, Gemini, "
                    "tool, and artifact-proxy receipts; preserve blockers instead of smoothing them."
                ),
                out_dir=out_dir,
                attempt_gemini=gemini_requested,
                include_haiku=args.include_haiku,
            )
            premortem["matrix_receipt"] = matrix_receipts["failure.premortem"].get("receipt_path")
            premortem["ok"] = matrix_receipts["failure.premortem"].get("status") in {"accepted", "completed"}
            premortem["status"] = matrix_receipts["failure.premortem"].get("status")
        premortem_text = json.dumps(premortem, indent=2, sort_keys=True) + "\n"
        premortem_path.write_text(premortem_text, encoding="utf-8")
        (out_dir / "premortem.json").write_text(premortem_text, encoding="utf-8")
        helper = run([sys.executable, "scripts/helper_process_audit.py", "--strict"])
        helper_summary = helper_process_summary(helper)
        qit_index_write = run(
            qit_evidence_index_command(
                evidence_index,
                skip_external_scan=False,
            )
        )
        stage_gate = run([sys.executable, "scripts/stage_gate.py"])
        stage_summary = stage_gate_summary(stage_gate)
        qit_index_stdout_path.write_text(qit_index_write["stdout"], encoding="utf-8")
        (out_dir / "qit_index_write.out").write_text(qit_index_write["stdout"], encoding="utf-8")
        stage_gate_stdout_path.write_text(stage_gate["stdout"], encoding="utf-8")
        (out_dir / "stage_gate.out").write_text(stage_gate["stdout"], encoding="utf-8")
        qit_summary = qit_evidence_summary(evidence_index)
        preflight_all_pass = not helper.get("returncode") and not qit_index_write.get("returncode") and not stage_gate.get("returncode")
        preflight_receipt_path = out_dir / f"preflight_receipts_{iteration:02d}.json"
        preflight_receipt_path.write_text(
            json.dumps(
                {
                    "schema": "wizard_autoresearch_preflight_receipts",
                    "iteration": iteration,
                    "premortem_path": str(premortem_path),
                    "helper_process_audit": helper,
                    "helper_process_summary": helper_summary,
                    "qit_index_write": qit_index_write,
                    "qit_index_stdout_path": str(qit_index_stdout_path),
                    "qit_evidence_index": str(evidence_index),
                    "qit_evidence_summary": qit_summary,
                    "stage_gate": stage_gate,
                    "stage_gate_summary": stage_summary,
                    "stage_gate_stdout_path": str(stage_gate_stdout_path),
                    "all_pass": preflight_all_pass,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        counts = evidence_counts(evidence_index)
        taxonomy = {"summary": {"runner_taxonomy_disagreement_count": 0, "row_state_counts": {"queue_candidate": len(counts.get("next_acceptance_targets", []))}}}
        opus = {"status": "skipped"}
        if args.opus_audit:
            opus = {"status": "blocked", "reason": "opus_audit unavailable in local deterministic loop", "returncode": 1}
        latest_decision = decide_next(
            taxonomy,
            counts,
            [helper, qit_index_write, stage_gate],
            run_runner=args.run_runner,
            parallel_runner_authorized=args.run_runner,
            opus=opus,
            matrix_receipts=matrix_receipts,
        )
        if latest_decision["runner_launch_allowed"]:
            runner_target = "parallel-runner-dry" if args.dry_runner else "parallel-runner"
            latest_decision["runner"] = run(["make", runner_target, f"MINUTES={args.runner_minutes}", f"LANE_A_PARALLEL={args.lane_a_parallel}", f"LANE_B_PARALLEL={args.lane_b_parallel}"])
            latest_decision["runner"]["execution_mode"] = "dry_run" if args.dry_runner else "live"
            latest_decision["runner"]["dry_run"] = bool(args.dry_runner)
            latest_decision["runner"]["authorization_status"] = "permitted"
            if args.dry_runner:
                latest_decision["runner"]["outcome_status"] = "dry_run_completed" if not latest_decision["runner"].get("returncode") else "dry_run_failed"
            else:
                latest_decision["runner"]["outcome_status"] = "live_run_completed" if not latest_decision["runner"].get("returncode") else "live_run_failed"
        else:
            latest_decision["runner"] = runner_deferred_receipt(latest_decision)
        matrix_route_summaries = {
            route: {
                "status": route_receipt.get("status"),
                "counts": route_receipt.get("counts") or {},
                "model_family_statuses": route_receipt.get("model_family_statuses") or {},
                "receipt_path": route_receipt.get("receipt_path"),
            }
            for route, route_receipt in matrix_receipts.items()
        }
        matrix_route_statuses = [receipt.get("status") for receipt in matrix_receipts.values()]
        matrix_all_accepted = (
            all(status in {"accepted", "completed"} for status in matrix_route_statuses)
            if matrix_route_statuses
            else None
        )
        loop = build_ralph_goal_loop(
            objective_ref=args.run_tag or stamp,
            objective_text="make Wizard able to manage long official sim work without false promotion",
            iteration=iteration,
            counts=counts,
            premortem=premortem,
            decision=latest_decision,
            opus=opus,
            evidence_index_path=evidence_index,
            preflight_receipt_path=preflight_receipt_path,
        )
        council_receipt_path = write_council_receipts(
            out_dir,
            iteration=iteration,
            decision=latest_decision,
            premortem=premortem,
            external=external,
            matrix_receipts=matrix_receipts,
            matrix_enabled=not args.skip_wizard_matrix,
            gemini_enabled=gemini_requested,
            haiku_enabled=args.include_haiku,
        )
        goal_loop_path = out_dir / f"ralph_goal_loop_{iteration:02d}.json"
        goal_loop_path.write_text(json.dumps(loop, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        iteration_manifest.append(
            {
                "iteration": iteration,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "preflight_all_pass": preflight_all_pass,
                "helper_process_summary": helper_summary,
                "preflight_receipt": str(preflight_receipt_path),
                "council_receipt": str(council_receipt_path),
                "goal_loop_receipt": str(goal_loop_path),
                "premortem": str(premortem_path),
                "qit_index_stdout": str(qit_index_stdout_path),
                "stage_gate_stdout": str(stage_gate_stdout_path),
                "stage_gate_summary": stage_summary,
                "qit_evidence_summary": qit_summary,
                "qit_evidence_index": str(evidence_index),
                "goal_exit_eligible": bool(loop.get("goal_exit_eligible")),
                "runner_launch_allowed": bool(latest_decision.get("runner_launch_allowed")),
                "blockers": latest_decision.get("blockers", []),
                "matrix_route_count": len(matrix_receipts),
                "matrix_route_summaries": matrix_route_summaries,
                "matrix_all_accepted": matrix_all_accepted,
            }
        )
        write_run_manifest(
            out_dir,
            run_tag=args.run_tag or stamp,
            run_started_at=run_started_at,
            iterations_requested=args.iterations,
            evidence_index=evidence_index,
            matrix_enabled=matrix_requested,
            gemini_requested=gemini_requested,
            haiku_requested=args.include_haiku,
            runner_requested=args.run_runner,
            run_config=run_config,
            argv=sys.argv,
            latest_decision=latest_decision,
            iteration_manifest=iteration_manifest,
            run_status="in_progress",
        )

    write_run_manifest(
        out_dir,
        run_tag=args.run_tag or stamp,
        run_started_at=run_started_at,
        iterations_requested=args.iterations,
        evidence_index=evidence_index,
        matrix_enabled=matrix_requested,
        gemini_requested=gemini_requested,
        haiku_requested=args.include_haiku,
        runner_requested=args.run_runner,
        run_config=run_config,
        argv=sys.argv,
        latest_decision=latest_decision,
        iteration_manifest=iteration_manifest,
        run_status="complete",
    )

    print(json.dumps({"out_dir": str(out_dir), "decision": latest_decision}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
