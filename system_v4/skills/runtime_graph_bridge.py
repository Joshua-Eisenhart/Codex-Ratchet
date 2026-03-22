"""
runtime_graph_bridge.py — Canonical Runtime → Graph Bridge

This is the CHECKED-IN, REPRODUCIBLE bridge that writes B kernel,
SIM engine, and graveyard results into the canonical graph.

It follows the GraphNode/GraphEdge schema from v4_graph_builder.py:
  - GraphNode requires: id, node_type, layer, name, description
  - GraphEdge requires: source_id, target_id, relation, attributes

The bridge is observational: the graph RECORDS what the lower loop
produced, it does not impersonate or invent it.
"""

import json
import time
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any, Optional


# ═══════════════════════════════════════════════════════════
# Layer Constants (match v4_graph_builder.py)
# ═══════════════════════════════════════════════════════════

LAYER_B_ADJUDICATED = "B_ADJUDICATED"
LAYER_SIM_EVIDENCED = "SIM_EVIDENCED"
LAYER_GRAVEYARD = "GRAVEYARD"
LAYER_TERM_REGISTRY = "TERM_REGISTRY"
LAYER_A2_INTAKE = "A2_3_INTAKE"
LAYER_SKILL_REGISTRY = "SKILL_REGISTRY"

SKILL_ID_ALIASES = {
    "codex-automation-controller": "automation-controller",
    "playwright": "browser-automation",
}


def _append_edge(edges: List[dict], source_id: str, target_id: str,
                 relation: str, attributes: Optional[dict] = None) -> bool:
    if source_id == target_id:
        return False

    edge = {
        "source_id": source_id,
        "target_id": target_id,
        "relation": relation,
        "attributes": attributes or {},
    }
    if edge in edges:
        return False
    edges.append(edge)
    return True


def _resolve_existing_target(nodes: Dict[str, dict], *candidates: Optional[str]) -> Optional[str]:
    for candidate in candidates:
        if candidate and candidate in nodes:
            return candidate
    return None


def _merge_list_values(primary: Any, secondary: Any) -> list[Any]:
    merged: list[Any] = []
    for value in list(primary or []) + list(secondary or []):
        if value not in merged:
            merged.append(value)
    return merged


def _witness_primary_text(entry: dict, kind: str) -> str:
    witness = entry.get("witness", {})
    trace = witness.get("trace", [])
    if trace and isinstance(trace[0], dict):
        notes = trace[0].get("notes", [])
        if notes:
            return str(notes[0])
    tags = entry.get("tags", {})
    if kind == "intent":
        return str(tags.get("intent", ""))
    if kind == "context":
        return str(tags.get("context", ""))
    return ""


def _bridge_intent_context_witnesses(
    nodes: Dict[str, dict],
    edges: List[dict],
    witness_corpus: list[dict],
) -> tuple[int, int]:
    nodes_added = 0
    edges_added = 0
    batch_intent_nodes: dict[str, list[str]] = {}
    batch_context_nodes: dict[str, list[str]] = {}

    for idx, entry in enumerate(witness_corpus):
        witness = entry.get("witness", {})
        kind = str(witness.get("kind", "")).lower()
        if kind not in {"intent", "context"}:
            continue

        tags = entry.get("tags", {}) or {}
        recorded_at = entry.get("recorded_at", "")
        source = str(tags.get("source", "system" if kind == "context" else "maker"))
        batch = str(tags.get("batch", ""))
        text = _witness_primary_text(entry, kind).strip()
        if not text:
            continue

        if kind == "intent":
            nid = f"INTENT_SIGNAL::WITNESS::{idx:06d}"
            node_type = "INTENT_SIGNAL"
            object_family = "IntentRecord"
            source_class = "DERIVED"
            status = "LIVE"
            admissibility_state = "PROPOSAL_ONLY"
            tag_list = ["intent", "witness", source]
            if topic := tags.get("topic"):
                tag_list.append(str(topic))
            batch_intent_nodes.setdefault(batch, []).append(nid)
        else:
            nid = f"CONTEXT_SIGNAL::WITNESS::{idx:06d}"
            node_type = "CONTEXT_SIGNAL"
            object_family = "ContextRecord"
            source_class = "DERIVED"
            status = "RUNTIME_ONLY"
            admissibility_state = "RUNTIME_ONLY"
            tag_list = ["context", "witness", source]
            batch_context_nodes.setdefault(batch, []).append(nid)

        if nid not in nodes:
            nodes_added += 1

        nodes[nid] = {
            "id": nid,
            "node_type": node_type,
            "layer": LAYER_A2_INTAKE,
            "name": f"{node_type}:{source}:{idx}",
            "description": text,
            "trust_zone": LAYER_A2_INTAKE,
            "tags": sorted(set(tag_list)),
            "authority": "SOURCE_CLAIM",
            "properties": {
                "witness_index": idx,
                "witness_kind": kind,
                "recorded_at": recorded_at,
                "source": source,
                "batch": batch,
                "phase": str(tags.get("phase", "")),
                "priority": str(tags.get("priority", "")),
                "topic": str(tags.get("topic", "")),
            },
            "object_family": object_family,
            "source_class": source_class,
            "status": status,
            "admissibility_state": admissibility_state,
            "lineage_refs": [],
            "witness_refs": [f"WITNESS_CORPUS::{idx}"],
        }

    for batch, context_nodes in batch_context_nodes.items():
        if not batch:
            continue
        for context_nid in context_nodes:
            for intent_nid in batch_intent_nodes.get(batch, []):
                if _append_edge(
                    edges,
                    context_nid,
                    intent_nid,
                    "CONTEXT_FOR",
                    {"batch": batch, "inferred": True},
                ):
                    edges_added += 1

    return nodes_added, edges_added


def _skill_graph_node(skill_id: str, record: dict, existing: Optional[dict] = None) -> dict:
    zones = list(record.get("applicable_trust_zones", []) or [])
    graphs = list(record.get("applicable_graphs", []) or [])
    tags = sorted(
        {
            str(tag)
            for tag in (
                list(record.get("tags", []) or [])
                + [record.get("skill_type", ""), record.get("source_type", "")]
            )
            if str(tag).strip()
        }
    )
    existing = existing or {}
    return {
        "id": f"SKILL::{skill_id}",
        "node_type": "SKILL",
        "layer": LAYER_SKILL_REGISTRY,
        "name": record.get("skill_id", skill_id),
        "description": record.get("description", "") or record.get("name", skill_id),
        "trust_zone": LAYER_SKILL_REGISTRY,
        "tags": tags,
        "authority": "SOURCE_CLAIM",
        "properties": {
            "skill_type": record.get("skill_type", ""),
            "source_type": record.get("source_type", ""),
            "source_path": record.get("source_path", ""),
            "status": record.get("status", ""),
            "applicable_layers": zones,
            "applicable_trust_zones": zones,
            "applicable_graphs": graphs,
            "inputs": list(record.get("inputs", []) or []),
            "outputs": list(record.get("outputs", []) or []),
            "adapters": dict(record.get("adapters", {}) or {}),
            "related_skills": list(record.get("related_skills", []) or []),
        },
        "object_family": "SkillRecord",
        "source_class": "DERIVED",
        "status": "LIVE" if record.get("status", "active") == "active" else "INACTIVE",
        "admissibility_state": "REGISTERED",
        "lineage_refs": list(existing.get("lineage_refs", []) or []),
        "witness_refs": list(existing.get("witness_refs", []) or []),
    }


def _sync_active_skill_registry_nodes(
    nodes: Dict[str, dict],
    edges: List[dict],
    skill_registry: dict[str, dict],
) -> tuple[int, int, int]:
    nodes_added = 0
    nodes_refreshed = 0
    related_edges_added = 0
    active_records: dict[str, dict] = {}

    for skill_id, record in skill_registry.items():
        if str(record.get("status", "active")) != "active":
            continue
        active_records[skill_id] = record
        nid = f"SKILL::{skill_id}"
        if nid in nodes:
            nodes_refreshed += 1
        else:
            nodes_added += 1
        nodes[nid] = _skill_graph_node(skill_id, record, nodes.get(nid))

    for skill_id, record in active_records.items():
        source_nid = f"SKILL::{skill_id}"
        for related_skill_id in record.get("related_skills", []) or []:
            target_nid = f"SKILL::{related_skill_id}"
            if target_nid not in nodes or target_nid == source_nid:
                continue
            if _append_edge(
                edges,
                source_nid,
                target_nid,
                "RELATED_TO",
                {
                    "inferred": True,
                    "role": "registry_related_skill",
                },
            ):
                related_edges_added += 1

    return nodes_added, nodes_refreshed, related_edges_added


def _migrate_skill_alias_nodes(
    nodes: Dict[str, dict],
    edges: List[dict],
    skill_registry: dict[str, dict],
) -> int:
    migrated = 0
    for alias_skill_id, canonical_skill_id in SKILL_ID_ALIASES.items():
        alias_nid = f"SKILL::{alias_skill_id}"
        canonical_nid = f"SKILL::{canonical_skill_id}"
        if alias_nid not in nodes or canonical_skill_id not in skill_registry:
            continue

        alias_node = nodes[alias_nid]
        canonical_existing = nodes.get(canonical_nid, {})
        if canonical_nid not in nodes:
            nodes[canonical_nid] = {
                **alias_node,
                "id": canonical_nid,
                "name": canonical_skill_id,
            }
        else:
            nodes[canonical_nid]["lineage_refs"] = _merge_list_values(
                canonical_existing.get("lineage_refs", []),
                alias_node.get("lineage_refs", []),
            )
            nodes[canonical_nid]["witness_refs"] = _merge_list_values(
                canonical_existing.get("witness_refs", []),
                alias_node.get("witness_refs", []),
            )

        for edge in edges:
            if edge.get("source_id") == alias_nid:
                edge["source_id"] = canonical_nid
            if edge.get("target_id") == alias_nid:
                edge["target_id"] = canonical_nid

        del nodes[alias_nid]
        migrated += 1

    return migrated


def _remove_non_registry_skill_nodes(
    nodes: Dict[str, dict],
    edges: List[dict],
    active_skill_ids: set[str],
) -> tuple[List[dict], int]:
    stale_skill_nids = {
        nid
        for nid, node in nodes.items()
        if node.get("node_type") == "SKILL" and nid.replace("SKILL::", "") not in active_skill_ids
    }
    if not stale_skill_nids:
        return edges, 0

    for nid in stale_skill_nids:
        del nodes[nid]

    filtered_edges = [
        edge
        for edge in edges
        if edge.get("source_id") not in stale_skill_nids and edge.get("target_id") not in stale_skill_nids
    ]
    return filtered_edges, len(stale_skill_nids)


def bridge_runtime_to_graph(repo_root: str, clean: bool = True) -> dict:
    """
    Bridge the current runtime state into the canonical graph.

    Args:
        repo_root: Path to the repo root
        clean: If True, remove stale bridge nodes before writing new ones

    Returns:
        Summary stats dict
    """
    repo = Path(repo_root)

    # Load runtime state
    brain_path = repo / "system_v4" / "a1_state" / "a1_brain_state.json"
    b_path = repo / "system_v4" / "runtime_state" / "b_kernel_state.json"
    sim_path = repo / "system_v4" / "runtime_state" / "sim_state.json"
    witness_path = repo / "system_v4" / "a2_state" / "witness_corpus_v1.json"
    graph_path = repo / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json"

    brain_state = json.loads(brain_path.read_text()) if brain_path.exists() else {}
    b_state = json.loads(b_path.read_text()) if b_path.exists() else {}
    sim_state = json.loads(sim_path.read_text()) if sim_path.exists() else {}
    witness_corpus = json.loads(witness_path.read_text()) if witness_path.exists() else []
    graph = json.loads(graph_path.read_text()) if graph_path.exists() else {"nodes": {}, "edges": []}

    # ─── Guard rail: refuse clean if runtime state is missing ───
    state_present = b_path.exists() and sim_path.exists()
    if clean and not state_present:
        print("WARNING: clean=True but runtime state files missing. "
              "Skipping clean to avoid losing graph data.")
        clean = False

    nodes = graph["nodes"]
    edges = [e for e in graph["edges"] if e.get("source_id") != e.get("target_id")]
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # ─── Tag legacy-era nodes (Phase 1A) ───
    # Old pipeline wrote B_OUTCOME, CARTRIDGE_PACKAGE, EXECUTION_BLOCK
    # without real B-adjudication. Tag them so they don't pollute new results.
    legacy_tagged = 0
    LEGACY_TYPES = {"B_OUTCOME", "CARTRIDGE_PACKAGE", "EXECUTION_BLOCK"}
    for nid, n in nodes.items():
        if n.get("node_type") in LEGACY_TYPES and n.get("status") != "LEGACY_ERA":
            n["status"] = "LEGACY_ERA"
            n.setdefault("properties", {})["legacy_tagged_utc"] = ts
            n.setdefault("tags", [])
            if "LEGACY_ERA" not in n["tags"]:
                n["tags"].append("LEGACY_ERA")
            legacy_tagged += 1

    # ─── Clean stale bridge nodes if requested ───
    stale_prefixes = ("B_SURVIVOR::", "B_PARKED::", "GRAVEYARD_RECORD::",
                      "SIM_EVIDENCED::", "SIM_KILL::", "TERM_ADMITTED::",
                      "INTENT_SIGNAL::WITNESS::", "CONTEXT_SIGNAL::WITNESS::")
    if clean:
        stale_ids = [nid for nid in nodes if any(nid.startswith(p) for p in stale_prefixes)]
        for nid in stale_ids:
            del nodes[nid]
        edges = [e for e in edges if not any(
            e.get("source_id", "").startswith(p) or e.get("target_id", "").startswith(p)
            for p in stale_prefixes
        )]
        graph["edges"] = edges

    n_added = 0
    e_added = 0

    # ─── Bridge B Survivors ───
    for sid, survivor in b_state.get("survivor_ledger", {}).items():
        nid = f"B_SURVIVOR::{sid}"
        item = survivor.get("item", {})
        kind = survivor.get("kind", "")
        source_concept_id = (
            survivor.get("provenance", {}).get("source_concept_id")
            or item.get("source_concept_id", "")
        )

        struct = ""
        term = ""
        for df in item.get("def_fields", []):
            if df.get("name") == "structural_form":
                struct = df.get("value", "")
            if df.get("name") == "term_literal":
                term = df.get("value", "")

        desc_parts = [f"B-accepted {kind}"]
        if struct:
            desc_parts.append(f"structural_form={struct}")
        if term:
            desc_parts.append(f"term={term}")

        nodes[nid] = {
            "id": nid,
            "node_type": "B_SURVIVOR",
            "layer": LAYER_B_ADJUDICATED,
            "name": f"B_SURVIVOR_{sid}_{kind}",
            "description": ". ".join(desc_parts),
            "trust_zone": LAYER_B_ADJUDICATED,
            "tags": [kind, "EARNED"],
            "authority": "B_ACCEPTED",
            "properties": {
                "candidate_id": sid,
                "kind": kind,
                "item_class": survivor.get("class", ""),
                "batch_id": survivor.get("provenance", {}).get("batch_id", ""),
                "accepted_utc": survivor.get("provenance", {}).get("accepted_utc", ""),
                "source_concept_id": source_concept_id,
            },
            "object_family": "RuntimeProcessRecord",
            "source_class": "DERIVED",
            "status": "LIVE",
            "admissibility_state": "B_ACCEPTED",
            "lineage_refs": [source_concept_id] if source_concept_id else [],
            "witness_refs": [],
        }
        n_added += 1
        source_target = _resolve_existing_target(nodes, source_concept_id)
        if source_target and _append_edge(
            edges, nid, source_target, "ACCEPTED_FROM",
            {"batch_id": survivor.get("provenance", {}).get("batch_id", "")},
        ):
            e_added += 1

    # ─── Bridge Graveyard Records ───
    for i, grav in enumerate(b_state.get("graveyard", [])):
        cid = grav.get("candidate_id", f"UNKNOWN_{i}")
        nid = f"GRAVEYARD_RECORD::{cid}"
        step_trace = grav.get("step_trace", [])
        target_ref = grav.get("target_ref", "")
        source_concept_id = grav.get("source_concept_id", "") or target_ref
        primary_candidate_id = grav.get("primary_candidate_id", "") or target_ref

        nodes[nid] = {
            "id": nid,
            "node_type": "GRAVEYARD_RECORD",
            "layer": LAYER_GRAVEYARD,
            "name": f"GRAVEYARD_{cid}",
            "description": (f"B-killed: [{grav.get('reason_tag', '')}] "
                          f"@ {grav.get('stage', '')}. "
                          f"{grav.get('detail', '')[:120]}"),
            "trust_zone": LAYER_GRAVEYARD,
            "tags": [grav.get("reason_tag", ""), grav.get("failure_class", ""), "EARNED"],
            "authority": "B_REJECTED",
            "properties": {
                "candidate_id": cid,
                "reason_tag": grav.get("reason_tag", ""),
                "failure_class": grav.get("failure_class", ""),
                "stage": grav.get("stage", ""),
                "timestamp_utc": grav.get("timestamp_utc", ""),
                "step_trace_length": len(step_trace),
                "target_ref": target_ref,
                "source_concept_id": source_concept_id,
                "primary_candidate_id": primary_candidate_id,
            },
            "object_family": "RuntimeProcessRecord",
            "source_class": "DERIVED",
            "status": "DEAD",
            "admissibility_state": "B_REJECTED",
            "lineage_refs": [source_concept_id] if source_concept_id else ([] if not target_ref else [target_ref]),
            "witness_refs": [],
        }
        n_added += 1

        # Prefer canonical lineage over raw candidate IDs. Never emit edges to
        # missing raw IDs; that creates dangling projections.
        source_nid = _resolve_existing_target(
            nodes,
            f"B_SURVIVOR::{target_ref}" if target_ref else None,
            source_concept_id,
        )
        if source_nid and _append_edge(
            edges,
            nid,
            source_nid,
            "GRAVEYARD_OF",
            {
                "reason_tag": grav.get("reason_tag", ""),
                "stage": grav.get("stage", ""),
            },
        ):
            e_added += 1

        # BEAT_IN_RATCHET edge: the survivor that beat this alternative
        if primary_candidate_id:
            survivor_nid = f"B_SURVIVOR::{primary_candidate_id}"
            if survivor_nid in nodes and _append_edge(
                edges,
                survivor_nid,
                nid,
                "BEAT_IN_RATCHET",
                {
                    "reason_tag": grav.get("reason_tag", ""),
                    "failure_class": grav.get("failure_class", ""),
                },
            ):
                e_added += 1

    # ─── Bridge SIM Evidence (grouped by target) ───
    evidence_by_target = {}
    for ev in sim_state.get("evidence_log", []):
        tid = ev.get("target_id", "")
        if tid not in evidence_by_target:
            evidence_by_target[tid] = {"passed": 0, "failed": 0, "families": set()}
        if ev.get("outcome") == "PASS":
            evidence_by_target[tid]["passed"] += 1
        else:
            evidence_by_target[tid]["failed"] += 1
        evidence_by_target[tid]["families"].add(ev.get("family", ""))

    for tid, summary in evidence_by_target.items():
        nid = f"SIM_EVIDENCED::{tid}"
        t0_complete = summary["passed"] >= 9 and summary["failed"] == 0

        nodes[nid] = {
            "id": nid,
            "node_type": "SIM_EVIDENCED",
            "layer": LAYER_SIM_EVIDENCED,
            "name": f"SIM_T0_{tid}",
            "description": (f"T0_ATOM evidence: {summary['passed']} PASS / "
                          f"{summary['failed']} FAIL. "
                          f"{'T0 COMPLETE' if t0_complete else 'T0 INCOMPLETE'}"),
            "trust_zone": LAYER_SIM_EVIDENCED,
            "tags": ["T0_ATOM", "EARNED",
                     "T0_COMPLETE" if t0_complete else "T0_INCOMPLETE"],
            "authority": "SIM_T0_EARNED" if t0_complete else "SIM_T0_PARTIAL",
            "properties": {
                "target_id": tid,
                "tier": "T0_ATOM",
                "passed": summary["passed"],
                "failed": summary["failed"],
                "t0_complete": t0_complete,
                "families_tested": sorted(summary["families"]),
            },
            "object_family": "RuntimeProcessRecord",
            "source_class": "DERIVED",
            "status": "LIVE",
            "admissibility_state": "SIM_EVIDENCED",
            "lineage_refs": [],
            "witness_refs": [],
        }
        n_added += 1

        # SIM_EVIDENCE_FOR edge (canonical relation)
        survivor_nid = f"B_SURVIVOR::{tid}"
        if survivor_nid in nodes:
            if _append_edge(
                edges,
                nid,
                survivor_nid,
                "SIM_EVIDENCE_FOR",
                {
                    "tier": "T0_ATOM",
                    "passed": summary["passed"],
                    "failed": summary["failed"],
                },
            ):
                e_added += 1

    # ─── Bridge Witness Refs into SIM evidence nodes ───
    # Prefer explicit target_ids when witness records carry them; otherwise
    # fall back to evidence-log ordering for older persisted states.
    witness_log = sim_state.get("witness_log", [])
    ev_log = sim_state.get("evidence_log", [])
    witness_count_by_target = {}
    explicit_target_ids = [w.get("target_id", "") for w in witness_log if w.get("target_id")]
    if explicit_target_ids:
        for tid in explicit_target_ids:
            witness_count_by_target[tid] = witness_count_by_target.get(tid, 0) + 1
    else:
        witness_idx = 0
        for ev in ev_log:
            tid = ev.get("target_id", "")
            if witness_idx < len(witness_log):
                witness_count_by_target[tid] = witness_count_by_target.get(tid, 0) + 1
                witness_idx += 1
    for tid, wcount in witness_count_by_target.items():
        ev_nid = f"SIM_EVIDENCED::{tid}"
        if ev_nid in nodes:
            nodes[ev_nid]["witness_refs"] = [f"witness_{tid}_{i}" for i in range(wcount)]

    # ─── Bridge intent/context witness corpus into first-class A2 nodes ───
    ic_nodes_added, ic_edges_added = _bridge_intent_context_witnesses(
        nodes, edges, witness_corpus
    )
    n_added += ic_nodes_added
    e_added += ic_edges_added

    # ─── Sync all active registry skills into graph-native SKILL nodes ───
    skill_registry_path = repo / "system_v4" / "a1_state" / "skill_registry_v1.json"
    skill_registry = (
        json.loads(skill_registry_path.read_text()) if skill_registry_path.exists() else {}
    )
    skill_alias_nodes_migrated = 0
    skill_nodes_added = 0
    skill_nodes_refreshed = 0
    skill_related_edges_added = 0
    skill_stale_nodes_removed = 0
    if skill_registry:
        skill_alias_nodes_migrated = _migrate_skill_alias_nodes(
            nodes,
            edges,
            skill_registry,
        )
        (
            skill_nodes_added,
            skill_nodes_refreshed,
            skill_related_edges_added,
        ) = _sync_active_skill_registry_nodes(nodes, edges, skill_registry)
        n_added += skill_nodes_added
        e_added += skill_related_edges_added

    # ─── Bridge SIM Kills ───
    for idx, kill in enumerate(sim_state.get("kill_log", [])):
        kill_nid = f"SIM_KILL::{kill.get('sim_id', '')}::{idx}"
        target_id = kill.get("target_id", "")

        nodes[kill_nid] = {
            "id": kill_nid,
            "node_type": "SIM_KILL",
            "layer": LAYER_GRAVEYARD,
            "name": f"SIM_KILL_{kill.get('target_id', '')}",
            "description": f"SIM kill: {kill.get('detail', '')[:120]}",
            "trust_zone": LAYER_GRAVEYARD,
            "tags": ["SIM_KILL", "EARNED"],
            "authority": "SIM_KILLED",
            "properties": {
                "target_id": kill.get("target_id", ""),
                "failure_mode_id": kill.get("failure_mode_id", ""),
                "replay_manifest_hash": kill.get("replay_manifest_hash", ""),
            },
            "object_family": "RuntimeProcessRecord",
            "source_class": "DERIVED",
            "status": "DEAD",
            "admissibility_state": "SIM_KILLED",
            "lineage_refs": [],
            "witness_refs": [],
        }
        n_added += 1
        survivor_target = _resolve_existing_target(nodes, f"B_SURVIVOR::{target_id}")
        if survivor_target and _append_edge(
            edges,
            kill_nid,
            survivor_target,
            "SIM_KILLED",
            {
                "failure_mode_id": kill.get("failure_mode_id", ""),
            },
        ):
            e_added += 1

    # ─── Bridge Parked Items ───
    for pid, parked in b_state.get("park_set", {}).items():
        nid = f"B_PARKED::{pid}"
        source_concept_id = parked.get("provenance", {}).get("source_concept_id", "")
        primary_candidate_id = parked.get("provenance", {}).get("primary_candidate_id", "")

        nodes[nid] = {
            "id": nid,
            "node_type": "B_PARKED",
            "layer": LAYER_B_ADJUDICATED,
            "name": f"B_PARKED_{pid}",
            "description": f"B-parked: {parked.get('provenance', {}).get('reason', '')[:120]}",
            "trust_zone": LAYER_B_ADJUDICATED,
            "tags": parked.get("tags", []) + ["EARNED"],
            "authority": "B_PARKED",
            "properties": {
                "candidate_id": pid,
                "item_class": parked.get("class", ""),
                "batch_id": parked.get("provenance", {}).get("batch_id", ""),
                "source_concept_id": source_concept_id,
                "primary_candidate_id": primary_candidate_id,
            },
            "object_family": "RuntimeProcessRecord",
            "source_class": "DERIVED",
            "status": "PARKED",
            "admissibility_state": "B_PARKED",
            "lineage_refs": [source_concept_id] if source_concept_id else [],
            "witness_refs": [],
        }
        n_added += 1
        park_target = _resolve_existing_target(nodes, source_concept_id)
        if park_target and _append_edge(
            edges,
            nid,
            park_target,
            "PARKED_FROM",
            {
                "batch_id": parked.get("provenance", {}).get("batch_id", ""),
            },
        ):
            e_added += 1

    # ─── Bridge Term Registry ───
    for term, info in brain_state.get("term_registry", {}).items():
        nid = f"TERM_ADMITTED::{term}"
        bound_math_def = info.get("bound_math_def", "")

        nodes[nid] = {
            "id": nid,
            "node_type": "TERM_ADMITTED",
            "layer": LAYER_TERM_REGISTRY,
            "name": f"TERM_{term}",
            "description": f"Admitted term '{term}' via {info.get('bound_math_def', '')}",
            "trust_zone": LAYER_B_ADJUDICATED,
            "tags": ["TERM_PERMITTED", "EARNED"],
            "authority": "TERM_ADMITTED",
            "properties": {
                "term": term,
                "state": info.get("state", ""),
                "bound_math_def": bound_math_def,
                "provenance": info.get("provenance", ""),
            },
            "object_family": "RuntimeProcessRecord",
            "source_class": "DERIVED",
            "status": "LIVE",
            "admissibility_state": "TERM_ADMITTED",
            "lineage_refs": [],
            "witness_refs": [],
        }
        n_added += 1
        survivor_target = _resolve_existing_target(nodes, f"B_SURVIVOR::{bound_math_def}" if bound_math_def else None)
        if survivor_target and _append_edge(
            edges,
            nid,
            survivor_target,
            "TERM_ADMITTED_FROM",
            {
                "term": term,
            },
        ):
            e_added += 1

    # ─── Fix any remaining CANON authority ───
    canon_fixed = 0
    for nid, n in nodes.items():
        if n.get("authority") == "CANON":
            n["authority"] = "SOURCE_CLAIM"
            canon_fixed += 1

    # ─── Orphan Cleanup Pass ───
    # Fix orphan runtime nodes that lack edges due to pre-lineage batches
    # or stale SKILL nodes from pre-migration names.
    has_outgoing = {e["source_id"] for e in edges}
    has_incoming = {e["target_id"] for e in edges}
    connected = has_outgoing | has_incoming
    orphans_fixed = 0

    # 1. Retire ALL stale SKILL nodes (not in current registry)
    active_skills = {
        skill_id
        for skill_id, record in skill_registry.items()
        if str(record.get("status", "active")) == "active"
    }
    if active_skills:
        edges, skill_stale_nodes_removed = _remove_non_registry_skill_nodes(
            nodes,
            edges,
            active_skills,
        )
        orphans_fixed += skill_stale_nodes_removed
        has_outgoing = {e["source_id"] for e in edges}
        has_incoming = {e["target_id"] for e in edges}
        connected = has_outgoing | has_incoming

    # 1b. Anchor otherwise-isolated skills onto existing hubs.
    # This avoids leaving active operator specs as dead islands while keeping
    # the schema simple and the relation type generic.
    skill_hub_map = {
        "brain-delta-consolidation": "SKILL::ratchet-reweave",
        "closeout-result-ingest": "SKILL::thread-closeout-auditor",
        "codex-automation-controller": "SKILL::run-real-ratchet",
        "external-research-refinery-launcher": "SKILL::a2-brain-refresh",
        "memory-admission-guard": "SKILL::a2-a1-memory-admission-guard",
        "playwright": "SKILL::runtime-graph-bridge",
        "pro-return-instant-audit": "SKILL::ratchet-verify",
        "ratchet-prompt-stack": "SKILL::run-real-ratchet",
        "safe-run-maintenance": "SKILL::ratchet-verify",
        "thread-closeout-auditor": "SKILL::ratchet-verify",
        "thread-dispatch-controller": "SKILL::run-real-ratchet",
        "thread-run-monitor": "SKILL::run-real-ratchet",
    }
    for nid, n in list(nodes.items()):
        if n.get("node_type") != "SKILL" or nid in connected:
            continue
        skill_id = nid.replace("SKILL::", "")
        hub_candidates = [
            skill_hub_map.get(skill_id),
            "SKILL::ratchet-verify",
            "SKILL::run-real-ratchet",
            "SKILL::runtime-graph-bridge",
        ]
        hub = next(
            (candidate for candidate in hub_candidates if candidate and candidate in nodes and candidate != nid),
            None,
        )
        if hub and _append_edge(
            edges,
            nid,
            hub,
            "RELATED_TO",
            {
                "inferred": True,
                "role": "skill_hub",
            },
        ):
            orphans_fixed += 1

    # 2. Link B_PARKED orphans to source concepts via candidate_id
    for nid, n in list(nodes.items()):
        if n.get("node_type") != "B_PARKED" or nid in connected:
            continue
        props = n.get("properties", {})
        cid = props.get("candidate_id", "")
        if not cid:
            cid = nid.replace("B_PARKED::", "") if nid.startswith("B_PARKED::") else ""
        if not cid:
            continue
        # Try to find a source concept this parked item came from
        target = _resolve_existing_target(nodes, props.get("source_concept_id"))
        if not target:
            primary_candidate_id = props.get("primary_candidate_id", "")
            target = _resolve_existing_target(
                nodes,
                f"B_SURVIVOR::{primary_candidate_id}",
                f"B_PARKED::{primary_candidate_id}",
                f"B_SURVIVOR::{cid}",
                f"B_PARKED::{cid}",
                primary_candidate_id,
                cid,
            )
        if target and _append_edge(edges, nid, target, "PARKED_NEAR", {"inferred": True}):
            orphans_fixed += 1

    # 3. Link GRAVEYARD_RECORD orphans to closest matching node
    for nid, n in list(nodes.items()):
        if n.get("node_type") != "GRAVEYARD_RECORD" or nid in connected:
            continue
        props = n.get("properties", {})
        target = _resolve_existing_target(
            nodes,
            props.get("source_concept_id"),
            f"B_PARKED::{props.get('primary_candidate_id', '')}",
            f"B_SURVIVOR::{props.get('target_ref', '')}",
            f"B_PARKED::{props.get('target_ref', '')}",
            props.get("target_ref"),
        )
        relation = "GRAVEYARD_OF"
        if not target:
            target = _resolve_existing_target(
                nodes,
                "SKILL::b-kernel",
                "SKILL::run-real-ratchet",
            )
            relation = "RELATED_TO"
        if target and _append_edge(edges, nid, target, relation, {"inferred": True}):
            orphans_fixed += 1

    # ─── Save ───
    graph["edges"] = edges
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(json.dumps(graph, indent=2))

    return {
        "nodes_added": n_added,
        "edges_added": e_added,
        "intent_context_nodes_added": ic_nodes_added,
        "intent_context_edges_added": ic_edges_added,
        "skill_alias_nodes_migrated": skill_alias_nodes_migrated,
        "skill_registry_nodes_added": skill_nodes_added,
        "skill_registry_nodes_refreshed": skill_nodes_refreshed,
        "skill_registry_related_edges_added": skill_related_edges_added,
        "skill_stale_nodes_removed": skill_stale_nodes_removed,
        "legacy_tagged": legacy_tagged,
        "canon_fixed": canon_fixed,
        "orphans_fixed": orphans_fixed,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
    }


def main():
    import sys
    repo = str(Path(__file__).resolve().parents[2])
    sys.path.insert(0, repo)

    print("Runtime → Graph Bridge (canonical)")
    print("=" * 60)

    stats = bridge_runtime_to_graph(repo, clean=True)

    print(f"  Nodes added:        {stats['nodes_added']}")
    print(f"  Edges added:        {stats['edges_added']}")
    print(f"  Skill aliases moved:{stats['skill_alias_nodes_migrated']}")
    print(f"  Skill stale removed:{stats['skill_stale_nodes_removed']}")
    print(f"  CANON→SOURCE_CLAIM: {stats['canon_fixed']}")
    print(f"  Total nodes:        {stats['total_nodes']}")
    print(f"  Total edges:        {stats['total_edges']}")

    # Verify
    graph_path = Path(repo) / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json"
    graph = json.loads(graph_path.read_text())
    nodes = graph["nodes"]

    type_counts = Counter(n.get("node_type", "") for n in nodes.values())
    layer_counts = Counter(n.get("layer", "MISSING") for n in nodes.values())

    print(f"\n  Bridge node types:")
    for t in ["B_SURVIVOR", "GRAVEYARD_RECORD", "SIM_EVIDENCED",
              "SIM_KILL", "B_PARKED", "TERM_ADMITTED"]:
        print(f"    {t:20s} {type_counts.get(t, 0)}")

    print(f"\n  Nodes missing 'layer': "
          f"{sum(1 for n in nodes.values() if not n.get('layer'))}")

    # Check edges schema
    bad_edges = sum(1 for e in graph["edges"]
                    if "edge_type" in e or ("relation" not in e))
    print(f"  Edges with wrong schema: {bad_edges}")


if __name__ == "__main__":
    main()
