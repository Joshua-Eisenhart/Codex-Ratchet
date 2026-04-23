from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ObjectFamily = Literal[
    "SurfaceRecord",
    "LayerBoundaryRecord",
    "SliceRecord",
    "StateCarrierRecord",
    "RuntimeProcessRecord",
    "WitnessRecord",
    "BranchRecord",
    "RejectorRecord",
]

SourceClass = Literal[
    "SOURCE_BOUND",
    "OWNER_BOUND",
    "SUPPORT_ONLY",
    "DERIVED",
    "PROPOSAL_ONLY",
    "EVIDENCE",
]

AdmissibilityState = Literal[
    "READ_ONLY",
    "PROPOSAL_ONLY",
    "ADMITTED",
    "BLOCKED",
    "DISPUTED",
]

Status = Literal["LIVE", "PARKED", "ARCHIVED", "FAILED", "SUPERSEDED"]


@dataclass(frozen=True)
class RegistryRecord:
    schema: str
    schema_version: str
    registry_id: str
    revision: int
    object_family: ObjectFamily
    object_type: str
    layer_scope: str
    created_utc: str
    updated_utc: str
    status: Status
    source_class: SourceClass
    trust_zone: str
    admissibility_state: AdmissibilityState
    lineage_refs: tuple[str, ...] = ()
    relation_refs: tuple[str, ...] = ()
    witness_refs: tuple[str, ...] = ()
    content_hash: str = ""
    attrs: dict[str, str | tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class RegistryRelation:
    relation_id: str
    relation_type: str
    from_ref: str
    to_ref: str
    status: Status
    source_class: SourceClass
    trust_zone: str
    attrs: dict[str, str] = field(default_factory=dict)
