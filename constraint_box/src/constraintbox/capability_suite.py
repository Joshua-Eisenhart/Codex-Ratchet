"""Controller-owned integration suite for the fixed external capabilities.

This is a test harness, not a new CB kernel layer. It invokes each fixed
ordered Mini-LevOS capability flow in one fresh controller-selected CPython
child, then independently replays its receipt in a second fresh child. The
parent records only bounded summaries; it cannot release, promote, or claim
that an external engine is generally ready.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from .capability_origin import capability_ids
from .failure_repair import REPAIR_PLAN_NAME, load_verified_repair_contract_for_run
from .intake import IntakeError, canonical_json, parse_json_object
from .repair_outcome import (
    REPAIR_OUTCOME_NAME,
    _run_capability_suite_fresh_rerun_outcome,
)


SCHEMA = "constraintbox.capability-suite-receipt.v1"
RECEIPT_NAME = "capability_suite_receipt.json"
REPLAY_RESULT_NAME = "capability_independent_replay.json"
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_HEX = re.compile(r"[0-9a-f]{64}")
_CAPABILITY_IDS = capability_ids()
_COMPONENT_REQUEST_SCHEMA = "constraintbox.capability-suite-component-request.v1"
_REPLAY_REQUEST_SCHEMA = "constraintbox.capability-suite-replay-request.v1"
_REPLAY_RESULT_SCHEMA = "constraintbox.capability-suite-replay-result.v1"
_REPAIR_HOOK_SUMMARY_SCHEMA = "constraintbox.capability-suite-repair-hook.v1"
_RUNTIME_CONTRACT_REPORT_SCHEMA = "constraintbox.capability-runtime-contract-report.v1"
_CONTROLLER_FRESH_RERUNS_DIRNAME = "controller_fresh_reruns"
_COMPONENT_TIMEOUT_SECONDS = 180
_MAX_COMPONENT_STREAM_BYTES = 8 * 1024 * 1024
CLAIM_CEILING = (
    "one local sequential run of the fixed external capability profiles, each "
    "executed and independently replayed in fixed fresh CPython child "
    "processes; not a general engine readiness result, full sim-stack "
    "readiness, a statement that every adapter is portable, CR truth, scientific "
    "proof, hostile-code containment, release, or canonical promotion"
)
_REQUIRED_RESULT_FIELDS = frozenset(
    {
        "schema",
        "capability_id",
        "request_id",
        "request_sha256",
        "run_id",
        "flow_policy_sha256",
        "disposition",
        "reason",
        "capability_receipt_sha256",
        "flow_receipt_sha256",
        "artifacts",
        "external_system",
        "kernel_membership",
        "release_allowed",
        "engine_readiness_claim",
        "cr_truth_claim",
        "promotion_allowed",
        "claim_ceiling",
    }
)

# Operation eligibility and runtime-policy migration are separate controller
# facts.  A profile can have an implemented controller-selected compatibility
# policy without a fresh clean-host installation proof.  An adapter can also
# execute and replay locally while retaining an old Mac path, exact wheel hash,
# or other host policy.  The suite must expose both kinds of debt instead of
# flattening a locally green row into a portable-product claim.
_RUNTIME_CONTRACT_BY_CAPABILITY: dict[str, dict[str, object]] = {
    "pytorch-jacobian-v1": {
        "state": "PROFILE_IMPLEMENTED_UNVERIFIED",
        "profile_implemented": True,
        "clean_install_verified": False,
        "runtime_policy": "external-cpython-3.11-3.13-v1",
        "migration_required": False,
    },
    "jax-autodiff-v1": {
        "state": "PROFILE_IMPLEMENTED_UNVERIFIED",
        "profile_implemented": True,
        "clean_install_verified": False,
        "runtime_policy": "external-cpython-3.11-3.13-v1",
        "migration_required": False,
    },
    "pysindy-affine-generator-v1": {
        "state": "PROFILE_IMPLEMENTED_UNVERIFIED",
        "profile_implemented": True,
        "clean_install_verified": False,
        "runtime_policy": "external-cpython-3.11-3.13-v1",
        "migration_required": False,
    },
    "julia-diffeq-v1": {
        "state": "PROFILE_IMPLEMENTED_UNVERIFIED",
        "profile_implemented": True,
        "clean_install_verified": False,
        "runtime_policy": "external-julia-1.12-v1",
        "migration_required": False,
    },
    "scipy-expm-rotation-v1": {
        "state": "PROFILE_IMPLEMENTED_UNVERIFIED",
        "profile_implemented": True,
        "clean_install_verified": False,
        "runtime_policy": "external-cpython-3.11-3.13-v1",
        "migration_required": False,
    },
    "diffrax-tsit5-affine-flow-v1": {
        "state": "PROFILE_IMPLEMENTED_UNVERIFIED",
        "profile_implemented": True,
        "clean_install_verified": False,
        "runtime_policy": "external-cpython-3.11-3.13-v1",
        "migration_required": False,
    },
    "graph-topology-crosscheck-v1": {
        "state": "PROFILE_IMPLEMENTED_UNVERIFIED",
        "profile_implemented": True,
        "clean_install_verified": False,
        "runtime_policy": "external-cpython-compatible-api-v1",
        "migration_required": False,
    },
    "pydmd-discrete-rate-v1": {
        "state": "PROFILE_IMPLEMENTED_UNVERIFIED",
        "profile_implemented": True,
        "clean_install_verified": False,
        "runtime_policy": "external-cpython-3.11-3.13-v1",
        "migration_required": False,
    },
    "pymdp-two-state-inference-v1": {
        "state": "PROFILE_IMPLEMENTED_UNVERIFIED",
        "profile_implemented": True,
        "clean_install_verified": False,
        "runtime_policy": "external-cpython-3.11-3.13-v1",
        "migration_required": False,
    },
    "pykoopman-identity-edmd-v1": {
        "state": "LEGACY_HOST_BOUND",
        "profile_implemented": False,
        "clean_install_verified": False,
        "runtime_policy": "legacy_exact_runtime_and_artifact_policy",
        "migration_required": True,
    },
    "quimb-cotengra-bounded-suite-v1": {
        "state": "LEGACY_HOST_BOUND",
        "profile_implemented": False,
        "clean_install_verified": False,
        "runtime_policy": "legacy_exact_runtime_and_artifact_policy",
        "migration_required": True,
    },
    "multiengine-dlpack-diffeq-v1": {
        "state": "LEGACY_HOST_BOUND",
        "profile_implemented": False,
        "clean_install_verified": False,
        "runtime_policy": "legacy_exact_runtime_and_artifact_policy",
        "migration_required": True,
    },
    "basic-packet-cross-engine-v1": {
        "state": "LEGACY_HOST_BOUND",
        "profile_implemented": False,
        "clean_install_verified": False,
        "runtime_policy": "legacy_fixed_fixture_runtime_policy",
        "migration_required": True,
    },
    "e3nn-wigner-crosscheck-v1": {
        "state": "PROFILE_IMPLEMENTED_UNVERIFIED",
        "profile_implemented": True,
        "clean_install_verified": False,
        "runtime_policy": "external-cpython-3.11-3.13-v1",
        "migration_required": False,
    },
}
if set(_RUNTIME_CONTRACT_BY_CAPABILITY) != set(_CAPABILITY_IDS):
    raise RuntimeError("capability runtime-contract table differs from registry")


class CapabilitySuiteError(ValueError):
    """The controller-owned capability integration suite could not run."""


class ComponentProcessError(CapabilitySuiteError):
    """One isolated fixed profile died, timed out, or returned invalid output."""

    def __init__(self, message: str, metadata: dict[str, Any]) -> None:
        super().__init__(message)
        self.metadata = metadata


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _runtime_contract(capability_id: str) -> dict[str, object]:
    """Return one closed portability classification for a registered profile."""

    try:
        return dict(_RUNTIME_CONTRACT_BY_CAPABILITY[capability_id])
    except KeyError as exc:
        raise CapabilitySuiteError(
            f"registered capability has no runtime-contract classification: {capability_id}"
        ) from exc


def _runtime_contract_report(
    capability_ids_in_run: tuple[str, ...],
) -> dict[str, object]:
    profiled = [
        capability_id
        for capability_id in capability_ids_in_run
        if _runtime_contract(capability_id)["profile_implemented"] is True
    ]
    legacy = [
        capability_id
        for capability_id in capability_ids_in_run
        if _runtime_contract(capability_id)["profile_implemented"] is False
    ]
    return {
        "schema": _RUNTIME_CONTRACT_REPORT_SCHEMA,
        "profile_implemented_unverified_capability_ids": profiled,
        "legacy_host_bound_capability_ids": legacy,
        "runtime_profile_migration_state": "COMPLETE" if not legacy else "PARTIAL",
        "clean_external_install_verified_capability_ids": [],
        "full_external_suite_clean_install_verified": False,
        "full_external_suite_profile_implemented": not legacy,
        "full_external_suite_portable_install_claim": False,
        "claim_ceiling": (
            "a controller-owned classification of runtime-policy migration; "
            "PROFILE_IMPLEMENTED_UNVERIFIED means source-level profile "
            "implementation, not a clean-host external-install proof; local "
            "operation eligibility remains a separate result"
        ),
    }


def _component_worker_code(module: str) -> str:
    """Return the fixed child bootstrap; no caller input enters its code text."""

    source_root = Path(__file__).resolve().parents[1]
    return (
        "import sys\n"
        f"sys.path.insert(0, {str(source_root)!r})\n"
        f"from {module} import main\n"
        "raise SystemExit(main())\n"
    )


def _component_process_metadata(
    *,
    returncode: int | None,
    timed_out: bool,
    stdout: bytes,
    stderr: bytes,
) -> dict[str, Any]:
    return {
        "executable": str(Path(sys.executable).resolve()),
        "fresh_python_process": True,
        "isolated_python": False,
        "timeout_seconds": _COMPONENT_TIMEOUT_SECONDS,
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout_sha256": _sha256(stdout),
        "stderr_sha256": _sha256(stderr),
    }


def _run_fixed_component(
    *,
    capability_id: str,
    request_id: str,
    run_root: Path,
) -> dict[str, Any]:
    """Run one fixed profile in a fresh child CPython process.

    This keeps optional native/import state local to the profile. A child crash
    becomes an auditable component error rather than terminating the controller
    or laundering later profiles into a green aggregate.
    """

    request = {
        "schema": _COMPONENT_REQUEST_SCHEMA,
        "capability_id": capability_id,
        "request_id": request_id,
        "run_root": str(run_root),
    }
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                "-c",
                _component_worker_code("constraintbox.capability_suite_worker"),
            ],
            input=canonical_json(request),
            capture_output=True,
            check=False,
            timeout=_COMPONENT_TIMEOUT_SECONDS,
        )
        stdout, stderr = completed.stdout, completed.stderr
        metadata = _component_process_metadata(
            returncode=completed.returncode,
            timed_out=False,
            stdout=stdout,
            stderr=stderr,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
        metadata = _component_process_metadata(
            returncode=None,
            timed_out=True,
            stdout=stdout,
            stderr=stderr,
        )
        raise ComponentProcessError("fixed component timed out", metadata) from exc
    if len(stdout) > _MAX_COMPONENT_STREAM_BYTES or len(stderr) > _MAX_COMPONENT_STREAM_BYTES:
        raise ComponentProcessError("fixed component stream exceeded byte bound", metadata)
    try:
        result = parse_json_object(stdout)
    except IntakeError as exc:
        detail = stderr.decode("utf-8", errors="replace")[:1_000]
        raise ComponentProcessError(
            f"fixed component returned no canonical result: {detail}", metadata
        ) from exc
    if stdout != canonical_json(result) + b"\n":
        raise ComponentProcessError("fixed component result is not canonical JSON", metadata)
    expected_exit = {
        "ELIGIBLE": 0,
        "BLOCKED": 1,
        "PARKED": 4,
        "HOLD": 5,
    }.get(result.get("disposition"))
    if expected_exit is None or completed.returncode != expected_exit:
        raise ComponentProcessError("fixed component exit/result mismatch", metadata)
    return result


def _verify_fixed_component(
    *,
    result: dict[str, Any],
    run_root: Path,
) -> dict[str, Any]:
    """Replay a component in a second fresh process before aggregation."""

    request = {
        "schema": _REPLAY_REQUEST_SCHEMA,
        "run_root": str(run_root),
    }
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                "-c",
                _component_worker_code(
                    "constraintbox.capability_suite_replay_worker"
                ),
            ],
            input=canonical_json(request),
            capture_output=True,
            check=False,
            timeout=_COMPONENT_TIMEOUT_SECONDS,
        )
        stdout, stderr = completed.stdout, completed.stderr
        metadata = _component_process_metadata(
            returncode=completed.returncode,
            timed_out=False,
            stdout=stdout,
            stderr=stderr,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
        metadata = _component_process_metadata(
            returncode=None,
            timed_out=True,
            stdout=stdout,
            stderr=stderr,
        )
        raise ComponentProcessError("fixed component replay timed out", metadata) from exc
    if len(stdout) > _MAX_COMPONENT_STREAM_BYTES or len(stderr) > _MAX_COMPONENT_STREAM_BYTES:
        raise ComponentProcessError(
            "fixed component replay stream exceeded byte bound", metadata
        )
    try:
        verified = parse_json_object(stdout)
    except IntakeError as exc:
        detail = stderr.decode("utf-8", errors="replace")[:1_000]
        raise ComponentProcessError(
            f"fixed component replay returned no canonical result: {detail}",
            metadata,
        ) from exc
    if stdout != canonical_json(verified) + b"\n":
        raise ComponentProcessError(
            "fixed component replay result is not canonical JSON", metadata
        )
    expected_fields = {
        "schema",
        "capability_id",
        "disposition",
        "capability_result_sha256",
        "origin_attestation_sha256",
        "flow_ledger_head_sha256",
        "independent_replay",
        "repair_plan",
    }
    if set(verified) != expected_fields:
        raise ComponentProcessError("fixed component replay fields differ", metadata)
    if (
        verified.get("schema") != _REPLAY_RESULT_SCHEMA
        or verified.get("capability_id") != result.get("capability_id")
        or verified.get("disposition") != result.get("disposition")
        or verified.get("capability_result_sha256")
        != _sha256(canonical_json(result))
        or verified.get("independent_replay") is not True
    ):
        raise ComponentProcessError("fixed component replay binding differs", metadata)
    expected_exit = {
        "ELIGIBLE": 0,
        "BLOCKED": 1,
        "PARKED": 4,
    }.get(result.get("disposition"))
    if expected_exit is None or completed.returncode != expected_exit:
        raise ComponentProcessError(
            "fixed component replay exit/result mismatch", metadata
        )
    return verified


def _write_new_json(path: Path, value: dict[str, Any]) -> None:
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(canonical_json(value).decode("utf-8"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise CapabilitySuiteError(
            f"could not persist capability-suite receipt: {exc}"
        ) from exc


def _repair_hook_summary(
    *,
    state: str,
    reason: str,
    selected_action: str | None,
    attempts: int,
    automatic_fixed_replay: bool,
) -> dict[str, Any]:
    """Build the fixed audit record for the suite's one repair decision."""

    return {
        "schema": _REPAIR_HOOK_SUMMARY_SCHEMA,
        "state": state,
        "reason": reason,
        "selected_action": selected_action,
        "controller_selected": True,
        "attempts": attempts,
        "automatic_fixed_replay": automatic_fixed_replay,
        "automatic_retry_or_tuning": False,
        "automatic_retry_loop": False,
        "automatic_tuning": False,
        "llm_decision_authority": False,
        "source_or_environment_mutation_requested_or_performed": False,
        "release_allowed": False,
        "promotion_allowed": False,
    }


def _controller_repair_hook_for_verified_component(
    *,
    verified: dict[str, Any],
    capability_id: str,
    component_root: Path,
    suite_root: Path,
    component_index: int,
) -> dict[str, Any]:
    """Consume one closed repair decision for the first non-pass component.

    The replayed plan is only a compact binding.  The private outcome runner
    regenerates and verifies the full parent contract before it dispatches one
    same-capability fresh child.  This function is called at most once from a
    suite invocation, and the resulting child never enters this suite again.
    """

    repair_plan = verified.get("repair_plan")
    if repair_plan is None:
        return _repair_hook_summary(
            state="EVALUATION_ERROR",
            reason="first_noneligible_component_has_no_replayed_repair_plan",
            selected_action=None,
            attempts=0,
            automatic_fixed_replay=False,
        )
    if not isinstance(repair_plan, dict) or set(repair_plan) != {
        "path",
        "repair_plan_sha256",
        "selected_action",
        "execution_authorized",
    }:
        return _repair_hook_summary(
            state="EVALUATION_ERROR",
            reason="replayed_repair_plan_shape_invalid",
            selected_action=None,
            attempts=0,
            automatic_fixed_replay=False,
        )
    selected_action = repair_plan.get("selected_action")
    plan_sha256 = repair_plan.get("repair_plan_sha256")
    if (
        not isinstance(selected_action, str)
        or not isinstance(repair_plan.get("path"), str)
        or not isinstance(plan_sha256, str)
        or _HEX.fullmatch(plan_sha256) is None
        or repair_plan.get("execution_authorized") is not False
    ):
        return _repair_hook_summary(
            state="EVALUATION_ERROR",
            reason="replayed_repair_plan_binding_invalid",
            selected_action=selected_action if isinstance(selected_action, str) else None,
            attempts=0,
            automatic_fixed_replay=False,
        )
    if selected_action != "fresh_rerun":
        return _repair_hook_summary(
            state="NOT_EXECUTED",
            reason="first_noneligible_component_selected_nonexecuting_action",
            selected_action=selected_action,
            attempts=0,
            automatic_fixed_replay=False,
        )

    # The compact child-replay record is not enough to choose even a derived
    # output name. Reopen the retained full contract and make the two bindings
    # agree before any fresh rerun directory is created.
    try:
        verified_parent = load_verified_repair_contract_for_run(component_root)
        contract = verified_parent["contract"]
        full_plan = contract.get("repair_plan")
        full_plan_sha256 = contract.get("repair_plan_sha256")
        expected_plan_path = component_root / REPAIR_PLAN_NAME
        if (
            not isinstance(full_plan, dict)
            or full_plan_sha256 != plan_sha256
            or full_plan.get("selected_action") != "fresh_rerun"
            or full_plan.get("execution_authorized") is not False
            or repair_plan.get("path") != str(expected_plan_path)
        ):
            raise CapabilitySuiteError(
                "replayed fresh-rerun plan differs from retained repair contract"
            )
    except (OSError, ValueError, KeyError) as exc:
        summary = _repair_hook_summary(
            state="EVALUATION_ERROR",
            reason="replayed_fresh_rerun_plan_not_current_and_verified",
            selected_action="fresh_rerun",
            attempts=0,
            automatic_fixed_replay=False,
        )
        summary["exception_type"] = type(exc).__name__
        summary["error"] = str(exc)
        return summary

    rerun_parent = suite_root / _CONTROLLER_FRESH_RERUNS_DIRNAME
    rerun_root = rerun_parent / (
        f"{component_index:02d}_{capability_id}_{plan_sha256[:16]}"
    )
    relative_rerun_root = rerun_root.relative_to(suite_root)
    try:
        # The suite root is new, so a pre-existing derived parent is a race or
        # stale artifact.  Either case fails closed instead of creating a
        # second attempt or accepting an arbitrary caller path.
        rerun_parent.mkdir()
        if rerun_parent.is_symlink():
            raise CapabilitySuiteError("controller fresh-rerun parent must not be a symlink")
        outcome = _run_capability_suite_fresh_rerun_outcome(
            capability_run_root=component_root,
            run_root=rerun_root,
        )
    except (OSError, ValueError) as exc:
        summary = _repair_hook_summary(
            state="EVALUATION_ERROR",
            reason="controller_selected_fresh_rerun_failed",
            selected_action="fresh_rerun",
            attempts=1,
            automatic_fixed_replay=True,
        )
        summary["exception_type"] = type(exc).__name__
        summary["error"] = str(exc)
        summary["rerun_root"] = str(relative_rerun_root)
        return summary

    execution = outcome.get("execution") if isinstance(outcome, dict) else None
    if (
        not isinstance(outcome, dict)
        or not isinstance(outcome.get("outcome_sha256"), str)
        or _HEX.fullmatch(outcome["outcome_sha256"]) is None
        or outcome.get("disposition") != "PARKED"
        or outcome.get("repair_resolved") is not False
        or outcome.get("promotion_allowed") is not False
        or outcome.get("release_allowed") is not False
        or not isinstance(execution, dict)
        or execution.get("invocation_kind")
        != "controller_selected_capability_suite_hook"
        or execution.get("execution_authority") != "fixed_capability_suite_hook"
        or execution.get("automatic_fixed_replay") is not True
        or execution.get("automatic_tuning") is not False
        or execution.get("llm_decision_authority") is not False
    ):
        return _repair_hook_summary(
            state="EVALUATION_ERROR",
            reason="controller_selected_fresh_rerun_outcome_invalid",
            selected_action="fresh_rerun",
            attempts=1,
            automatic_fixed_replay=True,
        )

    outcome_path = rerun_root / REPAIR_OUTCOME_NAME
    try:
        if outcome_path.is_symlink():
            raise CapabilitySuiteError("fresh rerun outcome must not be a symlink")
        raw_outcome = outcome_path.read_bytes()
        persisted_outcome = parse_json_object(raw_outcome)
        if raw_outcome != canonical_json(persisted_outcome) + b"\n":
            raise CapabilitySuiteError("fresh rerun outcome is not canonical JSON")
        if persisted_outcome != outcome:
            raise CapabilitySuiteError("fresh rerun outcome differs from returned outcome")
        relative_outcome = outcome_path.relative_to(suite_root)
    except (OSError, IntakeError, ValueError) as exc:
        summary = _repair_hook_summary(
            state="EVALUATION_ERROR",
            reason="controller_selected_fresh_rerun_artifact_invalid",
            selected_action="fresh_rerun",
            attempts=1,
            automatic_fixed_replay=True,
        )
        summary["exception_type"] = type(exc).__name__
        summary["error"] = str(exc)
        summary["rerun_root"] = str(relative_rerun_root)
        return summary

    summary = _repair_hook_summary(
        state="VERIFIED",
        reason="controller_selected_fresh_rerun_independently_verified",
        selected_action="fresh_rerun",
        attempts=1,
        automatic_fixed_replay=True,
    )
    summary.update(
        {
            "rerun_root": str(relative_rerun_root),
            "outcome_artifact": str(relative_outcome),
            "outcome_sha256": outcome["outcome_sha256"],
            "outcome_state": outcome["outcome_state"],
            "disposition": outcome["disposition"],
            "repair_resolved": outcome["repair_resolved"],
        }
    )
    return summary


def _validate_component_result(
    result: object,
    *,
    capability_id: str,
    request_id: str,
    run_root: Path,
) -> dict[str, Any]:
    """Refuse a malformed component result before the suite can report it."""

    if not isinstance(result, dict) or set(result) != _REQUIRED_RESULT_FIELDS:
        raise CapabilitySuiteError(
            f"{capability_id} returned an invalid capability-result shape"
        )
    fixed = {
        "capability_id": capability_id,
        "request_id": request_id,
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
    }
    for key, expected in fixed.items():
        if result.get(key) != expected:
            raise CapabilitySuiteError(
                f"{capability_id} result fixed field differs: {key}"
            )
    if result.get("disposition") not in {"ELIGIBLE", "BLOCKED", "PARKED", "HOLD"}:
        raise CapabilitySuiteError(f"{capability_id} result disposition is invalid")
    for key in (
        "request_sha256",
        "flow_policy_sha256",
        "capability_receipt_sha256",
        "flow_receipt_sha256",
    ):
        if not isinstance(result.get(key), str) or _HEX.fullmatch(result[key]) is None:
            raise CapabilitySuiteError(f"{capability_id} result {key} is invalid")
    if not isinstance(result.get("run_id"), str) or _SAFE_ID.fullmatch(result["run_id"]) is None:
        raise CapabilitySuiteError(f"{capability_id} result run_id is invalid")
    artifacts = result.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != {
        "capability_receipt",
        "flow_receipt",
        "flow_ledger",
        "flow_ledger_head",
    }:
        raise CapabilitySuiteError(f"{capability_id} result artifacts are invalid")
    expected_root = run_root.resolve()
    for name, path_text in artifacts.items():
        if not isinstance(path_text, str):
            raise CapabilitySuiteError(f"{capability_id} artifact path is invalid: {name}")
        try:
            path = Path(path_text).resolve(strict=True)
        except OSError as exc:
            raise CapabilitySuiteError(
                f"{capability_id} artifact is unavailable: {name}: {exc}"
            ) from exc
        if expected_root not in (path, *path.parents) or not path.is_file():
            raise CapabilitySuiteError(
                f"{capability_id} artifact escapes its controller run root: {name}"
            )
    return result


def run_capability_suite(
    *,
    request_id: str,
    run_root: Path,
) -> tuple[dict[str, Any], int]:
    """Run every controller-owned external capability profile once, in order."""

    if not isinstance(request_id, str) or _SAFE_ID.fullmatch(request_id) is None:
        raise CapabilitySuiteError("request_id must be one safe bounded identifier")
    if not isinstance(run_root, Path) or not run_root.is_absolute():
        raise CapabilitySuiteError("run_root must be one absolute pathlib.Path")
    try:
        run_root.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise CapabilitySuiteError(
            f"capability-suite run directory must be new: {exc}"
        ) from exc

    components: list[dict[str, Any]] = []
    terminal_states: list[str] = []
    # Exactly one component can consume the hook decision.  This starts as a
    # no-op record so an audit can distinguish "nothing needed repair" from
    # a non-executing or failed controller decision.
    repair_hook = _repair_hook_summary(
        state="NO_ACTION",
        reason="all_components_eligible",
        selected_action=None,
        attempts=0,
        automatic_fixed_replay=False,
    )
    repair_hook.update(
        {
            "selection_rule": "first_noneligible_component_in_fixed_controller_order",
            "decision_made": False,
            "selected_component_index": None,
            "selected_capability_id": None,
            "later_components_not_retried": True,
        }
    )
    for index, capability_id in enumerate(_CAPABILITY_IDS, start=1):
        component_root = run_root / f"{index:02d}_{capability_id}"
        try:
            raw_result = _run_fixed_component(
                capability_id=capability_id,
                request_id=request_id,
                run_root=component_root,
            )
            result = _validate_component_result(
                raw_result,
                capability_id=capability_id,
                request_id=request_id,
                run_root=component_root,
            )
            # A returned dict or existing artifact is never enough for a green
            # suite row. Replay the fixed flow and require the dispatch-origin
            # sidecar in a second fresh process before aggregation.
            verified = _verify_fixed_component(
                result=result,
                run_root=component_root,
            )
            # Retain the compact result emitted by the second fresh verifier.
            # Without this artifact the suite could truthfully say that it
            # replayed a row, but a later audit would have only the parent's
            # assertion rather than the verifier's bound output.
            replay_path = component_root / REPLAY_RESULT_NAME
            _write_new_json(replay_path, verified)
        except (OSError, ValueError) as exc:
            component_error = {
                "capability_id": capability_id,
                "runtime_contract": _runtime_contract(capability_id),
                "state": "EVALUATION_ERROR",
                "reason": "component_exception",
                "exception_type": type(exc).__name__,
                "error": str(exc),
            }
            if isinstance(exc, ComponentProcessError):
                component_error["component_process"] = exc.metadata
            if repair_hook["decision_made"] is False:
                summary = _repair_hook_summary(
                    state="EVALUATION_ERROR",
                    reason="first_noneligible_component_unverified",
                    selected_action=None,
                    attempts=0,
                    automatic_fixed_replay=False,
                )
                component_error["controller_repair_hook"] = summary
                repair_hook.update(summary)
                repair_hook.update(
                    {
                        "decision_made": True,
                        "selected_component_index": index,
                        "selected_capability_id": capability_id,
                    }
                )
            components.append(component_error)
            terminal_states.append("EVALUATION_ERROR")
            continue
        component = {
            "capability_id": capability_id,
            "runtime_contract": _runtime_contract(capability_id),
            "state": result["disposition"],
            "result_sha256": _sha256(canonical_json(result)),
            "result": result,
            "independent_replay": verified,
            "independent_replay_sha256": _sha256(canonical_json(verified)),
            # Keep the aggregate portable when its run directory is archived
            # or copied; static flow results retain their legacy paths, but
            # this new suite-owned evidence need not inherit that weakness.
            "independent_replay_artifact": str(replay_path.relative_to(run_root)),
        }
        repair_plan = verified["repair_plan"]
        if repair_plan is not None:
            component["repair_plan"] = repair_plan
        summary: dict[str, Any] | None = None
        if result["disposition"] != "ELIGIBLE" and repair_hook["decision_made"] is False:
            summary = _controller_repair_hook_for_verified_component(
                verified=verified,
                capability_id=capability_id,
                component_root=component_root,
                suite_root=run_root,
                component_index=index,
            )
            component["controller_repair_hook"] = summary
            repair_hook.update(summary)
            repair_hook.update(
                {
                    "decision_made": True,
                    "selected_component_index": index,
                    "selected_capability_id": capability_id,
                }
            )
        components.append(component)
        # A successful fresh rerun is evidence about the original failure; it
        # never launders that parent non-pass into an eligible suite.  If the
        # controller-owned hook itself cannot produce a verified outcome, make
        # the aggregate failure visible rather than silently retaining only the
        # old blocked state.
        if summary is not None and summary["state"] == "EVALUATION_ERROR":
            terminal_states.append("EVALUATION_ERROR")
        else:
            terminal_states.append(result["disposition"])

    if terminal_states and all(state == "ELIGIBLE" for state in terminal_states):
        disposition = "ELIGIBLE"
        reason = "all_fixed_capability_flows_eligible"
        exit_code = 0
    elif "EVALUATION_ERROR" in terminal_states or "HOLD" in terminal_states:
        disposition = "EVALUATION_ERROR"
        reason = "one_or_more_fixed_capability_flows_unsettled"
        exit_code = 5
    elif "BLOCKED" in terminal_states:
        disposition = "BLOCKED"
        reason = "one_or_more_fixed_capability_flows_blocked"
        exit_code = 1
    else:
        disposition = "PARKED"
        reason = "one_or_more_fixed_capability_flows_parked"
        exit_code = 4
    receipt = {
        "schema": SCHEMA,
        "request_id": request_id,
        "capability_ids": list(_CAPABILITY_IDS),
        "components": components,
        "runtime_contract_report": _runtime_contract_report(_CAPABILITY_IDS),
        "disposition": disposition,
        "reason": reason,
        "sequential_execution": True,
        "controller_selected_order": True,
        "repair_hook": repair_hook,
        "components_external_to_kernel": True,
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    _write_new_json(run_root / RECEIPT_NAME, receipt)
    return receipt, exit_code
