#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from validate_codex_thread_launch_handoff import validate as validate_handoff


SCHEMA = "A1_WORKER_LAUNCH_HANDOFF_v1"
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


def _require_abs_text(value: str, key: str) -> str:
    cleaned = str(value).strip()
    if not cleaned:
        raise ValueError(f"missing_{key}")
    path = Path(cleaned)
    if not path.is_absolute():
        raise ValueError(f"non_absolute_{key}")
    return cleaned


class MonitorRoute(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill: str
    owner_surface: str
    allowed_decisions: list[str]

    @field_validator("skill", "owner_surface")
    @classmethod
    def _validate_abs_existing(cls, value: str, info) -> str:
        return _require_abs_existing_text(value, info.field_name)

    @field_validator("allowed_decisions")
    @classmethod
    def _validate_allowed_decisions(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        if not value:
            raise ValueError("missing_allowed_decisions")
        for index, item in enumerate(value, start=1):
            cleaned = str(item).strip()
            if not cleaned:
                raise ValueError(f"invalid_allowed_decisions[{index}]")
            normalized.append(cleaned)
        return normalized


class CloseoutRoute(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill: str
    closeout_prompt: str
    staging_text_path: str
    staging_json_path: str
    sink_path: str
    extract_command: str
    append_command: str

    @field_validator("skill", "closeout_prompt")
    @classmethod
    def _validate_abs_existing(cls, value: str, info) -> str:
        return _require_abs_existing_text(value, info.field_name)

    @field_validator("staging_text_path", "staging_json_path", "sink_path")
    @classmethod
    def _validate_abs_path(cls, value: str, info) -> str:
        return _require_abs_text(value, info.field_name)

    @field_validator("extract_command", "append_command")
    @classmethod
    def _validate_text(cls, value: str, info) -> str:
        cleaned = str(value).strip()
        if not cleaned:
            raise ValueError(f"missing_{info.field_name}")
        return cleaned


class A1WorkerLaunchHandoff(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_name: Literal[SCHEMA] = Field(alias="schema")
    source_packet_json: str
    thread_class: Literal[THREAD_CLASS]
    role_label: str
    role_type: str
    role_scope: str
    model: str
    mode: Literal[MODE]
    queue_status: str
    dispatch_id: str
    required_a1_boot: str
    a1_reload_artifacts: list[str] = Field(default_factory=list)
    source_a2_artifacts: list[str]
    stop_rule: str
    send_text_path: str
    send_text_sha256: str
    return_capture_path: str
    operator_steps: list[str]
    monitor_route: MonitorRoute
    closeout_route: CloseoutRoute

    @field_validator(
        "source_packet_json",
        "required_a1_boot",
        "send_text_path",
    )
    @classmethod
    def _validate_abs_existing(cls, value: str, info) -> str:
        return _require_abs_existing_text(value, info.field_name)

    @field_validator("return_capture_path")
    @classmethod
    def _validate_abs_path(cls, value: str) -> str:
        return _require_abs_text(value, "return_capture_path")

    @field_validator(
        "role_label",
        "role_type",
        "role_scope",
        "model",
        "queue_status",
        "dispatch_id",
        "stop_rule",
        "send_text_sha256",
    )
    @classmethod
    def _validate_text(cls, value: str, info) -> str:
        cleaned = str(value).strip()
        if not cleaned:
            raise ValueError(f"missing_{info.field_name}")
        return cleaned

    @field_validator("source_a2_artifacts", "a1_reload_artifacts", "operator_steps")
    @classmethod
    def _validate_lists(cls, value: list[str], info) -> list[str]:
        normalized: list[str] = []
        if info.field_name in {"source_a2_artifacts", "operator_steps"} and not value:
            raise ValueError(f"missing_{info.field_name}")
        for index, item in enumerate(value, start=1):
            if info.field_name == "operator_steps":
                cleaned = str(item).strip()
                if not cleaned:
                    raise ValueError(f"invalid_operator_steps[{index}]")
                normalized.append(cleaned)
            else:
                normalized.append(_require_abs_existing_text(item, f"{info.field_name}[{index}]"))
        return normalized

    @model_validator(mode="after")
    def _cross_validate(self) -> "A1WorkerLaunchHandoff":
        payload = {
            "schema": self.schema_name,
            "source_packet_json": self.source_packet_json,
            "thread_class": self.thread_class,
            "role_label": self.role_label,
            "role_type": self.role_type,
            "role_scope": self.role_scope,
            "model": self.model,
            "mode": self.mode,
            "queue_status": self.queue_status,
            "dispatch_id": self.dispatch_id,
            "required_a1_boot": self.required_a1_boot,
            "a1_reload_artifacts": self.a1_reload_artifacts,
            "source_a2_artifacts": self.source_a2_artifacts,
            "stop_rule": self.stop_rule,
            "send_text_path": self.send_text_path,
            "send_text_sha256": self.send_text_sha256,
            "return_capture_path": self.return_capture_path,
            "operator_steps": self.operator_steps,
            "monitor_route": self.monitor_route.model_dump(),
            "closeout_route": self.closeout_route.model_dump(),
        }
        validation_result = validate_handoff(payload)
        if not validation_result["valid"]:
            raise ValueError(f"handoff_validation_failed:{validation_result['errors'][0]}")
        return self

    def to_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        handoff_node = "a1_worker_launch_handoff"
        graph.add_node(
            handoff_node,
            kind="a1_worker_launch_handoff",
            role_label=self.role_label,
            role_type=self.role_type,
            monitor_skill=self.monitor_route.skill,
        )
        packet_node = f"source_packet:{self.source_packet_json}"
        graph.add_node(packet_node, kind="source_packet", path=self.source_packet_json)
        graph.add_edge(handoff_node, packet_node, relation="source_packet")
        send_node = f"send_text:{self.send_text_path}"
        graph.add_node(send_node, kind="send_text", path=self.send_text_path)
        graph.add_edge(handoff_node, send_node, relation="send_text")
        monitor_node = f"monitor_skill:{self.monitor_route.skill}"
        graph.add_node(monitor_node, kind="monitor_skill", path=self.monitor_route.skill)
        graph.add_edge(handoff_node, monitor_node, relation="monitor_skill")
        closeout_node = f"closeout_skill:{self.closeout_route.skill}"
        graph.add_node(closeout_node, kind="closeout_skill", path=self.closeout_route.skill)
        graph.add_edge(handoff_node, closeout_node, relation="closeout_skill")
        return graph

    def graph_summary(self) -> dict[str, object]:
        graph = self.to_graph()
        return {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "role_type": self.role_type,
            "operator_step_count": len(self.operator_steps),
            "monitor_skill": self.monitor_route.skill,
        }


def load_a1_worker_launch_handoff(path: Path) -> A1WorkerLaunchHandoff:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc
    try:
        return A1WorkerLaunchHandoff.model_validate(payload)
    except ValidationError as exc:
        raise SystemExit(exc.json(indent=2)) from exc
