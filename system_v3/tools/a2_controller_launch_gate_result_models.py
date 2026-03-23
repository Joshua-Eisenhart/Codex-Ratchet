#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


SCHEMA = "A2_CONTROLLER_LAUNCH_GATE_RESULT_v1"
ALLOWED_STATUSES = {
    "LAUNCH_READY",
    "STOP_RELOAD_REQUIRED",
    "FAIL_CLOSED",
}
THREAD_CLASS = "A2_CONTROLLER"
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


class A2ControllerLaunchGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_name: Literal[SCHEMA] = Field(alias="schema")
    status: str
    valid: bool
    errors: list[str]
    model: str
    thread_class: Literal[THREAD_CLASS]
    mode: Literal[MODE]
    primary_corpus: str
    state_record: str
    boot_surface: str
    current_primary_lane: str
    current_a1_queue_status: str
    go_on_count: int
    go_on_budget: int
    stop_rule: str
    dispatch_rule: str
    initial_bounded_scope: str
    allowed_first_actions: list[str]

    @field_validator("status")
    @classmethod
    def _validate_status(cls, value: str) -> str:
        cleaned = str(value).strip()
        if cleaned not in ALLOWED_STATUSES:
            raise ValueError("invalid_status")
        return cleaned

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

    @field_validator("errors", "allowed_first_actions")
    @classmethod
    def _validate_string_list(cls, value: list[str], info) -> list[str]:
        normalized: list[str] = []
        for index, item in enumerate(value, start=1):
            cleaned = str(item).strip()
            if not cleaned:
                raise ValueError(f"invalid_{info.field_name}[{index}]")
            normalized.append(cleaned)
        return normalized

    @model_validator(mode="after")
    def _cross_validate(self) -> "A2ControllerLaunchGateResult":
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
        return self

    def to_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        gate_node = "a2_controller_launch_gate_result"
        graph.add_node(
            gate_node,
            kind="a2_controller_launch_gate_result",
            status=self.status,
            valid=self.valid,
            go_on_count=self.go_on_count,
            go_on_budget=self.go_on_budget,
        )

        status_node = f"gate_status:{self.status}"
        graph.add_node(status_node, kind="gate_status", status=self.status)
        graph.add_edge(gate_node, status_node, relation="has_status")

        boot_node = f"boot_surface:{self.boot_surface}"
        graph.add_node(boot_node, kind="boot_surface", path=self.boot_surface)
        graph.add_edge(gate_node, boot_node, relation="locks_boot_surface")

        corpus_node = f"primary_corpus:{self.primary_corpus}"
        graph.add_node(corpus_node, kind="primary_corpus", path=self.primary_corpus)
        graph.add_edge(gate_node, corpus_node, relation="locks_primary_corpus")

        state_node = f"state_record:{self.state_record}"
        graph.add_node(state_node, kind="state_record", path=self.state_record)
        graph.add_edge(gate_node, state_node, relation="locks_state_record")

        lane_node = f"lane:{self.current_primary_lane}"
        graph.add_node(lane_node, kind="current_primary_lane", label=self.current_primary_lane)
        graph.add_edge(gate_node, lane_node, relation="current_primary_lane")

        queue_node = f"queue_status:{self.current_a1_queue_status}"
        graph.add_node(queue_node, kind="current_a1_queue_status", label=self.current_a1_queue_status)
        graph.add_edge(gate_node, queue_node, relation="current_a1_queue_status")

        for action in self.allowed_first_actions:
            action_node = f"allowed_action:{action}"
            graph.add_node(action_node, kind="allowed_first_action", label=action)
            graph.add_edge(gate_node, action_node, relation="allowed_first_action")

        return graph

    def graph_summary(self) -> dict[str, object]:
        graph = self.to_graph()
        return {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "status": self.status,
            "allowed_first_action_count": len(self.allowed_first_actions),
        }


def load_a2_controller_launch_gate_result(path: Path) -> A2ControllerLaunchGateResult:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc
    try:
        return A2ControllerLaunchGateResult.model_validate(payload)
    except ValidationError as exc:
        raise SystemExit(json.dumps(exc.errors(), indent=2, sort_keys=True)) from exc
