from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from hookkernel.cb_light_runtime import MANDATED_INTERPRETER

import constraintbox.control_plane as control_plane
from constraintbox.control_plane import (
    ControlPlaneError,
    PIN_FILE,
    run_candidate_evaluation,
    sha256_file,
)

def _seed_state(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    db_path = tmp_path / "cb_light.sqlite"
    output_path = tmp_path / "gate.json"
    completed = subprocess.run(
        [
            # The state being consumed must originate from the actual
            # contained Light gate. The separate Pydantic control-plane
            # profile is only the typed consumer, never the probe executor.
            str(MANDATED_INTERPRETER),
            "-I",
            "-m",
            "constraintbox.core_cli",
            "cb-light",
            "--db",
            str(db_path),
            "probe",
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    body = json.loads(completed.stdout)
    assert output_path.is_file()
    return db_path, {
        "snapshot_id": body["snapshot_id"],
        "probe_run_id": body["probe_run_id"],
        "selection_id": body["selection_id"],
    }


def _request(binding: dict[str, str], request_id: str) -> dict[str, object]:
    return {
        "schema": "constraintbox.control-plane-request.v1",
        "request_id": request_id,
        "operation": "candidate_evaluation",
        "candidate_id": "pydantic",
        **binding,
        "candidate_pin_sha256": sha256_file(PIN_FILE),
        "capabilities": ["schema_envelope"],
    }


def _operation_count(db_path: Path) -> int:
    connection = sqlite3.connect(db_path)
    try:
        return int(
            connection.execute("SELECT COUNT(*) FROM candidate_evaluation").fetchone()[
                0
            ]
        )
    finally:
        connection.close()


def test_strict_candidate_request_consumes_selection_and_replays(tmp_path: Path):
    db_path, binding = _seed_state(tmp_path)
    request = _request(binding, "pydantic-replay")

    first = run_candidate_evaluation(request, db_path=db_path)
    second = run_candidate_evaluation(request, db_path=db_path)

    assert first["disposition"] == "CANDIDATE_EVALUATED_LOCAL"
    assert first["reason_code"] == "STRICT_PACKET_AND_SELECTION_BOUND"
    assert first["probe_interpreter"] == str(MANDATED_INTERPRETER)
    assert first["light_runtime_interpreter"] == str(MANDATED_INTERPRETER)
    assert first["control_plane_runtime"]["interpreter"] == sys.executable
    assert first["control_plane_runtime"]["pydantic_version"] == "2.12.5"
    assert first["control_plane_runtime"]["jsonschema_version"] == "4.26.0"
    assert second["operation_id"] == first["operation_id"]
    assert _operation_count(db_path) == 1


def test_extra_field_and_capability_boundary_refuse_before_sqlite_write(tmp_path: Path):
    db_path, binding = _seed_state(tmp_path)
    extra = _request(binding, "pydantic-extra")
    extra["unexpected"] = True

    extra_result = run_candidate_evaluation(extra, db_path=db_path)

    boundary = _request(binding, "pydantic-capability")
    boundary["capabilities"] = ["provider_launch"]
    boundary_result = run_candidate_evaluation(boundary, db_path=db_path)

    assert extra_result["reason_code"] == "REFUSE_UNEXPECTED_FIELD"
    assert boundary_result["reason_code"] == "REFUSE_UNDECLARED_CAPABILITY"
    assert _operation_count(db_path) == 0


def test_selection_triple_mismatch_refuses_before_sqlite_write(tmp_path: Path):
    db_path, binding = _seed_state(tmp_path)
    request = _request(binding, "pydantic-stale")
    request["snapshot_id"] = "0" * 64

    result = run_candidate_evaluation(request, db_path=db_path)

    assert result["disposition"] == "REFUSE"
    assert result["reason_code"] == "REFUSE_SELECTION_TRIPLE_MISMATCH"
    assert _operation_count(db_path) == 0


def test_probe_interpreter_mismatch_holds_before_sqlite_write(tmp_path: Path):
    db_path, binding = _seed_state(tmp_path)
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            "UPDATE probe_run SET interpreter = ? WHERE run_id = ?",
            ("/not-the-contained-cb-light-python", binding["probe_run_id"]),
        )
        connection.commit()
    finally:
        connection.close()

    result = run_candidate_evaluation(
        _request(binding, "pydantic-interpreter-mismatch"), db_path=db_path
    )

    assert result["disposition"] == "HOLD"
    assert result["reason_code"] == "HOLD_LIGHT_PROBE_RUNTIME_MISMATCH"
    assert _operation_count(db_path) == 0


def test_probe_interpreter_symlink_alias_holds_before_sqlite_write(tmp_path: Path):
    db_path, binding = _seed_state(tmp_path)
    alias = tmp_path / "other-contained-runtime" / "python"
    alias.parent.mkdir()
    alias.symlink_to(MANDATED_INTERPRETER)
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            "UPDATE probe_run SET interpreter = ? WHERE run_id = ?",
            (str(alias), binding["probe_run_id"]),
        )
        connection.commit()
    finally:
        connection.close()

    result = run_candidate_evaluation(
        _request(binding, "pydantic-interpreter-symlink-alias"), db_path=db_path
    )

    assert result["disposition"] == "HOLD"
    assert result["reason_code"] == "HOLD_LIGHT_PROBE_RUNTIME_MISMATCH"
    assert _operation_count(db_path) == 0


def test_raw_mapping_severance_is_held_before_sqlite_write(tmp_path: Path):
    db_path, binding = _seed_state(tmp_path)
    request = _request(binding, "pydantic-severance")

    result = run_candidate_evaluation(
        request,
        db_path=db_path,
        validator=lambda raw: dict(raw),
    )

    assert result["disposition"] == "HOLD"
    assert result["reason_code"] == "HOLD_VALIDATED_ENVELOPE_REQUIRED"
    assert _operation_count(db_path) == 0


def test_missing_control_plane_dependency_holds_before_sqlite_write(tmp_path: Path):
    db_path, binding = _seed_state(tmp_path)

    def missing_dependency(_raw: object):
        raise ControlPlaneError(
            "HOLD_CONTROL_PLANE_DEPENDENCY_MISSING",
            "Pydantic is unavailable in the executing interpreter.",
        )

    result = run_candidate_evaluation(
        _request(binding, "pydantic-dependency-severance"),
        db_path=db_path,
        validator=missing_dependency,
    )

    assert result["disposition"] == "HOLD"
    assert result["reason_code"] == "HOLD_CONTROL_PLANE_DEPENDENCY_MISSING"
    assert _operation_count(db_path) == 0


def test_control_plane_provider_version_drift_holds_before_sqlite_write(
    tmp_path: Path, monkeypatch
):
    db_path, binding = _seed_state(tmp_path)
    real_version = control_plane.version

    def drifted_version(name: str) -> str:
        if name == "pydantic":
            return "0.0.0"
        return real_version(name)

    monkeypatch.setattr(control_plane, "version", drifted_version)

    result = run_candidate_evaluation(
        _request(binding, "pydantic-provider-version-drift"), db_path=db_path
    )

    assert result["disposition"] == "HOLD"
    assert result["reason_code"] == "HOLD_CONTROL_PLANE_PROVIDER_VERSION_MISMATCH"
    assert _operation_count(db_path) == 0
