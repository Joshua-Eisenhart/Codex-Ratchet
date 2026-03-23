#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from a2_controller_launch_gate_result_models import A2ControllerLaunchGateResult
from a2_controller_launch_handoff_models import A2ControllerLaunchHandoff
from a2_controller_launch_packet_models import A2ControllerLaunchPacket
from a2_controller_send_text_companion_models import A2ControllerSendTextCompanion
from build_a2_controller_launch_handoff import build_handoff
from build_a2_controller_send_text_companion import build_companion
from run_a2_controller_launch_from_packet import build_result as build_gate_result
from validate_a2_controller_launch_packet import validate as validate_packet


SCHEMA = "A2_CONTROLLER_LAUNCH_SPINE_v1"
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


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_model(path: Path, model_cls):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc
    return model_cls.model_validate(payload)


class A2ControllerLaunchSpine(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_name: Literal[SCHEMA] = Field(alias="schema")
    launch_packet_json: str
    launch_gate_result_json: str
    send_text_companion_json: str
    launch_handoff_json: str
    launch_packet_sha256: str
    launch_gate_result_sha256: str
    send_text_companion_sha256: str
    launch_handoff_sha256: str
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
    launch_gate_status: str
    launch_gate_valid: bool
    allowed_first_actions: list[str]
    queue_helper_mode: str
    handoff_role_label: str
    handoff_role_type: str
    handoff_role_scope: str
    monitor_mode: str
    closeout_mode: str
    read_path_count: int
    operator_step_count: int

    @field_validator(
        "launch_packet_json",
        "launch_gate_result_json",
        "send_text_companion_json",
        "launch_handoff_json",
        "send_text_path",
        "primary_corpus",
        "state_record",
    )
    @classmethod
    def _validate_abs_existing(cls, value: str, info) -> str:
        return _require_abs_existing_text(value, info.field_name)

    @field_validator(
        "launch_packet_sha256",
        "launch_gate_result_sha256",
        "send_text_companion_sha256",
        "launch_handoff_sha256",
        "send_text_sha256",
        "model",
        "current_primary_lane",
        "current_a1_queue_status",
        "stop_rule",
        "dispatch_rule",
        "initial_bounded_scope",
        "launch_gate_status",
        "queue_helper_mode",
        "handoff_role_label",
        "handoff_role_type",
        "handoff_role_scope",
        "monitor_mode",
        "closeout_mode",
    )
    @classmethod
    def _validate_nonempty_text(cls, value: str, info) -> str:
        cleaned = str(value).strip()
        if not cleaned:
            raise ValueError(f"missing_{info.field_name}")
        return cleaned

    @field_validator("go_on_count", "go_on_budget", "read_path_count", "operator_step_count")
    @classmethod
    def _validate_nonnegative_int(cls, value: int, info) -> int:
        if not isinstance(value, int):
            raise ValueError(f"invalid_{info.field_name}")
        if value < 0:
            raise ValueError(f"negative_{info.field_name}")
        return value

    @field_validator("allowed_first_actions")
    @classmethod
    def _validate_string_list(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        if not value:
            raise ValueError("missing_allowed_first_actions")
        for index, item in enumerate(value, start=1):
            cleaned = str(item).strip()
            if not cleaned:
                raise ValueError(f"invalid_allowed_first_actions[{index}]")
            normalized.append(cleaned)
        return normalized

    @model_validator(mode="after")
    def _cross_validate(self) -> "A2ControllerLaunchSpine":
        if self.go_on_count > self.go_on_budget:
            raise ValueError("go_on_count_exceeds_budget")

        path_fields = [
            ("launch_packet_json", self.launch_packet_json, self.launch_packet_sha256),
            ("launch_gate_result_json", self.launch_gate_result_json, self.launch_gate_result_sha256),
            ("send_text_companion_json", self.send_text_companion_json, self.send_text_companion_sha256),
            ("launch_handoff_json", self.launch_handoff_json, self.launch_handoff_sha256),
            ("send_text_path", self.send_text_path, self.send_text_sha256),
        ]
        for field_name, path_str, expected_hash in path_fields:
            actual_hash = _sha256_file(Path(path_str))
            if actual_hash != expected_hash:
                raise ValueError(f"{field_name}_hash_mismatch")

        packet = _load_model(Path(self.launch_packet_json), A2ControllerLaunchPacket)
        gate_result = _load_model(Path(self.launch_gate_result_json), A2ControllerLaunchGateResult)
        companion = _load_model(Path(self.send_text_companion_json), A2ControllerSendTextCompanion)
        handoff = _load_model(Path(self.launch_handoff_json), A2ControllerLaunchHandoff)

        validation_result = validate_packet(json.loads(Path(self.launch_packet_json).read_text(encoding="utf-8")))
        expected_gate_result = build_gate_result(
            json.loads(Path(self.launch_packet_json).read_text(encoding="utf-8")),
            validation_result,
        )
        actual_gate_result = json.loads(Path(self.launch_gate_result_json).read_text(encoding="utf-8"))
        if actual_gate_result != expected_gate_result:
            raise ValueError("launch_gate_result_content_mismatch")

        send_text_path = Path(companion.send_text_path)
        expected_companion = build_companion(Path(self.launch_packet_json), json.loads(Path(self.launch_packet_json).read_text(encoding="utf-8")), send_text_path)
        actual_companion = json.loads(Path(self.send_text_companion_json).read_text(encoding="utf-8"))
        if actual_companion != expected_companion:
            raise ValueError("send_text_companion_content_mismatch")

        expected_handoff = build_handoff(Path(self.launch_packet_json), json.loads(Path(self.launch_packet_json).read_text(encoding="utf-8")), send_text_path)
        actual_handoff = json.loads(Path(self.launch_handoff_json).read_text(encoding="utf-8"))
        if actual_handoff != expected_handoff:
            raise ValueError("launch_handoff_content_mismatch")

        shared_text_fields = (
            "model",
            "thread_class",
            "mode",
            "primary_corpus",
            "state_record",
            "current_primary_lane",
            "current_a1_queue_status",
            "stop_rule",
            "dispatch_rule",
        )
        for field_name in shared_text_fields:
            packet_value = getattr(packet, field_name)
            gate_value = getattr(gate_result, field_name)
            companion_value = getattr(companion, field_name)
            handoff_value = getattr(handoff, field_name)
            spine_value = getattr(self, field_name)
            if not (
                packet_value == gate_value == companion_value == handoff_value == spine_value
            ):
                raise ValueError(f"shared_field_mismatch:{field_name}")

        if not (
            packet.go_on_count
            == gate_result.go_on_count
            == companion.go_on_count
            == self.go_on_count
        ):
            raise ValueError("shared_field_mismatch:go_on_count")
        if not (
            packet.go_on_budget
            == gate_result.go_on_budget
            == companion.go_on_budget
            == self.go_on_budget
        ):
            raise ValueError("shared_field_mismatch:go_on_budget")

        if companion.source_packet_json != self.launch_packet_json:
            raise ValueError("companion_source_packet_mismatch")
        if handoff.source_packet_json != self.launch_packet_json:
            raise ValueError("handoff_source_packet_mismatch")
        if companion.send_text_path != self.send_text_path:
            raise ValueError("companion_send_text_path_mismatch")
        if handoff.send_text_path != self.send_text_path:
            raise ValueError("handoff_send_text_path_mismatch")
        if companion.send_text_sha256 != self.send_text_sha256:
            raise ValueError("companion_send_text_hash_mismatch")
        if handoff.send_text_sha256 != self.send_text_sha256:
            raise ValueError("handoff_send_text_hash_mismatch")

        if gate_result.status != self.launch_gate_status:
            raise ValueError("launch_gate_status_mismatch")
        if gate_result.valid != self.launch_gate_valid:
            raise ValueError("launch_gate_valid_mismatch")
        if gate_result.allowed_first_actions != self.allowed_first_actions:
            raise ValueError("allowed_first_actions_mismatch")

        if companion.queue_helper_mode != self.queue_helper_mode:
            raise ValueError("queue_helper_mode_mismatch")
        if handoff.role_label != self.handoff_role_label:
            raise ValueError("handoff_role_label_mismatch")
        if handoff.role_type != self.handoff_role_type:
            raise ValueError("handoff_role_type_mismatch")
        if handoff.role_scope != self.handoff_role_scope:
            raise ValueError("handoff_role_scope_mismatch")
        if handoff.role_scope != self.initial_bounded_scope:
            raise ValueError("handoff_role_scope_initial_scope_mismatch")
        if handoff.monitor_route.mode != self.monitor_mode:
            raise ValueError("monitor_mode_mismatch")
        if handoff.closeout_route.mode != self.closeout_mode:
            raise ValueError("closeout_mode_mismatch")
        if len(companion.read_paths) != self.read_path_count:
            raise ValueError("read_path_count_mismatch")
        if len(handoff.operator_steps) != self.operator_step_count:
            raise ValueError("operator_step_count_mismatch")
        return self

    def to_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        spine_node = "a2_controller_launch_spine"
        graph.add_node(
            spine_node,
            kind="a2_controller_launch_spine",
            model=self.model,
            launch_gate_status=self.launch_gate_status,
            queue_helper_mode=self.queue_helper_mode,
        )

        for relation, path in (
            ("launch_packet", self.launch_packet_json),
            ("launch_gate_result", self.launch_gate_result_json),
            ("send_text_companion", self.send_text_companion_json),
            ("launch_handoff", self.launch_handoff_json),
        ):
            node_id = f"{relation}:{path}"
            graph.add_node(node_id, kind=relation, path=path)
            graph.add_edge(spine_node, node_id, relation=relation)

        send_text_node = f"send_text:{self.send_text_path}"
        graph.add_node(send_text_node, kind="send_text", path=self.send_text_path)
        graph.add_edge(spine_node, send_text_node, relation="send_text")

        for relation, label in (
            ("current_primary_lane", self.current_primary_lane),
            ("current_a1_queue_status", self.current_a1_queue_status),
            ("stop_rule", self.stop_rule),
            ("dispatch_rule", self.dispatch_rule),
            ("initial_bounded_scope", self.initial_bounded_scope),
            ("monitor_mode", self.monitor_mode),
            ("closeout_mode", self.closeout_mode),
        ):
            node_id = f"{relation}:{label}"
            graph.add_node(node_id, kind=relation, label=label)
            graph.add_edge(spine_node, node_id, relation=relation)

        for action in self.allowed_first_actions:
            node_id = f"allowed_first_action:{action}"
            graph.add_node(node_id, kind="allowed_first_action", label=action)
            graph.add_edge(spine_node, node_id, relation="allowed_first_action")
        return graph

    def graph_summary(self) -> dict[str, object]:
        graph = self.to_graph()
        return {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "launch_gate_status": self.launch_gate_status,
            "queue_helper_mode": self.queue_helper_mode,
            "allowed_first_action_count": len(self.allowed_first_actions),
        }


def load_a2_controller_launch_spine(path: Path) -> A2ControllerLaunchSpine:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc
    try:
        return A2ControllerLaunchSpine.model_validate(payload)
    except ValidationError as exc:
        raise SystemExit(exc.json(indent=2)) from exc
