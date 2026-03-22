"""Smoke tests for normalized runtime intent-policy helpers."""

from __future__ import annotations

from system_v4.skills.intent_runtime_policy import (
    build_runtime_policy,
    merge_execution_bias,
    normalize_intent_runtime_policy,
)


def test_intent_runtime_policy_smoke() -> None:
    runtime_policy = build_runtime_policy(
        ["intent", "context"],
        [{"label": "intent_first_class"}],
    )
    assert runtime_policy["schema"] == "INTENT_RUNTIME_POLICY_v1"
    assert runtime_policy["steering_focus_terms"] == ["intent", "context"]
    assert runtime_policy["executable_focus_terms"] == ["intent", "context"]
    assert runtime_policy["executable_non_negotiables"] == ["intent_first_class"]
    assert runtime_policy["bias_config"]["max_alternatives_per_primary"] == 2

    legacy_intent_control = {
        "control": {
            "focus_terms": ["intent"],
            "concept_selection": {
                "mode": "focus-term-gate-then-reorder",
                "gate_min_concepts": 2,
            },
            "candidate_policy": {
                "mode": "suppress-off-focus-term-defs",
            },
            "alternative_policy": {
                "mode": "cap_alternatives_per_primary",
                "max_alternatives_per_primary": 2,
            },
            "bias_config": {
                "intent_focus_terms": ["intent"],
                "max_alternatives_per_primary": 3,
            },
        }
    }
    normalized = normalize_intent_runtime_policy(legacy_intent_control)
    assert normalized["focus_terms"] == ["intent"]
    assert normalized["steering_focus_terms"] == ["intent"]
    assert normalized["executable_focus_terms"] == ["intent"]
    assert normalized["alternative_policy"]["max_alternatives_per_primary"] == 2
    assert normalized["bias_config"]["max_alternatives_per_primary"] == 2

    merged = merge_execution_bias(
        {
            "allowed_kinds": ["MATH_DEF", "TERM_DEF"],
            "preferred_kind_order": ["MATH_DEF", "TERM_DEF"],
            "max_alternatives_per_primary": 2,
        },
        {
            "allowed_kinds": ["TERM_DEF", "LABEL_DEF"],
            "preferred_kind_order": ["LABEL_DEF", "TERM_DEF"],
            "max_alternatives_per_primary": 3,
            "suppress_alternatives": True,
        },
    )
    assert merged["allowed_kinds"] == ["TERM_DEF"]
    assert merged["preferred_kind_order"] == ["TERM_DEF"]
    assert merged["max_alternatives_per_primary"] == 2
    assert merged["suppress_alternatives"] is True

    print("PASS: test_intent_runtime_policy_smoke")


if __name__ == "__main__":
    test_intent_runtime_policy_smoke()
