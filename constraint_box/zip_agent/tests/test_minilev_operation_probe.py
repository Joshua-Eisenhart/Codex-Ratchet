"""Focused tests for the contained-Light Mini-Lev ZIP adapter."""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
from pathlib import Path
import zipfile

import pytest

from constraintbox_zip_agent import minilev_operation_probe as probe
from constraintbox_zip_agent.protocol import validate_return_zip
from constraintbox_zip_agent.runtime import execute_packet


CB = Path(os.environ.get("CB_BOX_ROOT", Path(__file__).resolve().parents[2]))
LIGHT_PYTHON = Path(
    os.environ.get("CB_LIGHT_PYTHON", CB / ".venv" / "bin" / "python")
)
PIN_FILE = CB / "requirements" / "control_plane_candidates" / "cb_control_plane_candidate_pins_v1.txt"


def _run_light(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(LIGHT_PYTHON), "-I", "-m", "constraintbox.core_cli", *args],
        cwd=CB,
        capture_output=True,
        check=False,
        text=True,
        timeout=120,
    )


def _request(operation_id: str, request_id: str = "zip-probe-positive") -> dict[str, object]:
    return {
        "schema": "constraintbox.mini-lev-polynomial-request.v1",
        "bridge_request_id": request_id,
        "candidate_operation_id": operation_id,
        "task": "mini_lev.symbolic_polynomial_qq.v1",
        "payload": {
            "terms": [
                {"coefficient": {"numerator": 3, "denominator": 1}, "exponent": 2},
                {"coefficient": {"numerator": 2, "denominator": 1}, "exponent": 1},
                {"coefficient": {"numerator": 1, "denominator": 1}, "exponent": 0},
            ],
            "claimed_degree": 2,
        },
    }


@pytest.fixture(scope="module")
def seeded_state(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, str]:
    if not LIGHT_PYTHON.is_file():
        pytest.skip("contained Light interpreter is not installed")
    work = tmp_path_factory.mktemp("minilev-light-state")
    db_path = work / "cb-light.sqlite"
    probe_path = work / "probe.json"
    completed = _run_light("cb-light", "--db", str(db_path), "probe", "--output", str(probe_path))
    if completed.returncode != 0:
        pytest.skip(f"contained Light probe unavailable: {completed.stderr}")
    binding = json.loads(completed.stdout)
    control_request = {
        "schema": "constraintbox.control-plane-request.v1",
        "request_id": "zip-probe-parent",
        "operation": "candidate_evaluation",
        "candidate_id": "pydantic",
        "snapshot_id": binding["snapshot_id"],
        "probe_run_id": binding["probe_run_id"],
        "selection_id": binding["selection_id"],
        "candidate_pin_sha256": hashlib.sha256(PIN_FILE.read_bytes()).hexdigest(),
        "capabilities": ["schema_envelope"],
    }
    request_path = work / "parent-request.json"
    request_path.write_text(json.dumps(control_request), encoding="utf-8")
    evaluated = _run_light(
        "control-plane",
        "--db",
        str(db_path),
        "--request",
        str(request_path),
    )
    if evaluated.returncode != 0:
        pytest.skip(f"contained Light parent unavailable: {evaluated.stderr}")
    result = json.loads(evaluated.stdout)
    return db_path, str(result["operation_id"])


def test_installed_light_source_matches_and_never_points_at_legacy_src() -> None:
    status = probe.inspect_light_source_status()
    if not LIGHT_PYTHON.is_file():
        pytest.skip("contained Light interpreter is not installed")
    assert status["status"] == "MATCH", status
    assert status["reason_code"] == "LIGHT_INSTALLED_SOURCE_MATCH"
    for row in status["expected"].values():
        assert "/light_runtime/src/" in row["path"]
    for row in status["installed"].values():
        assert "/site-packages/" in row["origin"]
        assert "/constraint_box/src/" not in row["origin"]
    assert status["expected_source_sha256"] == status["installed_source_sha256"]


def test_unbound_light_root_holds_before_state_access(tmp_path: Path) -> None:
    # A source mismatch/root hold is fail-closed and does not even make a
    # temporary state copy.  The input path is intentionally absent.
    result = probe.run_minilev_operation(
        {"not": "a Mini-Lev request"},
        tmp_path / "no-state.sqlite",
        light_root=tmp_path / "not-a-light-root",
    )
    assert result["disposition"] == "HOLD"
    assert result["reason_code"] in {
        "HOLD_MINILEV_LIGHT_ROOT_UNBOUND",
        "REFUSE_MINILEV_REQUEST_NOT_CANONICAL",
    }
    assert result["state_copy_only"] is True


def test_one_operation_is_canonical_and_does_not_write_caller_state(
    seeded_state: tuple[Path, str],
) -> None:
    db_path, operation_id = seeded_state
    request = _request(operation_id)
    original = json.loads(json.dumps(request, sort_keys=True))
    before_bytes = hashlib.sha256(db_path.read_bytes()).hexdigest()
    result = probe.run_minilev_operation(request, db_path)
    assert request == original
    assert result["disposition"] == "SUCCEEDED"
    assert result["reason_code"] == "MINILEV_TYPED_SYMBOLIC_CVC5_Z3_BOUND"
    assert result["result"]["disposition"] == probe.LIGHT_SUCCESS
    assert result["source"]["status"] == "MATCH"
    assert result["receipt"]["state_copy_only"] is True
    assert result["receipt"]["source_state_unchanged"] is True
    assert result["receipt"]["no_write_on_refusal"] is False
    assert result["state_before"]["logical_sha256"] != result["state_after"]["logical_sha256"]
    assert hashlib.sha256(db_path.read_bytes()).hexdigest() == before_bytes


def test_cohort_records_replay_mutation_boundary_actual_role_ablations_and_order(
    seeded_state: tuple[Path, str],
) -> None:
    db_path, operation_id = seeded_state
    cohort = probe.run_minilev_probe_cohort(_request(operation_id, "zip-probe-cohort"), db_path)
    assert cohort["disposition"] == "SUCCEEDED"
    assert cohort["promotion_allowed"] is False
    assert cohort["admission_allowed"] is False
    assert cohort["core_update"] is False
    scenarios = {row["scenario"] for row in cohort["events"]}
    assert {"positive", "replay", "mutation", "boundary", "role_ablation"} <= scenarios
    positive, replay = cohort["events"][:2]
    assert positive["disposition"] == "SUCCEEDED"
    assert replay["disposition"] == "SUCCEEDED"
    assert replay["replay_stable"] is True
    mutation = next(row for row in cohort["events"] if row["scenario"] == "mutation")
    boundary = next(row for row in cohort["events"] if row["scenario"] == "boundary")
    assert mutation["disposition"] == "REFUSE"
    assert mutation["no_write_on_refusal"] is True
    assert boundary["disposition"] == "SUCCEEDED"
    ablations = [row for row in cohort["events"] if row["scenario"] == "role_ablation"]
    assert {row["role"] for row in ablations} == set(probe.ROLE_IDS)
    assert all(row["no_write_on_refusal"] is True for row in ablations)
    assert {row["role"] for row in cohort["roles"]} == set(probe.ROLE_IDS)
    assert all(row["settlement_delta"] == 1.0 for row in cohort["roles"])
    assert cohort["order"]["ab_disposition"] == "SUCCEEDED"
    assert cohort["order"]["ba_disposition"] == "REFUSE"
    assert cohort["order"]["order_sensitive"] is True
    assert cohort["order"]["ab_ba_interaction_observed"] is True
    assert all("event_id" in row for row in cohort["events"])


def test_source_probe_failure_is_a_hold_even_when_state_is_valid(
    seeded_state: tuple[Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path, operation_id = seeded_state
    original = probe.inspect_light_source_status

    def mismatch(**kwargs: object) -> dict[str, object]:
        return {"status": "HOLD", "reason_code": "HOLD_MINILEV_SOURCE_MISMATCH"}

    monkeypatch.setattr(probe, "inspect_light_source_status", mismatch)
    result = probe.run_minilev_operation(_request(operation_id, "source-mismatch"), db_path)
    assert result["disposition"] == "HOLD"
    assert result["reason_code"] == "HOLD_MINILEV_SOURCE_MISMATCH"
    assert result["no_write_on_refusal"] is True
    monkeypatch.setattr(probe, "inspect_light_source_status", original)


def test_registered_minilev_probe_packet_executes_and_replays(
    seeded_state: tuple[Path, str],
) -> None:
    db_path, operation_id = seeded_state
    packet = probe.build_minilev_zip_packet(
        request=json.dumps(_request(operation_id, "registered-zip-probe"), sort_keys=True).encode(),
        state_bytes=db_path.read_bytes(),
        cohort=True,
    )
    first = execute_packet(packet)
    second = execute_packet(packet)
    assert first.return_zip_bytes == second.return_zip_bytes
    validate_return_zip(
        first.return_zip_bytes,
        expected_input_sha256=first.input_packet_sha256,
        input_packet_bytes=packet,
    )
    with zipfile.ZipFile(io.BytesIO(first.return_zip_bytes), "r") as archive:
        result = json.loads(archive.read("output/minilev_probe.json"))
    assert result["schema"] == probe.COHORT_SCHEMA
    assert result["disposition"] == "SUCCEEDED"
    assert result["core_update"] is False
    assert result["promotion_allowed"] is False
