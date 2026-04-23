from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime

from .registry_types import RegistryRecord, RegistryRelation
from .slice_manifest import SliceManifest, SliceMember, SliceRejectRecord
from .slice_request import SliceRequest


class SliceCompiler:
    """Fail-closed first slice compiler seam for system_v4."""

    def __init__(
        self,
        records: dict[str, RegistryRecord],
        relations: dict[str, RegistryRelation],
        compiler_version: str = "v1",
    ) -> None:
        self.records = records
        self.relations = relations
        self.compiler_version = compiler_version

    def compile(self, request: SliceRequest) -> SliceManifest | SliceRejectRecord:
        failed_checks: list[str] = []

        anchor_records = self._resolve_records(
            request.anchor_refs,
            failed_checks,
            "missing_anchor",
        )
        must_include_records = self._resolve_records(
            request.must_include_refs,
            failed_checks,
            "missing_required_include",
        )
        boundary_records = self._resolve_records(
            request.boundary_refs,
            failed_checks,
            "missing_boundary",
        )

        if not request.return_target:
            failed_checks.append("missing_return_target")

        if request.witness_mode == "REQUIRED":
            if any(not record.witness_refs for record in anchor_records):
                failed_checks.append("missing_required_witness")

        if any(
            record.admissibility_state == "BLOCKED" for record in anchor_records
        ):
            failed_checks.append("blocked_anchor")

        if any(
            record.trust_zone != request.trust_zone for record in anchor_records
        ):
            failed_checks.append("trust_zone_mismatch")

        relation_ids = self._collect_relations(request)
        if request.relation_families and not relation_ids:
            failed_checks.append("missing_allowed_relations")

        if failed_checks:
            return SliceRejectRecord(
                request_id=request.request_id,
                failed_checks=tuple(sorted(set(failed_checks))),
                reason="slice compile failed closed",
            )

        primary_refs = tuple(dict.fromkeys(request.anchor_refs + request.must_include_refs))
        primary_members = tuple(
            self._to_member(self.records[ref], "primary") for ref in primary_refs
        )
        support_members = tuple(
            self._to_member(record, "support") for record in boundary_records
        )

        return SliceManifest(
            slice_id=f"slice__{request.request_id}",
            slice_class=request.slice_class,
            purpose=request.purpose,
            requesting_layer=request.requesting_layer,
            target_layer=request.target_layer,
            created_utc=datetime.now(UTC).isoformat(),
            compiler_version=self.compiler_version,
            primary_members=primary_members,
            support_members=support_members,
            included_relations=relation_ids,
            boundary_relations=tuple(record.registry_id for record in boundary_records),
            lineage_relations=tuple(
                lineage_ref
                for record in anchor_records + must_include_records
                for lineage_ref in record.lineage_refs
            ),
            stop_rule=request.stop_rule,
            allowed_actions=self._allowed_actions_for(request.slice_class),
            required_witness_mode=request.witness_mode,
            return_target=request.return_target,
            ingest_expectation="typed_return_or_closeout_required",
            gate_results={
                "shape_gate": True,
                "scope_gate": True,
                "boundary_gate": True,
                "admissibility_gate": True,
                "terminal_path_gate": True,
            },
            terminal_path_status="PASS",
            notes=(
                "first fail-closed compiler seam",
                "expand with typed rejectors before widening runtime use",
            ),
        )

    def compile_dict(self, request: SliceRequest) -> dict[str, object]:
        result = self.compile(request)
        return asdict(result)

    def _resolve_records(
        self,
        refs: tuple[str, ...],
        failed_checks: list[str],
        missing_code: str,
    ) -> tuple[RegistryRecord, ...]:
        resolved: list[RegistryRecord] = []
        for ref in refs:
            record = self.records.get(ref)
            if record is None:
                failed_checks.append(missing_code)
                continue
            resolved.append(record)
        return tuple(resolved)

    def _collect_relations(self, request: SliceRequest) -> tuple[str, ...]:
        relation_ids: list[str] = []
        allowed_from_refs = set(request.anchor_refs + request.must_include_refs)
        for relation in self.relations.values():
            if relation.relation_type not in request.relation_families:
                continue
            if relation.from_ref not in allowed_from_refs and relation.to_ref not in allowed_from_refs:
                continue
            relation_ids.append(relation.relation_id)
        return tuple(sorted(set(relation_ids)))

    def _to_member(self, record: RegistryRecord, member_role: str) -> SliceMember:
        return SliceMember(
            ref=record.registry_id,
            object_family=record.object_family,
            source_class=record.source_class,
            trust_zone=record.trust_zone,
            admissibility_state=record.admissibility_state,
            member_role=member_role,
        )

    def _allowed_actions_for(self, slice_class: str) -> tuple[str, ...]:
        if slice_class in {"OWNER_KERNEL", "SOURCE_BOUND_EVIDENCE", "CONTRADICTION"}:
            return ("READ", "COMPARE", "ANNOTATE")
        if slice_class in {"DISPATCH", "RETURN_INGEST"}:
            return ("READ", "VALIDATE", "ROUTE")
        return ("READ",)
