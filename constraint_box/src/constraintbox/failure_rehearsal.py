"""Retained controller-owned failure rehearsals for external capabilities.

This module is deliberately a *test instrument*, not a generic fault-injection
API.  It owns one fixed SciPy scenario: run the normal operation, deliberately
sever only its replay using the worker's pre-existing operation-severance
control, retain the resulting non-pass/repair plan, and then run the ordinary
unpoisoned same-profile fresh-rerun path.  No caller selects an engine,
capability, worker, command, operation, tolerance, or repair action.

The failure is deliberately induced.  It demonstrates that ConstraintBox
catches and retains a real external-worker failure path; it is not evidence of
a spontaneous SciPy defect, engine readiness, automatic tuning, release,
promotion, or scientific admission.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any

from .capability_dispatch import run_capability_flow
from .capability_origin import CAPABILITY_FLOW_RESULT_NAME, ORIGIN_ATTESTATION_NAME
from .external_bounded_numerics import (
    SEVERED_EXIT_CODE,
    bounded_numerics_binding_from_dict,
)
from .external_scipy_capability import (
    CAPABILITY_ID as SCIPY_CAPABILITY_ID,
    SCIPY_EXPM_PROFILE,
    validate_scipy_expm_receipt,
)
from .external_scipy_capability_flow import (
    controller_replay_severance_rehearsal_scope,
)
from .failure_repair import (
    REPAIR_PLAN_NAME,
    load_verified_repair_contract_for_run,
    write_repair_plan_for_run,
)
from .intake import IntakeError, canonical_json, parse_json_object
from .repair_outcome import (
    REPAIR_OUTCOME_NAME,
    _run_capability_suite_fresh_rerun_outcome,
    verify_fresh_rerun_outcome,
)


REHEARSAL_SCHEMA = "constraintbox.external-scipy-replay-severance-rehearsal.v1"
REHEARSAL_POLICY_ID = "constraintbox.fixed-replay-severance-rehearsal-policy.v1"
REHEARSAL_ID = "scipy-expm-replay-severance-v1"
REHEARSAL_RECEIPT_NAME = "failure_rehearsal_result.json"
_FAILURE_DIRNAME = "deliberate-replay-severance"
_RERUN_DIRNAME = "unpoisoned-fresh-rerun"
_FIXED_REQUEST_ID = "scipy-replay-severance-rehearsal-v1"
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_HEX = re.compile(r"[0-9a-f]{64}")


class FailureRehearsalError(ValueError):
    """The fixed external failure rehearsal could not be retained or verified."""


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _source_metadata() -> dict[str, str]:
    path = Path(__file__).resolve()
    try:
        source_sha256 = _sha256(path.read_bytes())
    except OSError as exc:
        raise FailureRehearsalError(f"failure-rehearsal source is unavailable: {exc}") from exc
    return {
        "module": "constraintbox.failure_rehearsal",
        "source_path": str(path),
        "source_sha256": source_sha256,
    }


def _require_new_root(run_root: Path) -> Path:
    candidate = Path(run_root).expanduser()
    if not candidate.is_absolute():
        raise FailureRehearsalError("failure-rehearsal run root must be absolute")
    if candidate.exists() or candidate.is_symlink():
        raise FailureRehearsalError("failure-rehearsal run root must be new and non-symlink")
    parent = candidate.parent
    if parent.is_symlink():
        raise FailureRehearsalError("failure-rehearsal parent must not be a symlink")
    try:
        resolved_parent = parent.resolve(strict=True)
    except OSError as exc:
        raise FailureRehearsalError(
            f"failure-rehearsal parent is unavailable: {exc}"
        ) from exc
    if not resolved_parent.is_dir() or resolved_parent != parent:
        raise FailureRehearsalError("failure-rehearsal parent must be one direct directory")
    return resolved_parent / candidate.name


def _write_new_canonical(path: Path, value: dict[str, Any]) -> None:
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(canonical_json(value).decode("utf-8"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except (OSError, TypeError, ValueError) as exc:
        raise FailureRehearsalError(
            f"could not retain failure-rehearsal receipt: {exc}"
        ) from exc


def _read_canonical(path: Path, label: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        value = parse_json_object(raw)
    except (OSError, IntakeError) as exc:
        raise FailureRehearsalError(f"{label} is unavailable or invalid: {exc}") from exc
    if raw != canonical_json(value) + b"\n":
        raise FailureRehearsalError(f"{label} is not canonical JSON")
    return value


def _failure_summary(
    *,
    failure_root: Path,
    parent: dict[str, Any],
) -> dict[str, Any]:
    result = parent["result"]
    contract = parent["contract"]
    evidence = parent["evidence"]
    receipt = _read_canonical(
        Path(result["artifacts"]["capability_receipt"]),
        "failure capability receipt",
    )
    binding = bounded_numerics_binding_from_dict(SCIPY_EXPM_PROFILE, receipt["binding"])
    errors = validate_scipy_expm_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=receipt["receipt_sha256"],
        require_pass=False,
    )
    if errors:
        raise FailureRehearsalError(
            "failure capability receipt did not validate: " + "; ".join(errors)
        )
    if (
        result["capability_id"] != SCIPY_CAPABILITY_ID
        or result["disposition"] != "BLOCKED"
        or result["reason"] != "controller_recomputed_check_failed"
        or receipt.get("status") != "FAIL"
        or receipt.get("reason") != "controller_recomputed_check_failed"
        or receipt["normal"].get("returncode") != 0
        or receipt["replay"].get("returncode") != SEVERED_EXIT_CODE
        or receipt["severance"].get("returncode") != SEVERED_EXIT_CODE
        or receipt["controls"].get("replay") is not False
        or receipt["controls"].get("severance") is not True
    ):
        raise FailureRehearsalError("fixed replay-severance failure did not occur")
    plan = contract["repair_plan"]
    if (
        plan.get("selected_action") != "fresh_rerun"
        or plan.get("execution_authorized") is not False
        or plan.get("retry_budget", {}).get("authorized_attempts") != 0
    ):
        raise FailureRehearsalError("failure did not yield the fixed non-executing plan")
    return {
        "run_root": str(failure_root),
        "capability_result_path": str(failure_root / CAPABILITY_FLOW_RESULT_NAME),
        "capability_result_sha256": _sha256(canonical_json(result)),
        "origin_attestation_path": str(failure_root / ORIGIN_ATTESTATION_NAME),
        "origin_attestation_sha256": evidence["origin_attestation_sha256"],
        "repair_plan_path": str(failure_root / REPAIR_PLAN_NAME),
        "repair_plan_sha256": contract["repair_plan_sha256"],
        "capability_id": result["capability_id"],
        "disposition": result["disposition"],
        "reason": result["reason"],
        "normal_worker_returncode": receipt["normal"]["returncode"],
        "replay_worker_returncode": receipt["replay"]["returncode"],
        "severance_worker_returncode": receipt["severance"]["returncode"],
        "replay_control_passed": receipt["controls"]["replay"],
        "severance_control_passed": receipt["controls"]["severance"],
    }


def _rerun_summary(*, rerun_root: Path, outcome: dict[str, Any]) -> dict[str, Any]:
    verified = verify_fresh_rerun_outcome(outcome, expected_run_root=rerun_root)
    verified_outcome = verified["outcome"]
    if (
        verified_outcome != outcome
        or outcome.get("disposition") != "PARKED"
        or outcome.get("outcome_state") != "FRESH_RERUN_ELIGIBLE_REVIEW_REQUIRED"
        or outcome.get("repair_resolved") is not False
        or outcome.get("rerun", {}).get("capability_id") != SCIPY_CAPABILITY_ID
        or outcome.get("rerun", {}).get("disposition") != "ELIGIBLE"
        or outcome.get("execution", {}).get("automatic_fixed_replay") is not True
        or outcome.get("execution", {}).get("automatic_retry_or_tuning") is not False
        or outcome.get("execution", {}).get("llm_decision_authority") is not False
    ):
        raise FailureRehearsalError("unpoisoned fresh rerun did not retain the fixed outcome")
    return {
        "run_root": str(rerun_root),
        "repair_outcome_path": str(rerun_root / REPAIR_OUTCOME_NAME),
        "repair_outcome_sha256": outcome["outcome_sha256"],
        "capability_id": outcome["rerun"]["capability_id"],
        "rerun_disposition": outcome["rerun"]["disposition"],
        "outcome_disposition": outcome["disposition"],
        "outcome_state": outcome["outcome_state"],
        "independent_fresh_python_replay": outcome["verification"][
            "fresh_child_replay"
        ]["process"]["fresh_python_process"],
    }


def _build_receipt(
    *,
    rehearsal_root: Path,
    failure: dict[str, Any],
    fresh_rerun: dict[str, Any],
) -> dict[str, Any]:
    body = {
        "schema": REHEARSAL_SCHEMA,
        "policy_id": REHEARSAL_POLICY_ID,
        "rehearsal_id": REHEARSAL_ID,
        "run_root": str(rehearsal_root),
        "fixed_request_id": _FIXED_REQUEST_ID,
        "controller_injection": {
            "kind": "source_owned_replay_only_operation_severance",
            "capability_id": SCIPY_CAPABILITY_ID,
            "operation": SCIPY_EXPM_PROFILE.exact_api[-1],
            "normal_operation_injected": False,
            "replay_operation_injected": True,
            "ordinary_severance_control_injected": True,
            "ambient_environment_selector_accepted": False,
            "caller_capability_override_accepted": False,
            "caller_worker_or_command_override_accepted": False,
            "caller_verifier_or_tolerance_override_accepted": False,
            "llm_decision_authority": False,
        },
        "failure": failure,
        "fresh_rerun": fresh_rerun,
        "source": _source_metadata(),
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": (
            "one deliberate controller-owned SciPy replay-operation severance, "
            "a retained BLOCKED receipt and non-executing repair plan, then one "
            "unpoisoned controller-selected same-profile fresh rerun independently "
            "replayed in a fresh Python process; not a spontaneous SciPy defect, "
            "engine readiness, automatic repair/tuning, release, promotion, CR truth, "
            "or scientific claim"
        ),
    }
    return body | {"rehearsal_sha256": _sha256(canonical_json(body))}


def verify_scipy_replay_severance_rehearsal(
    receipt: dict[str, Any],
    *,
    expected_run_root: Path,
) -> dict[str, Any]:
    """Regenerate the proof obligations for one retained rehearsal receipt."""

    if not isinstance(expected_run_root, Path) or not expected_run_root.is_absolute():
        raise FailureRehearsalError("expected rehearsal root must be absolute")
    expected_root = expected_run_root.resolve(strict=True)
    expected_fields = {
        "schema",
        "policy_id",
        "rehearsal_id",
        "run_root",
        "fixed_request_id",
        "controller_injection",
        "failure",
        "fresh_rerun",
        "source",
        "external_system",
        "kernel_membership",
        "release_allowed",
        "engine_readiness_claim",
        "cr_truth_claim",
        "promotion_allowed",
        "claim_ceiling",
        "rehearsal_sha256",
    }
    if not isinstance(receipt, dict) or set(receipt) != expected_fields:
        raise FailureRehearsalError("failure-rehearsal receipt fields differ")
    root_digest = receipt.get("rehearsal_sha256")
    if not isinstance(root_digest, str) or _HEX.fullmatch(root_digest) is None:
        raise FailureRehearsalError("failure-rehearsal root digest is invalid")
    body = dict(receipt)
    body.pop("rehearsal_sha256")
    if root_digest != _sha256(canonical_json(body)):
        raise FailureRehearsalError("failure-rehearsal root digest differs")
    if (
        receipt["schema"] != REHEARSAL_SCHEMA
        or receipt["policy_id"] != REHEARSAL_POLICY_ID
        or receipt["rehearsal_id"] != REHEARSAL_ID
        or receipt["fixed_request_id"] != _FIXED_REQUEST_ID
        or receipt["run_root"] != str(expected_root)
        or receipt["source"] != _source_metadata()
        or receipt["external_system"] is not True
        or receipt["kernel_membership"] != "EXTERNAL_NOT_CB_KERNEL"
        or receipt["release_allowed"] is not False
        or receipt["engine_readiness_claim"] is not False
        or receipt["cr_truth_claim"] is not False
        or receipt["promotion_allowed"] is not False
    ):
        raise FailureRehearsalError("failure-rehearsal controller boundary differs")
    expected_injection = _build_receipt(
        rehearsal_root=expected_root,
        failure=receipt["failure"],
        fresh_rerun=receipt["fresh_rerun"],
    )["controller_injection"]
    if receipt["controller_injection"] != expected_injection:
        raise FailureRehearsalError("failure-rehearsal injection contract differs")
    failure_root = expected_root / _FAILURE_DIRNAME
    rerun_root = expected_root / _RERUN_DIRNAME
    if receipt["failure"].get("run_root") != str(failure_root):
        raise FailureRehearsalError("failure-rehearsal failure root differs")
    if receipt["fresh_rerun"].get("run_root") != str(rerun_root):
        raise FailureRehearsalError("failure-rehearsal rerun root differs")
    parent = load_verified_repair_contract_for_run(failure_root)
    expected_failure = _failure_summary(failure_root=failure_root, parent=parent)
    if receipt["failure"] != expected_failure:
        raise FailureRehearsalError("failure-rehearsal failure summary differs")
    outcome = _read_canonical(rerun_root / REPAIR_OUTCOME_NAME, "fresh rerun outcome")
    expected_rerun = _rerun_summary(rerun_root=rerun_root, outcome=outcome)
    if receipt["fresh_rerun"] != expected_rerun:
        raise FailureRehearsalError("failure-rehearsal fresh-rerun summary differs")
    return {
        "receipt": receipt,
        "failure_run_root": failure_root,
        "fresh_rerun_root": rerun_root,
    }


def run_scipy_replay_severance_rehearsal(*, run_root: Path) -> dict[str, Any]:
    """Run and retain the one fixed external SciPy failure rehearsal."""

    rehearsal_root = _require_new_root(run_root)
    if _SAFE_ID.fullmatch(_FIXED_REQUEST_ID) is None:
        raise FailureRehearsalError("fixed rehearsal request id is invalid")
    failure_root = rehearsal_root / _FAILURE_DIRNAME
    rerun_root = rehearsal_root / _RERUN_DIRNAME
    with controller_replay_severance_rehearsal_scope():
        try:
            rehearsal_root.mkdir()
        except OSError as exc:
            raise FailureRehearsalError(
                f"could not create rehearsal root: {exc}"
            ) from exc
        result = run_capability_flow(
            capability_id=SCIPY_CAPABILITY_ID,
            request_id=_FIXED_REQUEST_ID,
            run_root=failure_root,
        )
    if (
        result.get("disposition") != "BLOCKED"
        or result.get("reason") != "controller_recomputed_check_failed"
    ):
        raise FailureRehearsalError("fixed replay-severance route did not block")
    write_repair_plan_for_run(failure_root)
    parent = load_verified_repair_contract_for_run(failure_root)
    failure = _failure_summary(failure_root=failure_root, parent=parent)
    outcome = _run_capability_suite_fresh_rerun_outcome(
        capability_run_root=failure_root,
        run_root=rerun_root,
    )
    fresh_rerun = _rerun_summary(rerun_root=rerun_root, outcome=outcome)
    receipt = _build_receipt(
        rehearsal_root=rehearsal_root,
        failure=failure,
        fresh_rerun=fresh_rerun,
    )
    _write_new_canonical(rehearsal_root / REHEARSAL_RECEIPT_NAME, receipt)
    verified = verify_scipy_replay_severance_rehearsal(
        receipt,
        expected_run_root=rehearsal_root,
    )
    return verified["receipt"]
