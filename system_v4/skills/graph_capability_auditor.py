"""
graph_capability_auditor.py

Produce a grounded report of what the current system_v4 graph substrate can
actually express. This is meant to prevent overclaiming about the nested graph
stack while still giving the controller a concrete capability surface.
"""

from __future__ import annotations

import inspect
import json
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a2_graph_refinery import A2GraphRefinery
from system_v4.skills.graph_store import load_graph_json


AUTHORITATIVE_GRAPH = "system_v4/a2_state/graphs/system_graph_a2_refinery.json"
SKILL_REGISTRY = "system_v4/a1_state/skill_registry_v1.json"
NESTED_PROJECTION = "system_v4/a2_state/graphs/nested_graph_v1.json"
PROMOTED_SLICE = "system_v4/a2_state/graphs/promoted_subgraph.json"
A1_PROJECTION = "system_v4/a1_state/A1_GRAPH_PROJECTION.json"
IDENTITY_REGISTRY = "system_v4/a2_state/graphs/identity_registry_v1.json"
NESTED_BUILD_PROGRAM = "system_v4/a2_state/NESTED_GRAPH_BUILD_PROGRAM__2026_03_20__v1.json"

TARGET_LAYER_STORES = {
    "A2_HIGH_INTAKE": "system_v4/a2_state/graphs/a2_high_intake_graph_v1.json",
    "A2_MID_REFINEMENT": "system_v4/a2_state/graphs/a2_mid_refinement_graph_v1.json",
    "A2_LOW_CONTROL": "system_v4/a2_state/graphs/a2_low_control_graph_v1.json",
    "A1_JARGONED": "system_v4/a1_state/a1_jargoned_graph_v1.json",
    "A1_STRIPPED": "system_v4/a1_state/a1_stripped_graph_v1.json",
    "A1_CARTRIDGE": "system_v4/a1_state/a1_cartridge_graph_v1.json",
}
PRESERVED_OVERLAP_TREATMENT_LAYERS = (
    "A2_HIGH_INTAKE",
    "A2_MID_REFINEMENT",
    "A2_LOW_CONTROL",
)
OBSERVATION_KEY = "preserved_overlap_observation_summary"
HEALTH_KEY = "preserved_overlap_queue_health_summary"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return load_graph_json(REPO_ROOT, str(path.relative_to(REPO_ROOT)), default={})
    except (ValueError, json.JSONDecodeError):
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}


def _extract_next_required_lane(output_paths: list[Path]) -> str:
    for path in output_paths:
        if not path.exists() or path.suffix.lower() != ".md":
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("next_required_lane: "):
                return line.split(": ", 1)[1].strip()
    return ""


def _inspect_handoff(root: Path, raw_handoff_path: str) -> dict[str, Any]:
    if not raw_handoff_path:
        return {}
    handoff_path = Path(raw_handoff_path)
    if not handoff_path.is_absolute():
        handoff_path = root / handoff_path
    handoff = _load_json(handoff_path)
    if not handoff_path.exists() or not handoff:
        return {
            "path": str(handoff_path),
            "exists": handoff_path.exists(),
            "unit_id": "",
            "dispatch_id": "",
            "layer_id": "",
            "role_type": "",
            "thread_class": "",
            "mode": "",
            "queue_status": "",
            "state": "BLOCKED",
            "missing_boot": [],
            "missing_sources": [],
            "expected_output_count": 0,
            "existing_outputs": [],
            "write_scope": [],
            "next_required_lane": "",
        }
    required_boot = [Path(p) if Path(p).is_absolute() else (root / p) for p in handoff.get("required_boot", [])]
    source_artifacts = [Path(p) if Path(p).is_absolute() else (root / p) for p in handoff.get("source_artifacts", [])]
    expected_outputs = [Path(p) if Path(p).is_absolute() else (root / p) for p in handoff.get("expected_outputs", [])]
    missing_boot = [str(p) for p in required_boot if not p.exists()]
    missing_sources = [str(p) for p in source_artifacts if not p.exists()]
    existing_outputs = [str(p) for p in expected_outputs if p.exists()]
    if expected_outputs and len(existing_outputs) == len(expected_outputs):
        state = "COMPLETED"
    else:
        state = "BLOCKED" if (missing_boot or missing_sources) else "QUEUED"
    next_required_lane = _extract_next_required_lane(expected_outputs)
    return {
        "path": str(handoff_path),
        "exists": True,
        "unit_id": str(handoff.get("unit_id", "")),
        "dispatch_id": str(handoff.get("dispatch_id", "")),
        "layer_id": str(handoff.get("layer_id", "")),
        "role_type": str(handoff.get("role_type", "")),
        "thread_class": str(handoff.get("thread_class", "")),
        "mode": str(handoff.get("mode", "")),
        "queue_status": str(handoff.get("queue_status", "")),
        "state": state,
        "depends_on": list(handoff.get("depends_on", [])),
        "missing_boot": missing_boot,
        "missing_sources": missing_sources,
        "expected_output_count": len(expected_outputs),
        "existing_outputs": existing_outputs,
        "write_scope": list(handoff.get("write_scope", [])),
        "next_required_lane": next_required_lane,
    }


def _layer_store_state(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    if path.suffix.lower() != ".json":
        return "MATERIALIZED"
    data = _load_json(path)
    if data.get("materialized") is False:
        return "BLOCKED"
    build_status = str(data.get("build_status", "")).strip().upper()
    if build_status.startswith("FAIL") or build_status.startswith("BLOCKED"):
        return "BLOCKED"
    return "MATERIALIZED"


def _extract_preserved_overlap_treatment(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    preserve = data.get("preserve_diagnostics", {}) or {}
    overlap_hygiene = preserve.get("preserved_only_overlaps_hygiene", {}) or {}
    overlap_treatment = preserve.get("preserved_only_overlaps_treatment", {}) or {}
    has_preserve_diagnostics = bool(preserve)
    has_overlap_hygiene = bool(overlap_hygiene)
    has_overlap_treatment = bool(overlap_treatment)
    if not path.exists():
        treatment_state = "missing_layer_store"
    elif not has_preserve_diagnostics:
        treatment_state = "no_preserve_diagnostics_present"
    elif has_overlap_treatment:
        treatment_state = "treatment_reported"
    elif has_overlap_hygiene:
        treatment_state = "hygiene_only"
    else:
        treatment_state = "preserve_without_overlap_hygiene"
    return {
        "path": str(path),
        "exists": path.exists(),
        "treatment_state": treatment_state,
        "has_preserve_diagnostics": has_preserve_diagnostics,
        "has_overlap_hygiene": has_overlap_hygiene,
        "has_overlap_treatment": has_overlap_treatment,
        "preserved_only_edge_count": int(preserve.get("preserved_only_edge_count", 0) or 0),
        "preserved_only_overlap_edge_count": int(
            overlap_hygiene.get("preserved_only_overlap_edge_count", 0) or 0
        ),
        "current_runtime_effect": overlap_treatment.get("current_runtime_effect", ""),
        "equal_runtime_weight_admissible_now": overlap_treatment.get(
            "equal_runtime_weight_admissible_now"
        ),
        "recommended_future_handling": overlap_treatment.get(
            "recommended_future_handling", ""
        ),
        "reason_flags": list(overlap_treatment.get("reason_flags", [])),
    }


def _build_preserved_overlap_queue_health(
    summary: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    treatment_reported_layer_count = 0
    hygiene_only_layer_count = 0
    no_preserve_diagnostics_layer_count = 0
    missing_layer_store_count = 0
    preserved_only_overlap_layer_count = 0
    max_overlap_count = 0

    for info in summary.values():
        state = str(info.get("observation_state", ""))
        overlap_count = int(info.get("preserved_only_overlap_edge_count", 0) or 0)
        if state == "treatment_reported":
            treatment_reported_layer_count += 1
        elif state == "hygiene_only":
            hygiene_only_layer_count += 1
        elif state == "no_preserve_diagnostics_present":
            no_preserve_diagnostics_layer_count += 1
        elif state == "missing_layer_store":
            missing_layer_store_count += 1
        if overlap_count > 0:
            preserved_only_overlap_layer_count += 1
        if overlap_count > max_overlap_count:
            max_overlap_count = overlap_count

    return {
        "observation_mode": "non_operative",
        "derived_from": OBSERVATION_KEY,
        "layer_count": len(summary),
        "treatment_reported_layer_count": treatment_reported_layer_count,
        "hygiene_only_layer_count": hygiene_only_layer_count,
        "no_preserve_diagnostics_layer_count": no_preserve_diagnostics_layer_count,
        "missing_layer_store_count": missing_layer_store_count,
        "preserved_only_overlap_layer_count": preserved_only_overlap_layer_count,
        "max_preserved_only_overlap_edge_count": max_overlap_count,
        "note": "observational summary only; queue control fields remain unchanged",
    }


def _extract_nested_queue_health_summary(
    nested_build_program: dict[str, Any],
    queue_packet: dict[str, Any],
    current_queue_handoff: dict[str, Any],
) -> dict[str, Any]:
    program_observations = nested_build_program.get(OBSERVATION_KEY, {}) or {}
    queue_observations = queue_packet.get(OBSERVATION_KEY, {}) or {}
    program_health = nested_build_program.get(HEALTH_KEY, {}) or {}
    queue_health = queue_packet.get(HEALTH_KEY, {}) or {}

    if queue_observations and program_observations:
        observation_sync_state = (
            "in_sync" if queue_observations == program_observations else "mismatch"
        )
    elif queue_observations:
        observation_sync_state = "queue_only"
    elif program_observations:
        observation_sync_state = "program_only"
    else:
        observation_sync_state = "missing_both"

    if queue_health and program_health:
        stored_health_sync_state = "in_sync" if queue_health == program_health else "mismatch"
    elif queue_health:
        stored_health_sync_state = "queue_only"
    elif program_health:
        stored_health_sync_state = "program_only"
    else:
        stored_health_sync_state = "missing_both"

    active_observations = queue_observations or program_observations
    derived_health = _build_preserved_overlap_queue_health(active_observations)
    if stored_health_sync_state == "in_sync":
        synced_stored_health = queue_health or program_health
        stored_health_match_state = (
            "matches_observations"
            if synced_stored_health == derived_health
            else "mismatch_vs_observations"
        )
        if stored_health_match_state == "matches_observations":
            active_health = synced_stored_health
            stored_health_source = "queue_packet"
        else:
            active_health = derived_health
            stored_health_source = "derived_fallback"
    elif stored_health_sync_state in {"queue_only", "program_only", "mismatch"}:
        active_health = derived_health
        stored_health_source = "derived_fallback"
        stored_health_match_state = "fallback_required"
    else:
        stored_health_source = "derived_fallback" if active_observations else ""
        stored_health_match_state = (
            "derived_from_observations" if active_observations else "missing_both"
        )
        active_health = derived_health

    carryover_heavy_layers = [
        layer_id
        for layer_id, info in active_observations.items()
        if str(info.get("observation_state", "")) == "treatment_reported"
        and int(info.get("preserved_only_overlap_edge_count", 0) or 0) > 0
    ]
    observation_flags: list[str] = []
    if str(queue_packet.get("queue_status", "")).strip() == "NO_WORK":
        observation_flags.append("queue_paused_no_work")
    if str(nested_build_program.get("program_status", "")).startswith("NO_CURRENT_WORK"):
        observation_flags.append("program_paused_no_current_work")
    if observation_sync_state == "in_sync":
        observation_flags.append("observation_sync_in_place")
    elif observation_sync_state == "mismatch":
        observation_flags.append("observation_sync_mismatch")
    elif observation_sync_state != "missing_both":
        observation_flags.append("observation_sync_partial")
    if stored_health_sync_state == "mismatch":
        observation_flags.append("stored_health_sync_mismatch")
    elif stored_health_sync_state in {"queue_only", "program_only"}:
        observation_flags.append("stored_health_sync_partial")
    if stored_health_match_state == "mismatch_vs_observations":
        observation_flags.append("stored_health_mismatch_vs_observations")
    if carryover_heavy_layers:
        observation_flags.append("carryover_heavy_a2_layers_observed")

    return {
        "queue_status": str(queue_packet.get("queue_status", "")),
        "program_status": str(nested_build_program.get("program_status", "")),
        "queue_handoff_state": str(current_queue_handoff.get("state", "")),
        "observation_sync_state": observation_sync_state,
        "observation_source": (
            "queue_packet"
            if queue_observations
            else ("program" if program_observations else "")
        ),
        "stored_health_sync_state": stored_health_sync_state,
        "stored_health_source": stored_health_source,
        "stored_health_match_state": stored_health_match_state,
        "preserved_overlap_observation_health": active_health,
        "carryover_heavy_layer_count": len(carryover_heavy_layers),
        "carryover_heavy_layers": carryover_heavy_layers,
        "observation_flags": observation_flags,
    }


def _extract_skill_graph_coverage(
    authoritative: dict[str, Any],
    skill_registry: dict[str, Any],
) -> dict[str, Any]:
    nodes = authoritative.get("nodes", {}) or {}
    edges = authoritative.get("edges", []) or []
    active_skill_ids = sorted(
        skill_id
        for skill_id, record in skill_registry.items()
        if str(record.get("status", "active")) == "active"
    )
    skill_node_ids = sorted(
        nid for nid, node in nodes.items() if str(node.get("node_type", "")) == "SKILL"
    )
    graphed_skill_ids = {nid.replace("SKILL::", "") for nid in skill_node_ids}
    active_skill_set = set(active_skill_ids)
    matching_skill_ids = sorted(active_skill_set & graphed_skill_ids)
    missing_active_skill_ids = sorted(active_skill_set - graphed_skill_ids)
    stale_skill_ids = sorted(graphed_skill_ids - active_skill_set)

    connected = {edge.get("source_id", "") for edge in edges} | {
        edge.get("target_id", "") for edge in edges
    }
    isolated_skill_ids = sorted(
        nid.replace("SKILL::", "") for nid in skill_node_ids if nid not in connected
    )

    degree_by_skill_id: dict[str, int] = {nid.replace("SKILL::", ""): 0 for nid in skill_node_ids}
    for edge in edges:
        source_id = str(edge.get("source_id", ""))
        target_id = str(edge.get("target_id", ""))
        if source_id.startswith("SKILL::"):
            degree_by_skill_id[source_id.replace("SKILL::", "")] = (
                degree_by_skill_id.get(source_id.replace("SKILL::", ""), 0) + 1
            )
        if target_id.startswith("SKILL::"):
            degree_by_skill_id[target_id.replace("SKILL::", "")] = (
                degree_by_skill_id.get(target_id.replace("SKILL::", ""), 0) + 1
            )

    single_edge_skill_ids = sorted(
        skill_id for skill_id, degree in degree_by_skill_id.items() if degree == 1
    )

    return {
        "active_skill_count": len(active_skill_ids),
        "graphed_skill_node_count": len(skill_node_ids),
        "matching_active_skill_count": len(matching_skill_ids),
        "missing_active_skill_count": len(missing_active_skill_ids),
        "stale_skill_node_count": len(stale_skill_ids),
        "isolated_skill_node_count": len(isolated_skill_ids),
        "single_edge_skill_node_count": len(single_edge_skill_ids),
        "fully_graphed": not missing_active_skill_ids and not stale_skill_ids,
        "sample_missing_active_skill_ids": missing_active_skill_ids[:10],
        "sample_stale_skill_ids": stale_skill_ids[:10],
        "sample_isolated_skill_ids": isolated_skill_ids[:10],
        "sample_single_edge_skill_ids": single_edge_skill_ids[:10],
    }


def build_graph_capability_report(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()

    authoritative_path = root / AUTHORITATIVE_GRAPH
    skill_registry_path = root / SKILL_REGISTRY
    nested_projection_path = root / NESTED_PROJECTION
    promoted_slice_path = root / PROMOTED_SLICE
    a1_projection_path = root / A1_PROJECTION
    identity_registry_path = root / IDENTITY_REGISTRY
    nested_build_program_path = root / NESTED_BUILD_PROGRAM

    authoritative = _load_json(authoritative_path)
    skill_registry = _load_json(skill_registry_path)
    nested_projection = _load_json(nested_projection_path)
    promoted_slice = _load_json(promoted_slice_path)
    a1_projection = _load_json(a1_projection_path)
    nested_build_program = _load_json(nested_build_program_path)
    queue_packet = _load_json(
        Path(str(nested_build_program.get("current_queue_packet_json", "")))
        if str(nested_build_program.get("current_queue_packet_json", "")).strip()
        else (root / "system_v4" / "a2_state" / "NESTED_GRAPH_BUILD_QUEUE_STATUS_PACKET__CURRENT__2026_03_20__v1.json")
    )
    raw_handoff_path = str(
        queue_packet.get("dispatch_handoff_json", "")
        or nested_build_program.get("next_correction_handoff_json", "")
    )
    if not raw_handoff_path and str(queue_packet.get("queue_status", "")).strip() == "NO_WORK":
        current_queue_handoff = {
            "path": "",
            "exists": False,
            "unit_id": "",
            "dispatch_id": "",
            "layer_id": "",
            "role_type": "",
            "thread_class": "",
            "mode": "",
            "queue_status": "NO_WORK",
            "state": "NO_WORK",
            "missing_boot": [],
            "missing_sources": [],
            "expected_output_count": 0,
            "existing_outputs": [],
            "write_scope": [],
            "next_required_lane": "",
        }
    else:
        current_queue_handoff = _inspect_handoff(root, raw_handoff_path)

    master_nodes = authoritative.get("nodes", {})
    master_edges = authoritative.get("edges", [])
    layer_population: dict[str, int] = {}
    for node in master_nodes.values():
        layer = str(node.get("layer", "")).strip()
        if not layer:
            continue
        layer_population[layer] = layer_population.get(layer, 0) + 1

    target_layer_store_status = {
        layer_id: {
            "path": str(root / rel_path),
            "exists": (root / rel_path).exists(),
            "state": _layer_store_state(root / rel_path),
            "materialized": _layer_store_state(root / rel_path) == "MATERIALIZED",
        }
        for layer_id, rel_path in TARGET_LAYER_STORES.items()
    }
    preserved_overlap_treatment_summary = {
        layer_id: _extract_preserved_overlap_treatment(root / TARGET_LAYER_STORES[layer_id])
        for layer_id in PRESERVED_OVERLAP_TREATMENT_LAYERS
    }
    skill_graph_coverage = _extract_skill_graph_coverage(authoritative, skill_registry)
    nested_queue_health_summary = _extract_nested_queue_health_summary(
        nested_build_program,
        queue_packet,
        current_queue_handoff,
    )

    refinery = A2GraphRefinery(str(root))
    nx_method_names = [
        "nx_ancestors",
        "nx_descendants",
        "nx_ego_graph",
        "nx_simple_cycles",
        "nx_topological_sort",
    ]
    nx_methods = {}
    for name in nx_method_names:
        fn = getattr(refinery, name, None)
        if fn is None:
            nx_methods[name] = {"available": False, "relation_filter": False}
            continue
        params = inspect.signature(fn).parameters
        nx_methods[name] = {
            "available": True,
            "relation_filter": "relation_filter" in params,
        }

    limitations: list[str] = []
    if authoritative_path.exists():
        limitations.append("one authoritative live graph store still carries all A2/A1 populations")
    if not identity_registry_path.exists():
        limitations.append("identity registry owner surface does not exist yet")
    for layer_id, info in target_layer_store_status.items():
        if info["state"] == "MISSING":
            limitations.append(f"separate layer store missing for {layer_id}")
        elif info["state"] == "BLOCKED":
            limitations.append(f"separate layer store blocked for {layer_id}")
    if a1_projection and not isinstance(a1_projection.get("edges"), list):
        limitations.append("A1 graph projection has no explicit edge list")
    if nested_projection_path.exists():
        nested_layers = nested_projection.get("layers", {})
        nested_count = len(nested_layers) if isinstance(nested_layers, dict) else 0
        if nested_count:
            limitations.append("nested_graph_v1 is a projection summary, not a live owner graph")
    if not all(info["relation_filter"] for info in nx_methods.values() if info["available"]):
        limitations.append("not all NX wrappers support relation filtering")
    if current_queue_handoff:
        if current_queue_handoff.get("missing_boot"):
            limitations.append("current queued correction handoff has missing boot surfaces")
        if current_queue_handoff.get("missing_sources"):
            limitations.append("current queued correction handoff has missing source artifacts")
        if current_queue_handoff.get("state") == "COMPLETED":
            limitations.append("current queued correction handoff has already produced its expected output; controller queue state may need advancement")
        if current_queue_handoff.get("state") == "NO_WORK":
            limitations.append("current queued correction flow is intentionally paused with no immediate bounded follow-on lane")
    limitations.append("bridge contracts between the intended 3+3 layer stores are not materialized as separate owner surfaces")

    materialized_layer_stores = [
        layer_id for layer_id, info in target_layer_store_status.items() if info["materialized"]
    ]
    if not identity_registry_path.exists():
        next_recommended_unit = "IDENTITY_REGISTRY"
    elif str(nested_build_program.get("program_status", "")).startswith("NO_CURRENT_WORK") or str(queue_packet.get("queue_status", "")).strip() == "NO_WORK":
        next_recommended_unit = None
    elif str(nested_build_program.get("program_status", "")).startswith("BLOCKED_ON_"):
        if current_queue_handoff and current_queue_handoff.get("state") == "QUEUED":
            next_recommended_unit = str(nested_build_program.get("next_correction_unit_id", ""))
        elif current_queue_handoff and current_queue_handoff.get("state") == "COMPLETED":
            next_recommended_unit = str(current_queue_handoff.get("next_required_lane", "") or "CONTROLLER_ADVANCE_REQUIRED")
        elif current_queue_handoff and current_queue_handoff.get("state") == "NO_WORK":
            next_recommended_unit = None
        else:
            next_recommended_unit = "REPAIR_CURRENT_QUEUE_HANDOFF"
    else:
        next_recommended_unit = next(
            (layer_id for layer_id in TARGET_LAYER_STORES if target_layer_store_status[layer_id]["state"] != "MATERIALIZED"),
            "",
        )

    report = {
        "schema": "GRAPH_CAPABILITY_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "canonical_graph_count": 1 if authoritative_path.exists() else 0,
        "explicit_identity_registry": identity_registry_path.exists(),
        "typed_layer_stores_materialized": materialized_layer_stores,
        "next_recommended_unit": next_recommended_unit,
        "authoritative_live_store": {
            "path": str(authoritative_path),
            "exists": authoritative_path.exists(),
            "node_count": len(master_nodes),
            "edge_count": len(master_edges),
        },
        "projection_surfaces": {
            "nested_graph_v1": {
                "path": str(nested_projection_path),
                "exists": nested_projection_path.exists(),
                "layer_count": len(nested_projection.get("layers", {})) if isinstance(nested_projection.get("layers"), dict) else 0,
            },
            "promoted_subgraph": {
                "path": str(promoted_slice_path),
                "exists": promoted_slice_path.exists(),
                "node_count": len(promoted_slice.get("nodes", {})),
                "edge_count": len(promoted_slice.get("edges", [])),
            },
            "a1_projection": {
                "path": str(a1_projection_path),
                "exists": a1_projection_path.exists(),
                "node_count": len(a1_projection.get("nodes", {})),
                "has_edges": isinstance(a1_projection.get("edges"), list),
            },
        },
        "layer_population_in_master_graph": layer_population,
        "skill_graph_coverage": skill_graph_coverage,
        "target_layer_store_status": target_layer_store_status,
        "preserved_overlap_treatment_summary": preserved_overlap_treatment_summary,
        "nested_queue_health_summary": nested_queue_health_summary,
        "identity_registry_status": {
            "path": str(identity_registry_path),
            "exists": identity_registry_path.exists(),
        },
        "current_queue_handoff_status": current_queue_handoff,
        "query_capabilities": {
            "graph_backend": "networkx.MultiDiGraph",
            "nx_methods": nx_methods,
            "graphml_export": True,
            "relation_filtered_queries_available": any(
                info["relation_filter"] for info in nx_methods.values()
            ),
        },
        "limitations": limitations,
    }
    return report


def render_graph_capability_note(report: dict[str, Any]) -> str:
    lines = [
        "# GRAPH_CAPABILITY_AUDIT__CURRENT__v1",
        "",
        f"generated_utc: {report['generated_utc']}",
        f"authoritative_live_store: {report['authoritative_live_store']['path']}",
        f"authoritative_node_count: {report['authoritative_live_store']['node_count']}",
        f"authoritative_edge_count: {report['authoritative_live_store']['edge_count']}",
        f"canonical_graph_count: {report['canonical_graph_count']}",
        f"explicit_identity_registry: {report['explicit_identity_registry']}",
        f"typed_layer_stores_materialized: {len(report['typed_layer_stores_materialized'])}",
        f"next_recommended_unit: {report['next_recommended_unit']}",
        "",
        "## Current Queue Handoff",
        f"- path: {report['current_queue_handoff_status'].get('path', '')}",
        f"- unit_id: {report['current_queue_handoff_status'].get('unit_id', '')}",
        f"- dispatch_id: {report['current_queue_handoff_status'].get('dispatch_id', '')}",
        f"- layer_id: {report['current_queue_handoff_status'].get('layer_id', '')}",
        f"- role_type: {report['current_queue_handoff_status'].get('role_type', '')}",
        f"- thread_class: {report['current_queue_handoff_status'].get('thread_class', '')}",
        f"- mode: {report['current_queue_handoff_status'].get('mode', '')}",
        f"- queue_status: {report['current_queue_handoff_status'].get('queue_status', '')}",
        f"- state: {report['current_queue_handoff_status'].get('state', '')}",
        f"- existing_outputs: {len(report['current_queue_handoff_status'].get('existing_outputs', []))}/{report['current_queue_handoff_status'].get('expected_output_count', 0)}",
        "",
    ]
    if report["current_queue_handoff_status"].get("next_required_lane"):
        lines.insert(
            len(lines) - 2,
            f"- next_required_lane: {report['current_queue_handoff_status'].get('next_required_lane', '')}",
        )
    if report["current_queue_handoff_status"].get("write_scope"):
        lines.append("- write_scope:")
        for item in report["current_queue_handoff_status"]["write_scope"]:
            lines.append(f"  - {item}")
        lines.append("")
    lines.extend([
        "## Nested Queue Health",
        f"- queue_status: {report['nested_queue_health_summary'].get('queue_status', '')}",
        f"- program_status: {report['nested_queue_health_summary'].get('program_status', '')}",
        f"- queue_handoff_state: {report['nested_queue_health_summary'].get('queue_handoff_state', '')}",
        f"- observation_sync_state: {report['nested_queue_health_summary'].get('observation_sync_state', '')}",
        f"- observation_source: {report['nested_queue_health_summary'].get('observation_source', '')}",
        f"- stored_health_sync_state: {report['nested_queue_health_summary'].get('stored_health_sync_state', '')}",
        f"- stored_health_source: {report['nested_queue_health_summary'].get('stored_health_source', '')}",
        f"- stored_health_match_state: {report['nested_queue_health_summary'].get('stored_health_match_state', '')}",
    ])
    preserved_overlap_health = (
        report["nested_queue_health_summary"].get("preserved_overlap_observation_health", {})
        or {}
    )
    if preserved_overlap_health:
        lines.extend([
            f"- preserved_overlap_health_derived_from: {preserved_overlap_health.get('derived_from', '')}",
            f"- preserved_overlap_health_observation_mode: {preserved_overlap_health.get('observation_mode', '')}",
            f"- preserved_overlap_health_layer_count: {preserved_overlap_health.get('layer_count', 0)}",
            "- preserved_overlap_health_treatment_reported_layer_count: "
            f"{preserved_overlap_health.get('treatment_reported_layer_count', 0)}",
            "- preserved_overlap_health_no_preserve_diagnostics_layer_count: "
            f"{preserved_overlap_health.get('no_preserve_diagnostics_layer_count', 0)}",
            "- preserved_overlap_health_preserved_only_overlap_layer_count: "
            f"{preserved_overlap_health.get('preserved_only_overlap_layer_count', 0)}",
            "- preserved_overlap_health_max_preserved_only_overlap_edge_count: "
            f"{preserved_overlap_health.get('max_preserved_only_overlap_edge_count', 0)}",
        ])
    lines.append(
        f"- carryover_heavy_layer_count: {report['nested_queue_health_summary'].get('carryover_heavy_layer_count', 0)}"
    )
    if report["nested_queue_health_summary"].get("carryover_heavy_layers"):
        lines.append(
            "- carryover_heavy_layers: "
            f"{report['nested_queue_health_summary'].get('carryover_heavy_layers', [])}"
        )
    if report["nested_queue_health_summary"].get("observation_flags"):
        lines.append(
            "- observation_flags: "
            f"{report['nested_queue_health_summary'].get('observation_flags', [])}"
        )
    lines.extend([
        "",
        "## Layer Population In Master Graph",
    ])
    for layer_id, count in sorted(report["layer_population_in_master_graph"].items()):
        lines.append(f"- {layer_id}: {count}")
    lines.extend([
        "",
        "## Skill Graph Coverage",
        f"- active_skill_count: {report['skill_graph_coverage'].get('active_skill_count', 0)}",
        "- graphed_skill_node_count: "
        f"{report['skill_graph_coverage'].get('graphed_skill_node_count', 0)}",
        "- matching_active_skill_count: "
        f"{report['skill_graph_coverage'].get('matching_active_skill_count', 0)}",
        "- missing_active_skill_count: "
        f"{report['skill_graph_coverage'].get('missing_active_skill_count', 0)}",
        f"- stale_skill_node_count: {report['skill_graph_coverage'].get('stale_skill_node_count', 0)}",
        "- isolated_skill_node_count: "
        f"{report['skill_graph_coverage'].get('isolated_skill_node_count', 0)}",
        "- single_edge_skill_node_count: "
        f"{report['skill_graph_coverage'].get('single_edge_skill_node_count', 0)}",
        f"- fully_graphed: {report['skill_graph_coverage'].get('fully_graphed', False)}",
    ])
    if report["skill_graph_coverage"].get("sample_missing_active_skill_ids"):
        lines.append(
            "- sample_missing_active_skill_ids: "
            f"{report['skill_graph_coverage'].get('sample_missing_active_skill_ids', [])}"
        )
    if report["skill_graph_coverage"].get("sample_stale_skill_ids"):
        lines.append(
            "- sample_stale_skill_ids: "
            f"{report['skill_graph_coverage'].get('sample_stale_skill_ids', [])}"
        )
    if report["skill_graph_coverage"].get("sample_isolated_skill_ids"):
        lines.append(
            "- sample_isolated_skill_ids: "
            f"{report['skill_graph_coverage'].get('sample_isolated_skill_ids', [])}"
        )
    if report["skill_graph_coverage"].get("sample_single_edge_skill_ids"):
        lines.append(
            "- sample_single_edge_skill_ids: "
            f"{report['skill_graph_coverage'].get('sample_single_edge_skill_ids', [])}"
        )
    lines.extend([
        "",
        "## Target Layer Store Status",
    ])
    for layer_id, info in report["target_layer_store_status"].items():
        state = info["state"]
        lines.append(f"- {layer_id}: {state} ({info['path']})")
    lines.extend([
        "",
        "## Preserved Overlap Treatment",
    ])
    for layer_id, info in report["preserved_overlap_treatment_summary"].items():
        lines.append(
            f"- {layer_id}: state={info['treatment_state']} "
            f"preserved_only_edges={info['preserved_only_edge_count']} "
            f"preserved_only_overlaps={info['preserved_only_overlap_edge_count']}"
        )
        if info.get("current_runtime_effect"):
            lines.append(f"  - current_runtime_effect: {info['current_runtime_effect']}")
        if info.get("equal_runtime_weight_admissible_now") is not None:
            lines.append(
                "  - equal_runtime_weight_admissible_now: "
                f"{info['equal_runtime_weight_admissible_now']}"
            )
        if info.get("recommended_future_handling"):
            lines.append(
                "  - recommended_future_handling: "
                f"{info['recommended_future_handling']}"
            )
        if info.get("reason_flags"):
            lines.append(f"  - reason_flags: {info['reason_flags']}")
    lines.extend([
        "",
        "## Query Capabilities",
    ])
    for name, info in report["query_capabilities"]["nx_methods"].items():
        lines.append(
            f"- {name}: available={info['available']} relation_filter={info['relation_filter']}"
        )
    lines.extend([
        "",
        "## Current Limits",
    ])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def write_graph_capability_report(workspace_root: str) -> dict[str, str]:
    root = Path(workspace_root).resolve()
    report = build_graph_capability_report(str(root))
    audit_dir = root / "system_v4" / "a2_state" / "audit_logs"
    audit_dir.mkdir(parents=True, exist_ok=True)
    json_path = audit_dir / "GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json"
    md_path = audit_dir / "GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_graph_capability_note(report), encoding="utf-8")
    return {"json_path": str(json_path), "md_path": str(md_path)}


if __name__ == "__main__":
    result = write_graph_capability_report(str(REPO_ROOT))
    print(json.dumps(result, indent=2, sort_keys=True))
