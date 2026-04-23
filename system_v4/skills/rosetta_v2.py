"""
rosetta_v2.py — Typed Structural Proposal Layer

Rosetta v2 replaces the flat overlay→kernel glossary with a typed packet
system.  Every entry is a packet carrying an object_class, dependency
targets, kernel binding targets, conflict sets, and a lifecycle status.

Object classes
--------------
OVERLAY_ALIAS        Surface term pointing at an existing kernel object.
AMBIGUOUS_LABEL      Overloaded term; never promotes directly.
SENSE_CANDIDATE      One explicit reading of an overloaded term.
AXIS_CANDIDATE       Proposed degree-of-freedom axis.
INVARIANT_CANDIDATE  Property claimed to persist under transforms.
COUPLING_CANDIDATE   Relation between admitted axes/invariants.
ENGINE_CANDIDATE     Mechanism emerging from couplings/constraints.
KERNEL_BINDING       Successful mapping from sense to structural math.

Status lifecycle
----------------
PROPOSED → BOUND | ALIASED | FRONTIER | AMBIGUOUS | CONFLICTED | PARKED | REJECTED
"""
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any


# ── Constants ────────────────────────────────────────────────────────────────

OBJECT_CLASSES = frozenset({
    "OVERLAY_ALIAS",
    "AMBIGUOUS_LABEL",
    "SENSE_CANDIDATE",
    "AXIS_CANDIDATE",
    "INVARIANT_CANDIDATE",
    "COUPLING_CANDIDATE",
    "ENGINE_CANDIDATE",
    "KERNEL_BINDING",
})

STATUSES = frozenset({
    "PROPOSED",
    "BOUND",
    "ALIASED",
    "FRONTIER",
    "AMBIGUOUS",
    "CONFLICTED",
    "PARKED",
    "REJECTED",
})

CONFIDENCE_MODES = frozenset({
    "literal",
    "structural",
    "analogy",
    "theory_internal",
    "unknown",
})

# Which statuses count as "terminal" (will not be promoted further)
TERMINAL_STATUSES = frozenset({"BOUND", "ALIASED", "REJECTED"})


# ── Packet dataclass ─────────────────────────────────────────────────────────

@dataclass
class RosettaPacket:
    """A single typed proposal in the Rosetta v2 store."""

    packet_id: str
    source_term: str
    source_context: str
    object_class: str                          # one of OBJECT_CLASSES
    candidate_sense_id: str                    # e.g. "entropy::von_neumann"
    source_concept_id: str = ""                # Graph node ID that sourced this packet
    source_node_type: str = ""                 # e.g. REFINED_CONCEPT
    source_tags: List[str] = field(default_factory=list)
    source_batch_id: str = ""
    confidence_mode: str = "unknown"           # one of CONFIDENCE_MODES
    kernel_targets: List[str] = field(default_factory=list)
    dependency_targets: List[str] = field(default_factory=list)
    orthogonality_claims: List[str] = field(default_factory=list)
    invariant_claims: List[str] = field(default_factory=list)
    probe_suggestions: List[str] = field(default_factory=list)
    conflict_set: List[str] = field(default_factory=list)
    status: str = "PROPOSED"
    legacy_imported: bool = False
    routing_reason: str = ""
    updated_utc: str = ""

    def __post_init__(self):
        if self.object_class not in OBJECT_CLASSES:
            raise ValueError(f"Unknown object_class: {self.object_class}")
        if self.status not in STATUSES:
            raise ValueError(f"Unknown status: {self.status}")
        if self.confidence_mode not in CONFIDENCE_MODES:
            raise ValueError(f"Unknown confidence_mode: {self.confidence_mode}")
        if not self.updated_utc:
            self.updated_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "RosettaPacket":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ── Promotion rules ──────────────────────────────────────────────────────────

# Each rule returns (allowed: bool, reason: str).
# The store's promote() method calls the appropriate rule.

def _can_promote_overlay_alias(pkt: RosettaPacket, store: "RosettaStore") -> tuple:
    """OVERLAY_ALIAS promotes only if the target already exists as BOUND."""
    for kt in pkt.kernel_targets:
        bound = store.find_bound_sense(kt)
        if not bound:
            return False, f"Kernel target '{kt}' is not yet BOUND"
    return True, "All kernel targets are BOUND"


def _can_promote_ambiguous_label(pkt: RosettaPacket, store: "RosettaStore") -> tuple:
    """AMBIGUOUS_LABEL never promotes directly."""
    return False, "AMBIGUOUS_LABEL never promotes; split into SENSE_CANDIDATEs first"


def _can_promote_sense_candidate(pkt: RosettaPacket, store: "RosettaStore") -> tuple:
    """SENSE_CANDIDATE promotes only if it binds to explicit structural math."""
    if not pkt.kernel_targets:
        return False, "No kernel_targets — cannot bind to structure"
    return True, "Has explicit kernel targets"


def _can_promote_axis_candidate(pkt: RosettaPacket, store: "RosettaStore") -> tuple:
    """AXIS_CANDIDATE promotes only if orthogonality is demonstrated."""
    if not pkt.orthogonality_claims:
        return False, "No orthogonality_claims — axis is unjustified"
    if not pkt.probe_suggestions:
        return False, "No probe_suggestions — cannot verify orthogonality"
    return True, "Has orthogonality claims and probes"


def _can_promote_invariant_candidate(pkt: RosettaPacket, store: "RosettaStore") -> tuple:
    """INVARIANT_CANDIDATE promotes only if it has probes."""
    if not pkt.invariant_claims:
        return False, "No invariant_claims"
    if not pkt.probe_suggestions:
        return False, "No probe_suggestions — cannot falsify"
    return True, "Has invariant claims and probes"


def _can_promote_coupling_candidate(pkt: RosettaPacket, store: "RosettaStore") -> tuple:
    """COUPLING_CANDIDATE promotes only if both endpoints exist."""
    if len(pkt.dependency_targets) < 2:
        return False, "Coupling needs at least 2 dependency_targets"
    for dt in pkt.dependency_targets:
        bound = store.find_bound_sense(dt)
        if not bound:
            return False, f"Dependency target '{dt}' is not yet BOUND"
    return True, "Both endpoints are BOUND"


def _can_promote_engine_candidate(pkt: RosettaPacket, store: "RosettaStore") -> tuple:
    """ENGINE_CANDIDATE promotes only if mechanism is explicit + probeable."""
    if not pkt.kernel_targets:
        return False, "No kernel_targets — mechanism not decomposed"
    if not pkt.probe_suggestions:
        return False, "No probe_suggestions — cannot distinguish from relabel"
    return True, "Has kernel targets and probes"


def _can_promote_kernel_binding(pkt: RosettaPacket, store: "RosettaStore") -> tuple:
    """KERNEL_BINDING promotes only if deps are explicit and acyclic enough."""
    if not pkt.kernel_targets:
        return False, "No kernel_targets"
    # Check for circular deps (shallow: does any dep point back to us?)
    for dt in pkt.dependency_targets:
        dep_pkt = store.get_by_sense_id(dt)
        if dep_pkt and pkt.candidate_sense_id in dep_pkt.dependency_targets:
            return False, f"Circular dependency with '{dt}'"
    return True, "Dependencies are explicit and non-circular"


PROMOTION_RULES = {
    "OVERLAY_ALIAS": _can_promote_overlay_alias,
    "AMBIGUOUS_LABEL": _can_promote_ambiguous_label,
    "SENSE_CANDIDATE": _can_promote_sense_candidate,
    "AXIS_CANDIDATE": _can_promote_axis_candidate,
    "INVARIANT_CANDIDATE": _can_promote_invariant_candidate,
    "COUPLING_CANDIDATE": _can_promote_coupling_candidate,
    "ENGINE_CANDIDATE": _can_promote_engine_candidate,
    "KERNEL_BINDING": _can_promote_kernel_binding,
}


# ── Store ────────────────────────────────────────────────────────────────────

class RosettaStore:
    """
    Manages the Rosetta v2 typed proposal store.

    All packets are keyed by packet_id.  Convenience lookups by
    source_term, candidate_sense_id, and object_class are provided.
    """

    SCHEMA = "ROSETTA_TYPED_PROPOSAL_v2"
    SCHEMA_VERSION = 2

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()
        self.a1_state_dir = self.workspace_root / "system_v4" / "a1_state"
        self.store_path = self.a1_state_dir / "rosetta_v2.json"
        self.a1_state_dir.mkdir(parents=True, exist_ok=True)

        self.packets: Dict[str, RosettaPacket] = {}
        self._load()

    # ── persistence ──

    def _load(self):
        if self.store_path.exists():
            raw = json.loads(self.store_path.read_text())
            for pid, pdata in raw.get("packets", {}).items():
                try:
                    self.packets[pid] = RosettaPacket.from_dict(pdata)
                except (ValueError, TypeError):
                    pass  # skip malformed
        # If file doesn't exist, start empty

    def save(self):
        out = {
            "schema": self.SCHEMA,
            "schema_version": self.SCHEMA_VERSION,
            "packets": {pid: pkt.to_dict() for pid, pkt in self.packets.items()},
        }
        self.store_path.write_text(json.dumps(out, indent=2, sort_keys=False))

    # ── packet creation ──

    def add_packet(self, pkt: RosettaPacket) -> RosettaPacket:
        """Add a packet to the store.  Overwrites if packet_id exists."""
        self.packets[pkt.packet_id] = pkt
        return pkt

    def emit_ambiguous_label(self, term: str,
                              context: str = "",
                              source_concept_id: str = "",
                              source_node_type: str = "",
                              source_tags: Optional[List[str]] = None,
                              source_batch_id: str = "") -> RosettaPacket:
        """Create an AMBIGUOUS_LABEL packet for an overloaded term."""
        pid = f"RST_AMB_{term}_{int(time.time())}"
        pkt = RosettaPacket(
            packet_id=pid,
            source_term=term,
            source_context=context,
            source_concept_id=source_concept_id,
            source_node_type=source_node_type,
            source_tags=source_tags or [],
            source_batch_id=source_batch_id,
            object_class="AMBIGUOUS_LABEL",
            candidate_sense_id=f"{term}::UNRESOLVED",
            status="AMBIGUOUS",
        )
        return self.add_packet(pkt)

    def split_senses(self, ambiguous_packet_id: str,
                      senses: List[Dict[str, Any]]) -> List[RosettaPacket]:
        """
        Split an AMBIGUOUS_LABEL into N SENSE_CANDIDATE packets.

        Each sense dict should have:
          - sense_suffix: str  (e.g. "von_neumann")
          - context: str
          - kernel_targets: list[str]
          - dependency_targets: list[str]  (optional)
          - conflict_set: list[str]  (optional)
        """
        parent = self.packets.get(ambiguous_packet_id)
        if not parent or parent.object_class != "AMBIGUOUS_LABEL":
            raise ValueError(f"Packet {ambiguous_packet_id} is not AMBIGUOUS_LABEL")

        children = []
        sibling_ids = []

        # Pre-build sense IDs for conflict_set cross-referencing
        for s in senses:
            sibling_ids.append(f"{parent.source_term}::{s['sense_suffix']}")

        for i, s in enumerate(senses):
            sense_id = sibling_ids[i]
            conflicts = [sid for sid in sibling_ids if sid != sense_id]
            conflicts.extend(s.get("conflict_set", []))

            pid = f"RST_SENSE_{parent.source_term}_{s['sense_suffix']}_{int(time.time())}"
            pkt = RosettaPacket(
                packet_id=pid,
                source_term=parent.source_term,
                source_context=s.get("context", parent.source_context),
                source_concept_id=parent.source_concept_id,
                source_node_type=parent.source_node_type,
                source_tags=parent.source_tags[:],
                source_batch_id=parent.source_batch_id,
                object_class="SENSE_CANDIDATE",
                candidate_sense_id=sense_id,
                confidence_mode=s.get("confidence_mode", "structural"),
                kernel_targets=s.get("kernel_targets", []),
                dependency_targets=s.get("dependency_targets", []),
                probe_suggestions=s.get("probe_suggestions", []),
                conflict_set=conflicts,
                status="PROPOSED",
            )
            children.append(self.add_packet(pkt))

        return children

    def propose_binding(self, sense_packet_id: str,
                         kernel_targets: List[str]) -> RosettaPacket:
        """Create a KERNEL_BINDING from an existing SENSE_CANDIDATE."""
        sense = self.packets.get(sense_packet_id)
        if not sense:
            raise ValueError(f"Packet {sense_packet_id} not found")

        pid = f"RST_BIND_{sense.candidate_sense_id}_{int(time.time())}"
        pkt = RosettaPacket(
            packet_id=pid,
            source_term=sense.source_term,
            source_context=sense.source_context,
            source_concept_id=sense.source_concept_id,
            source_node_type=sense.source_node_type,
            source_tags=sense.source_tags[:],
            source_batch_id=sense.source_batch_id,
            object_class="KERNEL_BINDING",
            candidate_sense_id=sense.candidate_sense_id,
            confidence_mode=sense.confidence_mode,
            kernel_targets=kernel_targets,
            dependency_targets=sense.dependency_targets,
            probe_suggestions=sense.probe_suggestions,
            conflict_set=sense.conflict_set,
            status="PROPOSED",
        )
        return self.add_packet(pkt)

    # ── promotion ──

    def promote(self, packet_id: str) -> tuple:
        """
        Attempt to promote a packet according to its object_class rules.

        Returns (success: bool, new_status: str, reason: str).
        """
        pkt = self.packets.get(packet_id)
        if not pkt:
            return False, "", f"Packet {packet_id} not found"

        if pkt.status in TERMINAL_STATUSES:
            return False, pkt.status, f"Already terminal: {pkt.status}"

        rule = PROMOTION_RULES.get(pkt.object_class)
        if not rule:
            return False, pkt.status, f"No promotion rule for {pkt.object_class}"

        allowed, reason = rule(pkt, self)
        if allowed:
            if pkt.object_class == "OVERLAY_ALIAS":
                pkt.status = "ALIASED"
            elif pkt.object_class in ("KERNEL_BINDING", "SENSE_CANDIDATE",
                                       "AXIS_CANDIDATE", "INVARIANT_CANDIDATE",
                                       "COUPLING_CANDIDATE", "ENGINE_CANDIDATE"):
                pkt.status = "BOUND"
            pkt.updated_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            return True, pkt.status, reason
        else:
            return False, pkt.status, reason

    def reject(self, packet_id: str, reason: str = "") -> bool:
        """Reject a packet."""
        pkt = self.packets.get(packet_id)
        if not pkt:
            return False
        pkt.status = "REJECTED"
        pkt.updated_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return True

    def park(self, packet_id: str, reason: str = "") -> bool:
        """Park a packet (waiting on prerequisites)."""
        pkt = self.packets.get(packet_id)
        if not pkt:
            return False
        pkt.status = "PARKED"
        pkt.updated_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return True

    # ── queries ──

    def get(self, packet_id: str) -> Optional[RosettaPacket]:
        return self.packets.get(packet_id)

    def get_by_sense_id(self, sense_id: str) -> Optional[RosettaPacket]:
        """Find the first packet with this candidate_sense_id."""
        for pkt in self.packets.values():
            if pkt.candidate_sense_id == sense_id:
                return pkt
        return None

    def find_bound_sense(self, sense_or_target: str) -> Optional[RosettaPacket]:
        """Find a BOUND packet by sense_id or kernel_target."""
        for pkt in self.packets.values():
            if pkt.status != "BOUND":
                continue
            if pkt.candidate_sense_id == sense_or_target:
                return pkt
            if sense_or_target in pkt.kernel_targets:
                return pkt
        return None

    def get_by_source_term(self, term: str) -> List[RosettaPacket]:
        """All packets for a given source term."""
        return [p for p in self.packets.values() if p.source_term == term]

    def get_by_source_concept(self, source_concept_id: str) -> List[RosettaPacket]:
        """All packets originating from a given graph concept node."""
        return [p for p in self.packets.values()
                if p.source_concept_id == source_concept_id]

    def get_kernel_translation(self, overlay_term: str) -> Optional[str]:
        """Check if an overlay term has a BOUND or ALIASED translation."""
        pkts = self.get_by_source_term(overlay_term)
        for p in pkts:
            if p.status in ("BOUND", "ALIASED") and p.kernel_targets:
                return p.kernel_targets[0]
        return None

    def upsert_diversion(self, *,
                          source_concept_id: str,
                          source_term: str,
                          source_context: str = "",
                          source_node_type: str = "",
                          source_tags: Optional[List[str]] = None,
                          source_batch_id: str = "",
                          object_class: str = "SENSE_CANDIDATE",
                          candidate_sense_id: str = "",
                          confidence_mode: str = "unknown",
                          status: str = "PARKED",
                          routing_reason: str = "") -> RosettaPacket:
        """Insert or update a diversion packet keyed by source_concept_id.

        If a packet for this source_concept_id already exists, update its
        context/tags/timestamp instead of creating a duplicate.
        """
        existing = self.get_by_source_concept(source_concept_id)
        if existing:
            pkt = existing[0]
            # Refresh ALL fields so re-routing keeps the packet current
            pkt.source_context = source_context or pkt.source_context
            pkt.source_tags = source_tags if source_tags is not None else pkt.source_tags
            pkt.source_node_type = source_node_type or pkt.source_node_type
            pkt.source_batch_id = source_batch_id or pkt.source_batch_id
            pkt.object_class = object_class or pkt.object_class
            pkt.candidate_sense_id = candidate_sense_id or pkt.candidate_sense_id
            pkt.confidence_mode = confidence_mode or pkt.confidence_mode
            pkt.status = status or pkt.status
            pkt.routing_reason = routing_reason or pkt.routing_reason
            pkt.updated_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            return pkt

        if not candidate_sense_id:
            candidate_sense_id = f"{source_term}::theory_internal"

        pkt = RosettaPacket(
            packet_id=f"RST_{object_class}_{source_concept_id}_{int(time.time())}",
            source_term=source_term,
            source_context=source_context,
            source_concept_id=source_concept_id,
            source_node_type=source_node_type,
            source_tags=source_tags or [],
            source_batch_id=source_batch_id,
            object_class=object_class,
            candidate_sense_id=candidate_sense_id,
            confidence_mode=confidence_mode,
            status=status,
            routing_reason=routing_reason,
        )
        return self.add_packet(pkt)

    def get_by_class(self, obj_class: str) -> List[RosettaPacket]:
        """All packets of a given object class."""
        return [p for p in self.packets.values() if p.object_class == obj_class]

    def get_by_status(self, status: str) -> List[RosettaPacket]:
        """All packets with a given status."""
        return [p for p in self.packets.values() if p.status == status]

    def get_unresolved_frontier(self) -> List[RosettaPacket]:
        """Packets in FRONTIER status (dependencies incomplete)."""
        return self.get_by_status("FRONTIER")

    def get_conflict_pairs(self) -> List[tuple]:
        """Return pairs of packets whose conflict_sets overlap."""
        pairs = []
        pkts = list(self.packets.values())
        for i, a in enumerate(pkts):
            for b in pkts[i+1:]:
                if (a.candidate_sense_id in b.conflict_set or
                        b.candidate_sense_id in a.conflict_set):
                    pairs.append((a.packet_id, b.packet_id))
        return pairs

    def summary(self) -> Dict[str, Any]:
        """Print a terse summary of the store."""
        from collections import Counter
        status_dist = Counter(p.status for p in self.packets.values())
        class_dist = Counter(p.object_class for p in self.packets.values())
        return {
            "total_packets": len(self.packets),
            "by_status": dict(status_dist),
            "by_class": dict(class_dist),
        }

    # ── migration from v1 ──

    def migrate_from_v1(self, v1_path: Optional[str] = None):
        """
        Read rosetta.json (v1 flat glossary) and create OVERLAY_ALIAS
        packets for each existing mapping.

        Migrated entries come in as PROPOSED with legacy_imported=True,
        not ALIASED.  They must earn promotion through v2 rules.
        """
        if v1_path is None:
            v1_path = str(self.a1_state_dir / "rosetta.json")

        v1_file = Path(v1_path)
        if not v1_file.exists():
            print(f"No v1 rosetta at {v1_file}")
            return 0

        v1_data = json.loads(v1_file.read_text())
        mappings = v1_data.get("mappings", {})
        count = 0

        for overlay_term, entry in mappings.items():
            kernel_id = entry.get("kernel_target_id", "")
            sources = entry.get("source_refs", [])

            pid = f"RST_V1_{overlay_term}"
            pkt = RosettaPacket(
                packet_id=pid,
                source_term=overlay_term,
                source_context=f"Migrated from rosetta v1 ({', '.join(sources)})",
                object_class="OVERLAY_ALIAS",
                candidate_sense_id=f"{overlay_term}::v1_alias",
                confidence_mode="literal",
                kernel_targets=[kernel_id] if kernel_id else [],
                status="PROPOSED",
                legacy_imported=True,
                routing_reason="v1_migration",
                updated_utc=entry.get("updated_utc", ""),
            )
            self.add_packet(pkt)
            count += 1

        print(f"Migrated {count} v1 entries as PROPOSED OVERLAY_ALIAS packets (legacy_imported=True).")
        return count


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    repo = str(Path(__file__).resolve().parents[2])
    store = RosettaStore(repo)

    if "--migrate" in sys.argv:
        n = store.migrate_from_v1()
        store.save()
        print(f"Migration complete.  {n} packets written to {store.store_path}")
    else:
        print(f"Rosetta v2 store at: {store.store_path}")
        s = store.summary()
        print(f"  Total:  {s['total_packets']}")
        for status, cnt in s.get("by_status", {}).items():
            print(f"  {status:15s} {cnt}")
        for cls, cnt in s.get("by_class", {}).items():
            print(f"  {cls:25s} {cnt}")
