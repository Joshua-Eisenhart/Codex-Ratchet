#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from a1_queue_ready_integrity import validate_ready_queue_artifact_coherence


QUEUE_REGISTRY_SCHEMA = "A1_QUEUE_CANDIDATE_REGISTRY_v1"
QUEUE_PACKET_SCHEMA = "A1_QUEUE_STATUS_PACKET_v1"
READY_QUEUE_STATUSES = {
    "READY_FROM_NEW_A2_HANDOFF",
    "READY_FROM_EXISTING_FUEL",
    "READY_FROM_A2_PREBUILT_BATCH",
}
BLOCKED_QUEUE_STATUSES = {
    "BLOCKED_MISSING_BOOT",
    "BLOCKED_MISSING_ARTIFACTS",
}
ALLOWED_QUEUE_STATUSES = READY_QUEUE_STATUSES | BLOCKED_QUEUE_STATUSES | {"NO_WORK"}
READY_SURFACE_KINDS = {
    "A1_WORKER_LAUNCH_PACKET",
    "A1_LAUNCH_BUNDLE",
}
ALLOWED_VALIDATION_REQUESTED_MODES = {"jsonschema", "local_pydantic", "auto"}
ALLOWED_VALIDATION_RESOLVED_MODES = {"jsonschema", "local_pydantic"}
ALLOWED_VALIDATION_SOURCES = {"jsonschema_plus_runtime_semantics", "local_pydantic_audit"}


def _require_abs_existing_text(value: str, key: str) -> str:
    cleaned = str(value).strip()
    if not cleaned:
        raise ValueError(f"missing_{key}")
    path = Path(cleaned)
    if not path.is_absolute():
        raise ValueError(f"non_absolute_{key}")
    if not path.exists():
        raise ValueError(f"missing_path_{key}:{path}")
    return cleaned


def _normalize_abs_existing_list(values: list[str], key: str) -> list[str]:
    normalized: list[str] = []
    for index, item in enumerate(values, start=1):
        normalized.append(_require_abs_existing_text(item, f"{key}[{index}]"))
    return normalized


class ValidationRequestedProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str

    @field_validator("mode")
    @classmethod
    def _validate_mode(cls, value: str) -> str:
        cleaned = str(value).strip()
        if cleaned not in ALLOWED_VALIDATION_REQUESTED_MODES:
            raise ValueError("invalid_family_slice_validation_requested_provenance_mode")
        return cleaned


class ValidationResolvedProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str
    source: str

    @field_validator("mode")
    @classmethod
    def _validate_mode(cls, value: str) -> str:
        cleaned = str(value).strip()
        if cleaned not in ALLOWED_VALIDATION_RESOLVED_MODES:
            raise ValueError("invalid_family_slice_validation_resolved_provenance_mode")
        return cleaned

    @field_validator("source")
    @classmethod
    def _validate_source(cls, value: str) -> str:
        cleaned = str(value).strip()
        if cleaned not in ALLOWED_VALIDATION_SOURCES:
            raise ValueError("invalid_family_slice_validation_resolved_provenance_source")
        return cleaned


class A1QueueCandidateRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_name: Literal[QUEUE_REGISTRY_SCHEMA] = Field(alias="schema")
    candidate_family_slice_jsons: list[str]
    selected_family_slice_json: str = ""

    @field_validator("candidate_family_slice_jsons")
    @classmethod
    def _validate_candidates(cls, value: list[str]) -> list[str]:
        normalized = _normalize_abs_existing_list(value, "candidate_family_slice_jsons")
        seen: set[str] = set()
        for item in normalized:
            if item in seen:
                raise ValueError("duplicate_candidate_family_slice_json")
            seen.add(item)
        return normalized

    @field_validator("selected_family_slice_json")
    @classmethod
    def _validate_selected(cls, value: str) -> str:
        if not str(value).strip():
            return ""
        return _require_abs_existing_text(value, "selected_family_slice_json")

    @model_validator(mode="after")
    def _selected_in_candidates(self) -> "A1QueueCandidateRegistry":
        if self.selected_family_slice_json and self.selected_family_slice_json not in self.candidate_family_slice_jsons:
            raise ValueError("selected_family_slice_not_in_candidates")
        return self

    def to_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        registry_node = "a1_queue_candidate_registry"
        graph.add_node(
            registry_node,
            kind="queue_candidate_registry",
            candidate_count=len(self.candidate_family_slice_jsons),
            has_selected=bool(self.selected_family_slice_json),
        )
        for candidate in self.candidate_family_slice_jsons:
            node_id = f"family_slice:{candidate}"
            graph.add_node(node_id, kind="family_slice_ref", path=candidate)
            graph.add_edge(registry_node, node_id, relation="candidate_family_slice")
        if self.selected_family_slice_json:
            selected_node = f"family_slice:{self.selected_family_slice_json}"
            graph.add_node(selected_node, kind="family_slice_ref", path=self.selected_family_slice_json)
            graph.add_edge(registry_node, selected_node, relation="selected_family_slice")
        return graph


class A1QueueStatusPacket(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_name: Literal[QUEUE_PACKET_SCHEMA] = Field(alias="schema")
    queue_status: str
    reason: str
    dispatch_id: str = ""
    target_a1_role: str = ""
    required_a1_boot: str = ""
    a1_reload_artifacts: list[str] = Field(default_factory=list)
    source_a2_artifacts: list[str] = Field(default_factory=list)
    bounded_scope: str = ""
    prompt_to_send: str = ""
    stop_rule: str = ""
    go_on_count: int = 0
    go_on_budget: int = 0
    family_slice_json: str = ""
    ready_surface_kind: str = ""
    ready_packet_json: str = ""
    ready_bundle_result_json: str = ""
    ready_send_text_companion_json: str = ""
    ready_launch_spine_json: str = ""
    family_slice_validation_requested_mode: str = ""
    family_slice_validation_resolved_mode: str = ""
    family_slice_validation_source: str = ""
    family_slice_validation_requested_provenance: ValidationRequestedProvenance | None = None
    family_slice_validation_resolved_provenance: ValidationResolvedProvenance | None = None
    missing: list[str] = Field(default_factory=list)

    @field_validator("queue_status")
    @classmethod
    def _validate_queue_status(cls, value: str) -> str:
        cleaned = str(value).strip()
        if cleaned not in ALLOWED_QUEUE_STATUSES:
            raise ValueError("invalid_queue_status")
        return cleaned

    @field_validator("reason")
    @classmethod
    def _validate_reason(cls, value: str) -> str:
        cleaned = str(value).strip()
        if not cleaned:
            raise ValueError("missing_reason")
        return cleaned

    @field_validator("a1_reload_artifacts")
    @classmethod
    def _validate_reload_artifacts(cls, value: list[str]) -> list[str]:
        return _normalize_abs_existing_list(value, "a1_reload_artifacts")

    @field_validator("source_a2_artifacts")
    @classmethod
    def _validate_source_a2_artifacts(cls, value: list[str]) -> list[str]:
        return _normalize_abs_existing_list(value, "source_a2_artifacts")

    @field_validator("missing")
    @classmethod
    def _validate_missing(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        for index, item in enumerate(value, start=1):
            cleaned = str(item).strip()
            if not cleaned:
                raise ValueError(f"invalid_missing[{index}]")
            normalized.append(cleaned)
        return normalized

    @model_validator(mode="after")
    def _cross_validate(self) -> "A1QueueStatusPacket":
        if self.go_on_count < 0:
            raise ValueError("negative_go_on_count")
        if self.go_on_budget < 0:
            raise ValueError("negative_go_on_budget")
        if self.go_on_count > self.go_on_budget:
            raise ValueError("go_on_count_exceeds_budget")

        if self.queue_status == "NO_WORK":
            unexpected_text = {
                "dispatch_id": self.dispatch_id,
                "target_a1_role": self.target_a1_role,
                "required_a1_boot": self.required_a1_boot,
                "bounded_scope": self.bounded_scope,
                "prompt_to_send": self.prompt_to_send,
                "stop_rule": self.stop_rule,
                "family_slice_json": self.family_slice_json,
                "ready_surface_kind": self.ready_surface_kind,
                "ready_packet_json": self.ready_packet_json,
                "ready_bundle_result_json": self.ready_bundle_result_json,
                "ready_send_text_companion_json": self.ready_send_text_companion_json,
                "ready_launch_spine_json": self.ready_launch_spine_json,
            }
            for key, value in unexpected_text.items():
                if str(value).strip():
                    raise ValueError(f"unexpected_{key}_for_no_work")
            if self.a1_reload_artifacts:
                raise ValueError("unexpected_a1_reload_artifacts_for_no_work")
            if self.source_a2_artifacts:
                raise ValueError("unexpected_source_a2_artifacts_for_no_work")
            if self.missing:
                raise ValueError("unexpected_missing_for_no_work")
            return self

        if self.queue_status in BLOCKED_QUEUE_STATUSES:
            if not self.missing:
                raise ValueError("missing_missing")
            return self

        if not str(self.dispatch_id).strip():
            raise ValueError("missing_dispatch_id")
        if not str(self.target_a1_role).strip():
            raise ValueError("missing_target_a1_role")
        if not str(self.bounded_scope).strip():
            raise ValueError("missing_bounded_scope")
        if not str(self.prompt_to_send).strip():
            raise ValueError("missing_prompt_to_send")
        if not str(self.stop_rule).strip():
            raise ValueError("missing_stop_rule")
        if not self.source_a2_artifacts:
            raise ValueError("missing_source_a2_artifacts")
        self.required_a1_boot = _require_abs_existing_text(self.required_a1_boot, "required_a1_boot")
        self.family_slice_json = _require_abs_existing_text(self.family_slice_json, "family_slice_json")
        self.ready_packet_json = _require_abs_existing_text(self.ready_packet_json, "ready_packet_json")
        if self.ready_surface_kind not in READY_SURFACE_KINDS:
            raise ValueError("invalid_ready_surface_kind")
        if self.ready_surface_kind == "A1_LAUNCH_BUNDLE":
            self.ready_bundle_result_json = _require_abs_existing_text(
                self.ready_bundle_result_json,
                "ready_bundle_result_json",
            )
            self.ready_send_text_companion_json = _require_abs_existing_text(
                self.ready_send_text_companion_json,
                "ready_send_text_companion_json",
            )
            self.ready_launch_spine_json = _require_abs_existing_text(
                self.ready_launch_spine_json,
                "ready_launch_spine_json",
            )
        elif self.ready_bundle_result_json.strip():
            self.ready_bundle_result_json = _require_abs_existing_text(
                self.ready_bundle_result_json,
                "ready_bundle_result_json",
            )
        if self.ready_surface_kind == "A1_WORKER_LAUNCH_PACKET":
            if self.ready_send_text_companion_json.strip():
                raise ValueError("unexpected_ready_send_text_companion_json_for_packet_mode")
            if self.ready_launch_spine_json.strip():
                raise ValueError("unexpected_ready_launch_spine_json_for_packet_mode")
        requested_mode = str(self.family_slice_validation_requested_mode).strip()
        resolved_mode = str(self.family_slice_validation_resolved_mode).strip()
        validation_source = str(self.family_slice_validation_source).strip()
        if requested_mode or resolved_mode or validation_source:
            if requested_mode not in ALLOWED_VALIDATION_REQUESTED_MODES:
                raise ValueError("invalid_family_slice_validation_requested_mode")
            if resolved_mode not in ALLOWED_VALIDATION_RESOLVED_MODES:
                raise ValueError("invalid_family_slice_validation_resolved_mode")
            if validation_source not in ALLOWED_VALIDATION_SOURCES:
                raise ValueError("invalid_family_slice_validation_source")
            if not requested_mode:
                raise ValueError("missing_family_slice_validation_requested_mode")
            if not resolved_mode:
                raise ValueError("missing_family_slice_validation_resolved_mode")
            if not validation_source:
                raise ValueError("missing_family_slice_validation_source")
            if requested_mode != "auto" and requested_mode != resolved_mode:
                raise ValueError("family_slice_validation_mode_mismatch")
        if requested_mode or self.family_slice_validation_requested_provenance is not None:
            if self.family_slice_validation_requested_provenance is None:
                raise ValueError("missing_family_slice_validation_requested_provenance")
            if self.family_slice_validation_requested_provenance.mode != requested_mode:
                raise ValueError("family_slice_validation_requested_provenance_mode_mismatch")
        if resolved_mode or validation_source or self.family_slice_validation_resolved_provenance is not None:
            if self.family_slice_validation_resolved_provenance is None:
                raise ValueError("missing_family_slice_validation_resolved_provenance")
            if self.family_slice_validation_resolved_provenance.mode != resolved_mode:
                raise ValueError("family_slice_validation_resolved_provenance_mode_mismatch")
            if self.family_slice_validation_resolved_provenance.source != validation_source:
                raise ValueError("family_slice_validation_resolved_provenance_source_mismatch")
        payload = {
            "schema": self.schema_name,
            "queue_status": self.queue_status,
            "reason": self.reason,
            "dispatch_id": self.dispatch_id,
            "target_a1_role": self.target_a1_role,
            "required_a1_boot": self.required_a1_boot,
            "a1_reload_artifacts": self.a1_reload_artifacts,
            "source_a2_artifacts": self.source_a2_artifacts,
            "bounded_scope": self.bounded_scope,
            "prompt_to_send": self.prompt_to_send,
            "stop_rule": self.stop_rule,
            "go_on_count": self.go_on_count,
            "go_on_budget": self.go_on_budget,
            "family_slice_json": self.family_slice_json,
            "ready_surface_kind": self.ready_surface_kind,
            "ready_packet_json": self.ready_packet_json,
            "ready_bundle_result_json": self.ready_bundle_result_json,
            "ready_send_text_companion_json": self.ready_send_text_companion_json,
            "ready_launch_spine_json": self.ready_launch_spine_json,
            "family_slice_validation_requested_mode": self.family_slice_validation_requested_mode,
            "family_slice_validation_resolved_mode": self.family_slice_validation_resolved_mode,
            "family_slice_validation_source": self.family_slice_validation_source,
            "family_slice_validation_requested_provenance": (
                self.family_slice_validation_requested_provenance.model_dump()
                if self.family_slice_validation_requested_provenance is not None
                else None
            ),
            "family_slice_validation_resolved_provenance": (
                self.family_slice_validation_resolved_provenance.model_dump()
                if self.family_slice_validation_resolved_provenance is not None
                else None
            ),
            "missing": self.missing,
        }
        integrity_errors = validate_ready_queue_artifact_coherence(payload)
        if integrity_errors:
            raise ValueError(integrity_errors[0])
        return self

    def to_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        packet_node = "a1_queue_status_packet"
        graph.add_node(packet_node, kind="queue_status_packet", queue_status=self.queue_status)
        status_node = f"queue_status:{self.queue_status}"
        graph.add_node(status_node, kind="queue_status", queue_status=self.queue_status)
        graph.add_edge(packet_node, status_node, relation="has_queue_status")

        if self.queue_status in READY_QUEUE_STATUSES:
            family_slice_node = f"family_slice:{self.family_slice_json}"
            graph.add_node(family_slice_node, kind="family_slice_ref", path=self.family_slice_json)
            graph.add_edge(packet_node, family_slice_node, relation="selected_family_slice")

            ready_packet_node = f"ready_packet:{self.ready_packet_json}"
            graph.add_node(ready_packet_node, kind="ready_packet_ref", path=self.ready_packet_json)
            graph.add_edge(packet_node, ready_packet_node, relation="emits_ready_packet")

            boot_node = f"required_boot:{self.required_a1_boot}"
            graph.add_node(boot_node, kind="required_boot", path=self.required_a1_boot)
            graph.add_edge(packet_node, boot_node, relation="requires_boot")

            for path in self.source_a2_artifacts:
                node_id = f"source_a2:{path}"
                graph.add_node(node_id, kind="source_a2_artifact", path=path)
                graph.add_edge(packet_node, node_id, relation="uses_source_a2_artifact")

            for path in self.a1_reload_artifacts:
                node_id = f"a1_reload:{path}"
                graph.add_node(node_id, kind="a1_reload_artifact", path=path)
                graph.add_edge(packet_node, node_id, relation="uses_a1_reload_artifact")

            if self.ready_bundle_result_json:
                bundle_node = f"bundle_result:{self.ready_bundle_result_json}"
                graph.add_node(bundle_node, kind="bundle_result_ref", path=self.ready_bundle_result_json)
                graph.add_edge(packet_node, bundle_node, relation="emits_ready_bundle_result")
            if self.ready_send_text_companion_json:
                companion_node = f"send_text_companion:{self.ready_send_text_companion_json}"
                graph.add_node(
                    companion_node,
                    kind="send_text_companion_ref",
                    path=self.ready_send_text_companion_json,
                )
                graph.add_edge(packet_node, companion_node, relation="emits_ready_send_text_companion")
            if self.ready_launch_spine_json:
                spine_node = f"launch_spine:{self.ready_launch_spine_json}"
                graph.add_node(spine_node, kind="launch_spine_ref", path=self.ready_launch_spine_json)
                graph.add_edge(packet_node, spine_node, relation="emits_ready_launch_spine")

        return graph


def load_queue_candidate_registry(path: Path) -> A1QueueCandidateRegistry:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc
    try:
        return A1QueueCandidateRegistry.model_validate(payload)
    except ValidationError as exc:
        raise SystemExit(json.dumps(exc.errors(), indent=2, sort_keys=True)) from exc


def load_queue_status_packet(path: Path) -> A1QueueStatusPacket:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc
    try:
        return A1QueueStatusPacket.model_validate(payload)
    except ValidationError as exc:
        raise SystemExit(json.dumps(exc.errors(), indent=2, sort_keys=True)) from exc
