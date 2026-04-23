"""
wiggle_lane_runner.py — Sequential multi-lane A1 wrapper

This is the smallest honest wiggle surface in the current repo:
- runs multiple A1 lanes sequentially
- keeps each lane on ephemeral routing state
- emits a comparison/merge envelope plus one merged strategy packet

It does not claim parallel or subagent execution yet.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Dict, List, Optional

from system_v4.skills.a1_brain import A1Brain, A1StrategyPacket, A1WigglePacket
from system_v4.skills.intent_runtime_policy import (
    merge_execution_bias,
    normalize_intent_runtime_policy,
)


DEFAULT_LANE_CONFIGS: List[Dict[str, Any]] = [
    {
        "lane_id": "literal-math",
        "bias_config": {
            "allowed_kinds": ["MATH_DEF", "TERM_DEF"],
            "preferred_kind_order": ["MATH_DEF", "TERM_DEF", "LABEL_DEF"],
            "max_candidates_per_concept": 2,
            "max_alternatives_per_primary": 3,
        },
    },
    {
        "lane_id": "term-first",
        "bias_config": {
            "allowed_kinds": ["TERM_DEF", "LABEL_DEF", "MATH_DEF"],
            "preferred_kind_order": ["TERM_DEF", "LABEL_DEF", "MATH_DEF"],
            "max_candidates_per_concept": 2,
            "max_alternatives_per_primary": 2,
        },
    },
]


def _merge_lane_bias_config(
    base_bias_config: Dict[str, Any],
    lane_specific_bias: Dict[str, Any],
) -> Dict[str, Any]:
    return merge_execution_bias(base_bias_config, lane_specific_bias)


def _candidate_signature(candidate: dict[str, Any]) -> str:
    def_fields = tuple(
        (df.get("name", ""), df.get("value_kind", ""), df.get("value", ""))
        for df in candidate.get("def_fields", [])
    )
    asserts = tuple(
        (a.get("token_class", ""), a.get("token", ""))
        for a in candidate.get("asserts", [])
    )
    requires = tuple(candidate.get("requires", []))
    source_concept_id = candidate.get("source_concept_id", "")
    return repr((
        candidate.get("item_class", ""),
        candidate.get("kind", ""),
        source_concept_id,
        def_fields,
        asserts,
        requires,
    ))


def _apply_merged_alternative_policy(
    merged_alternatives: List[dict[str, Any]],
    runtime_policy: Dict[str, Any],
    primary_identity_by_id: Dict[str, str],
) -> tuple[List[dict[str, Any]], dict[str, Any]]:
    alternative_policy = dict(runtime_policy.get("alternative_policy", {}) or {})
    report = {
        "configured_mode": alternative_policy.get("mode", ""),
        "max_alternatives_per_primary": alternative_policy.get("max_alternatives_per_primary"),
        "primaries_evaluated": 0,
        "primaries_trimmed": 0,
        "alternatives_trimmed": 0,
        "applied": False,
    }
    cap = alternative_policy.get("max_alternatives_per_primary")
    if (
        alternative_policy.get("mode") != "cap_alternatives_per_primary"
        or not isinstance(cap, int)
        or cap < 0
    ):
        return merged_alternatives, report

    kept: List[dict[str, Any]] = []
    kept_counts: Counter[str] = Counter()
    evaluated_primaries: set[str] = set()
    trimmed_primaries: set[str] = set()
    for alt in merged_alternatives:
        primary_id = str(alt.get("primary_candidate_id", "") or "")
        primary_identity = primary_identity_by_id.get(primary_id) or repr((
            alt.get("source_concept_id", ""),
            alt.get("item_class", ""),
            alt.get("kind", ""),
        ))
        if primary_identity:
            evaluated_primaries.add(primary_identity)
            if kept_counts[primary_identity] >= cap:
                report["applied"] = True
                report["alternatives_trimmed"] += 1
                trimmed_primaries.add(primary_identity)
                continue
            kept_counts[primary_identity] += 1
        kept.append(alt)

    report["primaries_evaluated"] = len(evaluated_primaries)
    report["primaries_trimmed"] = len(trimmed_primaries)
    return kept, report


def _merge_strategy_packets(
    lane_packets: List[A1StrategyPacket],
    wiggle_id: str,
    concept_ids: List[str],
    lane_configs: List[Dict[str, Any]],
    *,
    base_lane_id: Optional[str] = None,
    intent_control: Optional[Dict[str, Any]] = None,
) -> tuple[A1StrategyPacket, dict[str, Any]]:
    runtime_policy = normalize_intent_runtime_policy(intent_control)
    merged_targets: List[dict[str, Any]] = []
    merged_alternatives: List[dict[str, Any]] = []
    comparison_entries: Dict[str, dict[str, Any]] = {}
    seen_target_signatures: set[str] = set()
    seen_alt_signatures: set[str] = set()
    primary_identity_by_id: Dict[str, str] = {}

    for lane_cfg, packet in zip(lane_configs, lane_packets):
        lane_id = lane_cfg["lane_id"]
        for target in packet.targets:
            sig = _candidate_signature(target)
            entry = comparison_entries.setdefault(sig, {
                "kind": target.get("kind", ""),
                "source_concept_id": target.get("source_concept_id", ""),
                "lane_ids": [],
                "candidate_ids": [],
                "support_count": 0,
            })
            entry["lane_ids"].append(lane_id)
            entry["candidate_ids"].append(target.get("id", ""))
            entry["support_count"] += 1
            target_id = str(target.get("id", "") or "")
            if target_id:
                primary_identity_by_id[target_id] = sig
            if sig not in seen_target_signatures:
                merged_targets.append(target)
                seen_target_signatures.add(sig)
        for alt in packet.alternatives:
            sig = _candidate_signature(alt)
            if sig not in seen_alt_signatures:
                merged_alternatives.append(alt)
                seen_alt_signatures.add(sig)

    merged_alternatives, merged_alt_policy_runtime = _apply_merged_alternative_policy(
        merged_alternatives,
        runtime_policy,
        primary_identity_by_id,
    )

    merged_packet = A1StrategyPacket(
        strategy_id=f"{wiggle_id}::MERGED",
        inputs={
            "concept_ids": concept_ids,
            "lane_ids": [cfg["lane_id"] for cfg in lane_configs],
            "wiggle_id": wiggle_id,
            "base_lane_id": base_lane_id,
            "intent_control": {
                "surface_id": (intent_control or {}).get("surface_id", ""),
                "surface_hash": ((intent_control or {}).get("provenance", {}) or {}).get("surface_hash", ""),
                "focus_terms": runtime_policy.get("focus_terms", []),
                "runtime_policy": runtime_policy,
            },
        },
        targets=merged_targets,
        alternatives=merged_alternatives,
        sims={"positive": [], "negative": []},
        self_audit={
            "wiggle_id": wiggle_id,
            "lane_count": len(lane_packets),
            "candidate_count": len(merged_targets),
            "alternative_count": len(merged_alternatives),
            "intent_control_surface_id": (intent_control or {}).get("surface_id", ""),
            "alternative_policy_runtime": merged_alt_policy_runtime,
        },
    )
    merge_report = {
        "wiggle_id": wiggle_id,
        "lane_ids": [cfg["lane_id"] for cfg in lane_configs],
        "lane_packet_counts": {
            cfg["lane_id"]: {
                "targets": len(packet.targets),
                "alternatives": len(packet.alternatives),
            }
            for cfg, packet in zip(lane_configs, lane_packets)
        },
        "comparison_matrix": list(comparison_entries.values()),
        "merged_target_count": len(merged_targets),
        "merged_alternative_count": len(merged_alternatives),
        "alternative_policy_runtime": merged_alt_policy_runtime,
    }
    return merged_packet, merge_report


def build_wiggle_envelope(
    repo: str,
    brain: A1Brain,
    concept_ids: List[str],
    graph_nodes: Dict[str, Any],
    lane_configs: Optional[List[Dict[str, Any]]] = None,
    wiggle_id: Optional[str] = None,
    lane_id: Optional[str] = None,
    bias_config: Optional[Dict[str, Any]] = None,
    intent_control: Optional[Dict[str, Any]] = None,
) -> A1WigglePacket:
    lane_configs = lane_configs or deepcopy(DEFAULT_LANE_CONFIGS)
    wiggle_id = wiggle_id or "A1_WIGGLE"
    runtime_policy = normalize_intent_runtime_policy(intent_control)
    base_bias_config = merge_execution_bias(runtime_policy.get("bias_config", {}), bias_config or {})

    lane_packets: List[A1StrategyPacket] = []
    serial_counters = dict(brain._id_counters)
    aggregated_routes: Dict[str, Any] = {}

    for idx, lane_cfg in enumerate(lane_configs, start=1):
        lane_label = lane_cfg["lane_id"]
        lane_bias_config = _merge_lane_bias_config(
            base_bias_config,
            dict(lane_cfg.get("bias_config", {})),
        )

        lane_brain = A1Brain(str(brain.repo_root), eval_mode=True)
        lane_brain.term_registry = deepcopy(brain.term_registry)
        lane_brain.graveyard_terms = deepcopy(brain.graveyard_terms)
        lane_brain._id_counters = dict(serial_counters)

        packet = lane_brain.build_strategy_packet(
            concept_ids=concept_ids,
            graph_nodes=graph_nodes,
            strategy_id=f"{wiggle_id}::LANE{idx}",
            lane_id=lane_label,
            bias_config=lane_bias_config,
            intent_control=intent_control,
        )
        serial_counters = dict(lane_brain._id_counters)
        lane_packets.append(packet)

        for concept_id, route in lane_brain.routing.records.items():
            existing = aggregated_routes.get(concept_id)
            if existing is None:
                aggregated_routes[concept_id] = deepcopy(route)
                continue
            if route.route_status == "KERNEL_EXTRACTED" and existing.route_status != "KERNEL_EXTRACTED":
                aggregated_routes[concept_id] = deepcopy(route)
                existing = aggregated_routes[concept_id]
            for kid in route.kernel_candidate_ids:
                if kid not in existing.kernel_candidate_ids:
                    existing.kernel_candidate_ids.append(kid)
            for rid in route.rosetta_packet_ids:
                if rid not in existing.rosetta_packet_ids:
                    existing.rosetta_packet_ids.append(rid)

    merged_packet, merge_report = _merge_strategy_packets(
        lane_packets=lane_packets,
        wiggle_id=wiggle_id,
        concept_ids=concept_ids,
        lane_configs=lane_configs,
        base_lane_id=lane_id,
        intent_control=intent_control,
    )

    brain._id_counters = dict(serial_counters)
    if not brain.eval_mode and aggregated_routes:
        for route in aggregated_routes.values():
            brain.routing.upsert(route)
        brain.routing.save()

    return A1WigglePacket(
        wiggle_id=wiggle_id,
        lane_packets=[packet.to_dict() for packet in lane_packets],
        merge_report=merge_report,
        merged_strategy_packet=merged_packet.to_dict(),
    )
