from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import Disposition, ProfileOutcome
from .intake import IntakeError, canonical_json, parse_json_object


SELF_AUTHORITY_FIELDS = {
    "all_pass",
    "decision",
    "exemption",
    "numeric_engine_required",
    "pass",
    "profile_id",
    "promotion_allowed",
    "ran",
    "tolerance",
    "verdict",
}


@dataclass(frozen=True)
class SemanticRegistry:
    registry_id: str
    object_types: frozenset[str]
    metric_types: frozenset[str]
    claim_types: frozenset[str]

    @classmethod
    def from_path(cls, path: Path) -> "SemanticRegistry":
        body = parse_json_object(path.read_bytes())
        if body.get("schema") != "constraintbox.semantic-registry.v1":
            raise ValueError("unknown semantic registry schema")
        return cls(
            str(body["registry_id"]),
            frozenset(map(str, body["object_types"])),
            frozenset(map(str, body["metric_types"])),
            frozenset(map(str, body["claim_types"])),
        )

@dataclass(frozen=True)
class SemanticClaimProfile:
    """Generic semantic intake shaped by later manifold requirements.

    It validates type declarations and evidence obligations. It does not decide
    scientific truth, choose a sim profile, or admit a manifold layer.
    """

    registry: SemanticRegistry
    profile_id: str = "constraintbox.semantic-claim.v1"
    claim_ceiling: str = (
        "one typed finite claim is structurally eligible for independent checks"
    )

    def evaluate(self, payload: bytes, run_dir: Path) -> ProfileOutcome:
        del run_dir
        try:
            body = parse_json_object(payload)
        except IntakeError as exc:
            return ProfileOutcome(
                Disposition.BLOCKED, "semantic_claim_invalid_json", {"error": str(exc)}
            )
        if body.get("schema") != "constraintbox.semantic-claim.v1":
            return ProfileOutcome(Disposition.BLOCKED, "semantic_claim_schema_unknown")

        authority_paths: list[str] = []

        def walk(value: object, path: str = "$") -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    child_path = f"{path}.{key}"
                    if key.casefold() in SELF_AUTHORITY_FIELDS:
                        authority_paths.append(child_path)
                    walk(child, child_path)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, f"{path}[{index}]")

        walk(body)
        if authority_paths:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "claim_attempted_controller_authority",
                {"forbidden_paths": authority_paths},
            )

        required = {
            "claim_id",
            "claim_type",
            "claim_ceiling",
            "object_types",
            "carrier",
            "demand_ids",
            "candidate_branches",
            "falsifiers",
            "evidence_obligations",
            "typed_metrics",
            "mss_scope",
        }
        missing = sorted(required - set(body))
        if missing:
            return ProfileOutcome(
                Disposition.PARKED, "semantic_claim_incomplete", {"missing": missing}
            )

        claim_type = body["claim_type"]
        if claim_type not in self.registry.claim_types:
            return ProfileOutcome(
                Disposition.PARKED,
                "claim_type_not_registered",
                {"claim_type": claim_type},
            )

        object_types = body["object_types"]
        if not isinstance(object_types, list) or not object_types:
            return ProfileOutcome(Disposition.PARKED, "object_types_empty")
        unknown_objects = sorted(
            value
            for value in object_types
            if not isinstance(value, str) or value not in self.registry.object_types
        )
        if unknown_objects:
            return ProfileOutcome(
                Disposition.PARKED,
                "object_type_not_registered",
                {"unknown": unknown_objects},
            )

        carrier = body["carrier"]
        if not isinstance(carrier, dict):
            return ProfileOutcome(Disposition.BLOCKED, "carrier_not_object")
        carrier_required = {"carrier_id", "finite_bound", "domain", "maps"}
        carrier_missing = sorted(carrier_required - set(carrier))
        if carrier_missing:
            return ProfileOutcome(
                Disposition.PARKED,
                "carrier_incomplete",
                {"missing": carrier_missing},
            )
        if (
            isinstance(carrier["finite_bound"], bool)
            or not isinstance(carrier["finite_bound"], int)
            or carrier["finite_bound"] < 1
        ):
            return ProfileOutcome(Disposition.BLOCKED, "carrier_bound_not_positive_integer")
        if not isinstance(carrier["maps"], list):
            return ProfileOutcome(Disposition.BLOCKED, "carrier_maps_not_list")

        for field in (
            "demand_ids",
            "candidate_branches",
            "falsifiers",
            "evidence_obligations",
        ):
            if not isinstance(body[field], list) or not body[field]:
                return ProfileOutcome(Disposition.PARKED, f"{field}_empty")

        mss_scope = body["mss_scope"]
        if mss_scope != "relative_to_declared_candidates_and_demands":
            return ProfileOutcome(
                Disposition.BLOCKED,
                "absolute_or_undefined_mss_forbidden",
                {"mss_scope": mss_scope},
            )

        metrics = body["typed_metrics"]
        if not isinstance(metrics, list):
            return ProfileOutcome(Disposition.BLOCKED, "typed_metrics_not_list")
        metric_types: set[str] = set()
        metric_ids: set[str] = set()
        for index, metric in enumerate(metrics):
            if not isinstance(metric, dict):
                return ProfileOutcome(
                    Disposition.BLOCKED,
                    "typed_metric_not_object",
                    {"index": index},
                )
            required_metric = {"metric_id", "metric_type", "scope", "value"}
            metric_missing = sorted(required_metric - set(metric))
            if metric_missing:
                return ProfileOutcome(
                    Disposition.PARKED,
                    "typed_metric_incomplete",
                    {"index": index, "missing": metric_missing},
                )
            metric_id = metric["metric_id"]
            metric_type = metric["metric_type"]
            if metric_id in metric_ids:
                return ProfileOutcome(
                    Disposition.BLOCKED,
                    "duplicate_metric_id",
                    {"metric_id": metric_id},
                )
            metric_ids.add(metric_id)
            if metric_type not in self.registry.metric_types:
                return ProfileOutcome(
                    Disposition.PARKED,
                    "metric_type_not_registered",
                    {"metric_type": metric_type},
                )
            metric_types.add(metric_type)

        aggregation = body.get("metric_aggregation")
        if aggregation not in {None, "typed_vector", "partial_order"}:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "heterogeneous_scalarization_forbidden",
                {"metric_aggregation": aggregation},
            )

        digest = hashlib.sha256(canonical_json(body)).hexdigest()
        return ProfileOutcome(
            Disposition.ELIGIBLE,
            "semantic_claim_structurally_eligible",
            {
                "claim_sha256": digest,
                "registry_id": self.registry.registry_id,
                "object_types": sorted(set(object_types)),
                "metric_types": sorted(metric_types),
                "candidate_branch_count": len(body["candidate_branches"]),
                "evidence_obligation_count": len(body["evidence_obligations"]),
            },
        )
