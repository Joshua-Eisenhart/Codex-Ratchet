from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
LIGHT_SOURCE = ROOT / "light_runtime" / "src"
_PACKAGE_NAME = "_cb_light_fixture_wave_cli"


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_core_cli():
    if _PACKAGE_NAME not in sys.modules:
        init_py = LIGHT_SOURCE / "constraintbox" / "__init__.py"
        spec = importlib.util.spec_from_file_location(
            _PACKAGE_NAME,
            init_py,
            submodule_search_locations=[str(init_py.parent)],
        )
        assert spec is not None and spec.loader is not None
        package = importlib.util.module_from_spec(spec)
        sys.modules[_PACKAGE_NAME] = package
        spec.loader.exec_module(package)
    return importlib.import_module(f"{_PACKAGE_NAME}.core_cli")


core_cli = _load_core_cli()
contracts = importlib.import_module(f"{_PACKAGE_NAME}.wave_contracts")
controller = importlib.import_module(f"{_PACKAGE_NAME}.wave_controller")


@pytest.fixture(autouse=True)
def _current_light_gate_for_fixture_logic(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep fixture semantics tests independent of the installed-wheel gate.

    These tests deliberately load source under a private package name, whereas
    the public gate executes the installed contained wheel.  The distinct
    entry-gate suite exercises that live boundary; without this fixture any
    source edit correctly makes the installed wheel stale and masks the local
    packet assertions below.
    """

    monkeypatch.setattr(
        core_cli,
        "_current_cb_light_evaluation_for_wave",
        lambda: (
            True,
            "CB_LIGHT_EVALUATION_GATE_CURRENT",
            {"mode": "test-current-light"},
        ),
    )


def _digest(char: str) -> str:
    return char * 64


def _packet() -> dict[str, Any]:
    return {
        "schema": "constraintbox.wave-probe-packet.v1",
        "packet_id": "packet-cli",
        "wave_definition_id": "wave-definition-cli",
        "issue": {
            "schema": "constraintbox.wave-issue-card.v1",
            "issue_id": "issue-cli",
            "statement": "CLI fixture runs only a sealed local three-probe packet.",
            "target_ids": ["target-cli"],
            "required_probe_kinds": ["witness", "falsifier", "evidence_map"],
            "root_input_sha256": _digest("0"),
        },
        "target_id": "target-cli",
        "probes": [
            {
                "kind": "witness",
                "node_id": "node-witness-cli",
                "mmm_sha256": _digest("1"),
                "constrained_input_sha256": _digest("4"),
                "payload": {"bounded": "yes"},
                "evidence_refs": ["evidence:operation"],
            },
            {
                "kind": "falsifier",
                "node_id": "node-falsifier-cli",
                "mmm_sha256": _digest("2"),
                "constrained_input_sha256": _digest("5"),
                "payload": {"bounded": "yes"},
                "evidence_refs": ["evidence:counterexample"],
            },
            {
                "kind": "evidence_map",
                "node_id": "node-evidence-cli",
                "mmm_sha256": _digest("3"),
                "constrained_input_sha256": _digest("6"),
                "payload": {"bounded": "yes"},
                "evidence_refs": ["evidence:source"],
            },
        ],
    }


def _refuted_packet() -> dict[str, Any]:
    packet = _packet()
    witness = next(probe for probe in packet["probes"] if probe["kind"] == "witness")
    falsifier = next(
        probe for probe in packet["probes"] if probe["kind"] == "falsifier"
    )
    witness["payload"]["fixture_claim"] = "target_is_admissible"
    validated = contracts.validate_probe_packet(packet)
    assert validated.packet is not None
    falsifier["payload"].update(
        {
            "counterexample": "negates_target_admissibility",
            "refutes_witness_node_id": witness["node_id"],
            "refutes_witness_fact_sha256": controller._witness_fact_sha256(
                validated.packet
            ),
        }
    )
    return packet


def test_wave_cli_returns_zero_only_for_local_settled_fixture(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request_path = tmp_path / "request.json"
    output_path = tmp_path / "result.json"
    db_path = tmp_path / "wave.sqlite"
    request_path.write_text(json.dumps(_packet()), encoding="utf-8")

    core_cli.main(
        [
            "wave",
            "--request",
            str(request_path),
            "--db",
            str(db_path),
            "--output",
            str(output_path),
        ]
    )

    rendered = json.loads(capsys.readouterr().out)
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert rendered == written
    assert rendered["disposition"] == "SETTLED"
    assert rendered["promotion_allowed"] is False


def test_wave_dependency_gate_requires_exact_control_plane_pins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allowed, reason, binding = core_cli._current_control_plane_dependencies_for_wave()

    assert allowed is True
    assert reason == "CONTROL_PLANE_DEPENDENCIES_CURRENT"
    assert binding["expected_versions"] == {
        "pydantic": "2.12.5",
        "jsonschema": "4.26.0",
    }
    assert str(binding["interpreter"]).endswith(".venv-control-plane/bin/python")
    assert binding["installed"]["pydantic"]["observed_version"] == "2.12.5"
    assert binding["installed"]["jsonschema"]["observed_version"] == "4.26.0"

    monkeypatch.setattr(
        core_cli,
        "_CONTROL_PLANE_EXACT_PINS",
        {"pydantic": "0.0.0", "jsonschema": "4.26.0"},
    )
    allowed, reason, binding = core_cli._current_control_plane_dependencies_for_wave()

    assert allowed is False
    assert reason == "HOLD_WAVE_CONTRACT_DEPENDENCY_VERSION_MISMATCH"
    assert binding["version_mismatches"]["pydantic"]["expected_version"] == "0.0.0"


def test_wave_cli_holds_before_request_or_sqlite_when_typed_profile_is_not_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request_path = tmp_path / "unread-request.json"
    db_path = tmp_path / "wave.sqlite"
    monkeypatch.setattr(
        core_cli,
        "_current_cb_light_evaluation_for_wave",
        lambda: (
            True,
            "CB_LIGHT_EVALUATION_GATE_CURRENT",
            {"mode": "test-current-light"},
        ),
    )
    monkeypatch.setattr(
        core_cli,
        "_current_control_plane_dependencies_for_wave",
        lambda: (
            False,
            "HOLD_WAVE_CONTRACT_DEPENDENCY_VERSION_MISMATCH",
            {"mode": "test-stale-control-plane"},
        ),
    )

    with pytest.raises(SystemExit) as exc_info:
        core_cli.main(["wave", "--request", str(request_path), "--db", str(db_path)])

    rendered = json.loads(capsys.readouterr().out)
    assert exc_info.value.code == 2
    assert rendered["disposition"] == "HOLD"
    assert rendered["reason_code"] == "HOLD_WAVE_CONTRACT_DEPENDENCY_VERSION_MISMATCH"
    assert rendered["persisted"] is False
    assert rendered["entry_gate"]["mode"] == "test-current-light"
    assert rendered["entry_gate"]["control_plane_dependencies"]["mode"] == (
        "test-stale-control-plane"
    )
    assert not db_path.exists()


def test_wave_cli_returns_two_for_local_refuted_fixture(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request_path = tmp_path / "refuted-request.json"
    db_path = tmp_path / "refuted.sqlite"
    request_path.write_text(json.dumps(_refuted_packet()), encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        core_cli.main(
            ["wave", "--request", str(request_path), "--db", str(db_path)]
        )

    rendered = json.loads(capsys.readouterr().out)
    assert exc_info.value.code == 2
    assert rendered["disposition"] == "SETTLED_REFUTED"
    assert rendered["promotion_allowed"] is False


def test_wave_cli_exits_two_for_refusal(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    request_path = tmp_path / "invalid-request.json"
    db_path = tmp_path / "invalid.sqlite"
    packet = _packet()
    packet["unexpected"] = True
    request_path.write_text(json.dumps(packet), encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        core_cli.main(
            ["wave", "--request", str(request_path), "--db", str(db_path)]
        )

    rendered = json.loads(capsys.readouterr().out)
    assert exc_info.value.code == 2
    assert rendered["disposition"] == "REFUSE"
    assert rendered["reason_code"] == "REFUSE_UNEXPECTED_FIELD"
    assert not db_path.exists()
