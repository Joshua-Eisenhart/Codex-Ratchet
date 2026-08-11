"""One receipt-bound CB Light premortem-remediation round.

The controller deliberately does not execute a skill, model, MMM, formal
agent, command, installer, shell, browser, or UI.  It accepts one sealed
external action application and records its custody in the existing CB Light
wave ledger.  An externally supplied PASS receipt is never completion here: a
locally invoked trusted deterministic gate would be required by a later slice.
A failed round returns a continuation packet for an external nested wave/skill
layer; it never starts a hidden retry scheduler.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from hookkernel.cb_light_state import StateError, append_only_transaction, connect
from hookkernel.cb_light_wave_state import (
    artifact_sha256_for,
    initialize_wave_state,
    record_artifact,
    record_asset_binding,
    record_wave_attempt,
    record_wave_settlement,
    verify_wave_attempt,
)

from . import premortem_contracts as contracts


REMEDIATION_REQUEST_SCHEMA = "constraintbox.premortem-remediation-request.v1"
REMEDIATION_RESULT_SCHEMA = "constraintbox.premortem-remediation-result.v1"
CLASSIFICATION_RECEIPT_SCHEMA = "constraintbox.premortem-classification-receipt.v1"
PRODUCER_BINDING_EVIDENCE_SCHEMA = "constraintbox.premortem-producer-binding-evidence.v1"
EXTERNAL_ACTION_RECEIPT_SCHEMA = "constraintbox.premortem-external-action-receipt.v1"

CONTROL_PLANE_PROFILE_REPAIR_ACTION = "control_plane_profile_repair"
REMAINING_CANDIDATE_FRONTIER_MEASURE = "remaining-admissible-candidate-frontier"
ISSUE_SCOPE = "single_issue_run"

CLAIM_CEILING = (
    "CB Light single-issue one-round remediation: validates content-addressed external action "
    "and fresh declared-gate receipts in append-only state; does not execute or "
    "independently prove skill, model, provider, installer, command, UI, browser, "
    "repository mutation, CB Heavy, or simulation work."
)

_REQUEST = frozenset(
    {
        "schema", "run_id", "captured_at", "run_policy", "concern", "issue",
        "classification_receipt", "producer_binding", "binding_evidence",
        "repair_candidate", "candidate_frontier", "execution_receipt",
        "action_application", "gate_run", "parent",
    }
)
_CLASSIFICATION = frozenset(
    {
        "schema", "issue_id", "concern_id", "gate_id", "gate_definition_sha256",
        "disposition", "reason_code", "captured_at",
    }
)
_BINDING_EVIDENCE = frozenset(
    {
        "schema", "binding_id", "producer_id", "issue_id", "candidate_id",
        "binding_state", "captured_at",
    }
)
_EXTERNAL_RECEIPT = frozenset(
    {
        "schema", "executor_asset_id", "action_type", "action_id", "action_sha256",
        "candidate_id", "candidate_sha256", "run_policy_sha256", "target_sha256",
        "input_state_sha256", "output_state_sha256", "executed_at",
        "execution_claim_ceiling",
    }
)
_PARENT = frozenset(
    {"attempt_id", "issue_id", "action", "gate_run", "excluded_repair_action_fingerprint"}
)
_ACTION = frozenset(
    {
        "schema", "action_id", "issue_id", "candidate_id", "candidate_sha256",
        "run_policy_sha256", "promotion_rule_id", "round_index", "parent_gate_run_sha256",
        "action_type", "scope_paths", "diff_bound",
    }
)
_INPUT_ARTIFACT = frozenset(
    {
        "attempt_id", "request_sha256", "run_id", "round", "fingerprint", "frontier",
        "action_application_sha256", "execution_receipt_sha256", "gate_sha256",
    }
)


class _Invalid(ValueError):
    pass


@dataclass(frozen=True)
class _Round:
    request: Mapping[str, Any]
    policy: contracts.RunPolicy
    concern: contracts.ConcernRecord
    issue: contracts.Issue
    classification: Mapping[str, Any]
    binding: contracts.ProducerBinding
    evidence: tuple[Mapping[str, Any], ...]
    candidate: contracts.RepairCandidate
    fingerprint: str
    frontier: tuple[str, ...]
    action: contracts.RepairAction
    parent_attempt_id: str | None
    parent_gate: contracts.GateRun | None


def _map(raw: Any, fields: frozenset[str]) -> Mapping[str, Any] | None:
    return raw if isinstance(raw, Mapping) and set(raw) == fields else None


def _text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _sha(value: Any) -> str | None:
    if not isinstance(value, str) or len(value) != 64:
        return None
    return value if all(char in "0123456789abcdef" for char in value) else None


def _time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None


def _sequence(value: Any) -> tuple[Any, ...] | None:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        return None
    return tuple(value)


def _digest(value: Mapping[str, Any]) -> str:
    try:
        return contracts.canonical_sha256(value)
    except (TypeError, ValueError) as exc:
        raise _Invalid("REFUSE_NONCANONICAL_ARTIFACT") from exc


def _terminal_for(validation: contracts.ContractValidation[Any]) -> tuple[str, str]:
    terminal = validation.disposition if validation.disposition in contracts.TERMINALS else "REFUSE"
    return terminal, validation.reason_code


def _output(
    terminal: str,
    reason: str,
    detail: str,
    *,
    attempt: Mapping[str, Any] | None = None,
    selection: str | None = None,
    gate_sha: str | None = None,
    continuation: Mapping[str, Any] | None = None,
    state: Mapping[str, Any] | None = None,
    external_action_execution: str = "not_claimed",
) -> dict[str, Any]:
    outcomes = {
        "VERIFIED_DONE": "SETTLED", "HOLD": "HOLD", "REFUSE": "REFUSE",
        "EXHAUSTED": "EXPIRED", "PROPOSED_FOR_OWNER": "HOLD",
    }
    return {
        "schema": REMEDIATION_RESULT_SCHEMA,
        "terminal": terminal,
        "state_outcome": outcomes[terminal],
        "reason_code": reason,
        "detail": detail,
        "claim_ceiling": CLAIM_CEILING,
        "issue_scope": ISSUE_SCOPE,
        "attempt_id": None if attempt is None else attempt["attempt_id"],
        "attempt": None if attempt is None else dict(attempt),
        "selection_sha256": selection,
        "gate_sha256s": [] if gate_sha is None else [gate_sha],
        "continuation": None if continuation is None else dict(continuation),
        "external_action_execution": external_action_execution,
        "state_verification": dict(state or {}),
    }


def _action_from_raw(raw: Any) -> contracts.RepairAction | None:
    raw = _map(raw, _ACTION)
    if raw is None or raw["schema"] != contracts.REPAIR_ACTION_SCHEMA:
        return None
    identifiers = ("action_id", "issue_id", "candidate_id", "promotion_rule_id", "action_type")
    values = {name: _text(raw[name]) for name in identifiers}
    digests = {name: _sha(raw[name]) for name in ("candidate_sha256", "run_policy_sha256")}
    parent_sha = raw["parent_gate_run_sha256"]
    scopes = _sequence(raw["scope_paths"])
    if (
        any(value is None for value in values.values())
        or any(value is None for value in digests.values())
        or (parent_sha is not None and _sha(parent_sha) is None)
        or scopes is None
        or not all(_text(path) for path in scopes)
        or isinstance(raw["round_index"], bool)
        or not isinstance(raw["round_index"], int)
        or raw["round_index"] < 0
        or isinstance(raw["diff_bound"], bool)
        or not isinstance(raw["diff_bound"], int)
        or raw["diff_bound"] < 0
    ):
        return None
    return contracts.RepairAction(
        contracts.REPAIR_ACTION_SCHEMA,
        values["action_id"], values["issue_id"], values["candidate_id"],
        digests["candidate_sha256"], digests["run_policy_sha256"],
        values["promotion_rule_id"], raw["round_index"], parent_sha,
        values["action_type"], tuple(scopes), raw["diff_bound"],
    )


def _validate_classification(
    raw: Any, concern: contracts.ConcernRecord, issue: contracts.Issue
) -> Mapping[str, Any]:
    receipt = _map(raw, _CLASSIFICATION)
    if (
        receipt is None
        or receipt["schema"] != CLASSIFICATION_RECEIPT_SCHEMA
        or receipt["issue_id"] != issue.issue_id
        or receipt["concern_id"] != concern.concern_id
        or receipt["gate_id"] != issue.classification_gate.gate_id
        or receipt["gate_definition_sha256"] != issue.classification_gate.definition_sha256
        or receipt["disposition"] != issue.disposition
        or receipt["reason_code"] != issue.reason_code
        or _time(receipt["captured_at"]) is None
        or _digest(receipt) != issue.classification_receipt_sha256
    ):
        raise _Invalid("REFUSE_CLASSIFICATION_RECEIPT_BINDING_MISMATCH")
    return receipt


def _validate_binding_evidence(
    raw: Any, binding: contracts.ProducerBinding, candidate: contracts.RepairCandidate
) -> tuple[Mapping[str, Any], ...]:
    evidence = _sequence(raw)
    if evidence is None or len(evidence) != len(binding.binding_history):
        raise _Invalid("PRODUCER_BINDING_EVIDENCE_INVALID")
    checked: list[Mapping[str, Any]] = []
    for index, item in enumerate(evidence):
        item = _map(item, _BINDING_EVIDENCE)
        if (
            item is None
            or item["schema"] != PRODUCER_BINDING_EVIDENCE_SCHEMA
            or item["binding_id"] != binding.binding_id
            or item["producer_id"] != binding.producer_id
            or item["issue_id"] != binding.issue_id
            or item["candidate_id"] != candidate.candidate_id
            or item["binding_state"] != binding.binding_history[index]
            or _time(item["captured_at"]) is None
            or _digest(item) != binding.binding_evidence_sha256s[index]
        ):
            raise _Invalid("REFUSE_PRODUCER_BINDING_EVIDENCE_MISMATCH")
        checked.append(item)
    if binding.binding_state != "receipt_verified" or (
        binding.producer_receipt_sha256 != binding.binding_evidence_sha256s[-1]
    ):
        raise _Invalid("HOLD_RECEIPT_NOT_VERIFIED")
    return tuple(checked)


def _validate_parent(
    raw: Any,
    *,
    connection,
    policy: contracts.RunPolicy,
    issue: contracts.Issue,
    current_run_id: str,
    current_fingerprint: str,
    current_frontier: tuple[str, ...],
) -> tuple[int, str | None, contracts.GateRun | None, tuple[str, ...]]:
    if raw is None:
        return 0, None, None, ()
    parent = _map(raw, _PARENT)
    action = None if parent is None else _action_from_raw(parent["action"])
    attempt_id = None if parent is None else _text(parent["attempt_id"])
    excluded = None if parent is None else _sha(parent["excluded_repair_action_fingerprint"])
    if (
        parent is None
        or action is None
        or attempt_id is None
        or excluded is None
        or parent["issue_id"] != issue.issue_id
        or action.issue_id != issue.issue_id
        or action.run_policy_sha256 != policy.sha256
        or (
            policy.iteration_bound is not None
            and action.round_index + 1 >= policy.iteration_bound
        )
    ):
        raise _Invalid("REFUSE_PARENT_ROUND_BINDING_MISMATCH")
    parent_gate_result = contracts.validate_gate_run(parent["gate_run"], policy, action)
    if not parent_gate_result.is_validated or parent_gate_result.value is None:
        _, reason = _terminal_for(parent_gate_result)
        raise _Invalid(reason)
    parent_gate = parent_gate_result.value
    if parent_gate.aggregate_result != "FAIL" or current_fingerprint == excluded:
        raise _Invalid("REFUSE_PARENT_ROUND_BINDING_MISMATCH")
    try:
        verified = verify_wave_attempt(connection, attempt_id)
    except Exception as exc:  # State verifier gives no typed public exception hierarchy.
        raise _Invalid("REFUSE_PARENT_ATTEMPT_UNVERIFIED") from exc
    settlement = verified.get("settlement")
    if not isinstance(settlement, Mapping) or settlement.get("outcome") != "HOLD":
        raise _Invalid("REFUSE_PARENT_ATTEMPT_UNVERIFIED")
    gate_artifact_sha = _sha(settlement.get("gate_artifact_sha256"))
    if gate_artifact_sha is None:
        raise _Invalid("REFUSE_PARENT_GATE_ARTIFACT_MISMATCH")
    artifact = connection.execute(
        "SELECT artifact_kind, content_json, claim_ceiling "
        "FROM cb_light_wave_artifact WHERE artifact_sha256 = ?",
        (gate_artifact_sha,),
    ).fetchone()
    expected_gate_json = contracts.canonical_bytes(parent_gate.as_dict()).decode("utf-8")
    if (
        artifact is None
        or artifact["artifact_kind"] != "premortem_remediation_gate"
        or artifact["claim_ceiling"] != CLAIM_CEILING
        or artifact["content_json"] != expected_gate_json
    ):
        raise _Invalid("REFUSE_PARENT_GATE_ARTIFACT_MISMATCH")
    parent_attempt = verified.get("attempt")
    input_artifact_sha = (
        _sha(parent_attempt.get("input_artifact_sha256"))
        if isinstance(parent_attempt, Mapping)
        else None
    )
    if input_artifact_sha is None:
        raise _Invalid("REFUSE_PARENT_INPUT_ARTIFACT_MISMATCH")
    input_artifact = connection.execute(
        "SELECT artifact_kind, content_json, claim_ceiling "
        "FROM cb_light_wave_artifact WHERE artifact_sha256 = ?",
        (input_artifact_sha,),
    ).fetchone()
    try:
        payload = json.loads(input_artifact["content_json"]) if input_artifact is not None else None
    except (TypeError, ValueError):
        payload = None
    if (
        input_artifact is None
        or input_artifact["artifact_kind"] != "premortem_remediation_input"
        or input_artifact["claim_ceiling"] != CLAIM_CEILING
        or not isinstance(payload, Mapping)
        or set(payload) != _INPUT_ARTIFACT
        or payload["attempt_id"] != attempt_id
        or _sha(payload["request_sha256"]) is None
        or not isinstance(payload["round"], int)
        or isinstance(payload["round"], bool)
        or payload["round"] != action.round_index
        or _sha(payload["fingerprint"]) is None
        or _sha(payload["action_application_sha256"]) is None
        or _sha(payload["execution_receipt_sha256"]) is None
        or _sha(payload["gate_sha256"]) is None
    ):
        raise _Invalid("REFUSE_PARENT_INPUT_ARTIFACT_MISMATCH")
    parent_frontier = _sequence(payload["frontier"])
    if (
        not isinstance(payload["run_id"], str)
        or parent_frontier is None
        or not parent_frontier
        or any(_sha(value) is None for value in parent_frontier)
        or len(set(parent_frontier)) != len(parent_frontier)
        or payload["fingerprint"] != excluded
        or parent_frontier[0] != excluded
        or parent_gate.measure_value != len(parent_frontier) - 1
    ):
        raise _Invalid("REFUSE_PARENT_INPUT_ARTIFACT_MISMATCH")
    if payload["run_id"] != current_run_id:
        raise _Invalid("REFUSE_PARENT_RUN_LINEAGE_MISMATCH")
    if current_frontier != parent_frontier[1:]:
        raise _Invalid("REFUSE_CONTINUATION_FRONTIER_SUBTRACTION_MISMATCH")
    return action.round_index + 1, attempt_id, parent_gate, (excluded,)


def _validate_round(raw: Any, connection) -> _Round:
    request = _map(raw, _REQUEST)
    if (
        request is None
        or request["schema"] != REMEDIATION_REQUEST_SCHEMA
        or _text(request["run_id"]) is None
        or _time(request["captured_at"]) is None
    ):
        raise _Invalid("REMEDIATION_REQUEST_INVALID")
    policy_result = contracts.validate_run_policy(request["run_policy"])
    if not policy_result.is_validated or policy_result.value is None:
        terminal, reason = _terminal_for(policy_result)
        raise _Invalid(f"{terminal}:{reason}")
    policy = policy_result.value
    if (
        policy.progress_measure.measure_id != REMAINING_CANDIDATE_FRONTIER_MEASURE
        or policy.progress_measure.measure_domain != "natural_nonnegative_integer"
        or policy.progress_measure.terminal_value != 0
    ):
        raise _Invalid("HOLD_UNSUPPORTED_PROGRESS_MEASURE")
    validations = (
        contracts.validate_concern_record(request["concern"]),
        contracts.validate_issue(request["issue"]),
        contracts.validate_producer_binding(request["producer_binding"]),
        contracts.validate_repair_candidate(request["repair_candidate"], policy),
    )
    if any(not result.is_validated or result.value is None for result in validations):
        invalid = next(result for result in validations if not result.is_validated or result.value is None)
        terminal, reason = _terminal_for(invalid)
        raise _Invalid(f"{terminal}:{reason}")
    concern, issue, binding, candidate = (result.value for result in validations)
    assert concern is not None and issue is not None and binding is not None and candidate is not None
    if issue.concern_id != concern.concern_id or binding.issue_id != issue.issue_id or binding.producer_id != candidate.producer_id or candidate.issue_id != issue.issue_id:
        raise _Invalid("REFUSE_RECEIPT_CHAIN_SEVERED")
    classification = _validate_classification(request["classification_receipt"], concern, issue)
    evidence = _validate_binding_evidence(request["binding_evidence"], binding, candidate)
    fingerprint = contracts.repair_action_fingerprint(candidate)
    frontier = _sequence(request["candidate_frontier"])
    if (
        frontier is None
        or not frontier
        or any(_sha(value) is None for value in frontier)
        or len(set(frontier)) != len(frontier)
        or frontier[0] != fingerprint
    ):
        raise _Invalid("HOLD_FRONTIER_SELECTION_MISMATCH")
    round_index, parent_attempt_id, parent_gate, excluded = _validate_parent(
        request["parent"], connection=connection, policy=policy, issue=issue,
        current_run_id=request["run_id"], current_fingerprint=fingerprint,
        current_frontier=tuple(frontier),
    )
    admitted = contracts.admit_repair_candidate(
        candidate, binding, issue, policy, round_index=round_index,
        excluded_repair_action_fingerprints=excluded, parent_gate_run=parent_gate,
    )
    if not admitted.is_validated or admitted.value is None:
        terminal, reason = _terminal_for(admitted)
        raise _Invalid(f"{terminal}:{reason}")
    return _Round(
        request, policy, concern, issue, classification, binding, evidence, candidate, fingerprint,
        tuple(frontier), admitted.value, parent_attempt_id, parent_gate,
    )


def _validate_external_receipt(
    wrapper: Any, round_: _Round, application: contracts.ActionApplication
) -> Mapping[str, Any]:
    if not isinstance(wrapper, Mapping) or set(wrapper) != {"execution_receipt_sha256", "receipt"}:
        raise _Invalid("EXTERNAL_ACTION_RECEIPT_INVALID")
    receipt = _map(wrapper["receipt"], _EXTERNAL_RECEIPT)
    digest = _sha(wrapper["execution_receipt_sha256"])
    if receipt is None or digest is None or _digest(receipt) != digest:
        raise _Invalid("REFUSE_EXECUTION_RECEIPT_HASH_MISMATCH")
    if application.execution_receipt_sha256 != digest:
        raise _Invalid("REFUSE_ACTION_APPLICATION_RECEIPT_HASH_MISMATCH")
    action, candidate, policy = round_.action, round_.candidate, round_.policy
    if (
        receipt["schema"] != EXTERNAL_ACTION_RECEIPT_SCHEMA
        or receipt["executor_asset_id"] != application.executor_asset_id
        or receipt["action_type"] != CONTROL_PLANE_PROFILE_REPAIR_ACTION
        or receipt["action_id"] != action.action_id
        or receipt["action_sha256"] != action.sha256
        or receipt["candidate_id"] != candidate.candidate_id
        or receipt["candidate_sha256"] != candidate.sha256
        or receipt["run_policy_sha256"] != policy.sha256
        or receipt["target_sha256"] != candidate.proposed_action.target_sha256
        or receipt["input_state_sha256"] != application.input_state_sha256
        or receipt["output_state_sha256"] != application.output_state_sha256
        or receipt["executed_at"] != application.applied_at
        or _time(receipt["executed_at"]) is None
        or _text(receipt["execution_claim_ceiling"]) is None
    ):
        raise _Invalid("REFUSE_EXTERNAL_ACTION_RECEIPT_BINDING_MISMATCH")
    return receipt


def _record_bindings(connection, round_: _Round, attempt_id: str, states: Sequence[str]) -> list[str]:
    asset = record_artifact(
        connection,
        artifact_kind="premortem_external_producer_asset",
        payload={"producer_id": round_.candidate.producer_id, "producer_type": round_.candidate.producer_type, "execution": "not_invoked_by_controller"},
        claim_ceiling=CLAIM_CEILING,
    )
    evidence = [
        record_artifact(connection, artifact_kind="premortem_producer_binding_evidence", payload=item, claim_ceiling=CLAIM_CEILING)
        for item in round_.evidence
    ]
    ids: list[str] = []
    for state in states:
        index = contracts.BINDING_STATES.index(state)
        ids.append(record_asset_binding(
            connection, attempt_id=attempt_id, council_id=round_.policy.run_policy_id,
            member_id=round_.issue.issue_id,
            asset_id=f"{round_.candidate.producer_type}:{round_.candidate.producer_id}",
            purpose="receipt_bound_external_producer_input", binding_state=state,
            fixture_mode=False, asset_artifact_sha256=asset, claim_ceiling=CLAIM_CEILING,
            reference_artifact_sha256=evidence[1] if index >= 1 else None,
            invocation_artifact_sha256=evidence[2] if index >= 2 else None,
            receipt_artifact_sha256=evidence[3] if index >= 3 else None,
        ))
    return ids


def _attempt_identity(round_: _Round) -> str:
    """Keep a root run/round identity stable even when its contents change."""

    return contracts.canonical_sha256({
        "run_id": round_.request["run_id"],
        "round": round_.action.round_index,
        "policy": round_.policy.sha256,
        "issue": round_.issue.issue_id,
    })


def _attempt_id(round_: _Round) -> str:
    return f"premortem-{_attempt_identity(round_)[:32]}"


def _plan_fingerprint(
    round_: _Round,
    application: contracts.ActionApplication | None = None,
    external_receipt: Mapping[str, Any] | None = None,
    gate: contracts.GateRun | None = None,
) -> str:
    """Use a custody identity for a fully supplied external execution tuple."""

    if application is not None and external_receipt is not None and gate is not None:
        return contracts.canonical_sha256({
            "policy_sha256": round_.policy.sha256,
            "issue_id": round_.issue.issue_id,
            "round_index": round_.action.round_index,
            "action_sha256": round_.action.sha256,
            "action_application_sha256": application.sha256,
            "application_receipt_sha256": application.execution_receipt_sha256,
            "execution_receipt_sha256": _digest(external_receipt),
            "gate_sha256": gate.sha256,
        })
    return contracts.canonical_sha256({"identity": _attempt_identity(round_), "fingerprint": round_.fingerprint})


def _assert_external_custody_unused(
    connection,
    round_: _Round,
    application: contracts.ActionApplication,
    external_receipt: Mapping[str, Any],
    gate: contracts.GateRun,
) -> None:
    """Refuse a custody component already retained by another attempt."""

    initialize_wave_state(connection)
    attempt_id = _attempt_id(round_)
    plan = _plan_fingerprint(round_, application, external_receipt, gate)
    plans = connection.execute(
        "SELECT attempt_id FROM cb_light_wave_attempt WHERE plan_fingerprint = ?", (plan,)
    ).fetchall()
    if any(row["attempt_id"] != attempt_id for row in plans):
        raise _Invalid("REFUSE_EXECUTION_RECEIPT_REUSED")
    if plans:
        return
    gate_artifact_sha = artifact_sha256_for(
        artifact_kind="premortem_remediation_gate", payload=gate.as_dict(), claim_ceiling=CLAIM_CEILING
    )
    settlements = connection.execute(
        "SELECT attempt_id FROM cb_light_wave_settlement WHERE gate_artifact_sha256 = ?",
        (gate_artifact_sha,),
    ).fetchall()
    if any(row["attempt_id"] != attempt_id for row in settlements):
        raise _Invalid("REFUSE_EXECUTION_RECEIPT_REUSED")
    for kind, payload in (
        ("premortem_external_action_application", application.as_dict()),
        ("premortem_external_action_receipt", external_receipt),
        ("premortem_remediation_gate", gate.as_dict()),
    ):
        existing = connection.execute(
            "SELECT artifact_sha256 FROM cb_light_wave_artifact "
            "WHERE artifact_kind = ? AND content_json = ? AND claim_ceiling = ?",
            (kind, contracts.canonical_bytes(payload).decode("utf-8"), CLAIM_CEILING),
        ).fetchone()
        if existing is not None:
            raise _Invalid("REFUSE_EXECUTION_RECEIPT_REUSED")


def _persist(
    connection,
    round_: _Round,
    *,
    terminal: str,
    reason: str,
    states: Sequence[str],
    application: contracts.ActionApplication | None = None,
    external_receipt: Mapping[str, Any] | None = None,
    gate: contracts.GateRun | None = None,
) -> tuple[dict[str, Any], Mapping[str, Any]]:
    source_sha = sha256(Path(__file__).read_bytes()).hexdigest()
    attempt_id = _attempt_id(round_)
    plan = _plan_fingerprint(round_, application, external_receipt, gate)
    topology = record_artifact(
        connection, artifact_kind="premortem_remediation_closed_topology",
        payload={"source_sha256": source_sha, "actions": [CONTROL_PLANE_PROFILE_REPAIR_ACTION], "issue_scope": ISSUE_SCOPE, "external_execution": "receipt_only"},
        claim_ceiling=CLAIM_CEILING,
    )
    input_artifact = record_artifact(
        connection, artifact_kind="premortem_remediation_input",
        payload={
            "attempt_id": attempt_id, "request_sha256": _digest(round_.request),
            "run_id": round_.request["run_id"], "round": round_.action.round_index,
            "fingerprint": round_.fingerprint, "frontier": list(round_.frontier),
            "action_application_sha256": None if application is None else application.sha256,
            "execution_receipt_sha256": None if external_receipt is None else _digest(external_receipt),
            "gate_sha256": None if gate is None else gate.sha256,
        },
        claim_ceiling=CLAIM_CEILING,
    )
    attempt_id = record_wave_attempt(
        connection, attempt_id=attempt_id, parent_attempt_id=round_.parent_attempt_id,
        plan_fingerprint=plan, topology_artifact_sha256=topology,
        input_artifact_sha256=input_artifact, fixture_mode=False, claim_ceiling=CLAIM_CEILING,
    )
    for kind, payload in (
        ("premortem_concern", round_.concern.as_dict()), ("premortem_issue", round_.issue.as_dict()),
        ("premortem_classification_receipt", round_.classification),
        ("premortem_producer_binding", round_.binding.as_dict()), ("premortem_candidate", round_.candidate.as_dict()),
        ("premortem_action", round_.action.as_dict()),
    ):
        record_artifact(connection, artifact_kind=kind, payload=payload, claim_ceiling=CLAIM_CEILING)
    binding_ids = _record_bindings(connection, round_, attempt_id, states)
    if application is not None:
        record_artifact(connection, artifact_kind="premortem_external_action_application", payload=application.as_dict(), claim_ceiling=CLAIM_CEILING)
    if external_receipt is not None:
        record_artifact(connection, artifact_kind="premortem_external_action_receipt", payload=external_receipt, claim_ceiling=CLAIM_CEILING)
    gate_payload = gate.as_dict() if gate is not None else {"terminal": terminal, "reason": reason}
    gate_artifact = record_artifact(connection, artifact_kind="premortem_remediation_gate", payload=gate_payload, claim_ceiling=CLAIM_CEILING)
    outcome = {"VERIFIED_DONE": "SETTLED", "HOLD": "HOLD", "REFUSE": "REFUSE", "EXHAUSTED": "EXPIRED", "PROPOSED_FOR_OWNER": "HOLD"}[terminal]
    receipt_artifact = record_artifact(
        connection, artifact_kind="premortem_remediation_receipt",
        payload={"attempt_id": attempt_id, "terminal": terminal, "reason": reason, "issue_scope": ISSUE_SCOPE, "binding_ids": sorted(binding_ids)},
        claim_ceiling=CLAIM_CEILING,
    )
    settlement_id = record_wave_settlement(
        connection, attempt_id=attempt_id, outcome=outcome, reason_code=reason,
        gate_artifact_sha256=gate_artifact, receipt_artifact_sha256=receipt_artifact,
        claim_ceiling=CLAIM_CEILING,
    )
    verified = verify_wave_attempt(connection, attempt_id)
    settlement = verified.get("settlement")
    if not isinstance(settlement, Mapping) or settlement.get("settlement_id") != settlement_id:
        raise RuntimeError("remediation settlement failed retained-state verification")
    return {
        "attempt_id": attempt_id, "parent_attempt_id": round_.parent_attempt_id,
        "round_index": round_.action.round_index, "fixture_mode": False,
        "binding_states": list(states), "binding_ids": sorted(binding_ids),
        "settlement_id": settlement_id, "reason_code": reason, "state_outcome": outcome,
        "frontier_before": len(round_.frontier),
        "frontier_after": None if gate is None else gate.measure_value,
    }, verified


def _persist_output(
    connection, round_: _Round, terminal: str, reason: str, detail: str,
    *, states: Sequence[str], application: contracts.ActionApplication | None = None,
    receipt: Mapping[str, Any] | None = None, gate: contracts.GateRun | None = None,
    continuation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    attempt, verified = _persist(
        connection, round_, terminal=terminal, reason=reason, states=states,
        application=application, external_receipt=receipt, gate=gate,
    )
    return _output(
        terminal, reason, detail, attempt=attempt,
        selection=round_.fingerprint, gate_sha=None if gate is None else gate.sha256,
        continuation=continuation,
        external_action_execution="receipt_bound_external_action_only" if application and receipt else "not_claimed",
        state={
            "retained_state_integrity_verified": True,
            "binding_count": len(verified["bindings"]),
            "independent_external_execution_proof": "not_claimed",
            "time_bound_scope": (
                "not_declared" if round_.policy.time_bound_seconds is None
                else "refused_without_prepared_run_start"
            ),
        },
    )


def _failure(text: str) -> dict[str, Any]:
    if ":" in text:
        terminal, reason = text.split(":", 1)
        if terminal in contracts.TERMINALS:
            return _output(terminal, reason, "Strict remediation preflight did not authorize a state transition.")
    return _output("HOLD" if text.startswith("HOLD_") else "REFUSE", text, "Strict remediation input validation failed.")


def run_remediation(raw: Any, *, db_path: Path | None = None) -> dict[str, Any]:
    """Run exactly one externally performed repair round, or refuse/hold it."""

    connection = connect(db_path)
    try:
        try:
            round_ = _validate_round(raw, connection)
        except _Invalid as exc:
            return _failure(str(exc))
        with append_only_transaction(connection):
            if round_.issue.disposition in {"OUT_OF_SCOPE", "EVIDENCE_INSUFFICIENT"}:
                return _persist_output(
                    connection, round_, "PROPOSED_FOR_OWNER", "ISSUE_REQUIRES_OWNER_RULING",
                    "The deterministic issue is outside automatic repair authority.",
                    states=("declared", "bound_reference"),
                )
            if round_.issue.disposition != "OPEN":
                return _persist_output(
                    connection, round_, "HOLD", "ISSUE_NOT_OPEN",
                    "Only an OPEN issue can enter the contained external-action route.",
                    states=("declared", "bound_reference"),
                )
            if round_.action.action_type != CONTROL_PLANE_PROFILE_REPAIR_ACTION:
                return _persist_output(
                    connection, round_, "PROPOSED_FOR_OWNER", "ACTION_NOT_IN_CLOSED_REGISTRY",
                    "The proposed action is not the one contained external-profile repair route.",
                    states=("declared", "bound_reference"),
                )
            if round_.policy.time_bound_seconds is not None:
                return _persist_output(
                    connection, round_, "HOLD", "HOLD_TIME_BOUND_REQUIRES_PREPARED_ATTEMPT",
                    "This first receipt-only slice has no immutable prepared run-start to enforce "
                    "a declared wall-clock bound, so it will not accept an action receipt under one.",
                    states=("declared", "bound_reference"),
                )
            if round_.request["action_application"] is None:
                return _persist_output(
                    connection, round_, "HOLD", "HOLD_EXTERNAL_ACTION_APPLICATION_REQUIRED",
                    "CB Light will not execute the repair; it requires an exact external application receipt.",
                    states=("declared", "bound_reference"),
                )
            application_result = contracts.validate_action_application(round_.request["action_application"], round_.action)
            if not application_result.is_validated or application_result.value is None:
                _, reason = _terminal_for(application_result)
                return _persist_output(connection, round_, "REFUSE", reason, "The application does not bind the admitted action.", states=("declared", "bound_reference"))
            application = application_result.value
            try:
                receipt = _validate_external_receipt(round_.request["execution_receipt"], round_, application)
            except _Invalid as exc:
                return _persist_output(connection, round_, "REFUSE", str(exc), "The external receipt is absent, altered, or severed.", states=("declared", "bound_reference"))
            gate_result = contracts.validate_gate_run(round_.request["gate_run"], round_.policy, round_.action)
            if not gate_result.is_validated or gate_result.value is None:
                _, reason = _terminal_for(gate_result)
                return _persist_output(connection, round_, "REFUSE", reason, "The declared completion gate receipt is not bound to this action.", states=("declared", "bound_reference"))
            gate = gate_result.value
            if (
                _time(gate.executed_at) is None or _time(application.applied_at) is None
                or _time(gate.executed_at) <= _time(application.applied_at)
                or gate.input_state_sha256 != application.output_state_sha256
                or gate.current_state_sha256 != application.output_state_sha256
            ):
                return _persist_output(connection, round_, "REFUSE", "REFUSE_GATE_APPLICATION_SEVERED", "The gate is not a fresh recheck of the application output.", states=("declared", "bound_reference"))
            if round_.parent_gate is not None and gate.measure_value >= round_.parent_gate.measure_value:
                return _persist_output(connection, round_, "HOLD", "NONDECREASING_RETRY_MEASURE", "A later round must strictly reduce the parent gate's scalar frontier measure.", states=("declared", "bound_reference"))
            expected_measure = 0 if gate.aggregate_result == "PASS" else len(round_.frontier) - 1
            if gate.measure_value != expected_measure:
                return _persist_output(connection, round_, "REFUSE", "REFUSE_GATE_FRONTIER_MEASURE_MISMATCH", "The gate receipt does not match the declared candidate frontier transition.", states=contracts.BINDING_STATES, application=application, receipt=receipt, gate=gate)
            _assert_external_custody_unused(
                connection, round_, application, receipt, gate
            )
            if gate.aggregate_result == "PASS":
                return _persist_output(
                    connection, round_, "HOLD",
                    "HOLD_RECEIPT_VALIDATED_AWAITING_TRUSTED_GATE",
                    "The supplied external action and PASS gate receipts are structurally bound, but "
                    "this controller did not invoke a trusted deterministic gate; it cannot declare "
                    "the issue done.",
                    states=contracts.BINDING_STATES,
                    application=application,
                    receipt=receipt,
                    gate=gate,
                )
            if (
                round_.policy.iteration_bound is not None
                and round_.action.round_index + 1 >= round_.policy.iteration_bound
            ):
                return _persist_output(connection, round_, "EXHAUSTED", "ITERATION_BOUND_REACHED", "The declared round bound ended after a failed fresh gate; this is not success.", states=contracts.BINDING_STATES, application=application, receipt=receipt, gate=gate)
            if len(round_.frontier) == 1:
                return _persist_output(
                    connection, round_, "EXHAUSTED", "CANDIDATE_FRONTIER_EXHAUSTED",
                    "The declared candidate frontier reached its terminal value after a failed "
                    "fresh gate, so no next candidate is admissible; this is not success.",
                    states=contracts.BINDING_STATES,
                    application=application,
                    receipt=receipt,
                    gate=gate,
                )
            continuation = {
                "attempt_id": _attempt_id(round_),
                "issue_id": round_.issue.issue_id, "action": round_.action.as_dict(),
                "gate_run": gate.as_dict(), "excluded_repair_action_fingerprint": round_.fingerprint,
            }
            return _persist_output(connection, round_, "HOLD", "AWAITING_NEXT_RECEIPT_VERIFIED_CANDIDATE", "The fresh gate failed; an external nested wave may submit one stricter parent-linked next round.", states=contracts.BINDING_STATES, application=application, receipt=receipt, gate=gate, continuation=continuation)
    except _Invalid as exc:
        return _failure(str(exc))
    except StateError:
        return _output(
            "REFUSE", "REFUSE_ROUND_IDENTITY_REUSED",
            "An existing immutable run/round identity has different content or state.",
        )
    finally:
        connection.close()
