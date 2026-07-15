from __future__ import annotations

import copy
import datetime as dt
import json
from pathlib import Path

from provider_advisory_control import (
    catalog_receipt,
    preflight_receipt,
    write_receipt,
)
from validate_provider_advisory import validate


def write(path: Path, payload: object) -> Path:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def test_fixture_catalog_is_dynamic_and_nonauthoritative(tmp_path: Path) -> None:
    fixture = write(
        tmp_path / "models.json",
        {
            "data": [
                {"id": "z/model-b"},
                {"id": "a/model-a"},
                {"id": "a/model-a"},
            ]
        },
    )
    receipt, code = catalog_receipt("nvidia", fixture=fixture)
    assert code == 0
    assert receipt["models"] == ["a/model-a", "z/model-b"]
    assert receipt["gate_authority"] is False
    assert validate(receipt) == []


def test_unknown_quota_holds(tmp_path: Path) -> None:
    fixture = write(
        tmp_path / "models.json", {"data": [{"id": "grok-test"}]}
    )
    catalog, _ = catalog_receipt("xai", fixture=fixture)
    catalog_path = tmp_path / "catalog.json"
    write_receipt(catalog_path, catalog)
    policy = write(
        tmp_path / "policy.json",
        {
            "schema": "codex_ratchet.provider_quota_policy.v1",
            "policies": [
                {
                    "provider": "xai",
                    "model": "*",
                    "max_requests": None,
                    "window_seconds": None,
                }
            ],
        },
    )
    receipt, code = preflight_receipt(
        catalog_path, policy, "xai", "grok-test"
    )
    assert code == 2
    assert receipt["decision"] == "HOLD"
    assert receipt["reason"] == "quota_unknown"
    assert validate(receipt) == []


def test_known_quota_and_catalog_allow_only_advisory_dispatch(
    tmp_path: Path,
) -> None:
    fixture = write(
        tmp_path / "models.json",
        {"data": [{"id": "deepseek/example"}]},
    )
    catalog, _ = catalog_receipt("nvidia", fixture=fixture)
    catalog_path = tmp_path / "catalog.json"
    write_receipt(catalog_path, catalog)
    policy = write(
        tmp_path / "policy.json",
        {
            "schema": "codex_ratchet.provider_quota_policy.v1",
            "policies": [
                {
                    "provider": "nvidia",
                    "model": "deepseek/example",
                    "max_requests": 2,
                    "window_seconds": 3600,
                }
            ],
        },
    )
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(
        json.dumps(
            {
                "provider": "nvidia",
                "model": "deepseek/example",
                "timestamp": "2026-07-15T12:30:00+00:00",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    receipt, code = preflight_receipt(
        catalog_path,
        policy,
        "nvidia",
        "deepseek/example",
        ledger_path=ledger,
        now=dt.datetime(2026, 7, 15, 13, 0, tzinfo=dt.UTC),
    )
    assert code == 0
    assert receipt["decision"] == "ADVISORY_DISPATCH_ALLOWED"
    assert receipt["remaining_requests"] == 1
    assert receipt["gate_authority"] is False
    assert validate(receipt) == []


def test_model_catalog_drift_holds(tmp_path: Path) -> None:
    fixture = write(
        tmp_path / "models.json", {"data": [{"id": "current-model"}]}
    )
    catalog, _ = catalog_receipt("xai", fixture=fixture)
    catalog_path = tmp_path / "catalog.json"
    write_receipt(catalog_path, catalog)
    policy = write(
        tmp_path / "policy.json",
        {
            "schema": "codex_ratchet.provider_quota_policy.v1",
            "policies": [
                {
                    "provider": "xai",
                    "model": "*",
                    "max_requests": 10,
                    "window_seconds": 60,
                }
            ],
        },
    )
    receipt, code = preflight_receipt(
        catalog_path, policy, "xai", "removed-model"
    )
    assert code == 2
    assert receipt["reason"] == "model_not_in_catalog"


def test_validator_rejects_gate_authority_and_fabricated_catalog_hash(
    tmp_path: Path,
) -> None:
    fixture = write(tmp_path / "models.json", {"data": [{"id": "m"}]})
    receipt, _ = catalog_receipt("nvidia", fixture=fixture)
    promoted = copy.deepcopy(receipt)
    promoted["gate_authority"] = True
    assert "gate_authority fence mismatch" in validate(promoted)
    fabricated = copy.deepcopy(receipt)
    fabricated["model_catalog_sha256"] = "0" * 64
    assert "catalog hash mismatch" in validate(fabricated)
    fabricated_source = copy.deepcopy(receipt)
    fabricated_source["source"]["sha256"] = "0" * 64
    assert "catalog source hash mismatch" in validate(fabricated_source)
