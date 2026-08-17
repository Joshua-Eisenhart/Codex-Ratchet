from __future__ import annotations

from pathlib import Path

import pytest

from constraintbox.ingress_capture import (
    CaptureError,
    capture_and_validate,
    capture_event,
    make_transport_result,
    validate_controller_result,
    verify_capture,
)


def _payload(command: str = "printf probe") -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }


def test_capture_identity_is_replayable_and_bound(tmp_path: Path) -> None:
    first = capture_event(
        _payload(), host="fixture", command="printf probe", capture_root=tmp_path
    )
    replay = capture_event(
        _payload(), host="fixture", command="printf probe", capture_root=tmp_path
    )
    changed_command = capture_event(
        _payload("printf changed"),
        host="fixture",
        command="printf changed",
        capture_root=tmp_path,
    )
    changed_host = capture_event(
        _payload(), host="other", command="printf probe", capture_root=tmp_path
    )
    assert replay["capture_id"] == first["capture_id"]
    assert replay["capture_receipt_sha256"] == first["capture_receipt_sha256"]
    assert changed_command["capture_id"] != first["capture_id"]
    assert changed_host["capture_id"] != first["capture_id"]
    assert len(list(tmp_path.glob("*.json"))) == 3


def test_capture_receipt_is_required_for_result_validation(tmp_path: Path) -> None:
    payload = _payload()
    capture = capture_event(
        payload, host="fixture", command="printf probe", capture_root=tmp_path
    )
    Path(capture["capture_receipt_path"]).unlink()
    with pytest.raises(CaptureError) as error:
        verify_capture(capture, payload=payload, host="fixture", command="printf probe")
    assert error.value.reason_code == "REFUSE_CAPTURE_RECEIPT_UNREADABLE"


def test_missing_controller_cannot_be_success(tmp_path: Path) -> None:
    with pytest.raises(CaptureError) as error:
        capture_and_validate(
            _payload(),
            host="fixture",
            command="printf probe",
            capture_root=tmp_path,
        )
    assert error.value.reason_code == "REFUSE_CONTROLLER_MISSING"


def test_withhold_result_cannot_be_overridden(tmp_path: Path) -> None:
    capture, result = capture_and_validate(
        _payload(),
        host="fixture",
        command="printf probe",
        capture_root=tmp_path,
        controller=lambda bound: make_transport_result(bound, action="withhold"),
    )
    assert result["allow"] is False
    assert result["disposition"] == "WITHHOLD_UNAUTHORITY"
    assert result["capture_id"] == capture["capture_id"]


def test_wrong_result_binding_refuses(tmp_path: Path) -> None:
    capture = capture_event(
        _payload(), host="fixture", command="printf probe", capture_root=tmp_path
    )
    result = make_transport_result(capture)
    result["command_sha256"] = "0" * 64
    with pytest.raises(CaptureError) as error:
        validate_controller_result(capture, result)
    assert error.value.reason_code == "REFUSE_CONTROLLER_RESULT_BINDING_MISMATCH"


def test_result_extra_fields_refuse(tmp_path: Path) -> None:
    capture = capture_event(
        _payload(), host="fixture", command="printf probe", capture_root=tmp_path
    )
    result = {**make_transport_result(capture), "override": True}
    with pytest.raises(CaptureError) as error:
        validate_controller_result(capture, result)
    assert error.value.reason_code == "REFUSE_CONTROLLER_RESULT_SHAPE"
