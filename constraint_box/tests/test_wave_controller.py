from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
import sqlite3
import sys
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
LIGHT_SOURCE = ROOT / "light_runtime" / "src"
_PACKAGE_NAME = "_cb_light_fixture_controller"


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_contained_light_modules():
    """Load the contained package without importing the legacy root package."""

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
    contracts = importlib.import_module(f"{_PACKAGE_NAME}.wave_contracts")
    adapters = importlib.import_module(f"{_PACKAGE_NAME}.wave_adapters")
    controller = importlib.import_module(f"{_PACKAGE_NAME}.wave_controller")
    return contracts, adapters, controller


contracts, adapters, controller = _load_contained_light_modules()


def _digest(char: str) -> str:
    return char * 64


def _packet() -> dict[str, Any]:
    return {
        "schema": "constraintbox.wave-probe-packet.v1",
        "packet_id": "packet-alpha",
        "wave_definition_id": "wave-definition-alpha",
        "issue": {
            "schema": "constraintbox.wave-issue-card.v1",
            "issue_id": "issue-alpha",
            "statement": "Bounded local fixture checks one target without external authority.",
            "target_ids": ["target-a"],
            "required_probe_kinds": ["witness", "falsifier", "evidence_map"],
            "root_input_sha256": _digest("0"),
        },
        "target_id": "target-a",
        "probes": [
            {
                "kind": "witness",
                "node_id": "node-witness",
                "mmm_sha256": _digest("1"),
                "constrained_input_sha256": _digest("4"),
                "payload": {"bounded": "yes", "role": "witness"},
                "evidence_refs": ["evidence:operation"],
            },
            {
                "kind": "falsifier",
                "node_id": "node-falsifier",
                "mmm_sha256": _digest("2"),
                "constrained_input_sha256": _digest("5"),
                "payload": {"bounded": "yes", "role": "falsifier"},
                "evidence_refs": ["evidence:counterexample"],
            },
            {
                "kind": "evidence_map",
                "node_id": "node-evidence",
                "mmm_sha256": _digest("3"),
                "constrained_input_sha256": _digest("6"),
                "payload": {"bounded": "yes", "role": "evidence"},
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


def _table_count(db_path: Path, table: str) -> int:
    connection = sqlite3.connect(db_path)
    try:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    finally:
        connection.close()


def test_positive_fixture_wave_runs_exactly_three_local_adapters_and_verifies_state(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "wave.sqlite"

    result = controller.run_fixture_wave(_packet(), db_path=db_path)

    assert result["disposition"] == "SETTLED"
    assert result["reason_code"] == "SETTLED_LOCAL_FIXTURE_FACTSET"
    assert result["persisted"] is True
    assert result["promotion_allowed"] is False
    assert result["corroboration"] == "none"
    assert len(result["controller_source_sha256"]) == 64
    assert set(result["controller_source_sha256"]) <= set("0123456789abcdef")
    assert result["executed_local_adapters"] == [
        "cb-light-fixture-witness-v1",
        "cb-light-fixture-falsifier-v1",
        "cb-light-fixture-evidence-map-v1",
    ]
    assert result["external_assets"] == {
        "models": "not_invoked",
        "providers": "not_invoked",
        "skills": "not_invoked",
        "mmms": "reference_digest_only",
        "pydantic_ai": "not_imported",
        "cb_heavy": "not_imported",
        "network": "not_used",
    }
    assert result["gate"]["enumeration_cases"] == 64
    assert result["gate"]["agreement"] is True
    assert result["state_verification"] == {
        "schema": "constraintbox.cb-light-wave-state.v1",
        "schema_version": 1,
        "binding_count": 6,
        "retained_state_integrity_verified": True,
        "independent_semantic_proof": "not_claimed",
    }
    assert _table_count(db_path, "cb_light_wave_attempt") == 1
    assert _table_count(db_path, "cb_light_wave_asset_binding") == 6
    assert _table_count(db_path, "cb_light_wave_settlement") == 1

    connection = sqlite3.connect(db_path)
    try:
        binding_states = {
            row[0]
            for row in connection.execute(
                "SELECT binding_state FROM cb_light_wave_asset_binding"
            )
        }
        settlement = connection.execute(
            "SELECT outcome, reason_code FROM cb_light_wave_settlement"
        ).fetchone()
    finally:
        connection.close()
    assert binding_states == {"bound_reference"}
    assert settlement == ("SETTLED", "SETTLED_LOCAL_FIXTURE_FACTSET")


def test_missing_falsifier_and_pydantic_extra_refuse_before_database_creation(
    tmp_path: Path,
) -> None:
    no_falsifier_db = tmp_path / "no-falsifier.sqlite"
    missing_falsifier = _packet()
    missing_falsifier["probes"] = [
        probe
        for probe in missing_falsifier["probes"]
        if probe["kind"] != "falsifier"
    ]

    no_falsifier = controller.run_fixture_wave(
        missing_falsifier,
        db_path=no_falsifier_db,
    )

    extra_db = tmp_path / "extra.sqlite"
    extra = _packet()
    extra["unexpected"] = True
    extra_result = controller.run_fixture_wave(extra, db_path=extra_db)

    assert no_falsifier["disposition"] == "REFUSE"
    assert no_falsifier["reason_code"] == "REFUSE_FALSIFIER_REQUIRED"
    assert no_falsifier["persisted"] is False
    assert extra_result["disposition"] == "REFUSE"
    assert extra_result["reason_code"] == "REFUSE_UNEXPECTED_FIELD"
    assert extra_result["persisted"] is False
    assert not no_falsifier_db.exists()
    assert not extra_db.exists()


def test_missing_optional_pydantic_contract_dependency_holds_before_database_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "missing-pydantic.sqlite"

    def missing_dependencies():
        raise contracts.WaveContractDependencyMissing("Pydantic is unavailable")

    monkeypatch.setattr(contracts, "_contract_models", missing_dependencies)
    result = controller.run_fixture_wave(_packet(), db_path=db_path)

    assert result["disposition"] == "HOLD"
    assert result["reason_code"] == "HOLD_WAVE_CONTRACT_DEPENDENCY_MISSING"
    assert result["persisted"] is False
    assert not db_path.exists()


@pytest.mark.parametrize(
    ("forged_field", "forged_value"),
    (("authority", "AUTHORITATIVE"), ("pass", True)),
)
def test_forged_authority_or_pass_shaped_observation_refuses_before_database_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    forged_field: str,
    forged_value: object,
) -> None:
    db_path = tmp_path / f"forged-{forged_field}.sqlite"
    original_observe = adapters.WitnessObservationAdapter.observe

    def forged_observe(self, packet):
        observation = original_observe(self, packet)
        object.__setattr__(observation, forged_field, forged_value)
        return observation

    monkeypatch.setattr(adapters.WitnessObservationAdapter, "observe", forged_observe)
    result = controller.run_fixture_wave(_packet(), db_path=db_path)

    assert result["disposition"] == "REFUSE"
    assert result["reason_code"] == "REFUSE_SYNTHETIC_OBSERVATION_FORGED"
    assert result["persisted"] is False
    assert not db_path.exists()


def test_local_counterexample_settles_refuted_fixture_without_promotion(tmp_path: Path) -> None:
    db_path = tmp_path / "refuted.sqlite"

    result = controller.run_fixture_wave(_refuted_packet(), db_path=db_path)

    assert result["disposition"] == "SETTLED_REFUTED"
    assert result["reason_code"] == "SETTLED_REFUTED_LOCAL_COUNTEREXAMPLE"
    assert result["promotion_allowed"] is False
    assert result["fixture_claim_outcome"] == "LOCAL_COUNTEREXAMPLE_BOUND"
    assert result["fact_set"]["counterexample_present"] is True
    assert result["state_outcome"] == "REFUSE"
    assert _table_count(db_path, "cb_light_wave_settlement") == 1


def test_unbound_counterexample_field_cannot_flip_a_fixture_result(tmp_path: Path) -> None:
    packet = _packet()
    falsifier = next(
        probe for probe in packet["probes"] if probe["kind"] == "falsifier"
    )
    falsifier["payload"]["counterexample"] = "present"

    result = controller.run_fixture_wave(packet, db_path=tmp_path / "unbound.sqlite")

    assert result["disposition"] == "SETTLED"
    assert result["fixture_claim_outcome"] == "NO_LOCAL_COUNTEREXAMPLE"
    assert result["fact_set"]["counterexample_present"] is False


def test_topology_cycle_refuses_before_database_creation(tmp_path: Path) -> None:
    db_path = tmp_path / "cycle.sqlite"
    cycle_edges = (
        ("issue", "witness"),
        ("issue", "falsifier"),
        ("issue", "evidence_map"),
        ("witness", "settlement"),
        ("falsifier", "settlement"),
        ("evidence_map", "settlement"),
        ("settlement", "issue"),
    )

    result = controller.run_fixture_wave(
        _packet(),
        db_path=db_path,
        topology_edges=cycle_edges,
    )

    assert result["disposition"] == "REFUSE"
    assert result["reason_code"] == "REFUSE_WAVE_TOPOLOGY_CYCLE"
    assert result["persisted"] is False
    assert not db_path.exists()
