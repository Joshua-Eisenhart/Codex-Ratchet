#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


SCHEMA = "A2_CONTROLLER_LAUNCH_PACKET_v1"
THREAD_CLASS = "A2_CONTROLLER"
MODE = "CONTROLLER_ONLY"


def _normalize_text(value: str) -> str:
    text = str(value).replace("`", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


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


class A2ControllerLaunchPacket(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_name: Literal[SCHEMA] = Field(alias="schema")
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
    boot_surface: str

    @field_validator(
        "model",
        "current_primary_lane",
        "current_a1_queue_status",
        "stop_rule",
        "dispatch_rule",
        "initial_bounded_scope",
    )
    @classmethod
    def _validate_nonempty_text(cls, value: str, info) -> str:
        cleaned = str(value).strip()
        if not cleaned:
            raise ValueError(f"missing_{info.field_name}")
        return cleaned

    @field_validator("primary_corpus", "state_record", "boot_surface")
    @classmethod
    def _validate_abs_existing(cls, value: str, info) -> str:
        return _require_abs_existing_text(value, info.field_name)

    @field_validator("go_on_count", "go_on_budget")
    @classmethod
    def _validate_nonnegative_int(cls, value: int, info) -> int:
        if not isinstance(value, int):
            raise ValueError(f"invalid_{info.field_name}")
        if value < 0:
            raise ValueError(f"negative_{info.field_name}")
        return value

    @model_validator(mode="after")
    def _cross_validate(self) -> "A2ControllerLaunchPacket":
        if self.go_on_count > self.go_on_budget:
            raise ValueError("go_on_count_exceeds_budget")

        state_text = _normalize_text(Path(self.state_record).read_text(encoding="utf-8"))
        for key, value in (
            ("primary_corpus", self.primary_corpus),
            ("current_primary_lane", self.current_primary_lane),
            ("current_a1_queue_status", self.current_a1_queue_status),
        ):
            if _normalize_text(value) not in state_text:
                raise ValueError(f"state_record_mismatch:{key}")
        return self

    def to_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        packet_node = "a2_controller_launch_packet"
        graph.add_node(
            packet_node,
            kind="a2_controller_launch_packet",
            model=self.model,
            thread_class=self.thread_class,
            mode=self.mode,
            go_on_count=self.go_on_count,
            go_on_budget=self.go_on_budget,
        )

        corpus_node = f"primary_corpus:{self.primary_corpus}"
        graph.add_node(corpus_node, kind="primary_corpus", path=self.primary_corpus)
        graph.add_edge(packet_node, corpus_node, relation="locks_primary_corpus")

        state_node = f"state_record:{self.state_record}"
        graph.add_node(state_node, kind="state_record", path=self.state_record)
        graph.add_edge(packet_node, state_node, relation="locks_state_record")

        boot_node = f"boot_surface:{self.boot_surface}"
        graph.add_node(boot_node, kind="boot_surface", path=self.boot_surface)
        graph.add_edge(packet_node, boot_node, relation="locks_boot_surface")

        lane_node = f"lane:{self.current_primary_lane}"
        graph.add_node(lane_node, kind="current_primary_lane", label=self.current_primary_lane)
        graph.add_edge(packet_node, lane_node, relation="current_primary_lane")

        queue_node = f"queue_status:{self.current_a1_queue_status}"
        graph.add_node(queue_node, kind="current_a1_queue_status", label=self.current_a1_queue_status)
        graph.add_edge(packet_node, queue_node, relation="current_a1_queue_status")

        stop_node = f"stop_rule:{self.stop_rule}"
        graph.add_node(stop_node, kind="stop_rule", label=self.stop_rule)
        graph.add_edge(packet_node, stop_node, relation="uses_stop_rule")

        dispatch_node = f"dispatch_rule:{self.dispatch_rule}"
        graph.add_node(dispatch_node, kind="dispatch_rule", label=self.dispatch_rule)
        graph.add_edge(packet_node, dispatch_node, relation="uses_dispatch_rule")

        scope_node = f"initial_scope:{self.initial_bounded_scope}"
        graph.add_node(scope_node, kind="initial_bounded_scope", label=self.initial_bounded_scope)
        graph.add_edge(packet_node, scope_node, relation="initial_bounded_scope")
        return graph

    def graph_summary(self) -> dict[str, object]:
        graph = self.to_graph()
        return {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "queue_status": self.current_a1_queue_status,
            "current_primary_lane": self.current_primary_lane,
        }


def load_a2_controller_launch_packet(path: Path) -> A2ControllerLaunchPacket:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc
    try:
        return A2ControllerLaunchPacket.model_validate(payload)
    except ValidationError as exc:
        raise SystemExit(json.dumps(exc.errors(), indent=2, sort_keys=True)) from exc
