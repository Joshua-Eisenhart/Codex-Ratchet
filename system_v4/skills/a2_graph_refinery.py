"""
A2 Graph Refinery — V4.1

The upgraded A2 refinery with a 12-layer architecture reflecting the full
system pipeline from raw file index through ratcheted knowledge.

Layer stack (outer → inner):
  INDEX         — pre-A2 file catalog, document index
  A2_HIGH       — actual reading, claim identification, entropy-tagged intake
  A2_MID        — cross-validation, contradiction detection, entropy reduction
  A2_LOW        — distilled control surfaces, structural understanding
  A1_JARGONED   — source concepts in original dialect, Rosetta input
  A1_STRIPPED   — Rosetta cold-core output, pure math objects
  A1_CARTRIDGE  — full ratchet-ready strategy with sims/alts/graveyard plans
  A0_COMPILED   — deterministic EXPORT_BLOCK compilation
  B_ADJUDICATED — ACCEPT/PARK/REJECT outcome from B kernel
  SIM_EVIDENCED — positive + negative + stress family evidence
  GRAVEYARD     — structural memory, heat reservoir, dependency graph

Thermodynamic principle: every layer manages heat (entropy) bidirectionally.
Induction brings in possibilities, deduction reduces them. The graveyard
retains heat so the system never freezes. A2 boundary emits waste heat.

Self-similarity: The nested layers mirror the nested Hopf tori of
the physics engine. The system that reasons about the engine is built
in the same topology as the engine itself. The system bootstraps:
ratcheted concepts improve the refinery that ratchets them.

Nothing is canon until ratcheted through B + SIM + graveyard.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from system_v4.skills.v4_graph_builder import (
    GraphEdge,
    GraphNode,
    SystemGraphBuilder,
)
from system_v4.skills.graph_store import load_graph_json


# ── Layer Definitions ──────────────────────────────────────────────────

class RefineryLayer(str, Enum):
    # Pre-A2: file catalog / document index
    INDEX         = "INDEX"

    # A2 layers (mining — gold extraction)
    A2_HIGH       = "A2_HIGH_INTAKE"       # raw document reading, claim ID
    A2_MID        = "A2_MID_REFINEMENT"    # cross-validation, contradictions
    A2_LOW        = "A2_LOW_CONTROL"       # distilled control surfaces

    # A1 layers (smelting — impurity removal)
    A1_JARGONED   = "A1_JARGONED"          # source concepts in original dialect
    A1_STRIPPED   = "A1_STRIPPED"           # Rosetta cold-core output, pure math
    A1_CARTRIDGE  = "A1_CARTRIDGE"          # ratchet-ready strategy w/ sims+alts

    # Lower layers (ratchet pipeline)
    A0_COMPILED   = "A0_COMPILED"           # deterministic EXPORT_BLOCK
    B_ADJUDICATED = "B_ADJUDICATED"         # ACCEPT/PARK/REJECT outcome
    SIM_EVIDENCED = "SIM_EVIDENCED"         # positive + negative + stress
    GRAVEYARD     = "GRAVEYARD"             # structural memory, heat reservoir

    # ── Backward-compatible aliases for existing graph nodes ──
    A2_3_INTAKE    = "A2_3_INTAKE"          # alias → maps to A2_HIGH
    A2_2_CANDIDATE = "A2_2_CANDIDATE"       # alias → maps to A2_MID
    A2_1_KERNEL    = "A2_1_KERNEL"          # alias → maps to A2_LOW


# Mapping from old 3-layer names to new expanded layers
LAYER_MIGRATION = {
    "A2_3_INTAKE":    "A2_HIGH_INTAKE",
    "A2_2_CANDIDATE": "A2_MID_REFINEMENT",
    "A2_1_KERNEL":    "A2_LOW_CONTROL",
}


LAYER_ADMISSIBILITY = {
    RefineryLayer.INDEX:         "CATALOGED",
    RefineryLayer.A2_HIGH:       "PROPOSAL_ONLY",
    RefineryLayer.A2_MID:        "PROPOSAL_ONLY",
    RefineryLayer.A2_LOW:        "PROPOSAL_ONLY",
    RefineryLayer.A1_JARGONED:   "PROPOSAL_ONLY",
    RefineryLayer.A1_STRIPPED:   "PROPOSAL_ONLY",
    RefineryLayer.A1_CARTRIDGE:  "RATCHET_READY",
    RefineryLayer.A0_COMPILED:   "COMPILED",
    RefineryLayer.B_ADJUDICATED: "ADJUDICATED",
    RefineryLayer.SIM_EVIDENCED: "EVIDENCED",
    RefineryLayer.GRAVEYARD:     "STRUCTURAL_MEMORY",
    # Backward-compat aliases
    RefineryLayer.A2_3_INTAKE:   "PROPOSAL_ONLY",
    RefineryLayer.A2_2_CANDIDATE: "PROPOSAL_ONLY",
    RefineryLayer.A2_1_KERNEL:   "ADMITTED",
}


# ── Authority Levels (entropy-gradient, not canon-claim) ──────────────
# Nothing is CANON until ratcheted through B + SIM + graveyard.

AUTHORITY_LEVELS = ("SOURCE_CLAIM", "CROSS_VALIDATED", "STRIPPED", "RATCHETED")

# Legacy alias for backward compatibility
LEGACY_AUTHORITY = {"CANON": "SOURCE_CLAIM", "DRAFT": "SOURCE_CLAIM", "NONCANON": "SOURCE_CLAIM"}


# ── Extraction Modes ──────────────────────────────────────────────────

class ExtractionMode(str, Enum):
    SOURCE_MAP           = "SOURCE_MAP_PASS"
    TERM_CONFLICT        = "TERM_CONFLICT_PASS"
    ENGINE_PATTERN       = "ENGINE_PATTERN_PASS"
    MATH_CLASS           = "MATH_CLASS_PASS"
    QIT_BRIDGE           = "QIT_BRIDGE_PASS"
    PERSONALITY_ANALOGY  = "PERSONALITY_ANALOGY_PASS"
    CONTRADICTION_REPROCESS = "CONTRADICTION_REPROCESS_PASS"


# ── Batch Record ──────────────────────────────────────────────────────

@dataclass
class RefineryBatch:
    batch_id: str
    layer: RefineryLayer
    extraction_mode: ExtractionMode
    source_paths: list[str]
    node_ids: list[str] = field(default_factory=list)
    edge_ids: list[str] = field(default_factory=list)
    promotion_status: str = "QUARANTINED"
    parent_batch_ids: list[str] = field(default_factory=list)
    created_utc: str = ""
    jargon_warnings: list[str] = field(default_factory=list)  # Gap 4

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "layer": self.layer.value,
            "extraction_mode": self.extraction_mode.value,
            "source_paths": self.source_paths,
            "node_ids": self.node_ids,
            "edge_ids": self.edge_ids,
            "promotion_status": self.promotion_status,
            "parent_batch_ids": self.parent_batch_ids,
            "created_utc": self.created_utc,
            "jargon_warnings": self.jargon_warnings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RefineryBatch":
        """Reconstruct a RefineryBatch from a serialized dict."""
        return cls(
            batch_id=data["batch_id"],
            layer=RefineryLayer(data["layer"]),
            extraction_mode=ExtractionMode(data["extraction_mode"]),
            source_paths=data.get("source_paths", []),
            node_ids=data.get("node_ids", []),
            edge_ids=data.get("edge_ids", []),
            promotion_status=data.get("promotion_status", "QUARANTINED"),
            parent_batch_ids=data.get("parent_batch_ids", []),
            created_utc=data.get("created_utc", ""),
            jargon_warnings=data.get("jargon_warnings", []),
        )


# ── Session Logger ────────────────────────────────────────────────────
# Gap 5: Session logging

@dataclass
class SessionState:
    session_id: str
    start_utc: str
    docs_processed: list[str] = field(default_factory=list)
    batches_created: list[str] = field(default_factory=list)
    nodes_added: int = 0
    edges_added: int = 0
    contradictions_found: int = 0
    checkpoints: int = 0
    findings: list[str] = field(default_factory=list)


# ── Refinery Engine ───────────────────────────────────────────────────

class A2GraphRefinery:
    """
    Manages the 12-layer nested graph refinery.

    Layer stack: INDEX → A2_HIGH/MID/LOW → A1_JARGONED/STRIPPED/CARTRIDGE
    → A0 → B → SIM → GRAVEYARD

    Each layer is a trust_zone boundary in the master graph.
    Promotion between layers is explicit and fail-closed.
    Nothing is canon until ratcheted through B + SIM + graveyard.
    """

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()
        self.builder = SystemGraphBuilder(workspace_root)
        self.batches: list[RefineryBatch] = []
        self.batch_index_path = (
            self.workspace_root
            / "system_v4"
            / "a2_state"
            / "refinery_batch_index.json"
        )
        self.refinery_witness_path = (
            self.workspace_root
            / "system_v4"
            / "a2_state"
            / "refinery_witness_corpus_v1.json"
        )
        self.session_log_dir = (
            self.workspace_root
            / "system_v4"
            / "a2_state"
            / "session_logs"
        )
        self._active_session: Optional[SessionState] = None
        self._load_existing_graph()
        self._load_batch_index()  # Gap 1: reload batches from disk

    def _utc_iso(self) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def _content_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def _normalize_name(self, name: str) -> str:
        """Normalize a concept name for dedup comparison."""
        return name.strip().lower().replace(" ", "_").replace("-", "_")

    def _load_existing_graph(self) -> None:
        self.builder.load_graph_artifacts(version_label="a2_refinery")

    # ── Gap 1: Batch Index Reload ─────────────────────────────────────

    def _load_batch_index(self) -> None:
        """Reload batch records from disk so resumed sessions keep history."""
        if not self.batch_index_path.exists():
            return
        try:
            data = json.loads(
                self.batch_index_path.read_text(encoding="utf-8")
            )
            if isinstance(data, list):
                self.batches = [RefineryBatch.from_dict(d) for d in data]
        except (json.JSONDecodeError, KeyError, ValueError):
            # Corrupted index — start fresh but don't overwrite yet
            self.batches = []

    def _save(self) -> None:
        self.builder.save_graph_artifacts(version_label="a2_refinery")
        self._save_batch_index()

    def _save_batch_index(self) -> None:
        import os, tempfile
        self.batch_index_path.parent.mkdir(parents=True, exist_ok=True)
        data = [b.to_dict() for b in self.batches]
        content = json.dumps(data, indent=2, sort_keys=True) + "\n"
        # Atomic write: tmp → rename
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(self.batch_index_path.parent), suffix=".tmp"
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp_path, str(self.batch_index_path))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    # ── Gap 2: Query / Search Tools ───────────────────────────────────

    def find_nodes(
        self,
        layer: Optional[RefineryLayer] = None,
        name_contains: Optional[str] = None,
        tags_any: Optional[list[str]] = None,
    ) -> list[dict[str, str]]:
        """
        Search graph nodes by layer, name substring, or tags.
        Returns list of {id, name, layer, node_type} dicts.
        """
        results = []
        for node in self.builder.pydantic_model.nodes.values():
            if layer is not None and node.trust_zone != layer.value:
                continue
            if name_contains is not None:
                if name_contains.lower() not in node.name.lower():
                    continue
            if tags_any is not None:
                # Read from top-level tags first, fall back to properties for old nodes
                node_tags = node.tags if node.tags else node.properties.get("tags", [])
                if not any(t in node_tags for t in tags_any):
                    continue
            results.append({
                "id": node.id,
                "name": node.name,
                "layer": node.trust_zone,
                "node_type": node.node_type,
            })
        return results

    def find_edges(
        self,
        relation_type: Optional[str] = None,
        source_layer: Optional[str] = None,
        target_layer: Optional[str] = None,
    ) -> list[dict[str, str]]:
        """Search graph edges by relation type or trust zone."""
        results = []
        for edge in self.builder.pydantic_model.edges:
            if relation_type is not None and edge.relation != relation_type:
                continue
            if source_layer is not None and edge.trust_zone != source_layer:
                continue
            results.append({
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "relation": edge.relation,
                "trust_zone": edge.trust_zone,
            })
        return results

    # Extensions that should NEVER be ingested as source documents.
    # .graphml exports were accidentally re-ingested as "Unprocessed File Type" nodes.
    EXCLUDED_EXTENSIONS = {
        ".graphml", ".tmp", ".pyc", ".pyo", ".DS_Store",
        ".json.tmp", ".graphml.tmp",
    }

    # Generic names that should NOT trigger dedup (cause semantic collapse)
    GENERIC_NAMES = {
        "readme", "manifest_json", "manifest", "changelog", "license", "index",
        "setup", "config", "main", "test", "utils", "init", "makefile",
        "dockerfile", "requirements", "package_json", "gitignore", "todo",
        "contributing", "authors", "history", "v3surf_manifest",
    }

    def concept_exists(
        self,
        name: str,
        layer: Optional[RefineryLayer] = None,
    ) -> Optional[str]:
        """
        Check if a concept with a similar name already exists.
        Returns the existing node ID if found, None otherwise.
        Uses normalized name comparison (lowercase, collapsed underscores).
        Skips generic/common names to prevent semantic collapse.
        """
        target = self._normalize_name(name)
        # Skip generic names — they cause false dedup
        if target in self.GENERIC_NAMES or len(target) < 4:
            return None
        for node in self.builder.pydantic_model.nodes.values():
            if layer is not None and node.trust_zone != layer.value:
                continue
            if node.node_type not in (
                "EXTRACTED_CONCEPT", "REFINED_CONCEPT", "KERNEL_CONCEPT"
            ):
                continue
            if self._normalize_name(node.name) == target:
                return node.id
        return None

    # ── Gap 4: Jargon Warning ─────────────────────────────────────────

    def warn_jargon(self, batch_id: str, warning: str) -> bool:
        """Attach a jargon warning to a batch. Returns True if batch found."""
        for batch in self.batches:
            if batch.batch_id == batch_id:
                batch.jargon_warnings.append(warning)
                self._save_batch_index()
                return True
        return False

    # ── Gap 5: Session Logging ────────────────────────────────────────

    def start_session(self, session_id: Optional[str] = None) -> str:
        """Start a new extraction session. Returns the session ID."""
        if session_id is None:
            session_id = f"SESSION_{time.strftime('%Y-%m-%d', time.gmtime())}_{self._content_hash(str(time.time()))[:6]}"
        self._active_session = SessionState(
            session_id=session_id,
            start_utc=self._utc_iso(),
        )
        return session_id

    def log_finding(self, finding: str) -> None:
        """Log a notable finding during the session."""
        if self._active_session:
            self._active_session.findings.append(finding)

    def end_session(self) -> Optional[str]:
        """
        End the current session and write the session log.
        Returns the path to the session log file.
        """
        if self._active_session is None:
            return None

        s = self._active_session
        self.session_log_dir.mkdir(parents=True, exist_ok=True)
        log_path = self.session_log_dir / f"{s.session_id}.md"

        lines = [
            f"# {s.session_id}",
            f"",
            f"- **Start:** {s.start_utc}",
            f"- **End:** {self._utc_iso()}",
            f"- **Documents processed:** {len(s.docs_processed)}",
            f"- **Batches created:** {len(s.batches_created)}",
            f"- **Nodes added:** {s.nodes_added}",
            f"- **Edges added:** {s.edges_added}",
            f"- **Contradictions found:** {s.contradictions_found}",
            f"- **Checkpoints:** {s.checkpoints}",
            f"",
            f"## Graph Totals",
            f"- INDEX: {self.get_layer_node_count(RefineryLayer.INDEX)} nodes",
            f"- A2_HIGH: {self.get_layer_node_count(RefineryLayer.A2_HIGH)} nodes",
            f"- A2_MID: {self.get_layer_node_count(RefineryLayer.A2_MID)} nodes",
            f"- A2_LOW: {self.get_layer_node_count(RefineryLayer.A2_LOW)} nodes",
            f"- A1_JARGONED: {self.get_layer_node_count(RefineryLayer.A1_JARGONED)} nodes",
            f"- A1_STRIPPED: {self.get_layer_node_count(RefineryLayer.A1_STRIPPED)} nodes",
            f"- A1_CARTRIDGE: {self.get_layer_node_count(RefineryLayer.A1_CARTRIDGE)} nodes",
            f"- GRAVEYARD: {self.get_layer_node_count(RefineryLayer.GRAVEYARD)} nodes",
            f"- (legacy A2-3): {self.get_layer_node_count(RefineryLayer.A2_3_INTAKE)} nodes",
            f"- (legacy A2-2): {self.get_layer_node_count(RefineryLayer.A2_2_CANDIDATE)} nodes",
            f"- (legacy A2-1): {self.get_layer_node_count(RefineryLayer.A2_1_KERNEL)} nodes",
            f"- Total: {len(self.builder.pydantic_model.nodes)} nodes, "
            f"{len(self.builder.pydantic_model.edges)} edges",
            f"",
        ]

        if s.docs_processed:
            lines.append("## Documents")
            for doc in s.docs_processed:
                lines.append(f"- {doc}")
            lines.append("")

        if s.findings:
            lines.append("## Key Findings")
            for finding in s.findings:
                lines.append(f"- {finding}")
            lines.append("")

        if s.batches_created:
            lines.append("## Batches")
            for bid in s.batches_created:
                lines.append(f"- `{bid}`")
            lines.append("")

        log_path.write_text("\n".join(lines), encoding="utf-8")
        self._active_session = None
        return str(log_path)

    # ── Gap 7: Mid-Session Checkpoint ─────────────────────────────────

    def checkpoint(self) -> None:
        """
        Save graph + batch index + increment checkpoint counter.
        Called after each ingest to prevent data loss in long sessions.
        """
        self._save()
        if self._active_session:
            self._active_session.checkpoints += 1

    # ── Operational Context / Thread Seals ────────────────────────────

    def seal_thread(self, active_tasks: list[str], context_notes: str) -> str:
        """
        Create a permanent THREAD_SEAL node in the graph capturing the 
        operational handoff state, so the next thread can resume seamlessly.
        """
        seal_id = f"A2_SEAL::{self._utc_iso()}_{self._content_hash(context_notes)[:6]}"
        
        session_id = self._active_session.session_id if self._active_session else "NO_SESSION"
        
        node = GraphNode(
            id=seal_id,
            node_type="THREAD_SEAL",
            layer="A2",
            name=f"Thread Seal {self._utc_iso()}",
            description=context_notes,
            trust_zone=RefineryLayer.A2_MID.value,
            admissibility_state="ADMITTED",
            object_family="SealRecord",
            source_class="DERIVED",
            properties={
                "active_tasks": active_tasks,
                "session_id": session_id,
                "timestamp": self._utc_iso()
            }
        )
        self.builder.add_node(node)
        self.checkpoint()
        return seal_id

    def get_latest_seal(self) -> Optional[dict]:
        """Fetch the most recent THREAD_SEAL from the graph."""
        seals = []
        for n in self.builder.pydantic_model.nodes.values():
            if n.node_type == "THREAD_SEAL":
                seals.append(n)
        
        if not seals:
            return None
            
        # Sort by timestamp via ID since ID contains UTC iso
        latest = sorted(seals, key=lambda x: x.id, reverse=True)[0]
        return {
            "seal_id": latest.id,
            "timestamp": latest.properties.get("timestamp"),
            "active_tasks": latest.properties.get("active_tasks", []),
            "context_notes": latest.description,
            "session_id": latest.properties.get("session_id")
        }

    # ── Intent Capture / Refinement ──────────────────────────────────

    def record_intent_signal(
        self,
        intent_text: str,
        *,
        source_label: str = "user",
        intent_kind: str = "MAKER_INTENT",
        tags: Optional[list[str]] = None,
        related_node_ids: Optional[list[str]] = None,
        witness_refs: Optional[list[str]] = None,
    ) -> str:
        """
        Persist one raw intent signal as a first-class graph node.

        This is SOURCE_BOUND intake memory, not earned truth. It exists so the
        system can preserve maker/system intent explicitly instead of relying on
        volatile chat context or summaries.
        """
        captured_utc = self._utc_iso()
        raw_tags = tags or []
        intent_tags = ["intent", "intent-signal", source_label.lower()]
        if intent_kind:
            intent_tags.append(intent_kind.lower())
        intent_tags.extend(raw_tags)
        dedup_tags = sorted(set(t for t in intent_tags if t))
        node_id = (
            f"INTENT::SIGNAL::{source_label.upper()}::{self._content_hash(intent_text + captured_utc)}"
        )

        node = GraphNode(
            id=node_id,
            node_type="INTENT_SIGNAL",
            layer="A2",
            name=f"{intent_kind}:{source_label}",
            description=intent_text,
            trust_zone=RefineryLayer.A2_3_INTAKE.value,
            admissibility_state=LAYER_ADMISSIBILITY[RefineryLayer.A2_3_INTAKE],
            object_family="IntentRecord",
            source_class="DERIVED",
            authority="SOURCE_CLAIM",
            tags=dedup_tags,
            witness_refs=sorted(set(witness_refs or [])),
            properties={
                "captured_utc": captured_utc,
                "source_label": source_label,
                "intent_kind": intent_kind,
                "provenance_mode": "verbatim_intent_capture",
            },
        )
        self.builder.add_node(node)

        for target_id in related_node_ids or []:
            if not self.builder.node_exists(target_id):
                continue
            edge_id = f"EDGE::{node_id}--INFORMS-->{target_id}"
            self.builder.add_edge(
                GraphEdge(
                    source_id=node_id,
                    target_id=target_id,
                    relation="INFORMS",
                    relation_id=edge_id,
                    trust_zone=RefineryLayer.A2_3_INTAKE.value,
                    source_class="SOURCE_BOUND",
                    attributes={"captured_utc": captured_utc},
                )
            )

        if self._active_session:
            self._active_session.findings.append(
                f"intent captured: {intent_kind} from {source_label}"
            )

        self.checkpoint()
        return node_id

    def record_context_signal(
        self,
        context_text: str,
        *,
        source_label: str = "system",
        context_kind: str = "RUNTIME_CONTEXT",
        tags: Optional[list[str]] = None,
        related_node_ids: Optional[list[str]] = None,
        witness_refs: Optional[list[str]] = None,
    ) -> str:
        """
        Persist one raw runtime/control context signal as a first-class graph node.

        This is live context memory, not doctrine. It exists so the system can
        preserve active runtime/control state explicitly in graph space.
        """
        captured_utc = self._utc_iso()
        raw_tags = tags or []
        context_tags = ["context", "context-signal", source_label.lower()]
        if context_kind:
            context_tags.append(context_kind.lower())
        context_tags.extend(raw_tags)
        dedup_tags = sorted(set(t for t in context_tags if t))
        node_id = (
            f"CONTEXT::SIGNAL::{source_label.upper()}::{self._content_hash(context_text + captured_utc)}"
        )

        node = GraphNode(
            id=node_id,
            node_type="CONTEXT_SIGNAL",
            layer="A2",
            name=f"{context_kind}:{source_label}",
            description=context_text,
            trust_zone=RefineryLayer.A2_3_INTAKE.value,
            admissibility_state=LAYER_ADMISSIBILITY[RefineryLayer.A2_3_INTAKE],
            object_family="ContextRecord",
            source_class="DERIVED",
            authority="SOURCE_CLAIM",
            tags=dedup_tags,
            witness_refs=sorted(set(witness_refs or [])),
            properties={
                "captured_utc": captured_utc,
                "source_label": source_label,
                "context_kind": context_kind,
                "provenance_mode": "verbatim_context_capture",
            },
            status="RUNTIME_ONLY",
        )
        self.builder.add_node(node)

        for target_id in related_node_ids or []:
            if not self.builder.node_exists(target_id):
                continue
            edge_id = f"EDGE::{node_id}--CONTEXT_FOR-->{target_id}"
            self.builder.add_edge(
                GraphEdge(
                    source_id=node_id,
                    target_id=target_id,
                    relation="CONTEXT_FOR",
                    relation_id=edge_id,
                    trust_zone=RefineryLayer.A2_3_INTAKE.value,
                    source_class="DERIVED",
                    attributes={"captured_utc": captured_utc},
                )
            )

        if self._active_session:
            self._active_session.findings.append(
                f"context captured: {context_kind} from {source_label}"
            )

        self.checkpoint()
        return node_id

    def refine_intent_signal(
        self,
        source_intent_ids: list[str],
        refined_text: str,
        *,
        title: str = "intent_refinement",
        tags: Optional[list[str]] = None,
        related_node_ids: Optional[list[str]] = None,
        witness_refs: Optional[list[str]] = None,
    ) -> str:
        """
        Persist a derived A2 intent refinement linked to one or more raw intent
        signals. This keeps intent extraction/refinement first-class in the graph.
        """
        refined_utc = self._utc_iso()
        node_id = f"INTENT::REFINED::{self._content_hash(title + refined_text + refined_utc)}"
        resolved_witness_refs = set(witness_refs or [])
        for source_id in source_intent_ids:
            source_node = self.builder.get_node(source_id)
            if source_node is None:
                continue
            for ref in source_node.witness_refs:
                if ref:
                    resolved_witness_refs.add(ref)
        node = GraphNode(
            id=node_id,
            node_type="INTENT_REFINEMENT",
            layer="A2",
            name=title,
            description=refined_text,
            trust_zone=RefineryLayer.A2_2_CANDIDATE.value,
            admissibility_state=LAYER_ADMISSIBILITY[RefineryLayer.A2_2_CANDIDATE],
            object_family="IntentRecord",
            source_class="DERIVED",
            authority="CROSS_VALIDATED",
            lineage_refs=list(source_intent_ids),
            tags=sorted(set(["intent", "intent-refinement", *(tags or [])])),
            witness_refs=sorted(resolved_witness_refs),
            properties={
                "refined_utc": refined_utc,
                "source_intent_ids": list(source_intent_ids),
            },
        )
        self.builder.add_node(node)

        for source_id in source_intent_ids:
            if not self.builder.node_exists(source_id):
                continue
            edge_id = f"EDGE::{source_id}--REFINES_INTENT-->{node_id}"
            self.builder.add_edge(
                GraphEdge(
                    source_id=source_id,
                    target_id=node_id,
                    relation="REFINES_INTENT",
                    relation_id=edge_id,
                    trust_zone=RefineryLayer.A2_2_CANDIDATE.value,
                    attributes={"refined_utc": refined_utc},
                )
            )

        for target_id in related_node_ids or []:
            if not self.builder.node_exists(target_id):
                continue
            edge_id = f"EDGE::{node_id}--GUIDES-->{target_id}"
            self.builder.add_edge(
                GraphEdge(
                    source_id=node_id,
                    target_id=target_id,
                    relation="GUIDES",
                    relation_id=edge_id,
                    trust_zone=RefineryLayer.A2_2_CANDIDATE.value,
                    attributes={"refined_utc": refined_utc},
                )
            )

        if self._active_session:
            self._active_session.findings.append(
                f"intent refined: {title}"
            )

        self.checkpoint()
        return node_id

    # ── A2-3: High-Entropy Intake ─────────────────────────────────────

    def process_extracted_simple(self, doc_path: str, concepts: list[dict[str, Any]]) -> RefineryBatch:
        """
        Simplified wrapper for LLM agents to inject concepts without 
        needing to manually craft batch IDs or extraction modes.
        NOTE: Prefer process_extracted() (the full version) which also marks queue.
        """
        batch_id = f"BATCH_DEEP_READ_{self._content_hash(doc_path)[:8]}_{self._utc_iso()}"
        return self.ingest_document(
            doc_path=doc_path,
            extraction_mode=ExtractionMode.SOURCE_MAP,
            batch_id=batch_id,
            concepts=concepts
        )

    def ingest_document(
        self,
        doc_path: str,
        extraction_mode: ExtractionMode,
        batch_id: str,
        concepts: list[dict[str, Any]],
    ) -> RefineryBatch:
        """
        Ingest a single document into the A2-3 outer graph.

        Each concept dict should have:
          - name: str
          - description: str
          - tags: list[str]
          - source_line_range: optional str
          - authority: optional str (CANON / DRAFT / NONCANON)  # Gap 3

        Returns the batch record.
        """
        doc_abs = Path(doc_path).resolve()

        # Step 1: Block excluded file types from source ingestion
        if any(doc_abs.name.endswith(ext) for ext in self.EXCLUDED_EXTENSIONS):
            skip_batch = RefineryBatch(
                batch_id=batch_id,
                layer=RefineryLayer.A2_3_INTAKE,
                extraction_mode=extraction_mode,
                source_paths=[str(doc_abs)],
                promotion_status="EXCLUDED_FILE_TYPE",
                created_utc=self._utc_iso(),
            )
            self.batches.append(skip_batch)
            if self._active_session:
                self._active_session.docs_processed.append(str(doc_abs))
                self._active_session.batches_created.append(batch_id)
            return skip_batch

        source_node_id = f"A2_3::SOURCE::{doc_abs.name}::{self._content_hash(str(doc_abs))}"

        source_node = GraphNode(
            id=source_node_id,
            node_type="SOURCE_DOCUMENT",
            layer="A2",
            name=doc_abs.name,
            description=f"High-entropy source document ingested at A2-3.",
            original_path=str(doc_abs),
            trust_zone=RefineryLayer.A2_3_INTAKE.value,
            admissibility_state=LAYER_ADMISSIBILITY[RefineryLayer.A2_3_INTAKE],
            object_family="SurfaceRecord",
            source_class="SOURCE_BOUND",
        )
        self.builder.add_node(source_node)

        batch_node_ids = [source_node_id]
        batch_edge_ids = []

        for concept in concepts:
            concept_name = concept["name"]
            authority = concept.get("authority", "SOURCE_CLAIM")
            # Migrate legacy authority values
            if authority in LEGACY_AUTHORITY:
                authority = LEGACY_AUTHORITY[authority]

            # ── Gap 6: Concept Dedup ──────────────────────────────────
            existing_id = self.concept_exists(
                concept_name, layer=RefineryLayer.A2_3_INTAKE
            )
            if existing_id is not None:
                # Near-duplicate found — create OVERLAPS edge, skip new node
                edge_id = f"EDGE::{source_node_id}--OVERLAPS-->{existing_id}"
                edge = GraphEdge(
                    source_id=source_node_id,
                    target_id=existing_id,
                    relation="OVERLAPS",
                    relation_id=edge_id,
                    trust_zone=RefineryLayer.A2_3_INTAKE.value,
                    attributes={
                        "duplicate_source": str(doc_abs),
                        "original_description": concept.get("description", ""),
                    },
                )
                self.builder.add_edge(edge)
                batch_edge_ids.append(edge_id)
                batch_node_ids.append(existing_id)
                continue

            c_id = f"A2_3::{extraction_mode.value}::{concept_name}::{self._content_hash(concept_name)}"
            c_node = GraphNode(
                id=c_id,
                node_type="EXTRACTED_CONCEPT",
                layer="A2",
                name=concept_name,
                description=concept.get("description", ""),
                trust_zone=RefineryLayer.A2_3_INTAKE.value,
                admissibility_state=LAYER_ADMISSIBILITY[RefineryLayer.A2_3_INTAKE],
                object_family="SliceRecord",
                source_class="DERIVED",
                authority=authority,
                tags=concept.get("tags", []),
                properties={
                    "source_line_range": concept.get("source_line_range", ""),
                    "extraction_mode": extraction_mode.value,
                },
            )
            self.builder.add_node(c_node)
            batch_node_ids.append(c_id)

            edge_id = f"EDGE::{source_node_id}--{extraction_mode.value}-->{c_id}"
            edge = GraphEdge(
                source_id=source_node_id,
                target_id=c_id,
                relation=extraction_mode.value,
                relation_id=edge_id,
                trust_zone=RefineryLayer.A2_3_INTAKE.value,
            )
            self.builder.add_edge(edge)
            batch_edge_ids.append(edge_id)

        batch = RefineryBatch(
            batch_id=batch_id,
            layer=RefineryLayer.A2_3_INTAKE,
            extraction_mode=extraction_mode,
            source_paths=[str(doc_abs)],
            node_ids=batch_node_ids,
            edge_ids=batch_edge_ids,
            promotion_status="A2_3_REUSABLE",
            created_utc=self._utc_iso(),
        )
        self.batches.append(batch)

        # Track session metrics
        if self._active_session:
            self._active_session.docs_processed.append(str(doc_abs))
            self._active_session.batches_created.append(batch_id)
            self._active_session.nodes_added += len(batch_node_ids)
            self._active_session.edges_added += len(batch_edge_ids)

        self.checkpoint()  # Gap 7: checkpoint after each ingest
        return batch

    # ── A2-2: Mid-Refinement ──────────────────────────────────────────

    def promote_to_a2_2(
        self,
        source_batch_ids: list[str],
        refined_concepts: list[dict[str, Any]],
        new_batch_id: str,
        contradictions: Optional[list[tuple[str, str, str]]] = None,
    ) -> RefineryBatch:
        """
        Promote selected A2-3 concepts into the A2-2 mid-refinement layer.

        refined_concepts: list of dicts with name, description, source_node_ids
        contradictions: optional list of (node_id_a, node_id_b, description) tuples
        """
        batch_node_ids = []
        batch_edge_ids = []

        for concept in refined_concepts:
            c_id = f"A2_2::REFINED::{concept['name']}::{self._content_hash(concept['name'])}"
            c_node = GraphNode(
                id=c_id,
                node_type="REFINED_CONCEPT",
                layer="A2",
                name=concept["name"],
                description=concept.get("description", ""),
                trust_zone=RefineryLayer.A2_2_CANDIDATE.value,
                admissibility_state=LAYER_ADMISSIBILITY[RefineryLayer.A2_2_CANDIDATE],
                object_family="SliceRecord",
                source_class="DERIVED",
                lineage_refs=concept.get("source_node_ids", []),
            )
            self.builder.add_node(c_node)
            batch_node_ids.append(c_id)

            # Lineage edges back to A2-3 sources
            for src_id in concept.get("source_node_ids", []):
                edge_id = f"EDGE::{src_id}--REFINED_INTO-->{c_id}"
                edge = GraphEdge(
                    source_id=src_id,
                    target_id=c_id,
                    relation="REFINED_INTO",
                    relation_id=edge_id,
                    trust_zone=RefineryLayer.A2_2_CANDIDATE.value,
                )
                self.builder.add_edge(edge)
                batch_edge_ids.append(edge_id)

        # Contradiction edges
        contradiction_count = 0
        if contradictions:
            for node_a, node_b, desc in contradictions:
                edge_id = f"EDGE::{node_a}--CONTRADICTS-->{node_b}"
                edge = GraphEdge(
                    source_id=node_a,
                    target_id=node_b,
                    relation="CONTRADICTS",
                    relation_id=edge_id,
                    trust_zone=RefineryLayer.A2_2_CANDIDATE.value,
                    attributes={"description": desc},
                )
                self.builder.add_edge(edge)
                batch_edge_ids.append(edge_id)
                contradiction_count += 1

        batch = RefineryBatch(
            batch_id=new_batch_id,
            layer=RefineryLayer.A2_2_CANDIDATE,
            extraction_mode=ExtractionMode.SOURCE_MAP,
            source_paths=[],
            node_ids=batch_node_ids,
            edge_ids=batch_edge_ids,
            promotion_status="A2_2_CANDIDATE",
            parent_batch_ids=source_batch_ids,
            created_utc=self._utc_iso(),
        )
        self.batches.append(batch)

        if self._active_session:
            self._active_session.batches_created.append(new_batch_id)
            self._active_session.nodes_added += len(batch_node_ids)
            self._active_session.edges_added += len(batch_edge_ids)
            self._active_session.contradictions_found += contradiction_count

        self.checkpoint()
        return batch

    # ── A2-1: Kernel Promotion ────────────────────────────────────────

    def promote_to_kernel(
        self,
        source_batch_ids: list[str],
        kernel_concepts: list[dict[str, Any]],
        new_batch_id: str,
    ) -> RefineryBatch:
        """
        Selectively promote A2-MID concepts into the A2-LOW control surface.
        Only explicitly admitted material reaches here.
        Nothing promoted here is canon — canon requires the full ratchet.
        """
        batch_node_ids = []
        batch_edge_ids = []

        for concept in kernel_concepts:
            c_id = f"A2_1::KERNEL::{concept['name']}::{self._content_hash(concept['name'])}"
            c_node = GraphNode(
                id=c_id,
                node_type="KERNEL_CONCEPT",
                layer="A2",
                name=concept["name"],
                description=concept.get("description", ""),
                trust_zone=RefineryLayer.A2_1_KERNEL.value,
                admissibility_state=LAYER_ADMISSIBILITY[RefineryLayer.A2_1_KERNEL],
                object_family="SurfaceRecord",
                source_class="OWNER_BOUND",
                lineage_refs=concept.get("source_node_ids", []),
            )
            self.builder.add_node(c_node)
            batch_node_ids.append(c_id)

            for src_id in concept.get("source_node_ids", []):
                edge_id = f"EDGE::{src_id}--PROMOTED_TO_KERNEL-->{c_id}"
                edge = GraphEdge(
                    source_id=src_id,
                    target_id=c_id,
                    relation="PROMOTED_TO_KERNEL",
                    relation_id=edge_id,
                    trust_zone=RefineryLayer.A2_1_KERNEL.value,
                )
                self.builder.add_edge(edge)
                batch_edge_ids.append(edge_id)

        batch = RefineryBatch(
            batch_id=new_batch_id,
            layer=RefineryLayer.A2_1_KERNEL,
            extraction_mode=ExtractionMode.SOURCE_MAP,
            source_paths=[],
            node_ids=batch_node_ids,
            edge_ids=batch_edge_ids,
            promotion_status="PROMOTED",
            parent_batch_ids=source_batch_ids,
            created_utc=self._utc_iso(),
        )
        self.batches.append(batch)

        if self._active_session:
            self._active_session.batches_created.append(new_batch_id)
            self._active_session.nodes_added += len(batch_node_ids)
            self._active_session.edges_added += len(batch_edge_ids)

        self.checkpoint()
        return batch

    # ── Query helpers ─────────────────────────────────────────────────

    def get_layer_node_count(self, layer: RefineryLayer) -> int:
        count = 0
        for node in self.builder.pydantic_model.nodes.values():
            if node.trust_zone == layer.value:
                count += 1
        return count

    def get_batch_summary(self) -> dict[str, int]:
        summary: dict[str, int] = {}
        for b in self.batches:
            key = b.layer.value
            summary[key] = summary.get(key, 0) + 1
        return summary

    def _runtime_state_for_batch(self, batch: RefineryBatch):
        from system_v4.skills.runtime_state_kernel import (
            BoundaryTag,
            LoopScale,
            RuntimeState,
        )

        phase_by_layer = {
            RefineryLayer.A2_3_INTAKE: 1,
            RefineryLayer.A2_2_CANDIDATE: 3,
            RefineryLayer.A2_1_KERNEL: 5,
        }
        loop_by_layer = {
            RefineryLayer.A2_3_INTAKE: LoopScale.MICRO,
            RefineryLayer.A2_2_CANDIDATE: LoopScale.MESO,
            RefineryLayer.A2_1_KERNEL: LoopScale.MESO,
        }
        boundaries = [BoundaryTag.STABLE]
        if batch.layer == RefineryLayer.A2_2_CANDIDATE:
            boundaries.append(BoundaryTag.FRONTIER)
        if batch.promotion_status.startswith("EXCLUDED") or batch.promotion_status.startswith("BLOCKED"):
            boundaries.append(BoundaryTag.BLOCKED)

        return RuntimeState(
            region=batch.layer.value,
            phase_index=phase_by_layer.get(batch.layer, 0),
            phase_period=8,
            loop_scale=loop_by_layer.get(batch.layer, LoopScale.MICRO),
            boundaries=boundaries,
            invariants=[
                f"promotion_status={batch.promotion_status}",
                f"node_count={len(batch.node_ids)}",
                f"edge_count={len(batch.edge_ids)}",
            ],
            dof={
                "node_count": len(batch.node_ids),
                "edge_count": len(batch.edge_ids),
            },
            context={
                "batch_id": batch.batch_id,
                "layer": batch.layer.value,
                "parent_batch_ids": list(batch.parent_batch_ids),
            },
        )

    def record_batch_runtime_witness(self, batch: RefineryBatch) -> dict[str, Any]:
        from system_v4.skills.witness_recorder import WitnessRecorder
        from system_v4.skills.z3_constraint_checker import (
            ConstraintResult,
            check_constraints,
            constraints_to_witness,
            standard_constraints,
            z3_check_phase_boundaries,
        )

        state = self._runtime_state_for_batch(batch)
        structural = check_constraints(state, standard_constraints())
        phase = z3_check_phase_boundaries(state)
        violations = list(dict.fromkeys([*structural.violations, *phase.violations]))
        combined = ConstraintResult(
            all_satisfied=len(violations) == 0,
            violations=violations,
            minimal_failure_set=violations[:5],
            checked_count=structural.checked_count + phase.checked_count,
            elapsed_ms=structural.elapsed_ms + phase.elapsed_ms,
        )
        witness = constraints_to_witness(state, combined)
        recorder = WitnessRecorder(self.refinery_witness_path)
        record_index = recorder.record(
            witness,
            tags={
                "batch_id": batch.batch_id,
                "layer": batch.layer.value,
                "promotion_status": batch.promotion_status,
                "source": "a2_graph_refinery",
            },
        )
        total = recorder.flush()
        witness_ref = f"refinery_witness_{record_index}"
        for node_id in batch.node_ids:
            node = self.builder.get_node(node_id)
            if node is None:
                continue
            refs = list(node.witness_refs)
            if witness_ref not in refs:
                refs.append(witness_ref)
                self.builder.update_node(node_id, witness_refs=refs)

        return {
            "record_index": record_index,
            "total_witnesses": total,
            "violations": violations,
            "passed": combined.all_satisfied,
        }

    # ── Node Promotion / Demotion ─────────────────────────────────────

    LAYER_TRUST_ZONES = {
        RefineryLayer.INDEX:         "INDEX",
        RefineryLayer.A2_HIGH:      "A2_HIGH_INTAKE",
        RefineryLayer.A2_MID:       "A2_MID_REFINEMENT",
        RefineryLayer.A2_LOW:       "A2_LOW_CONTROL",
        RefineryLayer.A1_JARGONED:  "A1_JARGONED",
        RefineryLayer.A1_STRIPPED:  "A1_STRIPPED",
        RefineryLayer.A1_CARTRIDGE: "A1_CARTRIDGE",
        RefineryLayer.A0_COMPILED:  "A0_COMPILED",
        RefineryLayer.B_ADJUDICATED: "B_ADJUDICATED",
        RefineryLayer.SIM_EVIDENCED: "SIM_EVIDENCED",
        RefineryLayer.GRAVEYARD:    "GRAVEYARD",
        # Backward-compat
        RefineryLayer.A2_3_INTAKE:   "A2_3_INTAKE",
        RefineryLayer.A2_2_CANDIDATE: "A2_2_CANDIDATE",
        RefineryLayer.A2_1_KERNEL:   "A2_1_KERNEL",
    }

    # Per-layer admissibility (class-level, mirrors module-level for promote_node)
    LAYER_ADMISSIBILITY_MAP = {
        RefineryLayer.INDEX:         "CATALOGED",
        RefineryLayer.A2_HIGH:      "PROPOSAL_ONLY",
        RefineryLayer.A2_MID:       "PROPOSAL_ONLY",
        RefineryLayer.A2_LOW:       "PROPOSAL_ONLY",
        RefineryLayer.A1_JARGONED:  "PROPOSAL_ONLY",
        RefineryLayer.A1_STRIPPED:  "PROPOSAL_ONLY",
        RefineryLayer.A1_CARTRIDGE: "RATCHET_READY",
        RefineryLayer.A0_COMPILED:  "COMPILED",
        RefineryLayer.B_ADJUDICATED: "ADJUDICATED",
        RefineryLayer.SIM_EVIDENCED: "EVIDENCED",
        RefineryLayer.GRAVEYARD:    "STRUCTURAL_MEMORY",
        RefineryLayer.A2_3_INTAKE:   "PROPOSAL_ONLY",
        RefineryLayer.A2_2_CANDIDATE: "CANDIDATE_ACTIVE",
        RefineryLayer.A2_1_KERNEL:   "KERNEL_ADMITTED",
    }

    # Node type transitions by target layer
    LAYER_NODE_TYPE = {
        RefineryLayer.A2_3_INTAKE:    "EXTRACTED_CONCEPT",
        RefineryLayer.A2_HIGH:        "EXTRACTED_CONCEPT",
        RefineryLayer.A2_2_CANDIDATE: "REFINED_CONCEPT",
        RefineryLayer.A2_MID:         "REFINED_CONCEPT",
        RefineryLayer.A2_1_KERNEL:    "KERNEL_CONCEPT",
        RefineryLayer.A2_LOW:         "KERNEL_CONCEPT",
        RefineryLayer.A1_JARGONED:    "KERNEL_CONCEPT",
        RefineryLayer.A1_STRIPPED:    "REFINED_CONCEPT",
        RefineryLayer.A1_CARTRIDGE:  "CARTRIDGE_PACKAGE",
        RefineryLayer.A0_COMPILED:   "EXECUTION_BLOCK",
        RefineryLayer.B_ADJUDICATED: "B_SURVIVOR",
        RefineryLayer.SIM_EVIDENCED: "SIM_EVIDENCED",
        RefineryLayer.GRAVEYARD:     "GRAVEYARD_RECORD",
    }

    def promote_node(
        self,
        node_id: str,
        target_layer: RefineryLayer,
        reason: str = "",
    ) -> bool:
        """Promote a node to a higher refinery layer (A2-3 → A2-2 → A2-1).

        Uses builder.update_node to keep Pydantic + NetworkX in sync.
        Updates node_type to match target layer semantics.
        Creates a PROMOTED_FROM lineage edge for traceability.
        Returns True if the node was found and promoted.
        """
        node = self.builder.get_node(node_id)
        if node is None:
            return False

        old_zone = node.trust_zone
        old_type = node.node_type
        new_zone = self.LAYER_TRUST_ZONES.get(target_layer, target_layer.value)
        new_admissibility = self.LAYER_ADMISSIBILITY_MAP.get(target_layer, "UNKNOWN")
        new_type = self.LAYER_NODE_TYPE.get(target_layer, old_type)

        # Don't change type for non-concept nodes (SOURCE_DOCUMENT, THREAD_SEAL, etc.)
        if old_type not in ("EXTRACTED_CONCEPT", "REFINED_CONCEPT", "KERNEL_CONCEPT"):
            new_type = old_type

        # Update via canonical API
        self.builder.update_node(
            node_id,
            trust_zone=new_zone,
            layer=target_layer.value,
            admissibility_state=new_admissibility,
            node_type=new_type,
            authority="CROSS_VALIDATED" if node.authority == "SOURCE_CLAIM" else node.authority,
            properties={
                **node.properties,
                "promoted_by": self._active_session.session_id if self._active_session else "MANUAL",
                "promoted_reason": reason,
                "promoted_from": old_zone,
            },
        )

        # Create lineage edge
        from system_v4.skills.v4_graph_builder import GraphEdge
        self.builder.add_edge(GraphEdge(
            source_id=node_id,
            target_id=node_id,
            relation="PROMOTED",
            trust_zone=new_zone,
            attributes={
                "from_zone": old_zone,
                "to_zone": new_zone,
                "from_type": old_type,
                "to_type": new_type,
                "reason": reason,
            }
        ))

        # Persist to disk
        self._save()

        if self._active_session:
            self._active_session.findings.append(
                f"PROMOTED {node_id}: {old_zone}→{new_zone} ({old_type}→{new_type}) | {reason}"
            )

        return True

    def demote_node(
        self,
        node_id: str,
        target_layer: RefineryLayer,
        reason: str = "",
    ) -> bool:
        """Demote a node to a lower refinery layer. Same mechanics as promote."""
        return self.promote_node(node_id, target_layer, f"DEMOTION: {reason}")

    # Expected node_type for each zone (concept types only)
    EXPECTED_ZONE_TYPES = {
        "A2_3_INTAKE": {"EXTRACTED_CONCEPT", "SOURCE_DOCUMENT", "THREAD_SEAL", "THREAD_CONTEXT"},
        "A2_2_CANDIDATE": {"REFINED_CONCEPT", "SOURCE_DOCUMENT"},
        "A2_1_KERNEL": {"KERNEL_CONCEPT"},
        "B_ADJUDICATED": {"B_OUTCOME", "B_SURVIVOR", "B_PARKED"},
        "SIM_EVIDENCED": {"EMPIRICAL_EVIDENCE", "SIM_EVIDENCED", "SIM_KILL"},
        "GRAVEYARD": {"GRAVEYARD_RECORD", "EXTRACTED_CONCEPT", "REFINED_CONCEPT"},
        "TERM_REGISTRY": {"TERM_ADMITTED"},
    }

    def graph_audit(self) -> dict:
        """Run an integrity audit on the graph. Returns audit report dict."""
        data = load_graph_json(
            self.workspace_root,
            "system_v4/a2_state/graphs/system_graph_a2_refinery.json",
            default={},
        )
        if not data:
            return {"error": "Graph file not found"}
        nodes = data.get("nodes", {})
        edges = data.get("edges", [])

        zone_counts: dict[str, int] = {}
        type_counts: dict[str, int] = {}
        orphan_nodes: list[str] = []
        edge_node_ids = set()
        zone_type_mismatches: list[dict] = []

        for e in edges:
            src = e.get("source_id", "")
            tgt = e.get("target_id", "")
            edge_node_ids.add(src)
            edge_node_ids.add(tgt)

        for nid, n in nodes.items():
            zone = n.get("trust_zone", "UNKNOWN")
            ntype = n.get("node_type", "UNKNOWN")
            zone_counts[zone] = zone_counts.get(zone, 0) + 1
            type_counts[ntype] = type_counts.get(ntype, 0) + 1
            if nid not in edge_node_ids and ntype != "SOURCE_DOCUMENT":
                orphan_nodes.append(nid)
            # Check zone/type coherence
            expected = self.EXPECTED_ZONE_TYPES.get(zone)
            if expected and ntype not in expected and ntype != "SOURCE_DOCUMENT":
                zone_type_mismatches.append({"id": nid, "zone": zone, "type": ntype})

        # Check for dangling edges
        dangling_edges = []
        for i, e in enumerate(edges):
            src = e.get("source_id", "")
            tgt = e.get("target_id", "")
            if src not in nodes or tgt not in nodes:
                dangling_edges.append(i)

        # Determine integrity level
        issues = []
        if dangling_edges:
            issues.append(f"{len(dangling_edges)} dangling edges")
        if orphan_nodes:
            issues.append(f"{len(orphan_nodes)} orphan non-source nodes")
        if zone_type_mismatches:
            issues.append(f"{len(zone_type_mismatches)} zone/type mismatches")

        if issues:
            integrity = f"NEEDS_ATTENTION: {'; '.join(issues)}"
        else:
            integrity = "CLEAN"

        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "zone_counts": zone_counts,
            "type_counts": type_counts,
            "orphan_concept_nodes": len(orphan_nodes),
            "zone_type_mismatches": len(zone_type_mismatches),
            "dangling_edges": len(dangling_edges),
            "integrity": integrity,
        }


    # ── Doc Queue ─────────────────────────────────────────────────────

    DOC_QUEUE_PATH_REL = "system_v4/a2_state/doc_queue.json"

    # Entropy class ordering: lower number = process first
    ENTROPY_CLASS_ORDER = {
        "SPEC_CORE": 0,         # specs 03-09, 16-21
        "SPEC_SUPPLEMENT": 1,   # specs 10-15, 22-29+
        "CONTROL_PLANE": 2,     # control_plane_bundle specs
        "A2_STATE_FORMAL": 3,   # brain slice, term map, distillation
        "A1_STATE": 4,          # a1 campaigns, packs, families
        "RUN_ANCHOR": 5,        # run anchors and regen witnesses
        "CORE_DOCS_REFINED": 6, # a1_refined fuel, constraint ladder
        "CORE_DOCS_RAW": 7,     # upgrade docs, bootpack
        "HIGH_ENTROPY": 8,      # a2_feed_high entropy, chat logs, txt
        "SYSTEM_V4": 9,         # v4 boot, process docs
    }

    def _queue_path(self) -> Path:
        return self.workspace_root / self.DOC_QUEUE_PATH_REL

    def load_queue(self) -> list[dict]:
        """Load the doc queue from disk."""
        qp = self._queue_path()
        if not qp.exists():
            return []
        try:
            return json.loads(qp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            return []

    def save_queue(self, queue: list[dict]) -> None:
        """Save the doc queue to disk."""
        qp = self._queue_path()
        qp.parent.mkdir(parents=True, exist_ok=True)
        qp.write_text(
            json.dumps(queue, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )

    def get_queue_status(self) -> dict:
        """Return queue progress summary."""
        queue = self.load_queue()
        total = len(queue)
        done = sum(1 for d in queue if d.get("status") == "DONE")
        skip = sum(1 for d in queue if d.get("status") == "SKIP")
        pending = total - done - skip
        by_class: dict[str, dict[str, int]] = {}
        for d in queue:
            ec = d.get("entropy_class", "UNKNOWN")
            if ec not in by_class:
                by_class[ec] = {"pending": 0, "done": 0, "skip": 0}
            by_class[ec][d.get("status", "PENDING").lower()] = (
                by_class[ec].get(d.get("status", "PENDING").lower(), 0) + 1
            )
        return {
            "total": total,
            "done": done,
            "skip": skip,
            "pending": pending,
            "by_class": by_class,
        }

    def next_unprocessed(self, n: int = 5) -> list[dict]:
        """Return the next N unprocessed docs from the queue in order."""
        queue = self.load_queue()
        results = []
        for entry in queue:
            if entry.get("status") == "PENDING":
                results.append(entry)
                if len(results) >= n:
                    break
        return results

    def mark_processed(self, doc_path: str, batch_id: str) -> None:
        """Mark a doc as processed in the queue."""
        queue = self.load_queue()
        norm = str(Path(doc_path).resolve())
        for entry in queue:
            ep = str(Path(entry["path"]).resolve()) if not Path(entry["path"]).is_absolute() else entry["path"]
            if ep == norm or entry["path"] == doc_path:
                entry["status"] = "DONE"
                entry["processed_batch_id"] = batch_id
                break
        self.save_queue(queue)

    # ── Auto-Extract Prompt ───────────────────────────────────────────

    EXTRACTION_PROMPT_TEMPLATE = """You are the A2 Graph Refinery extraction agent.

Read the following document and extract structured concepts.

## Rules
1. No narrative smoothing — preserve contradictions explicitly
2. No implicit ontology admission
3. No implicit time or commutative defaults
4. Every claim needs a source locator
5. If extraction is incomplete, report gaps explicitly
6. Prefer over-capture over missing structure
7. All extracted concepts default to authority: SOURCE_CLAIM (nothing is canon until ratcheted)

## Output Format
Return a JSON array of concept objects. Each concept:
```json
{{
  "name": "snake_case_concept_name",
  "description": "2-4 sentence description of the concept. Be precise. Include specific rules, numbers, enums.",
  "tags": ["relevant", "tags", "max_5"],
  "authority": "SOURCE_CLAIM"
}}
```

## Guidelines
- Extract 2-8 concepts per document (more for large/dense docs)
- Name concepts descriptively: what_it_is, not what_doc_says
- Include specific numbers, enums, field names in descriptions
- Tag with layer (kernel, a0, a1, a2), domain (entropy, term, pipeline), and function (gate, fence, carrier)
- Classify authority: SOURCE_CLAIM (first reading), CROSS_VALIDATED (verified against other sources), STRIPPED (jargon removed), RATCHETED (survived B+SIM+graveyard)
- If the document has a Status line saying DRAFT/NONCANON, that tells you about the doc status, not the authority of the extracted concept
- All extracted concepts start as SOURCE_CLAIM — nothing is canon until ratcheted

## Document
Path: {doc_path}
Entropy class: {entropy_class}

---
{doc_content}
---

Extract concepts now. Return ONLY the JSON array, no other text."""

    def auto_extract(self, doc_path: str, entropy_class: str = "UNKNOWN") -> str:
        """
        Read a document and return the extraction prompt.

        The calling LLM should:
        1. Call this method to get the prompt
        2. Process the prompt (it includes the doc content)
        3. Parse the JSON response
        4. Feed the concepts into ingest_document()

        Returns the formatted prompt string with the doc content embedded.
        """
        abs_path = Path(doc_path).resolve()
        if not abs_path.exists():
            return f"ERROR: File not found: {abs_path}"

        content = abs_path.read_text(encoding="utf-8", errors="replace")

        # Truncate very large docs to avoid context overflow
        max_chars = 60000
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n[TRUNCATED — original was {len(content)} chars, showing first {max_chars}]"

        return self.EXTRACTION_PROMPT_TEMPLATE.format(
            doc_path=str(abs_path),
            entropy_class=entropy_class,
            doc_content=content,
        )

    def process_extracted(
        self,
        doc_path: str,
        concepts_json: list[dict],
        extraction_mode: ExtractionMode = ExtractionMode.SOURCE_MAP,
    ) -> RefineryBatch:
        """
        Ingest LLM-extracted concepts for a document.

        This is the bridge between auto_extract() output (LLM response)
        and ingest_document(). Call this after the LLM returns concepts.
        """
        abs_path = Path(doc_path).resolve()
        batch_id = f"AUTO_{abs_path.stem}_{self._content_hash(str(abs_path))}"

        batch = self.ingest_document(
            doc_path=str(abs_path),
            extraction_mode=extraction_mode,
            batch_id=batch_id,
            concepts=concepts_json,
        )

        # Mark as done in queue
        self.mark_processed(str(abs_path), batch_id)
        return batch

    def process_next(self, n: int = 5) -> list[dict]:
        """
        Get the next N docs to process with their extraction prompts.

        Returns list of {path, entropy_class, prompt} dicts.
        The calling LLM reads each prompt, extracts concepts,
        and calls process_extracted() for each.
        """
        pending = self.next_unprocessed(n)
        results = []
        for entry in pending:
            prompt = self.auto_extract(
                entry["path"],
                entry.get("entropy_class", "UNKNOWN"),
            )
            results.append({
                "path": entry["path"],
                "entropy_class": entry.get("entropy_class", "UNKNOWN"),
                "prompt": prompt,
            })
        return results

    # ── NetworkX Query Wrappers (Step 4) ──────────────────────────────
    # These expose the already-synced nx.MultiDiGraph for structural queries.
    # All wrappers accept an optional relation_filter to restrict to specific
    # relation families (e.g. {"DEPENDS_ON"} for dependency-only queries).

    def _filtered_view(self, relation_filter: set[str] | None = None):
        """Return an NX view restricted to edges matching relation_filter."""
        import networkx as nx
        if relation_filter is None:
            return self.builder.graph
        # Build a filtered subgraph with only matching edges
        filtered = nx.MultiDiGraph()
        filtered.add_nodes_from(self.builder.graph.nodes(data=True))
        for u, v, k, data in self.builder.graph.edges(data=True, keys=True):
            if data.get("relation") in relation_filter:
                filtered.add_edge(u, v, key=k, **data)
        return filtered

    def nx_ancestors(self, node_id: str, relation_filter: set[str] | None = None) -> set[str]:
        """All nodes reachable by following edges backward from node_id."""
        import networkx as nx
        g = self._filtered_view(relation_filter)
        if node_id not in g:
            return set()
        return nx.ancestors(g, node_id)

    def nx_descendants(self, node_id: str, relation_filter: set[str] | None = None) -> set[str]:
        """All nodes reachable by following edges forward from node_id."""
        import networkx as nx
        g = self._filtered_view(relation_filter)
        if node_id not in g:
            return set()
        return nx.descendants(g, node_id)

    def nx_ego_graph(self, node_id: str, radius: int = 2, relation_filter: set[str] | None = None) -> list[str]:
        """Subgraph of all nodes within `radius` hops of node_id."""
        import networkx as nx
        g = self._filtered_view(relation_filter)
        if node_id not in g:
            return []
        sub = nx.ego_graph(g, node_id, radius=radius, undirected=True)
        return list(sub.nodes())

    def nx_simple_cycles(self, max_length: int = 20, relation_filter: set[str] | None = None) -> list[list[str]]:
        """Find simple cycles. Use relation_filter={"DEPENDS_ON"} for real dependency loops."""
        import networkx as nx
        g = self._filtered_view(relation_filter)
        cycles = []
        for cycle in nx.simple_cycles(g, length_bound=max_length):
            cycles.append(cycle)
            if len(cycles) >= 100:  # cap to prevent runaway
                break
        return cycles

    def nx_topological_sort(
        self,
        subgraph_node_ids: list[str] | None = None,
        relation_filter: set[str] | None = None,
    ) -> list[str]:
        """
        Topological ordering of nodes. Returns [] if graph has cycles.
        Use relation_filter={"DEPENDS_ON"} for dependency ordering.
        """
        import networkx as nx
        g = self._filtered_view(relation_filter)
        if subgraph_node_ids is not None:
            g = g.subgraph(subgraph_node_ids)
        try:
            return list(nx.topological_sort(g))
        except nx.NetworkXUnfeasible:
            return []  # has cycles

    # ── Graph Health Pass (Steps 2-3) ─────────────────────────────────

    # Node types that are expected to be leaf nodes (no edges is normal)
    EXPECTED_LEAF_TYPES = {
        "THREAD_SEAL", "SIM_KILL", "B_PARKED", "TERM_ADMITTED",
    }

    def graph_health_pass(self) -> dict[str, Any]:
        """
        Run a structural health check and repair pass:
        - Quarantine dangling edges (+ rebuild NX mirror)
        - Classify orphan nodes as expected_leaf vs broken_orphan
        Returns a summary dict of what was found and fixed.
        """
        nodes = self.builder.pydantic_model.nodes
        edges = self.builder.pydantic_model.edges

        # Step 2: Find and quarantine dangling edges
        dangling = []
        clean_edges = []
        for edge in edges:
            if edge.source_id not in nodes or edge.target_id not in nodes:
                dangling.append({
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "relation": edge.relation,
                })
            else:
                clean_edges.append(edge)

        if dangling:
            self.builder.pydantic_model.edges = clean_edges
            self.builder._edge_index = {
                (e.source_id, e.target_id, e.relation) for e in clean_edges
            }
            # Rebuild NX mirror to stay in sync
            self.builder.graph.clear()
            for n_id, node in nodes.items():
                self.builder.graph.add_node(
                    n_id,
                    type=node.node_type,
                    layer=node.layer,
                    name=node.name,
                    authority=node.authority,
                    tags=node.tags,
                    trust_zone=node.trust_zone,
                )
            for edge in clean_edges:
                self.builder.graph.add_edge(
                    edge.source_id,
                    edge.target_id,
                    relation=edge.relation,
                    **edge.attributes,
                )

        # Step 3: Classify orphan nodes (expected_leaf vs broken_orphan)
        edge_nodes: set[str] = set()
        for e in clean_edges:
            edge_nodes.add(e.source_id)
            edge_nodes.add(e.target_id)

        orphan_ids = set(nodes.keys()) - edge_nodes
        expected_leaf_count = 0
        broken_orphan_count = 0
        orphan_by_type: dict[str, int] = {}
        for oid in orphan_ids:
            node = nodes[oid]
            nt = node.node_type
            if nt in self.EXPECTED_LEAF_TYPES:
                node.properties["orphan_class"] = "expected_leaf"
                expected_leaf_count += 1
            else:
                node.properties["orphan_class"] = "broken_orphan"
                broken_orphan_count += 1
            orphan_by_type[nt] = orphan_by_type.get(nt, 0) + 1

        return {
            "dangling_edges_removed": len(dangling),
            "dangling_details": dangling,
            "orphan_nodes_total": len(orphan_ids),
            "expected_leaf_count": expected_leaf_count,
            "broken_orphan_count": broken_orphan_count,
            "orphan_by_type": orphan_by_type,
            "total_nodes": len(nodes),
            "total_edges": len(clean_edges),
        }
