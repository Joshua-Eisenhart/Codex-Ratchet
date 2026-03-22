from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SliceClass = Literal[
    "OWNER_KERNEL",
    "SOURCE_BOUND_EVIDENCE",
    "CONTRADICTION",
    "SAVE_LINEAGE",
    "DISPATCH",
    "RETURN_INGEST",
]

LineageMode = Literal["NONE", "MIN", "FULL"]
WitnessMode = Literal["NONE", "MIN", "REQUIRED"]


@dataclass(frozen=True)
class SliceRequest:
    request_id: str
    slice_class: SliceClass
    purpose: str
    requesting_layer: str
    target_layer: str
    anchor_refs: tuple[str, ...]
    must_include_refs: tuple[str, ...]
    relation_families: tuple[str, ...]
    boundary_refs: tuple[str, ...]
    trust_zone: str
    admissibility_floor: str
    lineage_mode: LineageMode
    witness_mode: WitnessMode
    return_target: str
    stop_rule: str
