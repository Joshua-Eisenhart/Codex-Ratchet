"""Controller-bounded fresh-rerun outcomes for repair contracts.

This module is deliberately *not* a source or environment repair executor.  A
repair plan remains non-executing and grants no general retry budget.  There
are only two fixed ways to run the one safe, non-mutating follow-up selected by
the controller's closed failure table:

* an operator supplies the fixed acknowledgement to the public outcome surface;
* the controller-owned capability suite invokes its internal one-shot hook.

Both routes rerun only the already named static capability, independently
replay the new receipt, and retain a non-promoting outcome for human review.
No LLM, plan field, user-supplied capability name, worker, verifier, command,
tolerance, source edit, or environment change can alter the selected work.
The local-process provenance checks here are not hostile-host containment.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from .capability_dispatch import CapabilityDispatchError, run_capability_flow
from .capability_origin import CAPABILITY_FLOW_RESULT_NAME
from .failure_repair import (
    FailureRepairError,
    _parse_canonical_object,
    _read_regular_bytes,
    _require_sha256,
    _sha256,
    load_verified_repair_contract_for_run,
    verify_capability_result,
)
from .intake import canonical_json


REPAIR_OUTCOME_NAME = "repair_outcome.json"
REPAIR_OUTCOME_SCHEMA = "constraintbox.capability-repair-outcome.v1"
REPAIR_OUTCOME_POLICY_ID = "constraintbox.external-capability-repair-outcome-policy.v1"
_REPLAY_REQUEST_SCHEMA = "constraintbox.repair-outcome-replay-request.v1"
_REPLAY_RESULT_SCHEMA = "constraintbox.repair-outcome-replay-result.v1"
_REPLAY_TIMEOUT_SECONDS = 180
_MAX_REPLAY_STREAM_BYTES = 8 * 1024 * 1024
_OUTCOME_FIELDS = frozenset(
    {
        "schema",
        "policy_id",
        "outcome_verifier",
        "parent",
        "rerun",
        "verification",
        "execution",
        "outcome_state",
        "disposition",
        "repair_resolved",
        "next_step",
        "external_system",
        "kernel_membership",
        "release_allowed",
        "engine_readiness_claim",
        "cr_truth_claim",
        "promotion_allowed",
        "claim_ceiling",
        "outcome_sha256",
    }
)
_OUTCOME_STATES = {
    "ELIGIBLE": "FRESH_RERUN_ELIGIBLE_REVIEW_REQUIRED",
    "BLOCKED": "FRESH_RERUN_BLOCKED",
    "PARKED": "FRESH_RERUN_PARKED",
}
_OPERATOR_ACKNOWLEDGEMENT_MODE = "operator_fixed_acknowledgement"
_CAPABILITY_SUITE_HOOK_MODE = "capability_suite_fixed_hook"
_EXECUTION_MODES = frozenset(
    {_OPERATOR_ACKNOWLEDGEMENT_MODE, _CAPABILITY_SUITE_HOOK_MODE}
)
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")


class RepairOutcomeError(ValueError):
    """A bounded fresh-rerun outcome could not be verified or retained."""


def _execution_record(execution_mode: str) -> dict[str, Any]:
    """Return one closed execution record; callers cannot define a third mode."""

    if execution_mode == _OPERATOR_ACKNOWLEDGEMENT_MODE:
        invocation_kind = "explicit_fixed_acknowledgement"
        authority = "operator_acknowledges_fixed_controller_action"
        automatic_fixed_replay = False
    elif execution_mode == _CAPABILITY_SUITE_HOOK_MODE:
        invocation_kind = "controller_selected_capability_suite_hook"
        authority = "fixed_capability_suite_hook"
        automatic_fixed_replay = True
    else:
        raise RepairOutcomeError("fresh rerun execution mode is not controller-defined")
    return {
        "invocation_kind": invocation_kind,
        "execution_authority": authority,
        "parent_plan_execution_authorized": False,
        "parent_plan_authorized_attempts": 0,
        "controller_selected_action": "fresh_rerun",
        "caller_capability_override_accepted": False,
        "caller_worker_or_command_override_accepted": False,
        "caller_verifier_or_tolerance_override_accepted": False,
        "constraintbox_mutation_requested_or_performed": False,
        "source_and_runtime_identity_rechecked": True,
        "automatic_fixed_replay": automatic_fixed_replay,
        "automatic_retry_or_tuning": False,
        "automatic_retry_loop": False,
        "automatic_tuning": False,
        "llm_decision_authority": False,
    }


def _execution_mode_from_outcome(outcome: dict[str, Any]) -> str:
    execution = outcome.get("execution")
    if not isinstance(execution, dict):
        raise RepairOutcomeError("repair outcome execution record is invalid")
    for execution_mode in _EXECUTION_MODES:
        if execution == _execution_record(execution_mode):
            return execution_mode
    raise RepairOutcomeError("repair outcome execution record differs from fixed modes")


def _claim_ceiling_for_mode(execution_mode: str) -> str:
    if execution_mode == _OPERATOR_ACKNOWLEDGEMENT_MODE:
        prefix = "one explicitly acknowledged, controller-bound fresh rerun"
    elif execution_mode == _CAPABILITY_SUITE_HOOK_MODE:
        prefix = "one controller-selected fixed fresh rerun from the capability-suite hook"
    else:
        raise RepairOutcomeError("fresh rerun execution mode is not controller-defined")
    return (
        f"{prefix} whose new external receipt was independently replayed; not "
        "a source or environment change, retry budget, engine-readiness result, "
        "release, promotion, tuning, or scientific claim"
    )


def _outcome_source_metadata() -> dict[str, str]:
    path = Path(__file__).resolve()
    try:
        source_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise RepairOutcomeError(f"repair outcome source is unavailable: {exc}") from exc
    return {
        "verifier_id": "constraintbox.repair-outcome.v1",
        "source_path": str(path),
        "source_sha256": source_sha256,
    }


def _require_new_outcome_root(run_root: Path, parent_root: Path) -> Path:
    """Accept one new direct child path without silently following a link."""

    candidate = Path(run_root).expanduser()
    if not candidate.is_absolute():
        raise RepairOutcomeError("repair outcome run root must be an absolute pathlib.Path")
    if candidate.is_symlink() or candidate.exists():
        raise RepairOutcomeError("repair outcome run directory must be new and non-symlink")
    lexical_parent = candidate.parent
    if lexical_parent.is_symlink():
        raise RepairOutcomeError("repair outcome parent directory must not be a symlink")
    try:
        resolved_parent = lexical_parent.resolve(strict=True)
    except OSError as exc:
        raise RepairOutcomeError(f"repair outcome parent directory is unavailable: {exc}") from exc
    if not resolved_parent.is_dir() or resolved_parent != lexical_parent:
        raise RepairOutcomeError("repair outcome parent directory must be one direct directory")
    resolved = resolved_parent / candidate.name
    if resolved.exists() or resolved.is_symlink():
        raise RepairOutcomeError("repair outcome run directory must be new and non-symlink")
    if (
        resolved == parent_root
        or parent_root in resolved.parents
        or resolved in parent_root.parents
    ):
        raise RepairOutcomeError("repair outcome run directory must be disjoint from parent run")
    return resolved


def _derived_request_id(repair_plan_sha256: str) -> str:
    _require_sha256(repair_plan_sha256, "repair plan digest")
    request_id = f"fresh-rerun-{repair_plan_sha256[:32]}"
    if _SAFE_ID.fullmatch(request_id) is None:
        raise RepairOutcomeError("derived fresh-rerun request id is invalid")
    return request_id


def _load_verified_parent(run_root: Path) -> dict[str, Any]:
    try:
        parent = load_verified_repair_contract_for_run(run_root)
    except FailureRepairError as exc:
        raise RepairOutcomeError(f"parent repair contract is not current and verified: {exc}") from exc
    contract = parent["contract"]
    plan = contract.get("repair_plan")
    if not isinstance(plan, dict) or plan.get("selected_action") != "fresh_rerun":
        raise RepairOutcomeError("parent repair plan does not select fresh_rerun")
    if plan.get("execution_authorized") is not False:
        raise RepairOutcomeError("parent repair plan must remain non-executing")
    retry_budget = plan.get("retry_budget")
    if not isinstance(retry_budget, dict) or retry_budget.get("authorized_attempts") != 0:
        raise RepairOutcomeError("parent repair plan retry budget differs")
    required = plan.get("required_regression_guard")
    if not isinstance(required, dict) or required.get("must_rerun_same_external_capability") is not True:
        raise RepairOutcomeError("parent repair plan lacks the same-capability guard")
    if required.get("must_preserve_parent_flow_policy") is not True:
        raise RepairOutcomeError("parent repair plan lacks the same-policy guard")
    return parent


def _load_verified_rerun(
    *,
    parent: dict[str, Any],
    run_root: Path,
) -> dict[str, Any]:
    """Independently replay the new flow and enforce the parent bindings."""

    result_path, raw_result = _read_regular_bytes(
        run_root / CAPABILITY_FLOW_RESULT_NAME,
        CAPABILITY_FLOW_RESULT_NAME,
    )
    result = _parse_canonical_object(raw_result, CAPABILITY_FLOW_RESULT_NAME)
    try:
        evidence = verify_capability_result(result, expected_run_root=run_root)
    except FailureRepairError as exc:
        raise RepairOutcomeError(f"fresh rerun failed independent verification: {exc}") from exc
    contract = parent["contract"]
    plan = contract["repair_plan"]
    parent_result = parent["result"]
    expected_request_id = _derived_request_id(contract["repair_plan_sha256"])
    if result["capability_id"] != parent_result["capability_id"]:
        raise RepairOutcomeError("fresh rerun capability differs from parent plan")
    if result["request_id"] != expected_request_id:
        raise RepairOutcomeError("fresh rerun request id differs from controller derivation")
    required_verifier = plan["required_verifier"]
    if result["flow_policy_sha256"] != required_verifier[
        "required_parent_flow_policy_sha256"
    ]:
        raise RepairOutcomeError("fresh rerun flow policy differs from parent plan")
    origin = evidence["origin_attestation"].get("origin")
    required_origin = plan["required_controller_origin"]
    if not isinstance(origin, dict) or origin.get("registry_sha256") != required_origin[
        "registry_sha256"
    ]:
        raise RepairOutcomeError("fresh rerun controller origin differs from parent plan")
    parent_evidence = parent["evidence"]
    parent_attestation = parent_evidence["origin_attestation"]
    rerun_attestation = evidence["origin_attestation"]
    for field in ("origin", "runner", "issuer"):
        if rerun_attestation.get(field) != parent_attestation.get(field):
            raise RepairOutcomeError(
                f"fresh rerun controller source binding differs from parent: {field}"
            )
    if evidence["runtime_identity_sha256"] != contract["failure_event"]["parent_bindings"][
        "runtime_identity_sha256"
    ]:
        raise RepairOutcomeError("fresh rerun runtime identity differs from parent plan")
    independent_replay = _run_fresh_replay_child(result=result, run_root=run_root)
    summary = independent_replay["summary"]
    expected_summary = {
        "schema": _REPLAY_RESULT_SCHEMA,
        "capability_id": result["capability_id"],
        "disposition": result["disposition"],
        "capability_result_sha256": _sha256(canonical_json(result)),
        "origin_attestation_sha256": evidence["origin_attestation_sha256"],
        "flow_ledger_head_sha256": evidence["flow_ledger_head_sha256"],
        "runtime_identity_sha256": evidence["runtime_identity_sha256"],
        "independent_replay": True,
    }
    if summary != expected_summary:
        raise RepairOutcomeError("fresh child replay differs from independent verifier")
    return {
        "result": result,
        "result_path": result_path,
        "evidence": evidence,
        "independent_replay": independent_replay,
    }


def _fixed_worker_code() -> str:
    """Return the fixed replay child bootstrap without caller-provided code."""

    source_root = Path(__file__).resolve().parents[1]
    return (
        "import sys\n"
        f"sys.path.insert(0, {str(source_root)!r})\n"
        "from constraintbox.repair_outcome_replay_worker import main\n"
        "raise SystemExit(main())\n"
    )


def _fresh_replay_command() -> list[str]:
    """Keep the verifier child's CPython optimization identity unchanged."""

    command = [sys.executable]
    if sys.flags.optimize:
        command.append("-" + ("O" * sys.flags.optimize))
    command.extend(["-B", "-c", _fixed_worker_code()])
    return command


def _replay_process_metadata(
    *,
    returncode: int | None,
    timed_out: bool,
    stdout: bytes,
    stderr: bytes,
) -> dict[str, Any]:
    return {
        "executable": str(Path(sys.executable).resolve()),
        "fresh_python_process": True,
        "python_optimization_level": sys.flags.optimize,
        "timeout_seconds": _REPLAY_TIMEOUT_SECONDS,
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout_sha256": _sha256(stdout),
        "stderr_sha256": _sha256(stderr),
    }


def _run_fresh_replay_child(
    *,
    result: dict[str, Any],
    run_root: Path,
) -> dict[str, Any]:
    """Replay exactly one rerun receipt in a second fresh CPython child."""

    request = {
        "schema": _REPLAY_REQUEST_SCHEMA,
        "run_root": str(run_root),
    }
    try:
        completed = subprocess.run(
            _fresh_replay_command(),
            input=canonical_json(request),
            capture_output=True,
            check=False,
            timeout=_REPLAY_TIMEOUT_SECONDS,
        )
        stdout, stderr = completed.stdout, completed.stderr
        metadata = _replay_process_metadata(
            returncode=completed.returncode,
            timed_out=False,
            stdout=stdout,
            stderr=stderr,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
        metadata = _replay_process_metadata(
            returncode=None,
            timed_out=True,
            stdout=stdout,
            stderr=stderr,
        )
        raise RepairOutcomeError("fresh rerun independent replay timed out") from exc
    except OSError as exc:
        raise RepairOutcomeError(
            f"fresh rerun independent replay could not start: {exc}"
        ) from exc
    if len(stdout) > _MAX_REPLAY_STREAM_BYTES or len(stderr) > _MAX_REPLAY_STREAM_BYTES:
        raise RepairOutcomeError("fresh rerun independent replay stream exceeded byte bound")
    try:
        summary = _parse_canonical_object(stdout, "fresh rerun independent replay")
    except FailureRepairError as exc:
        detail = stderr.decode("utf-8", errors="replace")[:1_000]
        raise RepairOutcomeError(
            f"fresh rerun independent replay returned no canonical result: {detail}"
        ) from exc
    expected_exit = {
        "ELIGIBLE": 0,
        "BLOCKED": 1,
        "PARKED": 4,
    }.get(result.get("disposition"))
    if expected_exit is None or completed.returncode != expected_exit:
        raise RepairOutcomeError("fresh rerun independent replay exit/result mismatch")
    return {"summary": summary, "process": metadata}


def _build_outcome(
    *,
    parent: dict[str, Any],
    rerun: dict[str, Any],
    rerun_root: Path,
    execution_mode: str,
) -> dict[str, Any]:
    """Build the exact non-promoting outcome body from independently checked runs."""

    execution = _execution_record(execution_mode)
    contract = parent["contract"]
    plan = contract["repair_plan"]
    event = contract["failure_event"]
    parent_result = parent["result"]
    rerun_result = rerun["result"]
    rerun_evidence = rerun["evidence"]
    rerun_disposition = rerun_result["disposition"]
    if rerun_disposition not in _OUTCOME_STATES:
        raise RepairOutcomeError("fresh rerun disposition is not independently consumable")
    parent_bindings = event["parent_bindings"]
    body = {
        "schema": REPAIR_OUTCOME_SCHEMA,
        "policy_id": REPAIR_OUTCOME_POLICY_ID,
        "outcome_verifier": _outcome_source_metadata(),
        "parent": {
            "capability_run_root": str(parent["run_root"]),
            "repair_plan_path": str(parent["repair_plan_path"]),
            "repair_contract_sha256": _sha256(canonical_json(contract)),
            "failure_event_sha256": contract["failure_event_sha256"],
            "repair_plan_sha256": contract["repair_plan_sha256"],
            "capability_id": parent_result["capability_id"],
            "request_id": parent_result["request_id"],
            "disposition": parent_result["disposition"],
            "reason": parent_result["reason"],
            "capability_result_sha256": parent_bindings["capability_result_sha256"],
            "capability_receipt_sha256": parent_bindings["capability_receipt_sha256"],
            "flow_receipt_sha256": parent_bindings["flow_receipt_sha256"],
            "flow_policy_sha256": parent_bindings["flow_policy_sha256"],
            "controller_origin_attestation_sha256": parent_bindings[
                "controller_origin_attestation_sha256"
            ],
        },
        "rerun": {
            "capability_run_root": str(rerun_root),
            "capability_result_path": str(rerun["result_path"]),
            "capability_id": rerun_result["capability_id"],
            "request_id": rerun_result["request_id"],
            "run_id": rerun_result["run_id"],
            "disposition": rerun_disposition,
            "reason": rerun_result["reason"],
            "capability_result_sha256": _sha256(canonical_json(rerun_result)),
            "capability_receipt_sha256": rerun_result["capability_receipt_sha256"],
            "flow_receipt_sha256": rerun_result["flow_receipt_sha256"],
            "flow_policy_sha256": rerun_result["flow_policy_sha256"],
            "controller_origin_attestation_sha256": rerun_evidence[
                "origin_attestation_sha256"
            ],
        },
        "verification": {
            "parent_contract": "regenerated_and_matched",
            "rerun_receipt": "in_process_and_fresh_child_independently_replayed",
            "same_capability": True,
            "same_flow_policy": True,
            "same_controller_registry": True,
            "same_controller_origin_runner_and_issuer_pins": True,
            "same_runtime_identity": True,
            "fresh_challenge_policy": plan["required_regression_guard"][
                "rerun_challenge_policy"
            ],
            "fresh_child_replay": rerun["independent_replay"],
        },
        "execution": execution,
        "outcome_state": _OUTCOME_STATES[rerun_disposition],
        # This is intentionally never an eligible gate result.  A fresh
        # successful probe does not repair the parent failure or promote an
        # engine; it is retained for an explicit human follow-up decision.
        "disposition": "PARKED",
        "repair_resolved": False,
        "next_step": "human_review_required",
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": _claim_ceiling_for_mode(execution_mode),
    }
    return {**body, "outcome_sha256": _sha256(canonical_json(body))}


def _validate_outcome_shape(outcome: object) -> dict[str, Any]:
    if not isinstance(outcome, dict) or set(outcome) != _OUTCOME_FIELDS:
        raise RepairOutcomeError("repair outcome fields differ")
    if outcome.get("schema") != REPAIR_OUTCOME_SCHEMA:
        raise RepairOutcomeError("repair outcome schema differs")
    if outcome.get("policy_id") != REPAIR_OUTCOME_POLICY_ID:
        raise RepairOutcomeError("repair outcome policy differs")
    _require_sha256(outcome.get("outcome_sha256"), "repair outcome digest")
    body = dict(outcome)
    digest = body.pop("outcome_sha256")
    if digest != _sha256(canonical_json(body)):
        raise RepairOutcomeError("repair outcome digest does not match its body")
    fixed = {
        "disposition": "PARKED",
        "repair_resolved": False,
        "next_step": "human_review_required",
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
    }
    for field, expected in fixed.items():
        if outcome.get(field) != expected:
            raise RepairOutcomeError(f"repair outcome fixed field differs: {field}")
    _execution_mode_from_outcome(outcome)
    return outcome


def _existing_outcome_root(value: object, label: str) -> Path:
    if not isinstance(value, str):
        raise RepairOutcomeError(f"{label} must be one absolute directory path")
    path = Path(value)
    if not path.is_absolute() or path.is_symlink():
        raise RepairOutcomeError(f"{label} must be one absolute non-symlink directory")
    try:
        path = path.resolve(strict=True)
    except OSError as exc:
        raise RepairOutcomeError(f"{label} is unavailable: {exc}") from exc
    if not path.is_dir():
        raise RepairOutcomeError(f"{label} must be one directory")
    return path


def verify_fresh_rerun_outcome(
    outcome: object,
    *,
    expected_run_root: Path | None = None,
) -> dict[str, Any]:
    """Independently recheck one retained non-promoting fresh-rerun outcome."""

    outcome = _validate_outcome_shape(outcome)
    execution_mode = _execution_mode_from_outcome(outcome)
    parent_data = outcome["parent"]
    rerun_data = outcome["rerun"]
    if not isinstance(parent_data, dict) or not isinstance(rerun_data, dict):
        raise RepairOutcomeError("repair outcome parent or rerun binding is invalid")
    parent_root = _existing_outcome_root(
        parent_data.get("capability_run_root"), "parent capability run root"
    )
    rerun_root = _existing_outcome_root(
        rerun_data.get("capability_run_root"), "rerun capability run root"
    )
    if expected_run_root is not None:
        expected = Path(expected_run_root).expanduser()
        if expected.is_symlink():
            raise RepairOutcomeError("expected repair outcome run root must not be a symlink")
        try:
            expected = expected.resolve(strict=True)
        except OSError as exc:
            raise RepairOutcomeError(
                f"expected repair outcome run root is unavailable: {exc}"
            ) from exc
        if rerun_root != expected:
            raise RepairOutcomeError("repair outcome rerun root differs from expected root")
    if (
        rerun_root == parent_root
        or parent_root in rerun_root.parents
        or rerun_root in parent_root.parents
    ):
        raise RepairOutcomeError("repair outcome rerun root is not disjoint from parent run")
    outcome_path, raw_outcome = _read_regular_bytes(
        rerun_root / REPAIR_OUTCOME_NAME,
        REPAIR_OUTCOME_NAME,
    )
    persisted = _parse_canonical_object(raw_outcome, REPAIR_OUTCOME_NAME)
    if persisted != outcome:
        raise RepairOutcomeError("persisted repair outcome differs from submitted outcome")
    parent = _load_verified_parent(parent_root)
    rerun = _load_verified_rerun(parent=parent, run_root=rerun_root)
    expected_outcome = _build_outcome(
        parent=parent,
        rerun=rerun,
        rerun_root=rerun_root,
        execution_mode=execution_mode,
    )
    if outcome != expected_outcome:
        raise RepairOutcomeError("repair outcome differs from regenerated controller outcome")
    _checked_path, checked_raw_outcome = _read_regular_bytes(
        outcome_path,
        REPAIR_OUTCOME_NAME,
    )
    if checked_raw_outcome != raw_outcome:
        raise RepairOutcomeError("repair outcome changed during verification")
    return {
        "outcome": outcome,
        "parent_run_root": parent_root,
        "rerun_run_root": rerun_root,
        "rerun_disposition": rerun["result"]["disposition"],
    }


def _write_outcome_exclusive(run_root: Path, outcome: dict[str, Any]) -> Path:
    output = run_root / REPAIR_OUTCOME_NAME
    try:
        with output.open("x", encoding="utf-8") as stream:
            stream.write(canonical_json(outcome).decode("utf-8"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except (OSError, TypeError, ValueError) as exc:
        raise RepairOutcomeError(f"could not persist repair outcome: {exc}") from exc
    return output


def _run_plan_bound_fresh_rerun(
    *,
    capability_run_root: Path,
    run_root: Path,
    execution_mode: str,
) -> dict[str, Any]:
    """Execute exactly one fixed rerun after selecting one closed caller mode."""

    # Validate before starting an external worker.  A new call site cannot
    # smuggle a third authority or execution mode into the outcome.
    _execution_record(execution_mode)
    parent_before = _load_verified_parent(capability_run_root)
    rerun_root = _require_new_outcome_root(run_root, parent_before["run_root"])
    contract = parent_before["contract"]
    request_id = _derived_request_id(contract["repair_plan_sha256"])
    try:
        run_capability_flow(
            capability_id=parent_before["result"]["capability_id"],
            request_id=request_id,
            run_root=rerun_root,
        )
    except (CapabilityDispatchError, OSError, ValueError) as exc:
        raise RepairOutcomeError(f"fresh rerun dispatch failed: {exc}") from exc
    # Re-derive the parent after the external action. A source, policy, or
    # artifact change cannot be hidden by the earlier admission check and then
    # retained as a seemingly valid outcome.
    parent_after = _load_verified_parent(capability_run_root)
    if (
        parent_after["contract"] != parent_before["contract"]
        or parent_after["result"] != parent_before["result"]
    ):
        raise RepairOutcomeError("parent repair contract changed during fresh rerun")
    rerun = _load_verified_rerun(parent=parent_after, run_root=rerun_root)
    outcome = _build_outcome(
        parent=parent_after,
        rerun=rerun,
        rerun_root=rerun_root,
        execution_mode=execution_mode,
    )
    _write_outcome_exclusive(rerun_root, outcome)
    verified = verify_fresh_rerun_outcome(outcome, expected_run_root=rerun_root)
    return verified["outcome"]


def run_fresh_rerun_outcome(
    *,
    capability_run_root: Path,
    run_root: Path,
    execute_fresh_rerun: bool,
) -> dict[str, Any]:
    """Run one explicitly acknowledged, plan-bound fresh capability rerun.

    ``execute_fresh_rerun`` is a fixed acknowledgement, not a configurable
    action choice.  The parent plan grants no execution permission and records
    zero attempts.  This public surface therefore stays manual and cannot be
    used to select a capability, worker, verifier, tolerance, or mutation.
    """

    if execute_fresh_rerun is not True:
        raise RepairOutcomeError("fresh rerun requires the fixed explicit acknowledgement")
    return _run_plan_bound_fresh_rerun(
        capability_run_root=capability_run_root,
        run_root=run_root,
        execution_mode=_OPERATOR_ACKNOWLEDGEMENT_MODE,
    )


def _run_capability_suite_fresh_rerun_outcome(
    *,
    capability_run_root: Path,
    run_root: Path,
) -> dict[str, Any]:
    """Run the suite's one fixed controller-selected non-mutating follow-up.

    This is intentionally not a CLI surface.  The fixed-order capability suite
    calls it after replaying the parent receipt and only when the regenerated
    closed repair table selected ``fresh_rerun``.  The function accepts neither
    a caller-selected action nor any engine/profile/worker/verifier/tolerance
    override.  It is source-level routing, not hostile-host containment.
    """

    return _run_plan_bound_fresh_rerun(
        capability_run_root=capability_run_root,
        run_root=run_root,
        execution_mode=_CAPABILITY_SUITE_HOOK_MODE,
    )
