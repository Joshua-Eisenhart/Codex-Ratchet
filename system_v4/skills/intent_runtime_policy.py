"""
intent_runtime_policy.py

Shared helpers for the bounded runtime intent-policy contract.

The intent-control surface may keep legacy mirrored fields for compatibility,
but execution should normalize onto one runtime policy shape before steering
runner, A1, or wiggle behavior.
"""

from __future__ import annotations

from typing import Any


RUNTIME_POLICY_SCHEMA = "INTENT_RUNTIME_POLICY_v1"
_BOUNDED_INT_KEYS = (
    "max_candidates_per_concept",
    "max_alternatives_per_primary",
)


def _copy_dict(value: Any) -> dict[str, Any]:
    return dict(value or {})


def _copy_list(value: Any) -> list[Any]:
    return list(value or [])


def _copy_list_if_present(value: Any) -> list[Any] | None:
    if isinstance(value, list):
        return list(value)
    return None


def _prefer_bounded_int(primary: Any, secondary: Any) -> int | None:
    values = [val for val in (primary, secondary) if isinstance(val, int) and val >= 0]
    if not values:
        return None
    return min(values)


def build_runtime_policy(
    focus_terms: list[str],
    non_negotiables: list[dict[str, Any]],
    *,
    executable_focus_terms: list[str] | None = None,
    executable_non_negotiables: list[dict[str, Any]] | None = None,
    executable_focus_refinement_candidates: list[dict[str, Any]] | None = None,
    executable_focus_promotion_readiness: list[dict[str, Any]] | None = None,
    executable_focus_semantic_comparison: dict[str, Any] | None = None,
) -> dict[str, Any]:
    executable_focus_terms = list(executable_focus_terms or focus_terms)
    executable_non_negotiables = list(executable_non_negotiables or non_negotiables)
    executable_focus_refinement_candidates = list(
        executable_focus_refinement_candidates or []
    )
    executable_focus_promotion_readiness = list(
        executable_focus_promotion_readiness or []
    )
    executable_focus_semantic_comparison = _copy_dict(
        executable_focus_semantic_comparison
    )
    non_negotiable_labels = [
        str(item.get("label", "")).strip()
        for item in executable_non_negotiables
        if str(item.get("label", "")).strip()
    ]
    concept_selection = {
        "mode": "focus-term-gate-then-reorder",
        "focus_terms": list(focus_terms),
        "gating_focus_terms": list(executable_focus_terms),
        "min_focus_score": 1,
        "gate_min_concepts": 2,
        "fallback_mode": "reorder_only",
        "respect_explicit_targets": True,
    }
    candidate_policy = {
        "mode": "suppress-off-focus-term-defs",
        "apply_on_modes": ["focus-term-gated", "reorder_only"],
        "min_focus_score": 1,
        "suppress_term_defs_without_focus": True,
        "respect_explicit_targets": True,
        "fallback_mode": "keep_non_term_candidates",
    }
    alternative_policy = {
        "mode": "cap_alternatives_per_primary",
        "apply_on_modes": ["focus-term-gated", "reorder_only"],
        "max_alternatives_per_primary": 2,
        "respect_explicit_targets": False,
        "rationale": "Keep the mandatory graveyard-seeking fail set bounded while intent steering is active.",
    }
    bias_config = {
        "intent_focus_terms": list(executable_focus_terms),
        "intent_non_negotiables": non_negotiable_labels,
        "intent_surface_class": "DERIVED_A2",
        "max_alternatives_per_primary": alternative_policy["max_alternatives_per_primary"],
    }
    return {
        "schema": RUNTIME_POLICY_SCHEMA,
        "focus_terms": list(focus_terms),
        "steering_focus_terms": list(executable_focus_terms),
        "executable_focus_terms": list(executable_focus_terms),
        "executable_non_negotiables": non_negotiable_labels,
        "executable_focus_refinement_candidates": executable_focus_refinement_candidates,
        "executable_focus_promotion_readiness": executable_focus_promotion_readiness,
        "executable_focus_semantic_comparison": executable_focus_semantic_comparison,
        "focus_term_quality": [],
        "steering_quality": {
            "status": "legacy_implicit",
            "downgrade_applied": False,
            "reasons": [],
            "descriptive_focus_term_count": len(focus_terms),
            "steering_focus_term_count": len(executable_focus_terms),
            "top_weak_terms": [],
        },
        "concept_selection": concept_selection,
        "candidate_policy": candidate_policy,
        "alternative_policy": alternative_policy,
        "bias_config": bias_config,
    }


def normalize_intent_runtime_policy(intent_control: dict[str, Any] | None) -> dict[str, Any]:
    control = ((intent_control or {}).get("control", {}) or {})
    runtime_policy = _copy_dict(control.get("runtime_policy"))
    legacy_concept_selection = _copy_dict(control.get("concept_selection"))
    legacy_candidate_policy = _copy_dict(control.get("candidate_policy"))
    legacy_alternative_policy = _copy_dict(control.get("alternative_policy"))
    legacy_bias_config = _copy_dict(control.get("bias_config"))

    focus_terms = _copy_list(
        runtime_policy.get("focus_terms")
        or legacy_concept_selection.get("focus_terms")
        or control.get("focus_terms")
        or legacy_bias_config.get("intent_focus_terms")
    )
    runtime_concept_selection = _copy_dict(runtime_policy.get("concept_selection"))
    explicit_executable_focus_terms = (
        _copy_list_if_present(runtime_policy.get("executable_focus_terms"))
        or _copy_list_if_present(runtime_concept_selection.get("gating_focus_terms"))
        or _copy_list_if_present(runtime_policy.get("steering_focus_terms"))
    )
    executable_focus_terms = (
        explicit_executable_focus_terms
        if explicit_executable_focus_terms is not None
        else list(focus_terms)
    )
    explicit_steering_focus_terms = _copy_list_if_present(runtime_policy.get("steering_focus_terms"))
    steering_focus_terms = (
        explicit_steering_focus_terms
        if explicit_steering_focus_terms is not None
        else list(executable_focus_terms)
    )
    focus_term_quality = _copy_list(runtime_policy.get("focus_term_quality"))
    executable_focus_graph_metrics = _copy_dict(
        runtime_policy.get("executable_focus_graph_metrics")
    )
    executable_focus_refinement_candidates = _copy_list(
        runtime_policy.get("executable_focus_refinement_candidates")
    )
    executable_focus_promotion_readiness = _copy_list(
        runtime_policy.get("executable_focus_promotion_readiness")
    )
    executable_focus_semantic_comparison = _copy_dict(
        runtime_policy.get("executable_focus_semantic_comparison")
    )
    steering_quality = _copy_dict(
        runtime_policy.get("steering_quality")
        or {
            "status": "legacy_implicit",
            "downgrade_applied": False,
            "reasons": [],
            "descriptive_focus_term_count": len(focus_terms),
            "steering_focus_term_count": len(steering_focus_terms),
            "top_weak_terms": [],
        }
    )
    explicit_executable_non_negotiables = _copy_list_if_present(
        runtime_policy.get("executable_non_negotiables")
    )
    executable_non_negotiables = (
        explicit_executable_non_negotiables
        if explicit_executable_non_negotiables is not None
        else _copy_list(legacy_bias_config.get("intent_non_negotiables"))
    )

    concept_selection = _copy_dict(
        runtime_policy.get("concept_selection") or legacy_concept_selection
    )
    candidate_policy = _copy_dict(
        runtime_policy.get("candidate_policy") or legacy_candidate_policy
    )
    alternative_policy = _copy_dict(
        runtime_policy.get("alternative_policy") or legacy_alternative_policy
    )
    bias_config = _copy_dict(runtime_policy.get("bias_config") or legacy_bias_config)

    if focus_terms:
        concept_selection.setdefault("focus_terms", list(focus_terms))
    if executable_focus_terms:
        concept_selection.setdefault("gating_focus_terms", list(executable_focus_terms))
        bias_config["intent_focus_terms"] = list(executable_focus_terms)
    elif focus_terms:
        bias_config.setdefault("intent_focus_terms", list(focus_terms))
    if executable_non_negotiables:
        bias_config.setdefault("intent_non_negotiables", list(executable_non_negotiables))
    bias_config.setdefault("intent_surface_class", "DERIVED_A2")

    alt_cap = _prefer_bounded_int(
        alternative_policy.get("max_alternatives_per_primary"),
        bias_config.get("max_alternatives_per_primary"),
    )
    if alt_cap is not None:
        alternative_policy["max_alternatives_per_primary"] = alt_cap
        bias_config["max_alternatives_per_primary"] = alt_cap

    concept_runtime = _copy_dict(
        runtime_policy.get("concept_selection_runtime") or control.get("concept_selection_runtime")
    )
    if concept_runtime:
        concept_selection["runtime"] = concept_runtime

    normalized = {
        "schema": str(runtime_policy.get("schema") or RUNTIME_POLICY_SCHEMA),
        "focus_terms": list(focus_terms),
        "steering_focus_terms": list(steering_focus_terms),
        "executable_focus_terms": list(executable_focus_terms),
        "executable_non_negotiables": list(executable_non_negotiables),
        "executable_focus_graph_metrics": executable_focus_graph_metrics,
        "executable_focus_refinement_candidates": executable_focus_refinement_candidates,
        "executable_focus_promotion_readiness": executable_focus_promotion_readiness,
        "executable_focus_semantic_comparison": executable_focus_semantic_comparison,
        "focus_term_quality": focus_term_quality,
        "steering_quality": steering_quality,
        "concept_selection": concept_selection,
        "candidate_policy": candidate_policy,
        "alternative_policy": alternative_policy,
        "bias_config": bias_config,
    }
    if concept_runtime:
        normalized["concept_selection_runtime"] = concept_runtime
    return normalized


def merge_execution_bias(
    base_bias_config: dict[str, Any] | None,
    overlay_bias_config: dict[str, Any] | None,
) -> dict[str, Any]:
    base = _copy_dict(base_bias_config)
    overlay = _copy_dict(overlay_bias_config)
    merged = dict(base)

    base_allowed = _copy_list(base.get("allowed_kinds"))
    overlay_allowed = _copy_list(overlay.get("allowed_kinds"))
    if base_allowed and overlay_allowed:
        allowed_set = set(overlay_allowed)
        merged["allowed_kinds"] = [kind for kind in base_allowed if kind in allowed_set]
    elif overlay_allowed:
        merged["allowed_kinds"] = overlay_allowed
    elif base_allowed:
        merged["allowed_kinds"] = base_allowed

    allowed_filter = set(merged.get("allowed_kinds", []) or [])
    preferred_order = _copy_list(overlay.get("preferred_kind_order"))
    if not preferred_order:
        preferred_order = _copy_list(base.get("preferred_kind_order"))
    if preferred_order:
        filtered_order = [
            kind for kind in preferred_order if not allowed_filter or kind in allowed_filter
        ]
        if allowed_filter:
            for source_order in (base.get("preferred_kind_order"), overlay.get("preferred_kind_order")):
                for kind in _copy_list(source_order):
                    if kind in allowed_filter and kind not in filtered_order:
                        filtered_order.append(kind)
            for kind in merged.get("allowed_kinds", []):
                if kind not in filtered_order:
                    filtered_order.append(kind)
        merged["preferred_kind_order"] = filtered_order

    for bounded_key in _BOUNDED_INT_KEYS:
        bounded_value = _prefer_bounded_int(base.get(bounded_key), overlay.get(bounded_key))
        if bounded_value is not None:
            merged[bounded_key] = bounded_value
        elif bounded_key in overlay:
            merged[bounded_key] = overlay[bounded_key]

    if (
        "suppress_alternatives" in base
        or "suppress_alternatives" in overlay
        or base.get("suppress_alternatives", False)
        or overlay.get("suppress_alternatives", False)
    ):
        merged["suppress_alternatives"] = bool(
            base.get("suppress_alternatives", False) or overlay.get("suppress_alternatives", False)
        )

    for key, value in overlay.items():
        if key in {"allowed_kinds", "preferred_kind_order", "suppress_alternatives", *_BOUNDED_INT_KEYS}:
            continue
        merged[key] = value

    return merged
