#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _status(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def _latest_strategy_payload(run_dir: Path) -> tuple[Path | None, dict]:
    zip_dir = run_dir / "zip_packets"
    if not zip_dir.exists():
        return None, {}
    for zip_path in sorted(zip_dir.glob("*.zip"), reverse=True):
        try:
            with zipfile.ZipFile(zip_path) as zf:
                payload = json.loads(zf.read("A1_STRATEGY_v1.json").decode("utf-8"))
        except Exception:
            continue
        if isinstance(payload, dict):
            return zip_path, payload
    return None, {}


def _candidate_def_field_map(candidate: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for field in (candidate.get("def_fields", []) or []):
        if not isinstance(field, dict):
            continue
        name = str(field.get("name", "")).strip()
        if not name:
            continue
        out[name] = str(field.get("value", "")).strip()
    return out


def _is_rescue_candidate(candidate: dict) -> bool:
    field_map = _candidate_def_field_map(candidate)
    return any(
        str(field_map.get(name, "")).strip()
        for name in ("RESCUE_FROM", "RESCUE_FAILURE_MODE", "RESCUE_LIBRARY_TERM", "RESCUE_MODE")
    )


def _strategy_rescue_candidates(strategy_payload: dict) -> list[dict]:
    out: list[dict] = []
    for section in ("targets", "alternatives"):
        for item in (strategy_payload.get(section, []) or []):
            if not isinstance(item, dict) or str(item.get("kind", "")).strip() != "SIM_SPEC":
                continue
            if _is_rescue_candidate(item):
                out.append(item)
    return out


def _strategy_candidates(strategy_payload: dict) -> list[dict]:
    out: list[dict] = []
    for section in ("targets", "alternatives"):
        for item in (strategy_payload.get(section, []) or []):
            if not isinstance(item, dict) or str(item.get("kind", "")).strip() != "SIM_SPEC":
                continue
            out.append(item)
    return out


def _strategy_non_rescue_candidates(strategy_payload: dict) -> list[dict]:
    out: list[dict] = []
    for section in ("targets", "alternatives"):
        for item in (strategy_payload.get(section, []) or []):
            if not isinstance(item, dict) or str(item.get("kind", "")).strip() != "SIM_SPEC":
                continue
            if _is_rescue_candidate(item):
                continue
            out.append(item)
    return out


def _strategy_branch_lineage_fields_used(strategy_payload: dict) -> list[str]:
    out: set[str] = set()
    lineage_names = {"BRANCH_ID", "PARENT_BRANCH_ID", "FEEDBACK_REFS"}
    for item in _strategy_non_rescue_candidates(strategy_payload):
        field_map = _candidate_def_field_map(item)
        for name in lineage_names:
            if str(field_map.get(name, "")).strip():
                out.add(name.lower())
    return sorted(out)


def _strategy_branch_lineage_complete(strategy_payload: dict, required_fields: list[str]) -> bool:
    required = {str(field).strip().lower() for field in (required_fields or []) if str(field).strip()}
    if not required:
        return True
    candidates = _strategy_non_rescue_candidates(strategy_payload)
    if not candidates:
        return False
    for item in candidates:
        field_map = {key.lower(): value for key, value in _candidate_def_field_map(item).items()}
        if not all(str(field_map.get(name, "")).strip() for name in required):
            return False
    return True


def _strategy_non_rescue_branch_parentage_map(strategy_payload: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in _strategy_non_rescue_candidates(strategy_payload):
        field_map = _candidate_def_field_map(item)
        branch_id = str(field_map.get("BRANCH_ID", "")).strip()
        if not branch_id:
            continue
        out[branch_id] = str(field_map.get("PARENT_BRANCH_ID", "")).strip() or "NONE"
    return {branch_id: out[branch_id] for branch_id in sorted(out)}


def _strategy_non_rescue_root_branch_ids(strategy_payload: dict) -> list[str]:
    parentage = _strategy_non_rescue_branch_parentage_map(strategy_payload)
    return sorted([branch_id for branch_id, parent in parentage.items() if parent == "NONE"])


def _strategy_non_rescue_branch_child_counts(strategy_payload: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for parent in _strategy_non_rescue_branch_parentage_map(strategy_payload).values():
        token = str(parent).strip() or "NONE"
        counts[token] = counts.get(token, 0) + 1
    return {parent: counts[parent] for parent in sorted(counts)}


def _strategy_branch_group_map(strategy_payload: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in _strategy_candidates(strategy_payload):
        field_map = _candidate_def_field_map(item)
        branch_id = str(field_map.get("BRANCH_ID", "")).strip() or str(field_map.get("SIM_ID", "")).strip()
        branch_group = str(field_map.get("BRANCH_GROUP", "")).strip()
        if not branch_id or not branch_group:
            continue
        out[branch_id] = branch_group
    return {branch_id: out[branch_id] for branch_id in sorted(out)}


def _strategy_branch_groups_used(strategy_payload: dict) -> list[str]:
    return sorted({group for group in _strategy_branch_group_map(strategy_payload).values() if str(group).strip()})


def _strategy_branch_group_complete(strategy_payload: dict) -> bool:
    expected_branch_ids: set[str] = set()
    for item in _strategy_candidates(strategy_payload):
        field_map = _candidate_def_field_map(item)
        branch_id = str(field_map.get("BRANCH_ID", "")).strip() or str(field_map.get("SIM_ID", "")).strip()
        if branch_id:
            expected_branch_ids.add(branch_id)
    if not expected_branch_ids:
        return False
    return expected_branch_ids == set(_strategy_branch_group_map(strategy_payload).keys())


def _strategy_branch_track_map(strategy_payload: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in _strategy_candidates(strategy_payload):
        field_map = _candidate_def_field_map(item)
        branch_id = str(field_map.get("BRANCH_ID", "")).strip() or str(field_map.get("SIM_ID", "")).strip()
        branch_track = str(field_map.get("BRANCH_TRACK", "")).strip()
        if not branch_id or not branch_track:
            continue
        out[branch_id] = branch_track
    return {branch_id: out[branch_id] for branch_id in sorted(out)}


def _strategy_branch_tracks_used(strategy_payload: dict) -> list[str]:
    return sorted({track for track in _strategy_branch_track_map(strategy_payload).values() if str(track).strip()})


def _strategy_branch_track_complete(strategy_payload: dict) -> bool:
    expected_branch_ids: set[str] = set()
    for item in _strategy_candidates(strategy_payload):
        field_map = _candidate_def_field_map(item)
        branch_id = str(field_map.get("BRANCH_ID", "")).strip() or str(field_map.get("SIM_ID", "")).strip()
        if branch_id:
            expected_branch_ids.add(branch_id)
    if not expected_branch_ids:
        return False
    return expected_branch_ids == set(_strategy_branch_track_map(strategy_payload).keys())


def _strategy_non_rescue_parentage_internal_ok(strategy_payload: dict) -> bool:
    parentage = _strategy_non_rescue_branch_parentage_map(strategy_payload)
    branch_ids = set(parentage.keys())
    if not parentage:
        return False
    for parent in parentage.values():
        token = str(parent).strip() or "NONE"
        if token == "NONE":
            continue
        if token not in branch_ids:
            return False
    return True


def _strategy_rescue_linkages_used(strategy_payload: dict) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in _strategy_rescue_candidates(strategy_payload):
        linkage = str(_candidate_def_field_map(item).get("RESCUE_LINKAGE", "")).strip()
        if not linkage or linkage in seen:
            continue
        seen.add(linkage)
        out.append(linkage)
    return out


def _strategy_rescue_lineage_fields_used(strategy_payload: dict) -> list[str]:
    out: set[str] = set()
    lineage_names = {"BRANCH_ID", "PARENT_BRANCH_ID", "FEEDBACK_REFS", "RESCUE_LINKAGE"}
    for item in _strategy_rescue_candidates(strategy_payload):
        field_map = _candidate_def_field_map(item)
        for name in lineage_names:
            if str(field_map.get(name, "")).strip():
                out.add(name.lower())
    return sorted(out)


def _strategy_rescue_lineage_complete(strategy_payload: dict, required_fields: list[str]) -> bool:
    required = {str(field).strip().lower() for field in (required_fields or []) if str(field).strip()}
    if not required:
        return True
    candidates = _strategy_rescue_candidates(strategy_payload)
    if not candidates:
        return False
    for item in candidates:
        field_map = {key.lower(): value for key, value in _candidate_def_field_map(item).items()}
        if not all(str(field_map.get(name, "")).strip() for name in required):
            return False
    return True


def _family_slice_expected(campaign_summary: dict) -> bool:
    return str(campaign_summary.get("goal_source", "")).strip() == "family_slice"


def _family_slice_strategy_heads(family_slice: dict) -> list[str]:
    hints = family_slice.get("family_admissibility_hints", {}) or {}
    heads = [str(x).strip() for x in (hints.get("strategy_head_terms", []) or []) if str(x).strip()]
    if heads:
        return heads
    admissibility = family_slice.get("admissibility", {}) or {}
    return [str(x).strip() for x in (admissibility.get("executable_head", []) or []) if str(x).strip()]


def _family_slice_negative_classes(family_slice: dict) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for group_name in ("negative_emphasis_classes", "required_negative_classes"):
        for raw in (family_slice.get(group_name, []) or []):
            token = str(raw).strip().upper()
            if not token or token in seen:
                continue
            seen.add(token)
            out.append(token)
    return out


def _family_slice_required_sim_families(family_slice: dict) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    sim_hooks = family_slice.get("sim_hooks", {}) or {}
    for raw in (sim_hooks.get("required_sim_families", []) or []):
        token = str(raw).strip().upper()
        if not token or token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def _family_slice_sim_family_tiers(family_slice: dict) -> dict[str, str]:
    sim_hooks = family_slice.get("sim_hooks", {}) or {}
    raw = sim_hooks.get("sim_family_tiers", {}) or {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for family, tier in raw.items():
        family_token = str(family).strip().upper()
        tier_token = str(tier).strip().upper()
        if family_token and tier_token:
            out[family_token] = tier_token
    return out


def _family_slice_recovery_sim_families(family_slice: dict) -> list[str]:
    sim_hooks = family_slice.get("sim_hooks", {}) or {}
    raw = sim_hooks.get("recovery_sim_families", []) or []
    if not isinstance(raw, list) or not raw:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for family in raw:
        token = str(family).strip().upper()
        if not token or token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def _family_slice_rescue_source_limit(family_slice: dict) -> int:
    rescue_start = family_slice.get("rescue_start_conditions", {}) or {}
    try:
        limit = int(rescue_start.get("max_rescue_sources", 6) or 6)
    except Exception:
        limit = 6
    return max(1, limit)


def _family_slice_graveyard_negative_expansion_limit(family_slice: dict) -> int:
    rescue_start = family_slice.get("rescue_start_conditions", {}) or {}
    raw = rescue_start.get("graveyard_negative_expansion_limit", None)
    if raw in (None, ""):
        return 0
    try:
        limit = int(raw)
    except Exception:
        limit = 0
    return max(1, limit) if limit else 0


def _family_slice_lane_minimums(family_slice: dict) -> dict[str, int]:
    raw = family_slice.get("lane_minimums", {}) or {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, int] = {}
    for lane, payload in raw.items():
        lane_token = str(lane).strip()
        if not lane_token:
            continue
        try:
            min_branches = int((payload or {}).get("min_branches", 0) or 0)
        except Exception:
            min_branches = 0
        if min_branches > 0:
            out[lane_token] = min_branches
    return out


def _family_slice_branch_requirements(family_slice: dict) -> dict[str, str]:
    return {
        "primary": str(family_slice.get("primary_branch_requirement", "") or "").strip(),
        "alternative": str(family_slice.get("alternative_branch_requirement", "") or "").strip(),
        "negative": str(family_slice.get("negative_branch_requirement", "") or "").strip(),
        "rescue": str(family_slice.get("rescue_branch_requirement", "") or "").strip(),
    }


def _effective_lane_minimums(family_slice: dict, debate_mode: str) -> dict[str, int]:
    expected = _family_slice_lane_minimums(family_slice)
    if not expected:
        return {}
    mode = str(debate_mode).strip()
    if not mode:
        return {}
    return expected


def _track_token(value: str) -> str:
    token = "".join(ch if ch.isalnum() else "_" for ch in str(value).strip().upper())
    token = "_".join(part for part in token.split("_") if part)
    return token or "UNSPECIFIED"


def _family_slice_target_class_prefix(family_slice: dict) -> str:
    family_token = _track_token(
        str(family_slice.get("family_id", "") or family_slice.get("family_kind", "") or "FAMILY_SLICE")
    )
    return f"TC_FAMILY_{family_token}"


LIVE_SIM_FAMILY_OPERATOR_DEFAULTS: dict[str, list[str]] = {
    "BASELINE": ["OP_BIND_SIM"],
    "BOUNDARY_SWEEP": ["OP_REPAIR_DEF_FIELD"],
    "PERTURBATION": ["OP_MUTATE_LEXEME"],
    "COMPOSITION_STRESS": ["OP_REORDER_DEPENDENCIES"],
    "ADVERSARIAL_NEG": ["OP_NEG_SIM_EXPAND"],
}
LIVE_STRATEGY_BUDGET_DEFAULTS: dict[str, dict[str, int]] = {
    "balanced": {"max_items": 32, "max_sims": 48},
    "graveyard_first": {"max_items": 48, "max_sims": 64},
    "graveyard_recovery": {"max_items": 32, "max_sims": 48},
}
LIVE_OPERATOR_POLICY_SOURCES: list[str] = [
    "ENUM_REGISTRY_v1",
    "A1_REPAIR_OPERATOR_MAPPING_v1",
]
FAMILY_SLICE_GOAL_PROBE_SOURCES: tuple[str, ...] = (
    "family_slice_override",
    "family_slice_goal_term",
    "family_slice_component_available",
    "family_slice_component_declared",
    "family_slice_declared_available",
    "family_slice_declared_fallback",
)


SIM_TIER_ORDER: tuple[str, ...] = (
    "T0_ATOM",
    "T1_COMPOUND",
    "T2_OPERATOR",
    "T3_STRUCTURE",
    "T4_SYSTEM_SEGMENT",
    "T5_ENGINE",
    "T6_WHOLE_SYSTEM",
)


def _sim_tier_rank(tier: str) -> int:
    token = str(tier).strip().upper()
    try:
        return SIM_TIER_ORDER.index(token)
    except ValueError:
        return -1


def _family_slice_budget_for_debate_mode(family_slice: dict, debate_mode: str) -> dict[str, int]:
    mode = str(debate_mode).strip()
    defaults = LIVE_STRATEGY_BUDGET_DEFAULTS.get(mode, LIVE_STRATEGY_BUDGET_DEFAULTS["balanced"])
    budget = {"max_items": int(defaults["max_items"]), "max_sims": int(defaults["max_sims"])}
    rescue_start = family_slice.get("rescue_start_conditions", {}) or {}
    override_keys = {
        "balanced": ("balanced_max_items", "balanced_max_sims"),
        "graveyard_first": ("graveyard_first_max_items", "graveyard_first_max_sims"),
        "graveyard_recovery": ("graveyard_recovery_max_items", "graveyard_recovery_max_sims"),
    }
    keys = override_keys.get(mode)
    if not keys:
        return budget
    max_items_key, max_sims_key = keys
    raw_items = rescue_start.get(max_items_key, None)
    raw_sims = rescue_start.get(max_sims_key, None)
    if raw_items not in (None, ""):
        try:
            budget["max_items"] = max(1, int(raw_items))
        except Exception:
            pass
    if raw_sims not in (None, ""):
        try:
            budget["max_sims"] = max(1, int(raw_sims))
        except Exception:
            pass
    return budget


def build_report(*, run_dir: Path, min_graveyard_count: int = 1) -> dict:
    summary_path = run_dir / "summary.json"
    campaign_path = run_dir / "campaign_summary.json"
    report_path = run_dir / "reports" / "autoratchet_campaign_summary.json"
    summary = _read_json(summary_path)
    campaign_summary = _read_json(campaign_path) or _read_json(report_path)

    state_metrics = campaign_summary.get("state_metrics", {}) if isinstance(campaign_summary.get("state_metrics", {}), dict) else {}
    steps_completed = int(summary.get("steps_completed", 0) or 0)
    steps_executed = int(campaign_summary.get("steps_executed", 0) or 0)
    graveyard_count = int(state_metrics.get("killed_unique_count", 0) or 0)
    sim_registry_count = int(state_metrics.get("sim_registry_count", 0) or 0)
    canonical_term_count = int(state_metrics.get("canonical_term_count", 0) or 0)
    zip_packet_count = len(list((run_dir / "zip_packets").glob("*.zip"))) if (run_dir / "zip_packets").exists() else 0
    latest_zip_path, latest_strategy = _latest_strategy_payload(run_dir)
    family_slice_expected = _family_slice_expected(campaign_summary)
    goal_source = str(campaign_summary.get("goal_source", "") or "").strip()
    planning_mode = str(campaign_summary.get("planning_mode", "") or "").strip()
    legacy_goal_profile_mode = goal_source != "family_slice"
    compatibility_goal_profile = str(campaign_summary.get("compatibility_goal_profile", "") or "").strip()
    family_slice_id = str(campaign_summary.get("family_slice_id", "") or "").strip()
    family_slice_json_raw = str(campaign_summary.get("family_slice_json", "") or "").strip()
    family_slice_json_path = Path(family_slice_json_raw).expanduser().resolve() if family_slice_json_raw else None
    family_slice = _read_json(family_slice_json_path) if family_slice_json_path else {}
    strategy_inputs = latest_strategy.get("inputs", {}) if isinstance(latest_strategy.get("inputs", {}), dict) else {}
    strategy_self_audit = (
        latest_strategy.get("self_audit", {}) if isinstance(latest_strategy.get("self_audit", {}), dict) else {}
    )
    strategy_budget = latest_strategy.get("budget", {}) if isinstance(latest_strategy.get("budget", {}), dict) else {}
    expected_lanes = sorted(
        {str(x).strip() for x in (family_slice.get("required_lanes", []) or []) if str(x).strip()}
    )
    visible_lanes = sorted(
        {str(x).strip() for x in (strategy_self_audit.get("family_slice_required_lanes", []) or []) if str(x).strip()}
    )
    expected_heads = sorted(_family_slice_strategy_heads(family_slice))
    visible_heads = sorted(
        {str(x).strip() for x in (strategy_self_audit.get("family_slice_strategy_head_terms", []) or []) if str(x).strip()}
    )
    expected_negative_classes = sorted(_family_slice_negative_classes(family_slice))
    visible_negative_classes = sorted(
        {
            str(x).strip().upper()
            for x in (strategy_self_audit.get("family_slice_required_negative_classes", []) or [])
            if str(x).strip()
        }
    )
    expected_math_surface_terms = sorted(
        {
            str(x).strip()
            for x in (((family_slice.get("term_math_surfaces", {}) or {}).keys()) if isinstance(family_slice.get("term_math_surfaces", {}), dict) else [])
            if str(x).strip()
        }
    )
    visible_math_surface_terms = sorted(
        {
            str(x).strip()
            for x in (strategy_self_audit.get("family_slice_math_surface_terms", []) or [])
            if str(x).strip()
        }
    )
    expected_target_class_prefix = _family_slice_target_class_prefix(family_slice) if family_slice_expected else ""
    visible_target_class_prefix = str(strategy_self_audit.get("family_slice_target_class_prefix", "") or "").strip()
    visible_strategy_target_class = str(strategy_self_audit.get("strategy_target_class", "") or "").strip()
    visible_graveyard_negative_classes = sorted(
        {
            str(x).strip().upper()
            for x in (strategy_self_audit.get("graveyard_negative_classes_used", []) or [])
            if str(x).strip()
        }
    )
    expected_probe_terms = sorted(
        {
            str(x).strip()
            for x in (((family_slice.get("sim_hooks", {}) or {}).get("required_probe_terms", []) or []))
            if str(x).strip()
        }
    )
    visible_debate_mode = str(strategy_self_audit.get("debate_mode", "") or "").strip()
    expected_lane_minimums = _family_slice_lane_minimums(family_slice)
    expected_effective_lane_minimums = _effective_lane_minimums(family_slice, visible_debate_mode) if family_slice_expected else {}
    expected_branch_requirements = _family_slice_branch_requirements(family_slice)
    expected_lineage_requirements = sorted(
        {str(x).strip() for x in (family_slice.get("lineage_requirements", []) or []) if str(x).strip()}
    )
    expected_branch_lineage_requirements = sorted(
        {token for token in expected_lineage_requirements if token != "rescue_linkage"}
    )
    expected_rescue_lineage_required = bool(family_slice.get("rescue_lineage_required", False))
    expected_sim_families = _family_slice_required_sim_families(family_slice)
    expected_sim_family_tiers = _family_slice_sim_family_tiers(family_slice)
    expected_recovery_sim_families = _family_slice_recovery_sim_families(family_slice)
    expected_rescue_source_limit = _family_slice_rescue_source_limit(family_slice)
    expected_graveyard_negative_expansion_limit = _family_slice_graveyard_negative_expansion_limit(family_slice)
    expected_graveyard_negative_classes = (
        expected_negative_classes[:expected_graveyard_negative_expansion_limit]
        if expected_graveyard_negative_expansion_limit > 0
        else expected_negative_classes
    )
    expected_budget = _family_slice_budget_for_debate_mode(family_slice, visible_debate_mode) if visible_debate_mode else {}
    expected_probe_overrides = {
        str(term).strip(): str(probe_term).strip()
        for term, probe_term in (((family_slice.get("sim_hooks", {}) or {}).get("probe_term_overrides", {}) or {}).items())
        if str(term).strip() and str(probe_term).strip()
    }
    expected_term_sim_tiers = {
        str(term).strip(): str(tier).strip().upper()
        for term, tier in (((family_slice.get("sim_hooks", {}) or {}).get("term_sim_tiers", {}) or {}).items())
        if str(term).strip() and str(tier).strip()
    }
    expected_tier_floor = str(((family_slice.get("sim_hooks", {}) or {}).get("expected_tier_floor", "") or "")).strip().upper()
    family_slice_run_mode = str(family_slice.get("run_mode", "") or "").strip()
    visible_goal_term = str(strategy_self_audit.get("goal_term", "") or "").strip()
    visible_goal_probe_term = str(strategy_self_audit.get("goal_probe_term", "") or "").strip()
    visible_goal_probe_source = str(strategy_self_audit.get("goal_probe_source", "") or "").strip()
    visible_goal_sim_tier = str(strategy_self_audit.get("goal_sim_tier", "") or "").strip().upper()
    visible_recovery_sim_families = [
        str(x).strip().upper()
        for x in (strategy_self_audit.get("family_slice_recovery_sim_families", []) or [])
        if str(x).strip()
    ]
    visible_rescue_sim_families_used = [
        str(x).strip().upper()
        for x in (strategy_self_audit.get("rescue_sim_families_used", []) or [])
        if str(x).strip()
    ]
    visible_rescue_linkages_used = _strategy_rescue_linkages_used(latest_strategy)
    visible_rescue_lineage_fields = _strategy_rescue_lineage_fields_used(latest_strategy)
    rescue_lineage_complete = _strategy_rescue_lineage_complete(latest_strategy, expected_lineage_requirements)
    visible_rescue_branch_count = len(_strategy_rescue_candidates(latest_strategy))
    visible_rescue_source_limit = int(strategy_self_audit.get("family_slice_rescue_source_limit", 0) or 0)
    visible_graveyard_negative_expansion_limit = int(
        strategy_self_audit.get("family_slice_graveyard_negative_expansion_limit", 0) or 0
    )
    visible_budget_max_items = int(strategy_budget.get("max_items", 0) or 0)
    visible_budget_max_sims = int(strategy_budget.get("max_sims", 0) or 0)
    visible_family_slice_budget_max_items = int(strategy_self_audit.get("family_slice_budget_max_items", 0) or 0)
    visible_family_slice_budget_max_sims = int(strategy_self_audit.get("family_slice_budget_max_sims", 0) or 0)
    visible_family_slice_budget_source = str(strategy_self_audit.get("family_slice_budget_source", "") or "").strip()
    visible_rescue_source_count = int(strategy_self_audit.get("rescue_source_count", 0) or 0)
    visible_sim_families = [
        str(x).strip().upper()
        for x in (strategy_self_audit.get("sim_families_used", []) or [])
        if str(x).strip()
    ]
    visible_lane_minimums_raw = strategy_self_audit.get("family_slice_lane_minimums", {})
    visible_lane_minimums = {}
    if isinstance(visible_lane_minimums_raw, dict):
        for lane, value in visible_lane_minimums_raw.items():
            lane_token = str(lane).strip()
            if not lane_token:
                continue
            try:
                visible_lane_minimums[lane_token] = int(value or 0)
            except Exception:
                continue
    visible_branch_requirements_raw = strategy_self_audit.get("family_slice_branch_requirements", {})
    visible_branch_requirements = {}
    if isinstance(visible_branch_requirements_raw, dict):
        for key, value in visible_branch_requirements_raw.items():
            key_token = str(key).strip()
            if not key_token:
                continue
            visible_branch_requirements[key_token] = str(value or "").strip()
    visible_lineage_requirements = sorted(
        {
            str(x).strip()
            for x in (strategy_self_audit.get("family_slice_lineage_requirements", []) or [])
            if str(x).strip()
        }
    )
    visible_branch_lineage_fields = _strategy_branch_lineage_fields_used(latest_strategy)
    branch_lineage_complete = _strategy_branch_lineage_complete(latest_strategy, expected_branch_lineage_requirements)
    visible_non_rescue_branch_count = len(_strategy_non_rescue_candidates(latest_strategy))
    actual_branch_parentage_map = _strategy_non_rescue_branch_parentage_map(latest_strategy)
    actual_root_branch_ids = _strategy_non_rescue_root_branch_ids(latest_strategy)
    actual_branch_child_counts = _strategy_non_rescue_branch_child_counts(latest_strategy)
    branch_parentage_internal_ok = _strategy_non_rescue_parentage_internal_ok(latest_strategy)
    actual_branch_group_map = _strategy_branch_group_map(latest_strategy)
    actual_branch_groups_used = _strategy_branch_groups_used(latest_strategy)
    branch_group_complete = _strategy_branch_group_complete(latest_strategy)
    actual_branch_track_map = _strategy_branch_track_map(latest_strategy)
    actual_branch_tracks_used = _strategy_branch_tracks_used(latest_strategy)
    branch_track_complete = _strategy_branch_track_complete(latest_strategy)
    visible_branch_parentage_map_raw = strategy_self_audit.get("branch_parentage_map", {})
    visible_branch_parentage_map = {}
    if isinstance(visible_branch_parentage_map_raw, dict):
        for branch_id, parent_id in visible_branch_parentage_map_raw.items():
            branch_token = str(branch_id).strip()
            if not branch_token:
                continue
            visible_branch_parentage_map[branch_token] = str(parent_id).strip() or "NONE"
    visible_branch_group_map_raw = strategy_self_audit.get("branch_group_map", {})
    visible_branch_group_map = {}
    if isinstance(visible_branch_group_map_raw, dict):
        for branch_id, branch_group in visible_branch_group_map_raw.items():
            branch_token = str(branch_id).strip()
            group_token = str(branch_group).strip()
            if not branch_token or not group_token:
                continue
            visible_branch_group_map[branch_token] = group_token
    visible_branch_groups_used = sorted(
        {
            str(x).strip()
            for x in (strategy_self_audit.get("branch_groups_used", []) or [])
            if str(x).strip()
        }
    )
    visible_branch_track_map_raw = strategy_self_audit.get("branch_track_map", {})
    visible_branch_track_map = {}
    if isinstance(visible_branch_track_map_raw, dict):
        for branch_id, branch_track in visible_branch_track_map_raw.items():
            branch_token = str(branch_id).strip()
            track_token = str(branch_track).strip()
            if not branch_token or not track_token:
                continue
            visible_branch_track_map[branch_token] = track_token
    visible_branch_tracks_used = sorted(
        {
            str(x).strip()
            for x in (strategy_self_audit.get("branch_tracks_used", []) or [])
            if str(x).strip()
        }
    )
    visible_root_branch_ids = sorted(
        {
            str(x).strip()
            for x in (strategy_self_audit.get("root_branch_ids", []) or [])
            if str(x).strip()
        }
    )
    visible_branch_child_counts_raw = strategy_self_audit.get("branch_child_counts", {})
    visible_branch_child_counts = {}
    if isinstance(visible_branch_child_counts_raw, dict):
        for parent_id, count in visible_branch_child_counts_raw.items():
            parent_token = str(parent_id).strip() or "NONE"
            try:
                visible_branch_child_counts[parent_token] = int(count or 0)
            except Exception:
                continue
    visible_rescue_lineage_required = bool(strategy_self_audit.get("family_slice_rescue_lineage_required", False))
    visible_lane_branch_counts_raw = strategy_self_audit.get("lane_branch_counts", {})
    visible_lane_branch_counts = {}
    if isinstance(visible_lane_branch_counts_raw, dict):
        for lane, value in visible_lane_branch_counts_raw.items():
            lane_token = str(lane).strip()
            if not lane_token:
                continue
            try:
                visible_lane_branch_counts[lane_token] = int(value or 0)
            except Exception:
                continue
    visible_sim_family_tier_map_raw = strategy_self_audit.get("sim_family_tier_map", {})
    visible_sim_family_tier_map = {}
    if isinstance(visible_sim_family_tier_map_raw, dict):
        for family, tiers in visible_sim_family_tier_map_raw.items():
            family_token = str(family).strip().upper()
            if not family_token:
                continue
            values = []
            for tier in (tiers or []):
                token = str(tier).strip().upper()
                if token:
                    values.append(token)
            visible_sim_family_tier_map[family_token] = sorted({token for token in values})
    visible_sim_family_operator_map_raw = strategy_self_audit.get("sim_family_operator_map", {})
    visible_sim_family_operator_map = {}
    if isinstance(visible_sim_family_operator_map_raw, dict):
        for family, operators in visible_sim_family_operator_map_raw.items():
            family_token = str(family).strip().upper()
            if not family_token:
                continue
            values = []
            for op in (operators or []):
                token = str(op).strip().upper()
                if token:
                    values.append(token)
            visible_sim_family_operator_map[family_token] = sorted({token for token in values})
    visible_operator_policy_sources = sorted(
        {
            str(x).strip()
            for x in (strategy_self_audit.get("operator_policy_sources", []) or [])
            if str(x).strip()
        }
    )
    goal_negative_class = str(strategy_self_audit.get("goal_negative_class", "") or "").strip().upper()

    checks = [
        {
            "check_id": "AUTORATCHET_SUMMARY_PRESENT",
            "status": _status(bool(summary)),
            "detail": f"summary_present={bool(summary)}",
        },
        {
            "check_id": "AUTORATCHET_CAMPAIGN_SUMMARY_PRESENT",
            "status": _status(bool(campaign_summary)),
            "detail": f"campaign_summary_present={bool(campaign_summary)}",
        },
        {
            "check_id": "AUTORATCHET_STEPS_EXECUTED",
            "status": _status(steps_executed >= 1),
            "detail": f"steps_executed={steps_executed}",
        },
        {
            "check_id": "AUTORATCHET_STEP_COUNTS_CONSISTENT",
            "status": _status(steps_completed == steps_executed),
            "detail": f"summary_steps_completed={steps_completed} campaign_steps_executed={steps_executed}",
        },
        {
            "check_id": "AUTORATCHET_ZIP_PACKETS_PRESENT",
            "status": _status(zip_packet_count >= 1),
            "detail": f"zip_packet_count={zip_packet_count}",
        },
        {
            "check_id": "AUTORATCHET_BRANCH_PRESSURE_VISIBLE",
            "status": _status(sim_registry_count >= 1),
            "detail": f"sim_registry_count={sim_registry_count}",
        },
        {
            "check_id": "AUTORATCHET_GRAVEYARD_FILL_VISIBLE",
            "status": _status(graveyard_count >= int(min_graveyard_count)),
            "detail": f"graveyard_count={graveyard_count} min_required={int(min_graveyard_count)}",
        },
    ]
    if family_slice_expected:
        checks.extend(
            [
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_JSON_PRESENT",
                    "status": _status(bool(family_slice_json_path and family_slice_json_path.exists())),
                    "detail": f"family_slice_json={family_slice_json_raw}",
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_ID_PRESENT",
                    "status": _status(bool(family_slice_id)),
                    "detail": f"family_slice_id={family_slice_id}",
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_ID_MATCH",
                    "status": _status(bool(family_slice_id) and family_slice_id == str(family_slice.get('slice_id', '') or '').strip()),
                    "detail": (
                        f"campaign_family_slice_id={family_slice_id} "
                        f"loaded_family_slice_id={str(family_slice.get('slice_id', '') or '').strip()}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_LATEST_STRATEGY_PRESENT",
                    "status": _status(bool(latest_zip_path and latest_strategy)),
                    "detail": f"latest_zip_path={str(latest_zip_path) if latest_zip_path else ''}",
                },
                {
                    "check_id": "AUTORATCHET_STRATEGY_FAMILY_SLICE_ID_MATCH",
                    "status": _status(bool(family_slice_id) and str(strategy_inputs.get("family_slice_id", "") or "").strip() == family_slice_id),
                    "detail": (
                        f"strategy_family_slice_id={str(strategy_inputs.get('family_slice_id', '') or '').strip()} "
                        f"campaign_family_slice_id={family_slice_id}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_LANES_VISIBLE",
                    "status": _status(bool(expected_lanes) and set(expected_lanes).issubset(set(visible_lanes))),
                    "detail": f"expected_lanes={expected_lanes} visible_lanes={visible_lanes}",
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_HEAD_VISIBLE",
                    "status": _status(bool(expected_heads) and set(expected_heads).issubset(set(visible_heads))),
                    "detail": f"expected_heads={expected_heads} visible_heads={visible_heads}",
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_NEGATIVE_CLASSES_VISIBLE",
                    "status": _status(bool(expected_negative_classes) and set(expected_negative_classes).issubset(set(visible_negative_classes))),
                    "detail": (
                        f"expected_negative_classes={expected_negative_classes} "
                        f"visible_negative_classes={visible_negative_classes}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_GOAL_NEGATIVE_CLASS_VISIBLE",
                    "status": _status(bool(goal_negative_class) and goal_negative_class in set(expected_negative_classes)),
                    "detail": (
                        f"goal_negative_class={goal_negative_class} "
                        f"expected_negative_classes={expected_negative_classes}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_MATH_SURFACES_VISIBLE",
                    "status": _status(not expected_math_surface_terms or set(expected_math_surface_terms).issubset(set(visible_math_surface_terms))),
                    "detail": (
                        f"expected_math_surface_terms={expected_math_surface_terms} "
                        f"visible_math_surface_terms={visible_math_surface_terms}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_TARGET_CLASS_VISIBLE",
                    "status": _status(
                        bool(expected_target_class_prefix)
                        and visible_target_class_prefix == expected_target_class_prefix
                        and visible_strategy_target_class.startswith(expected_target_class_prefix)
                    ),
                    "detail": (
                        f"expected_target_class_prefix={expected_target_class_prefix} "
                        f"visible_target_class_prefix={visible_target_class_prefix} "
                        f"visible_strategy_target_class={visible_strategy_target_class}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_GRAVEYARD_NEGATIVE_CLASSES_VISIBLE",
                    "status": _status(
                        family_slice_run_mode != "GRAVEYARD_VALIDITY"
                        or set(expected_graveyard_negative_classes).issubset(set(visible_graveyard_negative_classes))
                    ),
                    "detail": (
                        f"family_slice_run_mode={family_slice_run_mode} "
                        f"expected_graveyard_negative_classes={expected_graveyard_negative_classes} "
                        f"visible_graveyard_negative_classes={visible_graveyard_negative_classes}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_GRAVEYARD_NEGATIVE_LIMIT_VISIBLE",
                    "status": _status(
                        family_slice_run_mode != "GRAVEYARD_VALIDITY"
                        or (
                            visible_graveyard_negative_expansion_limit == expected_graveyard_negative_expansion_limit
                            and (
                                expected_graveyard_negative_expansion_limit == 0
                                or len(visible_graveyard_negative_classes) <= expected_graveyard_negative_expansion_limit
                            )
                        )
                    ),
                    "detail": (
                        f"family_slice_run_mode={family_slice_run_mode} "
                        f"expected_graveyard_negative_expansion_limit={expected_graveyard_negative_expansion_limit} "
                        f"visible_graveyard_negative_expansion_limit={visible_graveyard_negative_expansion_limit} "
                        f"visible_graveyard_negative_classes={visible_graveyard_negative_classes}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_PROBE_TERMS_DECLARED",
                    "status": _status(bool(expected_probe_terms)),
                    "detail": (
                        f"required_probe_terms={expected_probe_terms}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_LANE_MINIMUMS_VISIBLE",
                    "status": _status(
                        not expected_lane_minimums
                        or (
                            visible_lane_minimums == expected_lane_minimums
                            and all(lane in visible_lane_branch_counts for lane in expected_lane_minimums)
                        )
                    ),
                    "detail": (
                        f"expected_lane_minimums={expected_lane_minimums} "
                        f"visible_lane_minimums={visible_lane_minimums} "
                        f"visible_lane_branch_counts={visible_lane_branch_counts}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_LANE_MINIMUMS_SATISFIED",
                    "status": _status(
                        not expected_effective_lane_minimums
                        or all(
                            visible_lane_branch_counts.get(lane, 0) >= min_branches
                            for lane, min_branches in expected_effective_lane_minimums.items()
                        )
                    ),
                    "detail": (
                        f"visible_debate_mode={visible_debate_mode} "
                        f"expected_effective_lane_minimums={expected_effective_lane_minimums} "
                        f"visible_lane_branch_counts={visible_lane_branch_counts}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_BRANCH_REQUIREMENTS_VISIBLE",
                    "status": _status(
                        not any(expected_branch_requirements.values())
                        or visible_branch_requirements == expected_branch_requirements
                    ),
                    "detail": (
                        f"expected_branch_requirements={expected_branch_requirements} "
                        f"visible_branch_requirements={visible_branch_requirements}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_LINEAGE_REQUIREMENTS_VISIBLE",
                    "status": _status(
                        not expected_lineage_requirements
                        or visible_lineage_requirements == expected_lineage_requirements
                    ),
                    "detail": (
                        f"expected_lineage_requirements={expected_lineage_requirements} "
                        f"visible_lineage_requirements={visible_lineage_requirements}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_BRANCH_LINEAGE_VISIBLE",
                    "status": _status(
                        not expected_branch_lineage_requirements
                        or (
                            visible_non_rescue_branch_count > 0
                            and branch_lineage_complete
                            and set(visible_branch_lineage_fields) >= set(expected_branch_lineage_requirements)
                        )
                    ),
                    "detail": (
                        f"expected_branch_lineage_requirements={expected_branch_lineage_requirements} "
                        f"visible_branch_lineage_fields={visible_branch_lineage_fields} "
                        f"branch_lineage_complete={branch_lineage_complete} "
                        f"visible_non_rescue_branch_count={visible_non_rescue_branch_count}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_BRANCH_PARENTAGE_VISIBLE",
                    "status": _status(
                        not expected_branch_lineage_requirements
                        or (
                            visible_non_rescue_branch_count > 0
                            and branch_parentage_internal_ok
                            and visible_branch_parentage_map == actual_branch_parentage_map
                            and visible_root_branch_ids == actual_root_branch_ids
                            and visible_branch_child_counts == actual_branch_child_counts
                        )
                    ),
                    "detail": (
                        f"branch_parentage_internal_ok={branch_parentage_internal_ok} "
                        f"actual_branch_parentage_map={actual_branch_parentage_map} "
                        f"visible_branch_parentage_map={visible_branch_parentage_map} "
                        f"actual_root_branch_ids={actual_root_branch_ids} "
                        f"visible_root_branch_ids={visible_root_branch_ids} "
                        f"actual_branch_child_counts={actual_branch_child_counts} "
                        f"visible_branch_child_counts={visible_branch_child_counts}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_BRANCH_GROUPS_VISIBLE",
                    "status": _status(
                        (
                            visible_non_rescue_branch_count == 0
                            and not actual_branch_group_map
                            and not visible_branch_group_map
                        )
                        or (
                            visible_non_rescue_branch_count > 0
                            and branch_group_complete
                            and visible_branch_group_map == actual_branch_group_map
                            and visible_branch_groups_used == actual_branch_groups_used
                        )
                    ),
                    "detail": (
                        f"visible_non_rescue_branch_count={visible_non_rescue_branch_count} "
                        f"branch_group_complete={branch_group_complete} "
                        f"actual_branch_group_map={actual_branch_group_map} "
                        f"visible_branch_group_map={visible_branch_group_map} "
                        f"actual_branch_groups_used={actual_branch_groups_used} "
                        f"visible_branch_groups_used={visible_branch_groups_used}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_BRANCH_TRACKS_VISIBLE",
                    "status": _status(
                        (
                            visible_non_rescue_branch_count == 0
                            and not actual_branch_track_map
                            and not visible_branch_track_map
                        )
                        or (
                            visible_non_rescue_branch_count > 0
                            and branch_track_complete
                            and visible_branch_track_map == actual_branch_track_map
                            and visible_branch_tracks_used == actual_branch_tracks_used
                        )
                    ),
                    "detail": (
                        f"visible_non_rescue_branch_count={visible_non_rescue_branch_count} "
                        f"branch_track_complete={branch_track_complete} "
                        f"actual_branch_track_map={actual_branch_track_map} "
                        f"visible_branch_track_map={visible_branch_track_map} "
                        f"actual_branch_tracks_used={actual_branch_tracks_used} "
                        f"visible_branch_tracks_used={visible_branch_tracks_used}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_RESCUE_LINEAGE_VISIBLE",
                    "status": _status(
                        not expected_rescue_lineage_required
                        or (
                            visible_rescue_lineage_required
                            and rescue_lineage_complete
                            and len(visible_rescue_linkages_used) >= visible_lane_branch_counts.get("RESCUER", 0)
                        )
                    ),
                    "detail": (
                        f"expected_rescue_lineage_required={expected_rescue_lineage_required} "
                        f"visible_rescue_lineage_required={visible_rescue_lineage_required} "
                        f"visible_rescue_linkages_used={visible_rescue_linkages_used} "
                        f"visible_rescue_lineage_fields={visible_rescue_lineage_fields} "
                        f"rescue_lineage_complete={rescue_lineage_complete} "
                        f"visible_rescue_branch_count={visible_rescue_branch_count} "
                        f"visible_rescuer_branch_count={visible_lane_branch_counts.get('RESCUER', 0)}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_REQUIRED_SIM_FAMILIES_VISIBLE",
                    "status": _status(set(expected_sim_families) == set(visible_sim_families)),
                    "detail": (
                        f"expected_sim_families={expected_sim_families} "
                        f"visible_sim_families={visible_sim_families}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_SIM_FAMILY_TIERS_VISIBLE",
                    "status": _status(
                        all(family in visible_sim_family_tier_map for family in expected_sim_families)
                        and all(bool(visible_sim_family_tier_map.get(family, [])) for family in expected_sim_families)
                        and all(
                            tier in visible_sim_family_tier_map.get(family, [])
                            for family, tier in expected_sim_family_tiers.items()
                        )
                    ),
                    "detail": (
                        f"expected_sim_family_tiers={expected_sim_family_tiers} "
                        f"visible_sim_family_tier_map={visible_sim_family_tier_map}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_RECOVERY_SIM_FAMILIES_VISIBLE",
                    "status": _status(
                        visible_recovery_sim_families == expected_recovery_sim_families
                        and set(visible_rescue_sim_families_used).issubset(set(expected_recovery_sim_families))
                    ),
                    "detail": (
                        f"expected_recovery_sim_families={expected_recovery_sim_families} "
                        f"visible_recovery_sim_families={visible_recovery_sim_families} "
                        f"visible_rescue_sim_families_used={visible_rescue_sim_families_used}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_RESCUE_SOURCE_LIMIT_VISIBLE",
                    "status": _status(
                        visible_rescue_source_limit == expected_rescue_source_limit
                        and visible_rescue_source_count <= expected_rescue_source_limit
                    ),
                    "detail": (
                        f"expected_rescue_source_limit={expected_rescue_source_limit} "
                        f"visible_rescue_source_limit={visible_rescue_source_limit} "
                        f"visible_rescue_source_count={visible_rescue_source_count}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_BUDGET_VISIBLE",
                    "status": _status(
                        not visible_debate_mode
                        or (
                            bool(expected_budget)
                            and visible_budget_max_items == expected_budget.get("max_items", 0)
                            and visible_budget_max_sims == expected_budget.get("max_sims", 0)
                            and visible_family_slice_budget_max_items == expected_budget.get("max_items", 0)
                            and visible_family_slice_budget_max_sims == expected_budget.get("max_sims", 0)
                            and visible_family_slice_budget_source
                            in {"planner_default", "family_slice_override"}
                        )
                    ),
                    "detail": (
                        f"visible_debate_mode={visible_debate_mode} "
                        f"expected_budget={expected_budget} "
                        f"visible_budget_max_items={visible_budget_max_items} "
                        f"visible_budget_max_sims={visible_budget_max_sims} "
                        f"visible_family_slice_budget_max_items={visible_family_slice_budget_max_items} "
                        f"visible_family_slice_budget_max_sims={visible_family_slice_budget_max_sims} "
                        f"visible_family_slice_budget_source={visible_family_slice_budget_source}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_SIM_FAMILY_OPERATOR_MAP_VISIBLE",
                    "status": _status(
                        all(family in visible_sim_family_operator_map for family in expected_sim_families)
                        and all(bool(visible_sim_family_operator_map.get(family, [])) for family in expected_sim_families)
                    ),
                    "detail": (
                        f"expected_sim_families={expected_sim_families} "
                        f"visible_sim_family_operator_map={visible_sim_family_operator_map}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_SIM_FAMILY_OPERATOR_MAP_CANONICAL",
                    "status": _status(
                        all(
                            visible_sim_family_operator_map.get(family, []) == LIVE_SIM_FAMILY_OPERATOR_DEFAULTS.get(family, [])
                            for family in expected_sim_families
                            if family in LIVE_SIM_FAMILY_OPERATOR_DEFAULTS
                        )
                    ),
                    "detail": (
                        f"expected_sim_family_operator_defaults={LIVE_SIM_FAMILY_OPERATOR_DEFAULTS} "
                        f"visible_sim_family_operator_map={visible_sim_family_operator_map}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_OPERATOR_POLICY_SOURCES_VISIBLE",
                    "status": _status(bool(visible_operator_policy_sources)),
                    "detail": (
                        f"visible_operator_policy_sources={visible_operator_policy_sources}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_OPERATOR_POLICY_SOURCES_CANONICAL",
                    "status": _status(set(visible_operator_policy_sources) == set(LIVE_OPERATOR_POLICY_SOURCES)),
                    "detail": (
                        f"expected_operator_policy_sources={LIVE_OPERATOR_POLICY_SOURCES} "
                        f"visible_operator_policy_sources={visible_operator_policy_sources}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_GOAL_PROBE_TERM_VISIBLE",
                    "status": _status(
                        bool(visible_goal_term)
                        and bool(visible_goal_probe_term)
                        and visible_goal_probe_term in set(expected_probe_terms)
                        and (
                            visible_goal_term not in expected_probe_overrides
                            or visible_goal_probe_term == expected_probe_overrides[visible_goal_term]
                        )
                    ),
                    "detail": (
                        f"visible_goal_term={visible_goal_term} "
                        f"visible_goal_probe_term={visible_goal_probe_term} "
                        f"expected_probe_terms={expected_probe_terms} "
                        f"expected_probe_override={expected_probe_overrides.get(visible_goal_term, '')}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_GOAL_PROBE_SOURCE_OWNED",
                    "status": _status(
                        bool(visible_goal_probe_source)
                        and visible_goal_probe_source in set(FAMILY_SLICE_GOAL_PROBE_SOURCES)
                    ),
                    "detail": (
                        f"visible_goal_probe_source={visible_goal_probe_source} "
                        f"allowed_goal_probe_sources={list(FAMILY_SLICE_GOAL_PROBE_SOURCES)}"
                    ),
                },
                {
                    "check_id": "AUTORATCHET_FAMILY_SLICE_GOAL_SIM_TIER_VISIBLE",
                    "status": _status(
                        bool(visible_goal_term)
                        and bool(visible_goal_sim_tier)
                        and (
                            (
                                visible_goal_term in expected_term_sim_tiers
                                and visible_goal_sim_tier == expected_term_sim_tiers[visible_goal_term]
                            )
                            or (
                                visible_goal_term not in expected_term_sim_tiers
                                and _sim_tier_rank(visible_goal_sim_tier) >= _sim_tier_rank(expected_tier_floor)
                            )
                        )
                    ),
                    "detail": (
                        f"visible_goal_term={visible_goal_term} "
                        f"visible_goal_sim_tier={visible_goal_sim_tier} "
                        f"expected_term_sim_tier={expected_term_sim_tiers.get(visible_goal_term, '')} "
                        f"expected_tier_floor={expected_tier_floor}"
                    ),
                },
            ]
        )

    status = "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL"
    family_slice_obligations_status = "PASS" if not family_slice_expected else _status(
        all(row["status"] == "PASS" for row in checks if row["check_id"].startswith("AUTORATCHET_FAMILY_SLICE_"))
        and all(row["status"] == "PASS" for row in checks if row["check_id"] == "AUTORATCHET_LATEST_STRATEGY_PRESENT")
        and all(row["status"] == "PASS" for row in checks if row["check_id"] == "AUTORATCHET_STRATEGY_FAMILY_SLICE_ID_MATCH")
    )
    return {
        "schema": "A1_AUTORATCHET_CYCLE_AUDIT_REPORT_v1",
        "status": status,
        "run_dir": str(run_dir),
        "summary_json_path": str(summary_path),
        "campaign_summary_json_path": str(campaign_path if campaign_path.exists() else report_path),
        "steps_completed": steps_completed,
        "steps_executed": steps_executed,
        "graveyard_count": graveyard_count,
        "canonical_term_count": canonical_term_count,
        "sim_registry_count": sim_registry_count,
        "zip_packet_count": zip_packet_count,
        "a1_semantic_gate_status": str((campaign_summary.get("a1_semantic_gate") or {}).get("status", "") or ""),
        "goal_source": goal_source,
        "planning_mode": planning_mode,
        "legacy_goal_profile_mode": legacy_goal_profile_mode,
        "compatibility_goal_profile": compatibility_goal_profile,
        "family_slice_expected": bool(family_slice_expected),
        "family_slice_id": family_slice_id,
        "family_slice_json": family_slice_json_raw,
        "family_slice_obligations_status": family_slice_obligations_status,
        "operator_policy_sources": visible_operator_policy_sources,
        "latest_strategy_zip_path": str(latest_zip_path) if latest_zip_path else "",
        "checks": checks,
        "errors": [] if status == "PASS" else ["A1_AUTORATCHET_CYCLE_AUDIT_FAILED"],
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Audit one direct A1 autoratchet cycle run surface.")
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--min-graveyard-count", type=int, default=1)
    ap.add_argument("--out-json", default="")
    args = ap.parse_args(argv)

    run_dir = Path(args.run_dir).expanduser().resolve()
    report = build_report(run_dir=run_dir, min_graveyard_count=int(args.min_graveyard_count))
    out_path = (
        Path(args.out_json).expanduser().resolve()
        if str(args.out_json).strip()
        else (run_dir / "reports" / "a1_autoratchet_cycle_audit_report.json")
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report_path": str(out_path)}, sort_keys=True))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
