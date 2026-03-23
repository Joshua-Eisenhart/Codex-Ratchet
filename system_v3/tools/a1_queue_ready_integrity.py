#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from validate_a1_worker_launch_packet import validate as validate_a1_worker_launch_packet


def _load_json_if_present(path_str: str) -> dict[str, Any] | None:
    path = Path(path_str)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _sha256_file(path_str: str) -> str:
    return hashlib.sha256(Path(path_str).read_bytes()).hexdigest()


def _compare_field(
    errors: list[str],
    *,
    surface: str,
    field: str,
    actual: Any,
    expected: Any,
) -> None:
    if actual != expected:
        errors.append(f"{surface}_{field}_mismatch")


def _compare_dict_field(
    errors: list[str],
    *,
    surface: str,
    field: str,
    actual: Any,
    expected: Any,
) -> None:
    if dict(actual or {}) != dict(expected or {}):
        errors.append(f"{surface}_{field}_mismatch")


def validate_ready_queue_artifact_coherence(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if not str(packet.get("ready_packet_json", "")).strip():
        return errors

    ready_packet_path = str(packet.get("ready_packet_json", "")).strip()
    ready_packet = _load_json_if_present(ready_packet_path)
    if ready_packet is None:
        return errors

    ready_packet_validation = validate_a1_worker_launch_packet(ready_packet)
    if not ready_packet_validation.get("valid"):
        errors.append(
            f"invalid_ready_packet_json:{ready_packet_validation['errors'][0]}"
        )
        return errors

    for field in (
        "dispatch_id",
        "target_a1_role",
        "required_a1_boot",
        "bounded_scope",
        "stop_rule",
        "go_on_count",
        "go_on_budget",
        "queue_status",
        "family_slice_validation_requested_mode",
        "family_slice_validation_resolved_mode",
        "family_slice_validation_source",
    ):
        _compare_field(
            errors,
            surface="ready_packet",
            field=field,
            actual=ready_packet.get(field, ""),
            expected=packet.get(field, ""),
        )
    for field in (
        "family_slice_validation_requested_provenance",
        "family_slice_validation_resolved_provenance",
    ):
        _compare_dict_field(
            errors,
            surface="ready_packet",
            field=field,
            actual=ready_packet.get(field, {}),
            expected=packet.get(field, {}),
        )

    _compare_field(
        errors,
        surface="ready_packet",
        field="source_a2_artifacts",
        actual=list(ready_packet.get("source_a2_artifacts", [])),
        expected=list(packet.get("source_a2_artifacts", [])),
    )
    _compare_field(
        errors,
        surface="ready_packet",
        field="a1_reload_artifacts",
        actual=list(ready_packet.get("a1_reload_artifacts", [])),
        expected=list(packet.get("a1_reload_artifacts", [])),
    )
    if str(packet.get("family_slice_json", "")).strip() not in list(ready_packet.get("source_a2_artifacts", [])):
        errors.append("family_slice_json_not_in_ready_packet_source_a2_artifacts")

    if packet.get("ready_surface_kind") != "A1_LAUNCH_BUNDLE":
        return errors

    bundle_result_path = str(packet.get("ready_bundle_result_json", "")).strip()
    send_text_companion_path = str(packet.get("ready_send_text_companion_json", "")).strip()
    launch_spine_path = str(packet.get("ready_launch_spine_json", "")).strip()

    bundle_result = _load_json_if_present(bundle_result_path)
    send_text_companion = _load_json_if_present(send_text_companion_path)
    launch_spine = _load_json_if_present(launch_spine_path)
    if bundle_result is None or send_text_companion is None or launch_spine is None:
        return errors

    _compare_field(
        errors,
        surface="ready_bundle_result",
        field="status",
        actual=bundle_result.get("status", ""),
        expected="READY",
    )
    _compare_field(
        errors,
        surface="ready_bundle_result",
        field="thread_class",
        actual=bundle_result.get("thread_class", ""),
        expected="A1_WORKER",
    )
    _compare_field(
        errors,
        surface="ready_bundle_result",
        field="packet_json",
        actual=bundle_result.get("packet_json", ""),
        expected=ready_packet_path,
    )
    for field in (
        "family_slice_validation_requested_mode",
        "family_slice_validation_resolved_mode",
        "family_slice_validation_source",
    ):
        _compare_field(
            errors,
            surface="ready_bundle_result",
            field=field,
            actual=bundle_result.get(field, ""),
            expected=packet.get(field, ""),
        )
    for field in (
        "family_slice_validation_requested_provenance",
        "family_slice_validation_resolved_provenance",
    ):
        _compare_dict_field(
            errors,
            surface="ready_bundle_result",
            field=field,
            actual=bundle_result.get(field, {}),
            expected=packet.get(field, {}),
        )

    _compare_field(
        errors,
        surface="ready_send_text_companion",
        field="source_packet_json",
        actual=send_text_companion.get("source_packet_json", ""),
        expected=ready_packet_path,
    )
    for field in (
        "dispatch_id",
        "target_a1_role",
        "required_a1_boot",
        "bounded_scope",
        "stop_rule",
        "go_on_count",
        "go_on_budget",
        "queue_status",
    ):
        _compare_field(
            errors,
            surface="ready_send_text_companion",
            field=field,
            actual=send_text_companion.get(field, ""),
            expected=ready_packet.get(field, ""),
        )
    _compare_field(
        errors,
        surface="ready_send_text_companion",
        field="source_a2_artifacts",
        actual=list(send_text_companion.get("source_a2_artifacts", [])),
        expected=list(ready_packet.get("source_a2_artifacts", [])),
    )
    _compare_field(
        errors,
        surface="ready_send_text_companion",
        field="a1_reload_artifacts",
        actual=list(send_text_companion.get("a1_reload_artifacts", [])),
        expected=list(ready_packet.get("a1_reload_artifacts", [])),
    )

    gate_result_path = str(bundle_result.get("gate_result_json", "")).strip()
    handoff_path = str(bundle_result.get("handoff_json", "")).strip()
    _compare_field(
        errors,
        surface="ready_launch_spine",
        field="launch_packet_json",
        actual=launch_spine.get("launch_packet_json", ""),
        expected=ready_packet_path,
    )
    _compare_field(
        errors,
        surface="ready_launch_spine",
        field="launch_gate_result_json",
        actual=launch_spine.get("launch_gate_result_json", ""),
        expected=gate_result_path,
    )
    _compare_field(
        errors,
        surface="ready_launch_spine",
        field="send_text_companion_json",
        actual=launch_spine.get("send_text_companion_json", ""),
        expected=send_text_companion_path,
    )
    _compare_field(
        errors,
        surface="ready_launch_spine",
        field="launch_handoff_json",
        actual=launch_spine.get("launch_handoff_json", ""),
        expected=handoff_path,
    )
    for field in (
        "dispatch_id",
        "target_a1_role",
        "required_a1_boot",
        "bounded_scope",
        "stop_rule",
        "go_on_count",
        "go_on_budget",
        "queue_status",
    ):
        _compare_field(
            errors,
            surface="ready_launch_spine",
            field=field,
            actual=launch_spine.get(field, ""),
            expected=ready_packet.get(field, ""),
        )
    _compare_field(
        errors,
        surface="ready_launch_spine",
        field="source_a2_artifacts",
        actual=list(launch_spine.get("source_a2_artifacts", [])),
        expected=list(ready_packet.get("source_a2_artifacts", [])),
    )
    _compare_field(
        errors,
        surface="ready_launch_spine",
        field="a1_reload_artifacts",
        actual=list(launch_spine.get("a1_reload_artifacts", [])),
        expected=list(ready_packet.get("a1_reload_artifacts", [])),
    )
    _compare_field(
        errors,
        surface="ready_launch_spine",
        field="launch_packet_sha256",
        actual=launch_spine.get("launch_packet_sha256", ""),
        expected=_sha256_file(ready_packet_path),
    )
    _compare_field(
        errors,
        surface="ready_launch_spine",
        field="send_text_companion_sha256",
        actual=launch_spine.get("send_text_companion_sha256", ""),
        expected=_sha256_file(send_text_companion_path),
    )
    _compare_field(
        errors,
        surface="ready_launch_spine",
        field="send_text_sha256",
        actual=launch_spine.get("send_text_sha256", ""),
        expected=send_text_companion.get("send_text_sha256", ""),
    )

    return errors
