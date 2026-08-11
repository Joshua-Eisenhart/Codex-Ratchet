from __future__ import annotations

import builtins
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LIGHT_SOURCE = ROOT / "light_runtime" / "src"
_PACKAGE_NAME = "_cb_light_fixture_contracts"

# ``hookkernel`` is bundled into the Light wheel alongside ``constraintbox``;
# source-level tests add the owning CB directory only to compare its shared
# canonicalizer, never to import the legacy ``constraintbox`` package.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from hookkernel.cb_light_domain import canonical_json as shared_canonical_json


def _load_contained_light_modules():
    """Load the source-owned Light package without importing legacy root source."""

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
    return contracts, adapters


contracts, adapters = _load_contained_light_modules()


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
            "statement": "Bounded local fixture checks one target without settling it.",
            "target_ids": ["target-b", "target-a"],
            "required_probe_kinds": ["evidence_map", "witness", "falsifier"],
            "root_input_sha256": _digest("0"),
        },
        "target_id": "target-a",
        "probes": [
            {
                "kind": "evidence_map",
                "node_id": "node-evidence",
                "mmm_sha256": _digest("3"),
                "constrained_input_sha256": _digest("6"),
                "payload": {"bounded": "yes", "role": "evidence"},
                "evidence_refs": ["evidence:ledger", "evidence:source"],
            },
            {
                "kind": "witness",
                "node_id": "node-witness",
                "mmm_sha256": _digest("1"),
                "constrained_input_sha256": _digest("4"),
                "payload": {"bounded": "yes", "role": "witness"},
                "evidence_refs": ["evidence:operation", "evidence:source"],
            },
            {
                "kind": "falsifier",
                "node_id": "node-falsifier",
                "mmm_sha256": _digest("2"),
                "constrained_input_sha256": _digest("5"),
                "payload": {"bounded": "yes", "role": "falsifier"},
                "evidence_refs": ["evidence:counterexample", "evidence:source"],
            },
        ],
    }


def test_strict_packet_is_sealed_bounded_and_contains_mandatory_falsifier() -> None:
    result = contracts.validate_probe_packet(_packet())

    assert result.disposition == "VALIDATED"
    assert result.reason_code == "STRICT_WAVE_PACKET_VALIDATED"
    assert result.packet is not None
    assert result.packet.wave_definition_id == "wave-definition-alpha"
    assert not hasattr(result.packet, "attempt_id")
    assert result.packet.issue.target_ids == ("target-a", "target-b")
    assert result.packet.issue.required_probe_kinds == contracts.PROBE_KINDS
    assert tuple(probe.kind for probe in result.packet.probes) == contracts.PROBE_KINDS
    assert result.packet.probe_for("falsifier").node_id == "node-falsifier"
    assert result.packet_sha256 is not None
    assert result.contract_schema_sha256 is not None
    assert "settlement" in result.claim_ceiling


def test_missing_falsifier_and_strict_extra_fields_refuse() -> None:
    missing_falsifier = _packet()
    missing_falsifier["probes"] = [
        probe
        for probe in missing_falsifier["probes"]
        if probe["kind"] != "falsifier"
    ]
    missing_result = contracts.validate_probe_packet(missing_falsifier)

    extra = _packet()
    extra["unexpected"] = True
    extra_result = contracts.validate_probe_packet(extra)

    assert missing_result.disposition == "REFUSE"
    assert missing_result.reason_code in {
        "REFUSE_FALSIFIER_REQUIRED",
        "REFUSE_WAVE_PACKET_INVALID",
    }
    assert extra_result.disposition == "REFUSE"
    assert extra_result.reason_code == "REFUSE_UNEXPECTED_FIELD"


def test_model_provider_pass_and_promotion_fields_are_refused_at_every_depth() -> None:
    cases = (
        ("provider", "not-a-route"),
        ("provider_name", "also-not-a-route"),
        ("model", "not-a-model"),
        ("promotion_allowed", True),
    )
    for key, value in cases:
        raw = _packet()
        raw["probes"][0][key] = value
        result = contracts.validate_probe_packet(raw)
        assert result.disposition == "REFUSE"
        assert result.reason_code == "REFUSE_FORBIDDEN_AUTHORITY_FIELD"


def test_missing_optional_contract_dependencies_returns_typed_hold(monkeypatch) -> None:
    original_import = builtins.__import__

    for blocked_module in ("pydantic", "jsonschema"):
        def missing_optional_dependency(name, globals=None, locals=None, fromlist=(), level=0):
            if name == blocked_module or name.startswith(f"{blocked_module}."):
                raise ModuleNotFoundError(
                    f"blocked optional dependency: {blocked_module}",
                    name=blocked_module,
                )
            return original_import(name, globals, locals, fromlist, level)

        with monkeypatch.context() as scoped:
            scoped.setattr(builtins, "__import__", missing_optional_dependency)
            result = contracts.validate_probe_packet(_packet())

        assert result.disposition == "HOLD"
        assert result.reason_code == "HOLD_WAVE_CONTRACT_DEPENDENCY_MISSING"
        assert result.packet is None
        assert result.packet_sha256 is None


def _canonical_bytes_with_hash_seed(seed: str, raw: dict[str, Any], cwd: Path) -> str:
    code = "\n".join(
        [
            "import json",
            "import sys",
            f"sys.path.insert(0, {str(ROOT)!r})",
            f"sys.path.insert(0, {str(LIGHT_SOURCE)!r})",
            "from constraintbox.wave_contracts import canonical_packet_bytes, validate_probe_packet",
            f"raw = json.loads({json.dumps(raw)!r})",
            "result = validate_probe_packet(raw)",
            "assert result.is_validated, result.as_dict()",
            "print(canonical_packet_bytes(result.packet).hex())",
        ]
    )
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONHASHSEED"] = seed
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    return completed.stdout.strip()


def test_canonical_packet_bytes_are_stable_across_hash_seeds(tmp_path: Path) -> None:
    first = _packet()
    second = _packet()
    second["issue"]["target_ids"] = list(reversed(second["issue"]["target_ids"]))
    second["issue"]["required_probe_kinds"] = [
        "falsifier",
        "evidence_map",
        "witness",
    ]
    second["probes"] = list(reversed(second["probes"]))
    second["probes"][0]["payload"] = {"role": "falsifier", "bounded": "yes"}
    second["probes"][0]["evidence_refs"] = list(
        reversed(second["probes"][0]["evidence_refs"])
    )

    normal = contracts.validate_probe_packet(first)
    reordered = contracts.validate_probe_packet(second)
    assert normal.is_validated and reordered.is_validated
    assert contracts.canonical_packet_bytes(normal.packet) == contracts.canonical_packet_bytes(
        reordered.packet
    )
    assert contracts.canonical_packet_bytes(normal.packet) == shared_canonical_json(
        normal.packet.as_dict()
    )

    seed_one = _canonical_bytes_with_hash_seed("1", first, tmp_path)
    seed_two = _canonical_bytes_with_hash_seed("987654", second, tmp_path)
    assert seed_one == seed_two


def test_three_local_adapters_only_emit_non_authoritative_observations() -> None:
    validated = contracts.validate_probe_packet(_packet())
    assert validated.packet is not None

    observations = [
        adapter.observe(validated.packet)
        for adapter in adapters.fixture_observation_adapters()
    ]

    assert len(observations) == 3
    assert tuple(observation.probe_kind for observation in observations) == contracts.PROBE_KINDS
    assert {observation.observation_kind for observation in observations} == {
        "SYNTHETIC_LOCAL_OBSERVATION"
    }
    assert {observation.authority for observation in observations} == {
        "NON_AUTHORITATIVE"
    }
    for observation in observations:
        body = observation.as_dict()
        assert observation.canonical_bytes() == observation.canonical_bytes()
        assert not {
            "pass",
            "status",
            "terminal",
            "promotion",
            "promotion_allowed",
        }.intersection(key.lower() for key in body)
        assert "settlement" in observation.claim_ceiling
