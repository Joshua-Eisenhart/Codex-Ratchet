#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from run_a1_worker_launch_from_packet import build_result as build_gate_result
from validate_a1_worker_launch_packet import (
    ALLOWED_QUEUE_STATUSES,
    ALLOWED_ROLES,
    validate as validate_packet,
)


SCHEMA = "A1_WORKER_LAUNCH_GATE_RESULT_v1"
THREAD_CLASS = "A1_WORKER"
MODE = "PROPOSAL_ONLY"
ALLOWED_STATUSES = {"LAUNCH_READY", "STOP_RELOAD_REQUIRED", "FAIL_CLOSED"}


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


class A1WorkerLaunchGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_name: Literal[SCHEMA] = Field(alias="schema")
    status: str
    valid: bool
    errors: list[str]
    model: str
    thread_class: Literal[THREAD_CLASS]
    mode: Literal[MODE]
    queue_status: str
    dispatch_id: str
    target_a1_role: str
    required_a1_boot: str
    a1_reload_artifacts: list[str] = Field(default_factory=list)
    source_a2_artifacts: list[str]
    bounded_scope: str
    prompt_to_send: str
    stop_rule: str
    go_on_count: int
    go_on_budget: int

    @field_validator("status")
    @classmethod
    def _validate_status(cls, value: str) -> str:
        cleaned = str(value).strip()
        if cleaned not in ALLOWED_STATUSES:
            raise ValueError("invalid_status")
        return cleaned

    @field_validator(
        "model",
        "dispatch_id",
        "bounded_scope",
        "prompt_to_send",
        "stop_rule",
    )
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

    @field_validator("errors")
    @classmethod
    def _validate_errors(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        for index, item in enumerate(value, start=1):
            cleaned = str(item).strip()
            if not cleaned:
                raise ValueError(f"invalid_errors[{index}]")
            normalized.append(cleaned)
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
    def _cross_validate(self) -> "A1WorkerLaunchGateResult":
        if self.go_on_count > self.go_on_budget:
            raise ValueError("go_on_count_exceeds_budget")
        if self.status == "FAIL_CLOSED" and self.valid:
            raise ValueError("fail_closed_cannot_be_valid")
        if self.status != "FAIL_CLOSED" and not self.valid:
            raise ValueError("non_fail_closed_must_be_valid")
        if self.status == "FAIL_CLOSED" and not self.errors:
            raise ValueError("fail_closed_missing_errors")
        if self.status == "LAUNCH_READY" and self.errors:
            raise ValueError("launch_ready_should_not_have_errors")

        packet = {
            "schema": "A1_WORKER_LAUNCH_PACKET_v1",
            "model": self.model,
            "thread_class": self.thread_class,
            "mode": self.mode,
            "queue_status": self.queue_status,
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
        }
        validation_result = validate_packet(packet)
        expected_result = build_gate_result(packet, validation_result)
        actual_result = {
            "schema": self.schema_name,
            "status": self.status,
            "valid": self.valid,
            "errors": self.errors,
            "model": self.model,
            "thread_class": self.thread_class,
            "mode": self.mode,
            "queue_status": self.queue_status,
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
        }
        if actual_result != expected_result:
            raise ValueError("gate_result_content_mismatch")
        return self

    def to_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        gate_node = "a1_worker_launch_gate_result"
        graph.add_node(
            gate_node,
            kind="a1_worker_launch_gate_result",
            status=self.status,
            valid=self.valid,
            target_a1_role=self.target_a1_role,
        )
        status_node = f"gate_status:{self.status}"
        graph.add_node(status_node, kind="gate_status", status=self.status)
        graph.add_edge(gate_node, status_node, relation="has_status")
        boot_node = f"required_a1_boot:{self.required_a1_boot}"
        graph.add_node(boot_node, kind="required_a1_boot", path=self.required_a1_boot)
        graph.add_edge(gate_node, boot_node, relation="required_a1_boot")
        for artifact in self.source_a2_artifacts:
            node_id = f"source_a2_artifact:{artifact}"
            graph.add_node(node_id, kind="source_a2_artifact", path=artifact)
            graph.add_edge(gate_node, node_id, relation="source_a2_artifact")
        for artifact in self.a1_reload_artifacts:
            node_id = f"a1_reload_artifact:{artifact}"
            graph.add_node(node_id, kind="a1_reload_artifact", path=artifact)
            graph.add_edge(gate_node, node_id, relation="a1_reload_artifact")
        return graph

    def graph_summary(self) -> dict[str, object]:
        graph = self.to_graph()
        return {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "status": self.status,
            "target_a1_role": self.target_a1_role,
            "a1_reload_artifact_count": len(self.a1_reload_artifacts),
        }


def load_a1_worker_launch_gate_result(path: Path) -> A1WorkerLaunchGateResult:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc
    try:
        return A1WorkerLaunchGateResult.model_validate(payload)
    except ValidationError as exc:
        raise SystemExit(exc.json(indent=2)) from exc
