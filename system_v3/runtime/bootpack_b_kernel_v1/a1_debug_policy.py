from dataclasses import dataclass


HARD_FAILURE_TAGS = {
    "SCHEMA_FAIL",
    "UNDEFINED_TERM_USE",
    "DERIVED_ONLY_PRIMITIVE_USE",
    "DERIVED_ONLY_NOT_PERMITTED",
    "SPEC_KIND_UNSUPPORTED",
}


@dataclass(frozen=True)
class EscalationDecision:
    escalate: bool
    reasons: list[str]


def evaluate_escalation(
    a1_generation_fail_count: int,
    repeated_schema_fail: int,
    recent_reject_tags: list[str],
    generation_fail_limit: int = 3,
    schema_fail_limit: int = 5,
) -> EscalationDecision:
    reasons: list[str] = []
    if a1_generation_fail_count >= generation_fail_limit:
        reasons.append("A1_GENERATION_FAIL_LIMIT")
    if repeated_schema_fail >= schema_fail_limit:
        reasons.append("REPEATED_SCHEMA_FAIL_LIMIT")
    if recent_reject_tags and all(tag in HARD_FAILURE_TAGS for tag in recent_reject_tags):
        if len(recent_reject_tags) >= 3:
            reasons.append("HARD_TAG_CLUSTER")
    return EscalationDecision(escalate=bool(reasons), reasons=sorted(set(reasons)))

