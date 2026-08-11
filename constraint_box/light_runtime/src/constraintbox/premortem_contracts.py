"""Lean, pure CB Light contracts for premortem remediation.

This module only validates immutable records and derives stable identities. It
does not execute gates, skills, models, MMMs, providers, commands, a database,
or a UI.  A later controller owns append-only persistence and execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import re
from typing import Any, Generic, Literal, Mapping, Sequence, TypeVar

from hookkernel.cb_light_domain import canonical_json as canonical_json_bytes


CONCERN_RECORD_SCHEMA = "constraintbox.premortem-concern-record.v1"
ISSUE_SCHEMA = "constraintbox.premortem-issue.v1"
ISSUE_EVENT_SCHEMA = "constraintbox.premortem-issue-event.v1"
RESOLUTION_EVENT_SCHEMA = "constraintbox.premortem-resolution-event.v1"
PRODUCER_BINDING_SCHEMA = "constraintbox.premortem-producer-binding.v1"
REPAIR_CANDIDATE_SCHEMA = "constraintbox.premortem-repair-candidate.v1"
REPAIR_ACTION_SCHEMA = "constraintbox.premortem-repair-action.v1"
REPAIR_ACTION_FINGERPRINT_SCHEMA = "constraintbox.premortem-repair-action-fingerprint.v1"
ACTION_APPLICATION_SCHEMA = "constraintbox.premortem-action-application.v1"
GATE_RUN_SCHEMA = "constraintbox.premortem-gate-run.v1"
CANDIDATE_EXCLUSION_SCHEMA = "constraintbox.premortem-candidate-exclusion.v1"
RECEIPT_SCHEMA = "constraintbox.premortem-receipt.v1"
RUN_POLICY_SCHEMA = "constraintbox.premortem-run-policy.v1"
CONTRACT_VALIDATION_SCHEMA = "constraintbox.premortem-contract-validation.v1"

CLAIM_CEILING = (
    "Typed CB Light contract records only; no execution, controller, database, "
    "settlement, completion, provider, UI, CB Heavy, or simulation claim."
)
BINDING_STATES = ("declared", "bound_reference", "invoked", "receipt_verified")
PRODUCER_TYPES = ("skill", "mmm", "formal_agent", "model_provider")
ISSUE_DISPOSITIONS = (
    "OPEN",
    "RESOLVED",
    "DUPLICATE",
    "OUT_OF_SCOPE",
    "EVIDENCE_INSUFFICIENT",
)
TERMINALS = ("VERIFIED_DONE", "HOLD", "REFUSE", "EXHAUSTED", "PROPOSED_FOR_OWNER")
DETERMINISTIC_EXECUTOR_KINDS = ("deterministic_callable", "deterministic_command")
MEASURE_DOMAINS = ("natural_nonnegative_integer",)

_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{2,95}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$")
_ALLOWED_OUTPUTS = frozenset({"structured_json", "typed_receipt"})
_AUTHORITY_KEYS = frozenset(
    {
        "vote", "verdict", "confidence", "consensus", "disposition", "decision",
        "status", "result", "terminal", "settlement", "promotion",
        "completion", "authority", "model", "provider", "selection", "ranking",
        "score", "grade", "rank", "approve", "veto", "trust", "certainty",
    }
)

Disposition = Literal["VALIDATED", "HOLD", "REFUSE", "PROPOSED_FOR_OWNER"]
T = TypeVar("T")


@dataclass(frozen=True)
class ContractValidation(Generic[T]):
    schema: str
    disposition: Disposition
    reason_code: str
    detail: str
    value: T | None = None
    claim_ceiling: str = CLAIM_CEILING

    @property
    def is_validated(self) -> bool:
        return self.disposition == "VALIDATED" and self.value is not None


class _Record:
    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def sha256(self) -> str:
        return canonical_sha256(self)


@dataclass(frozen=True)
class GateDeclaration(_Record):
    gate_id: str
    executor_kind: Literal["deterministic_callable", "deterministic_command"]
    executable_ref: str
    definition_sha256: str


@dataclass(frozen=True)
class ProgressMeasure(_Record):
    measure_id: str
    measure_domain: Literal["natural_nonnegative_integer"]
    terminal_value: int
    strict_per_retry_decrease: Literal[True]


@dataclass(frozen=True)
class RunPolicy(_Record):
    schema: str
    run_policy_id: str
    completion_gate: GateDeclaration
    required_regression_gates: tuple[GateDeclaration, ...]
    scope_paths: tuple[str, ...]
    diff_bound: int
    promotion_rule_id: str
    iteration_bound: int | None
    time_bound_seconds: int | None
    progress_measure: ProgressMeasure
    output_surfaces: tuple[str, ...]
    claim_ceiling: str


@dataclass(frozen=True)
class ConcernRecord(_Record):
    schema: str
    concern_id: str
    source: str
    locator: str
    description: str
    discovered_at: str
    source_sha256: str


@dataclass(frozen=True)
class Issue(_Record):
    schema: str
    issue_id: str
    concern_id: str
    classification_gate: GateDeclaration
    disposition: Literal[
        "OPEN", "RESOLVED", "DUPLICATE", "OUT_OF_SCOPE", "EVIDENCE_INSUFFICIENT"
    ]
    reason_code: str
    classification_receipt_sha256: str


@dataclass(frozen=True)
class ProducerBinding(_Record):
    """Append-only evidence ladder for the (producer_id, issue_id) pair."""

    schema: str
    binding_id: str
    producer_id: str
    issue_id: str
    binding_history: tuple[Literal["declared", "bound_reference", "invoked", "receipt_verified"], ...]
    binding_state: Literal["declared", "bound_reference", "invoked", "receipt_verified"]
    binding_evidence_sha256s: tuple[str, ...]
    producer_receipt_sha256: str | None
    updated_at: str


@dataclass(frozen=True)
class ProposedAction(_Record):
    action_type: str
    scope_paths: tuple[str, ...]
    diff_bound: int
    evidence_effect: Literal["non_evidence_increasing", "evidence_increasing"]
    target_sha256: str


@dataclass(frozen=True)
class RepairCandidate(_Record):
    """Producer output only; binding and authority are deliberately absent."""

    schema: str
    candidate_id: str
    issue_id: str
    producer_type: Literal["skill", "mmm", "formal_agent", "model_provider"]
    producer_id: str
    proposed_action: ProposedAction
    evidence_refs: tuple[str, ...]
    produced_at: str


@dataclass(frozen=True)
class RepairAction(_Record):
    """A pending deterministic promotion; application is a later event."""

    schema: str
    action_id: str
    issue_id: str
    candidate_id: str
    candidate_sha256: str
    run_policy_sha256: str
    promotion_rule_id: str
    round_index: int
    parent_gate_run_sha256: str | None
    action_type: str
    scope_paths: tuple[str, ...]
    diff_bound: int


@dataclass(frozen=True)
class ActionApplication(_Record):
    """Content-addressed completed application; never a terminal or GateRun."""

    schema: str
    application_id: str
    action_id: str
    action_sha256: str
    executor_asset_id: str
    execution_receipt_sha256: str
    input_state_sha256: str
    output_state_sha256: str
    applied_at: str


@dataclass(frozen=True)
class RegressionGateResult(_Record):
    gate_id: str
    definition_sha256: str
    result: Literal["PASS", "FAIL"]


@dataclass(frozen=True)
class GateRun(_Record):
    schema: str
    gate_run_id: str
    action_id: str
    action_sha256: str
    run_policy_sha256: str
    round_index: int
    aggregate_gate_id: str
    aggregate_gate_definition_sha256: str
    aggregate_result: Literal["PASS", "FAIL"]
    required_gate_results: tuple[RegressionGateResult, ...]
    input_state_sha256: str
    current_state_sha256: str
    measure_value: int
    executed_at: str


# These are small custody carriers.  Their append-only storage and terminal
# decision semantics remain controller/state responsibilities.
@dataclass(frozen=True)
class IssueEvent(_Record):
    schema: str
    event_id: str
    issue_id: str
    event_kind: str
    emitted_by_gate_id: str
    input_sha256: str
    output_sha256: str
    emitted_at: str


@dataclass(frozen=True)
class ResolutionEvent(_Record):
    schema: str
    event_id: str
    issue_id: str
    gate_run_id: str
    gate_run_sha256: str
    emitted_by_gate_id: str
    emitted_at: str


@dataclass(frozen=True)
class CandidateExclusion(_Record):
    schema: str
    exclusion_id: str
    issue_id: str
    repair_action_fingerprint: str
    gate_run_sha256: str
    round_index: int
    reason_code: str
    emitted_at: str


@dataclass(frozen=True)
class Receipt(_Record):
    schema: str
    receipt_id: str
    run_id: str
    terminal: Literal["VERIFIED_DONE", "HOLD", "REFUSE", "EXHAUSTED", "PROPOSED_FOR_OWNER"]
    supersedes_receipt_id: str | None
    emitted_by_gate_id: str
    custody_input_sha256: str
    custody_output_sha256: str
    receipt_payload_sha256: str
    emitted_at: str


def canonical_bytes(value: _Record | Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(value.as_dict() if isinstance(value, _Record) else dict(value))


def canonical_sha256(value: _Record | Mapping[str, Any]) -> str:
    return sha256(canonical_bytes(value)).hexdigest()


def _result(
    disposition: Disposition, reason_code: str, detail: str, value: T | None = None
) -> ContractValidation[T]:
    return ContractValidation(CONTRACT_VALIDATION_SCHEMA, disposition, reason_code, detail, value)


def _object(raw: Any, fields: set[str]) -> Mapping[str, Any] | None:
    if not isinstance(raw, Mapping) or not all(isinstance(key, str) for key in raw):
        return None
    return raw if set(raw) == fields else None


def _id(value: Any) -> str | None:
    return value if isinstance(value, str) and _ID.fullmatch(value) else None


def _text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _sha(value: Any) -> str | None:
    return value if isinstance(value, str) and _SHA.fullmatch(value) else None


def _time(value: Any) -> str | None:
    return value if isinstance(value, str) and _UTC.fullmatch(value) else None


def _nat(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _positive_or_none(value: Any) -> int | None | object:
    if value is None:
        return None
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else _BAD


def _seq(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _paths(value: Any) -> tuple[str, ...] | None:
    if not _seq(value) or not value:
        return None
    paths: list[str] = []
    for item in value:
        path = _text(item)
        if path is None or path.startswith("/") or "\\" in path:
            return None
        if any(part in {"", ".", ".."} for part in path.split("/")):
            return None
        paths.append(path)
    return tuple(sorted(set(paths)))


def _strings(value: Any, *, nonempty: bool = False) -> tuple[str, ...] | None:
    if not _seq(value):
        return None
    raw_values = [_text(item) for item in value]
    if any(item is None for item in raw_values):
        return None
    values = tuple(sorted(set(raw_values)))
    return values if values or not nonempty else None  # type: ignore[return-value]


def _gate(raw: Any) -> GateDeclaration | None:
    fields = {"gate_id", "executor_kind", "executable_ref", "definition_sha256"}
    raw = _object(raw, fields)
    if raw is None:
        return None
    gate_id, ref, digest = _id(raw["gate_id"]), _text(raw["executable_ref"]), _sha(raw["definition_sha256"])
    kind = raw["executor_kind"]
    if gate_id is None or ref is None or digest is None or kind not in DETERMINISTIC_EXECUTOR_KINDS:
        return None
    return GateDeclaration(gate_id, kind, ref, digest)


def _gate_list(raw: Any) -> tuple[GateDeclaration, ...] | None:
    if not _seq(raw):
        return None
    gates = [_gate(item) for item in raw]
    if any(gate is None for gate in gates):
        return None
    resolved = tuple(sorted(gates, key=lambda gate: gate.gate_id))  # type: ignore[union-attr]
    return resolved if len({gate.gate_id for gate in resolved}) == len(resolved) else None


def _measure(raw: Any) -> ProgressMeasure | None:
    fields = {"measure_id", "measure_domain", "terminal_value", "strict_per_retry_decrease"}
    raw = _object(raw, fields)
    if raw is None:
        return None
    measure_id, terminal = _id(raw["measure_id"]), _nat(raw["terminal_value"])
    domain = raw["measure_domain"]
    if measure_id is None or terminal is None or domain not in MEASURE_DOMAINS or raw["strict_per_retry_decrease"] is not True:
        return None
    return ProgressMeasure(measure_id, domain, terminal, True)


def _contains_authority(value: Any, prefix: str = "") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                return prefix or "<non-string-key>"
            path = f"{prefix}.{key}" if prefix else key
            if key.lower() in _AUTHORITY_KEYS:
                return path
            if found := _contains_authority(child, path):
                return found
    elif _seq(value):
        for index, child in enumerate(value):
            if found := _contains_authority(child, f"{prefix}[{index}]"):
                return found
    return None


def _nonallowlisted_output_surface(value: Any, prefix: str = "") -> str | None:
    """Find any declared output surface outside the tiny receipt-only allowlist."""

    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                return prefix or "<non-string-key>"
            path = f"{prefix}.{key}" if prefix else key
            if key.lower() in {"output_surface", "output_surfaces"}:
                if not _seq(child):
                    return path
                for surface in child:
                    if not isinstance(surface, str) or surface.strip().lower() not in _ALLOWED_OUTPUTS:
                        return path
            if found := _nonallowlisted_output_surface(child, path):
                return found
    elif _seq(value):
        for index, child in enumerate(value):
            if found := _nonallowlisted_output_surface(child, f"{prefix}[{index}]"):
                return found
    return None


def validate_run_policy(raw: Any) -> ContractValidation[RunPolicy]:
    """Require aggregate gate, explicit regressions, and well-founded stop policy."""

    if isinstance(raw, Mapping):
        if found := _contains_authority(raw):
            return _result(
                "REFUSE", "NONDETERMINISTIC_AUTHORITY",
                f"Policy field {found} cannot carry decision authority.",
            )
        if found := _nonallowlisted_output_surface(raw):
            return _result(
                "REFUSE", "PROHIBITED_OUTPUT_SURFACE",
                f"Policy output surface {found} is not receipt-only.",
            )
    if not isinstance(raw, Mapping):
        return _result("REFUSE", "RUN_POLICY_INVALID", "RunPolicy must be an object.")
    if raw.get("completion_gate") is None:
        return _result("HOLD", "NO_DECLARED_COMPLETION_GATE", "Aggregate completion gate is absent.")
    if "required_regression_gates" not in raw:
        return _result("HOLD", "NO_DECLARED_REGRESSION_AGGREGATE", "Regression gates must be explicit.")
    fields = {
        "schema", "run_policy_id", "completion_gate", "required_regression_gates",
        "scope_paths", "diff_bound", "promotion_rule_id", "iteration_bound",
        "time_bound_seconds", "progress_measure", "output_surfaces", "claim_ceiling",
    }
    raw = _object(raw, fields)
    if raw is None or raw["schema"] != RUN_POLICY_SCHEMA:
        return _result("REFUSE", "RUN_POLICY_INVALID", "RunPolicy fields are not exact.")
    completion, regressions, measure = _gate(raw["completion_gate"]), _gate_list(raw["required_regression_gates"]), _measure(raw["progress_measure"])
    if completion is None:
        return _result("HOLD", "NO_DECLARED_COMPLETION_GATE", "Completion gate is not deterministic and executable.")
    if regressions is None or completion.gate_id in {gate.gate_id for gate in regressions}:
        return _result("HOLD", "NO_DECLARED_REGRESSION_AGGREGATE", "Regression aggregate is not declared.")
    if measure is None:
        return _result("HOLD", "NO_DECLARED_STOP_CRITERION", "Measure domain, terminal value, and strict decrease are required.")
    policy_id, scope, diff, rule, ceiling = _id(raw["run_policy_id"]), _paths(raw["scope_paths"]), _nat(raw["diff_bound"]), _id(raw["promotion_rule_id"]), _text(raw["claim_ceiling"])
    iteration, timeout, outputs = _positive_or_none(raw["iteration_bound"]), _positive_or_none(raw["time_bound_seconds"]), _strings(raw["output_surfaces"])
    if (
        policy_id is None or scope is None or diff is None or rule is None or ceiling is None
        or iteration is _BAD or timeout is _BAD or outputs is None
        or any(output not in _ALLOWED_OUTPUTS for output in outputs)
    ):
        return _result("REFUSE", "RUN_POLICY_INVALID", "RunPolicy contains invalid fields.")
    return _result("VALIDATED", "RUN_POLICY_VALIDATED", "Policy validated; nothing ran.", RunPolicy(
        RUN_POLICY_SCHEMA, policy_id, completion, regressions, scope, diff, rule,
        iteration, timeout, measure, outputs, ceiling,
    ))


def validate_concern_record(raw: Any) -> ContractValidation[ConcernRecord]:
    fields = {"schema", "concern_id", "source", "locator", "description", "discovered_at", "source_sha256"}
    raw = _object(raw, fields)
    if raw is None or raw["schema"] != CONCERN_RECORD_SCHEMA:
        return _result("HOLD", "CONCERN_NOT_STRUCTURED", "Concern must be an exact structured record.")
    concern_id, source, locator = _id(raw["concern_id"]), _text(raw["source"]), _text(raw["locator"])
    description, found_at, digest = _text(raw["description"]), _time(raw["discovered_at"]), _sha(raw["source_sha256"])
    if None in (concern_id, source, locator, description, found_at, digest):
        return _result("HOLD", "CONCERN_NOT_STRUCTURED", "Concern needs source, locator, description, time, and hash.")
    return _result("VALIDATED", "CONCERN_RECORD_VALIDATED", "Concern validated; no Issue opened.", ConcernRecord(
        CONCERN_RECORD_SCHEMA, concern_id, source, locator, description, found_at, digest,  # type: ignore[arg-type]
    ))


def validate_issue(raw: Any) -> ContractValidation[Issue]:
    fields = {"schema", "issue_id", "concern_id", "classification_gate", "disposition", "reason_code", "classification_receipt_sha256"}
    raw = _object(raw, fields)
    if raw is None or raw["schema"] != ISSUE_SCHEMA:
        return _result("REFUSE", "ISSUE_INVALID", "Issue must be an exact record.")
    gate = _gate(raw["classification_gate"])
    if gate is None:
        return _result("HOLD", "ISSUE_CLASSIFICATION_GATE_REQUIRED", "Issue requires a deterministic classification gate.")
    issue_id, concern_id, reason, receipt = _id(raw["issue_id"]), _id(raw["concern_id"]), _text(raw["reason_code"]), _sha(raw["classification_receipt_sha256"])
    if issue_id is None or concern_id is None or reason is None or receipt is None or raw["disposition"] not in ISSUE_DISPOSITIONS:
        return _result("REFUSE", "ISSUE_INVALID", "Issue fields are invalid.")
    return _result("VALIDATED", "ISSUE_VALIDATED", "Immutable Issue validated.", Issue(
        ISSUE_SCHEMA, issue_id, concern_id, gate, raw["disposition"], reason, receipt,
    ))


def validate_producer_binding(raw: Any) -> ContractValidation[ProducerBinding]:
    fields = {"schema", "binding_id", "producer_id", "issue_id", "binding_history", "binding_state", "binding_evidence_sha256s", "producer_receipt_sha256", "updated_at"}
    raw = _object(raw, fields)
    if raw is None or raw["schema"] != PRODUCER_BINDING_SCHEMA:
        return _result("REFUSE", "PRODUCER_BINDING_INVALID", "ProducerBinding must be an exact record.")
    history = tuple(raw["binding_history"]) if _seq(raw["binding_history"]) else ()
    state = raw["binding_state"]
    if not history or history != BINDING_STATES[:len(history)] or history[-1] != state:
        return _result("REFUSE", "BINDING_STATE_SKIPPED", "Binding must advance one declared state at a time.")
    evidence = tuple(raw["binding_evidence_sha256s"]) if _seq(raw["binding_evidence_sha256s"]) else ()
    receipt = None if raw["producer_receipt_sha256"] is None else _sha(raw["producer_receipt_sha256"])
    binding_id, producer_id, issue_id, updated_at = _id(raw["binding_id"]), _id(raw["producer_id"]), _id(raw["issue_id"]), _time(raw["updated_at"])
    if (
        len(evidence) != len(history) or any(_sha(item) is None for item in evidence)
        or binding_id is None or producer_id is None or issue_id is None or updated_at is None
        or (raw["producer_receipt_sha256"] is not None and receipt is None)
    ):
        return _result("REFUSE", "PRODUCER_BINDING_INVALID", "Binding fields are invalid.")
    if state == "receipt_verified" and receipt is None:
        return _result("HOLD", "HOLD_RECEIPT_NOT_VERIFIED", "receipt_verified needs a receipt hash.")
    return _result("VALIDATED", "PRODUCER_BINDING_VALIDATED", "Binding validated; it grants no action authority.", ProducerBinding(
        PRODUCER_BINDING_SCHEMA, binding_id, producer_id, issue_id, history, state, evidence, receipt, updated_at,  # type: ignore[arg-type]
    ))


def _proposal(raw: Any) -> ProposedAction | None:
    fields = {"action_type", "scope_paths", "diff_bound", "evidence_effect", "target_sha256"}
    raw = _object(raw, fields)
    if raw is None:
        return None
    action_type, paths, diff, digest = _id(raw["action_type"]), _paths(raw["scope_paths"]), _nat(raw["diff_bound"]), _sha(raw["target_sha256"])
    effect = raw["evidence_effect"]
    if action_type is None or paths is None or diff is None or digest is None or effect not in {"non_evidence_increasing", "evidence_increasing"}:
        return None
    return ProposedAction(action_type, paths, diff, effect, digest)


def _under(path: str, scope: str) -> bool:
    return path == scope or path.startswith(scope + "/")


def validate_repair_candidate(raw: Any, policy: RunPolicy | Mapping[str, Any]) -> ContractValidation[RepairCandidate]:
    """Validate producer data.  Binding eligibility is deliberately separate."""

    if isinstance(raw, Mapping):
        if found := _contains_authority(raw):
            return _result("REFUSE", "NONDETERMINISTIC_AUTHORITY", f"Producer field {found} cannot decide.")
        if "binding_state" in raw or "binding_history" in raw:
            return _result("REFUSE", "REFUSE_CANDIDATE_CONTAINS_BINDING_STATE", "Binding belongs in ProducerBinding.")
    policy_result = policy if isinstance(policy, RunPolicy) else validate_run_policy(policy)
    if not isinstance(policy_result, RunPolicy):
        if not policy_result.is_validated or policy_result.value is None:
            return _result(policy_result.disposition, policy_result.reason_code, "Policy preflight failed.")
        policy_result = policy_result.value
    fields = {"schema", "candidate_id", "issue_id", "producer_type", "producer_id", "proposed_action", "evidence_refs", "produced_at"}
    raw = _object(raw, fields)
    if raw is None or raw["schema"] != REPAIR_CANDIDATE_SCHEMA:
        return _result("REFUSE", "REPAIR_CANDIDATE_INVALID", "Candidate must be an exact record.")
    candidate_id, issue_id, producer_id = _id(raw["candidate_id"]), _id(raw["issue_id"]), _id(raw["producer_id"])
    proposal, refs, produced_at = _proposal(raw["proposed_action"]), _strings(raw["evidence_refs"], nonempty=True), _time(raw["produced_at"])
    if candidate_id is None or issue_id is None or producer_id is None or proposal is None or refs is None or produced_at is None or raw["producer_type"] not in PRODUCER_TYPES:
        return _result("REFUSE", "REPAIR_CANDIDATE_INVALID", "Candidate fields are invalid.")
    if proposal.evidence_effect == "evidence_increasing":
        return _result("PROPOSED_FOR_OWNER", "CANDIDATE_EVIDENCE_INCREASING", "Evidence expansion needs owner authority.")
    if any(not any(_under(path, scope) for scope in policy_result.scope_paths) for path in proposal.scope_paths):
        return _result("PROPOSED_FOR_OWNER", "CANDIDATE_OUT_OF_SCOPE", "Candidate escapes declared scope.")
    if proposal.diff_bound > policy_result.diff_bound:
        return _result("HOLD", "ACTION_EXCEEDS_BOUND", "Candidate exceeds diff bound.")
    return _result("VALIDATED", "REPAIR_CANDIDATE_VALIDATED", "Candidate validated; no action was selected.", RepairCandidate(
        REPAIR_CANDIDATE_SCHEMA, candidate_id, issue_id, raw["producer_type"], producer_id, proposal, refs, produced_at,
    ))


def repair_action_fingerprint(candidate: RepairCandidate) -> str:
    """Bind exclusion to repair semantics, not mutable candidate envelope fields."""

    return canonical_sha256(
        {
            "schema": REPAIR_ACTION_FINGERPRINT_SCHEMA,
            "issue_id": candidate.issue_id,
            "proposed_action": candidate.proposed_action.as_dict(),
        }
    )


def admit_repair_candidate(
    candidate: RepairCandidate,
    binding: ProducerBinding,
    issue: Issue,
    policy: RunPolicy,
    *,
    round_index: int,
    excluded_repair_action_fingerprints: Sequence[str] = (),
    parent_gate_run: GateRun | None = None,
) -> ContractValidation[RepairAction]:
    """Produce a pending action for one controller-selected candidate only."""

    checked = validate_repair_candidate(candidate.as_dict(), policy)
    if not checked.is_validated:
        return _result(checked.disposition, checked.reason_code, "Candidate cannot be promoted.")
    if (
        binding.producer_id != candidate.producer_id or binding.issue_id != candidate.issue_id
        or binding.binding_state != "receipt_verified" or binding.producer_receipt_sha256 is None
    ):
        return _result("HOLD", "HOLD_CANDIDATE_NOT_RECEIPT_VERIFIED", "Matching binding is not receipt_verified.")
    if repair_action_fingerprint(candidate) in set(excluded_repair_action_fingerprints):
        return _result("REFUSE", "REFUSE_CANDIDATE_EXCLUDED", "Failed candidate cannot be retried.")
    if isinstance(round_index, bool) or not isinstance(round_index, int) or round_index < 0:
        return _result("REFUSE", "REPAIR_ACTION_INVALID", "round_index must be nonnegative.")
    if candidate.issue_id != issue.issue_id:
        return _result("REFUSE", "REFUSE_CANDIDATE_ISSUE_MISMATCH", "Candidate does not match Issue.")
    if issue.disposition in {"OUT_OF_SCOPE", "EVIDENCE_INSUFFICIENT"}:
        return _result("PROPOSED_FOR_OWNER", "ISSUE_REQUIRES_OWNER_RULING", "Issue is outside automatic authority.")
    if issue.disposition != "OPEN":
        return _result("HOLD", "ISSUE_NOT_OPEN", "Only OPEN Issues can receive actions.")
    if round_index > 0 and (
        parent_gate_run is None or parent_gate_run.round_index != round_index - 1
    ):
        return _result("HOLD", "SECOND_ACTION_WITHOUT_DECREASING_ROUND", "Later round needs a fresh parent GateRun.")
    seed = canonical_sha256({"issue": issue.issue_id, "candidate": candidate.sha256, "policy": policy.sha256, "round": round_index})
    return _result("VALIDATED", "REPAIR_ACTION_ADMITTED", "Pending action admitted; not applied.", RepairAction(
        REPAIR_ACTION_SCHEMA, f"repair-action-{seed[:24]}", issue.issue_id, candidate.candidate_id,
        candidate.sha256, policy.sha256, policy.promotion_rule_id, round_index,
        None if parent_gate_run is None else parent_gate_run.sha256,
        candidate.proposed_action.action_type, candidate.proposed_action.scope_paths, candidate.proposed_action.diff_bound,
    ))


def validate_action_application(
    raw: Any, action: RepairAction
) -> ContractValidation[ActionApplication]:
    """Bind a completed external application to one admitted RepairAction."""

    fields = {
        "schema", "application_id", "action_id", "action_sha256", "executor_asset_id",
        "execution_receipt_sha256", "input_state_sha256", "output_state_sha256", "applied_at",
    }
    raw = _object(raw, fields)
    if raw is None or raw["schema"] != ACTION_APPLICATION_SCHEMA:
        return _result("REFUSE", "ACTION_APPLICATION_INVALID", "ActionApplication must be an exact record.")
    if raw["action_id"] != action.action_id or raw["action_sha256"] != action.sha256:
        return _result(
            "REFUSE", "REFUSE_ACTION_APPLICATION_BINDING_MISMATCH",
            "ActionApplication is not bound to the admitted RepairAction.",
        )
    values = (
        _id(raw["application_id"]), _sha(raw["action_sha256"]), _id(raw["executor_asset_id"]),
        _sha(raw["execution_receipt_sha256"]), _sha(raw["input_state_sha256"]),
        _sha(raw["output_state_sha256"]), _time(raw["applied_at"]),
    )
    if any(value is None for value in values):
        return _result("REFUSE", "ACTION_APPLICATION_INVALID", "ActionApplication fields are invalid.")
    return _result(
        "VALIDATED", "ACTION_APPLICATION_VALIDATED",
        "Application receipt binding validated; no repair or gate result was claimed.",
        ActionApplication(
            ACTION_APPLICATION_SCHEMA, values[0], action.action_id, values[1], values[2],
            values[3], values[4], values[5], values[6],  # type: ignore[arg-type]
        ),
    )


def _regression_results(raw: Any, policy: RunPolicy) -> tuple[RegressionGateResult, ...] | None:
    if not _seq(raw):
        return None
    expected = {gate.gate_id: gate for gate in policy.required_regression_gates}
    observed: dict[str, RegressionGateResult] = {}
    for item in raw:
        item = _object(item, {"gate_id", "definition_sha256", "result"})
        if item is None:
            return None
        gate_id, digest, result = _id(item["gate_id"]), _sha(item["definition_sha256"]), item["result"]
        gate = expected.get(gate_id) if gate_id is not None else None
        if gate is None or digest != gate.definition_sha256 or result not in {"PASS", "FAIL"} or gate_id in observed:
            return None
        observed[gate_id] = RegressionGateResult(gate_id, digest, result)
    if set(observed) != set(expected):
        return None
    return tuple(observed[gate.gate_id] for gate in policy.required_regression_gates)


def validate_gate_run(raw: Any, policy: RunPolicy, action: RepairAction) -> ContractValidation[GateRun]:
    """Bind aggregate and every declared regression result; execute nothing."""

    fields = {
        "schema", "gate_run_id", "action_id", "action_sha256", "run_policy_sha256", "round_index",
        "aggregate_gate_id", "aggregate_gate_definition_sha256", "aggregate_result", "required_gate_results",
        "input_state_sha256", "current_state_sha256", "measure_value", "executed_at",
    }
    raw = _object(raw, fields)
    if raw is None or raw["schema"] != GATE_RUN_SCHEMA:
        return _result("REFUSE", "GATE_RUN_INVALID", "GateRun must be an exact record.")
    if raw["action_id"] != action.action_id or raw["action_sha256"] != action.sha256 or raw["run_policy_sha256"] != policy.sha256:
        return _result("REFUSE", "REFUSE_GATE_BINDING_MISMATCH", "GateRun does not bind action and policy.")
    if raw["round_index"] != action.round_index or raw["aggregate_gate_id"] != policy.completion_gate.gate_id or raw["aggregate_gate_definition_sha256"] != policy.completion_gate.definition_sha256:
        return _result("REFUSE", "REFUSE_GATE_NOT_DECLARED_COMPLETION_GATE", "Aggregate gate is not declared.")
    regressions = _regression_results(raw["required_gate_results"], policy)
    if regressions is None:
        return _result("REFUSE", "REFUSE_REQUIRED_REGRESSION_GATES_UNBOUND", "Every regression gate needs one exact result.")
    if raw["aggregate_result"] not in {"PASS", "FAIL"}:
        return _result("REFUSE", "GATE_RUN_INVALID", "Aggregate result must be PASS or FAIL.")
    if raw["aggregate_result"] == "PASS" and any(result.result == "FAIL" for result in regressions):
        return _result("REFUSE", "REFUSE_REGRESSION_GATE_HIDDEN", "Regression failure forces aggregate FAIL.")
    values = (
        _id(raw["gate_run_id"]), _sha(raw["action_sha256"]), _sha(raw["run_policy_sha256"]),
        _sha(raw["aggregate_gate_definition_sha256"]), _sha(raw["input_state_sha256"]),
        _sha(raw["current_state_sha256"]), _nat(raw["measure_value"]), _time(raw["executed_at"]),
    )
    if any(value is None for value in values):
        return _result("REFUSE", "GATE_RUN_INVALID", "GateRun fields are invalid.")
    return _result("VALIDATED", "GATE_RUN_VALIDATED", "GateRun bindings validated; no gate was run.", GateRun(
        GATE_RUN_SCHEMA, values[0], action.action_id, values[1], values[2], action.round_index,
        policy.completion_gate.gate_id, values[3], raw["aggregate_result"], regressions,
        values[4], values[5], values[6], values[7],  # type: ignore[arg-type]
    ))


_BAD = object()
