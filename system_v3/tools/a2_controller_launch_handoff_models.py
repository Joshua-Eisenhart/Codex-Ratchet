#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


SCHEMA = "A2_CONTROLLER_LAUNCH_HANDOFF_v1"
THREAD_CLASS = "A2_CONTROLLER"
ROLE_TYPE = "A2_CONTROLLER"
ROLE_LABEL = "C0"
MODE = "CONTROLLER_ONLY"


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


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MonitorRoute(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str
    owner_surface: str
    next_reader: str

    @field_validator("mode", "next_reader")
    @classmethod
    def _validate_text(cls, value: str, info) -> str:
        cleaned = str(value).strip()
        if not cleaned:
            raise ValueError(f"missing_{info.field_name}")
        return cleaned

    @field_validator("owner_surface")
    @classmethod
    def _validate_owner_surface(cls, value: str) -> str:
        return _require_abs_existing_text(value, "owner_surface")


class CloseoutRoute(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str
    state_refresh_target: str
    execution_log_target: str

    @field_validator("mode")
    @classmethod
    def _validate_mode(cls, value: str) -> str:
        cleaned = str(value).strip()
        if not cleaned:
            raise ValueError("missing_mode")
        return cleaned

    @field_validator("state_refresh_target", "execution_log_target")
    @classmethod
    def _validate_paths(cls, value: str, info) -> str:
        return _require_abs_existing_text(value, info.field_name)


class A2ControllerLaunchHandoff(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_name: Literal[SCHEMA] = Field(alias="schema")
    source_packet_json: str
    thread_class: Literal[THREAD_CLASS]
    role_label: Literal[ROLE_LABEL]
    role_type: Literal[ROLE_TYPE]
    role_scope: str
    model: str
    mode: Literal[MODE]
    primary_corpus: str
    state_record: str
    current_primary_lane: str
    current_a1_queue_status: str
    stop_rule: str
    dispatch_rule: str
    send_text_path: str
    send_text_sha256: str
    operator_steps: list[str]
    monitor_route: MonitorRoute
    closeout_route: CloseoutRoute

    @field_validator(
        "role_scope",
        "model",
        "current_primary_lane",
        "current_a1_queue_status",
        "stop_rule",
        "dispatch_rule",
        "send_text_sha256",
    )
    @classmethod
    def _validate_nonempty_text(cls, value: str, info) -> str:
        cleaned = str(value).strip()
        if not cleaned:
            raise ValueError(f"missing_{info.field_name}")
        return cleaned

    @field_validator("source_packet_json", "primary_corpus", "state_record", "send_text_path")
    @classmethod
    def _validate_abs_existing(cls, value: str, info) -> str:
        return _require_abs_existing_text(value, info.field_name)

    @field_validator("operator_steps")
    @classmethod
    def _validate_operator_steps(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        if not value:
            raise ValueError("invalid_operator_steps")
        for index, item in enumerate(value, start=1):
            cleaned = str(item).strip()
            if not cleaned:
                raise ValueError(f"invalid_operator_steps[{index}]")
            normalized.append(cleaned)
        return normalized

    @model_validator(mode="after")
    def _cross_validate(self) -> "A2ControllerLaunchHandoff":
        actual_hash = _sha256_file(Path(self.send_text_path))
        if actual_hash != self.send_text_sha256:
            raise ValueError("send_text_hash_mismatch")
        return self

    def to_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        handoff_node = "a2_controller_launch_handoff"
        graph.add_node(
            handoff_node,
            kind="a2_controller_launch_handoff",
            model=self.model,
            role_label=self.role_label,
            role_type=self.role_type,
        )

        source_packet_node = f"source_packet:{self.source_packet_json}"
        graph.add_node(source_packet_node, kind="source_packet", path=self.source_packet_json)
        graph.add_edge(handoff_node, source_packet_node, relation="source_packet")

        send_text_node = f"send_text:{self.send_text_path}"
        graph.add_node(send_text_node, kind="send_text", path=self.send_text_path)
        graph.add_edge(handoff_node, send_text_node, relation="send_text")

        corpus_node = f"primary_corpus:{self.primary_corpus}"
        graph.add_node(corpus_node, kind="primary_corpus", path=self.primary_corpus)
        graph.add_edge(handoff_node, corpus_node, relation="primary_corpus")

        state_node = f"state_record:{self.state_record}"
        graph.add_node(state_node, kind="state_record", path=self.state_record)
        graph.add_edge(handoff_node, state_node, relation="state_record")

        monitor_node = f"monitor_route:{self.monitor_route.mode}"
        graph.add_node(monitor_node, kind="monitor_route", mode=self.monitor_route.mode)
        graph.add_edge(handoff_node, monitor_node, relation="monitor_route")

        closeout_node = f"closeout_route:{self.closeout_route.mode}"
        graph.add_node(closeout_node, kind="closeout_route", mode=self.closeout_route.mode)
        graph.add_edge(handoff_node, closeout_node, relation="closeout_route")

        for step in self.operator_steps:
            step_node = f"operator_step:{step}"
            graph.add_node(step_node, kind="operator_step", label=step)
            graph.add_edge(handoff_node, step_node, relation="operator_step")

        return graph

    def graph_summary(self) -> dict[str, object]:
        graph = self.to_graph()
        return {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "operator_step_count": len(self.operator_steps),
            "monitor_mode": self.monitor_route.mode,
            "closeout_mode": self.closeout_route.mode,
        }


def load_a2_controller_launch_handoff(path: Path) -> A2ControllerLaunchHandoff:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc
    try:
        return A2ControllerLaunchHandoff.model_validate(payload)
    except ValidationError as exc:
        raise SystemExit(exc.json(indent=2)) from exc
