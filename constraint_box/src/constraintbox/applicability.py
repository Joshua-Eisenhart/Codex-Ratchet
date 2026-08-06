from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .intake import parse_json_object


@dataclass(frozen=True)
class CapabilityDemand:
    claim_type: str
    required: tuple[str, ...]
    optional: tuple[str, ...]
    claim_ceiling: str


class ApplicabilityRegistry:
    """Controller-owned claim-type to capability mapping."""

    def __init__(self, registry_id: str, demands: dict[str, CapabilityDemand]):
        self.registry_id = registry_id
        self._demands = dict(demands)

    @classmethod
    def from_path(cls, path: Path) -> "ApplicabilityRegistry":
        body = parse_json_object(path.read_bytes())
        if body.get("schema") != "constraintbox.applicability-registry.v1":
            raise ValueError("unknown applicability registry schema")
        demands: dict[str, CapabilityDemand] = {}
        for claim_type, row in body["claim_types"].items():
            demands[claim_type] = CapabilityDemand(
                claim_type,
                tuple(row["required_capabilities"]),
                tuple(row.get("optional_capabilities", [])),
                str(row["claim_ceiling"]),
            )
        return cls(str(body["registry_id"]), demands)

    def demand_for(self, claim_type: str) -> CapabilityDemand:
        try:
            return self._demands[claim_type]
        except KeyError as exc:
            raise KeyError(f"claim type not registered: {claim_type}") from exc

    def assess(
        self,
        claim_type: str,
        capability_states: dict[str, str],
    ) -> dict[str, Any]:
        demand = self.demand_for(claim_type)
        missing = [
            capability
            for capability in demand.required
            if capability_states.get(capability) != "READY"
        ]
        return {
            "schema": "constraintbox.applicability-decision.v1",
            "registry_id": self.registry_id,
            "claim_type": claim_type,
            "required_capabilities": list(demand.required),
            "optional_capabilities": list(demand.optional),
            "missing_or_unready": missing,
            "disposition": "ELIGIBLE_FOR_CHECKS" if not missing else "PARKED",
            "claim_ceiling": demand.claim_ceiling,
            "promotion_allowed": False,
        }
