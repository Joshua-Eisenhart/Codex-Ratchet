"""Deterministic user-request intake for ConstraintBox.

The request states what the user wants and authorizes.  It cannot select the
effective policy, checker, tolerance, tool, retry budget, disposition, or
release text.  Completeness is settled by the same finite encoding through
Z3, CVC5, and exhaustive enumeration.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .clause_feedback import (
    ClauseFeedbackError,
    ClauseFeedbackUnavailable,
    build_clause_feedback,
)
from .capability_origin import capability_ids
from .intake import IntakeError, canonical_json, parse_json_object


SCHEMA = "constraintbox.user-request.v1"
POLICY_ID = "constraintbox.user-request-policy.v1"
ELIGIBLE = "ELIGIBLE_FOR_PROPOSAL"
PARKED = "PARKED"
BLOCKED = "BLOCKED"
EVALUATION_ERROR = "EVALUATION_ERROR"
_ELIGIBLE_CLAIM_CEILING = (
    "the request is explicit enough to ask an untrusted model for a proposal; "
    "no proposal, tool result, or release is admitted"
)
_NONELIGIBLE_CLAIM_CEILING = (
    "request assessment and retry guidance only; no proposal generation, "
    "tool result, or release is admitted"
)

ROOT_FIELDS = {
    "schema",
    "request_id",
    "goal",
    "deliverable",
    "in_scope",
    "out_of_scope",
    "assumption_state",
    "assumptions",
    "evidence_required",
    "allowed_actions",
    "requested_external_tests",
    "claim_boundary",
    "unknowns",
    "communication_needs",
}

AUTHORITY_FIELDS = {
    "all_pass",
    "checker",
    "claim_ceiling",
    "command",
    "decision",
    "disposition",
    "effective_policy",
    "obligations",
    "pass",
    "policy",
    "profile_id",
    "promotion_allowed",
    "release",
    "retry_budget",
    "tolerance",
    "tool",
    "verdict",
}

CLAUSE_QUESTIONS = {
    "goal_explicit": "What exact outcome should the system produce?",
    "deliverable_explicit": "What concrete file, answer, code change, or receipt should come back?",
    "scope_explicit": "What is in scope, and what is explicitly out of scope?",
    "assumptions_explicit": "Which assumptions are being made, or should this state that no assumptions are currently asserted?",
    "evidence_explicit": "What evidence must exist before the requested work can be called complete?",
    "actions_explicit": "Which actions may the system take: read, edit, run tests, call an LLM, or run external tools?",
    "external_tests_explicit": "Which controller-supported external test packet is requested, or should external testing be omitted?",
    "claim_boundary_explicit": "What is the strongest conclusion this request is allowed to support?",
}

_CLAUSE_ORDER = tuple(CLAUSE_QUESTIONS)
_SAFE_ACTIONS = {
    "read",
    "edit",
    "execute_tests",
    "invoke_llm",
    "run_external_tools",
    "write_receipts",
}
# These names authorize fixed controller profiles.  They are not module names,
# command strings, or user-selectable implementations: each public caller
# binds one profile to its own static tool/gate flow.  The source-owned origin
# registry is the one authority so request intake cannot silently lag behind
# the dispatcher when a controller-owned profile is added.
_SUPPORTED_EXTERNAL_TESTS = frozenset({"basic_packet_v1", *capability_ids()})
_ASSUMPTION_STATES = {"listed", "none_stated", "unknown"}


class _RequiredSmtUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class RequestAssessment:
    schema: str
    request_id: str | None
    disposition: str
    reason: str
    request_sha256: str
    policy_id: str
    policy_sha256: str
    failed_clauses: tuple[str, ...]
    questions: tuple[str, ...]
    solver: dict[str, Any] | None
    evidence: dict[str, Any]
    claim_ceiling: str
    promotion_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "request_id": self.request_id,
            "disposition": self.disposition,
            "reason": self.reason,
            "request_sha256": self.request_sha256,
            "policy_id": self.policy_id,
            "policy_sha256": self.policy_sha256,
            "failed_clauses": list(self.failed_clauses),
            "questions": list(self.questions),
            "solver": self.solver,
            "evidence": self.evidence,
            "claim_ceiling": self.claim_ceiling,
            "promotion_allowed": self.promotion_allowed,
        }


def _policy_sha256() -> str:
    module_root = Path(__file__).resolve().parent
    source_digests = {
        name: hashlib.sha256((module_root / name).read_bytes()).hexdigest()
        for name in (
            "clause_feedback.py",
            "constraints.py",
            "dualsolve.py",
            "user_request.py",
        )
    }
    return hashlib.sha256(
        canonical_json(
            {
                "policy_id": POLICY_ID,
                "schema": SCHEMA,
                "root_fields": sorted(ROOT_FIELDS),
                "authority_fields": sorted(AUTHORITY_FIELDS),
                "clauses": list(_CLAUSE_ORDER),
                "safe_actions": sorted(_SAFE_ACTIONS),
                "supported_external_tests": sorted(_SUPPORTED_EXTERNAL_TESTS),
                "mandatory_deciders": ["z3", "cvc5", "enumeration"],
                "finite_state_bound": 2 ** len(_CLAUSE_ORDER),
                "source_sha256": source_digests,
            }
        )
    ).hexdigest()


def _request_sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _walk_authority_fields(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key.casefold() in AUTHORITY_FIELDS:
                found.append(child_path)
            found.extend(_walk_authority_fields(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_walk_authority_fields(child, f"{path}[{index}]"))
    return found


def _nonempty_text(value: Any, *, maximum: int = 10_000) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and len(value) <= maximum
    )


def _string_list(
    value: Any,
    *,
    nonempty: bool,
    allowed: set[str] | None = None,
) -> bool:
    if not isinstance(value, list) or (nonempty and not value):
        return False
    if any(not _nonempty_text(item, maximum=500) for item in value):
        return False
    if len(set(value)) != len(value):
        return False
    return allowed is None or set(value).issubset(allowed)


def _assumptions_valid(body: dict[str, Any]) -> tuple[bool, str | None]:
    state = body.get("assumption_state")
    assumptions = body.get("assumptions")
    if state not in _ASSUMPTION_STATES:
        return False, "assumption_state must be listed, none_stated, or unknown"
    if not isinstance(assumptions, list):
        return False, "assumptions must be a list"
    if state == "none_stated":
        return (not assumptions, None if not assumptions else "none_stated requires an empty assumptions list")
    if state == "unknown":
        return False, "assumptions are explicitly unresolved"
    if not assumptions:
        return False, "listed requires at least one assumption"
    for index, assumption in enumerate(assumptions):
        if not isinstance(assumption, dict) or set(assumption) != {
            "statement",
            "source",
            "status",
        }:
            return False, f"assumptions[{index}] must contain statement, source, and status"
        if not _nonempty_text(assumption["statement"], maximum=1_000):
            return False, f"assumptions[{index}].statement is invalid"
        if not _nonempty_text(assumption["source"], maximum=500):
            return False, f"assumptions[{index}].source is invalid"
        if assumption["status"] not in {"owner_asserted", "working", "to_test"}:
            return False, f"assumptions[{index}].status is invalid"
    return True, None


def _shape_errors(body: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if set(body) != ROOT_FIELDS:
        missing = sorted(ROOT_FIELDS - set(body))
        extra = sorted(set(body) - ROOT_FIELDS)
        if missing:
            errors.append("missing root fields: " + ", ".join(missing))
        if extra:
            errors.append("unexpected root fields: " + ", ".join(extra))
    if body.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    request_id = body.get("request_id")
    if not _nonempty_text(request_id, maximum=128):
        errors.append("request_id must be a nonempty string of at most 128 characters")
    for field in ("goal", "deliverable", "claim_boundary"):
        value = body.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(f"{field} must be a string")
    for field in (
        "in_scope",
        "out_of_scope",
        "evidence_required",
        "allowed_actions",
        "requested_external_tests",
        "unknowns",
        "communication_needs",
    ):
        if field in body and not isinstance(body[field], list):
            errors.append(f"{field} must be a list")
    if "allowed_actions" in body and isinstance(body["allowed_actions"], list):
        if any(not isinstance(item, str) for item in body["allowed_actions"]):
            errors.append("allowed_actions must contain only strings")
        else:
            unknown_actions = sorted(
                set(body["allowed_actions"]) - _SAFE_ACTIONS
            )
            if unknown_actions:
                errors.append(
                    "unknown allowed_actions: " + ", ".join(unknown_actions)
                )
    if "requested_external_tests" in body and isinstance(
        body["requested_external_tests"], list
    ):
        if any(
            not isinstance(item, str)
            for item in body["requested_external_tests"]
        ):
            errors.append("requested_external_tests must contain only strings")
        else:
            unknown_tests = sorted(
                set(body["requested_external_tests"])
                - _SUPPORTED_EXTERNAL_TESTS
            )
            if unknown_tests:
                errors.append(
                    "unknown requested_external_tests: "
                    + ", ".join(unknown_tests)
                )
    return errors


def _clause_values(body: dict[str, Any]) -> tuple[dict[str, bool], dict[str, Any]]:
    assumptions_ok, assumption_detail = _assumptions_valid(body)
    allowed_actions = body.get("allowed_actions")
    external_tools_requested = (
        isinstance(allowed_actions, list)
        and "run_external_tools" in allowed_actions
    )
    requested_external_tests = body.get("requested_external_tests")
    external_tests_explicit = _string_list(
        requested_external_tests,
        nonempty=external_tools_requested,
        allowed=_SUPPORTED_EXTERNAL_TESTS,
    ) and (
        external_tools_requested
        or requested_external_tests == []
    )
    values = {
        "goal_explicit": _nonempty_text(body.get("goal")),
        "deliverable_explicit": _nonempty_text(body.get("deliverable")),
        "scope_explicit": (
            _string_list(body.get("in_scope"), nonempty=True)
            and _string_list(body.get("out_of_scope"), nonempty=False)
        ),
        "assumptions_explicit": assumptions_ok,
        "evidence_explicit": _string_list(
            body.get("evidence_required"), nonempty=True
        ),
        "actions_explicit": _string_list(
            allowed_actions,
            nonempty=True,
            allowed=_SAFE_ACTIONS,
        ),
        "external_tests_explicit": external_tests_explicit,
        "claim_boundary_explicit": _nonempty_text(body.get("claim_boundary")),
    }
    detail = {
        "assumption_detail": assumption_detail,
        "unknowns_recorded": _string_list(body.get("unknowns"), nonempty=False),
        "communication_needs_recorded": _string_list(
            body.get("communication_needs"), nonempty=False
        ),
        "requested_external_tests": (
            list(requested_external_tests)
            if isinstance(requested_external_tests, list)
            else None
        ),
    }
    return values, detail


def _eq(variable: str, value: bool) -> dict[str, Any]:
    return {
        "op": "eq",
        "left": {"var": variable},
        "right": {"const": value},
    }


def _solve_clauses(
    values: dict[str, bool],
    failed: tuple[str, ...],
) -> dict[str, Any]:
    # Import here so strict parsing and authority rejection still work when a
    # solver is unavailable. Missing SMT then parks; it never silently falls
    # back to an all-Python release decision.
    try:
        from .dualsolve import dual_solve
    except ModuleNotFoundError as exc:
        if exc.name == "cvc5":
            raise _RequiredSmtUnavailable(str(exc)) from exc
        raise

    spec = {
        "variables": {name: [False, True] for name in _CLAUSE_ORDER},
        "constraints": [
            *[_eq(name, values[name]) for name in _CLAUSE_ORDER],
            *[_eq(name, True) for name in _CLAUSE_ORDER],
        ],
    }
    result = dual_solve(spec, max_states=2 ** len(_CLAUSE_ORDER))
    result["schema"] = "constraintbox.user-request-smt.v1"
    result["polarity"] = {
        "BOUNDED_SAT": "every required request clause is satisfied",
        "BOUNDED_UNSAT": "at least one required request clause is not satisfied",
        "UNKNOWN": "the request gate is unresolved and must not pass",
    }
    result["finite_state_bound"] = 2 ** len(_CLAUSE_ORDER)
    result["spec_sha256"] = hashlib.sha256(canonical_json(spec)).hexdigest()
    statuses = {
        result.get("z3"),
        result.get("cvc5"),
        result.get("enumeration"),
    }
    clean_dual_result = (
        result.get("agree") is True
        and result.get("has_execution_error") is False
        and result.get("definite_status_conflict") is False
        and statuses in (
            {"BOUNDED_SAT"},
            {"BOUNDED_UNSAT"},
        )
    )
    result["clause_feedback"] = None
    result["clause_feedback_state"] = "NOT_RUN_DUAL_SOLVER_UNSETTLED"
    result["retry_feedback"] = []
    if not clean_dual_result:
        return result
    try:
        result["clause_feedback"] = build_clause_feedback(
            values,
            clause_order=_CLAUSE_ORDER,
            retry_questions=CLAUSE_QUESTIONS,
            reference_failed=failed,
        )
    except ClauseFeedbackUnavailable as exc:
        raise _RequiredSmtUnavailable(str(exc)) from exc
    result["clause_feedback_state"] = "EXECUTED_AND_CROSSCHECKED"
    result["retry_feedback"] = result["clause_feedback"]["retry_feedback"]
    return result


def _assessment(
    raw: bytes,
    *,
    request_id: str | None,
    disposition: str,
    reason: str,
    failed_clauses: tuple[str, ...] = (),
    solver: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
    claim_ceiling: str = _NONELIGIBLE_CLAIM_CEILING,
) -> RequestAssessment:
    return RequestAssessment(
        schema="constraintbox.user-request-assessment.v1",
        request_id=request_id,
        disposition=disposition,
        reason=reason,
        request_sha256=_request_sha256(raw),
        policy_id=POLICY_ID,
        policy_sha256=_policy_sha256(),
        failed_clauses=failed_clauses,
        questions=tuple(CLAUSE_QUESTIONS[name] for name in failed_clauses),
        solver=solver,
        evidence=evidence or {},
        claim_ceiling=claim_ceiling,
    )


def assess_user_request(raw: bytes) -> RequestAssessment:
    """Assess one immutable user-request byte snapshot."""

    try:
        body = parse_json_object(raw)
    except IntakeError as exc:
        return _assessment(
            raw,
            request_id=None,
            disposition=BLOCKED,
            reason="strict_request_intake_failed",
            evidence={"error": str(exc)},
        )

    request_id = body.get("request_id") if isinstance(body.get("request_id"), str) else None
    authority_paths = _walk_authority_fields(body)
    if authority_paths:
        return _assessment(
            raw,
            request_id=request_id,
            disposition=BLOCKED,
            reason="request_attempted_controller_authority",
            evidence={"forbidden_paths": authority_paths},
        )

    shape_errors = _shape_errors(body)
    if shape_errors:
        return _assessment(
            raw,
            request_id=request_id,
            disposition=BLOCKED,
            reason="request_schema_invalid",
            evidence={"errors": shape_errors},
        )

    clauses, detail = _clause_values(body)
    failed = tuple(name for name in _CLAUSE_ORDER if not clauses[name])
    try:
        solver = _solve_clauses(clauses, failed)
    except _RequiredSmtUnavailable as exc:
        return _assessment(
            raw,
            request_id=request_id,
            disposition=PARKED,
            reason="required_smt_instrument_unavailable",
            failed_clauses=failed,
            evidence={"error": str(exc), "clauses": clauses, **detail},
        )
    except ClauseFeedbackError as exc:
        return _assessment(
            raw,
            request_id=request_id,
            disposition=EVALUATION_ERROR,
            reason="request_clause_feedback_evaluation_failed",
            failed_clauses=failed,
            evidence={
                "clause_feedback_reason": exc.reason,
                "clause_feedback": exc.evidence,
                "clauses": clauses,
                **detail,
            },
        )
    except Exception as exc:  # fail closed at the solver boundary
        return _assessment(
            raw,
            request_id=request_id,
            disposition=EVALUATION_ERROR,
            reason="request_smt_evaluation_failed",
            failed_clauses=failed,
            evidence={
                "exception_type": type(exc).__name__,
                "error": str(exc),
                "clauses": clauses,
                **detail,
            },
        )

    statuses = {
        solver.get("z3"),
        solver.get("cvc5"),
        solver.get("enumeration"),
    }
    definite_statuses = statuses & {"BOUNDED_SAT", "BOUNDED_UNSAT"}
    definite_status_conflict = (
        solver.get("definite_status_conflict") is True
        or len(definite_statuses) > 1
    )
    if definite_status_conflict:
        disposition = EVALUATION_ERROR
        reason = "request_solver_disagreement"
    elif solver.get("has_execution_error") is True:
        disposition = EVALUATION_ERROR
        reason = "request_solver_execution_failed"
    elif "UNKNOWN" in statuses or None in statuses:
        disposition = PARKED
        reason = "request_solver_unresolved"
    elif not solver.get("agree"):
        disposition = EVALUATION_ERROR
        reason = "request_solver_disagreement"
    elif statuses == {"BOUNDED_SAT"} and not failed:
        disposition = ELIGIBLE
        reason = "request_is_explicit_enough_for_untrusted_proposal_generation"
    elif statuses == {"BOUNDED_UNSAT"} and failed:
        disposition = PARKED
        reason = "request_needs_explicit_user_information"
    else:
        disposition = EVALUATION_ERROR
        reason = "request_solver_result_inconsistent_with_clause_evaluation"

    return _assessment(
        raw,
        request_id=request_id,
        disposition=disposition,
        reason=reason,
        failed_clauses=failed,
        solver=solver,
        evidence={
            "clauses": clauses,
            "assumption_state": body["assumption_state"],
            "allowed_actions": body["allowed_actions"],
            "requested_external_tests": body["requested_external_tests"],
            "declared_claim_boundary": body["claim_boundary"],
            "retry_feedback": solver["retry_feedback"],
            **detail,
        },
        claim_ceiling=(
            _ELIGIBLE_CLAIM_CEILING
            if disposition == ELIGIBLE
            else _NONELIGIBLE_CLAIM_CEILING
        ),
    )
