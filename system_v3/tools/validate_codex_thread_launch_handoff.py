#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


ALLOWED_SCHEMAS = {
    "A2_CONTROLLER_LAUNCH_HANDOFF_v1",
    "A2_WORKER_LAUNCH_HANDOFF_v1",
    "A1_WORKER_LAUNCH_HANDOFF_v1",
}
ALLOWED_THREAD_CLASSES = {"A2_CONTROLLER", "A2_WORKER", "A1_WORKER"}


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _is_nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_abs_existing_file(value: object) -> bool:
    if not _is_nonempty_text(value):
        return False
    path = Path(str(value).strip())
    return path.is_absolute() and path.exists() and path.is_file()


def _is_abs_existing_path(value: object) -> bool:
    if not _is_nonempty_text(value):
        return False
    path = Path(str(value).strip())
    return path.is_absolute() and path.exists()


def _is_abs_path(value: object) -> bool:
    if not _is_nonempty_text(value):
        return False
    return Path(str(value).strip()).is_absolute()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require_send_text_markers(
    *,
    handoff: dict,
    send_text_path: Path,
    errors: list[str],
    required_markers: list[str],
) -> None:
    expected_hash = str(handoff.get("send_text_sha256", "")).strip()
    if not expected_hash:
        errors.append("missing_send_text_sha256")
        return
    actual_hash = _sha256_file(send_text_path)
    if actual_hash != expected_hash:
        errors.append("send_text_hash_mismatch")

    send_text = _read_text(send_text_path)
    for marker in required_markers:
        if marker not in send_text:
            errors.append(f"send_text_missing_marker:{marker}")


def _validate_common(handoff: dict, errors: list[str]) -> None:
    if handoff.get("schema") not in ALLOWED_SCHEMAS:
        errors.append("invalid_schema")
    if handoff.get("thread_class") not in ALLOWED_THREAD_CLASSES:
        errors.append("invalid_thread_class")
    if not _is_abs_existing_file(handoff.get("source_packet_json")):
        errors.append("invalid_source_packet_json")
    if not _is_abs_existing_file(handoff.get("send_text_path")):
        errors.append("invalid_send_text_path")
    for key in ("role_label", "role_type", "role_scope", "model", "mode"):
        if not _is_nonempty_text(handoff.get(key)):
            errors.append(f"missing_{key}")
    operator_steps = handoff.get("operator_steps")
    if not isinstance(operator_steps, list) or not operator_steps or not all(
        _is_nonempty_text(step) for step in operator_steps
    ):
        errors.append("invalid_operator_steps")
    if not isinstance(handoff.get("monitor_route"), dict):
        errors.append("invalid_monitor_route")
    if not isinstance(handoff.get("closeout_route"), dict):
        errors.append("invalid_closeout_route")


def _validate_a2(handoff: dict, errors: list[str]) -> None:
    if handoff.get("thread_class") != "A2_CONTROLLER":
        errors.append("a2_thread_class_mismatch")
    if handoff.get("role_type") != "A2_CONTROLLER":
        errors.append("a2_role_type_mismatch")
    if not _is_abs_existing_path(handoff.get("primary_corpus")):
        errors.append("invalid_primary_corpus")
    if not _is_abs_existing_file(handoff.get("state_record")):
        errors.append("invalid_state_record")
    if not _is_nonempty_text(handoff.get("current_primary_lane")):
        errors.append("missing_current_primary_lane")
    if not _is_nonempty_text(handoff.get("current_a1_queue_status")):
        errors.append("missing_current_a1_queue_status")
    for key in ("stop_rule", "dispatch_rule"):
        if not _is_nonempty_text(handoff.get(key)):
            errors.append(f"missing_{key}")
    send_text_path = Path(str(handoff.get("send_text_path", "")).strip())
    if send_text_path.is_absolute() and send_text_path.exists() and send_text_path.is_file():
        _require_send_text_markers(
            handoff=handoff,
            send_text_path=send_text_path,
            errors=errors,
            required_markers=[
                "You are a fresh A2 controller thread.",
                f"MODEL: {handoff.get('model', '')}",
                f"THREAD_CLASS: {handoff.get('thread_class', '')}",
                f"MODE: {handoff.get('mode', '')}",
                f"PRIMARY_CORPUS: {handoff.get('primary_corpus', '')}",
                f"STATE_RECORD: {handoff.get('state_record', '')}",
                f"CURRENT_PRIMARY_LANE: {handoff.get('current_primary_lane', '')}",
                f"CURRENT_A1_QUEUE_STATUS: {handoff.get('current_a1_queue_status', '')}",
                f"STOP_RULE: {handoff.get('stop_rule', '')}",
                f"DISPATCH_RULE: {handoff.get('dispatch_rule', '')}",
                f"INITIAL_BOUNDED_SCOPE: {handoff.get('role_scope', '')}",
            ],
        )


def _validate_a2_worker(handoff: dict, errors: list[str]) -> None:
    if handoff.get("thread_class") != "A2_WORKER":
        errors.append("a2_worker_thread_class_mismatch")
    if not _is_nonempty_text(handoff.get("dispatch_id")):
        errors.append("missing_dispatch_id")
    if not _is_abs_existing_file(handoff.get("required_a2_boot")):
        errors.append("invalid_required_a2_boot")
    artifacts = handoff.get("source_artifacts")
    if not isinstance(artifacts, list) or not artifacts or not all(_is_abs_existing_file(path) for path in artifacts):
        errors.append("invalid_source_artifacts")
    if not _is_abs_path(handoff.get("return_capture_path")):
        errors.append("invalid_return_capture_path")
    if not _is_nonempty_text(handoff.get("stop_rule")):
        errors.append("missing_stop_rule")
    if handoff.get("mode") != "A2_ONLY":
        errors.append("a2_worker_mode_mismatch")
    send_text_path = Path(str(handoff.get("send_text_path", "")).strip())
    if send_text_path.is_absolute() and send_text_path.exists() and send_text_path.is_file():
        artifact_markers = [
            "source_artifacts:",
            *(f"- {path}" for path in handoff.get("source_artifacts", []) if _is_nonempty_text(path)),
        ]
        _require_send_text_markers(
            handoff=handoff,
            send_text_path=send_text_path,
            errors=errors,
            required_markers=[
                "You are an A2 Codex worker thread.",
                f"- {handoff.get('required_a2_boot', '')}",
                f"MODEL: {handoff.get('model', '')}",
                f"THREAD_CLASS: {handoff.get('thread_class', '')}",
                f"MODE: {handoff.get('mode', '')}",
                f"dispatch_id: {handoff.get('dispatch_id', '')}",
                f"ROLE_LABEL: {handoff.get('role_label', '')}",
                f"ROLE_TYPE: {handoff.get('role_type', '')}",
                f"ROLE_SCOPE: {handoff.get('role_scope', '')}",
                f"required_a2_boot: {handoff.get('required_a2_boot', '')}",
                f"stop_rule: {handoff.get('stop_rule', '')}",
                *artifact_markers,
            ],
        )


def _validate_a1(handoff: dict, errors: list[str]) -> None:
    if handoff.get("thread_class") != "A1_WORKER":
        errors.append("a1_thread_class_mismatch")
    for key in ("dispatch_id", "queue_status"):
        if not _is_nonempty_text(handoff.get(key)):
            errors.append(f"missing_{key}")
    if not _is_abs_path(handoff.get("return_capture_path")):
        errors.append("invalid_return_capture_path")
    if not _is_abs_existing_file(handoff.get("required_a1_boot")):
        errors.append("invalid_required_a1_boot")
    reload_artifacts = handoff.get("a1_reload_artifacts", [])
    if reload_artifacts is None:
        reload_artifacts = []
    if not isinstance(reload_artifacts, list) or not all(
        _is_abs_existing_file(path) for path in reload_artifacts
    ):
        errors.append("invalid_a1_reload_artifacts")
    artifacts = handoff.get("source_a2_artifacts")
    if not isinstance(artifacts, list) or not artifacts or not all(_is_abs_existing_file(path) for path in artifacts):
        errors.append("invalid_source_a2_artifacts")
    if not _is_nonempty_text(handoff.get("stop_rule")):
        errors.append("missing_stop_rule")
    send_text_path = Path(str(handoff.get("send_text_path", "")).strip())
    if send_text_path.is_absolute() and send_text_path.exists() and send_text_path.is_file():
        reload_markers = []
        if reload_artifacts:
            reload_markers = [
                "a1_reload_artifacts:",
                *(f"- {path}" for path in reload_artifacts if _is_nonempty_text(path)),
            ]
        artifact_markers = [
            "source_a2_artifacts:",
            *(f"- {path}" for path in handoff.get("source_a2_artifacts", []) if _is_nonempty_text(path)),
        ]
        _require_send_text_markers(
            handoff=handoff,
            send_text_path=send_text_path,
            errors=errors,
            required_markers=[
                "You are an A1 Codex thread.",
                f"- {handoff.get('required_a1_boot', '')}",
                f"MODEL: {handoff.get('model', '')}",
                f"THREAD_CLASS: {handoff.get('thread_class', '')}",
                f"MODE: {handoff.get('mode', '')}",
                f"A1_QUEUE_STATUS: {handoff.get('queue_status', '')}",
                f"dispatch_id: {handoff.get('dispatch_id', '')}",
                f"target_a1_role: {handoff.get('role_type', '')}",
                f"bounded_scope: {handoff.get('role_scope', '')}",
                f"stop_rule: {handoff.get('stop_rule', '')}",
                *reload_markers,
                *artifact_markers,
            ],
        )


def validate(handoff: dict) -> dict:
    errors: list[str] = []
    _validate_common(handoff, errors)

    schema = handoff.get("schema")
    if schema == "A2_CONTROLLER_LAUNCH_HANDOFF_v1":
        _validate_a2(handoff, errors)
    elif schema == "A2_WORKER_LAUNCH_HANDOFF_v1":
        _validate_a2_worker(handoff, errors)
    elif schema == "A1_WORKER_LAUNCH_HANDOFF_v1":
        _validate_a1(handoff, errors)

    return {
        "schema": "CODEX_THREAD_LAUNCH_HANDOFF_VALIDATION_RESULT_v1",
        "valid": not errors,
        "errors": errors,
        "thread_class": handoff.get("thread_class", ""),
        "role_type": handoff.get("role_type", ""),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate one A2 controller, A2 worker, or A1 worker launch handoff packet."
    )
    parser.add_argument("--launch-handoff-json", required=True)
    parser.add_argument("--out-json")
    args = parser.parse_args(argv)

    result = validate(_load_json(Path(args.launch_handoff_json)))
    if args.out_json:
        out_path = Path(args.out_json)
        if not out_path.is_absolute():
            raise SystemExit("non_absolute_out_json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
