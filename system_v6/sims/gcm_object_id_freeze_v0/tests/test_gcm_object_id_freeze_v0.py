#!/usr/bin/env python3
"""Tests for gcm_object_id_freeze_v0."""

from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
SCRIPTS_DIR = ROOT / "scripts"
for path in (SIM_DIR, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import gcm_object_id_freeze_v0 as common  # noqa: E402
import validate_gcm_object_id_freeze_v0 as validator  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


def test_registry_contract_and_validator() -> None:
    payload = common.build_registry()
    assert payload["counts"] == {"survivor_count": 16, "quotient_class_count": 8, "candidate_region_count": 6}
    assert validator.validate_payload(payload) == []


def test_unknown_object_id_fails() -> None:
    payload = common.build_registry()
    bad = {
        "gcm_lineage": {
            "gcm_object_id": payload["gcm_object_id"],
            "object_maps": [{"survivor_id": "surv_unknown"}],
        }
    }
    result = gcm_substrate_check(bad, common.RESULT_PATH)
    assert result["ok"] is False
    assert any("unknown survivor_id" in err for err in result["errors"])


def test_stale_registry_hash_fails_in_scratch() -> None:
    payload = common.build_registry()
    cited = {"gcm_lineage": {"gcm_object_id": payload["gcm_object_id"]}}
    stale = copy.deepcopy(payload)
    stale["carve_hashes"][0]["sha256"] = "0" * 64
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "registry.json"
        common.write_json(path, stale)
        result = gcm_substrate_check(cited, path)
    assert result["ok"] is False
    assert any("carve hash drift" in err for err in result["errors"])
