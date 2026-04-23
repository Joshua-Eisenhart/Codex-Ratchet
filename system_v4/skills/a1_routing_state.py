import json
import logging
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Set

logger = logging.getLogger(__name__)

# Statuses that mean "don't reselect this concept"
SELECTOR_BLOCKED_STATUSES: Set[str] = {
    "ROSETTA_DIVERTED",
    "NO_STRUCTURAL_SIGNAL",
    "REJECTED_AS_DISCOURSE",
}


@dataclass
class A1RouteRecord:
    """Tracks the routing outcome of an A1 boundary classification."""
    source_concept_id: str
    source_name: str
    source_node_type: str = ""
    route_status: str = "NO_STRUCTURAL_SIGNAL"
    classification_kind: str = ""
    route_reason: str = ""
    kernel_candidate_ids: list[str] = field(default_factory=list)
    rosetta_packet_ids: list[str] = field(default_factory=list)
    last_seen_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    reopen_requested: bool = False

    @property
    def selector_blocked(self) -> bool:
        if self.reopen_requested or self.route_status == "REOPEN_REQUESTED":
            return False
        return self.route_status in SELECTOR_BLOCKED_STATUSES

    @classmethod
    def from_dict(cls, d: dict) -> "A1RouteRecord":
        """Construct from dict, ignoring unknown fields."""
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


class A1RoutingState:
    """Manages the persistence of A1 routing outcomes."""

    SCHEMA = "A1_ROUTING_STATE_v1"

    def __init__(self, workspace_root: str | Path):
        self.workspace_root = Path(workspace_root).resolve()
        self.state_dir = self.workspace_root / "system_v4" / "a1_state"
        self.state_path = self.state_dir / "a1_routing_state.json"
        self.records: dict[str, A1RouteRecord] = {}

        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.load()

    def load(self):
        """Loads routing state from JSON. Handles both old envelope and new flat format."""
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                # Old format: {"schema": ..., "records": {...}}
                if "records" in data and isinstance(data["records"], dict):
                    records_dict = data["records"]
                else:
                    # New flat format: {concept_id: {...}, ...}
                    records_dict = {k: v for k, v in data.items()
                                    if isinstance(v, dict) and "source_concept_id" in v}
                for cid, record_dict in records_dict.items():
                    try:
                        self.records[cid] = A1RouteRecord.from_dict(record_dict)
                    except (TypeError, ValueError) as e:
                        logger.warning(f"Skipping record {cid}: {e}")
            except Exception as e:
                logger.error(f"Failed to load a1_routing_state.json: {e}")

    def save(self):
        """Saves routing state to JSON (envelope format for backward compat)."""
        try:
            out = {
                "schema": self.SCHEMA,
                "record_count": len(self.records),
                "records": {cid: asdict(rec) for cid, rec in self.records.items()},
            }
            self.state_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save a1_routing_state.json: {e}")

    def get(self, source_concept_id: str) -> Optional[A1RouteRecord]:
        return self.records.get(source_concept_id)

    def upsert(self, record: A1RouteRecord) -> A1RouteRecord:
        """Upserts a routing outcome for a source concept."""
        if record.source_concept_id in self.records:
            rec = self.records[record.source_concept_id]
            rec.source_name = record.source_name
            rec.source_node_type = record.source_node_type
            rec.route_status = record.route_status
            rec.classification_kind = record.classification_kind
            rec.route_reason = record.route_reason
            rec.last_seen_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            rec.reopen_requested = record.reopen_requested

            if record.kernel_candidate_ids:
                rec.kernel_candidate_ids = record.kernel_candidate_ids
            if record.rosetta_packet_ids:
                rec.rosetta_packet_ids = record.rosetta_packet_ids
        else:
            self.records[record.source_concept_id] = record

        return self.records[record.source_concept_id]

    def mark_reopen(self, source_concept_id: str, reason: str = "") -> bool:
        """Reopen a previously routed concept for reprocessing."""
        rec = self.records.get(source_concept_id)
        if not rec:
            return False
        rec.route_status = "REOPEN_REQUESTED"
        rec.reopen_requested = True
        rec.route_reason = reason or "manual_reopen"
        rec.last_seen_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return True

    def get_blocked_ids(self) -> List[str]:
        return [cid for cid, rec in self.records.items() if rec.selector_blocked]

    def get_reopen_requested_ids(self) -> List[str]:
        return [cid for cid, rec in self.records.items() if rec.reopen_requested]

    def summary(self) -> Dict[str, int]:
        return dict(Counter(r.route_status for r in self.records.values()))

