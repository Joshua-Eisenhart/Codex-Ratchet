import json
from pathlib import Path

from constraintbox.model_tier_budget import (
    ModelTierLedger,
    model_tier_reasons,
    tier_for_slug,
)


POLICY = json.loads(
    (Path(__file__).parents[1] / "config" / "model_tier_policy.json").read_text()
)
TASK = "task-1"


def attempt(tier, outcome="failed", task_id=TASK):
    return {"task_id": task_id, "tier": tier, "outcome": outcome}


def spend(*attempts, output_tokens=0, tier="cheap", dispatches=0):
    return {
        tier: {"dispatches": dispatches, "output_tokens": output_tokens},
        "_attempts": list(attempts),
    }


def test_cheap_floor_is_frictionless_with_empty_ledger():
    assert tier_for_slug("gpt-5.6-luna", POLICY) == "cheap"
    assert model_tier_reasons("gpt-5.6-luna", "gpt-5.6-luna", "build", POLICY, {}, task_id=TASK) == []


def test_standard_after_failed_cheap_attempt_is_admitted():
    assert model_tier_reasons(
        "gpt-5.6-terra", "gpt-5.6-terra", "build", POLICY,
        spend(attempt("cheap")), task_id=TASK,
    ) == []


def test_standard_without_failed_cheap_attempt_is_unjustified():
    assert model_tier_reasons(
        "gpt-5.6-terra", "gpt-5.6-terra", "build", POLICY, {}, task_id=TASK,
    ) == ["MODEL_TIER_ESCALATION_UNJUSTIFIED"]


def test_premium_after_failed_standard_attempt_is_admitted():
    assert model_tier_reasons(
        "gpt-5.6-sol", "gpt-5.6-sol", "audit", POLICY,
        spend(attempt("standard")), task_id=TASK,
    ) == []


def test_premium_after_only_failed_cheap_attempt_skips_rung():
    assert model_tier_reasons(
        "gpt-5.6-sol", "gpt-5.6-sol", "audit", POLICY,
        spend(attempt("cheap")), task_id=TASK,
    ) == ["MODEL_TIER_ESCALATION_SKIPS_RUNG"]


def test_premium_in_swarm_is_role_forbidden():
    assert model_tier_reasons("gpt-5.6-sol", "gpt-5.6-sol", "swarm", POLICY, {}, task_id=TASK) == [
        "MODEL_TIER_ROLE_FORBIDDEN"
    ]


def test_unlisted_slug_is_unknown():
    assert model_tier_reasons("unknown", "model-not-listed", "build", POLICY, {}, task_id=TASK) == [
        "MODEL_TIER_UNKNOWN"
    ]


def test_outer_ceiling_is_a_wall():
    assert model_tier_reasons(
        "gpt-5.6-sol", "gpt-5.6-sol", "audit", POLICY,
        spend(attempt("standard"), output_tokens=5_000_000, tier="premium"), task_id=TASK,
    ) == ["MODEL_TIER_CEILING_EXHAUSTED"]


def test_outer_ceiling_boundary_one_token_below_is_admitted():
    base = spend(attempt("standard"), output_tokens=4_999_999, tier="premium")
    assert model_tier_reasons("gpt-5.6-sol", "gpt-5.6-sol", "audit", POLICY, base, task_id=TASK) == []
    base["premium"]["output_tokens"] = 5_000_000
    assert model_tier_reasons("gpt-5.6-sol", "gpt-5.6-sol", "audit", POLICY, base, task_id=TASK) == [
        "MODEL_TIER_CEILING_EXHAUSTED"
    ]


def test_successful_lower_attempt_does_not_justify_escalation():
    assert model_tier_reasons(
        "gpt-5.6-terra", "gpt-5.6-terra", "build", POLICY,
        spend(attempt("cheap", "succeeded")), task_id=TASK,
    ) == ["MODEL_TIER_ESCALATION_UNJUSTIFIED"]


def test_successful_standard_attempt_does_not_justify_premium():
    assert model_tier_reasons(
        "gpt-5.6-sol", "gpt-5.6-sol", "audit", POLICY,
        spend(attempt("standard", "succeeded")), task_id=TASK,
    ) == ["MODEL_TIER_ESCALATION_UNJUSTIFIED"]


def test_owner_declared_escalation_is_an_explicit_receipt():
    data = spend()
    data["_owner_escalations"] = [{"task_id": TASK, "to_tier": "standard"}]
    assert model_tier_reasons("gpt-5.6-terra", "gpt-5.6-terra", "build", POLICY, data, task_id=TASK) == []


def test_attempt_receipt_is_scoped_to_stable_task_id():
    assert model_tier_reasons(
        "gpt-5.6-terra", "gpt-5.6-terra", "build", POLICY,
        spend(attempt("cheap", task_id="other-task")), task_id=TASK,
    ) == ["MODEL_TIER_ESCALATION_UNJUSTIFIED"]


def test_ledger_chains_two_appends_and_detects_tampered_middle_record(tmp_path):
    path = tmp_path / "model_tier_budget.jsonl"
    ledger = ModelTierLedger(path)
    for index, tier in enumerate(("cheap", "standard", "premium"), 1):
        ledger.append(
            model_resolved=f"gpt-5.6-{ {'cheap': 'luna', 'standard': 'terra', 'premium': 'sol'}[tier] }",
            tier=tier, role="audit", output_tokens=index * 10,
            dispatch_index=index, task_id=TASK, outcome="failed",
        )
        if index == 2:
            assert ledger.verify() == (True, "2 record(s)")
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[1]["record"]["output_tokens"] = 999
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    assert ledger.verify()[0] is False
