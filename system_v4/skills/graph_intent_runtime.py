"""
graph_intent_runtime.py — Graph-Driven Intent Runtime

Implements the primitives from jp graph prompt!!.txt:
  - The graph is the truth
  - Messages are observations, not facts
  - Every response is a proposal against the graph
  - Nothing is final until accepted

Primitives:
  Entity   — noun with lifecycle (ephemeral → proposed → accepted → stale → rejected)
  Intent   — inferred directional pressure (exploration, clarification, synthesis, execution, validation)
  Relation — edge between entities
  Proposal — suggested graph change (add, update, link, mark_stale)
  Patch    — concrete graph mutation (only after acceptance)
  Tick     — one conceptual heartbeat advancing the graph

This skill is the operating model for the A2 brain's graph layer.
It replaces static file-tracking with live proposal-based graph mutation.
"""

from __future__ import annotations

import json
import time
import hashlib
from pathlib import Path
from typing import Any, Optional
from enum import Enum


class EntityState(str, Enum):
    EPHEMERAL = "ephemeral"      # exists only in this turn
    PROPOSED = "proposed"        # suggested, not applied
    ACCEPTED = "accepted"        # committed to graph
    REJECTED = "rejected"        # discarded
    STALE = "stale"              # valid but outdated


class IntentVector(str, Enum):
    EXPLORATION = "exploration"
    CLARIFICATION = "clarification"
    SYNTHESIS = "synthesis"
    EXECUTION = "execution"
    VALIDATION = "validation"


class ProposalType(str, Enum):
    ADD = "add"
    UPDATE = "update"
    LINK = "link"
    MARK_STALE = "mark_stale"
    DELETE = "delete"


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _nid(prefix: str, name: str) -> str:
    raw = f"{prefix}::{name}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class Entity:
    """A first-class graph entity with lifecycle state."""

    def __init__(self, name: str, entity_type: str, state: EntityState = EntityState.PROPOSED,
                 attributes: dict[str, Any] | None = None):
        self.id = _nid(entity_type, name)
        self.name = name
        self.entity_type = entity_type
        self.state = state
        self.attributes = attributes or {}
        self.created_utc = _utc()
        self.updated_utc = self.created_utc

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type,
            "state": self.state.value,
            "attributes": self.attributes,
            "created_utc": self.created_utc,
            "updated_utc": self.updated_utc,
        }


class Relation:
    """An edge between entities."""

    def __init__(self, source_id: str, target_id: str, relation_type: str,
                 state: EntityState = EntityState.PROPOSED,
                 attributes: dict[str, Any] | None = None):
        self.source_id = source_id
        self.target_id = target_id
        self.relation_type = relation_type
        self.state = state
        self.attributes = attributes or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type,
            "state": self.state.value,
            "attributes": self.attributes,
        }


class Proposal:
    """A suggested graph change. Reasoning ≠ proposal ≠ patch ≠ acceptance."""

    _counter = 0

    def __init__(self, proposal_type: ProposalType, target: str,
                 rationale: str, changes: dict[str, Any],
                 intent: IntentVector | None = None):
        Proposal._counter += 1
        self.proposal_id = f"PROP_{Proposal._counter:06d}"
        self.proposal_type = proposal_type
        self.target = target
        self.rationale = rationale
        self.changes = changes
        self.intent = intent or IntentVector.SYNTHESIS
        self.status: EntityState = EntityState.PROPOSED
        self.created_utc = _utc()

    def accept(self) -> "Proposal":
        self.status = EntityState.ACCEPTED
        return self

    def reject(self) -> "Proposal":
        self.status = EntityState.REJECTED
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "type": self.proposal_type.value,
            "target": self.target,
            "rationale": self.rationale,
            "changes": self.changes,
            "intent": self.intent.value,
            "status": self.status.value,
            "created_utc": self.created_utc,
        }


class GraphIntentRuntime:
    """
    The graph-driven intent runtime.

    The graph is the truth.
    Messages are observations, not facts.
    Every response is a proposal against the graph.
    Nothing is final until accepted.
    """

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()
        self.graph_path = self.workspace_root / "system_v4" / "a2_state" / "graphs" / "system_architecture_v1.json"
        self.proposals_path = self.workspace_root / "system_v4" / "a2_state" / "proposals.jsonl"
        self.tick_count = 0

        # Live state
        self._graph: dict[str, Any] | None = None
        self._pending_proposals: list[Proposal] = []

    def load_graph(self) -> dict[str, Any]:
        """Load the graph truth."""
        if self._graph is None:
            if self.graph_path.exists():
                with self.graph_path.open() as f:
                    self._graph = json.load(f)
            else:
                self._graph = {"nodes": {}, "edges": [], "stats": {}}
        return self._graph

    # ── INTENT INFERENCE ──────────────────────────────────────────────────
    def infer_intent(self, message: str) -> list[IntentVector]:
        """
        Infer intent vectors from a message.
        Intent > Goal. Do not assume user goals.
        """
        intents = []
        msg = message.lower()

        if any(w in msg for w in ["what", "how", "where", "explore", "understand", "dig", "read"]):
            intents.append(IntentVector.EXPLORATION)
        if any(w in msg for w in ["why", "explain", "clarify", "mean", "difference"]):
            intents.append(IntentVector.CLARIFICATION)
        if any(w in msg for w in ["build", "create", "make", "wire", "connect", "integrate", "process"]):
            intents.append(IntentVector.SYNTHESIS)
        if any(w in msg for w in ["run", "execute", "do", "implement", "fix", "deploy"]):
            intents.append(IntentVector.EXECUTION)
        if any(w in msg for w in ["test", "verify", "check", "audit", "validate", "prove"]):
            intents.append(IntentVector.VALIDATION)

        return intents or [IntentVector.EXPLORATION]

    # ── PROPOSAL ENGINE ───────────────────────────────────────────────────
    def propose_add_entity(self, name: str, entity_type: str,
                           rationale: str, attributes: dict[str, Any] | None = None,
                           intent: IntentVector | None = None) -> Proposal:
        """Propose adding a new entity to the graph."""
        entity = Entity(name, entity_type, EntityState.PROPOSED, attributes)
        prop = Proposal(
            ProposalType.ADD, name, rationale,
            {"entity": entity.to_dict()}, intent,
        )
        self._pending_proposals.append(prop)
        return prop

    def propose_add_relation(self, source: str, target: str, relation_type: str,
                             rationale: str, attributes: dict[str, Any] | None = None,
                             intent: IntentVector | None = None) -> Proposal:
        """Propose adding a new relation to the graph."""
        rel = Relation(source, target, relation_type, EntityState.PROPOSED, attributes)
        prop = Proposal(
            ProposalType.LINK, f"{source}->{target}", rationale,
            {"relation": rel.to_dict()}, intent,
        )
        self._pending_proposals.append(prop)
        return prop

    def propose_mark_stale(self, entity_name: str, rationale: str,
                           intent: IntentVector | None = None) -> Proposal:
        """Propose marking an entity as stale."""
        prop = Proposal(
            ProposalType.MARK_STALE, entity_name, rationale,
            {"new_state": EntityState.STALE.value}, intent,
        )
        self._pending_proposals.append(prop)
        return prop

    def propose_update(self, entity_name: str, rationale: str,
                       updates: dict[str, Any],
                       intent: IntentVector | None = None) -> Proposal:
        """Propose updating an entity's attributes."""
        prop = Proposal(
            ProposalType.UPDATE, entity_name, rationale,
            {"updates": updates}, intent,
        )
        self._pending_proposals.append(prop)
        return prop

    # ── PATCH APPLICATION ─────────────────────────────────────────────────
    def apply_accepted_proposals(self) -> dict[str, Any]:
        """
        Apply all accepted proposals as patches to the graph.
        Reasoning ≠ proposal. Proposal ≠ patch. Patch ≠ acceptance.
        """
        graph = self.load_graph()
        applied = []
        rejected = []

        for prop in self._pending_proposals:
            if prop.status != EntityState.ACCEPTED:
                if prop.status == EntityState.PROPOSED:
                    # Auto-accept system proposals
                    prop.accept()
                else:
                    rejected.append(prop.to_dict())
                    continue

            if prop.proposal_type == ProposalType.ADD:
                entity_data = prop.changes.get("entity", {})
                nid = entity_data.get("id", _nid(entity_data.get("entity_type", "?"), prop.target))
                graph["nodes"][nid] = {
                    "node_type": entity_data.get("entity_type", "UNKNOWN"),
                    "name": entity_data.get("name", prop.target),
                    "state": EntityState.ACCEPTED.value,
                    "attributes": entity_data.get("attributes", {}),
                }
                applied.append(prop.to_dict())

            elif prop.proposal_type == ProposalType.LINK:
                rel_data = prop.changes.get("relation", {})
                graph["edges"].append({
                    "source": rel_data.get("source_id", ""),
                    "target": rel_data.get("target_id", ""),
                    "relation": rel_data.get("relation_type", "RELATED"),
                    "state": EntityState.ACCEPTED.value,
                    "attributes": rel_data.get("attributes", {}),
                })
                applied.append(prop.to_dict())

            elif prop.proposal_type == ProposalType.MARK_STALE:
                # Find and mark the entity
                for nid, ndata in graph["nodes"].items():
                    if ndata.get("name") == prop.target:
                        ndata["state"] = EntityState.STALE.value
                        applied.append(prop.to_dict())
                        break

            elif prop.proposal_type == ProposalType.UPDATE:
                for nid, ndata in graph["nodes"].items():
                    if ndata.get("name") == prop.target:
                        ndata.update(prop.changes.get("updates", {}))
                        applied.append(prop.to_dict())
                        break

        # Log proposals
        self._log_proposals(applied + rejected)

        # Clear pending
        self._pending_proposals.clear()

        return {
            "applied": len(applied),
            "rejected": len(rejected),
            "graph_nodes": len(graph["nodes"]),
            "graph_edges": len(graph["edges"]),
        }

    def _log_proposals(self, proposals: list[dict[str, Any]]) -> None:
        """Append proposals to the proposals log."""
        self.proposals_path.parent.mkdir(parents=True, exist_ok=True)
        with self.proposals_path.open("a", encoding="utf-8") as f:
            for p in proposals:
                f.write(json.dumps(p, separators=(",", ":")) + "\n")

    # ── TICK ──────────────────────────────────────────────────────────────
    def tick(self, message: str | None = None) -> dict[str, Any]:
        """
        One conceptual heartbeat. Advances the graph by one meaningful step.
        Do NOT dump the full system. Advance by one step.
        """
        self.tick_count += 1
        intents = self.infer_intent(message) if message else [IntentVector.SYNTHESIS]
        result = self.apply_accepted_proposals()

        return {
            "tick": self.tick_count,
            "timestamp": _utc(),
            "intents": [i.value for i in intents],
            "patches_applied": result["applied"],
            "patches_rejected": result["rejected"],
            "graph_size": {
                "nodes": result["graph_nodes"],
                "edges": result["graph_edges"],
            },
        }

    # ── DEBUG FOOTER ──────────────────────────────────────────────────────
    def debug_footer(self, message: str, entities_touched: list[str],
                     next_ticks: list[str]) -> dict[str, Any]:
        """
        Required response structure: a machine-facing debug/proposal footer.
        A user reading later should be able to reconstruct the graph from this trail.
        """
        return {
            "observed": {"message_summary": message[:200]},
            "inferred_intent": [i.value for i in self.infer_intent(message)],
            "entities_touched": entities_touched,
            "proposed_changes": [p.to_dict() for p in self._pending_proposals],
            "patch_status": "proposed",
            "next_possible_ticks": next_ticks,
        }

    # ── GRAPH QUERIES ─────────────────────────────────────────────────────
    def entities_by_state(self, state: EntityState) -> list[dict[str, Any]]:
        """Find all entities in a given state."""
        graph = self.load_graph()
        return [
            {"id": nid, **ndata}
            for nid, ndata in graph["nodes"].items()
            if ndata.get("state") == state.value
        ]

    def stale_entities(self) -> list[dict[str, Any]]:
        """Find all stale entities — valid but outdated."""
        return self.entities_by_state(EntityState.STALE)

    def pending_proposals(self) -> list[dict[str, Any]]:
        """Return all pending proposals."""
        return [p.to_dict() for p in self._pending_proposals]

    def save_graph(self) -> None:
        """Persist the graph truth to disk."""
        if self._graph is not None:
            with self.graph_path.open("w", encoding="utf-8") as f:
                json.dump(self._graph, f, indent=2)
