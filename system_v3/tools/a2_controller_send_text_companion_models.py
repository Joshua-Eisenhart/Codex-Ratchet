#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from build_a2_controller_send_text_from_packet import (
    ACTIVE_CONTEXT_SURFACES,
    GOVERNING_SURFACES,
    build_send_text,
)


SCHEMA = "A2_CONTROLLER_SEND_TEXT_COMPANION_v1"
THREAD_CLASS = "A2_CONTROLLER"
MODE = "CONTROLLER_ONLY"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


class A2ControllerSendTextCompanion(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_name: Literal[SCHEMA] = Field(alias="schema")
    source_packet_json: str
    send_text_path: str
    send_text_sha256: str
    model: str
    thread_class: Literal[THREAD_CLASS]
    mode: Literal[MODE]
    primary_corpus: str
    state_record: str
    current_primary_lane: str
    current_a1_queue_status: str
    go_on_count: int
    go_on_budget: int
    stop_rule: str
    dispatch_rule: str
    initial_bounded_scope: str
    governing_surfaces: list[str]
    active_context_surfaces: list[str]
    read_paths: list[str]
    queue_helper_mode: str
    required_closeout_fields: list[str]
    first_task_requirements: list[str]

    @field_validator(
        "source_packet_json",
        "send_text_path",
        "primary_corpus",
        "state_record",
    )
    @classmethod
    def _validate_abs_existing(cls, value: str, info) -> str:
        return _require_abs_existing_text(value, info.field_name)

    @field_validator(
        "send_text_sha256",
        "model",
        "current_primary_lane",
        "current_a1_queue_status",
        "stop_rule",
        "dispatch_rule",
        "initial_bounded_scope",
        "queue_helper_mode",
    )
    @classmethod
    def _validate_text(cls, value: str, info) -> str:
        cleaned = str(value).strip()
        if not cleaned:
            raise ValueError(f"missing_{info.field_name}")
        return cleaned

    @field_validator("go_on_count", "go_on_budget")
    @classmethod
    def _validate_nonnegative_int(cls, value: int, info) -> int:
        if not isinstance(value, int):
            raise ValueError(f"invalid_{info.field_name}")
        if value < 0:
            raise ValueError(f"negative_{info.field_name}")
        return value

    @field_validator("governing_surfaces", "active_context_surfaces", "read_paths", "required_closeout_fields", "first_task_requirements")
    @classmethod
    def _validate_string_list(cls, value: list[str], info) -> list[str]:
        normalized: list[str] = []
        if not value:
            raise ValueError(f"missing_{info.field_name}")
        for index, item in enumerate(value, start=1):
            cleaned = str(item).strip()
            if not cleaned:
                raise ValueError(f"invalid_{info.field_name}[{index}]")
            normalized.append(cleaned)
        return normalized

    @model_validator(mode="after")
    def _cross_validate(self) -> "A2ControllerSendTextCompanion":
        if self.go_on_count > self.go_on_budget:
            raise ValueError("go_on_count_exceeds_budget")
        if self.governing_surfaces != GOVERNING_SURFACES:
            raise ValueError("governing_surfaces_mismatch")
        if self.active_context_surfaces != ACTIVE_CONTEXT_SURFACES:
            raise ValueError("active_context_surfaces_mismatch")
        expected_read_paths = GOVERNING_SURFACES + [self.state_record] + ACTIVE_CONTEXT_SURFACES
        if self.read_paths != expected_read_paths:
            raise ValueError("read_paths_mismatch")

        send_text_path = Path(self.send_text_path)
        actual_hash = _sha256_file(send_text_path)
        if actual_hash != self.send_text_sha256:
            raise ValueError("send_text_hash_mismatch")

        packet = json.loads(Path(self.source_packet_json).read_text(encoding="utf-8"))
        expected_text = build_send_text(packet)
        actual_text = send_text_path.read_text(encoding="utf-8")
        if actual_text != expected_text:
            raise ValueError("send_text_content_mismatch")

        expected_queue_helper_mode = "a1_queue_helper_auto" if "a1? queue answer" in self.initial_bounded_scope else "none"
        if self.queue_helper_mode != expected_queue_helper_mode:
            raise ValueError("queue_helper_mode_mismatch")
        return self

    def to_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        companion_node = "a2_controller_send_text_companion"
        graph.add_node(
            companion_node,
            kind="a2_controller_send_text_companion",
            model=self.model,
            queue_helper_mode=self.queue_helper_mode,
            go_on_count=self.go_on_count,
            go_on_budget=self.go_on_budget,
        )

        source_packet_node = f"source_packet:{self.source_packet_json}"
        graph.add_node(source_packet_node, kind="source_packet", path=self.source_packet_json)
        graph.add_edge(companion_node, source_packet_node, relation="source_packet")

        send_text_node = f"send_text:{self.send_text_path}"
        graph.add_node(send_text_node, kind="send_text", path=self.send_text_path)
        graph.add_edge(companion_node, send_text_node, relation="send_text")

        for path in self.read_paths:
            read_node = f"read_path:{path}"
            graph.add_node(read_node, kind="read_path", path=path)
            graph.add_edge(companion_node, read_node, relation="reads")

        for item in self.required_closeout_fields:
            node_id = f"required_closeout_field:{item}"
            graph.add_node(node_id, kind="required_closeout_field", label=item)
            graph.add_edge(companion_node, node_id, relation="required_closeout_field")

        for item in self.first_task_requirements:
            node_id = f"first_task_requirement:{item}"
            graph.add_node(node_id, kind="first_task_requirement", label=item)
            graph.add_edge(companion_node, node_id, relation="first_task_requirement")
        return graph

    def graph_summary(self) -> dict[str, object]:
        graph = self.to_graph()
        return {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "queue_helper_mode": self.queue_helper_mode,
            "read_path_count": len(self.read_paths),
        }


def load_a2_controller_send_text_companion(path: Path) -> A2ControllerSendTextCompanion:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc
    try:
        return A2ControllerSendTextCompanion.model_validate(payload)
    except ValidationError as exc:
        raise SystemExit(exc.json(indent=2)) from exc
