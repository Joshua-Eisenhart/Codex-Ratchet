from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SliceMember:
    ref: str
    object_family: str
    source_class: str
    trust_zone: str
    admissibility_state: str
    member_role: str


@dataclass(frozen=True)
class SliceRejectRecord:
    request_id: str
    failed_checks: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class SliceManifest:
    slice_id: str
    slice_class: str
    purpose: str
    requesting_layer: str
    target_layer: str
    created_utc: str
    compiler_version: str
    primary_members: tuple[SliceMember, ...]
    support_members: tuple[SliceMember, ...]
    excluded_candidates: tuple[str, ...] = ()
    included_relations: tuple[str, ...] = ()
    boundary_relations: tuple[str, ...] = ()
    contradiction_relations: tuple[str, ...] = ()
    branch_or_graveyard_relations: tuple[str, ...] = ()
    lineage_relations: tuple[str, ...] = ()
    stop_rule: str = ""
    allowed_actions: tuple[str, ...] = ()
    required_witness_mode: str = "NONE"
    return_target: str = ""
    ingest_expectation: str = ""
    gate_results: dict[str, bool] = field(default_factory=dict)
    failed_checks: tuple[str, ...] = ()
    terminal_path_status: str = ""
    notes: tuple[str, ...] = ()
