#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from build_a1_worker_send_text_from_packet import build_send_text


SCHEMA = "A1_WORKER_SEND_TEXT_COMPANION_v1"
THREAD_CLASS = "A1_WORKER"
MODE = "PROPOSAL_ONLY"


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


class A1WorkerSendTextCompanion(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_name: Literal[SCHEMA] = Field(alias="schema")
    source_packet_json: str
    send_text_path: str
    send_text_sha256: str
    model: str
    thread_class: Literal[THREAD_CLASS]
    mode: Literal[MODE]
    queue_status: str
    dispatch_id: str
    target_a1_role: str
    required_a1_boot: str
    a1_reload_artifacts: list[str]
    source_a2_artifacts: list[str]
    bounded_scope: str
    stop_rule: str
    go_on_count: int
    go_on_budget: int
    read_paths: list[str]
    read_path_count: int

    @field_validator(
        "source_packet_json",
        "send_text_path",
        "required_a1_boot",
    )
    @classmethod
    def _validate_abs_existing(cls, value: str, info) -> str:
        return _require_abs_existing_text(value, info.field_name)

    @field_validator(
        "send_text_sha256",
        "model",
        "queue_status",
        "dispatch_id",
        "target_a1_role",
        "bounded_scope",
        "stop_rule",
    )
    @classmethod
    def _validate_text(cls, value: str, info) -> str:
        cleaned = str(value).strip()
        if not cleaned:
            raise ValueError(f"missing_{info.field_name}")
        return cleaned

    @field_validator("a1_reload_artifacts", "source_a2_artifacts", "read_paths")
    @classmethod
    def _validate_path_lists(cls, value: list[str], info) -> list[str]:
        normalized: list[str] = []
        if info.field_name in {"source_a2_artifacts", "read_paths"} and not value:
            raise ValueError(f"missing_{info.field_name}")
        for index, item in enumerate(value, start=1):
            normalized.append(_require_abs_existing_text(item, f"{info.field_name}[{index}]"))
        return normalized

    @field_validator("go_on_count", "go_on_budget", "read_path_count")
    @classmethod
    def _validate_nonnegative_int(cls, value: int, info) -> int:
        if not isinstance(value, int):
            raise ValueError(f"invalid_{info.field_name}")
        if value < 0:
            raise ValueError(f"negative_{info.field_name}")
        return value

    @model_validator(mode="after")
    def _cross_validate(self) -> "A1WorkerSendTextCompanion":
        if self.go_on_count > self.go_on_budget:
            raise ValueError("go_on_count_exceeds_budget")

        expected_read_paths = [self.required_a1_boot, *self.a1_reload_artifacts, *self.source_a2_artifacts]
        if self.read_paths != expected_read_paths:
            raise ValueError("read_paths_mismatch")
        if len(self.read_paths) != self.read_path_count:
            raise ValueError("read_path_count_mismatch")

        send_text_path = Path(self.send_text_path)
        if _sha256_file(send_text_path) != self.send_text_sha256:
            raise ValueError("send_text_hash_mismatch")

        packet = json.loads(Path(self.source_packet_json).read_text(encoding="utf-8"))
        expected_text = build_send_text(packet)
        actual_text = send_text_path.read_text(encoding="utf-8")
        if actual_text != expected_text:
            raise ValueError("send_text_content_mismatch")
        return self

    def to_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        companion_node = "a1_worker_send_text_companion"
        graph.add_node(
            companion_node,
            kind="a1_worker_send_text_companion",
            target_a1_role=self.target_a1_role,
            read_path_count=self.read_path_count,
        )
        packet_node = f"source_packet:{self.source_packet_json}"
        graph.add_node(packet_node, kind="source_packet", path=self.source_packet_json)
        graph.add_edge(companion_node, packet_node, relation="source_packet")
        send_node = f"send_text:{self.send_text_path}"
        graph.add_node(send_node, kind="send_text", path=self.send_text_path)
        graph.add_edge(companion_node, send_node, relation="send_text")
        for path in self.read_paths:
            node_id = f"read_path:{path}"
            graph.add_node(node_id, kind="read_path", path=path)
            graph.add_edge(companion_node, node_id, relation="reads")
        return graph

    def graph_summary(self) -> dict[str, object]:
        graph = self.to_graph()
        return {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "target_a1_role": self.target_a1_role,
            "read_path_count": self.read_path_count,
        }


def load_a1_worker_send_text_companion(path: Path) -> A1WorkerSendTextCompanion:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc
    try:
        return A1WorkerSendTextCompanion.model_validate(payload)
    except ValidationError as exc:
        raise SystemExit(exc.json(indent=2)) from exc
