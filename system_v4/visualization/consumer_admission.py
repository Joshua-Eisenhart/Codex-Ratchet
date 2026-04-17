from __future__ import annotations


def evaluate_consumer_admission(report: dict, consumer: str | None) -> dict:
    eligible = list(report.get("eligible_consumers", []))
    blocked = list(report.get("blocked_consumers", []))
    promotion_blockers = list(report.get("promotion_blockers", []))

    if consumer is None:
        return {
            "requested_consumer": None,
            "admitted": True,
            "decision": "no_consumer_requested",
            "reasons": [],
            "eligible_consumers": eligible,
            "blocked_consumers": blocked,
            "promotion_blockers": promotion_blockers,
        }

    reasons: list[str] = []
    if consumer in blocked:
        reasons.append("consumer_blocked")
    if eligible and consumer not in eligible:
        reasons.append("consumer_not_listed_as_eligible")

    admitted = not reasons
    decision = "admitted" if admitted else "blocked"
    if admitted and promotion_blockers:
        decision = "admitted_with_promotion_blockers"

    return {
        "requested_consumer": consumer,
        "admitted": admitted,
        "decision": decision,
        "reasons": reasons,
        "eligible_consumers": eligible,
        "blocked_consumers": blocked,
        "promotion_blockers": promotion_blockers,
    }
