"""Nonauthoritative explanation sidecars for ConstraintBox decisions."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from .intake import IntakeError, canonical_json, parse_json_object
from .user_request import AUTHORITY_FIELDS


ADVICE_SCHEMA = "constraintbox.audit-advice.v1"
ALLOWED_FIELDS = {
    "schema",
    "decision_sha256",
    "plain_explanation",
    "questions",
    "suggested_resubmission",
}
FORBIDDEN_FIELDS = {
    "claim_ceiling",
    "decision",
    "disposition",
    "effective_actions",
    "evidence",
    "obligations",
    "policy",
    "promotion_allowed",
    "release",
    "retry_budget",
    "tolerance",
    "verdict",
}
_ADVISORY_AUTHORITY_FIELDS = frozenset(
    field.casefold() for field in FORBIDDEN_FIELDS | AUTHORITY_FIELDS
)


class AdviceError(ValueError):
    pass


@dataclass(frozen=True)
class AdviceSidecar:
    schema: str
    decision_sha256: str
    advice_sha256: str
    plain_explanation: str
    questions: tuple[str, ...]
    suggested_resubmission: dict[str, Any]
    advisory_only: bool = True
    changes_deterministic_decision: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "decision_sha256": self.decision_sha256,
            "advice_sha256": self.advice_sha256,
            "plain_explanation": self.plain_explanation,
            "questions": list(self.questions),
            "suggested_resubmission": self.suggested_resubmission,
            "advisory_only": self.advisory_only,
            "changes_deterministic_decision": self.changes_deterministic_decision,
        }


def decision_sha256(decision: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(decision)).hexdigest()


def _forbidden_advice_paths(
    value: object,
    *,
    path: str = "$",
) -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = key if path == "$" else f"{path}.{key}"
            if key.casefold() in _ADVISORY_AUTHORITY_FIELDS:
                paths.append(child)
            paths.extend(_forbidden_advice_paths(item, path=child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(
                _forbidden_advice_paths(item, path=f"{path}[{index}]")
            )
    return paths


def build_audit_brief(
    decision: dict[str, Any],
    *,
    output_contract: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Build the frozen input that an optional explainer LLM may read."""

    digest = decision_sha256(decision)
    return {
        "schema": "constraintbox.audit-brief.v1",
        "decision_sha256": digest,
        "frozen_disposition": decision.get("disposition"),
        "frozen_reason": decision.get("reason"),
        "failed_clauses": list(decision.get("failed_clauses") or []),
        "controller_questions": list(decision.get("questions") or []),
        "claim_ceiling": decision.get("claim_ceiling"),
        "output_contract": list(output_contract),
        "allowed_advice_fields": sorted(ALLOWED_FIELDS),
        "instructions": [
            "Explain the frozen decision in plain language.",
            "Suggest how the user can make the request more explicit.",
            "Do not issue a verdict, change the disposition, alter evidence, or widen the claim ceiling.",
            "Any suggested resubmission will be checked again from the beginning.",
        ],
        "advisory_only": True,
    }


def deterministic_explanation(decision: dict[str, Any]) -> AdviceSidecar:
    """Fallback explanation that needs no LLM and cannot change settlement."""

    digest = decision_sha256(decision)
    disposition = decision.get("disposition", "EVALUATION_ERROR")
    questions = tuple(
        item
        for item in decision.get("questions", [])
        if isinstance(item, str) and item.strip()
    )
    if disposition == "ELIGIBLE_FOR_PROPOSAL":
        explanation = (
            "The request is explicit enough to ask an untrusted model for a proposal. "
            "No proposal, tool result, or final output has passed yet."
        )
    elif disposition == "PARKED":
        explanation = (
            "The request is paused because required information or a required "
            "checking instrument is missing or unresolved."
        )
    elif disposition == "BLOCKED":
        explanation = (
            "The request was rejected before work because its structure was "
            "invalid or it attempted to set controller-owned authority."
        )
    else:
        explanation = (
            "The request could not be settled consistently. No work or release "
            "should proceed from this result."
        )
    body = {
        "schema": ADVICE_SCHEMA,
        "decision_sha256": digest,
        "plain_explanation": explanation,
        "questions": list(questions),
        "suggested_resubmission": {},
    }
    return AdviceSidecar(
        schema=ADVICE_SCHEMA,
        decision_sha256=digest,
        advice_sha256=hashlib.sha256(canonical_json(body)).hexdigest(),
        plain_explanation=explanation,
        questions=questions,
        suggested_resubmission={},
    )


def accept_external_advice(
    raw: bytes,
    *,
    frozen_decision: dict[str, Any],
) -> AdviceSidecar:
    """Validate an explainer response without giving it decision authority."""

    try:
        body = parse_json_object(raw)
    except IntakeError as exc:
        raise AdviceError(f"advice is not strict JSON: {exc}") from exc
    forbidden = sorted(_forbidden_advice_paths(body))
    if forbidden:
        raise AdviceError(
            "advice attempted decision authority: " + ", ".join(forbidden)
        )
    if set(body) != ALLOWED_FIELDS:
        raise AdviceError("advice fields differ from the advisory-only schema")
    if body["schema"] != ADVICE_SCHEMA:
        raise AdviceError(f"advice schema must be {ADVICE_SCHEMA}")
    expected_decision = decision_sha256(frozen_decision)
    if body["decision_sha256"] != expected_decision:
        raise AdviceError("advice is not bound to the frozen decision")
    explanation = body["plain_explanation"]
    if not isinstance(explanation, str) or not explanation.strip():
        raise AdviceError("plain_explanation must be a nonempty string")
    questions = body["questions"]
    if (
        not isinstance(questions, list)
        or any(not isinstance(item, str) or not item.strip() for item in questions)
    ):
        raise AdviceError("questions must be a list of nonempty strings")
    suggested = body["suggested_resubmission"]
    if not isinstance(suggested, dict):
        raise AdviceError("suggested_resubmission must be an object")
    # The suggestion is deliberately not assessed or merged here. It must be
    # submitted to the normal request intake as new bytes.
    return AdviceSidecar(
        schema=ADVICE_SCHEMA,
        decision_sha256=expected_decision,
        advice_sha256=hashlib.sha256(canonical_json(body)).hexdigest(),
        plain_explanation=explanation.strip(),
        questions=tuple(questions),
        suggested_resubmission=suggested,
    )
