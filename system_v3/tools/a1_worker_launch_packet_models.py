#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from validate_a1_worker_launch_packet import (
    ALLOWED_QUEUE_STATUSES,
    ALLOWED_ROLES,
    ALLOWED_VALIDATION_REQUESTED_MODES,
    ALLOWED_VALIDATION_RESOLVED_MODES,
    ALLOWED_VALIDATION_SOURCES,
    validate as validate_packet,
)


SCHEMA = "A1_WORKER_LAUNCH_PACKET_v1"
THREAD_CLASS = "A1_WORKER"
MODE = "PROPOSAL_ONLY"


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


class A1WorkerLaunchPacket(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_name: Literal[SCHEMA] = Field(alias="schema")
    model: str
    thread_class: Literal[THREAD_CLASS]
    mode: Literal[MODE]
    queue_status: str
    dispatch_id: str
    target_a1_role: str
    required_a1_boot: str
    source_a2_artifacts: list[str]
    a1_reload_artifacts: list[str] = Field(default_factory=list)
    bounded_scope: str
    prompt_to_send: str
    stop_rule: str
    go_on_count: int
    go_on_budget: int
    family_slice_validation_requested_mode: str = ""
    family_slice_validation_resolved_mode: str = ""
    family_slice_validation_source: str = ""
    family_slice_validation_requested_provenance: ValidationRequestedProvenance | None = None
    family_slice_validation_resolved_provenance: ValidationResolvedProvenance | None = None

    @field_validator("model", "dispatch_id", "bounded_scope", "prompt_to_send", "stop_rule")
    @classmethod
    def _validate_nonempty_text(cls, value: str, info) -> str:
        cleaned = str(value).strip()
        if not cleaned:
            raise ValueError(f"missing_{info.field_name}")
        return cleaned

    @field_validator("queue_status")
    @classmethod
    def _validate_queue_status(cls, value: str) -> str:
        cleaned = str(value).strip()
        if cleaned not in ALLOWED_QUEUE_STATUSES:
            raise ValueError("invalid_queue_status")
        return cleaned

    @field_validator("target_a1_role")
    @classmethod
    def _validate_target_role(cls, value: str) -> str:
        cleaned = str(value).strip()
        if cleaned not in ALLOWED_ROLES:
            raise ValueError("invalid_target_a1_role")
        return cleaned

    @field_validator("required_a1_boot")
    @classmethod
    def _validate_required_a1_boot(cls, value: str) -> str:
        return _require_abs_existing_text(value, "required_a1_boot")

    @field_validator("source_a2_artifacts", "a1_reload_artifacts")
    @classmethod
    def _validate_path_lists(cls, value: list[str], info) -> list[str]:
        normalized: list[str] = []
        if info.field_name == "source_a2_artifacts" and not value:
            raise ValueError("invalid_source_a2_artifacts")
        for index, item in enumerate(value, start=1):
            normalized.append(_require_abs_existing_text(item, f"{info.field_name}[{index}]"))
        return normalized

    @field_validator("go_on_count", "go_on_budget")
    @classmethod
    def _validate_nonnegative_int(cls, value: int, info) -> int:
        if not isinstance(value, int):
            raise ValueError(f"invalid_{info.field_name}")
        if value < 0:
            raise ValueError(f"negative_{info.field_name}")
        return value

    @model_validator(mode="after")
    def _cross_validate(self) -> "A1WorkerLaunchPacket":
        if self.go_on_count > self.go_on_budget:
            raise ValueError("go_on_count_exceeds_budget")

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
            "model": self.model,
            "thread_class": self.thread_class,
            "mode": self.mode,
            "queue_status": self.queue_status,
            "dispatch_id": self.dispatch_id,
            "target_a1_role": self.target_a1_role,
            "required_a1_boot": self.required_a1_boot,
            "source_a2_artifacts": self.source_a2_artifacts,
            "a1_reload_artifacts": self.a1_reload_artifacts,
            "bounded_scope": self.bounded_scope,
            "prompt_to_send": self.prompt_to_send,
            "stop_rule": self.stop_rule,
            "go_on_count": self.go_on_count,
            "go_on_budget": self.go_on_budget,
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
        }
        validation_result = validate_packet(payload)
        if not validation_result["valid"]:
            raise ValueError(f"packet_validation_failed:{validation_result['errors'][0]}")
        return self

    def to_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        packet_node = "a1_worker_launch_packet"
        graph.add_node(
            packet_node,
            kind="a1_worker_launch_packet",
            model=self.model,
            queue_status=self.queue_status,
            target_a1_role=self.target_a1_role,
            go_on_count=self.go_on_count,
            go_on_budget=self.go_on_budget,
        )

        boot_node = f"required_a1_boot:{self.required_a1_boot}"
        graph.add_node(boot_node, kind="required_a1_boot", path=self.required_a1_boot)
        graph.add_edge(packet_node, boot_node, relation="required_a1_boot")

        for artifact in self.source_a2_artifacts:
            node_id = f"source_a2_artifact:{artifact}"
            graph.add_node(node_id, kind="source_a2_artifact", path=artifact)
            graph.add_edge(packet_node, node_id, relation="source_a2_artifact")

        for artifact in self.a1_reload_artifacts:
            node_id = f"a1_reload_artifact:{artifact}"
            graph.add_node(node_id, kind="a1_reload_artifact", path=artifact)
            graph.add_edge(packet_node, node_id, relation="a1_reload_artifact")

        for relation, label in (
            ("dispatch_id", self.dispatch_id),
            ("bounded_scope", self.bounded_scope),
            ("stop_rule", self.stop_rule),
        ):
            node_id = f"{relation}:{label}"
            graph.add_node(node_id, kind=relation, label=label)
            graph.add_edge(packet_node, node_id, relation=relation)
        return graph

    def graph_summary(self) -> dict[str, object]:
        graph = self.to_graph()
        return {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "target_a1_role": self.target_a1_role,
            "source_a2_artifact_count": len(self.source_a2_artifacts),
            "a1_reload_artifact_count": len(self.a1_reload_artifacts),
        }


def load_a1_worker_launch_packet(path: Path) -> A1WorkerLaunchPacket:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc
    try:
        return A1WorkerLaunchPacket.model_validate(payload)
    except ValidationError as exc:
        raise SystemExit(exc.json(indent=2)) from exc
