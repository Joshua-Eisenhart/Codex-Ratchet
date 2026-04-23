"""
graveyard_router.py — Graveyard Router and Resurrection Interface

Handles:
  1. INTAKE: Routes REJECT/FAIL items to the graveyard WITH sim evidence
  2. LINKING: Connects survivors to the graveyard items they beat
  3. SIMMING: Graveyard items carry their own sim results (user spec)
  4. RESURRECTION: A1 OP_GRAVEYARD_RESCUE pulls items back for re-attempt
  5. QUERY: Graveyard is queryable by failure class, target ref, reason tag

Architecture per specs:
  - B Kernel (RQ-028, RQ-060..064): rejection records with candidate_id, reason_tag,
    raw_lines, failure_class (B_KILL|SIM_KILL), target_ref
  - Pipeline Spec: graveyard is a core state object, append-only
  - A1 Wiggle (RQ-103): each cycle emits graveyard-seeking alternatives
  - A1 Wiggle: OP_GRAVEYARD_RESCUE has 12% quota, boosted on stall
  - SIM Evidence Spec (RQ-050-052): meaningful survivors require graveyard alternatives
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, List
from dataclasses import dataclass, field, asdict


@dataclass
class GraveyardRecord:
    """A single graveyard entry per the B Kernel Graveyard Write Contract."""
    graveyard_id: str
    candidate_id: str
    candidate_name: str
    reason_tag: str              # Why it was killed
    failure_class: str           # B_KILL or SIM_KILL
    target_ref: Optional[str]    # What it was an alternative to (if applicable)
    raw_lines: List[str]         # Raw evidence lines
    sim_evidence: Dict           # SIM results at time of failure (graveyard items ARE simmed)
    linked_survivor_id: Optional[str] = None   # Which survivor beat this item
    resurrection_attempts: int = 0             # How many times A1 tried to rescue
    resurrection_outcome: Optional[str] = None # Last rescue outcome
    timestamp: str = ""
    properties: Dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class GraveyardRouter:
    """
    Routes failed items to graveyard, links survivors to their beaten alternatives,
    and provides resurrection interface for A1 OP_GRAVEYARD_RESCUE.
    """

    def __init__(self, refinery):
        self.refinery = refinery
        self.records: Dict[str, GraveyardRecord] = {}
        self._load_existing()

    def _load_existing(self):
        """Load any existing graveyard records from the graph."""
        pydantic_nodes = self.refinery.builder.pydantic_model.nodes
        for nid, node in pydantic_nodes.items():
            if node.layer == "GRAVEYARD":
                rec = GraveyardRecord(
                    graveyard_id=nid,
                    candidate_id=node.properties.get("candidate_id", nid),
                    candidate_name=node.name,
                    reason_tag=node.properties.get("reason_tag", "UNKNOWN"),
                    failure_class=node.properties.get("failure_class", "UNKNOWN"),
                    target_ref=node.properties.get("target_ref"),
                    raw_lines=json.loads(node.properties.get("raw_lines", "[]")),
                    sim_evidence=json.loads(node.properties.get("sim_evidence", "{}")),
                    linked_survivor_id=node.properties.get("linked_survivor_id"),
                    resurrection_attempts=int(node.properties.get("resurrection_attempts", 0)),
                    resurrection_outcome=node.properties.get("resurrection_outcome"),
                    timestamp=node.properties.get("timestamp", ""),
                )
                self.records[nid] = rec

    # ─── INTAKE: Route failures to graveyard ────────────────────────────

    def route_to_graveyard(
        self,
        candidate_id: str,
        reason_tag: str,
        failure_class: str,
        raw_lines: List[str],
        sim_evidence: Dict,
        target_ref: Optional[str] = None,
    ) -> str:
        """
        Routes a REJECT/FAIL item to graveyard with full evidence.
        Per RQ-028: Every rejection record must include candidate_id, reason_tag,
        raw_lines, failure_class, target_ref.
        Per user spec: Graveyard items carry their sim results.

        Returns the graveyard record ID.
        """
        pydantic_nodes = self.refinery.builder.pydantic_model.nodes

        # Resolve the candidate node
        found_id = None
        candidate_name = candidate_id
        if candidate_id in pydantic_nodes:
            found_id = candidate_id
            candidate_name = pydantic_nodes[found_id].name
        else:
            for nid, data in pydantic_nodes.items():
                if data.name == candidate_id:
                    found_id = nid
                    candidate_name = data.name
                    break

        # Build graveyard ID
        hash_input = f"{candidate_id}:{reason_tag}:{failure_class}".encode('utf-8')
        short_hash = hashlib.sha256(hash_input).hexdigest()[:12]
        graveyard_id = f"GRAVEYARD::{candidate_name}::{short_hash}"

        if graveyard_id in self.records:
            return graveyard_id

        record = GraveyardRecord(
            graveyard_id=graveyard_id,
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            reason_tag=reason_tag,
            failure_class=failure_class,
            target_ref=target_ref,
            raw_lines=raw_lines,
            sim_evidence=sim_evidence,
        )
        self.records[graveyard_id] = record

        # Write to graph via canonical API
        from system_v4.skills.v4_graph_builder import GraphNode, GraphEdge
        builder = self.refinery.builder

        builder.add_node(GraphNode(
            id=graveyard_id,
            node_type=failure_class,  # Write SIM_KILL or B_KILL directly, not GRAVEYARD_RECORD
            name=f"{candidate_name}_GRAVEYARD",
            description=f"Failed: {reason_tag} ({failure_class})",
            layer="GRAVEYARD",
            trust_zone="GRAVEYARD",
            authority="GRAVEYARD",
            properties={
                "candidate_id": candidate_id,
                "reason_tag": reason_tag,
                "failure_class": failure_class,
                "target_ref": target_ref or "",
                "raw_lines": json.dumps(raw_lines),
                "sim_evidence": json.dumps(sim_evidence),
                "resurrection_attempts": "0",
                "timestamp": record.timestamp,
            }
        ))

        # Edge: graveyard record -> the original candidate
        if found_id:
            builder.add_edge(GraphEdge(
                source_id=graveyard_id, target_id=found_id,
                relation="GRAVEYARD_OF", attributes={}
            ))

        self.refinery.log_finding(
            f"GRAVEYARD INTAKE: {candidate_name} -> {failure_class} ({reason_tag})"
        )
        self.refinery._save()
        return graveyard_id

    def route_parked(
        self,
        candidate_id: str,
        reason_tag: str,
        raw_lines: List[str],
        target_ref: Optional[str] = None
    ) -> str:
        """Explicitly tracks and deposits B_PARKED nodes into structural memory."""
        from system_v4.skills.v4_graph_builder import GraphNode, GraphEdge
        builder = self.refinery.builder
        node_id = f"PARKED::{candidate_id}"
        
        builder.add_node(GraphNode(
            id=node_id,
            node_type="B_PARKED",
            name=f"{candidate_id}_PARKED",
            description=f"Parked: {reason_tag}",
            layer="GRAVEYARD",
            trust_zone="GRAVEYARD",
            authority="B_PARKED",
            properties={
                "candidate_id": candidate_id,
                "reason_tag": reason_tag,
                "target_ref": target_ref or "",
                "raw_lines": json.dumps(raw_lines)
            }
        ))
        # Point park back to candidate
        from system_v4.skills.v4_graph_builder import GraphEdge
        builder.add_edge(GraphEdge(
            source_id=node_id, target_id=candidate_id,
            relation="PARKED_VERSION_OF", attributes={}
        ))
        self.refinery._save()
        return node_id

    def route_survivor(self, candidate_id: str) -> str:
        """Explicitly tracks B_SURVIVOR nodes into structural memory."""
        from system_v4.skills.v4_graph_builder import GraphNode, GraphEdge
        builder = self.refinery.builder
        node_id = f"SURVIVOR::{candidate_id}"
        builder.add_node(GraphNode(
            id=node_id,
            node_type="B_SURVIVOR",
            name=f"{candidate_id}_SURVIVOR",
            description=f"Survivor: Admitted to B Kernel",
            layer="B_ADJUDICATED",
            trust_zone="B_ADJUDICATED",
            authority="B_ACCEPTED",
            properties={"candidate_id": candidate_id}
        ))
        from system_v4.skills.v4_graph_builder import GraphEdge
        builder.add_edge(GraphEdge(
            source_id=node_id, target_id=candidate_id,
            relation="SURVIVOR_VERSION_OF", attributes={}
        ))
        self.refinery._save()
        return node_id

    # ─── LINKING: Connect survivors to graveyard ────────────────────────

    def link_survivor_to_graveyard(self, survivor_id: str, graveyard_id: str):
        """
        Per RQ-050-052 + RQ-064: meaningful survivors must carry explicit links
        to graveyard alternative ids. A survivor only means something because
        its alternatives died with evidence.
        """
        if graveyard_id not in self.records:
            print(f"Error: Graveyard record {graveyard_id} not found.")
            return

        self.records[graveyard_id].linked_survivor_id = survivor_id

        # Update graph via canonical API
        builder = self.refinery.builder
        builder.update_node(graveyard_id, 
            properties={**builder.get_node(graveyard_id).properties, "linked_survivor_id": survivor_id}
        )

        from system_v4.skills.v4_graph_builder import GraphEdge
        builder.add_edge(GraphEdge(
            source_id=survivor_id, target_id=graveyard_id,
            relation="BEAT_IN_RATCHET", attributes={}
        ))

        self.refinery.log_finding(
            f"SURVIVOR LINKED: {survivor_id} beats {graveyard_id}"
        )
        self.refinery._save()

    # ─── RESURRECTION: A1 OP_GRAVEYARD_RESCUE ───────────────────────────

    def get_rescue_candidates(
        self,
        failure_class: Optional[str] = None,
        max_attempts: int = 3,
        limit: int = 10,
    ) -> List[GraveyardRecord]:
        """
        Returns graveyard items eligible for A1 rescue.
        Per A1 Wiggle spec: OP_GRAVEYARD_RESCUE gets 12% quota.
        Items with too many failed resurrection attempts are deprioritized.
        """
        candidates = []
        for rec in self.records.values():
            if rec.resurrection_attempts >= max_attempts:
                continue
            if failure_class and rec.failure_class != failure_class:
                continue
            candidates.append(rec)

        # Sort: fewest resurrection attempts first, then by timestamp (oldest first)
        candidates.sort(key=lambda r: (r.resurrection_attempts, r.timestamp))
        return candidates[:limit]

    def attempt_resurrection(self, graveyard_id: str, outcome: str) -> bool:
        """
        Records a resurrection attempt by A1. 
        outcome: "RESCUED" (re-entered pipeline) or "FAILED_AGAIN" (stays in graveyard)
        """
        if graveyard_id not in self.records:
            print(f"Error: Graveyard record {graveyard_id} not found.")
            return False

        rec = self.records[graveyard_id]
        rec.resurrection_attempts += 1
        rec.resurrection_outcome = outcome

        # Update graph via canonical API
        builder = self.refinery.builder
        node = builder.get_node(graveyard_id)
        if node:
            props = {**node.properties}
            props["resurrection_attempts"] = str(rec.resurrection_attempts)
            props["resurrection_outcome"] = outcome
            builder.update_node(graveyard_id, properties=props)

        self.refinery.log_finding(
            f"RESURRECTION ATTEMPT #{rec.resurrection_attempts}: {rec.candidate_name} -> {outcome}"
        )
        self.refinery._save()
        return True

    # ─── QUERY: Graveyard inspection ─────────────────────────────────────

    def query_by_failure_class(self, failure_class: str) -> List[GraveyardRecord]:
        return [r for r in self.records.values() if r.failure_class == failure_class]

    def query_by_target_ref(self, target_ref: str) -> List[GraveyardRecord]:
        return [r for r in self.records.values() if r.target_ref == target_ref]

    def query_by_reason_tag(self, reason_tag: str) -> List[GraveyardRecord]:
        return [r for r in self.records.values() if r.reason_tag == reason_tag]

    def get_alternatives_for_survivor(self, survivor_id: str) -> List[GraveyardRecord]:
        """Get all graveyard items that a specific survivor beat."""
        return [r for r in self.records.values() if r.linked_survivor_id == survivor_id]

    def summary(self) -> Dict:
        """Summary stats for the graveyard."""
        total = len(self.records)
        b_kills = sum(1 for r in self.records.values() if r.failure_class == "B_KILL")
        sim_kills = sum(1 for r in self.records.values() if r.failure_class == "SIM_KILL")
        rescued = sum(1 for r in self.records.values() if r.resurrection_outcome == "RESCUED")
        linked = sum(1 for r in self.records.values() if r.linked_survivor_id is not None)
        return {
            "total_records": total,
            "b_kills": b_kills,
            "sim_kills": sim_kills,
            "rescued": rescued,
            "linked_to_survivors": linked,
            "unlinked": total - linked,
        }
