#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from a1_worker_launch_gate_result_models import A1WorkerLaunchGateResult
from a1_worker_launch_handoff_models import A1WorkerLaunchHandoff
from a1_worker_launch_packet_models import A1WorkerLaunchPacket
from a1_worker_send_text_companion_models import A1WorkerSendTextCompanion
from build_a1_worker_launch_handoff import build_handoff
from build_a1_worker_send_text_companion import build_companion
from run_a1_worker_launch_from_packet import build_result as build_gate_result
from validate_a1_worker_launch_packet import validate as validate_packet


SCHEMA = "A1_WORKER_LAUNCH_SPINE_v1"
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


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_model(path: Path, model_cls):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc
    return model_cls.model_validate(payload)


class A1WorkerLaunchSpine(BaseModel):
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
    queue_status: str
    dispatch_id: str
    target_a1_role: str
    required_a1_boot: str
    source_a2_artifacts: list[str]
    a1_reload_artifacts: list[str]
    bounded_scope: str
    stop_rule: str
    go_on_count: int
    go_on_budget: int
    launch_gate_status: str
    launch_gate_valid: bool
    read_path_count: int
    handoff_role_label: str
    handoff_role_type: str
    handoff_role_scope: str
    operator_step_count: int
    monitor_skill: str

    @field_validator(
        "launch_packet_json",
        "launch_gate_result_json",
        "send_text_companion_json",
        "launch_handoff_json",
        "send_text_path",
        "required_a1_boot",
        "monitor_skill",
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
        "queue_status",
        "dispatch_id",
        "target_a1_role",
        "bounded_scope",
        "stop_rule",
        "launch_gate_status",
        "handoff_role_label",
        "handoff_role_type",
        "handoff_role_scope",
    )
    @classmethod
    def _validate_text(cls, value: str, info) -> str:
        cleaned = str(value).strip()
        if not cleaned:
            raise ValueError(f"missing_{info.field_name}")
        return cleaned

    @field_validator("source_a2_artifacts", "a1_reload_artifacts")
    @classmethod
    def _validate_path_lists(cls, value: list[str], info) -> list[str]:
        normalized: list[str] = []
        if info.field_name == "source_a2_artifacts" and not value:
            raise ValueError("missing_source_a2_artifacts")
        for index, item in enumerate(value, start=1):
            normalized.append(_require_abs_existing_text(item, f"{info.field_name}[{index}]"))
        return normalized

    @field_validator("go_on_count", "go_on_budget", "read_path_count", "operator_step_count")
    @classmethod
    def _validate_nonnegative_int(cls, value: int, info) -> int:
        if not isinstance(value, int):
            raise ValueError(f"invalid_{info.field_name}")
        if value < 0:
            raise ValueError(f"negative_{info.field_name}")
        return value

    @model_validator(mode="after")
    def _cross_validate(self) -> "A1WorkerLaunchSpine":
        if self.go_on_count > self.go_on_budget:
            raise ValueError("go_on_count_exceeds_budget")

        for field_name, path_str, expected_hash in (
            ("launch_packet_json", self.launch_packet_json, self.launch_packet_sha256),
            ("launch_gate_result_json", self.launch_gate_result_json, self.launch_gate_result_sha256),
            ("send_text_companion_json", self.send_text_companion_json, self.send_text_companion_sha256),
            ("launch_handoff_json", self.launch_handoff_json, self.launch_handoff_sha256),
            ("send_text_path", self.send_text_path, self.send_text_sha256),
        ):
            if _sha256_file(Path(path_str)) != expected_hash:
                raise ValueError(f"{field_name}_hash_mismatch")

        packet = _load_model(Path(self.launch_packet_json), A1WorkerLaunchPacket)
        gate_result = _load_model(Path(self.launch_gate_result_json), A1WorkerLaunchGateResult)
        companion = _load_model(Path(self.send_text_companion_json), A1WorkerSendTextCompanion)
        handoff = _load_model(Path(self.launch_handoff_json), A1WorkerLaunchHandoff)

        packet_payload = json.loads(Path(self.launch_packet_json).read_text(encoding="utf-8"))
        validation_result = validate_packet(packet_payload)
        expected_gate_result = build_gate_result(packet_payload, validation_result)
        actual_gate_result = json.loads(Path(self.launch_gate_result_json).read_text(encoding="utf-8"))
        if actual_gate_result != expected_gate_result:
            raise ValueError("launch_gate_result_content_mismatch")

        send_text_path = Path(companion.send_text_path)
        expected_companion = build_companion(Path(self.launch_packet_json), packet_payload, send_text_path)
        actual_companion = json.loads(Path(self.send_text_companion_json).read_text(encoding="utf-8"))
        if actual_companion != expected_companion:
            raise ValueError("send_text_companion_content_mismatch")

        expected_handoff = build_handoff(Path(self.launch_packet_json), packet_payload, send_text_path)
        actual_handoff = json.loads(Path(self.launch_handoff_json).read_text(encoding="utf-8"))
        if actual_handoff != expected_handoff:
            raise ValueError("launch_handoff_content_mismatch")

        for field_name in (
            "model",
            "thread_class",
            "mode",
            "queue_status",
            "dispatch_id",
            "target_a1_role",
            "required_a1_boot",
            "bounded_scope",
            "stop_rule",
        ):
            packet_value = getattr(packet, field_name)
            gate_value = getattr(gate_result, field_name)
            companion_value = getattr(companion, field_name)
            handoff_value = getattr(handoff, field_name if field_name not in {"target_a1_role", "bounded_scope"} else ("role_type" if field_name == "target_a1_role" else "role_scope"))
            spine_value = getattr(self, field_name)
            if not (packet_value == gate_value == companion_value == handoff_value == spine_value):
                raise ValueError(f"shared_field_mismatch:{field_name}")

        if packet.source_a2_artifacts != gate_result.source_a2_artifacts or packet.source_a2_artifacts != companion.source_a2_artifacts or packet.source_a2_artifacts != handoff.source_a2_artifacts or packet.source_a2_artifacts != self.source_a2_artifacts:
            raise ValueError("shared_field_mismatch:source_a2_artifacts")
        if packet.a1_reload_artifacts != gate_result.a1_reload_artifacts or packet.a1_reload_artifacts != companion.a1_reload_artifacts or packet.a1_reload_artifacts != handoff.a1_reload_artifacts or packet.a1_reload_artifacts != self.a1_reload_artifacts:
            raise ValueError("shared_field_mismatch:a1_reload_artifacts")
        if packet.go_on_count != gate_result.go_on_count or packet.go_on_count != companion.go_on_count or packet.go_on_count != self.go_on_count:
            raise ValueError("shared_field_mismatch:go_on_count")
        if packet.go_on_budget != gate_result.go_on_budget or packet.go_on_budget != companion.go_on_budget or packet.go_on_budget != self.go_on_budget:
            raise ValueError("shared_field_mismatch:go_on_budget")

        if companion.source_packet_json != self.launch_packet_json or handoff.source_packet_json != self.launch_packet_json:
            raise ValueError("source_packet_json_mismatch")
        if companion.send_text_path != self.send_text_path or handoff.send_text_path != self.send_text_path:
            raise ValueError("send_text_path_mismatch")
        if companion.send_text_sha256 != self.send_text_sha256 or handoff.send_text_sha256 != self.send_text_sha256:
            raise ValueError("send_text_sha256_mismatch")
        if gate_result.status != self.launch_gate_status or gate_result.valid != self.launch_gate_valid:
            raise ValueError("launch_gate_status_mismatch")
        if companion.read_path_count != self.read_path_count:
            raise ValueError("read_path_count_mismatch")
        if handoff.role_label != self.handoff_role_label or handoff.role_type != self.handoff_role_type or handoff.role_scope != self.handoff_role_scope:
            raise ValueError("handoff_role_mismatch")
        if len(handoff.operator_steps) != self.operator_step_count:
            raise ValueError("operator_step_count_mismatch")
        if handoff.monitor_route.skill != self.monitor_skill:
            raise ValueError("monitor_skill_mismatch")
        return self

    def to_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        spine_node = "a1_worker_launch_spine"
        graph.add_node(
            spine_node,
            kind="a1_worker_launch_spine",
            launch_gate_status=self.launch_gate_status,
            target_a1_role=self.target_a1_role,
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
        send_node = f"send_text:{self.send_text_path}"
        graph.add_node(send_node, kind="send_text", path=self.send_text_path)
        graph.add_edge(spine_node, send_node, relation="send_text")
        return graph

    def graph_summary(self) -> dict[str, object]:
        graph = self.to_graph()
        return {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "launch_gate_status": self.launch_gate_status,
            "target_a1_role": self.target_a1_role,
            "read_path_count": self.read_path_count,
        }


def load_a1_worker_launch_spine(path: Path) -> A1WorkerLaunchSpine:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc
    try:
        return A1WorkerLaunchSpine.model_validate(payload)
    except ValidationError as exc:
        raise SystemExit(exc.json(indent=2)) from exc
